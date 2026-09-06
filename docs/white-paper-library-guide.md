# The White Paper Library — A Reader's Guide

*Nineteen companion documents as of 6 September 2026 — sixteen full papers, one doctrine, and two Draft-1 editions written the week the execution layer was built, roughly 307,000 words.
The reports say what is happening; the papers explain the machinery, so each
refresh can be read quickly without re-deriving the framework. Every report has
at least one companion, and the tail watch has its own. Per the Final
Architecture Change Order, the library stays OUT of normal runtime context —
the system consumes it through a compact claims registry (claims, falsifiers,
evidence links); the papers themselves are for the human and for writing that
registry.*

**Five documents exist in two formats, and the two formats have different jobs.**
This guide, *The Dealer's Hand* (XIII), *Options as Expression* (XXII),
*Evidence and Inference* (XXIII) and *Earnings* (XXIV) are each published as
HTML alongside their Markdown source. **The HTML is canonical for reading** — it
carries the rendered tables, the anchor navigation and the computed figures the
Markdown can only hold as placeholders; XXIII's masthead says outright that its
figures live only there. **The Markdown is canonical for editing** — every
change is made in the `.md` and the HTML is regenerated from it, never the other
way round. An edit made only in the HTML is lost at the next regeneration, and
an HTML file that disagrees with its `.md` is stale by definition rather than a
second opinion. Every other paper in the library is Markdown only, and the
question does not arise.

*(This note has now been written three times and deleted twice — added on
6 September, removed the same afternoon by a full-file re-upload from a local
copy that predated it, restored in `8bf2f89`, removed again hours later by
`a3839ff` the same way. That is the editing hazard the rule describes, deleting
the rule. **The durable copy lives in `CLAUDE.md`, which no upload flow
touches**; if this paragraph is missing from the guide, it was dropped by a
stale re-upload rather than retired, and should be restored from there. Edit the
`.md` in the repo, or re-upload from a copy that has pulled.)*

---

## Contents

