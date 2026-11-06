# hb-lv-divergence ledger -- Item 118's high-beta / low-vol divergence: the S&P 500 up 0.5% while SPHB/SPLV falls 2%, and the S&P's next 1, 5 and 20 sessions

**Edition:** 2026-11-06, laptop run, public sources. A re-run against the box's store supersedes it (a new dated file).

**The pass rule is pre-registered** (ruled 17 Oct 2026): the rule the order states; where it states none, the rule the first (laptop) edition wrote is the registration. A box re-run may not change it, only apply it.

| | |
|---|---|
| As of | 2026-11-06 |
| Window | 2011-05-06 (SPHB's and SPLV's first common session) to 2026-11-06 |
| n | 9 |
| Statistic | the S&P 500's +1, +5 and +20 session returns after each event: n, mean, median, share negative, beside the same over every session of the window |
| Pass rule (as the order states it) | none stated -- the order names no pass rule ("the flag earns rights only after an event-study backtest"); this first edition is that backtest and sets none (pre-registered: docs/ledgers/hb-lv-divergence-preregistration-2026-11.md) |
| Verdict | **NO GATE IN THE ORDER -- base rate recorded. The order names this study but states no pass rule; none is supplied here, by judgment or otherwise. A gate, if one is wanted, is the operator's to pre-register.** |
| Rights consequence | None: the ledger grants nothing. The flag prints with "no rights until the backtest"; this backtest enters no composite, flag table, the T&B intake queue or the market-state object. |

## Sources and vintages

- spx: yahoo ^GSPC
- sphb: yahoo SPHB
- splv: yahoo SPLV
- read 2026-11-06T22:43:23+00:00

## Results

V-100a holds: on 2026-11-04 the S&P 500 closed +1.58% (at least +0.5%) and SPHB/SPLV -2.73% (at most -2%); the order's first row is the backtest's own event for that session.

**9 events** from 2011-05-06 to 2026-11-06 (3900 sessions screened); 3 fall within 20 sessions of the event before them, so their forward windows share days.

| Horizon | Events: n | Mean | Median | Share negative | All sessions: n | Mean | Median | Share negative |
|---|---|---|---|---|---|---|---|---|
| +1 | 9 | -1.40% | -1.00% | 67% | 3899 | +0.05% | +0.07% | 46% |
| +5 | 8 | -0.29% | +0.97% | 38% | 3895 | +0.25% | +0.39% | 40% |
| +20 | 8 | +2.81% | +4.56% | 12% | 3880 | +0.99% | +1.49% | 33% |

Pending (window not closed, not counted): +5: 1, +20: 1.

The most recent events:

| Session | S&P 500 | SPHB/SPLV | +1 | +5 | +20 | Marked |
|---|---|---|---|---|---|---|
| 2020-03-02 | +4.60% | -2.01% | -2.81% | -11.12% | -15.00% | backtest event |
| 2020-03-17 | +6.00% | -4.25% | -5.18% | -3.24% | +10.05% | backtest event (overlaps) |
| 2020-04-09 | +1.45% | -2.20% | -1.01% | +3.04% | +5.02% | backtest event (overlaps) |
| 2020-07-01 | +0.50% | -2.35% | +0.45% | +1.16% | +4.18% | backtest event |
| 2020-11-04 | +2.20% | -2.94% | +1.95% | +3.75% | +6.48% | backtest event |
| 2020-11-11 | +0.77% | -2.34% | -1.00% | -0.14% | +2.67% | backtest event (overlaps) |
| 2021-03-22 | +0.70% | -2.24% | -0.76% | +0.77% | +4.93% | backtest event |
| 2023-03-24 | +0.56% | -2.25% | +0.16% | +3.48% | +4.18% | backtest event |
| 2026-11-04 | +1.58% | -2.73% | -4.36% | pending | pending | the order's day (V-100a checked) |

## Caveats

- SPHB and SPLV are ETFs standing in for the S&P 500 High Beta and Low Volatility indices; their fees and tracking enter the ratio.
- Overlapping events share forward days, so the events' n overstates the independent observations.

The episodes are in `hb-lv-divergence-ledger-2026-11-06-episodes.csv`, beside this file.
