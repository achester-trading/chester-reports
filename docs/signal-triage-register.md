# Signal Triage Register

**One record per proposal; also the record of what was rejected and why.**

| | |
|---|---|
| Authority | [Change order — Signal Triage, Consolidated](change-order-signal-triage-2026-09-25.md), signed 2026-09-26 (§13) — §1.2 creates this register; §3 is the source of every entry below |
| Seeded | 2026-09-26 by ST-0, with SR-1…SR-27 |
| Intake | New proposals are written on the [signal intake template](templates/signal-intake.md) and filed here as the next free SR number |
| Calibration ledgers | [`docs/ledgers/`](ledgers/README.md) — a gate's result is written back to the entry it tests |

## How to read this register

- **Entries are copied verbatim from §3 of the order.** Section references
  inside them (§1.x, §2.x, §6, Appendix C, G-n) are to the order; `R`-numbers
  are the explicit rejections, reproduced at the foot of this file. *[integ.]*
  marks an integration edit made when Batches 1 and 2 were consolidated.
- **Every entry carries a register status and its build slot.** The status is
  this register's own field; the build slot is the "Built in" column of the
  order's §3 master table. ST-n are the sessions of the order's §8.
- **Dispositions change here, nowhere else.** A calibration ledger that fails
  its gate updates the entry's status to `DEFERRED — gate failed` with the
  statistic (§9); a passed gate records the ledger it passed in.
- **Rights come only from a passed gate** (§1.3). A third party's conclusion is
  recorded in the entry and never inherits rights. Everything here is
  REPORT_OK-class (§1.7); no entry can raise DECISION_BLOCKED or enter a
  composite.
- **Mechanism-watch candidates are not register entries.** They live in the
  `mechanism_watch` store table under SR-10.
- **Numbers are never reused.** A rejected or superseded entry keeps its number.

## Index

| SR | Thread | Item (source, date) | Ruling | Rights class | Built in | Status |
|---|---|---|---|---|---|---|
| 1 | E | Growth/Value relative performance (Weniger, 8 Sep) | Adopt mechanized; reject trendline | Narrow flag (after gate) | ST-8 → backlog panel | ADOPTED — gate pending |
| 2 | X | Yen carry stack (chat, 10 Sep) | Adopt four metrics; unwind tell + positioning first | Narrow flag → overlay queue #1 | ST-5, ST-10 | ADOPTED — gate pending |
| 3 | X | China external position (shadow-reserves post, 11 Sep) | Adopt panel inputs; reject conclusion; panel assembly deferred | Panel only | ST-2 feeds; tail edits by hand | ADOPTED — panel inputs; assembly deferred |
| 4 | X | US–China 10y spread / RMB funding (X post, 10 Sep) | Adopt as SR-2/3 inputs; devaluation tell in full; reject fade | Narrow flag (tell) | ST-5 | ADOPTED — gate pending |
| 5 | E | Consumer credit impulse (deGraaf/RenMac, 8 Sep) | Adopt bull side as trigger candidate, RS tell; bear side as tilt | Trigger candidate / modifier | ST-8; wired ST-11 | ADOPTED — gate pending |
| 6 | R | Yield move attribution (Runkevicius, 15 Sep) | Adopt block as `rates.driver` evidence; reject single-model reading | Confidence modifier | ST-3 | ADOPTED — gate pending |
| 7 | E | Hiking-cycle conditional table (Macrobond) | Adopt table by hand; reject unconditional average | None (base rate) | Tranche H | ADOPTED — base rate, by hand |
| 8 | E/A | Bear-market rally structure (Lemand, 19 Sep) | Adopt audit + bottom gate + Doctrine rule candidate | Gate | ST-9; wired ST-11 | ADOPTED — audit pending |
| 9 | R/A | 5.25% and stock-bond correlation (Simon White, Sep) | Adopt as `rates.driver` correlation member and Book A rule A-1; reject level | Confidence modifier | ST-3 | ADOPTED — regression in backlog |
| 10 | D | Digital Asset Mechanism Watch — Pearl (PRL) signposts S1–S8 and the emerging-mechanism scan (19 Sep order, integrated 26 Sep) | Adopt; watch-level rights only (MW-2) | Narrow flag (idle-GPU D6); discovery/attention otherwise | ST-13, ST-14, ST-15; Sunday block at ST-10 | ADOPTED — watch-level rights only (MW-2) |
| 11 | — | *Reserved:* Consensus drift (19 Sep batch Part C) | Backlog | — | Appendix C | RESERVED — backlog (Appendix C) |
| 12 | A | Investor bond allocation (Topdown, 24 Sep) | Adopt Book A line + conditional base rate; reject unconditional contrarian read | Modifier (after gate) | ST-6, ST-7 | ADOPTED — gate pending |
| 13 | E | Tech vs. defensives valuation (Topdown/LSEG, 24 Sep) | Adopt as SR-1 anchor + base rate; reject rates channel | Modifier after SR-1 gate | ST-8 | ADOPTED — gate pending |
| 14 | X | EM absolute and relative (Topdown/LSEG, 24 Sep) | Adopt US-vs-RoW line + trend flag; reject "decadal turn" | Narrow flag (after gate) | ST-8 | ADOPTED — gate pending |
| 15 | A | Cross-asset valuation z-scores (Topdown/LSEG, 24 Sep) | Adopt light strip + rebalancing modifier; reject "cheap commodities" | Modifier (after gate) | ST-6, ST-7 | ADOPTED — gate pending |
| 16 | E | Hyperscaler debt supply / absorption (Bloomberg via Lemand, 24 Sep) | Adopt Factor I funding panel + flag; reject issuance headline | Narrow flag | ST-4/ST-6 | ADOPTED — gate pending |
| 17 | R | Real-yield-led selloff (Alpine Macro / Zhao, 24 Sep) | Merged into `rates.driver` (DKW arbiter); no new analysis | None new | ST-3 | MERGED into `rates.driver` |
| 18 | C | Oil inventories vs. operational floor (JPM/Bloomberg; 15–25 Sep) | Adopt buffer state; reject chart as a print (projection fixture) | Narrow flag | ST-2, ST-6 | ADOPTED — gate pending |
| 19 | E | "3-month / 1-year beta" chart (Monchau) | DEFERRED — definition required | None | Appendix C | DEFERRED — definition required |
| 20 | X | IMF COFER Q1 2026 + reserve tracker (25 Sep) | Adopt Factor V scorecard; reject level as signal | None | ST-2; Tranche H | ADOPTED — scorecard, no rights |
| 21 | R | Oct 28 hike probability 70–77% (Bianco, 24 Sep) | Adopt Fed–market gap, credibility flag, Warsh cell, PM case; reject political framing | Narrow flag | ST-4 | ADOPTED — gate pending |
| 22 | R | 5y auction 5.033%, TLT record low (Padley, 24 Sep) | Adopt auction absorption; reject "meltdown"; Doctrine note | Narrow flag; A-3 input | ST-1, ST-4, ST-7 | ADOPTED — gate pending |
| 23 | R | G4 issuance gap vs. real yields (Lustig, 24 Sep) | Adopt — highest value; US monthly + projection | Modifier | ST-4, ST-7 | ADOPTED — gate pending |
| 24 | R | 5y5y breakeven vs. commodity producers (Costa, chart 12 Sep) | Adopt de-anchoring flag (definition only); reject trendline and producers-as-lead | Narrow flag | ST-4 | ADOPTED — definition only, no gate possible |
| 25 | E | Burry AI shorts (Monchau via Bull Theory, 24 Sep) | Reject as signal; adopt memory-cycle tell; narrative-register entry | None | ST-4 (+MU) | REJECTED as signal — memory-cycle tell adopted |
| 26 | X/R | TIC flows, 12m to Jul 2026 (Riemann, 24 Sep) | Adopt composition read; reject "demand collapsed" | Absorber-fragility modifier (after gate) | ST-2, ST-4 | ADOPTED — gate pending |
| 27 | X/R | TIC Major Foreign Holders, 12m change (research note) | Adopt holder panel with mechanism tags; reject "China dumping" | Absorber-fragility modifier (after gate) | ST-2, ST-4 | ADOPTED — gate pending |

---

## Entries

### SR-1 Growth vs. Value relative performance (Weniger, 8 Sep 2026) — Thread E

**Register status.** ADOPTED — gate pending · **Built in.** ST-8 → backlog panel

**Ruling.** Adopt the ratio, mechanized. Reject the 1980–2000 trendline as a rule: three touches in fifty years, and the line exists only on a linear axis (drawn through the same 1980 and 2000 points in log space, 2021 never touched it and 2026 has not). Defer any T&B overlay input until validation shows information beyond top-10 weight.

**Home.** Monthly style-regime panel; Book B pair trade; Book A tilt (cap-weight → value/equal-weight). Mechanism in Equities (concentration chapters); tactical expression in Positioning & Flows. Fills a real gap: the stack is heavier on top detection than on what leads next. *[integ.]* SR-13's tech/defensives spread is this panel's valuation anchor; the two are one backtest session (ST-8) and one panel.

**Rights.** Narrow flag: "Style regime — growth extreme / rotation triggered." Only after the gate.

**Rule to test.** Log Growth/Value total-return ratio, z-score vs. its 10-year trend > +2 (via `derived_forms`), followed by a break: ratio below its 40-week MA, or >8% off its 52-week high. Expression: long IVE / short IVW (or IWD/IWF), sized as a pair, hard stop on a new ratio high (2023 is the reason for the stop).

