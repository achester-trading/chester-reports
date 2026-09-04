# Portfolio Construction Across Regimes
## The Bridge Between Anticipating Disruption and Positioning for It

**Companion to: the full five-report stack — Disruptive Themes, Monthly Macro, Top & Bottom, Alternative Asset, Daily Cascade · Draft 1 · ~4,400 words · 31 August 2026**

---

> ### DRAFT 1 — PREVIEW EDITION
>
> **What this is.** A short paper that establishes the frame, the vocabulary, and the open questions for cross-asset portfolio construction under regime change. It is deliberately theoretical: it names the disciplines and states the rules, but it cannot yet show what those rules produced in this book, because the instrument that would show it — the trade recommendation register — does not yet have data.
>
> **What this is not.** Not the extended edition. Not a strategy. Not a list of positions.
>
> **Update trigger — when to write Draft 2.** All four conditions, not any one:
>
> 1. **The v17 rebuild has run** — the store layer (D1 + parquet + local mirror), the register, and the Weekend Synthesis are live and passing the validator.
> 2. **The dashboards are designed** — the Tier 0 System State Dashboard and the v17 report set are in their settled form, so the sizing tiers this paper leans on are the ones actually in production.
> 3. **The register has at least three months of data** — enough recommendations, with entries, invalidations, and outcomes, that the sections marked *[empirical in Draft 2]* below can be written from the book's own history rather than from principle.
> 4. **IBKR Gate 1 is live** — read-only sync gives the register mark-to-market, which turns the hedge-cost and rebalancing sections from estimates into measurements.
>
> Expected Draft 2 timing on the current schedule: **late Q4 2026 to Q1 2027.** Sections marked *[empirical in Draft 2]* are the ones that will change most. Everything else should survive largely intact.
>
> **Numbering.** This paper is unnumbered in Draft 1. It takes its Roman numeral when it enters the library guide alongside the Credit paper.

---

## Preamble · The gap this paper fills

The ten companion papers explain how markets work. Read together, they let you anticipate disruption with considerable precision — a Factor III chokepoint divergence, a Concentration & Complacency overlay firing five of five, a Monthly composite drifting toward TOP SIGNAL, a Hartnett Bull & Bear print at 8.0. What they do not do, except in fragments, is tell you what a book should look like while that is happening.

The fragments are real and they are good. The Metals paper carries a position-construction section (Part V-B) with vol-scaled sizing and the copper instrument problem. The Currencies paper carries hedging and trading FX, written with a specific baht exposure in view. The Top & Bottom Report ships scenario-weighted options portfolios in Appendix D; the Monthly ships illustrative thesis trades in Appendix C. The Daily Cascade sizes intraday setups within a tier.

None of them does the thing this paper does: treat the book as one object, across every asset the stack covers, and ask what happens to that object when the regime moves.

That question has four parts, and they are the four parts of this paper: **sizing** (how large, at the position level and the book level), **hedges** (what they cost, and — more important — when they fail), **rebalancing** (the discipline of adjusting a book you would rather leave alone), and **regime transition** (what actually changes for a book when the five-report stack moves from one row of the translation table to the next).

The paper takes one position throughout that is worth stating up front. **The book's job is not to predict the regime change. Its job is to be sized so that the regime change is survivable and the reports have time to catch it.** Prediction lives upstream in the five reports and the translation table. Construction lives here, and construction's virtue is robustness, not foresight.

---

## Part I · What a regime is, for a book

The five-report stack uses "regime" in a specific sense: the row of the translation table that the Disruptive Themes frame, the Monthly composite, the Top & Bottom verdict, and the Daily macro-risk read jointly imply. Soft-landing holds; late-cycle contained; late-cycle fragile; crisis or regime break; trough and reset. Those rows exist because the reports need a shared vocabulary.

For a book, a regime means something narrower and more mechanical. **A regime is a joint distribution** — of returns, of volatility, of correlation, and of liquidity — that persists long enough to be worth positioning for. When the regime changes, all four move at once, and they rarely move in the direction a position-by-position view would expect.

Four things change when a regime turns, in roughly this order of consequence for a book:

**Correlations go first.** The diversification that a book was built on is a property of the regime that built it. The 2022 episode is the cleanest modern example: equities and long-duration bonds fell together for the first sustained stretch in a generation, and the 60/40 construction that had worked since the early 1980s lost on both legs. The BlackRock Investment Institute note captured in the Monthly's Pillar 10 — Treasuries failing as portfolio hedges during the Iran-war energy shock — is the same mechanism, live, in the current cycle. A book that is "diversified" is diversified under the correlation matrix of the regime it was built in, and the transition is precisely when that matrix is least reliable.

