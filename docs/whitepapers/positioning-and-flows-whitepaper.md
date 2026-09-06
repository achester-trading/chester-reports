# Positioning & Flows

## Who Is Forced to Move, When, and Whether the Market Is Absorbing Them

**Companion white paper — chester-reports library**
**Series placement:** Companion **XVI** — after *Equities* (XV) and before *Portfolio Construction Across Regimes* (XVII), per the library guide. Cross-references in this paper are by name.
**Version:** 1.0 — Draft, 6 September 2026
**Status:** Framework with as-built sources. Three of its inputs (dealer exposure by bucket, closing-auction flow, retail activity) were built or admitted in the first week of September 2026; the rest are specified with their data status stated honestly. Reread when the closing-auction sampler has sixty sessions of history and when the first fifty positioning-conditioned decisions have closed.

---

### Reader's note

Every other paper in the library explains how a piece of the market *thinks* — how the rate machine sets discount rates, how the earnings cycle reprices equities, how the tail scenarios would unfold. This paper explains how a large part of the market *doesn't* think. A dealer hedging a book, a volatility-targeting fund cutting exposure because realized volatility rose, a leveraged ETF rebalancing into the close, an index fund buying a name because a committee added it, a pension rebalancing because stocks beat bonds this month, a yen-funded carry trade being unwound because the yen moved: none of these participants has a view. They have a rule, and the rule is public or inferable. The *Operating Doctrine* names this edge family — structural flows — as the one a small book can harvest precisely because the counterparty is not trying to win; it is trying to comply.

The paper is organized around one question, asked of every flow: **who is forced to move, when, in which direction and size, and is the market absorbing them?** The first three parts of the question produce a *map and a calendar*. The fourth produces the paper's contribution to the architecture — the measurement of *response per unit of stimulus*, which Change Order #3 identified as a single primitive shared by four otherwise unrelated signals and which this paper treats as the organizing idea. A forced seller met by deep demand is a bullish fact wearing a bearish headline. A forced seller met by nothing is the beginning of the thing the tail scenarios describe.

The paper is long because the map is large. Part I is the argument; Part II the map of mechanical holders; Part III their calendars; Part IV the absorption measurement, with worked examples; Part V the models by which the system *estimates* flows it cannot observe, with their uncertainties stated; Part VI the reading of positioning surveys, which is where most retail use of this data goes wrong; Part VII the wiring into the cascade and the books; Part VIII the data-status table; Part IX validation and what would change the paper. Readers who want the operating content can go to Parts IV, VI and VII.

---

## Part I — The Premise

### 1.1 A market with two kinds of participants

Divide the market's participants by whether their next trade depends on their view or on a rule. The first kind — discretionary managers, informed insiders, the operator of this book — trade when they believe something. The second kind trade when a condition is met: a price crosses a level, a date arrives, a volatility measure changes, an index committee publishes a list, a margin ratio is breached. The second kind has grown for thirty years and now accounts for a substantial share of daily volume, and its defining property is the one this paper exploits: **its behavior is knowable in advance**, in direction and often in magnitude, because the rule is public or can be inferred from the participant's mandate.

That knowledge is not a prediction of price. A flow is not a forecast; it is a *pressure*, and pressure meets other participants. The paper's claim is narrower than "forced flows move prices," which is true but useless on its own. The claim is that **the combination of a known pressure and a measured response is information the headline does not contain** — that watching what price does per unit of forced flow tells you about the participants who are *not* forced, which is the thing you actually want to know.

### 1.2 Why this is an edge family for a small book

The doctrine's Part III sorts the nine alpha families by whether a $300,000 part-time book can harvest them, and structural flows are among the most available, for three reasons the paper states because they also mark the family's limits.

The flows are large relative to the book and small relative to their own market, which means the book can position around them at sizes that matter to no one. A leveraged ETF rebalancing $2 billion into a close does not notice a hundred-share order in front of it. The flows are *scheduled* or *triggered* rather than continuous, which suits a book that decides at three daily touches: a calendar can be read on Sunday, a trigger level can be staged as a conditional order, and neither requires a screen during the session. And the flows are *mechanically explainable*, which satisfies the doctrine's Rule 6 — name the edge, the counterparty, and why it persists. It persists because the counterparty's mandate is to follow the rule, not to avoid being front-run; that is what the family is.

The limits are the mirror. A flow that is public is also visible to every other participant who reads the same calendar, and the obvious version of the trade — buy the inclusion name before the inclusion date, fade the month-end rebalance — is priced quickly and often over-priced. Nasdaq's own research on closing-auction imbalances found the average price reaction to the announced imbalance small and rapidly incorporated. The edge, where it exists, is in the parts that are *not* obvious: the second-order timing, the interaction of two flows, the absorption reading, and the flows that are inferred rather than announced. The paper's models in Part V are aimed there.

### 1.3 The independence principle

The architecture's rule that correlated confirmation counts once (its Section 26.9) governs this paper more than any other, because positioning data is the easiest kind to double-count. Five surveys that all say "bullish" are one fact about the crowd, not five. Dealer gamma, dealer delta, dealer vanna and dealer charm are one chain read four ways. A closing-auction sell imbalance and a leveraged-ETF rebalance on a down day are the *same* flow seen twice if the ETF's rebalance is a component of the imbalance. The paper therefore assigns every flow to a **mechanism group**, and the groups — six of them, listed in Part VII — are the units that vote. Within a group, additional series add color; across groups, they add confirmation. The architecture's failure mode that this prevents is the one the doctrine's Part VIII calls fighting the tape with five indicators that are secretly one.

---

## Part II — The Map: Mechanical Holders

Each holder is described by its rule, the direction and approximate size of the flow the rule produces, the observability of the flow (announced, inferable, or hidden), and the data the system uses. The order runs from the fastest clocks to the slowest.

### 2.0 The participant map — who owns the market and who trades it

Before the mechanical holders are described one at a time, the paper places them among *all* the holders, because the share a participant has of ownership and the share it has of daily volume are different numbers, and the difference is most of what this paper is about. A pension owns a tenth of the market and transacts almost nothing until quarter-end; a high-frequency market maker owns almost nothing and is on one side of half the tape. The table gives approximate shares for the U.S. equity market as of mid-2026, drawn from exchange, industry-association, and market-maker disclosures and from the academic literature on passive ownership; every figure is a range, every range is a snapshot, and the registry carries them as `observation_type: inferred` with a review date. Two cautions attach. Volume shares are *per side* — every trade has two participants — so the column does not sum to one hundred; and ownership and volume come from different measurement systems (Federal Reserve flow-of-funds for ownership; exchange and wholesaler tapes for volume), so the two columns are not directly comparable.

**First, what is being measured.** Three denominators are routinely confused in positioning commentary, and they give answers that differ by an order of magnitude for the same institution.

*Direct ownership of U.S.-listed equity* (Table A) is the Federal Reserve's flow-of-funds measure: who legally holds the shares, immediate holder only, one asset class, one country. On this measure pension funds hold ~9% and insurers ~2%.

*Global assets under management by institution type* is a different universe: pension assets worldwide are roughly $55–60 trillion, insurance assets roughly $40 trillion, regulated open-end funds roughly $70–80 trillion, sovereign wealth funds roughly $12–13 trillion. On this measure pensions and insurers are among the largest pools of capital in existence.

*Equity-relevant AUM* is the intersection: global AUM multiplied by each institution's equity allocation — pensions at roughly 40–45%, insurers at perhaps 10–20% depending on jurisdiction and on whether separate accounts are counted, with general accounts bond-heavy by regulation and by liability structure.

