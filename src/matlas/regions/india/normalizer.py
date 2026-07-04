from matlas.regions.base import NormalizedTxn

# Two narration shapes seen in Indian bank/UPI statements, both variable-length
# once slash-split:
#   merchant payment (6 fields): "UPI/DR/408.../SWIGGY/YESB/Payment for order"
#   P2P transfer (5 fields):     "UPI/DR/512.../rahul.verma@okhdfcbank/Payment"


def normalize_india(raw: str) -> NormalizedTxn:
    s = raw.strip()
    parts = s.split("/")

    if len(parts) < 5 or parts[0].upper() != "UPI" or parts[1].upper() not in ("DR", "CR"):
        return NormalizedTxn(rail="UPI", merchant_str=s, refs=[], remark=raw)

    ref = parts[2]
    payee = parts[3]

    if "@" in payee:
        counterparty_id = payee
        merchant_str = payee.split("@", 1)[0]
        remark = "/".join(parts[4:]).strip()
        refs = [ref]
    else:
        counterparty_id = None
        merchant_str = payee
        handle_or_bank = parts[4] if len(parts) > 4 else None
        remark = "/".join(parts[5:]).strip()
        refs = [ref] + ([handle_or_bank] if handle_or_bank else [])

    return NormalizedTxn(
        rail="UPI",
        merchant_str=merchant_str,
        counterparty_id=counterparty_id,
        refs=refs,
        remark=remark or raw,
    )
