"""
The voices, as the reports print them -- DATA AND FIXED SENTENCES, read from the
stored rows only.

    from daily_cascade import voices_block
    voices_block.daily_line(session_day, cutoff, db_path)     # the close's line
    voices_block.week_section(week_ending, as_of, db_path)    # Weekly section 8
    voices_block.month_block(start, end, as_of, db_path)      # Monthly section 4

Phase B, ruled 4 Oct 2026. Nothing here fetches (the 06:45 scan does) and nothing
here declares a status (altdata/voices.py computes it). Every line that carries a
voice carries its source: outlet, date and URL. "No stored source, not printed."

EVERY PRINTED VIEW IS AUDITED. A view is the model's paraphrase, so it is held to
the rules every paragraph is: the style list (motive phrases, banned closers,
intensity words without a figure, internal vocabulary) and the policy-word rule
(hike, cut and hold only about the Fed's rate). A view that fails prints as
"view withheld: <reason>" in its place; the voice, its source and its computed
status still print, because they are stored facts, not prose.
"""

from __future__ import annotations

import datetime as dt
from collections import Counter
from typing import Any, Optional

from altdata import session
from altdata import voices as vmod

MAX_ITEMS_PER_STORY = 5


# ---------------------------------------------------------------------------
# The audit every printed view passes
# ---------------------------------------------------------------------------
def view_faults(text: str) -> list[str]:
    from . import stack as stack_mod                            # noqa: PLC0415
    from . import stack_prose                                   # noqa: PLC0415
    try:
        from altdata import prediction_markets as pm            # noqa: PLC0415
        pm_cfg = pm.load_config()
    except Exception:                                           # noqa: BLE001
        pm_cfg = None
    return (stack_prose.style_faults(text, stack_mod.config())
            + stack_prose.policy_word_faults(text, pm_cfg))


def printed_view(row: dict) -> str:
    """A voice row's view, or an evidence row's summary (the same paraphrase),
    audited."""
    v = str(row.get("view") or row.get("summary") or "")
    f = view_faults(v)
    return f"view withheld: {'; '.join(f[:2])}" if f else v


def cite(row: dict) -> str:
    """outlet, date, URL -- the stored source, as a reader can follow it."""
    d = str(row.get("published_at") or "")[:10]
    try:
        x = dt.date.fromisoformat(d)
        d = f"{x.day} {x:%b %Y}"
    except ValueError:
        pass
    return f"{row.get('outlet')}, {d}, {row.get('source_url')}"


def _kind(k: Optional[str]) -> str:
    return str((vmod.load_config().get("kinds") or {}).get(k) or k or "")


def _stories(db_path: Optional[str]) -> dict[str, dict]:
    from altdata import narratives                              # noqa: PLC0415
    try:
        with narratives.NarrativeRegister(db_path) as reg:
            return {r["narrative_id"]: r for r in reg.all("active")}
    except Exception:                                           # noqa: BLE001
        return {}


def _close_utc(day: dt.date) -> str:
    """The instant the session `day` closed, in UTC ISO."""
    t = session.close_time_et(day)
    et = dt.datetime.combine(day, t, tzinfo=session._eastern_tz())
    return et.astimezone(dt.timezone.utc).isoformat()


def unreachable_line(runs: dict) -> Optional[str]:
    bad = sorted({r["source_name"] for r in runs.values()
                  if r["state"] in ("unreachable", "robots_disallowed")})
    nc = sorted({r["source_name"] for r in runs.values()
                 if r["state"] == "not_configured"})
    parts = []
    if bad:
        parts.append("Unreachable on the latest scan: " + "; ".join(bad) + ".")
    if nc:
        parts.append(f"The scan is not configured on this machine ({len(nc)} "
                     f"source(s) not read).")
    return " ".join(parts) or None


