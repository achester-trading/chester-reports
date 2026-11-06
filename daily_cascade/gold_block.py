"""
The gold spine laid out (signal-triage Batch 16 items 87 and 88(a), (c), (d);
written as round 7's 80 and 81; B75). The figures are altdata/gold_attribution.py's
and the dealer engine's; this module computes nothing of its own.

  THE CLOSE (88(d))  Mechanics, after the event lines: one gold line ONLY when
                     the 2-sigma trigger fires or an exhaustion tell flips -- the
                     move, the five lenses in one line, the tell that flipped.
                     Otherwise nothing. The session's rows (the beta each
                     session, the lenses on a fired day) are kept in the
                     section's data for the close to store; never on a dry run.
  THE WEEKLY (88(a)) Its own section, `gold`, between Plumbing & rates and
                     Positioning & flows (config/reporting_stack.yaml; S1's
                     config/stack_hooks/ is not on this base, so the section
                     list carries it): the tape, the attribution and the beta,
                     positioning and flows, the official bid, the targets line,
                     the exhaustion checklist, GLD's dealer levels and the
                     block's own Ahead line, with one chart (W13). Its prose is
                     the stack's commentary path. Before its first edition (8 Nov
                     2026) it prints its header and "First edition 8 Nov." only.

Report rights only: nothing here enters a composite, the market-state object, a
dial or a packet.
"""

from __future__ import annotations

import datetime as dt
import logging
import math
import statistics
from typing import Any, Optional

log = logging.getLogger(__name__)

SECTION_ID = "gold"
CLOSE_TITLE = "Gold on exception"


def _safe(fn, what: str, default: Any = None) -> Any:
    try:
        return fn()
    except Exception:                                           # noqa: BLE001
        log.warning("%s faulted", what, exc_info=True)
        return default


def _item(key: str, text: str, priority: int, value: Any = None) -> dict:
    from . import stack                                         # noqa: PLC0415
    return stack.item(key, text, priority, value)


# ---------------------------------------------------------------------------
# The close: one line on exception
# ---------------------------------------------------------------------------
def close_lines(series: dict, day: str, cfg: Optional[dict] = None) -> list[str]:
    from altdata import gold_attribution as ga                  # noqa: PLC0415
    cl = ga.close_line(series, day, cfg)
    return [cl["line"]] if cl else []


def close_extras(built: dict, st, day: str, cutoff: str) -> None:
    from altdata import gold_attribution as ga                  # noqa: PLC0415
    from . import batch15_a_block                               # noqa: PLC0415
    mech = built.get("mechanics")
    if mech is None:
        return
    cfg = ga.config()
    series = _safe(lambda: ga.read_series(st, cutoff, cfg), "the gold series")
    if not series:
        return
    ev = _safe(lambda: ga.evaluate(series, day, cfg), "the gold attribution")
    if ev:
        mech.setdefault("data", {})["_gold_attr"] = ev
    lines = _safe(lambda: close_lines(series, day, cfg), "the gold line", [])
    if not lines:
        return
    subs = mech.setdefault("subsections", [])
    subs.insert(batch15_a_block._after_events(subs),            # noqa: SLF001
                {"title": CLOSE_TITLE, "paragraph_wanted": False, "lines": lines})
    for i, ln in enumerate(lines):
        mech["items"].append(_item(f"mech:gold_attr:{i}", ln, 1, ln))


def store_rows(mech_data: dict, now: str) -> list[dict]:
    """The session's rows for the close to write (never on a dry run)."""
    from altdata import gold_attribution as ga                  # noqa: PLC0415
    ev = mech_data.pop("_gold_attr", None)
    return ga.rows_for(ev, now) if ev else []


# ---------------------------------------------------------------------------
# The Weekly's section
# ---------------------------------------------------------------------------
def _n(v: Optional[float], dp: int = 2, unit: str = "", signed: bool = False) -> str:
    if v is None:
        return "not stored"
    return (f"{v:+,.{dp}f}{unit}" if signed else f"{v:,.{dp}f}{unit}")


