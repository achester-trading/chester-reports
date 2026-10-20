# ST-R5.43b ledger -- the global policy-diffusion index's lead on the OECD CLI

**Edition:** 2026-10-17, laptop run, public sources. A re-run against the box's store supersedes it (a new dated file).

| | |
|---|---|
| As of | 2026-09 |
| Window | 1985-02 to 2026-09 (index); the CLI from 1961-01 |
| n | 492 |
| Statistic | cross-correlation of the diffusion index with the OECD CLI 0-18 months later; the best lead and the value at 8 |
| Pass rule (as the order states it) | none stated (item 43: 'calibration ledger on the lead before modifier rights'; it does not say what the lead must show) |
| Verdict | **NO GATE IN THE ORDER -- base rate recorded. The order names this study but states no pass rule; none is supplied here, by judgment or otherwise. A gate, if one is wanted, is the operator's to pre-register.** |
| Rights consequence | Report only until the ledger; modifier after (the order). With no pass rule stated for the lead, the index stays report only: this ledger grants no modifier. |

## Sources and vintages

- bis: bis
- cli: oecd_cli G20
- cli_oecd: oecd_cli G7
- read 2026-10-17T23:56:48+00:00

## Results

The index runs 1985-02 to 2026-09 (500 months, from the first month 20 banks had a last move; 49 banks in the table). **Now: +0.27** (net share of banks whose last move was a cut).

**Against the G20 CLI:** the best lead is **13 months** (r +0.21, n 487); at the order's 8 months, r +0.12 (n 492).
Robustness, the G7 CLI: best lead 14 months (r +0.34), at 8 months r +0.21.

| Lead (months) | r, G20 CLI | n | r, G7 CLI |
|---|---|---|---|
| 0 | -0.258 | 500 | -0.268 |
| 1 | -0.198 | 499 | -0.200 |
| 2 | -0.136 | 498 | -0.128 |
| 3 | -0.080 | 497 | -0.058 |
| 4 | -0.031 | 496 | +0.008 |
| 5 | +0.011 | 495 | +0.066 |
| 6 | +0.048 | 494 | +0.117 |
| 7 | +0.083 | 493 | +0.165 |
| 8 | +0.116 | 492 | +0.208 |
| 9 | +0.147 | 491 | +0.248 |
| 10 | +0.176 | 490 | +0.284 |
| 11 | +0.196 | 489 | +0.312 |
| 12 | +0.208 | 488 | +0.331 |
| 13 | +0.210 | 487 | +0.340 |
| 14 | +0.205 | 486 | +0.341 |
| 15 | +0.196 | 485 | +0.336 |
| 16 | +0.181 | 484 | +0.326 |
| 17 | +0.164 | 483 | +0.311 |
| 18 | +0.144 | 482 | +0.293 |

The global PMI headline (S&P Global, by hand) is not stored; the order's own comparison with it is not in this ledger.

## Caveats

- Monthly levels are autocorrelated: the correlations describe, they do not test.
- The OECD CLI is a cross-check the order names, not the PMI itself.
- The BIS table's coverage changes over time; the index's denominator is the banks with a last move that month.

The episodes are in `st-r5.43b-ledger-2026-10-17-episodes.csv`, beside this file.
