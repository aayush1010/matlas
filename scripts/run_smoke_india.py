"""Run the India gold fixture through the real agent loop. Live API —
costs real money.

This is a PORTABILITY SMOKE TEST, not a benchmark: the fixture is our own
gazetteer (no public labeled corpus of Indian bank narrations exists), so
the number proves the UPI pipeline holds together end to end — it is not
an accuracy claim. Keep it labeled that way everywhere it's reported.

Usage: ANTHROPIC_API_KEY=... python scripts/run_smoke_india.py [n]
Optional n = row cap for a cheap dry run before the full set.
"""

import sys

import anthropic

from matlas.config import Settings
from matlas.core.loop import EnrichmentAgent
from matlas.eval.gold import load_gold_india
from matlas.eval.harness import run_benchmark
from matlas.eval.judge import exact_match_judge, make_llm_judge
from matlas.eval.report import render_report
from matlas.regions.india import IndiaRegionPack

rows = load_gold_india()
if len(sys.argv) > 1:
    rows = rows[: int(sys.argv[1])]

settings = Settings()
agent = EnrichmentAgent(IndiaRegionPack(), settings)
_llm = make_llm_judge(anthropic.Anthropic(), settings.judge_model)


def judge(predicted: str, expected: str) -> bool:
    # exact hit costs nothing; only genuine name mismatches go to the LLM
    return exact_match_judge(predicted, expected) or _llm(predicted, expected)


result = run_benchmark(agent, rows, region="IN", judge=judge)
render_report(
    result,
    title=f"matlas India portability smoke test ({len(rows)} rows, {settings.model_hard})",
)
