from typing import Protocol

from pydantic import BaseModel

from matlas.eval.gold import GoldRow
from matlas.eval.judge import exact_match_judge


class _HasValue(Protocol):
    value: str


class _Result(Protocol):
    merchant: str
    category: _HasValue  # SharedCategory-like: exposes .value


class _Agent(Protocol):
    def run(self, raw: str, region: str) -> _Result: ...


class BenchmarkResult(BaseModel):
    n: int
    merchant_accuracy: float
    category_accuracy: float
    mean_tool_calls: float | None = None


def run_benchmark(agent: _Agent, gold_rows: list[GoldRow], region: str = "US") -> BenchmarkResult:
    merchant_hits = 0
    category_hits = 0
    tool_call_counts = []

    for row in gold_rows:
        result = agent.run(row.raw, region)
        if exact_match_judge(result.merchant, row.merchant):
            merchant_hits += 1
        if result.category.value == row.category:
            category_hits += 1
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
    )
