"""
The two-bid decomposition, the parts that can start now (AQ-8a; change order
"Alternative Assets Quarterly", 10 Oct 2026, section 5 row "Two-bid
decomposition"; arch Session 12; I 4.1, 4.6; II S10).

    python -m altdata.paper_bid record --session 2026-10-12
    python -m altdata.paper_bid backfill --days 60 [--dry-run]
    python -m altdata.paper_bid show [--as-of ...]

THE PAPER BID, per symbol of altdata.config.PAPER_BID_SYMBOLS (GLD, SLV, IBIT,
USO -- the four the Part 9 ruling named), from each session's close-nearest
captured chain, the capture exposure_compute reads for the SPY exposure fields
and by the same Black-Scholes delta from the chain's own IV:

  calc.paper_bid.<symbol>.net_call_put_oi   call OI less put OI, contracts, over
                                            every expiry after the session's own
  calc.paper_bid.<symbol>.rr_25d            the 25-delta risk reversal at 30
                                            days, in vol points (call IV less
                                            put IV; positive = calls bid)

THE OFFICIAL BID reads China's reported holdings (safe.gold_reserves_oz) now;
the IMF IFS series is not_yet_sourced, a ruling pending, and nothing here writes
it. GLD's tonnage is a feeds-writer item for a later order.

THE TWO STATES -- fragile rally (paper surging, official flat) and durable base
(official accumulating, paper absent) -- print only when both legs hold twelve
months of history; until then the block says which leg is waiting. The numbers
behind "surging", "absent", "flat" and "accumulating" are session-set, in
config/attribution.yaml `two_bid`.

THE CLOCKS (chain_metrics' rule). observed_at is the session; available_at the
capture's own fetched_at -- a reading cannot be known before its chain was
captured. The EOD pass writes it after the capture (run_eod.py, stage 1c); the
backfill rebuilds it from captures on disk and is idempotent.
"""

from __future__ import annotations

import datetime as dt
import logging
import math
import sys
from pathlib import Path
from typing import Any, Optional

from . import config, observations

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
SOURCE = "paper_bid_chain"
PREFIX = "calc.paper_bid."


def oi_key(symbol: str) -> str:
    return f"{PREFIX}{symbol.lower()}.net_call_put_oi"


def rr_key(symbol: str) -> str:
    return f"{PREFIX}{symbol.lower()}.rr_25d"


# The registry's two bulk blocks read these (members_are: keys).
PAPER_OI_SERIES = {oi_key(s): f"{s} net call-put open interest"
                   for s in config.PAPER_BID_SYMBOLS}
PAPER_RR_SERIES = {rr_key(s): f"{s} 25-delta risk reversal, 30 days"
                   for s in config.PAPER_BID_SYMBOLS}


def cfg() -> dict:
    from . import attribution  # noqa: PLC0415
    return attribution.config().get("two_bid") or {}


