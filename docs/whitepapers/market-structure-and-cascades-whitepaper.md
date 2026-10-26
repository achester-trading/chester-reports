# Market Structure and Cascades

## How a Trade Becomes a Price, Who Stands in the Middle and Why They Step Away, and How Forced Flow Turns a Move into a Cascade

**Companion white paper — chester-reports library**
**Series placement:** Companion **XXX** — Markets shelf, reading-plan position 8 beside *Positioning & Flows* and *Technical Indicators*, after the options sequence — per the library guide, which is canonical for numerals; cross-references in this paper are by name
**Version:** 1.0 — Draft 1, 26 October 2026
**Last reviewed:** 26 October 2026 (seeded with the version date; no structural review has been held)
**Status:** Draft 1, for the operator's review. The body is timeless; every level, share and probability lives in Appendix B. The seven figures are placeholders, named with the store keys each will draw from, and are drawn in a later edition.

---

### Reader's note

The library has explained, paper by paper, how particular participants are obliged to trade: dealers hedging gamma, volatility-targeting funds cutting exposure, pensions matching liabilities, index funds buying at the close. What it has not done is put those obligations in one place and asked the question they share. When does a move that one set of participants must answer become larger than the willingness of everyone else to absorb it? That question is this paper's subject.

**Liquidity is not a stock that markets hold but a flow that intermediaries supply when it pays and withdraw when it does not.** A cascade is what happens when the flow that must trade exceeds the flow that is willing to. Margin calls, rebalancing, hedging and redemptions must trade; dealers, market makers and patient capital may. The size of a move is therefore set less by the news than by the ratio of forced flow to depth, and the claim this paper defends is that the ratio can be estimated before the move. The system's own attempt to estimate it has, so far, failed its ledger, and Part IV says so plainly. A paper that teaches "measurable before the move" owes its reader the measurement, including when the measurement does not work.

Part I is the plumbing: venues, intermediaries, ETFs, clearing and margin, depth. Part II treats cascades as one subject rather than a list of disasters. Part III teaches the mechanisms through cases, weighted to where the system's measures reach. Part IV is the fragility read as the system measures it, with each ledger's verdict as filed. Part V carries the closing chapters every markets paper carries.

**What this paper does not do.** It does not teach options mechanics; *The Dealer's Hand* does, once, in its Part I, and this paper cites it. It does not re-narrate an episode that *Tops and Bottoms* tells; it gives the mechanism and cites the episode. It does not tell the 2022 gilt crisis as a fiscal story, which belongs to *Debt Cycles*; it tells the collateral mechanics. And it does not restate the participant ecology of *Price, Time, and Edge*; it uses it.

**Prerequisites.** *Price, Time, and Edge*, for the participant classes, the forcing mechanisms and the horizon ladder; *The Dealer's Hand*, Part I, for how a dealer's options book becomes a hedging flow; *Volatility*, for volatility targeting and the variance risk premium's unwinds; *Rates & Liquidity*, for the Treasury market and repo; *Positioning & Flows*, for the calendar of mechanical holders. A reader who has those can read this paper straight through.

---

# Part I — How a Trade Becomes a Price

## Chapter 1 — Venues and auctions

A price is not discovered in one place. In a modern equity market it forms across a dozen lit exchanges, several dozen off-exchange venues, and the internal books of wholesalers who fill retail orders before they reach any exchange. Two mechanisms organise that sprawl: the continuous limit order book, which runs through the session, and the auction, which opens and closes it.

### 1.1 The continuous book

The continuous book is a queue of resting limit orders at each price, bids below and offers above. A marketable order consumes the queue on the other side until it is filled. Price moves when a queue empties. That is the whole mechanism, and its consequence is easy to miss: the price change a trade causes depends on how much sits in the queues it walks through, not on how large the trade is in the abstract. A thousand shares that meet a thin offer move the price more than a hundred thousand shares that meet a deep one.

The queues are mostly supplied by intermediaries, the subject of Chapter 2, and they are cancellable at no cost. A resting order is an option the market maker has written and can withdraw in microseconds. What a screen displays as depth is the depth the suppliers are willing to show at that instant. Depth that has been displayed is not depth that has been promised.

### 1.2 The auctions

The opening and closing auctions collect orders over a period and clear them at a single price that maximises the volume matched. Before the match, the exchange publishes the imbalance: how many more shares are to buy than to sell at the indicative price. That publication invites the other side to arrive. The auction is a call market grafted onto a continuous one, and it exists because some participants need a single, verifiable price rather than the best price.

**The close is the day's largest trade, and the reason is mandate rather than preference.** Index funds are measured against a closing price, so they trade at the close. Mutual funds strike their net asset value at the close, so their flows land there. Leveraged and inverse funds rebalance into it. Derivatives settle against it. Every participant whose benchmark, liability or contract names the closing price has an incentive to trade at that price and at no other. The closing auction has therefore grown as indexation has grown, *in US-listed equities since the mid-2000s; last verified October 2026*, and its share of the day's volume is large enough that a session's continuous trading is in a sense price discovery for the auction rather than the reverse. The shares are dated and live in Appendix B.

*Worked example (illustrative).* Into an index rebalance close, the published imbalance is 4 million shares to buy in a stock whose closing auction normally matches 6 million. The imbalance is two-thirds of the auction's usual size. Liquidity providers who sell into it must be paid to carry the position overnight, and the payment is the auction price's concession above the last continuous trade. If they demand 30 basis points for warehousing that much inventory, the close prints 30 basis points above where the stock traded at 15:59, and the price reverses partly the next morning as the inventory is distributed. The concession is the price of immediacy at a moment when everyone who must trade has chosen the same instant.

*Historical instance.* Index reconstitution days, when the largest index families rebalance together, produce the year's largest closing auctions and the clearest imbalance-driven concessions.

*On the day.* The imbalance publications in the final minutes of the session are the tell. A large, one-sided imbalance that grows rather than shrinks as the close approaches means the other side has not arrived at the indicative price.

### 1.3 Dark venues and internalisation

Off-exchange venues match orders without displaying them. Dark pools let institutions trade size without signalling. Wholesalers internalise retail orders against their own inventory, paying for the flow because uninformed orders are cheap to trade against. Both take volume away from the lit book, and both depend on it, because they price their matches against the displayed quote. A cascade therefore reaches the dark venues last and leaves them first. When the lit quote becomes unreliable, venues that reference it stop matching, and their flow is pushed back onto the book at exactly the moment the book is thinnest.

### 1.4 Non-US structure, in brief

The book trades US instruments, but three differences abroad change how a cascade travels.
- **Europe is fragmented by law.** The same share trades on its primary exchange, on multilateral trading facilities and through systematic internalisers. For most of the period the market has had no single consolidated tape, so "the price" is less a fact than a reconstruction.
- **Asia's sessions are interrupted.** Several major exchanges break for lunch. The sessions do not overlap with New York, so a shock that begins in the US afternoon is first priced in Tokyo, Seoul and Hong Kong through futures and through their own opening auctions.
- **Price limits differ.** Some Asian markets cap daily moves per stock. A capped market cannot clear, so selling pressure is pushed into the next session or into whatever related instrument is still open.

The common lesson is that when one venue cannot clear, the order flow it would have absorbed goes to whatever venue can. In a cascade, that is usually the futures market or the most liquid ETF. The US equity index future is the instrument the world sells when it cannot sell what it holds.

| Mechanism | What it does | What a cascade does to it |
|---|---|---|
| Continuous book | Clears marketable orders against resting quotes | The quotes are cancelled; depth vanishes before price moves |
| Opening and closing auctions | Clear at one price after publishing the imbalance | Mandated flow concentrates there; the concession widens |
| Dark venues and internalisers | Match against the lit quote without displaying | Stop matching when the quote is unreliable; flow returns to the book |
| Non-US venues | Fragmented, interrupted, price-limited | Pressure moves to futures and to whatever is open |

## Chapter 2 — Who supplies liquidity

*Price, Time, and Edge* lays out the participant ecology, and this chapter does not restate it. It asks one narrower question of each class that stands in the middle of a trade: what is it paid for, and what makes it stop?

### 2.1 Bank dealers

A bank dealer warehouses risk on its balance sheet: it buys a block it cannot immediately resell and holds it until it can. It is paid for immediacy and for risk-bearing, and its capacity is set by the capital its regulators make it hold against the inventory. A dealer stops when the balance sheet is full, when the risk limits on the desk bind, or when the capital charge on the position exceeds the spread it earns. None of those is a decision about the market. They are constraints, and they bind hardest when volatility rises, because value-at-risk limits shrink the inventory a desk may hold exactly when inventory is cheapest to buy.

### 2.2 Non-bank market makers

Electronic market makers quote continuously on both sides of thousands of instruments and hold inventory for seconds or minutes rather than days. They are paid the spread, and in some venues a rebate for posting liquidity. Their capacity is set by their models' confidence and by their own risk limits, not by regulatory capital. They stop when the variance of the next price exceeds what the spread pays for, when their data feeds disagree, or when their models detect that the flow is informed. Each of those conditions arrives suddenly. A non-bank market maker does not reduce its quoting gradually as risk rises; it widens, then pulls.

### 2.3 Automated liquidity

High-frequency firms that are not formal market makers supply much of the displayed depth and take much of it back. They trade against short-lived imbalances and among themselves. Their contribution is real in calm markets: narrower spreads, deeper top-of-book quotes. In stress it can reverse, because a strategy that supplies liquidity for a profit in a fraction of a second will consume it if consuming pays. Inventory passed between automated traders is the "hot potato" of the 2010 flash crash (Chapter 13). The volume rises, and the price falls anyway, because no participant is willing to hold.

### 2.4 Patient capital

Behind the intermediaries stand the participants who are the market's true risk absorbers: long-only funds with cash, pensions with rebalancing rules, corporate buyback desks, and value investors who buy what is cheap. They are not paid to supply liquidity. They supply it because price has moved past their own valuation. They are slow; their decisions are made over days. The gap between the intermediaries' withdrawal, which takes seconds, and patient capital's arrival, which takes days, is the window in which a cascade runs.

| Class | Paid for | Capacity set by | Stops when |
|---|---|---|---|
| Bank dealer | Immediacy and warehousing | Regulatory capital; risk limits | The balance sheet or the VaR limit binds |
| Non-bank market maker | The spread, rebates | Model confidence; own limits | Variance outruns the spread; feeds disagree; flow looks informed |
| Automated liquidity | Short-lived imbalances | Latency and risk budget | Consuming pays more than supplying |
| Patient capital | Nothing; it buys value | Its own cash and mandate | It is slow to start, not quick to stop |

