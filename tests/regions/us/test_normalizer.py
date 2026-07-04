import pytest

from matlas.regions.us.normalizer import normalize_us

CASES = [
    ("SQ *STARBUCKS #4521 SEATTLE WA", "STARBUCKS"),
    ("SQ *COFFEE 0432 SAN FRAN CA", "COFFEE"),
    ("TST* BLUE BOTTLE", "BLUE BOTTLE"),
    ("WHOLE FOODS MKT #10245 AUSTIN TX", "WHOLE FOODS MKT"),
    ("TRADER JOE'S #142", "TRADER JOE'S"),
    ("UBER   TRIP HELP.UBER.COM", "UBER TRIP"),
    ("NETFLIX.COM", "NETFLIX.COM"),
    ("AT&T*BILL PAYMENT", "AT&T*BILL PAYMENT"),
    ("COMCAST CABLE COMM", "COMCAST CABLE COMM"),
    ("TARGET #00456 MINNEAPOLIS MN", "TARGET"),
    ("PAYPAL *SPOTIFY USA", "SPOTIFY USA"),
    ("CVS/PHARM #3021 CHICAGO IL", "CVS/PHARM"),
]


@pytest.mark.parametrize("raw,expected", CASES)
def test_normalize_us(raw, expected):
    result = normalize_us(raw)
    assert result.merchant_str == expected
    assert result.rail == "card"
    assert result.remark == raw
