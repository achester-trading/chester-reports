# Evidence and Inference

## How to Read Your Own Ledger

**Companion white paper — chester-reports library**
**Series placement:** with the positioning and book layer, immediately before *Building and Validating a Systematic Book* (numeral assigned by the library guide on commit; cross-references by name)
**Version:** 1.0 — September 2026
**Status:** Doctrine-adjacent. Governs how every figure the register prints is to be read. The HTML edition is canonical — the figures live only there.

---

### Reader's note

Every other paper in this library is written to increase the operator's confidence in something. This one is written to calibrate it. It exists because the system's entire output is a ledger, the Doctrine promises to change its rules on that ledger's evidence, and nothing yet says what the evidence can bear.

The paper's central claim is uncomfortable and is stated once here so that nothing later softens it: **for a book of this size and cadence, most of the questions the operator wants to ask of his own results cannot be answered by those results — not "not yet," but ever.** A discretionary book making three to five decisions a week produces perhaps two hundred a year. With ordinary per-trade noise, two hundred decisions cannot distinguish a good process from a break-even one. The correct response is not despair. It is to know which questions the data can settle, to lean on mechanism and prior evidence for the rest, and to stop treating a thirteen-week number as a verdict.

The paper is deliberately short on algebra and long on pictures. Part I is what a number means — the error bars on everything the register prints. Part II is the catalogue of ways a careful person fools himself with a ledger. Part III is what to do instead: how to weigh mechanism against data, how a shadow outcome multiplies the sample, and a chapter-length honesty table on which of the register's cuts will ever be decidable. Part IV applies the whole to sizing and to edge decay.

Written before the register has results, on purpose. Written afterward, it would be an argument against conclusions already drawn.

---

# Part I — What a Number Means

## Chapter 1 — The standard error of everything

Every figure the register prints — expectancy, hit rate, average winner and loser, Sharpe ratio — is an estimate from a sample, and every estimate has an error bar. The error bar is the paper's only real subject.

For an average of *n* independent observations with spread *σ*, the standard error is *σ* divided by the square root of *n*. Trading results have a per-decision spread close to one R — a winner and a loser differ by roughly a full unit of risk — so the standard error of measured expectancy is roughly 1 ÷ √n in R. The ninety-five percent interval is about twice that on either side.

*[Figure 1 — computed figure; rendered in the HTML edition]*

The figure is the paper compressed. An edge of 0.2R per decision — a good process by any standard — measured over the Doctrine's thresholds:

| Decisions | Standard error | 95% interval on a true 0.2R edge | What can be said |
|---|---|---|---|
| 30 | ±0.18R | −0.16R to +0.56R | Nothing. Could be losing; could be excellent |
| 50 | ±0.14R | −0.08R to +0.48R | Nothing |
| 150 | ±0.08R | +0.04R to +0.36R | Barely positive, at the edge of the interval |
| 200 (≈ one year) | ±0.07R | +0.06R to +0.34R | Positive, magnitude unknown by a factor of six |
| 400 (≈ two years) | ±0.05R | +0.10R to +0.30R | Positive; magnitude known within a factor of three |
| 1,000 (≈ five years) | ±0.03R | +0.14R to +0.26R | Known |

**The Doctrine's thirty-and-fifty thresholds are minima for the crudest question — is the sign positive — and are far too small for any interesting one.** A year of disciplined trading cannot exclude zero. Two years establish the sign and leave the magnitude open by a factor of three. The paper's first instruction follows: every figure the register prints carries its sample size *and its interval*, and the interval is read before the point.

## Chapter 2 — The Sharpe ratio's error bar

The Sharpe ratio is the number most likely to be quoted and least likely to be quoted with its uncertainty. For an annualized Sharpe *S* estimated from *T* years of data, the standard error is approximately √((1 + S²/2) ÷ T) — in the same units as the estimate.

*[Figure 2 — computed figure; rendered in the HTML edition]*

