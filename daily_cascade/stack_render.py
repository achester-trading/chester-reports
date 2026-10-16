"""
The stacked editions' HTML: the daily close, the Weekly and the Monthly, one
renderer. (T1; T2.5; T2.6; T2.7)

    html = stack_render.render(payload, edition, charts, mode="email")
    one = stack_render.section_html(section, n, charts, mode, cadence="monthly")
    tail = stack_render.details_html(edition["detail"], cadence="monthly")
    page = stack_render.page_html(edition, "monthly", title, mode, charts,
                                  "Changed since last Monthly", "Monthly")
    md = stack_render.markdown(edition, "monthly", title,
                               "Changed since last Monthly", "Monthly")

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

THE MONTHLY'S LONG FORM (T2.7), all per cadence from config: a sub-section
carries its own charts (`subsection_charts`) and notes; any block may carry
READING ENTRIES (entries_html) -- a hyperlinked title line, then a stored summary
printed escaped and otherwise verbatim, never polished, audited or trimmed;
page_html prints a whole edition and markdown() the same edition in the same
order, each chart as an image line where the HTML places it.

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
# ON THE PHONE (T3.1 item 1, the Monthly; config `cadences: mobile_tables`). Gmail
# on iPhone ignores SCROLL's horizontal scrolling, so one table wider than the
# screen zooms the whole email out. A cadence that sets `mobile_tables` therefore
# lets a text cell wrap anywhere (a URL, a long series name) while a number keeps
# TD's nowrap, and fixes the column layout of a table that came in wider than six
# columns, so its parts lay out to the screen rather than to their longest cell.
TDL_WRAP = TDL + ";overflow-wrap:anywhere;word-break:break-word"
TBL_FIXED = TBL + ";table-layout:fixed"
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


def _cell(v: Any, n: int, wrap: bool = False) -> str:
    txt = "—" if v is None or v == "" else str(v)
    right = n > 0 and is_number(txt)
    style = (TDW if " / " in txt else TD) if right else (TDL_WRAP if wrap else TDL)
    return f'<td style="{style}">{esc(txt)}</td>'


def _table(t: Optional[dict], wrap: bool = False) -> str:
    """`wrap`: the cadence's `mobile_tables` (T3.1 item 1) -- text cells wrap,
    numbers do not, and a table wider than six columns lays out fixed."""
    if not t or not t.get("rows"):
        return ""
    out = []
    tbl = (TBL_FIXED if wrap and len(t.get("columns") or []) > rd.MAX_TABLE_COLUMNS
           else TBL)
    parts = _split(t)
    # A CELL'S LINK (W-1.2 item 2.4): `cell_links` [[row, column, href], ...] on
    # the table, applied where the table prints whole -- "resolved by Plumbing"
    # links to the section that holds the evidence.
    links = ({(int(r), int(c)): h for r, c, h in t.get("cell_links") or []}
             if len(parts) == 1 else {})
    for part in parts:
        head = "".join(f'<th style="{THL if n == 0 else TH}">{esc(c)}</th>'
                       for n, c in enumerate(part["columns"]))
        zebra = f' style="{ZEBRA}"'
        body = "".join(
            f'<tr{zebra if k % 2 else ""}>'
            + "".join((f'<td style="{TDL_WRAP if wrap else TDL}">{_a(v, links[(k, n)])}'
                       f'</td>') if (k, n) in links else _cell(v, n, wrap)
                      for n, v in enumerate(r)) + "</tr>"
            for k, r in enumerate(part["rows"]))
        out.append(f'<div style="{SCROLL}"><table style="{tbl}"><tr>{head}</tr>'
                   f'{body}</table></div>')
    return "".join(out)


def lines_table(lines: list[str], head: str = "Readings",
                marks: Optional[list[bool]] = None, wrap: bool = False) -> str:
    """Code-written lines as a one-column table -- never a list (item 1)."""
    if not lines:
        return ""
    rows = [[(DIAMOND + " " if marks and marks[n] else "") + x]
            for n, x in enumerate(lines)]
    return _table({"columns": [head], "rows": rows}, wrap)


def header_html(s: dict, n: int) -> str:
    sub = (f' <span style="{SUBTITLE}">&mdash; {esc(s["subtitle"])}</span>'
           if s.get("subtitle") else "")
    anchor = f' id="sec-{esc(s["id"])}"' if s.get("id") else ""
    return f'<h2 style="{SECTION}"{anchor}>{n} &middot; {esc(s["title"])}{sub}</h2>'


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


def tables_html(b: dict, wrap: bool = False) -> str:
    """A block's table, then any further tables it carries (`tables`)."""
    return (_table(b.get("table"), wrap)
            + "".join(_table(t, wrap) for t in b.get("tables") or []))


