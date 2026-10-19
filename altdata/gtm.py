"""
The J.P. Morgan Guide to the Markets batch, part 1 -- the seven items computed
from data the store holds or FRED serves.

    python -m altdata.gtm show [--db PATH] [--as-of INSTANT]   # every table, text
    python -m altdata.gtm check                                # the sourced figures

Change order docs/change-order-jpm-gtm-2026-10-03.md (ruled 3 Oct 2026); settings
and the sourced figures in config/gtm.yaml; layout in daily_cascade/gtm_block.py;
the three base-rate tables stored by tools/base_rates.py; tools/validate_gtm.py
holds every table to a hand figure on a fixture.

  GTM-1   the inflection-points table: the prior tops and bottoms as the scan
          states them (sourced), and a "today" row from the store
  GTM-7   the stock-bond correlation regime table (amends SR-9): three eras from
          Shiller's monthly sheet, the current 24-month correlation, a regime word
  GTM-8   the sentiment turning-point base rate: Michigan's peaks and troughs and
          the S&P 500's next 12 months, our own n, the Guide's figures beside
  GTM-9   the all-time-high base rates from ^GSPC's daily closes
  GTM-13  the fixed-income scenario table: yield, year to date, duration, the two
          correlations and the +/-100 bp price return, by sector with a proxy
  GTM-15  the effective tariff rate (customs duties over goods imports, FRED)
  GTM-21  the household debt-service ratio with dual percentiles (SR-5's modifier)

TWO KINDS OF NUMBER. A computed figure is computed here from the store as of the
cutoff. A figure only the Guide has is a SOURCED figure, declared in the config
with the scan's own words, stored by `altdata.scans ingest` and read back from
the store; it is printed beside ours, labelled, and never recomputed.

Every input that is absent prints "not stored" (or "no proxy", "not in the
scan"), never a blank or a zero. Nothing here writes, fetches or calls a model,
and nothing grants a right: each table is a base-rate row or a modifier, read by
a human.
"""

from __future__ import annotations

import datetime as dt
import math
import re
from pathlib import Path
from typing import Any, Optional

import yaml

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "gtm.yaml"
REFERENCE_PATH = REPO / "config" / "instrument_reference.yaml"
NOT_STORED = "not stored"
NOT_IN_SCAN = "not in the scan"
NOT_ON_SLIDE = "not on the slide"
NO_PROXY = "no proxy"
METRIC_PREFIX = "GTM-"


class GtmError(ValueError):
    """A sourced figure the batch refuses, with its reason."""


def config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# Sourced figures
# ---------------------------------------------------------------------------
def scan_path(cfg: dict) -> Path:
    return REPO / "docs" / "scans" / f"{cfg['scan_id']}.md"


def metric_name(entry: dict) -> str:
    """The stored metric: 'GTM-7 · 1964 to 1999, average inflation'."""
    return f"{entry['item']} · {entry['label']}"


def sourced_refusal(entry: dict, scan_text: str) -> Optional[str]:
    """Why a declared figure cannot be stored, or None. A figure needs its item,
    label and value; a section reference and the Guide's slide; the scan's words
    quoted exactly; and its value inside that quote (a trailing % aside, where the
    scan writes the figure without one)."""
    for f in ("item", "label", "value"):
        if not str(entry.get(f) or "").strip():
            return f"no {f}"
    if not str(entry.get("section") or "").strip():
        return "no section reference"
    q = str(entry.get("quote") or "")
    if not q.strip():
        return "no quote from the scan"
    if q not in scan_text:
        return "the quote is not in the scan"
    if str(entry["value"]).rstrip("%") not in q:
        return f"the value {entry['value']!r} is not in its quote"
    slide = entry.get("slide")
    if slide is None:
        return "no slide reference"
    if not (isinstance(slide, int) and slide > 0):
        return "a slide must be a positive number"
    return None


def sourced_figures(cfg: Optional[dict] = None,
                    path: Optional[Path] = None) -> tuple[list[dict], list[dict]]:
    """(figures for scans.write, refusals). The scan's header supplies the URL,
    the as-of and the read-on date, so a figure with no as-of is refused there
    (scans.refusal) as well as here."""
    from . import scans  # noqa: PLC0415
    cfg = cfg or config()
    p = Path(path or scan_path(cfg))
    if not p.exists():
        return [], [{"metric": None, "reason": f"{p.name} is not in docs/scans"}]
    text = p.read_text(encoding="utf-8")
    head = {k: v for k, v in scans.parse(p).items() if k not in ("figures", "refused")}
    figs, refused = [], []
    for e in cfg.get("sourced") or []:
        why = sourced_refusal(e, text)
        fig = {**head, "metric": metric_name(e), "value": str(e["value"]),
               "comparison": None, "section_ref": e.get("section"),
               "slide": e.get("slide")} if not why else None
        if fig is not None:
            why = scans.refusal(fig)
        if why:
            refused.append({"metric": e.get("id"), "reason": why})
        else:
            figs.append(fig)
    return figs, refused


