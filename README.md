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
pip install matlas          # library + CLI
pip install "matlas[api]"   # + REST API / MCP server
```

Working on matlas itself? Clone and use an editable install instead:

```bash
pip install -e ".[api,dev]"
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

Wondering which merchants resolve without the LLM? `matlas merchants
--region us` (or `india`) prints the current gazetteer grouped by
category — it reads the shipped data, so it's never out of date.

**Bulk CSV** — the realistic path. Nobody enriches one transaction at a
time; you have a statement export or a feed dump. Point matlas at a CSV
with a descriptor column and it runs every row through the cost-tiered
batch path (exact gazetteer hits never touch the LLM — a file of known
merchants costs nothing and needs no API key):

```bash
matlas enrich-csv transactions.csv --column descriptor --out enriched.csv
```

Output is the input CSV with `merchant`, `category`, `confidence`, and
`is_unknown` columns appended. Bank gave you a PDF? Export the CSV from
your net-banking portal instead — every major bank offers it, and PDF
table extraction is a different problem than transaction enrichment.

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

Latest full runs through the real agent loop (claude-sonnet-5,
2026-07-05):

|  | US (benchmark) | India (portability smoke test) |
|---|---|---|
| rows | 330 | 186 |
| merchant accuracy | 99.7% | 99.5% |
| category accuracy | 100.0% | 100.0% |
| mean tool calls / transaction | 1.00 | 1.00 |
| calibration | said 1.00, right 100% | said 1.00, right 100% |

Read those numbers honestly. The gold rows are the gazetteers' own keys —
clean canonical merchant strings, so every row exact-hits the resolver.
This measures the agent loop's ceiling on *known* merchants (does the
model reliably call the tool, agree with the deterministic signal, and
emit clean output — yes, 1.00 tool calls per transaction, zero category
misses in either region). It is not a claim about messy real-world
descriptors with store numbers, truncation, and processor prefixes —
building a gold set of those is the highest-leverage open contribution
(see below).

And the two columns are labeled differently on purpose: the India
fixture is our own gazetteer with no external corpus to validate
against, so its column is a **portability smoke test** — proof the UPI
pipeline (narration parsing, P2P carve-out, resolver) holds together
end to end — never an accuracy benchmark. Running it live still paid
for itself: it caught the model emitting `"Travel"` where the category
enum expected `"travel"`, a crash no offline test had hit.

The eval harness runs the gold set (the same curated gazetteer rows,
330 US + 186 India) through the full agent loop and reports per-field
accuracy plus mean tool calls per transaction. Reproduce the numbers
above yourself (live API, costs real money — both scripts take an
optional row cap for a cheap dry run first):

```bash
ANTHROPIC_API_KEY=... python scripts/run_benchmark_us.py 5   # dry run
ANTHROPIC_API_KEY=... python scripts/run_benchmark_us.py     # full 330
ANTHROPIC_API_KEY=... python scripts/run_smoke_india.py      # full 186
```

Judging defaults to exact match; an LLM-as-judge (cheap model, one-turn
same-merchant check) is available for fuzzy merchant-name comparison.

The report includes a confidence-calibration table — predictions bucketed
by reported confidence, each bucket's mean confidence side by side with
its actual accuracy. When matlas says 0.9, that table is how you check it
was right about nine times in ten. Calibration here is measured, never
tuned blind.

## Privacy stance

Descriptors you enrich are sent to the Anthropic API and nowhere else.
matlas keeps no telemetry, no logging of your data, and no server-side
anything — it's a library. The gazetteer lookup happens locally. If a
descriptor resolves with an exact gazetteer hit through the tiered batch
path, it never leaves your machine at all.

## Contributing

The highest-leverage contribution is gold-set rows: real (anonymized)
descriptor shapes, especially Indian bank narrations, where no public
corpus exists. Second-highest: a new region pack — the whole point of the
`RegionPack` seam is that your country's rails plug in without touching
the core. [CONTRIBUTING.md](CONTRIBUTING.md) walks through both, including
the data-honesty rules (every US MCC verified against `iso18245`, no
invented benchmarks).

## Status

v0.1.0, on [PyPI](https://pypi.org/project/matlas/). The full stack —
agent loop, US + India packs, CLI, REST API, MCP server, cost-tiered
batching, eval harness — is tested offline in CI and verified end to end
against the live API (which is how the fence-wrapped-JSON and
case-sensitive-category bugs got caught before you hit them). Young
project, honest scope: known-merchant coverage is 330 US + 186 India
rows and growing, and India intentionally ships without an accuracy
claim until a real labeled corpus exists.
