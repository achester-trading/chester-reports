# Earnings

## The Reaction Is the Object

**Companion white paper — chester-reports library**
**Series placement:** with the market-structure layer, after *Equities* and *International Equities* (numeral assigned by the library guide on commit; cross-references by name)
**Version:** 1.0 — September 2026
**Status:** Framework and manual. Governs the earnings-event setup, the cohort monitor's revision flags, and the valuation vocabulary the single-name books use. The HTML edition is canonical.

---

### Reader's note

Books B and D hold single names, the speculative-cohort monitor is built on estimate revisions, the Daily Cascade's event-reaction setup is one of Book C's three, and the library had no paper on the single most important recurring event in a single name's life. This one closes that gap, and it does so around one claim: **the print is not the event.** Roughly three-quarters of companies beat the consensus estimate, which means a beat carries almost no information. What carries information is the *reaction relative to what positioning implied should happen* — and that quantity is measurable in advance, from the options market, before the print.

The paper has six parts. Part I is the machine that sets expectations — who makes the consensus and why it is built to be beaten. Part II is what the options market already knows: the implied move, the event premium, and the positioning going in. Part III is the reaction — the four quadrants, the gap and the drift, and the setup this book is permitted to trade. **Part IV is the denominator and the multiple**: which earnings figure goes under the price, why the same stock carries five price-to-earnings ratios, when book value means anything, and a map of where each sector normally trades and how that map moves through a cycle — added on review because no paper in the library owned the practical vocabulary, and connecting to *Equities*, *Base Rates*, and *Tops and Bottoms* rather than repeating them. Part V is sector grammar, with the insurance sector as the worked example because it is the operator's own. Part VI is expression and wiring.

Figures are computed rather than sketched and live in the HTML edition.

---

# Part I — The Machine That Sets Expectations

## Chapter 1 — Who makes the consensus, and why it is beatable

The consensus estimate is not a forecast of what a company will earn. It is the mean of sell-side analysts' estimates, and those estimates converge on the company's own guidance, and the company's guidance is set to be exceeded. The loop is closed and everyone in it knows it: management guides conservatively, analysts anchor to guidance, the company beats, and the beat rate runs near three-quarters in an ordinary quarter — the *Base Rates* paper's figure.

Three consequences. **The beat-or-miss binary is nearly information-free** — a beat is the base case, and the surprise is a miss. **The real expectation is the whisper**, the buy-side's unpublished number that the stock already reflects, which is why a company can beat consensus and fall: it missed the whisper. **And the revision cycle carries more information than the level**, because analysts revise estimates in response to guidance and to each other, and the direction and breadth of revisions across a sector is a measurement of where expectations are moving before the prints arrive.

## Chapter 2 — The revision cycle as a signal

Estimate revisions are one of the oldest documented anomalies: names whose estimates are being revised upward tend to outperform for a period afterward, because the revision process is slow and analysts under-react. The system uses the cycle in three forms.

**Direction and breadth** — the share of analysts revising up versus down, across a name and across a sector — is the *Equities* paper's estimate-revision breadth measure at the index level, applied to names.

**Velocity** — the rate of revision, and its change — is the input the speculative-cohort monitor needs most. The second-derivative flag from Part 29: *revision velocity decelerating while price velocity accelerates* is the signature of a name where excellent results may no longer suffice, because the price has begun to assume an acceleration the estimates are not delivering.

*[Figure 1 — computed figure; rendered in the HTML edition]*

**The forward-only constraint.** Revision *history* is a vendor product, and the system declined to buy it. It logs its own consensus nightly, so the velocity series begins in September 2026 and the decomposition reads *insufficient history* until a quarter has passed. This paper exists partly so that when the first flags fire in December they are read with the framework rather than without it.

## Chapter 3 — Reading a print in ten minutes

What matters, in order:

1. **Guidance.** The next quarter's and the year's; the change versus prior guidance; the tone of the language around it. Guidance moves the stock more often than the print does, which is Chapter 7's subject.
2. **Revenue quality.** Organic versus acquired; volume versus price; the trajectory of the growth rate rather than its level.
3. **Margins.** Gross margin as the business's pricing power; operating margin as its discipline; the *direction* of each.
4. **The cash reconciliation.** Operating cash flow against reported earnings; free cash flow after capex. The gap between earnings and cash is the first place accounting flatters.
5. **The non-GAAP bridge.** What was added back to get from reported to adjusted, and whether the add-backs are recurring.

