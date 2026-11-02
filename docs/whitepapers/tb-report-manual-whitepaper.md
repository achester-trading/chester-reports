# The Top & Bottom Report Manual

## The Turn Detector: What It Measures, How It Was Calibrated, and What It May Say

**Companion white paper — chester-reports library**
**Series placement:** Companion **XXXI** — System shelf, beside the Monthly manual and the Reader's Guide, per the library guide, which is canonical for numerals; cross-references in this paper are by name
**Version:** 1.0 — 24 October 2026
**Status:** Draft 1, for the operator's review. The working manual of the Top & Bottom report. It describes the report as specified and as its engine was built on 3 September 2026, and says plainly where this repository holds no harness for it. Not investment advice.

---

### Reader's note

This is the manual for one report: the Top & Bottom report, the system's turn detector. The Monthly manual explains the Monthly's pillars; this paper does the same job for the report that asks whether the market is near a tradeable extreme, in either direction. It covers what the report is for, the composite and its eight categories, the ten triggers, the three overlays that fire independently of the composite, the gap-patch inputs, the calibration against thirteen historical episodes and what it found, the history of the weights, the false-bottom audit, the queue by which a new signal may join it, what the report may and may not say, and how to read an edition.

One fact governs the whole paper and it is stated first so that nothing later can be misread. **The report's engine is not built in this repository.** It was built on 3 September 2026 as a separate pipeline, a scoring engine at its eighth version, a calibration script and a report at its thirteenth, and its build log is the architecture document's Part 23. The repository the reports now run from holds the report's specification, two inert configuration files, its intake queue, its false-bottom ledger and a section of the Monthly that prints, in the report's place, that the harness is not built. The system's plan is to bring the report in not as a standalone edition but as a state variable, a verdict and a composite printed inside the Monthly and the Weekly. Until that is done, this manual is the specification such a build must satisfy, and every figure it quotes is a figure the separate engine produced, dated in Appendix B.

The history the report is calibrated on belongs to *Tops and Bottoms*, which studies every major U.S. equity top and bottom since 1970 and the corrections that did not become bears. This manual cites that paper for the history and never re-narrates it. Where the specification and the code in this repository differ, the code wins, and Appendix A lists each difference.

**Prerequisites.** *Tops and Bottoms*, for the episodes; the Operating Doctrine's Parts I to IV, for Book A's bands and the override this report holds; *Base Rates*, for the bear-rally base rate the Monthly prints beside the report's place; and *Evidence and Inference*, for why thirteen episodes are not thirteen observations.

---

## Part I — What the Report Is

### 1. The question it answers

The Top & Bottom report asks one question: *is the regime about to turn, up or down, and how many independent warning lights are on?* It works at the horizon of weeks to months. The Disruptive Themes report describes the era and moves too slowly to time anything; the Daily Cascade describes the session and moves too fast to see a regime. The Monthly says what is true of the economy and the market's plumbing. This report says whether that truth is priced, and whether the price has run far enough in one direction that the risk of a reversal is rising.

It calls both sides. A turn detector that only watched for tops would be a permanent bear, because tops are where the anxious reader looks; one that only watched for bottoms would be a permanent buyer of dips. The report's value is that it holds the two to the same discipline: a bottom signal must be earned by the same kind of evidence as a top signal, and the calibration in Part VI measures both.

Its cadence is monthly, refreshed on the first trading day after the month's consumer prices, the manufacturing survey and the fund-manager survey have landed. During stress the fast-moving inputs refresh weekly, and a release that crosses a threshold refreshes the read when it lands.

### 2. Where the report sits among the books

The report's one right in the Operating Doctrine is **Book A's override**. Book A holds a stance, expressed as exposure bands by regime, and moves only at the monthly session. Between sessions it does nothing unless the Top & Bottom report fires an override, in which case the stance moves to the override band at the next session, or, for a bottom signal, sooner. Within the band, the report's composite is one of the modifiers that set where the stance sits: toward the bottom of the band as top triggers accumulate, toward the top after a bottom signal.

Two of the Doctrine's regime rules name the report directly. In a Contraction regime, bottom-fishing is prohibited until the report gives a bottom signal, and shorts close on that signal. In a Crisis, the report's bottom signal is the only permission to add. Both rules wait on a harness that does not exist, so the Doctrine #2 pack drafts the override as dormant: kept in the Doctrine's text and marked dormant until the harness is built, with Book A moving only at the monthly session meanwhile.

The system's tier rule for reconciling reports places this one third of seven. The slower tier wins on direction and the faster on timing. The Disruptive Themes report caps sizing; the Monthly sets the month's baseline; the Top & Bottom composite is the primary structural read within the month, its verdict driving any escalation or relaxation of the baseline; an active overlay shifts the sizing read one row more cautious even if the composite has not moved; a trigger refines the verdict; the Alternative Asset read may raise caution and never lower it; and the Daily sets timing inside the cap. The rule is the operator's to apply. No code applies it.

### 3. What exists, and what does not

