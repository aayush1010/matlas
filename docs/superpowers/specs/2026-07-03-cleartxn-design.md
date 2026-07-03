# cleartxn — Agentic Transaction Enrichment (design spec)

Date: 2026-07-03
Status: approved for implementation planning

## Context

Plaid Enrich, Ntropy, and MX sell transaction enrichment (raw bank/card descriptor →
structured merchant + category + MCC) as closed APIs. No open-source developer library
does this in either the US or India market — confirmed by live GitHub research
(2026-07-01 → 07-03; see "Evidence trail" below).

This project was chosen after five other candidates were researched and falsified:
an MCP red-team tool (promptfoo already owns that niche at 22.8k★), synthetic fraud
data generation (genuine loop, but off the user's fintech/payments focus), generic
fraud/AML tooling (doesn't trend as OSS), and three of five payments-adjacent lanes
(gateway mocks, ledgers, agentic-commerce — all saturated or star-farmed). Transaction
enrichment is the surviving option: genuinely open (near-zero real repos for "merchant
name normalization" / "transaction enrichment"), proven demand (closed competitors +
apps at 20–54k★ that lack this component), a genuine agent loop (not a single-shot
LLM call), and a real technical moat for this user specifically (merchant-string
normalization is entity resolution — their day job).

Goal: ship a reproducible US benchmark (the trending hook) plus an architecturally
honest India portability pack (no fabricated India accuracy claim, since no labeled
Indian descriptor corpus exists publicly).

## What it is

An open-source Python library + CLI + REST API + MCP server that turns a messy
bank/card transaction descriptor into clean structured data:

- US: `"SQ *COFFEE 0432 SAN FRAN CA"` → `{ merchant: "Square — Coffee", category:
  "Food & Drink > Coffee Shop", mcc: 5814, confidence: 0.92 }`
- India: `"UPI/DR/408..../SWIGGY/YESB/Payment"` → `{ merchant: "Swiggy", category:
  "Food & Drink", vpa_psp: "Yes Bank", rail: "UPI", confidence: 0.88 }`

## What it is not

- Not a personal-finance app — it's the reusable component those apps lack.
- Not a hosted SaaS.
- Not a scraper of proprietary/gated merchant databases (no bundled Plaid/Ntropy/MX
  or gated Razorpay data).
- Not a single-shot classifier — the agentic loop and self-correction are
  non-negotiable; cutting them collapses this into a `messages.parse` call.
- Not claiming a validated India accuracy number in v1. No public, labeled,
  redistributable Indian descriptor corpus exists (everything found is synthetic
  with unverifiable licensing). India ships as parsing + best-effort enrichment
  against a curated gazetteer, reported as a portability smoke test — never a
  fabricated benchmark.

## Why it's agentic

Not a wrapper around one LLM call. Given a descriptor, the system decides whether it
already knows the merchant or must call a tool, observes a result it can't predict in
advance, and self-corrects on a machine-checkable contradiction.

The insight that unifies both regions: MCC was never parsed from the descriptor — it's
resolved by a tool, even in the US (Plaid itself doesn't expose MCC in descriptors).
So India isn't a different loop, it's the same loop with a different resolver. A
validator maps both the LLM's proposed category and the resolver's authoritative
signal into one shared category enum and checks agreement; a contradiction forces
re-proposal, a gated web-search escalation, or a confidence drop.

Loop shape, identical across regions: **decide → tool → observe → refine**.

## Who uses it

Developers building fintech/budgeting/accounting products who need enrichment and
won't pay Plaid/Ntropy or hand-roll it: indie fintech devs, PFM-app builders, fintech
startups, data engineers on transaction pipelines — in both the US and India. The
broader GitHub audience is the "open-source alternative to a closed API" crowd plus
the LLM-agent-project crowd, pulled in by the benchmark and the two-rails portability
story. Adopters skew individual/startup/indie — banks buy closed platforms — which is
also the crowd that drives OSS stars.

## Gating verdicts (researched, not assumed)

**Verdict 1-US — US benchmark data is buildable.** `iso18245` (MIT) supplies the MCC
taxonomy/lookup; Plaid's PFC taxonomy (~13 primary × ~85 detailed categories) is
public and becomes the standard; MIT-licensed HF datasets (68k and 4.5M rows) supply
free messy inputs for a hand-labeled 300–500 row US gold set (merchant + MCC as hard
columns, category bootstrapped from coarse labels). MCC range 3000–3999 gives a free
authoritative airline/hotel/car-rental brand→MCC seed.

**Verdict 1-IN — India benchmark data is blocked.** No real, labeled, redistributable
Indian descriptor→merchant/category corpus exists publicly; every candidate found is
synthetic with unverifiable licensing. This is a hard data constraint, not a scoping
choice — India cannot ship a validated accuracy number in v1. It ships as a curated
gazetteer + best-effort resolver, reported honestly as a ~75–150 row portability smoke
test fixture, not a benchmark.

**Verdict 2 — the agent loop is genuine, not forced.** It survives India intact
because MCC was always a resolver output, never a parsed field, in both regions. Two
mechanics make the naive single-call version into a real loop: (1) the consistency
validator forcing self-correction on proposal/resolver disagreement, and (2) gated
web-search escalation for unknowns. This is the project's biggest technical teaching
surface (manual `stop_reason` loop, LLM-as-judge, confidence calibration, deterministic
resolver design across two rails) — cutting it turns the project into a classifier.

**Verdict 3 — multi-region scope resolves to "architecture-multi-region, US-
benchmarked."** Fully benchmarking both regions in the initial build is impossible —
not on effort, but because India's ground truth doesn't exist to compute a number
from. The region-pack seam is nearly free architecturally and improves the design
regardless of region count. So: the region-pack seam ships from day one, US is
polished and benchmarked, India ships as a thin, honest portability pack, and India's
benchmark grows post-launch as real data becomes available.

## Architecture

Region-agnostic core with swappable `RegionPack`s.

Flow, identical per region: raw string → `RegionPack.normalize` (pure function) →
agent loop `{ LLM proposes {merchant, category, confidence} → RegionPack.resolve
returns an authoritative signal → validator maps both into SharedCategory and checks
agreement → contradiction triggers self-correction }` → validated record.

**Region-agnostic (`core/`):** the loop, the `SharedCategory` enum, the
`EnrichedTransaction` schema, the validator, the web-search escalation tool, the eval
harness, the CLI, the REST API, the MCP server, the router.

**Region-specific (`regions/<code>/`, the `RegionPack`):** normalizer, resolver,
gazetteer, taxonomy→`SharedCategory` map, and a `consistency_applicable()` predicate
(`False` for P2P/ATM/self-transfer — a first-class correct branch, not a miss).

```python
class RegionPack(Protocol):
    region_code: str                                    # "US", "IN"
    def detect(self, raw: str) -> float: ...            # 0..1 confidence this pack owns the descriptor
    def normalize(self, raw: str) -> NormalizedTxn: ...  # rail, merchant_str, counterparty_id, refs, remark
    def resolve(self, n: NormalizedTxn) -> ResolvedSignal: ...  # authoritative merchant-type/MCC + SharedCategory + source + confidence
    gazetteer: Gazetteer                                 # merchant/VPA -> canonical name + SharedCategory
    taxonomy: Taxonomy                                   # region categories <-> SharedCategory
    def consistency_applicable(self, n: NormalizedTxn) -> bool: ...  # False for P2P/ATM/self-transfer
```

- **US resolver:** merchant → MCC (`iso18245`) → `SharedCategory`.
- **India resolver (two-stage):** VPA handle → PSP/bank via a deterministic ~200-row
  table (`@ybl`→PhonePe/Yes Bank, `@paytm`→Paytm, `@okhdfcbank`→GPay/HDFC,
  `@apl`→Amazon Pay) for provenance/normalization; payee-name → merchant-type →
  `SharedCategory` (gazetteer + web-search escalation) for category. P2P resolves to
  `PERSONAL_TRANSFER` with `consistency_applicable = False`.

Every output record carries `region`, `rail` (UPI/card/NEFT/IMPS), and
`consistency_check_applicable`, so India results are self-describing and honestly
scoped rather than silently degraded US results.

## The moat

Merchant-name normalization is entity resolution on merchant strings — the user does
identity hashing and entity linkage professionally. Differentiators:

- Brand-collision / adversarial disambiguation (DELTA airline vs. faucet brand;
  lookalike UPI payees).
- Canonicalization and dedup via `rapidfuzz` + deterministic blocking keys.
- Calibrated, inspectable confidence with a real "unknown" escape hatch — a
  fraud precision/recall instinct applied to a self-reported model score, rather
  than trusting the model's own confidence claim.
- Privacy / local-first: normalizer, gazetteer, MCC/VPA lookup, and validation all
  run locally; only the cleaned merchant string ever leaves the machine — never
  account numbers, amounts, or full statements. Web search is opt-in. This
  resonates especially in India (DPDP Act, Account Aggregator data sensitivity) and
  is a headline feature there.

## Reuse vs. build

**Reuse:** `iso18245` (MCC), `rapidfuzz` (fuzzy matching), `cleanco` (legal suffix
stripping), `pydantic` v2, `typer` + `rich`, `fastapi` + `uvicorn`, the `mcp` SDK,
`pandas`, `anthropic`. Gazetteer seeds from Wikidata (CC0), the DoDataThings MIT
dataset (US), and community-curated VPA handle lists (India).

**Build:** the region-agnostic core (loop, validator, `SharedCategory`), both
normalizers, both resolvers (US MCC, India VPA/merchant-type), both gazetteers, and
both gold sets.

**Never bundle:** scraped Plaid/Ntropy/MX data or the gated, non-redistributable
Razorpay VPA→MCC API.

## Repo layout

```
cleartxn/
├── pyproject.toml            # hatchling; console_scripts → cleartxn.cli:app
├── README.md                 # US benchmark hero + two-rails portability demo + privacy stance
├── LICENSE (Apache-2.0), CONTRIBUTING.md, CHANGELOG.md
├── .github/workflows/ci.yml  # lint+type+test, no live API (record/replay cassettes only)
├── src/cleartxn/
│   ├── core/
│   │   ├── schema.py          # EnrichedTransaction (region, rail, consistency_check_applicable), Evidence
│   │   ├── shared_category.py # the region-agnostic SharedCategory enum
│   │   ├── loop.py            # EnrichmentAgent manual tool-use loop  ← learning core (Verdict 2)
│   │   ├── validator.py       # proposal + resolved-signal → SharedCategory consistency + confidence calibration
│   │   └── websearch_tool.py  # gated Anthropic server tool (pause_turn handling)
│   ├── regions/
│   │   ├── base.py            # RegionPack Protocol + NormalizedTxn, ResolvedSignal, Gazetteer, Taxonomy
│   │   ├── us/                # normalizer.py, resolver_mcc.py, gazetteer.us.jsonl, mcc_table, taxonomy_map.py
│   │   └── india/             # normalizer.py, resolver_vpa.py, vpa_handles.csv, gazetteer.in.jsonl, taxonomy_map.py
│   ├── router.py               # picks pack via detect() or --region
│   ├── config.py               # pydantic-settings: models per tier, region, web-search flag, thresholds
│   ├── batch.py                # tiered enrichment + cost control (deterministic → Haiku confirm → Opus loop)
│   ├── eval/{gold,harness,judge,report}.py
│   ├── api.py                  # FastAPI: POST /enrich, /enrich/batch, GET /healthz (region-agnostic)
│   └── mcp_server.py           # MCP server exposing `enrich`
├── data/gold/
│   ├── gold_us.jsonl           # 300–500 rows, the benchmark
│   └── gold_in.jsonl           # ~75–150 rows, a portability smoke-test fixture — not a benchmark
├── examples/                    # enrich_one.py, enrich_csv.py, sample_us.csv, sample_in.csv (synthetic/user-owned only)
├── tests/                        # test_normalize_us/in, test_validate, test_agent_replay, test_router, test_eval_harness + cassettes/
└── docs/{taxonomy,privacy,benchmark,regions}.md
```

Most critical files: `core/loop.py` (the loop and self-correction, Verdict 2),
`core/validator.py` (the `SharedCategory` consistency mechanic that unifies both
regions), `regions/base.py` (the `RegionPack` seam — multi-region done right),
`eval/harness.py` (the US benchmark, the trending hook), `regions/us/normalizer.py`
and `regions/india/normalizer.py` (the entity-resolution moat), `data/gold/gold_us.jsonl`
(the benchmark itself).

## Config, CLI, and surfaces

**Config:** `model_hard="claude-opus-4-8"`, `model_cheap="claude-haiku-4-5"`,
`judge_model="claude-haiku-4-5"`, `region="auto"` (or `us`/`india`),
`taxonomy="plaid_pfc"`, `enable_web_search=false`, `web_search_max_uses=3`,
`confidence_threshold=0.6`, `max_agent_iterations=5`.

**CLI (Typer):**
- `cleartxn enrich "<descriptor>" [--region auto|us|india]`
- `cleartxn enrich-csv in.csv -o out.csv`
- `cleartxn benchmark [--region us]`
- `cleartxn serve --api|--mcp`

**Surfaces:** Python library (`from cleartxn import EnrichmentAgent`), REST API
(FastAPI), MCP server (exposes `enrich`). All three are region-agnostic; region is
chosen by the router or an explicit flag.

## Key decisions

- US card enrichment resolves MCC↔category; India UPI enrichment resolves
  merchant-type↔category. Both project into one `SharedCategory` enum that the
  validator checks against — one loop design, swappable resolvers.
- P2P/ATM/self-transfer is a first-class correct branch
  (`consistency_applicable = False`), not a failure mode — otherwise India output
  reads as broken.
- India ships honest: every record carries `region`/`rail`/
  `consistency_check_applicable`; India is reported as a portability smoke test,
  never a fabricated accuracy percentage.
- Standardize on Plaid PFC + `iso18245` MCC for US comparability; hand-build the
  MCC→`SharedCategory` and India-taxonomy→`SharedCategory` maps.
- Gazetteer legality: CC0/MIT/community-derived seeds only, with documented
  provenance; long tail covered via opt-in web search; never bundle gated
  (Razorpay) or scraped proprietary data.
- Testing an LLM enricher: normalizers and the validator are pure functions →
  exhaustive unit tests need no API key; the agent loop is tested via
  record/replay cassettes so CI runs with no live API; gold-set regression
  catches drift.
- Honest accuracy ceiling: LLMs hallucinate merchants. Evidence trails,
  calibrated confidence, and a real `is_unknown` escape hatch are load-bearing,
  and the README states the ceiling plainly rather than overselling accuracy.

## Anti-goals and ethics

Not in v1: a PFM app, a hosted SaaS, a scraper of proprietary/gated merchant
databases, a validated India accuracy claim, live-API dependence in CI, an
SMS-alert parser (a different, already-crowded niche).

Ethics/privacy: this handles financial data. Examples and gold sets use only
synthetic or user-owned data. Local-first by default. Only cleaned merchant
strings are ever sent to the API — never account numbers, amounts, or full
statements. All data provenance is documented. License: Apache-2.0.

## Verification plan

1. **Pure core, no tokens:** `pytest tests/test_normalize_us.py
   tests/test_normalize_in.py tests/test_validate.py tests/test_router.py` —
   both normalizers, the `SharedCategory` consistency validator, and region
   routing. Fully offline.
2. **Agent loop, replayed:** `pytest tests/test_agent_replay.py` — drives
   `core/loop.py` over recorded cassettes; asserts `stop_reason` branching, tool
   dispatch, consistency-contradiction feedback, `is_unknown`, and India's P2P
   `consistency_applicable = False` branch. No live API.
3. **Live enrichment** (needs `ANTHROPIC_API_KEY`): `cleartxn enrich "SQ *COFFEE
   0432 SAN FRAN CA" --region us` and `cleartxn enrich
   "UPI/DR/408.../SWIGGY/YESB/Payment" --region india` → structured records with
   evidence; confirm an ambiguous case fires ≥1 tool call plus a consistency
   self-correction (proves the loop is real), and a UPI P2P case returns
   `PERSONAL_TRANSFER` with the consistency check marked not applicable.
4. **The trending hook:** `cleartxn benchmark --region us` → merchant/category/MCC
   accuracy, cost-per-transaction, and mean tool-calls-per-transaction (the last
   metric proves the loop earns its keep). This is the README hero and is
   reproducible from cassettes without spend.
5. **Portability proof:** the same `serve --api` / `serve --mcp` and the same loop
   handle both a US card descriptor and an Indian UPI descriptor — the two-rails
   demo. India is reported as a smoke test, not a benchmark.

## Milestone plan

- **Week 1 — shared core + US pack, end to end.** `core/schema.py` +
  `core/shared_category.py` + `regions/base.py` (the seam); `regions/us/normalizer.py`
  with pure unit tests; `core/loop.py` with one tool (the US MCC resolver) +
  `core/validator.py` consistency check + final `messages.parse`. US runs end to
  end. Biggest learning stretch of the project: the manual `stop_reason` loop plus
  consistency feedback.
- **Week 2 — US breadth + India stood up behind the same interface.** US gazetteer
  + gated `websearch_tool.py` escalation + `batch.py` tiering. `regions/india/`:
  UPI normalizer, deterministic VPA→PSP table, small gazetteer, P2P branch. This
  is where the region-pack seam earns its keep — India runs end to end on UPI.
  Grow the US gold set to 300–500 rows; add `eval/judge.py` LLM-as-judge.
- **Week 3 — surfaces + reproducibility.** `router.py`, `api.py` (FastAPI),
  `mcp_server.py` — all region-agnostic. `test_agent_replay.py` cassettes and a
  green `ci.yml` with no live key. `eval/report.py` produces the US benchmark
  table.
- **Week 4 — polish + launch.** README (US benchmark hero, two-rails portability
  demo, privacy stance), CONTRIBUTING (how to add gold rows / add a RegionPack),
  docs. Thin India gold fixture (~75–150 rows) reported honestly as a smoke test.
  Tune confidence calibration. Publish to PyPI as `cleartxn`; first release.
- **If time slips:** cut the India gold fixture down to a demo — never cut the
  India normalizer or VPA table, since those are the portability proof; the
  fixture is garnish.

Biggest learning stretches, sequenced early: the manual `stop_reason` tool-use loop
with consistency feedback (week 1), gated server-tool web-search escalation (week
2), LLM-as-judge (week 2), and designing the `RegionPack` abstraction itself (weeks
1–2).
