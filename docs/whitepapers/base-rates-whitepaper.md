# Base Rates

## What Markets Usually Do — and How Far Back "Usually" Goes

**Companion white paper — chester-reports library**
**Series placement:** with the market-timing layer, beside *Tops and Bottoms* (numeral assigned by the library guide on commit; cross-references in this paper are by name)
**Version:** 1.0 — September 2026
**Status:** Reference. Consulted before a thesis is written, not after. Figures are recomputed annually and on any methodology change; every number carries its window and its source class.

---

### Reader's note

Every other paper in this library explains a mechanism. This one supplies the denominators. It exists because the Operating Doctrine's central edge concept — variant perception — is arithmetic on a base rate: to hold a view that differs from consensus you must first know what ordinarily happens, and most trading error is a failure of that first step rather than of the second. A trader who does not know that the S&P 500 has closed higher on roughly 54% of days since 1928 will read a three-day losing streak as information. A trader who does not know that a 10% drawdown occurs in most years will treat one as a regime change. A trader who does not know that the median analyst estimate is beaten about three-quarters of the time will read a beat as a surprise.

The paper is deliberately boring, and that is its function. It is a reference to consult *before* writing a thesis, in the way one consults a mortality table before pricing a policy — a comparison the operator will find familiar. The Doctrine's Rule 6 requires that an edge name its counterparty and say why it persists; this paper is where the claim "and here is what normally happens instead" gets its number.

---

## Executive summary — the twelve things this paper says

*For the reader who will consult the tables later and wants the conclusions now.*

1. **Ordinary is not average.** The interquartile range of a year runs from about −1% to +25%. A year near the +10% mean is rare. Any thesis that needs a "normal year" is a thesis about an uncommon event.

2. **A 10% decline is an annual event, and half of all years see one.** The average intra-year drawdown is 14%, in years that finish positive three times in four. Treating a correction as the start of 2008 is the specific mechanism by which the Book A floor gets breached, and this operator's record says he does it.

3. **A bear takes about a year to complete and contains three to five rallies of 5% or more**, any of which will feel like the bottom. Conviction is unreliable in exactly that window, which is why a short campaign ends on the bottom signal and not on judgment.

4. **The equity premium arrives in a minority of days, and those days cluster inside drawdowns.** Being out of the market during stress is not neutral; it is where the return is forfeited. This is the arithmetic behind the allocation floor.

5. **Daily direction has no memory; trend is a cross-sectional, multi-week phenomenon.** A three-day streak is noise. A name at a twelve-month high with twelve-month relative strength is a documented anomaly. Book B enters on pivotal points, not streaks, for this reason.

6. **Volatility clusters and correlations converge in stress.** The Volatility dial is a state, not a level; diversification weakens exactly when it is being relied on; the heat cap across books counts correlated positions once because in the crisis row they *are* one.

7. **The stock–bond hedge is a regime statistic that one long disinflationary period made look permanent.** 2022 falsified it. The duration sleeve is a deflation hedge specifically — Part IV's central practical claim, arriving here from the correlation table.

8. **Seasonality is real, small, decaying since publication, and never a thesis.** The one exception worth *watching* is the midterm-year cycle — 2026 is one — which enters the register as a hypothesis, not a signal.

9. **A beat is not a surprise and guidance beats the print.** Three-quarters of companies beat. The tradeable object is the reaction relative to positioning, and the long single option into a print is a negative-expectancy trade on average because the implied move has slightly exceeded the realized move.

10. **Options decay as √T; a third expire worthless, not ninety percent; same-day expiries are half of index option volume.** The verticals-by-default rule follows from decay and from spread cost together — at Book C's size, a wide single-name option can consume a tenth of the risk budget in the round trip.

11. **The U.S. record since 1970 is eight bears, and it excludes the two mechanisms the operator most fears.** Extending to 1907 doubles the sample and adds debt deflation, funding crises outside the regulatory perimeter, and financial repression — the resolution in which bonds, not equities, are destroyed.

12. **The tail the operator worries about sits near the 95th percentile of the historical distribution, not beyond it.** Japan's thirty-four years and 1929's twenty-five are developed-market events within living memory. No single hedge covers both resolutions of a debt cycle. That is why the tail budget is convex and renewed rather than held — and why a portfolio hedged for 2008 is not hedged for 1946.

---

Three conventions run throughout. **Every figure carries its window**, because a base rate computed since 1928 and one computed since 2009 are different claims about different worlds; where the two disagree materially, both are given. **Every figure carries a source class** — measured from data the system holds, computed from public series, or cited from the literature — because the system's registry distinguishes them and so should the reader. And **no figure is a forecast.** A base rate is what happened in a sample; the future is not obliged to resemble it, and Chapter 9 is the honest account of where these numbers are least trustworthy.

The paper has three parts. Part I is the return and drawdown distribution — the shape of ordinary. Part II is the base rates of the events a trading day is made of: gaps, streaks, earnings, expiries, options decay, spread costs. Part III is the historical extension the *Tops and Bottoms* paper does not cover: the downturns before 1970, treated on the same template, because eight bears since 1970 is a sample of eight and the questions this operator asks — how bad can it get, how long, what preceded it — need more.

---

# Part I — The Shape of Ordinary

## Chapter 1 — Returns

### 1.1 The distribution, at four frequencies

| Horizon | Positive share | Median | Mean | Notes |
|---|---|---|---|---|
| Daily | ~54% | ~+0.04% | ~+0.03% | The mean is below the median because the left tail is fatter; the gap is the whole subject of Chapter 2 |
| Weekly | ~56–57% | ~+0.2% | ~+0.15% | |
| Monthly | ~62–63% | ~+1.0% | ~+0.7% | |
| Calendar year | ~73–75% | ~+12% | ~+10% total return; ~+8% price | Since 1928; the post-1950 figures are one to two points higher |
| Rolling 10-year | ~95% positive nominal | ~+7%/yr | | Negative decades exist: the 1930s, the 2000s |
| Rolling 20-year | 100% positive nominal in the U.S. sample | | | *The sample is one country that won the century — see 9.2* |

*Source class: computed from public index series, 1928–2026.*

**What to take from this table.**

