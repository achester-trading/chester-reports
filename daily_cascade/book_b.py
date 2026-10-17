"""
THE BOOK, SECTION 10: Book B's candidates and the sitting's productivity
(W-1.3a items 3.8 and 3.6; change order of 11 Oct 2026, section 4, amended 12 Oct).

    from daily_cascade import book_b
    run = book_b.scanner_run(ending, db_path, cutoff=now, calendar=cal, walls=w)
    scan = None if run is None else run["candidates"]
    flow = book_b.sitting_flow(ending, db_path, scan, prior_printed)
    subs, kept = book_b.subsections(scan, flow, run)

CANDIDATES FOR THE SITTING (PAPER), item 3.8. Book B's candidates print as a
ranked list, one line each: the instrument, the direction, the thesis in a clause,
the catalyst and its date, the invalidation, the horizon and the size band, and
beside them the scanner's own terms -- the pivot's parameters, R, the time stop,
"against the tape", a crowding WARNING, the entry timing, the counter-thesis.
RANKED BY THE SCANNER'S OWN SCORE; the Weekly adds no score of its own. The top
ten print; every candidate below them goes to the reference tier. A candidate the
prior sitting passed over prints once more with its reason, then drops (it is not
carried in this edition's printed list, so the next edition does not see it).

  THE HOOK. The Book B scanner (altdata/book_b_scanner.py; the brief of 12 Oct
  2026) runs inside the Weekly's build over Friday's close. `scanner_run` reads
  its whole result (the ranked candidates, the refused, the parameters as set);
  `scanner_output` the candidates alone, through the module's
  `candidates(ending, db_path=None) -> list[dict]`. A scanner that fails is
  logged, and the block prints NO_SCANNER.

  THE CANDIDATE'S SHAPE (ruled 12 Oct 2026, the W-1.3 follow-up): the register's
  DRAFT fields as the Alternative Assets change order section 4.1 item 10 lists
  them, plus the setup, the scanner's score, the catalyst and an id:

      candidate_id   the scanner's own id (REQUIRED)
      instrument, direction, thesis, edge, horizon, size, invalidation,
      counter_thesis                 the register's draft fields
      setup_id       a family config/setups.yaml declares (EL-1; REQUIRED)
      score          the scanner's rank score, higher first
      catalyst, catalyst_date        the event and its ISO date
      decision_id    NULL on every candidate: it is assigned only when the
                     sitting approves a packet
      risk_usd       the dollars from entry to invalidation at the printed size,
                     on the paper capital (config/risk_limits.yaml), computed by
                     the scanner so the order gate (EL-2/3) never delays a
                     taken candidate for a missing input (follow-up 5, 13 Oct)

  An instrument the restriction list names is never printed, whatever the
  scanner wrote -- the same check the register makes at write time -- and the
  count of any so dropped is footnoted. A candidate with no id or no declared
  setup is not printed either, and counted.

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
NO_SCANNER = "the Book B scanner could not be read this week — no candidates"
REFERENCE_TITLE = "Book B candidates below the top ten (paper)"
HEADING = "Candidates for the sitting (paper)"
PRODUCTIVITY = "Productivity: triggers fired → reviewed → packets drafted → approved"
DECISIONS_CAPTION = ("register decisions (chat rulings on briefs are not book "
                     "decisions)")
NO_REASON = "no reason recorded"
FIELDS = ("candidate_id", "instrument", "direction", "thesis", "edge", "horizon",
          "size", "invalidation", "counter_thesis", "setup_id", "score",
          "catalyst", "catalyst_date", "decision_id", "risk_usd")


# ---------------------------------------------------------------------------
# The scanner's output
# ---------------------------------------------------------------------------
def scanner_run(ending: str, db_path: Optional[str] = None,
                module: str = SCANNER_MODULE, **kw) -> Optional[dict]:
    """The scanner's whole result for the week ending `ending` -- `candidates`
    ranked, and where the module gives them the refused, the reference tier and
    the parameters line -- or None when the scanner cannot be imported or
    fails (logged): the edition prints, and says no candidates were read."""
    try:
        mod = importlib.import_module(module)
    except ImportError:
        return None
    try:
        if hasattr(mod, "scan"):
            res = dict(mod.scan(ending, db_path, **kw))
            res["candidates"] = list(res.get("candidates") or [])
            return res
        return {"candidates": list(mod.candidates(ending, db_path=db_path) or [])}
    except Exception:                                           # noqa: BLE001
        log.warning("the Book B scanner failed", exc_info=True)
        return None


def scanner_output(ending: str, db_path: Optional[str] = None,
                   module: str = SCANNER_MODULE, **kw) -> Optional[list[dict]]:
    """The scanner's candidates alone, or None (see scanner_run)."""
    run = scanner_run(ending, db_path, module, **kw)
    return None if run is None else run["candidates"]


