# Base Rates

## What Markets Usually Do — and How Far Back "Usually" Goes

**Companion white paper — chester-reports library**
**Series placement:** Companion **XX** — with the market-timing layer, beside *Tops and Bottoms* — per the library guide, which is canonical for numerals; cross-references in this paper are by name
**Version:** 1.4 — September 2026
**Status:** Reference. Consulted before a thesis is written, not after. Figures are recomputed annually and on any methodology change; every number carries its window and its source class.

**Revision, 30 September 2026 (v1.3 → v1.4).** Three changes. (1) **Chapter 3.1's presidential-cycle conditional is restated ex ante.** The v1.3 text measured forward returns *from the midterm-year low*, which is known only in hindsight. It now leads with the election-day form — 19 of 19 midterm years up over the following twelve months against 55 of 73 in all years (0.753) — and flags the low-anchored form as a hindsight statistic. With it the paper adopts a convention for every conditional rate: printed beside its unconditional rate, with both n's. (2) **Part I is the computed tables.** Each figure is the stored `tools/base_rates.py` table value as of 30 September 2026, cited by its `baserate.` id rather than restated by hand. A figure the tables do not compute is labelled cited or illustrative. Several v1.3 prose figures move to their computed values: the daily up-share is 52.4%, not ~54%; a ±2% move comes in 7 sessions in the median year, not 10–12; and a 20% swing decline comes every 3.7 years, not 4–5. (3) **Section 2.4 settles the bear-market count**: twelve computed from the running maximum, thirteen narrated, and which the paper uses for what. The v1.3 erratum below is kept as the record of how the difference was found.

**Erratum, 23 September 2026 (v1.2 → v1.3) — twelve computed, thirteen narrated.** `baserate.drawdown_by_depth` counts **twelve** bear markets where this paper's narrative counts **thirteen**, and the two do not reconcile because they are not the same question. The computed count is episodes of −20% or worse **from the running maximum on closing prices, ^GSPC from 30 December 1927** — one episode per unrecovered decline. Four of the narrated thirteen fall outside it. **1907** predates the series. **1937–38** (−54.5% from its own March 1937 high) and **1946–47** (−28.5%) both sit *inside* the 1929 episode, whose September 1929 peak was not recovered until 22 September 1954: under a running-maximum definition no new episode can open while the old one is unrecovered, which is the same property that makes 1929–32 one −86% event rather than two hundred small ones. And **1990** is a near-miss on closes — **−19.92%** from 16 July to 11 October 1990, eight hundredths of a point short of the rule — which *Tops and Bottoms* includes by near-universal convention and because a recession accompanied it. Three run the other way, computed but not narrated: **1956–57** (−21.5%), **1966** (−22.2%) and **1968–70** (−36.1%), all qualifying on the rule and all falling in the gap between the five mechanism-bearing episodes Chapter 11 selects and the post-1970 roster that starts in 1970. Nine are common to both. **The definition governs the figure:** any number carried under `baserate.drawdown_by_depth` — including the counter-trend-rally row the Monthly prints — is a distribution over the computed twelve, while the narrated thirteen remains the *calibration* sample *Tops and Bottoms* scores against. Where this paper says "thirteen", read: thirteen narrated, twelve computed.

**Erratum, 23 September 2026 (v1.1 → v1.2).** Chapter 1.3's intra-year drawdown quartiles and Chapter 2.2's ~14% average are the **post-1950 subsample**, not the 1928–2026 sample the source notes claimed. Both source notes are corrected and the full-sample figures are given beside them. The difference is the Depression: 1929–32 and 1937–38 put the full sample about three points deeper at every quartile. Found when `tools/base_rates.py` computed the tables from the store and the full sample would not reconcile with the printed figures at any tolerance — the post-war sample reconciled to a tenth of a point. Nothing else in the paper changes; the drawdown ladder in 2.1, the return distributions in 1.1 and the VIX quantiles all reconcile on the sample their notes name.

---

### Reader's note

Every other paper in this library explains a mechanism. This one supplies the denominators. It exists because the Operating Doctrine's central edge concept — variant perception — is arithmetic on a base rate: to hold a view that differs from consensus you must first know what ordinarily happens, and most trading error is a failure of that first step rather than of the second. A trader who does not know that the S&P 500 has closed higher on 52.4% of sessions since 1927 (`baserate.returns_by_frequency|frequencies.daily.positive_share`) will read a three-day losing streak as information. A trader who does not know that a 10% drawdown occurs in most years will treat one as a regime change. A trader who does not know that the median analyst estimate is beaten about three-quarters of the time will read a beat as a surprise.

The paper is deliberately boring, and that is its function. It is a reference to consult *before* writing a thesis, in the way one consults a mortality table before pricing a policy — a comparison the operator will find familiar. Doctrine Rule 6 requires that an edge name its counterparty and say why it persists; this paper is where the claim "and here is what normally happens instead" gets its number.

---

## Executive summary — the twelve things this paper says

*For the reader who will consult the tables later and wants the conclusions now.*

1. **Ordinary is not average.** The post-war interquartile range of a calendar year runs from about 0% to +22% on price, around a median of +12% (Chapter 1.3). A year near the mean is uncommon. Any thesis that needs a "normal year" is a thesis about an uncommon event.

2. **A 10% decline is an annual event, and most years see one.** The average post-war intra-year drawdown is 13.6%, in years that finish positive on price 72.7% of the time; since 1928, 61.6% of years fell 10% or more at some point (Chapter 2.2). Treating a correction as the start of 2008 is the specific mechanism by which the Book A floor gets breached, and this operator's record says he does it.