def _ec():
    tools = str(REPO / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import exposure_compute                                      # noqa: PLC0415
    return exposure_compute


def chain_dir() -> Path:
    p = Path(config.CHAIN_DIR)
    return p if p.is_absolute() else REPO / p


# ---------------------------------------------------------------------------
# The readings
# ---------------------------------------------------------------------------
def net_call_put_oi(rows: list[dict]) -> Optional[dict]:
    """Call OI less put OI, over every expiry after the session's own."""
    calls = sum(r["open_interest"] or 0.0 for r in rows
                if r["right"] == "C" and (r.get("dte") or 0) >= 1)
    puts = sum(r["open_interest"] or 0.0 for r in rows
               if r["right"] == "P" and (r.get("dte") or 0) >= 1)
    if calls + puts <= 0:
        return None
    return {"net": calls - puts, "calls": calls, "puts": puts}


def _iv_at_delta(points: list[tuple[float, float]], target: float) -> Optional[float]:
    """IV at `target` delta, linear in delta between the two points either side."""
    pts = sorted(points)
    for (d0, v0), (d1, v1) in zip(pts, pts[1:]):
        if d0 <= target <= d1 and d1 > d0:
            return v0 + (target - d0) / (d1 - d0) * (v1 - v0)
    return None


def expiry_rr(rows: list[dict], spot: float, dte: int, r: float) -> Optional[float]:
    """One expiry's 25-delta risk reversal (call IV less put IV), in vol points."""
    ec = _ec()
    t = max(dte, 0) / 365.0
    calls, puts = [], []
    for x in rows:
        iv, k = x.get("implied_vol"), x.get("strike")
        if not (iv and k) or not 0 < iv < ec.MAX_SANE_IV:
            continue
        if not ((x.get("open_interest") or 0) > 0 or (x.get("bid") or 0) > 0):
            continue
        g = ec.bs_greeks(spot, k, iv, t, r, x["right"])
        if not g:
            continue
        (calls if x["right"] == "C" else puts).append((g["delta"], iv))
    c = _iv_at_delta(calls, 0.25)
    p = _iv_at_delta(puts, -0.25)
    return None if c is None or p is None else 100.0 * (c - p)


def rr_25d(rows: list[dict], target_days: float = 30.0, min_dte: int = 7,
           r: Optional[float] = None) -> Optional[dict]:
    """The 30-day 25-delta risk reversal: linear in days between the two expiries
    bracketing the target, the nearest where none does."""
    rate = config.RISK_FREE_RATE if r is None else r
    spot = next((x["spot"] for x in rows if x.get("spot")), None)
    if not spot:
        return None
    by: dict[str, list[dict]] = {}
    for x in rows:
        if (x.get("dte") or 0) >= min_dte:
            by.setdefault(x["expiry"], []).append(x)
    pts = []
    for exp, xs in by.items():
        v = expiry_rr(xs, spot, int(xs[0]["dte"]), rate)
        if v is not None:
            pts.append((int(xs[0]["dte"]), v, exp))
    if not pts:
        return None
    pts.sort()
    below = [p for p in pts if p[0] <= target_days]
    above = [p for p in pts if p[0] >= target_days]
    if below and above:
        (d1, v1, e1), (d2, v2, e2) = below[-1], above[0]
        if d1 == d2:
            return {"rr": v1, "method": "exact", "expiries": [e1]}
        w = (target_days - d1) / (d2 - d1)
        return {"rr": v1 + w * (v2 - v1), "method": "interpolated", "expiries": [e1, e2]}
    d, v, e = min(pts, key=lambda p: abs(p[0] - target_days))
    return {"rr": v, "method": "nearest", "expiries": [e]}


def readings(day: str, symbols: Optional[list[str]] = None,
             base: Optional[Path] = None) -> dict:
    """Each symbol's two readings from the session's close-nearest capture."""
    ec = _ec()
    c = cfg()
    syms = list(symbols or config.PAPER_BID_SYMBOLS)
    caps = ec.newest_chains(day, syms, str(base or chain_dir()))
    out: dict[str, Any] = {"session": day, "symbols": {}}
    for s in syms:
        path = caps.get(s)
        if not path:
            out["symbols"][s] = {"reason": "no chain captured for the session"}
            continue
        rows = ec.load_chain(path)
        if not rows:
            out["symbols"][s] = {"reason": f"{path.name} has no rows"}
            continue
        rec: dict[str, Any] = {"capture": path.name, "fetched_at": rows[0].get("fetched_at")}
        rec["net_call_put_oi"] = net_call_put_oi(rows)
        try:
            rec["rr_25d"] = rr_25d(rows, float(c.get("rr_target_days", 30)),
                                   int(c.get("rr_min_dte", 7)))
        except Exception as exc:                                 # noqa: BLE001
            rec["rr_25d"] = None
            rec["rr_reason"] = f"{type(exc).__name__}: {exc}"[:160]
        out["symbols"][s] = rec
    return out


def observation_rows(rd: dict) -> list[dict]:
    rows = []
    for s, rec in (rd.get("symbols") or {}).items():
        avail = rec.get("fetched_at")
        if not avail:
            continue
        oi = rec.get("net_call_put_oi")
        if oi:
            rows.append({"registry_key": oi_key(s), "instrument": None,
                         "observed_at": rd["session"], "available_at": avail,
                         "value": float(oi["net"]), "source": SOURCE,
                         "availability_kind": "observed"})
        rr = rec.get("rr_25d")
        if rr and math.isfinite(rr["rr"]):
            rows.append({"registry_key": rr_key(s), "instrument": None,
                         "observed_at": rd["session"], "available_at": avail,
                         "value": round(rr["rr"], 4), "source": SOURCE,
                         "availability_kind": "observed"})
    return rows


def record_session(day: str, store=None, base: Optional[Path] = None) -> dict:
    """Compute and store the session's paper-bid readings. Never raises."""
    try:
        rd = readings(day, base=base)
        rows = observation_rows(rd)
        if rows:
            own = store is None
            st = store or observations.ObservationStore()
            try:
                rows = observations.drop_unchanged(st, rows)
                st.write_many(rows)
            finally:
                if own:
                    st.close()
        rd["written"] = len(rows)
        return rd
    except Exception as exc:                                    # noqa: BLE001
        return {"session": day, "error": f"{type(exc).__name__}: {exc}"[:200]}


def backfill(days: int = 60, dry_run: bool = False, base: Optional[Path] = None,
             store=None) -> dict:
    """ONE-TIME: the readings for every session on disk in the last `days`
    calendar days. Idempotent: only a changed value is written."""
    root = base or chain_dir()
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    sessions = sorted(p.name for p in root.iterdir() if p.is_dir() and p.name >= since) \
        if root.is_dir() else []
    out = {"days": days, "dry_run": dry_run, "sessions": {}}
    own = store is None and not dry_run
    st = store or (None if dry_run else observations.ObservationStore())
    try:
        for d in sessions:
            rows = observation_rows(readings(d, base=root))
            if st is not None and rows:
                rows = observations.drop_unchanged(st, rows)
                if not dry_run:
                    st.write_many(rows)
            out["sessions"][d] = len(rows)
    finally:
        if own and st is not None:
            st.close()
    return out


# ---------------------------------------------------------------------------
# The two legs and the two states (read from the store)
# ---------------------------------------------------------------------------
def _rows(st, key: str, now: str) -> list[tuple[str, float]]:
    return sorted((str(r["observed_at"])[:10], float(r["value_num"]))
                  for r in st.as_of(key, now) if r.get("value_num") is not None)


def months_held(rows: list[tuple[str, float]]) -> int:
    """Distinct calendar months the series has printed in."""
    return len({d[:7] for d, _ in rows})


def _pct(vals: list[float], x: float) -> Optional[float]:
    from . import derived  # noqa: PLC0415
    return derived.percentile_of(vals, x)


# THE OFFICIAL LEG (post-Friday fix 2, ruled 16 Oct 2026): the IMF IFS writer's
# aggregate net purchases, a flow, in place of China's reported holdings
# (safe.gold_reserves_oz). config/attribution.yaml two_bid.official names it.
OFFICIAL_KEY = "imf.ifs.gold_net_purchases_oz.total"
OFFICIAL_LABEL = "central banks' net gold purchases (IMF IFS)"


def two_bid_state(st, now: str, c: Optional[dict] = None) -> dict:
    """Gold's two legs and, once both hold twelve months, the state: fragile
    rally, durable base, or neither (with why). Before then, which leg waits."""
    c = c or cfg()
    need = int(c.get("min_history_months", 12))
    sym = str(c.get("gold_symbol") or "GLD")
    oi, rr = _rows(st, oi_key(sym), now), _rows(st, rr_key(sym), now)
    oc = c.get("official") or {}
    off_key = oc.get("key") or OFFICIAL_KEY
    flow = (oc.get("kind") or "flow") == "flow"
    off = _rows(st, off_key, now)
    paper_n = min(months_held(oi), months_held(rr)) if oi and rr else 0
    off_n = months_held(off)
    out: dict[str, Any] = {"symbol": sym, "paper_months": paper_n,
                           "official_months": off_n, "need_months": need,
                           "official_key": off_key,
                           "official_label": oc.get("label") or OFFICIAL_LABEL,
                           "not_yet_sourced": [x["key"] for x in
                                               (c.get("official") or {}).get("not_yet_sourced") or []]}
    if oi:
        out["paper_oi"] = {"latest": oi[-1][1], "as_of": oi[-1][0],
                           "percentile": _pct([v for _, v in oi], oi[-1][1])}
    if rr:
        out["paper_rr"] = {"latest": rr[-1][1], "as_of": rr[-1][0],
                           "percentile": _pct([v for _, v in rr], rr[-1][1])}
    k = int(c.get("official_months", 3))
    if flow and len(off) >= k:
        # A flow (IMF IFS net purchases): the change is the months' sum.
        out["official_change"] = {"change_oz": sum(v for _, v in off[-k:]),
                                  "months": k, "as_of": off[-1][0]}
    elif not flow and len(off) > k:
        out["official_change"] = {"change_oz": off[-1][1] - off[-1 - k][1],
                                  "months": k, "as_of": off[-1][0]}
    if oc.get("count_key") and off:
        cnt = dict(_rows(st, oc["count_key"], now))
        if off[-1][0] in cnt:
            out["official_countries"] = int(cnt[off[-1][0]])
    waiting = [leg for leg, n in (("paper", paper_n), ("official", off_n)) if n < need]
    if waiting:
        out["state"] = None
        out["waiting"] = waiting
        return out
    po, pr = out["paper_oi"]["percentile"], out["paper_rr"]["percentile"]
    hi, lo = float(c.get("surging_pct", 80)), float(c.get("absent_pct", 50))
    paper = ("surging" if po is not None and pr is not None and po >= hi and pr >= hi
             else "absent" if po is not None and pr is not None and po <= lo and pr <= lo
             else "neither surging nor absent")
    ch = (out.get("official_change") or {}).get("change_oz")
    official = (None if ch is None else "accumulating" if ch > 0 else
                "flat" if ch == 0 else "selling")
    out["paper_reading"], out["official_reading"] = paper, official
    out["state"] = ("fragile rally" if paper == "surging" and official == "flat" else
                    "durable base" if official == "accumulating" and paper == "absent"
                    else "neither")
    return out


def two_bid_lines(s: dict) -> list[str]:
    """The block's sentences: the state, or which leg is waiting."""
    need = s["need_months"]
    if s.get("state") is None:
        parts = []
        if "paper" in s["waiting"]:
            parts.append(f"the paper leg ({s['symbol']} options) holds "
                         f"{s['paper_months']} of {need} months")
        if "official" in s["waiting"]:
            parts.append(f"the official leg ({s.get('official_label') or OFFICIAL_LABEL}) "
                         f"holds {s['official_months']} of {need} months")
        return [f"Two-bid state: not yet read, as both legs need {need} months; "
                + "; ".join(parts) + "."]
    return [f"Two-bid state: {s['state']} (paper {s['paper_reading']}, official "
            f"{s['official_reading'] or 'unread'})."]


def oi_kill_state(st, symbol: str, now: str, c: Optional[dict] = None) -> str:
    """Section 5's twelve-month kill test on call-put OI: waiting until the
    series holds twelve months; then due, and not yet built (AQ-10)."""
    c = c or cfg()
    need = int(c.get("kill_test_months", 12))
    n = months_held(_rows(st, oi_key(symbol), now))
    if n < need:
        return f"kill test waits: {n} of {need} months of call-put OI"
    return ("kill test due: twelve months held; the forward 20-day test is AQ-10's "
            "kill-condition gate, not yet built")


def rr_kill_state() -> str:
    return "no kill condition ruled on the risk reversal (section 5 names call-put OI only)"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _main(argv: list[str]) -> int:
    import argparse  # noqa: PLC0415
    import json  # noqa: PLC0415
    from . import session  # noqa: PLC0415
    p = argparse.ArgumentParser(description="The paper bid (AQ-8a).")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--session", required=True)
    b = sub.add_parser("backfill")
    b.add_argument("--days", type=int, default=60)
    b.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("show")
    s.add_argument("--as-of", default=None)
    a = p.parse_args(argv)
    if a.cmd == "record":
        print(json.dumps(record_session(a.session), indent=2, default=str))
        return 0
    if a.cmd == "backfill":
        print(json.dumps(backfill(a.days, a.dry_run), indent=2, default=str))
        return 0
    now = a.as_of or session.utc_iso(timespec="microseconds")
    with observations.ObservationStore() as st:
        for sym in config.PAPER_BID_SYMBOLS:
            oi, rr = _rows(st, oi_key(sym), now), _rows(st, rr_key(sym), now)
            print(f"  {sym:5} call-put OI " + (f"{oi[-1][1]:+,.0f} ({oi[-1][0]})" if oi else "none")
                  + "   RR25 " + (f"{rr[-1][1]:+.2f} ({rr[-1][0]})" if rr else "none"))
            print(f"        {oi_kill_state(st, sym, now)}")
        for line in two_bid_lines(two_bid_state(st, now)):
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