Three red flags, each with its reason. **A widening gap between GAAP and adjusted earnings** — the adjustments are becoming the business. **Receivables growing faster than revenue** — sales are being financed, or pulled forward. **A change in segment disclosure** — something is being hidden by reorganization, and the thing hidden is usually the thing that stopped growing.

---

# Part II — What the Options Market Already Knows

## Chapter 4 — The implied move

Before every print the options market states, in dollars, how large a move it expects. The at-the-money straddle expiring just after the event, as a percentage of the stock price, is the implied move; a refinement adjusts for skew. A name's implied move against its *own history of realized moves* is the actual signal — not the implied move alone.

*[Figure 2 — computed figure; rendered in the HTML edition]*

The figure is one name across sixteen quarters. Implied exceeded realized in eleven of them, matched the *Base Rates* finding that implied moves have on average slightly exceeded realized: **the seller of the event has positive expectancy on average and catastrophic tails, and the buyer has negative expectancy with the fat right tail.** Neither is a strategy. The signal is the ratio's departure from the name's own norm — an implied move well below the name's realized history is cheap optionality; well above is expensive.

## Chapter 5 — The event premium and the crush

The volatility term structure isolates what the event alone is worth.

*[Figure 3 — computed figure; rendered in the HTML edition]*

The front expiry containing the print carries implied volatility that builds for weeks; the next expiry barely moves. The difference is the *event premium* — the cleanest measure of how much drama is priced — and it collapses the morning after, the crush that *Options as Expression* describes from the buyer's side. Two readings for the book. A trader long a single option into the print must beat the priced move, not merely be right; and the morning after, optionality on the *reaction* is suddenly cheap, which is why the highest-expectancy expression is usually entered after the event.

## Chapter 6 — Positioning into the print

The *Positioning & Flows* mechanism groups, applied to one date. Open-interest buildup at particular strikes tells where the crowd expects the stock to land; call skew against put skew tells which direction is feared; borrow tightening in a shorted name says a squeeze is loaded; and for the cohort names, retail attention share says whether the print is a public event or a professional one. None of these is a forecast. Together they say what a *surprise* would have to look like — and that is the object Chapter 9 trades.

---

# Part III — The Reaction

## Chapter 7 — The four quadrants

Cross the print against the guidance and four cells emerge, with base-rate reactions that differ in sign and size.

*[Figure 7 — computed figure; rendered in the HTML edition]*

| Quadrant | Typical reaction | What it says |
|---|---|---|
| **Beat and raise** | Positive, moderate | The base case; already mostly priced |
| **Beat and lower** | **Negative** | The quarter was fine and the future is not — the market trades the future |
| **Miss and raise** | **Positive** | The quarter was noise and the trajectory is intact |
| **Miss and lower** | Negative, large | The rare genuine bad news |

The two off-diagonal cells carry the information. **Guidance beats the print** — a name that beats and lowers falls, and one that misses and raises rises, more often than the headline would predict. Read the table as the *Base Rates* discipline applied to a single event: the interquartile ranges are wide, the sign pattern is the durable part, and the quadrant is known within minutes of the release.

## Chapter 8 — The gap, the fade, and the drift

*[Figure 8 — computed figure; rendered in the HTML edition]*

Three phases, on different clocks. **The gap** — the overnight repricing, mostly complete at the open — is where the implied move is realized. **The fade** — the first one to three sessions — reverses a portion of the gap on average as the initial reaction is tested; the base rate for a gap holding through the third session is somewhat better than a coin flip in large caps and worse in small. **The drift** — the following one to three months — is the post-earnings-announcement drift documented since the 1960s: prices continue in the direction of the surprise as the information is slowly absorbed. It has weakened since the 2000s as capital chased it, and it persists, particularly in smaller and less-followed names.

The clock matters for expression. The gap is untradeable after the fact; the fade is a Book C session-structure setup; the drift is a Book B swing on a known catalyst with the crush already behind it.

## Chapter 9 — Reaction versus expectation: the tradeable object

The Daily Cascade's event-reaction setup, formalized.

Before the print, the system holds: the implied move, the skew's direction, the open-interest map, the borrow state, and the quadrant base rates. After the print, it holds the quadrant and the actual reaction. **The tradeable object is the difference between the reaction and the reaction that positioning implied** — a stock that beat and raised into a call-skewed, crowded-long positioning, and fell, is telling you the marginal buyer was already in; one that missed and lowered into put-skewed, shorted positioning, and rose, is telling you the marginal seller was exhausted.

