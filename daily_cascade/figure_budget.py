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

THE SECOND PASS (W-1.1 item 1.0, T3.4c, ruled 11 Oct 2026):
  RANKING BY z. Relative-to-level favoured low-level series (IG OAS -4 bp
    outranked CCC OAS +37 bp). Where the section's data carries `_move_z` -- the
    z of each row's change against its own trailing-year changes
    (derived.period_change_z, the Weekly computes it) -- moves rank by |z|; a
    row whose series has fewer than 60 such changes ranks after them, relative
    to its level, and the frame names it under `ranking`.
  ALLOCATION. A section declared under `figure_budget_sections.<cadence>` takes
    that cap (the Weekly's Plumbing, Positioning and What's priced: 8) and, with
    `per_block`, one figure for every sub-block that moved before the rest go to
    the largest z.
  NO FILLER. The names the frame does not quantify sit under the heading "In the
    tables (do not enumerate)"; the prose rule and the filler audit
    (filler_faults) refuse "X, Y and Z also moved".
  THE FOUR OTHER FRAMES. The read, Mechanics, What doesn't fit and Ahead each get
    a budgeted frame of their own (read_frame, mechanics_frame, misfit_frame,
    ahead_frame) with a "move" defined for each.
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
IN_TABLES = "In the tables (do not enumerate)"
NAME_KEYS = frozenset({"section", "block", "series", "name", "title", "also_moved",
                       IN_TABLES, "ranking", "sub_block", "family", "outcomes",
                       "event", "date", "connector_rule", "flagged_sessions",
                       "depth", "depth_reason", "session", "month", "from", "to",
                       "as_of", "note", "blocks_carry", "where", "period",
                       "columns"})
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
                prefer: Optional[str] = None,
                zmap: Optional[dict] = None) -> list[dict]:
    """Every row of a table as a move: its name, the change cell exactly as
    printed, the level cell, and the magnitudes the two rankings use. The
    change column is the cadence's own period column (`prefer`: "Week", "The
    month") where the table has one -- the Weekly's tape also prints the
    session's move -- else the first change-like head. A table whose rows are
    sessions ("Session" first) carries no series and gives no moves. `zmap`
    ({name, lower case: {z, reason}}) attaches each row's z (T3.4c)."""
    out = []
    zmap = zmap or {}
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
        zz = zmap.get(name.strip().lower()) or {}
        out.append({"name": name, "change": str(change), "level": level, "kind": "move",
                    "where": where, "order": k, "relative": rel,
                    "absolute": abs(c[0]), "moved": c[0] != 0,
                    "z": (abs(zz["z"]) if isinstance(zz.get("z"), (int, float))
                          else None),
                    "z_reason": zz.get("reason")})
    return out


def section_moves(s: dict, prefer: Optional[str] = None) -> list[dict]:
    """The section's moves, from its own table and every sub-section's, in the
    payload's order; one entry per series name (the first table naming it).
    Each carries its `sub_block`: the row's own (`_row_block` in the section's
    data -- Plumbing's buckets) or else the table it sits in."""
    moves, seen = [], set()
    data = s.get("data") or {}
    zmap = data.get("_move_z") or {}
    blocks = data.get("_row_block") or {}
    tables = [(s.get("title"), s.get("table"))] + \
        [(ss.get("title"), ss.get("table")) for ss in s.get("subsections") or []]
    for where, t in tables:
        for m in table_moves(t, str(where or ""), prefer, zmap):
            key = m["name"].strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            m["sub_block"] = blocks.get(key) or m["where"]
            moves.append(m)
    return moves


def ranked(moves: list[dict], by: str = "relative") -> list[dict]:
    """Largest first by `by`; moves with no figure, or nothing to scale it by,
    after, in the payload's order. By "z" (T3.4c): moves with a z by |z|, then
    those without one relative to their level, then the rest."""
    if by == "z":
        zs = [m for m in moves if m.get("change") is not None and m.get("z") is not None]
        rel = ranked([m for m in moves if m not in zs], "relative")
        return sorted(zs, key=lambda m: -m["z"]) + rel
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


