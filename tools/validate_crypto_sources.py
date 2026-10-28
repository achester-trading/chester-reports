#!/usr/bin/env python3
"""
Validation gate for Batch 4 Tranche A, part 1 (crypto-tranche-a-1, 17 Oct 2026):
CD-1's watch names, CD-2's perp venues, CD-5's network state and the fear-and-greed
index, and the S-1 and S-3 derived series. config/crypto_sources.yaml.

    python tools/validate_crypto_sources.py

Every parser runs on a STORED FIXTURE OF THE REAL RESPONSE (tests/fixtures/hl, fut,
mempool, fng, eth, llama; captured 17 Oct 2026 -- Bybit's are its documented shape,
the venue being geo-blocked from the US and switched off). No socket is opened, no
live store read, no model called.

  A PARSERS     one per endpoint, each against figures computed here from the
                fixture by hand
  B DERIVED     S-1's share by chain and S-3 (OI-weighted funding, total OI,
                OI over market cap, the 90-day z) against hand computations on a
                seeded store; the two-venue rule; the all-venues total
  C WEIGHT      Hyperliquid's documented limits in config; the guard charges
                before sending, waits on a fake clock, and REFUSES a burst
  D ISOLATION   a venue that fails does not stop the others; a writer whose
                every series fails is STALE and writes nothing
  E BACKFILL    bounded (start date, page cap) and point in time (available_at
                the pull instant, never backdated)
  F ONCE        no series is stored twice with the crypto basket
  G WIRING      every key registered with family, long_window and a unit in the
                vocabulary; on the external roster and the daily crypto run; the
                catalogue; the gaps named; no key read
  H WATCH       the watch names' slugs resolved at run time from /protocols and
                /overview/fees, never written down; an ambiguous name is refused
  O CD-12       bitcoin-data.com with the operator's free key (ruling 2 of 19 Oct
                2026): a fixture response parses; with no key nothing is fetched;
                the guard refuses a 9th request in an hour and a 16th in a day;
                the terms quoted; no gate fetches
"""

from __future__ import annotations

import datetime as dt
import json
import math
import os
import socket
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
TD = Path(gate_mkdtemp("crypto_sources_"))
FX = REPO / "tests" / "fixtures"
TODAY = "2026-10-17"
NOW = "2026-10-17T20:10:00.000000+00:00"
_SOCKETS: list = []


def _no_connect(*a, **k):
    _SOCKETS.append(a[1:2] or a)
    raise OSError("validate_crypto_sources: no network in a code gate")


# A CONNECTION is the failure, not a socket: urllib3 opens one at import to probe
# for IPv6 and connects nowhere.
socket.socket.connect = _no_connect                             # type: ignore[method-assign]
socket.socket.connect_ex = _no_connect                          # type: ignore[method-assign]
socket.create_connection = _no_connect                          # type: ignore[assignment]


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def L(rel: str):
    return json.loads((FX / rel).read_text(encoding="utf-8"))


def near(a, b, tol=1e-9) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol * max(1.0, abs(b))


def day_of(ms) -> str:
    v = float(ms)
    v = v / 1000 if v > 1e11 else v
    return dt.datetime.fromtimestamp(v, dt.timezone.utc).date().isoformat()


def store(path: str):
    from altdata import observations
    return observations.ObservationStore(path)


# CD-12's key is never this gate's: an empty value is "absent" to altdata.secrets,
# and the environment always wins over .env, so the laptop's .env cannot change
# the verdict. The rate guard's state file lives in this gate's temp directory.
os.environ["BITCOIN_DATA_API_KEY"] = ""
os.environ["CHESTER_STATE_DIR"] = str(TD / "state")

# bitcoin-data.com's response shape: rows carrying their day ("d") and a unix time
# (the API's description; source_registry.yaml `bitcoin_data`), plus the one value
# field. Synthetic figures.
BD_LTH = [{"d": "2026-10-14", "unixTs": "1760400000", "lthSupply": 14_800_000.0},
          {"d": "2026-10-15", "unixTs": "1760486400", "lthSupply": 14_810_000.0},
          {"d": "2026-10-16", "unixTs": "1760572800", "lthSupply": 14_820_000.0}]
BD_STH = {"content": [{"d": "2026-10-15", "unixTs": "1760486400", "sthSupply": 5_130_000.0},
                      {"d": "2026-10-16", "unixTs": "1760572800", "sthSupply": 5_121_000.0}]}
BD_CUR = [{"d": "2026-10-15", "unixTs": "1760486400", "supplyCurrent": 19_940_000.0},
          {"d": "2026-10-16", "unixTs": "1760572800", "supplyCurrent": 19_941_000.0},
          {"d": "2026-10-18", "unixTs": "1760745600", "supplyCurrent": 19_943_000.0}]