LINK = "color:#0d2b45;text-decoration:underline"
META = "color:#475569"
# POINTS (T3.1 item 7, the Monthly's What doesn't fit): a short header, one
# sentence, then the figures as bullets -- the one place a stacked edition prints
# a list, because the operator ruled the table carried the message less well.
POINT_HEAD = ("font-size:13px;font-weight:600;color:#0d2b45;margin:10px 0 2px 0;"
              "line-height:1.4")
BULLETS = "margin:2px 0 10px 0;padding-left:18px;font-size:12.5px;line-height:1.5"
BULLET = "margin:0 0 2px 0;overflow-wrap:anywhere"
BULLET_SOURCE = "font-size:11px;color:#6b7785;line-height:1.4"


def _bullet(x: Any) -> str:
    """A bullet is a string, or {"text", "source"}: the source prints on its
    own line under the bullet (T3.1 item 17, the voices)."""
    if isinstance(x, dict):
        src = (f'<br><span style="{BULLET_SOURCE}">{esc(x["source"])}</span>'
               if x.get("source") else "")
        return f'<li style="{BULLET}">{esc(x.get("text"))}{src}</li>'
    return f'<li style="{BULLET}">{esc(x)}</li>'


def _a(text: Any, url: Optional[str]) -> str:
    if not url:
        return esc(text)
    return f'<a href="{esc(url)}" style="{LINK}">{esc(text)}</a>'


def entries_html(b: dict) -> str:
    """A block's READING ENTRIES (T2.7; the Monthly's Reading chapter): for each,
    the hyperlinked title line -- the publication, its meta, a link to the scan,
    a list item's one line -- then the stored summary as a paragraph. A summary
    is STORED TEXT: HTML-escaped and otherwise printed exactly as stored --
    never polished, audited or trimmed, outside the prose budget, inside the
    reading time (readability.stored_words). Nothing when the block has none."""
    out = []
    for e in b.get("entries") or []:
        head = f"<strong>{_a(e.get('publication'), e.get('url'))}</strong>"
        if e.get("meta"):
            head += f' <span style="{META}">— {esc(e["meta"])}</span>'
        if e.get("scan_url"):
            head += f' <span style="{META}">· {_a("scan", e["scan_url"])}</span>'
        if e.get("line"):
            head += f" — {esc(e['line'])}"
        out.append(f'<p style="{PARA}">{head}</p>')
        if e.get("summary"):
            out.append(f'<p style="{PARA}">{esc(e["summary"])}</p>')
    return "".join(out)


def points_html(b: dict) -> str:
    """A block's POINTS (T3.1 item 7): for each, its header, its one sentence
    and its bullets. Code-written from the block's data; nothing when the block
    carries none -- only the Monthly's builders set them."""
    out = []
    for pt in b.get("points") or []:
        out.append(f'<p style="{POINT_HEAD}">{esc(pt.get("head"))}</p>')
        if pt.get("sentence"):
            out.append(f'<p style="{PARA}">{esc(pt["sentence"])}</p>')
        for x in pt.get("more") or []:
            out.append(f'<p style="{PARA}">{esc(x)}</p>')
        if pt.get("bullets"):
            out.append(f'<ul style="{BULLETS}">'
                       + "".join(_bullet(x) for x in pt["bullets"]) + "</ul>")
    return "".join(out)


