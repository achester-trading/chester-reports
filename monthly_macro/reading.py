"""
The Monthly's Reading chapter. (docs/briefs/reading-shelf-brief-2026-10-05.md
section 5; change order 2026-10-08, ruling D1; T3 second half)

    from monthly_macro import reading
    sec = reading.section(then, month_end, now, voices_urls, cfg)

PLACED IMMEDIATELY AFTER NARRATIVES AND BEFORE AHEAD (D1): outside views sit
together, and "due next month" leads into Ahead. Built from the committed
docs/reading/register.json and docs/reading/watchlist.json with NO MODEL CALL.

PUBLISHED THIS MONTH: the register's entries with `published` in (the prior
month's end, this month's end] -- consecutive Monthlies tile the calendar, so no
edition prints twice and none falls between -- status read or listed, in the
watchlist's group order. Each prints a hyperlinked title line -- publication,
publisher, the published date, the data-as-of date where it differs, the scan
where one exists -- and then:

  deep and skim   the stored `summary`, VERBATIM. The renderer escapes it and
                  never rewrites, trims or polishes it; the budget neither counts
                  nor cuts it (it is stored text, not this edition's prose); the
                  numeral audit does not apply (its figures are the
                  publication's, carried with their as-of dates). The reading
                  time does count it.
  list            the one-liner (`line`) on the title line.

NO STORED SOURCE, NOT PRINTED: an entry without a URL is withheld and the
footnote counts it. A pending entry never prints. A shelf voices entry whose URL
the daily scan already stored -- and Narratives' voices table therefore already
prints -- is not printed twice: it is deduped by URL and named in the footnote.
No candidate, ruling, theme or stance prints here.

DUE BEFORE THE NEXT MONTHLY: the watchlist's items whose expected months include
the coming month, linked to their index pages. Irregular items are not listed.
An empty month prints "Nothing on the shelf was published this month." and the
due list.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parent.parent
REGISTER = REPO / "docs" / "reading" / "register.json"
WATCHLIST = REPO / "docs" / "reading" / "watchlist.json"
SECTION_ID = "reading"
EMPTY_LINE = "Nothing on the shelf was published this month."
URL = re.compile(r"https?://[^\s,;)\]\"'<>]+")


def load(register: Optional[Path] = None, watchlist: Optional[Path] = None
         ) -> tuple[list[dict], dict]:
    reg = json.loads(Path(register or REGISTER).read_text(encoding="utf-8"))
    wl = json.loads(Path(watchlist or WATCHLIST).read_text(encoding="utf-8"))
    return list(reg.get("entries") or []), wl


def _day(d: Optional[str]) -> str:
    """'2026-10-01' -> '1 Oct 2026'."""
    try:
        x = dt.date.fromisoformat(str(d)[:10])
    except (TypeError, ValueError):
        return str(d)
    return f"{x.day} {x:%b %Y}"


def voices_urls(voices_block: Optional[dict]) -> set[str]:
    """Every URL the Narratives' voices table prints (the daily scan's rows)."""
    return set(u.rstrip(".") for u in URL.findall(json.dumps(voices_block or {})))


def title_line(e: dict) -> dict:
    """The title line's parts, for both renderers: the linked publication, then
    the meta in order. The renderer links `publication` to `url` and `scan` to
    `scan_url`."""
    meta = [e.get("publisher") or "", f"published {_day(e.get('published'))}"]
    if e.get("as_of") and str(e["as_of"])[:10] != str(e.get("published"))[:10]:
        meta[-1] += f" (data as of {_day(e['as_of'])})"
    return {"publication": e.get("publication") or e.get("id"), "url": e["url"],
            "meta": " · ".join(m for m in meta if m)}


def section(then: str, month_end: str, now: str, printed_voice_urls: set[str],
            cfg: dict,
            register: Optional[Path] = None, watchlist: Optional[Path] = None
            ) -> dict:
    """The chapter's data. Never raises on content: a register that cannot be
    read prints its reason in the footnote."""
    rcfg = cfg.get("monthly_reading") or {}
    blob = str(rcfg.get("repo_blob_url") or "").rstrip("/")
    lo, hi = str(then)[:10], str(month_end)[:10]
    try:
        entries, wl = load(register, watchlist)
    except (OSError, ValueError) as exc:
        return {"entries_by_group": [], "due": [], "withheld": 0, "deduped": [],
                "fault": f"the reading register could not be read "
                         f"({type(exc).__name__})"}
    groups = wl.get("groups") or {}
    order = list(groups) + sorted({e.get("group") for e in entries} - set(groups)
                                  - {None})
    month = [e for e in entries
             if e.get("status") in ("read", "listed")
             and lo < str(e.get("published") or "")[:10] <= hi]
    withheld = [e for e in month if not str(e.get("url") or "").startswith("http")]
    deduped = [e for e in month if e not in withheld and e.get("group") == "voices"
               and e["url"] in printed_voice_urls]
    shown = [e for e in month if e not in withheld and e not in deduped]
    by_group = []
    for g in order:
        rows = sorted((e for e in shown if e.get("group") == g),
                      key=lambda e: (str(e.get("published")), e["id"]))
        if not rows:
            continue
        out = []
        for e in rows:
            t = title_line(e)
            scan = e.get("scan")
            out.append({
                "id": e["id"], **t,
                "scan": scan,
                "scan_url": (f"{blob}/{scan}" if scan and blob else None),
                # STORED TEXT, VERBATIM: a summary for deep and skim, the line
                # for list items. Nothing below this point edits either.
                "summary": e.get("summary") or None,
                "line": None if e.get("summary") else (e.get("line") or None)})
        by_group.append({"group": g, "title": groups.get(g, g), "entries": out})
    return {"entries_by_group": by_group, "due": due(wl, now), "withheld": len(withheld),
            "deduped": [e.get("publication") or e["id"] for e in deduped]}


def due(wl: dict, now: str) -> list[dict]:
    """Watchlist items expected in the coming month (the month of the next
    Monthly's window), irregular items left out."""
    d = dt.date.fromisoformat(str(now)[:10])
    nxt = d.month if d.day <= 7 else (d.month % 12) + 1
    out = []
    for it in wl.get("items") or []:
        exp = it.get("expected")
        if not isinstance(exp, dict) or nxt not in (exp.get("months") or []):
            continue
        out.append({"publication": it.get("publication"),
                    "publisher": it.get("publisher"),
                    "window": exp.get("window"), "url": it.get("index_url"),
                    "group": it.get("group")})
    return out


def words(sec: dict) -> int:
    """The stored text the chapter prints -- counted in the reading time, never
    in the prose budget."""
    n = 0
    for g in sec.get("entries_by_group") or []:
        for e in g["entries"]:
            n += len(str(e.get("summary") or e.get("line") or "").split())
    return n


def stack_section(data: dict, spec: dict, prior: Optional[dict]) -> dict:
    """The chapter as a stack section, in the shape every renderer reads, plus
    `entries` blocks: one sub-section per group, then the due list."""
    from daily_cascade.stack import _fp, item                    # noqa: PLC0415
    subs: list[dict[str, Any]] = []
    items = []
    for g in data.get("entries_by_group") or []:
        subs.append({"title": g["title"], "entries": g["entries"]})
        for e in g["entries"]:
            items.append(item(f"reading:{e['id']}", e["publication"], 2,
                              (e["url"], e.get("summary"), e.get("line"))))
    n = sum(len(g["entries"]) for g in data.get("entries_by_group") or [])
    subs.append({"title": "Due before the next Monthly",
                 "entries": [{"publication": d["publication"], "url": d["url"],
                              "meta": " · ".join(x for x in (
                                  d.get("publisher"),
                                  f"usually {d['window']}" if d.get("window") else None)
                                  if x),
                              "summary": None, "line": None}
                             for d in data.get("due") or [] if d.get("url")],
                 "lines": ([] if data.get("due") else
                           ["Nothing on the shelf is due before the next Monthly."])})
    notes = []
    if data.get("withheld"):
        k = data["withheld"]
        notes.append(f"{k} {'entry' if k == 1 else 'entries'} withheld: no stored "
                     f"source.")
    if data.get("deduped"):
        notes.append("Printed once, under Narratives' voices (same URL): "
                     + "; ".join(data["deduped"]) + ".")
    if data.get("fault"):
        notes.append(data["fault"] + ".")
    for it in items:
        it["show"] = False
    claim = (f"{n} shelf edition{'' if n == 1 else 's'} published this month, "
             f"each with its stored summary or line." if n else EMPTY_LINE)
    pr = {x["id"]: x for x in (prior or {}).get("sections") or []}.get(SECTION_ID) or {}
    pmarks = {i["key"]: i["fingerprint"] for i in pr.get("items") or []}
    for it in items:
        it["changed"] = bool(prior) and pmarks.get(it["key"]) != it["fingerprint"]
    return {"id": SECTION_ID, "title": spec.get("title") or "Reading",
            "subtitle": spec.get("monthly_subtitle") or spec.get("subtitle"),
            "depth": spec.get("monthly") or "deep", "depth_reason": None,
            "items": items, "print_items": False, "table": None,
            "subsections": subs, "data": {"reading": data},
            "not_tracked": [], "legend": None, "notes": notes,
            "fingerprint": _fp([(i["key"], i["fingerprint"]) for i in items]),
            "collapsed": False, "unchanged_since": None, "prior_claim": None,
            "claim": claim, "paragraphs": [], "trimmed": False, "period": "month",
            "phase_a": [], "prose_wanted": False, "empty": False,
            "stored_words": words(data)}
