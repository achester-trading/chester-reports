# st-r5-audit — session notes (session A, 16 Oct 2026)

**What this branch builds on.** It is cut from the tip of `st-r5-fixes` (`278a1c9`, its CI fix), so it carries session A's whole line: `st-r5-rates`, `st-r5-index`, `st-r5-t1-rest` and `st-r5-fixes`. **It merges after `st-r5-fixes`, in this order:** the chain, then `st-r5-rates`, `st-r5-index`, `st-r5-t1-rest`, `st-r5-fixes`, then this branch.

It is branch-only. Nothing was merged or deployed, and nothing ran on the box. Session B's `6e-rest` and `6e-releases`, every branch on the Friday list, and Monday's chain are untouched.

The branch has three parts:
1. **The by-hand audit**, ruled 16 Oct.
2. **SR-30's daily French yield**, read keyless. The Italian yield stays monthly.
3. **A home for the Warsh-matrix lines.**

## Step 0

- **`st-r5-fixes` CI.**
  - **Run 38974652897** (on `ce6cf33`) failed, with 93 of 95 jobs green. The cause was `check_library` failure [10]: the HTML editions of Base Rates, Equities and Metals were stale against the papers' new appendices. The second failed job was `gates-passed`, which only reports that.
  - **The fix is `278a1c9`.** It rebuilds the three editions with `tools/build_paper_html.py`; no paper text changed. Its run, **38990099325**, is **green**.
  - The fixes notes record both runs, and point here for the second.
- **`sm-schema-1-1`** is now recorded in the fixes notes, under its own heading:
  - what it is: Security Master export schema 1.1, with `restricted` and `restricted_reason`, and the new-listing start-date ruling;
  - its base, `origin/aud-3b-security-master` `2fb1048`;
  - its tip, `6c8c666`;
  - its CI, run 38970887891, green.

## The rulings of 16 October this branch applies

- **(a) Prefer public, easy-to-access sources.** Friction is a gap, not a key. That rules out the Banque de France Webstat key, the Bank of Korea (ECOS) key and the Bank of Thailand key.
- **(b) No recurring by-hand data line survives without Ari's explicit yes.**
  - There are two yeses so far: the global PMI headline (Batch 6 item 43) and item 47's quarterly AI unit-economics line (Batch 7).
  - The S&P DJI estimates workbook is pending (its public link answered 404 on 16 Oct). Nothing about it changes here.
- **(c) Judgment drafts are committed as drafted** and listed for Ari's accept-all.
- **(d) The blocklist may be strengthened, never weakened.** This branch does not touch it.

## Part 1 — the by-hand audit

### How each verdict was reached

Every source named below was probed from the laptop with the repo's own agent (`chester-reports/1.0`). Its robots.txt was read first with the wildcard-aware reader, and nothing was registered for.

- **AUTOMATE:** a free source reads within robots, with no key or with a key Ari already holds. The reader is built when it takes under an hour; otherwise it is listed with an estimate.
- **DROP:** no such source exists. The line prints "not tracked" with the reason, and the key is removed.
- **KEEP:** only for the two explicit yeses.

**A key whose automation is listed but not built is removed too.** Under ruling (b), no by-hand line waits for its reader. Where something printed from the key, it now prints "not tracked" until the reader exists. Most of the dropped keys were registered but read by nothing.

### The audit table

**The manual_input keys** (`tools/manual_input.py` and the registry):

