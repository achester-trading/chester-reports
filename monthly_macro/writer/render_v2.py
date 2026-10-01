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
           "*The month in one page, then the month by theme, the voices, the "
           "months ahead and where our read lands; then the record — the regime "
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
# MONTHLY v2, PHASE A -- sections 1 to 5 and the tie-back sentences
# ---------------------------------------------------------------------------
def _cite(s: dict) -> str:
    """One stored source, as a reader can look it up: kind:id, date."""
    if not s:
        return "—"
    t = f" — {s['title']}" if s.get("title") and s.get("kind") == "event" else ""
    tier = f", tier {s['tier']}" if s.get("tier") is not None else ""
    return f"`{s.get('kind')}:{s.get('id')}`, {s.get('date')}{tier}{t[:90]}"


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


def month_section(p: dict, narrative: Optional[Any] = None) -> str:
    b = p.get("month_in_one_page") or {}
    out = ["## 1. The month in one page\n"]
    takes = b.get("takeaways") or []
    if b.get("state") == "fault":
        out.append(f"**FAULT.** {b.get('reason')}\n")
    elif not takes:
        out.append(f"**No takeaway.** {b.get('reason') or 'No reason recorded.'}\n")
    for t in takes:
        out.append(f"{t['n']}. {t['text']}  \n"
                   f"   <sub>{'; '.join(_cite(s) for s in t.get('sources') or [])}"
                   f"</sub>")
    if takes and len(takes) < 5:
        out.append(f"\n*{len(takes)} takeaway(s), not five: a takeaway is printed "
                   f"only when a stored record supports it.*")
    out += _paragraph(narrative)
    return "\n".join(out) + "\n---\n"


def looking_back_section(p: dict) -> str:
    b = p.get("looking_back") or {}
    if b.get("state") != "ok":
        return _absent("2. Looking back, by theme", b)
    w = b.get("window") or ["—", "—"]
    out = ["## 2. Looking back, by theme\n", _tie(p, "looking_back"),
           f"*Window {w[0]} to {str(w[1])[:10]} · themes "
           f"{b.get('themes_version')} · tags: CONSENSUS needs two tier-1–2 "
           f"sources, DISSENT names its source, CORRECTION cites what it "
           f"corrects, NEW is dated inside the window.*\n"]
    for t in b.get("themes") or []:
        out.append(f"### {t['name']}\n")
        reads = ", ".join(t.get("dimensions") or []) or "no dimension"
        stories = ", ".join(f"`{s}`" for s in t.get("stories") or []) or "no story"
        out.append(f"*Reads {reads}; carries {stories}.*"
                   + (f" *{t['no_dimension_why']}*" if t.get("no_dimension_why")
                      else "") + "\n")
        for it in t.get("items") or []:
            out.append(f"- **{it['tag']}** {it['text']}  \n"
                       f"  <sub>{'; '.join(_cite(s) for s in it['sources'][:3])}"
                       f"</sub>")
            c = it.get("corrects")
            if c:
                out.append(f"  - corrects: {c['statement']} (`{c['id']}`, "
                           f"{c['date']})")
        if not t.get("items"):
            out.append("- *Nothing new in the stored record this window.*")
        if t.get("held"):
            out.append(f"\n*Held: {'; '.join(t['held'])}.*")
        if t.get("refused"):
            out.append(f"\n*{t['refused']} item(s) refused: no stored source, or "
                       f"a tag its sources do not support.*")
        out.append("")
    wc = b.get("what_changed") or {}
    out.append("### What changed from last month\n")
    out.append(f"*Computed from the store, never written: {wc.get('count', 0)} "
               f"difference(s) between stored records inside the window"
               + (f". {wc['note']}" if wc.get("note") else "") + ".*\n")
    if wc.get("rows"):
        out.append("| What | From | To | Source |\n|---|---|---|---|")
        for r in wc["rows"]:
            out.append(f"| {r['what']} | {r.get('from') or '—'} | "
                       f"{r.get('to') or '—'} | {_cite(r.get('source') or {})} |")
    return "\n".join(out) + "\n\n---\n"


