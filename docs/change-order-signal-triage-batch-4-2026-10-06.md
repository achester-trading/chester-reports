# Change Order — Signal Triage Batch 4

| | |
|---|---|
| **File** | `docs/change-order-signal-triage-batch-4-2026-10-06.md` |
| **Revision** | r1 — 2026-10-06 |
| **Status** | DRAFT — per-item rulings proposed in chat 2026-10-06; §8 decisions pending; not yet in the repo |
| **Filed** | Filed as DRAFT 6 Oct 2026. §8 decisions 1–10 are taken at Audit #4 (14–15 Oct), which also assigns its numbers and places its tranches; nothing from it enters the October calendar until then. |
| **Proposed encoding** | Batch 5 of Post-Freeze Amendment #4. This is the fourth signal-triage batch; the crypto data-sources order of 2026-10-06 took Batch 4. Amendment and batch numbers confirmed at Audit #4. |
| **Precedence** | Below architecture Part 26 and the dated change-orders file; coequal with the batch-2, batch-3 and crypto data-sources orders; above session-level work. Where this order touches an entry another order owns (SR-36, the OAT–Bund flag, the batch-2 oil-inventories and hyperscaler-issuance entries) it amends by reference and does not restate. |
| **Register** | SR-37 … SR-49, provisional. Next free after batch 3 is SR-37; the crypto order's five Thread-D candidates are unnumbered until Audit #4, which reconciles both. Two items are logged as *seen, no entry*. |
| **Work IDs** | ST4-01 … ST4-16, batch-local; renumbered into the ST-n sequence at filing. |
| **Intake** | Running chat, 2026-10-06, 06:36–11:21 ET. Fifteen third-party items plus two commissioned in chat (items 10 and 11). Sources in Appendix A. |

---

## 1. Purpose and scope

This order consolidates the fourth signal-triage batch: fifteen third-party charts and posts triaged in a running chat on 6 October 2026, plus two items commissioned in the same chat after a check of what the daily, weekly and monthly reporting would have caught from a random social-media news recap (an EM shock screen, item 10; a private AI-financing ledger, item 11).

Each item was assessed for incremental insight against the framework as it stands after batches 1–3, the JPM GTM order, the reporting-stack brief and the crypto data-sources order. Rulings carry only the rights Amendment #4 allows — narrow flag, modifier, base rate, report-only — and nothing here changes a scenario, a theme score or a book rule without a calibration ledger first.

Thirteen register entries result. Two items are duplicates of existing entries and are logged as seen. Four cross-item consolidations (§4) reduce what would have been eighteen separate series into three lenses and one sub-state axis.

## 2. Batch read (dated 2026-10-06)

Five of the first eight items are one circuit, and the later items hang off it.

Hyperscaler capex is semiconductor revenue — the BofA series shows forward FCF for the five hyperscalers at roughly −$25bn against roughly $420bn for the four semis, the two lines having crossed in 2025. That semiconductor revenue is most of the +~28% forward-EPS growth that is holding the S&P 500 up while its forward multiple de-rates ~14% (index +~10% YTD). The capex is now debt-financed at 5%+ — public issuance where the batch-2 entry sees it, and increasingly in private, lease-backed packages where nothing in the stack sees it — against a ~5% cash alternative. Yields are held up by sticky inflation (core PCE rising, diesel at ~$6.50 running ahead of CPI, a long-run inflation anchor above the 10y), and the bond market has historically been let off only by an equity shakeout. Treasury volatility has moved (MOVE ~110) while liquidity has not yet followed.

The fulcrum is hyperscaler capex guidance. Cut it and semiconductor EPS, then index EPS, slips; the equity "resilience" ends and yields get their relief. Hold it and hyperscaler FCF goes deeper negative, issuance rises, and the credit-absorption test comes. Both legs are tested in the same week: the late-October hyperscaler prints and the 28 October FOMC.

On the bond side the morning's voices disagree cleanly. Diebel reads a 1994-type correlated repricing that is nearly done; Courtial's twin-deficit fit says ~50bp of fiscal premium is still unpaid (5.8% fitted against 5.3% paid); Visseau says the market is priced for a 5.0–5.5% chop while the mechanics flirt with a spiral; Sarmaya says the Fed blinks. Four answers to one question. The 10y anchors lens (§4.1) and the selloff-shape axis (§4.2) are the two builds that would adjudicate that rather than narrate it.

Copper sits apart from the circuit but is a positioning tell on the same theme: large speculators at a 23-year high as a share of open interest on the AI/power-demand narrative.

## 3. Governance inherited

