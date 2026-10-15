# AUD-3b: Security Master v1, its listings layer and the export for chester-meme

Branch `aud-3b-security-master`, cut from `origin/w-1-3c-weekly-polish` at
**fb67bf3** (its tip; it had not moved). It merges after Friday's merges, with a
refresh paste. Branch only: nothing merged to main, nothing deployed, nothing run
on the box. Session A's AUD-3a files were not touched: metrics_registry.yaml,
tools/check_registry.py, altdata/derived.py, source_registry.yaml and
altdata/catalogue.py. The gate *reads* metrics_registry.yaml to show that no key
was added.

## 1. The inventory

The audit counted at main cc91752; these counts are this branch's, at fb67bf3.
The four maps the consistency gate walks were counted by loading the modules:
316 identifiers, every one resolving to exactly one master entry today.

### ID schemes

| Scheme | Where it lives | Names | Maps |
|---|---|---|---|
| Yahoo symbol → store key `mkt_*` | `altdata/sources/yfinance_source.py` `SYMBOLS` | **106** | `BRK-B` → `yfinance.mkt_brk_b`. 8 `^` indices, 5 `=F`, 6 `=X`, 4 `-USD`, DX-Y.NYB, 29 single names, the rest ETFs |
| Yahoo crypto id → `crypto_*` | `yfinance_source.CRYPTO_BASKET`, from `config/crypto_basket.yaml` | **12** | suffixed ids such as `SKY33038-USD` |
| CoinGecko-style id | `crypto_basket.yaml` `llama_coin`; `loggers/shielded.py` `ZEC_LLAMA_COIN` | 12 + 1 | `coingecko:lido-dao`, `coingecko:zcash` |
| DefiLlama slug | `crypto_basket.yaml` `llama_slug` | 12 | protocol slugs |
| Overnight slug | `altdata/sources/overnight.py` `SYMBOLS` | **10** | `JPY=X` → `usdjpy`, `BTC-USD` → `btcusd` |
| Single-symbol writers | `sources/cnh.py` (`CNH=X` → `cnh.usdcnh`); `fed_funds.symbol()` (`ZQ<m><yy>.CBT`, 10 months, stored by `YYYY-MM`) | 1 + 10 | |
| Option underlyings / OCC roots | `altdata/config.py`: `options_universe()` 13, `chain_universe()` 17, `MASSIVE_SYMBOLS` 2 (SPX, SPCX); `tools/probe_massive.py` `SPX_ROOTS` (`I:SPX`, `SPX`, `SPXW`) | 19 roots | contract ids stored as yfinance `contractSymbol` (OCC) or Massive `O:` tickers; no root-splitting map |
| Ticker-reuse fence | `config.UNDERLYING_VERIFIED_FROM` | 1 | `SPCX` → `2026-06-16`, by hand |
| IBKR | `ibkr_portfolio.instrument_key()`: `<localSymbol>@<exchange>.<CCY>`; `portfolio.position_con_id` beside it; `executions.con_id` | per position | conIds live only in the box's store |
| Prediction markets | `config/prediction_markets.yaml` `watch_list`; store instrument `<venue>:<market id>` | 6 watches (4 Kalshi series, 2 events; 6 Polymarket query/slug pairs) | contracts exist only in the box's store |
| Issuer roots (the blocklist) | `config/tracked_entities.yaml` via `register/instruments.normalise()` | **29** roots, 2 name patterns, 2 name-only (RA, INF) | |
| CFTC codes | `sources/cftc.py` `CONTRACTS` 10, `DISAGG_CONTRACTS` 5, `TFF_CONTRACTS` 12 | 27 | code → contract name |
| FRED ids | `altdata/config.py` `FRED_PULL_SERIES` | 129 | series, not instruments; not in the master |

### Universes and alias maps

