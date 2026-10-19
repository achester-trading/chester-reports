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
carries `gamma_weekly`, the EOD options pass, and `weekly_tactical`, the Weekly,
added 6 Oct 2026). Treat that set as the registry of report
identities — a new report adds its key there before anything else.

`docs/chester-reports-architecture-v3.md` **is the canonical planning document**
for the system. It is committed, and it declares its own authority in
**Part 26 — FINAL ARCHITECTURE CHANGE ORDER (controlling)**. Read it before
making structural decisions, and prefer it over this file wherever the two
disagree: CLAUDE.md describes the code as it stands, the architecture document
governs where it is going and overrides this file on intent.

`docs/` also carries `chester-reports-master-schedule.md` and
`white-paper-library-guide.md`, plus the white paper library itself in
`docs/whitepapers/`. `docs/scheduled-tasks.md` lists the chat-side scheduled
tasks, which the box's units do not declare.

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
                          description, pillar, units, freq) in FRED_SERIES, the
                          Monthly's set; 27 more in FRED_SIGNAL_SERIES (ST-1/2),
                          pulled and freshness-watched; 43 in five smaller
                          lists (FX scan 18, SLOOS 5, AQ-3 7, SR-43 12,
                          Thailand 1); 25 in FRED_6E_SERIES (6e, the rest:
                          Session 3b-3c and the CPI lead's components);
                          45 in FRED_RELEASES_SERIES (Batch 7's release
                          lenses, Group A); 29 in FRED_GROUP_B_SERIES
                          (Group B, the PPI and GDP lenses);
                          FRED_PULL_SERIES, 228, is the union the
                          pull walks.
                          + ENABLED_SOURCES switches (fred, eia and cftc on;
                          CoinGecko is no source and has no switch)
  store.py                Store — one CSV per series, columns date/value/source/
                          as_of. $ALTDATA_STORE from the environment, else from
                          .env, else ./data_store. On the VPS it is set in .env
                          to ~/chester-data/data_store, OUTSIDE the checkout, so
                          no pass writes the tracked data_store/ that git pull
                          --ff-only needs clean; the writing units allow it in
                          ReadWritePaths and the backup sweeps it
                          (deploy/systemd/README.md section 11)
  sources/
    _base.py              http_get_json: timeout, retry w/ backoff, FetchError
                          (4xx surfaces immediately; 5xx retries)
    fred.py               Pulls every config.FRED_SERIES into the store
    yfinance_source.py    106 market symbols -> store keys yfinance.mkt_<sym>
  market_features.py      calc.* series: breadth, trend, realized vol — and the
                          macro transforms that were monthly_macro/compute.py
                          (Sahm, the YoY family, 2s10s, r-vs-g, net liquidity).
                          Computed from the OBSERVATION store, one pass after
                          every price fetch. A row's available_at is the MAXIMUM
                          across its inputs' — a feature is never knowable before
                          the data it is made of
  correlation.py          The correlation layer (AQ-5): rolling 60/252-session
                          return correlations across config/correlation.yaml's
                          universe, the former report's 30-vs-120-day break, a
                          shift flag per pair, the named rows. Rides the
                          market_features pass (last few sessions); the full
                          history is `compute --backfill`. Narrow flags only
  thesis_register.py      AQ-6: the Quarterly's theses, ledgered under
                          alt_asset:<family>. Loads the operator's
                          config/alt_asset_theses/<YYYY>q<N>.yaml (measurables
                          only), resolves from the store as of, grades sets by
                          ordering and direction, writes book DRAFTS only; reached
                          through `python -m altdata.probability_ledger
                          seed-alt-asset | show | resolve-alt-asset`

monthly_macro/            The Monthly. Since T3 it is the STACKED Monthly: the ten
                          sections at Monthly depth, Slow layers eleventh, then the
                          detail tables (the regime, the scenario record, the
                          register's month, the appendix); the Monthly v2 render is
                          its fallback when the stacked edition faults
  run.py                  Entry point: python -m monthly_macro.run
  stack.py                The stacked edition: builds the sections through the
                          Weekly's builders at cadence "monthly" and the one
                          stack.assemble(), reconciles Monthly v2 Phase A into
                          them (each fact printed once), enforces the 10,000-word
                          budget (T3.1), opens on the executive summary written
                          last from the finished sections, archives the edition
                          JSON. At cadence "quarterly" the same build() makes
                          the Quarterly's front matter
  quarterly.py            AQ-1: the Alternative Assets Quarterly, the fourth
                          cadence (`run --cadence quarterly`). The stack's ten
                          sections over the previous quarter as front matter,
                          the eleven family chapters (config quarterly_chapters,
                          the section 4.1 template) as slow layers; every section
                          and item tiered lead or reference; the read timed apart
                          from the whole edition; state key alt_asset. Timer
                          chester-quarterly.timer ships disabled
  dealer.py               Mechanics' dealer retrospective: the month's stored
                          dealer.scorecard_day rows, per-session flags by the
                          Weekly's rule, counts and hit rates; "insufficient
                          sessions (n=...)" below 20; the flag-word audit
  snapshot.py             Writes snapshots/<report_date>.json each run; compares
                          against the newest snapshot strictly BEFORE today so a
                          same-day re-run still compares to last month
  payload.py              Six sections of change: regime (read from the object),
                          scenarios with a Brier beside every weight, Top &
                          Bottom, alternative assets, the register's month, and
                          the appendix. Absences carry reasons; ends in
                          precision.apply so no figure is carried at a precision
                          the report would not print
  pillars.py              Reads config/pillars.yaml: eleven pillars mapped onto
                          the three dials with declared weights. Maps and reads;
                          computes no pillar state
  narrative.py            The Monthly's brief and template path. One paragraph
                          over one payload, long form, behind the numeral audit.
                          The ten per-pillar placeholders are gone
  writer/                 (the stacked Monthly renders through
                          daily_cascade/stack_render.py at cadence "monthly")
    render_v2.py          The v2 report (the fallback): six sections in payload
                          order, each pillar printed beneath the dial it feeds
    build_html.py         Markdown -> navy-styled <details> accordion HTML

state/emit.py             POSTs one report's state to the Worker. Never raises.
                          Producers report as_of, never freshness — the Worker
                          computes staleness at read time so a dead pipeline
                          cannot claim to be healthy.

data_store/               Committed CSV store (59 FRED series) -- the laptop's
                          and CI's store; never written on the box
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
`--dry-run` builds with the model, reads the real archive's prior Monthly and
writes only to `reports/dryrun/` (no fetch, snapshot or state record); add
`--email` to send it once under a "[DRY RUN]" subject.

**`make validate` runs every gate** — 100 code gates (97 Python,
three shell) and seven data gates, no network, no box. **A code gate never reads the live store**: each seeds a
temporary store of its own, so its verdict is about the commit and is the same
in CI, on the laptop and on the box. Checks about the box's real history are
data gates (`GATE_KIND = "data"`, the Makefile's `DATA_GATES`), which report
without setting the exit code and print NOT VALIDATED where there is no store.
It keeps
going past a failure and summarises at the end, because the question after a
change is "what did I break", not "what did I break first"; `make validate-fast`
stops at the first failure for a tight edit loop. The list lives in the
`Makefile` and `.github/workflows/registry-check.yml` reads it from there, so CI
and a local run cannot hold different lists — which is how four validators
drifted out of CI while still passing locally. Adding a gate means adding one
line to the Makefile.

`make` is absent on a stock Windows box, so **`scripts/make.sh` is the same
targets for a machine without make** — `bash scripts/make.sh validate`,
`validate-fast`, `data-gates`, `html`, `library-check`, `list`. It parses the gate
list out of the Makefile rather than carrying a copy, so it cannot become the
third place the list lives; it resolves the venv interpreter the same way the
Makefile does; and it deliberately wraps neither `figures` (whose `ADOPT=1` mode
overwrites the committed figures) nor the deploy (which stays one shape, in
`scripts/deploy.sh`). Every validator also still runs directly.

One of them is the library's own: `tools/check_library.py`, also reachable
as **`make library-check`**, which is the one to run while editing a paper rather
than code. It enforces the Library conventions above — cite by name, the masthead
owns the version, one namespace per rule, consecutive parts and figures — plus
the guide's roster, every path this file names, every link under `docs/`, and
every figure link a paper carries. It fails on those and warns on a built
edition older than its `.md`, a stale word total, and a forward reference to a
paper that now exists.

**Reports read the market-state object; no report recomputes regime.** `regime.py`
computes one object per session day from the declared rules in
`config/market_state.yaml` — eight dimensions, three dials and an eight-row
contradiction table — and the 16:45 close pass is its only writer. Every report
reads it through `regime.latest()`: the 07:00 morning anchor does not recompute,
because an anchor computing its own object could disagree with the close report's,
and then the system holds two regimes with no way to say which one a decision was
taken under. The **07:00 morning anchor** opens on a **WHAT CHANGED** block rendered
by `daily_cascade/state_block.py`, with every magnitude stamped with its percentile
and the levels moved behind it, and so does the pre-stack `--classic` close. The
live stacked close does NOT open on it: ruled 6 Oct 2026, the state and
contradiction tables belong at the END of the stacked close as detail tables, and
they are built (T2.6) -- `state_block.detail_tables()` reads them from the stored
object the payload carries, never recomputing, and `stack_render.details_html()`
prints them after section 10 and before the glossary.

**One stack, four cadences (T2.6; AQ-1).** The close, the Weekly, the Monthly and
the Quarterly share the section builders, the renderer, the prose and the
paragraph guard, each taking a `cadence` ("daily", "weekly", "monthly",
"quarterly"). What differs is config, under
`cadences:` in `config/reporting_stack.yaml` (period noun, column head, depth
allowances, paragraph rule, prompt frames, guards), read through
`daily_cascade/cadence.py`, whose `Period` builds every period phrase ("on the
week", "This month"). No section hard-codes "week": a new phrase goes in `Period`.
The Monthly's long form is the same renderer's (T2.7): `stack_render.page_html` and
`stack_render.markdown` print a whole edition at any cadence; at "monthly" a
sub-section carries its own charts and notes, a Reading entry's stored summary
prints verbatim (escaped, never polished, audited or trimmed; in the reading time,
never in the budget), and `stack.trim_to_budget` cuts paragraphs to the 10,000
words (T3.1 item 22; 7,000 before). A section declared at one cadence only (Reading) is skipped at the others
(`stack.section_ids`).

**Each family of metrics is measured its own way (6e, the metric lenses; ruled
1 Oct, ratified 4 Oct 2026).** Every level series in the registry carries a
`family` -- price, rate, spread, release, quantity, conditions or ratio -- in the
`families` map, a block's `family` or `member_families`; a series that is not a
level is named in `lens_excluded` with its reason. `derived.lens_forms()` computes
the family's forms (returns and drawdown flags for a price; bp changes for a rate;
YoY, 3-month annualized and the revision line for a release; direction for a
quantity; dual percentiles with n wherever a level is placed), point-in-time,
and the Monthly v2 pillar tables print them. A monthly release never shows a
20-session change. `tools/validate_lenses.py` holds it.

**6e, the rest (16 Oct 2026): macro completeness and the bound lenses.**
`altdata/macro_6e.py` writes, in the market_features pass, the architecture's
Session 3 series the free sources carry: path divergence (S3a, the close against
the noon fixing), the policy spreads, differentials and real policy rate (S3b),
the twelve-month deficit, interest burden, effective rate, R less G on both bases,
the TGA's range and debt against GDP by sector (S3c), the core CPI less core PCE
gap, and `altdata/cpi_lead.py`'s CPI lead composite (stated lags, unvalidated,
with its kill test). The lens thresholds and the surprise's "no consensus" are
`config/metric_lenses.yaml`'s; the 10-year's lens carries the SR-43 anchors and
fair value. `daily_cascade/lens_cells.py` formats the cells once, so the Weekly's
and the close's lens tables print the Monthly's forms; `daily_cascade/
inflation_block.py` holds Plumbing's inflation panels, with slots for Batch 7
items 46 and 48. `tools/validate_6e_rest.py` and `tools/validate_lenses.py` hold
it.

**The release lenses (Batch 7 items 46 and 48, Group A; 6e-releases, 16 Oct
2026).** `altdata/releases.py` reads, as of the cutoff, the CPI decomposition (five
contributions, the Cleveland Fed median and trimmed mean, the share of 24
categories above 4% annualised), item 46's pass-through flag, employment lenses
1-6 and CPI lenses 7-11; thresholds in `config/releases.yaml`. Flags only where
the order names them (diffusion, revisions, permanent job losers, pass-through),
each withheld when it needs a vintage not yet published. The inflation block
prints the CPI panels; `daily_cascade/labour_block.py` is the Monthly's own section
after Plumbing (Monthly only, no paragraph); the close carries one code-written
"what moved the print" item on a release's day. New readers:
`altdata/sources/rent_indices.py` (Zillow, Apartment List; the CPI lead's shelter
lead) and `altdata/sources/clevfed_rules.py` (the Cleveland Fed's policy-rules
path, not market pricing). The BLS API and data.bls.gov disallow every agent in
robots.txt, so the CES industry diffusion indexes, birth-death and the new-tenant
rent index are listed gaps. `tools/validate_releases.py` holds it.

**Group B and the surprise index (Batch 7 item 48 lenses 12-20 and 48f;
lenses-group-b, 18 Oct 2026).** `altdata/releases_b.py` reads, as of the cutoff:
- the PPI lenses: the four intermediate-demand stages against final demand, the
  PCE-relevant lines (NSA, read on the year) and trade services beside the core
  less trade, in the inflation block's `ppi` panel, which is Monthly-only
  (ruling 5 of 18 Oct; the close keeps the release-day line);
- the GDP lenses: final sales to private domestic purchasers and BEA's
  contributions, the investment split (structures less the Census's data
  centers, read by name), GDI less GDP, NIPA profits against S&P EPS, income and
  saving, and GDPNow's path from its FRED vintages with the first print read
  against it. They are two tables at the end of the Monthly's Slow layers
  (`daily_cascade/gdp_block.py`).

Every lens figure carries its family, its long window, two percentiles over its
own history with their n, and the 30-point disagreement. Report-only, no
composite. The NY Fed nowcast and the K-shape panel are listed gaps.
`altdata/surprise_index.py` is actual less consensus in the release's own units,
standardised by the release's own surprises, with no composite (the order
defines none). Its rows ride `altdata.surprise compute`
(`calc.consensus_surprise.<id>`, `_z.<id>`, `_z.earnings` per name). The
consensus logger's yfinance serves no macro consensus, so every macro release,
payrolls among them, prints "no consensus" (ruling 5 of 18 Oct). The FOMC
surprise is **market-implied, not a survey consensus** (ruling 1 of 18 Oct): the
decision less the change the stored fed funds futures implied at the prior
session's close, in bp, standardised the same way, under its own keys
(`calc.market_implied_surprise.fomc`, `_z.fomc`) so no survey consensus is
mixed with it. Lens 24 gains the PPI and GDP lines, and every line's surprise
clause carries its percentile and z once a consensus is stored; the edition's
first z says "against the release's own surprise history". Engine 4 reads the
consensus surprise by name ahead of the naive one (for FOMC, the market-implied
key). `tools/validate_releases_b.py` holds it.

**The PRL data layer (signal-triage ST-13, Tranche 5; st-t5-prl, 18 Oct 2026).**
PRL is the Security Master's first `crypto.watch` instrument (SM00118,
reclassified in place). It is keyed by its CoinGecko id (`crypto_id
coingecko:pearl-2`, `Master.by_coingecko`) and carries MW-1's fields under
`watch`. A watch entry keyed by a ticker is refused by `structural()`, and it
has no FIGI, so the chester-meme export never carries it.
- `altdata/prl.py` holds Appendix E's emission (`reward`, `supply_code`) and
  D1-D6 as `calc.prl_*`, with the thesis status and its trace. A height with no
  explorer read is ESTIMATED, stepped at the 194 s target, never blank.