def charts_html(b: dict, charts: Optional[dict], mode: str) -> str:
    """The charts a block carries (`charts_rendered`) that were drawn: `cid:` in
    the email, the SVG's file name beside the archived HTML."""
    return "".join(_chart_html(charts[c], mode)
                   for c in b.get("charts_rendered") or [] if c in (charts or {}))


def subsection_html(ss: dict, period: str, cad: dict, heading: str = H3,
                    charts: Optional[dict] = None, mode: str = "email") -> str:
    """One sub-section: its heading, its tables, its reading entries and its
    lines; on a cadence whose sub-sections carry their own charts, those charts;
    on one whose sub-sections keep their own paragraphs, those paragraphs and
    its own footnote (its notes, what it does not track, why anything was
    withheld) too. Nothing at all when it has nothing to print.

    A DIVIDER (AQ-1, the Quarterly): a sub-section carrying `divider` is the line
    between a chapter's lead items and its reference items -- its heading and
    its one line, nothing else."""
    if ss.get("divider"):
        return (f'<h3 style="{heading}">{esc(ss["divider"])}</h3>'
                + (f'<p style="{FOOT}">{esc(ss["divider_note"])}</p>'
                   if ss.get("divider_note") else ""))
    wrap = bool(cad.get("mobile_tables"))
    # A LEAD (ST-R6.45d, the ES block): a paragraph printed BEFORE the tables --
    # the block's read comes first on a phone, then its levels.
    lead = (f'<p style="{PARA}" class="lead">{esc(ss["lead"])}</p>'
            if ss.get("lead") else "")
    body = (lead + tables_html(ss, wrap) + entries_html(ss) + points_html(ss)
            + lines_table(ss.get("lines") or [], f"This {period}", wrap=wrap))
    figs = charts_html(ss, charts, mode) if cad.get("subsection_charts") else ""
    paras = foot = ""
    if cad.get("subsection_paragraphs"):
        paras = "".join(f'<p style="{PARA}">{esc(p)}</p>'
                        for p in ss.get("paragraphs") or [])
        foot = _foot(foot_parts(ss, True, _trimmed_note(cad)))
    # A sub-section may print its charts UNDER its paragraph (T3.1 item 8, the
    # Monthly's Plumbing buckets); otherwise they print above it.
    body += (paras + figs if ss.get("charts_after_prose") else figs + paras) + foot
    return (f'<h3 style="{heading}">{esc(ss.get("title"))}</h3>' + body) if body else ""


def section_html(s: dict, n: int, charts: dict, mode: str,
                 cadence: str = "daily") -> str:
    cad = _cadence(cadence)
    wrap = bool(cad.get("mobile_tables"))
    period = s.get("period") or cad["period"]
    out = [header_html(s, n)]
    if s.get("empty"):
        return "".join(out) + footnote(s, cadence)
    if cad.get("opener"):
        return opener_section_html(s, out, charts, mode, cad, period, wrap)
    # THE RELEVANCE SENTENCE (W-1.2 item 2.3): the précis's one sentence tying
    # the section to the week's tension, at the head of its commentary.
    if s.get("relevance") and s.get("claim"):
        out.append(f'<p style="{PARA}" class="relevance"><i>'
                   f'{esc(s["relevance"])}</i></p>')
    if s.get("claim"):
        out.append(f'<p style="{CLAIM}">{esc(s["claim"])}</p>')
    # TABLES: the section's, each sub-section's, then the lines left over.
    # A TABLE'S STANDING NOTE -- how to read it, how its flags are computed --
    # is printed once, in the glossary (table_notes), never under the table.
    out.append(tables_html(s, wrap) + entries_html(s) + points_html(s))
    for ss in s.get("subsections") or []:
        out.append(subsection_html(ss, period, cad, charts=charts, mode=mode))
    # COLLAPSED BY DEFAULT (W-1.2 item 2.6): one line each in the read path, the
    # rows in the reference tables after the last section.
    if s.get("summarised"):
        out.append(lines_table(list(s["summarised"]),
                               "Summarised; the rows are in the reference tables",
                               wrap=wrap))
    items = rd.printable_items(s)
    if items:
        out.append(lines_table([i["text"] for i in items],
                               s.get("lines_head") or f"Also this {period}",
                               [bool(i.get("changed")) for i in items], wrap))
    # CHARTS: the section's own, then -- on a cadence whose sub-sections do not
    # carry their own (the close, the Weekly) -- its sub-sections'.
    ids = list(s.get("charts_rendered") or [])
    if not cad.get("subsection_charts"):
        for ss in s.get("subsections") or []:
            ids += list(ss.get("charts_rendered") or [])
    for c in ids:
        if c in (charts or {}):
            out.append(_chart_html(charts[c], mode))
    # THE PARAGRAPHS THE GUARD KEPT: one on the close and the Weekly.
    limit = cad.get("paragraphs")
    paras = s.get("paragraphs") or []
    for p in (paras[:limit] if limit else paras):
        out.append(f'<p style="{PARA}">{esc(p)}</p>')
    # A CODE-AND-FRAME CLOSING LINE (W-1.2 item 2.5: the book's terms).
    for ln in s.get("closing_lines") or []:
        out.append(f'<p style="{PARA}" class="closing"><b>{esc(ln)}</b></p>')
    out.append(footnote(s, cadence))
    return "".join(out)