| Item | What it feeds | Cadence | The source a human would read | Verdict | Reason |
|---|---|---|---|---|---|
| `manual.global_pmi` | ST-R5.43a, the global PMI headline beside the diffusion index | monthly | S&P Global's J.P.Morgan Global Manufacturing PMI release | **KEEP** | Ari's yes (Batch 6 item 43). Automation is also closed: pmi.spglobal.com answers this agent with 403, robots.txt included. |
| `manual.sep_median_next2` | SR-21's Fed–market gap (`calc.fed_mkt_gap_m1/_m2`, unbuilt); nothing read the key | quarterly, at each SEP | the Fed's SEP tables | **AUTOMATE** (listed, about 1.5 h) | FRED, whose key Ari holds, publishes the SEP median as FEDTARMD, one value per projection year, revised each SEP. The reader maps the current and next year-ends, with ALFRED vintages. Not built: over an hour, and no reader waits. |
| `manual.sep_median_12m` | SR-21, `calc.fed_mkt_gap_12m` (unbuilt) | quarterly | the Fed's SEP tables | **AUTOMATE** (listed, with the row above) | Same as the row above. |
| `manual.fedwatch_next_meeting_prob` | SR-21's headline object | daily | CME FedWatch | **AUTOMATE** (exists) | The prediction-market writer already pulls Kalshi's FOMC decision markets (`config/prediction_markets.yaml`, `fomc_decision`, series KXFEDDECISION). CME FedWatch has no free API (G-4). |
| `manual.cbo_deficit_path` | SR-23's projection input; GTM-12 | at each CBO baseline | CBO's budget projections | **DROP** | cbo.gov answers this agent with 403, robots.txt included (checked 16 Oct 2026). |
| `manual.ig_nic_median_bp` | SR-16's absorption price | quarterly | Bloomberg | **DROP** | Bloomberg-only; no free source. |
| `manual.ig_cover_median` | SR-16 | quarterly | Bloomberg | **DROP** | Bloomberg-only; no free source. |
| `manual.aaii_stocks_pct` | ST-R5.30a's allocation line (SR-12) | monthly | AAII's asset-allocation survey | **DROP** | aaii.com answers this agent with 403, robots.txt included, and a writer never passes for a browser. The line now prints "AAII asset-allocation survey: not tracked" with the reason. |
| `manual.aaii_bonds_pct` | ST-R5.30a | monthly | AAII | **DROP** | Same as the row above. |
| `manual.aaii_cash_pct` | ST-R5.30a | monthly | AAII | **DROP** | Same as the row above. |
| `manual.msci_em_usd` | SR-14; the Quarterly's EM chapter | monthly | MSCI end-of-day data | **DROP** | msci.com's robots.txt disallows `/en`, its index pages. The Quarterly row prints "not tracked", and EEM, already stored, prints beside it. |
| `manual.msci_em_local` | SR-14; the Quarterly's EM chapter | monthly | MSCI | **DROP** | Same as the row above. |
| `manual.msci_world_usd` | SR-14's DM leg; the Quarterly's EM and international chapters | monthly | MSCI | **DROP** | Same as the row above. |
| `manual.msci_acwi_exus_usd` | the Quarterly's international chapter | monthly | MSCI | **DROP** | Same as the row above. |
| `manual.oecd_days_cover` | SR-18 | monthly | the IEA's Oil Market Report | **DROP** | iea.org answers this agent with 403 behind a bot challenge, robots.txt included. The full report is by subscription. |
| `manual.global_visible_stocks_bbl` | SR-18 | monthly | JPMorgan's figure (G-17) | **DROP** | Not free (G-17). |
| `manual.cofer_usd_share` | SR-20's scorecard; nothing read the key | quarterly | IMF COFER | **AUTOMATE** (listed, about 1 h) | The IMF's SDMX 3.0 API is keyless; `altdata/sources/_imf_sdmx.py` already reads IFS through it. The COFER dataflow's key is confirmed at build. |
| `manual.cofer_usd_share_constant_fx` | the Quarterly dollar chapter's row | quarterly | an ECB or IMF report's calculation | **DROP** | No published series. The row prints "not tracked". |
| `manual.gold_share_total_reserves` | the Quarterly's sovereign gold-share analysis; SR-20 | quarterly | WGC (login-gated, G-34) or IMF IFS | **AUTOMATE** (listed, about 1.5 h) | IMF IFS is keyless; whether its world aggregate carries gold at market value is verified at build. The analysis now "waits", with that reason. |
| `manual.mu_hbm_share` | SR-25 | quarterly | TrendForce | **DROP** | Paid research; no free series. |
| `manual.dram_contract_dir` | SR-25 | monthly | TrendForce's DRAM price page | **AUTOMATE** (listed, about 1.5 h) | trendforce.com/price/dram loads for this agent and its robots.txt has no rule over it. **Its terms are read before any build;** if they forbid a writer, the verdict becomes DROP. |
| `manual.g4_issuance_gap_gdp` | SR-23 | annual | Lustig's published figure | **DROP** | A figure in a paper, not a series. It stays a citation, which is judgment, not data. |
| `manual.panda_bond_issuance` | SR-4; the Quarterly's China row | monthly | ChinaBond and PBoC releases | **DROP** | No free machine-readable series is known. **Not probed further in this paste.** The row prints "not tracked". |
| `manual.state_bank_dollar_selling` | SR-4's devaluation tell, third leg; the Quarterly's China row | as reported | press reports (G-21) | **DROP** | A reading of press reports, not a series. The row prints "not tracked". |

