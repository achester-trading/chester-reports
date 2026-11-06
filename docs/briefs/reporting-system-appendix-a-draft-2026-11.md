# Draft: the Reporting System paper's Appendix A, after the merge week (B123)

**This is a brief, not the paper.** It drafts the replacement for Appendix A of
`docs/whitepapers/reporting-system-whitepaper.md`, as the appendix will stand once the
merge week's five chains are on main. The paper is not touched here: under the
library's rule for dated appendices, its Appendix A is replaced whole at the real
refresh, and its "as of" heading then names that day.

**Where the values come from.** Every value is read from the rehearsed tree,
`origin/a105-merge-week-rehearsal-2` at `b8023fba`, and cited by file. That tree was
read only, never merged. One pending branch is included and marked: A112, "pending,
a112".

**The marks.** They compare with the appendix on main, which is dated 19 October
2026:
- "(changed: …)" marks a line whose value differs, and says what changed;
- "(new)" marks a line that appendix does not have;
- an unmarked line is unchanged.

The line-by-line diff is in `docs/briefs/b123-notes.md`.

The paper reached this shape through two editions:
- the 19 October appendix (main) has the sections below;
- the 24 October appendix (chain-7, on the rehearsed tree) added the budgets table,
  the publication-lag families and the superseded keys.

A mark against the 19 October text therefore also covers what 24 October already
said.

---

## Appendix A — Dated: Timers, Gates, Windows, Thresholds, Budgets, Sources, Charts (as of 4 November 2026)

*Everything in this appendix is as of 4 November 2026, the day the docs tranche (chain-12) merges. It is read from main after the merge week, whose content the second rehearsal (`a105-merge-week-rehearsal-2`, commit `b8023fba`) assembled. The sources are:*
- *the systemd units in `deploy/systemd/` and the deploy's timer list in `scripts/deploy_remote.sh`;*
- *the backup sweep, `scripts/rclone_sync.sh`;*
- *the `Makefile`, `tools/gate_list.py`, `tools/stitch_counts.py` and `CLAUDE.md`;*
- *the configuration files `config/reporting_stack.yaml`, `config/risk_limits.yaml`, `config/market_state.yaml`, `config/vol_event.yaml`, `config/data_quality.yaml`, `config/price_sources.yaml`, `config/publication_lags.yaml`, `config/dth1.yaml`, `config/alpha_families.yaml`, `config/flashalpha.yaml` and `config/digital_addendum.yaml`;*
- *`source_registry.yaml`, the dealer pre-registration ledger and the feed modules.*

*All times are U.S. Eastern. Whether each timer is enabled on the production box is not recorded in the repository; the box sheets and the merge-week runbook (`docs/runbooks/merge-week-2026-11-03.md`) list the ones the operator enables.* (changed: the date, the source tree, five files added to the list, and the runbook named)

**Timers the deploy enables.** The deploy and the box's self-deploy enable a declared list of fourteen timers, and copy every other unit without enabling it (`scripts/deploy_remote.sh`, `DEPLOY_TIMERS`).

| Unit | When | What it runs |
|---|---|---|
| Voices and news scan | Weekdays 06:15 | The voices scan, then the voice seeds |
| Overnight fetch | Weekdays 06:45 | Correction pass; Japan and China writers; events; the loggers; the ES and tape bars; the listings and the Security Master export; the meme ingest's second chance |
| Morning anchor | Weekdays 07:00 | The anchor, with the DTH-1 rules checklist after the ES read (changed: the checklist added, `config/dth1.yaml` `checklist`; A92) |
| Heartbeat | Daily 08:30 | Health check; verdict and exit code |
| Broker sync | Weekdays every 30 minutes, 09:00–17:30 | Portfolio Truth; reconciliation (its install section is held back in the unit file) |
| Closing-auction sampler | Weekdays 15:49 | Auction imbalance |
| End-of-day pull | Weekdays 16:10 | Every feed but the loggers; option chains and exposures; the derived features; the volume profile; the one-day 10-year ledger's resolution (changed: the 10-year ledger added) |
| Daily close | Weekdays 16:45 | The object; the calibration rows; the close (changed: the calibration rows added) |
| Crypto basket | Daily 17:25 | The crypto basket and data layer; GDELT, the degree days and the model-release watch; on Saturdays the cyber lists; each day the protocol counts (changed: the added writers) |
| Backup | Daily 02:30 | The encrypted sweep. It also copies the inbound folders: the DTH-1 ledger from the private folder `chester-cards`; the archive copies of `chester-letters` and `chester-cards`, which nothing in the repository reads; and the AAII task's weekly folder (`scripts/rclone_sync.sh`, `pull_inbox_path` and `pull_folder`; D52 and D54, 1 November; A92b) (changed: the inbound copies added) |
| Saturday prices | Saturdays 06:00 | The week's price corrections |
| Weekly | Sundays 05:00 | The Weekly and the digital-assets addendum (changed: the addendum added) |
| Monthly | The 1st, 07:30 | The scans ingest; the Monthly |
| Self-deploy | Every 30 minutes inside the windows | Unit copy, daemon reload, the declared timers, the drift check; never a restart |

