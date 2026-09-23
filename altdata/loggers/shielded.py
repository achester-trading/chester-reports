"""
Zcash shielded-pool explorer probe, and the ZEC market series. (Part 29.5, LOGGING)

Two halves with different fates, which is why the order asked for the probe first:

  THE SHIELDED SHARE IS NOT AVAILABLE from anything reachable. Probed, failure
  stored, and the metric registered so it exists the day a source does.
  THE MARKET SERIES ARE, and they are logged nightly regardless -- price, realized
  volatility, and beta to BTC.

No theme block, no privacy-coin analysis: that is 6h and gated. This writes rows.

    python -m altdata.loggers.shielded probe
    python -m altdata.loggers.shielded pull

-----------------------------------------------------------------------------
THE POOLS ARE NOW SOURCED. THE TRANSACTION SHARE STILL IS NOT.
-----------------------------------------------------------------------------

Seven candidates, and the ruling's extra ones led to the one that answers:

    mainnet.zcashexplorer.app/api/v1/blockchain-info  HTTP 200, valuePools -- YES
    api.blockchair.com/zcash/stats                    HTTP 200, no shielded split
    api.zcashblockexplorer.com/status                 DNS does not resolve
    api.zcha.in/v2/mainnet/network                    HTTP 520
    data.messari.io/.../zec/metrics                   HTTP 404
    api.zechub.xyz/api/v1/shielded                    DNS does not resolve
    api.zfnd.org/metrics                              DNS does not resolve

zcashexplorer proxies zcashd's own blockchain-info, which publishes `valuePools`: the
balance of every pool on the chain. So the shielded share of SUPPLY is computable, and
it is logged as `zec.shielded_value_share`.

IT IS NOT THE TRANSACTION SHARE, AND THE TWO ARE NOT INTERCHANGEABLE. A value pool
balance is a STOCK; the transaction share is a FLOW -- how much of today's activity
used a shielded pool. A chain can hold a third of its supply shielded with almost no
shielded activity, or the reverse. This is the same distinction that keeps short
interest and short volume in separate mechanism groups, and it is why
`zec.shielded_tx_share` stays registered and EMPTY while the value share gets its own
name.

WHICH POOLS COUNT IS DECLARED, NOT INFERRED FROM "NOT TRANSPARENT". The chain has six
pools and three of them are a user choosing privacy (sprout, sapling, orchard). The
other three are excluded and each says why: transparent is not shielded; `lockbox` is
the NU6 development-fund reserve, which is protocol accounting rather than anyone's
privacy decision; and `ironwood` holds 3.99M ZEC -- nearly a quarter of supply -- whose
semantics I have not verified, and a number that large should not move a headline on a
guess. The three documented pools read 5.4 percent; folding in lockbox and ironwood
would read 29.4. The gap between those two numbers is the entire reason the list is
explicit.

A pool this code has never seen is reported as `unclassified_pools` and logged at
WARNING rather than silently dropped or averaged in: the chain gains pools at network
upgrades, and that should reach a human.

-----------------------------------------------------------------------------
SHARE OF CRYPTO CAP NOW HAS A SOURCE, AND IT IS FORWARD-ONLY
-----------------------------------------------------------------------------

CoinGecko's public API serves both halves, keyless -- /api/v3/global for the total and
simple/price with include_market_cap for ZEC's -- so the ruling's "stop and tell me if
it needs a key" branch does not fire. First read: total 2.93 trillion USD, ZEC 27.50
billion, a share of 0.938 percent.

IT CANNOT BE BACKFILLED. The free tier serves the CURRENT total capitalisation and no
history of it, so this series starts today and grows forward. That is precisely what
a forward-only logger is, and it is the argument for starting tonight rather than
after a data purchase: every night not logged is a night of this series that cannot
be recovered.

zec.btc_ratio KEEPS ITS OWN NAME, per the ruling. It is a relative price and the cap
share is a share of a market; now that both exist, having built the second is no
reason to conflate it with the first.
"""

from __future__ import annotations

