# b56-batch15-2: signal triage Batch 15, session B -- items 74, 75, 77 and 78 (23-24 Oct 2026)

**What it is.** Session B's four items from the Batch 15 order (items 72-78, filing amendments G1-G6 ruled 23 Oct 2026, 19:13 ET):
- **Item 74** (written as 67): hedge-fund positioning and the squeeze-risk flag;
- **Item 75** (written as 68): the AI-lab financials ledger;
- **Item 77** (written as 70): the cyber-pressure line;
- **Item 78** (written as 71): crypto protocol shutdowns.

Section 0 governs, and items are cited by their filed numbers. **It merges after the 1 Nov Monthly, whatever CI says (G4).**

## Base and boundaries

- **Base.** `b56-batch15-2` was cut from **`origin/chain-5` at `6fa2024`**. Then **`origin/a57-batch14-b1` at `711631b`** was merged in with one merge commit (`c48c8a1`), because item 74 reads item 71's depth. The gate count is recounted on that base: chain-5's 133 code gates plus a57's one makes 134, and this branch's gate makes **135 (132 Python, 3 shell)**, with 8 data gates.
- **The merge met in eleven files, not two.** a57 was cut from chain-4, and chain-5 carries b52's capex-chain proxies on top of it. Each was resolved once:
  - **Kept both sides:** `Makefile`, `config/source_tiers.yaml`, `config/voices_sources.yaml`, `tools/validate_audit_3a.py`, the Master Guide's Table 7a rows.
  - **The Security Master:** b52's SM00205-212 and a57's SM00213-214 both stand (a57 had numbered past b52's), `next_id` 215.
  - **The basket counts are the union:** 124 + AIQ + SPXT = 126 symbols, 106 volume units, a volume-shares block of 96 (the registry's three blocks, `validate_prices`, CLAUDE.md, the architecture document).
  - **The gate count and the FRED pull:** CLAUDE.md's gate count 134; `FRED_PULL_SERIES` 281 (277 + a57's four).
  - **The Master Guide's HTML** was rebuilt with the builder, never hunk-resolved.
  - **Checked on the merged tree:** `check_master_guide` 0/0, `validate_audit_3a` 88/0, `validate_prices` 101/0, `validate_security_master` 102/0, `validate_batch14_b1` 67/0, `validate_batch14_a1` 30/0, `validate_batch14_a2` 40/0, `validate_narratives` 103/0.
- **Its own checkout:** `../chester-b56`. `../chester-reports-t3` holds b55.
- **Branch only:** pushed, not merged. Nothing was run on the box and no unit was touched. No register write, no `.env`, no secret. No vendor value is read.
- **Not touched:** session A's items (72, 73, 76) and the order's filing. The order was read from `C:\Users\arich\Downloads\change-order-signal-triage-batch-15-2026-10-23.md`; a58 commits it.
- **Where the order and the code differ, the code wins.** Every difference is listed below.

## Commits

| Commit | What |
|---|---|
| `c48c8a1` | The merge of a57 into chain-5 (above) |
| `eacd60d` | Item 74's ledger pre-registration, committed alone before any scoring code |
| (next) | Items 74, 75, 77 and 78, the gate, the first ledger edition, the notes |

## Part 0: the source checks (run 23 Oct 2026, from the laptop, before building)

| # | Check | Result |
|---|---|---|
| 1a | **CFTC TFF** (74) | **Passes.** It is the keyless Socrata dataset the repo already reads (`gpe5-46if`, `altdata/sources/cftc.py`). <br>• **Codes:** ES is **13874A** ("E-MINI S&P 500 STOCK INDEX" to 1 Feb 2022, "E-MINI S&P 500" after) and NQ is **209742** ("NASDAQ-100 STOCK INDEX (MINI)", then "NASDAQ MINI"). <br>• **History:** both from **13 Jun 2006**, 1,063 reports to 20 Oct 2026. <br>• **Columns:** `lev_money_positions_long` and `_short` (the writer's existing category map). Each pull reads a contract's whole history, so the first pull is the backfill |
| 1b | **FINRA short interest as a share of float** for the S&P 500 (74) | **Not simple: a listed gap.** FINRA's short interest is stored (`finra.short_interest`, `altdata/loggers/borrow.py`), but for the tracked universe only. Nothing stored or keyless gives the S&P 500's constituent list (S&P DJI withdrawn 17 Oct) or float |
| 1c | **A free hedge-fund performance proxy** (74) | **None keyless: a listed gap.** HFR's robots.txt disallows one path, but its index performance data is sold by subscription ("Purchase an Indices Subscription to download performance data"). A replicating ETF (e.g. QAI) would be keyless through Yahoo, but it is not a hedge-fund performance series and would enlarge the basket; listed in needs-you |
| 1d | **Verify item 3: the prime-book figures' source** (74) | **Holds, as reported on 22 Oct 2026.** The source is Bloomberg's report on a bank's prime-brokerage data, republished by Yahoo Finance from IBTimes. It gives: short sales outpacing long purchases about five to one in October; short leverage at the 99th percentile of five years; global fundamental long-short funds -2.9% in the week to 15 Oct; Asia-focused stock pickers -6.8% for the first half of October. The order's "funds still adding shorts" is not stated as such (the reports say positions were "building"). It is one dated record (G3), never a line |
| 2 | **Verify item 4: Anthropic's S-1 on EDGAR** (75) | **Not public, per public reporting to 22 Oct 2026; EDGAR itself was not read.** No SEC contact is configured on the laptop, so the `CHESTER_SEC_CONTACT` path returned nothing and no SEC request was made. <br>• **Timeline:** the draft was submitted confidentially in June; on 21 Oct, reports said a public S-1 could come "as soon as Friday" (23 Oct), and no report found confirms it did. <br>• **The first entry:** the WSJ-reported draft figures, one provisional dated record. They were checked against Investing.com's relay of the WSJ report (20 Oct 2026): revenue $16.3bn (from $1.1bn), net loss $80.7bn with $72bn non-cash financing charges, "nearly $9 billion" of compute, "roughly $450 billion" of cloud agreements over the decade, about 20% from two customers. <br>• **Not entered:** the order's "up to $86bn of Nvidia chip rental" is not in that report |
| 3 | **Verify item 6: CISA KEV and NVD** (77) | **Both pass, keyless.** <br>• **KEV:** one JSON file (`www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json`), catalogue 2026.10.23, 1,756 entries, `dateAdded` from **3 Nov 2021** (287 that first day: the seeding). robots.txt allows the path; a US government work. <br>• **NVD:** CVE API 2.0 (`services.nvd.nist.gov/rest/json/cves/2.0`). There is no robots.txt (404, no rules). The public limit without a key is 5 requests in a rolling 30 seconds, so the reader waits 6.5 s. `cvssV3Severity=CRITICAL` is a base score of 9.0-10.0. CVSS v3 scores run from late 2015. **Scoring lags publication:** in the week of 12 Oct 2026, 5,499 CVEs were published but 17 were scored critical, against 34 to 39 in older weeks. So the last 8 weeks are re-read each Saturday and the newest 4 print as provisional |
| 4 | **Verify item 7: DefiLlama's protocol count over time** (78) | **Today's list only.** `api.llama.fi/protocols` (no key; DefiLlama is the registered `defillama` source, terms read for Tranche A) served 8,813 protocols on 23 Oct: 7,904 neither `deadFrom` nor `deprecated`, 5,485 of those with TVL above zero. Its `deadFrom` and `listedAt` dates are today's vintage, and a removed protocol drops off the list, so no point-in-time history can be rebuilt. **A daily snapshot is stored from the first pull, and every line says the history starts there** |
| 5 | **Verify item 8: the leader's health report** (log only) | **Unverified; the log-only entry is unchanged.** No CNN report from October 2026 was found; the CNN "critical condition" report found is April 2020's. The October 2026 claim traces to posts on X, relayed by the New York Post (ANI syndication, 20 Oct 2026), with no official confirmation. KCNA reported him touring an exhibition on 19 Oct, with photos not independently authenticated. Nothing is built |

## Item 74: hedge-fund positioning and the squeeze-risk flag

- **The pull.** `TFF_CONTRACTS` gains `13874A: ES` and `209742: NQ`. The same keys (`cftc.tff_lev_money_*`) get new instruments, so no new key.
- **The line** (`altdata/hf_positioning.py`, `config/hf_positioning.yaml`; the Weekly's Positioning & flows, after the CFTC table, `daily_cascade/batch15_b2_block.py`). For ES and NQ:
  - leveraged funds' net in contracts and as a share of open interest;
  - the **net short share's** dual percentiles (five years and the stored history from 2006, each with its n);
  - FINRA's share of float and the performance proxy each print as a listed gap;
  - the prime-book figures do not print (G3).
- **The squeeze-risk flag.** ES's net short at or above its 90th percentile of five years, while item 71's depth is below its 10th.
  - **The depth arm:** depth is not tracked (a57's check 8). Its stand-in, SPY's Amihud illiquidity, rises as depth falls, so "depth below its 10th" is the Amihud measure at or above its 90th, on the same five-year window. That is a57's own depth arm.
  - **Not read:** if either arm is unread, the flag prints "not read".
  - **Where it prints:** in the line's block, and as one context line in item 45's levels read on the close, after item 71's fragility line ("Squeeze risk: ...").
  - **Report only:** no composite and no market-state import.
- **The ledger, ST-R6.74b.**
  - **The pre-registration** is `docs/ledgers/short-extremes-preregistration-2026-10.md`, committed alone (`eacd60d`). Its SHA-256 over the LF bytes is **`584442322783b3cf85ca6bb16c4a08b705ec36c8360f8323dcb4233273f90211`**, held by the gate and by `hf_positioning.PREREG_SHA256`. The script refuses to run if the file changes.
  - **The rule.** An episode is the first week of ES's net short at or above its 90th percentile of the trailing 260 reports, after at least four quiet weeks. Entry is the first S&P 500 close on or after the Friday release. Outcomes are 5 and 20 sessions.
  - **The pass rule:** INSUFFICIENT below 12 episodes. PASS when the episodes' median 20-session outcome beats the baseline's by at least 1.0 pp and at least 60% are positive. FAIL otherwise.
  - **Stored history only.** `tools/calibration/st_r6_74b_short_extremes.py --db PATH` opens the store with `mode=ro` and fetches nothing.
  - **The laptop first edition**, `docs/ledgers/st-r6.74b-ledger-2026-10-23.md`, is **INSUFFICIENT, n 0**. The laptop's store (`../chester-reports/data/chester.db`, 15 Oct) holds no TFF rows for ES, because ES joins the pull with this build. It is a rule-31 draft and grants nothing. The box edition, after the first pull, is the real first read (needs-you 4).

## Item 75: the AI-lab financials ledger

- **The template** is `docs/ledgers/ai-lab-financials-ledger.md`. Its header carries:
  - **the order's disclosure,** that the ledger concerns Anthropic, which builds Claude and drafted the order, and takes no view on the company;
  - **the fields and how each ratio is computed;**
  - **G3's status:** the first row is a provisional dated record, and quarterly entries after it are a **listed gap pending the operator's yes**.
- **The ratios are code** (`altdata/ai_lab_ledger.py`):
  - revenue growth;
  - compute and infrastructure over revenue;
  - **the loss excluding non-cash financing charges**, labelled a cash-burn measure: the ledger has net loss and the charges, not a cash-flow statement;
  - forward commitments over TTM revenue, computed only when TTM revenue is in the row;
  - the top-two concentration, as entered.
- **The first row:** Anthropic, H1 2026, provisional. On it the line reads:
  - revenue +1,382% on the year;
  - compute 55% of revenue;
  - loss excluding the charges $8.7bn;
  - top two customers 20%;
  - commitments $450bn, with the TTM ratio "not computed (TTM revenue not in the entry)".
- **The link** (the Monthly's Factor I lines, `daily_cascade/absorption_block.py` `ai_lab_lines`):
  - item 47's unit-economics line and SR-16's commitments entry, each "no ledger entry" when the ledger is empty;
  - **the mega-IPO watch beside SPCX** (`config/ai_lab_ledger.yaml`): Anthropic's expected float, index-inclusion timing and lock-ups each print "not yet public".
- **The dated record:** the S-1 figures are one dated record in `docs/dated-appendix-queue.md`, marked PROVISIONAL, with the disclosure.

## Item 77: the cyber-pressure line

- **The writer** (`altdata/cyber_pressure.py`, `config/cyber_pressure.yaml`) is a **Saturday step of the crypto basket's 17:25 run** (`scripts/run_crypto_basket.sh`; it skips itself on other days). There is no new timer, and it sits on the freshness roster as `cyber`. Two weekly keys, observed_at the ISO week's Monday:
  - **`cyber.kev_added_week`**, from the whole KEV catalogue, reconstructed: complete at the week's Sunday 23:59 ET. The seeding week (3 Nov 2021) is stored and left out of the percentiles.
  - **`cyber.nvd_critical_week`**, NVD's CVSS v3 CRITICAL count for the last 8 complete weeks, each a vintage at the pull instant.
  - **The NVD backfill** (`python -m altdata.cyber_pressure backfill`, about 35 requests from 2016) is the operator's.
- **The line** (the Weekly's Ahead, "Tail register: cyber pressure"): each count with its dual percentiles, then the flag. The flag is **ON** when both are at or above their 95th percentile of five years in the same week.
- **What the line is, and is not.** It is a report-only line for the Twenty-Five's cyber family (scenario 13) and item 16, **never a tripwire**: scenario 13 keeps its documented no-tripwire ruling.
- **The cross-reference** prints in the Digital Assets addendum's incidents section (see the differences, 3).
- **The X digest's incidents reference** (item 50) is the same section, which reads the digests: a line, no Drive link.

## Item 78: crypto protocol breadth

- **The writer** (`altdata/protocol_breadth.py`) is a **daily step of the crypto basket's run**, on the freshness roster as `protocols`. It stores two keys, source `defillama`:
  - `defillama.protocols_listed`: neither dead nor deprecated;
  - `defillama.protocols_active`: of those, TVL above zero.
- **Where the count prints:**
  - in the Monthly's digital chapter, as "Digital assets: protocol breadth", after the network-health rows, with the hand count's listed gap;
  - in the Weekly addendum's incidents section, with its history start ("History from <first day> (n daily snapshots): DefiLlama serves today's list only").
- **The monthly hand count** from compiled lists is a listed gap (G3).
- **The base-rate note:** `docs/base-rate-notes/crypto-winters-protocol-shutdowns-2026-10.md` (the folder b55 starts for its LTEG note). It cites a title and URL per claim:
  - TechCrunch for 2018's more than 1,000 failed tokens;
  - crypto.news, on DefiLlama's data, for 2022's DeFi TVL from $180.7bn to $42.7bn;
  - Cointelegraph for 2026's 82 and DefiLlama's own 100.
  - **2022-23's shutdown count is not written:** no source was found. The note's finding is that the three counts are not like for like.
- **No person is named:** the compiled list is "a researcher's".

## The gate

`tools/validate_batch15_2.py`, nine groups, **57/0** locally: synthetic fixtures only, scratch stores, a fake fetch, no network.
- **A.** The TFF net and percentiles by hand.
- **B.** Each gap path.
- **C.** The squeeze flag on, off, not read and at the edge, and its placement.
- **D.** The pre-registration's hash; INSUFFICIENT, PASS and FAIL on fixtures; entry after the release; the first edition; the read-only script.
- **E.** The lab ratios by hand and "no ledger entry"; the disclosure and G3; the IPO watch.
- **F.** KEV's and NVD's weekly counts by hand, the pacing, the joint flag (on, off, not read), the hooks.
- **G.** DefiLlama's counts and the history-start label.
- **H.** The note's citations (every paragraph with a figure carries a URL) and the dated records.
- **I.** The keys and sources registered; the rosters and run steps; no unit; no composite, market-state, register or vendor import; no direct SQL write; no person's name, handle or email; this gate writes no store but its own.

**Registered** in the Makefile's `PY_VALIDATORS`, and CLAUDE.md says one hundred and thirty-five code gates (one hundred and thirty-two Python, three shell).

**Run locally:**

| Gate | Result |
|---|---|
| `validate_batch15_2` | 57/0 |
| `validate_es_block` | 69/0 |
| `validate_digital_addendum` | 94/0 (the 52-line budget holds) |
| `check_registry` | OK |
| `check_library` | 0 failures, 0 warnings |
| `validate_official_sources` | 340/0 |
| `validate_audit_3a` | 88/0 |
| `check_master_guide` | 0/0, after Table 7a's three rows and the HTML rebuilt |
| `validate_st_t5_prl` | 62/0 |
| `validate_basis_proxy` | 31/0 |
| `validate_aq3_series` | 84/0 |
| `validate_crypto_sources` | 117/0 |

The stack gates are left to CI.

## Every listed gap

1. **FINRA short interest as a share of float** for the S&P 500 (74): no constituent list or float source.
2. **A hedge-fund performance proxy** (74): no keyless series (HFR is by subscription).
3. **The prime-book figures as a line** (74, G3): one dated record only.
4. **ES top-of-book depth** (74, via item 71): not tracked; the Amihud stand-in arms the flag.
5. **Quarterly lab-ledger entries after the first** (75, G3): pending the operator's yes.
6. **TTM revenue for the first lab row** (75): not reported, so commitments over TTM revenue is not computed.
7. **The order's "$86bn of chip rental"** (75): not in the cited report, so not entered.
8. **The public S-1** (75): not on EDGAR per reporting; float, index inclusion and lock-ups "not yet public".
9. **CVEs scored only under CVSS v4** (77): not counted (the line counts v3 CRITICAL).
10. **DefiLlama's protocol count before the first pull** (78): no point-in-time history exists.
11. **The monthly hand count of shutdowns** (78, G3).
12. **A 2022-23 protocol-shutdown count** for the note (78): no source found, so it is not written.

## Every session-set value, with its reason

| Value | Setting | Reason |
|---|---|---|
| The flag's arm contract | ES (NQ beside it) | item 45's levels read is ES's |
| The net short measure | the net's share of open interest, negated | the 10A standard: positions scaled to OI compare across years |
| The squeeze thresholds | net short ≥ 90th; Amihud ≥ 90th (depth ≤ 10th) | the ruling's 90th and 10th; the Amihud measure is inverse to depth |
| The percentile windows | five years and the full stored history | the paste and `st_r5_rates.lens` |
| The ledger's ranking window | 260 reports, at least 156 behind | five years of weekly reports; three years before a week is ranked |
| The ledger's episode rule | the first extreme week after at least 4 quiet weeks | "first week of each episode"; a month apart |
| The ledger's entry | the first close on or after the Friday release | no week entered before the market could know it |
| The ledger's pass rule | n ≥ 12; median 20-session lift ≥ 1.0 pp; 60% positive | a modest, two-sided test of the squeeze case, written before the code |
| The cash-burn measure | net loss less non-cash financing charges | the order's "cash burn excluding non-cash financing charges", from what the row holds; labelled |
| KEV's excluded seeding | weeks before 8 Nov 2021 | 287 entries on launch day are a load, not a week's exploitation |
| NVD's severity | CVSS v3 CRITICAL | the ruling's 9.0 or higher, on the version NVD scores most |
| NVD's re-read and provisional weeks | 8 re-read, 4 provisional | scoring lags publication by weeks (check 3) |
| NVD's pacing | 6.5 s between requests | the public limit of 5 in 30 s, with margin |
| The cyber flag | both ≥ 95th of five years, the same week | the ruling's 95th, "in the same week" |
| The cyber feeds' cadence | Saturdays, in the crypto basket's run | weekly counts; no new timer |
| "Active" protocols | neither dead nor deprecated, TVL above zero | a protocol with no locked value is listed, not active; both counts are stored |

## Each new key, its source and its real publication lag (for b51's `config/publication_lags.yaml`)

| Key | Source | Cadence | Lag to add |
|---|---|---|---|
| `cyber.kev_added_week` | `cisa_kev` (new) | weekly, read Saturdays | none: the weekly allowance holds |
| `cyber.nvd_critical_week` | `nvd` (new) | weekly, read Saturdays | none |
| `defillama.protocols_listed`, `defillama.protocols_active` | `defillama` | daily | none |

The ES and NQ rows are existing keys (`cftc.tff_lev_money_*`) under new instruments.

## Where the order and the code differ

1. **"Item 71's depth proxy below its 10th percentile"**: the proxy is an illiquidity measure (higher is less depth), so the arm is the Amihud measure at or above its 90th.
2. **"FINRA short interest as a share of float for the S&P 500 (bimonthly)"** and **"a free hedge-fund performance proxy"**: listed gaps (checks 1b and 1c).
3. **"Cross-references printed in item 51's incidents section"** and **"the DefiLlama count in the Weekly addendum's incidents section"**: the addendum's full fixture week sits at exactly its 52-line budget. So both print in the incidents section's **footnote**, which is printed but outside the line count. Raising the budget is the operator's call (needs-you 2).
4. **"The weekly cyber-pressure line in the tail register"**: no rendered tail register exists in the code. The line prints in the Weekly's Ahead ("what we are watching") under the title "Tail register: cyber pressure". Scenario 13 keeps its no-tripwire ruling, so the flag is a line, not a tripwire.
5. **"Feeding the cyber family"**: the families map (6f) is not built, so the link is the line's label and note, not a mapping.
6. **The hedge-fund line is the Weekly's only**: TFF is weekly, and the Monthly's Positioning keeps its five read blocks (T3.1 item 10), as Batch 5's overnight split does.
7. **"Item 47's AI unit-economics line"**: no such line existed in the code (item 47 is a by-hand yes with no key). The line is new, in Factor I beside SR-16's neocloud and AI-credit lines.
8. **Verify item 8, the leader's health report**: still unverified; the log-only entry is unchanged and nothing is built.
9. **The ledger's first edition is INSUFFICIENT, n 0.** That is the honest result of "stored history only" on a laptop store without ES rows; the box edition follows the first pull.

## Files shared with other branches

| File | a58-batch15-1 (`e219bc8`) | a57-batch14-b1 (`711631b`, merged here) | b55-batch14-b2 (`505d834`) | chain-5 (`6fa2024`, base) | At the merge |
|---|---|---|---|---|---|
| `CLAUDE.md` | ✓ (135 gates) | ✓ | ✓ (134; FRED 278) | — | keep every paragraph; recount once: chain-5's 133 + a57, a58, b55, b56 = **137** if a58 adds one gate (a58 says 135 on chain-5 + a57) |
| `Makefile` | ✓ | ✓ | ✓ | — | keep every gate line |
| `metrics_registry.yaml` | ✓ | ✓ | ✓ | — | splice the new entries and families |
| `config/catalogue_commands.yaml` | ✓ | ✓ | ✓ | — | keep every module line |
| `source_registry.yaml` | ✓ | ✓ | — | — | keep every source |
| `daily_cascade/weekly_stack.py`, `stack_close.py`, `absorption_block.py` | ✓ | ✓ | — | — | keep every hook; in the close, item 71's line, then a58's, then this branch's squeeze line |
| `monthly_macro/stack.py` | ✓ | ✓ | ✓ | — | keep every hook |
| `docs/dated-appendix-queue.md` | ✓ | — | ✓ | — | all append at the end: keep every entry |
| `docs/master-guide.md` and its HTML | ✓ | ✓ | — | — | Table 7a's rows from all; rebuild the HTML with the builder |
| `docs/base-rate-notes/` | — | — | ✓ (the LTEG note) | — | two different files in one folder |

## The CI rounds

| Round | Run | On | Result |
|---|---|---|---|
| 1 | — | — | — |

## Needs you

1. **The box commands, after the merge** (inside the windows; dry runs first). Yes or no to running:
   - the TFF pull, which reads ES's and NQ's history whole: `python -m altdata.sources.cftc`;
   - the NVD backfill: `python -m altdata.cyber_pressure backfill --dry-run`, then without;
   - the first cyber and protocol reads: `python -m altdata.cyber_pressure weekly --force --dry-run`, `python -m altdata.protocol_breadth daily --dry-run`;
   - then the ledger's box edition, outside the checkout: `tools/calibration/st_r6_74b_short_extremes.py --db data/chester.db --out ~/chester-data/ledgers`.
2. **The addendum's line budget:** yes to raising `max_lines` from 52 to 54 so the cyber and protocol cross-references print as body lines, or no to keeping them in the incidents footnote.
3. **Quarterly lab-ledger entries** (G3): yes or no to a by-hand quarterly row per filing lab, entered from each filing with its URL.
4. **ST-R6.74b's first edition** (INSUFFICIENT, n 0, laptop): yes or no to accepting it as the rule-31 draft until the box edition supersedes it.
5. **A hedge-fund performance proxy:** yes or no to adding a keyless replicating ETF (for example QAI) to the basket as a labelled proxy. Today it is a listed gap.