- **CoinGecko stays retired** (13 and 18 Oct 2026: its terms forbid the
  point-in-time store; MW-4's clause is superseded). No fetcher and no switch are
  kept.
  - PRL's price and 24h volume are Yahoo's at the basket's symbol; its cap and
    circulating supply are DefiLlama's coin service's.
  - D5 is "not tracked (source retired)".
  - D3 is the formula against the explorer's supply, ESTIMATED until the
    explorer reads.
- `altdata/sources/pearl_explorer.py` reads only a declared endpoint that
  robots allows (G-26: none discovered yet).
- Both steps run in the crypto basket's 17:25 run (`altdata.prl weekly` on
  Saturdays, `altdata.prl daily` after the basket's writes; no new timer). They
  are on the freshness roster (`prl`).

Config is `config/prl.yaml`. Watch-level rights only, and no Daily module names
PRL. `tools/validate_st_t5_prl.py` holds it.

**The Monthly's Mechanism Watch part and the emerging scan (ST-14, ST-15;
st-t5-render, 18 Oct 2026).**
- **The part.** `monthly_macro/prl_part.py` prints in the slow layers, after the
  digital-assets material. It holds the thesis with its trace (a label, never a
  recommendation), the S1-S8 table with "not tracked" and ESTIMATED where the
  inputs say so, and the register's month.
  - It reads stored rows and computes nothing.
  - Its guards: the Security Master entry, the explorer's supply within 2% of the
    formula, STALE never empty.
  - Its one figure, M13, draws only once the explorer has read.