import json
import logging
import math
import statistics
import urllib.error
import urllib.request
from typing import Any, Optional

from .. import observations, session
from . import LoggerSpec, guarded_days, register

log = logging.getLogger(__name__)

PROBE_KEY = "zec.shielded_probe"
CAP_PROBE_KEY = "zec.cap_probe"
ZEC_CAP_KEY = "zec.market_cap_usd"
CRYPTO_CAP_KEY = "crypto.total_market_cap_usd"
SHIELDED_SHARE_KEY = "zec.shielded_tx_share"
PRICE_KEY = "zec.price_usd"
REALIZED_VOL_KEY = "zec.realized_vol_20d"
BETA_BTC_KEY = "zec.beta_to_btc_60d"
BTC_RATIO_KEY = "zec.btc_ratio"
CRYPTO_CAP_SHARE_KEY = "zec.crypto_cap_share"

BTC_SERIES = "yfinance.mkt_btc_usd"
ZEC_SYMBOL = "ZEC-USD"

EXPLORERS = (
    # THE ONE THAT ANSWERS. zcashd's own blockchain-info, proxied: it publishes
    # `valuePools`, the balance of every shielded pool, which is what makes the
    # value share below computable.
    ("zcashexplorer", "https://mainnet.zcashexplorer.app/api/v1/blockchain-info"),
    ("blockchair", "https://api.blockchair.com/zcash/stats"),
    ("zcashblockexplorer", "https://api.zcashblockexplorer.com/status"),
    ("zcha.in", "https://api.zcha.in/v2/mainnet/network"),
    ("messari", "https://data.messari.io/api/v1/assets/zec/metrics"),
    # Added on the ruling, and neither resolves: no DNS for either host.
    ("zechub", "https://api.zechub.xyz/api/v1/shielded"),
    ("zcash_foundation", "https://api.zfnd.org/metrics"),
)

VALUE_POOLS_URL = "https://mainnet.zcashexplorer.app/api/v1/blockchain-info"
POOL_VALUE_KEY = "zec.pool_value"
SHIELDED_VALUE_SHARE_KEY = "zec.shielded_value_share"

# WHICH POOLS COUNT AS USER-SHIELDED, declared rather than inferred from "not
# transparent". The chain has six pools and only three of them are a user choosing
# privacy:
#
#   sprout, sapling, orchard  -- the three shielded protocol versions. A balance here
#                                is someone's shielded note.
#   transparent               -- not shielded, by definition.
#   lockbox                   -- the NU6 development-fund reserve. Protocol-level, not
#                                a user's privacy decision, and counting it would
#                                credit the protocol's own accounting to user demand.
#   ironwood                  -- 3.99M ZEC, nearly a quarter of supply, and I have NOT
#                                verified what it holds. It is logged as its own
#                                series and EXCLUDED from the share, because a number
#                                that large moving the headline on a guess is worse
#                                than a narrower number that is defensible.
#
# Including lockbox and ironwood would read 29.4 percent; the three documented
# shielded pools read 5.4. The difference is the whole reason this list is explicit.
USER_SHIELDED_POOLS = ("sprout", "sapling", "orchard")
EXCLUDED_FROM_SHARE = {
    "transparent": "not shielded by definition",
    "lockbox": "the NU6 development-fund reserve -- protocol accounting, not a user's "
               "privacy decision",
    "ironwood": "semantics not verified; 3.99M ZEC is too large to fold into a "
                "headline on a guess",
}

# COINGECKO, public and keyless. Probed before use: the ruling said to stop and ask
# if it needed a key, and it does not -- /global and simple/price both answer 200
# anonymously.
COINGECKO_GLOBAL = "https://api.coingecko.com/api/v3/global"
COINGECKO_ZEC = ("https://api.coingecko.com/api/v3/simple/price"
                 "?ids=zcash&vs_currencies=usd&include_market_cap=true")