## Chapter 3 — Exchange-traded funds

An exchange-traded fund is a share whose price is tied to a basket by arbitrage. The tie is enforced by authorised participants, dealers who may create new shares by delivering the basket to the fund, or redeem shares by taking the basket out. When the fund's price rises above the value of its holdings, an authorised participant buys the basket, creates shares and sells them; when it falls below, it buys shares, redeems them and sells the basket. The premium or discount to net asset value is the arbitrage's error term.

### 3.1 What the arbitrage needs

The arbitrage works when the basket can be traded at the price used to value it. For a large-capitalisation equity fund it can, and the premium is a rounding error. For a corporate bond fund it often cannot: many of the bonds do not trade on a given day, and the fund's net asset value is computed from evaluated prices, which are models of where the bonds would trade. The fund's own price is the only observed price. In calm markets the two agree. In stress they separate, and the separation is information rather than error.

### 3.2 What a fund does to its underlying

In calm markets an ETF adds liquidity to its underlying. Investors who would otherwise trade a hundred bonds trade one share, and the authorised participants net the flows and touch the bonds only when the imbalance is persistent. In stress the direction can reverse. A wave of selling in the fund produces redemptions, and redemptions deliver bonds to the authorised participant, who must sell them into a market that is not bidding. The fund has transmitted the selling from the most liquid instrument to the least. Whether it does depends on whether the authorised participants step in at all. They are not obliged to, and they will not when their own balance sheets are full (Chapter 2).

*Worked example (illustrative).* A bond fund holds bonds whose evaluated prices sum to a net asset value of 100. On a stressed day the bonds barely trade, but the fund's shares trade heavily at 95. The 5% discount says that sellers who need liquidity today will pay 5% for it; the evaluated prices say where the bonds would trade if anyone were trading them. An authorised participant could buy the shares at 95 and redeem them for bonds worth 100 on paper, but only if it can sell those bonds at something near 100, which the day's market does not offer. The arbitrage does not close, because its second leg is the trade nobody can do.

*Historical instance.* March 2020, when the largest corporate bond funds traded at discounts to net asset value that would be absurd in normal markets, and the discount closed only when the central bank announced it would buy both the bonds and the funds (Chapter 15).

*On the day.* The discount opened while the underlying bonds were barely quoted. A reader who treated the net asset value as the true price and the fund's price as the error had the roles reversed.

| Condition | ETF's premium or discount | What the fund does to its underlying |
|---|---|---|
| Liquid basket, calm market | Rounding error | Adds liquidity; flows net |
| Illiquid basket, calm market | Small, stable | Adds liquidity; authorised participants touch the basket rarely |
| Illiquid basket, stress | Large discount; the fund is the price | Transmits selling to the basket if authorised participants redeem; otherwise the discount stays open |

## Chapter 4 — Settlement, clearing, collateral and margin

Every cascade in Part III turns at some point on a payment that had to be made. The price of an asset is a fact about the market; the margin on a position is a fact about a contract, and it falls due whether or not the market is open, liquid or kind. This chapter is the plumbing through which a price move becomes a cash demand.

### 4.1 The clearing house

A central counterparty steps between the two sides of every cleared trade, becoming the buyer to every seller and the seller to every buyer. It replaces a web of bilateral exposures with one hub, and it makes the hub safe by charging for it. Members post initial margin against what a position could lose over the time it would take to close out after a default. Variation margin is settled at least daily, so that losses are paid as they accrue rather than at the end. Behind the margin sits a default waterfall: the defaulter's margin, then its contribution to a default fund, then the clearing house's own capital, then the surviving members' contributions.

The design concentrates risk in order to manage it. A clearing house is a shock absorber, but it absorbs shocks by charging the survivors, and the charge arrives at the worst time.

### 4.2 Why margin is procyclical

Initial margin is computed from a model of how far prices can move. When realised volatility rises, the model says prices can move further, and the margin rises. That is correct risk management for the clearing house and a cash demand on every member at once. A rise in volatility thus does two things. It produces losses, which are paid as variation margin, and it raises the margin on positions that have not lost anything. Both are paid in cash or eligible collateral, on the clearing house's schedule. The participant who cannot pay must sell, and the selling moves the price, which raises realised volatility, which raises the margin. Margin models carry anti-procyclicality tools (floors, buffers and long look-back windows) precisely because the loop is known. The tools damp it; they do not remove it.

*Worked example (illustrative).* A futures position of $100 million notional carries initial margin of 5%, so $5 million. Realised volatility doubles over three sessions, and the margin model steps the rate to 9%. The position has not changed, but its margin is now $9 million, a $4 million cash call due at the next settlement. If the same move has also cost the position $3 million in variation margin, the member must find $7 million in cash in three days. A member that holds its liquidity in the same asset it is hedging must sell that asset to pay.

*Historical instances.* January 2021, when a clearing deposit charged to a retail broker rose so sharply that the broker restricted its customers' buying (Chapter 16). September 2022, when the collateral calls on leveraged liability-matching funds forced the sale of the very bonds whose fall had triggered the calls (Chapter 17).

*On the day.* Margin events look like operational events: a broker restricting trading, a fund suspending redemptions, a central bank announcing a facility at an unusual hour. The price action follows the cash, not the other way round.

### 4.3 Collateral and haircuts

Outside cleared markets, leverage is financed by repo and securities lending: a borrower posts a security and receives cash, less a haircut. The haircut is margin by another name, and it is just as procyclical. Lenders raise haircuts when the collateral becomes volatile or hard to value. A borrower whose collateral is suddenly worth less, and whose haircut has risen, receives less cash against the same securities. The difference must be found or the position cut. *Rates & Liquidity* carries the repo market's mechanics and its 2019 dysfunction; what this paper adds is that haircuts and initial margin are one mechanism wearing two contracts.

### 4.4 Settlement

Settlement is the delivery of the security against the cash. A shorter settlement cycle reduces the exposure a clearing house must margin between trade and delivery, which lowers margin in calm markets. It also compresses the time a participant has to find the cash or the security when something goes wrong. Each shortening of the cycle trades one risk for another: less counterparty exposure for less operational slack. The dates are in Appendix B.

### 4.5 Who must post, and when

The cascade question is not who has losses but who must post cash before they can choose not to. Four classes are forced at once:
- **Futures and options holders** post variation margin daily and initial margin on the clearing house's schedule.
- **Leveraged long holders of securities on margin** at a broker receive margin calls, and the broker sells if they do not answer.
- **Repo and swap counterparties** post collateral against marks, usually daily.
- **Funds** with redemptions due must pay in cash on their own settlement terms.

The first three are contractual and arrive within a day. The fourth arrives on the fund's terms, which is why daily-dealing funds holding illiquid assets are fragile in a way closed-end and long-lock vehicles are not.

| Contract | The margin | Procyclical because | Arrives |
|---|---|---|---|
| Cleared futures and options | Initial and variation | The model's volatility input rises | Daily; intraday in stress |
| Securities on margin | Maintenance margin | Losses reduce equity below the requirement | On the call; the broker sells |
| Repo, securities lending | The haircut | Lenders widen it on volatile collateral | On renewal, often overnight |
| Swaps (bilateral, cleared) | Collateral against marks | The mark moves | Daily |
| Fund shares | Redemptions in cash | Losses drive redemptions | On the fund's dealing terms |

## Chapter 5 — Depth and impact

Liquidity is talked about as one thing and measured as several. Volume is how much traded. Depth is how much could have traded without moving the price. Impact is how far the price moved per unit traded. The three diverge, and the divergence is where cascades hide.

### 5.1 Price impact per unit of flow

Kyle (1985) modelled a market maker who cannot tell informed orders from uninformed ones and protects itself by moving the price in proportion to net order flow. The constant of proportionality, Kyle's lambda, is the price impact of a unit of flow. It is high when the market maker believes much of the flow is informed and when little uninformed flow is there to hide it. Lambda is a property of the market's beliefs about flow, not of the flow itself, so it can jump without any change in the trading.

Amihud (2002) offered a measure that needs only daily data: the absolute return divided by the dollar volume. It reads how far price moved per dollar traded. It is crude, it mixes information with illiquidity, and it rises when volume falls for any reason, but it is computable for any instrument with a price and a volume. That is why the system uses it as its depth stand-in (Chapter 19), and why Chapter 20 is devoted to what it cannot see.

### 5.2 Why volume and depth diverge

In a cascade, volume rises and depth falls together. The rise in volume is the forced flow arriving and the intermediaries passing inventory among themselves; the fall in depth is the intermediaries withdrawing their resting orders. A market that is trading record volume can be at its least liquid, because none of that volume is anyone willing to hold. A reader who equates volume with liquidity will read a cascade's peak as its healthiest moment.

*Worked example (illustrative).* On a calm day an index fund trades $40 billion and moves 0.5%; its Amihud measure is 0.5% ÷ $40 billion, about 1.25 basis points of move per billion dollars. On a stressed day it trades $80 billion and moves 4%: about 5 basis points per billion. Volume doubled, and so did the willingness to trade. But the price impact per dollar quadrupled, which says the market was absorbing each dollar of selling at four times the cost. The second day's volume is evidence of distress, not of depth.

*Historical instance.* 6 May 2010, when depth in the index futures fell to a small fraction of its normal level within minutes while volume surged (Chapter 13).

*On the day.* The quoted size at the top of the book thinning while the volume tape accelerates.

### 5.3 Resilience

A third dimension is how fast depth returns after it is consumed. A resilient market refills its queues within seconds; a fragile one leaves them empty. Resilience is the hardest of the three to measure from daily data and the most important in a cascade, because a market that refills is one where the next forced order meets the same depth as the last.

### 5.4 The microstructure the book's execution actually uses

*This section moved here from the Systematic Book on 26 October 2026. It records the pieces of microstructure the book's execution layer consumes; the Systematic Book keeps the broker, Portfolio Truth, brackets and the session rule.*

**The closing auction is where the book's most important prices form.** The settled 16:10 capture is timed to it, and the pin log grades against it. The Doctrine's Book C setups are entered from the 07:00 list and exited by bracket, but their *reference* (the pin, the wall, the flip) is a closing-auction price. Change Order #3 adds the auction's own flow, NYSE-family imbalance ticks through the Gateway with a 15:50–16:00 sampler, as the other side of the picture. Dealer gamma says how the close *reacts* to a move; the imbalance says what *pushes* it. For execution, the practical rule is the Doctrine's: no Book C entry after 10:30 without the 10:00 report's confirmation, and no entry into the last ten minutes at all unless the packet is explicitly a closing-auction expression.

