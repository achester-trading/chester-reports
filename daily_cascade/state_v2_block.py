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


def _safe(fn: Callable, what: str, default: Any = None) -> Any:
    try:
        return fn()
    except Exception:                                           # noqa: BLE001
        log.warning("%s faulted", what, exc_info=True)
        return default


def _object(st, cutoff: str) -> Optional[dict]:
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
        movers = "; ".join(
            f"{m['metric']} {_num(m.get('percentile'), '{:.0f}')}th"
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
    return {"title": TAIL_TITLE, "paragraph_wanted": False, "table": t,
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
    return {"title": DEBT_TITLE, "paragraph_wanted": False,
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
