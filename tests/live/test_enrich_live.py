import os

import pytest

from matlas.config import Settings
from matlas.core.loop import EnrichmentAgent
from matlas.regions.us import USRegionPack

RAW = "SQ *STARBUCKS #4521 SEATTLE WA"


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live API smoke test",
)
def test_enrich_starbucks_against_real_api():
    agent = EnrichmentAgent(USRegionPack(), Settings())
    result = agent.run(RAW, "US")
    assert result.merchant.lower() == "starbucks"
    assert result.category.value == "food_and_drink"
    assert result.is_unknown is False
