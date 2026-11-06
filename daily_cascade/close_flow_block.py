"""
The levered-ETF close flow in Positioning & flows (signal-triage Batch 22 item 116,
the order's 98.1; A127, 6 Nov 2026). The figures are altdata/close_flow.py's; this
module lays them out and computes nothing of its own.

  THE CLOSE     a table: the 16:45 estimate by bucket, $bn and % of ADV, the 15:00
                estimate beside it; the 15:00 flag's line when it fired; the one
                "mechanical close flow" line; the funds left out, named. The
                16:45 estimate is computed in memory here and stored by the close
                (daily_cascade/stack_close.py) after the report.
  THE WEEKLY    the week's sessions, largest first (|the 16:45 total|), with the
                15:00 total and whether the flag fired. The Monthly reads the same
                table over its month (the five largest).
  NOT THE 07:00 ANCHOR.

THE "MECHANICAL CLOSE FLOW" LINE (98.1) is this estimate combined with 6b's
dealer-hedging estimate. That estimate is not wired, so the line prints the
levered-ETF figure alone and says "dealer hedging: not yet combined" (the order's
cross-item note: "If 98 lands first, it prints the levered-ETF line alone until 6b
is wired in").

Report-only: a report line and the 15:00 flag (alert-only, no rights).
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Optional

log = logging.getLogger(__name__)

TITLE = "Levered-ETF close flow (estimate)"
NOTE = ("Estimate: sum over the roster's funds of AUM at the prior close x L x (L - 1) "
        "x the underlying's return from the prior close (3x trades 6x AUM, -3x 12x); "
        "positive is buying into the close. Index funds read their index's ETF as a "
        "proxy; % of ADV is against the 20-session dollar volume of the instruments "
        "driving each bucket. Static AUM overstates the flow when dip-buying creates "
        "units, and swap books net some of it. Report-only; the 15:00 flag is "
        "alert-only (O-1).")
COLUMNS = ["Bucket", "16:45, $bn", "16:45, % of ADV", "15:00, $bn", "15:00, % of ADV"]
WEEK_COLUMNS = ["Session", "16:45 total, $bn", "16:45, % of ADV", "15:00 total, $bn",
                "15:00 flag"]


def _bn(v: Optional[float]) -> str:
    return "—" if v is None else f"{v / 1e9:+,.1f}"


def _pc(v: Optional[float]) -> str:
    return "—" if v is None else f"{v:+.1f}%"


def mechanical_line(total: Optional[dict], cfg: Optional[dict] = None) -> str:
    """The one line: the levered-ETF figure, and dealer hedging not yet combined."""
    from altdata import close_flow as cf                        # noqa: PLC0415
    cfg = cfg or cf.config()
    tail = cfg["dealer_hedging"]["not_combined"]
    t = total or {}
    if t.get("flow") is None:
        return f"Mechanical close flow: levered ETFs not estimated; {tail}."
    side = "buying" if t["flow"] > 0 else "selling" if t["flow"] < 0 else "flat"
    pct = "" if t.get("pct_adv") is None else f", {t['pct_adv']:+.1f}% of ADV"
    return (f"Mechanical close flow (16:45 estimate): levered ETFs {cf.usd(t['flow'])} "
            f"({side}{pct}); {tail}.")


def _left_line(left: dict) -> Optional[str]:
    if not left:
        return None
    by: dict[str, list[str]] = {}
    for t, why in sorted(left.items()):
        by.setdefault(why, []).append(t)
    parts = [f"{', '.join(ts)} ({why})" for why, ts in by.items()]
    return "Not in the estimate: " + "; ".join(parts) + "."


def close_table(est: dict, s1500: dict) -> dict:
    rows = []
    for b in est["buckets"]:
        f15, p15 = s1500.get(b["id"], (None, None))
        rows.append([b["label"], _bn(b["flow"]), _pc(b["pct_adv"]), _bn(f15), _pc(p15)])
    f15, p15 = s1500.get("total", (None, None))
    rows.append(["Total", _bn(est["total"]["flow"]), _pc(est["total"]["pct_adv"]),
                 _bn(f15), _pc(p15)])
    return {"columns": COLUMNS, "rows": rows}


def close_subsection(st, day: str, cutoff: str, now: Optional[str] = None
                     ) -> tuple[Optional[dict], list[dict]]:
    """(the close's sub-section, the 16:45 rows the close stores). Never raises."""
    from altdata import close_flow as cf                        # noqa: PLC0415
    try:
        cfg = cf.config()
        est = cf.for_close(st, day, cutoff, cfg)
        s15 = cf.stored(st, day, cutoff, "1500", cfg)
        fl = cf.flag_for(st, day, cutoff, cfg)
    except Exception:                                           # noqa: BLE001
        log.warning("the close-flow estimate faulted", exc_info=True)
        return None, []
    # The mechanical line prints once, as the section's item (stack.build pops
    # it from here); the sub-section's lines are the flag and the left-out funds.
    lines = [fl["line"]] if fl.get("fired") else []
    left = _left_line(est["left_out"])
    if left:
        lines.append(left)
    nt = [] if est["total"]["flow"] is not None else [
        "the 16:45 close-flow estimate (no fund had a stored prior AUM and a close)"]
    if s15.get("total", (None, None))[0] is None:
        nt.append("the 15:00 close-flow estimate (the 15:00 pass stored none for "
                  f"{day})")
    sub = {"title": TITLE, "table": close_table(est, s15), "lines": lines,
           "mechanical_line": mechanical_line(est["total"], cfg),
           "paragraph_wanted": False, "table_note": NOTE, "not_tracked": nt,
           "data": {"close_flow": {"total_1645": est["total"],
                                   "total_1500": dict(zip(("flow", "pct_adv"),
                                                          s15.get("total", (None, None)))),
                                   "flag_1500": {"fired": fl.get("fired"),
                                                 "basis": fl["rule"]["basis"]},
                                   "left_out": est["left_out"]}}}
    return sub, cf.rows(est, "1645", day, now or cutoff)


def _sessions(now: str, cadence: str) -> list[str]:
    from altdata import session                                 # noqa: PLC0415
    end = dt.date.fromisoformat(now[:10])
    if cadence == "monthly":
        start = (end.replace(day=1) - dt.timedelta(days=1)).replace(day=1)
        start = start if end.day <= 7 else end.replace(day=1)
        span = (end - start).days + 1
    else:
        span = 7
    out = []
    for i in range(span):
        d = end - dt.timedelta(days=i)
        if session.is_trading_session(d):
            out.append(d.isoformat())
    return sorted(out)


def period_subsection(st, now: str, cadence: str = "weekly") -> Optional[dict]:
    """The Weekly's table (the Monthly reads the same one): the period's sessions,
    largest first by |the 16:45 total|; the Monthly keeps the five largest."""
    from altdata import close_flow as cf                        # noqa: PLC0415
    try:
        cfg = cf.config()
        recs = []
        for d in _sessions(now, cadence):
            s45 = cf.stored(st, d, now, "1645", cfg)["total"]
            s15 = cf.stored(st, d, now, "1500", cfg)["total"]
            if s45[0] is None and s15[0] is None:
                continue
            fl = cf.flag_for(st, d, now, cfg)
            recs.append((d, s45, s15, fl.get("fired")))
    except Exception:                                           # noqa: BLE001
        log.warning("the close-flow period table faulted", exc_info=True)
        return None
    recs.sort(key=lambda r: -abs(r[1][0] if r[1][0] is not None else (r[2][0] or 0.0)))
    if cadence == "monthly":
        recs = recs[:5]
    rows = [[d, _bn(a[0]), _pc(a[1]), _bn(b[0]),
             "fired" if f else ("not fired" if f is False else "not read")]
            for d, a, b, f in recs]
    period = "month" if cadence == "monthly" else "week"
    lines = [] if rows else [f"No close-flow estimate stored this {period}: the history "
                             "builds from the first live run (A127, 6 Nov 2026)."]
    top = recs[0] if recs else None
    data: dict[str, Any] = {"sessions": len(recs),
                            "largest": None if not top else
                            {"session": top[0], "total_1645": top[1][0]},
                            "flags_fired": sum(1 for r in recs if r[3])}
    if top and top[1][0] is not None:
        lines.append(mechanical_line({"flow": top[1][0], "pct_adv": top[1][1]}, cfg)
                     .replace("(16:45 estimate)", f"(the {period}'s largest, {top[0]})"))
    title = TITLE + (", the month's five largest sessions" if cadence == "monthly"
                     else ", the week's sessions")
    return {"title": title, "table": {"columns": WEEK_COLUMNS, "rows": rows},
            "lines": lines, "paragraph_wanted": False, "table_note": NOTE,
            "data": {"close_flow_period": data}}