The gap between the first and the second has two causes, both of them accounting rather than economics. **Flow-of-funds records the immediate holder, not the beneficial one:** a pension whose U.S. equity exposure sits in a commingled index fund or an ETF appears in the mutual-fund or ETF row, not the pension row. Pension funds held close to 30% of U.S. equities in the 1980s, when they held stocks directly; the fall to ~9% is overwhelmingly a change in *how* they hold rather than in *how much*. And **an institution's asset mix is not the market's**: an insurer with an enormous balance sheet may be a minor equity holder.

None of the three, however, is the measure this paper needs. What determines a participant's importance to a forced-flow framework is:

> **forced-flow footprint = equity exposure × turnover × rule-boundness**

A forty-trillion-dollar insurance industry holding fifteen percent equity with near-zero annual turnover generates less tradeable forced flow than a five-hundred-billion-dollar volatility-control complex that can reset its entire book inside a week, because the second is obliged to trade on a rule and the first is not. This is why the tables below size participants by *volume on the day their rule binds* rather than by assets, and why the same institution can appear twice with different weights: insurers are negligible in ordinary equity volume and a major forced seller of duration in a liability-driven rate shock, which is a rates event that reaches equities through the discount rate and the collateral chain rather than through the equity tape.

**Table A — beneficial ownership. This one sums to 100%, and it is the only one that does.** These are the sectors that legally own U.S. corporate equity, on the Federal Reserve's flow-of-funds basis. Approximate, mid-2026.

| Owner sector | Share of U.S. equity owned |
|---|---|
| Households and nonprofits, direct holdings | ~38% |
| Mutual funds | ~20% |
| Foreign investors (private ~15–16%, official ~2%) | ~18% |
| Exchange-traded funds | ~9% |
| Pension funds (private, state and local) | ~9% |
| Insurance companies | ~2% |
| Other (broker-dealers, banks, closed-end funds, holding companies) | ~4% |
| **Total** | **~100%** |

Two conventions in that table matter and are the source of most published confusion. **Hedge funds are inside the household row**, not beside it — the Federal Reserve's accounts treat hedge-fund holdings as household-sector assets, which is why "households own 38% of the market" is true and misleading at once. And **"passive" is not a sector**: an index fund's shares are owned by whoever owns the fund. Passive management is an attribute that cuts across the mutual-fund, ETF, pension, and foreign rows.

**Table B — cross-cutting attributes. These do not sum to 100% and must not be added to Table A.** They are the lenses the rest of this paper actually uses, because obligation follows the *mandate*, not the legal owner.

| Attribute | Approximate share of the market it applies to | What it cuts across |
|---|---|---|
| Passively managed (index mandates) | ~33–38% once institutional index mandates are counted, against a headline fund-only figure near half that | Mutual funds, ETFs, pensions, foreign, insurers |
| Actively managed by professionals | ~35–40% | The same rows, minus the passive share |
| Self-directed by households | ~30–35% | The household row, less the part held through funds |
| Hedge funds | ~3–5% | Sits inside the household residual |
| Leveraged and inverse ETFs | ~0.3% ($100–150B) | Inside the ETF row |
| Shares sold short | ~1.5–2% of index market cap; 20%+ of float in individual names | A negative position layered on the above |

**Table C — who trades, and when they are forced.** Ownership share and volume share are different measurement systems and different questions; this is the table the rest of the paper is built on. Volume shares are *one side* of the tape and therefore do not sum to 100%. "Heightened" is defined per row, because each participant's stress day is a different day.

| Participant | Owned (Table A/B basis) | Ordinary volume (one side) | Heightened volume — and the day it happens | Forced or discretionary |
|---|---|---|---|---|
| Households / retail, self-directed | ~30–35% (attribute) | 30–37% (2026, a record; ~18% in 2024) | 40–45% on meme and gap days | Discretionary, attention-driven |
| Index and passive mandates | ~33–38% (attribute) | 2–5% | 50–85% of an *affected name's* volume on reconstitution or inclusion day, nearly all in the close; 15–25% of market-wide close volume on quarterly rebalance days | **Forced** by mandate |
| Active managers (mutual funds, separate accounts) | ~35–40% (attribute) | ~15%, half their share of a decade ago | 20–25% on period-end sessions and redemption waves | Discretionary, mechanical at the edges |
| Hedge funds | 3–5% | ~15% (platforms ~5%, single-manager ~2%, quant the rest) | 25–35% in degrossing episodes | Discretionary until a risk limit binds |
| Pensions, endowments, insurers | ~11% (sectors) | 2–3% | 10–15% of the quarter-end closing auction; forced sellers of duration in a liability-driven rate shock | **Forced** at rebalance |
| Foreign investors, private | ~15–16% | 5–8% | 10–15% during currency-hedge rebalancing and stress repatriation | Discretionary, FX-mechanical |
| Foreign official / sovereign | ~2% | <1% | Rare, large, announced | Policy-driven |
| Corporates (buybacks) | net buyer, not a holder | 3–4% (~$925B authorized in 1H 2026, a record pace) | 5–8% on drawdown days outside blackouts; **zero** inside them | **Forced** by schedule within windows |
| Options dealers | ~0 net, large gross hedge books | scales with gamma; market makers are ~49% of *options* volume | Dominant in the final hour on expiry and pin days | **Forced** by delta |
| HFT / electronic market makers | ~0 | 50–60% | 70–75% by count on the most volatile sessions, while providing *less* liquidity per trade | Liquidity-providing; their withdrawal is the event |
| CTAs / trend followers | $300–350B AUM, mostly futures | small in cash, material in index futures | 10–20% of index-futures volume after a trend-flip level breaks | **Forced** by rule |
| Vol-control / risk parity | $400–600B AUM (estimates disagree by half) | near zero | 10–20% of index-product volume 1–5 sessions after a realized-vol spike | **Forced** by mandate |
| Leveraged / inverse ETFs | $100–150B | 1–2% of close volume | 5–10% of close volume on a ±3% index day | **Forced** by prospectus |
| Short sellers | 1.5–2% of index cap | embedded in the rows above | 30–50% of a squeezed name's volume during forced covering | Discretionary until the borrow says otherwise |

The ratio between the two volume columns is each participant's *forcing multiple* — how much larger its footprint becomes on the day its rule binds — and it is the reason the calendar in Part III exists: for most rows, the heightened day is a date the system can know in advance.

Every figure in Tables A–C is a range and a snapshot, drawn from flow-of-funds data, exchange and wholesaler disclosures, industry-association statistics, and the academic literature on passive ownership. The registry carries them as `observation_type: inferred` with a review date, and the heightened column is the least well-documented of the three: stress-day attribution comes from episode studies and auction statistics rather than any standing series, and it is to be replaced by the system's own closing-auction sampler readings as those accumulate.

**Table D — the cross-tabulation: WHO × HOW, estimated.** Tables A, B and C describe three different axes — legal owner, management mandate, trading behavior — as three separate lists, which leaves the reader unable to see where a row of one lands in a column of another. This table crosses the first two: rows are the owner sectors of Table A, columns are the mandate types of Table B, and each cell is the estimated share of the total U.S. equity market held by that owner under that mandate. **Rows sum to Table A; columns sum to a mandate breakdown that is itself 100%.** Every cell is an estimate and is carried in the claims registry as `inferred` with a review date.

| Owner (rows sum to A) ↓ · Mandate → | Passive / index | Active professional | Self-directed | Hedge funds | Official / sovereign | Systematic rule-driven | Market-maker inventory | **Row total** |
|---|---|---|---|---|---|---|---|---|
| Households, direct | — | 7 (advised SMAs) | **27** | **4** | — | — | — | **38** |
| Mutual funds | **10** | **10** | — | — | — | — | — | **20** |
| Foreign | 8 | 8 | — | — | 2 | — | — | **18** |
| ETFs | 8.5 | 0.2 | — | — | — | 0.3 (leveraged/inverse) | — | **9** |
| Pensions | 6 | 2.5 | — | — | — | 0.5 (risk parity, vol targets) | — | **9** |
| Other (broker-dealers, banks, closed-end) | — | 3 | — | — | — | — | 1 | **4** |
| Insurers | 0.5 | 1.5 | — | — | — | — | — | **2** |
| **Column total** | **33** | **32** | **27** | **4** | **2** | **~1.5** | **1** | **~100** |

