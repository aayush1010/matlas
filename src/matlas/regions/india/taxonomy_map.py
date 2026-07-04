from matlas.core.shared_category import SharedCategory

# India has no MCC-equivalent standard code to translate from, so the
# gazetteer already stores SharedCategory values directly — this map is an
# identity lookup (plus PERSONAL_TRANSFER for the P2P carve-out, which never
# appears in the merchant gazetteer itself).
INDIA_CATEGORY_TO_SHARED: dict[str, SharedCategory] = {
    category.value: category
    for category in (
        SharedCategory.FOOD_AND_DRINK,
        SharedCategory.TRANSPORTATION,
        SharedCategory.ENTERTAINMENT,
        SharedCategory.GENERAL_MERCHANDISE,
        SharedCategory.RENT_AND_UTILITIES,
        SharedCategory.TRAVEL,
        SharedCategory.MEDICAL,
        SharedCategory.PERSONAL_TRANSFER,
    )
}