**Front matter**
1. [The library at a glance](#the-library-at-a-glance) — the full roster in one table
2. [Cross-references and interdependencies](#cross-references-and-interdependencies) — what depends on what
3. [From the library to the trade](#from-the-library-to-the-trade) — how a paper becomes a decision

**The papers, in reading order**

| # | Paper | Layer |
|---|---|---|
| I | Foundations and Field Guide to the Five-Force Framework | Macro & disruptive |
| II | The Twenty-Five — Tail Scenarios | Macro & disruptive |
| III | The Monthly Macro Report: A Working Manual | Macro & disruptive |
| IV | The Rate and Liquidity Machine | Macro & disruptive |
| V | Currencies: A Structural Framework | Macro & disruptive |
| VI | Credit: A Structural Framework | Structural asset classes |
| VII | Energy: A Structural Framework | Structural asset classes |
| VIII | Metals: A Structural Framework | Structural asset classes |
| IX | Digital Assets: A Structural Framework | Structural asset classes |
| X | Tops and Bottoms: Every Major U.S. Turning Point Since 1970 | Market timing |
| XX | Base Rates: What Markets Usually Do | Market timing |
| XI | Volatility: A Structural Framework | Micro & execution |
| XII | The Daily Cascade Paper | Micro & execution |
| XIII | The Dealer's Hand | Micro & execution |
| XIV | Technical Indicators | Micro & execution |
| XXII | Options as Expression | Micro & execution |
| XV | Equities: A Structural Framework | Market structure |
| XXI | International Equities | Market structure |
| XXIV | Earnings: The Reaction Is the Object | Market structure |
| XVI | Positioning & Flows | Positioning & the book |
| XVII | Portfolio Construction Across Regimes | Positioning & the book |
| XVIII | The Operating Doctrine | Positioning & the book |
| XIX | Building and Validating a Systematic Book | Positioning & the book |
| XXIII | Evidence and Inference | Positioning & the book |

**Back matter**
- [In draft and planned](#in-draft-and-planned)
- [Appendix — Executive summary: the current read](#appendix--executive-summary-the-current-read-september-2026) *(perishable; rewritten quarterly)*

---

## The library at a glance

| Layer | # | Paper | Companion to | Size | One-line description |
|---|---|---|---|---|---|
| Macro & disruptive | **I** | Foundations and Field Guide to the Five-Force Framework | Disruptive Themes | ~21,700 words | The intellectual apparatus behind the five factors — lineage, decoder ring, seven-element factor chapters, decade-horizon geopolitics |
|  | **II** | The Twenty-Five — Tail Scenarios: Mechanism, Mutation, and Instrumentation | Tail watch (all reports) | ~21,300 words | The 25 scenarios by mechanism family, with mutations, routing matrix, and the price-insensitive-buyer thesis |
|  | **III** | The Monthly Macro Report: A Working Manual | Monthly Macro | ~29,000 words | Ten-lens treatment per pillar, named failure modes, lead-lag synthesis, conflict-resolution rules |
|  | **IV** | The Rate and Liquidity Machine | Monthly Macro (liquidity, sovereign) | ~16,450 words | Eleven regime eras 1907–Warsh, ~fifty policy and plumbing instruments across six families, the 1942–51 yield peg as the live analogue |
|  | **V** | Currencies: A Structural Framework | Foundational to every dollar-priced asset | ~14,800 words | How exchange rates move and who moves them, the dollar question, digital assets as currency, hedging and trading FX risk |
| Structural asset classes | **VI** | Credit: A Structural Framework | Top & Bottom, Monthly (credit pillar), Disruptive Themes | ~15,400 words | A lending-standards cycle, not a spread cycle — private credit and bifurcation, credit as a timing tool, the seven concealment mechanisms, plus the library's trading-the-curve section |
|  | **VII** | Energy: A Structural Framework | Alternative Asset (oil, gas), Monthly (inflation, geopolitics) | ~12,900 words | A buffer market, not a resource market — and electricity as the scarce commodity; oil, gas, power, uranium, the Hormuz test |
|  | **VIII** | Metals: A Structural Framework | Alternative Asset | ~17,100 words | Gold, silver, copper as three distinct assets — stock-vs-flow frame, signal hierarchies, false signals, position construction |
|  | **IX** | Digital Assets: A Structural Framework | Alternative Asset | ~19,150 words | Long-horizon crypto self-sufficiency — taxonomy, value accrual, honest bull and bear, forecast track records |
| Market timing | **X** | Tops and Bottoms: Every Major U.S. Turning Point Since 1970 | Top & Bottom | ~16,000 words (est.) · 3 formats | Eight bears and the near-misses on one template, forward returns standardized, calibration against 13 episodes |
|  | **XX** | Base Rates: What Markets Usually Do | Every thesis, before it is written; Top & Bottom (extended episode set); the tail watch | Draft 1 · ~7,500 words | The denominators — return and drawdown distributions, streaks and mean reversion, correlation by regime, earnings and options base rates, costs; seasonality with its decay evidence and the midterm-cycle conditional; percentiles (p25/median/p75) throughout rather than means; the pre-1970 downturn extension (1907, 1929–32, 1937–38, 1946–47, 1961–62) that doubles the Tops & Bottoms calibration sample; **and Part IV — how bad it can get outside the U.S. record: Japan's 34 years, Weimar, Greece, Argentina, the markets that went to zero, the long-term debt cycle's two resolutions, and what protected capital in each** |
| Micro & execution | **XI** | Volatility: A Structural Framework | Execution layer, Daily Cascade, expressibility | ~15,000 words | The price of insurance — VRP, crowding and unwinds as one fact; regime identification and cross-asset vol; the options-ETF complex at scale |
|  | **XII** | The Daily Cascade Paper | Daily Cascade | ~15,000 words (est.) | Operating manual for the intraday suite — five blocks, dealer-gamma reading rules, the dependency map |
|  | **XIII** | The Dealer's Hand | Daily Cascade (dealer positioning) | not yet measured · illustrated edition **v1.1** (HTML canonical; md carries figure placeholders) | Derives the dealer-hedging mechanics from first principles — sign conventions, who is on which side, the JHEQX exception — with 21 computed figures and 2 worked ledgers; **Part V adds the multi-horizon book (GEX/DEX by bucket, 0DTE session taxonomy)**; elaborates Daily Cascade Ch. 2 |
|  | **XXIV** | Earnings: The Reaction Is the Object | The event-reaction setup; the cohort monitor's revision flags; the single-name books' valuation vocabulary | Draft 1 · ~4,300 words, 9 computed figures · HTML canonical | The print is not the event — the managed consensus, the whisper, the revision cycle and its second-derivative flag; the implied move against a name's own history, the event premium, positioning into the print; the four quadrants (guidance beats the print), gap–fade–drift, reaction-versus-expectation as the tradeable object; **the denominator problem — five P/Es on one stock**, when book value means anything, EV multiples, cash versus earnings, **the sector multiple map and the cycle inversion (cyclicals cheapest on trailing at the peak)**; sector grammar with insurance as the worked example |
|  | **XXII** | Options as Expression | Book C's every trade; Book A's convexity sleeve; the expression check | Draft 1 · ~6,200 words, 10 computed figures · HTML canonical | Choosing the instrument after choosing the view — the four primitives as shapes, your greeks versus the dealer's, verticals and the four numbers, time spreads, the three costs (decay, the volatility crush, the spread tax); and the engineered payoffs: buffered funds, **synthetic principal protection from a cash-equivalent fund plus long-dated calls**, and **dual-directional structures built as bills-plus-iron-butterfly rather than as barrier notes** — with the tenor arithmetic showing why option cost grows as √T while funding grows as T |
|  | **XIV** | Technical Indicators | Daily Cascade + execution layer | ~6,350 words, 5 figures | Price-derived measures — the lag argument, the five permitted clusters, levels by mechanism, the traps, and the wall keeping technicals out of the composite |
| Market structure | **XV** | Equities: A Structural Framework | Top & Bottom, Daily Cascade, Disruptive Themes (Factor II) | ~8,350 words | The residual claim, the index as a momentum machine, factors, the concentration and its fulcrum, the AI rings and the new listings, scenario families, what to watch by cadence |
|  | **XXI** | International Equities: Europe, Japan, China, and the Rest of the World | Book A's allocation sleeve; Book B candidates; the Daily Cascade's overnight read; Disruptive Themes (AI supply chain); the tail watch (Taiwan) | Draft 1.1 · ~9,300 words | The global map and home-bias arithmetic; **the 55-year record of alternating leadership (five flips, ~decade runs, the current U.S. run the longest and widest)**; the decomposition of fifteen years of U.S. outperformance (a third currency, a third multiple, a third earnings) and which parts can repeat; the currency term and the hedged/unhedged decision as a recorded choice; Europe, UK, Japan, China, Taiwan/Korea, India and EM one at a time; instruments and their traps — stale NAV as live price discovery, withholding tax by account type, the session clock behind the overnight gap; **correlation's long rise, its regime dependence and downside asymmetry, and why daily correlation is a clock artifact**; **a full part on China — three markets, the dilution/state-allocation explanation of the lost decade, the technology record sector by sector, the winning-the-industry-without-earning-a-return trap, and four ten-year scenarios**; **and a ten-year probabilistic view of relative returns built from decomposed components, with falsification conditions per scenario** |
| Positioning & the book | **XVI** | Positioning & Flows | Every report's positioning line; the tail watch; the heat factor map | Draft 1.1 · ~10,300 words | Who is forced to move, when, and whether the market is absorbing them — **the participant map (ownership share vs. volume share, forced vs. discretionary, mid-2026 figures)**, ten mechanical-holder types plus the discretionary holders' mechanical failure modes (degrossing, redemptions, liability-driven rate shocks, currency-hedge rebalancing, market-maker withdrawal), the master calendar, absorption as response-per-unit-stimulus, six flow models with stated uncertainty, the seven-group independence table |
| | **XVII** | Portfolio Construction Across Regimes | All reports → positioning | Draft 1 · ~4,400 words | Preview edition — frame, vocabulary, sizing disciplines, open questions — with a four-condition trigger for the empirical Draft 2 (register data + IBKR Gate 1) |
| | **XVIII** | The Operating Doctrine | How every report is consumed; how capital is deployed | **v1.0 · Doctrine** · ~25,600 words | The four books, the three regime dials, the kill-switch ladder, the volatile-day protocol, twenty-nine rules each traced to its Wizard origin and its enforcement point, the honest arithmetic of the return target, and the adoption sequence. Changes only at the monthly session |
| | **XXIII** | Evidence and Inference: How to Read Your Own Ledger | How every register figure is read; the promotion gates; the trust matrix's sample-size rules | Draft 1 · ~4,100 words, 5 computed figures · HTML canonical | The error bar on everything — a year cannot exclude zero, two years give the sign, five give the size; effective sample size; **regime as a sample size** (the doctrine's most important cut is permanently the thinnest); forking paths, overfitting, survivorship, outcome bias; Bayes in sentences and mechanism as evidence; **the shadow outcome as a 3.5× sample multiplier**; the decidability table of every register cut at three horizons; Kelly under edge uncertainty; edge decay detected in the mechanism, not the P&L |
| | **XIX** | Building and Validating a Systematic Book | Trading infrastructure; the register; IBKR gates | Draft 1 · ~9,100 words · as-built | The register and its immutable packets, DECISION_BLOCKED, the three senses of read-only (and which was false), execution mechanics, sizing and cost as code, the five named failure classes, tax as an expression decision, the compliance boundary, the gate ladder and the honest not-yet-built list |

*Numerals are the canonical series IDs, assigned here in reading order from the top down — the macro and disruptive layer first, then the structural asset classes, then market timing, then the micro and execution layer. Where a paper's masthead carries a different number, the masthead is relabelled to match this guide when it is committed to `docs/`. Word counts marked (est.) are estimated from page counts; the others are measured. Detailed summaries follow, one page per paper. File this guide in the repo's
`docs/` index so future sessions know the library exists.*

---

## Cross-references and interdependencies

**A numbering hazard, and the fix.** The papers cross-reference each other by
series numeral inside their text — Energy cites "paper VII" for Metals and
"XIII" for Volatility; Credit cites "Top & Bottom (V)" and "Rates & Liquidity
(X)"; the Dealer's Hand cites "Companion IX" — and those numerals were assigned
chat by chat before this guide existed. The reorder makes every one of them
wrong. **Rule going forward: inside a paper, cross-reference by name, never by
numeral.** Numerals live only in this guide. When the papers are committed to
`docs/`, a find-and-replace on "paper VII" → "the Metals paper" and its
siblings takes minutes and removes the hazard permanently.

**The dependency graph.** Each paper owns one thing, references others rather
than re-deriving them, and feeds specific consumers. Read down the rows to see
what a paper needs; read across to see what breaks if it is wrong.

| Paper | Owns | Draws on | Feeds |
|---|---|---|---|
| I Foundations | The five forces, the composite, the yield channel as common bus | II (tails), IV (rates), V (dollar), VI (AI financing → credit) | Every report's regime frame; X's overlays |
| II The Twenty-Five | Tail mechanisms, mutations, the price-insensitive buyer class | I, IV, VI, VII, IX, XI (one scenario family each) | Tail watch in every report; XII's Backdrop block |
| III Monthly manual | Pillar semantics, failure modes, lead-lag order | IV (liquidity/sovereign), VI (credit pillar), VII (inflation transmission) | X (pillar inputs to the composite); XII's Direction block |
| IV Rates & Liquidity | Price of money, the Treasury–Fed plumbing, the funding channel | I (Factor IV), III | VI (funding channel), V (rate differentials), XI (vol of rates), II (scenarios 1, 9, 10, 11) |
| V Currencies | How exchange rates move, the dollar question, FX hedging | IV (differentials), IX (digital dollar), VIII (gold as reserve) | Every dollar-priced asset paper; II (scenarios 2, 15); the Thai baht exposure |
| VI Credit | Price of risk, lending-standards cycle, private-credit concealment | IV (funding), V (dollar funding), III | X (overlay: HY acceleration), I (Factor I financing), II (scenarios 6, 14, 24, 25) |
| VII Energy | The buffer, power as the scarce commodity, chokepoints | VIII (copper), V (petrodollar), XI (OVX regime) | I (Factor III), III (inflation pillar), II (scenario 7), IX (miner-to-AI-hosting bridge) |
| VIII Metals | Stock vs. flow, the official gold bid, silver's byproduct trap | V (dollar), IV (real rates), VII (energy cost curve) | I (Factor V, debasement share), II (scenario 21), positioning |
| IX Digital Assets | Taxonomy, value accrual, the stablecoin–Treasury link | V (currency), IV (bill demand), XI (crypto vol) | I (Factor V), II (scenarios 4, 18, 23), III (real-assets pillar) |
| X Tops and Bottoms | Historical turning points, the 13-episode calibration, forward-return distributions | III (pillars), VI (credit overlay), I (concentration) | The composite's top-side language; XVII (sizing by regime) |
| XI Volatility | The price of insurance, VRP as one fact, vol regimes, expressibility | XIII (dealer mechanics, not re-derived), IV, VII (OVX) | XII (regime lines), XIV (regime gate), every paper's "how to express it" |
| XII Daily Cascade | The five blocks, reading rules, the dependency map | XIII (derives what XII applies), XI, XIV | The intraday reports; XIX (execution rules); XVIII (Book C) |
| XIII Dealer's Hand | Hedging mechanics from first principles, sign conventions, the JHEQX exception | — (foundational; corrected XII) | XII, XI, XIV (levels by mechanism) |
| XIV Technical Indicators | Price-derived regime and levels, the traps, the wall | XIII (hedging levels), XII (blocks), XI (vol regime) | Execution only; nothing upstream |
| XV Equities | Earnings cycle, buybacks, index and passive mechanics, factors, single names | I (Factor II), VI (financing), X (turning points), XVI (flows) | X's overlays; XII; II (scenarios 20, 22, 24) |
| XVI Positioning & Flows *(Draft 1)* | The mechanical holders, their calendars, absorption | II (price-insensitive buyers), XIII (dealer flow), XI (vol-control), XIV (trigger levels) | XII's Confirmation block; XVIII's trust matrix rows and Rule 16 factor map; XIX's heat calculator; XV |
| XVII Portfolio Construction *(Draft 1)* | Cross-asset sizing, hedge cost, rebalancing disciplines | X, XI, IV, V, VI, VIII, IX, XV | XVIII's Book A bands; the book |
| XVIII Operating Doctrine *(v1.0)* | Books, dials, switches, rules, target arithmetic, adoption | Every paper (consumes the whole library); XIII (gamma dial), XI (vol dial), III (macro dial), X (override) | XIX (what enforces it); the operator |
| XIX Systematic Book *(Draft 1, as-built)* | Register, execution, sizing-as-code, validation, tax, compliance, the gate ladder | XVIII (the rules it enforces), XII, XIII, XIV, XVI, X (calibration lessons) | The execution layer; Gate 2 |

**Where a wrong paper does the most damage.** Three papers are load-bearing for
everything beneath them: **Rates & Liquidity** (if the funding-channel read is
wrong, Credit, Currencies and the fiscal-dominance thesis are wrong together),
**the Dealer's Hand** (if the sign convention is wrong, every level in the
execution layer is wrong — which is exactly what it caught), and **Foundations'
yield-channel claim** (if the five forces do not compound through the long
yield, the composite is aggregating things that diversify). Those three deserve
the annual re-read first.

---

## From the library to the trade

The library exists to make tactical decisions better than they would be without
it. This section states how, because "read all fourteen papers before trading"
is not a process. The chain has four steps, and each step draws on a different
layer.

**Step 1 — What regime am I in?** *(macro & disruptive layer)*
The composite band from Foundations, the pillar configuration and lead-lag
position from the Monthly manual, the funding state from Rates & Liquidity, and
the dollar regime from Currencies. This step produces one sentence — "late-cycle
concentration, fiscal dominance emerging, dollar soft, liquidity loose on a spent
buffer" — and it changes slowly. It is never itself a trade. It sets which
direction is *permitted* to be a thesis and which is fighting the tape.

**Step 2 — What does the structural view on this asset say?** *(asset layer)*
For whatever is being traded: Credit's dispersion read, Energy's buffer state,
Metals' official-versus-paper bid, Digital Assets' architecture-versus-asset
question. Each paper produces a standing view with named kill conditions. A
tactical trade that runs against the structural view is not forbidden, but it is
tagged `counter-structural` in the register and sized smaller, and it must state
what it knows that the structural view does not.

**Step 3 — Where is the market in its turning distribution?** *(market timing)*
Tops and Bottoms converts the regime into a distribution: at OVEREXTENDED, the
odds of a drawdown over the horizon are higher and the payoff of holding hedges
continuously rather than timing them is better. This is where sizing gets its
prior. It never gives an entry.

**Step 4 — Where, when, how, and at what cost?** *(micro & execution layer)*
Volatility answers *how* — which structure expresses the view and whether the
insurance is cheap or dear right now. The Dealer's Hand and the Daily Cascade
answer *where* — the level stack by mechanism, the flip, the walls. Technical
Indicators answers *when* within that — regime-gated timing, invalidation off
the obvious line. Only here does a trade exist, and every element of it traces
to a paper.

**Seven principles that recur across the papers and should govern the trade.**
These emerged independently in separate documents, which is the best evidence
they are real:

1. **The long yield is the common bus.** Foundations found it across the five
   forces; The Twenty-Five found it across six tail clusters; Rates & Liquidity
   derived why. *Tactical consequence:* any position is implicitly a position
   on the long end, and the book should know its aggregate duration exposure
   even when it holds no bonds.
2. **The buffer sets the price, not the stock.** Metals' stock-versus-flow;
   Energy's spare-capacity thesis; Rates' reserve-scarcity mechanics — the same
   idea in three markets. *Tactical consequence:* the series to watch is the
   one measuring slack, and slack disappearing is the signal, not price moving.
3. **Dispersion is the signal, not the level.** Credit's manager-mark
   dispersion; the CCC–BB gap with IG flat; Volatility's implied-correlation
   read; Technical Indicators' breadth-versus-index. *Tactical consequence:*
   when the aggregate is calm and the cross-section is not, trust the
   cross-section and reduce.
4. **Regime, not level.** Volatility's operational core; Technical Indicators'
   oscillator gate; the Monthly's five configurations; Tops and Bottoms'
   distribution framing. *Tactical consequence:* no reading is actionable
   until the regime it sits in is classified, and the same number means
   opposite things in different regimes.
5. **Mechanical bids fail differently.** The Twenty-Five's price-insensitive
   buyer class; Volatility's options-ETF complex; Digital Assets' stablecoin
   bill demand; Metals' official gold bid. *Tactical consequence:* know which
   flows in a position are mechanical, because their withdrawal will not
   reverse when the asset looks cheap.
6. **Count mechanisms, not instruments.** The Daily Cascade's dependency map;
   Technical Indicators' five clusters; the correlated-confirmation guard
   everywhere. *Tactical consequence:* confluence is only real across
   independent mechanisms — a gamma wall on a volume node near a systematic
   trigger, not three attention levels.
7. **Expressibility decides.** The Monthly's expressibility lens; Volatility's
   entire second half; Metals' copper instrument problem; Currencies' hedging
   chapter. *Tactical consequence:* a view is only worth what its cheapest
   clean expression costs, and the cost is measured before the trade, not after.

**A worked pass, to make the chain concrete.** Suppose the Weekend Synthesis
proposes fading strength in the index toward the call wall. Step 1: regime says
OVEREXTENDED, liquidity loose on a spent buffer — a fade is *permitted* but
fighting a still-permissive tape, so it is a small-size thesis. Step 2: no
single-asset paper governs the index, but Credit's dispersion read (CCC wide, IG
flat) and Technical Indicators' breadth line both say the cross-section is
weaker than the aggregate — structural support for the fade. Step 3: Tops and
Bottoms says the drawdown odds are elevated but tops are structurally hard to
time — hold the position as a continuous hedge, not a timed bet. Step 4:
Volatility says skew is steep, so buying puts is dear — express through a call
spread sold into the wall instead; the Dealer's Hand puts the wall at a specific
strike with a width from the OI distribution; Technical Indicators gates the
entry on a range-regime classification and places invalidation a buffer beyond
the wall, not on it. The trade enters the register with `technical_context:
at-level`, `structural: aligned`, `expression: call spread, skew-driven`, and a
kill condition. Every element came from a paper. None of the papers made the
decision.

**What this section does not claim.** The chain is a reading order, not an
algorithm; the papers inform judgment rather than replace it; and the register
is what tests, over time, whether the informed judgment is any better than the
uninformed kind. That test is the one thing the library cannot do for itself.

---

## I. Foundations and Field Guide to the Five-Force Framework
**Companion to: Disruptive Themes · ~21,700 words**

**What it contains.** The complete intellectual apparatus behind the quarterly
structural report. It opens with the framework's lineage — Minsky and
Kindleberger on credit cycles, Dalio on the debt machine, Soros on reflexivity,
Mandelbrot and Taleb on fat tails, Tetlock on forecasting discipline — and a
"decoder ring" for the report's conventions (composite bands, factor scoring,
premise expiry). The core is five factor chapters, each with a seven-element
treatment: a 101 explainer, historical context, a newspaper-style dispatch
anchored to late August 2026, two-to-three-year probability-weighted paths,
ten-year scenario families, an instrument panel, and factor couplings. The
geopolitics chapter was substantially expanded beyond the current Hormuz
situation into a full decade-horizon assessment: a Taiwan escalation ladder in
which the quarantine rung is identified as most likely and least modeled, a
nine-theater table with decade probabilities, and the mechanisms by which
theaters correlate. Closing chapters cover the composite's construction and
limitations, the discipline sections (steelman, what-would-change-my-mind,
calibration check, media scan), and a synthesis chapter on compound pathways.

**Timeless takeaways:**
- **The yield channel is the common bus.** All five factors — AI, valuation,
  geopolitics, debt/dollar, monetary architecture — transmit into portfolios
  primarily through the long yield, which is why the factors compound rather
  than diversify.
- **Top-side signals shift distributions; they never time.** The composite's
  OVEREXTENDED reading is a statement about forward return odds, not a turn
  call, and the framework's language is deliberately built to prevent the
  stronger claim.
- **Taiwan's most probable escalation path is the one nobody models:** a
  quarantine rather than a blockade or invasion — legally ambiguous, hard to
  respond to proportionally, and made more likely by the precedent of
  chokepoint disruption being absorbed without price response.
- **Every factor carries a falsification condition and an expiry on its
  premise.** A score whose premise event has collapsed reverts rather than
  carrying forward — the paper documents the Factor III failure that taught
  this rule.

---

## II. The Twenty-Five — Tail Scenarios: Mechanism, Mutation, and Instrumentation
**Companion to: the tail watch across all reports · ~21,300 words**

**What it contains.** The full treatment of the 25 tail scenarios, organized by
seven *mechanism families* rather than by monitoring cadence — the reorganization
is itself analytical, grouping scenarios by how they break rather than how often
they are checked. Each scenario receives seven elements, including a novel
**Mutations** section with four bounded sub-parts: scope drift, substitution,
aliasing, and the re-specification trigger — the ways a scenario changes shape
while its label stays constant. Four front-matter chapters establish the
epistemics: why the listed tail is not the black swan, the n≈0 problem and its
three prohibitions, the price-insensitive buyer class as the paper's central
analytical claim, and cadence-follows-speed as a design principle. Part 2 is
operational: a 25-row routing matrix (scenario → tier → instrument → carrying
report → what a firing changes), a clustering map, a coverage audit, a ranked
build queue, and a re-specification log opened with three entries. Scenario 13
(cyberattack on settlement) receives an extended defense of why it deliberately
carries no tripwire.

**Timeless takeaways:**
- **The price-insensitive buyer class is the central claim:** the most dangerous
  tails are not shocks to the world but failures of mechanical bids — sovereign
  funds, passive flows, stablecoin issuers, IG mandates, ETF authorized
  participants — because their withdrawal is invisible to macro indicators and
  does not reverse when assets look cheap.
- **The long yield is the correlating variable across all six scenario
  clusters,** meaning the 25 scenarios are less diversified than they appear and
  a single rate event can fire several at once.
- **Roughly 28 of the 41 required instruments have no home in any report yet** —
  the coverage audit converts the scenario list from commentary into a ranked
  build queue.
- **A decorative instrument is worse than an acknowledged gap.** Scenario 13
  keeps no tripwire because settlement stops before prices move; attaching a
  weak proxy would create false confidence exactly where the failure mode is
  invisibility.

---

## III. The Monthly Macro Report: A Working Manual
**Companion to: Monthly Macro Report v16 and successors · ~29,000 words, 16 chapters**

**What it contains.** The pillar-by-pillar operating manual for the densest
report in the system. A preamble establishes the epistemic position, defines the
ten lenses applied to every pillar, and warns that pillar numbering is not turn
order. Chapters 1–8 give each quantitative pillar the full ten-lens treatment —
what it measures, the underlying metrics, historical behavior, named failure
modes, evolution and crowding, expressibility, and how to read it this cycle.
Chapters 9–10 handle Banking and Commentary on a deliberately modified template
(what the pillar watches, why it earns a slot despite thin instrumentation, and
the concrete list of what would make it quantitative). Chapter 11 is the
synthesis: the cycle sequence in five tiers — liquidity and credit turn early,
labor late, sovereign slowest of all — seven conflict-resolution rules for when
pillars disagree, five recognizable market configurations, a reading guide by
horizon, and an honest section on why compositing ten pillars into one number is
harder than it looks. A coda closes with three reading habits and the paper's
own falsification criteria.

**Timeless takeaways:**
- **The failure modes are named, specific, and load-bearing:** the Sahm Rule's
  2024 false trigger (rising unemployment from labor-force growth, not
  layoffs), the 818K benchmark revision, ISM below 50 for two years, LEI
  declining for two years, CAPE "overvalued" for thirty, the JGB widowmaker,
  and the 2011 downgrade where yields *fell*. Knowing how each indicator has
  embarrassed its users is the manual's core value.
- **Lead-lag order is the synthesis, not a footnote.** Which pillar turns
  first across a cycle tells you which pillar deserves the weight in a given
  month — liquidity and credit lead, labor lags, sovereign moves slowest — and
  it is inherently cross-pillar, which is why it lives in the closing chapter
  rather than inside any pillar.
- **Expressibility is a lens in its own right:** a great signal that can only
  be expressed through an illiquid structure is worth less than a mediocre one
  expressible in SPX options — the bridge between the report's analysis and
  its options appendix.
- **Financial repression is the arithmetic's base case** for the sovereign
  pillar — nominal growth held above nominal rates, negative real returns on
  government bonds — historically the typical resolution and politically
  durable, which argues for real assets over nominal ones on the long horizon
  and for holding the structural hedge continuously rather than timing it.

---

## IV. The Rate and Liquidity Machine
**Companion to: Monthly Macro — liquidity and sovereign pillars · ~16,450 words · referenced elsewhere in the library as “the Rates & Liquidity paper”**

**What it contains.** The plumbing paper, in two parts. **Part I** is history:
eleven monetary regime eras from 1907 through the Warsh appointment, treated as
a sequence of institutional settlements rather than a list of rate decisions.
The section the paper directs readers to first is the 1942–1951 yield peg and
the Treasury–Fed Accord: nine years in which the Fed subordinated policy
entirely to Treasury financing needs, ended by a negotiated settlement rather
than a law — seventy-five years old, and the closest historical analogue to the
pressures now on the committee. **Part II** is the instrument set: roughly fifty
levers across six families, spanning the Fed's price tools, the balance sheet,
and — weighted most heavily — the Treasury-side levers that have moved into the
foreground: the bill-versus-coupon issuance mix, the TGA, IORB, and the
buyback and reserve-management mechanics that the Treasury financing chain in
the Monthly report tracks — with a deep dive on the five levers that matter
most, five worked case studies (September 2019, March 2020, the 2022 gilt
crisis, SVB 2023, the 2023 bill-share shift), scenarios at four horizons with
probabilities and falsifiers, and 36 tactical signals mapped across all five
reports with thresholds and a cascade order.

**Timeless takeaways:**
- **Fed independence was restored by negotiation, not statute** — which means
  it can be eroded the same way, and the 1951 Accord is the template for how
  subordination to financing needs actually happens in practice.
- **The levers that carry the most weight now are Treasury's, not the Fed's:**
  bill share, the TGA, and buyback funding source together determine system
  liquidity at the margin, which is why a fiscal operation can be monetary in
  effect.
- **Fifty instruments across six families is the map for the liquidity pillar's
  instrumentation** — the paper is the reference for which series answers which
  question when reserves, RRP, TGA and issuance move together.
- **Regime eras, not rate paths, are the unit of analysis** — the paper's
  organizing claim, and the reason its history section precedes its mechanics.

---

## V. Currencies: A Structural Framework
**Companion to: Alternative Asset Report — and foundational to every paper above it · ~14,800 words, 33 sections across eight parts**

**What it contains.** The eighth paper in the series, and the one that sits
underneath the others: every asset in the Alternative Asset Report is priced in
dollars, and roughly half the theses in the metals and digital-assets papers are,
at bottom, theses about the dollar. The paper answers seven questions in
sequence — how currencies appreciate and depreciate and what that does to an
economy; how much of a currency's price is set by traders versus central banks;
where digital assets fit as a form of currency; the dollar's reserve status and
what would erode it; the Dalio big-debt-cycle devaluation framework applied
honestly; how to hedge foreign-currency exposure (written with the Thai baht
property exposure specifically in view); and how to trade currency views through
futures, options and ETFs. It carries a devaluation-scenario probabilities table
and a live case study: the first coordinated US–Japan yen intervention since
1998, which the paper uses to show what intervention can and cannot do.
Researched fresh at the time of writing, and materially reshaped by what the
research found. A September 2026 update added eight figures regenerated from
live daily history by a pipeline module (`fx_charts.py`) and a "Long View in
Pictures" block — thirty-year envelopes and five-year detail per major, the
envelope-versus-gold comparative, and the range table.

**Timeless takeaways:**
- **The reaction function outranks the balance sheet.** Any devaluation or
  debasement thesis must first survive the central bank's stance — a hawkish
  committee is the opposite of fiscal dominance, and a thesis that cannot
  explain the chair is not yet a thesis.
- **De-dollarization is into gold, not into other currencies.** The reserve-share
  data shows the dollar's decline in central bank portfolios accruing to gold,
  with no rival currency gaining — which changes what "dollar weakness" would
  even look like.
- **Intervention resets positioning without changing the differential.** The yen
  case study: the US reportedly sold euros rather than dollars to fund it, most
  plausibly to spare Japan from selling Treasuries — protecting the yen and the
  Treasury market at once, and within two weeks judged to have moved positioning
  but not fundamentals.
- **A view on any dollar-priced asset without a view on the dollar is
  incomplete in a way that eventually costs money** — the paper's organizing
  claim, and the reason it is filed as foundational rather than as one more
  asset paper.

---

## VI. Credit: A Structural Framework
**Companion to: Top & Bottom, Monthly Macro (valuation & credit pillar), Disruptive Themes · ~15,400+ words, 40 sections across twelve parts (re-measure after §29 insertion)**

**What it contains.** Subtitled *The price of risk, the ability to pay, and where
the cycle hides*, with two agreed emphases: private credit and bifurcation, and
corporate credit as a cycle-timing tool. The organising claim is that **the
credit cycle is a lending-standards cycle, not a spread cycle** — spreads move
last, and private credit's lagged marks have made the cycle partly invisible
until it isn't. Part III (private credit) is the longest at seven sections and
rests on the strongest single finding the research produced: PIMCO's June
observation that private-credit marks show *low time-series volatility alongside
high cross-sectional dispersion* across managers on comparable credits. Both
cannot be true if marks track a common value — so net asset values are driven by
manager-specific assumptions rather than a shared clearing level, which is the
bifurcation thesis in one finding and the reason mark dispersion sits in Tier 1
of the monitoring. The corporate-credit and signals parts are built around
lead-lag and acceleration rather than description. Current state at writing: HY
at 269bp, the richest decile against a ~450bp long-run median, with dispersion
widening beneath it. Appendix C is a one-page table of the **seven concealment
mechanisms** — LME rerouting, manager marking, PIK, amend-and-extend,
non-accrual discretion, index composition, aggregate averaging — each with the
segment it operates in, what it suppresses, and the tell that sees through it.
Owns the price of risk and the borrower's ability to pay; hands the funding
channel to Rates & Liquidity. A post-publication addition folded the library's
trading-the-curve material into its Position Construction part — duration,
steepeners and flatteners, term-premium expression, TIPS and breakevens, swap
spreads, futures basis and roll — closing with a common-bus table mapping each
paper's long-yield exposure to its direct rates expression. (Inserted as §29;
subsequent sections renumbered 30–40.)

