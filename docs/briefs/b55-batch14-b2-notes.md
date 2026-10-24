# b55-batch14-b2: signal triage Batch 14, Part B2 -- items 62, 67 and 68 (session B, 23 Oct 2026)

**What it is.** Three of Part B's items from the Batch 14 order (ruled 20 Oct 2026 with filing amendments F1 to F8). Part B **merges after the 1 Nov Monthly**, whatever CI says (F8).
- **Item 62** (written as 55): the cross-house CMA table, through the reading shelf;
- **Item 67** (written as 60): the PEG/LTEG gap line, the base-rate note and the narrative entry;
- **Item 68** (written as 61): the per-household pending-sales line.

Section 0 governs, and items are cited by their filed numbers.

## Base and boundaries

**Base.** `b55-batch14-b2` was cut from **`origin/chain-5` at `6fa2024`** ("chain-5: the stitch notes name a57-batch14-b1 as outside this chain"), which had not moved when checked (23 Oct, about 21:00 ET). The gate count is recounted on that base.
- **Its own checkout:** `../chester-reports-t3`, which was on chain-5 and clean.
- **Branch only:** pushed, not merged, not deployed. Nothing was run on the box and no unit was touched. No register write, no `.env`, no secret.
- **Read only:** a57-batch14-b1 (`711631b`) and a58-batch15-1 (session A's, tonight). chester-meme was not opened.
- **Not touched:** items 65 and 71 (session A's, on a57), the order's filing and its indexes.
- **The specification** is `docs/change-order-signal-triage-batch-14-2026-10-20.md` on chain-5. Where it and the code differ, the code wins; every difference is listed below.

## Commits

| Commit | What |
|---|---|
| (first) | Items 62, 67 and 68, the gate, its fixtures, the counts and these notes |

## Part 0: the source checks (run 23 Oct 2026, from the laptop, before building)

| # | Check | Result |
|---|---|---|
| 1a | **HSBC AM's Capital Market Assumptions** (62): page, robots.txt, terms, cadence | **Passes for the shelf.** <br>• **Page:** one page per edition, its month and year in its name: `www.assetmanagement.hsbc.co.uk/en/institutional-investor/news-and-insights/capital-market-assumptions-october-2026` (HTTP 200; the "third edition", 9 Oct 2026). The October 2025 edition's page is no longer served there (404); search listed it, and another HSBC regional site carries the 2026 edition. <br>• **robots.txt** (the .com, .co.uk and .com.hk sites): one prospectus PDF disallowed, a 2-second crawl delay; the pages are allowed. <br>• **Terms:** extracts may be printed, copied or stored "for your personal use"; any other use needs written permission. <br>• **Cadence:** annual, October. <br>• **What it means:** the chat-side watch reads the edition and records the figures with their URL, as it does for every other shelf entry. No session and no writer fetches a figure |
| 1b | **Vanguard's Capital Markets Model outlook** (62): the same | **Passes for the shelf.** <br>• **Page:** `corporate.vanguard.com/content/corporatesite/us/en/corp/vemo/vemo-return-forecasts.html` (HTTP 200; data as of 30 Sep 2026 on the 23 Oct read). <br>• **robots.txt** (corporate.vanguard.com): only `/404` disallowed. <br>• **Terms:** content is licensed "solely for your personal and noncommercial use". <br>• **Cadence:** the page says, "We make our updated forecasts available at least quarterly", on quarter-end runs. <br>• **What it means:** the same as HSBC: the watch records, no session fetches |
| 2 | **PEG and LTEG** (67) | **F3's ruling is the check:** both are listed gaps. the independent chart house's series fails the standing rule (A53's check of 20 Oct: robots.txt disallows `/api`, which the chart pages read, and the copyright notice forbids use without consent). S&P DJI was withdrawn on 17 Oct, and LTEG is a proprietary consensus field. No workaround was looked for |
| 3a | **Census household counts through FRED** (68) | **Passes.** `TTLHHM156N`, "Household Estimates", the Census Bureau's: **thousands, not seasonally adjusted, monthly**, from 1955 (quarterly before the monthly rows begin). The newest row on 23 Oct is June 2026 (133,971). It is read off FRED's own series page and the keyless graph CSV, and is new to the store: `fred.households` |
| 3b | **Redfin's pending sales, already stored** (68) | `redfin.pending_sales` (national, from the data center's `country.csv`), **monthly from January 2012** (`altdata/sources/redfin.py`'s verify item 5) |
| — | **NAR's 66.0 print** (68's dated record) | **NAR's release** of 20 Oct 2026 says pending sales "decreased by 7.3% month-over-month and 11.3% year-over-year". Its chart gives the index as 66.0, down 7.3%. The release does **not** itself call it a record; the order's source chart and the trade press do. The dated record says exactly that |
| — | **The note's citations** (67) | Each study was checked against its DOI through Crossref, and the abstracts quoted were read there. The 2000 figures are from Acadian Asset Management's piece (June 2026), read in full. **No published study stating 2021's level was found**, so that part of the note is "not written" |

## Item 62: the cross-house CMA table

**The shelf** (`docs/reading/watchlist.json`, version 2026-10-23). Both entries use the existing schema, in the chartbook group beside J.P. Morgan's LTCMA, at depth `list`:

| id | Publication | Cadence | Expected |
|---|---|---|---|
| `hsbc-cma` | Capital Market Assumptions, HSBC Asset Management | annual | October, first half |
| `vanguard-vcmm` | Capital Markets Model return forecasts, Vanguard Investment Strategy Group | at least quarterly | Jan, Apr, Jul, Oct, weeks after the quarter-end run |

The "not on the shelf" note excluded "Vanguard outlooks". It now excludes only Vanguard's **narrative** outlooks and says the model's forecasts joined for this table.

**The data shape: a scan file per edition, not a field in `register.json`.** The register's edition entries are written by `tools/reading_register.py` or by hand. A number stored there would be a by-hand line (F2), and the Reading chapter prints those entries verbatim. So:
- **the edition** stays a register entry, as every shelf edition is, with its URL and its `scan`;
- **the figures** are its scan's reference table, `docs/scans/cma-<house>-<YYYY>q<N>.md` (family `cma-<house>`), which `python -m altdata.scans ingest` stores as sourced figures under the existing refusal rules: no URL, section or as-of means not stored, and advice is refused.

**One change to the ingest** (`altdata/scans.py`): a reference table with a `Source URL` column stores each row's own URL in place of the header's. That gives each asset's figure its URL, as the paste asks. No existing scan has the column, so nothing stored changes.

**The table** (`altdata/cma_table.py`, `config/cma_table.yaml`).
- **Houses:** J.P. Morgan (LTCMA), AQR, GMO, Research Affiliates, HSBC, Vanguard, in the ruling's order.
- **Assets:** US equity, ex-US developed equity, EM equity, Treasuries, IG credit, HY credit, 60/40.
- **Per asset:** the median, the high less the low, and the count of houses with a current edition.
- **The 15-month drop:** an edition whose data as-of is more than 15 months before the cutoff is dropped and counted ("1 dropped as older than 15 months").
- **Readable at the cutoff:** a scan read after the cutoff is not counted (`read_on`, the scans rule).
- **A house with nothing stored** prints "no edition stored", never a recalled figure.
- **Each edition's horizon and basis** (nominal or real) are two rows of its own scan, `Horizon` and `Basis`, and print in its edition line. The houses differ: GMO's is 7-year and real, J.P. Morgan's 10 to 15 years. The median is taken across them as published, with no conversion, and the read says so.

**Where it prints:** the Monthly's slow layers, after the sourced figures, under "Capital market assumptions across houses: 10-year expected returns" (`daily_cascade/batch14_b2_block.py`). The code-written read comes first as a `lead` (the ES block's pattern: printed before the tables), then the table, then one line per edition. The CMA families are left out of the generic sourced-figures sub-sections, so each figure prints once.

**Today:** `docs/scans/` holds no CMA edition, and the J.P. Morgan GTM scan carries no LTCMA figures. So every house prints "no edition stored" and no median prints.

**Item 30's Book A line:** the allocation block (Positioning & flows, the Weekly and the Monthly) ends on "Book A long-horizon expected return (cross-house CMA median, US equity): …", or "no CMA edition stored". It is report-only: nothing reads it back, and it enters no composite or rule table. It reads the scans table of the store the block was given, and nothing when given none.

## Item 67: PEG and LTEG

- **No PEG or LTEG line prints (F3).** Item 60's lines (`altdata/eps_overshoot.py`, printed by `daily_cascade/index_carry_block.py`'s what's-priced sub-section) now end on one line in every branch: "PEG and long-term growth: no keyless source; see the LTEG overshoot note (docs/base-rate-notes/lteg-overshoot-2026-10.md)."
- **The note:** `docs/base-rate-notes/lteg-overshoot-2026-10.md`, a new folder, since no notes folder for base-rate notes existed (B56's crypto-winter note will sit beside it). It makes three claims from studies (2003, 1996, 2024), each with its title and DOI, and the 2000 peak from Acadian's June 2026 piece, with its URL. **2021 is "Not written":** no citable source was found. No author's name appears (the paste's no-names rule), so each citation is its title, journal, year and URL.
- **The narrative entry** `market_cheap_on_peg` in `config/narratives.yaml` `proposals:`:
  - It seeds at the next seed as PROPOSED, emerging, origin `config_proposal`.
  - The caveat is in its direction: "the denominator is an inflated long-term growth estimate".
  - Its source is "a chart-house post", tagged as the order tags it (credible voice; chart-house source), with no person's name.
  - Its evidence and outcome are in store terms: the S&P 500's five-session rise for evidence, and ^GSPC higher in 182 days for the outcome (see "where the order and the code differ", 3).
  - **The `validate_narratives` proposals pin goes from six to seven.**

## Item 68: the per-household line

- **What:** Redfin's pending sales over the Census household estimates (thousands), so the figure is pending sales per 1,000 households. Each month uses the latest estimate on or before it. It is monthly and labelled single-source (F3: NAR's index has no free series).
- **Percentiles:** dual (five years and the full stored history, each with its n), by `st_r5_rates.lens`.
- **Where:** item 36's housing block (`altdata/st_r5_rates.py`, `housing` and `housing_lines`), the line right after the raw Redfin level. It prints in the Weekly's and the Monthly's Plumbing & rates, and on the close where the block prints.
- **Absent:** "not read" with its reason, until `fred.households` has its first pull.
- **The first figure:** September 2026's 316,652 over June's 133,971 thousand is about **2.36** per 1,000 households. That is arithmetic on the two published figures, not a stored read; the box prints its own after the pull.
- **The NAR 66.0 print** is a dated record at the end of `docs/dated-appendix-queue.md`, under item 36's ledger (ST-R5.36b), with its source line. It is not a data line.