3. **A bear takes a year to a year and a half to complete (median 15.7 months, peak to trough) and contains several rallies of 5% or more**, the largest of them a median +13.5%, any of which will feel like the bottom. Conviction is unreliable in exactly that window, which is why a short campaign ends on the bottom signal and not on judgment.

4. **The equity premium arrives in a minority of days, and those days cluster inside drawdowns.** Being out of the market during stress is not neutral; it is where the return is forfeited. This is the arithmetic behind the allocation floor.

5. **Daily direction has no memory; trend is a cross-sectional, multi-week phenomenon.** A three-day streak is noise. A name at a twelve-month high with twelve-month relative strength is a documented anomaly. Book B enters on pivotal points, not streaks, for this reason.

6. **Volatility clusters and correlations converge in stress.** The Volatility dial is a state, not a level; diversification weakens exactly when it is being relied on; the heat cap across books counts correlated positions once because in the crisis row they *are* one.

7. **The stock–bond hedge is a regime statistic that one long disinflationary period made look permanent.** 2022 falsified it. The duration sleeve is a deflation hedge specifically — Part IV's central practical claim, arriving here from the correlation table.

8. **Seasonality is real, small, decaying since publication, and never a thesis.** The one exception worth *watching* is the midterm-year cycle — 2026 is one. Measured ex ante from election day, the midterm years were up 19 times in 19 against 55 in 73 for all years, and the effect enters the register as a dated hypothesis, not a signal (Chapter 3.1).

9. **A beat is not a surprise and guidance beats the print.** Three-quarters of companies beat. The tradeable object is the reaction relative to positioning, and the long single option into a print is a negative-expectancy trade on average because the implied move has slightly exceeded the realized move.

10. **Options decay as √T; a third expire worthless, not ninety percent; same-day expiries are half of index option volume.** The verticals-by-default rule follows from decay and from spread cost together — at Book C's size, a wide single-name option can consume a tenth of the risk budget in the round trip.

11. **The U.S. record since 1970 is eight bears, and it excludes the two mechanisms the operator most fears.** Extending to 1907 takes the narrated sample from eight bears to thirteen (the computed count from 1928 is twelve; Chapter 2.4 says why) and adds debt deflation, funding crises outside the regulatory perimeter, and financial repression — the resolution in which bonds, not equities, are destroyed.

12. **The tail the operator worries about sits near the 95th percentile of the historical distribution, not beyond it.** Japan's thirty-four years and 1929's twenty-five are developed-market events within living memory. No single hedge covers both resolutions of a debt cycle. That is why the tail budget is convex and renewed rather than held — and why a portfolio hedged for 2008 is not hedged for 1946.

---

Three conventions run throughout. **Every figure carries its window**, because a base rate computed since 1928 and one computed since 2009 are different claims about different worlds; where the two disagree materially, both are given. **Every figure carries a source class** — measured from data the system holds, computed from public series, or cited from the literature — because the system's registry distinguishes them and so should the reader. And **no figure is a forecast.** A base rate is what happened in a sample; the future is not obliged to resemble it, and Chapter 9 is the honest account of where these numbers are least trustworthy.

The paper has three parts. Part I is the return and drawdown distribution — the shape of ordinary. Part II is the base rates of the events a trading day is made of: gaps, streaks, earnings, expiries, options decay, spread costs. Part III is the historical extension the *Tops and Bottoms* paper does not cover: the downturns before 1970, treated on the same template, because eight bears since 1970 is a sample of eight and the questions this operator asks — how bad can it get, how long, what preceded it — need more.

---

# Part I — The Shape of Ordinary

**How Part I's numbers are written.** Every figure computed from data the system holds comes from the stored tables of `tools/base_rates.py`. Each is printed at the precision the table holds and cited by its id, `baserate.<table>|<field>` — the same id a decision packet cites in `base_rate_cited` — so it can be replayed as of the date it was read rather than retyped. The figures below are the tables as computed on **30 September 2026** (`base-rates-method-1`; ^GSPC closes from 30 December 1927 to 29 September 2026, VIX from 2 January 1990). They are **price returns**: the store holds dividend-unadjusted closes, so an annual figure here is roughly two points below the total-return figure the literature quotes, and where the paper uses a total-return figure it says so and names it as cited. A figure the tables do not compute is labelled with its source class. Each section gives the prose first and the cheat-sheet table after.

**Every conditional rate is printed beside its unconditional rate, with both n's.** A conditional rate alone cannot say whether the condition did anything, and the reader should never have to look up the denominator.

## Chapter 1 — Returns

### 1.1 The distribution, at four frequencies

The S&P 500 closed higher on **52.4%** of the 24,802 sessions since 1927. It rose in **59.6%** of 1,185 months, and in **74.0%** of the 77 post-war calendar years on price alone, against **67.7%** of all 99 years. A coin-flip edge at the daily frequency becomes a three-in-four edge at the annual one: the positive-share column is the cost of sitting out. The operator who is out of the market "waiting for clarity" is declining a three-in-four bet, every year, on the strength of a near coin-flip daily read.

