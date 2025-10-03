# tools/build_lexicon.py
"""
Build /words_4_7.jsonl.gz from a frequency source.

Requires: pip install wordfreq

This pulls common words, keeps 4–7 letters, uppercases them,
and writes JSONL.gz with a Zipf-based score.
"""
import gzip
import json
import re
from pathlib import Path

from wordfreq import top_n_list, zipf_frequency

OUT = Path(__file__).resolve().parents[1] / "words_4_7.jsonl.gz"
WORD_RE = re.compile(r"^[A-Z]{4,7}$")

def is_ok(w: str) -> bool:
    if not WORD_RE.match(w):
        return False
    # Optional: filter weird proper nouns / abbreviations
    # Keep it simple for now.
    return True

def main():
    # Pull ~120k common tokens; filter to 4–7 letters; keep top ~50–100k
    raw = top_n_list("en", 200000)  # generous; we’ll filter down
    kept = []
    for w in raw:
        W = w.upper()
        if is_ok(W):
            score = zipf_frequency(w, "en")  # ~1..7
            kept.append((W, round(score, 3)))

    # Deduplicate and keep best score per word
    best = {}
    for w, s in kept:
        if w not in best or s > best[w]:
            best[w] = s

    # Sort by (score desc, length desc, alpha)
    rows = sorted(best.items(), key=lambda kv: (-kv[1], -len(kv[0]), kv[0]))

    # Cap to ~100k (tune if needed)
    rows = rows[:100000]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT, "wt", encoding="utf-8") as fh:
        for w, s in rows:
            fh.write(json.dumps({"word": w, "score": float(s)}) + "\n")

    print(f"Wrote {len(rows)} words → {OUT}")

if __name__ == "__main__":
    main()