UA = {"User-Agent": "chester-reports/1.0 (research logging)"}
TIMEOUT = 25
VOL_WINDOW = 20
BETA_WINDOW = 60
MIN_HISTORY = 60
TRADING_DAYS_YEAR = 365      # ZEC trades every day, unlike the equity basket


def _get(url: str, limit: int = 400_000) -> bytes:
    """One HTTP read. Named here because three functions in this module needed it and
    two of them were reaching for a helper that lived in a sibling logger -- which
    failed at call time, not at import, so nothing caught it until the pool reader ran.
    """
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read(limit)


def probe(store: Optional[observations.ObservationStore] = None) -> dict:
    """Ask every candidate explorer and record all the answers, not just the first."""
    out: dict[str, Any] = {"checked_at": session.utc_iso(), "candidates": {},
                           "state": "unknown"}
    found = None
    for name, url in EXPLORERS:
        entry: dict[str, Any] = {"url": url}
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=UA), timeout=TIMEOUT) as r:
                body = r.read(400_000).decode("utf-8", "replace")
            entry["http"] = r.status
            try:
                data = json.loads(body)
            except Exception:                                  # noqa: BLE001
                data = {}
            flat = data.get("data") if isinstance(data.get("data"), dict) else data
            fields = sorted(flat) if isinstance(flat, dict) else []
            entry["fields"] = len(fields)
            # A field that is actually about the shielded pool -- not a mempool
            # counter that happens to contain the substring.
            shielded = [f for f in fields
                        if ("shield" in f.lower() or "sapling" in f.lower()
                            or "orchard" in f.lower())
                        and "mempool" not in f.lower()]
            entry["shielded_fields"] = shielded
            if shielded:
                found = (name, shielded)
        except urllib.error.HTTPError as exc:
            entry["http"] = exc.code
        except Exception as exc:                               # noqa: BLE001
            entry["error"] = f"{type(exc).__name__}: {str(exc)[:120]}"
        out["candidates"][name] = entry

    if found:
        out["state"] = "available"
        out["source"] = found[0]
        out["shielded_fields"] = found[1]
    else:
        out["state"] = "no_shielded_field"
        out["reason"] = ("every reachable explorer answers without a "
                         "shielded/unshielded split; the fields whose names "
                         "contain 'shield' are mempool counters. The shielded-pool "
                         "transaction share has no reachable source today.")
    own = store is None
    db = store or observations.ObservationStore()
    try:
        db.write(PROBE_KEY, None, session.session_date(),
                 session.utc_iso(timespec="microseconds"),
                 json.dumps(out, sort_keys=True), source="blockchair",
                 availability_kind="ingest_instant")
    finally:
        if own:
            db.close()
    return out


def probe_cap(store: Optional[observations.ObservationStore] = None) -> dict:
    """Total crypto capitalisation and ZEC's, from CoinGecko. Keyless.

    THE ONE THING TO KNOW ABOUT THIS SERIES: it is POINT-IN-TIME and cannot be
    backfilled. CoinGecko's free tier serves the CURRENT total capitalisation and no
    history of it, so `crypto.total_market_cap_usd` and the share derived from it
    start today and grow forward. That is what a forward-only logger is, and it is the
    reason this was worth starting tonight rather than after a data purchase.
    """
    out: dict[str, Any] = {"checked_at": session.utc_iso(), "state": "unknown",
                           "needs_key": False}
    try:
        g = json.loads(_get(COINGECKO_GLOBAL).decode("utf-8", "replace"))
        total = ((g.get("data") or {}).get("total_market_cap") or {}).get("usd")
        out["total_market_cap_usd"] = total
    except urllib.error.HTTPError as exc:
        out["state"] = "http_error"
        out["reason"] = f"/global returned HTTP {exc.code}"
        # 401/403 is what a key requirement looks like, and the ruling says stop.
        out["needs_key"] = exc.code in (401, 403)
        total = None
    except Exception as exc:                                   # noqa: BLE001
        out["state"] = "error"
        out["reason"] = f"{type(exc).__name__}: {str(exc)[:120]}"
        total = None

    zec_cap = None
    try:
        z = json.loads(_get(COINGECKO_ZEC).decode("utf-8", "replace"))
        zec_cap = (z.get("zcash") or {}).get("usd_market_cap")
        out["zec_market_cap_usd"] = zec_cap
        out["zec_price_usd"] = (z.get("zcash") or {}).get("usd")
    except urllib.error.HTTPError as exc:
        out.setdefault("reason", f"simple/price returned HTTP {exc.code}")
        out["needs_key"] = out["needs_key"] or exc.code in (401, 403)
    except Exception as exc:                                   # noqa: BLE001
        out.setdefault("reason", f"{type(exc).__name__}: {str(exc)[:120]}")

    if total and zec_cap:
        out["state"] = "available"
        out["share"] = round(zec_cap / total, 10)
    elif out["state"] == "unknown":
        out["state"] = "partial"
        out["reason"] = out.get("reason", "one of the two endpoints returned no "
                                          "capitalisation")
    own = store is None
    db = store or observations.ObservationStore()
    try:
        db.write(CAP_PROBE_KEY, None, session.session_date(),
                 session.utc_iso(timespec="microseconds"),
                 json.dumps(out, sort_keys=True, default=str),
                 source="coingecko", availability_kind="ingest_instant")
    finally:
        if own:
            db.close()
    return out


