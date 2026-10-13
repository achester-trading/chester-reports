"""
THE BOOK, SECTION 10: Book B's candidates and the sitting's productivity
(W-1.3a items 3.8 and 3.6; change order of 11 Oct 2026, section 4, amended 12 Oct).

    from daily_cascade import book_b
    scan = book_b.scanner_output(ending, db_path)    # None until the scanner merges
    flow = book_b.sitting_flow(ending, db_path, scan, prior_printed)
    subs = book_b.subsections(scan, flow)

CANDIDATES FOR THE SITTING (PAPER), item 3.8. Book B's candidates print as a
ranked list, one line each: the instrument, the direction, the thesis in a clause,
the catalyst and its date, the invalidation, the horizon and the size band. RANKED
BY THE SCANNER'S OWN SCORE; the Weekly adds no score of its own. A candidate the
prior sitting passed over prints once more with its reason, then drops (it is not
carried in this edition's printed list, so the next edition does not see it).

  THE HOOK -- ACTIVATES WHEN THE SCANNER MERGES. The Book B scanner (Audit #4
  agenda item 3: "reads Friday's close, writes Book B candidates to the register
  as drafts with level, invalidation, time stop, falsifiers and the gate's
  pre-check") is not built. Until a module SCANNER_MODULE exposes
  `candidates(ending, db_path=None) -> list[dict]`, the block prints NO_SCANNER.
  The renderer is built against this shape, one dict a candidate:

      decision_id    the register draft the scanner wrote (REQUIRED: a candidate
                     that did not pass the register is not printed -- the
                     register is where the Brookfield restriction is enforced)
      instrument, direction, thesis, setup_id
      catalyst, catalyst_date        the event and its ISO date
      invalidation   the level or event that kills the thesis
      horizon        e.g. "swing (time stop 2026-10-30)"
      size_band      e.g. "0.25-0.5% of NAV"
      score          the scanner's rank score, higher first

  Belt and braces: an instrument the restriction list names is never printed,
  whatever the scanner wrote, and the count of any so dropped is footnoted.

THE PRODUCTIVITY LINE, item 3.6, beside the compliance line: triggers fired ->
reviewed -> packets drafted -> approved, four counts, from the scanner's output
and the register:

  fired      the scanner's candidates this week ("—" until it exists)
  reviewed   decisions the operator acted on (an operator action on a row
             created this week, or on the lineage of a candidate the prior
             edition printed)
  drafted    decisions entered this week that are not supersessions -- each
             carries its packet
  approved   lineages that went active this week (the attention count's own)

A PASSED-OVER ROW for every reviewed signal that did not reach a packet that was
approved, with its reason from the register's declined row (its abstention
reason or note) where recorded, else "no reason recorded". The decisions count is
captioned "register decisions (chat rulings on briefs are not book decisions)".
"""

from __future__ import annotations

import datetime as dt
import importlib
import logging
from typing import Any, Optional

log = logging.getLogger(__name__)

SCANNER_MODULE = "altdata.book_b_scanner"
NO_SCANNER = "no scanner yet — the first candidates arrive with Book B"
HEADING = "Candidates for the sitting (paper)"
PRODUCTIVITY = "Productivity: triggers fired → reviewed → packets drafted → approved"
DECISIONS_CAPTION = ("register decisions (chat rulings on briefs are not book "
                     "decisions)")
NO_REASON = "no reason recorded"
FIELDS = ("decision_id", "instrument", "direction", "thesis", "catalyst",
          "catalyst_date", "invalidation", "horizon", "size_band", "score")


# ---------------------------------------------------------------------------
# The scanner's output
# ---------------------------------------------------------------------------
def scanner_output(ending: str, db_path: Optional[str] = None,
                   module: str = SCANNER_MODULE) -> Optional[list[dict]]:
    """The scanner's candidates for the week ending `ending`, or None while no
    scanner exists. A scanner that exists and fails is logged and read as
    None too: the edition prints, and says no candidates were read."""
    try:
        mod = importlib.import_module(module)
    except ImportError:
        return None
    try:
        return list(mod.candidates(ending, db_path=db_path) or [])
    except Exception:                                           # noqa: BLE001
        log.warning("the Book B scanner failed", exc_info=True)
        return None


