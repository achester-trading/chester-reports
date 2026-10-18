# lenses-group-b: Batch 7 Group B, the surprise index and the quarterly meta-loop (session notes, 18 Oct 2026)

**This branch, `lenses-group-b`, is cut from the tip of `alpha-lab-3` (`fceb3b8`,
the CI fix below). It is session B's own line, so it carries the 6e lenses,
Tranche A, the leftovers and the lab. It merges after `alpha-lab-3` in the
second stitched chain.**

Branch only: pushed, not merged, not deployed, nothing run on the box. Every box
step is printed below for Ari, and no unit was enabled, started or reconfigured.

What it does:
- **Part 0:** reads `alpha-lab-3`'s CI and applies the 18 Oct rulings on its
  report.
- **Part 1:** builds Batch 7's Group B (ST-R6.48d, the PPI lenses; ST-R6.48e,
  the GDP lenses) and the surprise index (ST-R6.48f).
- **Part 2:** builds X-3.7, the Alpha Lab's quarterly meta-loop.

| Part | Commit |
|---|---|
| 0, the rulings of 18 Oct | `186b5a7` |
| 1, Group B and the surprise index | `f94072d` |
| 2, the meta-loop | `cef6e8a` |
| these notes | the commit after |

## Step 0: alpha-lab-3's CI

| Run | Commit | Result |
|---|---|---|
| 39097051684 | `395483f` (the build) | **failed**: 103 of 105 jobs. `validate_alpha` 254 passed, 3 failed, and the `gates-passed` roll-up |
| 39097161999 | `71ae80d` (its notes) | **failed**, the same: 103/105, `validate_alpha` 254/3 |
| 39111875413 | `fceb3b8` (the fix) | **success, 105 of 105 jobs** |

**The cause was mine.** Three checks in `validate_alpha` pinned the engine
registry to Tranche 2's four engines:
- the registry's list;
- `load_all()`'s length;
- the nightly loop's map of candidates.

alpha-lab-3 adds five engines. The checks now hold Tranche 2's four first, then
Tranche 3's five, all candidates that trade nothing (`ENGINE_IDS`); locally that
is 257 passed, 0 failed. The fix and the two failed runs' numbers are on
`alpha-lab-3` (`fceb3b8`). The fix's green run is read here; `alpha-lab-3`'s notes
say it would be.

## The rulings of 18 Oct, as applied

1. **"Doctrine tell" means the section 5.3 trust matrix's entries and nothing
   else.**
   - Rule 9 is gone from `config/alpha_tells.yaml` and from the importer;
     `doctrine_tells()` reads the matrix and nothing more.
   - The fixture's import now registers Doctrine 10 (not 11), and tells 30 in all.
   - On the box the import has not yet run, so no Rule 9 registration exists to
     supersede.
2. **Book D's horizon of 21 sessions stands as the registration's declared
   horizon, stated in the manifest as session B's.**
   - Book D's `from` now says so.
   - The tells batch's manifest carries a `notes` field naming the horizon as
     declared by session B at registration, not stated by the source, with the
     tells it covers.
   - Group B checks it on the fixture manifest.
3. **Venue fees.** Every fee in `config/alpha_crypto_venues.yaml` carries a
   `fee_basis`:
   - `venue_schedule`: Hyperliquid and Deribit, read on their own pages;
   - `third_party`: OKX and Coinbase. Each source line begins "THIRD-PARTY,
     dated 17 Oct 2026".

   Coinbase's 0.60% spot taker stands as the dated constant. The cost framework
   (X-1.4, the walk-forward net of costs) decides whether the carry clears it;
   the engine does not. Group D checks the labels.
4. **The macro engine trades the session after the print**, as built. No change.
5. **The payroll and FOMC surprises.** The consensus logger's source does not
   carry them, so they are listed gaps. The budget is under 48f below.

The rest of the ten are accepted as built. None grants a right.

## Part 1: Batch 7's Group B and the surprise index

