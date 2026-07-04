from fastapi.testclient import TestClient

import matlas.api as api_module
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


client = TestClient(api_module.app)


def test_healthz():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_enrich(monkeypatch):
    monkeypatch.setattr(api_module, "EnrichmentAgent", _FakeAgent)
    resp = client.post("/enrich", json={"descriptor": "SQ *STARBUCKS #4521 SEATTLE WA"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["merchant"] == "Starbucks"
    assert body["region"] == "US"


def test_enrich_with_region_override(monkeypatch):
    monkeypatch.setattr(api_module, "EnrichmentAgent", _FakeAgent)
    resp = client.post(
        "/enrich", json={"descriptor": "UPI/DR/408123456789/SWIGGY/YESB/Payment", "region": "india"}
    )
    assert resp.status_code == 200
    assert resp.json()["region"] == "IN"


def test_enrich_invalid_region_returns_400(monkeypatch):
    monkeypatch.setattr(api_module, "EnrichmentAgent", _FakeAgent)
    resp = client.post("/enrich", json={"descriptor": "whatever", "region": "mars"})
    assert resp.status_code == 400


def test_enrich_batch(monkeypatch):
    monkeypatch.setattr(api_module, "EnrichmentAgent", _FakeAgent)
    resp = client.post(
        "/enrich/batch",
        json={"descriptors": ["SQ *STARBUCKS #4521 SEATTLE WA", "SQ *COFFEE 0432 SAN FRAN CA"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert all(row["merchant"] == "Starbucks" for row in body)
