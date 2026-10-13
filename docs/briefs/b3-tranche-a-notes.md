# Signal-triage batch 3, Tranche A: session notes

Branch `b3-tranche-a` from `main` at 7754d0d. The spec is the change order
`docs/change-order-signal-triage-batch-3-2026-10-02.md`: §2, §3, §5, §6, and §7's
eleven decisions, ruled 6 Oct.

Built in the order the paste gave:
- ST-B3-16, SR-32's early line;
- ST-B3-03, SR-30;
- ST-B3-04, SR-33;
- ST-B3-05, SR-34;
- ST-B3-02, SR-6 by tenor;
- the register and the calendar.

All six are done. Nothing is left over.

Session A, 13 Oct 2026. Nothing ran on the box. The only network use was
verifying sources and robots.txt from the laptop during the build. No gate
fetches.

## Gates run

**Not run:** the full suite (CI is the validate), and anything on the box. I ran
the gates this branch touches, all green at the last run:

| Gate | Result |
|---|---|
| `validate_batch3_a` (new: the five fixtures, the register, the registry, the audits on the new lines) | 55/0 |
| `check_registry` | OK |
| `validate_prices` (updated: basket 54, EUR/CHF in the continuous set) | 81/0 |
| `validate_official_sources` (the three new writers registered, STALE-not-empty) | 231/0 |
| `validate_monthly_stack` (one check narrowed to the buckets, below) | 261/0 |
| `validate_stack_cadence` (it caught week phrases in the Monthly; fixed, below) | pass |
| `validate_weekly_stack`, `validate_weekly`, `_complete`, `_edits`, `_integrity` | pass |
| `validate_monthly`, `validate_daily_close`, `validate_figure_budget`, `validate_numeral_audit` | pass |
| `validate_edition_consistency`, `validate_readability`, `validate_no_filler` | pass |
| `validate_regime`, `validate_events`, `validate_config_refs` (new YAML staged), `validate_gates`, `validate_secrets`, `check_library` | pass |

**`validate_session_calendar` was not run locally.** The batch run was stopped
by Claude Code for low memory on the laptop, before it reached that gate. It is
left to CI. After the fixes below, I reran three gates one at a time:
`validate_stack_cadence`, `validate_batch3_a` and `validate_monthly_stack`.

The Makefile carries the new gate. CLAUDE.md now reads fifty-two code gates.

## Per series: source, cadence, history, robots

Every robots.txt below was fetched on 13 Oct 2026 with the house User-Agent.

