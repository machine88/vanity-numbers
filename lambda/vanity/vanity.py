from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple, DefaultDict
import gzip
import json
from collections import defaultdict

# ------------------ Types ------------------
@dataclass
class VanityCandidate:
    display: str       # e.g., "303-FLOWERS" (filled by handler)
    raw_letters: str   # e.g., "FLOWERS"
    score: float

# ------------------ T9 Map ------------------
T9 = {
    "2": "ABC", "3": "DEF",
    "4": "GHI", "5": "JKL", "6": "MNO",
    "7": "PQRS","8": "TUV","9": "WXYZ",
}

# ------------------ Lexicon loading ------------------
# Supports (checked in this order):
#   - words_4_7.jsonl.gz   (JSONL: {"word":"FLOWERS","score":4.5})
#   - words_common.txt.gz  (JSONL: same shape)
#   - words_common.json.gz (JSON array: [{"word":"...","score":...}, ...])
#   - words_small.txt      (one WORD per line)  [fallback/dev]
#
# Exports:
#   WORDS: Set[str]            (for compatibility)
#   WORD_SCORE: Dict[str, float]
def _load_words() -> Tuple[Set[str], Dict[str, float]]:
    here = Path(__file__).parent

    # 0) Preferred file name used in your ZIP
    p = here / "words_4_7.jsonl.gz"
    if p.exists():
        ws: Set[str] = set()
        score: Dict[str, float] = {}
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                w = str(obj["word"]).upper()
                s = float(obj.get("score", 0.0))
                ws.add(w); score[w] = s
        return ws, score

    # 1) JSONL gz (legacy alt)
    p = here / "words_common.txt.gz"
    if p.exists():
        ws: Set[str] = set()
        score: Dict[str, float] = {}
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                obj = json.loads(line)
                w = str(obj["word"]).upper()
                s = float(obj.get("score", 0.0))
                ws.add(w); score[w] = s
        return ws, score

    # 2) JSON array gz
    p = here / "words_common.json.gz"
    if p.exists():
        ws: Set[str] = set()
        score: Dict[str, float] = {}
        with gzip.open(p, "rt", encoding="utf-8") as f:
            arr = json.load(f)
            for obj in arr:
                w = str(obj["word"]).upper()
                s = float(obj.get("score", 0.0))
                ws.add(w); score[w] = s
        return ws, score

    # 3) Tiny txt fallback
    p = here / "words_small.txt"
    if p.exists():
        ws = {w.strip().upper() for w in p.read_text().splitlines() if w.strip()}
        score = {w: 0.0 for w in ws}
        return ws, score

    # 4) Nothing available
    return set(), {}

WORDS, WORD_SCORE = _load_words()  # keep WORDS exported

# ------------------ Helpers ------------------
def _digits_only(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())

def _t9_key(s: str) -> str:
    """Map letters -> digits (e.g., FLOWERS -> 3569377)."""
    rev: Dict[str, str] = {}
    for d, letters in T9.items():
        for L in letters:
            rev[L] = d
    return "".join(rev.get(ch, "") for ch in s if ch.isalpha())

def _fallback_letters(digits: str, n: int) -> str:
    last = digits[-n:]
    out: List[str] = []
    for d in last:
        if d in T9:
            out.append(T9[d][0])  # deterministic
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
            picks.append(VanityCandidate("", letters, 0.05 - i*0.01))
    if not picks and d:
        letters = _fallback_letters(d, min(len(d), 4))
        picks.append(VanityCandidate("", letters, 0.01))
    return picks or [VanityCandidate("", "CALLME", 0.001)]

def _score_word(word: str) -> float:
    """Longer > frequent > pronounceable-ish."""
    base = float(len(word))
    freq = float(WORD_SCORE.get(word, 0.0))  # ~0..5 typical
    vowels = sum(1 for ch in word if ch in "AEIOU")
    vow_bonus = 0.2 if vowels >= max(1, len(word)//4) else 0.0
    repeat_pen = -0.1 if any(word[i] == word[i+1] for i in range(len(word)-1)) else 0.0
    return base + freq + vow_bonus + repeat_pen

# ------------------ Precomputed T9 index (cold start) ------------------
# index[n][t9_digits] -> list of words of length n that map to t9_digits
_INDEX: Dict[int, Dict[str, List[str]]] = {}
if WORDS:
    by_len: DefaultDict[int, List[str]] = defaultdict(list)
    for w in WORDS:
        by_len[len(w)].append(w)
    for n, words in by_len.items():
        bucket: DefaultDict[str, List[str]] = defaultdict(list)
        for w in words:
            bucket[_t9_key(w)].append(w)
        _INDEX[n] = bucket  # type: ignore[assignment]

# ------------------ Main API ------------------
def vanity_candidates(e164: str, max_letters: int = 7) -> List[VanityCandidate]:
    """
    Return best-first VanityCandidate list using the curated lexicon if present,
    else deterministic fallback so we never return zero.
    """
    digits = _digits_only(e164)
    if not digits:
        return []

    # Try longest suffix first (7..4)
    matches: List[str] = []
    for n in range(min(max_letters, 7), 3, -1):
        tail = digits[-n:] if len(digits) >= n else ""
        if not tail:
            continue
        words_by_key = _INDEX.get(n)
        if words_by_key:
            hit = words_by_key.get(tail, [])
            if hit:
                matches = hit
                break

    if not matches:
        return _fallback_candidates(e164)

    scored = [VanityCandidate("", w, _score_word(w)) for w in matches]
    scored.sort(key=lambda c: c.score, reverse=True)
    return scored