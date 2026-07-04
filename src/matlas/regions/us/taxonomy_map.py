from matlas.core.shared_category import SharedCategory

# Hand-maintained, covers only the MCCs present in the Week-1 gazetteer seed
# (data/regions/us/gazetteer.us.jsonl). Grow alongside the gazetteer, not ahead of it.
MCC_TO_SHARED_CATEGORY: dict[str, SharedCategory] = {
    "5814": SharedCategory.FOOD_AND_DRINK,
    "5411": SharedCategory.FOOD_AND_DRINK,
    "3058": SharedCategory.TRAVEL,
    "3000": SharedCategory.TRAVEL,
    "3509": SharedCategory.TRAVEL,
    "3504": SharedCategory.TRAVEL,
    "4121": SharedCategory.TRANSPORTATION,
    "5815": SharedCategory.ENTERTAINMENT,
    "5399": SharedCategory.GENERAL_MERCHANDISE,
    "5310": SharedCategory.GENERAL_MERCHANDISE,
    "5912": SharedCategory.MEDICAL,
    "4814": SharedCategory.RENT_AND_UTILITIES,
    "4899": SharedCategory.RENT_AND_UTILITIES,
    "5211": SharedCategory.HOME_IMPROVEMENT,
    "7230": SharedCategory.PERSONAL_CARE,
    "8398": SharedCategory.GOVERNMENT_AND_NON_PROFIT,
    "7276": SharedCategory.GENERAL_SERVICES,
    "7832": SharedCategory.ENTERTAINMENT,
    "5300": SharedCategory.GENERAL_MERCHANDISE,
    "5311": SharedCategory.GENERAL_MERCHANDISE,
    "5541": SharedCategory.TRANSPORTATION,
    "5732": SharedCategory.GENERAL_MERCHANDISE,
    "5812": SharedCategory.FOOD_AND_DRINK,
}