The report exists in three forms, and it matters which one a reader is looking at.

**The specification.** The master narrative's section on the report, the translation table's tier rule, the architecture document's Part 23, *Tops and Bottoms*' methodology chapter, and the signal-triage order's intake queue together describe what the report computes and how it is used. This manual is drawn from them.

**The engine built on 3 September.** A separate pipeline, outside this repository: a scoring engine at version 8, about seven hundred lines, that read the Monthly's former database, ran each indicator through its own scoring function, built the categories, computed the weighted composite, evaluated the triggers and the overlays, and wrote a small status file for the Daily Cascade and a full snapshot per edition. A calibration script ran the thirteen episodes through the same scoring functions. Its figures, the last of them dated 3 September, are what Part VI and Appendix B quote.

**What this repository holds.** Five things, and none of them computes the report:
- a section of the Monthly that reads the report's composite and verdict as a state variable from the store, finds none, and prints that the harness is not built, because a composite invented in its place would have no harness behind it and no way to be calibrated;
- the bear-rally base rate beside that section, from *Base Rates*' tables;
- an inert configuration of the false-bottom gate, read by no module, which a gate fails if any module names it;
- the intake queue for new overlay and trigger candidates, every entry a draft with no rights;
- the false-bottom audit's ledger and its episode file.

When the report is built here, it will be built as the system builds everything now: its inputs read point in time from the one store, its composite written to the store with its knowable time, its verdict read by the Monthly and the Weekly rather than mailed as an edition of its own, and its every threshold declared in configuration with its reason.

| Form | Where | Computes the report? |
|---|---|---|
| Specification | The master narrative, the translation table, the architecture's Part 23, *Tops and Bottoms*, the triage order's §2.6 | No; it describes it |
| The engine of 3 September | A separate pipeline, outside this repository | Yes, as of 3 September 2026 |
| This repository | The Monthly's not-built section; two inert configs; the intake queue; the false-bottom ledger | No |

---

## Part II — The Composite

### 4. Eight categories, one weighted score

The composite is a weighted sum of eight category scores. Each category gathers the indicators that bear on one kind of evidence:

- **Valuation**: the forward and trailing multiples, the cyclically adjusted multiple, the equity risk premium and price to book, across the main U.S. indices.
- **Momentum and trend**: where price sits against its moving averages, and the slope of those averages.
- **Breadth**: how many members are participating, the share above their long averages, and the equal-weighted index against the cap-weighted.
- **Sentiment and positioning**: the surveys, the fund-manager cash levels, a published bull-and-bear indicator from a large bank's research desk, and the futures positioning.
- **Leading indicators**: the series that have historically turned before the market, the high-yield acceleration score among them.
- **Macro and liquidity**: the policy path, the curve, net liquidity and the funding markets.
- **AI concentration**: the weight of the largest technology names and the semiconductor complex, carried informationally at zero weight.
- **Bank stress**: carried informationally at zero weight.

Roughly fifty indicators sit across these categories. Each is scored on a scale from −2 to +2 by a scoring function of its own, through five threshold bands: a reading in the band most associated with a top scores −2, one most associated with a bottom scores +2, and the middle band scores zero. The bands are the report's Appendix C, its threshold reference, so that a reader can see not only where an indicator sits but what level would move it into the next band.

The two zero-weight categories deserve a sentence. They are printed because their readings matter to how the composite should be read (a top built on the concentration of a handful of names is a different object from a broad one), but they are kept out of the score because the calibration had no episode against which to weight them. A category the evidence cannot weight is shown, not counted.

### 5. From score to verdict

The weighted composite maps to one of five verdicts: **TOP SIGNAL**, **OVEREXTENDED**, **NEUTRAL**, **CONSTRUCTIVE** and **BOTTOM SIGNAL**. The verdict is the report's headline and the read Book A's override and its in-band modifier take. A composite deep in the negative reads as overextended or worse; one deep in the positive as constructive or better.

The verdict is a reading of risk, not an order. *Disruptive Themes* puts the same discipline in five words for its own composite: bands are regimes, not orders. TOP SIGNAL does not say sell. It says the left tail is fat enough that position sizing, hedge budgets and liquidity should assume it.

### 6. Reading the composite honestly

Three properties of the composite should shape how much weight a reader gives it.

It is **episode-calibrated, not backtested**. Its weights were set by running thirteen episodes through the scoring functions and asking which classifications came out right (Part VI). That is a test of whether the composite would have recognised the turns it was designed around, not a measurement of how often it fires falsely in ordinary time. The continuous backtest that would measure the false-positive rate was specified and deferred.

It is **an average**, and an average is mathematically prone to missing a turn whose cause sits in one category while the others look calm. That is the reason the overlays exist (Part IV).

It **moves slowly by construction**. Fifty indicators with monthly inputs do not swing on a week's news, which is the point: a turn detector that turned every week would be a mood ring. It also means that a sharp turn whose evidence arrives in one week, as March 2020's did, will be read late.