**Volatility changes character, not just level.** The Dealer's Hand paper makes the point for index options: GEX regime is a forecast of volatility *character*, not direction. At the book level the same is true. A regime transition from positive to negative dealer gamma does not merely raise realized vol; it changes the autocorrelation of returns, the reliability of mean-reversion, and the cost of any position that is short convexity. A short-gamma edge — which is the stated edge in this system — is an edge in one volatility character and a liability in another.

**Liquidity changes, and with it execution cost.** The bid-ask spread on a Friday afternoon in a positive-gamma regime and the bid-ask spread at 9:35 on the morning after a credit event are not the same instrument. Sizing that was appropriate under the first is oversized under the second, not because the thesis changed but because the cost of exiting did. This is the connection to the Systematic Book paper: execution cost is regime-dependent, and any sizing rule that ignores that will be right in calm regimes and wrong when it matters.

**The hedges that work change.** This is Part III's subject and the paper's most important claim. A hedge is a bet on a correlation. When correlations move, the hedge moves with them, and the hedge that paid in the last drawdown is not guaranteed to pay in the next.

The practical consequence: **a regime label in the translation table is a summary of a joint distribution, and the book should be constructed against the distribution, not the label.** The label tells you which row you are in. The distribution tells you what the row will do to the positions.

---

## Part II · Sizing

### The book-level dial

The translation table already contains a sizing dial: 100% normal, 50–70% normal, 25–40% normal with no new longs, defensive only and hedged, scaling back in. The Tier 0 dashboard computes which setting the dial is on by walking the conflict-resolution rule. That is the book-level constraint, and everything in this section operates inside it.

What "normal" means is the first thing to pin down, and it is the one thing the current system leaves undefined. Draft 2 will define it from the register. For Draft 1, the working definition: **normal is the gross exposure at which the book's realized volatility, measured over the last regime, matched its target.** That makes "50% normal" a statement about volatility budget, not about dollars, which is the right unit.

### Position-level sizing: volatility-scaled by default

The Metals paper's Part V-B establishes vol-scaled sizing for a single asset class. The generalization to the book is direct: **each position's notional is set so that its contribution to book volatility is the intended fraction of the book's volatility budget**, using a trailing realized-vol estimate appropriate to the holding horizon.

Three refinements matter cross-asset:

- **The vol estimate should be regime-aware.** A 60-day trailing vol on the day after a regime break is a measurement of the old regime. Using it to size a new position is a known error. The practical fix is a short-window override: when the Top & Bottom overlays or the Daily's vol block flag a regime change, the sizing window shortens, and positions are sized against the new realized vol even though it has less data. Less data, more relevance.
- **Correlated stacking is a sizing error, not a diversification benefit.** A long-ES, long-NQ, short-VIX-call, long-gold-as-risk-on book is one position with four tickers. The register's cross-report conflict detection — flagging contradictions, duplicates, and correlated stacking before sizing — is the mechanism that catches this. Until the register is live, the rule is manual: **sum exposures by factor, not by instrument**, and size the factor.
- **Kelly is an upper bound, not a target.** The fractional-Kelly discussion belongs in the Systematic Book paper because it needs expectancy data. Here the only point is directional: no position in a book governed by a regime dial should be sized at full Kelly, because full Kelly assumes the edge estimate is right, and the whole architecture of this system is built on the premise that estimates drift with the regime.

### Hard constraints

Two constraints sit outside the sizing logic entirely and cannot be overridden by it.

**The Brookfield restriction.** No recommendation for any security in the Brookfield complex — BN, BAM, BIP, BIPC, BEP, BEPC, BBU, BNT, and the property preferreds — under any regime, at any size. This is enforced at register write-time as a schema constraint, which is the correct enforcement point: a rule that lives in a prompt can be argued with; a rule that lives in a schema cannot. The restriction is personal and professional and requires no compliance review, but it is a construction constraint and belongs in this paper for completeness.

**The Thai baht property exposure.** This is not a restriction but a standing exposure that the book does not choose and cannot easily close. The Currencies paper treats how to hedge it. For construction purposes the point is that **it is a permanent position in the book's factor sum** — an unhedged or partially hedged emerging-market currency exposure that must be counted against the FX factor budget before any discretionary FX position is added.

### *[empirical in Draft 2]*

