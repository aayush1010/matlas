# Contributing to matlas

Thanks for looking. Two kinds of contribution move this project forward
more than anything else: **gold-set rows** (more verified merchants to
resolve against and measure with) and **region packs** (new countries'
transaction rails behind the same interface). Both are described below,
along with the ground rules that keep the data honest.

## Dev setup

```bash
git clone https://github.com/aayush1010/matlas && cd matlas
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[api,dev]"
```

Before you open a PR, all three of these must pass — they're exactly what
CI runs, and none of them need an API key:

```bash
ruff check .
mypy src
pytest tests --ignore=tests/live
```

The agent loop is tested against replayed response fixtures
(`tests/core/test_agent_replay.py`), not live API calls. If you touch
`core/loop.py`, add a fixture for the new behavior — the markdown-fence
parsing bug taught us that anything the cassettes don't cover, the live
API will eventually break.

## The one rule that isn't negotiable: no invented data

Every accuracy claim in matlas is backed by something checkable, and
every row in the gold set is individually verifiable. Concretely:

- **US MCC codes are never guessed.** Before a code goes into a
  gazetteer row or `INDUSTRY_TO_MCC_CATEGORY`, verify it against the
  installed `iso18245` package:

  ```python
  import iso18245
  iso18245.get_mcc("5814").iso_description
  # 'Fast food restaurants'
  ```

  If the description doesn't match the merchant's actual business, it's
  the wrong code — find the right one, don't shrug it in.

- **India ships no accuracy number**, because no public labeled corpus
  of Indian bank narrations exists to benchmark against. Don't add one
  to the README, the report output, or a docstring. If you have a real
  labeled Indian dataset you can share, that's a far bigger
  contribution than any code.

## Adding gold-set rows

The gazetteer files double as the gold set — one curated file per
region, no separate benchmark data to keep in sync:

- `src/matlas/regions/us/gazetteer.us.jsonl` — `{key, canonical, category, mcc}`
- `src/matlas/regions/india/gazetteer.in.jsonl` — `{key, canonical, category}` (no MCC — India has no equivalent standard)

Don't edit the `.jsonl` files by hand. Add entries to the `MERCHANTS`
list in the matching pipeline script and rerun it — the scripts are
idempotent (they skip keys already present):

```bash
python scripts/build_gazetteer_us.py   # or build_gazetteer_in.py
```

Each entry is `(canonical name, industry keyword, [key variants])` in
the US script (the keyword maps to a verified MCC + category via
`INDUSTRY_TO_MCC_CATEGORY`) and `(canonical name, category, [key
variants])` in the India script (no MCC layer). The key variants are
what descriptors actually contain — `"dd doordash"`, `"h-e-b"` —
lowercased.

Two hard-won rules for variants:

1. **No bare variants of ~5 characters or fewer** unless the string
   can't plausibly appear inside an ordinary word. We shipped a bare
   `"ally"` for Ally Bank and rapidfuzz happily matched it inside
   "TOTALLY UNKNOWN MERCHANT" at 0.9 confidence. Prefer `"ally bank"`.
2. **After adding short brand names, run the unknown-merchant tests**
   (`tests/regions/*/test_resolver*`) and spot-check a nonsense
   descriptor still resolves to `unknown`.

Then bump the row-count assertions in `tests/eval/test_gold.py` and
make sure the category-completeness tests still pass — if you introduced
a category the region's taxonomy map doesn't know, they'll tell you.

## Adding a region pack

Regions plug into one Protocol seam (`src/matlas/regions/base.py`).
A pack provides:

```python
class RegionPack(Protocol):
    region_code: str          # "US", "IN", ...
    gazetteer: Gazetteer      # key -> (canonical name, SharedCategory)
    taxonomy: Taxonomy        # region-native category -> SharedCategory

    def detect(self, raw: str) -> float: ...           # 0..1: does this descriptor look like my region?
    def normalize(self, raw: str) -> NormalizedTxn: ...
    def resolve(self, n: NormalizedTxn) -> ResolvedSignal: ...
    def consistency_applicable(self, n: NormalizedTxn) -> bool: ...
```

The pattern, using the two existing packs as templates:

1. **`normalizer.py`** — parse the region's raw descriptor shape into a
   `NormalizedTxn`. Pure function, table-driven tests with real messy
   examples. (US: strip store numbers/state codes, `cleanco` legal
   suffixes. India: split UPI narration, distinguish merchant payee
   from person-to-person VPA.)
2. **`resolver_*.py`** — the deterministic tool call. Gazetteer exact
   match → rapidfuzz fuzzy (≥85) → `UNKNOWN`. Never an LLM guess: this
   is the signal the validator uses to catch the LLM's mistakes, so it
   must not share the LLM's failure modes. Region-specific fallbacks go
   here (India adds: VPA-shaped counterparty with no gazetteer hit →
   `personal_transfer`).
3. **`taxonomy_map.py`** — region-native code → `SharedCategory`. Only
   map codes that actually appear in your gazetteer; the completeness
   test keeps the two honest against each other.
4. **`__init__.py`** — wire it into the Protocol. `detect()` is a cheap
   heuristic (India: `UPI/` prefix or `@` handle). `consistency_applicable()`
   returns `False` for transactions where a category consistency check
   makes no sense (ATM withdrawals, P2P transfers) — this is what lets
   the shared validator skip them without region-specific branches.

Register the pack in `cli.py`/`api.py`'s pack lists. The router,
validator, agent loop, and eval harness need **zero changes** — if you
find yourself editing them, the seam is being violated; stop and ask.

Ship it with: normalizer tests, resolver tests (exact / fuzzy / unknown),
a pack-level normalize→resolve test, and a gazetteer big enough to prove
the pack works (India launched with 23 rows — the bar is honesty, not
size).

## Style

Match what's there: small single-purpose files (~100–150 lines), no
abstractions ahead of a second use, stdlib and already-installed deps
before new ones. If you take a deliberate shortcut, mark it with a
`# ponytail:` comment naming the ceiling and the upgrade path — simple
should read as intent, not oversight.
