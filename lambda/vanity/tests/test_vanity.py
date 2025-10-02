# lambda/vanity/tests/test_vanity.py
import re
from lambda.vanity.handler import normalize_e164
from lambda.vanity.vanity import vanity_candidates, WORDS

def test_normalize_e164():
    assert normalize_e164("(303) 555-1212") == "+13035551212"
    assert normalize_e164("13035551212") == "+13035551212"
    assert normalize_e164("+13035551212") == "+13035551212"
    assert normalize_e164("555-1212") == "+15551212"  # fallback, odd length but still digits

def test_generate_candidates_basic():
    e164 = "+13035553679"  # last 7 digits map to something plausible
    cands = vanity_candidates(e164, max_letters=7)
    assert len(cands) > 0
    # Sorted desc by score
    scores = [c.score for c in cands[:10]]
    assert scores == sorted(scores, reverse=True)

def test_dictionary_bonus_present():
    # Ensure dictionary exists and includes our seed words
    assert "FLOWERS" in WORDS