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

`docs/chester-reports-architecture-v3.md` **is the canonical planning document**
for the system. It is committed, and it declares its own authority in
**Part 26 — FINAL ARCHITECTURE CHANGE ORDER (controlling)**. Read it before
making structural decisions, and prefer it over this file wherever the two
disagree: CLAUDE.md describes the code as it stands, the architecture document
governs where it is going and overrides this file on intent.

`docs/` also carries `chester-reports-master-schedule.md` and
`white-paper-library-guide.md`, plus the white paper library itself in
`docs/whitepapers/`.

**The Markdown is canonical for everything.** A paper's `.md` under
`docs/whitepapers/` holds its text, its tables and its figure references, and it
is the only file anyone edits. Nothing lives only in an HTML edition any more.

- **Figures are files**, under `docs/figures/<slug>/`, named `fig-NN.svg` (or
  `.png` where the source was a raster). Each directory carries an `index.md`
  mapping figure number → caption → file. A paper references one with an
  ordinary Markdown image link, `![Figure N — caption](../figures/<slug>/fig-NN.svg)`.
  Six papers have figures — Currencies (8), the Dealer's Hand (21), Technical
  Indicators (5), Options as Expression (37 panels), Positioning & Flows (1),
  Earnings (9). Every other paper has none.
- **`docs/html/` is build output.** One `<slug>-whitepaper.html` per roster
  paper, written by `tools/build_paper_html.py` with the figures embedded
  inline. `make html` rebuilds all of them. Never edit a file in it, and never
  upload one into it.
- **`make figures`** redraws the eight Currencies charts from
  `altdata/fx_charts.py` and its packaged anchor dataset `altdata/fx_anchors.py`,
  and skips rather than fails when either is absent. It renders into `build/`
  and reports what changed; it **replaces** the committed figures only when
  invoked as `make figures ADOPT=1`. Do not adopt yet — the generator is behind
  the one that drew them, see Known cleanup.

**The rule this replaced, and why the replacement is the point.** For a week the
library ran on "the HTML edition is canonical for reading, the Markdown is
canonical for editing", because six papers' figures existed only inside their
HTML. That rule was written into `docs/white-paper-library-guide.md` on
6 September and deleted the same afternoon by a full-file re-upload from a stale
local copy; it was restored in `8bf2f89` and deleted again hours later by
`a3839ff`, the same way. Three writes, two deletions, one day. The rule was
unkeepable because it asked a human to remember which of two files won, and it
was necessary only because the figures were trapped. Taking the figures out of
the HTML and into `docs/figures/` removed the reason for it, so the rule is
retired: there is one canonical file per paper and it is the `.md`.

**What survives from it is the upload discipline.** A full-file re-upload from a
stale local copy silently reverts whatever the repo learned since — that is what
destroyed the rule twice, and it will destroy prose just as easily. Pull first,
or edit the `.md` in the repository. `make library-check` fails on a figure link
that does not resolve and warns when a built edition is older than its `.md`.

**The library guide is canonical for the papers' series numerals.** A paper's
masthead carries the numeral the guide assigns it; inside a paper, cross-
references to other papers are **by name, never by numeral**, because the
numerals were reassigned once already and every in-text numeral broke.

### Library conventions

- **Cross-references are by name.** Inside a paper's body, other papers are
  cited by name only, title forms ("White Paper I") included. Mastheads keep
  their own numeral and may name their neighbours'. (D1)
- **The Daily Cascade is v2 in the library.** That is its architecture version.
  Report build numbers (v12) live in code and commit messages, not in papers.
  (D3)
