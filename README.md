# matlas

Agentic transaction enrichment. Turns messy bank/card/UPI descriptors into
clean structured data — merchant, category, MCC/VPA, confidence.

Region-agnostic core + swappable `RegionPack`s. US is the benchmarked pack
(MCC-backed). India is a portability pack — same loop, no fabricated
accuracy claim (no MCC-equivalent ground truth exists for UPI).

## Install

```bash
pip install -e ".[dev]"       # library + CLI + tests
pip install -e ".[api,dev]"   # + REST API / MCP server surfaces
```

Requires `ANTHROPIC_API_KEY` for anything that actually runs the agent loop
(CLI/API/MCP). Offline tests (`pytest tests --ignore=tests/live`) need no key.

## CLI

```bash
matlas enrich "SQ *STARBUCKS #4521 SEATTLE WA"
matlas enrich "UPI/DR/408123456789/SWIGGY/YESB/Payment for order" --region india
matlas serve --api             # FastAPI on :8000
matlas serve --mcp             # MCP server, stdio transport
```

`--region` accepts `auto` (default, detected), `us`, or `india`.

## REST API

```
POST /enrich        {"descriptor": "...", "region": "us"}   -> EnrichedTransaction
POST /enrich/batch   {"descriptors": [...], "region": "us"} -> [EnrichedTransaction]
GET  /healthz
```

## MCP server

Exposes one tool, `enrich(descriptor, region=None)`, returning the same
structured record as the CLI/API.

## How it works

Deterministic resolver (gazetteer exact match → fuzzy match → fallback)
does the merchant/category lookup as a tool call — never an LLM guess. The
agent proposes, the resolver's tool result is cross-checked against the
proposal (`core/validator.py`), and a contradiction triggers one bounded
self-correction retry before returning.

Full design and build log live in the project's Obsidian vault
(`Projects/matlas/Build-Spec.md`, `Build-Log.md`) — not in this repo.

## Status

Week 1 (US pack, agent loop, CLI, eval harness, CI) and Week 2 (India
`RegionPack`, REST API, MCP server) complete. Not yet built: batch/cost
tiering, real cost/token accounting.