The mean sits below the median at every frequency. The daily median is **+0.05%** against a mean of **+0.03%**; the monthly median is **+0.94%** against a mean of **+0.66%**. The annual price-return mean is **+8.1%** against a median of **+11.8%**. The distribution is left-skewed: a few very bad days pull the average down. That is not a reason to be out. It is the reason the Doctrine has a volatile-day protocol rather than a market-timing rule — the bad days are handled by size, not by absence. For the short side the same column is the base rate against the position — 52% of days, 60% of months, three years in four — and a short thesis must name what makes this the minority case. The Doctrine's extra-confirmation rule for shorts is that requirement made procedural.

Two readings matter most. **The equity risk premium arrives in a minority of the time.** A small number of very good days carry the compounded return. The often-cited finding that missing the best ten or twenty days over a multi-decade span destroys most of the return is real, with the essential companion fact that those days cluster inside drawdowns, adjacent to the worst days. This is the arithmetic behind the Doctrine's Book A floor: being out of the market during stress is not a neutral act. **And the annual mean is not a typical year.** Returns cluster away from their own average, and a year near it is uncommon. Multi-decade rows — rolling ten-year returns positive in roughly 95% of windows, rolling twenty-year windows positive throughout the U.S. sample — are *cited from the long-run literature, not computed here*, and they describe one country that won the century (Chapter 16): use them to size patience, not to promise outcomes. The total-return annual mean of roughly +10% is likewise cited; the computed figure is the price return.

| Horizon | Positive share | Median | Mean | n | Cited as |
|---|---|---|---|---|---|
| Daily | 52.4% | +0.05% | +0.03% | 24,802 sessions | `baserate.returns_by_frequency\|frequencies.daily.positive_share`, `…daily.median`, `…daily.mean` |
| Monthly | 59.6% | +0.94% | +0.66% | 1,185 months | `…\|frequencies.monthly.positive_share`, `…monthly.median`, `…monthly.mean` |
| Calendar year, price, 1928– | 67.7% | +11.8% | +8.1% | 99 years | `…\|frequencies.annual.positive_share`, `…annual.median`, `…annual.mean` |
| Calendar year, price, post-war | 74.0% | +12.3% | +9.6% | 77 years | `…\|frequencies.annual.postwar.positive_share`, `…postwar.median`, `…postwar.mean` |
| Calendar year, total return | ~73–75% | ~+12% | ~+10% | — | *Cited, not computed: the store holds price returns* |
| Rolling 10- / 20-year, nominal | ~95% / 100% (U.S.) | ~+7%/yr | — | — | *Cited from the long-run literature; one country* |

### 1.2 Volatility

The ordinary texture of the market is a ±1% session roughly once a week. The median calendar year since 1928 had **54** sessions with a close-to-close move of 1% or more and **7** with 2% or more, across 99 years. A 1% move is not news, not a signal and not a reason to touch a position; the volatile-day protocol's triggers sit well above it for that reason. The worst single session in the sample, **−20.47%**, is 19 October 1987. VIX's median close since 1990 is **17.58**.

Volatility clusters — the autocorrelation of absolute returns is one of the most robust facts in finance. That is why the Doctrine's Volatility dial is a state rather than a level, and why the volatile-day protocol assumes the next day resembles this one more than it resembles the average. The first ±2% day is the best predictor of the second: reduce on the first, not the third. The operator's record of "periodic damage in extreme volatility" is, mechanically, a record of acting on the third. The calm and stressed columns of the regime view — realized volatility of 8–12% in calm, 20–30% stressed, 40%+ in crisis — are *illustrative regime bands, not computed figures*. The calm column is where Book C's fade-toward-pin setup lives and the stressed column is where it dies: same setup, opposite expectancy, and the trust matrix's regime rows are those columns.

| Measure | Value | n | Cited as |
|---|---|---|---|
| Sessions a year with a ±1% move, median | 54 | 99 years | `baserate.vix_distribution\|move_counts_per_year.abs_1pct.median` |
| Sessions a year with a ±2% move, median | 7 | 99 years | `baserate.vix_distribution\|move_counts_per_year.abs_2pct.median` |
| Worst single session, 1928– | −20.47% (19 Oct 1987) | 24,802 sessions | `baserate.returns_by_frequency\|frequencies.daily.min` |
| VIX median close, 1990– | 17.58 | 9,254 sessions | `baserate.vix_distribution\|level_distribution.median` |
| Realized volatility by regime | 8–12% calm / 20–30% stressed / 40%+ crisis | — | *Illustrative regime bands, not computed* |

### 1.3 Percentiles, not averages

The mean is the least useful summary of any of these distributions, and the paper gives quartiles wherever it can: **p25 / median / p75**, with the mean beside them when the gap between mean and median is itself informative.

The annual row is the one to carry. On price, the post-war calendar year runs from **−0.0%** at p25 to **+21.7%** at p75 around a median of **+12.3%**. On the full sample it runs from **−4.9%** to **+22.4%**. One year in four is roughly flat to down, and a flat year is not a failed year or evidence that a thesis was wrong — it is the lower quartile of ordinary. A position sized so that a flat year is survivable and a +22% year is participated in is sized to the distribution; a position sized to the mean is sized to a fiction. Any thesis whose payoff depends on a "normal year" is a thesis about a rare event.

The intra-year maximum drawdown is stated for **two windows on purpose**. The widely circulated figures are post-war, and the full sample that contains the Depression is materially deeper. Post-war, the quartiles are **−7.6% / −10.3% / −17.2%** of depth, with a mean of **−13.6%**. Since 1928 they are **−7.7% / −13.1% / −20.3%**, with a mean of **−16.2%**. Quote the window with the number or the number means nothing. The p75 matters most for the book: one year in four contains a decline that would trip the Doctrine's Drawdown I switch if it were fully held with no regime response. The bands exist so that it is not fully held when the Volatility dial has already said Stressed. Drawdowns are measured from the running peak *within* the calendar year on closing prices; an intraday measurement is deeper again by a point or more in a volatile year.