- **The scan.** `altdata/mechanism_scan.py` runs the `mechanism_watch` group of
  `config/story_queries.yaml` over declared feeds under robots
  (`news.mechanism_items`), and DefiLlama's recently-added list.
  - It dedupes against the Security Master and the register, then applies the
    rule pre-filter.
  - Only when a candidate survives is the model called, once, with Appendix F
    read verbatim from the order.
  - It writes drafts only, into the `mechanism_watch` tables of
    `altdata/mechanism_watch.py`.
  - `promote` and `reject` write only with the operator's `--confirm`.
  - It is a Saturday step of the crypto basket's run; `make mechanism-register`
    renders the register. `tools/validate_st_t5_render.py` holds it.

**The Digital Assets addendum (Batch 8 item 51, Phase 1, and item 49c; 6e-digital,
17 Oct 2026).** Not a sixth report: `daily_cascade/digital_addendum.py` builds a
page of its own in the Sunday Weekly's run, before the Weekly, archives it beside
the Weekly (`weekly_digital_<ending>.html` and `.pdf`, its edition JSON and its
appendix line) and attaches it to the Weekly's own email as a second PDF (ruled
17 Oct 2026); the Weekly prints one line naming
it, and a failed addendum costs only the addendum. A Sunday before the first edition (the Weekly of 1 Nov 2026) builds it as a dry run under `reports/dryrun/` only. Nine code-written sections in
the ruling's order (`config/digital_addendum.yaml`, its budgets session-set: five
minutes, 1,100 words, two charts); every Batch 4 Tranche A cell prints "awaiting
Tranche A" until its key has a row; the read is one paragraph through the
existing narrative step and its audits, from the page's figures only. The X
pilot's ledgers and digests are read from the box's inbox, which the nightly
sweep fills from the Drive folders chester-x-digest and x-triage,
each file's available_at its `.copied_at` stamp. The book section opens the
register read-only (`mode=ro`). The dated index events (the STRC vote, MSCI's
review, FTSE Russell's reconstitution) are `config/digital_asset_calendar.yaml`,
by hand, which the Weekly's Ahead also reads. `tools/validate_digital_addendum.py`
holds it.

**The crypto data layer, Batch 4 Tranche A part 1 (crypto-tranche-a-1, 17 Oct
2026).** Keyless writers on `feeds.EXTERNAL_WRITERS` and on the crypto basket's
daily run (`scripts/run_crypto_basket.sh`, which covers the weekend): perp funding
and open interest from Hyperliquid (`altdata/sources/hl.py`, behind a weight guard
under its documented 1,200-a-minute limit) and from OKX and Deribit
(`altdata/sources/fut.py`; Bybit is geo-blocked from the US and switched off);
Bitcoin's network state (`mempool.py`); the fear-and-greed index (`fng.py`);
Ethereum's gas and activity, keyless, from Blockscout (`blockscout.py`; Etherscan's
key was not registered, so ETH supply and burn are a gap). DefiLlama's watch names
resolve their slugs at run time (`llama.py`). `altdata/sources/crypto_derived.py`
writes S-1's share by chain and S-3 (OI-weighted funding, total OI, OI over market
cap, 90-day z), which begin when two venues carry OI on the same day. Every row is
point in time: the pull instant as available_at, complete UTC days for history.
Config `config/crypto_sources.yaml`; `tools/validate_crypto_sources.py` holds it.

**Part 2 (crypto-tranche-a-2, 17 Oct 2026)** adds four more writers:
- Deribit's DVOL (`deribit.py`, from March 2021);
- Farside's ETF flow tables (`farside.py`), with a column-change detector, STALE
  with its last good date on any refusal, and a 06:45 read for the T-1 figure;
- the froth gauge's sample (`gt.py`), which reads nothing while GeckoTerminal's
  robots.txt disallows its API, with a DexScreener fallback marked in the row and
  never scored;
- CoinPaprika's total market cap and BTC dominance (`paprika.py`), in place of
  CoinGecko.

`crypto_derived.py` computes S-1 to S-5 and stores the three flags with gate status
"not passed"; no block prints a flag. `altdata/crypto_blocks.py` prints the Weekly's
crypto flows block (at most 12 lines, a table in Positioning & flows) and the
Monthly's network-health and data-layer rows, every Monthly row in the triple form
with dual percentiles. The daily paragraph and the 12:30 line are Tranche B.

**CD-12 (Tranche C; alpha-lab-4, 19 Oct 2026; ruling 2 of 19 Oct): SR-29 reads
the operator's free key.** bitcoin-data.com serves the long- and short-term-holder
supply and has no robots file; its terms (14 Oct 2026) make the API a free-key
service and forbid redistribution, not the store (`source_registry.yaml`
`bitcoin_data` quotes them). `altdata/sources/btcdata.py` reads
`BITCOIN_DATA_API_KEY` from `.env`, sends it as a Bearer header, and writes
`btcdata.lth_supply`, `.sth_supply`, `.supply_current` and
`btcdata.lth_supply_share` (computed, LTH over current x 100), available at the
pull. Its guard counts every request in a state file and refuses the 9th in an
hour and the 16th in a day; no retry. One request per series a day, in the
crypto basket's 17:25 run (no new timer, not on the external roster). Without the
key it fetches nothing and the Monthly and the addendum print "not tracked
(btcdata.lth_supply_share): no key in .env (BITCOIN_DATA_API_KEY)". No by-hand
line (rule 30). CD-11 (Dune) stays unbuilt, a listed gap (ruling 3).
`tools/validate_crypto_sources.py` group O holds it.

**Item 49 and the addendum's Phase 2 (digital-49-51b, 17 Oct 2026).**
`altdata/sources/treasury.py` stores three inputs:
- the treasury companies' BTC holdings, from BitcoinTreasuries.com's table
  (treasuries.bitbo.io);
- Strategy's share count, from EDGAR, which needs `CHESTER_SEC_CONTACT`, otherwise
  a listed gap;