**Options spreads are a cost the packet must pay for.** Doctrine Rule 13 says no trade whose expected R is less than three times its round-trip cost in commissions, spread and slippage. *Illustratively,* for a single-name option with a $0.10 wide market, a one-lot round trip costs $0.20 of spread before commission. On a $2.00 contract that is 10% of the premium, a cost that makes a 1.5R expectation impossible. The expression check's forward work (Gate 1.5) is to read the live spread from the chain and refuse the packet's R arithmetic when the spread makes it unattainable. Until then, the operator applies the rule from the chain the report shows.

**The data is fifteen minutes stale at the time it matters most.** The book's chain source is delayed. At the 09:45 intraday refresh, where the day's zero-day structure is captured, fifteen minutes is the difference between a live quote and a memory. The real-time options entitlement exists for that window alone. The settled 16:10 capture does not need it; by then the quotes are, in the Systematic Book's phrase, corpses.

| Measure | What it reads | Rises in a cascade? | Measurable from daily data? |
|---|---|---|---|
| Volume | How much traded | Yes | Yes |
| Depth | How much could trade without moving price | No: it falls | No; top-of-book depth needs quote data |
| Impact (Kyle's lambda, Amihud) | Price move per unit traded | Yes | Amihud, yes; lambda needs signed flow |
| Resilience | How fast depth refills | No: it slows | No |

---

# Part II — Cascades as One Subject

## Chapter 6 — Endogenous risk and feedback loops

Most risk models treat price moves as weather: something that happens to the participants, drawn from a distribution they did not make. Danielsson and Shin (2003) named the alternative *endogenous risk*: the risk that arises because participants respond to prices, and their responses move prices. A move that changes the participants' constraints produces the next move. The distribution is not given. The market makes it.

### 6.1 The loop

The loop has four steps. A price move changes some participants' constraints: their margin, their value-at-risk, their volatility target, their fund's redemptions, their dealer's hedge ratio. The changed constraint obliges them to trade in the direction of the move. The trade moves the price further. The further move tightens the constraint again. Whether the loop dies or runs depends on two things: how much of the market's capital sits under constraints of the same shape, and how deep the market is relative to the flow the constraints release.

**Figure 7 — The cascade as a loop.** *Placeholder, drawn in a later edition: a conceptual diagram with no series. The price move tightens constraints, forced flow meets depth, the move extends, and the loop either damps or runs.*

The loop explains why the same news produces small moves in some markets and enormous ones in others. The news is the first step. Everything after it is the market's own structure, and the structure can be read beforehand: who is under which constraint, at what size, against what depth.

### 6.2 Homogeneity is the amplifier

A market of participants with different constraints damps shocks. A seller forced by margin meets a buyer whose rebalancing rule says buy, and the price barely moves. A market in which most capital sits under the same constraint amplifies them, because every participant receives the same instruction at the same time. Risk management that is prudent for each firm becomes destabilising for all of them together. The fallacy of composition is the core of endogenous risk. Each firm's value-at-risk limit is sensible, and their sum is a selling programme.

### 6.3 Why this is measurable before the move

If the loop's strength depends on like constraints and on depth, both can in principle be estimated in advance, from positioning, margin debt, the leveraged and volatility-targeting products, dealer gamma and a depth measure. Part IV reports how the system's test of that has gone.

| Step | What happens | What sets its strength |
|---|---|---|
| A move | Prices change on news, or on nothing | The news |
| Constraints tighten | Margin, VaR, vol targets, redemptions, hedge ratios | The share of capital under like constraints |
| Forced flow | Participants trade with the move | The size of the constrained capital |
| The next move | Forced flow meets depth | Depth, and how fast it refills |

## Chapter 7 — Forced flows

*Price, Time, and Edge* lists the forcing mechanisms and argues the asymmetry that matters most here: forced buying is gradual and stabilising, while forced selling is abrupt and destabilising, because the triggers for selling are functions of price. This chapter takes the five forced flows that matter most to cascades and states, for each, what triggers it, how large it can be, and when it arrives.

### 7.1 Margin

Margin is the forced flow of Chapter 4: a participant whose losses or whose margin rate rise must post cash or cut the position. It arrives within a day and it is contractual. Its size is a function of leverage, which is why margin debt and futures positioning are the first places to look. Margin flows are the mechanism most likely to cross asset classes, because a participant that must raise cash sells what it can sell, not what fell.

### 7.2 Volatility targeting

A fund that targets a constant volatility holds exposure inversely proportional to realised volatility. When volatility doubles, the fund halves its exposure. *Volatility* carries the strategy, its scale and its unwinds, and this paper does not repeat them. What matters here is the shape of the flow: it lags the move, because realised volatility is measured over a trailing window, and it continues for days after the shock. A vol-targeting fund sells on the second, third and fourth days of a sell-off, after the first day's move has entered its window.

*Worked example (illustrative).* A fund targets 10% annualised volatility and holds $10 billion of equity exposure when realised volatility is 10%. A shock lifts the trailing 20-day realised volatility to 20% over a week. The fund's exposure target falls to $5 billion, and it sells $5 billion over the days the window takes to absorb the shock. The selling is predictable in direction and roughly in size, and it does not wait for the price to recover.

### 7.3 Leveraged and inverse products' rebalancing

A fund that promises a multiple L of the daily return must rebalance every day to keep its leverage constant. The rebalance is, to first order, AUM × L × (L − 1) × the day's return (Cheng and Madhavan, 2009). For a leveraged long fund (L = 2 or 3) the term is positive on an up day and negative on a down day: it buys strength and sells weakness. For an inverse fund (L = −1, −2, −3), L × (L − 1) is also positive, so it too buys on up days and sells on down days. Every daily-reset product, long or inverse, trades with the day's move, and it trades at the close.

*Worked example (illustrative).* A 3× long fund with $10 billion of assets on a −4% day must sell 10 × 3 × 2 × 4% = $2.4 billion at the close. A −2× inverse fund with $3 billion on the same day: 3 × (−2) × (−3) × (−4%) = −$0.72 billion, also a sale. The complex's combined rebalance is one-sided and concentrated in the closing auction, which is why it is the flow arm of the system's fragility flag (Chapter 19).

### 7.4 Dealer gamma

When dealers are net short options, their delta hedging trades with the move: they sell as prices fall and buy as they rise. When they are net long, the hedging trades against the move and damps it. *The Dealer's Hand* teaches the mechanics, in its Part I, once for the library, and this paper does not teach them again. Its contribution here is placement. Short dealer gamma is a forced flow of the same shape as margin and volatility targeting: it trades with the move, mechanically, at a size set by positioning the dealers did not choose. Zero-day options concentrate that flow inside the session. Their gamma is largest near expiry and at the money, so their hedging can amplify an intraday move and then vanish at the close. *The Dealer's Hand* and *Volatility* carry the zero-day market at depth; a fourth treatment here would be the duplication the library's audit warned against.

**Figure 4 — Dealer gamma and the session's range.** *Placeholder, drawn in a later edition: the stored net gamma exposure (`exposure.net_gex`) against SPY's daily range (`yfinance.mkt_spy`), from the captures' first stored session.*

### 7.5 Redemptions

A fund whose investors redeem must sell to pay them. Open-end funds holding illiquid assets are the fragile case: they promise daily liquidity on assets that do not offer it, so the first redeemers are paid at a price that does not yet reflect the cost of selling. That gives every investor an incentive to redeem first, and the incentive is a run.

| Forced flow | Trigger | Direction | When it arrives | Size set by |
|---|---|---|---|---|
| Margin | Losses; a higher margin rate | Sells what it can | Within a day | Leverage |
| Volatility targeting | Realised volatility rising | With the move, lagged | Days two to five | Assets under the strategy |
| Leveraged and inverse ETPs | The day's return | With the move | The close | AUM × L × (L − 1) |
| Short dealer gamma | Price moving through strikes | With the move | Intraday | Dealers' option positioning |
| Redemptions | Losses; a run incentive | Sells the fund's assets | On the dealing terms | Fund size; asset illiquidity |

## Chapter 8 — Liquidity spirals

Brunnermeier and Pedersen (2009) gave the loop between funding and markets its standard form. *Funding liquidity* is a trader's ability to finance its positions: margin, haircuts, credit lines. *Market liquidity* is the ease of trading an asset. Each depends on the other. When market liquidity falls, prices become more volatile, lenders raise margins, and funding liquidity falls. When funding liquidity falls, traders must sell, and their selling reduces market liquidity. The two reinforce each other, and the result is a spiral.

### 8.1 The two spirals

The model has two spirals running together:
- **The loss spiral.** A leveraged trader's losses reduce its capital, and at constant leverage a smaller capital supports a smaller position, so it sells.
- **The margin spiral.** Volatility raises margins, which forces de-leveraging even without losses.

Each sale depresses the price and raises volatility, feeding both spirals at once. The model's sharpest result is that liquidity can be fragile: a small shock can switch a market from a high-liquidity equilibrium to a low one, because the spiral, once started, does not need the original shock to continue.

### 8.2 What breaks the spiral

The spiral stops when someone with unencumbered capital buys: patient capital at a price far enough below value, or a central bank willing to lend against the collateral at a fixed haircut. That is why the end of so many cascades in Part III is an announcement rather than a trade. A lender of last resort breaks the margin spiral by refusing to let haircuts rise. A buyer of last resort breaks the loss spiral by putting a floor under the price.

*Worked example (illustrative).* A relative-value fund runs $10 billion of positions on $500 million of capital, 20× leverage, financed at a 5% haircut. The positions fall 1%, a $100 million loss, so capital falls to $400 million. At the same 20× it can now carry $8 billion, so it must sell $2 billion. Meanwhile lenders raise the haircut to 8% because the positions have become volatile, and at 8% the $400 million supports only $5 billion. The fund must sell half its book into a market where everyone running the same trade is selling too, and its selling widens the next lender's haircut.

*Historical instance.* 1998, and the dealers whose own books held the same trades as the fund they were financing (Chapter 12).

*On the day.* The trades that should converge diverge further, in instruments whose fundamentals have not changed. The divergence is the cost of the forced sale, not news about the instruments.

| Spiral | Mechanism | What stops it |
|---|---|---|
| Loss | Losses cut capital; leverage held constant forces sales | A buyer with unencumbered capital |
| Margin | Volatility raises margins and haircuts | A lender at a fixed haircut |
| Both together | Each sale feeds both | Usually an announcement by an official lender or buyer |

## Chapter 9 — Correlation breakdown and path dependence

### 9.1 Why diversification fails exactly when it is needed

Diversification works through low correlation, and correlations measured in calm markets are low because the assets are being priced on their own news. In a cascade the marginal seller is not pricing news; it is raising cash, and it sells whatever can be sold. The assets become correlated because they share a seller, not because their fundamentals moved together. Longin and Solnik (2001) found that equity-market correlations rise in down markets more than a normal model predicts. *The finding is measured on developed equity markets from the 1960s to the late 1990s; last verified October 2026.* The mechanism is the shared forced seller of Chapter 7.

The stock–bond correlation is the case that matters most to a portfolio that holds both, and its sign is a property of the regime rather than a constant. When inflation is the dominant risk, stocks and bonds fall together, because both are being repriced by the same rise in rates. When growth is the dominant risk, bonds rally as stocks fall. A 60/40 portfolio is diversified in the second regime and concentrated in the first. *Debt Cycles* carries the environments in which each sign holds; the cascade mechanism adds only that a forced seller of everything can briefly make the correlation positive in any regime.

**Figure 6 — The stock–bond correlation's sign through regimes.** *Placeholder, drawn in a later edition: the 60-session correlation of SPY and TLT returns (`calc.corr_spy_tlt_60d`), its sign shaded.*

*Worked example (illustrative).* A 60/40 portfolio in a regime where the stock–bond correlation is −0.3 has a volatility well below the equity sleeve's. If the correlation flips to +0.5 while equity falls 20% and bonds fall 10%, the portfolio falls 16% against the equity sleeve's 20%: diversification saved four points, not the ten a negative correlation had seemed to promise. The joint drawdown is not a tail of the old distribution. It is the normal behaviour of the new regime.

*Historical instance.* 2022, when stocks and bonds fell together through most of the year.

*On the day.* The days on which the hedge sleeve fell with the risk sleeve; there were many, and none of them looked like a cascade.

### 9.2 Path dependence

The order in which moves arrive matters because constraints are evaluated along the path, not at its end. A position that falls 20% and recovers ends where it began, but if a margin call, a stop or a volatility target was triggered on the way down, the participant is no longer holding it when it recovers. Two paths with the same end point can produce completely different forced flows. That is why a cascade is often followed by a recovery that the forced sellers do not participate in, and why the participants who were not forced are the ones who are paid.

| Effect | Mechanism | Consequence |
|---|---|---|
| Correlation rises in a cascade | A shared forced seller sells everything | Diversification fails when needed |
| The stock–bond sign is regime-dependent | Inflation risk versus growth risk dominating | A 60/40 is diversified in one regime and concentrated in the other |
| Path dependence | Constraints evaluated along the path | Same end point, different forced flows; the forced miss the recovery |

## Chapter 10 — Short squeezes

A short squeeze is the cascade mechanism run upward. Short sellers who have borrowed shares must buy them back to close. When the price rises, their losses and their margin rise, and some are forced to buy. Their buying lifts the price, which forces the next. The squeeze is a cascade with the forced flow on the bid.

### 10.1 What makes a short crowded

Three things make a short position fragile:
- **short interest large against the float**, so the shorts' buying is large against what is available to buy;
- **borrow that is expensive or scarce**, so holding the short costs money every day;
- **the lender's right to recall the shares**, which forces a cover regardless of price.

A position can be crowded by any one of the three. All three together make it a forced buyer waiting for a trigger.

### 10.2 The forced buyer and the options channel

In the modern squeeze, a second forced buyer often matters more than the shorts: the dealer who has sold call options. When buyers of out-of-the-money calls push the dealers short gamma, the dealers' hedging buys the stock as it rises (Chapter 7). *The Dealer's Hand* carries that mechanism, and this paper cites it.

### 10.3 What stops a squeeze

A squeeze stops when supply arrives: a secondary offering, lenders returning shares, the shorts exhausted, or a constraint on the buyers. The last is the case this library has most reason to study, because in 2021 it was a clearing deposit rather than a price that stopped the buying (Chapter 16).

*Worked example (illustrative).* A stock has 50 million shares of float, of which 60 million are reported short; lent shares have been re-lent, so short interest can exceed the float. Borrow costs 50% a year. A 30% rise in the stock lifts each short's loss and margin. If a third of the shorts must cover, 20 million shares must be bought in a stock that trades 10 million a day. The buying is two days' volume, all on the bid, and the shorts know that every other short knows it.

*Historical instance.* January 2021.

*On the day.* The borrow rate spiking, recalls, trading halts on volatility, and the brokers' restrictions.

**Figure 3 — Leveraged funds' net in ES against the squeeze cases.** *Placeholder, drawn in a later edition: CFTC Traders in Financial Futures, leveraged funds' net in the E-mini S&P 500 as a share of open interest (`cftc.tff_lev_money_net_oi`), with the squeeze cases marked.*

| Ingredient | What it does | The tell |
|---|---|---|
| Short interest against float | Makes the cover large against supply | Short interest, days to cover |
| Expensive or scarce borrow | Makes the short costly to hold | The borrow rate, utilisation |
| Recall | Forces a cover regardless of price | Recall notices; fails to deliver |
| Short dealer gamma from call buying | Adds a second forced buyer | Call volume, dealer positioning |
| A constraint on the buyers | Stops the squeeze | Broker restrictions; clearing deposits |

---

# Part III — The Cases

The cases are weighted to where the system's measures reach. February 2018 and March 2020 are told in full, 2021 and 2022 at medium length. 1987, 1998 and 2010 predate the store, so they are mechanism chapters cited to their histories. August 2024 and April 2025 are short instances that the air-pocket ledger scores (Chapter 19). Each chapter gives the mechanism; *Tops and Bottoms* tells the episodes. The cases' figures are in Appendix B, dated.

**Figure 5 — The volatility index through the seven cases.** *Placeholder, drawn in a later edition: the VIX's daily close (`fred.vix`) from its first stored observation, with the seven cases and the two short instances marked.*

## Chapter 11 — 1987: portfolio insurance as a forced seller

*Tops and Bottoms* tells October 1987 as a turning point, and *Debt Cycles* places it among the environments. This chapter takes only the mechanism.

Portfolio insurance was a dynamic hedging strategy: it replicated a put option on an equity portfolio by selling index futures as prices fell and buying them back as prices rose. It was a short-gamma position held by the insured portfolios themselves, and it gave a large pool of capital the same rule: sell more as the market falls. The strategy's designers assumed that the market could absorb the selling continuously. Grossman (1988) argued the deeper flaw: because the insurance was synthetic rather than a traded option, nobody could see how much of it there was, so the market could not price the selling it would release.

In the week before the crash the market fell, and the insurers fell behind their hedge ratios. On the Monday they sold futures in size, and the futures traded at a deep discount to the cash index. Index arbitrageurs, who would normally buy futures and sell stocks to close the gap, sold stocks into a specialist system that could not process the orders. The order-routing system backed up, quotes became stale, and the arbitrage link between futures and stocks broke. Each market's price was then uninformative about the other's, which made every participant less willing to supply liquidity.

The lessons are the paper's in miniature. A strategy that sells into weakness is a forced flow (Chapter 7). Synthetic positions whose size is unknown cannot be priced (Chapter 6). And the link between a derivative and its underlying is only as strong as the venue that carries the arbitrage (Chapter 1). The Brady Commission's report (1988) is the official history; the circuit breakers it recommended are the structure the market still uses.

| Element | In 1987 |
|---|---|
| Forced flow | Portfolio insurance's futures selling, a synthetic short gamma |
| What failed | The futures–cash arbitrage, through an overloaded venue |
| What it taught | Synthetic positions of unknown size cannot be priced |
| What stayed | Circuit breakers; coordinated halts across venues |

## Chapter 12 — 1998: leverage, crowded relative value and the dealers' own books

Long-Term Capital Management ran relative-value trades: long the cheaper of two closely related instruments and short the dearer, betting the spread would converge. The trades were individually small in expected return and safe in normal markets, so the fund levered them heavily. Lowenstein (2000) and the President's Working Group report (1999) are the histories.

The mechanism was the liquidity spiral of Chapter 8, with an amplifier that made it systemic: the fund's counterparties ran the same trades on their own books. When Russia's default in August 1998 triggered a flight to the most liquid instruments, spreads that should have converged widened. Every holder of the convergence trade lost at once, and every lender raised haircuts at once. The fund needed to sell, and the only buyers of what it held were the dealers. But the dealers held the same positions and knew the fund was forced, so they had every reason to wait or to sell ahead of it.

The episode ended when the Federal Reserve Bank of New York convened the fund's creditors, who recapitalised it and unwound its book over time. No public money was lent. The intervention broke the spiral by removing the forced seller from the market, which is the general form of every resolution in Part III.

The lesson for this paper is about homogeneity. A trade that is safe at one fund's size is fragile at the industry's, because the exit is shared. The fund's leverage made it the first forced seller; the dealers' copies made the market unable to absorb the sale.

| Element | In 1998 |
|---|---|
| Forced flow | De-leveraging of crowded relative-value trades |
| Spiral | Loss and margin together; haircuts rising across lenders |
| Amplifier | The dealers held the same trades |
| Resolution | The creditors recapitalised the fund and unwound it slowly |

## Chapter 13 — 2010: the flash crash

On 6 May 2010 the US equity market fell several percent in minutes and recovered most of it within the hour. The joint CFTC–SEC report (2010) and Kirilenko, Kyle, Samadi and Tuzun (2017) are the histories.

The trigger was a large sell programme in the E-mini S&P 500 futures, executed by an algorithm that sized its orders to a fraction of recent volume without regard to price or time. As the futures fell, high-frequency traders bought the contracts and then sold them to each other, rapidly. Volume surged, and the algorithm, which read volume as liquidity, sold faster. That was Chapter 5's divergence made literal: record volume and vanishing depth at the same moment. Depth in the futures fell to a small fraction of its normal level. The futures exchange's automatic pause halted the contract for five seconds, and the pause let depth return.

In individual stocks the collapse was worse, because market makers withdrew entirely and the only orders left were stub quotes, placeholders set far from the market to meet a quoting obligation. Market orders executed against them at prices near zero, and the exchanges later cancelled trades far from the pre-crash price.

The mechanism is automated withdrawal (Chapter 2): intermediaries whose models detected abnormal conditions stopped quoting, as their design required, all at once. The lessons were structural, and they produced single-stock circuit breakers, then the limit up–limit down bands, and the end of stub quotes.

*Worked example (illustrative).* An instrument normally shows $50 million at the top of its book. Within ten minutes the quoted size falls to $5 million. A sell order of $20 million that would have moved the price by a few ticks now walks through four levels of a thin book and moves it several percent. Nothing about the instrument's value has changed; its depth has.

*On the day.* Stub-quote executions at absurd prices, and the busted trades afterwards.

| Element | In 2010 |
|---|---|
| Forced flow | A volume-sized sell programme blind to price |
| What failed | Automated liquidity: withdrawal, then the hot potato |
| Signature | Volume up, depth down; stub-quote prints |
| What stayed | Single-stock circuit breakers; limit up–limit down; no stub quotes |

## Chapter 14 — February 2018: the short-volatility products and the vol-control sellers

*Volatility* carries February 2018 as the variance risk premium's unwind and *Tops and Bottoms* as an episode. This chapter assembles the forced flows that made a small equity decline into the largest one-day rise in the volatility index on record, *in Cboe's VIX history from 1990; last verified October 2026*. It is told in full because the store reaches it: the leveraged-product, margin, positioning and volatility series all cover it.

### 14.1 The setting

Through 2017 realised volatility was exceptionally low, and a large pool of capital was positioned to collect the premium between implied and realised volatility. Some of it sat in exchange-traded products that delivered the inverse of the daily return on short-dated VIX futures. Those products were daily-reset funds of exactly the kind Chapter 7 describes: L was −1, so L × (L − 1) was 2, and the rebalance traded with the day's move in VIX futures. When VIX futures rose, the inverse products had to *buy* VIX futures at the close to restore their exposure. Their buying was predictable in direction, concentrated at the close, and large against the depth of the futures they traded.

A second pool sat in volatility-targeting and risk-parity strategies, whose equity exposure was large because realised volatility had been low. Their exposure was inversely proportional to realised volatility (Chapter 7), and a year of calm had levered them up.

### 14.2 The mechanism

Equities fell in the last days of January and on Friday 2 February, after a strong wage print raised rate expectations. The fall raised realised volatility and VIX futures. On Monday 5 February the equity decline continued into the afternoon, and VIX futures rose sharply. The inverse products' rebalance, which is a function of the day's percentage move in the futures, grew with the move and was due at the close, in a market everyone could see would have to absorb it. Participants who understood the arithmetic bought VIX futures ahead of the close, which raised the futures further and enlarged the rebalance. The loop ran into the closing minutes. After the close, the largest inverse note's indicative value had fallen by so much that its issuer exercised its right to terminate it.

The equity side followed over the next sessions. The vol-control and risk-parity strategies, reading a trailing volatility that had now jumped, cut equity exposure on the second, third and fourth days. That was the lagged selling of Chapter 7.2, arriving after the initial shock and extending it.

### 14.3 What the store sees, and what the ledger said

February 2018 is the first of the system's three air pockets (Chapter 19). The system's fragility panel, replayed on public history, shows the leveraged-ETF flow arm firing in the sessions before the drop, the estimate at or near the top of its five-year range. The depth arm stayed off: SPY's Amihud measure was low, because volume was high and the moves before the drop were modest. The flag, which needs both arms, never fired. The case is therefore a clean lesson about the stand-in. The forced flow was visible beforehand. The depth that failed was the VIX futures' depth, not SPY's, and an equity depth measure could not see it. The figures are in Appendix B.

*Worked example (illustrative).* An inverse VIX-futures product with $2 billion of assets faces a day on which its futures rise 80%. Its rebalance is 2 × 2 × 80%, about $3.2 billion of futures to buy at the close. If the market's depth in those futures at the close is a fraction of that, the buying alone moves the price far enough to enlarge the rebalance before it is done. A product whose rebalance is large against the depth of its own underlying is one bad day from self-destruction, and the arithmetic says so in advance.

*On the day.* The volatility index doubling, and the after-hours notices: indicative values collapsing, then a termination announcement before the next open.

| Element | February 2018 |
|---|---|
| Forced flow | The inverse VIX products' close rebalance; then vol-control selling |
| Where depth failed | VIX futures at the close, not equities |
| The store's read | The flow arm fired; the depth arm, on SPY, did not |
| Resolution | The largest product was terminated; the vol sellers finished in days |

## Chapter 15 — March 2020: the dash for cash

*Rates & Liquidity* tells March 2020 as a Treasury-market event. This chapter tells the cascade: how a shock to growth became, for about two weeks, a demand for cash so broad that the market's safest assets were sold to meet it. It is told in full because the store's margin, positioning, volatility and correlation series cover it.

### 15.1 The sequence

The pandemic's spread was a real shock to growth, and equities and credit fell on it in the last week of February. The cascade began in the second week of March, when the selling spread to assets that should have rallied. Treasuries fell while equities fell. The stock–bond correlation, negative through most of the preceding two decades *(US data, 2000–2020; last verified October 2026)*, turned positive for days (Chapter 9). Gold fell. Investment-grade corporate bond funds traded at discounts to net asset value of a size the funds had not shown before. Haddad, Moreira and Muir (2021) document the bond-fund dislocation; Duffie (2020) and the Financial Stability Board's review of the turmoil (2020) document the Treasury market's.

### 15.2 The forced flows

Every forced flow of Chapter 7 arrived together:
- **Margin.** Futures margins rose with realised volatility, and the calls were paid by selling whatever was liquid. The most liquid asset in the world, the US Treasury, was the first thing sold.
- **Leveraged relative value.** Funds running the cash–futures basis trade in Treasuries (long cash bonds financed in repo, short futures) faced rising futures margins and repo haircuts together, which is Chapter 8's spiral in its purest form. Their unwind sold cash Treasuries into dealers whose balance sheets were already full.
- **Redemptions.** Open-end bond funds and money funds holding commercial paper met redemptions, and sold the bonds they could sell, not the ones they would have chosen.
- **Volatility targeting.** The vol-control and risk-parity sellers cut on the lag, as in 2018, but this time on a much larger move.
- **Foreign official holders,** short of dollars, sold Treasuries to raise them.

Market makers, constrained by balance-sheet rules that counted Treasuries against leverage limits, could not absorb what was sold. The safest asset became, for days, hard to sell at a quoted price.

### 15.3 The ETF that was the price

Chapter 3's mechanism ran in public. The largest investment-grade and high-yield bond funds traded at deep discounts. Their net asset values, built from evaluated prices on bonds that were barely trading, said the bonds were worth more than anyone would pay. The authorised participants, whose own balance sheets were full, did not close the gap. The fund's price was the market's only real-time read of what the bonds would fetch, and it was the read the central bank's own announcement eventually acted on.

### 15.4 What stopped it

The Federal Reserve broke both spirals in a sequence of announcements. It bought Treasuries and agency mortgages in unlimited quantity, which put a floor under the price of the most-sold collateral. It opened dollar swap lines and a repo facility for foreign official holders, removing a forced seller. It announced corporate bond facilities that would buy both bonds and bond ETFs, which closed the funds' discounts before most of the buying had happened. The announcement was the trade, because it replaced a forced seller's market with a buyer of last resort.

### 15.5 What the store sees

The store covers March 2020 end to end: margin debt (Figure 2), futures positioning, the volatility index (Figure 5) and the stock–bond correlation (Figure 6). It is the library's clearest case of that correlation turning positive without an inflation regime, because a shared forced seller overrode the regime's sign (Chapter 9). It is not one of the air-pocket ledger's events, which are one-day drops after calm (Chapter 19).

*Worked example (illustrative).* A basis-trade fund holds $10 billion of cash Treasuries financed in repo at a 2% haircut, $200 million of its own capital, and is short the equivalent futures. Futures initial margin rises from 3% to 6%, a $300 million call against futures worth $10 billion, and the repo haircut rises to 4%, another $200 million. The fund must raise $500 million against $200 million of capital. It cannot, so it sells cash Treasuries, and every fund running the same trade sells the same bonds. The trade was hedged against price; it was not hedged against margin.

*On the day.* Treasuries selling off on days equities fell; bond ETFs at discounts; central-bank announcements arriving outside market hours, one after another.

| Element | March 2020 |
|---|---|
| Forced flow | Margin, basis-trade unwind, redemptions, vol targeting, official dollar demand: all together |
| Where depth failed | Treasuries, under dealers' balance-sheet limits; corporate bonds |
| Signature | Stocks and bonds falling together; bond ETFs at deep discounts |
| Resolution | A buyer and lender of last resort, by announcement |

## Chapter 16 — 2021: GameStop and the clearing deposit

The January 2021 squeeze is the clearest case of Chapter 10 in the record, and the clearest case of a cascade stopped by a margin call rather than by a price. The SEC staff's report on the episode (2021) is the history.

### 16.1 The squeeze

Short interest in the stock exceeded its float, borrow was expensive, and the position was widely known. Retail buyers, coordinating in public, bought the stock and short-dated out-of-the-money calls. The call buying left dealers short gamma, so their hedging bought the stock as it rose (Chapter 7.4). The rising price forced shorts to cover. Two forced buyers, the shorts and the dealers, met a float that was largely held by passive and long-term owners who were not selling.

### 16.2 What stopped it

What stopped the buying was a clearing deposit. The equity clearing house computes a deposit for each member broker from the risk of its unsettled trades. The settlement cycle was two days at the time, so the clearing house was exposed to two days of each broker's customers' trades, and the deposit's model charged heavily for concentrated, volatile positions. One morning the deposit charged to the largest retail broker rose to a multiple of its usual level, overnight, because its customers' buying was concentrated in a handful of stocks whose volatility had exploded. The broker could not post it on the schedule, and it restricted its customers to closing their positions in those stocks. Other brokers did the same. The forced buyers lost their access to the market, and the price fell.

The case is Chapter 4 in public: a margin model, behaving correctly, became the binding constraint on an entire class of market participants. The clearing house did not act on the price. It acted on the risk of the unsettled trades, and the risk was a function of the price.

*Worked example (illustrative).* A broker's customers have $3 billion of unsettled buying concentrated in a few stocks. The clearing house's model charges a deposit of 5% on diversified flow, but adds a concentration charge and a volatility charge that bring the requirement on this flow to 30%: $900 million, against a usual deposit an order of magnitude smaller. The broker has hours to post it. Restricting buying reduces the unsettled flow and therefore the deposit, so the restriction is the cheapest way to meet the call.

*On the day.* The broker's restrictions announced before the open; the borrow rate and the halts; the price falling on the restrictions, not on news about the company.

| Element | January 2021 |
|---|---|
| Forced flow | Short covering and dealers' gamma hedging, both buying |
| The constraint that stopped it | A clearing deposit on unsettled trades |
| Signature | Buying restricted by brokers; the price falling on access, not news |
| What stayed | A shorter settlement cycle; scrutiny of deposit models |

## Chapter 17 — 2022: the gilts and the LDI collateral spiral

*Debt Cycles* tells the September 2022 gilt crisis as a fiscal crisis: a budget the market did not believe, and a sovereign whose financing cost jumped. This chapter tells only the collateral mechanics, which would have run the same way whatever the cause of the first move.

### 17.1 The structure

UK defined-benefit pension schemes hedged their long-dated liabilities with liability-driven investment strategies, many held in pooled funds. To match the liabilities' interest-rate sensitivity without holding only gilts, the funds used leverage: long gilts financed in repo, and interest-rate swaps that paid the fund when long yields fell. When long yields rose, the hedges lost value, and the funds owed collateral to their repo and swap counterparties. In normal markets the losses on the hedges were matched by the falling value of the liabilities, so the schemes were not worse off. They did, however, owe cash, and the cash was due within days, while the liability gain was an accounting entry decades away.

### 17.2 The spiral

When long gilt yields rose very sharply over a few sessions, the collateral calls exceeded the funds' cash buffers. To meet them, the funds sold what they held, which was gilts. Their selling pushed long yields higher, which raised the next round of calls. This was Chapter 8's margin spiral with an unusual feature: the forced seller was selling the asset whose fall was creating the call. The pension schemes behind the pooled funds could have injected cash, but on a timescale of weeks, while the calls arrived in days. The Bank of England's Financial Policy Committee record (2022) is the official account.

### 17.3 What stopped it

The Bank of England announced a temporary programme to buy long-dated gilts, explicitly to restore orderly market conditions rather than as monetary policy. It broke the spiral by putting a buyer of last resort under the asset the forced sellers were selling, for long enough for the funds to rebuild their buffers. The programme bought far less than its stated capacity, as the 2020 corporate facilities had: the announcement was the trade.

*Worked example (illustrative).* A pooled fund holds £1 billion of capital and hedges £4 billion of liability sensitivity, so it is levered four times through repo and swaps. A 100 basis point rise in long yields costs the hedges, at a duration of 20, roughly 20% of £4 billion: £800 million owed in collateral. The fund holds £300 million of cash. It must sell £500 million of gilts within days into a market where every similar fund is selling the same gilts.

*On the day.* Long gilt yields rising in a straight line; the central bank's announcement after three sessions; the yields reversing on the announcement.

| Element | September 2022 |
|---|---|
| Forced flow | Collateral calls on leveraged liability hedges |
| Spiral | The forced sale was of the asset whose fall caused the call |
| Timing mismatch | Calls in days; the schemes' cash in weeks |
| Resolution | A temporary buyer of last resort, by announcement |

## Chapter 18 — Two short instances: August 2024 and April 2025

The system's air-pocket ledger scores three events: February 2018 (Chapter 14), and the two below. They are told briefly because their value to this paper is less the mechanism than the honesty: they are where the system's measure was tested, and failed.

### 18.1 August 2024

Through mid-2024 a large carry position had built up: borrowing in yen, at near-zero rates, to hold higher-yielding assets. The Bank of Japan raised rates at the end of July, and a weak US employment report on the following Friday lowered US yields. The interest-rate differential that paid the carry narrowed from both ends at once. On the Monday, Japanese equities fell further in one session than on any day since 1987, *by the Nikkei 225's daily history; last verified October 2026*. In the US, the volatility index printed an intraday spike far larger than the realised move. That was partly a measurement artefact of the pre-open: the index is computed from option quotes, and wide quotes in a thin pre-market produce a high index value without a trade. The equity decline itself was modest by the standard of the cases, and it reversed within weeks.

The mechanism is the carry unwind, a forced flow of margin and funding type across currencies (*Currencies* carries the yen carry), meeting a thin overnight market. The fragility panel's flow arm fired in the sessions before; the depth arm did not.

### 18.2 April 2025

At the start of April 2025 the United States announced tariffs far larger than markets had priced. Equities fell sharply over two sessions, and the following week Treasury yields rose while equities fell, with swap spreads and the cash–futures basis moving in ways that pointed to leveraged relative-value positions being cut. The shock was policy rather than leverage. The cascade element was the speed of the Treasury market's move and the brief reappearance of March 2020's signature, stocks and bonds falling together. The tariffs were then partly paused within days, and the market recovered much of the loss.

The fragility panel's flow arm fired once in the week before; the depth arm did not.

| Instance | Trigger | Forced flow | The panel before it |
|---|---|---|---|
| August 2024 | A policy-rate hike and a weak payroll report | The yen carry unwind | Flow arm on; depth arm off; flag off |
| April 2025 | A tariff announcement | Leveraged relative-value cuts in Treasuries | Flow arm on once; depth arm off; flag off |

---

# Part IV — The Fragility Read, as Measured

The organising claim says the ratio of forced flow to depth is measurable before the move. This Part describes how the system measures it and what its ledgers say. It re-derives no figure the store holds, and it does not upgrade a FAIL or an INSUFFICIENT into a finding. The verdicts are stated as filed; their figures are in Appendix B.

## Chapter 19 — Forced flow against depth

### 19.1 The fragility panel (item 71)

The system's direct measure of the organising claim is the liquidity-fragility panel, signal-triage item 71. It is computed by the fragility module from stored series and printed in the close's and the Weekly's Mechanics. It has four legs:
- **The depth stand-in:** SPY's Amihud measure, absolute return per dollar of volume (Chapter 5), with its range per unit of volume beside it. Top-of-book depth in the index futures is a listed gap: the system has no source it may store.
- **Margin debt:** FINRA's margin statistics, and their share of the Federal Reserve's Z.1 equity market value, the leverage leg of Chapter 7.1.
- **The leveraged-ETF rebalance estimate:** AUM × L × (L − 1) × the day's return, summed over seven ProShares equity funds whose net asset values are published without a key, the forced flow of Chapter 7.3.
- **Dealer gamma:** the stored net gamma exposure from the system's own captures (*The Dealer's Hand*), the forced flow of Chapter 7.4.

