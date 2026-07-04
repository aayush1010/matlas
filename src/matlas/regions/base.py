from typing import Protocol

from pydantic import BaseModel

from matlas.core.shared_category import SharedCategory


class NormalizedTxn(BaseModel):
    rail: str
    merchant_str: str
    counterparty_id: str | None = None
    refs: list[str] = []
    remark: str | None = None


class ResolvedSignal(BaseModel):
    merchant_type: str
    mcc: str | None
    category: SharedCategory
    source: str
    confidence: float


class Gazetteer:
    """Dict-backed merchant/VPA -> (canonical name, category) lookup."""

    def __init__(self, entries: dict[str, tuple[str, SharedCategory]]):
        self.entries = entries

    def lookup(self, key: str) -> tuple[str, SharedCategory] | None:
        return self.entries.get(key.lower())


class Taxonomy:
    """Region category string -> SharedCategory."""

    def __init__(self, region_to_shared: dict[str, SharedCategory]):
        self.region_to_shared = region_to_shared

    def map(self, region_category: str) -> SharedCategory:
        return self.region_to_shared.get(region_category, SharedCategory.UNKNOWN)


class RegionPack(Protocol):
    region_code: str  # "US", "IN"
    gazetteer: Gazetteer
    taxonomy: Taxonomy

    def detect(self, raw: str) -> float:
        """0..1 confidence this pack owns this descriptor."""
        ...

    def normalize(self, raw: str) -> NormalizedTxn: ...

    def resolve(self, n: NormalizedTxn) -> ResolvedSignal: ...

    def consistency_applicable(self, n: NormalizedTxn) -> bool:
        """False for P2P/ATM/self-transfer."""
        ...
