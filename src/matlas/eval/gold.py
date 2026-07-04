import json
from pathlib import Path

from pydantic import BaseModel

_US_GOLD_PATH = Path(__file__).parent.parent / "regions" / "us" / "gazetteer.us.jsonl"
_INDIA_GOLD_PATH = Path(__file__).parent.parent / "regions" / "india" / "gazetteer.in.jsonl"


class GoldRow(BaseModel):
    raw: str
    merchant: str
    category: str
    mcc: str | None = None


def _load(path: Path) -> list[GoldRow]:
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            rows.append(
                GoldRow(
                    raw=row["key"],
                    merchant=row["canonical"],
                    category=row["category"],
                    mcc=row.get("mcc"),
                )
            )
    return rows


def load_gold(path: Path = _US_GOLD_PATH) -> list[GoldRow]:
    """The US gazetteer doubles as the Week-1 gold set — its `key` values are
    already-normalized descriptors, close enough to raw input for benchmarking
    without a second hand-curated dataset."""
    return _load(path)


def load_gold_india(path: Path = _INDIA_GOLD_PATH) -> list[GoldRow]:
    """India gazetteer doubles as a portability smoke-test set, same pattern as
    US — but this is NOT a validated accuracy benchmark (no MCC-equivalent
    ground truth exists for India, per the design spec's honest-portability
    stance). Callers must label results as a smoke test, never an accuracy claim."""
    return _load(path)
