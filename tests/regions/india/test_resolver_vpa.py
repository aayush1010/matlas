from matlas.core.shared_category import SharedCategory
from matlas.regions.base import NormalizedTxn
from matlas.regions.india.resolver_vpa import IndiaResolver, load_gazetteer


def _resolver():
    return IndiaResolver(load_gazetteer())


def test_exact_merchant_match():
    r = _resolver()
    result = r.resolve(NormalizedTxn(rail="UPI", merchant_str="SWIGGY"))
    assert result.merchant_type == "Swiggy"
    assert result.category is SharedCategory.FOOD_AND_DRINK
    assert result.source == "gazetteer_exact"
    assert result.confidence == 1.0


def test_fuzzy_merchant_match():
    r = _resolver()
    result = r.resolve(NormalizedTxn(rail="UPI", merchant_str="SWIGGY LTD"))
    assert result.merchant_type == "Swiggy"
    assert result.source == "gazetteer_fuzzy"
    assert result.confidence >= 0.85


def test_p2p_vpa_falls_back_to_personal_transfer():
    r = _resolver()
    n = NormalizedTxn(
        rail="UPI",
        merchant_str="rahul.verma",
        counterparty_id="rahul.verma@okhdfcbank",
    )
    result = r.resolve(n)
    assert result.category is SharedCategory.PERSONAL_TRANSFER
    assert result.source == "p2p_heuristic"
    assert result.confidence == 0.8


def test_unknown_with_no_vpa_counterparty():
    r = _resolver()
    result = r.resolve(NormalizedTxn(rail="UPI", merchant_str="TOTALLY UNKNOWN BIZ"))
    assert result.category is SharedCategory.UNKNOWN
    assert result.source == "unknown"
    assert result.confidence == 0.0
