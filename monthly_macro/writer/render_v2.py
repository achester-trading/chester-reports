"""
The Monthly, halved: six sections of change. DATA ONLY. (Phase 4b)

Markdown, because build_html.py turns it into the styled edition and the `.md` is
the archived artefact beside it. No model call and no prose generation here: the
paragraph arrives already written and already audited, and this module places it.

THE SECTION ORDER IS THE PAYLOAD'S ORDER. A renderer choosing its own would make the
document and the payload two accounts of the month, and validate_monthly.py asserts
they agree.

WHY THE PILLARS APPEAR UNDER THE DIALS. Audit #3's ruling is that pillars are inputs
and dials are the regime: eleven peer scores left a reader with eleven readings and
no answer. So each dial prints its state, what it was at the previous Monthly, and
the pillars that feed it with their weights -- and the pillar's own detail is one
delta row in the appendix.
"""

from __future__ import annotations

import re
from typing import Any, Optional


def _v(x: Any, dp: int = 2, dash: str = "—") -> str:
    if x is None or x == "":
        return dash
    if isinstance(x, bool):
        return "yes" if x else "no"
    try:
        return f"{float(x):,.{dp}f}"
    except (TypeError, ValueError):
        return str(x)


def _signed(x: Any, dp: int = 2) -> str:
    try:
        return f"{float(x):+,.{dp}f}"
    except (TypeError, ValueError):
        return "—"


def _tail(reason: Any) -> str:
    """A reason with its first clause dropped when a bold lead already said it.

    The bold lead and the reason's opening sentence are the same sentence twice --
    "**No probability has been emitted.** no probability has been emitted. The
    ledger is seeded..." -- which is how a reader learns to skip the reason.
    """
    text = str(reason or "").strip()
    if not text:
        return "No reason recorded."
    head, sep, rest = text.partition(". ")
    return (rest.strip() if sep and len(head) < 90 else text)


def _scaled_usd(v: Any) -> str:
    """A dollar amount at its own scale: 5872234000000.0 -> `$5.87tn`.

    THE SAME FIGURE, NOT A DIFFERENT ONE. precision.round_scaled has already
    rounded the payload's value at this scale, so the printed form is exact rather
    than a rounding the payload does not know about -- and altdata.numeral_audit
    reads scale words, so a paragraph citing "5.87 trillion" matches the payload's
    5872234000000.0 and is publishable.
    """
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "—"
    for word, mult in (("tn", 1e12), ("bn", 1e9), ("mm", 1e6), ("k", 1e3)):
        if abs(x) >= mult:
            return f"${x / mult:,.2f}{word}"
    return f"${x:,.2f}"


def _macro_level(row: dict) -> str:
    """The level with its unit word, by what the metric IS."""
    v = row.get("level")
    if v is None:
        return "—"
    units = row.get("units")
    if units == "usd":
        return _scaled_usd(v)
    if units == "bps":
        return f"{_v(v, 1)} bp"
    if units == "percent":
        return f"{_v(v, 2)}%"
    return _v(v)


def _delta(x: Any, unit: Any) -> str:
    """A change with its unit -- and NO unit when there is no change.

    `— raw` reads as though the change were raw rather than absent, which is the
    unit word supplying a fact the figure does not have. The registry's unit belongs
    to a number; without one there is nothing for it to qualify.
    """
    if x is None:
        return "—"
    return f"{_signed(x)} {unit}".strip() if unit else _signed(x)


def _absent(title: str, block: dict) -> str:
    return (f"## {title}\n\n**{block.get('state', 'absent')}.** "
            f"{block.get('reason') or 'No reason recorded.'}\n\n---\n")


def _paragraph(narrative: Optional[Any]) -> list[str]:
    """The audited paragraph, or the reason there is none. Never a substitute."""
    if narrative is None:
        return ["\n*No paragraph: the narrative step did not run for this "
                "edition. The takeaways above are the month either way.*\n"]
    if getattr(narrative, "published", False):
        return [f"\n{narrative.text}\n",
                f"\n*Model {narrative.model} · {narrative.figures_checked} figures "
                f"audited against the payload.*\n"]
    note = getattr(narrative, "withheld_note", lambda: "narrative withheld")()
    return [f"\n> **{note}**\n>\n> The paragraph is withheld rather than "
            f"corrected: a figure the payload does not carry is a figure nobody "
            f"can check, and the sections below are the record either way.\n"]


