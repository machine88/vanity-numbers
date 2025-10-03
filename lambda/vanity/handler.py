from __future__ import annotations

import os
import re
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List
from decimal import Decimal

import boto3
from app.vanity import vanity_candidates

# ---------- logging ----------
log = logging.getLogger(__name__)
if not log.handlers:
    logging.basicConfig(level=logging.INFO)

# ---------- aws resources ----------
DDB_TABLE_NAME = os.environ.get("DDB_TABLE", "")
_dynamo = boto3.resource("dynamodb") if DDB_TABLE_NAME else None
table = _dynamo.Table(DDB_TABLE_NAME) if _dynamo else None

# ---------- T9 helpers for deterministic fallbacks ----------
T9 = {
    "2": "ABC", "3": "DEF",
    "4": "GHI", "5": "JKL", "6": "MNO",
    "7": "PQRS", "8": "TUV", "9": "WXYZ",
}


def _digits_only(s: str) -> str:
    return "".join(ch for ch in s if s and ch.isdigit())


def _fallback_letters(digits: str, n: int) -> str:
    """Deterministic T9 letters for last n digits: first letter from each mapping."""
    last = digits[-n:]
    out: List[str] = []
    for d in last:
        if d in T9:
            out.append(T9[d][0])  # deterministic first choice
        elif d == "0":
            out.append("O")
        elif d == "1":
            out.append("I")
        else:
            out.append(d)
    return "".join(out)


# ---------- e164 normalization (referenced by tests) ----------
_E164 = re.compile(r"^\+?\d+$")


def normalize_e164(s: str) -> str:
    """
    Best-effort normalize to +1XXXXXXXXXX style (US-centric for this exercise).
    Matches your tests exactly.
    """
    if not s:
        return "+1"

    digs = "".join(ch for ch in s if ch.isdigit())

    if s.startswith("+") and _E164.match(s):
        return s

    if len(digs) == 11 and digs[0] == "1":
        return f"+{digs}"

    if len(digs) == 10:
        return f"+1{digs}"

    if len(digs) == 7:
        return f"+1{digs}"

    return f"+{digs}" if digs else "+1"


# ---------- display & ssml formatting ----------
def _format_display(e164: str, letters: str) -> str:
    """Format like 303-555-FLOWERS (or with 4–7 letter tails)."""
    if not letters:
        return ""
    d = _digits_only(e164)

    if len(d) >= 10:
        area, mid = d[-10:-7], d[-7:-4]
        return f"{area}-{mid}-{letters}"

    if len(d) >= 7:
        return f"{d[-7:-4]}-{d[-4:]}-{letters}"

    return f"{d}-{letters}" if d else letters


def _build_ssml(displays: List[str]) -> str:
    spoken = [f'<say-as interpret-as="characters">{disp}</say-as>' for disp in displays if disp]
    parts = ['<speak>Here are your vanity options:']
    for s in spoken:
        parts.append('<break time="250ms"/>')
        parts.append(s)
    parts.append('.</speak>')
    return "".join(parts)


# ---------- event parsing ----------
def _extract_phone(event: Dict[str, Any]) -> str:
    """
    Accepts either:
      {"phone": "+1..."}
    or Amazon Connect:
      {"Details":{"ContactData":{"CustomerEndpoint":{"Address":"+1..."}}}}
    """
    phone = event.get("phone")
    if phone:
        return normalize_e164(phone)

    try:
        addr = (
            event.get("Details", {})
            .get("ContactData", {})
            .get("CustomerEndpoint", {})
            .get("Address")
        )
        if addr:
            return normalize_e164(addr)
    except Exception:
        pass

    try:
        s = json.dumps(event)
        m = re.search(r"\+\d{7,}", s)
        if m:
            return normalize_e164(m.group(0))
    except Exception:
        pass

    return "+1"


# ---------- ddb write ----------
def _write_recent(e164: str, displays: List[str], scored_raw: List[tuple[str, float]]) -> None:
    """
    Store the latest call in the schema the API and web expect.
    Schema example:
      pk: "RECENT"
      sk: "TS#2025-10-03T21:07:59.123456+00:00"
      caller_number: "+15555551234"
      created_at: ISO-8601 string
      vanity_candidates: ["303-555-FLOWERS","303-555-FLOWE","303-555-FLOW"]
      raw: [
        {"letters":"FLOWERS","display":"303-555-FLOWERS","score":7.2},
        {"letters":"FLOWE",  "display":"303-555-FLOWE",  "score":5.0},
        {"letters":"FLOW",   "display":"303-555-FLOW",   "score":4.0},
      ]
    """
    if not table:
        log.info("No DDB table configured; skipping put_item")
        return

    try:
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "pk": "RECENT",
            "sk": f"TS#{now}",
            "caller_number": e164,
            "created_at": now,
            # FIX: keep exactly 3 slots, even if some are fallback/empty
            "vanity_candidates": displays[:3],
            "raw": [
                {"letters": letters, "display": disp, "score": Decimal(str(score))}
                for (letters, score), disp in zip(scored_raw, displays)
                if disp
            ],
        }
        log.info("Writing to DDB: %s", item)
        table.put_item(Item=item)
        log.info("Wrote item successfully")
    except Exception as e:
        log.warning("Failed to write recent to DDB: %s", e)


# ---------- main lambda ----------
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    log.debug("event: %s", event)
    e164 = _extract_phone(event)
    digits = _digits_only(e164)

    # 1) curated lexicon matches (best-first)
    cands = vanity_candidates(e164, max_letters=7)
    letters: List[str] = [c.raw_letters for c in cands[:3] if c and c.raw_letters]

    # 2) ensure 3 options via deterministic fallbacks
    if len(letters) < 3:
        for n in (5, 4):
            if len(letters) >= 3:
                break
            if len(digits) >= n:
                letters.append(_fallback_letters(digits, n))
    while len(letters) < 3:
        letters.append("")

    # 3) build displays + SSML (skip empties in SSML)
    displays = [_format_display(e164, L) if L else "" for L in letters]
    ssml = _build_ssml(displays)

    # Build scored_raw alongside (use 0.0 if letter came from fallback)
    # cands already sorted best-first; align letters->score
    score_by_letters = {c.raw_letters: c.score for c in cands[:3]}
    scored_raw = [(L, score_by_letters.get(L, 0.0)) for L in letters]

    # 4) best-effort DDB write (correct schema & all three options)
    _write_recent(e164, displays[:3], scored_raw)

    return {
        "option1": displays[0],
        "option2": displays[1],
        "option3": displays[2],
        "prompt_ssml": ssml,
    }