# ---------------------------------------------------------------------------
# The daily close: one line
# ---------------------------------------------------------------------------
def daily_line(session_day: str, cutoff: str, db_path: Optional[str] = None) -> dict:
    """The day's most-cited story and a dissent if one was published, each
    sourced. "The day" is what the scan retrieved after the previous session's
    close and up to this cutoff."""
    day = dt.date.fromisoformat(session_day)
    since = _close_utc(session.previous_trading_session(day))
    stories = _stories(db_path)
    with vmod.VoicesStore(db_path, readonly=True) as vs:
        ev = [e for e in vs.evidence(as_of=cutoff) if e["retrieved_at"] > since]
        runs = vs.latest_runs(cutoff)
    out: dict[str, Any] = {"since": since, "cutoff": cutoff, "evidence": len(ev)}
    lines: list[str] = []
    if not ev:
        lines.append("No sourced voice bore on a story since the previous close.")
    else:
        by = Counter(e["narrative_id"] for e in ev)
        top, n = sorted(by.items(), key=lambda kv: (-kv[1], kv[0]))[0]
        rows = [e for e in ev if e["narrative_id"] == top]
        sides = Counter(e["side"] for e in rows)
        name = (stories.get(top) or {}).get("name") or top
        lead_side = "for" if sides["for"] >= sides["against"] else "against"
        lead = next(e for e in rows if e["side"] == lead_side)
        line = (f"Most cited: {name}, {n} item{'s' if n != 1 else ''} "
                f"({sides['for']} for, {sides['against']} against). "
                f"{lead['voice']}, {lead_side}: {printed_view(lead)} ({cite(lead)}).")
        lines.append(line)
        minority = "against" if lead_side == "for" else "for"
        dis = [e for e in rows if e["side"] == minority]
        if dis and sides[minority] < sides[lead_side]:
            d = dis[-1]
            lines.append(f"Dissent: {d['voice']}, {minority}: {printed_view(d)} "
                         f"({cite(d)}).")
        elif dis:
            lines.append("The items split evenly; no side is the dissent.")
        else:
            lines.append("No dissent was published.")
        out["story"] = top
        out["sides"] = dict(sides)
    u = unreachable_line(runs)
    if u:
        lines.append(u)
    out["lines"] = lines
    return out


# ---------------------------------------------------------------------------
# Status table and the consensus line
# ---------------------------------------------------------------------------
def table(st: dict, *, with_13f: Optional[dict] = None) -> dict:
    cols = ["Voice", "Affiliation", "Kind", "View", "Status", "Source", "Tier",
            "Horizon"]
    if with_13f is not None:
        cols.append("13F (period of report)")
    rows = []
    for v in st["voices"]:
        r = v["row"]
        status = v["status"]
        if v["status"] == "INFLECTED":
            ch = [f"{vmod.subject_label(x['subject'])} {x['was']}→{x['now']}"
                  for x in v["subjects"] if x["status"] == "INFLECTED"]
            status += f" ({'; '.join(ch)})"
        elif v["status"] == "UNREACHABLE":
            status += f" ({v.get('source_name')})"
        row = [r["voice"], r["affiliation"], _kind(r["kind"]),
               (printed_view(r) if v["status"] not in ("SILENT", "UNREACHABLE")
                else f"last: {printed_view(r)}"),
               status, cite(r), r["tier"], r.get("horizon") or "—"]
        if with_13f is not None:
            f = with_13f.get(r["voice_key"])
            row.append(f"{f['form']} for {f['period_of_report']} (filed {f['filed']}, "
                       f"{f['source_url']})" if f else "—")
        rows.append(row)
    return {"columns": cols, "rows": rows}


