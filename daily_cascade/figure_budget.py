"""
THE FIGURE BUDGET AT THE FRAME (T3.4, 10 Oct 2026).

Three dry runs in a row, the five parent sections (the tape, Plumbing,
Positioning, What's priced, Slow layers) and the FOMC and liquidity blocks cited
9 to 21 figures against a cap of 8, through three explicit retries. Telling the
writer the cap did not work, because its frame offered it every number the
section's tables held. This module builds frames that offer no more figures than
the paragraph may cite:

  PARENT SECTIONS, every cadence: at most the cadence's cap of figures, one per
    move -- the section's moves ranked largest first, each with its display form
    exactly as its table prints it. Every other series the section covers is
    under `also_moved`, by name only, with no number. The frame says the blocks
    beneath carry those numbers.
  BLOCKS (the Monthly's written reads under a table): rows ranked by absolute
    change, as many as fit the cap; the rest by name only.
  SUMMARY PARAGRAPHS (the Monthly's executive summary): the summarised section's
    prose, its figures masked, plus "figures you may cite" -- the section's top
    three moves, ranked the same way. The audit's scope (T3.3: the union of the
    sections' figures and ordinals) is not this module's and is unchanged.

Every frame presents a percentile as its `_ordinal` only, never the raw number,
so a writer cannot round one itself. The caps are the cadence's configuration
(`cadences.<c>.paragraph_figures`, `cadences.<c>.summary_figures`), never a
literal here. `quantified_figures()` is the count the gate holds every frame to.

WHAT "LARGEST FIRST" MEANS (session-set, T3.4). A section's moves come in
different units -- a price in percent, a yield in basis points, a balance in
dollars -- so the parent ranking is by the move relative to its level: a
percent move as printed; a basis-point, point, dollar or count change divided by
the level it moved from. A move with no level to scale it ranks after those that
have one, in table order. A block's rows are ranked by absolute change in the
row's own unit, as ruled.
"""

from __future__ import annotations

import re
from typing import Optional

from . import readability

# A table's change column and its level column, by header.
CHANGE_HEAD = re.compile(r"\b(move|change|the month|month or prior|priced or change|"
                         r"week|session)\b", re.I)
LEVEL_HEAD = re.compile(r"\b(close|level|latest|actual|kalshi)\b", re.I)
# Keys whose values are names or dates, never quantified figures.
NAME_KEYS = frozenset({"section", "block", "series", "name", "title", "also_moved",
                       "depth", "depth_reason", "session", "month", "from", "to",
                       "as_of", "note", "blocks_carry", "where", "period"})
_NUM = re.compile(r"(?P<sign>[+\-−±])?\s?(?P<dollar>\$)?(?P<num>\d[\d,]*(?:\.\d+)?)\s?"
                  r"(?P<unit>%|bp\b|bps\b|pts\b|points\b|tn\b|bn\b|mn\b|m\b|k\b|x\b)?")
_SCALE = {"tn": 1e12, "bn": 1e9, "mn": 1e6, "m": 1e6, "k": 1e3}


def parse_figure(cell) -> Optional[tuple[float, str]]:
    """(value, unit) of a printed figure -- "+25 bp" (25, "bp"), "−$100bn"
    (-1e11, "$"), "+5.00%" (5, "%"), "4.25%" (4.25, "%"), "148.00" (148, "")
    -- or None for a cell that carries no figure ("—", "n/a", "none held")."""
    if cell is None or isinstance(cell, bool):
        return None
    if isinstance(cell, (int, float)):
        return float(cell), ""
    text = str(cell).strip()
    m = _NUM.search(text)
    if not m or not readability.figures(text):
        return None
    v = float(m.group("num").replace(",", ""))
    unit = (m.group("unit") or "").lower()
    if unit in _SCALE:
        v *= _SCALE[unit]
        unit = "$" if m.group("dollar") else ""
    elif m.group("dollar"):
        unit = "$"
    unit = {"bps": "bp", "points": "pts"}.get(unit, unit)
    if m.group("sign") in ("-", "−"):
        v = -v
    return v, unit


