# Monthly Regime & Allocation — 2026-09-23

*As-of cutoff 2026-09-24T01:42:01.920475+00:00 · run `monthly-20260924T014201.920442Z` · pillar mapping pillars-v1*

*Six sections of change. The pillars are inputs to the three dials and appear beneath them; their detail is one delta row each in the appendix. No section computes a regime — every dial and dimension is read from the market-state object.*

> **Absences**
>
> - top_bottom: absent -- top_bottom.composite is not in the store. The Top & Bottom harness is not built -- it is a report in the registry and an unbuilt pipeline -- and this section reads its state variable rather than computing one, because a composite invented here would have no harness behind it and no way to be calibrated


> **narrative withheld: ANTHROPIC_API_KEY is not set (checked environment, then .env)**
>
> The paragraph is withheld rather than corrected: a figure the payload does not carry is a figure nobody can check, and the sections below are the record either way.

---

## I. Regime

*Object session 2026-09-23 · config market-state-v1.7 · method market-state-method-5 · against 2026-09-23*

### Dial: macro — **ABSENT** — held

*Absent: the declared rules read ['growth', 'inflation'] and ['growth', 'inflation'] are absent; the catch-all rule is for readings that disagree, not for readings that do not exist*


| Pillar | Weight | Reads dimension |
|---|---|---|
| 1 Labor Market Vitality | 0.25 | growth |
| 2 Macroeconomic Momentum | 0.20 | growth |
| 3 Systemic Liquidity | 0.20 | liquidity |
| 4 Inflation Dynamics | 0.20 | inflation |
| 7 Global Interconnectivity | 0.10 | rates |
| 8 Sovereign Health & Debt Cycle | 0.05 | *(none — no dimension covers debt sustainability. 31.2 rules that the)* |

### Dial: vol — **normal** — held

- Term structure, published by **challenger**: contango
- champion `calc.vx_front_ratio` contango (ratio 1.0500, pctile 37.3)
- challenger `calc.vix3m_over_vix` contango (ratio 1.2300, pctile 94.0)
- legs agree: yes · basis 3.07 vol points · dual run to 2026-12-23

- realized/implied: **implied_rich** (ratio 0.6200 = 9.16 / 14.87)


| Pillar | Weight | Reads dimension |
|---|---|---|
| 6 Valuation & Credit Spreads | 0.60 | credit |
| 5 Investor Sentiment & Positioning | 0.40 | volatility |
| 9 Banking System Health | 0.00 | credit |

### Dial: gamma — **negative** — held


*No pillar feeds this dial. Gamma is dealer positioning read from the option chain; no macro series bears on it, and a pillar mapped here would be decoration.*


### Dimensions

| Dimension | State | Previous Monthly | Pctile | Dir | Conf |
|---|---|---|---|---|---|
| growth | *absent* | — | — | — | low |
| inflation | *absent* | — | — | — | low |
| rates | *absent* | — | — | — | low |
| liquidity | *absent* | — | — | — | low |
| credit | *absent* | — | — | — | low |
| volatility | subdued | subdued | 20.6 | - | med |
| trend | flat | flat | 42.8 | - | med |
| breadth | narrow | narrow | 23.1 | - | med |

*5 of 8 dimensions are absent, each with its reason:*

- **growth** — the primary member fred.claims_4wk was last observed 2026-05-23, 84 sessions before this cutoff. Its own allowance is 8 sessions -- from its registry half_life at its own cadence, not a daily calendar -- and 3.0x that is 24. A state computed from it would be a stale state presented as a current one
- **inflation** — the primary member fred.breakeven_10y was last observed 2026-05-29, 80 sessions before this cutoff. Its own allowance is 2 sessions -- from its registry half_life at its own cadence, not a daily calendar -- and 3.0x that is 6. A state computed from it would be a stale state presented as a current one
- **rates** — the primary member fred.yield_10y was last observed 2026-05-28, 81 sessions before this cutoff. Its own allowance is 2 sessions -- from its registry half_life at its own cadence, not a daily calendar -- and 3.0x that is 6. A state computed from it would be a stale state presented as a current one
- **liquidity** — the primary member fred.rrp was last observed 2026-05-29, 80 sessions before this cutoff. Its own allowance is 2 sessions -- from its registry half_life at its own cadence, not a daily calendar -- and 3.0x that is 6. A state computed from it would be a stale state presented as a current one
- **credit** — the primary member fred.hy_oas was last observed 2026-05-28, 81 sessions before this cutoff. Its own allowance is 2 sessions -- from its registry half_life at its own cadence, not a daily calendar -- and 3.0x that is 6. A state computed from it would be a stale state presented as a current one