def read_value_pools() -> dict:
    """Every pool's balance, and the share held in the DOCUMENTED shielded pools.

    THIS IS A STOCK, NOT A FLOW, and the distinction is the same one that separates
    short interest from short volume. `valuePools` reports the ZEC currently sitting
    in each pool -- a balance. The order asked for the shielded TRANSACTION share,
    which is how much of today's activity used a shielded pool, and that is a
    different measurement this endpoint does not serve.

    So this is `zec.shielded_value_share` and `zec.shielded_tx_share` stays registered
    and empty. Calling a value share a transaction share would be the proxy-under-the-
    wrong-label error, on a number where the two genuinely differ: a chain can have a
    third of its supply shielded and almost no shielded activity, or the reverse.
    """
    out: dict[str, Any] = {"checked_at": session.utc_iso(), "state": "unknown"}
    try:
        d = json.loads(_get(VALUE_POOLS_URL).decode("utf-8", "replace"))
    except Exception as exc:                                   # noqa: BLE001
        out["state"] = "error"
        out["reason"] = f"{type(exc).__name__}: {str(exc)[:140]}"
        return out
    supply = ((d.get("chainSupply") or {}).get("chainValue"))
    pools = {str(p.get("id")): p.get("chainValue")
             for p in (d.get("valuePools") or [])
             if p.get("id") is not None and p.get("chainValue") is not None}
    if not supply or not pools:
        out["state"] = "no_pools"
        out["reason"] = "the endpoint answered without chainSupply or valuePools"
        return out
    shielded = sum(v for k, v in pools.items() if k in USER_SHIELDED_POOLS)
    unknown = sorted(set(pools) - set(USER_SHIELDED_POOLS) - set(EXCLUDED_FROM_SHARE))
    out.update({
        "state": "available",
        "chain_supply": supply,
        "pools": pools,
        "user_shielded_pools": list(USER_SHIELDED_POOLS),
        "excluded": EXCLUDED_FROM_SHARE,
        "shielded_value": shielded,
        "shielded_value_share": round(shielded / supply, 8),
        "blocks": d.get("blocks"),
        # A POOL THIS CODE HAS NEVER SEEN is a finding, not a silent zero: the chain
        # gains pools at network upgrades, and one appearing unclassified should reach
        # a human rather than being averaged in or quietly dropped.
        "unclassified_pools": unknown,
    })
    return out


def _zec_closes() -> list[tuple[str, float]]:
    from ..sources import yfinance_source as yf_src
    parsed = yf_src._fetch_symbol(ZEC_SYMBOL, period="2y")     # noqa: SLF001
    # ZEC trades every day, so the session filter must not touch it -- the same
    # declaration BTC gets in the price basket.
    return parsed["closes"]