The panel's **fragility flag** fires when two arms are on together: the depth stand-in at or above its 90th percentile over five years, and the forced-flow estimate above its 90th. It carries flag rights only. It modifies nothing, and any right it could earn is the operator's ruling after its ledger. The panel also supplies the "liquidity" row of the volatility-event lenses (item 52) and a line in the ES levels read (item 45).

**Figure 1 — Forced flow against depth.** *Placeholder, drawn in a later edition: the leveraged-ETF rebalance estimate and SPY's Amihud stand-in, the three air pockets marked. Keys: `levetf.aum` and `yfinance.mkt_spy`; the estimate and the measure are computed by the fragility module, not stored as keys.*

**Figure 2 — Margin debt through the cases.** *Placeholder, drawn in a later edition: FINRA margin debit balances (`finra.margin_debit`), with the cases marked.*

### 19.2 Its ledger: ST-R6.71d, FAIL

The panel's calibration ledger, ST-R6.71d, asks whether the flag was on before the three air pockets of February 2018, August 2024 and April 2025, and whether sessions with the flag on were followed by a sharp fall more often than sessions with it off. Its pass rule was pre-registered before the scoring code was written. The flag must be on in at least one of the five sessions before at least two of the three air pockets, with at least 20 flag-on sessions in the sample. The share of flag-on sessions followed within five sessions by an SPY fall of 2.5% or more must also be at least twice the flag-off share.