- *Read the positive-share column as the cost of sitting out.* A 54% daily edge is invisible; a 74% annual edge is the whole game. The operator who is out of the market "waiting for clarity" is declining a three-in-four bet, every year, on the strength of a coin-flip daily read.
- *The mean is below the median at every frequency.* The distribution is left-skewed — a few very bad days pull the average down. This is not a reason to be out; it is the reason the Doctrine has a volatile-day protocol rather than a market-timing rule. The bad days are handled by size, not by absence.
- *The ten-year and twenty-year rows describe one country.* Chapter 16 says why they cannot be generalized. Use them to size patience, not to promise outcomes.
- *For the short side specifically:* the base rate is against you 54% of days, 62% of months, 74% of years. A short thesis must name what makes this the minority case, and the Doctrine's extra-confirmation rule for shorts is that requirement made procedural.

The two readings that matter most. **The equity risk premium arrives in a minority of the time**: a small number of very good days carry the compounded return, and the frequently cited finding that missing the best ten or twenty days over a multi-decade span destroys most of the return is real, with the essential companion fact that those days cluster inside drawdowns, adjacent to the worst days. This is the arithmetic behind the Doctrine's Book A floor: being out of the market during stress is not a neutral act. **And the annual mean is not a typical year.** Returns cluster in the tails: the S&P's annual return has fallen between +8% and +12% — the neighborhood of its own average — in a small minority of years. "An average year" is a statistical artifact, not an experience.

### 1.2 Volatility

| Measure | Typical | Calm regime | Stressed | Crisis |
|---|---|---|---|---|
| Realized volatility, S&P 500, annualized | ~15–16% long-run | 8–12% | 20–30% | 40%+ |
| VIX, median | ~17–18 | <15 | 20–30 | >35 |
| Days per year with a ±1% move | ~50–60 | ~20 | ~90 | 120+ |
| Days per year with a ±2% move | ~10–12 | ~2 | ~25 | 40+ |
| Largest single-day decline in a typical year | ~−3% | | | 1987: −20.5%; 2020: −12.0%; 2008: −9.0% |

*Source class: computed.* Volatility clusters — the autocorrelation of absolute returns is one of the most robust facts in finance — which is why the Doctrine's Volatility dial is a state rather than a level, and why the volatile-day protocol assumes the next day resembles this one more than it resembles the average.

**What to take from this table.**

- *Fifty ±1% days a year is the ordinary texture of the market.* A 1% move is not news, not a signal, and not a reason to touch a position. The volatile-day protocol's triggers are set well above this level for that reason.
- *The largest single-day decline in an ordinary year is about −3%.* Anything larger is regime information — a Rising or Stressed reading — and is the moment to halve size rather than to judge the move.
- *Volatility clusters, so the first ±2% day is the best predictor of the second.* Reduce on the first, not the third. The operator's record of "periodic damage in extreme volatility" is, mechanically, a record of acting on the third.
- *The Calm column is where Book C's fade-toward-pin setup lives and the Stressed column is where it dies.* Same setup, opposite expectancy — the trust matrix's regime rows are this table's columns.

### 1.3 Percentiles, not averages

The mean is the least useful summary of any of these distributions, and the paper gives quartiles wherever it can. The convention throughout: **p25 / median / p75**, with the mean beside them when the gap between mean and median is itself informative.

| Series | p25 | Median | p75 | Mean | Read |
|---|---|---|---|---|---|
| Daily return | −0.50% | +0.05% | +0.58% | +0.03% | Mean below median: the left tail is fatter |
| Monthly return | −1.9% | +1.1% | +3.6% | +0.7% | A typical month is a small gain |
| Annual total return | ~−1% | ~+12% | ~+25% | ~+10% | **The middle two quartiles span −1% to +25%** — this is what "ordinary" means for a year |
| Intra-year max drawdown | −6% | −10% | −18% | −14% | Half of all years see a decline of 10% or worse |
| VIX daily close | ~13.5 | ~17.6 | ~22.5 | ~19.5 | p95 near 33; the distribution is heavily right-skewed |

*Source class: computed from public index series, 1928–2026 for returns, 1990–2026 for VIX; figures rounded and approximate.*

**What to take from this table.**

- *The p25 annual return is about −1%.* One year in four is roughly flat-to-down. A flat year is not a failed year and not evidence that a thesis was wrong; it is the lower quartile of ordinary.
- *The p75 intra-year drawdown is −18%.* One year in four contains a decline that would trip the Doctrine's Drawdown I switch if it were fully held with no regime response. The bands exist so that it is not fully held when the Volatility dial has already said Stressed.
- *VIX's median is about 17.6 and its p75 about 22.5.* A VIX in the low twenties is the upper-ordinary range, not stress. Stress begins near the p95, around 33 — which is where the volatile-day protocol's threshold sits, on purpose.
- *For sizing:* the interquartile range of a year is twenty-six points wide. A position sized so that a −1% year is survivable and a +25% year is participated in is a position sized to the distribution. A position sized to the mean is sized to a fiction.

The annual row is the one to carry. A year that ends −1% and a year that ends +25% are both inside the interquartile range: **the ordinary experience of a year is nothing like +10%.** Any thesis whose payoff depends on a "normal year" is a thesis about a rare event.

## Chapter 2 — Drawdowns

### 2.1 Frequency and duration — the table to memorize

| Drawdown from peak | Frequency | Median duration peak-to-trough | Median time to recover |
|---|---|---|---|
| −5% | 3–4 times a year | ~2 weeks | ~1 month |
| −10% (correction) | about once a year | ~1–2 months | ~3–4 months |
| −15% | about every 2 years | ~3 months | ~6 months |
| −20% (bear) | about every 4–5 years | ~9–10 months | ~1.5–2 years |
| −30% | about every decade | ~12 months | ~2–4 years |
| −50%+ | twice since 1928 excluding the Depression's −86% | 15–25 months | 4–7 years |

*Source class: computed from index series; consistent with the episode set in* Tops and Bottoms *and Part III below.*

The same episodes as a distribution rather than as averages:

| Bear-market property | p25 | Median | p75 | Extreme in sample |
|---|---|---|---|---|
| Depth (peak to trough) | −22% | −30% | −48% | −86% (1929–32) |
| Duration, peak to trough | ~6 months | ~11 months | ~20 months | 34 months (1929–32) |
| Time to recover the prior peak | ~5 months | ~2 years | ~4–5 years | 25 years nominal (1929–54); 34 years (Japan, 1989–2024) |
| Largest counter-trend rally inside the decline | +7% | +10% | +16% | +46% (Nov 1929–Apr 1930) |

