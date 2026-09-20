"""
WHAT CHANGED, and the state table -- rendered once, read by both anchors.

O.6: "Deltas and percentiles as the Daily's first block; levels as an appendix."
This module is that block. It renders the market-state object's diff against the
previous object, and it is the FIRST DATA BLOCK in both the 16:45 close report and
the 07:00 morning anchor.

WHY IT IS ONE MODULE AND NOT TWO. Two renderings of the same object would drift,
and the drift would be invisible: both would look right, and the close report and
the morning anchor would describe the same session differently. The close report
and the morning anchor are the two documents an operator compares.

DATA ONLY. No model call, no prose generation, nothing that could invent a figure.
This module is on the data path and tools/validate_daily_close.py scans it for the
same forbidden imports as payload.py and render.py.

EVERY MAGNITUDE CARRIES ITS PERCENTILE, which is the point of the block. "Credit
moved to stressed" is a label. "Credit moved to stressed, 4th percentile of five
years, confidence high, two of three members agreeing" is a measurement. A reader
can disagree with the second.
"""

from __future__ import annotations

from typing import Optional

H2 = ("font-size:13px;margin:22px 0 6px 0;color:#0d2b45;font-weight:600;"
      "text-transform:uppercase;letter-spacing:0.04em;")
NOTE = "font-size:11px;color:#5a6b7a;margin:4px 0 0 0;line-height:1.45;"
ABSENT = ("background:#f4f6f8;border-left:3px solid #94a3b8;padding:9px 12px;"
          "margin:6px 0;font-size:12px;color:#43525f;")
QUIET = ("background:#f4f9f4;border-left:3px solid #4d7c4d;padding:9px 12px;"
         "margin:6px 0;font-size:12px;color:#2f4f2f;")
MOVED = ("background:#fff4e5;border-left:3px solid #d97706;padding:9px 12px;"
         "margin:6px 0;font-size:12px;color:#7c3a00;")
TBL = ("border-collapse:collapse;width:100%;font-size:12px;"
       "font-variant-numeric:tabular-nums;"
       "font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;")
TH = "text-align:right;padding:5px 7px;border-bottom:2px solid #0d2b45;color:#0d2b45"
THL = "text-align:left;padding:5px 7px;border-bottom:2px solid #0d2b45;color:#0d2b45"
TD = "text-align:right;padding:4px 7px;border-bottom:1px solid #e6ebef"
TDL = "text-align:left;padding:4px 7px;border-bottom:1px solid #e6ebef"


def esc(s) -> str:
    return (str("" if s is None else s).replace("&", "&amp;")
            .replace("<", "&lt;").replace(">", "&gt;"))


def pctf(v) -> str:
    """A percentile, or the dash. NEVER an exception and never a bare label."""
    try:
        return f"{float(v):.1f}"
    except (TypeError, ValueError):
        return "&mdash;"


def zf(v) -> str:
    try:
        return f"{float(v):+.2f}"
    except (TypeError, ValueError):
        return "&mdash;"


def dashed(v) -> str:
    """An escaped value, or the em-dash ENTITY -- which must not go through esc().

    esc() escapes the ampersand, so "&mdash;" handed to it renders as the literal
    six characters. It did, in the first archived report: the exceptions table's
    `since` column read "&mdash;" rather than a dash.
    """
    return esc(v) if v not in (None, "") else "&mdash;"


def _li(items: list[str]) -> str:
    return ("<ul style='margin:6px 0 0 0;padding-left:18px'>"
            + "".join(f"<li>{i}</li>" for i in items) + "</ul>")