**Timers the operator enables** (copied by the deploy and enabled by hand; the box sheets give the steps).

| Unit | When | What it runs |
|---|---|---|
| Dealer captures | Weekdays 09:45 and 12:30 | Intraday chain captures; the 12:30 alert slot |
| Open note | Weekdays 09:50 | The open note, after its own fetch (new) |
| Vendor writer | Weekdays 16:25 | The FlashAlpha cross-check |
| Vendor chains | Weekdays 16:31 | SPX and SPCX from Massive, after its 15-minute delay |
| Alpha Lab, nightly | Weekdays 17:40 | Fill, mark, grade, govern, learn; the grammar search last (changed: the grammar search added) |
| Alpha Lab, proposer | Weekdays 18:10 | The one model call that proposes hypotheses |
| Meme ingest | Sunday to Friday 21:15 | chester-meme's packets as Book D drafts (the overnight pass repeats it before 07:00) (changed: 21:45 to 21:15, the secondary-notes order) |
| Evening note | Sunday to Thursday 21:30 | The evening note, after its own fetch (new) |
| Alpha Lab, weekly | Sundays 06:00 | Walk-forward, re-fit, rebalance, the agenda, the verdicts |
| Restore test | Sundays 10:15 | Restores the newest encrypted snapshot and checks it against the sweep's count |
| Quarterly | The second Saturday of January, April, July and October, 06:00 | The Alternative Assets Quarterly; ships disabled; first edition 9 January 2027 |
| Broker gateway restart and watchdog | Held back | Enabled only after a witnessed clean start |

The monthly restore drill's units are deleted, and its tool remains. (changed: on 19 October the drill was a row, "never enabled")