**Data.** IVW/IVE, IWF/IWD daily from 2000 via yfinance (total return; point-in-time). Ken French HML monthly from 1926 for long calibration (library revised occasionally — log the vintage). S&P's own index history is licensed; skip. *Lives in:* `yfinance.mkt_ivw` etc.; `calc.gv_z`, `calc.gv_break`.

**Validation gate.** Forward 3/6/12-month value-minus-growth after each trigger, HML from 1963 and ETFs from 2000; hit rate and asymmetry; check the late 1990s for early fires and 2023 for the reversal. Ledger in Base Rates. Pass: positive expectancy after costs at 6 and 12 months across ≥6 non-overlapping episodes. Offline (ST-8).

### SR-2 Yen carry stack (chat question, 10 Sep 2026) — Thread X

**Register status.** ADOPTED — gate pending · **Built in.** ST-5, ST-10

**Ruling.** Adopt. Confirmed gap: the yen section of the Alt Asset build carries carry-trade prose with `[LIVE DATA REQUIRED]` placeholders; the Monthly and the June 2026 rate-expectations spec pull only the US legs. Currencies and The Rate and Liquidity Machine explain the mechanism; nothing computes it.

**Home.** Monthly Factor IV panel; T&B Liquidity & Funding Stress overlay input after the gate (an unwind is a deleveraging mechanism) — **queue position #1** (§2.6); Daily Cascade risk-off flag in the 07:00 anchor, with the 12:30 alert if the unwind tell trips intraday. Books A and C. *[integ.]* Metric 3 (hedged carry) is consumed by the Duration Absorption block as the explanation of Japan's holdings line (SR-27) — computed once here.

**Metrics (four, not one).** (1) Front-end differential: US 2y (or 3m) minus Japan, plus its 60-day change — velocity mattered in Aug 2024, not level. (2) Positioning: CFTC yen net non-commercial position, z-scored — the fuel. (3) Hedged carry for Japanese investors: 10y UST − (3m USD − 3m JPY); negative means hedged Treasury buying stops — the Treasury-demand / term-premium channel. (4) Unwind tell: USDJPY 5-day move against a realized-vol spike.

**Rights.** Narrow flag at launch; overlay input after the gate, in queue order.

**Data.** FRED Japan 10y and 3m (monthly); Japan MoF daily JGB yield CSV; CFTC COT weekly (Tuesday positions, Friday release — `available_at` = release); USDJPY held (`fred.usd_jpy`, plus yfinance daily). JPY implied vol and risk reversals are not free; use realized. *Lives in:* `altdata/sources/cftc.py`, `mof_jgb.py`; `calc.jp_front_diff`, `calc.jpy_pos_z`, `calc.jp_hedged_carry`, `calc.jpy_unwind`; candidate contradiction row `carry_vs_vol`.

**Validation gate.** Anatomy check on Oct 1998, 2007–08, Jan–Feb 2016, Aug 2024 (narrowing differential + crowded shorts + vol spike). Pass: all four flagged with ≤2 false positives 1998–2026 at the chosen thresholds. Offline (ST-8); thresholds then set in `config/market_state.yaml`.

### SR-3 China external position (shadow-reserves post, 11 Sep 2026) — Thread X

**Register status.** ADOPTED — panel inputs; assembly deferred · **Built in.** ST-2 feeds; tail edits by hand

**Ruling.** Adopt as a Monthly China panel. The post's facts are accepted (Setser: ~$6T state-controlled foreign assets — SAFE's ~$3.4T plus state commercial banks, policy banks and CIC; NIIP north of $3T; the PBOC's balance sheet is FX and bank loans, not government debt). Its conclusion is rejected: external creditor status and an RMB-denominated debt deflation coexist (Japan 1990). "Hidden" overstates it — the assets appear in the quarterly IIP; they are not classified as reserves, and much of the shadow layer is illiquid. *[integ.]* Panel **assembly** is deferred (Appendix C, as tranched on 19 Sep); its inputs are fetched in ST-2 so assembly is a rendering task; the China Treasury-holdings row comes from the shared `tic.*` family with SR-27's custodial caveat (G-9).

