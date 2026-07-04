import json
from pathlib import Path

from matlas.core.shared_category import SharedCategory
from matlas.regions.india.taxonomy_map import INDIA_CATEGORY_TO_SHARED

GAZETTEER_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "src"
    / "matlas"
    / "regions"
    / "india"
    / "gazetteer.in.jsonl"
)


def _gazetteer_rows():
    with GAZETTEER_PATH.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def test_every_gazetteer_category_has_taxonomy_entry():
    categories = {row["category"] for row in _gazetteer_rows()}
    missing = categories - INDIA_CATEGORY_TO_SHARED.keys()
    assert not missing, f"categories in gazetteer with no taxonomy_map entry: {missing}"


def test_personal_transfer_entry_present_for_p2p_carveout():
    assert INDIA_CATEGORY_TO_SHARED["personal_transfer"] is SharedCategory.PERSONAL_TRANSFER


def test_taxonomy_map_agrees_with_gazetteer_categories():
    for row in _gazetteer_rows():
        expected = SharedCategory(row["category"])
        assert INDIA_CATEGORY_TO_SHARED[row["category"]] == expected, row
