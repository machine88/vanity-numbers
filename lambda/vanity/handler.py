# app/handler.py
import os, re
from datetime import datetime, timezone
from typing import Dict, Any, List
from decimal import Decimal


import boto3
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit

from .model import VanityCandidate, response_for_connect
from .vanity import vanity_candidates, WORDS


# Observability setup (no fragile correlation_paths constant)
logger  = Logger(service="vanity-processor")
tracer  = Tracer(service="vanity-processor")
metrics = Metrics(namespace="VanityConnect")

DDB_TABLE_NAME = os.getenv("DDB_TABLE", "vanity-numbers-VanityCalls")
ENV = os.getenv("ENV", "dev")
ddb = boto3.resource("dynamodb")
table = ddb.Table(DDB_TABLE_NAME)

def _digits_blocks(e164: str) -> Dict[str, str]:
    d = re.sub(r"\D", "", e164)
    if len(d) >= 10:
        return {"area": d[-10:-7], "prefix": d[-7:-4], "line": d[-4:]}
    return {"area": "", "prefix": "", "line": d[-4:]}

def _format_display(e164: str, letters_suffix: str) -> str:
    p = _digits_blocks(e164)
    if p["area"] and p["prefix"]:
        return f"{p['area']}-{p['prefix']}-{letters_suffix.upper()}"
    d = re.sub(r"\D", "", e164)
    return f"{d}-{letters_suffix.upper()}" if d else letters_suffix.upper()

def _normalize_e164(raw: str) -> str:
    d = re.sub(r"\D", "", raw or "")
    if not d: return ""
    if len(d) == 11 and d.startswith("1"): return f"+{d}"
    if len(d) == 10: return f"+1{d}"
    return f"+{d}"

def _dec(x):
    """Convert floats to Decimal for DynamoDB, recurse into lists/dicts."""
    if isinstance(x, float):
        return Decimal(str(x))
    if isinstance(x, dict):
        return {k: _dec(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_dec(v) for v in x]
    return x

def _put_record(caller_e164: str, top5: List[VanityCandidate]) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    table.put_item(
        Item={
            "pk": f"CALLER#{caller_e164}",
            "sk": f"TS#{ts}",
            "caller_number": caller_e164,
            "created_at": ts,
            "vanity_candidates": [c.display for c in top5],
            "raw": [
                {
                    "display": c.display,
                    "score": _dec(c.score),
                    "letters": c.raw_letters,
                }
                for c in top5
            ],
        }
    )

@tracer.capture_lambda_handler
@logger.inject_lambda_context
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: Dict[str, Any], context):
    # Correlate with Connect ContactId if present (don’t crash if missing)
    contact_id = (
        event.get("Details", {})
             .get("ContactData", {})
             .get("ContactId")
    )
    if contact_id:
        logger.set_correlation_id(contact_id)

    try:
        # 1) Extract caller number (Connect or test)
        if "Details" in event and "ContactData" in event["Details"]:
            caller_raw = event["Details"]["ContactData"]["CustomerEndpoint"]["Address"]
        else:
            caller_raw = event.get("phone", "")

        e164 = _normalize_e164(caller_raw)
        if not e164:
            logger.warning("No valid caller number", extra={"caller_raw": caller_raw})
            metrics.add_metric("InvalidCallerNumber", MetricUnit.Count, 1)
            # Return empty, but keep both shapes for safety
            return {"option1": "", "option2": "", "option3": "", "prompt_ssml": ""}

        # 2) Generate candidates
        with tracer.provider.in_subsegment("generate_candidates") as sub:
            all_cands = vanity_candidates(e164, max_letters=7)
            for c in all_cands:
                c.display = _format_display(e164, c.raw_letters)  # type: ignore[attr-defined]
            all_cands.sort(key=lambda c: c.score, reverse=True)
            top5 = all_cands[:5]
            sub.put_annotation("candidate_count", len(all_cands))
            sub.put_metadata("top5", [c.display for c in top5])

        # 3) Persist to DynamoDB
        try:
            _put_record(e164, top5)
        except Exception:
            logger.exception("Failed to persist call record")
            metrics.add_metric("DdbWriteErrors", MetricUnit.Count, 1)

        # 4) Metrics
        matched_words = sum(1 for c in top5 if c.raw_letters.upper() in WORDS)
        metrics.add_dimension("env", ENV)
        metrics.add_dimension("service", "vanity-processor")
        metrics.add_metric("CallsProcessed", MetricUnit.Count, 1)
        metrics.add_metric("Top5MatchedWords", MetricUnit.Count, matched_words)

        # 5) Prepare outputs (robust to <3 candidates)
        safe = [c.display for c in top5] + [""] * 3
        o1, o2, o3 = safe[0], safe[1], safe[2]

        # Build compact SSML (no indentation/newlines issues)
        prompt_ssml = (
            "<speak>"
            "Here are your vanity options:"
            "<break time=\"150ms\"/>"
            f"<say-as interpret-as=\"characters\">{o1}</say-as>,"
            "<break time=\"250ms\"/>"
            f"<say-as interpret-as=\"characters\">{o2}</say-as>,"
            "<break time=\"250ms\"/>"
            f"and <say-as interpret-as=\"characters\">{o3}</say-as>."
            "</speak>"
        )

        logger.info("Call processed", extra={"caller_e164": e164, "top3": [o1, o2, o3]})

        # Return BOTH shapes:
        return {
            "option1": o1,
            "option2": o2,
            "option3": o3,
            "prompt_ssml": prompt_ssml,
        }

    except Exception:
        logger.exception("Unhandled error")
        metrics.add_metric("Errors", MetricUnit.Count, 1)
        return {"option1": "", "option2": "", "option3": "", "prompt_ssml": ""}