# XXV — Draft 1.1 Revisions (operator review)

*Instruction recorded verbatim, 7 September 2026.*

---

Revise docs/whitepapers/price-time-and-edge-whitepaper.md to Draft 1.1 per the operator's review. First save this instruction, verbatim, as docs/briefs/xxv-draft-1-1-revisions.md for the record.

Presentation standard (applies here and to every paper from now on — also update the "House standards" section of docs/briefs/phase-2-briefs-xxv-xxvii.md and §4.7 of docs/white-paper-library-audit-2.md):

Confidence tiers: remove every "(mechanism)" marker — unmarked text is mechanism by default. Keep the sample period and last-verified date on empirical claims, but as a short italic closing clause in the sentence, not a bracketed label; drop the word "regularity." Forecasts remain appendix-only.
Any taxonomy, list, or matrix is presented as paragraphs first, then summarized in a concise table — the table is a cheat sheet, fewer words than the prose, never the primary carrier.
Conceptual, rounded, order-of-magnitude figures (ownership and turnover shares by participant class) are permitted in the timeless body when the table is labelled "conceptual; rounded; dated figures in Appendix B." The gate continues to police exact figures without an as-of date.

Revisions, by chapter:

Part I (Chapters 1–5): shorten by roughly a fifth; cut the passages that are academic rather than actionable; every chapter ends with what the reader does differently because of it.
Chapter 6: a paragraph on each of the seven rungs, then the table reduced to a one-line-per-rung cheat sheet.
Chapters 11–14: re-include conceptual tables of the participant classes' approximate ownership share and turnover share (rounded, labelled per standard 3, with one sentence on why the methodology is imperfect); cite Positioning & Flows for the measured versions.
Chapter 15: merge the Direction and Observability columns into one.
Chapter 16: extend from three worked identifications to six, covering at least one from each of holders, intermediaries, speculators, and issuers/sovereigns; keep one that fails.
Chapter 18: the twelve edges as paragraphs (mechanism, holder, capacity, competitor, killer in prose), then a concise summary table.
Chapter 20: extend the worked theses from three to six — two that pass, and one failing at each of Q1, Q2, Q4, and Q6 (the existing Q3 and Q5 failures stay) — so every question has a failure example.
Chapter 21: open with a plain paragraph defining the four books (A allocation, B swing, C tactical, D no fixed horizon — take the definitions from the Doctrine Part IV and cite it); then paragraphs, then the concise table. Also add the four books to the prerequisites note at the head of the paper.
Chapter 24: paragraphs per horizon, then the nine-column table reduced to a cheat sheet.
Chapter 26: convert the table to a paragraph with bullets per environment.
Appendix A (d): the register items as paragraphs, then a concise table.
Appendix B.3: elevate the hypothesis — which edge families a small book can reach and why — into Chapter 22 as a standing argument; leave the dated scorecard in B.3 with a pointer to Chapter 22.

Bump the masthead to Version 1.1 — September 2026; keep 26 chapters; re-run the internal cross-reference audit; regenerate the HTML edition; run make library-check (0 failures, 0 warnings); commit as "XXV Draft 1.1 — operator review revisions; presentation standard" and stop. Report the new word count and which chapters changed most.