*Source class: inferred, mid-2026; the row totals are the Federal Reserve's, the column totals are consistent with the passive-ownership literature and industry flow data, and the cells are the paper's allocation of the one to the other. The systematic column understates the *futures* footprint of CTAs and vol-control strategies, which own little cash equity and much index exposure — see Table C.*

**The third layer — what forces each mandate to trade.** The diagram adds it. Owners on the left, mandates in the middle, forcing mechanisms on the right; ribbon width is share of the market.

*[Figure — owner → mandate → forcing-mechanism diagram; rendered in the HTML edition]*

Four things the cross-tabulation makes visible that the three lists could not.

*Passive is not a sector; it is a third of every large sector.* Mutual funds are half passive, ETFs almost entirely, pensions two-thirds, foreign holders nearly half. The index-event forcing mechanism therefore reaches into every owner row at once — which is why reconstitution day is the year's largest close regardless of who owns what.

*Self-directed households are the largest single cell in the table, and the only large cell with an attention-driven forcing mechanism.* Twenty-seven percent of the market responds to velocity of attention rather than to a rule or a mandate. That cell, and the retail-attention data of Part 29.3, is why the paper treats attention as a flow variable.

*Hedge funds are four percent of ownership and fifteen percent of the tape* — the ratio between their cell in this table and their row in Table C is the paper's forcing-multiple concept in a single comparison. Ownership share measures presence; volume share measures activity; the gap is turnover, and the degrossing mechanism is what turns it into forced flow.

*The systematic column is tiny in cash equity and large in derivatives.* CTAs, vol-control and risk-parity strategies together hold perhaps a percent and a half of listed shares directly and control several times that through index futures. **The cross-tabulation measures the cash market; the forcing mechanisms that matter most for intraday flow sit in a derivative layer above it** — dealers hedging option books, systematic funds resizing futures — that owns almost no equity and moves a great deal of it. Table C's rows for those participants, and *The Dealer's Hand*, are that layer.

Three readings of the table carry into the rest of the paper.

*Ownership is concentrated in slow money; volume is concentrated in fast money.* Households, passive funds, active managers, and pensions own roughly nine-tenths of the market and transact a minority of the tape on an ordinary day. Market makers, retail traders, and hedge funds are the majority of the tape and a small share of the ownership. Forced flow is the moment slow money is made to behave like fast money — a pension at quarter-end, a passive fund on reconstitution day — and the tape's capacity to absorb it is set by the fast money's willingness to take the other side.

*Retail has doubled its share of the tape in two years and is now the single largest discretionary participant by volume.* The 2026 figures are records: a third of daily equity volume, a record pace of options premium, and buy-the-dip behavior measured at several times the average on down days. The paper's retail sections treat this as a structural fact rather than a sentiment reading: when a third of volume is attention-driven, attention velocity is a flow variable.

*The largest net buyer of U.S. equities is the issuers themselves.* Corporate repurchases run near a trillion dollars a year; the buyback bid is the price-insensitive demand that the Equities paper describes and this paper places on the calendar, and its withdrawal in blackout windows is a scheduled absence of demand that the closing-auction module reads directly.

The mechanical holders that the numbered sections describe are the rows marked *forced*. The discretionary rows — hedge funds, active managers, foreign private investors — appear in Section 2.12 for their *mechanical failure modes*: the moments when a risk limit, a redemption, or a currency hedge converts a discretionary holder into a forced one.

### 2.1 Options dealers (intraday to monthly)

**The rule.** Market makers hedge the delta of their option books continuously, and the sign and size of the hedge depend on the gamma, vanna and charm of the book against spot, volatility and time. *The Dealer's Hand* derives the mechanics; this paper records only what the flow looks like from outside. In a positive-gamma regime dealers buy dips and sell rallies, dampening moves and producing pins near large open-interest strikes. In a negative-gamma regime they sell dips and buy rallies, amplifying moves. Charm flow — the decay of delta as expiry approaches — produces a systematic, calendar-driven hedge unwind concentrated in the last days before an expiry; vanna flow links a volatility crush to spot buying.

**Observability.** Inferred, not observed. The book's exposure engine computes dealer gamma, delta, vanna and charm from public open interest under the standard signing assumption, and the registry records every one of those twenty-eight metrics as `observation_type: inferred` — "wrong in a way arithmetic cannot be," in the architecture's phrase — because public chains cannot see which side of a trade the dealer is on. The vendor cross-check validated the arithmetic (walls matching to the strike) but cannot validate the assumption.

**The system's data.** The exposure engine's four Greeks by four expiry buckets, the dated **expiration-release ladder** (how much dealer delta unwinds at each coming expiry — the most directly tradeable forced flow the system computes), the pin log, and the intraday cadence's 0DTE structure at 09:45. All built.

### 2.2 Leveraged and inverse ETFs (daily, at the close)

**The rule.** A leveraged ETF promising *L* times the daily return of an index must rebalance at each close to restore its leverage. The rebalance notional is exact:

> Rebalance = (L² − L) × AUM × r

where *r* is the day's index return. For a 2× fund the factor is 2; for a 3× fund it is 6; for a −1× inverse it is also 2, and *in the same direction* as the leveraged long — leveraged and inverse funds both buy on up days and sell on down days. The flow is always in the direction of the day's move, always at the close, and larger when the move is larger. A 3% down day across the major leveraged equity complex produces a mechanical sell program into the auction in the billions.

**Observability.** Inferable to within the AUM estimate, which is public daily for listed funds. This is the one mechanical flow the system can compute almost exactly and in advance — by 15:50 the day's return is nearly known and the rebalance size follows.

**The system's data.** Leveraged-ETF AUM by underlying index (a small table, refreshed weekly), the day's return at 15:50, and the closing-auction sampler that observes the resulting imbalance. Not yet built; specified in Part V as the first flow model because it is the cleanest.

### 2.3 Volatility-targeting and vol-control strategies (days to weeks)

**The rule.** A fund targeting a fixed portfolio volatility sizes its equity exposure inversely to realized volatility: exposure = min(cap, σ_target ÷ σ_realized). When realized volatility rises, the fund sells until the target is restored; when it falls, the fund buys. The flow lags the volatility move by the fund's lookback (commonly one to three months, sometimes with a short-window overlay), so a spike in realized volatility produces selling that continues for days as the trailing window absorbs the spike, and a quiet period produces buying that continues as the spike rolls out. Risk-parity funds behave similarly with an additional rebalance on correlation.

**Observability.** Inferred. Aggregate vol-control AUM is a research estimate, not a published figure, and it is the parameter this model is most uncertain about. The paper's rule is that the *direction and timing* of the flow are reliable (they follow from the formula and the realized-volatility series, both computable), while the *magnitude* carries a stated uncertainty band and is never presented as a single number.

**The system's data.** Realized volatility at the standard lookbacks from stored prices; the model's exposure path; a declared AUM assumption with its band. Specified in Part V; not yet built.

### 2.4 Trend followers and CTAs (days to months)

**The rule.** Systematic trend funds hold positions whose sign is set by a trend signal — a moving-average relationship, a breakout, a time-series momentum measure — over several lookbacks, and they add or cut as the signal strengthens or reverses. Their flow is *triggered* rather than scheduled: it occurs when price crosses the level at which the aggregate signal flips. Because the signals are standard and the lookbacks are conventional, the levels can be estimated, and *The Technical Indicators* paper's systematic-trigger levels are exactly this estimate.

**Observability.** Inferred; the trigger levels are computable, the positioning at any moment is estimated from the signal state, and the AUM is a research figure. As with vol-control, direction and timing are the reliable part.