**The verdict as filed is FAIL.** The flag was on before none of the three air pockets. The second condition was met: the fall-after share with the flag on was more than twice the share with it off. But the ledger itself notes that both arms rise with volatility, so part of that lift is volatility clustering rather than fragility. The ruling of 24 October 2026 (D9) accepted the verdict. The flag keeps a flag's rights and nothing more.

The FAIL is informative, and Chapters 14 and 18 have already said why. In each of the three events the flow arm fired in the week before and the depth arm did not. The forced flow was visible. What the system could not see was depth, because its depth measure is a stand-in that reads low when volume is high, which is exactly when the forced flow is building (Chapter 20).

### 19.3 The squeeze line (item 74)

The second measure is item 74's hedge-fund positioning line, printed in the Weekly's Positioning & flows. It reads leveraged funds' net positions in the E-mini S&P 500 and Nasdaq-100 futures from the CFTC's Traders in Financial Futures report, with the net short share's dual percentiles, beside FINRA short interest. Its **squeeze-risk flag** pairs ES's net short at or above its 90th percentile with the Amihud stand-in at or above its 90th. That is Chapter 10's crowded short meeting thin depth, written as a rule. It prints in Positioning & flows and as a context line in the ES levels read.

### 19.4 Its ledger: ST-R6.74b, INSUFFICIENT at n 0