def take(moves: list[dict], cap: int, by: str = "relative",
         per_block: bool = False) -> tuple[list, list]:
    """(quantified, named): the ranked moves that fit `cap` figures, and the
    names of every other series. `per_block` (T3.4c): first the top move of
    every sub-block that moved, in rank order, then the rest by rank."""
    order = ranked(moves, by)
    got, used = [], 0

    def add(m) -> None:
        nonlocal used
        n = _figs(m) if m.get("change") is not None else 0
        if n and m not in got and used + n <= cap:
            got.append(m)
            used += n
    if per_block:
        firsts: dict = {}
        for m in order:
            if m.get("kind") == "move" and m.get("moved"):
                firsts.setdefault(m.get("sub_block") or m.get("where"), m)
        for m in order:
            if firsts.get(m.get("sub_block") or m.get("where")) is m:
                add(m)
    for m in order:
        add(m)
    got.sort(key=order.index)
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


BLOCKS_CARRY = ("The tables beneath this section print every other number. The "
                "series under 'In the tables (do not enumerate)' are there for "
                "reference: never list them, never quantify them, and never write "
                "that they also moved, all moved or moved alongside.")


def ranking_note(moves: list[dict]) -> Optional[str]:
    """The frame's word on how its moves were ranked (T3.4c): by z, and which
    series fell back to relative-to-level for want of history."""
    if not any(m.get("z") is not None for m in moves):
        return None
    rel = [m["name"] for m in moves if m.get("z") is None and m.get("kind") == "move"
           and m.get("change") is not None]
    return ("Ranked by how unusual each move is against its own series' "
            "trailing-year changes of the same length"
            + (f"; ranked relative to its level, for want of 60 such changes: "
               f"{', '.join(rel)}" if rel else "") + ".")


def section_cap(sid: Optional[str], cadence_cfg: dict, cfg: Optional[dict] = None
                ) -> tuple[int, bool]:
    """(cap, per_block) for one section at a cadence: its override under
    `figure_budget_sections.<cadence>` (T3.4c), else the cadence's
    `paragraph_figures` with no per-block rule."""
    if cfg is None:
        from altdata import bars as bars_mod                    # noqa: PLC0415
        cfg = bars_mod.load_config()
    over = (((cfg.get("figure_budget_sections") or {})
             .get(cadence_cfg.get("name") or "") or {}).get(sid or "") or {})
    base = int(cadence_cfg.get("paragraph_figures") or 6)
    return int(over.get("cap") or base), bool(over.get("per_block"))