def _col(columns: list, rx: re.Pattern, skip: tuple = ()) -> Optional[int]:
    for i, c in enumerate(columns or []):
        if i not in skip and rx.search(str(c or "")):
            return i
    return None


def table_moves(table: Optional[dict], where: str,
                prefer: Optional[str] = None) -> list[dict]:
    """Every row of a table as a move: its name, the change cell exactly as
    printed, the level cell, and the magnitudes the two rankings use. The
    change column is the cadence's own period column (`prefer`: "Week", "The
    month") where the table has one -- the Weekly's tape also prints the
    session's move -- else the first change-like head. A table whose rows are
    sessions ("Session" first) carries no series and gives no moves."""
    out = []
    t = table or {}
    cols = list(t.get("columns") or [])
    rows = list(t.get("rows") or [])
    if not rows:
        return out
    # The name is the first text column; a leading rank column is skipped.
    name_i = 1 if cols and str(cols[0]).strip().lower() == "rank" else 0
    if cols and str(cols[name_i]).strip().lower() in ("session", "date", "day"):
        return out
    lvl = _col(cols, LEVEL_HEAD, (name_i,))
    chg = next((i for i, c in enumerate(cols) if prefer and i != name_i
                and str(c).strip().lower() == prefer.strip().lower()), None)
    if chg is None:
        chg = _col(cols, CHANGE_HEAD, (name_i,) + ((lvl,) if lvl is not None else ()))
    for k, r in enumerate(rows):
        r = list(r)
        name = str(r[name_i]) if len(r) > name_i else ""
        change = r[chg] if chg is not None and len(r) > chg else None
        level = r[lvl] if lvl is not None and len(r) > lvl else None
        c, lv = parse_figure(change), parse_figure(level)
        if c is None:
            # A LEVEL TABLE (the slow layers' valuation, a theme with no change
            # printed): the row offers its level, ranked after every move.
            if lv is not None:
                out.append({"name": name, "change": str(level), "kind": "level",
                            "where": where, "order": k, "relative": None,
                            "absolute": None})
            else:
                out.append({"name": name, "change": None, "where": where, "order": k})
            continue
        if c[1] == "%":
            rel = abs(c[0])                 # a percent move is already relative
        elif lv and lv[0]:
            # A basis-point move of a percent level is scaled to the level in bp.
            base = abs(lv[0]) * (100.0 if c[1] == "bp" and lv[1] == "%" else 1.0)
            rel = abs(c[0]) / base * 100.0
        else:
            rel = None
        out.append({"name": name, "change": str(change), "level": level, "kind": "move",
                    "where": where, "order": k, "relative": rel,
                    "absolute": abs(c[0])})
    return out


def section_moves(s: dict, prefer: Optional[str] = None) -> list[dict]:
    """The section's moves, from its own table and every sub-section's, in the
    payload's order; one entry per series name (the first table naming it)."""
    moves, seen = [], set()
    tables = [(s.get("title"), s.get("table"))] + \
        [(ss.get("title"), ss.get("table")) for ss in s.get("subsections") or []]
    for where, t in tables:
        for m in table_moves(t, str(where or ""), prefer):
            key = m["name"].strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            moves.append(m)
    return moves


def ranked(moves: list[dict], by: str = "relative") -> list[dict]:
    """Largest first by `by`; moves with no figure, or nothing to scale it by,
    after, in the payload's order."""
    have = [m for m in moves if m.get("change") is not None and m.get(by) is not None]
    rest = [m for m in moves if m not in have]
    return sorted(have, key=lambda m: -m[by]) + rest


def _figs(m: dict) -> int:
    return readability.figure_count(m.get("change"))


def cite(m: dict, where: bool = False) -> dict:
    """One figure as a frame offers it: the series and its move -- or, from a
    level table, its level -- exactly as the table prints it."""
    out = {"series": m["name"],
           ("level" if m.get("kind") == "level" else "change"): m["change"]}
    if where:
        out["where"] = m["where"]
    return out


def take(moves: list[dict], cap: int, by: str = "relative") -> tuple[list, list]:
    """(quantified, named): the ranked moves that fit `cap` figures, and the
    names of every other series."""
    got, used = [], 0
    for m in ranked(moves, by):
        n = _figs(m) if m.get("change") is not None else 0
        if n and used + n <= cap:
            got.append(m)
            used += n
    names = [m["name"] for m in moves if m not in got and m["name"]]
    return got, names


