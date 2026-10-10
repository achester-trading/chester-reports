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
    for part in _split(t):
        head = "".join(f'<th style="{THL if n == 0 else TH}">{esc(c)}</th>'
                       for n, c in enumerate(part["columns"]))
        zebra = f' style="{ZEBRA}"'
        body = "".join(
            f'<tr{zebra if k % 2 else ""}>'
            + "".join(_cell(v, n, wrap) for n, v in enumerate(r)) + "</tr>"
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


def tables_html(b: dict, wrap: bool = False) -> str:
    """A block's table, then any further tables it carries (`tables`)."""
    return (_table(b.get("table"), wrap)
            + "".join(_table(t, wrap) for t in b.get("tables") or []))


LINK = "color:#0d2b45;text-decoration:underline"
META = "color:#475569"


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
    withheld) too. Nothing at all when it has nothing to print."""
    wrap = bool(cad.get("mobile_tables"))
    body = (tables_html(ss, wrap) + entries_html(ss)
            + lines_table(ss.get("lines") or [], f"This {period}", wrap=wrap))
    if cad.get("subsection_charts"):
        body += charts_html(ss, charts, mode)
    if cad.get("subsection_paragraphs"):
        body += "".join(f'<p style="{PARA}">{esc(p)}</p>'
                        for p in ss.get("paragraphs") or [])
        body += _foot(foot_parts(ss, True, _trimmed_note(cad)))
    return (f'<h3 style="{heading}">{esc(ss.get("title"))}</h3>' + body) if body else ""


def section_html(s: dict, n: int, charts: dict, mode: str,
                 cadence: str = "daily") -> str:
    cad = _cadence(cadence)
    wrap = bool(cad.get("mobile_tables"))
    period = s.get("period") or cad["period"]
    out = [header_html(s, n)]
    if s.get("empty"):
        return "".join(out) + footnote(s, cadence)
    if s.get("claim"):
        out.append(f'<p style="{CLAIM}">{esc(s["claim"])}</p>')
    # TABLES: the section's, each sub-section's, then the lines left over.
    # A TABLE'S STANDING NOTE -- how to read it, how its flags are computed --
    # is printed once, in the glossary (table_notes), never under the table.
    out.append(tables_html(s, wrap) + entries_html(s))
    for ss in s.get("subsections") or []:
        out.append(subsection_html(ss, period, cad, charts=charts, mode=mode))
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
    out.append(footnote(s, cadence))
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
                extra_html: str = "", wrap: bool = False) -> str:
    """Title, the as-of in ET, the reading time, and what changed (item 7)."""
    ch = (lines_table(changed, changed_head, wrap=wrap)
          if changed and changed_head else "")
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


def glossary_html(entries: list[dict], ed: Optional[dict] = None,
                  wrap: bool = False) -> str:
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
EDITION_NAMES = {"daily": "close", "weekly": "Weekly", "monthly": "Monthly"}


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
                                   if target else ""), wrap=wrap)
    return (f'<div style="{WRAP}">{head}{secs}'
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


def md_block(b: dict) -> list[str]:
    """A block's table, its reading entries, its further tables, its lines."""
    out = md_table(b.get("table")) + md_entries(b)
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
    body = md_block(ss)
    if with_charts and cad.get("subsection_charts"):
        body += md_charts(list(ss.get("charts_rendered") or []), charts)
    if cad.get("subsection_paragraphs"):
        body += [f"{p}\n" for p in ss.get("paragraphs") or []]
        body += _md_foot(foot_parts(ss, True, _trimmed_note(cad)))
    return ([f"{level} {ss.get('title')}\n"] + body) if body else []


def markdown(ed: dict, cadence: str, title: str, changed_head: Optional[str] = None,
             what: Optional[str] = None, charts: Optional[dict] = None) -> str:
    """The edition as Markdown, in page_html's order: sections (their tables,
    entries, sub-sections, lines, charts, paragraphs, footnotes), the detail
    tables, and the run's line."""
    cad = _cadence(cadence)
    charts = charts if charts is not None else (ed.get("charts") or {})
    target = ed.get("reading_target_minutes")
    out = [f"# {title}\n",
           f"*{rd.stamp_et(ed.get('as_of'))} · about "
           f"{rd.plural(edition_minutes(ed), 'minute')} to read"
           + (f" · target {target} minutes" if target else "") + "*\n"]
    if ed.get("changed_since") and changed_head:
        out.append(f"**{changed_head}**\n")
        out += [f"- {x}" for x in ed["changed_since"]] + [""]
    limit = cad.get("paragraphs")
    for n, s in enumerate(ed["sections"], start=1):
        out.append(f"## {n} · {s['title']}" + (f" — *{s['subtitle']}*"
                                               if s.get("subtitle") else "") + "\n")
        if s.get("empty"):
            out += _md_foot(foot_parts(s, not cad.get("subsection_paragraphs"),
                                       _trimmed_note(cad)))
            continue
        if s.get("claim"):
            out.append(f"**{s['claim']}**\n")
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
