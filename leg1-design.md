# Leg 1 Design — Log Detection & Context Gathering

## Flow
1. **CloudWatch** monitors `/PayActiv/internalapis/code` for backend/API errors.
2. **Subscription Filter** triggers Lambda only on useful error keywords (ERROR, Exception, Failed, Timeout, 500, NullReferenceException, StackTrace).
3. **Lambda** decodes the CloudWatch payload, extracts the error message + metadata.
4. Lambda fetches **surrounding context logs** (+/- 30s window) using `get_log_events`.
5. **Noise filtering** drops irrelevant lines (health checks, pings, warmups, debug/info).
6. **Snowflake config check** (`snowflake_config.py`) looks up whether this error/app pair should be ignored, and what severity + routing team it maps to. Currently runs in **stub mode** (safe local defaults) until real Snowflake credentials are added — see that file's docstring for the exact query to drop in once connected.
7. Cleaned error + context + severity/routing is written to **DynamoDB** (`ProActiv-ErrorContext` table).
8. **Bedrock payload builder** (`bedrock_payload.py`) packages everything into the exact structured input Leg 2 needs — error, context, severity, routing, and the prompt template — and writes it to a second table (`ProActiv-BedrockPayloads`).
9. Leg 2 reads directly from `ProActiv-BedrockPayloads` and calls Bedrock — no rebuilding required on their end.

## Required IAM permissions (Lambda execution role)
- `logs:GetLogEvents`
- `logs:DescribeLogStreams`
- `dynamodb:PutItem` on `ProActiv-ErrorContext` and `ProActiv-BedrockPayloads`
- Standard `AWSLambdaBasicExecutionRole` for CloudWatch Logs write access
- (Once Snowflake is live) network access to Snowflake, plus `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, `SNOWFLAKE_WAREHOUSE`, `SNOWFLAKE_DATABASE`, `SNOWFLAKE_SCHEMA` as Lambda environment variables

## Cost control
Filtering both at the subscription-filter level (pattern match) and inside Lambda (noise list + Snowflake ignore rules) keeps invocation count and DynamoDB writes low, which keeps Leg 2's Bedrock token usage down.

## Status
All 5 pieces of the original Leg 1 scope are now implemented: CloudWatch detection, subscription filter, Lambda extraction/context, Snowflake config check (stubbed pending real credentials), and Bedrock payload preparation.
