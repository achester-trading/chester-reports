"""
The EM vulnerability scorecard: a table of lenses, never a composite. (AQ-9a)

    python -m altdata.em_scorecard [--as-of 2026-10-11]   # the table, to stdout

Change order "Alternative Assets Quarterly" (10 Oct 2026), section 4.5: "the
table every EM strategist carries ... for the twelve largest EM plus Thailand --
ranked, with the quarter's change. Free, annual-to-quarterly, no composite: a
table of lenses." Section 26.8's moratorium holds: the lenses are never summed,
averaged or scored into one number, and every series is trigger_eligible: false.

ONE TABLE, country x lens (config/em_scorecard.yaml `lenses`). Each cell:
  value        the lens's latest observation knowable at the as-of, with its
               data-as-of date (the observation's own period)
  percentile   that value against the lens's own observations over the last ten
               years (the as-of join's latest vintages), as an ordinal with n
  change       the value less the value knowable one quarter (91 days) earlier --
               a new period, or a revision, or both
  rank         within its column, 1 the most vulnerable (the lens's `worse`
               direction)
A country with no source for a lens prints "not tracked: <why>", from the
config's `not_yet_sourced` or, where a source exists but nothing is stored yet,
"not tracked: nothing stored at this cutoff" -- never a blank cell.

READERS. `quarterly_block()` is the Quarterly EM chapter's hook (AQ-1 places it):
a sub-section in the stack's shape (title, table, notes, data). `monthly_line()`
is the Monthly's one line in the slow layers: the quarter's three largest
deteriorations, by lens, with their data-as-of. A deterioration is measured in
PERCENTILE POINTS toward the lens's worse side -- the only unit the lenses share
(a percent of GDP, months of imports and a real rate are not comparable in their
own units) -- and a cell whose percentile cannot be taken at both dates is not
ranked. The writer never reads this module's output: it reads the store.
"""

from __future__ import annotations

import datetime as dt
import math
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "em_scorecard.yaml"
NOT_STORED = "nothing stored at this cutoff"


def config() -> dict:
    import yaml  # noqa: PLC0415
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}


def _iso(now: str) -> str:
    from . import observations                                  # noqa: PLC0415
    return observations.canonical_instant(now)


def _shift(now: str, days: int) -> str:
    d = dt.datetime.fromisoformat(_iso(now).replace("Z", "+00:00"))
    return (d - dt.timedelta(days=days)).isoformat()


def _rows(st, key: str, cutoff: str) -> list[tuple[str, float]]:
    return sorted((str(r["observed_at"])[:10], float(r["value_num"]))
                  for r in st.as_of(key, cutoff) if r.get("value_num") is not None)


def percentile(value: float, window: list[float]) -> Optional[float]:
    """The share of the window at or below `value`, in percent (the store's
    convention for a level's percentile); None without a window."""
    if not window:
        return None
    return 100.0 * sum(1 for x in window if x <= value) / len(window)


def _cell(st, key: str, now: str, years: int, qdays: int) -> dict:
    rows = _rows(st, key, now)
    if not rows:
        return {"state": "not_tracked", "why": NOT_STORED}
    day, v = rows[-1]
    lo = (dt.date.fromisoformat(day) - dt.timedelta(days=int(365.25 * years))).isoformat()
    win = [x for d, x in rows if d > lo]
    then_rows = _rows(st, key, _shift(now, qdays))
    out = {"state": "tracked", "value": v, "as_of": day, "n": len(win),
           "percentile": percentile(v, win)}
    if then_rows:
        tday, tv = then_rows[-1]
        tlo = (dt.date.fromisoformat(tday) - dt.timedelta(days=int(365.25 * years))).isoformat()
        out.update(change=v - tv, prior_as_of=tday,
                   prior_percentile=percentile(tv, [x for d, x in then_rows if d > tlo]))
    return out