- **Rule citations carry their namespace.** Outside the Doctrine, its rules are
  `Doctrine Rule N` — any phrasing naming the Doctrine in the same sentence
  counts. Section-local rules cited from another paper carry the owner's prefix:
  `DC 2.7.1` (Daily Cascade), `DH 18.1` (Dealer's Hand). Inside the owning
  paper, unprefixed dotted IDs stay. Bare `Rule N` outside the Doctrine is not
  allowed. (D4)
- **Filenames** are `docs/whitepapers/<slug>-whitepaper.md`, hyphens only, slug
  from the paper's title, no version or draft number. Superseded editions go to
  `docs/whitepapers/archive/`. (D6)
- **Quoted market levels name their series and as-of date.** Levels are not
  retro-aligned across papers. Spread levels are ICE BofA OAS via FRED
  (`BAMLH0A0HYM2`, `BAMLC0A0CM`, `BAMLH0A3HYC`) unless stated otherwise. (D7)
- **Numerals are stable accession IDs, never reassigned.** They are not reading
  order; reading order is what the guide's tables show. (D8)

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

**`make validate` runs every gate** — 15 of them, no network, no box. It keeps
going past a failure and summarises at the end, because the question after a
change is "what did I break", not "what did I break first"; `make validate-fast`
stops at the first failure for a tight edit loop. The list lives in the
`Makefile` and `.github/workflows/registry-check.yml` reads it from there, so CI
and a local run cannot hold different lists — which is how four validators
drifted out of CI while still passing locally. Adding a gate means adding one
line to the Makefile. (`make` is absent on a stock Windows box; the validators
all run directly too.)

One of the fifteen is the library's own: `tools/check_library.py`, also reachable
as **`make library-check`**, which is the one to run while editing a paper rather
than code. It enforces the Library conventions above — cite by name, the masthead
owns the version, one namespace per rule, consecutive parts and figures — plus
the guide's roster, every path this file names, every link under `docs/`, and
every figure link a paper carries. It fails on those and warns on a built
edition older than its `.md`, a stale word total, and a forward reference to a
paper that now exists.

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

**`altdata/fx_charts.py` is behind the generator that drew the committed
Currencies figures, and has to catch up before it can replace them.** The
module, its anchor dataset and matplotlib are all in place and an online run
completes, but three things say the committed set came from a later fx_charts
than the 3 September snapshot:

- **Curated marks.** `fx_anchors.py` carries `marks_long` and `marks_five` —
  hand-written callouts like "8.28 peg", "1997–2005", "now". The committed
  figures draw them. `fx_charts.py` never reads either field: `fig_currency`
  calls `_extreme_label()` and marks the series min and max instead, which for
  USD/CNY lands on the December-1996 start point rather than the peg era.
- **Source default.** The committed figures are the offline anchor
  reconstruction — their captions say so outright — while the generator
  defaults to live daily FRED history and only falls back to anchors. Roughly
  180 path nodes a chart against 1,300, and the data moves with it: USD/THB's
  thirty-year range reads "25.3 to 55.8 (~75% of the midpoint)" committed and
  "22.75 to 56.1 (~85%)" regenerated; USD/CHF's span goes ~88% to ~86%.
- **Captions.** `_caption()` must produce what the paper's Part V note and
  `docs/figures/currencies/index.md` already say — annual anchors with daily
  extremes marked, indicative of range and not tick data — rather than
  contradicting them.

Until all three are fixed, **the committed figures stay canonical.**
`make figures` therefore renders into `build/figures/currencies/` and prints a
per-file report from `tools/diff_figures.py`; it writes into `docs/figures/`
only when invoked as `make figures ADOPT=1`, which is a deliberate act that
also obliges reconciling the captions and the Part V note.

Fix the `:286` NumPy `DeprecationWarning` in the same pass — `s.index.max() +
pd.Timedelta(days=40)` on a bare integer, seven warnings per run today and an
error in a future NumPy.

**`altdata/report/` is content, not a pipeline.** The Alternative Asset report
is not produced by any running pipeline in this repo. This package is its
designed report layer, vendored from the 3 September 2026 snapshot and kept as
content and reference for folding the report into the Monthly under the system
redesign. Nothing schedules it, no Makefile target names it, and no other
module imports it.

It is a subpackage, so its `sources.py` sits at `altdata.report.sources` and
does not shadow the `altdata/sources/` package. Seven of its thirteen modules
do not import against the current `altdata/` — they want `altdata.analytics`,
which does not exist here, and `altdata.config.ASSETS` / `ASSETS_BY_ID` /
`BENCHMARKS`, which this repo's `config.py` does not define. The six that do
import are the ones worth having: the narratives, the case and positioning
material, and the peer and source tables. Do not repair the other seven in
place — what they should become is a question for the redesign, not a patch.

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
