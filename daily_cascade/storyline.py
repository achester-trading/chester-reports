"""
THE WEEKLY'S STORYLINE LAYOUT (W-1.2 items 2.4, 2.6, 2.7; change order of 11 Oct
2026, section 3). Code only, over the finished edition, after the prose:

  2.4  each open contradiction in What doesn't fit carries a status line --
       "resolved by <section>" (linked to the section that holds the evidence),
       "carried -- resolves when <condition>", or "stale" -- from the
       contradiction's state and the sections' printed rows;
  2.6  collapse by default, expand in reference: silent and unreachable voices to
       one line; a family of prediction-market resolutions to one row, its modal
       outcome and probability; an extreme the tape already prints to one line;
       the rows to the reference tables after the last section;
  2.7  tape and mechanics de-duplicated: the daily session tables (the week by
       day, the overnight split) print in Mechanics only; the tape's named
       levels go to the reference tables.

Never raises into the report: each step is independent, and a step that faults
leaves the edition as it was.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

log = logging.getLogger(__name__)

STATUSES = ("resolved by", "carried", "stale")
DAILY_TABLE_TITLES = ("The week by day", "SPY overnight against the cash session")


def _by(ed: dict) -> dict:
    return {s["id"]: s for s in ed.get("sections") or []}


def _detail(ed: dict, title: str, table: dict, note: Optional[str] = None) -> None:
    if table and table.get("rows"):
        ed.setdefault("detail", []).append(
            {"title": title, "table": table, **({"notes": [note]} if note else {})})


def row_names(s: dict) -> set[str]:
    """The first-column names every table in a section prints."""
    out = set()
    for t in [s.get("table")] + [ss.get("table") for ss in s.get("subsections") or []]:
        for r in (t or {}).get("rows") or []:
            if r:
                out.add(str(r[0]).strip())
    return out


# ---------------------------------------------------------------------------
# 2.4 contradiction status lines
# ---------------------------------------------------------------------------
def status_for(c: dict, gap: dict, ed: dict, cfg: dict) -> tuple[str, Optional[str]]:
    """(status line, link) for one open contradiction."""
    from altdata import labels                                  # noqa: PLC0415
    sc = cfg.get("storyline") or {}
    by = _by(ed)
    res = (sc.get("contradiction_resolution") or {}).get(c.get("id")) or {}
    s = by.get(res.get("section") or "")
    if s and s.get("claim") and set(res.get("rows") or []) <= row_names(s):
        return f"resolved by {s['title']}", f"#sec-{s['id']}"
    sessions = gap.get("sessions_open") or c.get("persistence_days") or 0
    if int(sessions or 0) >= int(sc.get("stale_sessions") or 20) \
            and gap.get("direction") in ("falling", "—", None):
        return "stale", None
    closes = (labels.contradiction_plain(c.get("id")) or {}).get("closes") \
        or "the gap's z falls back inside its line"
    return f"carried — resolves when {closes}", None


def contradiction_status(ed: dict, cfg: dict) -> None:
    """The gap table's last column becomes the status line (it carried "what
    would close it", which the carried status now says)."""
    m = _by(ed).get("misfit") or {}
    data = m.get("data") or {}
    rows = data.get("_contradiction_rows") or []
    gaps = data.get("gaps") or []
    t = m.get("table") or {}
    if not rows or not t.get("rows"):
        return
    cols = list(t.get("columns") or [])
    if cols and cols[-1] == "What would close it":
        cols[-1] = "Status"
    t["columns"] = cols
    links = []
    for k, (c, g) in enumerate(zip(rows, gaps)):
        line, href = status_for(c, g, ed, cfg)
        g["status"] = line
        if k < len(t["rows"]):
            t["rows"][k][-1] = line
            if href:
                links.append([k, len(cols) - 1, href])
    if links:
        t["cell_links"] = links