def masthead(p: dict, narrative: Optional[Any] = None) -> str:
    """Title, provenance and absences. The paragraph is section 1's (v2)."""
    out = [f"# Monthly Regime & Allocation — {p.get('report_date')}\n",
           f"*As-of cutoff {p.get('as_of')} · run `{p.get('run_id') or 'n/a'}` · "
           f"pillar mapping {p.get('pillar_mapping_version')}*\n",
           "*The month in markets, the month in one page, the month by theme, the "
           "voices, the months ahead and where our read lands; then the record — "
           "the regime "
           "read from the market-state object, the scenarios, Top & Bottom, the "
           "alternative assets, the register and the appendix. Every item names "
           "the stored record it came from.*\n"]
    if p.get("warnings"):
        out.append("> **Absences**\n>\n"
                   + "\n".join(f"> - {w}" for w in p["warnings"]) + "\n")
    if p.get("month_in_one_page") is None:
        # A pre-v2 payload (an archived 4b edition): the paragraph stays here.
        out += _paragraph(narrative)
    return "\n".join(out) + "\n---\n"


# ---------------------------------------------------------------------------
# MONTHLY v2 -- the storyline sections, prose first, tables for data only
# ---------------------------------------------------------------------------
def _cite(s: dict) -> str:
    """One stored source, as a reader can look it up: kind:id, date."""
    if not s:
        return "—"
    tier = f", tier {s['tier']}" if s.get("tier") is not None else ""
    return f"`{s.get('kind')}:{s.get('id')}`, {s.get('date')}{tier}"


def _cell(text: Any) -> str:
    """Table-safe text: no pipes, no line breaks."""
    return str(text or "—").replace("|", "/").replace("\n", " ")


def _tie(p: dict, section: str) -> str:
    s = (p.get("tie_backs") or {}).get(section)
    return f"*{s}*\n" if s else ""


def _with_tie(text: str, p: dict, section: str) -> str:
    """Insert the section's tie-back sentence under its heading."""
    tie = _tie(p, section)
    if not tie:
        return text
    head, nl, rest = text.partition("\n")
    return f"{head}\n\n{tie}{rest}" if nl else text


def _prose(prose: Optional[dict], key: str) -> list[str]:
    """A section's audited prose, or why there is none. Never a substitute."""
    if prose is None:
        return ["*Prose not generated for this edition (the narrative step did "
                "not run); the tables below are the record.*\n"]
    r = prose.get(key)
    if not r:
        return ["*No prose call was made for this section.*\n"]
    if r.get("published") and r.get("text"):
        return [f"{r['text'].strip()}\n"]
    return [f"> **Section withheld.** {r.get('reason') or r.get('state')}\n>\n"
            f"> Withheld rather than corrected: a figure this section's data does "
            f"not carry is a figure nobody can check. The tables below stand.\n"]


def _move(r: dict) -> str:
    unit = r.get("change_unit")
    if unit == "bps":
        return f"{_signed(r.get('change'), 1)} bp"
    if unit == "percent":
        return f"{_signed(r.get('change'))}%"
    return _signed(r.get("change"), 4)


def _level(r: dict, which: str) -> str:
    v = r.get(f"{which}_level")
    return f"{_v(v)}%" if r.get("change_unit") == "bps" else _v(v)


def _footnote(gaps: Optional[list]) -> str:
    """The section's gaps, OUTSIDE the prose, in plain words."""
    gaps = [g for g in (gaps or []) if g]
    return (f"\n<sub>**Not yet tracked:** {'; '.join(gaps)}.</sub>\n"
            if gaps else "")


def _first_sentence(text: Optional[str]) -> Optional[str]:
    """The claim a section opens with -- prose is written insight first."""
    if not text:
        return None
    para = text.strip().split("\n\n")[0]
    m = re.match(r"(.+?[.!?])(\s|$)", para, flags=re.S)
    return (m.group(1) if m else para).strip()


def _series_table(rows: list[dict]) -> list[str]:
    if not rows:
        return []
    out = ["\n| Series | Latest | Date | Change | Since |\n|---|---|---|---|---|"]
    for r in rows:
        if "latest_pct" in r:
            lvl, mv = f"{_v(r['latest_pct'])}%", (
                f"{_signed(r['change_bps'], 1)} bp" if "change_bps" in r else "—")
        else:
            lvl = _v(r.get("latest_level"))
            mv = (f"{_signed(r['change_pct'])}%" if "change_pct" in r else
                  _signed(r["change"], 2) if "change" in r else "—")
        out.append(f"| {_cell(r['label'])} | {lvl} | {r.get('latest_date')} | "
                   f"{mv} | {r.get('since') or '—'} |")
    return out