def _restricted(instrument: Any) -> bool:
    try:
        from register import instruments                        # noqa: PLC0415
        return instruments.restrictions().is_restricted(instrument)
    except Exception:                                           # noqa: BLE001
        # The list unreadable: refuse to print rather than risk it.
        return True


def printable(scan: Optional[list[dict]]) -> tuple[list[dict], dict]:
    """The candidates that may print, ranked by the scanner's score, and the
    counts of those that may not (no register draft; a restricted instrument)."""
    keep, drop = [], {"no_register_draft": 0, "restricted": 0}
    for c in scan or []:
        if not c.get("decision_id"):
            drop["no_register_draft"] += 1
        elif _restricted(c.get("instrument")):
            drop["restricted"] += 1
        else:
            keep.append(c)
    keep.sort(key=lambda c: -(c.get("score") if isinstance(c.get("score"),
                                                           (int, float)) else -1e9))
    return keep, drop


def candidate_line(n: int, c: dict) -> str:
    cat = c.get("catalyst") or "no catalyst named"
    if c.get("catalyst_date"):
        cat += f" ({c['catalyst_date']})"
    sc = c.get("score")
    return (f"{n}. {c.get('instrument')} {c.get('direction')} — {c.get('thesis')}; "
            f"catalyst: {cat}; invalidation: {c.get('invalidation') or 'none named'}; "
            f"horizon: {c.get('horizon') or 'not stated'}; size band: "
            f"{c.get('size_band') or 'not stated'}"
            + (f" (scanner score {sc:g})" if isinstance(sc, (int, float)) else "")
            + ".")


def passed_line(c: dict) -> str:
    return (f"Passed over at the sitting: {c.get('instrument')} "
            f"{c.get('direction')} — {c.get('reason') or NO_REASON}.")


# ---------------------------------------------------------------------------
# The register: what the sitting did
# ---------------------------------------------------------------------------
def _week(ending: str) -> tuple[str, str]:
    end = dt.date.fromisoformat(ending[:10])
    mon = end - dt.timedelta(days=end.weekday())
    return mon.isoformat(), (mon + dt.timedelta(days=6)).isoformat()


def register_rows(db_path: Optional[str] = None) -> list[dict]:
    try:
        from register.store import Register                     # noqa: PLC0415
        with Register(db_path) as reg:
            return [dict(r) for r in reg.conn.execute("SELECT * FROM decisions")]
    except Exception:                                           # noqa: BLE001
        log.warning("the register is unreadable", exc_info=True)
        return []


def lineage(rows: list[dict], decision_id: str) -> list[dict]:
    """The decision and every row that superseded it, oldest first."""
    by = {r["id"]: r for r in rows}
    out, cur, seen = [], by.get(decision_id), set()
    while cur and cur["id"] not in seen:
        seen.add(cur["id"])
        out.append(cur)
        cur = by.get(cur.get("superseded_by")) if cur.get("superseded_by") else None
    return out


def outcome(chain: list[dict]) -> dict:
    """reviewed / approved / declined, and the reason a declined row carries."""
    approved = any(r.get("status") in ("active", "closed") for r in chain)
    declined = next((r for r in reversed(chain) if r.get("status") == "declined"), None)
    reviewed = bool(declined) or approved or any(r.get("operator_action")
                                                 for r in chain)
    reason = None
    if declined is not None:
        why = [x for x in (declined.get("abstention_reason"), declined.get("note")) if x]
        reason = "; ".join(str(x).replace("_", " ") for x in why) or None
    return {"reviewed": reviewed, "approved": approved,
            "declined": declined is not None, "reason": reason}


