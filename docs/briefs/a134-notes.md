# A134 notes: items 121 and 122, the forward TGA row and earnings quality

Paste A134, 7 Nov 2026, session A. Branch `a134-items-121-122` from `origin/main` at `ee04ba21`. The paste is `1a1b38ab`; the calibration ledger's pre-registered head, committed alone before the code that runs it, is `5240d51c`.

## The order

Batch 22 items 121 and 122 (the body's 103 and 104) and section 0's O-3, on `origin/b129-five-filings`.

## Item 121: the forward TGA-path row

**What prints.** One row in item 17's net-liquidity table and one line beneath it (Plumbing & rates, the Weekly and the Monthly through the same `plumbing_subsections`). For example, once a refunding read is stored:

> Forward TGA path (refunding of 2 Nov): TGA $922.752bn on 5 Nov (Daily Treasury Statement) to the assumed $850bn at 31 Dec = an implied reserve add of $73bn. Q1 2027 is the quarter to watch: the assumed $1.000tn at 31 Mar against $850bn implies a drain of $150bn.

Today, with no read stored:

> Forward TGA path: no refunding read stored; TGA … (Daily Treasury Statement). Q1 2027 is the quarter to watch (the borrowing estimate, the bills share, the RRP cushion left).

**The current TGA.** It comes from the Daily Treasury Statement, keyless, through the fiscaldata writer extended: `fiscaldata.dts_tga_close`, the operating-cash-balance line "Treasury General Account (TGA) Closing Balance", millions stored in dollars, daily.
- **The quirk.** Since the 2021 redesign the closing line carries its figure in `open_today_bal`, with `close_today_bal` served as "null".
- **History.** The line is served from 18 Apr 2022, 1,142 days to 5 Nov 2026.
- **Faults.** A DTS fault never fails the MSPD rows.

**The assumption.** It is the latest refunding's "assumed end-of-<month> cash balance", read only from the scans table, family `treasury-refunding`.
- **Who writes it.** The reading-shelf publication watch writes the scan; `docs/scans/PROMPT-treasury-refunding.md` gives its shape. The operator commits it and `altdata.scans ingest` stores it.
- **No by-hand line (rule 30).** No figure sits in code or config.
- **Before a read is stored.** The row prints "no refunding read stored". No scan is committed on this branch, because writing one here would be a by-hand entry, so the first print on the box says so until the watch's file lands.

**V-103a** (checked at build, 7 Nov 2026):

| Item | Result |
|---|---|
| The $1.040tn TGA on 29 Oct (secondary source) | **Confirmed against the DTS**: closing balance $1,040,236m on 29 Oct 2026. Then $951.6bn on 30 Oct and $922.8bn on 5 Nov. |
| The end-December assumption in the 2 Nov estimates | **$850bn, unchanged from August.** Treasury's "Marketable Borrowing Estimates" of 2 Nov 2026 (press release sb0675): "During the October–December 2026 quarter, Treasury expects to borrow $618 billion in privately-held net marketable debt, assuming an end-of-December cash balance of $850 billion." The order's ~$190bn release stands (1,040.2 less 850 = $190.2bn from 29 Oct); from 5 Nov's $922.8bn the remaining add is about $73bn. |
| January–March 2027 (the quarter to watch) | $800bn privately held, "assuming an end-of-March cash balance of $1.000 trillion": a $150bn rebuild, a drain. |
| The current RRP balance | Not re-read here. It is item 17's own leg (`fred.rrp`) and prints in the same table. |

The 2 Nov statement's figures are recorded here as the verification only; they reach the report when the reading-shelf watch writes its scan.

## Item 122: earnings quality

**V-104a** (checked at build, 7 Nov 2026):
- **BEA domestic nonfinancial profits.** The FRED id is `A463RC1Q027SBEA`, "Corporate profits with inventory valuation and capital consumption adjustments: Domestic industries: Nonfinancial", billions SAAR, quarterly from 1947. It joins the pull as `fred.profits_domestic_nonfin`, beside `fred.cpatax` (CPATAX); this is FRED_ITEM122_SERIES, so FRED_PULL_SERIES goes from 286 to 288. Lens 18's `fred.corp_profits_after_tax` (CP, without the adjustments) is unchanged.
- **S&P operating EPS.** No keyless source:
  - S&P DJI's EPS file was withdrawn on 17 Oct 2026, and its old link answers 403 (probed 7 Nov).
  - The stack's earnings chain reads Shiller's trailing twelve-month EPS, which is **as reported**, not operating. The line uses it and says so: "S&P EPS (Shiller, trailing twelve months, as reported; operating EPS not tracked)".
- **For the record: Econovis's series.** Not established from the chart. Its ~6% profits-to-market-cap level implies a pre-tax measure that includes receipts from abroad (the order's own note); not checked further.

