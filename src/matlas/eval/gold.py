import json
from pathlib import Path

from pydantic import BaseModel

_GOLD_PATH = Path(__file__).parent.parent / "regions" / "us" / "gazetteer.us.jsonl"


class GoldRow(BaseModel):
    raw: str
    merchant: str
    category: str
    mcc: str


def load_gold(path: Path = _GOLD_PATH) -> list[GoldRow]:
    """The US gazetteer doubles as the Week-1 gold set — its `key` values are
    already-normalized descriptors, close enough to raw input for benchmarking
    without a second hand-curated dataset."""
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
                    mcc=row["mcc"],
                )
            )
    return rows