def cd12() -> None:
    """CD-12 (ruling 2 of 19 Oct 2026): bitcoin-data.com with the operator's free
    key. A fixture response parses; with no key nothing is fetched; the guard
    refuses a 16th request in a day and a 9th in an hour; no gate fetches."""
    import yaml as _yaml                                        # noqa: PLC0415
    from altdata import secrets                                 # noqa: PLC0415
    from altdata.sources import btcdata as B                    # noqa: PLC0415
    head("O. CD-12, BITCOIN-DATA.COM (SR-29), WITH THE OPERATOR'S FREE KEY")
    real_http = B._http                                         # noqa: SLF001
    fetched: list = []

    def no_fetch(*a, **k):
        fetched.append(a)
        raise AssertionError("a gate never fetches")
    B._http = no_fetch                                          # noqa: SLF001
    try:
        check(B.parse(BD_LTH, "2026-10-17") == [("2026-10-14", 14_800_000.0),
                                               ("2026-10-15", 14_810_000.0),
                                               ("2026-10-16", 14_820_000.0)]
              and B.parse(BD_STH, "2026-10-17")[-1] == ("2026-10-16", 5_121_000.0)
              and B.parse(BD_CUR, "2026-10-17")[-1] == ("2026-10-16", 19_941_000.0),
              "a fixture response parses: the day from d, the one value field, a page "
              "object's content, nothing dated after today")
        try:
            B.parse([{"d": "2026-10-15", "lthSupply": 1.0, "other": 2.0}], "2026-10-17")
            refused = False
        except ValueError:
            refused = True
        check(refused, "a row with two value fields is refused, not guessed")

        st_path = TD / "state" / "btcdata_requests.json"
        clock = [1_000_000.0]
        g = B.RateGuard(st_path, per_hour=8, per_day=15, clock=lambda: clock[0])
        pages = {B.BASE + p: d for p, d in (("/v1/long-term-hodler-supply-btc", BD_LTH),
                                            ("/v1/short-term-hodler-supply-btc", BD_STH),
                                            ("/v1/supply-current", BD_CUR))}
        asked: list = []

        def fake(url, params):
            asked.append((url, dict(params)))
            return pages[url]
        rows, notes = B.collect(get=fake, guard=g, today="2026-10-17", now=NOW)
        share = {r["observed_at"]: r["value"] for r in rows
                 if r["registry_key"] == "btcdata.lth_supply_share"}
        want = {d: round(100 * lth / cur, 6) for d, lth, cur in
                (("2026-10-15", 14_810_000.0, 19_940_000.0),
                 ("2026-10-16", 14_820_000.0, 19_941_000.0))}
        check(share == want and not notes
              and all(r["available_at"] == NOW and r["availability_kind"] == "ingest_instant"
                      and r["source"] == "bitcoin_data" for r in rows),
              f"btcdata.lth_supply_share is the long-term-holder supply over the current "
              f"supply, on the days both are read ({share}); every row available at the "
              f"pull instant")
        check(len(asked) == 3 and all(a[1]["startday"] == "2022-10-17" and a[1]["size"] == 2000
                                      for a in asked),
              "the first run reads the free tier's four years in one page per series: "
              "3 requests")
        for _ in range(5):                                      # 8 in the hour now
            g.charge()
        try:
            g.charge()
            nine = False
        except B.RateExceeded:
            nine = True
        clock[0] += 3601
        for _ in range(7):                                      # 15 in the day
            g.charge()
        clock[0] += 3601
        try:
            g.charge()
            sixteen = False
        except B.RateExceeded as exc:
            sixteen = "would make 16 in a day" in str(exc)
        reread = B.RateGuard(st_path, per_hour=8, per_day=15, clock=lambda: clock[0])
        check(nine and sixteen and reread.counts()[1] == 15,
              "the rate guard refuses a 9th request in an hour and a 16th in a day, and "
              "a second run reads the first's count from the state file")
        clock[0] += 86401
        rows2, notes2 = B.collect(get=fake, guard=B.RateGuard(st_path, 8, 2,
                                                              clock=lambda: clock[0]),
                                  today="2026-10-17", now=NOW)
        check(len(notes2) == 1 and "waits for the next run" in notes2[0]
              and len(asked) == 5,
              "a request the guard refuses is not sent; that series waits for the next run")

        n0 = len(asked)
        out = B.pull(get=fake)
        check(out["status"] == "NOT_TRACKED" and out["written"] == 0 and len(asked) == n0
              and out["reason"] == "not tracked (btcdata.lth_supply_share): no key in .env "
                                   "(BITCOIN_DATA_API_KEY)"
              and not secrets.present("BITCOIN_DATA_API_KEY"),
              "with no key nothing is fetched, and the summary names the key")
        check(not fetched, "no gate fetches: the HTTP call was never reached")
    finally:
        B._http = real_http                                     # noqa: SLF001

    src = (REPO / "altdata" / "sources" / "btcdata.py").read_text(encoding="utf-8")
    check('"Authorization": f"Bearer {key}"' in src and "token=" not in src.replace(
        "?token=...", "") and "max_retries" not in src and "@" not in src.split('"""')[2],
          "the key goes in the Authorization header, never a URL; one attempt, no retry; "
          "no address in the User-Agent")
    _src = _yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))
    _reg = _yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    bd = (_src.get("sources") or _src).get("bitcoin_data") or {}
    M = _reg.get("metrics") or {}
    lic = str(bd.get("license"))
    check(bd.get("status") == "built" and bd.get("implemented_by") == "altdata/sources/btcdata.py"
          and all(q in lic for q in ("available with a free API key", "robots.txt",
                                     "no clause on storing", "must not be provided to third "
                                     "parties", "must be credited", "October 14, 2026")),
          "source_registry quotes the terms, re-read: the free key, robots, the storing "
          "clause (none), redistribution and credit")
    keys = ("btcdata.lth_supply", "btcdata.sth_supply", "btcdata.supply_current",
            "btcdata.lth_supply_share")
    check(all(M.get(k, {}).get("source") == "bitcoin_data" and M[k].get("family")
              and M[k].get("long_window") and M[k].get("units") for k in keys)
          and M["btcdata.lth_supply_share"]["units"] == "percent_share"
          and "tracked" not in M["btcdata.lth_supply_share"]
          and "manual_input" not in M["btcdata.lth_supply_share"],
          "the four keys are registered with family, long window and units; no by-hand line")
    wrap = (REPO / "scripts" / "run_crypto_basket.sh").read_text(encoding="utf-8")
    cat = _yaml.safe_load((REPO / "config" / "catalogue_commands.yaml").read_text(
        encoding="utf-8"))["commands"]
    from altdata import feeds                                   # noqa: PLC0415
    check("altdata.sources.btcdata" in wrap and "altdata.sources.btcdata" in cat
          and "btcdata" not in feeds.EXTERNAL_WRITERS,
          "it rides the crypto basket's daily run (no new timer, not a second roster "
          "pull that would spend the budget twice) and has its catalogue line")


