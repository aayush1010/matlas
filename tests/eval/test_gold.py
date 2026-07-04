from matlas.eval.gold import load_gold


def test_load_gold_returns_rows_matching_gazetteer():
    rows = load_gold()
    assert len(rows) == 36
    starbucks = next(r for r in rows if r.raw == "starbucks")
    assert starbucks.merchant == "Starbucks"
    assert starbucks.category == "food_and_drink"
    assert starbucks.mcc == "5814"
