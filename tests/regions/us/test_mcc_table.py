from matlas.regions.us.mcc_table import mcc_in_travel_range, mcc_info


def test_mcc_info_matches_installed_package():
    info = mcc_info("5814")
    assert info == mcc_info("5814")
    assert info.mcc == "5814"
    assert "fast food" in (info.iso_description or "").lower()


def test_mcc_in_travel_range():
    assert mcc_in_travel_range("3000") is True
    assert mcc_in_travel_range("3999") is True
    assert mcc_in_travel_range("5814") is False
