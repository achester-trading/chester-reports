"""
The stacked editions' HTML: the daily close, the Weekly and the Monthly, one
renderer. (T1; T2.5; T2.6)

    html = stack_render.render(payload, edition, charts, mode="email")
    one = stack_render.section_html(section, n, charts, mode, cadence="monthly")
    tail = stack_render.details_html(edition["detail"], cadence="monthly")

TWO EDITIONS OF ONE DOCUMENT. `mode="email"` references each chart as
`cid:<id>@chester` -- the PNG travels in the same multipart/related message;
`mode="archive"` references the SVG written beside the HTML on disk. Everything
else is byte-for-byte the same.

THE FIXED ORDER INSIDE EVERY SECTION (T2.5 item 2, ruled 5 Oct 2026): the header;
the claim line; the table(s) -- the section's, then each sub-section's under its
own small heading, then any code-written lines as a table of their own; the
chart(s); ONE paragraph; the footnote. A section with no new facts prints its
header and its footnote and nothing else (item 5).

PER CADENCE (T2.6), from config `cadences:`. The close and the Weekly print one
paragraph per section, and a sub-section's "not yet tracked" folds into the
section's footnote. A cadence whose sub-sections keep their own paragraphs (the
Monthly) prints each sub-section as a block of its own -- its tables, its lines,
its paragraphs, its footnote -- and every paragraph the guard kept. The period in
"This week" / "Also this month" is the cadence's.

DETAIL TABLES (T2.6): after the last section, an edition may carry `detail`, a
list of blocks each printed under "Detail tables" with its own heading -- the
close's state and contradiction tables (ruled 6 Oct 2026), the Monthly's record.

THE STYLES (item 10), inline because Gmail strips stylesheets, and the same
constants for every stacked report: the section header; the claim line, bold and
larger; the table, with a header row, light zebra rows, numbers right-aligned and
at most six columns; the chart with a small italic caption; the paragraph; the
footnote, small and grey. Nothing prints as a list.

The run's metadata -- stack version, word count, as-of cutoff, run id -- sits in a
small footer with the one line that points to the Reader's Guide (item 7).
"""

from __future__ import annotations

import re
from typing import Any, Optional

from . import readability as rd
from . import render as base

esc = base.esc
DIAMOND = "◆"

# ---- the six element styles (item 10) -------------------------------------
WRAP = ("font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,"
        "sans-serif;font-size:13px;color:#1a1a1a;background:#ffffff;"
        "max-width:720px;margin:0 auto;padding:12px;")
H1 = "font-size:20px;margin:0 0 4px 0;color:#0d2b45;font-weight:700;line-height:1.3"
SUB = "font-size:12.5px;color:#43525f;margin:0 0 12px 0;line-height:1.5"
SECTION = ("font-size:13px;margin:26px 0 8px 0;padding-top:8px;color:#0d2b45;"
           "font-weight:600;text-transform:uppercase;letter-spacing:0.04em;"
           "border-top:2px solid #0d2b45")
SUBTITLE = ("font-size:12px;font-weight:400;font-style:italic;color:#5a6b7a;"
            "text-transform:none;letter-spacing:0")
CLAIM = ("font-size:15.5px;font-weight:700;line-height:1.4;color:#0d2b45;"
         "margin:0 0 10px 0")
H3 = ("font-size:12px;font-weight:600;color:#0d2b45;margin:12px 0 4px 0")
# AT 400 PX (T2.5 item 10): a table wider than the screen scrolls inside its
# own box (SCROLL) instead of widening the page; a number never breaks inside
# itself (TD) -- a cell of several, "a / b / c", wraps at its spaces (TDW); and a
# long unbroken string in a footnote or caption -- a path, a URL -- wraps
# anywhere, so nothing pushes the page past the screen.
SCROLL = "overflow-x:auto;max-width:100%;margin:0 0 10px 0"
TBL = ("border-collapse:collapse;width:100%;font-size:12px;margin:0;"
       "font-variant-numeric:tabular-nums")
TH = ("text-align:right;padding:5px 6px;background:#e9eef3;color:#0d2b45;"
      "font-weight:600;border-bottom:1px solid #c5d0db")
THL = ("text-align:left;padding:5px 6px;background:#e9eef3;color:#0d2b45;"
       "font-weight:600;border-bottom:1px solid #c5d0db")
TD = ("text-align:right;padding:4px 6px;border-bottom:1px solid #edf1f4;"
      "white-space:nowrap")
TDW = "text-align:right;padding:4px 6px;border-bottom:1px solid #edf1f4"
TDL = "text-align:left;padding:4px 6px;border-bottom:1px solid #edf1f4"
ZEBRA = "background:#f6f8fa"
FIG = "margin:6px 0 12px 0"
IMG = "max-width:100%;height:auto;display:block"
CAPTION = ("font-size:11px;font-style:italic;color:#5a6b7a;margin:3px 0 0 0;"
           "line-height:1.4;overflow-wrap:anywhere")
