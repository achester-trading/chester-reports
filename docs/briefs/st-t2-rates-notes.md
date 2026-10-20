# st-t2-rates — the signal-triage order's Tranche 2 for session A's line: ST-7's first calibration studies and ST-5's funding-currency features (session A, 18 Oct 2026)

**What it builds on.** The branch starts at the tip of `st-t1-rest` (`40b52f2`, the CI fixes), on session A's own line. It therefore carries ST-4, ST-6 and the GTM batch.

**Merge order.** It merges after `st-t1-rest`, in the second stitched chain: gtm-core-1, gtm-core-2, st-t1-rest, then st-t2-rates.

**What was done.** I pushed only. Nothing was merged or deployed, nothing ran on the box, and no unit was enabled or started.

**Commits:**

| Commit | What |
|---|---|
| `40b52f2` (on st-t1-rest) | Step 0's fixes |
| `76fc704` | Part 1: ST-7 |
| `8b40125` | Part 2: ST-5 |
| `e1a6083` | The gate fix after Part 1's CI |
| this commit | These notes |

---

## Step 0: CI read once, and the validate_stack finding

### st-t1-rest

- **Part 1** (`18ec03d`, run 39096586909) and **the notes** (`ac676f0`, run 39096734904) both **failed**, on the same two checks of mine:
  - **`validate_numeral_audit`.** The 5y5y percentile line wrote "th" by hand (`absorption_block.py:124`). It now goes through `numeral_audit.ordinal()`.
  - **`validate_by_hand_audit` A.** The dropped key's literal id (`manual.cbo_deficit_path`) appeared in `altdata/absorption.py` and in the registry. The not-tracked lines still name each key, now by its bare id ("by-hand key cbo_deficit_path, dropped 16 Oct"), which no reader can resolve. The other three not-tracked keys got the same form.
- **The fix commit** `40b52f2`: run 39112463758 is **green**. The same commit, pushed as st-t2-rates' first, is green as run 39112468313.
- The st-t1-rest notes record both runs.

### gtm-core-2

- **Run 39095118380:**
  - Attempt 1 **failed** on `validate_stack` M, a gate I had not touched.
  - Attempt 2, the re-run of the failed job, is **green**.
- **Run 39095548260** is st-t1-rest part 0, which carries gtm-core-2's fix commit. It is **green**.

### The validate_stack finding: a day-boundary fault

**The failure.** Attempt 1's job ran at 04:01 UTC, which is 00:01 ET on 18 Oct.

1. During the build, the close summed the model meter over the Eastern day it read when it wrote the footer, which was 17 Oct. The footer check passed.
2. Seconds later, the gate's own check re-read "today" in ET, got 18 Oct, and summed an empty day.

So the check failed: "and the line is the meter's own sum over the day's rows".

**The fix:**
- `daily_cascade/stack_close.py` reads the day once and keeps it with the edition as `model_day`. The footer is the meter's sum over that day.
- `tools/validate_stack.py` M compares against the edition's own `model_day`, not the gate's today.
- A new fixture records one call at 23:59 ET and one at 00:01 ET (03:59 and 04:01 UTC). Each counts on its own day.

`validate_stack` passes locally, 84/0.

**Why the day, not the session as-of.** "The edition's own as-of" here is the day the close summed. The meter's rows carry wall-clock times, not the fixture's session date. So the session date would count no calls at all, while the day the edition summed is right at any hour.

---

## Part 1: ST-7, the calibration studies

**The form.** Each study is a runnable module under `tools/calibration/` over `st7_common.py`. The modules follow the calibration rule:
- They pull public sources directly, through the writers' own readers where one exists.
- They never open the store or read the market-state object.

Each writes `docs/ledgers/sr-NN-ledger-2026-10-18.md` with its episodes CSV, through `altdata.ledgers.write_ledger`. That is the form the sessions used this week: as-of, window and n, the pass rule evaluated by code, and a verdict that prints its inputs.

**Labels and rules:**
- Every edition is labelled **"laptop run, public sources"**.
- Where the register states a pass rule, that is the rule. Where it is silent, the first edition pre-registers one, and the ledger prints it.
- Every ledger states its rights consequence without granting it.

