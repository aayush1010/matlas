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