def main() -> int:
    from altdata.sources import (_crypto as C, blockscout, crypto_derived as D, fng,
                                 fut, hl, llama, mempool)
    cfg = C.config()

    # --- A --------------------------------------------------------------------
    head("A. PARSERS, ON THE STORED RESPONSES")
    # Hyperliquid
    doc = L("hl/meta_and_asset_ctxs.json")
    ctx = hl.parse_ctxs(doc, ["BTC", "ETH"])
    uni = [u["name"] for u in doc[0]["universe"]]
    raw = doc[1][uni.index("BTC")]
    check(near(ctx["BTC"]["oi_usd"], float(raw["openInterest"]) * float(raw["markPx"]))
          and set(ctx) == {"BTC", "ETH"},
          f"hl metaAndAssetCtxs: BTC's OI in USD = openInterest x markPx "
          f"({ctx['BTC']['oi_usd']:,.0f}), aligned by index")
    fh = L("hl/funding_history_btc.json")
    by: dict = {}
    for r in fh:
        by.setdefault(day_of(r["time"]), []).append(float(r["fundingRate"]))
    want = {d: 100 * 365 * sum(v) for d, v in by.items() if d < TODAY and len(v) >= 24}
    got = dict(C.daily_funding(hl.parse_funding(fh), TODAY, expected=24))
    check(got.keys() == want.keys() and all(near(got[d], want[d]) for d in want)
          and len(want) >= 2,
          f"hl fundingHistory: the day's 24 hourly prints summed x 365 ({len(want)} "
          f"complete days; the partial first and current days not written)")
    # OKX
    oh = L("fut/okx_funding_history.json")["data"]
    byo: dict = {}
    for r in oh:
        byo.setdefault(day_of(r["fundingTime"]), []).append(float(r["realizedRate"]))
    wo = {d: 100 * 365 * sum(v) for d, v in byo.items() if d < TODAY and len(v) >= 3}
    go = dict(C.daily_funding(fut.okx_funding(L("fut/okx_funding_history.json")), TODAY))
    check(go.keys() == wo.keys() and all(near(go[d], wo[d]) for d in wo),
          f"okx funding-rate-history: three eight-hourly realizedRate prints a day, "
          f"summed x 365 ({len(wo)} days)")
    check(near(fut.okx_oi_now(L("fut/okx_open_interest.json")),
               float(L("fut/okx_open_interest.json")["data"][0]["oiUsd"])),
          "okx open-interest: oiUsd")
    hist = fut.okx_oi_history(L("fut/okx_oi_history.json"))
    check(len(hist) == len(L("fut/okx_oi_history.json")["data"])
          and near(hist[-1][1], float(L("fut/okx_oi_history.json")["data"][0][3])),
          "okx open-interest-history: [ts, oi, oiCcy, oiUsd] -> the USD column, oldest first")
    rat = fut.okx_ratio(L("fut/okx_ls_account.json"))
    check(rat[-1][1] == float(L("fut/okx_ls_account.json")["data"][0][1]),
          "okx long-short-account-ratio: [ts, ratio]")
    # Deribit
    dh = L("fut/deribit_funding_history_btc.json")["result"]
    byd: dict = {}
    for r in dh:
        byd.setdefault(day_of(r["timestamp"]), []).append(r["interest_1h"])
    wd = {d: 100 * 365 * sum(v) for d, v in byd.items() if d < TODAY and len(v) >= 24}
    gd = dict(C.daily_funding(fut.deribit_funding(L("fut/deribit_funding_history_btc.json")),
                              TODAY, expected=24))
    check(gd.keys() == wd.keys() and all(near(gd[d], wd[d]) for d in wd) and wd,
          f"deribit get_funding_rate_history: interest_1h summed x 365 ({len(wd)} days)")
    check(fut.deribit_oi(L("fut/deribit_book_btc.json"))
          == L("fut/deribit_book_btc.json")["result"][0]["open_interest"],
          "deribit book summary: open_interest (USD on an inverse perpetual)")
    # Bybit (documented shape; the venue is off)
    gb = dict(C.daily_funding(fut.bybit_funding(L("fut/bybit_funding_history.json")), TODAY))
    check(len(gb) >= 3 and near(fut.bybit_oi_now(L("fut/bybit_tickers.json")),
                                4482560000.12)
          and near(fut.bybit_ratio(L("fut/bybit_account_ratio.json"))[-1][1], 0.55 / 0.45),
          "bybit (documented shape): funding by day, openInterestValue, buy/sell ratio")
    try:
        fut.bybit_list({"retCode": 10001, "retMsg": "params error"})
        bad = False
    except ValueError:
        bad = True
    check(bad, "a venue's error code raises, never parses to an empty success")
    # mempool
    hr, df = mempool.parse_hashrate(L("mempool/hashrate_3m.json"), TODAY)
    src = L("mempool/hashrate_3m.json")
    last = max((r for r in src["hashrates"] if day_of(r["timestamp"]) < TODAY),
               key=lambda r: r["timestamp"])
    check(hr[-1][0] == day_of(last["timestamp"]) and near(hr[-1][1], last["avgHashrate"])
          and len(df) == len({day_of(r["time"]) for r in src["difficulty"]
                              if day_of(r["time"]) < TODAY}),
          f"mempool hashrate: the day's avgHashrate ({len(hr)} days) and the "
          f"difficulty at each adjustment ({len(df)})")
    fees = mempool.parse_fees(L("mempool/fees_recommended.json"))
    check(fees == {"fastest": 2.0, "half_hour": 1.0, "hour": 1.0, "economy": 1.0,
                   "minimum": 1.0},
          "mempool fees/recommended: five tiers, sat/vB")
    check(near(mempool.parse_mempool_vsize(L("mempool/mempool_blocks.json")),
               sum(b["blockVSize"] for b in L("mempool/mempool_blocks.json"))),
          "mempool fees/mempool-blocks: the projected blocks' vsize summed")
    pools = mempool.parse_pools(L("mempool/pools_1w.json"))
    p1 = L("mempool/pools_1w.json")
    check(len(pools) == 10 and near(pools["foundryusa"],
                                    100 * 265 / p1["blockCount"]),
          f"mempool pools/1w: the top ten pools' share of the week's blocks "
          f"(Foundry {pools['foundryusa']:.2f}%)")
    check(near(mempool.parse_adjustment(L("mempool/difficulty.json")),
               L("mempool/difficulty.json")["difficultyChange"]),
          "mempool difficulty-adjustment: the estimated change, %")
    # fear and greed
    fg = fng.parse(L("fng/fng_all.json"), TODAY)
    check(fg[-1] == (TODAY, 55.0) and len(fg) == 400 and fg[0][0] < fg[-1][0],
          "fng: the day's value by UTC day (400 days in the trimmed fixture)")
    # blockscout
    bs = blockscout.parse_stats(L("eth/blockscout_stats.json"))
    tx = blockscout.parse_tx_chart(L("eth/blockscout_chart_txs.json"), TODAY)
    check(bs["gas"] == {"slow": 0.09, "average": 0.32, "fast": 1.84}
          and near(bs["utilization"], 51.0092185446754)
          and tx[-1] == ("2026-10-16", 1769890.0) and len(tx) >= 28,
          "blockscout /stats (gas oracle, utilisation) and the daily transaction chart")
    check("coin_price" not in json.dumps(bs) and "market_cap" not in json.dumps(bs),
          "Blockscout's CoinGecko price and cap are not parsed (13 Oct ruling)")
    # DefiLlama watch fees
    lw = llama.parse_chart(L("llama/fees_watch_hyperliquid.json"), TODAY)
    check(lw and lw[-1][0] < TODAY and lw[-1][1] == L("llama/fees_watch_hyperliquid.json")
          ["totalDataChart"][-1][1],
          "llama /summary/fees/hyperliquid: the daily chart, complete days")

    # --- B --------------------------------------------------------------------
    head("B. THE DERIVED SERIES AGAINST HAND COMPUTATIONS")
    db = str(TD / "obs.sqlite")
    days = [(dt.date(2026, 6, 1) + dt.timedelta(days=i)).isoformat() for i in range(120)]
    rows = []

    def put(key, d, v, inst=None):
        rows.append(C.row(key, d, v, f"{d}T23:00:00+00:00", "synthetic", inst))
    for i, d in enumerate(days):
        put("llama.stable_total", d, 300e9 + 1e9 * i)
        put("llama.stable_by_chain", d, 150e9 + 0.2e9 * i, "Ethereum")
        put("llama.stable_by_chain", d, 80e9, "Tron")
        put("hl.funding", d, 10.0 + (i % 7), "BTC")
        put("fut.funding_okx", d, 5.0 + (i % 5), "BTC")
        put("fut.funding_deribit", d, 2.0, "BTC")
        if i >= 20:                                   # OI from day 20 at two venues
            put("hl.oi", d, 3e9, "BTC")
            put("fut.oi_okx", d, 2e9 + 1e7 * i, "BTC")
        if i >= 30:                                   # the third from day 30
            put("fut.oi_deribit", d, 1e9, "BTC")
        put("llama.mcap_btc", d, 1.6e12)
        put("hl.funding", d, 4.0, "ETH")
        put("fut.funding_okx", d, 6.0, "ETH")
        if i >= 30:
            put("hl.oi", d, 2e9, "ETH")
            put("fut.oi_okx", d, 1e9, "ETH")
            put("fut.oi_deribit", d, 0.5e9, "ETH")
    with store(db) as st:
        st.write_many(rows)
        out = D.compute(st, now=NOW)
    get = lambda k, inst, d: next((r["value"] for r in out if r["registry_key"] == k  # noqa: E731
                                   and r["instrument"] == inst and r["observed_at"] == d),
                                  None)
    d5 = days[5]
    check(near(get("calc.stable_share", "Ethereum", d5),
               round(100 * (150e9 + 1e9) / (300e9 + 5e9), 4)),
          f"S-1: Ethereum's share {get('calc.stable_share', 'Ethereum', d5)}% = "
          f"151bn over 305bn on {d5}")
    d25, d40 = days[25], days[40]
    w25 = ((10.0 + 25 % 7) * 3e9 + (5.0 + 25 % 5) * (2e9 + 2.5e8)) / (3e9 + 2.25e9)
    check(near(get("calc.funding_agg", "BTC", d25), round(w25, 6))
          and get("calc.funding_agg", "BTC", days[10]) is None,
          f"S-3: BTC funding OI-weighted over the two venues with OI on {d25} "
          f"({w25:.4f}%); not written before two venues carry OI")
    oi40 = 3e9 + (2e9 + 4e8) + 1e9
    w40 = ((10.0 + 40 % 7) * 3e9 + (5.0 + 0) * 2.4e9 + 2.0 * 1e9) / oi40
    check(near(get("calc.funding_agg", "BTC", d40), round(w40, 6))
          and near(get("calc.oi_usd", "BTC", d40), oi40)
          and get("calc.oi_usd", "BTC", d25) is None,
          f"S-3: with all three venues, funding {w40:.4f}% and total OI "
          f"${oi40 / 1e9:.1f}bn on {d40}; the total is not written while a venue is "
          f"missing")
    check(near(get("calc.oi_mcap", "BTC", d40), round(100 * oi40 / 1.6e12, 6)),
          "S-3: OI over market cap, %")
    check(near(get("calc.oi_usd", None, d40), oi40 + 3.5e9),
          "S-3: the BTC + ETH total (instrument NULL)")
    agg = {r["observed_at"]: r["value"] for r in out
           if r["registry_key"] == "calc.funding_agg" and r["instrument"] == "BTC"}
    zd = days[-1]
    lo = (dt.date.fromisoformat(zd) - dt.timedelta(days=89)).isoformat()
    xs = [v for d, v in agg.items() if lo <= d <= zd]
    mu = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - mu) ** 2 for x in xs) / len(xs))
    check(near(get("calc.leverage_z", "BTC", zd), round((agg[zd] - mu) / sd, 4), 1e-6)
          and len(xs) >= 60 and get("calc.leverage_z", "BTC", days[60]) is None,
          f"S-3: the 90-day z of the aggregate on {zd} by hand ({(agg[zd] - mu) / sd:+.3f},"
          f" n={len(xs)}); not written under 60 observations")
    check(D.funding_agg({"a": (10.0, 1e9), "b": (None, 1e9)}) is None
          and D.funding_agg({"a": (10.0, 1e9)}, 1) == 10.0,
          "a single venue is never an aggregate (min_venues 2)")
    with store(db) as st:
        res = D.pull(db=st)
    check(res["status"] == "OK" and res["written"] > 0,
          f"crypto_derived writes through the publication contract ({res['written']} rows)")
    with store(str(TD / "empty.sqlite")) as st:
        e = D.pull(db=st)
    check(e["status"] == "STALE" and e["written"] == 0,
          "with no inputs stored the derived writer is STALE and writes nothing")

    # --- C --------------------------------------------------------------------
    head("C. HYPERLIQUID'S WEIGHT GUARD")
    h = cfg["hyperliquid"]
    check(h["limit_per_min"] == 1200 and h["budget_per_min"] <= h["limit_per_min"]
          and h["weight_info"] == 20 and h["weight_per_items"] == {"fundingHistory": 20}
          and h["max_items"] == 500,
          "config holds the documented limits: 1,200 a minute; info 20; fundingHistory "
          "+1 per 20 items, 500 a page; a budget under the limit")
    check(hl.weight_of({"type": "metaAndAssetCtxs"}) == 20
          and hl.weight_of({"type": "fundingHistory"}) == 45,
          "a funding page is charged its worst case (20 + 500/20 = 45) before it is sent")
    t = [0.0]
    sent: list = []
    g = hl.WeightGuard(budget=100, limit=1200, clock=lambda: t[0],
                       sleep=lambda s: None, max_wait=0)
    c = hl.Client(guard=g, post=lambda b: sent.append(b) or [], cfg=cfg)
    c.info({"type": "fundingHistory"})
    c.info({"type": "fundingHistory"})
    try:
        c.info({"type": "fundingHistory"})
        refused = False
    except hl.WeightExceeded:
        refused = True
    check(refused and len(sent) == 2 and g.total == 90,
          "a burst past the minute's budget is REFUSED and the request is never sent")
    t[0] = 61.0
    c.info({"type": "fundingHistory"})
    check(len(sent) == 3, "after the window clears the request goes")
    slept: list = []
    t2 = [0.0]
    g2 = hl.WeightGuard(budget=50, limit=1200, clock=lambda: t2[0],
                        sleep=lambda s: (slept.append(s), t2.__setitem__(0, t2[0] + s)))
    g2.charge(45)
    g2.charge(45)
    check(slept and 59 < slept[0] < 61, f"with waiting allowed the guard sleeps out the "
                                        f"window ({slept[0]:.1f}s) instead of overrunning")
    try:
        hl.WeightGuard(budget=1300, limit=1200)
        over = False
    except ValueError:
        over = True
    check(over, "a budget above Hyperliquid's limit is refused at construction")

    # --- D --------------------------------------------------------------------
    head("D. ONE VENUE FAILING DOES NOT STOP THE OTHERS")

    def fake_get(url, params=None):
        if "okx.com" in url:
            raise OSError("okx down")
        if "get_funding_rate_history" in url:
            return L("fut/deribit_funding_history_btc.json")
        if "get_book_summary" in url:
            return L("fut/deribit_book_btc.json")
        raise AssertionError(url)
    rows_f, s = fut.collect(fake_get, cfg=cfg, today=TODAY, now=NOW)
    keys = {r["registry_key"] for r in rows_f}
    check({"fut.funding_deribit", "fut.oi_deribit"} <= keys
          and not any(k.endswith("_okx") for k in keys)
          and {"okx[BTC]", "okx[ETH]"} == {f[0] for f in s["failed"]}
          and s["off"].get("bybit"),
          "OKX failing: Deribit's rows land, OKX is named, Bybit is reported off "
          "with its reason")
    with store(str(TD / "fail.sqlite")) as st:
        r_all = fut.pull(db=st, get=lambda u, p=None: (_ for _ in ()).throw(OSError("down")),
                         today=TODAY, now=NOW)
        n = st.conn.execute("select count(*) from observations").fetchone()[0]
    check(r_all["status"] == "STALE" and n == 0,
          "every venue failing: STALE, nothing written")

    def mp_get(path):
        if "pools" in path:
            raise OSError("pools down")
        name = {"/v1/mining/hashrate/3m": "hashrate_3m", "/v1/difficulty-adjustment":
                "difficulty", "/v1/fees/recommended": "fees_recommended",
                "/v1/fees/mempool-blocks": "mempool_blocks"}[path]
        return L(f"mempool/{name}.json")
    mrows, ms = mempool.collect(mp_get, lambda p: "971859", today=TODAY, now=NOW)
    check({r["registry_key"] for r in mrows} == {
        "mempool.hashrate", "mempool.difficulty", "mempool.difficulty_change_est",
        "mempool.fee_rate", "mempool.mempool_vsize", "mempool.tip_height"}
          and ms["failed"][0][0] == "pool_share",
          "mempool: the pools endpoint failing costs the pool shares only")

    # --- E --------------------------------------------------------------------
    head("E. BACKFILLS: BOUNDED AND POINT IN TIME")
    calls: list = []

    def hl_post(body):
        calls.append(body)
        if body["type"] == "metaAndAssetCtxs":
            return L("hl/meta_and_asset_ctxs.json")
        t0 = body["startTime"]
        return [{"coin": body["coin"], "fundingRate": "0.00001", "premium": "0",
                 "time": t0 + k * 3_600_000} for k in range(500)
                if t0 + k * 3_600_000 < body["endTime"]]
    gq = hl.WeightGuard(budget=600, clock=lambda: 0.0, sleep=lambda s: None,
                        max_wait=1e12)
    gq.charge = lambda w: None                                   # no pacing in a gate
    cl = hl.Client(guard=gq, post=hl_post, cfg=cfg)
    with store(str(TD / "bf.sqlite")) as st:
        res = hl.backfill(db=st, client=cl)
        rws = st.conn.execute("select observed_at, available_at from observations "
                              "where registry_key='hl.funding' order by observed_at").fetchall()
    fpages = [b for b in calls if b["type"] == "fundingHistory"]
    first_ms = int(dt.datetime.fromisoformat(
        str(cfg["backfill"]["hyperliquid_funding_from"]) + "T00:00:00+00:00").timestamp() * 1000)
    check(res["status"] == "OK" and rws[0][0] == str(cfg["backfill"]["hyperliquid_funding_from"])
          and all(b["startTime"] >= first_ms for b in fpages)
          and len(fpages) <= 2 * int(cfg["backfill"]["max_pages"]),
          f"hl backfill from {cfg['backfill']['hyperliquid_funding_from']} in "
          f"{len(fpages)} pages (500 hours each), within the page cap")
    av = {r[1] for r in rws}
    check(len(av) == 1 and next(iter(av)) > "2026-01-01",
          "every backfilled day carries the pull instant as available_at, never "
          "a backdated one")
    small = dict(cfg, backfill=dict(cfg["backfill"], max_pages=3))
    cl2 = hl.Client(guard=gq, post=hl_post, cfg=small)
    calls.clear()
    hl.collect(cl2, start_day="2023-05-12", today=TODAY, now=NOW)
    check(len([b for b in calls if b["type"] == "fundingHistory"]) == 2 * 3,
          "the page cap stops a backfill (3 pages a coin)")
    seen_urls: list = []

    def fut_get(url, params=None):
        seen_urls.append((url, dict(params or {})))
        if "okx.com" in url:
            return {"code": "0", "data": []}
        if "get_funding_rate_history" in url:
            return {"result": []}
        return {"result": []}
    fut.collect(fut_get, cfg=cfg, today=TODAY, now=NOW,
                first={"okx": "2025-10-17", "deribit": "2019-01-01"}, backfill=True)
    der = [p for u, p in seen_urls if "get_funding_rate_history" in u]
    check(der and der[0]["start_timestamp"] == 1546300800000
          and all(p["end_timestamp"] - p["start_timestamp"] <= 30 * 86_400_000 for p in der)
          and not any("get_book_summary" in u or "public/open-interest" in u
                      for u, _ in seen_urls),
          f"fut backfill: Deribit from its bound in 30-day windows ({len(der)} calls a "
          f"coin pair); no snapshot is written as history")
    mrows2, _ = mempool.collect(lambda p: L("mempool/hashrate_3m.json") if p.endswith("/all")
                                else (_ for _ in ()).throw(AssertionError(p)),
                                lambda p: "1", period="all", history_only=True,
                                today=TODAY, now=NOW)
    check(mrows2 and all(r["observed_at"] < TODAY and r["available_at"] == NOW
                         for r in mrows2),
          "mempool backfill: /hashrate/all once, history only, complete days, the pull "
          "instant as available_at")

    # --- F --------------------------------------------------------------------
    head("F. NOTHING STORED TWICE WITH THE CRYPTO BASKET")
    basket = set(llama.basket())
    watch_syms = {n["sym"] for n in cfg["watch_names"]}
    check(not (basket & watch_syms),
          f"the watch names exclude the basket names ({sorted(basket & {'AAVE', 'TAO', 'PRL'})}"
          f" are the basket's)")
    check(not (set(llama.WATCH_KEYS) & set(llama.PROTOCOL_KEYS))
          and set(llama.COIN_KEYS) >= {"mcap_btc", "mcap_eth"}
          and len(set(llama.COIN_KEYS)) == len(llama.COIN_KEYS),
          "no watch key is a basket key; the coin service's BTC and ETH caps join its "
          "own list once")
    newk = set(hl.KEYS + fut.KEYS + mempool.KEYS + fng.KEYS + blockscout.KEYS + D.KEYS)
    from altdata.sources import yfinance_source as yf
    from altdata import crypto_basket as cb
    existing = ({f"llama.{k}" for k in llama.PROTOCOL_KEYS + llama.COIN_KEYS + llama.MACRO_KEYS}
                | {f"yfinance.{k}" for k in yf.CRYPTO_BASKET_KEYS}
                | {"calc.stable_impulse_30d", "calc.stable_impulse_90d"}
                | {f"calc.{k}" for k in cb.DILUTION_KEYS})
    check(not (newk & existing),
          f"the {len(newk)} new keys meet none of the basket's")
    src_d = (REPO / "altdata" / "sources" / "crypto_derived.py").read_text(encoding="utf-8")
    check('"llama.stable_total"' in src_d and "stablecoincharts" not in src_d,
          "S-1's share reads the stored stablecoin series, never a second fetch of it")

    # --- G --------------------------------------------------------------------
    head("G. REGISTRY, ROSTER, CATALOGUE, GAPS")
    import yaml
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    vocab = set(reg["vocabularies"]["units"])
    M = reg["metrics"]
    ok = [k for k in sorted(newk) if k in M and M[k].get("family") and M[k].get("long_window")
          and M[k].get("units") in vocab]
    check(len(ok) == len(newk), f"every new key is registered with family, long_window "
                                f"and a vocabulary unit ({len(ok)}/{len(newk)})")
    bulk = reg["bulk_imports"]
    check(bulk["llama_watch_daily"]["expected_members"] == len(llama.WATCH_KEYS) == 12
          and bulk["llama_coin_mcap"]["expected_members"] == len(llama.MCAP_KEYS) == 14,
          "the watch names' block (12) and the caps' block (14) match the code")
    srcs = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))["sources"]
    check({"hyperliquid", "perp_venues", "mempool_space", "alternative_me", "blockscout"}
          <= set(srcs), "the five sources are registered")
    from altdata import feeds
    ew = feeds.EXTERNAL_WRITERS
    check(all(n in ew for n in ("hl", "fut", "mempool", "fng", "blockscout", "crypto_derived"))
          and ew.index("crypto_derived") > max(ew.index("hl"), ew.index("fut")),
          "the six writers are on the external roster, the derived one after the venues")
    wrap = (REPO / "scripts" / "run_crypto_basket.sh").read_text(encoding="utf-8")
    check(all(f"altdata.sources.{n}" in wrap for n in ("hl", "fut", "mempool", "fng",
                                                       "blockscout", "crypto_derived")),
          "and on the daily crypto run (17:25 ET every day: the weekend too)")
    cat = yaml.safe_load((REPO / "config" / "catalogue_commands.yaml").read_text(
        encoding="utf-8"))["commands"]
    check(all(f"altdata.sources.{n}" in cat for n in ("hl", "fut", "mempool", "fng",
                                                      "blockscout", "crypto_derived")),
          "each has its line in the command catalogue")
    gaps = cfg["gaps"]
    check({"raises", "eth_supply_burn", "coingecko_global", "bybit"} <= set(gaps)
          and "ETHERSCAN_API_KEY" in gaps["eth_supply_burn"]
          and not cfg["venues"]["bybit"]["enabled"],
          "the gaps are named: /raises (402), ETH supply and burn (ETHERSCAN_API_KEY), "
          "CoinGecko /global, Bybit (off)")
    srcs_txt = "".join((REPO / "altdata" / "sources" / f"{n}.py").read_text(encoding="utf-8")
                       for n in ("hl", "fut", "mempool", "fng", "blockscout",
                                 "crypto_derived", "_crypto"))
    check("secrets" not in srcs_txt and "API_KEY" not in srcs_txt.replace(
        "ETHERSCAN_API_KEY", ""),
          "no writer reads a key")
    check(not set(fut.BYBIT_KEYS) & set(M),
          "Bybit's keys are not registered while the venue is off")

    # --- H --------------------------------------------------------------------
    head("H. THE WATCH NAMES, RESOLVED AT RUN TIME")
    prot, ov = L("llama/protocols_watch.json"), L("llama/fees_overview_chains.json")
    res = llama.resolve_watch(cfg["watch_names"], prot, ov)
    check({k: v[0] for k, v in res.items()} == {
        "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "ZEC": "zcash",
        "HYPE": "hyperliquid", "LINK": "chainlink"},
          "chains from /overview/fees by name; HYPE and LINK as their /protocols "
          "parent (hyperliquid, chainlink)")
    check(not any("slug" in n for n in cfg["watch_names"]),
          "config carries no slug: nothing is hard-coded")
    amb = llama.resolve_watch([{"sym": "X", "kind": "protocol", "match": "X"}],
                              [{"symbol": "X", "parentProtocol": "parent#a"},
                               {"symbol": "X", "parentProtocol": "parent#b"}], {})
    check(amb["X"][0] is None and "2 parents" in amb["X"][1],
          "two candidate parents: refused with the reason, never a guess")
    fetched: list = []

    def ll_get(url, params=None):
        fetched.append(url)
        if url.endswith("/protocols"):
            return prot
        if "/overview/fees" in url:
            return ov
        if "/summary/fees/" in url:
            return L("llama/fees_watch_hyperliquid.json")
        raise AssertionError(url)
    lrows, ls = llama.collect(only="watch", fetch=ll_get, today=TODAY)
    check({r["registry_key"] for r in lrows} == {f"llama.{k}" for k in llama.WATCH_KEYS}
          and ls["watch_slugs"]["HYPE"][0] == "hyperliquid" and not ls["failed"],
          f"llama --only watch writes the twelve watch series ({len(lrows)} rows)")

    part2(cfg)
    treasury_checks(cfg)
    check(not _SOCKETS, "no connection was attempted")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