def sourced(as_of: Optional[str] = None, db_path: Optional[str] = None,
            cfg: Optional[dict] = None) -> dict[str, dict]:
    """The stored sourced figures readable at the cutoff, by config id: each the
    store's row (value, source_ref, as_of, source_url) and the declared number."""
    from . import scans  # noqa: PLC0415
    cfg = cfg or config()
    by_metric = {metric_name(e): e for e in cfg.get("sourced") or []}
    out = {}
    for r in scans.latest(as_of, db_path):
        e = by_metric.get(r["metric"])
        if e is None or r["family"] != scans.FAMILY_SUFFIX.sub("", cfg["scan_id"]):
            continue
        out[e["id"]] = {**r, "id": e["id"], "number": e.get("number"),
                        "n": e.get("n"), "label": e["label"]}
    return out


def cite(row: Optional[dict]) -> str:
    """'+0.28 (the Guide, §6, as of 2026-09-30)', or "not stored"."""
    if not row:
        return NOT_STORED
    return f"{row['value']} (the Guide, {row['source_ref']}, as of {row['as_of']})"


# ---------------------------------------------------------------------------
# Reading the store
# ---------------------------------------------------------------------------
def points(st, key: str, cutoff: str, instrument: Optional[str] = None,
           observed_from: Optional[str] = None) -> list[tuple[str, float]]:
    """[(day, value)] knowable at the cutoff, oldest first; [] when absent."""
    if st is None:
        return []
    try:
        rows = st.as_of(key, cutoff, instrument, observed_from=observed_from)
    except Exception:                                          # noqa: BLE001
        return []
    out = [(str(r["observed_at"])[:10], float(r["value_num"])) for r in rows
           if r.get("value_num") is not None]
    out.sort()
    return out


def latest(pts: list[tuple[str, float]]) -> Optional[tuple[str, float]]:
    return pts[-1] if pts else None


def month_end(pts: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """[(YYYY-MM, the month's last value)] from daily points."""
    out: dict[str, float] = {}
    for d, v in pts:
        out[d[:7]] = v
    return sorted(out.items())


def by_month(pts: list[tuple[str, float]]) -> dict[str, float]:
    """{YYYY-MM: value} for a monthly series (the period's own observed_at)."""
    return {d[:7]: v for d, v in pts}


def _month_add(m: str, k: int) -> str:
    y, mo = int(m[:4]), int(m[5:7])
    i = y * 12 + (mo - 1) + k
    return f"{i // 12:04d}-{i % 12 + 1:02d}"


def _months(a: str, b: str) -> list[str]:
    out, m = [], a
    while m <= b:
        out.append(m)
        m = _month_add(m, 1)
    return out


# ---------------------------------------------------------------------------
# Small statistics
# ---------------------------------------------------------------------------
def pearson(xs: list[float], ys: list[float]) -> Optional[float]:
    n = len(xs)
    if n < 3 or n != len(ys):
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sxx * syy)


def mean(xs: list[float]) -> Optional[float]:
    return sum(xs) / len(xs) if xs else None


def median(xs: list[float]) -> Optional[float]:
    if not xs:
        return None
    s = sorted(xs)
    k = len(s) // 2
    return s[k] if len(s) % 2 else (s[k - 1] + s[k]) / 2


def _f(v: Optional[float], nd: int = 2, sign: bool = False, unit: str = "") -> str:
    if v is None:
        return NOT_STORED
    return f"{v:+.{nd}f}{unit}" if sign else f"{v:.{nd}f}{unit}"


# ---------------------------------------------------------------------------
# GTM-7: the stock-bond correlation regime table (amends SR-9)
# ---------------------------------------------------------------------------
def par_bond_price(coupon: float, yld: float, years: int = 10) -> float:
    """A par bond's price per 1 of face: semiannual coupon `coupon` (a decimal),
    priced at yield `yld`, `years` to maturity."""
    n = 2 * years
    if abs(yld) < 1e-12:
        return 1.0 + coupon / 2 * n
    d = (1 + yld / 2) ** (-n)
    return coupon / yld * (1 - d) + d


