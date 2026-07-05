from matlas.eval.gold import load_gold, load_gold_india


def test_load_gold_returns_rows_matching_gazetteer():
    rows = load_gold()
    assert len(rows) == 330
    starbucks = next(r for r in rows if r.raw == "starbucks")
    assert starbucks.merchant == "Starbucks"
    assert starbucks.category == "food_and_drink"
    assert starbucks.mcc == "5814"


def test_load_gold_india_returns_rows_matching_gazetteer():
    rows = load_gold_india()
    assert len(rows) == 186
    swiggy = next(r for r in rows if r.raw == "swiggy")
    assert swiggy.merchant == "Swiggy"
    assert swiggy.category == "food_and_drink"
    assert swiggy.mcc is None