PARA = "font-size:13.5px;line-height:1.6;margin:4px 0 10px 0;color:#1a1a1a"
FOOT = ("font-size:11px;color:#6b7785;margin:2px 0 0 0;line-height:1.45;"
        "overflow-wrap:anywhere")

# Kept for callers that still read the old names.
TABLE_NOTE = FOOT
NOTE = FOOT
H2 = SECTION

# A NUMBER, not a name that starts with one: "4.289%", "+4 bp", "772.65 / 758.79"
# and "22 minutes" are right-aligned; "10-year yield" and "2026-10-02" are not.
_NUMERIC = re.compile(r"^[+\-−±]?\$?\d[\d,.]*(?![\w\-])")


def is_number(txt: str) -> bool:
    return bool(_NUMERIC.match(str(txt)))


def cid(chart_id: str) -> str:
    return f"{chart_id.lower()}@chester"


def _chart_html(ch: dict, mode: str) -> str:
    if ch.get("unavailable"):
        return f'<p style="{FOOT}">Chart unavailable: {esc(ch["unavailable"])}</p>'
    src = (f"cid:{cid(ch['id'])}" if mode == "email" else
           esc(str(ch.get("svg_path") or "").replace("\\", "/").split("/")[-1]))
    return (f'<figure style="{FIG}">'
            f'<img src="{src}" alt="{esc(ch.get("caption"))}" style="{IMG}" width="700">'
            f'<figcaption style="{CAPTION}">{esc(ch.get("caption"))}</figcaption>'
            f'</figure>')


def _split(t: dict) -> list[dict]:
    """At most six columns (item 10): a wider table prints as several, each
    repeating its first column."""
    cols = list(t.get("columns") or [])
    if len(cols) <= rd.MAX_TABLE_COLUMNS:
        return [t]
    step = rd.MAX_TABLE_COLUMNS - 1
    out = []
    for a in range(1, len(cols), step):
        idx = [0] + list(range(a, min(a + step, len(cols))))
        out.append({"columns": [cols[i] for i in idx],
                    "rows": [[r[i] if i < len(r) else None for i in idx]
                             for r in t.get("rows") or []]})
    return out


def _cell(v: Any, n: int) -> str:
    txt = "—" if v is None or v == "" else str(v)
    right = n > 0 and is_number(txt)
    style = (TDW if " / " in txt else TD) if right else TDL
    return f'<td style="{style}">{esc(txt)}</td>'


def _table(t: Optional[dict]) -> str:
    if not t or not t.get("rows"):
        return ""
    out = []
    for part in _split(t):
        head = "".join(f'<th style="{THL if n == 0 else TH}">{esc(c)}</th>'
                       for n, c in enumerate(part["columns"]))
        zebra = f' style="{ZEBRA}"'
        body = "".join(
            f'<tr{zebra if k % 2 else ""}>'
            + "".join(_cell(v, n) for n, v in enumerate(r)) + "</tr>"
            for k, r in enumerate(part["rows"]))
        out.append(f'<div style="{SCROLL}"><table style="{TBL}"><tr>{head}</tr>'
                   f'{body}</table></div>')
    return "".join(out)


def lines_table(lines: list[str], head: str = "Readings",
                marks: Optional[list[bool]] = None) -> str:
    """Code-written lines as a one-column table -- never a list (item 1)."""
    if not lines:
        return ""
    rows = [[(DIAMOND + " " if marks and marks[n] else "") + x]
            for n, x in enumerate(lines)]
    return _table({"columns": [head], "rows": rows})


def header_html(s: dict, n: int) -> str:
    sub = (f' <span style="{SUBTITLE}">&mdash; {esc(s["subtitle"])}</span>'
           if s.get("subtitle") else "")
    return f'<h2 style="{SECTION}">{n} &middot; {esc(s["title"])}{sub}</h2>'


def _foot(parts: list[str]) -> str:
    return "".join(f'<p style="{FOOT}">{esc(x)}</p>' for x in parts if x)


def _cadence(name: str) -> dict:
    from . import cadence as cadence_mod                        # noqa: PLC0415
    return cadence_mod.get(name)