| Map | Where | Names |
|---|---|---|
| `EARNINGS_SYMBOLS` | yfinance_source L286 | 29 |
| `OHLC_SYMBOLS` / `CONTINUOUS_SYMBOLS` / `VOLUME_UNITS` | yfinance_source | 9 / 20 / 91 |
| the tape | `config/reporting_stack.yaml` `tape` | 9 (Yahoo bars + store key, six with prose aliases) |
| correlation | `config/correlation.yaml` `universe` 21, `aliases` 1, `peers` 18 | |
| horizon charts | `config/horizon_charts.yaml` `universe` 20, `assets` 25 | |
| Book B scanner | `config/book_b_scanner.yaml` `alt_assets` 20, `positioning.map` 15 (symbol → CFTC name) | |
| `ALIASES` | `daily_cascade/consistency.py` L144 | 4 (`y10` → `yfinance.mkt_tnx`, `fred.yield_10y`) |
| `quote_conventions` | metrics_registry.yaml | 4 store keys with pair names |
| fx charts `CATALOG` | `altdata/fx_charts.py` | 9 (key → FRED id and/or Yahoo) |
| fundamentals | `sources/fundamentals.py` `TICKERS` 9 | |
| funds | `proshares.FUNDS` 7, `ishares_trusts.TRUSTS` 3 | |
| `edgar.universe()` | SYMBOLS less `^`, `=`, `-` | 81 |
| the meme loggers | `loggers/borrow.py` over `consensus.universe()` | **24** (options 13 + 11 sectors). ApeWisdom instrument `<TICKER>@<feed>`; Reg SHO the FINRA symbol; RTAT unfiltered (536 tickers over its history) |

### Where two of them disagree

1. **One name, two dollar indices.** `yfinance.mkt_dxy` (DX-Y.NYB), fx_charts
   `DXY` and the tape mean ICE DXY. `fred.dxy` is the Fed's broad index,
   DTWEXBGS. `monthly_themes.yaml` still says the store holds no ICE DXY.
2. **normalise() collisions:**
   - DX-Y.NYB → `DX`; BTC-USD, SOL-USD and ZEC-USD → `BTC`, `SOL`, `ZEC` (SOL is
     also a listed equity ticker).
   - BRK-B and BRK.B → `BRK`, while IBKR's space form would stay `BRK B`.
   - None of these is a restricted root, so the blocklist is not affected. The
     master keeps them apart by scheme.
3. **EDGAR drops BRK-B.** Its universe filter removes any symbol with `-`.
4. **GOOG and GOOGL.** SYMBOLS carries both; the options universe, ai_fcf,
   narratives and story_queries carry GOOGL only. They are two instruments in the
   master.
5. **Crypto spellings.** `BTC-USD` (Yahoo), `mkt_btc_usd`, `btcusd` (overnight),
   `BTC` (levels). ZEC has two price series, `yfinance.mkt_zec_usd` and
   `zec.price_usd`.
6. **FRED FX direction.** `fred.usd_eur` (DEXUSEU) is dollars per euro, while
   `fred.usd_jpy` and `fred.usd_cny` are units per dollar.
7. **Duplicate series for one thing:**
   - USD/CNY: `fred.usd_cny`, `mkt_usdcny`, `cfets.cny_fix`.
   - JPY, VIX and the 10-year have both a FRED series and a Yahoo series.
   - The yfinance comments still say CNH is not tracked; `cnh.usdcnh` is.
8. **CFTC names.** `043602` is `UST10Y` in one map and `TY` in the TFF map;
   `020601` is `UST30Y` vs `US`.
9. **Named elsewhere, no close stored:**
   - MSTR, COIN, ASTS (options, borrow, ApeWisdom).
   - IBIT (paper bid, iShares).
   - MU, AMAT (fundamentals).
   - SPX, SPCX; ES=F, NQ=F, ^N225, ^STOXX50E, ^FTSE (overnight); CNH=X; the ZQ
     months; the ProShares funds.
10. **Continuity and cost class.**
    - TRY=X and IDR=X are not in `CONTINUOUS_SYMBOLS`.
    - The backfill's `AVAILABILITY_RULES` omit EURCHF=X, TRY=X and IDR=X.
    - alpha-lab-2's `alpha_rules.yaml` `by_symbol` prices only four symbols by
      class.
11. **Stale copies.**
    - horizon_charts still marks six assets as having no feed, which
      correlation.yaml now keys.
    - quarterly_chapters names three paper-bid chains, while `PAPER_BID_SYMBOLS`
      has four.
    - The auction logger omits XLB, XLRE and XLC.
12. **SPX and ^GSPC** are two entries in the master, because no stored source says
    Massive's SPX and Yahoo's ^GSPC are the same index. Needs-you 5.

## 2. The master

