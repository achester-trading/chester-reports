"""
The close's outlooks: odds computed from the store, in the ledger BEFORE printing.
(docs/briefs/reporting-stack-brief-2026-10-02.md 1.3 rule 3 and 2.1 rule 6, T1)

    from daily_cascade import outlooks
    rows = outlooks.build(session, bar_store)            # computed, not recorded
    outlooks.record(rows, dry_run=False)                 # into the ledger
    outlooks.resolve_due(as_of)                          # idempotent, every close

A LEAN WITHOUT AN ENTRY IS REFUSED. The model never chooses a probability: each
outlook declared in config/reporting_stack.yaml is a RULE, its probability the
empirical frequency of that rule's outcome over SPY's stored daily closes, with
its n, clamped into the open interval the ledger requires. The entry is written
with a machine-readable resolution criterion before the edition is rendered;
the prose may print a probability only if it is an outlook's, and the audit
(stack_prose.outlook_misprints) refuses one that is not.

Resolution reads the same stored closes the probability was computed from, so
the Brier the Weekly prints grades exactly the claim that was made.
"""

from __future__ import annotations

import datetime as dt
import json
from typing import Any, Optional

from altdata import bars as bars_mod, session

LEDGER_SOURCE = "daily_close_outlook"


def _weekday_sessions(day: dt.date) -> list[dt.date]:
    """The trading sessions of `day`'s week, Monday to Friday."""
    start = day - dt.timedelta(days=day.weekday())
    out = []
    for i in range(5):
        d = start + dt.timedelta(days=i)
        ok = session.is_trading_session(d) if session.calendar_covers(d) \
            else d.weekday() < 5
        if ok:
            out.append(d)
    return out


def _closes(store, symbol_id: str, last_day: str, as_of=None) -> list[tuple[str, float]]:
    return [(str(r["observed_at"])[:10], r["close"])
            for r in bars_mod.daily(store, symbol_id, last_day, as_of)]


def _clamp(p: float) -> float:
    return round(min(0.98, max(0.02, p)), 2)


# ---------------------------------------------------------------------------
# The rules
# ---------------------------------------------------------------------------
def week_closing_low_holds(closes: list[tuple[str, float]], day: str) -> dict:
    """P(the week's lowest close so far holds through the week's last session)."""
    d = dt.date.fromisoformat(day)
    week = _weekday_sessions(d)
    if not week or d >= week[-1]:
        return {"skip": "today is the week's last session -- nothing left to hold"}
    pos = week.index(d) if d in week else None
    if pos is None:
        return {"skip": f"{day} is not a session"}
    by_week: dict[str, list[tuple[str, float]]] = {}
    for day_s, c in closes:
        dd = dt.date.fromisoformat(day_s)
        by_week.setdefault((dd - dt.timedelta(days=dd.weekday())).isoformat(),
                           []).append((day_s, c))
    this_key = (d - dt.timedelta(days=d.weekday())).isoformat()
    hits = n = 0
    for k, rows in by_week.items():
        if k == this_key or len(rows) <= pos + 1:
            continue
        low_so_far = min(c for _, c in rows[:pos + 1])
        n += 1
        hits += int(min(c for _, c in rows[pos + 1:]) >= low_so_far)
    cur = [c for day_s, c in by_week.get(this_key, []) if day_s <= day]
    if not cur or n < 20:
        return {"skip": f"too few comparable weeks stored (n={n})"}
    return {"probability": _clamp(hits / n), "n": n, "hits": hits,
            "level": round(min(cur), 2), "horizon_date": week[-1].isoformat(),
            "criterion": {"rule": "week_closing_low_holds", "symbol_id": "spy",
                          "from": day, "through": week[-1].isoformat(),
                          "level": round(min(cur), 2)}}


def stays_above_20d_next_session(closes: list[tuple[str, float]], day: str) -> dict:
    """P(the next close is on the same side of its 20-day average as today's)."""
    vals = [c for _, c in closes]
    if len(vals) < 60 or closes[-1][0] != day:
        return {"skip": f"{len(vals)} closes stored, today's not among them"
                if closes and closes[-1][0] != day else "fewer than 60 closes"}

    def side(i: int) -> int:
        ma = sum(vals[i - 19:i + 1]) / 20
        return 1 if vals[i] >= ma else -1
    hits = n = 0
    for i in range(19, len(vals) - 1):
        n += 1
        hits += int(side(i) == side(i + 1))
    today = side(len(vals) - 1)
    nxt = session.next_trading_session(day) if hasattr(
        session, "next_trading_session") else None
    if nxt is None:
        nd = dt.date.fromisoformat(day) + dt.timedelta(days=1)
        while not (session.is_trading_session(nd) if session.calendar_covers(nd)
                   else nd.weekday() < 5):
            nd += dt.timedelta(days=1)
        nxt = nd
    ma = round(sum(vals[-20:]) / 20, 2)
    return {"probability": _clamp(hits / n), "n": n, "hits": hits,
            "level": ma, "side": "above" if today > 0 else "below",
            "horizon_date": str(nxt)[:10],
            "criterion": {"rule": "stays_above_20d_next_session",
                          "symbol_id": "spy", "from": day,
                          "through": str(nxt)[:10],
                          "side": "above" if today > 0 else "below"}}