| Composite property | What it means for the reader |
|---|---|
| Episode-calibrated | It recognises the turns it was built on; its false-fire rate is unmeasured |
| An average | It can miss a turn driven by one category; the overlays are the guard |
| Slow | It will not chase a week; it will read a sudden turn late |
| Two zero-weight categories | Printed for context, never counted |

---

## Part III — The Ten Triggers

### 7. What a trigger is

Where the composite averages, a trigger watches one thing. Each of the ten has a threshold that marks a top-side warning and an inverse threshold that arms a bottom signal, and each reads in three states: **CLEAR**, **APPROACHING** and **TRIGGERED**. The triggers refine the composite rather than replace it: an approaching trigger adds caution, a triggered one confirms the composite's reading, and a new fire between monthly refreshes shifts the read one row more cautious under the tier rule.

The set grew from six to ten in the report's third live version. The ten, in the order the specification lists them:

1. **A mega-cap technology IPO filing** (the first of two named filings): read from the SEC's filings monitor, as a completion signal of the kind a speculative cycle's late stage produces.
2. **A second mega-cap AI IPO filing**: the same mechanism, a second instance.
3. **Consumer prices breaching a stated rate**, approaching or exceeding it: the level at which the central bank is forced back toward tightening.
4. **The high-yield spread crossing a stated level**: credit's confirmation of what equities may be ignoring.
5. **The share of index members above their 200-day average falling below half**, while the index is near its highs: breadth breaking under the surface.
6. **The bank research desk's bull-and-bear indicator above its sell threshold**: a published contrarian signal armed.
7. **The 2-year to 10-year curve un-inverting** after a period of inversion: recession has typically followed the un-inversion rather than the inversion.
8. **The curve re-inverting**, on either the three-month or the two-year leg: a second-chance recession signal.
9. **Credit-spread acceleration**: the thirty-day rate of widening, because the rate of change leads the level at turns.
10. **Private-credit bifurcation**: private credit stressed while public spreads stay tight, a transmission channel that did not exist before 2020.

Two of the ten (the IPO filings) are events, not series, and two (the bank indicator and private-credit bifurcation) depend on sources outside the public, keyless set the system now prefers. The first engine read the bank's indicator from a public mirror with a manual override that always won, and the filings from the SEC's index. When the report is built here, each of the four must pass the sources rule of 16 October, or become a listed gap; a trigger the system cannot read is printed as not read, never assumed clear.

### 8. The roll-up, and what is not known

The triggers roll up into one status, **CLEAR**, **WATCH** or **ALERT**. With six triggers the tiers were zero or one fired, two, and three or more. Whether the tiers were scaled for ten, or held, is recorded in the specification as not confirmed against the engine. This manual therefore states no roll-up threshold for the ten-trigger set. A build in this repository must declare one in configuration, with its reason, and the Doctrine monthly must ratify it.

| # | Trigger | Kind | Top side | Bottom side |
|---|---|---|---|---|
| 1 | Mega-cap tech IPO filing | Event | Filed | Withdrawn or broken issue |
| 2 | Second mega-cap AI IPO filing | Event | Filed | As 1 |
| 3 | Consumer prices | Release | Breaching the stated rate | Falling back through it |
| 4 | High-yield spread | Daily | Crossing the stated level | Peaking and tightening |
| 5 | Breadth above the 200-day | Daily | Below half at highs | Recovering from a washout |
| 6 | Bank bull-and-bear indicator | Weekly, published | Above its sell line | Below its buy line |
| 7 | Curve un-inversion | Daily | After an inversion | — |
| 8 | Curve re-inversion | Daily | Flips back | — |
| 9 | Credit-spread acceleration | Daily | Fast widening | Fast tightening |
| 10 | Private-credit bifurcation | Monthly | Private stressed, public tight | Converging |

The thresholds are in Appendix B, as they stood on 3 September 2026.

---

## Part IV — The Three Overlays

### 9. Why the overlays exist

The calibration (Part VI) found that no weighting of the composite could catch every top, because tops are idiosyncratic by cause. One top is a valuation top, another a credit top, another a plumbing top, and an average that weights all categories will under-read the one that matters in a given episode. Bottoms rhyme; tops do not. The architectural answer was three overlays that fire **independently of the composite**, each designed for one documented failure mode, each a count of its own conditions, and each active when **three or more** of its conditions hold.

### 10. Concentration and Complacency

The first overlay is built for the valuation top that a composite averages away, the shape of 2000 and of 2022. Its five conditions are a high forward multiple, a high cyclically adjusted multiple, a thin equity risk premium, a high share of the index in its ten largest members, and a low implied volatility. When three of the five hold, it is active.

Its record includes a known false fire, and the manual says so because it teaches how to read the overlay. In August 2024 the overlay fired and no crash followed; the market was expensive and concentrated, and stayed so. The overlay was right about the condition and silent about the timing, which is what it is: **a condition, not a timing signal**. It says the market's shape resembles the shapes that preceded valuation tops. It does not say when the shape breaks.

