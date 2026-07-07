# DynamoDB Tables

## Table 1: ProActiv-ErrorContext

Raw cleaned error record, with Snowflake-derived severity/routing attached.

| Attribute        | Type   | Notes                                   |
|-------------------|--------|------------------------------------------|
| id (Partition Key) | String | `{logStream}-{timestamp}`                |
| logGroup          | String | Source log group                        |
| message           | String | The matched error message                |
| surroundingLogs   | List   | Context log lines around the error       |
| application       | String | e.g. "PayActiv internal APIs"            |
| severity          | String | High / Medium / Low, from Snowflake rules |
| routing           | String | Which team/queue this error routes to    |
| createdAt         | String | ISO timestamp of record creation         |

## Table 2: ProActiv-BedrockPayloads

The fully-structured payload Leg 2 reads and sends straight to Bedrock — no rebuilding needed on their end.

| Attribute        | Type   | Notes                                   |
|-------------------|--------|------------------------------------------|
| id (Partition Key) | String | `{logStream}-{timestamp}` (same as above) |
| payload           | String | JSON-encoded Bedrock payload (see `bedrock_payload.py`) |
| createdAt         | String | ISO timestamp of record creation         |

## Create via CLI

```bash
aws dynamodb create-table \
  --table-name ProActiv-ErrorContext \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

aws dynamodb create-table \
  --table-name ProActiv-BedrockPayloads \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```
