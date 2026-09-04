# TECHNICAL INDICATORS — COMPANION XIV

### Price-Derived Measures: What They Know, What They Cannot, and Where They Belong in the System

**Version 1.1 · September 1, 2026 · Companion to the Daily Cascade and the execution layer · Worked illustrations added in v1.1**

*This is the shortest paper in the library, deliberately. Technical analysis has generated more written material than any other subject in markets, and most of it fails a simple test stated in Chapter 1. What survives that test fits in a short document. The paper's job is to say precisely what price-derived indicators can contribute to this system, wall off what they cannot, and name the traps — several of which this system's own methodology rules were built to catch in other domains and apply here with full force.*

---

## Chapter 1 — What Technicals Can and Cannot Know

Begin with the uncomfortable part, because everything else in the paper depends on stating it plainly.

Nearly every technical indicator is a transformation of price, volume, or both. A moving average is a smoothed price. RSI is a normalized ratio of recent gains to recent losses — a transformation of price changes. MACD is the difference of two smoothed prices. Bollinger Bands are a rolling mean and standard deviation of price. Stochastics locate the current price within its recent range. Rate-of-change is price arithmetic, stated as a percentage.

This has a consequence that most technical writing avoids: **a transformation of price cannot contain information that price does not already have.** If the close is the input, the indicator is the input with a haircut and a lag. Whatever the indicator "sees," the price series saw first, by construction. The indicator's contribution is not new information — it is *compression*: a rule for summarizing what price has been doing, in a form a human or a system can act on consistently.

That is not a dismissal. Compression is genuinely valuable, for the same reason a percentile rank is valuable even though it adds nothing to the raw series: it standardizes, it removes discretion in the reading, and it makes today comparable to history. The failure mode is not using compressed price — it is mistaking compression for discovery, and treating an indicator's agreement with another indicator as confirmation when both are the same input wearing different clothes. Chapter 7 returns to this at length, because it is the central trap of the entire field.

Three uses survive the lag argument, and they organize the rest of the paper.

**First: regime classification.** "Is this market trending or ranging, compressing or expanding?" is a question about the *character* of price action, not its direction, and it can be answered from price history without pretending to predict. Regime measures are backward-looking on purpose — a regime is a description of the recent past that tends to persist. Persistence, not prediction, is what makes them useful. This is the strongest legitimate use, and it is the one this system already leans on: the gamma regime, the funding regime, and the leverage regime composite are all regime classifiers built from non-price data, and Chapter 2's measures are their price-derived siblings.

**Second: levels as coordination points.** A 200-day moving average has no physical significance. It matters — when it matters — because enough participants watch it that behavior clusters around it: stops beneath it, buy orders at it, commentary anchored to it. That is a *reflexivity* argument, identical in structure to the options-pinning argument in the Dealer's Hand: the level works because positioning concentrates there, and it stops working when positioning does not. Chapter 6 develops this, including the limits — a level that everyone watches is also a level that sophisticated flow trades *against*.

**Third: timing and location inside a view held on other grounds.** Once the macro system says "lean long duration" or the swing thesis says "fade strength toward the wall," a technical structure answers the questions the thesis leaves open: where is the entry, where is the invalidation, what does "wrong" look like in price terms. Used this way, technicals never decide *whether* — they decide *where* and *when*, inside a decision already made. This is their role in the execution block, and it is the only place in the system where they touch a trade.

What does **not** survive the lag argument: technicals as a standalone forecasting system. The evidence on simple technical rules as return predictors is, on the academic record, weak after costs and unstable across periods — rules that worked in one era (moving-average crossovers in trending FX markets of the 1970s–80s) degraded as they were arbitraged and as market structure changed. Where studies find persistent value, it clusters exactly where the three uses above predict: in regime description, in short-horizon liquidity effects, and in assets or eras with heavy trend-following participation — reflexivity again. The honest summary is that technicals describe well and predict poorly, and every use in this system is built on the describing.

