# Building and Validating a Systematic Book
## Execution, Sizing, Drawdown Control, and Backtesting — Before the First Order

**Companion to: `execution-framework-v2`, the trade recommendation register, and the IBKR execution roadmap · Draft 1 · ~4,900 words · 31 August 2026**

---

> ### DRAFT 1 — PREVIEW EDITION
>
> **What this is.** A short paper written deliberately *before* IBKR Gate 1, so that the rules for execution, sizing, drawdown control, and validation exist in writing before any code can place an order. It states what the systematic book must do, what it must never do, and how it will be validated. It cannot yet report what happened, because nothing has been executed.
>
> **What this is not.** Not a strategy paper. Not an edge claim. Not a set of parameters. Every number in this draft is a placeholder or a rule of thumb, flagged as such.
>
> **Update trigger — when to write Draft 2.** In stages, matching the gates:
>
> 1. **After the v17 rebuild has run** and the dashboards and report set are in their settled design, so the signals this book consumes are the production ones.
> 2. **After Gate 1 (read-only sync) is live** — the register has mark-to-market, and the execution and slippage sections can begin to carry measured numbers.
> 3. **After Gate 2 (paper) has completed its three-month minimum dwell** — the validation section can report realized paper expectancy against register-predicted expectancy, which is the single test this paper is built around.
>
> Draft 2 should be written at the end of Gate 2, not before. Expected timing on the current schedule: **Q1–Q2 2027.** Sections marked *[empirical in Draft 2]* will be rewritten from the book's fills, logs, and ledger. The governing principle and the architecture in Parts I and V should not change; if they do, that is itself a finding worth writing down.
>
> **Numbering.** Unnumbered in Draft 1; takes its Roman numeral at library integration.

---

## Preamble · The paper goal three did not have

The library's first ten papers build toward three goals. The first is to understand and anticipate disruption, and eight of the ten papers serve it. The second is to position accordingly, and the Portfolio Construction paper is the first to address it directly. The third goal is to run a systematic book — rules that could, in principle, be executed without you — and until this draft, no paper served it at all.

The absence was deliberate. There was nothing to write about until there was something to execute, and the v17 rebuild that begins tomorrow is what creates that. But the sequencing rule from the work plan is the right one and this paper honors it: **write the execution and validation rules before Gate 1, not after.** A rule written after the first order is a rationalization. A rule written before is a constraint.

Two distinctions organize the whole paper.

The first is between a **state estimator** and a **strategy**. The five-report stack, as built, is a state estimator: it tells you what regime you are in, with what confidence, and what the sizing tier should be. It does not, by itself, have an expectancy — a measurable expected return per trade — because it does not, by itself, make trades. The systematic book is where the state estimator becomes a strategy, and the only place expectancy can be measured is in the register of trades the strategy actually made. Everything in this paper about validation follows from that.

The second is the governing principle from `execution-framework-v2`, stated once here and assumed throughout: **Claude writes rules; Claude is not in the execution path.** Signals flow to deterministic rules; deterministic rules produce orders. No LLM output ever becomes an order. This is not a limitation to be relaxed later. It is the property that makes the book auditable, and an unauditable book cannot be validated.

---

## Part I · Architecture — three layers and a persistent host

The architecture is fixed by the roadmap and restated here because the rest of the paper depends on it.

**The strategy layer produces signals only.** It reads the store — the register, the Daily Cascade's blocks, the Top & Bottom's `status.json`, the Tier 0 sizing tier — and emits a signal: instrument, direction, conviction, horizon, invalidation. It does not know how large a position is or whether the book can take it. This is the layer where the five-report stack's output lands.

**The risk layer can veto or reduce, and nothing can override it.** It takes the signal and the current book and returns either a sized order, a reduced order, or nothing. It enforces the position and gross limits, the kill switch, the whitelist, the correlation-stacking check, and the staleness guard. Its outputs are logged even when its output is "nothing," because the trades it refused are as important to validation as the trades it allowed. **The risk layer is not a component the strategy layer can argue with.** That is the whole point of separating them.

**The execution adapter sits behind a clean interface with three modes.** Paper, Shadow, and Live are configuration flags on the same code path, so that the code that runs in Gate 4 is the code that ran in Gate 2, not a rewrite. Shadow mode — compute the order, log it, do not send it — is the mode most systems skip and the one that catches the most. It is what Gate 1's read-only sync grows into.