### 11. High-Yield Spread Acceleration

The second overlay is built for the credit top whose spread *level* still looks tight, the shape of 2007. Its four conditions are the high-yield spread's rise off its trailing twelve-month low, its thirty-day widening, investment grade's thirty-day widening, and investment grade's level. The insight it encodes is that at a credit top the level lies and the rate of change tells the truth: spreads that are still historically tight but have risen half again off their low are the warning.

With it came a new leading indicator in the composite, the high-yield acceleration score, deliberately **non-monotonic**: quiet when spreads sit near their low, early as they lift, most negative (the top signal) at a rise of half to double off the low, and positive again once spreads have fully blown out. A fully blown-out spread is fuel for a bottom, not a top risk, so the score turns. A monotonic score would have called the bottom of 2009 a top.

### 12. Liquidity and Funding Stress

The third overlay is built for plumbing stress before it becomes credit stress, the shapes of the 2019 repo spike and of funding strains since. Its five conditions are net liquidity's year-on-year contraction accelerating, bank reserves below a stated level, the secured overnight rate above the reserve rate for five days, the reverse repo facility drained below a stated level, and a large swing in the Treasury's cash balance.

This overlay's inputs are the same series as the Monthly's funding tripwires and the first movers of one of the Twenty-Five's tail scenarios. The build log recorded that the system must not keep two copies of them: build once in the store and have the report read from it. That rule now holds by construction, since the store is the one place any figure lives (the Reader's Guide, Part II). The overlay is also the most contested in the intake queue (Part VIII): three separate deleveraging mechanisms have been proposed for it.

| Overlay | Built for | Conditions (active at 3 or more) | How to read it |
|---|---|---|---|
| Concentration and Complacency | The valuation top (2000, 2022) | Forward multiple, cyclical multiple, risk premium, top-10 share, implied volatility | A condition, not a timing signal; known false fire August 2024 |
| High-Yield Spread Acceleration | The credit top with tight levels (2007) | HY off its low, 30-day HY and IG widening, IG level | The rate of change over the level; the score turns when spreads blow out |
| Liquidity and Funding Stress | Plumbing before credit (2019, 2020) | Net liquidity, reserves, SOFR against the reserve rate, the repo facility, the Treasury's cash | The same series as the Monthly's funding tripwires; read once from the store |

---

## Part V — The Gap-Patch

### 13. Why a patch, and what it patches

The report's indicator set is built on the U.S. equity market since 1970, because that is where *Tops and Bottoms* has data. That sample has a known blind spot: it contains few of the financial crises that the long historical record holds in abundance, and almost none of their precursors. The report therefore carries a **gap-patch**: inputs drawn from Reinhart and Rogoff's study of eight centuries of financial crises, *This Time Is Different* (2009), whose finding is that crises are preceded by the same small set of conditions across countries and centuries: a run-up in real house prices, a surge in private credit and in capital inflows, and a rise in debt that the boom makes look affordable.

The patch is the report's admission that its own calibration sample is too narrow to see a banking crisis coming, and its way of borrowing a wider sample's precursors without pretending the U.S. episodes contain them.

### 14. What the repository records of it

The repository records the patch's existence and one of its inputs, and no more. It records that the report carries the Reinhart–Rogoff inputs. It records that a real house-price input leads the patch: the signal-triage order for Batch 14 asks for the real Case–Shiller level, as a percentile of its history from 1890, to print beside the Reinhart–Rogoff input, and the housing ledger of 17 October names a house-price-decline watch as the flag that would lead that input. The real home-price percentile is now stored and printed in the Monthly's slow layers on its own line, because the input it was to sit beside is the report's and is not in this repository.

The specification does not record the patch's full input list, its scoring or its weight in the composite. This manual does not reconstruct them. A build of the report here must specify the patch from the published study, with each input's source checked under the sources rule, and the Doctrine monthly must ratify it.

---

## Part VI — Calibration and What It Found

### 15. Thirteen episodes, whole

The calibration ran thirteen historical episodes through the report's own scoring functions: the turns *Tops and Bottoms* studies, classified as tops, bottoms and controls. Each episode was keyed by hand at its turning date and scored once. That is **episode-level classification**, not a continuous backtest: the question each run answers is whether the composite, on the day of a known turn, would have read the turn correctly.

Episode-level calibration has a virtue the library returns to more than once. Thirteen episodes examined whole teach more about how turns look than five thousand daily points would, because a turn is an event with a shape, and the shape is lost when it is chopped into days. It also has the limit *Evidence and Inference* insists on: thirteen episodes are not thirteen independent observations, and a scoring engine with about fifty indicators, eight weights, five bands per indicator, ten triggers and three overlays has hundreds of free parameters against them. The calibration can show that a weighting recognises its own sample. It cannot show that the weighting generalises.

### 16. The result: stronger at bottoms than at tops

Under the original weights, the composite classified **none of the three tops**, **four of the six bottoms** and **all four controls** correctly. Read plainly, it recognised bottoms and quiet periods and missed tops.