def _back(day: str, days: int) -> str:
    return (dt.date.fromisoformat(day) - dt.timedelta(days=days)).isoformat()


def tape(gold: list[tuple[str, float]], day: str, cfg: dict) -> dict:
    """Close, the week's change, distance from the record and the 200-day, the
    run of closes below the 200-day, realised vol."""
    from altdata import gold_attribution as ga                  # noqa: PLC0415
    w = cfg["weekly"]
    pts = ga.upto(gold, day)
    if not pts:
        return {"state": "not stored"}
    close = pts[-1][1]
    wk = [v for d, v in pts if d <= _back(pts[-1][0], 7)]
    rec_d, rec = max(pts, key=lambda x: x[1])
    m = int(w["ma_sessions"])
    ma = statistics.fmean(v for _, v in pts[-m:]) if len(pts) >= m else None
    run = 0
    if len(pts) >= m:
        for i in range(len(pts) - 1, m - 2, -1):
            avg = statistics.fmean(v for _, v in pts[i - m + 1:i + 1])
            if pts[i][1] < avg:
                run += 1
            else:
                break
    lr = [math.log(b / a) for (_, a), (_, b) in zip(pts, pts[1:]) if a > 0 and b > 0]
    k = int(w["vol_sessions"])
    vol = statistics.stdev(lr[-k:]) * math.sqrt(252) * 100 if len(lr) >= k else None
    return {"state": "computed", "day": pts[-1][0], "close": close,
            "week_pct": (close / wk[-1] - 1) * 100 if wk else None,
            "record": rec, "record_day": rec_d, "from_record_pct": (close / rec - 1) * 100,
            "ma200": ma, "from_ma_pct": (close / ma - 1) * 100 if ma else None,
            "run_below": run if ma else None, "vol20": vol, "stored_from": pts[0][0]}


def tape_rows(t: dict, cfg: dict) -> list[list[str]]:
    if t["state"] != "computed":
        return [["Gold (COMEX front future)", "not stored (yfinance.mkt_gold_front)"]]
    return [
        ["Close", f"${t['close']:,.2f}/oz on {t['day']}"],
        ["The week", _n(t["week_pct"], 2, "%", True)],
        ["From the record", f"{t['from_record_pct']:+.2f}% (record ${t['record']:,.2f} on "
                            f"{t['record_day']}, stored from {t['stored_from']})"],
        ["From the 200-day", ("not stored (fewer than 200 closes)" if t["ma200"] is None
                              else f"{t['from_ma_pct']:+.2f}% (200-day ${t['ma200']:,.2f})")],
        ["Closes below the 200-day, running", "not stored" if t["run_below"] is None
         else str(t["run_below"])],
        ["Realised vol, 20 sessions", _n(t["vol20"], 1, "% annualised")],
        ["GVZ", cfg["not_stored"]["gvz"]],
    ]


def change_at(pts: list[tuple[str, float]], day: str, days: int) -> Optional[float]:
    from altdata import gold_attribution as ga                  # noqa: PLC0415
    now = ga.upto(pts, day)
    then = ga.upto(pts, _back(day, days))
    if not now or not then:
        return None
    return now[-1][1] - then[-1][1]


def flows_rows(series: dict, day: str, cfg: dict) -> list[list[str]]:
    w = cfg["weekly"]
    rows = []
    entries = [(e["key"], e["label"], e["unit"]) for e in w["etf"]] + [
        ("cftc", w["cftc"]["label"], "contracts")]
    for key, label, unit in entries:
        pts = series.get(key) or []
        known = [p for p in pts if p[0] <= day]
        if not known:
            rows.append([label, "not stored"] + [""] * len(w["windows"]))
            continue
        dp = 1 if unit == "tonnes" else 0
        cells = [_n(change_at(pts, day, d), dp, signed=True) for d in w["windows"].values()]
        rows.append([label, f"{known[-1][1]:,.{dp}f} {unit} ({known[-1][0]})"] + cells)
    h = series.get(w["holders_13f"]) or []
    hk = [p for p in h if p[0] <= day]
    rows.append(["13F holders of the gold ETFs (filed item 72)",
                 f"{hk[-1][1]:,.0f} ({hk[-1][0]})" if hk else "not stored"]
                + [_n(change_at(h, day, d), 0, signed=True) if hk else ""
                   for d in w["windows"].values()])
    return rows


