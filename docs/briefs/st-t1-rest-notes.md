# st-t1-rest — Batch 6's constituent ledgers and the signal-triage Tranche 1 remainder (session A, 18 Oct 2026)

**What it builds on, and the merge order.**
- **Cut from:** the tip of `gtm-core-2` at `89fdbaf`. It carries the GTM batch (both parts) and through it el-4-6, 6b and item 52.
- **Merge order:** **after `gtm-core-2`, in the second stitched chain.**
- **Branch-only:** pushed, not merged, not deployed, nothing run on the box, and no unit enabled or started.

The work:
- **Part 0:** Batch 6's two ledgers that need the constituent prices this line holds, ST-R5.31b and ST-R5.44b.
- **Part 1:** the signal-triage order's Tranche 1 remainder (`docs/change-order-signal-triage-2026-09-25.md` rows ST-3, ST-4 and ST-6), pulled forward from the week of 2 Nov.

---

## Step 0: `gtm-core-2`'s CI, and the rulings on its report

| Run | Commit | Result |
|---|---|---|
| 39093948685 | `ae09e15` (the build) | **failed**, two checks of mine |
| 39094111332 | `38276bf` (its notes) | **failed**, the same two |
| 39095118380 | `89fdbaf` (the fixes) | **failed**, one check, not mine (below); the failed job re-run |
| 39095548260 | `cd0bcd2` (this branch, part 0, carrying `89fdbaf`) | **green** |

**The two failures of mine,** fixed in `89fdbaf`:
- **`validate_official_sources`, the per-writer outage loop.** The new EDGAR reader was PENDING in CI (no SEC contact) instead of STALE. The loop now gives it a placeholder contact, so the outage path is the one tested.
- **`validate_st_r5_t1_rest`,** which pins the FRED counts. 57/159 became 63/165.

**The third failure is a midnight flake, not mine.** `validate_stack` M ("the line is the meter's own sum over the day's rows") compares with today in Eastern time. That run started at 23:52 ET and reached the check after midnight. The same commit is green in 39095548260, and the failed job has been re-run.

