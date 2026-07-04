import json
from pathlib import Path

from rapidfuzz import fuzz, process

from matlas.core.shared_category import SharedCategory
from matlas.regions.base import Gazetteer, NormalizedTxn, ResolvedSignal

_GAZETTEER_PATH = Path(__file__).parent / "gazetteer.in.jsonl"
FUZZY_THRESHOLD = 85


def load_gazetteer(path: Path = _GAZETTEER_PATH) -> Gazetteer:
    entries: dict[str, tuple[str, SharedCategory]] = {}
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            entries[row["key"].lower()] = (row["canonical"], SharedCategory(row["category"]))
    return Gazetteer(entries)


class IndiaResolver:
    """Two-stage resolver: merchant gazetteer (exact -> fuzzy) first; if no
    merchant match and the counterparty is a real VPA (person's UPI ID, not
    a known merchant/aggregator), fall back to PERSONAL_TRANSFER — the P2P
    carve-out, since there's no MCC-equivalent to cross-check a person's
    handle against."""

    def __init__(self, gazetteer: Gazetteer):
        self.gazetteer = gazetteer

    def resolve(self, n: NormalizedTxn) -> ResolvedSignal:
        key = n.merchant_str.lower()

        hit = self.gazetteer.lookup(key)
        if hit is not None:
            canonical, category = hit
            return ResolvedSignal(
                merchant_type=canonical, mcc=None, category=category,
                source="gazetteer_exact", confidence=1.0,
            )

        match = process.extractOne(key, self.gazetteer.entries.keys(), scorer=fuzz.WRatio)
        if match is not None and match[1] >= FUZZY_THRESHOLD:
            canonical, category = self.gazetteer.entries[match[0]]
            return ResolvedSignal(
                merchant_type=canonical, mcc=None, category=category,
                source="gazetteer_fuzzy", confidence=match[1] / 100,
            )

        if n.counterparty_id and "@" in n.counterparty_id:
            return ResolvedSignal(
                merchant_type=n.merchant_str, mcc=None, category=SharedCategory.PERSONAL_TRANSFER,
                source="p2p_heuristic", confidence=0.8,
            )

        return ResolvedSignal(
            merchant_type="unknown", mcc=None, category=SharedCategory.UNKNOWN,
            source="unknown", confidence=0.0,
        )