def parent_frame(s: dict, ed: dict, cap: int, period: str,
                 column: Optional[str] = None,
                 levels: Optional[list] = None,
                 per_block: bool = False) -> dict:
    """A parent section's frame: its top moves up to `cap` figures, each with its
    display form, and every other series by name only, under IN_TABLES.
    `column` is the cadence's period column head. `levels` (the tape's, T3.4b)
    are offered first and counted inside the same cap. Moves rank by z where
    the section carries one (T3.4c); `per_block` gives every sub-block that
    moved one figure before the rest."""
    lv = list(levels or [])[:cap]
    moves = section_moves(s, column)
    by = "z" if any(m.get("z") is not None for m in moves) else "relative"
    got, names = take(moves, cap - len(lv), by, per_block)
    out = {"section": s["title"], "depth": s.get("depth"),
           "depth_reason": s.get("depth_reason"),
           "session": ed.get("session"), "month": ed.get("month"),
           "period": period,
           "figures_you_may_cite": [cite(m, where=True) for m in got],
           IN_TABLES: names,
           "blocks_carry": BLOCKS_CARRY}
    note = ranking_note(moves)
    if note:
        out["ranking"] = note
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
    moves = table_moves(t, str(ss.get("title") or ""), column,
                        (s.get("data") or {}).get("_move_z"))
    by_name = {str(r[1] if cols and str(cols[0]).lower() == "rank" else r[0]): list(r)
               for r in t.get("rows") or [] if r}
    entries = _data_entries(ss.get("data"))
    rows, used, kept = [], 0, set()
    # T3.5: by z where the section carries one (the Weekly parents' T3.4c rule),
    # else by absolute change as before.
    by = "z" if any(m.get("z") is not None for m in moves) else "absolute"
    for m in ranked(moves, by):
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
    # THE WEEKLY PARENTS' TREATMENT, FOR THE MONTHLY'S BLOCKS (T3.5 (b); W-1.1
    # item 1.0): the rows the paragraph may cite under `figures_you_may_cite`;
    # the table with every other row's figures masked, so the writer sees the
    # block as the reader does and has no other figure to copy; those rows' names
    # under IN_TABLES. The column heads travel too -- "20-day change" is how the
    # writer names a column, and its "20" is the table's own.
    name_i = 1 if cols and str(cols[0]).strip().lower() == "rank" else 0
    masked = [[c if i == name_i or str(r[name_i] if len(r) > name_i else "") in kept
               or not readability.figures(str(c)) else MASKED
               for i, c in enumerate(r)] for r in (t.get("rows") or []) if r]
    return {"section": s["title"], "block": ss.get("title"), "month": month,
            "columns": cols,
            "table": {"columns": cols, "rows": masked},
            "figures_you_may_cite": rows, IN_TABLES: named,
            "note": BLOCK_NOTE if named else None,
            "lines": [ln for ln in ss.get("lines") or []
                      if not readability.figures(str(ln))] or None}


MASKED = "[in the table]"
BLOCK_NOTE = ("The table above prints every row. Cite only the figures under "
              "figures_you_may_cite, exactly as printed there; the rows marked "
              f"'{MASKED}' are for the reader, never for this paragraph: do not "
              "list them, quantify them, or say they also moved.")


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
            if isinstance(o.get("rows"), list) and "columns" in o:
                # A TABLE's name column is a name (T3.5): "CPI above 3% in
                # October" offers no figure, as it would not under "series".
                cols = list(o.get("columns") or [])
                ni = 1 if cols and str(cols[0]).strip().lower() == "rank" else 0
                for k, v in o.items():
                    if k != "rows":
                        walk(v, k)
                for r in o["rows"]:
                    walk([c for i, c in enumerate(r or []) if i != ni]
                         if isinstance(r, (list, tuple)) else r, "rows")
                return
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


# ===========================================================================
# THE FOUR OTHER FRAMES (W-1.1 item 1.0a, ruled 11 Oct 2026)
# ===========================================================================
# The 9 Oct Weekly's dry run cited 15 figures in The read, 12 in Mechanics and 7
# each in What doesn't fit and Ahead, against six: those sections' writers were
# handed their whole data. Each now gets a frame like a parent's -- the figures it
# may cite, up to its cap, each exactly as its table prints it, and the rest by
# name under IN_TABLES -- with a "move" defined for each section:
#   read       the five lines' figures: the top move of each section that has
#              one, then the week's largest SPY session, then the rest by z
#   mechanics  the daily move priced and realized; per-session range against
#              implied (actual / implied, largest first); the VIX, realized, SKEW
#              and MOVE week changes by z; the flip's move. Gamma-regime changes
#              and the flags are named, never quantified
#   misfit     gaps by |z|, extremes by their percentile's distance from the
#              median (as the z it corresponds to), prediction-market
#              disagreements by twice their gap over the threshold
#   ahead      the next FOMC date and its pricing, the graded-calls line, the
#              top-importance events' consensus or prior; a family of resolution
#              contracts (the 18 Core CPI rows) is ONE figure, its modal outcome,
#              and the rest by name
def _cands_take(cands: list[dict], cap: int) -> tuple[list, list]:
    """Candidates in priority order, each {"cite": {...}, "name": ...}: as many
    as fit `cap` figures; the names of the rest."""
    got, used, rest = [], 0, []
    for c in cands:
        n = quantified_figures(c["cite"])
        if n and used + n <= cap:
            got.append(c["cite"])
            used += n
        elif c.get("name"):
            rest.append(c["name"])
    return got, list(dict.fromkeys(rest))


