"""
The Weekly Tactical, rendered. DATA ONLY -- no model call, no prose generation.

Scanned by tools/validate_weekly.py for the same forbidden imports as payload.py
and render.py: nothing here may reach a network or a model. The paragraph arrives
already written and already audited, and this module places it.

THE BLOCK ORDER IS THE PAYLOAD'S ORDER, and the five headings are the five blocks.
A renderer that chose its own order would make the document and the payload two
different accounts of the week, and the validator asserts they agree.

STYLES ARE THE CLOSE REPORT'S, imported rather than restated: two documents from
one system that looked different would make a reader work out which was which
before reading either.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from daily_cascade.render import (                # noqa: E402
    ABSENT, H1, H2, NOTE, SUB, TBL, TD, TDL, TH, THL, WARN, WRAP,
    esc, num, _rows,
)


def _dash(v) -> str:
    return "&mdash;" if v in (None, "", []) else esc(v)


def _signed(v, dp: int = 2) -> str:
    try:
        return f"{float(v):+,.{dp}f}"
    except (TypeError, ValueError):
        return "&mdash;"


def absent_box(block: dict, title: str) -> str:
    return (f'<div style="{ABSENT}"><strong>{esc(title)} &mdash; '
            f'{esc(block.get("state") or "absent")}.</strong> '
            f'{esc(block.get("reason") or "no reason recorded")}</div>')


# ---------------------------------------------------------------------------
# 1. The week in state
# ---------------------------------------------------------------------------
def state_block(payload: dict) -> str:
    b = payload.get("week_in_state") or {}
    if b.get("state") != "ok":
        return absent_box(b, "The week in state")
    parts = [
        f'<p style="{NOTE}">{esc(b.get("previous_week_ending"))} &rarr; '
        f'<strong>{esc(b.get("week_ending"))}</strong> &middot; '
        f'{len(b.get("sessions_in_week") or [])} sessions, '
        f'{esc(b.get("objects_found"))} with an object &middot; '
        f'config {esc(b.get("config_version"))} &middot; '
        f'method {esc(b.get("method_version"))}</p>']

    changes = b.get("dimension_changes") or []
    if changes:
        rows = [f'<tr><td style="{TDL}">{esc(c["dimension"])}</td>'
                f'<td style="{TDL}">{_dash(c.get("from"))} &rarr; '
                f'<strong>{_dash(c.get("to"))}</strong></td>'
                f'<td style="{TD}">{num(c.get("percentile"), 1)}</td>'
                f'<td style="{TDL}">{_dash(c.get("direction"))}</td>'
                f'<td style="{TDL}">{_dash(c.get("confidence"))}</td>'
                f'<td style="{TDL}">{_dash(c.get("last_changed"))}</td></tr>'
                for c in changes]
        parts.append(
            f'<table style="{TBL}"><thead><tr><th style="{THL}">dimension</th>'
            f'<th style="{THL}">over the week</th><th style="{TH}">pctile</th>'
            f'<th style="{THL}">dir</th><th style="{THL}">conf</th>'
            f'<th style="{THL}">since</th></tr></thead>'
            f'<tbody>{_rows(rows)}</tbody></table>')
    else:
        parts.append(
            f'<div style="{ABSENT}"><strong>No dimension changed state over the '
            f'week.</strong> Stated positively, so a quiet week and a broken '
            f'comparison do not look the same. '
            f'{esc(b.get("comparison_note") or "")}</div>')
    held = b.get("dimensions_held") or []
    if held:
        parts.append(f'<p style="{NOTE}">Held: '
                     f'<code>{esc(", ".join(held))}</code>.</p>')

    dials = b.get("dial_changes") or []
    parts.append(
        f'<p style="{NOTE}"><strong>Dials</strong> &mdash; '
        + ", ".join(f'{esc(k)} <strong>{_dash(v)}</strong>'
                    for k, v in (b.get("dials_now") or {}).items())
        + ('. Changed this week: '
           + ", ".join(f'{esc(d["dial"])} {_dash(d.get("from"))}&rarr;'
                       f'{_dash(d.get("to"))}' for d in dials)
           if dials else '. None moved this week.') + '</p>')

    # EXCEPTIONS, with the intra-week set given its own line: an exception that
    # opened Tuesday and closed Thursday is in neither endpoint and is the fact a
    # weekly is most likely to miss.
    op, cl = b.get("exceptions_opened") or [], b.get("exceptions_closed") or []
    churn = b.get("exceptions_intraweek_only") or []
    items = []
    if op:
        items.append(f'<strong>opened</strong>: <code>{esc(", ".join(op))}</code>')
    if cl:
        items.append(f'<strong>closed</strong>: <code>{esc(", ".join(cl))}</code>')
    if churn:
        items.append(f'<strong>opened and closed inside the week</strong>: '
                     f'<code>{esc(", ".join(churn))}</code>')
    open_now = b.get("exceptions_open_now") or []
    items.append(f'open now: {len(open_now)}'
                 + (f' (<code>{esc(", ".join(open_now))}</code>)'
                    if open_now else ''))
    parts.append(f'<div style="{WARN if (op or churn) else ABSENT}">'
                 f'<strong>Exceptions</strong><br>' + '<br>'.join(items)
                 + '</div>')

    contras = [r for r in (b.get("contradictions") or [])
               if r.get("open_state") != "absent"]
    if contras:
        rows = [f'<tr><td style="{TDL}">{esc(r.get("id"))}</td>'
                f'<td style="{TDL}">{_dash(r.get("open_state"))}</td>'
                f'<td style="{TD}">{num(r.get("magnitude"), 2)}</td>'
                f'<td style="{TD}">{num(r.get("threshold_z"), 1)}</td>'
                f'<td style="{TD}">{_dash(r.get("persistence_days"))}</td>'
                f'<td style="{TDL}">{_dash(r.get("since"))}</td></tr>'
                for r in contras]
        parts.append(
            f'<table style="{TBL}"><thead><tr><th style="{THL}">pair</th>'
            f'<th style="{THL}">state</th><th style="{TH}">z</th>'
            f'<th style="{TH}">threshold</th><th style="{TH}">sessions</th>'
            f'<th style="{THL}">since</th></tr></thead>'
            f'<tbody>{_rows(rows)}</tbody></table>')

    # THE DUAL RUN'S WEEKLY COUNT, which is the whole point of running two legs.
    ts = b.get("vol_term_structure") or {}
    ag = ts.get("week_agreement") or {}
    ch, cl2 = ts.get("champion") or {}, ts.get("challenger") or {}
    parts.append(
        f'<div style="{ABSENT}"><strong>Vol term structure &mdash; the dual '
        f'run</strong><br>'
        f'published by <strong>{_dash(ts.get("published_by"))}</strong>: '
        f'{_dash(ts.get("published_state"))}<br>'
        f'champion <code>{_dash(ch.get("metric"))}</code> '
        f'<strong>{_dash(ch.get("state"))}</strong> '
        f'ratio {num(ch.get("ratio"), 4)}, pctile {num(ch.get("percentile"), 1)}<br>'
        f'challenger <code>{_dash(cl2.get("metric"))}</code> '
        f'<strong>{_dash(cl2.get("state"))}</strong> '
        f'ratio {num(cl2.get("ratio"), 4)}, pctile '
        f'{num(cl2.get("percentile"), 1)}<br>'
        f'this week: <strong>{esc(ag.get("agreed"))} agreed</strong>, '
        f'{esc(ag.get("disagreed"))} disagreed, '
        f'{esc(ag.get("not_comparable"))} not comparable &middot; '
        f'dual run to {_dash(ts.get("dual_run_until"))}'
        + (f'<br>basis {num((ts.get("basis") or {}).get("value"), 2)} vol points, '
           f'pctile {num((ts.get("basis") or {}).get("percentile"), 1)}'
           if (ts.get("basis") or {}).get("value") is not None else '')
        + f'<p style="{NOTE}">The quarter\'s question is a COUNT of disagreeing '
          f'sessions, not an opinion, and this is where it accumulates.</p></div>')
    return "".join(parts)


# ---------------------------------------------------------------------------
# 2. Grades
# ---------------------------------------------------------------------------
def grades_block(payload: dict) -> str:
    b = payload.get("grades") or {}
    if b.get("state") == "empty":
        return (f'<div style="{ABSENT}"><strong>No decision has reached its '
                f'horizon yet.</strong> {esc(b.get("reason"))}</div>'
                + brier_block(b))
    if b.get("state") != "ok":
        return absent_box(b, "Grades")
    cuts = b.get("cuts") or {}
    parts = [f'<p style="{NOTE}">{esc(b.get("total_graded"))} graded to date '
             f'&middot; method {esc(b.get("method_version"))} &middot; '
             f'{len(b.get("graded_this_week") or [])} reached a horizon this '
             f'week</p>']
    ov = cuts.get("overall") or {}
    parts.append(
        f'<div style="{ABSENT}"><strong>Overall</strong> &mdash; n='
        f'{esc(ov.get("n"))}, interval first: '
        f'{num(ov.get("lo"), 3)} to {num(ov.get("hi"), 3)}R, '
        f'mean {_signed(ov.get("mean"), 3)}R. '
        f'{esc(ov.get("note") or "")}</div>')

    for label, key in (("by status", "by_status"),
                       ("by owning report", "by_owning_report"),
                       ("by book", "by_book"),
                       ("by mechanism group", "by_mechanism_group"),
                       ("by regime (SPY gamma sign)", "by_regime_spy_gamma")):
        cut = cuts.get(key) or {}
        if not cut:
            continue
        rows = []
        for name, iv in sorted(cut.items()):
            rows.append(f'<tr><td style="{TDL}">{esc(name)}</td>'
                        f'<td style="{TD}">{esc(iv.get("n"))}</td>'
                        f'<td style="{TD}">{num(iv.get("lo"), 3)}</td>'
                        f'<td style="{TD}">{num(iv.get("hi"), 3)}</td>'
                        f'<td style="{TD}">{_signed(iv.get("mean"), 3)}</td></tr>')
        parts.append(
            f'<p style="{NOTE}"><strong>{esc(label)}</strong></p>'
            f'<table style="{TBL}"><thead><tr><th style="{THL}">cut</th>'
            f'<th style="{TH}">n</th><th style="{TH}">lo</th>'
            f'<th style="{TH}">hi</th><th style="{TH}">mean R</th></tr></thead>'
            f'<tbody>{_rows(rows)}</tbody></table>')

    week = b.get("graded_this_week") or []
    if week:
        rows = [f'<tr><td style="{TDL}">{esc(g.get("instrument"))}</td>'
                f'<td style="{TDL}">{_dash(g.get("horizon"))}</td>'
                f'<td style="{TDL}">{_dash(g.get("status"))}</td>'
                f'<td style="{TD}">{num(g.get("return_pct"), 2)}</td>'
                f'<td style="{TD}">{_signed(g.get("r_multiple"), 2)}</td>'
                f'<td style="{TDL}">{_dash(g.get("graded_at"))}</td></tr>'
                for g in week]
        parts.append(
            f'<p style="{NOTE}"><strong>Reached a horizon this week</strong></p>'
            f'<table style="{TBL}"><thead><tr><th style="{THL}">instrument</th>'
            f'<th style="{THL}">horizon</th><th style="{THL}">status</th>'
            f'<th style="{TH}">return %</th><th style="{TH}">R</th>'
            f'<th style="{THL}">graded</th></tr></thead>'
            f'<tbody>{_rows(rows)}</tbody></table>')
    return "".join(parts) + brier_block(b)


def brier_block(b: dict) -> str:
    br = b.get("brier") or {}
    if br.get("reason") and not br.get("emitted"):
        return (f'<div style="{ABSENT}"><strong>Brier &mdash; nothing to '
                f'score.</strong> {esc(br.get("reason"))}</div>')
    rows = []
    for src, s in sorted((br.get("by_source") or {}).items()):
        rows.append(f'<tr><td style="{TDL}">{esc(src)}</td>'
                    f'<td style="{TD}">{esc(s.get("n"))}</td>'
                    f'<td style="{TD}">{num(s.get("brier"), 4)}</td>'
                    f'<td style="{TD}">{num(s.get("mean_probability"), 3)}</td>'
                    f'</tr>')
    body = (f'<table style="{TBL}"><thead><tr><th style="{THL}">source</th>'
            f'<th style="{TH}">resolved</th><th style="{TH}">Brier</th>'
            f'<th style="{TH}">mean p</th></tr></thead>'
            f'<tbody>{_rows(rows)}</tbody></table>' if rows else '')
    return (f'<p style="{NOTE}"><strong>Brier</strong> &mdash; '
            f'{esc(br.get("emitted"))} emitted, {esc(br.get("resolved"))} '
            f'resolved. A running Brier above 0.25 is worse than a coin.</p>'
            + body)


# ---------------------------------------------------------------------------
# 3. The register
# ---------------------------------------------------------------------------
def register_block(payload: dict) -> str:
    b = payload.get("register") or {}
    if b.get("state") != "ok":
        return absent_box(b, "Register")
    parts = [f'<p style="{NOTE}">{esc(b.get("open_count"))} open &middot; '
             f'{esc(b.get("drafts_count"))} draft</p>']
    for label, key in (("Open", "open"), ("Drafts", "drafts")):
        items = b.get(key) or []
        if not items:
            parts.append(f'<div style="{ABSENT}">No {esc(label.lower())} '
                         f'decisions.</div>')
            continue
        rows = []
        for d in items:
            rows.append(
                f'<tr><td style="{TDL}">{esc(d.get("instrument"))}</td>'
                f'<td style="{TDL}">{_dash(d.get("direction"))}</td>'
                f'<td style="{TDL}">{_dash(d.get("thesis_state"))}</td>'
                f'<td style="{TD}">{num(d.get("invalidation_level"), 2)}</td>'
                f'<td style="{TD}">{num(d.get("mark"), 2)}</td>'
                f'<td style="{TD}">{_signed(d.get("distance_points"), 2)}</td>'
                f'<td style="{TD}">{_signed(d.get("distance_pct"), 2)}</td>'
                f'<td style="{TD}">{_dash(d.get("age_days"))}</td>'
                f'<td style="{TDL}">{_dash(d.get("expression_family"))}</td>'
                f'</tr>')
        parts.append(
            f'<p style="{NOTE}"><strong>{esc(label)}</strong></p>'
            f'<table style="{TBL}"><thead><tr><th style="{THL}">instrument</th>'
            f'<th style="{THL}">dir</th><th style="{THL}">thesis</th>'
            f'<th style="{TH}">invalidation</th><th style="{TH}">mark</th>'
            f'<th style="{TH}">dist pts</th><th style="{TH}">dist %</th>'
            f'<th style="{TH}">age d</th><th style="{THL}">expression</th>'
            f'</tr></thead><tbody>{_rows(rows)}</tbody></table>')

    rb = b.get("rule_breaks") or {}
    ns = rb.get("not_yet_sourced") or {}
    # The style is chosen before the f-string: an expression split across two
    # adjacent literals is not one expression, which is what the first version
    # tried and the parser refused.
    rb_style = (WARN if rb.get("restricted_instrument_attempts_this_week")
                else ABSENT)
    parts.append(
        f'<div style="{rb_style}"><strong>Rule breaks</strong><br>'
        f'restricted-instrument attempts this week: '
        f'<strong>{esc(rb.get("restricted_instrument_attempts_this_week"))}</strong>'
        f' &middot; running total '
        f'{esc(rb.get("restricted_instrument_attempts_total"))}<br>'
        f'decisions blocked on eligibility this week: '
        f'{esc(rb.get("decision_blocked_this_week"))}'
        f'<p style="{NOTE}">{esc(rb.get("running_total_note"))}</p>'
        f'<p style="{NOTE}"><strong>Not yet sourced</strong>, and a zero here would '
        f'read as "no rule was broken", which is a claim this system cannot make: '
        + "; ".join(f'<code>{esc(k)}</code> needs '
                    f'{esc(", ".join(v.get("needs") or []))}'
                    for k, v in sorted(ns.items()))
        + '</p></div>')
    return "".join(parts)


# ---------------------------------------------------------------------------
# 4. The week ahead
# ---------------------------------------------------------------------------
def week_ahead_block(payload: dict) -> str:
    b = payload.get("week_ahead") or {}
    if b.get("state") != "ok":
        return absent_box(b, "The week ahead")
    w = b.get("window") or ["", ""]
    parts = [f'<p style="{NOTE}">{esc(w[0])} to {esc(w[1])}</p>']

    evs = b.get("session_events") or {}
    if evs:
        rows = [f'<tr><td style="{TDL}">{esc(d)}</td>'
                f'<td style="{TDL}"><code>{esc(", ".join(v))}</code></td></tr>'
                for d, v in sorted(evs.items())]
        parts.append(
            f'<table style="{TBL}"><thead><tr><th style="{THL}">session</th>'
            f'<th style="{THL}">event classes</th></tr></thead>'
            f'<tbody>{_rows(rows)}</tbody></table>'
            f'<p style="{NOTE}">{esc(b.get("session_events_note"))}</p>')

    rel = b.get("releases") or {}
    if rel.get("state") == "ok":
        rows = [f'<tr><td style="{TDL}">{esc(r.get("date"))}</td>'
                f'<td style="{TDL}">{esc(r.get("release_name"))}</td>'
                f'<td style="{TDL}"><code>'
                f'{esc(", ".join(r.get("tracked_series") or []) or "&mdash;")}'
                f'</code></td></tr>'
                for r in (rel.get("rows") or [])
                if r.get("tracked_series")]
        parts.append(
            f'<p style="{NOTE}"><strong>Scheduled releases</strong> &mdash; '
            f'{esc(rel.get("tracked_count"))} of {esc(rel.get("count"))} carry a '
            f'tracked series; the series-to-release map is '
            f'{esc(rel.get("map_resolved"))} of {esc(rel.get("map_of"))} '
            f'resolved</p>'
            + (f'<table style="{TBL}"><thead><tr><th style="{THL}">date</th>'
               f'<th style="{THL}">release</th>'
               f'<th style="{THL}">tracked series</th></tr></thead>'
               f'<tbody>{_rows(rows)}</tbody></table>' if rows else
               f'<div style="{ABSENT}">No tracked series is released in this '
               f'window.</div>'))
    else:
        parts.append(absent_box(rel, "Scheduled releases"))

    ea = b.get("earnings") or {}
    if ea.get("state") == "ok":
        hits = ea.get("in_window") or []
        parts.append(
            f'<p style="{NOTE}"><strong>Earnings</strong> &mdash; '
            + (", ".join(f'<code>{esc(h["symbol"])}</code> '
                         f'{esc(", ".join(h["dates"]))}' for h in hits)
               if hits else "none in the window")
            + f'<br>{esc(ea.get("note"))}</p>')
    else:
        parts.append(absent_box(ea, "Earnings"))

    dated = b.get("dated_claims") or []
    parts.append(
        f'<div style="{ABSENT}"><strong>Dated claims</strong>'
        + "".join(
            f'<br><code>{esc(c.get("id"))}</code>: {esc(c.get("value"))}'
            + (f' <em>({esc(c.get("source"))}, as of {esc(c.get("as_of"))})</em>'
               if c.get("source") else
               f' &mdash; {esc(c.get("absent_reason"))}')
            for c in dated)
        + f'<p style="{NOTE}">Cited by id from the claims registry, never '
          f'retyped.</p></div>')
    return "".join(parts)


def events_block_text_lines(payload: dict) -> list[str]:
    """The weekend block for the plain-text edition, from the one renderer."""
    from . import events_block
    return events_block.text_lines(payload.get("weekend_developments") or {})


def weekend_block(payload: dict) -> str:
    """The events table, or an absence with a reason. Not a placeholder any more.

    THE ABSENT SHAPE IS KEPT, not deleted: when the ingest has not run this block
    still has to read differently from a quiet weekend, which is the whole argument
    the not_yet_sourced version was written to make.
    """
    b = payload.get("weekend_developments") or {}
    if b.get("state") != "ok":
        return (f'<div style="{ABSENT}"><strong>Weekend developments &mdash; '
                f'{esc(b.get("state") or "absent")}.</strong><br>'
                f'{esc(b.get("reason"))}'
                f'<p style="{NOTE}">{esc(b.get("why_the_block_exists"))}</p>'
                f'</div>')
    from . import events_block
    still = b.get("needs_still") or []
    tail = (f'<p style="{NOTE}">Still missing: '
            f'{esc("; ".join(still))}.</p>' if still else "")
    return f'<div style="{WRAP}">{events_block.html(b)}{tail}</div>'


# ---------------------------------------------------------------------------
# The document
# ---------------------------------------------------------------------------
def narrative_block(narrative: Optional[Any]) -> str:
    if narrative is None:
        return ""
    if getattr(narrative, "published", False):
        return (f'<div style="{WRAP}"><p style="font-size:14px;line-height:1.7;'
                f'color:#12304d;margin:0">{esc(narrative.text)}</p>'
                f'<p style="{NOTE}">Model {esc(narrative.model)} &middot; '
                f'{esc(narrative.figures_checked)} figures audited against the '
                f'payload.</p></div>')
    note = getattr(narrative, "withheld_note", lambda: "narrative withheld")()
    return (f'<div style="{ABSENT}"><strong>{esc(note)}</strong>'
            f'<p style="{NOTE}">The paragraph is withheld rather than corrected: a '
            f'figure the payload does not carry is a figure nobody can check, and '
            f'the blocks below are the record either way.</p></div>')


def render(payload: dict, extra: Optional[dict] = None,
           narrative: Optional[Any] = None) -> str:
    extra = extra or {}
    warn = ""
    if payload.get("warnings"):
        warn = (f'<div style="{WARN}"><strong>Absences</strong>'
                f'<ul style="margin:6px 0 0 0;padding-left:18px">'
                + "".join(f'<li>{esc(w)}</li>' for w in payload["warnings"])
                + '</ul></div>')
    return f"""<div style="{WRAP}">