*Source class: computed across the extended episode set of Part III; small samples — see Chapter 16.*

**What to take from these two tables.**

- *The drawdown ladder maps directly to the Doctrine's switches.* −5% three or four times a year is noise the daily switch should never see; −10% about annually is the correction the weekly and monthly switches are calibrated against; −20% every four or five years is the bear the Drawdown I switch and the regime dials exist for. Each switch is set at a frequency, and the frequencies are these.
- *Median recovery from a bear is about two years; p75 is four to five.* A book that is de-risked at the bottom and waits for "confirmation" will typically miss the first year of a two-year recovery — which, by Chapter 1's clustering finding, is where a disproportionate share of the return lives. The bottom-signal override exists to force re-entry against this instinct.
- *The p75 bear is −48%.* One bear in four is a halving. The allocation bands' floors are set so that the book participates; the bands' ceilings are set so that a halving costs the book its band-weighted share and not the whole.
- *The counter-trend rally row is the short-seller's table.* Median +10%, p75 +16%, extreme +46%. A short campaign will face three to five of these, and each will look like the turn. The rule that a short closes on the bottom signal — not on conviction — is written against this row.

The operator's stated history includes being under-invested since 2008 and periodically damaged in extreme volatility. Both are addressed by different rows of this table. **A −10% drawdown is an annual event, not a signal** — treating each as the beginning of 2008 is the mechanism by which the Book A floor gets breached. **And a −20% bear takes the better part of a year to complete** — which is why the Doctrine's Top & Bottom override permits adding at the bottom rather than requiring a call at the top, and why a short campaign that has worked for two months is not thereby vindicated.

### 2.2 Intra-year drawdowns versus annual outcomes

The single most useful fact in this chapter: the average *intra-year* maximum drawdown for the S&P 500 is roughly 14%, and the index still finishes positive in about three years in four. A year with a 12% mid-year decline is an ordinary year. This is the base rate against which every "the market is breaking down" thesis must be written.

**What to take from it.**

- *Write the drawdown number on the card.* Fourteen percent is the ordinary intra-year experience. A thesis that "the market is breaking down" at −8% is a thesis that this year will be worse than average, and it should say why.
- *The operator's known bias — reading a correction as a regime change — has a numerical antidote:* the question at any −10% is not "is this 2008?" but "is this the one year in four where it exceeds −18%, and what in the regime dials says so?" If the dials read Calm or Rising, the base rate says buy the dip inside the band, not exit it.
- *The floor is the instrument here.* The bands' floors exist so that a −14% year is held through, not traded around.

### 2.3 The shape of a decline

Declines are not smooth. Within bear markets, the largest single-day *advances* in history cluster — October 1929, October 2008, March 2020 — and 5%+ counter-trend rallies are routine. The base rate for the operator's short book: **during a −20% or worse decline, expect three to five rallies of 5% or more**, any of which will feel like the bottom. The Doctrine's rule that a short campaign ends on the Top & Bottom bottom signal rather than on conviction exists because this base rate makes conviction unreliable in exactly this window.

**What to take from it.**

- *The best days live inside the worst months.* The clustering of the largest advances inside bears is why "sell now, buy back when it's calmer" underperforms holding through: the buy-back happens after the days that mattered.
- *For the short book, size for five rallies, not one.* A short sized so that a single +10% counter-trend rally trips its stop is a short that will be stopped out of a correct thesis three to five times per bear. Sizing and stop placement in Book B's short rules are written against this row.
- *For the long book, the rally is not the signal.* A +8% bounce in a −25% decline is the median counter-trend move and carries no information about the bottom. The bottom signal is the composite, not the rally.

## Chapter 3 — Seasonality

Seasonality is the part of this paper most likely to be misused, so the chapter states the research, the decay, and the ruling in that order.

### 3.1 What the research actually found

**The Halloween effect (November–April versus May–October)** is the most robust of the calendar anomalies. Bouman and Jacobsen's 2002 study found November–April outperformance in the large majority of the thirty-seven markets they examined, and later work extending the U.K. record back roughly three centuries found the pattern present across most of that span. The average gap in modern U.S. data is on the order of several percentage points a year, and — unusually for an anomaly — it has not disappeared since publication, though it has weakened and has failed for multi-year stretches.

**The turn of the month.** Ariel (1987) and Lakonishok and Smidt (1988) documented that the last trading day of a month plus the first three of the next capture a disproportionate share of monthly return — in some samples, more than the entire month's return, with the remaining days net negative. The mechanism is plausible and mechanical: salary and pension contributions, index-fund inflows, and month-end rebalancing all land in that window, which is the Positioning & Flows paper's territory.

**The January effect** — small-cap outperformance in early January, attributed to tax-loss-selling reversal — was strong through the 1970s and has substantially decayed since publication, which is the canonical example of an anomaly being arbitraged once documented.

**September** is the only month with a negative average return in most long U.S. samples, and volatility seasonality peaks in September–October, which is where several of the historical crashes sit. Whether the crash cluster causes the statistic or the statistic is the crash cluster is unresolved; the honest reading is that a five-episode cluster in a century is a small sample making a monthly average look worse than the typical September felt.

**The presidential cycle** is the seasonal effect with the most immediate relevance. In the post-war U.S. record, the third year of the cycle has been the strongest by a wide margin and the second — the midterm year — the weakest, with the largest average intra-year drawdown of the four. The more useful form of the statistic is conditional: **forward returns measured from the midterm-year low have been unusually strong**, on the order of high-teens to twenty-plus percent over the subsequent twelve months across most cycles. **2026 is a midterm year**, which places the current calendar in the weakest quarter of the cycle and, if the pattern holds, ahead of its strongest — a fact the paper records as context rather than as a forecast, and one the prediction-market engine's midterm contracts will price independently.

**Day-of-week, holiday, and expiry effects** are smaller. The Monday effect has largely vanished; pre-holiday sessions retain a mild positive drift; monthly expiry week carries a small positive tilt whose sign is unstable.

### 3.2 The decay problem

McLean and Pontiff's work on published anomalies found that returns decay materially after publication — roughly a third out-of-sample, and more than half once in-sample overfitting is accounted for. Every effect in 3.1 has been published for decades. The prior should therefore be that each is smaller now than in the study that found it, and that some are gone.

