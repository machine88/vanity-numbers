# app/vanity.py
from __future__ import annotations
import gzip
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

# -------------------- Data types --------------------
@dataclass
class VanityCandidate:
    display: str      # set by handler later (e.g., 303-378-FLOWERS)
    raw_letters: str  # e.g., FLOWERS
    score: float

# -------------------- T9 maps -----------------------
T9_LETTERS = {
    "2": "ABC", "3": "DEF", "4": "GHI", "5": "JKL",
    "6": "MNO", "7": "PQRS", "8": "TUV", "9": "WXYZ"
}
LETTER_TO_DIGIT = {ch: d for d, letters in T9_LETTERS.items() for ch in letters}

def _digits_only(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())

def _t9_signature(word: str) -> str:
    # assumes word is A–Z only
    return "".join(LETTER_TO_DIGIT.get(c, "") for c in word)

# -------------------- Lexicon loading --------------------
# We’ll look for lambda/vanity/words_common.json.gz first (your new file),
# falling back to the small demo list if needed.
_LEXICON_CACHE: Dict[str, List[Tuple[str, float]]] | None = None  # signature -> [(WORD, freq_score)]
_WORD_COUNT = 0

def _load_lexicon() -> Dict[str, List[Tuple[str, float]]]:
    """
    Load a curated 4–7 letter lexicon with frequency scores and build
    a map from T9 signature -> list[(WORD, freq_score)].
    """
    global _LEXICON_CACHE, _WORD_COUNT
    if _LEXICON_CACHE is not None:
        return _LEXICON_CACHE

    here = Path(__file__).parent
    candidates = [
        here / "words_common.json.gz",   # your generated ~50k curated list
        here / "words_small.txt",        # tiny fallback for dev/demo
    ]

    sig_map: Dict[str, List[Tuple[str, float]]] = {}

    if candidates[0].exists():
        # New curated lexicon (gzipped JSON lines)
        with gzip.open(candidates[0], "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                w = obj.get("word", "").strip().upper()
                if not (4 <= len(w) <= 7) or not w.isalpha():
                    continue
                freq = float(obj.get("score", 0.0))
                sig = _t9_signature(w)
                if not sig:  # should not happen for A–Z
                    continue
                sig_map.setdefault(sig, []).append((w, freq))
        _WORD_COUNT = sum(len(v) for v in sig_map.values())
    elif candidates[1].exists():
        # Dev fallback (no frequency; all 0.0)
        with candidates[1].open() as f:
            for w in (x.strip().upper() for x in f if x.strip()):
                if not (4 <= len(w) <= 7) or not w.isalpha():
                    continue
                sig = _t9_signature(w)
                sig_map.setdefault(sig, []).append((w, 0.0))
        _WORD_COUNT = sum(len(v) for v in sig_map.values())
    else:
        # ultimate fallback: no lexicon available
        sig_map = {}
        _WORD_COUNT = 0

    _LEXICON_CACHE = sig_map
    # basic cold-start telemetry
    print(json.dumps({
        "msg": "lexicon_loaded",
        "entries": _WORD_COUNT,
        "unique_signatures": len(sig_map)
    }))
    return sig_map

# -------------------- Scoring helpers --------------------
_VOWELS = set("AEIOU")

def _word_heuristic(word: str) -> float:
    """small extras on top of frequency: vowels, no silly repeats, etc."""
    v_bonus = 0.1 if any(c in _VOWELS for c in word) else 0.0
    no_repeat_pen = -0.05 if any(word.count(c) >= 3 for c in set(word)) else 0.0
    length_bonus = 0.2 * (len(word) - 4)  # prefer longer (4..7)
    return v_bonus + no_repeat_pen + length_bonus

def _compose_score(freq: float, word: str) -> float:
    # Primary: lexicon frequency; Secondary: heuristics
    return freq + _word_heuristic(word)

# -------------------- Fallback letters --------------------
def _fallback_letters(digits: str, n: int) -> str:
    last = digits[-n:]
    out = []
    for d in last:
        if d in T9_LETTERS:
            out.append(T9_LETTERS[d][0])  # deterministic first letter
        elif d == "0":
            out.append("O")
        elif d == "1":
            out.append("I")
        else:
            out.append(d)
    return "".join(out)

def _fallback_candidates(e164: str) -> List[VanityCandidate]:
    d = _digits_only(e164)
    picks: List[VanityCandidate] = []
    for i, n in enumerate((7, 5, 4)):
        if len(d) >= n:
            letters = _fallback_letters(d, n)
            picks.append(VanityCandidate(display="", raw_letters=letters, score=0.05 - i * 0.01))
    if not picks and d:
        letters = _fallback_letters(d, min(len(d), 4))
        picks.append(VanityCandidate(display="", raw_letters=letters, score=0.01))
    return picks or [VanityCandidate(display="", raw_letters="CALLME", score=0.001)]

# -------------------- Main API --------------------
def vanity_candidates(e164: str, max_letters: int = 7) -> List[VanityCandidate]:
    """
    Return best-first vanity candidates using a curated 4–7 letter lexicon.
    Falls back to deterministic letters if no real word is possible.
    """
    digits = _digits_only(e164)
    if not digits:
        return []

    sig_map = _load_lexicon()

    found: List[VanityCandidate] = []

    # Try windows 7 → 4
    for n in range(min(max_letters, 7), 3, -1):
        if len(digits) < n:
            continue
        window = digits[-n:]  # last N digits
        words = sig_map.get(window, [])
        if not words:
            continue

        ranked = sorted(
            (VanityCandidate(display="", raw_letters=w, score=_compose_score(freq, w))
             for (w, freq) in words),
            key=lambda c: c.score, reverse=True
        )
        found.extend(ranked)

    # Deduplicate by word while preserving order
    seen = set()
    deduped: List[VanityCandidate] = []
    for c in found:
        if c.raw_letters not in seen:
            seen.add(c.raw_letters)
            deduped.append(c)

    # If none, guarantee a few deterministic fallbacks
    if not deduped:
        cands = _fallback_candidates(e164)
        print(json.dumps({"msg": "no_lexicon_match_fallback", "digits": digits[-7:]}))
        return cands

    # Emit a little metric on first few matches
    print(json.dumps({
        "msg": "matches_found",
        "digits": digits[-7:],
        "top": [c.raw_letters for c in deduped[:5]]
    }))

    return deduped