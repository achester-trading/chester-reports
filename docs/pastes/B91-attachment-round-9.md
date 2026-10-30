# Change order — signal triage, round 9 (items 98–109; Batch 18, provisional)

| | |
|---|---|
| **File** | `docs/change-order-signal-triage-batch-18-2026-10-29.md` |
| **Status** | RULED 27–29 Oct 2026 (all twelve items, in chat); filing pending |
| **Encoding** | Batch 18 of Post-Freeze Amendment #4 (provisional; Batch 16 = items 79–91, Batch 17 = items 92–97). SR numbers assigned at the audit that places this batch. |
| **Precedence** | Below Part 26, the Enterprise Layer order and the dated change-orders edition; equal to the other Amendment #4 batches. Amendments govern their parent items from filing. |
| **Totals** | ≈ 27 h of sessions · ≈ 2 h one-off by hand · recurring ≈ 0.25 h/quarter (105) |
| **Note** | A Binance "$6.28bn exploit" post was triaged on 29 Oct as a proposed rumour-track and **dropped by ruling**; it holds no number. Item 107 is the money-market-fund entry. |

Every item is REPORT_OK-class: no path to DECISION_BLOCKED, no composite or T&B weight change, no new regime tag (regime-like reads stay R28 sub-states). The paper engine (99) and the Alpha Lab hypotheses (100b) stay paper-only; no live orders before 2027. Nothing prints without a stored source.

---

## 1. Rulings at a glance

| Item | Short name | Ruled | Kind | Sessions | By hand |
|---|---|---|---|---|---|
| 98 | Kakushadze & Serur family registry (Alpha Lab) | Accept 27 Oct | AMEND lab rules; library | — | 1.5 h |
| 99 | Premium sleeve — XSP/SPX put-spread paper engine | Adopt paper engine 27 Oct | ADOPT (Alpha Lab, paper) | 4 h | — |
| 100 | Liquidity levels line + `liquidity-sweep` hypothesis | Accept 27 Oct | AMEND 45 (a); lab hypothesis (b) | 3 h | — |
| 101 | Kill-switch board | Accept 28 Oct | ADOPT (a–c) | 4.5 h | — |
| 102 | "Gold/silver could go negative" headline (a precious-metals fund manager, Crescat) | Accept 28 Oct | LOG; narrative + voices | — | 0.25 h |
| 103 | Global AI-complex panel (China AI crash) | Accept 28 Oct | ADOPT | 3 h | — |
| 104 | EM shock-screen audit (Brazil) + EM local bonds | Accept 28 Oct | AUDIT (a); AMEND em_scorecard (b) | 1.5 h | — |
| 105 | "Who owns BTC" (and gold) ownership line | Accept 28 Oct | AMEND Digital Assets chapter; 88(b) | 1.5 h | 0.25 h/qtr |
| 106 | Intraday dealer read + 0DTE volume proxy | Accept 29 Oct | ADOPT (a); test (b); no vendor (c) | 5 h | — |
| 107 | Money market funds (% GDP, flows, prime vs govt) | Accept 29 Oct | AMEND SR-12 / item 30 | 2 h | — |
| 108 | Hyperscaler earnings-reaction ledger | Yes, accept 29 Oct | AMEND 54 | 1.5 h | — |
| 109 | Real rate vs trend growth and r* | Yes, accept 29 Oct | AMEND 29 | 1 h | — |

---

## 2. Entries

### 98 · Kakushadze & Serur family registry — Alpha Lab
**Source.** an X aggregator account (X, 26 Oct) — *aggregator/engagement*; card summarising Kakushadze & Serur, *151 Trading Strategies* (2018; free on SSRN 3247865).
**Thought process.** A catalogue, not a signal. Its value is as a canonical family taxonomy: the lab's deflated Sharpe and RAS (91b) count variants per family, and families today are ad hoc labels.
**Decision.** (a) Each hypothesis carries a `family_ref` keyed to K&S section numbers (e.g. `KS §3.1 momentum`); the family budget and dSR/RAS variant counts key on it; H-001 onward mapped once; `docs/alpha-lab-rules.md` amended. (b) Add two named leakage cases to the lab's leakage list: HP-filter look-ahead; unfinished-candle. (c) K&S as a second reference in XVIII beside ML4T. By hand, 1.5 h. Post: LOG; the "$100K bot" claim discarded.

