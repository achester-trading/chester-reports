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

CI: the push's number is in the line below.

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