**The system's data.** The Technical Indicators paper's trigger levels for the index and major futures, a signal-state estimate per lookback, and — as the confirming observation — COT positioning of leveraged funds in the relevant futures, which is the closest public measurement of what CTAs actually hold. Trigger levels exist in the Technical Indicators work; the flow model is specified in Part V.

### 2.5 Index funds and index committees (quarterly, with announced dates)

**The rule.** Index inclusion, exclusion and reweighting force every fund tracking the index to trade the change at the effective close. The dates are published: S&P's quarterly rebalance at the third Friday of March, June, September and December (coinciding with quarterly options expiry — the "triple witching" close is the largest auction of the quarter); the Russell reconstitution at the end of June, with its preliminary lists published from May; Nasdaq-100's annual reconstitution in December with quarterly share adjustments; MSCI's semi-annual reviews. Additions are announced days to weeks ahead and the passive buy is concentrated at one close.

**Observability.** Announced, with the flow size computable from the index weight and the tracking AUM. This is the most public flow in the market and therefore the most thoroughly front-run; the paper's interest in it is the *absorption* reading (Part IV) and the interaction with dealer positioning at the witching close, not the naïve inclusion trade.

**The system's data.** The forward calendar (Session 9) carrying every index event with its expected flow direction; the closing-auction sampler observing the event-day auction; the event-classification table that labels the day so that its imbalance is never read as discretionary. The calendar is planned; the classification table is admitted in Change Order #3.

### 2.6 Month-end and quarter-end rebalancing (calendar)

**The rule.** Balanced mandates — pensions, target-date funds, sovereign funds, 60/40 portfolios — rebalance to policy weights at period ends. When equities have outperformed bonds in the period, they sell equities and buy bonds; the flow's direction is the *sign of the relative return*, and its size scales with the magnitude of the relative move and the rebalancing AUM. The flow is concentrated in the last two or three sessions of the month and the quarter, and the quarter-end flow is larger.

**Observability.** Inferable in direction from public returns; the magnitude is a research estimate with wide bands, and the timing within the window varies by mandate. The paper's practical use (Part IV) is the *surprise* — expected rebalance pressure versus observed closing-auction pressure — rather than the level.

**The system's data.** Equity-bond relative return over the period from stored prices; a declared rebalancing-AUM assumption with its band; the auction sampler on the last sessions. Specified in Part V.

### 2.7 Corporate buybacks (earnings-cycle calendar)

**The rule.** Companies repurchasing shares are the largest single source of net equity demand in most years, and the flow has a calendar: most firms suspend discretionary repurchases in a blackout window that begins roughly two weeks before quarter-end and runs until a day or two after the earnings release, then resume. The corporate bid is therefore absent for a predictable stretch each quarter — the stretch that includes the quarter-end rebalance and the first weeks of earnings season — and returns in a wave afterward. Announced authorizations are public; execution pace within an authorization is not.

**Observability.** The blackout calendar is inferable from the earnings calendar (which the events layer already tracks); authorizations are announced; execution is hidden until the quarterly filing. *Equities* (Companion XV) treats buybacks as an earnings-cycle input; this paper treats them as a flow with an absence window.

**The system's data.** The earnings calendar from events ingest; the derived blackout window per name and in aggregate; announced authorizations from filings. The window is computable now from Session 8's events; aggregate execution estimates are Part V.

### 2.8 Positioning surveys and reports (weekly to quarterly, lagged)

**The rule.** These are not flows; they are *stocks* — snapshots of what a class of participant holds — and they matter because a crowded position is a flow waiting for a trigger. The CFTC's Commitments of Traders report gives futures positioning by trader class (the Traders in Financial Futures breakdown separates leveraged funds from asset managers), published Fridays for the prior Tuesday. 13F filings give institutional equity holdings quarterly, forty-five days after quarter-end. FINRA's short-interest report gives outstanding shorts twice monthly. Survey series — AAII, NAAIM, Investors Intelligence — give stated sentiment weekly.

**Observability.** Observed, lagged, and partial. The paper's treatment (Part VI) is entirely about not misreading them: positioning is a level, the flow is its change, and extremes matter only with a catalyst.

**The system's data.** COT TFF for JPY (inside the yen monitor's state machine), for equity-index futures (the CTA confirmation), and for Treasuries; FINRA short interest and daily short volume (with the registry encoding that the two are not the same thing); the sentiment surveys from Sessions 16–17. COT for JPY is planned with Session 16; the rest are scheduled.

### 2.9 Retail (daily, attention-driven)