**Timeless takeaways:**
- **Dispersion is the signal, not the level.** An index at cycle tights says
  nothing the cross-section does not contradict; the tail tier and the
  manager-to-manager mark spread are where the cycle is visible first.
- **Lending standards lead, spreads lag** — SLOOS and the private-credit
  origination terms turn before any public spread does, which is what makes
  credit a timing tool rather than a confirmation.
- **Private credit's smoothness is manufactured**, and the seven concealment
  mechanisms are the checklist for seeing through it — each has a tell.
- **Bifurcation is structural, not cyclical:** the marginal borrower has
  migrated into floating-rate, quarterly-marked structures, so the public
  indices measure a healthier population than the one actually at risk.

---

## VII. Energy: A Structural Framework
**Companion to: Alternative Asset (oil and gas rows) and Monthly Macro (inflation, geopolitics) · ~12,900 words, 40 sections across twelve parts**

**What it contains.** Subtitled *Oil, gas, power, and the shift from barrels to
megawatts*, with power and the AI-load thesis as the agreed emphasis — Part IV
(Power) is the longest at seven sections. Two claims organise it. **Energy is a
spare-capacity and inventory market, not a resource market:** price is set by the
size of the buffer — OPEC+ spare capacity, inventories, refining slack, LNG
capacity, grid reserve margins — and every major price episode of fifty years is
a buffer story. And **electricity has become the scarce energy commodity**, with
binding constraints now in interconnection queues, transformer lead times, firm
generation and gas-turbine delivery rather than fuel. The power part is anchored
on PJM's capacity auction clearing *at its administrative price cap* of
$333.44/MW-day for 2027/28 — from $29 two years earlier — while still falling
6,517 MW short of its reliability requirement, read alongside the July 31 FERC
filing to curtail 50 MW-plus loads first. The buffer thesis is tested against the
Hormuz disruption: 7–8 mb/d removed produced a $40 monthly Brent range because
inventories sat below the five-year low and OPEC+'s "spare capacity" was behind
the strait. Same shock, four buffers, four prices — Appendix C tabulates it.
The track-record section carries Goldman's February call of $60 Brent and a 2.3
mb/d surplus, explicitly conditional on no Iran disruption; Brent touched $105
in July. Covers crude, gas and LNG, refining, power, uranium, coal briefly, and
energy geopolitics. Hands copper to Metals and the inflation transmission to
Monthly Macro.

