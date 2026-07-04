from matlas.core.shared_category import SharedCategory
from matlas.regions.base import NormalizedTxn
from matlas.regions.us.resolver_mcc import USResolver, load_gazetteer


def _resolver():
    gazetteer, key_to_mcc = load_gazetteer()
    return USResolver(gazetteer, key_to_mcc)


def test_exact_match():
    r = _resolver()
    result = r.resolve(NormalizedTxn(rail="card", merchant_str="STARBUCKS"))
    assert result.merchant_type == "Starbucks"
    assert result.mcc == "5814"
    assert result.category is SharedCategory.FOOD_AND_DRINK
    assert result.source == "gazetteer_exact"
    assert result.confidence == 1.0


def test_fuzzy_match():
    r = _resolver()
    result = r.resolve(NormalizedTxn(rail="card", merchant_str="WHOLE FOODS MKT"))
    assert result.merchant_type == "Whole Foods Market"
    assert result.mcc == "5411"
    assert result.source == "gazetteer_fuzzy"
    assert result.confidence >= 0.85


def test_unknown_merchant():
    r = _resolver()
    result = r.resolve(NormalizedTxn(rail="card", merchant_str="TOTALLY UNKNOWN MERCHANT XYZ"))
    assert result.category is SharedCategory.UNKNOWN
    assert result.mcc is None
    assert result.source == "unknown"
    assert result.confidence == 0.0
