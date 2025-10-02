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

def response_for_connect(cands: List[VanityCandidate], limit: int = 3) -> Dict[str, str]:
    """
    Shapes the Lambda result for Amazon Connect's contact flow.
    Connect will read $.External.option1/2/3.
    """
    top = cands[:limit]
    return {
        "option1": top[0].display if len(top) > 0 else "",
        "option2": top[1].display if len(top) > 1 else "",
        "option3": top[2].display if len(top) > 2 else "",
    }