What the register will add here: the realized ratio of book volatility to target by tier, the frequency with which correlated-stacking flags fired, and whether "normal" as defined above held stable across the first two regime transitions or needed redefining.

---

## Part III · Hedges — what they cost, and when they fail

### A taxonomy

Hedges in this book fall into four types, in ascending order of how directly they address the risk:

| Type | Examples | What it hedges | Carry |
|---|---|---|---|
| **Structural** | Cash, reduced gross, no new longs | Everything, imprecisely | Opportunity cost only |
| **Proxy** | Long TLT, long gold, long DXY | A correlation you believe in | Financing cost plus basis risk |
| **Direct** | SPX or ES puts, put spreads | The index the book is long | Premium, decaying |
| **Convex** | VIX calls, far-OTM puts, tail ladders | The regime change itself | Premium, decaying faster, paying rarely |

The translation table's sizing dial is a structural hedge. It is also the cheapest and most reliable one, which is why it sits at the top of the conflict-resolution rule. Everything else in this section is about the other three, and the paper's core claim about them is this: **each of the three is a bet on a correlation, and the correlation is a property of the regime.**

### The carry problem

Every non-structural hedge has a cost of being held, and the cost is highest when the hedge is most needed. Option premium rises with implied volatility; implied volatility rises when the regime is turning; the hedge you buy after the overlays fire is the expensive one. Proxy hedges have financing and basis cost that look small in calm regimes and compound over a holding period measured in quarters.

The discipline the paper proposes is the one the Top & Bottom Report's Appendix D already practices: **hedge at the tier, not at the event.** The dashboard's sizing tier changes on a regime signal, and the hedge budget is a function of the tier — a fixed percentage of book notional per tier, spent on hedges regardless of whether the event has arrived. This costs money in tiers where nothing happens. That is the price of having the hedge on when something does.

The Monthly's Appendix C and the Top & Bottom's Appendix D are the two live sources of hedge structures in the system, and the translation table's reconciliation rule governs them: Top & Bottom wins on structure because it is scenario-weighted; Monthly wins on macro framing because it explains why the hedge exists. A book that holds a hedge without being able to state which pillar or trigger produced it is holding a position it cannot invalidate, and a position that cannot be invalidated cannot be sized.

### When hedges fail

This is the section the extended edition will expand most, because the register will supply the book's own failures. Draft 1 states the four mechanisms.

**Correlation-to-one.** In a liquidity event, everything that can be sold is sold, and the hedge is sold with it. March 2020 is the modern archetype: gold and Treasuries fell alongside equities in the first two weeks, because the marginal seller needed dollars, not exposure. A proxy hedge fails first and worst here. A direct hedge holds, because the index put's payoff is contractual. A structural hedge — cash — is the only one that gains.

**Bonds and equities falling together.** The 2022 episode and the current cycle's energy-shock stretch are the same mechanism: when the driver of the drawdown is inflation or a rate shock rather than a growth shock, long duration is not a hedge but a second long. The Rate and Liquidity Machine paper carries the full treatment; here the rule is that **a TLT-style hedge is conditional on the drawdown being a growth event**, and the Monthly's Pillar 4 read is what tells you whether it will be. The Top & Bottom's Appendix D 12-month portfolio carries a TLT call spread for exactly this reason, and carries it as a hedge for the Fed-pivot path specifically, not as a general equity hedge.

**Vol-of-vol.** A rolled put or put-spread program is exposed to the cost of rolling into a higher-vol regime. When the VIX gaps from 17 to 35, the next roll costs roughly twice what the last one did, and a hedge budget sized in the calm regime buys half as much protection. The convex tail-ladder structures in Appendix D address this by buying the protection before the regime moves; the cost is that the ladder decays through every quiet quarter.

**Hedging the wrong regime.** A put spread caps its payoff at the short strike. It is the right hedge for a 5–15% correction and the wrong hedge for a 35% crash, where the short strike is deep in the money and the spread has stopped paying. The Top & Bottom's 3-month portfolio pairs the put spread with a VIX call precisely to cover the vol-spike scenario the spread underprices. The general rule: **know which row of the translation table each hedge is built for, and hold at least one hedge for the row below it.**

### *[empirical in Draft 2]*

The register plus Gate 1 mark-to-market will supply: realized carry paid per tier over the first two quarters; the realized correlation of each proxy hedge to the book during the first drawdown the book lived through; and whether the hedge-at-the-tier discipline was actually followed or was overridden at the event. That last one is the honest test.

---

