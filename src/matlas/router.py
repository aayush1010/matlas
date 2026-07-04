from matlas.regions.base import RegionPack


def pick_pack(raw: str, region_override: str | None, packs: list[RegionPack]) -> RegionPack:
    if region_override is not None:
        for pack in packs:
            if pack.region_code == region_override.upper():
                return pack
        raise ValueError(f"no RegionPack registered for region {region_override!r}")

    return max(packs, key=lambda pack: pack.detect(raw))
