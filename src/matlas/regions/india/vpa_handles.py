# Well-known UPI PSP handle suffixes -> issuing bank/PSP name. This is a
# curated subset of widely-documented handles, not NPCI's full certified
# list (no authoritative machine-readable source to verify against, same
# constraint noted in the design spec for India generally).
VPA_HANDLE_TO_BANK: dict[str, str] = {
    "okhdfcbank": "HDFC Bank",
    "okaxis": "Axis Bank",
    "oksbi": "State Bank of India",
    "okicici": "ICICI Bank",
    "ybl": "Yes Bank",
    "ibl": "IDBI Bank",
    "axl": "Axis Bank",
    "paytm": "Paytm Payments Bank",
    "apl": "Amazon Pay (Axis Bank)",
    "upi": "BHIM/NPCI",
    "icici": "ICICI Bank",
    "sbi": "State Bank of India",
    "hdfcbank": "HDFC Bank",
    "axisbank": "Axis Bank",
    "kotak": "Kotak Mahindra Bank",
    "yesbank": "Yes Bank",
    "idfcfirst": "IDFC First Bank",
    "pnb": "Punjab National Bank",
    "unionbank": "Union Bank of India",
    "cnrb": "Canara Bank",
    "indus": "IndusInd Bank",
    "federal": "Federal Bank",
    "rbl": "RBL Bank",
    "boi": "Bank of India",
}


def bank_for_handle(vpa: str) -> str | None:
    suffix = vpa.rsplit("@", 1)[-1].lower()
    return VPA_HANDLE_TO_BANK.get(suffix)
