# app/vanity.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set

# ---------- Optional word list (best-effort only) ----------
def load_words() -> Set[str]:
    here = Path(__file__).parent
    path = here / "words_small.txt"
    if not path.exists():
        return set()
    with path.open() as f:
        return {w.strip().upper() for w in f if w.strip()}

WORDS: Set[str] = load_words()

# ---------- T9 helpers & deterministic fallback ----------
T9 = {
    "2": "ABC", "3": "DEF",
    "4": "GHI", "5": "JKL", "6": "MNO",
    "7": "PQRS", "8": "TUV", "9": "WXYZ",
}

@dataclass
class VanityCandidate:
    display: str      # filled by handler for ###-###-LETTERS
    raw_letters: str  # e.g. FLOWERS
    score: float

def _digits_only(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())

def _fallback_letters(digits: str, n: int) -> str:
    last = digits[-n:]
    out: List[str] = []
    for d in last:
        if d in T9:
            out.append(T9[d][0])        # deterministic: take first letter for repeatability
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
    for i, n in enumerate((7, 5, 4)):   # three options, stable order
        if len(d) >= n:
            letters = _fallback_letters(d, n)
            # tiny scoring spread so sort order remains (7 > 5 > 4)
            picks.append(VanityCandidate(display="", raw_letters=letters, score=0.05 - i*0.01))
    # If number is super short, still return some letters to avoid empties
    if not picks and d:
        letters = _fallback_letters(d, min(len(d), 4))
        picks.append(VanityCandidate(display="", raw_letters=letters, score=0.01))
    return picks or [VanityCandidate(display="", raw_letters="CALLME", score=0.001)]

# ---------- Main API used by handler ----------
def vanity_candidates(e164: str, max_letters: int = 7) -> List[VanityCandidate]:
    """
    Return a list of VanityCandidate sorted best-first.
    Uses WORDS if present (future enhancement); always falls back so we never return zero.
    """
    digits = _digits_only(e164)
    if not digits:
        return []

    found: List[VanityCandidate] = []

    # (Placeholder for “real” matching with WORDS; keep interface stable.)
    # If you extend later, populate `found` with actual word matches, e.g.:
    #   1) build T9 string from last N digits
    #   2) intersect with WORDS
    #   3) score by length/frequency

    # Always guarantee at least 3 using fallback if no matches were found.
    return found if found else _fallback_candidates(e164)