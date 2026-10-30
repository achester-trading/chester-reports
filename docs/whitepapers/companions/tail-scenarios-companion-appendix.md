# The Twenty-Five — the scenario treatments (companion appendix)

**Companion appendix to The Twenty-Five (Tail Scenarios: Mechanism, Mutation, and Instrumentation) · maintained with the Monthly's Part 16 · moved from the paper's body on 25 October 2026 under Audit 2's Phase 3 (first edition 29 August 2026)**

*The twenty-five scenarios, each on the paper's seven-element template (mechanism, precedent, tripwire, current state, transmission, mutations, report routing), by mechanism family. Moved here unchanged; the paper's body keeps Part 0, the seven families, the operations and Part 3's mutation scan. The current states are as of the first edition (29 August 2026) and are refreshed with the Monthly's Part 16, not in the paper.*


## FAMILY A — FUNDING, DURATION AND PLUMBING

## Scenario 1 · Funding-market accident

**Tier A · daily**

### Mechanism

The plumbing failure runs in five steps, and each one is observable.

Bank reserves fall below the level at which dealers are willing to intermediate freely. That threshold is not a published number; it is a behavioral property of the system that reveals itself only by being crossed, which is the single most important fact about this scenario. As reserves tighten, dealers ration balance sheet: repo becomes expensive, then selective, then unavailable to the weakest counterparties. Secured overnight rates spike above the rate the Fed pays on reserves, which should be an arbitrage and is not, because the arbitrage requires balance sheet nobody will lend. Leveraged positions financed in that market — the Treasury basis trade above all, but also mortgage carry, swap spread positions, and relative-value books — face margin calls and cannot roll their funding. They liquidate into a market where the natural buyer is the same dealer community that just stopped intermediating. Prices gap, volatility rises, margin requirements rise mechanically with volatility, and the liquidation feeds itself.

The reason this sits at the top of the list is that every subsequent scenario in this family, and several outside it, terminate in this mechanism. It is the common failure mode.

**What makes today structurally different from 2019.** The September 2019 repo episode occurred at reserve levels *higher* than those prevailing now. Three buffers that existed then are diminished or gone. The reverse repo facility, which held over $2 trillion at its peak and functioned as a shock absorber that could be drained without touching reserves, is effectively exhausted. Reserves stand near $2.94 trillion, and every dollar of new bill issuance now drains them directly rather than pulling from the RRP. And the Treasury General Account, at roughly $950 billion, is both large and, per the Twist discussion in the *Foundations* paper, potentially mobile: a TGA drawdown *adds* reserves, a TGA build *drains* them, and the account is currently the subject of an unresolved policy question about funding buybacks. The system's shock absorber has been replaced by a variable that policy might move for unrelated reasons.

### Precedent

**September 17, 2019** is the clean instance: a corporate tax date and a large Treasury settlement coincided, SOFR printed near 10% intraday against an IORB near 2.10%, and the Fed was conducting emergency repo operations within twenty-four hours and buying bills within three weeks. Nothing was fundamentally wrong with the economy. The episode was purely mechanical, and its lesson is that the reserve threshold is discovered by crossing it.

**March 2020** is the severe instance and the more instructive one, because the failure occurred in the asset that is supposed to be the refuge. For roughly a week, Treasuries sold off during a flight to safety, as leveraged basis positions unwound and dealers refused to absorb the paper. The world's hedge asset failed at its one job until the Fed bought at a scale that made the failure moot. Every subsequent conversation about market functioning descends from that week.

**The disanalogy that matters:** in both episodes the Fed's balance sheet was available and its use was uncontroversial. The current configuration adds a complication the *Foundations* paper develops at length — a central bank whose chairman has staked his credibility on discipline and on the proposition that inflation is a choice, facing a fiscal authority whose financing needs are large and growing. The plumbing response is technically identical to easing, and will be read as easing by some portion of the market regardless of how it is framed.

### Tripwire

*First mover: SOFR–IORB spread, standing repo facility usage, settlement fails.*

**SOFR–IORB** is the primary instrument. Persistent positive readings mean secured funding is trading above the risk-free floor, which should not happen if balance sheet were freely available. A few basis points at a quarter-end is calendar noise. Persistent positive readings away from quarter-ends are the signal, and the elevated readings that matter arrive as a *sequence*, not a spike.

**Standing repo facility usage** is the stigma-adjusted confession. The SRF exists so that this scenario cannot happen, and non-trivial usage away from quarter-end means the mechanism it was built to prevent is already engaging. The instrument's weakness is stigma: usage may lag the stress it measures, so a zero reading is weaker evidence than a positive one.

**Settlement fails** are the slowest and most diagnostic of the three: a rising fails-to-deliver volume in Treasuries means the collateral chain itself is jamming rather than merely repricing.

**What a firing does not mean.** It does not mean a crisis has begun; it means the buffer is thinner than assumed. The 2019 episode resolved in weeks with no market damage outside the funding complex. The correct response is to tighten language on liquidity conditions and to raise attention on the leveraged structures in scenarios 19 and 20, not to reposition.

### Current state

**Armed.** Reserves near $2.94 trillion with the RRP buffer exhausted, roughly a third of marketable debt repricing within twelve months, bill-heavy issuance following the August 19 Twist, and a live policy question over whether the TGA gets drawn to fund buybacks. Every precondition the source list names is present. What is absent is a trigger, and triggers in this scenario are typically calendar events — a tax date, a large settlement, a quarter-end — which is precisely why the cadence is daily.

### Transmission

Lands squarely on **Factor IV**, and is the fastest of that factor's transmission paths: the slow fiscal thesis meeting its fast clock. Secondary transmission to **Factor II** through forced deleveraging and volatility-driven de-risking, and to **Factor V** if a stablecoin issuer is holding bills that must be liquidated into the same impaired market. The framework's own composite is not designed to move on this scenario, and should not: a funding accident is a condition of the plumbing, not of the cycle.

### Mutations

**Scope drift — the accident migrates to a market with no facility.** The Fed's tools are built for the Treasury repo market. The same mechanism operating in cross-currency basis, in the FX swap market, or in cleared derivatives margin has no equivalent domestic backstop, and the counterparties are frequently foreign. *Instrument:* cross-currency basis, FIMA repo usage (already promoted in early August as part of the yen intervention architecture, which is itself evidence this mutation is live).

**Substitution — the leveraged holder is not a hedge fund.** The basis trade is the named villain, but the same forced-seller dynamic now runs through leveraged Treasury ETFs, through insurance general accounts using repo for yield enhancement, and through the growing set of digital-asset treasury vehicles financing balance sheets against volatile collateral. Each has a different regulator, different disclosure, and different speed. *Instrument:* none consolidated. **Gap.**

**Aliasing — this becomes indistinguishable from scenarios 19 and 9 within one session.** A funding accident, an LDI-style deleveraging, and a failed auction all present as the same tape: long-end volatility, widening bid-offer, and a collateral chain under stress. The report's language when any one of them fires should acknowledge that the framework cannot yet tell which it is looking at.

**Re-specification trigger.** If SRF usage becomes routine rather than exceptional — a standing feature of month-end funding rather than an emergency valve — then the scenario has stopped being a tail and has become a description of the operating regime. At that point it should be rewritten as a *current condition* in Factor IV, and the tail slot should be re-scoped to the accident that occurs *despite* the facility.

### Report routing

**Primary: Daily Cascade, daily.** SOFR–IORB and SRF usage belong in the morning report as a standing liquidity block; both update intraday and neither is currently instrumented there. **Secondary: Top & Bottom, via the Liquidity & Funding Stress overlay**, which is the natural home for the persistence reading — the overlay's question is not whether the spread ticked positive but whether it has stayed positive. **Tertiary: Monthly Macro**, which carries the slow-moving context (reserve levels, TGA path, bill share of issuance) in the liquidity pillar. Settlement fails data has no home in any of the five reports today and goes to the build queue.

**What a firing changes:** Daily Cascade adds an explicit funding-conditions line and elevates it above the equity narrative; Top & Bottom's Liquidity overlay tightens; Disruptive Themes, at its next refresh, moves Factor IV's timing language from "the fast clock under a slow thesis" to a statement that the clock has started.

---

## Scenario 19 · LDI-style forced deleveraging

**Tier A · daily**

### Mechanism

An allocator with long-duration liabilities — a pension fund, an insurer, a liability-driven mandate — hedges those liabilities with leveraged long-duration assets, typically via repo or swaps. The leverage is rational: the liability is long, the capital available to match it is small, and derivatives close the gap efficiently. The vulnerability is that the hedge is collateralized. When long yields rise sharply, the hedge loses value, collateral is called, and the allocator must post cash. The cash is raised by selling assets. The most liquid assets are the same long-duration bonds whose price is falling. Each round of selling pushes yields higher, which generates the next collateral call.

The structure is a self-reinforcing loop with no natural stabilizer inside it. It stops when someone outside the loop buys, which in practice means the central bank.

### Precedent

**The UK gilt crisis, September 2022.** A mis-sized fiscal announcement produced a gilt selloff into pension LDI structures; the spiral ran for days; the Bank of England was buying long gilts within a week, against its own tightening program, and explicitly framed the intervention as financial stability rather than monetary policy. The episode's most portable lesson is institutional: the central bank's stated policy direction lasted precisely as long as the plumbing held.

**The disanalogy:** the UK system was unusually concentrated in a single technique with a single regulator, and the market was small enough for the spiral to be visible in real time. The equivalent US structures are more diffuse, less uniformly leveraged, and spread across insurers, corporate plans, and public funds with heterogeneous disclosure. Diffusion is not safety. It means the same aggregate exposure is harder to see, and the diagnosis will arrive later.

### Tripwire

*First mover: long-end realized volatility, term premium spikes, cross-asset correlation.*

Long-end **realized** volatility rather than implied is the correct primary, because the loop is driven by actual price movement generating actual collateral calls. A term premium spike distinguishes a duration event from a policy-expectations event, which matters: this scenario is indifferent to why yields rose. Rising cross-asset correlation is the confirmation that selling has become indiscriminate — the signature of a liquidation rather than a repricing.

**What a firing does not mean:** volatility at the long end is common and mostly benign. The scenario requires volatility *plus* evidence of forced flow, which means the confirmation series matter more here than the primary.

### Current state

**Loading.** The 30-year sits near 5.21%, a level the *Foundations* paper notes as above the threshold strategists had flagged. Rate volatility has been elevated through the guidance withdrawal. What is unknown, and unknowable from public data, is the leverage embedded in US liability-matching structures at these yields. That opacity is the scenario's defining feature.

### Transmission

**Factor IV** primarily, through the same long-end channel as scenarios 1 and 9. Secondary to **Factor II**: a forced seller of duration in size is frequently also a holder of equities, and correlated liquidation is how a bond-market accident becomes an equity drawdown without any change in earnings.

### Mutations

**Scope drift — the technique is no longer only pensions.** Any leveraged liability-matcher qualifies. Insurance general accounts running duration against annuity books, leveraged endowment overlays, and increasingly the digital-asset treasury companies discussed in the *Foundations* paper's Chapter 5, which hold volatile assets against fixed obligations and margin structures. The physics are identical; only the collateral differs. *Instrument:* none consolidated. **Gap.**

**Substitution — the collateral call arrives through clearing rather than bilateral repo.** Centrally cleared margin rises mechanically with volatility, which means a clearinghouse can generate the same forced-selling loop without any bilateral counterparty making a decision. This mutation is systemically *more* dangerous because it is fully automatic. *Instrument:* clearing margin requirement changes, which are published but not tracked anywhere in the system today. **Gap.**

