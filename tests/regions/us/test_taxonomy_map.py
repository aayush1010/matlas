import json
from pathlib import Path

from matlas.core.shared_category import SharedCategory
from matlas.regions.us.taxonomy_map import MCC_TO_SHARED_CATEGORY

GAZETTEER_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "src"
    / "matlas"
    / "regions"
    / "us"
    / "gazetteer.us.jsonl"
)


def _gazetteer_rows():
    with GAZETTEER_PATH.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def test_every_gazetteer_mcc_has_taxonomy_entry():
    mccs = {row["mcc"] for row in _gazetteer_rows()}
    missing = mccs - MCC_TO_SHARED_CATEGORY.keys()
    assert not missing, f"MCCs in gazetteer with no taxonomy_map entry: {missing}"


def test_taxonomy_map_agrees_with_gazetteer_categories():
    for row in _gazetteer_rows():
        expected = SharedCategory(row["category"])
        assert MCC_TO_SHARED_CATEGORY[row["mcc"]] == expected, row
