from datetime import datetime

# --------------------------------------------------------------------------
# Builds the structured payload that Leg 2 (Bedrock) will consume.
# Leg 1's job ends here: everything the AI reasoning step needs should be
# present in this one object, so Leg 2 doesn't have to go re-fetch anything.
# --------------------------------------------------------------------------


def build_bedrock_payload(record: dict, rules: dict) -> dict:
    """
    record: the cleaned error record produced by lambda_function.py
      {
        "logGroup", "logStream", "timestamp", "message",
        "surroundingLogs", "application"
      }
    rules: output of snowflake_config.get_error_rules()
      {"ignored", "severity", "routing"}

    Returns the payload Leg 2 will send to Bedrock, e.g.:

    {
      "application": "PayActiv internal APIs",
      "errorMessage": "...",
      "severity": "High",
      "routing": "backend-team-queue",
      "context": {
        "logGroup": "...",
        "logStream": "...",
        "timestamp": "...",
        "surroundingLogs": ["...", "..."]
      },
      "prompt": "You are a senior .NET architect reviewing a production
                 error. Given the error and surrounding logs, identify the
                 root cause, a quick fix, a long-term fix, and provide
                 relevant C# code snippets or SQL queries if applicable."
    }
    """
    return {
        "application": record["application"],
        "errorMessage": record["message"],
        "severity": rules["severity"],
        "routing": rules["routing"],
        "context": {
            "logGroup": record["logGroup"],
            "logStream": record["logStream"],
            "timestamp": datetime.utcfromtimestamp(
                record["timestamp"] / 1000
            ).isoformat(),
            "surroundingLogs": record["surroundingLogs"],
        },
        "prompt": (
            "You are a senior .NET architect reviewing a production error. "
            "Given the error message and surrounding log context below, "
            "identify: (1) the likely root cause, (2) a quick fix, "
            "(3) a long-term fix, and (4) relevant C# code snippets or SQL "
            "queries if applicable. Be specific and reference the actual "
            "error and context provided."
        ),
    }