def markets_section(p: dict, prose: Optional[dict] = None) -> str:
    b = p.get("month_in_markets") or {}
    out = [f"## 1. The month in markets — {b.get('month') or ''}\n"]
    out += _prose(prose, "month_in_markets")
    rows = b.get("rows") or []
    if rows:
        out.append(f"\n*Close on or before {b.get('start')} against close on or "
                   f"before {b.get('end')}. Yields and spreads move in basis points, "
                   f"prices and indices in percent.*\n")
        out.append("| Market | " + f"{b.get('start')} | {b.get('end')} | Move | "
                   "Level, 5y pctile |\n|---|---|---|---|---|")
        for r in rows:
            out.append(f"| {r['label']} | {_level(r, 'start')} | {_level(r, 'end')} | "
                       f"**{_move(r)}** | {_v(r.get('percentile'), 1)} |")
    else:
        out.append(f"\n**No market moves to show.** {b.get('reason') or ''}")
    out.append(_footnote([m.split(" (")[0] for m in b.get("missing") or []]))
    return "\n".join(out) + "\n\n---\n"


def month_section(p: dict, prose: Optional[dict] = None) -> str:
    b = p.get("month_in_one_page") or {}
    out = ["## 2. The month in one page\n", _tie(p, "month_in_one_page")]
    takes = b.get("takeaways") or []
    r = (prose or {}).get("month_in_one_page") or {}
    if r.get("published") and r.get("text"):
        out.append(f"{r['text'].strip()}\n")
    else:
        if prose is not None:
            out += _prose(prose, "month_in_one_page")
        for t in takes:
            out.append(f"{t['n']}. {t['text']}")
    if takes:
        out.append("\n<sub>Built from: "
                   + "; ".join(_cite(s) for t in takes
                               for s in (t.get("sources") or [])[:1]) + ".</sub>")
    return "\n".join(out) + "\n\n---\n"


def looking_back_section(p: dict, prose: Optional[dict] = None) -> str:
    b = p.get("looking_back") or {}
    if b.get("state") != "ok":
        return _absent("3. Looking back, by theme", b)
    themes = b.get("themes") or []
    out = ["## 3. Looking back, by theme\n", _tie(p, "looking_back")]
    # THE EXECUTIVE SUMMARY: one plain line per theme -- each theme's opening
    # claim, which the prose is written to lead with.
    lines = []
    for t in themes:
        r = (prose or {}).get(f"theme:{t['theme']}") or {}
        first = _first_sentence(r.get("text")) if r.get("published") else None
        if first:
            lines.append(f"**{t['name']}.** {first}")
    if lines:
        out.append("### In one line each\n")
        out.append("  \n".join(lines) + "\n")
    for t in themes:
        out.append(f"### {t['name']}\n")
        out += _prose(prose, f"theme:{t['theme']}")
        out += _series_table(t.get("rows") or [])
        items = t.get("items") or []
        if items:
            out.append("\n| Development | Tag | Source |\n|---|---|---|")
            for it in items:
                corr = (f" (corrects: {it['corrects']['statement']})"
                        if it.get("corrects") else "")
                out.append(f"| {_cell(it['text'] + corr)} | **{it['tag']}** | "
                           f"{'; '.join(_cite(s) for s in it['sources'][:2])} |")
        out.append(_footnote(t.get("not_yet_tracked")))
    wc = b.get("what_changed") or {}
    out.append("### What changed from last month\n")
    out.append(f"*{wc.get('count', 0)} change(s) between this edition and the last, "
               f"each read from a stored record.*\n")
    if wc.get("rows"):
        out.append("| What | From | To | Source |\n|---|---|---|---|")
        for r in wc["rows"]:
            out.append(f"| {_cell(r['what'])} | {_cell(r.get('from'))} | "
                       f"{_cell(r.get('to'))} | {_cite(r.get('source') or {})} |")
    return "\n".join(out) + "\n\n---\n"


def _md_table(t: Optional[dict]) -> list[str]:
    if not t or not t.get("rows"):
        return []
    out = ["| " + " | ".join(t["columns"]) + " |",
           "|" + "---|" * len(t["columns"])]
    out += ["| " + " | ".join(_cell(c) for c in r) + " |" for r in t["rows"]]
    return out + [""]


