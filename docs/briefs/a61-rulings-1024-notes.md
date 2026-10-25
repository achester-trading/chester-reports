# A61: the rulings of 24 Oct 2026, filed and the small ones applied (session A)

**Branch-only. Nothing here merges before the 1 Nov Monthly.** The larger builds (D15, D20's build, D26, D27) are other pastes and are not built here.

## Base and commits

- **Base:** `a61-rulings-1024` from `origin/chain-6` at `69cc88d` ("chain-6 notes: a58's third tip (a27ca1d, its notes only) merged as eae6a18"). chain-6 had not moved when the branch was cut.
- **Worktree:** `../chester-a57`.

| Commit | What |
|---|---|
| `93288d4` | docs: the operator's rulings of 24 Oct 2026 (D1-D27). The log, byte for byte, alone. |
| `d5a8b2d` | Index line in `docs/attention-log.md`. |
| `649e59b` | Part 1 (D5): the voices. |
| `4cb25f7` | Part 2 (D13, D22): the five funds; QAI and the performance line; the Security Master; the count pins. |
| `861d3bf` | Part 2 (D17): the CMA table's two medians. |
| `4cf03c0` | Part 2 (D21, D9, D3, D20). |
| `05af21f` | The Master Guide's HTML rebuilt, and these notes. |
| (this) | The notes' commit hashes and the CI run as read. |

## Part 0: the log

- **The file.** `C:\Users\arich\Downloads\rulings-2026-10-24.md` was there (4,528 bytes). It was copied to `docs/briefs/rulings-2026-10-24.md` and checked identical with `cmp`, then committed alone first.
- **The index.** No rulings index exists; the existing minutes (`doctrine-monthly-2026-10-minutes.md`) are indexed in `docs/attention-log.md`. The log is indexed there, with one ruling line dated 2026-10-24 (minutes "—": rulings given in chat are not timed).

## Part 1: the voices (D5, standing: a voices entry names the outlet, never the person; F4 still governs)

1. **Every entry on chain-6 was checked** for a person's name in its name, label or note. That covers `config/voices_sources.yaml` (`sources`, `not_used`, `seeds`, `filers_13f`) and the outlets in `config/source_tiers.yaml`.
   - **Changed (one):** the `not_used` entry "Apollo Academy (Torsten Slok)" is now "Apollo Academy (Apollo Global Management)".
   - **Kept, with reasons:**
     - `filers_13f`'s "GRANTHAM, MAYO, VAN OTTERLOO & CO. LLC" and "PRICE T ROWE ASSOCIATES INC /MD/" are firms' legal names. The scan counts a 13F only when EDGAR's current name equals the string exactly.
     - "T. Rowe Price" (an outlet) and "Yardeni QuickTakes" (a publication, in `not_used` and tier 2) are firms' and publications' names.
   - **Outside the voices register, listed and not changed:** a person's name survives in `altdata/ledgers/st_r5_44b.py` ("via Lemand", a ledger's source line), in a comment in `config/narratives.yaml`, and in the signal-triage register's SR headings, which file the orders' own text. None is a voices entry.
2. **A56's newsletter voice (Batch 14 item 70) is added as the outlet FXEmpire**, because F4's check passes.
   - **robots.txt** (www.fxempire.com, read 24 Oct 2026 with the project's generic User-Agent, HTTP 200) disallows only `/m/`, `/mobile/` and `/members/` for every agent.
   - **The terms of use** (`/terms-of-use`, "Last Revised: March 16, 2026") carry no clause on automated access, scraping or crawling. They forbid reproducing or redistributing the content without approval, so the scan stores the URL, the dates and a one-line paraphrase, never the text, as for Carson Group.
   - **The feed:** `https://www.fxempire.com/api/v1/en/articles/rss/forecasts`. It served 20 dated items without a login.
   - **The entry:** `fxempire_forecasts`, group `news`, method `rss`, with the general outlet's `require_any` words. Its kind is `independent` with the tag "newsletter" in its note, because the vocabulary has no newsletter kind (as for JDI Research's tag). `FXEmpire` is added to `config/source_tiers.yaml` at tier 3.
   - The entry reads the outlet's feed, not the writer's own author page: that page's URL is the writer's name.
