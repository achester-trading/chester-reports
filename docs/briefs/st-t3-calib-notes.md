# st-t3-calib — the signal-triage order's Tranche 3 for session A's line: the rulings of 18 Oct on Tranche 2, ST-8's calibration studies II and ST-9's false-bottom audit (session A, 18 Oct 2026)

**What it builds on.** The branch starts at the tip of `st-t2-rates` (`254a225`, its notes), on session A's own line. It therefore carries ST-5 and ST-7, and everything under them (ST-4, ST-6, the GTM batch).

**Merge order.** It merges after `st-t2-rates`, in the second stitched chain: gtm-core-1, gtm-core-2, st-t1-rest, st-t2-rates, then st-t3-calib.

**What was done.** I pushed only. Nothing was merged or deployed, nothing ran on the box, and no unit was enabled or started. Every box step is printed below for the operator.

**Commits:**

| Commit | What |
|---|---|
| `6e14694` | Part 0: the rulings of 18 Oct |
| `ea57ff8` | Part 1: ST-8 |
| `3f64691` | Part 2: ST-9 |
| `493601f` | The CI fixes after Part 1's run |
| this commit | These notes |

---

## Part 0: CI read once, and the rulings applied

### st-t2-rates' CI

| Commit | Run | Result |
|---|---|---|
| `8b40125` (part 2) | 39114598627 | **failed**: `validate_regime` L, 406 passed and 1 failed. That is the same pattern fault `e1a6083` fixed. |
| `e1a6083` | 39114669648 | **green**, 104 of 104 jobs |
| `254a225` (its notes) | 39114912209 | **green**, 104 of 104 jobs |

Nothing of mine on st-t2-rates was left failing. The numbers are now in `docs/briefs/st-t2-rates-notes.md`. I added them **on this branch**, so st-t2-rates' tip did not move.

### The rulings as applied

- **Ruling 2 (SR-21).** The register's SR-21 entry carries a dated rule-31 note under its A-3 paragraph:
  - the sign reversal: +45.5 bp conceded against −17.5 bp refused, n=46 (22 conceded, 24 refused);
  - the verdict FAIL stands;
  - the mechanism text is not amended; the amendment is the Doctrine monthly's (7–8 Nov), drafted by the operator.

  CRED_STRESS and the venues' line print "descriptive only (SR-21's gate failed; ruling of 18 Oct)".
