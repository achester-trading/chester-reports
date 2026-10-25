# Off yfinance: the price-source migration brief (B68, session B, 25 Oct 2026)

**Status: DRAFT for Doctrine #2 (7–8 Nov 2026), which rules on the plan and the deadline.** Written on branch `b68-price-source-migration` from `origin/b67-quarterly-source-checks`. Docs, plus one read-only inventory script, `tools/price_source_inventory.py`. No reader is built, no source is cut over, and the live pull is not touched.

**The ruling this serves (D33, 24 Oct 2026).** Yahoo's chart host, `query1.finance.yahoo.com`, disallows every automated agent in robots.txt (B67 read it: `User-agent: *`, `Disallow: /`). Yahoo's terms forbid automated collection: users may not "access or collect data ... from our Services using any automated means ... for any purpose without our express written permission". The system's live yfinance source uses that host for the whole price basket. The ruling has four parts:
- no new yfinance symbols from today;
- the existing pull keeps running until a replacement is live;
- this brief maps every yfinance key to a licensed or public replacement, with hours and a cutover plan;
- Doctrine #2 rules on the plan and the deadline, with the exposure stated beside it.

**Method.** Each candidate source got one keyless request for its robots.txt and terms, and one for a sample where the terms allow. All went out on 25 Oct 2026 with the generic project User-Agent (`altdata/sources/user_agent.py`). Where a terms page was not at the first URL, the located page was read once.

None of these requests went to Yahoo. None went to the sources the repository already records as refused: CME's pages (AQ-3: "CME prohibits scripted access"), Stooq (AQ-3: robots `Disallow: /`) and Bybit ("geo-blocked from the US and switched off", CLAUDE.md). Nothing was stored but this brief and the script.

---

## 1. The exposure, measured

`python -m tools.price_source_inventory` reads the registries and the code's symbol tables. It opens no store, makes no request and writes nothing.

The registry declares no start date for these keys. So "history" below is the code's declared pull:
- the routine period, `LOOKBACK_PERIOD` "2y";
- `tools/backfill_prices.py`'s five years, with `--period max` for ^GSPC and ^VIX;
- the long-history symbols' documented starts.

None of it is measured from the store.

Readers are counted by a literal match of each key, or of the shared list it is read through, in the tree's `.py`, `.yaml` and `.sh` files. The roles are writers, computations, reports, ledgers, the lab, gates and config. A reader that reaches a key only through a generic loop over `SYMBOLS` is counted under the basket's writer, not by name.

**The tool's output (25 Oct 2026):**

| Group | Keys | Symbols | Readers by role (files) | History (the code's) | Stops if Yahoo stopped today |
|---|---|---|---|---|---|
| Price basket: US equity index funds | 5 | 5 | writers 1; ledgers 1; lab 3; reports 6; gates 35; computations 9; config 15; other tools 2; other 3 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD); tools/backfill_prices.py: five years for every symbol, availability RECONSTRUCTED; `--period max` for ^GSPC and ^VIX | the closes stop: every return, percentile, lens and chart on that family |
| Price basket: Sector funds | 13 | 13 | writers 2; reports 2; gates 10; computations 1; config 7; other tools 1; other 1 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD); tools/backfill_prices.py: five years for every symbol, availability RECONSTRUCTED; `--period max` for ^GSPC and ^VIX | the closes stop: every return, percentile, lens and chart on that family |
| Price basket: Style funds | 4 | 4 | writers 1; reports 1; gates 1; config 1 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD); tools/backfill_prices.py: five years for every symbol, availability RECONSTRUCTED; `--period max` for ^GSPC and ^VIX | the closes stop: every return, percentile, lens and chart on that family |
| Price basket: Rates and credit funds | 9 | 9 | writers 1; gates 12; computations 4; config 9; other tools 1; other 1 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD); tools/backfill_prices.py: five years for every symbol, availability RECONSTRUCTED; `--period max` for ^GSPC and ^VIX | the closes stop: every return, percentile, lens and chart on that family |
| Price basket: Commodity and real-asset funds | 8 | 8 | writers 1; reports 1; gates 11; computations 2; config 9 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD); tools/backfill_prices.py: five years for every symbol, availability RECONSTRUCTED; `--period max` for ^GSPC and ^VIX | the closes stop: every return, percentile, lens and chart on that family |
| Price basket: International and EM funds | 18 | 18 | writers 1; gates 8; computations 1; config 8 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD); tools/backfill_prices.py: five years for every symbol, availability RECONSTRUCTED; `--period max` for ^GSPC and ^VIX | the closes stop: every return, percentile, lens and chart on that family |
| Price basket: Thematic and replication funds | 6 | 6 | writers 1; gates 4; config 5; other 1 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD); tools/backfill_prices.py: five years for every symbol, availability RECONSTRUCTED; `--period max` for ^GSPC and ^VIX | the closes stop: every return, percentile, lens and chart on that family |
| Price basket: Single names | 34 | 34 | writers 2; ledgers 5; lab 1; reports 4; gates 36; computations 11; config 24; other tools 3; other 1 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD); tools/backfill_prices.py: five years for every symbol, availability RECONSTRUCTED; `--period max` for ^GSPC and ^VIX | the closes stop: every return, percentile, lens and chart on that family |
| Price basket: Index levels (Cboe, S&P, ICE) | 12 | 12 | writers 2; ledgers 5; lab 1; reports 4; gates 30; computations 12; config 25; other tools 2; other 1 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD); tools/backfill_prices.py: five years for every symbol, availability RECONSTRUCTED; `--period max` for ^GSPC and ^VIX; ^GSPC daily from 1927-12-30 and ^VIX from 1990-01-02 (yfinance_source's THE LONG HISTORY comment) | the closes stop: every return, percentile, lens and chart on that family |
| Price basket: Yield proxies | 2 | 2 | writers 1; reports 1; gates 8; computations 2; config 4; other tools 1; other 1 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD); tools/backfill_prices.py: five years for every symbol, availability RECONSTRUCTED; `--period max` for ^GSPC and ^VIX | the closes stop: every return, percentile, lens and chart on that family |
| Price basket: Futures fronts (gold, oil, copper, products, the 10-year note) | 6 | 6 | writers 2; reports 2; gates 11; computations 4; config 12; other 2 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD); tools/backfill_prices.py: five years for every symbol, availability RECONSTRUCTED; `--period max` for ^GSPC and ^VIX | the closes stop: every return, percentile, lens and chart on that family |
| Price basket: FX rates | 6 | 6 | writers 1; reports 5; gates 15; computations 3; config 8; other tools 1; other 1 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD); tools/backfill_prices.py: five years for every symbol, availability RECONSTRUCTED; `--period max` for ^GSPC and ^VIX | the closes stop: every return, percentile, lens and chart on that family |
| Price basket: Crypto in the basket | 4 | 4 | writers 4; lab 1; reports 2; gates 9; config 11; other 1 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD); tools/backfill_prices.py: five years for every symbol, availability RECONSTRUCTED; `--period max` for ^GSPC and ^VIX | the closes stop: every return, percentile, lens and chart on that family |
| Crypto basket (config/crypto_basket.yaml) | 12 | 12 | writers 1; reports 1; gates 7; computations 1; config 2; other tools 1; other 1 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD); tools/backfill_prices.py: five years for every symbol, availability RECONSTRUCTED; `--period max` for ^GSPC and ^VIX | the crypto basket's closes and the Digital Assets addendum's price rows |
| OHLC companions (_open/_high/_low) | 33 | 11 | writers 1; gates 4; config 1; other tools 1; other 1 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD); tools/backfill_prices.py: five years for every symbol, availability RECONSTRUCTED; `--period max` for ^GSPC and ^VIX | ranges, ATR and the ES/levels reads that use daily highs and lows |
| Volume (_volume) | 107 | 107 | writers 6; ledgers 1; lab 2; reports 8; gates 19; computations 8; config 8; other tools 3; other 2 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD);  backfill (`--volume-only`) | the volume shares, Amihud's depth stand-in (item 71) and the volume profile's daily approximation |
| Dividends and splits (_dividend/_split) | 254 | 127 | writers 2; ledgers 4; reports 6; gates 6; computations 4; config 3; other tools 4; other 1 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD); tools/backfill_prices.py: five years for every symbol, availability RECONSTRUCTED; `--period max` for ^GSPC and ^VIX | total-return computations (no new actions recorded) |
| The notes' 5-minute bars (note_bars_prices) | 12 | 12 | writers 1; gates 1; other 1 | intraday;  the session only | the 09:50 and 21:30 notes' bars and first-hour readings |
| The tape set's bars (bars_prices and volume) | 17 | 0 | writers 1; gates 3; other 1 | intraday 5-minute and daily frames | the ES block, the volume profile and the session tables |
| Overnight levels and changes (the 07:00 anchor) | 46 | 10 | writers 3; reports 2; gates 12; computations 4; config 3; other tools 1; other 4 | intraday;  forward only | the 07:00 anchor's overnight block and gap attribution |
| The pin log's columns (tools/pin_log.py) | 83 | 0 | reports 2; gates 10; computations 3; other tools 3; other 3 | forward only | the pin log's spot and settlement columns |
| S&P 500 members' closes (registry source sp500_members; values from Yahoo) | 1 | 0 | writers 1; ledgers 2; gates 3; computations 2; config 3; other 1 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD) | the breadth histogram, the average-member gap, the top-10 share and the dispersion fallback |
| Registry entries, source yfinance | 74 | 0 | writers 4; lab 3; reports 2; gates 18; computations 7; config 9; other 2 | none: the registry's yfinance entry says it 'serves NO history for option chains, so an uncaptured session is lost permanently' | the option chains (and every exposure.* reading the dealer engine computes from them), earnings dates and consensus, ZEC's price rows, fed funds futures |
| Registry entries, source yfinance_fundamentals | 40 | 0 | config 1; other 1 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD) | the hyperscaler cash-flow bridge's quarterly fundamentals |
| Registry entries, source yahoo_cnh | 1 | 0 | writers 1; reports 1; gates 2; computations 2; config 2; other tools 1; other 1 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD) | USD/CNH's hourly-derived daily close |
| Registry entries, source yahoo_set | 1 | 0 | writers 1; gates 1; other 1 | the routine pull's period is '2y' (yfinance_source.LOOKBACK_PERIOD) | the SET index close |
| **All groups (keys can appear in two groups)** | **808** | | | | |

