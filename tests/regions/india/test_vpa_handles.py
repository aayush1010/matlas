from matlas.regions.india.vpa_handles import bank_for_handle


def test_known_handle_resolves_bank():
    assert bank_for_handle("swiggy@ybl") == "Yes Bank"
    assert bank_for_handle("rahul.verma@okhdfcbank") == "HDFC Bank"


def test_unknown_handle_returns_none():
    assert bank_for_handle("someone@totallymadeup") is None


def test_case_insensitive():
    assert bank_for_handle("someone@YBL") == "Yes Bank"
