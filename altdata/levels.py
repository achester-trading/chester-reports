"""
The level list: computed once per edition, read by the prose and the charts.
(docs/briefs/reporting-stack-brief-2026-10-02.md 2.2, Tranche T1)

    from altdata import levels
    book = levels.compute("2026-10-01", exposure_rows, store=bar_store)

ONE OBJECT, TWO READERS. The chart draws only levels in this list; the prose names
only levels in this list; the gate checks both against the same object. Each level
carries its label, value, source and as-of, and a STATUS against the session --
held, broke or untested -- by a declared rule (`status_of`), so "the 20-day held"
is a computed fact and never the model's reading of a chart.

Per tape instrument: prior close; session high, low and VWAP (from the 5-minute
bars); week high and low; the 20-, 50- and 200-day averages; the 52-week high and
low with the drawdown from the high; GEX flip, call wall, put wall and max pain
from the dealer profile where one exists; the 40-week and the 10- and 20-month
averages for the long frames. A level that cannot be computed is absent from the
list with its reason, never zero.

THE FLAT ROW. `row` carries the same values under field names the label audit
knows (gamma_flip, call_wall, ma_20d, week_high ...) beside the instrument's
symbol, so "the 20-day at 640.30" in a sentence is checked against SPY's 20-day
and nothing else.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from . import bars as bars_mod, session

# How a level type is labelled in prose and on a chart, in list order.
LEVEL_TYPES = (
    ("prior_close", "prior close"), ("session_high", "session high"),
    ("session_low", "session low"), ("vwap", "VWAP"),
    ("week_high", "week high"), ("week_low", "week low"),
    ("ma_20d", "20-day average"), ("ma_50d", "50-day average"),
    ("ma_200d", "200-day average"), ("high_52w", "52-week high"),
    ("low_52w", "52-week low"), ("gamma_flip", "gamma flip"),
    ("call_wall", "call wall"), ("put_wall", "put wall"),
    ("max_pain", "max pain"), ("ma_40w", "40-week average"),
    ("ma_10m", "10-month average"), ("ma_20m", "20-month average"))
LABEL = dict(LEVEL_TYPES)
DEALER_FIELDS = ("gamma_flip", "call_wall", "put_wall", "max_pain")


def _mean(xs: list[float]) -> Optional[float]:
    return sum(xs) / len(xs) if xs else None


def _week_start(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=d.weekday())


def status_of(level: float, prior_close: Optional[float], o: dict,
              tol_bps: float) -> str:
    """held | broke | untested -- the declared rule (brief 2.1 rule 5).

    A level below the prior close is SUPPORT: it BROKE if the session closed
    below it, HELD if the low came within the tolerance of it and the close
    stayed above. A level above is RESISTANCE, mirrored. Untouched is untested.
    """
    if prior_close is None or not o:
        return "untested"
    lo, hi, c = o.get("low"), o.get("high"), o.get("close")
    if lo is None or hi is None or c is None:
        return "untested"
    tol = abs(level) * tol_bps / 1e4
    if level <= prior_close:
        if c < level:
            return "broke"
        return "held" if lo <= level + tol else "untested"
    if c > level:
        return "broke"
    return "held" if hi >= level - tol else "untested"


def _monthly_closes(daily: list[dict]) -> list[float]:
    out: dict[str, float] = {}
    for r in daily:
        out[str(r["observed_at"])[:7]] = r["close"]
    return list(out.values())


def _weekly_closes(daily: list[dict]) -> list[float]:
    out: dict[str, float] = {}
    for r in daily:
        d = dt.date.fromisoformat(str(r["observed_at"])[:10])
        out[_week_start(d).isoformat()] = r["close"]
    return list(out.values())


def instrument(spec: dict, day: str, store: bars_mod.BarStore,
               dealer: Optional[dict] = None, as_of: Optional[str] = None,
               tol_bps: float = 25.0, complete_share: float = 0.9) -> dict:
    """The level list for one tape instrument on `day`."""
    iid, kind = spec["id"], spec.get("kind", "price")
    daily = bars_mod.daily(store, iid, day, as_of)
    intra = bars_mod.intraday(store, iid, day, as_of, complete_share)
    today = daily[-1] if daily and str(daily[-1]["observed_at"])[:10] == day else None
    hist = daily[:-1] if today else daily
    closes = [r["close"] for r in daily]
    out: dict[str, Any] = {"id": iid, "label": spec.get("label") or iid,
                           "symbol": spec.get("dealer") or spec.get("label") or iid,
                           "kind": kind, "session": day, "levels": [],
                           "absent": {}, "intraday": {k: intra[k] for k in
                                                      ("n", "expected", "complete",
                                                       "reason")}}
    vals: dict[str, Optional[float]] = {k: None for k, _ in LEVEL_TYPES}
    src: dict[str, str] = {}
    prior = hist[-1]["close"] if hist else None
    vals["prior_close"], src["prior_close"] = prior, "bars 1d"
    if today:
        out["ohlc"] = {k: today[k] for k in ("open", "high", "low", "close")}
    if intra["bars"]:
        b = intra["bars"]
        vals["session_high"] = max(x["high"] for x in b)
        vals["session_low"] = min(x["low"] for x in b)
        src["session_high"] = src["session_low"] = "bars 5m"
        vol = sum((x.get("volume") or 0) for x in b)
        if intra["complete"] and vol > 0:
            vals["vwap"] = sum((x["high"] + x["low"] + x["close"]) / 3
                               * (x.get("volume") or 0) for x in b) / vol
            src["vwap"] = "bars 5m"
        elif not intra["complete"]:
            out["absent"]["vwap"] = intra["reason"]
        else:
            out["absent"]["vwap"] = "no volume on the session's bars"
    elif today:
        vals["session_high"], vals["session_low"] = today["high"], today["low"]
        src["session_high"] = src["session_low"] = "bars 1d"
        out["absent"]["vwap"] = intra["reason"] or "no 5-minute bars"
    d = dt.date.fromisoformat(day)
    wk = [r for r in daily if _week_start(dt.date.fromisoformat(
        str(r["observed_at"])[:10])) == _week_start(d)]
    if wk:
        vals["week_high"] = max(r["high"] for r in wk)
        vals["week_low"] = min(r["low"] for r in wk)
        src["week_high"] = src["week_low"] = "bars 1d"
    for n, key in ((20, "ma_20d"), (50, "ma_50d"), (200, "ma_200d")):
        if len(closes) >= n:
            vals[key], src[key] = _mean(closes[-n:]), "bars 1d"
        else:
            out["absent"][key] = f"{len(closes)} daily closes stored, {n} needed"
    yr = [r for r in daily if str(r["observed_at"])[:10] >
          (d - dt.timedelta(days=365)).isoformat()]
    if len(yr) >= 200:
        vals["high_52w"] = max(r["high"] for r in yr)
        vals["low_52w"] = min(r["low"] for r in yr)
        src["high_52w"] = src["low_52w"] = "bars 1d"
    else:
        out["absent"]["high_52w"] = f"{len(yr)} sessions in the last year stored"
    wkc, mc = _weekly_closes(daily), _monthly_closes(daily)
    for n, key, series in ((40, "ma_40w", wkc), (10, "ma_10m", mc), (20, "ma_20m", mc)):
        if len(series) >= n:
            vals[key], src[key] = _mean(series[-n:]), "bars 1d resampled"
        else:
            out["absent"][key] = f"{len(series)} periods stored, {n} needed"
    for k in DEALER_FIELDS:
        v = (dealer or {}).get(k)
        if isinstance(v, (int, float)):
            vals[k], src[k] = float(v), f"dealer profile {spec.get('dealer')}"
        elif spec.get("dealer"):
            out["absent"][k] = "not in the session's dealer profile"
    ohlc = out.get("ohlc") or ({"low": vals["session_low"], "high":
                                vals["session_high"],
                                "close": closes[-1] if today else None})
    as_of_day = str(today["observed_at"])[:10] if today else (
        str(daily[-1]["observed_at"])[:10] if daily else None)
    row: dict[str, Any] = {"symbol": out["symbol"]}
    for key, label in LEVEL_TYPES:
        v = vals.get(key)
        if v is None:
            continue
        v = round(float(v), 4 if kind == "yield" else 2)
        lv = {"type": key, "label": label, "value": v, "source": src.get(key),
              "as_of": as_of_day}
        if key not in ("prior_close", "session_high", "session_low"):
            lv["status"] = status_of(v, prior, ohlc, tol_bps)
        out["levels"].append(lv)
        row[key] = v
    if vals["high_52w"] and closes:
        row["drawdown_52w_pct"] = round(100.0 * (closes[-1] / vals["high_52w"] - 1), 2)
    # The frame: the session's move, week to date, month to date, in the
    # instrument's unit -- bp for a yield, percent for a price.
    last = closes[-1] if today else None
    frame: dict[str, Any] = {"last": last, "as_of": as_of_day}

    def move(a, b):
        if a is None or b is None or not b:
            return None
        return round((a - b) * 100.0, 1) if kind == "yield" else \
            round(100.0 * (a / b - 1.0), 2)
    unit = "bps" if kind == "yield" else "pct"
    wk_prior = [r for r in hist if _week_start(dt.date.fromisoformat(
        str(r["observed_at"])[:10])) < _week_start(d)]
    mo_prior = [r for r in hist if str(r["observed_at"])[:7] < day[:7]]
    frame[f"session_change_{unit}"] = move(last, prior)
    frame[f"wtd_change_{unit}"] = move(last, wk_prior[-1]["close"] if wk_prior else None)
    frame[f"mtd_change_{unit}"] = move(last, mo_prior[-1]["close"] if mo_prior else None)
    out["frame"] = frame
    out["row"] = {**row, **{k: v for k, v in frame.items() if v is not None}}
    return out


def compute(day: str, exposure: Optional[list[dict]] = None,
            store: Optional[bars_mod.BarStore] = None, as_of: Optional[str] = None,
            tol_bps: float = 25.0) -> dict:
    """The edition's level list: every tape instrument, one object."""
    cfg = bars_mod.load_config()
    share = float((cfg.get("bars") or {}).get("complete_share") or 0.9)
    by_sym = {r.get("symbol"): r for r in exposure or []}
    own = store is None
    st = store or bars_mod.BarStore()
    try:
        insts = [instrument(t, day, st, by_sym.get(t.get("dealer")), as_of,
                            tol_bps, share)
                 for t in cfg.get("tape") or []]
    finally:
        if own:
            st.close()
    return {"session": day, "computed_at": session.utc_iso(),
            "config_version": cfg.get("version"), "instruments": insts}


def labelled(book: dict) -> list[tuple[str, str, float]]:
    """(instrument id, label, value) for every listed level -- what the chart
    and the prose may name."""
    return [(i["id"], lv["label"], lv["value"])
            for i in book.get("instruments") or [] for lv in i["levels"]]