# ---------------------------------------------------------------------------
# 2.6 collapse by default
# ---------------------------------------------------------------------------
def collapse_voices(ed: dict) -> None:
    s = _by(ed).get("narratives") or {}
    t = s.get("table") or {}
    cols = list(t.get("columns") or [])
    if "Status" not in cols:
        return
    i = cols.index("Status")
    quiet = [r for r in t.get("rows") or []
             if str(r[i]).startswith(("SILENT", "UNREACHABLE"))]
    if not quiet:
        return
    n_s = sum(1 for r in quiet if str(r[i]).startswith("SILENT"))
    n_u = len(quiet) - n_s
    t["rows"] = [r for r in t["rows"] if r not in quiet]
    s.setdefault("summarised", []).append(
        f"Voices: {n_s} silent, {n_u} unreachable.")
    _detail(ed, "Voices: silent and unreachable this week",
            {"columns": cols, "rows": quiet})


def collapse_families(ed: dict, cfg: dict) -> None:
    """Ahead's prediction-market resolutions: a family of outcomes on one day
    prints as one row -- its modal outcome (the likeliest) and its probability."""
    from .figure_budget import contract_family, parse_figure   # noqa: PLC0415
    s = _by(ed).get("ahead") or {}
    t = s.get("table") or {}
    cols = list(t.get("columns") or [])
    if "Event" not in cols:
        return
    ei = cols.index("Event")
    # The consensus column by name (W-1.3a's ranked table carries two after it).
    ci = next((i for i, c in enumerate(cols) if str(c).startswith("Consensus")),
              len(cols) - 1)
    groups: dict = {}
    for r in t.get("rows") or []:
        ev = str(r[ei])
        if ev.startswith("Prediction market resolves:"):
            groups.setdefault((r[0], contract_family(ev)), []).append(r)
    need = int((cfg.get("storyline") or {}).get("family_min_outcomes") or 2)
    fams = {k: v for k, v in groups.items() if len(v) >= need}
    if not fams:
        return
    full = []

    def p(r) -> float:
        f = parse_figure(r[ci])
        return f[0] if f else -1.0
    keep, done = [], set()
    for r in t["rows"]:
        k = (r[0], contract_family(str(r[ei])))
        if k not in fams:
            keep.append(r)
            continue
        if k in done:
            continue
        done.add(k)
        rows = fams[k]
        modal = max(rows, key=p)
        q = str(modal[ei]).split(":", 1)[1].strip()
        row = list(modal)
        row[ei] = (f"Prediction markets resolve: {len(rows)} outcomes; "
                   f"modal: {q}")
        row[ci] = str(modal[ci]).replace("last ", "modal outcome, last ")
        keep.append(row)
        full += rows
        s.setdefault("summarised", []).append(
            f"{r[0]}: {len(rows)} prediction-market outcomes resolve; the modal one, "
            f"{q}, {str(modal[ci]).replace('last ', 'last at ')}.")
    t["rows"] = keep
    _detail(ed, "Prediction-market resolutions, every outcome",
            {"columns": cols, "rows": full})


def tape_metrics() -> set[str]:
    from altdata import bars as bars_mod                        # noqa: PLC0415
    out = set()
    for t in bars_mod.tape():
        out.add(str(t.get("daily") or ""))
        out.add(str((t.get("fallback") or {}).get("daily") or ""))
    return {x for x in out if x}


def collapse_exceptions(ed: dict) -> None:
    """An exception that only restates a five-year extreme of a series the tape
    already prints: one line each, the row to the reference tables."""
    from altdata import labels                                  # noqa: PLC0415
    s = _by(ed).get("misfit") or {}
    ids = (s.get("data") or {}).get("_exception_ids") or []
    tm = tape_metrics()
    dup = {labels.exception(e) for e in ids
           if str(e).startswith("extreme:") and str(e).split(":", 1)[1] in tm}
    if not dup:
        return
    for ss in s.get("subsections") or []:
        t = ss.get("table") or {}
        if not str(ss.get("title", "")).startswith("Exceptions open"):
            continue
        moved = [r for r in t.get("rows") or [] if str(r[0]) in dup]
        if not moved:
            continue
        t["rows"] = [r for r in t["rows"] if r not in moved]
        for r in moved:
            s.setdefault("summarised", []).append(f"{r[0]} -- the tape prints it.")
        _detail(ed, "Exceptions the tape already prints",
                {"columns": t.get("columns"), "rows": moved})