3. **A57's Carson Group entry stands as an outlet.** Name, outlet and default voice are "Carson Group", and its comment says "no person is named here". No change.
4. **A58's held entry (Batch 15 item 72): nothing added.** The voices scan already reads Bridgewater's public research page as `bridgewater_research` ("Bridgewater Research & Insights", outlet "Bridgewater Associates", `https://www.bridgewater.com/research-and-insights`, group `desk`, since Phase B on 4 Oct 2026). The reading shelf's 8 Oct order also added a Bridgewater publication. "Bridgewater (public research)" would be a second entry for the same page.

`tools/validate_voices.py`: 72 passed, 0 failed.

## Part 2: the small builds

1. **D13: five ProShares funds.** QID −2, UDOW 3, SDOW −3, URTY 3 and SRTY −3 join `altdata/sources/proshares.py`'s `FUNDS` and `config/fragility.yaml`'s rebalance estimate (`leveraged_etfs.covered`).
   - **Each is in the writer's keyless file** (`accounts.profunds.com/etfdata/ByFund/<TICKER>-historical_nav.csv`, read 24 Oct 2026, each HTTP 200 with a 23 Oct row): QID from 07/11/2006 (5,105 rows), and UDOW, SDOW, URTY and SRTY from 02/09/2010 (4,203 rows each). None is absent.
   - **Gaps.** Their `not_covered` line is removed. Direxion's SPXL/SPXS and TNA/TZA stay listed gaps.
   - **Proxies (session-set).** The Dow funds ride `yfinance.mkt_dia` and the Russell funds `yfinance.mkt_iwm`, the basket's own ETFs for those indices, as the S&P and Nasdaq funds ride SPY and QQQ.
   - **The gate.** a57's `validate_batch14_b1` now checks the five leverages in both places and that only Direxion's four remain gaps.
   - **The Security Master.** SM00216–SM00220 are added; currency and exchange are listed unverified.
2. **D17: two CMA medians.** `altdata/cma_table.py` computes two medians, nominal and real, each with its count of houses and its spread, never mixed.
   - **Basis.** An edition's basis is its scan's `Basis` row, read as the word "real" or "nominal". A basis that is neither is in neither median, and the read says so.
   - **The table.** Each house's cell prints its figure with its own basis and horizon as published, for example "5.0% (nominal, 10 years)". The table ends with Median, nominal / Houses, nominal / Median, real / Houses, real.
   - **Book A's line** reads the nominal US-equity median, or the real one when fewer than two nominal houses have a current edition, labelled which and why.
   - **Session-set:** with one nominal house and no real one, it prints that one nominal house, n=1. The ruling does not name that case.
   - **b55's gate** (`validate_batch14_b2`) is updated by hand:
     - nominal US equity 4.5 (HSBC 5.0, Vanguard 4.0), n=2, spread 1.0;
     - real US equity 4.6 (AQR), n=1;
     - the nominal ex-US gap +2.3 pp;
     - the Book A line nominal 4.5%, and at a 15 Oct cutoff (Vanguard not yet read) real 4.6%, labelled.
   - Result: 57 passed, 0 failed.