**The change orders' by-hand data lines with no key.** These come from the by-hand cadence sections and work lines of:
- the 25 Sep order;
- Batches 3 to 7;
- the Alpha Lab, crypto, Quarterly and JPM GTM orders.

| Item | What it feeds | Cadence | The source a human would read | Verdict | Reason |
|---|---|---|---|---|---|
| Item 47, AI unit economics (Batch 7) | Factor I | quarterly | Epoch AI, plus the token-volume and revenue proxies | **KEEP** | Ari's yes (Batch 7). Epoch's data page loads for this agent and robots allows it, so the constant-capability cost series may automate later. Not tested beyond that. |
| UK CPI, headline and core (Batch 6 item 39's gap) | ST-R5.39a's UK real yield | monthly | ONS MM23 | **AUTOMATE** (built) | `altdata/sources/ons_cpi.py`. |
| Canada CPI, headline and core (item 39's gap) | ST-R5.39a's Canada real yield | monthly | Statistics Canada, table 18-10-0004-01 | **AUTOMATE** (built) | `altdata/sources/statcan_cpi.py`. |
| Korea 2-year (ST-R5.34b's G8 panel) | the market-does-the-tightening panel | daily | KOFIA's bond service; the BoK's ECOS | **DROP** | The ECOS key is ruled out by (a). KOFIA's site is a script-driven frameset with no export URL a writer can read. The panel's gap reason now says so (`config/st_r5_rates.yaml`). |
| NAR pending home sales index (items 36 and 37) | ST-R5.36a's housing confirm | monthly | NAR's monthly release | **AUTOMATE** (listed, about 1.5 h) | nar.realtor's robots.txt allows it, but the index level is only in the newsroom release's prose, linked from the PHS page. A reader must find the newest release and parse a sentence, which is over an hour with its gate. Housing stays Redfin alone, labelled single-source, until then. The key was dropped on `st-r5-fixes`. |
| SR-29, bitcoin long-term-holder supply (25 Sep; crypto D-8) | the SR-29 scorecard row | monthly | paid on-chain data | **AUTOMATE** (listed, about 1 h; CD-12) | bitcoin-data.com serves `/v1/long-term-hodler-supply-btc` and `/v1/supply-current` with no key, and its robots.txt answers 404 (no rules). It is CD-12 in the crypto order's Tranche C, not built here. |
| DS-21, the token-unlock schedules' quarterly page check (crypto) | the book's next-90-day unlock table | quarterly | DefiLlama's unlocks page | **DROP** | DefiLlama's `/emissions` API is Pro (`altdata/sources/llama.py`). The schedules seeded from project documents stay as dated reference; the quarterly re-read by hand ends. |
| Item 16, exposed-key supply share (Batch 5) | the cryptographic-fragility tail entry | quarterly | on-chain analytics | **DROP** | No free series is known. |
| Item 21, the sovereign fragility scorecard's data columns (Batch 5) | Factor IV, slow layers | quarterly | the IMF Fiscal Monitor and the OECD | **AUTOMATE** (listed, about 3 h; partial) | The IMF's keyless SDMX serves the Fiscal Monitor's GFN, primary balance and interest columns (to confirm at build). Weighted average maturity and the foreign-held share have no free cross-country series, so they stay gaps. The scorecard is session B's (item 21). |
| Item 26, capex-guidance revisions (Batch 5) | Factor I | quarterly | earnings calls | **DROP** | Guidance lives in call transcripts, which are not free. Factor I keeps reported capex from EDGAR. |
| Item 28, the CDS 2014/2003 basis (Batch 5) | SR-30 | when reported | dealers' CDS quotes | **DROP** | CDS data are proprietary. |
| Item 28, Japanese OAT holdings (Batch 5) | the slow-money family | quarterly | Japan MoF and BoJ regional tables | **DROP** | No free quarterly series by issuer country is known. **Not probed further in this paste.** |
| Item 33, the AI Big 10's normalised-margin multiple (Batch 6) | Equities, the semiconductor fulcrum | quarterly | filings and prices | **AUTOMATE** (listed, about 2 h) | Computable from stored EDGAR fundamentals and closes; no outside source is needed. |
| Item 33, analysts' buy-rating share (Batch 6) | a sentiment line | — | consensus vendors | **DROP** | No free source; the order says drop if none. |
| Item 37, the MBA level, and item 41, euro CCC (Batch 6) | ST-R5.37a; ST-R5.41a | weekly; when reported | MBA members' file; public reporting | **DROP** | Done on `st-r5-fixes`: the level is chained from the weekly changes, and euro high yield prints as the labelled proxy. |
| Item 39, the scorecard's real-yield column (Batch 6) | item 21's scorecard | quarterly | — | **AUTOMATE** (exists) | The t1-rest real-yield panel computes it, now including the UK and Canada. |
| Item 45, FlashAlpha levels in the interim (Batch 6) | the ES block | daily | FlashAlpha, whose key Ari holds | **AUTOMATE** (planned) | It ends when the self-computed dealer engine (6b) is live (ST-R6.45c). |
| GTM-6, the HY rating mix (JPM GTM) | the credit twin | quarterly | ICE index constituents | **DROP** | Licensed. |
| GTM-12, the CBO debt path (JPM GTM) | Factor IV | at each CBO update | CBO | **DROP** | As `manual.cbo_deficit_path`. |
| World equity capitalisation (item 38) | the gold/equity ratio | quarterly | WFE (login), MSCI (PDF) | **DROP** | Done on `st-r5-fixes`. It prints "not tracked: no free source for world equity capitalisation". |
| S&P DJI estimates workbook (item 40, SR-38) | the forward earnings legs | weekly | the operator's drop | **unchanged** | Pending by ruling (b): a decision still open. |
| The AAII sentiment survey, weekly (T2.7) | W9's bull-bear spread | weekly | the chat-side "AAII weekly read" task | **unchanged** | A scheduled task, not a by-hand line. |

**Judgment items, not data inputs, left as they are under ruling (c):**
- the Warsh-matrix lines and disagreement pairs;
- base-rate notes and rows, and the Doctrine notes;
- tail-register edits;
- narrative intensities and voices entries;
- the Quarterly's theses and political notes;
- the China and Thailand political calendars;
- the Mechanism Watch reviews;
- the Factor I revenue-leg log;
- SR-20's holder-split tags and SR-21's statement bias;
- item 20's signpost;
- GTM-4's bucket definitions.

**One to confirm.** The EM calendar (`config/em_calendar.yaml`: elections, IMF reviews, central-bank meetings) holds event dates, not judgments. It is classed here as reference seeded by hand, not as a data line. It is empty today. Say if it should be audited as data. Needs-you 4.

### What changed

- **Keys removed: 23**, from the registry's metrics, families and long windows. Only `manual.global_pmi` is left in `tools/manual_input.py`, whose docstring now states the rule.
- **The lines those keys fed:**
  - the Quarterly's eight rows (MSCI ×5, COFER constant-currency, panda bonds, state-bank dollar selling) print "not tracked (by-hand audit, 16 Oct 2026): <reason>";
  - the sovereign gold-share analysis waits, with its reason;
  - the allocation block prints AAII as a listed gap beside ICI;
  - the numeral audit's units table drops the visible-stocks entry.
- **Gates that pinned the keys:**
  - `validate_official_sources` group J now holds the CLI on `manual.global_pmi`. It refuses a dropped key, and holds the fraction and label rules on synthetic keys (they stay for the next ruled key). Group P holds the 17 ST-2 keys gone.
  - `validate_audit_3a`: `DROPPED_BY_HAND` names the 23. They are gone on purpose, not "lost", and each was a key `fb67bf3` resolved.
- **Leftover wording fixed:** the rates-transmission table note still said "the MBA level and NAR's index are entered by hand". It now says Redfin alone, the MBA level chained, and nothing by hand.
- **Readers built, two:** see the next section.

### Readers built

1. **`altdata/sources/ons_cpi.py`** writes `uk.cpi_yoy` (D7G7) and `uk.cpi_core_yoy` (DKO8, the ONS's core: excluding energy, food, alcohol and tobacco).
   - **Source:** the ONS series pages' CSV download.
   - **Robots:** robots.txt answers 404, which is no rules under RFC 9309. The new shared helper `pub.robots_allows()` reads it each run and stops on a disallow, or on any other failure to read it.
   - **Stamp:** every row is stamped at the file's stated release date, 07:00 UK.
   - **Refuses:** another CDID, another unit, no release date, a release date in the future, or no monthly row.
   - **On the live file (16 Oct):** August 2026 reads 3.1% headline and 2.6% core.
2. **`altdata/sources/statcan_cpi.py`** writes `ca.cpi_yoy` (v41690973) and `ca.cpi_core_yoy` (v41691233, all-items excluding food and energy).
   - **Source:** one keyless WDS GET.
   - **Stamp:** each point carries its own `releaseTime`, a true first-publication stamp; the year-on-year row takes the later of its two months.
   - **Refuses:** a missing vector, another vector, or a vector with no point.
   - **On the live data:** August 2026 reads 3.0% headline and 2.1% core.
3. **Both feed the real-yield panel.** In `config/st_r5_t1_rest.yaml`, the UK and Canada rows read `core_yoy` and `headline_yoy`, so neither is a CPI gap any more.
4. **Registration:** both are on `feeds.EXTERNAL_WRITERS`, registered (sources A0, live; four keys with families and long windows), and named in the catalogue.

## Part 2 — SR-30's daily OAT and BTP yields

### The paths tried, in the order given

**French 10-year:**
1. **Webstat's own export links (webstat.banque-france.fr). Reads, keyless.**
   - robots.txt is "Allow: /".
   - The catalogue API (`/api/explore/v2.1/catalog/datasets`) answers anonymously. It holds one dataset per series, but no records, so the observations are not there.
   - Each series page's export path does serve the data: `/export/csv/fr/catalogue/FM/FM.D.FR.EUR.FR2.BB.FRMOYTEC10.HSTA`. That is the daily TEC 10 (the constant-maturity 10-year), from 3 Nov 2004 to 16 Oct 2026, 5,620 days, with each row's `updated_at`.
   - Webstat's API proper, the one that needs the ruled-out key, is not used.
2. **data.gouv.fr.** Its search finds no dataset for TEC 10 or OAT under those names. Its "Banque de France : Webstat" organisation republishes Webstat's FM dataset, as resource "Ressource FM" → `webstat.banque-france.fr/export/csv/fr/catalogue/fm`. That is the same export (54 MB, every FM series). So data.gouv leads back to path 1, and the reader takes the single series.

**Italian 10-year:**
1. **The Banca d'Italia's statistical database (infostat.bancaditalia.it).** It is reachable, and its robots.txt answers 404. But it is a stateful servlet portal (`home?calltype=asin&service=…`) with no export URL. No SDMX endpoint answered: `infostat…/sdmx/rest` gave 404, and `sdmx.bancaditalia.it` does not resolve. **No keyless path.**
2. **The Treasury (MEF, dt.mef.gov.it).** Its robots.txt answers 403 ("Access Denied"), so its rules cannot be read, and a writer does not guess. Its key-interest-rates page carries only a yearly PDF. **No keyless path.**
3. **Webstat's FM export** carries a daily series only for France. Italy is monthly there too.

### What was built

**`altdata/sources/bdf_webstat.py`** writes `bdf.oat_tec10`, daily.
- **Read by column name;** a file carrying another series, missing a column, or with no row is refused.
- **Stamped at each row's `updated_at`** (`observed`): the publication itself for current days, about 11:00–13:00 UTC the same day. History reloaded on 2 Dec 2024 carries that instant, later than the truth, and a revision carries its own instant, never backdated.
- **Registration:** on `feeds.EXTERNAL_WRITERS`, a registered source (A0, live) and in the catalogue.

**The tiers** (`altdata/batch3.py`, `config/batch3_tranche_a.yaml` `eu_stress.daily`):
- **OAT–Bund reads daily** when both daily legs are stored: `bdf.oat_tec10` less `bbk.bund_10y`.
- **Its percentiles** are over the daily series.
- **Its tier sits on the latest weekly close**: the last stored day of the latest ISO week whose Friday has passed, as ruled 13 Oct and in Batch 5 item 28. A Wednesday above the line prints its level, and the tier moves only when the week closes.
- **The lines:** watch at 150 bp. Crisis at **208.1 bp**, the daily series' own November 2011 peak (17 Nov 2011; 167.1 bp on the 15th and 162.0 on the 16th), computed on 16 Oct 2026 from both publishers' files. `crisis_level_daily()` recomputes it from the store after the first pull.
- **The Monthly's "what doesn't fit" sentence** prints at the crisis tier only, naming the weekly close.
- **BTP–Bund stays the ECB's monthly average**, labelled and untiered. The table note says that no keyless daily Italian 10-year was found.
- **The fallback:** without the daily legs, OAT–Bund falls back to the ECB monthly series, labelled and untiered, as before.
- **The basis:** an interpolated constant-maturity yield less the Bundesbank's fitted zero-coupon 10-year. It is neither benchmark screen's, which is why the crisis line is the series' own and not the entry's ~190 bp. Needs-you 3.

## Part 3 — the Warsh-matrix lines

**`docs/warsh-matrix-lines.md`** is new, in the shape of `docs/narrative-register-pairs.md`. Each entry carries:
- the item, dated;
- the scenario in one sentence;
- the weighting it suggests;
- the measure that adjudicates it.

The entries:
- **Item 34** (market does the tightening), adjudicated by ST-R5.34a's flag with the NFCI. No draft existed anywhere, so it is drafted here.
- **Item 42** (inflation expectations turning up), adjudicated by ST-R5.42a's composite against item 34's flag. It is moved from the t1-rest notes, which now point to the file; the fixes notes say it moved.
- **Item 46:** a placeholder heading for session B.

The file is listed below for accept-all.

## Drafts committed, for Ari's accept-all

| Draft | File | Lines |
|---|---|---|
| Item 34's Warsh-matrix line (new draft) | `docs/warsh-matrix-lines.md` | 14–19 |
| Item 42's Warsh-matrix line (moved, substance unchanged) | `docs/warsh-matrix-lines.md` | 21–28 |
| CLAUDE.md standing rule 3, the by-hand rule (the paste's wording, with its context) | `CLAUDE.md` | 740–752 |

## Gates

**Run locally, one at a time, only those written or changed here. Each passed.**

| Gate | Result |
|---|---|
| `tools/validate_batch3_a.py` (B daily: the weekly-close tiers on 149/151/208.1 bp, the Wednesday above the line, the monthly fallback, BTP–Bund monthly, the Webstat parser and its refusals) | 77 passed, 0 failed |
| `tools/validate_st_r5_t1_rest.py` (the ONS and Statistics Canada readers with their refusals, robots, the 404 rule and pulls into a temporary store; the UK and Canada real yields; the registry and catalogue) | 103 passed, 0 failed |
| `tools/validate_st_r5_index.py` (AAII a listed gap; no AAII key read) | 57 passed, 0 failed |
| `tools/validate_st_r5_rates.py` (unchanged checks over the edited config and table note) | 72 passed, 0 failed |
| `tools/validate_official_sources.py` (J: the CLI on the one key, a dropped key refused, the synthetic unit rules; P: the 17 gone) | 288 passed, 0 failed |
| `tools/validate_audit_3a.py` (`DROPPED_BY_HAND`; the gate count CLAUDE.md prints) | 84 passed, 0 failed |
| `tools/validate_deploy.py` (F: CLAUDE.md's standing rules carry the by-hand rule word for word) | 154 passed, 0 failed |
| `tools/validate_by_hand_audit.py` (new: A, the one key and the 23 gone with nothing reading them; B, each line's reason; C, this table's verdicts; D, the Warsh file) | 17 passed, 0 failed |

**The new gate is in the Makefile,** and CLAUDE.md's count moves to eighty-eight code gates (eighty-five Python).

**Left to CI:** every other gate, including:
- `check_library`, which checks CLAUDE.md's new paths and the two new docs files;
- `validate_aq3_series` and `validate_weekly_complete`, which walk the writer roster;
- the quarterly and monthly stack gates, which read `config/quarterly_chapters.yaml`;
- anything that renders a PDF.

No gate reads the live store, fetches or calls a model.

## CI

| Run | Commit | Result |
|---|---|---|
| (first push) | — | recorded at the next read |

## Box commands (Ari's, after the merge, inside a window: weekdays 09:05–15:40 or 17:20–23:30 ET, never 16:00–17:20, clear of Sunday 05:00)

```
cd ~/chester-reports
.venv/bin/python -m altdata.sources.ons_cpi
.venv/bin/python -m altdata.sources.statcan_cpi
.venv/bin/python -m altdata.sources.bdf_webstat
```

- **Each prints its summary.** OK with the rows written is a success; STALE carries its reason.
- **The first pull takes each series' whole history:**
  - the ONS, monthly from 1989, two series;
  - Statistics Canada, from 1991, the first year with a year-earlier month;
  - Webstat, daily from Nov 2004.
- **After that, the three ride the existing external pull.** No unit changes.
- **After the Webstat pull, optionally confirm the crisis line from the store:**
  ```
  .venv/bin/python -c "from altdata import batch3, observations; st = observations.ObservationStore(); print(batch3.crisis_level_daily(st, '2026-12-31', {'fr': 'bdf.oat_tec10', 'de': 'bbk.bund_10y'}))"
  ```
  It should print 208.1. A different figure means the config line follows the store, and the session sets it.

## Files shared with the open branches

| Branch | Shared files |
|---|---|
| `st-r4-tranche-1b`, `st-r4-tranche-1` (session B) | `altdata/batch3.py`, `config/batch3_tranche_a.yaml`, `tools/validate_batch3_a.py`, `altdata/feeds.py`, `metrics_registry.yaml`, `source_registry.yaml`, `config/catalogue_commands.yaml`, `tools/validate_audit_3a.py`, `CLAUDE.md`, `Makefile` |
| `6e-rest` (session B) | `CLAUDE.md`, `Makefile`, `config/catalogue_commands.yaml`, `metrics_registry.yaml`, `tools/validate_audit_3a.py` |
| `6e-metric-lenses` | `CLAUDE.md`, `Makefile`, `metrics_registry.yaml` |
| `st-r6-es-block` | `CLAUDE.md`, `Makefile`, `config/catalogue_commands.yaml` |
| `sm-schema-1-1` | `CLAUDE.md` |

- **`6e-releases` is not on origin yet,** so it could not be compared.
- **SR-30 at stitching, with session B's Greece–Bund:**
  - `st-r4-tranche-1b` adds a monthly Greece–Bund pair to `EU_PAIRS`, untiered, with a comment that mentions `tiers_live`.
  - This branch removes `tiers_live`: the tier is now live exactly when OAT–Bund reads daily.
  - Greece–Bund has no `eu_stress.daily` entry, so it stays monthly and untiered under this code. Only B's comment and B's `tiers_live` test need the new wording.
- **CLAUDE.md's gate count** moves on several branches; the last to merge sets it.
- **The registry, catalogue and source files** take additive, separate blocks.

## Needs you

1. **Accept-all on the three drafts above** (ruling (c)).
2. **The box commands above,** after the merge, inside a window.
3. **SR-30's daily crisis line.** It is 208.1 bp, the daily series' own November 2011 peak, as decision 2 rules for the stored series. The entry's ~190 bp was the benchmark screen's close, and this basis (TEC 10 less the fitted Bund) reads one spiky day higher. Say if you want 190 kept instead.
4. **The EM calendar's class.** It is classed as reference seeded by hand, and it is empty. Say if it should be audited as a data line.
5. **The listed automations,** each a session's work. Say which to queue:
   - the SEP median from FRED, about 1.5 h;
   - COFER from the IMF, about 1 h;
   - the gold share from IMF IFS, about 1.5 h;
   - DRAM direction from TrendForce, about 1.5 h, after its terms are read;
   - NAR's PHSI from the newsroom release, about 1.5 h;
   - SR-29 from bitcoin-data.com, about 1 h (CD-12);
   - the item-21 scorecard columns from the IMF Fiscal Monitor, about 3 h (session B's item);
   - item 33's normalised multiple from stored fundamentals, about 2 h.
6. **The Emerging Markets paper names three dropped keys** (`docs/whitepapers/emerging-markets-whitepaper.md`, lines 467, 474 and 519; T1's falsification test reads MSCI EM over MSCI World). This branch does not edit papers. The library session rewords T1 against the stored EEM/ACWX ratio, or marks it not tracked.