**Home.** Monthly (Alt Asset folds into the Monthly per the 7 Sep ruling); tail register; Factor V thread (reserve diversification, official gold bid; explains why China's Treasury holdings fell without dollar selling).

**Panel.** SAFE reserves (monthly); banks' net foreign assets from the quarterly IIP; TIC China Treasury holdings (monthly, both vintages); CNY fix vs. band (daily); from SR-4: CGB 10y level, US–China 10y spread, CNH–CNY gap, CNH HIBOR.

**Tail register edits (by hand, Tranche H).** CNY balance-of-payments crisis: score low — the state controls the capital account and official reserves alone cover external debt; any sharp devaluation is a choice, not a forced event. Domestic deflation / balance-sheet recession: keep fully live (the Koo case in the Debt Cycles brief). New scenario: deliberate devaluation to export deflation — Factor III/IV cross; hits commodities, EM FX and US inflation expectations together; tell defined in SR-4.

**Rights.** Panel only.

**Data.** SAFE (reserves, IIP, BoP); US Treasury TIC; CFETS central parity. All free. *Lives in:* `altdata/sources/safe.py`, `tic.py`, `cfets.py`.

### SR-4 US–China 10-year spread and RMB as funding currency (X post, 10 Sep 2026) — Thread X

**Register status.** ADOPTED — gate pending · **Built in.** ST-5

**Ruling.** Adopt as inputs to SR-2 and SR-3. Reject "widest ever" as a fade signal: a 24-year record set inside a four-year inverted regime (US above China through much of the 2000s, China above the US ~2010–2022, inversion since April 2022), and the two legs price off unrelated regimes; Japan–US stayed wide for two decades. The devaluation tell is built in full now (ST-5); it is also SR-14's exit.

**Home.** China panel (spread and CGB level as regime context; CGB below 2% is the Japanification gauge on its own). Funding-currency stack: the RMB leg beside JPY in SR-2 — panda-bond issuance, CNH HIBOR, CNH–CNY gap — with the note that the PBOC controls offshore CNH liquidity (overnight CNH HIBOR reached 66% in January 2016), so RMB carry unwinds are policy-driven and abrupt.

**Rights.** One narrow flag — the deliberate-devaluation tell: the fix stops leaning against the previous close, the CNH–CNY gap widens with CNH weaker, and state banks stop selling dollars (third leg a by-hand field until sourced).

**Data.** DGS10 (held); FRED China 10y monthly (IRLTLT01CNM156N) and ChinaBond daily; CFETS fix; CNH=X (yfinance); HK TMA CNH HIBOR; panda-bond volumes as a monthly `manual_input`. *Lives in:* `calc.cny_fix_dev`, `calc.cnh_cny_gap`, `calc.uscn_10y_spread`, `calc.deval_tell`; candidate contradiction row `fix_vs_offshore`.

**Validation gate.** Calibrate fix-deviation and CNH–CNY thresholds on Aug 2015–Jan 2017 and Sep 2022–Sep 2023. Base rate for spread persistence from Japan–US 1998–2022. Offline (ST-8).

### SR-5 Consumer credit impulse (deGraaf / RenMac, G.19 July print, 8 Sep 2026) — Thread E

**Register status.** ADOPTED — gate pending · **Built in.** ST-8; wired ST-11

**Ruling.** Adopt the bull side (bottom decile of the 6-month-average net-change rolling z-score: 84% W/L, ≈+9% six-month expectancy, double the base rate) as a T&B bottom-confirmation candidate — same asymmetry as the existing calibration, stronger at bottoms than tops. Log the bear side (top decile: 59% W/L, ≈−0.5% expectancy against ≈+4.5% unconditional) as a Monthly tilt only. Adopt the consumer-dependent relative-strength tell. Reject as a standalone top signal. *[integ.]* Enters T&B's bottom side **after** SR-8's gate (§2.6), so it is tested against the raised threshold.

**Mechanism notes for the register.** Late-cycle borrowing sustains spending income no longer supports; the clean historical hits (1969, 1973, 1979, 2000, 2007) were inflation-and-tightening peaks; 1994–95 was the loud miss. ~70 overlapping observations reduce to ~12 episodes; rolling z-scores inflate after quiet stretches (2023–25); composition matters (revolving spike = distress, nonrevolving spike may be auto pull-forward).

**Home.** T&B bottom side; Monthly consumer/credit pillar; weekly Book B tell (XLY/XLP — the held `calc.cyclical_over_defensive` where its definition matches; equal-weight discretionary vs. SPY; homebuilders).

**Rights.** Bull side: trigger candidate after gate. Bear side: confidence modifier. RS tell: narrow flag.

**Data.** TOTALSL, REVOLSL, NONREVSL (FRED) with ALFRED first-print vintages. G.19 lag ≈5 weeks; heavily revised. *Lives in:* `fred.consumer_credit*` (new, with vintages once O.16 lands; the calibration script pulls ALFRED directly meanwhile); `calc.cc_z`, `calc.cons_rs`.

**Validation gate.** Replicate at 5- and 10-year z windows; count non-overlapping episodes; run the revolving-only variant; rerun everything on first prints. Bull side passes if first-print six-month expectancy stays ≥2× unconditional across ≥8 episodes. Offline (ST-8).

### SR-6 Yield move attribution (Runkevicius, SF Fed decomposition, 10y at 5%, 15 Sep 2026) — Thread R

**Register status.** ADOPTED — gate pending · **Built in.** ST-3

**Ruling.** Adopt an attribution block. Reject the single-model conclusion: term-premium models (SF Fed Christensen–Rudebusch, NY Fed ACM, Board Kim–Wright) disagree on level and can disagree on the sign of a change over months; the "expected short rate" leg is a residual, not a survey; ACM in particular pushes short-run shocks into term premium. *[integ.]* **The block is the evidence set of `rates.driver` (§2.1.1), not a tag of its own.** The two-state regime tag in the 19 Sep ruling (path-driven-real; term-premium/supply) becomes the `fed_path` and `term_premium` cells; `growth` and `mixed` are added; SR-17's DKW real-side split joins as the fourth model and the sign arbiter; SR-9's correlation is a member.

**Home.** The Rate and Liquidity Machine; `rates.driver` in the market-state object; feeds the Rate Repricing Velocity overlay's hawkish/dovish tag when T&B is built (G-7) and the Valuation trigger's ERP input; Book A rule A-1; Warsh matrix.

**Block.** For 1-week, 1-month and since-event windows: Δ10y = Δbreakeven + Δreal (`fred.breakeven_10y`, `fred.tips_10y`); Δ10y = Δ2y + Δ(10s–2s) (held series); model term premia as tie-breakers — Kim–Wright (THREEFYTP10), ACM, SF Fed, DKW real term premium. Cell rule as in §2.1.1.

**Rights.** Confidence modifier: `fed_path` → weight the valuation-compression channel up in T&B. The 5% level itself is logged as a valuation input (ERP; earnings yield below bond yield at a >20× forward multiple), not an event.

**Data.** DGS2/DGS10/T10YIE/T5YIFR (held); **DFII10 (new — not among the 59)**; THREEFYTP10 (new); ACM CSV (NY Fed, new source); SF Fed Treasury Yield Premiums (per publication, new source); DKW (Fed Board Excel, new source); SPY, TLT (yfinance). *Lives in:* `fred.tips_10y`, `fred.term_premium_kw`, `acm.*`, `sffed.*`, `dkw.*`; `calc.attr_*`, `calc.corr_spy_tlt_60d`; `rates.driver`.

**Validation gate.** Run the four models side by side over Feb–Sep 2026; where they disagree on sign, the curve decomposition arbitrates. Calibrate forward equity returns and stock-bond correlation on the bear-flattening set (1994, Q4 2018, 2022) vs. the bear-steepening set (2013, Aug–Oct 2023), plus SR-17's four DKW episodes. Offline ledger (ST-3); cell thresholds then declared in config.

### SR-7 S&P returns during Fed hiking cycles (Macrobond, five cycles since 1994) — Thread E

**Register status.** ADOPTED — base rate, by hand · **Built in.** Tranche H

**Ruling.** Adopt a conditional base-rate table. Reject the unconditional average: the chart measures first hike → first cut, which is the calm window; three of the five were followed by 25–55% declines after the endpoint (2001, 2007, 2020); the sample is Great Moderation only, and the one "coincidence" (1999–2000, CAPE 44) is the only cycle that began at current valuations. *[integ.]* Built by hand (as tranched); SR-21's rows join the same table.

**Home.** Base Rates (table); Debt Cycles brief, tops-from-inside Part (hiking into a bubble: 1929, 1937, 1973, 2000, 2018); Bull Rebuttal gate entry for "stocks rise during hiking cycles." Book A.

**Table spec.** All cycles since 1955 (~15 rows): first hike, last hike, first cut; returns first hike→last hike, last hike→first cut, first cut→+12m; max drawdown inside the cycle and within 12 months after the last hike; conditioned on starting CAPE (>30 vs. <25) and on supply-shock inflation; cut type (insurance vs. recession); **plus SR-21's columns: whether the Fed conceded to or refused market pricing at the turn, and the long end's 3m move after.** Monthly note: a cycle starting at CAPE ~40 has n=2 analogs (1999, 2022), both with drawdowns first.

**Rights.** None (base rate).

**Data.** FEDFUNDS, USREC (FRED, new); Shiller data; yfinance; hand-coded cycle-date table `data/reference/fed_cycles.csv`.

### SR-8 Bear-market rallies as structure (Lemand, Nasdaq 2000–02, 19 Sep 2026) — Threads E and A

**Register status.** ADOPTED — audit pending · **Built in.** ST-9; wired ST-11

**Ruling.** Adopt a T&B false-bottom audit, a bottom-side gate and a Doctrine rule candidate. The bottom side was calibrated on real bottoms; the false ones (five rallies of 12–45% inside a 78% decline, each a "bottom" in real time) are the untaken test. *[integ.]* The audit is offline (ST-9) and produces the gate spec; wiring waits for T&B full (ST-11). The gate is Book A rule A-2 (§2.4) and precedes SR-5's trigger in the bottom-side queue.

**Home.** T&B; Operating Doctrine; Positioning & Flows (fuel metrics); operator behavioral paper (behavioral inventory: the dip-buying cohort, the rally trap); Daily "rally inside bear" flag (ST-10).

**Confirmation set.** Breadth thrust in the first weeks; leadership by new groups rather than the most-shorted prior leaders; HY spreads tightening through the rally; VIX term structure back in contango; a successful retest. Time prior: bears off valuation peaks run two to three years, so a bottom four months in is a low-probability call by base rate alone.

**Gate.** Once the T&B top side has fired and price is below a falling 200-day, the bottom threshold rises and two of the confirmation set are required before Book A re-enters; rallies in that state are Book C material.

**Doctrine rule candidate (number to be assigned).** "In a declared bear regime a rally is a mechanism, not a signal. Book A re-entry requires the bottom composite plus confirmation. Size on the assumption that a bear rally and a new bull are indistinguishable in real time."

**Fuel metrics.** FINRA margin debt (monthly, new); leveraged-ETF AUM from issuer daily files (new); FINRA short interest (**already registered**: `finra.short_interest`, `finra.short_interest_days_to_cover`); breadth (**already registered**: `calc.breadth_*`); VIX term structure (**already registered**: `calc.vix3m_over_vix`, `cfe.vx1/2/3`).

**Validation gate.** Replay the bottom side rally-by-rally through 2000–02, 2007–09 (Mar 2008), 1973–74 and 2022 (Mar; Jun–Aug); count false bottoms. Score each confirmation element on whether it separates those from Oct 2002, Mar 2009, Oct 1974 and Oct 2022. Elements that discriminate enter the gate; elements that don't are dropped.

### SR-9 5.25% and stock-bond correlation (Simon White, Sep 2026) — Threads R and A

**Register status.** ADOPTED — regression in backlog · **Built in.** ST-3

**Ruling.** Adopt as the correlation member of `rates.driver` and as Book A rule A-1. Reject 5.25% as a line: it is an era effect — the 10y sat above 5.25% almost continuously 1973–98 and below it 2001–23, and the correlation flipped negative around 1998–2000 when growth shocks replaced inflation shocks as the dominant driver. Yield level is a proxy for the inflation regime, not a cause. *[integ.]* The scatter regression is deferred (Appendix C, as tranched); the level prior stays a by-hand note; the correlation itself is `calc.corr_spy_tlt_60d`, computed once.

**Home.** The Rate and Liquidity Machine; Book A hedge-substitution rule (A-1); Market Structure & Cascades (risk-parity and target-vol de-levering as a named cascade channel); Warsh matrix — the reaction-function variable "does the Fed defend the front end or the long end," which `rates.driver` adjudicates in real time (10y rising through breakevens/term premium with the front end anchored = the long end is lost; rising through the expected path = tight but credible).

**Rule.** Yield-level prior: above ~5.25%, treat a positive correlation reading as persistent rather than transient. When the driver is `fed_path` or `term_premium` (or the correlation member is positive and persistent), Book A's hedge mix shifts from duration to T-bills, gold, commodities, trend-following and option structures (defined-outcome work applies here).

**Rights.** Confidence modifier.

**Data.** ^GSPC daily; constant-maturity 10y return proxy built from DGS10 (1962–); SPY, IEF/TLT for the live reading; core CPI (held) and its rolling volatility as the regime variable. *Lives in:* `calc.corr_spy_tlt_60d`, `calc.infl_vol`.

**Validation gate (backlog).** Reproduce the scatter (2-year rolling correlation of weekly changes vs. 10y level). Regress next-6-month correlation on yield level and inflation volatility. If level adds nothing, inflation vol is the lever and 5.25% stays a heuristic.

### SR-10 Digital Asset Mechanism Watch — Pearl (PRL) and the emerging-mechanism scan (change order of 19 Sep 2026; integrated 26 Sep) — Thread D

**Register status.** ADOPTED — watch-level rights only (MW-2) · **Built in.** ST-13, ST-14, ST-15; Sunday block at ST-10

**Where the rest lives.** The full specification — rulings MW-1…MW-10, signposts S1–S8, derived metrics D1–D6, the thesis-status rule, block layouts and the emerging-scan specification — is §2.7 of the [change order](change-order-signal-triage-2026-09-25.md). Emerging-mechanism candidates live in the `mechanism_watch` store table (rendered by `make mechanism-register` once ST-15 lands) and are referenced from this entry; they are never entered as rows of this register.

**Ruling.** Adopt. PRL under systematic coverage as a `crypto.watch` instrument with signposts S1–S8, derived metrics D1–D6 and a rule-based thesis status; a weekly emerging-mechanism scan with a materiality bar, a store-backed register and a human-gated intake path. Full specification in §2.7.

**Home.** Sunday 05:00 anchor (Mechanism Watch block, at D6); Monthly Macro Report (Digital Asset Mechanism Watch part); Alternative Asset dashboard Surveillance tab until the fold; Disruptive Themes narrative register (Factor I or V entries, graded); Digital Assets (dated appendix). Excluded from the Daily Cascade except the 12:30 information line.

**Mechanism.** Factor I: difficulty-vs-price behaviour reads idle GPU capacity seeking yield — the idle-GPU flag. Factor V: a compute-backed native-currency claim. Thesis for the coin itself: paid compute must overtake speculative mining, a PRL demand sink must ship, and the week-one overhang (38.9% of supply minted in the first 5.9 days at difficulty 1) must dilute before a tier-1 listing is plausible; the 57.7M PRL gap between code-derived and reported circulating supply is unexplained; three small venues with one at ~91% of volume; Nvidia-only mining. Evidence: Hashrate Index (2 Jun), Together AI announcement (15 May), Tom's Hardware (31 May), Alea Research, the Pearl repo and explorer, the Komargodski–Weinstein paper (arXiv 2504.09971).

**Data.** CoinGecko (`pearl-2`; price, market cap, 24h volume, circulating, tickers) weekly plus a daily close; explorer height/difficulty weekly with the MW-4 fallbacks; emission and supply from the Appendix E formula; S1, S2, S7, S8 as `manual_input` narrative fields fed by the scan. *Lives in:* `altdata/sources/coingecko.py` (existing switch turned on), `altdata/sources/pearl_explorer.py`; `calc.prl_supply_code`, `calc.prl_overhang`, `calc.prl_supply_gap`, `calc.prl_emission_to_volume`, `calc.prl_venue_conc`, `calc.prl_idle_gpu_flag`, `calc.prl_thesis_status`; `mechanism_watch` store table.

**Rights.** Narrow flag (D6) under Factor I; discovery and attention otherwise; graded narrative-register entries; no scoring, no theme changes, no overlay path (MW-2). Candidates: register status only, human PROMOTE/REJECT (MW-6).

**Validation.** Formula unit tests (block 1 ≈ 3,229.6 PRL; block 113,770 ≈ 2,339.4 PRL; supply at 113,770 ≈ 312.72M); D4/D6 thresholds calibrated after 90 days; the 2.7.8 usefulness test at 90 days; quarterly MW-7 review from December 2026. Falsifiers: the DETERIORATED conditions of 2.7.5; MW-7's demotion and removal rules.

**Disposition.** Adopt as Tranche 5 (ST-13, ST-14, ST-15; Sunday block in ST-10; dated appendix in ST-L; parallel run and decommission in ST-12). ≈25.5 h of sessions plus the shared items. The interim Saturday scan runs until MW-9.

### SR-11 *Reserved* — Consensus drift — 19 Sep batch Part C

**Register status.** RESERVED — backlog (Appendix C) · **Built in.** Appendix C

**Where the specification lives.** Appendix C of the [change order](change-order-signal-triage-2026-09-25.md), "19 Sep batch Part C (by reference; register SR-11)". This number is held so the consensus-drift item keeps its place if it is ever scheduled; it has no ruling, rights or build slot until then.

Register entry points to the Part C specification and its backlog status (Appendix C). The interim bimonthly scan (§1.12) continues.

### SR-12 Investor bond allocation (Topdown Charts, AAII + ICI + Fed FoF blend, 24 Sep 2026) — Thread A

**Register status.** ADOPTED — gate pending · **Built in.** ST-6, ST-7

**Ruling.** Adopt as a Book A positioning line plus a conditional base-rate table; reject the unconditional "classic contrarian play." No T&B or composite rights.

**Home.** Monthly Cheap-and-Unloved block (§2.4); Portfolio Construction (the duration-vs-commodities barbell; rule A-3); Base Rates (the table).

**Mechanism.** The series is mostly the complement of two things already scored — the equity share (a price artifact carried by CAPE ~40 and the Complacency overlay) and the cash share built when bills paid 4–5% — so the ~18.5% trough is correlated confirmation of late-cycle positioning, not independent information, and would double-count Valuation in T&B. The one independent piece is the bond-vs-cash split: cash rotating into duration as bill yields fall is a testable flow mechanism and the real catalyst behind the contrarian case. Regime caveat is the whole game: the 1987 start makes the sample disinflation-only, and both prior troughs (2000, 2007) resolved through recession-driven bond rallies under negative stock-bond correlation. In an inflation regime a low allocation is a persistent condition, not a setup (Z.1 equivalents in the late 1960s/1972 were followed by a decade of real losses). "Underowned" pays only in the `growth` or `term_premium` cell.

**Data.** AAII allocation survey (monthly from Nov 1987; three numbers a month as `manual_input`); ICI fund assets by type (monthly, free); Fed Z.1 via FRED (quarterly, ~10-week lag) — the Z.1 complement extends the window to the early 1950s and adds inflation-regime episodes. *Lives in:* `manual.aaii_*`, `fred.z1_*`; `calc.bond_alloc`, `calc.bond_cash_split`.

**Rights.** Base rate; confidence modifier for Book A duration sizing only after the gate; input to rule A-3.

**Validation gate.** Episodes: bottom-decile readings (AAII 2000, 2007, 2024–26; Z.1 adds late 1960s/1972). Statistic: forward 12m and 36m 10y Treasury total return, nominal and real, vs. cash, split by trailing CPI ≥4% / <4% and by 1y stock-bond correlation sign. Pass for the modifier: in the growth/term-premium cell, median real return beats unconditional with ≥2/3 hit rate. If the split does not separate, table only. Falsifier: bonds lose to cash over 12m from a bottom-decile print in an inflation regime. Offline (ST-7).

### SR-13 Tech (TMT) vs. defensives relative valuation (Topdown Charts / LSEG, 24 Sep 2026) — Thread E

**Register status.** ADOPTED — gate pending · **Built in.** ST-8

**Ruling.** Adopt as the valuation anchor for SR-1's style panel plus a base-rate table; reject the standalone rates-channel read. No T&B or composite rights.

**Home.** SR-1 style panel; Book A tilt; Book B pair note; Base Rates; Equities (concentration chapter).

**Mechanism.** The object is the spread, not either line: ≈+115% tech vs. a record ≈−38% defensives, ≈150 pp — widest since 2000–01, though 2000 peaked near 210 pp and sat above today's level for about two years first. Level is magnitude, not timing; timing comes from the relative-performance break SR-1 mechanizes. The tech leg is the concentration story already carried (Complacency overlay, Factor I, Equities) — adding it to T&B double-counts. The incremental piece is the defensives leg: a record discount is the unloved-asset condition, mirror of SR-12. Two construction checks: the basket is internally dispersed (utilities re-rated on the AI-power bid; healthcare's discount is partly policy-driven and does not revert on the cycle) — show staples / healthcare / utilities separately; and 1972 is the counterexample where defensives were the expensive one-decision leg. The rates mechanism is misassigned: mega-cap tech is cash-rich; the duration channel bites the unprofitable growth tier, and only when real yields drive the move (`rates.driver`). The 2003–10 path is the quiet falsifier: the premium fell from ≈160% to ≈20% largely through earnings catch-up with flat relative prices — spread reversion ≠ tech crash ≠ defensives rally.

