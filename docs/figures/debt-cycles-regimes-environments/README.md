# Figures: Debt Cycles, Regimes, and Environments (Draft 1)

No figure is drawn in Draft 1. Each entry below is a placeholder: what the figure
would show, and the stored series it would be drawn from. When a figure is drawn,
it becomes `fig-NN.svg` in this directory, this README becomes the `index.md`
mapping number to caption to file, and the paper links it in place of its
placeholder text (Appendix A (e)).

| # | What it would show | Drawn from |
|---|---|---|
| 1 | The long cycle in one panel: federal debt to output and net interest to revenue, as far back as the store holds, with the five tops of Part III marked | `calc.fed_debt_total_pct_gdp`, `calc.interest_to_receipts` |
| 2 | r against g: the real effective rate on the debt against real growth, with the repression era shaded | `calc.r_minus_g` and its average and marginal forms |
| 3 | The branch tells: the ten-year breakeven, the ten-year real yield and the gold front future on one axis, with the proposed rule's state as a band | `fred.breakeven_10y`, `fred.tips_10y`, `calc.r_real_10y_cpi`, `yfinance.mkt_gold_front` |
| 4 | The stock–bond correlation through regimes, inflation and disinflation shaded | `calc.corr_spy_tlt_60d` |
| 5 | Five tops, from inside: the diagnostic's first appearance, the top and the resolution per instance, in months from the top | The cited episode dates (Tops and Bottoms, Base Rates); not a stored series |
| 6 | The environment matrix: Chapter 14's table as a grid shaded by direction, each row's instance count beside it | The paper's Chapter 14; not a stored series |
