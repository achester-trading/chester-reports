# B69: the Quarterly's readers, tranche 1 (oil and energy, agriculture, currencies): build notes

*Session B, 25 Oct 2026, on branch `b69-quarterly-readers-1` from `origin/b68-price-source-migration` (`fa7e298`). Ruling D34 of 24 Oct 2026: the sources that passed B67's checks are built as report-only readers for the Alternative Assets Quarterly's unfilled series. Each "PASSES WITH LIMITS" condition is built into the reader and its registry entry. **Nothing here merges before the 1 Nov Monthly.** No Security Master id was needed: none of these readers lists an instrument.*

## Base and commits

- **Base:** `origin/b68-price-source-migration` at `fa7e298`.
- **B68's CI, read once at the start** (this branch is built on it): runs 40151381144 and 40151394265 were both still **queued**, after 32 minutes.
- **The commits:** `02d1861` (the readers, the gate, the registries and these notes, in one commit), then this CI line.
- **CI:** at the one read after the push of `02d1861`, no run was listed yet, so there is no run id. B70 branches from this tip and reads it once.

## The readers

Every reader:
- reads its host's robots.txt at every pull, through `altdata/sources/_quarterly_common.robots_check` (the wildcard-aware `aaii.robots_verdict`). A file answered 401, 403, 404 or 410 means no rules (RFC 9309 2.3.1.3, the reading `cboe_indices` already takes); any other failure to read it raises and becomes STALE;
- sends every request through its own module's `http_get_response` and `http_get_text`, so `validate_official_sources`' outage test can replace them;
- treats a 4xx as an immediate failure (`_base`) and never retries around it; the one-a-day readers also pass `max_retries=1`;
- runs as an official writer in the existing feed, with no new timer;
- has `--dry-run`, which writes a temporary store only.

Terms were re-read on 25 Oct 2026.

