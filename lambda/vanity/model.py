# lambda/vanity/model.py
from dataclasses import dataclass
from typing import List, Dict

@dataclass(frozen=True)
class VanityCandidate:
    """
    Represents one vanity option.
    - display: Fully formatted output e.g., '303-555-FLOWERS'
    - score:   Numeric score used for ranking
    - raw_letters: The letters forming the vanity suffix e.g., 'FLOWERS'
    """
    display: str
    score: float
    raw_letters: str

def response_for_connect(cands, limit=3):
    top = [c.display for c in (cands or [])][:limit]
    # fallbacks if empty; keep your existing logic if you prefer
    while len(top) < 3:
        top.append("CALL-ME")
    # Build complete SSML with <speak> wrapper
    def ssml_chars(s):  # spell characters cleanly
        return f"<say-as interpret-as=\"characters\">{s}</say-as>"
    prompt_ssml = (
        "<speak>"
        "Here are your vanity options: "
        f"{ssml_chars(top[0])}, "
        "<break time=\"250ms\"/>"
        f"{ssml_chars(top[1])}, "
        "<break time=\"250ms\"/>"
        f"and {ssml_chars(top[2])}."
        "</speak>"
    )
    return {
        "option1": top[0],
        "option2": top[1],
        "option3": top[2],
        "prompt_ssml": prompt_ssml,   # ← NEW
    }