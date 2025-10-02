import os, json, boto3
from decimal import Decimal
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit

logger  = Logger(service="vanity-api")
tracer  = Tracer(service="vanity-api")
metrics = Metrics(namespace="VanityConnect")

DDB_TABLE = os.getenv("DDB_TABLE", "vanity-numbers-VanityCalls")
ddb = boto3.resource("dynamodb")
table = ddb.Table(DDB_TABLE)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
}

def _jsonable(o):
    if isinstance(o, Decimal):
        # choose float or str; float is fine if you don’t need exact precision
        return float(o)
    raise TypeError

def _ok(body):
    return {"statusCode": 200, "headers": CORS_HEADERS, "body": json.dumps(body, default=_jsonable)}

def _no_content():
    return {"statusCode": 204, "headers": CORS_HEADERS}

@tracer.capture_lambda_handler
@logger.inject_lambda_context
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event, context):
    method = (event.get("requestContext", {}).get("http", {}).get("method")
              or event.get("httpMethod"))
    if method == "OPTIONS":
        return _no_content()

    # ---- your existing "last 5" read logic ----
    # Example: scan last 5 (replace with your real query)
    resp = table.scan(Limit=5)
    items = [
        {
            "caller_number": it.get("caller_number", ""),
            "created_at": it.get("created_at", ""),
            "vanity_candidates": it.get("vanity_candidates", []),
        }
        for it in resp.get("Items", [])
    ]
    # -------------------------------------------

    metrics.add_metric("ApiLast5Requests", MetricUnit.Count, 1)
    return _ok(items)