def ahead_line(events: list[dict], cfg: dict) -> str:
    """The week's gold-moving events (the calendar's rows by release class),
    ranked by the calendar's importance tier, then date, numbered 1-5."""
    w = cfg["weekly"]
    classes = set(w["ahead_classes"])
    mine = [e for e in events or [] if e.get("cls") in classes]
    mine.sort(key=lambda e: (e.get("tier") or 9, str(e.get("date") or ""),
                             str(e.get("time") or "")))
    mine = mine[:int(w["ahead_max"])]
    if not mine:
        return "Ahead for gold: no scheduled gold-moving event in the calendar's week."
    return "Ahead for gold: " + "; ".join(
        f"{i}. {e.get('event')} ({e.get('date')})" for i, e in enumerate(mine, 1)) + "."


def gld_levels_line(computed_dir: Optional[str], ending: str) -> str:
    """GLD's dealer levels from the engine's newest settled profile (88(c))."""
    from . import dealer_block                                  # noqa: PLC0415
    prof = _safe(lambda: dealer_block.newest_settled(ending, "GLD", computed_dir),
                 "GLD's profile") if computed_dir else None
    vendor = "vendor: FlashAlpha does not serve GLD in its plan (config/flashalpha.yaml)"
    if not prof or prof.get("error"):
        return (f"GLD's dealer levels: no settled profile stored for the week "
                f"(the exposure files' exception, item 88(c)); {vendor}.")
    o = prof.get("overall") or {}

    def lv(v):
        return "—" if not isinstance(v, (int, float)) else f"{v:,.2f}"
    return (f"GLD's dealer levels ({prof.get('session_date')}; inferred, not observed): "
            f"spot {lv(prof.get('spot'))}, gamma flip {lv(o.get('gamma_flip'))}, call wall "
            f"{lv(o.get('call_wall_otm'))}, put wall {lv(o.get('put_wall_otm'))}, net GEX "
            f"{lv(o.get('net_gex'))} $ a point, DEX ${lv(o.get('dex_notional'))}; {vendor}.")


