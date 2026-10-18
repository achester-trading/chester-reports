# ST-R5.31b ledger -- post-peak paths of top-10 concentration at the 40-44% band

**Edition:** 2026-10-17, laptop run, public sources. A re-run against the box's store supersedes it (a new dated file).

| | |
|---|---|
| As of | 2026-10-15 |
| Window | 2021-10-18 to 2026-10-15 (back-cast from 2026-10-15); horizon 504 sessions after each peak |
| n | 0 |
| Statistic | the peak-day top ten's value against the rest of the members: its low within 24 months of the peak, the sessions to it, and breadth (share above the 50-day) at peak and trough |
| Pass rule (as the order states it) | Pre-registered by this first edition (the order states none): PASS if at least 5 episodes are completed and in at least 4 of every 5 the peak-day top ten fell 10% or more against the rest within 504 sessions (24 months) of the peak; fewer than 5 completed: INSUFFICIENT, and no rate prints |
| Verdict | **INSUFFICIENT -- 0 completed episode(s), below the floor of 5; no rate prints** |
| Rights consequence | Calibration of an existing overlay input; no new weight (the order). A PASS would let the peak-band flag be proposed as the Concentration & Complacency overlay's calibrated ceiling, for the operator to grant; INSUFFICIENT or FAIL keeps it report-only. This ledger grants nothing, and the queue entry (31c) is not filed. |

## Sources and vintages

- SSGA's SPY holdings file, as of 2026-10-15 (the constituent writer's reader, altdata/sources/sp500_members.py)
- Yahoo daily closes, 5y, for its 503 members (the same reader)
- read 2026-10-18T03:57:49+00:00

## Results

Our top-10 share (back-cast from SPY's holdings of 2026-10-15; 503 members) runs 2021-10-18 to 2026-10-15: **40.2% now**

Episodes at or above 40%: **3**, of which **0 completed** (504 sessions after the peak). No rate prints below the floor of 5 completed episodes.

| Peak | Share at peak | Leaders' low against the rest | Sessions to it | Completed | Above 50-day, peak / trough |
|---|---|---|---|---|---|
| 2025-10-29 | 41.9% | -20.4% | 163 | no | 43.29 / 63.2 |
| 2026-05-14 | 41.1% | -14.9% | 28 | no | 47.8 / 63.2 |
| 2026-10-07 | 41.0% | -4.1% | 6 | no | 28.49 / 44.02 |

**Sourced comparisons (BofA via the order, item 31; never episodes of ours):**

- Railroads: 63% at the peak
- 1920s utilities, telco, industrials: 36% at the peak
- Nifty Fifty: 40% at the peak
- Japan (of MSCI ACWI): 44% at the peak
- TMT: 41% at the peak
- 'AI Big 10' (Mag 7 + Broadcom, AMD, Micron): 42% at the peak

## Caveats

- Back-cast from one holdings day: today's members only, share counts held at that day's, so buybacks, issuance and index changes are not in the history (survivorship).
- BofA's baskets are defined ex post and its measures differ (Japan is a country share of ACWI); they are comparisons, not a sample.
- The store's own holdings begin 16 Oct 2026; the box's re-run back-casts from the store's newest holdings day the same way.

The episodes are in `st-r5.31b-ledger-2026-10-17-episodes.csv`, beside this file.
