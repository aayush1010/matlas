# matlas

Turn messy bank-statement strings into clean, structured data.

If you've ever pulled transactions from a bank feed, you know the problem:
what a human calls "coffee at Starbucks" arrives as
`SQ *STARBUCKS #4521 SEATTLE WA`, and a food delivery order in India shows
up as `UPI/DR/408123456789/SWIGGY/YESB/Payment for order`. Closed APIs like
Plaid Enrich, Ntropy, and MX solve this behind a paywall. matlas is the
open-source alternative: give it the raw descriptor, get back the merchant,
a spending category, a confidence score, and the evidence trail (including
the MCC, where one exists) that backs them up.

```bash
$ matlas enrich "SQ *STARBUCKS #4521 SEATTLE WA"
```

```json
{
  "raw": "SQ *STARBUCKS #4521 SEATTLE WA",
  "region": "US",
  "rail": "card",
  "merchant": "Starbucks",
  "category": "food_and_drink",
  "confidence": 0.95,
  "consistency_check_applicable": true,
  "consistency_ok": true,
  "evidence": [
    {"source": "llm", "detail": "Starbucks", "confidence": 0.9},
    {"source": "resolver", "detail": "gazetteer_exact:5814", "confidence": 1.0}
  ],
  "is_unknown": false
}
```

## Why it's built as an agent (and why that matters)

Most LLM wrappers ask the model to guess a category and call it a day. The
problem: models are confidently wrong about merchants, and there's no way
to tell a good guess from a bad one.

matlas splits the job in two:

1. **The LLM proposes.** It reads the raw descriptor and suggests a
   merchant and category — the thing LLMs are genuinely good at
   (untangling `SQ *`, store numbers, city suffixes).
2. **A deterministic resolver checks.** A curated merchant gazetteer
   (exact match, then fuzzy match) looks up the authoritative
   category and MCC. This is a real tool call inside the agent loop —
   a lookup table, never a second LLM guess.

When the two disagree, a validator (`core/validator.py`) catches the
contradiction and sends it back: the model sees the resolver's evidence and
gets exactly one bounded retry to reconsider. If the resolver has high
confidence, its answer wins. Every returned record carries the evidence
trail, so you can see *why* matlas believes what it believes.

The result: hallucinations get caught by a lookup table instead of shipping
to your ledger.

## Two regions, one honest difference

The core is region-agnostic; regions plug in as swappable `RegionPack`s.

- **US** — the benchmarked pack. Card descriptors resolve against a
  330-row gazetteer with real, `iso18245`-verified MCC codes. This is
  where accuracy claims live, because MCC gives us ground truth to
  measure against.
- **India** — the portability pack. UPI narrations (`UPI/DR/.../SWIGGY/...`)
  are parsed, merchant payees resolve against a 186-row gazetteer, and
  person-to-person transfers get carved out as `personal_transfer`
  (there's no meaningful "category" for paying your friend back for
  dinner). India ships **without** an accuracy claim — no public labeled
  corpus of Indian bank narrations exists, so any number we printed would
  be made up. The pack demonstrates that the architecture ports; it
  doesn't pretend to a benchmark that can't exist yet.

That asymmetry is deliberate. We'd rather tell you what we can't measure
than invent a number.

## Install

```bash
pip install -e ".[dev]"       # library + CLI + tests
pip install -e ".[api,dev]"   # + REST API / MCP server
```

You need an `ANTHROPIC_API_KEY` in the environment for anything that runs
the agent loop (CLI, API, MCP). The offline test suite
(`pytest tests --ignore=tests/live`) needs no key — the agent loop is
tested against replayed response cassettes, which is also what keeps CI
green without secrets.

## Using it

**CLI:**

```bash
matlas enrich "SQ *STARBUCKS #4521 SEATTLE WA"
matlas enrich "UPI/DR/408123456789/SWIGGY/YESB/Payment for order" --region india
```

`--region` accepts `auto` (default — detected from the descriptor's shape),
`us`, or `india`.

**REST API** (`matlas serve --api`, FastAPI on :8000):

```
POST /enrich         {"descriptor": "...", "region": "us"}    -> EnrichedTransaction
POST /enrich/batch   {"descriptors": [...], "region": "us"}   -> [EnrichedTransaction]
GET  /healthz
```

The batch endpoint is cost-tiered: an exact gazetteer hit skips the LLM
entirely (free), a fuzzy hit gets confirmed by a cheap model, and only
genuinely ambiguous descriptors escalate to the strong model. On realistic
batches, most rows never touch the expensive path.

**MCP server** (`matlas serve --mcp`, stdio transport): exposes one tool,
`enrich(descriptor, region=None)`, returning the same structured record —
plug it into Claude Desktop or any MCP client and let the model enrich
transactions mid-conversation.

## Measuring it

The eval harness runs the gold set (the same curated gazetteer rows,
330 US + 186 India) through the full agent loop and reports per-field
accuracy plus mean tool calls per transaction:

```python
from matlas.eval.gold import load_gold
from matlas.eval.harness import run_benchmark
from matlas.eval.report import render_report

render_report(run_benchmark(agent, load_gold()))
```

Judging defaults to exact match; an LLM-as-judge (cheap model, one-turn
same-merchant check) is available for fuzzy merchant-name comparison.
India results are labeled a *portability smoke test* in the report output,
never an accuracy benchmark — see above.

## Privacy stance

Descriptors you enrich are sent to the Anthropic API and nowhere else.
matlas keeps no telemetry, no logging of your data, and no server-side
anything — it's a library. The gazetteer lookup happens locally. If a
descriptor resolves with an exact gazetteer hit through the tiered batch
path, it never leaves your machine at all.

## Contributing

The highest-leverage contribution is gold-set rows: real (anonymized)
descriptor shapes, especially Indian bank narrations, where no public
corpus exists. `scripts/build_gazetteer_us.py` and
`scripts/build_gazetteer_in.py` show the pattern — curated entries, every
US MCC verified against `iso18245` before it goes in.

## Status

Weeks 1–3 of the build plan complete and verified end-to-end against the
live API: agent loop, US + India packs, CLI, REST API, MCP server,
cost-tiered batching, LLM-judge, eval harness, CI. Week 4 (launch polish,
PyPI release) in progress. Design docs and the full build log live outside
this repo.
