# library-xxxii: The Annual Structural Review, Draft 1 (session A, A73, 24 Oct 2026)

**What it is.** Paper XXXII, the Annual Structural Review protocol, at the numeral Audit 2 reserved for it:
- Audit 2 Part 5;
- Part 7's Phase 2 row: "XXXII The Annual Structural Review (protocol + the standing register as a file the gate reads)";
- decision 1 of 7 September 2026.

**File:** `docs/whitepapers/annual-structural-review-whitepaper.md`, with the register at `docs/reading/structural-review-register.yaml`.

**Branch:** `library-xxxii` from `origin/main` at `41803980`, in the library worktree `../chester-lib31`. It merges by its own pull request after the operator reads it.

## Size

**About 4,250 words** (4,239, whitespace-split). The paste asks for about 4–6k, and the audit's roster row says about 5k.

## What it contains

- **Part I:** the four questions a review asks: mechanism, empirical claims, the dated appendix, tactical applications by horizon. Then the decision per section, and what the review is not.
- **Part II:** the audit's four instruments, and which is built.
- **Part III:** the questionnaire, verbatim from Audit 2 §5.1: the ten adversarial questions, the three forced inputs and the per-paper record.
- **Part IV:** the calendar.
- **Part V:** the standing register and who writes it.
- **Part VI:** the gate.
- **Part VII:** the log.
- **Part VIII:** a review worked through (*Credit*, illustrative, no figures).
- **Appendices:** A, dated, the register at seeding; B, Assumptions and Falsifiers.

## The register

`docs/reading/structural-review-register.yaml`. The audit names the file only as "the standing register"; the paste names this path.

**Twenty-eight papers.** Every paper on main's roster, plus XXXII itself, seeded from the guide's at-a-glance rows and each masthead. The dates:
- Each masthead's date where it gives one; a month-only date is that month's first.
- The Monthly manual gives no date, so it carries 2026-09-06, its first commit's date. Rates and Liquidity carries its anchor date of 30 August.
- `last_reviewed` is null for all, and the status is "never reviewed".
- XXVII and XXXI, on open branches, are noted for rowing at their merge.

**Fifteen changes.** The audit's §5.3 table of what could change, every row "watching".

**Format.** One flow-style line per row, so the gate reads it without a YAML parser. `check_library.py` is standard library only, and the regex is in check 15.

## The calendar: a difference from the audit

The audit puts the whole review in January. The paste asks for "which papers in which month, spread across the year". The protocol keeps January for the corpus pass (Instruments 2 and 3, the corpus questionnaire, the ranking) and spreads the papers from February to December, two or three a month. The reason is in Part IV: the attention budget's two-hour sitting holds three or four papers.

No paper on today's roster passes thirteen months in the first cycle (2027). The oldest, Tops and Bottoms (May 2026), is reviewed in February.

## The gate: what was changed, and what is proposed

The paste says to propose the gate change in the notes and not edit the gate unless the audit's text specifies it. **The audit's text does specify the warning** (§5.2): "library-check warns when any paper's last-reviewed date is more than thirteen months old". So `tools/check_library.py` gains **check 15**, which reads the register on every run:
- a warning when a roster paper has no row;
- a warning when a paper's clock (the last review, or the version date while never reviewed) is past thirteen months;
- a warning when a row names a paper the roster lacks.

**Today:** no warning. On 1 July 2027, with no review held, it warns for Tops and Bottoms (tested).

**Proposed, not adopted:** the audit's second check, "fails when a paper's appendix (b) is missing". Two of the 27 papers on main's roster carry an Assumptions and Falsifiers appendix (*Price, Time, and Edge* and the Reporting System), so it would fail 25 papers on its first run. XXXII §15 proposes adopting it shelf by shelf, by a ruling that names the date.

## What the gate forced

As for XXXI (A72):
- the REGISTRY gains `"XXXII": "annual-structural-review"`;
- the guide gains **one placeholder at-a-glance row**, marked as a placeholder;
- the Master Guide's map places XXXII in "How to decide and judge evidence", serving Books A–D, and Table 9 gains one row;
- Figure 5 is regenerated;
- both HTML editions are built.

`check_library`: 28 papers, 0 failures, 0 warnings. `check_master_guide`: 0 failures.

## The guide's one-page entry, drafted for review (not written into the guide)

> ## XXXII. The Annual Structural Review
> **Companion to: every paper in the library, and the library gate · v1.0 Draft 1 · ~4,250 words, eight parts + two appendices · 24 Oct 2026**
>
> **What it contains.** The protocol that makes the library's review a mechanism, not an intention.
> - Part I is the four questions a review asks of every paper, and the per-section decision: reaffirm, amend, rewrite, retire.
> - Part II is the four instruments: the Assumptions and Falsifiers appendix, the dated-figure recomputation, the relationship health check and the structural scan.
> - Part III is the questionnaire: ten adversarial questions and three forced inputs.
> - Part IV is the calendar: January for the corpus, the papers from February to December.
> - Part V is the standing register, the file the gate reads.
> - Part VI is the gate's thirteen-month warning, and the proposed failing check.
> - Part VII is the log, and Part VIII a review worked through.
>
> **Timeless takeaways:**
> - **The absence of an edit is a recorded decision** — a paper whose claims all held gets a one-line log entry, and that line is the review.
> - **The expensive part runs without the operator** — the recomputation and the health check run before the sitting, so the two hours go on judgment.
> - **List what lies outside the papers** — the register of what could change is reviewed on a schedule, with a rule for when it becomes a subject.

## CI

| Run | On | Result |
|---|---|---|
| read once after the push | the tip | see the report |

## Needs you

1. **Read Draft 1.** It merges by its own pull request.
2. **The calendar's departure from the audit's all-in-January:** keep it, or review everything in January.
3. **The failing check on a missing appendix (b):** the date from which it fails, or keep it proposed.