The finding that matters most is the asymmetry, and it is the report's main lesson. **Bottoms rhyme; tops do not.** A bottom is a washout: spreads blown out, breadth destroyed, sentiment at its worst, positioning flushed, and a composite built from those readings sees it. A top has a cause, and the cause differs by episode: valuation in one, credit in another, policy in a third. A composite that averages all categories under-reads whichever one carries the episode. *Tops and Bottoms* reaches the same conclusion from the history alone, in its synthesis chapter: tops are idiosyncratic, bottoms rhyme.

### 17. The 2007 top: structurally uncatchable

The calibration's sharpest single finding concerns 2007. A sweep of the composite's weights showed that **no reweighting of the existing indicator set catches a 2007-type top**. In 2007 the cyclically adjusted multiple was elevated but nowhere near extreme, implied volatility was low, breadth was acceptable, and spreads were tight in level. The fragility sat in leverage and in the structure of funding, which the composite's indicators did not measure. The top was not late in the indicators; it was absent from them.

The report's response was not to bend the weights until 2007 appeared. It was to add the High-Yield Spread Acceleration overlay (Part IV), built to read a credit top in the rate of change rather than the level, and to record the finding as a rule the Systematic Book paper generalises: *know which turns the system can see, and which it cannot.* A system that claims to catch every top has fitted its sample.

### 18. The reweighting history

The weights have one recorded revision, version 8 of the scoring engine on 3 September 2026. It moved weight from Macro and Liquidity to Valuation, by five points, leaving the others unchanged and the sum at one. On the calibration set the change moved the 2000 top into OVEREXTENDED, so one of the three missed tops became a correct classification. On the live read it moved the composite deeper into OVEREXTENDED (Appendix B). The weight sweep that produced it is also what proved the 2007 finding: rebalancing alone could not catch the 2007 or the 2022 shape, which is why the overlays were made independent of the composite rather than folded into it.

The weights as they now stand are in Part II's table of categories; their values are in Appendix B with their date.

### 19. What calibration was deferred

Two measurements were specified and not built. The first is the **continuous backtest harness**, which would replay the scoring engine over the daily history and measure each overlay's false-positive rate, the figure that would make the overlays' thresholds honest. The second is the **quarterly calibration** the master narrative describes: every ninety days, the live engine replayed against the prior eight quarters, reporting the composite's track, the weights' sensitivity to a five-point shift, each overlay's false-positive and false-negative rate, and whether the triggers' thresholds suit the current volatility regime. Neither exists. Until one does, the report's thresholds are set by the episodes and by judgment, and the manual says so.

| Calibration finding | What it means |
|---|---|
| Tops 0 of 3, bottoms 4 of 6, controls 4 of 4 (original weights) | The composite recognised washouts and quiet, and missed tops |
| Bottoms rhyme, tops do not | A single average cannot weight every top's cause |
| 2007 uncatchable by reweighting | The fragility was outside the indicator set; the HY acceleration overlay answers it |
| Version 8: Valuation up, Macro down, five points | The 2000 top read correctly in calibration |
| No continuous backtest | The overlays' false-fire rates are unmeasured |

---

## Part VII — The False-Bottom Audit

### 20. The question

The bottom side was calibrated on real bottoms. But a bear market contains false ones: rallies of a tenth or more that look like the end and are followed by a lower low. Five of them came inside the 1929–32 decline alone. A bottom signal that fires on every such rally would be worse than none, because it would hand Book A permission to add at exactly the moments a bear punishes most. The signal-triage register's SR-8 adopted a false-bottom audit to answer one question: of the confirmations a reader might use to tell a true bottom from a false one, which actually discriminate?

### 21. The ledger and its verdict

The audit's first edition was run on 18 October 2026 from public sources, labelled as a laptop edition that a re-run against the box's store will supersede. It replayed the S&P 500 through four bears (1973–74, 2000–02, 2007–09 and 2022), finding a candidate bottom wherever a new bear low was followed by a 10% rally before a lower close, and **found sixteen candidates: twelve false bottoms and four true**. It then asked of each confirmation element whether it fired at the true bottoms and not at the false ones, under a rule written before the run: an element discriminates if it fires at three-quarters or more of at least two testable true bottoms and at no more than a third of at least three testable false ones. The audit would pass if two or more elements discriminated.

**It failed.** One element discriminated: breadth, read as the equal-weighted S&P 500 against the cap-weighted, higher at the read than at the trough. It fired at both testable true bottoms and two of six false ones. Industry breadth, sector breadth, new leadership, credit tightening, the volatility curve in contango, a successful retest, spent margin and the time since the prior high did not discriminate. Short-interest fuel could not be tested, because the free history begins at the end of 2017. Leveraged-fund assets are a listed gap.

### 22. What the failure leaves

