# Change order — Signal triage Batch 14 (items 62–71): round 6, Part 6

| | |
|---|---|
| File | `docs/change-order-signal-triage-batch-14-2026-10-20.md` |
| Status | **RULED 20 Oct 2026 in chat**: items 55–60 "accepted; build change order"; items 61–64 "Accepted, and integrate into the change order starting at 55". Filed 20 Oct 2026 with filing amendments F1 to F8 (§0), ruled 20 Oct 2026, 23:07 ET ("Accepted"). |
| Encoding | Batch 14 of Post-Freeze Amendment #4. It was written as "round 6, Part 6, items 55–64, Batch 12 (provisional)", with the instruction to fold Batches 7–11 into one order if they were unfiled. They are filed: Batches 7, 8, 9 and 11 (items 46–58), Batch 12 (items 59–60, filed today from the round-6 Part 5 order's items 53–54) and Batch 13 (item 61, relative options volume, filed today). Batch 10 was never used. Items 55–64 are therefore filed as **62–71** (§0, F1). |
| Precedence | Below Part 26 and the 25 Sep integrated signal-triage order. It follows that order's integration rules: R28 sub-states, one system of record, T&B overlay intake one at a time, Track D preconditions, and validation gates as offline calibration studies with dated ledgers. |
| Built by | Two parts (§0, F8). Part A, the 1 Nov Monthly candidates: session A (paste A56: items 64, 69, 70; it files this order) and session B (paste B52: items 63, 66), each on its own branch, merged before the Monthly's last dry run on 28 Oct. Part B after the 1 Nov Monthly. |

---

## 0. Filing amendments (ruled 20 Oct 2026, "Accepted")

- **F1, the numbering.** Batch 14; items 62 to 71; work IDs keep the round-6 prefix with the new numbers (ST-R6.62a to ST-R6.71d). Every number below reads through this table:

  | Written as | Filed as | | Written as | Filed as |
  |---|---|---|---|---|
  | 55 HSBC CMA line | **62** | | 60 PEG at 0.68 | **67** |
  | 56 AI capex chain | **63** | | 61 NAR pending sales | **68** |
  | 57 10y and real 10y | **64** | | 62 $200bn MBS claim | **69** |
  | 58 one big AI trade | **65** | | 63 10y vs nominal GDP | **70** |
  | 59 transmission mechanisms | **66** | | 64 top-of-book depth | **71** |

  The order's "item 54" is the filed **item 60** (the earnings-estimate overshoot, its implied growth, its forecast error and SR-16's neocloud line) and its "item 53" is the filed **item 59**. Its items 52 and below keep their numbers.

- **F2, no new by-hand lines.** Rule 30 and the 16 Oct standing rule on sources: friction means a keyless alternative or a listed gap.
  - **62's cross-house CMA table** is not updated by hand. It becomes a reference table of the reading shelf's publication watch: the watch adds HSBC AM's Capital Market Assumptions and Vanguard's Capital Markets Model outlook to the shelf, and records each house's 10-year assumptions (US equity, ex-US developed equity, EM equity, Treasuries, IG, HY, 60/40) with the URL and the edition date. The scans ingest stores them as sourced figures; code computes the median and the dispersion; the Monthly's slow layers print the table. The watch is a chat-side scheduled task, and this chat updates its prompt.
  - **65's AI-credit watch** (CoreWeave, Oracle and SpaceX CDS and spreads) is a **listed gap**, beside SR-16's neocloud line (Batch 12, F2), unless Ari gives an explicit yes to a monthly by-hand line.
  - **65's Broad AI against S&P ex-AI-enablers** is built only from a free proxy the session maps (§5, item 2), labelled "proxy" and never given Goldman's name. Until then it is a listed gap.
  - **The one-off lines** go to `docs/dated-appendix-queue.md`: the 10y and real-10y record (64), the NAR 66.0 print (68) and the 8% forecast (70). Each is a dated record, not a data line.

