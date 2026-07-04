from matlas.core.shared_category import SharedCategory
from matlas.regions.india import IndiaRegionPack


def _pack():
    return IndiaRegionPack()


def test_full_pipeline_merchant():
    pack = _pack()
    n = pack.normalize("UPI/DR/408123456789/SWIGGY/YESB/Payment for order")
    result = pack.resolve(n)
    assert result.merchant_type == "Swiggy"
    assert result.category is SharedCategory.FOOD_AND_DRINK


def test_full_pipeline_p2p():
    pack = _pack()
    n = pack.normalize("UPI/DR/512987654321/rahul.verma@okhdfcbank/Payment")
    result = pack.resolve(n)
    assert result.category is SharedCategory.PERSONAL_TRANSFER


def test_detect_high_for_upi_narration():
    pack = _pack()
    assert pack.detect("UPI/DR/408123456789/SWIGGY/YESB/Payment") >= 0.9


def test_detect_low_for_us_card_descriptor():
    pack = _pack()
    assert pack.detect("SQ *STARBUCKS #4521 SEATTLE WA") <= 0.1


def test_consistency_applicable_true_for_merchant_payment():
    pack = _pack()
    n = pack.normalize("UPI/DR/408123456789/SWIGGY/YESB/Payment for order")
    assert pack.consistency_applicable(n) is True


def test_consistency_applicable_false_for_p2p():
    pack = _pack()
    n = pack.normalize("UPI/DR/512987654321/rahul.verma@okhdfcbank/Payment")
    assert pack.consistency_applicable(n) is False