OPENER = PARA + ";margin:6px 0 12px 0"


def opener_html(s: dict) -> str:
    """W-1.3a item 3.0: the section's commentary as ONE paragraph -- the
    relevance sentence, the claim, the body, and the Takeaway with its word in
    bold -- or, when it was withheld, the withholding line in its place.

    ONLY THE LABEL IS BOLD (W-1.3c item 4). The claim was set in bold, and in dry
    run #6 the claim was a generic definition, so the most prominent text in
    each section said nothing about the week. The claim prints in the
    paragraph's weight; "Takeaway:" is the one bold run."""
    from . import opener                                        # noqa: PLC0415
    c = opener.commentary(s)
    if c is None:
        w = opener.withheld_line(s)
        return (f'<p style="{OPENER}" class="opener withheld"><i>{esc(w)}</i></p>'
                if w else "")
    parts = []
    if c["relevance"]:
        parts.append(f'<span class="relevance">{esc(c["relevance"])}</span>')
    if c["claim"]:
        parts.append(f'<span class="claim">{esc(c["claim"])}</span>')
    if c["body"]:
        parts.append(esc(c["body"]))
    if c["takeaway"]:
        parts.append(f'<span class="takeaway"><b>{opener.TAKEAWAY}:</b> '
                     f'{esc(c["takeaway"])}</span>')
    return f'<p style="{OPENER}" class="opener">' + " ".join(parts) + "</p>"


def opener_section_html(s: dict, out: list, charts: dict, mode: str, cad: dict,
                        period: str, wrap: bool) -> str:
    """A section on a cadence with an opener: the commentary first, then the
    tables, the sub-sections, the collapsed lines, the items and the charts;
    the code-written closing lines; the footnote (whose withheld note has moved
    up to where the paragraph would be)."""
    limit = cad.get("paragraphs")
    out.append(opener_html({**s, "paragraphs": (s.get("paragraphs") or [])[:limit]}
                           if limit else s))
    out.append(tables_html(s, wrap) + entries_html(s) + points_html(s))
    for ss in s.get("subsections") or []:
        out.append(subsection_html(ss, period, cad, charts=charts, mode=mode))
    if s.get("summarised"):
        out.append(lines_table(list(s["summarised"]),
                               "Summarised; the rows are in the reference tables",
                               wrap=wrap))
    items = rd.printable_items(s)
    if items:
        out.append(lines_table([i["text"] for i in items],
                               s.get("lines_head") or f"Also this {period}",
                               [bool(i.get("changed")) for i in items], wrap))
    ids = list(s.get("charts_rendered") or [])
    if not cad.get("subsection_charts"):
        for ss in s.get("subsections") or []:
            ids += list(ss.get("charts_rendered") or [])
    for c in ids:
        if c in (charts or {}):
            out.append(_chart_html(charts[c], mode))
    for ln in s.get("closing_lines") or []:
        out.append(f'<p style="{PARA}" class="closing"><b>{esc(ln)}</b></p>')
    out.append(_foot(foot_parts({**s, "withheld": None}, not cad.get(
        "subsection_paragraphs"), _trimmed_note(cad))))
    return "".join(out)


