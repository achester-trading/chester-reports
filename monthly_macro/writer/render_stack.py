"""
The stacked Monthly's HTML and Markdown. (T3, first half)

    html = render_stack.html(edition, mode="email")
    md = render_stack.markdown(edition)

THE WEEKLY'S PAGE, AT THE MONTHLY'S LENGTH. The styles, the header with its
reading time, the tables, the glossary and the footer are the stacked reports'
own (daily_cascade.stack_render) -- the Monthly imports them and changes none.
What differs is the Monthly's long form: a section or a sub-section may carry
SEVERAL paragraphs (the Monthly v2 prose -- the themes, the look-ahead, our
read), and a sub-section carries its own footnote, so each theme keeps its "Not
yet tracked" line. Inside every section the order is fixed: the header, the
claim line, the tables, each sub-section (its tables, its lines, its paragraphs,
its footnote), the paragraphs, the footnote.

After the eleventh section (Slow layers), the DETAIL TABLES: the regime, the
scenario record, the register's month and the appendix.

The Markdown is the same edition in the same order: the attachment and the text
fallback. Neither renderer computes anything.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from daily_cascade import readability as rd
from daily_cascade import stack_render as sr

esc = sr.esc


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------
def _foot_parts(b: dict, own_nt: bool = True) -> list[str]:
    parts = []
    if b.get("empty"):
        parts.append(b.get("empty_note"))
    parts.append(b.get("legend"))
    nt = list(dict.fromkeys(b.get("not_tracked") or [])) if own_nt else []
    if nt:
        parts.append("Not yet tracked: " + "; ".join(nt) + ".")
    if b.get("withheld"):
        why = re.sub(r"^(?:narrative\s+)?withheld:\s*", "", str(b["withheld"]),
                     flags=re.I)
        parts.append("Commentary withheld by the audit: " + why)
    parts += list(b.get("notes") or [])
    if b.get("trimmed"):
        parts.append("(trimmed)")
    return [x for x in parts if x]


def _tables_html(b: dict) -> str:
    out = sr._table(b.get("table"))
    for t in b.get("tables") or []:
        out += sr._table(t)
    return out


def _sub_html(ss: dict, period: str) -> str:
    body = (_tables_html(ss)
            + sr.lines_table(ss.get("lines") or [], f"This {period}")
            + "".join(f'<p style="{sr.PARA}">{esc(p)}</p>'
                      for p in ss.get("paragraphs") or [])
            + sr._foot(_foot_parts(ss)))
    return (f'<h3 style="{sr.H3}">{esc(ss.get("title"))}</h3>' + body) if body else ""


def section_html(s: dict, n: int) -> str:
    out = [sr.header_html(s, n)]
    if s.get("empty"):
        return "".join(out) + sr._foot(_foot_parts(s))
    if s.get("claim"):
        out.append(f'<p style="{sr.CLAIM}">{esc(s["claim"])}</p>')
    out.append(_tables_html(s))
    for ss in s.get("subsections") or []:
        out.append(_sub_html(ss, s.get("period") or "month"))
    items = rd.printable_items(s)
    if items:
        out.append(sr.lines_table([i["text"] for i in items],
                                  f"Also this {s.get('period') or 'month'}",
                                  [bool(i.get("changed")) for i in items]))
    for p in s.get("paragraphs") or []:
        out.append(f'<p style="{sr.PARA}">{esc(p)}</p>')
    out.append(sr._foot(_foot_parts(s)))
    return "".join(out)


def detail_html(d: dict) -> str:
    out = [f'<h3 style="{sr.H3}">{esc(d["title"])}</h3>', _tables_html(d),
           sr.lines_table(d.get("lines") or [], "This month")]
    for ss in d.get("subsections") or []:
        out.append(_sub_html(ss, "month"))
    out.append(sr._foot(_foot_parts(d)))
    return "".join(out)


def title(ed: dict) -> str:
    return f"Monthly — {ed.get('month') or ed.get('report_date')}"


def html(ed: dict, mode: str = "email") -> str:
    """The page: the header (as-of in ET, reading time against its target, what
    changed since the last Monthly), the eleven sections, the detail tables, the
    glossary, the footer."""
    secs = "".join(section_html(s, n) for n, s in enumerate(ed["sections"], start=1))
    target = ed.get("reading_target_minutes")
    head = sr.page_header(title(ed), rd.stamp_et(ed.get("as_of")),
                          int(ed.get("reading_minutes") or 1),
                          ed.get("changed_since") or [], "Changed since last Monthly",
                          extra_html=(f" &middot; target {esc(target)} minutes"
                                      if target else ""))
    detail = "".join(detail_html(d) for d in ed.get("detail") or [])
    if detail:
        detail = f'<h2 style="{sr.SECTION}">Detail tables</h2>' + detail
    try:
        from altdata import labels                              # noqa: PLC0415
        gl = labels.glossary()
    except Exception:                                           # noqa: BLE001
        gl = []
    return (f'<div style="{sr.WRAP}">{head}{secs}{detail}'
            f'{sr.glossary_html(gl, ed)}'
            + sr.page_footer(ed, ed.get("run_id"), ed.get("archive_path"),
                             sr._marks(ed, "Monthly"))
            + "</div>")


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------
def _c(v: Any) -> str:
    return str("—" if v in (None, "") else v).replace("|", "/").replace("\n", " ")


def _md_table(t: Optional[dict]) -> list[str]:
    if not t or not t.get("rows"):
        return []
    return (["| " + " | ".join(_c(c) for c in t["columns"]) + " |",
             "|" + "---|" * len(t["columns"])]
            + ["| " + " | ".join(_c(c) for c in r) + " |" for r in t["rows"]] + [""])


def _md_block(b: dict) -> list[str]:
    out = _md_table(b.get("table"))
    for t in b.get("tables") or []:
        out += _md_table(t)
    out += [f"- {x}" for x in b.get("lines") or []]
    if b.get("lines"):
        out.append("")
    return out


def _md_foot(b: dict) -> list[str]:
    return [f"<sub>{x}</sub>\n" for x in _foot_parts(b)]


def markdown(ed: dict) -> str:
    target = ed.get("reading_target_minutes")
    out = [f"# {title(ed)}\n",
           f"*{rd.stamp_et(ed.get('as_of'))} · about "
           f"{rd.plural(int(ed.get('reading_minutes') or 1), 'minute')} to read"
           + (f" · target {target} minutes" if target else "") + "*\n"]
    if ed.get("changed_since"):
        out.append("**Changed since last Monthly**\n")
        out += [f"- {x}" for x in ed["changed_since"]] + [""]
    for n, s in enumerate(ed["sections"], start=1):
        out.append(f"## {n} · {s['title']}" + (f" — *{s['subtitle']}*"
                                               if s.get("subtitle") else "") + "\n")
        if s.get("empty"):
            out += _md_foot(s)
            continue
        if s.get("claim"):
            out.append(f"**{s['claim']}**\n")
        out += _md_block(s)
        for ss in s.get("subsections") or []:
            body = _md_block(ss) + [f"{p}\n" for p in ss.get("paragraphs") or []] \
                + _md_foot(ss)
            if body:
                out += [f"### {ss.get('title')}\n"] + body
        items = rd.printable_items(s)
        out += [f"- {'◆ ' if i.get('changed') else ''}{i['text']}" for i in items]
        if items:
            out.append("")
        out += [f"{p}\n" for p in s.get("paragraphs") or []]
        out += _md_foot(s)
    if ed.get("detail"):
        out.append("## Detail tables\n")
        for d in ed["detail"]:
            out.append(f"### {d['title']}\n")
            out += _md_block(d)
            for ss in d.get("subsections") or []:
                body = _md_block(ss) + [f"{p}\n" for p in ss.get("paragraphs") or []] \
                    + _md_foot(ss)
                if body:
                    out += [f"#### {ss.get('title')}\n"] + body
            out += _md_foot(d)
    out.append(f"\n*Stack {ed.get('config_version')} · "
               f"{rd.plural(int(ed.get('words') or 0), 'word')} · "
               f"{rd.plural(int(ed.get('chart_count') or 0), 'chart')} · run "
               f"{ed.get('run_id') or 'n/a'}. {sr._marks(ed, 'Monthly')}*\n")
    return "\n".join(out)