## The gate

`tools/validate_batch14_b2.py`, nine groups, **55/0** on the laptop: synthetic fixtures only (`tests/fixtures/batch14_b2/`, four fixture CMA scans), scratch stores, no network.
- **A.** The shelf entries in the schema, and the due list.
- **B.** The CMA ingest: per-row URLs, idempotent; median, spread and count by hand; the 15-month drop and its count; "no edition stored"; the read-on cutoff; no live CMA scan.
- **C.** Placement: the lead before the table; the sourced-figures exclusion; the Book A line, and its "no CMA edition stored" path; no default-database read.
- **D.** The PEG gap line in every branch, and no PEG or LTEG key or value.
- **E.** The note's citations: a quoted title and a URL per claim; 2021 "Not written"; every percentage beside a URL.
- **F.** The proposal validates, carries its caveat and seeds PROPOSED in a scratch register.
- **G.** The per-household figure and its percentiles by hand, its placement, and its absent path.
- **H.** The appendix entry.
- **I.** The new key registered and pulled; no store write, vendor value, by-hand key, composite, market-state or register import; no person's name, handle or email.

**Registered** in the Makefile's `PY_VALIDATORS`. CLAUDE.md's count, recounted on chain-5's base, goes from 133 code gates (130 Python, 3 shell) to **134 (131 Python, 3 shell)**, with 8 data gates.