def scrub_percentiles(v):
    """No raw percentile in a frame: a key naming a percentile survives only as
    its `_ordinal`."""
    if isinstance(v, dict):
        return {k: scrub_percentiles(x) for k, x in v.items()
                if not ("percentile" in str(k).lower()
                        and not str(k).endswith("_ordinal"))}
    if isinstance(v, list):
        return [scrub_percentiles(x) for x in v]
    return v


BLOCKS_CARRY = ("The blocks beneath this section carry every other number: name a "
                "series under also_moved, never quantify it.")


def parent_frame(s: dict, ed: dict, cap: int, period: str,
                 column: Optional[str] = None,
                 levels: Optional[list] = None) -> dict:
    """A parent section's frame: its top moves up to `cap` figures, each with its
    display form, and every other series by name only. `column` is the
    cadence's period column head. `levels` (the tape's, T3.4b) are offered
    first and counted inside the same cap."""
    lv = list(levels or [])[:cap]
    got, names = take(section_moves(s, column), cap - len(lv))
    out = {"section": s["title"], "depth": s.get("depth"),
           "depth_reason": s.get("depth_reason"),
           "session": ed.get("session"), "month": ed.get("month"),
           "period": period,
           "figures_you_may_cite": [cite(m, where=True) for m in got],
           "also_moved": names,
           "blocks_carry": BLOCKS_CARRY}
    if lv:
        out["levels_you_may_cite"] = lv
    return out


# THE TAPE'S LEVELS (T3.4b, ruled 11 Oct 2026). The daily close's and the Weekly's
# tape name levels by rule (stack_prose.RULES: "a level is named by its label and
# value exactly as the data lists it"; "held" or "broke" only with its status), and
# T3.4 took the level list out of the frame. These come back, at most three, in
# this order -- the pin level first on an expiry session, then the 50-day, the
# dealer flip and the wall nearest the last price -- for the tape's first
# instrument (SPY), each with its status, inside the cadence's cap. The Monthly's
# tape is unchanged.
TAPE_LEVELS_MAX = 3


def is_expiry_session(day: Optional[str]) -> bool:
    """The monthly options expiry: the third Friday of the month."""
    import datetime as dt                                       # noqa: PLC0415
    try:
        d = dt.date.fromisoformat(str(day)[:10])
    except (TypeError, ValueError):
        return False
    return d.weekday() == 4 and 15 <= d.day <= 21


def tape_levels(s: dict, ed: dict, n: int = TAPE_LEVELS_MAX) -> list[dict]:
    """The tape's levels you may cite: label, value and status exactly as the
    level list carries them, with the level's field name beside its value so the
    label audit ties the figure to its level."""
    from altdata import levels as levels_mod                    # noqa: PLC0415
    data = s.get("data") or {}
    rows = data.get("levels") or []
    if not rows:
        return []
    row = rows[0]
    status = {x.get("label"): x.get("status")
              for x in (data.get("level_status") or {}).get(str(row.get("symbol", "")).lower()) or []}
    order = (["max_pain"] if is_expiry_session(ed.get("session")) else []) \
        + ["ma_50d", "gamma_flip"]
    last = row.get("last")
    walls = [w for w in ("call_wall", "put_wall") if isinstance(row.get(w), (int, float))]
    if walls and isinstance(last, (int, float)):
        order.append(min(walls, key=lambda w: abs(row[w] - last)))
    out = []
    for f in order:
        v = row.get(f)
        if not isinstance(v, (int, float)) or len(out) >= n:
            continue
        label = levels_mod.LABEL.get(f, f)
        if f == "max_pain":
            label = "max pain (the pin level on this expiry)"
        out.append({"market": row.get("name") or row.get("symbol"), "symbol": row.get("symbol"),
                    "level": label, f: v,
                    "status": status.get(levels_mod.LABEL.get(f, f))})
    return out


def is_parent(s: dict, parents) -> bool:
    return s.get("id") in set(parents or ()) and bool(s.get("subsections"))