One more distinction before the catalogue, because the paper depends on it. **A lagging measure is not a useless measure.** The Sahm Rule is a lagging transformation of the unemployment rate; it earns its place because it classifies a state reliably. The CCC spread lags the deterioration of the companies inside it; it earns its place because it prices that deterioration continuously. The objection to technicals is not that they lag — everything lags — it is that they lag *price itself*, the one series the market prices in real time. The bar they must clear is therefore higher: they must organize price history into something more decision-useful than the raw chart. The chapters that follow keep only the measures that clear it.

---

## Chapter 2 — Regime Measures: The Family That Survives Scrutiny

The regime question — trending or ranging, quiet or violent, compressing or expanding — is the most valuable thing price history can answer, because regime persistence is one of the few robust empirical facts in markets. Volatility clusters. Trends, once established, persist somewhat longer than chance. Ranges, once established, contain price somewhat longer than chance. None of these persistence effects is strong enough to trade on its own; all of them are strong enough to *condition* on.

**Realized volatility, in windows.** The foundation of the family, and not usually called a "technical" — which says something about the label. Twenty-day realized vol against its own one-year percentile answers "is this market moving more or less than is normal for it," and the percentile framing matters more than the level: 15 vol is quiet for a single stock and violent for a bond index. The system already computes this pattern everywhere; the only note specific to price is to use log returns and to be deliberate about the window, since the window *is* the regime definition. Twenty days describes the tactical regime; sixty describes the swing backdrop. Both, side by side, tell you when the short regime has diverged from the long one — which is the actual signal, and the same construction as the SPHB/SPLV realized-versus-implied pairing in `internals`.

**Range and compression measures.** Average true range (ATR) is realized volatility's intraday cousin — it captures gap risk and intrabar range that close-to-close vol misses, which is why the reactive-trade triggers and the expected-move comparisons in the Daily use it. Compression measures — current ATR or band width against its own percentile — describe coiling: narrow ranges resolve into expansions more reliably than they persist, one of the few forward-leaning statements in this paper, and even it says nothing about *direction*. Compression is a size-and-attention signal, not a positioning signal: the honest trade on compression is owning optionality or widening stops, never picking the breakout side in advance.