def detail_html(d: dict, cadence: str = "daily") -> str:
    """One detail block: its heading, its tables and lines, its sub-sections,
    its footnote."""
    cad = _cadence(cadence)
    wrap = bool(cad.get("mobile_tables"))
    period = cad["period"]
    out = [f'<h3 style="{H3}">{esc(d["title"])}</h3>', tables_html(d, wrap),
           lines_table(d.get("lines") or [], f"This {period}", wrap=wrap)]
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
                extra_html: str = "", wrap: bool = False,
                reading: Optional[str] = None) -> str:
    """Title, the as-of in ET, the reading time, and what changed (item 7).
    `reading` replaces the one reading time with an edition's own line (AQ-1:
    the Quarterly's two paths)."""
    ch = (lines_table(changed, changed_head, wrap=wrap)
          if changed and changed_head else "")
    rt = (esc(reading) if reading else
          f'about {esc(rd.plural(minutes, "minute"))} to read')
    return (f'<h1 style="{H1}">{esc(title)}</h1>'
            f'<p style="{SUB}">{esc(stamp)} &middot; {rt}{extra_html}</p>{ch}')


def reading_line(ed: dict) -> Optional[str]:
    """THE TWO PATHS' READING TIMES (AQ-1, change order section 3): "the read:
    n min; the whole edition: m min" where the edition times its read apart
    (`read_minutes`); None for every other edition."""
    if ed.get("read_minutes") is None:
        return None
    return (f"the read: {int(ed['read_minutes'])} min; the whole edition: "
            f"{edition_minutes(ed)} min")


def page_footer(ed: dict, run_id: Optional[str], archive_path: Optional[str],
                marks: str, pdf_note: Optional[str] = None) -> str:
    """The run's metadata, small, and the one line to the Reader's Guide."""
    meta = (f"Stack {ed.get('config_version')} &middot; "
            f"{esc(rd.plural(int(ed.get('words') or 0), 'word'))} &middot; "
            f"{esc(rd.plural(int(ed.get('chart_count') or 0), 'chart'))} &middot; "
            f"as-of cutoff {esc(rd.stamp_et(ed.get('as_of')))} &middot; run "
            f"{esc(run_id or 'n/a')}")
    lines = [meta, esc(marks)]
    # AUD-2 item 4: the model meter -- the close's one line, the Monthly's month
    # by report. Tokens, never dollars.
    for x in ([ed["model_line"]] if ed.get("model_line") else []) + list(
            ed.get("model_lines") or []):
        lines.append(esc(x) + ("" if str(x).endswith(".") else "."))
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


def glossary_html(entries: list[dict], ed: Optional[dict] = None,
                  wrap: bool = False, stamp: Optional[str] = None) -> str:
    """The glossary, printed once at the end of an edition, as a table: the
    declared terms, the tables' standing notes, and the standing notes that
    left the body (T2.5 item 3)."""
    entries = list(entries or []) + table_notes(ed)
    entries += [e for e in rd.STANDING_NOTES
                if e["term"] not in {x.get("term") for x in entries}]
    if not entries:
        return ""
    rows = [[e.get("term"), e.get("text")] for e in entries]
    # THE DEFINITIONS-VERSION STAMP (W-1.3a item 3.7): which config the terms
    # were rendered from.
    st = (f'<p style="{FOOT}" class="definitions-version">Definitions version '
          f'{esc(stamp)} (the config\'s git short hash at render).</p>'
          if stamp else "")
    return (f'<h2 style="{SECTION}">Glossary</h2>' + st
            + _table({"columns": ["Term", "Meaning"], "rows": rows}, wrap))