def voices_section(p: dict) -> str:
    """Section 4 (Phase B): one row per voice with its monthly status, computed
    from stored rows; the four weeks rolled up by story; consensus against
    contrarian. Every row carries its source; nothing is printed without one."""
    b = p.get("voices") or {}
    if b.get("state") not in ("ok", "empty"):
        return _absent("4. Voices", b)
    w = b.get("window") or {}
    out = ["## 4. Voices\n", _tie(p, "voices")]
    if b.get("state") == "empty":
        out.append(f"**{b.get('reason')}.**\n")
    else:
        out.append(f"Status is computed against each voice's stored entry before "
                   f"{w.get('start')}; SILENT means an entry in the month before "
                   f"and none in this one.\n")
        out += _md_table(b.get("table"))
        out.append(f"**Consensus vs contrarian.** {b.get('consensus')}\n")
    if (b.get("rollup") or {}).get("rows"):
        out.append("**The four weeks, by story** (sourced items for and against):\n")
        out += _md_table(b.get("rollup"))
    if b.get("unreachable"):
        out.append(f"*{b['unreachable']}*\n")
    return "\n".join(out) + "\n---\n"


def looking_ahead_section(p: dict, prose: Optional[dict] = None) -> str:
    b = p.get("looking_ahead") or {}
    if b.get("state") not in ("ok", "empty"):
        return _absent("5. Looking ahead, 2–3 months", b)
    out = ["## 5. Looking ahead, 2–3 months\n", _tie(p, "looking_ahead")]
    out += _prose(prose, "looking_ahead")
    for w in b.get("windows") or []:
        out.append(f"\n### {w['name']}\n")
        if w["calendar"]:
            out.append("| Date | Event |\n|---|---|")
            for c in w["calendar"]:
                out.append(f"| {c['date']} | {_cell(c['title'])} |")
        else:
            out.append("*Nothing on our calendar for this period yet.*")
    scen = b.get("scenarios") or []
    out.append("\n### Scenarios, and what would change our mind\n")
    if scen:
        out.append("| Scenario | p | Brier | Resolves | What would change our "
                   "mind |\n|---|---|---|---|---|")
        for s in scen:
            brier = (_v(s.get("brier"), 4) if s.get("brier") is not None
                     else "pending")
            mind = "; ".join(f"{sp['observable']} ({sp['date']})"
                             for sp in s.get("signposts") or [])
            out.append(f"| {_cell(s.get('claim'))} | {_v(s.get('probability'), 3)} | "
                       f"{brier} | {s.get('resolve_by') or '—'} | {_cell(mind)} |")
    else:
        out.append("*No live scenario weight this month.*")
    out.append(_footnote(b.get("not_yet_tracked")))
    return "\n".join(out) + "\n\n---\n"


def our_read_section(p: dict, prose: Optional[dict] = None) -> str:
    b = p.get("our_read") or {}
    if b.get("state") != "ok":
        return _absent("6. Where our read lands", b)
    out = ["## 6. Where our read lands\n", _tie(p, "our_read")]
    out += _prose(prose, "our_read")
    out.append(f"\n<sub>The bound, restated from the weights and the positions: "
               f"{b.get('paragraph')}</sub>\n")
    return "\n".join(out) + "\n---\n"