**Trend-strength measures, direction removed.** ADX is the standard: it asks "how one-sided has directional movement been," without caring which side. Read it as a classifier with bands — below ~20, range dynamics dominate and mean-reversion tactics have their best environment; above ~25–30, trend dynamics dominate and fading strength is fighting the tape. The specific thresholds are fitted parameters (Chapter 7's warning applies — shift them and the classification wobbles at the margin), so use them as bands with hysteresis rather than lines: require the measure to *cross and hold* before reclassifying, exactly as the pillar scoring rules require persistence before a regime label changes.

### Worked illustrations — reading the regime lines

Six illustrative mornings, index at roughly 7,700. Every number is synthetic but
sized to be realistic; the point is the *mapping* from readings to classification
to behavior.

| Morning | 20d RV (pctile) | ATR (pctile) | ADX | Classification | Tactical consequence |
|---|---|---|---|---|---|
| A | 11.2% (28th) | 62 pts (31st) | 15 | Range, quiet | Fade edges; breakout entries penalized; normal size |
| B | 9.8% (12th) | 48 pts (9th) | 13 | Range, **compressing** | Reduce directional size; own optionality; expect expansion, direction unknown |
| C | 14.5% (55th) | 78 pts (58th) | 24 | Transitional | No oscillator trades either way; wait for the band to resolve |
| D | 18.9% (78th) | 105 pts (81st) | 31 | **Trend**, established | Pullback entries with trend; fading strength is fighting the tape |
| E | 27.4% (96th) | 160 pts (97th) | 38 | Trend, violent | Halve unit size (stops scale with ATR); no counter-trend at all |
| F | 16.0% (60th) | 88 pts (66th) | 19 ↓ from 27 | Trend **decaying** | Hysteresis: still classified trend until ADX holds < 20; tighten trailing stops |

Note the two disciplines the table encodes: morning C produces *no* trade
permission in either direction — transitional readings are a real state, not a
failure to classify — and morning F stays classified as trend despite the ADX
print, because reclassification requires the cross to *hold* (hysteresis), not
to occur.

*[Figure 1 renders in the HTML edition.]*

*[Figure 2 renders in the HTML edition.]*

**A worked reading, to fix the pattern.** Suppose the morning lines show: 20-day realized vol at the 28th percentile, ATR compressed to the 12th percentile of its two-year range, ADX at 15, and price mid-range between the put wall and call wall from the options stack. The classification writes itself: quiet, coiling, directionless, and pinned between hedging levels — a range regime with compression building. The tactical consequences are mechanical: mean-reversion tactics at the range edges are favored, breakout entries are penalized until the compression resolves, position sizes for any directional attempt are reduced (compression resolves violently, and a stop inside a coil is a stop inside the noise), and the one forward-leaning note is attention — compression at the 12th percentile does not persist, so the Weekend Synthesis should carry "expansion likely within the swing window, direction unknown." Nothing in that paragraph predicted anything. All of it changed behavior. That is the family working as intended.

**Where the regime family reports.** Into the Daily's Market Base and Confirmation blocks as context lines — "20d RV 34th percentile, ATR compressing, ADX 17: range regime, mean-reversion tactics favored" — and into the Weekend Synthesis as the price-regime backdrop for the swing thesis. Never into the Monthly, whose Momentum pillar is a macro-momentum pillar and should stay one. And always as conditioners: `trigger_eligible: false` across the family, because a regime label describes the environment a signal fires in; it is not the signal.

---

## Chapter 3 — Trend and Momentum: Useful, Crowded, and Honest About Which

Trend measures answer "which way has this been going, and how persistently." They are the most heavily used family in the field and the one with the strongest institutional footprint — trend-following CTAs run meaningful assets on systematized versions of exactly these rules, which cuts both ways: the persistence is real enough that an industry monetizes it, and the crowding is real enough that the entries and exits of that industry are themselves a flow to track.

**Moving averages, used three ways.** As a *trend filter* — price above or below a slow average (100/200-day) as a binary state — they are a blunt but honest regime classifier, and the blunter the better: the value is in the discipline of a consistent definition, not in the choice of 200 over 180. As a *crossover signal* — fast average crossing slow — they are a lagging trend-change detector whose whipsaw cost in ranges is the price of their reliability in trends; the register should grade any crossover-informed entries separately, because their expectancy is regime-dependent in exactly the way Chapter 2's classifier predicts. As a *level* — price interacting with a widely watched average — they belong to Chapter 6's reflexivity discussion, not to trend analysis at all. Keeping these three uses distinct prevents the most common moving-average error: reading a level touch as a trend signal.

**Momentum proper.** Rate-of-change over a lookback, and its cross-sectional cousin, relative strength — ranking assets against each other rather than against their own history. The cross-sectional version has the stronger empirical record (persistent enough to be a named factor with a century of data behind it) and is already half-built in this system: the four-rung size ladder, SPY/MDY, S&P 600 versus Russell 2000 are all relative-strength constructions with an economic reading attached. That is the standard to hold: **a relative-strength line earns its place when the pair means something** — profitable versus unprofitable, mega versus mid — and is decoration when it is just two tickers racing.

**Breadth.** Advance-decline lines, percentage of constituents above their own 200-day, new highs minus new lows. Breadth is the one member of this family that adds information beyond the index price, because it looks *through* the index to the census of its members — which is precisely why it lives in `internals` and why divergences (index up, breadth deteriorating) are the family's highest-value output. The 2021–22 top is the modern exemplar: breadth peaked months before the cap-weighted index because the index was riding an ever-narrower cohort. Note the connection rather than double-building: the Mag 7 earnings-versus-cap-share work, the size ladder, and percentage-above-200-day are one analytical family — concentration read three ways — and the correlated-confirmation guard should treat them as such.

**The institutional history, briefly, because it disciplines expectations.** Systematic trend-following is the one corner of technical analysis that institutionalized and survived measurement: managed-futures firms have run moving-average and breakout systems across futures markets since the 1970s, and the composite record shows a specific, instructive shape — long stretches of flat-to-negative performance in ranging markets punctuated by large gains in sustained macro trends (1970s inflation, 2008, 2014 oil, 2022 rates). The lesson is not "trend following works"; it is that trend following is a *payoff shape* — short many small losses, long a few large trends — that pays for crisis convexity with chop. Cross-sectional momentum has an even longer measured record as an equity factor, with its own known catastrophe mode: momentum crashes at regime turns, when the losers rally violently (2009 being the canonical case). Both records say the same thing this paper keeps saying — these measures monetize persistence and pay for it at reversals, and any use of them inherits that shape whether acknowledged or not.

**The honesty section for this family.** Trend measures are late by design: they confirm persistence after it has begun and surrender a piece of every reversal. That cost is acceptable when it is *priced in advance* — a trend-following entry expects to lose the first leg and the last leg and to be paid in the middle. It becomes a trap when trend confirmation is read as safety: the measure is most bullish at exactly the moment the move is most mature. The register's `origin` tagging should make this measurable within a few quarters: entries taken with trend confirmation versus against it, graded separately, will show what the confirmation is actually worth in this operator's hands. That is an empirical question the system can answer, and it should be answered rather than assumed in either direction.

---

## Chapter 4 — Mean Reversion and Oscillators: One Indicator in Many Costumes

The oscillator family — RSI, stochastics, Williams %R, CCI, the MACD histogram read as an oscillator — is where indicator proliferation is worst, so this chapter opens with its own conclusion: **these are one measurement.** Each takes recent price change, normalizes it to a bounded or semi-bounded scale, and calls the top of the scale "overbought" and the bottom "oversold." The normalizations differ; the input is identical; correlations among them run high enough that displaying two is displaying one twice. If a chart carries RSI and stochastics and a MACD histogram, it carries one fact and two echoes — the correlated-confirmation guard, applied to a screen.

So pick one and learn its behavior. RSI is the conventional choice and as good as any. What matters is not the choice but the two honest readings and the one dishonest reading.

**Honest reading one: stretched-in-range.** In a classified range regime (Chapter 2), an oscillator at its extreme says price sits at the edge of its recent distribution — a location statement, and in a range, edges tend to hold. This is the environment where fading extremes has its best expectancy, and even here the oscillator's role is *location*, with the range classification carrying the actual thesis.

**Honest reading two: divergence as a persistence check.** Price makes a new high; the oscillator makes a lower high. Mechanically this says the *rate* of advance is slowing — second-derivative information, genuinely earlier than the trend measures of Chapter 3, and the oscillator family's one forward-leaning contribution. It is also weak on its own: advances slow and then re-accelerate constantly. A divergence is a flag to check the other clusters (is breadth also thinning? is the wall above holding?), never a trigger. One echo of this pattern already earned its place in the system on harder data: the 2022 bottom turned on the second derivative of inflation while levels were still deteriorating. Second derivatives lead; they also false-signal freely. Both facts, always together.

**The dishonest reading: "overbought means sell."** In a trend, overbought is what strength looks like — an uptrend spends most of its life overbought, and the oscillator pinned high is *confirming* the regime, not contradicting it. Selling a trending market because RSI crossed 70 is the single most reliable way retail technical use loses money, and the protection is mechanical: no oscillator reading is actionable until Chapter 2 has classified the regime. Range: extremes are fadeable locations. Trend: extremes are the trend talking. The oscillator is the same number in both; the regime is the meaning.

### Worked illustrations — the same RSI, four meanings

| RSI print | Regime (from Ch. 2) | Reading | Action permission |
|---|---|---|---|
| 78 | Range (ADX 14) | Price at the edge of its recent distribution | Fade permitted, at a level from the Ch. 6 stack, stop beyond the zone |
| 78 | Trend up (ADX 32) | The trend talking; strength confirming itself | **No fade.** Pullback entries only; an uptrend lives overbought |
| 24 | Range (ADX 15) | Stretched at the low edge | Fade permitted at a defended level |
| 24 | Trend down (ADX 34) | Downtrend confirming | **No knife-catching**; wait for regime change, not for a low RSI |
| 62 after 81, price at new high | Either | **Divergence** — advance decelerating (second derivative) | Flag only: check other clusters; never a trigger alone |

The first and second rows are the chapter's entire argument in two lines: the
identical print, opposite permissions, and the regime — not the oscillator —
carries the meaning.

*[Figure 3 renders in the HTML edition.]*

*[Figure 4 renders in the HTML edition.]*

**Bands deserve one paragraph** because they make the location logic explicit: Bollinger Bands are a rolling mean and standard deviation, so "price at the lower band" says "two sigmas below the recent mean" — a z-score on a chart. The band-width compression reading belongs to Chapter 2; the band-touch reading is the stretched-in-range logic above; the "band walk" (price riding a band for weeks) is a trend regime announcing itself. Nothing in the bands is new relative to those three readings, which is the point of this chapter: the family is small once the costumes come off.

---

## Chapter 5 — Volume and Structure: The One Family With Its Own Information

Everything so far transforms price. Volume is the first input that is not price, and market structure — where volume occurred, how price traveled between levels — is the second. This family accordingly gets a different epistemic grade: it can, in principle, know something price alone does not, because it observes *participation*, not just outcome.

**Volume confirmation, and its limits.** The classical readings — advances on expanding volume are healthier than advances on shrinking volume; capitulation lows print on volume spikes — have a real mechanism (participation measures conviction and forced activity) and a real modern complication: index volume is now dominated by systematic, closing-auction, and passive flows whose size has nothing to do with conviction. Single-name volume retains more meaning than index volume. Read volume confirmations as mild evidence, and read volume *extremes* — multi-sigma spikes — as event markers worth a note in the Daily regardless of direction.

**Volume-at-price and the profile.** Where volume concentrated historically marks prices where positions actually changed hands — inventory levels, in the Dealer's Hand's sense. High-volume nodes act as congestion (positions defended, average costs clustered); low-volume gaps between them are prices where little business was done and through which price tends to travel fast. This is the most defensible piece of "structure" analysis because its mechanism is inventory rather than pattern: it says where the market has commitments. It also connects directly to the options-derived levels — a high-volume node that coincides with a gamma wall is one level attested by two independent instruments, and that coincidence *is* worth more, because the underlying mechanisms (cash inventory, dealer hedging) are genuinely different. This is the rare place where two technical-adjacent readings are not the same fact twice.

**The candlestick question, answered honestly.** The Daily Cascade renders candlesticks across three timeframes, and the reading discipline there is right: bars summarize the session's *path* — where price opened, how far it was rejected, where it settled — and path is modestly informative about who won the session. Long rejection wicks at a known level say the level was defended; that reading is a level-plus-flow statement, and it inherits its value from the level (Chapter 6), not from the candle's name. The named-pattern taxonomy — dozens of two- and three-bar formations with evocative names — does not survive testing as a signal class and should be read as vocabulary, not evidence. The system's use (candles as a compact display of path around levels that matter for other reasons) is the defensible use.

**Gaps and opening structure.** The overnight session and the opening auction are structural boundaries: gaps mark repricing that occurred without continuous trading, and the statistics around them (gaps fill often, but trend-day gaps do not) are regime-dependent enough that the honest summary is the one the reactive-trade design already encodes — the open is the noisiest, most reversal-prone stretch of the day, which is why the cooling-off rule exists. Opening range measures (where the first 30–60 minutes settled relative to overnight range) are legitimate Market Base context lines and are already on the deferred conditioner list. Nothing further needed.

---

## Chapter 6 — Levels and Reflexivity: Why They Work Until They Don't

A price level has no properties. It acquires them when behavior concentrates around it, and understanding *whose* behavior, and *why*, is the difference between using levels and being used by them.

**Four sources of real concentration, in descending order of mechanical force:**

**Dealer hedging levels** — gamma walls, the flip, max pain into expiry. The strongest class, because the flow is contractual rather than discretionary: dealers must hedge, and the Dealer's Hand derives exactly how much and which way. These are not "technical levels" at all, but they are the standard against which technical levels should be judged — a level backed by required flow versus a level backed by attention.

**Inventory levels** — the high-volume nodes of Chapter 5, plus round numbers where orders cluster and prior major highs and lows where trapped positions sit. The mechanism is average cost and the behavior of underwater holders: prior support becomes resistance because the buyers from that level, made whole, sell. This is the classical support-resistance logic, and its mechanism is real while its precision is not — these are zones, and treating them as lines is false precision.

**Attention levels** — the 200-day average, 52-week highs, index round numbers. Pure reflexivity: they matter because commentary and systematic rules reference them. Real, but the weakest class, because attention-based flow is discretionary and fickle — and because widely watched levels attract *predatory* flow. The stop-run through an obvious level, followed by reversal, is common enough to have a name in every trading tradition; its mechanism is that resting stops are liquidity, and liquidity gets taken. The practical consequence: an obvious level is more useful as a place where *other people's* risk sits than as a place to put yours. Invalidation set exactly at the obvious level is invalidation set where the sweep happens.

**Systematic trigger levels** — CTA trend thresholds, vol-control rebalancing bands, risk-parity leverage lines. Sell-side desks publish estimates of these, and they are the modern, larger version of the attention class: rule-driven rather than discretionary, which moves them toward the dealer class in force. Desk estimates of these levels are already part of the views ingest; they belong in the same Confirmation-block line as the gamma levels, labeled as estimates.

**Zone discipline, made operational.** Because levels are zones, the system renders each with a width — derived from the instrument, not invented: a gamma wall's width from the strike spacing and the OI distribution around it; a volume node's width from the profile's shoulder; an attention level's width from ATR (a 200-day "touch" within a quarter-ATR is a touch). Interactions are then classified against the zone, not the line: *defended* (entered and rejected with a closing print back outside), *accepted* (traded through and held beyond for N closes), or *swept* (pierced intraday, closed back inside — the stop-run signature, and a mild contrarian flag for Chapter 6's predatory-flow reasons). Three verbs, mechanically assignable, gradeable after the fact. This converts level-reading from chart narration into a log — the same conversion the pin log performs for max pain — and after two quarters the log answers the only question that matters about levels: which *mechanism class* is actually holding in this market, at what rate.

### Worked illustration — a morning level stack

Illustrative stack, index at 7,712, rendered the way the Confirmation block
should render it — by mechanism, with widths, ranked by force:

| Level | Zone (width) | Mechanism class | Source | Distance | Note |
|---|---|---|---|---|---|
| 7,750 | ±10 (strike spacing/OI) | Dealer hedging | Call wall, largest net OI | +0.5% | Strongest lid; hedging flow leans against approach |
| 7,700 | ±8 | Dealer hedging | Peak GEX / pin candidate | −0.2% | Pin log tolerance 25bps; log tonight either way |
| 7,685 | ±15 (profile shoulder) | Inventory | High-volume node, 3-week profile | −0.4% | Congestion; expect two-sided trade inside it |
| 7,640 | ±12 | Dealer hedging | Gamma flip (est.) | −0.9% | Below it, hedging amplifies; regime boundary, not support |
| 7,630 | ±20 (desk estimate) | Systematic | CTA trend trigger (sell-side est.) | −1.1% | Estimate, labeled as such; clusters with the flip — treat as one zone |
| 7,590 | ±19 (¼ ATR) | Attention | 50-day moving average | −1.6% | Weakest class; expect the sweep, not the hold |

Reading it: the two zones that matter today are 7,700 ± 8 (pin) and the
7,630–7,652 composite (flip + CTA trigger — two mechanisms, one zone, which is
real confluence). The 50-day at 7,590 is where *other people's* stops are; an
invalidation for a long entered at the node belongs below 7,571 (the zone edge
minus buffer), not at 7,590.

*[Figure 5 renders in the HTML edition.]*

**The synthesis, and it is the same synthesis as everywhere else in the system:** a level's reliability is proportional to the mechanical force behind it, and confluence across *mechanisms* — a gamma wall, atop a volume node, near a systematic trigger estimate — is the only confluence that counts. Three attention levels stacked together are one crowd, thrice.

---

## Chapter 7 — The Traps

Every trap in this chapter is a general methodological failure the system already guards against in other domains. Technicals deserve their own recital because the field industrializes all four at once.

**Trap one: redundancy dressed as confirmation.** The dependency-map finding from the Daily Cascade paper, at indicator scale: RSI agreeing with stochastics agreeing with MACD is one input agreeing with itself. Count *clusters*, and in this domain the clusters are: regime measures (Ch. 2), trend/breadth (Ch. 3), oscillators — all one cluster (Ch. 4), volume/structure (Ch. 5), levels by mechanism (Ch. 6). Five clusters. A screen showing twelve indicators shows five facts at most, and usually three.

A worked count, to make the trap concrete. A screen shows: RSI 76, stochastics
88, MACD histogram positive, price above 20/50/200-day averages, ADX 31, up
volume 78% of total, new 20-day high, +2.1% above upper band. Eight bullish
"confirmations." Clustered: RSI + stochastics + MACD + band position = *one*
oscillator/extension fact; the three MA states + new high + ADX = *one* trend
fact; the volume line = one participation fact. Three facts, one of which
(extension) is mildly *cautionary* in a trend, not bullish. The screen said
eight-for-eight; the clusters said two-and-a-half.

**Trap two: every parameter is a fitted parameter.** The 200-day average, RSI-14, 70/30 thresholds, 20-2 Bollinger settings — all are conventions that survived by convention, and every threshold inherits the fragility audit's finding: shift the lookback and the signal history changes. The protection is the same as everywhere else in the system — percentiles and bands with hysteresis rather than lines; convention-standard parameters rather than optimized ones (optimizing technical parameters on your own history is the purest overfitting available, because the search space is infinite and the data is one path); and `kill_condition` stated before use.

**Trap three: hindsight pattern clarity.** Every historical chart shows clean setups because the eye finds them after the outcome selects them. The patterns that failed are invisible — they never became "patterns." This is survivorship bias operating at the perceptual level, faster than any audit can catch, and it is why the paper's standing rule is that *no pattern-class claim enters the system without a stated base rate* — and since almost no candlestick or chart-pattern claim survives base-rate measurement, almost none enter. The pin log is the template for the alternative: convert one pattern claim (options pinning) into a measured base rate before trusting it. Any technical claim worth using is worth the same treatment.

**Trap four: the timeframe shell game.** A signal that fails on the daily chart "works" on the 4-hour; a stopped trade was "actually right" on the weekly. Unfalsifiable in aggregate, because some timeframe always retro-fits. The system's defense is structural: each report owns one horizon, each technical reading is tagged to the block and horizon it serves, and a reading is graded on the horizon it was issued for. A swing-horizon level claim is right or wrong at the swing horizon, full stop.

**And the meta-trap that contains the others: technicals are cheap to generate and emotionally satisfying to read**, which makes them fill whatever space they are allowed. A chart with twelve indicators feels rigorous the way the twenty-metric dashboard feels rigorous — density masquerading as insight. The one-question test from the registry applies to every technical line the system renders: what question does this answer that nothing else on the screen already answers? Most fail. The ones that pass are in this paper.

---

## Chapter 8 — Placement in the System

This chapter is the reason the paper exists. Everything above says what the measures are; this says exactly where they live, which is a shorter list than the field would like.

**The regime layer (Chapter 2) feeds the Daily's Market Base and Confirmation blocks and the Weekend Synthesis backdrop.** Realized-vol percentile, ATR compression, ADX band — three lines, rendered as context, refreshed daily. They condition tactics ("range regime: fade-the-edge tactics favored, breakout entries penalized") and they gate the oscillator readings per Chapter 4. `trigger_eligible: false`.

**The levels layer (Chapters 5–6) feeds the Confirmation block and the execution plan.** One consolidated level stack per session — gamma-derived levels first, volume nodes second, systematic-trigger estimates third, attention levels last and labeled — with confluence counted across mechanisms only. Entries and invalidations in the execution block reference this stack; invalidations avoid the obvious line by a stated buffer, for Chapter 6's reasons.

**The timing layer (Chapters 3–4) feeds execution only.** Once a thesis exists — swing thesis from the Weekend, reactive trigger from the Daily — trend state and oscillator location refine entry and define price-terms invalidation. They never generate the thesis. The register's `origin` field already separates planned from reactive; a `technical_context` note on entries (with-trend / counter-trend / at-level) makes the Chapter 3 empirical question answerable at the annual review.

**Breadth and relative strength (Chapter 3) live in `internals`**, where they already do, with the correlated-confirmation guard treating the concentration measures as one family.

**Nothing from this paper enters the Monthly composite, any pillar score, or any trigger.** The Momentum pillar remains macro-momentum. The tail watch remains data-and-mechanism tripwires. The composite remains price-blind below the regime level. This is the wall, and it is worth stating as bluntly as the paper's opening: price-derived measures describe the tape; the system's views come from elsewhere, and the tape is where those views get executed.

**The grading commitment that keeps all of it honest:** every technical reading the system renders is either a conditioner (regime lines, level stacks — graded on whether the classification was stable and the levels held, in the quarterly review) or an execution refinement (graded through the register's expectancy split). Nothing floats free of grading, because a measure that is never graded accumulates authority it never earned — which is, in one sentence, the history of technical analysis.

---

## Appendix — The Reference Table

One row per measure the system permits, with its cluster, its legitimate use, and its trap. Anything not on this table renders nowhere.

| Measure | Cluster | Construction | Legitimate use | The trap it invites |
|---|---|---|---|---|
| Realized vol (20d/60d), percentile | Regime | Std. dev. of log returns, ranked vs. own history | Regime classification; divergence between windows | Reading the level without the percentile |
| ATR + compression percentile | Regime | Average true range vs. own two-year range | Gap-inclusive vol; coiling detection; stop-width scaling | Trading the breakout direction of a coil in advance |
| ADX (banded, with hysteresis) | Regime | Smoothed directional-movement ratio | Trend-vs-range classification gating all oscillator reads | Treating 20/25 as lines rather than bands |
| Slow MA state (100/200d) | Trend | Price above/below smoothed price | Blunt trend filter; consistent regime definition | Reading a level touch as a trend signal |
| MA crossover | Trend | Fast smoothed price minus slow | Lagging trend-change confirmation, graded separately in register | Whipsaw cost in ranges, unpriced |
| Cross-sectional relative strength | Trend | Ratio of two series with an economic pairing | Size ladder, quality spreads — pairs that mean something | Ticker races with no economic reading |
| Breadth (% above 200d, A/D, NH-NL) | Trend | Census of constituents vs. own trend | Sees through the index; divergence at concentration extremes | Double-counting with the other concentration measures |
| One oscillator (RSI, by convention) | Oscillator | Normalized recent gains vs. losses | Stretched-in-range location; divergence as persistence check | "Overbought = sell" in a trend; displaying three costumes of it |
| Bands (rolling mean ± 2σ) | Oscillator/Regime | Z-score of price, drawn on the chart | Width → compression (regime); touch → location (range only) | Band touch traded without the regime gate |
| Volume extremes and confirmation | Volume/structure | Participation vs. own history | Event marking; capitulation/conviction context, single-name > index | Reading passive-era index volume as conviction |
| Volume-at-price nodes | Volume/structure | Where business was actually done | Inventory levels; confluence partner for gamma walls | False precision — nodes are zones |
| Candlestick path display | Volume/structure | Session OHLC as a bar | Compact display of path around levels that matter for other reasons | The named-pattern taxonomy as evidence |
| Level stack (by mechanism class) | Levels | Gamma > inventory > systematic > attention | Entry/invalidation geography; cross-mechanism confluence | Stacked attention levels counted as three; stops on the obvious line |
| Opening range / gap context | Structure | First 30–60m vs. overnight range | Market Base context; reactive-trade conditioning | Trading the open before the cooling-off window |

Fourteen rows. Five clusters. That is the entire permitted surface, and the annual registry prune applies to it like everything else: any row that has not changed a classification or refined an execution in a year is cut.

---

*Version 1.1 — September 2026. Companion XIV. The shortest paper in the library, for the reasons Chapter 1 states. Cross-references: the Dealer's Hand (IX) for hedging-derived levels; the Daily Cascade paper (V) for the block structure and candlestick display discipline; the Monthly manual (III) for the macro-momentum pillar this paper deliberately does not touch.*