- **Rights.** Narrow flag, modifier, base rate, report-only, per Amendment #4. No automatic scenario, theme or book change.
- **One regime (R28).** Anything regime-like is a `rates.driver` sub-state on the market-state object, never a separate tag. This order adds a second axis to that sub-state (§4.2) and one flag (SR-41); it adds no new object.
- **T&B overlays** enter through the one-at-a-time intake queue. Nothing here wires to T&B directly. SR-39, SR-42 (base-rate leg), SR-45 and SR-40 enter the queue only after their calibration ledgers (Tranche B).
- **Track D preconditions** unchanged: D1c before any new writer; Daily and T&B wiring only after D4/D6 and "T&B full".
- **Validation** = offline calibration studies with dated ledgers.
- **Phase B.** No stored source, not printed. Every voice in this order is added to the voices register (Appendix A) before any of its lines print.
- **Dated content** stays in dated blocks: the batch read above, Appendix B's narrative lines and Appendix C's base-rate rows all carry their as-of dates.

## 4. Cross-item rulings

### 4.1 The 10y anchors lens (SR-43; items 6 and 13)

Two of the batch's items and one existing series are the same kind of thing — a fair-value anchor for the 10-year — and are consolidated into one lens in the 6e metric-lenses build, rates family:

1. **Inflation anchor** — 10y minus trailing-10-year average CPI YoY. This is a transparent stand-in for the Topdown Charts "10-Year Inflation Rate Model", whose specification is not published; the lens prints the stand-in and labels it so.
2. **Fiscal anchor** — the twin-balance cross-section (budget balance plus current account, % of GDP, IMF WEO) against 10y yields across 14 developed markets, refit at each WEO (April, October). The US reading is the fitted yield minus the market yield. Courtial's 5 October 2026 fit gives 5.8% fitted against 5.3% paid (~69% of cross-sectional variance explained; China excluded; Netherlands, Switzerland and Japan off the line).
3. **Term premium** — the existing ACM series, unchanged.

One printed line: 10y against each anchor, gap in basis points, sign. Right: modifier on the Factor IV note and the plumbing & rates commentary only. Caveat carried in the lens text: a 14-point cross-sectional fit is fragile and is refit, never extrapolated.

### 4.2 `rates.driver` gets a shape axis (SR-49; item 15)

The driver axis (inflation-led / real-yield-led / term-premium-led, batch 1 and batch 2) is joined by a **shape axis**: *correlated* (every DM yield rising together — 1994-type reaction-function repricing), *divergent* (the focal sovereign rising while core falls — 2011-type fiscal crisis), or *mixed*. Measured as the rolling 13-week correlation and cross-sectional dispersion of weekly 10y changes across G7+ (OECD long-term rates on FRED, monthly, with daily yfinance fills where available).

The **reflexive state** (SR-41) is a flag on the object, not a third axis. Two axes and one flag; no further sub-states are added by this order.

### 4.3 One breadth input (SR-45; items 9 and 14)

