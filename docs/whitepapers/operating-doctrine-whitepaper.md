# The Operating Doctrine

## Trading Styles, Horizons, Regimes, and the Rules of the Book

**Companion white paper — chester-reports library**
**Series placement:** Companion **XVIII** — between *Portfolio Construction Across Regimes* (XVII) and *Building and Validating a Systematic Book* (XIX), per the library guide; cross-references in this paper are by name
**Version:** 1.0 — September 2026
**Status:** Doctrine. Governs how the reports are consumed and how capital is deployed. Changes only at the monthly session (Rule 20).

---

### Reader's note

This paper is different in kind from the others in the library. The Monthly Macro manual, the Dealer's Hand, the Rate and Liquidity Machine and the rest explain how a piece of the market works and how a report measures it. This paper explains how *I* am to behave given what those reports say. It is written in the first person because doctrine that is not owned is not followed, and it is written against the trader I have been rather than the trader I hope to become. That trader had roughly a decade of experience, real fluency in market mechanics, and a retail-grade record: under-performance of the index, periodic damage in extreme volatility, weeks spent fighting the tape, a temperamental preference for the short side and a reluctance to hold the long one, and a strategy that was data-informed more often than data-driven. Nothing in this paper assumes that trader has gone away. Everything in it assumes he can be constrained.

The paper is long because the library convention is long, but it is built to be consumed in three ways. Part I is a single page — the card — and is the only part that needs re-reading weekly. Parts IV through VII are the operating manual: the four books, the regime dials, the wiring from report to trade, and the risk budget, including the honest arithmetic on the return target. Part VIII is the rules, each tied to its origin among the Market Wizards, to the specific way I have failed before, and to the place in the system that enforces it. Parts II, III and IX are the argument, the lineage, and the adoption plan, and can be read once.

A note on sources. The intellectual scaffolding comes from Jack Schwager's Market Wizards series — the 1989 original, *The New Market Wizards*, *Stock Market Wizards*, *Hedge Fund Market Wizards*, *Unknown Market Wizards*, and the June 2026 volume *Market Wizards: The Next Generation* written with George Coyle — and from Edwin Lefèvre's *Reminiscences of a Stock Operator*, the lightly fictionalized account of Jesse Livermore. Where a specific trader's practice is invoked, it is the practice as Schwager reported it; the interpretation, and the application to a $300,000 part-time book, is mine.

---

## Part I — The Card

*Print this. It is the whole doctrine compressed to one page. Everything below it is explanation.*

**The objective.** Not to predict the market. To run a portfolio of partially independent, economically explainable edges; to know which of them work in the current regime; to express each in the best instrument; to size by expected payoff and uncertainty; and to prevent any single error from damaging the book.

**The four books.**

| Book | Horizon | Edge family | Owner report | Standard risk per position | Book loss stop (monthly) |
|---|---|---|---|---|---|
| **A — Allocation** | 1–6 months | Macro regime, valuation, positioning extremes | Monthly Macro, with Top & Bottom override; Disruptive Themes and Alt Asset for tilts | Managed by exposure band, not stop | Exposure floor by regime |
| **B — Swing** | 1–6 weeks | Trend and momentum, variant perception, thematic | Weekly reflection report (Daily Cascade), Monthly for context | 0.75% ($2,250); 1.5% exceptional (Phase 2 onward) | 3% ($9,000) |
| **C — Tactical** | 1–5 days | Event reaction, dealer positioning, session structure | Daily Cascade 0700 and 1000 reports | 0.35% ($1,050); 0.7% exceptional (Phase 2 onward) | 3% ($9,000); 1% daily, 2% weekly |
| **D — Opportunistic** | No fixed horizon | Behavioral and alternative data, forced flows, mispriced optionality | Alerts (meme monitor, prediction-market engine, overhang tracker, tail scan) | 0.25% ($750) maximum | 1% ($3,000) |

