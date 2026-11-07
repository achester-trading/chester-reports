# Runbook: the annual review's computed instruments

**What this is.** The two computed instruments of the Annual Structural Review (the library's protocol for re-examining every paper once a year), built as the library programme's L-5 (`docs/change-order-library-programme-2026-11-06.md`, L-5 and R-6) from Audit 2's section 5.1 (`docs/white-paper-library-audit-2.md`):
- **Instrument 2,** the dated-figure recomputation;
- **Instrument 3,** the relationship health check.

They run before the January corpus pass, the first on 16 Jan 2027, so the session reads numbers rather than computing them. Instruments 1 (the Assumptions and Falsifiers appendix) and 4 (the structural scan's questionnaire) are the papers' and the session's, not code.

**What it never does.** It never writes a paper, never writes the store (it opens it `mode=ro`), and never sets an exit code. It is not a gate and is in no gate list.

## Running it

On the box, inside a window, the week before the corpus pass:

```
make annual-review DB=~/chester-data/chester.db
bash scripts/make.sh annual-review --db ~/chester-data/chester.db     # without make
```

Either form writes two files under `docs/reviews/` and prints their paths:

| File | What it holds |
|---|---|
| `annual-review-figures-<date>.md` | a table per paper (the figure, the printed value, the recomputed value, the difference, the verdict), the unrecomputable list, and a one-line count |
| `annual-review-relationships-<date>.md` | each relationship row's stated-window and trailing-window correlation, the window between them, and its grade (holding / weakening / broken / re-attached); the claims in part (b) not in the relationship form; the papers without an Appendix A(b) |

One instrument alone: `python -m tools.annual_review figures [--paper <slug>]` or `relationships`. A dry count that parses without the store: `python -m tools.annual_review count`.

The laptop's store does not reach far enough back for most dated figures. Its FRED history starts in 2022, so run it against the box's store.

## How the corpus pass uses the two files

The Annual Structural Review's January pass:
- runs Instruments 2 and 3 for every paper;
- answers the corpus questionnaire;
- ranks the papers by how many broken or weakening claims each carries.

In that sitting:

1. **Broken first.** Read the relationships file's **broken** rows before anything else: each is a place where a paper is now teaching something false. A paper with a broken claim is pulled forward into February, whatever its scheduled month.
2. **Then weakening and re-attached.** A weakening claim goes on its paper's review as a question. A re-attached one is recorded with both windows' numbers, because a relationship that broke and came back is a different claim from one that never broke.
3. **The ranking.** Count broken and weakening rows per paper from the relationships file, and write the ranking into the corpus log.
4. **The figures file.** A figure **beyond tolerance** is a dated value the store now reads differently: a revision, a vintage or a misprint. Its paper's review refreshes the appendix from the store and says so in its log. A figure "not stored at its date" names a series the store does not reach; the review notes the gap.
5. **The unrecomputable list is the Instrument 1 work list.** Each line is a figure that names no stored series, or names it without a date. The fix belongs to the paper's own review: its Assumptions and Falsifiers appendix, part (e), inventories each dated figure with the series it is recomputed from. The figure's sentence should name its series by the D7 convention, "(FRED DGS10)" or a backticked store key.
6. **The papers without an Appendix A(b)** are listed, not failed (the protocol's section 15). Each one's first review writes the appendix.
7. **The questionnaire.** Its adversarial questions and its three forced scans are answered in writing in the corpus log, with the two files cited by name and date.

## The formats the tool reads

**A figure** sits in a dated appendix: a level-2 heading `## Appendix ...` that says "dated". A figure is a number with a decimal point, a %, a bp or a $, and its sentence names the series. Its date is "on <date>" after it, or "<date> (<value>)" before it, or the sentence's only date when the sentence has only one figure. The as-of is the heading's "as of <date>"; otherwise the figure's date plus `grace_days`.

**A relationship row** is a line in an Assumptions and Falsifiers appendix, inside its part (b). Part (b) opens at a line starting "**(b)" or "**Regularities". The row names:
- two series, as a figure does;
- a sign ("positive" / "negative") or a range ("between -0.6 and -0.2");
- a window ("1990 to 2019", or "1990-01 to 2019-12");
- optionally "lag N months" (the second series N months after the first) and "levels" (otherwise month-on-month changes).

**The settings** are `config/annual_review.yaml`: the tolerances per family and the grading rule (`weak_ratio`, `min_abs`, `trailing_years`, `min_months`). Every value is session-set; the first corpus pass may overrule any of them.