### 3.3 The ruling

Seasonality is **a tiebreaker at the margin of an existing thesis, never a thesis.** It may shade the size tier within its band or the timing of an entry already justified on other grounds. It may not generate a packet, and every seasonal metric enters the registry `trigger_eligible: false` permanently — not pending evidence, but by construction, because a calendar effect has no counterparty story that survives the Doctrine's Rule 6. The presidential-cycle conditional is the one exception worth watching rather than trading: it is a *positioning* statement about a crowded consensus in an election year, and it belongs to the register as a hypothesis with a dated entry, graded like any other.

## Chapter 4 — Trends, streaks, and mean reversion

| Pattern | Base rate |
|---|---|
| Consecutive up days | 2 in a row ~29%; 3 ~16%; 5 ~5%; the record is 12–14 |
| Consecutive down days | Similar, slightly less persistent |
| Probability the next day is up given today was up | ~54% — essentially the unconditional rate; **daily direction has almost no memory** |
| Overnight vs intraday | Since the 1990s, a large majority of the index's cumulative return has accrued overnight rather than during regular hours |
| Gap fill, same day | Small gaps (<0.5%) fill same-session more often than not; large gaps (>1%) fill same-day well under half the time |
| Momentum, 12-month minus 1-month, cross-sectional | Positive expectancy over most decades; violent crashes after bear-market bottoms |
| Mean reversion, 1-month | Weakly negative autocorrelation in single names; the short-term reversal effect |

*Source class: computed and literature.* The reading for Book B: **trend persistence is a cross-sectional and multi-week phenomenon, not a daily one.** A three-day streak is noise; a name at a 12-month high with 12-month relative strength is a documented anomaly. The Doctrine's Book B entry at a pivotal point rather than on a streak follows directly.

**What to take from this table.**

- *A streak is a coin sequence.* Five up days in a row happens about one week in twenty by chance. It is not momentum, not exhaustion, and not a reason to act in either direction.
- *The overnight row is the Daily Cascade's reason to exist.* Most of the index's cumulative return has accrued outside regular hours. The 07:00 report reads a session that has already happened — two foreign sessions plus futures — and the gap it reports is where the day's return usually already sits.
- *Gap-fill is a size-dependent base rate.* Small gaps fill more often than not; large gaps under half the time. A Book C fade of a 1.5% gap is a below-coin-flip bet before positioning is considered; the setup requires the positioning read to move it above.
- *Momentum's crash after bear bottoms is the trust matrix's "momentum: Off after a bottom signal" row.* The strategy that works for most of the cycle is the one that loses most at the turn.

## Chapter 5 — Correlation and diversification

| Regime | S&P 500 / 10-year Treasury correlation | Average pairwise stock correlation |
|---|---|---|
| Disinflationary calm (1998–2020 typical) | −0.3 to −0.5 | 0.20–0.35 |
| Inflationary (1970s; 2022) | +0.2 to +0.6 | 0.35–0.50 |
| Crisis | Bonds usually rally, but not always (2022, and the March 2020 dash-for-cash days) | 0.60–0.85 |

*Source class: computed.* The base rate that governs Book A's duration sleeve: **the stock–bond hedge is regime-dependent and was negative for one unusually long disinflationary period.** Sizing a duration sleeve as a hedge on the 1998–2020 correlation is sizing on a sample that 2022 falsified. And the crisis row is the reason the Doctrine caps heat across books at a common factor: correlations converge exactly when diversification is being relied upon.

**What to take from this table.**

- *Ask which row you are in before sizing the hedge.* In the disinflationary row, duration hedges equity; in the inflationary row, it amplifies the loss. The Macro dial's Overheat and Tightening states are the inflationary row, and the Doctrine's bands cut duration in exactly those states for this reason.
- *Pairwise correlation of 0.7–0.9 in crisis means a portfolio of ten names is roughly one position.* The heat calculator's "count correlated positions once at their common factor" is this row applied. Six long semiconductors and a long NQ call spread is one trade with three tickers.
- *The crisis row is also the diversification-across-countries finding of the International Equities paper:* correlations converge in joint downside moves and not in joint upside. The insurance is against the single-country tail, not the bad quarter.

---

# Part II — The Base Rates of a Trading Day

## Chapter 6 — Earnings

| Fact | Base rate |
|---|---|
| Companies beating consensus EPS | ~70–78% in a typical quarter — the beat is the norm, the *guidance* is the news |
| Companies beating on revenue | ~60–65% |
| Earnings-day absolute move, large-cap — p25 / median / p75 | ~2% / ~4% / ~7%; single-name tech p75 routinely 10%+ |
| Options-implied move versus realized, on average | Implied slightly exceeds realized — selling the event has positive expectancy on average and catastrophic tails |
| Post-earnings-announcement drift | Documented for decades; weaker since the 2000s but not extinguished |
| IV crush | Front-month implied volatility typically falls by a third to a half the morning after |

*Source class: literature and computed.* Two consequences for the books. **A beat is not a surprise**; the tradeable object is the reaction relative to the positioning-implied expectation, which is the Daily Cascade's event-reaction setup. And **the long-option expression into an earnings print is a losing trade on average** — the IV crush is a base rate, and the Doctrine's expression table should never default to it.

**What to take from this table.**

- *Seventy-five percent beat, so a beat is the null hypothesis.* The information is in the reaction, the guidance, and the off-diagonal quadrants — beat-and-lower, miss-and-raise. The Earnings paper is built on this row.
- *The implied move slightly exceeds the realized on average.* Selling the event has positive expectancy and catastrophic tails; buying it has negative expectancy and a fat right tail. Neither is a strategy. The signal is the implied move against the name's own history.
- *Front-month IV falls by a third to a half the next morning.* A long call bought into the print is fighting that collapse; a post-print entry on the reaction is buying after it. The order of operations is the edge.
- *Post-earnings drift persists in smaller names.* The Book B swing on a surprise, entered after the crush and held on the sixty-day clock, is the expression of this row.

## Chapter 7 — Options: decay, moneyness, and the cost of being wrong on timing

