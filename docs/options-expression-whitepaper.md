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

Part I is the grammar — the four shapes everything is built from, and what you are actually paying for. Part II is the structures, one figure each. Part III is the three costs that determine whether a correct view makes money. Part IV is the engineered payoffs: buffered funds, synthetic principal protection built from a cash-equivalent fund and long-dated calls, and the dual-directional structures that pay off in both directions — including how to build each from listed options, what each really costs, and how each compares to the honest baseline of simply owning the index. Part V is the decision procedure and its wiring into the register.

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

## Chapter 8 — Straddles, strangles, butterflies, condors

The volatility structures, in one paragraph each.

**Long straddle** (buy the call and put at the same strike): pays for movement in either direction, costs roughly 0.8 × implied volatility × √T of notional. At 16% implied volatility, a one-year straddle costs about 12.8% and a three-month about 6.4% — the numbers that govern Part IV's arithmetic. It is the purest long-volatility expression and the most expensive.

**Long strangle** (out-of-the-money call and put): cheaper, needs a bigger move, and is the structure most often bought before events by people who have not checked what implied volatility already prices.

**Short butterfly / short condor**: the same shapes sold, betting on stillness, with the risk profile inverted.

**Long iron butterfly** (buy the at-the-money call and put, sell an out-of-the-money call and put): the shape that matters most for Part IV. It profits from a move in *either* direction, and its profit is capped at the wings you sold. Figure 9 draws it. **This is the listed-options version of the dual-directional structured note**, and the rest of this paper's engineered section turns on that equivalence.

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

**Long the at-the-money call and put, short the out-of-the-money call and put — a long iron butterfly.** It profits from a move in either direction and caps at the wings you sold. There is no barrier, no discontinuity, no issuer credit risk, and no tail sale: your worst case is the debit you paid.

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

**The construction.** Put most of the capital in the cash-equivalent leg — bills, STRIPS, or BOXX — and spend the interest on the iron butterfly.

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

# Part V — Choosing, and Wiring

## Chapter 15 — The expression table

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

## Chapter 16 — Wiring into the register

The expression check already flags mismatches between edge type and instrument shape. This paper adds four rules it should enforce:

1. **A packet naming an option instrument must state tenor, strike, and the four vertical numbers** where applicable — debit, width, breakeven, and risk–reward. A packet that names "calls" is incomplete.
2. **A long single option into a scheduled event fires a warning**, with the implied-move-versus-history comparison attached. Chapter 10's rule, mechanized.
3. **A structure with an undefined tail is refused, not warned** — the naked-short-call and bare-short-stock cases, consistent with the Doctrine's meme rules.
4. **Engineered structures carry their components.** A synthetic protected position enters the register as one decision with its legs enumerated and its horizon date recorded, because the floor exists only at that date and a mid-period mark below it is not an invalidation.

And one registry addition: **`expression_family`** — outright, vertical, time spread, volatility structure, engineered — so the ledger can eventually answer the question this paper cannot: *which expressions actually made money, cut by regime.* The Doctrine's Rule 11 asserts that expression matters; only the register can prove it.

## Chapter 17 — What would change this paper

*A material change in the rate environment.* Every arithmetic result in Part IV is a function of the risk-free rate. At 1%, the self-funding tenor moves out beyond a decade and engineered structures stop working; at 6%, twelve-month structures fund themselves and the case for them strengthens sharply.

*A settled answer on box-spread-fund taxation*, in either direction.

*The register's first fifty option expressions*, cut by family and regime — the first evidence on whether the verticals-by-default rule is right for this operator, and the first measurement of what the spread tax actually costs at Book C's size.

*Sub-penny index option spreads or a change in same-day expiry structure*, either of which would change the friction arithmetic that drives the index-only restriction.

---

## Appendix A — Cheat sheet

**Rules of thumb.** At-the-money option ≈ 0.4 × σ × √T of spot. Straddle ≈ 0.8 × σ × √T. Delta of an at-the-money option ≈ 0.5; delta approximates the probability of finishing in the money. Half of time value is gone at a quarter of the life remaining. A 30-delta option finishes in the money about 30% of the time.

**Vertical arithmetic.** Max loss = debit. Max profit = width − debit. Breakeven = long strike + debit. Target payoff ratio ≥ 2:1, so pay ≤ ⅓ of the width.

**Funding arithmetic.** Option package cost ∝ σ√T; interest funding ∝ rT. Self-funding tenor ≈ (0.8σ ÷ r)² for a straddle — at σ = 16% and r = 4%, about ten years; for a ±10% iron butterfly, roughly three years.

**Structure selection in one line.** Know the direction and the target → vertical. Know the date, not the direction → funded butterfly. Know neither but need to be invested → bills plus long-dated calls. Know all three and volatility is cheap → the outright option, and only then.

## Appendix B — The engineered structures, side by side

| Structure | Floor | Cap | Funded by | Tail risk | Best tenor |
|---|---|---|---|---|---|
| Buffered fund | Buffer (e.g. −10%) | Yes | Dividends + cap | Below buffer, 1:1 | 12 months (the issue period) |
| Synthetic PPN (bills + LEAPS) | 0% at maturity | None; participation < 100% | Dividends + participation | None | 3–7 years |
| Dual-directional note | None below barrier | Yes, both ways | Dividends + cap + **your tail** | **Discontinuous at the barrier** | 12–36 months |
| Bills + iron butterfly | ≈ the unfunded portion | Yes, both ways | Dividends + cap + interest | **None** | 12 months+ |
| Collar (long index, long put, short call) | Put strike | Call strike | Dividends retained; cap | Below put strike, protected | Any |