def _frame(s: dict, ed: dict, period: str, got: list, names: list, **extra) -> dict:
    out = {"section": s.get("title"), "depth": s.get("depth"),
           "session": ed.get("session"), "period": period,
           "figures_you_may_cite": got, IN_TABLES: names}
    out.update({k: v for k, v in extra.items() if v not in (None, [], {})})
    return out


def _rows(t: Optional[dict]) -> tuple[list, list]:
    t = t or {}
    return list(t.get("columns") or []), [list(r) for r in t.get("rows") or []]


def _cell(cols: list, row: list, head: str) -> Optional[str]:
    for i, c in enumerate(cols):
        if str(c).strip().lower() == head.lower() and i < len(row):
            v = row[i]
            return None if v in (None, "—", "") else str(v)
    return None


def _plain_items(s: dict) -> list[str]:
    """The section's shown items that carry no figure: context, never a cite."""
    return [i["text"] for i in s.get("items") or []
            if i.get("show", True) and not readability.figures(i["text"])]


def mechanics_frame(s: dict, ed: dict, cap: int, period: str) -> dict:
    """Mechanics' frame (see above)."""
    data = s.get("data") or {}
    zmap = data.get("_move_z") or {}
    cands: list[dict] = []
    vol = next((ss for ss in s.get("subsections") or []
                if ss.get("title") == "Volatility"), None)
    vcols, vrows = _rows((vol or {}).get("table"))
    for r in vrows:
        if str(r[0]).startswith("Daily move priced"):
            cands.append({"cite": {"series": r[0], "priced": r[1], "realized": r[2]},
                          "name": r[0]})
    rng = next((ss for ss in s.get("subsections") or []
                if ss.get("title") == "Ranges and flags"), None)
    rcols, rrows = _rows((rng or {}).get("table"))
    scored = []
    for r in rrows:
        imp = parse_figure(_cell(rcols, r, "Implied range"))
        act = parse_figure(_cell(rcols, r, "Actual range"))
        if imp and act and imp[0]:
            scored.append((act[0] / imp[0], r))
    scored.sort(key=lambda x: -x[0])
    for _, r in scored[:2]:
        cands.append({"cite": {"series": f"SPY range, {r[0]}",
                               "implied_range": _cell(rcols, r, "Implied range"),
                               "actual_range": _cell(rcols, r, "Actual range")},
                      "name": f"SPY range, {r[0]}"})
    vchg = []
    for r in vrows:
        ch = _cell(vcols, r, "Week")
        if ch and parse_figure(ch):
            z = (zmap.get(str(r[0]).strip().lower()) or {}).get("z")
            vchg.append((abs(z) if isinstance(z, (int, float)) else -1.0,
                         {"cite": {"series": r[0], "level": r[1], "change": ch},
                          "name": r[0]}))
    cands += [c for _, c in sorted(vchg, key=lambda x: -x[0])]
    pcols, prows = _rows(s.get("table"))
    flips = [(r[0], _cell(pcols, r, "Flip")) for r in prows if _cell(pcols, r, "Flip")]
    if len(flips) >= 2:
        cands.append({"cite": {"series": "SPY gamma flip, first and last session",
                               "first_session": flips[0][1],
                               "last_session": flips[-1][1]},
                      "name": "SPY gamma flip"})
    got, names = _cands_take(cands, cap)
    regimes, prev = [], None
    for r in prows:
        g = _cell(pcols, r, "Gamma regime")
        if g and prev and g != prev:
            regimes.append({"session": r[0], "from": prev, "to": g})
        prev = g or prev
    flagged = [{"session": r[0], "flags": _cell(rcols, r, "Flags")} for r in rrows
               if (_cell(rcols, r, "Flags") or "none") != "none"]
    return _frame(s, ed, period, got, names, gamma_regime_changes=regimes,
                  flagged_sessions=flagged, items=_plain_items(s))


