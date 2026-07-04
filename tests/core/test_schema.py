import json

import pytest
from pydantic import ValidationError

from matlas.core.schema import EnrichedTransaction, Evidence
from matlas.core.shared_category import SharedCategory


def _minimal():
    return EnrichedTransaction(
        raw="SQ *COFFEE 0432 SAN FRAN CA",
        region="US",
        rail="card",
        merchant="Square — Coffee",
        category=SharedCategory.FOOD_AND_DRINK,
        confidence=0.92,
        consistency_check_applicable=True,
        consistency_ok=True,
        evidence=[Evidence(source="resolver", detail="mcc:5814", confidence=1.0)],
        is_unknown=False,
    )


def test_construct_minimal_valid():
    txn = _minimal()
    assert txn.category is SharedCategory.FOOD_AND_DRINK


def test_rejects_invalid_category():
    with pytest.raises(ValidationError):
        EnrichedTransaction(
            raw="x",
            region="US",
            rail="card",
            merchant="x",
            category="not_a_real_category",
            confidence=0.5,
            consistency_check_applicable=False,
            consistency_ok=None,
            evidence=[],
            is_unknown=False,
        )


def test_json_round_trip():
    txn = _minimal()
    dumped = txn.model_dump_json()
    restored = EnrichedTransaction.model_validate(json.loads(dumped))
    assert restored == txn