3. **D22: QAI.** QAI joins the price basket (`altdata/sources/yfinance_source.py`).
   - **Blocklist.** Not a Brookfield-complex instrument: a57's and b56's gates check the blocklist at write time over the funds and proxies.
   - **The Security Master.** SM00215 is added, with yahoo and store_key; its other facts are null and listed unverified, the same as AIQ and SPXT. `next_id` moves to 221.
   - **Item 74's block** (`altdata/hf_positioning.py`, `config/hf_positioning.yaml`) prints "Hedge-fund performance (QAI, replication proxy)" beside the CFTC line:
     - the week's (5 sessions) and the four weeks' (20 sessions) price return;
     - each with its dual percentiles (five years and the full stored history, each with its n) against every rolling return of the same length;
     - report only.
   - **Unstored**, it prints "not stored yet (its history arrives with the basket's backfill)".
   - **The old gap is gone.** The listed gap "A hedge-fund performance proxy: NOT TRACKED" is removed.
   - **b56's gate** (`validate_batch15_2`, group B) checks the unstored line and a 1,600-session fixture by hand. Result: 60 passed, 0 failed.
   - **The pins moved for the 127th symbol:**
     - `metrics_registry.yaml`: the price and action blocks go to 127, the volume-shares block to 97;
     - `tools/validate_prices.py`: 127 symbols, 107 volume units;
     - `tools/validate_audit_3a.py`: QAI's four keys;
     - CLAUDE.md's repo-layout line, the architecture document's refresh line, and the Master Guide (two places, with its HTML rebuilt).
   - **Price return only:** dividends are stored separately and not added in. Labelled "price return".
4. **D21: item 75's lab ledger takes quarterly rows from filings only.** The template's header (`docs/ledgers/ai-lab-financials-ledger.md`, "Status of entries") and the module docstring now say:
   - each entry is made by a session from a filed document (the S-1 and amendments, a 10-Q, a 10-K or an equivalent public filing) cited by URL, about once a quarter;
   - press reports are never a source;
   - the first Anthropic row stays a provisional dated record until the S-1 is on EDGAR.

   The "listed gap" wording for quarterly entries is removed. No row is added. b56's gate (group E) checks the new wording and that "listed gap" no longer appears.
5. **D24: confirmed, nothing changed.** `config/gold_event.yaml` `central_banks.key` is `imf.ifs.gold_net_purchases_oz.total` and its label is "Central banks' net gold purchases (IMF IFS)".
6. **D9: four rule-31 lines.** The register has no ST-R6 entries, so the lines go under "Rule-31 acceptances outside the SR entries", in the shape of the 19 Oct lines, each with its ledger, verdict and n:
   - ST-R6.66c FAIL, n 65 (b52);
   - ST-R6.65a INSUFFICIENT, n 28 (a57);
   - ST-R6.71d FAIL (a57);
   - ST-R6.74b INSUFFICIENT, n 0 (b56).

   Each line says that nothing prints differently and no right is granted.
