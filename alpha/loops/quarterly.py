"""
The quarterly meta-loop (X-3.7; the change order's section 5; lenses-group-b,
18 Oct 2026) -- does the loop's learning earn its keep?

    python -m alpha.loops.quarterly [--quarter 2026Q4] [--as-of ISO]
                                    [--ledger PATH] [--store PATH] [--dry-run]

FOR EVERY LOOP CHANGE OF THE QUARTER, THE COUNTERFACTUAL FROM THE SAME STORED
PRICES: what the lab would have earned without the change. The loop's changes
are the weekly loop's two adaptive acts, each a loop_events row:

  refit_accepted  new parameters for an engine. The engine's own strategy is
                  re-run over its rows from the change to the next re-fit (or
                  the quarter's end), read from the store as of the quarter's
                  end, once at the new parameters and once at the old (the
                  event's `counterfactual`): contribution = (sum of returns at
                  the new less at the old) x the engine's capital that day.
  rebalance       new allocator weights. Each engine's recorded daily return
                  (its equity index, the paper book's) over the days the
                  weights held, times the notional, times the change in weight:
                  contribution = sum of r_d x notional x (w_after - w_before).
                  An engine weighted to zero has no paper return to scale and
                  is listed as not computable, never guessed.

Every other loop_events kind is not a learning choice -- the governor's moves
are the constitution's rules, the register's and the harness's are bookkeeping
-- and is listed as such, uncounted. A reversed event counts nothing.

THE NET CONTRIBUTION is the sum. If it is NEGATIVE, for the next quarter the
re-fit bounds are narrowed and the cadence slowed (config/alpha.yaml
`meta_loop:`), written as ONE loop event of its own, kind `meta_tighten`, with
the before, the after and the quarter it applies to; the weekly loop reads it
(`state()`, `refit_due()`, `effective_ranges()`). A positive or zero
contribution changes nothing and writes nothing. One review per quarter.

It reads the store read-only and alpha.db, and writes alpha.db's loop_events
only (one row, on a negative quarter). It writes no candidate, packet, dial,
band, tell or narrative, reads no report, and places nothing.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
from typing import Any, Callable, Optional

from altdata import session

from .. import book
from .. import config as acfg
from ..ledger import Ledger
from ..store import ReadOnlyStore

log = logging.getLogger(__name__)
LOOP = "quarterly"
KIND = "meta_tighten"
COUNTED = ("refit_accepted", "rebalance")
REFIT_DECISIONS = ("refit_accepted", "refit_rejected", "refit_out_of_range")


# ---------------------------------------------------------------------------
# Quarters
# ---------------------------------------------------------------------------
def quarter_of(day: str) -> str:
    d = dt.date.fromisoformat(str(day)[:10])
    return f"{d.year}Q{(d.month - 1) // 3 + 1}"


def bounds(q: str) -> tuple[str, str]:
    """(first day, last day) of a quarter like 2026Q4."""
    y, n = int(q[:4]), int(q[-1])
    first = dt.date(y, 3 * (n - 1) + 1, 1)
    nxt = dt.date(y + (n == 4), (3 * n) % 12 + 1, 1)
    return first.isoformat(), (nxt - dt.timedelta(days=1)).isoformat()


def next_quarter(q: str) -> str:
    y, n = int(q[:4]), int(q[-1])
    return f"{y + (n == 4)}Q{n % 4 + 1}"


def previous_quarter(q: str) -> str:
    y, n = int(q[:4]), int(q[-1])
    return f"{y - (n == 1)}Q{(n - 2) % 4 + 1}"


def settings(cfg: Optional[dict] = None) -> dict:
    return dict((cfg or acfg.settings()).get("meta_loop") or {})


def _day(e: dict) -> str:
    return session.session_date(e["as_of"]) if "T" in str(e["as_of"]) else str(e["as_of"])[:10]


def _j(v: Any) -> Any:
    return json.loads(v) if isinstance(v, str) and v else (v or {})


def covered(ledger: Ledger, q: str) -> bool:
    """The lab has run through all of the quarter: its first loop event is on or
    before the quarter's first day."""
    r = ledger.one("SELECT MIN(as_of) AS a FROM loop_events")
    return bool(r and r["a"]) and str(r["a"])[:10] <= bounds(q)[0]


