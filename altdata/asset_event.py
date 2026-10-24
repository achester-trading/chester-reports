"""
The pieces item 73's two event screens share (signal-triage Batch 15 item 73;
a58-batch15-1): the gold event (altdata/gold_event.py) and the developed-market
drawdown screen (altdata/dm_drawdown.py). Item 52's event pattern and a57's
speed-flag ledger shape: a trigger read against the series' own history, an
attribution that waits for its inputs, and a ledger row per event with its
realised outcomes, each resolution a new vintage, never an overwrite.

Nothing here reads a composite or the market-state object.
"""

from __future__ import annotations

import datetime as dt
import json
import math
from typing import Any, Optional


def threshold(values: list[float], pct: float) -> Optional[float]:
    """The nearest-rank `pct` percentile of `values` (the ceil(pct/100 x n)-th
    smallest), or None for no values. Written out so a gate can do it by hand."""
    if not values:
        return None
    s = sorted(values)
    k = max(1, math.ceil(pct / 100.0 * len(s)))
    return s[k - 1]


def years_back(day: str, years: int) -> str:
    d = dt.date.fromisoformat(day)
    try:
        return d.replace(year=d.year - years).isoformat()
    except ValueError:                                          # 29 Feb
        return d.replace(year=d.year - years, day=28).isoformat()


def on_or_before(pts: list[tuple[str, float]], day: str) -> Optional[tuple[str, float]]:
    best = None
    for d, v in pts:
        if d <= day:
            best = (d, v)
        else:
            break
    return best


def before(pts: list[tuple[str, float]], day: str) -> Optional[tuple[str, float]]:
    best = None
    for d, v in pts:
        if d < day:
            best = (d, v)
        else:
            break
    return best


def leg_change(pts: list[tuple[str, float]], start: str, day: str, unit: str,
               tol_days: int) -> dict:
    """A leg's change from `start` to `day`: bp for a rate (in %), % for a price.
    "awaiting" when the day's observation is not stored yet."""
    end = on_or_before(pts, day)
    if not end or end[0] != day:
        return {"state": "awaiting", "stored_through": end[0] if end else None}
    beg = on_or_before(pts, start)
    if not beg or (dt.date.fromisoformat(start) - dt.date.fromisoformat(beg[0])).days > tol_days:
        return {"state": "absent", "reason": f"no observation within {tol_days} days before {start}"}
    if unit == "bp":
        ch = (end[1] - beg[1]) * 100.0
    elif beg[1] == 0:
        return {"state": "absent", "reason": "a zero start value"}
    else:
        ch = (end[1] / beg[1] - 1.0) * 100.0
    return {"state": "computed", "change": round(ch, 2), "unit": unit,
            "from": beg[0], "to": end[0]}


def leg_text(label: str, r: dict) -> str:
    if r["state"] == "computed":
        u = " bp" if r["unit"] == "bp" else "%"
        return f"{label} {r['change']:+.{0 if r['unit'] == 'bp' else 2}f}{u}"
    if r["state"] == "awaiting":
        return f"{label} awaiting (stored through {r.get('stored_through') or 'nothing'})"
    if r["state"] == "not tracked":
        return f"{label}: {r['reason']}"
    return f"{label} absent ({r.get('reason')})"


def forward(pts: list[tuple[str, float]], day: str, sessions: list[int],
            move_sign: Optional[float], prefix: str) -> dict:
    """The series' realised % change over the next `sessions`; None where not yet
    stored. `continued` compares the last horizon's sign with the move's."""
    days = [d for d, _ in pts]
    vals = dict(pts)
    out: dict[str, Any] = {}
    if day not in vals:
        out.update({f"{prefix}_{int(f)}d_pct": None for f in sessions})
        out["resolved"] = False
        return out
    i = days.index(day)
    for f in sessions:
        f = int(f)
        out[f"{prefix}_{f}d_pct"] = (round((vals[days[i + f]] / vals[day] - 1.0) * 100.0, 2)
                                     if i + f < len(days) and vals[day] else None)
    last = out.get(f"{prefix}_{int(sessions[-1])}d_pct")
    out["continued"] = (None if last is None or not move_sign else
                        (last > 0) == (move_sign > 0) and last != 0)
    out["resolved"] = all(out[f"{prefix}_{int(f)}d_pct"] is not None for f in sessions)
    return out


def ledger_row(key: str, instrument: str, day: str, body: dict, now: str, source: str) -> dict:
    return {"registry_key": key, "instrument": instrument, "observed_at": day,
            "available_at": now, "value": json.dumps(body, sort_keys=True, default=str),
            "source": source}


def latest_bodies(st, key: str, cutoff: str) -> dict[str, dict]:
    """{instrument: the newest vintage's body} as of the cutoff."""
    by: dict[str, dict] = {}
    for r in st.as_of(key, cutoff):
        try:
            by[str(r["instrument"])] = json.loads(r["value_text"])
        except (TypeError, ValueError):
            continue
    return dict(sorted(by.items()))