def block_frame(s: dict, ss: dict, month: Optional[str], cap: int,
                column: Optional[str] = None) -> dict:
    """A block's frame: its table's rows ranked by absolute change, as many as
    fit `cap` figures with their level and change; the rest by name only. Each
    kept row carries the display fields of its data entry (`_signed`,
    `_display`, `_ordinal`), never a raw number beside them."""
    t = ss.get("table") or {}
    cols = list(t.get("columns") or [])
    moves = table_moves(t, str(ss.get("title") or ""), column)
    by_name = {str(r[1] if cols and str(cols[0]).lower() == "rank" else r[0]): list(r)
               for r in t.get("rows") or [] if r}
    entries = _data_entries(ss.get("data"))
    rows, used, kept = [], 0, set()
    for m in ranked(moves, "absolute"):
        if m.get("change") is None:
            continue
        row = by_name.get(m["name"]) or []
        cells = {str(c): v for c, v in zip(cols, row)}
        disp = {k: v for k, v in (entries.get(m["name"].strip().lower()) or {}).items()
                if str(k).endswith(("_signed", "_display", "_ordinal"))}
        rec = {"series": m["name"], **{k: v for k, v in cells.items()
                                       if v != m["name"]}, **disp}
        n = quantified_figures(rec)
        if used + n > cap:
            continue
        rows.append(rec)
        used += n
        kept.add(m["name"])
    named = [m["name"] for m in moves if m["name"] not in kept and m["name"]]
    return {"section": s["title"], "block": ss.get("title"), "month": month,
            "rows": rows, "also_moved": named,
            "note": ("The table above prints every row; cite only these rows' "
                     "figures and name the others without a number.")
            if named else None,
            "lines": [ln for ln in ss.get("lines") or []
                      if not readability.figures(str(ln))] or None}


def _data_entries(data) -> dict:
    """A block's data rows keyed by their series name, wherever they sit."""
    out = {}

    def walk(o):
        if isinstance(o, dict):
            name = o.get("series") or o.get("label") or o.get("market") \
                or o.get("contract") or o.get("item")
            if name:
                out.setdefault(str(name).strip().lower(), o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(data)
    return out


def mask_figures(text: Optional[str]) -> Optional[str]:
    """The section's prose with its figures replaced, for a summary frame: the
    summary carries the reading and cites only the figures it is handed."""
    if not text:
        return text
    keep = []
    t = text
    # A name that carries digits ("the 10-year") is held aside as one private-use
    # character -- a placeholder with no digit for the figure pattern to find.
    for rx in readability._NOT_FIGURES:                       # noqa: SLF001
        t = rx.sub(lambda m: (keep.append(m.group(0)) or chr(0xE000 + len(keep) - 1)), t)
    t = readability._FIG.sub("[figure]", t)                   # noqa: SLF001
    return re.sub("[-]", lambda m: keep[ord(m.group(0)) - 0xE000], t)


def summary_frame(s: dict, n: int, column: Optional[str] = None) -> dict:
    """A summary paragraph's frame: the section's prose (figures masked) and
    the `n` figures it may cite -- the section's top moves, ranked as the
    parent's are."""
    got, _ = take(section_moves(s, column), n)
    subs = [{"title": ss.get("title"),
             "paragraphs": [mask_figures(p) for p in ss.get("paragraphs") or []]}
            for ss in s.get("subsections") or [] if ss.get("paragraphs")]
    return {"section": s["title"], "claim": mask_figures(s.get("claim")),
            "paragraphs": [mask_figures(p) for p in s.get("paragraphs") or []],
            "subsections": subs,
            "figures_you_may_cite": [cite(m) for m in got]}


def quantified_figures(frame) -> int:
    """The distinct figures a frame offers outside its names and dates: what
    the gate holds to the cap."""
    found: set = set()

    def walk(o, key=None):
        if key in NAME_KEYS:
            return
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, key)
        elif isinstance(o, bool) or o is None:
            return
        elif isinstance(o, (int, float)):
            found.add(f"{o:g}")
        else:
            for f in readability.figures(str(o)):
                found.add(f.replace("−", "-"))
    walk(frame)
    return len(found)