def foot_parts(s: dict, fold_subsections: bool = True,
               trimmed_note: str = "Commentary trimmed to one paragraph.") -> list[str]:
    """Everything that is not the block's facts or its reading: the legend,
    what is not yet tracked, and why anything was withheld or cut. With
    `fold_subsections`, the sub-sections' "not yet tracked" print here too."""
    nt = list(s.get("not_tracked") or [])
    if fold_subsections:
        for ss in s.get("subsections") or []:
            nt += list(ss.get("not_tracked") or [])
    nt = list(dict.fromkeys(nt))
    parts = []
    if s.get("empty"):
        parts.append(s.get("empty_note"))
    parts.append(s.get("legend"))
    if nt:
        parts.append("Not yet tracked: " + "; ".join(nt) + ".")
    if s.get("withheld"):
        why = re.sub(r"^(?:narrative\s+)?withheld:\s*", "", str(s["withheld"]),
                     flags=re.I)
        parts.append("Commentary withheld by the audit: " + why)
    parts += list(s.get("notes") or [])
    if s.get("trimmed"):
        parts.append(trimmed_note)
    return [x for x in parts if x]


def _trimmed_note(cad: dict) -> str:
    return ("Commentary trimmed to one paragraph." if cad.get("paragraphs") == 1
            else "(trimmed)")


def footnote(s: dict, cadence: str = "daily") -> str:
    cad = _cadence(cadence)
    return _foot(foot_parts(s, not cad.get("subsection_paragraphs"),
                            _trimmed_note(cad)))


def tables_html(b: dict) -> str:
    """A block's table, then any further tables it carries (`tables`)."""
    return _table(b.get("table")) + "".join(_table(t) for t in b.get("tables") or [])


def subsection_html(ss: dict, period: str, cad: dict, heading: str = H3) -> str:
    """One sub-section: its heading, its tables and lines; on a cadence whose
    sub-sections keep their own paragraphs, those paragraphs and its own
    footnote too. Nothing at all when it has nothing to print."""
    body = tables_html(ss) + lines_table(ss.get("lines") or [], f"This {period}")
    if cad.get("subsection_paragraphs"):
        body += "".join(f'<p style="{PARA}">{esc(p)}</p>'
                        for p in ss.get("paragraphs") or [])
        body += _foot(foot_parts(ss, True, _trimmed_note(cad)))
    return (f'<h3 style="{heading}">{esc(ss.get("title"))}</h3>' + body) if body else ""


def section_html(s: dict, n: int, charts: dict, mode: str,
                 cadence: str = "daily") -> str:
    cad = _cadence(cadence)
    period = s.get("period") or cad["period"]
    out = [header_html(s, n)]
    if s.get("empty"):
        return "".join(out) + footnote(s, cadence)
    if s.get("claim"):
        out.append(f'<p style="{CLAIM}">{esc(s["claim"])}</p>')
    # TABLES: the section's, each sub-section's, then the lines left over.
    # A TABLE'S STANDING NOTE -- how to read it, how its flags are computed --
    # is printed once, in the glossary (table_notes), never under the table.
    out.append(tables_html(s))
    for ss in s.get("subsections") or []:
        out.append(subsection_html(ss, period, cad))
    items = rd.printable_items(s)
    if items:
        out.append(lines_table([i["text"] for i in items],
                               s.get("lines_head") or f"Also this {period}",
                               [bool(i.get("changed")) for i in items]))
    # CHARTS: the section's own, then its sub-sections'.
    ids = list(s.get("charts_rendered") or [])
    for ss in s.get("subsections") or []:
        ids += list(ss.get("charts_rendered") or [])
    for c in ids:
        if c in charts:
            out.append(_chart_html(charts[c], mode))
    # THE PARAGRAPHS THE GUARD KEPT: one on the close and the Weekly.
    limit = cad.get("paragraphs")
    paras = s.get("paragraphs") or []
    for p in (paras[:limit] if limit else paras):
        out.append(f'<p style="{PARA}">{esc(p)}</p>')
    out.append(footnote(s, cadence))
    return "".join(out)


def detail_html(d: dict, cadence: str = "daily") -> str:
    """One detail block: its heading, its tables and lines, its sub-sections,
    its footnote."""
    cad = _cadence(cadence)
    period = cad["period"]
    out = [f'<h3 style="{H3}">{esc(d["title"])}</h3>', tables_html(d),
           lines_table(d.get("lines") or [], f"This {period}")]
    for ss in d.get("subsections") or []:
        out.append(subsection_html(ss, period, cad))
    out.append(_foot(foot_parts(d, False, _trimmed_note(cad))))
    return "".join(out)


def details_html(detail: Optional[list], cadence: str = "daily") -> str:
    """The detail tables after the last section, under one heading; nothing
    when the edition carries none."""
    body = "".join(detail_html(d, cadence) for d in detail or [])
    return (f'<h2 style="{SECTION}">Detail tables</h2>' + body) if body else ""