**Data.** Kenneth French industry portfolios (annual sum-BE/sum-ME for relative P/B by industry from 1926; monthly returns for the forward test); Damodaran industry multiples (annual since ~1998) as cross-check; sector ETF trailing multiples via yfinance for the current print (sector ETFs are already fetched). *Lives in:* `calc.techdef_spread`, `calc.def_z` by sub-basket.

**Rights.** Base rate; Book A tilt modifier gated on SR-1's break; no new flag.

**Validation gate.** Episodes: top-decile spread (1929, 1968–72, 1983, 1999–2000, 2020–21, 2024–26). Statistic: forward 12/36/60m relative return of defensives vs. tech, (a) on spread alone, (b) on spread plus negative 12m tech relative momentum. Pass for the tilt modifier: defensives' 36m relative return positive in ≥4 of 5 completed episodes in cell (b). Falsifier: reversion via earnings with flat relative prices. Runs in SR-1's session (ST-8).

### SR-14 EM equities, absolute and relative to DM (Topdown Charts / LSEG; MSCI EM from 1987, 24 Sep 2026) — Thread X

**Register status.** ADOPTED — gate pending · **Built in.** ST-8

**Ruling.** Adopt as a Book A US-vs-rest-of-world allocation line with one mechanized trend flag; reject "decadal turning point" as a standing claim. No T&B or composite rights.

**Home.** Monthly Factor IV / dollar panel (US-vs-RoW block: EM/World and ACWX/SPY, USD and local); Book A tilt; Currencies; Equities; Base Rates. Flow-side confirmation from SR-26's `calc.us_foreign_net_12m`.