| Fact | Base rate |
|---|---|
| Probability an at-the-money option expires in the money | ~50%, slightly less after costs |
| Probability a 30-delta option expires in the money | ~30%, by construction — delta approximates it |
| Theta as a share of premium, at the money | Accelerates as √T: roughly a third of remaining premium decays in the final third of the life |
| Share of options expiring worthless | Roughly a third expire worthless, a third are closed early, a third are exercised — *the folk claim that "80–90% expire worthless" is false* |
| Same-day expiry share of index option volume | Roughly half of S&P index options volume by 2025–26, from near zero in 2016 |
| Bid-ask cost, index ETF options, at the money | Cents on liquid strikes; multiples of that on single names and far strikes |

*Source class: exchange statistics and computed.* The Doctrine's Book C default of vertical spreads follows from row three and row six together: a spread caps the theta bleed and halves the number of spreads crossed.

**What to take from this table.**

- *Delta is a probability.* A 30-delta option finishes in the money about 30% of the time. A trader buying it is making a 30% bet and should size and price it as one — which is why the Options paper's verticals rule pays no more than a third of the width.
- *The "options expire worthless" folk claim is false, and the reason matters:* a third are closed early, which means most option positions are managed, not held to expiry. Management is the skill; expiry is the exception.
- *Theta's √T acceleration is the reason short-dated options are decay instruments and long-dated ones are volatility instruments.* The tenor decision is a decision about which greek you are buying.
- *Half of index option volume is same-day.* The 0DTE book is now the market's largest intraday flow; the Dealer's Hand and the intraday cadence exist because of this row.

## Chapter 8 — Expiries, auctions, and the clock inside the day

| Fact | Base rate |
|---|---|
| Monthly expiry week, historical drift | Mildly positive on average; the effect is small and unstable |
| Quarterly triple-witching volume | Multiples of an ordinary session; the largest expiries of the year |
| Closing auction share of daily volume | ~10% on ordinary days; 20%+ on rebalance days; the majority of an affected name's volume on reconstitution day |
| Reconstitution day | Routinely the year's single largest closing auction |
| First and last thirty minutes | Carry a disproportionate share of daily volume and range |
| Average daily range as a share of price | ~1.0–1.3% in calm regimes; 2–3% in stressed |

*Source class: exchange statistics.* These are the numbers the Positioning & Flows paper's calendar assumes and the market-on-close module measures against.

**What to take from this table.**

- *The closing auction is a tenth of the day and the majority of a reconstitution-day name.* An imbalance read on a classified day is the calendar's flow, not a holder's decision — the event-classification table exists to prevent this misreading.
- *The first and last thirty minutes carry disproportionate range.* The Doctrine's three-touch rhythm — 07:00, 10:00, the close — is built around this: the operator is absent during the low-information middle of the session by design.
- *Quarterly witching is the year's largest expiry release.* The Dealer's Hand's expiration-release ladder is largest on these four days, and the post-expiry rewrite of the dealer book is the reason the Weekend report uses post-expiry state.
- *Average daily range doubles in stressed regimes.* A stop placed at "1% below entry" in a Calm regime is inside the noise in a Stressed one; stop distance is a function of the regime's range, not a fixed percent.

## Chapter 9 — Costs, and the arithmetic of turnover

The Doctrine sizes in dollars of risk; this chapter supplies the dollars of friction.

| Cost | Typical magnitude |
|---|---|
| Commission, this account (Fixed schedule) | $0.005/share, $1.00 minimum, 1% cap |
| Bid-ask, large-cap equity | 1–3 basis points |
| Bid-ask, index ETF | Sub-basis-point on the largest |
| Bid-ask, liquid index option | Pennies wide near the money |
| Bid-ask, single-name option, out of the money | 5–15% of premium — *the dominant cost in Book D* |
| Slippage, market order in size | Rises with participation rate; the reason the execution framework prefers limits |
| Borrow, hard-to-borrow name | 10–100%+ annualized; the meme lifecycle's DO-NOT-SHORT input |

The arithmetic that matters: **at Book C's standard risk of about $1,050 per trade, a round trip in a wide single-name option can consume a tenth of the risk budget before the thesis is tested.** This is why the Doctrine restricts Book C to index instruments and why the expression check flags illiquid expressions.

---

# Part III — The Long Record of Downturns

## Chapter 10 — Why the sample must go back further than 1970

*Tops and Bottoms* treats every major U.S. turning point since 1970 — eight bears and the near-misses — on one template, with a thirteen-episode calibration harness. That paper is the operative one; it owns the signal-by-signal scoring and the forward-return distributions the Top & Bottom report uses. This chapter does not repeat it. It extends the *sample*, for three reasons the operator's own history makes concrete.

**Eight is a small number.** A framework calibrated on eight episodes has eight degrees of freedom against the ways a market can fall, and the confidence interval on "how often does a bear reach −40%" from eight observations is uselessly wide.

**The post-1970 sample excludes the two mechanisms the operator most worries about.** There is no deflationary debt-liquidation in it, and no inflationary destruction of a bond portfolio's real value across a decade — the 1970s appear as price declines but the real-return story is the one that mattered. A tail framework whose sample begins in 1970 has never seen 1929–32 or 1946.

**Regimes recur on a longer clock than a career.** The operator has traded through roughly one interest-rate regime. The Rate and Liquidity Machine's eleven regime eras from 1907 exist for the same reason this chapter does.

The episodes below are given on the same template as *Tops and Bottoms* — context, mechanism, what signaled, what stayed silent, the shape and the aftermath — compressed, because the operative detail lives in that paper and its calibration harness. Depths and durations are approximate and are given for the S&P composite or its predecessor index unless noted.

## Chapter 11 — Pre-1970 downturns on the template

### 11.1 The Panic of 1907 — a liquidity crisis without a lender of last resort
*Depth:* roughly −45% peak to trough. *Duration:* about 15 months. *Mechanism:* a failed corner in a copper stock triggered runs on the trust companies — the shadow banks of their day, outside the clearinghouse system — and the crisis was ended by a private bailout organized by J. P. Morgan. *What signaled:* call-money rates spiking to extraordinary levels; trust-company balance-sheet fragility visible to anyone who looked. *What stayed silent:* the broad economy until the panic was underway. *Aftermath:* the Federal Reserve Act, 1913. *Why it belongs in the sample:* it is the cleanest case of a funding crisis in an institution class the regulatory perimeter did not cover — the mechanism that recurred in 2008 and that the tail scenarios track in private credit today.