A Sharpe of 1.0 measured over one year has a standard error of about 1.2: the estimate is smaller than its own error bar, and zero sits comfortably inside the interval. Over five years the error falls to about 0.55 and a Sharpe of 1.0 becomes distinguishable from zero at ordinary confidence. Over ten, the interval is roughly 0.6 to 1.4.

The reframing this forces is general. **Every performance figure the operator will ever read — a fund's, a strategy's, a newsletter's, his own — carries an error bar most quoters omit, and for anything under five years the error bar is roughly the size of the number.** The Doctrine's promotion gates at 150 decisions across two regimes are, in these terms, permission to believe the sign, not the size.

## Chapter 3 — Effective sample size

The formulas above assume independence, and trades are not independent. Six long semiconductor positions entered in the same week on the same thesis are closer to one observation than to six: they share a factor, they share a regime, and they will share an outcome. The register's mechanism-group tagging exists for the confluence guard, and it does the same work here — decisions sharing a mechanism group and a window count once toward the sample.

The discount is large. A book that makes 200 decisions a year in clusters of three or four on shared themes has an effective sample closer to 60. The honest interval on a year's expectancy is therefore not the ±0.07R of Chapter 1 but something nearer ±0.13R. **The Doctrine's heat rule — correlated positions count once at their common factor — is a risk rule and a statistics rule at the same time, and the register should compute effective n rather than raw n wherever it prints a figure.**

## Chapter 4 — Regime is a sample size too

This is the chapter the operator most needs and will find least intuitive.

The Doctrine's most important cut is performance by regime, because that is how the trust matrix is revised. But two hundred decisions made inside a single bull market are, on the question "does this work across regimes," a sample of **one** — one regime, observed two hundred times. The number of regime-observations, not the number of decisions, bounds what can be said about regime dependence, and regimes arrive at a rate of a few per decade.

The consequence is severe and unavoidable: **the cut the Doctrine cares about most is the one the data will be thinnest on, permanently.** In three years the register may hold a thousand decisions and two or three regime states, with perhaps thirty decisions in the least common. No statistical method repairs that. What repairs it is the same thing that repairs every small-sample problem in this paper — mechanism, prior evidence from history, and the discipline of not concluding.

The practical rule: a regime cut with fewer than thirty decisions in it prints its figures in grey with "insufficient" beside them, and the trust matrix does not move on it. The Doctrine already says this; this chapter is why.

---

# Part II — How to Fool Yourself

## Chapter 5 — The garden of forking paths

Test twenty candidate rules at the conventional threshold and one of them "works" by chance. The operator will not run twenty formal tests. He will do something worse: adjust a threshold, look at the result, adjust again, look again — and stop when it looks good. That is the same twenty tests without the paper trail, and its false-discovery rate is identical.

The remedy is the one the register already applies to decisions: **pre-declaration.** A hypothesis is written before its test — what is claimed, what would confirm it, what sample size decides it — and is graded against that declaration, never against a threshold found afterward. The Part 29 additions entered the register as dated hypotheses for this reason; the pin log's tolerance was fixed in advance for this reason; and the register's supersession rule, which forbids editing a decision after the fact, is this chapter enforced in a schema.

## Chapter 6 — Overfitting, and why a declared threshold matters

An in-sample result overstates the true effect, and the overstatement grows with the number of configurations tried. A strategy that looks best among a hundred variants is, on average, a good deal worse than it looks — the deflation is a function of how many things were tried, which is why the count of things tried must be recorded.

The system's own gates are the illustration. When the data-quality gates falsely excluded every symbol on their first run, the cause was traced to an input bug and **no threshold was touched**; the commit history shows each threshold appearing exactly once. That history is what makes the pin log's base rate honest: a base rate measured against a tolerance that was never tuned to make it look better is a base rate a reader can trust. Had the tolerance been widened until the hit rate looked respectable, the resulting number would describe the tuning, not the market.

The general rule: **the number of things tried is part of the result**, and a result that does not report it should be discounted by a reader's guess at it.

## Chapter 7 — Survivorship and look-ahead, at the strategy level