def monthly_total_returns(price: dict[str, float], dividend: dict[str, float],
                          gs10: dict[str, float], years: int = 10
                          ) -> dict[str, tuple[float, float]]:
    """{month: (equity total return, bond total return)}, both decimals.
    Equity: (P_m + D_m / 12) / P_{m-1} - 1, D the sheet's annualised dividend.
    Bond: a 10-year par bond bought at last month's yield, priced at this
    month's, plus a month's coupon."""
    out = {}
    for m in sorted(price):
        p0 = price.get(_month_add(m, -1))
        y0, y1 = gs10.get(_month_add(m, -1)), gs10.get(m)
        if p0 is None or y0 is None or y1 is None or m not in dividend or p0 <= 0:
            continue
        eq = (price[m] + dividend[m] / 12.0) / p0 - 1
        bd = par_bond_price(y0 / 100, y1 / 100, years) - 1 + y0 / 100 / 12
        out[m] = (eq, bd)
    return out


def rolling_correlation(tr: dict[str, tuple[float, float]], n: int
                        ) -> dict[str, float]:
    """{window-end month: Pearson correlation of the n monthly pairs ending there},
    only over n consecutive months."""
    months = sorted(tr)
    out = {}
    for i in range(n - 1, len(months)):
        win = months[i - n + 1:i + 1]
        if _month_add(win[0], n - 1) != win[-1]:
            continue
        c = pearson([tr[m][0] for m in win], [tr[m][1] for m in win])
        if c is not None:
            out[win[-1]] = c
    return out


def cpi_yoy(cpi: dict[str, float]) -> dict[str, float]:
    return {m: 100 * (v / cpi[_month_add(m, -12)] - 1) for m, v in cpi.items()
            if cpi.get(_month_add(m, -12))}


def regime_word(c: Optional[float], bands: dict) -> Optional[str]:
    if c is None:
        return None
    if c >= float(bands["positive"]):
        return "positive"
    if c <= float(bands["negative"]):
        return "negative"
    return "near zero"


def stock_bond_eras(price: dict[str, float], dividend: dict[str, float],
                    cpi: dict[str, float], gs10: dict[str, float],
                    cfg: Optional[dict] = None) -> dict:
    """The three eras and the current reading, from monthly series keyed YYYY-MM."""
    cfg = cfg or config()
    sb = cfg["stock_bond"]
    n = int(sb["rolling_months"])
    tr = monthly_total_returns(price, dividend, gs10, int(sb["bond_maturity_years"]))
    roll = rolling_correlation(tr, n)
    yoy = cpi_yoy(cpi)
    if not tr:
        return {"state": "absent", "absent_reason":
                "Shiller's price, dividend and GS10 are not stored together"}
    last = max(roll) if roll else None
    eras = []
    for e in sb["eras"]:
        end = e.get("end") or last or max(tr)
        months = _months(e["start"], end)
        cs = [roll[m] for m in months if m in roll]
        inf = [yoy[m] for m in months if m in yoy]
        cover = len(cs) / len(months) if months else 0.0
        ok = cover >= float(sb["min_coverage"])
        eras.append({"id": e["id"], "label": e["label"], "start": e["start"],
                     "end": end, "months": len(months), "n_windows": len(cs),
                     "coverage": round(cover, 4),
                     "correlation": round(mean(cs), 4) if ok and cs else None,
                     "inflation": round(mean(inf), 4) if ok and inf else None,
                     "computed": ok})
    cur = roll.get(last) if last else None
    # The latest reading's own window, printed beside the eras' (step 0.5 of the
    # GTM part 2 paste): a 24-month window is not an era's average.
    trm = sorted(tr)
    start = (trm[trm.index(last) - n + 1] if last in trm and trm.index(last) >= n - 1
             else None)
    return {"state": "ok", "window_months": n,
            "first_month": min(tr), "last_month": max(tr),
            "eras": eras, "current": {"month": last, "from": start,
                                      "correlation": round(cur, 4) if cur is not None else None,
                                      "word": regime_word(cur, sb["regime_bands"])},
            "method": ("monthly total returns from Shiller's sheet: the S&P "
                       "Composite (price, dividend / 12) and a 10-year par bond "
                       "priced off GS10; the 24-month rolling correlation, "
                       "averaged over windows ending in the era; CPI on the year")}