**Timeless takeaways:**
- **Spare capacity that cannot reach the market is not a buffer** — the Hormuz
  episode is the proof, and the buffer-not-reserves frame is how every energy
  price should be read.
- **A market offering its maximum permitted price and still failing to procure
  enough supply is genuine physical scarcity** — the capacity-auction
  signature; when the driver is domestic and structural, it survives scenarios
  that reprice the fuel.
- **Energy balances are conditional on the absence of exactly the events that
  move energy prices** — the forecasting record is bad not from carelessness
  but from construction.
- **Every demand thesis has a single point of failure, and it must be named** —
  when load forecasts span a factor of two, the honest posture is to carry the
  bust as a live, weighted scenario in Tier 1 of the monitoring rather than as
  a caveat.

---

## VIII. Metals: A Structural Framework
**Companion to: Alternative Asset Report · ~17,100 words, 38 sections**

**What it contains.** The sibling to the digital-assets paper, built on the same
principle — understand mechanisms rather than narrative, and know in advance what
evidence would change your mind — applied to gold, silver and copper as three
genuinely distinct assets rather than three points on a "commodities" spectrum.
Gold receives roughly half the paper by design: it is the only one of the three
priced primarily by financial rather than industrial demand, which makes it both
the hardest to model and the most consequential for portfolios. The analytical
frame rests on the stock-versus-flow distinction (gold is never consumed, so
incremental buying draws on the above-ground stock, not mine supply), then works
through supply mechanics, demand pools, and cross-cutting drivers for each metal.
Part VI is a signal-reading guide with a signal hierarchy per metal and an explicit
false-signals section. Later parts cover forecast ranges with their track record
(including the 2026 disagreement in which Goldman projects a copper surplus while
Morgan Stanley projects a deficit), a ten-year structural view, a monitoring
framework, a regime-dependent correlations section, and a position-construction
part covering physical, ETFs, futures, options and mining equities with vol-scaled
sizing and the copper instrument problem.

