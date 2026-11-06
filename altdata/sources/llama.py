"""
DefiLlama -- the `llama.*` family (DS-29; CD-1 of the crypto data-sources order,
pulled forward by the crypto basket brief of 12 Oct 2026, decision 7).

    python -m altdata.sources.llama pull                 # everything below
    python -m altdata.sources.llama pull --only basket   # the basket's protocols
    python -m altdata.sources.llama pull --only coins    # caps and supply
    python -m altdata.sources.llama pull --only macro    # stablecoins, chains, DEX, OI
    python -m altdata.sources.llama pull --only watch    # the watch names' fees
    python -m altdata.sources.llama pull --dry-run       # fetch and parse, write nothing
    python -m altdata.sources.llama resolve              # the basket's slugs, from /protocols

Open REST API, no key (docs/change-order-crypto-data-sources-2026-10-06.md,
Appendix A). DefiLlama's terms (defillama.com/terms, effective 24 Jun 2025) allow
the official public API for personal, non-commercial use and forbid republishing
the data without permission; the reports are the operator's own. Neither API host
publishes a robots.txt rule.

WHAT IS PULLED
  per basket protocol   llama.fees_<sym>, llama.revenue_<sym>,
                        llama.holders_revenue_<sym>  (/summary/fees/{slug},
                        dataType dailyFees / dailyRevenue / dailyHoldersRevenue)
                        llama.tvl_<sym>               (/protocol/{slug})
  per basket coin       llama.mcap_<sym>, llama.supply_<sym>
                        (coins.llama.fi /mcaps and /prices/current; supply is the
                        cap over the service's own price at the same instant)
  S-1                   llama.stable_total (all chains, full history),
                        llama.stable_by_chain (instrument = the chain)
  chains                llama.chain_tvl (instrument = the chain; NULL = all)
  DEX volume            llama.dex_volume (/overview/dexs, daily total)
  perps                 llama.perps_oi (/overview/open-interest, daily total)

  per watch name        llama.fees_<sym>, llama.revenue_<sym> for the order's watch
                        names that are not basket names (BTC, ETH, SOL, ZEC, HYPE,
                        LINK; config/crypto_sources.yaml). The slug is RESOLVED AT
                        RUN TIME, never written down: a chain from /overview/fees
                        (protocolType "chain", by name), a protocol as the parent
                        its /protocols rows share (by symbol). Tranche A part 1,
                        crypto-tranche-a-1, 17 Oct 2026.
  per watch coin        llama.mcap_btc, llama.mcap_eth (and supply), the S-3
                        denominator, forward-only like the basket's caps

NOT SERVED FREE, and so not pulled: `/raises` ("Upgrade to the paid API plan",
probed 13 Oct 2026, and again 17 Oct 2026: HTTP 402) and `/emissions` (Pro, as the
order recorded). DS-21's unlock schedules stay by hand.

POINT-IN-TIME (ST-13's conventions, as altdata/sources/yfinance_source.py writes
them): observed_at is the UTC day the figure describes; available_at is the pull
instant, availability_kind `ingest_instant`, never backdated -- DefiLlama's
adapters refill history, so a backfilled row is NOT `reconstructed`. A day is
written only once it has ended in UTC: the last point of a TVL chart is an
intraday snapshot and is held back. A re-read of an unchanged value writes
nothing (observations.drop_unchanged).
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import time
from pathlib import Path
from typing import Any, Callable, Optional

from ._base import FetchError, http_get_json

log = logging.getLogger(__name__)

API = "https://api.llama.fi"
STABLES = "https://stablecoins.llama.fi"
COINS = "https://coins.llama.fi"
SOURCE = "defillama"
FAMILY = "llama"
REPO = Path(__file__).resolve().parents[2]
BASKET_PATH = REPO / "config" / "crypto_basket.yaml"

# S-1's chains (the order: Ethereum, Tron, Solana, Base), and the same four for
# chain TVL beside the all-chains total.
STABLE_CHAINS = ("Ethereum", "Tron", "Solana", "Base")
TVL_CHAINS = ("Ethereum", "Tron", "Solana", "Base")
FEE_TYPES = {"fees": "dailyFees", "revenue": "dailyRevenue",
             "holders_revenue": "dailyHoldersRevenue"}
NOT_SERVED = {
    "raises": "DefiLlama /raises answers 'Upgrade to the paid API plan' (probed 13 Oct 2026)",
    "emissions": "DefiLlama /emissions is Pro-only (the order's Appendix A)",
}


# ---------------------------------------------------------------------------
# The basket, from config
# ---------------------------------------------------------------------------
def basket(path: Optional[Path] = None) -> dict:
    import yaml  # noqa: PLC0415
    return (yaml.safe_load((path or BASKET_PATH).read_text(encoding="utf-8"))
            or {}).get("names") or {}


def protocol_keys(path: Optional[Path] = None) -> list[str]:
    """Every llama.* protocol series the basket declares: the kinds its
    `llama_series` lists, which are the ones DefiLlama serves for that slug."""
    out = []
    for sym, n in basket(path).items():
        if n.get("llama_slug"):
            out += [f"{kind}_{sym.lower()}" for kind in n.get("llama_series") or []]
    return out


def coin_keys(path: Optional[Path] = None) -> list[str]:
    out = []
    for sym, n in basket(path).items():
        if n.get("llama_coin"):
            out += [f"mcap_{sym.lower()}", f"supply_{sym.lower()}"]
    return out


def watch(path: Optional[Path] = None) -> dict:
    """config/crypto_sources.yaml: the watch names and coins (CD-1, Tranche A)."""
    import yaml  # noqa: PLC0415
    p = path or (REPO / "config" / "crypto_sources.yaml")
    cfg = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {"names": cfg.get("watch_names") or [], "coins": cfg.get("watch_coins") or []}


def watch_keys(path: Optional[Path] = None) -> list[str]:
    return [f"{kind}_{n['sym'].lower()}" for n in watch(path)["names"]
            for kind in n.get("series") or []]


MACRO_KEYS = ["stable_total", "stable_by_chain", "chain_tvl", "dex_volume",
              "perps_oi"]
# The registry's bulk blocks read these (member names; key_prefix `llama.`).
PROTOCOL_KEYS = protocol_keys()
WATCH_KEYS = watch_keys()
COIN_KEYS = coin_keys() + [f"{k}_{c['sym'].lower()}" for c in watch()["coins"]
                           for k in ("mcap", "supply")]
MCAP_KEYS = [k for k in COIN_KEYS if k.startswith("mcap_")]
SUPPLY_KEYS = [k for k in COIN_KEYS if k.startswith("supply_")]


# ---------------------------------------------------------------------------
# Parsers -- pure, fixture-tested (tests/fixtures/llama/)
# ---------------------------------------------------------------------------
def _day(ts: Any) -> str:
    return dt.datetime.fromtimestamp(int(float(ts)), dt.timezone.utc).date().isoformat()


def _complete(day: str, today: str) -> bool:
    """A UTC day is written only once it has ended."""
    return day < today


def _num(v: Any) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f


def parse_chart(d: dict, today: str) -> list[tuple[str, float]]:
    """/summary/fees and /overview/*: totalDataChart [[ts, value], ...]."""
    out: dict[str, float] = {}
    for pt in (d or {}).get("totalDataChart") or []:
        if not isinstance(pt, (list, tuple)) or len(pt) < 2:
            continue
        v = _num(pt[1])
        day = _day(pt[0])
        if v is not None and _complete(day, today):
            out[day] = v
    return sorted(out.items())


def parse_protocol_tvl(d: dict, today: str) -> list[tuple[str, float]]:
    """/protocol/{slug}: tvl [{date, totalLiquidityUSD}]; the last point of a
    day stands for it, and today's intraday snapshot is held back."""
    out: dict[str, float] = {}
    for pt in (d or {}).get("tvl") or []:
        v = _num(pt.get("totalLiquidityUSD"))
        day = _day(pt.get("date"))
        if v is not None and _complete(day, today):
            out[day] = v
    return sorted(out.items())


def parse_stable_chart(rows: list, today: str) -> list[tuple[str, float]]:
    """stablecoincharts/{all|chain}: the dollar-pegged circulating supply, USD."""
    out: dict[str, float] = {}
    for r in rows or []:
        v = _num(((r or {}).get("totalCirculatingUSD") or {}).get("peggedUSD"))
        day = _day(r.get("date"))
        if v is not None and _complete(day, today):
            out[day] = v
    return sorted(out.items())


def parse_chain_tvl(rows: list, today: str) -> list[tuple[str, float]]:
    out: dict[str, float] = {}
    for r in rows or []:
        v = _num((r or {}).get("tvl"))
        day = _day(r.get("date"))
        if v is not None and _complete(day, today):
            out[day] = v
    return sorted(out.items())


def parse_coins(mcaps: dict, prices: dict) -> dict[str, dict]:
    """coin id -> {day, mcap, price, supply}. The cap and the price come from the
    same service; supply = cap / price, and only when both are stamped within an
    hour of each other (otherwise supply is not computed rather than mixed)."""
    out: dict[str, dict] = {}
    pr = (prices or {}).get("coins") or {}
    for coin, m in (mcaps or {}).items():
        cap = _num((m or {}).get("mcap"))
        ts = (m or {}).get("timestamp")
        if cap is None or ts is None:
            continue
        p = pr.get(coin) or {}
        price, pts = _num(p.get("price")), p.get("timestamp")
        supply = None
        if price and pts is not None and abs(int(pts) - int(ts)) <= 3600:
            supply = cap / price
        out[coin] = {"day": _day(ts), "mcap": cap, "price": price,
                     "supply": supply, "timestamp": int(ts)}
    return out


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------
def resolve_watch(names: list[dict], protocols: list, fees_overview: dict
                  ) -> dict[str, tuple[Optional[str], str]]:
    """sym -> (slug, how), or (None, why). A chain is the /overview/fees row of
    protocolType "chain" named `match`; a protocol is the one parent shared by the
    /protocols rows whose symbol is `match`. Two parents, or none: no slug."""
    out: dict[str, tuple[Optional[str], str]] = {}
    rows = (fees_overview or {}).get("protocols") or []
    for n in names:
        sym, m = n["sym"], str(n.get("match") or n["sym"])
        if n.get("kind") == "chain":
            hit = sorted({str(r.get("slug")) for r in rows
                          if r.get("protocolType") == "chain" and r.get("slug")
                          and str(r.get("name") or "").lower() == m.lower()})
            out[sym] = ((hit[0], f"chain row '{m}'") if len(hit) == 1 else
                        (None, f"{len(hit)} chain slugs named {m} in /overview/fees"
                               + (f": {', '.join(hit)}" if hit else "")))
            continue
        parents = sorted({str(p.get("parentProtocol"))
                          for p in protocols or []
                          if str(p.get("symbol") or "").upper() == m.upper()
                          and str(p.get("parentProtocol") or "").startswith("parent#")})
        out[sym] = ((parents[0].split("#", 1)[1], f"parent of the {m} rows")
                    if len(parents) == 1 else
                    (None, f"{len(parents)} parents among /protocols rows of symbol {m}"
                           + (f": {', '.join(parents)}" if parents else "")))
    return out


def _get(url: str, params: Optional[dict] = None) -> Any:
    return http_get_json(url, params=params, timeout=120)


def _post_json(url: str, body: dict, retries: int = 3) -> Any:
    import requests  # noqa: PLC0415
    last: Optional[Exception] = None
    for i in range(retries):
        try:
            r = requests.post(url, json=body, timeout=60)
            if 400 <= r.status_code < 500:
                raise FetchError(f"HTTP {r.status_code} from {url}: {r.text[:200]}")
            r.raise_for_status()
            return r.json()
        except FetchError:
            raise
        except Exception as exc:                              # noqa: BLE001
            last = exc
            time.sleep(2 * (i + 1))
    raise FetchError(f"{url}: {type(last).__name__}: {last}")


def _today() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _rows(key: str, points: list[tuple[str, float]], now: str,
          instrument: Optional[str] = None, run_id: Optional[str] = None) -> list[dict]:
    return [{"registry_key": f"{FAMILY}.{key}", "instrument": instrument,
             "observed_at": d, "available_at": now, "value": v,
             "source": SOURCE, "run_id": run_id,
             "availability_kind": "ingest_instant"} for d, v in points]


def collect(only: Optional[str] = None, fetch: Callable[..., Any] = _get,
            post: Callable[..., Any] = _post_json, today: Optional[str] = None,
            run_id: Optional[str] = None) -> tuple[list[dict], dict]:
    """(rows, summary). Each series isolated: one failure is named and the rest
    still land."""
    from .. import session as sess                          # noqa: PLC0415
    now = sess.utc_iso(timespec="microseconds")
    today = today or _today()
    rows: list[dict] = []
    summary: dict = {"series": {}, "failed": [], "not_served": dict(NOT_SERVED)}

    def take(key: str, pts: list, instrument: Optional[str] = None) -> None:
        rows.extend(_rows(key, pts, now, instrument, run_id))
        label = key + (f"[{instrument}]" if instrument else "")
        summary["series"][label] = {"rows": len(pts),
                                    "first": pts[0][0] if pts else None,
                                    "last": pts[-1][0] if pts else None}

    def guard(label: str, fn: Callable[[], None]) -> None:
        try:
            fn()
        except Exception as exc:                              # noqa: BLE001
            summary["failed"].append((label, f"{type(exc).__name__}: {exc}"[:240]))
            log.warning("llama: %s failed -- %s", label, exc)

    names = basket()
    if only in (None, "basket"):
        for sym, n in names.items():
            slug = n.get("llama_slug")
            if not slug:
                continue
            if n.get("llama_hold"):
                # HELD (the feed repair of 24 Oct 2026): nothing requested.
                summary.setdefault("held", {})[sym] = n["llama_hold"]
                continue
            s = sym.lower()
            served = set(n.get("llama_series") or [])
            # A labelled break (AERO, ruling D29.3): points from its date only,
            # so the history stored before it is never restated.
            since = str((n.get("llama_break") or {}).get("date") or "")
            if since:
                summary.setdefault("breaks", {})[sym] = since

            def cut(pts: list, since: str = since) -> list:
                return [p for p in pts if p[0] >= since] if since else pts
            for kind, dtype in FEE_TYPES.items():
                if kind not in served:
                    continue
                guard(f"{kind}_{s}", lambda kind=kind, dtype=dtype, slug=slug, s=s, cut=cut: take(
                    f"{kind}_{s}", cut(parse_chart(fetch(f"{API}/summary/fees/{slug}",
                                                         {"dataType": dtype}), today))))
            if "tvl" in served:
                guard(f"tvl_{s}", lambda slug=slug, s=s, cut=cut: take(
                    f"tvl_{s}", cut(parse_protocol_tvl(fetch(f"{API}/protocol/{slug}"),
                                                       today))))
    if only in (None, "watch"):
        def watch_names() -> None:
            w = watch()["names"]
            slugs = resolve_watch(w, fetch(f"{API}/protocols"),
                                  fetch(f"{API}/overview/fees",
                                        {"excludeTotalDataChart": "true",
                                         "excludeTotalDataChartBreakdown": "true",
                                         "dataType": "dailyFees"}))
            summary["watch_slugs"] = {k: v for k, v in slugs.items()}
            for n in w:
                s = n["sym"].lower()
                slug, how = slugs.get(n["sym"], (None, "not resolved"))
                if not slug:
                    summary["failed"].append((f"watch_{s}", how))
                    continue
                for kind in n.get("series") or []:
                    dtype = FEE_TYPES[kind]
                    guard(f"{kind}_{s}", lambda kind=kind, dtype=dtype, slug=slug, s=s: take(
                        f"{kind}_{s}", parse_chart(fetch(f"{API}/summary/fees/{slug}",
                                                         {"dataType": dtype}), today)))
        guard("watch", watch_names)
    if only in (None, "coins"):
        def coins() -> None:
            ids = {n["llama_coin"]: sym.lower() for sym, n in names.items()
                   if n.get("llama_coin")}
            ids.update({c["coin"]: c["sym"].lower() for c in watch()["coins"]})
            caps = post(f"{COINS}/mcaps", {"coins": sorted(ids)})
            prices = fetch(f"{COINS}/prices/current/{','.join(sorted(ids))}")
            parsed = parse_coins(caps, prices)
            for coin, s in ids.items():
                p = parsed.get(coin)
                if not p:
                    summary["failed"].append((f"mcap_{s}", "not in the coin service's answer"))
                    continue
                if not _complete(p["day"], today) and p["day"] != today:
                    continue
                take(f"mcap_{s}", [(p["day"], p["mcap"])])
                if p["supply"] is not None:
                    take(f"supply_{s}", [(p["day"], p["supply"])])
                else:
                    summary["failed"].append((f"supply_{s}", "cap and price not "
                                              "stamped within an hour; not computed"))
        guard("coins", coins)
    if only in (None, "macro"):
        guard("stable_total", lambda: take(
            "stable_total", parse_stable_chart(fetch(f"{STABLES}/stablecoincharts/all"), today)))
        for ch in STABLE_CHAINS:
            guard(f"stable_by_chain[{ch}]", lambda ch=ch: take(
                "stable_by_chain", parse_stable_chart(
                    fetch(f"{STABLES}/stablecoincharts/{ch}"), today), ch))
        guard("chain_tvl", lambda: take(
            "chain_tvl", parse_chain_tvl(fetch(f"{API}/v2/historicalChainTvl"), today)))
        for ch in TVL_CHAINS:
            guard(f"chain_tvl[{ch}]", lambda ch=ch: take(
                "chain_tvl", parse_chain_tvl(
                    fetch(f"{API}/v2/historicalChainTvl/{ch}"), today), ch))
        guard("dex_volume", lambda: take("dex_volume", parse_chart(fetch(
            f"{API}/overview/dexs", {"excludeTotalDataChartBreakdown": "true"}), today)))
        guard("perps_oi", lambda: take("perps_oi", parse_chart(fetch(
            f"{API}/overview/open-interest",
            {"excludeTotalDataChartBreakdown": "true"}), today)))
    return rows, summary


def pull(only: Optional[str] = None, dry_run: bool = False, store: Any = None,
         run_id: Optional[str] = None, **kw) -> dict:
    """Fetch, parse and write; returns the summary with `written`."""
    from .. import observations as obs                      # noqa: PLC0415
    rows, summary = collect(only=only, run_id=run_id, **kw)
    summary["computed"] = len(rows)
    if dry_run:
        summary["written"] = 0
        return summary
    own = store is None
    db = store or obs.open_writer(__name__)
    try:
        fresh = obs.drop_unchanged(db, rows)
        summary["written"] = db.write_many(fresh)
        summary["unchanged"] = len(rows) - len(fresh)
    finally:
        if own:
            db.close()
    # S-1's derived series, from what is now stored.
    if only in (None, "macro"):
        from .. import crypto_basket                         # noqa: PLC0415
        summary["derived"] = crypto_basket.write_stable_impulse(store=store)
        # S-1's share by chain (and S-3 from what the venues have stored), the
        # derived writer of Tranche A part 1.
        from . import crypto_derived                           # noqa: PLC0415
        summary["derived_tranche_a"] = crypto_derived.pull(db=store).get("written")
    return summary


def resolve(protocols: Optional[list] = None) -> list[dict]:
    """Each basket name against /protocols: the declared slug, and every listed
    protocol whose symbol or gecko id matches -- so a wrong slug is visible."""
    P = protocols if protocols is not None else _get(f"{API}/protocols")
    out = []
    for sym, n in basket().items():
        gid = (n.get("llama_coin") or "").split(":", 1)[-1]
        hits = [p for p in P if (p.get("symbol") or "").upper() == sym
                or (gid and p.get("gecko_id") == gid)]
        out.append({"symbol": sym, "declared": n.get("llama_slug"),
                    "candidates": [(p.get("slug"), p.get("name"), p.get("gecko_id"),
                                    p.get("parentProtocol")) for p in hits]})
    return out


def _main(argv: list[str]) -> int:
    import argparse  # noqa: PLC0415
    import sys  # noqa: PLC0415
    ap = argparse.ArgumentParser(description="DefiLlama, the llama.* family.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull")
    p.add_argument("--only", choices=("basket", "coins", "macro", "watch"),
                   default=None)
    p.add_argument("--dry-run", action="store_true")
    sub.add_parser("resolve")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if a.cmd == "resolve":
        for r in resolve():
            print(f"{r['symbol']:<7} declared {r['declared']!s:<14} candidates "
                  + "; ".join(f"{c[0]} ({c[1]}, gecko {c[2]}, {c[3] or 'top-level'})"
                              for c in r["candidates"][:6]))
        return 0
    s = pull(only=a.only, dry_run=a.dry_run)
    for k, v in sorted(s["series"].items()):
        print(f"  {k:<32} {v['rows']:>6} rows  {v['first']} .. {v['last']}")
    for k, why in s["failed"]:
        print(f"  FAILED {k}: {why}")
    for k, why in s["not_served"].items():
        print(f"  not served: {k} -- {why}")
    print(f"llama: {s['computed']} row(s) computed, {s['written']} written"
          + ("  (dry run)" if a.dry_run else ""))
    return 1 if s["failed"] and not s["series"] else 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
