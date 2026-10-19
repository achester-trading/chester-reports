# ST-R4.17b ledger -- net liquidity's 13-week change against the S&P

**Edition:** 2026-10-17, laptop run, public sources. A re-run against the box's store supersedes it (a new dated file).

| | |
|---|---|
| As of | 2026-10-14 |
| Window | 2003-03-19 to 2026-07-15 (weeks with a full next 13 weeks); the series to 2026-10-14 |
| n | 1218 |
| Statistic | correlation of net liquidity's 13-week change with the S&P's next and same 13 weeks, all weeks and 2022-2023; the next 13 weeks by quintile and by leading leg |
| Pass rule (as the order states it) | none stated (item 17: 'modifier rights only after a calibration ledger vs SPX') |
| Verdict | **NO GATE IN THE ORDER -- base rate recorded. The order names this study but states no pass rule; none is supplied here, by judgment or otherwise. A gate, if one is wanted, is the operator's to pre-register.** |
| Rights consequence | Report-only until the ledger; modifier after (the order). The order states no pass rule, so this ledger grants no modifier: the series stays report-only in Plumbing until the operator rules a gate. |

## Sources and vintages

- walcl: fred WALCL
- tga: fred WTREGEN
- rrp: fred RRPONTSYD
- spx: yahoo ^GSPC
- read 2026-10-18T01:53:54+00:00

## Results

**Now (2026-10-14):** net liquidity $5,872bn; 13 weeks -115bn (Fed +13, TGA -127, RRP -0; led by TGA (transient)), 4 weeks +8bn.

| Correlation of the 13-week change with | All weeks | 2022-2023 |
|---|---|---|
| the S&P's NEXT 13 weeks (from the Friday after the release) | r +0.09 (n 1218); non-overlapping r +0.09 (n 94) | r +0.52 (n 104) |
| the S&P over the SAME 13 weeks (the popular read) | r -0.15 (n 1231) | r +0.58 (n 104) |

The S&P's next 13 weeks by quintile of the 13-week change (every week +2.57%, n 1218):

| Quintile of the change | Bounds ($bn) | Next 13 weeks (mean) | n |
|---|---|---|---|
| 1 | below to -74 | +2.66% | 244 |
| 2 | -74 to +2 | +2.81% | 243 |
| 3 | +2 to +28 | +1.62% | 244 |
| 4 | +28 to +146 | +2.49% | 243 |
| 5 | +146 to above | +3.28% | 244 |

The top quintile's next 13 weeks by its leading leg:

- balance sheet (durable): +2.42% (n 168)
- TGA (transient): +4.92% (n 50)
- RRP (little left): +5.67% (n 26)

## Caveats

- Weekly observations overlap by 12 of 13 weeks: n 1218 weeks is about 93 independent quarters, the non-overlapping row's n.
- FRED's current vintage of the H.4.1 legs, not ALFRED's: revisions to WALCL and WTREGEN are rare and small.
- RRPONTSYD prints only when the facility operated; a week with no print in the seven days before reads 0.

The episodes are in `st-r4.17b-ledger-2026-10-17-episodes.csv`, beside this file.