- **Ruling 3 (SR-22).**
  - **The base rate.** Wherever ABS_STRESS prints (Duration Absorption, and A-3's conditions in Cheap-and-Unloved), its base rate prints beside it: "on for 67 percent of auctions since 2009, n=1,540". The figure is `altdata.absorption.ABS_STRESS_BASE`, and the gate recomputes it from the first edition's CSV (1,034 of 1,540).
  - **The suspension.** The line also prints "display only: any modifier effect suspended by the ruling of 18 Oct until the Doctrine monthly rules". The gate holds that nothing outside the writer and the block reads `calc.abs_stress`.
  - **The labelled variant.** The ledger's second edition is `docs/ledgers/sr-22-ledger-2026-10-18-r2.md`. Its variant is the dealer share above its own rolling two-year 80th percentile, per tenor, with at least 8 prior auctions. It fires on 175 of 1,540 (11%), median 3m −1.0 bp, a fall in 51.4%: **FAIL** under the same rule. It is a candidate re-specification for the monthly and replaces nothing.
  - **The first edition** is byte for byte unchanged.
- **Ruling 6 (the devaluation tell).** The tell prints "Devaluation tell: 2 of 3 legs tracked (as of D)". The line carries:
  - each leg's state ("held" / "not held") with its value and threshold;
  - leg 3, NOT TRACKED, with its by-hand key named;
  - "no verdict prints while a leg is not tracked (ruling of 18 Oct)".

  The rule is `funding_currency.verdict_allowed()`, which reads the config's `third_leg`. The leg arithmetic has one home, `tell_legs()`: the stored `calc.deval_tell` and the printed legs both come from it. A fixture covers three states (both legs held, neither held, none readable) and shows no verdict word prints in any of them. A config with a third-leg source would allow one.
- **Rulings 1, 4, 5, 7, 8, 9 and 10** needed no code here:
  - SR-12's cell stands.
  - SR-15's draft already states gold's base-rate-only consequence.
  - SR-23 stays FAIL to descriptive.
  - The candidate rows stay outside `market_state.yaml`.
  - ST-5's thresholds waited for ST-8: Part 1 below. They stay session-set.
  - Z.1 is the box's.

  The SR-23 Kim-Wright and DKW legs are the box edition's where stored.

---

## Part 1: ST-8, calibration studies II

**The form.** Each study is a runnable module under `tools/calibration/` over `st8_common.py`, which builds on ST-7's `st7_common.py`. The calibration rule holds: public sources only, no store, no market-state object.

Each writes `docs/ledgers/sr-N-ledger-2026-10-18.md` with its CSV, labelled **"laptop run, public sources"**. Where the register states a pass rule, that is the rule. Where it is silent, the first edition pre-registers one in the module's docstring, written before the first run, and the ledger prints it. Long samples borrowed from the register's cited charts are labelled **"Sourced comparison, not episodes of ours"**.

| Study | Sources (point in time?) | As of | Window | n | Verdict |
|---|---|---|---|---|---|
| **SR-1** growth/value | French F-F factors (HML; CRSP 202608, restated each update); IVW/IVE, IWF/IWD auto-adjusted (Yahoo) | HML 2026-08; ETFs 2026-10-16 | HML 1963-07 on; ETFs 2000-05 on | 6 HML episodes | **PASS** (+4.2% at 6m, +17.9% at 12m after 0.5% costs; rule both > 0 over ≥ 6) |
| **SR-13** tech/defensives | French 49 industries (BE/ME, firms, size, VW returns) | formation 2026 | 1927–2026 | 4 completed in cell (b) | **INSUFFICIENT** (floor 5) |
| **SR-5** credit impulse | FRED TOTALSL, REVOLSL (**latest vintage**); Shiller S&P | G.19 2026-08 | 1943 on (total), 1968 on (revolving) | 19 episodes (10-year window) | **INSUFFICIENT** (the rule is on first prints; on latest vintages 1.49× and 1.57×, under 2×) |
| **SR-14** EM/dollar | EEM, ACWI, SPY (Yahoo, adjusted); FRED RTWEXBGS | 2026-10 | EEM/ACWI 2008 on | 3 completed | **INSUFFICIENT** (1 dollar-up episode; floor 2 a cell) |
| **SR-2** yen unwind | FRED DGS2, DEXJPUS; MoF JGB 2y (from 1974); CFTC legacy yen (from 1986); none revised | USDJPY 2026-10-09; CFTC 2026-10-13 | 1998 on | 6 episodes | **FAIL** (3 of 4 windows, 3 false positives; rule all four, ≤ 2) |
| **SR-4** fix and gap | CFETS fix (chinamoney, from 2015); CNY=X; CNH=X hourly (from 2024); CNH=F (proxy); FRED GS10, Japan 10y | fix 2026-10-16 | 2015 on; base rate 1998–2022 | 701 spot sessions | **INSUFFICIENT** (no keyless spot CNH reaches either window; the CNH=F proxy FAILs and admits nothing) |

### Each study in brief

**SR-1.**
- **The rule.** The z of the log growth/value ratio against its 10-year least-squares trend above +2 arms the rule. The first break while armed is a trigger: below the 40-week (9-month) mean, or more than 8% off the 52-week high.
- **The HML episodes:** 1981, 1992, 2000, 2009, 2019 and 2021. That is exactly the floor of six. There is no late-1990s early fire: the first triggers come in Apr–Jun 2000.
- **The ETF pairs read the other way.** IVE-IVW triggered in Sep 2008, Nov 2018 and Jan 2021, and IWD-IWF on the same three dates, but they are under their floor of six each. 5 of the 6 are negative at 52 weeks. Under the pre-registered rule they inform and do not block; see Needs you.
- **The 2023 reversal.** The 2021-01 HML trigger made +33% over 12 months. The ETF triggers of 2021–22 were mixed.
- **One definition of the rule.** The rule's arithmetic is `altdata/style_regime.py`, shared by the study and the panel.

**SR-13.**
- **The construction.** From French's 49 industries: tech is Softw, Hardw, Chips and Telcm. Defensives are staples, healthcare and utilities. Each basket's price-to-book is set against the market's.
- **Today:** tech +79% and defensives −20%, a spread of 99 points, at the 99th percentile of 100 years.
- **The top-decile episodes:** 1985, 1996, 2000 and 2020–26, against the register's list of six (a different construction from the chart's ~150 pp). Cell (b) has 4 completed episodes, under the floor of 5.