def weekly_section(st, now: str, ending: str, *, computed_dir: Optional[str] = None,
                   events: Optional[list] = None, cfg: Optional[dict] = None,
                   series: Optional[dict] = None) -> dict:
    """The Weekly's gold section in the shape stack.assemble reads."""
    from altdata import gold_attribution as ga                  # noqa: PLC0415
    cfg = cfg or ga.config()
    w = cfg["weekly"]
    if ending < w["first_edition"]:
        return {"items": [], "data": {"gold": {"first_edition": w["first_edition"]}},
                "before_first": w["before_first"], "print_items": False}
    series = series if series is not None else ga.read_series(st, now, cfg)
    gold = series.get("gold") or []
    day = (ga.upto(gold, ending) or [(ending, None)])[-1][0]
    t = tape(gold, day, cfg)
    ev = ga.evaluate(series, day, cfg) if t["state"] == "computed" else None
    tl = ga.tells(series, day, cfg)
    # The week's 2-sigma days, newest first.
    wk = [d for d, _ in gold if _back(day, 7) < d <= day]
    fired = [e for e in (ga.evaluate(series, d, cfg) for d in wk) if e["fired"]]
    items = []
    if t["state"] == "computed":
        items.append(_item("gold:close", f"Gold closed at ${t['close']:,.2f}/oz, "
                           f"{_n(t['week_pct'], 2, '%', True)} on the week and "
                           f"{t['from_record_pct']:+.2f}% from its stored record.", 1,
                           round(t["close"], 2)))
        if t["ma200"] is not None:
            items.append(_item("gold:ma200", f"{t['from_ma_pct']:+.2f}% from the 200-day; "
                               f"{t['run_below']} closes running below it.", 2,
                               (round(t["from_ma_pct"], 2), t["run_below"])))
    else:
        items.append(_item("gold:none", "Gold: not stored (yfinance.mkt_gold_front).", 1,
                           "none"))
    # The newest 2-sigma day in full; the week's others by date (their lenses are
    # stored under gold.attr.* and in the close's line on each day).
    att_lines = ([ga.trigger_text(fired[-1]["trigger"]) + " on " + fired[-1]["day"] + ". "
                  + ga.lenses_line(fired[-1]["lenses"])]
                 + ([f"Also past 2σ this week: {', '.join(e['day'] for e in fired[:-1])}."]
                    if len(fired) > 1 else [])
                 if fired else
                 ["No 2σ gold move this week (the move screen's sigma and window)."])
    beta_line = ga.beta_text(ev["beta"]) if ev else "The 60-day beta: not stored."
    for i, ln in enumerate(att_lines):
        items.append(_item(f"gold:attr:{i}", ln, 2, ln))
    items.append(_item("gold:beta", beta_line, 2, (ev or {}).get("beta", {}).get("beta")))
    off = ga.official_text(ga.official_bid(series, day, cfg))
    items.append(_item("gold:official", f"The official bid: {off}.", 3, off))
    items.append(_item("gold:targets", w["targets"], 3, "not built"))
    tl_line = ga.tells_line(tl, cfg)
    items.append(_item("gold:tells", tl_line, 2, tuple(x["state"] for x in tl.values())))
    gl = gld_levels_line(computed_dir, ending)
    items.append(_item("gold:gld_levels", gl, 3, gl))
    ah = ahead_line(events or [], cfg)
    items.append(_item("gold:ahead", ah, 3, ah))
    cols = ["Line", "Level"] + list(w["windows"])
    subs = [
        {"title": "The tape", "paragraph_wanted": False,
         "table": {"columns": ["Line", "Reading"], "rows": tape_rows(t, cfg)}},
        {"title": "Attribution", "paragraph_wanted": False,
         "lines": att_lines + [beta_line]},
        {"title": "Positioning and flows", "paragraph_wanted": False,
         "table": {"columns": cols, "rows": flows_rows(series, day, cfg)}},
        {"title": "Official bid, targets and the checklist", "paragraph_wanted": False,
         "lines": [f"The official bid: {off}.", w["targets"], tl_line,
                   "The checklist's ledger: docs/ledgers/gold-exhaustion-"
                   "preregistration-2026-10.md (pre-registered; no rights).", gl]},
        {"title": "Ahead for gold", "paragraph_wanted": False, "lines": [ah]},
    ]
    return {"items": items, "print_items": False, "subsections": subs,
            "not_tracked": [cfg["not_stored"]["gvz"], cfg["not_stored"]["squeeze"]],
            "data": {"gold": {"tape": {k: v for k, v in t.items()},
                              "fired_days": [e["day"] for e in fired],
                              "tells": {k: v["state"] for k, v in tl.items()},
                              "chart_days": int(w["chart_days"])}}}


def mark_before_first(sections: list[dict], built: dict) -> None:
    """Before the first edition the section prints its header and one line, and
    asks for no prose (its empty note)."""
    b = built.get(SECTION_ID) or {}
    for s in sections:
        if s["id"] == SECTION_ID and b.get("before_first"):
            s["empty"], s["empty_note"] = True, b["before_first"]


def chart_series(gold: list[tuple[str, float]], day: str, cfg: dict) -> dict:
    """W13's points: the close over the chart's window, the 200-day and the record."""
    from altdata import gold_attribution as ga                  # noqa: PLC0415
    w = cfg["weekly"]
    pts = ga.upto(gold, day)
    m = int(w["ma_sessions"])
    ma = [(pts[i][0], statistics.fmean(v for _, v in pts[i - m + 1:i + 1]))
          for i in range(m - 1, len(pts))]
    lo = _back(day, int(w["chart_days"]))
    rec = max(pts, key=lambda x: x[1]) if pts else None
    return {"close": [p for p in pts if p[0] >= lo], "ma200": [p for p in ma if p[0] >= lo],
            "record": rec}
