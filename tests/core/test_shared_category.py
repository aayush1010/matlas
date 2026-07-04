from matlas.core.shared_category import SharedCategory

EXPECTED_MEMBERS = {
    "INCOME",
    "TRANSFER_IN",
    "TRANSFER_OUT",
    "PERSONAL_TRANSFER",
    "LOAN_PAYMENTS",
    "BANK_FEES",
    "ENTERTAINMENT",
    "FOOD_AND_DRINK",
    "GENERAL_MERCHANDISE",
    "HOME_IMPROVEMENT",
    "MEDICAL",
    "PERSONAL_CARE",
    "GENERAL_SERVICES",
    "GOVERNMENT_AND_NON_PROFIT",
    "TRANSPORTATION",
    "TRAVEL",
    "RENT_AND_UTILITIES",
    "UNKNOWN",
}


def test_exact_membership():
    assert {m.name for m in SharedCategory} == EXPECTED_MEMBERS


def test_values_lowercase_snake():
    for m in SharedCategory:
        assert m.value == m.value.lower()
        assert " " not in m.value


def test_round_trip():
    assert SharedCategory("food_and_drink") is SharedCategory.FOOD_AND_DRINK