## Part IV · Rebalancing discipline

Rebalancing is the part of construction that is easiest to state and hardest to do, because it requires acting against the book's recent experience — adding to what has lost, trimming what has won, and buying the hedge that has been bleeding.

Three rebalancing triggers are in common use. **Time-based** (monthly, quarterly) is simple and is what most of the industry does. **Threshold-based** (rebalance when any position drifts more than *x* from target) is more responsive but generates trades in noise. **Regime-triggered** rebalances when the regime read changes.

For a book run on this stack, **regime-triggered is the natural fit**, because the stack already produces the trigger: the Tier 0 dashboard's sizing tier. When the tier changes, the book rebalances to the new tier's volatility budget and hedge budget. When the tier does not change, the book holds, and threshold bands catch the drift. Time-based rebalancing is retained only as a floor — a quarterly review that fires even if nothing else has, aligned to the quarterly calibration in the Systematic Book paper.

Two disciplines within that:

**Rebalancing into a losing hedge is the test of whether the hedge budget is real.** If the tier says 25–40% normal and the hedge budget is a fixed fraction of notional, then a put spread that has decayed 40% since purchase must be topped back up to the budget, in the same regime, at the higher implied vol. Every instinct says not to. The discipline says that the hedge budget is a function of the tier and the tier has not changed. The register will record whether this was done.

**Drift bands should be wider in the direction of the tier.** If the tier has moved from 100% to 50–70%, positions that have drifted *below* target through losses should be tolerated longer than positions that have drifted *above* target through gains. The asymmetry encodes the tier's direction into the rebalancing tolerance rather than fighting it.

Friction — commissions, the futures roll, the option roll, tax — is real and is treated in the Systematic Book paper's execution section. Here the point is that rebalancing cost is itself regime-dependent, and a rebalance that costs 5 basis points in a positive-gamma regime can cost 30 in a negative one. Regime-triggered rebalancing has the incidental virtue of front-running that cost increase: the trigger fires on the regime signal, before the execution cost has fully repriced.

---

## Part V · What a regime change means for a book — a walk-through

This section walks the translation table's five rows and states what the book looks like in each and what changes at each transition. Draft 2 will replace the illustrative language with the book's actual history.

**Soft-landing holds → late-cycle contained.** The book moves from 100% to 50–70% normal. The transition is usually triggered by the Monthly composite crossing −0.5 or the Top & Bottom moving to WATCH. What changes: gross comes down, the hedge budget turns on (it was zero or near zero in the top row), and the position-level vol estimate window shortens. What does *not* change: the book's factor mix. This transition is a volume adjustment, not a composition change.

**Late-cycle contained → late-cycle fragile.** The book moves to 25–40% normal, no new longs. This is the transition the current cycle is in as of this writing — the Disruptive Themes composite at −1.2 on the edge of TOP SIGNAL, the Concentration & Complacency overlay at five of five, the Monthly's modal scenario a Hartnett pullback at 40–50%. What changes: composition. Concentrated-name exposure comes out first, because the overlay that fired is a concentration overlay. The hedge budget rises, and it shifts from direct toward convex, because the row below is the one where vol-of-vol punishes rolled direct hedges. New longs are prohibited, which is a harder rule than it sounds — it prohibits adding to a winner, and it prohibits the "this dip is different" trade.

**Late-cycle fragile → crisis or regime break.** Defensive only, hedged. The book's factor exposures collapse toward zero; what remains is the hedges, cash, and the standing exposures the book cannot close (the baht property). This is the row where proxy hedges fail and direct and convex hedges pay. The discipline that matters most here is not adding a new hedge — it is too late and too expensive — but *not selling the hedges that are paying* in order to buy the dip. The Top & Bottom's BOTTOM SIGNAL arms are the only instruction to begin re-entering, and the row below is where that happens.

**Crisis → trough and reset.** Begin scaling longs back in. The Top & Bottom calibration found the framework stronger at detecting bottoms than tops, which is the empirical basis for trusting this transition more than the ones above it. What changes: the hedge budget comes off — gradually, because the first BOTTOM SIGNAL arm is often early — and the factor mix is rebuilt from the Disruptive Themes scenario distribution, not from the pre-crisis book. The trough is the one row where the book's composition is a fresh decision rather than an adjustment.