**The persistent-host fact.** Everything else in this system is serverless — GitHub Actions and cron-job.org. IB Gateway must run continuously. Execution therefore requires an always-on host, monitored and patched, that the book now depends on. The roadmap is right to call this a deliberate decision rather than a drift, and to budget for the host, the monitoring, and the failure modes of a machine that must be up at 9:30 every morning. The persistent host is also the place the reconciliation loop and the dead-man switch live, because they need to be up when the CI runners are not.

**Prerequisite before any order.** The Daily Cascade's run status was last recorded as unclear. *No orders route off a pipeline whose execution cannot be confirmed.* Before Gate 2, the Daily must be on the store, covered by alerting, and passing the validator. This is stated in the roadmap and repeated here because it is the kind of prerequisite that gets waived under schedule pressure.

---

## Part II · Execution and microstructure

This is the section the extended edition will expand most, because every number in it becomes measurable the day Gate 1 is live. Draft 1 establishes what to measure and the rules that apply before the measurement exists.

### Order types, and when each is wrong

- **Market orders** fill immediately at the best available price and are wrong whenever the spread is wide, which is exactly when the book most wants to trade. Their use should be restricted to liquid futures in regular hours, and even there the risk layer should convert them to marketable limits with a tick or two of tolerance.
- **Limit orders** control price and surrender certainty of fill. They are right for entries and wrong for stops.
- **Stop and stop-limit orders** trigger on a price and then behave as a market or limit order. A stop that becomes a market order in a gap is a market order at the gap. A stop-limit that does not fill in a gap is a stop that did not work. Neither is acceptable as the book's only protection, which is why the kill switch in Part III is evaluated on fills, not on resting orders.
- **OCO brackets** — one-cancels-other, an entry with a linked take-profit and stop — are the roadmap's default for Gate 2 and the right one. The bracket encodes invalidation at order time, which is the discipline the register requires: every recommendation carries an `invalidation`, and the bracket is where that field becomes a resting order.
- **MOC and LOC** — market and limit on close — are the instruments for the Daily Cascade's 3:00 PM block, and the Dealer's Hand paper's treatment of close-auction dynamics is the reference. They should be sized against the auction's liquidity, not the day's.
- **Trailing stops** are a rebalancing rule disguised as an order type and should be treated as such — governed by the Portfolio Construction paper's drift bands, not set ad hoc.

### Slippage

Slippage is the difference between the price the strategy layer assumed and the price the fill achieved. It has three components: the half-spread, market impact (the price moved because you traded), and timing (the price moved between signal and order). All three are regime-dependent, and the Portfolio Construction paper's point that execution cost is a property of the regime is the reason slippage must be measured by regime, not in aggregate.

**Measurement rule.** Every fill is logged against its *arrival price* — the mid at the moment the signal was generated — and slippage is the fill minus arrival, signed by direction. The register joins this to `rec_id`. The extended edition's slippage table will be by instrument, by order type, by time of day, and by the Daily's GEX regime read. Until then the working assumptions are placeholders: **one to two ticks in ES in regular hours under positive gamma; assume double under negative gamma; assume worse at the open and into the close.** These are guesses, and Draft 2 will replace them.

### Futures — roll, tick, margin

The book's core instruments are ES/MES and NQ/MNQ. Three mechanics matter.

**Tick size and value.** ES ticks at 0.25 points, $12.50 per tick, $50 per point. MES is one-tenth. NQ ticks at 0.25 points, $5 per tick, $20 per point. MNQ is one-tenth. The micro contracts exist so that vol-scaled sizing can be granular; the risk layer should size in micros and round to minis only when the position is large enough that the commission difference matters.

**Margin.** Exchange-set initial and maintenance margin move with volatility, and the risk layer should read the current requirement rather than assume it. A margin increase in a vol spike is a forced deleveraging if the book was sized to the old requirement, and this is a known failure mode that the gross-exposure limit in Part III exists to prevent.

**The roll.** Equity index futures expire quarterly — March, June, September, December, third Friday — and volume migrates to the next contract roughly a week before expiration. Three rules:

1. **The Daily Cascade carries the roll date**, and the strategy layer does not emit a signal in the expiring contract inside the roll window. The risk layer enforces this as a staleness-style guard.
2. **The roll has a cost** — the calendar spread between the two contracts, which is mostly the carry (financing minus dividends) and which the book pays four times a year. It is small per roll and material per year, and it must be in the backtest (Part IV) or the backtest is overstated.
3. **Backtests use a continuous contract, and the adjustment method changes the answer.** Back-adjusted (additive) series preserve point moves and can produce negative prices deep in history. Ratio-adjusted (multiplicative) series preserve percentage returns. Unadjusted series with explicit roll trades are the most honest and the most work. The v17 store should hold the raw contracts and the roll dates and let the analysis choose; the rule is that **the adjustment method is stated in every backtest** and never changed mid-comparison.