### 11.2 1929–1932 — the deflationary debt liquidation
*Depth:* −86% peak to trough, the deepest in the record. *Duration:* 34 months of decline; the nominal peak was not recovered for 25 years. *Mechanism:* a leveraged equity bubble met a banking collapse, a contracting money supply, and policy that tightened into the downturn; margin debt, a fragmented banking system with no deposit insurance, and the gold standard's constraint on response combined. *What signaled:* extreme margin debt; a two-year parabolic advance; deteriorating breadth into the 1929 peak. *What stayed silent:* the initial October crash looked survivable — the index recovered nearly half its loss by April 1930 before losing 80% more. *Aftermath:* deposit insurance, securities regulation, the abandonment of the gold peg. *The reading:* the −86% is not the useful number; **the bear-market rally of +46% between November 1929 and April 1930 is** — it is the archetype of the counter-trend rally that ends short campaigns and restarts long ones at the wrong time.

### 11.3 1937–1938 — the policy-error recession
*Depth:* roughly −50%. *Duration:* about 12 months. *Mechanism:* premature tightening — a doubling of reserve requirements and fiscal contraction — into an incomplete recovery. *Why it belongs:* it is the canonical case of the second downturn inside a longer recovery, and the reason the Monthly's policy pillar watches for tightening into weakness rather than for tightening as such.

### 11.4 1946–1949 and the 1940s real-return bear
*Depth:* roughly −30% nominal in 1946–47. *Mechanism:* the post-war demobilization, the end of price controls, and an inflation spike that ran above 15%. *Why it belongs:* the *real* damage in this period fell on bondholders, not equity holders — the era of financial repression in which nominal yields were capped below inflation for years. A duration sleeve held through it lost a third of its purchasing power. This is the episode that a stock–bond correlation estimated on 1998–2020 cannot imagine.

### 11.5 1961–1962 — the "Kennedy Slide"
*Depth:* roughly −28%. *Duration:* about 6 months, with a sharp late-May crash. *Mechanism:* a speculative advance in growth stocks, a confidence shock, and a fast unwind with no recession. *Why it belongs:* it is the cleanest pre-1970 example of a bear market without an economic contraction — the pattern that makes "wait for the recession" an unreliable rule.

### 11.6 The pre-1970 aggregate

| Episode | Depth | Months down | Recession? | Mechanism family |
|---|---|---|---|---|
| 1907 | ~−45% | ~15 | Yes | Funding/liquidity crisis |
| 1929–32 | −86% | 34 | Yes, severe | Debt deflation + policy error |
| 1937–38 | ~−50% | ~12 | Yes | Policy error |
| 1946–47 | ~−30% | ~12 | No (inflation shock) | Inflation/repression |
| 1961–62 | ~−28% | ~6 | No | Valuation unwind |

Adding these five to the eight post-1970 episodes roughly doubles the calibration sample and — more importantly — adds three mechanism families that the post-1970 set contains weakly or not at all: pre-Fed liquidity crisis, debt deflation, and financial repression.

## Chapter 12 — What the extended sample changes

**Depth.** Across thirteen-plus episodes, the median bear is about −30% and the interquartile range roughly −25% to −50%. The post-1970 sample alone understates the left tail because it excludes 1929 and 1937.

**Duration.** Median peak-to-trough about 10–12 months; the distribution is right-skewed, with 1929–32 and 2000–02 in the tail. Recoveries to the prior peak run from months (1987, 2020) to decades (1929, and in real terms the 1970s).