**SR-5.**
- **The laptop edition reads FRED's latest vintages and says so.**
- **The box edition.** `--alfred` reads ALFRED through `altdata.fred_history`'s paged reader with the key. It takes the first-print change: month m's first-vintage level less m−1's level in that same vintage. That edition's word is the gate's.
- **Revolving-only and the bear side** are printed, not judged.

**SR-14.**
- **Our proxies:** EEM/ACWI from 2008, plus EEM/SPY from 2003, labelled auxiliary and not judged.
- **The episodes:** firings in 2011, 2016 (dollar up, −12.5% over 36m), 2020, and 2025 (open).
- **Out of reach:** 1988 and 2001 are the chart's, not ours.
- **The flag is on now** (fired 2025-09). It stays display only.

**SR-2.**
- **The thresholds** are ST-5's, read from `config/funding_currency.yaml`. Crowding is pre-registered here: the lowest positioning z released in the previous 91 days at or below −1.0, with a Tuesday report read from its Friday.
- **The windows.** Oct 1998, 2007–08 and Aug 2024 flag. **Jan–Feb 2016 misses on crowding**: the speculators were barely short, z −0.15.
- **The false positives:** Mar 2004, Jun 2013 and Jan 2023.
- **The sensitivity grid.** Each threshold alone was loosened, holding the others at ST-5's. None reaches all four windows within two false positives. Loosening crowding to z ≤ 0 catches 2016 but adds a fourth false positive.
- **The thresholds stay session-set.**

**SR-4.**
- **The pass rule** is pre-registered, since the register states none: both legs in Aug 2015, never in Sep 2022–Sep 2023, and at most 2 episodes outside.
- **Spot CNH starts on 1 Jan 2024**, through Yahoo's hourly bars. So the verdict is INSUFFICIENT.
- **The CNH=F proxy** is labelled and carries forward points. It FAILs: 22 episodes outside the windows.
- **Spot since 2024:** the two legs held together twice, in Feb and Oct 2024.
- **The base rate.** The Japan–US 10-year spread was positive in every month of 1998–2022. Its sign held at 12, 24 and 60 months every time, and it spent 131 months running above +200 bp.
- **FRED no longer serves a China 10-year.** IRLTLT01CNM156N, the register's named source, returns 404, so the US–China line is NOT AVAILABLE on the laptop. The live line reads the CFETS curve.

### Gate status, written back

Each of the six register entries carries, after its validation gate, a rule-31 draft:

> *Drafted under rule 31, 18 Oct 2026 (ST-8, for the accept-all; the register status above is unchanged):* **Gate status (ST-8): \<VERDICT\>.** ledger: docs/ledgers/sr-N-ledger-2026-10-18.md, \<VERDICT\> (laptop run, public sources): …