**Aliasing — indistinguishable from 1 and 9 in the first days**, and from 24 if the forced selling occurs in credit rather than governments.

**Re-specification trigger.** If a US structure delivers even a contained version of the gilt spiral, this scenario ceases to be an analogy borrowed from another jurisdiction and becomes a domestic condition with a named cohort. The rewrite would move it from Tier A tail to a standing surveillance item in the Liquidity overlay.

### Report routing

**Primary: Top & Bottom, Liquidity & Funding Stress overlay**, which is the correct home because the scenario is a stress-state question rather than a daily-tape question. **Secondary: Daily Cascade** for long-end realized volatility, which FlashAlpha's data can support directly. **Monthly Macro** carries term premium in the rates pillar. The confirmation series — evidence of forced flow — has no instrument and goes to the build queue as an acknowledged gap rather than a weak proxy.

---

## Scenario 9 · Failed Treasury auction

**Tier B · weekly**

### Mechanism

Not a literal failure, which is essentially impossible given primary dealer obligations. The scenario is an auction that *tails* badly: the yield awarded comes in materially above the pre-auction market level, indicating that bidders demanded a concession to absorb the size. A single bad auction is noise. A sequence, particularly at the long end and particularly with falling indirect bidder participation, is a repricing of the term premium driven by demand rather than by policy expectations, and it forces every holder of duration to reconsider what they are being paid for it.

The structural aggravator is issuance composition. Bill-heavy issuance following the Twist means the coupon auctions that remain are being absorbed by a narrower buyer base, and the elevated near-term maturity share means the calendar is relentless: roughly a third of marketable debt reprices within twelve months, so the test recurs continuously.

### Precedent

There is no clean US instance, which is exactly why the scenario merits a slot. The closest analogs are foreign: the 2022 gilt episode, and periodic Japanese long-bond auctions that have cleared poorly enough to move global term premia. The US instance would be historically novel, and novelty in this domain means the market's reaction function is unknown.

### Tripwire

*First mover: auction tails, bid-to-cover, indirect bidder share, term premium.*

Tails are the primary and should be read as a rolling sequence. Bid-to-cover is the weakest of the four and is frequently misread as a headline. Indirect bidder share is the one that carries information about foreign demand specifically, and it is the series that connects this scenario to 11 and 21.

**What a firing does not mean:** a single tail reflects the auction's timing, its size, and what happened in the two hours before it. The signal is persistence with deteriorating indirect participation.

### Current state

**Loading.** 10-year at 4.72% and 30-year at 5.21% with guidance withdrawn, record issuance volumes, and a demand base whose largest foreign component is being actively managed through intervention and FIMA repo arrangements rather than behaving freely.

### Transmission

**Factor IV**, directly, and it is one of the pre-registered falsifiers in Disruptive Themes' What Would Change My Mind list: a genuine tail event in 10s or 30s with indirect share falling moves the score toward TOP SIGNAL. This is the rare tail scenario that is formally wired into the composite's own falsification criteria.

### Mutations

**Scope drift — the failure appears in the bill market instead.** Bill auctions are assumed to be trivially absorbed; that assumption depends on money funds and stablecoin issuers continuing to buy. A bill auction clearing poorly would be far more alarming than a bond auction clearing poorly, and no one is watching for it. *Instrument:* bill auction stop-out versus secondary levels. **Gap.**

**Substitution — the buyer strike is silent rather than visible.** Foreign demand can decline without a single bad auction, by simply reinvesting less at each maturity. This is scenario 11's mechanism and it produces no observable event at all, only a slow drift in indirect share and TIC data.

**Aliasing — with 1, 11, 19 and 21.** Falling indirect share could be Japanese repatriation, sovereign fund liquidation, a strategic reduction by a large official holder, or simple price sensitivity. The tripwire cannot distinguish them, and the report's language should not pretend otherwise.

**Re-specification trigger.** If a tail sequence occurs and the Treasury responds with issuance composition changes rather than the market clearing at higher yields, the scenario becomes a story about debt management under stress rather than about demand, and belongs inside Factor IV's Twist analysis rather than in the tail list.

### Report routing

**Primary: Monthly Macro**, which is the right cadence for auction statistics and term premium. **Secondary: Disruptive Themes**, where it is already a named falsifier. Auction tails and indirect share are published by Treasury and are not currently in any pipeline; both go to the build queue, and they are among the cheapest items on it.

---

## Scenario 2 · Yen carry unwind

**Tier A · daily**

### Mechanism

The yen is the world's funding currency: low domestic rates make it the cheapest liability with which to finance holdings of higher-yielding assets, and the resulting carry positions are enormous, diffuse, and largely unmeasured. Japan is simultaneously the largest foreign holder of US Treasuries. The unwind mechanism is a single loop: yen appreciation raises the cost of the funding leg, forcing position closure, which requires buying yen, which appreciates the yen further. Because the assets financed by the carry are global and heterogeneous, the liquidation is cross-asset and correlated by construction.

The trigger can be a faster-than-expected Bank of Japan normalization, a widening of Japanese yields that closes the carry's economics, or a *failed intervention* — the case where the authorities act and the market keeps going, which converts a policy floor into a proven ceiling.

### Precedent

**August 2024** is the recent live-fire test: a modest BoJ move and a soft US payroll print together produced a violent multi-day unwind, a Nikkei decline of over 12% in a session, and a global volatility spike that resolved within weeks. The episode calibrates the *speed* and *breadth* of this mechanism without telling us anything reliable about its ceiling. **1998** is the deeper precedent, when a yen move of roughly 15% in days contributed to LTCM's failure.

**Today's specific configuration:** the early-August coordinated intervention described in the *Foundations* paper — Japan selling European assets rather than Treasuries, with the Fed promoting FIMA repo — was explicitly designed to prevent the largest foreign holder from having to sell US paper. That the architecture was necessary is the evidence that this scenario is not dormant.

### Tripwire

*First mover: USD/JPY intramonth path divergence, JGB 30-year, cross-asset correlation spike.*

Path divergence rather than level: the scenario is about the *speed* of yen appreciation, not its destination. The JGB 30-year carries the carry's economics. A cross-asset correlation spike is the confirmation that an FX move has become a global deleveraging.

### Current state

**Armed, and actively managed.** Intervention held in early August; the structural pressure that made intervention necessary is unresolved.

### Transmission

**Factor IV** through the Treasury demand channel and **Factor II** through correlated liquidation. The scenario's band in the Disruptive Themes tail table is currently unchanged, with the note that intervention held while the structural pressure did not resolve.

### Mutations

**Scope drift — the funding currency changes.** Carry structures migrate to whichever currency offers the cheapest liability. Renminbi-funded carry and, at the margin, stablecoin-denominated leverage perform the same function with different plumbing and far worse disclosure. *Instrument:* none. **Gap.**

**Substitution — repatriation replaces unwind.** Scenario 11 is this scenario's slow twin, and the two are frequently conflated. The unwind is fast, leveraged, and reversible by intervention; the repatriation is slow, unleveraged, and not reversible by intervention. Distinguishing them in real time requires TIC data that arrives with a two-month lag.

**Aliasing — with 11 and 15.** A dollar squeeze in emerging markets and a yen unwind both present as correlated cross-asset liquidation with a strong dollar.

**Re-specification trigger.** A *failed* intervention would convert this scenario from a tail into a regime statement about the limits of official capacity, and would require re-scoping toward the broader question of coordinated intervention credibility.

### Report routing

**Primary: Daily Cascade**, where USD/JPY path and cross-asset correlation belong on the intraday clock. **Secondary: Alternative Asset Report**, whose Correlations tab is the natural home for the correlation-spike detection across its 18 assets. **Monthly Macro** carries JGB yields and the TIC context.

---

## Scenario 11 · Japanese repatriation from the domestic side

**Tier C · monthly**

### Mechanism

Distinct from the carry unwind in every operationally relevant way. Japanese life insurers and pension funds hold foreign bonds because domestic yields have been inadequate for a generation. If JGB yields rise far enough that domestic paper compensates on an *unhedged* basis — the hedging cost being the decisive variable, not the headline yield — the rational allocation is to bring the money home. This is not a leveraged position being liquidated. It is a strategic reallocation by unleveraged holders with long horizons, and it is therefore slow, persistent, and immune to intervention. Nobody can be talked out of it, because nothing is going wrong.

The consequence for Treasuries is a structural withdrawal of the largest foreign bid, arriving at maturity rather than through sales.

### Precedent

No clean instance, because the condition that would cause it — adequate domestic Japanese yields — has not existed since the 1990s. Partial analogs exist in periods when hedging costs made unhedged Treasuries unattractive for Japanese buyers, producing observable slowdowns in purchase flows.

### Tripwire

*First mover: Treasury International Capital data for Japan, JGB 30-year, hedged-yield spreads.*

Hedged-yield spreads are the actual decision variable and should be the primary. TIC data confirms with a lag of roughly two months, making it a confirmation instrument rather than an early warning.

### Current state

**Loading.** JGB long yields have been normalizing for several years; the hedged-yield calculus has been at or near the indifference point for domestic institutions repeatedly.

### Transmission

**Factor IV.** This is the scenario most likely to be mistaken for a benign environment while it is happening, because it produces no volatility, only a persistent absence of a buyer.

### Mutations

**Scope drift — the same logic applies to every major foreign holder.** European institutions face the same hedged-yield arithmetic. A generalized version is not "Japanese repatriation" but "the end of the global reach-for-yield bid," which would be a far larger scenario requiring its own scoping.

**Substitution — the seller is official rather than institutional.** Scenario 21's sovereign fund and central bank reserve managers execute the same withdrawal for different reasons, and both show up in the same TIC series.

**Aliasing — with 9 and 21**, and materially with 2, since a repatriation trend and a carry unwind can coexist and would be reported as a single "foreign selling" narrative.

**Re-specification trigger.** If TIC data confirms two consecutive quarters of net Japanese reduction, this ceases to be a tail and becomes a structural input to Factor IV's demand analysis.

### Report routing

**Primary: Monthly Macro**, correct cadence and the natural home for TIC and JGB series. Hedged-yield spreads are not currently computed anywhere in the system and go to the build queue; the calculation is straightforward from available inputs and would be one of the higher-value additions in this family.

---


## FAMILY B — CREDIT AND THE MANDATE MACHINE

## Scenario 6 · Private credit mark event

**Tier B · weekly**

### Mechanism

Private credit's structural vulnerability is a timing mismatch between three clocks. The loans are **floating rate**, so borrower interest costs reprice immediately with policy. The borrowers are the **most refinancing-exposed cohort in credit**: sponsor-backed, levered, and originated in a rate regime that no longer exists. But the **marks are quarterly**, model-driven, and set by the manager whose fee depends on them.

The result is that deterioration accumulates invisibly. Interest coverage compresses in real time; the reported value does not. The adjustment, when it comes, arrives as a step function rather than a drift, and it arrives simultaneously across a sector holding assets that were originated under similar assumptions by managers using similar models.

The tell that leads the marks is payment-in-kind income: a borrower that cannot pay cash interest is permitted to accrue it, which converts a liquidity problem into a reported-earnings improvement. Rising PIK share is a portfolio deteriorating while its income statement improves.

Business development companies are the crack in the wall. They hold similar assets, and their *shares* trade daily. A BDC trading at a persistent discount to net asset value is the public market stating that it does not believe the private mark.

### Precedent