### Options — assignment, pin risk, settlement

The book's options instruments are index options — SPX, and possibly SPY/QQQ. The distinction between them is the whole section.

**SPX options are European and cash-settled.** No early exercise, no assignment risk, and the position resolves to cash at expiration. Standard monthly SPX options are AM-settled — the settlement value is computed from the opening prices on expiration Friday, which means the position's final value is determined by an open you cannot trade through. Weekly SPXW options are PM-settled. The difference matters for any position held into expiration, and the risk layer should know which it holds.

**SPY and QQQ options are American and physically settled.** They can be assigned early, and the risk of early assignment rises when a short put is deep in the money or when a short call is in the money ahead of an ex-dividend date. Assignment converts an options position into a share position overnight, which changes the book's delta, its margin, and its factor sum without any signal having fired. The rule: **short American-style options are permitted in the book only with the assignment path modeled in the risk layer** — meaning the layer knows what the book looks like after assignment and has confirmed it is within limits.

**Pin risk.** A short option whose strike is at or near the underlying's price at the close on expiration day has an uncertain assignment outcome until after the close. The Daily Cascade's 3:00 PM block treats gamma-pin dynamics from the dealer's side; from the book's side the rule is simpler: **do not carry a short option within a small band of its strike into the expiration close.** Roll it or close it. The band is a Draft 2 parameter; the placeholder is one strike width for SPX.

**0DTE.** Same-day-expiration index options are the most gamma-dense instrument the book could touch, and the stated edge — short-gamma, high-vol expansion — is exactly the regime in which 0DTE positions move fastest against a short. Draft 1's rule is prohibition: the book does not trade 0DTE until Gate 3 has run and the register has enough short-dated fills to say what the realized slippage and gamma exposure were. This is a rule about sequencing, not about the instrument.

### What the IBKR API actually does

Stated plainly, because the roadmap's Gate 1 depends on understanding it.

**TWS or IB Gateway is a local process that exposes a socket.** The API does not talk to Interactive Brokers' servers; it talks to that local process, which talks to IBKR. Gateway is the headless version and is what the persistent host runs. The ports are convention: TWS uses 7496 live and 7497 paper; Gateway uses 4001 live and 4002 paper. **The port is the mode**, which is why Paper and Live in the execution adapter must be a configuration flag and never a code change — and why the risk layer should refuse to start if the port and the declared mode disagree.

**`ib_async` is the async Python wrapper.** The roadmap originally named `ib_insync`; that project was archived after its author's death in 2024 and the maintained continuation is `ib_async`. **Verified and resolved 5 Sep 2026, before any Gate 1 code existed:** the repo depends on `ib_async>=1.0` and nothing was ever written against the archived library. The API surface is near-identical — `IB.connect(host, port, clientId, readonly=...)`, `positions()`, `accountSummary()` — so the roadmap's design carries over unchanged.

