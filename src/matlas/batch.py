from matlas.config import Settings
from matlas.core.loop import EnrichmentAgent
from matlas.core.schema import EnrichedTransaction, Evidence
from matlas.regions.base import RegionPack
from matlas.router import pick_pack


def enrich_one_tiered(
    descriptor: str,
    settings: Settings,
    packs: list[RegionPack],
    region_override: str | None = None,
) -> EnrichedTransaction:
    """Cost-tiered enrichment: deterministic gazetteer hit -> no LLM call at
    all; else cheap-model confirm; else the full hard-model agent loop."""
    pack = pick_pack(descriptor, region_override, packs)
    normalized = pack.normalize(descriptor)
    resolved = pack.resolve(normalized)

    if resolved.source == "gazetteer_exact":
        return EnrichedTransaction(
            raw=descriptor,
            region=pack.region_code,
            rail=normalized.rail,
            merchant=resolved.merchant_type,
            category=resolved.category,
            confidence=resolved.confidence,
            consistency_check_applicable=pack.consistency_applicable(normalized),
            consistency_ok=True,
            evidence=[
                Evidence(source="gazetteer", detail=resolved.merchant_type, confidence=resolved.confidence)
            ],
            is_unknown=False,
        )

    cheap_settings = settings.model_copy(update={"model_hard": settings.model_cheap})
    cheap_result = EnrichmentAgent(pack, cheap_settings).run(descriptor, pack.region_code)
    if not cheap_result.is_unknown and cheap_result.confidence >= settings.confidence_threshold:
        return cheap_result

    return EnrichmentAgent(pack, settings).run(descriptor, pack.region_code)


def enrich_batch_tiered(
    descriptors: list[str],
    settings: Settings,
    packs: list[RegionPack],
    region_override: str | None = None,
) -> list[EnrichedTransaction]:
    return [enrich_one_tiered(d, settings, packs, region_override) for d in descriptors]