**What prints** (Monthly only, in "What's carrying the index", the earnings chain): the quarter's growth on the year of the three series, the gap EPS less each NIPA leg in points, and the flag line.

**The flag.** EPS growth at least the margin above CPATAX growth, two quarters running. The flag decides nothing.

**O-3, the calibration** (`tools/calibration/earnings_quality.py`, public sources, never the store; ledger `docs/ledgers/earnings-quality-calibration-2026-11.md` with its CSV):
- **The head.** It was committed alone in `5240d51c`. Rule SHA-256 `30174e18250c5c1cc3d85c82914ccae94348505b3170d008d23cfca4739aa8f9`, held in `config/earnings_quality.yaml`.
- **Disclosure.** Before writing the head the session made one exploratory read of the public series at a handful of whole margins (5 to 30) on CPATAX and the nonfinancial leg. The head says so. The selection rule — the admissible margin with the fewest false-positive episodes, 10 points if tied or none — was then fixed, and the run applied it unchanged.
- **The result: 15 points**, not ambiguous.
  - **Admissible margins:** 5 through 15, which fire in both 1999-2000 and 2006-07.
  - **The minimum:** 15 has the fewest false-positive episodes (4), uniquely.
  - **False positives since 1990: 4 episodes:** 1995Q1–Q2, 2004Q1–Q3, 2010Q1–2011Q3, 2021Q4–2022Q2. All are recovery rebounds of reported EPS off write-down-depressed troughs, which NIPA excludes.
- **The knife edge.** At 15, the 2006-07 target fires on one quarter only, 2007Q2 (gaps of 21.3 and 15.3 points), and 16 points loses it. Read the 15 with that in mind.
- **Beside it, never selecting:** the nonfinancial leg at 15 catches 1999-2000 but not 2006-07, with 5 false positives.
- **The latest quarter, from the public data:** 2026Q2 gap 14.6 points, 2026Q1 11.0 points. The flag is off at 15 and would be on at 10.

## Settings

| Setting | Where | Value |
|---|---|---|
| forward_tga key, family, pattern, watch quarter, stale days | `config/batch5_tranche_1.yaml` `net_liquidity.forward_tga` | `fiscaldata.dts_tga_close`, `treasury-refunding`, the "Assumed end-of-<Month> <YYYY> cash balance" pattern, 2027-03-31 ("Q1 2027"), 7 |
| keys, EPS label, margin, calibration | `config/earnings_quality.yaml` | CPATAX, A463RC1Q027SBEA, Shiller; 15 points; the rule SHA, targets, 1990Q1, 5–30, 10 if ambiguous |

## Registry and counts

- **Registered:**
  - `fiscaldata.dts_tga_close` (usd, daily, quantity, full window);
  - the `fred_item122` block (CPATAX and A463RC1Q027SBEA, family release);
  - a `market_state_barred` entry for the two legs and `calc.earnings_quality_*` (no such key is stored; the flag computes at read).
- **The count gates:** `validate_audit_3a`'s block list gains `fred_item122`, and `validate_st_r5_t1_rest`'s pull count reads 288.
- **The new gate:** `tools/validate_items_121_122.py` (code, clock pinned). `stitch_counts --write` moved the counts by one.
- **Master Guide:** Table 7a carries the new ledger.

## Gates (one at a time, foreground)

| Gate | Result |
|---|---|
| validate_items_121_122 (new) | 43/0 |
| validate_st_r4_t1 (item 17's block) | 49/0 |
| validate_releases_b (the GDP lenses) | 76/0 |
| validate_monthly_stack (run whole: its groups are letters, none named for the earnings chain) | 268/0 |
| check_registry | OK |
| validate_gates | 32/0 |
| check_library | 27 papers, 0 failures, 0 warnings |

Also run, all clean:
- validate_audit_3a 88/0, validate_st_r5_t1_rest 103/0 (both count pins moved), check_master_guide 14/0;
- validate_weekly_edits 91/0, validate_weekly_stack 83/0, validate_lenses 49/0;
- validate_config_refs 148/0, validate_stitch_tools 21/0, validate_st_t5_render 46/0;
- validate_regime 524/0, validate_secrets 58/0;
- `stitch_counts --check`: 63 counts, 0 disagree.

## Box steps

None required. The fiscaldata writer backfills the DTS line on its next run, and the FRED pull picks up the two new series on its next run. The forward row prints "no refunding read stored" until the reading-shelf watch's `treasury-refunding-2026q4.md` is committed and ingested.