def _pct_z(p) -> Optional[float]:
    """A percentile as the |z| it corresponds to under a normal: 98th -> 2.05."""
    import statistics                                           # noqa: PLC0415
    if not isinstance(p, (int, float)):
        return None
    q = min(max(float(p) / 100.0, 0.001), 0.999)
    return abs(statistics.NormalDist().inv_cdf(q))


def misfit_frame(s: dict, ed: dict, cap: int, period: str) -> dict:
    """What doesn't fit's frame (see above). A gap cites its z and its age in
    sessions -- the gap's age, never the exception's (item 1.3); its sides and
    what would close it are words."""
    data = s.get("data") or {}
    scored = []
    for g in data.get("gaps") or []:
        if isinstance(g.get("z"), (int, float)):
            scored.append((abs(g["z"]), {
                "cite": {"series": g.get("gap"), "z": f"{g['z']:+.1f}",
                         "gap_open_sessions": g.get("sessions_open"),
                         "sides": g.get("sides"), "closes_when": g.get("closes_when")},
                "name": g.get("gap")}))
    for e in data.get("extremes") or []:
        z = _pct_z(e.get("percentile"))
        if z is not None:
            scored.append((z, {"cite": {"series": e.get("name"),
                                        "percentile": e.get("percentile_ordinal"),
                                        "side": e.get("side")},
                               "name": e.get("name")}))
    for d in ((data.get("venue_disagreements") or {}).get("fed_funds") or []):
        th = float(d.get("threshold_points") or 15)
        scored.append((2.0 * abs(d.get("gap_points") or 0) / th, {
            "cite": {"series": f"{str(d.get('venue')).title()}, FOMC {d.get('meeting')}, "
                               f"{d.get('side')}",
                     "prediction_market": f"{round(d['venue_probability'] * 100):.0f}%",
                     "fed_funds_futures": f"{round(d['fed_funds_implied'] * 100):.0f}%"},
            "name": f"FOMC {d.get('meeting')} {d.get('side')}"}))
    scored.sort(key=lambda x: -x[0])
    got, names = _cands_take([c for _, c in scored], cap)
    cited = {g.get("series") for g in got}
    for n in data.get("exceptions_open_now") or []:
        if n not in names and n not in cited:
            names.append(n)
    return _frame(s, ed, period, got, names, items=_plain_items(s))


# A resolution contract's question with its strikes struck: the family key ("Will
# Core CPI rise more than 0.3%?" and "... 0.2% ..." are one family).
_STRIKE = re.compile(r"[+\-−]?\$?\d[\d,]*(?:\.\d+)?\s?(?:%|bp|bps)?")


def contract_family(question: str) -> str:
    return re.sub(r"\s+", " ", _STRIKE.sub("#", str(question or ""))).strip()


