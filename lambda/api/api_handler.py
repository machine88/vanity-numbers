# api_handler.py
import os
import boto3
from boto3.dynamodb.conditions import Key
from aws_lambda_powertools import Logger

logger = Logger(service="vanity-api")
DDB_TABLE_NAME = os.getenv("DDB_TABLE", "vanity-numbers-VanityCalls")
ddb = boto3.resource("dynamodb")
table = ddb.Table(DDB_TABLE_NAME)

def handler(event, context):
    try:
        # newest first, exactly 5
        resp = table.query(
            KeyConditionExpression=Key("pk").eq("RECENT"),
            ScanIndexForward=False,   # descending by sk
            Limit=5,
            ConsistentRead=True
        )
        items = resp.get("Items", [])
        out = [
            {
                "caller": it["caller_number"],
                "created_at": it["created_at"],
                "top3": (it.get("vanity_candidates") or [])[:3]
            }
            for it in items
        ]
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": event.get("headers", {}).get("origin", "*"),
                "Access-Control-Allow-Credentials": "true",
            },
            "body": __import__("json").dumps({"items": out})
        }
    except Exception:
        logger.exception("API error")
        return {"statusCode": 500, "body": '{"message":"Internal Server Error"}'}