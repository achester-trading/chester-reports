# gtm-core-2 — the J.P. Morgan Guide batch, part 2 (session A, 17 Oct 2026)

**What it builds on, and the merge order.**
- **Cut from:** the tip of `gtm-core-1` at `faded6c`, which is part 1 plus this paste's step 0. So `gtm-core-2` carries part 1, and through it el-4-6, 6b (parts 1 to 3) and item 52.
- **Merge order:** **after `gtm-core-1`, in the second stitched chain.**
- **Branch-only:** pushed, not merged, not deployed, nothing run on the box, and no unit enabled or started.

The work is the GTM change order (`docs/change-order-jpm-gtm-2026-10-03.md`, ruled 3 Oct 2026) for the four adopted items that need the scan's sourced figures or an intake-queue entry: GTM-3, 4, 10 and 12. It also applies rulings 2 and 3 of 17 Oct to GTM-13 and GTM-15.

---

## This branch's CI, and the rulings of 17 Oct on this report

| Run | Commit | Result |
|---|---|---|
| 39093948685 | `ae09e15` (the build) | **failed**, two checks of mine |
| 39094111332 | `38276bf` (these notes) | **failed**, the same two |

Both failures were gates pinning what this branch changed, and both are fixed in the next commit:
1. **`validate_official_sources`, "edgar_xbrl: an outage is STALE and writes nothing".** CI has no SEC contact, so the new reader was correctly PENDING and never reached its fetch. The outage loop now gives it a placeholder contact (no address), so the outage path is the one tested. 290/0 locally.
2. **`validate_st_r5_t1_rest`,** which pins the FRED counts. It now pins 63 / 165 (GTM-12's six). 103/0 locally.

Everything else passed in both runs. The fix commit's run is read in `st-t1-rest`'s notes, the next branch on this line.

**The rulings of 17 Oct on this report, applied:**
1. **The queue order:** the operator rules it at the 25 Oct dry run. GTM-3's entry stays a draft with no position.
2. **SR-49:** confirmed skipped. SR-48 and SR-50 to SR-59 stand.
3. **Slides 8, 11, 15, 22 and 27:** they stand as one-time sourced figures, each with its slide and as-of. They are reference data, not a recurring line.
4. **The four GICS buckets:** no membership by hand (rule 30). They print the Guide's figures, labelled; no keyless membership source is pursued.
5. **The consensus log** may read the top 10 plus ORCL and GOOG. The budget it uses is now stated in its catalogue line: one Yahoo `.info` read per name, 0.6 s apart, nightly. That is 24 names before (13 options names, 11 sector ETFs) and at most 39 with the GTM names. GTM-3 and the hyperscaler bucket print the Guide's figures until the names are logged.

---

## Step 0 (committed on `gtm-core-1`, `faded6c`)

### `gtm-core-1`'s CI

| Run | Commit | Result |
|---|---|---|
| 39089207209 | `2672e4e` (the build) | **failed**, two checks of mine |
| 39089519115 | `552374f` (the notes) | **failed**, the same two |
| 39091890898 | `faded6c` (step 0) | **green** |

The two failures, both fixed in `faded6c`:
1. **`validate_weekly_edits`, check 9** ("every gate removes its temporary store on exit"). `validate_gtm.py` used a bare `tempfile.mkdtemp`, and now uses `gate_tmp.mkdtemp`.
2. **`validate_thesis_register`** ("the Monthly's slow layers carry the seed table after the base rates"). The GTM tables had been spliced in directly after the base-rates table, which pushed the theses seed table one place down. They now go in after the seed table.

`gtm-core-1`'s notes record the run numbers and the step.

### Register numbers (ruling 4)

The GTM items take fresh numbers from **SR-48** upward, in the change order's table order. The working numbers the other branches use stand: SR-43, SR-45 and SR-46.

**Conservative reading: SR-49 is skipped too.** It is the selloff-shape axis's working number in main's own code (`altdata/rates_shape.py`, `config/rates_anchors.yaml`, `tools/validate_rates_anchors.py`; signal-triage batch 4). That is a working number in exactly the ruling's sense. Needs-you 2 asks you to confirm.

The final map:

| Item | Part 1 | Now | Status |
|---|---|---|---|
| GTM-1 | SR-37 | **SR-48** | built (part 1) |
| GTM-3 | SR-38 | **SR-50** | built here, report-only |
| GTM-4 | SR-39 | **SR-51** | built here |
| GTM-8 | SR-40 | **SR-52** | built (part 1) |
| GTM-9 | SR-41 | **SR-53** | built (part 1) |
| GTM-10 | SR-42 | **SR-54** | built here |
| GTM-11 | SR-43 | **SR-55** | reserved: Amendment #3 workstream B |
| GTM-12 | SR-44 | **SR-56** | built here |
| GTM-13 | SR-45 | **SR-57** | part 1, amended here (ruling 2) |
| GTM-14 | SR-46 | **SR-58** | reserved: pulled into T3 |
| GTM-15 | SR-47 | **SR-59** | part 1, amended here (ruling 3) |

GTM-7 (SR-9) and GTM-21 (SR-5) keep their keys.

These changed together:
- the register's entries;
- `config/gtm.yaml` `register_numbers`;
- the table notes in `daily_cascade/gtm_block.py`;
- Base Rates Appendix C, row A-7, and its HTML edition;
- the CLAUDE.md line;
- `validate_gtm` group H.

Batch 4's own SR-37, SR-38, SR-43 and SR-46 references in code are theirs and were not touched.

### The incidents line (ruling 6)

The Audit #4 baseline column prints **"INC-1 to INC-9, one open (by hand, Audit #4, 14 Oct)"** again, labelled like the rest (`config/reporting_stack.yaml`). `validate_system_metrics` group C holds it against the agenda's own words.

### GTM-1's historical cells (ruling 1)

My tools reached the public PDF: the 4Q 2026 edition, 71 slides, "Data are as of September 30, 2026". I transcribed slide 4 once into the scan as a new **§7, "Slide transcriptions"**, dated as read 17 Oct 2026.
- **Cells:** 24 of the 32 are stored as sourced figures with slide 4 and the as-of. The slide prints the dividend yield and the 10-year at the four tops only, so the bottoms' cells for those two fields print "not on the slide".
- **Two corrections against part 1:** the 2000 multiple is the slide's 25.2x, not the scan's rounded "25x"; and the rows carry the slide's exact dates.
- **Not recurring:** this is a one-time transcription of reference data.

**Conservative readings taken here (needs-you 3):**
- **§7 covers more than GTM-1.** It also transcribes slides 8, 11, 15, 22 and 27, the reference data part 2 prints. The scan's §6 has the headline figures, but not the per-sector rows (P/E against the 20-year average, EPS against the median, foreign sales), not the bucket definitions and not the capex history before 2025. The same one-time transcription under ruling 1's logic was the conservative way to get them with a slide and an as-of. The parser stops at §7's heading, so none of it reaches the Monthly's reference table.
- **Every sourced figure now carries its slide.** I read each of part 1's figures against the PDF:
  - GTM-7: slide 65;
  - GTM-8: slide 30;
  - GTM-9: slide 62;
  - GTM-13: slide 34;
  - GTM-15: slide 24;
  - GTM-21: slide 26;
  - the Guide's 30 Sep row: slide 4.

  `gtm.sourced_refusal` now refuses a figure with no slide.
- **GTM-21's note is now dated.** It said the scan does not name the delinquency flows' quarter. Slide 26 dates them 2Q26, and its 11.1% DSR is a 3Q26 estimate of the Guide's own; the note says so.

### The stock–bond window (step 0.5)

GTM-7's table has a row for the **latest 24-month window**, printed with its own months, beside the Guide's 2021–25 era figure (+0.33). Its line now says that the regime word is read on the latest 24-month window, and that the Guide's figure is an era average over a different window. **No regime word changed.**

### Part 1's drafts (the rulings)

Accepted as drafted, and now marked so:
- the SR-5 and SR-9 amendments in the register;
- Book A rows A-6 and A-7 in Base Rates Appendix C (the HTML edition is rebuilt);
- the GTM-8 disagreement entry in `config/narratives.yaml`.

The disagreement entry's status is `accepted`. It is still in config only: confirming it into the narrative register is your gate, and I did not touch it.

---

## The four items

Every sub-section is **tables and lines**, asking no paragraph and drawing no chart, so **no word and no chart is displaced**:
- the Weekly holds at 3,500 words and 10 charts;
- the Monthly at 10,000 and 12.

Every table keeps six columns at most. Every figure only the Guide has is a sourced figure, with its slide and as-of, and is never recomputed. **A measure missing an input prints the Guide's figure, labelled, never a partial computation presented as whole.**

### GTM-3, the concentration twin (SR-50): report-only

**Inputs:**
- **SPY's holdings:** `sp500.member_weight`, the constituent writer's.
- **The names' trailing and forward P/E:** `yf.trailing_pe` and `yf.forward_pe`, the consensus log's.
- **The index:**
  - the S&P 500's close, `yfinance.mkt_gspc`;
  - Shiller's trailing earnings, `shiller.sp_earnings`;
  - S&P DJI's forward operating EPS, `spdji.fwd12m_op_eps`.

**What the fundamentals writer carries:** cash flow, capex, net debt, inventory and COGS for nine names. It carries **no EPS and no share counts**. So the twin is built from the consensus log's multiples and needs no share count: cap share over P/E is earnings share.

**The computation:**
- **The top 10:** the ten largest issuers, with GOOG counted with GOOGL. These are item 31's ten.
- **Earnings share:** each name's weight over its trailing P/E, times the index's trailing P/E. The index's is the close over Shiller's trailing twelve months, and the line names Shiller's month.
- **Forward P/E:** the top 10's from Yahoo's forward P/E (the next fiscal year), and the index's from S&P DJI. The other 490 back the top 10 out of the index, the Guide's method.

**Own averages:** over every stored holdings day, with the window and n. The history starts 16 Oct 2026, so it prints as **short**, and the Guide's averages since 1996 (100%, 112% and 113% of own average) are the comparison.

**Where it prints:** Mechanics, the Weekly and the Monthly, right after item 31's "Concentration and breadth". Two tables:
- ours beside the Guide's slide-8 figures (40.6% / 36.1%; 20.9x / 17.9x / 19.0x);
- each P/E against its own average.

**What the live box will show at first:** the consensus log covered only seven of the likely top 10 (not AVGO, BRK-B or JPM, for example). So until its next runs, the earnings share and the top-10 and other-490 P/Es print **"not stored (no multiple for …)"**, naming the names, beside the Guide's figures.

**The consensus log now reads more names.** It adds the newest holdings' top 12 issuers and the hyperscaler bucket's ORCL and GOOG (`gtm_equities.consensus_names`) beside its own universe. That is keyless Yahoo, the same read it already makes. This is a writer change; needs-you 5 asks you to confirm it.

**Bases differ from the Guide's (FactSet).** Ours and the Guide's print side by side. Needs-you 6.

**The intake-queue entry (filed as a draft).** It is in `config/tb_intake_queue.yaml`:

```
id: GTM-3 · register: SR-50 · overlay: Concentration & Complacency · side: top
status: draft · rights: none · position: null (your ruling, 25 Oct)
filed: 2026-10-17, under rule 31
adds beyond the overlay: the Top-10 >= 25% input reads the cap share alone;
  the twin asks whether that share is earned
ledger needed: a pre-registered monthly calibration ledger -- the cap-less-earnings
  gap and the top 10's P/E against its own average, beside the overlay's
  five-input state, resolved against the next twelve months' equal-weight less
  cap-weight return and the top 10's drawdown; in the probability ledger under a
  source of its own (proposed tb_intake:gtm3), written only once you accept it
```

No code reads the file. `validate_gtm` group Q holds every entry to `draft` / `none` / no position. It also diffs the overlay's five declared inputs against the ones pinned in the gate, in each of the three documents that state them (the master narrative, the translation table and the architecture), and checks that the overlay is still not built.

### GTM-4, the AI buckets and the hyperscaler bridge (SR-51): the Factor I exhibit

**The buckets** (`config/ai_buckets.yaml`): the Guide's five, as slide 11 defines them, dated 30 Sep 2026, refreshed each quarter from the scan.
- **Hyperscalers:** the only bucket with named members (AMZN, GOOGL/GOOG, META, MSFT, ORCL), so the only one we compute:
  - **weight:** the members' SPY weights;
  - **year to date:** the market-weighted price return from the last close of 2025;
  - **NTM P/E:** from Yahoo's forward P/E.
- **The other four** are GICS industries, and the store holds no GICS industry classification. Their cells print the Guide's figures, labelled:
  - semis 18.6% of the index, +44% year to date, 18.2x;
  - hardware 11.2%, +37%, 27.1x;
  - power 2.5%, +22%, 20.6x;
  - software 9.3%, +4%, 25.9x;
  - and 53.2% together.

**The bridge** (`altdata/sources/edgar_xbrl.py`, new):
- **Source:** SEC EDGAR's XBRL frames, keyless, with the SEC contact through `edgar.user_agent()` alone. It is registered as an SEC caller in `validate_secrets` group J.
- **Tags:**
  - operating cash flow: `NetCashProvidedByUsedInOperatingActivities`;
  - capex: `PaymentsToAcquirePropertyPlantAndEquipment`, else `PaymentsToAcquireProductiveAssets` (Amazon's tag).
- **Years:** 2019 to last year, by calendar frame. A June (MSFT) or May (ORCL) fiscal year sits in the frame its larger part falls in.
- **Gaps:** a filer without a tag prints "not stored (filer)".
- **Beside it,** as sourced figures (slide 22): the Guide's capex history, and its path of $799bn for 2026, $1,093bn for 2027 and $1,200bn for 2028.
- **Without the contact** the reader is PENDING and fetches nothing.
- **Keys:** `edgar.xbrl_operating_cash_flow` and `edgar.xbrl_capex`, in dollars, instrument = ticker. The reader is scheduled with the external writers.

**Where it prints:**
- **The Monthly:** the Mechanics, the bucket table and the bridge right after the SR-37 panel (the Factor I exhibit).
- **The Weekly:** the bucket table only, in the Mechanics. A table spends no words, so the budget allows it.

**What it displaces:** nothing.

### GTM-10, the sector rows (SR-54)

**Computed:** the correlation of each sector ETF's daily price return with the 10-year's daily change in bp (FRED DGS10, `fred.yield_10y`). Over 252 and 1,260 sessions, with 90% coverage, else "not reached".

**Where it prints:**
- **The Weekly:** a column ("Correlation to the 10-year, 1 year") in the leadership table, "Sector rotation and leadership". It is a table cell inside the budget, and pairs get "—".
- **The Monthly:** the sector sub-section keeps its pinned four columns and carries the full rows as a second table, ours (one year and five) beside the Guide's slide-15 rows:
  - forward P/E (20-year average);
  - NTM EPS growth (20-year median);
  - foreign share of sales;
  - the Guide's own correlation, two years of monthly returns, a different window and frequency from ours.

### GTM-12, federal finances (SR-56): the Factor IV rows

**What the panel lacked.** The Factor IV rows carry debt to GDP and r minus g (pillar 8, the `fiscal_dollar` theme). GTM-12 adds six FRED series, each unit read off its FRED page on 17 Oct:

| Key | FRED id | Units, frequency |
|---|---|---|
| `fred.fed_interest_payments` | A091RC1Q027SBEA | $bn SAAR, quarterly |
| `fred.fed_defense` | FDEFX | $bn SAAR, quarterly |
| `fred.fy_net_interest` | FYOINT | $ mn, fiscal year |
| `fred.fy_net_outlays` | FYONET | $ mn, fiscal year |
| `fred.fy_deficit` | FYFSD | $ mn, fiscal year |
| `fred.fy_deficit_gdp` | FYFSGDA188S | % of GDP, annual |

**Two bases, never mixed in one ratio:**
- **The national accounts:** interest, defense and customs (B235RC1Q027SBEA), as shares of current expenditures (FGEXPND). Defense includes gross investment, which current expenditures exclude, and the note says so.
- **The budget:** net interest and the deficit as shares of net outlays, and the deficit as a share of GDP.

**Percentiles:** each share's, over ten years and the full history, with n. Every key has family `quantity` (the deficit-to-GDP `ratio`) and long window `full`. The FY series are `freq: annual`, whose allowance is 260 sessions × 3.

**The CBO debt path** is a sourced figure, dated, replaced at each update: 99.4% of GDP at the end of FY2025, 120.2% in 2036 (slide 27, CBO's February 2026 update). The Guide's 2026 figures print as lines: net interest $1,039bn, defense $885bn, customs $418bn, the deficit $1,853bn.

**Where it prints:** "Federal finances (Factor IV)", a table in the Monthly's Plumbing & rates. It displaces nothing.

### GTM-13 and GTM-15, the fixes (rulings 2 and 3)

**GTM-13** (SR-57):
- **The proxies:** TIP, MUB and MBB join the price basket (now 111 symbols; Yahoo, keyless) and the Security Master (SM00197–SM00199; currency, exchange and multiplier listed unverified for your review).
- **The durations:** theirs and AGG's are the issuers' own effective durations, read off the iShares product pages on 17 Oct (as of 15 Oct): **AGG 5.70, TIP 6.19, MUB 7.13, MBB 5.75 years**. They are in `config/instrument_reference.yaml` with the date read.
- **Before the backfill:** the three rows print "not stored" until the price backfill runs.

**GTM-15** (SR-59) is **monthly**:
- **The rate:** the MTS's customs duties collected (Table 4, gross) over the month's BOPGIMP, read through the fiscaldata writer (`fiscaldata.mts_customs_gross`, `_refunds` and `_net`, dollars).
- **Beside it:** three months, and the month's refunds. The rate reads the gross because refunds of IEEPA duties turned net receipts negative from mid-2026. Probed 17 Oct: June 2026 was net −$25.6bn on gross $23.6bn.
- **The cross-check:** the quarterly FRED rate. Both print with their as-of.
- **Fault isolation:** a failure in the MTS line never fails the MSPD rows.

---

## Registry, catalogue, units (AUD-3a)

**New stored keys, each registered with units, family and long window:**
- `fiscaldata.mts_customs_gross`, `_refunds` and `_net` (`usd`, `macro_sovereign`);
- `edgar.xbrl_operating_cash_flow` and `edgar.xbrl_capex` (`usd`, `corporate_fundamentals`, source `edgar_xbrl`, new in `source_registry.yaml`);
- the six FRED series (the FRED signal block now 63; `fy_deficit_gdp` as `percent_share`);
- TIP, MUB and MBB in both price blocks (111) and the share-volume block (85).

**The catalogue:** `altdata.gtm_equities`, `altdata.sources.edgar_xbrl`, and the updated `altdata.gtm` and `altdata.sources.fiscaldata` lines.

**CLAUDE.md:** 63 more in `FRED_SIGNAL_SERIES`; `FRED_PULL_SERIES`, 165; 111 market symbols; the GTM paragraph rewritten for both parts. The gate count is unchanged: no new gate file, `validate_gtm` is extended.

---

## Gates

`tools/validate_gtm.py`, extended with groups K to Q. Hand figures are in `tests/fixtures/gtm/README.md`, and every part-2 fixture value is synthetic and says so.

| Group | What it holds |
|---|---|
| K | GTM-3 against the hand figures: 39.4%, 29.4286%, 27.7861x, 16.9178x, 20.0x, and own averages of 100.50% and 100.70% |
| K | The cap share equals item 31's |
| K | A name without its multiple: the cell is not stored, naming BRK-B, with the Guide's 20.9x beside it |
| L | The hyperscalers: 19.2%, +6.2374%, 25.9576x |
| L | A missing member (ORCL's multiple) prints the Guide's 22.2x, labelled |
| L | The GICS buckets print the Guide's figures |
| L | The bridge parses the XBRL-frames fixture: 380 − 155 = 225 bn |
| L | "not stored (META)" where a filer lacks a tag |
| L | With no SEC contact, the reader is PENDING and fetches nothing |
| M | The sector correlation, −0.8964 by hand; "not reached" past the store |
| M | The Weekly's one new column; the Monthly's Guide rows |
| N | The MTS reader keeps the customs line only: 10.8% and 10.2695%, refunds beside |
| O | The federal shares: 15.7143%, 14.2857%, 25.7143%, 5.9% of GDP; the CBO path as a sourced figure |
| P | Every sourced figure (167) carries a slide and a section; a part-2 figure without a slide is refused; a stored one prints with its slide and as-of |
| Q | The queue entry is a draft and grants nothing; the overlay's inputs are diffed |

No gate reads the live store, fetches or calls a model: group J's import scan now covers `gtm_equities.py`.

**Run locally, one at a time, only those this branch writes or changes:**

| Gate | Result |
|---|---|
| `validate_gtm` | 77/0 |
| `validate_system_metrics` | 21/0 |
| `validate_prices` | 101/0 |
| `validate_audit_3a` | 85/0 |
| `validate_secrets` | 54/0 |
| `validate_weekly_complete` | 63/0 |

Every other gate is CI's.

**CI for `gtm-core-2`:** recorded in the section below once read.

---

## Box commands, for the operator

Run these inside a window, after Thursday's merge: weekdays 09:05–15:40 or 17:20–23:30 ET, never 16:00–17:20; weekends are open, clear of Sunday 05:00. I ran none of them, and no unit is enabled or started.

```bash
cd ~/chester-reports && git pull --ff-only

# 1. TIP, MUB and MBB: five years of closes and volume (GTM-13's three rows):
.venv/bin/python tools/backfill_prices.py --years 5 --symbols TIP,MUB,MBB --dry-run
.venv/bin/python tools/backfill_prices.py --years 5 --symbols TIP,MUB,MBB

# 2. GTM-12's six FRED series, first pull, then their history from ALFRED:
.venv/bin/python -m altdata.feeds pull --only fred
.venv/bin/python -m altdata.fred_history backfill --series fed_interest_payments,fed_defense,fy_net_interest,fy_net_outlays,fy_deficit,fy_deficit_gdp --dry-run
.venv/bin/python -m altdata.fred_history backfill --series fed_interest_payments,fed_defense,fy_net_interest,fy_net_outlays,fy_deficit,fy_deficit_gdp

# 3. The MTS customs line (its first pull reads every month from 2015; the
#    16:10 and 06:45 official passes run it after this anyway):
.venv/bin/python -m altdata.sources.fiscaldata

# 4. The hyperscalers' filings (PENDING, fetching nothing, unless
#    CHESTER_SEC_CONTACT is set in .env -- which the fundamentals writer uses too):
.venv/bin/python -m altdata.sources.edgar_xbrl

# 5. The scan's figures: the 167 GTM rows, slide 4's cells and part 2's
#    (idempotent; the Monthly's run does this too):
.venv/bin/python -m altdata.scans ingest

# 6. The first read, text only, read-only:
.venv/bin/python -m altdata.gtm show
.venv/bin/python -m altdata.gtm_equities show
```

**On their own:** the consensus log picks up the top 10 and ORCL and GOOG in the overnight pass, with nothing to run. The twin's and the hyperscaler bucket's multiples fill from the night after.

**The first renders to read:**
- **The Weekly of Sunday 26 Oct:** GTM-13 with its three new proxies, the twin and the bucket table in Mechanics, and the sector column.
- **The 1 Nov Monthly:** the rest. Its dry run is yours, as always: `python -m monthly_macro.run --dry-run`.

**Ruling 5:** the first box pull after Thursday's merge (the BLS feeds under the generic User-Agent) stays on your list to watch. Nothing here changes it.

---

## Files shared with the open branches

**Session B's lines.** `meme-ingest-ledgers-1` and `audit-leftovers-2` (and `audit-leftovers-1` before them) touch these same files in commits of their own:
- `CLAUDE.md`, `Makefile`;
- `altdata/config.py`, `altdata/feeds.py`, `altdata/loggers/consensus.py`, `altdata/sources/fiscaldata.py`, `altdata/sources/yfinance_source.py`;
- `config/catalogue_commands.yaml`, `config/reporting_stack.yaml`;
- `daily_cascade/weekly_stack.py`, `monthly_macro/stack.py`;
- `docs/signal-triage-register.md`, `metrics_registry.yaml`, `source_registry.yaml`;
- `tools/validate_audit_3a.py`, `tools/validate_monthly_stack.py`, `tools/validate_prices.py`, `tools/validate_secrets.py`.

Each of my edits is an insertion beside a named anchor, or a count. The counts are the stitch's to recompute:
- the basket's 111;
- the FRED signal block's 63;
- the share-volume block's 85;
- CLAUDE.md's count lines;
- `validate_audit_3a`'s `NEW_BLOCK_MEMBERS`.

`validate_secrets`' `SEC_UA_CALLERS` gains one line beside session B's group I. Neither of session B's lines adds a Security Master entry (their `next_id` is 195), so SM00197–SM00199 do not collide.

**This line's own:** `gtm-core-1` (part 1 and step 0), which this branch carries whole.

Nothing in `chester-meme`, Monday's chain, the decision register, the trade ledgers, `.env` or the box was touched.

---

## Needs you

1. **The queue order (for the 25 Oct dry run).** GTM-3's intake-queue entry is filed as a draft with no position. Rule its place among the top-side candidates: Batch 6's items 30, 31 and 44, and GTM-3. Then accept the entry and the ledger it names, or strike them.
2. **SR-49.** I skipped it as the shape axis's working number, so the GTM run is SR-48, then SR-50 to SR-59. Confirm, or rule that SR-49 is the GTM-3 number and shift the rest down by one.
3. **§7's reach.** Ruling 1 named slide 4. I transcribed slides 8, 11, 15, 22 and 27 the same way: once, from the public PDF, dated, as reference data, not a recurring line. They are what GTM-3, 4, 10 and 12 print as sourced figures, and the scan's §6 lacks them. Confirm, or name what to strike.
4. **The four GICS buckets.** They print the Guide's figures because no stored source classifies S&P 500 members by GICS industry. Computing them needs a membership source. Two options:
   - a quarterly by-hand list, which is a by-hand line and so needs your explicit yes;
   - leaving them sourced.

   Standing rule 3 points to the second.
5. **The consensus log's wider universe.** It now reads the newest holdings' top 12 issuers, plus ORCL and GOOG, beside its own universe: keyless Yahoo, the same read. Confirm the writer change. Without it, GTM-3 and the hyperscaler bucket print the Guide's figures.
6. **Mixed P/E bases.** Ours uses:
   - Yahoo's forward P/E for the names (the next fiscal year);
   - S&P DJI's forward operating EPS for the index;
   - Shiller's as-reported trailing earnings.

   The Guide uses FactSet throughout. Both print side by side, never blended. Rule whether that stands or one basis should replace another.
7. **The SEC contact on the box.** The bridge is PENDING without `CHESTER_SEC_CONTACT`. If it is unset, the cash-flow bridge prints "not stored" beside the Guide's capex path.
8. **Pillar 8's gap line.** `config/pillars.yaml` still lists "federal interest burden" as not yet sourced (A091RC1Q027SBEA). It is now stored. Moving it into the pillar's metrics is a pillar change, so it is yours.
9. **The Security Master's three entries** (SM00197–SM00199, the funds' names from the issuer's page). Currency, exchange and multiplier are listed unverified for your review, as item 52's were.
10. **GTM-1's forward P/E today** still prints "not stored". S&P DJI's forward EPS, the one GTM-3 now reads, could fill it from the next drop. Say so and it goes in.
