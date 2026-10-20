# ST-R5.30b ledger -- investor equity allocation and the S&P's 10-year forward return

**Edition:** 2026-10-17, laptop run, public sources. A re-run against the box's store supersedes it (a new dated file).

| | |
|---|---|
| As of | 2026-04 |
| Window | 1945-10 to 2016-07 (forward decades); allocation history 1945-10 to 2026-04 |
| n | 266 |
| Statistic | OLS of the 10-year forward annualised total return on the aggregate equity allocation; R2; the current reading's fitted value and residual band |
| Pass rule (as the order states it) | none stated (item 30 names the regression as the base rate; the queue entry follows 'after a calibration ledger') |
| Verdict | **NO GATE IN THE ORDER -- base rate recorded. The order names this study but states no pass rule; none is supplied here, by judgment or otherwise. A gate, if one is wanted, is the operator's to pre-register.** |
| Rights consequence | Book A modifier (the rule-table line drafted 16 Oct, 'inactive until ST-R5.30b's ledger is filed') and the T&B intake queue (ST-R5.30c, after this ledger and 'T&B full', part 2). With no gate in the order, neither is granted here: activating either is the operator's ruling. |

## Sources and vintages

- NCBEILQ027S: fred NCBEILQ027S
- FBCELLQ027S: fred FBCELLQ027S
- TCMILBSHNO: fred TCMILBSHNO
- TCMILBSNNCB: fred TCMILBSNNCB
- TCMILBSNNB: fred TCMILBSNNB
- FGTCMDODNS: fred FGTCMDODNS
- SLGTCMDODNS: fred SLGTCMDODNS
- DODFFSWCMI: fred DODFFSWCMI
- BOGZ1FL153064486Q: fred BOGZ1FL153064486Q
- shiller.sp_price: shiller shiller.sp_price
- shiller.sp_dividend: shiller shiller.sp_dividend
- read 2026-10-17T23:56:31+00:00

## Results

Regression of the S&P's annualised 10-year forward total return on the aggregate allocation, quarterly: **forward return = 31.25 -0.633 x allocation (pp)**, R2 0.74, n 266 quarters (1945-10 to 2016-07; about 6.7 independent decades).
Robustness, the household share (BOGZ1FL153064486Q): forward return = 22.67 -0.532 x share, R2 0.55, n 266.
**The current reading** (2026-04, Z.1's latest quarter): allocation 54.2%, the 100th percentile of 305 quarters since 1945-10. On the fitted line it implies -3.1% a year over the next decade; the residuals' 10th-90th percentile band puts it between -5.8% and -0.0% (median residual -0.3 pp).
The latest observed residual (2016-07, the last quarter with a full forward decade) is +8.5 pp, the 100th percentile of the residuals.

## Caveats

- Overlapping decades: the R2 and the band are descriptive, not a test.
- DODFFSWCMI's FRED page says 'Seasonally Adjusted Annual Rate' though its title says Level (flagged on st-r5-index); it enters as a level.
- The construct follows the paper's published description; its own values were not re-fetched to compare.

The episodes are in `st-r5.30b-ledger-2026-10-17-episodes.csv`, beside this file.