def _marks(ed: dict, what: str) -> str:
    if ed.get("prior_session"):
        try:
            when = rd.prose_date(ed["prior_session"])
        except ValueError:
            when = ed["prior_session"]
        return f"{DIAMOND} marks a line that changed since the {what} of {when}."
    return (f"No prior stacked {what} to compare against: nothing is marked as "
            f"changed and nothing collapses.")


# What the footer's change-mark line calls the prior edition, by cadence.
EDITION_NAMES = {"daily": "close", "weekly": "Weekly", "monthly": "Monthly",
                 "quarterly": "Quarterly"}


def _glossary_entries() -> list[dict]:
    try:
        from altdata import labels                              # noqa: PLC0415
        return labels.glossary()
    except Exception:                                           # noqa: BLE001
        return []


def edition_minutes(ed: dict) -> int:
    """The header's reading time: the edition's own figure where its budget step
    set one, else readability.reading_minutes over it."""
    return int(ed.get("reading_minutes") or rd.reading_minutes(ed))


def summary_html(ed: dict) -> str:
    """THE EXECUTIVE SUMMARY (T3.1 item 20, the Monthly's): after the header and
    before section 1, one paragraph per section under the section's name, with
    the short path's own reading time -- the summary with section 1. Nothing
    when the edition carries no summary (every other report)."""
    summ = ed.get("summary") or []
    if not summ:
        return ""
    mins = ed.get("summary_minutes")
    out = [f'<h2 style="{SECTION}">Executive summary</h2>']
    if mins:
        out.append(f'<p style="{SUB}">About {esc(rd.plural(int(mins), "minute"))} to '
                   f'read, with section 1 &middot; the short path</p>')
    for e in summ:
        out.append(f'<p style="{PARA}"><strong>{esc(e.get("title"))}.</strong> '
                   f'{esc(e.get("text") or e.get("note") or "")}</p>')
    return "".join(out)


def md_summary(ed: dict) -> list[str]:
    """As summary_html, for the Markdown."""
    summ = ed.get("summary") or []
    if not summ:
        return []
    out = ["## Executive summary\n"]
    if ed.get("summary_minutes"):
        out.append(f"*About {rd.plural(int(ed['summary_minutes']), 'minute')} to "
                   f"read, with section 1 · the short path*\n")
    out += [f"**{e.get('title')}.** {e.get('text') or e.get('note') or ''}\n"
            for e in summ]
    return out


def page_html(ed: dict, cadence: str, title: str, mode: str = "email",
              charts: Optional[dict] = None, changed_head: Optional[str] = None,
              what: Optional[str] = None) -> str:
    """A whole stacked edition at `cadence` (T2.7, the Monthly's page): the
    header -- the title, the as-of in ET, the reading time and, where the
    edition carries one, its target; what changed since the last edition under
    `changed_head` -- then every section, the detail tables, the glossary and
    the footer, whose change-mark line names the prior edition as `what`.
    `charts` defaults to the edition's own."""
    charts = charts if charts is not None else (ed.get("charts") or {})
    wrap = bool(_cadence(cadence).get("mobile_tables"))
    secs = "".join(section_html(s, n, charts, mode, cadence)
                   for n, s in enumerate(ed["sections"], start=1))
    target = ed.get("reading_target_minutes")
    head = page_header(title, rd.stamp_et(ed.get("as_of")), edition_minutes(ed),
                       ed.get("changed_since") or [], changed_head,
                       extra_html=(f" &middot; target {esc(target)} minutes"
                                   + (" for the read" if reading_line(ed) else "")
                                   if target else ""), wrap=wrap,
                       reading=reading_line(ed))
    return (f'<div style="{WRAP}">{head}{summary_html(ed)}{secs}'
            f'{details_html(ed.get("detail"), cadence)}'
            f'{glossary_html(_glossary_entries(), ed, wrap)}'
            + page_footer(ed, ed.get("run_id"), ed.get("archive_path"),
                          _marks(ed, what or EDITION_NAMES.get(cadence, cadence)))
            + "</div>")


