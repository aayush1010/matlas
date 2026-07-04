import json

from typer.testing import CliRunner

import matlas.cli as cli_module
from matlas.core.schema import EnrichedTransaction

runner = CliRunner()


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


def test_enrich_command_outputs_json(monkeypatch):
    monkeypatch.setattr(cli_module, "EnrichmentAgent", _FakeAgent)
    result = runner.invoke(cli_module.app, ["enrich", "SQ *STARBUCKS #4521 SEATTLE WA"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["merchant"] == "Starbucks"
    assert payload["category"] == "food_and_drink"


def test_enrich_command_with_region_override(monkeypatch):
    monkeypatch.setattr(cli_module, "EnrichmentAgent", _FakeAgent)
    result = runner.invoke(
        cli_module.app, ["enrich", "SQ *STARBUCKS #4521 SEATTLE WA", "--region", "us"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["region"] == "US"


def test_enrich_command_with_india_region_override(monkeypatch):
    monkeypatch.setattr(cli_module, "EnrichmentAgent", _FakeAgent)
    result = runner.invoke(
        cli_module.app,
        ["enrich", "UPI/DR/408123456789/SWIGGY/YESB/Payment", "--region", "india"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["region"] == "IN"


def test_serve_requires_exactly_one_flag():
    result = runner.invoke(cli_module.app, ["serve"])
    assert result.exit_code != 0
    result = runner.invoke(cli_module.app, ["serve", "--api", "--mcp"])
    assert result.exit_code != 0


def test_serve_api_calls_uvicorn(monkeypatch):
    calls = {}
    monkeypatch.setattr(
        "uvicorn.run", lambda app, host, port: calls.update(host=host, port=port)
    )
    result = runner.invoke(cli_module.app, ["serve", "--api"])
    assert result.exit_code == 0
    assert calls == {"host": "127.0.0.1", "port": 8000}


def test_serve_mcp_calls_mcp_run(monkeypatch):
    called = {}
    monkeypatch.setattr(
        "matlas.mcp_server.mcp.run", lambda: called.setdefault("ran", True)
    )
    result = runner.invoke(cli_module.app, ["serve", "--mcp"])
    assert result.exit_code == 0
    assert called == {"ran": True}