def consensus_line(st: dict) -> dict:
    """Where consensus sits and who dissents, computed from the window's latest
    view per voice. CONSENSUS needs two or more tier 1-2 voices in one direction
    on one subject (the Monthly brief's rule); the dissent is the opposite
    direction on that subject, named with its source."""
    now = [v for v in st["voices"] if v["status"] not in ("SILENT", "UNREACHABLE")]
    tally: dict[tuple, list] = {}
    for v in now:
        for x in v["subjects"]:
            tally.setdefault((x["subject"], x["now"]), []).append(v)
    best = None
    for (subj, d), vs in tally.items():
        if d == "neutral":
            continue
        t12 = [v for v in vs if int(v["row"]["tier"]) <= 2]
        if len(t12) >= 2 and (best is None or len(t12) > best[2]):
            best = (subj, d, len(t12), vs)
    if not best:
        return {"text": "No consensus: no subject drew two tier 1–2 voices in the "
                        "same direction.", "subject": None}
    subj, d, n, vs = best
    opp = "bearish" if d == "bullish" else "bullish"
    against = tally.get((subj, opp)) or []
    names = ", ".join(v["row"]["voice"] for v in vs[:5])
    text = (f"Consensus: {d} on {vmod.subject_label(subj)} ({len(vs)} voices, "
            f"{n} of them tier 1–2: {names}).")
    if against:
        a = against[0]["row"]
        text += (f" Against it: {a['voice']} ({a['affiliation']}), {opp} "
                 f"({cite(a)})" + (f", and {len(against) - 1} more" if
                                   len(against) > 1 else "") + ".")
    else:
        text += " No contrarian view on it was published."
    return {"text": text, "subject": subj, "direction": d,
            "consensus": [v["voice_key"] for v in vs],
            "contrarian": [v["voice_key"] for v in against]}


# ---------------------------------------------------------------------------
# The Weekly's section 8 -- the synthesis
# ---------------------------------------------------------------------------
def story_items(ev: list[dict], stories: dict) -> list[dict]:
    """For each active story: its count for and against, three to five sourced
    items (the most recent, both sides represented when both exist), and who
    dissented -- the minority side, named."""
    out = []
    for sid, s in stories.items():
        rows = [e for e in ev if e["narrative_id"] == sid]
        sides = Counter(e["side"] for e in rows)
        pick: list[dict] = []
        for side in ("for", "against"):
            pick += [e for e in rows if e["side"] == side][-3:]
        pick = sorted(pick, key=lambda e: e["published_at"])[-MAX_ITEMS_PER_STORY:]
        minority = None
        if sides["for"] and sides["against"] and sides["for"] != sides["against"]:
            minority = "against" if sides["for"] > sides["against"] else "for"
        out.append({"story": sid, "name": s.get("name"), "state": s.get("state"),
                    "for": sides["for"], "against": sides["against"],
                    "items": pick, "minority": minority,
                    "dissent": [e for e in rows if e["side"] == minority]})
    return out


def week_section(week_ending: str, as_of: str, db_path: Optional[str] = None,
                 item_fn=None) -> dict:
    """Section 8 for the Weekly: per story, what moved it for and against and who
    dissented; the voices table with weekly status; the consensus line."""
    end = (dt.date.fromisoformat(week_ending[:10]) + dt.timedelta(days=1)).isoformat()
    st = vmod.status_table(end, "weekly", as_of=as_of, db_path=db_path)
    stories = _stories(db_path)
    with vmod.VoicesStore(db_path, readonly=True) as vs:
        ev = vs.evidence(as_of=as_of, since=st["start"], until=st["end"])
        runs = vs.latest_runs(as_of)
    mk = item_fn or (lambda k, t, p=2, v=None: {"key": k, "text": t, "priority": p})
    items = []
    syn = story_items(ev, stories)
    for s in syn:
        n = s["for"] + s["against"]
        head = (f"{s['name']} ({s['state']}): "
                + (f"{n} sourced item{'s' if n != 1 else ''} this week, "
                   f"{s['for']} for, {s['against']} against."
                   if n else "no sourced voice bore on it this week."))
        if s["dissent"]:
            d = s["dissent"][-1]
            head += f" Dissent: {d['voice']} ({s['minority']})."
        items.append(mk(f"voices:story:{s['story']}", head, 1,
                        (s["for"], s["against"])))
        for e in s["items"]:
            items.append(mk(f"voices:ev:{e['id']}",
                            f"— {e['side']}: {e['voice']} ({_kind(e['kind'])}): "
                            f"{printed_view(e)} ({cite(e)})", 2, e["id"]))
    cons = consensus_line(st)
    items.append(mk("voices:consensus", cons["text"], 1, cons.get("subject")))
    counts = Counter(v["status"] for v in st["voices"])
    if st["voices"]:
        items.append(mk("voices:status", "Voices this week: " + ", ".join(
            f"{counts[s]} {s.lower()}" for s in vmod.STATUSES if counts[s]) + ".",
            2, dict(counts)))
    u = unreachable_line(runs)
    if u:
        items.append(mk("voices:unreachable", u, 1, u))
    return {"items": items, "table": table(st),
            "data": {"stories": [{k: s[k] for k in ("name", "state", "for",
                                                     "against")}
                                 | {"items": [{"voice": e["voice"], "side": e["side"],
                                               "view": e["summary"],
                                               "outlet": e["outlet"],
                                               "published": e["published_at"][:10]}
                                              for e in s["items"]],
                                    "dissent": [e["voice"] for e in s["dissent"]]}
                                 for s in syn],
                     "consensus": cons["text"],
                     "voices": [{"voice": v["row"]["voice"],
                                 "affiliation": v["row"]["affiliation"],
                                 "status": v["status"], "view": v["row"]["view"],
                                 "outlet": v["row"]["outlet"],
                                 "published": v["row"]["published_at"][:10]}
                                for v in st["voices"]]},
            "window": {"start": st["start"], "end": st["end"]}}