No systemic instance, because the asset class at this scale is roughly fifteen years old and has not experienced a full default cycle. The closest analog is the pre-2008 experience with model-marked structured credit, where the gap between reported and transactable value closed abruptly once a forced seller established a print. The relevant lesson is not about credit quality; it is that **a mark is a claim, not a price, until someone has to sell.**

### Tripwire

*First mover: BDC price-to-net-asset-value, CCC spreads, payment-in-kind income share.*

BDC price-to-NAV is the primary because it is daily and public. A persistent, sector-wide discount is the signal; individual discounts are manager-specific. CCC spreads, currently near 855 basis points against BB, are the corroborating public-market read on the same borrower cohort. PIK share is the slowest and most diagnostic.

**What a firing does not mean:** BDC discounts widen for reasons unrelated to asset quality, including rate sensitivity and equity beta. The scenario requires the discount *plus* corroboration from CCC or PIK.

### Current state

**Loading.** The CCC−BB differential near 855 basis points is the credit market's own statement that the marginal borrower is distressed while the index is calm, which the *Foundations* paper identifies as Factor II's central dissent. Private credit is where a large share of that marginal borrower now lives.

### Transmission

**Factor II** directly, since the CCC dissent is one of Factor II's named indicators, and **Factor I** at the intersection where AI-adjacent lending has migrated into private credit books. The triple-confirmation falsifier in Disruptive Themes — CCC−BB, BDC discounts, and the unprofitable-small-cap spread widening together — is precisely this scenario's confirmation set.

### Mutations

**Scope drift — the mark problem migrates to interval funds and retail-distributed vehicles.** The fastest-growing distribution channel for private assets is now semi-liquid vehicles sold to individuals with periodic redemption windows. A redemption queue in a semi-liquid vehicle produces a forced seller, which produces a print, which resets the marks for everyone. This mutation converts a slow scenario into a fast one. *Instrument:* redemption gate and queue disclosures, which are public but scattered. **Gap.**

**Substitution — the stress appears in the bank channel instead.** Private credit's growth was partly a migration of assets off bank balance sheets, but banks retained exposure through subscription lines, fund financing, and NAV loans. The same borrower distress can therefore surface as a bank credit event with no private mark ever changing. *Instrument:* bank disclosures on fund finance exposure. **Gap.**

**Aliasing — with 24 and 14.** All three are credit events transmitted by mandate and marking conventions, and in a stress episode they would be narrated as a single credit cycle turning.

**Re-specification trigger.** The first large forced sale that establishes a transactable print for a broad private book converts this from a tail scenario into a repricing already underway, and the scenario should be rewritten around the *pace* of mark convergence rather than its possibility.

### Report routing

**Primary: Top & Bottom, HY Spread Acceleration overlay**, which already carries CCC dynamics and is the right structural home. **Secondary: Monthly Macro** for the spread series. BDC price-to-NAV and PIK share are not instrumented anywhere and go to the build queue; BDC discount data is publicly available and cheap to add, making it one of the highest value-per-effort items in the entire audit.

---

## Scenario 14 · Commercial real estate credit cascade

**Tier B · weekly**

### Mechanism

Three conditions compound. Regional banks hold a disproportionate share of commercial real estate exposure relative to their capital. A maturity wall of loans originated at low rates requires refinancing at current rates against properties whose income has not risen proportionally. And office valuations have not cleared, because transaction volume collapsed rather than prices adjusting, so the marks reflect an absence of trades rather than a market level.

The transmission is the important part and is frequently misdescribed. It does not run through property prices into the economy. It runs through **bank capital**: a wave of realized losses forces capital rebuilding, which forces lending contraction across every category the bank serves, most of it unrelated to real estate. The mechanism is a credit contraction in the small-business economy caused by an office building in a different city.

### Precedent

**The 1990–91 episode** is the direct template: a commercial real estate downturn transmitted through bank capital into a broad credit contraction, contributing to a recession whose proximate cause looked unrelated. **March 2023** demonstrated the modern speed of the deposit side of the same institutions, where the run occurred in hours rather than days.

**The disanalogy:** post-2008 capital requirements are materially higher, and the regional banking system has already absorbed one shock in 2023 with substantial regulatory attention since.

### Tripwire

*First mover: CMBS spreads by rating tier, regional bank options skew, bank CRE delinquencies.*

CMBS spreads **by tier** is the correct specification, because the distress is concentrated in specific vintages and property types, and an aggregate index will mask it. Regional bank options skew is the fastest of the three and is available through the FlashAlpha subscription. Delinquencies are the confirmation, and they lag by construction.

### Current state

**Loading.** The maturity wall is a calendar fact rather than a forecast, and the refinancing arithmetic worsens with every month that long yields stay near current levels.

### Transmission

**Factor II** through credit conditions and **Factor IV** through the possibility that a regional banking event forces a policy response inconsistent with the Fed's stated stance. The 2023 precedent is instructive: the facility created then was framed as financial stability and functioned as easing.

### Mutations

**Scope drift — the exposure is in the non-bank lender.** Debt funds, mortgage REITs, and insurance company allocations hold a growing share of the same assets with lower disclosure and, in several cases, leverage. *Instrument:* mortgage REIT price-to-book, partially available. **Partial gap.**

**Substitution — the asset class is data centers rather than offices.** This is the mutation most relevant to this framework. Data-center financing has grown rapidly, is frequently structured as asset-backed paper against long-term contracts with a concentrated set of tenants, and depends on the durability of the AI capex cycle in scenario 3. A buildout pause converts high-quality contracted infrastructure into a vacancy problem with the same maturity-wall arithmetic. *Instrument:* data-center ABS spreads. **Gap**, and a priority one, because it is the direct link between scenarios 3 and 14.

**Aliasing — with 6**, since both are private-market credit stress marked by convention, and with any regional banking event, which would be reported as a deposit story regardless of the asset cause.

**Re-specification trigger.** If data-center ABS becomes a larger share of the relevant maturity wall than office, the scenario should be renamed and re-scoped around infrastructure credit rather than commercial real estate.

### Report routing

**Primary: Monthly Macro**, weekly-to-monthly cadence in the credit pillar. **Secondary: Daily Cascade** for regional bank options skew from FlashAlpha data. CMBS tier spreads and data-center ABS spreads both go to the build queue.

---

## Scenario 5 · European sovereign fragmentation

**Tier B · weekly**

### Mechanism

Peripheral and semi-core spreads widen to the point where the ECB's willingness to intervene is tested. The euro area's structural problem is unchanged since 2012: a shared currency without a shared fiscal authority means sovereign spreads carry redenomination risk as well as credit risk, and the backstop is discretionary and politically constrained. France's inclusion in the relevant series reflects that this is no longer only a periphery question.

### Precedent

**2011–12**, resolved by verbal commitment rather than by purchases. **2018 Italy** and **2024–25 France** are lesser instances that repriced without escalating.

### Tripwire

*First mover: OAT–Bund and BTP–Bund spreads.* Persistent widening in OAT–Bund is the more informative of the two, because a semi-core widening tests the framework in a way a peripheral widening does not.

### Current state

**Dormant.** Mechanism intact, no elevated pressure evident.

### Transmission

**Factor IV** through global term premium, and the channel the source list identifies correctly: this is the only euro-area mechanism that reliably becomes a global event.

### Mutations

**Substitution — the stress appears in bank-sovereign linkage rather than in spreads.** European banks hold domestic sovereign debt in size; a spread event and a bank event are the same event viewed from two sides.

**Scope drift — the defense-spending path is the new fiscal variable.** European rearmament changes the debt trajectories that spreads price, and does so in a direction and at a speed that the 2012-era framework did not contemplate.

**Aliasing — with 15**, since both present as sovereign credit stress under a strong dollar.

**Re-specification trigger.** An actual ECB intervention under the current framework would answer the question the scenario poses, and the tail would need rewriting around what remains untested after that answer.

### Report routing

**Primary: Monthly Macro**, rates pillar. Both spread series are available and low-cost additions.

---


## FAMILY C — CONCENTRATION AND THE BUILDOUT

## Scenario 3 · AI capex halt

**Tier B · weekly**

### Mechanism

**One hyperscaler cutting capital expenditure guidance is sufficient.** That is the scenario's entire thesis, and the reason it is sufficient is circularity.

In a normally structured supply chain, one customer reducing orders costs the supplier that customer's revenue. In the current structure it does considerably more, because the buildout's financing has become reflexive at four separate joints. The supplier takes equity stakes in and lends to its customers, so a customer's distress is also a mark on the supplier's balance sheet. Forward purchase commitments — roughly $530 billion against about $96 billion of quarterly sales — mean the supplier has pre-committed capacity spending against orders that assume the cycle continues. Neocloud borrowers financed their fleets against contracted revenue from a small set of counterparties, so one cut reprices their debt. And data-center asset-backed paper, power purchase agreements, and construction financing are all underwritten against the same demand assumption.

A single guidance cut therefore propagates simultaneously through chip orders, neocloud debt, data-center ABS, power contracts, and the supplier's own receivables, which stand at $63 billion with roughly 70% owed by five customers and 64% growth in six months. The mechanism is not "demand falls." It is **"one decision reprices five markets at once, because they were all underwritten against the same sentence."**

The second-order mechanism is the bullwhip. Because scarcity produced double-ordering, the observed order book overstates true end demand by an unknown margin. A modest genuine slowdown therefore produces an outsized cancellation wave, which is what the 2021–22 GPU cycle demonstrated: two to three quarters from commitment peak to revenue miss.

### Precedent

**2021–22 in the same complex** is the direct template and is discussed at length in the *Foundations* paper: crypto-driven scarcity, double-ordering, an air pocket, channel inventory, a revenue miss, and a roughly 60% drawdown in the supplier's equity against an end market that remained healthy.

**Lucent and Nortel, 1999–2002**, are the vendor-financing precedent and the darker one. Both booked revenue on sales financed with their own capital to thinly capitalized customers. When the customers failed, the receivables and the recognized revenue vanished together. The structural feature that made it fatal was not the credit loss; it was that **the income statement could not distinguish financed demand from earned demand until the financing stopped.**

**The disanalogy that the bull case rests on:** deferred revenue tripled to $6.4 billion including $2.8 billion of customer advances. Prepayment runs in the direction circular financing cannot fake. Today's supplier is enormously cash-generative, and its forward earnings have tracked and at times led its price. Cisco in 2000 was a multiple story; this is not, yet.

### Tripwire

*First mover: supplier inventory and forward purchase commitments, hyperscaler capex as a share of operating cash flow, Korean semiconductor export data.*

**Forward purchase commitments as a ratio to revenue** is the primary and is the single best early-warning line in the entire framework. Its 2021–22 trace is the template; two consecutive declining quarters *with stable margins* is the benign reading, which is why margin must be read alongside it.

**Inventory**, currently up 48% since January, distinguishes strategic buffer from involuntary accumulation only when read against margins and against the commitment ratio.

**Hyperscaler capex as a share of operating cash flow** is the discipline gauge: capex funded from cash flow is a strategic choice, capex funded from debt at a rising share is a commitment that becomes hard to reverse and harder to sustain.

**Korean semiconductor exports**, particularly the 20-day series, are the most valuable instrument in the set because they sit *outside* the reflexive American financing loop. Foreign, mandatory, high-frequency, and unspinnable.

**What a firing does not mean:** a single quarter of commitment decline is digestion, not a halt. The scenario requires the ratio to decline *while* margins compress, or a guidance cut from a top-five spender.

### Current state

**Loading, with the strongest counter-evidence of any scenario on the list.** Every input above is at or near an extreme, and the demand ledger simultaneously argues the boom is real: $96.2 billion in quarterly revenue at 106% growth, guidance of $108 billion, and prepayments rising. The correct reading is the one Disruptive Themes gives Factor I: level positive, derivative negative.

