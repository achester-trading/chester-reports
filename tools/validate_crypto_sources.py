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
    check(near(get("calc.funding_agg_z", "BTC", zd), round((agg[zd] - mu) / sd, 4), 1e-6)
          and len(xs) >= 60 and get("calc.funding_agg_z", "BTC", days[60]) is None,
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

    check(not _SOCKETS, "no connection was attempted")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