def ahead_frame(s: dict, ed: dict, cap: int, period: str) -> dict:
    """Ahead's frame (see above)."""
    data = s.get("data") or {}
    cands: list[dict] = []
    priced = next((x for x in ed.get("sections") or [] if x.get("id") == "priced"), {})
    for ss in [priced] + list(priced.get("subsections") or []):
        cols, rows = _rows(ss.get("table"))
        fomc = next((r for r in rows if str(r[0]).startswith("FOMC ")
                     and "implied rate" in str(r[0])), None)
        if fomc:
            cands.append({"cite": {"series": fomc[0], "level": fomc[1],
                                   "priced": fomc[2], "where": "What's priced"},
                          "name": fomc[0]})
            break
    gc = (data.get("graded_calls") or {}).get("rows") or []
    for r in sorted(gc, key=lambda r: -(r.get("n") or 0))[:1]:
        cands.append({"cite": {"series": f"graded calls, {r.get('source')}",
                               "resolved": r.get("n"),
                               "mean_brier": f"{r['mean_brier']:.3f}"},
                      "name": f"graded calls, {r.get('source')}"})
    fams: dict[str, list] = {}
    plain = []
    for r in data.get("calendar") or []:
        ev = str(r.get("event") or "")
        if ev.startswith("Prediction market resolves:"):
            fams.setdefault(contract_family(ev), []).append(r)
        else:
            plain.append(r)
    named_only = []
    for r in sorted(plain, key=lambda r: (r.get("tier") or 9, r.get("date") or "")):
        if (r.get("tier") or 9) > 1:
            continue
        con = r.get("consensus")
        if con and readability.figures(str(con)):
            cands.append({"cite": {"series": r.get("event"), "date": r.get("date"),
                                   "consensus_or_prior": con},
                          "name": r.get("event")})
        else:
            named_only.append({"event": r.get("event"), "date": r.get("date")})
    families = []

    def prob(r) -> float:
        f = parse_figure(r.get("consensus"))
        return f[0] if f else -1.0
    for key, rows in fams.items():
        modal = max(rows, key=prob)
        cands.append({"cite": {"series": modal.get("event"),
                               "modal_outcome": modal.get("consensus")},
                      "name": key})
        if len(rows) > 1:
            families.append({"family": key, "outcomes": len(rows)})
    got, names = _cands_take(cands, cap)
    return _frame(s, ed, period, got, names, contract_families=families,
                  tier1_events_without_a_figure=named_only,
                  watching=[w for w in data.get("watching") or []
                            if not readability.figures(str(w))])


# The sections the read draws its figures from, in the edition's order.
READ_SOURCES = ("tape", "mechanics", "misfit", "plumbing", "positioning", "priced")


def read_frame(ed: dict, cap: int, period: str) -> dict:
    """The read's frame: each section's claim with its figures masked; the
    figures it may cite -- the top move of each section in turn, the week's
    largest SPY session, then the rest by z; the press's attributions with
    their figures masked (they are the outlet's words, never ours)."""
    secs = {s["id"]: s for s in ed.get("sections") or []}
    per: list[list] = []
    for sid in READ_SOURCES:
        s = secs.get(sid)
        if not s or s.get("empty"):
            continue
        if sid in FRAMES:
            fr = FRAMES[sid](s, ed, cap, period)
            per.append([{"cite": {**c, "where": s["title"]}, "name": c.get("series"),
                         "z": None} for c in fr["figures_you_may_cite"]
                        if quantified_figures(c)])
            continue
        moves = section_moves(s, "Week")
        by = "z" if any(m.get("z") is not None for m in moves) else "relative"
        got, _ = take(moves, cap, by)
        per.append([{"cite": cite(m, where=True), "name": m["name"], "z": m.get("z")}
                    for m in got])
    read = secs.get("read") or {}
    cols, rows = _rows(read.get("table"))
    best = None
    for r in rows:
        f = parse_figure(_cell(cols, r, "SPY"))
        if f and (best is None or abs(f[0]) > best[0]):
            best = (abs(f[0]), r)
    first = [lst[0] for lst in per if lst]
    rest = sorted([c for lst in per for c in lst[1:]], key=lambda c: -(c.get("z") or 0))
    spy = ([{"cite": {"series": f"SPY, {best[1][0]}", "change": _cell(cols, best[1], "SPY"),
                      "where": "The week by day"}, "name": f"SPY, {best[1][0]}"}]
           if best else [])
    got, names = _cands_take(first + spy + rest, cap)
    return {"session": ed.get("session"), "period": period,
            "sections": [{"section": s["title"], "claim": mask_figures(s.get("claim"))}
                         for s in ed.get("sections") or []
                         if s["id"] != "read" and s.get("claim")],
            "figures_you_may_cite": got, IN_TABLES: names,
            "press_attributions": [mask_figures(re.sub(r"\s*\(https?://[^)]*\)", "",
                                                       i["text"]))
                                   for i in read.get("items") or []
                                   if str(i.get("key", "")).startswith("read:attr")]}


FRAMES = {"mechanics": mechanics_frame, "misfit": misfit_frame,
          "ahead": ahead_frame}
