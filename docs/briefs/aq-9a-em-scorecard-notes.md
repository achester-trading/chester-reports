# AQ-9a: the EM vulnerability scorecard — notes (11 Oct 2026)

Branch `aq-9a-em-scorecard`, from `origin/main` at `989b49b`, not merged. Change
order "Alternative Assets Quarterly" §4.5 (the scorecard paragraph) and §10.

**What it is.** One table of country × lens, never a composite (§26.8). Each cell
carries:

- the latest value, with its data-as-of date;
- its percentile over ten years, as an ordinal with n;
- its change on the quarter;
- its rank in the column, where #1 is the most vulnerable.

Every series is `trigger_eligible: false`.

## Base: main, with a shared client

I built on **main, not on `imf-ifs-gold`**. The SDMX 3.0 client and the
publication-date handling from `imf_ifs.py` are generalised into
`altdata/sources/_imf_sdmx.py`. It parses any IMF dataflow's series into
`{dimension: code}` and `{period: value}`, and reads the publication instant as
the later of `PUBLICATION_DATE` and `UPDATE_DATE`.

Building on `imf-ifs-gold` would have made this branch wait on an unmerged one.
`imf_ifs` can move onto the shared client once both are on main; nothing here
imports it.

## Sources

All are free and answer without a key; each was checked on 10–11 Oct 2026.

| Lens or input | Source | Request | Lag on 11 Oct 2026 |
|---|---|---|---|
| Current account, fiscal balance, government debt (% GDP); GDP in USD | IMF WEO, `IMF.RES:WEO` + vintage flows | one request per edition | April and October editions; the current edition is April 2026 (published 14 Apr, updated 15 Apr); October 2026 is due mid-October; latest year 2025 (an estimate) |
| Reserves (total, gold at market value, USD) | IMF IL `TRGMV_REVS` | one request | most countries Aug 2026; Korea and Saudi Arabia Jul; China Jun; Taiwan Apr |
| Goods imports (CIF, USD) | IMF ITG `MG` | one request | May–Jun 2026 (four to five months) |
| CPI, % year on year | IMF CPI `_T` `YOY_PCH_PA_PT` | one request | Jul–Sep 2026 (one to three months) |
| Policy rate | BIS `WS_CBPOL`, CSV | one request | Sep 2026 for most; India Jun, Korea Jul |
| External debt, total and short-term (USD) | World Bank QEDS (SDDS, API source 22) | two requests | 2026Q1 (updated 7 Aug 2026), China 2025Q4 |

**Writers.** Four source writers and a lens pass run in the feeds' official
group, in this order: `imf_weo`, `imf_em`, `bis_cbpol`, `wb_qeds`, then
`em_lenses`.

- **One writer per source.** The feeds check marks every key of a writer stale
  when its pull fails, so a BIS outage does not stale the IMF series.
- **First pull is the backfill.** Each writer's first pull writes whatever history
  its source serves.
- **Re-pulls write nothing.** The second pull wrote 0 rows in a live run.
- **Failure writes nothing.** On failure a writer is STALE and the store keeps the
  last good vintage.

**WEO vintages.** Every configured WEO flow (the current one, `WEO_2025_OCT_VINTAGE`
and `WEO_2026_APR_VINTAGE`) is read on every pull. Each row is stamped with its
own flow's publication instant.

- China's 2025 debt is stored as two vintages: 96.3% from October 2025 and 99.2%
  from April 2026.
- An as-of read before April sees October's number.
- Projections (to 2031 in the response) are never stored.
- When the IMF lists a new vintage flow, add it to `config/em_scorecard.yaml`
  under `weo.dataflows`.

**The derived lenses** (`altdata/sources/em_lenses.py`):

| Lens | Built from |
|---|---|
| Reserves in months of imports | reserves over the trailing twelve months' average imports |
| Reserves / short-term external debt | reserves at the quarter-end over short-term external debt |
| External debt, % of GDP | QEDS external debt over WEO GDP, using the quarter's year where stored, else the latest full year |
| Real policy rate | the BIS policy rate less CPI inflation |
| Inflation against target | CPI inflation less the configured target |

- A lens row is knowable at the latest of its inputs' instants. Its
  availability kind is the least observed of theirs.
- A period missing an input has no row.
- The inflation gap applies today's target to the whole history. A past target
  change, such as China's 3% → 2% in 2025, is not modelled.

**The live run, 11 Oct 2026, into a throwaway store:**

| Writer | Rows written |
|---|---|
| `imf_weo` | 4,039 |
| `imf_em` | 18,768 |
| `bis_cbpol` | 4,700 |
| `wb_qeds` | 1,808 |
| `em_lenses` | 14,121 |

Spot checks:

- Brazil: external debt 37.5% of GDP (2026Q1), real policy rate +9.8 points
  (Aug), government debt 93.3% (2025).
- Malaysia: reserves 0.83× short-term debt.

## Not yet sourced (each prints "not tracked: <why>", never a blank)

| Country | Lens | Why | Candidate |
|---|---|---|---|
| Taiwan | reserves / ST debt, external debt % GDP | outside the World Bank's tables | the CBC's external debt statistics |
| Taiwan | real policy rate, inflation gap | no BIS policy rate or IMF CPI row; no formal target | the CBC discount rate; DGBAS CPI |
| UAE | months of imports | no IMF ITG row | IMF BOP goods debits (quarterly) or FCSC |
| UAE | reserves / ST debt, external debt % GDP | no QEDS row | CBUAE external debt data, if published |
| UAE | real policy rate | no BIS row | the CBUAE base rate |
| South Africa | months of imports | no IMF ITG row | IMF BOP goods debits (quarterly) or SARS |

Saudi Arabia, the UAE, Malaysia and Taiwan have no inflation target, so their
inflation-gap cell reads "not tracked: no inflation target", with the source.

## Readers

- **The Quarterly.** `em_scorecard.quarterly_block(st, now)` is the EM chapter's
  hook for AQ-1 to place. It is one sub-section in the stack's shape (title,
  table, notes, data), with each figure in its display form and percentiles as
  `_ordinal` only.
- **The Monthly.** `em_scorecard.monthly_line(st, now)` prints one line in the
  slow layers, as a new sub-section, "Emerging markets: the scorecard's quarter".
  It names the quarter's three largest deteriorations, by lens, each with its
  data-as-of date.
  - A deterioration is measured in percentile points toward the lens's worse
    side. That is the only unit the lenses share, because a percent of GDP,
    months of imports and a real rate are not comparable in their own units.
  - Until the store has held the lenses for a quarter, the line says the
    quarter's change cannot be read yet, rather than that nothing deteriorated.
- **CLI:** `python -m altdata.em_scorecard [--as-of YYYY-MM-DD]` prints the table
  and the line.

## Session-set readings (each changeable in the config)

- **The twelve largest EM by MSCI EM weight:** China, Taiwan, India, Korea, Brazil,
  Saudi Arabia, South Africa, Mexico, the UAE, Malaysia, Indonesia and Poland,
  plus Thailand. The tail reorders quarter to quarter; confirm it against the
  current factsheet.
- **Targets and their sources.** These are in the config. China's (2%, from the
  2025 Government Work Report) and South Africa's (3%, ruled November 2025) are
  marked "verify".
- **"Worse" directions.** A lower real policy rate counts as more vulnerable, as
  does inflation above target.
- **Change on the quarter** is the value knowable now less the value knowable 91
  days ago. So it captures a new period, a revision, or both.

## What the China panel (AQ-9b) still needs from AQ-3

- **TSF and the credit impulse.** PBOC aggregate financing stock and flow, and
  nominal GDP. AQ-3's list names "TSF and credit impulse"; no writer exists yet.
- **China property.** Starts, inventory months, developer spreads (AQ-3 names
  "China property").
- **The CNY/CNH fixing gap.**
  - The fix is stored (`cfets.cny_fix`) and onshore CNY is in the price feed
    (`mkt_usdcny`).
  - Offshore CNH is not tracked: Yahoo's CNH=X broke on 5 Oct (PB-1).
  - AQ-3 names "CNY/CNH fixing gap", so it needs a CNH source.
- **Capacity discipline.** Utilisation, module and cell prices, and the survival
  of subscale makers. No free source is named in AQ-3, so this needs a ruling on
  sources before AQ-9b can build it.

## Box commands (the operator, after the merge, inside the windows)

The writers then run nightly in the 16:10 official pass. To backfill at once
rather than wait:

```
cd ~/chester-reports && git pull --ff-only
.venv/bin/python -m altdata.sources.imf_weo
.venv/bin/python -m altdata.sources.imf_em
.venv/bin/python -m altdata.sources.bis_cbpol
.venv/bin/python -m altdata.sources.wb_qeds
.venv/bin/python -m altdata.sources.em_lenses
.venv/bin/python -m altdata.em_scorecard
```

Each writer prints `"status": "OK"` and its row count; the last command prints the
table.

## What the January edition can print

- **WEO:** the October 2026 edition, with 2025 as its latest year (an estimate).
- **Reserves:** through about November 2026 for most countries, September for
  China.
- **Months of imports:** through about September–October 2026, because imports
  lag.
- **Real rate and inflation gap:** through about November–December 2026.
- **External debt lenses:** through 2026Q2. 2026Q3 lands about February 2027.