The register's gate reads: once the report's top side has fired and price is below a falling 200-day average, the bottom threshold rises, and two of the confirmation set are required before Book A re-enters; rallies in that state are Book C material. The audit found one element, not two. So the gate's specification stands as written, with its gap, in an inert configuration file that records the one discriminating element with its parameters, the dropped elements with none, and the number of confirmations required left empty, because that number is the operator's ruling. Book A's rule A-2 changes nothing until then.

The Doctrine #2 pack carries the consequence: adopt the false-bottom rule's first and third sentences as a Doctrine principle (once the top side has fired and price is below a falling average, the bottom threshold rises; rallies in that state are Book C's), and hold the second sentence, the re-entry on two confirmations, until a second element discriminates. Breadth alone prints beside the composite, with no right.

| Element | Word | Why |
|---|---|---|
| Equal-weight against cap-weight breadth | Discriminates | Both true bottoms, two of six false |
| Industry and sector breadth; new leadership; credit tightening; volatility contango; retest; spent margin; time since the high | Does not discriminate | Fired as often at false bottoms |
| Short-interest fuel | Not testable | Free history from December 2017 |
| Leveraged-fund assets | Listed gap | No admissible source |

---

## Part VIII — How a Signal Joins the Report

### 23. One candidate at a time

The report is the system's most tempting place to add a signal, because every interesting chart about markets claims to show a top or a bottom. The signal-triage order of 25 September answers that temptation with a queue. A candidate for an overlay or a trigger enters **one at a time**: the next enters a champion-and-challenger test only after the previous is adopted or rejected, so that an overlay never counts the same mechanism twice. Before the test, the candidate needs **a pre-registered calibration ledger**: a pass rule written before the run, a verdict, and the right the verdict would grant, stated and not granted. And the queue applies **once the report is built**; until then every entry is a draft with no rights, and the queue file says so in its header.

The queue's order, as the order rules it:
- **Liquidity and Funding Stress:** the yen-carry unwind (SR-2) first, then auction stress (SR-22), then the absorbers' fragility (SR-26 and SR-27). The three are deleveraging mechanisms, which is exactly the double-count the one-at-a-time rule exists to prevent.
- **High-Yield Spread Acceleration:** the ring-three high-yield spreads of the AI build-out's debt (SR-16), after SR-16's own gate.
- **The bottom side:** the false-bottom gate (SR-8) first, because it raises the threshold, then the consumer-credit bull trigger (SR-5), so that the new trigger is tested against the raised threshold rather than the old one.
- **A rate-repricing tag:** the market-state object's rates driver was to replace any tag of the report's own. The driver was withdrawn after failing its gate twice, so this line waits.
- **Concentration and Complacency:** the growth-against-value style flag (SR-1) only if it adds information beyond the top-ten weight; the share of members with a negative beta to the index (SR-19); and, filed since, the concentration twin from the Guide to the Markets batch (GTM-3), which asks whether the top ten's share of the index is earned by its share of earnings.

The order among the top-side candidates filed since (GTM-3 and three items of Batch 6) is the operator's ruling.

### 24. How a triage item that names the report enters it

Every proposal in the signal-triage register declares its home and its rights. An item whose home names the report enters by one of three paths, and only these:
- **As an intake candidate**, through the queue above, with its own calibration ledger. This is the only path to a weight, a threshold or a trigger.
- **As a report-only exhibit**, printed where the report's place prints (the Monthly's slow layers) or beside it, with no right. The GTM batch's concentration twin is built this way: a standing exhibit, its queue entry filed as a draft.
- **As a refusal of rights.** Many items record that they enter neither the report nor any composite. An investor bond allocation line, a style spread, a regional allocation line, a cross-asset valuation strip and an AI funding panel were each adopted with "no T&B rights" written into the ruling, because a signal adopted as a reading is not thereby a turn signal.

The register's order is also explicit that nothing from the intake can enter the report's composite while the report is unbuilt: every item in it is report-only class, unable to raise a blocked decision, write a packet or enter a composite.

| Path | What it grants | Example |
|---|---|---|
| Intake candidate | A weight, threshold or trigger, after a ledger and a champion/challenger test | SR-2 for the Liquidity overlay |
| Report-only exhibit | A printed line, no right | GTM-3's concentration twin |
| No rights | Nothing; a reading elsewhere | Investor bond allocation, "No T&B rights" |

---

## Part IX — What the Report May Say, and How to Read It

### 25. What it may and may not say

