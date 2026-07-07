import gzip
import json
import base64
import boto3
import os
from datetime import datetime, timedelta

from snowflake_config import get_error_rules
from bedrock_payload import build_bedrock_payload

logs_client = boto3.client("logs")
dynamodb = boto3.resource("dynamodb")

# Environment variables (set these in Lambda console)
TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "ProActiv-ErrorContext")
CONTEXT_WINDOW_SECONDS = int(os.environ.get("CONTEXT_WINDOW_SECONDS", "30"))

# Noise patterns to ignore (case-insensitive)
IGNORE_PATTERNS = [
    "health check",
    "ping",
    "warmup",
    "authorization success",
    "info:",
    "debug:",
]


def lambda_handler(event, context):
    """
    Entry point triggered by a CloudWatch Logs subscription filter.
    Decodes the gzip+base64 payload, pulls out matching error events,
    fetches surrounding log context, filters noise, and stores the
    cleaned result for Leg 2 (Bedrock analysis).
    """
    compressed_payload = base64.b64decode(event["awslogs"]["data"])
    payload = json.loads(gzip.decompress(compressed_payload))

    log_group = payload.get("logGroup")
    log_stream = payload.get("logStream")
    results = []

    for log_event in payload.get("logEvents", []):
        message = log_event.get("message", "")

        if _is_noise(message):
            continue

        context_logs = _fetch_surrounding_logs(
            log_group, log_stream, log_event["timestamp"]
        )

        record = {
            "logGroup": log_group,
            "logStream": log_stream,
            "timestamp": log_event["timestamp"],
            "message": message,
            "surroundingLogs": context_logs,
            "application": "PayActiv internal APIs",
        }

        # Check Snowflake config tables: is this ignored, and what's its
        # severity/routing?
        rules = get_error_rules(record["application"], message)
        if rules.get("ignored"):
            continue

        # Attach severity/routing so it's saved alongside the raw record
        record["severity"] = rules["severity"]
        record["routing"] = rules["routing"]
        _store_record(record)

        # Build the structured payload Leg 2 will hand to Bedrock
        bedrock_payload = build_bedrock_payload(record, rules)
        _store_bedrock_payload(record, bedrock_payload)

        results.append(record)

    return {
        "statusCode": 200,
        "processed": len(results),
    }


def _is_noise(message: str) -> bool:
    lower_msg = message.lower()
    return any(pattern in lower_msg for pattern in IGNORE_PATTERNS)


def _fetch_surrounding_logs(log_group, log_stream, timestamp_ms):
    """
    Pulls log events within +/- CONTEXT_WINDOW_SECONDS of the error
    to give Bedrock enough context in Leg 2.
    """
    start_time = timestamp_ms - (CONTEXT_WINDOW_SECONDS * 1000)
    end_time = timestamp_ms + (CONTEXT_WINDOW_SECONDS * 1000)

    try:
        response = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=log_stream,
            startTime=start_time,
            endTime=end_time,
            limit=50,
        )
        return [e["message"] for e in response.get("events", [])]
    except Exception as e:
        print(f"Could not fetch context logs: {e}")
        return []


def _store_record(record):
    """
    Writes the cleaned error + context package to DynamoDB.
    Leg 2 will read from this table to build Bedrock prompts.
    """
    try:
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(
            Item={
                "id": f"{record['logStream']}-{record['timestamp']}",
                "logGroup": record["logGroup"],
                "message": record["message"],
                "surroundingLogs": record["surroundingLogs"],
                "application": record["application"],
                "severity": record.get("severity"),
                "routing": record.get("routing"),
                "createdAt": datetime.utcnow().isoformat(),
            }
        )
    except Exception as e:
        print(f"Could not write to DynamoDB: {e}")


def _store_bedrock_payload(record, bedrock_payload):
    """
    Writes the fully-structured Bedrock payload to DynamoDB under a
    dedicated table, so Leg 2 can just read this item and call Bedrock
    directly without rebuilding anything.
    """
    try:
        table = dynamodb.Table(
            os.environ.get("BEDROCK_PAYLOAD_TABLE", "ProActiv-BedrockPayloads")
        )
        table.put_item(
            Item={
                "id": f"{record['logStream']}-{record['timestamp']}",
                "payload": json.dumps(bedrock_payload),
                "createdAt": datetime.utcnow().isoformat(),
            }
        )
    except Exception as e:
        print(f"Could not write Bedrock payload: {e}")
