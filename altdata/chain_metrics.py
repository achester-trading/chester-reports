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
PC_KEY = "chain.spy_put_call_volume"
SOURCE = "spy_chain_capture"
TARGET_DAYS = 30.0
LABEL_PC = "SPY chain, own capture"


def chain_dir() -> Path:
    p = Path(config.CHAIN_DIR)
    return p if p.is_absolute() else REPO / p


def latest_capture(day: str, base: Optional[Path] = None) -> Optional[Path]:
    """The session's last SPY capture (the file names carry the UTC time)."""
    d = (base or chain_dir()) / day
    files = sorted(p for p in d.glob("SPY_*.csv") if "_quality" not in p.name) \
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
    a = p.parse_args(argv)
    if a.cmd == "show":
        print(json.dumps(readings(a.session), indent=2, default=str))
    else:
        print(json.dumps(backfill(a.days, a.dry_run), indent=2, default=str))
    return 0


if __name__ == "__main__":                                     # pragma: no cover
    raise SystemExit(_main(sys.argv[1:]))