*Base Rates* treats survivorship at the level of countries — the markets that went to zero and left the record. The same bias operates at the level of strategies and instruments: the rules a trader remembers are the ones that worked, the names in today's index are the ones that survived, and a backtest on the current index membership is a backtest on winners.

Look-ahead is subtler and the system has already spent real engineering on it. The point-in-time store's three clocks and its as-of join exist so that no report, no draft, and no replay can see a value before it was knowable. Chapter 3 of the *Systematic Book* paper gives the mechanism; this chapter gives the statistical reason: **a result computed with information the decision could not have had is not a result, it is a fabrication with a correct-looking decimal.** The migrated macro rows, whose availability timestamps are upper bounds, are flagged in the store for exactly this reason and are treated as stale by the freshness check until repaired.

## Chapter 8 — Outcome bias, and the seven categories

A good decision can have a bad outcome and a bad decision a good one, and a trader who grades decisions by outcomes will learn the wrong lessons with great confidence. The register's closing decomposition — forecast, timing, expression, sizing, execution, exit, process — exists to separate the two, and this chapter is its theory.

The distinction is operational, not philosophical. A decision made by the rules, sized by the tier, with a written invalidation, that lost because the regime changed mid-trade is a *process success* and a *regime-change outcome*; it goes to the transition rules, not to the operator's confidence. A decision that broke a rule and won is a *process failure* with a lucky outcome; it goes to the rule-break count, and the win is not evidence for anything. **The register grades the decision on the seven fields and the ledger grades the process on the count of each; the P&L is a by-product that the Doctrine correctly calls noise at the weekly horizon.**

---

# Part III — What to Do About It

## Chapter 9 — Bayes for traders, in sentences

A belief before evidence, updated by evidence, yields a belief after. The strength of the belief before determines how much the evidence moves it, and thirty observations move a strong prior very little.

*[Figure 3 — computed figure; rendered in the HTML edition]*

The figure shows three traders watching the same thirty decisions from a process whose true hit rate is 60%. The trader with a weak prior — willing to believe almost anything — is at 58% after thirty and close to the truth by a hundred. The sceptic, whose prior is equivalent to having already seen eighty decisions at 50%, has moved to 53% after thirty and needs several hundred observations to arrive. The third trader started at 60% *because the mechanism said so* — a named counterparty, a reason for persistence — and the data merely confirmed what he already had reason to believe.

Three readings. **The data does not speak for itself; it speaks against a prior, and the prior's provenance matters.** A prior built from a mechanism and a documented analogue is legitimately stronger than one built from hope, and the same thirty observations mean more for it. **A sceptical prior is the right default for anything without a mechanism**, and it will take longer to persuade than the operator's patience. **And the strength of a prior should be recorded** — the register's hypothesis entries carry a stated confidence for exactly this reason, so that the update can be honest about what it started from.

## Chapter 10 — Mechanism as evidence

The Doctrine's Rule 6 requires that an edge name its counterparty, explain who is on the other side, and say why it has not been arbitraged away. This chapter is the formal case that those three answers *are evidence*, in the Bayesian sense, and not merely rhetoric.