<h1 style="{H1}">Weekly Tactical &mdash; week ending {esc(payload.get('week_ending'))}</h1>
<p style="{SUB}">
  Generated {esc(payload.get('generated_at'))} &middot;
  as-of cutoff {esc(payload.get('as_of'))} &middot;
  run <code>{esc(payload.get('run_id') or 'n/a')}</code><br>
  {esc(len(payload.get('sessions_in_week') or []))} sessions &middot;
  previous week ending {esc(payload.get('previous_week_ending'))}
</p>
{warn}
{narrative_block(narrative)}

<h2 style="{H2}">The week in state</h2>
{state_block(payload)}

<h2 style="{H2}">Grades</h2>
{grades_block(payload)}

<h2 style="{H2}">Register</h2>
{register_block(payload)}

<h2 style="{H2}">The week ahead</h2>
{week_ahead_block(payload)}

<h2 style="{H2}">Weekend developments</h2>
{weekend_block(payload)}

<p style="{NOTE}">
  Archive: <code>{esc(extra.get('archive_path') or 'n/a')}</code>.
  This anchor replaces the Friday Reflection and the Sunday Forward Plan. No slot
  computes: every figure above was read from the object, the register, the grader,
  the probability ledger or the store, and anything unreadable says so.
</p>
</div>"""


def text_fallback(payload: dict) -> str:
    """The plain-text part of the email. Deliberately short: the HTML is the report."""
    st = payload.get("week_in_state") or {}
    gr = payload.get("grades") or {}
    rg = payload.get("register") or {}
    return "\n".join([
        f"Weekly Tactical -- week ending {payload.get('week_ending')}",
        f"  state      : {st.get('state')} -- "
        f"{len(st.get('dimension_changes') or [])} dimension change(s), "
        f"{len(st.get('exceptions_opened') or [])} exception(s) opened",
        f"  grades     : {gr.get('state')} -- {gr.get('total_graded')} to date, "
        f"{len(gr.get('graded_this_week') or [])} this week",
        f"  register   : {rg.get('open_count')} open, {rg.get('drafts_count')} draft",
        f"  weekend    : "
        + "; ".join(events_block_text_lines(payload)),
        "",
        "The HTML edition carries the tables.",
    ])
