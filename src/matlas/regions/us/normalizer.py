import re

from cleanco import basename

from matlas.regions.base import NormalizedTxn

_POS_PREFIX_RE = re.compile(r"^(SQ \*|SQ\*|TST\*\s?|PAYPAL \*|PP\*)", re.IGNORECASE)
_URL_SUFFIX_RE = re.compile(r"(?<=\S)\s+[A-Z0-9.-]+\.(?:COM|NET|ORG)\s*$", re.IGNORECASE)
_TRAILING_CITY_STATE_RE = re.compile(r"\s+[A-Z][A-Za-z.' -]*\s+[A-Z]{2}$")
_TRAILING_STORE_ID_RE = re.compile(r"\s+#?\d{3,6}$")


def normalize_us(raw: str) -> NormalizedTxn:
    """Strip POS-processor prefixes, URL suffixes, trailing city/state, and
    trailing store IDs, then collapse whitespace and strip legal suffixes
    (Inc/LLC/Corp) via cleanco. Doesn't attempt full merchant-name equivalence
    (e.g. apostrophes, abbreviations) — that's the resolver's fuzzy-match job.
    """
    s = raw.strip()
    s = _POS_PREFIX_RE.sub("", s)
    s = _URL_SUFFIX_RE.sub("", s)
    s = _TRAILING_CITY_STATE_RE.sub("", s)
    s = _TRAILING_STORE_ID_RE.sub("", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = basename(s) or s
    return NormalizedTxn(rail="card", merchant_str=s, refs=[], remark=raw)