- MSTR's spot, from the captured chains.

`crypto_derived.py` computes `calc.mnav` (market cap over BTC value, the order's
basic definition) and `calc.treasury_net_purchases`. The Digital Assets addendum's
panels read Tranche A by key:
- mNAV carries the 1.2 watch line and item 49's one flag at 1.0, which prints with
  its date;
- "who is buying" sets ETF flow and treasury purchases against new supply, and
  withholds the residual when a leg is missing;
- an absent series prints "awaiting the first pull", "not tracked" or "awaiting
  EL-12".

The page holds Phase 1's 52-line budget, and the read's audits gain a flag-word
check. `python -m altdata.sources.treasury show` reads mNAV for the MSTR/MSCI
watch, read-only.

`altdata/derived.py` is the one place a delta, a percentile or a z-score is
computed — the delta's meaning comes from the registry's `units` (bps for rates
and spreads, percent for prices, raw for counts), never from one formula. Do not
add a second regime anywhere: if a report needs one, point it at the object. ST-3's rates attribution is deliberately NOT
part of it: `altdata/rates_attribution.py` prints each model's path/premium split,
dated, and a models-agree flag, and decides nothing. The four-cell driver it
replaces failed its gate twice and was withdrawn; config v1.11/v1.12 and
method-9/10 are retired numbers, so the next bumps are v1.13 and method-11.
Dimensions whose data is missing or stale are absent, each with its reason, rather
than substituting a proxy; the count varies by session. Full schema, rules and the v1/v2 boundary: `docs/market-state.md`.

**Voices are stored and sourced before they are printed (Phase B, 4 Oct 2026).**
`altdata/sources/voices_scan.py` runs once a day on its own timer
(`chester-voices.timer`, 06:15 ET, a fifteen-minute budget) over the public
sources declared in `config/voices_sources.yaml`, officials first, then desks,
then news. It obeys robots.txt, identifies itself with the EDGAR contact in a
browser-like User-Agent, and makes one model call per new item under a daily
cap. A source the box cannot read is declared unreachable with its reason. `altdata/voices.py` refuses any row without a URL, a published
date, a retrieval instant or a tier, and never stores the article body. Status
(NEW / REITERATED / INFLECTED / SILENT) is computed from the stored directions;
the model never declares it. `daily_cascade/voices_block.py` is the only renderer,
for the close's Narratives line, the Weekly's section 8 and the Monthly's section
4, and it audits every printed view.

The Google News story-query fetch is retired: its robots.txt forbids it. The scan
now writes those `headline` rows under each story's declared query.

**What the store holds is listed, searched and checked against the registry
(AUD-3a, 14 Oct 2026).** `python -m altdata.catalogue` lists every resolved key
(`list --domain/--kind/--source/--cadence`), searches ids, descriptions and
aliases (`search TEXT`), reads one key whole (`show ID [--db PATH]`: its fields,
units, delta rule, block and producing command) and prints the per-domain
commands (`commands`, declared in `config/catalogue_commands.yaml`).
`python -m tools.check_store_registry --db PATH` opens a store read-only and lists
the stored keys the registry does not know, the registered keys with no rows, the
stale keys by their own allowance, and the stored source strings on no list
(`altdata/source_ids.py` reads `<id>:<variant>` as the id; the store is never
rewritten). **`percent` is split by meaning**: `percent_rate` (a yield or rate, its
change in bp), `percentile` (points), `percent_return` and `percent_share`
(percentage points), `vol_pct`, `vol_index` and `index_points` (points; ^SKEW);
`check_registry` refuses the undivided word, and a renderer formats a level
through `derived.level_units_of()`, so a split unit prints as it did. FRED's
shares and rates of change carry their own unit in their block (`member_units`,
pp); its yields, rates and spreads keep bp (15 Oct 2026). The move screen pins
the volatility indexes and SKEW to log changes in `config/move_screen.yaml`. `tools/validate_audit_3a.py`
holds the counts this file prints against the code.

**Every model call goes through one client and is counted (AUD-2, 14 Oct 2026).**
`altdata/model_meter.py` builds the one Anthropic client (timeout 90 s, one retry)
for every report path, and `model_meter.create()` writes a row per call to the
`model_calls` table in chester.db: run id, report, section, attempt, model id, input
and output tokens, time. A call outside a report's `scope()` writes nothing. The
close's footer prints the day's calls and tokens, the Monthly's the month's by
report; tokens, never dollars. **A restore is drilled, not assumed:**
`python -m tools.restore_drill` restores the backup's newest database snapshot into a temporary
directory, integrity-checks it and counts it against the live store, read-only;
`docs/runbooks/restore.md` is the dead-box procedure. `tools/validate_audit_2.py`
holds the auction sampler's stand-aside, the meter's client and the drill.

**Backups are encrypted, go to a separate account, and are restored every week
(audit-leftovers-1, 17 Oct 2026).**

- `scripts/rclone_sync.sh` sends every tree to an rclone crypt remote that
  `scripts/rclone_crypt_env.sh` builds from `.env`. The trees are the db
  snapshot, data, chester-data, state, reports and the EOD zips; the settings are
  `CHESTER_RCLONE_BACKUP_REMOTE` (a Drive used only for backups),
  `CHESTER_RCLONE_CRYPT_PASSWORD` and `CHESTER_RCLONE_CRYPT_SALT`. File names are
  encrypted too, and nothing secret sits in `rclone.conf`.
- Without those settings the sweep exits 1 (`no_crypt`); the old plaintext
  remote is never written.
- The inbound files come from the main Drive through
  `CHESTER_RCLONE_INBOX_REMOTE`, a read-only token.
- Retention: the db snapshots keep 14 daily, 8 weekly and monthly forever; the chain zips
  keep the newest 14 on the box and on Drive alike.
- The sweep records the snapshot's row count in the state directory's
  `backup_snapshot`.
- `chester-restore-test.timer` (Sundays, enabled by hand) restores the newest
  snapshot through the crypt remote, integrity-checks it, compares the count and
  writes `restore_test_status`. The heartbeat's `backup=` field reads it:
  `failed:restore_test`, `stale_restore:<d>d`, both exit 12.

