"""
The EVENTS block: what landed since the previous close, and what is ahead.

    from daily_cascade.events_block import build, render

ONE IMPLEMENTATION, TWO READERS. The 07:00 anchor asks "since the previous close"
and the Weekly asks "since Friday's close", which is the same question with a
different `since`. A second implementation would be a second answer about what
happened, and the Weekly's block has been printing `not_yet_sourced` precisely
because there was nothing to read; now there is.

-----------------------------------------------------------------------------
DATA ONLY
-----------------------------------------------------------------------------

No prose is generated here and none is asked for. The block prints what the table
holds: releases with their actual against the declared naive expectation, earnings
with the real consensus surprise, filings for universe names, headline counts per
DECLARED story query with the top items linked, and the calendar ahead. A reader
who wants to know what it means reads the paragraph, which is audited; a reader who
wants to know what happened reads this, which is not interpreted at all.

-----------------------------------------------------------------------------
IT READS. IT DOES NOT FETCH.
-----------------------------------------------------------------------------

Every figure comes from the events table and the observation store, both written by
the ingest passes at 06:45 and 16:10. A render that fetched would have a different
answer every time it ran, could not be replayed, and would fail in a way that looks
like a quiet news day. `tools/validate_events.py` asserts this twice: statically,
by grepping this module and the renderers for a network call, and at runtime, by
building a block with the network guard armed.

ABSENCE IS REPORTED PER SOURCE, not as one empty block. A dormant EDGAR (no contact
address configured) and a failed RSS pull are different facts, and "no filings" is
not the same statement as "filings not collected".
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from altdata import events as ev_mod
from altdata import session, surprise

# How many of each kind the block prints. A block that printed everything would be
# a feed reader; these caps are what make it a briefing. The COUNTS are always
# reported in full, so a cap never hides how much there was.
MAX_RELEASES = 8
MAX_EARNINGS = 8
MAX_FILINGS = 10
MAX_HEADLINES_PER_QUERY = 3
MAX_AHEAD = 12

# How far ahead "the day ahead" looks for the anchor, and the weekly's own window.
AHEAD_DAYS_DEFAULT = 2


def _surprise_for(entities: Iterable[str], as_of: Optional[str],
                  store: Optional[Any] = None) -> list[dict]:
    """The naive surprise for each fred.* entity a release names.

    THE LABEL TRAVELS WITH THE NUMBER. `expectation_kind` is `naive` on every row
    and the metric id says `vs_naive`, because the one thing this must never be
    read as is a consensus surprise -- there is no macro consensus in this system.
    """
    from altdata import derived
    out = []
    for ent in entities:
        if not str(ent).startswith("fred."):
            continue
        key = str(ent).split(".", 1)[1]
        s_key = surprise.surprise_key(key)
        e_key = surprise.expectation_key(key)
        s = derived.derived_forms(s_key, as_of, store=store)
        if s.get("level") is None:
            continue
        e = derived.derived_forms(e_key, as_of, store=store)
        method, why = surprise.method_for(key)
        out.append({
            "metric": str(ent),
            "observed_at": s.get("observed_at"),
            "surprise": s.get("level"),
            "surprise_percentile": s.get("percentile"),
            "naive_expectation": e.get("level"),
            "actual": (None if e.get("level") is None or s.get("level") is None
                       else round(e["level"] + s["level"], 6)),
            "units": (derived.registry_entry(s_key) or {}).get("units"),
            "expectation_kind": "naive",
            "expectation_method": method,
            "expectation_because": why,
        })
    return out


def build(since: str, as_of: Optional[str] = None,
          ahead_days: int = AHEAD_DAYS_DEFAULT,
          store: Optional[Any] = None) -> dict:
    """Everything since `since`, knowable at `as_of`, plus the calendar ahead."""
    cutoff = as_of or session.utc_iso(timespec="microseconds")
    out: dict[str, Any] = {"state": "ok", "since": since, "as_of": cutoff,
                           "ahead_days": ahead_days}
    try:
        ev = ev_mod.EventStore()
    except Exception as exc:                                   # noqa: BLE001
        return {"state": "absent", "since": since, "as_of": cutoff,
                "reason": f"events table unreachable: "
                          f"{type(exc).__name__}: {exc}"}
    try:
        rows = ev.since(since, as_of=cutoff)
        sources = ev.sources()
        counts = ev.counts(since=since, as_of=cutoff)
        import datetime as dt
        first = cutoff[:10]
        last = (dt.date.fromisoformat(cutoff[:10])
                + dt.timedelta(days=ahead_days)).isoformat()
        ahead = ev.calendar(first, last, as_of=cutoff)
    finally:
        ev.close()

    by_type: dict[str, list[dict]] = {}
    for r in rows:
        by_type.setdefault(r["type"], []).append(r)

    # --- RELEASES, with the actual against the declared naive ---------------
    releases = []
    for r in (by_type.get("release") or [])[-MAX_RELEASES:]:
        releases.append({
            "when": r["observed_at"], "source": r["source"],
            "title": r["title"], "url": r.get("url"),
            "entities": r.get("entities") or [],
            "surprises": _surprise_for(r.get("entities") or [], cutoff,
                                       store=store),
        })
    out["releases"] = releases
    out["releases_total"] = len(by_type.get("release") or [])

    # --- EARNINGS, with the real surprise ----------------------------------
    earnings = []
    for r in (by_type.get("earnings") or [])[-MAX_EARNINGS:]:
        p = r.get("payload") or {}
        earnings.append({
            "when": r["observed_at"], "symbol": p.get("symbol"),
            "reported_eps": p.get("reported_eps"),
            "eps_estimate": p.get("eps_estimate"),
            "surprise_pct": p.get("surprise_pct"),
            "expectation_kind": "consensus",
            "consensus": p.get("consensus"),
        })
    out["earnings"] = earnings
    out["earnings_total"] = len(by_type.get("earnings") or [])

    # --- FILINGS, and the difference between none and not-collected ---------
    filings = []
    for r in (by_type.get("filing") or [])[-MAX_FILINGS:]:
        p = r.get("payload") or {}
        filings.append({
            "when": r["observed_at"], "title": r["title"],
            "form": p.get("form"), "why_it_arrived": p.get("why_it_arrived"),
            "entities": r.get("entities") or [], "url": r.get("url"),
        })
    out["filings"] = filings
    out["filings_total"] = len(by_type.get("filing") or [])
    if "sec_edgar" not in sources:
        out["filings_absent_reason"] = (
            "EDGAR has never written: CHESTER_SEC_CONTACT is unset, and EDGAR "
            "refuses a User-Agent without a contact address. `no filings` and "
            "`filings not collected` are different statements and this is the "
            "second")

    # --- HEADLINES, per DECLARED query ------------------------------------
    stories: dict[str, dict] = {}
    for r in by_type.get("headline") or []:
        p = r.get("payload") or {}
        q = str(p.get("query") or "unattributed")
        s = stories.setdefault(q, {"query": q, "theme": p.get("theme"),
                                   "count": 0, "top": []})
        s["count"] += 1
        if len(s["top"]) < MAX_HEADLINES_PER_QUERY:
            s["top"].append({"when": r["observed_at"], "title": r["title"],
                             "url": r.get("url"), "source": r["source"]})
    out["headlines"] = sorted(stories.values(), key=lambda s: -s["count"])
    out["headlines_total"] = len(by_type.get("headline") or [])
    out["headline_note"] = (
        "A COUNT IS ATTENTION, NOT EVIDENCE. The result set is whatever a free "
        "aggregator returned for a query declared in config/story_queries.yaml, "
        "capped per query per day, so the denominator is nobody's published "
        "figure. It cannot corroborate a price move: the story and the move are "
        "one fact reported twice")

    # --- SESSION EVENTS since, and the CALENDAR AHEAD ----------------------
    out["session_events"] = [
        {"when": r["observed_at"], "title": r["title"],
         "classes": (r.get("payload") or {}).get("classes") or []}
        for r in (by_type.get("session_event") or [])]
    out["ahead"] = [
        {"when": r["observed_at"], "type": r["type"], "title": r["title"],
         "source": r["source"], "entities": (r.get("entities") or [])[:6],
         "payload": {k: v for k, v in (r.get("payload") or {}).items()
                     if k in ("kind", "classes", "eps_estimate", "release_name",
                              "series", "symbol")}}
        for r in ahead[:MAX_AHEAD]]
    out["ahead_total"] = len(ahead)

    # --- WHAT EACH SOURCE HAS DONE ----------------------------------------
    out["sources"] = {name: {"rows": c["n"], "newest": c["newest"],
                             "last_ingest": c["last_ingest"]}
                      for name, c in sources.items()}
    out["dormant"] = {k: v for k, v in ev_mod.DORMANT_REASONS.items()
                      if k not in sources}
    out["counts_since"] = {k: v["n"] for k, v in counts.items()}
    if not rows and not ahead:
        out["state"] = "empty"
        out["reason"] = (
            f"the events table holds nothing between {since} and {cutoff} and "
            f"nothing scheduled in the next {ahead_days} day(s). The ingest runs "
            f"at 06:45 and 16:10; if it has never run, "
            f"`python -m altdata.events_ingest pull` fills it")
    return out


def narrative_figures(block: dict) -> dict:
    """The compact form a paragraph may cite. Counts and named surprises only.

    NARROWER THAN THE BLOCK, on the same rule the Monthly's payload follows: the
    full block carries a hundred headlines' worth of timestamps, and a paragraph
    given all of them can cite an intermediate as a headline. What travels is what
    a sentence would legitimately say.
    """
    biggest = None
    for r in block.get("releases") or []:
        for s in r.get("surprises") or []:
            p = s.get("surprise_percentile")
            if p is None:
                continue
            if biggest is None or p > (biggest.get("surprise_percentile") or -1):
                biggest = dict(s, release=r.get("title"))
    return {
        "since": block.get("since"),
        "releases_total": block.get("releases_total"),
        "earnings_total": block.get("earnings_total"),
        "filings_total": block.get("filings_total"),
        "headlines_total": block.get("headlines_total"),
        "headlines_by_query": {s["query"]: s["count"]
                               for s in (block.get("headlines") or [])},
        "ahead_total": block.get("ahead_total"),
        "largest_naive_surprise": biggest,
        "earnings_surprises": [
            {"symbol": e.get("symbol"), "surprise_pct": e.get("surprise_pct")}
            for e in (block.get("earnings") or [])
            if e.get("surprise_pct") is not None],
        "absent": block.get("filings_absent_reason"),
        "dormant": block.get("dormant"),
    }


# The anchor is HTML and the Weekly is Markdown, so this module emits both from ONE
# block dict -- the same arrangement state_block.py has. Styles copied from there
# rather than imported, because state_block is not this module's dependency and a
# shared style module for six constants would be indirection for its own sake.
H2 = ("font-size:13px;margin:22px 0 6px 0;color:#0d2b45;font-weight:600;"
      "letter-spacing:0.02em;text-transform:uppercase")
NOTE = "font-size:11px;color:#5a6b7a;margin:4px 0 0 0;line-height:1.45;"
P = "font-size:12px;color:#20313f;margin:3px 0 0 0;line-height:1.5;"
TABLE = "border-collapse:collapse;width:100%;font-size:12px;margin:4px 0 0 0"
THL = ("text-align:left;padding:5px 7px;border-bottom:2px solid #0d2b45;"
       "color:#0d2b45")
TH = ("text-align:right;padding:5px 7px;border-bottom:2px solid #0d2b45;"
      "color:#0d2b45")
TDL = "text-align:left;padding:4px 7px;border-bottom:1px solid #e6ebef"
TD = "text-align:right;padding:4px 7px;border-bottom:1px solid #e6ebef"


def _esc(v: Any) -> str:
    import html
    return html.escape("" if v is None else str(v), quote=True)


def _link(title: Any, url: Any) -> str:
    t = _esc(title)
    return (f'<a href="{_esc(url)}" style="color:#1d4e6f">{t}</a>' if url
            else t)


def html(block: dict) -> str:
    """The anchor's EVENTS block. Data only; every figure came from the store."""
    if block.get("state") != "ok":
        return (f'<p style="{P}"><b>{_esc(block.get("state") or "absent")}.</b> '
                f'{_esc(block.get("reason") or "No reason recorded.")}</p>')
    out = [f'<p style="{NOTE}">Since {_esc(str(block.get("since"))[:16])}. '
           f'Read from the events table; this block fetched nothing.</p>']

    out.append(f'<p style="{P}"><b>Releases '
               f'({block.get("releases_total", 0)})</b></p>')
    rel = block.get("releases") or []
    if not rel:
        out.append(f'<p style="{NOTE}">None in the window.</p>')
    for r in rel:
        out.append(f'<p style="{P}">{_esc(str(r["when"])[:16])} &middot; '
                   f'{_esc(r["source"])} &mdash; {_link(r["title"], r.get("url"))}'
                   f'</p>')
        for sp in r.get("surprises") or []:
            out.append(
                f'<p style="{NOTE}">&nbsp;&nbsp;<code>{_esc(sp["metric"])}</code> '
                f'actual {_fmt(sp["actual"])} against a naive '
                f'{_fmt(sp["naive_expectation"])} ({_esc(sp["expectation_method"])})'
                f' &rarr; <b>{_fmt(sp["surprise"])} {_esc(sp.get("units") or "")}</b>,'
                f' {_fmt(sp["surprise_percentile"], 1)} percentile of its own '
                f'surprise history. Naive, not a consensus.</p>')

    earn = block.get("earnings") or []
    out.append(f'<p style="{P}"><b>Earnings '
               f'({block.get("earnings_total", 0)})</b></p>')
    if not earn:
        out.append(f'<p style="{NOTE}">None in the window.</p>')
    else:
        rows = "".join(
            f'<tr><td style="{TDL}">{_esc(str(e["when"])[:10])}</td>'
            f'<td style="{TDL}">{_esc(e.get("symbol"))}</td>'
            f'<td style="{TD}">{_fmt(e.get("reported_eps"))}</td>'
            f'<td style="{TD}">{_fmt(e.get("eps_estimate"))}</td>'
            f'<td style="{TD}">{_fmt(e.get("surprise_pct"))}%</td></tr>'
            for e in earn)
        out.append(
            f'<table style="{TABLE}"><tr><th style="{THL}">When</th>'
            f'<th style="{THL}">Symbol</th><th style="{TH}">Reported</th>'
            f'<th style="{TH}">Consensus</th><th style="{TH}">Surprise</th></tr>'
            f'{rows}</table>')

    out.append(f'<p style="{P}"><b>Filings '
               f'({block.get("filings_total", 0)})</b></p>')
    if block.get("filings_absent_reason"):
        out.append(f'<p style="{NOTE}">{_esc(block["filings_absent_reason"])}</p>')
    elif not (block.get("filings") or []):
        out.append(f'<p style="{NOTE}">None in the window.</p>')
    for f in block.get("filings") or []:
        out.append(f'<p style="{P}">{_esc(str(f["when"])[:16])} &middot; '
                   f'{_link(f["title"], f.get("url"))} &mdash; '
                   f'{_esc(f.get("why_it_arrived") or f.get("form"))}</p>')

    out.append(f'<p style="{P}"><b>Story queries '
               f'({block.get("headlines_total", 0)} items)</b></p>')
    heads = block.get("headlines") or []
    if not heads:
        out.append(f'<p style="{NOTE}">No items returned for any declared '
                   f'query.</p>')
    for sq in heads:
        out.append(f'<p style="{P}">{_esc(sq.get("theme") or sq["query"])} '
                   f'&mdash; {sq["count"]} item(s)</p>')
        for it in sq.get("top") or []:
            out.append(f'<p style="{NOTE}">&nbsp;&nbsp;'
                       f'{_esc(str(it["when"])[:10])} '
                       f'{_link(it["title"], it.get("url"))}</p>')
    out.append(f'<p style="{NOTE}">{_esc(block.get("headline_note"))}</p>')

    out.append(f'<p style="{P}"><b>Ahead, next {block.get("ahead_days")} '
               f'day(s) ({block.get("ahead_total", 0)})</b></p>')
    ahead = block.get("ahead") or []
    if not ahead:
        out.append(f'<p style="{NOTE}">Nothing scheduled in the window.</p>')
    for r in ahead:
        extra = {k: v for k, v in (r.get("payload") or {}).items()
                 if k in ("kind", "eps_estimate") and v is not None}
        bits = (" (" + ", ".join(f"{k}={v}" for k, v in extra.items()) + ")"
                if extra else "")
        out.append(f'<p style="{P}">{_esc(str(r["when"])[:16])} &middot; '
                   f'{_esc(r["source"])} &mdash; {_esc(r["title"])}'
                   f'{_esc(bits)}</p>')

    dormant = block.get("dormant") or {}
    if dormant:
        out.append(f'<p style="{NOTE}">Dormant sources: '
                   + _esc("; ".join(f"{k} ({v})" for k, v in dormant.items()))
                   + ".</p>")
    return "\n".join(out)


