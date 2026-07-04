import pytest

from matlas.regions.us import USRegionPack
from matlas.router import pick_pack


class _DummyLowConfidencePack:
    region_code = "XX"

    def detect(self, raw: str) -> float:
        return 0.0


def test_override_path_returns_matching_pack():
    us = USRegionPack()
    dummy = _DummyLowConfidencePack()
    result = pick_pack("anything", "us", [dummy, us])
    assert result is us


def test_invalid_override_raises():
    us = USRegionPack()
    with pytest.raises(ValueError):
        pick_pack("anything", "IN", [us])


def test_detect_based_path_picks_highest_confidence_pack():
    us = USRegionPack()
    dummy = _DummyLowConfidencePack()
    result = pick_pack("SQ *STARBUCKS #4521 SEATTLE WA", None, [dummy, us])
    assert result is us
