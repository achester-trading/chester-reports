"""
The daily close as the ten-section stack. DATA AND PLACED PROSE ONLY. (T1)

    html = stack_render.render(payload, edition, charts, mode="email")

TWO EDITIONS OF ONE DOCUMENT. `mode="email"` references each chart as
`cid:<id>@chester` -- the PNG travels in the same multipart/related message;
`mode="archive"` references the SVG written beside the HTML on disk. Everything
else is byte-for-byte the same.

Each section prints, in order: its title (and the trigger when a conditional
depth fired); its claim line in bold, or the reason it was withheld; "(unchanged
since <date>)" and nothing more when it collapsed; its paragraphs; its items, a ◆
before each that changed since the prior edition; its table; its charts; and a
"Not yet tracked" footnote. "(trimmed)" marks a section the budget cut.

The detail tables of the pre-stack close follow the stack, unchanged, so nothing
the report used to carry is lost.
"""

from __future__ import annotations

from typing import Any, Optional

from . import render as base
from . import state_block

esc, NOTE, TBL, TH, THL, TD, TDL, ABSENT, WARN = (
    base.esc, base.NOTE, base.TBL, base.TH, base.THL, base.TD, base.TDL, base.ABSENT,
    base.WARN)
H2 = base.H2
DIAMOND = "◆"


def cid(chart_id: str) -> str:
    return f"{chart_id.lower()}@chester"


def _chart_html(ch: dict, mode: str) -> str:
    if ch.get("unavailable"):
        return f'<p style="{NOTE}"><em>chart unavailable: {esc(ch["unavailable"])}</em></p>'
    src = (f"cid:{cid(ch['id'])}" if mode == "email" else
           esc(str(ch.get("svg_path") or "").replace("\\", "/").split("/")[-1]))
    return (f'<figure style="margin:8px 0 12px 0">'
            f'<img src="{src}" alt="{esc(ch.get("caption"))}" '
            f'style="max-width:100%;height:auto" width="700">'
            f'<figcaption style="{NOTE}">{esc(ch.get("caption"))}</figcaption></figure>')


def _table(t: Optional[dict]) -> str:
    if not t or not t.get("rows"):
        return ""
    head = "".join(f'<th style="{THL if n == 0 else TH}">{esc(c)}</th>'
                   for n, c in enumerate(t["columns"]))
    body = "".join("<tr>" + "".join(
        f'<td style="{TDL if n == 0 else TD}">{esc(v if v is not None else "—")}</td>'
        for n, v in enumerate(r)) + "</tr>" for r in t["rows"])
    return f'<table style="{TBL}"><tr>{head}</tr>{body}</table>'


def section_html(s: dict, n: int, charts: dict, mode: str) -> str:
    depth = s["depth"] + (f": {s['depth_reason']}" if s.get("depth_reason") else "")
    out = [f'<h2 style="{H2}">{n}. {esc(s["title"])} '
           f'<span style="font-size:11px;color:#5a6b7a;font-weight:400">'
           f'({esc(depth)}){" (trimmed)" if s.get("trimmed") else ""}</span></h2>']
    if s.get("claim"):
        out.append(f'<p style="font-size:13.5px;margin:0 0 8px 0"><strong>'
                   f'{esc(s["claim"])}</strong>'
                   + (f' <span style="{NOTE}">(unchanged since '
                      f'{esc(s["unchanged_since"])})</span>' if s.get("collapsed")
                      else "") + "</p>")
    elif s.get("withheld"):
        out.append(f'<div style="{ABSENT}"><strong>Claim withheld.</strong> '
                   f'{esc(s["withheld"])}</div>')
    if s.get("collapsed"):
        return "".join(out)
    for p in s.get("paragraphs") or []:
        out.append(f'<p style="font-size:13px;line-height:1.55;margin:0 0 10px 0">'
                   f'{esc(p)}</p>')
    if s.get("items"):
        out.append('<ul style="margin:4px 0 8px 0;padding-left:18px;font-size:12.5px">'
                   + "".join(f'<li>{DIAMOND + " " if i.get("changed") else ""}'
                             f'{esc(i["text"])}</li>' for i in s["items"]) + "</ul>")
    out.append(_table(s.get("table")))
    for c in s.get("charts_rendered") or []:
        if c in charts:
            out.append(_chart_html(charts[c], mode))
    if s.get("legend"):
        out.append(f'<p style="{NOTE}">{esc(s["legend"])}</p>')
    if s.get("not_tracked"):
        out.append(f'<p style="{NOTE}"><strong>Not yet tracked:</strong> '
                   f'{esc("; ".join(s["not_tracked"]))}.</p>')
    return "".join(out)


def _detail(fn, p: dict) -> str:
    """A pre-stack detail table; one that cannot render says so, never blanks."""
    try:
        return fn(p)
    except Exception as exc:                                    # noqa: BLE001
        return (f'<p style="{NOTE}">detail table unavailable: '
                f'{esc(type(exc).__name__)}: {esc(exc)}</p>')


def render(p: dict, ed: dict, charts: dict, mode: str = "email",
           delivery: Optional[dict] = None) -> str:
    secs = "".join(section_html(s, n, charts, mode)
                   for n, s in enumerate(ed["sections"], start=1))
    marks = (f"{DIAMOND} marks a line that changed since the {esc(ed['prior_session'])} "
             f"edition." if ed.get("prior_session") else
             "No prior stacked edition to compare against: nothing is marked as "
             "changed and nothing collapses.")
    warn = ""
    if p.get("warnings"):
        warn = (f'<div style="{WARN}"><strong>Warnings</strong><ul style="margin:6px '
                f'0 0 0;padding-left:18px">' + "".join(f"<li>{esc(w)}</li>"
                                                      for w in p["warnings"])
                + "</ul></div>")
    return f"""<div style="{base.WRAP}">
<h1 style="{base.H1}">Close &mdash; {esc(p.get('session'))}</h1>
<p style="{base.SUB}">As-of cutoff {esc(p.get('as_of'))} &middot; run
<code>{esc(p.get('run_id') or 'n/a')}</code> &middot; stack
<code>{esc(ed.get('config_version'))}</code> &middot; {esc(ed.get('words'))} words
&middot; {marks}<br>{state_block.session_events_line(p)}</p>
{warn}
{secs}
<h2 style="{H2}">Detail tables</h2>
{_detail(state_block.state_table, p)}
{_detail(state_block.contradiction_table, p)}
{_detail(base.exposure_table, p)}
{_detail(base.pin_table, p)}
{_detail(base.portfolio_block, p)}
{_detail(base.enforcement_block, p)}
<p style="{NOTE}">Every figure above was read from the store, the computed profiles
or the 5-minute bars pulled after the close. No figure here is a recommendation;
every probability printed is a ledger entry written before this edition. Archived
to <code>{esc((delivery or {}).get('archive_path') or 'n/a')}</code>.</p>
</div>"""