### Transmission

**Factor I** at the source, **Factor II** through the concentration channel, since the ten names that would reprice are the index's premium, and **Factor IV** through the disappearance of AI-related issuance from the credit calendar and, more consequentially, through the removal of the productivity story that is the debt arithmetic's only painless exit.

### Mutations

**Scope drift — the halt is a *deceleration in growth rate*, not a cut.** The scenario as scoped waits for a guidance cut, which is a discrete and highly visible event that management teams have every incentive to avoid. The realistic version is capex growth decelerating from 40% to 10% across three quarters with no announcement at all, which produces the same effect on suppliers and neoclouds while never firing a tripwire built around cuts. *Instrument:* second derivative of aggregate capex guidance across the top five. **Gap**, and the most important single addition this scenario needs.

**Substitution — the constraint is power, not capital.** The buildout can halt because electricity cannot be delivered on schedule, with no financial decision involved. Interconnection queues, transformer lead times, and turbine availability would produce a capex *deferral* that looks operational rather than financial and would be reported as a delay rather than a cut. *Instrument:* interconnection queue data and utility capex commentary. **Gap.**

**Substitution — the failure is a financed customer, not a hyperscaler.** A neocloud or a leveraged lab defaulting produces the credit-event variant: receivables written down, vendor financing repriced as counterparty risk, contagion through AI-adjacent debt. This is faster and gappier than the demand-side version and lands on scenario 14's data-center ABS mutation. *Instrument:* neocloud debt spreads. **Gap.**

**Aliasing — with 20 and 14.** An AI capex halt, an index concentration accident, and a data-center credit cascade would be a single narrative in the press within a week.

**Re-specification trigger.** If the commitment ratio declines two consecutive quarters with margins stable, the benign falsifier has fired and the scenario should be re-scoped from "halt" to "digestion pace," moving from tail list to Factor I's standing analysis.

### Report routing

**Primary: Disruptive Themes, Factor I**, where the commitment ratio, inventory, receivables, and margin lines already live. **Secondary: Monthly Macro** for the Korean export series, which is available and belongs in the trade or industrial pillar. **Tertiary: Daily Cascade**, which already tracks the complex's equities intraday and would carry the first evidence of a repricing. Hyperscaler capex-to-cash-flow and the capex second derivative go to the build queue; the second derivative is the highest-priority instrumentation gap in this family.

---

## Scenario 20 · Index concentration accident

**Tier A · daily**

### Mechanism

Purely mechanical, with no fundamental content required. As the top-ten weight in the index rises, the arithmetic of a single-name failure changes character: at 15% combined weight, a 30% decline in one large constituent is a sector story; at current concentrations it is an index event. The amplifier is passive ownership. **Index funds must sell proportionally regardless of view**, so a decline in a large constituent generates mechanical selling in that constituent from every fund tracking the index, with no valuation judgment available to arrest it.

The second amplifier is options structure. Single-name gamma on the largest constituents has grown to the point where dealer hedging flows in one name can move the index, and the relationship is reflexive: as dealers hedge short gamma into a decline, they sell into weakness, which extends the decline.

The scenario does not require the large constituent to be *wrong*. It requires it to move.

### Precedent

**October 1987** is the pure case: no recession, no credit event, an extended market plus a mechanical seller (portfolio insurance) producing a 22% single-day decline. **August 2024** is the modern miniature: a concentrated unwind amplified by positioning, resolved in weeks. **2000–02** provides the concentration-unwind template with fundamentals attached.

**The disanalogy:** 1987's mechanical seller was a strategy sold to a subset of institutions. Today's mechanical seller is the *ownership structure of the market itself*, which is both larger and more predictable in behavior.

### Tripwire

*First mover: single-name gamma on the largest constituents, top-ten weight, implied correlation.*

Single-name gamma is available through the FlashAlpha subscription and is the fast instrument. Top-ten weight is the slow structural context. **Implied correlation** is the most diagnostic of the three: rising implied correlation means the market is pricing the constituents as one asset, which is the precondition for the accident.

### Current state

**Armed.** Top-ten weight near historic highs, equal-weight at 19.8x against cap-weight at 25.5x locating the entire premium in those names, and an earnings yield below the risk-free rate at the index level.

### Transmission

**Factor II** directly, and it is the mechanism by which Factor I's problems become index problems. Disruptive Themes' Concentration & Complacency framing in the Top & Bottom overlay is the same analysis in a different report.

### Mutations

**Scope drift — the accident is in a sector ETF or a thematic wrapper rather than the index.** Concentrated thematic products hold overlapping constituents at higher weights with less liquidity, and their forced flows hit the same names. *Instrument:* thematic ETF flows and holdings overlap. **Gap.**

**Substitution — the mechanical seller is a leveraged retail structure.** Single-stock leveraged ETFs and covered-call funds on individual mega-caps have grown substantially. They rebalance daily and mechanically, in the direction of the move. This is portfolio insurance rebuilt, with a ticker. *Instrument:* AUM and daily rebalancing requirements of single-stock leveraged products. **Gap**, and a genuinely under-watched one.

**Aliasing — with 3, and with any single-name event.** The framework will not be able to distinguish a concentration accident from the fundamental event that triggered it, and should not try in real time.

**Re-specification trigger.** If implied correlation reaches a level at which the index trades as a single asset for a sustained period, the scenario stops being about an accident and becomes a description of market structure, belonging in Factor II's standing analysis.

### Report routing

**Primary: Top & Bottom, Concentration & Complacency overlay**, which exists for exactly this and is the correct structural home. **Secondary: Daily Cascade**, using FlashAlpha's dealer-positioning and gamma data on the intraday clock. Implied correlation and single-stock leveraged product AUM go to the build queue.

---


## FAMILY D — PHYSICAL SHOCKS AND GEOPOLITICS

## Scenario 7 · Chokepoint disruption–price divergence resolves

**Tier A · daily · re-specified**

### Mechanism

This scenario is the source list's own worked example of re-specification, and the reason principle 6 exists. It was originally scoped as **closure risk**: the tail was that a chokepoint would shut. The chokepoint shut. Holding the original scoping would have meant carrying a tail scenario that had already occurred, which is the exact failure that Disruptive Themes' premise fields were later built to prevent.

The re-specified scenario is the **divergence**, and it is more interesting than the original. Physical disruption sits at crisis extremes — Hormuz effectively closed roughly 181 days, three transits counted on August 23 against an 85-per-day baseline, Gulf exports down some 47%, war-risk premiums near 10% of hull value against 0.05% pre-war, a 200-fold repricing by the market that pays claims. Brent sits near $89.

Two readings explain that, with opposite implications. **Adaptation:** shadow fleets, rerouting, inventory draws, strategic reserve releases, and demand destruction have genuinely absorbed the disruption, and the price is correct. **Mispricing:** finite buffers are papering over an unresolved physical problem, underwritten at normal premiums, and the gap will close violently.

**The tail is the divergence closing from the price side.** Not the closure, which has happened, and not the adaptation, which would be benign. The tail is a $30–60 move in crude arriving into an economy that has already banked the disinflation.

### Precedent

**1973** is the case where price closed every divergence violently. **The Tanker War, 1984–88**, is the case where it did not: four years of attacks on over 400 vessels, premiums elevated throughout, traffic never stopping, and oil falling through most of the period. **Abqaiq 2019** is the modern reversion reflex: 5% of world supply removed, a 15% spike, round-tripped within weeks.

The honest summary of the precedent set is that it splits, which is why the source list gives the scenario two readings rather than a direction.

### Tripwire

*First mover: transit counts as a ratio to pre-crisis baseline, against crude.*

The instrument is explicitly a **ratio against a price**, which is the correct construction: neither series alone carries the information. The supporting instrument, and arguably the better one, is the war-risk premium, because an insurance rate is a probability-times-severity estimate made by people paying claims, while a crude price is a probability estimate made by people who can also be positioned.

**What a firing does not mean:** the divergence widening further is not confirmation of mispricing. It is equally consistent with adaptation succeeding. The instrument's honest property is that it measures the *size of the disagreement*, not who is right.

### Current state

**Armed, at the widest reading the construction can produce.** Disruptive Themes carries a standing decision rule: divergence persisting two more quarters resolves in favor of adaptation, with the date recorded in advance.

### Transmission

**Factor III** directly. If the divergence closes via price, the disinflation path inverts and the Fed's easing option disappears, which lands on **Factor IV** and connects to scenario 16. If it closes via adaptation, Factor III de-escalates in writing and the chokepoint weight is cut.

### Mutations

**Scope drift — the divergence construction applies to every chokepoint, not just this one.** The same physical-versus-priced gap can be built for Bab el-Mandeb, the Panama Canal, the Taiwan Strait, and for non-maritime chokepoints such as critical-mineral licensing. A generalized divergence index across chokepoints would be a considerably more powerful instrument than the single-strait version. *Instrument:* a composite requiring transit and premium data by chokepoint. **Gap**, and a high-value one.

**Substitution — the closure moves from oil to a non-substitutable good.** Crude has reserves, substitutes, and demand elasticity, which is why adaptation is possible. Fertilizer, refined products, and above all semiconductors do not. The same physical disruption in a non-substitutable good produces no divergence at all, because the price closes immediately. *Instrument:* the nitrogen complex, Tampa ammonia and NOLA urea, already named in Factor III. **Partial gap** — the series are identified but unfetched.

**Aliasing — with 8 and 17.** A chokepoint event, a Taiwan event, and a catastrophe-driven insurance event all present initially as a shipping and insurance repricing.

**Re-specification trigger.** Already fired once. The next one: if the two-quarter rule resolves for adaptation, the scenario should be re-scoped again, from divergence to **precedent risk** — the question of what the demonstrated survivability of a closed chokepoint does to the price of the next closure elsewhere. That mutation is the direct bridge to scenario 8 and is developed in the *Foundations* paper's revised Chapter 3.

### Report routing

**Primary: Disruptive Themes, Factor III**, which carries the divergence as a named indicator and ties the score to its resolution. **Secondary: Daily Cascade** for the crude leg. PortWatch transit data and war-risk quotations are both identified and neither is automated; both go to the build queue under the S3c line already named in the Disruptive Themes gaps register.

---

## Scenario 8 · Taiwan

**Tier D · quarterly**

### Mechanism

The source list's description is four words longer than it needs to be: *low probability, near-unbounded impact*. The mechanism is that a Taiwan contingency removes the semiconductor supply chain and the artificial intelligence trade simultaneously, and adds the shipping and insurance consequences of a regional conflict on top.

What makes this categorically different from every other item on the list is **irreplaceability**. Roughly nine-tenths of leading-edge logic is fabricated on one island, along with the advanced packaging that converts wafers into accelerators. Oil has substitutes, routes, reserves, and elastic demand, which is why scenario 7 has an adaptation branch. Leading-edge silicon has none on any relevant timescale: a fab is a three-to-five-year, multi-tens-of-billions project, and the onshoring underway in Arizona, Kumamoto and Dresden will not relocate the center of gravity before the early 2030s.

The escalation ladder matters more than the binary. Sustained gray-zone pressure, then **customs quarantine**, then blockade, then strike campaign, then invasion. The quarantine rung is the most likely and the least modeled: coast-guard-led rather than navy-led, framed as law enforcement rather than war, reversible, deniable, and specifically engineered to place the escalation decision on Washington's desk. Public analysis concentrates on invasion because it is dramatic and militarily difficult. The cheap option is the one that gets chosen.