*Changed since the previous Monthly: none.*

### Exceptions

Open now: 1 · opened since the previous Monthly: 0 · closed: 0


### Contradictions

| Pair | State | z | Threshold | Sessions | Since |
|---|---|---|---|---|---|
| price_vs_breadth | closed | 1.63 | 2.0 | 0 | — |
| implied_vs_realized_vol | closed | 0.07 | 2.0 | 0 | — |
| gamma_vs_trend | closed | — | 2.0 | 0 | — |

---

## II. Scenarios — every weight with its Brier

*Grouped by scenario. grouped by SCENARIO, because config/scenario_families.yaml does not exist. The collapse of the twenty-five scenarios into ~6 mechanism families is 6f in the phase plan and is not done; until the mapping is config, grouping them here would be this report inventing a taxonomy that the tail watch and the Brier ledger would then disagree with*

**No probability has been emitted.** The ledger is seeded from a Monthly's own scenario table (probability_ledger.seed_from_monthly), so the first weights arrive when a Monthly with a scenario section is published -- and until one is, a Brier score would be a number about nothing

---

## III. Top & Bottom — a section, not a report

**Verdict and composite absent.** top_bottom.composite is not in the store. The Top & Bottom harness is not built -- it is a report in the registry and an unbuilt pipeline -- and this section reads its state variable rather than computing one, because a composite invented here would have no harness behind it and no way to be calibrated


### The bear-rally base rate, on the top-side language

From `baserate.drawdown_by_depth` (base-rates-method-1), over 12 bear markets: the largest counter-trend rally inside a decline runs **p25 +9.74%, median +13.48%, p75 +18.41%**, extreme +46.77%.


*31.1: the top-side language carries the bear-rally base rate, because that governs how a top call is HELD rather than how it is made. A short campaign inside a -20% decline faces three to five of these and each will look like the turn*


**Claims cited by id** — never retyped:

- `br.episode_1929_32`: -86% *(docs/whitepapers/base-rates-whitepaper.md, 11.2 and 11.6, as of 2026-09-06)*
  - ⚠ Small samples, given for the shape rather than the decimal. Thirteen bear markets is a sample of thirteen, and a quartile of it is not a distribution.
- `br.extended_tail_percentiles`: p95 of bad markets is -80% over 20-35 years *(docs/whitepapers/base-rates-whitepaper.md, 13.3, as of 2026-09-06)*
  - ⚠ Small samples, given for the shape rather than the decimal. Thirteen bear markets is a sample of thirteen, and a quartile of it is not a distribution.
  - ⚠ Survivorship operates at the level of the COUNTRY, not merely the company. A base rate built from markets that still exist is conditioned on survival, and the honest correction is not a smaller number but a wider distribution with mass at total loss.

---

## IV. Alternative Assets — a section, not a report

*A SECTION, NOT A REPORT. The Alternative Asset report is not produced by any pipeline here -- altdata/report/ is vendored content, nothing schedules it -- so this reads the store directly and says which families it cannot reach*

### digital — ok

*bitcoin from the price basket; the ZEC block from the 29.5 shielded-pool logger, including the shielded share of SUPPLY (not of transactions -- see that module)*

| Metric | Level | 20d change | Pctile | Conf |
|---|---|---|---|---|
| `yfinance.mkt_btc_usd` | 80,453.03 | +1.80 percent | 75.2 | low |
| `zec.price` | *absent* | — | — | — |
| `zec.shielded_value_share` | *absent* | — | — | — |
| `crypto.cap_share` | *absent* | — | — | — |

### energy — ok

*the oil fund and WTI spot*

| Metric | Level | 20d change | Pctile | Conf |
|---|---|---|---|---|
| `yfinance.mkt_uso` | 153.82 | +20.79 percent | 99.5 | low |
| `fred.wti` | 97.63 | — | 89.9 | low |

### metals — ok

*gold and silver funds; the store holds no spot metal*

| Metric | Level | 20d change | Pctile | Conf |
|---|---|---|---|---|
| `yfinance.mkt_gld` | 401.17 | -4.78 percent | 89.9 | low |
| `yfinance.mkt_slv` | 59.93 | -2.70 percent | 89.4 | low |

