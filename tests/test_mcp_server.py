import matlas.mcp_server as mcp_module
from matlas.core.schema import EnrichedTransaction


class _FakeAgent:
    def __init__(self, pack, settings, client=None):
        pass

    def run(self, raw, region):
        return EnrichedTransaction(
            raw=raw,
            region=region,
            rail="card",
            merchant="Starbucks",
            category="food_and_drink",
            confidence=0.9,
            consistency_check_applicable=True,
            consistency_ok=True,
            evidence=[],
            is_unknown=False,
        )


def test_enrich_tool(monkeypatch):
    monkeypatch.setattr(mcp_module, "EnrichmentAgent", _FakeAgent)
    result = mcp_module.enrich("SQ *STARBUCKS #4521 SEATTLE WA")
    assert result["merchant"] == "Starbucks"
    assert result["region"] == "US"


def test_enrich_tool_india_override(monkeypatch):
    monkeypatch.setattr(mcp_module, "EnrichmentAgent", _FakeAgent)
    result = mcp_module.enrich("UPI/DR/408123456789/SWIGGY/YESB/Payment", region="india")
    assert result["region"] == "IN"
