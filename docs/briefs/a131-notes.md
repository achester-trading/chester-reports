# A131 notes: the annual-review tooling (the library programme's L-5)

Paste A131, 6 Nov 2026, session A. Branch `a131-annual-review-tooling` from `origin/main` at `ee04ba21`. The paste is `33f95b1d`. Merges Monday in chain-13. It is needed before XXXII's corpus pass on 16 Jan 2027.

## Orders read first

- `docs/change-order-library-programme-2026-11-06.md` (on `origin/b129-five-filings`), L-5 and R-6: "Instrument 2 recomputes every dated-appendix figure from the point-in-time store with `available_at`, and diffs against tolerance. Instrument 3 is the relationship health check, returning holding / weakening / broken / re-attached for each Appendix A(b) regularity. The papers that lack an A(b) are listed, not failed."
- Audit 2, section 5.1 (`docs/white-paper-library-audit-2.md`), Instruments 2 and 3.
- XXXII, The Annual Structural Review (`origin/library-xxxii`), for the review's shape:
  - Part II, the four instruments;
  - Part III, section 9, the per-paper record;
  - Part IV, the January corpus pass and its ranking;
  - section 15, the appendix rule.

## What was built

| Piece | Where |
|---|---|
| Both instruments, `figures`, `relationships`, `all`, `count` | `tools/annual_review.py` |
| Tolerances, formats and the grading rule (session-set) | `config/annual_review.yaml` |
| `make annual-review [DB=PATH]`; `bash scripts/make.sh annual-review [--db PATH]` | `Makefile`, `scripts/make.sh` (one target each) |
| How the 16 Jan pass uses the two files with XXXII's questionnaire | `docs/runbooks/annual-review.md` |
| The gate | `tools/validate_annual_review.py`, 33/0 |

**Instrument 2.**
- **What counts as a figure.** A dated appendix is a `## Appendix ...` heading that says "dated". A figure is a number with a decimal point, a %, a bp or a $; bare integers (years, counts, item numbers) are not figures.
- **Series and date.** Its sentence must name the series by the D7 convention: "(FRED DGS10)", mapped to the store key through the FRED pull, or a backticked registered key. Its date is "on <date>" after it, or "<date> (<value>)" before it, or the sentence's only date when that date reads "on <date>" and the sentence has one figure.
- **Recomputation.** The figure is recomputed at its own date from the store as of the appendix's stated date (end of day ET, `available_at` respected), using the newest vintage knowable then. An appendix with no stated date uses the figure's date plus `grace_days` (7).
- **The diff.** It is taken under the series family's tolerance:
  - a rate 1bp absolute;
  - a spread 2bp;
  - a price 0.5% relative;
  - a release 0.2% relative;
  - everything else 1% relative.

  A "bp" figure is divided by 100 against a series stored in percent.
- **Unrecomputable.** Anything else in a dated appendix is listed, never guessed: no series key, a key the store does not carry, or no date.
- **Output.** `docs/reviews/annual-review-figures-<date>.md`.

**Instrument 3.**
- **What counts as a row.** A relationship row is a line in an Assumptions and Falsifiers appendix's part (b). It names two series, a sign ("positive" / "negative") or a range ("between -0.6 and -0.2"), and a window. "lag N months" and "levels" are optional.
- **The windows.** Correlations of the monthly changes are computed over three windows:
  - the stated window;
  - the trailing window (three years to the last stored month);
  - the window between them.
- **The grade.** By the config's rule:
  - **holding:** the sign agrees and |ρ| is at least half the stated window's and at least 0.10;
  - **weakening:** the sign agrees but the strength falls short;
  - **broken:** the trailing sign is opposite;
  - **re-attached:** holding now, after an opposite sign between the windows.
- **Ranges.** A range claim holds inside its range.
- **Thin windows.** Fewer than 24 months in a window is "insufficient (n=k of 24)", never graded.
- **Everything else.** Other lines of part (b) are listed with why they are not relationship rows. Papers without an Appendix A(b) are listed, not failed.
- **Output.** `docs/reviews/annual-review-relationships-<date>.md`.

**Read-only and not a gate.**
- The store is opened `mode=ro` (the gate proves its hash unchanged).
- No paper is written (the gate proves the fixture paper's hash unchanged).
- `all` exits 0 even with no store.
- `tools/annual_review.py` declares no `GATE_KIND`, so it is in no gate list.

## What the parser finds on main's papers

`python -m tools.annual_review count`, on main at `ee04ba21` (27 papers by the roster's file pattern):

| | Count |
|---|---|
| Figures in dated appendices | **190** |
| Recomputable (series key, value and date) | **8**, all in Rates and Liquidity's dated records (DGS10 ×7, DFII10 ×1) |
| Unrecomputable | **182**: 179 with no series key in the sentence, 3 with no date for the value |
| Relationship rows in the Appendix A(b) form | **0** |
| Claims in a part (b) not in that form | **1** (the Reporting System's "Regularities with dates", a prose claim naming no series) |
| Papers without an Appendix A(b) | **26**; the Reporting System is the one paper with the appendix |

**What the counts say.**
- **Unrecomputable figures.** Most of the unrecomputable figures are thresholds, budgets and counts in the Reporting System's and the Doctrine's dated tables. Others are quoted levels whose sentence does not name a series key. Both lists are the Instrument 1 work list the runbook describes: each paper's first review inventories its dated figures with their series, its Appendix A(e).
- **Regularities.** The relationship form has no rows on main yet, because no paper's part (b) states a regularity as two series, a sign or range, and a window. Writing those rows is the first reviews' work. The runbook gives the form, and the gate proves the grading on a fixture paper.

**A run against the laptop's store** (into the scratchpad, not committed): the 8 recomputable figures read "not stored at its date". The laptop's FRED history starts in 2022 and ends 21 Sep 2026, before the October dates. The January run reads the box's store, which holds the ALFRED history.

## Gates (one at a time, foreground)

| Gate | Result |
|---|---|
| validate_annual_review | 33/0 |
| check_library (the runbook's links) | 27 papers, 0 failures, 0 warnings |
| validate_gates | 32/0 |
| validate_deploy (the Makefile, the shim) | 155/0 |
| check_registry | OK |

Also run, all clean:
- validate_audit_3a 88/0, validate_names 20/0, validate_secrets 58/0;
- validate_config_refs 148/0, validate_stitch_tools 21/0, validate_numeral_audit 181/0;
- check_master_guide 0 failures (its one warning is main's own: the Guide's as-of predates the newest change order).

**Counts** (`stitch_counts.py --write`): 168 code gates (165 Python, 3 shell), 8 data gates.

## For the operator

- **Every tolerance and grading threshold is session-set,** for the first corpus pass to overrule: `weak_ratio` 0.5, `min_abs` 0.10, `trailing_years` 3, `min_months` 24.
- **The January run is the box's:** `make annual-review DB=~/chester-data/chester.db`, inside a window, the week before 16 Jan 2027. The two files it writes under `docs/reviews/` are the corpus pass's inputs. Committing them is the review session's call.
