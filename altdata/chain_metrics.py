"""
Per-session readings from SPY's own captured option chain.

    python -m altdata.chain_metrics show --session 2026-10-02
    python -m altdata.chain_metrics backfill --days 60 [--dry-run]

T2.2 rulings of 5 Oct 2026:

  item 3  SPY's AT-THE-MONEY 30-DAY IMPLIED VOLATILITY, solved by the chain
          solver (tools/iv_solver.py) from mid prices -- not yfinance's IV
          column -- and stored per session. The Weekly's dealer table uses it
          for the implied one-day range; where it is absent the table uses the
          VIX, labelled "VIX as proxy".
  item 4  SPY's VOLUME PUT/CALL per session: total put volume over total call
          volume across the session's captured chain, labelled "SPY chain, own
          capture" wherever it prints (the W9 gauge). It replaces any third-party
          put/call series: Cboe's public file ended in 2019.

THE METHOD, ATM IV. Per expiry, the solver's forward (put-call parity at the
tightest strike) and its OTM-only solved IVs; the expiry's ATM IV is the solved
IV interpolated linearly in strike between the nearest OTM put below the forward
and the nearest OTM call above it. The 30-day figure interpolates TOTAL VARIANCE
between the two expiries bracketing 30 calendar days -- the VIX construction --
and says "nearest" instead when no expiry brackets it. Stored in percent.

THE CLOCKS. observed_at is the session; available_at is the capture's own
fetched_at -- the reading could not be known before the chain was captured.
The close writes it (daily_cascade/stack_close.py); the backfill rebuilds it from
captures already on disk and is idempotent.
"""

from __future__ import annotations

import csv
import datetime as dt
import logging
import math
import sys
from pathlib import Path
from typing import Any, Optional

from . import config, observations

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
IV_KEY = "chain.spy_atm_iv_30d"
# OS-10 (a44-opening-setup, 18 Oct 2026): per name, from each session's last capture.
VOL_KEY = "chain.options_volume"
FRONT_IV_KEY = "chain.atm_iv_front"
# OS-8, OS-4, OS-5 (a45-opening-setup-2): per name, from the same captures.
SKEW_KEY = "chain.skew_25d_put"          # front month: put IV at -25 delta less ATM, vol points
IV_RV_KEY = "chain.iv_minus_rv20"        # front ATM IV less 20-session realised, vol points
FRONT_EXP_KEY = "chain.front_expiry"     # the front-month expiry the two used (a label)
PUT_VOL_KEY = "chain.put_share_volume"   # puts' share of the session's volume, percent
PUT_OI_KEY = "chain.put_share_oi_build"  # puts' share of the day's positive OI build, percent
# BATCH 11 ITEM 56 (ruled 19 Oct 2026): per-name volatility state.
IV30_KEY = "chain.iv30_atm"   # 30-day constant-maturity ATM IV, percent, SPY's method
RR_KEY = "chain.rr_25d"       # front month: 25-delta put IV less 25-delta call IV, vol points
RV20_KEY = "chain.rv20"       # 20-session close-to-close realised vol, annualised percent
RV60_KEY = "chain.rv60"       # 60-session, the same
NAMES_SOURCE = "chain_capture"
PC_KEY = "chain.spy_put_call_volume"
SOURCE = "spy_chain_capture"
TARGET_DAYS = 30.0
LABEL_PC = "SPY chain, own capture"


def chain_dir() -> Path:
    p = Path(config.CHAIN_DIR)
    return p if p.is_absolute() else REPO / p


def latest_capture(day: str, base: Optional[Path] = None,
                   symbol: str = "SPY") -> Optional[Path]:
    """The session's last capture of `symbol` (the file names carry the UTC
    time)."""
    d = (base or chain_dir()) / day
    files = sorted(p for p in d.glob(f"{symbol}_*.csv") if "_quality" not in p.name) \
        if d.is_dir() else []
    return files[-1] if files else None