# ---------------------------------------------------------------------------
# GTM-8: the sentiment turning-point base rate
# ---------------------------------------------------------------------------
def turning_points(series: list[tuple[str, float]], window: int,
                   min_swing: float) -> list[dict]:
    """Peaks and troughs of a monthly series [(YYYY-MM, v)], by the declared rule:
    strictly the extreme within `window` months either side (both sides
    observed; a tie is neither), then
    alternation (two peaks keep the higher, two troughs the lower), then pairs
    less than `min_swing` apart dropped, repeated until none is."""
    s = sorted(series)
    if not s:
        return []
    first, last = s[0][0], s[-1][0]
    cands = []
    for i, (m, v) in enumerate(s):
        lo, hi = _month_add(m, -window), _month_add(m, window)
        if lo < first or hi > last:
            continue
        others = [x for mm, x in s if lo <= mm <= hi and mm != m]
        if not others:
            continue
        # STRICTLY the extreme: a month level with another in its window is
        # neither, so a flat stretch marks no turning point.
        if v > max(others):
            cands.append({"month": m, "kind": "peak", "value": v})
        elif v < min(others):
            cands.append({"month": m, "kind": "trough", "value": v})

    def alternate(pts):
        out = []
        for p in pts:
            if out and out[-1]["kind"] == p["kind"]:
                better = (p["value"] > out[-1]["value"] if p["kind"] == "peak"
                          else p["value"] < out[-1]["value"])
                if better:
                    out[-1] = p
                continue
            out.append(p)
        return out

    pts = alternate(cands)
    changed = True
    while changed and len(pts) > 1:
        changed = False
        for i in range(len(pts) - 1):
            if abs(pts[i]["value"] - pts[i + 1]["value"]) < min_swing:
                del pts[i:i + 2]
                pts = alternate(pts)
                changed = True
                break
    return pts


def sentiment_base_rate(sentiment: list[tuple[str, float]],
                        spx_daily: list[tuple[str, float]],
                        cfg: Optional[dict] = None) -> dict:
    """Our own peaks and troughs of Michigan sentiment with the S&P 500's next
    12 months (price, month-end closes), n and the mean and median of each."""
    cfg = cfg or config()
    sc = cfg["sentiment"]
    k = int(sc["forward_months"])
    if not sentiment or not spx_daily:
        return {"state": "absent", "absent_reason":
                "Michigan sentiment or the S&P 500's closes are not stored"}
    sent = sorted(by_month(sentiment).items())
    spx = dict(month_end(spx_daily))
    tps = turning_points(sent, int(sc["window_months"]), float(sc["min_swing_points"]))
    hi12 = {}
    months = sorted(spx)
    for i, m in enumerate(months):
        hi12[m] = max(spx[x] for x in months[max(0, i - 12):i + 1])
    episodes = []
    for tp in tps:
        a, b = spx.get(tp["month"]), spx.get(_month_add(tp["month"], k))
        dd = (100 * (a / hi12[tp["month"]] - 1)) if a and tp["month"] in hi12 else None
        episodes.append({**tp, "spx": a, "spx_forward": b,
                         "forward_return": (round(100 * (b / a - 1), 4)
                                            if a and b else None),
                         "drawdown_from_12m_high": round(dd, 4) if dd is not None else None})
    out = {"state": "ok", "first_month": sent[0][0], "last_month": sent[-1][0],
           "rule": {k2: sc[k2] for k2 in ("window_months", "min_swing_points",
                                          "forward_months")},
           "episodes": episodes}
    for kind in ("peak", "trough"):
        rs = [e["forward_return"] for e in episodes
              if e["kind"] == kind and e["forward_return"] is not None]
        out[kind + "s"] = {"n": len(rs),
                           "mean": round(mean(rs), 4) if rs else None,
                           "median": round(median(rs), 4) if rs else None,
                           "unresolved": sum(1 for e in episodes if e["kind"] == kind
                                             and e["forward_return"] is None)}
    tr = [e for e in episodes if e["kind"] == "trough"
          and e["drawdown_from_12m_high"] is not None]
    low = float(sc["price_low_drawdown_pct"])
    out["troughs"]["at_price_low"] = sum(1 for e in tr
                                         if e["drawdown_from_12m_high"] <= -low)
    out["troughs"]["with_price"] = len(tr)
    cur_m, cur_v = sent[-1]
    from .derived import percentile_of  # noqa: PLC0415
    cur_dd = None
    if spx_daily:
        closes = [v for _, v in spx_daily]
        cur_dd = 100 * (closes[-1] / max(closes) - 1)
    out["current"] = {"month": cur_m, "value": cur_v,
                      "percentile_full": percentile_of([v for _, v in sent], cur_v),
                      "n_full": len(sent),
                      "spx_from_ath_pct": round(cur_dd, 4) if cur_dd is not None else None}
    out["caveat"] = sc["caveat"]
    return out


