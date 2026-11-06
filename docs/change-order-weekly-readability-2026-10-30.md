# Change order — the Weekly's readability fixes (W10-1 to W10-3)

| | |
|---|---|
| **File** | `docs/change-order-weekly-readability-2026-10-30.md` |
| **Status** | Drafted 30 Oct 2026 from D36 (25 Oct); accepted 31 Oct 2026, 10:33 ET (the operator; D46), decisions 1–4 as recommended; filed 31 Oct 2026 (paste B95); built by A97 |
| **Origin** | D36: the Weekly Letter was adopted as the readable edition; the Weekly itself keeps three fixes "post-Monthly": the audit's fallback, a "what to see" line per chart, the coverage rows. |
| **Scope** | The Weekly (Sunday 05:00) and, where the same code serves it, the Monthly. Report-only: no measure, flag, dial or decision changes. |
| **Totals** | ≈ 5 h of sessions · no by-hand work |
| **Timing** | Built branch-only on the weekend of 31 Oct; merges Tue 3 or Wed 4 Nov with the post-Monthly merges; first edition the 8 Nov Weekly. |

## W10-1 · The audit's fallback: withhold the sentence, not the section

**Today.** When the numeral audit fails a draft twice, the whole section is withheld. On 28 Oct the Monthly's dry run withheld 20 of 61 sections that way; most of the withheld drafts were right except for one figure's binding. A withheld section prints nothing, so the reader loses the nine correct sentences with the one the audit could not place.

**Decision.** After the second attempt fails, the fallback publishes the draft with each failing sentence removed and a visible marker in its place: "[one sentence withheld: figure audit]". The section's status line reads "published, k sentence(s) withheld" and the run log names each withheld sentence and reason, as it does now. Limits that keep the audit's design: the fallback never edits a figure; it removes the whole sentence that carries it; if more than a third of a section's sentences fail, or the section's first sentence fails, the whole section is withheld as today (a paragraph with holes in its lead misleads); the Précis and "Our read" keep the whole-section rule, because their sentences depend on each other. A gate on fixtures: a two-failure draft with one bad sentence publishes with the marker; a draft with four bad sentences of nine is withheld whole; no figure is ever changed.

**Decisions for the operator.** (1) The threshold: a third of sentences (recommended), or a fixed two sentences. (2) Whether the marker names the figure ("[sentence withheld: 5.29%]") or not (recommended: not; the figure is the thing the audit could not place).

## W10-2 · One "what to see" line under every chart

**Today.** The Weekly's eleven charts carry a title and a source line. The Letter writes a "Takeaway" for each; the Weekly does not.

**Decision.** Every chart in the Weekly and the Monthly carries one line beneath it, "What to see:", written by the section's model call from the chart's own data block, under the numeral audit like any sentence; withheld (the chart prints without the line) when the audit fails it. The line names the observation, not a conclusion: what the eye should find in the figure this week. Gate: the line's figures are in the chart's data block; a chart with no data block carries no line.

**Decision for the operator.** (3) The line's length cap: 30 words (recommended) or 50.

## W10-3 · Coverage, in one table

**Today.** "Not stored", "not tracked", "gap", "awaiting" and "descriptive; unvalidated, n=0" markers appear cell by cell across the edition, about 140 tables.

**Decision.** The markers stay in the cells (they are the honesty record), and the edition gains one "Coverage" table at the end of section 10, before the Detail Tables: one row per family of keys with its state (stored / declared gap / refused / awaiting / unvalidated) and count, the reason where declared, and the date it changed. Built from the store check's declared and stale lists, which already exist. The Letter's coverage paragraph reads this table.

**Decision for the operator.** (4) Whether the per-cell markers also shrink to a footnote mark ("—¹") pointing at the table (recommended: no, not in this order; it changes 140 tables and the Letter already reads the table).

## Sign-off

| Date / time (ET) | Items | Ruling as stated |
|---|---|---|
| 25 Oct 2026, 06:13 | the three fixes named in D36 | "yes" (as the Letter's follow-up) |
| 31 Oct 2026, 10:33 | W10-1 to W10-3 and decisions 1–4 | "the operator, 31 Oct 2026, accept all, decisions 1-4 as recommended": (1) a third of the section's sentences; (2) the marker does not name the figure; (3) "What to see" capped at 30 words; (4) no per-cell footnote marks (D46) |
