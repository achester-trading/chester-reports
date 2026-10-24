# library-xxvii: Debt Cycles, Regimes, and Environments, Draft 1 (session B, B62, 24–25 Oct 2026)

**What it is.** The commissioned Phase 2 paper XXVII, written from its brief (`docs/briefs/phase-2-briefs-xxv-xxvii.md`, section "XXVII", emphasis decisions of 7 Sep 2026). File: `docs/whitepapers/debt-cycles-regimes-environments-whitepaper.md`. It is a NEW paper; no other paper's body is edited. Nothing in it grants a right.

**Base and branch.** `library-xxvii` from `origin/main` at `4180398`, in its own worktree `../chester-lib27`. Library line: it merges by its own pull request after review, never through chain-7. Docs only, with one exception: the library gate's registry line (below).

## The outline as written, against the brief

| Brief | As written | Words (whitespace-split) |
|---|---|---|
| Masthead; prerequisites note | Masthead in the house format (Companion; Series placement XXVII; Version 1.0 Draft 1, 24 October 2026; Status Draft); reader's note; the conventions; prerequisites; not-advice | 958 |
| Part I — The cycles (Ch 1–4) | The five lenses, argued and tabled. Ch 1 the short cycle; Ch 2 the long cycle (2.1 the frame, the four levers, "beautiful", its failures; 2.2 the two deleveragings; 2.3 **the internal-order cycle, a coequal lens**); Ch 3 repression, fiscal dominance, yield-curve control and capital controls; Ch 4 the reserve currency | 5,463 |
| Part II — Locating the present (Ch 5–7) | Ch 5 the twelve diagnostic questions, each with its lens and stored series; Ch 6 what a hundred years can and cannot tell us; Ch 7 the current read, a pointer to Appendix B only | 2,668 |
| Part III — Tops of long cycles, from inside (Ch 8–12) | 1929; 1989 (Japan); 2000; 2007; now as diagnostics. Each carries the same six things at equal weight: diagnostics and the day's frameworks; who was forced; how long the top took and what being early cost (the base rates cited from Base Rates and Tops and Bottoms); what resolved it; the stance it implies; what it looked like on the day. Then "The five, read together" | 4,202 |
| Part IV — The environments (Ch 13–16) | Ch 13 the eighteen, by mechanism family (13.1 cycle, 13.2 market, 13.3 crisis, 13.4 structural); Ch 14 × asset classes with the instance count (n) per row; Ch 15 × the seven signals; Ch 16 × participants | 3,724 |
| Part V — Identification and transition (Ch 17–20) | Ch 17 identification as a skill (17.1 the dials; 17.2 leading and confirming; 17.3 the base rates of transitions; **17.4 the two branches, told apart early**); Ch 18 how regimes end (1972–74, 1980–82, 2000, 2007–09, 2020, 2022; the false transitions); Ch 19 structural breaks (the break-or-regime test); Ch 20 the library through the regime, a table per markets paper | 3,723 |
| Part VI (Tactical; Wiring; Assumptions and Falsifiers; dated appendix) | Ch 21 tactical applications, all seven rungs, nine fields each, plus Book A's stance by regime and the environment-switch table; Ch 22 wiring; Ch 23 environments; Appendix A (a)–(e); Appendix B, the dated appendix | 1,913 + 1,074 + 922 |
| **Total** | | **24,647** (whitespace-split, the library gate's method; `wc -w` reads about 1.5% lower) |

**The 6f section (17.4).** The observables the 6f spec's section 5 names and the four the built field prints, what each branch does to them (prose, then a table), and a **PROPOSED** rule stated for the operator's ruling:
- a precondition (the interest burden above its five-year 80th percentile, or the deficit above its five-year median outside recession);
- three tells on a thirteen-week window (breakeven direction, real-yield direction, gold against real yields);
- deflationary when all three agree; inflationary when the breakeven rises or the real yield is negative, *and* gold diverges;
- persistence of two month-ends to print and two to revert;
- confidence as the count of agreeing tells, never a probability.

It carries its own assumptions and four falsifiers, a worked example, a historical instance (2008) and the day. The field stays report-only whatever is ruled, and the sizing consequence is left to the Doctrine.

## Departures from the brief, each with its reason

1. **The guide carries one at-a-glance row now, and the gate one registry line.** The paste says the guide is not written. But the library gate fails any file in `docs/whitepapers/` without an at-a-glance row (check 1) and any guide row without a registry entry. So `tools/check_library.py` gains `"XXVII": "debt-cycles-regimes-environments"`, and the guide gains a placeholder row that says it is a placeholder. The one-page entry is drafted below, not written into the guide. The guide header's word total (426,000) is not changed, so the gate warns (check 11, measured 468,027): the header changes when the paper merges.
2. **About 24,600 words against the brief's ~20,000.** Part I runs long (5,460) because the internal-order lens and the four repression regimes each carry the full worked-example, instance and on-the-day triple. Trimming Part I to about 4,000 would bring the paper to about 23,000; the review decides.
3. **Part VI has three chapters and two appendices.** Ch 21 tactical (with Book A's stance by regime), Ch 22 wiring, Ch 23 environments. The house standard's Environments chapter is, for this paper, Part IV itself, so Ch 23 points to it and restates only the two cautions rather than duplicating the matrix.
4. **The worked-example triple in Part IV is given per mechanism family** (cycle, market, crisis, structural), with each of the eighteen environments carrying its own mechanism and instances. A full triple for each of the eighteen would have added about 4,000 words of repetition. In Part III, each instance's "being early" arithmetic is its worked example with numbers.
5. **Amendment #3 workstream B's order is not in the repository.** No file `docs/change-order-*amendment-3*` exists, and no "13 Sep" order is filed. The architecture document's Part 29 is Change Order #3's tactical additions and does not mention the internal order. The internal-order lens (2.3) is therefore built from what the repository says of it:
   - batch 5 item 18's "Workstream B added Strauss & Howe";
   - GTM-11's "Internal Order panel" (labour against profits share, wealth by cohort);
   - batch 6 item 38's "the regimes Factor V and the Internal Order workstream watch".

   It cites Dalio's internal order and disorder, Strauss and Howe, and Turchin as published works, and it uses their observables rather than their clocks. See needs-you 5.
6. **The 6f branch section is 17.4, inside Chapter 17,** because identification is that chapter's subject. It is not a separate chapter, so the brief's twenty chapters stand.
7. **Appendix B's twelve values are cited, not computed.** Five cells carry values from the library's own dated material (Currencies, August 2026; Foundations; Base Rates 14.3), each with its date and source. Seven cells say "not stated here" and name the stored series to read at the refresh. No number was computed or guessed for this Draft.
8. **The dated-appendix queue's XXVII entries are copied into Appendix B, and the queue is not edited.** B.3 is the DGS10 closes, B.4 the long-bond chart note and B.5 the gold-to-equities note (batch 6 item 38, which also names XXVII's appendix). In B.4 and B.5 the names of the pitch's author and of the fund manager are taken out, under the no-names rule. The queue strikes the entries when the paper merges; leaving it untouched keeps this branch clear of chain-7's queue appends.
9. **No people's names in the paper except authors of cited published works:** Dalio, Minsky, Reinhart and Rogoff, Reinhart and Sbrancia, Koo, Kindleberger, Fisher, Strauss and Howe, Turchin, and Shiller's dataset.
   - Central-bank chairs, officials and bankers are described by role ("a central bank chair's December 1996 warning", "a new central-bank chair from May 2026").
   - The 1971 event is "the closing of the gold window".
   - No Brookfield-group instrument appears.
10. **Figures are placeholders only.** Six are listed in Appendix A (e) and in `docs/figures/debt-cycles-regimes-environments/README.md`, each with the stored keys it would draw from (checked against `metrics_registry.yaml`). None is drawn, and none is linked as an image, because the gate fails a figure link that does not resolve.
11. **The wiring names the stack's sections as they stand** (The read, Plumbing & rates, What's priced, Mechanics, the slow layers, Pillar 8), not the old numbered daily sections Price, Time, and Edge cites.