Registry bulk blocks whose source is Yahoo, with their declared member counts: `market_closes` 127, `market_ohlc` 11, `market_volume_shares` 97, `market_volume_contracts` 6, `market_volume_usd` 4, `note_bars_prices` 12, `bars_prices` 10, `bars_volume_shares` 3, `bars_volume_contracts` 3, `bars_volume_usd` 1, `market_actions` 127, `pin_log_columns` 83, `overnight_levels` 36, `overnight_percent_changes` 10, `crypto_basket_closes` 12, `crypto_basket_volume` 12.

Files that call Yahoo directly (`import_yfinance()`), gates excluded: `altdata/bars.py`, `altdata/dealer_capture.py`, `altdata/fed_funds.py`, `altdata/fx_charts.py`, `altdata/ledgers/sources.py`, `altdata/loggers/consensus.py`, `altdata/note_fetch.py`, `altdata/sources/cnh.py`, `altdata/sources/earnings.py`, `altdata/sources/fundamentals.py`, `altdata/sources/options_chain.py`, `altdata/sources/overnight.py`, `altdata/sources/sp500_members.py`, `altdata/sources/thai_set.py`, `altdata/sources/yfinance_source.py`, `tools/calibration/sn1_release_first_hour.py`, `tools/calibration/sn2_after_hours_earnings.py`, `tools/calibration/st8_common.py`, `tools/calibration/st_r6_71d_air_pockets.py`.