Read first:
- the filed order (`docs/change-order-signal-triage-batch-7-2026-10-16.md` on
  `docs-batch-7`, `7b4f821`): item 48 in full, the ruling that Group B builds after
  Group A, and section 8's filing notes 2, 3 and 8;
- my 6e-releases notes;
- the metric-lenses brief and 6e's lens form in `altdata/derived.py`;
- the consensus logger and `altdata/surprise.py`.

**One finding first.** The consensus logger (`altdata/loggers/consensus.py`)
logs analysts' forward EPS and P/E per name, through yfinance. The earnings
writer reads the analyst mean before each print from the same library. Neither
carries a consensus for any macro release: yfinance as pinned (`>=0.2.40,<1.0`,
0.2.66 installed) has no economic-calendar route. So "the settled source" covers
**earnings only**. Every macro release prints "no consensus", payrolls and FOMC
among them (ruling 5). The machinery reads `consensus.<id>` by name, so a source
that writes it later fills its row with no code change. Needs-you 1.

### The FRED series added (29; `FRED_GROUP_B_SERIES`; the pull is 228)

Every id, its first and latest observation, and its title were read off FRED on
18 Oct, through fredgraph.csv and the series page.

| Lens | Ids |
|---|---|
| 12, the pipeline | WPSID51, WPSID52, WPSID53, WPSID54 (stages 1-4 intermediate demand, SA, from Nov 2009). Final demand, PPIFIS, was already pulled |
| 13, PCE-relevant | PCU523940523940 (portfolio management and investment advice, from Dec 2022: PCU523920523920, the older code, stops in Dec 2022), PCU481111481111 (scheduled passenger air), PCU622622 (hospitals), PCU621111621111 (physicians); all NSA |
| 14, trade | PPITSS (final demand trade services, SA), WPSFD49116 (final demand less foods, energy and trade services, SA, from Aug 2013) |
| 15, the core | A191RL1Q225SBEA (real GDP growth), LB0000031Q020SBEA (real final sales to private domestic purchasers), the six contributions DPCERY2Q224SBEA, A008RY2Q224SBEA, A011RY2Q224SBEA, A014RY2Q224SBEA, A019RY2Q224SBEA, A822RY2Q224SBEA, and GDPDEF |
| 16, investment | Y034RC1Q027SBEA (information processing equipment), B985RC1Q027SBEA (software), B009RC1Q027SBEA (nonresidential structures), PRFIC1 (real residential, from 2007) |
| 17, GDI | GDI (the gap is computed against GDP, already stored) |
| 18, profits | CP (after tax, without IVA and CCAdj); S&P EPS is Shiller's stored `shiller.sp_earnings` |
| 19, income | DSPIC96, W875RX1, PSAVERT |
| 20, the nowcast | GDPNOW. Its updates are its vintages, so the path through a quarter comes from ALFRED's backfill and each later pull |

Rejected while checking:
- `A030RC1Q027SBEA` is the government's discrepancy, not NIPA's;
- `A446RC1Q027SBEA` is before tax;
- `PPIFDT`, `NYFEDNOW` and `TLDCCONS` do not exist on FRED.

### ST-R6.48d: the PPI lenses (`altdata/releases_b.py` `ppi_lenses`)

- **12:** each stage's month, three months annualised and year over year, and its
  gap on the year to final demand.
- **13:** the four PCE-relevant lines on the year. They are NSA, so the month
  prints labelled NSA and nothing is annualised over three months.
- **14:** trade services (the margin proxy item 35 strips out) beside final demand
  less foods, energy and trade services.
- **The display:** the inflation block's reserved `ppi` slot is now
  `ppi_panel`. It is one table plus the pipeline line, and it prints nothing
  while no PPI series is stored.
- **The release-day read line:** "PPI for Sep 2026: final demand +0.2% on the
  month (+2.4% on the year, …); what moved it: less foods, energy and trade …;
  trade services …; stage 4 … (surprise: …)."

### ST-R6.48e: the GDP lenses (`gdp_lenses`)