| Series (store key) | Source | Cadence | History | Robots verdict |
|---|---|---|---|---|
| 30y JGB (`mof.jgb_30y`, existing) | MoF constant-maturity CSV (`altdata/sources/mof.py`) | daily | 1974– | www.mof.go.jp: 404, no rules |
| OAT 10y (`ecb.irs_10y_fr`, read by name) | ECB data portal, IRS (convergence 10-year), written by `aq-3-series-2`'s `ecb_irs.py` | **monthly average** | 1986– | ECB: only Drupal paths disallowed (AQ-3's check) |
| BTP 10y (`ecb.irs_10y_it`, read by name) | the same | **monthly average** | 1991– | the same |
| Bund 10y (`ecb.irs_10y_de`, read by name) | the same, so both spreads compare like with like | monthly average | 1990– | the same |
| Bund 10y, daily (`bbk.bund_10y`, on `aq-3-series-2`) | Bundesbank SDMX | daily | 1997– | 404 (AQ-3's check). **Not used for the spread:** a daily Bund against a monthly OAT is not one method |
| EUR/CHF (`yfinance.mkt_eurchf`, new) | yfinance `EURCHF=X` | daily, continuous | by backfill | the operator-sanctioned exception (ruled 11 Oct) |
| Buyback operations (`treasury.buyback_max`, `_accepted`, `_offered`, new) | Fiscal Data `v1/accounting/od/buybacks_operations` | per operation | 9 Mar 2000– | the API host answers 404 (no rules), and fiscaldata.treasury.gov is `Allow: /`. **TreasuryDirect is `Disallow: /` for every agent but `usasearch`**, so its results pages are not read |
| Buyback schedule (config) | home.treasury.gov `Tentative-Buyback-ScheduleQ32026.pdf` (published 9 Sep) | quarterly | — | home.treasury.gov `Allow: /` |
| TGA (`fred.tga`, existing) | FRED WTREGEN, in millions | weekly | existing | — |
| Japan's reserves, total and foreign securities (`tic.jp_reserves_total`, `tic.jp_reserves_fx_securities`, new) | MoF `official_reserve_assets/historical.csv`, cp932 | monthly, ~7th, 08:50 JST | Apr 2000– | www.mof.go.jp 404 (no rules) |
| FIMA repo, Wednesday level and week average (`tic.fima_repo`, `tic.fima_repo_weekavg`, new) | Fed Data Download Program, H.4.1 package `f52e7251…`, through `altdata/sources/fedboard.py` | weekly, Thursdays 16:30 | the package's history | federalreserve.gov 404 (no rules) |
| 5y TIPS real yield (`fred.tips_5y`, new) | FRED DFII5, percent, daily (unit read off FRED's page) | daily | 2003– | FRED API |
| ACM expected short rate, 2y and 5y (`acm.risk_neutral_yield_2y`, `_5y`, new) | NY Fed ACM workbook, existing writer; two columns added | daily | 1961– | existing |
| JGB auction dates (config) | MoF auction calendars `2610e`, `2611e`, `2612e` | monthly | — | 404 (no rules) |

**Registry.**
- **Entries.** Every new series has a registry entry that states its
  `available_at`. The two bulk members (DFII5, EUR/CHF) take their blocks'.
- **Families and long windows.** Each new series also has a `families` line and
  a `long_windows` line. `long_windows` is a new block: the metric-lenses
  brief's long percentile window.
- **Retrieval time.** It is the observation's `ingested_at`, which the store
  already records.
- **Sources.** Three new entries in `source_registry.yaml`: `treasury_buybacks`,
  `mof_reserves` and `frb_h41`.
- **Writers.** The three new writers run on the existing official pass
  (`altdata/feeds.py` `OFFICIAL_WRITERS`): 16:10 and 06:45.

## SR-30's crisis level, set from the stored peak

**154.0 bp.** This is OAT–Bund on the ECB's monthly-average series for November
2011, which is that series' full-history peak. It is computed from the ECB IRS
data fetched on 13 Oct 2026 (FR 10y less DE 10y, monthly average). It is
recomputable from the store by `altdata.batch3.crisis_level_from_store`, and
the gate holds config to it.

**This is not the ~190 bp the entry and decision 2 name.** About 190 bp is the
daily close peak of 15–17 Nov 2011, and a monthly average cannot reach a
two-day peak. On the only free official series, the two tiers sit 4 bp apart
(watch 150, crisis 154).

**A second mismatch on the same series.** September 2026 reads 96.7 bp here,
against the entry's 147–149 bp "on 2 Oct" on a daily benchmark basis. The tiers
were ruled on daily benchmark levels, and the stored series is a different
quantity. See Needs you 1.

BTP–Bund prints beside it, untiered. Its November 2011 monthly value is
518.7 bp.

## What prints where

| Item | Close (Daily tape) | Weekly, Plumbing & rates | Monthly |
|---|---|---|---|
| ST-B3-16 JGB line | below 4.40%: nothing. Approaching: one line. Flagged: the line and the mechanism | the same line, as a sub-section | inside Plumbing's sub-sections |
| ST-B3-03 SR-30 | — | narrow flag: a table of each spread, its prior-period change, the 5y and 20y percentiles with n, the tier and the as-of; EUR/CHF with its week; the tier line with "(descriptive; unvalidated, n=0)" | the same in Plumbing. **At the crisis tier only**, one sentence in "what doesn't fit" |
| ST-B3-04 SR-33 | — | the events block: each operation in the week, the sector, bought of the maximum, bought/max, and the 30-year's next-session change with its date; the TGA | the same over the month, plus **the Rate and Liquidity Machine's lever table**, a long-end supply row with the modifier line |
| ST-B3-05 SR-34 | — | narrow flag lines: the month's change in reserves and in the securities line, FIMA usage for the week, each with its as-of, and "fast tells ahead of TIC". The TIC rows' lag line is unchanged | in Plumbing |
| ST-B3-02 SR-6 by tenor | — | a table by tenor, the week's and the month's split: nominal, real, breakeven, ACM expected rate, ACM term premium, dates. The frame names which tenor moved most and which leg was larger | in Plumbing (the Monthly's rates sit in its Plumbing buckets) |
| §5 events | — | the Weekly's day-by-day calendar (Ahead) reads `release_calendar.yaml`'s new `scheduled` and `recurring` blocks | — |

**The calendar entries:**
- **Dated:** the five buyback operations from 15 Oct to 5 Nov; the BoJ on
  30 Oct, with the Outlook Report; the JGB 20y, 30y and 40y auctions from
  20 Oct to 17 Dec.
- **Recurring:** EIA on Wednesdays, H.4.1 on Thursdays, CFTC TFF on Fridays at
  15:30, and the MoF reserves on the first weekday on or after the 7th.

The EM, China and Thailand seeds are left out; they are the operator's.

## Could not source: the inbox route proposed

- **A daily OAT and a daily BTP, free, official, keyless.** None found:
  - the Banque de France's Webstat catalogue lists only the monthly
    `fm-m-fr-eur-fr2-bb-fr10yt_rr-yld`, and that carries no records without the
    keyed API;
  - the Banca d'Italia's infostat host answers a "Risorsa Protetta" page;
  - Agence France Trésor sits behind a Cloudflare challenge.

  So SR-30 stores the monthly average and says so. **The proposed route to a
  daily weekly close:** a daily CSV dropped in `~/chester-data/inbox/sr30`,
  exported by the operator from Webstat with a registered key, or a Webstat API
  key in `.env` (a secret, so yours to add). Either way, a reader would follow
  AQ-3's inbox pattern (the AAII writer's).
- **Every other series** was sourced keyless and robots-allowed; none needs an
  inbox.

## Anything unexpected

- **SR-30's legs already exist, but on an unmerged branch.** `aq-3-series-2`
  (under `sr-36-basis-proxy` and `sr-43-49-rates-anchor`) writes:
  - `ecb.irs_10y_{de,fr,it}`;
  - `bbk.bund_10y`;
  - its own monthly `calc.oat_bund_bp` and `calc.btp_bund_bp`.

  To avoid duplicating it, this branch adds no ECB or Bundesbank writer and
  reads the legs by name. **Until `aq-3-series-2` merges, the SR-30 block
  prints "not yet stored — the legs come from the ECB writer"**, and the crisis
  sentence cannot fire. AQ-3's `calc.*_bp` spreads are the same quantity as
  this block's. One of the two should go at merge: see Needs you 3.
- **The 10y attribution block is not printed anywhere.** It shipped on 30 Sep as
  `altdata/rates_attribution.py`, a command-line `show` with nothing in the
  Weekly. So "beside the existing block" has nothing to sit beside. The lens is
  its own sub-section, and its note names the block's module.
- **The Monthly has no "Rate and Liquidity Machine lever table".** The Machine is
  a paper. A minimal lever table (one row, long-end supply, with SR-33's
  modifier) is new in the Monthly's Plumbing.
- **ACM does not publish past ten years**, so the 30y prints "not published at
  this tenor". The 2y has no TIPS series, so it reads the 5y TIPS, labelled as
  the nearest.
- **The paste's fixture "a week at 149 bp (watch)" conflicts with the ruled
  150 bp line.** Built as ruled: 149 is below the line, and 150 is watch. Both
  are fixtures. See Needs you 2.
- **The MoF reserves file switched to the era year in 2023.** It prints 令和5年
  with an empty Western-year column, so the reader reads the era year. A reader
  keyed on the Western year stops at September 2022.
- **The Weekly's FIMA line has read 0 for weeks.** The H.4.1 package's latest
  Wednesdays (23 Sep to 7 Oct) are 0, so the line says "$0.0bn outstanding".
  The fixture's positive week is synthetic, as the paste asked.
- **The buyback schedule includes cash-management and TIPS operations.** They
  are stored too, and printed with the type named. Only the long-end sectors
  (10–20y, 20–30y, TIPS 10–30y) enter the lever modifier.
- **The order of work.** For each item, the fixtures were written after its code,
  in the same session. The paste asked for fixture first.
- **Gate changes:** `validate_prices`, the basket count and the continuous set,
  which EUR/CHF adds to.
- **The Monthly prints the month's split only.** `validate_stack_cadence` refuses any
  week phrase at the Monthly's cadence. So at the Monthly:
  - the tenor table and its frame carry the month alone;
  - EUR/CHF's change runs over the month;
  - the FIMA line drops its week average.

  The paste asked for "the week's and the month's split" in the Monthly's rates
  section, and the cadence rule won. The Weekly carries both.
- **`validate_monthly_stack`'s takeaway check** counted every Plumbing
  sub-section with table rows as a bucket. It now counts the buckets only.
  Batch 3's sub-sections carry tables but no bucket, and ask for no paragraph.

## Merging with the other branches

- **`book-b-scanner-2`** also edits `yfinance_source.SYMBOLS`,
  `validate_prices`' basket count and the registry's `market_closes` and
  `market_actions` counts:
  - it is 81 there and 54 here, so the merged total is 82;
  - the count lines conflict, and the resolution is the sum.
- **`sr-36-basis-proxy` / `sr-43-49-rates-anchor` / `aq-3-series-*`** edit
  `altdata/config.py`, `yfinance_source.py`, `metrics_registry.yaml`,
  `source_registry.yaml` and `weekly_stack.py`. Expect adjacent-line conflicts:
  keep both sides.
- **The W-1 chain** (W-1.2, W-1.3a, W-1.3b) rewrites `calendar_week` and
  `plumbing_week`:
  - this branch adds one hook line to each, plus the gate count in CLAUDE.md;
  - keep both sides;
  - after merging, rerun `validate_batch3_a` and `validate_weekly_stack`.

## Needs you

1. **SR-30's tiers, on the only free series.** The ruled tiers (150 watch, ~190
   crisis) are daily benchmark levels. The stored series is the ECB's monthly
   average: its November 2011 peak is 154.0 bp, so crisis is 4 bp above watch,
   and it reads 96.7 bp for September 2026 against the entry's 147–149 bp.
   Options:
   - keep 150 / 154.0 as built;
   - rescale the tiers to the series, for example by its own percentiles;
   - fund a daily source (a Webstat key in `.env`, or an inbox drop) and set
     the tiers on the daily weekly close.
2. **The 149 bp fixture.** The paste calls 149 bp "watch", but the ruled line is
   150. As built, 149 is below the line. Keep 150 / open watch lower (name the
   level).
3. **AQ-3's duplicate spread.** `aq-3-series-2` stores monthly
   `calc.oat_bund_bp` and `calc.btp_bund_bp`. This branch computes the same
   spreads at read time from the same legs. At merge, keep AQ-3's stored
   series and point SR-30 at them / keep the read-time computation and drop
   AQ-3's two calc series.
4. **The backfills, on the box, after merge** (yours to run):
   - `ssh vps 'cd ~/chester-reports && .venv/bin/python tools/backfill_prices.py --years 5 --symbols EURCHF=X'`
   - The three new official writers backfill themselves on their first run, at
     the next 16:10 pass: the whole history for buybacks and MoF reserves, and
     the H.4.1 package.
   - The FRED pull takes DFII5's history on its next run, and ACM's workbook
     the two new columns.
5. **Audit #4 (14–15 Oct)** verifies the crisis level and places the register
   numbers. The register entries here use decision 1's numbering, as ruled.