| Study | Sources (point in time?) | As of | Window | n | Verdict |
|---|---|---|---|---|---|
| **SR-12** bond allocation | Z.1 `HNODSAQ027S`/`TFAABSHNO` (**revised**, current vintage); GS10, TB3MS, CPIAUCNS (not revised); Shiller | Z.1 2026-04; last completed entry 2021-06 | 1945–2026 | 3 in the cell (7 episodes) | **INSUFFICIENT**: below the floor of 5; no rate prints |
| **SR-15** rank test, gold window | World Bank Pink Sheet gold and total index; Shiller CAPE, price, dividend; GS10, CPIAUCNS | 2026-09; last paired month 2023-06 | 1971 on (gold also 1994 on) | 570 paired months | **FAIL**: cheap beat rich in 55.8% (rule ≥ 66.7%); gold window **FLIPS** |
| **SR-21** divergence episodes | DGS1, DGS10, DFEDTAR/L/U (not revised); ^GSPC | 2026-10-15; last completed 2025-12-11 | 1982–2026 | 46 completed (22 conceded, 24 refused) | **FAIL**: refused −17.5 bp vs conceded +45.5 bp (rule: refused ≥ conceded + 25) |
| **SR-22** auctions | TreasuryDirect search API, 2009–2026 (never revised); DGS2–DGS30 | 2026-10-08; last with 63 sessions forward 2026-07-09 | 2009-01-06 to 2026-10-08 | 1,034 flagged | **FAIL**: stress flag only (median −2.0 bp, falls 51.8%; rule median < 0 and ≥ 60%) |
| **SR-23** net supply | MSPD through `fiscaldata.py`; TREAST, FEDFUNDS, DFII10 (not revised); GDP (**revised**, with a publication lag); ACM (**re-estimated monthly**) | 2026-09 | 2003-12 to 2026-09 | 262 (49 pre-2008, 213 post) | **FAIL**: post-2008 b +5.1, t 1.29; pre-2008 b −34.1, t −3.47; descriptive, no modifier |

### Each study in brief

**SR-12.**
- **The cell:** the register's pass rule names "the growth/term-premium cell". That was a cell of the rates driver, which stays withdrawn (ruling 1). The first edition therefore reads the cell as CPI < 4% and a negative 12-month stock-bond correlation, within the paste's split of inflation by correlation.
- **The allocation:** it is Z.1, as ST-R5.30a built the live panel. AAII is not tracked and ICI is a gap.
- **Today's reading:** it sits at the 34th percentile, not a bottom decile. The register expected 2024–26 in the bottom decile, but that was AAII's reading, not Z.1's.
- **The falsifier:** bonds lost to cash over 12 months after 3 of 4 inflation-regime episodes (1969, 1977, 2021).

**SR-15.**
- **Current z:** gold +2.44, S&P +1.98, Treasuries +0.26, commodities +0.72.
- **The rank test:** it fails on overlapping months (55.8%) and on non-overlapping ones (43.8% of 16).
- **Gold's window test:** the 1971 start says rich gold reverts (median −12.6% against +29.7%). The 1994 start says it does not (+39.4% against +21.0%). So under the register, gold drops to base-rate rights only. The ledger states that consequence and does not grant it.

**SR-21.**
- **The legs:** the live gap's legs (futures and the SEP dot) have no keyless history. FEDTARMD's graph CSV serves only the current SEP. So the edition pre-registers DGS1 less the funds target.
- **Episodes:** the rule finds episodes in 1994, 1998, 2007, 2018, 2022 and 2024, but not in 2013.
- **Open now:** one episode is open, from 14 Sep 2026: the market leaning to hikes, the gap at +62 bp. 28 Oct is the first live test.
- **The result:** the split does separate, by 63 bp, but in the opposite direction: conceded episodes saw the long end move the market's way more than refused ones. The pre-registered rule is one-sided, the way the register states its mechanism, so it fails.

**SR-22.**
- **The flag tested:** G-32 makes ABS_STRESS the flag under test. The study calls the live rule itself, `altdata.absorption.abs_stress`. The pseudo-tail is a candidate row only, and it also fails (40.8%).
- **What the dealer leg does:** the "dealers above 20%" leg fires on 1,031 of the 1,540 auctions with forward data. Dealers took well over 20% of competitive awards through the early 2010s, so the live flag is on most of the time historically.
- **The sample:** 1,564 coupon auctions, 1,357 nominal and 207 TIPS.
- **Field names:** the study reads TreasuryDirect's renamed fields and the old ones, and queries on `competitiveAuctionCloseDate`. `writer-fixes-1` makes the writer's fix; this branch does not touch the writer.
- **No box vintages needed:** the API serves the whole history from 2009, and results are never revised. So the laptop edition reads the same records the box stores.