RULES = {"week_closing_low_holds": week_closing_low_holds,
         "stays_above_20d_next_session": stays_above_20d_next_session}


def build(day: str, store: bars_mod.BarStore, as_of: Optional[str] = None) -> list[dict]:
    """Every configured outlook for `day`, computed. Nothing is recorded."""
    cfg = bars_mod.load_config()
    out = []
    for o in cfg.get("outlooks") or []:
        closes = _closes(store, o["symbol"].lower(), day, as_of)
        res = RULES[o["rule"]](closes, day)
        row = {"id": o["id"], "symbol": o["symbol"], "rule": o["rule"],
               "kind": o.get("kind") or "base_rate"}
        if "skip" in res:
            out.append({**row, "state": "skipped", "reason": res["skip"]})
            continue
        side = f" ({res['side']} it, at {res['level']})" if "side" in res else \
            f" ({res['level']})"
        claim = f"{o['text']}{side}"
        out.append({**row, "state": "computed", "claim": claim,
                    "probability": res["probability"], "n": res["n"],
                    "base_rate_hits": res["hits"], "level": res["level"],
                    "horizon_date": res["horizon_date"],
                    "criterion": res["criterion"], "ledger_id": None})
    return out


def record(rows: list[dict], day: str, dry_run: bool = False,
           db_path: Optional[str] = None) -> list[dict]:
    """Write each computed outlook to the probability ledger, once per session.

    A re-run of the same session reuses the entry already written for it
    (scenario_set `outlook:<id>:<session>`) rather than emitting a second
    forecast of the same claim. A dry run records nothing and says so.
    """
    from altdata import probability_ledger as pl                # noqa: PLC0415
    if dry_run:
        for r in rows:
            if r["state"] == "computed":
                r["ledger_id"] = "dry-run (not recorded)"
        return rows
    with pl.ProbabilityLedger(db_path) as led:
        existing = {x.get("scenario_set"): x for x in led.all_rows()
                    if x.get("source") == LEDGER_SOURCE}
        for r in rows:
            if r["state"] != "computed":
                continue
            sset = f"outlook:{r['id']}:{day}"
            if sset in existing:
                r["ledger_id"] = existing[sset]["probability_id"]
                r["probability"] = existing[sset]["probability"]
                continue
            r["ledger_id"] = led.record(
                source=LEDGER_SOURCE, scenario_set=sset, claim=r["claim"],
                probability=r["probability"], horizon_date=r["horizon_date"],
                resolution_criterion=json.dumps(r["criterion"], sort_keys=True),
                emitted_by="daily_cascade.close_report")
    return rows


def resolve_one(crit: dict, store: bars_mod.BarStore,
                as_of: Optional[str] = None) -> Optional[int]:
    closes = [(d, c) for d, c in _closes(store, crit["symbol_id"], crit["through"],
                                         as_of) if d > crit["from"]]
    if not closes or closes[-1][0] < crit["through"]:
        return None                                   # not yet knowable
    if crit["rule"] == "week_closing_low_holds":
        return int(min(c for _, c in closes) >= float(crit["level"]))
    if crit["rule"] == "stays_above_20d_next_session":
        allc = [c for _, c in _closes(store, crit["symbol_id"], crit["through"],
                                      as_of)]
        ma = sum(allc[-20:]) / 20
        now_side = "above" if allc[-1] >= ma else "below"
        return int(now_side == crit["side"])
    return None


def resolve_due(as_of: Optional[str] = None, db_path: Optional[str] = None) -> dict:
    """Resolve every outlook past its horizon, from the stored closes. Idempotent."""
    from altdata import probability_ledger as pl                # noqa: PLC0415
    out: dict[str, Any] = {"resolved": [], "waiting": []}
    cutoff = as_of or session.utc_iso()
    with pl.ProbabilityLedger(db_path) as led, bars_mod.BarStore(db_path) as st:
        for r in led.due(cutoff):
            if r["source"] != LEDGER_SOURCE:
                continue
            res = resolve_one(json.loads(r["resolution_criterion"]), st, cutoff)
            if res is None:
                out["waiting"].append(r["probability_id"])
                continue
            out["resolved"].append(led.resolve(r["probability_id"], res,
                                               note="outlook rule, stored closes",
                                               resolved_at=cutoff))
    return out