def text_lines(block: dict) -> list[str]:
    """The same block for the plain-text fallback. Counts, not content."""
    if block.get("state") != "ok":
        return [f"EVENTS: {block.get('state')} -- "
                f"{(block.get('reason') or '')[:120]}"]
    L = [f"EVENTS since {str(block.get('since'))[:16]}: "
         f"{block.get('releases_total', 0)} release(s), "
         f"{block.get('earnings_total', 0)} earnings, "
         f"{block.get('filings_total', 0)} filing(s), "
         f"{block.get('headlines_total', 0)} headline(s), "
         f"{block.get('ahead_total', 0)} ahead"]
    for r in (block.get("releases") or [])[-3:]:
        L.append(f"  {str(r['when'])[:16]} {r['title'][:70]}")
        for sp in r.get("surprises") or []:
            L.append(f"    {sp['metric']} surprise {_fmt(sp['surprise'])} "
                     f"vs naive (not a consensus)")
    for sq in block.get("headlines") or []:
        L.append(f"  {sq.get('theme') or sq['query']}: {sq['count']} item(s)")
    if block.get("dormant"):
        L.append("  dormant: " + ", ".join(block["dormant"]))
    return L


def _fmt(v: Any, dp: int = 2) -> str:
    try:
        return f"{float(v):,.{dp}f}"
    except (TypeError, ValueError):
        return "—"