**Timeless takeaways:**
- **The supply side is knowable; the demand side is where the work lives.** Mine
  output, grades, cost curves and treatment charges are published, slow, and
  observable — a rare gift — so the divergence among the three metals is almost
  entirely a demand-pool story.
- **Silver is the most analytically treacherous of the three:** roughly 70% is
  mined as a byproduct of lead, zinc, copper and gold, so its supply is nearly
  insensitive to its own price and can tighten for reasons wholly unrelated to
  silver — a base-metal downturn cuts silver output as a side effect. Treating it
  as "high-beta gold" or "an industrial metal" both fail, because which identity
  dominates changes with the regime.
- **For gold, the marginal-buyer hierarchy outranks supply:** identify which
  bid is on — official sector (the floor), Western ETF (the second leg), fast
  money (the fragile one) — because jewellery, recycling and mine supply are
  second-order to who is buying at the margin.
- **Correlations are regime-dependent by shock type, and copper's instrument
  problem is real:** the paper's portfolio summary table and position-construction
  part exist because the expressible version of a metals view is often a poorer
  instrument than the analysis deserves — the expressibility lens from the Monthly
  manual, applied to physical markets.

---

## IX. Digital Assets: A Structural Framework
**Companion to: Alternative Asset Report · ~19,150 words**

**What it contains.** An educational reference designed to make the reader
self-sufficient in forming and updating a long-horizon view on digital assets —
explicitly not a thesis or price target. It covers taxonomy and value-accrual
theory (what each asset class actually is and how value would mechanically
attach to it), the honest bull and bear cases stated as their strongest
proponents would state them, the open questions that do not yet have answers
(Ethereum's value capture, Bitcoin's correlation under institutional ownership,
quantum timing), and a monitoring map of what to watch so views update on
evidence rather than narrative. A published-forecast section compiles
institutional price ranges (ARK, Bernstein, Standard Chartered, VanEck,
JPMorgan and others) — led deliberately by their track records, including the
stock-to-flow post-mortem and Standard Chartered's Ethereum reversal. Written
intentionally during the 2026 drawdown (BTC ~$78K off $126K), on the stated
test that durable content should read identically had it been written at the
top.

**Timeless takeaways:**
- **Separate durable structure from cyclical noise:** mechanisms move slowly,
  prices move constantly, and nearly all crypto commentary fails by analyzing
  the second while claiming to analyze the first.
- **Stock-to-flow is the cautionary case for the whole asset class** — 95%
  historical fit, catastrophic out-of-sample failure, and academic post-mortems
  showing its explanatory power was ~80% a log-time trend. Fitted scarcity
  models are curve-fitting wearing a thesis.
- **Institutional forecasts are anchors, not evidence:** the compiled ranges
  exist to be argued against, and the paper documents forecasters abandoning
  their own correct structural work in response to price.
- **The bear case deserves equal rigor because crypto research is structurally
  polluted by advocacy** — nearly everyone writing about the asset class owns
  it, so the paper states each side at full strength and names the evidence
  that would settle each disagreement.

---

## X. Tops and Bottoms: Every Major U.S. Turning Point Since 1970
**Companion to: Top & Bottom Report · ~16,000 words (est.), 38 pages · three formats from one source (docx → pdf → offline HTML with anchor TOC)**

**What it contains.** A disciplined historical study of every major U.S. equity
top and bottom since 1970 — roughly eight true bears plus the near-misses — with
each episode given an identical treatment: context, drivers, what signaled and
what stayed silent, the descent, bottom signals, a standardized metrics table,
forward returns at 1/3/5/10 years measured from both the top and the bottom, and
the aftermath. Two structural decisions define the paper. First, episode chapters
are strictly historical and objective — present-day comparisons are confined to a
single closing "Today Against History" chapter, because forced analogies scattered
through history chapters are worse than none. Second, the near-misses get their
own chapter (LTCM 1998, 2011, 2015–16, 2018, 2024): a study of only confirmed
turning points has survivorship bias built in, and the episodes that looked
terminal but resolved without bears are what separate signal from noise. The
paper is explicit about data honesty — no VIX before 1990, no HY OAS before
~1996 — showing gaps rather than backfilling fabricated numbers. It sits directly
on the 13-episode calibration harness that scores the live composite — and as
of September 2026 its findings are production code: the v8 weight rebalance,
an eighth Leading indicator (HY spread acceleration), and three parallel
overlays (concentration/complacency, credit acceleration, funding stress)
that catch the top types the composite structurally cannot. The synthesis
chapter's trigger taxonomy — inflation-policy, credit, valuation, mechanical,
exogenous — is the analytical basis for that overlay architecture.

**Timeless takeaways:**
- **The controls passing 4-of-4 is the most important calibration finding.**
  Volatility spikes, mid-cycle pullbacks and sharp corrections all stayed
  NEUTRAL — the framework does not over-fire, which means the fix it needs is
  more sensitivity at the extremes, not more specificity in the middle.