def build(st, now: Optional[str] = None, cfg: Optional[dict] = None) -> dict:
    """The scorecard at `now`: {as_of, lenses, countries, cells, ranks}."""
    from . import session                                       # noqa: PLC0415
    cfg = cfg or config()
    now = now or session.utc_iso(timespec="microseconds")
    years, qdays = int(cfg.get("percentile_years", 10)), int(cfg.get("quarter_days", 91))
    nys = cfg.get("not_yet_sourced") or {}
    cells: dict[str, dict] = {}
    for c in cfg["countries"]:
        iso = c["iso3"]
        row = {}
        for L in cfg["lenses"]:
            why = (nys.get(iso) or {}).get(L["id"])
            if L["id"] == "infl_gap" and c.get("target") is None and not why:
                why = "no inflation target (" + str(c.get("target_source") or "") + ")"
            if why:
                row[L["id"]] = {"state": "not_tracked", "why": why}
                continue
            row[L["id"]] = _cell(st, L["key"].replace("<iso3>", iso.lower()), now,
                                 years, qdays)
        cells[iso] = row
    ranks: dict[str, dict[str, int]] = {}
    for L in cfg["lenses"]:
        have = [(iso, cells[iso][L["id"]]["value"]) for iso in cells
                if cells[iso][L["id"]].get("state") == "tracked"]
        have.sort(key=lambda x: x[1], reverse=(L["worse"] == "higher"))
        for i, (iso, _v) in enumerate(have, start=1):
            cells[iso][L["id"]]["rank"] = i
            ranks.setdefault(L["id"], {})[iso] = i
    return {"as_of": _iso(now), "lenses": cfg["lenses"],
            "countries": cfg["countries"], "cells": cells, "ranks": ranks}


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------
def fmt_value(v: float, unit: str) -> str:
    if unit == "pct_gdp":
        return f"{v:.1f}%"
    if unit == "months":
        return f"{v:.1f} mo"
    if unit == "times":
        return f"{v:.2f}x"
    if unit == "pts":
        return f"{v:+.1f} pts"
    return f"{v:g}"


def fmt_change(v: Optional[float], unit: str) -> str:
    if v is None:
        return "—"
    if unit == "pct_gdp":
        return f"{v:+.1f} pts"
    if unit == "months":
        return f"{v:+.1f} mo"
    if unit == "times":
        return f"{v:+.2f}x"
    return f"{v:+.1f} pts"


def ordinal(p: Optional[float]) -> Optional[str]:
    if p is None:
        return None
    from .numeral_audit import percentile_ordinal               # noqa: PLC0415
    return percentile_ordinal(p)


def cell_text(cell: dict, unit: str) -> str:
    """What a table cell prints: never blank."""
    if cell.get("state") != "tracked":
        return f"not tracked: {cell.get('why') or NOT_STORED}"
    parts = [fmt_value(cell["value"], unit), f"({cell['as_of']})"]
    o = ordinal(cell.get("percentile"))
    if o:
        parts.append(f"{o} pctl (n={cell['n']})")
    parts.append(f"Δq {fmt_change(cell.get('change'), unit)}")
    parts.append(f"#{cell['rank']}")
    return " · ".join(parts)


def table(sc: dict) -> dict:
    cols = ["Country"] + [L["label"] for L in sc["lenses"]]
    rows = [[c["name"]] + [cell_text(sc["cells"][c["iso3"]][L["id"]], L["unit"])
                           for L in sc["lenses"]] for c in sc["countries"]]
    return {"columns": cols, "rows": rows}


def markdown(sc: dict) -> str:
    t = table(sc)
    out = ["| " + " | ".join(t["columns"]) + " |",
           "|" + "---|" * len(t["columns"])]
    out += ["| " + " | ".join(r) + " |" for r in t["rows"]]
    return "\n".join(out) + "\n"


