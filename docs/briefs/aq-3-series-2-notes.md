# AQ-3 part 2 — the remaining series writers: build notes (11 Oct 2026)

Branch `aq-3-series-2`, from `origin/aq-3-series-1` (9ce3e9f). Not merged. It
follows the change order `docs/change-order-alternative-assets-quarterly-2026-10-10.md`:
§11 row AQ-3.

## Step 0 (housekeeping), done first

1. **`aq-2-chapters-2` was fast-forwarded** from d401afe to c54d8b1, part 1's
   scenario-set commit, and pushed. **`aq-3-scenarios-1` was deleted on
   origin.**
2. **One commit on `aq-2-chapters-2`, 833bf99:**
   - Every structure row that part 1's writers fill now names its key as a
     hook on `aq-3-series-1`. It prints "not yet: aq-3-series-1" until that
     branch merges. The rows are part 1's notes table.
   - The EM OAS rows hook c1-move-screen's `fred.em_corp_oas` and
     `fred.em_hy_oas`.
   - **USD/THB stays out of the currency chapter**, pending part 1's
     Needs you 2.
   - **SLOOS is the credit chapter's lending-standards measurable**
     (`not_tightened`, hooked on `aq-3-series-2`). The HY-OAS leg's evidence
     is labelled "proxy until SLOOS".
   - `quarterly_items` gained one `resolve_hook` helper for the five lines,
     structure rows, chart legs and pairs. The pairs' scan tier now reads its
     keys.
   - `validate_config_refs` skips a hook that names its branch.
   - `validate_quarterly_stack` passes 94 checks and `validate_config_refs`
     passes 29.

## What was built

Every writer rides the existing pulls and is registered in `altdata/feeds.py`.
**No unit file was touched, and no timer change is needed.**

| # | Writer (group) | What it stores | Source, verified 11 Oct 2026 |
|---|---|---|---|
| 1 | — | **ICE BofA EM spreads are not duplicated.** Session A registered `fred.em_corp_oas` and `fred.em_hy_oas` on `c1-move-screen`; the EM chapter hooks them (step 0) | — |
| 2 | FRED (`FRED_SLOOS_SERIES`, block `fred_sloos`, **moves in pp**) | `fred.sloos_ci_large` (DRTSCILM), `fred.sloos_ci_small` (DRTSCIS), `fred.sloos_cre_construction` (SUBLPDRCSC), `fred.sloos_cre_nonres` (SUBLPDRCSN), `fred.sloos_cre_multifamily` (SUBLPDRCSM) | FRED, quarterly, last 2026-07-01. The CRE split starts 2013Q4 |
| 3 | `nbs` (official) | 70-city new homes: `nbs.city70_new_mm_down`, `_mm_up`, `_yy_down` (counts), and `_mm_avg`, `_yy_avg` (unweighted means). Year to date: `nbs.re_starts_ytd`, `nbs.re_sold_area_ytd`, `nbs.re_sales_ytd`, each with `_yoy` | NBS English press releases. Each release is found on the index by its title, and each table by its caption. **TSF is not built** (see below) |
| 4 | `bot` (official) | `thai.bot_policy_rate`, one row a decision since May 2000 (206 rows) | The BoT's MPC table, keyless. The BoT API is used **only** if `BOT_API_KEY` is in the environment; otherwise the writer logs and prints "no key" |
| 4 | `tpso` (official) | `thai.cpi` (index, 2023 = 100, from 1976), `thai.cpi_yoy` | Commerce Ministry (TPSO) index service, a keyless POST. FRED has Thai CPI only annually |
| 4 | `mots` (official) | `thai.tourist_arrivals` (persons a month) | MOTS workbook, found by link text: category 411, then the year's category, then the arrivals category, then `/images/v2022_*.xlsx` |
| 4 | `nesdc` (official) | `thai.gdp_real_sa` (million baht, chain volume, SA, from 1993Q1), `thai.gdp_real_sa_qoq` | NESDC's QGDP CSV release: the RSS feed, then the download page, then the `?ddl=` redirect to a zip of CSVs, read by content |
| 4 | `thai_set` (external) | `thai.set_index`, **forward-only** | Yahoo `^SET.BK` via yfinance. Yahoo serves one bar whatever the period asked |
| 5 | FRED (`FRED_AQ3_SERIES`, block `fred_aq3`) | `fred.cre_delinq` (DRCRELEXFACBS, the real-estate headline), `fred.case_shiller_national` (CSUSHPINSA) | FRED |
| 5 | computed | `calc.xlre_spy`, `calc.vnq_spy`, `calc.mortgage_spread_10y_bp` | From stored bars (**VNQ added to the basket**) and FRED |
| 6 | computed | `calc.efa_spy`, `calc.vea_spy`, `calc.hefa_efa`. Hedged yields, labelled **APPROXIMATION** with their method: `calc.bund_hedged_yield`, `calc.bund_hedged_spread_bp`, `calc.jgb_hedged_yield`, `calc.jgb_hedged_spread_bp` | **VEA and HEFA added to the basket** (58 symbols). The hedging cost uses `fred.effr_daily` (DFF), `fred.ecb_dfr` (ECBDFR) and `fred.jp_call_rate` (IRSTCI01JPM156N) |
| 7 | `bundesbank` (official) | `bbk.bund_10y`, daily since 1997 | Bundesbank SDMX API, no key; robots.txt returns 404 |
| 7 | `ecb_irs` (official) | `ecb.irs_10y_de`, `_fr`, `_it`, monthly | ECB data portal, IRS dataset, no key |
| 7 | FRED | `fred.gilt_10y` (IRLTLT01GBM156N), monthly | FRED. The Bank of England's database is robots-disallowed (below) |
| 7 | computed | `calc.oat_bund_bp`, `calc.btp_bund_bp` (ECB, one method), `calc.us_jgb_10y_bp` (DGS10 less `mof.jgb_10y`) | — |
| 8 | — | **IIF portfolio flows not built** (below) | — |