**Scheduled writers open the store through `observations.open_writer(name)`**
(WAL, the busy timeout, the writer's name: D1c as one function). Once
`python -m altdata.observations install-triggers` has run on the box, two
triggers refuse UPDATE and DELETE on `observations`. The one exception is
`observations.maintenance()`, a row inserted and removed inside the caller's own
transaction, which the FRED compaction and the prediction-market backfill use.

**Pulls are incremental:**

- FRED asks from its newest stored day less a revision window by frequency
  (daily 30 days, weekly 120, monthly and quarterly 400), or for the full
  history when nothing is stored, and merges into the CSV copy.
- `_publication.since()` gives other writers the same window.
- `feeds.freshness` reads the whole roster in one grouped query.

The gates are `tools/validate_backups.py`, `validate_audit_1.py` group E,
`validate_secrets.py` group I and the data gate `validate_backup_crypt.py` (real
rclone, the local backend).

**chester-meme's packets come in as Book D drafts, never decisions
(meme-ingest-ledgers-1, 17 Oct 2026).** `altdata/meme_ingest.py` runs at 21:45
(`chester-meme-ingest.timer`, enabled by hand) and at the end of the 06:45 pass.
It reads `$CHESTER_MEME_DROP` (else the meme checkout's drop directory in the
same user's home) and never writes into it:

- the manifest first: its schema must be the copy in `docs/interface/`, the same
  version and SHA-256, or nothing is read;
- a restricted packet, or a Brookfield-blocklisted name (by root or by name,
  aliases included), is refused and logged, never stored;
- a packet the schema rejects is logged and skipped, never repaired;
- the rest become one row each in the register database's `meme_drafts`, keyed
  by `packet_id`; a second sighting writes nothing.

A trigger refuses a restricted instrument there too, the packet columns are
immutable, and the decision tables are never written. The close and the anchor
print one line, "meme drafts awaiting review: n (refused: m)". The operator
confirms with `decide.py record --meme-packet <id>` and rejects with `decide.py
meme-reject <id>`; both are on the deny list. `tools/validate_meme_ingest.py`
holds it.

**The calibration ledgers are studies, not rights (Batch 6 Tranche 2 part 1 and
Batch 5 Tranche 2, 17 Oct 2026).** `altdata/ledgers/` holds ST-R5.30b, 32b, 35b,
36b and 43b, and ST-R4.17b and 19b; `python -m
altdata.ledgers run <item|all> --source public|store` writes
`docs/ledgers/<item>-ledger-<date>.md` and its episodes CSV, dated and never
edited. Each prints its as-of, window, n, statistic, the pass rule as the order
states it and that rule's verdict. Neither order states a pass rule for any of
the seven, so each says so and none is invented. The pass rule is pre-registered
(ruled 17 Oct 2026): the order's, else the first edition's, and every edition
says so at its head; `write_ledger` refuses a re-run that changes it. Each states its rights consequence
and grants nothing; the package never opens the register. A ledger without its
as-of, window or n is refused. `tools/validate_ledgers_b6.py` holds it.

**A bad print is checked before it is read (AUD-3c, 15 Oct 2026).**
`python -m altdata.quality check [--date D] [--db PATH]` opens the store
read-only after each pull and lists three things: an outlier (a price's or a FRED
series' new print past 6 standard deviations of its last 60 changes, measured by
its own delta rule and the move screen's pinned basis), a revision (a FRED value
restated for the same observation date: listed, never flagged), and a
cross-source gap (^TNX/DGS10, ^TYX/DGS30, ^VIX/VIXCLS past the pair's measured
tolerance). The close prints the day's flags in its Warnings table, at most five
and a count, nothing on a clean day; a flag never blocks a report or changes a
value. The numbers live in `config/data_quality.yaml`, each with its reason.

**A bad print is marked, a source is registered, and the tier decides a tie
(audit-leftovers-2, 17 Oct 2026; the 14 Oct audit's items 12, 14 and 15).**

- `python -m altdata.quality record` runs after the EOD pass's price pull and the
  06:45 FRED pull, over the closes and every FRED block. Each flag becomes a row
  in `data_quality_flags`, a table of its own that refuses UPDATE and DELETE, and
  is listed in the run log. The freshness check and the heartbeat print the
  day's count, "n outliers" (`quality=<n>`). A flagged value is marked, never
  corrected: nothing is altered, dropped or withheld. The sigma and the window
  are listed per family under `outliers.families`.
- A store opened through `open_writer()` refuses a write whose source is not a
  registered id or `<id>:<variant>` (`observations.UnregisteredSource`). The
  history is never rewritten; old strings read through `source_ids.canonical()`'s
  declared aliases.
- When two sources hold one period at the same newest instant, the as-of join,
  `latest_as_of()` and the row cache keep the higher tier (A0, A1, B, C, D, E,
  derived, then a string on no list) and say which they chose (`tier`,
  `tier_over`; `python -m altdata.observations as-of KEY`). A newer vintage still
  wins over an older one.
- The yfinance basket and the crypto basket resolve their store keys through the
  Security Master (`yfinance_source.resolve_basket()`, `instrument()`); the
  module's maps are its seed.

`tools/validate_outliers.py` holds the marks, the source refusal and the tier
rule; `tools/validate_security_master.py` group M holds the basket.

**The volume profile is data, never a claim (VP-1, 14 Oct 2026).**
`altdata/volume_profile.py` is the one module that bins volume by price, and every
reader calls it: the level list (POC, VAH and VAL of six windows for spy, qqq and
iwm, appended after the older types; statuses on the prior windows only), the
close's, the Weekly's and the Monthly's value-area tables (migration and close
against value by declared rule), C1's shaded prior-session value area, W7's
volume-at-price panel, the Book B candidate line's clause (approximated from daily
bars; the score never reads it), and the stored `calc.vp_<id>_session_*` and
`_20s_*` series that `python -m altdata.volume_profile compute` writes after the
derived features in the EOD pass. A window that is incomplete or mixes sources is
absent with its reason; every read is as of. The settings are
`config/volume_profile.yaml`, all session-set. What the profile predicts is H-006
to H-008 in the Alpha Lab, so no report says a level will hold or a node will be
crossed. `tools/validate_volume_profile.py` holds it on fixtures; the definition
is `docs/volume-profile.md`.

**The scheduled roster is 31 official writers, 27 external writers and 7
loggers** (`feeds.OFFICIAL_WRITERS`, `feeds.EXTERNAL_WRITERS`,
`altdata.loggers.load_all()`), beside the prices, FRED, bars, prediction-market
and fed-funds feeds.

**Feed freshness has two words, STALE and PENDING, and they are `altdata/feeds.py`'s
(T2.6).** Stale: due and not current, or never written by a writer that failed.
Pending: not yet due -- never tried, or tried by a writer that ran cleanly while
the source has published nothing, until one staleness allowance has passed since
the first attempt. The 08:30 heartbeat uses those words and no others, and names
each stale series with its reason in the verdict line.

**A writer obeys robots.txt with its wildcards.** `urllib.robotparser` ignores `*`
inside a path, which is how AAII's `Disallow: /files/*` was read as "no rule" on
4 Oct; aaii.com also answers any client that names itself with a 403. The AAII
writer (`altdata/sources/aaii.py`) therefore reads its inbox on the box,
~/chester-data/inbox/aaii, and fetches only while robots.txt allows it; it
never passes for a browser. The inbox holds the history (the operator's
browser-downloaded `sentiment.csv` or `.xls`, told apart by content, loaded once
with `--history`) and, from 10 Oct 2026, `aaii-weekly.csv`: one row a week from
the chat-side "AAII weekly read" task via Drive, pulled by the nightly rclone
sweep and unioned with the history by date. The manual weekly drop is
discontinued.

**Import yfinance through `altdata.import_yfinance()`, never bare.** yfinance's own
`__init__` puts a `default` warnings rule for its modules at the front of the
filter list, overriding ours, so the helper re-asserts the filter after the import.
Gate L in `tools/validate_weekly_complete.py` refuses a bare import and proves the
silence in a fresh interpreter.

**Instrument identity is the Security Master's (AUD-3b, 15 Oct 2026).**
`config/security_master.yaml` is the source of truth, reviewed by the operator and
served by `altdata/security_master.py`: a stable `SM` + five-digit id that is never
reused, the asset class, currency, multiplier, exchange, identifiers by scheme
(yahoo, store_key, ticker, occ_root, ibkr_conid, pm_id, crypto_id, overnight_slug),
aliases, and an active window. An identifier names an instrument only inside its
window, so a reused ticker (BAM before 9 Dec 2022, SPCX before 12 Jun 2026)
resolves to the right issuer on each date; `resolve()` returns one or raises. A
fact not in the repo or a stored source is null and listed as unverified.
`restricted` is computed at load from `config/tracked_entities.yaml` through
`register/instruments.py`, never read from the YAML. It was seeded once by
`tools/seed_security_master.py`; the call sites keep their own maps until they
move one at a time, and `tools/validate_security_master.py` holds every
identifier in those maps to exactly one entry today. The listings layer
(`altdata/listings.py`, a logger in the 06:45 step) keeps Nasdaq Trader's daily
symbol directories as reference data under data/reference/listings/ with a
change file per day. The export is chester-meme's contract,
`docs/interface/security_master.schema.json` (copied byte for byte, pinned by
SHA-256, kept LF): one security per composite FIGI from OpenFIGI
(`altdata/figi.py`), with the ticker history `altdata/ticker_history.py` rebuilds
each morning (unknown starts 1900-01-01, from_known false). The 06:45 job maps and
exports after the listings step; `altdata/sm_export.py` validates the file before
it writes it. Nothing here reads it back. A listing in Nasdaq Trader's files trades
on a US exchange in USD (ruled 15 Oct 2026); `config/listing_exchanges.yaml` maps
its exchange codes to MICs and to the contract's venues.

### Layer X — the Alpha Lab (`alpha/`)

**`alpha/` is a machine's book in ledger-paper beside the reports and the four
books** (change order `docs/change-order-alpha-lab-2026-10-12.md`, ruled 12 Oct
2026; Tranche 2's amendments of 14 Oct in its section 10; `docs/alpha-lab.md`).
It writes `alpha.db` and, through `alpha/files.py` and nowhere else, its own
files: the weekly agenda (`alpha/research/agenda.md` and `.json`, gitignored), the
workbench's verdicts (alpha/research/reports/, written at run time) and the
outbox (~/chester-data/outbox/lab/ on the box), both `alpha/files.py`'s. Four rules hold it, and a gate holds each:

- **The observation store is opened read-only.** `alpha/store.py` opens
  `file:...?mode=ro` through the point-in-time reader and refuses `write()`.
  `tools/validate_alpha.py` proves the store file's hash is unchanged after a
  full nightly run on its fixture. The lab never writes the register, the
  probability ledger, the narrative ledger or a report. Three reports read it,
  read-only, each through one hook: the Weekly's line
  (`daily_cascade/weekly_stack.py`), the Daily close's line
  (`daily_cascade/stack_close.py`), and the Monthly's Lab report attachment
  (`monthly_macro/run.py`, `alpha/report.py`).
- **No order, gate, broker or network import, and no fetch.**
  `tools/validate_alpha_no_orders.py` covers:
  - the order gate and the whole `register` package;
  - the IBKR modules;
  - the ledgers and the report writers;
  - every network library and the repo's fetchers;
  - `subprocess`.

  It checks the source by AST and checks a fresh interpreter's `sys.modules`.
  The blocklist is the system's own: `register/instruments.py`, loaded from its
  file by `alpha/blocklist.py`. `alpha.db`'s triggers refuse a restricted
  instrument again.
- **The constitution is unchanged without a quoted ruling.**
  `config/alpha_constitution.yaml` is read by every loop and written by none.
  Its sha256 is recorded in `docs/alpha-lab.md` beside the ruling, and
  `tools/validate_alpha.py` fails on an unrecorded change. A session edits it
  only on a paste that quotes the ruling, and adds a hash row when it does.
  Session-set values (shrinkage, correlation threshold, heat cap) live in
  `config/alpha.yaml`.
- **The two-session rule is unchanged.** The lab is built by session A or B as
  the queue allows, never a third. Its loops run on their own timers
  (`chester-alpha-nightly`, `chester-alpha-weekly`, `chester-alpha-proposer`),
  never inside a report's run. Enabling them is the operator's.

**Every idea is pre-registered before it is tested (Tranche 2).** The register
is `alpha.db`'s `hypotheses` table (`alpha/hypotheses.py`), on the batch schema
alpha-lab-hypotheses v1. The first batch is the pinned fixture
`tests/fixtures/alpha/inbox/hypotheses-2026-10-14.yaml`. Every channel enters
through `alpha/intake.py`:

- the Drive inbox (`alpha/inbox.py`, pre-registered at the file's Drive creation
  time from the sweep's `rclone lsjson --metadata` manifest);
- the daily proposer (`alpha_proposer/`, a package OUTSIDE `alpha/` because it
  makes the one model call; `tools/validate_alpha_proposer.py`);
- the workbench (`python -m alpha.research new | run | report`);
- the research sitting (`docs/briefs/alpha-research-sitting-template.md`).

The harness refuses a hypothesis registered after its run. Failures are kept,
and duplicates of them screened out. A rule in the grammar
(`docs/alpha-lab-rules.md`, interpreted by `alpha/rules.py`) runs the night it
is registered and is promoted on the loop's authority if it passes. A model's
idea must also pass the model-idea rule (`alpha/promote.py`).

**A manifest is written before the register (Tranche 3 part 1, alpha-lab-3, 17 Oct
2026).** Outside Drive and the proposer, whose manifests are their own,
`alpha/manifest.py` writes the batch, its sha256 and its instant under the
research directory first, and the register takes that instant; the harness
refuses a hypothesis whose batch carries no manifest, one dated after the run,
or one edited since. Three things now register this way:
- **The tells (X-3.6).** `python -m alpha.tells import` reads the Weekly's tells
  (`config/book_b_scanner.yaml`), the Doctrine's section 5.3 trust matrix (its
  entries only, ruled 18 Oct 2026), the setups in `config/setups.yaml` and the probability ledger's graded
  sources (by SQL over the read-only store). It registers each as "predicts at h
  sessions after costs?", needs_code, with its mechanism quoted from the cited
  section. Every quote is checked word for word (`config/alpha_tells.yaml`). An
  unchanged tell writes nothing; a changed one supersedes its old registration.
- **The event base rates (X-3.1).** `python -m alpha.event_rates compute` writes
  the system's own CPI, payroll, FOMC and earnings base rates, each row with its n
  and window, to alpha.db's `event_base_rates` (`config/alpha_events.yaml`).
  Macro surprises are the naive ones; the dealer regime is read from 6b's keys by
  name and prints "awaiting" where absent.
- **The X-3 engines.** Engine 4 is `alpha/engines/events.py`; engine 5 is
  `alpha/engines/carry.py`, crypto carry. Engine 5 runs nothing until S-3 holds
  its 92-week window, uses venue fees as dated constants
  (`config/alpha_crypto_venues.yaml`) and books the paper book's two-leg crypto
  rows in `carry_book`. Their roster, `alpha/research/roster-2026-10-17-x3.yaml`,
  is registered on the box by `python -m alpha.manifest register`.

The lab line and the Lab report gain the tells' counts and these rows.
`tools/validate_alpha_lab_3.py` holds all of it.

**The quarterly meta-loop (X-3.7; lenses-group-b, 18 Oct 2026).**
`alpha/loops/quarterly.py` reviews a closed quarter the lab ran through whole.
The weekly loop asks for the review inside 21 days of the quarter's end; there
is no new timer. For each of the loop's own changes it computes what the lab
would have earned without the change, from the same stored prices:
- an accepted re-fit, re-run at the old parameters;
- a rebalance, the engines' recorded returns at the old weights.

The governor's moves are the constitution's, listed and not counted. When the
net contribution is negative, ONE `meta_tighten` loop event narrows each
re-fitted engine's ranges toward its current parameters and slows the re-fit
cadence (`config/alpha.yaml` `meta_loop:`) for the next quarter only. The weekly
loop obeys it through `refit_due()` and `effective_ranges()`. A positive quarter
changes nothing. The Quarterly mails the lab's page
(`alpha/report.py` `quarter_page`, through `quarterly_attachment` in
`monthly_macro/run.py`), which prints "no quarter closed yet" until a whole
quarter exists.

**Engine 6, extremes reversion (X-3.3; alpha-lab-4, 19 Oct 2026).**
`alpha/engines/reversion.py` fades a 2.5-sigma print only where that bucket's
own point-in-time history reverses.
- A bucket is a series and the sign of its print.
- A print is identified against its own trailing window as known on its day,
  never against the move screen's in-sample "false flag k/N".
- Below 30 completed formation prints a bucket prints "awaiting (n=k of 30)"
  and trades nothing.
- At 30, the horizon (1, 5, 10 or 20 sessions) with the highest reversal share
  in the formation sample is frozen, and only later prints are traded.

Every rule is `config/alpha_reversion.yaml`'s `spec`. Its sha256 is quoted by
the roster's E-6 (`alpha/research/roster-2026-10-19-x3-3.yaml`), and the engine
refuses a spec that no longer hashes to it. `tools/validate_alpha_lab_4.py`
group A holds it.

**The grammar search (X-3.5; alpha-lab-4, 19 Oct 2026).** `alpha/search.py`
enumerates `config/alpha_search.yaml`'s family: signal families x
conditioning options x horizons x instruments x exits, 3,840 candidates, each
a grammar rule. The conditioning variables are the macro dial, the volatility
dial, the CFTC net's z and calc.funding_agg. A variable joins a run only if its
point-in-time history (the first day a value was knowable) starts at least five
years before the holdout's first day (ruling 5(a) of 19 Oct 2026); one that
fails is pending with "history from <date>" and its options are not
candidates. The dealer regime is pending on its captures' history and is not
in search-v1. A run goes in this order:
1. coverage, then its manifest (the family's sha256, each variable's first date
   and verdict, the count, the split, the deflation and the survivor rule)
   before the first backtest;
2. the family's variant count raised by every candidate;
3. formation against the constitution's deflated gate;
4. the survivor list frozen, and only then the holdout backtested;
5. the survivors of both registered as `systematic` hypotheses of the
   `search` channel, at the manifest's instant.

A step is capped at 400 candidates and resumes from its progress file. A
resumed run refuses a changed family. While a run is unfinished, its next step
is the nightly loop's last (ruling 5(c)): its wall clock is the unit's 20
minutes less 3 spare less what the unit has spent, at most 600 s, and under
120 s it skips and says why. A new run begins only in a month's first week,
once the previous run is complete; one lock (`files.lock`) covers every step.
No new timer; the Monthly's Lab report prints its line, naming the variables
that passed and failed coverage. `tools/validate_alpha_lab_4.py` groups B and C
hold it.

Coded engines are named in `config/alpha_engines.yaml` (trend_ts, trend_xs,
pm_futures, vrp_dealer, events_macro, events_fomc, events_pead, events_crush,
crypto_carry, reversion, all candidates until they pass); a promoted grammar
rule is named by its register id in `alpha.db`. No gate reads the live store.

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

## What runs without asking

`.claude/settings.json` holds a narrow permission allowlist so a deploy can run
unattended. `tools/validate_deploy.py` enforces both halves of it — that the
deploy cannot take a running unit down, and that the allow list has not quietly
grown.

**Deny takes precedence over allow.** That is Claude Code's own rule rather than
something this repo arranges, and it is why the deny list can be written broadly
without reasoning about overlaps: `Bash(make deploy*)` is allowed and *anything*
containing `systemctl --user restart` is denied, so a deploy that grew a restart
would be refused rather than inherited from the allow.

**Every `make` entry is paired with the form that runs without `make`.** The
allowlist was first written as three `make` entries, and `make` is absent on this
repo's authoring laptop — so those entries matched commands that cannot run there
and granted nothing: every gate run and every deploy went back to a prompt. The
mirrors are `bash scripts/make.sh validate`, `bash scripts/make.sh html` and
`bash scripts/deploy.sh`. They are the same fixed bodies reached by a different
spelling rather than a wider grant, which is what makes the pairing acceptable:
each names a script in this repo that `validate_deploy.py` audits, and group G of
that validator fails if a `make` entry and its mirror ever come apart.

### Allowed, and why each is safe

| Allowed | Why its worst case is known |
|---|---|
| `make validate`, `bash scripts/make.sh validate` | Reads. Every gate is read-only over the repo and the store. |
| `make html`, `bash scripts/make.sh html` | Regenerates `docs/html/` from the papers' `.md`. Build output; recoverable by re-running. |
| `make deploy*`, `bash scripts/deploy.sh*` | Its whole body is fixed in `scripts/deploy.sh` and the box half it ships, `scripts/deploy_remote.sh`, and both are audited by `validate_deploy.py`. The narrowness is the feature: a deploy typed twelve different ways cannot be allowlisted at all. |
| `git add` / `commit` / `push` / `pull` | History is recoverable, and a bad commit is visible and revertable. `push` is included deliberately — a deploy that cannot push is a deploy that stops halfway. |
| `ssh vps systemctl --user is-active` / `list-timers` | Reads unit state. Neither can change it. |
| `ssh vps cat` / `tail` | Reads logs and state files on the box. Made safe by the secrets deny below, not by the verb. |

### Denied, and the reason beside each

Every one of these is denied **explicitly**, and the deny wins over any allow that
would otherwise reach it.

| Denied | The reason |
|---|---|
| `systemctl --user stop`, `disable`, `restart`, `kill`, `mask` — in any composition, local or over ssh | **Asymmetric cost.** The worst case of refusing is a printed command; the worst case of acting is the Gateway down mid-session with a position open. An unattended process should never be able to choose the second. `make deploy` therefore prints the exact `restart` command and **exits 3** so a human runs it — the one case where handing the job back is the correct outcome rather than a limitation. |
| `rm` against `~/state`, `data/`, `chester.db`, `pin_log`, `~/backups`, `~/chester-data`, `~/.chester`; `git clean -fdx` | **These are the irreplaceable files.** `~/state` holds the heartbeats whose age *is* the outage clock; `data/` holds the captured chains and the pin log, which are a market at an instant and cannot be re-fetched; `chester.db` holds the register, the grades and the probability ledger. Losing any of them loses evidence, not configuration. AUD-2 (14 Oct 2026) adds `~/backups` (the EOD zips the restore runbook falls back on), `~/chester-data` (the live CSV store and the inboxes) and `~/.chester` (the wrappers' status and locks), and `git clean -fdx`, which deletes every untracked file in the checkout -- `data/` and `.env` among them -- in one command. |
| `decide.py record`, `decide.py set-status`, `decide_remote.sh` with either, `migrate_register.py import`, `altdata.narratives confirm` / `reject`, `alpha.promote retire`, `alpha.governor resume` | **Register writes stay the operator's.** The register is the record against which the system is graded, and a grader that could also write the decisions it grades is a system marking its own homework. This is the same reason `derived_grade` and `derived_probability` have an empty `allowed_reports`. The narrative register (6c-2) is written by the sessions -- seeds, rule-driven transitions, model proposals -- with ONE human gate, confirming or rejecting a proposal, and that gate is denied here on the same argument. The Alpha Lab's retirement of an engine by ruling (X-2.6) is the operator's for the same reason: the loop retires by the kill rule alone. So is lifting the lab's -15% halt (ruling 6, 14 Oct 2026): `python -m alpha.governor resume --reason` writes the one event that lifts it. |
| `sudo`, in any position — privilege escalation | **Nothing here needs root.** Every unit is a `--user` unit, every path is under `$HOME`, and the one documented `sudo` (`loginctl enable-linger`, `apt install xvfb`) is a one-time install step a human does once. Privilege escalation in an unattended path is a category error before it is a risk: if a deploy appears to need root, the deploy is wrong, not under-permissioned. |
| `placeOrder`, `place_order`, `bracketOrder`, `submit_order`, `order_router`, `ibkr_orders`, `execution_framework`, `reqGlobalCancel`, `--allow-live` | **Named now so Gate 3 is already blocked when it exists.** There is no order path in this repo today — `validate_ibkr_portfolio.py` proves the source contains none, and the architecture puts live-with-approval at Gate 3 behind months of paper dwell. These patterns are pre-emptive on purpose: the moment an order entry point is written it must arrive already denied, rather than relying on somebody remembering to add a rule in the same session they gain the capability. `--allow-live` is included because it is the flag that selects the live port; an unattended process has no business reading the live account, let alone trading it. |
| `cat`/`tail` of `.env`, `config.ini`, `rclone.conf`, anything under `/.ssh/`, any `environ`, and any literal key name (`ANTHROPIC_API_KEY`, `SMTP_PASSWORD`, `FRED_API_KEY`, `CHESTER_STATE_TOKEN`, `MASSIVE_API_KEY`, `FLASHALPHA_API_KEY`, `NASDAQ_DATA_LINK_API_KEY`, `OPENAI_API_KEY`) | **`ssh vps cat *` is allowed, which would otherwise permit reading `.env`.** The standing rule is that a key reaching a transcript is a leaked key that must be rotated, so the deny closes the hole the broad read rule opens. This one was added rather than requested: an allowlist that permits an unattended secret read contradicts the repo's own invariant. |
| `Read` and `Edit` of `**/.env*` (except `.env.example`), `~/ibc/**`, `~/.config/rclone/**`, `~/.ssh/**` and `//proc/*/environ` | **A session reads files through tools the Bash rules never see** (AUD-2, 14 Oct 2026). The Read and Edit file tools, Grep and Glob would each have shown a key while every Bash rule above held. Claude Code consults `Read`/`Edit` path rules (gitignore syntax) and applies a `Read` deny to Grep and Glob; a `Grep(...)` or `Glob(...)` path rule is accepted and never consulted, so none is written. `~/` is the home directory and `//` the filesystem root (one `/` would mean this project's root). `.env.example` is carved back out by a `!` negation listed after its rule in the same deny list -- an allow cannot override a deny. `tools/validate_deploy.py` group J fails on any missing rule. |

### What a deploy does not do

`make deploy` is six steps and nothing else: `git pull --ff-only`, copy
`deploy/systemd/*.service` and `*.timer` into `~/.config/systemd/user/`,
`daemon-reload`, `enable --now` any timer in `DEPLOY_TIMERS`
(`scripts/deploy_remote.sh`) that is not yet enabled, run the drift check and the heartbeat checker, print the timer
roster.

**A push to main deploys code at the next timer; unit files follow at the next
self-deploy; restarts stay the operator's.** Each box wrapper runs
`git pull --ff-only` on main before it starts, so code and config reach the box at
the next timer run after a push, whether or not anybody deploys. Unit files reach
`~/.config/systemd/user/` through the box's **self-deploy** (A-4, 9 Oct 2026):
`chester-deploy.timer` fires every 30 minutes inside the operating windows only,
and when main's `deploy/systemd/` tree differs from the one it last deployed,
`scripts/run_self_deploy.sh` runs the same box half the laptop ships,
`scripts/deploy_remote.sh` (unit copy, `daemon-reload`, enable of `DEPLOY_TIMERS`,
the drift check). It never restarts, stops or disables a unit. A changed unit that
was running is written to `~/state/alerts/restart_pending` as
`restart pending: <unit>` (`scripts/restart_pending.sh`), and the heartbeat's
verdict names it (`restart_pending`, exit 14) until the operator restarts it.
`tools/validate_deploy.py` group I holds all of that. `scripts/deploy.sh` from the
laptop still does the same six steps on demand, and it is how the self-deploy's
own timer is first enabled. Hence the rule under "Operating windows": a merge to
main is a box write and happens only inside the windows.

**All six box-side steps run over ONE ssh connection.** `scripts/deploy.sh`
ships `scripts/deploy_remote.sh` to the box as `ssh -o BatchMode=yes vps 'bash -s'
< deploy_remote.sh`, streams its sections back, and decides the exit code from
three marker lines the box half prints last (`@@NEEDS`, `@@DRIFT`, `@@HB`). Until
28 Sep 2026 the deploy opened a session per step and two per timer, about fifteen
connections a minute, and that deploy timed out on port 22 after step 3 while the
box was up. ssh ControlMaster is not available from the Windows laptop, so one
session is the design rather than a multiplexed many. The restart command is
still printed on the laptop and never run, and `validate_deploy.py` group H runs
`deploy.sh` against a fake ssh to hold the exit codes, and `deploy_remote.sh`
end to end from stdin against a scratch clone.

`DEPLOY_TIMERS` is a declared list and not a glob over the unit directory,
because `ibgateway.service` and `ibgateway-restart.timer` are deliberately held
back behind one witnessed clean start (`deploy/systemd/README.md` section 4) and a
glob would enable them the first time anybody deployed.

Exit codes: `0` clean, `3` a changed unit is running and needs the printed
restart, `4` drift still reported after the copy so the deploy did not take, `1`
the pull or copy failed, or the connection did.

## Operating windows (Eastern time)

- **Deploys and box writes:** weekdays 09:05–15:40 and 17:20–23:30 ET, and never
  16:00–17:20, when the EOD pass and the 16:45 close are running. Weekends are
  open, but stay clear of Sunday 05:00, when the Weekly runs.
- **A merge to main is a box write.** Every box wrapper (`run_eod_cron.sh`,
  `run_daily_close.sh`, `fetch_overnight.sh`, `sync_ibkr.sh`, the anchors, the
  Weekly and the Monthly) runs `git pull --ff-only` on main before it starts, so
  a push to main reaches the box at the next timer run -- not at the next deploy.
  A changed unit file follows at the next self-deploy tick (`chester-deploy.timer`,
  every 30 minutes inside these windows). Merges to main therefore happen only
  inside the windows above, the same as deploys; `scripts/deploy.sh` is for unit
  files, timers and the checks only.
- **Check the clock in ET, not UTC.** Git Bash's `TZ=` prints UTC on the laptop,
  so read the time in ET through Python's `zoneinfo`.
- **A session never runs unit commands, `sudo` or register writes.** It prints
  them for the operator to run, as described under "What runs without asking".

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

**Unit mismatch in net liquidity — and the unit this file itself had wrong.**
(Resolved 24 September 2026; kept here because the trap is generic and the next
series to hit it will not be net liquidity.)
`WALCL` (`fed_balance`), **`WTREGEN` (`tga`) and `WRESBAL` (`bank_reserves`)
are all in millions**; only `RRPONTSYD` (`rrp`) is in billions. `WRESBAL` was
declared `"B"` in `config.py` until 5 October 2026, when the Weekly's first
Plumbing render printed bank reserves as **$2,948tn** -- the same trap a second
time, caught only because a figure that absurd was put in front of a reader. This paragraph said TGA was billions, and so
did `altdata/config.py`'s units field, and so did
`monthly_macro/compute.py:fed_net_liquidity` — which therefore returned
**−823.6 trillion** on every run it ever made, and the Monthly printed it as a
liquidity level. TGA at 830,296 is $830bn read as millions and $830 *trillion*
read as billions, which is why the sign flipped and nobody noticed: a figure that
absurd reads as a bug in the report rather than in the number.

The metric now lives at `calc.net_liquidity` in `altdata/market_features.py`, in
**dollars**, normalised leg by leg — `fed_balance × 1e6`, `rrp × 1e9`,
`tga × 1e6` — and it reads **$5.87tn** as of 27 May 2026.
`tools/validate_regime.py` group I asserts both that the result is inside
`NET_LIQUIDITY_BAND` and that the un-normalised subtraction falls outside it, so
the guard is shown to fire rather than assumed to. `monthly_macro/compute.py` is
deleted; the liquidity dimension reads this series as its **primary**.

Re-check the unit of every new series against FRED's own page, not against a
neighbouring line in `config.py`: that is how this one was copied. And note what
made it survivable — one report's private arithmetic, checkable against nothing.
A figure in the registry has a percentile, a band and a gate; a figure inside a
renderer has a reader's credulity.

**FRED history comes from ALFRED, at its first publication (AUD-3d, 15 Oct
2026).** The live pull stamps each row with the instant it was written, so a deep
FRED pull would be invisible to every as-of query before today.
`python -m altdata.fred_history backfill` writes each value with
`availability_kind` observed at its vintage's first publication: the release
time where the release calendar holds it, otherwise the end of that day ET. A
revised value gets its own row from its own vintage, under source `fred:backfill`
and its own run. A revisable series without vintages gets nothing, and only a
`never`/`split_only` series may reconstruct. `tools/validate_fred_history.py`
holds it against a fake ALFRED.

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