# ---------------------------------------------------------------------------
# The Markdown: the same edition in the same order (T2.7) -- the attachment and
# the text fallback. Computes nothing.
# ---------------------------------------------------------------------------
def _md_cell(v: Any) -> str:
    return str("—" if v in (None, "") else v).replace("|", "/").replace("\n", " ")


def md_table(t: Optional[dict]) -> list[str]:
    if not t or not t.get("rows"):
        return []
    return (["| " + " | ".join(_md_cell(c) for c in t["columns"]) + " |",
             "|" + "---|" * len(t["columns"])]
            + ["| " + " | ".join(_md_cell(c) for c in r) + " |" for r in t["rows"]]
            + [""])


def _md_link(text: Any, url: Optional[str]) -> str:
    t = str(text or "").replace("[", "(").replace("]", ")")
    return f"[{t}]({url})" if url else t


def md_entries(b: dict) -> list[str]:
    """As entries_html: the title line, then the stored summary verbatim."""
    out = []
    for e in b.get("entries") or []:
        head = f"**{_md_link(e.get('publication'), e.get('url'))}**"
        if e.get("meta"):
            head += f" — {e['meta']}"
        if e.get("scan_url"):
            head += f" · {_md_link('scan', e['scan_url'])}"
        if e.get("line"):
            head += f" — {e['line']}"
        out.append(head + "\n")
        if e.get("summary"):
            out.append(f"{e['summary']}\n")
    return out


def md_points(b: dict) -> list[str]:
    """As points_html: the header in bold, the sentence, the bullets."""
    out = []
    for pt in b.get("points") or []:
        out.append(f"**{pt.get('head')}**\n")
        if pt.get("sentence"):
            out.append(f"{pt['sentence']}\n")
        out += [f"{x}\n" for x in pt.get("more") or []]
        for x in pt.get("bullets") or []:
            if isinstance(x, dict):
                out.append(f"- {x.get('text')}"
                           + (f"  \n  <sub>{x['source']}</sub>" if x.get("source")
                              else ""))
            else:
                out.append(f"- {x}")
        if pt.get("bullets"):
            out.append("")
    return out


def md_block(b: dict) -> list[str]:
    """A block's table, its reading entries, its points, its further tables,
    its lines."""
    out = md_table(b.get("table")) + md_entries(b) + md_points(b)
    for t in b.get("tables") or []:
        out += md_table(t)
    out += [f"- {x}" for x in b.get("lines") or []]
    if b.get("lines"):
        out.append("")
    return out


def md_charts(ids: list, charts: Optional[dict]) -> list[str]:
    """Each drawn chart as an image line: the SVG beside the archived Markdown,
    its caption as the alt text; an unavailable chart says why."""
    out = []
    for c in ids:
        x = (charts or {}).get(c)
        if not x:
            continue
        if x.get("unavailable"):
            out.append(f"*Chart unavailable: {x['unavailable']}*\n")
            continue
        svg = str(x.get("svg_path") or "").replace("\\", "/").split("/")[-1]
        out.append(f"![{_md_cell(x.get('caption'))}]({svg})\n" if svg else
                   f"*{_md_cell(x.get('caption'))}*\n")
    return out


def _md_foot(parts: list[str]) -> list[str]:
    return [f"<sub>{x}</sub>\n" for x in parts]


def _md_sub(ss: dict, cad: dict, charts: Optional[dict], level: str = "###",
            with_charts: bool = True) -> list[str]:
    if ss.get("divider"):
        return [f"{level} {ss['divider']}\n"] + (
            [f"<sub>{ss['divider_note']}</sub>\n"] if ss.get("divider_note") else [])
    body = ([f"{ss['lead']}\n"] if ss.get("lead") else []) + md_block(ss)
    figs = (md_charts(list(ss.get("charts_rendered") or []), charts)
            if with_charts and cad.get("subsection_charts") else [])
    paras, foot = [], []
    if cad.get("subsection_paragraphs"):
        paras = [f"{p}\n" for p in ss.get("paragraphs") or []]
        foot = _md_foot(foot_parts(ss, True, _trimmed_note(cad)))
    body += (paras + figs if ss.get("charts_after_prose") else figs + paras) + foot
    return ([f"{level} {ss.get('title')}\n"] + body) if body else []


