# Commissioning briefs — Phase 2 papers

These briefs are the handoff from Audit 2 (`docs/white-paper-library-audit-2.md`) to the writing sessions. A session writing one of these papers reads the audit's Part 0, Part 1, Part 4, and the relevant card, then this brief, then the papers named under "must cite" — and writes to the brief. Emphasis decisions recorded here were taken by the operator on 7 September 2026 and are not reopened in the writing session.

## House standards (apply to both)

- **Shelf and voice.** Markets-shelf paper: explains how markets work; does not restate the Doctrine's rules (cites them by "Doctrine Rule N"); does not describe the system's mechanics (cites the report manuals). Mechanism-first. Bull and bear stated fairly. Track record before any forecast. Percentiles, not means. Not-investment-advice caveat in any construction or forecast section.
- **Confidence tiers, marked in the text:** *mechanism* (durable), *regularity* (empirical — state the sample period, the regime, and last-verified date), *forecast* (dated; lives only in the dated appendix). No level, probability, or "today" read in the timeless body.
- **Cross-references** by short name only, never numeral, per the guide's short-name column. The masthead carries the paper's own numeral.
- **Required closing chapters** (Audit 2 §4.1–4.3, 4.7, 5.1): Tactical Applications (seven horizon rows × nine columns: what is tradeable, edge type, who is on the other side and why they transact, why competition hasn't removed it, what would end it, expression, Book, report section); Wiring (daily §s, Weekend Synthesis, Monthly pillar/part, quarterly, register fields, claims-registry entries, what the annual review re-verifies); Environments (the eighteen, for this paper's subject); Assumptions & Falsifiers appendix (mechanisms; regularities with sample/regime/date; falsifier per regularity; standing-register items that touch this paper; inventory of dated figures with their series); Dated appendix (as-of dated, every figure).
- **Prerequisites note** at the head: what the paper assumes and where it is taught.
- **Examples:** every mechanism gets one worked example with numbers, one historical instance, and one "what it looked like on the day."
- **Masthead** in the house format (title, subtitle, "Companion white paper — chester-reports library", Series placement with numeral, Version 1.0 and date, Status). File at `docs/whitepapers/<slug>-whitepaper.md`; figures as files under `docs/figures/<slug>/` linked from the `.md`; the guide's at-a-glance row and one-page entry drafted at the end for the operator to review.
- **Validation before delivery:** sequential section numbering; cross-reference audit (every "Chapter N"/"Section N" against its heading); `make library-check` green if run in the repo.

---

## XXV — Price, Time, and Edge

**Slug:** `price-time-and-edge` · **Numeral:** XXV · **Shelf:** Markets · **Target:** ~18,000 words · **Reading-plan position:** 2 (after Doctrine Parts I–III) · **Version:** 1.0

**Purpose.** The library's foundational layer, which it has lacked: what a price is, what time does to what is knowable, who the participants are and what forces them, and why an opportunity can exist at all. Every other Markets paper will cite it for its participant and horizon vocabulary and for the six questions.

**Organizing claim.** A price is the expectation of the marginal participant, weighted by his capital and his urgency. Markets move on the difference between what happens and what was expected; the move then changes what participants do and what the fundamentals are. Edge is a durable reason to be on the right side of that difference — and every durable reason is information someone lacks, analysis someone can't do, behavior someone can't help, structure someone can't escape, or time someone doesn't have.

**Two sentences the paper opens with and the rest of the library cites, not restates:** markets trade on the difference between reality and expectations, not on whether news is good or bad; price itself changes behavior, positioning, fundamentals, narratives, and subsequent price.

**Parts and chapters.**

*Part I — What a price is.*
1. The marginal participant — capital × urgency; the order book as the physical fact; who sets the price at the margin and why it is rarely the largest holder.
2. Reality versus expectations — the surprise as the unit of price change; consensus as a positioning object; why "priced in" is a claim about who has already acted.
3. Price as a participant — reflexivity as the general case: price → positioning → fundamentals (financing, hiring, capex, collateral, deposits) → narrative → price.
4. Narratives — formation, spread, and reversal; the narrative as compressed expectation; how to read one without believing it.
5. Efficiency as the special case — when prices are right and why; the Grossman–Stiglitz paradox; where inefficiency must exist for markets to function at all.

*Part II — Time.*
6. The seven rungs — intraday, days, weeks, months, cyclical, secular, generational: for each, what moves price, who competes there and with what resources, what is knowable and what is noise.
7. How horizons couple — the slower sets the prior for the faster; the faster sets the timing for the slower; the Doctrine's "slower wins on direction, faster wins on timing" derived rather than asserted.
8. **The weeks-to-months rung, in full (centerpiece — operator's decision).** Its own mini-craft: what moves price over weeks (earnings drift, sector rotation, positioning cycles, macro- and vol-regime persistence, calendar flows); who competes there (pods with weekly risk budgets above it, CTAs at longer scales, retail at shorter) and why the middle is the emptiest rung for a discretionary individual; entry and exit as the horizon defines them; what to read (which report sections, which paper signals); the failure modes specific to the rung (thesis drift into a day trade or a "long-term holding" — the Doctrine's observation, given its mechanism).
9. Horizon as edge — the ability to wait; the ability to change horizon without asking; the cost of each; tax as a horizon input.

