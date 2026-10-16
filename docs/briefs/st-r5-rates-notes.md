# ST-R5 rates transmission — Batch 6 items 34, 36, 37 and 41 (Tranche 1): session notes

**Builds on the stitched chain, and merges after it.** Branch `st-r5-rates` from
the tip of `aud-3b-security-master` (`2fb1048`, the stitching notes for the week
of 19 Oct), the last branch of the chain stitched this week. It needs that chain
on main first. It must not be merged ahead of the chain.

Spec: the filed change order
`docs/change-order-signal-triage-batch-6-2026-10-15.md`. It sits on branch
`docs-batch-6` (`origin/docs-batch-6`) until Friday. The parts read were:

- items 34, 36, 37 and 41;
- section 4, cross-item ruling 1;
- section 8, verify items 3, 4 and 5;
- section 11, filing notes 3 and 7.

Also read: the 25 Sep integrated order's integration rules (R28, Track D's D1c,
calibration offline), and CLAUDE.md.

Session A, 16 Oct 2026. Branch only: pushed, not merged, not deployed, nothing on
the box.

## Needs you

1. **D1c is not complete, so two new writers are held.**
   - **Landed:** WAL and `busy_timeout`, on 6 Sep (`f98fec4`, both stores).
   - **Not landed:** the repo-wide write lock. `TODO.md`'s D1c line is still
     open, and there is no shared lock helper in the repo.
   - **Held:** `altdata/sources/redfin.py` (item 36) and
     `altdata/sources/mba.py` (item 37). Each is built and passes its fixture
     gate, but `HELD_FOR_D1C = True`: `pull()` fetches nothing, writes nothing,
     and returns `HELD` with its reason. Neither is on a feeds roster, and
     `source_registry.yaml` lists both as `status: held`.
   - **What prints meanwhile:** the housing block and the MBA line print "not
     read — held until D1c's write lock lands". So of the four 1 Nov candidates
     in this cluster, the 34 flag and the 41 quality tail can print on 1 Nov;
     36/37's housing block cannot until the hold is lifted.
   - **Precedent cuts the other way.** AQ-3, AQ-9a and the AAII writer shipped
     on WAL and `busy_timeout` alone. If that is the ruling — that the two
     PRAGMAs satisfy D1c for an append-only writer in the 16:10 pull — lifting
     each hold is two edits: `HELD_FOR_D1C = False`, and the module name added to
     `EXTERNAL_WRITERS` in `altdata/feeds.py`. Gate B already proves both writers
     write correctly once the hold is off. Otherwise D1c's lock comes first.
   - **Not held:** everything else on this branch extends a writer that already
     exists: the Bundesbank and CFETS 2-years, the fed funds contract count, two
     FRED series.
2. **Where item 34's flag goes.** The order puts it "in `rates.driver`". That
   sub-state was withdrawn from the market-state object on 30 Sep after failing
   its calibration gate twice. `config/market_state.yaml` is at v1.10, and
   `tools/validate_regime.py` group L fails on any `driver` node and on the
   string `fed_path` anywhere in tracked Python.
   - **Built:** as SR-49's shape axis was. The flag is computed in
     `altdata/st_r5_rates.py`, report-only, beside `altdata/rates_attribution.py`.
     `regime.py` imports nothing from it, and gate H checks both directions.
   - **Rights:** unchanged ("flag only"). R28 is met by not being a state at all.
   - **Your options:** (a) leave it report-only; (b) rule a fresh
     pre-registration as a declared sub-state at v1.13 / method-11, the next free
     numbers (v1.11, v1.12 and method-9/10 are retired); or (c) rule a home other
     than the rates dimension.
