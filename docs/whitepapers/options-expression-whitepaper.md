# Options as Expression

## Choosing the Instrument After You Have Chosen the View

**Companion white paper — chester-reports library**
**Series placement:** with the micro and execution layer, after *Volatility* and *The Dealer's Hand* (numeral assigned by the library guide on commit; cross-references in this paper are by name)
**Version:** 1.0 — September 2026
**Status:** Framework and manual. Governs the expression half of every packet. The HTML edition is canonical — the figures live only there.

---

### Reader's note

The Operating Doctrine's Rule 11 says that the thesis and the instrument are two decisions. The library has papers on how to form the thesis and no paper on how to choose the instrument, which is a strange omission given that Book C is composed entirely of defined-risk options and futures and that Book A's convexity-managed sleeve is an options structure by another name. This paper fills it.

It is written to be *seen* rather than read, on the model of *The Dealer's Hand*. Every structure in it is a shape, and the shape is the argument: once a reader can picture what a spread pays at every price, the question "which instrument expresses this view" stops being a matter of jargon and becomes a matter of matching one picture to another. The figures are computed rather than sketched.

A distinction that runs through the whole paper. *The Dealer's Hand* looks at options from the outside — as inventory in a market maker's book whose hedging moves the market. This paper looks at the same contracts from the inside, as instruments the operator owns. The greeks in that paper are the dealer's and describe a flow; the greeks here are yours and describe a risk. They are the same numbers with opposite signs and entirely different meanings, and confusing them is the most common error a reader of both papers can make.

Part I is the grammar — the four shapes everything is built from, and what you are actually paying for. Part II is the structures, one figure each. Part III is the three costs that determine whether a correct view makes money. Part IV is the engineered payoffs: buffered funds, synthetic principal protection built from a cash-equivalent fund and long-dated calls, and the dual-directional structures that pay off in both directions — including how to build each from listed options, what each really costs, and how each compares to the honest baseline of simply owning the index. Part IV closes with the scenario matrix against the index across four asset classes and a chapter on leverage — which form, at what cost, and the playbook for adding after a decline. Part V is the decision procedure and its wiring into the register.

---

# Part I — The Grammar

## Chapter 1 — Why the instrument is a second decision

A view has three properties that a price chart does not show: a **direction**, a **magnitude**, and a **deadline**. "The index mean-reverts toward the call wall" is a different claim from "the index grinds higher for six weeks," and the two want different instruments even though both are bullish. Options are the only instrument class that lets a trader express magnitude and deadline separately from direction, which is exactly why they reward precision and punish vagueness.

Four questions choose the structure, and the packet should answer all four before an instrument is named:

1. **How far** do I think it goes? — determines whether a cap is free money or a real cost.
2. **By when?** — determines tenor, and tenor determines the decay you pay.
3. **What is implied volatility telling me?** — determines whether you should be a buyer or a seller of premium.
4. **What is the worst case I will tolerate?** — determines whether the structure may have an undefined tail at all.

A trader who answers only the first question buys a call. A trader who answers all four buys the cheapest structure that pays for the move he actually expects, and stops paying for the parts he does not.

## Chapter 2 — The four shapes

Everything in this paper is built from four primitives. Each is drawn at expiry, as profit and loss against the underlying's level, with a strike at 100 and a premium of 4.

*[Figure 1 — payoff diagram; rendered in the HTML edition]*

Read them as commitments rather than as bets.

**Long call.** You have paid 4 for the right to buy at 100. Your loss is capped at what you paid; your gain is unbounded; you need the underlying above 104 to break even, which means *you need to be right about direction and magnitude and timing simultaneously.* This is the most-bought and least-considered structure in retail trading.

**Long put.** The mirror image, and the only clean way to be short with a known worst case. The Doctrine's meme rule — shorts default to defined risk — is a rule about this shape versus the shape below it.

**Short call.** You have received 4 and accepted an unbounded obligation. The payoff picture is the entire argument for why the Doctrine forbids naked short calls: the good outcome is a small number that repeats and the bad outcome has no floor.

**Short put.** You have received 4 and agreed to buy at 100 no matter what. The loss is bounded only by zero, which is not the same as bounded. Sold deliberately against cash you intend to deploy, it is a reasonable way to get paid for patience; sold for income against nothing, it is the structure that ends accounts.

**The asymmetry to internalize:** buying options means paying for a right and losing slowly; selling options means being paid for an obligation and losing suddenly. Neither is better. They fail in different directions, and the failure directions are what a book must diversify.

## Chapter 3 — Your greeks, not the dealer's

Five numbers describe how a position's value changes. State them as sentences about your own book.

| Greek | Sentence about your position | Sign when you own options |
|---|---|---|
| **Delta** | If the underlying moves one point, I make delta | + for calls, − for puts |
| **Gamma** | As it moves, my delta improves in my favor | **+** — the good half of owning options |
| **Theta** | Every day that passes costs me theta | **−** — the price of the good half |
| **Vega** | If implied volatility rises one point, I make vega | **+** |
| **Rho** | Rates matter, and at long tenors they matter a lot | + for calls |

The whole of options trading sits in one trade-off: **long gamma and short theta are the same position seen from two sides.** You are paid for movement and charged for time, and the exchange rate between the two is implied volatility. If the underlying moves more than implied volatility said it would, owning the option wins; if it moves less, decay wins. Every structure in Part II is an attempt to tilt that exchange rate.

A practical corollary the Doctrine's Book C rules already assume: **gamma is largest and theta is worst at the money and near expiry.** A same-day at-the-money option is nearly all gamma and nearly all decay; a one-year option is nearly all vega and rho. The tenor decision is therefore a decision about which greek you want to be exposed to, not merely about how long you want to be in the trade.

## Chapter 4 — The three prices inside every option

An option's premium decomposes into three things you are paying for, and a disciplined buyer knows which one he is actually buying:

**Intrinsic value** — what you would get by exercising now. Free of assumption; it is arithmetic.

**Time value** — the value of optionality over the remaining life. Decays as √T, which is the shape in Figure 4 and the reason the last third of an option's life is the expensive third.

**The volatility premium** — the difference between the implied volatility you paid and the realized volatility you will get. Structurally, index implied volatility has exceeded subsequent realized volatility most of the time — the variance risk premium the *Volatility* paper measures — which means **the buyer of index options starts behind on average and must have a reason.** "I think it goes up" is not a reason to be long premium; "I think it moves more than the market expects, in this direction, by this date" is.

---

# Part II — The Structures

## Chapter 5 — One thesis, three expressions

Suppose the thesis is: *the index rallies toward the call wall at +10% over the next month.* Three instruments express it, and the figure shows why they are not interchangeable.

*[Figure 2 — payoff diagram; rendered in the HTML edition]*

**Long index.** Linear, uncapped, no decay, no expiry — and the full downside. Correct when the view has no deadline and no magnitude, i.e., when it is an allocation rather than a trade.

**Long call.** Convex, loss capped at the premium, and a breakeven above spot. It buys the tail you may not need — everything above +10% — and charges you for it every day.

**Call spread.** Buy the 100 call, sell the 110. Cost falls to 2 from 4; the breakeven falls from 104 to 102; the maximum profit becomes 8 instead of unbounded. **You have sold the part of the distribution your own thesis said would not happen, and used the proceeds to lower your breakeven.**

That last sentence is the paper's central practical idea. A cap is only a cost if your thesis expected to reach it. The Doctrine's expression rules default Book C to verticals for exactly this reason: a setup that names a target has already declared where its cap belongs.

## Chapter 6 — Verticals: the workhorse

*[Figure 3 — payoff diagram; rendered in the HTML edition]*

Four numbers define every vertical, and a packet that names an instrument should name all four:

- **Debit** (what you pay) = maximum loss.
- **Width** (distance between strikes) − debit = maximum profit.
- **Breakeven** = long strike + debit.
- **Risk–reward** = (width − debit) ÷ debit.

Four rules of thumb that follow from the arithmetic:

*Pay no more than a third of the width* for a directional debit spread you expect to win roughly half the time; the resulting two-to-one payoff is what makes an ordinary hit rate profitable.

*Put the short strike at your target, not beyond it.* Selling a strike you expect to be exceeded converts a winning thesis into a capped one.

*Use debit spreads when implied volatility is high and outright options when it is low* — because a debit spread is short vega on the wing you sold, which partly neutralizes the volatility you are overpaying for.

*Credit spreads are the same picture reflected.* Selling the 100/110 put spread for 2 is buying the 100/110 call spread's mirror: maximum profit 2, maximum loss 8. It wins more often and loses bigger, and the Doctrine's asymmetry rules — asymmetry before hit rate — are a standing bias against it.

## Chapter 7 — Time spreads: calendars and diagonals

A **calendar** sells a near-dated option and buys a longer-dated one at the same strike. It profits if the underlying sits near the strike while the near leg decays faster than the far leg — which is the √T shape in Figure 4 expressed as a trade. It is long vega and short gamma: it wants stillness now and volatility later.

*[Figure 4 — payoff diagram; rendered in the HTML edition]*

A **diagonal** does the same across different strikes, adding a directional tilt. Both structures share a hazard worth stating once: **their maximum loss is not the debit** in every scenario, because the two legs respond to a volatility change differently, and a violent move can widen the near leg faster than the far leg gains. The Doctrine's requirement that a structure be exitable in one session at ordinary size is the binding constraint on using them at all.

Calendars belong to one specific and useful case: a *known date* — an earnings print, a policy meeting, an expiry — where you expect stillness before and movement after. That is a narrow case, and outside it the structure is usually a way of being wrong in two dimensions at once.

## Chapter 8 — The volatility structures: pictures, mechanics, and when to use each

*Every structure below is drawn at expiry with the strikes stated, and each entry answers the same four questions: what are the legs, what does it bet on, what is its greek posture (gamma, theta, vega), and in which of the Doctrine's regimes does it belong. A terminology note first, because the names are inconsistent across brokers and books: this paper names every structure by its legs, and where a common name is ambiguous it says so.*