def quarterly_block(st, now: Optional[str] = None, cfg: Optional[dict] = None) -> dict:
    """THE QUARTERLY'S HOOK (AQ-1 places it in the EM chapter): one sub-section
    in the stack's shape. Each cell's figures ride in `data` with an `_ordinal`
    beside the percentile, so the chapter's prose is audited against them."""
    sc = build(st, now, cfg)
    data = []
    for c in sc["countries"]:
        for L in sc["lenses"]:
            cell = sc["cells"][c["iso3"]][L["id"]]
            d = {"country": c["name"], "lens": L["label"], "state": cell["state"]}
            if cell["state"] == "tracked":
                d.update(value_display=fmt_value(cell["value"], L["unit"]),
                         data_as_of=cell["as_of"], rank=cell["rank"], n=cell["n"],
                         percentile_10y_ordinal=ordinal(cell.get("percentile")),
                         change_quarter_signed=fmt_change(cell.get("change"), L["unit"]))
            else:
                d["why"] = cell["why"]
            data.append(d)
    srcs = "; ".join(f"{L['label']}: {L['source']}" for L in sc["lenses"])
    return {"title": "The EM vulnerability scorecard",
            "table": table(sc),
            "notes": ["A table of lenses, never a composite: each cell is the latest "
                      "value with its data-as-of date, its percentile over ten years, "
                      "its change on the quarter and its rank in the column (1 the most "
                      "vulnerable).", "Sources: " + srcs + "."],
            "data": {"as_of": sc["as_of"], "cells": data}}


def deteriorations(sc: dict, n: int = 3) -> list[dict]:
    """The quarter's largest deteriorations, in percentile points toward each
    lens's worse side; a cell without both percentiles is not ranked."""
    out = []
    names = {c["iso3"]: c["name"] for c in sc["countries"]}
    for L in sc["lenses"]:
        for iso, row in sc["cells"].items():
            cell = row[L["id"]]
            if cell.get("state") != "tracked" or cell.get("prior_percentile") is None \
                    or cell.get("percentile") is None:
                continue
            d = cell["percentile"] - cell["prior_percentile"]
            worse = d if L["worse"] == "higher" else -d
            if worse > 0 and not math.isclose(worse, 0.0):
                out.append({"country": names[iso], "lens": L["label"], "unit": L["unit"],
                            "points": worse, "value": cell["value"],
                            "change": cell.get("change"), "as_of": cell["as_of"],
                            "percentile": cell["percentile"]})
    out.sort(key=lambda x: -x["points"])
    return out[:n]


def monthly_line(st, now: Optional[str] = None, cfg: Optional[dict] = None) -> str:
    """THE MONTHLY'S ONE LINE (slow layers): the three largest deteriorations on
    the quarter, by lens, each with its data-as-of."""
    sc = build(st, now, cfg)
    if not any(c.get("state") == "tracked" for row in sc["cells"].values()
               for c in row.values()):
        return "EM scorecard: not yet stored (its writers fill the store on their first pull)."
    if not any(c.get("prior_percentile") is not None for row in sc["cells"].values()
               for c in row.values()):
        return ("EM scorecard: no cell was knowable a quarter ago yet, so no "
                "deterioration on the quarter can be read; the line fills once the "
                "store holds a quarter of history.")
    worst = deteriorations(sc)
    if not worst:
        return ("EM scorecard: no lens deteriorated on the quarter against its own "
                "ten-year history.")
    parts = [f"{w['country']} {w['lens'].lower()} {fmt_value(w['value'], w['unit'])} "
             f"({fmt_change(w['change'], w['unit'])} on the quarter, "
             f"{ordinal(w['percentile'])} percentile, data as of {w['as_of']})"
             for w in worst]
    return ("EM scorecard, the quarter's largest deteriorations against each lens's "
            "own ten-year history: " + "; ".join(parts) + ".")


if __name__ == "__main__":
    import argparse
    import sys
    from . import observations
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", default=None)
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    now = f"{a.as_of}T23:59:59Z" if a.as_of else None
    with observations.ObservationStore() as _st:
        _sc = build(_st, now)
        print(markdown(_sc))
        print(monthly_line(_st, now))
