"""
The horizon bars, the family long frames, the returns quilt and the roll-yield
row, from the store. (AQ-4, 10 Oct 2026; change order "Alternative Assets
Quarterly" section 7, and section 3's "the tape")

    python -m tools.horizon_charts --as-of 2026-09-30 --out build/horizon/
    python tools/horizon_charts.py --as-of 2026-09-30 --out build/horizon/ --db /path/chester.db

READ-ONLY, AND IT NEVER FETCHES. It reads the observation store as of the date it
is given and writes PNGs, two Markdown tables and one JSON to --out. A series the
store holds too little of prints what it has -- "since <first stored date>" -- and
deepening the history is the operator's one-shot price backfill, run on the box
(docs/briefs/aq-4-horizon-charts-notes.md), never this tool's.

  bars_20y.png, bars_5y.png, bars_1y.png
        total return over 20 years (annualised), 5 years (annualised) and one
        year, for every asset in the quarterly universe plus SPY and TLT, ranked
        within each chart. An asset younger than the horizon -- or whose stored
        history is -- prints "since <date>" with its annualised return over its
        own life (cumulative, and says so, under a year), hatched: never a padded
        or truncated bar.
  horizon_table.md
        QTD and YTD beneath the bars, with each asset's first stored date.
  frame_<family>.png
        one 20-year log chart per family, each member rebased to 100 at its first
        point in the window, the 5-year and 1-year windows marked.
  quilt.png
        calendar-year total returns ranked by year over fifteen years for ten
        asset classes; the current year's column is YTD and says so.
  roll_yield.md
        front against second, annualised, per futures-held commodity, through
        the curve hook (`CURVE_HOOK`): "not tracked" until 6b stores the curve.
  horizon_charts.json
        every figure plotted -- asset, horizon, value, start date, return kind --
        written from the values read back off the drawn bars, so the Quarterly's
        tables and the numeral audit read the numbers the charts drew.

WHAT "AS OF" MEANS. A date D reads every observation dated on or before D that was
knowable by D + 1 at 06:00 UTC: a New York close is stamped at 20:20 or 21:20 UTC,
a coin's daily bar at the end of its UTC day plus twenty minutes (the price feed's
reconstructed availability), so that cutoff holds D's closes and nothing later.
Every figure carries D and the cutoff.

TOTAL RETURN, PRICE RETURN. The price feed stores the close split-adjusted and
dividend-unadjusted, with the dividends beside it as their own series
(yfinance_source.py: the adjusted close is never stored). A fund's total return is
therefore rebuilt here from the close and the dividends, reinvested at the
ex-date's close -- the adjusted close's arithmetic, from rows that never restate.
Everything else (a front future, a spot price, a coin, a currency) is price
return, and each chart's footnote lists which is which.

Palette, surface and labelling are tools/dealer_charts.py's: this is its sibling.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path
from typing import Optional

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import matplotlib                                     # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.patches import Patch, Rectangle       # noqa: E402
from matplotlib.ticker import FuncFormatter           # noqa: E402

CONFIG = REPO / "config" / "horizon_charts.yaml"
CURVE_HOOK = "6b"         # the build that stores the futures curve; see roll_yield()

# --- palette: the report's light surface (tools/dealer_charts.py) -------------
SURFACE = "#fcfcfb"
INK, INK2, MUTED, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.edgecolor": BASE, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "savefig.dpi": 160, "savefig.facecolor": SURFACE,
})


# ---------------------------------------------------------------------------
# Configuration and the universe
# ---------------------------------------------------------------------------
def load_config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8"))


def universe(cfg: dict, repo: Path = REPO) -> tuple[list[dict], str]:
    """The assets, in order, and where the universe came from.

    The quarterly universe is config/correlation.yaml's when that file exists
    (AQ-5), else this config's own copy; `assets` adds family and return kind,
    and the section-7 assets the universe does not key yet."""
    src = repo / cfg.get("universe_file", "config/correlation.yaml")
    skip = set(cfg.get("universe_skip") or [])
    if src.exists():
        uni = (yaml.safe_load(src.read_text(encoding="utf-8")) or {}).get("universe") or []
        origin = str(src.relative_to(repo)).replace("\\", "/")
    else:
        uni, origin = cfg["universe"], "config/horizon_charts.yaml (own copy)"
    meta = cfg["assets"]
    out, seen = [], set()
    for u in uni:
        if u["id"] in skip:
            continue
        if u["id"] not in meta:
            raise ValueError(f"universe asset {u['id']!r} has no row in "
                             f"horizon_charts.yaml `assets` (its family and return kind)")
        out.append({**u, **meta[u["id"]], "id": u["id"],
                    "label": meta[u["id"]].get("label") or u.get("label") or u["id"]})
        seen.add(u["id"])
    for aid, m in meta.items():
        if aid not in seen:
            out.append({"id": aid, **m, "label": m.get("label") or aid})
    for a in out:
        if a["family"] not in cfg["families"]:
            raise ValueError(f"{a['id']}: family {a['family']!r} is not declared")
    return out, origin


def cutoff_for(as_of: str) -> str:
    d = dt.date.fromisoformat(as_of)
    return f"{(d + dt.timedelta(days=1)).isoformat()}T06:00:00Z"


def years_before(d: dt.date, years: int) -> dt.date:
    try:
        return d.replace(year=d.year - years)
    except ValueError:                                  # 29 February
        return d.replace(year=d.year - years, day=28)


def _d(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


# ---------------------------------------------------------------------------
# Reading the store: levels, total-return indices, the cash index
# ---------------------------------------------------------------------------
def read_series(st, key: str, cutoff: str, as_of: str) -> list[tuple[str, float]]:
    """(date, value) for every period dated on or before as_of and knowable at
    the cutoff, one value a day (the latest vintage the store's join returns)."""
    by_day: dict[str, float] = {}
    for r in st.as_of(key, cutoff):
        day = str(r["observed_at"])[:10]
        v = r.get("value_num")
        if v is None or day > as_of:
            continue
        by_day[day] = float(v)
    return sorted(by_day.items())


def total_return_index(closes: list[tuple[str, float]],
                       dividends: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """The close with each dividend reinvested at its ex-date's close: the level
    starts at the first close and grows by (close + dividends since the last
    close) / last close. A dividend dated between two closes is paid at the next."""
    if not closes:
        return []
    divs = sorted(dividends)
    out = [closes[0]]
    j = 0
    while j < len(divs) and divs[j][0] <= closes[0][0]:
        j += 1
    level = closes[0][1]
    for (d0, p0), (d1, p1) in zip(closes, closes[1:]):
        paid = 0.0
        while j < len(divs) and divs[j][0] <= d1:
            paid += divs[j][1]
            j += 1
        if p0 > 0:
            level *= (p1 + paid) / p0
        out.append((d1, level))
    return out


def cash_index(rates: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """The 3-month bill compounded: DTB3 is quoted on a discount basis, so each
    day's rate is taken to its bond-equivalent yield, 365d / (360 - 91d), and
    accrued over the calendar days to the next quote."""
    if not rates:
        return []
    level, out = 100.0, [(rates[0][0], 100.0)]
    for (d0, r0), (d1, _) in zip(rates, rates[1:]):
        d = r0 / 100.0
        bey = 365.0 * d / (360.0 - 91.0 * d)
        level *= 1.0 + bey * (_d(d1) - _d(d0)).days / 365.0
        out.append((d1, level))
    return out


def level_series(st, asset: dict, cutoff: str, as_of: str) -> tuple[list, str]:
    """The series an asset's returns are read on, and its return kind."""
    key = asset["key"]
    closes = read_series(st, key, cutoff, as_of)
    if asset.get("cash"):
        return cash_index(closes), "total"
    if asset.get("invert"):
        return [(d, 1.0 / v) for d, v in closes if v], "price"
    if asset.get("fund"):
        divs = read_series(st, f"{key}_dividend", cutoff, as_of)
        return total_return_index(closes, divs), "total"
    return closes, "price"


# ---------------------------------------------------------------------------
# The figures
# ---------------------------------------------------------------------------
def value_at(points: list, day: dt.date, stale_days: int) -> Optional[tuple[str, float]]:
    """The last point on or before `day`, if it is no older than stale_days."""
    best = None
    for d, v in points:
        if _d(d) <= day:
            best = (d, v)
        else:
            break
    if best is None or (day - _d(best[0])).days > stale_days:
        return None
    return best


def _ann(ratio: float, days: int) -> float:
    return ratio ** (365.25 / days) - 1.0


def horizon_figure(points: list, as_of: str, years: int, annualise: bool,
                   grace_days: int, stale_days: int) -> dict:
    """One asset's figure at one horizon.

    Full horizon: the start is the last close on or before the date `years`
    before as_of (or the first close, if it falls within grace_days after it).
    Otherwise "since inception" -- the first stored close -- annualised over the
    asset's own life, or cumulative under a year, and flagged either way."""
    if not points:
        return {"value": None, "reason": "no stored history"}
    end_day = _d(as_of)
    end = value_at(points, end_day, stale_days)
    if end is None:
        return {"value": None, "reason": f"no close within {stale_days} days of "
                                          f"{as_of} (last stored {points[-1][0]})"}
    target = years_before(end_day, years)
    first = points[0]
    since = False
    if _d(first[0]) <= target:
        start = value_at(points, target, stale_days)
        if start is None:
            return {"value": None, "reason": f"a gap in the stored history at {target}"}
    elif (_d(first[0]) - target).days <= grace_days:
        start = first
    else:
        start, since = first, True
    days = (_d(end[0]) - _d(start[0])).days
    if days <= 0 or start[1] <= 0:
        return {"value": None, "reason": "fewer than two stored closes"}
    ratio = end[1] / start[1]
    if since:
        annualised = days >= 365
    else:
        annualised = annualise
    value = _ann(ratio, days) if annualised else ratio - 1.0
    return {"value": value, "start": start[0], "end": end[0], "since_inception": since,
            "annualised": annualised, "span_days": days}


def period_return(points: list, as_of: str, anchor: dt.date, stale_days: int) -> dict:
    end = value_at(points, _d(as_of), stale_days)
    start = value_at(points, anchor, stale_days)
    if end is None or start is None or start[1] <= 0:
        why = ("no stored history" if not points else
               f"not stored at {anchor}" if start is None else f"no close near {as_of}")
        return {"value": None, "reason": why}
    return {"value": end[1] / start[1] - 1.0, "start": start[0], "end": end[0]}


def quarter_anchor(d: dt.date) -> dt.date:
    q = (d.month - 1) // 3
    return dt.date(d.year, 3 * q + 1, 1) - dt.timedelta(days=1)


def year_anchor(d: dt.date) -> dt.date:
    return dt.date(d.year - 1, 12, 31)


def pct(v: Optional[float], annualised: bool = False) -> str:
    if v is None:
        return "—"
    return f"{100 * v:+.1f}%" + ("/yr" if annualised else "")


# ---------------------------------------------------------------------------
# Compute everything (no drawing)
# ---------------------------------------------------------------------------
def compute(st, cfg: dict, as_of: str, repo: Path = REPO) -> dict:
    cutoff = cutoff_for(as_of)
    assets, origin = universe(cfg, repo)
    grace, stale = int(cfg.get("grace_days", 7)), int(cfg.get("stale_days", 10))
    series: dict[str, list] = {}
    rows = []
    for a in assets:
        row = {"asset": a["id"], "id": a["id"], "label": a["label"], "family": a["family"],
               "proxy": a.get("proxy"), "key": a.get("key")}
        if a.get("absent") or not a.get("key"):
            row.update(absent=a.get("absent") or "no key", return_kind=None, first_stored=None)
            rows.append(row)
            continue
        pts, kind = level_series(st, a, cutoff, as_of)
        series[a["id"]] = pts
        row.update(return_kind=kind, first_stored=pts[0][0] if pts else None,
                   last_stored=pts[-1][0] if pts else None, note=a.get("note"),
                   added=a.get("added"))
        for h in cfg["horizons"]:
            row[h["id"]] = horizon_figure(pts, as_of, h["years"], h["annualise"], grace, stale)
        d = _d(as_of)
        row["qtd"] = period_return(pts, as_of, quarter_anchor(d), stale)
        row["ytd"] = period_return(pts, as_of, year_anchor(d), stale)
        rows.append(row)
    return {"as_of": as_of, "cutoff": cutoff, "universe_from": origin, "assets": rows,
            "series": series, "quilt": quilt(st, cfg, as_of, cutoff),
            "roll_yield": roll_yield(st, cfg, as_of, cutoff)}


def quilt(st, cfg: dict, as_of: str, cutoff: str) -> dict:
    q = cfg["quilt"]
    stale = int(cfg.get("stale_days", 10))
    d = _d(as_of)
    years = list(range(d.year - q["years"] + 1, d.year + 1))
    cells: dict[int, list] = {y: [] for y in years}
    first: dict[str, Optional[str]] = {}
    for c in q["classes"]:
        pts, kind = level_series(st, c, cutoff, as_of)
        first[c["id"]] = pts[0][0] if pts else None
        for y in years:
            end_day = d if y == d.year else dt.date(y, 12, 31)
            r = period_return(pts, end_day.isoformat(), dt.date(y - 1, 12, 31), stale)
            cells[y].append({"class": c["id"], "label": c["label"], "short": c.get("short") or c["label"],
                             "hue": c["hue"], "value": r.get("value"), "return_kind": kind,
                             "start": r.get("start"), "end": r.get("end"),
                             "reason": r.get("reason")})
    for y in years:
        cells[y].sort(key=lambda x: (x["value"] is None, -(x["value"] or 0.0)))
    return {"years": years, "ytd_year": d.year, "cells": cells, "first_stored": first}


def roll_yield(st, cfg: dict, as_of: str, cutoff: str) -> list[dict]:
    """THE ROLL-YIELD ROW, through the curve hook. Each commodity reads its front
    and second contracts from the keys config/horizon_charts.yaml declares, which
    the curve build (CURVE_HOOK, with ST-B3-13) will write; until both are in the
    store the row is the hook's "not tracked" line, never a zero."""
    ry = cfg["roll_yield"]
    stale = int(cfg.get("stale_days", 10))
    out = []
    for r in ry["rows"]:
        front = value_at(read_series(st, r["front"], cutoff, as_of), _d(as_of), stale)
        second = value_at(read_series(st, r["second"], cutoff, as_of), _d(as_of), stale)
        row = {"id": r["id"], "label": r["label"], "hook": ry.get("hook", CURVE_HOOK)}
        if not front or not second or front[1] <= 0 or second[1] <= 0:
            row.update(value=None, state=ry["message"])
            out.append(row)
            continue
        dk = value_at(read_series(st, r["days_key"], cutoff, as_of), _d(as_of), stale)
        days = dk[1] if dk and dk[1] > 0 else 365.0 / 12.0 * r["spacing_months"]
        v = math.log(front[1] / second[1]) * 365.0 / days
        row.update(value=v, front=front[1], second=second[1], days=days, date=front[0],
                   state="backwardation" if v > 0 else "contango" if v < 0 else "flat",
                   days_from=("stored" if dk and dk[1] > 0 else "declared spacing"))
        out.append(row)
    return out


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------
def _style(ax) -> None:
    ax.tick_params(length=0)


def _stamp(res: dict) -> str:
    return f"as of {res['as_of']} · store cutoff {res['cutoff'][:16]}Z"


def kind_footnote(res: dict) -> str:
    tot = [a["label"] for a in res["assets"] if a.get("return_kind") == "total"]
    prc = [a["label"] for a in res["assets"] if a.get("return_kind") == "price"]
    return ("Total return, distributions reinvested (close and stored dividends): "
            + ", ".join(tot) + ".\nPrice return: " + ", ".join(prc)
            + " (copper is the front future, its roll in the return; natural gas is spot).")


def not_drawn_line(rows: list[dict], hid: str) -> str:
    """One clause per reason: "Oil, Copper: no stored history; PRL: no feed ..."."""
    by: dict[str, list[str]] = {}
    for a in rows:
        why = a.get("absent") or (a.get(hid) or {}).get("reason") or "no figure"
        by.setdefault(why, []).append(a["label"])
    return "Not drawn — " + "; ".join(f"{', '.join(v)}: {k}" for k, v in by.items())


def draw_bars(res: dict, cfg: dict, hid: str, out: Path) -> tuple[Path, list[dict]]:
    h = next(x for x in cfg["horizons"] if x["id"] == hid)
    fams = cfg["families"]
    figs = [a for a in res["assets"] if a.get(hid, {}).get("value") is not None]
    figs.sort(key=lambda a: a[hid]["value"], reverse=True)
    not_drawn = [a for a in res["assets"] if a not in figs]
    n = max(len(figs), 1)
    fig, ax = plt.subplots(figsize=(10, 0.34 * n + 2.6))
    ys = list(range(len(figs)))[::-1]
    vals = [100 * a[hid]["value"] for a in figs]
    hues = [fams[a["family"]]["hue"] for a in figs]
    bars = ax.barh(ys, vals, height=0.55, color=hues, zorder=2)
    for rect, a in zip(bars, figs):
        if a[hid]["since_inception"]:
            rect.set_hatch("////")
            rect.set_alpha(0.6)
            rect.set_edgecolor(SURFACE)
    span = (max(vals + [0]) - min(vals + [0])) or 1.0
    for y, v, a in zip(ys, vals, figs):
        f = a[hid]
        txt = pct(f["value"], f["annualised"])
        if f["since_inception"]:
            txt += f"  since {f['start']}" + ("" if f["annualised"] else ", not annualised")
        ax.text(v + (0.01 if v >= 0 else -0.01) * span, y, txt, va="center",
                ha="left" if v >= 0 else "right", fontsize=8.5, color=INK2)
    ax.set_yticks(ys, [a["label"] for a in figs], fontsize=9)
    ax.axvline(0, color=BASE, lw=1)
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.0f}%"))
    ax.margins(x=0.28)
    what = (f"{h['years']}-year total return, annualised" if h["annualise"]
            else "One-year total return")
    ax.set_title(f"{what}, ranked\n{_stamp(res)}", loc="left", fontsize=11)
    _style(ax)
    present = []
    for a in figs:
        if a["family"] not in present:
            present.append(a["family"])
    handles = [Patch(color=fams[f]["hue"], label=fams[f]["label"]) for f in present]
    if any(a[hid]["since_inception"] for a in figs):
        handles.append(Patch(facecolor=SURFACE, edgecolor=INK2, hatch="////",
                             label="since inception / first stored close"))
    ax.legend(handles=handles, frameon=False, fontsize=8, loc="lower right")
    foot = kind_footnote(res)
    if not_drawn:
        foot += "\n" + not_drawn_line(not_drawn, hid)
    fig.text(0.01, 0.005, foot, fontsize=7, color=MUTED, va="bottom", ha="left", wrap=True)
    fig.tight_layout(rect=(0, 0.04 + 0.012 * foot.count("\n") + 0.02 * (len(foot) // 160), 1, 1))
    path = out / f"bars_{hid}.png"
    fig.savefig(path)
    plt.close(fig)
    # READ BACK OFF THE ARTISTS: the JSON is what was drawn, not what was meant.
    drawn = [{"asset": a["id"], "drawn_value": rect.get_width() / 100.0}
             for rect, a in zip(bars, figs)]
    return path, drawn


def frame_window(points: list, as_of: str, years: int = 20) -> list:
    lo = years_before(_d(as_of), years).isoformat()
    return [(d, v) for d, v in points if d >= lo]


def draw_frame(res: dict, cfg: dict, family: str, out: Path) -> tuple[Optional[Path], dict]:
    fams = cfg["families"]
    hue = fams[family]["hue"]
    members = [a for a in res["assets"] if a["family"] == family]
    lines = []
    for a in members:
        w = frame_window(res["series"].get(a["id"]) or [], res["as_of"])
        if len(w) >= 2 and w[0][1] > 0:
            lines.append((a, [(d, 100.0 * v / w[0][1]) for d, v in w]))
    info = {"family": family, "members": [], "missing": [
        {"asset": a["id"], "label": a["label"],
         "why": a.get("absent") or "no stored history in the window"}
        for a in members if a["id"] not in {x["id"] for x, _ in lines}]}
    if not lines:
        info["unavailable"] = "no member has stored history"
        return None, info
    d_end = _d(res["as_of"])
    fig, ax = plt.subplots(figsize=(10, 4.8))
    styles = ["-", (0, (5, 2)), (0, (2, 1.5)), (0, (6, 2, 1, 2)), (0, (1, 1))]
    for i, (a, pts) in enumerate(lines):
        xs = [dt.date.fromisoformat(d) for d, _ in pts]
        ys = [v for _, v in pts]
        ax.plot(xs, ys, color=hue, lw=1.6 if i == 0 else 1.2, ls=styles[i % len(styles)],
                alpha=1.0 - 0.12 * min(i, 4), zorder=3)
        ax.annotate(f"{a['label']} {ys[-1]:,.0f}" + (f"  (from {pts[0][0]})"
                    if (_d(pts[0][0]) - years_before(d_end, 20)).days
                    > int(cfg.get("grace_days", 7)) else ""),
                    (xs[-1], ys[-1]), xytext=(6, 0), textcoords="offset points",
                    fontsize=8.5, color=INK2, va="center")
        info["members"].append({"asset": a["id"], "start": pts[0][0], "end": pts[-1][0],
                                "rebased_end": ys[-1], "return_kind": a.get("return_kind")})
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
    for yrs, alpha, lab in ((5, 0.06, "5 years"), (1, 0.12, "1 year")):
        x0 = years_before(d_end, yrs)
        ax.axvspan(x0, d_end, color=hue, alpha=alpha, lw=0, zorder=1)
        ax.text(x0, 0.98, f" {lab}", transform=ax.get_xaxis_transform(), fontsize=8,
                color=MUTED, va="top", ha="left")
    ax.set_xlim(years_before(d_end, 20), d_end + dt.timedelta(days=int(365 * 3.5)))
    ax.set_title(f"{fams[family]['label']}: 20 years on a log scale, each rebased to 100 "
                 f"at its first point\n{_stamp(res)}", loc="left", fontsize=11)
    ax.set_ylabel("Rebased to 100 (log)")
    ax.grid(axis="x", visible=False)
    _style(ax)
    foot = "Total return for funds (distributions reinvested); price return otherwise."
    if info["missing"]:
        foot += "  Not drawn: " + "; ".join(f"{m['label']} ({m['why']})" for m in info["missing"])
    fig.text(0.01, 0.01, foot, fontsize=7, color=MUTED, va="bottom", ha="left", wrap=True)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    path = out / f"frame_{family}.png"
    fig.savefig(path)
    plt.close(fig)
    return path, info


def draw_quilt(res: dict, out: Path) -> tuple[Path, list[dict]]:
    q = res["quilt"]
    years = q["years"]
    nrows = max(len(v) for v in q["cells"].values())
    fig, ax = plt.subplots(figsize=(1.0 * len(years) + 1.2, 0.62 * nrows + 1.9))
    ax.set_xlim(0, len(years))
    ax.set_ylim(nrows, -0.9)
    ax.axis("off")
    drawn = []
    for i, y in enumerate(years):
        head = f"{y}\nYTD" if y == q["ytd_year"] else str(y)
        ax.text(i + 0.5, -0.45, head, ha="center", va="center", fontsize=8.5,
                fontweight="bold", color=INK2)
        rank = 0
        for c in q["cells"][y]:
            if c["value"] is None:
                continue
            ax.add_patch(Rectangle((i + 0.04, rank + 0.04), 0.92, 0.92,
                                   facecolor=c["hue"], edgecolor=SURFACE, lw=1))
            dark = c["hue"] in ("#b9b6a8", "#c99a06")
            label = f"{c['short']}\n{100 * c['value']:+.1f}%"
            ax.text(i + 0.5, rank + 0.5, label, ha="center", va="center", fontsize=6.6,
                    color=INK if dark else "#ffffff")
            drawn.append({"year": y, "rank": rank + 1, "class": c["class"],
                          "drawn_value": float(label.split("\n")[1].rstrip("%")) / 100.0,
                          "value": c["value"]})
            rank += 1
    ax.set_title(f"Calendar-year total returns, ranked, {years[0]}–{years[-1]} "
                 f"({years[-1]} is year to date)\n{_stamp(res)}", loc="left", fontsize=11)
    missing = sorted({c["label"] for y in years for c in q["cells"][y] if c["value"] is None})
    foot = ("Funds are total return (distributions reinvested); Bitcoin and the dollar index "
            "are price return; cash is the 3-month bill (FRED DTB3) compounded at its "
            "bond-equivalent yield. Broad commodities is DBC, a futures fund.")
    if missing:
        foot += ("\nBlank below a column: the class is not stored for that whole year — "
                 + "; ".join(f"{m} (first stored {q['first_stored'][c]})"
                             for c, m in {c["class"]: c["label"] for y in years
                                          for c in q["cells"][y] if c["value"] is None}.items()))
    fig.text(0.01, 0.01, foot, fontsize=7, color=MUTED, va="bottom", ha="left", wrap=True)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    path = out / "quilt.png"
    fig.savefig(path)
    plt.close(fig)
    return path, drawn


# ---------------------------------------------------------------------------
# Tables and the JSON
# ---------------------------------------------------------------------------
def horizon_table(res: dict) -> str:
    lines = [f"QTD and YTD, {_stamp(res)}", "",
             "| Asset | Family | Return | QTD | YTD | First stored |",
             "|---|---|---|---|---|---|"]
    for a in res["assets"]:
        if a.get("absent"):
            lines.append(f"| {a['label']} | {a['family']} | absent | — | — | {a['absent']} |")
            continue
        lines.append(f"| {a['label']} | {a['family']} | {a['return_kind']} | "
                     f"{pct(a['qtd'].get('value'))} | {pct(a['ytd'].get('value'))} | "
                     f"{a.get('first_stored') or 'none'} |")
    return "\n".join(lines) + "\n"


def roll_table(res: dict) -> str:
    lines = [f"Roll yield, front against second, annualised — {_stamp(res)}", "",
             "| Commodity | Roll yield | Curve |", "|---|---|---|"]
    for r in res["roll_yield"]:
        lines.append(f"| {r['label']} | {pct(r['value'])} | {r['state']} |")
    return "\n".join(lines) + "\n"


def figures_json(res: dict, cfg: dict, drawn: dict, frames: dict, quilt_drawn: list) -> dict:
    figs = []
    for hid, rows in drawn.items():
        by = {a["asset"]: a for a in res["assets"]}
        for d in rows:
            a, f = by[d["asset"]], by[d["asset"]][hid]
            figs.append({"asset": a["id"], "label": a["label"], "family": a["family"],
                         "horizon": hid, "value": d["drawn_value"],
                         "printed": pct(f["value"], f["annualised"]),
                         "annualised": f["annualised"], "since_inception": f["since_inception"],
                         "start": f["start"], "end": f["end"], "return_kind": a["return_kind"]})
    return {
        "as_of": res["as_of"], "cutoff": res["cutoff"], "universe_from": res["universe_from"],
        "bars": figs,
        "not_drawn": {hid: [{"asset": a["id"], "why": a.get("absent") or a.get(hid, {}).get("reason")}
                            for a in res["assets"]
                            if a["id"] not in {d["asset"] for d in rows}]
                      for hid, rows in drawn.items()},
        "table": [{"asset": a["id"], "label": a["label"], "family": a["family"],
                   "return_kind": a.get("return_kind"), "first_stored": a.get("first_stored"),
                   "absent": a.get("absent"),
                   "qtd": (a.get("qtd") or {}).get("value"),
                   "qtd_start": (a.get("qtd") or {}).get("start"),
                   "ytd": (a.get("ytd") or {}).get("value"),
                   "ytd_start": (a.get("ytd") or {}).get("start")} for a in res["assets"]],
        "frames": frames,
        "quilt": {"years": res["quilt"]["years"], "ytd_year": res["quilt"]["ytd_year"],
                  "cells": quilt_drawn, "first_stored": res["quilt"]["first_stored"]},
        "roll_yield": res["roll_yield"],
    }


def run(st, as_of: str, out: Path, cfg: Optional[dict] = None, repo: Path = REPO) -> dict:
    """Compute, draw, check the drawn against the computed, write. Returns the JSON."""
    cfg = cfg or load_config()
    out.mkdir(parents=True, exist_ok=True)
    res = compute(st, cfg, as_of, repo)
    drawn, made = {}, []
    for h in cfg["horizons"]:
        path, rows = draw_bars(res, cfg, h["id"], out)
        by = {a["asset"]: a for a in res["assets"]}
        for d in rows:
            want = by[d["asset"]][h["id"]]["value"]
            if abs(d["drawn_value"] - want) > 1e-9:
                raise AssertionError(f"{d['asset']} {h['id']}: drew {d['drawn_value']}, "
                                     f"computed {want}")
        drawn[h["id"]] = rows
        made.append(path)
    frames = {}
    for fam, f in cfg["families"].items():
        if not f.get("frame"):
            continue
        path, info = draw_frame(res, cfg, fam, out)
        frames[fam] = info
        if path:
            made.append(path)
    qpath, qdrawn = draw_quilt(res, out)
    made.append(qpath)
    doc = figures_json(res, cfg, drawn, frames, qdrawn)
    (out / "horizon_table.md").write_text(horizon_table(res), encoding="utf-8")
    (out / "roll_yield.md").write_text(roll_table(res), encoding="utf-8")
    (out / "horizon_charts.json").write_text(json.dumps(doc, indent=1, sort_keys=True),
                                             encoding="utf-8")
    doc["_written"] = [str(p) for p in made] + [str(out / n) for n in
                                                ("horizon_table.md", "roll_yield.md",
                                                 "horizon_charts.json")]
    return doc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--as-of", required=True, help="YYYY-MM-DD: the date every figure is read at")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--db", default=None, help="observation store path (default: the configured store)")
    a = ap.parse_args(argv)
    dt.date.fromisoformat(a.as_of)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from altdata import observations                            # noqa: PLC0415
    with observations.ObservationStore(a.db) as st:
        doc = run(st, a.as_of, Path(a.out))
    for p in doc["_written"]:
        print(p)
    since = sorted({f"{b['label']} since {b['start']}" for b in doc["bars"] if b["since_inception"]})
    if since:
        print(f"{len(since)} figure(s) print 'since' their first stored close: "
              + "; ".join(since[:8]) + (" ..." if len(since) > 8 else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
