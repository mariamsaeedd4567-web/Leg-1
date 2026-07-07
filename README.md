# Leg-1: ProActiv AI Agent — Log Detection & Context Gathering

AI-powered log analysis system using AWS (Leg 1 of 2).

## What this covers
- CloudWatch detects application/API errors in `/PayActiv/internalapis/code`
- A subscription filter triggers Lambda only for meaningful error patterns
- Lambda extracts the error + fetches surrounding log context
- Irrelevant/noisy logs are filtered out to control downstream Bedrock cost
- Cleaned context is stored in DynamoDB, ready for Leg 2 (Bedrock analysis)

## Structure
```
lambda/log_processor/     -> Lambda function code
cloudwatch/               -> subscription filter pattern + setup docs
dynamodb/                 -> table schema
docs/                     -> design docs
```

## Setup order
1. Create the DynamoDB table (`dynamodb/table-schema.md`)
2. Deploy the Lambda function (`lambda/log_processor/`)
3. Attach the CloudWatch subscription filter (`cloudwatch/subscription-filter.md`)