**The rule.** Retail is not mechanical in the sense above — it has views, loudly — but its *aggregate* behavior has become measurable and regime-like: attention concentrates in a small number of names, persists for days, and produces flows in single names and in the options market (small-lot call buying) that dealers must hedge, which converts retail attention into a dealer flow. The meme lifecycle (Change Order #3's state machine) is the formalization.

**Observability.** Partially observed. Nasdaq's retail-activity series gives the top ten names by retail dollar share daily with a ten-year history — the rare positioning source with a record — and its registry entry carries `sample: top10_censored` so that no one reads the head of the distribution as its breadth. Attention velocity comes from aggregated social data; borrow conditions from the broker.

**The system's data.** RTAT10 with its derived concentration, persistence and new-entrant metrics; the meme lifecycle classifier; IBKR borrow series. Admitted in Change Order #3; the retail fetcher is the first item in its build order.

### 2.10 Forced sellers (event-driven, the tail's domain)

**The rule.** The category the tail scenarios are written about: participants selling because they must, not because they choose — margin calls, deleveraging of a funded trade when its funding currency moves, liquidation cascades in leveraged crypto positions, fund redemptions, lock-up expiries releasing a supply overhang. Each has a known mechanism and an unknown trigger.

**Observability.** The *vulnerability* is often visible (crowded yen shorts in COT; open interest and funding rates in crypto; the unlock calendar of a mega-IPO); the *trigger* is not. The paper's tools here are the vulnerability measures and the absorption reading once the flow begins.

**The system's data.** The yen carry stress monitor (Change Order #3, 29.1: a four-state regime machine escalated by independent mechanism groups, with COT positioning as one vote); the SPCX and ASTS overhang trackers (the single-name overhang pattern already in the Daily); crypto liquidation data in *Alternative Assets*' domain. The yen monitor and the overhang trackers are specified; the liquidation feed is in Alt Asset's plan.

### 2.12 Discretionary holders and their mechanical failure modes

The paper's premise is obligation, and hedge funds, active managers, insurers, and foreign investors are not obligated holders in the ordinary course. Each, however, has a state in which its behavior becomes as mechanical as a leveraged ETF's, and those states are where the discretionary rows of the participant map matter to this paper.

**Multi-strategy platforms — degrossing.** The largest hedge-fund complexes run many independent portfolio-manager "pods" under a central risk system with hard limits on drawdown, factor exposure, and gross leverage. When a pod breaches its limit it is cut, not consulted; when several breach at once — because they were crowded into the same factor or the same names — the platform reduces gross exposure across the book, selling longs and covering shorts in whatever is most liquid. The flow is mechanical once triggered, it is factor-shaped rather than name-shaped, and it is the modern form of the 2007 "quant quake." Observability: inferred, from crowding measures (prime-broker positioning surveys, factor-crowding indices, the concentration of hedge-fund ownership in 13F data) and from the tape's signature — simultaneous, sharp moves in crowded longs and crowded shorts in opposite directions with the index barely moving. Rights: a flag for the Confirmation block when the signature appears; never a magnitude.

**Active managers — redemptions and the benchmark.** Mutual-fund redemptions force selling of holdings pro rata or of the most liquid names, on a settlement clock; large flows are visible in industry flow data with a lag of days. The benchmark imposes a second mechanism: a manager far from the index into a period-end has an incentive to close the gap — "window dressing" — which produces period-end demand for the names that outperformed and supply of those that lagged, in the same auctions as the pension rebalance and in the opposite direction from it. Observability: flows observed with a lag; window dressing inferred from period-end auction signatures.

**Insurers and liability-driven investors — the rate shock.** Insurers and defined-benefit pensions match long-dated liabilities with long-duration assets, and a sharp move in long rates changes both sides at once. When the move is large enough, the collateral calls on hedging derivatives force asset sales — the 2022 U.K. liability-driven-investment episode, in which pension funds were forced sellers of the very gilts whose fall had triggered the calls, is the reference case, and the mechanism is not peculiar to Britain. For this operator, whose professional domain is the insurance balance sheet, the reading is direct: a fast move in long rates is a forced-flow event for the largest slow-money holders, and the Rate and Liquidity Machine's duration-supply work is where the system watches for it. Observability: the rate move is observed; the forced sales are inferred from bond-market signatures (long-end dislocation exceeding what the move in expectations implies) and, with a lag, from disclosures.

**Foreign private investors — the currency hedge.** A foreign holder of U.S. equities who hedges the currency must rebalance the hedge as the equity position's value changes; a rally increases the required hedge, a decline reduces it, and the rebalancing is a mechanical flow in the currency market at period-ends. Under funding-currency stress the mechanism runs in reverse and faster: holders who financed U.S. assets in a low-yielding currency repatriate when that currency appreciates against them, and the repatriation is a forced sale of the asset and a forced purchase of the currency. Observability: hedge-ratio surveys are periodic and lagged; the stress version is observed in the currency's velocity and in the positioning data the yen monitor consumes.

**Market makers — the withdrawal.** The one participant whose *absence* is the forced event. Electronic market makers provide the liquidity that absorbs every other holder's flow, subject to inventory limits and volatility thresholds; when volatility exceeds their models' tolerance they widen or withdraw, and the same forced flow that was absorbed at ten basis points is absorbed at seventy. This is what the paper's absorption measurement detects, and it is why the measurement is more informative than the flow: it is a direct reading of whether the liquidity providers are present. Observability: observed, in the tape, through absorption; and in depth-of-book data where subscribed.

**Sovereign and official holders — the announcement.** Reserve managers and sovereign funds move rarely and in size, on policy decisions that are announced or leak; their flows are the tail watch's domain rather than the daily's, and the paper records them for completeness.

The paper's rule for the discretionary rows follows from the map: they enter the reading only through their *failure-mode signatures* — the degrossing pattern, the redemption wave, the collateral-call dislocation, the hedge rebalance, the liquidity withdrawal — each of which is a mechanism group that votes once, and none of which is a magnitude the reports may print.

### 2.13 The closing auction: where the flows meet

Most of the flows above — leveraged-ETF rebalances, index reconstitutions, month-end rebalancing, a large share of institutional program trading, and dealer hedges of expiring options — execute in the closing auction. The auction is therefore the *observable aggregate* of mechanical flow, and the imbalance feed (NYSE-family through the broker, admitted in Change Order #3 with a 15:50–16:00 sampler) is the closest thing the system has to a direct reading of forced flow. It is also the natural confluence partner for dealer positioning: gamma says how the close *reacts*; the imbalance says what *pushes* it. The two are independent mechanisms — one of the few pairs in this paper that genuinely counts as two votes.

---

## Part III — The Calendars

### 3.1 The master calendar

The forward calendar (Session 9) carries every dated flow with its expected direction, and the event-classification table beside the exchange-holiday table labels every session so that a flow is read in its context. The recurring entries:

| Cadence | Event | Flow | Direction rule |
|---|---|---|---|
| Daily | Leveraged-ETF rebalance | Close | With the day's move |
| Daily | 0DTE expiry | Session | Charm unwind into the close; pin near dominant strike |
| Weekly (Fri) | Weekly options expiry | Close | Charm unwind; DEX release per the ladder |
| Weekly (Fri) | COT release | 15:30 ET | Not a flow — a positioning update |
| Monthly (3rd Fri) | Monthly options expiry | Close | Largest DEX release of the month; pin regime resets Monday |
| Monthly (last 2–3 sessions) | Month-end rebalance | Close | Against the period's equity-bond relative return |
| Quarterly (3rd Fri Mar/Jun/Sep/Dec) | Triple witching + S&P rebalance | Close | Largest auction of the quarter; index reweights + expiry release |
| Quarterly (last sessions) | Quarter-end rebalance | Close | Against the quarter's relative return; larger than month-end |
| Quarterly | Buyback blackout | ~2 weeks pre-quarter-end through earnings + 2 days | Corporate bid absent, then returns |
| Quarterly (45 days after) | 13F filings | — | Positioning update, lagged |
| Annual (late June) | Russell reconstitution | Close | Largest single-name passive flow of the year |
| Annual (December) | Nasdaq-100 reconstitution | Close | Concentrated in additions/deletions |
| Semi-annual (May/Nov) | MSCI reviews | Close | Global passive flows |
| Event | Index inclusion (announced) | Effective close | Passive buy of the added name |
| Event | Lock-up expiry | Date | Supply overhang release |
| Event | FOMC / CPI / payrolls | Session | Vol-control repricing follows realized-vol response |

### 3.2 How the system uses the calendar

Three uses, in ascending order of value. **Labeling:** every session carries its classification, so the closing-auction sampler never records a reconstitution-day imbalance as discretionary flow — a Russell-day sell imbalance and an ordinary-Tuesday sell imbalance are different objects, and the register's signal-rights rules treat them differently. **Expectation:** for the flows with computable direction and size (leveraged ETFs exactly; month-end and index events approximately), the calendar carries the *expected* flow, so that the observed auction can be read as a surprise against it (Part IV). **Staging:** the doctrine's Sunday session reads the coming week's calendar and stages Book B and C packets around it — not to trade the flow directly, but to know which sessions' price action is mechanical and which is informational.

### 3.3 The clock inside the day

Two flows have intraday structure the book's cadence is timed to. The **0DTE structure** is built in the opening hour and captured at 09:45; the charm flow it produces accelerates into the last ninety minutes; and the *Dealer's Hand*'s finding that pins are strongest in the final hour is the reason the settled 16:10 capture, not an intraday one, grades the pin log. The **closing-auction imbalance** publishes from 15:50 and evolves to the bell; the sampler's thirty-second cadence exists because the *shape* of that evolution — accelerating or absorbed — is the information, not the final print.

---

## Part IV — Absorption: Response per Unit of Stimulus

### 4.1 The measurement

For any flow with a measurable pressure *P* and a measurable price response *R* over a window *w*:

> absorption = R ÷ P, compared against a declared baseline of the same ratio

with a *deterioration flag* when the ratio moves away from baseline in the direction that means the market is failing to absorb — more price per unit of pressure. The primitive is generic; Change Order #3 specifies it once (`response_ratio`) and four signals call it. What differs by signal is the choice of *P*, *R*, *w*, and the baseline. The paper's rule for each: *P* must be a flow the system can measure or compute, not a level; *R* must be measured at the horizon the flow acts on; the baseline is the ratio's own history, percentile-ranked, never a fixed number.

### 4.2 Worked example — the closing auction

At 15:50 the sampler reads a $600 million sell imbalance in SPY's auction and an indicative price 3 basis points below the last continuous trade. At 15:55, $1.0 billion and 5 basis points. At 15:58, $1.7 billion and 8 basis points. The imbalance is accelerating; the price is barely moving. **Absorption is high**: a forced or rebalancing seller is meeting deep latent demand. Compare the same imbalance path with an indicative price at −40, −55, −70 basis points: **absorption is low**; the seller is moving the market, and the participants who would ordinarily take the other side are absent. The headline — "$1.7 billion sell imbalance" — is identical. The information is opposite.

The two readings map to two registered hypotheses (Change Order #3, 29.4): *Absorption Reversal* — fade an extreme, well-absorbed imbalance, on the reading that the pressure is temporary and the demand is real; and *Pressure Continuation* — follow an extreme, poorly absorbed imbalance confirmed by futures, volatility and breadth, on the reading that this is real risk reduction. Both are hypotheses, graded through the register against six months of sampler history before either is a setup. The paper's own prior is that the reversal case is the more robust, because well-absorbed forced selling is the cleanest instance of the family's premise — the counterparty is not trying to win — but it is a prior, and the register will say.

### 4.3 Worked example — the yen

The yen carry stress monitor's premise is that a yen move is dangerous in proportion to the positioning it hits, and its state machine escalates on independent groups. Absorption enters as the relationship between the FX-velocity group and the risk-asset group: USDJPY down 4% over five sessions with leveraged funds at a 90th-percentile short is the *pressure*; the *response* is what equities, credit and volatility do per unit of that pressure. In early August 2024 the response was large — a 12% Nikkei session, a VIX spike into the sixties intraday, credit widening — and the monitor's design would have read SYSTEMIC. A comparable yen move in a period with neutral positioning and a muted risk-asset response reads ELEVATED at most. The monitor's rule that a large USDJPY move is "much more dangerous when JPY shorts are in the 85th–95th percentile" is an absorption statement: crowded positioning is the condition under which the market cannot absorb the move.

### 4.4 Worked example — the leveraged-ETF rebalance

The one flow the system computes in advance. At 15:50 on a day the Nasdaq-100 is down 2.5%, the leveraged complex on that index must sell (L² − L) × AUM × r: for the 3× funds, 6 × AUM × 2.5%; for the 2× and −1× funds, 2 × AUM × 2.5%. Summed across the listed funds' AUM, the expected sell program is a dollar figure, and it will appear in the closing auction. The absorption reading is then *expected mechanical sell* against *observed imbalance and indicative price*: an observed imbalance close to the expected program with little price displacement says the flow was anticipated and absorbed; an observed imbalance far larger than the program says discretionary sellers joined it; a price displacement out of proportion to the program says liquidity is thin. Because the pressure is computed rather than estimated, this is the cleanest absorption measurement the system can make, and the paper recommends it as the first flow model built.

### 4.5 Worked example — index inclusion

An inclusion announced two weeks ahead produces a known passive buy at the effective close. The interesting measurement is not the close itself but the *path*: how much of the eventual passive demand is pre-positioned by arbitrageurs (visible as the name's outperformance from announcement to effective date), and how the effective-day auction absorbs the residual. A name that ran 8% into inclusion and prints a small auction with little displacement was fully pre-positioned — the flow is spent, and the post-inclusion drift tends to be negative as arbitrageurs exit. A name that ran little and prints a large, poorly absorbed auction was under-anticipated. The reading tells the book which side of the post-event drift to expect, and it is the version of the inclusion trade that is not already priced.

### 4.6 The deterioration flag as the general signal

Across the four examples the flag is the same: the ratio of response to stimulus moving away from its baseline in the direction of *less absorption* — more price per unit of forced flow, more equity damage per unit of yen move, more auction displacement per dollar of program. The Speculative Cohort monitor uses the same primitive in the other direction (price velocity rising while revision velocity falls — response outrunning stimulus); the meme lifecycle uses it for exhaustion (price failing to respond to rising attention). One computation, six callers, and the paper's claim that it is the organizing idea of positioning analysis: **the flows tell you who must move; the absorption tells you who is there to meet them.**

---

## Part V — Estimating the Flows You Cannot See

### 5.1 The honesty rule for inferred flows

Every model in this part produces an `observation_type: inferred` metric. The rule is that direction and timing are stated plainly where they follow from public formulas and public inputs, magnitude carries an explicit uncertainty band whenever an AUM or participation assumption enters, and no inferred flow is ever presented as a single number without its band. The architecture's registry enforces the first part (the type field); the report renderer enforces the second (bands render or the row is GAP).

### 5.2 Model 1 — Leveraged-ETF rebalance (exact to the AUM)

Inputs: a table of leveraged and inverse ETFs by underlying index with leverage factor and daily AUM; the underlying's return at 15:50. Output: expected rebalance notional by underlying, signed with the day's move. Uncertainty: the AUM is end-of-prior-day and the return is ten minutes early; both are small. Registry: `flow.letf_rebalance_expected`, session half-life, intraday horizon, mechanism group `passive_calendar`. Consumer: the closing-auction sampler's expected-flow line; the Daily's Into-the-Close run. Build: small; first in order.

### 5.3 Model 2 — Vol-control exposure path (direction reliable, magnitude banded)

Inputs: realized volatility of the index at 1-month and 3-month lookbacks from stored prices; a target-volatility assumption (commonly 10–12% for the largest such mandates); a declared AUM assumption with a wide band. Output: the model's exposure path — exposure = min(cap, target ÷ realized) — and its day-over-day change, which is the flow's direction and relative size; the dollar magnitude is the change times the AUM band. Registry: `flow.volcontrol_exposure` (inferred, weekly horizon, half-life session), mechanism group `systematic_flow_inferred`. Consumer: the Weekly's flow state; the T&B's crowding read (a fully-invested vol-control complex is a vulnerability). The paper's caution: the model's value is in *turning points* — the days the exposure path flips from rising to falling after a volatility spike — not in the level, which no one can verify.

### 5.4 Model 3 — CTA trend state (direction reliable, triggers computable)

Inputs: the Technical Indicators paper's trigger levels on the index and major futures at the conventional lookbacks; current price; COT leveraged-fund positioning as the confirming observation. Output: an aggregate trend-signal state (long / flat / short by lookback), the distance from price to the nearest flip level, and the estimated flow if it is crossed (signed; magnitude banded by the AUM assumption). Registry: `flow.cta_state`, `flow.cta_trigger_distance` (inferred, swing horizon), mechanism group `systematic_flow_inferred` — the *same* group as vol-control, deliberately: both are systematic de-risking mechanisms and they count once together. Consumer: the Daily's Confirmation block (a trigger level within a day's range is a known pressure point), Book B's entry timing (the doctrine's "breakouts distrusted in positive gamma; trusted in negative gamma" rule interacts with whether a breakout crosses a CTA level).

### 5.5 Model 4 — Month-end rebalance expectation (surprise is the signal)

Inputs: equity-bond relative return over the period from stored prices; a rebalancing-AUM assumption with a wide band; the calendar. Output: expected direction and a banded magnitude for the last sessions of the period, then — from the sampler — the *observed* auction pressure, and the difference. Registry: `flow.rebalance_expected`, `flow.rebalance_surprise` (inferred; the surprise is calculated from an observed and an inferred input and carries the inferred type). Mechanism group `passive_calendar`. Consumer: the Weekly at month-end; the T&B's flow overlay. The paper's use: a month in which equities beat bonds by a wide margin and the month-end auction shows *no* sell pressure is a month in which the rebalancers had already sold, or in which discretionary buyers absorbed them — either way a fact worth the Weekly's attention.

### 5.6 Model 5 — Buyback window (absence is the signal)

Inputs: the earnings calendar from events ingest; announced authorizations from filings. Output: per-name and aggregate blackout state (in window / open), and a rough intensity estimate from authorizations and the prior quarter's filed execution. Registry: `flow.buyback_window` (calculated from the calendar — this one is not inferred), `flow.buyback_intensity` (inferred). Mechanism group `passive_calendar`. Consumer: *Equities*' earnings-cycle logic; the T&B's demand overlay. The paper's use is the corporate bid's *absence*: a market that holds its levels through the blackout has demand from elsewhere; one that sags into the blackout and recovers on its lifting is being carried by the corporate bid, which is a statement about fragility.

### 5.7 Model 6 — Dealer expiration release (built)

The exposure engine's DEX release ladder already produces the dated, per-expiry dealer-delta unwind — the one flow model that is built, bucketed, and in the pin log. The paper records it here for completeness and for the independence rule: it belongs to mechanism group `dealer_chain_derived`, and it does not vote with the systematic or passive groups.

---

## Part VI — Reading Positioning Without Misreading It

### 6.1 Levels, changes, and the crowded-plus-catalyst rule

The commonest error in retail use of positioning data is to treat a level as a signal: "speculators are record short the yen, therefore buy the yen." The record short was in place for months before August 2024 and was profitable throughout; the level was not the signal. The *change* — the pace at which the short was being covered once the yen moved — was, and so was the *catalyst* that started the covering. The paper's rule, adopted from the yen monitor's design: **an extreme positioning level is a vulnerability, not a signal. It becomes a signal when a catalyst arrives, and its size is read as the amount of forced flow the catalyst can release.** The registry carries positioning levels with `half_life` weekly and a rights entry that permits them to *condition* (size, stop discipline, tail state) and never to trigger.

### 6.2 Percentiles against own history, never fixed thresholds

Positioning series drift: contract sizes change, participants enter and exit, reporting definitions are revised. A fixed threshold ("net short more than 100,000 contracts") ages badly. Every positioning metric in the registry is read as a percentile against its own three- and five-year history, with the raw level shown beside it. The standard derived forms — level, percentile, z-score, four-week change, change-of-change — are computed by the generic function Change Order #3's Part 30.8 specifies, so that every positioning row in every report reads the same way.

### 6.3 COT specifics

The Commitments of Traders report's Traders in Financial Futures breakdown is the one to read for financial contracts, and *leveraged funds* is the class that matters for the flows in this paper — the hedge funds and CTAs whose positioning is most likely to be unwound mechanically. *Asset managers* are the structural side, slow to move and often positioned opposite; the *spread* between the two classes is frequently more informative than either level. The report is Friday-published for Tuesday positions, a three-day lag that matters in a fast unwind: by the time the August 2024 covering appeared in COT, most of it had happened. The paper's rule: COT positions the *vulnerability* reading a week ahead; it does not time the unwind, and the monitor's FX-velocity group is what does.

### 6.4 Short interest: two series that are not the same

FINRA's semi-monthly short-interest report is a *position*: shares sold short and not yet covered, as of a settlement date, published roughly nine business days later. FINRA's daily short-sale volume is an *activity* count: shares sold short that day through reporting facilities, most of which are covered intraday by market makers. The second is not a proxy for the first, and FINRA says so. The registry encodes both with the relationship stated: short interest for the crowding level (the vulnerability), daily short volume for the activity pulse (a fast but noisy tell), and the broker's borrow data — cost-to-borrow and availability, through the Gateway — for the *tradability* reading that neither FINRA series gives. For the meme lifecycle, the change in borrow conditions is more informative than the level of short interest: a stable 25% short with 3% borrow is crowded and manageable; the same 25% with borrow rising from 8% to 45% and availability collapsing is a squeeze in progress.

### 6.5 13F: the lag makes it structural

Forty-five days after quarter-end, a 13F describes positions that may no longer exist. The paper's use is therefore structural and slow: concentration of institutional ownership in a name or a factor, quarter-on-quarter changes in aggregate exposure, and — for the Speculative Cohort — whether the holders of a momentum name are the kind that rebalance mechanically (index and quant) or the kind that decide (discretionary). Session 19's institutional-versus-retail divergence is built on this series against RTAT's retail share, and it is a quarterly reading by construction.

### 6.6 Surveys: sentiment is context

AAII, NAAIM and Investors Intelligence are stated attitudes, not positions, and the doctrine's regime card lists sentiment as context rather than a vote. The paper agrees and adds one use: the *divergence* between stated sentiment and measured positioning (bullish surveys with falling NAAIM exposure; bearish surveys with rising leveraged-fund longs) is occasionally informative, and it is a divergence the standard derived forms make easy to compute.

### 6.7 Retail: reading a censored sample

RTAT10's ten names are the head of a distribution of nine and a half thousand. Concentration measured on the head is concentration of the head; persistence and new-entrant shock are exactly right on the head, because the head is where manias live; but "retail breadth" from ten names is not breadth. The registry flag exists so the reports say so. The series' compensating virtue is its decade of history: the derived signals can be backtested against 2021 and 2022 before they are trusted — the only positioning series in this paper for which that sentence is true.

---

## Part VII — Wiring: Reports, Books, and the Independence Table

### 7.1 Mechanism groups (the units that vote)

| Group | Members | Observation type | Native horizon |
|---|---|---|---|
| `dealer_chain_derived` | GEX, DEX, VEX, CHEX by bucket; expiration-release ladder; flip, walls | inferred | intraday–monthly |
| `dealer_chain_oi` | max pain, OI shelves, OI put/call | calculated / observed | daily |
| `auction_flow` | imbalance, absorption, acceleration, displacement; ETF-vs-underlying divergence | observed / calculated | intraday, close |
| `systematic_flow_inferred` | vol-control exposure path; CTA state and trigger distance | inferred | swing |
| `passive_calendar` | leveraged-ETF rebalance; month-end expectation and surprise; index events; buyback window | calculated (exact/computed) or inferred (banded) | session–quarterly |
| `positioning_survey` | COT TFF; FINRA short interest; 13F; sentiment surveys | observed, lagged | weekly–quarterly |
| `retail_attention` | RTAT10 derived; attention velocity; borrow conditions | observed (censored) / calculated | intraday–daily |

Seven groups. The confluence rules of the architecture and the doctrine (a full-size setup needs three of four clusters confirming; correlated positions count once) operate on these, not on the forty-odd series inside them. The doctrine's trust matrix gains a row per group, entered at Low or Medium with a sample-size requirement; nothing enters at High.

### 7.2 Which report consumes what

| Report | Consumes | As |
|---|---|---|
| **Daily 07:00** | Expiration-release ladder for the day; 0DTE structure (from 09:45 once live); CTA trigger distance; calendar labels for the session; leveraged-ETF expected rebalance | Confirmation block context; setup-list conditions |
| **Daily 15:00 / 16:30** | Auction sampler: imbalance path, absorption, expected-vs-observed | Into-the-Close and Debrief blocks; pin-log companion column |
| **Weekly Reflection** | Vol-control and CTA state changes; month-end expectation/surprise; COT changes; buyback window; RTAT persistence and new entrants | Flow state of the week; candidate-list conditions |
| **Monthly Macro** | COT percentiles by asset; 13F structural reads; rebalance surprises accumulated | Positioning pillar; regime modifiers |
| **Tops & Bottoms** | Breadth of crowding across groups; vol-control exposure at cap; buyback-window fragility; retail concentration and persistence; DAT premia | Cycle-maturity overlays |
| **Tail watch** | Yen monitor state; crypto liquidation vulnerability; lock-up calendar; CTA trigger clusters | First-mover and vulnerability lines per scenario |
| **Alert layer (Book D)** | Meme lifecycle transitions; overhang trackers; absorption hypotheses when they graduate | Opportunistic candidates |

### 7.3 Signal rights

Every metric in this paper is a **conditioner**. It may set size, stop discipline, the choice of expression, the tail-scenario state, and a book's permission to open; it may raise a hedge-review flag; it may never trigger a trade on its own. The three exceptions in the direction of *more* restriction: a CTA trigger level inside a day's expected range forbids a Book C counter-trend entry that session; a vol-control exposure path at its cap in a Rising-volatility regime forces Book A to the lower half of its band ahead of the dial's own reading; and a meme-lifecycle DO_NOT_SHORT flag overrides any short packet in the name regardless of the other signals. Rights are recorded per metric in the registry and enforced by the register's write path.

### 7.4 The factor map for heat

The doctrine's Rule 16 — correlated positions count once at their common factor — needs a factor map, and this paper supplies its first version: every instrument in the book is tagged with the flows it is exposed to (index beta; the leveraged-ETF complex on its index; the CTA signal on its futures; the vol-control complex; the buyback window of its sector; the yen carry for anything funded or correlated). Two Book B semiconductor longs and a Book C NQ call spread share the index-beta factor and the CTA-on-NQ factor; they are one position for heat. The map is a configuration table, reviewed quarterly, and the register's heat calculator (Track D) consumes it.

### 7.5 What each book does with positioning

**Book A** reads positioning as a regime modifier: crowding across the systematic and survey groups moves the stance toward the bottom of its band; a washed-out reading after a forced unwind (COT covering complete, vol-control exposure at its floor, retail concentration collapsed) is the condition under which the T&B bottom signal is most trusted and the stance moves to the top. **Book B** uses CTA trigger distances and dealer-expiry cycles for entry timing — a breakout that also crosses a CTA level in a negative-gamma regime is the doctrine's "trusted breakout"; one that does not is the "wait for the retest" case — and reads positioning extremes as the condition for variant-perception entries. **Book C** consumes the dealer and auction groups almost exclusively: the pin, the flip, the expiration release, and — once the sampler has history — the absorption reading into the close. **Book D** is where the forced-flow trades live: the overhang tracker's unlock dates, the meme lifecycle's phase transitions, an index event's under-anticipated auction, a squeeze exhausting with borrow improving.

---

## Part VIII — Data Status

| Input | Source | Status (6 Sep 2026) | Cost | History |
|---|---|---|---|---|
| Dealer Greeks by bucket, expiration ladder, pin log | Own engine on Massive + yfinance chains | **Built** | $29/mo (Massive) | Forward-only from 4 Sep 2026 — OI has no history at any vendor probed |
| 0DTE structure at 09:45 | Own engine, OPRA real-time via IBKR | Intraday cadence approved; prerequisite (capture-instant T) open | $1.50/mo | Forward-only |
| Closing-auction imbalance path | NYSE/Arca/MKT ticks via IBKR Gateway | Feeds subscribed 5 Sep; probe Tuesday; sampler in Change Order #3 | $3/mo | Forward-only; **Nasdaq Closing Cross is a GAP** |
| Leveraged-ETF rebalance | Own model on public AUM | Specified (Model 1) | — | Computable historically from AUM and returns |
| Vol-control exposure path | Own model on stored prices | Specified (Model 2) | — | Computable; AUM band inferred |
| CTA state and triggers | Technical Indicators levels + own model | Levels exist; model specified (Model 3) | — | Computable |
| Month-end expectation/surprise | Own model + sampler | Specified (Model 4) | — | Expectation computable; surprise forward-only |
| Buyback window | Events ingest (earnings calendar) + filings | Window computable with Session 8 (Model 5) | — | Computable |
| COT TFF (JPY, equity index, Treasuries) | CFTC | Session 16; JPY pulled forward with the yen monitor | free | Full history |
| FINRA short interest; daily short volume | FINRA | Meme v0 (Change Order #3) | free | Full history (semi-monthly); daily |
| Borrow conditions (CTB, availability) | IBKR via Gateway | Meme v0; probe Tuesday | included | Forward-only |
| 13F | SEC EDGAR | Session 19 | free | Full history, 45-day lag |
| Sentiment surveys | AAII, NAAIM, II | Sessions 16–17 | free/low | Full history |
| RTAT10 retail activity | Nasdaq Data Link | Change Order #3 item 1 — **first build** | free | **To 2016** |
| Attention velocity | ApeWisdom | Meme v0 | free | Limited |
| Yen carry monitor (composite) | Own state machine | Change Order #3, 29.1 v0 | — | Components historied; composite forward |
| Crypto liquidation / funding | Alt Asset's sources | Alt Asset plan | — | Vendor-dependent |
| Lock-up calendar | Filings; SPCX/ASTS trackers | Overhang pattern in Daily | — | Announced |

The table's honest summary: the flows that can be *computed* (leveraged ETFs, calendars, buyback windows) can be backtested; the flows that can only be *observed* (auction, borrow, dealer positioning) accumulate forward from the week this paper was drafted; the positioning surveys have history but lag. The paper's recommendations are ordered accordingly — computable models first, forward-only loggers started immediately, surveys as they are scheduled.

---

## Part IX — Validation, and What Would Change This Paper

### 9.1 Hypotheses, not features

Seven hypotheses are registered in Change Order #3 — four on the closing auction, three on the meme lifecycle — and this paper adds four of its own to the same table, dated the day it is committed: that leveraged-ETF rebalance expectation explains a large share of ordinary-day auction imbalance variance (testable as soon as the sampler has a month); that vol-control turning points lead index drawdown recoveries by days (testable against history now, since both inputs are computable); that the buyback-window absence is visible in breadth (testable now); and that the response-ratio deterioration flag on the auction precedes multi-day declines more often than chance (testable after a quarter of sampler history). Each is graded through the register's hypothesis path, with a declared test date and sample, before any becomes a setup. The paper's position, borrowed from *Building and Validating a Systematic Book*: a hypothesis that has a test date is knowledge in progress; one that does not is a story.

### 9.2 Lead/lag as the test that can retire a source

Part 27's phase-2 lead/lag test — does a source add information *before* the assets it is supposed to inform — applies to every positioning input here. If COT's JPY positioning never leads the FX-velocity group, it is a vulnerability measure and not a timing one, which is what this paper already assumes; if RTAT's new-entrant shock never leads the name's price, the retail group's rights shrink. The test is what keeps the family from accumulating inputs that describe the past. It runs quarterly on the store, and its results move trust-matrix rows.

### 9.3 The independence audit

Once a quarter, the store's correlation structure across the seven mechanism groups is recomputed. Groups whose signals have become highly correlated over the trailing year are candidates for merger — one vote, not two — and the paper expects the systematic and passive-calendar groups to be the first test, since a large down day makes vol-control selling, CTA selling and leveraged-ETF selling coincide by construction. If the audit merges them, the confluence rule's arithmetic changes, and the doctrine's setups need one more independent cluster. The audit is the mechanism by which the paper's independence table stays honest.

### 9.4 What would change this paper

Three things. **Nasdaq Closing Cross data**, if a route is found, changes Part IV's auction reading from NYSE-family to market-wide and retires the GAP flag. **A year of sampler history** turns Part IV's worked examples from illustrations into base rates, and turns the four auction hypotheses into either setups or discarded ideas — this paper's second edition is written from that year. And **a forced-flow episode the monitors watched in real time** — a yen unwind, a reconstitution-day auction that failed to absorb, a meme squeeze the lifecycle classifier tracked from ignition to exhaustion — would give the paper the thing it lacks as of this draft: a case study the system observed rather than one it reconstructs.

---

## Appendix — The absorption primitive, stated once

```
response_ratio(stimulus, response, window, baseline_history):
    ratio      = response / stimulus                  # signed, over the window
    baseline   = percentile(ratio, baseline_history)  # own history, never a constant
    flag       = deteriorating if ratio moves away from baseline
                 toward less absorption (more response per unit stimulus,
                 or less response where response was the stimulus's purpose)
    returns ratio, percentile, flag, n_baseline
```

Callers as of this draft: closing-auction absorption (stimulus = normalized imbalance; response = indicative-price displacement); yen carry (stimulus = yen appreciation × positioning percentile; response = risk-asset and credit move); leveraged-ETF program (stimulus = computed rebalance; response = auction displacement); Speculative Cohort (stimulus = revision velocity; response = price velocity — inverted sense); meme lifecycle (stimulus = attention velocity; response = price); prediction-market divergence (stimulus = probability change; response = mapped-asset move). One function. The paper's claim is that positioning analysis is, at bottom, this function applied to the mechanical holders' calendars.