**SR-23.**
- **The supply measure:** it is ST-4's. MSPD's monthly change less TREAST's month-end change, summed over 12 months, over the GDP published by then.
- **The control:** the 12-month change in FEDFUNDS.
- **Errors:** Newey-West at 12 lags.
- **Robustness:** DFII10 and the ratio's own 12-month change are printed as robustness rows. None is significant post-2008.
- **The falsifier windows:** 2010–13, b −12.0 without the control and −6.2 with it. 2018–19, +8.1 without and +2.6 with.

### The A-3 gate status, written back

Each of the five register entries now carries a rule-31 draft after its validation gate:

> *Drafted under rule 31, 18 Oct 2026 (ST-7, for the accept-all; the register status above is unchanged):* **A-3 gate status: \<VERDICT\>.** ledger: docs/ledgers/sr-NN-ledger-2026-10-18.md, \<VERDICT\> (laptop run, public sources): …

The verdicts are:

| Entry | Verdict |
|---|---|
| SR-12 | INSUFFICIENT |
| SR-15 | FAIL |
| SR-21 | FAIL |
| SR-22 | FAIL |
| SR-23 | FAIL |

Each register status still reads "ADOPTED — gate pending". The change order's decision rows for these five entries and for rule A-3 are byte for byte unchanged; the gate pins their sha256.

### Gates

`tools/validate_st_t2_rates.py`, groups A to I:
- **A–F:** each study reproduces hand figures on a fixture. Its `judge()` returns PASS, FAIL and INSUFFICIENT on hand-made inputs, and the verdict prints its inputs.
- **G:** each committed ledger carries its as-of, window, n, pass rule, label and CSV. A ledger without its as-of, window or n is refused.
- **H:** the register drafts are checked, and the decision rows are untouched.
- **I:** no store, and no fetch: every HTTP helper raises during the studies.

---

## Part 2: ST-5, the funding-currency features

`altdata/funding_currency.py` rides the features pass after ST-4's absorption step, and it is never fatal. Its settings are session-set in `config/funding_currency.yaml`, each with its reason, until ST-8's gates calibrate them. Every feature is display and modifier only.

