"""
THE CROSS-TABLE CONSISTENCY GATE (W-1.1 item 1.1, ruled 11 Oct 2026).

    from daily_cascade import consistency
    log = consistency.reconcile(ed)      # fixes rounding, raises beyond it
    consistency.check(ed)                # the same, report-only

The report identifies and explains its own inconsistencies; a reader never has
to. The 9 Oct Weekly printed SPY's week as +1.16% in the tape and +1.17% in the
overnight/cash split: two tables, one fact, two conventions (close to close,
against overnight and cash legs compounded after rounding).

A FACT IS KEYED BY (series, as-of, measure). A builder that prints a figure it
knows another table also prints tags the cell -- a table's `facts`, one entry
per cell: {"row", "col", "key", "canonical"}. This module reads the edition only
(the rendered payload), groups the tagged cells by key and compares them at
printed precision:

  IDENTICAL                         nothing to do
  WITHIN ROUNDING TOLERANCE         every cell prints the canonical one -- the
                                    cell tagged `canonical`, else the first in
                                    edition order -- and the difference is logged
                                    with each cell's source (ruling 1)
  BEYOND TOLERANCE                  EditionInconsistent: the run fails (ruling 1)

Tolerance is one unit in the last decimal the coarser of the two cells prints
(+1.16% against +1.17%: 0.01); a cell that does not parse as a figure is never
compared. The log rides on the edition as `consistency` so the archive keeps it.
"""

from __future__ import annotations

from typing import Optional

from . import figure_budget as fb


class EditionInconsistent(RuntimeError):
    """A fact printed in two places differs beyond rounding."""

    def __init__(self, mismatches: list[dict]):
        self.mismatches = mismatches
        super().__init__("; ".join(
            f"{m['key']}: " + " against ".join(f"{c['printed']} ({c['where']})"
                                               for c in m["cells"])
            for m in mismatches))


def _decimals(text: str) -> int:
    import re                                                   # noqa: PLC0415
    m = re.search(r"\d[\d,]*\.(\d+)", str(text))
    return len(m.group(1)) if m else 0


def _tables(ed: dict):
    """(where, table) for every table the edition prints, in order."""
    for s in ed.get("sections") or []:
        if s.get("table"):
            yield s.get("title") or s.get("id"), s["table"]
        for ss in s.get("subsections") or []:
            if ss.get("table"):
                yield f"{s.get('title')} / {ss.get('title')}", ss["table"]


def collect(ed: dict) -> dict[str, list[dict]]:
    """{fact key: [cell, ...]} -- each cell {where, table, row, col, printed,
    value, canonical}."""
    out: dict[str, list[dict]] = {}
    for where, t in _tables(ed):
        rows = t.get("rows") or []
        for f in t.get("facts") or []:
            r, c = f.get("row"), f.get("col")
            if r is None or c is None or r >= len(rows) or c >= len(rows[r]):
                continue
            printed = rows[r][c]
            got = fb.parse_figure(printed)
            if got is None:
                continue
            out.setdefault(str(f["key"]), []).append(
                {"where": where, "table": t, "row": r, "col": c,
                 "printed": str(printed), "value": got[0], "unit": got[1],
                 "canonical": bool(f.get("canonical"))})
    return out


def compare(cells: list[dict]) -> tuple[str, Optional[dict]]:
    """("same" | "rounding" | "beyond", the canonical cell)."""
    canon = next((c for c in cells if c["canonical"]), cells[0])
    if all(c["printed"] == canon["printed"] for c in cells):
        return "same", canon
    if len({c["unit"] for c in cells}) > 1:
        return "beyond", canon
    tol = 10.0 ** -min(_decimals(c["printed"]) for c in cells)
    spread = max(c["value"] for c in cells) - min(c["value"] for c in cells)
    return ("rounding" if spread <= tol + 1e-9 else "beyond"), canon


def reconcile(ed: dict, fix: bool = True, fail: bool = True) -> list[dict]:
    """Compare every fact printed more than once. Within rounding, every cell
    prints the canonical value (when `fix`) and the difference is logged;
    beyond it, EditionInconsistent (when `fail`). Returns the log, also kept as
    `ed["consistency"]`."""
    log, bad = [], []
    for key, cells in collect(ed).items():
        if len(cells) < 2:
            continue
        verdict, canon = compare(cells)
        if verdict == "same":
            continue
        entry = {"key": key, "verdict": verdict, "canonical": canon["printed"],
                 "canonical_where": canon["where"],
                 "cells": [{"where": c["where"], "printed": c["printed"]}
                           for c in cells]}
        if verdict == "rounding" and fix:
            for c in cells:
                c["table"]["rows"][c["row"]][c["col"]] = canon["printed"]
            entry["fixed"] = True
        log.append(entry)
        if verdict == "beyond":
            bad.append(entry)
    ed["consistency"] = log
    if bad and fail:
        raise EditionInconsistent(bad)
    return log


