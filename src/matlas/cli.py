import typer

from matlas.config import Settings
from matlas.core.loop import EnrichmentAgent
from matlas.regions.base import RegionPack
from matlas.regions.us import USRegionPack
from matlas.router import pick_pack

app = typer.Typer()


@app.command()
def enrich(
    descriptor: str,
    region: str = typer.Option("auto", "--region", help="'auto' or a region code like 'us'"),
) -> None:
    settings = Settings()
    packs: list[RegionPack] = [USRegionPack()]
    override = None if region == "auto" else region
    pack = pick_pack(descriptor, override, packs)
    agent = EnrichmentAgent(pack, settings)
    result = agent.run(descriptor, pack.region_code)
    typer.echo(result.model_dump_json(indent=2))