**Mechanism.** Two objects: the absolute line at all-time highs in USD and the relative line at a 25-year low with a one-year uptick — the 2010–24 relative bear was US outperformance, not EM decline. The relative cycle is the equity expression of the dollar cycle: every completed turn (1988, 1994, 2001, 2010) sat within about a year of a dollar turn; 2016–18 is the instructive false start. Operational version: stay tilted while the dollar-down regime holds, exit on the flip; the decadal framing is unfalsifiable at its own horizon. Composition contaminates the evidence: Taiwan, Korea and China tech are roughly 40% of MSCI EM, so the absolute breakout is substantially the AI-semis trade — decomposition needed (USD vs. local; EM ex-China alongside; semis share noted). Callum Thomas's "neutral" is recorded as a pattern, not a call: valuation and positioning signals fade early in regime trades; only the trend flag closes the tilt. SR-4's devaluation tell is the kill switch (2015 precedent).

**Data.** MSCI end-of-month levels, free (EM from Dec 1987, World from 1969; USD and local) — quarterly `manual_input`; daily proxies via yfinance (EEM/VWO, ACWX, EMXC from 2017); real broad dollar index (`fred.dxy` is the nominal broad index — add the real index, DTWEXBGS vs. RTWEXBGS, G-12). *Lives in:* `manual.msci_*`, `yfinance.mkt_eem` etc.; `calc.em_rel`, `calc.em_rel_flag`, `calc.em_fx_contrib`, `calc.emxc_rel`.

**Rights.** Narrow flag (relative trend break: 12m EM/World relative return > 0 and ratio above its 24m average); Book A tilt modifier conditioned on the dollar regime tag; SR-4 tell as exit.

**Validation gate.** Episodes: 1988, 2001, 2016 (false), 2024. Statistic: forward 36m EM/World relative return after the flag fires, split by real-dollar 12m change sign. Pass: the dollar cell discriminates (2016 in the dollar-up failure cell). If not, flag only. Falsifier for the current instance: the turn proceeds with a flat or strong dollar — then it is the AI trade and the tilt earns no credit. Offline (ST-8).
### SR-15 Cross-asset valuation z-scores — gold, S&P 500, Treasuries, commodities (Topdown Charts / LSEG, 1994–, 24 Sep 2026) — Thread A

**Register status.** ADOPTED — gate pending · **Built in.** ST-6, ST-7

**Ruling.** Adopt as a Monthly cross-asset valuation strip and a Book A rebalancing modifier; reject "cheap commodities" — the chart shows them at zero, average. No T&B change.

**Home.** Monthly Cheap-and-Unloved block (§2.4); Portfolio Construction (rebalancing rule; A-3 input); Metals (gold window fragility); Base Rates.

**Mechanism.** The value is the common scale: four assets on one z-axis lets Book A rank diversifiers instead of judging each alone, and SR-12's barbell needs exactly this to pick and size legs. Read correctly: gold rich (+1.7 after a +2.9 spike), stocks moderately rich (+1), Treasuries cheap (−0.8), commodities average — commodities are cheap only relative to gold and stocks, and the commodity/gold ratio at multi-decade lows is the cleaner object. Three cautions. Z-scores assume a stable anchor, and the four anchors differ in kind (cash flows, monetary reference, marginal cost). Gold is the problem child: a 1994-start window treats the official-sector bid as an anomaly when Factor V frames it as regime change — gold's z is reported with zero rebalancing weight while Factor V is active. The S&P at +1 vs. CAPE ~40 (nearer +2 on the same window) is model disagreement of the SR-6 kind — a confidence cross-check on the Valuation pillar, not a replacement. Magnitude for tilts, not timing: every asset has held above +1 for years at a stretch.

**Data.** Light house version, all free: CAPE plus ERP (Shiller, FRED); 10y real yield (`fred.tips_10y`, new) and ACM term premium; real gold vs. long trend (LBMA via Stooq/yfinance, CPI held); World Bank Pink Sheet commodity index vs. trend (monthly since 1960 — extends past 1994). Expanding-window z-scores only, through `derived_forms`. Full four-metric composites deferred (Appendix C). *Lives in:* `calc.val_z_gold/_spx/_ust/_cmdty`, `calc.cmdty_gold_ratio`.

**Rights.** Book A rebalancing modifier (tilt toward the lowest-z diversifier, sized by |z|, gated by `rates.driver`); confidence modifier on the Valuation pillar.

**Validation gate.** Cross-asset rank test — forward 3y real return of the cheapest-tercile asset vs. the richest, paired by date; per-asset forward 3y/5y real returns conditional on z > +1.5 and z < −1. Pass: cheap beats rich in ≥2/3 of paired observations. Window-fragility test on gold: if its conclusion flips between 1971-start and 1994-start windows, gold drops to base-rate rights only. Falsifier: an anchor-shift regime in which "expensive" persists for a decade. Offline (ST-7).

### SR-16 Hyperscaler debt supply and AI credit absorption (Bloomberg chart via Lemand, 24 Sep 2026) — Thread E (supply side of Thread R)

**Register status.** ADOPTED — gate pending · **Built in.** ST-4/ST-6

**Ruling.** Adopt as a Factor I funding panel with one narrow flag; reject the headline ("four companies borrowed more in nine months than fifteen years") as a signal. No T&B input yet.

**Home.** Disruptive Themes Factor I evidence log (human-gated); Monthly Duration Absorption block (supply side, §2.1.2); Credit; Equities (rings chapter); Debt Cycles brief (analog set).

**Mechanism.** The transition from self-funded to debt-funded capex is the classic late-stage marker of a capex boom (telecom 1998–2001, shale 2012–15, merchant power 2000–02). The post's real evidence is absorption, not issuance: new-issue concessions 2→12 bp, cover 3.2×→2.5×, 78 of 91 bonds wider than launch — the marginal buyer charging. Two objects the panel keeps apart: the hyperscaler unsecured leg, where solvency is not the question (≈1.8× leverage) and the signal is price (concession, spread, long-end appetite); and rings 2–3 (neocloud HY, GPU-backed ABS, SPV/private-credit and vendor financing), where the signal is default risk and where marginal financing has migrated. The mechanism variable is free and quarterly: aggregate self-funding ratio (operating cash flow ÷ capex) for AMZN, GOOGL, MSFT, META, ORCL, with net debt change — below 1 for two quarters is the regime line. The long-end supply share (42% of 15y+ issuance) is the bridge to SR-23. One daily tell falls out of the quality mix: hyperscalers are AA-class and a fifth of supply, so AA OAS widening relative to BBB (quality unchanged, supply changed) reads as supply pressure. A hike into this (SR-21) is the 1999–2000 sequence; this panel deteriorates first.

**Data.** yfinance quarterly cash-flow statements (free); ICE BofA AA and BBB OAS via FRED (new — IG/HY/BB/CCC are held, AA and BBB are not); SIFMA issuance by maturity (monthly); NIC/cover figures are Bloomberg-only — `manual_input` quarterly, three numbers. *Lives in:* `yfinance.fund_*`, `fred.aa_oas`, `fred.bbb_oas`, `sifma.*`; `calc.self_fund_ratio`, `calc.hs_netdebt_12m`, `calc.aa_bbb_oas_diff`, `calc.ai_long_share`.

**Rights.** Narrow flag: self-funding ratio < 1 for two quarters, or AA–BBB differential compressing past a gate-set threshold → Factor I refresh input (human-gated). Ring-3 HY spreads as a HY Spread Acceleration overlay candidate only after gate (§2.6).

**Validation gate.** Episodes: telecom, shale, merchant power. Statistic: lead time from (a) sector self-funding < 1 and (b) NIC/cover deterioration to the sector's equity relative peak and to its spread blowout. Pass: (a) or (b) led the equity peak by 6–24 months in ≥2 of 3. Falsifier: AI revenue catch-up returns the ratio above 1 by 2027.

### SR-17 Real-yield-led bond selloff, breakevens falling (Alpine Macro via Chen Zhao, 24 Sep 2026) — Thread R

**Register status.** MERGED into `rates.driver` · **Built in.** ST-3

**Ruling.** No new analysis — SR-6's block reading a live print. **Merged into `rates.driver`**: the DKW real-side decomposition (expected real short rate, real term premium, TIPS liquidity premium — Fed Board, monthly, free) is the fourth term-premium model and the sign arbiter when Kim–Wright and ACM disagree; the growth / Fed-path / term-premium distinction is the cell rule of §2.1.1.

