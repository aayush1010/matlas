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


def test_enrich_csv_writes_enriched_columns(monkeypatch, tmp_path):
    import matlas.batch as batch_module

    def fake_tiered(descriptor, settings, packs, region_override=None):
        return EnrichedTransaction(
            raw=descriptor,
            region="US",
            rail="card",
            merchant="Starbucks",
            category="food_and_drink",
            confidence=0.9,
            consistency_check_applicable=True,
            consistency_ok=True,
            evidence=[],
            is_unknown=False,
        )

    monkeypatch.setattr(batch_module, "enrich_one_tiered", fake_tiered)
    src = tmp_path / "txns.csv"
    src.write_text("date,descriptor\n2026-01-01,SQ *STARBUCKS #4521\n")
    result = runner.invoke(cli_module.app, ["enrich-csv", str(src)])
    assert result.exit_code == 0, result.output
    out = (tmp_path / "txns.enriched.csv").read_text()
    assert "merchant" in out.splitlines()[0]
    assert "Starbucks" in out and "food_and_drink" in out and "2026-01-01" in out


def test_enrich_csv_rejects_missing_column(tmp_path):
    src = tmp_path / "txns.csv"
    src.write_text("date,amount\n2026-01-01,4.50\n")
    result = runner.invoke(cli_module.app, ["enrich-csv", str(src)])
    assert result.exit_code != 0
    assert "descriptor" in result.output
