from matlas.regions.india.normalizer import normalize_india


def test_merchant_payment_narration():
    n = normalize_india("UPI/DR/408123456789/SWIGGY/YESB/Payment for order")
    assert n.rail == "UPI"
    assert n.merchant_str == "SWIGGY"
    assert n.counterparty_id is None
    assert n.remark == "Payment for order"


def test_p2p_vpa_narration():
    n = normalize_india("UPI/DR/512987654321/rahul.verma@okhdfcbank/Payment")
    assert n.rail == "UPI"
    assert n.merchant_str == "rahul.verma"
    assert n.counterparty_id == "rahul.verma@okhdfcbank"


def test_credit_transaction_type():
    n = normalize_india("UPI/CR/999000111222/ZOMATO/PYTM/Refund")
    assert n.merchant_str == "ZOMATO"


def test_unrecognized_format_falls_back_to_raw():
    n = normalize_india("some random narration")
    assert n.merchant_str == "some random narration"
    assert n.counterparty_id is None