That divergence is a Book C setup with a specific shape: defined-risk, in the direction of the *reaction* rather than the *news*, entered after the crush, sized at ordinary tier, with the invalidation at the reversal of the gap. It is the only earnings setup the Doctrine permits Book C to trade, and it is permitted because it trades what the market did rather than what the company said.

---

# Part IV — The Denominator and the Multiple

*The* Equities *paper owns the concept: price is earnings times a multiple, and the multiple is a duration instrument. It hands valuation to the* Foundations *paper, which treats the aggregate premium. Neither covers the practical vocabulary, and the earnings paper is where it belongs — the print determines the denominator, and the reaction is partly the market re-rating the multiple on what it learned.*

## Chapter 10 — Which earnings? The denominator problem

The same stock, the same day, carries five price-to-earnings ratios, and they can differ by half.

*[Figure 4 — computed figure; rendered in the HTML edition]*

| Denominator | What it is | When it misleads |
|---|---|---|
| **Trailing GAAP** | The last four reported quarters, as audited | Distorted by one-time items in either direction; the number most often quoted and least often meant |
| **Trailing adjusted** | The same, with management's exclusions | The exclusions are management's choice; a widening gap to GAAP is Chapter 3's red flag |
| **Forward** | The next four quarters' consensus | Consensus is managed (Chapter 1) and is a forecast; "cheap on forward earnings" assumes the forecast |
| **Normalized** | A multi-year average, smoothing the cycle | Meaningful for cyclicals; meaningless for a business whose earnings have structurally changed |
| **Cyclically adjusted** | Ten years of real earnings (the CAPE construction) | The aggregate-market tool; at the single-name level it assumes a stationarity most names lack |

**The rule: know which denominator a claim uses before agreeing or disagreeing with it.** Most valuation disagreements are two people using different denominators without knowing it. The register's `base_rate_cited` field, from Part 31, should carry the denominator whenever a multiple is cited in a thesis.

## Chapter 11 — Price-to-book, and when it means anything

Book value is what the balance sheet says the equity is worth, and price-to-book is meaningful exactly where the balance sheet *is* the business: banks, insurers, asset-heavy industrials, real estate. In those sectors the ratio has a natural anchor — one times book is what the assets are carried at — and the relationship between price-to-book and return on equity is the whole valuation: a bank earning 15% on tangible equity deserves a premium to book, one earning 6% deserves a discount, and the line through those points is the sector's valuation map.

It is meaningless where the assets are intangible and the equity has been consumed. The arithmetic: a company buying back shares above book value drives book value per share *down* while creating value for the remaining holders, and after enough of it the book value is small, zero, or negative — at which point the ratio inverts or ceases to exist. The largest buyback programs in the market belong to businesses with trivial or negative book values, and their price-to-book ratios say nothing at all.

## Chapter 12 — Enterprise-value multiples, and why they exist

Two identical businesses with different leverage have different price-to-earnings ratios and the same enterprise-value-to-EBITDA. Enterprise value adds net debt to the equity's market value, and EBITDA is earnings before the interest that debt generates — so the ratio is capital-structure neutral, which is why acquirers use it: they are buying the business, not the financing.

When each misleads: P/E flatters a leveraged company in a good year and punishes it in a bad one; EV/EBITDA ignores capital intensity entirely, which is why a capex-heavy business can look cheap on it while consuming every dollar it earns. **EV-to-sales** is the multiple for the unprofitable — and its specific trap is paying for revenue with no stated path to margin.

## Chapter 13 — Cash versus earnings

Free-cash-flow yield — operating cash flow less capital expenditure, over market value — against earnings yield is the comparison that catches what accounting hides. The live case is the capex-heavy cohort the *Equities* paper's Part V describes: reported earnings will be flattered relative to cash for years by the buildout's depreciation lag, and cash is the truth. **Shareholder yield** — dividends plus net buybacks over market value — is the cleanest single measure of what an owner actually receives, and it is the yield component the ten-year building blocks in *International Equities* use.

## Chapter 14 — Relative measures and their false precision