A claim that survives the three questions has independent support: it is consistent with a documented mechanism (dealers must hedge; pensions must rebalance; a borrow that vanishes must be covered), it has a historical analogue (the paper's cases), and it has a reason the counterparty will keep paying. Each of those raises the prior. A claim without them — "this pattern has worked" — starts from the sceptic's prior and needs more data than the book will ever generate.

The practical consequence inverts the usual ordering. **The operator should decline mechanism-free ideas at the outset rather than testing them forever**, because the test cannot conclude. And he should be willing to act on mechanism-backed ideas at sample sizes that would be reckless for mechanism-free ones, because the prior is doing legitimate work. The trust matrix's rule that nothing enters at High is consistent with this: a mechanism earns Medium; only data earns High; and most rows will never see enough data to get there, which is fine, because Medium with a mechanism is a tradeable state.

## Chapter 11 — The shadow outcome as a sample multiplier

The single largest available increase in the register's evidential power costs no additional trades.

The shadow-outcome grader computes, for every decision at its declared horizon, what it would have returned from stored prices — taken, declined, and drafted-but-untraded alike. A book that trades two hundred times a year but *decides* seven hundred times — three declines and a draft for every take — has seven hundred graded decisions, not two hundred. Effective sample size is still discounted for correlation, but the multiplier is real: the interval on expectancy narrows by roughly √3.5, and questions that were undecidable at two hundred become decidable at seven hundred.

Two further gains. **Declines are graded**, so the operator's veto is audited — the count of profitable declines is the measurement of a bias the Doctrine names. **And drafts grade the reports**, because a report that drafts packets is forecasting whether or not anyone trades them, and the shadow outcomes of its drafts, cut by regime, are its calibration. The pin log already does this for the dealer family; the shadow grader does it for every owning report.

This chapter is the paper's strongest practical argument. It justifies the grader on statistical grounds alone, independent of the learning-loop argument the *Systematic Book* paper makes, and it is why that step of Track D should not slip.

## Chapter 12 — Sequential decisions, and when to stop

A rule that is watched "a little longer" every time it looks marginal is a rule that never gets retired, because the stopping decision is being made by the same hope that started it. The remedy is a pre-declared review point: a sample size or a date at which the hypothesis is graded, fixed when the hypothesis is written.

And when the answer at the review point is "still unknowable" — which, by Chapter 1's arithmetic, it often will be — the response is not to extend the test but to **shrink the position.** A rule whose edge cannot be established in the time available is a rule to run at half size while it continues to accumulate evidence, not one to run at full size while hoping. The Doctrine's champion-and-challenger process is this chapter's mechanism: the challenger runs in paper for size-increasing changes and in production for restricting ones, at a declared sample, and is promoted or withdrawn at a session.

## Chapter 13 — Reading the register's cuts honestly

The table this chapter exists for. Each row is a cut the register will print; each column is a horizon; each cell is the honest sample size and a judgment — **decidable**, **suggestive**, or **never** — for the question "is the expectancy in this cut positive."

| Cut | 3 months | 1 year | 3 years | Verdict at 3 years |
|---|---|---|---|---|
| All decisions, all books | ~50 | ~200 (≈700 with shadows) | ~600 (≈2,000) | **Decidable** — sign and rough magnitude |
| Book B alone | ~15 | ~60 | ~180 | Suggestive — sign likely |
| Book C alone | ~25 | ~100 | ~300 | Decidable for sign |
| Book D alone | ~5 | ~25 | ~75 | Suggestive at best |
| Long vs short | ~25 / ~25 | ~100 / ~100 | ~300 / ~300 | Decidable — the difference between them, suggestive |
| With-trend vs counter-trend | similar | similar | similar | As above |
| By regime — most common state | ~35 | ~140 | ~400 | Decidable |
| By regime — least common state | ~0–5 | ~15 | ~50 | **Never**, on its own; mechanism must carry it |
| By signal family, per family | ~5–10 | ~20–40 | ~60–120 | Suggestive for the largest families; never for the rest |
| By expression family | ~10 | ~40 | ~120 | Suggestive |
| Regime × book × direction | ~1–5 | ~5–20 | ~15–60 | **Never** |

*Sample sizes assume the Doctrine's Phase 1 cadence and count decisions, not effective n; discount by roughly a third for correlation. Shadow outcomes multiply the top rows by three to four.*

The table's message is not that measurement is futile. It is that **the register will decide perhaps five questions in three years and suggest answers to ten more, and the operator should know in advance which they are** — so that the numbers he sees at Christmas are read as the descriptive statistics they are, and so that the questions in the "never" rows are answered the only way they can be, by mechanism and by the history in the rest of the library.

---

# Part IV — Application

## Chapter 14 — Kelly, and why the Doctrine sizes far below it

The Kelly criterion gives the bet size that maximizes long-run growth: for a bet won with probability *p* at odds *b*, the fraction is *p* − (1−*p*)/*b*. At a 55% hit rate on even payoffs it is 10% of capital per bet. The Doctrine's standard Book B risk is 0.75%.

The gap is deliberate and this chapter defends it. Kelly assumes four things, and a discretionary book violates all four: that the edge is *known* (it is estimated, with the error bars of Part I); that bets are *independent* (they cluster, Chapter 3); that the bettor has *logarithmic utility* and is indifferent to drawdown (the Doctrine's switches say otherwise); and that bets are *infinitely divisible and repeatable* (they are neither).

*[Figure 5 — computed figure; rendered in the HTML edition]*

The figure shows the first violation alone. When the edge estimate carries uncertainty comparable to its size — which Part I says it will for years — the growth-optimal fraction collapses toward a fraction of full Kelly, and at the uncertainty levels a two-hundred-decision sample implies, it sits near or below quarter-Kelly. **The Doctrine's sizing is not conservative relative to Kelly; it is approximately Kelly-optimal once the edge's uncertainty is admitted.** The promotion gates that allow tiers to rise as the register accumulates are the mechanism by which sizing tracks the narrowing error bar — never reaching full Kelly, because the error bar never reaches zero.

## Chapter 15 — Edge decay: a fading edge or a bad month

The Doctrine's Section 9.3 says edges erode and rules are hypotheses. The measurement is the trailing expectancy series, and the question is how to tell decay from noise.

*[Figure 6 — computed figure; rendered in the HTML edition]*

The figure is a process whose true edge begins decaying at week forty. The measured thirteen-week expectancy, with its error band, does not distinguish the decay from ordinary variation until roughly week sixty-five — six months after it began. That lag is not a flaw in the measurement; it is what the error bar implies, and a trader who reacts to the first bad quarter will be reacting to noise most of the time and to decay some of the time, with no way to tell which.

Two responses, and the paper prefers the second. The first is to accept the lag and act at the review point — the Doctrine's monthly session, on the evidence, with the rule change as a challenger. The second is to watch a *leading* indicator: the response-per-unit-stimulus primitive from *Positioning & Flows*. A signal whose price response per unit of stimulus is shrinking is a signal whose edge is decaying, and that ratio moves before the expectancy does because it measures the mechanism rather than the outcome. **Edge decay is best detected in the mechanism, not in the P&L**, which is the same conclusion Chapter 10 reached from the other direction.

## Chapter 16 — What would change this paper

*The first thousand graded decisions* — at which point Chapter 13's table can be replaced with the actual intervals, and the paper's claims about decidability can themselves be graded.

*A material change in cadence* — a book making twenty decisions a week faces different arithmetic, and Chapter 1's table shifts by the square root of the ratio.

*A regime change observed inside the register* — the first real test of Chapter 4, and the first regime cut with a second state in it.

Until then the paper's standing instruction is modest: read the interval before the point, count the regimes before the trades, prefer the mechanism to the pattern, grade the decisions you did not take, and let the register be descriptive for longer than feels comfortable. The observer was always good. The auditor of the observer is this paper.

---

## Appendix — The card

*Error bars:* expectancy SE ≈ 1/√n in R. Sharpe SE ≈ √((1+S²/2)/T). A year cannot exclude zero; two years give the sign; five give the size.

*Effective n:* correlated decisions count once at their factor. Discount raw n by a third for a clustered book.

*Regimes:* n regimes, not n trades, bound regime claims. The Doctrine's most important cut is permanently the thinnest.

*Priors:* mechanism-backed beliefs start stronger and need less data. Mechanism-free ideas should be declined, not tested forever.

*Shadows:* grading declines and drafts multiplies the sample ~3.5×. The biggest free evidence in the system.

*Stopping:* pre-declare the review point. If unknowable at the review, shrink the position rather than extend the test.

*Sizing:* the Doctrine's tiers are approximately Kelly-optimal once edge uncertainty is admitted.

*Decay:* watch the mechanism (response per unit stimulus), not the P&L; the P&L lags decay by two quarters.
