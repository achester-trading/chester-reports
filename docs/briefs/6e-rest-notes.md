# 6e, the rest: macro completeness and the lenses other orders bind to it (session notes, 16 Oct 2026)

**This branch, `6e-rest`, is cut from the tip of `6e-metric-lenses` (`273dd8a`),
session B's own branch, so it carries 6e part 1 and merges after it. Both merge in
the second stitched chain (ruling (d)7, 16 Oct 2026).** Branch only: pushed, not
merged, not deployed, nothing run on the box.

Read first: `docs/briefs/6e-lenses-notes.md` ("What remains of 6e" and "Needs
you", ruled on 16 Oct); `docs/briefs/metric-lenses-brief-2026-10-01.md`;
architecture v3, Session 3 (lines 422-697) and Part 17 (lines 3386-3516); the
Batch 4 order, section 4.1 (SR-43); the JPM GTM order of 3 Oct (the CPI-PCE gap).
Batch 7's items 46 and 48 are the next paste on this line, not this one.

## Part 0: CI and the rulings on `st-r4-tranche-1b`

Recorded in full in `docs/briefs/st-r4-tranche-1b-notes.md`, "Part 0". In short:

**The CI reads:**

| Run | Commit | Jobs passed / failed | Failing gates | Fix |
|---|---|---|---|---|
| 38970818174 | `bd5cd2a` | 111 / 13 | `validate_security_master`, `validate_alpha`, `validate_monthly_stack` | SM00195-198 with `next_id` 199; the alpha fixture moved from TLT to IEF; 27a made the Weekly's only |
| 38974666074 | `036c393` | 101 / 7 | `validate_official_sources`: a renderer imported the Census writer | `96342c1` |

Run 38977257824 on `96342c1`: **passed, 95 jobs, 0 failed** (read 16 Oct). Part 0 is green.

**The changes:**
- **Census:** the hold is lifted (ruling (a)). The writer is on the external
  roster, its `KEYS` are now literal, and the source registry says live.
- **Cboe history:** a new writer, `altdata/sources/cboe_indices.py`, reads COR1M
  and COR3M from 2006 and DSPX from 2014 (ruling (e)). The dispersion panel reads
  Cboe first and Yahoo's pull as the fallback.
- **Drafts:** the Batch 5 drafts are committed for your accept-all (ruling (c)).
  - The three narrative lines are pending proposals in `config/narratives.yaml`.
  - The appendix notes, A-6 and the pair are in `docs/dated-appendix-queue.md`.
  - Item 24's line is corrected from FRED: the 10-year first closed at or above
    5.25% on 29 Sep 2026. The close before that was 12 Jun 2007, not 2002.

**Drafts on this branch:** none. Part 0's drafts are on `st-r4-tranche-1b`,
listed there with file and line under "Drafts committed, for Ari's accept-all".

## What this branch builds

### 1. Macro completeness: S3a, S3b, S3c and the CPI lead composite

**"S3a", "S3b" and "S3c" are the architecture's Session 3 work blocks, not
series sets** (master schedule lines 42-44 and 190-192). The free sources carry
part of each; the rest is a named gap below.
- **New FRED series:** `altdata/config.py` gains **`FRED_6E_SERIES`, 25 series**
  on the existing pull (`FRED_PULL_SERIES` 129 → 154). Each id and unit was read
  off fredgraph and the series page on 16 Oct 2026, with its latest print, in the
  list's comment.
- **New calc series:** `altdata/macro_6e.py` writes **23 calc series** in the
  market_features pass, after the AQ-3 rows (`rows()`). A fault there costs only
  these rows.
- **Availability:** every row's availability is its latest input's.

**S3a, path-aware sampling.**
- **`calc.path_divergence_usdjpy`:** Yahoo's USD/JPY close (`JPY=X`) less FRED's
  H.10 noon fixing (DEXJPUS), same day, in percent.
- **The flag:** `macro_6e.path_divergence_flag()` fires at 3 sigma of the
  trailing year, with at least 120 days. This is the architecture's "JPY flags
  `path_divergence`".
- **Gaps:** the source abstraction (`sources/base.py`) is not built here,
  `_base.py` being its nearest form. THB has no stored Yahoo close.

**S3b, rates and policy.**

New FRED series:

| Key | FRED id | Notes |
|---|---|---|
| `fred.fed_target_upper` | DFEDTARU | the target range, upper limit |
| `fred.fed_target_lower` | DFEDTARL | the target range, lower limit |
| `fred.effr` | EFFR | business days; DFF was already stored as `effr_daily` |
| `fred.estr` | ECBESTRVOLWGTTRMDMNRT | the euro short-term rate |
| `fred.sonia` | IUDSOIA | Bank Rate's FRED series, BOERUKM, stopped in 2017 |

Calc series:
- `calc.policy_2y_minus_effr_bp`: the architecture's easing-priced proxy.
- `calc.sofr_iorb_bp` and `calc.sofr_effr_bp`: funding stress.
- `calc.ccc_bb_oas_bp`: Session 2's CCC-BB differential.
- `calc.real_policy_rate`: EFFR less core PCE year over year.
- `calc.policy_diff_us_ea_bp` and `calc.policy_diff_us_uk_bp`: the overnight
  differentials.

Gaps (not free, or not on FRED):
- Term SOFR, repo fails and SRF usage.
- Swap spreads (FRED's ICE swap series are discontinued).
- The Cleveland Fed expected rate path, the ZQ strip and the path dispersion
  (`policy_path`).
- The German 2-year, euro-area core HICP, Euribor-OIS, PEPP/APP runoff and the
  BoE Bank Rate.
- The ECB balance sheet. ECBASSETSW is in **euro** millions, and no registry unit
  carries a euro stock, so it is not registered.

**S3c, fiscal and demand.**

New FRED series:

| Key | FRED id | Units |
|---|---|---|
| `fred.mts_deficit` | MTSDS133FMS | millions |
| `fred.mts_receipts` | MTSR133FMS | millions |
| `fred.mts_outlays` | MTSO133FMS | millions |
| `fred.fed_interest_payments` | A091RC1Q027SBEA | billions SAAR |
| `fred.fed_current_receipts` | FGRECPT | billions SAAR |
| `fred.fed_debt_total` | GFDEBTN | millions |
| `fred.nonfin_corp_debt` | BCNSDODNS | Z.1, millions |
| `fred.korea_exports` | XTEXVA01KRM667S | US dollars, monthly |

CMDEBT, already stored as `total_hh_debt`, was checked: millions.

Calc series:
- `calc.deficit_ttm_pct_gdp`: twelve consecutive MTS months against nominal GDP,
  both legs in millions.
- `calc.interest_to_receipts`: interest against receipts.
- `calc.federal_effective_rate`: interest over total public debt.
- `calc.r_minus_g_marginal` and `calc.r_minus_g_average`: **R less G on both
  bases**, the 10-year and the effective rate, each against nominal growth. The
  gate's "R-vs-G on both bases".
- `calc.tga_range_13w` and `calc.tga_vol_13w`: the TGA's range and volatility, in
  dollars.
- `calc.fed_debt_total_pct_gdp`, `calc.nonfin_corp_debt_pct_gdp` and
  `calc.household_debt_pct_gdp`: debt against GDP by sector.

Gaps:
- The 12-month maturity share (MSPD by maturity) and the coverage stress test
  that needs it.
- Korea's 20-day exports (FRED carries the monthly) and TSMC's revenue.
- The shelter, PPI-stage and Manheim leads beyond what FRED serves.
- The disruption-price divergence (PortWatch).

**The CPI lead composite.** `altdata/cpi_lead.py`, configured in
`config/macro_6e.yaml` `cpi_lead`.
- **Components:** one leading series per basket component, so nothing is
  counted twice:
  - core goods ← import prices ex fuel, stated lag 6 months;
  - services ex shelter ← the Atlanta Fed wage tracker less 1.5% trend
    productivity, stated lag 6 months;
  - shelter, food and energy are named as **not covered**, each with its reason.
- **Weights:** CPI basket shares (BLS, December 2025, rounded to sum to one).
- **Horizons:** 3 and 6 months cover **44.5%** of the basket. The 9-month horizon
  is absent: no stated lag reaches it.
- **Series:** `calc.cpi_lead_3m`, `_6m` and `_9m`.
- **Status: stated lags, unvalidated.** The architecture says the composite cannot
  be built before Session 6's lag fit, so the lags are parameters.
- **The kill test is coded.** The 6-month composite is checked against realized
  CPI six months later. It is untested under 60 months, and below a 0.3
  correlation it is killed and the composite withheld.
- **The conditioner:** `calc.realized_10y_vs_expected_10y`, trailing ten-year CPI
  less the breakeven, with its roll-off calendar of flat 2.5%, 3.0% and 3.5% paths
  over 12 and 24 months.
- **More FRED series stored for the next pass:** the CPI shelter, rent, OER,
  services, core goods and used-cars indices; PPI final demand, intermediate and
  unprocessed; and import prices.

**Every new key has its family and forms under part 1's rules.** Each is
registered with its units and a family:
- the 25 in a `fred_6e` block, with `member_families`;
- the 23 calc keys individually, with `family:` inline.

The exception is `fred.mts_deficit`, a monthly flow of either sign, which is
lens-excluded with its reason and read through the twelve-month ratio.

### 2. The three lenses other orders bind to 6e

- **The core CPI less core PCE gap** (the JPM GTM order, 3 Oct: "a derived series
  with a lens"). It is `calc.core_cpi_pce_gap` in the ratio family: percentiles
  and the 3-month trend. Its lens adds a **sign-flipped** flag and the date the
  current sign began (`config/metric_lenses.yaml` `sign_flip`).
- **The SR-43 inflation anchor and the 10-year fair-value lens.** Batch 4 section
  4.1 consolidates the anchors "into one lens in the 6e metric-lenses build, rates
  family", and no other text specifies a fair-value lens, so this reads the two as
  that one lens. `fred.yield_10y`'s lens now carries:
  - the inflation anchor and its gap in bp;
  - the fair value on the inflation fit and on the twin-deficit fit, each with
    its gap;
  - the term premium.

  All are read from `altdata/rates_anchors.py`, which still owns the fits. Each
  absent part carries its reason. Today the twin-deficit fit has fewer than ten
  countries with WEO balances. One printed line is tagged "(descriptive;
  unvalidated, n=0)".

### 3. The Weekly and the close adopt the lens columns

- **The cells:** `daily_cascade/lens_cells.py` now holds the columns and cells,
  moved from `monthly_macro/writer/render_v2.py`. A series' cell is therefore the
  same in every report.
- **The table:** `lens_cells.lens_table()` builds one table (Series, Family,
  Lens, Flags). The Lens cell is the family's two headline forms:
  - a rate: its 5-year and long percentiles;
  - a spread: its 3-month change and 5-year percentile;
  - a release: year over year and 3 months annualized;
  - a price: distance from the 52-week high and the 12-month-return percentile.

| Report | What it gains | What it displaces |
|---|---|---|
| **The Weekly**, Plumbing | Plumbing's six series plus IG OAS, CPI, core PCE, U-3 and the CPI-PCE gap, each by its family's forms, with the 10-year's anchors line; and the inflation block's two panels | nothing. Tables and lines only, so no prose word (words count prose only, `stack.section_words`) and no chart |
| **The close**, Plumbing | the same six series by their forms (the 5-year and long percentiles beside the one-session change the items already print) | nothing. No word and no chart; Plumbing keeps its one conditional chart, C3 |

The Monthly's stacked edition is untouched, as part 1 left it. The **Monthly v2
appendix** gains one table group, "Macro completeness (6e)", with the 48 new keys
by family.

### 4. The surprise prints "no consensus"

Ruling (d)6. With no consensus supplied, a release's lens carries
`surprise_state: "no consensus"` and the reason "no free consensus source exists
(ruled 16 Oct 2026); the SPF stays the quarterly anchor". The Surprise cell prints
**no consensus**: not a guess, a blank or a zero. A caller-supplied consensus
still computes it.

### 5. The widening thresholds and the 19 `long_window: ratio` values

**The thresholds** now live in `config/metric_lenses.yaml`, each with its basis.
The four ratified values are unchanged, and **four are session-set** under ruling
(d)4 (table below). Each fires at its value and not 1 bp below (`validate_lenses`
group H).

**The 19 `long_window: ratio` values** read as their family's default, with the
reason "not a window" (ruling (d)2). All 19 are the correlation layer's ratio-family
series, so each takes the ratio default of 20 years:
- `corr.avg_pairwise.60d`;
- `corr.btc__qqq.{60d,252d}` and `corr.btc__spy.{60d,252d}`;
- `corr.copper_gold__10y.{60d,252d}`;
- `corr.gold__dxy.{60d,252d}` and `corr.gold__spy.60d`;
- `corr.oil__dxy.{60d,252d}`;
- `corr.silver_over_gold`;
- `corr.stock_bond.spx_10y.{60d,252d}` and `corr.stock_bond.spx_tlt.{60d,252d,756d}`;
- `corr.us_intl.756d`.

The gate prints each with the window it reads.

The 295 boolean flags take no lens and their declarations are left alone, as part
1 built it. Direction of travel's rule stands (ruling (d)3).

### 6. The registry, the catalogue, the assignments

- **Registry:** `fred_6e` and the calc entries added; `fred.mts_deficit` added to
  `lens_excluded`.
- **Catalogue:** `altdata.macro_6e` in `config/catalogue_commands.yaml`.
- **Assignments:** `tools/assign_families.py` gains the 6e FRED members by hand,
  and `docs/briefs/6e-family-assignments.md` is regenerated: 2,666 keys.
  - The ambiguous count rises from 278 to **284**. The six new ones are the MTS
    receipts and outlays, the interest and receipts, total debt and corporate
    debt, read as quantities (alternative: release).
  - The 278 stand as the tool made them (ruling (d)1).
- **ERP (ruling (d)5):** still a listed gap. No series is registered, so the
  valuation lens has nothing to apply to.

## The session-set values, for Ari

| Item | Setting | Value | Why |
|---|---|---|---|
| widening, AA OAS | 3-month change | +25 bp | about 0.3 of AA's long-run median OAS (≈0.75%): the IG rule (+40 on ≈1.3%) scaled to AA |
| widening, BBB OAS | 3-month change | +50 bp | about 0.3 of BBB's median (≈1.6%) |
| widening, EM corporate OAS | 3-month change | +75 bp | about 0.3 of its median (≈2.6%) |
| widening, EM high-yield OAS | 3-month change | +150 bp | about 0.3 of its median (≈5%); above US HY's 100 as its spread is wider |
| path divergence | the flag | 3 sigma of the trailing year, ≥ 120 days | the series is mostly timing noise; the flag is for the day the path made the gap |
| TGA range | window | 13 weekly prints | one quarter: the tax-date and refunding swings |
| CPI lead | lags | 6 months, both components | import prices into core goods over about two quarters (the architecture's freight lag); wages into services likewise |
| CPI lead | wage offset | −1.5% | wage growth less trend productivity is unit-labour-cost growth |
| CPI lead | kill test | correlation ≥ 0.3 over ≥ 60 months | a weak positive relationship over five years at least |
| CPI lead | weights | 19 / 25.5 / 35.5 / 13.6 / 6.4 | BLS relative importance, December 2025, rounded to sum to one |

## Where Batch 7's items 46 and 48 attach

**`daily_cascade/inflation_block.py`** is Plumbing's inflation block (the
Weekly's). It is a list of panels, `PANELS`: `lead`, `gap`, then two reserved
slots that print nothing until filled.
- **Item 46, the CPI decomposition:** slot `"decomposition"`.
  - It holds the contributions from energy, food, core goods, shelter and core
    services ex shelter; the Cleveland Fed median and trimmed mean; diffusion; and
    the pass-through flag.
  - It is one builder `(st, cutoff) -> sub-section`, placed after the gap.
  - The close's CPI-day line reads the same builder's data.
  - Its FRED legs are new series:
    - Cleveland's median and trimmed mean, MEDCPIM158SFRBCLE and
      TRMMEANCPIM158SFRBCLE (not stored);
    - the components, which partly ride this branch's `cpi_*` series.
- **Item 48, group A, the macro-release lenses:** slot `"labour"`.
  - Employment lenses 1-6 go here, after the decomposition.
  - The CPI lenses 7-11 extend the release family's forms in `derived.lens_forms`.
    The CPI-PCE wedge (lens 11) is this branch's `calc.core_cpi_pce_gap`.
  - The cross-cutting 21-24 are forms for every release. "First print against
    revised" already reads `available_at`, through part 1's revision line.
  - Lens 23's surprise stays "no consensus" until a source is ruled.

## Box commands, for Ari (inside a window; nothing here was run on the box)

These run after this branch merges, which is after the chain and 6e part 1. No
unit file changed. The 25 FRED series arrive at the next scheduled pull. Their
history, and the calc series' history, are backfilled once:

1. The 25 FRED series at their first publication. `altdata.fred_history` reaches
   main with the chain (AUD-3d). Dry run first:
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.fred_history backfill --series fed_target_upper,fed_target_lower,effr,estr,sonia,mts_deficit,mts_receipts,mts_outlays,fed_interest_payments,fed_current_receipts,fed_debt_total,nonfin_corp_debt,korea_exports,cpi_shelter,cpi_rent,cpi_oer,cpi_services,cpi_core_goods,cpi_used_cars,ppi_final_demand,ppi_intermediate,ppi_unprocessed,import_prices,import_prices_ex_fuel,atl_wage_tracker --dry-run | tail -40'`
2. The calc series over the stored history. Dry run first:
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.market_features compute --from 2000-01-01 --dry-run | tail -20'`
   then the same without `--dry-run`.
3. What 6e's series read today (reads only):
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.macro_6e show | head -120'`

## Gates, locally, one at a time

| Gate | Result |
|---|---|
| `tools/validate_6e_rest.py` (new) | **33 passed, 0 failed**. Groups: A S3a-S3c by hand; B the CPI lead composite (horizons, coverage, kill test, roll-off); C path divergence at 3 sigma; D the inflation block and its reserved slots; E the budgets hold; F registry, config, hooks, no fetch |
| `tools/validate_lenses.py` (extended) | **49 passed, 0 failed**. Groups H-L: the thresholds at their values and not below, and the 19 ratio windows; "no consensus" renders; the CPI-PCE gap's sign flip; the 10-year's anchors; the Weekly's and the close's lens table equal to the Monthly's forms on a shared fixture |
| `tools/validate_audit_3a.py` | **83 passed, 0 failed**. It now expects the `fred_6e` block and 6e's calc keys. Its worded-count mutation reads the count CLAUDE.md prints, where it hard-coded "seventy-five" |
| `tools/check_registry.py` | OK |
| `tools/check_library.py` | 0 failures |

**Left to CI:** every other gate. That includes those that render the Weekly, the
close and the Monthly through the changed builders: `validate_weekly_*`,
`validate_daily_close`, `validate_monthly*`, `validate_figure_budget` and
`validate_edition_consistency`.

No gate read the live store, fetched or called a model.

**CI:** run 38977476616 on `9cefce1`: **passed, 85 jobs, 0 failed** (read once, 16 Oct).
`6e-releases` starts from this tip; no fix was needed.

The Makefile gains the gate. CLAUDE.md is recounted: seventy-seven code gates
(seventy-four Python), `FRED_PULL_SERIES` 154 with `FRED_6E_SERIES` 25 named, and
a paragraph on 6e, the rest.

## Files shared with the open branches

Each branch was compared with its merge base and this branch's diff from
`273dd8a`. The overlap with session A's branches comes from the chain they carry,
which merges first.

| Branch | Shared files | At the stitch |
|---|---|---|
| `st-r5-fixes` (session A) | CLAUDE.md, Makefile, `altdata/config.py`, `altdata/market_features.py`, `config/catalogue_commands.yaml`, `daily_cascade/stack.py`, `daily_cascade/weekly_stack.py`, `metrics_registry.yaml`, `tools/validate_audit_3a.py` | take both sides. Counts are re-summed from the code: the FRED lists, the gates, `NEW_KEY_BLOCKS` |
| `docs-batch-7` (session A) | none | none |
| `st-r5-index`, `st-r5-t1-rest`, `sm-schema-1-1` | the same nine, `altdata/config.py` excepted on `sm-schema-1-1` | as above |
| `st-r4-tranche-1b` (B) | the same nine | as above; its Batch 5 hooks sit beside this branch's in `weekly_stack.py` |

The likeliest conflict points:
- **`metrics_registry.yaml`:** this branch appends before `bulk_imports:`, before
  `fred_aq3:` and at `lens_excluded:`.
- **`altdata/config.py`:** the `FRED_PULL_SERIES` union line.
- **`daily_cascade/weekly_stack.py`:** after the Batch 3 sub-sections.
- **`daily_cascade/stack.py`:** the close's `plumbing_section` return.
- **`monthly_macro/writer/render_v2.py`:** its lens cells now import from
  `daily_cascade/lens_cells.py`; no other branch touches it.

## Needs you

1. **The four session-set widening thresholds and the other session-set values**
   above, the CPI lead's lags and kill floor above all.
2. **The 10-year fair-value lens:** read as Batch 4 section 4.1's consolidated
   anchors lens, since no other text specifies one. Say if a separate model was
   meant.
3. **The CPI lead composite** covers 44.5% of the basket until a shelter lead is
   stored. The free new-tenant rent series are not on FRED. Name a source, or
   accept the gap.
4. **The six new ambiguous assignments** (the fiscal stocks and flows read as
   quantities), beside the 278 that stand.
5. **The gaps named under section 1**, if any should be bought or sourced: Term
   SOFR, swap spreads, the Cleveland Fed rate path, the 12-month maturity share,
   the ECB balance sheet's euro unit.
6. **Run box commands 1 to 3** after the merge, inside a window.
