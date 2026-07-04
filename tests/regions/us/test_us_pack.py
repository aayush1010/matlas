from matlas.core.shared_category import SharedCategory
from matlas.regions.us import USRegionPack


def test_full_pipeline_on_seed_merchants():
    pack = USRegionPack()
    cases = [
        ("SQ *STARBUCKS #4521 SEATTLE WA", "Starbucks", "5814", SharedCategory.FOOD_AND_DRINK),
        ("TARGET #00456 MINNEAPOLIS MN", "Target", "5310", SharedCategory.GENERAL_MERCHANDISE),
        ("NETFLIX.COM", "Netflix", "5815", SharedCategory.ENTERTAINMENT),
        ("AT&T*BILL PAYMENT", "AT&T", "4814", SharedCategory.RENT_AND_UTILITIES),
    ]
    for raw, merchant, mcc, category in cases:
        n = pack.normalize(raw)
        resolved = pack.resolve(n)
        assert resolved.merchant_type == merchant
        assert resolved.mcc == mcc
        assert resolved.category is category


def test_detect_high_confidence_for_card_descriptor():
    pack = USRegionPack()
    assert pack.detect("SQ *STARBUCKS #4521 SEATTLE WA") >= 0.5


def test_detect_low_confidence_for_upi_handle():
    pack = USRegionPack()
    assert pack.detect("UPI/DR/408.../SWIGGY/YESB/Payment user@ybl") < 0.5


def test_consistency_not_applicable_for_atm_withdrawal():
    pack = USRegionPack()
    n = pack.normalize("ATM WITHDRAWAL CHASE BANK NYC NY")
    assert pack.consistency_applicable(n) is False


def test_consistency_applicable_for_normal_purchase():
    pack = USRegionPack()
    n = pack.normalize("SQ *STARBUCKS #4521 SEATTLE WA")
    assert pack.consistency_applicable(n) is True