def sitting_flow(ending: str, db_path: Optional[str], scan: Optional[list[dict]],
                 prior_printed: Optional[list[dict]] = None,
                 approved: Optional[int] = None,
                 rows: Optional[list[dict]] = None) -> dict:
    """Item 3.6's four counts and the passed-over rows; item 3.8's passed-over
    candidates (the prior edition's printed candidates the sitting did not
    approve)."""
    rows = register_rows(db_path) if rows is None else rows
    mon, sun = _week(ending)
    week = [r for r in rows if mon <= str(r.get("created_at"))[:10] <= sun]
    supersessions = {r["superseded_by"] for r in rows if r.get("superseded_by")}
    drafted = [r for r in week if r["id"] not in supersessions]
    heads = {}
    for r in rows:                       # each row's lineage root
        if r["id"] not in supersessions:
            for x in lineage(rows, r["id"]):
                heads[x["id"]] = r["id"]
    reviewed_roots, passed = set(), []
    for r in week:
        if r.get("operator_action") or r.get("status") == "declined":
            reviewed_roots.add(heads.get(r["id"], r["id"]))
    prior_ids = {c.get("decision_id") for c in prior_printed or [] if c.get("decision_id")}
    reviewed_roots |= {heads.get(i, i) for i in prior_ids
                       if outcome(lineage(rows, heads.get(i, i)))["reviewed"]}
    by = {r["id"]: r for r in rows}
    this_week = {c.get("decision_id") for c in scan or []}
    passed_candidates = []
    for root in sorted(reviewed_roots):
        o = outcome(lineage(rows, root))
        if o["approved"]:
            continue
        r0 = by.get(root) or {}
        row = {"decision_id": root, "instrument": r0.get("instrument"),
               "direction": r0.get("direction"), "reason": o["reason"] or NO_REASON}
        if root in prior_ids:
            if root not in this_week:
                passed_candidates.append(row)
        else:
            passed.append(row)
    if approved is None:
        approved = sum(1 for r in week if r.get("status") == "active")
    open_n = sum(1 for r in rows if r.get("status") in ("active", "draft")
                 and not r.get("superseded_by"))
    return {"fired": None if scan is None else len(scan),
            "reviewed": len(reviewed_roots), "drafted": len(drafted),
            "approved": approved, "decisions_open": open_n,
            "passed_over": passed, "passed_candidates": passed_candidates}


# ---------------------------------------------------------------------------
# The blocks
# ---------------------------------------------------------------------------
def productivity_line(flow: dict) -> str:
    """Item 3.6: the four counts, and the decisions count with its caption."""
    f = "—" if flow["fired"] is None else flow["fired"]
    return (f"Triggers fired {f} → reviewed {flow['reviewed']} → packets drafted "
            f"{flow['drafted']} → approved {flow['approved']}; "
            f"{DECISIONS_CAPTION}: {flow['decisions_open']} open.")


def subsections(scan: Optional[list[dict]], flow: dict) -> tuple[list[dict], dict]:
    """The candidates block and the productivity block, and what the edition
    archives for the next week (the candidates it printed)."""
    keep, drop = printable(scan)
    if scan is None:
        lines = [NO_SCANNER]
    else:
        lines = [candidate_line(n, c) for n, c in enumerate(keep, start=1)] or \
            ["The scanner fired no candidate this week."]
    lines += [passed_line(c) for c in flow.get("passed_candidates") or []]
    notes = []
    if drop["no_register_draft"]:
        notes.append(f"{drop['no_register_draft']} candidate(s) without a register "
                     f"draft not printed: a candidate prints only after the register "
                     f"has accepted it.")
    if drop["restricted"]:
        notes.append(f"{drop['restricted']} candidate(s) on a restricted instrument "
                     f"not printed.")
    if scan is None:
        notes.append("The candidates block activates when the Book B scanner "
                     "merges; until then nothing fires.")
    notes.append("Paper candidates for the sitting: nothing here is an order.")
    cand = {"title": HEADING, "lines": lines, "notes": notes,
            "candidates": [{k: c.get(k) for k in FIELDS} for c in keep]}
    prod = {"title": PRODUCTIVITY, "lines": [productivity_line(flow)],
            "table": ({"columns": ["Passed over", "Direction", "Reason"],
                       "rows": [[r["instrument"], r["direction"], r["reason"]]
                                for r in flow["passed_over"]]}
                      if flow["passed_over"] else None)}
    return [cand, prod], {"printed": cand["candidates"]}