| Key | What | Source |
|---|---|---|
| `calc.jp_front_diff` | US 2-year less the JGB 2-year, bp | FRED DGS2; MoF JGB 2-year |
| `calc.jp_front_diff_60d` | its change over 60 sessions, bp | the above |
| `calc.jpy_pos_z` | CFTC yen net non-commercial, z over 156 weeks (52 minimum) | CFTC COT (legacy, JPY), at release |
| `calc.jp_hedged_carry` | DGS10 less (DTB3 less Japan's 3-month), % | FRED DGS10, DTB3, OECD IR3TIB01JPM156N (carried 70 days) |
| `calc.usdjpy_rvol_20d` | USDJPY 20-session realized vol, annualised | yfinance JPY=X |
| `calc.jpy_unwind` | 1 when USDJPY −3% in 5 sessions with vol ≥ 1.5× its 250-session median | the above |
| `calc.cny_fix_dev` | the fix against the previous onshore close, bp | CFETS fix; yfinance CNY=X |
| `calc.uscn_10y_spread` | DGS10 less the CGB 10-year, bp | FRED; CFETS |
| `calc.deval_tell` | the tell's **two tracked legs**, 1 or 0 | CFETS fix, CNH, CNY=X |

**Points to note:**
- **The third leg is not tracked (rule 30).** It is "state banks stop selling dollars", by-hand key `state_bank_dollar_selling`, dropped on 16 Oct. No keyless source within terms reports state-bank FX flows daily. CNH HIBOR is also registered NOT AVAILABLE (the TMA's terms). So a 1 is two of three legs, and every reader says so.
- **`calc.cnh_cny_gap` is not a second series.** `calc.cnh_cny_bp` (AQ-3, 11 Oct) is that gap. Its registry description now says so, and the tell computes it through the same `cfets.gap_bp`.
- **The candidate contradiction rows (G-10)** are `carry_vs_vol` and `fix_vs_offshore`. They are declared in `config/funding_currency.yaml`, in the table's own form, and are not in the table. The Monthly prints each one's `contradictions.gap_z`. No row opens, and nothing reaches the object or the Weekly's section 4. Moving them into `config/market_state.yaml` is a rules change (v1.13), for G-10's decision at the first Monthly after ST-5.
- **The Monthly lines:**
  - Factor IV gets eight lines: the yen stack, the unwind tell, the fix, the devaluation tell with its NOT TRACKED third leg, and the two candidates.
  - Duration Absorption gets the hedged carry beside Japan's holdings (SR-2's integration note), as line 18 of 18.
  - The China panel's "NOT AVAILABLE (ST-5)" lines are now stored values: the US-China 10-year spread, and the CNH-CNY gap read from `calc.cnh_cny_bp`.
- **Registry, catalogue and units (AUD-3a).** All nine keys are registered (bps, ratio, percent_rate, vol_pct, boolean), with families and long windows, all `trigger_eligible: false`. `config/catalogue_commands.yaml` names `altdata.funding_currency`. No `manual.*` key was added.
- **CLAUDE.md** gets a paragraph on ST-5 and ST-7, and the gate count is recounted to ninety-five code gates (ninety-two Python, three shell).

### Gates

- **`validate_st_t2_rates` J–M:**
  - J: every ST-5 key against a hand figure on one fixture. The front differential is +369 bp and +60 bp; positioning z 1.6826 and 1.7006; hedged carry 1.00%; calm vol 8.1435%; the unwind tell on and off; fix −14.2857 bp, then 0; spread +270 bp; the tell on and off; `fix_vs_offshore` z −1.2486 over 39 dates.
  - K: an empty or half store writes no row and no zero, and every line names its key and source.
  - L: nothing enters a composite or the object.
  - M: registry, catalogue, no by-hand key, no network import.
- **`validate_monthly` J:** on the fixture, the eight Factor IV lines are populated with their as-of, the Japan line and the China lines are stored, and the blocks are still lines only.

### Gates run locally

I ran only the gates I wrote or changed, one at a time:

| Gate | Result |
|---|---|
| `validate_st_t2_rates` | 71/0 |
| `validate_monthly` | 359/0 (1 skip, its own) |
| `validate_st_t1_rest` | 34/0 |
| `validate_stack` | 84/0 |
| `validate_by_hand_audit` | 17/0 |
| `validate_numeral_audit` | 172/0 |
| `check_registry` | OK |
| `check_library` | 0 failures |

Everything else is CI's, including `validate_regime` (whose group L reads `tools/calibration/`) and `validate_audit_3a`.

### CI for this branch

| Commit | Run | Result |
|---|---|---|
| `40b52f2` | 39112468313 | **green** |
| `76fc704` (part 1) | 39113766486 | **failed** |
| `8b40125` (part 2) | 39114598627 | **failed**: `validate_regime` L, 406 passed and 1 failed (the same pattern fault as part 1's run) |
| `e1a6083` | 39114669648 | **green**, 104 of 104 jobs |
| `254a225` (these notes) | 39114912209 | **green**, 104 of 104 jobs |

Part 1's failure was `validate_regime` L: my new gate's search pattern spelled the withdrawn cell's name, which that check forbids in any module. Fixed in `e1a6083`: the pattern drops that half, which stays `validate_regime`'s.

The later runs were read once on 18 Oct by st-t3-calib's step 0, which added them here (on st-t3-calib, so st-t2-rates' tip did not move). The branch is green at its tip.

---

## Box commands, for the operator

Run these inside a window, after Thursday's merge (22 Oct): weekdays 09:05–15:40 or 17:20–23:30 ET, never 16:00–17:20; weekends are open, clear of Sunday 05:00. I ran none of them.

**Where the ledgers go.** The ledger re-runs write outside the checkout, so no box run dirties the tree that `git pull --ff-only` needs clean. Copy the files back and commit them from the laptop. Each supersedes its laptop first edition: it is a new dated file, and the old one is never edited.

```bash
cd ~/chester-reports && git pull --ff-only
mkdir -p ~/chester-data/ledgers

# 1. ST-7's five ledgers, box editions (the same public sources, the calibration rule):
.venv/bin/python tools/calibration/sr12_bond_alloc.py --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/sr15_valuation.py  --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/sr21_divergence.py --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/sr22_auctions.py   --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/sr23_net_supply.py --box --out ~/chester-data/ledgers

# 2. ST-5's features over their whole history once (the features pass after this
#    keeps only its recompute window):
.venv/bin/python -m altdata.funding_currency compute --dry-run
.venv/bin/python -m altdata.funding_currency compute

# 3. The Factor IV and China lines as text, read-only, before the first render:
.venv/bin/python -m altdata.funding_currency show
```

**The first Factor IV render is the Monthly dry run, which is yours:** `python -m monthly_macro.run --dry-run`. It writes only to `reports/dryrun/`.

**From the laptop afterwards:**

```bash
scp 'vps:~/chester-data/ledgers/sr-*' docs/ledgers/
```

Then commit them, or tell a session to.

**st-t1-rest's ledger step (its #5)** writes into the checkout's `docs/ledgers/` by default. Adding `--out ~/chester-data/ledgers` there is safer, for the same reason as above.

---

## Files shared with the open branches

**New files of this branch** (nobody else has them):
- `tools/calibration/st7_common.py` and `sr12_bond_alloc.py`, `sr15_valuation.py`, `sr21_divergence.py`, `sr22_auctions.py`, `sr23_net_supply.py`;
- `tools/validate_st_t2_rates.py`;
- `altdata/funding_currency.py` and `config/funding_currency.yaml`;
- the ten files of `docs/ledgers/sr-*-2026-10-18*`.

**Edited, and shared by the stitched chains:**
- `CLAUDE.md`
- `Makefile` (one line, after `validate_st_t1_rest.py`)
- `metrics_registry.yaml`
- `config/catalogue_commands.yaml`
- `docs/signal-triage-register.md` (ten lines, the drafts only)
- `altdata/market_features.py` (the ST-5 hook after ST-4's)
- `tools/validate_monthly.py` (group J)
- `daily_cascade/absorption_block.py`
- `daily_cascade/stack_close.py` and `tools/validate_stack.py` (step 0, committed on st-t1-rest as `40b52f2`)

**Session B (alpha-lab-3, lenses-group-b).**
- A read-only trial merge (`git merge-tree`) of this branch's tip against each finds **no conflicting file that st-t1-rest's tip did not already have**. Those files are `CLAUDE.md`, `Makefile`, `metrics_registry.yaml`, `config/catalogue_commands.yaml`, `altdata/ledgers/__init__.py`, `monthly_macro/stack.py` and their neighbours.
- This branch adds hunks inside `CLAUDE.md`, `metrics_registry.yaml` and `config/catalogue_commands.yaml`. Each is an insertion beside st-t1-rest's own, so the stitch resolves them in the same pass.
- I used B's `altdata/ledgers/__init__.py` (`write_ledger`) and `sources.py` and did not edit them.

**writer-fixes-1.** Its TreasuryDirect field fix is in the writer, and this branch does not touch the writer. SR-22 reads both field names itself.

---

## Needs you

1. **SR-12's cell.** The withdrawn driver's growth/term-premium cell is read as CPI < 4% with a negative stock-bond correlation. That is pre-registered and stands unless you rule otherwise. The verdict is INSUFFICIENT either way, at 3 of 5.
2. **SR-21.**
   - **The keyless legs:** DGS1 less the target, not futures against the SEP dot.
   - **The result:** the one-sided rule fails, but the two-sided split is 63 bp the other way. Conceded episodes saw the long end move the market's way more than refused ones. That contradicts the register's mechanism and may warrant an amendment. The amendment is your judgment; I drafted none.
3. **SR-22's dealer leg.** "Dealers above 20%" of competitive accepted fires on 1,031 of 1,540 auctions since 2009, so the live ABS_STRESS is on most of the time historically. The 20% is G-32's ruling, and I changed nothing. The threshold or its denominator may want a ruling.
4. **SR-15's gold consequence.** The window test flips, and under the register gold drops to base-rate rights only. The ledger states it; it waits for your accept-all.
5. **SR-23.** It FAILs to descriptive, no modifier, for the item the order called the highest-value one. The pre-2008 subsample is 49 months with a negative coefficient. ACM's history is re-estimated, which the ledger notes.
6. **The devaluation tell is two-legged** while its third leg is not tracked. Accept that definition, or rule otherwise; for example, write nothing until a source exists.
7. **G-10.** The candidate rows sit outside `market_state.yaml`. Joining the table is a v1.13 rules change, at the first Monthly after ST-5.
8. **The session-set thresholds** in `config/funding_currency.yaml` are:
   - yen: −3% over 5 sessions, 1.5× vol, a 156-week z;
   - yuan: −10 bp lean, +30 bp gap, +20 bp widening.

   They wait for ST-8.
9. **Z.1 is revised.** An SR-12 run on ALFRED's first prints is possible on the box with the key. It is not needed for an INSUFFICIENT.
10. **The drafts for your accept-all (rule 31):** the five A-3 gate-status paragraphs in `docs/signal-triage-register.md`.