| # | Reader (module) | Keys | Terms condition, and how the code honours it | Probe on the laptop, 25 Oct 2026 |
|---|---|---|---|---|
| 1 | EIA buffers (`eia_buffers`, source `eia`) | `eia.spr_stocks` (barrels), `eia.refinery_util` (%), `eia.gas_storage` (Bcf), `eia.lng_exports` (MMcf, monthly) | public domain, acknowledgment asked; the registry descriptions name the EIA | robots allows `/dnav/`; the four workbooks answered 200 at B67 (OLE2 .xls); not re-requested |
| 2 | OVX (`fred.ovx`, `FRED_6I_SERIES`) | `fred.ovx` | Cboe's copyright, own use: through the FRED API with the key, never the graph CSV; the block's description says "own use, never redistributed" | from B67: 200, from 2007-05-10 |
| 3 | IMF PortWatch (`portwatch`, source `imf_portwatch`) | `imf.portwatch.transits.{hormuz,suez,bab_el_mandeb,malacca}` and `.tanker` | IMF Data terms, attribution: every row's source is `imf_portwatch:IMF PortWatch`. **One request a day:** `DailyGuard` charges before sending, so a second run of a day is STALE "already spent" | chokepoint list 200 (28 ports; ids 6, 1, 4, 5); sample 200, newest row 2026-10-18; robots 403 = no rules |
| 4 | WASDE (`esmis_wasde`, source `usda_esmis`) | `usda.wasde.{wheat,corn,soybeans}.{ending_stocks,stocks_to_use}` | US Government work (17 U.S.C. 105); ESMIS has no terms page. **Projections kept apart:** the instrument is "2026/27 proj", "2025/26 est" or "2024/25"; each release is its own vintage | the listing 200; `wasde1026.xml` 200, 3.6 MB; parsed wheat 740, corn 1,849, soybeans 315 (the Oct projections) |
| 5 | Crop Progress (`esmis_crop_progress`) | `usda.crop_progress.{corn,soybeans,wheat}` | as 4 | `prog4226.txt` 200; corn 56% good or excellent (43 + 13) |
| 6 | ONI (`cpc_oni`, source `noaa_cpc`) | `noaa.oni` | NWS material not subject to copyright | from B67: 200, DJF 1950 onward; robots 404 |
| 7 | CFTC grains (`cftc_grains`, source `cftc`) | `cftc.disagg.{corn,wheat,soybeans}.managed_money_net` and `_oi` | public, keyless; the existing client (`cftc.fetch_records`) | robots allows `/resource/`; B67's corn sample 200 |
| 8 | Bank of Canada (`boc_valet`, source `boc`) | `boc.yield_2y` | free use with attribution; the registry and the description name the Bank | 200, newest 2026-10-22, 3.22 |
| 9 | Riksbank (`riksbank`, source `riksbank`) | `riksbank.yield_2y` | free use; per-IP rate limit: **one request a day**, no retry | 200, 2026-10-01 2.735 |
| 10 | SNB (`snb_sight`, source `snb`) | `snb.sight_deposits_total`, `snb.sight_deposits_domestic` (CHF millions) | "Open use. Must provide the source": every row's source is `snb:Swiss National Bank`; the registry records non-commercial own use | robots open; cube `snbgwdchfsgw` 200, 415 KB from 2009-01-09, PublishingDate 2026-10-19 10:00 |
| 11 | MoF intervention (`mof_intervention`, source `mof_intervention`) | `jp.mof.intervention_jpy` (yen) | PDL 1.0 (https://www.mof.go.jp/english/notice.htm, the page B67 could not find): every row cites "Ministry of Finance, Japan"; the backfill is paced at one page a second | the notice 200; the index 200 (44 monthly pages since Jan 2023); one page 200, Aug 27 to Sep 28, 2026: ¥0 |

**Where each prints:** `config/quarterly_chapters.yaml`. Its absent rows are switched to key rows:
- the oil chapter: the SPR, utilisation, OVX, and the four tanker-transit rows beside the Gulf-exports gap;
- the second half: gas storage and LNG exports;
- currencies: the Bank of Canada and Riksbank 2-year yields beside the DXY-weighted spread's gap, which now names only the UK leg; the MoF and SNB rows in place of "Intervention footprints";
- agriculture: WASDE stocks-to-use and ending stocks (the 2026/27 projection), crop condition, the ONI, and managed money's share of open interest.

`tools/validate_quarterly_stack.py` passes with the rows switched.

**Two placements in the paste that are not built here.** Item 18's floor read (the buffer state gaining the SPR and storage legs as context) and Factor III's disruption line both live in code outside the Quarterly. Here they print in the Quarterly's chapters only; the disruption-price analysis stays "not built (AQ-8)", its wait now naming the stored transits.

## Session-set values, with reasons

| Value | Setting | Reason |
|---|---|---|
| EIA WPSR availability | the Wednesday 10:30 ET after the week-ending Friday | `eia.available_at`, the existing rule |
| Gas storage availability | the Thursday 10:30 ET after the week-ending Friday | the Weekly Natural Gas Storage Report's release |
| LNG exports availability | the end of the second month after, 16:00 ET | the Natural Gas Monthly publishes about two months after the month |
| Crop Progress availability | the release date, 16:00 ET | the report's own words: "released after 4:00 pm ET" |
| ONI availability | the 15th of the month after the season's last month, 12:00 ET | CPC's ENSO discussion is on the second Thursday; the 15th bounds it |
| Bank of Canada availability | the day, 18:00 ET | posted after the close |
| Riksbank availability | the day, 12:00 ET (18:00 Stockholm) | evening posting, Swedish time |
| SNB availability | the reporting day plus three days, 10:00 Zurich; the newest row at the cube's PublishingDate | the Monday release |
| MoF availability | the page's date, 19:00 Tokyo | the month's last business day |
| PortWatch availability | the read instant (`ingest_instant`) | the service publishes no release time |
| PortWatch page size | 2,000 records, one request | one request a day |
| Lag families | `imf_portwatch` 6 (bound 8), `eia_ng_monthly` 55 (60), `noaa_oni` 42 (45) | each the publisher's own delay, measured or documented, in `config/publication_lags.yaml`. The other readers publish inside their cadence's own allowance (weekly 8, daily 2, monthly 32), so b51's rule ("never a number chosen to clear a key") gives them no lag. **A departure:** the paste asked for a family per source |

## The gate

`tools/validate_quarterly_readers_1.py` passes 48 to 0, on fixtures only. Its groups:
- A: each parser on a fixture;
- B: units and cadence;
- C: STALE on a 403 with one call and no retry; a robots disallow refused; robots 403 read as no rules; an unreadable robots.txt raised;
- D: the one-a-day guard, and PortWatch's and the Riksbank's second run of a day sending nothing;
- E: the attribution strings on the stored rows, read as registered ids;
- F: WASDE projections and estimates never sharing an instrument;
- G: the three lag families within their bounds, PortWatch's ahead of the `imf.*` glob;
- H: no address or literal User-Agent in a reader;
- I: every key registered, barred from the market-state object (a new `market_state_barred` entry citing D34), and no regime import;
- J: the official roster, static KEYS, OVXCLS in the FRED pull, the catalogue lines and the Quarterly rows.

It is registered in the Makefile after `validate_b59`. **CLAUDE.md's count line is recounted to one hundred and forty code gates (one hundred and thirty-seven Python, three shell)**, from chain-7's 139 plus this one.

Run locally:
- **the new gate:** 48 passed, 0 failed;
- **`validate_official_sources`:** 360 passed, 0 failed;
- **`check_registry`:** OK;
- **`check_library`:** 0 failures, 0 warnings;
- **`validate_audit_3a`:** 88 passed, 0 failed (the printed counts: 43 official writers, 284 FRED series);
- **`validate_st_r5_t1_rest`:** passed (its FRED pin moved to 284);
- **`validate_quarterly_stack`:** passed.

**A disclosure.** The first local run of `validate_official_sources` came before each reader routed its requests through its own module's helpers. So its outage test did not reach them, and it made one real request per new reader from the laptop, with the generic User-Agent, into the gate's temporary store. Nothing was written to any live store, and PortWatch's and the Riksbank's guards were in the gate's temporary state directory. The readers were fixed at once, and the gate now sends nothing.

**What else moved with the readers:**
- `altdata/feeds.py` OFFICIAL_WRITERS (33 to 43);
- `altdata/config.py` FRED_6I_SERIES (the pull 283 to 284);
- `metrics_registry.yaml`: 33 keys, their families, the barred entry and the `fred_6i` block;
- `source_registry.yaml`: six sources (`imf_portwatch`, `usda_esmis`, `boc`, `riksbank`, `snb`, `mof_intervention`), each with `terms_url`, `terms_read` and `limit`;
- `config/catalogue_commands.yaml`: ten lines;
- `tools/validate_audit_3a.py` NEW_KEY_BLOCKS (`fred_6i`);
- `tools/validate_st_r5_t1_rest.py`'s FRED pin;
- CLAUDE.md: the FRED list sentence, the roster count and a paragraph;
- the architecture document's store box (284; 43 official writers).

## Listed gaps

- **WASDE's production and trade lines:** only ending stocks and total use are read.
- **Crude skew:** no crude options chain is captured.
- **The DXY-weighted two-year spread:** the UK leg stays absent (the Bank of England's database disallows robots).
- **Daily LNG feedgas:** EIA's files carry monthly exports.
- **The crop-stage window:** condition is stored, stage is not.
- **The MoF record before January 2023:** the English index lists pages from then only.
- **Item 18's floor read and Factor III's disruption line,** as above.

## Box commands, for chain-8's box sheet (the operator's; dry runs first)

Each reader on the box, in the checkout, after the merge:

```
python -m altdata.sources.eia_buffers --dry-run
python -m altdata.sources.portwatch --dry-run           # spends today's one request
python -m altdata.sources.esmis_wasde --dry-run
python -m altdata.sources.esmis_crop_progress --dry-run
python -m altdata.sources.cpc_oni --dry-run
python -m altdata.sources.cftc_grains --dry-run
python -m altdata.sources.boc_valet --dry-run
python -m altdata.sources.riksbank --dry-run            # spends today's one request
python -m altdata.sources.snb_sight --dry-run
python -m altdata.sources.mof_intervention --dry-run
```

Then the backfills, where the source serves history:

```
python -m altdata.sources.esmis_wasde --releases 12        # the listing page's releases, each its own vintage
python -m altdata.sources.esmis_crop_progress --reports 30
python -m altdata.sources.mof_intervention --pages 44      # paced at one page a second
python -m altdata.fred_history backfill --series OVXCLS --dry-run, then without --dry-run
```

**The rest take their history on the first real pull:** the EIA workbooks, the ONI file, the CFTC grains, the Bank of Canada from 2000, the Riksbank from 2000, the SNB from 2009, and PortWatch one page. The official feed then runs them at 16:10 and 06:45. PortWatch and the Riksbank each send one request a day, so a dry run on the box spends that day's request.

## Needs you (five)

1. **ESMIS has no terms page** (/about answered 404). The readers rely on the WASDE and Crop Progress being US Government works (17 U.S.C. 105). Accept, or have them read through another USDA route?
2. **The SNB's terms text** is a JavaScript page no reader can fetch. The licence quoted is the SNB's own listing on Switzerland's open-data catalogue: open use, attribution, commercial use with permission. Accept, or confirm the portal's text in a browser first?
3. **WASDE's Quarterly rows name the "2026/27 proj" instrument,** which rolls each September. Options: change the six rows by hand each year, or a later tranche adds a "current projection" selector to the chapter reader.
4. **Crop Progress is seasonal.** Out of season, its three keys age past their weekly allowance, so the freshness check will list them STALE through the winter. Accept that as true, or add a seasonal note to the freshness roster in a later tranche?
5. **The CI queue.** Every push here starts the full matrix, and B66 to B68's runs were still queued at their one read (B68's for 32 minutes). Tonight's pushes are adding to the backlog. If the queue is a minutes or concurrency limit, the remaining pastes' CI results will lag well behind their reports.