### Precedent

**The Taiwan Strait crises of 1954–55, 1958 and 1995–96** all de-escalated, and the base rate they establish is the most misleading number in this paper. Each de-escalated because the local balance of forces made testing it unattractive and because, in 1996, the American answer — sail two carrier groups through the strait — was available at acceptable risk. That specific answer is no longer available at the same risk. A base rate computed from a period whose decisive variable has since changed is not a base rate.

**1914** is the standing rebuke to the interdependence argument. **The Cuban missile crisis** supplies the market's structural blind spot: equities fell roughly 3% and recovered within weeks, because there is no hedge that pays in the tail of an existential binary, so the tail is not priced.

### Tripwire

*First mover: Taiwan export orders, foundry revenue, semiconductor equities, shipping and war-risk insurance rates.*

The cadence question is the instructive one. This is the highest-impact scenario on the list and it is checked quarterly, because these series update monthly to quarterly. Checking daily would be theatre.

**War-risk insurance rates for Taiwan Strait transits are the best instrument in the set**, and they are portable from scenario 7: the same capital-backed sensor that repriced Hormuz by 200x would reprice the strait before any government said anything. Taiwan export orders and foundry revenue are the economic thermometers. Semiconductor equities are the fastest and the least informative, because they reflect the AI cycle far more than the strait.

**Additional instruments not in the source list, recommended:** PLA exercise *duration and sustainment* rather than sortie counts, which distinguishes demonstration from rehearsal; customs and coast-guard inspection precedents against individual vessels, which is the quarantine rung's leading edge; fab qualification milestones outside Taiwan, which is the only variable that reduces the exposure; and Chinese strategic reserve builds in grain and crude, since pre-positioning is visible in inventories long before it is visible in policy.

### Current state

**Dormant as an event, loading as a structure.** No market-transmitting escalation. The structural drivers — capability trajectory, the semiconductor concentration, and the precedent supplied by six months of a closed Hormuz with no decisive cost imposed on the party that closed it — all move in one direction.

### Transmission

**All five factors on the same day**, which no other scenario on this list can claim. Factor I at its physical substrate; Factor II through the concentration channel, since the ten names largely *are* the semiconductor complex; Factor III as the chokepoint case that has no adaptation branch; Factor IV through a simultaneous fiscal and defense shock into a record interest burden; Factor V through a reserve-weaponization question applied to the second-largest holder of Treasuries, whose response options include the one thing Factor IV cannot absorb.

### Mutations

**Scope drift — the event is economic rather than military.** Export controls, entity listings, or a mineral-licensing cutoff can remove a large share of the same value without a single ship moving. This mutation is already partly realized, and it is the reason the *Foundations* paper's revised Chapter 3 argues the geoeconomic half of the factor is the near-certain path while the military half is the tail. *Instrument:* export license issuance, entity list additions, effective tariff rates. **Gap.**

**Substitution — the chokepoint is the undersea cable, not the strait.** Taiwan's connectivity runs through a small number of cables that have already proven cuttable, and a connectivity interruption produces financial and operational disruption with full deniability. *Instrument:* cable incident reporting. **Gap.**

**Aliasing — with 18 and 13** in the first hours if the opening move is cyber or infrastructure rather than kinetic, and with 3 and 20 in market terms, since the immediate tape would be a semiconductor and index event.

**Re-specification trigger.** A customs quarantine, even a brief one conducted as an exercise, converts this scenario from a tail into a current condition with a named mechanism, and the tail slot would need re-scoping toward escalation beyond quarantine.

### Report routing

**Primary: Disruptive Themes**, where the *Foundations* paper's revised Chapter 3 now carries the theater analysis, the escalation ladder, and the decade probabilities. **Secondary: Monthly Macro, Tail Scan section**, which is the correct quarterly home. Taiwan export orders, foundry revenue, war-risk quotations, and PLA activity data are all uninstrumented and go to the build queue. Semiconductor equities are already visible through the Daily Cascade.

---

## Scenario 12 · China property or LGFV event

**Tier C · monthly**

### Mechanism

Three transmission channels from one event, which is what earns it a slot. A property or local-government financing vehicle credit event in China **exports deflation** through goods prices, as excess capacity is dumped into export markets at falling prices. It **applies currency pressure**, since the policy response involves easing into capital-flight risk. And it delivers a **commodity demand shock**, because construction is the marginal buyer of industrial metals.

The three channels point in different directions for different assets, which is why the scenario is frequently misread as unambiguously deflationary. Goods deflation and a commodity demand shock are disinflationary for the US; a materially weaker renminbi is disinflationary for goods and destabilizing for everything else.

### Precedent

**2015–16** is the direct instance: a currency adjustment and a growth scare that transmitted globally through commodities and risk sentiment. **2021 onward** is the slow-burn version already underway in the property sector, which has so far been managed rather than resolved.

### Tripwire

*First mover: renminbi, copper-to-gold ratio, Chinese export prices.*

The copper-to-gold ratio is the elegant instrument here, since it nets the growth signal against the debasement signal in a single line. Chinese export prices are the deflation-export instrument and the most directly relevant to US inflation.

### Current state

**Loading.** The property adjustment continues without resolution; the policy stance manages rather than repairs.

### Transmission

**Factor IV** through the inflation path, in the disinflationary direction, which makes this the rare scenario that would *relieve* pressure on one factor while creating it elsewhere. **Factor I** through the demand channel for the buildout's inputs, and **Factor V** through reserve and gold behavior.

### Mutations

**Scope drift — the event is a policy choice rather than an accident.** A deliberate devaluation as a response to tariffs would produce the same transmission with none of the credit-event signature.

**Substitution — the deflation arrives through the AI supply chain.** Chinese overcapacity in solar, batteries, EVs and increasingly in commodity semiconductors exports price declines that read as disinflation in US data while destroying margin in specific sectors.

**Aliasing — with 15**, since a China event and an emerging-market dollar squeeze share the strong-dollar signature.

**Re-specification trigger.** A disorderly renminbi move of sufficient size would convert this from a credit scenario into a currency-regime scenario requiring its own scoping.

### Report routing

**Primary: Monthly Macro**, global pillar. **Secondary: Alternative Asset Report**, whose Correlations tab would carry copper-gold and the commodity complex.

---

## Scenario 17 · Insurance or reinsurance capital event

**Tier C · monthly**

### Mechanism

A very large catastrophe, or several correlated ones in a single season, forces insurers and reinsurers to fund claims. Claims are paid in cash; general accounts hold long-duration corporate and structured credit. The result is a large, price-insensitive seller of credit arriving in a market that may already be under stress, for reasons entirely unrelated to credit fundamentals.

The under-appreciated feature is scale: **insurance capital is a significant and under-monitored holder of corporate and structured credit**, and its selling is driven by loss experience rather than by any view on the assets. This is the same structural property that defines Family G, which is why the scenario is arguably misfiled in the source list's tiering, though correctly placed by cadence.

The compounding condition is a hard market that follows: capital destroyed by losses raises the price of risk transfer, which constrains capacity across the economy at the same moment credit conditions tighten.

### Precedent

**2005 (Katrina, Rita, Wilma)** and **2017 (Harvey, Irma, Maria)** are the capital-event templates, both followed by hard markets. **2022 (Ian)** compounded losses with a bond portfolio already marked down by rate increases, which is the modern configuration: the asset side and the liability side deteriorating together.

### Tripwire

*First mover: catastrophe bond spreads, reinsurer equity, January renewal pricing.*

Cat bond spreads are the market-priced view of the tail. Reinsurer equity is fast and noisy. January renewal pricing is the definitive read on whether capital was actually destroyed, and it arrives once a year.

### Current state

**Dormant, seasonally loading.** The scenario has an explicit calendar: Atlantic season risk concentrates in the third quarter and resolves at January renewals.

### Transmission

**Factor II** through credit conditions and **Factor IV** if the selling lands in a market with impaired dealer capacity. The link to scenario 1 is direct: a forced seller of credit into a balance-sheet-constrained market is how a natural disaster becomes a funding event.

### Mutations

**Scope drift — the correlated event is not weather.** Wildfire, earthquake, and increasingly cyber losses aggregate in ways the catastrophe models handle poorly. Cyber in particular has correlated-loss properties that natural catastrophe does not, since a single vulnerability can trigger simultaneous claims across an entire book with no geographic limit.

**Substitution — the capital event happens in life and annuity rather than P&C.** Rate-driven surrender activity in annuity books forces asset sales with the same mechanics and a completely different trigger, and this cohort holds substantially more long-duration credit than the property side.

**Aliasing — with 19**, since an insurer selling duration under stress is an LDI event by another name, and with 6 if the sales occur in private credit allocations.

**Re-specification trigger.** If cyber becomes a material share of aggregated catastrophe exposure, the scenario should be re-scoped to sit alongside 13 rather than as a weather-driven event.

### Report routing

**Primary: Monthly Macro, Tail Scan**, which already covers the relevant risk domains and is the correct cadence. Cat bond spreads and renewal pricing are uninstrumented and go to the build queue. This is the scenario where the framework's own professional expertise most exceeds its instrumentation, which makes it a natural early build.

---


## FAMILY E — POLICY LEGITIMACY AND THE INFLATION PATH

## Scenario 16 · Inflation reacceleration forcing hikes

**Tier C · monthly**

### Mechanism

Three inputs combine, none of which requires an economic boom. **Tariff pass-through** raises goods prices with a lag that depends on inventory cycles and margin absorption. **An energy floor** arrives through the physical channel of scenario 7, and — the piece most dashboards structurally cannot see — through the fertilizer chain, where gas to ammonia to urea to planting economics to harvest to food CPI runs on a two-to-three-quarter lag. **Services stickiness** persists because shelter and wage-driven components adjust slowly and asymmetrically.

The mechanism's danger is not the level of inflation. It is the **conditional structure of every portfolio and every policy framework built on the assumption of a disinflation path**. If inflation re-accelerates, the Fed's option to ease disappears exactly when the rest of the system needs it: equity multiples lose the discount-rate support that justifies them, the fiscal arithmetic in Factor IV loses the nominal-growth cushion it depends on, and the stock-bond correlation stays positive, which means the hedge fails at the moment it is needed.

The source list flags this as **the scenario most frameworks are least positioned for**, and adds the correct reason: contemporary analysis is generally built on an assumed disinflation path, which makes the asymmetry itself a reason to weight it. That is a statement about *crowding of assumptions*, not about probability, and it is the sharpest single line in the source document.

### Precedent

**1966–1982** is the multi-wave template, and its central lesson is that the second and third waves were larger than the first because credibility had been spent. **1974** is the supply-shock-into-extended-market case that the *Foundations* paper identifies as the closest historical rhyme to the current factor configuration. **2021–22** is the recent instance of the assumption failing: almost no participant pre-specified what data, by what date, would count as being wrong about transitory, so nobody was.

### Tripwire

*First mover: sticky core CPI, five-year five-year forward inflation, policy path dispersion.*

Sticky core is the correct primary because it filters the volatile components that produce false signals in both directions. Five-year five-year forwards measure whether expectations are becoming unanchored, which is the variable that separates an inflation *episode* from an inflation *regime*. **Policy path dispersion** is the subtlest of the three and the most useful in the current environment: with forward guidance withdrawn on principle, dispersion widens mechanically, which means it must be read against a baseline rather than in levels.

**What a firing does not mean:** a single hot print in a guidance-free regime moves market-implied paths violently and reverses just as fast. September hike odds moved from 35% to 57% on one speech. The signal is a *sequence* of sticky-core prints with forwards rising alongside.

