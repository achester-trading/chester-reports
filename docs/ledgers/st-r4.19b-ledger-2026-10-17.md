# ST-R4.19b ledger -- the MOVE-VIX divergence flag, replicated

**Edition:** 2026-10-17, laptop run, public sources. A re-run against the box's store supersedes it (a new dated file).

| | |
|---|---|
| As of | 2026-10-16 |
| Window | 2003-11-24 to 2026-10-16 (a 252-session z from 2002-11-12) |
| n | 39 |
| Statistic | non-overlapping watch- and strong-tier episodes: the share with the VIX higher within 1-3 months and the S&P lower at 3 months, against every day's, beside the study's 10/12 and 9/12 |
| Pass rule (as the order states it) | none stated (item 19: 'own calibration ledger replicating the study'; the queue entry follows once the ledger is written) |
| Verdict | **NO GATE IN THE ORDER -- base rate recorded. The order names this study but states no pass rule; none is supplied here, by judgment or otherwise. A gate, if one is wanted, is the operator's to pre-register.** |
| Rights consequence | Flag now; overlay via the queue after the ledger (the order). The flag stays as built in 19a; the queue entry is ST-R4.19c, after 'T&B full' and the operator's queue ruling. This ledger grants nothing. |

## Sources and vintages

- move: yahoo ^MOVE
- vix: yahoo ^VIX
- spx: yahoo ^GSPC
- read 2026-10-18T01:53:59+00:00

## Results

**Now (2026-10-16):** MOVE z +2.19 (percentile 94), VIX z +0.58 (percentile 81); tier: **none**. The conditioner is inactive: T&B is not built.

| | Episodes (complete) | VIX higher at 1, 2 or 3 months | S&P lower at 3 months | S&P at 3 months (mean) |
|---|---|---|---|---|
| Watch tier (strong included) | 40 (39) | 24 of 39 (62%) | 13 of 39 (33%) | +2.09% |
| Strong tier | 28 (27) | 19 of 27 (70%) | 9 of 27 (33%) | +2.24% |
| Every day (the base) | 5,603 days | 68% | 29% | |
| The study, as the order records it | 12 | 10 of 12 | 9 of 12 | strong: every case negative |

The replication's window starts 2003-11-24: Yahoo's ^MOVE begins 2002-11-12, and the first z needs 252 sessions. The study counts from 2000, so its earliest instances are outside this window.

## Caveats

- Small n, as the order warns: the episodes are counted, not tested.
- The z window includes the day itself (19a's rule); the study's own window was not stated (verify item 3: the ruling's one year is used).
- The conditioner cannot be applied: T&B's bottom signal does not exist yet.

The episodes are in `st-r4.19b-ledger-2026-10-17-episodes.csv`, beside this file.