### 8.1 The four basic volatility shapes

*[Figure set 8a — payoff diagrams; rendered in the HTML edition]*

**Long straddle** — buy the at-the-money call and put, same strike, same expiry. *Bets on:* a large move in either direction, larger than the premium. *Posture:* long gamma, long vega, short theta — the purest long-volatility position. *Cost:* about 0.8 × σ × √T of spot; at 16% vol a one-year straddle is ~13%, a three-month ~6.4%. *Use when:* implied volatility is demonstrably cheap against realized history and a catalyst with an unknown sign is near — a binary event, a policy decision. *Do not use when:* the event is already priced (the Chapter 10 crush) or when you have a directional view, which wastes half the premium.

**Long strangle** — the same idea with out-of-the-money strikes. *Bets on:* a *big* move either way. *Posture:* long gamma and vega, short theta; cheaper than the straddle and needs a larger move to pay. *Use when:* the straddle's cost is prohibitive and the expected move is extreme. *The trap:* it is the structure most often bought before events by people who have not checked what implied volatility already prices, because it *feels* cheap.

**Long butterfly** — buy one lower call, sell two at-the-money calls, buy one higher call (or the same with puts). *Bets on:* **stillness** — the underlying finishing at or near the middle strike. Maximum profit is at the middle strike; the loss is capped at the small debit on either side. *Posture:* short gamma and short vega near the middle strike, long theta — it earns as time passes with the underlying pinned. *Use when:* the Dealer's Hand's pin reading is strong — a positive-gamma regime with a large open-interest peak at a strike and expiry approaching — and you want to be paid for the pin at defined risk. *This is the Doctrine-compliant way to express "it pins here."*

**Iron condor** — sell an out-of-the-money put spread *and* an out-of-the-money call spread, collecting a credit. *Bets on:* a range — the underlying finishing between the short strikes. *Posture:* short gamma, short vega, long theta. *Risk:* defined by the wing width, which is why the Doctrine permits it and forbids the naked strangle it resembles. *Use when:* implied volatility is high relative to realized, the regime is Calm or positive-gamma, and the Dealer's Hand's walls bracket the range. *Do not use when:* the regime is Rising or Stressed, or a tier-1 event sits inside the expiry — a short-volatility position into an event is the reverse of the Chapter 10 rule.

### 8.2 The iron butterfly, both ways — and the name that causes trouble

*[Figure set 8b — payoff diagrams; rendered in the HTML edition]*

The **iron butterfly** — sell the at-the-money straddle, buy an out-of-the-money strangle as wings — is a *credit* structure that bets on stillness, with the same payoff shape as the long butterfly above. It is the higher-credit, tighter-range cousin of the iron condor.

Its mirror, **buy the at-the-money straddle and sell the wings**, is a *debit* structure that bets on movement in either direction, capped at the wings. The standard name is **reverse iron butterfly**; some brokers call it a "long iron butterfly," which is the source of endless confusion, because in the same broker's vocabulary the plain "iron butterfly" is the sold version. **This paper uses "reverse iron butterfly" for the movement structure from here on**, and Part IV's dual-directional construction is built from it. Its posture is long gamma, long vega, short theta; its cost is the straddle minus the wings — roughly 6% of notional for a one-year ±10% structure at 16% vol; its use case is Chapter 14's: a large move of unknown sign by a known date, funded properly.

### 8.3 The convexity structures the Doctrine's books actually need

The four shapes above are the textbook set. The four below are the ones this operator's books call for, and each has a home in a specific book.

*[Figure set 8c — payoff diagrams; rendered in the HTML edition]*

**Collar** — own the index, buy a put below, sell a call above; choose the strikes so the call's premium pays for the put. *Bets on:* holding equity exposure through a period in which you cannot afford to be wrong about timing. *Posture:* long the underlying, with delta reduced and gamma near zero inside the strikes. *Cost:* the cap and the dividends you keep (unlike a buffered fund, the underlying is still yours). *Use when:* **Book A holds beta through a Transition or Stressed regime** — the Doctrine's "convexity-managed form" is literally this. *The trade-off:* a zero-cost collar in a high-skew market has a stingy cap, because puts are dear and calls are cheap; the put-spread collar fixes that.

**Put-spread collar** — the same, with a put *spread* instead of a put: buy the 95 put, sell the 85 put, sell the 110 call. *Bets on:* protection against the ordinary correction (down 5–15%) while accepting the tail below it, in exchange for a higher cap. *Use when:* the *Base Rates* reading says the likely drawdown is a correction, not a crash, and the tail is covered elsewhere — by the tail-hedge budget — rather than in this position. *This is the buffered fund of Chapter 12 built by hand, with control of the dates and no fee.*

*[Figure set 8d — payoff diagrams; rendered in the HTML edition]*

**Put backspread** — sell one put near the money, buy two further out, for roughly zero cost. *Bets on:* a *crash*, cheaply. The payoff is flat or slightly positive if nothing happens, has a valley of loss at the long strike, and becomes **convex** — accelerating profit — below it. *Posture:* long gamma and vega in the tail, roughly neutral near spot. *Use when:* **the Doctrine's tail-hedge budget wants convex crash protection that expires worthless cheaply most months** — this is that instrument, and it is what "a small long-volatility structure" in the budget's description should usually mean. *The trap:* the valley — a modest decline to the long strike at expiry is the worst outcome, so the structure wants either nothing or a lot, and it wants to be entered when skew is *low* (the long puts are cheaper relative to the short one).

**Call backspread** — the mirror: sell one call near the money, buy two further out. *Bets on:* a melt-up, cheaply. *Use when:* the Volatility paper's regime says a squeeze or a right-tail is live and you want convex participation without paying for a call outright. *For Book D's "mispriced optionality" edge, this and the put backspread are the natural expressions.*

*[Figure set 8e — payoff diagrams; rendered in the HTML edition]*

**Risk reversal** — buy an out-of-the-money call, sell an out-of-the-money put. *Bets on:* direction, harvesting the skew — because puts are structurally richer than calls in equity indices, the pair is often entered for a *credit*. *Posture:* long delta, long the tail on the call side, **short the tail on the put side with undefined risk below the put strike.** *Use when:* a professional wants cheap directional exposure and is prepared to own the underlying at the put strike. *For this book:* the short put is a naked short, which the Doctrine forbids unless cash-secured at a level you want to own — so the risk reversal is admissible only as a cash-secured structure in Book A's rebalance, never in Book C. It is described here because you will see it constantly and should know what it is.

**Broken-wing butterfly** — a butterfly with unequal wings: buy 100, sell two 105s, buy 115 (the upper wing twice as wide). The asymmetry lets it be entered for a *credit*, which makes the lower side free. *Bets on:* a modest directional drift to the middle strike, with no cost if you are wrong in the other direction. *Posture:* like a butterfly, with the risk moved entirely to one side. *Use when:* you have a directional target (the middle strike) and want the position to cost nothing if the underlying goes the other way — a Book C setup with a target and a positive-gamma regime. *The trap:* the risk above the upper short strike is real and is the price of the free side.

### 8.4 The income pair, and the Doctrine's line

**Covered call** — own the underlying, sell a call against it. It is a collar without the put, and it caps upside for premium. **Cash-secured put** — sell a put with the cash to buy the shares set aside. It is the risk reversal's short leg alone, and it is paid for patience. The Doctrine permits the second at a level you want to own and in Calm regimes only, and treats the first as a Book A rebalancing tool rather than a trade. Neither is an income strategy in the sense the retail literature means: both are short volatility, both lose in the direction the premium did not cover, and both are the shapes in Chapter 2's bottom row wearing a friendlier name.

### 8.5 The iron condor in depth — the structure retail trades most and understands least

The iron condor deserves more than the paragraph in 8.1, because it is the default "income" structure of the retail options world and its arithmetic is the opposite of what the marketing implies.

**The arithmetic.** A typical condor sells a put spread and a call spread each ten points wide, roughly one standard deviation out, for a combined credit of perhaps three. Maximum profit is the three; maximum loss is the ten-point wing minus the three — seven. **You are risking seven to make three**, and the structure is built so that the seven happens rarely. Its hit rate can run seventy to eighty percent. Its expectancy is the hit rate times three minus the miss rate times seven, and at a seventy-five percent hit rate that is +2.25 − 1.75 = **+0.5 per trade before costs**, on seven at risk — a thin margin that transaction costs, one bad month, and the volatility-clustering the *Base Rates* paper documents can erase. This is the Doctrine's *asymmetry before hit rate* rule made numerical: the condor is the archetype of the high-hit-rate, negative-asymmetry structure the rule was written against.

**When it nonetheless belongs in Book C.** Three conditions, all required: implied volatility high relative to the name's realized history (so the credit is genuinely rich); a Calm or positive-gamma regime with the Dealer's Hand's walls bracketing the short strikes (so the range has a mechanism); and no tier-1 event inside the expiry. Absent any one, the structure is a bet that nothing happens, sold at a price that assumes nothing happens.

**Managing it, which is where the money is actually made or lost.** Four rules, each with its reason.

*Close at half the credit.* Once the position has earned fifty percent of its maximum, the remaining fifty is being earned against the full seven of risk — the risk-reward has inverted. Closing early is the single most important condor habit.

*Manage at three weeks to expiry.* Gamma accelerates into expiry (Chapter 9); a condor held into its final weeks is a short-gamma position at exactly the moment gamma is largest, and a two-percent move can take it from a winner to a max loser in a session. Close or roll before the final three weeks regardless of P&L.

*Roll the untested side, never the tested one.* When the underlying moves toward one wing, the standard adjustment is to move the *other* spread closer, collecting more credit to offset. Chasing the tested side — rolling the losing spread further out — converts a defined loss into a larger defined loss with a worse probability.

*Never let it expire with a short strike near the money.* The pin-risk problem of Chapter 11, four times over. In cash-settled index options it cannot bite; in equity or ETF options it can produce an assignment on one leg and not the other, leaving a position you did not intend at a price you did not choose.

