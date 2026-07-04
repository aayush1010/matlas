import iso18245


def mcc_info(code: str) -> iso18245.MCC:
    return iso18245.get_mcc(code)


def mcc_in_travel_range(code: str) -> bool:
    return 3000 <= int(code) <= 3999
