# ST-R5.44b ledger -- how wide average-member vs index drawdown gaps resolved

**Edition:** 2026-10-17, laptop run, public sources. A re-run against the box's store supersedes it (a new dated file).

| | |
|---|---|
| As of | 2026-10-16 |
| Window | 2022-09-29 to 2026-10-16; 52-week highs, horizon 126 sessions after each peak |
| n | 0 |
| Statistic | the index's drawdown less the average member's (points); for each wide-gap episode, whether the index's drawdown deepened (leaders fell) or the average member's narrowed (broadening) within six months |
| Pass rule (as the order states it) | Pre-registered by this first edition (the order states none): PASS if at least 5 wide-gap episodes (gap >= 15 points) are completed and the leaders fell (the index's drawdown deepened by 5 points or more within 126 sessions of the peak) in at least 60% of them; fewer than 5 completed: INSUFFICIENT, and no rate prints |
| Verdict | **INSUFFICIENT -- 0 completed episode(s), below the floor of 5; no rate prints** |
| Rights consequence | Report now; T&B via queue after ledger (the order). A PASS would let the gap's queue entry (44c) be filed for the operator's ruling, one candidate at a time; INSUFFICIENT or FAIL keeps it report-only. This ledger grants nothing, and 44c is not filed (ruling 1 of 17 Oct 2026). |

## Sources and vintages

- SSGA's SPY holdings file, as of 2026-10-15 (membership; the constituent writer's reader)
- Yahoo daily closes, 5y, for its 503 members (the same reader)
- Yahoo ^GSPC daily closes
- read 2026-10-18T03:58:27+00:00

## Results

The gap (the index's drawdown from its 52-week high less the average member's) runs 2022-09-29 to 2026-10-16: **+15.7 points now** (index -2.0%, average member -17.7%, 500 members)

Wide-gap episodes (>= 15 points): **3**, of which **0 completed** (126 sessions after the peak). No rate prints below the floor of 5 completed episodes.

| Peak | Gap | Index / average member at peak | Deepest index after | Best member after | Resolution | Completed |
|---|---|---|---|---|---|---|
| 2026-05-13 | +17.0 | +0.0% / -17.0% | -4.5% | -13.7% | unresolved | no |
| 2026-07-15 | +16.1 | -0.5% / -16.6% | -3.9% | -13.7% | unresolved | no |
| 2026-10-07 | +18.8 | -0.2% / -19.0% | -2.0% | -17.5% | unresolved | no |

**Sourced comparisons (the order's read, item 44; never episodes of ours):**

- Share of S&P members above their 50-day: about 70% to 21% in 3Q26
- 40% of members 20% or more off their highs; 40% 10-20% off; 18% within 10%; 2% at a record
- The average member 20.1% below its high (Raymond James via Lemand, 3Q26)

## Caveats

- Today's members only: a member that fell out of the index is not in the history, so past gaps read narrower than a point-in-time list would show (survivorship).
- Price closes, not total return; an index drawdown is the S&P 500's own, not the members' cap-weighted average.
- The store's member closes reach two years back; a box re-run reads them, so its first 52-week window starts a year in.

The episodes are in `st-r5.44b-ledger-2026-10-17-episodes.csv`, beside this file.