**How the writers behave:**

- **Shape changes fail the run.** Every writer is STALE, not empty: a failed
  fetch or a changed shape writes nothing and keeps the last vintage.
  Specifically:
  - the Bundesbank writer refuses another series;
  - the ECB writer refuses a missing country or one it did not ask for;
  - NBS refuses a 70-city table without exactly 70 cities;
  - NESDC passes over the percent twin of its GDP table and the
    current-price table.
- **`available_at` by writer:**

  | Writer | `available_at` |
  |---|---|
  | Bund | The next weekday, 12:00 Frankfurt, by rule (`reconstructed`) |
  | ECB, MOTS, NESDC | The file's Last-Modified (`observed`) |
  | NBS | The release date in its URL, at 09:30 or 10:00 Beijing |
  | BoT | 14:05 Bangkok on the decision date (the BoT's own release time) |
  | TPSO | The 10th of the next month, by rule |
  | SET | 17:00 Bangkok |
  | Computed series | The latest input's |
- **A new HTTP helper.** `_base.http_post_json` serves TPSO's query.
  `validate_official_sources`'s outage test now patches it too, so no writer
  can reach the network in that test.

**Gate:** `tools/validate_aq3_series.py` now has groups K–P, 73 checks in all
(part 1's 40 plus 33), no network. Each new writer parses its synthetic
fixture, registers its keys, stores `available_at` and degrades
STALE-not-empty. The gate also checks the hedged-yield, spread and ratio
arithmetic, and every new Thai key: `thai.*`, `namespace: thailand`, never
`trigger_eligible`.

**Gates run and passing:**

- `validate_aq3_series` (73), `check_registry`, `validate_official_sources`, `validate_feeds_scheduled`, `validate_prices` (58);
- `validate_derived`, `validate_config_refs`, `validate_regime`, `validate_secrets`, `validate_deploy`;
- `validate_systemd_units`, `validate_gates`, `validate_weekly_complete`, `validate_weekly_edits`;
- `validate_monthly_stack`, `validate_weekly_stack`, `check_library`.

### The absent rows these keys fill (for AQ-2's next follow-up; one config line each)

Row labels are `aq-2-chapters-2`'s. SLOOS is already switched (step 0); the
rest are not.

| Chapter | Absent row | Key(s) |
|---|---|---|
| Credit | SLOOS C&I net tightening | **done in step 0**: `fred.sloos_ci_large`, `fred.sloos_ci_small`, `fred.sloos_cre_nonres` |
| Real estate | Real house prices, year on year | `fred.case_shiller_national` (nominal. "Real" needs a CPI deflator: a `ratio_pct` against `fred.cpi`) |
| Real estate (new headline row) | CRE loan delinquency | `fred.cre_delinq` |
| Real estate (new rows) | REITs against the market | `calc.xlre_spy`, `calc.vnq_spy`. `calc.mortgage_spread_10y_bp` can replace the chapter's own `diff` |
| International equities | Hedged against unhedged | `calc.hefa_efa`; the hedged-yield pair `calc.bund_hedged_spread_bp`, `calc.jgb_hedged_spread_bp` |
| International equities | The euro fragmentation spread | `calc.btp_bund_bp` (and `calc.oat_bund_bp`) |
| International equities (new rows) | EFA and VEA against SPY | `calc.efa_spy`, `calc.vea_spy` |
| China | Property: starts | `nbs.re_starts_ytd`, `nbs.re_starts_ytd_yoy` (sales: `nbs.re_sold_area_ytd`, `nbs.re_sales_ytd`) |
| China (new row) | 70-city new-home prices | `nbs.city70_new_mm_down`, `nbs.city70_new_mm_avg` |
| Thailand | The BoT policy rate (five lines, structure) | `thai.bot_policy_rate` |
| Thailand | Thai CPI | `thai.cpi_yoy` (level `thai.cpi`) |
| Thailand | Tourist arrivals | `thai.tourist_arrivals` |
| Thailand (new rows) | Real GDP; the SET | `thai.gdp_real_sa_qoq`, `thai.set_index` |
| Currency, rates (new rows) | The gilt, UST-JGB | `fred.gilt_10y`, `calc.us_jgb_10y_bp` |

## No free source

| Series | What was checked (11 Oct 2026) | Result |
|---|---|---|
| **China TSF and the credit impulse** | pbc.gov.cn robots.txt: `User-agent: * / Disallow: /` (Baiduspider alone allowed). NBS releases do not carry TSF, and `data.stats.gov.cn` answers 403. chinamoney.com.cn's pages are JavaScript shells with no data. Xinhua reposts the PBOC text, but as Chinese prose at a hashed URL with no index to find it by | **Not built**, and so the credit impulse (TSF flow / GDP) is not built either |
| **SET index history** | Yahoo `^SET.BK` serves one bar for every period, `max` included. set.or.th's endpoints answer an Incapsula JavaScript challenge. stooq's robots.txt is `Disallow: /` | **Forward-only** from the first pull |
| **IIF Capital Flows Tracker** | iif.com robots.txt puts `User-agent: *` in the same group as `Disallow: /`. The tracker itself is a monthly PDF and press release, with no tabular file found | **Not built** |
| **CMBS delinquency by property type** | Trepp's data is paid. TreppTalk's monthly post is robots-allowed, but its HTML carries only the overall rate, in a share-link summary ("rose 17 bp to 8.02% in September 2026"). The property-type split is not in the page | **Not built**. `fred.cre_delinq` (banks' CRE loans) is the headline row instead |
| **Daily OAT and BTP** | Banque de France's Webstat API needs a registered key. The Bundesbank publishes the Bund only. The ECB publishes monthly averages | Built **monthly** (ECB IRS) |
| **Daily gilt** | The Bank of England's database answers, but its robots.txt disallows `/boeapps/database/_iadb-FromShowColumns.asp` and `/boeapps/iadb` | Built **monthly**, from FRED (OECD) |
| **Daily BoJ policy rate** | FRED carries Japan's call rate monthly only | The JGB hedge uses the monthly rate, carried forward at most 70 days |
| **The 3-month hedging cost from forward points or the basis** | No free daily FX forward or cross-currency basis was found (AQ-2 already lists the basis as absent) | Approximated by the policy-rate differential and labelled so |
| **NBS history and a 70-city aggregate** | `data.stats.gov.cn` answers 403. The English 70-city edition prints city rows only | Forward from the first run; the counts and means are computed |
| **MOTS arrivals before 2025** | 2025's year category has no arrivals sub-category. Older years' workbooks use other layouts | History starts with the current workbook: 2026 to date and 2025's same months |
| **BoT API without a key** | `gateway.api.bot.or.th/PolicyRate/v3/policy_rate/` answers 401 with no key. A key is free but personal (a secret) | Built to read `BOT_API_KEY`. The keyless MPC table carries the history |

## Choices made for the operator to overrule

1. **The hedged-yield method.** The hedged yield is the foreign 10-year less
   (EFFR − the foreign policy rate):
   - This is covered interest parity on policy rates, not on 3-month forward
     points, and it ignores the basis.
   - The yen leg is Japan's monthly call rate, carried forward at most 70
     days.
   - It is labelled APPROXIMATION in the registry.
2. **The Bund.** The daily Bund is the Bundesbank's Svensson-fitted 10-year
   zero-coupon yield. It sits a few bp from the benchmark bond's quote.
   - Its `available_at` is the next weekday at 12:00 Frankfurt, by rule; the
     API sends no Last-Modified.
   - The OAT–Bund and BTP–Bund spreads use the ECB's monthly series for all
     three, so the method is the same on both legs. They do not use the daily
     Bund.
3. **The 70-city summary is computed here,** because the English edition
   prints only city rows:
   - the count of cities down and up on the month (flat counts as neither);
   - the count of cities below a year earlier;
   - the unweighted mean index change.
4. **SLOOS:**
   - "tightened" means any print above zero in the prior four quarters, read
     on C&I to large and middle-market firms;
   - the block moves in pp, not bp;
   - three of the five SLOOS series are wired into the credit chapter.
5. **TPSO and BoT timestamps:**
   - TPSO's months are stamped the 10th of the next month at 10:30 Bangkok,
     an upper bound;
   - BoT decisions are stamped at the BoT's stated 14:05.
6. **The ratios are close ratios,** price only (XLRE, VNQ, EFA and VEA to SPY;
   HEFA to EFA). They move in percent of themselves.
7. **NBS is not an early writer.** It is read at the 16:10 pull, about 19
   hours after a 09:30 Beijing release. For monthly data that is soon enough,
   and it keeps the 06:45 pass's budget unchanged.
8. **USD/THB is not displayed in the currency chapter** until part 1's
   Needs you 2 is answered. The Thailand chapter reads it.
9. **`BOT_API_KEY` is not added to `.env.example`.** This session was not
   permitted to read that file, so the placeholder line is the operator's to
   add if wanted.

## Needs you

1. Yahoo's query hosts (query1/query2.finance.yahoo.com, which yfinance reads) serve robots.txt `User-agent: * / Disallow: /`. That covers the whole yfinance basket, including part 1's CNH and this part's VNQ, VEA, HEFA and SET. Keep the yfinance basket as an operator-sanctioned exception to the robots rule? yes / no
2. Will you put a Bank of Thailand API key in the box's `.env` as `BOT_API_KEY`? It is optional: the keyless MPC table carries the full history. yes / no
3. Accept the policy-rate-differential approximation for the Bund and JGB hedged yields? yes / no
4. Accept monthly OAT, BTP and Bund (ECB) and a monthly gilt (FRED) in place of daily series? yes / no
5. Merge order, inside windows: `aq-3-series-1`, then `aq-3-series-2` (stacked on it), then `aq-2-chapters-2`, whose hooks name both? yes / no
