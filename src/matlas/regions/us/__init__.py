import re

from matlas.regions.base import NormalizedTxn, ResolvedSignal, Taxonomy
from matlas.regions.us.normalizer import normalize_us
from matlas.regions.us.resolver_mcc import USResolver, load_gazetteer
from matlas.regions.us.taxonomy_map import MCC_TO_SHARED_CATEGORY

_VPA_HANDLE_RE = re.compile(r"@[a-z]+", re.IGNORECASE)
_ATM_KEYWORDS = ("ATM WITHDRAWAL", "ATM DEBIT")
_TRANSFER_KEYWORDS = ("TRANSFER TO", "TRANSFER FROM", "SELF TRANSFER")


class USRegionPack:
    region_code = "US"

    def __init__(self) -> None:
        gazetteer, key_to_mcc = load_gazetteer()
        self.gazetteer = gazetteer
        self.taxonomy = Taxonomy(dict(MCC_TO_SHARED_CATEGORY))
        self._resolver = USResolver(gazetteer, key_to_mcc)

    def detect(self, raw: str) -> float:
        # India detection doesn't need to exist yet — this just needs to not
        # misfire against US card descriptors.
        if _VPA_HANDLE_RE.search(raw):
            return 0.1
        return 0.9

    def normalize(self, raw: str) -> NormalizedTxn:
        return normalize_us(raw)

    def resolve(self, n: NormalizedTxn) -> ResolvedSignal:
        return self._resolver.resolve(n)

    def consistency_applicable(self, n: NormalizedTxn) -> bool:
        raw = (n.remark or n.merchant_str).upper()
        if any(kw in raw for kw in _ATM_KEYWORDS):
            return False
        if any(kw in raw for kw in _TRANSFER_KEYWORDS):
            return False
        return True