The PEG ratio — P/E over expected growth — is a rule of thumb that assumes a linearity between growth and multiple that does not exist, and it produces absurdities at both ends. Multiples against the company's own history and against peers are the honest relatives, and the *Base Rates* discipline governs both: **a multiple is a percentile against a distribution, not a number against a threshold.** "Twenty-two times is expensive" is a claim about a threshold; "twenty-two times is the 85th percentile of this name's ten-year range" is a measurement.

## Chapter 15 — The multiple map, and how it moves through the cycle

The chapter that connects the dots. Two figures and a table.

*[Figure 5 — computed figure; rendered in the HTML edition]*

**Where sectors normally trade, and why.** The ranges differ by a factor of three or more, and the reasons are structural rather than sentimental:

| Sector | Typical forward P/E | Typical P/B | The reason |
|---|---|---|---|
| Utilities | 13–19× | 1.5–2.5× | Regulated returns, bond-like, rate-sensitive |
| Banks | 9–14× | 0.8–1.8× (tangible) | Leverage, credit risk, ROE anchors the P/B |
| **Insurers** | 10–15× | 1.0–2.0× | **Book value is the business; the combined ratio and reserve adequacy set the multiple** |
| Energy | 8–16× | 1.0–2.5× | Commodity cyclicality; asset-based valuation |
| Industrials | 15–22× | 3–6× | Cyclical growth; capital discipline |
| Health care | 15–22× | 3–5× | Durable demand; patent cycles |
| Staples | 17–23× | 5–10× | Predictability; book value irrelevant (buybacks) |
| Semiconductors | 15–30× | 4–10× | Cyclical growth at high returns on capital |
| Software | 25–45× | 8–15× | Asset-light, high margins, recurring revenue; book meaningless |
| Mega-cap technology | 22–35× | 8–15× | Scale, network effects, the concentration premium |

*Source class: cited, approximate, ten-year ranges; the current readings marked in the figure are mid-2026 and drift.*

A bank at 1.2× book and a software company at 12× book are two different measurements, not one cheap and one expensive. The question is always *where in its own range*, and *why the range is what it is*.

**How the map moves through the cycle.** This is where the paper connects *Equities* Part IV (sector rotation), *Tops and Bottoms*, and the *Base Rates* distributions, and it contains the single most valuable line in the chapter:

*[Figure 6 — computed figure; rendered in the HTML edition]*

**Cyclical sectors look cheapest on trailing earnings at the top of the cycle and most expensive at the bottom**, because the earnings collapse faster than the price does. An energy or semiconductor name at eight times trailing at the peak is a trap — the E is about to halve; the same name at forty times at the trough is the buy — the E is about to recover. This inversion catches experienced traders repeatedly, and it is the reason Chapter 10's *normalized* denominator exists: for a cyclical, the trailing number is the least informative of the five.

The rest of the cycle overlay, compressed: **defensives' multiples expand in contractions** as capital seeks predictability, and contract in expansions as it leaves; **the aggregate market multiple is a rate instrument** over years and a sentiment instrument over months, per the *Equities* paper; and **the multiple gap between growth and value widens late in an expansion and closes in the bust**, which is the factor cycle from the same paper. Where the current market sits on each is a *Tops and Bottoms* reading, refreshed monthly, and this chapter defers to it.

---

# Part V — Sector Grammar

## Chapter 16 — What matters, by sector, and what multiple applies

The same headline means different things in different books. One paragraph per sector, written as *what a beat means here*.

**Semiconductors.** Bookings, backlog, and lead times matter more than the quarter; the capex cycle of the customers is the demand; **Taiwanese monthly revenue statements are the highest-frequency fundamental read on the AI capital cycle** and arrive before any quarterly print. Valued on forward earnings through the cycle, never on trailing — Chapter 15's inversion is most violent here.

**Software.** Net revenue retention, remaining performance obligations, and billings versus recognized revenue are the leading indicators; the print itself lags them. Valued on enterprise value to recurring revenue with the margin path as the argument; book value is meaningless.

**Banks.** Net interest income and its sensitivity to the curve; provisions as the credit-cycle tell; loan growth as the demand read. Valued on price to tangible book against return on tangible equity — the relationship between the two is the whole valuation, and a bank cheap on P/E with a low ROE is not cheap.