def markdown(ed: dict, cadence: str, title: str, changed_head: Optional[str] = None,
             what: Optional[str] = None, charts: Optional[dict] = None) -> str:
    """The edition as Markdown, in page_html's order: sections (their tables,
    entries, sub-sections, lines, charts, paragraphs, footnotes), the detail
    tables, and the run's line."""
    cad = _cadence(cadence)
    charts = charts if charts is not None else (ed.get("charts") or {})
    target = ed.get("reading_target_minutes")
    rl = reading_line(ed)
    out = [f"# {title}\n",
           f"*{rd.stamp_et(ed.get('as_of'))} · "
           + (rl if rl else
              f"about {rd.plural(edition_minutes(ed), 'minute')} to read")
           + (f" · target {target} minutes" + (" for the read" if rl else "")
              if target else "") + "*\n"]
    if ed.get("changed_since") and changed_head:
        out.append(f"**{changed_head}**\n")
        out += [f"- {x}" for x in ed["changed_since"]] + [""]
    out += md_summary(ed)
    limit = cad.get("paragraphs")
    for n, s in enumerate(ed["sections"], start=1):
        out.append(f"## {n} · {s['title']}" + (f" — *{s['subtitle']}*"
                                               if s.get("subtitle") else "") + "\n")
        if s.get("empty"):
            out += _md_foot(foot_parts(s, not cad.get("subsection_paragraphs"),
                                       _trimmed_note(cad)))
            continue
        if s.get("claim"):
            # W-1.3c item 4: an opener's claim is not bold.
            out.append(f"{s['claim']}\n" if cad.get("opener")
                       else f"**{s['claim']}**\n")
        out += md_block(s)
        for ss in s.get("subsections") or []:
            out += _md_sub(ss, cad, charts)
        items = rd.printable_items(s)
        out += [f"- {DIAMOND + ' ' if i.get('changed') else ''}{i['text']}"
                for i in items]
        if items:
            out.append("")
        ids = list(s.get("charts_rendered") or [])
        if not cad.get("subsection_charts"):
            for ss in s.get("subsections") or []:
                ids += list(ss.get("charts_rendered") or [])
        out += md_charts(ids, charts)
        paras = s.get("paragraphs") or []
        out += [f"{p}\n" for p in (paras[:limit] if limit else paras)]
        out += _md_foot(foot_parts(s, not cad.get("subsection_paragraphs"),
                                   _trimmed_note(cad)))
    if ed.get("detail"):
        out.append("## Detail tables\n")
        for d in ed["detail"]:
            out.append(f"### {d['title']}\n")
            out += md_block(d)
            for ss in d.get("subsections") or []:
                out += _md_sub(ss, cad, charts, "####", with_charts=False)
            out += _md_foot(foot_parts(d, False, _trimmed_note(cad)))
    out.append(f"\n*Stack {ed.get('config_version')} · "
               f"{rd.plural(int(ed.get('words') or 0), 'word')} · "
               f"{rd.plural(int(ed.get('chart_count') or 0), 'chart')} · run "
               f"{ed.get('run_id') or 'n/a'}. "
               f"{_marks(ed, what or EDITION_NAMES.get(cadence, cadence))}*\n")
    return "\n".join(out)


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
                       extra_html=f" &middot; {events}" + (
                           f' &middot; {esc(ed["alpha_lab"])}' if ed.get("alpha_lab") else ""))
    try:
        gl = labels.glossary()
    except Exception:                                           # noqa: BLE001
        gl = []
    return (f'<div style="{WRAP}">{head}{warn}{secs}'
            f'{details_html(ed.get("detail"), "daily")}{glossary_html(gl, ed)}'
            + page_footer(ed, p.get("run_id"), (delivery or {}).get("archive_path"),
                          _marks(ed, "close"), ed.get("pdf_note"))
            + "</div>")