### 8.6 The other four-leg structures

*[Figure set 8f — payoff diagrams; rendered in the HTML edition]*

**Reverse iron condor** — buy the put spread and the call spread, paying a debit. *Bets on:* a breakout beyond a range, in either direction. It is the iron condor's mirror and the reverse iron butterfly's wider, cheaper cousin: cheaper because the long strikes are further out, and requiring a larger move for the same reason. *Use when:* a known catalyst, unknown sign, and a range whose edges you can name — an expiry-week range with the walls as the strikes.

**Long call condor** — the same shape as the iron condor built entirely from calls (buy low, sell two middle strikes, buy high). Drawn to make one point: **the iron condor and the call condor are the same payoff**, one entered for a credit and one for a debit, and the choice between them is about margin treatment and execution, not economics. In practice the iron version is preferred because each spread is separately liquid.

**Double diagonal** — sell a near-dated strangle, buy a further-dated strangle at wider strikes. *Bets on:* stillness *now* and a volatility expansion *later* — the calendar of Chapter 7 built on both sides at once. *Posture:* short near gamma, long far vega. *Use when:* the near expiry is quiet and a known event sits in the far one. *The trap:* the same as every time spread — the two expiries respond to a volatility shock differently, and the maximum loss is not the debit in every path. Exitable-in-one-session is the binding constraint.

**The diagonal as a synthetic covered call** — buy a deep-in-the-money long-dated call (a LEAP, delta near 0.9) instead of the stock, and sell a near-dated call against it. *Bets on:* the same thing a covered call does, with a fraction of the capital. *Use when:* **Book A wants beta exposure with capped upside and less capital at risk** — the LEAP's cost, not the stock's price, is the maximum loss, which is why it is drawn here. *The trap:* the LEAP has its own theta and its own expiry, and a strategy that rolls a deep-in-the-money LEAP every year is paying a spread on a large notional each time.

### 8.7 Entering, margining, and exiting a multi-leg position

The mechanics matter as much as the shape, and they are where a correct structure loses money.

**Enter as one order, not as legs.** Every broker supports a combination order that executes all legs simultaneously at a net price. Legging in — buying the long side and then selling the short side — exposes the position to *leg risk*: the market moves between fills and the structure is entered at a worse net price, or one leg fills and the other does not, leaving a naked position that the Doctrine forbids. The rule is absolute: **a multi-leg structure is entered and exited as a single combination order at a net limit price.**

**The net limit, not the mid.** A four-leg order quoted at a mid of 3.00 will often fill at 2.85; the spread on a four-leg combination is the sum of four spreads, and in anything but the most liquid index chains it is the dominant cost. Chapter 11's arithmetic quadruples.

**Margin.** A defined-risk spread is margined at its maximum loss — the width minus the credit — which is the reason the Doctrine can size Book C by dollars of risk: the margin *is* the risk. An undefined-risk structure is margined by a formula on the underlying's notional that can change overnight, which is the second reason the Doctrine excludes them.

**Assignment on the short legs.** In equity and ETF options, any short leg can be assigned early, most predictably a short call the day before a dividend when the dividend exceeds the remaining time value. An early assignment on one leg of a four-leg structure leaves three legs and a stock position; the structure is broken and must be repaired at market. **In cash-settled index options this cannot happen**, which — together with the spread arithmetic and the Section 1256 treatment — is the third and strongest reason Book C lives in the SPX family.

**Exit before the final week.** For any structure with a short strike, the last week is where gamma, pin risk, and assignment risk all peak at once. The management rule from 8.5 generalizes: a multi-leg position with short legs is closed or rolled before its final week, whatever its P&L.

### 8.8 What the chapter excludes, and why

| Structure | Why it is not here |
|---|---|
| Ratio spread (sell two, buy one) | A naked short leg; undefined risk on one side |
| Jade lizard, big lizard | A naked short put under a friendly name |
| Ladders (long call ladder, etc.) | A naked short leg at the top |
| Seagulls and other three-leg FX structures | A naked leg, and no consumer in this book |
| Short straddle, short strangle | Chapter 2's bottom row, twice |
| Box spreads as a trade | Covered in Chapter 13 as a cash-equivalent; not a directional structure |
| Conversions, reversals, dividend arbitrage | Dealer arbitrage; no edge for a small book |

The principle is the Doctrine's second standing rule: no short option without a defined wing. Every structure in this chapter satisfies it; every structure in this table fails it.

### 8.9 A map of the chapter

| Structure | Bets on | Gamma / theta / vega | Defined risk? | Home book | Regime |
|---|---|---|---|---|---|
| Long straddle | Big move, either way | + / − / + | Yes | C, D | Calm, cheap vol, catalyst near |
| Long strangle | Very big move | + / − / + | Yes | D | Same, extreme move expected |
| Long butterfly | Stillness at a strike | − / + / − | Yes | C | Positive gamma, strong pin |
| Iron condor | Range | − / + / − | Yes | C | Calm, high vol, walls bracket |
| Iron butterfly | Stillness | − / + / − | Yes | C | Same, tighter |
| Reverse iron butterfly | Move, either way, capped | + / − / + | Yes | C, D; Part IV | Known date, unknown sign |
| Collar | Hold beta with a floor | ~0 / ~0 / ~0 | Yes | **A** | Transition, Stressed |
| Put-spread collar | Hold beta, buffer the correction | ~0 inside | Tail open below | **A** | Same, when the tail is hedged elsewhere |
| Put backspread | Crash, convexly | + tail / ~0 / + | Yes (valley) | **D tail budget** | Any; enter on low skew |
| Call backspread | Melt-up, convexly | + tail / ~0 / + | Yes (valley) | D | Squeeze regimes |
| Risk reversal | Direction, skew-funded | + / ~0 / mixed | **No** | A only, cash-secured | Calm |
| Broken-wing butterfly | Drift to a target, free if wrong | − / + / − | One side | C | Positive gamma, target known |
| Reverse iron condor | Breakout beyond a range | + / − / + | Yes | C, D | Known catalyst, range edges named |
| Double diagonal | Stillness now, vol later | − near / + far | Not the debit in every path | C | Quiet near expiry, event in the far one |
| Diagonal (synthetic covered call) | Beta with a cap, less capital | + / − / + | LEAP cost | **A** | Any; roll cost is the tax |

The column that matters most is *home book*. A structure is not good or bad; it is appropriate to a book, a regime, and a thesis shape, or it is not. The Doctrine's expression table in Chapter 17 is this map with the regime dials in charge.

---

# Part III — The Three Costs

## Chapter 9 — Decay

Time value decays as the square root of time remaining, which means the decay *rate* accelerates as expiry approaches: roughly half of an option's time value is gone at a quarter of its life remaining. Figure 4 is that curve.

Three consequences. **Short-dated options are decay instruments and long-dated options are volatility instruments** — a one-week option is a bet on a move by Friday, a one-year option is a bet on the volatility surface. **Rolling short-dated options to maintain a view is the most expensive way to hold it**, because each roll pays the steepest part of the curve again. And **a long-dated option held for a short view wastes most of what it paid for**, which is the mirror error.

## Chapter 10 — Volatility, the second price

You can be right about direction and lose money because you paid the wrong price for movement. The clearest case is an earnings print.

*[Figure 5 — payoff diagram; rendered in the HTML edition]*

Implied volatility is bid up into a known event and collapses the instant the uncertainty resolves. A trader long a call into the print needs the move to exceed *the move the market already priced*, not merely to be in the right direction. The *Base Rates* paper's number is the operative one: implied moves have on average slightly exceeded realized moves, so buying the event is a negative-expectancy trade on average with a fat right tail.

**The rule that follows:** never express a directional event view with a long single option unless the implied move is demonstrably cheap relative to that name's own history. Use a spread, which is partly immune to the crush because you sold volatility too, or express the view after the print, when the crush has already happened and you are buying cheap optionality on the reaction.

## Chapter 11 — Frictions, assignment, and the traps

**The spread is the tax.** Liquid index options cross for pennies; a far out-of-the-money single-name option can cost five to fifteen percent of premium in the round trip. The *Base Rates* arithmetic is blunt: at Book C's standard risk, a wide single-name option can consume a tenth of the risk budget before the thesis is tested. **This is the single strongest argument for the Doctrine's restriction of Book C to index instruments**, and it is an arithmetic argument, not a preference.

**Assignment and exercise.** American-style options on equities and ETFs can be exercised against you at any time, and early assignment on a short call typically comes the day before an ex-dividend date when the dividend exceeds the remaining time value — the one predictable case. European-style index options (the SPX family) cannot be assigned early, settle in cash, and carry no assignment risk at all, which is a second structural reason index expression is cleaner.

**Pin risk.** A short option that finishes within pennies of the strike leaves you not knowing on Friday evening whether you will own a position on Monday morning. Cash-settled index options eliminate it. For anything else, the rule is to close rather than to let expire.

**Tax.** Broad-based index options and futures are Section 1256 contracts: marked to market at year end, taxed at a blended long/short rate regardless of holding period, and exempt from wash-sale rules. Equity and ETF options are not. **The same view expressed on SPX and on SPY has a different after-tax value**, and the expression table should know it. The mark-to-market feature cuts both ways — it accelerates gains as well as losses into the current year.

---

# Part IV — Engineered Payoffs

*The rest of the paper builds shapes that no single option produces: capped-and-buffered exposure, principal protection, and payoffs that profit in both directions. Each is presented three ways — the picture, the replication from listed instruments, and the honest comparison to owning the index.*

## Chapter 12 — Defined-outcome and buffered funds

The packaged version, and the baseline the later chapters improve on.

*[Figure 6 — payoff diagram; rendered in the HTML edition]*

A buffered fund holds a portfolio of index options that delivers, over a stated outcome period, a payoff of: full participation up to a cap, no loss within a buffer, and one-for-one losses below the buffer. The construction is a **collar with a spread**: long the index synthetically (long call, short put at the money), long a put spread covering the buffer zone, short a call at the cap to pay for it.