**Insurers — the operator's domain and the worked example.** The earnings of an insurer are two businesses: an underwriting business, measured by the **combined ratio** (losses plus expenses over premiums — below 100 is an underwriting profit), and an investment business, measured by the yield on the **float**. Book value is the business, so **price-to-book against return on equity** is the valuation map. The quality questions the multiple cannot see: **reserve development** — whether prior-year loss estimates are proving adequate or are being strengthened, which is the single most important line in a property-casualty print and the one most often buried; the duration and credit quality of the investment portfolio against the liabilities; and, for the reinsurance-exposed, the catastrophe load and its pricing cycle. A beat driven by favorable reserve development is a different animal from one driven by the underwriting margin, and a reader who cannot tell them apart will misprice every insurer print. *The operator will catch this paper's errors here before anywhere else, and that is the right place for its most detailed example to live.*

**Real estate.** Funds from operations, adjusted for maintenance capital, against the capitalization rate; leverage and the debt maturity ladder.

**Retail and consumer.** Comparable-store sales, inventory-to-sales, and gross margin as the pricing-power tell.

**Energy and industrials.** The cycle position; capital discipline versus growth spending; reserve-based and replacement-cost metrics where the assets are the business.

---

# Part VI — Expression and Wiring

## Chapter 17 — How to express an earnings view

The rules of *Options as Expression*, applied to a date:

- **Never a long single option into a print** unless the implied move is demonstrably cheap against the name's own realized history (Chapter 4). The crush is a base rate.
- **A vertical spread** is the crush-resistant pre-event expression — it sold some volatility too.
- **The post-event entry** — after the crush, on the reaction (Chapter 9) — is the highest-expectancy structure and the one Book C is built for.
- **A calendar** is the only legitimate pre-event structure for a *known date* with expected stillness before and movement after, and only then.
- **Book B's swing on the drift** (Chapter 8) is a defined-risk position in the direction of the surprise, entered in the sessions after the print, held on the sixty-day clock, with a time stop.

## Chapter 18 — The calendar and the blackout

Reporting season has a structure: the large banks open it, technology and industrials follow, retail closes it, and the sequence is a bellwether order — the early reporters set the tone for the sector. The *Positioning & Flows* master calendar carries the dates.

*[Figure 9 — computed figure; rendered in the HTML edition]*

The buyback blackout is the scheduled absence: companies suspend repurchases from roughly two weeks before the print until a day or two after, and in aggregate the market's largest net buyer withdraws for several weeks each quarter. The closing-auction module reads that absence directly; this paper's contribution is that it is *on the calendar in advance*, and a weak tape inside a blackout window is partly explained before it is diagnosed.

## Chapter 19 — What the system automates, and what it cannot

**Automatable, and scheduled with the events-ingest layer:** the earnings calendar with bellwether ordering; the implied move and its ratio to the name's realized history; the event premium from the term structure; the positioning snapshot into the print; the quadrant classification within minutes of the release; the reaction-versus-expectation computation; the drift measurement on the sixty-day clock; the nightly consensus log and the velocity series; and the blackout calendar.

**Not automatable, and left to the operator:** reading the call, judging the quality of guidance, choosing the right denominator for a multiple, and the sector grammar of Part V. The machine can say a beat-and-lower fell three percent into call-skewed positioning; only a reader can say whether the lowered guide was conservatism or a confession.

## Chapter 20 — What would change this paper

*The register's first fifty earnings-adjacent decisions*, cut by quadrant and by expression — the first evidence on whether the reaction-versus-expectation setup carries the edge the paper claims.

*The first four quarters of self-logged revision data*, at which point Chapter 2's velocity series has a history and the cohort monitor's flags have a base rate.

*A structural change in the guidance game* — regulation, or a shift in disclosure norms — that moved the beat rate materially from its long-run band.

---

## Appendix — The card

*The print is not the event.* Three-quarters beat; the whisper is the expectation; guidance beats the print; the off-diagonal quadrants carry the information.

*The options market prices the move.* Implied versus the name's own realized history is the signal; the event premium is front-expiry IV minus next; it collapses the morning after.

*The reaction is the object.* Trade the divergence between the reaction and what positioning implied, after the crush, defined-risk, in the direction of the reaction.

*Five P/Es, one stock.* Know the denominator. For a cyclical, trailing is the least informative — cheap at the peak, dear at the trough.

*Book value means something where the balance sheet is the business.* Banks, insurers, asset-heavy. Meaningless where buybacks have consumed the equity.

*A multiple is a percentile, not a threshold.* Against the name's own range, and the sector's, and the cycle.

*Insurers:* combined ratio, float yield, reserve development. A beat from reserve releases is not a beat from underwriting.
