# ST-R6.66c ledger -- the wealth-effect impulse against real consumption growth

**Edition:** 2026-10-28, box run, public sources. 

**The pass rule is pre-registered** (ruled 17 Oct 2026): the rule the order states; where it states none, the rule the first (laptop) edition wrote is the registration. A box re-run may not change it, only apply it.

| | |
|---|---|
| As of | real PCE to 2026-08-01; Z.1 to 2026-04-01; SPX to 2026-10-28 |
| Window | Decembers 1960 to 2024, each with its twelve forward months |
| n | 65 |
| Statistic | Spearman's rho between each December's impulse (Z.1's household equity share, lagged three months for publication, times SPX's year-on-year return) and real PCE growth over the next twelve months; its halves; the terciles' median outcomes |
| Pass rule (as the order states it) | the pre-registration's (docs/ledgers/wealth-effect-preregistration-2026-10.md): Spearman rho between each December's impulse and real PCE growth over the next twelve months >= 0.20 with n >= 40, rho > 0 in each half split at the median year, and the impulse's top tercile's median outcome above the bottom tercile's; INSUFFICIENT under n 40 |
| Verdict | **FAIL -- rho +0.06 (rule >= 0.2), halves +0.13 and +0.12 (rule > 0), top tercile +3.74% against bottom +3.29% (rule: top above bottom)** |
| Rights consequence | None. The impulse stays report-only whatever the verdict, as ruled (item 66: 'report only until the ledger is built'); a verdict grants nothing by itself, and any later right is the operator's ruling. Stated, not granted: the verdict reaches the register only as a rule-31 draft, and no right changes until the operator accepts it. |

## Sources and vintages

- FRED graph CSV (no key): BOGZ1FL153064486Q, DPCERA3M086SBEA, current vintages
- Yahoo daily closes: ^GSPC (month-end closes)
- retrieved 2026-10-28T23:08:52+00:00
- pre-registration: docs/ledgers/wealth-effect-preregistration-2026-10.md

## Results

- rho over the whole sample: +0.06 (n 65)
- rho by half: +0.13 (Decembers 1960 to 1992), +0.12 (the rest)
- real PCE growth over the next twelve months, median: top tercile of the impulse +3.74%, bottom tercile +3.29% (k 21 each)

## Caveats

- Equity returns and consumption both follow the business cycle: a positive rho is consistent with a common cause as well as a wealth effect. The ledger claims no cause.
- Current vintages: BEA's and Z.1's revisions are not undone; no public source serves all three series' first prints.

The episodes are in `st-r6.66c-ledger-2026-10-28-episodes.csv`, beside this file.
