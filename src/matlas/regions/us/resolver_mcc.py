import json
from pathlib import Path

from rapidfuzz import fuzz, process

from matlas.core.shared_category import SharedCategory
from matlas.regions.base import Gazetteer, NormalizedTxn, ResolvedSignal

_GAZETTEER_PATH = Path(__file__).parent / "gazetteer.us.jsonl"
FUZZY_THRESHOLD = 85


def load_gazetteer(path: Path = _GAZETTEER_PATH) -> tuple[Gazetteer, dict[str, str]]:
    """Returns the Protocol-facing Gazetteer plus a key->MCC side table
    (base.Gazetteer's shape doesn't carry MCC, only canonical name + category)."""
    entries: dict[str, tuple[str, SharedCategory]] = {}
    key_to_mcc: dict[str, str] = {}
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            key = row["key"].lower()
            entries[key] = (row["canonical"], SharedCategory(row["category"]))
            key_to_mcc[key] = row["mcc"]
    return Gazetteer(entries), key_to_mcc


class USResolver:
    """Deterministic MCC resolver: gazetteer exact lookup -> rapidfuzz fuzzy
    fallback -> UNKNOWN. This is the "tool call" that resolves MCC even in
    the US (per the core insight) — never an LLM guess."""

    def __init__(self, gazetteer: Gazetteer, key_to_mcc: dict[str, str]):
        self.gazetteer = gazetteer
        self.key_to_mcc = key_to_mcc

    def resolve(self, n: NormalizedTxn) -> ResolvedSignal:
        key = n.merchant_str.lower()

        hit = self.gazetteer.lookup(key)
        if hit is not None:
            canonical, category = hit
            return ResolvedSignal(
                merchant_type=canonical,
                mcc=self.key_to_mcc[key],
                category=category,
                source="gazetteer_exact",
                confidence=1.0,
            )

        match = process.extractOne(key, self.gazetteer.entries.keys(), scorer=fuzz.WRatio)
        if match is not None and match[1] >= FUZZY_THRESHOLD:
            matched_key = match[0]
            canonical, category = self.gazetteer.entries[matched_key]
            return ResolvedSignal(
                merchant_type=canonical,
                mcc=self.key_to_mcc[matched_key],
                category=category,
                source="gazetteer_fuzzy",
                confidence=match[1] / 100,
            )

        return ResolvedSignal(
            merchant_type="unknown",
            mcc=None,
            category=SharedCategory.UNKNOWN,
            source="unknown",
            confidence=0.0,
        )