**The three dials.** Every decision carries a regime stamp: **Macro** (Expansion / Overheat / Tightening / Contraction / Transition — from the Monthly composite), **Volatility** (Calm / Rising / Stressed / Crisis — from the Volatility framework), **Gamma** (Positive / Flip-zone / Negative — from the Dealer's Hand stack). The dials set which books are open, the size multiplier, the instrument, and the stop discipline. A signal outside its regime is ignored, not discounted.

**The kill-switch ladder.** Daily −2% ($6,000): Books B, C, D closed for the day. Weekly −4% ($12,000): B, C, D closed for the week. Monthly −7% ($21,000): all books at half size the following month, mandatory review. Drawdown −12% from peak ($36,000): B, C, D closed, A to its regime floor, thirty-day cool-off, rules review. Drawdown −20% ($60,000): full stop; capital is re-approved, not resumed. Re-entry after any switch happens at the next *scheduled* session, never sooner.

**The volatile-day protocol.** Triggered by the 0700 report when VIX is at or above 25 or up 20% on the day, when the overnight range exceeds 1.5× the 20-day ATR or the open gaps 1% or more, when the gamma dial reads Negative, or on a tier-1 event day. Then: all sizes halved on top of the dial multipliers; no new Book D; no futures outside a pre-staged Book A rebalance; Book C only from the 0700 setup list, only defined-risk, brackets at entry, no entries after 10:30 unless confirmed in the 1000 report; no adds to any losing position; no manual stop overrides; sixty-minute cool-off after any stop-out.

**The ten non-negotiables** (numbers in brackets are the rule numbers in Part VIII). The book survives first [R1]. Never trade through a tripped switch [R2]. On volatile days, I am the risk — halve everything and act only from the list [R3]. Never add to a loser [R4]. Every position has its exit written before entry [R5]. Edge before signal: name the edge, the counterparty, and why it persists [R6]. Asymmetry before hit rate [R7]. The thesis and the instrument are two decisions [R11]. Top-down sets the budget; bottom-up spends it and may veto but never enlarge [R19]. No Decision Packet, no trade [R18].

**The known biases.** Short by temperament; tail-cynical; under-invested since 2008; prone to fighting the tape for weeks. Each has a rule [R26–R29], a structural cost, and a ledger cut that is read first: long versus short expectancy, counter-trend versus with-trend expectancy, Book A versus its floor, and the hedge budget's spend.

**The score.** The weekly number is noise. The score is rolling thirteen-week expectancy by book and by regime, and the count of rules broken, which should be zero. The active books (B, C, D) are benchmarked, over four quarters, against Book A alone and against a static 60/40; if they do not beat both, they are shrunk.

---

## Part II — The Premise

### 2.1 Two questions

There are two questions that sound alike and are not. The first is whether markets can be beaten. The second is whether a *repeatable process* can beat them, after costs, across several regimes, run by a particular person with particular constraints. The answer to both is yes. The second is much rarer than the first, and it is the only one that matters for this book.

The evidence for the first question is not controversial among people who have looked. Schwager's interviews span four decades and several dozen traders whose records are exceedingly difficult to attribute to luck; add the long records of Buffett and Munger, Renaissance's Medallion fund, Soros and Druckenmiller, Thorp, Lynch, and the list is long enough that "markets cannot be beaten" is simply an empirical mistake. What the same evidence also shows, and what is easier to forget, is that none of those records was smooth. A strategy with an expected excess return of eight percent a year and eighteen percent volatility is a very valuable thing — and it will lose to the index in something like a third of individual years, and occasionally in two or three years running. A trader who abandons it after twelve bad months has thrown away an edge, and will do so again with the next one.

So "consistent" needs to be defined before it can be pursued. I define it as positive risk-adjusted excess returns across a sufficiently large number of independent decisions and across multiple market regimes. It is not beating the index every calendar year, and it is emphatically not making money every week. This definition is the first constraint on everything that follows, and it will return with teeth in Part VII, where the arithmetic of the return target is laid out.

### 2.2 Why alpha is scarce, and where a small book can find it

Alpha is scarce because it comes from something that is scarce. The main sources are well catalogued: knowing something sooner or understanding it better; processing public information in a way others do not; buying from forced or frightened sellers and selling into euphoria; exploiting structural flows — index rebalancing, dealer hedging, closing-auction imbalances, systematic fund positioning, options expiry; being willing to wait longer than other participants; entering and exiting more intelligently; and surviving long enough for a statistical edge to express itself. Increasingly there is an eighth source, which is the integration of datasets that most discretionary participants do not systematically combine. That eighth source is what the five-report system is, and it is the reason the system exists.

A sophisticated individual with $300,000 has, in 2026, a better opportunity to generate alpha than he had twenty years ago. He does not have that opportunity by trying to beat Citadel at Citadel's game. He has it because institutional-quality data, APIs, and language-model research are now available at retail cost; because he is not constrained by the capacity problem that keeps a twenty-billion-dollar fund out of trades that cannot move its needle; and because he can move across horizons — from months to hours — without a mandate or a risk committee telling him to stay in his lane. The five-report cascade is the first advantage made concrete. The four-book structure in Part IV is the second and third.

The same freedom is also where the retail trader dies, and the doctrine has to be honest about that from the start. No mandate means no one stops him from over-trading. No capacity constraint means he can take a position in something illiquid enough to trap him. Cross-horizon freedom means the swing thesis can be quietly converted into a day trade when it goes against him, or the day trade into a "long-term holding" when it does not stop out. Every one of those has happened in this book's history. The advantage and the failure mode are the same thing viewed from different sides; the rules exist to keep the one and lose the other.

### 2.3 The operator as a design input

Most trading frameworks are written for an idealized operator. This one is written for a specific one, and his constraints are treated as engineering inputs rather than as apologies.

He works a demanding day job in specialty insurance and cannot be in front of a screen during the session. This is not a limitation to be worked around; it is the single most valuable structural fact about the book, because it removes the possibility of the most destructive retail behavior — watching every tick and acting on it — provided the system does not reintroduce it through a phone. It means every trade must be executable in minutes from a prepared list, with its exits placed at entry, and every report must be consumable in the time it takes to drink a coffee. Semi-automation is therefore not a convenience but a load-bearing wall: the machine holds the brackets, enforces the switches, computes the size, logs the packet, and raises the alert; the human allocates, approves, and vetoes.

He has roughly a decade of experience and a strong conceptual understanding of institutional mechanics — options structure, dealer positioning, flows, index inclusion — which means the deficit was never analytical. The deficit was behavioral and structural: no fixed process for deciding what to trade, no fixed process for deciding how much, and a tendency for risk discipline to fail precisely on the days it mattered most. The Market Wizards literature is unanimous that this is the common shape of failure among intelligent traders, and that the remedy is not more intelligence but externalized rules.

The specific shape of his record is known, and the doctrine is written to it rather than around it. He has at times done well in volatile markets — the observer is good when the tape is moving — and has been badly hurt in *extreme* volatility, when the size that was right for a fast market was wrong for a disorderly one. He has fought the tape: held against the primary trend for days and weeks at a time, which is the single behavior the Wizards most uniformly condemn and the one Livermore paid for most often. He has a standing preference for the short side, which is unusual, which he recognizes as unusual, and which means that his "neutral" is not the market's neutral. He is temperamentally cynical about tail risk, including the monetary system itself, and that cynicism has expressed itself as positioning rather than as hedging. He entered the markets professionally into the 2008–2010 downturn, and the imprint has been a reluctance to hold long-term long positions at all — a reluctance whose cost, over a fifteen-year bull market, has been larger than any single losing trade. And the record contains a clean specimen of the whole pattern: profitable short positioning into the 2020 collapse, followed by losses as the market turned and recovered faster than the thesis could be abandoned.

He describes the conclusion as "I am my own enemy," and the doctrine takes the phrase literally. Each of those tendencies gets a named rule in Part VIII, a cut in the ledger that makes it visible, and a structural feature that makes it expensive to indulge: a floor on the allocation book that makes under-investment a rule break, a confirmation asymmetry that makes shorts harder to open than longs, a time stop on any counter-trend position, and a hedge budget that gives the tail cynicism a defined-risk home so that it stops living in the book's net exposure.

He is putting $300,000 at risk and has stated an aspiration of $5,000 to $10,000 per week on average — with the qualification, in his own words, that the regime and environment have to support the trade. He also holds, at the same time, the suspicion that active trading in pursuit of out-performance may be illusory for him. Both are taken seriously in Part VII, where the aspiration is shown for what it implies, the regime qualification is shown to be the thing that makes it coherent, and the suspicion is turned into a standing benchmark test that the active books must pass or be shrunk. What the doctrine will not do is let the target drive the sizing. Among the retail behaviors the Wizards warn against, sizing to a P&L goal rather than to the opportunity is the most reliably fatal, because it guarantees that position size is largest exactly when the edge is weakest — when the trader is behind and trying to catch up.

He will not trade Brookfield-family securities, for reasons of employment. This is a hard exclusion in the Security Master, not a preference.

### 2.4 The objective, restated

The premise, then, is not "build the system that beats the market." It is:

> Assemble a portfolio of identifiable, partially independent edges. Determine the environments in which each works. Express each in the best instrument. Size by expected payoff and uncertainty. Prevent any single error from damaging the book. Measure everything, and let the losses teach.

Every element of that sentence maps to a component of the architecture. The edges are the four books. The environments are the three regime dials. The expressions are the instrument tables. The sizing is the tiered, quarter-Kelly-capped calculator. The prevention is the kill-switch ladder and the volatile-day protocol. The measurement is the decision register and the expectancy ledger. The doctrine is the sentence; the architecture is its implementation; the rules are what the operator agrees to in order to make the two coincide.

---

## Part III — What the Wizards Actually Share

### 3.1 No single method; a common operating system

The single most useful fact in the Market Wizards literature is that the traders in it disagree about almost everything. Richard Dennis and Ed Seykota made fortunes from mechanical trend following. Paul Tudor Jones and Bruce Kovner made theirs from discretionary macro that blended fundamentals, price action, sentiment and historical analogy. Marty Schwartz traded short-term momentum and market structure. William O'Neil combined earnings acceleration with price and volume behavior. Michael Steinhardt's edge was "variant perception" — knowing where consensus was wrong. Tony Saliba and later Jamie Mai built businesses on convexity. Jim Rogers waited for money to be lying in the corner. They held nearly contradictory views of how markets work, and all of them made money. The conclusion is not that method does not matter; it is that *prediction accuracy is not the objective*. What matters is the combination of edge, sizing, payoff asymmetry and loss control, and that combination can be assembled from very different components.

What they share is closer to an operating system than a strategy, and it has six recognizable features.

They each had an identifiable edge and could say what it was. Dennis and Seykota exploited the fact that markets trend farther than fundamentals imply. Schwartz exploited short-horizon structure. Jones exploited the interaction of macro, positioning and price. O'Neil exploited the persistence of earnings acceleration. None of them was vague about why the money came to them, and none of them assumed it would keep coming after the reason had gone.

They managed losses far more aggressively than the average participant. Schwager's summary across the books amounts to a single sentence: being wrong is normal; staying wrong is the problem. Kovner's rule of deciding the exit before the entry, Jones' insistence on defense over offense, Brandt's willingness to be stopped out of a chart he still believed in — these are the same discipline in different accents.

Position sizing was part of the edge, not an afterthought. They did not treat every idea equally. Ordinary ideas got ordinary size; exceptional configurations got exceptional size, and the willingness to be, in Druckenmiller's phrase, "a pig" when the odds were unusually favorable is what separated the great records from the merely good ones. Thorp's formalization of this through Kelly-fraction sizing is the analytical version of what the discretionary traders did by feel.

They adapted. Most changed tactics when market structure changed rather than assuming a historically successful signal would work forever. Schwager's more recent commentary, around the 2026 volume, is explicit that edges erode and that the traders who last are the ones who notice.

They concentrated when odds were unusually favorable and did not try to generate alpha every day. This is the least intuitive feature to a retail trader and the most important. The great records are lumpy. They were made in a small number of periods when everything lined up, and the rest of the time the job was to not lose much while waiting.

They understood their own psychology and built around it. Fear of missing out, refusal to take a loss, doubling down to vindicate a thesis, trading too large after a win or a loss — these destroy otherwise sound strategies, and the Wizards are unusual not in being immune to them but in having noticed and constructed defenses.

### 3.2 The nine alpha families, and which are available to this book

Rather than imitate the thirty or forty most useful of them, it is more useful to sort them into families of edge and ask, for each family, whether a $300,000 part-time semi-automated book can plausibly harvest it, and if so through which of the four books and fed by which report.

| Alpha family | Representative Wizards | The real edge | Available to this book? | Book | Feeding report |
|---|---|---|---|---|---|
| Trend / momentum | Dennis, Seykota, Eckhardt, Driehaus, Minervini, Kullamägi | Markets trend farther than fundamentals imply; winners persist | Yes, at the weeks horizon | B (and A for exposure direction) | Weekly reflection, Monthly, Technical Indicators |
| Discretionary macro | Kovner, Jones, Druckenmiller, O'Shea, Marcus | Regime plus positioning plus price confirmation | Yes, at the months horizon | A | Monthly Macro, Top & Bottom, Rate and Liquidity Machine |
| Variant perception / contrarian | Steinhardt, Rogers, Shapiro, Okumus | Consensus positioning or narrative is wrong | Yes, at extremes only | B, A | T&B overlays, Monthly sentiment pillar, Positioning & Flows (planned) |
| Event / information reaction | Clark, Cohen, Netto, Platt, Breitstein | Price behavior relative to what should have happened | Yes, with defined risk | C | Daily Cascade 0700/1000, event calendar |
| Behavioral / alternative data | Camillo, Neumann, Shapiro | Detect behavioral change before financial data does | Yes, small and gated | D | Meme monitor, prediction-market engine, social velocity |
| Quant / statistical | Thorp, Hull, Shaw, Woodriff, Trout | Small edges repeated with disciplined sizing | Partly — as a sizing and validation discipline, not as a strategy | All (as method) | Register, expectancy ledger, *Systematic Book* paper |
| Asymmetric / optionality | Mai, Saliba, Bender, Sall | Small defined losses versus occasional enormous gains | Yes — the natural instrument for a part-time book | C, D, and A's hedges | Dealer's Hand, Volatility, tail scan |
| Value / fundamental dislocation | Greenblatt, Rogers, Galante, O'Neil | Price/fundamental disconnect with a catalyst | Limited — requires research time the operator lacks | A (thematic tilts only) | Disruptive Themes, Equities paper |
| Execution / risk as edge | Hite, Brandt, Platt, Dhaliwal, Basso, Schwartz | Survival, sizing, selectivity and execution themselves create alpha | Yes, and it is the family that determines whether the others survive | All | Kill switches, Gate 1.5 execution analytics, register |

Three observations follow from the table.

First, the quant family is present but not as a strategy. The book does not have the data depth, the turnover capacity, or the operator time to run cross-sectional statistical arbitrage. What it takes from Thorp and Woodriff is the *method*: sizing from measured expectancy, demanding sample sizes before believing a result, and treating every rule as a hypothesis with a decay rate. The forthcoming *Building and Validating a Systematic Book* paper is where that method becomes procedure.

Second, the value family is deliberately under-weighted. It is the family that most rewards research hours, and research hours are the book's scarcest resource. Its place is confined to the thematic tilts in Book A, which the Disruptive Themes report supplies with a human gate, and it is not allowed to become a stock-picking habit in Book B, where the discipline is trend and confirmation rather than conviction about intrinsic value.

Third, and most important: the asymmetric family and the execution family are not two among nine. They are the two that make a part-time book possible at all. Defined-risk structures are the only honest way to hold positions one cannot watch. And the risk-as-edge family — Hite's survival, Brandt's patience, Platt's ruthless cutting of anything that does not behave — is the family that this operator's history says was missing. The doctrine over-invests in these two on purpose.

### 3.3 The small-capital advantage, stated precisely

The advantage of a small book is often described loosely as "nimbleness." It is worth being exact, because exactness reveals where the advantage actually lives and where it is an illusion.

A $300,000 book can enter and exit any liquid instrument at effectively zero market impact. It can hold a position in a single-name option series where a fund's minimum size would be the entire open interest. It can trade the closing auction, the expiry pin, and the index-inclusion flow at sizes that are invisible. It can act on a prediction-market divergence or a social-velocity spike in a small-cap name where the entire opportunity is worth less than a fund's research budget for evaluating it. And it can shift from a six-month allocation stance to a two-day tactical trade without asking anyone. These are real, and Books C and D exist to harvest them.

What the small book cannot do is out-research, out-model, or out-execute the institutions in the trades the institutions care about. It has no edge in mega-cap earnings, in the direction of the ten-year yield over the next hour, or in the fair value of the S&P. Where it competes on those, it competes as the liquidity that the institutions harvest. The allocation book therefore does not try to be clever; it tries to be *positioned correctly for the regime* and to change stance rarely and deliberately, which is a game the institutions play badly because their mandates prevent it.

The shadow side is that the same freedom that makes Books C and D possible makes them the natural home of every retail pathology. Illiquid options that cannot be exited, meme names that gap through stops, "opportunities" that are really the operator's boredom — these are all Book D behaviors. The book is therefore the smallest, the most tightly budgeted, and the last to be activated in the adoption sequence of Part IX.

### 3.4 Discretion, kept — and machine-assisted

Schwager's observation in discussing the 2026 volume is worth dwelling on: most of the truly extraordinary records he has found are discretionary, not purely systematic. He is not arguing that systematic trading lacks edge — the trend-following records alone refute that — but that the extreme records tend to involve human adaptation, judgment, and the synthesis of multiple inputs that no single model captured.

That has a direct implication for the architecture, and it is the opposite of the implication a novice would draw. The goal is not to remove the human from the loop. It is to give the human a dramatically better loop. The machine should do everything that is impossible to do manually: monitor thousands of instruments, categorize and score information, detect anomalies, measure historical analogues, track prediction-market movement, monitor positioning, recognize regime changes, compute expected distributions, flag conflicting signals, retrieve prior comparable trades, and maintain an objective performance ledger. The five reports are that machine. The top of the loop remains a human who allocates capital, approves or vetoes packets, and — critically — is himself constrained by rules that the machine enforces.

The formula, then, is machine-generated evidence plus systematic risk control plus discretionary capital allocation. This is closer to the collective Market Wizards model than a fully autonomous black box would be, and it is also more honest about where this particular operator's edge and this particular operator's weakness both live: in judgment. The judgment is kept; the weakness is fenced.

### 3.5 Livermore, the pre-Wizard

Jesse Livermore belongs in the doctrine before the Wizards, and he belongs in it for two reasons that pull in opposite directions.

The first is that his method, as Lefèvre rendered it, is a remarkably complete statement of the things this book's Swing and Allocation books are trying to do. Trade with the primary trend rather than against it because prices seem high or low. Wait for the pivotal point — the level or the moment at which the market must declare itself — and do not be in the market simply because it is open. Let the price reaction to news, rather than the news, tell you where positioning is. Add to winners on confirmation and never to losers; "pyramiding" was his word for the first half and his fortunes were lost on the second. And sit tight when right, because the money is in the large move, not in trading around it. Every one of those maps to a rule in Part VIII, and the Swing book's entry and add logic is essentially Livermore's.

The second reason is that he destroyed himself, more than once, and finally. He possessed an extraordinary market instinct and no institutional risk control whatsoever. It is worth noticing, for this book in particular, where his fame came from: the great trades of 1907 and 1929 were shorts, and the great short of 1929 was followed by the losses of the 1930s. A trader whose best instinct is for the downside, who is right about a collapse and then cannot leave it, is the Livermore pattern exactly, and the operator's 2020 record is the same pattern in miniature. The doctrine's response — that short campaigns end on the Top & Bottom bottom signal and not on conviction — is written with both cases in view. The lesson the doctrine draws is stated as its motto and as Rule 23: *never confuse being a good market observer with being a good risk manager.* Sustainable alpha requires both, and the evidence of this book's own history is that the observer was always better than the risk manager. The kill-switch ladder is the risk manager Livermore never hired.

If Schwager teaches how great traders operate, Livermore teaches why even a great trader needs a system that protects him from himself. This book has never had a great trader in it. It has had a competent observer with a retail record, which is precisely the profile for which Livermore's example is most useful and most sobering.

---

## Part IV — The Horizon Ladder: Four Books

### 4.0 Why books, not trades

The retail trader thinks in trades. He has an account, he has ideas, and each idea becomes a position in the account with no formal relationship to the others. The consequence is that he cannot answer the questions that matter: which of his edges is working, which of his time horizons is paying, whether his day trades and his long-term holdings are secretly the same bet on the same day, and whether the loss he just took was a bad trade or a bad book.

The doctrine replaces the account with four books. A book is a distinct combination of an edge family, a time horizon, an instrument set, a risk budget, an owning report, a cadence, and its own ledger. The books are deliberately partially independent: they are fed by different reports, they hold different instruments, they are evaluated on different clocks, and they have separate loss stops. They are not fully independent — on a crash day all four will be long beta unless the regime dials have already reduced them — and Section 4.5 handles the correlation between them. But the separation is what makes measurement possible, and measurement is what makes the doctrine self-correcting rather than merely aspirational.

The four horizons were chosen to match the cascade rather than the other way round. The Monthly Macro report and the Top & Bottom report are monthly instruments; they own the months-horizon book. The weekly reflection report in the Daily Cascade is a weekly instrument; it owns the weeks-horizon book. The 0700 and 1000 reports are daily instruments; they own the days-horizon book. The alert layer — the meme monitor, the prediction-market engine, the overhang tracker, the tail scan — is event-driven; it owns the opportunistic book. Each book is therefore consumed at the cadence at which its owning report is produced, which is what makes the time budget in Section 6.5 possible.

A note on tense. Parts IV through VIII describe the system's components — the register, the sizing calculator, the heat figure, the brackets, the switches — in the present tense, as designed. Section 9.5 says which of them exist today, which are prerequisites to activating each book, and which wait on the broker integration. Nothing in the doctrine depends on a component the adoption sequence does not build before the book that needs it.

### 4.1 Book A — Allocation (one to six months)

**The edge.** Book A harvests the discretionary-macro family and, at extremes, the contrarian family. Its claim is modest and well-supported: that the joint state of growth, inflation, liquidity and positioning determines the distribution of returns for broad asset classes over the following months, and that a book which is positioned for that distribution and changes stance rarely will out-perform one that is either static or twitchy. Institutions know this and cannot act on it fully because their mandates fix their exposure; the small book can.

**What "trading" means here.** Book A does not take trades. It holds a stance, expressed as exposure bands, and it rebalances to the stance at the monthly session. The stance is a set of target exposures — net equity beta as a percentage of capital, duration, a real-asset sleeve, a digital-asset sleeve, a cash-equivalent residual — each set within a band that the Macro dial determines. Between monthly sessions the book does nothing unless the Top & Bottom report fires an override, in which case the stance moves to the override band at the next session or, for a bottom signal, immediately.

**Exposure bands by Macro dial.** These are the Phase 1 bands and are the single most consequential numbers in the doctrine, because Book A carries the largest notional and is the book whose behavior on a bad month determines whether the drawdown switches trip.

| Macro dial | Net equity beta (% of capital) | Duration sleeve | Real assets (gold, energy, via Alt Asset) | Digital sleeve | Cash residual |
|---|---|---|---|---|---|
| Expansion | 60–80% | 0–10% | 5–10% | 0–5% | Balance |
| Overheat | 40–60% | 0% | 10–20% | 0–5% | Balance |
| Tightening | 20–40% | 10–20% | 10–15% | 0% | Balance |
| Contraction | 20–40% | 20–30% | 5–10% | 0% | Balance |
| Transition | The lower half of the band the dial is leaving, hedged | Hold | Hold | Hold | Higher |

The floor of each band is as binding as the ceiling, and for this operator it is the more important number. The ceiling is written against the retail habit of being fully invested at the top; the floor is written against his own habit of not being invested at all. A stance below the floor of the current band is a rule break, logged and counted like any other, and the only things that move Book A below its floor are the Drawdown I switch and a Crisis volatility regime without a bottom signal. The 2008 imprint is not a reason to hold less than the floor; it is the reason the floor exists.

The bands are wide on purpose. Where within the band the stance sits is set by three modifiers: the Top & Bottom composite (toward the bottom of the band as top triggers accumulate, toward the top after a bottom signal), the Disruptive Themes composite (a reading of −1.0 or worse, as at the May through August 2026 runs, holds the stance in the lower half of any band until the composite recovers), and the Volatility dial (Stressed or Crisis forces the lower half regardless of Macro, with one exception: a Top & Bottom bottom signal permits the top of the band even in Crisis, for the reasons given in Section 6.3).

**Instruments.** Broad index ETFs and index futures for the beta sleeve; Treasury ETFs or futures for duration; the Alt Asset report's instruments for the real-asset and digital sleeves. No single names. Where the book needs to hold equity exposure through a Transition or a Stressed volatility regime, the exposure is converted to a convexity-managed form — a defined-outcome ETF, a collar, or a put spread against the sleeve — rather than reduced to zero, because reducing to zero is the retail behavior that guarantees missing the recovery. This is the one place where the prior work on defined-outcome structures earns its keep: they are not a trade, they are how the allocation book holds beta when it cannot afford to be wrong about timing.

**Sizing and risk.** Book A is not stop-managed and does not have a per-position risk figure. Its risk is controlled by the bands, which cap the loss the book can take in any month at roughly the exposure multiplied by a bad month for the asset class, and by the T&B override. In a Contraction stance at 30% net beta, a 10% equity drawdown costs the book about 3% of capital; in an Expansion stance at 70%, the same move costs 7%, which is why the Expansion band does not go to 100% and why the monthly kill switch at 7% is set where it is. The Volatility dial's forcing of the lower band in Stressed regimes is what prevents Book A from being at 80% net beta when the drawdown arrives.

**Cadence and time.** One session a month, on the first weekend after the Monthly Macro and Top & Bottom reports publish: read the two reports and the Alt Asset report, read the Disruptive Themes report when it has refreshed, set the dial, set the stance within the band, generate the rebalance packet, execute the rebalance as a set of limit orders on Monday. Ninety minutes, including the review of the prior month's books.

**Expected contribution.** In a well-run year, Book A is the largest contributor to P&L and the smallest contributor to Sharpe. It is the book that keeps the operator invested through the regimes in which the index does the work, and it is the book whose out-performance of a static allocation is the cleanest test of whether the Monthly Macro report earns its existence.

### 4.2 Book B — Swing (one to six weeks)

**The edge.** Book B harvests trend and momentum, with variant perception at extremes and thematic tilts when the Disruptive Themes report supplies them. Its claim is Livermore's and Dennis's: that markets and individual instruments trend further than fundamentals alone would imply, that the persistence is strongest after a pivotal point has been decisively cleared, and that the retail crowd's habit of fading strength and buying weakness creates the counterparty.

**What a Swing trade is.** A directional position in a single name, a sector or thematic ETF, a commodity or currency instrument from the Alt Asset universe, or a futures contract, entered at or immediately after a pivotal point — a breakout from a defined base, a reclaim of a lost level with volume, a failed breakdown — and held for the duration of the move or until the plan's exit, whichever comes first. The entry is Livermore's: it waits for the market to declare itself rather than anticipating. The add is Livermore's: additional size is committed only on confirmation, at a higher price for a long, never on weakness. The exit is Brandt's: a written invalidation level that is honored without renegotiation, a time stop that closes a position which has done nothing in its expected window, and a plan for taking profit that is set before the trade, not during it.

**Instruments and expressions.** Equity and ETF positions for the base case. Vertical spreads or diagonal spreads when the Volatility dial is Rising or Stressed and implied volatility makes outright options expensive — the spread caps the cost of being right about direction and wrong about timing. Outright long options only in the Calm regime, and only on names with liquid chains. Futures for index, rate, and commodity expressions, always with a working bracket. No short options without a defined wing; no naked short stock; nothing that cannot be exited in one session at ordinary size.

**Sizing.** Standard risk per position is 0.75% of capital, or $2,250, defined as the distance from entry to invalidation multiplied by the position size. The exceptional tier at 1.5% is available from Phase 2 onward and requires the three-dial alignment described in Section 7.3 plus one independent confirmation from a different signal family — in practice the T&B overlays and, once written, the Positioning & Flows inputs. A maximum of six open positions; a maximum of 4% of capital, or $12,000, in total open risk, with correlated positions counted once at their common factor. The book's monthly loss stop is 3% of capital, $9,000, after which the book is closed until the next monthly session.

**Cadence and time.** The weekly reflection report is the owning instrument. On Sunday: read the report, review the candidate list it has generated from the week's price action against the Monthly context, select at most three candidates, write their packets with entry conditions and exits, and stage them as conditional orders with brackets for the week. During the week the book requires no attention beyond the 0700 report's confirmation that stops and brackets remain in place. Forty-five to sixty minutes on Sunday; five minutes a day.

**The short side.** Book B is the book in which the operator's short preference will try to express itself, and it carries three asymmetries for that reason. A short requires one more confirmation than a long: where a long needs a pivotal point and one confirming signal, a short needs the pivotal point, the confirming signal, and a regime in which shorts are permitted at all — Overheat, Tightening, Contraction, or a Volatility dial at Rising or worse. In an Expansion, Calm, Positive-gamma regime, Book B does not open outright shorts; a bearish view there is expressed as a pair, a reduction of Book A within its band, or a pass. A short that is working is closed on the Top & Bottom bottom signal, not on conviction — the campaign ends when the framework's strongest signal says it ends, which is the rule the 2020 record was missing. And the ledger reports long and short expectancy separately, with the short figure printed first, so that the bias is measured before it is indulged.

**Fighting the tape.** A Book B position against the primary trend — a short in an uptrend defined by the Technical Indicators paper's structure, or a long in a downtrend — is permitted only at ordinary tier, carries a five-session time stop instead of the standard one, and may not be added to under any circumstances. If the primary trend has not turned by the fifth session, the position is closed, whatever the thesis. The operator's record says he can be right about a turn and early by weeks; the five-session stop is the price of being allowed to try.

**The behavioral fence.** Book B is where the two most common retail conversions happen: the swing trade that becomes a day trade when it goes against the operator on day one, and the swing trade that becomes an investment when it fails to stop out. Both are outlawed. A Book B position closed inside two sessions of entry for a reason other than its invalidation level is logged as a rule break. A Book B position that has passed its time stop is closed regardless of thesis. The register makes both visible.

### 4.3 Book C — Tactical (one to five days)

**The edge.** Book C harvests event reaction, dealer positioning, and session structure. Its claim, which the Dealer's Hand paper develops in full, is that the mechanical hedging of options dealers creates predictable intraday and multi-day behavior — mean reversion and pinning when dealers are long gamma, trend amplification and range expansion when they are short — and that the price reaction to scheduled and unscheduled information relative to what the positioning implied *should* have happened contains information that the headline does not. This is Platt's edge and Breitstein's, and it is the one that requires the most machine assistance, which is why the 0700 and 1000 reports exist.

**What a Tactical trade is.** A defined-risk position in an index instrument — SPX or SPY options, QQQ options, or ES and NQ futures — entered from the 0700 report's setup list, confirmed or vetoed by the 1000 report, held for one to five sessions, and managed entirely by a bracket placed at entry. The setups are of three kinds: a fade toward a gamma-implied pin in a Positive-gamma regime; a continuation through a level in a Negative-gamma regime after confirmation; and an event-reaction trade in the session after a scheduled release, taken in the direction of the reaction when it contradicts the positioning-implied expectation.

**Instruments and expressions.** Vertical spreads are the default expression, because they are defined-risk, they can be sized to the exact dollar risk of the packet, and they are indifferent to the operator's absence. Outright long options are permitted in Calm and Positive-gamma regimes when the expected move is large relative to the premium. Futures are permitted only with a server-side OCO bracket working from the moment of entry — the execution framework's bracket rules govern this — and are prohibited on volatile-protocol days. Zero-days-to-expiry structures are the subject of a specific rule: they are permitted only in a Positive-gamma regime, only as defined-risk spreads, only from the 0700 list as confirmed by the 1000 report, and only while the register shows a positive thirteen-week expectancy for that session type. The Dealer's Hand paper's 0DTE session taxonomy is the reference; the doctrine's position is that the instrument is a legitimate expression of a gamma-regime edge and an illegitimate expression of boredom, and that the register is how the difference is detected.

**Sizing.** Standard risk per trade is 0.35% of capital, $1,050; the exceptional tier at 0.7% is available from Phase 2 onward and requires the alignment test. A maximum of two concurrent positions. The book carries three stops: a daily stop of 1% of capital ($3,000), after which the book is closed for the day; a weekly stop of 2% ($6,000), after which it is closed for the week; and a monthly stop of 3% ($9,000). These are tighter than Book B's because Book C is where the operator's history says the damage happens, and because Book C trades are the ones most likely to be taken on a volatile day.

**Cadence and time.** The 0700 report is read before the work day: ten minutes, to note the regime stamps, the setup list, and the volatile-day flag. Conditional orders with brackets are staged then. The 1000 report is read at a break: five minutes, to confirm or cancel the staged orders. The close is checked in five minutes for fills and for the next day's carry. No other screen time is permitted during the session, and the rule is enforced by the simplest mechanism available — the brackets are working, and nothing in the rhythm requires a screen between the three touches.

**The behavioral fence.** Book C's fence is the volatile-day protocol, which is triggered by the 0700 report and which halves size, restricts the book to defined-risk expressions from the list, forbids entries after 10:30 without 1000-report confirmation, and imposes a sixty-minute cool-off after any stop-out. The protocol is the doctrine's direct response to the operator's stated history, and it is described in full in Section 5.5.

### 4.4 Book D — Opportunistic (no fixed horizon)

**The edge.** Book D harvests the behavioral and alternative-data family, forced-flow structure, and mispriced optionality. Its claim is Camillo's and Neumann's and Shapiro's: that behavioral change is visible in social velocity, search, and positioning data before it is visible in price; that forced flows — index inclusion, the unlock and lock-up mechanics of a mega-IPO, closing-auction imbalances, expiry pins — create predictable pressure that a small book can trade at sizes that do not matter to anyone else; and that prediction markets, read for divergence from the price of the corresponding financial instrument rather than for their own forecasts, occasionally reveal a mispricing worth a small, convex position.

**What an Opportunistic trade is.** Anything the alert layer surfaces that passes the packet test and that does not belong in another book. The current alert sources are the meme and squeeze monitor, the prediction-market intelligence engine, the SpaceX and ASTS overhang tracker, the Monthly's tail scan, and whatever the Positioning & Flows paper adds. The typical expression is a small long-option position or a small equity position with a hard stop; a pair when the edge is relative; occasionally a short with a defined wing when a squeeze has exhausted. The horizon is whatever the catalyst dictates, but every packet carries a time stop, because "no fixed horizon" is not the same as "no horizon."

**Sizing.** Maximum risk per position of 0.25% of capital, $750, with no exceptional tier — Book D does not get one, because the asymmetry it seeks is supposed to come from the payoff, not the size. A maximum of three concurrent positions. A monthly loss budget of 1% of capital, $3,000, after which the book is closed for the month with no exceptions. The budget is small by design: Book D is expected to lose money in most months and to make it back and more in a few, and the budget is the price of admission to those few.

**The tail-hedge budget.** Within Book D's 1% sits a ring-fenced tail-hedge budget of 0.4% of capital a month, $1,200, which is the doctrine's answer to the operator's tail cynicism. The Monthly's tail scan and the Disruptive Themes report's monetary-architecture factor are exactly the places where a worry about the monetary system belongs, and the hedge budget is exactly the form it is allowed to take: far-out-of-the-money puts, a small long-volatility structure, or an increment to the gold sleeve, sized so that the entire budget can expire worthless every month for a year at a cost of 5% of capital. What the cynicism may not do is live in the book's net exposure — as a standing short, as a stance below Book A's floor, or as a reason to pass on a long the regime supports. A tail thesis is a hedge budget, not a position. The ledger reports the hedge budget's spend and its payoff separately, so that the operator can see, over time, what his worry has cost and what it has been worth.

**Cadence and time.** Alert-driven, but decided only at a scheduled touch. When an alert fires, it waits for the next touch — the 1000 report, the close, or the weekend session — and at that touch the operator has fifteen minutes to write a packet or to log a pass; if he cannot write the packet in fifteen minutes, the answer is a pass. No Book D packet is written on a volatile-protocol day, and none is written after a Book C stop-out in the same session. An opportunity that cannot survive a few hours' wait was a forced flow the operator was going to be on the wrong side of.

**The behavioral fence.** Book D is the natural home of every retail pathology, and it has the most fences. Meme and squeeze trading is explicitly a secondary, opportunistic activity and not the book's purpose; the doctrine's position, consistent with the earlier ruling, is that the book wants early *awareness* of extreme meme activity and only occasionally wants a position in it. The Brookfield-family exclusion applies with particular force here, because the overhang tracker and the thematic alerts are the places where a related name is most likely to surface. And Book D is the last book activated in the adoption sequence, after the register has shown that Books A through C are being run to rule.

### 4.5 How the books interact

Four books with separate budgets are not four independent bets. They share an operator, a capital base, and — on the days that matter — a factor. The doctrine handles this in three ways.

**Heat is capped across books.** Total open risk across Books B, C and D may not exceed 6% of capital, $18,000, at any time, with correlated positions counted once at their common factor. Two long semiconductor names in Book B and a long NQ call spread in Book C are one position for heat purposes. The register's heat calculator does this arithmetic; the operator does not.

**Net exposure is capped across books.** The sum of Book A's net beta and the beta-equivalent of Books B, C and D may not exceed the top of Book A's Macro band plus 15 percentage points. In an Expansion regime that is 95% of capital; in Contraction, 55%. This is the rule that prevents the situation in which the allocation book is at its ceiling, the swing book is long three cyclical names, the tactical book is long a call spread, and the opportunistic book is long a squeeze candidate — four books, one trade, and a very bad day.

**The regime dials act on all books simultaneously.** When the Volatility dial moves to Stressed, Book A moves to the lower half of its band, Book B stops adding, Book C moves to defined-risk only at half size — a quarter once the volatile-day protocol's own halving is applied, since the protocol runs every day in Stressed — and Book D closes. The dials are the mechanism by which the books de-correlate at the moment correlation is most dangerous, and they are described next.

---

## Part V — Regime Switches

### 5.1 Three dials, not one

The retail trader asks whether a signal "works." The Wizards ask under what conditions it works, and the honest answer is always conditional: on volatility, on liquidity, on the inflation and growth backdrop, on policy, on positioning. Kovner and Jones adapted their tactics as those conditions changed; Dennis's trend systems made most of their money in a minority of regimes and gave some of it back in the rest; Platt's cutting discipline was a response to the observation that a thesis that is not working in the current environment is not a thesis, it is a hope.

The doctrine operationalizes regime conditionality as three dials rather than one composite, because the three things they measure move on different clocks and act on different books. The Macro dial moves monthly and governs Book A. The Volatility dial moves weekly to daily and governs sizing and instrument choice in every book. The Gamma dial moves daily and governs Book C's setup type and Book B's entry timing. Collapsing them into one number would lose exactly the information the books need.

**The Macro dial** is read from the Monthly Macro report's ten-pillar composite, collapsed for dial purposes into the growth, inflation and liquidity triad that the Rate and Liquidity Machine paper uses. Five states: **Expansion** (growth improving, inflation stable or falling, liquidity easy), **Overheat** (growth strong, inflation rising, liquidity beginning to tighten), **Tightening** (growth slowing, inflation elevated, liquidity tight — the stagflationary quadrant), **Contraction** (growth and inflation both falling, liquidity easing or about to), and **Transition**, which is declared whenever the composite crosses a state boundary or the pillars disagree beyond a threshold the Monthly report defines. Transition is a state in its own right, not an absence of one, because the first weeks after a regime change are where the most money is lost by people positioned for the old regime.

**The Volatility dial** is read from the Volatility paper's regime identification: the level of implied volatility, the shape of the term structure, and the relationship between realized and implied. Four states: **Calm** (VIX below roughly 15, term structure in steep contango, realized below implied), **Rising** (VIX in the mid-teens to low twenties and climbing, realized catching up to or exceeding implied), **Stressed** (VIX in the mid-twenties to thirties, term structure flat or inverting), and **Crisis** (VIX above roughly 40, backwardation, correlation toward one). The thresholds are illustrative and the Volatility paper's are canonical; what the doctrine fixes is the number of states and what each does to the books.

**The Gamma dial** is read from the Dealer's Hand stack, self-computed from raw option chains with FlashAlpha's aggregate levels as a cross-check. Three states: **Positive** (spot above the gamma flip, dealers long gamma, hedging flows dampen moves), **Flip-zone** (spot within a defined distance of the flip, the regime unstable), and **Negative** (spot below the flip, dealers short gamma, hedging flows amplify moves). Two modifiers: proximity to a monthly or quarterly expiry, which strengthens pinning in Positive and increases the risk of a violent unpin, and the DEX reading, which indicates the direction in which hedging pressure leans.

### 5.2 The regime card

The card is the object the operator actually consults. It says, for each state of each dial, what each book does. The dials act multiplicatively on size and conjunctively on permissions: a book is open only if every dial permits it, and its size multiplier is the product of the three dial multipliers, capped at 1.0 in Phase 1.

**Macro dial — acts mainly on Book A, sets the context for B**

| State | Book A | Book B | Book C | Book D |
|---|---|---|---|---|
| Expansion | Band 60–80% | Open; long bias; momentum trusted; no outright shorts (pairs only) | Open | Open |
| Overheat | Band 40–60%; real assets up | Open; sector rotation toward real assets and energy; longs and shorts, shorts with the extra confirmation | Open | Open |
| Tightening | Band 20–40%; duration sleeve on | Open; short side open; trend trusted more than mean reversion | Open | Open at half budget |
| Contraction | Band 20–40%; duration sleeve up | Open; bottom-fishing prohibited until T&B bottom signal; shorts close on that signal; then long bias | Open | Open at half budget |
| Transition | Lower half of the departing band, hedged | Half size; no exceptional tier; no adds for two weeks | Half size | Closed for two weeks |

**Volatility dial — acts on every book's size and instrument**

| State | Size multiplier (B, C, D) | Book A | Instrument rule | Stop discipline |
|---|---|---|---|---|
| Calm | 1.0 | Full band available | Outright options permitted; premium selling with defined wings permitted in C | Standard |
| Rising | 0.75 | Full band available; hedges considered | Spreads preferred over outright; premium selling only with defined wings, at half size | Tightened by 25% |
| Stressed | 0.5 | Lower half of band forced; convexity-managed beta | Defined-risk options only; no futures in B or C; no adds in B; no D entries | Volatile-day protocol every day (which halves size again) |
| Crisis | 0.25 in C; B and D closed | Regime floor; T&B bottom signal is the only permission to add | C: event-reaction setups only, defined-risk, from the 0700 list; no fades (mean reversion is Off); no continuation longs | Volatile-day protocol; no adds anywhere |

**Gamma dial — acts on Book C's setup type and Book B's timing**

| State | Book C setup type | Book B timing | Size multiplier (C) |
|---|---|---|---|
| Positive | Fade toward pin; premium structures; mean-reversion levels trusted | Breakouts distrusted — wait for the retest; adds on confirmation only | 1.0 |
| Flip-zone | No new positions until the zone resolves; existing positions to half | No new entries | 0.5 |
| Negative | Continuation after confirmation; momentum trusted; range-expansion expected | Breakouts trusted; pyramiding permitted on confirmation | 0.75, and the volatile-day protocol is on — so 0.375 effective |

The combined multiplier is the product of the three dial multipliers, halved again whenever the volatile-day protocol is on. In an Expansion, Calm, Positive regime — the benign case — every book is at full size and the operator's job is to not over-trade. In a Transition, Stressed, Negative regime — the case that has historically cost this book the most — Book A is hedged in the lower half of its departing band; Book B is at 0.5 × 0.5 = 0.25 of standard size from the dials and 0.125 after the protocol's halving, with no adds; Book C is at 0.5 × 0.5 × 0.75 ≈ 0.19 from the dials and about 0.09 after the protocol — roughly $100 of risk per trade, which is to say effectively closed, and confined to defined-risk continuation setups from the list; and Book D is closed. The arithmetic is what removes the discretion from the moment when discretion has been worst.

### 5.3 The meta-model: which signals to trust now

The reports generate more signals than any book can act on, and the signals disagree. The meta-model is the answer to the question the Market Wizards Alpha Framework identified as the sophisticated one — not "what does the signal say?" but "should this signal be trusted right now?" — and it is expressed as a trust matrix: signal families in rows, regime states in columns, and a trust level in each cell. High means the signal may drive a packet on its own. Medium means it may drive a packet only with independent confirmation. Low means it is context, not a trigger. Off means it is ignored regardless of what it says.

| Signal family | Source | Calm / Positive | Rising / Flip-zone | Stressed or Crisis / Negative | Transition (any) |
|---|---|---|---|---|---|
| Macro composite and pillars | Monthly Macro | Medium (monthly session only) | Medium | High for reducing; Low for adding | High |
| Turn detection — bottoms | Top & Bottom | Low | Medium | High | High |
| Turn detection — tops | Top & Bottom | Medium (permission to cut, never to short on its own) | Medium | Low | Medium |
| Positioning extremes | T&B overlays and the GEX stack now; Positioning & Flows once written | Low unless above the 90th percentile | Medium | High | High |
| Trend and momentum | Weekly reflection, Technical Indicators | Medium — chop risk | High | High for continuation; Off for new longs in Crisis | Low |
| Mean reversion and levels | Dealer's Hand, 0700 report | High | Medium | Off | Off |
| Event reaction | 0700 / 1000 reports | Medium | High | High with defined risk | Medium |
| Sentiment and social velocity | Meme monitor | Medium for D | Medium for D | Off | Off |
| Prediction-market divergence | PM engine | Discovery only | Discovery only | Discovery only | Discovery only |
| Tail scan | Monthly Part 16 | Watchlist for D hedges | Watchlist | Active hedging input for A | Active |

Two features of the matrix deserve comment. The asymmetry between bottom and top detection is a direct transcription of the Top & Bottom report's own calibration finding that the framework is stronger at bottoms than at tops and that the 2007 top was structurally uncatchable. A top signal is therefore never permission to short on its own; it is permission to reduce Book A toward the bottom of its band and to raise the bar for Book B longs. A bottom signal, by contrast, is the only thing that permits adding in a Crisis regime, and it may act on its own. The second feature is that the prediction-market engine is confined to discovery in every column. This transcribes the amendment that gave it narrow signal rights pending a calibration archive; the doctrine does not enlarge those rights, and will not until the archive exists.

Signal half-life is the other dimension of trust. A Monthly composite reading is good for a month and should not be re-litigated daily. A gamma reading is good for a session and should not be extrapolated to a week. The register stamps every packet with the regime and the signal that generated it, and the ledger reports expectancy by signal family, which is the mechanism by which the trust matrix is revised.

### 5.4 Transitions are the danger zone

Every one of the doctrine's three dials has a Transition or Flip-zone state, and the rules for those states are the most restrictive in the card. This is deliberate and is the doctrine's answer to a specific finding across the Wizards: the periods in which adaptable traders distinguished themselves from rigid ones were regime changes, and the way they distinguished themselves was not by predicting the new regime but by *reducing exposure to the old one quickly and re-engaging slowly*.

The transition rule applies to the two slow dials. In the two weeks after the Macro or the Volatility dial changes state, no book operates above half its standard size, no exceptional-tier packets are written, no adds are made to existing positions, and Book D is closed. The Gamma dial moves too often for a two-week rule; its transitions are handled by the Flip-zone state — no new positions until the zone resolves, existing positions to half — and by the volatile-day protocol, which the Negative state switches on. Book A moves to the lower half of the band it is leaving, hedged with a convexity structure, rather than to the band it is entering — because the dial may revert, and because a stance set by a regime that lasted three weeks is worse than a stance set by the one that lasted three months. The re-engagement into the new regime's bands happens at the next monthly session, by which time the Monthly report has either confirmed the change or withdrawn it.

The operator's history is relevant here. The days on which risk management failed were not random; they were, disproportionately, days on which the Volatility dial had moved from Calm to Rising or from Rising to Stressed, and on which the positions carried into the change were sized for the regime that had ended. The transition rule is the structural response: size is reduced by the dial change itself, before the operator has had a chance to decide whether the change is real.

### 5.5 The volatile-day protocol

This is the doctrine's most specific rule and the one written most directly against the operator's record. It exists because poor risk management on volatile days is, by his own statement, the failure mode that has done the most damage, and because the general rules of the card are not enough on those days: they require the operator to apply them, and the operator's application is precisely what has failed.

**Triggers.** The 0700 report raises the volatile-day flag when any one of the following holds: the VIX is at or above 25, or has risen 20% or more over the prior session; the overnight range in the ES has exceeded 1.5 times the 20-day average true range, or the gap at the open is 1% or more; the Gamma dial reads Negative; or the calendar shows a tier-1 event — an FOMC decision, CPI, the employment report, or earnings from a name large enough to move the index. The flag is machine-set and cannot be cleared by the operator.

**Automatic actions.** All size multipliers are halved on top of whatever the dials already impose. No new Book D packet may be written. Book C is confined to the setups on the 0700 list, to defined-risk expressions, with brackets placed at entry, and no entry is permitted after 10:30 unless the 1000 report confirms it. No add is permitted to any losing position in any book. No stop may be manually moved away from the price. After any stop-out, a sixty-minute cool-off applies before any new packet may be written in any book.

**The hands-off list.** On a flagged day the operator does not trade futures in any book other than a Book A rebalance staged the prior evening as limit orders, does not sell options without a defined wing, does not average into anything, does not re-enter a position that has just stopped him out in the same direction, and does not check the book between the 1000 report and the close. The list is short because it is the list of things that have actually happened.

**Why it halves rather than closes.** The operator's record says he has at times done well in volatile markets and badly in extreme ones, and the protocol is built to that distinction. A flagged day is not a closed day: Book C stays open at half size in defined-risk structures from the list, because a fast tape with dealer hedging amplifying moves is a regime in which the event-reaction and continuation setups have their cleanest edge, and the register will be asked whether the operator's volatile-regime expectancy is in fact his best. What closes the books is Crisis — the disorderly regime in which size that was right for a fast market becomes wrong for a broken one — and the difference between the two is a dial reading the machine sets, not a judgment the operator makes on the day.

**Why it is structured this way.** Schwartz's rule after a large loss was to trade small until confidence returned; Marcus's was to get out and re-evaluate; Jones's was that the days after a big loss are the days on which the next big loss is most likely. The protocol encodes all three, and it also encodes the observation in Part VII's arithmetic — that a Sharpe-1.0 process is reduced to roughly a quarter of its expected annual return by two uncontrolled weeks a year, and to a losing process by four. There is no rule in the doctrine with a higher expected value than this one.

### 5.6 Expression by regime: the O'Shea rule

The thesis and the instrument are two decisions. Colm O'Shea's example in *Hedge Fund Market Wizards* is the canonical one: convinced that the technology bubble's burst would slow the economy, he did not short the NASDAQ — a trade that would have been correct in thesis and repeatedly wrong in expression as counter-trend rallies ran — but bought bonds, which expressed the same view without the path risk. The doctrine generalizes this into a table that the packet must consult: given a directional thesis and the current Volatility and Gamma states, which expression carries the thesis with the best payoff-to-path-risk ratio?

| Thesis | Calm / Positive | Rising / Flip-zone | Stressed or Crisis / Negative |
|---|---|---|---|
| Index higher over weeks | Long ETF or futures with bracket; long call if premium is cheap | Call vertical; or long ETF with put spread | Call vertical only, small; or wait for the T&B bottom signal |
| Index lower over weeks | Short futures with bracket; long put if cheap | Put vertical | Put vertical; or reduce Book A rather than add a short — the reduction is the expression |
| Single name higher over weeks | Stock with stop; long call | Call vertical or diagonal | Do not initiate; if held, collar |
| Index range-bound this week | Iron condor or short strangle with wings, from 0700 list | Iron condor, narrower, half size | Not permitted |
| Rates lower over months | Long duration ETF or futures | Same, with the sleeve capped | Same — this is the regime where the expression works best |
| Dollar lower, real assets higher | Long gold via Alt Asset sleeve; energy tilt | Same | Gold sleeve is the hedge, not the trade — hold it |
| Volatility higher | Long VIX call spread, small, D budget | Long put spread on index | Already expressed by reduced size — do not double it |

The last row is the doctrine's most important application of the rule. When the regime is already Stressed, the operator's instinct to "trade the volatility" is usually an instinct to add risk in the direction the book is already exposed. The reduced size the dials have imposed *is* the volatility trade. Adding a long-volatility position on top of it is buying insurance on a house that has already been sold.

---

## Part VI — Wiring the Cascade

### 6.1 Authority: top-down sets the budget, bottom-up spends it

The five reports form a cascade from the generational frame of Disruptive Themes, through the monthly instruments, to the daily and intraday instruments. The doctrine's authority rule is that authority flows downward and veto flows upward.

A higher-horizon report sets the *budget* for the horizons below it: the Macro dial's bands cap Book A's exposure, and through the net-exposure rule of Section 4.5 they cap the total beta the lower books may add. The Volatility dial, which the Monthly and the Volatility framework jointly set, caps the size multipliers. A lower-horizon report *spends* that budget — it decides which specific trades, at which specific times, in which specific instruments — and it may *veto* a trade the higher horizon would have permitted, but it may never *enlarge* what the higher horizon has allowed. The 1000 report can cancel a Book C setup the 0700 report staged; it cannot double it. A Negative gamma reading can keep Book B out of a breakout the weekly reflection report liked; it cannot raise Book B's size above what the Volatility dial permits.

This rule resolves most conflicts before they arise, and it does so in the direction of restraint, which is the direction the Wizards' evidence favors. The retail conversion in which a monthly thesis is used to justify a daily add — "the macro is bullish, so I'll buy this dip at three times size" — is exactly the enlargement the rule forbids. The macro is the budget. The dip is a Book C setup with a Book C size, or it is nothing.

### 6.2 The report-to-book map

Each report has a defined set of rights over each book. The map is the doctrine's statement of those rights, and any use of a report outside its rights is a rule break.

**Disruptive Themes** (generational, human-gated, refreshed several times a year). Rights over Book A: it sets the thematic tilts within the equity sleeve, and its composite modifies where within the Macro band the stance sits — a reading at or beyond −1.0 holds the stance in the lower half of any band. Rights over Book B: its factors define the thematic candidate lists the weekly reflection report may draw on. Rights over Books C and D: none directly, though its factors seed the alert vocabulary. The report is permanently human-gated in the automation addendum, and the doctrine's position is that a report which moves once a quarter has no business in a daily decision.

**Monthly Macro** (monthly, ten pillars, tail scan in Part 16). Rights over Book A: it sets the Macro dial and therefore the bands; it is the owning report. Rights over Book B: context only — its pillars inform the sector and factor tilt of the candidate list, but no Book B packet is generated from the Monthly alone. Rights over Book C: none. Rights over Book D: the tail scan's twenty-five scenarios are Book D's standing watchlist for convex hedges, and the monthly session decides whether any scenario has moved from watchlist to packet.

**Top & Bottom** (monthly, ten triggers, three overlays). Rights over Book A: override. A bottom signal permits Book A to move to the top of its band immediately, ahead of the monthly session, and is the only signal that permits adding in a Crisis volatility regime. A top signal moves the stance to the bottom of the band at the next session; it does not on its own permit a short. Rights over Book B: a top signal raises the confirmation bar for longs and opens the short side; a bottom signal opens the long side after a Contraction regime has closed it. Rights over C and D: the overlays — Concentration & Complacency, HY spread acceleration, liquidity and funding stress — feed the positioning-extreme row of the trust matrix.

**Alternative Asset** (eighteen assets across metals, digital, currencies, energy). Rights over Book A: it owns the real-asset and digital sleeves and their bands. Rights over Book B: it supplies the non-equity candidates — a gold breakout, a currency trend, an energy rotation — on the same pivotal-point and confirmation terms as equities. Rights over C: none. Rights over D: its surveillance tab is an alert source.

**Daily Cascade** — the eight reports. The **0700 report** owns Book C: it stamps the three dials for the day, raises or clears the volatile-day flag, publishes the setup list with levels and expressions, and confirms that Book B's brackets are working. The **1000 report** has veto and confirmation rights over the 0700 list and no rights to add to it. The **weekly reflection report** owns Book B: it generates the candidate list, reviews the prior week's packets against their plans, and reports the thirteen-week expectancy by book. The **close report** records fills and carry. The remaining reports are diagnostic and have no rights over any book.

**The Prediction Market Intelligence Engine** (read-only, Polymarket and Kalshi). Rights: discovery only, in every regime, for Book D. It may put a name or an event on the alert list; it may not generate a packet, and it may not modify the confidence of any other signal until the calibration archive exists. This transcribes the amendment exactly.

**Positioning & Flows** (the paper to be written next) will, when written, own the positioning-extreme row of the trust matrix and supply Book B's variant-perception confirmations and Book C's dealer-positioning inputs beyond what the Dealer's Hand already provides. Until it exists, those rights sit with the T&B overlays and the GEX stack.

### 6.3 Conflict rules

Five conflicts recur. Each has a fixed resolution.

*The Monthly says Expansion and Top & Bottom accumulates top triggers.* Book A stays within the Expansion band but at its bottom, 60%. Book B's long confirmation bar rises and its short side opens. The Monthly sets the band; T&B sets where in it.

*The 0700 report lists a long setup and the Gamma dial reads Negative.* The setup is permitted only as a continuation trade after confirmation, at the 0.75 gamma multiplier halved again by the volatile-day protocol that Negative gamma switches on — 0.375 of standard size. A fade-toward-pin long is not permitted in a Negative regime regardless of the level — the trust matrix reads Off for mean reversion there.

*The weekly reflection report likes a breakout and the Volatility dial has just moved to Stressed.* The transition rule and the Stressed multiplier both apply: a quarter of standard size, no adds, and the expression moves from stock to call vertical. If the dial moved in the same week the candidate was generated, the candidate is deferred a week.

*A Top & Bottom bottom signal fires in a Crisis volatility regime.* This is the one case in which the lower dial does not veto the higher signal. Book A may add to the top of its band. Books B, C and D remain under Crisis rules. The doctrine accepts this asymmetry because the T&B calibration says bottoms are the framework's strength, and because the retail behavior at bottoms is to be fully de-risked and to stay that way.

*A Book D alert fires on a volatile-protocol day.* The alert is logged and the packet is not written. If the opportunity is real it will be there tomorrow; if it is not there tomorrow it was a forced flow the operator was going to be on the wrong side of.

*A winning short campaign meets a Top & Bottom bottom signal.* The campaign ends. Shorts in Book B are covered at the next session at the latest; Book A moves toward the top of its band. The operator's conviction that the bottom is false is logged as a pass on the long side, not expressed as a held short. This is the 2020 rule, and it is the conflict the operator's record says he resolves wrongly when left to himself.

Where a conflict arises that the five rules do not cover, the default is the more restrictive action, and the conflict is logged for the monthly session to rule on and add to this list.

### 6.4 Decision Packets as the unit of action

The architecture change order made immutable Decision Packets the unit of decision governance, with a point-in-time store, a decision register, and the REPORT_OK versus DECISION_BLOCKED distinction. The doctrine adopts the packet as the unit of *trading* action as well: no packet, no trade, and a packet missing any required field is DECISION_BLOCKED regardless of how good the trade looks.

A packet carries, for every book:

- the book, the edge family from the nine, and the owning report and section that generated it;
- the regime stamp — all three dials and the volatile-day flag — at the time of writing;
- the thesis in one sentence, and the answers to the three edge questions: why should this make money, who is on the other side, and why has it not been arbitraged away;
- the expression, chosen from the regime's expression table, and the reason if it departs from the default;
- the size tier — ordinary, good, or exceptional — and the computed dollar risk;
- the invalidation level, the time stop, and the profit plan;
- the expected R and the expected holding period;
- for Book B, the add rule; for Book C, the bracket; for Book D, the catalyst and its date.

The automation addendum already provides that drafted Daily setups enter the register automatically as drafts. The doctrine extends the draft mechanism to Books A and B at their respective sessions, so that the operator's job at every session is to approve, modify or reject drafts rather than to write from a blank page. This is the single biggest time saving in the operating rhythm, and it is also a behavioral fence: a trade that the machine did not draft has to be written in full, which is enough friction to stop most impulse trades.

Every packet is closed with a post-mortem stamp — the six questions of Section 9.2 — whether it won or lost. Packets that were passed on are also logged, with a one-line reason, because the doctrine's claim that doing nothing is a position requires that the nothing be recorded.

### 6.5 The operating rhythm and the time budget

The doctrine is only credible if it can be run in the time the operator actually has. The rhythm below totals roughly three to four hours a week in ordinary conditions — the monthly session amortized, the weekly session, three short daily touches, and the occasional alert — and is designed so that no step requires being at a screen during the session.

**Monthly session** — the first weekend after the Monthly Macro and Top & Bottom reports publish. Ninety minutes. Read the Monthly's composite and pillars, the T&B composite and overlays, the Alt Asset signals tab, and Disruptive Themes if refreshed. Set the Macro dial. Set Book A's stance within its band and approve the rebalance packet. Review the prior month's ledger by book and by regime. Rule on any logged conflicts. Consider rule changes — this is the only session at which rules may change. Stage Book A's rebalance orders for Monday.

**Weekly session** — Sunday. Forty-five to sixty minutes. Read the weekly reflection report. Review the prior week's Book B and C packets against their plans and stamp post-mortems. Select up to three Book B candidates from the drafted list, approve or modify their packets, and stage conditional entries with brackets. Note the coming week's tier-1 events. Confirm the heat and net-exposure figures.

**Daily** — three touches. The 0700 report before work, ten minutes: dials, flag, setup list, bracket confirmation; approve or reject the drafted Book C packets and stage them. The 1000 report at a break, five minutes: confirm or cancel. The close, five minutes: fills, carry, and whether any switch has tripped. On volatile-protocol days the 1000 touch is mandatory and the close touch is the last look of the day.

**Opportunistic** — alert-driven but decided at the next scheduled touch; fifteen minutes to a packet or a pass; never on a flagged day.

The rhythm implies a set of requirements on the automation that the doctrine states as obligations rather than wishes. The reports must publish on time on the VPS, because a 0700 report that arrives at 0900 is a report the operator will read at his desk, which is the behavior the rhythm exists to prevent. The drafts must be complete enough to approve in one reading. The brackets must be server-side at the broker so that they work when the operator's machine is off. The kill switches must be enforced at the execution layer, not by the operator's memory. And the ledger figures — heat, net exposure, thirteen-week expectancy, rule-break count — must be at the top of the weekly reflection report, above anything about the market.

### 6.6 The semi-automation contract

The execution framework already draws the line: Claude writes the rules and does not sit in the execution path. The doctrine extends the line into a contract between the machine and the operator that says who does what, and it is the contract that makes the rhythm possible.

**The machine** computes the dials and stamps them on every report and packet; raises and clears the volatile-day flag; drafts packets for every book at the book's cadence; computes size from tier, risk and multiplier; places and maintains brackets; enforces the kill-switch ladder at the execution layer by refusing orders that would breach it; maintains the heat and net-exposure figures; logs every packet, pass, and post-mortem in the register; computes the ledger; and raises alerts.

**The operator** sets the Macro dial's stance within the band at the monthly session; approves, modifies or rejects drafted packets at each session; vetoes; writes packets for opportunities the machine did not draft, in full, with the friction that implies; stamps post-mortems; and changes rules only at the monthly session.

**Neither** moves a stop away from price, adds to a losing position, trades through a tripped switch, or trades a Brookfield-family security. These are enforced by the execution layer where the IBKR integration permits and by the register's rule-break count where it does not.

The IBKR gates in the architecture — Gate 1 for the integration, Gate 1.5 for expression and execution analytics — are the doctrine's dependencies. Until Gate 1 is passed, the contract is executed by hand with the register as the enforcement mechanism, which is weaker; the adoption sequence in Part IX takes account of this by activating the books in the order that least depends on automated enforcement.

---

## Part VII — Risk Doctrine and the Target

### 7.1 Risk is the alpha

Larry Hite's line is the shortest statement of the doctrine's first principle: if you don't bet, you can't win; if you lose all your chips, you can't bet. Brandt describes discipline, patience, risk management and execution — not chart reading — as his sources of edge. Platt cuts anything that does not behave as expected, on the theory that a thesis which is not working now is not a thesis. The Wizards' agreement on this point is nearly total, and it is the point on which this book's history is weakest.

It is worth quantifying what "weakest" has cost, because the number is larger than intuition suggests and because it is the number that justifies every restrictive rule in the card. Take a process that is, by any honest standard, good: a Sharpe ratio of 1.0 at 25% annualized volatility, which on $300,000 produces a median year of about $75,000, or $1,450 a week. Now add the retail failure mode — a small number of weeks a year in which size was too large on a volatile day and the stop was not honored, each costing 8% of capital. The simulation is in Appendix A; the summary is this.

| Uncontrolled weeks per year | Average week | Median annual P&L | 10th-percentile year | Realized Sharpe | P(losing year) | Median max drawdown | Bad-case drawdown | P(drawdown > 25%) |
|---|---|---|---|---|---|---|---|---|
| 0 | $1,461 | $74,857 | −$27,527 | 1.01 | 18% | −15% | −28% | 15% |
| 2 | $539 | $18,427 | −$77,013 | 0.34 | 41% | −21% | −37% | 36% |
| 4 | −$399 | −$30,583 | −$117,512 | −0.24 | 64% | −28% | −46% | 60% |
| 6 | −$1,318 | −$71,722 | −$148,706 | −0.74 | 81% | −36% | −54% | 78% |

Two uncontrolled weeks a year convert a good process into one that makes a quarter of what it should and loses money in two years out of five. Four convert it into a losing process. This is the arithmetic of the retail record, and it is the reason the doctrine treats the volatile-day protocol as the highest-value rule it contains. Nothing in the edge families is worth as much as not having those weeks.

### 7.2 The budget architecture

The budget is stated in dollars of loss, not in notional, because loss is what the operator experiences and what the switches measure. Capital at risk is $300,000. Every figure below is a Phase 1 figure and is revisited only through the promotion gates of Section 7.7.

**Per-position risk** is defined as the distance from entry to invalidation multiplied by size, and it is the number the packet computes and the execution layer enforces. Book B: 0.75% standard, 1.5% exceptional. Book C: 0.35% standard, 0.7% exceptional. Book D: 0.25% maximum, no exceptional tier. Book A has no per-position risk; it is governed by bands.

**Book loss stops** close a book until its next scheduled session. Book B: 3% of capital in a month. Book C: 1% in a day, 2% in a week, 3% in a month. Book D: 1% in a month.

**Heat and exposure caps** bind across books: 6% total open risk across B, C and D; net beta-equivalent exposure across all books capped at Book A's band ceiling plus 15 points.

**The kill-switch ladder** binds the whole book and overrides everything above it.

| Level | Trigger | Action | Re-entry |
|---|---|---|---|
| Daily | −2% of capital ($6,000) in a session | Books B, C, D closed for the day; A untouched | Next session's 0700 list, at half size for that day |
| Weekly | −4% ($12,000) in a week | B, C, D closed for the week | Next Sunday session; first week back at half size |
| Monthly | −7% ($21,000) in a month | All books at half size the following month; mandatory review at the monthly session | Full size resumes only after a month at half size with no switch tripped |
| Drawdown I | −12% from peak ($36,000) | B, C, D closed; A to its regime floor; thirty-day cool-off; rules review | B first, at half size for a month; then C; then D; each activation requires a clean month |
| Drawdown II | −20% from peak ($60,000) | Full stop | Capital is re-approved as if new: one month of paper trading to rule, then Phase 1 from the beginning |

The re-entry column is the part most retail systems lack, and it is the part that matters. A switch that trips and is then reset by the operator's mood the following morning is not a switch. Every re-entry in the ladder is tied to a *scheduled session*, so that the decision to resume is made by the process that made the decision to stop.

The switches do not improve expectancy. It is important to be clear about this, because the temptation is to believe that a stop-loss adds return. It does not; on a random path it converts a few large losses into more frequent small ones at roughly the same expected cost. What the switches do is make the *realized* distribution of the book behave like the *assumed* distribution of the risk budget — that is, they remove the fat left tail that the operator's own behavior adds. The budget-first arithmetic of Section 7.5 assumes a distribution with no behavioral tail. The switches are what make that assumption honest.

### 7.3 Sizing to the opportunity

Druckenmiller's observation that it takes courage to be a pig, Jones's that he is only ever playing defense until the moment he is not, and Thorp's formalization of both through Kelly sizing agree on the structure of the thing: most opportunities deserve ordinary size, a few deserve much more, and the skill is in telling them apart and in being solvent when the few arrive.

The doctrine uses three tiers. **Ordinary** is the standard risk figure for the book. **Good** is 1.5 times standard and requires two of the three dials to favor the trade's direction plus a signal at High in the trust matrix. **Exceptional** is 2 times standard — the "exceptional" figures in the book descriptions, available from Phase 2 onward — and requires all three dials aligned, a High signal, one independent confirmation from a different signal family, and a Top & Bottom reading that does not contradict. No more than two exceptional-tier packets may be written in a month, and none in a Transition state or on a flagged day.

Kelly is the ceiling, not the target, and the ceiling is far above where the doctrine sizes. The reference table shows why.

| Hit rate | Average win ÷ average loss | Expectancy per trade | Full Kelly | Quarter Kelly | Quarter Kelly on $300K |
|---|---|---|---|---|---|
| 40% | 2.5 | +0.40R | 16% | 4.0% | $12,000 |
| 45% | 2.0 | +0.35R | 18% | 4.4% | $13,125 |
| 50% | 1.5 | +0.25R | 17% | 4.2% | $12,500 |
| 55% | 1.2 | +0.21R | 18% | 4.4% | $13,125 |
| 60% | 1.0 | +0.20R | 20% | 5.0% | $15,000 |

Even quarter-Kelly on a demonstrated 45%-hit, 2:1 process would be $13,000 of risk per trade — six times the doctrine's standard Book B figure. The gap is deliberate and has two justifications. The first is that Kelly assumes the edge is *known*, and this book's edge is, as of Phase 1, a hypothesis with no register data behind it; sizing at a fraction of a fraction is what one does with an unmeasured edge. The second is that the ladder's monthly and drawdown switches must not be tripped by ordinary variance, and at quarter-Kelly sizes they would be. As the register accumulates and the hit rate and payoff become measured rather than assumed, the promotion gates in Section 7.7 allow the tiers to move toward the Kelly ceiling — never to it.

### 7.4 The target, treatment one: adopted as given

The operator's stated aspiration is $5,000 to $10,000 a week on average on $300,000 of capital. Taken literally, this is 1.67% to 3.33% a week, which is 87% to 173% a year without compounding and 136% to 450% with it. The question the doctrine has to answer honestly is what a process that produces those averages must look like — in volatility, in Sharpe ratio, in the frequency of losing weeks, and in drawdown — because the average is the only part of the target the operator has specified, and the average is the least important part.

The simulation draws weekly returns from a fat-tailed distribution with the target mean and a range of annualized volatilities, and reports what the year looks like. The full tables are in Appendix A; the rows that matter are these.

**At $5,000 a week (87% a year):**

| Annual vol | Weekly vol ($) | Required Sharpe | Losing weeks | Bad week (10th pct) | Good week (90th pct) | Median max drawdown | Bad-case drawdown | P(drawdown > 25%) | P(drawdown > 40%) | P(losing year) |
|---|---|---|---|---|---|---|---|---|---|---|
| 30% | $12,500 | 2.9 | 30% | −$8,500 | +$18,500 | −12% | −22% | 6% | 1% | ~0% |
| 45% | $18,700 | 1.9 | 36% | −$15,300 | +$25,300 | −21% | −38% | 36% | 8% | 5% |
| 60% | $25,000 | 1.4 | 40% | −$22,100 | +$32,100 | −31% | −53% | 70% | 28% | 13% |

**At $7,500 a week (130% a year):**

| Annual vol | Weekly vol ($) | Required Sharpe | Losing weeks | Bad week | Good week | Median max drawdown | Bad-case drawdown | P(drawdown > 25%) | P(drawdown > 40%) | P(losing year) |
|---|---|---|---|---|---|---|---|---|---|---|
| 30% | $12,500 | 4.3 | 22% | −$6,000 | +$21,000 | −9% | −18% | 3% | ~0% | ~0% |
| 45% | $18,700 | 2.9 | 30% | −$12,800 | +$27,800 | −17% | −32% | 22% | 4% | 1% |
| 60% | $25,000 | 2.2 | 35% | −$19,500 | +$34,600 | −26% | −46% | 55% | 17% | 4% |

**At $10,000 a week (173% a year):**

| Annual vol | Weekly vol ($) | Required Sharpe | Losing weeks | Bad week | Good week | Median max drawdown | Bad-case drawdown | P(drawdown > 25%) | P(drawdown > 40%) | P(losing year) |
|---|---|---|---|---|---|---|---|---|---|---|
| 30% | $12,500 | 5.8 | 16% | −$3,500 | +$23,600 | −8% | −16% | 2% | ~0% | ~0% |
| 45% | $18,700 | 3.9 | 25% | −$10,300 | +$30,300 | −15% | −28% | 15% | 3% | ~0% |
| 60% | $25,000 | 2.9 | 30% | −$17,000 | +$37,100 | −23% | −42% | 43% | 12% | 1% |

The reading is uncomfortable and should be. There are two ways to average $5,000 a week on $300,000. One is to run a process with a Sharpe ratio near 3 — a figure that, sustained over years, places a trader among the handful of records in Schwager's books that are not attributable to luck, and above the long-run figures commonly estimated for the great discretionary macro traders. The other is to run a process with a Sharpe ratio a good discretionary trader might actually achieve, around 1.5 to 2, at 45% to 60% annualized volatility. At 45%, that means a typical bad week costs $15,000, the median year contains a 21% drawdown, and one year in three sees a drawdown past 25%. At 60%, the bad week costs $22,000, the median drawdown is 31%, seven years in ten see a drawdown past 25%, more than one in four sees a drawdown past 40%, and there is a one-in-eight chance of a losing year. The $10,000 figure requires either a Sharpe near 4 or a drawdown profile that no part-time operator with this book's history should accept.

There is one more thing the tables do not show and the doctrine must say. The regime in which a 45%-to-60%-volatility book operates is the regime in which the volatile-day protocol fires constantly, in which the kill-switch ladder is tripped by ordinary variance, and in which the operator's specific historical failure — risk discipline collapsing on the loud days — has the most opportunity to express itself. Section 7.1's table describes what happens when it does. The target, adopted as given, does not merely demand a world-class process; it demands one operated by a trader who has never been the trader this doctrine is written for.

### 7.5 The target, treatment two: derived from the risk budget

The alternative is to specify the thing the operator can actually control — how much he is willing to lose — and let the return be whatever a process of a given quality produces within that constraint. The question becomes: for a maximum drawdown that is acceptable one year in ten, and for a process of a given Sharpe ratio, what is the largest volatility the book can run, and what average weekly P&L does that support?

The tables below answer it for three drawdown tolerances. Each row finds the highest annualized volatility at which a fat-tailed process of that Sharpe breaches the tolerance no more than 10% of the time in a year, then reports what that process yields. The simulation is again in Appendix A.

**Drawdown tolerance 15% ($45,000):**

| Process Sharpe | Max annual vol | Weekly vol ($) | Average week | Bad week | Good week | Losing weeks | Median year | 10th-pct year | 90th-pct year | P(losing year) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1.0 | 12% | $5,000 | $680 | −$4,700 | +$6,100 | 43% | $35,600 | −$11,400 | $89,400 | 17% |
| 1.5 | 14% | $5,800 | $1,220 | −$5,100 | +$7,500 | 39% | $66,600 | $6,600 | $138,600 | 8% |
| 2.0 | 16% | $6,700 | $1,860 | −$5,400 | +$9,100 | 36% | $108,500 | $32,900 | $199,600 | 3% |
| 2.5 | 18% | $7,500 | $2,590 | −$5,500 | +$10,700 | 33% | $162,100 | $66,500 | $280,200 | 1% |

**Drawdown tolerance 20% ($60,000):**

| Process Sharpe | Max annual vol | Weekly vol ($) | Average week | Bad week | Good week | Losing weeks | Median year | 10th-pct year | 90th-pct year | P(losing year) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1.0 | 16% | $6,700 | $940 | −$6,300 | +$8,200 | 43% | $48,800 | −$15,700 | $125,900 | 17% |
| 1.5 | 20% | $8,300 | $1,740 | −$7,300 | +$10,800 | 39% | $97,400 | $7,800 | $211,100 | 8% |
| 2.0 | 22% | $9,200 | $2,550 | −$7,400 | +$12,500 | 36% | $156,100 | $44,500 | $297,700 | 3% |
| 2.5 | 24% | $10,000 | $3,470 | −$7,400 | +$14,300 | 32% | $230,500 | $92,900 | $414,900 | 1% |

**Drawdown tolerance 25% ($75,000):**

| Process Sharpe | Max annual vol | Weekly vol ($) | Average week | Bad week | Good week | Losing weeks | Median year | 10th-pct year | 90th-pct year | P(losing year) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1.0 | 20% | $8,300 | $1,160 | −$7,900 | +$10,200 | 43% | $60,400 | −$21,500 | $163,900 | 18% |
| 1.5 | 24% | $10,000 | $2,070 | −$8,700 | +$12,900 | 39% | $118,700 | $7,500 | $263,800 | 8% |
| 2.0 | 28% | $11,600 | $3,230 | −$9,400 | +$15,800 | 36% | $204,600 | $53,700 | $416,500 | 3% |
| 2.5 | 32% | $13,300 | $4,610 | −$9,800 | +$19,100 | 33% | $334,700 | $120,000 | $634,900 | 1% |

The reading here is more useful than uncomfortable. At the drawdown tolerance the Phase 1 ladder implies — the Drawdown I switch at 12% and Drawdown II at 20% put the effective tolerance at roughly 20% — a process of Sharpe 1.5 supports an average week of about $1,700 and a median year near $100,000, with a bad week around −$7,000 and a losing year one time in twelve. A process of Sharpe 2.0, which is excellent, supports about $2,500 a week and a median year of $156,000. The operator's $5,000-a-week figure does not appear in these tables at all. The closest they come is $4,600 a week, at a 25% tolerance and a Sharpe of 2.5 — the average of a process whose median year is $335,000 and whose 90th-percentile year is $635,000. That is not a plan. It is what a Wizard-grade process looks like on average, and the $5,000 week is what it looks like in a good year.

The tables also make a point about volatility that the target-first treatment obscures: at every tolerance, the book that supports the highest return is the one with the *highest Sharpe*, not the highest volatility. Volatility is what the drawdown constraint rations; Sharpe is what the operator earns through process. The only lever the doctrine gives the operator for raising his average week is raising the quality of his decisions, as measured in the register. Raising his size is not on the list.

**The lumpy year.** There is one more model worth showing, because it is closer to how the Wizards' records actually look than a constant-Sharpe process is. Suppose most weeks are near flat — a disciplined base with a small positive drift and low volatility — and that a handful of times a year, when the three dials align and the exceptional tier is earned, the book takes a position that produces a large week. The simulation models a base of roughly 0.1% a week at 1.2% weekly volatility, with fat-pitch weeks averaging 5% at 5% volatility.

| Configuration | Average week | Median year | 10th-pct year | 90th-pct year | Realized annual vol | Realized Sharpe | Median max drawdown | Share of P&L from fat-pitch weeks |
|---|---|---|---|---|---|---|---|---|
| Disciplined base, 5 fat pitches a year | $1,710 | $94,000 | $24,600 | $192,500 | 17% | 1.7 | −6% | 84% |
| Disciplined base, 8 fat pitches a year | $2,580 | $154,700 | $59,000 | $292,600 | 21% | 2.1 | −5% | 90% |
| Aggressive base, 8 fat pitches a year | $3,740 | $241,100 | $77,000 | $498,300 | 31% | 2.1 | −11% | 87% |
| Aggressive base, 12 fat pitches a year | $5,290 | $397,200 | $159,600 | $784,500 | 35% | 2.6 | −10% | 91% |

This is the shape of the Livermore and Jones and Druckenmiller years: the money is made in a few weeks, the rest of the year is spent not losing it, and the average week is a statistical artifact of the few. The doctrine's exceptional tier, its two-per-month cap, its three-dial alignment test and its restriction of Books B and C to ordinary size the rest of the time are all designed to produce this shape. Note what it requires: eight to twelve genuinely exceptional configurations a year, each correctly identified and correctly sized, and a base process disciplined enough to lose almost nothing in the forty-odd weeks between them. The first is a claim about the reports; the second is a claim about the operator. Neither is yet demonstrated, which is why the exceptional tier does not exist in Phase 1: the lumpy year is the shape the book is built to grow into, not the shape it starts in.

### 7.6 The weekly number is noise

The operator's target is stated per week, and the doctrine has to say plainly why a weekly figure cannot be the score. The table is analytical, under a normal approximation; the simulated fat-tailed figures differ by a point or two.

| Annual Sharpe | Weekly Sharpe | P(positive week) | P(positive month) | P(positive quarter) | P(positive year) |
|---|---|---|---|---|---|
| 0.5 | 0.07 | 53% | 56% | 60% | 69% |
| 1.0 | 0.14 | 56% | 61% | 69% | 84% |
| 1.5 | 0.21 | 58% | 67% | 77% | 93% |
| 2.0 | 0.28 | 61% | 72% | 84% | 98% |
| 3.0 | 0.42 | 66% | 81% | 93% | 99.9% |

A Sharpe-2.0 process — which would place this book in rare company — loses money in 39% of weeks. A week's P&L is therefore almost entirely variance, and a trader who evaluates himself weekly is evaluating noise, with the predictable consequence that he changes what he is doing in response to it. The doctrine's Rule 22 follows: the weekly number is recorded and not judged. The score is the rolling thirteen-week expectancy by book and by regime, and the count of rules broken. At a quarter, a Sharpe-1.5 process is positive three times in four, which is enough signal to act on; at a week, it is a coin with a slight bias.

This also answers a question the target raises implicitly. "Average $5,000 a week" is an annual claim wearing weekly clothes. Restated as "$260,000 a year," it can be compared against the tables above and against the Wizards' records, and it can be planned for. Restated as a weekly expectation, it becomes a weekly disappointment in 35% to 45% of weeks even if it is being achieved, and the disappointment is what drives the over-sizing that ensures it is not.

### 7.7 Recommendation: the ladder

The operator asked to see both treatments and to choose. The doctrine's recommendation is that the choice is not between them but between *sequences*, and that the right sequence is budget-first with promotion gates that lead, if the register earns it, toward the aspiration.

**Phase 1 — budget-first, from activation.** Drawdown tolerance 20%, enforced by the ladder as written. Ordinary tier only at activation in every book; the good tier becomes available in a book after fifty closed decisions in it; the exceptional tier does not exist in Phase 1. The operating target is not a P&L figure at all; it is a set of process figures: rule-break count of zero, every packet complete, every post-mortem stamped, and a register of at least 100 decisions across Books A through C. The *expected* outcome, if the process turns out to be Sharpe 1.5 to 2.0, is about $1,500 to $2,500 a week averaged over the year — roughly 30% to 45% on capital, which is already the kind of year that the great discretionary records are made of — with a bad week near −$7,000 and a losing year somewhere between one time in twelve and one in thirty. The doctrine states this figure so that the operator knows what "working" looks like in Phase 1, and so that a $1,700 average week is recognized as success rather than as a shortfall against $5,000.

**Promotion to Phase 2** requires, at a monthly session, all of the following from the register: at least 150 closed decisions; a thirteen-week expectancy positive in every active book; a realized Sharpe of at least 1.5 over the trailing two quarters; no Drawdown I switch tripped in the period; and at least two distinct Macro dial states traversed. On promotion, the drawdown tolerance rises to 25% — Drawdown I moves to 15%, Drawdown II to 25% — the size tiers rise by one third, and the exceptional tier becomes available. Expected outcome at Sharpe 2.0: roughly $3,000 a week, a median year near $200,000.

**Promotion to Phase 3** requires at least 300 decisions, a realized Sharpe of at least 2.0 over the trailing four quarters, three Macro states traversed including at least one Transition, and a clean rule-break record. On promotion, the tolerance rises to 30% and the tiers rise again. This is the phase in which the $5,000-a-week average becomes a plausible median rather than a good year, and it is at least eighteen months away on the most favorable path.

**Demotion** is automatic: a Drawdown I switch in any phase returns the book to the prior phase's tolerances and tiers, and re-promotion requires the gate to be re-passed from a fresh window.

**The regime-conditional reading of the target.** The operator's own statement of the aspiration carried a qualification — that the regime and environment have to support the trade — and the qualification is what makes the aspiration coherent. Read as an unconditional weekly average, $5,000 to $10,000 is the 87%-to-173% process of Section 7.4. Read as a *conditional* figure — $5,000 to $10,000 in the weeks the dials are aligned and the exceptional tier is earned, and roughly nothing in the weeks they are not — it is the lumpy-year model of Section 7.5, and the arithmetic is different. Eight to twelve supportive windows a year, each producing a $5,000-to-$10,000 week, and forty weeks of disciplined near-flat trading, average to $1,700 to $5,300 a week depending on the aggressiveness of the base and the number of windows, at a realized Sharpe of 1.7 to 2.6 and a median drawdown of 6% to 11%. That is a demanding but coherent claim. It is a claim that the reports can identify the windows, that the operator will take them at the size the tier permits and no more, and that he will do almost nothing in between. The register counts the windows, and the promotion gates are how the count becomes permission.

**The benchmark test.** The operator also suspects that active trading in pursuit of out-performance may, for him, be illusory. The doctrine does not argue with the suspicion; it measures it. Over every trailing four quarters, the combined P&L of Books B, C and D is compared with two benchmarks: what Book A alone produced, and what a static 60/40 allocation of the same capital would have produced. If the active books do not beat both, on a risk-adjusted basis, their budgets are cut by a third at the next monthly session, and cut again a year later if the result repeats. The suspicion is, in other words, a standing hypothesis with a test date, and the doctrine's position is that a trader who is willing to let the data shrink his own active book is the only kind for whom the active book is worth keeping.

The sequence is champion-and-challenger applied to the operator's own risk budget, and it does for the target what the architecture's promotion gates do for the reports: it refuses to let anything run at full authority until it has earned it in data. The doctrine's position is that this is not a compromise of the aspiration. It is the only route to it that a trader with this book's history should trust, because every other route runs through the volatile days, and the volatile days have been decided already.

---

## Part VIII — The Rules

Each rule is stated, then traced to its origin among the Wizards or Livermore, then tied to the specific way this book has failed, then located in the component of the system that enforces it. A rule that the system cannot enforce is enforced by the register's rule-break count, which the weekly reflection report prints above the P&L. The rules are numbered for reference; the card in Part I carries the ten that are non-negotiable.

### Survival

**Rule 1 — The book survives first. Every other rule is subordinate to this one.**
*Origin.* Hite: if you lose all your chips, you can't bet. Jones: the most important rule is to play great defense, not great offense.
*Why it applies to me.* The retail record is not a record of bad ideas. It is a record of good ideas held at sizes that could not survive being wrong, and of the recovery from those episodes consuming the returns from everything else.
*Enforced by.* The kill-switch ladder, at the execution layer where the IBKR integration permits and in the register where it does not.

**Rule 2 — Never trade through a tripped switch. Re-entry happens at the next scheduled session, never sooner.**
*Origin.* Livermore, by negative example: every fortune he lost was lost by resuming before he had finished stopping. Marcus: after a large loss, get out and come back when you can think.
*Why it applies to me.* The morning after a bad day has historically been the second bad day. The instinct to "make it back" is the instinct the switch exists to interrupt, and a switch the operator can reset is not a switch.
*Enforced by.* The re-entry column of the ladder; execution-layer order refusal while a switch is active; the register flags any order placed inside a closed book.

**Rule 3 — On volatile days, I am the risk. Halve everything and act only from the list.**
*Origin.* Schwartz: after a big loss, trade small until confidence returns. Jones: the days after a large loss are the most dangerous. Platt: cut anything that is not behaving.
*Why it applies to me.* This is the stated failure mode. Not a bad strategy on ordinary days; a collapse of discipline on loud ones. The general rules require the operator to apply them, and on these days the operator's application is what fails. The protocol removes the application.
*Enforced by.* The volatile-day flag, machine-set in the 0700 report and not clearable by the operator; the halved multipliers; the 0700-list restriction; the cool-off timer.

**Rule 4 — Never add to a losing position. Adds are earned by confirmation — at a higher price for a long, a lower one for a short — because the market has moved my way, never because it has moved against me.**
*Origin.* Livermore's pyramiding, and Livermore's ruin when he inverted it. Marcus and Kovner both describe averaging down as the mechanism by which a small loss becomes a disaster.
*Why it applies to me.* Averaging down is the natural expression of conviction, and conviction was never this book's deficit. The behavior converts the swing book's 0.75% risk into an undefined risk without a packet.
*Enforced by.* The packet's add rule, which specifies the confirmation price; execution-layer refusal of adds below entry for longs and above for shorts; the register.

**Rule 5 — Every position has its exit written before entry: the price at which the thesis is wrong, the time by which it must have worked, and the plan for taking profit.**
*Origin.* Kovner: decide where you will get out before you get in. Brandt: the stop is honored without renegotiation, even on a chart he still believes. Seykota: the elements of good trading are cutting losses, cutting losses, and cutting losses.
*Why it applies to me.* A position without a written exit is a position whose exit will be decided by the P&L on the day, and the P&L on the day is the worst possible advisor. The "swing trade that became an investment" is a position that never had a time stop.
*Enforced by.* Packet required fields; DECISION_BLOCKED without them; OCO brackets placed at entry; time stops enforced by the close report.

### Edge

**Rule 6 — Edge before signal. A trade must name its edge family, say who is on the other side, and say why the edge has not been arbitraged away.**
*Origin.* This is Schwager's synthesis across all the books: the Wizards could each say why the money came to them. It is also the first question of the Market Wizards Alpha Framework.
*Why it applies to me.* The retail strategy was "data-informed" rather than "data-driven" because it could produce a reason to trade without producing a reason the trade should pay. A signal is not an edge; an edge is a signal plus a counterparty plus a persistence argument.
*Enforced by.* The three edge questions are required packet fields; the edge family is a required stamp; the ledger reports expectancy by family.

**Rule 7 — Asymmetry before hit rate. I optimize expectancy, not the number of green days. Minimum expected R is 1.5 for Books B and C and 3.0 for Book D.**
*Origin.* Jones's five-to-one; Dennis's willingness to be right a minority of the time; Mai and Saliba, whose entire businesses were built on small defined losses and occasional very large gains.
*Why it applies to me.* A high hit rate is psychologically rewarding and financially irrelevant; the retail record is full of strategies that won often and lost the year in a handful of trades. The 80%-hit-rate strategy that occasionally loses ten units is a losing strategy that feels like a winning one.
*Enforced by.* Expected R is a packet field with a minimum by book; the ledger reports average win, average loss and expectancy separately from hit rate, and the weekly reflection report prints them in that order.

**Rule 8 — Regime conditionality. No signal is trusted without its regime stamp. A signal outside its regime is ignored, not discounted.**
*Origin.* Kovner and Jones changed tactics with the environment; Dennis's systems earned most of their return in a minority of regimes; the 2026 volume's recurring theme is that edges erode and adaptation is survival.
*Why it applies to me.* Mean-reversion trades in a negative-gamma regime and breakout trades in a calm positive-gamma chop are both trades this book has taken, and both are trades that the trust matrix reads as Off. The signal was real; the regime was wrong; the loss was the same either way.
*Enforced by.* The three-dial stamp on every report and packet; the trust matrix; the regime card's permissions.

**Rule 9 — Price reaction outranks the headline. What the market does with news is the information; the news is the occasion.**
*Origin.* Platt, explicitly, in *Hedge Fund Market Wizards*: if the market cannot go down on bad news, it is telling you about positioning. Livermore watched the reaction, not the tape's explanation.
*Why it applies to me.* The retail tendency is to trade the narrative — buy the good number, sell the bad one — and to be surprised when the market does the opposite. The opposite is the trade. Book C's event-reaction setup exists to take it, and only after the reaction has been seen.
*Enforced by.* The 1000 report's confirmation and veto rights over the 0700 list; the event-reaction setup definition, which requires the reaction before the entry.

**Rule 10 — Doing nothing is a position, and often the best one. A no-trade week costs nothing and is logged as a decision.**
*Origin.* Rogers waits until there is money lying in the corner and walks over to pick it up. Livermore's "sit tight." Steinhardt's observation that the hardest thing is to do nothing when nothing is warranted.
*Why it applies to me.* The retail trader treats an open market as an obligation to act, and the frequency of his trades bears no relation to the frequency of his edge. The lumpy-year model in Part VII says the year is made in eight to twelve weeks; the other forty are for not losing.
*Enforced by.* Passes are logged in the register with a reason; the weekly reflection report scores restraint — the count of drafted packets declined — as a process metric alongside the count taken.

### Expression

**Rule 11 — The thesis and the instrument are two decisions. I trade the best expression for the volatility and gamma state, not the obvious one.**
*Origin.* O'Shea's bonds rather than short NASDAQ. Kovner's insistence on expressing a view where the risk-reward is best, not where the view is most direct.
*Why it applies to me.* Being right about direction and wrong about path has cost this book as much as being wrong about direction. The expression table converts a directional thesis into the structure that survives the path.
*Enforced by.* The expression table in Section 5.6 is a packet lookup; departures from the default must be justified in the packet; Gate 1.5's expression analytics measure whether departures paid.

**Rule 12 — Defined risk when I cannot watch. Undefined risk lives only in Book A's exposure bands.**
*Origin.* Saliba's and Mai's structural preference for convexity; Basso's observation that the trade should be sized so that the trader can sleep.
*Why it applies to me.* The operator is at work during the session. An undefined-risk position held through a session he cannot watch is a position whose risk is defined by the market, not by him.
*Enforced by.* The instrument whitelist per book; the volatile-day protocol's defined-risk restriction; execution-layer refusal of naked short options in Books B, C and D.

**Rule 13 — Costs are part of the edge. No trade whose expected R is less than three times its round-trip cost in commissions, spread and slippage.**
*Origin.* Thorp, Trout and Hull, for whom execution cost was the difference between an edge and its absence; the 2026 volume's emphasis on execution as a competence.
*Why it applies to me.* Short-horizon trades in options with wide markets have a cost that the retail trader does not compute and that consumes most of the expectancy of a 0.35%-risk position.
*Enforced by.* Gate 1.5's execution analytics; a cost field in the Book C and D packets; the ledger's turnover and slippage columns.

### Sizing

**Rule 14 — Size to the opportunity in three tiers. Exceptional exists only from Phase 2 and requires three-dial alignment, a High-trust signal, one independent confirmation, and a Top & Bottom reading that does not contradict. No more than two exceptional packets a month.**
*Origin.* Druckenmiller's pig; Jones's shift from defense to offense when the configuration is rare; Thorp's fractional Kelly.
*Why it applies to me.* The retail record sized to conviction, which meant the largest positions were the most emotionally invested rather than the most favorably configured. The tier test replaces conviction with a checklist.
*Enforced by.* The sizing calculator computes the tier from the stamps and refuses a tier the stamps do not support; the monthly cap is a register count.

**Rule 15 — Quarter-Kelly is the ceiling, not the target, and it is a ceiling I cannot see until the register has measured the edge.**
*Origin.* Thorp, who used fractional Kelly precisely because the edge is estimated, not known, and who observed that over-betting a true edge is the fastest way to lose it.
*Why it applies to me.* The book's edge is, as of Phase 1, a hypothesis. Sizing at a fraction of a fraction is what one does with a hypothesis. The promotion gates move size toward Kelly as the hypothesis becomes a measurement.
*Enforced by.* The tier figures are fixed per phase; the phases change only at a monthly session on register evidence.

**Rule 16 — Heat is capped across books, and correlated positions count once. Net exposure across all books is capped at Book A's band ceiling plus fifteen points.**
*Origin.* Kovner's and Jones's attention to correlated exposure; the collective experience of the 1987 and 2008 Wizards that diversification across instruments is not diversification across risk.
*Why it applies to me.* Four books long the same factor on the same day is one trade with four names, and it is the trade that produces the −8% week of Section 7.1.
*Enforced by.* The heat calculator on the register; the net-exposure figure at the top of the weekly reflection report; execution-layer refusal of orders that would breach either cap.

**Rule 17 — Exits follow the plan, not the P&L. Profit is taken where the packet said, reduced into strength on exceptional-tier positions only, and never "let run" past a time stop because it is winning.**
*Origin.* Livermore's sit tight is about holding through noise, not about abandoning the plan; Brandt's profit-taking is written in advance; Seykota's systems exit on rules, not on feelings.
*Why it applies to me.* The retail record contains both errors: taking profit early out of fear and holding past the plan out of greed. Both are decisions made by the P&L. The plan was made by the process.
*Enforced by.* The profit plan is a packet field; brackets carry the profit leg; time stops are enforced by the close report.

### Process

**Rule 18 — No Decision Packet, no trade. A packet missing a required field is DECISION_BLOCKED, however good the trade looks.**
*Origin.* Every Wizard who kept a journal, which is most of them; the 2026 volume's insistence on reviewing trades like game film, which requires that the game was recorded.
*Why it applies to me.* The retail strategy was not data-driven because its decisions were not recorded in a form that data could be extracted from. The packet is the record and the friction; the friction is the point.
*Enforced by.* The architecture's decision governance: immutable packets, the point-in-time store, REPORT_OK versus DECISION_BLOCKED.

**Rule 19 — Top-down sets the budget; bottom-up spends it. A lower horizon may veto but never enlarge.**
*Origin.* Kovner and Jones both describe the macro view as the frame within which the trades are chosen, never as a justification for the size of a trade. O'Shea's expression discipline is the same idea applied to instruments.
*Why it applies to me.* "The macro is bullish, so I'll buy this dip at three times size" is a sentence this book has spoken. The macro is the band; the dip is a Book C packet at a Book C size.
*Enforced by.* The authority rule of Section 6.1; the net-exposure cap; the size multipliers, which only ever reduce.

**Rule 20 — Rules change only at the monthly session, never during a drawdown, and every change is logged with its reason and its expected effect.**
*Origin.* Seykota: the system must fit the trader, and a system that is changed every time it loses is not a system. Schwager on adaptation: the Wizards adapted deliberately, on evidence, not reflexively, on pain.
*Why it applies to me.* Rule changes made during drawdowns are made to relieve the drawdown, not to improve the process, and they are the mechanism by which a retail trader has a new strategy every quarter.
*Enforced by.* Rules are versioned in the repository; changes are commits with reasons; the register stamps every packet with the rules version in force; champion-and-challenger applies to rule changes as it does to report versions.

**Rule 21 — Every loss and every large win is reviewed as game film, against the six questions, before the next session opens.**
*Origin.* The 2026 volume, and Schwager's and Coyle's commentary around it: journaling and post-mortem review are the practices most consistently reported by the traders who lasted.
*Why it applies to me.* Losses that are not categorized are losses that will recur, because the category is what the operator can act on. Was the thesis wrong, the timing wrong, the expression wrong, the size wrong, the regime changed, or the signal degraded? Each has a different remedy, and "I lost" has none.
*Enforced by.* The post-mortem stamp is a required field for packet closure; the weekly reflection report lists unstamped packets first.

**Rule 22 — The weekly number is noise. The score is rolling thirteen-week expectancy by book and by regime, and the count of rules broken.**
*Origin.* Thorp and Woodriff on sample size; Schwager's definition of consistency as risk-adjusted excess return over many independent decisions and multiple regimes, not over calendar periods.
*Why it applies to me.* The target was stated per week, and a Sharpe-2 process loses money in 39% of weeks. A trader who judges himself weekly changes what he is doing in response to variance. The retail record is, in part, a record of responding to noise.
*Enforced by.* The weekly reflection report prints the thirteen-week figures and the rule-break count above the weekly P&L; the monthly session reviews the quarterly figures and nothing shorter.

### Self

**Rule 23 — Never confuse being a good market observer with being a good risk manager. Sustainable alpha requires both, and this book has only ever had the first.**
*Origin.* Livermore, whole and entire.
*Why it applies to me.* The observer was never the problem. The doctrine's every restrictive rule is the risk manager the observer never hired.
*Enforced by.* This is the motto; it is enforced by the rest of the rules.

**Rule 24 — I trade the book I have: part-time, semi-automated, four books, $300,000. No new instrument, venue, book or strategy is added without a gate.**
*Origin.* Seykota on fit; Schwager's finding that the method must suit the trader's life, not the other way round; the 2026 volume's traders, who mostly found one thing that fit them and did it.
*Why it applies to me.* The retail record includes strategies that were right for a full-time trader and wrong for this one, and instruments that were right for a larger book. Scope creep is a rule break, not an experiment.
*Enforced by.* The instrument whitelist; the Security Master; the adoption sequence's gates; the monthly session as the only place scope changes.

**Rule 25 — Brookfield-family securities are never traded, in any book, in any expression, for any reason.**
*Origin.* Not a Wizard. Employment.
*Why it applies to me.* The overhang tracker and the thematic alerts are the places where a related name is most likely to surface, and Book D is the book most likely to act on it quickly.
*Enforced by.* The Security Master's exclusion list, checked at packet drafting and again at order placement.

### Self — the known biases

**Rule 26 — My neutral is short. A short requires one more confirmation than a long, is not opened outright in an Expansion, Calm, Positive regime, and a short campaign ends on the Top & Bottom bottom signal, not on conviction.**
*Origin.* Livermore, whose great trades were shorts and whose great losses followed them; Druckenmiller's 1999 technology short, right in thesis, a year early, and abandoned at the worst moment; the Top & Bottom report's own finding that bottoms are what it catches.
*Why it applies to me.* The preference is stated and acknowledged. The 2020 record is the specimen: profitable into the collapse, unprofitable through the recovery, because the campaign was ended by the P&L rather than by a signal. A bias that is measured before it is indulged is a bias that can be managed.
*Enforced by.* The regime card's Book B permissions; the extra-confirmation field on short packets; the sixth conflict rule; the ledger's long-versus-short cut, printed short-first.

**Rule 27 — I do not fight the tape. A counter-trend position is ordinary tier, carries a five-session time stop, and is never added to. If the trend has not turned by the fifth session, the position is closed, whatever the thesis.**
*Origin.* Livermore: trade with the primary trend. Seykota: the trend is your friend except at the end when it bends. Jones: losers average losers. The uniformity of the Wizards on this point is total.
*Why it applies to me.* Holding against the trend for days and weeks is, by the operator's own account, the behavior that has killed him. The thesis was often right and always early, and being early with size is the same as being wrong. The five-session stop lets the observer try and stops the risk manager's absence from costing weeks.
*Enforced by.* The counter-trend flag on the packet, set from the Technical Indicators structure; the shortened time stop enforced by the close report; execution-layer refusal of adds on flagged positions; the ledger's with-trend versus counter-trend cut.

**Rule 28 — A tail thesis is a hedge budget, not a position. Cynicism about the system is expressed in Book D's ring-fenced tail budget, in convexity, and nowhere else.**
*Origin.* Mai and Saliba, for whom tail exposure was a defined-cost business, not a stance; Kovner, who hedged what he feared and traded what he expected; Rogers, who waited rather than positioned.
*Why it applies to me.* The worry about tail events, including the monetary system, is a durable feature of the operator's temperament and is not going to be argued away. Its historical expression — as a standing short, as a stance below the floor, as a reason not to be long — has cost far more than a hedge budget would have. Given a defined-risk home at $1,200 a month, the worry becomes a line item; denied one, it becomes the book's net exposure.
*Enforced by.* The tail budget as a separate Book D sub-ledger; the Book A floor; the ledger's hedge-spend and hedge-payoff columns.

**Rule 29 — Book A's floor is as binding as its ceiling. Being under-invested against the regime is a rule break, and the 2008 imprint is not an exception to the floor but the reason for it.**
*Origin.* Lynch and Buffett on the cost of being out; every trend follower's finding that the large move is missed by those waiting for the pullback; Schwager's definition of consistency across regimes, which includes the regimes in which the index does the work.
*Why it applies to me.* Fifteen years of reluctance to hold a long-term long position is the largest single cost in the operator's record, larger than any losing trade, and it is invisible in a trade ledger because it never appears as a loss. The floor makes it appear.
*Enforced by.* The Book A stance is checked against the floor at every monthly session and every weekly review; a stance below the floor is counted as a rule break; the ledger reports Book A's realized exposure against the band.

---

## Part IX — Measurement, Learning, and Adoption

### 9.1 The ledger

The doctrine's claim that it is self-correcting rests on the ledger, and the ledger rests on the register. The metrics are the ones the Market Wizards Alpha Framework listed, and each is reported by book, by regime state, by signal family, and by long versus short — because the differences between those cuts are where the information is.

The core economics are the number of independent decisions, the hit rate, the average winner, the average loser, and the expectancy in R. The quality of returns is measured by the gain-to-pain ratio, the Sharpe and Sortino ratios, and the maximum drawdown, and the hidden catastrophe risk by the tail loss — the worst 5% of decisions and what they had in common. Capital efficiency is measured by holding period and by turnover and slippage. The framework's most important cuts are performance by regime, which is how the trust matrix is revised; performance long versus short, which is usually asymmetric, which the retail trader never separates, and which for this operator is printed short-first because the bias is known; performance with-trend versus counter-trend, for the same reason; Book A's realized exposure against its band, so that under-investment is visible; the tail-hedge budget's spend and payoff; signal half-life, which determines how quickly a draft must be acted on; correlation between books, which is the diversification the doctrine claims and must demonstrate; and edge decay, which is the trailing expectancy of each signal family plotted over time.

Minimum sample sizes are enforced before any figure is acted on. No signal family's trust level is changed on fewer than thirty decisions in the relevant regime. No book's size tier is changed on fewer than fifty. No phase promotion happens on fewer than the counts in Section 7.7. Until those samples exist, the figures are printed with their sample sizes beside them and treated as descriptive.

### 9.2 The six questions

Every closed packet carries the answers to six questions, and the answers are categorical so that they can be counted. Was the thesis wrong? Was the timing wrong? Was the expression wrong? Was the size wrong? Did the regime change during the trade? Was the signal itself degraded — that is, has this signal family's trailing expectancy fallen below its long-run figure? A seventh field records whether any rule was broken, and which.

The categories are the remedies. A thesis error is a report problem and goes to the monthly session for the report's owner to consider. A timing error is a signal-half-life problem and goes to the trust matrix. An expression error is an O'Shea problem and goes to the expression table. A size error is a tier-test problem. A regime change is a transition-rule problem. A degraded signal is an edge-decay problem and goes to champion-and-challenger. A rule break is an operator problem and goes to the operator, by name, in the weekly reflection report.

The behavioral paper that the work plan deferred by six months is to be written from these fields. The doctrine's contribution to that paper is to specify now what it will need: the seven categorical fields, the regime stamp, the tier, the time of day the packet was written and the time it was executed, whether the packet was machine-drafted or operator-written, whether the volatile-day flag was on, and the operator's one-line reason for any pass. With those fields populated for six months, the behavioral paper can say which of the retail pathologies survived the doctrine and which did not, and it can say it in numbers.

### 9.3 Edges decay and rules are hypotheses

Schwager's most consistent finding across four decades is that edges erode. The traders who lasted noticed and adapted; the traders who did not are not in the books. The doctrine treats this as a design requirement rather than a warning: every signal family has a trailing expectancy, every trust level in the matrix is a hypothesis with a sample size, and every rule in Part VIII is a hypothesis about the operator that the register tests.

The architecture's champion-and-challenger mechanism, built for report versions, applies to rules. A proposed rule change at a monthly session is a challenger; it runs alongside the champion for a defined period — in paper for rules that change size, in production for rules that only restrict — and it is promoted or withdrawn on the ledger's evidence. A rule that has never been broken and never bound is a candidate for removal; a rule that binds constantly is a candidate for tightening or for a rethink of the book it binds. The rules version is stamped on every packet so that the ledger can be cut by rules regime as well as by market regime.

The Positioning & Flows paper, when written, will introduce new signal families and therefore new rows in the trust matrix. They enter at Low or Medium with a sample-size requirement, and they earn High. Nothing enters at High.

The regime multipliers are hypotheses of the same kind, and one of them is worth naming. The operator's record says he has sometimes done well in volatile markets, and the doctrine's Rising and Stressed multipliers are set conservatively against the extreme-volatility failures rather than generously toward the volatile-market successes. If, after fifty decisions in each, the register shows that his Rising-regime and Stressed-regime expectancy in Book C is his best, the Phase 2 multipliers for those states can rise — deliberately, at a monthly session, on that evidence. The doctrine's conservatism on volatile days is a starting point, not a verdict.

### 9.4 Adapting without drifting

The distinction between adaptation and drift is the distinction between the Wizards and the retail trader, and it is a distinction of process rather than of outcome. Both change what they do. The Wizard changes it deliberately, at a scheduled review, on evidence, with a record of what was changed and why, and with the change tested before it is trusted. The retail trader changes it reflexively, during a drawdown, in response to pain, without a record, and with the change trusted before it is tested.

The doctrine's adaptation protocol is therefore procedural. Changes to any rule, tier, band, threshold or trust level are proposed only at the monthly session. No change is proposed in a month in which the monthly or a drawdown switch has tripped; that month's session reviews and does not revise. Every change is a commit with a reason and an expected effect, and the ledger reports whether the effect occurred. A change that is reversed within two sessions is flagged, because two reversals in a row is the signature of drift.

The operator's history is relevant one last time. The retail strategy was not one strategy; it was a sequence of them, each adopted after the previous one's drawdown and each abandoned in its own. The single most important structural feature of the doctrine is that it makes that sequence impossible without a paper trail, and the paper trail is what will show, six months from now, whether the doctrine has been followed or merely written.

### 9.5 The adoption sequence

The books are activated in the order that least depends on automated enforcement and that most quickly builds a register, and each activation is a gate.

**Now, before any book is active.** The register is live with the packet schema of Section 6.4 and the post-mortem fields of Section 9.2. The 0700 report stamps the three dials and raises the volatile-day flag. The weekly reflection report prints the thirteen-week figures, the heat and net-exposure figures, and the rule-break count above the P&L. The Security Master carries the exclusion list. The sizing calculator computes tiers from stamps. None of this requires the broker integration.

**Gate A — Book A activates first.** It requires only the Monthly and Top & Bottom reports, which exist and publish; a rebalance is a set of limit orders placed by hand on a Monday; and the book's risk is governed by bands rather than by switches, which means it can be run to rule before the execution layer can enforce anything. Activation at the next monthly session. The first month's stance is set in the lower half of the current Macro band, which the Disruptive Themes composite at −1.2 would require in any case.

**Gate C — Book C activates second, restricted.** Once Book A has run for a month to rule and the 0700 and 1000 reports are publishing on time from the VPS, Book C activates in Positive-gamma and Calm-or-Rising regimes only, with defined-risk expressions only, at ordinary tier only, and with brackets placed by hand at entry. The restriction to Positive gamma is deliberate: it is the regime in which the fade-toward-pin setup has the cleanest edge and in which the volatile-day protocol is least likely to be needed, and it keeps the book's first fifty decisions away from the conditions in which the operator's history is worst. Negative-gamma continuation setups activate after fifty decisions and a positive thirteen-week expectancy, or after IBKR Gate 1 passes and brackets are server-side, whichever is later.

**Gate B — Book B activates third.** Once the weekly reflection report is drafting candidates with complete packets and Book C has shown the operator can run a book to rule daily, Book B activates at ordinary tier with a maximum of three positions. The exceptional tier for Book B activates only in Phase 2.

**Gate D — Book D activates last.** After Books A, B and C have each run a full month with a rule-break count of zero, and after the alert layer is producing alerts that the operator has been logging as passes for at least a month — which is to say, after the operator has demonstrated that he can see a meme spike and not trade it. Book D's budget in its first quarter is half the figure in the card.

**The IBKR gates.** Gate 1 moves bracket placement and kill-switch enforcement to the execution layer, at which point the register's rule-break count should fall to zero by construction for the rules the layer enforces. Gate 1.5 adds the expression and execution analytics that Rules 11 and 13 need to be measured. The *Building and Validating a Systematic Book* paper is scheduled before Gate 1 and will specify the validation the doctrine assumes.

### 9.6 Closing: the trader this is written for

The paper began by saying it was written against the trader the operator has been. It should end by saying what it expects of the trader he is becoming, because the doctrine is not a set of constraints on a bad trader; it is the operating system of a good one, and the Wizards' evidence is that the difference between the two was never analytical.

The trader this is written for reads the 0700 report over coffee, approves or rejects three drafted packets, and goes to work. He does not look at the market until the 1000 report, and after that not until the close. On Sunday he spends an hour with the weekly reflection report, stamps last week's post-mortems, and stages next week's swing candidates with their brackets. Once a month he spends ninety minutes setting a stance he will not touch for a month. When an alert fires he gives it fifteen minutes and usually passes. When the volatile-day flag is up he halves everything and acts only from the list, and he does this without deciding to, because the machine has already halved it. He is long when the regime says long, at no less than the floor, and it costs him something to be, and he pays it. When he is short and the bottom signal fires, he covers, and logs his disagreement as a pass. His tail worry has a budget and spends it. His weekly P&L is a number he records and does not judge. His score is a thirteen-week expectancy and a rule-break count of zero, and when the expectancy is positive across two regimes and 150 decisions he raises his risk budget by a step, and not before.

He will average something like $1,500 to $2,500 a week in Phase 1 if the process turns out to be as good as a good discretionary process is, and he will regard that as the success it is. He will have the occasional $10,000 week and the occasional −$7,000 week and he will treat them identically, as variance. If, eighteen months from now, the register says the process is Wizard-grade, he will be running the book at the size the aspiration requires, with the drawdown tolerance to match, and the aspiration will be a plausible median rather than a good year. If the register says otherwise, he will know that too, in numbers, and he will be solvent.

The observer was always good. The doctrine is the risk manager. The book needs both.

---

## Appendix A — The simulations

All simulations draw weekly returns from a Student-t distribution with four degrees of freedom, scaled to the stated mean and volatility, over a fifty-two-week year, with equity compounding from $300,000. The fat tails are deliberate and make every drawdown figure in Part VII more conservative than a Gaussian assumption would. No kill switches are modeled in the return distribution, for the reason given in Section 7.2: switches make the realized distribution behave like the assumed one; they do not add expectancy. Forty thousand paths for the target-as-given tables; twenty thousand for the budget-first search, which finds the largest annualized volatility, in 2% steps, at which the probability of a maximum drawdown beyond the tolerance is at most 10%.

The target-as-given tables in Section 7.4 show the 30%, 45% and 60% volatility rows; the script also runs 20% and 80%. At 20% volatility the required Sharpe ratios are 4.3, 6.5 and 8.7 for the three targets — figures with no precedent in the discretionary record. At 80% volatility the required Sharpe falls to 1.1, 1.6 and 2.2, and the median maximum drawdown is 35% to 44% with a bad-case drawdown of 59% to 70%; the probability of a drawdown beyond 40% is 37% to 60%.

The retail-failure-mode simulation of Section 7.1 adds, to a Sharpe-1.0, 25%-volatility base process, a number of randomly placed weeks per year in which an additional 8% of capital is lost, representing an oversized position on a volatile day held without a stop.

The lumpy-year model draws each week from one of two distributions: an ordinary week with a mean of 0.1% (disciplined) or 0.2% (aggressive) and a weekly volatility of 1.2% or 2.5%, or a fat-pitch week with a mean of 5% (disciplined) or 7% (aggressive) and a matching volatility, with the fat-pitch weeks occurring at the stated annual frequency.

The Kelly table uses the standard formula for a binary outcome, f = p − (1 − p) / b, where p is the hit rate and b the ratio of average win to average loss. The signal-to-noise table in Section 7.6 is analytical under a normal approximation rather than simulated.

The script `doctrine_simulations.py` sits beside this paper and reproduces every figure with fixed seeds; Monte Carlo figures are quoted to the nearest hundred dollars or whole percentage point.

## Appendix B — The Decision Packet, by book

Common to all books: book; edge family; owning report and section; regime stamp (Macro, Volatility, Gamma, volatile-day flag); rules version; thesis in one sentence; the three edge questions; expression and reason for any departure from the table; size tier and computed dollar risk; invalidation level; time stop; profit plan; expected R; expected holding period; cost estimate (C and D); whether machine-drafted or operator-written; time written; time executed. On closure: realized R; the six post-mortem categories; rule-break field; one-line note.

Book A adds: target exposure by sleeve; band and position within band; the T&B reading; the Themes composite; hedge structure if in Transition or Stressed.

Book B adds: pivotal point and its type (breakout, reclaim, failed breakdown); direction, with the extra-confirmation field required for shorts and the regime permission check; counter-trend flag from the Technical Indicators structure, which sets the five-session time stop; add rule with confirmation price; maximum position count check; heat check.

Book C adds: setup type (fade-toward-pin, continuation, event reaction); gamma flip level and distance; bracket legs; 1000-report confirmation status; whether entered before or after 10:30.

Book D adds: alert source; catalyst and its date; liquidity check (can the position be exited in one session at ordinary size); Security Master check; tail-budget flag, which charges the position to the ring-fenced hedge budget rather than the general Book D budget.

Passes are logged with: book; alert or draft source; one-line reason; regime stamp.

## Appendix C — Crosswalk to the companion library

The three dials are read from: the Macro dial from the *Monthly Macro Working Manual* and the *Rate and Liquidity Machine*; the Volatility dial from *Volatility*; the Gamma dial from *The Dealer's Hand*, Part V. Book A's bands draw on *Portfolio Construction Across Regimes* when written, and on *Equities*, *Metals*, *Digital Assets*, *Currencies* and *Energy* for the sleeves. Book B's pivotal points and confirmation draw on *Technical Indicators*. Book C's setup taxonomy is the *Daily Cascade* paper's Chapter 2 as elaborated in *The Dealer's Hand*. Book D's alert vocabulary draws on *Foundations*, *The Twenty-Five*, and the prediction-market amendment. The trust matrix's positioning row is a placeholder for *Positioning & Flows*. The validation the doctrine assumes is specified in *Building and Validating a Systematic Book*. The behavioral paper deferred to early 2027 is to be written from the register fields in Section 9.2.

The library guide is the canonical source of series numbering. This paper's masthead is to be relabelled on commit.

---

*End of paper.*
