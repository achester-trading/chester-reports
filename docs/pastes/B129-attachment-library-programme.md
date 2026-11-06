# Change order — the library programme after Audit 2 (handoff from the library chat)

**Date:** 6 November 2026 · **Status:** PROPOSED — eight rulings in §4, pending
**File as:** `docs/change-order-library-programme-2026-11-06.md`
**Source:** the library chat (Audits 1 and 2, the XXV build, the 28 Sep "next papers" review), re-reviewed against `main` at `47238f50` (5 Nov) and the library branches. This order replaces the 28 Sep recommendations, most of which have since been built.
**Governs:** what remains of `docs/white-paper-library-audit-2.md` (the roster, Parts 4–7, and the 7 Sep decisions). The 30 Oct library review memo (D48) and its twelve decisions stand. Nothing here changes those decisions.

---

## 1. Where the programme stands

**On `main`:** XXV Price, Time, and Edge (Draft 1.1), XXXIII The Reporting System: A Reader's Guide, XXXIV Emerging Markets (Draft 1, provisional numeral), ST-L's dated appendices, and the Audit 1 conventions and gate. `check_library` passes 27 papers with 0 failures and 0 warnings.

**Written and rehearsed, not yet merged.** These follow B116's order (`docs/briefs/b116-library-script.md`):