### 99 · Premium sleeve — paper engine
**Source.** Options-selling "system" post (X, 27 Oct; "DM SYSTEM") — *educator/promoter*.
**Thought process.** CSPs are covered calls in disguise (long stock, capped upside, negative skew); the post's rules conflict (70%+ IV on "boring" names); single-name concentration; funding LEAPs with put premium is mental accounting that doubles long exposure. A rules-based index premium sleeve, gated by regime, is a legitimate engine to test.
**Decision.** Paper engine: XSP or SPX put spreads (cash-settled, §1256, defined tail); 30–45 DTE; short strike ≈ 16–20 delta; take profit at 50%; close/roll at 21 DTE. Entry gates: VRP > 0 · IV rank top third · net GEX positive or spot above flip. Stand down: HY Spread Acceleration or Liquidity overlay ACTIVE, or Capitulation Count *surrender* without a T&B BOTTOM SIGNAL. Benchmark: Cboe PUT index. Pre-registered in the Alpha Lab (family `KS options`); own sleeve cap under the Doctrine; promotion only through RAS (91b) and cost cliff (91c). OTM/LEAP buying stays a separate Book D sleeve with its own sizing, never funded by premium. 4 h. Post: LOG.

### 100 · Liquidity levels and the sweep hypothesis
**Source.** an X educator account's "Institutional Price Action & Liquidity" cheat sheet (91 patterns) — *educator/engagement*.
**Thought process.** Most patterns are hindsight-fitted and a multiple-testing problem. The objective core — reference levels where resting orders cluster, and sweep-and-reclaim of them — is real and codeable.
**Decisions.** (a) AMEND 45: a liquidity-levels line at 07:00 in ES terms — PDH/PDL, PWH/PWL, Globex high/low, Asia and London ranges, equal highs/lows within 0.1%, nearest unfilled gap; any level within 0.25% of a gamma wall or the flip marked *confluence*. Report rights. 2 h (less if the opening setup already carries part). (b) Pre-register family `liquidity-sweep` (new K&S registry entry): ES sweep of PDH/PDL, Globex or session extremes with a close back inside within N bars; outcomes at +30/+60/+120 min and session close; with and without dealer confluence; small fixed grid declared at registration. 1 h. Rest of the sheet: LOG.