def last_closed(ledger: Ledger, as_of: str) -> Optional[str]:
    """The newest quarter that has ended by `as_of` and that the lab ran through
    whole, or None ("no quarter closed yet")."""
    q = previous_quarter(quarter_of(session.session_date(as_of)))
    return q if covered(ledger, q) else None


# ---------------------------------------------------------------------------
# The counterfactuals
# ---------------------------------------------------------------------------
def _events(ledger: Ledger, q: str) -> list[dict]:
    first, last = bounds(q)
    return [e for e in ledger.q("SELECT * FROM loop_events ORDER BY id")
            if first <= _day(e) <= last]


def _refit(ledger: Ledger, store, e: dict, evs: list[dict], q_last: str,
           engines: dict) -> dict:
    eid = e["engine"]
    eng = engines.get(eid)
    if eng is None or not (hasattr(eng, "refit_rows") and hasattr(eng, "strategy")):
        return {"computable": False, "why": f"{eid} exposes no re-fit hooks here"}
    start = _day(e)
    later = [x for x in evs if x["engine"] == eid and x["kind"] == "refit_accepted"
             and x["id"] > e["id"] and x["reversed_by"] is None]
    end = _day(later[0]) if later else q_last
    rows = [r for r in sorted(eng.refit_rows(store, f"{q_last}T23:59:59+00:00"),
                              key=lambda r: r["day"]) if start < r["day"] <= end]
    if not rows:
        return {"computable": False, "why": f"no {eid} rows between {start} and {end}"}
    strat = eng.strategy()
    new = _j(e["after"]).get("params") or {}
    old = _j(e["counterfactual"]).get("params") or {}
    ra, rc = sum(strat.returns(rows, new)), sum(strat.returns(rows, old))
    eng_row = ledger.engine(eid) or {"id": eid, "min_size": 0.0}
    cap = book.capital(ledger, eng_row, start)
    return {"computable": True, "window": [start, end], "rows": len(rows),
            "return_after": ra, "return_counterfactual": rc, "capital": cap,
            "contribution": (ra - rc) * cap}


def _rebalance(ledger: Ledger, e: dict, evs: list[dict], q_last: str) -> dict:
    after = (_j(e["after"]).get("weights") or {})
    before = _j(e["counterfactual"]).get("weights") or _j(e["before"]) or {}
    start = _day(e)
    later = [x for x in evs if x["kind"] == "rebalance" and x["id"] > e["id"]
             and x["reversed_by"] is None]
    end = _day(later[0]) if later else q_last
    notional = float(acfg.settings().get("notional_capital") or 0)
    total, per, uncounted = 0.0, {}, []
    for eid, wa in after.items():
        wb = before.get(eid)
        if wb is None:
            eng = ledger.engine(eid)
            wb = float(eng["min_size"]) if eng else 0.0
        if float(wa) == 0.0:
            if float(wb) != 0.0:
                uncounted.append(f"{eid}: weighted to zero, no paper return to scale")
            continue
        rets = {d: r for d, r in book.daily_returns(ledger, eid).items() if start < d <= end}
        c = sum(rets.values()) * notional * (float(wa) - float(wb))
        per[eid] = {"w_before": float(wb), "w_after": float(wa), "days": len(rets),
                    "contribution": c}
        total += c
    return {"computable": True, "window": [start, end], "engines": per,
            "uncounted": uncounted, "contribution": total}


