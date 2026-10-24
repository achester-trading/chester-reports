# a58-batch15-1: signal triage Batch 15, session A's items 72, 73 and 76 (23 Oct 2026)

**What it is.** The filing of the Batch 15 order (items 72 to 78, ruled 20 and 23 Oct 2026, filing amendments G1 to G6 ruled 23 Oct 19:13 ET) and the build of three of its items:
- **Item 72** (written as 65): institutional gold-ETF ownership (13F) and WGC flows;
- **Item 73** (written as 66): the gold event trigger and the developed-market drawdown screen;
- **Item 76** (written as 69): the CDS protection-demand line.

Section 0 governs, and items are cited by their filed numbers. Items 74, 75, 77 and 78 are session B's (b56-batch15-2) and are not touched here.

**THIS BRANCH MERGES AFTER THE 1 NOV MONTHLY, whatever its CI says (G4).** CI: see "The CI run" below.

## Base and boundaries

- **Base:** `a58-batch15-1` was cut from **origin/chain-5 at `6fa2024`**. Then **origin/a57-batch14-b1 at `711631b`** was merged into it in one merge commit (`19d1c03`), because 76 builds on a57's AI-credit gap line and 73 on its event-ledger shape.
- **The merge's conflicts** were count lines and appended lists, resolved as unions:
  - the basket: 126 symbols (chain-5's 124 plus AIQ and SPXT);
  - 106 volume units and the shares block at 96;
  - 281 FRED series;
  - 134 code gates;
  - the Security Master's `next_id` 215 (a57 had left SM00205 to SM00212 to b52);
  - the Makefile, the source tiers and the voices list: both sides kept;
  - the Master Guide's Table 7a: both rows;
  - `master-guide.html`: rebuilt with the builder, not hunk-resolved.
- **Its own checkout:** `../chester-a57`. Another session uses the main checkout.
- **Branch only:** pushed, not merged, not deployed. Nothing was run on the box, no unit was touched, nothing was written to the register, and no secret or `.env` was read.
- **b56-batch15-2 and b55-batch14-b2** were not on origin when checked (23 Oct, late evening).

## The commits

| Commit | What |
|---|---|
| `19d1c03` | The merge of a57-batch14-b1 onto chain-5 |
| `48caa51` | Part 0: the order, filed byte for byte and committed alone (SHA-256 `d5318a6d…4e25`, identical to the operator's download) |
| `fda2489` | Part 0: the index lines, in `docs/change-orders.md` after Batch 14 and in the register's header |
| `cf7aff9` | Parts 2 to 4: items 72, 73 and 76, their registration, the hooks, the dated records |
| `4e5a8af` | Part 5: the gate, the Makefile, CLAUDE.md |
| (this commit) | These notes |

## Part 1: the source checks (G5; run 23 Oct 2026 from the laptop, before building)

| # | Check | Result |
|---|---|---|
| 1a | **EDGAR's Form 13F data sets (item 72)** | **Passes.** <br>• **Keyless:** the data-sets page lists direct zip links and asks for no login or key. <br>• **Coverage:** "July 2013 – August 2026", from `2013q2_form13f.zip` to `01jun2026-31aug2026_form13f.zip`, so about 53 quarters back. Since March 2024 each file covers three months of filings, ending in February, May, August or November. <br>• **Layout:** tab-separated tables in each zip. SUBMISSION carries the accession, filing date, type, CIK and period; COVERPAGE the amendment flag and type; INFOTABLE the CUSIP, VALUE, shares, share type and put/call. VALUE is dollars from 3 Jan 2023 and thousands before. <br>• **The count:** holders by CUSIP and their values can be counted per quarter. GLD is 78463V107. IAU is 464285204 (the issuer's page), and 464285105 is IAU's CUSIP as aggregators show it for filings before its May 2021 consolidation. <br>• **What the laptop could not do:** read the page directly. sec.gov answers a client without a contact in its User-Agent with 403, and `CHESTER_SEC_CONTACT` is the box's, so it was not used here. The page was read through a fetch tool, and the readme PDF did not text-extract on the laptop. So the column names are coded as the data sets document them, and **the reader refuses a file whose headers differ**; the box's first `load` is the live check |
| 1b | **WGC's gold-ETF flows and central-bank data (item 72, G5)** | **Fails: a listed gap.** <br>• **robots.txt** (www.gold.org) disallows only `/core/` and `/profiles/`. <br>• **But the files are gated.** The flows page's `ETF_Flows_2026-10-02_1401.xlsx` and the reserves page's two IFS workbooks are each marked `private`, and each answers HTTP 403 without a login; the page asks the reader to agree to its terms first. <br>• **Terms:** use is personal and non-commercial, and scraping is forbidden. <br>• **So:** WGC's regional flows are not tracked. The central-bank trend reads the IMF IFS series the system already stores (WGC's own source); see "Where the order and the code differ", 3 |
| 2 | **A keyless daily close for the seven indices (item 73)** | **Nikkei 225: passes.** FRED `NIKKEI225` (keyless graph CSV), daily from 1949-05-16 to 2026-10-23. <br>**KOSPI and TAIEX: ETF proxy.** The store already holds EWY and EWT (SR-46's basket), labelled "ETF proxy". <br>**TOPIX, DAX, CAC 40, FTSE 100: listed gaps.** FRED carries no series for them, and the store holds no country ETF for Japan beyond the Nikkei's own series, or for Germany, France or the UK. <br>**The gold series:** `yfinance.mkt_gold_front` (GC=F), the one item 38 and AQ-8a read |
| 3 | **Verify items 1 and 2 (item 73)** | **Gold:** GC=F's one-day falls of more than 3% since August are **-3.54% on 28 Sep 2026** (4,168.4); the next largest was -2.88% on 28 Aug, and -2.16% on 22 Oct. The post gives no date, so the 28 Sep fall is the match on the series, recorded and not asserted. <br>**Nikkei: mismatch, recorded.** FRED's closes never reach 61,825: the lowest recent close is **62,693.16 on 23 Oct**. The peak was 70,683.98 on 6 Oct, so the fall to 23 Oct is **-11.3% over 13 sessions**, not -13% over 16. No session closed -1.72%: 22 Oct was -2.65% and 23 Oct -0.34%. The post's level may be intraday or another day's close. **The screen built here fires on the Nikkei from 15 Oct** (FRED's series on the laptop): 11.3% from its 20-session high on 23 Oct, against a 95th percentile of 8.58% on five years |
| 4 | **DTCC's public weekly single-name CDS data (item 76; verify item 5)** | **Fails the standing rule: a listed gap.** <br>• **No public per-name report.** DTCC's public "Market & Index Data" page (`/repository-otc-data` redirects there) lists equity, ETF, repo, Treasury-fails and the regulators' GTR aggregates, and no weekly per-name CDS report. The Trade Information Warehouse's per-reference-entity data is now **CDS Kinetics, sold "to subscribers"**. <br>• **The SEC SBSDR public dashboard** (`pddata.dtcc.com/ppd/secdashboard`) is trade-level dissemination with capped notionals, not the weekly per-name volume the order means. <br>• **Terms** (`www.dtcc.com/terms`): "you may not use any automated device, computer program, tool, algorithm, bot or similar process to mine or systematically scrape or extract data from the DTCC Site". <br>• **So** which of the seven names and CoreWeave DTCC lists, and how deep its history goes, cannot be verified from a public page: verify item 5 is unanswered, and recorded so |

## Part 2: item 72, institutional gold-ETF ownership (`altdata/gold_13f.py`, `config/gold_13f.yaml`)

- **Item 51's 13F pipeline is not built in this repo.** No module reads 13F data, and item 51's addendum has no holder data. This is the minimal reader of the same data sets, written so item 51's can share it.
- **The line**, under Factor V in the Monthly's slow layers, right after item 38's gold/equity ratio:
  - per calendar quarter, the count of 13F filers holding GLD, IAU and either fund;
  - the value they report;
  - the change from the prior quarter;
  - with the 13F caveat (US-listed long positions of $100m+ managers, 45 days late).
- **Prose read first.** Item 38's slow-layer sub-section asks for no paragraph, and this one asks for none either, so no prose word is added.
- **The count:**
  - a filer's quarter is its latest original or RESTATEMENT report, plus the NEW HOLDINGS amendments filed after it;
  - share positions only: no options, no principal amounts, no 13F-NT;
  - VALUE in thousands is scaled to dollars for filings before 3 Jan 2023.
- **A quarter is written only when complete in the files read:** from the day after its end through its 45-day deadline. A later load restates it as a new vintage.
- **The store:** `sec13f.gold_etf_holders` and `sec13f.gold_etf_value_usd`, with instrument GLD, IAU or BOTH.
- **The box's commands:**
  - `fetch` reads robots.txt and the data-sets page, then saves zips to `~/chester-data/inbox/sec13f`. It identifies itself only through `edgar.user_agent()` (`CHESTER_SEC_CONTACT`) and refuses without it; no address is written anywhere;
  - `load` counts and stores;
  - there is no timer (status `built` in `source_registry.yaml`).
- **WGC's regional flows** print as a listed gap beside the line (check 1b).
- **The single-filer chart** the item came from is not a line, and no filer is named.
- **The voices entry** (the order's ruling 1) stays out, pending A56's needs-you item 2 (G6). Listed, not built.

## Part 3: item 73

### The gold event (ST-R6.73a; `altdata/gold_event.py`, `config/gold_event.yaml`)

- **The trigger (ruled):** gold's one-day move of ±2.5% or more, or its five-day move beyond its 95th percentile.
  - The five-day move is a log change, two-sided.
  - Its percentile is the nearest rank over the five years of sessions before the day: **a57's flag window**, the shorter of the dual windows.
  - With under 252 prior five-day changes, the arm is "not read", with its count.
- **The attribution**, over the trigger's horizon (one session for the one-day arm, else five):

  | Leg | How it is read |
  |---|---|
  | Real 10-year | `fred.tips_10y`, DFII10, in bp |
  | DXY | `yfinance.mkt_dxy`, DX-Y.NYB, the stored series, in % |
  | Brent | `fred.brent`, in % |
  | Gold-ETF flows | "not tracked": item 72's WGC line does not exist |
  | Central-bank trend | the stored IMF IFS net purchases, the 12 months against the 12 before, in tonnes |
  | Residual | one line: how many read legs moved the way the order's mechanism ties to the move's sign (oil, real yields and the dollar up, gold down). No leg is fitted, so the rest is "not attributed" |

  A leg whose input for the day is not stored yet is "awaiting", with how far it is stored. FRED posts DFII10 and Brent after the close.
- **The ledger:** `gold.event_ledger` (instrument = the day). It holds the trigger, the legs and gold's realised 5- and 20-session change.
  - The close stores a row on a fired day, never on a dry run.
  - `resolve`, in the EOD pass after the speed attribution's, writes new vintages as the legs and outcomes land.

### The developed-market drawdown screen (ST-R6.73b; `altdata/dm_drawdown.py`, `config/dm_drawdown.yaml`)

- **Item 10's shock screen** is SR-46's EM screen in `altdata/move_screen.py`. The DM screen is a sibling module on the same conventions; the EM screen's code is not edited.
- **The trigger (ruled):** the 10- or 20-session drawdown beyond its 95th percentile.
  - The drawdown is the close's fall from the window's highest close.
  - Its percentile is the nearest rank over the five years before the day (a57's window).
  - With under 500 prior drawdowns (the move screen's rule), the window is "not read".
- **The indices:** Nikkei 225 (FRED); KOSPI and TAIEX (ETF proxies). TOPIX, DAX, CAC 40 and FTSE 100 print as listed gaps by name, on every block.
- **The attribution,** over the window that fired:
  - the local currency: USD/JPY from Yahoo; USD/KRW and USD/TWD from FRED's H.10. For a proxy it is inside the fund's dollar return, and the table says so;
  - the local 10-year: the JGB 10-year (MoF, daily). Korea's is stored only as the OECD monthly average and Taiwan has none, so both are "not tracked";
  - the prior US session's S&P 500 move;
  - for Japan, the yen carry stack (SR-2: `calc.jpy_unwind`, `calc.jp_front_diff_60d`, `calc.jp_hedged_carry`, as stored) and SR-32's stored early line (the 30-year JGB; the `jp.slowmoney` family is a stub);
  - for KOSPI and TAIEX, item 63's capex-chain line (`capex_chain.relative`).
- **The ledger:** `equity.dm_drawdown_ledger` (instrument = "index:day"), with the same close, `resolve` and outcomes as the gold ledger.

### Where both print, and the first editions

- **Where they print:**
  - **the close:** the flag lines only, in the event area of Mechanics after item 52's and item 65's events;
  - **the Weekly and the Monthly:** each screen's block over the edition's sessions (a table of fired days, or one line saying none fired), with the gaps listed.
- **Flags only.** No composite, no market-state import; the gate checks the imports.
- **The first editions are from stored history only:**
  - `python -m altdata.gold_event history` and `python -m altdata.dm_drawdown history` read every stored day with only what came before it;
  - a row whose window is shorter than five years, or whose arm is not read, says so in `history_note`;
  - `--out` writes the edition outside the checkout, and `--write` stores the rows.
- **They were not run here.** The laptop holds no observation store with these series, and the box is the operator's (needs-you 2). The laptop run on FRED's CSV (check 3) is a smoke test, not an edition: 1,299 fired Nikkei days since 1949, with the history pass taking 12 seconds.

## Part 4: item 76

- **Check 4 failed**, so all of item 76 is a listed gap except the dated records. That covers the protection-demand line, its dual percentiles and the flag. No module, key or source id for DTCC exists.
- **G3, the dated records:** `docs/dated-appendix-queue.md`, "For the AI-credit watch and SR-16". It holds two records, each with a source line, an as-of date and "URL: not filed in the order" (the order gives none, and none is invented):
  - the five CDS levels and the 4.5x volume rise, as of mid-October and September 2026;
  - the $466bn against $101bn of year-to-date AI borrowing, as of 20 Oct 2026.

  The monthly rows are a listed gap.
- **a57's AI-credit gap line** (`absorption_block.AI_CREDIT_LINE` and `config/ai_trade.yaml`) now ends by naming item 76's gap and the dated records.

## Part 5: the gate

- **`tools/validate_batch15_1.py`:** 70 checks, groups A to H, on synthetic fixtures only (no network, no live store, no model):
  - **(A)** the filed order at its SHA-256, and both index lines;
  - **(B)** a fixture data set counted by hand:
    - a RESTATEMENT replacing, a NEW HOLDINGS adding;
    - an option, a principal amount and a 13F-NT excluded;
    - IAU's earlier CUSIP;
    - the thousands rule;
    - a partial quarter not written, a changed layout refused;
    - the change from the prior quarter through a store round-trip;
    - the absent path, and WGC's gap;
  - **(C)** the gold trigger on both arms, with the five-day threshold by hand:
    - the legs by hand: +15 bp, -1.00%, Brent "awaiting";
    - ETF flows "not tracked";
    - the IFS trend by hand, and absent on short history;
    - the residual's count;
    - the ledger row's 5-session outcome by hand, and `resolve`'s new vintage;
    - the history pass's short-history note;
  - **(D)** the drawdown and its percentile by hand:
    - a short-history index not read;
    - the four gaps by name, the proxy labels, the not-tracked 10-years;
    - Japan's legs by hand;
    - the ledger row;
  - **(E)** item 76's whole-item gap (no DTCC key or module), the amended line, both dated records;
  - **(F)** placement:
    - the close's lines after item 52's event, and its rows only off a dry run;
    - the Weekly's and Monthly's blocks;
    - item 72 after item 38;
    - the EOD resolve;
  - **(G)** every new key, block, source and command; NIKKEI225 in the pull; no Brookfield instrument;
  - **(H)** no person's name, handle or address in the new files or the appendix records; no composite, market-state, register or order import; the live store untouched.
- **What the gate does not cover.** The brief's "protection-demand percentiles by hand, the flag true/false" has nothing to test, because check 4 failed. Group E holds the gap path instead.
- **The count:** on chain-5 plus a57, **134 code gates** (131 Python, three shell). With this gate, **135** (132 Python, three shell), and eight data gates. CLAUDE.md's line and the Makefile say so.
- **Run locally, one at a time:**
  - `validate_batch15_1` 70/0;
  - `validate_vol_event` 50/0;
  - `check_registry` OK;
  - `check_library` 0 failures, 0 warnings;
  - `validate_official_sources` 340/0;
  - and, because this branch changes their pins, `validate_st_r5_t1_rest` 103/0 (FRED_PULL_SERIES 281 to 282), `validate_audit_3a` 88/0 (the new FRED block) and `validate_batch14_b1` 67/0 (the amended line).
- **Left to CI:** every other gate, the stack renders among them (the close, the Weekly and the Monthly gained hooks).

## The CI run

| Run | On | Result |
|---|---|---|
| (filled below) | | |

## Every listed gap

1. **WGC's gold-ETF flows by region** (item 72): login-gated, with terms for personal use only. The gold event's ETF-flow leg is "not tracked" for the same reason.
2. **WGC's central-bank purchase file** (item 72; check 1b): login-gated. The stored IMF IFS series stands in (WGC's own source).
3. **TOPIX, DAX, CAC 40 and FTSE 100** (item 73): no keyless daily close (check 2).
4. **Korea's and Taiwan's 10-year at a session horizon** (item 73): Korea's OECD monthly average only; Taiwan none.
5. **Item 76's protection-demand line and its flag:** DTCC's per-name CDS volumes are a subscription product, and its terms forbid automated extraction (check 4).
6. **Item 76's monthly CDS-level and borrowing rows** (G3): no recurring by-hand line.
7. **The voices entry of item 72's ruling 1** (G6): out, pending A56's needs-you item 2.
8. **SR-32's slow-money family** is a stub. The Japan attribution reads its stored early line (the 30-year JGB) and says so.

## Every session-set value, with its reason

| Value | Setting | Reason |
|---|---|---|
| The percentile window, both screens | five years of sessions before the day, nearest rank | a57's flag window; a rank a gate can do by hand |
| The gold five-day move | log change, two-sided | item 52's reading of the VIX's five-day change |
| The gold five-day arm's minimum | 252 prior changes | one year of sessions |
| The DM screen's minimum | 500 prior drawdowns | the move screen's rule |
| The drawdown | the close against the window's highest close, that many sessions back and the day | the plain reading of an N-session drawdown |
| The lead DM window | the longer when both fire | the larger move |
| The attribution horizon | the trigger's (one or five sessions; the DM window) | the move being explained |
| A leg's start tolerance | four calendar days | a57's; a long weekend, Brent's UK holidays |
| The central-bank trend | 12 months against the 12 before | a year smooths the IFS reporting gaps |
| The residual line | a count of the legs moving the mechanism's way; nothing fitted | the order asks for one line, and no weights are ruled |
| The ledgers' outcomes | the asset's change over 5 and 20 sessions, % | item 52's and a57's forward sessions |
| The 13F completeness rule | files covering a quarter's end through its 45-day deadline | a partial quarter would understate the count |
| The 13F amendment rule | the latest original or restatement, plus later NEW HOLDINGS | how the data sets mark amendments |
| IAU's earlier CUSIP | 464285105 counted as IAU | the May 2021 consolidation changed it |
| The 13F fetch pause | 2 seconds a file | far inside the SEC's ten requests a second |

## Each new key, its source and its real publication lag (for b51's `config/publication_lags.yaml`)

| Key | Source | Cadence | Publication | Lag to add |
|---|---|---|---|---|
| `fred.nikkei225` | FRED `NIKKEI225` | daily | FRED posts the Tokyo close the same US day or the next | none new: b51's FRED daily family covers it |
| `sec13f.gold_etf_holders`, `sec13f.gold_etf_value_usd` | SEC's 13F data sets | quarterly, dated the quarter end | filings 45 days after the quarter; the data set some weeks later | **new:** about 75 days from the quarter end to the data set; the load's instant stands in |
| `gold.event_ledger`, `equity.dm_drawdown_ledger` | this system, the close and the EOD resolve | event | written the fired day; later vintages as inputs land | none (event ledgers) |

## The box commands (the operator's; inside the windows; after the merge, which is after the 1 Nov Monthly)

```
cd ~/chester-reports
# NIKKEI225: nothing to run. The 16:10 FRED pull takes its full history at its next run.
# Item 72: the 13F data sets (needs CHESTER_SEC_CONTACT, already the EDGAR writer's):
.venv/bin/python -m altdata.gold_13f fetch --files 9 --dry-run
.venv/bin/python -m altdata.gold_13f fetch --files 9
.venv/bin/python -m altdata.gold_13f load ~/chester-data/inbox/sec13f/*.zip --dry-run
.venv/bin/python -m altdata.gold_13f load ~/chester-data/inbox/sec13f/*.zip
.venv/bin/python -m altdata.gold_13f show
# Item 73: the first editions, from the store only, written OUTSIDE the checkout:
mkdir -p ~/chester-data/ledgers
.venv/bin/python -m altdata.gold_event history --out ~/chester-data/ledgers/st-r6.73a-first-edition.md
.venv/bin/python -m altdata.dm_drawdown history --out ~/chester-data/ledgers/st-r6.73b-first-edition.md
# ... and, once read, store them as the ledgers' first rows:
.venv/bin/python -m altdata.gold_event history --write
.venv/bin/python -m altdata.dm_drawdown history --write
.venv/bin/python -m altdata.gold_event show
.venv/bin/python -m altdata.dm_drawdown show
```

- **Expect:**
  - `fetch --dry-run` lists the nine newest zips, or refuses without the contact;
  - `load --dry-run` prints each quarter's filers, marking the partial ones;
  - the history editions list every fired day, with a note where the history is short.
- **The EOD pass** resolves both ledgers from the next pull of main after the merge. No unit changes.

## Files shared with other branches

| Branch | Files |
|---|---|
| a57-batch14-b1 | merged in, so every a57 file is here. This branch changes, after the merge: `CLAUDE.md`, `Makefile`, `daily_cascade/absorption_block.py` and `config/ai_trade.yaml` (the AI-credit line), `daily_cascade/stack.py`, `stack_close.py`, `weekly_stack.py`, `monthly_macro/stack.py` (one hook each, after a57's), `scripts/run_eod_cron.sh` (after a57's resolve), `metrics_registry.yaml`, `source_registry.yaml`, `config/catalogue_commands.yaml`, `altdata/config.py`, `tools/validate_audit_3a.py` |
| chain-5 | the base. Besides the rows above: `docs/chester-reports-architecture-v3.md` (282 FRED series), `docs/change-orders.md`, `docs/signal-triage-register.md` (the header), `docs/dated-appendix-queue.md`, `tools/validate_st_r5_t1_rest.py` (282) |
| b56-batch15-2 | not on origin when checked. It reads the same filed order. Expect overlap in `CLAUDE.md` (the count line and a paragraph), the `Makefile`, `metrics_registry.yaml`, `source_registry.yaml`, `config/catalogue_commands.yaml`, `docs/dated-appendix-queue.md` (its 74 and 75 records), and probably the stack hooks. If b56 also adds a FRED series, `FRED_PULL_SERIES`' pins (`CLAUDE.md`, the architecture document, `validate_st_r5_t1_rest`) |
| b55-batch14-b2 | not on origin when checked. Expect `CLAUDE.md`, the `Makefile`, `metrics_registry.yaml` and the Master Guide's Table 7a |

The new files are this branch's alone: `altdata/gold_13f.py`, `gold_event.py`, `dm_drawdown.py`, `asset_event.py`, `daily_cascade/batch15_a_block.py`, the three configs and the gate.

## Where the order and the code differ

1. **"Extend item 10."** Item 10's shock screen is SR-46's EM screen in `move_screen.py`. The DM screen is a sibling module on its conventions, not an edit of the EM screen, so the EM screen's stored results and its gates are unchanged.
2. **"Gold-ETF flows (WGC, item 72)" in the attribution:** "not tracked" (check 1b).
3. **"The central-bank purchase trend (WGC, quarterly)".** WGC's file failed check 1b, and the brief says "not tracked" in that case. The system already stores the IMF IFS series WGC's own file is built from (`imf.ifs.gold_net_purchases_oz.total`), so the leg reads that, labelled IMF IFS. No new vendor. If the operator wants the literal reading, it is one config line (needs-you 4).
4. **The residual "one line".** No regression is ruled, so the line counts the read legs that moved the mechanism's way and attributes the rest to nothing.
5. **"Nikkei 225 at 61,825, down 13% in 16 sessions".** FRED shows 62,693 and -11.3% over 13 sessions to 23 Oct (check 3). This is recorded, not corrected; the screen fires on the series as it is.
6. **"10y yields" for Korea and Taiwan:** not tracked at a session horizon (a monthly average only, or none).
7. **"The JGB/slow-money family" for Japan:** `jp.slowmoney` is a stub. Its stored early line, the 30-year JGB, is read and labelled.
8. **"DTCC publishes weekly single-name CDS volumes for free".** It no longer does on a public page (check 4). The line, its percentiles and the flag are a listed gap.
9. **"Shares item 51's 13F pipeline".** Item 51's pipeline is not built; this is the minimal reader of the same data sets.
10. **"WGC monthly gold-ETF flows by region"** (item 72's ruling 3): a listed gap (check 1b).
11. **Item 72's placement "Metals paper appendix; voices"**: neither is written here. The Monthly's slow layer is the line; the voices entry waits (G6).
12. **Item 76's placement "positioning & flows".** Only the gap line prints (in Factor I's credit lines), since there is no line to place.

## Needs you (at most five; yes or no each)

1. **The merge: after the 1 Nov Monthly, whatever CI says?** First chain-5 and a57 onto main, then this branch, recounting the gate line and the FRED pins against whatever lands between (b56 above all). Yes / no.
2. **The box commands above, after the merge?** The 13F fetch and load (it uses the existing `CHESTER_SEC_CONTACT`), and the two first editions written outside the checkout, then `--write`. Yes / no.
3. **The SEC SBSDR dashboard for item 76.** Should a session check whether DTCC's public security-based swap dissemination (`pddata.dtcc.com`) can give a weekly per-name traded notional within its terms, as a new source check? Until then, item 76 stays a listed gap. Yes / no.
4. **The central-bank leg reading the stored IMF IFS series,** rather than printing "not tracked" because WGC failed. Keep? Yes / no.
5. **The session-set values above,** above all the five-year percentile windows, the 500-observation minimum and the residual line's form. Confirm? Yes / no.