**What the client does:** connects with a host, port, and client ID; qualifies a contract (turns a description like "ES, September 2026" into the exchange's canonical contract); subscribes to market data (subject to pacing limits on historical requests); places an order and receives a stream of order-status updates through a state machine — PendingSubmit, PreSubmitted, Submitted, Filled, Cancelled, and a few others; and reports account values, positions, and executions.

**What the client does not do**, and therefore what the book must: it has no risk layer, no idempotency (a retried request is a new order unless you give it the same client order ID), no reconciliation (it will report positions; it will not tell you they are wrong), and no kill switch. Every one of the Gate 4 constraints in Part V is something the book builds on top of the API, not something the API provides.

**Gate 1 uses roughly a third of this.** Connect, qualify, subscribe to account and positions, read executions, write to the store. The order-placement calls are not in the Gate 1 code — not disabled, not commented out, absent.

### *[empirical in Draft 2]*

Slippage tables by instrument, order type, time, and GEX regime. Realized roll cost per contract per quarter. The assignment log for any American-style options. The order-state-machine transition log, including every order that stalled in PreSubmitted and why.

---

## Part III · Position sizing and drawdown control

The Portfolio Construction paper sets the book-level dial and the vol-scaled sizing rule. This section is about what the risk layer does with them, and about the discipline that keeps a losing week from becoming a losing year.

### Volatility targeting

The book targets a volatility, and the sizing tier from the Tier 0 dashboard scales that target: 100% normal is the full target, 50–70% is that fraction of it, and so on. Position-level vol scaling then allocates the book's budget across positions. **Fixed-fractional sizing — risk a constant fraction of equity per trade — is the fallback when a vol estimate is unavailable, not the default.**

### Kelly, and why the book uses a fraction of it

The Kelly criterion gives the fraction of capital that maximizes long-run growth given a known edge and known payoff distribution. Neither is known. The edge estimate comes from the expectancy ledger, which is empty until Gate 2; the payoff distribution shifts with the regime. Full Kelly under an overstated edge is the fastest known route to ruin, and the standard remedy — half-Kelly or quarter-Kelly — is a hedge against the estimate being wrong. **Draft 1's rule: Kelly is computed from the ledger once the ledger has enough trades to compute it, and the book never sizes above one-quarter of it.** The fraction is a Draft 2 parameter. The upper bound is not.

### Limits, and the difference between a stop and a kill switch

The Gate 4 constraint list in Part V is the full set. Three matter enough to state here.

**Max position and max gross exposure** are ceilings, not targets, and they are evaluated by the risk layer before every order. Gross exposure is measured in vol-adjusted terms — the factor sum from the Portfolio Construction paper — not in notional, because a notional cap treats ES and gold as equivalent and they are not.

**The daily loss kill switch** halts the book when the day's realized loss crosses a threshold. It is evaluated on every fill, which means it is evaluated on the position's actual realized outcome, not on a resting stop that may not have executed. This is the distinction that matters: **a stop-loss is an order; a kill switch is a rule about the book.** A stop can fail to fill in a gap. A kill switch cannot fail to evaluate, because it runs on what has already happened. The threshold is a Draft 2 parameter; the placeholder is a fraction of the daily vol target, so that it scales with the tier.

**Drawdown-responsive sizing** cuts the vol target as the book draws down from its high-water mark and restores it as the book recovers. The shape of the cut — linear, stepped, half-target at half-of-maximum-tolerated-drawdown — is a Draft 2 parameter. The rule is that it exists and that it is a function of the drawdown, not of the operator's confidence, because the operator's confidence is highest at exactly the wrong time.

### Scaling into a move — the stated edge, sized

The stated edge is a short-gamma, high-volatility-expansion regime with large multi-day moves, and comfort scaling into 5–10% moves over a few days. That is a legitimate edge in a specific regime. It is also, as a sizing problem, the hardest one in the book, because scaling in is indistinguishable from averaging down until the move resolves.

Draft 1's rules for scaling-in, to be tested in Gate 2:

1. **The full intended size is declared at the first tranche**, in the register, with the tranche schedule. Scaling-in that was not planned is averaging down.
2. **Each tranche has its own invalidation**, and the invalidation tightens as tranches are added, because the thesis has had more time to be right and has not been.
3. **Tranche sizes are decreasing, not increasing.** The first tranche is the largest. Adding the largest tranche last is the classic error and the register will show whether it happened.
4. **The total position is governed by the regime tier**, and the tier is the Tier 0 dashboard's, not the operator's read of the tape. A 5–10% move over a few days is more likely to be occurring in the late-cycle-fragile row than in the soft-landing row, and the tier will be lower, and the total size will be smaller. The edge does not override the tier.

### Correlation stacking

The register's cross-report conflict detection is the mechanism, and the Portfolio Construction paper's factor-sum rule is the principle. The risk layer's job is to enforce it: **before sizing, sum the book's exposure by factor including the pending order, and reject or reduce if the factor limit would be breached.** A long ES signal from the Daily, a long NQ from the same block, and a short VIX call from the Top & Bottom's Appendix D are one factor exposure and should be sized as one.

### *[empirical in Draft 2]*

The kill-switch firing log. The drawdown-responsive sizing path the book actually traced. The scaling-in log — every multi-tranche position, whether the schedule was honored, and the outcome. The Kelly estimate from the ledger and the fraction actually used.

---

## Part IV · Backtesting methodology

This is where the Top & Bottom calibration's lessons become general rules. The calibration ran the scoring engine against thirteen historical episodes, found the framework stronger at bottoms than tops, identified the 2007 top as structurally uncatchable, and produced the three parallel overlays. Every one of those findings is a backtesting lesson, and this section states them as such.

### The n≈0 problem

The Twenty-Five paper establishes it and this paper does not restate it, except to note that it applies to the book as much as to the tail scenarios: **thirteen episodes is not thirteen observations.** Several are the same regime seen from different dates; several are correlated by construction because the indicators that define them overlap. The three prohibitions in that paper — on inferring frequency from a listed tail, on treating listed scenarios as exhaustive, and on point estimates where only ranges are defensible — apply to every backtest in this book.

### Overfitting, and the degrees-of-freedom rule

A scoring engine with roughly fifty indicators, eight category weights, five threshold bands per indicator, ten triggers, and three overlays has hundreds of free parameters and thirteen episodes to fit them to. That it works at all is because most of the parameters were set from economic reasoning rather than from the data, and the calibration adjusted a handful. **The rule generalized: the number of parameters adjusted by the data must be small relative to the number of independent episodes, and every adjustment must be defensible from mechanism before it is defended from fit.** The calibration's reweighting of Valuation to 17% and the addition of the Concentration overlay both had a mechanism story — the composite structurally under-weighted valuation tops — before they had a fit story. That ordering is the discipline.

### Walk-forward, and what the calibration was not

In-sample and out-of-sample separation is the standard defense against overfitting: fit on one period, test on a later one, never look at the test period while fitting. Anchored walk-forward grows the fit window; rolling walk-forward slides it. **The Top & Bottom calibration was essentially all in-sample** — the thirteen episodes were examined and the engine adjusted with all of them in view. That was the right thing to do for a first calibration with thirteen episodes, and it means the calibration's results are a description of fit, not a forecast of performance. Draft 2's walk-forward on the v17 store's vintages is what would turn them into the latter.

### Effective n, and regimes as the unit

A twenty-year daily backtest has five thousand observations and perhaps five independent regimes. The daily returns are autocorrelated in volatility and clustered in regime; the effective number of independent observations is much closer to the number of regimes than to the number of days. **The unit of a backtest for this book is the regime, not the day**, and any confidence interval that treats days as independent is overstated by a factor that can exceed ten. The practical rule: report results by regime row, and treat a strategy that has only been tested in two rows as tested in two rows.

### Point-in-time data and look-ahead

The v17 store carries vintages — the value of each series as it was known on each date, not as it was later revised. **Every backtest uses vintages.** A backtest on revised data has look-ahead baked into every revised series, and macro series are revised routinely: payrolls, GDP, the Sahm Rule's inputs. Survivorship is the same error in the cross-section — a universe defined today excludes the instruments that failed — and the book's instrument whitelist should be versioned in the store so that a backtest can use the whitelist as it was.

### Costs in the backtest

Commissions, the futures roll, the option roll, slippage by regime. A backtest without them is a backtest of a different, cheaper book. The placeholder cost assumptions in Part II go in until the Draft 2 measurements replace them, and the backtest reports results gross and net so that the cost sensitivity is visible.

### Multiple testing

If twenty variants of a rule are tested and the best is kept, the best is expected to look good by chance. The deflated Sharpe ratio is the formal correction; the informal one is to **record every variant tested, not only the survivor**, so that the number of trials is known. The register's `superseded_by` field is the natural home for this at the recommendation level; at the backtest level the rule is a log.

### What the Top & Bottom calibration taught, generalized

Seven findings, each restated as a rule for the book.

1. **Composites miss what they were not built to see.** The composite under-weighted valuation-driven tops and credit-acceleration tops because it scored levels. The overlays exist to catch what the composite structurally cannot. *Rule: every scoring system in the book carries a named list of the regimes it is blind to, and an independent check for each.*
2. **Rate of change beats level at turns.** HY OAS at 410 basis points in 2007 looked fine; HY OAS up 59% from its trough did not. *Rule: at turning points, score the acceleration, not the level.*
3. **A condition is not a timing signal.** The Concentration overlay fired in the 2024 yen-carry episode and no crash followed; the overlay was right that the market was expensive and silent on when. *Rule: separate condition flags from timing flags in the strategy layer, and never let a condition flag alone produce an order.*
4. **Some regimes are structurally uncatchable by a given system.** The 2007 top was not visible in the indicator set as constructed. *Rule: know which rows of the translation table the book cannot see, and hold structural hedges for them regardless of signal.*
5. **Bottoms are easier than tops.** The calibration found detection stronger at bottoms. *Rule: the book's sizing asymmetry should reflect the system's detection asymmetry — more confident scaling in at BOTTOM SIGNAL than scaling out at TOP SIGNAL.*
6. **A test suite makes the output reproducible.** The sixty-seven-test suite guarantees the composite in the artifact matches the engine. *Rule: every rule in the strategy and risk layers has a test, and the risk layer's tests are the ones that must pass before any mode change.*
7. **Calibrate on episodes, not on points.** Thirteen episodes examined whole taught more than five thousand daily points would have. *Rule: the unit of validation is the episode; the regime row is the unit of reporting.*

---

## Part V · Validation protocol — the four gates as four tests

The roadmap's four gates are an execution rollout. Read as a validation protocol, each gate is a test with a pass condition, and this section states the tests.

**Gate 1 — read-only sync. Test: does the register's mark-to-market agree with the broker's?** `ib_async` connection; account, positions, and marks into the store; no order capability in the code. The pass condition is a reconciliation that matches. This gate turns the expectancy ledger from theoretical to measured, and it is worth building even if the book never automates.

**Gate 2 — paper. Test: does realized paper expectancy match what the register predicted?** Orders to the paper account off Daily Cascade signals, full OCO brackets, minimum three months of dwell. This is the paper's central test and the reason the paper is written before the gate. The register predicts an outcome for every recommendation; the paper account delivers one. If they match, the signal pipeline is producing what it claims. If they diverge, the problem is upstream — in signal quality, in the translation table, in the tier logic — and going live would only fund the discovery. **Three months is the minimum, not the target.** The sample-size arithmetic in the next subsection is why.

**Gate 3 — live with approval. Test: which trades would you never have taken?** The system stages orders; the operator approves each from a phone. The purpose is to surface the trades the rules produce that the operator's judgment rejects — and there will be some. Each one is either a rule the operator does not actually believe, or a bias the operator has that the rule does not. The gate's output is a list, and the list is the most valuable artifact the rollout produces.

**Gate 4 — live automated. Test: every constraint below is implemented, tested, and has fired at least once in Gate 2 or 3.**

- Instrument whitelist — explicit, versioned in the store
- Max position size and max gross exposure, vol-adjusted
- Daily loss kill switch, evaluated on every fill
- Market-hours guard
- Staleness guard wired to the validator — no orders on data that failed a check
- Idempotent client order IDs derived from `rec_id` plus date — a retry can never double-fill
- Reconciliation loop — broker positions against expected positions, halt on any mismatch
- Dead-man switch, reachable from a phone, and tested

The last clause of the test — "has fired at least once" — is deliberate. A kill switch that has never fired is a kill switch whose wiring is unverified.

### How many trades before the ledger can say anything

The standard error of a mean falls with the square root of the sample size. With trade outcomes whose standard deviation is on the order of the mean — which is typical — roughly a hundred trades give a standard error of about a tenth of the mean, which is the first point at which the sign of the expectancy is reasonably established. Three months of Gate 2 at the Daily Cascade's cadence may or may not reach that; if it does not, the dwell extends. The rule is that **the ledger reports its standard error alongside its mean, and the book does not advance a gate on a mean whose standard error contains zero.** The regime caveat from Part IV applies on top: a hundred trades in one regime row is a hundred trades in one row.

---

## Part VI · What Draft 2 adds

Scoped in advance, so that the update is a fill-in and not a rewrite:

1. Slippage tables by instrument, order type, time of day, and GEX regime, from Gate 1 fills.
2. Realized futures roll cost per quarter and realized option roll cost per hedge, from the register.
3. The paper-versus-predicted expectancy comparison from Gate 2, with standard errors, by regime row.
4. The kill-switch and drawdown-sizing logs — every firing, and the book's path through each.
5. The scaling-in log against the four rules in Part III.
6. A first walk-forward on the v17 store's vintages, reported by regime.
7. The Gate 3 list — the trades the rules produced that the operator would not have taken — and what was changed as a result.
8. The Kelly estimate from the ledger and the fraction the book actually ran at.
9. Parameters replacing placeholders throughout, each with the date it was set and the evidence that set it.

---

*Draft 1 · 31 August 2026 · Written before IBKR Gate 1 · Companion to `execution-framework-v2` and the trade recommendation register · Not investment advice. No order is placed by any rule in this paper until the gates in Part V have passed. No instrument in the Brookfield complex, under any circumstances.*