The honest accounting versus owning the index:

| | You give up | You receive |
|---|---|---|
| Dividends | Every one, for the outcome period | — |
| Upside above the cap | All of it | — |
| Downside within the buffer | — | Protection |
| Downside below the buffer | — | Nothing; one-for-one from there |
| Fees | 70–90 basis points a year, typically | — |

Two structural cautions that the marketing does not lead with. **The protection exists only at the end of the outcome period** — buy midway through and the cap and buffer you get are not the advertised ones, and mark-to-market during the period can be well below the floor. And **the cap is set by prevailing volatility and rates at issue**: in a low-volatility, low-rate environment the cap is stingy, because there is less premium to sell.

## Chapter 13 — Synthetic principal protection: a cash-equivalent fund plus long-dated calls

### 13.1 The idea in one sentence

Put enough in an instrument that grows to your whole principal by the horizon, and spend the rest on long-dated call options. If the market falls you get your money back; if it rises you participate at whatever rate the leftover cash could buy.

*[Figure 7 — payoff diagram; rendered in the HTML edition]*

### 13.2 The arithmetic, worked

Take a five-year horizon and a 4% risk-free rate.

- **The floor leg.** The present value of $100 in five years at 4% is **$82.19**. That amount, in Treasury bills, a bill ladder, STRIPS, or a box-spread fund such as BOXX, grows to $100 regardless of what equities do.
- **The upside leg.** The remaining **$17.81** buys long-dated index calls. A five-year at-the-money index call, at plausible long-dated implied volatility, costs on the order of 20–24% of notional. At 22%, $17.81 buys **$81 of notional — a participation rate of roughly 81%.**

So the structure is: **no loss at maturity, and 81 cents of every dollar the index gains in price.** Figure 7 is that payoff.

### 13.3 What BOXX is, and its specific risk

BOXX is an exchange-traded fund that holds **box spreads** on index options — a combination of a call spread and a put spread at the same strikes, which has a fixed payoff at expiry and therefore behaves like a zero-coupon bond synthesized entirely from options. Its economic return tracks short-term rates closely.

The reason it exists is tax, not economics: because the fund's return arrives as share-price appreciation rather than as interest distributions, a holder can defer recognition and — on the fund's own reading — realize long-term capital gain rather than ordinary income on a sale after a year. **That treatment is a position, not a settled fact.** The straddle and constructive-ownership rules exist precisely to address arrangements of this shape, and a future ruling or examination could recharacterize it. The paper's position: BOXX is a legitimate cash-equivalent with a *tax-treatment risk that must be sized as a risk*, and the operator's accountant governs. A bill ladder or STRIPS does the same job with certain tax treatment and less optionality about the answer.

### 13.4 Against the honest baseline: just owning the index

This is the comparison that matters, and it is less flattering to the structure than its marketing suggests.

| Over a five-year horizon | Own the index | Synthetic PPN |
|---|---|---|
| Dividends (≈1.2%/yr) | **≈ +6.2% cumulative** | **Zero** |
| Participation in price gains | 100% | ≈ 81% |
| Worst case | The full drawdown | 0% (at maturity only) |
| Expected value | Higher | Lower by roughly 3–5 percentage points a year in a normal market |
| Volatility experienced | Full | Much lower |
| Mid-period marks | Track the index | Can be well below the floor |
| Complexity, roll, tracking | None | Real |

**Run the base rates against it.** Rolling five-year periods for U.S. equities have been positive something like 88–90% of the time. So the floor pays off in roughly one period in ten, and in the other nine you have paid — every year — the dividend yield plus a fifth of the upside for insurance you did not need. On expected value, **the structure is materially worse than owning the index.** On volatility and on worst case it is materially better. Whether that trade is good depends entirely on which constraint binds.

### 13.5 When it is nonetheless the right instrument — the case for this operator specifically

There is one condition under which a structure with a lower expected return is the correct choice, and the Doctrine names it explicitly: **when the alternative is not owning the index but owning cash.**

The Doctrine's own record of the operator says he has been under-invested since 2008, that Book A's *floor* is a more binding constraint for him than its ceiling, and that his tail concern has historically expressed itself as absence from the market rather than as a hedge. For a trader whose realistic alternative to a protected structure is a cash allocation earning the risk-free rate, the comparison is not "index versus PPN" but "4% versus 81% of the index with no downside" — and that comparison is not close.

**This is the honest use case: principal protection is a behavioral instrument.** It converts an unwillingness to hold equity risk into a holding of equity risk. The Doctrine's Book A language — that exposure through a Transition or Stressed regime is *converted to a convexity-managed form rather than reduced to zero, because reducing to zero is the retail behavior that guarantees missing the recovery* — is describing exactly this structure and exactly this purpose. Used that way it is excellent. Used as a replacement for an allocation the operator would have held anyway, it is an expensive way to underperform.

### 13.6 Variants worth knowing

**Partial protection is usually better value.** Protecting against the first 10% of loss rather than 100% of loss frees most of the budget for participation: a floor at −10% instead of 0% can lift participation from roughly 81% toward 100% or above.

**Leveraged participation.** Spending the same budget on calls struck below the money, or on a call spread rather than an outright call, buys more participation over a defined range at the cost of a cap — which converges on the buffered fund of Chapter 12 built by hand, at lower fees and with control over the cap and the dates.

**Ladder the maturities.** A single five-year structure has a single date on which the floor is real. Four overlapping structures maturing in successive years give a floor that is always somewhere near, at the cost of more rolls.

## Chapter 14 — Dual-directional: profiting in both directions

### 14.1 What the structured product does

The dual-directional or "absolute return" note pays you the index's gain up to a cap **and** pays you the absolute value of the index's *loss* up to a barrier — so a −7% index is a +7% payoff. Below the barrier, the feature vanishes and you take the loss from the original level.

*[Figure 8 — payoff diagram; rendered in the HTML edition]*

Look at the cliff at the barrier in Figure 8. At −10% the note pays **+10%**; a fraction below it, the note pays **−10%**. That twenty-point discontinuity is not a quirk of the drawing; it is how barrier notes are built, and it is the reason they are sold. **The issuer funds your "free" absolute return by buying your tail from you at a discontinuous price.** Any reader who finds the shape appealing should look at the cliff for a full minute before reading on.

### 14.2 Building the same shape from listed options

The good news is that the shape is buildable without the cliff, because the cliff is the funding mechanism, not the payoff.

*[Figure 9 — payoff diagram; rendered in the HTML edition]*

**Long the at-the-money call and put, short the out-of-the-money call and put — a reverse iron butterfly (Chapter 8.2).** It profits from a move in either direction and caps at the wings you sold. There is no barrier, no discontinuity, no issuer credit risk, and no tail sale: your worst case is the debit you paid.

The debit is the catch. A twelve-month structure at roughly 16% implied volatility, with wings at ±10%:

| Leg | Approximate cost, % of notional |
|---|---|
| Long at-the-money call | ≈ 7.5 |
| Long at-the-money put | ≈ 5.5 |
| Short 110 call | ≈ −3.0 |
| Short 90 put (richer, from skew) | ≈ −4.0 |
| **Net debit** | **≈ 6.0** |

So the listed version breaks even at roughly ±6% and pays a maximum of about +4% at either wing. That is *not* the note's payoff, which appeared to profit on a 2% move. The difference is the funding, and the funding is the whole subject of the next section.

### 14.3 Funding it properly: the cash-equivalent leg is the missing piece

The note does not profit on small moves by magic. It profits because the issuer funds the option package from three sources: **the interest on your principal for the term, the dividends you forgo, and the tail you sold.** Reproduce the first two and decline the third, and you have a strictly better instrument.

**The construction.** Put most of the capital in the cash-equivalent leg — bills, STRIPS, or BOXX — and spend the interest on the reverse iron butterfly.

Worked, at a 4% rate over twelve months, with the butterfly costing 6% of notional:

- Allocate **$96.15** to the floor leg → grows to **$100** at the horizon. Floor at 0%.
- Allocate the remaining **$3.85** to the butterfly at 6% of notional → **64% participation.**
- **Result: no loss at maturity; +6.4% if the index is ±10%; 0% if the index is unchanged.**

Or, accepting a small floor breach for a much better shape:

- Allocate **$94** to the floor leg → **$97.76** at the horizon; floor at **−2.2%**.
- Allocate **$6** to the butterfly → **100% participation.**
- **Result: −2.2% worst case; +7.8% at either ±10%; −2.2% if the index is unchanged.**

Both dominate the note in the left tail — a −30% index costs you nothing or 2.2%, where the note costs you 30% — and both give up the note's headline payoff at exactly the barrier.

### 14.4 Tenor: why three months is hard and five years is easy

*[Figure 10 — payoff diagram; rendered in the HTML edition]*

The single most useful piece of arithmetic in this chapter. **The option package costs roughly 0.8 × σ × √T. The interest available to fund it is roughly r × T.** Cost grows with the square root of time; funding grows linearly. So the ratio of funding to cost improves with tenor, without limit.

At 16% implied volatility and a 4% rate:

| Tenor | Straddle cost | Butterfly (±10% wings) | Interest earned | Self-funding? |
|---|---|---|---|---|
| 3 months | ≈ 6.4% | ≈ 3.5% | ≈ 1.0% | No — you fund ~29% |
| 6 months | ≈ 9.0% | ≈ 4.6% | ≈ 2.0% | No — ~43% |
| 12 months | ≈ 12.8% | ≈ 6.0% | ≈ 4.0% | No — ~67% |
| 3 years | ≈ 22% | ≈ 10% | ≈ 12.5% | **Yes, roughly** |
| 5 years | ≈ 29% | ≈ 13% | ≈ 21.7% | **Yes, comfortably** |

