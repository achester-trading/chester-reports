# library-ei-figures: Evidence and Inference's five figures (session A, A74, 24 Oct 2026)

**What it is.** The five computed figures of *Evidence and Inference* (XXIII), which the paper has carried as placeholders since September.

**Branch:** `library-ei-figures` from `origin/main` at `41803980`, in the library worktree `../chester-lib31`. It merges by its own pull request after the operator reads it.

## Figures drawn: five

All five are drawn by a new script, `tools/figures/evidence_inference.py`, beside the Master Guide's figure script. Each figure is computed from the paper's own formulas and worked numbers, deterministically (nothing sampled), and written as SVG in the house style to `docs/figures/evidence-inference/fig-01.svg` … `fig-05.svg`.

| # | Chapter | What it computes |
|---|---|---|
| 1 | 1 | The 95% interval on a true 0.2R edge, 0.2 ± 2/√n, the table's six sample sizes marked |
| 2 | 2 | A Sharpe of 1.0's error bar, SE = √((1 + S²/2)/T), at one and two standard errors; T = 1, 5, 10 marked (1.22, 0.55, 0.39) |
| 3 | 9 | Three priors on a true 60% hit rate along the expected path: weak Beta(3,3), 58% after 30; the sceptic's 80 decisions at 50%, Beta(40,40), 53% after 30; the mechanism's 40 at 60%, Beta(24,16) |
| 4 | 14 | The fraction of full Kelly against the edge's standard error as a share of the edge, by two rules, with quarter-Kelly and the Doctrine's 0.75%-of-10% lines and the paper's sample sizes |
| 5 | 15 | An edge decaying from week 40, the trailing 13-week expectancy with a one-standard-error band at 200 decisions a year; the band first excludes the old edge at week 65 |

## The body change: placeholders only

**The placeholders.** Each `*[Figure N — computed figure; not yet drawn …]*` line is replaced by its image link and caption, `![Figure N — caption](../figures/evidence-inference/fig-0N.svg)`. Nothing else in the body changes.

**One masthead sentence also changes.** The status line said the figures "have never been drawn; the placeholders below are where they go", which would now be false. It reads "Its five computed figures are drawn from the paper's own formulas (24 October 2026)". The masthead is not the body, but it is listed here.

**Two descriptions follow, in place.**
- The library guide's at-a-glance row and its one-page entry said "5 figure placeholders — none drawn"; they now say "5 computed figures in `docs/figures/`".
- The Master Guide's Table 9 row is changed the same way.

## The September artwork, replaced

`docs/figures/evidence-inference/` already held artwork from the 19 September docs batch, labelled A1, A2, A3, A5 and A6 (no A4). It was never wired into the paper, because its numbering did not match the paper's five placeholders, and its index left the mapping to the operator.

The paste's instruction (draw each from the paper's own formulas) settles it. By subject, the paper's Figures 1–5 are A1, A2, A3, A5 and A6. The five new files replace `fig-01`, `fig-02`, `fig-03` and `fig-05`, `fig-04` is new, and `fig-06` is removed. The September files remain in the repository's history (commit `c37870da`). The index is rewritten to say so.

**One difference between the old artwork and the paper:** A6 said "about week 60"; the paper says "roughly week sixty-five", and Figure 5 is drawn to the paper. The decay is illustrative: linear from 0.2R at week 40 to zero at week 66, which puts the first exclusion at week 65.

## Figure 4, and a sentence the paper's formula does not reach

Chapter 14 says that, at the uncertainty a two-hundred-decision sample implies, the growth-optimal fraction "sits near or below quarter-Kelly". The paper states no formula for this. So Figure 4 draws two standard rules:

- **Bayesian shrinkage of the estimated edge**, m²/(m²+s²), stays well above quarter-Kelly at 200 decisions (about 0.89 of Kelly, at s/m ≈ 0.35).
- **Sizing to the edge's lower two-standard-error bound**, 1 − 2s/m, sits near a third of Kelly at 200 raw decisions, and near none at Chapter 3's effective 60.

The paper's sentence matches the second rule, not the first. The figure shows both and says so in its foot line. No text in the body was changed (needs you 1).

## Gates

| Gate | Result |
|---|---|
| `tools/check_library.py` | 27 papers, 0 failures, 0 warnings (check 4: figures 1–5, no gaps; every link resolves) |
| `tools/check_master_guide.py` | 0 failures |
| The SVGs | all five parse |
| The paper's HTML edition | rebuilt with its builder, 5 figures embedded; the Master Guide's HTML rebuilt |

`make figures` covers only the Currencies charts (`altdata/fx_charts.py`), so the new script runs on its own. There is no figure gate beyond `check_library`'s check 4.

## CI

| Run | On | Result |
|---|---|---|
| read once after the push | the tip | see the report |

## Needs you

1. **Figure 4 and Chapter 14's sentence.** Only the lower-bound rule puts 200 decisions near quarter-Kelly. Either the sentence names that rule (a body edit, yours to rule), or the figure keeps both, as drawn.
2. **Look at the five once.** They were drawn by coordinates; no renderer is installed on the laptop.