- **15:** final sales to private domestic purchasers, quarter on quarter
  annualised and on the year; real growth; BEA's six contributions, government
  labelled the fiscal impulse; their sum against growth with the residual; the
  deflator.
- **16:** AI-related (information processing equipment plus software, nominal);
  nonresidential structures less data centers; real residential.
  - The data-center series is the Census's `census.vip_data_center`, read by
    name: the mean of the quarter's three months, millions to billions.
  - Its writer is session B's `st-r4-tranche-1b`, not on this line, so here it
    prints "not stored" until the stitch.
  - A spending series is not NIPA's concept, and the line says it is an
    approximation.
- **17:** GDI less GDP as a percent of GDP, and its change over four quarters.
  Report-only.
- **18:** NIPA after-tax profits on the year against S&P EPS on the year, at the
  quarter's last month, with the gap.
- **19:** real disposable income and real income ex transfers, on the year and
  three months annualised; the saving rate and its 12-month change. The K-shape
  consumption-by-income panel is a listed gap: no such series is stored on this
  line.
- **20:**
  - GDPNow's updates for the newest quarter it covers at the cutoff: their
    count, the first, the latest and the change.
  - The newest quarter whose first print is knowable, read against the last
    nowcast before it. It is the first print, never a revision.
  - **The NY Fed Staff Nowcast is a listed gap.** Its page allows robots, but it
    serves the figures through a JavaScript application with no documented file,
    and FRED does not carry it (checked 18 Oct). The 16 Oct rule says public and
    easy, else a gap. Needs-you 2.
- **The display:** `daily_cascade/gdp_block.py`, two tables at the end of the
  Monthly's Slow layers (the order's placement). Every row carries the lens
  form. The release-day line is "GDP for Q2 2026: +3.0% annualised (…); final
  sales …; what moved it: consumption …; against GDPNow's last +2.6%, +0.4 pp
  (surprise: …)."

**The vintage handling, as 48c built it.** Everything is read as of the cutoff.
A quarterly series is keyed by its quarter's first month, so a quarter's change
is the three-month step, annualised by the fourth power. The fixture proves the
first-print rule: Q2's first print of 3.0% stands, not the 3.3% revision. It also
proves that a cutoff of 29 Jul sees neither Q3's nowcast nor Q2's print.

**Every lens figure carries the form** (`releases_b.lens_stat`):
- its family (release);
- its long window (`derived.long_window_of`: the release family's 20 years);
- two percentiles over the figure's own history (year on year for an index,
  the level for a rate or share), five years and the long window, each with its
  n;
- the disagreement flag at 30 points or more (`derived.DISAGREEMENT_POINTS`).

An absent input prints "not stored": the reason carries the key, and the printed
line carries the series' name, since no renderer prints a store id. Nothing is a
flag, a market-state input or a composite's. The order's flags are lenses 2-4,
Group A's.

**What the panels displace: nothing.**
- Tables and lines count no words (`stack.section_words`), and neither block asks
  for a paragraph or draws a chart.
- The Monthly's 10,000 words and 12 charts are unchanged; group E checks it.
- The PPI panel also prints in the Weekly, since the inflation block is shared, as
  Group A's CPI panels are. Needs-you 5.

### ST-R6.48f: the surprise index (`altdata/surprise_index.py`)

- **The surprise:** actual less consensus, in the release's own units.
  - A macro release's actual is its first print, read as of that print's
    availability.
  - Earnings use the stored surprise, percent of the analyst mean, per name.
- **Standardised by the release's own history:** the surprise over the standard
  deviation of its earlier surprises (the latest 40, at least 8), with its
  percentile among them and the n. Needs-you 3.
- **No composite:** the order defines none. `index()` returns
  `composite: None` with the reason.
- **The release-day read line gains the surprise with its percentile.**
  `releases.surprise_note()` feeds CPI's, the employment report's, PPI's and
  GDP's lines. With a consensus stored it reads "surprise: +0.30 % m/m against
  consensus, 100th percentile of its surprises (n=8)". Without one it reads
  "surprise: no consensus", which is every macro release today. JOLTS and the
  ECI keep the lens config's "no consensus".
