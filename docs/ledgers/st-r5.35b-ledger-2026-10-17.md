# ST-R5.35b ledger -- the corporate-price/ULC gap and margins after its peaks

**Edition:** 2026-10-17, laptop run, public sources. A re-run against the box's store supersedes it (a new dated file).

| | |
|---|---|
| As of | 2026-04 |
| Window | 2014-07 to 2026-04 (the order's leg); 1975-01 to 2026-04 (robustness) |
| n | 6 |
| Statistic | the nonfinancial corporate profit share's change 4 and 8 quarters after each gap peak, against every quarter's; the margin-source attribution (price vs cost) by quarter |
| Pass rule (as the order states it) | none stated (item 35 asks for a 'base-rate ledger of margin behaviour after gap peaks') |
| Verdict | **NO GATE IN THE ORDER -- base rate recorded. The order names this study but states no pass rule; none is supplied here, by judgment or otherwise. A gate, if one is wanted, is the operator's to pre-register.** |
| Rights consequence | Flag only: the gap closing from above as a leading input to item 29's revisions-turn flag (built in Tranche 1). This ledger grants nothing new. |

## Sources and vintages

- ppi: fred WPSFD49116
- ppi_long: fred WPSFD4131
- ulc: fred ULCNFB
- profits: fred NFCPATAX
- gva: fred A455RC1Q027SBEA
- read 2026-10-17T23:56:42+00:00

## Results

**The latest quarter** (2026-04): PPI +4.8% on the year against unit labor costs +1.4%, a gap of +3.4 pp: the margin's source is **price**. Of 48 quarters since 2014-07, the source was price in 36.

**The order's PPI leg (WPSFD49116, from 2014-07):** 6 gap peak(s).
- Margin change over the next 4 quarters after a peak: mean +0.31 pp, falling after 3 of 6; every quarter's mean +0.27 pp (n=44)
- Margin change over the next 8 quarters after a peak: mean +1.24 pp, falling after 3 of 5; every quarter's mean +0.67 pp (n=40)

**Robustness, PPI finished goods less foods and energy (WPSFD4131, from 1975-01):** 25 gap peak(s).
- Margin change over the next 4 quarters after a peak: mean +0.46 pp, falling after 10 of 25; every quarter's mean +0.13 pp (n=202)
- Margin change over the next 8 quarters after a peak: mean +0.55 pp, falling after 10 of 24; every quarter's mean +0.24 pp (n=198)

## Caveats

- n is 6 on the order's series: the PPI leg begins in 2014. The long row is a different index.
- The profit share is a margin proxy at the national-accounts level, not the S&P's margin.

The episodes are in `st-r5.35b-ledger-2026-10-17-episodes.csv`, beside this file.