def session_events_line(payload: dict) -> str:
    """The session's event classes, for the report HEADER.

    In the header rather than in a block of its own because it qualifies EVERY number
    below it. An expiry close and an ordinary Tuesday's close are not the same
    measurement of the same thing, and a reader who learns that three screens down has
    already read the dealer surface as if it were routine.

    Friday 18 September 2026 was OPEX and TRIPLE_WITCHING, and nothing in this report
    said so until now.
    """
    obj = payload.get("market_state") or {}
    events = obj.get("session_events")
    if events is None:
        return ("session events: <em>not recorded on this object</em> (computed "
                "before the field existed)")
    if not events:
        return "session events: none &mdash; an ordinary close"
    strong = [e for e in events if e in ("OPEX", "TRIPLE_WITCHING",
                                        "INDEX_REBALANCE", "ETF_REBALANCE")]
    body = ", ".join(f"<strong>{esc(e)}</strong>" if e in strong else esc(e)
                     for e in events)
    tail = ""
    gamma = (obj.get("dials") or {}).get("gamma") or {}
    if gamma.get("provisional"):
        tail = (" &mdash; the gamma dial is <strong>PROVISIONAL</strong> on this "
                "session: its profile is computed over open interest much of which "
                "settles at this expiry")
    return f"session events: {body}{tail}"


def what_changed_block(payload: dict) -> str:
    """The diff, as the first data block. Levels move behind it."""
    obj = payload.get("market_state")
    wc = payload.get("what_changed")
    if not obj:
        return (f'<div style="{ABSENT}"><strong>No market-state object for this '
                f'session.</strong> The close pass computes it before the payload '
                f'is built, so its absence means that step did not run. This '
                f'report does not recompute it &mdash; two regimes with no way to '
                f'say which one a decision was made under is worse than one '
                f'missing block.</div>')
    if not wc:
        return (f'<div style="{ABSENT}">The object exists but no comparison was '
                f'made, so nothing is claimed about what changed.</div>')

    parts: list[str] = []

    if wc.get("compared_with") is None:
        parts.append(f'<div style="{ABSENT}">{esc(wc.get("note") or "no previous object")}'
                     f'</div>')
    elif wc.get("nothing_changed"):
        parts.append(
            f'<div style="{QUIET}"><strong>Nothing changed</strong> against '
            f'{esc(wc.get("compared_with"))}. No dimension changed state, no '
            f'extreme was set or cleared, no dial moved, and no contradiction '
            f'opened or closed. Stated positively, so that a quiet session and a '
            f'broken comparison do not look the same.</div>')

    rows = []
    for c in wc.get("dimension_changes") or []:
        rows.append(
            f'<tr><td style="{TDL}">{esc(c["dimension"])}</td>'
            f'<td style="{TDL}">{esc(c.get("from"))} &rarr; '
            f'<strong>{esc(c.get("to"))}</strong></td>'
            f'<td style="{TD}">{pctf(c.get("percentile"))}</td>'
            f'<td style="{TD}">{esc(c.get("direction"))}</td>'
            f'<td style="{TDL}">{esc(c.get("confidence"))}</td></tr>')
    if rows:
        parts.append(
            f'<table style="{TBL}"><thead><tr>'
            f'<th style="{THL}">dimension</th><th style="{THL}">state</th>'
            f'<th style="{TH}">pctile</th><th style="{TH}">dir</th>'
            f'<th style="{THL}">conf</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')

    pend = wc.get("pending_states") or []
    if pend:
        parts.append(
            f'<div style="{ABSENT}"><strong>Turning, not turned.</strong> A new '
            f'reading must hold the declared number of sessions before it is '
            f'published, so these are recorded and not yet in force.'
            + _li([f'<code>{esc(p["dimension"])}</code>: published '
                   f'{esc(p.get("published"))}, pending '
                   f'<strong>{esc(p.get("pending"))}</strong> '
                   f'({esc(p.get("sessions"))} of {esc(p.get("required"))} '
                   f'sessions), percentile {pctf(p.get("percentile"))}'
                   for p in pend]) + '</div>')

    dials = wc.get("dial_changes") or []
    if dials:
        parts.append(
            f'<div style="{MOVED}"><strong>Dials</strong>'
            + _li([f'<code>{esc(d["dial"])}</code>: {esc(d.get("from"))} &rarr; '
                   f'<strong>{esc(d.get("to"))}</strong>'
                   + (f' &mdash; {esc(d.get("reason"))}' if d.get("to") is None
                      and d.get("reason") else "")
                   for d in dials]) + '</div>')

    ex_set = wc.get("extremes_set") or []
    ex_clr = wc.get("extremes_cleared") or []
    if ex_set or ex_clr:
        items = [f'<code>{esc(e["metric"])}</code> ({esc(e["dimension"])}) SET '
                 f'&mdash; percentile {pctf(e.get("percentile"))}, '
                 f'z {zf(e.get("z_score"))}' for e in ex_set]
        items += [f'<code>{esc(e["metric"])}</code> ({esc(e["dimension"])}) '
                  f'CLEARED &mdash; percentile {pctf(e.get("percentile"))}'
                  for e in ex_clr]
        parts.append(f'<div style="{MOVED}"><strong>Extreme flags</strong>'
                     + _li(items) + '</div>')

    op = wc.get("contradictions_opened") or []
    pers = wc.get("contradictions_persisting") or []
    cl = wc.get("contradictions_closed") or []
    if op or pers or cl:
        items = []
        for r in op:
            items.append(
                f'<strong>OPENED</strong> <code>{esc(r["id"])}</code> '
                f'{esc(r.get("legs"))} &mdash; z {zf(r.get("magnitude"))} against '
                f'a threshold of {esc(r.get("threshold_z"))}, since '
                f'{esc(r.get("since"))}'
                + ("  <strong>EXCEPTION</strong> (report-only: this repo has no "
                   "exceptions alert path)" if r.get("exception") else ""))
        for r in pers:
            items.append(
                f'PERSISTING <code>{esc(r["id"])}</code> &mdash; z '
                f'{zf(r.get("magnitude"))}, {esc(r.get("persistence_days"))} '
                f'sessions since {esc(r.get("since"))}'
                + ("  <strong>EXCEPTION</strong> (report-only)"
                   if r.get("exception") else ""))
        for r in cl:
            items.append(f'CLOSED <code>{esc(r["id"])}</code> &mdash; '
                         f'{esc(r.get("closed_note") or "condition no longer met")}')
        parts.append(f'<div style="{MOVED}"><strong>Contradictions</strong>'
                     + _li(items) + '</div>')

    gone = wc.get("absences_opened") or []
    back = wc.get("absences_cleared") or []
    if gone or back:
        items = [f'<code>{esc(a["dimension"])}</code> was {esc(a.get("was"))}, now '
                 f'absent &mdash; {esc(a.get("reason"))}' for a in gone]
        items += [f'<code>{esc(a["dimension"])}</code> is back: '
                  f'<strong>{esc(a.get("now"))}</strong>, percentile '
                  f'{pctf(a.get("percentile"))}' for a in back]
        parts.append(f'<div style="{ABSENT}"><strong>Coverage</strong>'
                     + _li(items) + '</div>')

    return "".join(parts)