### Current state

**Loading, with the fuse visibly lit.** July CPI at 3.4% year over year with core at 2.5%; May PPI at 6.5%, a four-year high; energy down 1.5% on the month but up 14.7% year over year; September hike odds at 57% after Jackson Hole; a July FOMC that held 9–3 with three dissents *for* a hike; and June dots penciling an increase. The fertilizer chain's food-CPI echo of this summer's disruption is scheduled for the winter prints, arriving after the consensus that the shock is absorbed has hardened.

### Transmission

**Factor IV** primarily, and it is explicitly named there as the path the framework is least positioned for. **Factor II** through the multiple, since every basis point of policy path subtracts from the justified multiple at a starting equity risk premium already near negative 80 basis points. **Factor III** as the origin of the energy and food components.

### Mutations

**Scope drift — the reacceleration is in food rather than energy or services.** Food CPI has different political properties than any other component: it transmits into social stability with the longest lag and the least market anticipation, and it is the component least amenable to policy response. *Instrument:* the nitrogen complex named in Factor III. **Partial gap.**

**Substitution — the inflation is structural rather than cyclical, and monetary policy cannot address it.** Fragmentation, duplicated supply chains, friend-shored capacity, tariffs and defense spending raise the cost of producing the same output. A supply-side inflation floor does not respond to demand suppression except by breaking the economy, which converts the scenario from a policy question into a political one. *Instrument:* effective tariff rate, trade-weighted input costs. **Gap.**

**Substitution — the hikes are not the Fed's.** A foreign central bank, particularly the Bank of Japan, tightening faster than expected produces global rate transmission with no domestic decision, and aliases directly with scenario 2.

**Aliasing — with 10.** A hiking Fed and a Fed whose independence is in question produce opposite signatures at the front end and can produce similar ones at the long end, since both raise term premium. The distinguishing series is breakevens versus term premium, which is scenario 10's instrument.

**Re-specification trigger.** If a hike is delivered and followed by a second, the scenario ceases to be a tail and becomes the base case, requiring re-scoping toward the *depth* of the tightening cycle and the point at which something in Families A or B breaks.

### Report routing

**Primary: Monthly Macro**, inflation pillar, correct cadence, all three series available from FRED. **Secondary: Disruptive Themes, Factor IV**, which already names this as scenario 16 and carries the asymmetry argument. **Tertiary: Daily Cascade** for policy-path repricing on CPI days and Fed speeches. Policy path dispersion needs an explicit construction rather than a level reading and goes to the build queue as the S3b policy-path item already named in Disruptive Themes' gaps register.

---

## Scenario 10 · Fed independence event

**Tier C · monthly**

### Mechanism

Appointments, sustained political pressure, or a policy decision that markets read as politically rather than economically driven. The scenario's distinctive property is *where it prices*. The front end reflects expected policy, so a Fed under political pressure to ease would show lower front-end rates, which looks benign. The long end reflects **trust in the institution setting policy**, and so does the currency, and so does gold's speculative bid. An independence event therefore shows up as a curve steepening driven by term premium, a weaker dollar, and a stronger gold bid, all while the front end is doing what politics wanted.

That signature — front end down, term premium up, currency down, gold up — is the specific fingerprint that distinguishes this scenario from ordinary easing.

### Precedent

**1972** is the classic instance, with monetary accommodation ahead of an election contributing to the inflation of the following decade. **1951** is the resolution precedent: the Treasury–Fed Accord ended a period in which the Treasury effectively set monetary policy, and it stands as the institutional wall that the fiscal-dominance mechanics of Factor IV would breach from the other direction. **Turkey, repeatedly**, is the modern demonstration of the full sequence.

**The current configuration is genuinely ambiguous**, which the *Foundations* paper develops as the Warsh A/B question: an orthodox hawk executing regime change on the Fed's own terms, versus hawkish rhetoric providing cover while the institution accommodates the fiscal need. Both theses predict identical *rhetoric*. Only the realized mean path separates them.

### Tripwire

*First mover: breakevens versus term premium divergence, dollar, gold's speculative bid.*

The divergence construction is the important part: breakevens rising *with* term premium is an inflation story; term premium rising *without* breakevens is an institutional-credibility story. Gold's speculative bid — the paper leg of the two-bid decomposition, currently at roughly 2.4 million net call-minus-put open interest against a 0.8 million mean — is already elevated, which makes it a poor discriminator at present and a good one if physical joins it.

### Current state

**Loading.** A chairman whose committee dissented 9–3 in July, guidance withdrawn on principle, a Treasury conducting maturity operations with a floated central-bank-account funding source, and a coordinated intervention in early August. None of that is an independence event. All of it raises the variance of how the next one would be read.

### Transmission

**Factor IV**, and it is the scenario that would most directly validate the fiscal-dominance thesis. **Factor V** through the debasement rails, since an independence event is the cleanest possible confirmation for the official gold bid.

### Mutations

**Scope drift — the erosion is procedural rather than an event.** Independence can be lost through the appointment cycle, the composition of the board, and the gradual normalization of Treasury operations that create reserves, with no identifiable event to price. This is the more likely form and the harder one to instrument. *Instrument:* the TGA-versus-reserves series named in Factor IV, which is the closest available proxy.

**Substitution — the institution under pressure is a foreign one.** The same signature in another major central bank transmits globally through term premium and currency.

**Aliasing — with 16 and 4.** Rising term premium with a weaker dollar has several possible causes, and the framework should say so rather than attribute.

**Re-specification trigger.** If a TGA-funded buyback is confirmed at scale — TGA down and reserves up together — the scenario has partially realized through the procedural mutation rather than the event, and should be re-scoped accordingly. This condition is already a pre-registered falsifier in Disruptive Themes.

### Report routing

**Primary: Disruptive Themes, Factor IV**, where the Warsh A/B separator and the TGA-versus-reserves series already live. **Secondary: Monthly Macro** for breakevens and term premium. **Tertiary: Alternative Asset Report** for gold's bid decomposition, which is its natural home given the 18-asset coverage.

---

## Scenario 15 · Emerging market debt crisis with a dollar squeeze

**Tier C · monthly**

### Mechanism

Dollar strength combined with refinancing walls in frontier sovereigns. Dollar-denominated debt becomes more expensive to service in local-currency terms exactly as refinancing comes due; cross-currency funding markets tighten; the IMF-programme wave is the slow-burn version, and a disorderly version compounds through the same funding channels that Family A instruments.

### Precedent

**1997–98** for the full sequence, **2018** and **2022** for the contained versions. The consistent pattern is that contagion runs through *funding* channels rather than through trade linkages.

### Tripwire

*First mover: EM sovereign spreads, dollar path, cross-currency basis.* Cross-currency basis is the instrument that connects this scenario to Family A, and it is the one that would fire first in a disorderly version.

### Current state

**Dormant.** Mechanism intact, no acute pressure.

### Transmission

**Factor IV** through dollar dynamics and funding channels; secondary transmission to **Factor II** through credit sentiment.

### Mutations

**Scope drift — the borrower is a corporate rather than a sovereign.** EM corporate dollar debt exceeds sovereign in several major markets and has weaker disclosure.

**Substitution — the squeeze is relieved by a non-dollar channel.** Renminbi swap lines and, increasingly, stablecoin-denominated dollar access change the transmission in ways that have not been tested in a stress episode. This mutation connects directly to Family G's scenario 23: if dollar access for frontier borrowers has migrated partly to token rails, then a regulatory reversal in those rails is an EM funding event.

**Aliasing — with 2 and 12.**

**Re-specification trigger.** A cluster of three or more IMF programmes in a single quarter converts this from tail to current condition.

### Report routing

**Primary: Monthly Macro**, global pillar. Cross-currency basis is not currently instrumented and goes to the build queue, where it earns priority for being shared with scenarios 1 and 2.

---


## FAMILY F — SETTLEMENT AND MONEY ARCHITECTURE

## Scenario 4 · Stablecoin depeg at scale

**Tier B · weekly**

### Mechanism

**No longer a crypto event**, and the reason is statutory and fiscal rather than technological. Issuers hold Treasury bill reserves as a matter of law, which makes stablecoin growth mechanical bill demand. Official financing plans increasingly count on that demand to absorb bill issuance, which makes the issuers **load-bearing** in sovereign finance. A private payment instrument has become part of the government's funding plan.

The failure sequence: a reserve loss, a custody failure, an operational incident, or simply a large redemption wave breaks the peg. Redemption demand forces the issuer to liquidate bills. The liquidation arrives in a bill market where reserves stand near $2.94 trillion with the RRP buffer exhausted, so the sale lands in a system with no shock absorber. A payment-instrument problem becomes a Treasury-market problem inside a settlement day.

The property that makes this faster than its closest precedent: **redemption at chain speed**. A money-market fund redemption takes a day. A token redemption takes a block.

### Precedent

**Reserve Primary Fund, September 2008** is the canonical instance. A money fund broke the buck on Lehman paper; a run on the entire $3.5 trillion money-fund complex followed within days; a blanket Treasury guarantee stopped it. The template maps directly with one amendment that worsens it, which is speed.

**Terra/Luna, May 2022** is the demonstration of the failure mode at full speed — roughly $40 billion — and, more importantly, the demonstration of *containment*. It did not matter systemically because nothing sovereign depended on it. **That containment property has been spent.** The next depeg happens to an asset class the Treasury's issuance calendar assumes.

### Tripwire

*First mover: aggregate stablecoin supply, issuer reserve attestations, bill yields.*

Aggregate supply is the structural instrument and the one that tests the load-bearing thesis: if supply stalls for two quarters while bill issuance proceeds, the marginal-buyer assumption fails quietly, with no depeg required. That is scenario 23's territory and shows how tightly the two are coupled.

Reserve attestations are the quality instrument, and their weakness is that they are periodic, self-reported, and vary in rigor. Bill yields are the confirmation, and by the time they move the event is underway.

**What a firing does not mean:** a small issuer trading off par is idiosyncratic. The scenario requires a large issuer, or a correlated move across issuers indicating a quality question being asked of everyone simultaneously, which is the free-banking-era failure mode.

### Current state

**Armed.** Issuers are load-bearing by design, the reserve buffer that would absorb a forced bill liquidation is gone, and the framework's own Factor V was promoted specifically because of this linkage. Disruptive Themes sharpened both this scenario and its mirror this cycle.

### Transmission

**Factor V** at the source and **Factor IV** immediately after, through the bill market. This is the single tightest coupling between a tail scenario and a factor pair anywhere in the framework, and it runs in both directions: stablecoin growth absorbs the bill wave the Twist creates, while a depeg dumps the same bills back into a bufferless market.

### Mutations

**Substitution — the depeg happens in a tokenized money-market fund or tokenized Treasury vehicle instead.** This is the most important mutation in the paper. The fastest-growing part of the tokenized-collateral complex is not stablecoins but tokenized funds used as collateral in institutional settlement. They sit outside the stablecoin reserve-attestation regime, they are held by leveraged counterparties as margin, and a break in par there transmits directly into derivatives margin rather than into retail payments. *Instrument:* tokenized fund AUM and collateral usage. **Gap.**

**Scope drift — the failure is operational rather than a reserve loss.** A chain halt, a bridge exploit, or an oracle failure produces a functional depeg with fully solvent reserves. The instrument set built around reserve quality is silent in this case. *Instrument:* none. **Gap.**

**Substitution — the issuer fails through its banking relationship.** The 2023 regional banking episode produced exactly this: a large stablecoin depegged because its reserve deposits sat at a failing bank. The reserve was adequate and inaccessible. This mutation aliases the scenario directly into 14.