The label is "Gate status (ST-8)", not ST-7's "A-3 gate status": none of these six entries is an input to Book A's rule A-3 (see Needs you). The register statuses still read "ADOPTED — gate pending". The order's decision rows (SR-1, 2, 4, 5, 8, 13, 14 and rule A-2) and the register's Index table are pinned by sha256 and untouched.

### Thresholds into config, and the one panel

- **Only SR-1 passed**, so only its thresholds entered config: `config/style_regime.yaml`. The file names its admitting ledger as `admitted_by: docs/ledgers/sr-1-ledger-2026-10-18.md` (PASS). The gate refuses any config whose `admitted_by` names no ledger, or one that is not PASS, and checks that every value equals the study's.
- **SR-2 and SR-4:** the thresholds stay session-set in `config/funding_currency.yaml`. Nothing reached `config/market_state.yaml`.
- **The panel** is the Monthly's style-regime sub-section, `daily_cascade/style_block.py`, in Slow layers after the Factor lines. It reads the store's IVW/IVE and IWF/IWD closes plus their stored distributions, the total return the gate tested, through `altdata/style_regime.py`. Each pair prints:
  - its z against the 10-year trend;
  - its distance from the 52-week high;
  - its position against the 40-week mean;
  - "setup live" and "this week a break while armed".
- **No flag word.** The register's narrow flag waits for the operator's accept-all.
- **What it displaces: nothing.** It is lines only: zero words of the 10,000-word budget and no chart.
- **SR-13's line does not ride on the panel**, because its gate is INSUFFICIENT. The panel says so in one line.

---

## Part 2: ST-9, the SR-8 false-bottom audit

`tools/calibration/sr08_false_bottoms.py` writes `docs/ledgers/false-bottom-audit-2026.md` with its CSV.

**The replay.**
- **Definition.** A candidate bottom is a new bear low followed by a 10% rally before a lower close. A false bottom is one later undercut; the true bottom is the bear's final low.
- **Scoring is on the S&P 500.** The Nasdaq Composite is replayed for its count only.
- **The state** at each trough (below a falling 200-day) is printed, not required: T&B's top side is not built, so it is not replayable.