def regime_section(p: dict) -> str:
    b = p.get("regime") or {}
    if b.get("state") != "ok":
        return _absent("I. Regime", b)
    out = [f"## I. Regime\n",
           f"*Object session {b.get('session')} · config "
           f"{b.get('config_version')} · method {b.get('method_version')} · "
           f"against {b.get('previous_monthly') or 'no previous Monthly'}*\n"]
    for d in b.get("dials") or []:
        state = d.get("state") or "ABSENT"
        moved = (f" — **changed** from {d.get('previous_state') or 'absent'}"
                 if d.get("changed") else " — held")
        out.append(f"### Dial: {d['dial']} — **{state}**{moved}\n")
        if d.get("absent_reason"):
            out.append(f"*Absent: {d['absent_reason']}*\n")
        if d.get("provisional"):
            out.append("*PROVISIONAL — an expiry session; the profile measured "
                       "describes a book about to stop existing.*\n")
        ts = d.get("term_structure")
        if ts:
            out.append(
                f"- Term structure, published by **{ts.get('published_by')}**: "
                f"{ts.get('published_state') or '—'}\n"
                f"- champion `{(ts.get('champion') or {}).get('metric')}` "
                f"{(ts.get('champion') or {}).get('state') or '—'} "
                f"(ratio {_v((ts.get('champion') or {}).get('ratio'), 4)}, "
                f"pctile {_v((ts.get('champion') or {}).get('percentile'), 1)})\n"
                f"- challenger `{(ts.get('challenger') or {}).get('metric')}` "
                f"{(ts.get('challenger') or {}).get('state') or '—'} "
                f"(ratio {_v((ts.get('challenger') or {}).get('ratio'), 4)}, "
                f"pctile {_v((ts.get('challenger') or {}).get('percentile'), 1)})\n"
                f"- legs agree: {_v(ts.get('legs_agree'))} · basis "
                f"{_v(ts.get('basis'))} vol points · dual run to "
                f"{ts.get('dual_run_until') or '—'}\n")
        ri = d.get("realized_implied")
        if ri:
            out.append(f"- realized/implied: **{ri.get('state') or '—'}** "
                       f"(ratio {_v(ri.get('ratio'), 4)} = "
                       f"{_v(ri.get('realized'))} / {_v(ri.get('implied'))})\n")
        pl = d.get("pillars") or []
        if pl:
            out.append("\n| Pillar | Weight | Reads dimension |\n|---|---|---|")
            for x in pl:
                out.append(f"| {x['number']} {x.get('name')} | "
                           f"{_v(x.get('weight'))} | "
                           f"{x.get('reads_dimension') or '*(none — '
                              + str(x.get('absent_reason') or '')[:60] + ')*'} |")
            out.append("")
        else:
            out.append("\n*No pillar feeds this dial. Gamma is dealer "
                       "positioning read from the option chain; no macro series "
                       "bears on it, and a pillar mapped here would be "
                       "decoration.*\n")

    out.append("\n### Dimensions\n")
    out.append("| Dimension | State | Previous Monthly | Pctile | Dir | Conf |")
    out.append("|---|---|---|---|---|---|")
    # AN ABSENT DIMENSION SAYS `absent` IN THE CELL AND GIVES ITS REASON BELOW.
    # A reason cut to fit a table column ends mid-word -- "was last observed 2" --
    # and the truncated tail reads as a figure the report is asserting. A cell is
    # the wrong shape for a sentence; the sentence goes under the table whole.
    absent_why: list[str] = []
    for d in b.get("dimensions") or []:
        st = d.get("state") or "*absent*"
        if not d.get("state"):
            absent_why.append(f"**{d['dimension']}** — "
                              f"{d.get('absent_reason') or 'no reason recorded'}")
        mark = " **→**" if d.get("changed") else ""
        out.append(f"| {d['dimension']}{mark} | {st} | "
                   f"{d.get('previous_state') or '—'} | "
                   f"{_v(d.get('percentile'), 1)} | {d.get('direction') or '—'} | "
                   f"{d.get('confidence') or '—'} |")
    if absent_why:
        out.append(f"\n*{len(absent_why)} of {len(b.get('dimensions') or [])} "
                   f"dimensions are absent, each with its reason:*\n")
        for w in absent_why:
            out.append(f"- {w}")
        out.append("")
    changed = b.get("dimensions_changed") or []
    out.append(f"\n*Changed since the previous Monthly: "
               f"{', '.join(changed) if changed else 'none'}.*\n")

    op, cl = b.get("exceptions_opened") or [], b.get("exceptions_closed") or []
    out.append(f"### Exceptions\n\nOpen now: {len(b.get('exceptions_open_now') or [])}"
               f" · opened since the previous Monthly: {len(op)}"
               f" · closed: {len(cl)}\n")
    if op:
        out.append("- opened: " + ", ".join(f"`{x}`" for x in op))
    if cl:
        out.append("- closed: " + ", ".join(f"`{x}`" for x in cl))
    contras = [r for r in (b.get("contradictions") or [])
               if r.get("open_state") != "absent"]
    if contras:
        out.append("\n### Contradictions\n")
        out.append("| Pair | State | z | Threshold | Sessions | Since |")
        out.append("|---|---|---|---|---|---|")
        for r in contras:
            out.append(f"| {r.get('id')} | {r.get('open_state') or '—'} | "
                       f"{_v(r.get('magnitude'))} | {_v(r.get('threshold_z'), 1)} | "
                       f"{_v(r.get('persistence_days'), 0)} | "
                       f"{r.get('since') or '—'} |")
    return "\n".join(out) + "\n\n---\n"


