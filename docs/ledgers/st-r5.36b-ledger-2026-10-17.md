# ST-R5.36b ledger -- months-of-supply crossings and the real house price 12 months on

**Edition:** 2026-10-17, laptop run, public sources. A re-run against the box's store supersedes it (a new dated file).

| | |
|---|---|
| As of | 2026-09 |
| Window | A. 2012-01 to 2026-09; B. 2012-01 to 2026-09; C. 1963-01 to 2026-08 |
| n | 0 |
| Statistic | the real house price's change 12 months after each months-of-supply crossing (with the mortgage rate rising), against every month's |
| Pass rule (as the order states it) | none stated (item 36: 'base-rate ledger: real house-price change 12 months after months-of-supply crossings') |
| Verdict | **NO GATE IN THE ORDER -- base rate recorded. The order names this study but states no pass rule; none is supplied here, by judgment or otherwise. A gate, if one is wanted, is the operator's to pre-register.** |
| Rights consequence | Flag only (the house-price-decline watch leading the T&B Reinhart-Rogoff input). Which months-of-supply series and line the flag uses is a ruling still open; this ledger grants nothing. |

## Sources and vintages

- redfin_mos: redfin MONTHS OF SUPPLY
- census_mos: fred MSACSR
- mortgage: fred MORTGAGE30US
- hpi: fred CSUSHPINSA
- cpi: fred CPIAUCSL
- read 2026-10-17T23:56:45+00:00

## Results

| Row | Window | Crossings (with 12 months after) | Real HPI 12m after (mean) | Falling | Every month (mean, n) |
|---|---|---|---|---|---|
| A. Redfin, the order's 6-month line | 2012-01 to 2026-09 | 0 (0) | n/a | 0 of 0 | +3.82% (162) |
| B. Redfin, its own 80th percentile (5.00 months) | 2012-01 to 2026-09 | 3 (3) | +4.09% | 0 of 3 | +3.82% (162) |
| C. Census new homes (MSACSR), 6 months | 1963-01 to 2026-08 | 19 (8) | -0.26% | 5 of 8 | +1.58% (462) |

**Redfin's series begins 2012-01**: 177 months. Row A's n is 0; an n under 5 allows a description of the episodes and no inference about the rule. Redfin's latest (2026-09): 4.1 months, the 69th percentile of its own history; the order's line is 6.

## Caveats

- n (the table's first number in brackets, row A) counts crossings with a full 12 months after them; the headline n is row A's.
- Rows B and C answer the open ruling's two options; neither is the order's flag until it is ruled.
- Redfin's months of supply is not seasonally adjusted.
- The real house price (Case-Shiller national over CPI) begins in 1987, so row C's crossings before then have no 12-month figure: its n counts only those after.

The episodes are in `st-r5.36b-ledger-2026-10-17-episodes.csv`, beside this file.