| Step | Branch | Content | Open item before its PR |
|---|---|---|---|
| 1 | `library-xxvii` | XXVII Debt Cycles, Regimes, and Environments (24,647 words) | none; 17.4 stays "a proposal" (D30(2)) |
| 2 | `library-phase-3a` | Foundations split (timeless body + Appendix B); Twenty-Five contracted + companion appendix | none |
| 3 | `library-xxxi` | XXXI Top & Bottom Report Manual | the roll-up tier rule, ruled at **Doctrine #2 (7–8 Nov)** (D48 #7) |
| 4 | `library-xxxii` | XXXII The Annual Structural Review, with the spread review calendar | none |
| 5 | `library-ei-figures` | Evidence and Inference's five figures | none |
| 6 | `library-xxix` | XXIX Real Assets and Risk Transfer (marks cleared, B94) | none |
| 7 | `library-xxx` | XXX Market Structure and Cascades | **four store figures**: the box export (D48 #11) and then a drawing paste. The branch has no commit after 26 Oct, so this has not been done yet |

After all seven merges the gate reads 32 / 0 / 6. The six warnings are the guide's stale word count (451,000 against 504,151 measured) and check 15's "Assumptions and Falsifiers appendix owed at review" rows.

**Not started.** These Audit 2 items have no branch:

1. **The operator behavioral paper.** It was ruled on 7 Sep to be written now, from principles. The guide still lists it as "deliberately deferred", so the guide and the ruling disagree. Its planned numeral, XXXIII, was taken by the Reporting System paper.
2. **XXVI Turning Points, Bubbles, and Crises**, the rewrite and expansion of X.
3. **The Monthly manual split**: XXVIII Macro Dynamics (Markets shelf) plus III rewritten as the manual of the *current* Monthly. III still describes the v16 report. The Monthly has since become v2: the ten-section stack, the metric lenses, and the Reading chapter.
4. **XXIV Earnings, expanded to Events and Expectations.**
5. **XV Equities, expanded**: valuation, factors, single names.
6. **The Doctrine amendments of Audit 2 §4.9.** These are the twelve edges and six questions (by reference to XXV), the seven-rung ladder, and the library reading plan. The Doctrine does not yet cite XXV. The change ladder (Appendix D) and the attention budget, from the Enterprise Layer order, are already in.
7. **XXV's cross-references.** Fifteen papers carry a passage that XXV now owns, and none of them points to it yet. The list is in XXV's Draft 1 report, and §3 item L-3 below copies it.
8. **Phase 5 standard chapters** across the existing papers: Tactical Applications by horizon, Wiring, Environments, and the Assumptions and Falsifiers appendix. Check 15 already tracks the appendix as "owed at review".
9. **The guide restructure**: the three shelves (Markets / Craft / System, with the Doctrine as spine), the core-track reading plan, and a refreshed word total.
10. **Annual review tooling.** These are Audit 2 §5.1 Instruments 2 and 3: recomputing every dated figure, and the relationship health check. No `annual-review` target exists. XXXII's corpus pass is set for **16 Jan 2027** and needs both.
11. **The options running position** (§4.6): one trade carried through XXII, XIII and XI.

**Already scheduled elsewhere, so not restated:** Phase 3b (the two dated passages, at each paper's next edition, per D48 #6); XXVII 17.4 at Doctrine #3 (early Dec); XVII Draft 2 when its four conditions are met (three months of register data arrive around early December).

---

## 2. The change in one paragraph

Merge the seven library branches in B116's order first: XXXI after Doctrine #2, and XXX after its figures. Then write the four papers still owed, in this order: the behavioral paper, Turning Points, the Monthly split, then Events and Expectations. Equities follows after them. Do the cheap, high-value pieces in one session each: XXV's fifteen pointers, the guide restructure, and the annual-review tooling, which must exist before 16 Jan. The full Phase 5 chapters are not run as a batch. Each paper gets them in its XXXII review month, so every paper is opened once a year instead of twice. The Doctrine amendments go to Doctrine #3.

---

## 3. Work items, in order

Times are Claude Code session estimates, in auto mode, mostly unattended.

| ID | Work | Where | When | Est. |
|---|---|---|---|---|
| L-1 | The seven merges, B116's order (steps 1–2 and 4–6 now; 3 after Doctrine #2; 7 after L-2) | each branch → `main` by its own PR (D30) | from 9 Nov | 0.5 h per PR + your review |
| L-2 | XXX's four store figures: the read-only box export (D48 #11's command), then the drawing paste | box, then `library-xxx` | this week | 0.5 h by hand + 1 h |
| L-3 | XXV pointers: a one-line prerequisites pointer in each of the fifteen load-bearing papers (the Doctrine, Positioning & Flows, the Twenty-Five, the Dealer's Hand, Volatility, Technical Indicators, Earnings, Base Rates, Evidence and Inference, Metals, Tops and Bottoms, Equities, the Monthly manual, the Daily Cascade paper, Portfolio Construction). Plus the boundary sentence in Positioning & Flows: "XXV owns the holders, this paper the mechanical traders." The Doctrine's line waits for L-9 | `library-xxv-pointers` | after L-1 | 1 h |
| L-4 | The guide: three shelves as a column, the core-track reading plan (Audit 2 Part 3), the measured word total, and the behavioral paper moved from "deferred" to "commissioned" | `library-guide-shelves` | after L-1 | 1 h |
| L-5 | Annual review tooling: `annual-review` target. Instrument 2 recomputes every dated-appendix figure from the point-in-time store with `available_at`, and diffs against tolerance. Instrument 3 is the relationship health check, returning holding / weakening / broken / re-attached for each Appendix A(b) regularity. The papers that lack an A(b) are listed, not failed | system code, `main` | before 16 Jan 2027 | 4–6 h |
| L-6 | **The behavioral paper (XXXV)**, Draft 1, from principles: the canon applied to the operator; size creep, thesis attachment, overtrading in chop, narrative capture by one's own research; the Wizards' behavioral lessons; the failure modes the Doctrine records; and the signal-triage items routed to it (dip-buying cohort, rally trap). It also uses the register data that exists by then, labelled as early. Draft 2 is triggered by the register, the same condition as XVII. Brief first, in chat | `library-xxxv` | after L-1 | brief 20 min · 1.5–2 h |
| L-7 | **XXVI Turning Points, Bubbles, and Crises**: X's eight episodes and near-misses kept; adds bubbles as an anatomy (Minsky–Kindleberger, with a hold-and-trade playbook), banking crises as a mechanism (2023, 2008, Continental Illinois, the sovereign–bank loop), liquidity crises (2019 repo, March 2020, 2022 gilts), EM crises, and international tops. It takes the batch items already routed to turning points (BofA peak-concentration table, Capitulation Count, bear-rally structure). The boundary is XXVII Part III, which owns long-cycle tops, and neither paper re-narrates the other. X's numeral is retired to the archive with a pointer | `library-xxvi` | after L-6 | brief 20 min · 2–2.5 h |
| L-8 | **The Monthly split.** XXVIII Macro Dynamics takes the ten pillars' 101 / predictive properties / institutional use / tradability / failure modes / regime dependence, reorganized by mechanism. III is rewritten as the manual of the Monthly v2 (stack, lenses, Reading chapter, Part 16). Written after the 1 Dec edition settles | `library-xxviii` | after 1 Dec Monthly | brief 20 min · 3 h |
| L-9 | Doctrine amendments (§4.9), applied by a library session after Doctrine #3 rules them | `library-doctrine-4-9` | after Doctrine #3 | 1 h |
| L-10 | **XXIV Events and Expectations**: Earnings kept whole as Parts I–V, plus macro releases (absorbing batch 8 item 48's 24-lens release decomposition), FOMC, elections (the midterm row), and index events. It takes the event-vol ledger and the event-study utility | `library-xxiv` | after L-8 | brief 20 min · 1.5–2 h |
| L-11 | **XV Equities expanded**: valuation (ERP, the multiple's drivers, the denominator shared with XXIV), factors, the index machine (pointing to XXX for ETF mechanics), and single-name method. It absorbs the GTM items already routed there (valuation quad, concentration twin, earnings-vs-multiple) | `library-xv` | after L-10 | 1.5 h |
| L-12 | Phase 5 standard chapters, per paper in its XXXII review month, with the options running position (§4.6) done at XXII's review | per paper | rolling, 2027 | 0.5–0.75 h each |

**Total ahead:** about 20–25 hours of sessions through January, plus your reads of four new papers (about 80,000 words). L-12 then runs at about one paper a month.

---

## 4. Rulings

These are all eight at once. Each has a short explanation and my recommendation. Accept them as a block unless you disagree with one.

**R-1. The behavioral paper's numeral and timing.** *Recommend: XXXV, written now as L-6.* On 7 Sep you ruled to write it now, from principles. The guide was never updated, and XXXIII went to the Reporting System paper. XXXIV is EM's provisional numeral, so XXXV is the next free one. Writing it now still holds: the register has about two months of data, enough to illustrate, and not enough to conclude. That is exactly what a Draft 1 / Draft 2 split is for.

**R-2. The order of the four papers still owed.** *Recommend: behavioral → Turning Points → Monthly split → Events and Expectations, then Equities.* The behavioral paper is the shortest and the most personal. It also closes a disagreement between the guide and a ruling. Turning Points carries your item-7 emphasis, and it completes the pair with XXVII Part III. The Monthly split has to wait for the 1 Dec edition anyway. Events and Expectations then absorbs the release-decomposition and event-vol work once they are built.

**R-3. Phase 5 pacing.** *Recommend: per paper, in its XXXII review month (L-12), with the cheap cross-cutting pieces done now (L-3, L-4).* A batch of twenty papers costs 12–15 hours plus a skim of every paper, and it would reopen papers the review calendar opens again within the year. The gate already tracks what each paper owes, so nothing is lost by waiting. The two pieces worth doing now are the pointers and the guide, because every reader meets those first.

**R-4. The Doctrine amendments go to Doctrine #3 (early Dec).** *Recommend: yes.* Under Rule 20 they need a sitting. The Doctrine #2 agenda (7–8 Nov) is full, and Doctrine #3 already takes XXVII's 17.4 branch rule. Both are reading-the-library-into-the-Doctrine questions, so it makes sense to rule them together.

**R-5. The word budget.** *Recommend: accept the measured size (about 504,000 after the merges, about 560,000 after L-6 to L-11), and make the core track the reading promise.* Audit 2 estimated 420,000. The overrun came from the expansions you chose: XXV's two centerpieces, the presentation standard (prose first, then a cheat-sheet table), and XXVII's full Part on tops. The guide's reading plan (L-4) defines the roughly 230,000 words to read in order. Everything else is reference.

**R-6. The annual-review tooling is built before 16 Jan 2027.** *Recommend: yes, as L-5, a system-stream session.* XXXII's corpus pass is a written questionnaire without Instruments 2 and 3. The relationship health check is the one instrument that tells you a paper is now teaching something false.

**R-7. The Monthly split waits for the 1 Dec edition.** *Recommend: yes.* III's manual half should describe a Monthly that has stopped changing. The first edition was 1 Nov, and the 1 Dec edition will show whether the stack is settled. The XXVIII half could be written now, but splitting a paper twice costs more than waiting four weeks.

**R-8. X's fate when XXVI is written.** *Recommend: X goes to `archive/` with a forward pointer, and its numeral is never reused.* This follows Audit 1's rule that numerals are accession IDs. The T&B methodology now lives in XXXI, and XXVI is the market paper. Keeping X alive beside XXVI would duplicate its eight episodes.

---

## 5. Notes for the sessions

- Every new paper follows the house standards in `docs/briefs/phase-2-briefs-xxv-xxvii.md` (as amended by `xxv-draft-1-1-revisions.md`). That means prose first, then a concise table; no "(mechanism)" labels; sample and date as a closing clause; forecasts only in the dated appendix; the four books defined where first used; the Tactical, Wiring, Environments and Assumptions-and-Falsifiers chapters from the first draft; and a brief agreed in chat before writing.
- Each paper is written on its own `library-*` branch and merged by its own PR after your review (D30). The gate is green at each merge.
- Signal-triage items routed to a paper are taken into that paper's next writing or review session, not by a separate edit pass. ST-L established this pattern.
- This order closes the library chat. Audits 1 and 2, the briefs and this order hold everything it decided.