**Aliasing — with 23, 1 and 14.** A depeg, a regulatory reversal, a funding accident and a bank event can all present as bill-market disruption with a token symptom.

**Re-specification trigger.** If a major issuer depegs and the Treasury or the Fed backstops the redemption, the scenario is answered and must be rewritten around **moral hazard and contingent sovereign liability** rather than around the depeg itself. That rewrite would be one of the more consequential in the framework, because it would formalize private money as a public obligation.

### Report routing

**Primary: Disruptive Themes, Factor V**, which carries the load-bearing thesis and the aggregate-supply test. **Secondary: Alternative Asset Report**, whose Surveillance tab is the natural home for issuer-level monitoring. **Tertiary: Monthly Macro** for bill yields. Aggregate supply and reserve attestations are uninstrumented and go to the build queue; aggregate supply is publicly available and cheap, making it a priority build given the scenario's armed state.

---

## Scenario 18 · Cryptographic break in settlement infrastructure

**Tier D · quarterly**

### Mechanism

**Not primarily a cryptocurrency question**, which is the misreading the scenario's placement invites. The exposure is the public-key cryptography underlying settlement, custody, clearing, messaging and authentication across the entire financial system. A capability that can break it retroactively compromises everything encrypted before the migration, including data already harvested and stored for that purpose.

The scenario's crucial framing, and the reason it is instrumented the way it is: **the tracked variable is the gap between capability milestones and post-quantum migration progress.** The threat is bounded by migration speed, not by raw capability. A capability breakthrough into a fully migrated system is a non-event. A modest capability arriving into an unmigrated custody chain is a catastrophe. The risk is therefore a *race*, and only one of the two runners is being publicly timed.

### Precedent

None, which is the honest statement. The closest structural analogs are large-scale cryptographic transitions conducted under deadline pressure, and the general lesson from those is that migration always takes longer than planned and that the last ten percent of legacy systems is where the exposure concentrates.

### Tripwire

*First mover: post-quantum standard adoption in settlement, custody and banking infrastructure, measured against verified capability milestones.*

This is the correct construction and the hardest to instrument, because it requires tracking two series that update irregularly and are reported by parties with incentives in both directions: vendors overstate migration progress, and capability claims are frequently demonstrations rather than verified results. **Verified capability only, never announcements**, is the same discipline Disruptive Themes applies in its Part 19 technology block.

### Current state

**Dormant, with a widening gap.** The migration is behind schedule against an uncertain clock. The *Foundations* paper carries the PQC migration gap as Factor V's designated structural headwind for this reason.

### Transmission

**Factor V** structurally, and **everything** operationally if realized, since settlement is upstream of all pricing.

### Mutations

**Scope drift — the break is partial and targeted rather than general.** A single custody or messaging system compromised produces a confidence event without any general cryptographic failure, and would be reported as a hack rather than as a cryptographic break.

**Substitution — the exposure is harvest-now-decrypt-later.** Data already collected and stored against future capability means the loss event may predate the capability by years, and no instrument can detect it.

**Aliasing — with 13, almost perfectly.** In the first hours, a cryptographic break and a cyberattack on infrastructure are indistinguishable, and the operational signature is identical: settlement stops.

**Re-specification trigger.** A verified capability milestone that materially shortens the estimated timeline converts this from a quarterly structural item into an active migration-race scenario requiring monthly cadence.

### Report routing

**Primary: Monthly Macro, Tail Scan**, cyber domain, quarterly. **Secondary: Disruptive Themes, Part 19**, where quantum and PQC migration are already named as a tracked variable with an acknowledged gap. Migration-progress tracking against NIST timelines is uninstrumented in both places and goes to the build queue as a documentation task rather than a data pipeline, since the series is qualitative.

---

## Scenario 13 · Cyberattack on financial infrastructure — the documented blind spot

**Tier: none assigned · reviewed quarterly as an instrumentation problem**

This scenario receives an extended treatment despite carrying no tripwire, because the reasoning behind that absence is the most valuable epistemics on the list and deserves to be argued rather than noted.

### Mechanism

An attack on a central securities depository, a major exchange, or a systemically important custodian. Not a data breach and not a fraud: an availability or integrity failure in the infrastructure that records who owns what. If a depository's records are compromised, the question is not what securities are worth but *who holds them*, and no market can function while that question is open.

### Why price-based indicators fail by construction

This is the analytically important part, and it is a structural claim rather than a difficulty. **Settlement stops before prices move.** Every leading indicator in this entire paper is a price or a quantity derived from trading activity: spreads, volatility, transit counts, positioning, flows. Each of them requires a functioning market to be observed. In this scenario the market's recording layer is the thing that fails, which means the usual leading indicators are silent *precisely when the event occurs*, and are silent because of the event rather than despite it.

That is a different situation from a scenario that is merely hard to instrument. A poorly instrumented scenario can be improved with better data. This one cannot be improved with better price data at all, because the failure mode is the absence of the data.

### Why the blind spot is retained with no tripwire

The source list's reasoning is exactly right and worth restating in full force: **attaching a weak proxy would be worse than documenting the gap, because it would create false confidence in a domain where the failure mode is invisibility.**

Consider what a weak proxy would look like. Cybersecurity firm equity prices. Reported incident counts. A vendor threat index. Each would produce a comforting green light on a dashboard, and each would be uncorrelated with the actual event. Worse, the presence of *any* indicator in the slot would cause a reader scanning the report to register the domain as monitored. The gap would become invisible, which is the specific failure the whole list is designed to avoid.

An acknowledged gap stays visible at every review. That is the entire argument, and it generalizes: **in a system built on instrumentation, the most dangerous entry is not a missing instrument but a decorative one.**

### What can be done instead

Three things, none of which is a tripwire.

**Resilience posture rather than detection.** The question shifts from "will I see it coming" to "what is the position if it happens." Settlement-failure exposure, custodian concentration, and the operational dependencies of any automated system are answerable in advance.

**Aftermath instrumentation.** Once an event occurs, the relevant series are operational rather than price-based: settlement fails, exchange status notices, custodian communications. These are worth identifying now so the first hour is not spent looking for them, and they overlap with scenario 1's fails instrumentation.

**Correlation awareness.** This scenario aliases with 18 in the opening hours and with 8 if an escalation opens with infrastructure attack rather than kinetic action. A report that has thought about the aliasing will hedge its language correctly rather than confidently misattribute.

### Mutations

**Scope drift — the target is a third-party vendor rather than the institution.** Concentration in market data providers, cloud infrastructure, and post-trade software means a single vendor compromise reaches many institutions at once, and the vendor is outside the regulatory perimeter that covers its customers.

**Substitution — the attack is on integrity rather than availability.** A system that keeps running while producing subtly wrong records is far worse than one that stops, because the damage compounds silently and the recovery point is unknown.

**Aliasing — with 18 and 8**, as above.

**Re-specification trigger.** Any successful attack on a systemically important institution, anywhere in the world, converts this from a hypothetical instrumentation problem into a case study with observable aftermath data, and the scenario should be rewritten around the observed transmission rather than the anticipated one.

### Report routing

**Monthly Macro, Tail Scan**, cyber domain, retained explicitly as an open instrumentation problem reviewed each quarter. The correct report language when this domain is reviewed is not "no signal" but "no instrument," and the distinction should be visible in the rendered output.

---


## FAMILY G — THE PRICE-INSENSITIVE BUYER CLASS

## Scenario 24 · BBB downgrade cascade

**Tier C · monthly**

### Mechanism

Roughly half of the investment-grade market sits at the BBB tier, one notch above high yield. A large share of the holders of that paper — insurance general accounts, pension mandates, index funds tracking investment-grade benchmarks, and separately managed accounts with ratings floors — **cannot hold high yield**. Not "would prefer not to." Cannot, as a matter of mandate, statute, or capital treatment.

A downgrade to high yield therefore triggers selling that is entirely independent of the bond's price or prospects. The seller is not making a decision. The mandate is.

The arithmetic is what makes this dangerous rather than merely disruptive. The high-yield market is a fraction of the size of the BBB tier. A modest wave of downgrades — a few percent of the BBB stock — produces forced supply that overwhelms high yield's capacity to absorb it. The market that must buy is far smaller than the market that must sell, and the ratings agencies determine the timing.

This is structurally identical to tail-tier credit stress at far larger notional, and it converts a ratings decision into a market event.

### Precedent

**March 2020** is the near-miss: a downgrade wave began, "fallen angel" volumes reached records, and the Fed's decision to purchase fallen angels — an unprecedented step explicitly designed to interrupt this mechanism — stopped it. The precedent therefore establishes both that the mechanism is real and that the authorities regard it as requiring intervention. **2015–16** is the energy-sector version, contained because it was sectoral.

**The disanalogy:** the BBB tier is larger now than in 2020, and the intervention precedent creates its own hazard, since holders may be underwriting the expectation of a repeat.

### Tripwire

*First mover: BBB share of investment grade, ratings action counts, BBB–BB spread.*

BBB share is the slow structural instrument that sizes the exposure. Ratings action counts, particularly outlook changes and watch placements, are the leading indicator, because agencies telegraph before they act. **BBB–BB spread is the market's own estimate of the cliff**, and its compression is a warning rather than a comfort: a narrow BBB–BB spread means the market is not pricing the mandate discontinuity at all.

**What a firing does not mean:** individual downgrades are routine. The scenario requires clustering, and clustering is visible in outlook changes before it is visible in actions.

### Current state

**Loading.** The CCC−BB differential near 855 basis points indicates the market is discriminating sharply within high yield, which is the environment in which absorbing fallen-angel supply would be most difficult.

### Transmission

**Factor II** through credit conditions and **Factor IV** if the forced selling coincides with impaired dealer capacity, which is the scenario 1 intersection.

### Mutations

**Scope drift — the cliff is in bank capital treatment rather than ratings mandates.** Capital requirements step at ratings boundaries, so the same discontinuity exists in bank holdings with a different trigger and different disclosure.

**Substitution — the forced seller is passive rather than active.** Investment-grade index funds must sell a downgraded bond at the index rebalance date regardless of price, which makes the selling both mechanical and *calendar-predictable*, and therefore front-runnable. This mutation belongs jointly to scenarios 24 and 22. *Instrument:* index rebalance calendars against downgrade timing. **Gap.**

**Substitution — the downgraded issuers are AI-adjacent.** A material share of recent investment-grade issuance financed data-center and AI infrastructure. If scenario 3 realizes, the fallen-angel wave and the capex halt are the same event, and the credit transmission would be faster than the equity transmission. *Instrument:* AI-related IG issuance tracking. **Gap**, and a direct bridge between Families C and G.

**Aliasing — with 6 and 14**, all three being mandate-and-marking credit events.

**Re-specification trigger.** If a fallen-angel wave occurs and is again absorbed by official purchases, the scenario should be re-scoped around the moral-hazard equilibrium rather than the cascade, since the cascade would have been demonstrated to be backstopped.

### Report routing

**Primary: Top & Bottom, HY Spread Acceleration overlay**, which is the correct structural home. **Secondary: Monthly Macro** for the spread series. BBB share of investment grade and ratings action counts are uninstrumented; BBB share is available from index data and belongs in the build queue near the top of this family.

---

## Scenario 22 · Passive-flow reversal

**Tier C · monthly**

### Mechanism

Passive is the largest price-insensitive bid in equities. Its purchases are driven by contributions — payroll deferrals, automatic enrollment, target-date rebalancing — not by any assessment of value. The flow has been positive and growing for four decades, through every drawdown, which means **no version of this market has ever operated with the passive bid in reverse.**