**Mechanism (kept for the register).** "Real, not inflation" is half the attribution. Real yields rise for three reasons with opposite equity implications: growth (benign, correlation negative), Fed path (hawkish, correlation positive), real term premium (supply/fiscal — SR-23's channel, correlation positive). Breakevens falling while oil rises is anchored expectations — which makes 10y TIPS near 2.75% the SR-12 buy case if the term-premium cell drives, and a wait-for-the-pivot case if it is the Fed-path cell. Gold holding at these real yields is the Factor V scorecard metric (gold-vs-TIPS residual, already in Metals).

**Data.** Fed Board DKW output (monthly Excel). *Lives in:* `dkw.real_expected_path`, `dkw.real_term_premium`, `dkw.tips_liquidity`.

**Rights.** None new. **Validation.** Rides on SR-6's ledger; adds a four-episode calibration table (2013, Q4 2018, 2022, H2 2023) of forward 6m equity outcomes by cell — base rate only.

### SR-18 Global visible oil inventories vs. operational floor (JPM via Bloomberg; Brimberg 15 Sep, Monchau) — Thread C

**Register status.** ADOPTED — gate pending · **Built in.** ST-2, ST-6

**Ruling.** Adopt the mechanism (physical buffer state as a Factor III / Energy input); reject the chart as a current reading — §1.5 fixture.

**Home.** Monthly Factor III / Energy panel; Energy (buffer-market frame — this is the buffer variable); tail register (Hormuz).

**Mechanism.** The actual series on the chart ends around April 2026 (~8.0 bn bbl); the orange segment is JPM's June-published projection "assuming no resolution in June" with 5.6 mb/d of demand destruction. Tankers were transiting Hormuz by June 24 and WTI fell below $70, so "6.8 by September" is a counterfactual path, circulated on 15 Sep as "free fall." The mechanism is live again and the stack lacks it: price (`fred.wti`, `fred.brent` — held) conflates risk premium with physical tightness; inventory relative to the operational floor decides whether a second disruption spikes or shrugs. As of 25 Sep the strait is not fully open (Iran conditioning full reopening), product flows lag, and Brent $106.6 vs. WTI $94.5 — a $12 spread — is the tell: seaborne risk premium, not US physical tightness. The current level is required and is not on the chart.

**Data.** EIA weekly US stocks (free); IEA OMR OECD days-of-cover (monthly headline, `manual_input`); JODI non-OECD (free, 2-month lag); global-visible figure monthly `manual_input`; Brent–WTI from held series; prompt time-spreads via yfinance/CME (G-11). *Lives in:* `eia.crude_stocks`, `eia.product_stocks`, `manual.oecd_days_cover`, `manual.global_visible_stocks`; `calc.oil_buffer_state`, `calc.brent_wti`, `calc.oil_prompt_spread`.

**Rights.** Narrow flag (buffer above / at / below stress level) into Factor III; tail-register modifier for the Hormuz scenario.

**Validation gate.** Episodes: 1990, 2008, 2022. Statistic: forward 6m price change conditional on days-of-cover bottom decile × disruption event vs. none. Falsifier: demand destruction rebuilds stocks faster than the floor (2008 H2).

### SR-19 "3-month / 1-year beta" chart (Monchau, undated crop) — Thread E

**Register status.** DEFERRED — definition required · **Built in.** Appendix C

**Ruling.** DEFERRED — definition required (§1.6 fixture). The 0–45% scale and the "3-month daily / 1-year weekly" labels rule out a plain market beta; the spike pattern (1994, 1999–2001, 2018, 2020, 2024–26) is the signature of a one-factor market. Two readings, two homes: index beta/R² to the AI cohort or momentum → Concentration & Complacency overlay; index beta to yields → `rates.driver`'s correlation member, already covered. Timing lesson either way: the 1-year line peaked in 2001, after the top; a 63-day window is dominated by a handful of AI days — fragility state, not timing signal. House version in Appendix C. **Action:** register entry `DEFERRED — definition required`; request the full post text.

### SR-20 IMF COFER Q1 2026 and the reserve-composition tracker (FintechNews infographic; extension, 25 Sep 2026) — Thread X

**Register status.** ADOPTED — scorecard, no rights · **Built in.** ST-2; Tranche H

**Ruling.** Adopt as the Factor V scorecard of §1.9; reject the level as a signal in either direction.

**Home.** Disruptive Themes Factor V (scoreable input); Currencies; Duration Absorption block, absorber side (§2.1.2), through the shared `tic.*` family.

**Mechanism.** USD 57.1% (≈$7.5 tn of ≈$13.1 tn allocated) is near the post-1995 low (~71% in 2000, ~65% in 2015), but two things matter more than the level. The share is valuation-distorted — a weaker dollar mechanically lowers it; the ECB's constant-exchange-rate series shows slower, steadier erosion. And COFER excludes gold, which is where the shift is going: at market value official gold now rivals euro reserves, so the dollar's share of total reserves including gold is well below 57% and falling faster than the table shows — Factor V's official gold bid seen from the other side. Two narrative falsifiers sit in the table: CNY at 1.99%, down from ~2.8% in 2022, kills "RMB replacing the dollar" and supports SR-3/4 (funding currency, not reserve currency); growth is in CAD/AUD/other (~11% vs. ~2% in 2000) — diversification into liquid high-yielding sovereigns, a different story from de-dollarization. Base rate for expectations: sterling's displacement took roughly thirty years and two devaluations; the dollar's own share went from ~85% in the 1970s to the mid-40s by 1990 and back to 71% by 2000. Shares move ~1 pp/year on trend and by step at regime events; the tracker's job is regime classification once a year, not forecasting a number.

**Regimes and signposts.**

| Regime | Reads as | Signposts |
|---|---|---|
| Slow diversification (base) | Constant-FX USD share drifting down < 1 pp/yr; gains to CAD/AUD/KRW and gold | Nothing changes — that is the point |
| Sanctions-driven fragmentation | Gold share accelerating past ~25% of total reserves; CNY rising in *trade* settlement (SWIFT/CIPS, invoicing) while its *reserve* share stays flat (the SR-3/4 pattern) | A new large asset freeze; a major Gulf or Asian holder publicly shifting |
| Dollar re-consolidation | Official holdings falling while private foreign holdings and stablecoin T-bill float rise — the absorber changes, the currency doesn't | Stablecoin issuers as a new private absorber (already Factor V); crisis dollar demand |

**Data.** COFER quarterly (`manual_input`, ~3-month lag); WGC central-bank holdings and net purchases (monthly, new source); ECB constant-FX series (annual, `manual_input`); TIC official vs. private holdings (`tic.*`). *Lives in:* `manual.cofer_*`, `wgc.cb_gold_*`, `tic.official_holdings`, `tic.private_holdings`; `calc.cb_gold_12m`, `calc.tic_official_12m`, `calc.tic_private_12m`.

**Rights.** None. Scorecard; SR-23 absorber-side input.

**Disposition.** Annual by hand (three numbers plus the holder split, ≈30 min at each DT refresh); monthly proxies automated in ST-2/ST-4. G-13: whether Factor V already carries the gold-share line.

### SR-21 October 28 FOMC hike probability 70–77% (Bianco Research / Bloomberg WIRP, 24 Sep 2026) — Thread R

**Register status.** ADOPTED — gate pending · **Built in.** ST-4

**Ruling.** The probability itself is presumed already read in the Daily (G-4); adopt the derived object — the Fed–market gap — plus a Warsh-matrix scenario and a prediction-market disagreement case. Reject the political framing as mechanism.

**Home.** Daily 07:00 (FOMC weeks, ST-10); Sunday anchor; Rate machine; Warsh matrix (§2.1.5); the prediction-market spec's disagreement layer.

**Mechanism.** What is new is the configuration: a market pricing a hike against a Fed that has been easing, under a chair whose appointer wants cuts, a week before midterms. Three encodable consequences. (1) The gap between the market-implied path and the Fed's signalled path is a credibility variable with two branches: refuse, and the long end reprices through term premium (Bianco's "off the top of the page"; the `term_premium` cell; gauged by SR-24's flag); concede, and the curve bear-flattens then the `fed_path` cell resolves — 1994→1995, when hikes crushed bonds and the credibility they bought made 1995 the best bond year in a generation. Bianco prices only the first branch. (2) Sequencing with SR-16: a hike into debt-financed capex is the 1999–2000 sequence; SR-16's absorption metrics deteriorate first. (3) Kalshi's Fed-decision market vs. FedWatch on the same meeting is the cleanest test the disagreement layer will get. Base-rate note: "long yields rose during an easing cycle for the first time in 50+ years" was already true by January 2025; the useful base rate is what the long end did after the Fed conceded to market pricing (1994, 2022) vs. refused — into SR-7's table by hand.

**Data.** CME FedWatch (by hand until a free source is settled, G-4); fed funds futures via a free source; Kalshi Fed markets once PM-1 lands; SEP dots (`manual_input`, quarterly). *Lives in:* `manual.fedwatch_*`, `manual.sep_median_*`, later `kalshi.fed_*`; `calc.fed_mkt_gap_m1/_m2/_12m`, `CRED_STRESS`, `calc.pm_disagree_fed`.

**Rights.** Derived metric; narrow flag "policy-credibility stress" (≥60% of a move priced against the last signalled direction at the next meeting, or 12m gap > 50 bp); Warsh-matrix scenario ruling; PM disagreement record. No Book rights.

**Validation gate.** Episodes of ≥50 bp divergence within 3 months (1994, 1998, 2007, 2013, 2018, 2022, 2024). Statistic: forward 3m 10y change and equity return split by conceded / refused. Pass: the split separates the long-end outcome. First live test: 28 Oct 2026. Offline (ST-7).

### SR-22 5-year auction at 5.033%, TLT record low, "meltdown" (Padley, 24 Sep 2026) — Thread R

**Register status.** ADOPTED — gate pending · **Built in.** ST-1, ST-4, ST-7

**Ruling.** Adopt auction-absorption metrics — the one usable object in the post; reject the meltdown and cash-stance framing; add a Doctrine note that an ETF's record low is arithmetic.

**Home.** Daily 07:00 (auction days, ST-10); Monthly Duration Absorption block (price side); T&B Liquidity & Funding Stress overlay — **queue position #2** (§2.6); Book A rule A-3 (input); Operating Doctrine (note).

**Mechanism.** A 5-year at 5.03% with funds at 3.75–4.00% and a hike priced is the `fed_path` cell printed on a coupon — the same event as SR-17/21, not a new one. Ten basis points across global 10-years is a bad day, not a meltdown. TLT −50% from 2020 is what ~16 years of duration does when yields go from 1% to 5%; RSI 33 weekly is not oversold. The usable object hides behind "demand wasn't good": tail vs. when-issued, bid-to-cover, and dealer/direct/indirect takedown — free per auction, and the high-frequency symptom of SR-23's gap and SR-16's concessions. The base rate cuts against the post: the worst auctions of the last cycle (the 5 bp 30-year tail, Nov 2023) marked the top in yields, because a bad auction is the moment price-sensitive buyers finally get paid. The candidate flag is therefore a contrarian bottom-in-bonds tell, to be tested — and for Book A it is A-3's missing trigger.

**Data.** TreasuryDirect auction results API (free, per auction; `available_at` 13:00 ET auction day). Note: the registry's existing `ibkr.auction_*` keys are the equity closing auction; the new family is `auction.*` (Treasury). *Lives in:* `altdata/sources/treasury_auctions.py`; `auction.tail_bp`, `auction.bid_to_cover`, `auction.dealer_share`; `ABS_STRESS`.

**Rights.** Narrow flag "absorption stress" (tail ≥2 bp on two consecutive coupon auctions, or dealer takedown >20%) → overlay queue #2 after gate; A-3 input after gate.

**Validation gate.** ~1,000 coupon auctions 2009–2026; forward 1m and 3m 10y change conditional on top-decile tails. Pass for the contrarian read: median forward 3m change negative with ≥60% hit rate. Otherwise stress flag only. Offline (ST-7).

**Doctrine note (by hand).** Drawdown of a constant-duration fund is yield arithmetic; a "record low" in price is not a level that means anything. Candidate rule, not a rule.

### SR-23 G4 issuance gap vs. real yields (Lustig, corr 0.71, 24 Sep 2026) — Thread R

**Register status.** ADOPTED — gate pending · **Built in.** ST-4, ST-7

**Ruling.** Adopt — the highest-value item in either batch. It is the causal variable for the `term_premium` cell that the DKW split only measures, and it can be projected a year ahead.

**Home.** Monthly Duration Absorption block (supply side); Factor IV panel; Rate machine; Portfolio Construction (A-3's exit condition); Debt Cycles brief (supply regimes).

**Mechanism.** Net duration supply to price-sensitive private hands (issuance minus central-bank net purchases) is the preferred-habitat driver of the real term premium; G4 net supply at ≈7% of combined GDP is the highest since 2010 and the average 10y real yield has followed (−1.4% in 2020 to ≈+1.0% in 2025). Three cautions, one extension. The correlation is 16 annual points with both series trending on the QE regime — half of it is one dummy, so the test needs the pre-2008 sample and a funds-rate control (2019 is the tell: gap up, real yields down, because the Fed cut). It is projectable: CBO deficits plus announced QT paths give next year's bar before it prints — the only leading input in either batch. The extension is SR-16: AI-related IG long paper is additional supply competing for the same buyers. SR-20, SR-26 and SR-27 are the absorber-side symptoms; SR-22 the price-side symptom.

**Data.** US monthly house version, all free: Treasury net marketable issuance (Fiscal Data API, MSPD — field mapping G-14), Fed SOMA Treasury holdings (TREAST, new), nominal GDP (new); targets `fred.tips_10y` and ACM; CBO baseline as `manual_input`; SIFMA for IG issuance by maturity. G4 version annually by hand from Lustig's substack, cited. *Lives in:* `fiscaldata.mspd_*`, `fred.soma_treasuries`, `fred.gdp_nominal`, `manual.cbo_deficit_path`; `calc.net_supply_12m_gdp`, `calc.net_supply_proj_12m`, `calc.priv_residual_12m`.

**Note — G-14, the MSPD field mapping (decided in ST-1, 26 Sep 2026).** `fiscaldata.mspd_net_marketable_issuance` is the month-on-month change in MSPD Table I "Total Marketable", debt held by the public (`debt_held_public_mil_amt`, stored in dollars), consecutive month-ends only. It counts the Fed as public, so it *includes* SOMA auction add-ons, and it is at par or accreted principal, so it includes TIPS inflation accrual. It is therefore **not** the refunding's "privately-held net marketable borrowing", which "excludes rollovers (auction 'add-ons') of Treasury securities held in the SOMA but includes financing required due to SOMA redemptions" (Treasury press release sb0584, 3 Aug 2026). Checked for April–June 2026: MSPD +$239.6bn against the refunding's +$190bn. Subtracting the change in `fred.soma_treasuries` (about +$104bn) gives about $136bn, which does not reproduce $190bn either, because TREAST also moves with the Fed's secondary-market purchases, and the refunding counts those as privately held. For this entry's variable ("issuance minus central-bank net purchases"), ST-4's `calc.net_supply_*` should be this series minus the change in `fred.soma_treasuries`, and should not be compared with the refunding's privately-held figure as a like-for-like measure. The class levels (`fiscaldata.mspd_bills/_notes/_bonds/_tips/_frn`) are stored too; excluding TIPS accrual needs TIPS auction amounts, not the `_tips` level change. Full reasoning: `altdata/sources/fiscaldata.py` docstring.

**Rights.** Confidence modifier on the `rates.driver` cell assignment; Factor IV panel input; Book A duration-timing modifier via the projection, with refunding announcements as Daily events (`events.scheduled` already exists in the registry).

**Validation gate.** 2003–2026 monthly; regress the 12m change in ACM term premium (and `fred.tips_10y`) on the 12m change in net supply/GDP with a funds-rate-path control. Pass: positive, significant coefficient in both pre- and post-2008 subsamples. If only post-2008 → descriptive, no modifier. Falsifier: 2010–13 consistent; 2018–19 inconsistent without the Fed control. Offline (ST-7).

### SR-24 5y5y forward breakeven vs. MSCI World Commodity Producers (Costa / Azuria Capital, chart as of 12 Sep 2026) — Thread R

**Register status.** ADOPTED — definition only, no gate possible · **Built in.** ST-4

**Ruling.** Adopt a defined inflation-expectations de-anchoring flag as a rider on `rates.driver` and SR-21; reject the hand-drawn trendline breakout as a rule (the SR-1 lesson: three touches on a chosen axis) and the commodity-producers index as an expectations lead.

**Home.** Rate machine (breakeven anchoring); Factor IV; Warsh matrix (consequence gauge for the SR-21 "refuse" branch); Debt Cycles brief (fiscal-dominance lens, already carried); Energy and Metals (producers-vs-spot note).

**Mechanism.** The observation underneath is real and the stack has no defined version of it: 5y5y forward breakevens have made lower highs for twenty years (≈3.0% 2005, ≈2.9% 2011, ≈2.65% 2022). That sequence is Fed credibility as the market prices it, and a break above the 2022 high would be the first de-anchoring event of the TIPS era. The chart is dated 12 Sep with 5y5y at 2.31% "on the verge"; SR-17's chart shows the sequel — it failed at the line and fell toward 2.25% by 23 Sep while oil surged. The right wiring: the de-anchoring flag is what the "refuse" branch costs, and it feeds the inflation-risk-premium component of the `term_premium` cell. The producers index at an all-time high (8,114, above the 2008 and 2011 peaks) is a different object: substantially gold miners plus energy on a USD net-return basis, re-rating on scarcity and capex discipline, not a forecast of breakevens. The producers-vs-spot ratio at a high is a capital-cycle note (the market paying for discipline; 2011 shows what follows) — base rate for Energy and Metals. Costa's "policymakers pushed toward more inflation" is the fiscal-dominance thesis the Debt Cycles brief treats as one lens among several; his conclusion is his book (§1.3). Honest limit: there is no completed de-anchoring episode in market data since 2003, so the flag cannot be gated — its meaning comes from 1965–80 via the Livingston survey, and it carries definition-only rights.

**Flag definition.** `DEANCHOR` = `fred.breakeven_5y5y` above its 2022 high (≈2.65%, verify at build) for 20 consecutive sessions, confirmed by either the Fed Board's Common Inflation Expectations index above its 2022 high or UMich 5–10y expectations ≥3.5% for three consecutive months. Rendered with `calc.be5y5y_range_pos`.

**Data.** `fred.breakeven_5y5y` (held); Fed Board CIE (quarterly, new source); UMich 5–10y (monthly, new); NY Fed SCE 3y/5y (monthly, new); Livingston history (by hand, base rate); GUNR as the producers proxy (G-15). *Lives in:* `fedboard.cie`, `umich.expect_5_10y`, `nyfed.sce_*`; `DEANCHOR`, `calc.be5y5y_range_pos`, `calc.producers_spot_ratio`.

**Rights.** Narrow flag, definition only; Warsh-matrix consequence gauge. **Validation.** None possible on market data; Livingston 1965–80 base-rate note by hand.

### SR-25 Burry adding to AI shorts — Micron, Nebius, SOXX, Palantir (Monchau via Bull Theory, 24 Sep 2026) — Thread E

**Register status.** REJECTED as signal — memory-cycle tell adopted · **Built in.** ST-4 (+MU)

**Ruling.** Reject as a signal; adopt one memory-cycle tell from the evidence cited; record as a narrative-register entry graded "notable participant, low weight."

**Home.** Factor I evidence log (memory line); Equities (semiconductor fulcrum chapter, base-rate table); narrative register. No Daily or T&B surface.

**Mechanism.** Famous-investor positioning is low-information by construction: disclosures are lagged and partial, "in some size" is unquantified, and the public bearish calls since 2019 have marked local bottoms as often as tops; the cloning literature finds value in concentrated long-only managers at a 45-day lag, not in macro shorts. The information is in the evidence, not the position: the Acer CEO's comment that memory inventories are building while Chinese suppliers (CXMT, YMTC) add supply is the classic memory-downcycle trigger, and memory is the most cyclical part of the semiconductor fulcrum the Equities paper already treats as the AI trade's pivot — memory prices led SOX peaks by 0–2 quarters in 2000, 2008, 2018 and 2022. The nuance that decides whether the Micron short is right: the memory market is bifurcated — HBM (AI, supply-constrained, three producers) vs. commodity DRAM/NAND (consumer, where Chinese entry lands). Testable from filings: Micron inventory days and HBM revenue share, plus DRAM contract-price direction. The long list (QXO, Build-A-Bear, Sprouts, Birkenstock, MercadoLibre) is his book; no rights.

**Data.** MU quarterly balance sheet via yfinance (inventory ÷ COGS × 91 → inventory days; MU added to SR-16's fundamentals pull); HBM share (`manual_input`, quarterly); DRAM contract-price direction (`manual_input`, monthly). *Lives in:* `calc.mu_inv_days`, `manual.mu_hbm_share`, `manual.dram_dir`.

**Rights.** None. Base-rate table (memory downcycles 1996, 2001, 2008, 2011, 2018–19, 2022–23 → SOX peak lead) in Equities; quarterly line in the Factor I evidence log. Register entry records the rejection (R25).

### SR-26 TIC cross-border flows, 12 months through July 2026 — "foreign demand for U.S. debt collapsed 80%" (Riemann, 24 Sep 2026) — Threads X and R

**Register status.** ADOPTED — gate pending · **Built in.** ST-2, ST-4

**Ruling.** Adopt the composition read as the absorber-side detail of §2.1.2; reject the headline. Read whole, the same table shows net foreign acquisition of US long-term securities *rising* in the window (1,182.6 → 1,276.9 bn, +8%). What fell is the Treasury share of it.

**Home.** Monthly Duration Absorption block; Factor IV (external-financing composition); Currencies; Rate machine.

**Mechanism.** Private foreign net purchases of Treasury bonds and notes fell 506 → 263; official net selling slowed (−50 → −17); bills 251 → 49. But private foreign purchases of US equities rose 606 → 802, corporate bonds 305 → 392, agencies 127 → 142, and official accounts turned net buyers overall (−76 → +155) through equities (+140) and corporates (+60). Foreigners funded the US as much as before — through the equity market (largely the AI trade) and credit instead of Treasuries. Treasury share of net foreign long-term purchases: 39% → 19%. US residents meanwhile bought more foreign securities (−286 → −478): SR-14's US-vs-RoW turn in flow form. Three implications. (1) Treasury supply is landing on domestic price-sensitive buyers — SR-23's residual, now measurable from the same source. (2) The external financing mix has shifted from debt (sticky, price-insensitive) to equity (pro-cyclical): a US equity bear removes the marginal foreign funding just as Treasury supply peaks — the mechanism that links SR-13/SR-16 (the AI trade) to the `term_premium` cell and to the dollar. (3) Foreign bill demand fell as Treasury shifted issuance toward bills that MMFs and stablecoins absorb domestically (Factor V) — bills are not the constraint. TIC monthly flows are not seasonally adjusted, noisy, custodially biased and benchmark-revised; a single-row percentage change is not evidence (R26).

**Data.** TIC monthly cross-border flows table (free, ~6-week lag), first-print and revised vintages (G-8). *Lives in:* `tic.flow_*`; `calc.foreign_ust_share_lt`, `calc.foreign_eq_12m`, `calc.foreign_bill_12m`, `calc.us_foreign_net_12m`.

**Rights.** Absorber-fragility modifier on the block's read (after gate, jointly with SR-27); Factor IV panel input. No Book rights.

**Validation gate.** Episodes when the Treasury share of net foreign long-term purchases stayed below 25% for 12 months (check 2013–14, 2018–19, 2020–21); forward 12m change in ACM term premium and in the real broad dollar index. Small n; if no separation, descriptive line only.

### SR-27 TIC Major Foreign Holders — "who sold and who bought," 12-month change by reported holder, June 2025 to June 2026 (research note, Figure 3) — Threads X and R

**Register status.** ADOPTED — gate pending · **Built in.** ST-2, ST-4

**Ruling.** Adopt as the holder-level absorber panel (§2.1.2; layer 1 of §1.9); reject "China dumping Treasuries" as a signal without the custodial adjustment.

**Home.** Monthly Duration Absorption block; Factor V scorecard (holder split); Currencies; T&B Liquidity & Funding Stress overlay — **queue position #3** with SR-26 (§2.6).

**Mechanism.** The buyers are custodial and fund-management centres (UK +84, Belgium +52, Ireland +43, Luxembourg +31, Cayman +12) — private and often levered holders (basis-trade funds via Cayman, European asset managers via Ireland and Luxembourg) — plus Gulf and Asian financial centres (Singapore +31, UAE +18, Hong Kong +14, Saudi Arabia +12). The sellers are official reserve holders, for three different reasons the panel tags separately: reserve diversification (China −98 — though Euroclear in Belgium has historically custodied Chinese holdings, so the true China change is smaller than −98 and part of Belgium's +52 may be China); FX defense (India −41, Brazil −47 — reserves sold to defend the rupee and the real; SR-3's external-position mechanism, not de-dollarization); hedged-carry economics (Japan −38, Switzerland −16 — SR-2's `calc.jp_hedged_carry` turning negative stops Japanese hedged Treasury buying). Net: custodial/private ≈+220, official ≈−245 — roughly flat in total, but the marginal holder has changed from a central bank that holds to maturity to a levered fund that hedges and can unwind. That is the fragility the Liquidity & Funding Stress overlay is built to catch — March 2020 and April 2025 were basis-trade unwinds — and it is measurable.

**Data.** TIC Major Foreign Holders table (monthly, free; annual benchmark as a second vintage, G-8); TIC's official/private split. *Lives in:* `tic.holdings_by_country`, `tic.official_holdings`, `tic.private_holdings`; `calc.tic_official_share`, `calc.tic_custodial_share`, by-hand mechanism tags; `ABS_FRAGILITY` (candidate rule: Treasury share falling ∧ custodial share rising ∧ official share falling, 12m).

**Rights.** Absorber-fragility modifier with SR-26 (after gate); overlay queue #3 after gate; Factor V holder line (none).

**Validation gate.** Custodial share and official share versus the severity of Treasury liquidity events (Oct 2014 flash rally, Sep 2019 repo, Mar 2020, Apr 2025), severity measured by MOVE and dealer balance-sheet metrics. n = 4; base rate only unless the ordering is monotonic.

---

## Explicit rejections (do not re-propose)

Copied from §12 of the order.

- R1 — The 1980–2000 Growth/Value trendline as a rule.
- R2 — "Widest-ever" US–China 10y spread as a mean-reversion signal.
- R3 — "Domestic debt is a false narrative" as a conclusion from shadow reserves.
- R4 — Consumer-credit top decile as a standalone top signal.
- R5 — Single-model term-premium attribution treated as fact.
- R6 — Unconditional "stocks rise in hiking cycles" base rate.
- R7 — 5.25% as a causal level for stock-bond correlation.
- R8 — Any composite or trigger rights for SR-1…9 before the stated gate passes.
- R9 — PRL as a composite, overlay, trigger or factor input; auto-promotion of any mechanism-watch candidate; `PRL` as a key anywhere; PRL or Pearl content in the Daily Cascade outside the 12:30 information line; a thesis status treated as a market state.
- R10 — Carried from the 19 Sep batch Part C (consensus drift) unchanged.
- R11 — "Bonds are a classic contrarian play" from allocation alone, unconditional on regime.
- R12 — The rates channel as the mechanism for mega-cap tech's premium.
- R13 — "Decadal turning point" for EM as a standing claim.
- R14 — "Cheap commodities" from a zero z-score.
- R15 — Hyperscaler issuance level as a signal; absorption is the signal.
- R16 — Any projection segment read as a print (SR-18).
- R17 — Any chart entered without its definition (SR-19).
- R18 — COFER USD share level as a signal in either direction.
- R19 — Pre-midterm political framing as a mechanism for Fed behaviour.
- R20 — An ETF's record low, or a 10 bp global yield day, as a "meltdown" signal; the cash-stance conclusion.
- R21 — The 0.71 annual correlation as evidence without the pre-2008 subsample and funds-rate control.
- R22 — Any composite or trigger rights for SR-12…27 before the stated gate passes; A-3 before both its gates.
- R23 — A hand-drawn trendline on 5y5y breakevens as a breakout rule.
- R24 — The commodity-producers equity index as a lead on inflation expectations.
- R25 — Famous-investor positioning or "doubling down" disclosures as a signal in either direction.
- R26 — A single-row TIC flow change read as a collapse in foreign demand for US assets.
- R27 — "China dumping Treasuries" from the Major Foreign Holders table without the custodial adjustment and the benchmark vintage.
- **R28 (new, from the integration) — Any second regime, cell or tag computed outside the market-state object**, including the two-state tag of the 19 Sep SR-6 ruling and the four-cell table of the 25 Sep batch as standalone constructs.