### 101 · Kill-switch board
**Source.** an X on-chain analyst account, "The regime that kills each strategy" (lives in / dies in / early warning) — the operator liked the format.
**Decisions.** (a) A standing one-page board, one row per engine/book — trend engine, momentum/leadership, mean reversion, dealer-level fades, liquidity-sweep, premium sleeve (99), carry, basis, Book A allocation, gold (88), Book D OTM/LEAPs — each with *lives in*, *dies in*, and an early-warning threshold on a stored series (e.g. variance ratio, net GEX vs flip, VIX/VIX3M, VRP, SR-36 tiers, SR-9 5.25%, stock-bond correlation, 87's real-yield beta). Green/amber/red with date of last change. Prints every Sunday in the Weekly and at the front of the Master Guide. Thresholds pre-registered; a ledger records whether red preceded each engine's drawdowns. Report rights. 4 h. (b) Red lights feed the Enterprise Layer drift trigger (91d) as *pause candidates* only; the pause stays the operator's call at the Doctrine sitting. 0.5 h. (c) The dark, four-column, one-screen style becomes house style for cheat sheets (Master Guide, Capitulation Count, kill-switch board).

### 102 · "Gold and silver could go negative in 2027" (a precious-metals fund manager, Crescat; LinkedIn, 28 Oct)
**Thought process.** The underlying article appears fabricated ("Horizon Capital Research" untraceable); the claim is mechanically unsound (WTI's 2020 negative print was a physical-delivery storage squeeze on one contract). Metals Focus (19 Oct) reads the opposite. The fund manager's point is sentiment: an absurd bear headline is a capitulation marker — but he runs long precious-metals strategies.
**Decision.** LOG. Narrative register: *media capitulation (source likely fabricated)*, noted beside 88(a)'s exhaustion checklist, not scored. Voices: Crescat, *fund manager, long precious metals (conflicted)*. 0.25 h by hand.

### 103 · Global AI-complex panel
**Source.** an X aggregator account via a LinkedIn relay (28 Oct) — *aggregator*.
**Thought process.** Verified: STAR50 down ~40% in under four months, worst index globally; CSI 300 > 20% off its 22 Jun close. The US analogy is weak (STAR50 ~250x vs S&P ~19x forward; retail-driven; "49%" depends on the AI definition — JPM GTM buckets 53.2%). Anthropic S-1 filed; press reports H1 2026 net loss $80.7bn and a filing valuation ≈ $965bn (the post's $2tn was earlier secondary pricing) — closes Batch 16 V4 against the filing (Customer B). **Disclosure: Claude, which drafted this order, is built by Anthropic.** New: China is the first AI market to crack, and Korea/Taiwan carry the hardware leg; nothing aligns them with SOX/NDX.
**Decision.** Weekly tape panel: STAR50, CSI 300, KOSPI, TAIEX, SOX, NDX — drawdown from peak and 20-day correlation to SOX; lead-lag ledger testing whether Asian AI drawdowns lead SOX. FINRA margin debt (level, YoY) added if not stored. Report rights. 3 h.

### 104 · EM shock screen and local bonds
**Source.** an EM-debt chief economist (LinkedIn, 27 Oct) — *EM debt, credible*.
**Read.** GBI-EM Brazil YTD total return fell from ~+25% to ~+7% in October; GBI-EM China (1.7% yield) now ahead (+8%). Brazil local-asset stress on fiscal headwinds confirmed (MNI, Trading Economics).
**Decisions.** (a) AUDIT — did the EM shock screen (Batch 5 item 10, built after a Brazil miss) fire in October on BRL, the DI curve or Brazil local bonds? If not, amend thresholds. 0.5 h. **Priority.** (b) AMEND `em_scorecard`: local-currency EM bond total returns (EMLC aggregate; Brazil and China proxies); China's outperformance at 1.7% feeds SR-3/SR-4. 1 h.

### 105 · Who owns the asset classes
**Source.** River Financial (LinkedIn) — *promoter (bitcoin broker)*, sound sources (Z.1, TIC, WGC, bitcointreasuries.net).
**Decision.** Digital Assets chapter: quarterly "who owns BTC" line — ETFs, public companies, governments, exchanges as % of supply (bitcointreasuries.net). Matching gold line (official-sector share, WGC) in 88(b). Report rights. 1.5 h + 0.25 h/quarter. Ties to SR-29, Farside flows, MSTR/MSCI.

### 106 · Intraday dealer read
**Origin.** The operator's question (29 Oct) prompted by a QuantData "Interval Map" ad.
**Thought process.** OI updates once daily; intraday "GEX" on OI is yesterday's book repriced at spot, which the open's gamma profile already gives. Our chain is 15-min delayed. The genuinely new intraday information is 0DTE volume.
**Decisions.** (a) ADOPT: at 09:15, 10:30, the 12:30 alert and 15:00, print spot against the open's profile — distance to flip and nearest wall in ES points, whether negative gamma has been entered since the open, implied hedging flow per 1% from here; a flip crossing fires the 12:30 alert off-schedule. No new data. 2 h. (b) TEST: volume-weighted 0DTE gamma estimate from Massive's delayed chain at 10:30, 12:30 and 15:00 — where 0DTE activity concentrates, whether a new pin is forming; report rights; pre-registered ledger on whether pins/closes land near the estimated peak. 3 h + session compute. (c) No new subscription; QuantData not bought. Run 106(b)'s ledger beside the December vendor month (SpotGamma + FlashAlpha upgrade) and decide in January.

### 107 · Money market funds
**Source.** an independent educator, CFA, ex-JPM (LinkedIn, 29 Oct) — *educator, credible*.
**Read.** US MMF assets near 26% of GDP — near the GFC peak, above dot-com and COVID peaks.
**Thought process.** The level lags shocks and is largely yield- and structure-driven (rates ~4%, deposit migration, post-2008 reforms); "cash on the sidelines" is not a bull argument either. The information is in flow speed, prime-vs-government rotation (the 2008 and 2020 stress tell), and MMF allocation across ON-RRP, bills and repo.
**Decision.** AMEND SR-12 / item 30: MMF assets % GDP (Z.1, quarterly) with dual percentiles · ICI weekly flow z-score · prime-vs-government flow split as a narrow stress flag. Prints in plumbing & rates, noted beside the Liquidity overlay; never an overlay trigger without a ledger. Report rights. 2 h.

### 108 · Hyperscaler earnings-reaction ledger
**Source.** an X promoter account (X, 29 Oct) — *promoter/engagement* ("buy the dip").
**Read.** Google −12%+ on earnings (~$500bn, worst day since 2004); Amazon −12%+ after hours (~$315bn) — despite Google Cloud +103% and AWS +39% (fastest in ~5 years); revenue misses of 0.5% and 0.2%. Figures unverified.
**Thought process.** The signal is the reaction: accelerating cloud growth sold hard is "good news sold" — the market pricing capex and FCF, not revenue; Gartner's revenue-gap case (83) in prices.
**Decision.** AMEND 54: one row per print for MSFT, GOOGL, AMZN, META, ORCL (+ NVDA) — day-1 move, revenue and cloud surprise, capex-guide change, FCF change; "good news sold" flag when cloud beats and the stock falls > 5%. Weekly in earnings season; feeds Factor I. Report and base-rate rights. 1.5 h. Post: LOG.

### 109 · Real rate vs trend growth and r*
**Source.** LinkedIn post, "Pause and Effect" (a LinkedIn author (unattributed); author not captured) — *credible, neutral*.
**Read.** 10y estimated real rate ≈ 2.5% (Cleveland Fed) ≈ trend growth (gap ≈ 0), ≈ 1.4 pp above NY Fed HLW r*. Either the effect is still to come (locked-in mortgages, balance sheets, fiscal support) or neutral has risen (deficits; AI/energy/defence capex); pressure falls on borrowers whose growth lags financing costs, and on federal financing.
**Decision.** AMEND item 29 (r − g): add Cleveland Fed 10y real rate (FRED `REAINTRATREARAT10Y`) and NY Fed HLW r* and trend growth (quarterly download); print both gaps as a two-line chart in the Monthly's plumbing & rates. Base-rate rights. 1 h. Voices: author pending.

---

## 3. Cross-item notes

1. **Alpha Lab housekeeping lands together:** 98 (family registry, leakage cases), 99 (premium sleeve under `KS options`), 100(b) (`liquidity-sweep`) — register 99 and 100(b) only after 98's registry exists.
2. **The kill-switch board (101) reads series built elsewhere** — 82 tape character, 89 crowding and trend breadth, 97 Capitulation Count, 87 real-yield beta, SR-36, SR-9 — so it builds last in its tranche, and its premium-sleeve row depends on 99.
3. **Intraday dealer work (106) and the liquidity levels (100a) share the 07:00/intraday ES block** — build together; confluence marks need both.
4. **AI complex:** 103 (global panel), 108 (earnings reactions), 96 (growth contribution) and 83 (revenue gap) are one Factor I cluster for the next Disruptive Themes refresh.
5. **Rates:** 109 extends 29 and sits beside 94 (ex-post real rate) and SR-17 — one plumbing & rates exhibit family.

## 4. Work order

| Tranche | When | Work | Sessions | By hand |
|---|---|---|---|---|
| **Now** | Next ruling sitting | 104(a) EM screen audit | 0.5 h | — |
| **B** | After 8 Nov; Audit #5 places | 106(a)(b) + 100(a) intraday/levels · 103 AI panel · 108 earnings ledger · 107 MMF · 109 r* · 104(b) · 105 | 15.5 h | 0.25 h/qtr |
| **C** | With the Alpha Lab / Enterprise Layer queue | 98 registry (first) → 99 premium sleeve · 100(b) sweep hypothesis · 101 kill-switch board (last) | 11 h | 1.5 h |
| **By hand** | — | 98 · 102 | — | 1.75 h |

## 5. Verify items

| # | Item | What | Closes on |
|---|---|---|---|
| V1 | 108 | Google −12%+, Amazon −12%+ AH; Cloud +103%, AWS +39%; revenue misses | Box close 29–30 Oct; company releases |
| V2 | 103 | Anthropic S-1: H1 loss, filing valuation, Customer B | EDGAR (also closes Batch 16 V4) |
| V3 | 104(a) | Whether the EM shock screen fired in October | Box ledger |
| V4 | 109 | Author of the post | The operator supplies, else unattributed |
| V5 | 102 | "Horizon Capital Research" article | Treated as fabricated unless a source surfaces |
| V6 | 106(c) | QuantData not adopted | Revisit in January with the vendor-month verdict |

## 6. Registers

**Signal-triage register.** New entries (provisional SR numbers at the audit): 99 premium sleeve · 101 kill-switch board · 103 global AI-complex panel · 106 intraday dealer read. Amendments: 45 (100a) · 54 (108) · 29 (109) · SR-12 / item 30 (107) · `em_scorecard` (104b) · Digital Assets chapter and 88(b) (105) · `docs/alpha-lab-rules.md` (98). Alpha Lab registrations: `KS options` (99), `liquidity-sweep` (100b).

**Narrative register.** "Gold/silver negative" headline as media capitulation (102).

**Voices.**

| Voice | Outlet | Tag | Status |
|---|---|---|---|
| a precious-metals fund manager | Crescat | fund manager, long precious metals (conflicted) | new |
| an EM-debt chief economist | EM debt fund | EM debt, credible | new |
| an educator, CFA | independent / ex-JPM | educator, credible | new |
| River Financial | River Financial | promoter (bitcoin broker) | new |
| "Pause and Effect" author | LinkedIn | credible, neutral | pending V4 |
| X accounts (an aggregator, an options-selling educator, a price-action educator, an on-chain analyst, a promoter) and a LinkedIn relay | X / LinkedIn | promoter / aggregator / engagement | log only; the X-only accounts go to the X pilot's seed list chat-side |

**Disclosure.** Claude, which drafted this order, is built by Anthropic; relevant to 103 and V2.

## 7. Sign-off

| Date / time | Items | Ruling as stated |
|---|---|---|
| 27 Oct 2026, 03:32 GMT | 98 | "Accept" |
| 27 Oct 2026, 03:37 GMT | 99 | "Adopt paper engine" |
| 27 Oct 2026, 04:26 GMT | 100 | "Accept" |
| 28 Oct 2026, 14:32 GMT | 101 | "Accept" |
| 28 Oct 2026, 14:36 GMT | 102–105 | "Accept" |
| 29 Oct 2026, 22:18 ET | 106; Binance rumour-track | "Accept 106, ignore 107" (the dropped proposal held that number) |
| 29 Oct 2026, 22:20 ET | 107 (MMF) | "Accept" |
| 29 Oct 2026, 22:31 ET | 108, 109 | "Yes, accept" |
| 29 Oct 2026, 22:31 ET | Round 9 called | "summarize all of the change order since the last summarization" |

Open at filing: SR and batch numbers (audit); V1–V6.
