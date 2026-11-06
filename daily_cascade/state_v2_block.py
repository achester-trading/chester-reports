"""
The market-state object v2's report-only blocks (6f tranche 3; rulings 10a and
11a of 24 Oct 2026; docs/briefs/6f-spec-draft-2026-10-24.md sections 4 and 5):
the tail families and the debt-cycle branch, READ from the stored object, never
recomputed.

    slow_subsections(st, now)     the Monthly's slow layers: the families' table
                                  and the debt-cycle block
    weekly_subsection(st, cutoff) the Weekly: one line

Report only. The families are never summed (the Twenty-Five's 0.2: no tail index)
and carry no probability; the debt-cycle branch prints `state: none` with its
observables. Nothing here reads a book, a packet or a dial.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)

TAIL_TITLE = "Tail families (the Twenty-Five; report only)"
DEBT_TITLE = "Debt-cycle branch (report only)"
CAL_TITLE = "Dial transitions (calibration; report only)"
DIM_CAL_TITLE = "Dimension transitions (unledgered; report only)"


def _safe(fn: Callable, what: str, default: Any = None) -> Any:
    try:
        return fn()
    except Exception:                                           # noqa: BLE001
        log.warning("%s faulted", what, exc_info=True)
        return default


def _object(st, cutoff: str) -> Optional[dict]:
    """The stored object as of the cutoff, from the store the caller holds; with
    no store, nothing (never the default database)."""
    if st is None:
        return None
    import regime                                               # noqa: PLC0415
    return regime.latest(as_of=cutoff, store=st)


def _num(v, fmt: str = "{:,.2f}") -> str:
    return "—" if v is None else fmt.format(v)


def tail_table(obj: dict) -> Optional[dict]:
    fams = obj.get("tail_families")
    if not fams:
        return None
    rows = []
    for f in fams:
        from altdata.numeral_audit import ordinal               # noqa: PLC0415
        movers = "; ".join(
            f"{m['metric']} {ordinal(m['percentile'])}"
            + (" (extreme)" if m.get("extreme") else "")
            for m in f.get("first_movers") or [] if m.get("percentile") is not None)
        unread = f.get("unread") or []
        rows.append([f"{f['family']}: {f['name']}",
                     ", ".join(str(s) for s in f.get("scenarios") or []),
                     f["state"], movers or "none stored",
                     (", ".join(unread) + " not stored") if unread else "—",
                     "none"])
    return {"columns": ["Family", "Scenarios", "State", "First movers (five-year percentile)",
                        "Not read", "Probability"], "rows": rows}


def tail_subsection(obj: dict) -> Optional[dict]:
    t = tail_table(obj)
    if not t:
        return None
    f0 = obj["tail_families"][0]
    return {"title": TAIL_TITLE, "paragraph_wanted": False, "table": t, "not_tracked": [],
            "lines": [f"State rule: {f0['state_rule']}.",
                      f"Probability: {f0['probability_reason']}. Families are never summed.",
                      f"From the market-state object of {obj.get('session')} "
                      f"({obj.get('method_version')})."]}


def debt_subsection(obj: dict) -> Optional[dict]:
    dc = obj.get("debt_cycle_branch")
    if not dc:
        return None
    rows = [[o["label"], _num(o.get("level")), _num(o.get("percentile_5y"), "{:.0f}"),
             o.get("observed_at") or "—"] for o in dc.get("observables") or []]
    return {"title": DEBT_TITLE, "paragraph_wanted": False, "not_tracked": [],
            "lines": [f"State: none -- {dc['reason']}. The observables print read-only."],
            "table": {"columns": ["Observable", "Level", "Five-year percentile", "As of"],
                      "rows": rows}}


def slow_subsections(st, now: str) -> list[dict]:
    """The Monthly's slow layers: the families' table, then the debt-cycle block."""
    def build():
        obj = _object(st, now)
        if not obj:
            return []
        return [s for s in (tail_subsection(obj), debt_subsection(obj)) if s]
    return _safe(build, "the v2 slow-layer blocks", []) or []


def weekly_line(obj: dict) -> Optional[str]:
    fams = obj.get("tail_families") or []
    if not fams:
        return None
    watch = [f"{f['family']} ({f['name']})" for f in fams if f["state"] == "watch"]
    unread = [f["family"] for f in fams if f["state"] == "not read"]
    head = (f"Tail families on watch: {', '.join(watch)}" if watch
            else "No tail family on watch")
    return (head + f" ({len(fams)} families"
            + (f"; not read: {', '.join(unread)}" if unread else "")
            + "; an extreme first mover, never a probability; report only).")


def weekly_subsection(st, cutoff: str) -> Optional[dict]:
    """The Weekly's one line."""
    def build():
        obj = _object(st, cutoff)
        ln = weekly_line(obj) if obj else None
        return ({"title": TAIL_TITLE, "lines": [ln], "paragraph_wanted": False}
                if ln else None)
    return _safe(build, "the tail-family line", None)


# ---------------------------------------------------------------------------
# 6f tranche 2 (a63; rulings 7a, 8a): the dials' transition reads
# ---------------------------------------------------------------------------
def _calibration(st, cutoff: str):
    from altdata import state_calibration as sc                 # noqa: PLC0415
    m = sc.matrices(st, cutoff)
    return sc, m, _object(st, cutoff)


def calibration_subsection(st, cutoff: str, dimensions: bool = False) -> list[dict]:
    """The Weekly's and the Monthly's table (dial x horizon); the Monthly adds the
    dimensions' table, unledgered. With no store, nothing."""
    if st is None:
        return []

    def build():
        sc, m, obj = _calibration(st, cutoff)
        # "not_tracked" on every sub-section: the Monthly's slow layers append
        # their faults to the last one (a63 CI 40119503077).
        out = [{"title": CAL_TITLE, "paragraph_wanted": False, "table": sc.table(m, obj),
                "not_tracked": [],
                "lines": [f"From {m['sessions']} stored objects under {m['method']}, "
                          f"each read as of its own availability; a row prints once "
                          f"its state has {sc.MIN_STARTS} independent starts."]}]
        if dimensions:
            out.append({"title": DIM_CAL_TITLE, "paragraph_wanted": False, "not_tracked": [],
                        "table": sc.dimension_table(m, obj),
                        "lines": ["Printed, never ledgered: only the dials are scored (8a)."]})
        return out
    return _safe(build, "the calibration tables", []) or []


def close_extras(built: dict, st, cutoff: str) -> None:
    """The daily close's one line, in the mechanics section."""
    mech = built.get("mechanics")
    if mech is None or st is None:
        return

    def build():
        sc, m, obj = _calibration(st, cutoff)
        return sc.close_line(m, obj)
    ln = _safe(build, "the calibration line")
    if not ln:
        return
    mech.setdefault("subsections", []).append(
        {"title": CAL_TITLE, "paragraph_wanted": False, "lines": [ln]})
