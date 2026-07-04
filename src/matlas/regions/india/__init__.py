import re

from matlas.regions.base import NormalizedTxn, ResolvedSignal, Taxonomy
from matlas.regions.india.normalizer import normalize_india
from matlas.regions.india.resolver_vpa import IndiaResolver, load_gazetteer
from matlas.regions.india.taxonomy_map import INDIA_CATEGORY_TO_SHARED

_UPI_PREFIX_RE = re.compile(r"^UPI/", re.IGNORECASE)


class IndiaRegionPack:
    region_code = "IN"

    def __init__(self) -> None:
        self.gazetteer = load_gazetteer()
        self.taxonomy = Taxonomy(dict(INDIA_CATEGORY_TO_SHARED))
        self._resolver = IndiaResolver(self.gazetteer)

    def detect(self, raw: str) -> float:
        if _UPI_PREFIX_RE.match(raw.strip()):
            return 0.9
        if "@" in raw:
            return 0.7
        return 0.1

    def normalize(self, raw: str) -> NormalizedTxn:
        return normalize_india(raw)

    def resolve(self, n: NormalizedTxn) -> ResolvedSignal:
        return self._resolver.resolve(n)

    def consistency_applicable(self, n: NormalizedTxn) -> bool:
        # ponytail: proxy for "looks like a P2P narration" is "the narration
        # exposed a real VPA in the payee slot" (our two narration shapes map
        # 1:1 to merchant-vs-P2P today). Ceiling: a merchant that shows its own
        # VPA instead of a bank-code shorthand would also read as P2P here —
        # revisit if that shape shows up in real data.
        return n.counterparty_id is None