**The rulings of 17 Oct on the part 2 report, applied** (recorded in `gtm-core-2`'s notes):
- the queue entries stay drafts with no position until the 25 Oct dry run;
- SR-49 is skipped, confirmed;
- the five extra slides stand as one-time sourced figures;
- no GICS membership is taken by hand;
- the consensus log's budget is now its catalogue line: one Yahoo `.info` read per name, 0.6 s apart, nightly. That is 24 names before the change and at most 39 with the GTM names.

---

## Part 0: the two constituent ledgers

**Where they live.** Session B's ledger package is `altdata/ledgers/` (on `meme-ingest-ledgers-1` and `audit-leftovers-2`, not on this line).
- **Copied byte for byte:** its `__init__.py` and `sources.py`, identical on both of B's branches. The blobs are the same, `d0e73fa` and `b5893cc`, so the stitch sees one file; a trial merge with `audit-leftovers-2` confirms there is no conflict.
- **Not copied:** B's `__main__.py`, which differs between B's two branches. So `run 31b` / `run 44b` are not in its `ITEMS` yet. Each module runs on its own as `python -m altdata.ledgers.st_r5_31b`. Adding the two items to B's runner is one line each, at the stitch.

**The form is B's.**
- the as-of, the window and n;
- the statistic;
- the pass rule and the verdict that rule gives;
- the rights consequence, stated and never granted;
- a CSV of episodes beside the Markdown.

The pure functions take series, and the providers are the writers' own readers:
- `sp500_members.fetch_holdings`, `parse_holdings` and `yahoo_closes`;
- `ledgers.sources.yahoo`;
- or the store, on the box.

**Pass rules (the ruling: "the rule as stated, else the first edition's").** Neither item states one, so each first edition pre-registers its rule in the module before any run. Each has a **floor of five completed episodes**, the order's own count for item 31, below which **no rate prints** (needs-you 3):
- **ST-R5.31b, post-peak concentration:** PASS if, in at least 4 of every 5 completed episodes, the peak-day top ten fell 10% or more against the rest within 24 months of the peak.
- **ST-R5.44b, the drawdown gap:** a wide gap is 15 points or more. PASS if the leaders fell (the index's drawdown deepened by 5 points or more within six months) in at least 60% of completed episodes.

**The laptop's first editions** (public sources: SSGA's SPY file of 15 Oct, five years of Yahoo closes for its 503 members):

| Ledger | File | Now | Episodes | n (completed) | Verdict |
|---|---|---|---|---|---|
| ST-R5.31b | `docs/ledgers/st-r5.31b-ledger-2026-10-17.md` | top-10 share **40.2%** (back-cast) | 3 at or above 40% (peaks 29 Oct 2025, 14 May 2026, 7 Oct 2026) | **0** | **INSUFFICIENT**, no rate prints |
| ST-R5.44b | `docs/ledgers/st-r5.44b-ledger-2026-10-17.md` | gap **+15.7 points** (index −2.0%, average member −17.7%) | 3 at or above 15 points (May, Jul, Oct 2026) | **0** | **INSUFFICIENT**, no rate prints |

**What n allows: nothing yet.** Today's members back-cast over five years give three episodes each, none of them old enough to complete (24 months for 31b, six for 44b). The sourced comparisons print labelled and never as episodes of ours: BofA's six peaks for 31, and Raymond James's 3Q26 read for 44. The survivorship caveat is in each file. The box's re-run (below) supersedes each with a new dated file.

**Register lines, drafted under rule 31.** Items 31 and 44 have no register entries on any line yet, so I wrote none into the register:

```
ledger: docs/ledgers/st-r5.31b-ledger-2026-10-17.md, INSUFFICIENT (0 completed of 3 episodes; floor 5; top-10 share 40.2% now) -- laptop run, public sources
ledger: docs/ledgers/st-r5.44b-ledger-2026-10-17.md, INSUFFICIENT (0 completed of 3 episodes; floor 5; gap +15.7 pts now) -- laptop run, public sources
```

The queue entries 30c and 44c are not filed (ruling 1).

---

## Part 1: ST-3, ST-4 and ST-6

### ST-3: what was already built, and the one cut added

**Already built** (st-r5-rates, the rates attribution of 30 Sep, and the correlation layer):
- the attribution features, `calc.attr_*`, in both cuts (real/breakeven and curve) at 5, 20 and 60 observations: one week, one month, one quarter;
- the four models' shares (DKW, Kim-Wright, ACM);
- `calc.corr_spy_tlt_60d` and `calc.infl_vol`;
- the four model term premia, registered: ACM (`acm.*`), Kim-Wright (`fred.term_premium_kw`), DKW (`dkw.*`) and the SF Fed model (`sffed.*`);
- the descriptive block, `altdata/rates_attribution.py`, which carries the models' sign agreement.

Which of the four the box has actually stored after Friday's merges and Monday's chain is a box read (below); the laptop cannot see it.

**Added:** the third cut, **since the last FOMC decision**, as `calc.attr_d10y_since_fomc`, `calc.attr_real_share_since_fomc` and `calc.attr_curve_share_since_fomc`.
- **Base:** the close before the decision day, so the day's own reaction is in it.
- **Decision days:** the claims registry's (`cal.fomc_2026`, `cal.fomc_2027`), read by `events_ingest`'s own parser. Before the first registered decision there is no cut.
- **Registered,** and gated in `validate_st_t1_rest` C against hand figures (+18 bp, 0.6111, 1.0).

**Not built: the cell. A conflict for you (needs-you 1).** The paste asks for the `rates.driver` cell rules, persistence and trace in `config/market_state.yaml`, the `validate_regime` cell gates and a first edition of `tools/calibration/sr06_09_17_driver.py`. That cell failed its pre-registered gate twice (`docs/ledgers/rates-driver-2026-09.md` and `-2026-09-30-r2.md`) and **was withdrawn by the ruling of 30 Sep 2026**:
- config v1.11 and v1.12 are retired numbers;
- the script was deleted with the withdrawal (`920da70`);
- CLAUDE.md and `altdata/rates_attribution.py` both state it.

The paste quotes no ruling that reverses the withdrawal. Reinstating a withdrawn state in the market-state object is a structural change to the one regime, so I built none of it. The Monthly blocks say the cell is withdrawn and print the attribution's model agreement instead.

### ST-4: Duration Absorption and the rates flags

**G-30 first.** `treasury_auctions.result_time` takes TreasuryDirect's own `updatedTimestamp` as `available_at` when it falls on the auction day, marked `observed`. The fallback is 13:05 ET (`AVAILABLE_ET`). A timestamp on a later day is an edit, so it is not used. The 24 Sep 7-year is held at 13:03:20 ET in `validate_official_sources`.
- **B's field renames are not re-fixed.** `writer-fixes-1` merges Monday, and my change sits in other hunks; the trial merge is clean.
- **Rows already stored keep 13:00.** The writer refreshes only 45 days, so older rows are stamped minutes early for coupons, never late.

**G-31.** The SEP and FedWatch manual keys it renames no longer exist: the by-hand audit removed them (rule 30). Its purpose is served keylessly:
- **the SEP median dot:** FRED's **FEDTARMD**, "Percent", annual, each year's dot dated 1 Jan of that year, read off its page on 18 Oct. It is new in `FRED_SIGNAL_SERIES`, now 64 (166 pulled).
- **FedWatch's leg:** the stored fed funds futures path (`altdata/fed_funds.py`; G-4 is settled).

**The features.** `altdata/absorption.py` computes them; they ride `market_features.compute` after the correlation layer, never fatal. Each reconciles to a hand figure in `validate_st_t1_rest` D.

| Feature | Source | State |
|---|---|---|
| `calc.net_supply_1m`, `_12m`, `_12m_gdp` | `fiscaldata.mspd_net_marketable_issuance` less the month-end change in `fred.soma_treasuries` (TREAST, millions), over `fred.gdp_nominal` (G-14) | computes |
| `calc.net_supply_proj_12m` | needed `manual.cbo_deficit_path` | **not tracked** (rule 30) |
| `calc.priv_residual_12m` | net supply less the 12m change in `tic.official_holdings` + `tic.private_holdings` | computes |
| `calc.tic_official_12m`, `calc.tic_private_12m` | TIC holdings | computes |
| `calc.tic_official_share`, `calc.tic_custodial_share` | TIC holdings; the custodial centres UK, Belgium, Ireland, Luxembourg and Cayman (SR-27) | computes |
| `calc.foreign_ust_share_lt` | TIC flows lines 5 + 10 over line 3, 12 months (SR-26) | computes |
| `calc.abs_fragility` | SR-27's candidate rule, display only | computes |
| `calc.abs_stress` | G-32's rule per coupon auction: cover in its tenor's bottom decile twice in a row, or dealers over 20%; the trace is rebuilt by the block | computes |
| `calc.fed_mkt_gap_12m` | the futures-implied rate 12 months ahead less the FEDTARMD dot for the year-end nearest 12 months out, bp | computes |
| `calc.fed_mkt_gap_m1`, `_m2` | needed `manual.fed_signalled_direction` | **not tracked** (rule 30) |
| `calc.cred_stress` | the 12m leg (\|gap\| > 50 bp); the next-meeting leg needs the signalled direction | computes on the 12m leg; the other leg **not tracked** |
| `calc.pm_disagree_fed` | `prediction_markets`' venue-against-futures comparison, next meeting, the larger side in points | computes at the cutoff day only (the venues' history is weeks) |
| `calc.deanchor` | SR-24: 5y5y above its 2022 high for 20 sessions, and the CIE above its 2022 high or UMich 5–10y ≥ 3.5% for three months | computes |
| `calc.be5y5y_range_pos` | the 5y5y's percentile since 2010 | computes |
| `calc.producers_spot_ratio` | GUNR over DBC (G-15's producers proxy over the stored broad commodity basket) | computes; a note, no rights |
| `calc.aa_bbb_oas_diff` | FRED BBB less AA OAS, bp | computes |
| `calc.self_fund_ratio` | EDGAR XBRL frames: operating cash flow over capex, the five hyperscalers by calendar frame | computes when the box has filed frames; else **not stored** |
| `calc.hs_netdebt_12m` | EDGAR annual instant frames (`LongTermDebt`, else `LongTermDebtNoncurrent`; cash), year on year | as above |
| `calc.mu_inv_days` | EDGAR, Micron's company-concept files (`InventoryNet`; `CostOfGoodsAndServicesSold`, else `CostOfRevenue`) × 91 | as above |
| `calc.ai_long_share` | needed `manual.ig_issuance_10y_plus_share` and `manual.ai_ig_issuance_share` (G-35) | **not tracked** (rule 30) |
| `calc.cb_gold_12m` | `imf.ifs.gold_net_purchases_oz.total`, 12 months, in tonnes (G-34) | computes |

**The EDGAR additions.** Four new keys, read by `altdata/sources/edgar_xbrl.py` from `config/edgar_xbrl.yaml`:
- `edgar.xbrl_long_term_debt`, `edgar.xbrl_cash`, `edgar.xbrl_mu_inventory`, `edgar.xbrl_mu_cogs_q`;
- **cost:** the hyperscalers' year-end instant frames, plus two small Micron company-concept files, not a frame per quarter;
- **isolation:** a fault in them never costs the bridge's rows.

**Keys and rights.** The four not-tracked features are registered `not_yet_sourced` and never written, and no `manual.*` key is added. Every flag is display and modifier only, and none enters a composite.

### ST-6: the Monthly blocks

`daily_cascade/absorption_block.py`. In the Monthly's Plumbing & rates, after the GTM tables:
- **the Rate machine summary:** the driver line (withdrawn), the attribution's model agreement, DEANCHOR with the 5y5y's range position, CRED_STRESS with the 12m gap, the venues against the futures;
- **Duration Absorption:** 17 of its 18 lines; supply, absorbers, price and read.

In Slow layers, after the GTM tables:
- **Cheap-and-Unloved:** 10 of its 10 lines;
- **the Factor I, III, IV and V lines;**
- **the China panel's status lines,** with the assembly still deferred.

**What is unbuilt prints NOT AVAILABLE with its source.** Each line reads the store as of the cutoff and fetches nothing; a line without its input names the key and source. Much of Cheap-and-Unloved and the Factor IV lines rests on tranches not built yet:
- `calc.bond_alloc` and the `calc.val_z_*` strip (ST-8);
- the yen stack and the US–China spread (ST-5);
- the oil buffer.

**What they displace: nothing.** Each block is lines only: no paragraph asked, no chart, zero words in the budget (`validate_monthly` I).

**The first edition to carry them is the 23 Oct dry run.**

### Gates

**New in `tools/validate_st_t1_rest.py`** (it is in the Makefile; CLAUDE.md now counts ninety-four code gates, ninety-one Python):
- **A, B:** the two ledgers' hand figures, floors and pre-registered rules.
- **C:** the since-FOMC cut.
- **D:** each ST-4 feature against a hand figure.
- **E:** on an empty store nothing is written and every line names its key and source; the four not-tracked features are registered not_yet_sourced; the registry's `manual.*` metrics are the PMI alone; no network import; no store opened that the caller did not name.

**Extended:**
- **`validate_monthly` I:** the five blocks build with every HTTP helper raising; every line is populated or marked; the caps hold; zero words; placement.
- **`validate_official_sources`:** G-30, the 13:05 fallback, and the EDGAR outage path.
- **The count pins:** `validate_st_r5_t1_rest` (64/166), `validate_audit_3a` (FEDTARMD, the stale-count plant).

**Run locally, one at a time, only those this branch writes or changes:**

| Gate | Result |
|---|---|
| `validate_st_t1_rest` | 34/0 |
| `validate_monthly` | 355/0 (1 skipped, its own) |
| `validate_official_sources` | 291/0 |
| `validate_st_r5_t1_rest` | 103/0 |
| `validate_audit_3a` | 85/0 |
| `validate_gtm` | 77/0 |
| `check_registry` | OK |

**Left to CI:** `validate_regime` covers the three new `RATES_FEATURES` keys through its registry loop. Every other gate is CI's too.

**CI for this branch:**
- part 0 (`cd0bcd2`): **green**, 39095548260;
- part 1 (`18ec03d`): **failed**, 39096586909; these notes (`ac676f0`): **failed**, 39096734904. In both runs the same two checks of mine failed:
  - `validate_numeral_audit`: the 5y5y's percentile wrote "th" by hand (`absorption_block.py:124`). It now goes through `numeral_audit.ordinal()`.
  - `validate_by_hand_audit` A: dropped keys' literal ids appeared in code and config (`manual.cbo_deficit_path` in `absorption.py` and the registry). The not-tracked lines still name each key, by its bare id ("by-hand key cbo_deficit_path, dropped 16 Oct"), which no reader resolves. The other three keys got the same form.
- The fix commit follows these notes on this branch (18 Oct, read in st-t2-rates' step 0, whose notes carry its CI number). It also fixes `validate_stack` M's midnight fault. No other gate failed.

---

## Box commands, for the operator

Run these inside a window, after Thursday's merge: weekdays 09:05–15:40 or 17:20–23:30 ET, never 16:00–17:20; weekends are open, clear of Sunday 05:00. I ran none of them, and no unit is enabled or started.

```bash
cd ~/chester-reports && git pull --ff-only

# 1. FEDTARMD (the SEP median dot), first pull, then ALFRED's vintages:
.venv/bin/python -m altdata.feeds pull --only fred
.venv/bin/python -m altdata.fred_history backfill --series sep_median_ff --dry-run
.venv/bin/python -m altdata.fred_history backfill --series sep_median_ff

# 2. The EDGAR additions (PENDING without CHESTER_SEC_CONTACT):
.venv/bin/python -m altdata.sources.edgar_xbrl

# 3. ST-4's features over their whole history once (the features pass after
#    this keeps only its recompute window), then the attribution's since-FOMC cut:
.venv/bin/python -m altdata.absorption compute --dry-run
.venv/bin/python -m altdata.absorption compute
.venv/bin/python -m altdata.market_features compute

# 4. Which model term premia the store holds (ST-3's "registered where stored"):
.venv/bin/python -m altdata.catalogue show acm.term_premium_10y
.venv/bin/python -m altdata.catalogue show fred.term_premium_kw
.venv/bin/python -m altdata.catalogue show sffed.term_premium_10y
.venv/bin/python -m altdata.catalogue show dkw.real_term_premium_10y

# 5. The two ledgers against the store (each writes a new dated file that
#    supersedes the laptop's first edition; commit them from the laptop after
#    copying, or tell a session to):
.venv/bin/python -m altdata.ledgers.st_r5_31b --source store
.venv/bin/python -m altdata.ledgers.st_r5_44b --source store

# 6. The blocks as text, read-only, before the 23 Oct dry run:
.venv/bin/python -m altdata.absorption show
```

The 23 Oct Monthly dry run is yours, as always: `python -m monthly_macro.run --dry-run`.

---

## Files shared with the open branches

**`writer-fixes-1` (session B; merges Monday):**
- `altdata/sources/treasury_auctions.py`: my G-30 against its field renames. The read-only trial merge auto-merges this file.
- `tools/validate_official_sources.py`, `monthly_macro/stack.py`, `metrics_registry.yaml`, `Makefile`, `CLAUDE.md`.

The trial merge's only conflicts are CLAUDE.md and `tools/validate_batch3_a.py`, and the second is not this branch's file.

**`audit-leftovers-2` (session B):**
- `altdata/ledgers/__init__.py` and `sources.py`: byte-identical copies, no conflict.
- Also shared: `altdata/config.py`, `altdata/market_features.py`, `altdata/sources/treasury_auctions.py`, `config/catalogue_commands.yaml`, `metrics_registry.yaml`, `monthly_macro/stack.py`, `tools/validate_audit_3a.py`, `tools/validate_official_sources.py`, `Makefile`, `CLAUDE.md`.

The trial merge conflicts on CLAUDE.md, the Makefile, `metrics_registry.yaml` and the count pins. Those are the two chains' usual counts and lists, most of them predating this branch. The stitch recomputes:
- the gate count;
- `FRED_SIGNAL_SERIES` (64 here) and `FRED_PULL_SERIES` (166);
- the basket counts;
- `NEW_BLOCK_MEMBERS`.

B's ledger runner needs the two `ITEMS` lines for 31b and 44b.

**`alpha-lab-3`:** not on origin when checked, so nothing is shared yet. Nothing in `chester-meme`, Monday's chain, the decision register, the trade ledgers, `.env` or the box was touched.

---

## Needs you

1. **The rates driver cell.** The paste asks for it, and the ruling of 30 Sep withdrew it after two failed gates. Rule whether it comes back, and under which pre-registration, or whether ST-3 stays the descriptive attribution plus the since-FOMC cut, which is what is built. If it comes back:
   - the rules take v1.13;
   - the method takes method-11;
   - the calibration script must be restored from `920da70^`.
2. **The calibration ledger the row names** (rates-driver) has no first edition here, for the same reason. Its two editions stand, both FAIL.
3. **The ledgers' pre-registered rules and floors** (31b: 4 of 5 with a 10% relative fall in 24 months; 44b: 60% resolved by the leaders falling within six months; floors of five completed episodes). They are this first edition's, as the ruling allows. Accept them, or rule others before the box's re-run.
4. **The register lines above,** for items 31 and 44, if you accept them (rule 31). The register has no entries for Batch 6's items yet.
5. **G-31's next-meeting leg.** `calc.fed_mkt_gap_m1` and `_m2`, and CRED_STRESS's first leg, need the Fed's signalled direction. No keyless structured source within terms serves it. It stays not tracked unless you name one.
6. **`calc.ai_long_share`** (G-35) and **`calc.net_supply_proj_12m`** (CBO): not tracked under rule 30. The CBO debt path GTM-12 stores is not a deficit projection.
7. **The SEC contact on the box.** It is needed for the bridge and for ST-4's three EDGAR features.
8. **Pillar 8** still lists the interest burden as not yet sourced (from `gtm-core-2`). Still yours.
