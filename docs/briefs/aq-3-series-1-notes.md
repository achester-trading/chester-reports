# AQ-3 part 1 — the series writers for the Quarterly's first chapters: build notes (11 Oct 2026)

Branch `aq-3-series-1`, from `origin/main` (785fa19). Not merged. It follows the
change order `docs/change-order-alternative-assets-quarterly-2026-10-10.md`:
§11 row AQ-3, and §10A's flows-and-positioning standard.

**Part 2 (the three deep chapters' scenario sets) is on its own branch.**
`config/quarterly_chapters.yaml` does not exist on main; it lives on the AQ-2
branches. So part 2 is one commit, made on `aq-3-scenarios-1` from
`origin/aq-2-chapters-2`, and can be cherry-picked onto that branch. It is
config only, and the quarterly gate passes with it.

## What was built

Every writer rides the existing pulls. They are registered in
`altdata/feeds.py` and take the 16:10 pull and the 06:45 correction pass where
their group runs. No unit file was touched, and **no timer change is needed.**

| # | Writer (group) | What it stores | Source, verified 11 Oct 2026 |
|---|---|---|---|
| 1 | `spdr_gld` (external) | `etf.gld_oz`, `etf.gld_tonnes`, `etf.gld_shares`, `etf.gld_share_flow` | The GLD historical archive (.xlsx, from 18 Nov 2004), read **by content** from `~/chester-data/inbox/etf/` (see below) |
| 1 | `ishares_trusts` (external) | `etf.{iau,slv}_{oz,tonnes,shares,share_flow}`, `etf.ibit_shares`, `etf.ibit_share_flow` | ishares.com product pages, embedded key facts read by name; forward-only |
| 2 | `shfe` (external) | `shfe.stocks_t`, `shfe.warrants_t` (instrument COPPER, ALUMINIUM, ZINC), tonnes | SHFE weekly stock page, `weeklystock_<date>/ZH/all.html`, read by content |
| 3 | `eia_rigs` (official) | `eia.rigs_oil`, `eia.rigs_gas`, `eia.rigs_total` | Baker Hughes' count as the EIA republishes it (no-key history workbooks), **monthly**, from 1973 |
| 4 | computed (`market_features.aq3_rows`) | `calc.crack_321`, $/bbl | (2×RB + HO, each ×42, − 3×CL) / 3 from the same session's closes. RB=F and HO=F were added to the price basket (55 symbols) |
| 5 | `cnh` (external) | `cnh.usdcnh` | Yahoo CNH=X **hourly** bars → the New York close (the last bar opening before 17:00 NY). Yahoo serves no daily CNH history; the hourly bars go back 730 days |
| 5 | computed, band rule in `cfets.py` | `calc.cny_fix_gap_bp`, `calc.cny_band_position`, `calc.cnh_fix_gap_bp`, `calc.cnh_cny_bp` | `cfets.gap_bp` / `band_position` (±2%, BAND_PCT), extending the cfets writer rather than duplicating it |
| 6 | `cftc` extended | Disaggregated (`cftc.dis_*`): GOLD, SILVER, COPPER, WTI, NATGAS × producer/merchant, swap, managed money, other reportables. TFF (`cftc.tff_*`): EUR, JPY, GBP, CHF, CAD, AUD × dealer, asset manager, leveraged funds, other reportables. Each long, short and net, **and each as a % of open interest** (`_oi`, delta in pp), plus the report's OI | Socrata 72hh-3qpy and gpe5-46if, from 13 Jun 2006. The API serves the whole history, so the first pull is the backfill and the annual files are not needed. The legacy series are untouched |
| 7 | FRED H.10 | 18 pairs, `fred.usd_{aud,nzd,gbp,cad,chf,sek,nok,dkk,brl,zar,krw,twd,inr,sgd,hkd,myr,lkr,ves}` (`FRED_FX_SCAN_SERIES`). Plus `fred.usd_thb` in its own `FRED_THAILAND_SERIES` / `fred_thailand` block, under **`namespace: thailand`** with `trigger_eligible: false` | FRED, all live (last print 2 Oct). The quote convention is the unit: AUD, NZD and GBP are USD per unit, the rest units per USD |

How each writer behaves:

- **Shape changes fail the run.** Each writer is STALE, not empty: a fetch or
  shape failure writes nothing and keeps the last vintage. Specifically:
  - the CFTC writer raises on a report with none of its category columns;
  - SHFE raises on a page missing a metal;
  - iShares raises on a page without its key facts;
  - the EIA writer refuses a workbook naming another series.
- **Flows are share-count changes, never AUM.** Tonnes and shares are separate
  keys (choice 6 covers the rounding).
- **Timestamps:**

  | Writer | `available_at` |
  |---|---|
  | CFTC | Friday 15:30 ET (`reconstructed`), as the legacy series |
  | SHFE | The report date at 16:00 Beijing (`reconstructed`); the page has no Last-Modified |
  | Rigs | The workbook's Last-Modified |
  | GLD (inbox) | The file's mtime |
  | iShares | The write instant |
  | CNH | The close bar's end |
  | Computed series | The latest input's |
- **SHFE is bounded** to fit the 16:10 pull's deadline. It tries one request per
  page with a 20 s timeout and stops after two unanswered requests.

**Registry and gates:**

- 75 metric entries, plus two bulk blocks for the FRED pairs.
- Five sources: `spdr_gld`, `ishares_trusts`, `shfe`, `eia_rigs`, `yahoo_cnh`.
- Two mechanism groups: `commodity_holdings` and `commodity_supply`.
- Units added to `derived.DELTA_UNITS`: the H.10 currencies, which move in percent.
- `validate_prices` now expects 55 symbols.
- **Gate:** `tools/validate_aq3_series.py` (40 checks, no network, added to the
  Makefile). It covers each writer's fixture parse, its keys, `available_at`,
  STALE-not-empty, the crack arithmetic, the OI-share arithmetic, the band
  position, Thailand's isolation and the wiring.
- Fixtures are synthetic files in each source's shape, built in the gate. None
  is a cut of a publisher's file: the GLD archive's disclaimer forbids
  redistribution.
- **Gates run and passing:**
  - `check_registry`, `validate_official_sources` (233), `validate_feeds_scheduled`, `validate_monthly_stack`, `validate_weekly_stack`;
  - `validate_prices`, `validate_derived`, `validate_config_refs`, `validate_regime`;
  - `validate_secrets`, `validate_deploy`, `validate_systemd_units`, `validate_gates`;
  - `validate_weekly_complete`, `validate_weekly_edits`.

### The absent rows these writers fill (for AQ-2's follow-up; one config line each)

Row labels are `aq-2-chapters-2`'s. None is switched here.

| Chapter | Absent row | Key(s) |
|---|---|---|
| Metals | Gold ETF holdings (GLD/IAU tonnage) | `etf.gld_tonnes`, `etf.iau_tonnes` (flows: `etf.gld_share_flow`, `etf.iau_share_flow`) |
| Metals | COMEX managed money, silver and copper (disaggregated COT) | `cftc.dis_managed_money_net_oi`, instrument SILVER / COPPER (and GOLD) |
| Metals | LME, COMEX and SHFE copper inventories | `shfe.stocks_t` COPPER (with `shfe.warrants_t`). **The SHFE leg only**: LME and COMEX stay absent |
| Oil | Rig count, frac spreads, DUCs | `eia.rigs_oil`, `eia.rigs_gas`, `eia.rigs_total` (monthly). Frac spreads and DUCs stay absent |
| Oil | Refinery utilisation and cracks | `calc.crack_321`. Utilisation stays absent |
| Oil (new rows, no absent row today) | Crude and gas positioning | `cftc.dis_managed_money_net_oi` WTI / NATGAS |
| Currency | COT for EUR, GBP, CHF, AUD, CAD (TFF) | `cftc.tff_lev_money_net_oi` and `cftc.tff_asset_mgr_net_oi`, instrument EUR / GBP / CHF / AUD / CAD (and JPY) |
| Currency | CNH-CNY | `calc.cnh_cny_bp` |
| Currency, deep basket | GBP/USD, USD/CHF, AUD/USD, USD/CAD, USD/CNH, USD/THB | `fred.usd_gbp`, `fred.usd_chf`, `fred.usd_aud`, `fred.usd_cad`, `cnh.usdcnh`, `fred.usd_thb` (see Needs you 2) |
| Currency, scan tier | NZD, SEK, NOK, MXN, BRL, ZAR, KRW, TWD, INR, SGD, HKD | `fred.usd_nzd` (USD per NZD), `fred.usd_sek`, `fred.usd_nok`, `fred.usd_mxn` (already held; AQ-2 marked it absent), `fred.usd_brl`, `fred.usd_zar`, `fred.usd_krw`, `fred.usd_twd`, `fred.usd_inr`, `fred.usd_sgd`, `fred.usd_hkd` |
| Currency, scan tier | EUR/JPY, AUD/JPY, EUR/CHF, EUR/GBP | Each is two H.10 legs. AQ-2's row kinds (`diff`, `share`, `ratio_pct`) have no product, so a `cross` kind is one function in `quarterly_items` |
| China | USD/CNH, and CNH-CNY | `cnh.usdcnh`, `calc.cnh_cny_bp` |
| China | Fixing gap (AQ-2 computes it as `ratio_pct`) | Can read `calc.cny_fix_gap_bp` and `calc.cny_band_position` instead |
| EM | The EM FX basket | Partly: `fred.usd_brl`, `fred.usd_zar`, `fred.usd_krw`, `fred.usd_twd`, `fred.usd_inr`, `fred.usd_myr`, `fred.usd_mxn`. The EM dollar index stays absent |
| Crypto | ETF flows read against float, from share counts | `etf.ibit_shares`, `etf.ibit_share_flow`. The float itself stays absent |
| Thailand | USD/THB (five lines, structure, chart) | `fred.usd_thb` (`namespace: thailand`) |

## No free source

| Series | What was checked (11 Oct 2026) | Result |
|---|---|---|
| COMEX registered and eligible stocks (gold, silver, copper) | `cmegroup.com/delivery_reports/Gold_Stocks.xls`, `Silver_stocks.xls`, `Copper_Stocks.xls` | HTTP 403 with CME's notice that scripted access is blocked and prohibited by its Data Terms of Use. **Not built** |
| LME warehouse stocks | lme.com's warehouse-and-stocks page | 403 to a script; LME data is licensed. No free daily headline found. **Not built** |
| Baker Hughes weekly rig count | `rigcount.bakerhughes.com` (page and robots.txt) | Akamai "Access Denied" for any user agent. The **monthly** count is built from the EIA instead; the weekly is not |
| Frac spreads | Primary Vision's frac spread count page | Serves a 114-byte challenge to scripts; the count is a subscription product. **Not built** |
| GLD archive, fetched | `api.spdrgoldshares.com/api/v1/historical-archive` | Its robots.txt is `Disallow: /`. Built to read the operator's inbox and to fetch only if the rule lifts (Needs you 1) |
| IBIT bitcoin held | IBIT's product page | Carries the per-basket bitcoin amount only. Shares outstanding are stored; the bitcoin held is not |
| SHFE history before mid-2026 | Weekly pages for 2023–2025 dates | 404, so the series is effectively forward from the first run. The current pages are reachable only intermittently from a US address |
| USD/CNH daily history | Yahoo CNH=X daily; FRED (H.10 has onshore DEXCHUS only) | One bar for Yahoo daily. Built from the hourly bars instead |
| DUCs, refinery utilisation | Not checked in this part | Not built |

## Choices made for the operator to overrule

1. **The rig count is monthly (EIA), not weekly.** Baker Hughes refuses scripts,
   and this repo's writers do not pass for a browser.
2. **GLD follows AAII's inbox pattern.**
   - Its data host disallows robots, so the archive is downloaded in a browser
     from `spdrgoldshares.com/usa/historical-data/` and placed in
     `~/chester-data/inbox/etf/`. Any filename works; the file is recognised
     by content.
   - It could also come through the nightly rclone sweep, if a chat-side task
     drops it in Drive.
   - `available_at` is the file's mtime: an upper bound.
3. **CNH's daily close is session-set:** the last hourly bar opening before 17:00
   New York, weekends skipped, today's open session never stored.
4. **SHFE's `available_at`** is the report date at 16:00 Beijing, by rule.
5. **CFTC.** Spread positions are not stored. The `_oi` shares cover long, short
   and net, each in percent of the record's OI, moving in pp.
6. **GLD shares** are total ounces ÷ ounces per share. The trust's
   eight-digit ounces-per-share bounds the error at about ±40 shares.
7. **The baht is isolated in the registry.** It has its own block under
   `namespace: thailand`. The currency chapter's deep basket lists USD/THB; if
   that chapter displays `fred.usd_thb`, it is a read, never a trigger
   (Needs you 2).
8. **New units and groups.** The H.10 currencies are added to `DELTA_UNITS` as
   percent. VES is included because H.10 still publishes it, even though it is
   an administered rate.
9. **Part 2's ranges carry no weight.** The metal, DXY and pair bull/base/bear
   ranges print as "range …" in the prior column. Only the paper's
   probabilities print as priors.

## Needs you

1. Will you place the GLD archive in `~/chester-data/inbox/etf/` (or have a chat-side task drop it in Drive for the rclone sweep)? yes / no
2. May the currency chapter display `fred.usd_thb` in its deep basket (a read under the Thailand isolation, never a trigger)? yes / no
3. Is the monthly EIA rig count acceptable in place of Baker Hughes' weekly? yes / no
4. Cherry-pick the scenario-set commit (`aq-3-scenarios-1`) onto `aq-2-chapters-2`? yes / no
5. Merge order, inside windows: this branch to main independently of the AQ-2 branches? yes / no
