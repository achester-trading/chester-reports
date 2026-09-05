# THE DEALER'S HAND

### Options, Gamma, and the Mechanics Behind §06 — An Elaboration of Daily Cascade Chapter 2

**Companion IX · Version 1.0 · August 30, 2026**

---

*This paper sits directly beneath Chapter 2 of the Daily Cascade white paper. That chapter gave §06 its seven-element treatment — signal, adoption, strengths, limits, dependencies, and the eight rules of 2.7 — at the altitude of the rest of the cascade. It assumed the reader already knew what gamma is and why a dealer hedges. This paper removes that assumption. It builds the machinery from a single option contract upward, carries one numerical example through every layer, and ends where the other paper began: at the eight rules, now with the mechanics underneath them visible.*

*Twenty-one figures and the worked ledgers are placed where the mechanics are hardest; every curve is computed from the same Black-Scholes arithmetic as the running example, so the pictures and the numbers agree. Read this once, slowly, with a pen. The running example uses round numbers chosen for arithmetic clarity, then reconciles to the actual figures in the 0700 report's §06 in Part III. This paper is the controlling elaboration of Daily Cascade Chapter 2: where that chapter summarizes a mechanism, this one derives it.*

---

## HOW THIS PAPER IS ORGANIZED

**Part I — Options from first principles.** What a contract is, what it costs and why, and the Greeks as the risk measures they actually are. Built on the insurance mapping, which for options is not an analogy but a literal identity.

**Part II — The dealer.** Who sits on the other side, what they want, and the hedging mechanic that turns their inventory into forced flow in the underlying. Long gamma and short gamma as two different worlds. Aggregation into GEX. The walls, the flip, the second-order flows (vanna, charm), and the 0DTE regime that now dominates.

**Part III — Reading §06.** A line-by-line walkthrough of the section as printed in the report, each number reconciled to the mechanics.

**Part IV — Trading it.** The regime gate as a daily protocol, six setups with numbers, options-versus-futures expression, and the failure modes specific to trading positioning data.

**Part V — The multi-horizon book.** The four expiry books read simultaneously: the five stack configurations, the Greeks located by horizon, the 0DTE session taxonomy (why the same-day book shapes each day differently), and the layered intraday protocol. The advanced chapters — added by request once the single-horizon machinery was in hand.

**Appendix.** Glossary, the formulas in one place, and a one-page card.

---

# PART I — OPTIONS FROM FIRST PRINCIPLES

---

## CHAPTER 1 — THE CONTRACT

### 1.1 The insurance mapping, stated exactly

An equity index put option is a property policy on a portfolio. The mapping is term-for-term:

| Insurance | Option | In the running example |
|---|---|---|
| Premium | Option price | 137 SPX points (×100 = $13,700 per contract) |
| Attachment point / retention | Strike | 7,500 |
| Policy period | Time to expiry | 30 days |
| Rate on line | Implied volatility | 16% annualized |
| Earned premium over the period | Theta (time decay) | roughly 2.3 points/day at inception, accelerating |
| Loss sensitivity | Delta | −0.50 |
| How fast exposure grows as the loss develops | Gamma | 0.0010 per point |
| Rate-change sensitivity | Vega | ~8.6 points per 1 vol |
| The carrier | The option writer | the dealer, usually |
| Reinsuring away the loss cost, keeping the margin | Delta hedging | the subject of Part II |
| A layer (attach at X, exhaust at Y) | A vertical spread | JHEQX's 95%/80% put spread |

Everything in this paper follows from taking that table seriously. An option writer is a carrier. A dealer is a carrier who lays off the expected loss continuously and keeps only the margin and the development risk. GEX is the industry's aggregate exposure by attachment point. The gamma flip is the point where the industry's aggregate book turns from net-ceded to net-retained. Read the rest with that frame and nothing here will be surprising.

### 1.2 The four positions

A **call** is the right to buy the index at the strike before expiry. A **put** is the right to sell it. Each can be bought or sold, giving four positions:

- **Long call** — pays a premium for upside participation above the strike. Loss capped at the premium.
- **Long put** — pays a premium for protection below the strike. The policyholder.
- **Short call** — collects a premium and owes the upside above the strike. Unlimited exposure.
- **Short put** — collects a premium and owes the downside below the strike. The carrier.

