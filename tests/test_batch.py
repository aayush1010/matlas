import matlas.batch as batch_module
from matlas.config import Settings
from matlas.core.schema import EnrichedTransaction
from matlas.regions.us import USRegionPack

PACKS = [USRegionPack()]


class _FakeAgent:
    calls: list[str] = []

    def __init__(self, pack, settings, client=None):
        self._model = settings.model_hard

    def run(self, raw, region):
        _FakeAgent.calls.append(self._model)
        return EnrichedTransaction(
            raw=raw,
            region=region,
            rail="card",
            merchant="Cheap Result",
            category="food_and_drink",
            confidence=0.95,
            consistency_check_applicable=True,
            consistency_ok=True,
            evidence=[],
            is_unknown=False,
        )


def test_exact_gazetteer_hit_skips_llm_entirely(monkeypatch):
    monkeypatch.setattr(batch_module, "EnrichmentAgent", _FakeAgent)
    _FakeAgent.calls.clear()
    result = batch_module.enrich_one_tiered("starbucks", Settings(), PACKS)
    assert result.merchant == "Starbucks"
    assert result.evidence[0].source == "gazetteer"
    assert _FakeAgent.calls == []


def test_ambiguous_descriptor_confirmed_by_cheap_model(monkeypatch):
    monkeypatch.setattr(batch_module, "EnrichmentAgent", _FakeAgent)
    _FakeAgent.calls.clear()
    settings = Settings()
    result = batch_module.enrich_one_tiered("SOME RANDOM MERCHANT XYZ", settings, PACKS)
    assert result.merchant == "Cheap Result"
    assert _FakeAgent.calls == [settings.model_cheap]


def test_low_confidence_cheap_result_escalates_to_hard_model(monkeypatch):
    class _LowConfidenceThenHigh:
        calls: list[str] = []

        def __init__(self, pack, settings, client=None):
            self._model = settings.model_hard

        def run(self, raw, region):
            _LowConfidenceThenHigh.calls.append(self._model)
            confidence = 0.1 if len(_LowConfidenceThenHigh.calls) == 1 else 0.99
            return EnrichedTransaction(
                raw=raw,
                region=region,
                rail="card",
                merchant="Result",
                category="food_and_drink",
                confidence=confidence,
                consistency_check_applicable=True,
                consistency_ok=True,
                evidence=[],
                is_unknown=False,
            )

    monkeypatch.setattr(batch_module, "EnrichmentAgent", _LowConfidenceThenHigh)
    settings = Settings()
    result = batch_module.enrich_one_tiered("SOME RANDOM MERCHANT XYZ", settings, PACKS)
    assert result.confidence == 0.99
    assert _LowConfidenceThenHigh.calls == [settings.model_cheap, settings.model_hard]


def test_enrich_batch_tiered_runs_all(monkeypatch):
    monkeypatch.setattr(batch_module, "EnrichmentAgent", _FakeAgent)
    _FakeAgent.calls.clear()
    results = batch_module.enrich_batch_tiered(["starbucks", "SOME RANDOM MERCHANT XYZ"], Settings(), PACKS)
    assert len(results) == 2
    assert results[0].merchant == "Starbucks"
    assert results[1].merchant == "Cheap Result"