def page_header(title: str, stamp: str, minutes: int,
                changed: Optional[list[str]] = None,
                changed_head: Optional[str] = None,
                extra_html: str = "") -> str:
    """Title, the as-of in ET, the reading time, and what changed (item 7)."""
    ch = (lines_table(changed, changed_head) if changed and changed_head else "")
    return (f'<h1 style="{H1}">{esc(title)}</h1>'
            f'<p style="{SUB}">{esc(stamp)} &middot; about '
            f'{esc(rd.plural(minutes, "minute"))} to read{extra_html}</p>{ch}')


def page_footer(ed: dict, run_id: Optional[str], archive_path: Optional[str],
                marks: str, pdf_note: Optional[str] = None) -> str:
    """The run's metadata, small, and the one line to the Reader's Guide."""
    meta = (f"Stack {ed.get('config_version')} &middot; "
            f"{esc(rd.plural(int(ed.get('words') or 0), 'word'))} &middot; "
            f"{esc(rd.plural(int(ed.get('chart_count') or 0), 'chart'))} &middot; "
            f"as-of cutoff {esc(rd.stamp_et(ed.get('as_of')))} &middot; run "
            f"{esc(run_id or 'n/a')}")
    lines = [meta, esc(marks)]
    if archive_path:
        lines.append(f"Archived to {esc(archive_path)}.")
    if pdf_note:
        lines.append(esc(pdf_note))
    lines.append(f"How to read this report: {esc(rd.READERS_GUIDE)} "
                 f"({esc(rd.READERS_GUIDE_PATH)}).")
    return (f'<div style="margin:24px 0 0 0;padding-top:8px;border-top:1px solid '
            f'#d5dde5">' + "".join(f'<p style="{FOOT}">{x}</p>' for x in lines)
            + "</div>")


def table_notes(ed: Optional[dict]) -> list[dict]:
    """Each printed table's standing note as a glossary entry named for its
    table (T2.5 item 3): the explanation is kept, once, out of the body."""
    out = []
    for s in (ed or {}).get("sections") or []:
        if s.get("empty"):
            continue
        if s.get("table_note") and (s.get("table") or {}).get("rows"):
            out.append({"term": f"{s['title']} table", "text": s["table_note"]})
        for ss in s.get("subsections") or []:
            if ss.get("table_note") and (ss.get("table") or {}).get("rows"):
                out.append({"term": str(ss.get("title")), "text": ss["table_note"]})
    return out


def glossary_html(entries: list[dict], ed: Optional[dict] = None) -> str:
    """The glossary, printed once at the end of an edition, as a table: the
    declared terms, the tables' standing notes, and the standing notes that
    left the body (T2.5 item 3)."""
    entries = list(entries or []) + table_notes(ed)
    entries += [e for e in rd.STANDING_NOTES
                if e["term"] not in {x.get("term") for x in entries}]
    if not entries:
        return ""
    rows = [[e.get("term"), e.get("text")] for e in entries]
    return (f'<h2 style="{SECTION}">Glossary</h2>'
            + _table({"columns": ["Term", "Meaning"], "rows": rows}))


def _marks(ed: dict, what: str) -> str:
    if ed.get("prior_session"):
        try:
            when = rd.prose_date(ed["prior_session"])
        except ValueError:
            when = ed["prior_session"]
        return f"{DIAMOND} marks a line that changed since the {what} of {when}."
    return (f"No prior stacked {what} to compare against: nothing is marked as "
            f"changed and nothing collapses.")


def render(p: dict, ed: dict, charts: dict, mode: str = "email",
           delivery: Optional[dict] = None) -> str:
    """The daily close."""
    from altdata import labels                                  # noqa: PLC0415
    from . import state_block                                   # noqa: PLC0415
    secs = "".join(section_html(s, n, charts, mode)
                   for n, s in enumerate(ed["sections"], start=1))
    warn = ""
    if p.get("warnings"):
        warn = lines_table([str(w) for w in p["warnings"]], "Warnings")
    try:
        day = rd.prose_date(p.get("session"))
        dow = __import__("datetime").date.fromisoformat(p["session"]).strftime("%a")
    except (ValueError, TypeError, KeyError):
        day, dow = str(p.get("session")), ""
    events = state_block.session_events_line(p)
    head = page_header(f"Close — {dow} {day}".strip(), rd.stamp_et(ed.get("as_of")),
                       rd.reading_minutes(ed, int(ed.get("chart_count") or 0)),
                       extra_html=f" &middot; {events}")
    try:
        gl = labels.glossary()
    except Exception:                                           # noqa: BLE001
        gl = []
    return (f'<div style="{WRAP}">{head}{warn}{secs}'
            f'{details_html(ed.get("detail"), "daily")}{glossary_html(gl, ed)}'
            + page_footer(ed, p.get("run_id"), (delivery or {}).get("archive_path"),
                          _marks(ed, "close"), ed.get("pdf_note"))
            + "</div>")