# ===========================================================================
# PART 2 (crypto-tranche-a-2, 17 Oct 2026): CD-3, CD-4, CD-7, CD-8, CD-9, CD-10
# ===========================================================================
def part2(cfg: dict) -> None:
    from altdata.sources import (_crypto as C, crypto_derived as D, deribit, farside,
                                 fut, gt, hl, paprika)
    from altdata import crypto_blocks as B

    head("I. PART 2 PARSERS, ON THE STORED RESPONSES")
    dv = L("deribit/dvol_btc.json")["result"]["data"]
    want = {day_of(r[0]): r[4] for r in dv if day_of(r[0]) < TODAY}
    got = dict(deribit.parse_dvol(L("deribit/dvol_btc.json"), TODAY))
    check(got == want and len(got) >= 30,
          f"deribit get_volatility_index_data: each UTC day's candle close "
          f"({len(got)} days; today's open candle held back)")
    try:
        deribit.parse_dvol({"error": {"code": 10001}}, TODAY)
        raised = False
    except ValueError:
        raised = True
    check(raised, "a Deribit error answer raises, never parses to nothing")
    pg = paprika.parse(L("paprika/global.json"))
    check(pg["total_mcap_usd"] == L("paprika/global.json")["market_cap_usd"]
          and pg["btc_dominance"] == L("paprika/global.json")["bitcoin_dominance_percentage"],
          f"coinpaprika /v1/global: total cap and BTC dominance "
          f"({pg['btc_dominance']}%)")
    cols = cfg["farside"]["columns"]["btc"]
    fs = farside.parse_table((FX / "farside" / "btc.html").read_text(encoding="utf-8"),
                             "btc", cols)
    d16 = next(x for x in fs if x["date"] == "2026-10-16")
    d13 = next(x for x in fs if x["date"] == "2026-10-13")
    check(len(fs) == 5 and d16["total"] == -82.4 and d16["issuers"]["IBIT"] == -71.8
          and d16["issuers"]["BITB"] is None and d13["issuers"]["GBTC"] == -10.0
          and d13["issuers"]["BTCO"] == 0.0,
          "farside: date rows only (fee, Total, Average, Max, Min dropped); (x) is "
          "negative; '-' is no figure, never a zero; 0.0 stays 0.0")
    fr = farside.rows_from(fs, "btc", NOW, TODAY)
    tot = {r["observed_at"]: r["value"] for r in fr if r["registry_key"] == "farside.btc_total"}
    check(tot["2026-10-16"] == -82.4e6 and "2026-10-17" not in tot,
          "stored in dollars (US$m x 1e6); a session with no Total is not written")
    try:
        farside.parse_table((FX / "farside" / "btc_changed.html").read_text(encoding="utf-8"),
                            "btc", cols)
        refused = False
    except farside.HeaderChanged as exc:
        refused = "NEWF" in str(exc)
    check(refused, "THE COLUMN-CHANGE DETECTOR refuses a table whose issuer columns "
                   "changed, naming the change")
    now_dt = dt.datetime(2026, 10, 17, 20, 0, tzinfo=dt.timezone.utc)
    n, sat = gt.count_new([L("gt/new_pools_p1.json"), L("gt/new_pools_p2.json")], now_dt)
    want_n = sum(1 for p in L("gt/new_pools_p1.json")["data"] + L("gt/new_pools_p2.json")["data"]
                 if p["attributes"]["pool_created_at"] >= "2026-10-16T20:00:00Z")
    check(n == want_n and not sat,
          f"geckoterminal new_pools (the documented shape): {n} created in 24 hours, "
          f"counted across pages, newest first")
    tv = gt.trending_volume(L("gt/trending_pools.json"), 20)
    check(near(tv, sum(1e6 * (i + 1) for i in range(20))),
          "geckoterminal trending_pools: the top 20 pools' 24-hour volume summed")
    ds = L("gt/dexscreener_search_solana.json")
    wds = sum(sorted((p.get("volume") or {}).get("h24") or 0 for p in ds["pairs"]
                     if p["chainId"] == "solana")[::-1][:20])
    check(near(gt.dexscreener_volume(ds, "solana"), wds),
          "dexscreener search (the real response): the fallback's volume sum on the network")

    head("J. THE GECKOTERMINAL GUARD, TERMS AND FALLBACK")
    sent: list = []
    g = hl.WeightGuard(budget=3, limit=30, clock=lambda: 0.0, sleep=lambda s: None,
                       max_wait=0)

    def gt_get(url, params=None):
        sent.append(url)
        return L("gt/new_pools_p1.json") if "new_pools" in url else L("gt/trending_pools.json")
    rows, s = gt.collect(gt_get, lambda u, p=None: ds, robots=lambda: (True, ""),
                         guard=g, today=TODAY, now="2026-10-17T20:00:00.000000+00:00")
    check(len(sent) == 3 and s["failed"] and "WeightExceeded" in s["failed"][0][1],
          "a burst past the guard's budget is refused: the fourth call is never sent")
    # Ruling 4 of 17 Oct: the documented API is governed by its own terms, not by
    # the host's robots.txt, so the default collect reads no robots and calls it.
    calls: list = []

    def gt_ok(url, params=None):
        calls.append(url)
        return L("gt/new_pools_p1.json") if "new_pools" in url else L("gt/trending_pools.json")
    g2 = hl.WeightGuard(budget=30, limit=30, clock=lambda: 0.0, sleep=lambda s: None,
                        max_wait=0)
    rows, s = gt.collect(gt_ok, lambda u, p=None: ds, guard=g2, today=TODAY, now=NOW)
    check(calls and not s["failed"] and not hasattr(gt, "robots_ok")
          and any(r["registry_key"] == "gt.new_pools_24h" for r in rows),
          "ruling 4: the writer calls GeckoTerminal's documented API with no robots.txt "
          "read in front of it (its terms govern, not the host's robots)")
    gcfg = C.config().get("gt") or {}
    check(int(gcfg.get("per_min") or 0) == 10 and int(gcfg.get("budget_per_min") or 99) < 10
          and "version=20230203" in str(gcfg.get("accept")),
          "the guard sits under the published limit (about 10 calls a minute, the "
          "swagger read 17 Oct) and the Accept header names the documented version")
    import yaml
    srcreg = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))["sources"]
    check(all(srcreg[k].get("terms_url") and str(srcreg[k].get("terms_read")) == "2026-10-17"
              and srcreg[k].get("terms_reread") == "quarterly"
              for k in ("coinpaprika", "geckoterminal")),
          "rulings 3 and 4: CoinPaprika's and GeckoTerminal's catalogue entries carry the "
          "terms URL, the date read and the quarterly re-read")

    def gt_down(url, params=None):
        raise RuntimeError("HTTP 503")
    rows, s = gt.collect(gt_down, lambda u, p=None: ds, guard=g2, today=TODAY, now=NOW)
    fb = [r for r in rows if r["registry_key"] == "gt.trending_vol_24h"]
    check(fb and all(r["source"] == "dexscreener:fallback" for r in fb)
          and not any(r["registry_key"] == "gt.new_pools_24h" for r in rows),
          "the DexScreener fallback writes trending volume only, its row marked "
          "dexscreener:fallback in the source column")

    head("K. S-2, S-4, S-5 AND THE FLAGS AGAINST HAND COMPUTATIONS")
    db = str(TD / "p2.sqlite")
    sessions = [(dt.date(2026, 6, 1) + dt.timedelta(days=i)).isoformat() for i in range(60)]
    flows = [((-1) ** (i // 3)) * (10e6 + 1e6 * i) for i in range(60)]
    rows = []

    def put(key, d, v, inst=None, src="synthetic"):
        rows.append(C.row(key, d, v, f"{d}T23:00:00+00:00", src, inst))
    for d, v in zip(sessions, flows):
        put("farside.btc_total", d, v)
    days = [(dt.date(2026, 5, 1) + dt.timedelta(days=i)).isoformat() for i in range(140)]
    for i, d in enumerate(days):
        put("deribit.dvol_btc", d, 40.0 + (i % 17))
        put("yfinance.mkt_btc_usd", d, 60000.0 * (1 + 0.01 * ((i * 7) % 5 - 2)))
        put("gt.new_pools_24h", d, 100.0 + (i % 9), "solana", "geckoterminal")
        put("gt.trending_vol_24h", d, 5e6 + 1e5 * (i % 11), "solana", "geckoterminal")
    put("gt.trending_vol_24h", days[-1], 9e9, "base", "dexscreener:fallback")
    with store(db) as st:
        st.write_many(rows)
        out = D.compute(st, now=NOW)
    get = lambda k, inst, d: next((r["value"] for r in out if r["registry_key"] == k  # noqa: E731
                                   and r["instrument"] == inst and r["observed_at"] == d), None)
    # streak by hand: signs flip every three sessions
    i = 40
    run = 1
    while i - run >= 0 and (flows[i - run] > 0) == (flows[i] > 0):
        run += 1
    check(get("calc.etf_streak", "btc", sessions[40]) == run * (1 if flows[40] > 0 else -1),
          f"S-2: the streak on {sessions[40]} is {run} same-sign sessions, signed")
    s5 = [sum(flows[j - 4:j + 1]) for j in range(4, 41)]
    p = 100.0 * sum(1 for x in s5 if x <= s5[-1]) / len(s5)
    check(near(get("calc.etf_5d_pct", "btc", sessions[40]), round(p, 4))
          and get("calc.etf_5d_pct", "btc", sessions[10]) is None,
          f"S-2: the five-session sum's percentile against every sum to the day "
          f"({p:.1f}); none under 20 sums")
    flag = get("calc.flag_etf_extreme", "btc", sessions[40])
    check(flag == (1.0 if (p <= 5 or p >= 95) else 0.0),
          "S-2's flag is stored at the 5th and 95th percentile")
    dvs = [40.0 + (k % 17) for k in range(140)]
    pf = 100.0 * sum(1 for x in dvs[:100] if x <= dvs[99]) / 100
    check(near(get("calc.dvol_pct_full", "BTC", days[99]), round(pf, 4))
          and get("calc.dvol_pct_full", "BTC", days[30]) is None,
          f"S-4: DVOL's full-history percentile by hand ({pf:.1f}); none under 60 days")
    cl = [60000.0 * (1 + 0.01 * ((k * 7) % 5 - 2)) for k in range(140)]
    r = [math.log(cl[k] / cl[k - 1]) for k in range(70, 100)]
    mu = sum(r) / len(r)
    rv = 100 * math.sqrt(365) * math.sqrt(sum((x - mu) ** 2 for x in r) / (len(r) - 1))
    check(near(get("calc.dvol_minus_rv30", "BTC", days[99]), round(dvs[99] - rv, 4), 1e-6),
          f"S-4: DVOL less realised from the stored closes ({dvs[99] - rv:+.2f} pts)")
    fz = {r_["observed_at"]: r_["value"] for r_ in out if r_["registry_key"] == "calc.froth_z"
          and r_["instrument"] == "solana:new_pools"}
    check(fz and min(fz) == days[89] and not any(
        r_["registry_key"] == "calc.froth_z" and str(r_["instrument"]).startswith("base")
        for r_ in out),
          f"S-5: the froth z starts on the 90th day of GeckoTerminal store ({days[89]}); "
          f"a DexScreener fallback row is never scored")
    xs = [100.0 + (k % 9) for k in range(120, 140)]
    m_ = sum(xs) / 20
    sd = math.sqrt(sum((x - m_) ** 2 for x in xs) / 20)
    check(near(fz[days[139]], round((xs[-1] - m_) / sd, 4), 1e-6),
          "S-5: the z on a 20-day window by hand")
    check({k for k in D.FLAG_KEYS} <= {r_["registry_key"] for r_ in out} | {"calc.flag_leverage_crowded"}
          and D.GATE_STATUS == "not passed",
          "the flags are computed into the store, gate status \"not passed\"")

    head("L. THE BLOCKS: <= 12 LINES, DATA-AS-OF, STALE WITH ITS DATE, NO FLAG")
    db2 = str(TD / "blocks.sqlite")
    rows = []
    for k_, d in enumerate(days):
        put("llama.stable_total", d, 300e9 + 1e9 * k_)
        put("calc.funding_agg", d, 8.0, "BTC")
        put("calc.oi_usd", d, 50e9)
        put("mempool.hashrate", d, 1e21)
        put("mempool.fee_rate", d, 2.0, "fastest")
        put("paprika.btc_dominance", d, 57.3)
        put("paprika.total_mcap_usd", d, 2.9e12)
        for fk in D.FLAG_KEYS:                         # EVERY FLAG TRUE
            put(fk, d, 1.0, "BTC")
            put(fk, d, 1.0, "btc")
            put(fk, d, 1.0, "solana")
    put("farside.btc_total", "2026-10-01", 5e7)        # stale: last good 1 Oct
    put("mempool.difficulty", "2026-09-20", 1.40e14)
    put("mempool.difficulty", "2026-10-04", 1.42e14)
    with store(db2) as st:
        st.write_many(rows)
        wb = B.weekly_block(st, NOW, cfg)
        mm = B.monthly_mechanics(st, NOW)
        ms = B.monthly_slow(st, NOW, cfg)
    text = json.dumps([wb, mm, ms]).lower()
    lines = {r_[0]: r_ for r_ in wb["table"]["rows"]}
    check(len(wb["table"]["rows"]) <= 12 and all(r_[2] for r_ in wb["table"]["rows"]),
          f"the Weekly block: {len(wb['table']['rows'])} lines, at most 12, each with its "
          f"data-as-of")
    # Farside is refused since the feed repair of 24 Oct 2026 (a61b item 5): the
    # line prints the gap, never an empty cell or a zero, whatever is stored.
    from altdata import refusals as _ref
    _fs = lines["BTC spot ETF flows, the week"][1]
    check(_fs.startswith(_ref.text("farside")[:40]) and "0" != _fs.strip(),
          f"THE REFUSED RENDER: the Farside line prints the refusal -- never an empty "
          f"cell, never a zero ({_fs})")
    check("flag" not in text and "crowded" not in text and "extreme" not in text,
          "NO FLAG PRINTS: with every flag true in the store, no block prints one")
    check("z-score from 15 Dec 2026" in lines["BTC perp funding, OI-weighted (annualised)"][1],
          "ruling 5: the aggregate prints its level and \"z-score from 15 Dec 2026\"")
    check(lines["Crypto market cap; BTC dominance"][1] == "$2.90tn; 57.3%",
          "the dominance line reads CoinPaprika's stored figures (ruling 2)")
    check("not sampled" in lines[next(k for k in lines if k.startswith("Froth gauge"))][1]
          and "unscored until 15 Jan 2027" in next(k for k in lines if k.startswith("Froth")),
          "the froth line prints unscored, and says why it has no sample")
    check(any("ETHERSCAN_API_KEY" in x for x in mm["lines"])
          and any("SR-29" in x and "not tracked (btcdata.lth_supply_share)" in x
                  for x in mm["lines"]),
          "the Monthly's mechanics: the ETH supply-and-burn gap named, SR-29 not "
          "tracked with its key named")
    cd12()
    fv = next(x for x in ms if x["title"].startswith("Factor V"))
    check(fv["table"]["columns"][-2:] == ["Percentile, 5 years", "Percentile, full history"]
          and fv["table"]["rows"][0][0] == "Stablecoin supply, total",
          "Factor V rows (SR-20's amendment) in the triple form with dual percentiles")
    ul = next(x for x in ms if x["title"].startswith("Token unlocks"))
    vc = next(x for x in ms if x["title"].startswith("VC raises"))
    check(ul["lines"][0].startswith("No schedules entered") and "402" in vc["lines"][0],
          "unlocks print \"no schedules entered\"; VC raises \"not available: the "
          "endpoint is paywalled\"")

    head("M. ISOLATION, BACKFILLS, THE GREP GATE, AVAILABLE_AT")
    calls2: list = []

    def dv_get(url, params=None):
        calls2.append(dict(params))
        if params["currency"] == "ETH":
            raise OSError("ETH down")
        return L("deribit/dvol_btc.json")
    rr, ss = deribit.collect(dv_get, first="2021-03-24", today=TODAY, now=NOW)
    check(rr and all(r_["registry_key"] == "deribit.dvol_btc" for r_ in rr)
          and ss["failed"][0][0] == "deribit.dvol_eth",
          "DVOL: ETH failing leaves BTC's rows; the failure is named")
    btc_calls = [c for c in calls2 if c["currency"] == "BTC"]
    check(btc_calls[0]["start_timestamp"] == 1616544000000
          and all(c["end_timestamp"] - c["start_timestamp"] <= 900 * 86_400_000
                  for c in btc_calls) and len(btc_calls) <= 3,
          f"the DVOL backfill is bounded: from 24 Mar 2021 in {len(btc_calls)} windows "
          f"of at most 900 days")
    fs_rows, fs_s = farside.collect(lambda u: (_ for _ in ()).throw(OSError("403")),
                                    robots=lambda: (True, ""), today=TODAY, now=NOW)
    check(not fs_rows and len(fs_s["failed"]) == 2,
          "Farside refused: nothing parsed, both tables named")
    asked_fs: list = []
    with store(str(TD / "fs.sqlite")) as st:
        st.write_many([C.row("farside.btc_total", "2026-10-01", 1.0, "2026-10-02T00:00:00+00:00",
                             "farside")])
        res = farside.pull(db=st, get=lambda u: asked_fs.append(u) or "",
                           robots=lambda: (True, ""), today=TODAY, now=NOW)
    check(res["status"] == "REFUSED" and res["written"] == 0 and not asked_fs
          and "refuses automated reads" in res["reason"],
          "REFUSED: a declared refusal asks nothing and writes nothing, the reason named "
          "(the feed repair of 24 Oct 2026)")
    fb_rows, _ = farside.collect(lambda u: (FX / "farside" / ("btc.html" if "bitcoin" in u
                                                               or "/btc/" in u else "eth.html")
                                            ).read_text(encoding="utf-8"),
                                 pages="all_data", robots=lambda: (True, ""), today=TODAY,
                                 now=NOW)
    check(fb_rows and all(r_["available_at"] == NOW for r_ in fb_rows),
          "the all-data backfill is point in time: the pull instant as available_at")
    check(cfg["farside"]["backfill_from"] == dt.date(2024, 1, 11)
          or str(cfg["farside"]["backfill_from"]) == "2024-01-11",
          "and bounded: from the ETFs' first session, 11 Jan 2024")
    check(set(fut.VENUES) == {"okx", "deribit"} and hasattr(fut, "bybit"),
          "ruling 1: Bybit's reader stays in the tree with no call path")
    # THE GREP GATE: no report module imports a crypto writer; nothing fetches at render.
    import re as _re
    writers = ("llama", "hl", "fut", "mempool", "fng", "blockscout", "deribit",
               "farside", "gt", "paprika", "crypto_derived")
    pat = _re.compile(r"(?:from\s+altdata\.sources\s+import[^\n]*\b(?:"
                      + "|".join(writers) + r")\b|altdata\.sources\.(?:"
                      + "|".join(writers) + r")\b)")
    bad = []
    for root in ("daily_cascade", "monthly_macro"):
        for p_ in (REPO / root).rglob("*.py"):
            if pat.search(p_.read_text(encoding="utf-8", errors="replace")):
                bad.append(str(p_.relative_to(REPO)))
    bsrc = (REPO / "altdata" / "crypto_blocks.py").read_text(encoding="utf-8")
    check(not bad and "http_get" not in bsrc and "requests" not in bsrc
          and '"calc.flag' not in bsrc and "FLAG_KEYS" not in bsrc,
          f"THE GREP GATE: no report or renderer imports a crypto writer, the blocks "
          f"fetch nothing and read no flag key ({bad or 'none'})")
    # available_at on every crypto writer's rows
    samples = (fr + rr + fb + out)
    check(all(r_.get("available_at") for r_ in samples),
          f"available_at present on every row the part 2 writers produce "
          f"({len(samples)} checked)")


def treasury_checks(cfg: dict) -> None:
    """Item 49's writer (digital-49-51b, 17 Oct 2026)."""
    from altdata.sources import treasury as T
    from altdata import feeds
    head("N. ITEM 49: THE TREASURY WRITER")
    html = (FX / "treasury" / "bitbo_public_companies.html").read_text(encoding="utf-8")
    chains = TD / "chains" / "2026-10-16"
    chains.mkdir(parents=True, exist_ok=True)
    (chains / "MSTR_201500.csv").write_text(
        "expiry,dte,right,strike,bid,ask,last_price,volume,last_trade_date,fetched_at,spot\n"
        "2026-11-20,35,C,140,10,11,10.5,5,2026-10-16,2026-10-16T20:15:00+00:00,135.24\n",
        encoding="utf-8")
    rows, s = T.collect(lambda u: html, lambda u, h: (_ for _ in ()).throw(AssertionError("no UA")),
                        robots=lambda: (True, ""), user_agent=lambda: None,
                        chain_base=TD / "chains", today=TODAY, now=NOW)
    keys = {r["registry_key"] for r in rows}
    spot = [r for r in rows if r["registry_key"] == "treasury.mstr_spot"]
    check("treasury.btc_holdings" in keys and spot and spot[0]["value"] == 135.24
          and spot[0]["observed_at"] == "2026-10-16",
          "holdings from the table; MSTR's spot from the session's captured chain "
          "(local files, nothing fetched)")
    check(any(g[0] == "treasury.mstr_shares" and "CHESTER_SEC_CONTACT" in g[1]
              for g in s["gaps"]) and "treasury.mstr_shares" not in keys,
          "without the EDGAR contact the share count is a listed gap, never typed in")
    rows2, s2 = T.collect(lambda u: (_ for _ in ()).throw(AssertionError("fetched")),
                          robots=lambda: T.robots_ok(lambda u: "User-agent: *\nDisallow: /\n"),
                          user_agent=lambda: None, chain_base=TD / "chains",
                          today=TODAY, now=NOW)
    check(s2["failed"][0][0] == "holdings" and "refuses" in s2["failed"][0][1]
          and any(r["registry_key"] == "treasury.mstr_spot" for r in rows2),
          "a robots refusal stops the holdings read before any fetch; the spot still lands")
    src = (REPO / "altdata" / "sources" / "treasury.py").read_text(encoding="utf-8")
    code = src.split('"""', 2)[2]
    check("strategy.com" not in code and "bitcointreasuries.net" not in code,
          "strategy.com (403) and bitcointreasuries.net (terms forbid automated "
          "extraction) are never read")
    ew = feeds.EXTERNAL_WRITERS
    check("treasury" in ew and ew.index("treasury") < ew.index("crypto_derived"),
          "the treasury writer is on the roster, before the derived writer (mNAV)")


if __name__ == "__main__":
    sys.exit(main())