def review(ledger: Ledger, store, q: str, engines: Optional[dict] = None,
           registry_path=None) -> dict:
    """The quarter's loop changes, each with its counterfactual, and the net."""
    if engines is None:
        from .weekly import _loaded                             # noqa: PLC0415
        engines = _loaded(ledger, registry_path)
    q_last = bounds(q)[1]
    evs = _events(ledger, q)
    changes, other = [], {}
    for e in evs:
        if e["kind"] not in COUNTED:
            other[e["kind"]] = other.get(e["kind"], 0) + 1
            continue
        if e["reversed_by"] is not None:
            changes.append({"id": e["id"], "kind": e["kind"], "engine": e["engine"],
                            "day": _day(e), "computable": False,
                            "why": f"reversed by event {e['reversed_by']}"})
            continue
        cf = (_refit(ledger, store, e, evs, q_last, engines) if e["kind"] == "refit_accepted"
              else _rebalance(ledger, e, evs, q_last))
        changes.append({"id": e["id"], "kind": e["kind"], "engine": e["engine"],
                        "day": _day(e), **cf})
    counted = [c for c in changes if c.get("computable")]
    net = sum(c["contribution"] for c in counted)
    return {"quarter": q, "events": len(evs), "changes": changes,
            "net_contribution": net, "counted": len(counted),
            "uncounted": [c for c in changes if not c.get("computable")],
            "not_loop_choices": other}


# ---------------------------------------------------------------------------
# The adjustment, and what the weekly loop reads
# ---------------------------------------------------------------------------
def _current_params(ledger: Ledger, eid: str) -> dict:
    for r in ledger.q("SELECT kind, after FROM loop_events WHERE engine=? AND kind IN "
                      "('refit_accepted','refit_rejected','refit_out_of_range') AND "
                      "reversed_by IS NULL ORDER BY id DESC", (eid,)):
        a = _j(r["after"])
        p = a.get("params") if r["kind"] == "refit_accepted" else a.get("current")
        if p:
            return p
    return {}


def narrowed(ranges: dict, params: dict, factor: float) -> dict:
    """Each numeric range pulled toward the current value: each side keeps
    `factor` of its distance from it. A parameter without a numeric current
    value or range is left as it is."""
    out = {}
    for k, rg in (ranges or {}).items():
        v = params.get(k)
        if (not isinstance(rg, (list, tuple)) or len(rg) != 2 or
                not isinstance(v, (int, float)) or isinstance(v, bool)):
            out[k] = list(rg) if isinstance(rg, (list, tuple)) else rg
            continue
        lo, hi = float(rg[0]), float(rg[1])
        out[k] = [v - (v - lo) * factor, v + (hi - v) * factor]
    return out


def state(ledger: Ledger, as_of: str) -> dict:
    """The meta-loop's adjustment in force at `as_of`: the newest unreversed
    meta_tighten that applies to as_of's quarter, else the defaults (weekly, the
    validated ranges)."""
    q = quarter_of(session.session_date(as_of))
    for r in ledger.q("SELECT * FROM loop_events WHERE kind=? AND reversed_by IS NULL "
                      "ORDER BY id DESC", (KIND,)):
        a = _j(r["after"])
        if a.get("applies_to") == q:
            return {"quarter": q, "refit_every_weeks": int(a["refit_every_weeks"]),
                    "bounds": a.get("bounds") or {}, "event_id": r["id"]}
    return {"quarter": q, "refit_every_weeks": 1, "bounds": {}, "event_id": None}


def effective_ranges(ledger: Ledger, engine: dict, as_of: str) -> dict:
    """The ranges a re-fit must stay inside: the validated ones, or the
    meta-loop's narrowed ones where an adjustment is in force."""
    st = state(ledger, as_of)
    return (st["bounds"].get(engine["id"]) or engine.get("validated_ranges") or {})


def refit_due(ledger: Ledger, engine_id: str, as_of: str) -> tuple[bool, str]:
    """(due, why): a re-fit is due when the cadence in force has passed since the
    engine's last re-fit decision."""
    st = state(ledger, as_of)
    every = int(st["refit_every_weeks"])
    if every <= 1:
        return True, "weekly"
    r = ledger.one("SELECT as_of FROM loop_events WHERE engine=? AND kind IN "
                   "('refit_accepted','refit_rejected','refit_out_of_range') "
                   "ORDER BY id DESC LIMIT 1", (engine_id,))
    if not r:
        return True, f"every {every} weeks; no earlier re-fit"
    days = (dt.date.fromisoformat(session.session_date(as_of))
            - dt.date.fromisoformat(str(r["as_of"])[:10])).days
    due = days >= 7 * every - 3
    return due, (f"the meta-loop slowed the re-fit to every {every} weeks for "
                 f"{st['quarter']} (event {st['event_id']}); {days} days since the last")


