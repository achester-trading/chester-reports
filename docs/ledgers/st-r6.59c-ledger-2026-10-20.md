# ST-R6.59c ledger -- The bank-stress base rate: the correction-vs-crisis classifier (item 59)

**Edition:** 2026-10-20, laptop run, public sources. A re-run against the box's store supersedes it (a new dated file).

**The pass rule is pre-registered** (ruled 17 Oct 2026): the rule the order states; where it states none, the rule the first (laptop) edition wrote is the registration. A box re-run may not change it, only apply it.

| | |
|---|---|
| As of | 2026-10-20 |
| Window | KRE 2006-06-22 to 2026-10-20; each percentile over the five years before its session |
| n | 18 |
| Statistic | the classifier's most severe state within 20 sessions of each episode's start, against its crisis or correction label |
| Pass rule (as the order states it) | At least 8 episodes and at least 2 crisis episodes, else INSUFFICIENT; PASS when every crisis episode (a start in 2007-07-01 to 2009-03-31 or 2023-03-01 to 2023-05-31) reaches funding watch or banking stress within 20 sessions of its start AND at least two-thirds of the correction episodes stay correction; FAIL otherwise (docs/ledgers/bank-stress-preregistration-2026-10.md) |
| Verdict | **FAIL (crises caught 2 of 2; corrections stayed correction 6 of 16, the rule needs two-thirds)** |
| Rights consequence | Would grant: a T&B overlay intake-queue entry (ST-R6.59d, the Liquidity & Funding Stress family), only after "T&B full" and its place in the queue. The flags and the classifier stay report-only either way. Stated, not granted: the verdict reaches the register only as a rule-31 draft, and no right changes until the operator accepts it. |

## Sources and vintages

- FRED graph CSV (no key): SOFR, IORB, IOER, DCPF3M, DTB3, WLCFLPCL, BOGZ1FL403069330Q, DPSSCBW027SBOG, WRMFNS, BAMLH0A0HYM2; Yahoo daily closes: KRE, ^GSPC; retrieved 2026-10-20T20:39:49+00:00
- WRMFNS (retail money funds) stands in for ICI's total: ICI's file refuses an identified client

## Results

| Start | KRE, 20 sessions | Label | Class | Reached on | Funding above (read) | Deposit flag | SPX +63s | SPX +252s | HY OAS +63s |
|---|---|---|---|---|---|---|---|---|---|
| 2007-08-03 | -13.1% | crisis | banking stress | 2007-08-31 | fin_cp+dw (3) | on | +5.3% | -12.8% | not served |
| 2010-05-20 | -16.1% | correction | funding watch | 2010-06-11 | none (3) | on | +0.4% | +25.4% | not served |
| 2011-08-04 | -10.2% | correction | correction | — | none (3) | off | +3.2% | +15.9% | not served |
| 2012-06-05 | -10.1% | correction | correction | — | none (3) | off | +9.3% | +27.8% | not served |
| 2015-01-28 | -10.7% | correction | correction | — | fhlb (3) | off | +5.2% | -5.4% | not served |
| 2015-08-25 | -11.4% | correction | funding watch | 2015-08-25 | fin_cp+dw (3) | off | +11.7% | +16.5% | not served |
| 2016-01-11 | -10.4% | correction | funding watch | 2016-01-11 | fin_cp+dw (3) | off | +7.2% | +17.9% | not served |
| 2016-06-27 | -14.9% | correction | funding watch | 2016-07-18 | fin_cp+dw (3) | off | +7.3% | +20.9% | not served |
| 2018-10-18 | -11.6% | correction | funding watch | 2018-11-05 | sofr_iorb+fhlb (4) | off | -4.9% | +8.6% | not served |
| 2020-02-27 | -10.6% | correction | funding watch | 2020-03-17 | sofr_iorb+fin_cp (4) | off | +1.7% | +27.9% | not served |
| 2021-07-06 | -10.5% | correction | correction | — | none (4) | off | -1.0% | -11.5% | not served |
| 2022-04-13 | -10.0% | correction | correction | — | none (4) | off | -13.1% | -6.6% | not served |
| 2023-03-08 | -10.9% | crisis | banking stress | 2023-03-17 | dw+fhlb (4) | on | +6.9% | +28.3% | not served |
| 2023-08-23 | -10.5% | correction | funding watch | 2023-09-01 | fhlb (4) | on | +2.3% | +27.0% | not served |
| 2024-02-06 | -10.0% | correction | funding watch | 2024-03-01 | none (4) | on | +4.7% | +21.6% | -46 bp |
| 2024-12-23 | -10.6% | correction | funding watch | 2024-12-27 | sofr_iorb (4) | on | -4.7% | +16.0% | +42 bp |
| 2025-10-16 | -12.1% | correction | funding watch | 2025-10-31 | sofr_iorb+dw (4) | off | +4.7% | +16.0% | -39 bp |
| 2026-03-06 | -10.2% | correction | correction | — | none (4) | off | +9.6% | n/a | -37 bp |

**Forward S&P 500 by class** (not part of the pass rule):

- correction: n 6; median +63 sessions +4.2%, +252 sessions -5.4%.
- funding watch: n 10; median +63 sessions +3.5%, +252 sessions +19.4%.
- banking stress: n 2; median +63 sessions +6.1%, +252 sessions +7.8%.

## Caveats

- SOFR starts in April 2018: before it the funding flag reads at most three members and still needs two.
- FRED serves the ICE BofA HY OAS for recent years only; earlier episodes print 'not served' on that leg.
- A weekly series counts from the first Friday after its reference date, as registered; H.8's real lag is longer, so the deposit leg is read a little early.

The episodes are in `st-r6.59c-ledger-2026-10-20-episodes.csv`, beside this file.
