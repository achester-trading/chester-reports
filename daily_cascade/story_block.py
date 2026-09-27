"""
The 07:00 anchor's STORY block -- the news and narrative scan's payload. DATA ONLY.

    from daily_cascade.story_block import build, narrative_payload

6c-2, Audit #3 §I, Daily Cascade v2 Part 0.4. The block the reasoning model writes
over, and the table printed beneath its prose. Named `story_block` and not after the
narrative layer on purpose: this module is on the DATA PATH, and the data path must
never import, or be mistaken for, the module that reaches a model
(tools/validate_daily_close.py checks both).

WHAT IT READS, AND ONLY THAT
    events         since the previous close, knowable at the cutoff -- releases,
                   earnings, filings and headlines by declared story query, each
                   carried WITH ITS EVENT ID, because every claim the prose makes
                   must trace to one
    the register   each active story's latest evaluation as-of the cutoff: state,
                   attention, agreement, evidence ids, the conditions and runs --
                   and the transitions since the previous close
    the object     what_changed and the contradiction table, narrative_vs_data
                   included, read from regime.latest() and never recomputed

IT FETCHES NOTHING and it computes no state: a story's state is what the rules
wrote, read as-of the cutoff; a contradiction is what the object holds.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from altdata import events as ev_mod
from altdata import narratives as nr
from altdata import observations, session

# How many headlines per story the payload carries by id. The COUNT is always the
# full count; the cap is on what the model is shown to cite.
MAX_HEADLINES_PER_QUERY = 4
MAX_RELEASES = 10
MAX_EARNINGS = 10
MAX_FILINGS = 8

# The only prefix under which the prose may cite a stored event. Declared here,
# where the ids are gathered, so the audit's allowed set and the template's form
# cannot disagree.
CITE_WORD = "event"


def _events(since: str, cutoff: str, db_path: Optional[str]) -> dict:
    with ev_mod.EventStore(db_path) as ev:
        rows = ev.since(since, as_of=cutoff)
    out: dict[str, Any] = {"releases": [], "earnings": [], "filings": [],
                           "headlines_by_query": {}, "counts": {}}
    for r in rows:
        t = r["type"]
        out["counts"][t] = out["counts"].get(t, 0) + 1
        p = r.get("payload") or {}
        if t == "release":
            out["releases"].append({"event_id": r["id"], "when": r["observed_at"],
                                    "source": r["source"], "title": r["title"],
                                    "entities": r.get("entities") or []})
        elif t == "earnings":
            out["earnings"].append({"event_id": r["id"], "when": r["observed_at"],
                                    "symbol": p.get("symbol"),
                                    "surprise_pct": p.get("surprise_pct"),
                                    "reported_eps": p.get("reported_eps"),
                                    "eps_estimate": p.get("eps_estimate")})
        elif t == "filing":
            out["filings"].append({"event_id": r["id"], "when": r["observed_at"],
                                   "title": r["title"],
                                   "entities": r.get("entities") or []})
        elif t == "headline":
            q = str(p.get("query") or "unattributed")
            s = out["headlines_by_query"].setdefault(
                q, {"query": q, "theme": p.get("theme"), "count": 0, "top": []})
            s["count"] += 1
            if len(s["top"]) < MAX_HEADLINES_PER_QUERY:
                s["top"].append({"event_id": r["id"], "title": r["title"],
                                 "when": r["observed_at"]})
    out["releases_total"] = len(out["releases"])
    out["releases"] = out["releases"][-MAX_RELEASES:]
    out["earnings_total"] = len(out["earnings"])
    out["earnings"] = out["earnings"][-MAX_EARNINGS:]
    out["filings_total"] = len(out["filings"])
    out["filings"] = out["filings"][-MAX_FILINGS:]
    return out


def _register(cutoff: str, since: str, db_path: Optional[str]) -> dict:
    cfg = nr.load_config()
    stories, pending = [], []
    with nr.NarrativeRegister(db_path) as reg:
        for row in reg.all():
            if row["status"] == "proposed":
                pending.append({"id": row["narrative_id"], "name": row["name"],
                                "proposed_at": row["proposed_at"],
                                "confirm": nr.CONFIRM_COMMAND.format(
                                    id=row["narrative_id"])})
                continue
            if row["status"] != "active":
                continue
            ev = reg.conn.execute(
                "SELECT * FROM narrative_evaluations WHERE narrative_id = ? "
                " AND evaluated_at <= ? ORDER BY evaluated_at DESC, id DESC LIMIT 1",
                (row["narrative_id"], observations.canonical_instant(cutoff))
            ).fetchone()
            state = nr.state_as_of(reg.conn, row["narrative_id"], cutoff)
            item: dict[str, Any] = {
                "id": row["narrative_id"], "name": row["name"], "state": state,
                "direction": row["direction"], "opened": row["opened"],
                "linked_dimensions": row["linked_dimensions"],
                "implied_outcome": (row["implied_outcome"] or {}).get("claim"),
                "state_probability": nr.probability_for(state, cfg),
                "story_query": row["story_query"],
            }
            if ev is None:
                item["evaluation"] = None
                item["evaluation_absent_reason"] = (
                    "not yet evaluated -- the close pass evaluates each story after "
                    "it stores the object")
            else:
                inputs = json.loads(ev["inputs"])
                att, agr, evd = (inputs.get("attention") or {},
                                 inputs.get("agreement") or {},
                                 inputs.get("evidence") or {})
                item["evaluation"] = {
                    "session": ev["session"],
                    "attention_short": att.get("short"),
                    "attention_long": att.get("long"),
                    "attention_short_sessions": att.get("short_sessions"),
                    "attention_long_sessions": att.get("long_sessions"),
                    "attention_delta_short": att.get("delta_short"),
                    "attention_delta2_short": att.get("delta2_short"),
                    "attention_delta_long": att.get("delta_long"),
                    "agreement_ratio": agr.get("share"),
                    "dimensions_agreeing": agr.get("agree"),
                    "dimensions_disagreeing": agr.get("disagree"),
                    "dimensions_uncounted": agr.get("uncounted"),
                    "evidence_for": evd.get("for") or [],
                    "evidence_against": evd.get("against") or [],
                    # 6c-3: price moves by declared rule, beside the event ids.
                    "series_for": evd.get("series_for") or [],
                    "series_against": evd.get("series_against") or [],
                    "conditions_met": json.loads(ev["conditions"]),
                    "condition_runs": json.loads(ev["runs"]),
                }
            stories.append(item)
    trans = nr.transitions_since(since, as_of=cutoff, db_path=db_path)
    return {"stories": stories, "pending_proposals": pending,
            "transitions_overnight": trans,
            "persistence_sessions": (cfg.get("rules") or {}).get(
                "persistence_sessions"),
            "rules": cfg.get("rules")}


def build(prior_session: str, cutoff: Optional[str] = None,
          market_state: Optional[dict] = None,
          what_changed: Optional[dict] = None,
          db_path: Optional[str] = None) -> dict:
    """Everything the narrative scan may say, with the ids it may cite."""
    cut = cutoff or session.utc_iso(timespec="microseconds")
    since = f"{prior_session}T20:00:00+00:00"
    out: dict[str, Any] = {"state": "ok", "since": since, "as_of": cut}
    try:
        out["events"] = _events(since, cut, db_path)
    except Exception as exc:                                   # noqa: BLE001
        out["events"] = {"absent_reason": f"events table unreadable: "
                                          f"{type(exc).__name__}: {exc}"}
    try:
        out["register"] = _register(cut, since, db_path)
    except Exception as exc:                                   # noqa: BLE001
        out["register"] = {"absent_reason": f"narrative register unreadable: "
                                            f"{type(exc).__name__}: {exc}"}
    obj = market_state or {}
    out["object_session"] = obj.get("session")
    out["contradictions"] = [
        {k: r.get(k) for k in ("id", "open_state", "open", "magnitude", "since",
                               "persistence_days", "states", "narrative_state",
                               "dimensions_against", "exception")}
        for r in obj.get("contradictions") or []
        if r.get("open_state") != "absent"]
    out["contradictions_absent"] = sorted(
        r["id"] for r in obj.get("contradictions") or []
        if r.get("open_state") == "absent")
    out["what_changed"] = what_changed
    ids = set()
    ev = out.get("events") or {}
    for k in ("releases", "earnings", "filings"):
        ids.update(x["event_id"] for x in ev.get(k) or [])
    for q in (ev.get("headlines_by_query") or {}).values():
        ids.update(x["event_id"] for x in q.get("top") or [])
    for s in (out.get("register") or {}).get("stories") or []:
        e = s.get("evaluation") or {}
        ids.update(e.get("evidence_for") or [])
        ids.update(e.get("evidence_against") or [])
    out["citable_event_ids"] = sorted(int(i) for i in ids)
    if (ev.get("absent_reason") and (out.get("register") or {}).get(
            "absent_reason")):
        out["state"] = "absent"
        out["reason"] = f"{ev['absent_reason']}; {out['register']['absent_reason']}"
    return out


def narrative_payload(block: dict, what_changed: Optional[dict] = None) -> dict:
    """The subset the model is handed. The citable ids travel with it."""
    return {
        "since_previous_close": block.get("since"),
        "as_of": block.get("as_of"),
        "object_session": block.get("object_session"),
        "events": block.get("events"),
        "register": {k: v for k, v in (block.get("register") or {}).items()
                     if k != "rules"},
        "contradictions": block.get("contradictions"),
        "contradictions_absent": block.get("contradictions_absent"),
        "what_changed": what_changed if what_changed is not None
        else block.get("what_changed"),
        "citable_event_ids": block.get("citable_event_ids"),
    }