| Bear | False bottoms | True bottom |
|---|---|---|
| 1973–74 | 2 (Aug 1973, Feb 1974) | 1974-10-03 |
| 2000–02 | 4 (Apr 2000, Apr 2001, Sep 2001, Jul 2002) | 2002-10-09 |
| 2007–09 | 4 (**Mar 2008**, Oct 10 2008, Oct 27 2008, Nov 2008) | 2009-03-09 |
| 2022 | 2 (**Mar**, **Jun–Aug**) | 2022-10-12 |
| Nasdaq 2000–02 | 8 (the register's sourced five, at 12–45%) | (count only) |

**The scores.** Each element is read at the trough plus 30 sessions, or before an undercut if that comes first. An element discriminates when it fires at ≥ 75% of at least 2 testable true bottoms and ≤ ⅓ of at least 3 testable false ones.

| Element | Held key | True | False | Not testable before | Word |
|---|---|---|---|---|---|
| breadth_industries | French 49 industries, the breadth-thrust form (proxy) | 4 of 4 | 5 of 12 | — | does not discriminate |
| breadth_sectors | `calc.breadth_sector_above_50d`'s arithmetic | 2 of 3 | 2 of 10 | 2000-04-14 | does not discriminate |
| **breadth_rsp_spy** | `calc.breadth_rsp_over_spy` | **2 of 2** | **2 of 6** | 2008-03-10 | **DISCRIMINATES** |
| new_leadership | French 49 industries; prior leaders as the "most-shorted" proxy | 2 of 4 | 3 of 12 | — | does not discriminate |
| credit_tightening | Moody's Baa less the 10-year (proxy; FRED's HY OAS now starts 2023-10) | 3 of 4 | 7 of 12 | — | does not discriminate |
| vix_contango | `calc.vix3m_over_vix` | 2 of 2 | 4 of 6 | 2008-03-10 | does not discriminate |
| retest | S&P 500 closes | 4 of 4 | 7 of 12 | — | does not discriminate |
| margin_spent | `finra.margin_debit` (FINRA's margin statistics file, from 1997) | 2 of 3 | 2 of 10 | 2000-04-14 | does not discriminate |
| short_fuel | `finra.short_interest_days_to_cover` (SPY; FINRA's API from 2017-12-29) | 0 of 1 | 0 of 2 | 2022-03-08 | not testable |
| time_prior | months since the peak | 2 of 4 | 2 of 12 | — | does not discriminate |
| leveraged-ETF AUM | none | — | — | never | **listed gap** (no keyless history known; no key pursued) |

**The verdict: FAIL.** One element discriminates, and the gate asks two. RSP/SPY's discrimination rests on two true bottoms, 2009 and 2022.

**The gate specification** is in the ledger:
- **The state:** the top side has fired and the index is below a falling 200-day.
- **Then:** the bottom threshold rises, at T&B's level.
- **The set:** RSP/SPY only. Eight elements are dropped; short interest is not testable; leveraged-ETF AUM is a gap.
- **"Two of the set" cannot bind.** The monthly decides what stands in its place.

**The Doctrine rule proposal** is in the ledger, labelled a proposal for the Doctrine monthly, drafted under rule 31 and granting nothing. It keeps the register's candidate text. Because only one element discriminates, it asks for confirmation "in a number the monthly sets", rather than for two.

**The T&B config stub** is `config/tb_false_bottom_gate.yaml`. It is inert: status inert, and no top-level `admitted_by`, since the audit FAILed. Each element carries its word. Only RSP/SPY carries parameters, with the ledger named beside them. The gate checks that no module reads the stub: only the audit names its path, in its ledger text, and no line that names it opens or loads a file. The SR-8 register entry is untouched.

---

## Gates

**`tools/validate_st_t3_calib.py`, groups A–R** (88/0 locally):
- **A–C:** the rulings.
- **D–I:** each ST-8 study against a hand figure on a fixture.
- **J:** the ledgers' as-of, window, n, label, CSV and sourced comparisons.
- **K:** the register drafts, and the pinned decision rows and Index.
- **L:** no store, no fetch, on validate_regime's own pattern.
- **M:** thresholds in config only beside a passing ledger, with a refused case.
- **N:** no new by-hand key. This branch touches none of the Weekly's builders (`daily_cascade/weekly_*.py`, `dealer_weekly.py`); the check reads `git diff origin/st-t2-rates...HEAD`. It is not checkable on a shallow checkout and says so; locally it found none.
- **O:** the replay reproduces a hand count on one fixture episode (a false bottom at 80, none at 70, the true one at 60).
- **P:** each element's score is computed by code, and every printed score equals the CSV's count.
- **Q:** the ledger, the proposal and the inert stub.
- **R:** no fetch.

**Changed gates.** I also changed `validate_monthly` (six sub-sections, and the "not rendered" line), `validate_st_t1_rest` E (the same), and the Makefile line. CLAUDE.md's count is now ninety-six code gates.

### Gates run locally, one at a time

| Gate | Result |
|---|---|
| `validate_st_t3_calib` | 88/0 |
| `validate_st_t2_rates` | 71/0 |
| `validate_st_t1_rest` | 34/0 |
| `validate_monthly` | 359/0 (1 skip, its own) |
| `check_registry` | OK |

Everything else is CI's.

### CI for this branch

| Commit | Run | Result |
|---|---|---|
| `6e14694` (part 0) | 39148131796 | **failed** on `validate_alpha` only (256/1). This branch did not touch it: see Needs you. |
| `ea57ff8` (part 1) | 39150911701 | **failed**:<br>• `validate_st_t1_rest` E (33/1), mine, fixed in `493601f`<br>• `validate_weekly_edits` 9 (90/1), mine, fixed in `493601f`<br>• `validate_alpha`, not mine |
| `3f64691` (part 2) | 39151733576 | **failed**:<br>• `validate_regime` L, mine: my group R pattern spelled the withdrawn cell's name, fixed in the CI-fix commit below<br>• `validate_st_t1_rest` and `validate_weekly_edits`, fixed in `493601f`<br>• `validate_alpha`, not mine |
| `493601f` | 39151947418 | **failed**: `validate_regime` L (mine, the same fault) and `validate_alpha` |
| `ed1e533` (these notes) | 39152102354 | **failed**, 102 of 105 jobs green: `validate_regime` L (mine) and `validate_alpha`, plus the summary job |
| the CI-fix commit after these notes | read on a43-render | `validate_regime` L fixed: the pattern drops the cell's names, which stay `validate_regime`'s own check. `validate_alpha`'s fix of record is session B's `3b0da9a`, cherry-picked onto a43-render (ruling 8 of 18 Oct). |

---

## Box commands, for the operator

Run these inside a window, after Thursday's merge (22 Oct): weekdays 09:05–15:40 or 17:20–23:30 ET, never 16:00–17:20; weekends are open, clear of Sunday 05:00. I ran none of them.

**Where the ledgers go.** They write to `~/chester-data/ledgers`, outside the checkout. Each box edition is a new dated file that supersedes its laptop first edition.

```bash
cd ~/chester-reports && git pull --ff-only
mkdir -p ~/chester-data/ledgers

# 1. ST-8's ledgers, box editions (the same public sources):
.venv/bin/python tools/calibration/sr01_sr13_style.py   --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/sr14_em_dollar.py    --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/sr02_yen_unwind.py   --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/sr04_cny_fix.py      --box --out ~/chester-data/ledgers   # about 4 minutes: the CFETS fix pages at 20 a request

# 2. SR-5 on ALFRED first prints, with the box's FRED key (altdata.secrets) -- the gate's own edition:
.venv/bin/python tools/calibration/sr05_consumer_credit.py --box --alfred --out ~/chester-data/ledgers

# 3. ST-9's audit, box edition (writes false-bottom-audit-2026-box-<date>.md):
.venv/bin/python tools/calibration/sr08_false_bottoms.py --box --out ~/chester-data/ledgers

# 4. SR-22, box edition with the labelled variant and base rates (st-t2-rates' list had it without):
.venv/bin/python tools/calibration/sr22_auctions.py --box --out ~/chester-data/ledgers
```

**From the laptop afterwards:**

```bash
scp 'vps:~/chester-data/ledgers/sr-*' 'vps:~/chester-data/ledgers/false-bottom-*' docs/ledgers/
```

Then commit them, or tell a session to.

**If SR-1's box edition does not PASS,** `config/style_regime.yaml` and the panel go with it. A session removes them on that ledger.

**The first render of the style panel is the Monthly dry run, which is yours:** `python -m monthly_macro.run --dry-run`.

---

## Files shared with the open branches

**New files of this branch** (nobody else has them):
- `tools/calibration/st8_common.py`, `sr01_sr13_style.py`, `sr05_consumer_credit.py`, `sr14_em_dollar.py`, `sr02_yen_unwind.py`, `sr04_cny_fix.py`, `sr08_false_bottoms.py`;
- `tools/validate_st_t3_calib.py`;
- `altdata/style_regime.py`, `daily_cascade/style_block.py`;
- `config/style_regime.yaml`, `config/tb_false_bottom_gate.yaml`;
- the ledgers `docs/ledgers/sr-{1,13,5,14,2,4}-ledger-2026-10-18*`, `sr-22-ledger-2026-10-18-r2*` and `false-bottom-audit-2026*`;
- these notes.

**Edited:**
- `CLAUDE.md`
- `Makefile` (one line, after `validate_st_t2_rates.py`)
- `metrics_registry.yaml` (the `calc.deval_tell` description only)
- `docs/signal-triage-register.md` (two dated notes and six drafts)
- `docs/briefs/st-t2-rates-notes.md` (its CI rows)
- `altdata/absorption.py`, `altdata/funding_currency.py`, `daily_cascade/absorption_block.py`
- `tools/calibration/sr22_auctions.py`, `tools/calibration/README.md`
- `tools/validate_monthly.py`, `tools/validate_st_t1_rest.py`

**Session B's branches.**
- `lenses-group-b` touches five of the same files: `CLAUDE.md`, `Makefile`, `docs/signal-triage-register.md`, `metrics_registry.yaml` and `tools/validate_monthly.py`. `weekly-fixes-8` touches three: `CLAUDE.md`, `Makefile` and `metrics_registry.yaml`.
- A read-only trial merge (`git merge-tree`) of this tip against `lenses-group-b`, `weekly-fixes-7` and `weekly-fixes-8` finds **no conflicting file that st-t2-rates' tip did not already have**. This branch's hunks are insertions beside its own earlier ones.
- I did not touch the Weekly's builders, any of session B's branches, Monday's chain or chester-meme.

---

## Needs you

1. **SR-1 passes at the floor, against its own ETF pairs.**
   - HML gives exactly 6 episodes, PASS.
   - The tradeable pairs give 3 episodes each, under their floor, and 5 of the 6 are negative at 52 weeks.
   - The pre-registered rule says the pairs inform and do not block, so the thresholds entered config and the panel renders, display only.
   - Accept the status, or rule that the pairs' reading blocks it. In that case a session removes `config/style_regime.yaml` and the panel.
2. **The label of the six drafts.** They read "Gate status (ST-8)", not ST-7's "A-3 gate status", because none of the six is an input to Book A's rule A-3. Rule otherwise and a session renames them.
3. **SR-5's gate is the box's ALFRED edition** (command 2). The laptop's latest-vintage edition is INSUFFICIENT by construction.
4. **SR-2 FAILs at ST-5's thresholds.**
   - Jan–Feb 2016 misses on crowding, the one threshold I pre-registered (z ≤ −1.0 over 91 days).
   - No single loosening passes. The thresholds stay session-set.
   - Whether 2016 belongs in an unwind anatomy whose speculators were not short is a question for the register.
5. **SR-4 is INSUFFICIENT on our sources.**
   - No keyless spot CNH reaches 2015–17 or 2022–23.
   - FRED's China 10-year, IRLTLT01CNM156N, which the register names, is gone (404).
   - Both are listed gaps under the standing rule of 16 Oct: no key pursued.
6. **SR-13 and SR-14 are INSUFFICIENT on our n.** Their flags and lines stay display only, or do not render.
7. **SR-8's audit FAILs.**
   - One element discriminates, RSP/SPY, on two true bottoms. The register's "two of the set" cannot bind.
   - What stands in its place, and the proposal's number, are the Doctrine monthly's (7–8 Nov).
   - HY spreads are measured by Moody's Baa less the 10-year, because FRED's ICE BofA HY OAS now starts in Oct 2023.
8. **`validate_alpha` fails on every branch after 10:00 UTC on 18 Oct. It is not this branch's code.**
   - The fixture runs the weekly loop at a fixed `2026-10-18T10:00:00+00:00`.
   - `alpha/ledger.py:414` stamps rows with the wall clock.
   - So after 10:00 UTC today the fixture's own rows look as if they came after the run, and "it lists every hypothesis of the week" fails (256/1).
   - It is the lab's to fix: it needs an injected clock or a later fixture instant. I did not touch `alpha/`.
9. **The SR-22 variant** also FAILs. The ABS_STRESS re-specification for the monthly therefore has no passing candidate from this edition.
10. **The drafts for your accept-all (rule 31):**
    - the six ST-8 gate statuses (SR-1, 13, 5, 14, 2, 4);
    - the SR-21 dated note;
    - the SR-22 dated note;
    - the Doctrine rule proposal in `docs/ledgers/false-bottom-audit-2026.md`.