**Run locally:**

| Gate | Result |
|---|---|
| `validate_batch14_b2` | 55/0 |
| `validate_narratives` | 103/0 |
| `validate_st_r5_rates` | 72/0 |
| `check_registry` | OK |
| `check_library` | 0 failures, 0 warnings |
| `validate_batch12` (its eps-lines checks now expect the closing gap line) | 57/0 |
| `validate_audit_3a` (the counts and the new block) | 88/0 |
| `check_master_guide` | 0/0 |

The stack gates are left to CI.

## Every listed gap

- **PEG and LTEG** (67, F3): no keyless source. Neither prints; the one gap line points at the note.
- **The PEG/LTEG flag** (67): not built; it needs both series.
- **Item 60's realised forecast error**, the order's adjudicator for the PEG story: already a listed gap (Batch 12, F3). The proposal resolves on the index instead.
- **2021's LTEG level and overshoot** in the note: no citable source found on 23 Oct 2026, so it is not written.
- **NAR's pending home sales index** as a series (68, F3): no free series. It is the dated record only, and the line is Redfin's.
- **Every house's CMA figures** (62): none is stored until the publication watch writes the scan files (needs-you 1). No figure is fetched by a session or entered by hand.

## Every session-set value, with its reason

| Value | Setting | Reason |
|---|---|---|
| The CMA staleness floor | 15 months | the paste's figure: an annual edition stays in for one cycle and a quarter's slack |
| The houses and their order | JPM, AQR, GMO, RA, HSBC, Vanguard | the ruling's list (item 62's ruling 2) |
| The median | across houses as published, no horizon or basis conversion | the houses' horizons (7 to 15 years) and bases (nominal, real) differ, and no conversion is ruled; each prints beside its edition |
| The Book A asset | US equity | item 30's line is the equity allocation's long-horizon return |
| The dispersion | high less low, with the count | the paste's definition |
| The deflator | the latest household estimate on or before the month | the series is monthly but can lag Redfin by a quarter |
| The per-household unit | per 1,000 households | the estimate is in thousands, so the ratio is per thousand with no rescaling |
| The per-household percentile windows | five years and the full stored history | the paste and `st_r5_rates.lens`'s rule |
| The proposal's outcome horizon | 182 days | the paste's "within two quarters" |
| The proposal's evidence rule | ^GSPC's five-session rise at or past its 10th percentile | the committed proposals' shape, on the index the story names |
| Vanguard's expected months | Jan, Apr, Jul, Oct | "at least quarterly" on quarter-end runs; the watch registers the quarter-end run only |