The report inherits every rule the system holds its prose to (the Reader's Guide, Part V), and four of its own follow from what it is.

**It speaks in conditions, never in dates.** A verdict of OVEREXTENDED or an active overlay is a statement that the market's shape resembles shapes that preceded turns. The report may never say when a turn will come. The August 2024 false fire is the standing reminder that a correct condition can persist for a long time.

**It names what it cannot see.** The 2007 finding is a sentence the report carries: some tops are outside its indicator set. A report that implied it would catch every top would be overclaiming its own calibration.

**Its odds are base rates.** A probability may print only as a ledgered base rate with its sample size, "the base rate for … is X% (n = …)". The bear-rally base rate beside the report's place is the model: how often a counter-trend rally of a given size occurs inside a bear, with the count.

**It recommends nothing.** The report reads; Book A's override acts, at a session, by the operator's hand. No edition may name an instrument to buy or sell, and the register refuses at write time any recommendation touching a restricted security.

### 26. How to read an edition

When the report prints, read it in this order.

**First, the verdict and its direction.** Where does the composite sit among the five, and has it moved since the last edition? A move of one band is information; a reading that has sat in one band for months is a condition.

**Second, the overlays, independently of the verdict.** An active overlay matters even when the composite is calm, because the overlays exist for the turns the composite misses. Note which overlay, because each names a different kind of top.

**Third, the triggers.** How many are approaching, how many fired, and which. A fired trigger in a calm composite is a warning the average has not yet absorbed.

**Fourth, what the report says it cannot see.** The not-read triggers, the inputs whose sources are refused or unbuilt, and the categories carried at zero weight.

**Last, the base rate.** Before reading any of it as a forecast, read what usually happens: how often a reading like this one has been followed by a turn, and how often by nothing.

Until the report is built here, the Monthly's slow layers print its place: the harness is not built, and the bear-rally base rate stands beside it. That line is the report's honest edition today.

### 27. What a build in this repository must satisfy

The report's specification was written for a pipeline of its own, and the system it would now join holds every report to rules that pipeline did not have to meet. A build here is therefore not a port of the September engine. It must satisfy, at least, these eight conditions, each of which the system's other reports already meet.

**One store, point in time.** Every input is read from the observation store as of the edition's cutoff, so that an edition replayed for a past date sees only what was knowable then. The engine of September read a database it shared with the Monthly; the store is now the only place any figure lives.

**One composite, written once.** The composite and the verdict are written to the store as state variables with their knowable time, by the one writer, and every report that prints them reads them. No report computes its own, for the same reason no report computes its own regime.

**Declared thresholds.** Every band, trigger threshold, overlay condition and roll-up tier lives in configuration with a sentence of reason, under the same ratification path as any rule. The values in Appendix B are the starting point, not a ruling.

**The sources rule.** Each input passes the rule of 16 October: public, keyless and easy to read, or a listed gap. The bank's bull-and-bear indicator, the private-credit spread and the IPO filings are the inputs most likely to fail it, and a failed input prints as not read.

**A calibration ledger.** The thirteen-episode calibration is re-run against the store, with its pass rule written before the run, and a continuous backtest measures each overlay's false-fire rate. Until both exist, the report prints its verdict beside the statement that it is episode-calibrated only.

**Report-only first.** The verdict prints in the Monthly and the Weekly before it holds any right. Book A's override is a separate ruling, taken at a sitting once the report has run for a stated number of editions.

**The intake queue.** Every candidate in Part VIII enters by the queue's rule, one at a time, after its own ledger, and the false-bottom gate precedes any new bottom trigger.

**The audits.** The report's prose passes every audit the stacked reports pass: no figure outside its payload, no verdict word without its computed state, no odds except a ledgered base rate, no motive and no recommendation.

| Read | Ask |
|---|---|
| Verdict | Which of the five, and did it move? |
| Overlays | Is any active, whatever the verdict says? |
| Triggers | How many approaching or fired, and which? |
| Blind spots | What is not read, refused or at zero weight? |
| Base rate | How often has a reading like this been followed by nothing? |

---

## Appendix A — Where the Specification and the Code Differ

*The code wins. Each row is a place where this manual follows what the repository holds rather than what a specification document says.*

| # | The specification says | The code says |
|---|---|---|
| 1 | The report is a full pipeline, a view over the Monthly's database, writing a status file the Daily Cascade reads (master narrative) | No harness exists in this repository. The Monthly reads `top_bottom.composite` and `top_bottom.verdict` as state variables, finds none, and prints that the harness is not built (`monthly_macro/payload.py`, `top_bottom_block`) |
| 2 | The report runs monthly, weekly in stress, and on threshold-touching releases | No timer, unit or module runs it |
| 3 | The quarterly calibration replays the engine every ninety days | Not built; nor is the continuous backtest harness, which the build log deferred |
| 4 | The false-bottom gate wires Book A rule A-2 | `config/tb_false_bottom_gate.yaml` is inert, read by no module, and a gate fails if any module names it |
| 5 | The intake queue admits candidates in order | `config/tb_intake_queue.yaml` holds one entry (GTM-3), status draft, rights none; no module reads it to weight or score; a gate holds every entry to draft and diffs the overlay's declared inputs |
| 6 | The Reinhart–Rogoff input prints beside the real home-price percentile | The input is not in this repository; the real home-price percentile prints on its own line in the slow layers |
| 7 | The ten triggers' roll-up tiers | Recorded as unconfirmed against the engine; no value is stated here |
| 8 | The Liquidity overlay's inputs are fetched by the report's own plumbing | In this system every input lives once, in the store; the report, when built, reads them from it |
| 9 | The rate-repricing tag is replaced by the rates driver | The driver was withdrawn on 30 September after failing its gate twice; the line waits |
| 10 | Brief for this manual: "written from the code and its config (find the T&B package by name)" | No T&B package exists; the manual is written from the specification and the build log, and the configs and ledger this repository holds |

---

## Appendix B — Dated: The Report's Recorded Values (as of 24 October 2026)

*Every value here is as the separate engine recorded it, with its date and source. None is computed by this repository, and none is a current reading. The report's next edition, when built, supersedes the lot.*

### B.1 The category weights (scoring engine version 8, 3 September 2026)

Valuation 17%; Momentum and trend 12%; Breadth 15%; Sentiment and positioning 22%; Leading indicators 10%; Macro and liquidity 24%; AI concentration 0% (informational); Bank stress 0% (informational). Version 8 moved Valuation from 12% and Macro and liquidity from 29%. *Source: the architecture document, Part 23; the master narrative, §3.*

### B.2 The calibration (3 September 2026)

Thirteen hand-keyed episodes. Original weights: tops 0 of 3, bottoms 4 of 6, controls 4 of 4. Version 8 moved the 2000 top to OVEREXTENDED at −0.52 in calibration. *Source: the architecture document, Part 23.*

### B.3 The composite (3 September 2026)

−0.60, OVEREXTENDED, from −0.51 before version 8. The edition's stated synthesis: today is 2000's valuation plus 2007's policy plus 2022's concentration, with no visible trigger. *Source: the architecture document, Part 23.*

### B.4 The overlays' thresholds and states (3 September 2026)

- **Concentration and Complacency:** forward P/E at or above 20; CAPE at or above 30; equity risk premium at or below 1.5%; top-10 weight at or above 25%; VIX at or below 18. State: 5 of 5, ACTIVE (the August 2024 false fire noted).
- **High-Yield Spread Acceleration:** high yield at or above +50% off its 12-month low; 30-day high-yield widening of 40 bp or more; 30-day investment-grade widening of 15 bp or more; investment grade at or above 110 bp. State: 0 of 4, CLEAR (high yield about +8% off its low).
- **Liquidity and Funding Stress:** net liquidity's year-on-year at or below −10%, accelerating; reserves at or below $3.15 trillion; SOFR less the reserve rate at or above +5 bp for 5 days; the reverse repo facility at or below $200 billion; the Treasury's cash swinging $200 billion or more. State: 2 of 5, CLEAR (reserves at $3.05 trillion and the facility at $130 billion firing).

*Source: the architecture document, Part 23. The master narrative records the same three states as of 23 May 2026: ACTIVE 5/5, CLEAR 0/4, CLEAR 2/5.*

### B.5 The high-yield acceleration score's bands (3 September 2026)

+1 quiet; 0 early; −2 at +50% to +100% off the trailing 12-month low (the top signal); +1 fully blown out. *Source: the architecture document, Part 23.*

### B.6 The triggers (as specified, May 2026)

The trigger set as the master narrative lists it: the two IPO filings (an S-1 filed); consumer prices breaching 4%; high-yield OAS above 350 bp; the share of S&P 500 members above their 200-day below 50%; the bank's bull-and-bear indicator above 8.0; 2s10s un-inversion; 3m10y or 2s10s re-inversion; 30-day credit-spread acceleration; private credit stressed against public spreads tight. The roll-up tiers for ten triggers are unconfirmed. *Source: the master narrative, §3, "The Ten Triggers".*

### B.7 The false-bottom audit (18 October 2026)

Laptop first edition, public sources; S&P 500 as of 16 October 2026. Sixteen candidates (twelve false, four true) across 1973–74, 2000–02, 2007–09 and 2022. FAIL: one element discriminates (equal-weight against cap-weight breadth). *Source: `docs/ledgers/false-bottom-audit-2026.md` and its episode file.*

---

## Appendix C — Assumptions and Falsifiers

**Mechanisms this manual assumes.**
1. *Tops are idiosyncratic by cause; bottoms rhyme.* Falsified if a single weighting of the composite, tested on episodes outside the thirteen, classifies tops as reliably as bottoms.
2. *Each overlay catches one top type the composite misses.* Falsified by a continuous backtest that finds an overlay's false-fire rate no better than its base rate, or that the composite alone caught the overlay's episodes.
3. *The level of a credit spread lies at a credit top; its rate of change does not.* Falsified by a credit top preceded by no acceleration off the spread's low.
4. *A false bottom can be told from a true one by confirmation.* Already falsified for all but one element on four bears (Part VII); the box re-run is the next test.

**Regularities with dates.** The calibration's counts are as of 3 September 2026, on thirteen hand-keyed episodes; the false-bottom audit's as of 16 October 2026, on four bears. Both are first editions.

**Standing-register items touching this report.** Passive ownership and concentration (the Concentration overlay's top-ten input); dealer balance-sheet capacity and central-bank balance sheets (the Liquidity overlay); the growth of private markets (the private-credit trigger).

**Dated figures in this paper.** None in the body; every value is in Appendix B with its date and source.
