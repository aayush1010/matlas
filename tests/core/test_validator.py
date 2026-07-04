from matlas.core.shared_category import SharedCategory
from matlas.core.validator import validate
from matlas.regions.base import ResolvedSignal


def _resolved(category, confidence, mcc="5814"):
    return ResolvedSignal(
        merchant_type="Starbucks",
        mcc=mcc,
        category=category,
        source="gazetteer_exact",
        confidence=confidence,
    )


def test_not_applicable_trusts_proposal_no_retry():
    result = validate(
        SharedCategory.PERSONAL_TRANSFER,
        0.9,
        _resolved(SharedCategory.UNKNOWN, 0.0, mcc=None),
        consistency_applicable=False,
    )
    assert result.final_category is SharedCategory.PERSONAL_TRANSFER
    assert result.final_confidence == 0.9
    assert result.should_retry is False


def test_agreement_merges_confidence_no_retry():
    result = validate(
        SharedCategory.FOOD_AND_DRINK,
        0.8,
        _resolved(SharedCategory.FOOD_AND_DRINK, 1.0),
        consistency_applicable=True,
    )
    assert result.final_category is SharedCategory.FOOD_AND_DRINK
    assert result.final_confidence == 0.9
    assert result.should_retry is False


def test_contradiction_high_resolver_confidence_triggers_retry():
    result = validate(
        SharedCategory.GENERAL_MERCHANDISE,
        0.8,
        _resolved(SharedCategory.FOOD_AND_DRINK, 1.0),
        consistency_applicable=True,
    )
    assert result.final_category is SharedCategory.FOOD_AND_DRINK
    assert result.final_confidence == 0.5
    assert result.should_retry is True


def test_contradiction_low_resolver_confidence_keeps_proposal_no_retry():
    result = validate(
        SharedCategory.GENERAL_MERCHANDISE,
        0.8,
        _resolved(SharedCategory.FOOD_AND_DRINK, 0.3),
        consistency_applicable=True,
    )
    assert result.final_category is SharedCategory.GENERAL_MERCHANDISE
    assert result.final_confidence == 0.4
    assert result.should_retry is False