VIX's quartiles since 1990 are **13.99 / 17.58 / 22.68**, with **32.92** at p95. A VIX in the low twenties is the upper-ordinary range, not stress. Stress begins near the p95, which is where the volatile-day protocol's threshold sits, on purpose.

| Series | p25 | Median | p75 | Mean | n | Cited as |
|---|---|---|---|---|---|---|
| Daily return | −0.45% | +0.05% | +0.55% | +0.03% | 24,802 | `baserate.returns_by_frequency\|frequencies.daily.p25`, `.median`, `.p75` |
| Monthly return | −1.89% | +0.94% | +3.58% | +0.66% | 1,185 | `…\|frequencies.monthly.p25`, `.median`, `.p75` |
| Annual price return, post-war | −0.0% | +12.3% | +21.7% | +9.6% | 77 | `…\|frequencies.annual.postwar.p25`, `.median`, `.p75` |
| Annual price return, 1928– | −4.9% | +11.8% | +22.4% | +8.1% | 99 | `…\|frequencies.annual.p25`, `.median`, `.p75` |
| Intra-year max drawdown, **1950–** | −7.6% | −10.3% | −17.2% | −13.6% | 77 | `baserate.intra_year_drawdown\|postwar.by_depth.p25`, `.median`, `.p75`, `.mean` |
| Intra-year max drawdown, **1928–** | −7.7% | −13.1% | −20.3% | −16.2% | 99 | `baserate.intra_year_drawdown\|by_depth.p25`, `.median`, `.p75`, `.mean` |
| VIX daily close, 1990– (p95 32.92) | 13.99 | 17.58 | 22.68 | — | 9,254 | `baserate.vix_distribution\|level_distribution.p25`, `.median`, `.p75`; `…\|percentile_grid.95.0` |

## Chapter 2 — Drawdowns

### 2.1 Frequency and duration — the table to memorize