## The drafted guide entry (for the operator; written into the guide when the paper merges)

**At-a-glance row:**

| Layer | # | Paper | Short name | Companion to | Size | One-line description |
|---|---|---|---|---|---|---|
| Foundational | **XXVII** | Debt Cycles, Regimes, and Environments | Debt Cycles | Every markets paper's Environments section; the market-state object's debt-cycle branch; Book A's stance; read fourth in the core track | v1.0 Draft 1 · ~24,600 words, 6 figure placeholders | The library's frame for *where we are* — **every relationship the library teaches was measured inside a regime**; the short and long debt cycles read through five lenses (Dalio's vocabulary, Minsky, Reinhart–Rogoff, Koo, Kindleberger) with the internal-order cycle as a coequal sixth; the two deleveragings and the four repression regimes; twelve measurable diagnostic questions; **five long-cycle tops told from inside, each with what being early cost**; the eighteen environments defined by mechanism with asset, signal and participant matrices and n stated; identification and transition as one skill, structural breaks told from regimes, and **a proposed rule for telling the two branches apart early** |

**One-page entry:**

> ## XXVII. Debt Cycles, Regimes, and Environments
>
> **What it contains.** The library's frame for locating the present. Part I is the cycles: the short debt cycle by phase and what each phase does to each asset class; the long cycle with its four levers, what a "beautiful" deleveraging is and how it fails; the two deleveragings, decided by the currency the debt is owed in; the internal-order cycle as a coequal lens that biases the branch toward monetization when the other levers are politically blocked; the four operating regimes of a heavily indebted state (repression, fiscal dominance, yield-curve control, capital controls) and the captive holder each creates; and the reserve currency as what lengthens the cycle. Part II is twelve diagnostic questions, each with its lens and its stored series, and an honest account of what one long cycle in the U.S. record can and cannot say. Part III tells five tops from inside — 1929, Japan in 1989, 2000, 2007, and the present as a diagnostic — with equal weight on what being early cost. Part IV defines the eighteen environments by mechanism and gives the asset, signal and participant matrices with the instance count behind every row. Part V is identification and transition: the dials, leading against confirming, the base rates of false transitions, how six regimes ended, the break-or-regime test, the library read through the regime, and a proposed rule for the market-state object's debt-cycle branch, for the operator's ruling.
>
> **Why it matters.** It is the paper every other markets paper's Environments section points at, and the reason a relationship measured in disinflation is not trusted in inflation.
>
> **Read it with.** Price, Time, and Edge (participants and horizons); Base Rates (Parts III–IV); Tops and Bottoms; Currencies (the dollar); Metals (the broken model); the Doctrine (Part V).

**Papers that will need a reference to this one (for Phase 5):**
- Foundations, Factor IV (its debt-cycle 101 is absorbed here);
- Currencies, Chapter 14 (the Dalio chapter's mechanism is absorbed; its FX consequences stay there);
- the Monthly manual, Pillar 8;
- Base Rates, Chapters 14–15;
- the Doctrine, Part V (the environment-switch pointer, Chapter 21's table);
- Portfolio Construction (its regime part);
- every markets paper's Environments section, which becomes a row set of Part IV's matrices.

## The figure list

| # | Placeholder | Stored series |
|---|---|---|
| 1 | The long cycle in one panel | `calc.fed_debt_total_pct_gdp`, `calc.interest_to_receipts` |
| 2 | r against g | `calc.r_minus_g` (average, marginal) |
| 3 | The branch tells | `fred.breakeven_10y`, `fred.tips_10y`, `calc.r_real_10y_cpi`, `yfinance.mkt_gold_front` |
| 4 | The stock–bond correlation through regimes | `calc.corr_spy_tlt_60d` |
| 5 | Five tops, from inside | Episode dates from Tops and Bottoms and Base Rates (no stored series) |
| 6 | The environment matrix | The paper's Chapter 14 (no stored series) |

## Validation

| Check | Result |
|---|---|
| Sequential numbering | Parts I–VI; Chapters 1–23; sections 2.1–2.3, 13.1–13.4, 17.1–17.4; Figures 1–6; Appendices A–B. The gate's check 3 and check 4 pass |
| Cross-reference audit (every internal "Chapter N" or "N.M" against its heading) | 53 internal references, 0 unresolved; 34 references to other papers' chapters, each checked against that paper's headings |
| `tools/check_library.py` | **0 failures**, 1 warning (check 11, the guide header's word total; departure 1) |
| Readability gate | Not applicable: `validate_readability` covers the reporting stack's prose, not the papers |
| Cite by name, never numeral; no bare "Rule N"; no stale forward reference | The gate's checks 2, 5 and 12 pass |
| No people's names beyond cited authors; no Brookfield instrument | Searched; none |

## Needs you (at most five)

1. **The review itself:** Draft 1 against the brief, with the departures above.
2. **The proposed branch rule (17.4):** take it to Doctrine #2 (7–8 Nov) beside 6f's decision 11, or to a later sitting once the rule has been run back over the stored history?
3. **The guide:** accept the placeholder at-a-glance row the gate needs now and the drafted entry above for the merge, along with the header's word total, which changes then.
4. **Length:** keep about 24,600 words, or trim Part I toward 4,000 (about 23,000 in all)?
5. **Amendment #3 workstream B:** the internal-order lens was built without the 13 Sep order, which is not in the repository. File it (or point to it), so the lens can be checked against its words at the review?