The squeeze line's ledger, ST-R6.74b, asks whether the S&P 500's 20-session outcome after an episode of extreme leveraged-fund net shorts beats the baseline. Its pass rule was pre-registered: at least 12 episodes; the episodes' median 20-session outcome at least one percentage point above the baseline's, and at least 60% of episodes positive.

**The verdict as filed is INSUFFICIENT, at n 0.** The ledger reads the stored history only, and when it was first run the store held no ES rows: the futures report's pull added ES in the same build. The ruling of 24 October 2026 (D9) accepted it. The verdict says nothing about squeezes. It says the measure has not yet been tested.

### 19.5 The other measures that touch this paper

Four more items measure pieces of the mechanism, each with its own ledger:
- **The three-timeframe ES read (item 45)** prints levels and a lean each morning and at the close, and the ES ledger scores them on the next session.
- **The volatility-event flag (item 52)** fires on a one-day VIX change of 15% or 3 points, attributes the event by its lenses, and enters its own ledger. It earns no modifier right before 30 events.
- **Relative options volume (item 61)** flags a name whose session options volume runs at 1.5 times its 20-session average. It prints "volume, no side", because volume says nothing about direction, and its ledger is pre-registered.
- **The dealer captures (6b)** store net gamma, the gamma flip and the walls at three slots a session. The regime word prints only at a net-to-gross of 0.10 or more, and the scorecard prints "insufficient sessions" below 20.