def exceptions_block(payload: dict) -> str:
    """The object's exceptions[], in the anchors, matching the heartbeat's mail.

    THE SAME LIST THE HEARTBEAT EMAILS, and that matters more than it looks: the
    mail says what CHANGED and deliberately does not repeat a standing condition,
    so the anchor is where a reader sees everything currently open. If these two
    could disagree, the reader would have no way to tell a closed exception from an
    unreported one.
    """
    obj = payload.get("market_state") or {}
    exc = obj.get("exceptions")
    if exc is None:
        return (f'<div style="{ABSENT}">This object carries no exceptions field '
                f'(computed before Phase 2b added it).</div>')
    if not exc:
        return (f'<div style="{QUIET}"><strong>No exceptions open.</strong> No '
                f'contradiction has stayed open to its declared session count and '
                f'no member sits at a five-year extreme. Stated positively, so a '
                f'quiet table and a broken one do not look the same.</div>')
    rows = []
    for e in exc:
        rows.append(
            f'<tr><td style="{TDL}">{esc(e.get("kind"))}</td>'
            f'<td style="{TDL}">{esc(e.get("what"))}</td>'
            f'<td style="{TD}">{esc(e.get("value"))}</td>'
            f'<td style="{TDL}">{esc(e.get("threshold"))}</td>'
            f'<td style="{TDL}">{dashed(e.get("since"))}</td></tr>')
    return (f'<table style="{TBL}"><thead><tr>'
            f'<th style="{THL}">kind</th><th style="{THL}">what</th>'
            f'<th style="{TH}">value</th><th style="{THL}">threshold</th>'
            f'<th style="{THL}">since</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>'
            f'<p style="{NOTE}">An exception is a finding about the market, not '
            f'about the pipeline. The heartbeat emails these only when the set '
            f'CHANGES -- an alert that repeats a standing condition is one the '
            f'reader learns to delete -- so this block is where the full open set '
            f'lives.</p>')