Constituent drawdown breadth at record highs (Inovestor's measure) and the equal-weight/cap-weight ratio (RSP/SPY) are two measures of one thing and become one Concentration & Complacency overlay input, with one calibration ledger. The equal-weight seven-week losing streak itself (n = 2 priors: 2002, 2022) carries no signal right and is logged as seen.

### 4.4 Intake-template rule (new)

A single-date statistic carries no signal right until it carries its percentile among comparable dates. Gauvin's treatment of the "59% of the S&P 500 in a bear market" chart — the same measure as a share of *record* months since 1993, 95th percentile — is the model. Added to the signal-intake template as a required field for any item whose claim is a level.

### 4.5 Factor I evidence (SR-37, SR-47)

SR-37 is the capex-financing leg's panel; SR-47 is the ledger for what public issuance data misses. Together they are the financing leg of Factor I. The revenue leg's evidence log gets, by hand, the first dated entry from the recap check: Microsoft and Meta reducing internal frontier-lab spend in favour of in-house tooling (The Information, early October 2026, via secondary coverage).

## 5. Item rulings

Fields: **Source · Claim · In the framework already · Ruling · Right · Placement · Data · Cost.**

### SR-37 — AI FCF transfer panel (item 1)

- **Source** Ryan Lemand post, 5 Oct 2026, on BofA Investment Research chart via a16z Growth (as of 30 Aug 2026). Hyperscalers = AMZN, GOOGL, META, MSFT, ORCL; semis = NVDA, MU, AVGO, AMAT.
- **Claim** Hyperscaler 12-month-forward FCF peaked near $275bn in 2024 and is now ~−$25bn; semis' went from ~$50bn to ~$420bn; the lines crossed in 2025 and move inversely because capex on one side is revenue on the other.
- **In the framework** Factor I (AI capex vs revenue divergence) has the thesis; the batch-2 hyperscaler-issuance entry and the batch-3 FT tech-vs-HG spread have the credit consequence; the Equities paper has the semiconductor fulcrum. None carries the two aggregate FCF series.
- **Ruling** Adopt as a Factor I panel: aggregate FCF for the five and the four, the ratio, and a defined threshold state *hyperscaler aggregate FCF < 0*.
- **Right** Modifier on the Factor I score; report-only. No T&B queue entry.
- **Placement** Mechanics (Monthly); Disruptive Themes Factor I (bimonthly).
- **Data** Forward consensus is not free. Build trailing-twelve-month FCF from quarterly cash-flow statements (yfinance, nine tickers), labelled *trailing*; switch to forward only if a free source appears (§8 decision 2).
- **Cost** ~4h (ST4-01).

### SR-38 — Return-attribution lens and forward-EPS revision line (item 2)

- **Source** Joe Little (HSBC AM) post, 6 Oct 2026, on a Bloomberg chart: S&P 500 ~+10% YTD, blended forward EPS ~+28%, blended forward P/E ~−14%.
- **Claim** Equity resilience is earnings, not multiple; the risk is "what happens if profits slip", with a ~5% cash alternative now competing.
- **In the framework** The GTM valuation quad (incl. EY-minus-Baa) carries levels; nothing decomposes the index return into earnings and multiple, and nothing tracks forward-EPS revisions.
- **Ruling** Adopt a return-attribution lens in *what's priced*: 12-month price return split into forward-EPS growth and multiple change, plus a forward-EPS revision line (4-week and 13-week change in the forward estimate). Add EY-minus-3-month-bill beside EY-minus-Baa.
- **Right** Report-only; the revision line is a narrow flag candidate after one quarter of history.
- **Placement** What's priced (Monthly); revision line weekly in mechanics.
- **Data** S&P Dow Jones Indices' free EPS-estimates spreadsheet (operating EPS by quarter, actual and estimate); 3-month bill from FRED.
- **Cost** ~4h (ST4-02).

### SR-39 — Equity shakeouts cap rising yields (item 3)

- **Source** Alpine Macro chart (S&P 500 drawdown vs 10y, ~2018–2026) via LinkedIn, 5 Oct 2026.
- **Claim** Bond rallies have usually required an equity shakeout or financial crisis to start (1995, 1998, 2001, 2008 and the post-2018 episodes marked).
- **In the framework** The Rate and Liquidity Machine's scenarios and the Duration Absorption block (batch 2) assume the relationship; it has never been measured.
- **Ruling** Offline calibration study: at every 10y local peak since 1990 (26-week high followed by ≥50bp decline within 26 weeks), was there an S&P 500 drawdown ≥5% / ≥10% within ±8 weeks; and the inverse, what the 10y did around every ≥10% equity drawdown. Dated ledger.
- **Right** Base rate. If the conditional holds, a Duration Absorption rule follows (*no duration add before the shakeout*) as a separate Book A/B ruling.
- **Placement** Base-rate table; the book (rule, if earned).
- **Data** FRED DGS10; S&P 500 via yfinance (long history).
- **Cost** ~3h (ST4-03), Tranche B.

### SR-40 — MOVE leads Treasury liquidity (item 4a)

- **Source** Maxence Visseau (Arkevium) post, 5 Oct 2026; chart MOVE vs an Arkevium/Bloomberg Treasury liquidity index, 2016–2026.
- **Claim** Liquidity follows volatility with a lag (2022: vol first, liquidity second, impaired for two years). MOVE ~110, liquidity gauge ~1.6, "well below where it settles when MOVE trades above 100".
- **In the framework** MOVE is in the Volatility paper and the cross-asset vol set; the Liquidity & Funding Stress overlay carries funding inputs (SOFR–IORB, SRF usage, repo). The lead-lag is not encoded.
- **Ruling** Encode the sequence in the Liquidity & Funding Stress overlay: MOVE as the leading leg, the existing funding-stress inputs as the lagging confirmation, and an *early* state when MOVE's 20-day change is top-decile on a 20-year window while no lagging input has moved. Escalates to *confirmed* when any lagging input crosses its own threshold.
- **Right** Narrow flag; overlay input after calibration ledger (Tranche B); report-only until then.
- **Placement** Plumbing & rates (daily close and Weekly).
- **Data** MOVE via yfinance (^MOVE). The Bloomberg liquidity index is not free; **no proxy adopted** — open item (§9), §8 decision 9.
- **Cost** ~3h (ST4-04).

### SR-41 — Reflexive state and buyback efficacy (item 4b)

- **Source** Same Visseau post: three paths (reflexive spiral — oil > $100, breakevens > 2.6%, MOVE > 130, 10y toward 5.75–6.0%+; controlled repricing — 5.0–5.5% chop; growth shock — pivot, duration bought at 5.25% "the trade of the cycle"); Treasury's enhanced buyback programme as intervention in all but name, first two operations having failed to arrest the move; intervention bounces treated as tactical events.
- **In the framework** The batch-2 breakeven de-anchoring flag, the batch-3 10y speed flag, SR-36's unwind-watch and the batch-3 Treasury-buybacks note each carry one piece. Nothing combines them.
- **Ruling** (a) A **reflexive** flag on the `rates.driver` object from four inputs — WTI > $100, 10y breakeven > 2.6%, MOVE > 130, SR-36 unwind-watch on — set when ≥3 of 4 hold (§8 decision 3 on whether to keep his levels or set own percentiles). (b) A **buyback efficacy line**: for each Treasury buyback operation (results published by Treasury), the 10y change over the following five sessions; two consecutive failures (10y higher after both) print as a tell. (c) By hand: *intervention-induced bounce = Book C tactical event, not a Book B entry* into the Book rule table.
- **Right** Narrow flag (a); report-only (b); book rule (c) by hand.
- **Placement** Plumbing & rates; the book.
- **Data** All inputs exist except the buyback results scrape (Treasury's operation-results page).
- **Cost** ~2h composite + ~2h buyback line (ST4-05, ST4-06); ~0.25h by hand.

### SR-42 — Copper positioning extreme (item 5)

- **Source** Elliott Wave International chart, 2 Oct 2026 (COT data via insidercapital.com): large speculators as a share of total non-spreading open interest at a 23-year high; Market Vane bullish consensus at a 9-year high; a rising-wedge annotation.
- **Claim** Copper optimism and positioning are at multi-decade extremes.
- **In the framework** The Metals paper covers copper; the CFTC fetcher SR-36 brings in (Treasury futures) is the same source. No copper positioning series. The wedge is ignored under the Technical Indicators ruling.
- **Ruling** Extend the CFTC fetcher to COMEX HG: non-commercial net as a share of non-spreading OI, own-history percentile (20-year), tiers at the 90th and 97th percentiles. Market Vane is paid and is not adopted.
- **Right** Base rate only — copper's 3/6/12-month forward return after top-decile crowding — with a dated ledger; no flag until the ledger has ≥10 qualifying episodes.
- **Placement** Positioning & flows (Weekly); Alt Asset block of the Monthly.
- **Data** CFTC legacy COT, weekly, free; copper price via yfinance (HG=F).
- **Cost** ~2h (ST4-07); depends on the SR-36 fetcher existing.

### SR-43 — The 10y anchors lens (items 6 and 13)

Ruled in §4.1. Sources: Topdown Charts post (~30 Sep 2026, chart "US Treasury Yields vs Long-Term Inflation Rate", 1957–2026); Jeremy Courtial post, 6 Oct 2026, on an idea from Société Générale Cross Asset Research (IMF WEO 2026 balances, Bloomberg yields 5 Oct 2026).

- **Right** Modifier on the Factor IV note and plumbing & rates commentary.
- **Placement** Plumbing & rates; what's priced; Factor IV (bimonthly).
- **Data** FRED CPIAUCSL (inflation anchor); IMF WEO database (general government balance, current account, % GDP, free CSV); OECD long-term government bond yields on FRED (IRLTLT01 series, monthly); ACM term premium (existing).
- **Cost** ~1h inflation anchor + ~3h twin-deficit fit and OECD-yields fetcher (ST4-08, ST4-09; the fetcher is shared with SR-49). §8 decision 4 on interim handling.

### SR-44 — Rolling-decade bond return base-rate row (item 7)

- **Source** Till Christian Budelmann post, 6 Oct 2026, on Bianco Research / Edward F. McQuarrie (Santa Clara) chart: rolling 10-year annualised nominal return on US long bonds since 1793, Sep 2026 = −2.23%, the record low (prior low Dec 1959, −0.08%).
- **Claim** Worst decade on record for long Treasuries, before inflation.
- **In the framework** Base Rates and the Rate and Liquidity Machine already carry starting-yield-predicts-forward-return. No rolling-return row.
- **Ruling** By hand: one base-rate row (rolling-10y return percentile → subsequent 10-year return, McQuarrie data) plus the arithmetic note that the current window spans the 2020–21 near-zero starting yields and will keep deteriorating until roughly 2031 whatever bonds do now; starting yield is the signal, this is not.
- **Right** Base rate, by hand.
- **Placement** Base-rate table; a Book A note.
- **Cost** ~0.5h by hand (ST4-10).

### Seen, no entry — core PCE and the 10y rising together (item 8)

Tony Ferreira post, 5 Oct 2026 (core PCE index vs 10y, FRED). The read — inflation and yields rising together, bonds not hedging — is the batch-1 yield-move attribution entry and the batch-1 stock-bond correlation flag. Registered as seen. His 4.7% 10y is a data-vintage artefact against the 5.3% in the other posts, not a disagreement.

### SR-45 — Breadth at record highs (items 9 and 14)

- **Source** Karl Gauvin post, ~30 Sep 2026, on Inovestor CPMS point-in-time S&P 500 data (month-end, Dec 1993–Aug 2026): 49% of members ≥20% below their high at Aug 2026 month-end (59% on late-September daily data per Dow Jones Market Data); average month since 1993 47%, median record month 35%, Aug 2026 at the 95th percentile of record months; 2000 ran 52–62% with the index at records. Charles-Henry Monchau post, 4 Oct 2026, on Bull Theory charts: S&P 500 equal-weight seven consecutive weekly red closes, priors 2022 (7) and 2002 (10).
- **Claim** The cap-weighted index is at records on a narrow base.
- **In the framework** Concentration & Complacency overlay, the GTM concentration twin, SR-19 negative-beta share. No constituent-drawdown breadth, no equal-weight ratio.
- **Ruling** One overlay input, two measures: (a) share of current constituents ≥20% below their own high, monthly, conditioned on the index within 1% of a record, with the percentile among record months; (b) RSP/SPY ratio, 21-week change and 5-year percentile, daily. Calibration ledger before queue entry. The streak statistic is logged as seen (§4.3).
- **Right** Overlay input after ledger; report-only until then.
- **Placement** Tape (RSP/SPY, daily); mechanics (breadth, Weekly and Monthly).
- **Data** yfinance for current constituents and RSP/SPY. **Caveat printed with the series:** the free build uses today's constituents and survivorship bias reads it lower than Inovestor's point-in-time series; Gauvin's chart is the reference reading (§8 decision 5).
- **Cost** ~4h breadth + ~0.5h RSP/SPY (ST4-11).

### SR-46 — EM shock screen (item 10; commissioned in chat, approved 2026-10-06)

- **Origin** The recap check: a Brazil first-round result moving Brazilian assets would have been caught only by chance. The operator wants emerging-market shocks caught as a category.
- **In the framework** EM is covered thematically (China devaluation tell SR-4, yen carry stack, Factor IV dollar, batch-2 EM absolute/relative valuation). No cross-sectional shock catch. PM-1, once live, catches election surprises as ≥10pp venue moves by design.
- **Ruling** Four parts. (a) **Move screen**, daily: a fixed basket of ~10 EM currencies (FRED daily: BRL, MXN, ZAR, INR, KRW, TWD, THB, CNY; TRY and IDR via yfinance) and the matching country ETFs (EWZ, EWW, EZA, INDA, EWY, EWT, THD, FXI, TUR, EIDO); flag any member whose 1-day or 5-day move exceeds 2.5σ on its own 5-year history; two-sided. (b) **Idiosyncratic vs systemic**: basket dispersion against co-movement — one member alone is an event for the narrative register; the basket together is dollar/risk-off and already Factor IV's business. (c) **EM spread family**: ICE BofA EM corporate OAS and EM high-yield OAS (FRED), percentiles through the metric lenses, and an EM leg on the HY Spread Acceleration overlay. (d) **Contagion rule**: a single-country shock earns a Weekly or Monthly line only if it passes to the basket or to EM spreads within five sessions (the 1995 peso / 1998 Russia sequence). The EM calendar — elections, runoffs, IMF reviews, major EM central-bank meetings — goes into *ahead* by hand, with PM probabilities attached where a market exists.
- **Right** Narrow flag (a, c); modifier on Factor IV narrative (b); escalation rule (d).
- **Placement** Tape (a); what doesn't fit (b); plumbing & rates (c); ahead (calendar).
- **Cost** ~6h sessions (ST4-12: 3h screen, 1h dispersion, 1h spreads, 1h rule) + ~1h by hand (calendar seed).

### SR-47 — Private AI-financing ledger (item 11; commissioned in chat, **unruled**)

- **Origin** The recap check: a $60bn lease-backed TPU financing package (Bank of America, Citi, Morgan Stanley syndicating; $42bn senior secured backed by Broadcom, $18bn junior with Blackstone ~$9bn; up to $42bn of convertibles to Broadcom) and a ~$30bn+ OpenAI round at a ~$1.4tn pre-money never appear in public bond-issuance data until refinanced into IG.
- **In the framework** The batch-2 hyperscaler-issuance entry and the batch-3 FT tech-vs-HG spread see only the public leg. The private, structured leg is where AI financing has moved.
- **Ruling (proposed)** A by-hand register, `docs/registers/ai-financing-ledger.md`: date, borrower, lender/arranger, amount, structure, guarantor, tranches, who holds the junior, what it funds, source URL. Feeds Factor I (§4.5) and the credit-absorption block as a sourced table with a running total. Entries one and two are the two above.
- **Right** Report-only; a Factor I modifier only after four quarters of entries.
- **Placement** Mechanics (Monthly); Factor I (bimonthly).
- **Cost** ~1h by hand to seed, then per entry (ST4-13). §8 decision 6.

### SR-48 — Diesel leads CPI (item 12)

- **Source** Sarmaya Partners post, 6 Oct 2026 ("Return to Tangibles" paper), chart US national average diesel vs CPI YoY, 2006–2026, as of 22 Sep 2026: diesel ~$6.50, CPI YoY ~3.5%.
- **Claim** Diesel works into prices across the economy and CPI catches up; the two insulated engines (65+ household spending, data-centre construction) mean tightening lands on housing, small business and younger households; with the debt this large, fiscal pressure makes the Fed more likely to blink.
- **In the framework** The Energy paper's buffer-market frame; the GTM K-shape panel (insulated engines); the Warsh matrix's fiscal-dominance branch (Fed blinks). Diesel itself is not in the energy family.
- **Ruling** Add US No. 2 diesel retail price (FRED GASDESW, weekly) to the energy family with a YoY lens and a lagged read against headline CPI YoY (lead/lag correlation at 0–6 months, printed once per Monthly). "Fed blinks" to the narrative register with Sarmaya as a voice.
- **Right** Report-only; pipeline-inflation tell in the inflation pillar commentary.
- **Placement** Mechanics (inflation pillar, Monthly); narratives.
- **Cost** ~1h (ST4-14).

### SR-49 — Selloff shape axis: correlated vs divergent (item 15)

Ruled in §4.2. Source: Charles Diebel post, 6 Oct 2026 — 1994 (reaction-function surprise; Bunds +~190bp Feb–Oct 1994, then −~400bp over the following years; all yields correlated) against 2011 (fiscal-driven, divergent; Bunds fell while Italian and Greek yields spiked; Greece the focal point); now France, with 10y OAT at 4.839% above BTPs (4.545%) and Bunds at 3.436% (6 Oct 2026); his read is mostly 1994-type and nearing sufficient repricing, with deflationary risk by mid-2027 if energy reverses; his 2011 tell is OATs spiking while others fall.

- **Right** Sub-state axis (report-only; feeds the plumbing & rates read).
- **Placement** Plumbing & rates (Weekly, Monthly); what doesn't fit (his forward view, Appendix B).
- **By hand** (a) Amend the batch-3 OAT–Bund flag: *OAT above BTP* as a focal-point marker, printed beside the 150bp / ~190bp tiers. (b) The 1994 numbers into the base-rate table (Appendix C).
- **Data** OECD long-term yields on FRED (shared fetcher with SR-43); daily fills via yfinance where available.
- **Cost** ~3h (ST4-15); ~0.5h by hand (ST4-16).

## 6. Placement by stack section

Prose above; the table is the cheat-sheet.

| Section | Entries |
|---|---|
| The read | Batch read (§2) as dated narrative; nothing automatic |
| Tape | SR-45(b) RSP/SPY daily; SR-46(a) EM move screen daily |
| Mechanics | SR-37 FCF panel; SR-38 revision line (weekly) and attribution (monthly); SR-45(a) breadth; SR-47 ledger table; SR-48 diesel |
| What doesn't fit | The four-voice 10y disagreement; Visseau "priced for #2, mechanics flirting with #1"; SR-46(b) idiosyncratic EM events |
| Plumbing & rates | SR-40 lead-lag state; SR-41 reflexive flag and buyback line; SR-43 anchors; SR-46(c) EM spreads; SR-49 shape axis; OAT>BTP marker |
| Positioning & flows | SR-42 copper COT (beside SR-36) |
| What's priced | SR-38 EY-minus-bill; SR-43 gaps |
| Narratives | Appendix A voices; Appendix B lines |
| Ahead | Late-October hyperscaler prints and the 28 Oct FOMC as the batch's test dates; Treasury buyback operation dates; EM calendar |
| The book | Book C rule (intervention bounce); Duration Absorption rule pending SR-39; Book A note from SR-44 |
| Slow layers (monthly) | Factor I (SR-37, SR-47, revenue-leg log); Factor IV note (SR-43) |

## 7. Work order

Work IDs are batch-local (ST4-nn) and are renumbered into the ST-n sequence at filing.

### Tranche A — build now (standalone series and lenses; report-only)

| ID | Entry | Hours | Depends on |
|---|---|---|---|
| ST4-14 | SR-48 diesel series + lens | 1.0 | — |
| ST4-08 | SR-43 inflation anchor | 1.0 | 6e lens framework |
| ST4-09 | SR-43 twin-deficit fit + OECD-yields fetcher | 3.0 | IMF WEO CSV; shared with ST4-15 |
| ST4-15 | SR-49 shape axis | 3.0 | ST4-09 fetcher; `rates.driver` object |
| ST4-01 | SR-37 FCF transfer panel (TTM) | 4.0 | — |
| ST4-02 | SR-38 attribution lens + revision line + EY-minus-bill | 4.0 | — |
| ST4-12 | SR-46 EM shock screen (a–d) | 6.0 | — |
| ST4-07 | SR-42 copper COT extension | 2.0 | SR-36 CFTC fetcher |
| ST4-05 | SR-41 reflexive flag | 2.0 | SR-36 tiers; breakeven flag; MOVE series |
| ST4-06 | SR-41 buyback efficacy line | 2.0 | Treasury results scrape |
| ST4-04 | SR-40 lead-lag early state (MOVE leg only) | 3.0 | Liquidity & Funding Stress overlay inputs |
| ST4-11 | SR-45 breadth + RSP/SPY series | 4.5 | — |
| | **Tranche A** | **35.5** | |

### Tranche B — calibrate before any panel, flag or queue entry

| ID | Study | Hours | Gate |
|---|---|---|---|
| ST4-03 | SR-39 yield-peak / equity-shakeout conditional, 1990– | 3.0 | Dated ledger; rule only if the conditional holds at both drawdown thresholds |
| — | SR-42 copper crowding forward-return ledger | in ST4-07 | ≥10 qualifying episodes before any flag |
| — | SR-45 breadth ledger against subsequent 6/12-month returns | in ST4-11 | Ledger before T&B overlay-queue entry |
| — | SR-40 early-state ledger (did lagging inputs follow within 60 sessions) | in ST4-04 | Ledger before queue entry |
| | **Tranche B** | **3.0** | |

### Tranche C — by hand

| ID | Item | Hours |
|---|---|---|
| ST4-10 | SR-44 base-rate row + arithmetic note | 0.5 |
| ST4-13 | SR-47 ledger seed (two entries) — if adopted | 1.0 |
| ST4-16 | OAT>BTP marker on the batch-3 flag; 1994 base-rate row | 0.5 |
| — | Book rule: intervention bounce = Book C | 0.25 |
| — | Intake-template rule (§4.4) | 0.25 |
| — | EM calendar seed (SR-46) | 1.0 |
| — | Factor I revenue-leg log, first entry (§4.5) | 0.25 |
| — | Voices register entries (Appendix A); narrative lines (Appendix B) | 1.0 |
| | **Tranche C** | **~4.75** |

### Not adopted / deferred

- Market Vane consensus (paid) — not adopted.
- Equal-weight weekly-streak statistic as a signal — not adopted (n = 2).
- Rising-wedge and other pattern annotations — not adopted (Technical Indicators ruling).
- Treasury liquidity proxy for SR-40's lagging leg — open; deferred unless §8 decision 9 commissions it.
- Recap housekeeping (SPR series and streak lens; OCC most-active options volume by symbol) — §8 decision 7.

**Totals:** ~38.5h of sessions (A + B) + ~4.75h by hand. Default placement: after batch-3 Tranche A and the crypto order's Tranche A; Audit #4 confirms (§8 decision 8).

## 8. Decisions for the operator

Taken in chat one at a time; the recorded rulings constitute the signature.

1. **Encoding.** Batch 5 of Amendment #4 (proposed) or a standalone Amendment #6.
2. **SR-37 data.** Build trailing FCF from filings now and label it (proposed), or wait for a forward-consensus source.
3. **SR-41 thresholds.** Keep Visseau's levels as the composite's inputs (oil $100 / breakeven 2.6% / MOVE 130) plus SR-36 unwind-watch, ≥3 of 4 (proposed), or set own levels from 20-year percentiles.
4. **SR-43 interim.** Until the WEO/OECD fetcher is built, carry Courtial's 5.8%-vs-5.3% as a sourced figure in the Monthly (proposed) or print nothing until own fit exists.
5. **SR-45 build.** Accept the survivorship-biased free build, labelled, with Gauvin's chart as the reference reading (proposed), or read Inovestor's chart by hand monthly and build nothing.
6. **SR-47.** Adopt the private AI-financing ledger as a by-hand register (proposed) or drop.
7. **Recap housekeeping.** Adopt both, either or neither of: SPR series check plus a draw-streak lens in the energy family (~0.5h); OCC daily options volume by symbol into positioning & flows (~1.5h).
8. **Placement.** Default (after batch-3 Tranche A and crypto Tranche A), or pull ST4-01 and ST4-02 (~8h) ahead of the late-October test dates, since those two adjudicate the batch read.
9. **SR-40 lagging leg.** Leave the Treasury liquidity proxy open (proposed) or commission a proxy study now (~3h: on/off-the-run spread, swap spreads, futures basis as candidates).
10. **The rest.** All remaining per-item rulings as proposed in §5.

## 9. Open at filing

- Amendment and batch number (Audit #4).
- Register numbers SR-37…SR-49 against the crypto order's Thread-D candidates (Audit #4).
- ST4-nn → ST-n renumbering (filing).
- Treasury liquidity proxy (SR-40).
- Topdown's model specification — the stand-in is labelled until it is known.
- Visseau's "two scenarios" line resolved: it refers to his paths 2 and 1 (full post captured 2026-10-06).
- Whether the Alpine Macro and Bull Theory charts' underlying data can be sourced for the voices register (chart images only at intake).

## 10. Sign-off

| Decision | Ruling | Date |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |
| 6 | | |
| 7 | | |
| 8 | | |
| 9 | | |
| 10 | | |

Status on completion: RULED YYYY-MM-DD, filing pending → FILED on commit.

---

## Appendix A — Sources (voices register entries)

All dated 2026-10-06 intake unless stated; public LinkedIn posts; URLs to be captured at filing.

| Voice | Affiliation | Item(s) | Standing |
|---|---|---|---|
| Joe Little | HSBC Asset Management, Chief Strategist | 2 | Desk strategist |
| Elliott Wave International | — | 5 | Sentiment/positioning publisher; patterns ignored |
| Tony Ferreira | All Weather Portfolio Letter | 8 (seen) | Newsletter |
| Till Christian Budelmann | Bergos AG, CIO | 7 | Desk; relaying Bianco Research / E. F. McQuarrie |
| Ryan Lemand | — (financial economist) | 1 | Relaying BofA Investment Research via a16z Growth |
| Topdown Charts | — | 6 | Chart publisher; model spec unpublished |
| Alpine Macro | — | 3 | Research house; chart only |
| Maxence Visseau | Arkevium Capital & Research | 4 | Independent research; stored source for the three paths |
| Karl Gauvin | — (institutional advisor) | 9 | Relaying Inovestor CPMS data |
| Sarmaya Partners | — | 12 | Commodity manager; paper linked |
| Jeremy Courtial, CFA | Family office, Head of Investments | 13 | Relaying Société Générale Cross Asset Research idea; own fit |
| Charles-Henry Monchau | Syz Group, CIO | 14 | Relaying Bull Theory charts |
| Charles Diebel | Macro strategy | 15 | Practitioner recollection (1994, 2011) |

## Appendix B — Narrative register lines (dated 2026-10-06)

- **The 10y top, four answers.** Diebel: 1994-type correlated repricing, nearly complete; deflationary risk by mid-2027 if energy reverses. Courtial/SocGen: twin deficits imply 5.8%; ~50bp of fiscal premium unpaid. Visseau: priced for a 5.0–5.5% chop, mechanics flirting with a spiral to 5.75–6.0%+; the growth-shock path makes duration at 5.25% the trade of the cycle. Sarmaya: the Fed blinks. Status: disagreement, unresolved; adjudicated by SR-43 and SR-49 once built.
- **Visseau's three paths** (reflexive spiral / controlled repricing / growth shock) and the reading that the market is priced for the second while the mechanics flirt with the first. Status: scenario set, stored.
- **Treasury buybacks as intervention.** Two operations failed to arrest the move; buybacks do nothing for volatility, margin or correlation. Status: claim, to be tested by SR-41(b).
- **Profits are the whole story.** Little: resilience is earnings, not multiple; the question is what happens if profits slip. Lemand/BofA: the earnings are the hyperscalers' capex, and one of the two groups will be disappointed. Status: thesis pair, consistent with Factor I; tested at the late-October prints.
- **Copper is crowded.** 23-year positioning extreme on the AI/power narrative. Status: positioning tell; base rate pending SR-42 ledger.
- **Breadth at records.** 49% (month-end) / 59% (daily) of members ≥20% below their highs with the index at a record; 95th percentile of record months; 2000 the comparable. Status: contextualised; ledger pending SR-45.

## Appendix C — Base-rate rows to add by hand

| Row | Content | Source | Entry |
|---|---|---|---|
| Rolling-10y long-bond return at record low | Sep 2026 −2.23% annualised nominal; prior low Dec 1959 −0.08%; window spans 2020–21 starting yields and deteriorates mechanically until ~2031 | McQuarrie via Bianco | SR-44 |
| 1994 bond rout | Bunds +~190bp Feb–Oct 1994; −~400bp over the following years; all DM yields correlated | Diebel | SR-49 |
| 2011 sovereign crisis | Divergent: Bunds fell while BTPs/GGBs spiked; focal sovereign Greece; resolution required programme and hardship | Diebel | SR-49 |
| Equal-weight seven-week losing streaks | 2002 (10 weeks), 2022 (7 weeks); n = 2, no signal right | Bull Theory via Monchau | SR-45 (seen) |