- **The rows ride `python -m altdata.surprise compute`**, the existing step and
  writer, after the earnings rows (which they standardise). No writer is added to
  the roster.
- **The budget (ruling 5).** The consensus logger reads one Yahoo `.info` a name,
  0.6 s apart, nightly: 24 names, up to 39 with gtm-core-2's. Payrolls and FOMC
  add **no** reads, because the source carries neither.

**For the lab notes: the keys engine 4 reads by name.**
- `calc.consensus_surprise.<id>` and `calc.consensus_surprise_z.<id>` for `cpi`,
  `core_cpi`, `payrolls`, `unemployment`, `ppi`, `gdp` and `fomc`. All are
  registered, source calc, and have no rows until a consensus source writes.
- `calc.consensus_surprise_z.earnings`, per name as the instrument.
- `config/alpha_events.yaml` names `consensus_surprise` for CPI, payrolls and
  FOMC. `event_rates.surprise_series()` reads the consensus key where a row is
  stored, else the naive surprise under its own label, and the bucket's note
  says which.

### The registry, the catalogue and the counts (AUD-3a)

- **Registry:** the `fred_group_b` block (29 members, family release).
  - Growth rates, contributions and GDPNow are `percent_return`; the saving
    rate is `percent_share`; levels are `B`; indexes are `idx`.
  - The surprise index adds 15 `calc.` metrics, with payrolls in `count`
    (thousands).
  - `check_registry` is OK.
- **Catalogue:** `altdata.releases_b` and `altdata.surprise_index` (both `show`,
  read-only).
- **Counts:** CLAUDE.md now reads 29 in `FRED_GROUP_B_SERIES` and 228 for the
  pull, and ninety-seven code gates (ninety-four Python). The architecture box's
  pull count is 228. `validate_audit_3a` has the new block and count.
- **No new writer:** the 29 series ride the FRED pull; the surprise rows ride
  `altdata.surprise`.

## Part 2: X-3.7, the quarterly meta-loop

Read first:
- the change order's X-3.7 and section 6;
- alpha-lab-2's `loop_events`, the weekly loop's bounded re-fit (validated
  ranges, weekly) and its rebalance;
- the Quarterly's builder and budget (the read's 90-minute target, the
  quarterly depths);
- my alpha-lab-3 notes.

**`alpha/loops/quarterly.py`.** For every loop change of a closed quarter, it
computes the counterfactual from the same stored prices: what the lab would
have earned without the change.
- **`refit_accepted`:** the engine's own strategy is re-run over its rows from
  the change to its next re-fit (or the quarter's end), at the new and the old
  parameters. The contribution is the difference in summed returns times the
  engine's capital on the day.
- **`rebalance`:** each engine's recorded daily return times the notional times
  the change in weight, over the days the weights held. An engine weighted to
  zero has no paper return to scale, so it is listed and not guessed.

Everything else is not the loop's choice and is listed, not counted: the
governor's moves (the constitution's rules), the register's and the harness's
bookkeeping, and any reversed change.

**The net contribution:**
- **Negative:** ONE `meta_tighten` loop event, with its before, its after and the
  quarter it applies to (the next):
  - each re-fitted engine's ranges narrowed toward its current parameters, each
    side keeping half its distance;
  - the re-fit cadence doubled, never beyond every 8 weeks.
- **Positive or zero:** nothing changes and nothing is written.
- **Once per quarter.** A quarter is reviewed only if the lab ran through all of
  it.

**How it runs, without a new timer.** The weekly loop's first step asks for the
review within 21 days of a quarter's end (`meta_loop`). Its re-fit then obeys
`refit_due()` (the cadence in force) and `effective_ranges()` (the narrowed
ranges in force). The settings are in `config/alpha.yaml` `meta_loop:`,
session-set.

**The Quarterly's page** (`alpha/report.py` `quarter_page`) has five sections:
1. the lab's quarter (equity and drawdown);
2. the engines (P&L on the quarter);
3. the loop's contribution (each change against its counterfactual, the net,
   and the adjustment);