def pull(run_id: Optional[str] = None,
         store: Optional[observations.ObservationStore] = None) -> dict:
    """The market series, logged whatever the explorer probe said."""
    own = store is None
    db = store or observations.ObservationStore()
    out: dict[str, Any] = {}
    try:
        # THE PROBE RUNS EVERY NIGHT, cheaply, because an explorer that gains the
        # field is the event this logger is waiting for and nobody will re-check by
        # hand.
        p = probe(store=db)
        out["probe"] = {"state": p["state"], "reason": p.get("reason")}
        out["shielded_share"] = {
            "state": "absent",
            "reason": p.get("reason", "no source"),
        } if p["state"] != "available" else {"state": "available"}

        try:
            closes = _zec_closes()
        except Exception as exc:                               # noqa: BLE001
            out["market"] = {"state": "error",
                             "reason": f"{type(exc).__name__}: {exc}"}
            out["written"] = 0
            return out

        now = session.utc_iso(timespec="microseconds")
        rows = [{"registry_key": PRICE_KEY, "instrument": None,
                 "observed_at": d, "available_at": now, "value": v,
                 "source": "yfinance", "run_id": run_id,
                 "availability_kind": "ingest_instant"}
                for d, v in closes]

        # Realized volatility, annualised on a 365-day year: ZEC trades daily.
        by_day = dict(closes)
        days = sorted(by_day)
        for i in range(VOL_WINDOW, len(days)):
            window = days[i - VOL_WINDOW:i + 1]
            rets = []
            for a, b in zip(window, window[1:]):
                pa, pb = by_day[a], by_day[b]
                if pa > 0 and pb > 0:
                    rets.append(math.log(pb / pa))
            if len(rets) >= 2:
                sd = statistics.stdev(rets)
                rows.append({"registry_key": REALIZED_VOL_KEY, "instrument": None,
                             "observed_at": days[i], "available_at": now,
                             "value": round(100.0 * sd * math.sqrt(
                                 TRADING_DAYS_YEAR), 6),
                             "source": "calc", "run_id": run_id,
                             "availability_kind": "ingest_instant"})

        # Beta to BTC, and the ratio -- which is NOT a share of crypto cap.
        btc = {str(r["observed_at"])[:10]: r["value_num"]
               for r in db.as_of(BTC_SERIES) if r["value_num"]}
        common = [d for d in days if d in btc]
        for d in common:
            if btc[d]:
                rows.append({"registry_key": BTC_RATIO_KEY, "instrument": None,
                             "observed_at": d, "available_at": now,
                             "value": round(by_day[d] / btc[d], 10),
                             "source": "calc", "run_id": run_id,
                             "availability_kind": "ingest_instant"})
        for i in range(BETA_WINDOW, len(common)):
            window = common[i - BETA_WINDOW:i + 1]
            zr, br = [], []
            for a, b in zip(window, window[1:]):
                if by_day[a] > 0 and by_day[b] > 0 and btc[a] > 0 and btc[b] > 0:
                    zr.append(math.log(by_day[b] / by_day[a]))
                    br.append(math.log(btc[b] / btc[a]))
            if len(zr) >= 10:
                try:
                    var = statistics.variance(br)
                except statistics.StatisticsError:
                    continue
                if var <= 0:
                    continue
                mz, mb = statistics.fmean(zr), statistics.fmean(br)
                cov = sum((x - mz) * (y - mb) for x, y in zip(zr, br)) / (len(zr) - 1)
                rows.append({"registry_key": BETA_BTC_KEY, "instrument": None,
                             "observed_at": common[i], "available_at": now,
                             "value": round(cov / var, 6), "source": "calc",
                             "run_id": run_id,
                             "availability_kind": "ingest_instant"})

        written = db.write_many(observations.drop_unchanged(db, rows))
        out["market"] = {"state": "ok", "closes": len(closes),
                         "btc_overlap": len(common),
                         "last": closes[-1] if closes else None}
        # THE VALUE POOLS, which the ruling's extra candidates led to.
        vp = read_value_pools()
        out["value_pools"] = {k: vp.get(k) for k in
                              ("state", "shielded_value_share",
                               "unclassified_pools", "reason")}
        if vp.get("state") == "available":
            day = session.session_date()
            stamp = session.utc_iso(timespec="microseconds")
            pool_rows = [
                {"registry_key": POOL_VALUE_KEY, "instrument": pool,
                 "observed_at": day, "available_at": stamp, "value": float(val),
                 "source": "zcashexplorer", "run_id": run_id,
                 "availability_kind": "ingest_instant"}
                for pool, val in (vp.get("pools") or {}).items()]
            pool_rows.append(
                {"registry_key": SHIELDED_VALUE_SHARE_KEY, "instrument": None,
                 "observed_at": day, "available_at": stamp,
                 "value": float(vp["shielded_value_share"]), "source": "calc",
                 "run_id": run_id, "availability_kind": "ingest_instant"})
            written += db.write_many(observations.drop_unchanged(db, pool_rows))
            if vp.get("unclassified_pools"):
                log.warning("zec: UNCLASSIFIED value pool(s) %s -- decide whether "
                            "they are user-shielded before the share can include "
                            "them", vp["unclassified_pools"])

        # THE CAP SHARE, WHICH NOW HAS A SOURCE. CoinGecko is keyless, so the
        # ruling's "stop and tell me" branch does not fire.
        cap = probe_cap(store=db)
        out["crypto_cap_share"] = {"state": cap["state"],
                                   "share": cap.get("share"),
                                   "reason": cap.get("reason")}
        if cap["state"] == "available":
            day = session.session_date()
            stamp = session.utc_iso(timespec="microseconds")
            cap_rows = [
                {"registry_key": CRYPTO_CAP_KEY, "instrument": None,
                 "observed_at": day, "available_at": stamp,
                 "value": float(cap["total_market_cap_usd"]),
                 "source": "coingecko", "run_id": run_id,
                 "availability_kind": "ingest_instant"},
                {"registry_key": ZEC_CAP_KEY, "instrument": None,
                 "observed_at": day, "available_at": stamp,
                 "value": float(cap["zec_market_cap_usd"]),
                 "source": "coingecko", "run_id": run_id,
                 "availability_kind": "ingest_instant"},
                {"registry_key": CRYPTO_CAP_SHARE_KEY, "instrument": None,
                 "observed_at": day, "available_at": stamp,
                 "value": float(cap["share"]), "source": "calc",
                 "run_id": run_id, "availability_kind": "ingest_instant"},
            ]
            written += db.write_many(observations.drop_unchanged(db, cap_rows))
        out["written"] = written
        return out
    finally:
        if own:
            db.close()


def keys() -> list[str]:
    # The shielded share is NOT in the roster: there is no source, so a roster entry
    # would make the heartbeat red for a capability gap rather than for a fault. The
    # cap series IS watched -- it has a working keyless source, so its absence would
    # be a fault.
    return [PRICE_KEY, REALIZED_VOL_KEY, BTC_RATIO_KEY,
            CRYPTO_CAP_KEY, ZEC_CAP_KEY, CRYPTO_CAP_SHARE_KEY,
            POOL_VALUE_KEY, SHIELDED_VALUE_SHARE_KEY]


SPEC = register(LoggerSpec(
    name="shielded_zec",
    description="ZEC price, realized volatility, BTC beta and ratio, nightly. The "
                "shielded-pool share has no reachable source; the probe is stored.",
    keys=keys,
    run=pull,
    requires_key=None,
    min_history=MIN_HISTORY,
    notes="Part 29.5 logging only. No theme block, no privacy-coin analysis -- 6h.",
))


def _main(argv: list[str]) -> int:
    import argparse
    p = argparse.ArgumentParser(description="Zcash / ZEC logger.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe")
    sub.add_parser("pull")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps({"probe": probe, "pull": pull}[a.cmd](), indent=2,
                     sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
