# Monthly Regime & Allocation — Style and Coverage Specification

**For:** `monthly_macro/run.py` via `monthly_macro/narrative.py` · **Rule:** long-form permitted, shipped only if the numeral audit passes. Every number must exist in the payload, at the precision the payload carries it. No recommendation and no stance — the report is named for allocation and the register's rules decide it.

## What changed, and why this template is short

The old Monthly carried ten `*[NARRATIVE PLACEHOLDER — 4-paragraph synthesis: regime, data story, cross-pillar, matrix implication]*` markers, one per pillar, each replaced by its own API call. Ten calls asked a model to **characterise the regime from the pillars**, once per pillar, with no shared state and no obligation to agree with each other or with the close report that had already published a regime.

The regime now comes from the market-state object. The pillars are **inputs** to three dials with declared weights in `config/pillars.yaml`, printed beneath the dial each one feeds. There is one paragraph over one payload, and the placeholder is deleted rather than repointed: a marker that asked for a regime is a marker with nowhere left to point.

## Coverage, in this order

1. **The regime and what changed** — the three dials, what each read at the previous Monthly, and the dimensions that moved. **You do not infer a regime from the pillar series.** Say which pillars a reader should look at *because* of what a dial did; the weights say how much each should move a view.
2. **The scenario weights with their Brier scores** — and what an unresolved weight permits you to say about accuracy, which is nothing. A weight printed without its score is a forecast nobody has marked.
3. **Top & Bottom** — the verdict and composite if the harness has published one. Any top-side language carries the **bear-rally base rate** from `baserate.drawdown_by_depth`: a short campaign inside a −20% decline faces three to five counter-trend rallies and each will look like the turn. Claims are cited **by id**.
4. **Alternative assets** — the families with data and the families without, named. `real_assets` is empty by construction until a REIT or infrastructure series exists.
5. **The register's month** — grades, decisions opened and closed, rule breaks, and the expectancy **interval read before the point**. An interval that spans zero permits nothing about the sign.
6. **What is not sourced** — where the payload says so. Three pillars carry declared gaps and the Top & Bottom composite is one of them.

## Length

**Whatever the month needs. No word count.** What does not vary: print precision, the numeral audit, the model pin, and the rule that a figure the payload does not carry cannot be printed.

## Reference paragraph (September 2026) — emitted exactly as it should be

September's regime changed in one place and held everywhere else. The gamma dial went from positive to negative against the previous Monthly of 1 September, which is the one move a reader has to act on: a negative dealer gamma means the hedging flow amplifies moves rather than damping them, and the pillars that feed the macro dial did not move to explain it — gamma is the one dial no pillar feeds, read from the option chain rather than from any macro series. Macro itself has no state at this cutoff: growth and inflation are absent because the FRED vintages knowable here stop in May, and the dial declines to synthesise a reading from members it cannot see rather than substituting a proxy. Vol reads normal with its two term-structure legs agreeing on contango and disagreeing sharply on degree — the curve itself at its 30th percentile, the VIX3M proxy at its 94th — so the same word covers an ordinary curve and an unusually steep one, and the dual run to 23 December is the count that will decide which of them the report keeps. Breadth is the only dimension that changed state, and one exception opened while another closed, so the set is the same size and not the same set. No scenario weight has been emitted, which means the Brier column is empty and nothing about this system's forecasting accuracy can be said yet: the ledger is seeded from a Monthly's own scenario table, so the first score arrives a month after the first weight. The Top & Bottom verdict is absent because the harness is not built, and the section prints the bear-rally base rate regardless — a median counter-trend rally of +13.5% inside a bear market, p75 +18.4%, extreme +46.8% in November 1929 — because that is the number that governs how a top call is held rather than how it is made. On the alternative-asset side metals, energy and digital all have readings and real assets have none, needing a REIT index or an infrastructure proxy the store does not carry. The register closed the month with nothing at a grading horizon, so expectancy is undefined on every leg and the honest reading of an undefined interval is that nothing about the sign can be said; two decisions are open and no rule break was recorded, with three of the Doctrine's rule-break categories still unsourced because the register carries neither a book label nor a closing reason.

## Style rules

- Plain declaratives. No headers inside the prose, no bullets.
- **No markdown, and the reference paragraph above is shown exactly as it should be emitted.** These reports are HTML and Markdown: the renderer escapes what it is given, so `**bold**` reaches the reader as asterisks.
- **The interval before the point**, wherever an expectancy or a Brier score appears.
- **Do not restate a table row by row.** Every table is printed below the prose.
- A sign is part of the numeral: `-0.02%`, not "down 0.02%".
- A figure's unit word must match what the figure is: "13 rows" for a count, never "13-day-old".
- Never say buy, sell, add, trim, hold, or overweight.
- End on what the next month tests.