def render(block: dict) -> str:
    """The Markdown. Data only -- no sentence here was generated."""
    if block.get("state") != "ok":
        return (f"## EVENTS\n\n**{block.get('state', 'absent')}.** "
                f"{block.get('reason') or 'No reason recorded.'}\n")
    out = [f"## EVENTS — since {str(block.get('since'))[:16]}\n"]

    rel = block.get("releases") or []
    out.append(f"### Releases ({block.get('releases_total', 0)})\n")
    if not rel:
        out.append("*None in the window.*\n")
    for r in rel:
        out.append(f"- **{str(r['when'])[:16]}** · {r['source']} — {r['title']}"
                   + (f" ([source]({r['url']}))" if r.get("url") else ""))
        for s in r.get("surprises") or []:
            out.append(
                f"    - `{s['metric']}` actual {_fmt(s['actual'])} against a "
                f"naive {_fmt(s['naive_expectation'])} "
                f"({s['expectation_method']}) → **{_fmt(s['surprise'])} "
                f"{s.get('units') or ''}**, {_fmt(s['surprise_percentile'], 1)}"
                f" percentile of its own surprise history. *Naive, not a "
                f"consensus.*")
    out.append("")

    earn = block.get("earnings") or []
    out.append(f"### Earnings ({block.get('earnings_total', 0)})\n")
    if not earn:
        out.append("*None in the window.*\n")
    else:
        out.append("| When | Symbol | Reported | Consensus | Surprise |")
        out.append("|---|---|---|---|---|")
        for e in earn:
            out.append(f"| {str(e['when'])[:10]} | {e.get('symbol')} | "
                       f"{_fmt(e.get('reported_eps'))} | "
                       f"{_fmt(e.get('eps_estimate'))} | "
                       f"{_fmt(e.get('surprise_pct'))}% |")
        out.append("")

    fil = block.get("filings") or []
    out.append(f"### Filings ({block.get('filings_total', 0)})\n")
    if block.get("filings_absent_reason"):
        out.append(f"*{block['filings_absent_reason']}*\n")
    elif not fil:
        out.append("*None in the window.*\n")
    for f in fil:
        out.append(f"- **{str(f['when'])[:16]}** · {f['title']} — "
                   f"{f.get('why_it_arrived') or f.get('form')}"
                   + (f" ([filing]({f['url']}))" if f.get("url") else ""))
    out.append("")

    heads = block.get("headlines") or []
    out.append(f"### Story queries ({block.get('headlines_total', 0)} items)\n")
    if not heads:
        out.append("*No items returned for any declared query.*\n")
    for s in heads:
        out.append(f"- **{s.get('theme') or s['query']}** — {s['count']} item(s)")
        for it in s.get("top") or []:
            out.append(f"    - {str(it['when'])[:10]} [{it['title']}]"
                       f"({it.get('url') or ''})")
    out.append(f"\n*{block.get('headline_note')}*\n")

    ahead = block.get("ahead") or []
    out.append(f"### Ahead, next {block.get('ahead_days')} day(s) "
               f"({block.get('ahead_total', 0)})\n")
    if not ahead:
        out.append("*Nothing scheduled in the window.*\n")
    for r in ahead:
        extra = r.get("payload") or {}
        bits = ", ".join(f"{k}={v}" for k, v in extra.items()
                         if k in ("kind", "eps_estimate") and v is not None)
        out.append(f"- **{str(r['when'])[:16]}** · {r['source']} — {r['title']}"
                   + (f" ({bits})" if bits else ""))
    out.append("")

    dormant = block.get("dormant") or {}
    if dormant:
        out.append("*Dormant sources: "
                   + "; ".join(f"{k} ({v})" for k, v in dormant.items())
                   + ".*\n")
    return "\n".join(out)