### real_assets — not_yet_sourced

*the chain-capture universe holds no REIT and the store no real-asset series, so this family is named and empty rather than quietly missing*

Needs: a REIT index series, a farmland or infrastructure proxy

---

## V. The register's month

*Window 2026-09-01 to 2026-09-24*

**No decision has reached its horizon.** nothing has reached a horizon yet, which is the expected state of a register days old


Open now: 2 · opened this month: 4 · closed: 0

- `SPY` long (draft, no state, no expression) — 2026-09-05
- `SPY` long (active, no state, no expression) — 2026-09-05
- `SPY` long (active, INVALIDATED, no expression) — 2026-09-19
- `SPY@MEXI.MXN` short (draft, no state, no expression) — 2026-09-19

### Rule breaks

Restricted-instrument attempts this month: **0** · running total 0

*Not yet sourced: allocation_floor_breach, book_b_conversion, time_stop_passed. each needs something the register does not carry -- a band-weighted stance, a book label and a closing reason, a time stop -- and a zero would read as 'no rule was broken'*

---

## Appendix — the pillar pages, as one delta table

*The old report's ten pillar pages, condensed to one delta row per series. A level says where a series is; the change says what it did, and the change is in the metric's OWN unit -- basis points for a spread, percent for a price, raw for a count -- taken from the registry rather than from one formula*

*59 series across 8 of 11 pillars.*

*Pillar 9 — Banking System Health has no series in the store: the 2008 and 2023 mechanisms both ran through this pillar and none of it is fetched today*

*Pillar 10 — Commentary & Narrative Flow has no series in the store: it is not a measurement. A desk-commentary roster feeds no dial, and giving it one would let prose move a regime.*

*Pillar 11 — Thailand / THB has no series in the store: relocated to docs/thailand-monitor-spec.md*

### Pillar 1 — Labor Market Vitality (dial: macro, weight 0.25, reads growth)

| Series | Level | 20d change | Pctile | Conf | Stale |
|---|---|---|---|---|---|
| `fred.avg_wkly_hours` | 34.30 | — | 57.1 | low | 121 |
| `fred.claims_4wk` | 209,000.00 | — | 15.0 | low | 85 |
| `fred.emp_pop_ratio` | 59.10 | — | 2.1 **!** | low | 121 |
| `fred.hires_total` | 5,554.00 | — | 54.2 | low | 144 |
| `fred.job_openings` | 6,866.00 | — | 6.2 | low | 144 |
| `fred.layoffs` | 1,867.00 | — | 95.8 **!** | low | 144 |
| `fred.lfp_rate` | 61.80 | — | 2.1 **!** | low | 121 |
| `fred.lt_unemp` | 1,833.00 | — | 91.7 | low | 121 |
| `fred.nfp` | 158,736.00 | — | 100.0 **!** | low | 121 |
| `fred.quits_rate` | 2.00 | — | 33.3 | low | 144 |
| `fred.u3_rate` | 4.30 | — | 91.7 | low | 121 |

### Pillar 2 — Macroeconomic Momentum (dial: macro, weight 0.20, reads growth)

| Series | Level | 20d change | Pctile | Conf | Stale |
|---|---|---|---|---|---|
| `fred.ahe_yoy` | 37.41 | — | 100.0 **!** | low | 121 |
| `fred.auto_delinq` | 1.49 | — | 75.0 | low | 183 |
| `fred.cc_chargeoff` | 3.84 | — | 43.8 | low | 183 |
| `fred.cc_delinq_30` | 2.92 | — | 37.5 | low | 183 |
| `fred.existing_homes` | 4,020,000.00 | — | 38.5 | low | 121 |
| `fred.housing_permits` | 1,423.00 | — | 26.5 | low | 121 |
| `fred.housing_starts` | 1,465.00 | — | 75.5 | low | 121 |
| `fred.housing_starts_sf` | 930.00 | — | 38.8 | low | 121 |
| `fred.mortgage_30y` | 6.53 | — | 44.2 | low | 82 |
| `fred.mortgage_delinq` | 1.89 | — | 93.8 | low | 183 |
| `fred.new_homes` | 622.00 | — | 22.4 | low | 121 |
| `fred.real_gdp` | 24,152.66 | — | 100.0 **!** | low | 183 |
| `fred.total_hh_debt` | 20,934,549.00 | — | 100.0 **!** | low | 248 |
| `fred.yield_10y` | 4.45 | — | 86.4 | low | 82 |
| `fred.yield_2y` | 3.99 | — | 45.4 | low | 82 |
| `fred.yield_30y` | 4.98 | — | 97.2 **!** | low | 82 |