3. **Item 41's co-signal points at an overlay that does not exist.** HY Spread
   Acceleration is a Top & Bottom overlay. T&B is not built in this repo
   (`altdata/move_screen.py`; `quarterly_chapters.yaml`: "the Top & Bottom
   overlay is not on this build").
   - **Built:** the co-signal is computed and printed. Its line says it is
     "recorded as a co-signal to HY Spread Acceleration, which is not built on
     this report, so it is attached to nothing".
   - **Where it lives:** `config/st_r5_rates.yaml` `quality_tail.overlay_built:
     false`. When T&B arrives, ST-11's wiring session attaches it and flips that
     key; no new overlay is made.
   - **Your call:** whether, until then, it should also enter the T&B intake
     queue as a recorded candidate.
4. **Korea needs a Bank of Korea ECOS key** in the box's `.env`. The key is free
   and it is yours to get. Even with it, Korea is a new writer, held by D1c as in
   item 1. Until both are done, Korea is a listed gap.
5. **The thresholds are session-set.** The order rules directions, not sizes.
   Each is in `config/st_r5_rates.yaml` with its reason:
   - the flag fires at the 10-year ≥ +10 bp with 12-month pricing ≤ −10 bp, over
     28 days;
   - NFCI confirms above 0 change;
   - the quality tail fires when CCC widens and its 28-day widening exceeds BB's
     by ≥ 25 bp.
   Overrule any of them in the YAML. Gates C and G move with it.
6. **By-hand lines** have keys now (`tools/manual_input.py`, run on the box):
   - `manual.mba_purchase_index`: the level, member-only;
   - `manual.nar_phsi`: NAR's index, no free series;
   - `manual.euro_ccc_oas`: in bp, when reported.
   Until you enter them, each prints "by hand, not entered".
7. **Merge order:**
   - after the stitched chain;
   - after Batch 5;
   - after `docs-batch-6`, which files this order;
   - beside `6e-metric-lenses`; see "Files shared with open branches" below.

## Gates run

**Locally, one at a time, only the gates this branch writes or changes:**

| Gate | Result |
|---|---|
| `validate_st_r5_rates` (new) | 68/0 |
| `validate_audit_3a` (count literal and one declaration changed) | 83/0 |
| `check_registry` | OK (819 metrics, 90 sources) |

Every other gate, and anything that renders a PDF, is left to CI. CI's numbers
are in the session's closing report; `gh run list --branch st-r5-rates
--limit 3` reads them.

**What the new gate covers** (`tools/validate_st_r5_rates.py`, fixtures in
`tests/fixtures/st_r5_rates.json`, synthetic figures in the publishers' shapes;
no live store, no fetch, no model):

| Group | What it checks |
|---|---|
| A | Each extended writer reads its new series and refuses another's. One Bundesbank series failing does not stop the other. |
| B | The held writers: they parse by column and by phrase, refuse a changed template, and stop on a robots disallow. Held, they fetch and write nothing. Unheld, in a temporary store, they write. |
| C | The flag fires at threshold and not below. NFCI confirms or does not. The 12-month fallback is named. Absences carry their reasons. |
| D | The panel: eight rows in the order's order, with four gaps and their reasons. |
| E | The housing block: change on the year, metro breadth k of n, "NA" read as absent rather than zero, NAR by hand. |
| F | The MBA line: percentile with its window and n, the floor, Wednesday-only in the close. |
| G | The quality tail: 25 bp fires and 24.9 does not; a narrowing CCC does not; real windows and n; the overlay named as not built. |
| H | The display in all three reports. No week phrase at "monthly". The filler, coincidence, readability and numeral audits. Regime separation. |
| I | The registry and the catalogue. |

## What was built, item by item

### ST-R5.34a — "the market does the tightening" (`altdata/st_r5_rates.py` `tightening`, `policy_12m`)

- **The 10-year:** `fred.yield_10y`, latest close against the close on or
  before 28 days earlier.
- **12-month policy pricing, US:** 100 less the fed funds future twelve months
  ahead of each close's month (`fedfunds.futures_price`, instrument `YYYY-MM`).
  It is a constant horizon, so the contract rolls as the month turns.
  - **Why the writer changed:** `CONTRACT_MONTHS` was 10, and the 12-month
    contract was never stored. It is now 14. Probed 16 Oct: yfinance serves
    ZQX26 through ZQX27.
  - **Until four weeks of 12-month contracts are stored:** the read uses the
    longest horizon (6–12 months) stored at both ends, and the line names it
    ("11-month (the 12-month contract is not yet held)").
- **NFCI:** `fred.nfci`, already pulled. Its 28-day change confirms when it is
  above 0. The flag prints whether NFCI confirms or not.
- **Fixtures:** gate C.

### ST-R5.34b — the G8 2-year panel (`panel`)

| Country | Source | Status |
|---|---|---|
| Australia | — | **gap**: the RBA's F2 table is free and daily, but would be a new writer (D1c) |
| Euro area | `bbk.bund_2y`, Bundesbank Svensson 2.0-year (`R02XX`), daily from 1997; checked live 16 Oct | read; Germany as the euro-area proxy, labelled so |
| Korea | — | **gap**: Bank of Korea ECOS needs a free key in `.env` (yours), and a new writer (D1c) |
| Canada | — | **gap**: the Bank of Canada Valet API is free and daily, but would be a new writer (D1c) |
| US | `fred.yield_2y` (DGS2) | read |
| Japan | `mof.jgb_2y` (already stored; nothing read it before) | read |
| UK | — | **gap**: the BoE database disallows robots (`altdata/config.py`) |
| China | `cfets.cgb_2y`, the CFETS curve's 2.0 point; checked live 16 Oct | read; forward-only, "28 days not yet held" for its first four weeks |

The panel prints as the sub-section's table: the 2-year, its 28-day change, the
10-year's, and the read. A gap row prints "gap" and its reason, never a figure.
Filing note 7 is confirmed: the panel took more sources than two hours, and
three of the gaps are D1c's.

### ST-R5.36a — the housing block (`housing`; writer `altdata/sources/redfin.py`, HELD)

- **What prints:**
  - national pending sales and their change on the year;
  - active listings and months of supply;
  - metro breadth: k of n top-50 metros with pending sales below the same month
    a year earlier, computed at read from per-metro rows;
  - the 30-year mortgage rate (`fred.mortgage_30y`) and its 28-day change;
  - NAR's PHSI, by hand.
- **Monthly.** It prints in the Weekly and the Monthly, carrying its month.
- **The September 2026 file matches the order's read exactly:**
  - pending sales 316,652;
  - all 50 top metros below a year earlier;
  - months of supply 4.1.
- **Fixtures:** gates B and E.
- **ST-R5.36b** (the months-of-supply flag and its ledger) is Tranche 2 and not
  built; see "Not named in the order" item 4 before it is.

### ST-R5.37a — the MBA weekly line (`mba`; writer `altdata/sources/mba.py`, HELD)

- **From the release headline:**
  - the SA purchase index's change on the prior survey;
  - the NSA index's change on the year, its percentile with its real window and
    n.
- **Level:** by hand, against the 2023 floor (~127, the order's reading of the
  chart).
- **Where it prints:** in the Weekly, the Monthly, and the close on the release
  Wednesday only. The close's rule is the session is a Wednesday and the stored
  survey ended within the seven days before it. **A holiday week whose release
  moves to Thursday will miss the close;** the Weekly still carries it.
- **No headline read:** the line prints the hold's reason and the by-hand level
  (the paste's fallback).
- **Fixtures:** gates B and F.

### ST-R5.41a — the quality tail (`quality_tail`)

- **The spreads:**
  - CCC less BB (`fred.ccc_oas`, `fred.bb_oas`, both already pulled);
  - CCC less AAA (`fred.aaa_oas`, **new**: BAMLC0A1CAAA);
  - euro HY OAS (`fred.euro_hy_oas`, **new**: BAMLHE00EHYIOAS) as the daily
    European proxy, beside US HY OAS. That pair is the US-against-Europe line.
- **Both new series:** "Percent, Not Seasonally Adjusted", daily close, read off
  their FRED pages on 16 Oct. FRED serves each from 16 Oct 2023 only, which
  confirms filing note 3.
  - **How the percentiles print:** a series shorter than five years prints one
    percentile, "of its stored history since 2023-10-16 (n=…; shorter than 5
    years)". Five years and full history print separately only once the history
    is long enough.
- **The co-signal:** CCC widening, by at least 25 bp more than BB over 28 days.
  It is recorded and printed; no new overlay is made. See needs-you item 3.
- **Euro CCC:** by hand, `manual.euro_ccc_oas`.
- **Fixtures:** gate G.

### The display (`daily_cascade/rates_transmission_block.py`)

- **Weekly:** one "Rates transmission" sub-section in Plumbing & rates
  (`weekly_stack.plumbing_week`), after batch 3's. The panel is its table; the
  lines are the flag, housing, MBA and the quality tail. Its table note names
  the gaps and the windows.
- **Monthly:** the same sub-section, appended after the buckets, the anchors
  and batch 3 (`monthly_macro/stack.py`). It carries no `bucket`, so the
  takeaway checks in `validate_monthly_stack` skip it, as they skip batch 3's.
- **Close (light):** two items in Plumbing & rates, the flag line and the
  quality tail's headline with its co-signal, plus the MBA line on Wednesdays
  (`stack.build`).
- **Wording:** "over 28 days", never "four weeks". The Monthly prints no week
  phrase (`validate_stack_cadence`); the MBA line says "weekly survey".

## Verify items answered

- **3, the MBA headline path.** Answered from the laptop on 16 Oct; the box is
  yours to check (commands below).
  - **robots.txt:** `*` disallows `/Sitefinity`, `/sandbox`, `/search-results`
    and one schedule page. The newsroom is allowed, read with the
    wildcard-aware reader.
  - **Agent:** the site answers `chester-reports/1.0` (200) and refuses
    `python-requests` (403).
  - **The release:** it prints **changes only**, the SA week-on-week and the NSA
    year-on-year, in whole percent. **Never the level.** The level is a by-hand
    line.
  - **History:** the newsroom does not page older releases (`?page=N` returns
    the same list), so the series is forward-only from its first pull.
- **4, euro CCC beyond FRED's euro HY aggregate.**
  - **FRED** serves the euro HY index's OAS and effective yield.
  - **No euro rating-bucket series** answered under ICE's id pattern
    (BAMLHE1X–4X).
  - **No other free source was checked**, so euro CCC stays by hand.
- **5, Redfin months of supply.**
  - **The field:** `MONTHS OF SUPPLY` is in the data center's monthly
    `country.csv`, January 2012 onward, 177 months to September 2026.
  - **The files moved:** the current ones are
    `redfin_data_center/housing_market/monthly/{country,top_50_metros}.csv`
    (Last-Modified 12 Oct).
  - **The old path is stale:** `redfin_market_tracker/*.tsv000.gz` stopped at May
    2026 (Last-Modified 2 Jun). The writer reads the new path.
  - **Definition:** months of supply is **Redfin's own** (inventory over the
    month's sales), not NAR's.

## Box commands (yours, inside a window: weekdays 09:05–15:40 or 17:20–23:30 ET, never 16:00–17:20)

Everything below runs only after this branch reaches main. The wrappers pull
main, so no deploy is needed and no unit changes.

```bash
# 1. The Bund 2-year's first pull takes its history from 1997 (one request).
#    Otherwise it arrives with the 16:10 pull.
~/chester-reports/.venv/bin/python -m altdata.sources.bundesbank

# 2. The CGB 2-year arrives with the 06:45 early pull, the 12-month fed funds
#    contracts and FRED's AAA / euro HY with the 16:10 pull. Nothing to run.
#    FRED's first pull of the two new series takes their three years.

# 3. The cluster as the box sees it, and the registry check.
~/chester-reports/.venv/bin/python -m altdata.st_r5_rates show
~/chester-reports/.venv/bin/python -m tools.check_store_registry --db ~/chester-reports/data/chester.db

# 4. Verify item 3 from the box itself: robots.txt, then the newsroom, with
#    the repo's agent.
curl -s -A "chester-reports/1.0" https://www.mba.org/robots.txt | head -20
curl -s -A "chester-reports/1.0" -o /dev/null -w "%{http_code}\n" https://www.mba.org/news-and-research/newsroom
curl -sI https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_data_center/housing_market/monthly/country.csv | head -5

# 5. By-hand lines, when you have the figures (values are yours).
~/chester-reports/.venv/bin/python tools/manual_input.py manual.mba_purchase_index <LEVEL> <WEEK-ENDING YYYY-MM-DD> "<where read>"
~/chester-reports/.venv/bin/python tools/manual_input.py manual.nar_phsi <INDEX> <YYYY-MM-01> "NAR release <date>"
~/chester-reports/.venv/bin/python tools/manual_input.py manual.euro_ccc_oas <BP> <YYYY-MM-DD> "<measure, source>"
```

**If you rule D1c met for these writers** (needs-you item 1):

1. Commit the two edits: `HELD_FOR_D1C = False` in each module, and `"redfin",
   "mba"` added to `EXTERNAL_WRITERS`.
2. Make Redfin's first pull by hand, inside a window:
   `~/chester-reports/.venv/bin/python -m altdata.sources.redfin`.
3. MBA's first pull is on a Wednesday after 07:00 ET.

## Files shared with the open branches

| Branch | Shared files | Nature |
|---|---|---|
| `6e-metric-lenses` (session B) | `CLAUDE.md`, `Makefile`, `metrics_registry.yaml` | Each adds a gate line and moves the gate count. The registry edits are in different blocks: mine are entries before `bulk_imports`, plus lines at the top of `families`, `long_windows` and `series_kinds`. Expect textual conflicts in the count and the Makefile list only. |
| `el-1-packets` | `CLAUDE.md`, `Makefile` | Gate count and list. |
| `el-2-3-rollup` | `CLAUDE.md`, `Makefile`, `monthly_macro/stack.py` | Mine is three lines after batch 3's `monthly_subsections` call in `plumbing_section`. |
| item 45's branch (session B) | none pushed yet | — |

- **After `6e-metric-lenses` merges:** `st_r5_rates.lens()` should move onto 6e's
  `derived.lens_forms`. Mine is local because 6e is unmerged and its module is
  session B's.
- **The FRED count lines:**
  - CLAUDE.md now reads 29 in `FRED_SIGNAL_SERIES` and 131 in
    `FRED_PULL_SERIES`;
  - `validate_audit_3a`'s stale-count literal moved with it;
  - any branch adding FRED series reconciles the same two numbers.

## Not named in the order

1. `altdata/fed_funds.py` `CONTRACT_MONTHS` went from 10 to 14, so the 12-month
   contract exists. Its readers (`implied_path`, `path_as_of`) take whatever
   months are stored and are unaffected.
2. **Bundesbank's `allowed_reports`** gains `daily_cascade`. The 2-year prints
   in the close and the Weekly. Nothing enforces the field; the record is now
   true.
3. **`validate_audit_3a` declares two new block members** (`NEW_BLOCK_MEMBERS`:
   `fred.aaa_oas`, `fred.euro_hy_oas`). Its fb67bf3 check otherwise refuses any
   new key in an existing bulk block. The check's intent stands: a new block key
   must have a declared origin.
4. **Redfin's months of supply is not NAR's.** The order's balanced-market line
   (~6 months) is NAR's existing-home measure. Redfin's September read is 4.1.
   ST-R5.36b's flag (Tranche 2) needs a ruling first: does it use Redfin's
   measure against its own history, or NAR's six-month line with NAR's figure by
   hand?
5. **`mof.jgb_2y` and `fred.nfci` were stored but read by nothing.** They are
   read now. `mof.jgb_2y` gains a `series_kinds` line (`yield`).
6. **Process: a write-mode trap fixed in session.** On Windows,
   `Path.write_text` turns `\n` into `\r\n`. The index stayed LF throughout and
   nothing was committed wrong. The working files were put back to LF before
   the commit.