def adjust(ledger: Ledger, rv: dict, as_of: str, cfg: Optional[dict] = None,
           dry_run: bool = False) -> Optional[dict]:
    """On a negative quarter, the next quarter's bounds and cadence, written as
    one meta_tighten event. A positive or zero quarter returns None and writes
    nothing; a quarter already adjusted is not adjusted twice."""
    if rv["net_contribution"] >= 0:
        return None
    q, nq = rv["quarter"], next_quarter(rv["quarter"])
    for r in ledger.q("SELECT after FROM loop_events WHERE kind=?", (KIND,)):
        if _j(r["after"]).get("reviewed") == q:
            return None
    m = settings(cfg)
    f = float(m.get("narrow_factor", 0.5))
    cur = state(ledger, f"{bounds(q)[1]}T12:00:00+00:00")
    every = min(int(cur["refit_every_weeks"]) * int(m.get("cadence_multiplier", 2)),
                int(m.get("max_refit_every_weeks", 8)))
    engines = sorted({c["engine"] for c in rv["changes"]
                      if c["kind"] == "refit_accepted" and c["engine"]})
    new_bounds, before_bounds = {}, {}
    for eid in engines:
        e = ledger.engine(eid) or {"id": eid}
        rg = cur["bounds"].get(eid) or e.get("validated_ranges") or {}
        before_bounds[eid] = rg
        new_bounds[eid] = narrowed(rg, _current_params(ledger, eid), f)
    after = {"reviewed": q, "applies_to": nq, "refit_every_weeks": every,
             "bounds": new_bounds, "net_contribution": rv["net_contribution"],
             "narrow_factor": f}
    out = {"before": {"refit_every_weeks": cur["refit_every_weeks"],
                      "bounds": before_bounds}, "after": after}
    if not dry_run:
        out["event_id"] = ledger.event(
            LOOP, KIND, as_of, None, before=out["before"], after=after,
            counterfactual={"refit_every_weeks": cur["refit_every_weeks"],
                            "bounds": before_bounds})
    return out


def run_quarter(ledger: Ledger, store, q: str, as_of: str, engines: Optional[dict] = None,
                cfg: Optional[dict] = None, dry_run: bool = False) -> dict:
    rv = review(ledger, store, q, engines)
    rv["adjustment"] = adjust(ledger, rv, as_of, cfg, dry_run)
    return rv


def due_quarter(ledger: Ledger, as_of: str, cfg: Optional[dict] = None) -> Optional[str]:
    """The quarter the weekly loop should have reviewed now: the last closed,
    covered quarter, inside the review window after its end."""
    q = last_closed(ledger, as_of)
    if not q:
        return None
    days = (dt.date.fromisoformat(session.session_date(as_of))
            - dt.date.fromisoformat(bounds(q)[1])).days
    return q if days <= int(settings(cfg).get("review_window_days", 21)) else None


def run(as_of: Optional[str] = None, quarter: Optional[str] = None, ledger_path=None,
        store_path=None, dry_run: bool = False) -> dict:
    as_of = as_of or session.utc_iso(timespec="microseconds")
    with Ledger(ledger_path) as lg:
        q = quarter or last_closed(lg, as_of)
        if not q:
            return {"quarter": None, "state": "no quarter closed yet"}
        st = ReadOnlyStore(store_path)
        try:
            return run_quarter(lg, st, q, as_of, dry_run=dry_run)
        finally:
            st.close()


def _main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="The Alpha Lab's quarterly meta-loop")
    ap.add_argument("--quarter")
    ap.add_argument("--as-of")
    ap.add_argument("--ledger")
    ap.add_argument("--store")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    print(json.dumps(run(a.as_of, a.quarter, a.ledger, a.store, a.dry_run), indent=2,
                     default=str))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
