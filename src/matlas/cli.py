import csv
from pathlib import Path

import typer

from matlas.config import Settings
from matlas.core.loop import EnrichmentAgent
from matlas.regions.base import RegionPack
from matlas.regions.india import IndiaRegionPack
from matlas.regions.us import USRegionPack
from matlas.router import pick_pack

app = typer.Typer()

_REGION_ALIASES = {"india": "IN", "us": "US"}


@app.command()
def enrich(
    descriptor: str,
    region: str = typer.Option("auto", "--region", help="'auto', 'us', or 'india'"),
) -> None:
    settings = Settings()
    packs: list[RegionPack] = [USRegionPack(), IndiaRegionPack()]
    override = None if region == "auto" else _REGION_ALIASES.get(region.lower(), region)
    pack = pick_pack(descriptor, override, packs)
    agent = EnrichmentAgent(pack, settings)
    result = agent.run(descriptor, pack.region_code)
    typer.echo(result.model_dump_json(indent=2))


@app.command("enrich-csv")
def enrich_csv(
    input_path: Path = typer.Argument(..., help="CSV with a descriptor column"),
    column: str = typer.Option("descriptor", "--column", help="Name of the descriptor column"),
    region: str = typer.Option("auto", "--region", help="'auto', 'us', or 'india'"),
    out: Path | None = typer.Option(None, "--out", help="Output CSV (default: <input>.enriched.csv)"),
) -> None:
    """Bulk-enrich a CSV export through the cost-tiered batch path."""
    from matlas.batch import enrich_one_tiered

    settings = Settings()
    packs: list[RegionPack] = [USRegionPack(), IndiaRegionPack()]
    override = None if region == "auto" else _REGION_ALIASES.get(region.lower(), region)
    out = out or input_path.with_suffix(".enriched.csv")

    with input_path.open(newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or column not in reader.fieldnames:
            raise typer.BadParameter(
                f"column {column!r} not found in {input_path} (columns: {reader.fieldnames})"
            )
        rows = list(reader)

    fieldnames = list(rows[0].keys()) + ["merchant", "category", "confidence", "is_unknown"] if rows else []
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        with typer.progressbar(rows, label="enriching") as progress:
            for row in progress:
                result = enrich_one_tiered(row[column], settings, packs, override)
                writer.writerow(
                    row
                    | {
                        "merchant": result.merchant,
                        "category": result.category.value,
                        "confidence": result.confidence,
                        "is_unknown": result.is_unknown,
                    }
                )
    typer.echo(f"wrote {len(rows)} enriched rows to {out}")


@app.command()
def serve(
    api: bool = typer.Option(False, "--api", help="Serve the REST API (FastAPI/uvicorn)"),
    mcp: bool = typer.Option(False, "--mcp", help="Serve the MCP server (stdio transport)"),
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
) -> None:
    if api == mcp:
        raise typer.BadParameter("pass exactly one of --api or --mcp")

    if api:
        import uvicorn

        from matlas.api import app as fastapi_app

        uvicorn.run(fastapi_app, host=host, port=port)
    else:
        from matlas.mcp_server import mcp as mcp_server

        mcp_server.run()