# ONE INSTRUMENT, SEVERAL SERIES IDS (W-1.1a item 6, the Weekly dry run of 12
# Oct). The tape printed the 10-year at 5.244% (the 5-minute feed's ^TNX, 9 Oct)
# and Plumbing's chart caption 5.28% (FRED's DGS10, 7 Oct): one instrument, two
# series, two dates, and nothing told the reader which was which. Each instrument
# names the series ids that print it. At ONE date the figures must agree within
# the gate's tolerance (one unit in the coarser figure's last decimal), else the
# run fails; at DIFFERENT dates they are not compared, and a chart caption must
# carry its source and date ("10-year 5.28% (FRED, 7 Oct)").
ALIASES: dict[str, tuple[str, ...]] = {
    "y2": ("y2", "fred.yield_2y"),
    "y10": ("y10", "yfinance.mkt_tnx", "fred.yield_10y"),
    "y30": ("y30", "yfinance.mkt_tyx", "fred.yield_30y"),
    "hy_oas": ("hy_oas", "fred.hy_oas"),
}


# THE TOLERANCE BETWEEN TWO SERIES OF ONE INSTRUMENT, in the level's own unit
# (percentage points). Two series of one instrument are two measurements -- the
# CBOE's ^TNX at its close, FRED's constant-maturity DGS10 from the Fed's H.15 --
# and on one date they differ by a basis point or two without either being
# wrong; one unit of the printed precision would fail the run on that. Three
# basis points is the line: a 4 bp gap fails (the W-1.1a fixture).
ALIAS_TOLERANCE: dict[str, float] = {"y2": 0.03, "y10": 0.03, "y30": 0.03,
                                     "hy_oas": 0.03}


def instrument_of(series: str) -> Optional[str]:
    s = str(series or "")
    return next((i for i, ids in ALIASES.items() if s in ids), None)


def level_cells(ed: dict, charts: Optional[dict] = None) -> list[dict]:
    """Every level the edition prints for an aliased instrument: the tables'
    tagged `level` facts and the charts' declared `levels`."""
    out = []
    for key, cells in collect(ed).items():
        series, as_of, measure = (key.split("|") + ["", ""])[:3]
        inst = instrument_of(series)
        if measure != "level" or not inst:
            continue
        for c in cells:
            out.append({"instrument": inst, "series": series, "as_of": as_of,
                        "value": c["value"], "printed": c["printed"],
                        "where": c["where"], "caption": None})
    for cid, ch in (charts or {}).items():
        for lv in ch.get("levels") or []:
            inst = instrument_of(lv.get("series"))
            if not inst:
                continue
            out.append({"instrument": inst, "series": lv["series"],
                        "as_of": str(lv.get("as_of") or "")[:10],
                        "value": float(lv["value"]), "printed": str(lv["printed"]),
                        "where": f"chart {cid}", "caption": ch.get("caption") or "",
                        "source": lv.get("source")})
    return out


def reconcile_aliases(ed: dict, charts: Optional[dict] = None,
                      fail: bool = True) -> list[dict]:
    """Compare one instrument's levels across its series ids: at one date
    within tolerance, else EditionInconsistent (when `fail`); at different dates
    not compared, and a chart's caption must name its source and date. The log
    is added to `ed["consistency"]`."""
    log, bad = [], []
    cells = level_cells(ed, charts)
    for inst in sorted({c["instrument"] for c in cells}):
        mine = [c for c in cells if c["instrument"] == inst]
        for c in mine:
            if c["caption"] is not None and c["as_of"] and not (
                    c.get("source") and f"({c['source']}, " in c["caption"]):
                e = {"key": f"{inst}|{c['as_of']}|level", "verdict": "undated",
                     "cells": [{"where": c["where"], "printed": c["printed"]}],
                     "note": "a chart caption must carry its source and date"}
                log.append(e)
                bad.append(e)
        for day in sorted({c["as_of"] for c in mine}):
            same = [c for c in mine if c["as_of"] == day]
            if len({c["series"] for c in same}) < 2:
                continue
            tol = max(10.0 ** -min(_decimals(c["printed"]) for c in same),
                      ALIAS_TOLERANCE.get(inst, 0.0))
            spread = max(c["value"] for c in same) - min(c["value"] for c in same)
            verdict = "rounding" if spread <= tol + 1e-9 else "beyond"
            if spread == 0:
                continue
            e = {"key": f"{inst}|{day}|level", "verdict": verdict,
                 "cells": [{"where": c["where"], "printed": c["printed"]} for c in same]}
            log.append(e)
            if verdict == "beyond":
                bad.append(e)
        days = sorted({c["as_of"] for c in mine})
        if len(days) > 1:
            log.append({"key": f"{inst}|level", "verdict": "different dates",
                        "note": "not compared; each prints its own date",
                        "cells": [{"where": c["where"], "printed": c["printed"],
                                   "as_of": c["as_of"]} for c in mine]})
    ed["consistency"] = list(ed.get("consistency") or []) + log
    if bad and fail:
        raise EditionInconsistent(bad)
    return log


def check(ed: dict) -> list[dict]:
    """Report-only: the log, nothing rewritten, nothing raised."""
    return reconcile(ed, fix=False, fail=False)


def tag(table: Optional[dict], row: int, col: int, key: str,
        canonical: bool = False) -> None:
    """Tag one cell of a table as a fact."""
    if table is None:
        return
    table.setdefault("facts", []).append({"row": row, "col": col, "key": key,
                                          "canonical": canonical})


def fact_key(series: str, as_of: Optional[str], measure: str) -> str:
    return f"{series}|{str(as_of or '')[:10]}|{measure}"