`config/security_master.yaml` is the source of truth, and `altdata/security_master.py`
loads and serves it.

**Fields:**
- `id`
- `name`
- `asset_class` (equity, etf, index, future, option_root, fx, crypto, rate,
  prediction_contract)
- `currency`
- `multiplier`
- `exchange` (MIC)
- `identifiers` by scheme (yahoo, store_key, ticker, occ_root, ibkr_conid, pm_id,
  crypto_id, overnight_slug)
- `aliases`
- `active_from`, `active_to`
- `underlying`, for an option root
- `unverified`, the null facts by name
- `sources`, where each filled fact came from

**The id scheme: `SM` + five digits, allocated in order, never reused.** Why:
- An id derived from a ticker breaks on exactly the case the master exists for,
  ticker reuse.
- An id carrying the asset class breaks when a class is corrected, as the 32
  entries with an unverified class may be.
- An opaque counter has neither problem. The file carries `next_id`, and the gate
  fails an id at or above it, a duplicate, or a malformed id.
- An instrument that stops trading is closed with `active_to`, never deleted, so
  an id is never freed.

**`store_key` is the full registry key** (`yfinance.mkt_spy`, `cnh.usdcnh`), so one
scheme covers every writer's namespace (`mkt_`, `crypto_`, `cnh.`).

**Ticker reuse.** An identifier names an instrument only inside that
instrument's active window. Two reuses are seeded from facts the repo holds:

| Identifier | Before | After |
|---|---|---|
| `ticker:BAM` | SM00165, "Brookfield Asset Management Inc. (the issuer now called BN)", to 2022-12-08 | SM00164, Brookfield Asset Management Ltd., from 2022-12-09 |
| `ticker:SPCX` | SM00140 (the former SPAC/new-issue ETF), to 2026-06-11 | SM00141, Space Exploration Technologies Corp Class A, from 2026-06-12 |
| `occ_root:SPCX` | the former issuer's options, to 2026-06-15 | from 2026-06-16, `UNDERLYING_VERIFIED_FROM` |

`ticker:BN` before 2022-12-09 resolves to nothing. `resolve()` raises `NotFound`
or `Ambiguous`, and never picks the first of two.

**Seeded once** by `tools/seed_security_master.py`. It reads the code's own maps
(listed in its docstring) by `ast`, with no network and no store. It refuses to
overwrite the file, since the master is edited by review from here. The call
sites keep their own maps tonight; the consistency gate holds them to the master
until each moves.

### Counts by asset class