**This is why every principal-protected note you have ever been offered was long-dated, and why a three-month "profit either way with no downside" product does not exist without a tail sale.** At short tenors the interest simply is not there, and the only remaining funding sources are your dividends, a tighter cap, or your tail. Structured-product desks choose the tail. You should choose the cap.

At three and six months, the honest constructions are therefore:

- **Three months:** narrow the wings to ±5% (butterfly cost falls to roughly 2%), fund half from interest and half from cash, accept a floor around −1%. Payoff: up to about +4% if the index moves 5% either way, roughly −1% if it does not.
- **Six months:** wings at ±7%, cost around 3.5%, interest 2%, floor around −1.5%, participation near 100%, maximum payoff near +7% at either wing.
- **Twelve months:** the worked example in 14.3.

### 14.5 The honest comparison, and when this is ever right

| | Own the index | Dual-directional note | Listed replication (bills + iron butterfly) |
|---|---|---|---|
| Best case | Unbounded | Cap | Cap |
| Flat market | ≈ dividends | ≈ 0% | ≈ 0% to −2% |
| −7% market | −7% | **+7%** | +5% to +7% |
| −30% market | −30% | **−30%** | 0% to −2% |
| Dividends | Yes | No | No |
| Credit risk | None | **The issuer's** | None |
| Liquidity | Full | Poor; wide secondary | Full, in liquid index options |
| Fees | ~0 | 2–4% embedded | Spreads and commissions only |
| Tax | Qualified dividends, LTCG | Often ordinary income | **Section 1256: 60/40, marked to market** |

**When it is right:** when your genuine view is *high volatility with no directional edge over a defined period* — a known binary event with an uncertain sign, an election, a policy decision — and when the alternative is sitting in cash. It is a *volatility* expression wearing an *absolute return* costume, and it should be entered only when the four Part I questions produce "I expect a large move, I do not know the direction, by this date, and my worst case must be small."

**When it is wrong:** as a substitute for an equity allocation. Look at the flat-market row. In a market that is up modestly — the single most common annual outcome, and the base rate says roughly a quarter of years finish between zero and ten percent — the structure earns approximately nothing while the index earns the move plus dividends. **A structure that pays you for surprise is a structure that charges you for calm, and calm is the base case.**

---

## Chapter 15 — Structure versus the index: the scenario matrix

*This chapter is the one to open at the monthly session when the question is "hold the index outright, or wrap it in something." It prices every structure in the paper against the same set of outcomes, on four asset classes whose option costs differ by a factor of six, and it states the decision rules that fall out. Every number is computed — Black–Scholes on the stated inputs, a lognormal expectation for the expected-value column — and the inputs are given so the reader can disagree with them rather than with the arithmetic.*

### 15.1 Method and assumptions

Ten structures, each holding $100 of capital, each evaluated at ten index outcomes at the horizon, plus the expected P&L under a lognormal distribution and the probability of finishing below the starting capital. Dividends and bill interest are included where the structure earns them, because the dividend forgone is the largest hidden cost in most protected structures and a comparison that omits it flatters them.

| Input | U.S. equity | China | Real estate | Crypto |
|---|---|---|---|---|
| Implied volatility | 16% | 28% | 20% | 60% |
| Dividend yield | 1.3% | 2.5% | 3.8% | 0% |
| Assumed drift for the expectation | 8% | 8% | 7% | 15% |
| Risk-free rate | 4% | 4% | 4% | 4% |

*The drift assumptions are the least defensible numbers in the chapter and they only affect the expected-value column, not the scenario payoffs. The volatility figures are representative mid-2026 levels for liquid ETFs on each asset and are the numbers that actually drive the results.*