- **F3, the sources that are withdrawn or refused.**
  - **67, PEG and LTEG.** No keyless source serves either. Yardeni fails the standing rule (A53's check of 20 Oct: robots.txt disallows `/api`, which the chart pages read, and the copyright notice forbids use without written consent); S&P DJI was withdrawn on 17 Oct; long-term growth is a proprietary consensus field. So the pair and its flag are **listed gaps** and do not print. Built anyway: the base-rate note on LTEG's overshoot (2000, 2021), written from published studies and cited, as a note; and the narrative entry "the market is cheap on PEG", seeded as PROPOSED through the existing proposal path with its caveat. The pair leaves the 1 Nov Monthly list.
  - **64, the real 10y against the S&P forward earnings yield.** The forward earnings yield has no keyless source for the same reasons. The spread is built as the real 10y (FRED DFII10) against the cyclically adjusted earnings yield from Shiller's data, already stored: Shiller's "excess CAPE yield", labelled, with dual percentiles. The forward version is a listed gap.
  - **65's AI-bottleneck PPI lines** come through FRED, which carries BLS's PPI industry series (the IDs are §5, item 1), not from BLS directly: BLS refused the box's feed reads on 20 Oct.
  - **68, the per-household pending-sales index.** NAR's index has no free series (item 36 dropped it under rule 30), so the per-household line deflates **Redfin's** pending sales by Census household counts (FRED), labelled single-source.
  - **69, the housing footprint.** The primary mortgage rate is Freddie Mac's PMMS through FRED. The current-coupon MBS yield is built only from a keyless proxy (§5, item 7); otherwise it is a listed gap. GSE retained portfolios come from the GSEs' public monthly summaries only if they are keyless and simple; otherwise a listed gap. The real Case-Shiller level comes from Shiller's public housing data.
  - **71, the fragility panel.** ES top-of-book size is not in the bars store, which holds OHLCV only: a listed gap unless the intraday source serves level-1 size free (§5, item 8). SPY's Amihud measure and range per unit of volume come from stored daily bars; margin debt from the existing FINRA writer; the leveraged ETFs and their AUM from the existing leveraged-ETF writer where it covers them (§5, item 9).

- **F4, the voices.** An entry is added only where the person publishes on a public page the voices scan may read under its robots and terms (a blog or a site, for example). X-only accounts go to the X pilot's seed list, whose ledgers keep attention and voices. LinkedIn posts are not read. Tags as ruled.

- **F5, the rights.** As ruled, and no more. Nothing enters a composite or the market-state object. The fragility flag's "liquidity" lens is a report-only column in item 52's attribution table. The speed-flag attribution (65) runs only when the term-structure models' inputs for that day are stored, and says "awaiting" otherwise.

- **F6, item 69's claim, checked at filing.** The claim is real and dated. On 8 Jan 2026 the President said he was instructing purchases of $200bn of mortgage bonds through Fannie Mae and Freddie Mac, and FHFA's director confirmed it; later reports describe the GSEs increasing purchases (press reports, 20 Oct check). So:
  - the narrative entry is tagged "verified (announcement of 8 Jan 2026); the post's source is a promoter";
  - item 20's ledger records a housing intervention dated 8 Jan 2026;
  - the size and pace of what was actually bought is what the GSE retained-portfolio line measures.

  The session confirms the date and terms against a primary FHFA or GSE release and cites it.

- **F7, the source checks first.** The session runs §5's nine checks before building and records each result in its notes. Anything that fails the standing rule on sources becomes a listed gap.

- **F8, two parts.**
  - **Part A, the 1 Nov Monthly candidates (about 9 hours):** 63 (the capex-chain reference table and its relative line), 64 (the excess CAPE yield against the real 10y), 66 (the wealth-effect impulse, the net-transmission line and its ledger), 69 (the mortgage and MBS spreads, GSE holdings, the real Case-Shiller percentile) and 70 (the nominal-growth anchor and the scorecard column). It must merge before the Monthly's last dry run on 28 Oct; the deploy freeze starts 29 Oct at 23:30.
  - **Part B, after the 1 Nov Monthly (about 10 hours):** 62 (the CMA table, through the shelf), 65 (the speed-flag attribution and its ledger, the AI-bottleneck PPI lines, the AI proxy), 67 (the note and the narrative entry), 68 (the per-household line) and 71 (the fragility panel, flag, lens and air-pocket ledger).

---

## 1. Purpose and scope

These are ten third-party posts triaged and ruled on 20 Oct 2026: items 55–60 in the afternoon and items 61–64 in the evening. Most amend existing entries. In particular:
- They complete the earnings chain started in items 29, 35, 40 and 54.
- They add the "loosening" leg to the rates-transmission cluster from items 34, 36 and 41.
- They extend the AI-credit watch created in item 54.
- They deepen item 36's housing block (items 61, 62).
- They add a nominal-growth fair-value anchor for the 10y (item 63).
- They add a market-structure liquidity-fragility panel (item 64).

No composite weights change.

Entry conventions are unchanged: **Source** · **Read** · **Thought process** · **Ruling** · **Rights** · **Placement** · **Work**.

## 2. Entries

### 55 · HSBC AM capital market line (Joe Little, HSBC Asset Management)

**Source.** HSBC AM's 10-year Capital Market Assumptions, "Chart of the week". Tag: house view.

**Read.** The chart plots 10-year expected return against expected volatility, from US 2-year Treasuries at about 4% up to EM equity at about 10% and global private equity at about 11%, with Sharpe-ratio bands from 0.15 to 0.45. Little draws three signals:
- higher-for-longer lifts expected fixed-income returns;
- relative valuations favour EAFE and EM over US equities;
- investors should "diversify the diversifiers."

**Thought process.** One capital-market-assumptions chart is a single house's view. The useful signal is the cross-section of houses. Where houses disagree, an estimate carries little information. Where they converge (today, on bonds paying more than before), that consensus is the thing to test. JPM LTCMA, AQR, GMO and Research Affiliates are already on the reading shelf; HSBC is not. "Diversify the diversifiers" repeats the AQR lesson from item 25.

**Ruling.**
1. Add HSBC AM's Capital Market Assumptions to the reading shelf.
2. Build a **cross-house CMA table** in the Monthly's slow layers. It shows 10-year expected returns for US equity, ex-US developed equity, EM equity, Treasuries, IG, HY and 60/40 from JPM, AQR, GMO, Research Affiliates, HSBC and Vanguard, with the median and dispersion for each asset. Update it as editions publish.
3. The table feeds item 30's Book A long-horizon expected-return line.

**Rights.** Report only.
**Placement.** Slow layers; Book A rule table (as input to item 30).
**Work.** ST-R6.55a table and render, 2h. Edition updates by hand.

### 56 · Following the AI capex money (BNP Paribas Equity Research, via a16z / Ryan Lemand)

**Source.** BNP Paribas, illustrative $100 of AI capex mapped across the supply chain (August 2026), published by a16z and posted by Lemand. Tag: sell-side primary, aggregator post.

**Read.** The $100 splits as follows:
- semis $50: accelerators $25, memory $15, CPUs and server production $10;
- power $20: grid and independent generation $10, distribution $6.5, on-site routing $3.5;
- networking $15;
- cooling $7.5;
- facilities and construction $7.5.

Wafer-fab equipment takes about $8, roughly half of it lithography. Lemand's point is that half of every capex dollar stays with the chipmakers.

**Thought process.** This is the supply-chain weighting that the AI five-bucket decomposition (GTM-4) lacks. It answers who actually gets paid, and so serves as a revenue-exposure map for capex sensitivity. Power is the second-largest bucket but has the longest lead time, which explains item 23's puzzle of power construction at only +4%. BNP flags the weights as high-level estimates.

**Ruling.**
1. Adopt the BNP weights as a standing reference table in Factor I and in the Equities paper's AI-rings section, dated August 2026.
2. Map each bucket to a liquid proxy: semis (SMH/SOXX), memory names, networking equipment, power equipment and utilities, cooling, and construction.
3. Add a monthly **capex-chain relative-performance line** showing which bucket leads or lags against the capex-guidance series (item 26).

**Rights.** Report only.
**Placement.** Factor I (Disruptive Themes refresh brief); Equities paper; what's priced.
**Work.** ST-R6.56a proxy mapping and relative line, 2h.

### 57 · 10-year at 5.31%, real 2.95%: highest since 2002 and 2008 (Charlie Bilello via Monchau)

**Source.** Bilello / Creative Planning charts, as of 9 Oct 2026. Tag: credible aggregator.

**Read.** The 10-year nominal yield, at 5.31%, is the highest since 2002. The 10-year real yield, at 2.95%, is the highest since 2008. Both are set against the 2020 lows.

**Thought process.** The stack already carries these readings through item 24, item 39 and the 10-year attribution. What is new is the real-yield level. At about 3% real, the comparison between a risk-free real return and the equity earnings yield turns decisively. The valuation quad's EY-minus-Baa line (GTM-2) captures this only partly.

**Ruling.**
1. Log only, with a dated appendix line.
2. Add a **real 10-year yield vs S&P forward earnings yield** spread to the valuation quad as an amendment to GTM-2, with dual percentiles.

**Rights.** Report only.
**Placement.** What's priced (valuation quad).
**Work.** ST-R6.57a spread, 0.5h.

### 58 · "It's all one big AI trade" (Sonu Varghese, Carson Group)

**Source.** Varghese's blog and LinkedIn post, with Carson/Bloomberg charts as of 15 Oct 2026. The concentration statistics come from Michael Cembalest (JPM). Tag: credible.

**Read.**
- The 10-year fell from 5.33% to 5.08% in a single day despite hot inflation data.
- Anthropic's revenue growth slowed.
- CDS on AI-related debt (CoreWeave, Oracle, SpaceX) surged.
- AI bottlenecks are feeding inflation: PPI for printed circuit assemblies is +130% y/y and computer storage devices +84%.
- Brent is at $110.
- Per Cembalest, 42 AI stocks account for 67% of S&P price returns, 58% of earnings growth and 81% of capex/R&D growth since January 2024.
- The Goldman Broad AI index is up 387% cumulatively since 2023, against 46% for the S&P ex-AI-enablers.
- His conclusion: diversify outside AI without trying to time the top.

**Thought process.** Three points are new.
1. A 25bp one-day fall in the 10-year on a hot print is a rates-vol event. The speed flag catches it, but nothing explains it. The 10-year attribution should therefore run automatically whenever the speed flag fires, using the same event pattern as item 52.
2. AI-credit stress has broadened beyond CoreWeave (item 54) to Oracle and SpaceX. SpaceX links directly to the SPCX IPO work.
3. The AI-bottleneck PPI lines are a measurable, free inflation channel that item 46's pass-through basket does not yet carry.

"One big AI trade" is item 25's "one bet" check applied to the whole market. The Goldman AI vs ex-AI split is a clean series for it.

**Ruling.**
1. Run the **10-year attribution automatically on speed-flag days**, with its own event ledger (the item-52 pattern applied to rates). The output names whether expected short rates (growth / AI-returns repricing) or the term premium carried the move.
2. Extend item 54's neocloud credit line to an **AI-credit watch** covering CoreWeave, Oracle and SpaceX CDS/spreads, by hand from public reporting. The SpaceX line also feeds the SPCX work.
3. Add an **AI-bottleneck PPI line** to item 46's pipeline: BLS PPI for printed circuit assemblies, computer storage devices and semiconductors, monthly.
4. Add a **Broad AI vs S&P ex-AI-enablers** relative series to the concentration cluster (items 30, 31, 44), from public reporting until a free proxy is mapped.
5. Varghese (Carson Group) goes into the voices register.

**Rights.** Flag rights already exist on the speed flag; everything else is report only.
**Placement.** Plumbing & rates (attribution event); credit block; inflation block; mechanics (concentration).
**Work.** ST-R6.58a speed-flag attribution trigger and ledger, 1.5h. ST-R6.58b AI-bottleneck PPI line, 1h. ST-R6.58c AI vs ex-AI series, 0.5h. AI-credit watch by hand, monthly.

### 59 · "The Battle of Transmission Mechanisms" (Juliette Declercq, JDI Research)

**Source.** JDI Research October report, posted on LinkedIn, with a chart sourced from JDI (SPX, ISM). Tag: research seller with open positions.

**Read.** The chart sets an equity wealth-gains estimate (share of financial assets held in equities and mutual funds × SPX y/y return) against ISM new orders and employment. Declercq argues that the Fed tightens through housing and credit while the AI boom loosens through household wealth effects. She has opened two trades on the outcome.

**Thought process.** This is the missing half of the rates-transmission cluster. Items 34, 36, 37 and 41 measure the tightening channels; nothing measures the offset. The wealth-effect proxy is free to build: Z.1 household equity share (already in item 30) × SPX y/y. Read beside the K-shape panel (GTM-12, who holds the wealth) and the consumption-by-income lens (item 48.19), it shows whether tightening is reaching consumption at all.

**Ruling.**
1. Add a **wealth-effect impulse** series (Z.1 equity share × SPX y/y, monthly, with the ICI proxy between Z.1 releases) as the "loosening" leg of the rates-transmission cluster.
2. Add a **net-transmission line** setting the tightening legs (items 34, 36, 41) against this loosening leg, printed with the K-shape panel.
3. Build a calibration ledger against real consumption growth.
4. Declercq (JDI Research) goes into the voices register, tagged as a research seller with positions.

**Rights.** Report only until the ledger is built.
**Placement.** Plumbing & rates (rates-transmission cluster); slow layers.
**Work.** ST-R6.59a wealth-effect series and net-transmission line, 2h. Ledger, 1h.

### 60 · S&P 500 PEG ratio at 0.68, a record low (Mindset for Money / Yardeni, via Monchau) — AMENDMENT to item 54

**Source.** Yardeni Research / LSEG data, chart by Mindset for Money, posted by Monchau. Tag: credible voice; chart-house source.

**Read.** The S&P PEG (forward P/E ÷ 5-year consensus long-term expected EPS growth) was 0.68 on 17 Oct 2026. That is below the March 2009 low of 0.86 and well under the 1.35 average. Monchau asks whether this is a bargain or whether the 5-year growth estimate is simply wrong.

**Thought process.** The second question is the answer, and it is item 54's point. The PEG is low because the denominator is inflated, not because the price is low. A 0.68 PEG on a ~19x forward P/E implies ~28% annual long-term growth, matching item 54's implied forward growth. The 2009 low came from a depressed numerator; this one comes from an elevated denominator. Long-term growth (LTEG) is the least reliable consensus estimate, with a documented record of overshooting at peaks (2000; 2021). The low PEG is therefore a measure of estimate optimism, not of value.

**Ruling.**
1. Add **PEG and LTEG as a pair** to item 54's earnings-chain block:
   - PEG with dual percentiles;
   - LTEG against its own history and against realised 5-year EPS growth;
   - a base-rate note on LTEG overshoot (2000, 2021).
2. Add a **flag** that fires when LTEG-implied growth is above its 90th percentile while item 54's realised forecast error is negative.
3. Add a narrative-register entry, "the market is cheap on PEG," as a bull narrative carrying that caveat.
4. Source: Yardeni's public series, with S&P DJI as the cross-check.

**Rights.** Flag only.
**Placement.** What's priced (earnings chain).
**Work.** ST-R6.60a PEG/LTEG pair and flag, 1.5h.

### 61 · NAR pending home sales index at 66.0, a record low (Nick Gerli, Reventure) — AMENDMENT to items 36 and 37

**Source.** Gerli on X, 20 Oct 2026. The chart is by re:venture, using NAR data. Tag: housing-data product seller.

**Read.**
- NAR's pending home sales index fell to 66.0 in September 2026, the lowest reading ever recorded.
- It is 50% below the pandemic peak, 35% below 2019, below the 2008–09 lows, and down 11% y/y.
- Gerli says mortgage rates are back above 7%.

**Thought process.** This is item 36's NAR cross-check, and it confirms the Redfin read. "Lowest ever" is genuine on this index, but the index takes no account of household growth. The case that the market is frozen rather than falling gets stronger, because volume is now at a record low. Whether prices break is still the open question, and months of supply remains the tell. Item 36's flag already carries that.

**Ruling.**
1. Record the 66.0 print as a dated line in item 36's ledger.
2. Add a per-household version of the pending-sales index (index deflated by household counts) beside the raw level.

**Rights.** As item 36.
**Placement.** Plumbing & rates (housing block).
**Work.** ST-R6.61a per-household index, 0.5h.

### 62 · "$200bn of mortgage-bond purchases ordered" (@CryptoNobler on X)

**Source.** @CryptoNobler on X, ~20 Oct 2026, with a chart of real Case-Shiller house prices from 1890 to 2026. Tag: promoter (self-promoting top/bottom-caller account). **Claim unverified.**

**Read.**
- The post claims the President ordered $200bn of mortgage-bond purchases to force mortgage rates lower.
- It frames the purchases as keeping a housing bubble alive, with real home prices at record highs, affordability crushed and supply constrained.
- It says bonds, stocks, metals and crypto are all connected.

**Thought process.** The source is weak, but the mechanism is real and checkable. Any purchase programme, whether through the GSEs, Treasury or the Fed, shows up in the spread between mortgage rates and Treasuries and in the GSE retained portfolios. It matters twice:
- It would be a policy floor under item 36's house-price-decline watch.
- It would be a second instrument in item 20's Treasury reaction function, beside the 5% line.

Separately, the real Case-Shiller level the post cites is free. It is the right valuation companion to the T&B real house-price YoY input.

**Ruling.**
1. Verify the claim from primary sources (FHFA, Treasury, GSE releases) before anything prints. Until then it goes in the narrative register only, tagged promoter.
2. Add two spreads to item 36's housing block, with dual percentiles: the primary-mortgage-rate minus 10y spread, and the current-coupon MBS minus 10y spread. These are the measurable footprint of any purchase programme.
3. Add GSE retained-portfolio holdings, monthly, from FHFA and GSE monthly summaries.
4. If the claim is verified, log it in item 20's Treasury reaction-function ledger as a housing intervention.
5. Add the real Case-Shiller level, as a percentile of its 1890– history, to the slow layers beside the Reinhart–Rogoff input.

**Rights.** Report only.
**Placement.** Plumbing & rates (housing block); slow layers; `rates.driver` ledger (conditional).
**Work.** ST-R6.62a spreads and GSE holdings, 1.5h. ST-R6.62b real Case-Shiller percentile, 0.5h. Verification by hand.

### 63 · "10-year could reach 8%": bonds vs nominal GDP (Tom Bradshaw, FXEmpire)

**Source.** Bradshaw on LinkedIn and in an FXEmpire article, ~19 Oct 2026. Chart: US 10y yield vs 10-year CAGR of US nominal GDP, 1970–2026, with a stated 93% correlation. Tag: newsletter writer.

**Read.** The 10y tracks long-run nominal GDP growth. With nominal growth near 6% and the economy strong, Bradshaw argues the 10y could reach 8%.

**Thought process.** Yield ≈ nominal growth is a sound long-run anchor. The 93% figure, though, is a correlation between two trending levels and does not help with timing. The chart also contradicts its own headline: a ~6% nominal CAGR implies a 10y near 6%, not 8%. The useful measure is the gap between the two lines. That gap is macro r−g, the debt-sustainability counterpart of item 29's equity r−g. A small or negative gap is the condition under which debt can be sustained without fiscal consolidation, which links to items 20 and 21. Item 13 already carries a twin-deficit fair-value anchor; this adds a second, independent one.

**Ruling.**
1. Add a **nominal-growth anchor** to the 10y attribution block: 10y minus the 10-year nominal GDP CAGR, and 10y minus the 5-year CAGR, quarterly from BEA, with dual percentiles.
2. Print it beside item 13's twin-deficit anchor as a fair-value range.
3. Add the US macro r−g as a column in item 21's sovereign scorecard.
4. Log the 8% forecast as appendix-only.

**Rights.** Report only.
**Placement.** Plumbing & rates (10y attribution); slow layers (item 21 scorecard).
**Work.** ST-R6.63a anchor and scorecard column, 1h.

### 64 · S&P top-of-book depth at a record low (Goldman Sachs via ZeroHedge, posted by Ryan Lemand)

**Source.** Goldman Sachs GBM figures as compiled by ZeroHedge, posted by Lemand, ~16 Oct 2026. Tag: Goldman via public reporting only; ZeroHedge is an aggregator; Lemand is already in the register.

**Read.**
- S&P top-of-book depth per $1bn of daily US equity value traded was $162K in 2017, $40K in 2018, $12K in 2022, $13K in 2025, and $11K in 2026 YTD, the thinnest on record.
- Volume has exploded while depth has collapsed, so every dollar of volume moves price further.
- Lemand cites the air pockets of February 2018, August 2024 and April 2025.
- With record margin debt, leveraged-ETF close rebalancing and dealer gamma hedging all generating forced flow into an empty book, he argues a 3% day can become a 7% day. His caveat: thin books also snap back fast.

**Thought process.** This is the market-structure amplifier the stack lacks. Dealer gamma (6b), the vol-event block (item 52) and the three-timeframe ES read (item 45) all say where forced flow goes. Depth says how far price travels per unit of that flow. Goldman's series is proprietary, but free proxies exist:
- ES top-of-book size from the box's own intraday store (item 45 builds it);
- Amihud illiquidity (absolute return per dollar volume) on SPY;
- daily range per unit of volume.

The forced-flow sources can be measured in part: FINRA margin debt (free, monthly); a leveraged-ETF close-rebalance estimate from AUM and the day's return (a known formula); and dealer gamma. Forced-flow capacity divided by depth is a fragility measure.

**Ruling.**
1. A **liquidity-fragility panel** in mechanics:
   - ES top-of-book depth from item 45's store, and SPY Amihud illiquidity, daily, with dual percentiles;
   - FINRA margin debt, monthly, as a level and as a share of market cap;
   - a leveraged-ETF close-rebalance estimate for the major 2× and 3× index ETFs: AUM × L × (L − 1) × daily return;
   - dealer gamma from 6b.
2. A **fragility flag**: depth below its 10th percentile while the forced-flow estimate (leveraged-ETF rebalance plus negative dealer gamma) is above its 90th.
3. The flag becomes a tenth lens, "liquidity," in item 52's vol-event attribution, and feeds item 45's levels read.
4. A base-rate ledger on the air pockets of February 2018, August 2024 and April 2025, built from the free proxies.

**Rights.** Flag only. Any T&B or Book C modifier comes only after the ledger.
**Placement.** Mechanics; item 52's vol-event block; item 45's ES block.
**Work.** ST-R6.64a depth proxies and margin debt, 1.5h. ST-R6.64b leveraged-ETF rebalance estimate, 1h. ST-R6.64c flag and the item-52 lens, 0.5h. ST-R6.64d air-pocket ledger, 1h.

## 3. Cross-item notes

- **Earnings chain, complete.** The chain now runs from revisions turn (29) to forecast error (54) to implied growth and LTEG (54, 60), with the price–ULC gap as mechanism (35) and the decomposition as outcome (40). The real-yield-vs-earnings-yield spread (57) is the discount-rate side. All of it prints together in what's priced.
- **Rates-transmission cluster, two-sided.** The tightening legs (34, 36, 37, 41, 53) are now matched by the loosening leg (59), and the net-transmission line is the read.
- **AI thread.** The capex-chain weights (56), AI credit watch (58, extending 54), bottleneck PPI (58) and concentration split (58) all feed Factor I and the next Disruptive Themes refresh brief. None is scored before that brief.
- **Rates events.** Speed-flag attribution (58) and the vol-event block (52) print adjacent in mechanics when both fire.
- **Housing block, deepened.** Items 36, 37, 61 and 62 now cover demand (pending sales, purchase applications), supply (months of supply), price valuation (real Case-Shiller percentile) and the policy footprint (mortgage and MBS spreads, GSE holdings).
- **10y fair value.** The twin-deficit anchor (13) and the nominal-growth anchor (63) together give a fair-value range. The attribution says what moved the yield; the anchors say where it sits relative to fundamentals.
- **Fragility chain.** Liquidity depth (64) sits beside dealer gamma (6b), the vol-event block (52) and the ES levels (45). Depth measures how far forced flow travels; gamma and leveraged-ETF rebalancing measure how much forced flow there is.

## 4. Work order (provisional; the audit places it)

- **Now:** ST-R6.55a (2h), 56a (2h), 57a (0.5h), 58a (1.5h), 58b (1h), 58c (0.5h), 59a (2h), 60a (1.5h), 61a (0.5h), 62a (1.5h), 62b (0.5h), 63a (1h), 64a (1.5h), 64b (1h), 64c (0.5h). About 17.5h.
- **Ledgers:** item 59 calibration (1h); item 64 air-pocket ledger (1h).
- **By hand:** CMA edition updates, AI-credit watch, verification of the item-62 claim, and the voices entries. About 1.5h to set up, then about 1h a month.
- **Total:** about 19.5h of sessions plus about 1.5h by hand.
- **Candidates for the 1 Nov Monthly:**
  - item 57's spread;
  - item 60's PEG/LTEG pair, alongside item 54;
  - item 59's net-transmission line;
  - item 56's reference table;
  - item 63's nominal-growth anchor;
  - item 62's mortgage spreads.
- **Dependency:** item 64's ES depth proxy depends on item 45's intraday store. The SPY Amihud measure and margin debt can run first.

## 5. Verify items

1. BLS PPI series IDs for printed circuit assemblies and computer storage devices, and their history (58).
2. A free proxy for the Goldman Broad AI and S&P ex-AI-enablers indices (58).
3. Free availability and vintage history of Yardeni's LTEG and PEG series (60).
4. Publication cadence for the HSBC and Vanguard CMAs (55).
5. Whether the 5.33%→5.08% one-day move on the date Varghese cites matches FRED DGS10 (58).
6. The $200bn mortgage-bond purchase claim, checked against FHFA, Treasury, GSE or Fed releases (62).
7. A free current-coupon MBS yield series, or a proxy (MBS ETF yield, or the Freddie Mac PMMS spread alone) (62).
8. Free availability of ES top-of-book size in the intraday source chosen for item 45 (64).
9. A list of the leveraged index ETFs and their daily AUM for the rebalance estimate (64).

## 6. Register, voices and sources

**Register:** Items 55–64 keep their round numbers; SR numbers are assigned at filing, after Batches 5–11. Amendments:
- 57 amends GTM-2;
- 58 amends items 46 and 54;
- 60 amends item 54;
- 61 amends items 36 and 37;
- 62 amends item 36, and item 20's ledger if verified;
- 63 amends item 21's scorecard;
- 64 amends items 45 and 52.

**Voices:** Joe Little (HSBC AM, house view); Sonu Varghese (Carson Group, credible); Juliette Declercq (JDI Research, research seller with positions); Nick Gerli (Reventure, housing-data seller); @CryptoNobler (promoter); Tom Bradshaw (newsletter writer). Lemand, Monchau and Bilello are already registered.

**Shelf:** HSBC AM Capital Market Assumptions; Vanguard Capital Markets Model outlook (for the cross-house table).

**New sources:** BNP Paribas capex-chain weights (August 2026); BLS PPI detail lines; Yardeni LTEG/PEG series; Goldman AI indices (via public reporting); NAR pending home sales index; Census household counts; Freddie Mac PMMS; FHFA/GSE monthly summaries; Shiller real home-price series; BEA nominal GDP; FINRA margin statistics; leveraged-ETF AUM (issuer sites).

## 7. Decisions and sign-off

- Items 55, 56, 57, 58, 59 and 60 ruled on 2026-10-20 ("accepted; build change order").
- Items 61, 62, 63 and 64 ruled on 2026-10-20 ("Accepted, and integrate into the change order starting at 55").

Signed: A. Chester, 2026-10-20 (chat rulings as recorded above).
Filing: fold into the round-6 order if Batches 7–11 are still unfiled; otherwise commit after them. Register entries go to the next Doctrine sitting.