The drawdown ladder counts declines of a given size from a local high, each turn confirmed by the same size (the *threshold-swing* definition — the operator's question of how often a drop of this size is sat through). Since 1928 the index has fallen 5% about **3.4** times a year and 10% about **1.0** times a year. It has fallen 15% about **0.48** times a year, once every two years. A 20% decline has come every **3.7** years and a 30% decline every **7.6** years.

The ladder maps directly onto the Doctrine's switches. A −5% decline three or four times a year is noise the daily switch should never see. A −10% decline about once a year is the correction the weekly and monthly switches are calibrated against. A −20% decline every three to four years is the bear the Drawdown I switch and the regime dials exist for. Each switch is set at a frequency, and the frequencies are these.

| Decline from a local high | Frequency | Median months, peak to trough | Median months to recover | n declines | Cited as |
|---|---|---|---|---|---|
| −5% | 3.42 a year | 0.8 | 1.8 | 339 | `baserate.drawdown_by_depth\|bands.-5%.threshold_swings.full_sample.per_year` |
| −10% (correction) | 1.04 a year | 2.1 | 5.0 | 103 | `…\|bands.-10%.threshold_swings.full_sample.per_year` |
| −15% | 0.48 a year | 3.3 | 7.9 | 47 | `…\|bands.-15%.threshold_swings.full_sample.per_year` |
| −20% (bear) | every 3.67 years | 8.0 | 21.5 | 27 | `…\|bands.-20%.threshold_swings.full_sample.years_between` |
| −30% | every 7.62 years | 16.9 | 33.5 | 13 | `…\|bands.-30%.threshold_swings.full_sample.years_between` |

*The duration columns are the same table's `median_months_peak_to_trough` and `median_months_to_recover_peak` fields for each band.*

The same bears as a *distribution* use a different definition. A bear here is an episode measured from the **running maximum** — the loss from the high-water mark, opening below it and closing only when it is recovered (the portfolio's question). Section 2.4 explains why that gives twelve episodes and the narrated roster thirteen. Across those twelve, depth runs **−26.7% / −33.7% / −48.4%** at p25 / median / p75, and the deepest is **−86.2%** (1929–32). The median bear takes **15.7** months from peak to trough and **17.4** months to recover the prior peak. The largest counter-trend rally inside each decline has a median of **+13.5%** and a p75 of **+18.4%**; the largest of all is **+46.8%** (November 1929 to April 1930).

One bear in four is a halving. The allocation bands' floors are set so that the book participates, and the bands' ceilings so that a halving costs the book its band-weighted share and not the whole. A book that is de-risked at the bottom and waits for "confirmation" will typically miss the first part of a recovery whose median is about a year and a half — which, by Chapter 1's clustering finding, is where a disproportionate share of the return lives. The bottom-signal override exists to force re-entry against this instinct. The counter-trend rally row is the short-seller's table. A short campaign will face several of these, and each will look like the turn. The rule that a short closes on the bottom signal, not on conviction, is written against this row.

| Bear property (running maximum, 12 episodes) | p25 | Median | p75 | Extreme | Cited as |
|---|---|---|---|---|---|
| Depth, peak to trough | −26.7% | −33.7% | −48.4% | −86.2% (1929–32) | `baserate.drawdown_by_depth\|bear_properties.depth_by_depth.p25`, `.median`, `.p75`, `.deepest` |
| Months, peak to trough | 7.6 | 15.7 | 20.6 | 32.3 (1929–32) | `…\|bear_properties.months_peak_to_trough.p25`, `.median`, `.p75`, `.max` |
| Months to recover the prior peak | 10.0 | 17.4 | 50.4 | 265 (1929–54) | `…\|bear_properties.months_trough_to_recovery.p25`, `.median`, `.p75`, `.max` |
| Largest counter-trend rally inside | +9.7% | +13.5% | +18.4% | +46.8% (Nov 1929–Apr 1930) | `…\|bear_properties.largest_counter_trend_rally_pct.p25`, `.median`, `.p75`, `.max` |

*Japan's 34 years to recover its 1989 peak is outside this U.S. table; it is cited in Part IV.*

The operator's stated history includes being under-invested since 2008 and periodically damaged in extreme volatility. Different rows of these tables address each. **A −10% decline is an annual event, not a signal** — treating each as the beginning of 2008 is how the Book A floor gets breached. **And a bear takes the better part of a year and a half to complete** — which is why the Doctrine's Top & Bottom override permits adding at the bottom rather than requiring a call at the top, and why a short campaign that has worked for two months is not thereby vindicated.

### 2.2 Intra-year drawdowns versus annual outcomes

The single most useful fact in this chapter is that the average intra-year maximum drawdown since 1950 is **−13.6%** (77 years). In those same years the index still finished positive on price **72.7%** of the time. A year with a 12% mid-year decline is an ordinary year. This is the base rate against which every "the market is breaking down" thesis must be written.

**The window is part of the fact.** Over the full sample the average is **−16.2%** and the median **−13.1%** (99 years), because the sample then contains 1929–32 and 1937–38. In **61.6%** of all years since 1928 the index fell 10% or more at some point. The post-war figure is the right one for an ordinary year in the regime the operator trades. The full-sample figure is the right one for asking how bad an unusual year can be, and Part III is where that question is answered properly. Neither number is wrong; quoting either without its window is.

The operator's known bias — reading a correction as a regime change — has a numerical antidote. At any −10% the question is not "is this 2008?" but "is this the one year in four where the decline exceeds −17%, and what in the regime dials says so?" If the dials read Calm or Rising, the base rate says buy the dip inside the band, not exit it. The floor is the instrument here: the bands' floors exist so that a −14% year is held through, not traded around.

| Fact | Value | n | Cited as |
|---|---|---|---|
| Average intra-year drawdown, 1950– | −13.6% | 77 years | `baserate.intra_year_drawdown\|postwar.by_depth.mean` |
| Share of those years finishing positive, price | 72.7% | 77 years | `baserate.intra_year_drawdown\|postwar.share_of_years_positive` |
| Average / median intra-year drawdown, 1928– | −16.2% / −13.1% | 99 years | `…\|by_depth.mean`, `…\|by_depth.median` |
| Share of years with a 10% decline, 1928– | 61.6% | 99 years | `…\|share_of_years_with_10pct_drawdown` |

### 2.3 The shape of a decline

Declines are not smooth. Within bear markets, the largest single-day *advances* in history cluster — October 1929, October 2008, March 2020 — and counter-trend rallies of 5% or more are routine. For the operator's short book this means **expecting several rallies of 5% or more inside any −20% decline**, any of which will feel like the bottom. The count of three to five per bear is a reading of the episode record *cited from Tops and Bottoms*, not a computed figure; the computed size of the largest such rally is in 2.1. The Doctrine's rule that a short campaign ends on the Top & Bottom bottom signal rather than on conviction exists because this base rate makes conviction unreliable in exactly this window.

The best days live inside the worst months. That is why "sell now, buy back when it's calmer" underperforms holding through: the buy-back happens after the days that mattered. For the short book, size for five rallies, not one. A short sized so that a single +10% counter-trend rally trips its stop will be stopped out of a correct thesis several times per bear, and Book B's short rules are written against this. For the long book, the rally is not the signal. A +13% bounce is the *median* largest rally inside a bear and carries no information about the bottom; the bottom signal is the composite, not the rally.

### 2.4 Twelve or thirteen: what counts as a bear market

The paper counts bear markets two ways, and the counts differ because the definitions do.

**The computed count is twelve.** `baserate.drawdown_by_depth|bear_properties.n` counts episodes of −20% or worse **from the running maximum on closing prices**, ^GSPC from 30 December 1927. An episode opens when the index falls below its high-water mark and closes only when that mark is recovered, so no new episode can open while an old one is unrecovered. The same property makes 1929–32 one −86% event rather than a string of smaller ones.

**The narrated roster is thirteen.** It is the five pre-1970 episodes Chapter 11 tells (1907, 1929–32, 1937–38, 1946–47, 1961–62) plus the eight bears since 1970 that *Tops and Bottoms* treats. Nine episodes are in both lists. Four narrated episodes fall outside the computed twelve:

- **1907** predates the series.
- **1937–38** (−54.5% from its own March 1937 high) and **1946–47** (−28.5%) both sit *inside* the 1929 episode, whose September 1929 peak was not recovered until 22 September 1954.
- **1990** is a near-miss on closes, at **−19.92%** from 16 July to 11 October 1990 — eight hundredths of a point short of the rule. *Tops and Bottoms* includes it by near-universal convention and because a recession accompanied it.

Three run the other way, computed but not narrated: **1956–57** (−21.5%), **1966** (−22.2%) and **1968–70** (−36.1%). All three qualify on the rule, and all three fall between the episodes Chapter 11 selects and the post-1970 roster.

**This paper uses the computed twelve for every figure.** Every number carried under a `baserate.` id — the bear-property distribution in 2.1, and the counter-trend-rally row the Monthly prints — is a distribution over the twelve. The reason is that a figure cited by id must be reproducible from data by a stated rule, and the narrated roster is a selection: it includes episodes by mechanism and convention, and the series cannot recompute it. The thirteen remains the *calibration* sample *Tops and Bottoms* scores its signals against, and Part III's narrative uses it, because there the question is what each episode's mechanism teaches rather than how often a rule fires. Where this paper says "thirteen", read: thirteen narrated, twelve computed.

A third count exists and is not a bear count at all. The threshold-swing ladder in 2.1 records **27** declines of 20% from a *local* high since 1928 (`…|bands.-20%.threshold_swings.full_sample.declines`). A swing confirmed from a local high can open inside an unrecovered episode, so it counts every −20% leg rather than every new loss from the high-water mark. It is the right definition for "how often is a drop this size sat through" and the wrong one for "how many bear markets".

| Definition | Count, 1928– | Use in this paper | Cited as |
|---|---|---|---|
| −20% from the running maximum, closes | 12 | Every computed bear figure | `baserate.drawdown_by_depth\|bear_properties.n` |
| Narrated roster (Chapter 11 + *Tops and Bottoms*) | 13 (incl. 1907) | Part III's narrative; the calibration sample | *Narrated, not computed* |
| −20% threshold swings from a local high | 27 | The frequency ladder in 2.1 | `…\|bands.-20%.threshold_swings.full_sample.declines` |

## Chapter 3 — Seasonality

Seasonality is the part of this paper most likely to be misused, so the chapter states the research, the decay, and the ruling in that order.

### 3.1 What the research actually found

**The Halloween effect (November–April versus May–October)** is the most robust of the calendar anomalies. Bouman and Jacobsen's 2002 study found November–April outperformance in the large majority of the thirty-seven markets they examined, and later work extending the U.K. record back roughly three centuries found the pattern present across most of that span. The average gap in modern U.S. data is on the order of several percentage points a year, and — unusually for an anomaly — it has not disappeared since publication, though it has weakened and has failed for multi-year stretches.

**The turn of the month.** Ariel (1987) and Lakonishok and Smidt (1988) documented that the last trading day of a month plus the first three of the next capture a disproportionate share of monthly return — in some samples, more than the entire month's return, with the remaining days net negative. The mechanism is plausible and mechanical: salary and pension contributions, index-fund inflows, and month-end rebalancing all land in that window, which is the Positioning & Flows paper's territory.

**The January effect** — small-cap outperformance in early January, attributed to tax-loss-selling reversal — was strong through the 1970s and has substantially decayed since publication, which is the canonical example of an anomaly being arbitraged once documented.

**September** is the only month with a negative average return in most long U.S. samples, and volatility seasonality peaks in September–October, which is where several of the historical crashes sit. Whether the crash cluster causes the statistic or the statistic is the crash cluster is unresolved; the honest reading is that a five-episode cluster in a century is a small sample making a monthly average look worse than the typical September felt.

**The presidential cycle** is the seasonal effect with the most immediate relevance. In the post-war U.S. record, the third year of the cycle has been the strongest by a wide margin and the second — the midterm year — the weakest, with the largest average intra-year drawdown of the four.

**The conditional is stated ex ante: from election day.** Measured from the close on midterm election day to the close twelve months later, the S&P 500 rose in **19 of 19** post-war midterm cycles (1950–2022). The median gain was **+14.5%** and the quartiles **+8.9% / +20.9%**. The same anchor in every year rose **55 times in 73**, a rate of **0.753**, and in the non-midterm years **36 times in 54**, or **0.667**. The probability of 19 in 19 at the all-years rate is **0.005**. A second window, from 1 October of the midterm year to 31 March of the next — the cycle's historically strongest stretch — rose in **17 of 19** midterm cycles against **51 in 73** across all years (**0.699**). The effect survives being measured without hindsight. Its measured size is the one above, and it carries a binomial p beside it because a 19-year sample is small.

**The "from the midterm-year low" version is a hindsight statistic and is not used.** The widely quoted form of this effect measures forward returns *from the midterm year's low*. That low is known only after it has happened — it is fixed on 31 December of the midterm year — and any series measured from its own minimum rises. On ^GSPC closes that form makes 18 of the 19 post-war cycles clear +15% in the following twelve months, which is a selection artefact, not a rate, and no one could have traded it. The paper records it so a reader who meets it elsewhere knows what it is, and leads with the election-day form instead.

**2026 is a midterm year.** That places the current calendar in the weakest quarter of the cycle and, if the pattern holds, ahead of its strongest. The paper records this as context rather than as a forecast. The narrative register's two dated midterm hypotheses — entered at the close of 30 September 2026 at priors shrunk toward the all-years rates, never 0 or 1 — cite this section for the statement and the table for every number. The prediction-market engine's midterm contracts will price the same question independently.

**Day-of-week, holiday, and expiry effects** are smaller. The Monday effect has largely vanished; pre-holiday sessions retain a mild positive drift; monthly expiry week carries a small positive tilt whose sign is unstable.

| Window (S&P 500, close to close, 1950–2022 midterms) | Midterm years | All years, same window | Non-midterm years | Binomial p (midterm count at the all-years rate) | Cited as |
|---|---|---|---|---|---|
| Election day → twelve months later | 19 / 19 (1.000), median +14.5% | 55 / 73 (0.753) | 36 / 54 (0.667) | 0.005 | `baserate.midterm_from_election\|primary`, `…\|primary_unconditional.all_years`, `…\|primary_unconditional.non_midterm_years` |
| 1 Oct of the midterm year → 31 Mar of the next | 17 / 19 (0.895), median +14.6% | 51 / 73 (0.699) | 34 / 54 (0.630) | 0.045 | `…\|secondary`, `…\|secondary_unconditional.all_years`, `…\|secondary_unconditional.non_midterm_years` |
| *From the midterm-year low (hindsight)* | *18 / 19 clear +15%* | — | — | — | *Not a rate: the anchor is known only after the fact* |

### 3.2 The decay problem

McLean and Pontiff's work on published anomalies found that returns decay materially after publication — roughly a third out-of-sample, and more than half once in-sample overfitting is accounted for. Every effect in 3.1 has been published for decades. The prior should therefore be that each is smaller now than in the study that found it, and that some are gone.

### 3.3 The ruling

Seasonality is **a tiebreaker at the margin of an existing thesis, never a thesis.** It may shade the size tier within its band or the timing of an entry already justified on other grounds. It may not generate a packet, and every seasonal metric enters the registry `trigger_eligible: false` permanently — not pending evidence, but by construction, because a calendar effect has no counterparty story that survives Doctrine Rule 6. The presidential-cycle conditional is the one exception worth watching rather than trading: it is a *positioning* statement about a crowded consensus in an election year, and it belongs to the register as a hypothesis with a dated entry, graded like any other.

## Chapter 4 — Trends, streaks, and mean reversion

Daily direction has almost no memory. The probability that a session closes up **given that the previous session closed up** is **54.2%**. The unconditional probability of an up close is **52.4%**, and after a down close it is **50.4%**. The conditional n is the roughly 13,000 sessions that followed an up close; the unconditional n is all 24,802. The lag-one autocorrelation of daily returns is **−0.014**. A two-point tilt in a coin is not a trend.

Streaks are coin sequences. Two up sessions in a row occur **28.5%** of the time, three **15.1%** and five **4.1%** — five in a row happens about one week in twenty-five by chance. The longest run since 1928 is **14** up sessions and **12** down. A streak is not momentum, not exhaustion, and not a reason to act in either direction.

**Trend persistence is a cross-sectional and multi-week phenomenon, not a daily one.** A name at a twelve-month high with twelve-month relative strength is a documented anomaly. Cross-sectional momentum (twelve months less one) has positive expectancy over most decades and crashes violently after bear-market bottoms; single names show weakly negative one-month autocorrelation (the short-term reversal effect). These are *cited from the literature*. The Doctrine's Book B entry at a pivotal point rather than on a streak follows directly, and momentum's crash after bear bottoms is the trust matrix's "momentum: Off after a bottom signal" row — the strategy that works for most of the cycle is the one that loses most at the turn.

**Gaps and the overnight session are absent from the computed tables, with a reason.** A gap is the open against the prior close, and the store holds closes only, so `baserate.streaks_and_gaps` reports the gap-fill and overnight-versus-intraday rows as `not_yet_sourced` rather than computing a two-day return under the wrong name. The literature's readings stand as *cited*:
- Since the 1990s most of the index's cumulative return has accrued overnight rather than in regular hours. That is the Daily Cascade's reason to exist: the 07:00 report reads a session that has already happened.
- Small gaps (under 0.5%) fill the same session more often than not; large gaps (over 1%) fill the same day well under half the time. A Book C fade of a 1.5% gap is a below-coin-flip bet before positioning is considered, so the setup requires the positioning read to move it above.

| Pattern | Value | n | Cited as |
|---|---|---|---|
| P(up \| previous session up) — *conditional* | 54.2% | ~13,000 sessions after an up close | `baserate.streaks_and_gaps\|p_up_given_up` |
| P(up) — *unconditional* | 52.4% | 24,802 sessions | `baserate.streaks_and_gaps\|p_up` |
| P(up \| previous session down) | 50.4% | ~11,800 sessions after a down close | `baserate.streaks_and_gaps\|p_up_given_down` |
| Two / three / five up sessions in a row | 28.5% / 15.1% / 4.1% | 24,802 | `…\|runs.p_2_consecutive_up`, `…\|runs.p_3_consecutive_up`, `…\|runs.p_5_consecutive_up` |
| Longest run, up / down | 14 / 12 sessions | 24,802 | `…\|longest_up_run`, `…\|longest_down_run` |
| Gap fill; overnight vs intraday | absent | — | `not_yet_sourced`: the store holds closes only |
| Momentum, 12–1 cross-sectional; 1-month reversal | positive expectancy, crashes after bottoms; weakly negative | — | *Cited from the literature* |

## Chapter 5 — Correlation and diversification

The base rate that governs Book A's duration sleeve is that **the stock–bond hedge is regime-dependent, and it was negative for one unusually long disinflationary period.** Through the disinflationary calm typical of 1998–2020, the S&P 500 and the 10-year Treasury correlated between about −0.3 and −0.5. In the inflationary regimes of the 1970s and 2022 the correlation ran between about +0.2 and +0.6. In a crisis bonds usually rally, but not always — 2022, and the March 2020 dash-for-cash days. Sizing a duration sleeve as a hedge on the 1998–2020 correlation is sizing on a sample that 2022 falsified. Ask which regime you are in before sizing the hedge. In the disinflationary row, duration hedges equity; in the inflationary row, it amplifies the loss. The Macro dial's Overheat and Tightening states are the inflationary row, and the Doctrine's bands cut duration in exactly those states for this reason.

Average pairwise stock correlation runs about 0.20–0.35 in calm, 0.35–0.50 in inflationary regimes and 0.60–0.85 in crisis. Pairwise correlation that high in crisis means a portfolio of ten names is roughly one position. That is why the Doctrine caps heat across books at a common factor, and why the heat calculator counts correlated positions once: six long semiconductors and a long NQ call spread is one trade with three tickers. The crisis row is also the International Equities paper's diversification finding: correlations converge in joint downside moves and not in joint upside, so the insurance is against the single-country tail, not the bad quarter.

**These correlation figures are cited, not computed.** `baserate.correlation_by_regime` computes the stock–bond and pairwise correlations by volatility band, but only over the store's bond history, which reaches back about five years. Its rows state their own windows and n's, and a long-run regime table cannot come from them. The long-run figures below are from the literature until the store's history can carry them.

| Regime | S&P 500 / 10-year Treasury correlation | Average pairwise stock correlation | Source class |
|---|---|---|---|
| Disinflationary calm (1998–2020 typical) | −0.3 to −0.5 | 0.20–0.35 | *Cited* |
| Inflationary (1970s; 2022) | +0.2 to +0.6 | 0.35–0.50 | *Cited* |
| Crisis | Bonds usually rally, but not always (2022; March 2020) | 0.60–0.85 | *Cited* |

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

Adding these five to the eight post-1970 episodes gives the **thirteen-episode narrated roster** — not the twelve the computed table counts from the running maximum, for the reasons the erratum above sets out — and roughly doubles the calibration sample and — more importantly — adds three mechanism families that the post-1970 set contains weakly or not at all: pre-Fed liquidity crisis, debt deflation, and financial repression.

## Chapter 12 — What the extended sample changes

**Depth.** Across the thirteen-plus narrated episodes (Chapter 2.4 explains why the computed count is twelve and the computed median −33.7%), the median bear is about −30% and the interquartile range roughly −25% to −50%. The post-1970 sample alone understates the left tail because it excludes 1929 and 1937.

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

*Ordinary:* up 52.4% of sessions, 59.6% of months, 74.0% of post-war years (price). Median post-war year +12.3% price (~+12% total return, cited). The median year has 54 ±1% sessions and 7 ±2% sessions.

*Drawdowns:* −5% 3.4 times a year; −10% about annually (1.04); −20% every 3.7 years; −30% every 7.6 years (threshold swings). Average post-war intra-year drawdown −13.6%, in years that finish positive 72.7% of the time.

*Inside a bear:* several counter-trend rallies of 5%+; the largest is a median +13.5%. The 1929–30 rally was +46.8%. Twelve bears computed from the running maximum since 1928, thirteen narrated (Chapter 2.4).

*Streaks:* daily direction has no memory: P(up | up) 54.2% against P(up) 52.4%, n ≈ 13,000 and 24,802. Trend is cross-sectional and multi-week.

*Earnings:* 70–78% beat; the guidance is the news; implied move slightly exceeds realized; front-month IV falls a third to a half overnight.

*Options:* a third expire worthless, a third close early, a third are exercised. ATM theta accelerates as √T. Same-day expiries are about half of index option volume.

*Costs:* single-name out-of-the-money options are 5–15% of premium wide — a tenth of a Book C risk budget in a round trip.

*Percentiles to carry:* post-war annual price return p25 −0.0% / median +12.3% / p75 +21.7%. Post-war intra-year drawdown p25 −7.6% / median −10.3% / p75 −17.2%. Bear depth p25 −26.7% / median −33.7% / p75 −48.4%. Recovery of the prior peak p25 10 months / median 17 months / p75 50 months.

*Seasonality:* Nov–Apr beats May–Oct by several points on average and fails for years at a time; turn of the month carries a disproportionate share; September is the only negative month on average; **2026 is a midterm year — historically the weakest of the cycle. From election day, the following twelve months were up in 19 of 19 midterm years against 55 of 73 years overall (0.753); the "from the midterm-year low" form is hindsight and is not used.** Tiebreaker only; never a thesis.

*Downturn history, thirteen-plus episodes:* median depth ~−30%, median length ~10–12 months; credit and debt-deflation episodes are deepest and longest; the economy is fine at the peak; credit spreads and breadth signal, valuation does not.

*The tail, globally:* p90 −55 to −60% real over a decade or more; p95 −80% with recovery measured in decades (Japan 1989, U.S. 1929); p99 total loss (Russia, China). Deflationary resolutions destroy equities and reward long bonds; inflationary resolutions destroy bonds and reward real assets; **no single hedge covers both**, which is why the tail budget is convex and renewed rather than held.

## Appendix B — Recomputation and provenance

Each table names its window and source class. Figures computed from data the system holds are recomputed annually by a scheduled job and stored as observations with `available_at`, so that a base rate cited in a decision packet can be replayed as of the date it was cited. Figures cited from the literature carry their citation in the claims registry and are re-verified when the paper is revised. Any figure that moves by more than a stated tolerance on recomputation is flagged for review, on the principle that a base rate that changes is itself information.