| Class | Instruments |
|---|---|
| equity | 65 (29 priced single names, 5 more logged or captured (MSTR, COIN, ASTS, MU, AMAT), the Brookfield complex's 29 listed securities plus pre-2022 BAM, the current SPCX) |
| etf | 65 (53 priced through SYMBOLS, plus IAU, IBIT, the 7 ProShares funds, RA and INF, the former SPCX) |
| index | 11 |
| future | 7 |
| option_root | 21 |
| fx | 7 |
| crypto | 16 |
| rate | 2 (^TNX, ^TYX) |
| prediction_contract | 0 (the contracts live only in the box's store; needs-you 6) |
| **total** | **194**, next_id 195; 32 restricted, all the Brookfield complex |

Identifiers by scheme: yahoo 124, store_key 119, ticker 49, occ_root 21,
crypto_id 13, overnight_slug 10; ibkr_conid and pm_id 0.

### The unverified list

Every entry names its null facts in `unverified`; the gate fails a null that is
not listed.

| Fact | Null on | Why |
|---|---|---|
| exchange (MIC) | **194 of 194** | no MIC is in the repo or a stored source. The listings layer carries each US listing's exchange code as published; mapping codes to MICs is a later, reviewed step |
| currency | 171 | filled only where the identifier encodes it: 16 coins (-USD), 7 FX pairs (EURUSD=X → USD; mkt_usdjpy → JPY) |
| name | 149 | names come only from crypto_basket.yaml, tracked_entities.yaml and the SPCX note |
| multiplier | 81 | 1 for a share or a coin by definition. Futures, indices, FX and option roots are null: no contract size is in the repo |
| asset_class | 32 marked | the Brookfield listed securities, a mix of common, units, preferreds and notes kept as `equity`; RA and INF as `etf`; the former SPCX |
| active_to | 2 | the former SPCX and its option root, bounded by the new issuer's dates, because the old delisting date is not stored |

## 3. The restriction cannot be weakened

- `restricted` and `restricted_by` are computed at load by
  `register.instruments.Restrictions` over every identifier, alias and the name.
- A `restricted:` line in the YAML is discarded and counted, and the gate fails
  the committed file if it carries one.
- validate_security_master group B:
  - A copy claiming BN `restricted: false` still loads BN as restricted (by its
    root).
  - A claim that SPY is restricted is discarded too.
  - Renaming BN's entry does not clear it.
  - `is_restricted()` falls back to the register's rule for any string the master
    does not know: `bn.to`, `BN.PR.A`, `BEP.UN`, an OCC option, `BN@TSE.CAD`.
- `register/instruments.py`, `register/store.py` and its two block-restricted
  triggers are untouched. The gate checks that the triggers stand and that the
  master imports only the rule, not the register's store.

## 4. The API and the consistency gate

- `Master().resolve(identifier, scheme, on=date)`, `by_id`, `list(asset_class)`
  and `is_restricted`.
- On the command line: `python -m altdata.security_master check | resolve | export`.

The consistency gate (group E):
- **316 identifiers resolve to exactly one entry today.** They come from SYMBOLS
  (yahoo and store key), CRYPTO_BASKET, overnight's SYMBOLS (yahoo and slug),
  `chain_universe()` and `MASSIVE_SYMBOLS` as OCC roots, the basket's coingecko
  ids, and the 29 restricted roots.
- No two entries are active on one identifier at once.
- Every restricted root is flagged, and all 32 restricted entries are the
  Brookfield complex.

## 5. The listings layer

- **`altdata/listings.py`** reads Nasdaq Trader's `nasdaqlisted.txt` and
  `otherlisted.txt` (`https://www.nasdaqtrader.com/dynamic/SymDir/`):
  - It obeys robots.txt through aaii's wildcard-aware reader.
  - It refuses a file without its "File Creation Time" footer, so a truncated
    download is never a day of delistings.
  - It refuses a day under 1,000 listings, and drops test issues.
- **The snapshot** is `data/reference/listings/YYYY-MM-DD.csv`: symbol, name, the
  exchange code as published (`Q` for Nasdaq), market category, ETF flag, source
  file and file time.
  - It is reference data: no registry key, no observation.
- **The change file** is `changes/YYYY-MM-DD.csv`, comparing two consecutive
  snapshots: added, removed, renamed (a reuse candidate).
  - It is never applied to the master.
  - A day whose removals exceed 5% is marked `suspect` in the summary.
- **It runs as one more logger**, `altdata/loggers/listings.py`, in the 06:45
  step. `fetch_overnight.sh` runs `feeds pull --only loggers`, which walks the
  roster, so no script or unit changes and no enable is needed.
  - It has no keys, so the freshness roster does not watch it (needs-you 7).
  - The overnight unit already grants `%h/chester-reports`.
- The fixtures are four hand-written files in the published format plus a
  robots.txt, under `tests/fixtures/security_master/`. The gate never fetches.

The sample change file from the fixtures (`changes/2026-10-14.csv`):

```
change,symbol,old_name,new_name,exchange,previous,snapshot,reuse_candidate
renamed,MEMEA,Meme Alpha Holdings Inc. - Class A Common Stock,Meme Alpha Reborn Corp. - Common Stock,Q,2026-10-13,2026-10-14,Y
added,NEWCO,,Newco Acquisition Corp. Units,N,2026-10-13,2026-10-14,N
removed,OLDCO,Oldco Industries Inc. Common Stock,,A,2026-10-13,2026-10-14,N
```

## 6. The export

`python -m altdata.security_master export [--out PATH]` writes one JSON file,
atomically, to `~/chester-data/export/security_master.json` by default.

**Contents:**
- `schema_version` (`security-master-export-v1`) and `generated_at`.
- `content_hash`: the sha256 of the canonical JSON of instruments and listings,
  outside generated_at.
- `master` (path, version, count) and `listings_snapshot` (its date).
- `instruments`: every field, with `restricted` and `restricted_by`.
- `listings`: the newest snapshot, each row with identifiers, asset class (etf or
  equity by the flag), currency (null; needs-you 3), exchange, active window
  (null), `seen_on` and `restricted`, computed by the same rule from symbol and
  name.

**It is one-way:** the gate fails if any other file in the repo names the export.

The fixture (group G):
- it round-trips and its hash matches;
- an edited copy fails the hash;
- BN exports as restricted in both the instruments and the listings, and GME does
  not.

## Gates

Run locally, one at a time:

| Gate | Result |
|---|---|
| validate_security_master (new) | **47/0** |
| check_library | 0 failures |

CI is the validate for everything else. The loggers roster now holds `listings`,
so validate_events' heartbeat roster group is CI's to confirm. The gate count is
recounted from the Makefile: seventy-five code gates (seventy-two Python, three
shell) and six data gates.

CI: **#416 green** (`d6e5512`, every gate, validate_events included).

## Box commands, printed for Ari, run by no session

All of these run after this branch is on main, inside a window (weekdays
09:05-15:40 or 17:20-23:30 ET; not 16:00-17:20).

```bash
# 1. the export's directory, once
mkdir -p ~/chester-data/export

# 2. a first listings pull (the 06:45 loggers step does it on every trading day after)
cd ~/chester-reports && .venv/bin/python -m altdata.listings pull
.venv/bin/python -m altdata.listings show

# 3. a first export, then its counts
.venv/bin/python -m altdata.security_master check
.venv/bin/python -m altdata.security_master export
python3 -c "import json; d=json.load(open('$HOME/chester-data/export/security_master.json')); print(d['schema_version'], d['content_hash'], len(d['instruments']), len(d['listings']), sum(x['restricted'] for x in d['listings']))"
```

The second pull writes the first change file.

## Files shared with the other branches

Each branch was compared with its merge base and fb67bf3.

| Branch | Shared files |
|---|---|
| aud-1-data-fixes | `CLAUDE.md` (the gate count), `Makefile` (the gate list) |
| aud-2-ops-security | `CLAUDE.md`, `Makefile` |
| alpha-lab-2 | `CLAUDE.md`, `Makefile` |
| aud-3a-catalogue (on origin) | `CLAUDE.md`, `Makefile` |

Each is a one-line gate-list addition plus the count, and one new CLAUDE.md
paragraph before "Known cleanup". The refresh recounts the total once every
branch is in. `altdata/loggers/__init__.py` (one module name in `load_all`) is
shared with none.

## Not named by this paste, so chosen here

1. **The Brookfield complex is in the master** (31 entries plus pre-2022 BAM), so
   the export carries the blocklist as instruments, and listings are flagged by the
   same rule.
2. **SPX and ^GSPC are kept apart**, as is every pair the repo does not say is one
   instrument.
3. **Option roots are their own instruments** with an `underlying`, so a reused
   root (SPCX) gets its own window.
4. **Listings have no currency and no MIC** in the export: the source states
   neither.
5. **The export is not scheduled.** It is a command, as ruled. Running it after the
   listings step each morning would be a one-line addition, needs-you 2.
6. **A 5% removal threshold** marks a suspect day; it writes the file anyway.

## Needs you

1. **The export's format against chester-meme's spec of 11 Oct**, which this
   session cannot read: field names, the hash's definition, and whether listings
   should be keyed by ticker alone. Confirm or send the spec.
2. **Schedule the export** after the listings step in the 06:45 job, or keep it a
   command? schedule / keep
3. **Listings' currency:** rule "a US exchange listing is USD" (then the export
   fills it), or leave null? rule / leave
4. **Exchange MICs:** a reviewed map from Nasdaq Trader's codes (Q, N, A, P, Z, V)
   to MICs, committed as data with its source? yes / no
5. **SPX vs ^GSPC, and the other pairs in inventory item 12:** merge as one
   instrument or keep apart? Each needs a source.
6. **Prediction contracts and IBKR conids** live only in the box's store. Carry
   them in the master (seeded by a read-only box command, like the PM-map draft),
   or leave both schemes empty in v1?
7. **The listings logger is outside freshness** because it writes no registry
   key. Should the heartbeat watch the snapshot file's date instead? That is an
   AUD-3a / heartbeat question.
8. **The 32 entries with an unverified asset class** (the complex's preferreds and
   notes, RA, INF and the former SPCX): add classes such as `preferred` and `note`,
   or keep `equity`?
9. **The move of the call sites** onto the master, one at a time: which first?
   (The yfinance basket is the natural first.)


## 15 Oct

Two parts on this branch, from the paste that replaced the one of 07:26: Part 1,
Ari's answers to the needs-you list; Part 2, the export rebuilt to chester-meme's
contract.

### Part 1: the answers, as built

1. **The export's format:** rebuilt to the contract (Part 2).
2. **Scheduled** as the step after the listings step in the 06:45 job
   (`scripts/fetch_overnight.sh`):
   - first the loggers, which write the day's snapshot;
   - then `python -m altdata.figi map`, the morning FIGI mapping;
   - then `python -m altdata.security_master export`.

   Each step's failure is logged and skipped, never the job's. A morning write is
   well ahead of chester-meme's 19:30 read.
3. **The currency rule.** A listing in Nasdaq Trader's files trades on a US
   exchange in USD.
   - It is stated in `altdata/security_master.py`, `config/listing_exchanges.yaml`
     and CLAUDE.md.
   - It is filled in the master: **120 entries** found in the 15 Oct directories
     carry `currency: USD` and their MIC. The source line names the files'
     creation time (`1015202607:00`).
   - The two files were downloaded once, into a scratch directory, to read them.
     They are not committed.
   - The contract carries no currency.
4. **The MIC map** is `config/listing_exchanges.yaml`. Each code cites the Nasdaq
   Trader definitions page (https://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs),
   and each MIC quotes its line in ISO 10383's CSV
   (https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv).

   | Code | Nasdaq Trader | MIC | Venue |
   |---|---|---|---|
   | Q | a Nasdaq listing; category Q/G/S | XNAS (XNGS, XNMS, XNCM) | Nasdaq |
   | N | New York Stock Exchange (NYSE) | XNYS | NYSE |
   | A | NYSE MKT | XASE | NYSE American |
   | P | NYSE ARCA | ARCX | NYSE Arca |
   | Z | BATS Global Markets (BATS) | BATS | Cboe BZX |
   | V | Investors' Exchange, LLC (IEXG) | IEXG | IEX |

   **Code F** is on 17 of the 15 Oct listings and is not on the definitions page.
   It gets no MIC and venue OTHER (needs-you 3).
5. **SPX and ^GSPC are kept apart.** No issuer or exchange page names both:
   - Cboe's S&P 500 page names SPX only.
   - S&P DJI's page could not be read.

   The SPX entry says so in `sources.not_merged_with`. Inventory item 12 named no
   other pair.
6. **Prediction contracts and IBKR contract ids:**
   `python -m altdata.security_master draft-box` (`altdata/sm_draft.py`).
   - It opens the store mode=ro with query_only on and prints master YAML to the
     screen, with ids proposed from next_id. It writes nothing.
   - It reads the conId key alone, never a size, price or value.
   - Both schemes stay empty until Ari's paste is committed.
7. **The heartbeat watching the listings snapshot's date** is for the refresh
   after aud-1 merges, because the heartbeat is aud-1's file. Not built here.
8. **The new classes** `preferred`, `note` and `closed_end_fund` are added.
   - **30 of the 32** entries are set from a filing, each with its URL and quote
     in `sources.asset_class`:
     - note: BNH, BNJ, BEPH, BEPI, BEPJ, BIPH, BIPI, BIPJ;
     - preferred: BPYPP, BPYPO, BPYPN, BPYPM, DTLAP;
     - closed_end_fund: RA, INF;
     - equity: BN, BAM, BNT, BNRE, BAMR, BEP, BEPC, BIP, BIPC, BBU, BBUC, BPY,
       BPYU, OAK, OCSL.
   - **BIRET stays unverified.** No issuer or exchange page could be read; it is
     an NSE listing in INR.
   - **The former SPCX** is "The SPAC and New Issue ETF", an etf (SEC 497K).
     - Its ticker became **SPCK on 7 Apr 2026** (newsfilecorp release 291300).
     - Its entry carries `ticker_history`: SPCX to 2026-04-06, SPCK from
       2026-04-07.
     - Nobody held SPCX from 7 Apr to 11 Jun 2026.
   - **Also from the filings:**
     - INF merged into RA before the open on 9 Mar 2020, so `active_to` is
       2020-03-08.
     - BBU was exchanged into BBUC on 27 Mar 2026, so `active_to` is 2026-03-26.
       Its last trading day is not stated, so that date is unverified.
     - BN and the pre-2022 BAM are one security. BN's entry carries
       `ticker_history`: BAM to 2022-12-08, BN from 2022-12-09.
     - `SM00165` keeps its id with `merged_into: SM00163`.
9. **The call sites move onto the master** after aud-1 and this branch merge, the
   yfinance basket first. Listed; not started.

### Part 2: the export to chester-meme's contract

- **The contract files.**
  - `docs/interface/security_master.schema.json`, `decision_packet.schema.json`
    and `README-interface.md` are copied from the chester-meme checkout, which was
    read only.
  - They are LF, and `.gitattributes` keeps them LF (`docs/interface/* text
    eol=lf`).
  - Their SHA-256 over LF is as the paste gives it: `5288446f…78fb2`,
    `e3e97e0e…569522`, `bfe8ec7c…87a421`. Gate group G pins all three.
- **The FIGI mapper:** `altdata/figi.py`, `python -m altdata.figi map [--all]`.
  - Each US listing goes to OpenFIGI's `/v3/mapping` with exchange code US, the
    ticker in OpenFIGI's form (BRK.B → BRK/B, ABR$D → ABR/PD, AAC.W → AAC/WS).
  - It keeps, under `data/reference/figi/`:
    - `cache.json`: the composite FIGI, the share-class FIGI, the security type
      and the name, plus a FIGI-keyed record that is never pruned, so a holder
      that lost its ticker still exports;
    - `assignments.csv`: an append-only log of which FIGI a symbol was mapped to,
      from which day.
  - **The limits:**
    - keyless: 25 requests a minute, 10 jobs a request;
    - with OPENFIGI_API_KEY (optional, from `.env` through altdata.secrets, never
      printed): 25 requests per 6 seconds, 100 jobs a request;
    - a 429 waits the server's reset.
  - **Each morning** it maps only symbols that are new, renamed or not yet mapped,
    capped at 50 requests (500 symbols, about 2 minutes keyless) to fit the 06:45
    job.
  - A symbol OpenFIGI cannot map is listed with the reason, retried after 7 days,
    and never exported.
  - The fixtures are saved responses in the API's shape, with fixture FIGIs. The
    gate never fetches.
- **The ticker history:** `altdata/ticker_history.py`, rebuilt each morning from
  the snapshots (streamed a day at a time), the assignment log and the master's
  known windows.

  | Event | Result |
  |---|---|
  | rename, same FIGI | nothing changes |
  | ticker change, same FIGI | the old row closes and a new one opens on the snapshot date |
  | reuse, a new FIGI on a known ticker | the old holder closes with an exact, exclusive `effective_to` on the snapshot date; the new holder opens from it |
  | the master's known reuses | real dates: BN held BAM to 2022-12-09 and the new BAM from then; the ETF held SPCX to 2026-04-07, then SPCK; SpaceX holds SPCX from 2026-06-12 |
  | unknown start | `effective_from: 1900-01-01`, `from_known: false` |
  | delisting | the row closes |
  | a later new listing | a row from its snapshot date |

  The master's active_to is inclusive, so a window ending on D exports
  `effective_to` D+1.
- **The export:** `altdata/sm_export.py`, in the contract's shape.
  - Top level: `schema_version` "1.0", `exported_at` UTC with a Z, `source`
    "chester-reports".
  - Each security: figi, share_class_figi, cik (null), name, type, venue, active
    and ticker_history, with tickers in ACT form.
  - The two allowed extras: `restricted`, by register.instruments' rule over every
    ticker held and the name; and `from_known` on each row.
  - `type` comes from OpenFIGI's securityType, then securityType2, then the ETF
    flag. Anything else is OTHER, and the summary counts each OTHER's OpenFIGI
    type.
  - `venue` comes from the exchange code. An inactive holder's venue is null.
  - Only US listings with a FIGI are exported.
  - The file is validated against the committed schema before it is written, and
    written atomically (`.tmp`, then rename). An invalid file is never written,
    and the run exits 1 with the errors.
  - **jsonschema** is in requirements.txt (the laptop has 4.26.0). With no
    validator, nothing is written. **The self-deploy installs no packages**
    (`deploy_remote.sh` has no pip step), so its install is a box command below.
  - The path: `$CHESTER_SM_EXPORT`, else `~/chester-data/export/security_master.json`.
    The overnight unit already grants `-%h/chester-data`.

A sample of the fixture export (two hand-written days, saved responses):

```
{"figi": "BBG000FXRU01", "name": "REUS HOLDINGS", "type": "CS", "venue": null, "active": false,
 "ticker_history": [{"ticker": "REUS", "effective_from": "1900-01-01", "effective_to": "2026-10-14", "from_known": false}], "restricted": false}
{"figi": "BBG000FXRV02", "name": "REUS ACQUISITION CORP-A", "type": "CS", "venue": "NYSE American", "active": true,
 "ticker_history": [{"ticker": "REUS", "effective_from": "2026-10-14", "effective_to": null, "from_known": true}], "restricted": false}
{"figi": "BBG000FXBN01", "name": "BROOKFIELD CORP", "type": "CS", "venue": "NYSE", "active": true,
 "ticker_history": [{"ticker": "BAM", "effective_from": "1900-01-01", "effective_to": "2022-12-09", "from_known": false},
                    {"ticker": "BN", "effective_from": "2022-12-09", "effective_to": null, "from_known": true}], "restricted": true}
```

### Gates (locally, one at a time)

| Gate | Result |
|---|---|
| validate_security_master | **80/0**. Groups A–K: the master, the restriction, reuse, the API, consistency, listings, the contract files, the mapper, the history and the export, the box draft, the 06:45 order |
| check_library | 0 failures |

Other gates that read `fetch_overnight.sh` are CI's. CI: in the report.

### Box commands, printed for Ari, run by no session

All after this branch is on main, inside a window (weekdays 09:05–15:40 or
17:20–23:30 ET).

```bash
# 1. the validator (the self-deploy installs no packages)
cd ~/chester-reports && .venv/bin/pip install 'jsonschema>=4.18'

# 2. the export's directory, and a first listings pull
mkdir -p ~/chester-data/export
.venv/bin/python -m altdata.listings pull && .venv/bin/python -m altdata.listings show

# 3. the first full FIGI mapping: ~13,250 listings, ~55 minutes keyless, ~2 with a key
nohup .venv/bin/python -m altdata.figi map --all > ~/logs/figi_first_map.log 2>&1 &
.venv/bin/python -m altdata.figi show | head -60        # when it has finished

# 4. the first export, and its counts
.venv/bin/python -m altdata.security_master export
.venv/bin/python -c "import json, os; d = json.load(open(os.path.expanduser('~/chester-data/export/security_master.json'))); print(d['schema_version'], d['exported_at'], len(d['securities']), sum(s.get('restricted', False) for s in d['securities']))"

# 5. the store-only schemes, drafted read-only: paste the output into chat
.venv/bin/python -m altdata.security_master draft-box
```

**The MEME_SM_EXPORT line** goes wherever chester-meme takes its environment,
its `.env` or its unit's `Environment=`. This session read only the three
contract files, so it cannot say which:

```
MEME_SM_EXPORT=/home/ari/chester-data/export/security_master.json
```

### Needs you

1. **The sentinel, on chester-meme's side.** Confirm that the guard (R-T1a-3)
   reads `effective_from: 1900-01-01` with `from_known: false` as "keep the
   present assumption", so an unknown start repairs nothing and wipes nothing.
2. **The first full mapping's unmapped list** (box command 3) tests the ACT →
   OpenFIGI ticker conversion, above all for preferreds (`$`), warrants and units.
   Paste `figi show`.
3. **Exchange code F** (17 listings on 15 Oct) is not on Nasdaq Trader's page.
   Name a source, or keep it OTHER.
4. **OTHER types:** the first export's summary counts the OpenFIGI types that map
   to OTHER. Rule any that belong elsewhere.
5. **BNT, BNRE and BAMR** share one SEC registrant (CIK 1837429): one security
   under three tickers. The change dates are not in the filings read. Supply them,
   and they become one entry with a ticker history.
6. **Still unverified:** BBU's last trading day and BIRET's class.
7. **The draft-box output** (box command 5), to commit the prediction contracts
   and IBKR contract ids.
8. **For the refresh:**
   - the heartbeat watches the listings snapshot's date (answer 7);
   - the call sites move onto the master, the yfinance basket first (answer 9).
