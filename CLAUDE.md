# CLAUDE.md

## What this project is

`chester-reports` is a five-report market intelligence system. Each report is an
independent generator that pulls data, computes derived metrics, renders a
Markdown + styled-HTML document, and emits a small state record to a shared
Cloudflare Worker so one dashboard can show the health of all five at a glance.

| Report | State key | Status in this repo |
|---|---|---|
| Monthly Macro | `monthly_macro` | **Built** — the only implemented pipeline |
| Disruptive Themes | `disruptive_themes` | Not yet built |
| Top & Bottom | `top_bottom` | Not yet built |
| Alternative Asset | `alt_asset` | Not yet built |
| Daily Cascade | `daily_cascade` | Not yet built |

The state keys are already reserved in `state/emit.py:VALID_KEYS` (which also
carries a sixth, `gamma_weekly`). Treat that set as the registry of report
identities — a new report adds its key there before anything else.

`docs/architecture-v3.md` **will be the canonical planning document** for the
system once it is committed. It does not exist in the repo yet. When it lands,
read it before making structural decisions, and prefer it over this file wherever
the two disagree — CLAUDE.md describes the code as it stands, architecture-v3
describes where it is going.

## Repo layout

```
altdata/                  Shared ingestion package — used by every report
  config.py               Series registry: 59 SeriesSpec entries (key, fred_id,
                          description, pillar, units, freq) + ENABLED_SOURCES
                          switches (fred on; eia/cftc/coingecko off)
  store.py                Store — one CSV per series, columns date/value/source/
                          as_of. Reads $ALTDATA_STORE, default ./data_store
  sources/
    _base.py              http_get_json: timeout, retry w/ backoff, FetchError
                          (4xx surfaces immediately; 5xx retries)
    fred.py               Pulls every config.FRED_SERIES into the store
    yfinance_source.py    27 market symbols -> store keys prefixed mkt_

monthly_macro/            The one built report
  run.py                  Entry point: python -m monthly_macro.run
  compute.py              Derived metrics (Sahm, YoY, 2s10s, r-vs-g, net
                          liquidity). Never raises — missing input returns
                          {value: None, inputs: {...}, as_of: None}
  snapshot.py             Writes snapshots/<report_date>.json each run; compares
                          against the newest snapshot strictly BEFORE today so a
                          same-day re-run still compares to last month
  narrative.py            Phase 5 LLM step: replaces
                          *[NARRATIVE PLACEHOLDER — ...]* markers via the
                          Anthropic API. MAX_CALLS cost guard. Degrades in three
                          layers (no key / call fails / package missing)
  writer/
    render_md.py          Deterministic data -> Markdown, organized by pillar
    build_html.py         Markdown -> navy-styled <details> accordion HTML

state/emit.py             POSTs one report's state to the Worker. Never raises.
                          Producers report as_of, never freshness — the Worker
                          computes staleness at read time so a dead pipeline
                          cannot claim to be healthy.

data_store/               Committed CSV store (59 FRED series)
snapshots/                Committed per-run JSON snapshots
reports/                  Generated .md / .html output
smoke_test.py             Full pipeline against a synthetic store, no network
.github/workflows/
  monthly-report.yml      workflow_dispatch; installs deps, runs the report,
                          uploads artifacts BEFORE committing the snapshot, then
                          best-effort rebase-and-push of snapshots/
```

Environment: `FRED_API_KEY`, `ANTHROPIC_API_KEY`, `ALTDATA_STORE`,
`SNAPSHOT_DIR`, `NARRATIVE_MODEL`, `CHESTER_STATE_URL`, `CHESTER_STATE_TOKEN`.

Running: `python -m monthly_macro.run --verbose`; add `--skip-fetch` to render
from the existing store and `--skip-narrative` to skip the LLM step.
`python smoke_test.py` for a no-network end-to-end check.

### Known cleanup

Resolved: the root-level `compute.py` (a misplaced copy of
`altdata/sources/__init__.py`'s docstring) and
`.github/workflows/monthly_macro/__init__.py` were deleted, the package
docstring they carried now lives in `monthly_macro/__init__.py`, `README.md` is
a real readme, and `smoke_test.py` writes to `tempfile.gettempdir()` with
explicit UTF-8 so it runs on Windows.

Still open: `.github/workflows/.gitignore` duplicates coverage the root
`.gitignore` already provides. And `monthly_macro/run.py` has the Windows
encoding bug `smoke_test.py` just shed — `Path.write_text()` and the closing
`print` both assume a UTF-8 default, so a local run on Windows will fail on the
report's check marks. CI is Linux, so this only bites locally.

## Standing rules

### 1. No Brookfield-related securities recommendation is ever generated

No report may output a buy, sell, hold, rank, screen hit, or any other
recommendation touching a Brookfield-related security — Brookfield Corporation,
Brookfield Asset Management, Brookfield Renewable, Brookfield Infrastructure,
Brookfield Wealth Solutions, their affiliates, subsidiaries, spin-offs, and
associated tickers.

Enforcement is at **write time, in the register** — the register rejects them
when a recommendation is written, not in a prompt, not in a post-hoc filter, and
not by asking the model nicely. This is a hard invariant: any new
recommendation-producing path must route through the register, and any change
that lets a recommendation reach output without passing the register is a bug
regardless of what else it does.

### 2. Gotchas

**Unit mismatch in net liquidity.** `WALCL` (`fed_balance`) is in **millions**
while `RRP` and `TGA` are in **billions**. Normalize before subtracting —
`fed_balance / 1e6` and `rrp / 1e3`, `tga / 1e3` to reach trillions. Subtracting
raw values silently produces a number off by three orders of magnitude that still
looks plausible. `monthly_macro/compute.py:fed_net_liquidity` handles this
correctly today; preserve it, and re-check the unit of every new series against
`config.py`'s `units` field rather than assuming.

**FRED deprecates series silently.** Roughly one to two of the configured series
per year stop updating or disappear without notice, and the API returns an empty
or stale observation set rather than an error. The pipeline is built for this:
a failed series never kills a run, failures collect into the fetch summary and
surface in the report appendix. When a metric goes quiet, check the series on
fred.stlouisfed.org before assuming a code bug, and replace the `fred_id` in
`config.py` rather than deleting the `key` — downstream code and prior snapshots
reference the key.

**Never paste secrets into any chat, commit, or file.** API keys and tokens live
in `.env` (gitignored) locally and in GitHub Actions secrets in CI. Committed
files carry placeholders only. This includes pasting a key into a conversation to
"just test something" — a key that reaches a transcript or a commit is a leaked
key and must be rotated.
