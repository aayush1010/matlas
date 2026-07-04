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