**What the table says, in four sentences.**
- The price basket is 127 symbols in thirteen families. Its closes, OHLC, volume and corporate actions are 127 + 33 + 107 + 254 keys. Every return, percentile, lens, chart and the market-state object's price-based dimensions read them.
- Yahoo also serves things the basket table hides:
  - the option chains the dealer engine computes from (`altdata/sources/options_chain.py`; the registry's yfinance entry lists it as an implementer);
  - the 09:45 and 12:30 captures' spot (`altdata/dealer_capture.py`, `fast_info`);
  - every S&P 500 member's daily close, `sp500.member_close`, through `yf.download()`. That key's registry source is `sp500_members`, so the registry understates the exposure.
- Yahoo also serves:
  - the fed funds futures (`altdata/fed_funds.py`);
  - earnings dates and consensus (`altdata/sources/earnings.py`, `altdata/loggers/consensus.py`);
  - the hyperscaler fundamentals (`yfinance_fundamentals`, 40 keys);
  - USD/CNH (`yahoo_cnh`) and the SET index (`yahoo_set`);
  - the overnight block (ES, NQ and the foreign cash indices);
  - the notes' 5-minute bars;
  - four calibration scripts' public history pulls.
- **If Yahoo stopped today**, prices, the dealer block, the breadth and concentration panels, the overnight block, the notes' bars, earnings dates and the fundamentals bridge would all stop updating. The reports would print STALE and PENDING with their reasons, as built, but nearly every chapter would be on stale rows within a session.

---

## 2. The candidates, against the 16 Oct rule

### 2a. IBKR market data through the running IB Gateway
- **Verdict: PASSES WITH LIMITS** (own use, not redistributable; a subscription for some families; pacing).
- **What the box already does.** `altdata/ibkr_clients.py` names six client ids: `portfolio_sync` 17, `watchdog` 18, `costs` 19, `whatif` 20, `auction` 23 and `borrow` 25. Each connects to the paper account's gateway for its own read, and none requests historical bars. The registry's `ibkr_paper` is "PAPER account. ... brokerage account; not redistributable". A market-data writer would take a new id in that table.
- **Subscriptions already held**, as the registry records them, each "exchange market-data subscription via IBKR; not redistributable", "subscribed: 2026-09-05", "account: live, shared to paper", status `not_yet_used`:

  | Subscription | Monthly |
  |---|---|
  | OPRA Level 1 | USD 1.50 |
  | Cboe Streaming Market Indexes | USD 3.50 |
  | NYSE Order Imbalances | USD 3.00 |
  | CFE Enhanced | USD 4.50 |

  The operator confirms these are still active.
- **Published prices and the free tier** (https://www.interactivebrokers.com/en/pricing/market-data-pricing.php, read 25 Oct 2026):
  - "IBKR clients receive free real-time streaming market data on all US-listed stocks and ETFs from Cboe One and IEX. (Non-consolidated)";
  - "IBKR clients receive free delayed market data on other products where available";
  - the waiver table lists "US Securities Snapshot and Futures Value Bundle USD 10.00", waived at "USD 30.00" of commissions, and "OPRA Top of Book (L1)(US Option Exchanges) USD 1.50", waived at "USD 20.00".
  - The bundle covers US stocks, indices, bonds, futures and futures options per IBKR's knowledge base, as indexed; the operator confirms.
- **Delayed data without a subscription** (https://interactivebrokers.github.io/tws-api/delayed_data.html): "10-15 minute delayed streaming data is available for many types of instruments without market data subscriptions", via `reqMarketDataType(3)`. That page is marked deprecated in favour of IBKR Campus.
- **Pacing** (https://interactivebrokers.github.io/tws-api/historical_limitations.html). A pacing violation is:
  - "Making identical historical data requests within 15 seconds";
  - "Making six or more historical data requests for the same Contract, Exchange and Tick Type within two seconds";
  - "Making more than 60 requests within any ten minute period".

  At 60 requests per ten minutes, the 127-symbol basket's daily refresh is about 22 minutes of requests. The 500 S&P members would be about 84 minutes, which argues for a grouped source for the members (2b).
- **The gateway's read-only setting** permits market-data and historical requests. Read-only blocks orders, not data. The live port is denied (`--allow-live`), so the writer reads the paper account's shared entitlements.
- **Not checked from here:** whether historical daily bars for US stocks need the bundle, or are served under the free Cboe One/IEX feed (the free feed is "non-consolidated"). The operator's facts to confirm come first (Notes).

### 2b. Massive (ex-Polygon)
- **Verdict: PASSES WITH LIMITS** (individual use; the Stocks plan is a purchase; the price is unverified from here).
- **Terms** (https://massive.com/legal/terms): "The Massive for Individuals Terms of Service apply to your personal, individual, and non-business use of any service or product labeled for 'Individual Use'." The registry's `massive` entry is the Options Starter: "paid subscription, Starter tier", with `history_depth: 2 years, rolling` and `index_level: NOT entitled -- I:SPX aggregates return HTTP 403`.
- **The Stocks plan's price** did not render in the pricing page's text (it loads in script). A third-party guide lists individual Stocks plans at USD 29, 79 and 199 a month. The operator confirms on Massive's own page.
- **Why it matters:** a grouped daily endpoint returns every US stock in one call, which IBKR's pacing cannot match for the 500 members.
- **Currencies Basic and Futures Basic:** the paste names these tiers as held, but nothing in the repository records them, in the registry or in code. Their coverage is the operator's fact to confirm. The flat files used today are the options day bars (`tools/massive_flatfiles_backfill.py`, `altdata/flatfile_history.py`), under the Options Starter.

### 2c. FRED for index-level dailies
FRED is already pulled with the system's key (the API route; FRED's legal FAQ forbids "data mining, scraping or extraction" outside it). Each series page was read:

| Series | Copyright on the series page | Verdict | Replaces |
|---|---|---|---|
| `SP500` | "Reproduction of S&P 500 in any form is prohibited except with the prior written permission of S&P Dow Jones Indices LLC"; "FRED and its associated services will include 10 years of daily history" | **FAILS** for storage | not ^GSPC |
| `DJIA` | the same S&P DJI notice; tag "Copyrighted: Pre-Approval Required" | **FAILS** | — |
| `NASDAQCOM` | tag "Copyrighted: Pre-Approval Required" (Nasdaq, Inc.) | **FAILS** | — |
| `VIXCLS` | "Copyright, 2016, Chicago Board Options Exchange, Inc. Reprinted with permission"; tag "Copyrighted: Citation Required" | PASSES WITH LIMITS (cite; own use); already pulled as `fred.vix` | a cross-check for ^VIX; Cboe's own file is primary (2d) |
| `DGS10`, `DGS30` (H.15) | public domain (the Board's H.15) | **PASSES**; already pulled | ^TNX, ^TYX, with a labelled convention break |
| `DTWEXBGS` | tag "Public Domain: Citation Requested" | **PASSES** | **not** DX-Y.NYB one for one: a different index (the broad nominal dollar, not ICE's six-currency DXY); a labelled series change |
| `DEX*` (H.10) | public domain; already pulled (`fred.usd_*`) | **PASSES** | JPY=X, EURUSD=X, EURCHF=X (as a cross), CNY=X; not TRY or IDR (not in H.10) |
| `DCOILWTICO`, `DHHNGSP` (EIA spot) | tag "Public Domain: Citation Requested" | **PASSES** | **not** CL=F: spot, not the front future; a labelled series change |

### 2d. Cboe's public files; CME's pages
- **Cboe: PASSES**, already read. The registry's `cboe_indices`: "public CSVs, no key (cdn.cboe.com/api/global/us_indices/daily_prices/<SYM>_History.csv ...); robots.txt on cdn.cboe.com and cdn-api.cboe.com answers 403 (no rules, RFC 9309)". The same pattern is the candidate for VIX, VIX9D, VIX3M, VIX6M, VVIX and SKEW. One request per file at build confirms each symbol's file exists.
- **CME: not requested.** AQ-3 part 1 recorded "HTTP 403 with CME's notice that scripted access is blocked and prohibited by its Data Terms of Use". The futures fronts therefore go to IBKR (2a).

### 2e. Fallbacks: Stooq, Tiingo, Alpha Vantage
- **Stooq: FAILS**, not requested (AQ-3 part 2: "stooq's robots.txt is `Disallow: /`").
- **Tiingo: FAILS.** Its terms were not located (two URLs answered 404), and its free tier needs an account key. Friction is a gap, not a key.
- **Alpha Vantage: FAILS.** The free tier needs a key, and its terms page, https://www.alphavantage.co/terms_of_service/, rendered no readable text to the check.

### 2f. Crypto: the exchanges' public candles
- **OKX: PASSES WITH LIMITS.** It is already a live source for perp funding (`perp_venues`). One request to `api/v5/market/history-candles?instId=BTC-USDT&bar=1D` answered HTTP 200 with JSON daily candles; robots allows it. The registry's existing terms record for the venue applies.
- **Coinbase Exchange: PASSES WITH LIMITS.** One request to `products/BTC-USD/candles?granularity=86400` answered HTTP 200 with JSON `[time, low, high, open, close, volume]`. The Market Data Terms (https://www.coinbase.com/legal/market_data) say:
  - "Your use of Market Data is exclusively for you or your entity's personal or research purposes";
  - no redistribution, display or dissemination of the data or Derived Works "to any third party outside of your organization";
  - no use to create "(i) indexes, fixings, or other benchmarks; (ii) generic or fair value prices; or (iii) valuations of any investment product, digital currency ..."

  The last clause bars Coinbase prices from **marking** anything: the lab's crypto carry book, a paper position or a benchmark. So Coinbase can be a cross-check, never the mark.
- **Kraken: FAILS** for now. The OHLC endpoint answered HTTP 200 (keyless), but the terms page was not located; `/legal/terms` answered 404.
- **Bybit:** not requested (switched off, geo-blocked).

---

## 3. The mapping

**A "labelled break"** means the new source's rows go under new keys, starting at the cutover date. The old yfinance keys are superseded in the registry, and their history stays as stored. Nothing is restated, and a reader that joins the two prints the break's date.

**"Backfill honest?"** asks whether rows can be written with an `available_at` no earlier than the new source could have served them:
- a daily close at the session's close plus the source's declared delay;
- an intraday bar at its own close;
- otherwise, forward only.

| Group | Replacement | Terms | Cost | History | Backfill honest? | What changes in the printed figure |
|---|---|---|---|---|---|---|
| US equity, sector, style, rates, credit, commodity, international and thematic funds; single names | **IBKR** historical daily TRADES bars | own use, not redistributable | the bundle, USD 10 (waived at USD 30 commissions), if historical bars need it | to probe | yes, RECONSTRUCTED at close plus a declared delay, as `backfill_prices` does today | IBKR's bar close against Yahoo's official close: a labelled break; unadjusted stays unadjusted |
| S&P 500 members' closes | **Massive** grouped daily (Stocks plan) | individual use | the plan (unverified) | the plan's depth | yes, as above | the same break |
| Index levels: VIX family, VVIX, SKEW, DSPX, COR1M, COR3M | **Cboe** files | public CSVs | none | Cboe's (COR from 2006, DSPX from 2014 per the registry) | yes, at the file's Last-Modified | none in value; a source change |
| ^GSPC | **IBKR** index (the Cboe indexes subscription held) | own use | held, USD 3.50 | to probe | forward from the probe; the stored history from 1927 stays | a labelled break |
| ^MOVE | none found | — | — | — | — | **a listed gap** unless IBKR serves it |
| DX-Y.NYB | `fred.dxy_broad` (DTWEXBGS) | public domain | none | from 2006 | yes (H.10's lag) | a different index: a labelled series change, never a splice |
| ^TNX, ^TYX | `fred.yield_10y` (DGS10), DGS30 | public domain | none | decades | yes, at H.15's publication | constant-maturity yield against Cboe's ×10 index: a labelled break |
| Futures fronts: GC, CL, HG, RB, HO, ZN | **IBKR** continuous futures | own use | the bundle covers futures | to probe | yes, at settlement plus delay | settlement against last trade: labelled |
| FX: JPY, EURUSD, EURCHF, CNY | `fred.usd_*` (H.10) for the daily fix; **IBKR** IDEALPRO for continuous | public domain / own use | none / free FX on IBKR to confirm | decades / to probe | yes | the noon fix against Yahoo's close: labelled |
| FX: TRY, IDR | **IBKR** IDEALPRO | own use | to confirm | to probe | yes | labelled |
| Crypto, the basket's 4 and the crypto basket's 12 | **OKX** daily candles | the venue's terms (registry) | none | the venue's | yes, at the UTC day's close | the venue's close against Yahoo's aggregate: labelled; a name OKX does not list is a listed gap |
| OHLC companions | the replacement's daily bars | as above | — | — | as above | as above |
| Volume | the replacement's bars | as above | — | — | as above | IBKR may report US equity volume in round lots: the unit checked against IBKR's documentation at build, never assumed |
| Dividends and splits | **Massive** reference endpoints (Stocks plan), or a listed gap | individual use | the plan | the plan's | yes, at the announcement date | none in value |
| The notes' 5-minute bars, the tape set's bars | **IBKR** intraday bars | own use | the bundle | the session | an intraday bar at its own close | the bar's open-close convention, checked |
| Overnight: ES, NQ, BTC | **IBKR** futures; OKX for BTC | own use | the bundle | forward | at each bar's close | labelled |
| Overnight: ^N225, ^STOXX50E, ^FTSE | none keyless | — | — | — | — | **listed gaps** unless the operator buys the exchanges' feeds |
| Option chains (the 19 captured names) | **Massive** Options Starter (held), already writing the vendor chains | paid, held | held | 2 years rolling | captures are forward only, as now | the vendor's 15-minute delay, already labelled (`vendor_data_as_of`) |
| The captures' spot | **IBKR** snapshot, or the Massive chain's underlying | own use | held | — | forward | none |
| Fed funds futures | **IBKR** (CBOT) | own use | the bundle | to probe | yes | labelled |
| Earnings dates | EDGAR filing dates for actuals; the calendar a listed gap | public (contact) | none | EDGAR's | yes | dates from filings, not the vendor's calendar |
| Consensus | none keyless | — | — | — | — | **a listed gap** (macro releases already print "no consensus") |
| Fundamentals (40) | **EDGAR XBRL** (`edgar_xbrl`, live) | public | none | EDGAR's | yes, at the filing's acceptance | the filed value, not Yahoo's restated one |
| USD/CNH hourly | **IBKR** IDEALPRO CNH | own use | to confirm | to probe | yes | labelled |
| The SET index | none keyless (AQ-3: the SET's endpoints answer an Incapsula challenge) | — | — | — | — | **a listed gap** |
| ZEC's price rows | OKX, if listed; else a listed gap | venue terms | none | — | yes | labelled |
| The calibration scripts' public pulls | FRED, Cboe, Massive's history | as above | — | — | — | a new edition names its source; old editions are never edited |

---

## 4. The cutover plan

1. **Parallel running.** Each new writer runs beside the yfinance pull for **20 sessions** (decision 8), under its own keys. A cross-source check joins each pair in `config/data_quality.yaml`, the way the ^VIX/VIXCLS pair is measured today. Its tolerance is measured on the overlap and stated with its reason, never assumed.
2. **The switch, per family.** Once a family's 20 sessions are inside tolerance:
   - every reader of its yfinance keys moves to the new keys in one commit per family;
   - the old keys are marked `status_extra: superseded` with `superseded_by` in the registry, as `yfinance.mkt_usdcnh` already is;
   - the history stays as stored.
3. **The yfinance pull retired last,** after every family has switched or been declared a listed gap: the basket's writer, `options_chain.py`'s chain fetch, and the other direct callers named in section 1.
4. **What the Weekly prints during the overlap.** Its "what doesn't fit" section carries one line per family in parallel: "prices: <family> in parallel run, day k of 20, max gap x within tolerance y". It also prints any session outside tolerance, by key.
5. **The point-in-time rule throughout.** No row's `available_at` is earlier than it could have been known from the new source:
   - a daily bar at the session's close plus the declared delay;
   - an intraday bar at its own close;
   - a FRED row at its release.

   A backfill uses RECONSTRUCTED availability, as `backfill_prices` does.

---

## 5. Costs and hours

| Family | Writer | Subscription | Hours |
|---|---|---|---|
| The IBKR daily-bars writer (funds, single names, futures, FX, ^GSPC): the shared client, contracts through the Security Master's `ibkr_conid`, pacing at 60 per ten minutes | `altdata/sources/ibkr_bars.py` | the bundle, USD 10 (waived at USD 30 commissions), if needed | 10 |
| The Cboe index files (VIX family, VVIX, SKEW) | extend `cboe_indices.py` | none | 2 |
| FRED replacements (yields, the dollar, H.10 FX): the readers move; no new pull | config and readers | none | 2 |
| Crypto through OKX | extend the venue writer | none | 3 |
| S&P 500 members and corporate actions through Massive | `massive_stocks.py` | the Stocks plan, unverified | 4 |
| Intraday bars (the notes, the tape set) through IBKR | extend `bars.py` | the bundle | 4 |
| Overnight (ES, NQ, BTC) | extend `overnight.py` | the bundle | 3 |
| Option chains: the 19 names to Massive | `vendor_chains.py` | held | 6 |
| Earnings dates and fundamentals to EDGAR | extend `edgar_xbrl` | none | 4 |
| Cross-source checks, the parallel run, the supersession, the Weekly's line | config and the quality check | — | 5 |
| The calibration scripts' pulls | four scripts | — | 3 |
| **Total** | | **at most about USD 10 at IBKR plus Massive's Stocks plan, beside the USD 12.50 already held** | **46** |

**The order of work:**
1. the IBKR daily writer, because it carries the most keys;
2. the Cboe files and the FRED moves, cheapest and immediate;
3. the chains to Massive, since the dealer engine is the largest single dependency;
4. crypto;
5. intraday and overnight;
6. EDGAR;
7. the members;
8. the checks.

**The earliest honest retirement date: Tuesday 22 December 2026.** It assumes four things:
- Doctrine #2 rules on 7–8 Nov;
- the 46 hours are built across the weeks of 9 and 16 Nov, two sessions a night, merging after each tranche inside the windows;
- the first families run in parallel from Monday 23 Nov;
- the parallel run is 20 sessions: 23, 24, 25 and 27 Nov (the market closes on the 26th); 30 Nov to 4 Dec; 7 to 11 Dec; 14 to 18 Dec; and 21 Dec.

The pull retires after the close of the 21st. Any family whose probe fails, or that runs outside tolerance, moves its own date and holds the pull open for that family alone.

---

## 6. Rights and boundaries

- **No figure changes its meaning without a labelled break.** New keys, superseded old keys, the break's date printed wherever a reader joins the two; never a restatement.
- **No vendor value enters a flag, tell, dial or decision,** as today. The IBKR and Massive rows are vendor values, so every flag that reads a price reads the registry's primary for that key, under the tier rule: "Where it overlaps a higher tier on the same fact, it loses". No flag's definition changes in this migration.
- **The Brookfield blocklist** is applied at each new writer as at the old: through the Security Master's `restricted` and the register's instruments, at signal time and at write.
- **Own use only.** IBKR's and Massive's rows are not redistributable, Coinbase's are research only and never a mark, and the public repository never carries a stored value.
- **Nothing here touches the box, the live port, an order path or a register.**

---

## 7. DECISIONS FOR ARI

**1. The primary replacement for US funds and single names.** Options: (a) IBKR historical daily bars through the gateway; (b) Massive's Stocks plan; (c) both, IBKR primary and Massive the cross-check. **Recommend (a), with Massive only for the S&P members and corporate actions.** The account and gateway already exist, the subscriptions are a few dollars, and a broker's own data is what the decisions price against. Massive's grouped endpoint solves the one job IBKR's pacing cannot, the 500 members.

**2. The subscriptions to buy, and their ceiling.** Options: (a) IBKR's US Securities Snapshot and Futures Value Bundle (USD 10, waived at USD 30 commissions), plus Massive's lowest Stocks plan that serves grouped daily bars and reference data, under a ceiling of **USD 60 a month** for all market data; (b) IBKR only, with the members and actions as listed gaps; (c) none: delayed data and the public sources only. **Recommend (a).** The ceiling covers what is held (USD 12.50), the bundle and one Stocks plan, and it is stated so no later subscription arrives without a ruling.

**3. Index levels.** Options: (a) Cboe's public files for the VIX family, VVIX and SKEW; IBKR's held Cboe indexes subscription for ^GSPC; ^MOVE a listed gap; (b) IBKR for all. **Recommend (a).** Cboe's files are public and already read by a live writer. Only SPX needs the subscription, and ICE's MOVE has no source this brief found.

**4. The yield proxies.** Options: (a) FRED's DGS10 and DGS30 replace ^TNX and ^TYX, under a labelled break; (b) IBKR's TNX index. **Recommend (a).** The H.15 constant-maturity yield is public domain, already pulled, and the series the rates papers mean. The intraday reads that need a live yield keep `bars.y10` through the intraday writer.

**5. The dollar index.** Options: (a) DTWEXBGS as a labelled series change, never spliced; (b) ICE's DXY through IBKR's ICE futures feed. **Recommend (a).** It is the Fed's own index, public domain. The six-currency DXY is a convention the papers cite, but no check found a public source for it.

**6. Crypto.** Options: (a) OKX's daily candles, primary for marks; Coinbase as a research cross-check only, never a mark (its terms bar valuations); (b) Coinbase primary. **Recommend (a).** OKX is already a registered live source, and Coinbase's "no valuations" clause rules it out of the lab's carry book.

**7. The notes' bars.** Options: (a) move to IBKR intraday bars; (b) drop the notes' bars and print the notes from the daily rows only. **Recommend (a).** The notes are live from 26 Oct, and their first-hour readings and ledgers (SN-1, SN-2) are pre-registered on 5-minute bars. Dropping them would end two ledgers at n near zero.

**8. The parallel-run length.** Options: (a) 20 sessions; (b) 10; (c) 40. **Recommend (a).** Twenty is the scorecards' own minimum for a session-level figure in this system ("insufficient sessions" below 20). It covers a month-end and an options expiry, and it still allows a retirement before the year's end.

**9. The retirement deadline.** Options: (a) a ruled deadline of **Friday 8 January 2027**, with 22 Dec 2026 the earliest; (b) 22 Dec as the deadline; (c) no deadline, family by family. **Recommend (a).** The deadline leaves two weeks for one family that slips. It falls before the first Quarterly on 9 Jan, so that edition prints from licensed sources. (b) has no slack over the holidays.

**10. The keys no replacement covers.** Options: (a) declare them listed gaps now, printing "not tracked: <reason>" from the retirement date: ^MOVE, the foreign cash indices (^N225, ^STOXX50E, ^FTSE), the SET index, consensus estimates, the earnings calendar's forward dates, and any crypto name OKX does not list; (b) buy the exchanges' feeds. **Recommend (a).** None of them is a decision input. The overnight block keeps ES, NQ and BTC, which carry its attribution, and a gap stated is better than a feed bought for a footnote.

---

## Notes

**What could not be checked from here:**
- whether IBKR's historical daily bars for US stocks need the bundle or are served on the free non-consolidated feed;
- the depth IBKR serves for each family, and its volume unit;
- whether IBKR serves ^MOVE, TRY and IDR on the paper account.

All three are a probe on the box, which is the operator's: a session does not touch the box.

**The operator's facts to confirm:**
- the four IBKR subscriptions the registry lists as held (USD 12.50 in all);
- whether the account's commissions waive the bundle;
- Massive's Stocks plan price on its own page;
- whether the Currencies Basic and Futures Basic tiers named in the order are held. Nothing in the repository records them.

**yfinance keys not mapped one for one:**
- ^MOVE, ^N225, ^STOXX50E, ^FTSE, ^SET.BK, consensus, and the earnings calendar's forward dates are listed gaps, as decision 10 proposes;
- DX-Y.NYB, CL=F's spot substitute and ^TNX/^TYX change series under labelled breaks, as section 3 states.

**The registry understates the exposure in one place.** `sp500.member_close` is registered under source `sp500_members`, but its values come from `yf.download()` (the module's own docstring). The inventory script counts it separately for that reason.

**Sources read for this brief:**
- [IBKR market data pricing](https://www.interactivebrokers.com/en/pricing/market-data-pricing.php)
- [TWS API historical limitations](https://interactivebrokers.github.io/tws-api/historical_limitations.html)
- [TWS API delayed data](https://interactivebrokers.github.io/tws-api/delayed_data.html)
- [Massive terms](https://massive.com/legal/terms)
- [Massive pricing](https://massive.com/pricing)
- [FRED legal FAQ](https://fred.stlouisfed.org/legal/)
- the FRED series pages for [SP500](https://fred.stlouisfed.org/series/SP500), [DJIA](https://fred.stlouisfed.org/series/DJIA), [NASDAQCOM](https://fred.stlouisfed.org/series/NASDAQCOM), [VIXCLS](https://fred.stlouisfed.org/series/VIXCLS), [DTWEXBGS](https://fred.stlouisfed.org/series/DTWEXBGS) and [DCOILWTICO](https://fred.stlouisfed.org/series/DCOILWTICO)
- [Coinbase Market Data Terms](https://www.coinbase.com/legal/market_data)
- [Alpha Vantage terms](https://www.alphavantage.co/terms_of_service/)

**CI.** Read once after the push; recorded below.

---

## Appendix: the readers, by group and role (the inventory's file lists)


**Price basket: US equity index funds**
- writers (1): `altdata/sources/yfinance_source.py`
- ledgers (1): `tools/calibration/st_r6_71d_air_pockets.py`
- lab (3): `alpha/pit.py`, `alpha/research/roster-2026-10-17-x3.yaml`, `alpha/store.py`
- reports (6): `daily_cascade/open_note.py`, `daily_cascade/precis.py`, `daily_cascade/scorecard_backfill.py`, `daily_cascade/signal_lines.py`, `daily_cascade/volatile_day.py`, `register/heat.py`
- gates (35): `tools/validate_a43_render.py`, `tools/validate_a48_batch11.py`, `tools/validate_alpha.py`, `tools/validate_alpha_lab_3.py`, `tools/validate_alpha_proposer.py`, `tools/validate_aq3_series.py`, `tools/validate_audit_1.py`, `tools/validate_audit_3a.py`, `tools/validate_audit_fixes.py`, `tools/validate_b45_chain3.py`, `tools/validate_batch14_a2.py`, `tools/validate_batch14_b1.py`, `tools/validate_correlation_layer.py`, `tools/validate_daily_close.py`, `tools/validate_enforce.py`, `tools/validate_gtm.py`, `tools/validate_horizon_charts.py`, `tools/validate_lenses.py`, `tools/validate_monthly_stack.py`, `tools/validate_move_screen.py`, `tools/validate_outliers.py`, `tools/validate_packets.py`, `tools/validate_prices.py`, `tools/validate_quality.py`, `tools/validate_quarterly_stack.py` ...
- computations (9): `altdata/batch5.py`, `altdata/benchmark.py`, `altdata/book_b_scanner.py`, `altdata/capex_chain.py`, `altdata/dealer_scorecard.py`, `altdata/market_features.py`, `altdata/state_vector.py`, `altdata/volume_profile.py`, `regime.py`
- config (15): `config/alpha_events.yaml`, `config/batch5_tranche_1.yaml`, `config/book_b_scanner.yaml`, `config/capex_chain.yaml`, `config/correlation.yaml`, `config/display_labels.yaml`, `config/fragility.yaml`, `config/gtm.yaml`, `config/horizon_charts.yaml`, `config/market_state.yaml`, `config/monthly_themes.yaml`, `config/narratives.yaml`, `config/quarterly_chapters.yaml`, `config/reporting_stack.yaml`, `config/security_master.yaml`
- other tools (2): `tools/base_rates.py`, `tools/freshness.py`
- other (3): `metrics_registry.yaml`, `tests/fixtures/alpha/fixture_engine.py`, `tests/fixtures/alpha/fixture_store.py`

**Price basket: Sector funds**
- writers (2): `altdata/loggers/consensus.py`, `altdata/sources/yfinance_source.py`
- reports (2): `daily_cascade/weekly_sections.py`, `daily_cascade/weekly_stack.py`
- gates (10): `tools/validate_aq3_series.py`, `tools/validate_audit_3a.py`, `tools/validate_batch12.py`, `tools/validate_batch14_a2.py`, `tools/validate_book_b_scanner.py`, `tools/validate_gtm.py`, `tools/validate_horizon_charts.py`, `tools/validate_lenses.py`, `tools/validate_prices.py`, `tools/validate_quarterly_stack.py`
- computations (1): `altdata/market_features.py`
- config (7): `config/bank_stress.yaml`, `config/capex_chain.yaml`, `config/correlation.yaml`, `config/horizon_charts.yaml`, `config/quarterly_chapters.yaml`, `config/reporting_stack.yaml`, `config/security_master.yaml`
- other tools (1): `tools/base_rates.py`
- other (1): `metrics_registry.yaml`

**Price basket: Style funds**
- writers (1): `altdata/sources/yfinance_source.py`
- reports (1): `daily_cascade/signal_lines.py`
- gates (1): `tools/validate_st_t3_calib.py`
- config (1): `config/security_master.yaml`

**Price basket: Rates and credit funds**
- writers (1): `altdata/sources/yfinance_source.py`
- gates (12): `tools/validate_alpha.py`, `tools/validate_alpha_lab_4.py`, `tools/validate_audit_3a.py`, `tools/validate_benchmark.py`, `tools/validate_correlation_layer.py`, `tools/validate_gtm.py`, `tools/validate_horizon_charts.py`, `tools/validate_monthly_stack.py`, `tools/validate_quarterly_stack.py`, `tools/validate_regime.py`, `tools/validate_st_r4_t1.py`, `tools/validate_st_r4_t1b.py`
- computations (4): `altdata/batch5.py`, `altdata/batch5b.py`, `altdata/benchmark.py`, `altdata/market_features.py`
- config (9): `config/batch5_tranche_1.yaml`, `config/batch5_tranche_1b.yaml`, `config/correlation.yaml`, `config/gtm.yaml`, `config/horizon_charts.yaml`, `config/narratives.yaml`, `config/quarterly_chapters.yaml`, `config/reporting_stack.yaml`, `config/security_master.yaml`
- other tools (1): `tools/base_rates.py`
- other (1): `metrics_registry.yaml`

**Price basket: Commodity and real-asset funds**
- writers (1): `altdata/sources/yfinance_source.py`
- reports (1): `monthly_macro/payload.py`
- gates (11): `tools/validate_alpha_lab_4.py`, `tools/validate_aq3_series.py`, `tools/validate_attribution.py`, `tools/validate_horizon_charts.py`, `tools/validate_lenses.py`, `tools/validate_monthly_frames.py`, `tools/validate_monthly_stack.py`, `tools/validate_quarterly_gates.py`, `tools/validate_quarterly_stack.py`, `tools/validate_st_t1_rest.py`, `tools/validate_thesis_register.py`
- computations (2): `altdata/absorption.py`, `altdata/market_features.py`
- config (9): `config/alt_asset_theses/TEMPLATE.yaml`, `config/attribution.yaml`, `config/correlation.yaml`, `config/display_labels.yaml`, `config/horizon_charts.yaml`, `config/monthly_themes.yaml`, `config/quarterly_chapters.yaml`, `config/reporting_stack.yaml`, `config/security_master.yaml`

**Price basket: International and EM funds**
- writers (1): `altdata/sources/yfinance_source.py`
- gates (8): `tools/validate_aq3_series.py`, `tools/validate_batch15_1.py`, `tools/validate_correlation_layer.py`, `tools/validate_horizon_charts.py`, `tools/validate_monthly_stack.py`, `tools/validate_move_screen.py`, `tools/validate_quarterly_stack.py`, `tools/validate_weekly_fixes_9.py`
- computations (1): `altdata/market_features.py`
- config (8): `config/correlation.yaml`, `config/dm_drawdown.yaml`, `config/horizon_charts.yaml`, `config/move_screen.yaml`, `config/pillars.yaml`, `config/quarterly_chapters.yaml`, `config/reporting_stack.yaml`, `config/security_master.yaml`

**Price basket: Thematic and replication funds**
- writers (1): `altdata/sources/yfinance_source.py`
- gates (4): `tools/validate_audit_3a.py`, `tools/validate_batch14_a2.py`, `tools/validate_batch14_b1.py`, `tools/validate_batch15_2.py`
- config (5): `config/ai_trade.yaml`, `config/capex_chain.yaml`, `config/hf_positioning.yaml`, `config/reporting_stack.yaml`, `config/security_master.yaml`
- other (1): `metrics_registry.yaml`

**Price basket: Single names**
- writers (2): `altdata/loggers/vxcurve.py`, `altdata/sources/yfinance_source.py`
- ledgers (5): `altdata/ledgers/st_r4_17b.py`, `altdata/ledgers/st_r4_19b.py`, `altdata/ledgers/st_r5_32b.py`, `altdata/ledgers/st_r5_44b.py`, `tools/calibration/st_r6_74b_short_extremes.py`
- lab (1): `alpha/research/roster-2026-10-17-x3.yaml`
- reports (4): `daily_cascade/dealer_block.py`, `daily_cascade/weekly_sections.py`, `daily_cascade/weekly_stack.py`, `monthly_macro/dealer.py`
- gates (36): `tools/validate_a48_batch11.py`, `tools/validate_a50_dealer_store.py`, `tools/validate_ai_fcf.py`, `tools/validate_alpha_lab_3.py`, `tools/validate_aq3_series.py`, `tools/validate_audit_3a.py`, `tools/validate_b45_chain3.py`, `tools/validate_batch14_a2.py`, `tools/validate_batch14_b1.py`, `tools/validate_batch15_1.py`, `tools/validate_book_b_scanner.py`, `tools/validate_config_refs.py`, `tools/validate_daily_close.py`, `tools/validate_dealer_block.py`, `tools/validate_derived.py`, `tools/validate_figure_budget.py`, `tools/validate_gtm.py`, `tools/validate_horizon_charts.py`, `tools/validate_lenses.py`, `tools/validate_monthly.py`, `tools/validate_monthly_stack.py`, `tools/validate_move_screen.py`, `tools/validate_narratives.py`, `tools/validate_opening_setup.py`, `tools/validate_outliers.py` ...
- computations (11): `altdata/batch5b.py`, `altdata/derived.py`, `altdata/gtm.py`, `altdata/market_features.py`, `altdata/quality.py`, `altdata/return_attribution.py`, `altdata/st_r5_index.py`, `altdata/st_r5_t1_rest.py`, `altdata/state_vector.py`, `altdata/transmission.py`, `regime.py`
- config (24): `config/ai_fcf.yaml`, `config/alpha_events.yaml`, `config/batch5_tranche_1b.yaml`, `config/capex_chain.yaml`, `config/correlation.yaml`, `config/data_quality.yaml`, `config/display_labels.yaml`, `config/dm_drawdown.yaml`, `config/fragility.yaml`, `config/gtm.yaml`, `config/horizon_charts.yaml`, `config/market_state.yaml`, `config/monthly_themes.yaml`, `config/move_screen.yaml`, `config/narratives.yaml`, `config/pillars.yaml`, `config/quarterly_chapters.yaml`, `config/reporting_stack.yaml`, `config/security_master.yaml`, `config/st_r5_index.yaml`, `config/st_r5_t1_rest.yaml`, `config/story_queries.yaml`, `config/transmission.yaml`, `config/vol_event.yaml`
- other tools (3): `tools/assign_families.py`, `tools/base_rates.py`, `tools/seed_security_master.py`
- other (1): `metrics_registry.yaml`

**Price basket: Index levels (Cboe, S&P, ICE)**
- writers (2): `altdata/loggers/vxcurve.py`, `altdata/sources/yfinance_source.py`
- ledgers (5): `altdata/ledgers/st_r4_17b.py`, `altdata/ledgers/st_r4_19b.py`, `altdata/ledgers/st_r5_32b.py`, `altdata/ledgers/st_r5_44b.py`, `tools/calibration/st_r6_74b_short_extremes.py`
- lab (1): `alpha/research/roster-2026-10-17-x3.yaml`
- reports (4): `daily_cascade/dealer_block.py`, `daily_cascade/weekly_sections.py`, `daily_cascade/weekly_stack.py`, `monthly_macro/dealer.py`
- gates (30): `tools/validate_ai_fcf.py`, `tools/validate_alpha_lab_3.py`, `tools/validate_audit_3a.py`, `tools/validate_basis_proxy.py`, `tools/validate_batch14_a2.py`, `tools/validate_batch14_b1.py`, `tools/validate_batch15_1.py`, `tools/validate_config_refs.py`, `tools/validate_daily_close.py`, `tools/validate_dealer_block.py`, `tools/validate_derived.py`, `tools/validate_gtm.py`, `tools/validate_horizon_charts.py`, `tools/validate_lenses.py`, `tools/validate_monthly.py`, `tools/validate_monthly_stack.py`, `tools/validate_move_screen.py`, `tools/validate_narratives.py`, `tools/validate_outliers.py`, `tools/validate_prices.py`, `tools/validate_quality.py`, `tools/validate_quarterly_stack.py`, `tools/validate_regime.py`, `tools/validate_sr38_inbox.py`, `tools/validate_st_r4_t1b.py` ...
- computations (12): `altdata/basis_proxy.py`, `altdata/batch5b.py`, `altdata/derived.py`, `altdata/gtm.py`, `altdata/market_features.py`, `altdata/quality.py`, `altdata/return_attribution.py`, `altdata/st_r5_index.py`, `altdata/st_r5_t1_rest.py`, `altdata/state_vector.py`, `altdata/transmission.py`, `regime.py`
- config (25): `config/ai_fcf.yaml`, `config/alpha_events.yaml`, `config/basis_proxy.yaml`, `config/batch5_tranche_1b.yaml`, `config/correlation.yaml`, `config/data_quality.yaml`, `config/display_labels.yaml`, `config/dm_drawdown.yaml`, `config/fragility.yaml`, `config/gold_event.yaml`, `config/gtm.yaml`, `config/horizon_charts.yaml`, `config/market_state.yaml`, `config/monthly_themes.yaml`, `config/move_screen.yaml`, `config/narratives.yaml`, `config/pillars.yaml`, `config/quarterly_chapters.yaml`, `config/reporting_stack.yaml`, `config/security_master.yaml`, `config/st_r5_index.yaml`, `config/st_r5_t1_rest.yaml`, `config/story_queries.yaml`, `config/transmission.yaml`, `config/vol_event.yaml`
- other tools (2): `tools/assign_families.py`, `tools/base_rates.py`
- other (1): `metrics_registry.yaml`

**Price basket: Yield proxies**
- writers (1): `altdata/sources/yfinance_source.py`
- reports (1): `daily_cascade/consistency.py`
- gates (8): `tools/validate_audit_3a.py`, `tools/validate_audit_fixes.py`, `tools/validate_derived.py`, `tools/validate_lenses.py`, `tools/validate_outliers.py`, `tools/validate_quality.py`, `tools/validate_weekly_fixes_8.py`, `tools/validate_weekly_fixes_9.py`
- computations (2): `altdata/move_screen.py`, `altdata/rates_shape.py`
- config (4): `config/batch3_tranche_a.yaml`, `config/data_quality.yaml`, `config/reporting_stack.yaml`, `config/security_master.yaml`
- other tools (1): `tools/assign_families.py`
- other (1): `metrics_registry.yaml`

**Price basket: Futures fronts (gold, oil, copper, products, the 10-year note)**
- writers (2): `altdata/sources/lbma.py`, `altdata/sources/yfinance_source.py`
- reports (2): `daily_cascade/weekly_sections.py`, `daily_cascade/weekly_stack.py`
- gates (11): `tools/validate_aq3_series.py`, `tools/validate_attribution.py`, `tools/validate_audit_3a.py`, `tools/validate_batch15_1.py`, `tools/validate_figure_budget.py`, `tools/validate_monthly_stack.py`, `tools/validate_quarterly_gates.py`, `tools/validate_quarterly_stack.py`, `tools/validate_st_r4_t1b.py`, `tools/validate_st_r5_t1_rest.py`, `tools/validate_weekly_complete.py`
- computations (4): `altdata/batch5b.py`, `altdata/feeds.py`, `altdata/market_features.py`, `altdata/st_r5_t1_rest.py`
- config (12): `config/attribution.yaml`, `config/batch5_tranche_1b.yaml`, `config/correlation.yaml`, `config/display_labels.yaml`, `config/gold_event.yaml`, `config/horizon_charts.yaml`, `config/market_state.yaml`, `config/monthly_themes.yaml`, `config/quarterly_chapters.yaml`, `config/reporting_stack.yaml`, `config/security_master.yaml`, `config/st_r5_t1_rest.yaml`
- other (2): `metrics_registry.yaml`, `source_registry.yaml`

**Price basket: FX rates**
- writers (1): `altdata/sources/yfinance_source.py`
- reports (5): `daily_cascade/evening_note.py`, `daily_cascade/funding_hooks.py`, `daily_cascade/signal_lines.py`, `daily_cascade/weekly_sections.py`, `daily_cascade/weekly_stack.py`
- gates (15): `tools/validate_6e_rest.py`, `tools/validate_a43_render.py`, `tools/validate_aq3_series.py`, `tools/validate_batch15_1.py`, `tools/validate_batch3_a.py`, `tools/validate_figure_budget.py`, `tools/validate_horizon_charts.py`, `tools/validate_monthly_stack.py`, `tools/validate_move_screen.py`, `tools/validate_official_sources.py`, `tools/validate_prices.py`, `tools/validate_quarterly_stack.py`, `tools/validate_st_t2_rates.py`, `tools/validate_weekly_complete.py`, `tools/validate_weekly_fixes_9.py`
- computations (3): `altdata/batch3.py`, `altdata/funding_currency.py`, `altdata/market_features.py`
- config (8): `config/correlation.yaml`, `config/dm_drawdown.yaml`, `config/horizon_charts.yaml`, `config/macro_6e.yaml`, `config/move_screen.yaml`, `config/quarterly_chapters.yaml`, `config/reporting_stack.yaml`, `config/security_master.yaml`
- other tools (1): `tools/seed_security_master.py`
- other (1): `metrics_registry.yaml`

**Price basket: Crypto in the basket**
- writers (4): `altdata/loggers/shielded.py`, `altdata/sources/crypto_derived.py`, `altdata/sources/treasury.py`, `altdata/sources/yfinance_source.py`
- lab (1): `alpha/research/roster-2026-10-17-x3.yaml`
- reports (2): `daily_cascade/digital_addendum.py`, `monthly_macro/payload.py`
- gates (9): `tools/validate_alpha_lab_3.py`, `tools/validate_b45_chain3.py`, `tools/validate_crypto_basket.py`, `tools/validate_crypto_sources.py`, `tools/validate_digital_addendum.py`, `tools/validate_horizon_charts.py`, `tools/validate_lenses.py`, `tools/validate_prices.py`, `tools/validate_quarterly_stack.py`
- config (11): `config/alpha_crypto_venues.yaml`, `config/correlation.yaml`, `config/crypto_sources.yaml`, `config/digital_addendum.yaml`, `config/display_labels.yaml`, `config/horizon_charts.yaml`, `config/monthly_themes.yaml`, `config/quarterly_chapters.yaml`, `config/reporting_stack.yaml`, `config/security_master.yaml`, `config/story_queries.yaml`
- other (1): `metrics_registry.yaml`

**Crypto basket (config/crypto_basket.yaml)**
- writers (1): `altdata/sources/yfinance_source.py`
- reports (1): `monthly_macro/prl_part.py`
- gates (7): `tools/validate_b45_chain3.py`, `tools/validate_crypto_basket.py`, `tools/validate_crypto_sources.py`, `tools/validate_prices.py`, `tools/validate_security_master.py`, `tools/validate_st_t5_prl.py`, `tools/validate_st_t5_render.py`
- computations (1): `altdata/crypto_basket.py`
- config (2): `config/prl.yaml`, `config/security_master.yaml`
- other tools (1): `tools/seed_security_master.py`
- other (1): `metrics_registry.yaml`

**OHLC companions (_open/_high/_low)**
- writers (1): `altdata/sources/yfinance_source.py`
- gates (4): `tools/validate_alpha_lab_3.py`, `tools/validate_audit_3a.py`, `tools/validate_b45_chain3.py`, `tools/validate_st_r4_t1b.py`
- config (1): `config/batch5_tranche_1b.yaml`
- other tools (1): `tools/base_rates.py`
- other (1): `metrics_registry.yaml`

**Volume (_volume)**
- writers (6): `altdata/bars.py`, `altdata/loggers/borrow.py`, `altdata/sources/gt.py`, `altdata/sources/llama.py`, `altdata/sources/yfinance_source.py`, `tools/backfill_prices.py`
- ledgers (1): `tools/calibration/os12c_relative_volume.py`
- lab (2): `alpha/rules.py`, `alpha/store.py`
- reports (8): `daily_cascade/dealer_weekly.py`, `daily_cascade/opening_setup.py`, `daily_cascade/relative_volume.py`, `daily_cascade/scorecard_backfill.py`, `daily_cascade/stack.py`, `daily_cascade/stack_close.py`, `daily_cascade/weekly_stack.py`, `monthly_macro/prl_part.py`
- gates (19): `tools/validate_a48_batch11.py`, `tools/validate_alpha.py`, `tools/validate_audit_1.py`, `tools/validate_audit_3a.py`, `tools/validate_b45_chain3.py`, `tools/validate_batch13.py`, `tools/validate_batch14_b1.py`, `tools/validate_book_b_scanner.py`, `tools/validate_crypto_basket.py`, `tools/validate_crypto_sources.py`, `tools/validate_imf_ifs.py`, `tools/validate_opening_setup.py`, `tools/validate_prices.py`, `tools/validate_st_r4_t1b.py`, `tools/validate_st_t5_prl.py`, `tools/validate_st_t5_render.py`, `tools/validate_volume_profile.py`, `tools/validate_weekly_edits.py`, `tools/validate_weekly_fixes_9.py`
- computations (8): `altdata/book_b_scanner.py`, `altdata/chain_metrics.py`, `altdata/crypto_basket.py`, `altdata/flatfile_history.py`, `altdata/labels.py`, `altdata/prediction_markets.py`, `altdata/prl.py`, `altdata/volume_profile.py`
- config (8): `config/alt_asset_gaps.yaml`, `config/book_b_scanner.yaml`, `config/display_labels.yaml`, `config/fragility.yaml`, `config/market_state.yaml`, `config/opening_setup.yaml`, `config/prediction_markets.yaml`, `config/prl.yaml`
- other tools (3): `tools/assign_families.py`, `tools/massive_flatfiles_backfill.py`, `tools/quality_gates.py`
- other (2): `metrics_registry.yaml`, `tests/fixtures/alpha/fixture_store.py`

**Dividends and splits (_dividend/_split)**
- writers (2): `altdata/sources/shiller.py`, `altdata/sources/yfinance_source.py`
- ledgers (4): `altdata/ledgers/st_r5_30b.py`, `tools/calibration/sr05_consumer_credit.py`, `tools/calibration/sr12_bond_alloc.py`, `tools/calibration/sr15_valuation.py`
- reports (6): `daily_cascade/absorption_block.py`, `daily_cascade/opening_setup.py`, `daily_cascade/stack_render.py`, `daily_cascade/style_block.py`, `monthly_macro/quarterly_items.py`, `monthly_macro/stack.py`
- gates (6): `tools/validate_a48_batch11.py`, `tools/validate_audit_3a.py`, `tools/validate_base_rates.py`, `tools/validate_benchmark.py`, `tools/validate_gtm.py`, `tools/validate_monthly_stack.py`
- computations (4): `altdata/attribution.py`, `altdata/benchmark.py`, `altdata/gtm.py`, `altdata/return_attribution.py`
- config (3): `config/attribution.yaml`, `config/book_b_scanner.yaml`, `config/move_screen.yaml`
- other tools (4): `tools/assign_families.py`, `tools/base_rates.py`, `tools/horizon_charts.py`, `tools/pin_log.py`
- other (1): `metrics_registry.yaml`

**The notes' 5-minute bars (note_bars_prices)**
- writers (1): `altdata/bars.py`
- gates (1): `tools/validate_secondary_notes.py`
- other (1): `metrics_registry.yaml`

**The tape set's bars (bars_prices and volume)**
- writers (1): `altdata/bars.py`
- gates (3): `tools/validate_a50_dealer_store.py`, `tools/validate_audit_3a.py`, `tools/validate_secondary_notes.py`
- other (1): `metrics_registry.yaml`

**Overnight levels and changes (the 07:00 anchor)**
- writers (3): `altdata/loggers/listings.py`, `altdata/sources/overnight.py`, `altdata/sources/voices_scan.py`
- reports (2): `daily_cascade/__init__.py`, `daily_cascade/morning_payload.py`
- gates (12): `tools/check_registry.py`, `tools/validate_audit_3a.py`, `tools/validate_feeds_scheduled.py`, `tools/validate_heartbeat_caller.sh`, `tools/validate_meme_ingest.py`, `tools/validate_morning_anchor.py`, `tools/validate_official_sources.py`, `tools/validate_outliers.py`, `tools/validate_security_master.py`, `tools/validate_voices.py`, `tools/validate_weekly_complete.py`, `tools/validate_weekly_edits.py`
- computations (4): `altdata/batch5b.py`, `altdata/derived.py`, `altdata/feeds.py`, `altdata/meme_ingest.py`
- config (3): `config/basis_proxy.yaml`, `config/display_labels.yaml`, `config/security_master.yaml`
- other tools (1): `tools/seed_security_master.py`
- other (4): `metrics_registry.yaml`, `scripts/deploy_remote.sh`, `scripts/fetch_overnight.sh`, `scripts/run_morning_anchor.sh`

**The pin log's columns (tools/pin_log.py)**
- reports (2): `daily_cascade/payload.py`, `daily_cascade/stack_close.py`
- gates (10): `smoke_test.py`, `tools/check_registry.py`, `tools/check_store_registry.py`, `tools/validate_attribution.py`, `tools/validate_audit_3a.py`, `tools/validate_backup.py`, `tools/validate_deploy.py`, `tools/validate_monthly.py`, `tools/validate_monthly_stack.py`, `tools/validate_register.py`
- computations (3): `altdata/config.py`, `altdata/grader.py`, `altdata/session.py`
- other tools (3): `tools/assign_families.py`, `tools/decide.py`, `tools/pin_log.py`
- other (3): `metrics_registry.yaml`, `run_eod.py`, `source_registry.yaml`

**S&P 500 members' closes (registry source sp500_members; values from Yahoo)**
- writers (1): `altdata/sources/sp500_members.py`
- ledgers (2): `altdata/ledgers/st_r5_31b.py`, `altdata/ledgers/st_r5_44b.py`
- gates (3): `tools/validate_gtm.py`, `tools/validate_st_r4_t1b.py`, `tools/validate_st_r5_t1_rest.py`
- computations (2): `altdata/numeral_audit.py`, `altdata/st_r5_t1_rest.py`
- config (3): `config/batch5_tranche_1b.yaml`, `config/gtm.yaml`, `config/st_r5_t1_rest.yaml`
- other (1): `metrics_registry.yaml`

**Registry entries, source yfinance**
- writers (4): `altdata/fed_funds.py`, `altdata/loggers/consensus.py`, `altdata/loggers/shielded.py`, `altdata/sources/overnight.py`
- lab (3): `alpha/engines/vrp.py`, `alpha/research/roster-2026-10-14.yaml`, `alpha_proposer/packet.py`
- reports (2): `daily_cascade/absorption_block.py`, `monthly_macro/payload.py`
- gates (18): `tools/check_store_registry.py`, `tools/validate_a50_dealer_store.py`, `tools/validate_ai_fcf.py`, `tools/validate_alpha_lab_3.py`, `tools/validate_alpha_lab_4.py`, `tools/validate_audit_3a.py`, `tools/validate_b51_registry_html.py`, `tools/validate_crypto_basket.py`, `tools/validate_grader.py`, `tools/validate_gtm.py`, `tools/validate_lenses.py`, `tools/validate_morning_anchor.py`, `tools/validate_quarterly_stack.py`, `tools/validate_register.py`, `tools/validate_releases_b.py`, `tools/validate_st_r5_rates.py`, `tools/validate_st_t1_rest.py`, `tools/validate_weekly_complete.py`
- computations (7): `altdata/absorption.py`, `altdata/dealer_store.py`, `altdata/pe_dispersion.py`, `altdata/return_attribution.py`, `altdata/st_r5_rates.py`, `altdata/surprise.py`, `altdata/surprise_index.py`
- config (9): `config/ai_fcf.yaml`, `config/alpha_events.yaml`, `config/alpha_search.yaml`, `config/correlation.yaml`, `config/display_labels.yaml`, `config/gtm.yaml`, `config/market_state.yaml`, `config/quarterly_chapters.yaml`, `config/st_r5_rates.yaml`
- other (2): `metrics_registry.yaml`, `tests/fixtures/alpha/fixture_store.py`

**Registry entries, source yfinance_fundamentals**
- config (1): `config/narratives.yaml`
- other (1): `metrics_registry.yaml`

**Registry entries, source yahoo_cnh**
- writers (1): `altdata/sources/cnh.py`
- reports (1): `daily_cascade/absorption_block.py`
- gates (2): `tools/validate_aq3_series.py`, `tools/validate_st_t2_rates.py`
- computations (2): `altdata/funding_currency.py`, `altdata/market_features.py`
- config (2): `config/quarterly_chapters.yaml`, `config/security_master.yaml`
- other tools (1): `tools/seed_security_master.py`
- other (1): `metrics_registry.yaml`

**Registry entries, source yahoo_set**
- writers (1): `altdata/sources/thai_set.py`
- gates (1): `tools/validate_aq3_series.py`
- other (1): `metrics_registry.yaml`


**CI.** At the one read after the push of `3a11e8c`, no run was listed yet, so there is no run id. The next paste that touches this branch (B69 branches from it) reads it once.