4. the failures register;
5. the gate-ladder standing (the rung, and engines at their minimum sample).

It reaches the Quarterly's email through `quarterly_attachment`: one line in
`monthly_macro/run.py` `deliver_edition`, keyed on the `alt_asset` prefix, which
never raises. It prints "no quarter closed yet" until the lab has run through a
whole quarter. Its prose is held to the Quarterly's medium depth (220 words);
it renders 129 on the fixture, and it draws no chart.

**The first real review.** The lab's first loop event will date from its
enabling on the box. If that falls in 2026 Q4, the first whole quarter is
2027 Q1, reviewed by the weekly runs of early April 2027.

## The gates, locally, one at a time

| Gate | Result |
|---|---|
| `tools/validate_releases_b.py` (new) | **59 passed, 0 failed.** A: the lens form by hand (100 and 70: disagree at 30, not at 29.2). B: the PPI lenses by hand. C: the GDP lenses by hand and the vintage rule. D: the surprise index (z = 0.3/sqrt(0.075/7); AAPL's 10/sqrt(68/7)), the gaps, no composite, engine 4's key. E: the panels, the budgets, the release-day lines with the percentile. F: the registry, no by-hand key, no composite touched, no fetch or model import |
| `tools/validate_alpha_lab_3.py` (extended) | **65 passed, 0 failed.** The rulings (Doctrine 10, the manifest's declared horizon, the fee bases) and group F: the re-fit's counterfactual (-152.21) and the rebalance's (-410.00) by hand, the negative quarter's one event (k [0, 4] -> [0.75, 2.75], every 2 weeks), once, read by the weekly loop; the positive quarter writes nothing; the page within budget; "no quarter closed yet"; the store's hash unchanged |
| `tools/validate_alpha.py` (weekly loop changed) | **257 passed, 0 failed** |
| `tools/validate_audit_3a.py` | **86 passed, 0 failed** |
| `tools/validate_6e_rest.py` (group D re-pinned: the PPI slot filled) | **34 passed, 0 failed** |
| `tools/validate_releases.py` | **61 passed, 0 failed** |
| `tools/check_registry.py`, `tools/check_library.py` | OK; 0 failures, 0 warnings |

**Left to CI:**
- `validate_alpha_no_orders`, over the new module;
- `validate_monthly_stack` and `validate_quarterly_stack` (they render);
- the Weekly and close gates;
- every other gate.

No gate reads the live store, fetches or calls a model. The FRED id checks above
were reads of FRED's public pages, made while building, never by a gate.

## Box commands, for Ari (inside a window, after this branch merges; nothing here was run)

No unit file changed and no timer is added. The 29 series and the surprise rows
arrive at the next scheduled pull and the next `altdata.surprise` step.

1. **The 29 series at their first publication** (GDPNow's path needs its
   vintages). Dry run first:
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.fred_history backfill --series ppi_fd_core_ex_trade,ppi_trade_services,ppi_stage1,ppi_stage2,ppi_stage3,ppi_stage4,ppi_portfolio_mgmt,ppi_airline_passenger,ppi_hospitals,ppi_physicians,gdp_real_growth,final_sales_pdp,gdp_contrib_pce,gdp_contrib_nonres,gdp_contrib_residential,gdp_contrib_inventories,gdp_contrib_net_exports,gdp_contrib_government,gdp_deflator,gdi_nominal,inv_info_equipment,inv_software,inv_nonres_structures,inv_residential_real,corp_profits_after_tax,real_disp_income,real_income_ex_transfers,saving_rate,gdpnow --dry-run | tail -40'`
   then the same without `--dry-run`.
2. **What the lenses and the index read** (reads only):
   - `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.releases_b show | head -200'`
   - `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.surprise_index show | head -80'`
3. **The meta-loop:** nothing to run. `python -m alpha.loops.quarterly --dry-run`
   prints "no quarter closed yet" until the lab has run through one.

The first renders to read:
- the Monthly of 1 Nov: the PPI panel in Plumbing, the GDP tables at the end of
  the Slow layers;
- the next close on a PPI or GDP day: the read line.

The Monthly's dry run is yours, as always.

## Files shared with the open branches

Session A's `st-t1-rest`, `st-t2-rates` and `gtm-core-2` touch these files that
this branch also edits:
- `CLAUDE.md`, `Makefile`;
- `altdata/config.py`, `config/catalogue_commands.yaml`, `metrics_registry.yaml`;
- `monthly_macro/stack.py`, `tools/validate_audit_3a.py`.

Each of my edits is an insertion beside a named anchor, or a count:

| File | My edit |
|---|---|
| `altdata/config.py` | `FRED_GROUP_B_SERIES` before the GLD ratio, and the union line |
| `metrics_registry.yaml` | the `fred_group_b` block before `fred_aq3`; 15 metrics before `events.release` |
| `config/catalogue_commands.yaml` | two lines |
| `monthly_macro/stack.py` | the GDP block after the crypto insert in the slow layers |
| `tools/validate_audit_3a.py` | the block name and the count |
| `CLAUDE.md`, `Makefile` | the gate line, the counts, two paragraphs |

The counts are the stitch's to recompute. `monthly_macro/run.py` (one line in
`deliver_edition`) and `alpha/` are mine alone. Untouched: chester-meme, `.env`,
the units, the registers and the trade ledgers.

## Needs you

1. **A macro consensus source.** None is stored and none is in the logger's
   library as pinned.
   - Whether yfinance 1.x carries an economic calendar is unverified, and an
     upgrade past the `<1.0` pin is a ruling.
   - An FOMC surprise could be built from the stored fed-funds-futures rows. That
     is market-implied, not a consensus.
   - Rule which, or leave them as gaps.
2. **The NY Fed nowcast:** a gap, or rule that the page application's data
   endpoint may be traced and read (robots allows it; nothing documents it).
3. **The standardisation.** I set z as the surprise over the standard deviation
   of the earlier surprises, not demeaned, over the latest 40 with a minimum of
   8. These are session-set. Keep, or rule otherwise.
4. **Structures less data centers** subtracts Census construction spending from
   NIPA's structures: an approximation, labelled. It fills at the stitch with
   `st-r4-tranche-1b`.
5. **The PPI panel also prints in the Weekly**, because the inflation block is
   shared, as Group A's CPI panels are. Keep, or make it Monthly-only.
6. **The meta-loop's settings and scope:**
   - the settings: narrowing to half, the cadence doubled, a ceiling of 8 weeks,
     a window of 21 days;
   - the scope: re-fits and rebalances counted, the governor not;
   - a re-fit's lab dollars as summed returns times the engine's capital on the
     change day.
7. **The long window for PPI figures** is the release family's 20 years. 6c gives
   CPI-family keys their full history; say if PPI should have it too.

## CI

Each run was read once, with `gh run list --branch lenses-group-b --limit 5`.

| Run | Commit | Result |
|---|---|---|
| 39112365516 | `186b5a7` (Part 0) | **success, 105 of 105 jobs** |
| 39114094511 | `f94072d` (Part 1) | **failed**: 104 of 106 jobs; `validate_lenses` 48 passed, 1 failed, and the `gates-passed` roll-up |
| 39114929397 | `cef6e8a` (Part 2) | queued when read (it carries Part 1's failure) |
| 39115072458 | `73f08eb` (these notes) | queued when read (the same) |
| 39115166631 | `adf8e31` (the fix) | queued when read; reported in the session's closing message |

**The cause was mine.** `validate_lenses` holds every resolved series to a
family, or to a reason it has none. The surprise index's 15 `calc.` keys had
neither. They now carry `conditions`, marked ambiguous (alternative: ratio), in
the registry's `families` map, as the naive surprises' block does. Locally that
is 49 passed, 0 failed, and `check_registry`, `validate_audit_3a` and
`validate_releases_b` still pass. The fix is `adf8e31`.
