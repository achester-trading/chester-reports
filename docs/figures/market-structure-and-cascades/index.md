# Figures — market-structure-and-cascades

Drawn on 26 October 2026 (B78) by `tools/figures/market_structure.py --db PATH`,
numbered by order of appearance in the paper (B74 ruling 3). The script opens the
store read-only and reads each observation day at its latest vintage. Figure 1 is
conceptual. Figures 3 and 5 are drawn from the laptop's store, and the box
regenerates them. Figures 2, 4, 6 and 7 hold no rows on the laptop: the paper
keeps their placeholders, and they are drawn at merge from the box's store.

| # | Caption | File |
|---|---|---|
| 1 | The cascade as a loop (conceptual, no series) | [`fig-01.svg`](fig-01.svg) |
| 2 | Dealer gamma and the session's range (`exposure.net_gex`, `yfinance.mkt_spy`) | not drawn: drawn at merge from the box's store |
| 3 | The stock–bond correlation's sign through regimes (`calc.corr_spy_tlt_60d`; here from the stored SPY and TLT closes by the correlation layer's method) | [`fig-03.svg`](fig-03.svg) |
| 4 | Leveraged funds' net in ES against the squeeze cases (`cftc.tff_lev_money_net_oi`) | not drawn: drawn at merge from the box's store |
| 5 | The volatility index through the cases (`fred.vix`) | [`fig-05.svg`](fig-05.svg) |
| 6 | Forced flow against depth (`levetf.aum`, `yfinance.mkt_spy`) | not drawn: drawn at merge from the box's store |
| 7 | Margin debt through the cases (`finra.margin_debit`) | not drawn: drawn at merge from the box's store |
