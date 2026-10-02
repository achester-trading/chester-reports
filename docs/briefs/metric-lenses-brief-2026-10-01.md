# Brief — Metric lenses: each family of metrics measured its own way

| | |
|---|---|
| Status | **Ruled 2026-10-01 16:09 ET** — Ari: "yes and yes" (adopt per-family lenses, built in 6e; dual percentiles on every level metric). Thresholds marked *proposed* below are ratified at the Doctrine monthly (3–4 Oct). |
| Owner | Ari Chester |
| Binding on | Claude Code sessions building 6e and the Monthly |
| Placement | Built inside 6e (macro completeness, ~12 h planned) — this adds ~8–10 h. Displayed in the Monthly v2 tables; the Weekly and the close may adopt the same columns later. |
| Precedence | Below Part 26, the change orders and Amendments #4–#5. `altdata/derived.py` stays the one place a delta, percentile or z-score is computed. |

## Why

Every pillar metric today shows the same two columns — percentile of the level against five years, and a 20-session change — whatever the data is. A 20-session change on a monthly release is noise or nothing; a level percentile on a quantity that trends (the Fed's balance sheet) says little; a five-year percentile reads a 10-year yield as "100th" while it sits far below its long history. Each family should show the measures that reveal something about it.

## The lenses

Each registry series gets a `family` field; the family decides which forms are computed and shown.

| Family | Members (examples) | Forms |
|---|---|---|
| **price** | S&P 500, QQQ, IWM, sector ETFs, gold, oil, BTC | Returns 1m / 3m / 12m / YTD; drawdown from the 52-week high with a **correction** flag (≤ −10%) and **bear** flag (≤ −20%) *(thresholds proposed)*; 20-day realized volatility and its percentile; percentile of the 12-month return (not of the level) |
| **rate** | 2y, 10y, 30y, mortgage rate, real yields | Change in bp 1m / 3m / 12m; level percentile, five-year **and** full history |
| **spread** | HY, IG, CCC, BB OAS | Level percentile, five-year and since inception; bp change 1m / 3m; **widening** flag (≥ +100 bp in 3 months, *proposed*) |
| **release** | CPI, core PCE, payrolls, claims, retail sales | Year over year **and** 3-month annualized (momentum against trend); surprise against consensus where the events table holds one; **revision** line when the latest vintage changed a prior print ("Aug revised 3.1% → 3.3%") |
| **quantity** | Fed balance sheet, TGA, RRP, M2, reserves | Year-over-year change; 3-month change in units; direction of travel |
| **conditions** | VIX, NFCI, sentiment surveys | Level percentile; z-score; spike against the 1-year average |
| **ratio** | breadth (RSP/SPY), 2s10s, r-vs-g | Level percentile; 3-month trend |

## Rules

- **Dual percentiles.** Every level metric carries `pctile_5y` and `pctile_full` (the series' full stored history), each with its window and n; both print side by side.
- **The move's own percentile.** Where a change is shown, its percentile among that series' changes of the same length is available ("a −1.4% month at the 7th percentile of months"), via the existing `delta_percentile`.
- **Point-in-time.** Every form is computed only from data available at the as-of date; revision lines read the vintage store and never rewrite a published figure.
- **Units come from the registry** (bp for rates and spreads, percent for prices, units for quantities) — never inferred.
- **A form that cannot be computed** (too little history, no consensus) prints its reason, not a blank or a zero.
- **Ordinals** follow the 1 Oct rule: a precomputed `<field>_ordinal`, copied verbatim by any narrative.

## Gates

A fixture series per family producing the expected forms; a monthly series never shows a 20-session change; correction and bear flags at the declared thresholds; a revision line from a two-vintage fixture; both percentiles with their n.

## For the Doctrine monthly (3–4 Oct)

Ratify or change: the correction / bear thresholds (−10% / −20%), the spread-widening flag (+100 bp in 3 months), and the family assignment of any series that is ambiguous.
