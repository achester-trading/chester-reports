# ST-R6.71d ledger -- The air pockets against the fragility panel (item 71)

**Edition:** 2026-10-23, laptop run, public sources. A re-run against the box's store supersedes it (a new dated file).

**The pass rule is pre-registered** (ruled 17 Oct 2026): the rule the order states; where it states none, the rule the first (laptop) edition wrote is the registration. A box re-run may not change it, only apply it.

| | |
|---|---|
| As of | SPY to 2026-10-23; ProShares NAV to 2026-10-22; FINRA to 2026-09; Z.1 to 2026-04-01 |
| Window | sessions from 2015-01-02 to 2026-10-16, each with five sessions after; each percentile over the five calendar years to its session |
| n | 2965 |
| Statistic | the fragility flag (the Amihud stand-in and the leveraged-ETF arm) before the three air pockets, and the share of sessions followed within five by an SPY fall of 2.5% or more, flag on against flag off |
| Pass rule (as the order states it) | the pre-registration's (docs/ledgers/air-pocket-preregistration-2026-10.md): with at least 20 flag-on sessions (else INSUFFICIENT), the flag -- SPY's Amihud measure at or above its 90th percentile of five years, standing in for depth, and the leveraged-ETF rebalance estimate above its 90th -- is on in at least one of the five sessions before at least two of the three air pockets, and the share of flag-on sessions followed within five sessions by an SPY fall of 2.5% or more is at least twice the flag-off share |
| Verdict | **FAIL -- on before 0 of 3 air pockets (rule: 2); a fall within five sessions after 31.1% of flag-on sessions against 6.4% of flag-off (rule: at least twice)** |
| Rights consequence | Would grant nothing by itself: the flag keeps a flag's rights, and any T&B or Book C modifier is the operator's ruling after this ledger (item 71). Stated, not granted: the verdict reaches the register only as a rule-31 draft, and no right changes until the operator accepts it. |

## Sources and vintages

- Yahoo daily bars (through altdata.import_yfinance): SPY open, high, low, close and volume, unadjusted; QQQ and ^GSPC closes
- ProShares' keyless NAV history files (accounts.profunds.com): TQQQ, SQQQ, QLD, UPRO, SPXU, SSO, SDS, through the writer's parser
- FINRA's margin statistics workbook (finra.margin_debit, through the writer's parser); FRED graph CSV: BOGZ1LM893064105Q
- retrieved 2026-10-23T23:35:10+00:00
- pre-registration: docs/ledgers/air-pocket-preregistration-2026-10.md

## Results

- Sessions in the sample: 2965; flag on 135 (followed by a fall 42), off 2830 (followed by a fall 182).
- A fall of 2.5% or more within five sessions: flag on 31.1%, flag off 6.4%.
- For context, outside the rule: after sessions with SPY's 20-session realised volatility at its 90th percentile or above (328), 27.4%. Both arms rise with volatility, so part of any lift is volatility clustering.
- Dealer gamma is left out (no history before 6b's store): the flow arm is the leveraged-ETF estimate alone.

**2018-02: 2018-02-05** (SPY -4.18%). The flag was off in the five sessions before. Margin debt's share of Z.1 equity market value: 1.37% (2017-12).

| Session | Amihud, bp per $1bn | Percentile | Rebalance estimate | Percentile | Depth arm | Flow arm | Flag |
|---|---|---|---|---|---|---|---|
| 2018-01-29 | 1.93 | 24 | $-0.31bn | 77 | off | off | off |
| 2018-01-30 | 1.99 | 27 | $-0.50bn | 91 | off | on | off |
| 2018-01-31 | 1.85 | 19 | $+0.13bn | 45 | off | off | off |
| 2018-02-01 | 1.74 | 14 | $-0.28bn | 72 | off | off | off |
| 2018-02-02 | 1.88 | 21 | $-1.13bn | 100 | off | on | off |

**2024-08: 2024-08-05** (SPY -2.91%). The flag was off in the five sessions before. Margin debt's share of Z.1 equity market value: 0.95% (2024-06).

| Session | Amihud, bp per $1bn | Percentile | Rebalance estimate | Percentile | Depth arm | Flow arm | Flag |
|---|---|---|---|---|---|---|---|
| 2024-07-29 | 2.45 | 56 | $+0.36bn | 21 | off | off | off |
| 2024-07-30 | 2.50 | 58 | $-2.56bn | 79 | off | off | off |
| 2024-07-31 | 2.58 | 59 | $+5.59bn | 98 | off | on | off |
| 2024-08-01 | 2.62 | 60 | $-4.93bn | 96 | off | on | off |
| 2024-08-02 | 2.71 | 62 | $-4.79bn | 96 | off | on | off |

**2025-04: 2025-04-03** (SPY -4.93%). The flag was off in the five sessions before. Margin debt's share of Z.1 equity market value: 0.98% (2025-02, marked).

| Session | Amihud, bp per $1bn | Percentile | Rebalance estimate | Percentile | Depth arm | Flow arm | Flag |
|---|---|---|---|---|---|---|---|
| 2025-03-27 | 2.75 | 69 | $-1.08bn | 44 | off | off | off |
| 2025-03-28 | 2.86 | 71 | $-5.30bn | 97 | off | on | off |
| 2025-03-31 | 2.72 | 68 | $+0.25bn | 13 | off | off | off |
| 2025-04-01 | 2.67 | 67 | $+1.41bn | 53 | off | off | off |
| 2025-04-02 | 2.62 | 65 | $+1.44bn | 54 | off | off | off |


## Caveats

- The Amihud measure stands in for depth, which is not tracked: the verdict is about the stand-in.
- Each air pocket's margin share uses the latest FINRA month ending 25 or more days before it (FINRA publishes about three weeks after the month) and the Z.1 quarter at or before that month, marked to SPX; it is printed, not scored.
- Three air pockets are a record of three readings, not a sample; the base rate is the second question.

The episodes are in `st-r6.71d-ledger-2026-10-23-episodes.csv`, beside this file.