### Pillar 3 — Systemic Liquidity (dial: macro, weight 0.20, reads liquidity)

| Series | Level | 20d change | Pctile | Conf | Stale |
|---|---|---|---|---|---|
| `fred.bank_reserves` | 3,066,560.00 | — | 21.0 | low | 83 |
| `fred.fed_balance` | 6,704,383.00 | — | 22.9 | low | 83 |
| `fred.m2` | 22,804.50 | — | 100.0 **!** | low | 121 |
| `fred.nfci` | -0.51 | — | 15.4 | low | 85 |
| `fred.nfci_lev` | 0.36 | — | 92.1 | low | 85 |
| `fred.rrp` | 11.68 | — | 14.4 | low | 81 |
| `fred.tga` | 830,296.00 | — | 81.8 | low | 83 |

### Pillar 4 — Inflation Dynamics (dial: macro, weight 0.20, reads inflation)

| Series | Level | 20d change | Pctile | Conf | Stale |
|---|---|---|---|---|---|
| `fred.breakeven_10y` | 2.38 | — | 77.1 | low | 81 |
| `fred.breakeven_5y5y` | 2.24 | — | 36.5 | low | 81 |
| `fred.brent` | 102.75 | — | 88.4 | low | 84 |
| `fred.core_cpi` | 335.42 | — | 100.0 **!** | low | 121 |
| `fred.core_pce` | 129.63 | — | 100.0 **!** | low | 121 |
| `fred.cpi` | 332.41 | — | 100.0 **!** | low | 121 |
| `fred.flex_cpi` | 1.36 | — | 93.9 | low | 121 |
| `fred.natgas` | 3.10 | — | 59.5 | low | 84 |
| `fred.pce` | 130.90 | — | 100.0 **!** | low | 121 |
| `fred.sticky_core` | 0.39 | — | 67.3 | low | 121 |
| `fred.sticky_cpi` | 0.38 | — | 67.3 | low | 121 |
| `fred.wti` | 97.63 | — | 89.9 | low | 84 |

### Pillar 5 — Investor Sentiment & Positioning (dial: vol, weight 0.40, reads volatility)

| Series | Level | 20d change | Pctile | Conf | Stale |
|---|---|---|---|---|---|
| `fred.uoM_sent` | 49.80 | — | 2.0 **!** | low | 121 |
| `fred.vix` | 15.74 | — | 31.6 | low | 82 |

### Pillar 6 — Valuation & Credit Spreads (dial: vol, weight 0.60, reads credit)

| Series | Level | 20d change | Pctile | Conf | Stale |
|---|---|---|---|---|---|
| `fred.bb_oas` | 1.61 | — | 3.9 **!** | low | 82 |
| `fred.ccc_oas` | 9.35 | — | 72.5 | low | 82 |
| `fred.hy_oas` | 2.72 | — | 8.8 | low | 82 |
| `fred.ig_oas` | 0.73 | — | 0.6 **!** | low | 82 |

### Pillar 7 — Global Interconnectivity (dial: macro, weight 0.10, reads rates)

| Series | Level | 20d change | Pctile | Conf | Stale |
|---|---|---|---|---|---|
| `fred.dxy` | 119.29 | — | 14.7 | low | 85 |
| `fred.usd_cny` | 6.79 | — | 10.8 | low | 85 |
| `fred.usd_eur` | 1.16 | — | 82.6 | low | 85 |
| `fred.usd_jpy` | 159.20 | — | 96.7 **!** | low | 85 |

### Pillar 8 — Sovereign Health & Debt Cycle (dial: macro, weight 0.05, reads no dimension)

| Series | Level | 20d change | Pctile | Conf | Stale |
|---|---|---|---|---|---|
| `fred.current_account` | -60,307.00 | — | 77.1 | low | 144 |
| `fred.fed_debt_pct_gdp` | 122.57 | — | 100.0 **!** | low | 248 |
| `fred.fed_outlays` | 7,678.99 | — | 100.0 **!** | low | 183 |

---


*End of Monthly Regime & Allocation. Pillars are inputs; the dials are the regime. Every figure above was read from the object, the register, the grader, the probability ledger or the store, and anything unreadable says so.*