# ---------------------------------------------------------------------------
# The Monthly: the voices table with monthly status, the four weeks rolled up,
# and 13F where the voice's firm files one
# ---------------------------------------------------------------------------
def month_block(month_end: str, as_of: str, db_path: Optional[str] = None) -> dict:
    end = (dt.date.fromisoformat(month_end[:10]) + dt.timedelta(days=1)).isoformat()
    st = vmod.status_table(end, "monthly", as_of=as_of, db_path=db_path)
    stories = _stories(db_path)
    f13: dict[str, dict] = {}
    with vmod.VoicesStore(db_path, readonly=True) as vs:
        # Only a CIK that MATCHED EDGAR's current name prints a 13F (4 Oct
        # ruling); latest_13f returns nothing for any other.
        for v in st["voices"]:
            f = vs.latest_13f(v["row"]["affiliation"], month_end[:10], as_of)
            if f:
                f13[v["voice_key"]] = f
        weeks = []
        e = dt.date.fromisoformat(st["end"])
        while e > dt.date.fromisoformat(st["start"]) and len(weeks) < 5:
            s = max(e - dt.timedelta(days=7), dt.date.fromisoformat(st["start"]))
            ev = vs.evidence(as_of=as_of, since=s.isoformat(), until=e.isoformat())
            weeks.append({"week_ending": (e - dt.timedelta(days=1)).isoformat(),
                          "stories": {sid: dict(Counter(x["side"] for x in ev
                                                        if x["narrative_id"] == sid))
                                      for sid in stories}})
            e = s
        runs = vs.latest_runs(as_of)
    weeks.reverse()
    roll_rows = []
    for sid, s in stories.items():
        row = [s.get("name")]
        for w in weeks:
            c = w["stories"].get(sid) or {}
            row.append(f"{c.get('for', 0)} for / {c.get('against', 0)} against")
        roll_rows.append(row)
    return {"state": "ok" if st["voices"] else "empty",
            "reason": None if st["voices"] else
            "no voice was stored in the month or the month before",
            "window": {"start": st["start"], "end": st["end"],
                       "prior_start": st["prior_start"]},
            "table": table(st, with_13f=f13),
            "consensus": consensus_line(st)["text"],
            "rollup": {"columns": ["Story"] + [f"Week to {w['week_ending']}"
                                               for w in weeks],
                       "rows": roll_rows},
            "unreachable": unreachable_line(runs),
            "voices": len(st["voices"]),
            "with_13f": len(f13)}
