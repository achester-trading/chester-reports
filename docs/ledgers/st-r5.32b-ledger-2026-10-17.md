# ST-R5.32b ledger -- the oil-shock classifier: supply-shock episodes and what followed

**Edition:** 2026-10-17, laptop run, public sources. A re-run against the box's store supersedes it (a new dated file).

| | |
|---|---|
| As of | 2026-10-14 |
| Window | 2000-06-21 to 2026-10-14 (classifier); trailing 5,040 sessions for the percentiles, from 2,520 until 20 years exist |
| n | 3 |
| Statistic | episodes of the two-condition regime; mean S&P and 60/40 returns 63 and 126 sessions after each start against every day's |
| Pass rule (as the order states it) | none stated (item 32 asks for a 'base-rate ledger of SPX and 60/40 forward returns conditional on the regime') |
| Verdict | **NO GATE IN THE ORDER -- base rate recorded. The order names this study but states no pass rule; none is supplied here, by judgment or otherwise. A gate, if one is wanted, is the operator's to pre-register.** |
| Rights consequence | A sub-state (inflation.driver) and a Book A rule-table modifier: oil and commodities to the hedge sleeve while the regime is on. With no gate in the order, the sub-state stays as built in Tranche 1 and this ledger grants no modifier. |

## Sources and vintages

- brent: fred DCOILBRENTEU
- spx: yahoo ^GSPC
- y10: fred DGS10
- read 2026-10-17T23:56:39+00:00

## Results

The classifier ran on 6,228 sessions (2000-06-21 to 2026-10-14): **3 episodes**, merging runs fewer than 22 sessions apart. The regime is **ON** on 2026-10-14: Brent-SPX -0.33 (the 2nd percentile), Brent-10y +0.52 (the 100th).

| Horizon | S&P after an episode start (mean, n) | S&P, every day | 60/40 after a start | 60/40, every day |
|---|---|---|---|---|
| 63 sessions | -4.17% (n=3) | +2.03% (n=6,165) | -1.41% | +1.57% |
| 126 sessions | -4.53% (n=3) | +4.23% (n=6,102) | -1.86% | +3.24% |

What item 25's quadrant did in the two quarters after each episode: not built (the quadrant does not exist yet; no stand-in is used).

## Caveats

- Six-month windows of daily changes are noisy, as the order warns; episodes are few and overlapping horizons are not independent.
- The 60/40's bond leg is a constant-duration approximation, stated.
- Brent's daily history begins May 1987, so 20-year percentiles exist only from about 2007; earlier days use every correlation from ten years.

The episodes are in `st-r5.32b-ledger-2026-10-17-episodes.csv`, beside this file.