- **Tops went 0-for-3.** Every historical top scored between −0.13 and −0.52,
  never approaching the −1.2 threshold — the structural asymmetry that led to
  reframing top-side output as a distribution shift rather than a signal, and to
  the parallel overlays (concentration, HY acceleration, liquidity) that catch
  what the composite cannot.
- **The misses are diagnostic, not embarrassing.** LTCM was arguably a control
  mislabelled as a bottom — the framework's caution was correct; and 2022 was
  missed because the market turned on the second derivative of inflation while
  macro conditions were still worsening, which is a real lesson about what
  bottoms turn on.
- **"What signaled, what stayed silent" per episode is the paper's working
  core** — it extends the calibration exercise across the full history, with
  lead times, and is the section a future refresh should reread before trusting
  any current signal.

---

## XI. Volatility: A Structural Framework
**Companion to: the execution layer, the Daily Cascade, and every paper's expressibility question · ~15,000 words, 42 sections across twelve parts**

**What it contains.** The agreed emphasis is regime identification and
cross-asset volatility — Part III (cross-asset vol) and Part VI (regime
identification) carry the weight. The organising claim: **volatility is the price
of insurance, and the insurance is systematically overpriced except when it is
catastrophically underpriced** — the variance risk premium, its crowding, and
its unwinds are one fact, not three. The equity vol complex is treated in full:
VIX mechanics, term structure, the pathologies of vol ETNs, the surface, VVIX
and implied correlation, and what 0DTE changed about the realised-versus-implied
relationship. The paper's operational content reduces to two questions the VIX
level cannot answer — which regime is the market in, and how close is the
boundary — with a regime map, a signal hierarchy, and regime tells as the
working sections. Two flags worth knowing: the options-ETF complex is now 800-plus
funds and ~$250 billion, sixty times the inverse-VIX products that produced
February 2018; the paper is careful they are not directly comparable but gives a
February-2018-at-scale outcome 20% over the decade and names the candidates —
scheduled-reset products and bank hedging books. And the April 2025 haven
anomaly, in which Treasuries and the dollar sold off *with* equities, is recorded
as a category the framework should treat differently if it recurs, because the
resolution mechanism itself would be impaired. Cites the Dealer's Hand for
hedging mechanics rather than re-deriving them. **Now operationalized:** the
five-state regime classification and the tells counter run live in the Alt
Asset weekly's §7 (September 2026), with the four options-surface tells the
free data tier cannot compute stated as gaps in-render.

**Timeless takeaways:**
- **Regime, not level.** The VIX at 15 means different things in different
  regimes; the operational questions are which regime and how near the
  boundary, and the paper builds the map and the tells to answer them.
- **Three facts are one fact:** the risk premium, the crowding into harvesting
  it, and the unwinds are the same phenomenon at different points in the
  cycle — analysing them separately is how short-vol strategies look
  brilliant until they do not.
- **The vehicle carrying the short-volatility trade changes every cycle; the
  mechanism does not** — size the current complex against the last unwind's,
  and assume the failure mode has moved, not vanished.
- **A haven anomaly is a regime of its own** — when the hedges sell with the
  risk, the framework's resolution mechanism is impaired, and April 2025 is the
  template to recognise it.

---

## XII. The Daily Cascade Paper
**Companion to: Daily Cascade (intraday suite) · ~15,000 words (est.), six parts plus appendix**