| Item | Measures | Ledger | Verdict as filed |
|---|---|---|---|
| 71 | Forced flow against depth; the fragility flag | ST-R6.71d (the air pockets) | **FAIL** |
| 74 | Leveraged-fund shorts in ES and NQ; the squeeze-risk flag | ST-R6.74b (extreme net shorts) | **INSUFFICIENT, n 0** |
| 45 | The ES read's levels and lean | the ES ledger | scored daily |
| 52 | Volatility events and their lenses | the volatility-event ledger | no right before 30 events |
| 61 | Relative options volume, no side | OS-12c | pre-registered |
| 6b | Dealer gamma, flip, walls | the dealer scorecard | insufficient sessions below 20 |

## Chapter 20 — What the measures cannot see

The FAIL in Chapter 19 is a result about the measures as much as about the mechanism, and the honest reading separates the two.

**Top-of-book depth is a listed gap.** The quantity the organising claim needs is how much the market would absorb at the moment of the forced flow: the depth at the top of the futures book, and its resilience. The system has no source for it that its rules allow it to store, and it names no vendor's proprietary depth figure as a measured series. The Amihud measure is a stand-in. It reads price impact per dollar traded over a whole session, so it mixes information with illiquidity. And it falls when volume rises, which in a building cascade is exactly the wrong way. Volume rises before depth fails (Chapter 5), so the stand-in reads "deep" in the sessions when depth is about to vanish.

**The flow estimate is partial.** The leveraged-ETF estimate covers seven equity funds. It does not cover inverse volatility products, which were the decisive flow in February 2018, nor volatility-targeting and risk-parity funds, whose exposure is not published, nor commodity trading advisers, nor the basis trade. The system sees one forced flow of five, and the one it sees was not the largest in two of the three events.

**The other legs are slow.** Margin debt is monthly, and published weeks after the month. The futures positioning report is weekly, measured on a Tuesday and released on the Friday. FINRA short interest is twice monthly. Dealer gamma is inferred from open interest and an assumption about who holds which side, which is why the system prints "inferred, not observed" above every dealer table.

**No series sees the clearing house.** The margin rates the clearing houses charge, the deposits they call and the haircuts repo lenders apply are not in the store. Two of the seven cases (2021 and 2022) turned on exactly those numbers.

The consequence is a sharp distinction. The mechanism in Part II is argued from first principles and is expected to hold. The system's present ability to measure it before the move is unproven, and on its one completed test it failed. A reader should hold the first with confidence and the second not at all, until a ledger says otherwise.

| What the claim needs | What the system has | The gap |
|---|---|---|
| Top-of-book depth and resilience | SPY's Amihud measure | A stand-in that reads deep as volume rises |
| All forced flows | Seven leveraged equity funds' rebalance | Inverse vol products, vol targeting, CTAs, basis trades unmeasured |
| Leverage now | Monthly margin debt; weekly positioning | Weeks of lag |
| Dealer positioning | Inferred gamma from captures | Inferred, not observed |
| Clearing margins and haircuts | Nothing stored | The binding constraint in 2021 and 2022 |

---

# Part V — Tactical Applications, Wiring, Environments, and the Appendices

## Chapter 21 — Tactical applications, by horizon

This paper's tradeable content is the identification of fragility: who is forced, at what size, against what depth. Its most valuable application is defensive, because a cascade is a moment when the small book should be absent, or present only as patient capital after the forced flow is done. What follows lays that against the seven rungs, in prose and then as a cheat sheet.

*Nothing in this chapter is investment advice. It describes how one operator, running one book under one set of rules, decides which opportunities are theirs and which are not.*

**Intraday.** What is tradeable is nothing: the closing-auction concession and the zero-day hedging flow are visible, but the edge is a latency and inventory edge that belongs to market makers. The edge type would be liquidity, and the operator is not the one paid for it. The counterparty is the automated liquidity supplier, who transacts because it is paid the spread and can pull its quotes in microseconds. Competition has not removed the edge; it has removed the operator's access to it. Nothing would end that, because the asymmetry is structural. There is no expression and no book. The read is defensive, in the 12:30 slot's volatility-event gate and the close's Mechanics: a reason to delay an entry, never a reason to make one.

**Days.** What is tradeable is the aftermath of a forced flow that has finished: the reversal after a close rebalance, a vol-control unwind or a margin-driven liquidation, once the flow is spent and the price has overshot. The edges are liquidity and positioning and flow. The counterparty is the forced seller, who transacts because a constraint requires it, not because the price is right. Competition has not removed the edge because the capital that could supply it is the same capital under the constraint. Dealers and market makers withdraw exactly when the concession is largest. It would end if the forced flows became so well known that patient capital pre-positioned against them and the overshoot vanished. The expression is a defined-risk options position entered after the flow is spent, never into it. The book is C. It is read in the close's Mechanics (the fragility line, the volatility-event block, the dealer block) and the next 07:00 anchor's volatile-day flag.

**Weeks.** What is tradeable is the vol-control and risk-parity re-leveraging that follows a cascade: the strategies cut on the lag and re-buy on the lag, so their buying arrives weeks after the low. The edges are positioning and flow and horizon. The counterparty is the volatility-targeting fund, transacting because its trailing window says so. Competition has not removed the edge because the strategies' rules are public but their capital is large, and they cannot re-enter faster than their windows allow. It would end if the strategies shortened their windows or the pool shrank. The expression is equity or index exposure built over the re-leveraging window. The book is B. It is read in the Weekly's Positioning & flows and its volatility lens table.

**Months.** What is tradeable is the stance: the decision to hold less leverage when the forced-flow-to-depth ratio is high, and to be a buyer of last resort in size the book can afford when a cascade has run. The edges are patience and regime recognition. The counterparty is the forced seller at the bottom of a cascade and the de-risking allocator. They transact because a mandate or a margin call requires it. Competition has not removed the edge because the institutions able to buy are the ones under the constraint. It would end if a standing official backstop made every cascade end before it overshot, which the 2020 and 2022 announcements went some way towards. The expression is index and Treasury exposure inside the Doctrine's bands, added after the forced flow is spent. The book is A. It is read in the Monthly's Mechanics and slow layers, and in the Top & Bottom composite once it exists.

**Cyclical.** What is usable is the knowledge of where leverage has built: margin debt against equity value, the size of the leveraged-product and vol-targeting complex, the carry trades. It is an input to stance, not a trade. The edge is regime recognition. There is no transacting counterparty at this rung. Competition is absent because few participants hold a view across a leverage cycle. It would end if leverage became continuously and accurately measured, which Chapter 20 says it is not. It is expressed through the months-rung stance; it feeds Book A; and it is read in the Monthly's slow layers.

**Secular.** What is usable is structural change in who supplies liquidity: the shift from bank dealers to non-bank market makers, the growth of the closing auction, shorter settlement cycles. Each changes how cascades travel. The edge is analytical, and weak. There is no counterparty and no position. It feeds the annual structural review's questions and the standing register.

**Generational.** There is no edge for this book at this horizon. The usable content is that market structure is made by rules, and the rules change after each cascade. There is no counterparty, no expression and no book.

| Horizon | What is tradeable | Edges | Counterparty | Book | Read in |
|---|---|---|---|---|---|
| **Intraday** | Nothing; a reason to wait | — | Automated liquidity | — | The 12:30 slot; the close's Mechanics |
| **Days** | The aftermath of a spent forced flow | Liquidity; positioning and flow | The forced seller | C | The close's Mechanics; the 07:00 volatile-day flag |
| **Weeks** | The vol-control re-leveraging | Positioning and flow; horizon | Vol-targeting funds | B | The Weekly's Positioning & flows |
| **Months** | Stance: less leverage when fragile; buying after | Patience; regime recognition | Forced sellers; de-risking allocators | A | The Monthly's Mechanics and slow layers |
| **Cyclical** | Where leverage has built | Regime recognition | None | A, as input | The Monthly's slow layers |
| **Secular** | Who supplies liquidity, and how that changes | Analytical | None | — | The annual review; the register |
| **Generational** | — | — | — | — | — |

The principle this chapter states in this paper's terms: **the small book's edge in a cascade is that it is not forced.** Every edge above is the reward for transacting when someone else must. The operator who is leveraged, margined or volatility-targeted has given that edge away before the cascade begins.

## Chapter 22 — Wiring

This paper owns a mechanism the system measures in part. Its wiring is mostly where those measures print.

**The 16:45 close.** The close's Mechanics carries the fragility panel's line (item 71), the volatility-event block and its lenses (item 52), the dealer block (6b) and the ES read's levels (item 45, with the squeeze line's context from item 74). The close's detail tables carry relative options volume (item 61). A cascade day reads first there.

**The 07:00 anchor.** The volatile-day flag's arms (the VIX, ES's overnight range, the gap, the Gamma dial) and the ES read. The anchor recomputes nothing; it reads the object and the stored rows.

**The 12:30 slot.** It opens on a volatility rise of 15% or 3 points: the intraday rung's one defensive read.

**The Weekly.** Positioning & flows carries the hedge-fund positioning line and the squeeze-risk flag (item 74). Mechanics carries the fragility panel's week and the dealer block's facts.

**The Monthly.** Mechanics and the slow layers carry the panel at the Monthly's horizons, margin debt's share of equity value, and the dealer retrospective.

**Register fields this paper populates.** A decision taken on a cascade day should carry three things: the forced-flow class it believes is transacting (margin, vol targeting, leveraged-product rebalance, dealer gamma, redemptions, or squeeze cover); whether that flow is still running or spent; and the depth read at entry, with the stand-in named as a stand-in. These are categorical so they can be counted.

**Claims-registry entries this paper owns.** The forced-flow-to-depth ratio as the organising claim; the five forced flows and their timing (Chapter 7); the leveraged-product rebalance formula; margin and haircuts as one procyclical mechanism (Chapter 4); and the ETF as the price when its basket does not trade (Chapter 3). Other papers that use these cite this one.

**What the annual review re-verifies.** Whether the fragility ledger's verdict has changed on a box re-run; whether the squeeze ledger has reached its 12 episodes; whether a depth source the rules allow has appeared; whether the leveraged-product and vol-targeting complex has grown or shrunk; and whether any structural change (settlement, auctions, the clearing models) has altered how a cascade travels.

## Chapter 23 — Environments

The master environment matrix belongs to *Debt Cycles*. This paper's contribution is, for each of the eighteen, which forced flow dominates, what happens to depth, and how likely a cascade is to run. No entry carries a probability; the words describe mechanism, not frequency.