*Part III — Participants.*
10. The map — who owns the market versus who trades it; capital versus turnover; the numbers (dated appendix).
11. The holders — pensions, insurers, sovereign wealth funds, endowments, mutual funds, households: liability, mandate, benchmark, regulation, calendar; what forces each and when.
12. The intermediaries — banks, dealers, market makers, HFT, exchanges: balance sheet, inventory, regulation; what forces each.
13. The speculators — hedge funds and pods, CTAs, vol-control, risk parity, private equity, arbitrageurs, leveraged investors, retail: horizon, financing, drawdown limits, career risk; what forces each.
14. The issuers and sovereigns — corporations (issuance, buybacks), governments, central banks: what they must do and when.
15. Forced transactions — the taxonomy: margin, mandate, redemption, rebalance, regulation, hedging, calendar; the price-insensitive buyer and seller (cites the Twenty-Five's Part 0).
16. Who is on the other side — the method: for any trade, name the counterparty class and its reason; three worked identifications.

*Part IV — Edge.*
17. Why opportunities exist — limits to arbitrage: capital, horizon, mandate, information cost, risk-bearing capacity, agency.
18. The twelve edges — informational, analytical, behavioral, structural, liquidity, horizon, positioning/flow, event-driven, cross-asset, regime-recognition, execution, patience/optionality: each with mechanism, who holds it, capacity, who competes it away, what kills it.
19. Capacity — the arithmetic; why the small book's edges are the capacity-constrained ones and no others.
20. The six questions — why is there an opportunity; why should it exist; who is on the other side; why might they be forced or irrational; why has competition not removed it; what would end it — with three worked theses: one that passes, one that fails at "who is on the other side," one that fails at "why hasn't competition removed it."
21. Several partially independent edges — why one predictive model fails; correlation between edges; the Doctrine's nine alpha families mapped to the twelve edges and the four books.
22. The small book — the advantages stated as the market sees them (cites Doctrine §3.3; does not restate it) and the shadow: where the small book is the liquidity being harvested.
23. How edges die — crowding, capacity, structural change, regime change, technology (AI agents, automated liquidity, 24/7 markets); with the standing-register tripwires for each.

*Part V — Tactical Applications · Wiring · Environments · Assumptions & Falsifiers · Dated appendix.*

**Worked examples (use these; add if needed).** A "bad" CPI print that rallies; the 2023 regional-bank stock-price/deposit loop; gold's central-bank bid (cites Metals); the "soft landing" narrative's formation and reversal; the March 2020 pension rebalance; February 2018 (vol-control as the forced seller; cites Volatility); GameStop (forced buying); index inclusion as forced buying with a calendar (cites Positioning); an earnings-drift Book B thesis taken through the six questions.

**Emphasis decisions (taken 7 Sep 2026).** Part III at full depth (~5,000 words), not a compact map. Chapter 8 is the centerpiece with its own craft. Academic anchors named briefly — Grossman–Stiglitz, Shleifer–Vishny, Kyle, Lo, Soros — as names for ideas, not a literature review.

**Must cite (by short name):** the Doctrine (§2.2, §3.2, §3.3, Part IV); Positioning & Flows (Part II — this paper owns the holders, Positioning owns the mechanical traders; do not duplicate its map); the Twenty-Five (Part 0, the price-insensitive buyer); Base Rates; Evidence and Inference; Volatility; Metals (the broken model); the Dealer's Hand (dealers as a class — mechanics stay there).

**Must not.** Restate the Doctrine's rules; reproduce Positioning's mechanical-holder map; carry any level, share, or probability in the timeless body; introduce a fourth options 101.

---

## XXVII — Debt Cycles, Regimes, and Environments

**Slug:** `debt-cycles-regimes-environments` · **Numeral:** XXVII · **Shelf:** Markets · **Target:** ~20,000 words (raised from 18,000 for the full Part on long-cycle tops) · **Reading-plan position:** 4 · **Version:** 1.0

**Purpose.** The library's frame for *where we are*: the debt cycles, the policy regimes, the eighteen environments and what each does to assets, signals, and participants; regime identification and transition as one skill; structural breaks. Owns the master environment matrix that every other Markets paper's Environments section points at. Absorbs the debt-cycle 101s from Foundations (Factor IV), Currencies (the Dalio chapter), Monthly Pillar 8, and the mechanisms of Base Rates Part IV — each of which will then reference this paper.

**Organizing claim.** Every relationship the library teaches was measured inside a regime. The regime is set by where the economy stands in the short and long debt cycles and by the policy response. The reader's first job in any decision is to locate the present in the cycle and to know which of his regularities that location invalidates.

**Parts and chapters.**

*Part I — The cycles.*
1. The short debt cycle — expansion, tightening, recession, easing; what each phase does to rates, credit, equities, the dollar, commodities.
2. The long debt cycle — the frame stated, then examined: debt-to-income over decades; the two deleveragings (deflationary, inflationary); the four levers (austerity, default, monetization, transfer); what "beautiful" means and when it fails.
3. Financial repression, fiscal dominance, yield-curve control, capital controls — as operating regimes: mechanics, history (US and UK 1945–80; Japan since the 1990s; the EM instances), and what each does to each asset class and to the captive holder.
4. The reserve currency — the dollar's position; the timescales of erosion; what erosion looks like from inside; cites Currencies and Metals for the mechanisms they own.

*Part II — Locating the present.*
5. The twelve diagnostic questions, each measurable — debt-to-GDP and interest-to-revenue; who holds the debt; real rates against growth; policy space; private-sector leverage; valuations against income; the credit impulse; the fiscal impulse; the inflation regime; the external position; political constraints on the central bank; the top-of-cycle checklist.
6. What the last hundred years can and cannot tell us — one long cycle in the US record, Japan's as the second; the honest inference; how to reason about conditions that have not occurred (first principles from the mechanisms, not analogies from the sample).
7. The current read — **dated appendix only**.

*Part III — Tops of long cycles, from inside (full Part — operator's decision).*
8. 1929. 9. 1989 (Japan). 10. 2000. 11. 2007. 12. Now — as diagnostics, not a forecast.
Each instance carries, with equal weight: the diagnostics as they read at the time and what the frameworks of the day said; who was forced and by what; **how long the top took to form and what being early cost** (the base rates of early positioning, cited from Base Rates and Tops and Bottoms); what resolved it; and what the instance implies for the reader's stance rather than his forecast. The Part is framed as *locating*; it is not a tail paper. Boundary with Turning Points, Bubbles, and Crises: that paper owns equity-market turning points and the anatomy of manias; this Part owns the macro-structural view of long-cycle tops; the two cross-reference and neither re-narrates the other.

*Part IV — The environments.*
13. The eighteen defined — expansion, recession, inflation, disinflation, deflation, stagnation, bubble, crash, liquidity crisis, banking crisis, fiscal crisis, currency crisis, war, technological revolution, financial repression, capital controls, monetary-system change, structural break — each with historical instances and the mechanism that produces it.
14. Environments × asset classes — what each asset did, with dispersion and n; where n≈0, say so and give the mechanism.
15. Environments × the library's signals — which regularities hold, weaken, or invert in each (credit-leads-equities, curve inversion, gold–real rates, stock–bond correlation, the variance risk premium, momentum, the yen–vol link).
16. Environments × participants — who dominates, who is forced (the captive buyer under repression; the leveraged seller in a liquidity crisis; the sovereign in a currency crisis).

*Part V — Identification and transition.*
17. Identification as a skill — the dials (cites the Doctrine Part V and Volatility for the vol regimes); leading versus confirming indicators; the base rates of transitions; the cost of early versus late.
18. How regimes end — the sequences of 1972–74, 1980–82, 2000, 2007–09, 2020, 2022; the false transitions.
19. Structural breaks — the relationships that died (gold–real rates 2022, stock–bond correlation 2022, the curve's lead time, the Phillips curve); Metals' broken-model chapter as the template; how to know a break from a regime.
20. Reading the library through the regime — a table, per Markets paper, of what changes about its guidance in each major environment.

*Part VI — Tactical Applications (Book A stance by regime; the environment-switch table the Doctrine points to) · Wiring (which reports carry the dials) · Assumptions & Falsifiers · Dated appendix (the current read; the twelve diagnostic values, as-of dated).*

**Worked examples.** US 1945–51 repression; Japan 1990–2013; 2008 as a deflationary deleveraging; 2020–22 as the inflationary case; the simultaneous breaks of 2022; the 2022 gilt/LDI episode as a fiscal-market event; Argentina and Turkey as capital-control instances; Weimar against 1930 as the two resolutions (numbers from Base Rates).

**Emphasis decisions (taken 7 Sep 2026).** The debt-cycle frame is one lens among several — Minsky, Reinhart–Rogoff, Koo's balance-sheet recession, Kindleberger — with Dalio's vocabulary used because it is the most operational, and the diagnostic built from the union. All eighteen environments defined with mechanism; quantitative rows only where the sample supports it, with n stated. Part III is a full Part, five instances, with the anti-fault built in as above.

**Must cite (by short name):** Price, Time, and Edge (participants, horizons — written in parallel; cite its chapter titles); Base Rates (Parts III–IV numbers); Tops and Bottoms (episodes; note it becomes Turning Points, Bubbles, and Crises); Currencies; Metals; The Rate and Liquidity Machine; Credit; Volatility; the Doctrine Part V; Foundations (Factor IV); the Monthly manual (Pillar 8).

**Must not.** Forecast in the timeless body; re-narrate the eight bears (cite Tops and Bottoms); restate the Dalio chapter from Currencies (absorb its mechanism, cite it for the FX consequences); let Part III become a tail paper.

---

## Parallel-writing note

The two papers are written in parallel across two sessions. Order within the first session: XXV Parts II–III (the horizon and participant vocabulary) before anything in XXVII, so XXVII cites settled chapter titles. Each session ends by drafting its paper's guide row and one-page entry, and by listing which existing papers now need a reference to the new one (for Phase 5).
