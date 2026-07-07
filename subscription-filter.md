# CloudWatch Subscription Filter Setup

**Target log group:** `/PayActiv/internalapis/code`

## Steps (AWS Console)

1. Go to CloudWatch → Log groups → `/PayActiv/internalapis/code`
2. Click **Subscription filters** tab → **Create** → **Create Lambda subscription filter**
3. Choose the Lambda function (`log_processor`) as the destination
4. Filter pattern:
   ```
   ?ERROR ?Exception ?Failed ?Timeout ?500 ?NullReferenceException ?StackTrace
   ```
5. Name it: `ProActiv-Leg1-ErrorFilter`
6. Save

## Steps (AWS CLI equivalent)

```bash
aws logs put-subscription-filter \
  --log-group-name "/PayActiv/internalapis/code" \
  --filter-name "ProActiv-Leg1-ErrorFilter" \
  --filter-pattern '?ERROR ?Exception ?Failed ?Timeout ?500 ?NullReferenceException ?StackTrace' \
  --destination-arn "arn:aws:lambda:<region>:<account-id>:function:log_processor"
```

Also grant CloudWatch Logs permission to invoke the Lambda:

```bash
aws lambda add-permission \
  --function-name log_processor \
  --statement-id CloudWatchInvoke \
  --action lambda:InvokeFunction \
  --principal logs.amazonaws.com \
  --source-arn "arn:aws:logs:<region>:<account-id>:log-group:/PayActiv/internalapis/code:*"
```