def voices_section(p: dict) -> str:
    b = p.get("voices") or {}
    out = ["## 3. Voices\n", _tie(p, "voices"),
           f"**{b.get('reason') or 'Voices register not yet built'}.**\n",
           "*Sell-side desks, buy-side managers and independent strategists, one "
           "row each with a computed status (REITERATED / NEW / INFLECTED / "
           "SILENT), arrive with Phase B. Until then no view is attributed to "
           "anyone: a voice with no stored source is not printed.*\n"]
    if b.get("needs"):
        out.append("Needs: " + "; ".join(b["needs"]) + ".\n")
    return "\n".join(out) + "\n---\n"


def looking_ahead_section(p: dict) -> str:
    b = p.get("looking_ahead") or {}
    if b.get("state") not in ("ok", "empty"):
        return _absent("4. Looking ahead, 2–3 months", b)
    h = b.get("horizon") or ["—", "—"]
    out = ["## 4. Looking ahead, 2–3 months\n", _tie(p, "looking_ahead"),
           f"*{h[0]} to {h[1]}, from the events table.*\n"]
    cal = b.get("calendar") or []
    if cal:
        out.append("| Date | Event | Source |\n|---|---|---|")
        for c in cal:
            out.append(f"| {c['date']} | {c['title']} | "
                       f"`{c['source']['kind']}:{c['source']['id']}` |")
    else:
        out.append("*Nothing scheduled in the events table inside the horizon.*")
    reach = b.get("calendar_reach") or {}
    if reach:
        out.append("\n*Each calendar source is stored as far as: "
                   + ", ".join(f"{k} {v}" for k, v in sorted(reach.items()))
                   + ". A quiet stretch past those dates is the table's horizon, "
                     "not the market's.*")
    out.append("\n### Scenarios, and what would change our mind\n")
    scen = b.get("scenarios") or []
    if not scen:
        out.append("*No live weight in the probability ledger.*")
    for s in scen:
        out.append(f"- **p {_v(s.get('probability'), 3)}** · Brier "
                   f"{_v(s.get('brier'), 4) if s.get('brier') is not None else 'pending'}"
                   f" · resolves {s.get('resolve_by') or '—'} — {s.get('claim')}  \n"
                   f"  <sub>{_cite(s.get('cite') or {})}</sub>")
        for sp in s.get("signposts") or []:
            out.append(f"  - *would change our mind:* {sp['observable']} "
                       f"({sp['date']})")
    if b.get("scenarios_refused"):
        out.append(f"\n*{len(b['scenarios_refused'])} weight(s) refused: no "
                   f"stored, dated signpost.*")
    return "\n".join(out) + "\n\n---\n"


def our_read_section(p: dict) -> str:
    b = p.get("our_read") or {}
    if b.get("state") != "ok":
        return _absent("5. Where our read lands", b)
    return "\n".join(["## 5. Where our read lands\n", _tie(p, "our_read"),
                      f"{b.get('paragraph')}\n",
                      "*Bounded: this restates the scenario weights and the "
                      "books, and states nothing they do not already hold.*\n"]
                     ) + "\n---\n"


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


def appendix_section(p: dict) -> str:
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

    for num, v in sorted((b.get("pillars") or {}).items()):
        out.append(f"### Pillar {num} — {v.get('name')} "
                   f"(dial: {v.get('dial') or 'none'}, weight "
                   f"{_v(v.get('weight'))}, reads "
                   f"{v.get('reads_dimension') or 'no dimension'})\n")
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


def render(payload: dict, narrative: Optional[Any] = None) -> str:
    """The whole document, in the payload's section order.

    v2: sections 1-5 first, then "6. The record" -- the 4b sections, each opened
    by its tie-back sentence. A pre-v2 payload renders as it always did.
    """
    p = payload
    head = [masthead(p, narrative)]
    if p.get("month_in_one_page") is not None:
        head += [month_section(p, narrative), looking_back_section(p),
                 voices_section(p), looking_ahead_section(p),
                 our_read_section(p),
                 "## 6. The record\n\n*The regime read from the object, the "
                 "scenarios, Top & Bottom, the alternative assets, the register "
                 "and the appendix: the 4b sections, unchanged, each opened by "
                 "its tie-back.*\n"]
    return "\n".join(head + [
        _with_tie(regime_section(p), p, "regime"),
        _with_tie(scenarios_section(p), p, "scenarios"),
        _with_tie(top_bottom_section(p), p, "top_bottom"),
        _with_tie(alt_section(p), p, "alternative_assets"),
        _with_tie(register_section(p), p, "register_month"),
        _with_tie(appendix_section(p), p, "appendix"),
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
