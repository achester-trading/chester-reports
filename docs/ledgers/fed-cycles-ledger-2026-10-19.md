# FED-CYCLES ledger -- the hiking-cycle table, computed by rule

**Edition:** 2026-10-19, laptop run, public sources. A re-run against the box's store supersedes it (a new dated file).

**The pass rule is pre-registered** (ruled 17 Oct 2026): the rule the order states; where it states none, the rule the first (laptop) edition wrote is the registration. A box re-run may not change it, only apply it.

| | |
|---|---|
| As of | 2026-10 (latest month of the policy rate) |
| Window | 1954-07 to 2026-10 |
| n | 21 |
| Statistic | each hiking cycle's rise, length, the 10-year's change, the S&P 500 over and after it, and whether a recession followed within 24 months; split by that, never averaged across all cycles |
| Pass rule (as the order states it) | none in the order (Tranche H adopts the table). The cycle rule, pre-registered by this first edition: the monthly policy rate (FEDFUNDS' monthly average to 1982-09, the target at month-end from 1982-10, the range's midpoint from 2008-12); a turn is confirmed by a 75 bp reversal against the running extreme; a cycle runs from the first month above a confirmed trough to the first month at the next confirmed peak, and counts if the rise is at least 100 bp |
| Verdict | **NO GATE IN THE ORDER -- base rate recorded. The order adopts the table and states no pass rule; none is supplied here.** |
| Rights consequence | None: a base-rate table (SR-7's row grants no right). It is quoted beside the Warsh matrix and in the Base Rates paper's dated appendix as a table, never as a forecast. Stated, not granted: the verdict reaches the register only as a rule-31 draft, and no right changes until the operator accepts it. |

## Sources and vintages

- FRED graph CSV (no key): FEDFUNDS, DFEDTAR, DFEDTARL, DFEDTARU, GS10, USREC
- Yahoo ^GSPC daily closes through altdata.import_yfinance
- SR-21's episodes: docs/ledgers/sr-21-ledger-2026-10-18-episodes.csv

## Results

| Start | End | From | To | Rise (bp) | Months | 10y over the cycle (bp) | S&P over the cycle | S&P 12m after | Recession within 24m | SR-21 inside (conceded / refused) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1954-08 | 1957-10 | 0.80% | 3.50% | +270 | 39 | +167 | +33.0% | +25.0% | no | 0 / 0 |
| 1958-06 | 1959-11 | 0.63% | 4.00% | +337 | 18 | +161 | +32.2% | -4.7% | yes, after 6m | 0 / 0 |
| 1961-02 | 1961-02 | 1.45% | 2.54% | +109 | 1 | -6 | +2.7% | +10.3% | no | 0 / 0 |
| 1961-08 | 1966-11 | 1.17% | 5.76% | +459 | 64 | +124 | +20.5% | +16.8% | no | 0 / 0 |
| 1967-08 | 1969-08 | 3.79% | 9.19% | +540 | 25 | +153 | +0.8% | -14.6% | yes, after 5m | 0 / 0 |
| 1971-04 | 1971-08 | 3.71% | 5.57% | +186 | 5 | +88 | -1.3% | +12.2% | no | 0 / 0 |
| 1972-03 | 1973-09 | 3.30% | 10.78% | +748 | 19 | +101 | +1.7% | -41.4% | yes, after 3m | 0 / 0 |
| 1974-03 | 1974-07 | 8.97% | 12.92% | +395 | 5 | +85 | -17.6% | +11.9% | no | 0 / 0 |
| 1975-06 | 1975-09 | 5.22% | 6.24% | +102 | 4 | +37 | -8.0% | +25.5% | no | 0 / 0 |
| 1977-02 | 1980-04 | 4.61% | 17.61% | +1300 | 39 | +426 | +4.2% | +25.0% | yes, after 16m | 0 / 0 |
| 1980-08 | 1981-01 | 9.03% | 19.08% | +1005 | 6 | +232 | +6.5% | -7.1% | yes, after 7m | 0 / 0 |
| 1981-04 | 1981-06 | 14.70% | 19.10% | +440 | 3 | +35 | -3.5% | -16.5% | yes, after 2m | 0 / 0 |
| 1982-01 | 1982-04 | 12.37% | 14.94% | +257 | 4 | +15 | -5.0% | +41.2% | no | 0 / 0 |
| 1983-03 | 1984-08 | 8.50% | 11.50% | +300 | 18 | +200 | +12.6% | +13.2% | no | 2 / 0 |
| 1987-01 | 1987-09 | 5.88% | 7.31% | +144 | 9 | +231 | +32.9% | -15.5% | no | 1 / 0 |
| 1988-03 | 1989-05 | 6.50% | 9.81% | +331 | 15 | +65 | +19.7% | +12.7% | yes, after 15m | 2 / 0 |
| 1994-02 | 1995-02 | 3.00% | 6.00% | +300 | 13 | +172 | +1.2% | +31.4% | no | 2 / 0 |
| 1999-06 | 2000-05 | 4.75% | 6.50% | +175 | 12 | +90 | +9.1% | -11.6% | yes, after 11m | 0 / 2 |
| 2004-06 | 2006-06 | 1.00% | 5.25% | +425 | 25 | +39 | +13.3% | +18.4% | yes, after 19m | 0 / 0 |
| 2015-12 | 2018-12 | 0.12% | 2.38% | +225 | 37 | +57 | +20.5% | +28.9% | yes, after 15m | 0 / 1 |
| 2022-03 | 2023-07 | 0.12% | 5.38% | +525 | 17 | +197 | +4.9% | +20.3% | no | 0 / 2 |

The conditional table (completed cycles; no all-cycle average is printed, as the row rejects it):

| Recession began within 24 months of the last hike | n | Median rise (bp) | Median months | Median S&P 12m after |
|---|---|---|---|---|
| yes | 10 | +432 | 18 | -5.9% |
| no | 11 | +270 | 9 | +16.8% |

SR-21's rows inside the cycles: 7 conceded and 5 refused, read from docs/ledgers/sr-21-ledger-2026-10-18-episodes.csv (its episodes begin in 1983, so cycles before then carry none).

## Caveats

- Before October 1982 the rate is the effective rate's monthly average, not a target, so those cycles' start and end months can differ by a month or two from a narrative history.
- The S&P 500 is its price, not its total return.
- USREC is NBER's dating, published long after the fact: the recession column is a historical label, not something knowable at the last hike.

The episodes are in `fed-cycles-ledger-2026-10-19-episodes.csv`, beside this file.