**What it contains.** The operating manual for the intraday report system —
and, in its Chapter 24, the **canonical analytical backlog** for all Daily
Cascade refinements (three tiers, 22 ranked items; the guide stays canonical
for numbering, Ch. 24 for that backlog — Ch. 24 is the canonical *analytical* backlog for Daily Cascade refinements; the architecture doc's deferred list carries scheduling pointers only). The
five blocks (Direction, Market Base, Confirmation, Backdrop, Execution) and the
~24 numbered sections beneath them, with per-section reading rules. The dealer
positioning chapter is the technical core — gamma flip, call and put walls, the
JHEQX collar bookends, 0DTE mechanics — codified into numbered rules
(flip-drift as a reduce-size trigger; the rare gamma-up-skew-up divergence as a
warning regardless of tape; never carrying a position overnight on a 0DTE
level; ignoring quarterly collars unless spot is within ~2%). The synthesis
part contains the paper's most consequential chapter, the **dependency map**:
the 24 sections reduce to six genuinely distinct information clusters — dealer
mechanics, participation, macro pricing, price structure, sentiment, and slow
leverage/structure — with everything inside a cluster being one fact described
several ways. A deferred-refinements section lists the dealer-data upgrades
(vendor cross-check, charm/vanna, pin logging, normalization), all of which
have since been dispositioned into the v17 architecture.

**Timeless takeaways:**
- **Confluence must be counted across clusters, not sections.** Five sections
  agreeing inside the dealer-mechanics cluster is one signal, not five — the
  dependency map is what makes the confluence discipline honest.
- **Within-cluster divergence is the rare, high-value signal:** positive and
  rising GEX with steepening put skew means dealers are pinning spot while the
  market pays up for tails — reduce size regardless of the tape.
- **Flip drift beats flip level:** the gamma flip rising toward spot faster
  than spot is rising means the stabilizing structure is eroding, and it has
  more forward value than the absolute GEX reading.
- **0DTE structure dies at the close.** The strongest pins of the day are also
  the most worthless for anything held overnight — the entire late-day gamma
  edifice will not exist tomorrow.

---

## XIII. The Dealer's Hand
**Companion to: Daily Cascade — dealer positioning · word count not yet measured · illustrated edition: 15 computed figures + 2 worked ledgers**

**What it contains.** The paper that derives the mechanics the Daily Cascade
paper applies. Where Paper V gives reading rules for gamma, walls and flips, this
one builds them from first principles: who is on which side of the options
market, why dealers end up long calls and short puts under the standard customer
flow, and therefore why call gamma is positive and put gamma negative in the
conventional signing. It surfaced that the Daily Cascade paper's Chapter 2.3 had the sign
convention backwards; the discrepancy was resolved at the source (Ch. 2.3
corrected, this paper's language softened to a cross-reference), so the two
now read as application and elaboration of one mechanic. It points at the
real exception — a
fund that *sells* the lower put of its spread, leaving dealers long a put the
convention assumes they are short, with the JHEQX collar as the worked case.
Chapter 6.2 carries the reconciliation with the Daily Cascade paper explicitly.

**Timeless takeaways:**
- **Sign conventions are assumptions about who is on which side, not facts
  about the market** — standard GEX signing treats calls positive and puts
  negative because it assumes customer flow; when a large structure runs the
  other way, the convention is wrong at exactly the strikes that matter most.
- **The JHEQX collar is the canonical exception,** not the canonical example:
  the fund's short lower put makes dealers long that put, which inverts the
  usual read at that strike.
- **Two papers, one mechanic.** The Daily Cascade paper applies; the
  Dealer's Hand derives — and when they briefly disagreed on signs, the
  derivation located the error and the source was corrected. Derivation
  outranks application; that is why both exist.
- **Flow-signed data beats assumed-sign data** — the case for verifying whether
  customer-versus-dealer polarity is exposed at the current data tier before
  trusting any aggregate gamma figure.

---

## XIV. Technical Indicators
**Companion to: Daily Cascade and the execution layer · ~6,350 words, 8 chapters + reference appendix · v1.1 adds five worked figures and four numeric reading tables**

**What it contains.** The shortest paper in the library, and deliberately so — its
opening chapter argues that most technical indicators are transformations of
price and therefore cannot contain information price does not already have, which
leaves three legitimate uses: regime classification, levels as reflexivity-backed
coordination points, and timing inside a view held on other grounds. The chapters
then walk the permitted families: regime measures (realized-vol percentiles, ATR
compression, banded ADX with hysteresis) with a worked morning reading; trend and
momentum with the CTA and momentum-factor history as a discipline on
expectations; oscillators exposed as one indicator in many costumes with two
honest readings and one dishonest one; volume and structure as the single family
with information beyond price; and levels ranked by the mechanical force behind
them — dealer hedging strongest, attention weakest — with a three-verb zone
discipline (defended, accepted, swept) that converts level-reading into a
gradeable log. A traps chapter maps the field's failures onto the system's
existing guards, and the placement chapter draws the wall: regime lines and level
stacks into the Daily blocks and execution plan as conditioners, nothing into the
Monthly composite, any pillar score, or any trigger. A fourteen-row reference
table closes it — the entire permitted surface, subject to the annual prune.

**Timeless takeaways:**
- **A transformation of price cannot know more than price** — so technicals are
  compression, not discovery, and their value is standardizing the read, never
  generating the view.
- **Five clusters, not fourteen indicators:** regime, trend/breadth, one
  oscillator, volume/structure, and levels-by-mechanism. A screen of twelve
  indicators shows at most five facts, and confirmation is only counted across
  clusters.
- **No oscillator reading is actionable until the regime is classified** — in a
  range, extremes are fadeable locations; in a trend, overbought is what
  strength looks like, and selling it is the field's most reliable losing trade.
- **No pattern claim enters the system without a measured base rate** — the pin
  log is the template, the named-candlestick taxonomy is the cautionary case,
  and every level interaction gets logged in three mechanical verbs so the
  question "which level class actually holds" becomes empirical within two
  quarters.

---

## XV. Equities: A Structural Framework
**Companion to: Top & Bottom, the Daily Cascade, Disruptive Themes (Factor II) · ~8,350 words, 36 sections across twelve parts + two appendices**

**What it contains.** The paper on the asset the system trades most, built with
a deliberate emphasis on concentration. Part I establishes the equity as a
residual claim and the earnings-versus-multiple decomposition as the first
analytical act, with the revision mechanics that move price and the long yield
as the equity multiple's duration. Part II is the index machine: cap-weighting
as a momentum strategy, passive flow as the purest price-insensitive bid,
index inclusion as a calculable forced flow, and buybacks as the largest and
most pro-cyclical bid in the market, with a calendar. Part III gives the five
factors their honest payoff shapes and decomposes the concentration trade into
its factor book — long growth, long momentum, short value, short size at a
third of index assets. Part V is the core: the Mag 7 at ~32–34% of the index
(the highest top-seven share since the Nifty Fifty), why this episode is more
earnings-justified than any prior one, and why the multiple is still the risk;
the semiconductor fulcrum read as an equity — $530 billion of commitments
against a $96 billion quarter, five customers at 70% of receivables — and the
2021–22 unwind template. Part VI maps the AI complex as four concentric rings
and treats the mega-IPO wave as a float-against-forced-flow story, with the
Nasdaq-100's 15-day fast-entry rule and the SpaceX listing as the exhibit.
Part VII gives four scenario families for the concentration over three to five
years with weights (earned persistence 30%, orderly broadening 30%, capex
de-rating 25%, external regime break 15%). Part IX is what to watch by cadence;
Part X names the false signals; Appendix A is a twelve-row concentration
dashboard mapped to the reports; Appendix B tabulates the historical episodes.

**Timeless takeaways:**
- **A cap-weighted index is a momentum strategy, and a concentrated one is a
  leveraged momentum strategy** — the index is not the diversified thing its
  name implies, and the book should be built on what it actually is.
- **The concentration is more earnings-justified than any prior episode, and
  that is exactly what was true of every prior episode at its peak** — the
  businesses usually survive; the multiple does not; deceleration at a high
  multiple is the mechanism.
- **A concentration cohort resolves into one trade, and the trade breaks at
  its fulcrum** — map the circularity (whose earnings depend on whose capex),
  then watch the supplier's balance sheet — inventory, receivables aging, the
  margin trough — because revenue is the last line to turn.
- **In any capex boom, the buyers' guidance is the master series and the
  end-users' revenue is the decisive one** — the builders bear the losses in
  every historical case where the second never arrived to pay for the first.

---

## XVI. Positioning & Flows
**Companion to: every report's positioning line, the tail watch, the Confirmation block · Draft 1 · ~8,350 words, nine parts + appendix**

**What it contains.** The paper about the part of the market that does not
think. Part II maps ten mechanical-holder types — options dealers, leveraged
ETFs, vol-control and risk-parity funds, CTAs, index funds and committees,
month-end rebalancers, corporate buybacks, positioning surveys, retail, and
forced sellers — each with its rule, its observability (announced, inferable,
hidden), and the system's data. Part III is the master calendar with the
event-classification table that keeps a reconstitution-day auction from ever
reading as discretionary flow. Part IV is the spine: absorption as *response
per unit of stimulus*, stated once as a primitive and worked through four
examples — the closing auction (absorption reversal vs pressure continuation),
the yen (positioning × velocity against risk-asset response), the leveraged-ETF
rebalance ((L² − L) × AUM × r, the one flow computable in advance), and index
inclusion (the pre-positioned path vs the effective-day auction). Part V gives
six flow models with the honesty rule for inferred flows — direction and timing
reliable, magnitude always banded. Part VI is about not misreading positioning:
levels are vulnerabilities, changes with catalysts are signals; percentiles
against own history; COT's three-day lag; FINRA's two series that are not the
same; RTAT's censored sample. Part VII supplies the seven-group independence
table (the units that vote under the architecture's correlated-confirmation
rule) and the first factor map for the doctrine's Rule 16 heat calculation.
Part VIII is the data-status table — built, computable, forward-only, GAP.

**Timeless takeaways:**
- **A flow is a pressure, not a forecast; the information is in the response
  per unit of pressure** — a forced seller met by deep demand is a bullish
  fact wearing a bearish headline.
- **An extreme positioning level is a vulnerability; it becomes a signal only
  with a catalyst, and its size is the flow the catalyst can release** — the
  record yen short was profitable for months before August 2024.
- **Count mechanisms, not series** — five surveys saying bullish are one fact;
  vol-control, CTA and leveraged-ETF selling on a down day are one flow seen
  three times; the seven groups are the votes.
- **Compute the flows you can, log the ones you can only observe, and never
  buy history to shortcut the second** — leveraged-ETF rebalances are exact,
  auction absorption is forward-only from September 2026, and the difference
  decides what can be backtested.

---

## XVIII. The Operating Doctrine
**Governs: how every report is consumed and how capital is deployed · v1.0 · ~25,600 words, nine parts + appendix · changes only at the monthly session (Rule 20)**

**What it contains.** Different in kind from the rest of the library: it says
how the operator is to behave given what the reports say, in the first person,
written against the trader he has been. Part I is the card — one page, reread
weekly. Part IV is the horizon ladder: four books with separate edge families,
owning reports, risk figures and loss stops — Allocation (bands by Macro dial,
with a floor as binding as the ceiling), Swing (Livermore entries, Brandt
exits, a five-session stop on any counter-trend position), Tactical (defined
risk from the 0700 list, the volatile-day protocol as its fence), Opportunistic
(fifteen minutes to a packet or a pass, and a ring-fenced tail-hedge budget
where the cynicism is allowed to live). Part V is the three dials — Macro,
Volatility, Gamma — acting multiplicatively on size and conjunctively on
permission, with the trust matrix that answers "should this signal be trusted
*now*." Part VI wires the cascade: top-down sets the budget, bottom-up spends
it and may veto but never enlarge; the Decision Packet as the unit of action;
the semi-automation contract. Part VII is the risk doctrine and the honest
arithmetic of the $5,000–$10,000-a-week aspiration — shown to be a Sharpe-4
process if unconditional, and a lumpy-year model if regime-conditional — with
a budget-first ladder of promotion gates. Part VIII is twenty-nine rules, each
traced to its Market Wizards origin, the way this book has failed before, and
the component that enforces it. Part IX is the ledger, the six post-mortem
questions, edge decay, adapting without drifting, and the adoption sequence:
Book A first, Book C second restricted to positive gamma, B third, D last.

**Timeless takeaways:**
- **Prediction accuracy is not the objective; edge, sizing, asymmetry and loss
  control are, and they can be assembled from contradictory methods** — the
  Wizards agree on almost nothing except the operating system.
- **The operator is a design input, not an apology** — every known bias gets a
  named rule, a ledger cut read first, and a structural cost; a tail thesis is
  a hedge budget, not a position; the allocation floor exists because of 2008.
- **Size to the opportunity, never to the P&L goal** — sizing to a target
  guarantees size is largest when the edge is weakest; quarter-Kelly is a
  ceiling invisible until the register has measured the edge.
- **Re-entry after a switch happens at a scheduled session, never sooner** —
  a switch reset by the next morning's mood is not a switch.

---

## XIX. Building and Validating a Systematic Book
**Companion to: the trading infrastructure, the register, the IBKR gates · Draft 1 · ~9,100 words, eight parts + appendix · as-built after Gate 1 (5 Sep 2026)**

**What it contains.** Planned as the specification the broker integration
would be built to; written, instead, after the integration was built in a
weekend, as the as-built record with a forward section. Part II is the
register: a decision (not a trade) as the unit, packets immutable by database
trigger and replayed exactly as the acceptance test, supersession in place of
edits, DECISION_BLOCKED as the freshness gate between report and trade
(including the Saturday-vintage ruling and the two false-block bugs that
mattered more than the true blocks), and the two-layer Brookfield enforcement.
Part III is execution: the three senses of "read-only" and which one turned
out false; the What-If preview refused under Read-Only in the vendor's own
words and the ruling that keeps Read-Only on through the hand-placed phase;
server-side brackets, limits that say something, GTC into a closed market; the
one-session-per-username constraint; the opportunistic book's stricter rules.
Part IV is sizing and cost as code — risk dollars over distance to
invalidation, dial multipliers stamped on every packet, the Fixed commission
schedule verified by hand with provenance, the kill-switch ladder as
measurement today and refusal tomorrow. Part V is validation on three clocks,
the "a gate must be verified to fail and must not pass on nothing" discipline,
the IV solver's three-round path to an earned green, the **five named failure
classes** of the build (none found by reading), shadow outcomes for every
decision taken or not, and what can and cannot be backtested. Part VI makes
tax an expression decision (Section 1256 vs ETF options; wash sales between
Book C and Book A's beta sleeve; assignment risk for an absent operator). Part
VII is the compliance boundary. Part VIII is the gate ladder and the honest
not-yet-built list. The appendix walks decision #1 end to end.

**Timeless takeaways:**
- **A safety claim is a hypothesis until a test or the vendor's own refusal
  confirms it** — the client flag that "prevented trading" prevented nothing;
  the guarantee was the server's setting plus the absence of code.
- **Identity and time bugs are found by tests and deployment, never by
  reading** — five failure classes, zero caught by inspection; assert every
  directive, canonicalize every timestamp, key every write on the session.
- **Grade the decisions you did not take** — shadow outcomes for declined and
  drafted decisions are what make "doing nothing is a position" measurable.
- **The thesis, the instrument, and the tax treatment are three decisions** —
  an index thesis in SPX options and the same thesis in SPY options are not the
  same trade after tax, after assignment risk, or after the wash-sale rule.

---

## In draft and planned

**XVI and XIX — Draft 1 editions exist** (6 September 2026), written the week the
register, the broker connection and the closing-auction and retail sources were
built or admitted. Both are forward-looking by construction — XVI's absorption
base rates and XIX's measured edge accumulate from September 2026 — and both
declare what would trigger their second editions: sixty sessions of auction
history and a forced-flow episode watched in real time for XVI; Gate 2 and the
first hundred closed decisions for XIX.

**XVII. Portfolio Construction Across Regimes — Draft 1 exists** (~4,400
words, preview edition). The frame, vocabulary, sizing disciplines and open
questions, deliberately theoretical, with an explicit four-condition trigger
for the empirical Draft 2: the v17 store and register live, the dashboards
settled, three months of register data, and IBKR Gate 1 providing
mark-to-market. Expected Draft 2: late Q4 2026 to Q1 2027. (The
trading-the-curve material originally scoped here was folded into the Credit
paper's Position Construction part instead.)

**Deliberately deferred.** The behavioral paper — size creep after wins, thesis
attachment, overtrading in chop, narrative capture by one's own research — is
written in six months *from the register*, when it is this operator's data
rather than the literature; the Operating Doctrine's Section 9.2 specifies the
seven categorical fields it will need, populated from day one. Real estate, emerging markets and China, and
agriculture beyond the fertilizer chain remain real but lower-priority
candidates.

**The standing caution.** Knowledge is now the least scarce input. What is
scarce is calibration data and execution discipline under live conditions, and a
library this size carries the sophistication trap — being highly informed
substituting for being right, with every loss articulately explained. The
register is the antidote and outranks any paper on this list.

---

## Appendix — Executive summary: the current read (September 2026)

*This section is the most perishable material in the guide: it is a snapshot of what the library collectively says about the market **at one date**, and it is rewritten quarterly. It sits at the end for that reason — the tables, the cross-references and the per-paper entries above are durable; this is not. If the date above is more than a quarter old, treat what follows as history rather than as a read.*

*This section is the perishable half of the guide: one synthesis of what the
fifteen papers currently say about this market. The per-paper pages below are
the timeless half. Rewrite this section each quarter; the pages should barely
move.*

**The regime in one sentence:** a late-cycle, extraordinarily concentrated
market running on mechanical bids and spent buffers, priced for continuity by
its aggregates while its cross-sections, its plumbing, and one physical market
dissent — with every thread transmitting through a single variable, the long
yield.

**Start with the machine that prices everything else.** Net federal interest
has crossed its 1991 record share of revenue at roughly half the 1991 yield —
the stock is doing the work — and the policy response is a chain of
maturity-shortening operations: buybacks doubled, the Treasury's own cash
account floated as a funding source, a coordinated yen intervention designed
partly to keep the largest foreign holder from selling. The Rates & Liquidity
paper's history says this rhymes with 1942–51, when the Fed subordinated policy
to Treasury financing and independence returned only by negotiation — and the
same paper's instrument inventory says the levers that matter now are
Treasury's, not the Fed's. Against that, the Currencies paper's central caution:
the sitting Fed chair is hawkish, debating hikes, and a fiscal-dominance thesis
must explain how it survives a central bank actively fighting inflation. That
tension — quasi-monetary fiscal operations under a hawkish chairman — is the
single most important unresolved question in the system, and the
TGA-versus-reserves series is its referee.

**The markets are split on the verdict, and the split is the information.**
Bonds priced the operations as trivial: the ten-year returned to its highs
within a week. Hard assets priced the precedent: gold up 14% in a month to
records — but the Metals paper's decomposition says the *paper* bid did it,
with physical demand at a five-year low, which is the fragile-rally
configuration, not a confirmed debasement regime. The structural bid is the
official sector — central banks absorbing most of mine supply, the
reserve-share convergence gap unfilled — and the Currencies paper's data says
de-dollarization, where real, flows into gold rather than any rival currency.
Meanwhile the liquidity buffer beneath all of it is spent: the reverse-repo
facility at zero, reserves falling, every marginal drain now landing where it
can hurt.

**Credit is the dissenting pillar, and it dissents the way the Credit paper
predicts.** The index sits in its richest decile while the CCC tier has blown
out and — the paper's best finding — private-credit marks show low volatility
*across time* and high dispersion *across managers*, which cannot both be true
if marks track a common value. The cycle is a lending-standards cycle; spreads
move last; and the visible tail plus the manufactured smoothness say standards
are already turning where the marginal borrower actually lives.

**The equity market is the concentration, and the concentration is one trade.**
Seven companies are roughly a third of the index — the highest top-cohort share
since the Nifty Fifty — and the Equities paper's honest verdict is
double-edged: this is the most earnings-justified concentration episode on
record (roughly 31% of earnings, 70% of economic profit), *and* that is
precisely what every prior episode looked like at its peak, because the
casualty is never the businesses but the multiple, and the mechanism is
deceleration at a price that assumes none. The trade's fulcrum is the compute
supplier, whose balance sheet now carries the cycle — half a trillion of
forward commitments against a $96 billion quarter, five customers at 70% of
receivables — with the 2021–22 unwind template loaded and three lines to watch
(inventory, receivables aging, the margin trough) before any revenue headline.
The mega-IPO wave adds to the same trade: index fast-entry rules now feed the
passive machine companies with no public earnings history and small floats
against scheduled lockup supply. Hyperscaler capex guidance is the master
series for all of it; whether ring-four revenue ever arrives — whether anyone
besides the suppliers gets paid — is the decisive one.

**The loudest divergence in the system is physical.** The strait has been
effectively shut for six months, war-risk premiums have repriced two hundred
fold, Gulf exports have halved — and crude sits at pre-crisis prices. The
Energy paper's buffer frame sharpens rather than resolves it: the buffers that
normally absorb such a shock are at or below five-year lows, and spare capacity
trapped behind the chokepoint is not spare. Either the world has adapted or a
large tail is being underwritten at normal premiums; the framework holds both
hypotheses with a decision date rather than an opinion. And beneath the oil
story, the paper's power thesis is already resolved: a capacity market clearing
at its administrative price cap while still short of its reliability
requirement is genuine physical scarcity, domestic and structural — the place
where the energy system and the AI trade collide, with the same single point of
failure: hyperscaler capex.

**The monetary architecture is moving in plain sight.** Stablecoin issuers are
load-bearing in published Treasury financing plans — private money creation
inside sovereign finance — which sharpens both crypto tails at once (a depeg is
now a bill-market event; a regulatory reversal removes a marginal buyer by
decree), while bitcoin's violent month on a Fed speech says the asset behavior
is fully intact. The Digital Assets paper's frame holds: the infrastructure
question and the asset question are separating, and the infrastructure is
winning the official embrace while the asset keeps its beta.

**The volatility surface prices none of this.** Implied sits in the low teens
while the Volatility paper counts an options-income complex sixty times the
size of the products that produced February 2018 — different vehicles, same
premium-harvesting crowd — and flags the April 2025 haven anomaly, when the
hedges sold with the risk, as the template for what a modern unwind could look
like if the resolution mechanism itself is impaired. Insurance is cheap at
exactly the moment the list of things it would have to insure is long.

**Four threads run through all of it, and they are the library's real
findings.** *The buffers are spent* — RRP at zero, oil inventories below
five-year lows, grid reserve margins short, the credit tail already paying —
while every headline aggregate reads calm. *The surfaces are held by mechanical
bids* — passive flow, buybacks, stablecoin reserves, the official gold bid —
and mechanical bids fail differently: on calendars and rules, not on
valuations, and without reversing when things get cheap. *The divergences are
the tells* — physical-versus-price in energy, CCC-versus-IG in credit,
paper-versus-physical in gold, cap-versus-equal-weight in equities,
PCE-versus-CPI in inflation — because when an aggregate and its cross-section
disagree, the cross-section is usually early. And *everything rides the same
bus*: the long yield correlates the tail clusters, prices the concentration's
duration, sets the fiscal arithmetic, and decides the debasement trade. The
book's aggregate exposure to it is the book's real position.

**The path the whole framework is least positioned for is named, deliberately:
inflation re-acceleration.** Producer prices at a four-year high, the Fed's
preferred core measure running well above core CPI in the unusual direction,
guidance withdrawn, hike odds priced — every pillar currently assumes
disinflation, which is itself the reason to weight the alternative.

**What would rewrite this summary,** in either direction: the TGA-and-reserves
series confirming or refuting the monetization leg; any top-five capex cut, or
two more quarters of the supplier's balance-sheet lines outgrowing sales;
strait transits recovering — or a re-closure that finally moves price;
ring-four revenue arriving at scale; core PCE decelerating through three
percent; the equal-weight index quietly taking leadership. Each is observable,
each is logged, and the register — not the library — will grade whether reading
all of this made the trading any better. That is the standing caution: the
system is now long sophistication, and the only cure for the sophistication
trap is graded results.

---