def state_table(payload: dict) -> str:
    """The object itself: every dimension, its percentile, and its disagreements."""
    obj = payload.get("market_state")
    if not obj:
        return f'<div style="{ABSENT}">No object for this session.</div>'

    dial_items = []
    for name, d in (obj.get("dials") or {}).items():
        if d.get("state") is None:
            dial_items.append(f'<code>{esc(name)}</code> &mdash; ABSENT: '
                              f'{esc(d.get("absent_reason"))}')
        else:
            dial_items.append(f'<code>{esc(name)}</code> &mdash; '
                              f'<strong>{esc(d["state"])}</strong>'
                              + (f' (level {esc(d.get("level"))})'
                                 if d.get("level") is not None else ""))

    rows = []
    for name, d in (obj.get("dimensions") or {}).items():
        if d.get("state") is None:
            rows.append(
                f'<tr><td style="{TDL}">{esc(name)}</td>'
                f'<td style="{TDL}" colspan="5"><em>absent</em> &mdash; '
                f'{esc(d.get("absent_reason"))}</td></tr>')
            continue
        contra = d.get("contradicting")
        contra_s = (esc(contra) if isinstance(contra, str)
                    else ", ".join(esc(c) for c in contra))
        rows.append(
            f'<tr><td style="{TDL}">{esc(name)}</td>'
            f'<td style="{TDL}">{esc(d["state"])}</td>'
            f'<td style="{TD}">{pctf(d.get("percentile"))}</td>'
            f'<td style="{TD}">{esc(d.get("direction"))}</td>'
            f'<td style="{TDL}">{esc(d.get("confidence"))}</td>'
            f'<td style="{TDL}">{contra_s}</td></tr>')

    return (f'<div style="{NOTE}">Object <code>{esc(obj.get("schema_version"))}'
            f'</code> for session {esc(obj.get("session"))}, config '
            f'<code>{esc(obj.get("config_version"))}</code>, computed at '
            f'{esc(obj.get("computed_at"))} on <code>'
            f'{esc(obj.get("git_sha"))}</code>. Read, not recomputed.</div>'
            f'<div style="{ABSENT}"><strong>Dials</strong>'
            + _li(dial_items) + '</div>'
            f'<table style="{TBL}"><thead><tr>'
            f'<th style="{THL}">dimension</th><th style="{THL}">state</th>'
            f'<th style="{TH}">pctile</th><th style="{TH}">dir</th>'
            f'<th style="{THL}">conf</th>'
            f'<th style="{THL}">contradicting</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


def contradiction_table(payload: dict) -> str:
    obj = payload.get("market_state") or {}
    rows_in = obj.get("contradictions") or []
    if not rows_in:
        return f'<div style="{ABSENT}">No contradiction table on this object.</div>'
    rows = []
    for r in rows_in:
        if r.get("open_state") == "absent":
            rows.append(f'<tr><td style="{TDL}">{esc(r["id"])}</td>'
                        f'<td style="{TDL}" colspan="4"><em>absent</em> &mdash; '
                        f'{esc(r.get("absent_reason"))}</td></tr>')
            continue
        mag = ("state mismatch" if r.get("magnitude") is None
               else zf(r.get("magnitude")))
        rows.append(
            f'<tr><td style="{TDL}">{esc(r["id"])}</td>'
            f'<td style="{TDL}">{esc(r.get("open_state"))}'
            + ("  <strong>EXCEPTION</strong>" if r.get("exception") else "")
            + f'</td><td style="{TD}">{mag}</td>'
            f'<td style="{TD}">{esc(r.get("persistence_days"))}</td>'
            f'<td style="{TDL}">{dashed(r.get("since"))}</td></tr>')
    return (f'<table style="{TBL}"><thead><tr>'
            f'<th style="{THL}">pair</th><th style="{THL}">state</th>'
            f'<th style="{TH}">z</th><th style="{TH}">days</th>'
            f'<th style="{THL}">since</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>'
            f'<p style="{NOTE}">The magnitude is the z of the gap between the two '
            f'legs against that gap\'s own history, not the gap itself &mdash; so it '
            f'is a claim about the relationship rather than about either level. An '
            f'exception is report-only: this repo has no exceptions alert path.</p>')


def text_lines(payload: dict) -> list[str]:
    """The same block for the plain-text fallback."""
    obj = payload.get("market_state")
    wc = payload.get("what_changed") or {}
    if not obj:
        return ["WHAT CHANGED: no market-state object for this session -- the "
                "close pass did not compute one, and no report recomputes it."]
    L = [f"WHAT CHANGED (vs {wc.get('compared_with') or 'no previous object'})"]
    if wc.get("nothing_changed"):
        L.append("  nothing changed: no state, extreme, dial or contradiction "
                 "moved")
    for c in wc.get("dimension_changes") or []:
        L.append(f"  {c['dimension']}: {c.get('from')} -> {c.get('to')} "
                 f"(pctile {c.get('percentile')}, dir {c.get('direction')}, "
                 f"conf {c.get('confidence')})")
    for p in wc.get("pending_states") or []:
        L.append(f"  {p['dimension']}: pending {p.get('pending')} "
                 f"({p.get('sessions')}/{p.get('required')} sessions)")
    for d in wc.get("dial_changes") or []:
        L.append(f"  dial {d['dial']}: {d.get('from')} -> {d.get('to')}")
    for e in wc.get("extremes_set") or []:
        L.append(f"  extreme SET {e['metric']} (pctile {e.get('percentile')})")
    for e in wc.get("extremes_cleared") or []:
        L.append(f"  extreme CLEARED {e['metric']}")
    for r in (wc.get("contradictions_opened") or []):
        L.append(f"  contradiction OPENED {r['id']} z={r.get('magnitude')}")
    for r in (wc.get("contradictions_persisting") or []):
        L.append(f"  contradiction PERSISTING {r['id']} "
                 f"{r.get('persistence_days')}d")
    for r in (wc.get("contradictions_closed") or []):
        L.append(f"  contradiction CLOSED {r['id']}")
    for a in wc.get("absences_opened") or []:
        L.append(f"  {a['dimension']} went absent: {a.get('reason')}")
    for a in wc.get("absences_cleared") or []:
        L.append(f"  {a['dimension']} is back: {a.get('now')}")
    exc = obj.get("exceptions")
    L.append("")
    if exc is None:
        L.append("EXCEPTIONS: this object predates the field")
    elif not exc:
        L.append("EXCEPTIONS: none open")
    else:
        L.append(f"EXCEPTIONS ({len(exc)})")
        for e in exc:
            L.append(f"  {e.get('kind')}: {e.get('what')} "
                     f"value={e.get('value')} threshold={e.get('threshold')}"
                     + (f" since {e.get('since')}" if e.get("since") else ""))
    L.append("")
    L.append(f"STATE ({obj.get('schema_version')}, session {obj.get('session')})")
    for name, d in (obj.get("dials") or {}).items():
        L.append(f"  dial {name}: {d.get('state') or 'absent'}")
    for name, d in (obj.get("dimensions") or {}).items():
        if d.get("state") is None:
            L.append(f"  {name}: absent")
        else:
            L.append(f"  {name}: {d.get('state')} pctile {d.get('percentile')} "
                     f"dir {d.get('direction')} conf {d.get('confidence')}")
    return L
