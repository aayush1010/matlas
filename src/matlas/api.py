from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from matlas.batch import enrich_batch_tiered
from matlas.config import Settings
from matlas.core.loop import EnrichmentAgent
from matlas.core.schema import EnrichedTransaction
from matlas.regions.base import RegionPack
from matlas.regions.india import IndiaRegionPack
from matlas.regions.us import USRegionPack
from matlas.router import pick_pack

app = FastAPI(title="matlas")

_PACKS: list[RegionPack] = [USRegionPack(), IndiaRegionPack()]
_REGION_ALIASES = {"india": "IN", "us": "US"}


class EnrichRequest(BaseModel):
    descriptor: str
    region: str | None = None


class EnrichBatchRequest(BaseModel):
    descriptors: list[str]
    region: str | None = None


def _enrich_one(req: EnrichRequest) -> EnrichedTransaction:
    override = _REGION_ALIASES.get(req.region.lower(), req.region) if req.region else None
    try:
        pack = pick_pack(req.descriptor, override, _PACKS)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    agent = EnrichmentAgent(pack, Settings())
    return agent.run(req.descriptor, pack.region_code)


@app.post("/enrich")
def enrich(req: EnrichRequest) -> EnrichedTransaction:
    return _enrich_one(req)


@app.post("/enrich/batch")
def enrich_batch(req: EnrichBatchRequest) -> list[EnrichedTransaction]:
    override = _REGION_ALIASES.get(req.region.lower(), req.region) if req.region else None
    try:
        return enrich_batch_tiered(req.descriptors, Settings(), _PACKS, override)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