def scenarios_section(p: dict) -> str:
    b = p.get("scenarios") or {}
    out = ["## II. Scenarios — every weight with its Brier\n"]
    out.append(f"*Grouped by {b.get('grouping')}. "
               f"{b.get('grouping_note') or ''}*\n")
    if b.get("state") == "empty":
        out.append(f"**No probability has been emitted.** "
                   f"{_tail(b.get('reason'))}\n")
        return "\n".join(out) + "\n---\n"
    if b.get("state") != "ok":
        return _absent("II. Scenarios", b)
    out.append(f"{b.get('emitted')} emitted · {b.get('resolved')} resolved · "
               f"method {b.get('method_version')}\n")
    out.append("| Claim | p | Source | Outcome | Brier | Resolve by |")
    out.append("|---|---|---|---|---|---|")
    for w in b.get("weights") or []:
        out.append(f"| {str(w.get('claim'))[:60]} | {_v(w.get('probability'), 3)} | "
                   f"{w.get('source') or '—'} | "
                   f"{'—' if w.get('outcome') is None else w['outcome']} | "
                   f"{_v(w.get('brier'), 4)} | {w.get('resolve_by') or '—'} |")
    out.append("\n*A weight printed without its score is a forecast nobody has "
               "marked. A running Brier above 0.25 is worse than a coin.*\n")
    return "\n".join(out) + "\n---\n"


def top_bottom_section(p: dict) -> str:
    b = p.get("top_bottom") or {}
    out = ["## III. Top & Bottom — a section, not a report\n"]
    if b.get("state") == "ok":
        out.append(f"Verdict **{b.get('verdict') or '—'}** · composite "
                   f"{_v(b.get('composite'))} (as of {b.get('as_of')})\n")
    else:
        out.append(f"**Verdict and composite absent.** {b.get('reason')}\n")
    br = b.get("bear_rally_base_rate") or {}
    out.append("\n### The bear-rally base rate, on the top-side language\n")
    if br.get("absent_reason"):
        out.append(f"*{br['absent_reason']}*\n")
    else:
        out.append(f"From `{br.get('source_metric')}` "
                   f"({br.get('method_version')}), over {_v(br.get('n_bears'), 0)} "
                   f"bear markets: the largest counter-trend rally inside a decline "
                   f"runs **p25 {_signed(br.get('p25'))}%, median "
                   f"{_signed(br.get('median'))}%, p75 {_signed(br.get('p75'))}%**, "
                   f"extreme {_signed(br.get('max'))}%.\n")
    out.append(f"\n*{br.get('why_it_is_here')}*\n")
    cited = b.get("claims_cited") or []
    if cited:
        out.append("\n**Claims cited by id** — never retyped:\n")
        for c in cited:
            if c.get("absent_reason"):
                out.append(f"- `{c['id']}` — *{c['absent_reason']}*")
                continue
            out.append(f"- `{c['id']}`: {c.get('value')} "
                       f"*({c.get('source')}, as of {c.get('as_of')})*")
            for w in c.get("warnings") or []:
                out.append(f"  - ⚠ {w}")
    return "\n".join(out) + "\n\n---\n"


def alt_section(p: dict) -> str:
    b = p.get("alternative_assets") or {}
    out = ["## IV. Alternative Assets — a section, not a report\n",
           f"*{b.get('note')}*\n"]
    for fam, v in sorted((b.get("families") or {}).items()):
        out.append(f"### {fam} — {v.get('state')}\n")
        if v.get("state") == "not_yet_sourced":
            out.append(f"*{v.get('why')}*\n\nNeeds: "
                       f"{', '.join(v.get('needs') or [])}\n")
            continue
        if v.get("reason"):
            out.append(f"*{v['reason']}*\n")
        out.append(f"*{v.get('note') or ''}*\n")
        out.append("| Metric | Level | 20d change | Pctile | Conf |")
        out.append("|---|---|---|---|---|")
        for m in v.get("metrics") or []:
            if m.get("level") is None:
                out.append(f"| `{m['metric']}` | *absent* | — | — | — |")
                continue
            out.append(f"| `{m['metric']}` | {_v(m.get('level'))} | "
                       f"{_delta(m.get('delta_20d'), m.get('delta_unit'))} | "
                       f"{_v(m.get('percentile'), 1)} | {m.get('confidence')} |")
        out.append("")
    return "\n".join(out) + "\n---\n"