# ---------------------------------------------------------------------------
# 2.7 tape and mechanics de-duplicated
# ---------------------------------------------------------------------------
def move_daily_tables(ed: dict) -> None:
    by = _by(ed)
    read, tape, mech = by.get("read") or {}, by.get("tape") or {}, by.get("mechanics")
    if not mech:
        return
    subs = list(mech.get("subsections") or [])
    if read.get("table") and read["table"].get("rows"):
        subs.insert(0, {"title": "The week by day", "table": read["table"],
                        "table_note": read.get("table_note"),
                        "daily_session_table": True, "paragraph_wanted": False})
        read["table"] = None
        read["table_note"] = None
    keep = []
    for ss in tape.get("subsections") or []:
        title = str(ss.get("title") or "")
        if title.startswith("SPY overnight"):
            subs.append({**ss, "daily_session_table": True})
        elif title == "Levels":
            _detail(ed, "The tape: named levels", ss.get("table") or {})
        else:
            keep.append(ss)
    tape["subsections"] = keep
    mech["subsections"] = subs


def move_reference(ed: dict) -> None:
    """A section's own reference rows (W-1.3a: Ahead's routine releases and every
    outcome of a collapsed family) go to the reference tables."""
    for s in ed.get("sections") or []:
        for r in s.pop("reference", None) or []:
            _detail(ed, r["title"], r["table"], r.get("note"))


def layout(ed: dict, cfg: dict) -> None:
    for step in (lambda: move_reference(ed),
                 lambda: contradiction_status(ed, cfg), lambda: collapse_voices(ed),
                 lambda: collapse_families(ed, cfg), lambda: collapse_exceptions(ed),
                 lambda: move_daily_tables(ed)):
        try:
            step()
        except Exception:                                       # noqa: BLE001
            log.warning("storyline layout step failed", exc_info=True)


def daily_table_sections(ed: dict) -> list[str]:
    """The sections that print a daily session table (the gate's check: one)."""
    out = []
    for s in ed.get("sections") or []:
        tabs = [s] + list(s.get("subsections") or [])
        if any(x.get("daily_session_table") or (
                (x.get("table") or {}).get("rows")
                and str(((x.get("table") or {}).get("columns") or [""])[0]).strip()
                .lower() in ("session", "date")) for x in tabs):
            out.append(s["id"])
    return out


# ---------------------------------------------------------------------------
# 2.8 every table row carries its unit
# ---------------------------------------------------------------------------
_BARE = re.compile(r"^[+−-]?\d[\d,]*(?:\.\d+)?$")
_UNIT_CUE = re.compile(
    r"%|\bbp\b|\bbps\b|\$|\bpts\b|\bpoints?\b|\bcontracts?\b|\bz\b|z-score|"
    r"percentile|\bsessions?\b|\bdays?\b|\bminutes?\b|\bcount\b|\bratio\b|\bindex\b|"
    r"\bn\b|\bpackets?\b|\brulings?\b|\bdecisions?\b|\bbreaks?\b|\bimportance\b|"
    r"\brank\b|\bresolved\b|\bbrier\b|\bvol(?:ume)?\b|\byen\b|\bdollars?\b|\beuros?\b|"
    r"\byuan\b|\bper\b|\bmillion\b|\bbillion\b|\bthousand\b|\btrillion\b|\bx\b|"
    r"\(1-5\)|\bclusters?\b|\bvoices?\b|\bitems?\b|\bshares?\b|\bjobs?\b|\bbarrels?\b|"
    r"\bscore\b|\bcoin\b",
    re.I)


def unitless_rows(ed: dict) -> list[str]:
    """Rows in the read path with a bare number whose column head and row label
    both lack a unit: "<section> / <table> / <row>: <column> = <cell>"."""
    out = []
    for s in ed.get("sections") or []:
        for x in [s] + list(s.get("subsections") or []):
            t = x.get("table") or {}
            cols = [str(c) for c in t.get("columns") or []]
            for r in t.get("rows") or []:
                label = str(r[0]) if r else ""
                for i, v in enumerate(r[1:], start=1):
                    txt = "" if v is None else str(v).strip()
                    if not _BARE.match(txt):
                        continue
                    head = cols[i] if i < len(cols) else ""
                    if _UNIT_CUE.search(head) or _UNIT_CUE.search(label):
                        continue
                    out.append(f"{s.get('id')} / {x.get('title') or s.get('title')} / "
                               f"{label}: {head} = {txt}")
    return out