**The calendar.**
- The merge week: the chains merge Tuesday 3 and Wednesday 4 November, inside the windows (`docs/runbooks/merge-week-2026-11-03.md`). (changed: 19 October gave the Monthly's dry runs and freeze, now past)
- The first stacked Monthly and the first digital-assets addendum were issued on 1 November 2026. Appendix F records that edition and the readable editions. (changed: then a plan)
- The two notes have been live since 26 October. (new)
- Doctrine #2 sits on 7–8 November; Audit #5 is the week of 23 November. (new)
- The Weekly's gold block prints every Sunday from 8 November (`config/reporting_stack.yaml`, the `gold` section). (new)

**Gates.**
- **The count.** `make validate` runs every gate: 167 code gates (164 Python, smoke test included, and 3 shell) and 8 data gates, with no network and no box (`tools/gate_list.py`; `CLAUDE.md`, held by `tools/stitch_counts.py --check`). (changed: 118 code gates, 115 of them Python, to 167 and 164; the data gates are unchanged at 8)
- **What each kind does.** A code gate seeds a store of its own and never reads the live one. A data gate reports on the box's real history, does not set the exit code, and prints NOT VALIDATED where there is no store.
- **Where the list lives.** In the `Makefile`; CI reads it from there, and `tools/gate_list.py` prints it by kind. (changed: gate_list.py added)
- **Pinned clocks.** A gate whose fixtures are dated runs on its fixtures' clock, not the calendar's, so its verdict does not change with the date (B101, `pin_clock()`). (new)
- **The names gate.** `tools/validate_names.py` reads its list of names from outside the repository: the environment (`CHESTER_NAMES_DENYLIST`), or a file the environment names (`CHESTER_NAMES_FILE`). With neither set it runs its self-test and says so. The list never enters a committed file. (new)
- **CI.** CI caches the installed packages, keyed by operating system, Python version and the requirements file's hash. A push whose files all sit under `docs/briefs/` or `docs/pastes/` runs only the library, registry and Master Guide checks. On main, one run waits and none is cancelled in progress (B111). Grouping the code gates into about twenty jobs (B122, `config/ci_groups.yaml`) is pending: it merges after the merge week. (new)

**Operating windows.** Deploys and other box writes: weekdays 09:05–15:40 and 17:20–23:30, never 16:00–17:20; weekends open, clear of Sunday 05:00. A merge to main is a box write: every box wrapper pulls main before it starts, and unit files follow at the next self-deploy. A session never runs unit commands, privilege escalation or register writes.

**The stack's budgets** (targets, never caps; ruled 24 October 2026, D19 and D20; an edition over its target prints one line at its foot). (changed: 19 October gave one sentence of caps)

| Report | Prose words | Charts | Reading target |
|---|---|---|---|
| Daily close | 2,250 | 3 | 10 minutes |
| Weekly | 7,900 | 11 | 35 minutes |
| Monthly | 10,000 | 12 | 55 minutes |
| Quarterly | no word budget | 40 | 90 minutes |
| Digital-assets addendum | about 1,500 | 2 | 7 minutes |
| Open note | 250, a hard cap | 1 | 2 minutes |
| Evening note | 150, a hard cap (Sunday 400) | 1 | 1 minute (Sunday 3) |

These are read from `config/reporting_stack.yaml` (`budget`, `reading_targets_minutes`) and `config/digital_addendum.yaml`. What changed since 19 October:
- the close: 1,000 words and 5 minutes became 2,250 and 10;
- the Weekly: 3,500 words, 10 charts and 20 minutes became 7,900, 11 and 35. The eleventh chart is W13, the gold block's (ruled 26 October; B75);
- the addendum: 1,100 words and 5 minutes became about 1,500 and 7;
- the two notes' rows are new.

Reading time is prose words ÷ 250 plus 20 seconds per chart, and a firing trigger adds one chart.

The guards:
- The runaway guard withholds a reply past twice its section's ceiling, and never past 7,000 characters. (new)
- The dealer retrospective's floor is 20 scored sessions.
- The evening note asks for a paragraph on a weekday only when the e-mini or Nasdaq future moves past 0.75%, dollar-yen past 1.0%, or an Asian index past 1.5%. On Sunday it always asks. (new)

**Charts and what the dealer charts displace.**
- **The close:** C1 SPY's session; C2 sixty daily candles; C3 by rule; and D2 the dealer chart, after C1 and any C3. With C3 drawn and no trigger, C2 is set aside.
- **The Weekly** (changed: W11 is now the standing decomposition, W12 enters fifth, and W13 is added):
  - W1 SPY six months;
  - W2 two years;
  - W3 the curve and the high-yield spread;
  - W4 speculative positioning;
  - W5 sector and style returns;
  - W6 open contradictions, only when one is open;
  - W7 SPY over 23-hour sessions with the overnight future;
  - W8 six markets;
  - W9 positioning and sentiment gauges;
  - W10 prediction-market odds;
  - W11 the standing decomposition, in What's priced;
  - W12 the dealer panel, which enters fifth and sets W10 aside, and W11 too when W6 is open and no trigger fires;
  - W13 the gold block's chart, inside the cap of eleven (`config/reporting_stack.yaml`, the `gold` section).
- **The Monthly:** M0 to M13, fourteen charts, capped at twelve; M12 only when the month's dealer profiles exist. Set aside first are M13, then M8 (which does not render until scenario set #1 exists), then M9, then M12. (changed: thirteen planned charts, with two set aside, became fourteen, with four set aside)

**Thresholds.**

| Threshold | Value | Where |
|---|---|---|
| The market-state object | Rules v2.0, method 11. Persistence 2 sessions. A five-year window. Bands 66 and 33. Contradictions open at a gap z of 2.0 held 2 sessions, and close after 2 failing sessions. Exceptions at 5. Extremes at the 5th and 95th percentiles. The VIX bands 14, 20 and 30. (changed: rules v1.10 and method 8 became v2.0 and method 11; contradictions now close after two failing sessions) | `market_state.yaml`; `regime.py` |
| The volatility dial's source | Yahoo's same-day VIX (`yfinance.mkt_vix`) is primary, with FRED's next-morning VIXCLS kept as its check. The term-structure dual run continues to 23 December 2026: the champion is VX2/VX1 from Cboe's settlements and the challenger, which is published, is VIX3M/VIX. Under the Cboe hold (D45) the champion's legs take no new rows from 3 November, so the dial reads the published challenger. (new) | `market_state.yaml`, `term_structure`; `source_registry.yaml` `cboe` |
| The five added dimensions | Funding stress on absolute bands: stressed at 10 bp and above, watch at 0 and above. Policy at +25 and −25 bp. Valuation ranked over its full history beside five years. (new) | `market_state.yaml` |
| Per-horizon reads | 5, 20 and 63 sessions (Books C, B and A); bands 66 and 33; persistence 2. (new) | `market_state.yaml` |
| Calibration | 30 independent starts per row; horizons 5, 20 and 63 sessions; add-half smoothing. (new) | `altdata/state_calibration.py` |
| Dealer regime word | Prints only at net-to-gross ≥ 0.10 (ruled) | `reporting_stack.yaml`, `dealer_block` |
| Walls | The out-of-the-money walls; the all-strike peaks print as peaks | the dealer engine |
| Volatility event | A one-day VIX change of 15% or 3 points, either way. A five-day log change past its 95th percentile on a 20-year window. A crossing of the volatility dial's band. Compression within 5% of the 126-session low, held 3 sessions. | `vol_event.yaml` |
| The 12:30 volatility gate | Upward only: +15% or +3 points | `vol_event.yaml`, `midday` |
| The volatile-day flag | Any of: the overnight range past 1.5 times the 20-session average true range (at least 15 sessions); a gap of 1% or more; the VIX arm; a negative gamma dial; a tier-1 calendar event. (new) | `vol_event.yaml`, `volatile_day` |
| The one-day 10-year move | The day's absolute change past the 97.5th percentile of five years of changes, either way. "Not read" below 1,000 changes. (new) | `oneday_10y.yaml` |
| The gold event | A one-day move of 2.5%, or a five-day move past its five-year 95th percentile. The dollar leg is read through the price-source resolver. (new) | `gold_event.yaml` |
| The developed-market drawdown screen | Ten- and twenty-session drawdowns past their five-year 95th percentile. (new) | `dm_drawdown.yaml` |
| The EM shock screen's same-day rule | A member's one-day move at 4 sigma or more opens its country's shock that session, on an idiosyncratic or mixed session; a systemic session is excepted. Each past session is classified as of its own 16:45 close. Report-only. (new; pending, a112: D2-90 (a) to (d), ruled 2 November, not on the rehearsed tree) | `move_screen.yaml`, `same_day_sigma`, `classify_as_of` (on `a112-em-shock-screen-amendment`) |
| Relative options volume | 1.5 times (provisional; reviewed after 19 November). (new) | `opening_setup.yaml`, `relative_volume` |
| Outlier marks | 6 standard deviations of the last 60 changes, every family (session-set) | `data_quality.yaml` |
| Cross-source tolerances | VIX against VIXCLS: 0.01 (measured 15 October over 1,029 days). ^TNX against DGS10 and ^TYX against DGS30: not yet measured. | `data_quality.yaml` |
| The price-source parallel pairs | Inactive, and read by no check until a family's run starts. There are 49: five IBKR index-fund pairs (A93); three FRED pairs, the dollar index and the 10- and 30-year yields (A96); and 41 EDGAR pairs, 40 company-quarter pairs and one earnings-date pair (A102). Each tolerance is "to be measured on the overlap". (new) | `data_quality.yaml`: `inactive_pairs`, `inactive_pairs_fred`, `inactive_pairs_edgar` |
| Correction and bear | −10% and −20% from the 52-week high | `altdata/derived.py` |
| Credit widening | HY, BB and CCC +100 bp, and IG +40 bp, in three months (ruled 4 October). AA +25, BBB +50, EM corporate +75 and EM high yield +150 (session-set). | `metric_lenses.yaml` |
| Lens disagreement | 30 points between the five-year and the long-window percentile | `altdata/derived.py` |
| The store check's "dead?" | Past three times a key's own allowance. (new) | `tools/check_store_registry.py` |

**The price-source families** (`config/price_sources.yaml`, version 1; A96, A102; decisions 4 and 5 ruled D38 on 26 October). (new) There is one switch per family, and every reader asks the resolver for the active source's key. Every family ships on Yahoo, so nothing printed changes until a family is switched.

To switch, a family runs in parallel for 20 sessions. Then its `source` flips, and every reader moves at once. History is never spliced: a break label prints once beneath the first figure.

| Family | Members | Candidate source | Parallel run |
|---|---|---|---|
| `us_yields` | 2 (10- and 30-year) | FRED (DGS10, DGS30) | not started (`started: null`, 0 of 20) |
| `dollar_index` | 1 | FRED's broad index (DTWEXBGS), a different index | not started |
| `fundamentals` | 40 (eight names × five fields) | EDGAR's XBRL company facts | not started |
| `earnings_dates` | 3: history, next date, consensus | EDGAR's filings, for history only | not started |
| `us_index_funds`, `index_levels`, `futures_overnight`, `fx` | stubs, no members | IBKR (A93's writer, `ibkr_bars`, disabled) | not declared |

**The EDGAR gaps.** From an `earnings_dates` switch, two things become listed gaps: the next report date ("not tracked (no keyless source)") and the earnings surprise ("the consensus was Yahoo's; no keyless source"). EDGAR's reported EPS is knowable only at the periodic report, so a quarter's row waits for its 10-Q or 10-K (`price_sources.yaml`, `gaps`; `docs/briefs/a96-notes.md`, A102).

**Publication-lag families.** There are 34 in `config/publication_lags.yaml`, each stating its publisher's documented delay, its slack and its bound. The ones that state no delay, the Tuck data library and the shillerdata.com workbook's earnings and dividends, are listed with no family. (new: 19 October had no lag table, and 24 October counted 15, then 27 after the feed repair)

**The day-trading layer, DTH-1** (`config/dth1.yaml`; D41, 27 October; D52, 1 November; A92 and A92b). (new) The box prints two things, and never an order or a size:
- **The rules checklist.** A fixed block of four rules and the promotion test, in the 07:00 anchor after the ES read.
- **The ledger reader's aggregates.** These print in the Weekly's book section, as counts and R-multiples only, never a currency or a single trade's row.
  - The ledger's one home is the private Drive folder `chester-cards`, and the sweep copies it to the box's inbox; it is never read from the repository.
  - The reader reads only the date, the result in R, the rule broken and the status.
  - A row awaiting its broker statement is counted and named, never scored.
  - An open trade is counted as open.

**The dealer scorecard's pre-registration** (`docs/ledgers/dealer-scorecard-preregistration-2026-10.md`, dated 17 October 2026, never edited):
- A rate prints only from 20 scored sessions, and is no decision below 120 eligible sessions.
- 120 formation sessions come first, then 120 test sessions.
- The six tests use Benjamini–Hochberg at q = 0.10.
- A flag is demoted when a rolling 120-session interval includes its base rate for two consecutive months.

**Calibration ledgers.** Every ledger's pass rule is the order's where the order states one, else the first edition's; a box re-run applies it and may not change it. First editions run on the laptop from public sources and are labelled so; the box's re-runs write new dated files.

**The Alpha Lab's family registry** (`config/alpha_families.yaml`, version 1; Batch 19 item 99; B98). (new) Every hypothesis carries a `family_ref`. There are 63 families: sections of "151 Trading Strategies", plus two house entries. The family budget and the deflated-Sharpe variant counts key on it.

**The vendor writer** (`config/flashalpha.yaml`):
- The plan ends 31 March 2027.
- Symbols: SPY, QQQ, IWM, SPX and MSTR.
- The daily call budget is 60, planned at 57: 45 at 16:25, 6 at 09:45 and 6 at 12:30.
- The expected-move path prints "expected move: not served" on a 403 or 404.
- Its implied volatility is compared only on the first expiry of 20 days or more, from the 16:25 capture.
- The divergence data gate's tolerances: GEX 50% relative, DEX 15%, the flip 0.5% of spot, the walls 1.5%, and the regime word compared as a word.

**Risk limits and attention** (`risk-limits-v1`):
- capital base $300,000;
- net beta at the regime band's top plus 15 points;
- sector at most 30%;
- volatility exposure at most 0.5% of capital per vol point;
- duration at most 5% per 100 bp;
- Book A bands: Expansion 60–80%, Overheat 40–60%, Tightening and Contraction 20–40%;
- Transition for 10 sessions;
- attention: 7 packets a week and one sitting of at most 2 hours, as a rule; the third count is uncapped. (changed: "the third count uncapped" added)

**Prose and audits.**
- One call per section. A section the audit withholds gets one revision, and the rule broken, the failing span and the draft go back with it. This holds in the stack, the précis, the close, the anchor, the two notes and the Monthly's storyline fallback. (changed: the storyline fallback's three attempts became the one revision; the notes added)
- The Monthly's 10,000 words are a target, never trimmed for length (D20). (changed: "enforced by trimming")
- Voices scan: at most 60 model calls a day, 10 days' lookback, a 15-minute budget. The open note's voices pass gets 120 seconds, inside the same cap. (changed: the open note's pass added)

**Sources.**

| Family | Count |
|---|---|
| Price symbols | 127 (`yfinance_source.SYMBOLS`) (changed: 115) |
| FRED series pulled | 286 (`config.FRED_PULL_SERIES`) (changed: 266) |
| Official writers | 43 (`feeds.OFFICIAL_WRITERS`) (changed: 31) |
| External writers | 41 (`feeds.EXTERNAL_WRITERS`); the refused writers stay listed and request nothing (changed: 37) |
| Loggers | 7 (`altdata.loggers.load_all()`) |
| Option chains | the 17 captured names by Yahoo; SPX and SPCX by Massive at 16:31, their greeks behind the solver gate |
| Prediction markets | 2 venues |
| Voices sources | 22 declared, 16 enabled (`config/voices_sources.yaml`) (changed: 19 October gave no count) |
| Publication-lag families | 34 (new) |
| Price-source families | 8: 4 with members, 4 stubs (new) |

**The source registry** (`source_registry.yaml`). (new) It holds 146 sources. The 19 October tree held 115.

| Status | Count | Which |
|---|---|---|
| live | 90 | (as listed in the file) |
| built | 17 | built, not yet on a schedule or not yet read |
| active | 12 | |
| refused | 8 | MBA, Farside, PJM, LBNL, MOEA Taiwan, TSMC, Circle, Tether |
| not yet used | 5 | the IBKR live account and its four market-data entitlements |
| retired | 4 | CoinGecko, ICI's money funds, S&P DJI, the LBMA |
| not yet sourced | 4 | HKTMA, NAAIM, WGC, SIFMA |
| gated | 3 | the solver's derived greeks, Blockchair, IBKR stock loan |
| held | 2 | `cboe` (the VX settlements) and `cboe_indices` (COR1M, COR3M, DSPX), both `held_since: "2026-11-03"`: Cboe's terms forbid storage in a retrieval system (checked 30 October); held pending Doctrine #2; stored rows kept (D45, ruled 31 October; B95) |
| disabled | 1 | `ibkr_bars`, A93's writer, until the operator enables it |
| candidate (pending, a112) | 1 | `bcb_sgs`, Brazil's central bank SGS: its terms page answered HTTP 502 twice, so it is not passed, with no pair and no sample request |

**Keys held** (names only):
- FRED;
- Anthropic;
- the dashboard token;
- SMTP;
- Nasdaq Data Link;
- Massive, and its flat-files pair, read by one backfill tool only (changed: the flat-files pair added);
- FlashAlpha;
- OpenFIGI;
- the bitcoin-data service's free key (new);
- the backup's encryption passphrase (new);
- the SEC contact address.

**Keys not pursued**, under the standing rule of 16 October on sources:
- Webstat (its keyless TEC 10 export is read instead);
- the Bank of Korea's ECOS;
- the Bank of Thailand's API (its keyless table is read instead);
- Etherscan.

**Pending decisions:** the xAI path (item 50, Tranche 1) and the December vendor month.

**Sources that refuse, or that the system declines.** (changed: the October refusals and holds added)
- **Held:** Cboe's two readers, from 3 November (above).
- **Declared refused:**
  - MBA (an HTTP 403 on its robots.txt);
  - Apartment List (403; Zillow is read alone);
  - Farside (403 through a Cloudflare challenge);
  - PJM, LBNL, MOEA Taiwan, TSMC, Circle and Tether, as the registry states each.
- **Disabled:**
  - Yahoo Finance's voices index (its feed answers 404). Its candidate replacements were refused by their robots.txt and terms.
  - In the voices list: CNBC (403), Goldman's insights (403), and Morgan Stanley and Nuveen (time out).
- **Listed gaps:**
  - WGC's files, which need a login (the central-bank leg reads the IMF's IFS);
  - DTCC's per-name CDS volumes;
  - the next earnings date and the earnings surprise, from an EDGAR switch (above);
  - Brazil's local rates (pending, a112).
- **Withdrawn or retired:**
  - S&P DJI's EPS workbook, printed "not tracked (source withdrawn)";
  - CoinGecko, whose terms bar storing its data;
  - the LBMA writer;
  - the Google News story queries, refused by their robots.txt.
- **Other:**
  - Bybit is switched off by a country block.
  - State Street's GLD archive is refused to the API host by robots, so the operator drops it once.
  - GeckoTerminal's site robots disallow crawling; its documented API is read under its own terms.

**Superseded keys.** (new)
- IOER, by IORB (still pulled, read by nothing).
- The overnight 10-year index fields, by the daily index.
- The LBMA price, by the COMEX front future.
- WGC's keys, by the IMF's.

**Scans outside the repository.** These are recorded in the Master Guide's record of the chat-side tasks (`docs/master-guide/chat-tasks.yaml`, the Guide's Table 2), which since B102 also carries the readable editions' register rows. Appendix F covers the readable editions themselves, and they are not repeated here. (changed: the list's members, below, and the register added)
- the Guide to the Markets read (the 6th of January, April, July and October);
- the Monthly signal scan (the 25th, 06:57);
- the Saturday crypto mechanism scan (retiring);
- the AI-risk consensus-drift scan (the 20th of even months);
- the reading-shelf publication watch (the 12th and the 27th), with the six houses' capital-market-assumption files;
- the AAII weekly read (Thursdays), whose weekly file the sweep now copies from its own folder;
- the MSTR/MSCI event watch (weekdays 2–30 November, and 1 December);
- the FlashAlpha tasks (retiring);
- the X digest (daily 06:00) and its triage (06:50), a pilot since 17 October;
- the ES day-trading cards and the Sunday map, in the private folder `chester-cards`;
- the Saturday brief, which writes the Alpha Lab's inbox;
- the Alternative Assets Quarterly's scan (planned for January 2027).

**Pending the sitting.** Doctrine #2 (7–8 November) may change values in this appendix. These are the pack's decision rows that would, by number only (`docs/briefs/doctrine-2-pack-2026-11.md`):
- D2-2, D2-4: the lag families and the session-set values;
- D2-5 to D2-8: the budgets, the notes' caps, the anchor's caps and the guards;
- D2-10: the chart caps;
- D2-26, D2-27: the attention budget and the third count;
- D2-31: the December vendor month;
- D2-34: the volatile-day flag's values;
- D2-44, D2-60: the printing floor;
- D2-68: the v1.13 bump;
- D2-73: the price-source migration;
- D2-74: the Cboe hold;
- D2-75: the 23-hour session;
- D2-85: the X layer's cadence;
- D2-90: the EM shock screen's amendment.

---
