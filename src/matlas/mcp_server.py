from mcp.server.fastmcp import FastMCP

from matlas.config import Settings
from matlas.core.loop import EnrichmentAgent
from matlas.regions.base import RegionPack
from matlas.regions.india import IndiaRegionPack
from matlas.regions.us import USRegionPack
from matlas.router import pick_pack

mcp = FastMCP("matlas")

_PACKS: list[RegionPack] = [USRegionPack(), IndiaRegionPack()]
_REGION_ALIASES = {"india": "IN", "us": "US"}


@mcp.tool()
def enrich(descriptor: str, region: str | None = None) -> dict:
    """Enrich a raw bank/card/UPI transaction descriptor into structured merchant/category data."""
    override = _REGION_ALIASES.get(region.lower(), region) if region else None
    pack = pick_pack(descriptor, override, _PACKS)
    agent = EnrichmentAgent(pack, Settings())
    result = agent.run(descriptor, pack.region_code)
    return result.model_dump()


if __name__ == "__main__":
    mcp.run()