The structures, with strikes as a percent of spot: **hold the index**; **bills**; **50% index / 50% bills** (the simplest alternative, and the one every option structure must beat); **protective put** (buy the 95 put); **zero-cost collar** (buy the 90 put, sell the call whose premium pays for it); **put-spread collar** (buy the 95/85 put spread, sell the call that pays for it); **covered call** (sell the 105 call); **buffered** (10% buffer, the cap solved so it costs nothing, dividends forgone — the packaged fund's economics); **synthetic principal protection** (bills to the floor, the remainder in at-the-money calls); **bills plus a reverse iron butterfly** (bills to the floor, the remainder in the ±10% movement structure).

### 15.2 U.S. equity, twelve months — the full matrix

*[Figure — US equity (SPY): six structures against the index over 12 months; rendered in the HTML edition]*

| Structure | −30% | −20% | −10% | −5% | 0 | +5% | +10% | +15% | +20% | +30% | **E[P&L]** | P(loss) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Hold the index | -28.7 | -18.7 | -8.7 | -3.7 | +1.3 | +6.3 | +11.3 | +16.3 | +21.3 | +31.3 | **+8.2** | 34% |
| Bills (cash) | +4.0 | +4.0 | +4.0 | +4.0 | +4.0 | +4.0 | +4.0 | +4.0 | +4.0 | +4.0 | **+4.0** | 0% |
| 50% index / 50% bills | -12.3 | -7.3 | -2.3 | +0.2 | +2.7 | +5.2 | +7.7 | +10.1 | +12.7 | +17.7 | **+6.1** | 25% |
| Protective put (buy 95 put, cost 3.0) | -6.7 | -6.7 | -6.7 | -6.7 | -1.7 | +3.3 | +8.3 | +13.3 | +18.3 | +28.3 | **+7.3** | 41% |
| Zero-cost collar (90 put / 119 call) | -8.7 | -8.7 | -8.7 | -3.7 | +1.3 | +6.3 | +11.3 | +16.3 | +20.0 | +20.0 | **+6.6** | 34% |
| Put-spread collar (95/85 / 116 call) | -18.7 | -8.7 | -3.7 | -3.7 | +1.3 | +6.3 | +11.3 | +16.3 | +17.0 | +17.0 | **+6.3** | 34% |
| Covered call (sell 105 call, credit 5.3) | -23.4 | -13.4 | -3.4 | +1.6 | +6.6 | +11.6 | +11.6 | +11.6 | +11.6 | +11.6 | **+5.8** | 22% |
| Buffered (10% buffer, cap +11%) | -20.0 | -10.0 | +0.0 | +0.0 | +0.0 | +5.0 | +10.0 | +11.1 | +11.1 | +11.1 | **+4.5** | 16% |
| Synthetic PPN (bills + LEAP, 51% participation) | +0.0 | +0.0 | +0.0 | +0.0 | +0.0 | +2.5 | +5.1 | +7.6 | +10.1 | +15.2 | **+5.4** | 0% |
| Bills + reverse iron butterfly (53% part., ±10%) | +5.3 | +5.3 | +5.3 | +2.6 | +0.0 | +2.6 | +5.3 | +5.3 | +5.3 | +5.3 | **+4.1** | 0% |


**How to read it.** Three rows are the baselines: the index, bills, and the 50/50 mix. Every other row is a wrapper, and the question for each is what it gives up at the flat and modestly-up outcomes — the base-rate outcomes — to buy what it delivers at the tails.

The reading the paper wants remembered: **at zero, the index earns its dividend and every protected structure earns roughly nothing or pays.** At +10%, the index earns 11.3 and the collar earns the same, the put-spread collar the same, the buffered fund 10.0, the principal-protected note 5.1, the reverse iron butterfly 5.3. The protection's price is paid in exactly the outcomes that happen most.

And the expected-value column is the honest summary: the index at +8.2 leads everything; the 50/50 mix at +6.1 beats every option structure except the protective put and the collar, and does so with no option to price, no roll, and no counterparty; the principal-protected note and the reverse iron butterfly sit at +5.4 and +4.1, barely above bills, because at a twelve-month horizon the interest funds only half the option package — the tenor arithmetic of Chapter 14.4, now in a table.

### 15.3 The price of insurance, by asset class

The table that governs the macro-positioning decision across asset classes. Same structures, same twelve months; what changes is the volatility, and volatility is the price of every option.

| Twelve months | U.S. equity (σ 16%) | China (σ 28%) | Real estate (σ 20%) | Crypto (σ 60%) |
|---|---|---|---|---|
| Cost of a 95 put, % of capital | **3.0** | **7.7** | **5.2** | **18.4** |
| Zero-cost collar: 90 put buys a call at | +19 | +17 | **+13** | +30 |
| Put-spread collar cap (95/85 spread) | +16 | +27 | +14 | +109 |
| Buffered fund cap (10% buffer) | +11 | +23 | **+10** | +104 |
| Principal-protected participation | 51% | 33% | 50% | **15%** |
| Covered call credit, 105 strike | 5.3 | 9.4 | 5.8 | 23.2 |
| Bills + reverse iron butterfly participation | 53% | 47% | 50% | 43%* |

*\*Wings at ±10% are meaningless on a 60%-vol asset — they sit inside a fortnight's noise. Wing width should be set in units of the asset's volatility, not in percent.*

Four readings, one per asset.

**U.S. equity is where option structures are cheapest and therefore most defensible.** A three-percent put, a collar that caps at +19, a buffered fund that caps at +11 — the protection is real and the price is bearable. Even here, Chapter 15.2's expected-value column says the index wins on average and the 50/50 mix is a strong competitor.

**China's volatility premium is the whole story.** The 95 put costs more than double the U.S. figure. Principal protection buys a third of the upside. The collar cap is *tighter* than in the U.S. despite the higher volatility, because puts carry a larger skew premium. **A China position that needs protection is better sized down than wrapped** — the 50/50 row in the China table below beats every option structure on expected value.

**Real estate's dividend is the cost the structures hide.** At a 3.8% yield the forward is well below spot, which makes puts dear and calls cheap — so the zero-cost collar caps at only +13 and the buffered fund at +10, the tightest in the table. And every structure that forgoes the dividend — the buffered fund, the principal-protected note, the reverse iron butterfly — gives up nearly four points a year before the option cost is counted. **For a high-yield asset, the case for the outright holding is strongest and the case for any dividend-forgoing wrapper is weakest.**

**Crypto makes the arithmetic absurd.** An 18% put. A principal-protected note with 15% participation. A covered call whose 23% credit is the entire expected drift. At sixty percent volatility every option is so expensive that the only structures worth considering are the ones that *sell* the volatility — and selling volatility on an asset that can double is the one thing the Doctrine's asymmetry rule most forbids. **The honest crypto structures are the 50/50 mix, a smaller position, or the outright holding sized as Book D sizes things.** Not options.

### 15.4 The other three asset classes — six outcomes each

**China, twelve months**

| Structure | −30% | −10% | 0 | +10% | +20% | +30% | **E[P&L]** | P(loss) |
|---|---|---|---|---|---|---|---|---|
| Hold the index | -27.5 | -7.5 | +2.5 | +12.5 | +22.5 | +32.5 | **+8.1** | 44% |
| Bills (cash) | +4.0 | +4.0 | +4.0 | +4.0 | +4.0 | +4.0 | **+4.0** | 0% |
| 50% index / 50% bills | -11.8 | -1.8 | +3.2 | +8.2 | +13.2 | +18.2 | **+6.1** | 38% |
| Protective put (buy 95 put, cost 7.7) | -10.2 | -10.2 | -5.2 | +4.8 | +14.8 | +24.8 | **+7.1** | 55% |
| Zero-cost collar (90 put / 117 call) | -7.5 | -7.5 | +2.5 | +12.5 | +19.8 | +19.8 | **+5.5** | 44% |
| Put-spread collar (95/85 / 127 call) | -17.5 | -2.5 | +2.5 | +12.5 | +22.5 | +29.2 | **+6.5** | 44% |
| Covered call (sell 105 call, credit 9.4) | -18.1 | +1.9 | +11.9 | +16.9 | +16.9 | +16.9 | **+5.5** | 30% |
| Buffered (10% buffer, cap +23%) | -20.0 | +0.0 | +0.0 | +10.0 | +20.0 | +22.7 | **+3.8** | 33% |
| Synthetic PPN (bills + LEAP, 33% participation) | +0.0 | +0.0 | +0.0 | +3.3 | +6.7 | +10.0 | **+4.8** | 0% |
| Bills + reverse iron butterfly (47% part., ±10%) | +4.7 | +4.7 | +0.0 | +4.7 | +4.7 | +4.7 | **+4.0** | 0% |


**Real estate, twelve months**

| Structure | −30% | −10% | 0 | +10% | +20% | +30% | **E[P&L]** | P(loss) |
|---|---|---|---|---|---|---|---|---|
| Hold the index | -26.2 | -6.2 | +3.8 | +13.8 | +23.8 | +33.8 | **+7.0** | 40% |
| Bills (cash) | +4.0 | +4.0 | +4.0 | +4.0 | +4.0 | +4.0 | **+4.0** | 0% |
| 50% index / 50% bills | -11.1 | -1.1 | +3.9 | +8.9 | +13.9 | +18.9 | **+5.5** | 32% |
| Protective put (buy 95 put, cost 5.2) | -6.4 | -6.4 | -1.4 | +8.6 | +18.6 | +28.6 | **+6.3** | 50% |
| Zero-cost collar (90 put / 113 call) | -6.2 | -6.2 | +3.8 | +13.8 | +17.0 | +17.0 | **+5.3** | 40% |
| Put-spread collar (95/85 / 114 call) | -16.2 | -1.2 | +3.8 | +13.8 | +17.9 | +17.9 | **+5.6** | 40% |
| Covered call (sell 105 call, credit 5.8) | -20.4 | -0.4 | +9.6 | +14.6 | +14.6 | +14.6 | **+5.4** | 29% |
| Buffered (10% buffer, cap +10%) | -20.0 | +0.0 | +0.0 | +10.0 | +10.1 | +10.1 | **+1.5** | 28% |
| Synthetic PPN (bills + LEAP, 50% participation) | +0.0 | +0.0 | +0.0 | +5.0 | +9.9 | +14.9 | **+4.9** | 0% |
| Bills + reverse iron butterfly (50% part., ±10%) | +5.0 | +5.0 | +0.0 | +5.0 | +5.0 | +5.0 | **+4.0** | 0% |


**Crypto, twelve months**

| Structure | −30% | −10% | 0 | +10% | +20% | +30% | **E[P&L]** | P(loss) |
|---|---|---|---|---|---|---|---|---|
| Hold the index | -30.0 | -10.0 | +0.0 | +10.0 | +20.0 | +30.0 | **+16.2** | 52% |
| Bills (cash) | +4.0 | +4.0 | +4.0 | +4.0 | +4.0 | +4.0 | **+4.0** | 0% |
| 50% index / 50% bills | -13.0 | -3.0 | +2.0 | +7.0 | +12.0 | +17.0 | **+10.1** | 49% |
| Protective put (buy 95 put, cost 18.4) | -23.4 | -23.4 | -18.4 | -8.4 | +1.6 | +11.6 | **+13.4** | 63% |
| Zero-cost collar (90 put / 130 call) | -10.0 | -10.0 | +0.0 | +10.0 | +20.0 | +29.8 | **+6.8** | 52% |
| Put-spread collar (95/85 / 209 call) | -20.0 | -5.0 | +0.0 | +10.0 | +20.0 | +30.0 | **+12.8** | 52% |
| Covered call (sell 105 call, credit 23.2) | -6.8 | +13.2 | +23.2 | +28.2 | +28.2 | +28.2 | **+7.4** | 35% |
| Buffered (10% buffer, cap +104%) | -20.0 | +0.0 | +0.0 | +10.0 | +20.0 | +30.0 | **+12.6** | 45% |
| Synthetic PPN (bills + LEAP, 15% participation) | +0.0 | +0.0 | +0.0 | +1.5 | +3.1 | +4.6 | **+5.3** | 0% |
| Bills + reverse iron butterfly (43% part., ±10%) | +4.3 | +4.3 | +0.0 | +4.3 | +4.3 | +4.3 | **+4.0** | 0% |


*[Figure — China (MCHI/FXI): six structures against the index over 12 months; rendered in the HTML edition]*

*[Figure — Real estate (VNQ): six structures against the index over 12 months; rendered in the HTML edition]*

*[Figure — Crypto (BTC ETF): six structures against the index over 12 months; rendered in the HTML edition]*

### 15.5 Six months instead of twelve

Halving the tenor cuts option cost by about 30% (the √T rule) and halves the interest available to fund it. The net effect is that **funded structures get worse and simple hedges get relatively cheaper.**

**U.S. equity, six months**

| Structure | −30% | −10% | 0 | +10% | +20% | +30% | **E[P&L]** | P(loss) |
|---|---|---|---|---|---|---|---|---|
| Hold the index | -29.3 | -9.3 | +0.7 | +10.7 | +20.7 | +30.7 | **+4.1** | 38% |
| Bills (cash) | +2.0 | +2.0 | +2.0 | +2.0 | +2.0 | +2.0 | **+2.0** | 0% |
| 50% index / 50% bills | -13.7 | -3.7 | +1.3 | +6.3 | +11.3 | +16.3 | **+3.0** | 32% |
| Protective put (buy 95 put, cost 1.9) | -6.3 | -6.3 | -1.3 | +8.7 | +18.7 | +28.7 | **+3.6** | 45% |
| Zero-cost collar (90 put / 115 call) | -9.3 | -9.3 | +0.7 | +10.7 | +15.6 | +15.6 | **+3.5** | 38% |
| Put-spread collar (95/85 / 110 call) | -19.3 | -4.3 | +0.7 | +10.4 | +10.4 | +10.4 | **+3.1** | 38% |
| Covered call (sell 105 call, credit 3.0) | -26.4 | -6.4 | +3.6 | +8.6 | +8.6 | +8.6 | **+3.1** | 28% |
| Buffered (10% buffer, cap +5%) | -20.0 | +0.0 | +0.0 | +4.9 | +4.9 | +4.9 | **+1.9** | 12% |
| Synthetic PPN (bills + LEAP, 38% participation) | +0.0 | +0.0 | +0.0 | +3.8 | +7.5 | +11.3 | **+2.4** | 0% |
| Bills + reverse iron butterfly (30% part., ±10%) | +3.0 | +3.0 | +0.0 | +3.0 | +3.0 | +3.0 | **+2.0** | 0% |


The principal-protected participation falls from 51% to 38% and the reverse iron butterfly's from 53% to 30% — the interest simply is not there. The zero-cost collar's cap tightens from +19 to +15, the buffered fund's from +11 to +5. And the protective put falls from 3.0 to 1.9 — the one structure that improves in relative terms at short tenor, because its cost scales with √T and it gives up no upside. **At six months the choice narrows to three: the index, the 50/50 mix, or the index plus a put.**

### 15.6 The decision rules

These fall out of the tables; they are not opinions.

1. **The index wins on expected value in every asset class at every tenor.** Every wrapper is a purchase of a shape, paid for in expected return. The question is never whether the wrapper is cheaper than the index — it is not — but whether the shape is worth its price *to this book in this regime.*

2. **The 50/50 mix is the structure every option structure must beat, and most do not.** It has no option to price, no roll, no counterparty, no forgone dividend, and it beats the buffered fund, the principal-protected note and the reverse iron butterfly on expected value in all four asset classes at twelve months. When the instinct is "I want less risk," halving the position is usually the right answer and the cheapest one.

3. **Option structures earn their place when one of three conditions holds.** *The alternative is cash, not the index* — the behavioral case of Chapter 13.5, where 51% participation with a floor beats 4% in bills for a trader who would otherwise hold bills. *The regime dial forces a floor* — the Doctrine's Transition and Stressed states, where Book A must hold beta and cannot afford to be wrong on timing; here the collar or put-spread collar is the instrument, and its cost is the price of staying invested. *Volatility is demonstrably cheap* — the Chapter 4 test; a put bought at the 20th percentile of its own history is a different purchase from one at the 80th.

4. **Volatility sets the price; check it before choosing the asset to wrap.** A structure that is reasonable on U.S. equity is expensive on China and absurd on crypto, at the same strikes. The price-of-insurance table is the first thing to consult, and for anything above roughly 30% volatility the answer is to size the position, not to wrap it.

5. **Dividend yield sets the hidden cost; the higher the yield, the stronger the case for holding outright.** Every dividend-forgoing wrapper on a 4%-yielder starts four points behind.

6. **Tenor sets what is fundable.** Below a year, interest funds little; the principal-protected and funded-butterfly structures belong at three to seven years or not at all. At six months the menu is the index, the mix, or the index plus a put.

7. **Set wing widths in volatility units.** ±10% is one standard deviation on U.S. equity over a year and a fortnight's noise on crypto. A structure's strikes should be stated as multiples of the asset's σ√T, and the registry entry for any engineered position should record them that way.

### 15.7 The procedure for the monthly session

When Book A's stance calls for holding an asset through the coming period and the question is how:

1. Read the regime dials. If Calm and positive-gamma, the default is the outright holding at the band's stance. Stop here unless a condition in rule 3 applies.
2. If Transition or Stressed, the Doctrine requires a convexity-managed form. Price the collar and the put-spread collar on that asset at the current volatility; choose the put-spread version unless the tail is unhedged elsewhere.
3. Before pricing any wrapper, price the 50/50 mix — halve the position and hold bills. If the wrapper's expected value does not beat it by enough to pay for the complexity, use the mix.
4. Consult the price-of-insurance table for the asset. Above 30% volatility, size rather than wrap. Above 3% yield, prefer the outright holding and a put over any dividend-forgoing structure.
5. Record the decision in the register with the structure's legs, the volatility percentile at entry, and the horizon date — because the floor exists only at that date and a mid-period mark below it is not an invalidation.

The comparison tables are recomputed at each session from the current volatility surface by `tools/structure_compare.py` — the assumptions above are inputs, not constants — and the current run is attached to the session's packet.

---

## Chapter 16 — Leverage: when, how much, and in what form

*Leverage is not a strategy. It is a multiplier on a decision that has already been made, and the Doctrine has already made most of it: the three size tiers, the alignment test for the exceptional tier, the net-exposure cap at the band's top plus fifteen points, the kill-switch ladder that binds leveraged P&L exactly as it binds any other. This chapter answers the questions the Doctrine leaves open — which* form *of leverage, at what* cost*, and* when *— with particular attention to the moment the operator most wants it and is most likely to get it wrong: after the market has fallen.*

### 16.1 The frame: leverage is risk, not notional

The Doctrine sizes in dollars of loss — distance to invalidation times size — and leverage does not change that arithmetic; it changes the instrument that delivers a given dollar of risk. Three consequences before any instrument is named.

**Leverage is measured in risk, never in notional.** A deep-in-the-money call controlling $200,000 of index with $20,000 at risk is a $20,000 position; a futures contract controlling the same with a bracket that stops it at a $20,000 loss is the same position; a margin loan buying $200,000 of index with no stop is a $200,000 position. The register records risk, and the register is right.

**The tier is the leverage decision.** Ordinary, good, and exceptional — one, one-and-a-half, and two times the book's standard risk — are the only leverage settings the Doctrine offers, and the exceptional tier requires all three dials aligned, a High-trust signal, an independent confirmation, and a Top & Bottom reading that does not contradict. *Evidence and Inference* adds the statistical reason those conditions are strict: a doubled position on an edge whose error bar is still the size of the edge is a bet on noise.

**And the caps bind across books.** Net beta-equivalent exposure across all four books may not exceed Book A's band ceiling plus fifteen points. Leverage in Book C does not create room; it consumes it.

### 16.2 The forms of leverage and what each costs

| Form | Leverage at typical size | Financing cost | Defined risk? | Call risk? | Tax | Best use |
|---|---|---|---|---|---|---|
| **Index futures** (ES; micro ES at one-tenth) | ~8–10× on initial margin | Embedded in the basis: roughly the risk-free rate less the dividend yield, ~2.5–3% a year | No — bracket required | No margin call while the bracket holds; daily settlement | Section 1256 | The cheapest way to add beta fast; Book A's rebalance instrument |
| **Deep-in-the-money long-dated call** (delta 0.85–0.90) | ~4–6× | The extrinsic value, typically 3–6% of spot for two years at ordinary volatility | **Yes — the premium** | None | 1256 on index options | Stock replacement with a defined worst case; convexity for free |
| **Call spread to a target** | Varies; highest delta per dollar at the target | The debit | Yes | None | 1256 on index | The exceptional-tier expression when the target is known |
| **Call backspread** (sell one, buy two further out) | Convex — small until it isn't | Near zero | Yes, with a valley | None | 1256 on index | Melt-up convexity; Book D's optionality edge |
| **Cash-secured short put** | 1× on the cash reserved | Receives premium | Bounded at zero | None | 1256 on index | Paid to wait at a level you want to own — Book A at a bottom |
| **Margin loan** | Up to 2× | The broker's rate — commonly several points above the risk-free rate for retail | No | **Yes** | Interest may be deductible against investment income | Rarely; every alternative above is cheaper |
| **Short box spread** (sell an SPX box) | Financing only | **Near the risk-free rate** — the mirror of BOXX | Fixed payoff at expiry | None if held | 1256 | Borrowing against Book A at the cheapest rate available to a retail account |
| **Leveraged ETF** (2×, 3× daily reset) | 2–3× | The variance tax — Figure L4 | Bounded at zero | None | Ordinary | **Days only.** Never a multi-month holding |

Three rows deserve a sentence each.

*Futures are the default for adding beta*, because their financing is the cheapest available and it is invisible — it lives in the basis between the futures and cash prices rather than in an interest charge. The micro contract makes them sizable for a book of this scale. The cost is that risk is undefined without a bracket, which the execution framework makes mandatory.

*The short box spread is the tool most retail traders do not know exists.* Selling a box — a call spread and a put spread at the same strikes — receives cash now and pays a fixed amount at expiry, which is a loan at whatever rate the box's price implies, and in liquid SPX options that rate sits near Treasury bills. It is the same instrument BOXX holds, from the other side. A trader who would otherwise borrow on margin at several points over the risk-free rate can borrow through a box at a fraction of that, with no margin call and Section 1256 treatment on the interest. It requires the account to be margined for the box's payoff and it belongs only against Book A with a declared purpose, but it is the cheapest leverage a retail account can obtain.

*Leveraged ETFs are the most expensive.* Their daily reset compounds path-dependently, and in a flat market they lose the variance tax — roughly (L² − L) × σ² ÷ 2 a year, which is twelve percent at twenty-percent volatility for a 3× fund and more than half the capital at crypto volatility. They exist for a single-day view. Held for a quarter they are a bet on a trend strong enough to overcome the tax, which is a different and worse bet than the one the holder thinks he is making.

*[Figure L4 — rendered in the HTML edition]*

### 16.3 After the fall: the volatility problem

The moment the operator most wants leverage is after a twenty- or thirty-percent decline, and the instinct — "buy a far-dated call and let the recovery pay" — is precisely the instrument the moment prices worst.

*[Figure L1 — rendered in the HTML edition]*

Implied volatility is highest at the trough. At the 2008 and 2020 lows it exceeded eighty; at the 2011, 2018 and 2022 lows it sat in the mid-thirties to high forties. A two-year at-the-money call that costs about 11% of spot at sixteen-percent volatility costs about 24% at forty. **The instinct buys volatility at its peak in order to buy direction**, and pays for the volatility twice — once in the premium and again when it collapses during the recovery, which it does within months of every trough on record.

*[Figure L2 — rendered in the HTML edition]*

The figure shows the way out. The at-the-money call's price is dominated by volatility; the deep-in-the-money call's price is dominated by intrinsic value and its *extrinsic* — the part volatility affects — is a fraction. At forty-percent volatility a two-year call struck twenty points in the money costs about 27 on a spot of 70, of which 20 is intrinsic and only about 7 is the volatility purchase. Its delta is near 0.85. It is stock with a floor, bought at the trough, at a volatility cost the trough barely touches.

### 16.4 Five ways to add at the trough, priced

The setup: the index has fallen 30% to 70; implied volatility is 40%; the horizon is two years; the Top & Bottom framework has fired a bottom signal, which the Doctrine's Section 6.3 says permits Book A to move to the top of its band immediately, even in a Crisis regime. The operator has $100 to commit per unit and wants the most recovery for it.

*[Figure L3 — rendered in the HTML edition]*

| Instrument at the trough | What $100 buys | At the prior peak (100) two years out | At 120 | If it falls to 50 |
|---|---|---|---|---|
| **The index at 70** | 1.43 units | +43% | +71% | −29% |
| **2-year ATM call (cost 16.6 per unit)** | 6.0 calls | +81% | +201% | **−100%** |
| **2-year 50-strike call (cost 26.6; 20 intrinsic)** | 3.76 calls | +88% | +163% | −100% (but only on the extrinsic if exited earlier) |
| **70/95 call spread (cost 7.4)** | 13.5 spreads | **+238%** | +238% (capped) | −100% |
| **Cash-secured 60 put (credit 8.2 on 60 reserved)** | Paid 13.7% to wait | +13.7% | +13.7% | Own the index at 51.8 net |

The readings, and they are the chapter's core.

**The call spread is the highest-leverage recovery instrument by far** — because at forty-percent volatility the 95 call you sell is expensive, and selling it funds most of the 70 call you buy. A trader who believes the index recovers its prior peak in two years — the *Base Rates* median for a −30% bear is about two years to recovery — is paid more than three times for that belief with the spread, and half that with the outright call, and the spread's cap sits at the level the belief itself named.

**The deep-in-the-money call is the stock-replacement instrument** — nearly the index's participation, a defined worst case, and the smallest volatility purchase of any option on the table. It is the right instrument when the thesis is "recovery, timing unknown" rather than "recovery to a level by a date."

**The at-the-money call is the worst instrument on the table**, and it is the one the instinct reaches for. It pays the full volatility premium, needs a 24% recovery just to break even, and its 6× leverage is mostly a bet on the crush not happening.

**The cash-secured put is the Doctrine's Book A tool**, and it belongs here for a reason the others do not cover: it is paid to add *more* exposure at *lower* prices, at a premium that the panic has made rich — 13.7% for two years to agree to buy at 60 when the index is 70. For a book whose Doctrine requires it to be at the top of its band after a bottom signal and whose operator's history says he will hesitate, being paid to wait is the structure that makes the discipline profitable rather than merely correct.

### 16.5 The bottom-signal playbook

Sequenced, because the instruments in 16.4 are not alternatives; they are a schedule.

**Day 0 — the bottom signal fires.** Move Book A to the top of its band with **futures or the index**, not options. The move is mandatory under the Doctrine, the financing is cheapest, and no volatility is purchased. Bracket the futures per the execution framework.

**Days 0–5 — sell the panic.** With the band filled, sell **cash-secured puts** ten to fifteen percent below spot for the next tranche of exposure, at the trough's volatility. Either the market falls further and the book buys more at a level it wanted, having been paid to wait, or it does not and the premium is kept. This is the only short-option structure the Doctrine permits without a wing, and the trough is when it is most worth permitting.

**Weeks 4–12 — convert as volatility normalizes.** Implied volatility falls faster than price recovers at every trough on record. When it has fallen through the mid-twenties, convert a portion of the futures exposure into **deep-in-the-money two-year calls** — the same participation, now with a defined worst case, at a volatility cost that is no longer punitive. The book has gone from undefined risk (futures) to defined risk (calls) at the moment the conversion became cheap.

**When conviction on the level firms — the call spread.** If the recovery target is a level rather than a hope — the prior peak, the two-hundred-day average, the level the Top & Bottom composite names — the **call spread to that level** is the exceptional-tier instrument, and the exceptional tier is available precisely when the three dials align, which after a confirmed bottom they do.

**Throughout — the backspread for the melt-up.** A small **call backspread** further out, near-zero cost, for the outcome in which the recovery overshoots. Book D's convexity, sized at Book D's cap.

**And the principal-protected position's rebalance**, since the chapter's question began there. A synthetic PPN entering a 30% decline has a bond leg worth roughly its full principal and a call leg worth little. The rebalance is a **re-strike**: sell the old, now far-out-of-the-money call for whatever it retains; sell enough of the bond leg to buy new calls struck at the trough — deep-in-the-money if the floor must be kept intact, at-the-money if the operator will accept a floor below par for more participation. The old call's loss is realized; the new call's delta is several times larger. **The PPN is the one structure that arrives at a trough with its powder dry by construction**, which is the best argument for it in Chapter 13 that Chapter 13 did not make.

### 16.6 High-confidence directional bets — the exceptional tier's expression

When the alignment test is met and the Doctrine permits twice standard risk, three instruments express it and one does not.

**The call spread to the target** — the cheapest delta per dollar at the level the thesis names, defined risk equal to the tier's dollar figure, and the cap exactly where the thesis stops. Default.

**The deep-in-the-money long-dated call** — when the thesis has a direction and a horizon but no level. Stock replacement with a floor; the tier's dollars buy the extrinsic plus the intrinsic at risk.

**The call backspread** — when the thesis is not "up" but "up a lot": a squeeze regime, a melt-up. Near-zero cost, convex, and the valley is the price.

**Not the outright out-of-the-money call**, unless the Chapter 4 test says volatility is cheap against the name's own history. An out-of-the-money call is the retail expression of confidence, and it is the one that pays the most for the least delta.

Two rules from the Doctrine apply with extra force at this tier. **No more than two exceptional-tier packets a month, none in a Transition state or on a flagged day.** And **adds go on confirmation at higher prices, never on weakness** — leverage on a winner is Livermore's rule; leverage on a loser is the rule the drawdown switches exist to punish.

### 16.7 The rules that govern all of it

1. **Leverage is a tier, and the tier is earned by alignment, not by conviction.** Conviction is what the register grades; alignment is what the dials report.
2. **Prefer the instrument with the smallest volatility purchase for a given delta** — futures, then deep-in-the-money calls, then spreads, then outright options, in that order, and reverse the order only when volatility is demonstrably cheap.
3. **After a decline, buy direction and sell volatility** — spreads and deep-in-the-money calls, not at-the-money calls; cash-secured puts to be paid for the next tranche.
4. **Convert undefined to defined risk when volatility normalizes**, not before; the conversion is cheap then and ruinous at the trough.
5. **Finance through boxes, never margin loans**, and only against Book A with a declared purpose and a recorded rate.
6. **Leveraged ETFs are for days.** A quarter in one is a variance tax with a ticker.
7. **The caps and the ladder apply to leveraged P&L without adjustment.** A doubled position that trips the daily switch has tripped it; the tier does not buy an exemption.
8. **Every leveraged packet records its form, its financing cost, and its effective notional beside its risk**, so the ledger can eventually say which forms of leverage this operator uses well — the register's `expression_family` gains `leverage_form` as a sub-field.

---

# Part V — Choosing, and Wiring

## Chapter 17 — The expression table

The Doctrine's regime dials choose the row; the thesis's shape chooses the column.

| Thesis shape | Calm / positive gamma | Rising vol | Stressed / negative gamma |
|---|---|---|---|
| Direction, with a target | Debit vertical to the target | Debit vertical, narrower | Debit vertical, half size, defined risk only |
| Direction, no target | Long option (cheap vol) or the underlying | Vertical — do not buy expensive premium outright | Underlying at reduced size, or pass |
| Mean reversion toward a level | Vertical toward the level; short premium beyond it | Vertical only | **Pass** — the trust matrix reads mean reversion Off |
| Big move, unknown direction | Long straddle only if implied is cheap | Iron butterfly, funded | Already priced; usually pass |
| Event with a known date | Calendar or post-event entry | Vertical after the crush | Defined risk, small |
| Allocation with a floor | Bills + LEAPS, or partial buffer | Same, with a wider floor | Same — this is the Book A convexity form |
| Income against cash you will deploy | Cash-secured put at a level you want | Reduce size | **Pass** |

Three standing rules that override the table. **No naked short calls, ever.** **No short options without a defined wing.** **Nothing that cannot be exited in one session at ordinary size.**

## Chapter 18 — Wiring into the register

The expression check already flags mismatches between edge type and instrument shape. This paper adds four rules it should enforce:

1. **A packet naming an option instrument must state tenor, strike, and the four vertical numbers** where applicable — debit, width, breakeven, and risk–reward. A packet that names "calls" is incomplete.
2. **A long single option into a scheduled event fires a warning**, with the implied-move-versus-history comparison attached. Chapter 10's rule, mechanized.
3. **A structure with an undefined tail is refused, not warned** — the naked-short-call and bare-short-stock cases, consistent with the Doctrine's meme rules.
4. **Engineered structures carry their components.** A synthetic protected position enters the register as one decision with its legs enumerated and its horizon date recorded, because the floor exists only at that date and a mid-period mark below it is not an invalidation.

And one registry addition: **`expression_family`** — outright, vertical, time spread, volatility structure, engineered — so the ledger can eventually answer the question this paper cannot: *which expressions actually made money, cut by regime.* The Doctrine's Rule 11 asserts that expression matters; only the register can prove it.

## Chapter 19 — What would change this paper

*A material change in the rate environment.* Every arithmetic result in Part IV is a function of the risk-free rate. At 1%, the self-funding tenor moves out beyond a decade and engineered structures stop working; at 6%, twelve-month structures fund themselves and the case for them strengthens sharply.

*A settled answer on box-spread-fund taxation*, in either direction.

*The register's first fifty option expressions*, cut by family and regime — the first evidence on whether the verticals-by-default rule is right for this operator, and the first measurement of what the spread tax actually costs at Book C's size.

*Sub-penny index option spreads or a change in same-day expiry structure*, either of which would change the friction arithmetic that drives the index-only restriction.

---

## Appendix A — Cheat sheet

**Rules of thumb.** At-the-money option ≈ 0.4 × σ × √T of spot. Straddle ≈ 0.8 × σ × √T. Delta of an at-the-money option ≈ 0.5; delta approximates the probability of finishing in the money. Half of time value is gone at a quarter of the life remaining. A 30-delta option finishes in the money about 30% of the time.

**Vertical arithmetic.** Max loss = debit. Max profit = width − debit. Breakeven = long strike + debit. Target payoff ratio ≥ 2:1, so pay ≤ ⅓ of the width.

**Funding arithmetic.** Option package cost ∝ σ√T; interest funding ∝ rT. Self-funding tenor ≈ (0.8σ ÷ r)² for a straddle — at σ = 16% and r = 4%, about ten years; for a ±10% iron butterfly, roughly three years.

**Structure selection in one line.** Know the direction and the target → vertical. Know the date, not the direction → funded reverse iron butterfly. Know neither but need to be invested → bills plus long-dated calls. Know all three and volatility is cheap → the outright option, and only then.

## Appendix B — The engineered structures, side by side

| Structure | Floor | Cap | Funded by | Tail risk | Best tenor |
|---|---|---|---|---|---|
| Buffered fund | Buffer (e.g. −10%) | Yes | Dividends + cap | Below buffer, 1:1 | 12 months (the issue period) |
| Synthetic PPN (bills + LEAPS) | 0% at maturity | None; participation < 100% | Dividends + participation | None | 3–7 years |
| Dual-directional note | None below barrier | Yes, both ways | Dividends + cap + **your tail** | **Discontinuous at the barrier** | 12–36 months |
| Bills + reverse iron butterfly | ≈ the unfunded portion | Yes, both ways | Dividends + cap + interest | **None** | 12 months+ |
| Collar (long index, long put, short call) | Put strike | Call strike | Dividends retained; cap | Below put strike, protected | Any |