The running example: **SPX at 7,500. The 7,500-strike, 30-day put costs 137 points.** (Rates and dividends are set aside throughout — they matter to the dealer's book at the second decimal and to nothing in this paper.)

A portfolio manager holding $75 million of SPX exposure — 10,000 index-units — buys 100 of these puts (each contract covers 100 units). Cost: 100 × 137 × 100 = $1.37 million, or 1.8% of the portfolio, for 30 days of protection below 7,500. That is a 1.8% rate on line for a 30-day policy with zero retention, which annualizes to roughly 22% — and that number, the annualized premium as a fraction of notional, is the intuition behind why systematic option *selling* is a business: someone is being paid 22% a year to underwrite a risk whose realized frequency, most years, is a fraction of that. Chapter 4 of the Daily Cascade paper called this the vol risk premium. This is what it looks like from the policyholder's side of the desk.

### 1.3 Payoff at expiry, and why nobody holds to expiry

At expiry the put is worth max(7,500 − SPX, 0). At 7,300 it is worth 200; at 7,600, zero. The long-put holder's net result is the payoff minus the 137 paid — breakeven at 7,363.

*(Figure 1 — The long put at expiry — see the HTML edition for the chart.)*

Two facts about this picture matter more than the picture itself. First, **almost no index option trades to expiry as a bet on the terminal payoff**; the overwhelming majority are hedges, overlays, and structures that are adjusted, rolled, or closed long before. Second, and consequently, **the interesting quantity is never the payoff at expiry but the option's value right now, and how that value changes as the market moves.** That is the subject of the next two chapters, and it is where everything the report measures actually lives.

### 1.4 Put-call parity in one sentence

Owning a call and holding cash equal to the strike is economically identical to owning a put and the underlying. The formal statement is C + K·e^(−rt) = P + S; the practical consequence is that **a dealer who is long a 7,500 call and short one unit of the index has the same risk as a dealer long a 7,500 put.** Calls and puts at the same strike are the same convexity wearing different clothes. This is why, in Part II, call gamma and put gamma at a strike combine into one number rather than two.

---

## CHAPTER 2 — WHAT AN OPTION COSTS, AND WHY

### 2.1 Intrinsic and extrinsic value

The 137-point put at a 7,500 strike with the index at 7,500 has **zero intrinsic value** — exercising it now yields nothing. The entire 137 points is **extrinsic value**: the market's price for the *possibility* that the index finishes below 7,500 within 30 days, and for how far below it might finish.

Extrinsic value is what decays. It is what the carrier earns. It is the only thing a dealer's book is really made of. Move the index to 7,400 and the same put is worth roughly 100 intrinsic plus ~85 extrinsic; the extrinsic shrank because the option is now less uncertain (it is more likely to finish in the money, and certainty is cheap).

*(Figure 2 — Value before expiry: intrinsic + extrinsic — see the HTML edition for the chart.)*

### 2.2 The five inputs

An option's price is a function of spot, strike, time to expiry, the risk-free rate, and volatility. Four of those are observable. **Volatility is the price.** When a trader says "I paid 16 vol for the put," they mean that 137 points is the price the Black-Scholes machinery returns when you feed it 16% annualized volatility — so quoting the vol *is* quoting the price, in units that are comparable across strikes and expiries the way a rate on line is comparable across policies of different size.

**Implied volatility is therefore not a forecast.** It is the market-clearing rate for the risk. It embeds a forecast, a risk premium, supply and demand for that specific strike, and dealer inventory effects — exactly as a reinsurance rate embeds expected loss, a margin, market capacity, and the cedent's negotiating position.

### 2.3 The one calculation worth memorizing

The market's one-standard-deviation expected move over a horizon is approximately:

**Expected move ≈ Spot × IV × √(days / 365)**

For the example: 7,500 × 0.16 × √(30/365) = 7,500 × 0.16 × 0.287 ≈ **344 points** over 30 days.

For a single day: 7,500 × 0.16 × √(1/252) ≈ **76 points**, or about 1.0%.

A useful shortcut that avoids the arithmetic: **the at-the-money straddle price is roughly 0.8 times the one-sigma move**, so a straddle priced at 275 implies a one-sigma move of about 344, and — running the other way — the expected move the report quotes (±52 points, ±0.7%) is read off the 0DTE straddle directly. Chapter 12 does this reconciliation with the report's numbers.

### 2.4 Why the skew exists, in dealer terms

The 7,300 put (200 points out of the money) trades at a higher implied vol than the 7,500 put — 19 vol versus 16, say. The Daily Cascade paper explained skew as the rate-on-line differential across layers. The dealer's version: the 7,300 put is a policy the dealer is *structurally short* (institutions buy protection, dealers sell it), the risk it covers arrives fast and correlated (crashes are gap events, not diffusion), and hedging it continuously is impossible in the scenario where it pays out. The higher vol is the dealer's charge for warehousing an unhedgeable tail — the cat load. Chapter 6 shows why that structural short put position is also the reason aggregate dealer gamma turns negative below spot.

---

## CHAPTER 3 — THE GREEKS AS RISK MEASURES

*The Greeks are partial derivatives of the option's price with respect to each input. That sentence is true and useless. Each one is better understood as the answer to a specific operational question the dealer must ask every minute.*

### 3.1 Delta — "how much index am I effectively holding?"

Delta is the change in option value per one-point change in the index. The 7,500 put at 7,500 has delta **−0.50**: if SPX rises one point, the put loses half a point. A 7,500 call has delta **+0.50**.

Two readings, both used constantly:

**As a hedge ratio.** Owning 100 contracts of a 0.50-delta call (100 × 100 × 0.50 = 5,000 index-units of delta) is, for small moves, the same exposure as owning 5,000 SPX units — or 100 ES contracts, since each ES represents 50 units. To neutralize it, sell 100 ES. This is the entire basis of Part II.

**As a probability proxy.** Delta approximates the probability the option finishes in the money. A 0.25-delta put is roughly a one-in-four chance of paying. The "25-delta skew" in the vol surface section names its layer by this convention.

Delta is bounded: 0 to 1 for calls, −1 to 0 for puts. Deep in the money it approaches ±1 (the option behaves like the index); deep out of the money it approaches 0 (the option barely reacts).

*(Figure 3 — Delta across spot (30-day options, strike 7,500) — see the HTML edition for the chart.)*

### 3.2 Gamma — "how fast is my delta changing?"

Gamma is the change in delta per one-point change in the index. It is the convexity, and it is the reason a delta hedge does not stay hedged.

In the example, the 7,500 put has gamma of roughly **0.0010 per point** — meaning a 75-point rise in the index (1%) moves the put's delta from −0.50 to about −0.42, and a 75-point fall moves it to about −0.58.

Three properties of gamma drive everything downstream:

- **Gamma peaks at the money and falls off away from the strike.** A 7,500 option has maximal gamma with the index at 7,500; at 7,200 or 7,800 its delta is near its bound and barely moves.
- **Gamma is identical for the call and put at the same strike** (put-call parity again). A 7,500 call also has 0.0010 gamma.
- **Gamma explodes as expiry approaches.** At 30 days, the ATM delta drifts 0.08 for a 1% move. In the final minutes of the session, the delta of an ATM option flips from near 0 to near 1 across a range of a few points — with ten minutes left, the 7,500 call at 7,495 has delta ≈ 0.34 and at 7,505 ≈ 0.66. **Ten points of spot produced a delta change roughly thirty times larger than the same ten points produce in the 30-day option.** That single fact is why half of SPX volume now expires the same day and why 0DTE gets its own chapter.

*(Figure 4 — Gamma concentrates at the strike — and explodes into expiry — see the HTML edition for the chart.)*

The insurance reading: gamma is how fast a layer's expected loss accelerates as the loss develops toward the attachment point. Far from attachment, a marginal deterioration barely changes expected loss. Near attachment, every point of deterioration lands squarely in the layer. Gamma is highest exactly where the carrier's exposure is most sensitive — and that is not a coincidence, it is the same mathematics.

### 3.3 Theta — "what am I being paid to wait?"

Theta is the change in option value per day, holding everything else fixed. The 30-day ATM put loses roughly **2.3 points per day** at inception, and the loss accelerates: extrinsic value decays as the square root of time, so the last week costs the holder more than the first two combined.

*(Figure 5 — Theta: the earned-premium schedule — see the HTML edition for the chart.)*

Theta is the earned premium. **Gamma and theta are the same thing seen from opposite sides**: a long-gamma position (long options) pays theta for the privilege of owning convexity; a short-gamma position (short options) collects theta for underwriting it. There is no free convexity, and there is no free carry. The dealer's daily P&L is, to a first approximation, gamma P&L (from re-hedging) plus theta (from the clock), and the entire question of whether a dealer is happy today reduces to whether realized movement exceeded what the theta paid for.

### 3.4 Vega — "what happens if the rate changes?"

Vega is the change in option value per one-point change in implied vol. The example put, with vega around **8.6 points per vol**, gains ~8.6 points if IV rises from 16 to 17 with the index unmoved.

Vega is the exposure to repricing of the risk itself — a rate-adequacy move rather than a loss event. It matters most for the second-order flows in Chapter 8: when implied vol *falls* after an event, every option's delta shifts, and dealers must re-hedge even though the index has not moved. That re-hedging is the vanna flow, and it is the mechanism behind the post-Fed melt-up in the report's own narrative.

### 3.5 The two the report will add later — charm and vanna

**Charm** is the change in delta per day (∂Δ/∂t). Out-of-the-money options lose delta as expiry approaches; in-the-money options gain it. **Vanna** is the change in delta per one-point change in vol (∂Δ/∂σ). Out-of-the-money options lose delta magnitude as vol falls. Both are second-order — they describe how the hedge ratio drifts for reasons other than spot moving — and both generate systematic dealer flows at predictable times. They are listed in the Daily Cascade backlog (item 6) and get their full treatment in Chapter 8.

### 3.6 The Greeks in one table, for the running example

| Greek | 7,500 put, 30d, 16 vol, spot 7,500 | Plain reading |
|---|---|---|
| Price | 137 | 1.8% of notional for 30 days |
| Delta | −0.50 | Half an index-unit of short exposure per unit |
| Gamma | 0.0010 /pt | 1% move shifts delta by ~0.08 |
| Theta | −2.3 /day | Premium earned by the writer daily |
| Vega | 8.6 /vol | One vol point ≈ 8.6 points of price |

Everything in Part II is what happens when one participant is on the other side of ten thousand of these.


---

# PART II — THE DEALER

---

## CHAPTER 4 — WHO IS ON THE OTHER SIDE

### 4.1 The market maker's business

When the portfolio manager in Chapter 1 buys 100 puts, someone sells them. Occasionally that someone is another end-user with the opposite view. Overwhelmingly it is a **market maker** — Citadel Securities, Susquehanna, Optiver, Jane Street, IMC, Wolverine, and a handful of others who quote continuous two-sided markets in every listed strike. The report calls them "dealers." The word is right: they deal in options the way a bond dealer deals in bonds, and they want the same thing a bond dealer wants — **the bid-ask spread, repeated millions of times, with as little directional risk as possible.**

This is the single most important fact about dealers, and everything in the report depends on it: **the dealer does not want to be long or short the market. The dealer wants to be flat.** A dealer who sold 100 puts has a directional position they did not choose and do not want. They will get rid of it — not by finding a buyer for the puts, which would surrender the spread they just earned, but by **hedging the delta in the underlying**.

The insurance reading: the dealer is a fronting carrier. They write the policy for the fee, then immediately cede the expected loss. What they keep is the fronting fee (the spread), the development risk (gamma), and the rate-change risk (vega). They are compensated for warehousing convexity, not for taking a view.

### 4.2 The delta hedge, worked

The manager buys 100 contracts of the 7,500 put. The dealer is now **short 100 puts**. In index-units:

- Short 100 contracts × 100 units × (−0.50 delta) = the dealer's position has delta of **+5,000 units** (short a negative-delta instrument = positive delta; the dealer is effectively long 5,000 units of index).
- To be flat, the dealer must **sell 5,000 units** = **sell 100 ES contracts** (each ES is 50 units).

The dealer sells 100 ES. Net delta: zero. They have locked in the spread and, for the moment, have no directional exposure.

*For the moment.* Gamma is 0.0010 per point. The index moves. The hedge is no longer right.

### 4.3 The hedge drifts — and the drift is the whole story

**The index falls 1%, to 7,425.** The put's delta moves from −0.50 to about −0.58. The dealer's short-put position now has delta of +5,800 units — they are long 5,800, hedged with only 100 ES (5,000 units short). They are net long 800 units into a falling market. To get flat: **sell 16 more ES.**

**The index rises 1%, to 7,575.** Delta moves to −0.42. The dealer's position delta is now +4,200; they are short 5,000 via ES. Net short 800 into a rising market. To get flat: **buy back 16 ES.**

Write down what just happened. The dealer, short puts, **sold into the decline and bought into the rally.** Their hedging *chased* the market in both directions. Every 1% move forced roughly 16 ES contracts of trading in the *same direction as the move*, from a participant who did not want any directional exposure at all.

That is **dealer short gamma**, and its market effect is amplification.

### 4.4 The mirror image

Now suppose instead that the manager *sells* 100 calls at 7,500 — an overwrite, collecting 137 points of premium against the portfolio. The dealer is now **long 100 calls**, delta +0.50 each: position delta +5,000 units. Hedge: **sell 100 ES.** Flat.

**The index falls 1%.** Call delta drops to 0.42. Dealer position delta +4,200; still short 5,000 via ES; net short 800 into a falling market. To get flat: **buy 16 ES.** The dealer bought the dip.

**The index rises 1%.** Call delta rises to 0.58. Position delta +5,800; short only 5,000. Net long 800 into a rally. To get flat: **sell 16 ES.** The dealer sold the rip.

This dealer **bought weakness and sold strength**, mechanically, every time the market moved. That is **dealer long gamma**, and its market effect is suppression.

**The ledger, in numbers.** The two hedging sequences of 4.3 and 4.4, walked through a full round trip — down 1%, back, up 1%, back — for the short-gamma dealer of 4.3 (short 100 puts, initial hedge: short 100 ES):

| Step | Spot | Put delta | Position delta (units) | Hedge required | Trade forced |
|---|---|---|---|---|---|
| 1 | 7,500 | −0.50 | +5,000 | short 100 ES | sell 100 ES @ 7,500 (initial) |
| 2 | 7,425 | −0.58 | +5,800 | short 116 ES | **sell 16 ES @ 7,425** |
| 3 | 7,500 | −0.50 | +5,000 | short 100 ES | **buy 16 ES @ 7,500** |
| 4 | 7,575 | −0.42 | +4,200 | short 84 ES | **buy 16 ES @ 7,575** |
| 5 | 7,500 | −0.50 | +5,000 | short 100 ES | **sell 16 ES @ 7,500** |

Steps 2–3 sold low and bought high: 16 contracts × 75 points × $50 = **$60,000 paid**. Steps 4–5 bought high and sold low: another **$60,000**. The round trip cost the short-gamma dealer $120,000 in forced re-hedging — that is gamma P&L, paid to the market — against roughly $23,000 a day collected in theta (100 contracts × 2.3 points × $100). The long-gamma dealer of 4.4 ran the identical table with every trade reversed: **earned** the $120,000 and **paid** the theta. One table, two businesses: the short-gamma dealer is a carrier praying for a quiet day; the long-gamma dealer owns convexity and is praying for a loud one.

### 4.5 The one table

| Dealer position | Dealer gamma | As index rises, dealer must… | As index falls, dealer must… | Effect on the market |
|---|---|---|---|---|
| Long options (long calls or long puts) | Long (positive) | Sell | Buy | Counter-trend → **stabilizing**, range-bound, mean-reverting |
| Short options (short calls or short puts) | Short (negative) | Buy | Sell | Pro-trend → **amplifying**, trending, volatile |

Notice what is *not* in the table: whether the option is a call or a put. It does not matter. A dealer long a 7,500 call and a dealer long a 7,500 put hedge identically (put-call parity, Chapter 1.4). What matters is only whether the dealer is **long or short convexity**. That is why the aggregate metric is *gamma* exposure and not call-or-put exposure.

### 4.6 What the dealer earns and loses

The long-gamma dealer in 4.4 bought 16 ES at 7,425 and would sell 16 ES at 7,575 if the market round-tripped. That is gamma P&L — the dealer is paid by the market's movement. In exchange they pay theta: 2.3 points a day on 100 contracts is $23,000 a day bleeding out of the position. If the market moves *more* than the theta paid for (realized vol > implied), the long-gamma dealer wins. If it moves less, they lose.

The short-gamma dealer in 4.3 is the reverse: they collect the $23,000 a day and pay for every move. Calm markets are their business; violent ones are their catastrophe.

This is exactly the underwriting cycle. A book of short gamma is a book of written policies collecting premium; it makes money in quiet years and loses in loss years. The dealer community's aggregate gamma position is the industry's aggregate net-written position, and GEX is the number that says whether the industry as a whole is currently a net writer or a net buyer of convexity — and therefore whether its collective hedging will calm the market or feed it.

---

## CHAPTER 5 — THE TWO WORLDS

*Chapter 4 showed the mechanic for one dealer and one strike. This chapter describes what the market looks like from inside each regime, because the difference is not a matter of degree.*

*(Figure 6 — The two worlds: the same shocks, two regimes — see the HTML edition for the chart.)*

### 5.1 The positive-gamma world

When dealers are net long gamma across the market, every uptick is met with mechanical selling and every downtick with mechanical buying. The consequences are precisely the ones the report's current regime displays:

- **Realized volatility is suppressed** below what fundamentals alone would produce. Ranges compress. The index "grinds."
- **Mean reversion dominates.** Extremes get faded not because anyone thinks the extreme is wrong but because someone is *forced* to fade it.
- **Levels hold.** A strike with large dealer long gamma generates its own defense.
- **Intraday character is choppy-but-contained**; big moves require a catalyst strong enough to overwhelm the hedging flow, and even then the flow slows the move.
- **Short-vol strategies work** (they are selling into a regime that suppresses the thing they are short). Breakout strategies fail (the breakout gets sold by dealers before it can run).

The trader's posture: **fade extremes, buy dips at gamma support, sell rallies at gamma resistance, size for the range, expect the pin.** The Daily Cascade paper's dip-buy setup at 7,468–7,475 is a positive-gamma trade.

### 5.2 The negative-gamma world

When dealers are net short gamma, the same mechanic runs in reverse. Every uptick is met with mechanical buying and every downtick with mechanical selling:

- **Realized volatility expands.** Moves that would have been 0.5% become 1.5%.
- **Trends persist.** Momentum is *created* by the hedging, not merely permitted.
- **Levels fail.** Support becomes the place the selling accelerates, because breaking it triggers more dealer selling.
- **Gaps and air pockets** appear, because dealers hedge discretely in fast markets and their late hedges land on top of each other.
- **Short-vol strategies get destroyed** (February 2018, March 2020). Breakout and momentum strategies work.

The trader's posture: **trade breakouts, respect momentum, widen stops, cut size in half, expect follow-through.** Fading an extreme in negative gamma is stepping in front of forced flow.

### 5.3 Why "positive gamma is bullish" is the cardinal error

The Daily Cascade paper flagged this as §06's most common misreading; here is the mechanism that makes it wrong. Positive gamma suppresses *both* directions. It sells rallies as hard as it buys dips. A market in deep positive gamma is not a market that wants to go up; it is a market that does not want to go *anywhere*. The regime is a statement about **volatility and path**, never about direction. Direction comes from the catalyst and from where spot sits relative to the walls. If you find yourself long *because* GEX is positive, you have confused the road conditions with the destination.

### 5.4 The transition, and why it is non-linear

The regime does not change smoothly. Dealer gamma is a function of spot (Chapter 6), and as spot declines through the strikes where dealers are long gamma into the strikes where they are short, the aggregate flips sign — often within a few dozen points. Above the flip, a 1% decline is met with buying; below it, the *same* decline is met with selling. The market can go from suppressed to amplified across a single level, which is why the gamma flip is the report's regime boundary and why Rule 2.7.1 gates strategy on distance from it. It is also why regime transitions are the system's correlated failure mode (Daily Cascade Chapter 23, item 1): every mean-reversion tool stops working at the same price.

---

## CHAPTER 6 — AGGREGATING TO THE MARKET: GEX

### 6.1 From one dealer to the industry

Chapter 4 hedged one dealer's 100 contracts. The market has tens of millions of contracts of open interest across hundreds of strikes and dozens of expiries. **Gamma Exposure (GEX)** is the attempt to sum all of it into one number: the aggregate gamma the dealer community holds, signed, expressed in dollars of underlying that must be traded per 1% move.

The per-strike formula, in the standard form:

**GEX(strike) = Γ × OI × 100 × S² × 0.01 × (sign)**

where Γ is the option's gamma, OI is open interest in contracts, 100 is the contract multiplier, S² × 0.01 converts per-point gamma into dollars per 1% move, and the sign reflects whether dealers are assumed long or short that strike's gamma.

**Worked:** the 7,500 strike has 20,000 contracts of call open interest, gamma 0.0012, spot 7,500.
0.0012 × 20,000 × 100 × 7,500² × 0.01 = 0.0012 × 20,000 × 100 × 56,250,000 × 0.01 ≈ **$1.35 billion.**

Plain reading: **for every 1% the index moves, dealers holding this one strike must trade roughly $1.35 billion of underlying.** Sum across every strike and expiry and you have the report's 0700 headline: net GEX **+$13.8B** means that a 1% index move obliges the dealer community, in aggregate, to transact about $13.8 billion of index *against* the direction of the move. That is a large number relative to typical daily ES liquidity, and it is why the regime label is not a metaphor.

### 6.2 The sign assumption — and a correction

Open interest data tells you *how many* contracts exist at a strike. It does not tell you who is long and who is short. GEX therefore requires an assumption about which side the dealer is on, and this assumption is the model's load-bearing wall.

**The standard ("naive") convention**, introduced by SqueezeMetrics and used with refinements by SpotGamma and others:

- **Customers sell calls** (overwriting, yield enhancement, covered-call funds). Therefore **dealers are long calls** → call gamma counts **positive**.
- **Customers buy puts** (portfolio protection, the manager in Chapter 1). Therefore **dealers are short puts** → put gamma counts **negative**.

**Net GEX = Σ(call gamma × OI) − Σ(put gamma × OI)**, scaled as above.

Daily Cascade Chapter 2.3 states this convention in summary and notes that it is reasonable on average and wrong in specific cases, most visibly around the JHEQX roll. This chapter is where the convention is derived; Chapter 10 works through exactly why the JHEQX exception arises.

The naive convention has an immediate structural consequence. Call open interest concentrates *above* spot (people overwrite above the market); put open interest concentrates *below* spot (people protect below the market). Therefore:

- **Above spot, GEX tends to be positive** (dealer long call gamma dominates).
- **Below spot, GEX tends to be negative** (dealer short put gamma dominates).
- **The gamma flip** — where the sum crosses zero — therefore normally sits *below* spot in a rising market, and the market crosses into negative gamma by *falling* through it. The report's flip at 7,403 with spot at 7,489 is the textbook configuration.

### 6.3 What the vendors do differently

The naive model is a first approximation, and every serious vendor modifies it. Common refinements: inferring dealer position from the trade tape (did the trade print at the bid or the ask?), adjusting for known institutional structures (the JHEQX collar, index-fund overwriting programs), weighting by expiry, and modeling the 0DTE book separately. **Different vendors publish materially different GEX figures for the same day** — routinely disagreeing by tens of percent on magnitude and occasionally on sign near the flip. This is not a flaw to be embarrassed about; it is the honest consequence of inferring a hidden variable. The Daily Cascade backlog's top data item (vendor cross-check) exists because of this paragraph.

The practical hierarchy of reliability: **the sign of net GEX is the most robust output; the direction of change across the day is next; the location of the largest walls is next; the precise dollar magnitude is least.** Trade accordingly.

### 6.4 Reading the gamma profile

Plotted by strike, dealer gamma is a landscape: tall positive peaks at the strikes with heavy call OI above spot, deep negative troughs at heavy put strikes below, and the flip where the running sum crosses zero. Four features of that landscape are named in the report, and each has a mechanical meaning that the next chapter spells out — because two of them have cleaner mechanics than the other two, and knowing which is which is worth real money.

*(Figure 7 — The GEX landscape on the reference Friday — see the HTML edition for the chart.)*

---

## CHAPTER 7 — THE LEVELS: WALLS, FLIP, PEAK, MAX PAIN

### 7.1 The call wall — clean mechanics

The call wall is the strike with the largest positive (dealer-long-call) gamma. Its behavior as resistance follows directly from Chapter 4.4:

As spot rises toward the wall, dealer long-call deltas grow (gamma is largest near the strike), so dealers must **sell** increasingly large amounts of index to stay flat. The closer spot gets, the heavier the selling. This is resistance generated by forced flow, not by opinion. It is the cleanest mechanical level in the entire framework.

Two corollaries. First, **above the wall, gamma declines** (delta approaches 1 and stops changing), so the selling pressure *fades* once the wall is decisively cleared. A call wall that breaks on a catalyst can therefore produce a fast move — the resistance was the flow, and the flow is gone. Second, **the wall migrates**: as spot rises, new call overwriting arrives at higher strikes and the wall rolls up with it. The report's FRI 1800 reset table (call wall 7,500 → 7,540) is this migration observed.

### 7.2 The put wall — a positioning level with hybrid mechanics

The put wall is the strike with the largest put open interest, and it is conventionally described as support. Its mechanics are honestly messier, and the difference matters.

Under the naive convention dealers are *short* the puts at that strike. Short puts are short gamma. As spot falls *toward* the put wall, the dealer's short-put deltas grow in magnitude, forcing them to **sell** — pro-cyclical, the opposite of support. The pure gamma story says the put wall is where hedging *accelerates* a decline, not where it stops it.

So why does the level hold as often as it does? Three mechanisms that are not gamma:

- **Monetization.** The put wall is where the largest protective positions sit. As spot approaches, holders who bought those puts at 137 now hold them at 250 and sell some — taking profit on the hedge. When a customer sells a put back to the dealer, the dealer covers the ES they had sold as a hedge: **dealer buying**. The support comes from the *unwinding* of the hedge, not from the hedge itself.
- **The vol dynamics of a bounce.** When spot stabilizes at the wall, implied vol falls, and falling vol shrinks put deltas (vanna, Chapter 8), which forces dealers to buy back hedges. A pause becomes a bounce mechanically.
- **Reflexivity.** The level is watched, so it is defended.

The trading consequence: **the put wall is a legitimate level and a legitimate dip-buy zone, but it is a different kind of level from the call wall.** A call wall's resistance is present *before* spot arrives. A put wall's support is contingent on holders monetizing and vol behaving. When neither happens — a catalyst-driven decline where hedgers *add* rather than monetize and vol rises rather than falls — the put wall is precisely where the pure gamma mechanics take over and the decline accelerates. That is why the Daily Cascade paper's Rule 2.7.1 gates everything on distance from the *flip*, not the put wall, and why breaks of the put wall are treated as regime information rather than as a missed dip-buy.

### 7.3 Peak GEX — the magnet

The strike with the largest total gamma, calls and puts combined, is where dealer hedging flow is most intense. In a positive-gamma regime it acts as a **magnet**: moves away from it in either direction meet the strongest counter-flow, and spot tends to return to it, particularly into the close when 0DTE gamma is at its peak. The report's identification of 7,475 as the gravitational center is this. Peak GEX is a *destination*, not a boundary — the difference between it and a wall is that a wall is somewhere spot has trouble crossing while peak GEX is somewhere spot has trouble leaving.

### 7.4 Max pain — a coincidence worth knowing

Max pain is the strike at which the aggregate dollar value of expiring options is minimized: the price where the most contracts finish worthless. The folk theory holds that price is somehow steered there. There is no mechanism for that and the empirical support is weak.

What *is* true: max pain is computed from open interest, and open interest concentrates where gamma concentrates. So max pain and peak GEX frequently coincide — the report shows both at 7,475 — and when they do, the level is meaningful *because of the gamma*, not because of the pain. When they diverge, trust peak GEX and treat max pain as noise. The Daily Cascade paper's framing ("the two frequently point at the same price for different and better reasons") is exact.

### 7.5 The flip — the boundary

Everything in Chapter 5 turns on this level. Its mechanics are simply the running sum of 6.4 crossing zero. Two things about its behavior that the aggregate number hides:

**It moves.** Every new trade shifts it. Heavy put buying pulls it up toward spot (more negative gamma below); heavy call overwriting pushes it down (more positive gamma above). The report tracks the flip's delta between reports (7,408 → 7,403) precisely because the *movement* is a leading indicator: a flip rising toward spot while spot is flat means the stabilizing cushion is thinning from underneath. Rule 2.7.5 in the other paper is the operational version.

**Crossing it is not an event; being below it is a condition.** The market does not crash on crossing the flip. It changes *character* — from suppressed to amplified — and the change is visible in the next several moves, not the crossing itself. Traders who treat the flip as a trapdoor overreact at the level and then underreact to the regime they are now in. The correct response to a flip break is not a trade; it is a **change of playbook** (Chapter 14).

### 7.6 The levels, summarized by mechanism

| Level | Mechanism | Reliability | Use |
|---|---|---|---|
| Call wall | Dealer long-call hedging sells into rallies — pure gamma | High, and present before spot arrives | Resistance; fade zone; break = squeeze candidate |
| Put wall | Monetization + vanna + reflexivity; pure gamma is *against* it | Medium, contingent on holders' behavior | Dip-buy zone with a hard stop below; break = regime information |
| Peak GEX | Maximum counter-flow | High in positive regime | Magnet; pin target into close |
| Max pain | Coincides with OI concentration | Low on its own | Confirm peak GEX; ignore if divergent |
| Gamma flip | Running sum crosses zero | High as a regime boundary; drifts | Strategy gate; hard invalidation; track its movement |


---

## CHAPTER 8 — DEX, VANNA, AND CHARM: THE FLOWS THAT DON'T NEED SPOT TO MOVE

### 8.1 Delta exposure — the positioning read

Gamma tells you what dealers will be *forced* to do as spot moves. **Delta Exposure (DEX)** tells you what they are *already* holding. It is the aggregate delta of the dealer book, signed — and because dealers hedge, it is a mirror of what customers are holding.

Large positive DEX means dealers are net long delta through their option inventory and have hedged by being short a great deal of index. In customer terms: the market is heavily positioned long calls (dealers short calls, long index hedges) or short puts. Large negative DEX means the reverse — customers are long protection, dealers are long index against it.

DEX is not a flow forecast. It is a **positioning snapshot** and it answers a different question than GEX: not "what happens when spot moves" but "how crowded is the boat." A market with very high positive DEX is one where a great deal of directional bullish optionality has been bought; the hedges against it are already in place, and if the market falls, the customers' calls decay, dealers' hedges are unwound (buying back short index — supportive), but the customers themselves are the fragility. The Daily Cascade paper's Rule 2.7 setups halve size on "crowded positioning"; DEX is where that reading comes from.

### 8.2 Vanna — the flow when vol moves

Recall from Chapter 3.5: vanna is the sensitivity of delta to implied vol. For out-of-the-money options, **falling vol shrinks delta magnitude**. An OTM put that had −0.25 delta at 20 vol might have −0.18 delta at 15 vol, with spot unchanged.

Now run the dealer's book through a vol crush. The dealer is short OTM puts (the naive assumption), hedged by being short index. Vol falls — say a feared event passes benignly. Every OTM put's delta magnitude shrinks. The dealer's short-put position needs *less* short index against it. **The dealer buys back index.** Across the whole book, this is a systematic, mechanical bid that appears purely because vol fell — spot did not need to move first.

This is the **vanna rally**, and it is the mechanism behind one of the most reliable patterns in the report's own narrative: the post-event melt-up. When the Fed minutes at 2:00 PM on the report's Friday came in dovish, implied vol collapsed; the put hedges every institution had bought into the event shrank in delta; dealers covered their index shorts; and the market ran to 7,518 — not only because the news was good, but because the *vol* falling generated forced buying regardless of the news's content. A benign outcome to any feared binary produces this bid; the size of it scales with how much protection was bought beforehand.

*(Figure 8 — Vanna: the hedge shrinks when vol falls — see the HTML edition for the chart.)*

The mirror exists: a **vanna selloff** when vol *rises* — put deltas grow, dealers must sell more index to stay hedged, and a modest decline gets an extra push from the vol move itself. This is the amplification channel that makes negative-gamma declines worse than the gamma alone would predict.

### 8.3 Charm — the flow when time passes

Charm is the sensitivity of delta to time. OTM options lose delta as expiry approaches (an OTM option is increasingly certain to expire worthless, so it behaves less and less like the index). ITM options gain delta.

The dealer book is, on the naive assumption, long OTM calls and short OTM puts. As time passes:

- The long OTM calls lose delta → the dealer's position delta falls → they had sold index against it → **they buy back index.**
- The short OTM puts lose delta magnitude → the dealer's position delta (which was positive from being short puts) falls → they had sold index → **they buy back index.**

Both legs produce buying. This is the **charm bid**: a systematic drift of dealer buying into expiration in a positive-gamma regime, strongest in the final hours of the final days. It is one candidate mechanism for the well-documented tendency of the index to drift higher into Friday closes and into monthly opex during calm regimes, and for the muted downside on quiet afternoons. It is small per hour and large in aggregate.

The trading value: charm and vanna are **time-and-vol-driven flows that are directionally predictable in advance**, unlike gamma flows which require spot to move first. In a positive-gamma regime with a feared event behind you and expiry ahead, both point the same way, and the Daily Cascade backlog lists them as the top Tier 2 refinement for exactly that reason. Chapter 15's sixth setup trades them.

### 8.4 The second-order flows in one table

| Flow | Trigger | Dealer action (naive book) | Market effect | When it dominates |
|---|---|---|---|---|
| Gamma | Spot moves | Counter-trend (long γ) or pro-trend (short γ) | Suppression or amplification | Always; intraday |
| Vanna | Vol moves | Vol ↓ → buy index; vol ↑ → sell index | Post-event melt-ups; vol-spike air pockets | Around catalysts |
| Charm | Time passes | Buy index as OTM deltas decay | Drift into expiry; Friday-afternoon bid | Final days before opex; late session |
| DEX (not a flow) | — | Positioning snapshot | Crowding measure | Sizing input |

---

## CHAPTER 9 — THE 0DTE REGIME

### 9.1 What changed

As of 2026, options expiring the same day account for roughly 50–63% of total SPX options volume on a typical session, per Cboe data, up from about 20% in 2020; total 0DTE volume across the options market exceeded 20 million contracts per day in Q2 2026 (Cboe, *State of the Options Industry*, July 2026). Daily expirations in SPX were introduced in 2022 and the volume migrated with remarkable speed. **The intraday gamma landscape is now dominated by contracts that did not exist at yesterday's close and will not exist at tonight's.**

### 9.2 Why 0DTE gamma is different in kind

Return to Chapter 3.2. Gamma explodes as expiry approaches, because the delta of an at-the-money option must travel from ~0.5 to either 0 or 1 across an ever-narrower range as time runs out. In the final hours, a 0DTE ATM option has gamma many times that of a monthly at the same strike. Three consequences:

**Enormous but transient.** The report shows 0DTE at 68% of total GEX on the Friday afternoon — the intraday structure is mostly same-day contracts — and then resets to ~25% Monday morning as the new day's book builds. A 0DTE call wall at 7,500 is real at 2:00 PM and gone at 4:00 PM. **Rule 2.7.7 — never carry a position overnight on the strength of a 0DTE level — exists because the level literally ceases to exist.**

**Pins are strongest in the last hour.** With gamma at its maximum, dealer counter-flow around peak GEX is most intense in the final 60–90 minutes, and the index's tendency to close near the largest 0DTE strike is a genuine, measurable regularity in positive-gamma regimes. The Daily Cascade backlog's "log the pin" item is the plan to turn that regularity into a base rate.

**The structure moves within the day.** Morning 0DTE levels have a half-life of hours. A large 0DTE call purchase at 11:00 AM can relocate the intraday call wall; the 0920/1000/1200/1500 delta tables exist to catch this, and the 1500 report's reading of the late-day structure is the highest-value 0DTE read in the cascade, because by 3:00 PM the day's 0DTE positioning is nearly complete and the expiry dynamics are about to dominate.

*(Figure 9 — The 0DTE delta cliff — see the HTML edition for the chart.)*

The same fact as a table — the call's delta at two prices ten points apart, as the clock runs down:

| Time to expiry | Delta at 7,495 | Delta at 7,505 | Δ per 10 points | Dealer meaning |
|---|---|---|---|---|
| 30 days | 0.50 | 0.51 | ~0.01 | hedge drifts; re-hedge at leisure |
| Final hour | 0.43 | 0.57 | ~0.13 | hedge swings; re-hedge continuously |
| Final 10 minutes | 0.34 | 0.66 | ~0.32 | hedge snaps; the pin fight |

### 9.3 Who trades it and what that implies

The 0DTE book is a mix of systematic institutional strategies (premium harvesting, intraday hedging, event trades), market-maker inventory, and a large retail cohort that arrived after 2022. Cboe's own analysis has repeatedly found that 0DTE flow is roughly balanced between buying and selling and that its net gamma effect on the market is smaller than the volume suggests — which is consistent with the naive-model observation that dealer 0DTE gamma is often close to flat until late in the session when one side has clearly won. **The practical implication: 0DTE levels matter most when the 0DTE book is lopsided, which is a late-day phenomenon.** Morning 0DTE readings should be held loosely.

### 9.4 The 0DTE reading protocol

- **Before 11:00 AM:** monthly and weekly levels govern. 0DTE is context.
- **11:00 AM – 2:00 PM:** watch the 0DTE call and put walls in the delta tables; a wall that has held for two hours is credible.
- **After 2:00 PM:** 0DTE governs. Peak GEX / max pain convergence is the pin target. The report's 3:00 PM read is the one to trade from.
- **Last 30 minutes:** gamma at maximum; the pin is strongest; MOC imbalances can overwhelm it. Do not initiate; manage.
- **At the close:** every 0DTE level is void. Tomorrow starts from the monthly and weekly map.

---

## CHAPTER 10 — THE EXPIRATION CALENDAR

### 10.1 The buckets, and why the report separates them

The §06 table splits GEX into 0DTE, weekly, monthly, and quarterly for a structural reason: **each bucket has a different shelf life and a different dominant participant**, so the same dollar of gamma means different things depending on when it expires.

- **0DTE** — hours. Intraday traders and systematic programs. Chapter 9.
- **Weekly** (Monday, Wednesday, Friday expiries) — days. Tactical hedgers, event traders. Defines the structure for the current week.
- **Monthly** (third Friday) — weeks. The largest and most institutional bucket: portfolio hedges, overwriting programs, structured-product hedges. **This is the structural map.** The monthly gamma flip is the regime boundary in Rule 2.7.1 because the monthly book is the one that persists.
- **Quarterly** (third Friday of March/June/September/December) — months. Dominated by a handful of enormous systematic positions, the largest of which is the JPMorgan collar.

### 10.2 Opex week — the monthly gamma cycle

Because the monthly bucket is the largest, its expiration produces a recognizable cycle:

**Into opex.** Gamma at the monthly strikes is at its peak in the final week. If the regime is positive, pins strengthen, ranges compress, and the charm bid (Chapter 8.3) is at its most persistent. The week before monthly expiry is, in calm regimes, statistically among the quietest.

**Opex Friday.** A large fraction of the market's total gamma expires at once. Whatever the monthly book was doing to spot — pinning it, suppressing it — stops at the close.

**The week after.** With the monthly cushion gone and the new month's book not yet built, aggregate gamma is at its cycle low. This is the "opex unclench": the market is freer to move, in either direction, in the sessions after monthly expiry than at any other point in the cycle. Several well-known post-opex selloffs and rallies are this mechanism. The FRI 1800 report's "GEX Reset" table (+$17.4B pre-expiry → ~$5.8B post) documents exactly this drop for a weekly expiry; the monthly version is larger.

Trading consequence: **the same GEX reading means less in the week after opex than in the week before it**, because the structure is thinner and rebuilds fast. The regime gate still applies; the confidence in the levels should be lower.

*(Figure 10 — The monthly gamma cycle — see the HTML edition for the chart.)*

### 10.3 The JPMorgan collar — the quarterly bookends

The JPMorgan Hedged Equity Fund (JHEQX, with sibling funds on staggered schedules) is a large mutual fund that holds an S&P 500 portfolio and, every quarter, resets a **collar** on it: it **buys a put spread** (long a put roughly 5% below the market, short a put roughly 20% below — a layer that attaches at 95 and exhausts at 80) and **sells a call** roughly 3–5% above, all expiring at the next quarterly opex. The call premium funds the put spread. The fund's size means each leg is tens of thousands of SPX contracts — among the largest single positions in the market, and fully public.

Run it through the dealer's book. The dealer is on the other side of all three legs:

- **Short the ~95% put** (the fund bought it) → dealer short gamma there.
- **Long the ~80% put** (the fund sold it) → dealer long gamma there.
- **Long the ~105% call** (the fund sold it) → dealer long call gamma → **the dealer sells into any rally approaching that strike.**

That last leg is the famous "JPM collar ceiling." For three months, a very large block of dealer long-call gamma sits a few percent above where the market was at the roll date, generating mechanical selling as the index approaches it. When the market has rallied hard within a quarter, the collar strike can become the dominant resistance in the entire book. The report lists the current strikes (7,600 / 7,250 / 7,100) as structural endpoints and correctly ignores them day to day — Rule 2.7.8 — because they only bind when spot is within about 2% of a leg.

*(Figure 11 — The JHEQX collar at expiry — see the HTML edition for the chart.)*

Two further points. **The roll itself is an event.** On the last trading day of each quarter the fund closes the old collar and opens the new one; the resulting flow (tens of thousands of contracts crossing, dealers re-hedging) is large enough to move the index intraday and is widely watched. **And this position is the clearest case where the naive sign convention is wrong.** The fund *sold* the call — so the customer is short calls and the dealer is long, which matches the naive assumption. But the fund *bought* the 95% put and *sold* the 80% put — so at the 80% strike the customer is short a put and the dealer is *long*, which is the opposite of the naive assumption. Any vendor that does not hand-adjust for this position mis-signs a large block of gamma. This is the concrete example the Daily Cascade paper gestured at.

### 10.4 VIX expiration and the ancillary calendar

VIX options and futures settle on Wednesday mornings (monthly, plus weeklies), on a special opening quotation of SPX options. The settlement print is a known source of early-morning SPX option activity and occasionally of an anomalous open. It is worth knowing the date; it is not worth trading. The same goes for index rebalance days and the monthly equity-index futures roll (the week before quarterly expiry, when open interest migrates from the front ES contract to the next): each produces predictable, transient distortion in the basis and in reported GEX, and the correct response is to know it is happening rather than to interpret it.

### 10.5 The calendar in one table

| Expiry | Cadence | Who dominates | GEX shelf life | Report treatment |
|---|---|---|---|---|
| 0DTE | Daily | Intraday systematic + retail | Hours | Pin target after 2 PM; void at close |
| Weekly | Mon/Wed/Fri | Tactical hedgers, event trades | Days | Current-week structure |
| Monthly | 3rd Friday | Institutional hedges, overwriting | Weeks | **The regime map; flip = boundary** |
| Quarterly | Mar/Jun/Sep/Dec | JHEQX and similar | Months | Bookends; ignore unless within ~2% |
| VIX settlement | Wednesdays | Vol desks | — | Know the date; do not trade it |


---

# PART III — READING §06

*The section as printed in the 0700 report on the reference Friday, taken line by line. Every number is reconciled to a mechanism from Part II. The goal is that after this chapter the section reads as a map rather than a table.*

---

## CHAPTER 11 — THE SECTION, LINE BY LINE

### 11.1 The header rows

**Basis (/ES − SPX cash): +14.0 — normal carry.** The June futures trade 14 points above the cash index. That premium is the cost of carry — the financing cost of holding the index to the June expiry, less the dividends you would collect — and 14 points on 7,489 is about 0.19%, consistent with a few weeks of carry at prevailing rates. This row is a plumbing check. It has no directional content on a normal day. A basis that jumps or collapses without a rate move means either a funding dislocation or a very large index-arbitrage program crossing, and both are worth knowing before you trust any other level. The report grades it MED; that is right — it is a *gate*, not a signal.

**Expected Move (today): ±0.7% / ±52 pts (from ATM straddle).** Chapter 12 derives this. For now: the options market prices a one-standard-deviation day of about 52 points in either direction. Any target more than 52 points away requires a reason.

### 11.2 The delta table

| Field | Prior (4:30 PM) | Current (7:00 AM) | Δ |
|---|---|---|---|
| Net GEX | +$12.1B | +$13.8B | ▲ +$1.7B |
| Gamma Flip | 7,408 | 7,403 | ▼ −5.0 |
| Call Wall | 7,500 | 7,500 | — |
| 0DTE % of Total | — | 36% | — |

Read this table as a *trajectory*, not a snapshot — it is the stateful part of the section (Daily Cascade Chapter 22).

**Net GEX rose $1.7B overnight.** The dealer book got longer gamma while the market slept. Under the naive convention that means more call overwriting arrived, or protective puts were closed, or both — customers ceded more convexity to dealers. The stabilizing cushion thickened. This is a mild positive for the mean-reversion playbook.

**The flip fell 5 points, to 7,403.** The regime boundary moved *away* from spot. With spot at 7,489.50, the market sits 86.5 points (1.16%) inside the positive regime. Rule 2.7.1's "more than ~1% above the flip" condition is met with room to spare. The direction of the flip's movement (down, away) confirms the GEX read: the structure is strengthening, not eroding. Had the flip *risen* while net GEX rose — possible if new gamma arrived concentrated below spot — the two rows would disagree, and the disagreement would be the signal.

**The call wall held at 7,500.** No migration overnight. Resistance is where it was.

**0DTE is 36% of total.** At 7:00 AM, before the day's 0DTE book has built, same-day contracts already account for over a third of dealer gamma. That number will rise through the day (the 1500 report on the same Friday shows 68%). At 36%, the intraday structure is meaningful but not yet dominant; the weekly and monthly levels still carry most of the weight. By afternoon the balance inverts.

### 11.3 The ladder

Every named level, sorted by price, with spot inline. This is the map.

| Price | Level | Bucket | Mechanism (Part II) |
|---|---|---|---|
| 7,600 | Call Wall | QTRLY | JHEQX short-call leg; dealer long → resistance, but 1.5% away |
| **7,500** | **Call Wall** | **MNTHLY** | **Structural resistance — dealer long-call gamma sells into it** |
| 7,490 | Call Wall | 0DTE | Intraday resistance, half a point above spot |
| *7,489.50* | */ES spot* | — | — |
| 7,485 | Max Pain | WKLY | OI concentration; confirm only |
| **7,475** | **Peak GEX** | **0DTE** | **The magnet — maximum counter-flow** |
| 7,475 | Max Pain | 0DTE | Coincides with peak → the level is real |
| 7,470 | Max Pain | MNTHLY | OI concentration; confirm only |
| 7,468 | Gamma Flip | 0DTE | *The 0DTE book's own boundary — 21 points below spot* |
| 7,460 | Put Wall | 0DTE | Intraday support (hybrid mechanics, Ch. 7.2) |
| 7,450 | Put Wall | WKLY | Weekly support |
| 7,440 | Gamma Flip | WKLY | Weekly book's boundary |
| **7,403** | **Gamma Flip** | **MNTHLY** | **The regime boundary — hard invalidation** |
| 7,400 | Put Wall | MNTHLY | Structural support; below it, negative gamma |
| 7,250 | Gamma Flip | QTRLY | JHEQX structure; not actionable |
| 7,100 | Put Wall | QTRLY | JHEQX long-put leg; not actionable |

*(Figure 12 — The §06 ladder, drawn — see the HTML edition for the chart.)*

Five observations that the table makes visible and the raw numbers do not:

**First — the corridor.** Spot sits between the 0DTE put wall (7,460) and the 0DTE call wall (7,490): a 30-point intraday box, with the magnet at 7,475 in the lower third of it. Absent a catalyst, the mechanics of Chapter 7 say the day's path oscillates inside this box and gravitates toward 7,475 into the close. The report's "tight pin near magnet absent a catalyst" is this box read aloud.

**Second — the expected move exceeds the corridor.** ±52 points is wider than the 30-point box. The options market is pricing a one-sigma day that would break the 0DTE walls. That is not a contradiction; it is the market pricing the 2:00 PM FOMC minutes. The 0DTE structure describes the *pre-catalyst* tape; the expected move describes the *whole* day. Both are right, and reading them together tells you the morning will be pinned and the afternoon will not.

**Third — nested flips.** There is not one gamma flip; there are four, one per bucket, and they are at very different distances from spot. The 0DTE flip at 7,468 is only 21 points below; the monthly flip at 7,403 is 86 below. **Below 7,468, the 0DTE book turns short gamma even while the monthly book remains long.** That means a sharp intraday decline through 7,468 would see intraday hedging flip to amplifying *within* a structurally stabilizing regime — an intraday air pocket that the monthly structure would then catch at 7,440–7,400. The nested-flip reading is the most advanced thing in the ladder and the most useful: it says where an intraday move can *accelerate* even though the regime is intact. Trade the 0DTE flip as an intraday stop level; trade the monthly flip as the regime invalidation. They are different instruments.

**Fourth — convergence at 7,475.** Peak GEX (0DTE) and max pain (0DTE) coincide, with monthly max pain five points away and weekly max pain ten above. Four rows, one zone. The report's "gravitational center" is a five-row cluster, and Rule 2.7.2's convergence-level trade is built on it.

**Fifth — the walls at 7,500.** Monthly call wall, weekly call wall (from the bucket table), and monthly peak all sit at 7,500. That is a *three-bucket* convergence of resistance ten points above spot. It is the reason the setup in §23 is a dip-buy *toward the magnet* and not a breakout *through the wall*: the structure above spot is dense and the structure below is a soft cushion.

### 11.4 The bucket table

| Bucket | Net GEX | Peak | % Total | Call Wall | Put Wall | Flip |
|---|---|---|---|---|---|---|
| 0DTE | +$5.0B | 7,475 | 36% | 7,490 | 7,460 | 7,468 |
| Weekly | +$4.1B | 7,475 | 30% | 7,500 | 7,450 | 7,440 |
| Monthly | +$3.6B | 7,500 | 26% | 7,500 | 7,400 | 7,403 |
| Quarterly | +$1.1B | 7,600 | 8% | 7,600 | 7,100 | 7,250 |

The buckets sum to $13.8B, and every bucket is positive — there is no expiry at which dealers are net short gamma. This is a *uniformly* stabilizing book, which is a stronger statement than "net positive" (a net positive book can hide a short-gamma weekly inside a long-gamma monthly). The uniform sign is why the report grades the regime as intact without qualification.

Note the peaks: 0DTE and weekly peak at 7,475, monthly at 7,500. The shorter-dated gamma is centered slightly below spot, the structural gamma slightly above. The intraday magnet is below; the structural ceiling is above. That asymmetry — cushion below, wall above — is the shape of a market that grinds up slowly and gets sold at the top of the range, which is what the reference week's daily candles show.

### 11.5 The narrative rows

**"0DTE Read — Call/put gamma roughly balanced — expect tight pin near magnet absent a catalyst."** Chapter 9.3: when the 0DTE book is balanced, its net effect is small until one side wins; the pin is the default expectation and the catalyst is the exception. Correct, and graded LOW because it is an expectation, not a measurement.

**"Gamma Decay Narrative — AM: 0DTE dominant, tight mean-reversion to 7,475. By 2 PM the minutes hit just as 0DTE delta decays; structural levels reassert into the close."** This row is the section's forecast of *which bucket governs when*. Morning: 0DTE box. Afternoon: the catalyst breaks the box, and once it does, the 0DTE structure has been overwhelmed and the weekly/monthly levels (7,500 wall, 7,403 flip) are what remain. The 1500 report on the same day confirmed the sequence: the dovish surprise broke 7,500, net GEX rose to $17.4B as the market re-hedged long, and the day closed at 7,519 — above the morning's monthly wall, which had migrated by the Friday reset to 7,540.

---

## CHAPTER 12 — THE EXPECTED MOVE AND THE BASIS

### 12.1 Deriving ±52

The at-the-money straddle — buying both the call and the put at the strike nearest spot — is the purest expression of "how far will the index move, in either direction." Its price is the market's own estimate of the expected absolute move, with a small correction.

The report reads the 0DTE straddle: with /ES at 7,489.50 and the 7,490 strike straddle trading at roughly 52 points, the expected move is ±52. Two equivalent ways to get there:

**From the straddle directly:** Expected move ≈ straddle price. A refinement many desks use is straddle × 0.85 for the one-sigma figure and straddle × 1.0 for the "expected absolute move" — the two differ by a normal-distribution constant (E|X| = σ × √(2/π) ≈ 0.8σ). The report's ±52 is the straddle price used as the expected move; the one-sigma equivalent is ~61.

**From implied vol:** 7,489.50 × IV_daily. With the 0DTE ATM implied vol around 11% annualized (0DTE vol typically trades below the 30-day VIX on calm mornings), the daily sigma is 7,489.50 × 0.11 ÷ √252 ≈ 52. The two methods agree, as they must — the straddle *is* the vol, quoted in points.

*(Figure 13 — Expected move versus the 0DTE corridor — see the HTML edition for the chart.)*

### 12.2 Using it

**As a sizing denominator.** A position sized to risk a fixed dollar amount per one-sigma day is a position whose risk is comparable across regimes. When the expected move is 52, a 26-point stop is half a sigma; when it is 90, the same 26-point stop is under a third of a sigma and will be hit by noise. Size the stop to the expected move, not to the chart.

**As a target ceiling.** Rule 2.7.4: primary targets inside the expected move unless a catalyst justifies more. The reference Friday's target 1 at 7,500 was 10 points above the entry zone — well inside — and target 2 at 7,540 required the catalyst, which arrived.

**As a probability statement.** The index closes inside the expected move about 68% of days *if the options market is calibrated*. It is, roughly, over long samples — and the deviations are informative: stretches where the index repeatedly closes inside a shrinking expected move are the positive-gamma grind; stretches where it repeatedly breaks a widening one are regime transitions.

### 12.3 The basis, briefly

/ES − SPX cash = +14.0. The futures price equals the cash index plus financing minus dividends, to expiry. When rates are 4% and the dividend yield is 1.3%, the annualized carry is about 2.7%, and for a contract with a few weeks to run the premium is a few tenths of a percent — 14 points on 7,489 is 0.19%, in range. The basis contracts toward zero into expiry and resets on the roll.

When it is not in range — a sudden 30-point premium, or a discount — something is happening in funding or in flow that the options data cannot see, and it should freeze new positions until understood. The row is graded MED because the *normal* reading is uninformative and the *abnormal* reading is an override.

---

## CHAPTER 13 — READING THE DELTAS ACROSS THE DAY

*§06 appears in every intraday report, and after 0700 it appears as deltas only. This chapter is how to read those deltas — the stateful discipline the Daily Cascade paper's Chapter 22 described, applied to gamma.*

### 13.1 The four quantities to track

Every intraday §06 update reports the change since the prior report in net GEX, the gamma flip, the call wall, and 0DTE share. Each delta has a distinct meaning:

**Net GEX rising:** dealers getting longer gamma. Customers are ceding convexity — overwriting more, or monetizing protection. Stabilizing cushion thickening. In a rally, this is the market *re-hedging long*: the reference Friday's 1500 read (+$2.3B, "long-gamma deepened post-Fed") is dealers absorbing the call buying that followed the dovish surprise. Rising net GEX in a rally means the rally is being *contained*, not fueled — which is why post-Fed the day closed at 7,519 rather than running to the 7,540 target.

**Net GEX falling:** dealers getting shorter. Customers buying convexity — protection being bought, or calls being bought back. The cushion thinning. Falling net GEX while spot is flat is the quiet warning; falling net GEX while spot is falling is the regime-transition tape.

**Flip rising toward spot:** new gamma arriving concentrated below spot (put buying), pulling the boundary up. Even with net GEX unchanged, this is erosion — the distance to the regime change is shrinking. Rule 2.7.5 makes this a reduce-size trigger because it leads: the flip moves before the sign does.

**Flip falling away from spot:** the structure strengthening from below. The morning read on the reference Friday (7,408 → 7,403) was this.

**Call wall migrating up:** overwriting arriving at higher strikes; resistance rolling up. Typically follows price, so it is confirmation rather than lead.

**0DTE share rising through the day:** normal. It always does. The information is in *where* the 0DTE walls form as the share rises — if the 0DTE call wall builds above the weekly wall, the intraday book is positioned for a break; if it builds below, for a fade.

### 13.2 The disagreement cases

The deltas are most informative when they disagree with each other or with price:

| Net GEX | Flip | Spot | Reading |
|---|---|---|---|
| ↑ | ↓ | flat/↑ | Structure strengthening; the grind continues |
| ↑ | ↑ | ↑ | Gamma arriving but concentrated low; the rally is being hedged *from below* — protection buying under a rising market; watch |
| ↓ | ↑ | flat | **The quiet warning**: cushion thinning and boundary rising with no price move; reduce |
| ↓ | ↑ | ↓ | **Transition tape**: heading for the flip with a thinning cushion; switch playbooks before arrival |
| ↑ | — | ↓ | Dealers absorbing a selloff (customers monetizing puts); the decline is being *contained* — a dip-buy in the positive regime |

### 13.3 The two-minute §06 read at 1000, 1200, 1500

In order: (1) sign of net GEX — still positive? (2) distance from spot to the *monthly* flip — still more than ~1%? (3) direction of the flip's movement since the last report — toward or away? (4) has spot crossed the *0DTE* flip? (5) where has the 0DTE peak/max pain settled — has the magnet moved? Then the rest of the report.


---

# PART IV — TRADING IT

---

## CHAPTER 14 — THE REGIME GATE AS A DAILY PROTOCOL

*Rule 2.7.1 in the Daily Cascade paper says: run the regime gate first, every day, before consulting any other section. This chapter is what "running it" consists of, and what each answer commits you to.*

### 14.1 The three questions, in order

**1. What is the sign of net GEX?** Positive → the stabilizing world. Negative → the amplifying world. (Chapter 5.)

**2. How far is spot from the monthly gamma flip, in percent?** More than ~1% inside the positive regime → full mean-reversion permissions. Between ~0.5% and 1% → mean-reversion with reduced size. Within ~0.5% → the transition zone; no mean-reversion trades. Below → the negative-gamma playbook. On the reference Friday: 1.16% above, full permissions.

**3. Which way is the flip moving?** Away from spot → the structure is strengthening; hold the regime read with confidence. Toward spot → eroding; drop one permission level regardless of the distance.

Three questions, thirty seconds, and the answer selects one of three playbooks. Everything else in the report refines *which trade* within the playbook; nothing else in the report changes *which playbook*.

*(Figure 14 — The regime gate (Rule 2.7.1) as a decision tree — see the HTML edition for the chart.)*

### 14.2 The positive-gamma playbook

Permitted: dip-buys at gamma support and confluence zones; fades at walls with stalling momentum; premium-selling structures; pin trades into the close. Sizing: full, subject to the cluster-confluence rule (Daily Cascade 21.2) and event halving. Stops: tight, because the regime suppresses moves — a stop beyond the expected move is a stop that will never be tested and therefore risks too much. Targets: inside the expected move; walls as targets, not as things to trade through. Expectations: the range holds; the magnet pulls; the close pins.

Not permitted: breakout entries (they get sold by the hedging flow); trend-following adds; holding for the "big move" — the regime's whole nature is that the big move is suppressed.

### 14.3 The negative-gamma playbook

Permitted: breakout entries with confirmation; momentum continuation; long-vol structures (gamma is cheap relative to what the regime will realize). Sizing: half, always — the regime's moves are larger and the stops must be wider, so the same dollar risk means a smaller position. Stops: wide, beyond one expected move, because the regime *amplifies* noise into moves that would stop out a tight position before the thesis plays. Targets: extended — 1.5 to 2 expected moves, because dealer hedging pushes rather than pulls. Expectations: levels break; support becomes acceleration; gaps.

Not permitted: fading extremes; dip-buying at "support" (which is now the place selling accelerates); premium selling of any kind; the reflex "it always bounces" — it does not, in this regime, and that reflex is how positive-gamma traders get carried out in negative-gamma weeks.

### 14.4 The transition zone

Within ~0.5% of the monthly flip, or with net GEX near zero: neither playbook applies. The correct action is **the absence of action** — flat, or reduced to core positions with hard invalidations, until the market declares itself by moving decisively to one side. Traders lose more money in transition zones than in either regime, because they apply the playbook they were in an hour ago to conditions that have changed. The gate exists to make the pause mandatory.

---

## CHAPTER 15 — SIX SETUPS, WITH NUMBERS

*Each setup is stated as: what it is, conditions, entry, stop, target, size, invalidation, and the Daily Cascade rule it operationalizes. The reference Friday's levels are used throughout so the numbers are consistent with Part III.*

### 15.1 The magnet dip-buy

**What.** Buy a pullback to the zone between the 0DTE gamma flip and peak GEX, in a positive-gamma regime, targeting the wall above. The system's primary setup, and the one §23 printed on the reference Friday.

**Conditions.** Net GEX positive and rising or stable; spot > 1% above the monthly flip; peak GEX and max pain convergent (a real magnet); breadth (§10) without divergence; CVD (§11) not diverging; no catalyst inside the holding window. That is three clusters — A, B, and D — confirming.

**Entry.** Limit orders inside 7,468–7,475 (0DTE flip to peak GEX). Not a market order on the first touch: the report's own annotation expects a stop-hunt wick toward 7,455 before the level holds, so the limit sits inside the zone and the wick is the fill.

**Stop.** 7,455 — below the 0DTE put wall at 7,460, with room for the wick. 13–20 points of risk depending on fill.

**Targets.** T1 at 7,490–7,500 (0DTE wall, then monthly wall): 20–30 points, roughly 1:1.5 to 1:2. T2 at 7,530–7,540 (the post-catalyst wall migration target): requires the 2:00 PM catalyst to resolve favorably; 1:3.5 to 1:4.5.

**Size.** Full on the three-cluster confirmation; **halved** because a binary event sits inside the session (Daily Cascade Ch. 19's pre-committed halving). Scale the second half back in only after the catalyst resolves and net GEX confirms (Ch. 13.1: rising GEX in the rally).

**Invalidation.** Operational: stop at 7,455. Regime: an hourly close below the monthly flip at 7,403 — which voids not only this trade but every long in the book. The two-tier stop structure from Daily Cascade Chapter 19 is exactly this pair.

**Rule.** 2.7.2 (convergence-level trade) with 2.7.4 (expected-move targets).

*(Figure 15 — Setup 1 — the magnet dip-buy, drawn — see the HTML edition for the chart.)*

### 15.2 The call-wall fade

**What.** Sell a rally into the monthly call wall when momentum stalls, targeting the magnet. The report's secondary setup.

**Conditions.** Positive regime; spot approaches 7,500 with **stalling internals**: 5-minute RSI rolling over, CVD flattening while price rises, TICK failing to expand above +400 on the push. Net GEX *stable or rising* into the wall — meaning the overwriting that creates the wall is still there. Skip entirely if breadth is expanding into the wall (that is a break setting up, not a fade).

**Entry.** Short 7,496–7,500, on the first hourly stall, not on the first touch.

**Stop.** 7,508 — eight points above the wall. A wall that has been decisively cleared by more than a few points on volume is no longer a wall (Ch. 7.1: gamma fades above the strike), so the stop is tight by design.

**Target.** The magnet, 7,475–7,478. Roughly 22 points for 8–12 of risk: 1:2 to 1:2.7.

**Size.** Half — fading in any regime is the lower-probability side of the mechanics, and the trade is asymmetric in the wrong direction if the wall breaks on a catalyst.

**Invalidation.** An hourly close above 7,508 with net GEX *falling* (call buying arriving above the wall, dealers getting shorter, the selling pressure that was the wall dissolving). That is not a stopped-out fade; it is the setup in 15.3 forming.

**Rule.** 2.7.3 (call-wall discipline) — the fade is the only permitted long-side exception to "no longs within 0.15% of a wall."

### 15.3 The call-wall break

**What.** Buy the retest of a broken call wall from above, when the break has the mechanics behind it. The reference Friday's afternoon, in the reverse of 15.2.

**Conditions.** A catalyst (the 2:00 PM minutes); **volume surge** on the break (the hedging flow that was the wall is being overwhelmed, and that takes volume); **net GEX falling or the flip dropping** in the post-break delta table — or, subtly, net GEX *rising* but with the *call wall migrating up* (7,500 → 7,540 by the Friday reset), which means the resistance has relocated rather than dissolved; an hourly close above the wall. Above the wall, the dealer long-call gamma that generated the selling declines as deltas approach 1 — the resistance is mechanically *gone*, and what remains is whatever new wall forms above.

**Entry.** The retest of 7,500 from above, in the 7,500–7,505 zone, after the hourly close confirms. Not the breakout bar itself — the breakout bar is where the trapped fades (15.2) are covering, and the retest is where the flow shows its hand.

**Stop.** 7,492 — back inside the old wall. A failed retest that closes back below is a false break, and false breaks of major walls reverse hard (the trapped breakout longs are the fuel).

**Target.** The next structural level: the migrated wall (7,540 on the reference Friday) or one expected move from the break (7,500 + 52 ≈ 7,550). 40–50 points for 8–13 of risk.

**Size.** Half — post-catalyst tapes are fast, and the vanna bid (Ch. 8.2) can carry price well beyond the target but can also exhaust abruptly when the vol crush completes.

**Invalidation.** The reclaim of 7,492 on an hourly close, or a *rising* net GEX with the wall *not* migrating — meaning the market is re-hedging long *at the old wall*, and the break will be sold.

**Rule.** The exception clause of 2.7.3 ("wait for a decisive break on volume").

### 15.4 The flip break — trading the regime change

**What.** The transition from the positive to the negative playbook, executed as a trade rather than suffered as a surprise.

**Conditions.** Spot declining toward the monthly flip (7,403) with net GEX *falling* and the flip *rising* — the transition tape of Ch. 13.2. Breadth confirming the decline (§10 without a washout reading — a washout is a *bottom*, and a bottom at the flip is a different trade). An hourly close below the flip.

**Entry.** Short the retest of the flip from below, 7,400–7,405, after the hourly close confirms. As with 15.3, the retest rather than the break bar.

**Stop.** 7,412 — back above the flip. Tight, for the same reason as 15.3's stop: a reclaimed flip is a failed regime change, and failed regime changes produce violent snap-backs as dealers who had flipped to short-gamma hedging re-hedge long into a rising market. **The failed flip break is itself a high-quality long setup** — a reclaim within the same session, on volume, with net GEX turning back up, is the strongest reversal signal the framework produces. Have both orders ready.

**Target.** Extended, because the regime amplifies: 1.5 to 2 expected moves below the flip — 7,320 to 7,300 on the reference numbers — or the next structural put support (the weekly/monthly put walls at 7,450/7,400 are already broken by construction; the quarterly 7,250 is the next).

**Size.** Half, and stops wide relative to a positive-regime trade (Ch. 14.3). The trade is not "short at the flip"; it is "adopt the momentum playbook with the flip as the reference."

**Invalidation.** The hourly reclaim. And a discipline note: a flip break is not a trade signal until the *retest* — the first cross is where most of the false breaks live, and the regime does not change on a touch (Ch. 7.5).

**Rule.** 2.7.1's negative-regime branch, made executable.

### 15.5 The pin — trading the close with options

**What.** In a positive-gamma regime with no remaining catalyst, sell defined-risk premium around peak GEX after 2:00 PM, harvesting the 0DTE decay as the market pins.

**Conditions.** Positive regime; net GEX rising or stable through the afternoon; 0DTE peak and max pain convergent; no scheduled event after entry; VVIX calm; IV−RV rich (Daily Cascade Rule 4.7.3); spot within ~10 points of the magnet. On the reference Friday this setup was *not* available before 2:00 PM (the minutes) and was marginal after (the break to 7,519 moved spot off the magnet); it is a calm-afternoon trade.

**Structure.** An iron condor centered on the magnet with short strikes at the 0DTE walls and long wings beyond: with spot at 7,478, peak GEX 7,475, walls 7,460/7,490 — sell the 7,460 put and 7,490 call, buy the 7,445 put and 7,505 call. Net credit collected; maximum loss defined by the wing width less the credit. The trade is long theta and short gamma — a written policy for the last two hours of the day, in the regime where the industry's aggregate book is *also* long gamma and suppressing the very moves that would hurt the position.

**Management.** Take the trade off if spot breaches a short strike *and* crosses the 0DTE flip in the same direction — that combination means the intraday book has gone short gamma against you and the pin is gone. Otherwise, let it expire. Do not "adjust" a 0DTE condor; there is no time for adjustment to work.

**Size.** Small and fixed — this is a high-frequency, small-edge trade whose value comes from repetition across many calm afternoons, not from any single day. Size such that the max loss is a fraction of a normal day's futures risk.

**Rule.** 2.7.7's implication — the 0DTE level is real only until the close, so the trade that exploits it must *also* end at the close.

### 15.6 The vanna-charm drift

**What.** A long bias into a positive-gamma Friday afternoon or into monthly opex after a feared event has passed, buying pullbacks to VWAP and letting the second-order flows carry the position.

**Conditions.** Event behind you with a benign resolution; implied vol crushed (§08 term structure re-steepened, §18 confirms the vol crush); positive gamma; net GEX rising as the market re-hedges; time-of-week or time-of-cycle where charm is strongest (Friday afternoon, the final days before monthly opex). The reference Friday from 2:30 PM onward is the textbook instance: dovish resolution, vol crush, dealers covering put hedges (vanna) and OTM deltas decaying into the weekly expiry (charm), both producing systematic buying.

**Entry.** Pullbacks to session VWAP or to the retest of the broken wall (15.3's entry), not chases. The drift is a *bid*, not a *surge*; it rewards patience with the entry.

**Stop.** Below VWAP by half an expected move — the drift is gentle and the stop should not be tighter than the noise.

**Target.** The close. The trade's thesis is the flow into the close; take it off at 3:50 or into the MOC, not at a price.

**Size.** Half. The flows are real but small per hour; the trade is a bias, not a conviction.

**Invalidation.** Vol *rising* again intraday (the crush reversing — vanna flips to selling); net GEX falling (the re-hedge reversing); an hourly close below VWAP.

**Rule.** This setup does not correspond to a numbered rule in the Daily Cascade paper because charm and vanna are not yet in the report; it corresponds to backlog item 6, and should be added to §23's setup library when the flows are.

### 15.7 The six setups in one table

| # | Setup | Regime | Entry zone | Stop | Target | Size | Key condition |
|---|---|---|---|---|---|---|---|
| 1 | Magnet dip-buy | Positive | 0DTE flip → peak GEX | Below 0DTE put wall | Next wall up | Full (halved on events) | 3-cluster confluence |
| 2 | Call-wall fade | Positive | At the wall, on stall | 8 pts above wall | The magnet | Half | Stalling internals; GEX stable |
| 3 | Call-wall break | Positive → catalyst | Retest from above | Back inside wall | Migrated wall / +1 EM | Half | Volume + hourly close + wall migrates |
| 4 | Flip break | Transition → negative | Retest from below | Back above flip | 1.5–2 EM below | Half | GEX falling + flip rising; have the reversal order ready |
| 5 | The pin | Positive, post-catalyst | Condor at the magnet | Wall breach + 0DTE flip cross | Expiry | Small, fixed | No event; VVIX calm; IV−RV rich |
| 6 | Vanna-charm drift | Positive, post-event | VWAP pullbacks | ½ EM below VWAP | The close | Half | Vol crushed; GEX rising; Friday/opex |

---

## CHAPTER 16 — EXPRESSING IT: FUTURES OR OPTIONS

### 16.1 The default is futures

Your execution framework trades /ES, and for setups 1 through 4 that is correct: the thesis is directional and level-based, the regime gate governs, and futures give clean fills, no vega exposure, and no theta bleed. Options add a second dimension (vol) to a trade that only has a thesis in the first (price). Add the dimension only when the vol thesis is *also* present.

### 16.2 When options are the better expression

**Selling premium in positive gamma with rich IV−RV** (setup 5, and a defined-risk put spread below the put wall as an alternative to setup 1). The regime suppresses realized vol; the surface is pricing more than it will deliver; you are selling a policy in a soft loss year. The structure to reach for: **credit spreads** (sell the strike at the level, buy the wing beyond) — defined risk, positive theta, short gamma in the regime where the industry is long gamma and doing your hedging for you.

**Buying convexity into a catalyst with cheap IV−RV** (the event version of setup 3). When the surface is *under*-pricing an event — rare, but it happens when a catalyst is under-appreciated — a long call spread above the wall or a long straddle at the magnet converts the binary into defined risk. The trade wins if the move exceeds the premium; the regime gate tells you whether the move can (it can, if the catalyst is large enough to break the structure).

**Defining the risk on the flip break** (setup 4). Negative-gamma regimes gap; a futures stop can be gapped through. A long put spread below the flip caps the loss at the premium and captures the amplified move. The cost is theta if the break stalls.

### 16.3 A caution about becoming the customer

Every option you trade is a contract with a dealer, and your position becomes part of the book the report measures. At your size the effect is nil; the point is conceptual. When you sell a put spread below the put wall, you are one of the customers ceding convexity that thickens the cushion. When you buy protection, you are thinning it. The naive convention assumes you behave like the average customer; trading options with the GEX map in hand means you are, at least, an *informed* customer — one who knows what the dealer on the other side is about to be forced to do.

---

## CHAPTER 17 — FAILURE MODES SPECIFIC TO TRADING POSITIONING

*The Daily Cascade paper's Chapter 23 listed the system's eight failure modes. These nine are the ones that live inside §06.*

**1. Trading a wall that exists in one vendor's model and not another's.** The single largest risk. Chapter 6.3's reliability hierarchy is the defense: trade the sign and the direction with confidence, the major walls with moderate confidence, and precise magnitudes not at all. A wall that moves 20 points between vendors is a *zone*.

**2. Expecting a wall to hold against a repricing.** Walls are hedging flow; a catalyst large enough to reprice the index overwhelms hedging flow. The expected move (Ch. 12) is the market's own statement of how big a move it is pricing; when the expected move is wider than the corridor (11.3, second observation), the corridor is a *pre-catalyst* structure and should be treated as such.

**3. The put-wall stop-run.** Ch. 7.2: the put wall's support is contingent, the pure gamma mechanics *below* it are amplifying, and the level is watched — which makes it the ideal location for a liquidity sweep. Use limits inside the zone, expect the wick, and put the stop where the sweep would have to become a break (below the wall by a margin, not at it).

**4. Sign-convention failures around known structures.** The JHEQX legs (Ch. 10.3) are the visible case; structured-product hedges, index-fund overwriting programs, and large dispersion books are the invisible ones. When a level "should" work by the naive model and repeatedly does not, the model is mis-signing something there.

**5. Over-reading morning 0DTE.** Ch. 9.4. Before 11:00 AM the 0DTE book is balanced and thin; its levels are suggestions. The 3:00 PM read is the one with authority.

**6. Regime denial.** Continuing to fade in negative gamma because fading worked for the last six weeks. The gate (Ch. 14) is mandatory precisely because the playbook that made money is the one the trader wants to keep running, and it is the one that fails.

**7. Over-trading the flip.** Every touch is not an event (Ch. 7.5). The retest is the trade; the touch is noise. Traders who short every approach to the flip in a positive regime are fading the strongest support in the structure.

**8. Reading DEX as a flow.** Ch. 8.1. DEX is a snapshot of crowding; it says nothing about what dealers will do next. High positive DEX is a sizing input (halve), not a signal (sell).

**9. Being long protection into a benign resolution.** The vanna crush (Ch. 8.2) hits long puts twice — once as the index rallies, once as the vol collapses. A hedge bought into an event should be sized for the possibility that the event is a non-event, or structured as a spread so the vol crush is partially offset by the short leg.

---

# PART V — THE MULTI-HORIZON BOOK

*Parts II and III treated the dealer book mostly as one aggregate. It is not one thing — it is four inventories on four clocks, and the professional read of §06 is the simultaneous one: which book governs right now, which governs tonight, and what it means when they disagree. This Part is that read, plus the session-level behavior of the shortest book, which is where most of the intraday confusion lives. It extends Chapters 9–13; nothing here replaces them.*

*(Figure 16 — Four books, four clocks, one spot price — see the HTML edition for the chart.)*

---

## CHAPTER 18 — THE FOUR CLOCKS

### 18.1 The layered-program frame

The cleanest way in is the one you already own: the dealer book is a layered program. The **0DTE book is the working layer** — it takes the daily frequency, prices and expires within a session, and its behavior tells you nothing about the program's solvency. The **weekly book is the first excess layer** — it absorbs what the working layer passes through and defines this week's corridor. The **monthly book is the structural layer** — the layer whose attachment points (the monthly flip, the monthly walls) define whether the whole program is functioning. The **quarterly book is the cat layer** — JHEQX-class positions that only matter when the loss reaches them.

Two consequences follow immediately and resolve most day-to-day confusion:

**A working-layer event is not a program event.** Spot crossing the 0DTE flip (Chapter 11.3's nested case) changes the intraday physics for hours; it says nothing about the regime. Traders who treat every 0DTE flip cross as a regime signal churn themselves to death; traders who ignore the monthly flip because "the 0DTE flip breaks all the time" get carried out at the transition. The layers have different jobs.

**The layers hand off.** A decline that overwhelms the 0DTE cushion falls to the weekly structure; one that overwhelms the weekly falls to the monthly. In a healthy stack each hand-off *decelerates* the move, because each deeper layer is bigger and slower to erode. The worked session in Figure 20 is exactly this sequence. When the hand-offs stop decelerating — when the layers have converged (18.4) — the program is fragile regardless of the headline GEX number.

### 18.2 The five configurations

Everything the stack can do reduces to where the short-dated and long-dated flips sit relative to spot. Five configurations cover the space:

*(Figure 17 — The five stack configurations — see the HTML edition for the chart.)*

| # | Configuration | Who governs intraday | Who governs overnight | Playbook | The tell it's forming |
|---|---|---|---|---|---|
| 1 | **Aligned positive** — all flips stacked well below spot | 0DTE pin mechanics | Monthly structure | Full mean reversion (Ch. 14.2) | Flips *descending* across reports |
| 2 | **Post-opex thin** — short books positive, monthly freshly expired | 0DTE (outsized share) | *Nobody* — the cushion is thin | MR intraday, flat or reduced overnight | The calendar: week after third Friday |
| 3 | **Short-negative nested** — spot below 0DTE flip, above monthly | 0DTE *amplifies* | Weekly/monthly catch | Stand aside intraday or trade the catch at weekly support; regime intact | An ordinary decline that suddenly steepens |
| 4 | **Structurally negative, short-positive** — spot below monthly flip, 0DTE sellers returned | 0DTE pins | Negative regime resumes | **Rallies are to sell**; intraday calm is a trap | Orderly, low-vol up-days inside a downtrend |
| 5 | **All negative** | Amplification | Amplification | Ch. 14.3, no exceptions | Crisis tape; every bounce sold |

Configuration 4 deserves a paragraph because it is the one that fools experienced positive-regime traders. After a hard selloff below the monthly flip, 0DTE premium sellers return within a day or two — same-day income strategies re-engage fast — and their flow rebuilds an *intraday* positive-gamma pocket inside a structurally negative regime. The tape pins, ranges tighten, the day *feels* like the old regime. It is not. The monthly book is still short gamma; the first overnight shock trades in the amplifying world, and the intraday calm was the working layer, not the program. Bear-market rallies feel orderly for exactly this reason. The rule: **the monthly flip decides which playbook you are in; the 0DTE stack only decides how today feels.**

### 18.3 A day the stack changes twice — worked

Take the reference numbers and run a non-event Tuesday. 9:30: configuration 1 — spot 7,489, flips at 7,468 / 7,440 / 7,403, everything aligned, the morning grinds in the corridor. 11:30: a mid-morning flush (a rates headline, nothing structural) presses spot through 7,468. **The stack is now configuration 3.** The 0DTE book — by then ~50% of total gamma — is hedging pro-cyclically, and a 6-point drift becomes a 17-point slide in forty minutes. It reaches the weekly put wall at 7,450 and the weekly flip at 7,440, where the hand-off works: monetization flows and the still-long weekly/monthly gamma absorb it. 1:00–2:30: spot stabilizes at 7,450–56, recrosses 7,468 at 2:45. **Configuration 1 again** — and, this being the gamma ramp of the afternoon, the re-stabilized 0DTE book now pins harder than it did in the morning. Close: 7,478, twelve points off the magnet, an unremarkable print concealing two regime changes in the working layer.

*(Figure 20 — A nested-flip day, worked — see the HTML edition for the chart.)*

The reading discipline the example teaches: when a move accelerates for no visible reason, **check which flip just got crossed before checking the news.** Half of "mystery" intraday air pockets are configuration 3 arriving on schedule.

### 18.4 Flip-stack width — the fragility gauge

The distance from the 0DTE flip to the monthly flip — 65 points on the reference Friday — is the stack's *staging depth*, and it is a better fragility gauge than net GEX. A wide stack means shocks meet three cushions in sequence; a compressed stack means one impulse flips every horizon's hedging to amplification at once. Compression happens quietly: heavy near-dated put buying pulls the 0DTE and weekly flips up toward spot while the monthly barely moves, and the headline GEX number can be *rising* while the staging depth collapses.

*(Figure 21 — Flip-stack width — the fragility gauge — see the HTML edition for the chart.)*

**Rule 18.1 — track the width.** Monthly flip minus 0DTE flip, in points and as % of spot, at every report. Above ~0.7% of spot: normal staging. Under ~0.4%: reduce size one notch regardless of net GEX. Under ~0.2%: transition-zone posture (Ch. 14.4) even if every flip is still below spot. *(Candidate composite for the §06 delta table — logged in the backlog note at 21.4.)*

---

## CHAPTER 19 — THE GREEKS BY HORIZON

### 19.1 One matrix

Each Greek's market impact lives in a different part of the expiry stack, peaks at a different time, and produces a different flow. The whole chapter compresses into one table; the sections after it unpack the three cells traders most often mis-locate.

| Flow | Where it lives | When it peaks | Dealer action & market effect |
|---|---|---|---|
| **Gamma** | Every bucket; *0DTE dominates intraday share* | Last 2 hours of the session (Fig. 18) | Counter- or pro-trend hedging; pins and air pockets |
| **Vanna** | **Weekly / monthly / quarterly** — the OTM put inventory with real vega | Around vol shocks and crushes | Vol ↓ → buy index; vol ↑ → sell. The post-event bid |
| **Charm** | **0DTE and weekly** intraday; **monthly** in opex week | Final hours; final days before opex | OTM delta decay → systematic buy drift into expiry |
| **Theta** | Proportionally largest in 0DTE (Fig. 5's curve, compressed to hours) | Continuous | The rent; funds the whole premium-selling ecosystem |
| **DEX** (positioning) | Read *per bucket*, not aggregate | — | 0DTE DEX = today's crowd; monthly DEX = structural crowding |
| **Vega** | Long-dated books almost entirely | Vol regime shifts | Repricing risk; the channel vanna acts through |

### 19.2 The cell everyone mis-locates: vanna is a *long-dated* flow

Because 0DTE dominates volume, the reflex is to attribute every mechanical flow to it. Vanna is the corrective example. A same-day option has almost no vega — √T is tiny — so a vol crush barely moves its delta. The protective puts with real vol sensitivity are the weekly and monthly inventory. **The post-event melt-up is therefore a *long-dated* book phenomenon:** on the reference Friday, the 2:00 dovish print crushed 1-month implied vol, the *monthly* put deltas shrank, and dealers bought back monthly hedges — while, separately, the *0DTE* book supplied the late-day pin at the migrated strike. Two flows, two horizons, stacked in the same direction. That stacking is what an A+ afternoon tape is made of; when they *oppose* — a vol crush arguing higher while a heavy 0DTE put wall argues for a low pin — the long-dated flow wins into the close's final prints less often than the 0DTE pin does, because gamma at max always beats vanna locally. Sequence: vanna sets the drift, 0DTE sets the destination.

### 19.3 Charm's two seasons

Charm is expiry-proximate by definition, so it has an intraday season and a calendar season. **Intraday:** the 0DTE OTM strikes decay through the afternoon and the burn-off is part of the late-day drift (Setup 6). **Calendar:** in the several days before monthly opex, the *monthly* OTM inventory — far larger — decays the same way, and the drift becomes a multi-day phenomenon: the well-documented tendency of calm markets to grind up into third Fridays. Same Greek, two clocks. The trading distinction: intraday charm supports a *close-targeted* bias (exit at the bell); opex-week charm supports a *multi-session* bias (hold the drift, exit before the unclench).

### 19.4 DEX by bucket — today's crowd versus the structural crowd

Aggregate DEX blurs two very different readings. **0DTE DEX** is today's crowd: building positive 0DTE DEX through the morning means the day-trading cohort is accumulating long delta — chasing — and dealer hedges are stacking against a wall test. Fading a wall (Setup 2) with 0DTE DEX stretched long is the highest-quality version of that trade; the crowd is the fuel. **Monthly DEX** is the structural crowd: the input to the "crowded positioning → halve size" condition in the §23 setups. The divergence read: 0DTE DEX stretched while monthly DEX is flat is a *day-trade* signal only; monthly DEX stretched is a *sizing regime*. The report currently publishes one DEX number; splitting it is the natural refinement (21.4).

---

## CHAPTER 20 — THE 0DTE SESSION TAXONOMY

### 20.1 Why 0DTE's impact is different every day

The longer books carry memory; the 0DTE book has none. It is re-seeded every morning — strikes listed around the prior close, flows arriving fresh — so its influence on any given day depends on four things that reset nightly: **how lopsided** the day's flow becomes (a balanced book nets to little; Cboe's own studies find flows roughly balanced *on average*, which is precisely why the tail sessions matter); **when** it becomes lopsided (a one-sided morning shapes the whole day; a one-sided 3:00 PM shapes only the close); **what the longer books are doing** (the same 0DTE flow means different things in configurations 1 and 4); and **the calendar** (event days, opex Fridays, the post-opex thin week). Honesty note: sell-side estimates of 0DTE's amplification potential have ranged from negligible to multiple-of-the-move in stress scenarios, and the debate is unresolved because the amplifying tail is rare. The operational position this paper takes is conditional and observable: *usually pin-forming, occasionally an accelerant, and the tell is whether the walls hold or migrate on first test.*

*(Figure 18 — The 0DTE share through the session — see the HTML edition for the chart.)*

### 20.2 The six session types

*(Figure 19 — The six session types by 0DTE signature — see the HTML edition for the chart.)*

**1. The pin day.** No catalyst, balanced book, configuration 1. The morning establishes the corridor, midday chop shrinks, and the afternoon gamma ramp pulls price to peak GEX. The most common type in a positive regime, and the habitat of Setups 1, 2, and 5. Signature: walls *hold on first test*; the expected move is never threatened.

**2. The trend day.** The subtle one. Heavy one-directional 0DTE flow from the open — say aggressive call buying on a gap — puts dealers *short* the day's gamma: every hedging rule of Chapter 4.3 now runs pro-cyclically *intraday*, even though the monthly book is still long. The signature is unmistakable once named: **the 0DTE call wall migrates upward with price instead of repelling it** (the delta tables show the wall rolling 7,490 → 7,510 → 7,525), pullbacks are shallow, and the day closes near its extreme. The morning's "resistance" was never resistance — it was the crowd's footprint, moving. Fading a trend day with pin-day tools is the single most expensive session-classification error available.

**3. The event day.** The reference Friday, fully worked in Chapters 11 and 19.2: morning pin inside a corridor narrower than the expected move (Fig. 13's exact geometry — the surface *told you* the box would break), the catalyst breaks it, vanna and re-hedging flows carry, and a *new* 0DTE pin forms late at a migrated strike. The playbook is sequential: pin-day tools before the event, Setup 3/6 tools after.

**4. The opex-Friday overlay.** The day's 0DTE book coincides with the weekly (and monthly, on third Fridays) expiration whose open interest accumulated all period. Gamma at cycle maximum, charm at maximum, pins at their annual strongest — and at the close, the cycle's cushion vanishes at once (Fig. 18's cliff, scaled up). Trade the pin; respect the unclench that follows.

**5. The failed pin.** The diagnostic type. Price sits at max gamma into 3:30 and then breaks hard on *no news* — meaning a participant was willing to trade *through* the strongest counter-flow of the day and pay the gamma toll for immediacy. That is information: a large player valued being positioned tonight over executing well today. A failed pin into weakness has preceded enough gap-downs to earn a rule: **a pin that loses on no news cancels the overnight-hold permission from every other section.**

**6. The negative-gamma day.** Configuration 5 (or a deep 3): no pins exist, ranges run 1.5–3× the expected move, and the 0DTE book amplifies whatever the longer books started. The session taxonomy collapses to one entry: Chapter 14.3.

### 20.3 Session-to-session carryover — what persists overnight and what does not

Nothing of the 0DTE *book* survives the close; several things about the 0DTE *pattern* do. Tomorrow's strikes list around tonight's close, so the corridor re-centers on wherever the day ended — pins beget adjacent pins, which is why calm stretches produce those staircases of closes at successive round strikes. Round numbers dominate seeding (7,475, 7,500, 7,525), so wall candidates are guessable before the flows confirm them. The *cohort* persists even though its positions don't: the premium-selling programs that pinned today will sell tomorrow's strikes unless vol regime chases them out, and the chase-flow crowd that made today a trend day is statistically likelier to re-engage tomorrow in the same direction. And the calendar persists: the day after a trend day opens with the longer books' walls *relocated* (overnight overwriting follows price), so yesterday's breakout level is often today's put-side support — the migration mechanics of 7.1, compressed to a 24-hour cycle.

### 20.4 Classifying the day by 11 AM

Four questions, answerable from the 1000/1200 reports, that sort the session into the taxonomy while it is still tradable:

1. **Is the 0DTE book balanced or lopsided?** (Balance ratio in the §06 read; roughly balanced → pin-day prior.)
2. **Did the first wall test hold or migrate?** (Held → pin/event day. Migrated with price → trend day; retire the fade tools now.)
3. **Is the expected move wider than the corridor?** (Yes + a scheduled catalyst → event day; yes with no catalyst → respect the possibility the surface knows something.)
4. **Where is spot relative to the 0DTE and monthly flips?** (Above both → types 1–4 available. Between → type 6 locally, configuration 3. Below monthly → types 5–6 only.)

**Rule 20.1 — classify before noon, re-classify at 2:00, and let the classification select the toolset.** The session types are not trivia; each one enables some setups and forbids others, and most intraday losses in a system like this come from running type-1 tools on a type-2 day.

---

## CHAPTER 21 — THE SIMULTANEOUS READ

### 21.1 The full protocol at each report

Chapter 13.3 gave the two-minute §06 read; the multi-horizon version adds one pass across the buckets. At 0920/1000/1200/1500, in order: **(1)** net GEX sign and delta — the headline; **(2)** the *stack*: all four flips, their movement since the last report, and the flip-stack width (Rule 18.1); **(3)** the *walls by bucket*: stacked at one price (strong level) or dispersed (weak); did the 0DTE wall hold or migrate on its last test (the type-2 tell); **(4)** *DEX by bucket* where available — today's crowd vs the structural crowd; **(5)** the session classification (Rule 20.1), updated. Ninety seconds once practiced, and it replaces the single-number read with the layered one this Part exists to teach.

### 21.2 The divergence grid

The stack's disagreements, like the clusters of the Daily Cascade paper's Chapter 21, are richer than its agreements: **0DTE GEX rising while monthly GEX falls** — the day is calm because income sellers are active while the structure quietly erodes; the pin is real and the cushion under it is not. **All flips converging toward spot** — compression (18.4), the quiet fragility. **Walls stacking across buckets** at one strike — the strongest level type §06 produces, stronger than any single-bucket wall (the 7,500 triple-stack of Chapter 11.3, observation five). **0DTE flip above the weekly flip** — an inverted stack, meaning the day's book is positioned more bearishly than the week's: someone is paying for same-day downside specifically, which around event mornings is the surface's sharpest short-horizon warning.

### 21.3 Three rules to close the Part

**Rule 21.1 — one playbook, one layer.** The monthly stack selects the playbook (Ch. 14); the 0DTE stack selects the session type and the toolset (Ch. 20); the weekly stack sets this week's targets and stops. Never let a shorter layer answer a longer layer's question.

**Rule 21.2 — the migration override.** A 0DTE wall that migrates on first test retires every fade setup for the session, whatever the session started as.

**Rule 21.3 — the width gate.** Flip-stack width under 0.4% of spot caps size one notch below whatever the regime gate allowed. Fragility compounds the regime; it never improves it.

### 21.4 What this Part adds to the backlog

Three computed indicators, all cheap once the §06 feed is live, all belonging in the Daily Cascade paper's Chapter 24 alongside the existing GEX items: **flip-stack width** (Rule 18.1's series, displayed in the delta table), **a wall-migration flag** (held/migrated on first test, per bucket, per session — the type-2 detector), and **DEX split by bucket** (19.4). Each converts a judgment in this Part into a number the logging layer can grade.


---

# APPENDIX

---

## A.1 — Glossary

**Basis** — futures price minus cash index; the cost of carry. **Call wall** — strike with the largest dealer long-call gamma; mechanical resistance. **Charm** — sensitivity of delta to time; produces a systematic dealer bid into expiry in a positive regime. **Delta** — option price sensitivity to the underlying; the hedge ratio; a probability proxy. **DEX** — aggregate dealer delta; a positioning snapshot. **Expected move** — the options market's one-sigma estimate of the move over a horizon; read from the ATM straddle. **Gamma** — sensitivity of delta to the underlying; convexity; peaks at the money and explodes into expiry. **Gamma flip** — the price at which aggregate dealer gamma crosses zero; the regime boundary. **GEX** — Gamma Exposure; aggregate dealer gamma, signed, in dollars per 1% move. **JHEQX** — the JPMorgan Hedged Equity Fund; source of the quarterly collar bookends. **Max pain** — strike minimizing the value of expiring options; meaningful only when coincident with peak GEX. **Flip stack** — the four buckets' gamma flips read as one ladder; its width (monthly flip minus 0DTE flip) is the fragility gauge of Chapter 18.4. **Naive convention** — the assumption that dealers are long calls and short puts. **0DTE** — zero days to expiry; same-day options; ~50–60% of SPX volume. **Opex** — monthly expiration, third Friday. **Peak GEX** — strike with the largest total gamma; the magnet. **Pin** — the tendency of the index to close near peak GEX in a positive regime. **Session taxonomy** — the six 0DTE-signature day types of Chapter 20.2 (pin, trend, event, opex, failed-pin, negative-gamma). **Trend day** — a session whose one-sided 0DTE flow puts dealers short the day's gamma; the tell is walls migrating with price instead of holding. **Put-call parity** — a call plus cash equals a put plus the underlying; call and put gamma at a strike are identical. **Put wall** — strike with the largest put open interest; support by monetization and vanna, not by gamma. **Skew** — the implied-vol differential across strikes; the cat load on tail protection. **Straddle** — a call plus a put at the same strike; its price is the expected move. **Theta** — time decay; earned premium. **Vanna** — sensitivity of delta to implied vol; produces the post-event melt-up. **Vega** — option price sensitivity to implied vol. **Vol risk premium** — implied minus realized vol; the underwriting margin of the option writer.

## A.2 — The formulas in one place

- **Expected move (one sigma):** Spot × IV × √(days ÷ 365). Daily: Spot × IV ÷ √252.
- **From the straddle:** Expected move ≈ ATM straddle price; one sigma ≈ straddle ÷ 0.8.
- **Per-strike GEX:** Γ × OI × 100 × Spot² × 0.01 × sign (+ for dealer-long, − for dealer-short).
- **Net GEX:** Σ call GEX − Σ put GEX (naive convention).
- **Hedge size:** contracts × 100 × delta = index-units; ÷ 50 = ES contracts.
- **Put-call parity:** C + K·e^(−rt) = P + S.
- **Basis:** F − S ≈ S × (r − q) × t.
- **Flip-stack width:** monthly flip − 0DTE flip, in points and % of spot (gates: ~0.7% normal · <0.4% reduce · <0.2% transition posture).

## A.3 — The one-page card

**The gate (every morning, thirty seconds):** Sign of net GEX → distance to monthly flip in % → direction of flip's movement → playbook.

| Regime | Distance to flip | Posture | Permitted | Forbidden |
|---|---|---|---|---|
| Positive | > 1% | Full mean-reversion | Dip-buys, wall fades, premium selling, pins | Breakouts, trend adds |
| Positive | 0.5–1% | Reduced mean-reversion | Same, half size | Same |
| Either | < 0.5% | **Flat / core only** | Nothing new | Everything |
| Negative | Below flip | Momentum, half size, wide stops | Breakouts, long vol | Fades, dip-buys, premium selling |

**The levels:** Call wall = mechanical resistance, present before arrival. Put wall = contingent support; amplifying below. Peak GEX = magnet; pin target after 2 PM. Max pain = confirm peak GEX only. Flip = boundary; trade the retest, not the touch; track its movement.

**The deltas:** GEX ↑ = cushion thickening. GEX ↓ = thinning. Flip ↑ toward spot = erosion (reduce). Flip ↓ = strengthening. GEX ↓ + flip ↑ + spot flat = **the quiet warning**.

**The second-order flows:** Vol crush after an event → vanna bid. Time passing into expiry in positive gamma → charm bid. Both: long bias into the close, buy VWAP pullbacks.

**0DTE:** Suggestions before 11 AM. Credible by 1 PM. Governs after 2 PM. Void at 4 PM. Never carry a 0DTE level overnight.

**The setups:** 1 magnet dip-buy · 2 wall fade · 3 wall break · 4 flip break (+ its reversal) · 5 the pin · 6 vanna-charm drift. Numbers in Chapter 15.7.

**The multi-horizon read (per report):** net GEX → the four-flip stack + width → walls by bucket (held or migrated?) → DEX by bucket → session type. One playbook, one layer: monthly picks the playbook, 0DTE picks the toolset, weekly sets the week's levels.

**Classify the session by 11 AM:** balanced or lopsided 0DTE? · first wall test held or migrated? · expected move vs corridor (+ catalyst?) · spot vs the 0DTE and monthly flips. Migration on first test retires every fade for the day.

**The override inside §06:** Basis dislocation freezes new positions. Multi-vendor sign disagreement near the flip = transition zone regardless of your vendor's number.

---

*Companion IX · Version 1.1 · extended September 5, 2026 with Part V (the multi-horizon book) and Figures 16–21. This paper is the controlling elaboration of Daily Cascade Chapter 2; the two are consistent on mechanics, and this paper is the one that derives them. Report figures are the 0700 §06 values on the reference Friday. The setups are structured judgment awaiting the outcome-logging layer (Daily Cascade backlog, Tier 1, item 1) that will grade them.*

