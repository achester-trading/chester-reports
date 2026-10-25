"""
Signal-triage Batch 15, session A's items laid out (a58-batch15-1, 23 Oct 2026;
docs/change-order-signal-triage-batch-15-2026-10-23.md, G1-G6). The figures are
altdata/gold_event.py's, altdata/dm_drawdown.py's and altdata/gold_13f.py's; this
module computes nothing.

  THE CLOSE     Mechanics, the event area with item 52's and item 65's events: the
                gold event's and the developed-market drawdown's flag lines on a
                fired day (lines only); the events are kept in the section's data
                for the close to store in their ledgers.
  WEEKLY AND MONTHLY  Mechanics: each screen's block over the edition's sessions
                (a table of the fired days and their attribution, or one line that
                none fired), with the indices not screened listed.
  THE MONTHLY   Slow layers (Factor V), right after item 38's gold/equity ratio:
                item 72's institutional gold-ETF ownership line.
  FACTOR I      item 76: the AI-credit gap line, amended
                (daily_cascade/absorption_block.py).

Tables and code-written lines only: no paragraph is asked for, so no prose word is
added to any budget. A builder that faults is logged and prints nothing.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)

GOLD_TITLE = "Gold events"
DM_TITLE = "Developed-market drawdowns"
EVENT_TITLES = ("Volatility event", "10-year speed flag: what carried the move")


def _safe(fn: Callable, what: str, default: Any = None) -> Any:
    try:
        return fn()
    except Exception:                                           # noqa: BLE001
        log.warning("%s faulted", what, exc_info=True)
        return default


def _item(key: str, text: str, priority: int, value: Any = None) -> dict:
    from . import stack                                         # noqa: PLC0415
    return stack.item(key, text, priority, value)


def _after_events(subs: list[dict]) -> int:
    """The slot after the last of item 52's and item 65's sub-sections, else 0."""
    at = [i for i, x in enumerate(subs) if x.get("title") in EVENT_TITLES]
    return at[-1] + 1 if at else 0


# ---------------------------------------------------------------------------
# The close: flag lines only
# ---------------------------------------------------------------------------
def close_extras(built: dict, st, day: str, cutoff: str) -> None:
    from altdata import dm_drawdown, gold_event                 # noqa: PLC0415
    mech = built.get("mechanics")
    if mech is None:
        return
    g = _safe(lambda: gold_event.for_session(st, day, cutoff), "the gold event")
    d = _safe(lambda: dm_drawdown.for_session(st, day, cutoff), "the DM drawdown screen")
    lines = []
    if g and g.get("fired"):
        lines.append(g["line"])
        mech.setdefault("data", {})["_gold_event"] = g
    if d and d.get("fired"):
        lines += [e["line"] + "." for e in d["events"]]
        mech.setdefault("data", {})["_dm_event"] = d
    if not lines:
        return
    subs = mech.setdefault("subsections", [])
    subs.insert(_after_events(subs), {"title": "Gold and developed-market events",
                                      "paragraph_wanted": False, "lines": lines})
    for i, ln in enumerate(lines):
        mech["items"].append(_item(f"mech:asset_event:{i}", ln, 1, ln))


def store_rows(mech_data: dict, st, now: str) -> list[dict]:
    """The ledger rows for the close to write on a fired day (never on a dry run)."""
    from altdata import dm_drawdown, gold_event                 # noqa: PLC0415
    rows = []
    g = mech_data.pop("_gold_event", None)
    if g and g.get("fired"):
        gold = gold_event.read_series(st, now)["gold"]
        rows.append(gold_event.ledger_row(g, gold, now))
    d = mech_data.pop("_dm_event", None)
    if d and d.get("fired"):
        rows += dm_drawdown.ledger_rows(d, dm_drawdown.read_series(st, now), now)
    return rows


# ---------------------------------------------------------------------------
# The Weekly and the Monthly: the blocks over the edition's sessions
# ---------------------------------------------------------------------------
def _cell(legs: list[dict], lid: str) -> str:
    from altdata import gold_event                              # noqa: PLC0415
    x = next((l for l in legs if l["id"] == lid), None)
    return gold_event.leg_cell(x) if x else "—"


def gold_block(st, cutoff: str, first: str, last: str) -> dict:
    from altdata import gold_event                              # noqa: PLC0415
    cfg = gold_event.config()
    series = gold_event.read_series(st, cutoff, cfg)
    cache = gold_event.five_cache(series["gold"], cfg)
    days = [d for d, _ in series["gold"] if first <= d <= last]
    evs = [e for e in (gold_event.evaluate(series, d, cfg, cache) for d in days) if e["fired"]]
    sub: dict[str, Any] = {"title": GOLD_TITLE, "paragraph_wanted": False,
                           "not_tracked": [cfg["etf_flows_gap"]]}
    if not evs:
        sub["lines"] = [f"No gold event in the {len(days)} sessions from {first} to {last} "
                        f"stored (±{cfg['trigger']['one_day_pct']}% on a day, or a five-day "
                        f"move beyond its 95th percentile on five years)."]
        return sub
    rows = []
    for e in evs:
        legs = e["attribution"]["legs"]
        t = e["trigger"]
        rows.append([e["day"], (f"{t['one_day_pct']:+.2f}% (1d)" if t["one_day_fired"] else
                                f"{t['five_day_log_pct']:+.2f}% (5d)"),
                     _cell(legs, "real_10y"), _cell(legs, "dxy"), _cell(legs, "brent"),
                     _cell(legs, "central_banks")])
    sub["table"] = {"columns": ["Day", "Gold", "Real 10-year", "DXY", "Brent",
                                "Central banks"], "rows": rows}
    sub["lines"] = [e["attribution"]["residual"] for e in evs[-1:]] + [
        "A flag: no composite, no market-state input (item 73)."]
    return sub


def dm_block(st, cutoff: str, first: str, last: str) -> dict:
    from altdata import dm_drawdown                             # noqa: PLC0415
    cfg = dm_drawdown.config()
    series = dm_drawdown.read_series(st, cutoff, cfg)
    rows, n = [], 0
    for m in cfg["indices"]:
        pts = series.get(m["id"]) or []
        cache = dm_drawdown.dd_cache(pts, cfg)
        for d, _ in pts:
            if not first <= d <= last:
                continue
            n += 1
            tr = dm_drawdown.trigger(pts, d, cfg, cache)
            if not tr["fired"]:
                continue
            att = dm_drawdown.attribute(series, m, tr, cfg)
            w = tr["windows"][tr["lead"]]
            cells = dict((r[0].split(" (")[0], r[1]) for r in att["table"]["rows"])
            rows.append([f"{m['label']} ({m['source_label']})", d,
                         f"-{w['drawdown_pct']:.1f}% ({tr['lead']}s)",
                         cells.get(m["currency"]["label"], "—"),
                         next((r[1] for r in att["table"]["rows"]
                               if "10-year" in r[0] and "30-year" not in r[0]), "—"),
                         next((r[1] for r in att["table"]["rows"]
                               if r[0].startswith(cfg["us_session"]["label"])), "—")])
    sub: dict[str, Any] = {"title": DM_TITLE, "paragraph_wanted": False,
                           "not_tracked": list(cfg["gaps"].values())}
    labels = ", ".join(f"{m['label']} ({m['source_label']})" for m in cfg["indices"])
    if not rows:
        sub["lines"] = [f"No developed-market drawdown beyond its 95th percentile from "
                        f"{first} to {last} ({labels})."]
        return sub
    sub["table"] = {"columns": ["Index", "Day", "Drawdown", "Currency", "Local 10-year",
                                "Prior US session"], "rows": rows}
    sub["lines"] = ["A flag: no composite, no market-state input (item 73). An ETF proxy "
                    "is a US-listed fund in dollars, so its move holds the currency's."]
    return sub


def mechanics_subsections(subs: list[dict], st, cutoff: str, first: str, last: str
                          ) -> list[dict]:
    """The Weekly's and the Monthly's Mechanics, with both blocks after the events."""
    out = list(subs)
    add = [b for b in (_safe(lambda: gold_block(st, cutoff, first, last), "the gold block"),
                       _safe(lambda: dm_block(st, cutoff, first, last), "the DM block")) if b]
    at = _after_events(out) or len(out)
    return out[:at] + add + out[at:]


# ---------------------------------------------------------------------------
# The Monthly's slow layers: item 72
# ---------------------------------------------------------------------------
def place_slow(subs: list[dict], st, cutoff: str) -> list[dict]:
    """Item 72's line right after item 38's gold/equity ratio, else at the end."""
    from altdata import gold_13f                                # noqa: PLC0415
    from . import t1_rest_block                                 # noqa: PLC0415
    sub = _safe(lambda: gold_13f.subsection(st, cutoff), "the 13F gold line")
    if not sub:
        return subs
    out = list(subs)
    at = next((i for i, x in enumerate(out) if x.get("title") == t1_rest_block.GOLD_TITLE), None)
    out.insert(len(out) if at is None else at + 1, sub)
    return out