# ---------------------------------------------------------------------------
# GTM-9: the all-time-high base rates
# ---------------------------------------------------------------------------
def ath_flags(closes: list[tuple[str, float]]) -> list[bool]:
    """True where the close is above every prior close (the first close is not)."""
    out, hi = [], None
    for _, v in closes:
        out.append(hi is not None and v > hi)
        hi = v if hi is None else max(hi, v)
    return out


def ath_stats(closes: list[tuple[str, float]], cfg: Optional[dict] = None,
              start: Optional[str] = None, end: Optional[str] = None) -> dict:
    """Over sessions in [start, end] (the whole series when unset): the count of
    all-time highs, their share of sessions, the share that became floors (the
    scan's definition: never afterwards closed `floor_drawdown_pct` or more
    below, to the end of the data) and the share followed by another within
    `within_sessions` sessions."""
    cfg = cfg or config()
    a = cfg["all_time_highs"]
    if not closes:
        return {"state": "absent", "absent_reason": "the S&P 500's closes are not stored"}
    c = sorted(closes)
    flags = ath_flags(c)
    vals = [v for _, v in c]
    suffix_min = [math.inf] * (len(vals) + 1)
    for i in range(len(vals) - 1, -1, -1):
        suffix_min[i] = min(vals[i], suffix_min[i + 1])
    lim = 1 - float(a["floor_drawdown_pct"]) / 100
    w = int(a["within_sessions"])
    idx = [i for i, (d, _) in enumerate(c)
           if (start is None or d >= start) and (end is None or d <= end)]
    aths = [i for i in idx if flags[i]]
    floors = sum(1 for i in aths if suffix_min[i + 1] > vals[i] * lim)
    week = sum(1 for i in aths if any(flags[j] for j in range(i + 1, min(i + 1 + w, len(c)))))
    n_s = len(idx)
    return {"state": "ok", "start": c[idx[0]][0] if idx else start,
            "end": c[idx[-1]][0] if idx else end, "sessions": n_s,
            "ath_count": len(aths),
            "share_of_sessions": round(100 * len(aths) / n_s, 4) if n_s else None,
            "floors": floors,
            "share_floors": round(100 * floors / len(aths), 4) if aths else None,
            "followed_within": week,
            "share_followed_within": round(100 * week / len(aths), 4) if aths else None,
            "last_ath": c[aths[-1]][0] if aths else None,
            "data_end": c[-1][0],
            "definition": a["definition_source"]}


def ath_base_rate(closes: list[tuple[str, float]], cfg: Optional[dict] = None) -> dict:
    """The scan's comparison sample (1988 to 2025) over our own closes."""
    cfg = cfg or config()
    s = cfg["all_time_highs"]["sample"]
    out = ath_stats(closes, cfg, s["start"], s["end"])
    out["sample"] = dict(s)
    return out


def ath_year_to_date(closes: list[tuple[str, float]], day: str,
                     cfg: Optional[dict] = None) -> dict:
    return ath_stats([x for x in closes if x[0] <= day], cfg, f"{day[:4]}-01-01", day)


# ---------------------------------------------------------------------------
# GTM-1: the inflection-points table's "today" row
# ---------------------------------------------------------------------------
def inflection_today(st, cutoff: str) -> dict:
    """The level from the tape, the 10-year from its series, the dividend yield
    from Shiller's stored dividend and price where both are stored, and the
    forward P/E, which no writer stores."""
    lvl = latest(points(st, "yfinance.mkt_gspc", cutoff))
    y10 = latest(points(st, "fred.yield_10y", cutoff))
    p = by_month(points(st, "shiller.sp_price", cutoff))
    d = by_month(points(st, "shiller.sp_dividend", cutoff))
    both = sorted(m for m in d if m in p and p[m] > 0)
    dy = None
    if both:
        m = both[-1]
        dy = {"value": round(100 * d[m] / p[m], 4), "month": m,
              "source": f"Shiller, trailing dividend over price, {m}"}
    return {"level": {"value": lvl[1], "day": lvl[0]} if lvl else None,
            "yield_10y": {"value": y10[1], "day": y10[0]} if y10 else None,
            "dividend_yield": dy,
            "forward_pe": None,
            "forward_pe_reason": "no writer stores the S&P 500's forward earnings"}


# ---------------------------------------------------------------------------
# GTM-13: the fixed-income scenario table
# ---------------------------------------------------------------------------
def durations(path: Optional[Path] = None) -> dict[str, dict]:
    with open(path or REFERENCE_PATH, encoding="utf-8") as fh:
        return (yaml.safe_load(fh) or {}).get("durations") or {}