def _f(v) -> Optional[float]:
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def load_rows(path: Path) -> list[dict]:
    out = []
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out.append({"expiry": r.get("expiry"), "dte": int(_f(r.get("dte")) or 0),
                        "right": r.get("right"), "strike": _f(r.get("strike")),
                        "bid": _f(r.get("bid")), "ask": _f(r.get("ask")),
                        "last_price": _f(r.get("last_price")),
                        "volume": _f(r.get("volume")) or 0.0,
                        "open_interest": _f(r.get("open_interest")),
                        "last_trade_date": r.get("last_trade_date"),
                        "fetched_at": r.get("fetched_at"), "spot": _f(r.get("spot"))})
    return out


def put_call_volume(rows: list[dict]) -> Optional[dict]:
    calls = sum(r["volume"] for r in rows if r["right"] == "C")
    puts = sum(r["volume"] for r in rows if r["right"] == "P")
    if calls <= 0:
        return None
    return {"ratio": round(puts / calls, 4), "puts": puts, "calls": calls}


def _solver():
    tools = str(REPO / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import iv_solver                                            # noqa: PLC0415
    return iv_solver


def expiry_atm_iv(solved: list[dict], forward: float) -> Optional[float]:
    """The solved IV at the forward: linear in strike between the nearest OTM
    put below and the nearest OTM call above."""
    puts = [r for r in solved if r["right"] == "P" and r.get("solved_iv")
            and r["strike"] < forward]
    calls = [r for r in solved if r["right"] == "C" and r.get("solved_iv")
             and r["strike"] > forward]
    p = max(puts, key=lambda r: r["strike"]) if puts else None
    c = min(calls, key=lambda r: r["strike"]) if calls else None
    if p and c:
        w = (forward - p["strike"]) / (c["strike"] - p["strike"])
        return p["solved_iv"] + w * (c["solved_iv"] - p["solved_iv"])
    one = p or c
    return one["solved_iv"] if one else None


def atm_iv_30d(rows: list[dict], r: Optional[float] = None) -> Optional[dict]:
    """SPY's at-the-money 30-day IV, in percent, from the chain solver."""
    ivs = _solver()
    rate = config.RISK_FREE_RATE if r is None else r
    out = ivs.solve_chain(rows, rate)
    by_exp: dict[str, list] = {}
    for x in out["rows"]:
        by_exp.setdefault(x["expiry"], []).append(x)
    points = []
    for exp, meta in out["expiries"].items():
        if not meta.get("forward") or (meta.get("dte") or 0) < 1:
            continue
        iv = expiry_atm_iv(by_exp.get(exp) or [], meta["forward"])
        if iv:
            points.append((float(meta["dte"]), iv, exp))
    if not points:
        return None
    points.sort()
    below = [p for p in points if p[0] <= TARGET_DAYS]
    above = [p for p in points if p[0] >= TARGET_DAYS]
    if below and above:
        (d1, s1, e1), (d2, s2, e2) = below[-1], above[0]
        if d1 == d2:
            iv, method, used = s1, "exact", [e1]
        else:
            t1, t2, t = d1 / 365.0, d2 / 365.0, TARGET_DAYS / 365.0
            var = (s1 * s1 * t1 * (t2 - t) + s2 * s2 * t2 * (t - t1)) / (t * (t2 - t1))
            iv, method, used = math.sqrt(max(var, 0.0)), "variance_interpolated", [e1, e2]
    else:
        d, iv, e = min(points, key=lambda p: abs(p[0] - TARGET_DAYS))
        method, used = "nearest", [e]
    return {"iv_pct": round(100.0 * iv, 3), "method": method, "expiries": used}


def readings(day: str, base: Optional[Path] = None) -> dict:
    path = latest_capture(day, base)
    if not path:
        return {"session": day, "reason": "no SPY chain captured for the session"}
    rows = load_rows(path)
    if not rows:
        return {"session": day, "reason": f"{path.name} has no rows"}
    out: dict[str, Any] = {"session": day, "capture": path.name,
                           "fetched_at": rows[0].get("fetched_at")}
    try:
        out["atm_iv_30d"] = atm_iv_30d(rows)
    except Exception as exc:                                    # noqa: BLE001
        out["atm_iv_30d"] = None
        out["iv_reason"] = f"{type(exc).__name__}: {exc}"[:160]
    out["put_call_volume"] = put_call_volume(rows)
    return out


def third_friday(d: dt.date) -> dt.date:
    first = d.replace(day=1)
    return first + dt.timedelta(days=(4 - first.weekday()) % 7 + 14)


def _ec():
    tools = str(REPO / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import exposure_compute                                     # noqa: PLC0415
    return exposure_compute


def iv_at_delta(points: list[tuple[float, float]], target: float) -> Optional[float]:
    """IV at `target` delta, linear in delta between the points either side."""
    pts = sorted(points)
    for (d0, v0), (d1, v1) in zip(pts, pts[1:]):
        if d0 <= target <= d1 and d1 > d0:
            return v0 + (target - d0) / (d1 - d0) * (v1 - v0)
    return None


def put_skew_25d(solved: list[dict], spot: float, dte: float, atm_iv: float,
                 r: float) -> Optional[float]:
    """The 25-delta put skew, vol points: the solved put IV at -0.25 delta (Black-
    Scholes delta from the engine's bs_greeks on each put's solved IV) less the
    ATM IV, on one expiry."""
    ec = _ec()
    t = max(float(dte or 0), 0.0) / 365.0
    pts = []
    for x in solved:
        iv, k = x.get("solved_iv"), x.get("strike")
        if x.get("right") != "P" or not iv or not k:
            continue
        g = ec.bs_greeks(spot, k, iv, t, r, "P")
        if g:
            pts.append((g["delta"], iv))
    v = iv_at_delta(pts, -0.25)
    return None if v is None or not atm_iv else 100.0 * (v - atm_iv)


def call_iv_25d(solved: list[dict], spot: float, dte: float, r: float) -> Optional[float]:
    """The solved call IV at +0.25 delta on one expiry (as put_skew_25d's put side)."""
    ec = _ec()
    t = max(float(dte or 0), 0.0) / 365.0
    pts = []
    for x in solved:
        iv, k = x.get("solved_iv"), x.get("strike")
        if x.get("right") != "C" or not iv or not k:
            continue
        g = ec.bs_greeks(spot, k, iv, t, r, "C")
        if g:
            pts.append((g["delta"], iv))
    return iv_at_delta(pts, 0.25)


def risk_reversal_25d(skew_put: Optional[float], atm_iv: Optional[float],
                      call25: Optional[float]) -> Optional[float]:
    """25-delta put IV less 25-delta call IV, vol points. The put IV is the ATM IV
    plus the stored put skew (both on the front month)."""
    if skew_put is None or not atm_iv or call25 is None:
        return None
    return skew_put + 100.0 * (atm_iv - call25)


def front_month_iv(rows: list[dict], min_dte: int = 7,
                   r: Optional[float] = None) -> Optional[dict]:
    """The front month's ATM IV, percent: the nearest third-Friday expiry at least
    `min_dte` days out, else the first expiry that far out (method "nearest"),
    solved and interpolated as the 30-day figure's legs are."""
    ivs = _solver()
    rate = config.RISK_FREE_RATE if r is None else r
    out = ivs.solve_chain(rows, rate)
    by_exp: dict[str, list] = {}
    for x in out["rows"]:
        by_exp.setdefault(x["expiry"], []).append(x)
    ok = sorted((e, m) for e, m in out["expiries"].items()
                if m.get("forward") and (m.get("dte") or 0) >= min_dte)
    monthly = [(e, m) for e, m in ok
               if dt.date.fromisoformat(str(e)[:10]) == third_friday(dt.date.fromisoformat(str(e)[:10]))]
    pick, method = (monthly[0], "third Friday") if monthly else ((ok[0], "nearest") if ok else (None, None))
    if not pick:
        return None
    e, m = pick
    iv = expiry_atm_iv(by_exp.get(e) or [], m["forward"])
    if not iv:
        return None
    spot = next((x["spot"] for x in rows if x.get("spot")), None)
    skew = (put_skew_25d(by_exp.get(e) or [], spot, m.get("dte"), iv, rate)
            if spot else None)
    c25 = call_iv_25d(by_exp.get(e) or [], spot, m.get("dte"), rate) if spot else None
    rr = risk_reversal_25d(skew, iv, c25)
    return {"iv_pct": round(100.0 * iv, 3), "expiry": e, "dte": m.get("dte"),
            "method": method, "skew_25d_put": None if skew is None else round(skew, 3),
            "rr_25d": None if rr is None else round(rr, 3)}


def previous_capture(day: str, symbol: str, base: Optional[Path] = None) -> Optional[Path]:
    """The last capture of `symbol` on the latest session directory before `day`."""
    root = base or chain_dir()
    if not root.is_dir():
        return None
    for d in sorted((x.name for x in root.iterdir() if x.is_dir() and x.name < day),
                    reverse=True):
        p = latest_capture(d, root, symbol)
        if p:
            return p
    return None


def oi_changes(prev: list[dict], cur: list[dict]) -> list[dict]:
    """Per contract (expiry, strike, right) present in both captures: the later
    row and its open-interest change."""
    before = {(r["expiry"], r["strike"], r["right"]): r.get("open_interest")
              for r in prev if r.get("open_interest") is not None}
    out = []
    for r in cur:
        k = (r["expiry"], r["strike"], r["right"])
        if k in before and r.get("open_interest") is not None:
            out.append({**r, "oi_change": r["open_interest"] - before[k],
                        "oi_before": before[k]})
    return out


def put_shares(cur: list[dict], changes: list[dict]) -> dict:
    """OS-4/OS-5: puts' share of the session's volume, and of the day's positive
    open-interest build, percent; None where a total is zero."""
    pv = sum(r["volume"] for r in cur if r["right"] == "P")
    tv = sum(r["volume"] for r in cur)
    pb = sum(max(c["oi_change"], 0.0) for c in changes if c["right"] == "P")
    tb = sum(max(c["oi_change"], 0.0) for c in changes)
    return {"put_share_volume": 100.0 * pv / tv if tv else None,
            "put_share_oi_build": 100.0 * pb / tb if tb else None,
            "put_volume": pv, "volume": tv, "put_oi_build": pb, "oi_build": tb}


def name_readings(day: str, symbol: str, base: Optional[Path] = None,
                  min_dte: int = 7) -> dict:
    """OS-10: one name's session options volume (calls and puts, the last
    capture) and front-month ATM IV."""
    path = latest_capture(day, base, symbol)
    if not path:
        return {"session": day, "symbol": symbol, "reason": "no capture"}
    rows = load_rows(path)
    out: dict[str, Any] = {"session": day, "symbol": symbol, "capture": path.name,
                           "fetched_at": rows[0].get("fetched_at") if rows else None,
                           "volume": sum(r["volume"] for r in rows) if rows else None}
    prev = previous_capture(day, symbol, base)
    ch = oi_changes(load_rows(prev), rows) if prev else []
    out["put_shares"] = put_shares(rows, ch) if rows else None
    out["previous_capture"] = prev.name if prev else None
    if symbol in config.massive_universe():
        # SPX and SPCX: volume and put shares only -- their IV stays behind the
        # solver gate (tools/validate_iv_solver.py), as every other reader's does.
        out["front"] = None
        out["iv_reason"] = "pending the solver gate (vendor-only symbol)"
        return out
    try:
        out["front"] = front_month_iv(rows, min_dte) if rows else None
    except Exception as exc:                                    # noqa: BLE001
        out["front"] = None
        out["iv_reason"] = f"{type(exc).__name__}: {exc}"[:160]
    # Item 56: the 30-day constant-maturity IV, by SPY's method (total variance
    # between the two expiries bracketing 30 days, else "nearest").
    try:
        out["iv30"] = atm_iv_30d(rows) if rows else None
    except Exception as exc:                                    # noqa: BLE001
        out["iv30"] = None
        out["iv30_reason"] = f"{type(exc).__name__}: {exc}"[:160]
    return out


def realised_20(closes: list[float]) -> Optional[float]:
    """Annualised close-to-close realised vol over the last 20 returns, percent."""
    return realised_n(closes, 20)


def realised_n(closes: list[float], n: int) -> Optional[float]:
    """Annualised close-to-close realised vol over the last `n` returns, percent."""
    c = [x for x in closes if x][-(n + 1):]
    if len(c) < n + 1:
        return None
    r = [math.log(b / a) for a, b in zip(c, c[1:])]
    m = sum(r) / len(r)
    return 100.0 * math.sqrt(sum((x - m) ** 2 for x in r) / (len(r) - 1)) * math.sqrt(252)


def name_rows(rd: dict, rv20: Optional[float] = None,
              rv60: Optional[float] = None) -> list[dict]:
    avail, out = rd.get("fetched_at"), []
    if not avail:
        return out
    f = rd.get("front") or {}
    base = {"instrument": rd["symbol"], "observed_at": rd["session"], "available_at": avail,
            "source": NAMES_SOURCE}
    # Item 56's four keys.
    if (rd.get("iv30") or {}).get("iv_pct") is not None:
        out.append({**base, "registry_key": IV30_KEY, "value": rd["iv30"]["iv_pct"]})
    if f.get("rr_25d") is not None:
        out.append({**base, "registry_key": RR_KEY, "value": f["rr_25d"]})
    for key, v in ((RV20_KEY, rv20), (RV60_KEY, rv60)):
        if v is not None:
            out.append({**base, "registry_key": key, "value": round(v, 3)})
    if f.get("skew_25d_put") is not None:
        out.append({**base, "registry_key": SKEW_KEY, "value": f["skew_25d_put"]})
    if f.get("iv_pct") is not None and rv20 is not None:
        out.append({**base, "registry_key": IV_RV_KEY, "value": round(f["iv_pct"] - rv20, 3)})
    if f.get("expiry"):
        out.append({**base, "registry_key": FRONT_EXP_KEY,
                    "value": f"{f['expiry']} ({f.get('method')})"})
    ps = rd.get("put_shares") or {}
    for key, k in ((PUT_VOL_KEY, "put_share_volume"), (PUT_OI_KEY, "put_share_oi_build")):
        if ps.get(k) is not None:
            out.append({**base, "registry_key": key, "value": round(ps[k], 3)})
    if rd.get("volume") is not None:
        out.append({"registry_key": VOL_KEY, "instrument": rd["symbol"],
                    "observed_at": rd["session"], "available_at": avail,
                    "value": float(rd["volume"]), "source": NAMES_SOURCE})
    if rd.get("front"):
        out.append({"registry_key": FRONT_IV_KEY, "instrument": rd["symbol"],
                    "observed_at": rd["session"], "available_at": avail,
                    "value": rd["front"]["iv_pct"], "source": NAMES_SOURCE})
    return out


def record_names(day: str, store=None, base: Optional[Path] = None,
                 symbols: Optional[list[str]] = None) -> dict:
    """OS-10: every captured name's two readings for the session. Never raises."""
    syms = symbols or (config.chain_universe() + config.massive_universe())
    out: dict[str, Any] = {"session": day, "names": {}, "written": 0}
    rows: list[dict] = []
    own = store is None
    st = store or observations.ObservationStore()
    try:
        for sym in syms:
            try:
                rd = name_readings(day, sym, base)
                cl = [float(r["value_num"]) for r in
                      st.as_of(f"yfinance.mkt_{sym.lower()}", f"{day}T23:59:59+00:00") or []
                      if r.get("value_num") is not None and str(r["observed_at"])[:10] <= day]
                rv, rv60 = realised_20(cl), realised_n(cl, 60)
            except Exception as exc:                            # noqa: BLE001
                rd, rv, rv60 = {"error": f"{type(exc).__name__}: {exc}"[:160]}, None, None
            out["names"][sym] = {k: rd.get(k) for k in ("volume", "front", "put_shares",
                                                         "reason", "error")}
            if "error" not in rd:
                rows += name_rows(rd, rv, rv60)
        if rows:
            st.write_many(rows)
    finally:
        if own:
            st.close()
    out["written"] = len(rows)
    return out


def observation_rows(rd: dict) -> list[dict]:
    rows = []
    avail = rd.get("fetched_at")
    if not avail:
        return rows
    iv = rd.get("atm_iv_30d")
    if iv:
        rows.append({"registry_key": IV_KEY, "instrument": "SPY",
                     "observed_at": rd["session"], "available_at": avail,
                     "value": iv["iv_pct"], "source": SOURCE})
    pc = rd.get("put_call_volume")
    if pc:
        rows.append({"registry_key": PC_KEY, "instrument": "SPY",
                     "observed_at": rd["session"], "available_at": avail,
                     "value": pc["ratio"], "source": SOURCE})
    return rows


def record_session(day: str, store=None, base: Optional[Path] = None) -> dict:
    """Compute and store the session's two readings. Never raises."""
    try:
        rd = readings(day, base)
        rows = observation_rows(rd)
        if rows:
            own = store is None
            st = store or observations.ObservationStore()
            try:
                st.write_many(rows)
            finally:
                if own:
                    st.close()
        rd["written"] = len(rows)
        # OS-10 (a44-opening-setup): every captured name's volume and front IV,
        # recorded where the close already records SPY's, never fatal.
        rd["names"] = record_names(day, store, base)
        return rd
    except Exception as exc:                                    # noqa: BLE001
        return {"session": day, "error": f"{type(exc).__name__}: {exc}"[:200]}


def backfill(days: int = 60, dry_run: bool = False, base: Optional[Path] = None) -> dict:
    """ONE-TIME: the readings for every session whose capture is on disk in the
    last `days` calendar days. Idempotent: the store ignores a duplicate row."""
    root = base or chain_dir()
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    out = {"days": days, "dry_run": dry_run, "sessions": {}}
    sessions = sorted(p.name for p in root.iterdir() if p.is_dir() and p.name >= since) \
        if root.is_dir() else []
    st = None if dry_run else observations.ObservationStore()
    try:
        for d in sessions:
            rd = readings(d, root)
            rows = observation_rows(rd)
            if st is not None and rows:
                st.write_many(rows)
            out["sessions"][d] = {"atm_iv_30d": (rd.get("atm_iv_30d") or {}).get("iv_pct"),
                                  "put_call": (rd.get("put_call_volume") or {}).get("ratio"),
                                  "rows": len(rows), "reason": rd.get("reason")}
    finally:
        if st is not None:
            st.close()
    return out


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    import json                                                 # noqa: PLC0415
    p = argparse.ArgumentParser(description="SPY chain readings per session.")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show")
    s.add_argument("--session", required=True)
    b = sub.add_parser("backfill")
    b.add_argument("--days", type=int, default=60)
    b.add_argument("--dry-run", action="store_true")
    bn = sub.add_parser("backfill-names", help="OS-10: every name's volume and front IV")
    bn.add_argument("--days", type=int, default=60)
    bn.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    if a.cmd == "show":
        print(json.dumps(readings(a.session), indent=2, default=str))
    elif a.cmd == "backfill-names":
        root = chain_dir()
        since = (dt.date.today() - dt.timedelta(days=a.days)).isoformat()
        days = sorted(x.name for x in root.iterdir() if x.is_dir() and x.name >= since) \
            if root.is_dir() else []
        res = {}
        for d in days:
            if a.dry_run:
                res[d] = {s: name_readings(d, s).get("volume") for s in config.chain_universe()}
            else:
                res[d] = record_names(d)["written"]
        print(json.dumps(res, indent=2, default=str))
    else:
        print(json.dumps(backfill(a.days, a.dry_run), indent=2, default=str))
    return 0


if __name__ == "__main__":                                     # pragma: no cover
    raise SystemExit(_main(sys.argv[1:]))