def register_section(p: dict) -> str:
    b = p.get("register_month") or {}
    out = ["## V. The register's month\n",
           f"*Window {(b.get('window') or ['—', '—'])[0]} to "
           f"{(b.get('window') or ['—', '—'])[1]}*\n"]
    if b.get("state") == "empty":
        out.append(f"**No decision has reached its horizon.** {b.get('reason')}\n")
    elif b.get("state") != "ok":
        out.append(f"**Grades unavailable.** {b.get('reason')}\n")
    else:
        ov = ((b.get("cuts") or {}).get("overall") or {})
        out.append(f"{b.get('graded_total')} graded to date · "
                   f"{b.get('graded_this_month')} this month\n")
        out.append(f"**Expectancy, interval first:** n={ov.get('n')}, "
                   f"{_v(ov.get('lo'), 3)} to {_v(ov.get('hi'), 3)}R, mean "
                   f"{_signed(ov.get('mean'), 3)}R. {ov.get('note') or ''}\n")
    out.append(f"\nOpen now: {b.get('open_now')} · opened this month: "
               f"{len(b.get('decisions_opened') or [])} · closed: "
               f"{len(b.get('decisions_closed') or [])}\n")
    for d in b.get("decisions_opened") or []:
        out.append(f"- `{d.get('instrument')}` {d.get('direction')} "
                   f"({d.get('status')}, {d.get('thesis_state') or 'no state'}, "
                   f"{d.get('expression_family') or 'no expression'}) "
                   f"— {d.get('created_at')}")
    bz = b.get("books_vs_benchmark") or {}
    if bz:
        vs = bz.get("line") or (f"FAULT (code, not data) -- {bz['fault']}"
                                if bz.get("fault") else
                                f"Book Z absent: {bz.get('absent_reason')}")
        out.append("\n### Books vs Book Z\n")
        for bk, eq in sorted((bz.get("books") or {}).items()):
            out.append(f"- Book {bk}: paper equity {eq} · {vs}")
    rb = b.get("rule_breaks") or {}
    out.append(f"\n### Rule breaks\n\nRestricted-instrument attempts this month: "
               f"**{rb.get('restricted_instrument_attempts_this_month')}** · "
               f"running total {rb.get('restricted_instrument_attempts_total')}\n")
    out.append(f"*Not yet sourced: "
               f"{', '.join(rb.get('not_yet_sourced') or [])}. "
               f"{rb.get('not_yet_sourced_why')}*\n")
    return "\n".join(out) + "\n---\n"


def appendix_section(p: dict, prose: Optional[dict] = None) -> str:
    b = p.get("appendix") or {}
    if b.get("state") != "ok":
        return _absent("Appendix — pillar deltas", b)
    out = ["## Appendix — the pillar pages, as one delta table\n",
           f"*{b.get('note')}*\n",
           f"*{b.get('series_total')} series across "
           f"{len(b.get('pillars') or {})} of "
           f"{b.get('pillars_declared')} pillars.*\n"]
    # THE PILLARS WITH NO ROWS ARE NAMED HERE. Printing eight tables and stopping
    # leaves three pillars looking forgotten rather than empty, and the mapping
    # already records why each one has nothing to show.
    for g in b.get("pillars_without_series") or []:
        out.append(f"*Pillar {g['pillar']} — {g.get('name')} has no series in the "
                   f"store: {g.get('reason')}*\n")
    macro = b.get("derived_macro") or []
    if macro:
        out.append("### Derived macro series\n")
        out.append(f"*{b.get('derived_macro_note')}*\n")
        out.append("| Series | Level | Change | Pctile | Read by | Conf | Stale |")
        out.append("|---|---|---|---|---|---|---|")
        for m in macro:
            read = ", ".join(m.get("read_by") or []) or "—"
            out.append(
                f"| `{m['metric']}` | {_macro_level(m)} | "
                f"{_delta(m.get('delta_20d'), m.get('delta_unit'))} | "
                f"{_v(m.get('percentile'), 1)}"
                f"{' **!**' if m.get('extreme') else ''} | {read} | "
                f"{m.get('confidence') or '—'} | "
                f"{m.get('staleness_sessions') if m.get('staleness_sessions') is not None else '—'} |")
        unread = [m["metric"] for m in macro if not m.get("read_by")]
        src = b.get("derived_macro_read_from") or {}
        if src.get("predates_config"):
            # THE COLUMN IS EMPTY FOR A REASON THAT IS NOT THE WIRING.
            out.append(
                f"\n*`Read by` is read off the stored object, and the object for "
                f"{src.get('session')} was computed under {src.get('config_version')} "
                f"while the declared rules are {src.get('declared_config')}. It "
                f"therefore does not carry the new members yet — the close pass is "
                f"the object's only writer, and the next one will. The column is "
                f"empty here because the object predates the wiring, not because "
                f"the wiring is absent.*\n")
        elif unread:
            out.append(
                f"\n*{len(unread)} of {len(macro)} feed no dimension directly: "
                f"{', '.join('`' + u + '`' for u in unread)}. Each is either a leg "
                f"of one that does — core PCE year-over-year is read by r-vs-g — or "
                f"context the object has no member for. A derived series that feeds "
                f"nothing is a candidate for deletion, not a finding.*\n")
        out.append("")

    g = b.get("pm_calibration_gate") or {}
    if g.get("state") == "ok":
        out.append("### Prediction markets — the calibration-archive gate\n")
        out.append(f"*{g.get('right')}.*\n")
        out.append("| Condition | Have | Need | Met |")
        out.append("|---|---|---|---|")
        for c in g.get("conditions") or []:
            out.append(f"| {c['condition']} | {c['have']} | {c['need']} | "
                       f"{'yes' if c.get('met') else 'no'} |")
        out.append("")
    elif g:
        out.append(f"*Prediction-market calibration gate: not read "
                   f"({g.get('reason')}).*\n")
    for num, v in sorted((b.get("pillars") or {}).items()):
        out.append(f"### Pillar {num} — {v.get('name')} "
                   f"(dial: {v.get('dial') or 'none'}, weight "
                   f"{_v(v.get('weight'))}, reads "
                   f"{v.get('reads_dimension') or 'no dimension'})\n")
        # v2: the pillar's one plain-language paragraph -- what it measures, how
        # it moved, what to watch -- above its table.
        if prose is not None and prose.get(f"pillar:{num}"):
            out += _prose(prose, f"pillar:{num}")
        out.append("| Series | Level | 20d change | Pctile | Conf | Stale |")
        out.append("|---|---|---|---|---|---|")
        for r in v.get("series") or []:
            out.append(
                f"| `{r['metric']}` | {_v(r.get('level'))} | "
                f"{_delta(r.get('delta_20d'), r.get('delta_unit'))} | "
                f"{_v(r.get('percentile'), 1)}"
                f"{' **!**' if r.get('extreme') else ''} | "
                f"{r.get('confidence') or '—'} | "
                f"{_v(r.get('staleness_sessions'), 0)} |")
        out.append("")
    return "\n".join(out) + "\n---\n"