**Mechanism families, and their frequency.** Grouping the extended sample: valuation unwinds (1961, 1987, 2000), credit and funding crises (1907, 2008), policy errors (1937, 1973–74's aftermath, 2022), inflation shocks (1946, 1973–74), exogenous shocks (2020), and debt deflation (1929). The most useful cut for the tail watch: **the deepest and longest episodes are the credit and debt-deflation families; the fastest are the exogenous and valuation families.** Depth and speed are inversely related, which is why the 2020 recovery in five months and the 1929 recovery in twenty-five years are not the same kind of event and cannot inform the same rule.

**What signaled, across the extended sample.** The recurring antecedents, in rough order of reliability: credit-spread widening ahead of price; deteriorating breadth into the final advance; leverage at an extreme (margin debt, shadow-bank funding, or their era's equivalent); a policy tightening into an already-slowing economy; and a concentration of returns in a narrow leadership. The recurring *silences*: the economy at the peak, which is almost always fine; and valuation, which is a condition rather than a trigger and has been extreme for years at a time without consequence.

**What this changes in the Top & Bottom report.** Three concrete amendments, offered to that report's owner rather than asserted here. First, the calibration harness's episode set should be extendable to the pre-1970 cases with an explicit flag, because several of the modern triggers have no pre-1970 analogue and the harness must not score a signal that could not have existed. Second, the composite's top-side language should carry the bear-rally base rate from Chapter 2.3 — three to five 5% rallies inside a −20% decline — because that is the number that governs how a top call is *held*. Third, the bottom-side signal's forward-return distribution should be reported over the extended sample, where the tail of "bottoms that were not bottoms" (1930) is visible.

---

# Part IV — How Bad Can It Get

## Chapter 13 — Outside the United States, and before the modern record

Every number in Parts I through III describes one market in one country across one century, and that country's century was the best available. This chapter supplies the sample that the U.S. record excludes, because the operator's tail concern — a debt-cycle resolution with a monetary component — has no clean U.S.-only precedent since 1932 and several precedents elsewhere.

### 13.1 The global long-run record

The standard long-horizon evidence is the Dimson–Marsh–Staunton dataset, which since the late 1990s has assembled consistent real returns for twenty-one to thirty-five markets from 1900. Two findings from it govern this chapter. **Real equity returns outside the United States have been meaningfully lower** — the world index compounds at roughly 5% real against the U.S. at roughly 6.5% — which means the U.S. figure is the top of the distribution and not the centre of it. And **several markets in the 1900 index did not survive**: Russia in 1917 and China in 1949 went to zero for outside holders, and Austria-Hungary, Germany and Japan each suffered breaks in which the exchange closed, the currency was replaced, or both.

Survivorship therefore operates at the level of the country, not merely the company. A base rate constructed from the markets that still exist is conditioned on survival, and the honest correction is not a smaller number but a wider distribution with mass at total loss.

### 13.2 The deep drawdowns, on the same template

| Episode | Real drawdown | Time to recover in real terms | Mechanism |
|---|---|---|---|
| Japan, 1989–2009 | −82% nominal; deeper in real terms for property | **34 years to the nominal high (Feb 2024)** | Credit and asset bubble, slow bank recognition, deflation |
| United States, 1929–1932 | −86% nominal; roughly −79% real total return | Nominal price index 25 years; real total return by the mid-1940s | Debt deflation plus policy error |
| United States, 1966–1982 | Nominal roughly flat; real total return down by over 40% at the worst | About 17 years in real terms | Inflation; multiple compression |
| Germany, 1914–1923 | Equities preserved a fraction of real value; **bonds and cash went to zero** | Currency replaced twice within a generation | Hyperinflation and monetary reset |
| Germany and Japan, 1944–1948 | Roughly −90%+ real; exchanges closed | Decades | War, occupation, currency reform |
| Greece, 2007–2016 | Roughly −90% real | Not recovered | Sovereign crisis inside a currency union |
| Argentina, repeatedly since 1970 | Repeated 80–95% real drawdowns | Repeated resets | Fiscal dominance, currency destruction |
| Russia 1917, China 1949 | −100% | Never, for outside holders | Expropriation |

*Source class: cited from the long-run returns literature and standard market histories; approximate, and given for the shape rather than the decimal.*

### 13.3 What the extended distribution looks like

Putting the U.S. episode set beside the international one changes the shape of the tail rather than the middle:

| Percentile of "bad" | Depth | Duration to recovery | Example |
|---|---|---|---|
| Median bad market | −30% | ~2 years | 1990, 2022 |
| p75 | −45 to −50% | 4–5 years | 1973–74, 2000–02, 2008–09 |
| p90 | −55 to −60% real | 10–15 years | 1966–82 in real terms |
| p95 | −80% | 20–35 years | Japan 1989; U.S. 1929 |
| p99 | −90%+ real, or total loss | Never, for the original holders | Germany 1923 for bonds; Russia; China |

The reading the paper wants the operator to take is not "a −80% is coming." It is that **the tail he is worried about is real, has happened to developed markets with functioning institutions within living memory, and sits at roughly the 95th percentile of the historical distribution rather than off the end of it.** That is precisely the kind of risk a budget is for.

## Chapter 14 — The long-term debt cycle, and what a resolution looks like

### 14.1 The mechanism, stated without adjectives

The framework the operator is drawing on — Dalio's long-term or "big" debt cycle — makes a structural claim rather than a forecast. Debt grows faster than income for an extended period because each debt-financed expansion is easier than the alternative; debt service eventually consumes a rising share of income; the point arrives at which new borrowing is required to service old borrowing; and the imbalance is resolved through some combination of four channels — austerity, default and restructuring, transfers from those who have to those who have not, and debt monetization. The cycle runs on a clock of roughly fifty to seventy-five years, which is why it is invisible in a career and visible in a century.

The claim that matters for a portfolio is the *conditional* one. The resolution's form depends on the currency the debt is denominated in and on who holds it. **Debt in a currency the sovereign cannot print resolves deflationary** — default, contraction, falling prices — which is the United States in 1930–33 under the gold constraint, Greece in 2010–15 inside the euro, and emerging markets with dollar debt. **Debt in a currency the sovereign controls resolves inflationary** — monetization, currency depreciation, financial repression — which is Weimar Germany at the extreme and, in its mild and far more common form, the United States between 1946 and 1951.

### 14.2 Financial repression is the common case, and it does not look like a crash

The historically frequent resolution for a large sovereign with debt in its own currency is not a crash but a decade of quiet expropriation: nominal yields held below the inflation rate, so that the real value of the debt erodes while nominal asset prices rise. Reinhart and Sbrancia's work named the mechanism and estimated that it retired a substantial share of the post-war debt burden in the advanced economies. The U.S. instance ran from the wartime yield peg through the Treasury–Federal Reserve Accord of 1951, and it produced a decade in which equities did tolerably in nominal terms while long bonds lost a third or more of their purchasing power.

This is the single most important asymmetry in the chapter for a portfolio like this one. **The resolution the operator most fears is more likely to arrive as a bond bear market and a flat real decade than as an equity crash.** A portfolio hedged for 2008 is not hedged for 1946.

### 14.3 Where the current cycle sits, stated as observables rather than as a call

The paper does not forecast. It names the observables the framework says to watch, which are all series the system already holds or can hold, so that the tail watch tracks a mechanism rather than a mood:

- Federal debt to GDP, and its trajectory at full employment rather than in recession.
- The deficit as a share of GDP in an expansion — a structural deficit run at low unemployment is the framework's diagnostic, not a cyclical one.
- **Net interest expense as a share of revenue**, and the point at which it exceeds major discretionary categories — the United States crossed the defense-spending threshold in the mid-2020s.
- The share of issuance the central bank and the domestic banking system absorb versus foreign official holders — a falling foreign official share is the framework's early tell.
- The term premium, and whether long yields rise when growth expectations fall — the signature of a market pricing supply rather than growth.
- Real yields versus the inflation rate — the direct measure of whether repression is occurring.
- The gold price against real yields — the historical divergence signal when the market doubts the numéraire, and the Metals paper's central watch.
- Currency debasement measured against a basket of hard assets rather than against other fiat currencies, which can all depreciate together.

Several of these are already in the Monthly's sovereign and liquidity pillars and in the Rate and Liquidity Machine's regime eras. What this chapter asks of the system is that they be *read together as one mechanism* rather than as separate pillar rows, and that the tail watch carry a standing "long-cycle resolution" scenario with the two branches — deflationary and inflationary — as distinct states with distinct instrumentation.

### 14.4 The honest counter-case

The framework has weaknesses the paper states because the Doctrine requires a steelman. Debt-to-GDP thresholds have no demonstrated critical level: Japan has run at roughly twice the U.S. ratio for two decades without the predicted crisis, with yields near zero and a currency that weakened but did not break. Reinhart and Rogoff's ninety-percent threshold did not survive replication. The cycle's timing is unfalsifiable in practice — a forecast that resolves within fifty years is not a tradeable claim. And the strongest counter-argument is the reserve-currency exception: demand for the world's reserve asset is not a normal demand curve, and every historical analogue involves a sovereign that lacked one. **A trader can hold the view that the mechanism is real and the timing unknowable, which is exactly the view the Doctrine's tail-hedge budget is designed to express.**

## Chapter 15 — What protected capital, by resolution type

The chapter's practical payload. No single hedge works across the resolutions, and the most common portfolio error is holding the hedge for the wrong one.

| Resolution | What was destroyed | What protected | The tell that distinguishes it |
|---|---|---|---|
| **Deflationary debt liquidation** (U.S. 1929–32, Japan 1990s, Greece 2010s) | Equities, credit, real estate, banks | **Long government bonds of the solvent sovereign**, cash, gold once revalued | Falling inflation with rising real yields; credit spreads leading equities; the currency *strengthening* |
| **Inflationary deleveraging / repression** (U.S. 1946–51, U.S. 1966–82) | **Bonds and cash in real terms**; long duration worst | Gold, commodities, real assets, equities partially and unevenly; short duration | Nominal yields capped below inflation; negative real yields persisting; gold rising against real yields |
| **Hyperinflation / currency reset** (Weimar 1923, Argentina repeatedly) | Bonds and cash *totally*; domestic savings | Foreign currency, foreign assets, hard assets, equities partially — equity holders retained a fraction of real value where the businesses survived | Fiscal dominance explicit; monetary financing of deficits; capital controls appearing |
| **Expropriation / war** (Russia 1917, China 1949, 1940s Europe) | Everything domestically held | **Assets held outside the jurisdiction** — and only those | Political discontinuity; the risk no financial hedge addresses |

Three readings follow, and they are already consistent with the Doctrine rather than a revision of it.

**The duration sleeve is a deflation hedge, not a hedge.** Book A's Contraction band raises duration for exactly the first row of the table and is the wrong instrument for the second. The correlation table in Chapter 5 is the same fact stated statistically.

**The gold sleeve does the work in the second and third rows**, and its historical record in the first row is good only after policy revalues it. The Metals paper's stock-versus-flow frame and its signal hierarchy are the operative detail.

**The fourth row is not hedgeable inside the account**, and the paper says so plainly rather than pretending. Jurisdictional diversification is a different kind of decision from a portfolio one and sits outside this library's scope.

And the Doctrine's ruling stands unchanged and is, if anything, strengthened by this chapter: **a tail thesis is a hedge budget, not a position.** The historical record says the operator's concern is legitimate and its timing is unknowable, which is precisely the combination that a small, ring-fenced, repeatedly-renewed convex budget expresses correctly and that a standing short expresses catastrophically.

## Chapter 16 — Where these numbers are least trustworthy

**Survivorship, at the level of the country.** The U.S. equity record is the record of the twentieth century's most successful market. Long-run studies of many markets find substantially lower real returns and several total losses — Russia 1917, China 1949, and the interruptions in Germany and Japan. "Stocks always come back over twenty years" is a claim about one country's history.

**Regime dependence.** Every correlation in Chapter 4 is a regime statistic. The stock–bond hedge, the seasonal effects, and the momentum premium each have decade-long failures inside the sample.

**Measurement changes.** Index composition, the arrival of ETFs, decimalization, the growth of same-day options, and the shift of return into the overnight session all mean that a base rate computed since 1928 describes several different markets in sequence. Where the paper gives one figure for a long window, the reader should assume the recent decade differs.

**Small samples in the tails.** Every statement about −40% bears rests on a handful of observations. The honest form of "about every decade" is "four times in a century, irregularly."

**And the base rate is not the forecast.** The Doctrine's edge concept requires knowing the ordinary in order to depart from it; nothing in this paper licenses trading the base rate itself. Its rights in the registry are exactly those of a reference: it may inform a thesis, size an expectation, and set the bar for a variant view. It may not generate a signal, and no metric in this paper is `trigger_eligible`.

---

## Appendix A — The one-page card

*Ordinary:* up 54% of days, 62% of months, 74% of years. Median year +12% total return; a year in the +8–12% band is rare. Realized vol ~15%. Fifty ±1% days a year, ten ±2% days.

*Drawdowns:* −5% three or four times a year; −10% about annually; −20% every four or five years; −30% about every decade. Average intra-year drawdown 14% — in years that finish positive three times in four.

*Inside a bear:* three to five counter-trend rallies of 5%+. The 1929–30 rally was +46%.

*Streaks:* daily direction has no memory. Trend is cross-sectional and multi-week.

*Earnings:* 70–78% beat; the guidance is the news; implied move slightly exceeds realized; front-month IV falls a third to a half overnight.

*Options:* a third expire worthless, a third close early, a third are exercised. ATM theta accelerates as √T. Same-day expiries are about half of index option volume.

*Costs:* single-name out-of-the-money options are 5–15% of premium wide — a tenth of a Book C risk budget in a round trip.

*Percentiles to carry:* annual return p25 −1% / median +12% / p75 +25%. Intra-year drawdown p25 −6% / median −10% / p75 −18%. Bear depth p25 −22% / median −30% / p75 −48%. Recovery p25 5 months / median 2 years / p75 4–5 years.

*Seasonality:* Nov–Apr beats May–Oct by several points on average and fails for years at a time; turn of the month carries a disproportionate share; September is the only negative month on average; **2026 is a midterm year — historically the weakest of the cycle and the one whose low precedes the strongest forward twelve months.** Tiebreaker only; never a thesis.

*Downturn history, thirteen-plus episodes:* median depth ~−30%, median length ~10–12 months; credit and debt-deflation episodes are deepest and longest; the economy is fine at the peak; credit spreads and breadth signal, valuation does not.

*The tail, globally:* p90 −55 to −60% real over a decade or more; p95 −80% with recovery measured in decades (Japan 1989, U.S. 1929); p99 total loss (Russia, China). Deflationary resolutions destroy equities and reward long bonds; inflationary resolutions destroy bonds and reward real assets; **no single hedge covers both**, which is why the tail budget is convex and renewed rather than held.

## Appendix B — Recomputation and provenance

Each table names its window and source class. Figures computed from data the system holds are recomputed annually by a scheduled job and stored as observations with `available_at`, so that a base rate cited in a decision packet can be replayed as of the date it was cited. Figures cited from the literature carry their citation in the claims registry and are re-verified when the paper is revised. Any figure that moves by more than a stated tolerance on recomputation is flagged for review, on the principle that a base rate that changes is itself information.
