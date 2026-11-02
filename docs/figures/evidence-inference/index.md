# Figures — evidence-inference

Drawn on 24 October 2026 (A74) by `tools/figures/evidence_inference.py`, each from
the paper's own formulas and worked numbers; deterministic, nothing sampled.
Conceptual figures: no figure in them is data. Rerun the script to redraw them.

**What they replaced.** The 19 September 2026 docs batch delivered artwork labelled
A1, A2, A3, A5 and A6 (no A4), never wired into the paper because its numbering
did not match the paper's five placeholders. Drawing the five from the paper
itself settles the numbering: Figure 1 is A1's subject, 2 is A2's, 3 is A3's, 4
(Kelly) is A5's and 5 (edge decay) is A6's. The September files are in the
repository's history (commit `c37870da`); A6's "about week 60" is drawn here as
the paper's "roughly week sixty-five".

| # | Caption | File |
|---|---|---|
| 1 | The 95% interval on a true 0.2R edge narrows with the square root of the number of decisions | [`fig-01.svg`](fig-01.svg) |
| 2 | A Sharpe of 1.0 and its error bar: one year of data cannot tell it from zero | [`fig-02.svg`](fig-02.svg) |
| 3 | The same evidence, three priors: a process whose true hit rate is 60% | [`fig-03.svg`](fig-03.svg) |
| 4 | Kelly under an uncertain edge: the fraction of full Kelly falls as the edge's error bar grows | [`fig-04.svg`](fig-04.svg) |
| 5 | A 0.2R edge decaying from week 40 is not distinguishable from noise until about week 65 | [`fig-05.svg`](fig-05.svg) |
