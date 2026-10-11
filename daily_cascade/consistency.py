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