- **Expansion.** Calendar flows dominate and depth is ample. Leverage builds quietly, which is the cascade's preparation rather than its occasion.
- **Recession.** Redemptions and de-risking dominate. Depth thins in credit first. Cascades run where funds offer daily liquidity on illiquid assets.
- **Inflation.** Rate-driven repricing dominates, and stocks and bonds fall together. The cascade risk is in leveraged duration hedges, as in 2022.
- **Disinflation.** Duration buying dominates. Depth is good, and the stock–bond hedge works.
- **Deflation.** Margin and collateral dominate. Leveraged real assets are the forced sellers.
- **Stagnation.** Low turnover and thin depth that nobody notices until a flow arrives.
- **Bubble.** Momentum and leveraged-product flows dominate, and short squeezes are common. Depth is plentiful and illusory.
- **Crash.** Every forced flow at once; depth withdrawn. This is the environment Part II describes.
- **Liquidity crisis.** Margin and haircuts dominate everything. Whoever still quotes sets the price. The ETF is often the only price.
- **Banking crisis.** Deposit flight becomes asset sales. Dealers' own balance sheets are the constraint, and Treasury market depth can fail.
- **Fiscal crisis.** Collateral calls on leveraged sovereign-debt structures dominate. The gilts' mechanism belongs here; the fiscal story belongs to *Debt Cycles*.
- **Currency crisis.** Carry unwinds and official dollar demand. A foreign official seller of Treasuries is possible, as in 2020.
- **War.** State-imposed rules and venue closures. Price limits and halts push flow to whatever is open. n≈0 for most modern markets.
- **Technological revolution.** Issuance and lockup expiries; retail and options flow; squeezes in narrative names.
- **Financial repression.** Captive buyers supply depth in the repressed asset. A cascade is unlikely there and likely in whatever the repression pushes capital into.
- **Capital controls.** The permitted participants are the only depth. Forced flow cannot leave, so it moves the domestic price.
- **Monetary-system change.** The collateral's own value is in question. n≈0 in the modern sample.
- **Structural break.** A change in the rules of market structure itself (settlement, auctions, clearing) changes how every cascade travels. The relationships measured before it should be re-verified, not assumed.

---

## Appendix A — Assumptions and falsifiers

*The instrument the annual structural review reads. Sections (a) to (e) in the fixed format.*

**(a) Mechanisms treated as durable.**

1. Liquidity is supplied by intermediaries when it pays and withdrawn when it does not; displayed depth is not promised depth (Chapters 1–2).
2. The size of a move is set more by the ratio of forced flow to depth than by the news (Chapter 6).
3. Margin, haircuts and collateral calls are procyclical: volatility raises them and they force sales that raise volatility (Chapter 4).
4. Funding liquidity and market liquidity reinforce each other into spirals that need no further shock to continue (Chapter 8).
5. Daily-reset leveraged and inverse products trade with the day's move at the close, in proportion to AUM × L × (L − 1) (Chapter 7).
6. Volatility-targeting strategies sell on the lag of a volatility rise and re-buy on the lag of its fall (Chapter 7).
7. A shared forced seller raises correlations across assets regardless of their fundamentals (Chapter 9).
8. A cascade ends when a participant with unencumbered capital, often an official lender or buyer, replaces the forced seller (Chapters 8, 15, 17).

**(b) Empirical relationships relied on, with sample, regime and last verification.**

| Relationship | Sample | Regime measured in | Last verified | Where used |
|---|---|---|---|---|
| Equity correlations rise more in down markets than a normal model predicts | Developed equity markets, 1960s to the late 1990s (Longin and Solnik, 2001) | Multiple | October 2026 | Chapter 9 |
| The stock–bond correlation's sign depends on whether inflation or growth risk dominates | US data across the post-war period | Multiple; positive in inflationary regimes | October 2026 | Chapter 9 (owned by *Debt Cycles*) |
| Bond ETF discounts open in stress when the basket does not trade | US corporate and municipal bond funds, 2008 and 2020 | Stress | October 2026 | Chapters 3, 15 |
| Leveraged and inverse products' close rebalance is predictable from the day's return | US daily-reset ETPs, since their launch | All | October 2026 | Chapters 7, 14 |
| The fragility flag (item 71) is not on before the air pockets | US, 2015–2026, three events (ST-R6.71d) | One sample | October 2026 (FAIL) | Chapter 19 |

**(c) The falsifier for each relationship.**

- *Down-market correlation:* correlations measured on a recent window fail to rise in drawdowns. Then Chapter 9's first section is a historical regularity, not a mechanism's footprint.
- *The stock–bond sign:* the sign stops tracking the inflation-versus-growth balance over a full cycle. *Debt Cycles* owns the falsifier.
- *Bond ETF discounts:* a stress episode in which the basket stops trading and the discount does not open. Then the ETF is no longer the price in stress, perhaps because authorised participants' capacity has grown.
- *The close rebalance:* a stress close in which the leveraged-product complex's estimated rebalance does not appear in the imbalance. Then the estimate's AUM or leverage inputs are wrong.
- *The fragility flag:* a box re-run in which the flag is on before at least two of the three air pockets would reverse the FAIL. A new depth source might do that; a change in the rule after the fact would not count.

**(d) Standing-register items that touch this paper.**

Four changes are watched. *Automated liquidity provision*: a liquidity event with no bank dealer in it would reorder Chapter 2's account of who withdraws first. *Faster settlement or a round-the-clock venue* would change Chapter 4.4's trade-off and weaken the close's role in Chapter 1. *Growth in the leveraged-product and vol-targeting complex* would make Chapter 19's flow arm, and Chapter 20's coverage gap, matter more. *A rising zero-day share of index options* would enlarge Chapter 7.4's intraday flow, which *The Dealer's Hand* owns.

| Change | Tripwire | What it would do |
|---|---|---|
| Automated liquidity provision | A dealerless liquidity event; the non-bank share | Chapter 2's withdrawal ordering |
| Faster settlement; continuous markets | A shorter cycle; a 24-hour venue | Chapters 1 and 4.4 |
| Leveraged-product and vol-targeting growth | A stated asset level | Chapters 19 and 20 |
| Zero-day options | A stated volume share | Chapter 7.4; possibly a new case |

**(e) Inventory of dated figures.** The seven figures are placeholders in this draft, each named with its store keys: Figure 1, forced flow against depth (`levetf.aum`, `yfinance.mkt_spy`, computed by the fragility module); Figure 2, margin debt (`finra.margin_debit`); Figure 3, leveraged funds' net in ES (`cftc.tff_lev_money_net_oi`); Figure 4, dealer gamma and the session's range (`exposure.net_gex`, `yfinance.mkt_spy`); Figure 5, the volatility index through the cases (`fred.vix`); Figure 6, the stock–bond correlation (`calc.corr_spy_tlt_60d`); Figure 7, the cascade loop (conceptual, no series). Every case figure the text quotes is in Appendix B.

---

## Appendix B — The dated appendix

*Everything in this appendix carries an as-of date and is history rather than a read if that date is more than a year old. Nothing here is investment advice, and no security is recommended.*

**As of: 26 October 2026.**

**B.1 — The fragility chain's ledgers, as filed.** *(laptop first editions of 23 October 2026, public sources; a box re-run supersedes each; verdicts accepted under ruling D9 of 24 October 2026)*

- **ST-R6.71d, the air pockets against the fragility panel (item 71): FAIL.**
  - *Sample:* 2,965 sessions from January 2015 to October 2026.
  - *The first condition, on before the air pockets:* the flag was on before 0 of 3 against the rule's 2.
  - *The second condition, the fall-after share:* an SPY fall of 2.5% or more within five sessions followed 31.1% of flag-on sessions and 6.4% of flag-off sessions; the rule asks at least twice.
  - *Flag-on sessions:* 135.
  - *Context outside the rule:* after sessions with SPY's 20-session realised volatility at its 90th percentile or above, 27.4% were followed by such a fall.
  - *In the five sessions before each air pocket,* the flow arm was on: February 2018 twice (the estimate's percentile 91 and 100), August 2024 three times (98, 96 and 96), April 2025 once (97). The depth arm's percentile never exceeded 71.
  - *Dealer gamma* is left out of the replay, having no stored history before the captures began.
- **ST-R6.74b, extreme leveraged-fund net shorts in ES (item 74): INSUFFICIENT, n 0.** No ES rows were stored at the edition; the futures-positioning pull adds ES from the same build. The rule needs 12 episodes.

**B.2 — The cases' figures.** *(as recorded in the cited histories; last verified October 2026)*

| Case | Figure | Source |
|---|---|---|
| 19 October 1987 | The Dow Jones Industrial Average fell 22.6% in one session | Brady Commission (1988) |
| 1998 | LTCM's creditors' recapitalisation was about $3.6 billion | President's Working Group (1999) |
| 6 May 2010 | The sell programme was 75,000 E-mini contracts, about $4.1 billion; trades more than 60% from the pre-crash price were cancelled | CFTC–SEC (2010) |
| 5 February 2018 | The VIX rose about 116% in one session, its largest one-day percentage rise | Cboe |
| March 2020 | The VIX closed at a record of about 82.7 on 16 March | Cboe |
| January 2021 | The clearing deposit charged to the largest retail broker rose to about $3 billion on 28 January | SEC staff report (2021) |
| September 2022 | The Bank of England's temporary purchases totalled about £19 billion against a stated capacity of £65 billion | Bank of England (2022) |
| 5 August 2024 | The Nikkei 225 fell about 12.4% in one session | Japan Exchange Group |

**B.3 — Structure as it stands.** *(as of October 2026)*
- **US equity settlement** is T+1, since 28 May 2024; it was T+2 in January 2021.
- **The market-wide circuit breakers** halt trading at declines of 7%, 13% and 20% in the S&P 500 from the prior close.
- **Single stocks** trade inside limit up–limit down bands.
- **The closing auction** is commonly reported as roughly a tenth of US-listed equity volume, and more on index rebalance days. The figure varies by venue and by source.
- **The futures exchange's** automatic pause on the index futures is five seconds.

**B.4 — What the store does not yet hold.** *(as of October 2026)*
- No top-of-book depth series.
- No clearing-house margin or repo haircut series.
- No assets for volatility-targeting strategies or inverse volatility products.
- ES rows for the squeeze ledger began only with the build that added them.

Every gap is named in Chapter 20; this list dates them.
