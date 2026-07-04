from enum import Enum


class SharedCategory(str, Enum):
    """Region-agnostic category enum. The 16 Plaid PFC primary categories,
    plus two matlas-specific additions with no Plaid equivalent:
    PERSONAL_TRANSFER (India P2P / self-transfer carve-out) and UNKNOWN
    (validator fallback when nothing resolves).
    """

    INCOME = "income"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    PERSONAL_TRANSFER = "personal_transfer"
    LOAN_PAYMENTS = "loan_payments"
    BANK_FEES = "bank_fees"
    ENTERTAINMENT = "entertainment"
    FOOD_AND_DRINK = "food_and_drink"
    GENERAL_MERCHANDISE = "general_merchandise"
    HOME_IMPROVEMENT = "home_improvement"
    MEDICAL = "medical"
    PERSONAL_CARE = "personal_care"
    GENERAL_SERVICES = "general_services"
    GOVERNMENT_AND_NON_PROFIT = "government_and_non_profit"
    TRANSPORTATION = "transportation"
    TRAVEL = "travel"
    RENT_AND_UTILITIES = "rent_and_utilities"
    UNKNOWN = "unknown"