def total_return_index(closes: list[tuple[str, float]],
                       dividends: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """[(day, daily total return)] -- (P_t + D_t) / P_{t-1} - 1, D on its ex-day."""
    dv = dict(dividends)
    out = []
    for (d0, p0), (d1, p1) in zip(closes, closes[1:]):
        if p0 > 0:
            out.append((d1, (p1 + dv.get(d1, 0.0)) / p0 - 1))
    return out


def ytd_total_return(closes: list[tuple[str, float]],
                     dividends: list[tuple[str, float]], day: str) -> Optional[float]:
    """Percent, from the last close of the prior year to `day`'s close."""
    c = [x for x in closes if x[0] <= day]
    base = [i for i, (d, _) in enumerate(c) if d < f"{day[:4]}-01-01"]
    if not base or base[-1] == len(c) - 1:
        return None
    acc = 1.0
    for _, r in total_return_index(c[base[-1]:], dividends):
        acc *= 1 + r
    return 100 * (acc - 1)


def scenario_returns(duration: Optional[float], shift_bp: int) -> dict:
    """The price return under -shift and +shift, percent: -duration x change."""
    if duration is None:
        return {"down": None, "up": None}
    ch = shift_bp / 100.0
    return {"down": round(duration * ch, 4), "up": round(-duration * ch, 4)}


def guide_ytd(row: Optional[dict], token: str) -> Optional[str]:
    """The Guide's year-to-date return for one sector, read off the stored
    figure's text ('2y +0.3%, 10y −5.3%, ...'); never recomputed."""
    if not row or not token:
        return None
    m = re.search(r"(?:^|,\s*)" + re.escape(token) + r"\s+([+\-−][\d.]+%)", row["value"])
    return m.group(1) if m else None


def fixed_income(st, cutoff: str, cfg: Optional[dict] = None,
                 dur: Optional[dict] = None, guide: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    fi = cfg["fixed_income"]
    dur = durations() if dur is None else dur
    win = int(fi["window_sessions"])
    rate = dict(points(st, fi["rate_key"], cutoff))
    eq_c = points(st, fi["equity_key"], cutoff)
    eq_tr = dict(total_return_index(eq_c, points(st, fi["equity_key"] + "_dividend", cutoff)))
    day = cutoff[:10]
    rows = []
    for s in fi["sectors"]:
        r = {"sector": s["sector"], "proxy": s.get("proxy"),
             "guide_ytd": guide_ytd(guide, s.get("guide"))}
        if s.get("yield_key"):
            y = latest(points(st, s["yield_key"], cutoff))
            r["yield"] = ({"value": y[1], "day": y[0], "label": s["yield_label"]}
                          if y else None)
        else:
            r["yield"] = None
        r["yield_reason"] = None if r["yield"] else NOT_STORED
        if not s.get("proxy"):
            r.update({"state": NO_PROXY, "ytd": None, "duration": None,
                      "corr_rate": None, "corr_equity": None,
                      "scenario": scenario_returns(None, fi["shift_bp"])})
            rows.append(r)
            continue
        c = points(st, s["proxy_key"], cutoff)
        dv = points(st, s["proxy_key"] + "_dividend", cutoff)
        d = dur.get(s["proxy"]) or {}
        years = d.get("years")
        r["state"] = "ok" if c else NOT_STORED
        r["ytd"] = ytd_total_return(c, dv, day) if c else None
        r["duration"] = float(years) if years is not None else None
        r["duration_source"] = (f"{d.get('source')}, {d.get('as_of')}" if years is not None
                                else "no duration in config/instrument_reference.yaml")
        tr = total_return_index(c, dv)[-win:]
        days = sorted(rate)
        prev = {days[i]: days[i - 1] for i in range(1, len(days))}
        xs_r, ys_r, xs_e, ys_e = [], [], [], []
        for dd, ret in tr:
            if dd in rate and dd in prev:
                xs_r.append(ret)
                ys_r.append(100 * (rate[dd] - rate[prev[dd]]))
            if dd in eq_tr:
                xs_e.append(ret)
                ys_e.append(eq_tr[dd])
        cr, ce = pearson(xs_r, ys_r), pearson(xs_e, ys_e)
        r["corr_rate"] = round(cr, 4) if cr is not None else None
        r["corr_equity"] = round(ce, 4) if ce is not None else None
        r["n_rate"], r["n_equity"] = len(xs_r), len(xs_e)
        r["scenario"] = scenario_returns(r["duration"], fi["shift_bp"])
        rows.append(r)
    return {"state": "ok", "day": day, "window_sessions": win,
            "shift_bp": fi["shift_bp"], "rows": rows}


# ---------------------------------------------------------------------------
# GTM-15: the effective tariff rate
# ---------------------------------------------------------------------------
def tariff_series(customs: list[tuple[str, float]],
                  imports: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """[(quarter start, percent)]: the quarter's customs receipts (billions, SAAR)
    over four times its three months of goods imports (millions)."""
    imp = by_month(imports)
    out = []
    for d, v in sorted(customs):
        q = d[:7]
        ms = [q, _month_add(q, 1), _month_add(q, 2)]
        if all(m in imp for m in ms):
            annual_bn = 4 * sum(imp[m] for m in ms) / 1000.0
            if annual_bn > 0:
                out.append((d, 100 * v / annual_bn))
    return out


def dual_percentiles(series: list[tuple[str, float]], short_days: int = 1826) -> dict:
    """The latest value's percentile over five years and over the full stored
    history, each with its n (derived.percentile_of, the one definition)."""
    from .derived import percentile_of  # noqa: PLC0415
    if not series:
        return {"latest": None}
    d, v = series[-1]
    cut = (dt.date.fromisoformat(d) - dt.timedelta(days=short_days)).isoformat()
    short = [x for dd, x in series if dd > cut]
    return {"latest": v, "day": d,
            "pctile_5y": percentile_of(short, v), "n_5y": len(short),
            "pctile_full": percentile_of([x for _, x in series], v),
            "n_full": len(series), "since": series[0][0]}


def tariff(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    t = cfg["tariff"]
    s = tariff_series(points(st, t["customs_key"], cutoff),
                      points(st, t["imports_key"], cutoff))
    if not s:
        return {"state": "absent", "absent_reason":
                f"{t['customs_key']} and {t['imports_key']} are not stored for a "
                f"common quarter"}
    return {"state": "ok", "frequency": "quarterly", "series_ids":
            ["B235RC1Q027SBEA", "BOPGIMP"], **dual_percentiles(s)}


def monthly_tariff_series(gross: list[tuple[str, float]],
                          imports: list[tuple[str, float]],
                          smooth: int = 3) -> list[dict]:
    """[{month, rate, rate_smooth}], percent: the month's customs duties collected
    (MTS, dollars, gross) over the month's goods imports (BOPGIMP, millions); the
    smoothed rate is the last `smooth` months' duties over their imports."""
    g = {d[:7]: v for d, v in gross}
    imp = by_month(imports)
    months = sorted(m for m in g if m in imp and imp[m] > 0)
    out = []
    for i, m in enumerate(months):
        r = {"month": m, "rate": 100 * g[m] / (imp[m] * 1e6), "rate_smooth": None}
        win = [_month_add(m, -k) for k in range(smooth)]
        if all(x in g and x in imp for x in win):
            r["rate_smooth"] = 100 * sum(g[x] for x in win) / (sum(imp[x] for x in win) * 1e6)
        out.append(r)
    return out


def tariff_monthly(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """GTM-15 monthly (ruling 3 of 17 Oct 2026): the MTS's gross customs duties
    over the month's goods imports, with the month's refunds beside it."""
    cfg = cfg or config()
    t = cfg["tariff_monthly"]
    s = monthly_tariff_series(points(st, t["gross_key"], cutoff),
                              points(st, t["imports_key"], cutoff),
                              int(t["smooth_months"]))
    if not s:
        return {"state": "absent", "absent_reason":
                f"{t['gross_key']} and {t['imports_key']} are not stored for a "
                f"common month"}
    pts = [(f"{r['month']}-01", r["rate"]) for r in s]
    ref = {d[:7]: v for d, v in points(st, t["refunds_key"], cutoff)}
    last = s[-1]
    return {"state": "ok", "frequency": "monthly", "month": last["month"],
            "rate_smooth": last["rate_smooth"], "smooth_months": int(t["smooth_months"]),
            "refunds": ref.get(last["month"]),
            "series_ids": ["MTS Table 4 (Customs Duties, gross)", "BOPGIMP"],
            **dual_percentiles(pts)}


# ---------------------------------------------------------------------------
# GTM-12: what the Factor IV panel lacks
# ---------------------------------------------------------------------------
def share_series(num: list[tuple[str, float]], den: list[tuple[str, float]],
                 sign: int = 1) -> list[tuple[str, float]]:
    """[(period, percent)]: the numerator over the denominator for each period
    both carry (the same observed_at)."""
    dd = dict(den)
    return [(d, 100 * sign * v / dd[d]) for d, v in num if dd.get(d)]


def federal(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """Each row's latest level, its period and its share -- of federal current
    expenditures on the national-accounts basis, of net outlays on the budget's
    -- with the share's percentile over `short_years` and the full history. The
    deficit is printed positive (sign -1 on FRED's surplus-or-deficit)."""
    cfg = cfg or config()
    f = cfg["federal"]
    short = int(round(365.25 * int(f["short_years"])))
    den = {"nipa": points(st, f["nipa_denominator"], cutoff),
           "budget": points(st, f["budget_denominator"], cutoff)}
    rows = []
    for r in f["rows"]:
        sign = int(r.get("sign", 1))
        p = points(st, r["key"], cutoff)
        row = {"id": r["id"], "label": r["label"], "series": r["series"],
               "key": r["key"], "basis": r["basis"], "latest": None}
        if not p:
            row["reason"] = f"{r['key']} ({r['series']}) is not stored"
            rows.append(row)
            continue
        row["latest"], row["day"] = sign * p[-1][1], p[-1][0]
        if r["basis"] == "gdp":
            shares = [(d, sign * v) for d, v in p]
            row["share_of"] = "GDP"
        else:
            shares = share_series(p, den[r["basis"]], sign)
            row["share_of"] = ("current expenditures" if r["basis"] == "nipa"
                               else "net outlays")
        sh = dual_percentiles(shares, short) if shares else {"latest": None}
        row["share"] = sh.get("latest") if shares and shares[-1][0] == row["day"] else None
        row.update({k: sh.get(k) for k in ("pctile_5y", "n_5y", "pctile_full",
                                           "n_full", "since")})
        rows.append(row)
    return {"state": "ok" if any(r["latest"] is not None for r in rows) else "absent",
            "rows": rows, "short_years": int(f["short_years"]),
            "cbo_path": list(f["cbo_path"])}


# ---------------------------------------------------------------------------
# GTM-21: the debt-service ratio
# ---------------------------------------------------------------------------
def dsr(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    c = cfg["dsr"]
    rows = []
    for k in c["keys"]:
        p = points(st, k["key"], cutoff)
        rows.append({"key": k["key"], "label": k["label"],
                     **dual_percentiles(p, int(c["short_window_days"]))})
    return {"state": "ok" if any(r["latest"] is not None for r in rows) else "absent",
            "rows": rows}


# ---------------------------------------------------------------------------
# Everything, once per cutoff
# ---------------------------------------------------------------------------
def shiller_months(st, cutoff: str) -> dict:
    return {k: by_month(points(st, f"shiller.{k}", cutoff))
            for k in ("sp_price", "sp_dividend", "cpi", "gs10")}


def build(st, cutoff: str, db_path: Optional[str] = None,
          cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    # The sourced figures live beside the observations (scan_figures in the same
    # database): read from the store's own file, never from a default path a
    # caller did not name.
    db_path = db_path or (str(st.path) if getattr(st, "path", None) else None)
    src = sourced(cutoff, db_path, cfg) if db_path else {}
    sh = shiller_months(st, cutoff)
    gspc = points(st, "yfinance.mkt_gspc", cutoff)
    sent = points(st, "fred.uoM_sent", cutoff)
    return {
        "sourced": src,
        "inflection": {"today": inflection_today(st, cutoff)},
        "stock_bond": stock_bond_eras(sh["sp_price"], sh["sp_dividend"], sh["cpi"],
                                      sh["gs10"], cfg),
        "sentiment": sentiment_base_rate(sent, gspc, cfg),
        "ath": {"sample": ath_base_rate(gspc, cfg),
                "ytd": ath_year_to_date(gspc, cutoff[:10], cfg)},
        "fixed_income": fixed_income(st, cutoff, cfg, guide=src.get("gtm13.ytd")),
        "tariff": tariff(st, cutoff, cfg),
        "tariff_monthly": tariff_monthly(st, cutoff, cfg),
        "dsr": dsr(st, cutoff, cfg),
        "federal": federal(st, cutoff, cfg),
    }


def _main(argv: list[str]) -> int:
    import argparse  # noqa: PLC0415
    import json  # noqa: PLC0415
    from . import observations, session  # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.gtm")
    ap.add_argument("cmd", choices=["show", "check"])
    ap.add_argument("--db", default=None)
    ap.add_argument("--as-of", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "check":
        figs, refused = sourced_figures()
        print(f"{len(figs)} sourced figures declared and quoted; {len(refused)} refused")
        for r in refused:
            print(f"  REFUSED {r['metric']}: {r['reason']}")
        return 1 if refused else 0
    cut = a.as_of or session.utc_iso(timespec="microseconds")
    with observations.ObservationStore(a.db) as st:
        b = build(st, cut, a.db)
    b.pop("sourced", None)
    print(json.dumps(b, indent=2, default=str, sort_keys=True)[:20000])
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_main(sys.argv[1:]))
