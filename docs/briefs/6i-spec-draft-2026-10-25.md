# 6i: report completions (the T&B harness, the Themes refresh, the Alt Asset fetchers) — specification DRAFT

**Status: DRAFT for the operator's ruling.** Written 24–25 Oct 2026 (session B, B63) on branch `b63-6i-brief` from `origin/chain-7` (`62c19b4`). Docs only: no code, config or register is changed. Audit #3 names 6i in its Phase 4 row: "T&B harness with the extended episode set · Themes refresh automated for the Quarterly · Alt Asset live fetchers | 10 | Phase 4" (`docs/chester-reports-audit-3.md`, the 6i row). Workplan v7 places "the Quarterly Structural and the 6i brief" in the week of 2 Nov (`docs/workplan-v7-2026-10-16.md`).

**Sources read.**
- **Code and config:** `monthly_macro/payload.py` (`top_bottom_block`), `monthly_macro/stack.py` (the slow layers' Themes line), `monthly_macro/quarterly.py`, `config/quarterly_chapters.yaml`, `config/alt_asset_gaps.yaml`, `config/tb_intake_queue.yaml`, `config/tb_false_bottom_gate.yaml`, `state/emit.py`, `metrics_registry.yaml`, `altdata/config.py`, `altdata/sources/yfinance_source.py`, `deploy/systemd/chester-quarterly.timer`. All of it as it stands on chain-7.
- **Docs and orders:** the architecture's Part 23 (the Top & Bottom build log of 3 Sep), Part 28.3 and 28.4 (the Themes pipeline and the Alt Asset completion), Part 31 (the library additions) and Sessions 10–11; Audit #3's outputs table; the automation addendum; the Alternative Assets Quarterly change order of 10 Oct; the AQ-3 build notes, parts 1 and 2; the false-bottom audit ledger (`docs/ledgers/false-bottom-audit-2026.md`); the signal-triage order of 25 Sep (its section 1.7); `docs/scheduled-tasks.md`.
- **Library, read only:** Tops and Bottoms, Base Rates, the Operating Doctrine. No paper was edited.

**Where the code and a document differ, the code wins**, and each difference is named where it falls.

---

## 1. What the three pieces are, and what exists today

6i is three unrelated completions that Audit #3 grouped because each finishes a report the redesign folded into another. None of them is a new report.

**The Top & Bottom harness.** Top & Bottom was a standalone report with its own scoring engine (v8), three parallel overlays and a calibration script, built in a separate session on 3 Sep and recorded in the architecture's Part 23. None of that code is in this repository. What is here:
- the state key `top_bottom` in `state/emit.py:VALID_KEYS`, reserved;
- the Monthly's section, `monthly_macro/payload.py:top_bottom_block`, which reads `top_bottom.composite` and `top_bottom.verdict` and, finding neither, prints that the harness is not built and that "a composite invented here would have no harness behind it and no way to be calibrated";
- the bear-rally base rate on the top-side language, read from `baserate.*` in the same function;
- two inert configs: `config/tb_intake_queue.yaml` (draft entries such as GTM-3's concentration twin, granting nothing) and `config/tb_false_bottom_gate.yaml` (status `inert`, audit verdict FAIL; only `breadth_rsp_spy` discriminates);
- the paper, Tops and Bottoms, and the false-bottom audit ledger.

The audit's "harness" is therefore a build, not a port. The architecture's Part 23 names `calibrate_thresholds.py` (13 hand-keyed episodes, episode-level classification) and a deferred continuous backtest (`backtest_scorecard.py`); neither file exists here.

**The Themes refresh.** Disruptive Themes is not built as a report. The Monthly prints one not-tracked line, "Disruptive Themes (quarterly; folded into the Quarterly Structural)" (`monthly_macro/stack.py`, the slow layers' alternative-assets sub-section). The Quarterly Structural is itself not built (`docs/master-guide.md`, "The Quarterly Structural: not built. No code and no unit."). The architecture's Part 28.3 specifies the refresh as five stages, the fourth a review gate "permanently `auto_publish: false`". Several orders carry inputs "into the next Disruptive Themes refresh brief" (Batch 5 items 22, 23 and 26; Batch 7 item 47; Batch 14 items 56, 58 and 63; Batch 15 items 75 and 76), none scored before it.

**The Alt Asset live fetchers.** The standalone Alternative Asset report ran on synthetic fetchers ("numpy seed 7 still feeds the dashboard", architecture Part 28.4). That dashboard is not in this repository, and nothing here generates synthetic data for a report: the Alternative Assets Quarterly (`monthly_macro/quarterly.py`) reads only the store, and `config/quarterly_chapters.yaml` lists every series the store lacks as `absent: <reason>`, printed as "not tracked", "none is invented or proxied". The vendored `altdata/report/` package is content, not a pipeline (CLAUDE.md, Known cleanup). So **the Quarterly's synthetic count is zero**, and the live-fetcher work is the Quarterly's absent rows. There are 230 of them (`absent` 170, `waits` 30, `not_measured` 30), classified in section 4.

| Piece | What exists | What 6i adds | The architecture's estimate |
|---|---|---|---|
| T&B harness | the state key, the Monthly section's absence line, two inert configs, the paper and one audit ledger | the harness, the episode fixtures, its ledger | the extended set and the bear-rally language, 2 h (Part 31.7); the harness itself was never estimated in this repo |
| Themes refresh | one not-tracked line in the Monthly | Stages 1–3 and the review gate, for the Quarterly | Stages 1–3 and the review-gate UI, about 7–9 h (Part 28.5, A3) |
| Alt Asset fetchers | the Quarterly, built and disabled, with 230 absent rows | the rows switched to stored keys, then new readers | "existing Session 11 scope, unchanged" (Part 28.5, A4), about 2.5 h |

Audit #3 sizes the whole at 10 hours. Section 6 sizes it at more, and decision 1 asks what to cut.

---

## 2. The T&B harness

### 2.1 The 13 episodes

The architecture's Part 23 states the calibration result: "`calibrate_thresholds.py` runs 13 hand-keyed episodes through the production score functions (episode-level classification, not a continuous backtest). Original weights: tops 0/3, bottoms 4/6, controls 4/4." So the 13 are three tops, six bottoms and four controls. **The list itself is not in this repository**: the script and its hand-keyed table stayed in the 3 Sep session. What the repository does say:
- the tops include 2000 (moved to OVEREXTENDED by the v8 rebalance), 2007 and 2022 (the paper: the composite "missed this top" in 2007 and "missed the 2022 bottom");
- December 24, 2018 was a control, scored neutral, and the October 2011 low "scored as a bottom" (Tops and Bottoms, chapter 10);
- the controls are named as a class: "the 1994/1998/2015/2018/2024-type events it correctly refuses to call" (Tops and Bottoms, chapter 11).

The library guide's row for Tops and Bottoms says "calibration against 13 episodes". The Base Rates paper uses "the thirteen-episode narrated roster" for a different set (the eight post-1970 bears plus five pre-1970 episodes). The two thirteens are not the same list. Decision 2 asks which is the harness's base, and the work order's first tranche reconstructs the 3 Sep list from the paper so it is stored at last.

### 2.2 The extended episode set

The extension is Base Rates' first amendment to the Top & Bottom report: "the calibration harness's episode set should be extendable to the pre-1970 cases with an explicit flag, because several of the modern triggers have no pre-1970 analogue and the harness must not score a signal that could not have existed" (Base Rates, chapter 12). The candidates, with the dates as their sources give them:

| Set | Episodes | Source |
|---|---|---|
| Post-1970 bears (8) | 1973–74, 1980–82, 1987, 1990, 2000–02, 2007–09, 2020, 2022 | Tops and Bottoms, "Episode selection" |
| Near-misses (6) | 1994, 1998, 2011, 2015–16, 2018, 2024 | Tops and Bottoms, "Episode selection" and chapter 10 |
| Pre-1970 (5) | 1907, 1929–32, 1937–38, 1946–47, 1961–62 | Base Rates, 11.6 |
| False bottoms inside bears | the rallies inside 1973–74, 2000–02, 2007–09 and 2022 | the false-bottom audit ledger |

The series each needs, by the store key where one exists:

| Series | Key | Reaches |
|---|---|---|
| S&P 500 closes | `yfinance.mkt_gspc` | from 1927-12-30 (`altdata/sources/yfinance_source.py`, "THE LONG HISTORY") |
| CAPE, earnings, CPI, price (monthly) | `shiller.cape`, `shiller.sp_earnings`, `shiller.cpi`, `shiller.sp_price` | Shiller's own file, which begins in 1871 |
| VIX | `fred.vix`, `yfinance.mkt_vix` | from 1990 (the yfinance module's comment) |
| HY OAS | `fred.hy_oas` | **not the episodes**: the false-bottom ledger found FRED serves it "only from 2023-10, so it reaches no episode" |
| Baa less the 10-year (the credit proxy the false-bottom audit used) | none: DBAA and BAA are not in `altdata/config.py`; `fred.yield_10y` is | would need two FRED series added |
| Unemployment, fed funds, CPI, 10-year, recessions | `fred.u3_rate`, `fred.fed_funds`, `fred.cpi`, `fred.yield_10y`, `fred.usrec` | FRED's own starts |
| Margin debt | `finra.margin_debit` | Customer Margin Balances from 1997 (the false-bottom ledger) |
| Breadth (RSP/SPY) | `yfinance.mkt_rsp` with `yfinance.mkt_spy` | RSP's listing; the audit's one discriminating element |
| Industry breadth | `french.ind49_ret_vw` | French's library |
| Index forward P/E | `index.forward_pe` | **NOT_YET_SOURCED** (its registry entry) |
| Top-ten concentration | GTM-3's concentration twin (`altdata/gtm_equities.py`) | recent only |

A pre-1970 episode will print most of the composite's inputs as "not existent at the time", which is the flag the amendment asks for, not a gap to fill.

### 2.3 What the harness computes

1. **Episode classification.** Each episode, as of each of its decision dates, through one score function per overlay and the composite, giving the classification the paper's template uses (top, bottom, control) and whether the harness called it.
2. **The three overlays as Part 23 states them:** Concentration and Complacency, HY Spread Acceleration and Liquidity and Funding Stress, each firing at three or more of its triggers. Their thresholds are Part 23's, carried as session-set with the source named.
3. **The continuous false-positive rate.** Part 23's deferred item 3: every session in the store's history scored, with the share of fired readings that no episode followed inside the declared window. This is "the real false-positive-rate measurement; calibration is episode-level only."
4. **The bear-rally base rate** on the top-side language, already read in `top_bottom_block`; the harness adds its n.
5. **The false-bottom gate**, once its config is no longer inert. Its elements and words stay the audit's.

Its output is a ledger in the calibration-ledger convention: `docs/ledgers/tb-harness-<date>.md` and its episodes CSV, dated and never edited, each with as-of, window, n, statistic, the pass rule and that rule's verdict. No order states a pass rule for the harness, so the first edition pre-registers one (the ledger convention of 17 Oct) and says so at its head.

### 2.4 The point-in-time rule

Every reading is the value knowable at the decision date: the store's `available_at`, ALFRED's first vintage for FRED (`altdata/fred_history.py`), Shiller's file at the publication lag `config/publication_lags.yaml` states for it. A series that did not exist at the date is "not existent", never back-filled from a later series. The hand-keyed values of 3 Sep were "hand-compiled for this study, not machine-extracted from a point-in-time database" (Tops and Bottoms, "Caveats restated"); the harness replaces them and prints, beside each episode, where the two differ.

### 2.5 What prints, and rights

- **Before any ruling:** the Monthly's section prints its absence line, as now.
- **After the harness:** the Monthly's Top & Bottom section prints the overlays' states and their counts, the harness's episode record (k of n per class) and its false-positive rate with n. It prints `top_bottom.composite` only if decision 3 rules that the harness stores it.
- **Rights: none.** Report-only. Nothing enters a composite of the Monthly's, the market-state object, a dial, a band or a packet. The Doctrine's rights for Top & Bottom stay unexercised until a sitting grants them.

---

## 3. The Themes refresh, against "permanently human-gated"

The signal-triage order of 25 Sep says: "No item can ... change a Disruptive Themes factor, scenario or theme text. Disruptive Themes stays permanently human-gated" (section 1.7). The architecture's Part 28.3 agrees: "automate the mechanical, gate the judgment", with Stage 4 "permanently `auto_publish: false`". So "automated" in the audit's row can mean only the mechanical stages. The split:

| Stage (Part 28.3) | Automatable under the ruling? | In 6i |
|---|---|---|
| 1. Instrument panels refreshed from the store; gaps as GAP cells | yes: it reads the store and prints | built, as a Quarterly slow layer |
| 2. A research pass: per-factor notes, cited, stored, not prose | yes, as a scan: the same shape as the quarterly alt-assets scan, a chat-side task whose file a human commits | a scan prompt and an ingest |
| 3. A model draft through the Master Refresh Prompt, every factor, composite and scenario change as an explicit delta with its reason | yes **as a draft**: it is a proposal, written to a file, never the standing text | built, behind the paragraph guard and the numeral audit |
| 4. The review gate: prior against proposed, the standing score the champion | **no**: it is the human gate | a diff file the operator reads; no UI |
| 5. Publish on approval | the operator's act | the operator's command, on the deny list like the register's gates |

The inputs carried "into the next Disruptive Themes refresh brief" (section 1) enter at Stage 1 as panels and at Stage 3 as named evidence, still unscored. The Quarterly that carries the refresh is decision 4: the Quarterly Structural is not built, while the Alternative Assets Quarterly is built and disabled, and its first edition falls on Saturday 9 Jan 2027 (`chester-quarterly.timer`: the second Saturday after quarter-end).

**Rights: none beyond the Doctrine's.** The refresh writes drafts. The Doctrine's Themes rights over Book A (the equity sleeve's tilts and the lower-half hold) bind only the standing text the operator publishes.

---

## 4. The Alt Asset live fetchers

No source is checked in this brief, and candidates are named, not verified: the sources rule of 16 Oct re-checks robots.txt and the terms for each one when its tranche is built.

### 4.1 The 230 absent rows, classified

Every `absent`, `waits` and `not_measured` entry in `config/quarterly_chapters.yaml`, sorted into one class (the full table is the appendix):

| Class | Rows | What it means | The work |
|---|---|---|---|
| W: stored since the row was written | 40 | a key in `metrics_registry.yaml` now covers the row, wholly or in part; the row was never switched | one config line each (AQ-3's notes said so: "one config line each") |
| E: an event | 26 | read through the quarterly scan (AQ-7); not a series | none |
| G: a listed gap already | 30 | paid, licensed, or refused by robots or terms | none: it stands |
| A: code, not a fetcher | 20 | an analysis not built (AQ-8), a row kind not built (the H.10 crosses), the tail watch's S8 ladder | belongs to AQ-8 or the tail watch, outside 6i |
| C: waits for 6b's curves | 14 | futures curves, forwards, the basis term structure | belongs to 6b |
| T: waits on the T&B harness | 1 | "HY spread acceleration: the Top & Bottom overlay is not on this build" | section 2 |
| F: a fetcher, with a candidate | 57 | not stored; a keyless candidate is named | the fetcher tranches |
| N: no keyless source named | 42 | not stored; no candidate | a listed gap until one is found |

So the Quarterly's still-synthetic count is **0**, and the rows needing new data are **99** (F 57 plus N 42), of which 57 have a candidate. The W rows are the largest single finding: the crypto writers of 17 Oct (`llama.stable_total`, `calc.funding_agg`, `deribit.dvol_btc`, `mempool.hashrate`, `calc.mnav`), the AQ-3 keys of 11 Oct (`fred.case_shiller_national`, `fred.dxy_em`, `thai.*`, `nbs.re_starts_ytd`, `calc.btp_bund_bp`, `calc.hefa_efa`), ETH and SOL in the basket, and PRL's data layer (`calc.prl_*`) all landed after the chapters were filled, and the chapters still print them as not tracked.

### 4.2 The candidates, grouped by reader

| Reader | Rows (F) | Candidate (unchecked) |
|---|---|---|
| EIA, the source already on the roster | SPR, refinery utilisation, gas storage, LNG feedgas | EIA open data |
| FRED, already on the roster | OVX (`OVXCLS`), the five other two-year yields | FRED and its OECD tables |
| USDA | the three WASDE balances and their revisions, the crop calendar | USDA's WASDE and crop-progress files |
| Yahoo, through the basket | corn, wheat, soybeans front months; GDX and SIL | the existing yfinance basket |
| CFTC, the existing writer | disaggregated COT for the grains | the agricultural instruments added |
| NOAA | the ENSO state | NOAA CPC's tables |
| Power | PJM's capacity auction; the reserve margin, queue and turbine backlog | PJM's published reports; the RTOs' and EIA's files |
| Shipping | Gulf exports, the disruption-price divergence | the IMF's PortWatch |
| Chain explorers and DefiLlama, already on the roster | ETH issuance, burn and staking (Blockscout, if it serves burn; Etherscan's key is not registered), RWA, L2, venue share, holder base, sector returns, VC raises | by series |
| Issuers | crypto ETF holdings and float; stablecoin attestations | the issuers' own daily files and attestation pages |
| EDGAR, already on the roster | BDC non-accruals, PIK share, the listed-BDC discount | SEC filings |
| Thailand | the current account, the construction indices | the BoT's keyless tables (the BoT API needs a key) |
| Asia | Taiwan export orders, foundry monthly revenue | MOEA's database; the foundries' own releases |
| Japan, Switzerland | intervention footprints | the MoF's and the SNB's releases |

### 4.3 The reader shape

Each new reader follows the pattern the crypto and AQ-3 writers set:
- a module `altdata/sources/<name>.py` using `_base.http_get_json`, the generic project User-Agent, and a robots check with wildcards;
- the store through `observations.open_writer(name)`, a source id registered in `source_registry.yaml` with its robots and terms quoted and dated, keys in `metrics_registry.yaml` with a family and units checked against the source's own page;
- `available_at` the pull instant, or the vintage's publication where the source has vintages;
- on the freshness roster (`feeds.EXTERNAL_WRITERS` or `OFFICIAL_WRITERS`), riding an existing run with no new timer;
- one gate on fixtures, no network.

Decision 5 asks for the order.

---

## 5. Rights, boundaries, method and what prints

**Rights and boundaries.**
- All three pieces are report-only. Nothing enters a composite, the market-state object, a dial, a band, a tell, a narrative, a packet or the register.
- The Themes refresh writes drafts. Its human gate is the operator's command and goes on the deny list.
- No by-hand data line is added (rule 3). Friction is a gap, not a key.
- No Brookfield-group instrument appears in any fixture, panel or episode.
- Nothing is written into chester-meme.

**Method version.** None of the three changes a rule in `config/market_state.yaml`, so none bumps the config or the method. The next bumps stay v1.13 and method-11 (CLAUDE.md). If decision 3 stores `top_bottom.composite`, that is a new stored object read by the Monthly, not a rules change; it needs its registry entry and its gate.

**Gates.** Three new code gates on fixtures, one per piece (`validate_tb_harness.py`, `validate_themes_refresh.py`, and one per fetcher tranche or a shared `validate_alt_fetchers.py`), each a Makefile line. `tools/validate_quarterly_stack.py` and `validate_quarterly_gates.py` move with the switched rows. `tools/check_master_guide.py` moves when Table 9's T&B row and the reports table change.

**What prints, before and after.**

| Where | Before 6i (today) | After 6i |
|---|---|---|
| The Monthly's Top & Bottom section | "top_bottom.composite is not in the store. The Top & Bottom harness is not built ..." and the bear-rally base rate | the overlays' states, the harness's episode record and false-positive rate with n; the composite only on decision 3 |
| The Monthly's slow layers | "Disruptive Themes (quarterly; folded into the Quarterly Structural)" as not tracked | one line naming the Quarterly that carries the refresh and its date |
| The Quarterly's chapters | 230 rows not tracked, 40 of them stored already | the 40 print; each new reader's rows print; the rest stay not tracked with their reasons |
| The Quarterly's slow layers | no Themes chapter | Stage 1's panels and Stage 3's proposed deltas, labelled as proposals, on decision 4 |
| The Quarterly's credit chapter | "HY spread acceleration: the Top & Bottom overlay is not on this build" | the overlay's state, from the harness |

---

## 6. The work order

Hours are estimates from the nearest built analogues: AQ-3's writers and the crypto tranches for readers, the ledgers package for the harness.

| Tranche | What | Hours | Depends on | One paste? |
|---|---|---|---|---|
| 6i-1 | **The rows switched:** the 40 W rows to their stored keys, the gates moved | 2.5 | nothing | yes |
| 6i-2 | **The harness core:** the episode fixture (the 3 Sep thirteen reconstructed from the paper, plus the extended set), the three overlays, episode classification, the ledger's first edition with its pre-registered pass rule | 5 | decision 2 | yes |
| 6i-3 | **The continuous false-positive rate** over the store's history; DBAA and BAA added to the FRED pull for the credit proxy | 3 | 6i-2 | yes |
| 6i-4 | **The Monthly's T&B section and the Quarterly's credit row** read the harness | 1.5 | 6i-2; decision 3 | with 6i-3 |
| 6i-5 | **Themes Stage 1:** the panels as a Quarterly slow layer, GAP cells | 3 | decision 4 | yes |
| 6i-6 | **Themes Stages 2–3:** the scan prompt and ingest; the draft through the Master Refresh Prompt, behind the guards; the diff file for Stage 4 | 4 | 6i-5 | yes |
| 6i-7 | **Readers, first tranche:** the ones on existing sources (EIA, FRED, Yahoo, CFTC, EDGAR) | 4 | 6i-1 | yes |
| 6i-8 | **Readers, second tranche:** USDA, NOAA, PJM, PortWatch, MOEA, the issuers' files, the explorers' remaining series | 6 | 6i-7; each source checked | two pastes |
| | **Total** | **29** | | |

Audit #3 said 10 hours. Tranches 6i-1, 6i-2 and 6i-5 come to 10.5, which is what the audit's row can buy (decision 1).

**The week of 2 Nov.** The 1 Nov Monthly runs on Sunday and Doctrine #2 sits on 7–8 Nov. Nothing in 6i should merge before the Monthly. What fits, branch-only:
- 6i-1, the switched rows: config only, merging after the Monthly. Nothing prints until the Quarterly is enabled.
- 6i-2, the harness core: its ledger is evidence the Doctrine #2 pack could table, if it lands before 7 Nov.

The rest waits for the rulings below. The Themes stages need decision 4, and the Quarterly's first edition, on 9 Jan 2027, is their deadline.

---

## 7. DECISIONS FOR ARI

**1. The scope of 6i's ten hours.** Options: (a) the three highest-yield tranches only (6i-1, 6i-2, 6i-5, about 10.5 h), the rest queued; (b) all eight tranches (about 29 h) across November; (c) the harness alone. **Recommend (a).** The audit sized 6i at ten hours, and these three each unblock a printed line: the 40 stored rows print, the harness's ledger exists, and the Themes panels appear. The fetchers and the later Themes stages wait behind rulings and source checks anyway. Option (b) is honest about the size but spends November's nights on readers whose rows mostly lead nowhere until the January Quarterly.

**2. The harness's episode base.** Options: (a) the 3 Sep thirteen (three tops, six bottoms, four controls), reconstructed from the paper, with the extended set flagged beside it; (b) the eight bears and six near-misses of Tops and Bottoms, plus the five pre-1970 episodes, as one set of nineteen; (c) Base Rates' thirteen-episode narrated roster. **Recommend (a).** It is the set the weights were calibrated on, so the harness can show whether it reproduces "tops 0/3, bottoms 4/6, controls 4/4" before it says anything new. The extension then answers Base Rates' amendment with its flag. Option (b) merges calibration and test samples, which is the overfitting the systematic-book draft warned of ("thirteen episodes is not thirteen observations").

**3. Whether the harness stores `top_bottom.composite`.** Options: (a) no composite: the overlays and the episode record only; (b) store the composite and verdict, report-only, so the Monthly's section reads what it was written to read; (c) defer to Doctrine #2. **Recommend (a).** Part 23 found that "no composite can catch all top types", and the parallel overlays were its answer. Storing a composite the paper says fails structurally invites it to be read as a verdict. The overlays carry the information; the composite can follow if a sitting asks for it.

**4. Which Quarterly carries the Themes refresh.** Options: (a) the Alternative Assets Quarterly, as a slow-layer chapter, from its 9 Jan 2027 edition; (b) the Quarterly Structural, built as its own cadence first; (c) neither: Themes stays dormant (the Master Guide's gap row 9: "Mark dormant until the Quarterly Structural, or build"). **Recommend (a).** The Alternative Assets Quarterly already runs at the fourth cadence through the one stack, and Audit #3's Quarterly Structural would replace both anyway. One quarterly edition is cheaper to hold than two. (b) is the audit's design but has no code, no unit and no order; (c) leaves a dozen inputs queued for a brief that never comes.

**5. The fetcher order.** Options: (a) existing sources first (6i-7), then new sources (6i-8); (b) by chapter, finishing one chapter at a time; (c) by the Quarterly's lead items only. **Recommend (a).** A reader on a source already on the roster needs no new robots or terms record and no new failure mode on the box. Most of the chapters' lead rows are W rows that 6i-1 already prints. By-chapter ordering would mix a new source's checks into every tranche.

**6. The credit proxy for the episodes.** Options: (a) add DBAA and BAA to the FRED pull and use Baa less the 10-year for every episode, as the false-bottom audit did; (b) use `fred.hy_oas` where it exists and print "not existent" before; (c) both, side by side. **Recommend (c).** HY OAS from FRED reaches no episode, so (b) alone blinds the credit overlay for the whole calibration. Baa less the 10-year is the long series the audit already relied on. Printing both keeps the live overlay on the series it fires on and the history on the one that reaches back.

**7. Themes Stage 2: a chat-side scan or a box model call.** Options: (a) a chat-side scheduled task writing a scan file a human commits, like the quarterly alt-assets scan; (b) a box-side model call through `model_meter`; (c) the operator's own research. **Recommend (a).** The research pass needs web search, which the box's model client is not set up for. The scan pattern already has a committed-by-a-human step and an ingest. It also costs nothing on the box's budget.

**8. Where the Stage 4 review happens.** Options: (a) a diff file in the repository the operator reads and publishes with one command on the deny list; (b) the review-gate UI the architecture costed; (c) a Doctrine sitting each quarter. **Recommend (a), with (c) for anything that would move a Themes right.** A diff file is the smallest gate that keeps "permanently human-gated" true. A UI is build time for a quarterly event. Factor or scenario changes that touch Book A's tilts belong at a sitting anyway, under the Doctrine.

---

## Notes

- **Not found in the repository:** the 3 Sep thirteen-episode list and `calibrate_thresholds.py`; v8's indicator weights beyond the two Part 23 names; the Master Refresh Prompt's text (Part 28.3 calls it "the report's own appendix"; the Disruptive Themes report is not here).
- **Where the code and a document differ:** the Quarterly's config prints 40 rows as not tracked that the store holds (section 4.1); CLAUDE.md's Alt Asset row says "Built, disabled", while the audit's 6i row still treats the fetchers as unbuilt. The code wins: the report is built, and its gaps are the absent rows.
- **The classification** in section 4.1 and the appendix was made by rules over the config's own reason strings and checked by hand against the registry for the W rows. A row's class is a reading of its reason, not a source check.

---

## Appendix: the 230 rows, by family chapter

Classes as in section 4.1. "Row" is the config's label; a row without one is named by its field.


### metals (14: A 2, C 1, E 1, F 1, G 5, N 4)

| Row | The config's reason | Class | Key, candidate or gap |
|---|---|---|---|
| Copper TC/RCs | no free source stored (AQ-3) | G | a listed gap (stands) |
| LME and COMEX copper inventories | no free source (AQ-3 part 1: CME prohibits scripted access; LME is licensed) | G | a listed gap (stands) |
| COMEX and LBMA silver inventories | exchange inventories are not stored (AQ-3) | N | no keyless source named |
| Lease rates and EFP | no free source stored (AQ-3) | G | a listed gap (stands) |
| SGE and Yangshan premiums | no free source stored (AQ-3) | G | a listed gap (stands) |
| Chilean copper output (Cochilco) | not stored (AQ-3) | N | no keyless source named |
| (waits) | the futures curve and the roll arrive with 6b | C | 6b's curves |
| Effective-float elasticity | not built (AQ-8) | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |
| The sovereign gold-share gap | the by-hand gold-share key is dropped (16 Oct 2026); a reader from the IMF's keyless IFS world aggregate is listed, not built | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |
| silver_deficit | COMEX and LBMA silver inventories are not stored (AQ-3) | N | no keyless source named |
| silver_industrial | the Silver Institute's balance arrives with the quarterly scan (AQ-7) | E | the quarterly scan |
| copper_deficit | TC/RCs and the three exchanges' inventories are not stored (AQ-3) | N | no keyless source named |
| electrification | the paper names evidence, not a series | G | a listed gap (stands) |
| miners_leverage | the miners (GDX, SIL) are not in the price feed | F | Yahoo, through the existing basket |

### oil_energy (24: A 1, C 2, E 2, F 10, G 2, N 7)

| Row | The config's reason | Class | Key, candidate or gap |
|---|---|---|---|
| The SPR beside commercial stocks | the SPR is not stored (AQ-3) | N | no keyless source named |
| Brent M1-M6 and M1-M12 | the futures curve arrives with 6b | C | 6b's curves |
| Gulf exports and reachability-adjusted spare capacity | not stored (AQ-3; a named Gap) | G | a listed gap (stands) |
| Frac spreads, DUCs | frac spreads have no free source (AQ-3 part 1); DUCs not checked | G | a listed gap (stands) |
| OPEC+ output against quota | arrives with the quarterly scan (AQ-7) | E | the quarterly scan |
| Refinery utilisation | not stored (not in AQ-3 part 1) | F | EIA open data (an existing source on the roster) |
| OVX and crude skew | OVXCLS is not in the FRED pull (AQ-3) | F | FRED `OVXCLS` (an existing source) |
| (waits) | the Brent and WTI curves and the roll arrive with 6b; the WTI prompt spread is the one curve point stored | C | 6b's curves |
| The disruption-price divergence | PortWatch transits are not stored (AQ-8) | F | the IMF's PortWatch |
| Commodity pass-through and its residual | not built (AQ-8) | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |
| buffer_market | a supply shock's size is an event, not a stored series; the five-year band is not stored | E | the quarterly scan |
| hormuz_spare | Gulf export tracking is not stored (AQ-3) | F | the IMF's PortWatch |
| power_squeeze | PJM auction results are not stored (AQ-3) | F | PJM's published auction reports |
| data_centre_load | interconnection queues and hyperscaler capex are not stored | F | the RTOs' and EIA's published files |
| hh_bottleneck | TTF and US LNG export utilisation are not stored (AQ-3); Henry Hub is | N | no keyless source named |
| lng_glut | TTF is not stored (AQ-3) | N | no keyless source named |
| enrichment | SWU and term U3O8 prices are not stored (AQ-3) | N | no keyless source named |
| US gas storage against the five-year band | EIA storage is not stored (AQ-3) | F | EIA open data (an existing source on the roster) |
| LNG feedgas | not stored (AQ-3) | F | EIA open data (an existing source on the roster) |
| TTF and EU storage | not stored (AQ-3) | N | no keyless source named |
| JKM | not stored (AQ-3) | N | no keyless source named |
| PJM's capacity auction against the cap, and the shortfall | not stored (AQ-3) | F | PJM's published auction reports |
| The reserve margin, the interconnection queue, the turbine backlog | not stored (AQ-3) | F | the RTOs' and EIA's published files |
| Uranium term, SWU and the Russian waivers | not stored (AQ-3) | N | no keyless source named |

### currency (22: A 8, C 1, E 2, F 3, G 1, N 2, W 5)

| Row | The config's reason | Class | Key, candidate or gap |
|---|---|---|---|
| The dollar's COFER share, constant currency | not tracked (by-hand audit, 16 Oct 2026): no free series publishes the constant-currency share (an ECB/IMF calculation in their reports) | G | a listed gap (stands) |
| The EM dollar index | not stored (AQ-3) | W | `fred.dxy_em` |
| The DXY-weighted two-year spread | the five other two-year yields are not stored (AQ-3) | F | FRED's OECD monthly rate tables (an existing source), or each central bank's own file |
| The three-month cross-currency basis | not stored (AQ-3) | N | no keyless source named (AQ-3 found none) |
| Risk reversals | FXE and FXY chains are not captured | N | no keyless source named |
| Intervention footprints (MoF monthly, SNB sight deposits) | not stored (AQ-3) | F | the Ministry of Finance's and the SNB's own releases |
| Stablecoin supply | not stored (AQ-3) | W | `llama.stable_total`, `llama.stable_by_chain` |
| (waits) | forward points arrive with 6b | C | 6b's curves |
| The two-year-spread fair-value gap | the five other two-year yields are not stored (AQ-3) | F | FRED's OECD monthly rate tables (an existing source), or each central bank's own file |
| Carry-to-vol per pair | not built (AQ-8) | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |
| The dollar-cycles table (GTM-22) | not built (AQ-8) | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |
| The yen stack and hedged-yield spreads | not built (AQ-8) | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |
| The stablecoin-dollarisation line | stablecoin supply is not stored (AQ-3) | W | `llama.stable_total`, `llama.stable_by_chain` |
| disorderly_tail | waits for AQ-8a (the yields-up/dollar-down recurrence, its YUDD_KEYS[recurrence]); auction metrics are not a single stored series | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |
| yuan_reserve | a policy event, not a stored series | E | the quarterly scan |
| yen_undervalued | PPP is not stored (AQ-3); a policy decision | E | the quarterly scan |
| stablecoins_dollar | stablecoin supply is not stored (AQ-3) | W | `llama.stable_total`, `llama.stable_by_chain` |
| (absent) | stored as fred.usd_thb under namespace: thailand; read here only on the operator's ruling (AQ-3 part 1, Needs you 2) | W | `fred.usd_thb`, on the operator's ruling |
| (absent) | both H.10 legs are pulled (AQ-3 part 1); the cross row kind is not built | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |
| (absent) | both H.10 legs are pulled (AQ-3 part 1); the cross row kind is not built | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |
| (absent) | both H.10 legs are pulled (AQ-3 part 1); the cross row kind is not built | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |
| (absent) | both H.10 legs are pulled (AQ-3 part 1); the cross row kind is not built | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |

### em (10: C 1, G 3, N 4, W 2)

| Row | The config's reason | Class | Key, candidate or gap |
|---|---|---|---|
| MSCI EM, USD (SR-14) | not tracked (by-hand audit, 16 Oct 2026): msci.com's robots.txt disallows its index pages; EEM below is the stored proxy | G | a listed gap (stands) |
| MSCI EM, local currency (SR-14) | not tracked (by-hand audit, 16 Oct 2026): msci.com's robots.txt disallows its index pages | G | a listed gap (stands) |
| MSCI World, USD (SR-14's DM leg) | not tracked (by-hand audit, 16 Oct 2026): msci.com's robots.txt disallows its index pages | G | a listed gap (stands) |
| EM local-currency spreads | not stored (AQ-3) | N | no keyless source named |
| The EM dollar index | FRED's emerging-market dollar index is not in the pull (AQ-3) | W | `fred.dxy_em` |
| EM portfolio flows (the IIF Capital Flows Tracker, by region) | no writer (AQ-3) | N | no keyless source named |
| The funding channel (the three-month cross-currency basis) | not stored (AQ-3) | N | no keyless source named (AQ-3 found none) |
| (waits) | EM forwards and the basis arrive with 6b and AQ-3 | C | 6b's curves |
| The funding channel: the cross-currency basis fires first (Tail Scenarios, S15) | the basis is not stored (AQ-3) | N | no keyless source named (AQ-3 found none) |
| Copper-gold and the commodity complex (the S12 routing) | the correlation layer's rows (aq-5-correlation-layer) | W | the correlation layer (`altdata/correlation.py`, AQ-5, built) |

### china (23: A 3, C 1, E 1, F 2, G 5, N 9, W 2)

| Row | The config's reason | Class | Key, candidate or gap |
|---|---|---|---|
| Panda bond issuance | not tracked (by-hand audit, 16 Oct 2026): no free machine-readable series | G | a listed gap (stands) |
| (waits) | the CNH forward curve is not stored (6b, AQ-3) | C | 6b's curves |
| SAFE's gold against IMF IFS (the 1% cross-check) | imf-ifs-gold (imf.ifs.gold_reserves_oz.chn) | W | `imf.ifs.gold_reserves_oz.chn` |
| The credit impulse (total social financing against output) | TSF is not stored (AQ-3) | N | no keyless source named (AQ-3 found the PBOC and NBS closed to scripts) |
| Capacity discipline: utilisation in solar, batteries, EVs | not stored (AQ-3) | N | no keyless source named (AQ-3 found the PBOC and NBS closed to scripts) |
| Capacity discipline: module and cell prices | not stored (AQ-3) | N | no keyless source named (AQ-3 found the PBOC and NBS closed to scripts) |
| Capacity discipline: survival of subscale makers | not stored; a named Gap | G | a listed gap (stands) |
| Property: starts | not stored (AQ-3, China property) | W | `nbs.re_starts_ytd` |
| Property: inventory months | not stored (AQ-3, China property) | N | no keyless source named (AQ-3 found the PBOC and NBS closed to scripts) |
| Property: developer credit spreads | not stored (AQ-3, China property) | N | no keyless source named |
| Shareholder return: net issuance, buybacks, dividends | not stored (AQ-3) | N | no keyless source named |
| Participation: index weight | not stored (AQ-3) | N | no keyless source named (AQ-3 found the PBOC and NBS closed to scripts) |
| Participation: connect flows | not stored (AQ-3) | N | no keyless source named (AQ-3 found the PBOC and NBS closed to scripts) |
| Participation: ADR audit status | an event, read through the scan (AQ-7) | E | the quarterly scan |
| Deflation exit: CPI, PPI, the output deflator | not stored (AQ-3) | N | no keyless source named (AQ-3 found the PBOC and NBS closed to scripts) |
| State-bank dollar selling | not tracked (by-hand audit, 16 Oct 2026): a reading of press reports, not a series (G-21) | G | a listed gap (stands) |
| Grain reserve builds | not stored; a named Gap | G | a listed gap (stands) |
| Crude reserve builds | not stored; a named Gap | G | a listed gap (stands) |
| Strait war-risk quotes | the tail watch's S8 ladder is not stored | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |
| Taiwan export orders | not stored (AQ-3) | F | Taiwan MOEA's statistics database |
| Foundry monthly revenue | not stored (AQ-3) | F | the foundries' own monthly revenue releases |
| PLA sustainment indicators | the tail watch's S8 ladder is not stored | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |
| Customs inspections | the tail watch's S8 ladder is not stored | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |

### crypto (80: A 4, C 1, E 18, F 25, G 3, N 5, W 24)

| Row | The config's reason | Class | Key, candidate or gap |
|---|---|---|---|
| Stablecoin total supply (S-1) | not stored (AQ-3) | W | `llama.stable_total`, `llama.stable_by_chain` |
| BTC long-term-holder supply (SR-29) | not stored | W | `btcdata.lth_supply_share` (prints not tracked without the operator's key) |
| ETH burn against issuance | not stored (AQ-3) | F | Blockscout (on the roster), if it serves burn; Etherscan's key is not registered |
| RWA tokenised value and holder count | not stored (AQ-3) | F | DefiLlama or the chain explorers already on the roster, by series |
| ETF flows read against float (S-2) | the float is not stored; the share count is (IBIT, above) | F | the issuers' daily holdings files |
| Exchange balances | not stored | F | DefiLlama or the chain explorers already on the roster, by series |
| OI-weighted funding (S-3; crowded at z > +2 with OI/mcap at a 90-day high) | not stored | W | `calc.funding_agg`, `calc.oi_mcap` |
| The DVOL regime (S-4, DS-41) | not stored | W | `deribit.dvol_btc` |
| Hyperliquid whale positions | not stored | F | DefiLlama or the chain explorers already on the roster, by series |
| Miner reserves and hashrate | not stored | W | `mempool.hashrate` (reserves stay absent) |
| Treasury-company activity and premium to NAV | not stored; a named Gap | W | `calc.mnav`, `calc.treasury_net_purchases` |
| Sovereign purchase announcements | events, read through the scan (AQ-7) | E | the quarterly scan |
| The CLARITY and BIP-360/361 calendars | events, read through the scan (AQ-7) | E | the quarterly scan |
| (waits) | the CME basis and the perpetual funding curve are not stored (6b) | C | 6b's curves |
| The speculative-bid rotation between gold and BTC: liquidity beta or debasement hedge this quarter | not built (AQ-8) | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |
| Effective-float elasticity (bitcoin minus LTH, lost coins, ETF and treasury holdings) | not built (AQ-8); LTH supply and ETF holdings are not stored | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |
| The two-bid decomposition for the crypto ETFs (IBIT) | the paper bid is built for GLD (aq-8a-gold-residual); IBIT's chain is not captured | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |
| Factor V's four standing quarterly questions (infrastructure against speculation; the gold-against-BTC split; leverage depth; the security budget), with the adoption ledger | the adoption ledger is not stored; the four are answered at the quarterly review | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |
| Stablecoin supply against bill issuance | stablecoin supply is not stored (AQ-3) | W | `llama.stable_total`, `llama.stable_by_chain` |
| Issuer-level stablecoin surveillance and reserve composition (S4, S23) | issuer attestations are not stored (AQ-3) | F | the issuers' own attestation pages |
| Post-quantum milestones against verified capability (S18) | milestones arrive through the scan (AQ-7) | E | the quarterly scan |
| btc_scarcity | a quantum event or a contentious fork is an event, read through the scan (AQ-7) | E | the quarterly scan |
| eth_value_capture | ETH, ETH/BTC, L2 activity and base-layer fee capture are not stored (AQ-3) | F | DefiLlama or the chain explorers already on the roster, by series |
| sol_pmf | Solana's application TVL is not stored (AQ-3) | W | `llama.chain_tvl` |
| privacy_path | a regulatory event, read through the scan (AQ-7) | E | the quarterly scan |
| stablecoin_infra | stablecoin supply is not stored (AQ-3) | W | `llama.stable_total`, `llama.stable_by_chain` |
| (absent) | token rights are a field of the quarterly scan (AQ-7) | E | the quarterly scan |
| (absent) | circulating against fully diluted, LTH supply (SR-29), lost coins and ETF/treasury holdings — the effective float — are not stored | W | `btcdata.lth_supply_share` (prints not tracked without the operator's key) |
| (absent) | the holder base is not stored | F | DefiLlama or the chain explorers already on the roster, by series |
| (absent) | on-chain activity and fees, organic against subsidised, are not stored | F | DefiLlama or the chain explorers already on the roster, by series |
| (absent) | hashrate, miner reserves, client concentration, proof-of-reserve cadence and custodian post-quantum roadmaps are not stored (the paper's §5-7 watches; AQ-7) | F | the IMF's keyless data service (an existing source) |
| (absent) | venue volumes and depth are not stored | F | DefiLlama or the chain explorers already on the roster, by series |
| (absent) | funding, OI (S-3), CME positioning, DVOL (DS-41) and ETF flows are not stored | W | `calc.funding_agg`, `deribit.dvol_btc`, `farside.btc_total` (CME positioning stays absent) |
| (absent) | the CLARITY and GENIUS calendars and custody by jurisdiction arrive through the scan (AQ-7) | E | the quarterly scan |
| (absent) | the quarter's catalysts arrive through the scan (AQ-7) | E | the quarterly scan |
| (absent) | token rights are a field of the quarterly scan (AQ-7) | E | the quarterly scan |
| (absent) | ETH issuance, burn and staking ratio are not stored (AQ-3) | F | Blockscout (on the roster), if it serves burn; Etherscan's key is not registered |
| (absent) | base-layer fee capture is not stored | F | DefiLlama or the chain explorers already on the roster, by series |
| (absent) | L2 against mainnet activity is not stored | F | DefiLlama or the chain explorers already on the roster, by series |
| (absent) | validator and client concentration are not stored | F | DefiLlama or the chain explorers already on the roster, by series |
| (absent) | ETH is not in the price feed (AQ-3) | W | `yfinance.mkt_eth_usd` |
| (absent) | funding, OI and ETF flows are not stored | W | `hl.funding`, `fut.funding_okx`, `calc.oi_mcap`; ETF flows `farside.btc_total`/`farside.eth_total` where a fund exists |
| (absent) | arrives through the scan (AQ-7) | E | the quarterly scan |
| (absent) | arrives through the scan (AQ-7) | E | the quarterly scan |
| (absent) | token rights are a field of the quarterly scan (AQ-7) | E | the quarterly scan |
| (absent) | emissions, unlocks and staking are not stored | F | DefiLlama or the chain explorers already on the roster, by series |
| (absent) | application TVL and its composition are not stored | W | `llama.chain_tvl` |
| (absent) | application TVL, DEX volume and the memecoin share are not stored | W | `llama.chain_tvl`, `llama.dex_volume` (the memecoin share stays absent) |
| (absent) | validator concentration and outages are not stored | F | DefiLlama or the chain explorers already on the roster, by series |
| (absent) | SOL is not in the price feed (AQ-3) | W | `yfinance.mkt_sol_usd` |
| (absent) | funding, OI and ETF flows are not stored | W | `hl.funding`, `fut.funding_okx`, `calc.oi_mcap`; ETF flows `farside.btc_total`/`farside.eth_total` where a fund exists |
| (absent) | arrives through the scan (AQ-7) | E | the quarterly scan |
| (absent) | arrives through the scan (AQ-7) | E | the quarterly scan |
| (absent) | token rights are a field of the quarterly scan (AQ-7) | E | the quarterly scan |
| (absent) | circulating against fully diluted and holder concentration are not stored | N | no keyless source named |
| (absent) | shielded supply "cannot be faked by exchange speculation"; fee revenue is not stored | G | a listed gap (stands) |
| (absent) | not stored | N | no keyless source named |
| (absent) | venue share is not stored | F | DefiLlama or the chain explorers already on the roster, by series |
| (absent) | funding, OI and ETF flows are not stored | W | `hl.funding`, `fut.funding_okx`, `calc.oi_mcap`; ETF flows `farside.btc_total`/`farside.eth_total` where a fund exists |
| (absent) | the EU July 2027 headwind (MiCA) and US accommodations arrive through the scan (AQ-7); XMR stays as ZEC's delisted peer | E | the quarterly scan |
| (absent) | arrives through the scan (AQ-7) | E | the quarterly scan |
| (absent) | the crypto.watch entry and its MW-1 fields (ST-13) are not built | W | SM00118, `calc.prl_*` (ST-13, built 18 Oct) |
| (absent) | D1-D3 (code supply, week-one overhang, supply gap) are not stored (ST-13) | W | `calc.prl_supply_code`, `calc.prl_overhang`, `calc.prl_supply_gap` |
| (absent) | signposts S1-S2 (paid-compute partners, the PRL demand sink) are not stored (ST-13) | G | a listed gap (stands) |
| (absent) | not stored (ST-13) | N | no keyless source named |
| (absent) | signpost S7 (technical and chain integrity) is not stored (ST-13) | N | no keyless source named |
| (absent) | S3 (exchange access) and D5 (venue concentration) are not stored (ST-13) | W | `calc.prl_venue_conc` (D5 prints not tracked: source retired) |
| (absent) | S6 and D4 (emission-to-volume) are not stored (ST-13) | W | `calc.prl_emission_to_volume` |
| (absent) | S8 (team, funding, regulatory) is not stored (ST-13) | N | no keyless source named |
| (absent) | arrives through the scan (AQ-7) | E | the quarterly scan |
| Stablecoin supply by issuer and chain (S-1) | not stored (AQ-3) | W | `llama.stable_total`, `llama.stable_by_chain` |
| Tokenised treasuries and RWA | not stored (AQ-3) | F | DefiLlama or the chain explorers already on the roster, by series |
| L2 value secured | not stored (AQ-3) | F | DefiLlama or the chain explorers already on the roster, by series |
| Memecoin froth (S-5) | not stored (AQ-3) | W | `calc.froth_z` |
| The stablecoin plumbing, by issuer (not directional theses) | issuer attestations, on-chain supply by chain and peg history are not stored (S-1, S4, S23; AQ-3) | F | the issuers' own attestation pages |
| Sector returns: L1, L2, DeFi, RWA, memes, privacy | no sector index is stored (AQ-3) | F | DefiLlama or the chain explorers already on the roster, by series |
| Venue share: CEX against DEX, and Hyperliquid's share | not stored (AQ-3) | F | DefiLlama or the chain explorers already on the roster, by series |
| Crypto ETF AUM | share counts are not stored (AQ-3) | F | the issuers' daily holdings files |
| VC raises (DS-29 /raises) | not stored (DS-29) | F | DefiLlama or the chain explorers already on the roster, by series |
| Developer activity | a named gap | G | a listed gap (stands) |

### real_estate (6: C 1, G 2, N 2, W 1)

| Row | The config's reason | Class | Key, candidate or gap |
|---|---|---|---|
| CMBS delinquency by property type | Trepp is paid; not stored | G | a listed gap (stands) |
| The extension-versus-foreclosure share on maturing loans ("rising foreclosure share = deferral has stopped") | the special servicers' data is not stored | N | no keyless source named |
| The office / data-centre split, and data-centre ABS (S14) | not stored | N | no keyless source named |
| CPPI (commercial property prices) | paid; not stored | G | a listed gap (stands) |
| Real house prices, year on year | Case-Shiller is not in the FRED pull (AQ-3) | W | `fred.case_shiller_national` against `fred.cpi` |
| (waits) | no real-estate curve is stored | C | 6b's curves |

### credit (13: A 1, C 1, F 3, G 5, N 2, T 1)

| Row | The config's reason | Class | Key, candidate or gap |
|---|---|---|---|
| The dual-track default rate and the LME count | PitchBook LCD is paid; not stored | G | a listed gap (stands) |
| The loan distress ratio | PitchBook LCD is paid; not stored | G | a listed gap (stands) |
| Private-credit non-accruals and PIK share | BDC filings and the Boston Fed series are not stored (AQ-3) | F | SEC EDGAR filings (an existing source) |
| The listed-BDC discount to NAV | not stored (AQ-3) | F | SEC EDGAR filings (an existing source) |
| Cross-sectional mark dispersion | filings analysis; not stored | G | a listed gap (stands) |
| HY spread acceleration | the Top & Bottom overlay is not on this build | T | the T&B harness's HY Spread Acceleration overlay (piece 1) |
| Credit-equity divergence | not computed here; the HY OAS and SPY rows are printed beside each other | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |
| (waits) | CDX and the spread curve are not stored | C | 6b's curves |
| dispersion_signal | the listed-BDC discount is not stored (AQ-3); BB-CCC is, in item 4 | F | SEC EDGAR filings (an existing source) |
| default_suppressed | the LME count and the distress ratio are PitchBook LCD's (paid); not stored | G | a listed gap (stands) |
| marks_unanchored | mark dispersion is a filings analysis; not stored | G | a listed gap (stands) |
| vintage_cohort | refinancing spreads by vintage are not stored | N | no keyless source named |
| split_90_10 | the distressed share is not stored | N | no keyless source named |

### intl_equities (15: A 1, C 1, E 1, G 3, N 7, W 2)

| Row | The config's reason | Class | Key, candidate or gap |
|---|---|---|---|
| MSCI World, USD | not tracked (by-hand audit, 16 Oct 2026): msci.com's robots.txt disallows its index pages | G | a listed gap (stands) |
| MSCI ACWI ex-US, USD | not tracked (by-hand audit, 16 Oct 2026): msci.com's robots.txt disallows its index pages | G | a listed gap (stands) |
| The valuation quad by region | regional forward P/E, P/B and dividend yield are not stored (AQ-3) | N | no keyless source named |
| Hedged against unhedged ("two decisions wearing one ticker") | the hedged funds are not in the price feed (AQ-3) | W | `calc.hefa_efa` |
| Japan: the below-1x-book share | not stored (AQ-3) | N | no keyless source named |
| Japan: the buyback run-rate | not stored (AQ-3) | N | no keyless source named |
| Japan: the cross-holding unwind | not stored (AQ-3) | N | no keyless source named |
| Japan: the wage round | an event, read through the scan (AQ-7) | E | the quarterly scan |
| The euro fragmentation spread | Italian and German 10-year yields are not stored (AQ-3) | W | `calc.btp_bund_bp` |
| The leadership-regime clock | not built | A | code in `monthly_macro/quarterly_items.py` or AQ-8 |
| (waits) | no curve is stored for the chapter | C | 6b's curves |
| exceptionalism | the regional earnings and multiple gaps are not stored (AQ-3) | N | no keyless source named |
| convergence | the earnings gap and Japanese buybacks are not stored (AQ-3) | N | no keyless source named |
| reversal | relative earnings are not stored (AQ-3) | N | no keyless source named |
| derating | the paper defers it to the architecture's Part 31.2 | G | a listed gap (stands) |

### thailand (8: C 1, F 3, W 4)

| Row | The config's reason | Class | Key, candidate or gap |
|---|---|---|---|
| The BoT policy rate | the BoT API is not pulled (AQ-3, AQ-12) | W | `thai.bot_policy_rate` |
| The BoT policy rate and its stated path | the BoT API is not pulled (AQ-3, AQ-12) | W | `thai.bot_policy_rate` |
| Thai CPI | not pulled (AQ-3, AQ-12) | W | `thai.cpi_yoy` |
| The current account | not pulled (AQ-3, AQ-12) | F | the BoT's keyless tables and Thailand's official statistics |
| Tourist arrivals | not pulled (AQ-3, AQ-12) | W | `thai.tourist_arrivals` |
| The construction-materials price index | not pulled (AQ-3, AQ-12) | F | the BoT's keyless tables and Thailand's official statistics |
| The construction labour cost index | not pulled (AQ-3, AQ-12) | F | the BoT's keyless tables and Thailand's official statistics |
| (waits) | no THB forward is stored (AQ-3, AQ-12) | C | 6b's curves |

### agriculture (15: C 3, E 1, F 10, G 1)

| Row | The config's reason | Class | Key, candidate or gap |
|---|---|---|---|
| Corn (front month) | not in the price feed (AQ-3, AQ-13) | F | Yahoo front-month futures through the existing basket |
| Wheat (front month) | not in the price feed (AQ-3, AQ-13) | F | Yahoo front-month futures through the existing basket |
| Soybeans (front month) | not in the price feed (AQ-3, AQ-13) | F | Yahoo front-month futures through the existing basket |
| WASDE corn: production, use, trade, ending stocks, stocks-to-use | waits for AQ-3's WASDE writer (AQ-13) | F | USDA's WASDE files (usda.gov) |
| WASDE wheat: production, use, trade, ending stocks, stocks-to-use | waits for AQ-3's WASDE writer (AQ-13) | F | USDA's WASDE files (usda.gov) |
| WASDE soybeans: production, use, trade, ending stocks, stocks-to-use | waits for AQ-3's WASDE writer (AQ-13) | F | USDA's WASDE files (usda.gov) |
| The quarter's WASDE revisions, diffed against the stored vintage (projections kept apart from observed) | waits for AQ-3's writer; no vintage is stored | F | USDA's WASDE files (usda.gov) |
| The crop-stage window | the crop calendar is not stored | F | USDA crop progress files |
| NOAA's ENSO state (context, never extrapolated to price) | not stored | F | NOAA CPC's ENSO tables |
| Export commitments, bans and corridor access | events, read through the scan (AQ-7) | E | the quarterly scan |
| The nitrogen complex: Tampa ammonia, NOLA urea, DAP (Factor III; a 2-3-quarter lead on food CPI) | not stored; a named GAP | G | a listed gap (stands) |
| Calendar spreads and the roll | the futures curve arrives with 6b | C | 6b's curves |
| Disaggregated COT, scaled to open interest | the CFTC writer stores legacy non-commercial only (AQ-3) | F | the existing CFTC writer, the agricultural instruments added |
| (waits) | the grain curves arrive with 6b | C | 6b's curves |
| Sugar, coffee, cocoa and cotton | the softs are not in the price feed, the curve or the CFTC writer (AQ-3, AQ-13) | C | 6b's curves |
