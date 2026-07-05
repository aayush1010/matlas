from typing import Callable, Protocol

from pydantic import BaseModel

from matlas.eval.gold import GoldRow
from matlas.eval.judge import exact_match_judge


class _HasValue(Protocol):
    value: str


class _Result(Protocol):
    merchant: str
    category: _HasValue  # SharedCategory-like: exposes .value
    confidence: float


class _Agent(Protocol):
    def run(self, raw: str, region: str) -> _Result: ...


class CalibrationBucket(BaseModel):
    lo: float  # bucket lower bound, inclusive
    hi: float  # upper bound, exclusive (except the last bucket)
    n: int
    mean_confidence: float
    category_accuracy: float


class BenchmarkResult(BaseModel):
    n: int
    merchant_accuracy: float
    category_accuracy: float
    mean_tool_calls: float | None = None
    calibration: list[CalibrationBucket] = []


# Calibration = "when matlas says 0.9, is it right ~90% of the time?"
# Measured, never tuned blind: bucket predictions by reported confidence
# and compare each bucket's mean confidence against its actual accuracy.
_BUCKET_EDGES = [0.0, 0.5, 0.7, 0.85, 0.95, 1.01]


def _calibration_buckets(pairs: list[tuple[float, bool]]) -> list[CalibrationBucket]:
    buckets = []
    for lo, hi in zip(_BUCKET_EDGES, _BUCKET_EDGES[1:]):
        in_bucket = [(c, ok) for c, ok in pairs if lo <= c < hi]
        if not in_bucket:
            continue
        buckets.append(
            CalibrationBucket(
                lo=lo,
                hi=min(hi, 1.0),
                n=len(in_bucket),
                mean_confidence=sum(c for c, _ in in_bucket) / len(in_bucket),
                category_accuracy=sum(ok for _, ok in in_bucket) / len(in_bucket),
            )
        )
    return buckets


def run_benchmark(
    agent: _Agent,
    gold_rows: list[GoldRow],
    region: str = "US",
    judge: Callable[[str, str], bool] = exact_match_judge,
) -> BenchmarkResult:
    merchant_hits = 0
    category_hits = 0
    tool_call_counts = []
    confidence_pairs: list[tuple[float, bool]] = []

    for row in gold_rows:
        result = agent.run(row.raw, region)
        if judge(result.merchant, row.merchant):
            merchant_hits += 1
        category_ok = result.category.value == row.category
        if category_ok:
            category_hits += 1
        confidence_pairs.append((result.confidence, category_ok))
        # ponytail: cost/tokens deferred until the agent surfaces usage data
        # and a per-model pricing table exists — not fabricating one now.
        tool_calls = getattr(agent, "last_run_tool_calls", None)
        if tool_calls is not None:
            tool_call_counts.append(tool_calls)

    n = len(gold_rows)
    return BenchmarkResult(
        n=n,
        merchant_accuracy=merchant_hits / n,
        category_accuracy=category_hits / n,
        mean_tool_calls=(sum(tool_call_counts) / len(tool_call_counts)) if tool_call_counts else None,
        calibration=_calibration_buckets(confidence_pairs),
    )