## Each new key, its source and its real publication lag (for b51's `config/publication_lags.yaml`)

| Key | Source | Cadence | Lag to add |
|---|---|---|---|
| `fred.households` (block `fred_households`, `FRED_HOUSEHOLDS_SERIES`) | FRED `TTLHHM156N`, Census | monthly | **none:** FRED's monthly-release family covers it. The newest row on 23 Oct is June, so watch the first box read; if it is held stale, it needs its own lag (about four months) |

`FRED_PULL_SERIES` goes from 277 to **278** (CLAUDE.md, the architecture document's store box). The Master Guide's "FRED's pull walks 277 series" is the next chain refresh's, as b52 left its counts.

## Where the order and the code differ

1. **"A per-house CMA record in register.json's edition entries"**: the figures go in the edition's scan file, and the store, not in `register.json`, because a number in the register is a by-hand line and the chapter prints it verbatim (above). The edition entry still carries the house, the date, the URL and the scan.
2. **"10-year expected return"**: GMO publishes seven years, real, and J.P. Morgan 10 to 15 years. The table prints each edition's own horizon and basis and takes the median as published.
3. **The proposal's outcome**: the paste's example ("item 60's realised forecast error turning negative within two quarters") is a listed gap, so the store cannot answer it. The outcome is the S&P 500 two quarters on, and the note names the forecast error as the adjudicator once it exists.
4. **"Item 30's Book A long-horizon expected-return line"**: no such line existed. Item 30's ruling names it as a Book A modifier via the rule table, and no rule table reads it. The line is added to the allocation block, report only, and no rule table is edited.
5. **The note's folder**: there was no convention for base-rate notes, so the note starts `docs/base-rate-notes/`.
6. **"Item 36's ledger"** for the NAR print: ST-R5.36b is a dated, never-edited edition, so the line waits in the appendix queue for the ledger's next edition.

## Files shared with other branches

| File | a57-batch14-b1 (`711631b`) | a58-batch15-1 (`e219bc8`) | chain-5 (base) | At the merge |
|---|---|---|---|---|
| `CLAUDE.md` | ✓ (the count line; 281 FRED) | ✓ (135 gates; 282 FRED) | — | keep every paragraph; recount once. **FRED pull 277 + 4 (a57) + 1 (a58) + 1 (b55) = 283**; gates add one per branch |
| `Makefile` | ✓ | ✓ | — | keep every gate line |
| `altdata/config.py` | ✓ (`FRED_BATCH14_B1_SERIES`) | ✓ (`FRED_BATCH15_A_SERIES`) | — | keep every list in the union |
| `metrics_registry.yaml` | ✓ | ✓ | — | splice the new blocks |
| `tools/validate_audit_3a.py` | ✓ | ✓ | — | keep every `NEW_KEY_BLOCKS` entry |
| `config/catalogue_commands.yaml` | ✓ | ✓ | — | keep every module line |
| `docs/chester-reports-architecture-v3.md` | ✓ | ✓ | — | the store box's count: 283 |
| `monthly_macro/stack.py` | ✓ (slow layers) | ✓ | — | keep every hook |
| `docs/dated-appendix-queue.md` | — | ✓ | — | both append at the end: keep every entry |

a56-batch14-a1 is already in chain-5, so nothing is shared with it beyond the base. a57's notes name this branch as not yet on origin.

## The CI rounds

| Round | Run | On | Result |
|---|---|---|---|
| 1 | — | — | — |

## Needs you

1. **The publication-watch prompt** (this chat updates the scheduled task). Yes or no to this spec. When the watch finds a new edition of `jpm-ltcma`, `aqr-cma`, `gmo-7yr` (quarter-ends only), `ra-aai` (quarter-ends only), `hsbc-cma` or `vanguard-vcmm` (quarter-end runs), it writes `docs/scans/cma-<house>-<YYYY>q<N>.md`, house being `jpm`, `aqr`, `gmo`, `ra`, `hsbc` or `vanguard`, with:
   - `# <title>`;
   - `**Edition:** <name> — data as of <D Month YYYY>`;
   - `**Read on:** <D Month YYYY>. **Source:** <edition URL>`;
   - a section `## 1. Reference table — (as of <D Month YYYY>)` with columns `| Metric | Value | Source URL |`;
   - rows `Horizon` (e.g. "10 years") and `Basis` ("nominal" or "real", with the currency);
   - one row per asset, labelled exactly `US equity`, `Ex-US developed equity`, `EM equity`, `Treasuries`, `IG credit`, `HY credit`, `60/40`. The value is the house's 10-year (or stated-horizon) expected annual return as a percent. Where the house gives a range, use its median and say "median of range" in the value. Each row carries the URL of the page or PDF it was read from.

   An asset the house does not publish is left out (it prints "not in the edition"). The watch adds no advice words and no figure from anywhere but the edition. It also registers the edition in `register.json` as usual, with `scan` set to that file.
2. **The proposal `market_cheap_on_peg`**: confirm or reject when the Weekly lists it (yes or no).
3. **The session-set values** in the table above: keep them (yes or no). Above all, the 15-month floor, and taking the median across horizons and bases with no conversion.
4. **The first box read of `fred.households`**: yes or no to adding a publication lag for it in `config/publication_lags.yaml` if the store check holds it stale (the newest row runs about four months behind).
5. **The merge, after the 1 Nov Monthly** (F8): yes or no to merging this branch with a57 and a58, recounting the FRED pull to 283 and the gates once.
