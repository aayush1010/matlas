"""Run the US gold set through the real agent loop and print the benchmark
report (accuracy + confidence calibration). Live API — costs real money.

ponytail: no flags; env vars already control model/region via Settings.
Usage: ANTHROPIC_API_KEY=... python scripts/run_benchmark_us.py [n]
Optional n = row cap for a cheap dry run before the full 330.
"""

import sys

import anthropic

from matlas.config import Settings
from matlas.core.loop import EnrichmentAgent
from matlas.eval.gold import load_gold
from matlas.eval.harness import run_benchmark
from matlas.eval.judge import exact_match_judge, make_llm_judge
from matlas.eval.report import render_report
from matlas.regions.us import USRegionPack

rows = load_gold()
if len(sys.argv) > 1:
    rows = rows[: int(sys.argv[1])]

settings = Settings()
agent = EnrichmentAgent(USRegionPack(), settings)
_llm = make_llm_judge(anthropic.Anthropic(), settings.judge_model)


def judge(predicted: str, expected: str) -> bool:
    # exact hit costs nothing; only genuine name mismatches go to the LLM
    return exact_match_judge(predicted, expected) or _llm(predicted, expected)


result = run_benchmark(agent, rows, region="US", judge=judge)
render_report(result, title=f"matlas US benchmark ({len(rows)} rows, {settings.model_hard})")