def render(payload: dict, narrative: Optional[Any] = None,
           prose: Optional[dict] = None) -> str:
    """The whole document, in the payload's section order.

    v2: sections 1-6 first -- the month in markets, the month in one page, the
    themes, voices, the look-ahead and where our read lands, each written by its
    own audited call (`prose`) -- then "7. The record": the 4b sections, each
    opened by its tie-back. A pre-v2 payload renders as it always did, with the
    single paragraph (`narrative`) in the masthead.
    """
    p = payload
    head = [masthead(p, narrative)]
    if p.get("month_in_markets") is not None:
        head += [markets_section(p, prose), month_section(p, prose),
                 looking_back_section(p, prose), voices_section(p),
                 looking_ahead_section(p, prose), our_read_section(p, prose),
                 "## 7. The record\n\n*The regime read from the object, the "
                 "scenarios, Top & Bottom, the alternative assets, the register "
                 "and the appendix: the 4b sections, unchanged, each opened by "
                 "its tie-back.*\n"]
    return "\n".join(head + [
        _with_tie(regime_section(p), p, "regime"),
        _with_tie(scenarios_section(p), p, "scenarios"),
        _with_tie(top_bottom_section(p), p, "top_bottom"),
        _with_tie(alt_section(p), p, "alternative_assets"),
        _with_tie(register_section(p), p, "register_month"),
        _with_tie(appendix_section(p, prose), p, "appendix"),
        "\n*End of Monthly Regime & Allocation. Pillars are inputs; the dials are "
        "the regime. Every figure above was read from the object, the register, the "
        "grader, the probability ledger or the store, and anything unreadable says "
        "so.*\n",
    ])


def text_fallback(payload: dict) -> str:
    rg = payload.get("regime") or {}
    dials = ", ".join(f"{d['dial']} {d.get('state') or 'absent'}"
                      for d in (rg.get("dials") or []))
    return "\n".join([
        f"Monthly Regime & Allocation -- {payload.get('report_date')}",
        f"  dials    : {dials}",
        f"  changed  : {', '.join(rg.get('dimensions_changed') or []) or 'none'}",
        f"  sections : " + ", ".join(
            f"{s}={(payload.get(s) or {}).get('state')}"
            for s in payload.get("sections") or []),
        "",
        "The HTML edition carries the tables.",
    ])
