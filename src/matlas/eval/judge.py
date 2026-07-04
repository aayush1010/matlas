def exact_match_judge(predicted: str, expected: str) -> bool:
    # ponytail: exact-match only for Week 1 — gold set has unambiguous canonical
    # names. Upgrade to an LLM-based fuzzy judge if/when the gold set grows messier.
    return predicted.strip().lower() == expected.strip().lower()