Two mechanisms could reverse it. **Demographic decumulation**: retirees drawing down while contributions from a smaller cohort fail to offset, producing net negative flow as an arithmetic fact rather than a sentiment shift. **A change to retirement default treatment**: default enrollment rules, qualified default investment alternatives, and tax treatment of retirement accounts are the plumbing that makes the flow automatic, and a policy change to any of them alters the flow by decree.

The withdrawal's character is the defining feature: **mechanical, gradual, and unresponsive to valuation.** It does not reverse when stocks look cheap. There is no capitulation and no bottom-tick, because no one involved is making a market judgment at all. And it lands hardest on the most concentrated names, since capitalization-weighted flows exit in the same proportions they entered.

### Precedent

**None.** This is the scenario with the weakest historical grounding on the entire list, and it is precisely why it is dangerous: the structure is roughly forty years old and has only ever operated in one direction. **Japan post-1990** is the loose analog for demographic decumulation meeting a domestic equity market, and its lesson is that the effect is measured in decades rather than quarters.

### Tripwire

*First mover: fund flow data, net passive creation, retirement account net flows.*

Net passive creation is the primary and is available at weekly frequency. Retirement account net flows are the structural instrument and arrive with long lags. The honest characterization is that all three are **confirmation instruments rather than early warnings**: they measure the flow as it happens, not before.

**What a firing does not mean:** a month of negative flows is noise and is usually a tax-season or rebalancing artifact. This scenario is a trend measured in years.

### Current state

**Dormant as a flow, loading as a demographic.** The arithmetic of the boomer decumulation is a calendar fact; whether it exceeds contribution growth is the open question.

### Transmission

**Factor II** structurally. This is the scenario that would most cleanly produce the *Foundations* paper's Lost-Decade Grind: no crash, no crisis, simply the disappearance of a mechanical bid that made every dip buyable for four decades.

### Mutations

**Scope drift — the reversal is in a single vehicle type rather than passive as a whole.** Target-date funds mechanically shift from equity to fixed income on a glide path, so an aging cohort produces automatic equity selling *within* the passive complex without any net outflow. This is happening now and is invisible in headline flow data. *Instrument:* target-date fund AUM by vintage and glide-path schedules. **Gap**, and an unusually tractable one, since the schedules are published.

**Substitution — the withdrawal is a policy change rather than demographics.** Any change to retirement account tax treatment, contribution limits, or default investment rules alters the mechanical bid by decree and on a policy timetable rather than a demographic one. *Instrument:* the legislative and rulemaking calendar, which is the same instrument scenario 23 requires. **Gap.**

**Aliasing — with 21 and 24.** All three are price-insensitive withdrawals and would be reported as a single "structural selling" narrative.

**Re-specification trigger.** Two consecutive quarters of net negative passive equity creation would convert this from a demographic hypothesis into a market condition, requiring re-scoping around the pace of withdrawal and its concentration effects.

### Report routing

**Primary: Monthly Macro**, flows pillar, monthly cadence. **Secondary: Top & Bottom, Concentration & Complacency overlay**, since the withdrawal lands hardest on the concentrated names the overlay already tracks. Net passive creation and target-date glide-path data are uninstrumented and go to the build queue.

---

## Scenario 23 · Stablecoin regulatory reversal

**Tier B · weekly**

### Mechanism

The mirror of scenario 4, and the more likely of the pair. Not a depeg but a **rule change**: forced reserve divestment, issuance restriction, licensing withdrawal, or a change in permitted reserve composition. If issuers are the marginal buyer of bills, a regulatory reversal removes that bid **directly and by decree**, with no market event, no credit loss, and no failure of any kind.

That property is what places this scenario in Family G rather than Family F. The depeg is a failure; the reversal is a policy. One is an accident, the other is a decision, and the decision requires nothing to go wrong.

The mechanism's severity depends on a fact established in Factor V: official financing plans lean on stablecoin growth to absorb bill issuance. Removing a bid that the issuance calendar assumes is a funding problem regardless of how orderly the removal is.

### Precedent

**The National Banking Acts of 1863–64** are the deep precedent: private banknote issuance ended by legislation and taxation rather than by failure. **Money-market fund reform after 2008 and again in 2014** is the modern instance, where rule changes on floating NAV and gates moved trillions between fund categories in an orderly and entirely mandated fashion.

### Tripwire

*First mover: legislative and rulemaking calendar, issuer reserve composition.*

This is the only scenario on the list whose primary instrument is a **calendar rather than a series**, which makes it the easiest to monitor and the most likely to be neglected, since it requires reading rather than fetching. Issuer reserve composition is the second instrument and reveals what a rule change would force.

### Current state

**Loading.** Legislation has been a tailwind; the same legislative capacity that created the framework can amend it, and the issuers' load-bearing status raises the political salience of every future amendment.

### Transmission

**Factor V** and **Factor IV**, identically to scenario 4 but arriving through policy rather than failure.

### Mutations

**Scope drift — the reversal is foreign.** A major jurisdiction restricting dollar-token access, or a CBDC mandate displacing private issuance abroad, removes demand without any domestic rule changing.

**Substitution — the change is to reserve composition rather than to issuance.** Permitting or requiring different reserve assets — longer bills, repo, deposits — alters the bid's composition and duration without touching supply. A subtle version of this could remove the bill demand while leaving the industry untouched, which would satisfy every political constituency and hit the Treasury market anyway.

**Aliasing — with 4.** The consequence set is nearly identical; only the cause differs.

**Re-specification trigger.** Any concrete legislative proposal that would restrict reserve composition converts this from tail to active policy tracking, and it belongs in Factor V's adoption ledger rather than in the tail list at that point.

### Report routing

**Primary: Disruptive Themes, Factor V adoption ledger**, which already tracks stablecoin legislation as a named tailwind and is the correct home for a calendar-based instrument. **Secondary: Alternative Asset Report, Surveillance tab** for reserve composition. No pipeline build is required; this needs a reading discipline rather than a fetcher, which makes it the cheapest item in the entire audit and correspondingly easy to let slide.

---

## Scenario 21 · Sovereign wealth fund forced selling

**Tier C · monthly**

### Mechanism

A large reserve manager or sovereign fund liquidates assets to fund a domestic deficit. The usual trigger is a persistent oil price collapse that pushes revenue below fiscal breakeven, forcing the fund from accumulation into distribution. These entities are among the largest price-insensitive holders of global equities and bonds, and the source list's characterization of their behavior is the important part: **when they turn, they turn slowly and relentlessly rather than in a single event.**

There is no announcement, no forced-seller headline, and no capitulation. There is a persistent bid that was there and is now absent, and then a persistent offer.

### Precedent

**2015–16** is the direct instance: oil below Gulf fiscal breakevens produced sustained sovereign fund selling that was identified largely after the fact. **2020** produced a briefer repeat.

### Tripwire

*First mover: oil against Gulf fiscal breakevens, sovereign fund disclosures.*

The oil-against-breakeven construction is the leading instrument and is genuinely predictive, since fiscal breakevens are published and oil is observable. Fund disclosures are periodic, lagged, and incomplete.

**The current configuration is worth noting:** Brent near $89 sits above most Gulf breakevens, so this scenario is currently *dormant*. But it is directly coupled to scenario 7's adaptation branch: if the chokepoint divergence resolves toward adaptation and oil falls further, this scenario begins loading precisely because the geopolitical risk receded. A benign resolution in one scenario is a loading condition in another.

### Current state

**Dormant**, with the coupling above making it conditionally live.

### Transmission

**Factor II** through equity flows and **Factor IV** through official Treasury demand, aliasing with scenario 11 in the TIC data.

### Mutations

**Scope drift — the seller is a central bank reserve manager rather than a sovereign fund.** Reserve drawdowns to defend currencies produce the same Treasury selling with a different trigger, and are visible in reserve statistics with a lag.

**Substitution — the fund reallocates rather than sells.** A shift from equities into domestic investment or gold produces the same withdrawal of the bid from public markets without any headline liquidation, and connects directly to Factor V's official gold bid, where the accumulation is already running at roughly 860 tonnes in 2025 and 244 tonnes in the first quarter of 2026.

**Aliasing — with 11 and 22.**

**Re-specification trigger.** Sustained oil below the weighted Gulf breakeven for two quarters converts this to an active flow scenario.

### Report routing

**Primary: Monthly Macro**, global or flows pillar. Fiscal breakeven data is published by the IMF and is a straightforward build; sovereign fund disclosures are partial by nature and should be documented as such rather than proxied.

---

## Scenario 25 · ETF wrapper liquidity failure

**Tier B · weekly**

### Mechanism

**Not a fund failing.** The scenario is the failure of the *authorized-participant arbitrage mechanism* that keeps an ETF's price tethered to its net asset value. In normal conditions, APs create and redeem shares against the underlying basket whenever a gap appears, and the gap closes. The mechanism requires the AP to be able to transact in the underlying, and to want to.

In less liquid underlyings — high yield, bank loans, emerging market debt, and increasingly private credit — the underlying may not be transactable at scale during stress, and the AP has no obligation to make markets. When APs step back, the ETF trades at a discount that is not an anomaly but an accurate price for immediate liquidity in an illiquid asset.

**The wrapper promises intraday liquidity the underlying cannot deliver.** That promise is honored by an intermediary with no obligation to honor it, which is the structural flaw.

### Precedent

**March 2020** is the demonstration: high-yield and municipal bond ETFs traded at material discounts to stated NAV for several days. The instructive part of the resolution is that the ETF price was arguably *correct* and the NAV was stale, since the underlying bonds were not trading. **2008** produced similar dislocations in less-developed wrappers.

### Tripwire

*First mover: premium and discount to net asset value in high-yield ETFs, creation-redemption activity.*

Persistent discount is the primary. Creation-redemption activity is the mechanism instrument, and its *cessation* is the actual signal: an absence of activity where activity should be occurring.

**What a firing does not mean:** a discount during a fast selloff is the wrapper working as a price-discovery venue, which is arguably its most valuable function. The scenario requires the discount to persist alongside halted creation-redemption.

### Current state

**Dormant.** The mechanism is untested at the current scale of credit ETF assets, and the growth of semi-liquid and private-credit wrappers has extended the same promise to considerably less liquid underlyings.

### Transmission

**Factor II** through credit conditions, with the aliasing to scenarios 6 and 24 running strongly, since a wrapper failure in credit and a mark event in private credit would be narrated as one story.

### Mutations

**Scope drift — the wrapper is an interval fund or a semi-liquid private vehicle.** These extend the liquidity promise to genuinely illiquid assets with periodic gates, and a gate is a wrapper failure with a legal document attached. This mutation connects directly to scenario 6's fastest path.

**Substitution — the failure is in a leveraged or derivative-based wrapper.** Products holding futures, swaps, or options rather than the underlying face a different failure mode: the derivative market's own liquidity. Single-stock leveraged products, discussed in scenario 20's mutations, sit here as well.

**Aliasing — with 6 and 24.**

**Re-specification trigger.** A sustained discount with halted creations in any major credit wrapper converts this from a structural hypothesis into a demonstrated event, and the rewrite should focus on which wrapper types held and which did not.

### Report routing

**Primary: Monthly Macro**, credit pillar. **Secondary: Alternative Asset Report, Surveillance tab**, since ETF wrapper behavior across its 18 assets is directly observable there. Premium-discount data and creation-redemption activity are uninstrumented and go to the build queue; both are publicly available daily and are among the cheapest builds in the audit.

---