7. **D3: one agenda line** in `docs/briefs/doctrine-2-pack-2026-11.md`, under H-2 (SR-9's 5.25% note): the `calc.infl_vol` bridge question. It is an agenda line only, with no draft.
8. **D20: one agenda line**, as W-6 of the same pack, with the paste's wording verbatim.

## Rulings not applied here, and why

- **Other pastes (built elsewhere):** D15 (the one-day 10-year trigger), D20's build, D26 (the new sources) and D27 (6f).
- **Box, chat-side or already done; no edit on chain-6 is asked:** D1, D2, D4, D6, D7, D8, D10, D11, D12, D14, D16, D18, D19, D23 and D25, and the CHESTER_SEC_CONTACT line. D23 matches A58's notes already: the item 76 gap and the dated records stay.

## Where the ruling and the code differ

1. **D5 item 4.** The ruling says "A58 Dalio -> 'Bridgewater (public research)'". The scan already reads that page, so per the paste's own condition nothing is added. The firm is on file as "Bridgewater Associates".
2. **D5 item 2.** The FXEmpire entry reads the outlet's forecasts feed, not the writer's own pages. Its tier (3) and its `require_any` filter are session-set.
3. **D9.** The paste asks for the lines in the shape of the 19 Oct lines. Those sit under SR entries, and these four items have no SR entry, so the lines use the section the register keeps for that case.
4. **D13.** "The rebalance estimate and its gate pick them up". The estimate needed one line per fund in `config/fragility.yaml` (with its index proxy), and the gate's gap check had to change, because it asserted the five were gaps.
5. **D22.** "Its history arrives with the basket's backfill": QAI needs `tools/backfill_prices.py` (below). The five ProShares funds' history arrives on the writer's next pull, which reads each file from inception.

## Local gates (Part 3)

| Gate | Result |
|---|---|
| validate_batch14_b1 (a57; the leveraged-ETF gate) | 68 / 0 |
| validate_batch14_b2 (b55; the CMA gate) | 57 / 0 |
| validate_batch15_2 (b56) | 60 / 0 |
| validate_batch15_1 (a58) | 69 / 1 locally; the one is the Windows checkout, see below |
| validate_voices | 72 / 0 |
| validate_prices | 101 / 0 |
| validate_security_master | 102 / 0 |
| validate_audit_3a | 88 / 0 |
| check_registry | OK |
| check_library | 27 papers, 0 failures, 0 warnings |

**The one local failure is not a code fault.** `validate_batch15_1`'s check "the Batch 15 order is on file at its SHA-256" fails on this laptop because `core.autocrlf=true` checks the order out with CRLF (sha256 15f9ae19…). The blob in git is the filed bytes (sha256 d5318a6d…), and CI checks out LF. No file of this branch touches the order. The gate count is unchanged: no gate is added, so CLAUDE.md's gate line is not recounted.

## The CI run

| Run | On | Result |
|---|---|---|
| 40112619226 | `05af21f` | in progress when read once (24 Oct, about 12:40 ET); the result was not read in this session. Read it with `gh run list --branch a61-rulings-1024 --limit 3` |

## The box commands (the operator's; after the merge, which is after the 1 Nov Monthly)

```
# QAI's history (item 74's performance line reads nothing until it lands):
.venv/bin/python tools/backfill_prices.py --symbols QAI --years 8 --dry-run
.venv/bin/python tools/backfill_prices.py --symbols QAI --years 8
# The five ProShares funds' history: the next EOD pass's ProShares pull reads each
# file from inception; to take it at once:
.venv/bin/python -m altdata.sources.proshares
```

## Files shared with other branches

| Branch | Shared files |
|---|---|
| b56 (`b56-batch15-2`, on chain-6) | `altdata/hf_positioning.py`, `config/hf_positioning.yaml`, `tools/validate_batch15_2.py`, `altdata/ai_lab_ledger.py`, `docs/ledgers/ai-lab-financials-ledger.md` |
| b55 (`b55-batch14-b2`) | `altdata/cma_table.py`, `config/cma_table.yaml`, `tools/validate_batch14_b2.py` |
| a57 (`a57-batch14-b1`) | `config/fragility.yaml`, `tools/validate_batch14_b1.py`, `config/voices_sources.yaml` and `config/source_tiers.yaml` (the Carson Group block's neighbours) |
| a58 (`a58-batch15-1`) | none changed (D24 was a check) |
| chain-6, every later branch | `altdata/sources/yfinance_source.py`, `altdata/sources/proshares.py`, `config/security_master.yaml` (SM00215–SM00220, `next_id` 221), `metrics_registry.yaml`, `tools/validate_prices.py`, `tools/validate_audit_3a.py`, CLAUDE.md, the architecture document, `docs/master-guide.md` and its HTML, `docs/signal-triage-register.md`, `docs/briefs/doctrine-2-pack-2026-11.md`, `docs/attention-log.md` |

## Needs you (at most five; yes or no each)

1. **FXEmpire at tier 3**, read through the outlet's forecasts feed with the general-outlet filter (stored and shown, never counted toward attention or a consensus)? Yes / no.
2. **D17's unnamed case:** with one nominal house current and no real one, Book A's line prints that one nominal house (n=1, labelled). Yes / no.
3. **The Security Master ids:** SM00215 (QAI) and SM00216–SM00220 (the five funds), `next_id` 221. Any other branch cut from chain-6 that adds an instrument must take from 221, or the stitch renumbers. Yes / no.
4. **D13's index proxies:** DIA for the Dow funds and IWM for the Russell funds. Yes / no.
5. **The box commands above,** after the merge: QAI's backfill, dry run first. Yes / no.