**The current cycle, as a worked example.** The book as of 31 August 2026 sits in the late-cycle fragile row. The dashboard's sizing synthesis reads 25–40% normal, no new longs, escalated one tier from the Monthly's OVEREXTENDED baseline by the active Concentration overlay. The hedge budget is on, tilted convex. The HY Spread Acceleration overlay is clear at zero of four — which is the single most important thing the book is watching, because it is the overlay that would move the read to the row below. The Liquidity & Funding Stress overlay at two of five is the second. The book is built for a Hartnett-pullback-magnitude event (5–15%) with a convex leg for the crisis row. That is the construction. Whether it was right is a Draft 2 question.

---

## Part VI · Cross-asset notes

Brief, because the asset papers carry the detail. Each entry states where the asset sits in the book's factor sum and what construction rule this paper adds to the asset paper's own.

**Equities and index (ES, NQ, index options).** The core. The stated edge — short-gamma, high-vol expansion, scaling into 5–10% multi-day moves — lives here, and the Systematic Book paper treats how to size scaling-in. The construction rule this paper adds: **the edge is regime-conditional, and its size should scale with the Daily's GEX character read**, not only with the book-level tier.

**Rates (TLT and the curve).** A conditional hedge, per Part III. The Rate and Liquidity Machine paper is the reference. Construction rule: hold duration as a hedge only when the Monthly's Pillar 4 read says the drawdown driver is growth, not inflation.

**Gold and metals.** The Metals paper's Part V-B is the reference and this paper's sizing section generalizes it. Construction rule: gold's Factor V role — the official-sector bid, the debasement trade — makes it a structural position in this cycle, not a tactical hedge, and it should be sized against the FX and dollar factor budget, not the equity one.

**FX.** The Currencies paper is the reference. Construction rule: the baht exposure is counted first, always, and the discretionary FX budget is what remains.

**Digital assets.** The Digital Assets paper is the reference. Construction rule: crypto's correlation to equities is the least stable of any factor in the book, which argues for the smallest position-level vol budget and the shortest sizing window. The two-source crypto reconciliation the translation table used to carry is gone — Alt Asset writes to the store, one source — but the instability of the correlation itself is unchanged.

**Energy.** A gap. The Energy paper is unwritten and the Hormuz divergence is the single most important current signal in the Disruptive Themes frame. Construction rule, pending that paper: energy exposure in the book is currently *indirect* — through the inflation read in the Monthly's Pillar 4 and the Factor III score — and the book has no direct energy instrument. That is a construction gap, not just a coverage gap, and it is flagged here so that the Energy paper's instrument set can close it.

---

## Part VII · The register as the book's memory

Everything above is stated from principle. The instrument that will let Draft 2 state it from evidence is the trade recommendation register — the predicates table with P&L attached, recommendations and positions as separate tables joined on `rec_id`, feeding the expectancy ledger in `execution-framework-v2`.

What the register will teach that this draft cannot:

- **Realized hedge cost by tier** — what the hedge budget actually spent, quarter by quarter, and what it paid back.
- **Realized correlation inside the book** — not the textbook correlation matrix but the one this book lived through, position by position, during its first drawdown.
- **Conflict and stacking frequency** — how often the register's cross-report conflict detection fired, and what the book would have looked like if it had not.
- **Expectancy by regime row** — the only measurement that can say whether the construction was right, and the one the Systematic Book paper's validation protocol is built around.
- **Whether the disciplines were followed.** Rebalancing into losing hedges, no new longs in the fragile row, holding the hedges through the crisis row — the register will record whether these happened or were overridden, and Draft 2 will be honest about it.

The Monthly's Appendix C stops being a manually written section once the register is live and becomes a query. That is the intended end state for this paper too: a construction discipline that is stated once, in Draft 2, and thereafter measured rather than re-argued.

---

## Part VIII · What Draft 2 adds

For the record, so the update is scoped in advance:

1. A definition of "normal" derived from the register rather than asserted.
2. Realized hedge cost and hedge payoff tables by tier, from Gate 1 mark-to-market.
3. The book's own correlation matrix through its first regime transition under v17.
4. The rebalancing log — every tier change, what was rebalanced, at what cost, and whether the hedge budget was honored.
5. The regime walk-through in Part V rewritten from the book's history rather than from the translation table's rows.
6. An energy section, once the Energy paper exists and the instrument set is in the store.
7. Cross-references to the Credit paper, which will change the hedge taxonomy's treatment of credit-sensitive proxies.

---

*Draft 1 · 31 August 2026 · Companion to the five-report stack · Not investment advice. Illustrative constructions only; no recommendation for any specific instrument, and no instrument in the Brookfield complex under any circumstances.*