def _restricted(instrument: Any) -> bool:
    try:
        from register import instruments                        # noqa: PLC0415
        return instruments.restrictions().is_restricted(instrument)
    except Exception:                                           # noqa: BLE001
        # The list unreadable: refuse to print rather than risk it.
        return True


def _setups() -> tuple:
    try:
        from register.store import setup_ids                    # noqa: PLC0415
        return setup_ids()
    except Exception:                                           # noqa: BLE001
        return ()


def printable(scan: Optional[list[dict]]) -> tuple[list[dict], dict]:
    """The candidates that may print, ranked by the scanner's score, and the
    counts of those that may not (no id or no declared setup; a restricted
    instrument)."""
    keep, drop = [], {"malformed": 0, "restricted": 0}
    setups = set(_setups())
    for c in scan or []:
        if not c.get("candidate_id") or c.get("setup_id") not in setups:
            drop["malformed"] += 1
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
    # The scanner's own terms, where it gives them (the brief's section 3).
    extra = []
    if c.get("warnings"):
        extra += [f"WARNING: {w}" for w in c["warnings"]]
    if c.get("against_tape"):
        extra.append(f"against the tape: a {c.get('time_stop')}-session time stop, "
                     f"no add")
    if c.get("entry_timing"):
        # The regime card's words, beside the dial state they were read under
        # (Doctrine 5.2; scanner follow-up 2).
        st = c.get("entry_timing_state")
        extra.append(f"entry timing — the regime card"
                     + (f", Gamma {st}" if st else "")
                     + f": “{c['entry_timing']}”")
    if isinstance(c.get("expected_r"), (int, float)):
        extra.append(f"expected {c['expected_r']:.1f}R (the measured move against "
                     f"the invalidation distance)")
    if c.get("parameters"):
        extra.append(f"parameters: {c['parameters']}")
    if c.get("counter_thesis") and c.get("parameters"):
        extra.append(f"counter-thesis: {c['counter_thesis']}")
    vpr = c.get("volume_profile")
    if vpr:
        # VP-1 item 9: where volume traded, from daily bars, and nothing more.
        extra.append(f"volume profile ({vpr.get('note')}): "
                     f"{vpr.get('base_text') or 'base POC not computed'}; nearest "
                     f"HVN toward +1R {vpr.get('hvn_text') or 'not computed'}")
    return (f"{n}. {c.get('instrument')} {c.get('direction')} — {c.get('thesis')}; "
            f"catalyst: {cat}; invalidation: {c.get('invalidation') or 'none named'}; "
            f"horizon: {c.get('horizon') or 'not stated'}; size band: "
            f"{c.get('size') or 'not stated'}"
            + "".join(f"; {x}" for x in extra)
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


def _same(row: dict, c: dict) -> bool:
    """A register row is the candidate's when instrument and direction agree,
    and the setup too where the row records one."""
    return (str(row.get("instrument") or "").upper()
            == str(c.get("instrument") or "").upper()
            and row.get("direction") == c.get("direction")
            and (not row.get("setup_id") or row.get("setup_id") == c.get("setup_id")))


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
    by = {r["id"]: r for r in rows}
    # THE PRIOR EDITION'S CANDIDATES. A candidate has no decision_id until the
    # sitting approves a packet, so each is matched to the register rows written
    # since its edition by instrument, direction and setup: an approved lineage
    # is not passed over; a declined one carries its reason; no row at all is a
    # pass with no reason recorded. A candidate the scanner fires again this week
    # prints as a candidate, not as a pass.
    this_week = {c.get("candidate_id") for c in scan or []}
    passed_candidates = []
    matched_roots = set()
    unmatched = 0                         # put to the sitting, no register row
    for c in prior_printed or []:
        if not c.get("candidate_id") or c["candidate_id"] in this_week:
            continue
        roots = sorted({heads.get(r["id"], r["id"]) for r in week
                        if _same(r, c)})
        outs = [outcome(lineage(rows, x)) for x in roots]
        matched_roots |= set(roots)
        unmatched += 0 if roots else 1
        if any(o["approved"] for o in outs):
            continue
        reason = next((o["reason"] for o in outs if o["reason"]), None)
        passed_candidates.append({"candidate_id": c["candidate_id"],
                                  "instrument": c.get("instrument"),
                                  "direction": c.get("direction"),
                                  "reason": reason or NO_REASON})
    reviewed_roots |= matched_roots
    for root in sorted(reviewed_roots - matched_roots):
        o = outcome(lineage(rows, root))
        if o["approved"]:
            continue
        r0 = by.get(root) or {}
        passed.append({"decision_id": root, "instrument": r0.get("instrument"),
                       "direction": r0.get("direction"),
                       "reason": o["reason"] or NO_REASON})
    if approved is None:
        approved = sum(1 for r in week if r.get("status") == "active")
    open_n = sum(1 for r in rows if r.get("status") in ("active", "draft")
                 and not r.get("superseded_by"))
    return {"fired": None if scan is None else len(scan),
            "reviewed": len(reviewed_roots) + unmatched,
            "drafted": len(drafted),
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


def reference_rows(rest: list[dict], start: int) -> dict:
    """Every candidate below the top ten, one row each (six columns)."""
    return {"columns": ["Rank", "Instrument", "Direction", "Setup", "Invalidation",
                        "Score"],
            "rows": [[n, c.get("instrument"), c.get("direction"),
                      str(c.get("pivot") or c.get("setup_id") or "").replace("_", " "),
                      c.get("invalidation"),
                      f"{c['score']:.2f}" if isinstance(c.get("score"), (int, float))
                      else "—"]
                     for n, c in enumerate(rest, start=start)]}


def subsections(scan: Optional[list[dict]], flow: dict,
                run: Optional[dict] = None, top: int = 10
                ) -> tuple[list[dict], dict]:
    """The candidates block and the productivity block, and what the edition
    archives for the next week (the candidates it printed). The top `top`
    print; the rest go to the reference tier (`kept["reference"]`)."""
    keep, drop = printable(scan)
    keep, rest = keep[:top], keep[top:]
    if scan is None:
        lines = [NO_SCANNER]
    else:
        lines = [candidate_line(n, c) for n, c in enumerate(keep, start=1)] or \
            ["The scanner fired no candidate this week."]
    lines += [passed_line(c) for c in flow.get("passed_candidates") or []]
    notes = []
    if drop["malformed"]:
        notes.append(f"{drop['malformed']} candidate(s) without an id or a declared "
                     f"setup not printed.")
    if drop["restricted"]:
        notes.append(f"{drop['restricted']} candidate(s) on a restricted instrument "
                     f"not printed.")
    if rest:
        notes.append(f"{len(rest)} more candidate(s) below the top {top} in the "
                     f"reference tables.")
    refused = (run or {}).get("refused") or []
    if refused:
        why: dict[str, int] = {}
        for r in refused:
            k = str(r.get("refused") or "")
            if "confirmation" in k:
                k = f"a {r.get('direction')} short of the confirmations it needs"
            why[k] = why.get(k, 0) + 1
        notes.append(f"{len(refused)} pivot(s) refused at the gates: "
                     + "; ".join(f"{v} — {k}" for k, v in sorted(why.items())) + ".")
    if (run or {}).get("parameters"):
        notes.append(run["parameters"])
    notes.append("Paper candidates for the sitting: nothing here is an order.")
    cand = {"title": HEADING, "lines": lines, "notes": notes,
            "candidates": [{k: c.get(k) for k in FIELDS} for c in keep]}
    prod = {"title": PRODUCTIVITY, "lines": [productivity_line(flow)],
            "table": ({"columns": ["Passed over", "Direction", "Reason"],
                       "rows": [[r["instrument"], r["direction"], r["reason"]]
                                for r in flow["passed_over"]]}
                      if flow["passed_over"] else None)}
    ref = ([{"title": REFERENCE_TITLE, "table": reference_rows(rest, top + 1)}]
           if rest else [])
    return [cand, prod], {"printed": cand["candidates"], "reference": ref}
