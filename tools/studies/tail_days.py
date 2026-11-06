"""Tail days 2016-2026: a condition replay, a two-sided tail base-rate table and a
vol-managed backtest. A STUDY, not a report.

    python tools/studies/tail_days.py [--out docs/studies/tail-days-2016-2026-data.md]
                                      [--cache DIR]

What it reads, and what it never touches
----------------------------------------
* Prices through the repo's yfinance fetcher, `altdata.sources.yfinance_source.
  _fetch_symbol()` at period "max": split-adjusted, dividend-UNadjusted closes with
  the dividends beside them, exactly as the store would hold them. An ETF's return
  here is total return, (close + dividend) / previous close - 1, computed from the
  two; an index's is its price return.
* FRED through the repo's FRED reader, `altdata.sources.fred._fetch_series()`, with
  the key from the one secrets loader; when no key is available, FRED's public
  fredgraph CSV. Each table names which was used.
* Nothing is written but the output Markdown. The point-in-time store, the CSV
  store, the regime module and every report are left alone: this script opens no
  database and imports no report code.

A series with no value on or before a row's date prints "gap"; nothing is
substituted for it (no proxy, no carry-forward beyond FRED's own holiday gaps of
at most five calendar days).

Point in time: every Part 1 figure is as of the close of its row's session. FRED
values are keyed by observation date (HY/IG OAS for a day are published the next
morning, so they were knowable at T, not at T's close; the table says so).
"""
from __future__ import annotations

import argparse
import io
import pickle
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

ET = ZoneInfo("America/New_York")

BEST = ["2025-04-09", "2020-03-24", "2020-03-13", "2020-04-06", "2020-03-26",
        "2020-03-17", "2022-11-10", "2018-12-26", "2020-03-10", "2020-03-02"]
WORST = ["2020-03-16", "2020-03-12", "2020-03-09", "2020-06-11", "2025-04-04",
         "2020-03-18", "2020-03-11", "2025-04-03", "2020-04-01", "2026-11-05"]
# Morningstar's figures as the study prints them (Morningstar US Market Index).
MSTAR = {"2025-04-09": 9.6, "2020-03-24": 9.5, "2020-03-13": 9.0, "2020-04-06": 7.2,
         "2020-03-26": 6.2, "2020-03-17": 5.8, "2022-11-10": 5.7, "2018-12-26": 5.0,
         "2020-03-10": 4.8, "2020-03-02": 4.4,
         "2020-03-16": -12.3, "2020-03-12": -9.6, "2020-03-09": -7.8,
         "2020-06-11": -6.0, "2025-04-04": -5.9, "2020-03-18": -5.7,
         "2020-03-11": -5.1, "2025-04-03": -5.0, "2020-04-01": -4.6,
         "2026-11-05": -4.4}
OFFSETS = [1, 5, 20]

SECTORS = ["XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]
INDEX_SYMS = ["^GSPC", "^VIX3M", "^VVIX", "^MOVE"]
CHECK_SYMS = ["^IXIC", "SPHB", "SPLV"]          # §4's spot checks only
ETF_SYMS = ["SPY", "RSP"] + SECTORS
EXTRA_SYMS = ["QQQ"]                              # Part 5 only
FRED_IDS = ["VIXCLS", "BAMLH0A0HYM2", "BAMLC0A0CM", "DGS10", "T10Y2Y", "DTWEXBGS",
            "DTB3", "BAA10Y"]                     # DTB3: Part 6; BAA10Y: Part 7
EBP_URL = "https://www.federalreserve.gov/econres/notes/feds-notes/ebp_csv.csv"

FRED_MAX_FILL_DAYS = 5     # FRED holiday gaps; no longer carry-forward than this

# Outside the repo and never committed: later runs read every pull from here.
DEFAULT_CACHE = Path.home() / ".cache" / "chester-study" / "tail_days"


# --------------------------------------------------------------------------- data
class Data:
    def __init__(self, cache: Path | None):
        self.cache = cache
        self.px: dict[str, pd.DataFrame] = {}      # close, ret, volume, high, low
        self.fred: dict[str, pd.Series] = {}
        self.fred_via: dict[str, str] = {}
        self.errors: dict[str, str] = {}
        self.ebp: pd.DataFrame | None = None
        self.generated = datetime.now(ET)
        self.pulled: dict[str, datetime] = {}      # name -> instant the pull was made
        self.pulled_at = self.generated

    def _cached(self, name, fn):
        if self.cache:
            p = self.cache / f"{name.replace('^', '_')}.pkl"
            if p.exists():
                self.pulled[name] = datetime.fromtimestamp(p.stat().st_mtime, ET)
                return pickle.loads(p.read_bytes())
            v = fn()
            self.cache.mkdir(parents=True, exist_ok=True)
            p.write_bytes(pickle.dumps(v))
            self.pulled[name] = datetime.now(ET)
            return v
        self.pulled[name] = datetime.now(ET)
        return fn()

    def load(self):
        from altdata.sources import yfinance_source as yfs
        for sym in INDEX_SYMS + ETF_SYMS + CHECK_SYMS + EXTRA_SYMS:
            try:
                parsed = self._cached(f"yf_{sym}", lambda s=sym: yfs._fetch_symbol(s, period="max"))
            except Exception as exc:                            # noqa: BLE001
                self.errors[sym] = f"{type(exc).__name__}: {exc}"
                continue
            close = pd.Series(dict(parsed["closes"]), dtype=float)
            close.index = pd.to_datetime(close.index)
            close = close.sort_index()
            close = close[close > 0]
            div = pd.Series(dict(parsed.get("dividends") or []), dtype=float)
            div.index = pd.to_datetime(div.index)
            div = div.reindex(close.index).fillna(0.0)
            vol = pd.Series(dict(parsed.get("volumes") or []), dtype=float)
            vol.index = pd.to_datetime(vol.index)
            vol = vol.reindex(close.index)
            ret = (close + div) / close.shift(1) - 1.0
            hl = {}
            for k_ in ("highs", "lows"):
                s_ = pd.Series(dict(parsed.get(k_) or []), dtype=float)
                s_.index = pd.to_datetime(s_.index)
                hl[k_] = s_.reindex(close.index)
            self.px[sym] = pd.DataFrame({"close": close, "ret": ret, "volume": vol,
                                         "high": hl["highs"], "low": hl["lows"]})
        for fid in FRED_IDS:
            try:
                s, via = self._cached(f"fred_{fid}", lambda f=fid: _fred(f))
                # fredgraph's CSV now leaves holidays blank, which parse as NaN: drop them, so
                # an as-of read carries the last real value and "n observations" counts values.
                self.fred[fid], self.fred_via[fid] = s.dropna(), via
            except Exception as exc:                            # noqa: BLE001
                self.errors[fid] = f"{type(exc).__name__}: {exc}"
        try:
            self.ebp = self._cached("fed_EBP", _ebp)
        except Exception as exc:                                # noqa: BLE001
            self.errors["EBP"] = f"{type(exc).__name__}: {exc}"
        if self.pulled:
            self.pulled_at = min(self.pulled.values())

    def first_last(self, name):
        s = self.px[name]["close"] if name in self.px else self.fred.get(name)
        if s is None or s.dropna().empty:
            return "gap", "gap"
        s = s.dropna()
        return s.index[0].date().isoformat(), s.index[-1].date().isoformat()


def _fred(fid: str) -> tuple[pd.Series, str]:
    rows, via = None, None
    try:
        from altdata.sources import fred as fred_mod
        key = fred_mod._get_key()
        rows = fred_mod._fetch_series(fid, key)
        via = "FRED API (altdata.sources.fred)"
    except Exception:                                           # noqa: BLE001
        rows = None
    if rows is None:
        import requests
        r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv",
                         params={"id": fid}, timeout=60,
                         headers={"User-Agent": "chester-reports study (github.com/achester-trading)"})
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        df.columns = ["date", "value"]
        rows = [(d, None if v in (".", "") else float(v)) for d, v in zip(df["date"], df["value"])]
        via = "FRED fredgraph CSV"
    s = pd.Series({pd.Timestamp(d): v for d, v in rows if v is not None}, dtype=float).sort_index()
    return s, via


def _ebp() -> pd.DataFrame:
    """The Federal Reserve's GZ spread and excess bond premium, monthly (FEDS Notes CSV)."""
    import requests
    r = requests.get(EBP_URL, timeout=60,
                     headers={"User-Agent": "chester-reports study (github.com/achester-trading)"})
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date").sort_index()


# ----------------------------------------------------------------------- helpers
def fmt(v, nd=2, pct=False, sign=False):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return "gap"
    s = f"{v:+.{nd}f}" if sign else f"{v:.{nd}f}"
    return s + ("%" if pct else "")


def asof(s: pd.Series, day: pd.Timestamp, max_days=FRED_MAX_FILL_DAYS):
    """Value on `day`, or the last before it within max_days calendar days."""
    if s is None or s.empty:
        return np.nan
    sub = s.loc[:day]
    if sub.empty or (day - sub.index[-1]).days > max_days:
        return np.nan
    return float(sub.iloc[-1])


def asof_shift(s: pd.Series, day: pd.Timestamp, k: int):
    """Value k observations of the series before the as-of value on `day`."""
    if s is None or s.empty:
        return np.nan
    sub = s.loc[:day]
    if len(sub) <= k or (day - sub.index[-1]).days > FRED_MAX_FILL_DAYS:
        return np.nan
    return float(sub.iloc[-1 - k])


# ------------------------------------------------------------------ Part 1 rows
def conditions(d: Data, day: pd.Timestamp) -> dict:
    g = d.px["^GSPC"]
    i = g.index.get_loc(day)
    row = {}
    row["SPX close"] = g["close"].iloc[i]
    row["SPX ret %"] = g["ret"].iloc[i] * 100
    hi = g["close"].iloc[max(0, i - 251): i + 1].max()
    row["DD from 252d high %"] = (g["close"].iloc[i] / hi - 1) * 100
    lr = np.log1p(g["ret"].iloc[i - 19: i + 1])
    rv = lr.std(ddof=1) * np.sqrt(252) * 100
    row["RV20 %"] = rv
    row["|r|>2% days /20"] = int((g["ret"].iloc[i - 19: i + 1].abs() > 0.02).sum())
    vix = asof(d.fred.get("VIXCLS"), day)
    row["VIX"] = vix
    row["VIX - RV20"] = vix - rv
    v3m = d.px.get("^VIX3M")
    v3 = asof(v3m["close"], day, 0) if v3m is not None else np.nan
    row["VIX/VIX3M"] = vix / v3 if v3 == v3 and vix == vix else np.nan
    vv = d.px.get("^VVIX")
    row["VVIX"] = asof(vv["close"], day, 0) if vv is not None else np.nan
    hy = d.fred.get("BAMLH0A0HYM2")
    hyl = asof(hy, day)
    row["HY OAS bp"] = hyl * 100
    row["HY 20d chg bp"] = (hyl - asof_shift(hy, day, 20)) * 100
    row["IG OAS bp"] = asof(d.fred.get("BAMLC0A0CM"), day) * 100
    ten = d.fred.get("DGS10")
    tl = asof(ten, day)
    row["10y 3d chg bp"] = (tl - asof_shift(ten, day, 3)) * 100
    row["10y 5d chg bp"] = (tl - asof_shift(ten, day, 5)) * 100
    row["2s10s bp"] = asof(d.fred.get("T10Y2Y"), day) * 100
    mv = d.px.get("^MOVE")
    row["MOVE"] = asof(mv["close"], day, 0) if mv is not None else np.nan
    dx = d.fred.get("DTWEXBGS")
    dl = asof(dx, day)
    row["Broad $ 5d chg %"] = (dl / asof_shift(dx, day, 5) - 1) * 100
    # RSP/SPY 20d relative total return
    rel = np.nan
    if "RSP" in d.px and "SPY" in d.px:
        r20 = []
        for sym in ("RSP", "SPY"):
            rr = d.px[sym]["ret"].loc[:day]
            if len(rr) < 21 or rr.index[-1] != day or rr.iloc[-20:].isna().any():
                r20 = None
                break
            r20.append(np.prod(1 + rr.iloc[-20:]) - 1)
        if r20:
            rel = (r20[0] - r20[1]) * 100
    row["RSP-SPY 20d %"] = rel
    # sector share above 50d average
    above, n = 0, 0
    for sym in SECTORS:
        if sym not in d.px:
            continue
        c = d.px[sym]["close"].loc[:day]
        if len(c) < 50 or c.index[-1] != day:
            continue
        n += 1
        above += int(c.iloc[-1] > c.iloc[-50:].mean())
    row["Sectors >50d"] = f"{above}/{n}" if n else "gap"
    # SPY Amihud: mean(|r| / $vol) over 20d, percentile against its trailing 252
    row["SPY Amihud pctl"] = amihud_pctl(d, day)
    return row


_AMI = {}


def amihud_pctl(d: Data, day):
    if "SPY" not in d.px:
        return np.nan
    if "s" not in _AMI:
        p = d.px["SPY"]
        dv = p["close"] * p["volume"]
        ill = (p["ret"].abs() / dv.replace(0, np.nan))
        _AMI["s"] = ill.rolling(20, min_periods=20).mean()
    s = _AMI["s"].loc[:day].dropna()
    if len(s) < 252 or s.index[-1] != day:
        return np.nan
    w = s.iloc[-252:]
    return float((w <= w.iloc[-1]).mean() * 100)


COLS = ["SPX close", "SPX ret %", "DD from 252d high %", "RV20 %", "|r|>2% days /20",
        "VIX", "VIX - RV20", "VIX/VIX3M", "VVIX", "HY OAS bp", "HY 20d chg bp",
        "IG OAS bp", "10y 3d chg bp", "10y 5d chg bp", "2s10s bp", "MOVE",
        "Broad $ 5d chg %", "RSP-SPY 20d %", "Sectors >50d", "SPY Amihud pctl"]
NDP = {"SPX close": 2, "SPX ret %": 2, "DD from 252d high %": 1, "RV20 %": 1,
       "VIX": 2, "VIX - RV20": 1, "VIX/VIX3M": 3, "VVIX": 1, "HY OAS bp": 0,
       "HY 20d chg bp": 0, "IG OAS bp": 0, "10y 3d chg bp": 0, "10y 5d chg bp": 0,
       "2s10s bp": 0, "MOVE": 1, "Broad $ 5d chg %": 2, "RSP-SPY 20d %": 2,
       "SPY Amihud pctl": 0}
SHORT = {"SPX close": "SPX", "SPX ret %": "ret%", "DD from 252d high %": "DD%",
         "RV20 %": "RV20", "|r|>2% days /20": ">2%/20", "VIX": "VIX",
         "VIX - RV20": "VIX-RV", "VIX/VIX3M": "VIX/3M", "VVIX": "VVIX",
         "HY OAS bp": "HY", "HY 20d chg bp": "HYΔ20", "IG OAS bp": "IG",
         "10y 3d chg bp": "10yΔ3", "10y 5d chg bp": "10yΔ5", "2s10s bp": "2s10s",
         "MOVE": "MOVE", "Broad $ 5d chg %": "$Δ5%", "RSP-SPY 20d %": "RSP-SPY",
         "Sectors >50d": "Sect>50d", "SPY Amihud pctl": "Amihud pctl"}


def cell(col, v):
    if isinstance(v, str):
        return v
    if col == "|r|>2% days /20":
        return str(v)
    return fmt(v, NDP.get(col, 2))


# ------------------------------------------------------------------ Part 2
def part2(d: Data, out: list[str]):
    g = d.px["^GSPC"].loc["1950-01-03":].copy()
    r = g["ret"].dropna()
    c = g["close"].loc[r.index]
    n = len(r)
    first, last = r.index[0].date(), r.index[-1].date()
    out.append(f"Source: ^GSPC daily closes through `altdata.sources.yfinance_source._fetch_symbol` "
               f"(Yahoo Finance, price return), {first} to {last}, n = {n:,} sessions; "
               f"VIX from FRED VIXCLS ({d.fred_via.get('VIXCLS', 'gap')}). Pulled {d.pulled_at:%Y-%m-%d %H:%M} ET.\n")

    q10, q90 = r.quantile(0.10), r.quantile(0.90)
    bot_full = r <= q10
    top_full = r >= q90
    # rolling 10-year (2,520 sessions) thresholds, known before the day (window ends T-1)
    rq10 = r.rolling(2520, min_periods=2520).quantile(0.10).shift(1)
    rq90 = r.rolling(2520, min_periods=2520).quantile(0.90).shift(1)
    valid = rq10.notna()
    bot_roll = (r <= rq10) & valid
    top_roll = (r >= rq90) & valid
    out.append(f"Full-sample thresholds: bottom decile ≤ {q10*100:.2f}%, top decile ≥ {q90*100:.2f}%. "
               f"Rolling definition: the 10th/90th percentile of the trailing 2,520 sessions ending the day "
               f"before (point in time); first rolling day {r.index[valid.argmax()].date()}. "
               f"Latest rolling thresholds: ≤ {rq10.iloc[-1]*100:.2f}% / ≥ {rq90.iloc[-1]*100:.2f}%.\n")

    arr_idx = np.arange(n)

    def p_within(src: pd.Series, tgt: pd.Series, h: int, mask=None):
        s = src.values.copy()
        if mask is not None:
            s &= mask
        t = tgt.values
        hits, cnt = 0, 0
        for i in arr_idx[s]:
            if i + h >= n:
                continue
            cnt += 1
            hits += bool(t[i + 1: i + h + 1].any())
        return hits, cnt

    def base_within(tgt, h, mask):
        hits, cnt = 0, 0
        t = tgt.values
        for i in arr_idx[mask.values]:
            if i + h >= n:
                continue
            cnt += 1
            hits += bool(t[i + 1: i + h + 1].any())
        return hits, cnt

    out.append("### 2.1 Two-sided follow-through: P(opposite-tail day within h sessions)\n")
    out.append("h counts sessions after the conditioning day (T+1 … T+h). "
               "\"Any day\" is the unconditional rate over the same sample, for comparison.\n")
    out.append("| Definition | Conditioning day | n | h=1 | h=5 | h=10 | any day h=1 | any day h=5 | any day h=10 |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    for label, bot, top, mask in (("full sample", bot_full, top_full, pd.Series(True, index=r.index)),
                                  ("rolling 10y", bot_roll, top_roll, valid)):
        for cond, src, tgt in (("bottom-decile → top-decile", bot, top),
                               ("top-decile → bottom-decile", top, bot)):
            cells, base = [], []
            nn = None
            for h in (1, 5, 10):
                k, m = p_within(src, tgt, h)
                nn = m if nn is None else nn
                cells.append(f"{k/m*100:.1f}%" if m else "gap")
                kb, mb = base_within(tgt, h, mask)
                base.append(f"{kb/mb*100:.1f}%" if mb else "gap")
            out.append(f"| {label} | {cond} | {nn:,} | " + " | ".join(cells) + " | " + " | ".join(base) + " |")
    out.append("")

    fwd = {h: (c.shift(-h) / c - 1) * 100 for h in (1, 5, 20)}

    def dist_rows(lbl, mask):
        rows = []
        for h in (1, 5, 20):
            x = fwd[h][mask].dropna()
            if len(x) == 0:
                rows.append(f"| {lbl} | {h} | 0 | gap | gap | gap | gap | gap |")
                continue
            rows.append(f"| {lbl} | {h} | {len(x):,} | {x.mean():+.2f}% | {x.median():+.2f}% | "
                        f"{x.quantile(.1):+.2f}% | {x.quantile(.9):+.2f}% | {(x>0).mean()*100:.0f}% |")
        return rows

    out.append("### 2.2 Forward returns after a bottom-decile day (close T to close T+h)\n")
    out.append("| Conditioning | h | n | mean | median | 10th pct | 90th pct | share > 0 |")
    out.append("|---|---|---|---|---|---|---|---|")
    out += dist_rows("all days (baseline)", pd.Series(True, index=r.index))
    out += dist_rows("bottom decile, full sample", bot_full)
    out += dist_rows("bottom decile, rolling 10y", bot_roll)
    out += dist_rows("top decile, full sample", top_full)
    out.append("")

    vix = d.fred.get("VIXCLS")
    out.append("### 2.3 Bottom-decile days by VIX regime at T-1 (from 1990)\n")
    if vix is None or vix.empty:
        out.append("gap: VIXCLS unavailable.\n")
    else:
        vix_t1 = vix.reindex(r.index).ffill(limit=3).shift(1)
        since = r.index >= pd.Timestamp("1990-01-03")
        buckets = [("VIX < 20", vix_t1 < 20), ("VIX 20–30", (vix_t1 >= 20) & (vix_t1 < 30)),
                   ("VIX 30–45", (vix_t1 >= 30) & (vix_t1 < 45)), ("VIX > 45", vix_t1 >= 45)]
        out.append("Bottom decile on the full-sample threshold. VIX is FRED VIXCLS at the prior session's close.\n")
        out.append("| VIX at T-1 | h | n | mean | median | 10th pct | 90th pct | share > 0 |")
        out.append("|---|---|---|---|---|---|---|---|")
        for lbl, m in buckets:
            out += dist_rows(lbl, bot_full & m & since)
        out.append("")
        out.append("| VIX at T-1 | n bottom-decile days | P(top within 1) | P(top within 5) | P(top within 10) | share of all sessions in bucket that are bottom-decile |")
        out.append("|---|---|---|---|---|---|")
        for lbl, m in buckets:
            mm = (m & since).fillna(False)
            cells = []
            nn = 0
            for h in (1, 5, 10):
                k, cnt = p_within(bot_full, top_full, h, mask=mm.values)
                nn = cnt
                cells.append(f"{k/cnt*100:.1f}%" if cnt else "gap")
            share = (bot_full & mm).sum() / max(1, mm.sum()) * 100
            out.append(f"| {lbl} | {nn:,} | " + " | ".join(cells) + f" | {share:.1f}% |")
        out.append("")

    # clustering
    out.append("### 2.4 Clustering: share of top-decile days within 5 sessions (either side) of a bottom-decile day\n")

    def cluster(top, bot, lo=None, hi=None):
        idx = np.arange(n)
        sel = np.ones(n, bool)
        if lo is not None:
            sel &= (r.index >= pd.Timestamp(lo)) & (r.index <= pd.Timestamp(hi))
        t, b = top.values & sel, bot.values & sel
        bpos = idx[b]
        k = 0
        tops = idx[t]
        for i in tops:
            if np.any((np.abs(bpos - i) <= 5) & (bpos != i)):
                k += 1
        return k, len(tops)

    # unconditional benchmark: same count if top days were placed at random
    p_b = bot_full.mean()
    rnd = 1 - (1 - p_b) ** 10
    out.append("| Window | Definition | top-decile days | within ±5 of a bottom-decile day | share | if independent |")
    out.append("|---|---|---|---|---|---|")
    for lbl, lo, hi in (("1950–2026", None, None), ("Nov 2016–Nov 2026", "2016-11-07", "2026-11-05")):
        for dl, top, bot in (("full sample", top_full, bot_full), ("rolling 10y", top_roll, bot_roll)):
            k, m = cluster(top, bot, lo, hi)
            pb = bot[(r.index >= pd.Timestamp(lo or "1900")) & (r.index <= pd.Timestamp(hi or "2100"))].mean()
            ind = 1 - (1 - pb) ** 10
            out.append(f"| {lbl} | {dl} | {m:,} | {k:,} | {k/m*100:.1f}% | {ind*100:.1f}% |" if m else
                       f"| {lbl} | {dl} | 0 | gap | gap | gap |")
    out.append("")
    out.append("\"If independent\" is 1 − (1 − p)^10, the chance that a day has at least one bottom-decile day "
               "among its ten neighbours when bottom-decile days fall at random with that window's frequency p.\n")

    # Morningstar check
    out.append("### 2.5 Check: Morningstar's \"8 of the 10 best days within a week of a worst day\" (S&P 500, Nov 2016–Nov 2026)\n")
    w = r.loc["2016-11-07":"2026-11-05"]
    best10 = w.nlargest(10)
    worst10 = w.nsmallest(10)
    wpos = [r.index.get_loc(x) for x in worst10.index]
    out.append(f"Window {w.index[0].date()} to {w.index[-1].date()} (n = {len(w):,}). "
               "\"Within a week\" = within 5 sessions either side.\n")
    out.append("| Rank | ^GSPC best day | ret | nearest top-10 worst day | sessions apart | in Morningstar's best list? |")
    out.append("|---|---|---|---|---|---|")
    k = 0
    for rk, (dt, v) in enumerate(best10.items(), 1):
        i = r.index.get_loc(dt)
        dists = [(abs(i - j), r.index[j]) for j in wpos]
        dmin, near = min(dists)
        k += dmin <= 5
        out.append(f"| {rk} | {dt.date()} | {v*100:+.2f}% | {near.date()} | {dmin} | "
                   f"{'yes' if dt.date().isoformat() in BEST else 'no'} |")
    out.append(f"\n**^GSPC: {k} of 10 best days sit within 5 sessions of a top-10 worst day.**\n")
    out.append("| Rank | ^GSPC worst day | ret | in Morningstar's worst list? |")
    out.append("|---|---|---|---|")
    for rk, (dt, v) in enumerate(worst10.items(), 1):
        out.append(f"| {rk} | {dt.date()} | {v*100:+.2f}% | {'yes' if dt.date().isoformat() in WORST else 'no'} |")
    out.append("")
    # Morningstar's own dates
    bpos = [r.index.get_loc(pd.Timestamp(x)) for x in BEST if pd.Timestamp(x) in r.index]
    wpos2 = [r.index.get_loc(pd.Timestamp(x)) for x in WORST if pd.Timestamp(x) in r.index]
    k2 = sum(1 for i in bpos if any(abs(i - j) <= 5 for j in wpos2))
    out.append(f"On Morningstar's own twenty dates (as listed in the study): **{k2} of {len(bpos)}** best days "
               f"sit within 5 sessions of one of the {len(wpos2)} worst days on the S&P 500 trading calendar.\n")
    return {"best10": best10, "worst10": worst10, "k_gspc": k, "k_mstar": k2,
            "clusters": None}


# ------------------------------------------------------------------ Part 3
def part3(d: Data, out: list[str]):
    g = d.px["^GSPC"].loc["1989-01-01":]
    r = g["ret"].dropna()
    lr = np.log1p(r)
    rv = lr.rolling(20).var(ddof=1) * 252
    tgt = 0.12 ** 2
    expo = (tgt / rv).clip(lower=0.25, upper=1.5)
    held = expo.shift(1)                       # set at T-1's close, held through T
    sl = r.index >= pd.Timestamp("1990-01-02")
    r, held = r[sl], held[sl]
    turnover = held.diff().abs().fillna(held.iloc[0])
    strat = held * r
    strat_c = strat - turnover * 0.0002

    def stats(x):
        eq = (1 + x).cumprod()
        yrs = len(x) / 252
        cagr = eq.iloc[-1] ** (1 / yrs) - 1
        vol = x.std(ddof=1) * np.sqrt(252)
        sharpe = x.mean() / x.std(ddof=1) * np.sqrt(252)
        mdd = (eq / eq.cummax() - 1).min()
        return cagr, vol, sharpe, mdd

    out.append(f"Source: ^GSPC price return (no dividends) via `altdata.sources.yfinance_source`, "
               f"{r.index[0].date()} to {r.index[-1].date()}, n = {len(r):,}. Exposure = "
               "min(1.5, max(0.25, 0.12² / RV²₂₀)), RV₂₀ the annualised sample variance of the last 20 daily "
               "log returns, set at the close and held over the next session. Cash and borrowing earn and cost "
               "zero; Sharpe is on excess-of-zero returns. Cost case: 2bp × |Δexposure| each day. "
               f"Pulled {d.pulled_at:%Y-%m-%d %H:%M} ET.\n")
    out.append("| Strategy | Ann. return (CAGR) | Ann. vol | Sharpe (rf = 0) | Max drawdown | Mean exposure | Ann. turnover |")
    out.append("|---|---|---|---|---|---|---|")
    for lbl, x, me, to in (("Buy and hold", r, 1.0, 0.0),
                           ("Vol-managed, no costs", strat, held.mean(), turnover.mean() * 252),
                           ("Vol-managed, 2bp/turnover", strat_c, held.mean(), turnover.mean() * 252)):
        a, v, s, m = stats(x)
        out.append(f"| {lbl} | {a*100:.2f}% | {v*100:.2f}% | {s:.2f} | {m*100:.1f}% | {me:.2f} | {to:.1f}x |")
    out.append("")
    out.append("Exposure held on each of the twenty dates (set at T-1's close):\n")
    out.append("| Date | Side | ^GSPC ret | Exposure held | Strategy ret (no costs) |")
    out.append("|---|---|---|---|---|")
    rows = []
    for side, dates in (("best", BEST), ("worst", WORST)):
        for ds in dates:
            dt = pd.Timestamp(ds)
            if dt not in r.index:
                out.append(f"| {ds} | {side} | gap | gap | gap |")
                continue
            e = held.loc[dt]
            rows.append((side, e))
            out.append(f"| {ds} | {side} | {r.loc[dt]*100:+.2f}% | {e:.2f} | {e*r.loc[dt]*100:+.2f}% |")
    eb = [e for s, e in rows if s == "best"]
    ew = [e for s, e in rows if s == "worst"]
    out.append(f"\nMedian exposure: best days {np.median(eb):.2f}, worst days {np.median(ew):.2f}. "
               f"Sum of strategy returns on the ten worst {sum(e*r.loc[pd.Timestamp(ds)] for ds, e in zip([x for x in WORST if pd.Timestamp(x) in r.index], ew))*100:+.1f}% "
               f"vs buy-and-hold {sum(r.loc[pd.Timestamp(x)] for x in WORST if pd.Timestamp(x) in r.index)*100:+.1f}%; "
               f"on the ten best {sum(e*r.loc[pd.Timestamp(ds)] for ds, e in zip([x for x in BEST if pd.Timestamp(x) in r.index], eb))*100:+.1f}% "
               f"vs {sum(r.loc[pd.Timestamp(x)] for x in BEST if pd.Timestamp(x) in r.index)*100:+.1f}%.\n")
    a0 = stats(r)
    a1 = stats(strat)
    a2 = stats(strat_c)
    return {"bh": a0, "vm": a1, "vmc": a2, "eb": np.median(eb), "ew": np.median(ew)}


# ------------------------------------------------------------------ Parts 4-7 helpers
SHUFFLES = 1000
SEED = 20261105


def _near(flag: np.ndarray, before: int, after: int) -> np.ndarray:
    """For each i: is any flag set in [i-before, i+after], position i itself excluded?"""
    n = len(flag)
    f = flag.astype(np.int64)
    c = np.concatenate([[0], np.cumsum(f)])
    i = np.arange(n)
    lo = np.clip(i - before, 0, n)
    hi = np.clip(i + after + 1, 0, n)
    return (c[hi] - c[lo] - f) > 0


def tail_stats(x: pd.Series, shuffles: int = SHUFFLES) -> dict:
    """Part 2's decile statistics (full-sample thresholds) on any daily series."""
    v = x.values
    n = len(v)
    q10, q90 = np.quantile(v, 0.10), np.quantile(v, 0.90)
    bot, top = v <= q10, v >= q90
    out = {"n": n, "q10": q10, "q90": q90, "bot": bot, "top": top}
    for name, src, tgt in (("b2t", bot, top), ("t2b", top, bot)):
        for h in (1, 5, 10):
            ok = np.arange(n) < n - h
            fw = _near(tgt, 0, h)
            out[(name, h)] = fw[src & ok].mean() * 100
            out[(name, h, "n")] = int((src & ok).sum())
            out[(name, h, "base")] = fw[ok].mean() * 100

    def clus(b, t):
        return _near(b, 5, 5)[t].mean() * 100

    out["clus"] = clus(bot, top)
    out["clus_n"] = int(top.sum())
    out["clus_ind"] = (1 - (1 - bot.mean()) ** 10) * 100
    rng = np.random.default_rng(SEED)
    sh = np.empty(shuffles)
    for k in range(shuffles):
        p = rng.permutation(v)
        sh[k] = clus(p <= q10, p >= q90)
    out["clus_shuf"] = (sh.mean(), np.quantile(sh, 0.025), np.quantile(sh, 0.975))
    return out


def dist_cells(x: pd.Series) -> str:
    x = x.dropna()
    if len(x) == 0:
        return "0 | gap | gap | gap | gap | gap"
    return (f"{len(x):,} | {x.mean():+.2f} | {x.median():+.2f} | {x.quantile(.1):+.2f} | "
            f"{x.quantile(.9):+.2f} | {(x > 0).mean()*100:.0f}%")


def pct_of_history(s: pd.Series, day: pd.Timestamp, window: int | None = None):
    """Percentile (0-100, share of values <= it) of s's value on `day` against its own
    history up to and including `day` (the last `window` values, else all)."""
    if s is None:
        return np.nan
    h = s.loc[:day].dropna()
    if h.empty or h.index[-1] != day:
        return np.nan
    if window is not None:
        if len(h) < window:
            return np.nan
        h = h.iloc[-window:]
    return float((h <= h.iloc[-1]).mean() * 100)


def roll_ret(d: Data, sym: str, k: int = 20) -> pd.Series | None:
    if sym not in d.px:
        return None
    r = d.px[sym]["ret"]
    return np.expm1(np.log1p(r).rolling(k, min_periods=k).sum())


def tday_pos(gi: pd.DatetimeIndex, ds: str) -> int:
    dt = pd.Timestamp(ds)
    if dt in gi:
        return gi.get_loc(dt)
    return len(gi) if dt > gi[-1] else gi.searchsorted(dt)


def _src_line(d: Data, names: list[str]) -> str:
    bits = []
    for nm in names:
        if nm in d.px:
            s = d.px[nm]["close"].dropna()
            bits.append(f"{nm} (Yahoo Finance via `altdata.sources.yfinance_source`, "
                        f"{s.index[0].date()} to {s.index[-1].date()})")
        elif nm in d.fred:
            s = d.fred[nm]
            bits.append(f"FRED {nm} ({d.fred_via[nm]}, {s.index[0].date()} to {s.index[-1].date()})")
        elif nm == "EBP" and d.ebp is not None:
            bits.append(f"Federal Reserve excess bond premium (FEDS Notes CSV, {EBP_URL}, "
                        f"{d.ebp.index[0]:%Y-%m} to {d.ebp.index[-1]:%Y-%m})")
        else:
            bits.append(f"{nm}: gap ({d.errors.get(nm, 'not pulled')})")
    return ("Source: " + "; ".join(bits) + f". Data pulled {d.pulled_at:%Y-%m-%d %H:%M} ET "
            f"(cache `{DEFAULT_CACHE.as_posix().replace(Path.home().as_posix(), '~')}`).\n")


# ------------------------------------------------------------------ Part 4
def garch_sigma(r: pd.Series, first_year: int) -> tuple[pd.Series, list]:
    """One-step-ahead GARCH(1,1) daily sigma for each day of year Y >= first_year, from
    parameters fitted on returns through the end of Y-1 (constant mean, normal errors)."""
    from arch import arch_model
    y = r * 100
    sig = pd.Series(np.nan, index=r.index)
    fits = []
    last_year = r.index[-1].year
    for yr in range(first_year, last_year + 1):
        train = y.loc[: f"{yr - 1}-12-31"]
        res = arch_model(train, mean="Constant", vol="GARCH", p=1, q=1, dist="normal",
                         rescale=False).fit(disp="off")
        through = y.loc[: f"{yr}-12-31"]
        fixed = arch_model(through, mean="Constant", vol="GARCH", p=1, q=1, dist="normal",
                           rescale=False).fix(res.params)
        cv = fixed.conditional_volatility.loc[f"{yr}-01-01":] / 100
        sig.loc[cv.index] = cv.values
        fits.append((yr, res.params))
    return sig, fits


def part4(d: Data, out: list[str]):
    g = d.px["^GSPC"].loc["1950-01-03":]
    r = g["ret"].dropna()
    c = g["close"].loc[r.index]
    first_year = 1955
    sig_g, fits = garch_sigma(r, first_year)
    sig_rv = r.rolling(20, min_periods=20).std(ddof=1).shift(1)     # through T-1
    out.append(_src_line(d, ["^GSPC"]))
    yr, p = fits[-1]
    persist = p["alpha[1]"] + p["beta[1]"]
    out.append(f"Standardisation. GARCH(1,1), constant mean, normal errors, fitted by `arch` "
               f"{__import__('arch').__version__} on daily ^GSPC returns from 1950-01-03 through each "
               f"year-end and applied, with those parameters fixed, to the following year: σ_T is the "
               f"one-step-ahead forecast made at T-1's close. First applied year {first_year} (1950–54 is "
               f"the first fit). Latest fit (through {yr - 1}-12-31, applied to {yr}): ω = {p['omega']:.4f}, "
               f"α = {p['alpha[1]']:.4f}, β = {p['beta[1]']:.4f}, α+β = {persist:.4f}. Cross-check: σ_T = "
               f"sample standard deviation of the 20 daily returns ending T-1. z_T = r_T / σ_T (raw return, "
               f"not demeaned). Deciles on each series' own full-sample thresholds; Part 2's rolling-10y "
               f"definition is not repeated, because standardising already removes the level of vol.\n")

    common = sig_g.notna() & sig_rv.notna()
    idx = r.index[common]
    series = {
        "raw, Part 2 sample (1950–)": r * 100,
        f"raw, matched sample ({idx[0].year}–)": r.loc[idx] * 100,
        "GARCH-standardised": (r / sig_g).loc[idx],
        "RV20-standardised": (r / sig_rv).loc[idx],
    }
    st = {k: tail_stats(v) for k, v in series.items()}
    labels = list(series)
    out.append(f"Matched sample: {idx[0].date()} to {idx[-1].date()}, n = {len(idx):,}.\n")

    out.append("### Part 4.1 P(opposite-tail day within h sessions | tail day)\n")
    out.append("| Series | bottom-decile threshold | n bottom days | P(top ≤1) | P(top ≤5) | P(top ≤10) | "
               "any day ≤1 | any day ≤5 | any day ≤10 | n top days | P(bottom ≤5), given top | any day ≤5 |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for k in labels:
        s = st[k]
        unit = "%" if k.startswith("raw") else "σ"
        out.append(f"| {k} | ≤ {s['q10']:.2f}{unit} | {s[('b2t', 1, 'n')]:,} | "
                   + " | ".join(f"{s[('b2t', h)]:.1f}%" for h in (1, 5, 10)) + " | "
                   + " | ".join(f"{s[('b2t', h, 'base')]:.1f}%" for h in (1, 5, 10)) + " | "
                   f"{s[('t2b', 5, 'n')]:,} | {s[('t2b', 5)]:.1f}% | {s[('t2b', 5, 'base')]:.1f}% |")
    out.append("")

    out.append("### Part 4.2 Clustering against a shuffled baseline\n")
    out.append(f"Share of top-decile days with a bottom-decile day within ±5 sessions (Part 2.4's statistic). "
               f"Shuffled: the same series permuted {SHUFFLES:,} times (seed {SEED}), mean and 2.5–97.5% range. "
               "\"If independent\" is Part 2.4's 1 − (1 − p)^10.\n")
    out.append("| Series | top-decile days | share near a bottom-decile day | shuffled mean | shuffled 95% range | if independent | excess over shuffled |")
    out.append("|---|---|---|---|---|---|---|")
    for k in labels:
        s = st[k]
        m, lo, hi = s["clus_shuf"]
        out.append(f"| {k} | {s['clus_n']:,} | {s['clus']:.1f}% | {m:.1f}% | {lo:.1f}–{hi:.1f}% | "
                   f"{s['clus_ind']:.1f}% | {s['clus'] - m:+.1f}pp |")
    out.append("")

    out.append("### Part 4.3 Forward returns after a bottom-decile day\n")
    out.append("Raw: close T to close T+h, percent. Standardised: the h-session log return divided by "
               "σ_{T+1}·√h, σ_{T+1} being the forecast known at T's close under the same definition (GARCH or "
               "RV20), in σ units. \"Bottom decile\" is each series' own (raw rows: raw deciles; standardised "
               "rows: deciles of z). Columns: n | mean | median | 10th | 90th | share > 0.\n")
    fwd_raw = {h: (c.shift(-h) / c - 1) * 100 for h in (1, 5, 20)}
    lfwd = {h: np.log(c.shift(-h) / c) for h in (1, 5, 20)}
    sig_next = {"GARCH-standardised": sig_g.shift(-1), "RV20-standardised": sig_rv.shift(-1)}
    out.append("| Conditioning | h | raw: n | mean % | median % | 10th % | 90th % | >0 | std: n | mean σ | median σ | 10th σ | 90th σ | >0 |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for k in labels:
        s = st[k]
        x = series[k]
        bmask = pd.Series(s["bot"], index=x.index)
        for cond_lbl, mask in (("all days", pd.Series(True, index=x.index)), ("bottom decile", bmask)):
            for h in (1, 5, 20):
                sel = mask[mask].index
                raw_cells = dist_cells(fwd_raw[h].reindex(sel))
                if k in sig_next:
                    z = (lfwd[h] / (sig_next[k] * np.sqrt(h))).reindex(sel)
                    std_cells = dist_cells(z)
                else:
                    std_cells = "— | — | — | — | — | —"
                out.append(f"| {k}: {cond_lbl} | {h} | {raw_cells} | {std_cells} |")
    out.append("")
    return {"st": st, "labels": labels}


# ------------------------------------------------------------------ Part 5
def part5(d: Data, out: list[str], p2_q90: float):
    g = d.px["^GSPC"]
    gi = g.index
    allr = g["ret"]
    r = allr.loc["1990-01-02":].dropna()
    q01 = r.quantile(0.01)
    vix = d.fred.get("VIXCLS")
    vix_t1 = vix.reindex(gi).ffill(limit=3).shift(1).loc[r.index] if vix is not None else None
    prior_max = allr.abs().rolling(20, min_periods=20).max().shift(1).loc[r.index]
    bot1 = r <= q01
    calm_v = bot1 & (vix_t1 < 20)
    calm_q = bot1 & (prior_max < 0.02)
    openers = r[bot1 & (vix_t1 < 20) & (prior_max < 0.02)]
    big = openers[openers <= -0.04]

    out.append(_src_line(d, ["^GSPC", "VIXCLS", "SPY", "RSP", "QQQ"] + SECTORS))
    out.append(f"Definition: ^GSPC return in the bottom 1% of sessions since 1990-01-02 (threshold ≤ "
               f"{q01*100:.2f}%, n = {len(r):,} sessions, {int(bot1.sum())} days), with FRED VIXCLS at the "
               f"prior session's close below 20 and no session with |return| ≥ 2% among the 20 before T.\n")
    out.append(f"Of the {int(bot1.sum())} bottom-1% days: {int(calm_v.sum())} had VIX < 20 at T-1; "
               f"{int(calm_q.sum())} had no 2% day in the prior 20 sessions; **{len(openers)} had both** "
               f"(the calm-surface openers). **{len(big)} of them fell 4% or more**: "
               f"{', '.join(f'{t.date()} ({v*100:+.2f}%)' for t, v in big.items()) or 'none'}.\n")

    out.append("### Part 5.1 The openers\n")
    out.append("| # | Date | ^GSPC ret | VIX at T-1 | largest abs. ret, prior 20 | ≤ −4%? |")
    out.append("|---|---|---|---|---|---|")
    for k, (t, v) in enumerate(openers.items(), 1):
        out.append(f"| {k} | {t.date()} | {v*100:+.2f}% | {vix_t1.loc[t]:.2f} | {prior_max.loc[t]*100:.2f}% | "
                   f"{'yes' if v <= -0.04 else 'no'} |")
    out.append("")

    out.append("### Part 5.2 Part 1 condition rows at T-1\n")
    out.append("Columns as Part 1 (§1). HY and IG OAS print \"gap\" before 6 Nov 2023 (FRED's window).\n")
    hdr = ["Opener", "T-1 date"] + [SHORT[c] for c in COLS]
    out.append("| " + " | ".join(hdr) + " |")
    out.append("|" + "---|" * len(hdr))
    for t in openers.index:
        p = gi.get_loc(t) - 1
        row = conditions(d, gi[p])
        out.append("| " + " | ".join([str(t.date()), str(gi[p].date())] + [cell(c, row[c]) for c in COLS]) + " |")
    out.append("")

    out.append("### Part 5.3 Internals at T-1, as percentiles of their own history\n")
    internals_table(d, out, openers.index)

    out.append("### Part 5.4 What followed\n")
    n_top, n_obs = aftermath_table(d, out, openers, p2_q90)
    out.append(f"\nA top-decile day followed within 5 sessions after **{n_top} of {n_obs}** openers with five "
               "sessions of history.\n")
    return {"n": len(openers), "big": big, "q01": q01, "n_bot1": int(bot1.sum()), "n_top": n_top,
            "n_obs": n_obs}


def internal_series(d: Data) -> dict:
    """Part 5.3's internals as daily series: RSP-SPY and QQQ-SPY 20-session relative total
    return (pp), sector-SPDR dispersion (pp, >= 9 sectors), the sector count, SPY Amihud."""
    rsp, spy, qqq = roll_ret(d, "RSP"), roll_ret(d, "SPY"), roll_ret(d, "QQQ")
    rsp_rel = (rsp - spy).dropna() * 100 if rsp is not None and spy is not None else None
    qqq_rel = (qqq - spy).dropna() * 100 if qqq is not None and spy is not None else None
    sect = pd.DataFrame({s: roll_ret(d, s) for s in SECTORS if s in d.px})
    avail = sect.notna().sum(axis=1)
    disp = (sect.std(axis=1, ddof=1) * 100).where(avail >= 9)
    if "SPY" in d.px:
        p_ = d.px["SPY"]
        ami = (p_["ret"].abs() / (p_["close"] * p_["volume"]).replace(0, np.nan)).rolling(20, min_periods=20).mean()
    else:
        ami = None
    return {"rsp_rel": rsp_rel, "qqq_rel": qqq_rel, "disp": disp, "avail": avail, "ami": ami}


def internals_table(d: Data, out: list[str], days) -> None:
    """Part 5.3's table for tail days `days` (their T-1 rows)."""
    gi = d.px["^GSPC"].index
    s_ = internal_series(d)
    rsp_rel, qqq_rel, disp, avail, ami = (s_["rsp_rel"], s_["qqq_rel"], s_["disp"], s_["avail"],
                                          s_["ami"])
    out.append("Each value is as of T-1's close and its percentile is the share of the series' own values on or "
               "before T-1 that are at or below it (expanding history from the series' first observation; "
               "Amihud over the trailing 252 and 756 values). RSP-SPY and QQQ-SPY: 20-session total-return "
               "difference, pp (RSP from 2003, QQQ from 1999). Sector dispersion: cross-sectional standard "
               "deviation of the sector SPDRs' 20-session total returns, pp, computed when at least 9 sectors "
               "have 20 sessions of history (9 until XLRE in 2015, 11 from XLC in 2018). Amihud: SPY's "
               "20-session mean of |ret| ÷ dollar volume (100 = least liquid).\n")
    out.append("| Opener | T-1 | RSP-SPY pp | pctl | QQQ-SPY pp | pctl | sector disp. pp | pctl | n sectors | Amihud 1y pctl | Amihud 3y pctl |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|")

    def v_at(s, day):
        return float(s.loc[day]) if s is not None and day in s.index and pd.notna(s.loc[day]) else np.nan

    for t in days:
        day = gi[gi.get_loc(t) - 1]
        out.append(f"| {t.date()} | {day.date()} | {fmt(v_at(rsp_rel, day), 2, sign=True)} | "
                   f"{fmt(pct_of_history(rsp_rel, day), 0)} | {fmt(v_at(qqq_rel, day), 2, sign=True)} | "
                   f"{fmt(pct_of_history(qqq_rel, day), 0)} | {fmt(v_at(disp, day), 2)} | "
                   f"{fmt(pct_of_history(disp, day), 0)} | "
                   f"{int(avail.loc[day]) if day in avail.index and v_at(disp, day) == v_at(disp, day) else 'gap'} | "
                   f"{fmt(pct_of_history(ami, day, 252), 0)} | {fmt(pct_of_history(ami, day, 756), 0)} |")
    out.append("")


def aftermath_table(d: Data, out: list[str], openers: pd.Series, p2_q90: float) -> tuple[int, int]:
    """Part 5.4's table for tail days `openers` (date -> return); returns (n top, n observed)."""
    g = d.px["^GSPC"]
    gi = g.index
    out.append(f"T+1: close T to close T+1, and that session's high-low range ÷ close T. T+1..T+5: close T to "
               f"close T+5, and the highest high less the lowest low over the five sessions ÷ close T. Top decile "
               f"is Part 2's full-sample threshold (≥ {p2_q90*100:.2f}%), looked for in T+1..T+5. \"gap\" where the "
               "sessions have not happened yet.\n")
    out.append("| Opener | ret T | ret T+1 | range T+1 | ret T+1..5 | range T+1..5 | top-decile day within 5? |")
    out.append("|---|---|---|---|---|---|---|")
    n_top, n_obs = 0, 0
    for t, v in openers.items():
        i = gi.get_loc(t)
        cT = g["close"].iloc[i]
        if i + 1 < len(gi):
            r1 = (g["close"].iloc[i + 1] / cT - 1) * 100
            rg1 = (g["high"].iloc[i + 1] - g["low"].iloc[i + 1]) / cT * 100
        else:
            r1 = rg1 = np.nan
        if i + 5 < len(gi):
            r5 = (g["close"].iloc[i + 5] / cT - 1) * 100
            rg5 = (g["high"].iloc[i + 1: i + 6].max() - g["low"].iloc[i + 1: i + 6].min()) / cT * 100
            hit = bool((g["ret"].iloc[i + 1: i + 6] >= p2_q90).any())
            n_obs += 1
            n_top += hit
            hit_s = "yes" if hit else "no"
        else:
            r5 = rg5 = np.nan
            hit_s = "gap"
        out.append(f"| {t.date()} | {v*100:+.2f}% | {fmt(r1, 2, sign=True)}% | {fmt(rg1, 2)}% | "
                   f"{fmt(r5, 2, sign=True)}% | {fmt(rg5, 2)}% | {hit_s} |".replace("gap%", "gap"))
    return n_top, n_obs


# ------------------------------------------------------------------ Part 6
def part6(d: Data, out: list[str]):
    g = d.px["^GSPC"].loc["1989-01-01":]
    r_all = g["ret"].dropna()
    lr = np.log1p(r_all)
    rv = lr.rolling(20).var(ddof=1) * 252
    expo = (0.12 ** 2 / rv).clip(lower=0.25, upper=1.5)
    held_all = expo.shift(1)
    sl = r_all.index >= pd.Timestamp("1990-01-02")
    r, held = r_all[sl], held_all[sl]
    tb = d.fred.get("DTB3")
    if tb is None:
        out.append("gap: FRED DTB3 unavailable, so the T-bill rows cannot be built.\n")
        rf = None
    else:
        y = tb.reindex(g.index.union(tb.index)).ffill(limit=5).reindex(g.index)
        rf = ((1 + y / 100) ** (1 / 252) - 1).shift(1).reindex(r.index)
    ebar = float(held.mean())

    def cm_turnover(port, w):
        drift = w * (1 + r) / (1 + port)
        t = (drift - w).abs().shift(1).fillna(w)          # rebalance at the next close; day 1 buys in
        return t

    vm_to = held.diff().abs().fillna(held.iloc[0])
    rows = [("Buy and hold", r, pd.Series(1.0, index=r.index), pd.Series(0.0, index=r.index).where(
        r.index != r.index[0], 1.0))]
    rows.append(("Vol-managed, cash at zero (Part 3)", held * r, held, vm_to))
    cm0 = ebar * r
    rows.append((f"Constant mix {ebar:.2f}, cash at zero", cm0, pd.Series(ebar, index=r.index),
                 cm_turnover(cm0, ebar)))
    if rf is not None:
        vmb = held * r + (1 - held) * rf
        rows.append(("Vol-managed, cash and borrowing at DTB3", vmb, held, vm_to))
        cmb = ebar * r + (1 - ebar) * rf
        rows.append((f"Constant mix {ebar:.2f}, rest in DTB3", cmb, pd.Series(ebar, index=r.index),
                     cm_turnover(cmb, ebar)))

    def stats(x):
        eq = (1 + x).cumprod()
        yrs = len(x) / 252
        cagr = eq.iloc[-1] ** (1 / yrs) - 1
        vol = x.std(ddof=1) * np.sqrt(252)
        sharpe = x.mean() / x.std(ddof=1) * np.sqrt(252)
        xs = (x - rf) if rf is not None else None
        sh_x = xs.mean() / xs.std(ddof=1) * np.sqrt(252) if xs is not None else np.nan
        mdd = (eq / eq.cummax() - 1).min()
        w20 = (eq / eq.shift(20) - 1).min()
        return cagr, vol, sharpe, sh_x, mdd, w20

    out.append(_src_line(d, ["^GSPC", "DTB3"]))
    out.append(f"{r.index[0].date()} to {r.index[-1].date()}, n = {len(r):,}. The vol-managed rule is Part 3's. "
               f"The constant mix holds the rule's average exposure, {ebar:.4f}, rebalanced at each close; its "
               "turnover is the drift back to target. T-bill return: FRED DTB3 at T-1 (discount-basis annual %, "
               "carried at most 5 days), compounded to a 252-day year. Sharpe (rf = 0) is Part 3's definition; "
               "the next column is the same ratio on returns in excess of DTB3. Worst 20-session = the lowest "
               "close-to-close return over any 20 sessions. Costs: 2bp × turnover each day (buy and hold: one "
               "purchase). Price return, no dividends, as Part 3.\n")
    out.append("| Strategy | costs | Ann. return (CAGR) | Ann. vol | Sharpe (rf = 0) | Sharpe (excess of DTB3) | Max drawdown | Worst 20-session | Avg exposure | Ann. turnover |")
    out.append("|---|---|---|---|---|---|---|---|---|---|")
    res = {}
    for lbl, x, e, to in rows:
        for cl, xx in (("none", x), ("2bp", x - to * 0.0002)):
            a, v, s, sx, m, w = stats(xx)
            res[(lbl, cl)] = (a, v, s, sx, m, w, float(e.mean()))
            out.append(f"| {lbl} | {cl} | {a*100:.2f}% | {v*100:.2f}% | {s:.2f} | {fmt(sx)} | {m*100:.1f}% | "
                       f"{w*100:.1f}% | {e.mean():.2f} | {to.sum()/ (len(r)/252):.1f}x |")
    out.append("")

    out.append("### Part 6.1 Vol-managed exposure path, 2026-10-26 to the latest session\n")
    out.append("RV20 and the exposure it sets are as of each session's close; \"held\" is the exposure carried "
               "through that session (set at the prior close). The last row's set exposure applies to the next "
               "session.\n")
    out.append("| Date | ^GSPC ret | RV20 (ann.) | exposure set at close | exposure held |")
    out.append("|---|---|---|---|---|")
    path = []
    for t in r_all.loc["2026-10-26":].index:
        out.append(f"| {t.date()} | {r_all.loc[t]*100:+.2f}% | {np.sqrt(rv.loc[t])*100:.1f}% | "
                   f"{expo.loc[t]:.2f} | {held_all.loc[t]:.2f} |")
        path.append((t, expo.loc[t], held_all.loc[t], np.sqrt(rv.loc[t])))
    out.append("")
    return {"res": res, "ebar": ebar, "path": path}


# ------------------------------------------------------------------ Part 7
def part7(d: Data, out: list[str]):
    g = d.px["^GSPC"]
    gi = g.index
    baa = d.fred.get("BAA10Y")
    out.append(_src_line(d, ["BAA10Y", "EBP"]))
    out.append("BAA10Y (Moody's seasoned Baa corporate yield less the 10-year Treasury, percent, shown in bp) on "
               "the Part 1 calendar: the value at T-k's date, carried at most 5 days. Δ20 = change over the "
               "20 FRED observations before T-1's value. EBP: the Federal Reserve's excess bond premium "
               "(Gilchrist–Zakrajšek, percentage points) and GZ spread for the calendar month before T; the CSV "
               "is the current vintage, not what was published at the time.\n")
    out.append("| Tail day | side | BAA10Y T-1 bp | Δ20 at T-1 bp | BAA10Y T-5 bp | BAA10Y T-20 bp | EBP month | EBP pp | GZ spread pp |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    vals = {}
    for side, dates in (("worst", WORST), ("best", BEST)):
        for ds in dates:
            pos = tday_pos(gi, ds)
            v = {k: asof(baa, gi[pos - k]) * 100 if baa is not None else np.nan for k in OFFSETS}
            chg = (asof(baa, gi[pos - 1]) - asof_shift(baa, gi[pos - 1], 20)) * 100 if baa is not None else np.nan
            mth = (pd.Timestamp(ds).to_period("M") - 1).to_timestamp()
            if d.ebp is not None and mth in d.ebp.index:
                e_, gz = d.ebp.loc[mth, "ebp"], d.ebp.loc[mth, "gz_spread"]
            else:
                e_ = gz = np.nan
            vals[ds] = (v[1], chg, e_)
            out.append(f"| {ds} | {side} | {fmt(v[1], 0)} | {fmt(chg, 0, sign=True)} | {fmt(v[5], 0)} | "
                       f"{fmt(v[20], 0)} | {mth:%Y-%m} | {fmt(e_, 2, sign=True)} | {fmt(gz, 2)} |")
    out.append("")
    if baa is not None:
        b = baa.dropna()
        ref = b.loc["1990-01-01":]
        out.append(f"Context: BAA10Y since 1990 has median {ref.median()*100:.0f}bp, 90th percentile "
                   f"{ref.quantile(.9)*100:.0f}bp; its last observation is {b.index[-1].date()} at "
                   f"{b.iloc[-1]*100:.0f}bp.\n")
    out.append("### Part 7.1 Earliest observation FRED serves\n")
    out.append("| Series | Via | First obs. | Last obs. | n |")
    out.append("|---|---|---|---|---|")
    for fid in ("BAMLH0A0HYM2", "BAMLC0A0CM", "BAA10Y"):
        s = d.fred.get(fid)
        if s is None or s.empty:
            out.append(f"| {fid} | gap — {d.errors.get(fid, 'not pulled')} | gap | gap | gap |")
        else:
            out.append(f"| {fid} | {d.fred_via[fid]}, pulled {d.pulled.get('fred_' + fid, d.pulled_at):%Y-%m-%d %H:%M} ET | "
                       f"{s.index[0].date()} | {s.index[-1].date()} | {len(s):,} |")
    out.append("")
    return {"vals": vals}


# ------------------------------------------------------------------ Part 8
P8_START, P8_END = "2003-05-01", "2026-10-22"
P8_H = 10
P8_FIRST_FIT = 2007                 # first year-end refit; predictions from 2008
BOOT_DRAWS, BOOT_BLOCK = 500, 21
S_FEATS = ["VIX", "RV20", "VIX-RV20", "VIX/VIX3M", "VVIX", "|r|>2% /20", "DD 252"]
I_FEATS = ["RSP-SPY 20d", "RSP-SPY pctl", "QQQ-SPY 20d", "sector disp.", "Amihud 1y pctl",
           "Amihud 3y pctl", "HB/LV 20d", "SPY - HB/LV 1d"]


def p8_features(d: Data) -> pd.DataFrame:
    """Every feature as of each ^GSPC close; NaN where a series has no value (the models fill)."""
    g = d.px["^GSPC"]
    gi = g.index
    r = g["ret"]
    lr = np.log1p(r)
    f = pd.DataFrame(index=gi)
    vix = d.fred.get("VIXCLS")
    # as-of read, at most FRED_MAX_FILL_DAYS calendar days (asof() vectorised)
    if vix is not None:
        v = vix.reindex(gi.union(vix.index)).ffill()
        last = pd.Series(vix.index, index=vix.index).reindex(gi.union(vix.index)).ffill()
        v = v.reindex(gi).where((gi - pd.DatetimeIndex(last.reindex(gi))).days <= FRED_MAX_FILL_DAYS)
    else:
        v = pd.Series(np.nan, index=gi)
    f["VIX"] = v
    f["RV20"] = lr.rolling(20, min_periods=20).std(ddof=1) * np.sqrt(252) * 100
    f["VIX-RV20"] = f["VIX"] - f["RV20"]
    for nm, sym in (("VIX3M", "^VIX3M"), ("VVIX", "^VVIX")):
        f[nm] = d.px[sym]["close"].reindex(gi) if sym in d.px else np.nan
    f["VIX/VIX3M"] = f["VIX"] / f.pop("VIX3M")
    f["|r|>2% /20"] = (r.abs() > 0.02).astype(float).rolling(20, min_periods=20).sum()
    f["DD 252"] = (g["close"] / g["close"].rolling(252, min_periods=1).max() - 1) * 100
    s_ = internal_series(d)
    f["RSP-SPY 20d"] = s_["rsp_rel"].reindex(gi) if s_["rsp_rel"] is not None else np.nan
    f["RSP-SPY pctl"] = (s_["rsp_rel"].expanding().rank(method="max", pct=True) * 100).reindex(gi) \
        if s_["rsp_rel"] is not None else np.nan
    f["QQQ-SPY 20d"] = s_["qqq_rel"].reindex(gi) if s_["qqq_rel"] is not None else np.nan
    f["sector disp."] = s_["disp"].reindex(gi)
    ami = s_["ami"].dropna() if s_["ami"] is not None else None
    for nm, w in (("Amihud 1y pctl", 252), ("Amihud 3y pctl", 756)):
        f[nm] = (ami.rolling(w, min_periods=w).rank(method="max", pct=True) * 100).reindex(gi) \
            if ami is not None else np.nan
    if "SPHB" in d.px and "SPLV" in d.px:
        hl = ((1 + d.px["SPHB"]["ret"]) / (1 + d.px["SPLV"]["ret"]) - 1).dropna()
        idx_ = (1 + hl).cumprod()
        f["HB/LV 20d"] = ((idx_ / idx_.shift(20) - 1) * 100).reindex(gi)
        f["SPY - HB/LV 1d"] = ((d.px["SPY"]["ret"] - hl) * 100).reindex(gi)
    else:
        f["HB/LV 20d"] = f["SPY - HB/LV 1d"] = np.nan
    # targets over t+1..t+H
    fl = pd.concat([lr.shift(-k) for k in range(1, P8_H + 1)], axis=1)
    fr = pd.concat([r.shift(-k) for k in range(1, P8_H + 1)], axis=1)
    complete = fl.notna().all(axis=1)
    f["y_a"] = np.log(fl.std(axis=1, ddof=1) * np.sqrt(252)).where(complete)
    f["y_b"] = (fr.abs() >= 0.02).any(axis=1).astype(float).where(complete)
    f["y_c"] = (fr <= -0.03).any(axis=1).astype(float).where(complete)
    return f


def _design(F: pd.DataFrame, feats: list[str], tr: np.ndarray, te: np.ndarray):
    """Standardise on the training rows; missing -> training mean (0) plus a missing flag
    where the flag varies in training. Returns X_train, X_test (intercept first), names."""
    cols_tr, cols_te, names = [], [], []
    for c in feats:
        x = F[c].values.astype(float)
        xt = x[tr]
        ok = ~np.isnan(xt)
        if ok.sum() < 2:
            continue
        m, s = xt[ok].mean(), xt[ok].std(ddof=0)
        if not s > 0:
            continue
        z = np.where(np.isnan(x), 0.0, (x - m) / s)
        cols_tr.append(z[tr]); cols_te.append(z[te]); names.append(c)
        fl = np.isnan(x).astype(float)
        fm = fl[tr].mean()
        if 0 < fm < 1:
            cols_tr.append(fl[tr]); cols_te.append(fl[te]); names.append(c + " [missing]")
    Xtr = np.column_stack([np.ones(tr.sum())] + cols_tr)
    Xte = np.column_stack([np.ones(te.sum())] + cols_te)
    return Xtr, Xte, names


def _logit(X, y, ridge=1e-6, it=100):
    b = np.zeros(X.shape[1])
    for _ in range(it):
        p = 1 / (1 + np.exp(-np.clip(X @ b, -35, 35)))
        W = p * (1 - p)
        H = X.T @ (X * W[:, None]) + ridge * np.eye(len(b))
        step = np.linalg.solve(H, X.T @ (y - p) - ridge * b)
        b += step
        if np.max(np.abs(step)) < 1e-9:
            break
    return b


def _auc(y, p):
    from scipy.stats import rankdata
    y = y.astype(bool)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return np.nan
    rk = rankdata(p)
    return (rk[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def _metrics(o: dict, sel: np.ndarray) -> dict:
    m = {}
    ya, bench = o["y_a"][sel], o["bench"][sel]
    sst = ((ya - bench) ** 2).sum()
    for k in ("S", "SI"):
        m[("a", "R2", k)] = 1 - ((ya - o[("a", k)][sel]) ** 2).sum() / sst if sst > 0 else np.nan
        for t in ("b", "c"):
            y, p = o["y_" + t][sel], o[(t, k)][sel]
            m[(t, "AUC", k)] = _auc(y, p)
            m[(t, "Brier", k)] = float(((p - y) ** 2).mean()) if len(y) else np.nan
    return m


def part8(d: Data, out: list[str], q01_1990: float, p2_q90: float):
    F = p8_features(d)
    gi = F.index
    pos = np.arange(len(gi))
    insample = (gi >= pd.Timestamp(P8_START)) & (gi <= pd.Timestamp(P8_END)) & F["y_a"].notna().values
    years = range(P8_FIRST_FIT + 1, pd.Timestamp(P8_END).year + 1)
    o = {k: np.full(len(gi), np.nan) for k in
         [("a", "S"), ("a", "SI"), ("b", "S"), ("b", "SI"), ("c", "S"), ("c", "SI"), "bench"]}
    coefs = {}          # (target, year) -> {feature: coef} for the S+I model
    n_train = {}
    for yr in years:
        fit_pos = gi.searchsorted(pd.Timestamp(f"{yr}-01-01")) - 1     # last session of yr-1
        tr = insample & (pos + P8_H <= fit_pos)       # targets fully realised by the fit date
        te = insample & (gi.year == yr)
        if te.sum() == 0:
            continue
        n_train[yr] = int(tr.sum())
        o["bench"][te] = F["y_a"].values[tr].mean()
        for k, feats in (("S", S_FEATS), ("SI", S_FEATS + I_FEATS)):
            Xtr, Xte, names = _design(F, feats, tr, te)
            ya = F["y_a"].values[tr]
            ba = np.linalg.lstsq(Xtr, ya, rcond=None)[0]
            o[("a", k)][te] = Xte @ ba
            bs = {"a": ba}
            for t in ("b", "c"):
                bt = _logit(Xtr, F["y_" + t].values[tr])
                o[(t, k)][te] = 1 / (1 + np.exp(-np.clip(Xte @ bt, -35, 35)))
                bs[t] = bt
            if k == "SI":
                for t in ("a", "b", "c"):
                    coefs[(t, yr)] = dict(zip(names, bs[t][1:]))
    oos = insample & ~np.isnan(o[("a", "S")])
    for k in list(o):
        o[k] = o[k][oos]
    for t in ("a", "b", "c"):
        o["y_" + t] = F["y_" + t].values[oos]
    vix_t = F["VIX"].values[oos]
    low = vix_t < 20
    allm = np.ones(oos.sum(), bool)
    ex08 = gi[oos].year >= 2009          # sensitivity only: drops the first fit's year
    subs = {"all": allm, "low": low, "all09": ex08, "low09": low & ex08}
    point = {k: _metrics(o, v) for k, v in subs.items()}

    rng = np.random.default_rng(SEED)
    n = int(oos.sum())
    nb = int(np.ceil(n / BOOT_BLOCK))
    keys = [("a", "R2"), ("b", "AUC"), ("b", "Brier"), ("c", "AUC"), ("c", "Brier")]
    boots = {(sub, k): [] for sub in subs for k in keys}
    for _ in range(BOOT_DRAWS):
        starts = rng.integers(0, n - BOOT_BLOCK + 1, nb)
        ix = (starts[:, None] + np.arange(BOOT_BLOCK)).ravel()[:n]
        ob = {k: v[ix] for k, v in o.items()}
        for sub, sel in ((k, v[ix]) for k, v in subs.items()):
            mb = _metrics(ob, sel)
            for t, met in keys:
                boots[(sub, (t, met))].append(mb[(t, met, "SI")] - mb[(t, met, "S")])

    oos_idx = gi[oos]
    out.append(_src_line(d, ["^GSPC", "VIXCLS", "^VIX3M", "^VVIX", "SPY", "RSP", "QQQ", "SPHB", "SPLV"]
                         + SECTORS))
    out.append(f"Sample: every ^GSPC session from {P8_START} to {P8_END} with a complete t+1..t+{P8_H} window, "
               f"n = {int(insample.sum()):,}. Out of sample: {oos_idx[0].date()} to {oos_idx[-1].date()}, "
               f"n = {n:,}, of which {int(low.sum()):,} with VIXCLS < 20 at t. No new series was fetched; every "
               "input was read from the cache.\n")
    out.append("Features, each as of the close of t. **S** (vol state): VIXCLS (as-of, at most 5 days); RV20 "
               "(annualised stdev of the 20 daily ^GSPC log returns ending t, %); VIX − RV20; VIXCLS ÷ ^VIX3M "
               "(from 2006-07-17, else gap); ^VVIX (from 2007-01-03, else gap); sessions with |ret| > 2% among the "
               "20 ending t; drawdown from the 252-session closing high, %. **I** (internals): RSP − SPY 20-session "
               "total-return difference (pp) and its expanding percentile; QQQ − SPY 20-session difference; "
               "sector-SPDR dispersion (Part 5.3); SPY Amihud as a percentile of its trailing 252 and 756 values; "
               "SPHB/SPLV total-return ratio's 20-session change, % (from 2011-06, else gap); SPY's return less "
               "SPHB/SPLV's on day t, pp.\n")
    out.append(f"Targets over t+1..t+{P8_H} (^GSPC): (a) log of the annualised stdev of the ten daily log returns; "
               "(b) any |ret| ≥ 2%; (c) any ret ≤ −3%. Models: OLS for (a), logistic regression (Newton–Raphson, "
               "1e-6 ridge for numerical stability only) for (b) and (c). Features standardised on the training "
               "rows; a missing value takes the training mean (0 after standardising) and a missing flag joins "
               "the model wherever the flag varies in training; a feature with no variance in training is left "
               "out of that fit. Refit at each year-end from 2007 on the expanding window from 2003-05-01, "
               f"applied to the following year. Training rows are those whose target window had closed by the "
               f"fit date (t + {P8_H} sessions ≤ the year's last session), so no label is used before it is known.\n")
    out.append(f"Out-of-sample R² for (a) is 1 − Σ(y − ŷ)² / Σ(y − ȳ_train)², ȳ_train the training mean of the "
               f"fit that made the prediction. AUC is the Mann–Whitney statistic; Brier is the mean of (p − y)² "
               f"(lower is better). Intervals: {BOOT_DRAWS} moving-block bootstrap draws of the out-of-sample "
               f"series, {BOOT_BLOCK}-session blocks (seed {SEED}), the VIX < 20 subset taken within each draw; "
               "5th to 95th percentile of S+I minus S.\n")
    out.append("Base rates out of sample: "
               f"(b) any 2% day: {o['y_b'].mean()*100:.1f}% of all sessions, {o['y_b'][low].mean()*100:.1f}% "
               f"with VIX < 20; (c) any −3% day: {o['y_c'].mean()*100:.1f}% and {o['y_c'][low].mean()*100:.1f}%.\n")

    out.append("### Part 8.1 Out-of-sample results, S against S+I\n")
    out.append("| Subset | Target | Metric | S | S+I | S+I − S | 90% interval |")
    out.append("|---|---|---|---|---|---|---|")
    labels = {"a": "(a) log RV t+1..10", "b": "(b) any \\|ret\\| ≥ 2%", "c": "(c) any ret ≤ −3%"}
    ci = {}
    for sub, sl in (("all", "all sessions"), ("low", "VIX < 20 at t"),
                    ("all09", "sensitivity: all sessions, 2009–2026"),
                    ("low09", "sensitivity: VIX < 20 at t, 2009–2026")):
        for t, met in keys:
            pS, pSI = point[sub][(t, met, "S")], point[sub][(t, met, "SI")]
            lo, hi = np.nanquantile(boots[(sub, (t, met))], [0.05, 0.95])
            ci[(sub, t, met)] = (pSI - pS, lo, hi)
            out.append(f"| {sl} | {labels[t]} | {met} | {pS:.4f} | {pSI:.4f} | {pSI - pS:+.4f} | "
                       f"{lo:+.4f} to {hi:+.4f} |")
    out.append("")
    da, la, _ = ci[("low", "a", "R2")]
    db, lb, _ = ci[("low", "b", "AUC")]
    passed = da > 0 and la > 0 and db > 0 and lb > 0
    verdict = (f"**Pre-registered criterion (106c(ii)): {'PASS' if passed else 'FAIL'}.** On the VIX < 20 subset, "
               f"S+I minus S is {da:+.4f} on the (a) R² (90% interval lower bound {la:+.4f}) and {db:+.4f} on the "
               f"(b) AUC (lower bound {lb:+.4f}); the criterion needs both differences and both lower bounds above "
               "zero.")
    out.append(verdict + "\n")
    out.append("The sensitivity rows are not the pre-registered test. They drop 2008, whose predictions come "
               "from the first fit (2003-05 to 2007-12, a calm window): 2008's RV20 reached about 19 training "
               "standard deviations, and the linear models extrapolate from there, S+I much further than S. "
               "The verdict above is read from the pre-registered rows only.\n")

    out.append("### Part 8.2 The internal features' coefficients\n")
    last_yr = max(y for (_, y) in coefs)
    out.append(f"Standardised coefficients (per training standard deviation) of the I features in the S+I model "
               f"of the final fit (through {last_yr - 1}-12-31, applied to {last_yr}): log-vol units for (a), "
               f"log-odds for (b) and (c). Signs: positive / negative across the {len(n_train)} refits "
               f"({min(n_train)}–{max(n_train)}); a refit in which the feature had no variance is not counted. "
               "Missing-flag coefficients are not shown.\n")
    out.append("| Feature | (a) final | (a) + / − | (b) final | (b) + / − | (c) final | (c) + / − |")
    out.append("|---|---|---|---|---|---|---|")
    for fn in I_FEATS:
        cells = []
        for t in ("a", "b", "c"):
            fin = coefs[(t, last_yr)].get(fn, np.nan)
            vals = [coefs[(t, y)][fn] for y in n_train if fn in coefs[(t, y)]]
            cells += [fmt(fin, 3, sign=True), f"{sum(v > 0 for v in vals)} / {sum(v < 0 for v in vals)}"]
        out.append(f"| {fn} | " + " | ".join(cells) + " |")
    out.append("")

    # ---------------- looser opener class
    g = d.px["^GSPC"]
    allr = g["ret"]
    r = allr.loc["1990-01-02":].dropna()
    vix = d.fred.get("VIXCLS")
    vix_t1 = vix.reindex(gi).ffill(limit=3).shift(1).loc[r.index]
    big20 = (allr.abs() >= 0.02).astype(float).rolling(20, min_periods=20).sum().shift(1).loc[r.index]
    bot1 = r <= q01_1990
    loose = r[bot1 & (vix_t1 < 25) & (big20 <= 1)]
    out.append("### Part 8.3 The looser opener class\n")
    out.append(_src_line(d, ["^GSPC", "VIXCLS"]))
    out.append(f"Definition: a Part 5 bottom-1% day (^GSPC since 1990-01-02, threshold ≤ {q01_1990*100:.2f}%) "
               f"with FRED VIXCLS below 25 at the prior close and at most one session with |ret| ≥ 2% among the "
               f"20 before T. {int(bot1.sum())} bottom-1% days; **{len(loose)} in the looser class** "
               f"(Part 5's strict class: VIX < 20 and none).\n")
    out.append("| # | Date | ^GSPC ret | VIX at T-1 | 2% days in prior 20 | in Part 5's strict class? |")
    out.append("|---|---|---|---|---|---|")
    pm = allr.abs().rolling(20, min_periods=20).max().shift(1)
    for k, (t, v) in enumerate(loose.items(), 1):
        strict = vix_t1.loc[t] < 20 and pm.loc[t] < 0.02
        out.append(f"| {k} | {t.date()} | {v*100:+.2f}% | {vix_t1.loc[t]:.2f} | {int(big20.loc[t])} | "
                   f"{'yes' if strict else 'no'} |")
    out.append("")
    out.append("**Internals at T-1 (Part 5.3's table).** ")
    internals_table(d, out, loose.index)
    out.append("**Aftermath (Part 5.4's table).** ")
    nt, no = aftermath_table(d, out, loose, p2_q90)
    out.append(f"\nA top-decile day followed within 5 sessions after **{nt} of {no}** days in the looser class.\n")
    out.append("The two named near-misses:\n")
    out.append("| Date | ^GSPC ret | bottom 1%? | VIX at T-1 | 2% days in prior 20 | in the looser class? |")
    out.append("|---|---|---|---|---|---|")
    near = {}
    for ds in ("2018-02-05", "2024-08-05"):
        t = pd.Timestamp(ds)
        rv_, vv, bb = r.loc[t], vix_t1.loc[t], big20.loc[t]
        inn = t in loose.index
        near[ds] = (inn, rv_, vv, bb)
        why = [] if inn else ([f"return above the {q01_1990*100:.2f}% threshold"] if rv_ > q01_1990 else []) + \
            ([f"VIX {vv:.2f} ≥ 25"] if not vv < 25 else []) + ([f"{int(bb)} 2% days"] if bb > 1 else [])
        out.append(f"| {ds} | {rv_*100:+.2f}% | {'yes' if rv_ <= q01_1990 else 'no'} | {vv:.2f} | {int(bb)} | "
                   f"{'yes' if inn else 'no — ' + '; '.join(why)} |")
    out.append("")
    # the looser days the strict class lacks: their internals' percentiles, for the summary
    return {"point": point, "ci": ci, "passed": passed, "verdict": verdict, "n_oos": n,
            "n_low": int(low.sum()), "coefs": coefs, "last_yr": last_yr, "loose": loose, "near": near,
            "n_train": n_train, "rates": (o["y_b"].mean(), o["y_b"][low].mean(), o["y_c"].mean(),
                                          o["y_c"][low].mean())}


# ------------------------------------------------------------------ Part 9
def part9(d: Data, out: list[str]):
    g = d.px["^GSPC"].loc["1989-01-01":]
    gi = g.index
    r_all = g["ret"].dropna()
    lr = np.log1p(r_all)
    v20 = lr.rolling(20).var(ddof=1) * 252
    v60 = lr.rolling(60).var(ddof=1) * 252
    vix = d.fred.get("VIXCLS")
    vx_strict = vix.reindex(r_all.index)                      # the close's own value, or NaN
    vx = vix.reindex(gi.union(vix.index)).ffill(limit=5).reindex(r_all.index)
    sig_avg2 = ((np.sqrt(v20) + np.sqrt(v60)) / 2) ** 2
    expos = {
        "A. Part 3's rule (12% target, RV20, 0.25–1.5)": (0.12 ** 2 / v20).clip(0.25, 1.5),
        "B. A with a 0.5 floor": (0.12 ** 2 / v20).clip(0.5, 1.5),
        "C. VIX-based, (12 / VIX)², 0.25–1.5": ((12 / vx) ** 2).clip(0.25, 1.5),
        "D. A on the mean of RV20 and RV60": (0.12 ** 2 / sig_avg2).clip(0.25, 1.5),
        "E. A with a 10% target": (0.10 ** 2 / v20).clip(0.25, 1.5),
    }
    start = pd.Timestamp("1990-01-03")
    r = r_all.loc[start:]
    tb = d.fred.get("DTB3")
    y = tb.reindex(gi.union(tb.index)).ffill(limit=5).reindex(gi)
    rf = ((1 + y / 100) ** (1 / 252) - 1).shift(1).reindex(r.index)
    cost = 0.0002

    def stats(x):
        eq = (1 + x).cumprod()
        cagr = eq.iloc[-1] ** (252 / len(x)) - 1
        vol = x.std(ddof=1) * np.sqrt(252)
        xs = x - rf
        shx = xs.mean() / xs.std(ddof=1) * np.sqrt(252)
        mdd = (eq / eq.cummax() - 1).min()
        w20 = (eq / eq.shift(20) - 1).min()
        return cagr, vol, shx, mdd, w20

    def cm(eb):
        port = eb * r + (1 - eb) * rf
        drift = eb * (1 + r) / (1 + port)
        to = (drift - eb).abs().shift(1).fillna(eb)
        return port - to * cost, to

    out.append(_src_line(d, ["^GSPC", "VIXCLS", "DTB3"]))
    out.append(f"{r.index[0].date()} to {r.index[-1].date()}, n = {len(r):,} (from 1990-01-03, the first session "
               "with a prior-close VIXCLS for C, so A here differs from Part 6 by one day). Exposure is set at "
               "each close and held over the next session; the rest of the book is in, or borrowed at, FRED DTB3 "
               "at T-1 (carried at most 5 days, compounded to a 252-day year). Costs: 2bp × |Δexposure| each day "
               "for the variants, 2bp × the drift back to target for the constant mixes. RV20 and RV60: annualised "
               "sample stdev of the last 20 and 60 daily log returns; D averages the two vols, then applies A's "
               "formula. C reads VIXCLS at the close (carried at most 5 rows over FRED's holiday gaps for the "
               "backtest). Each variant's constant mix holds that variant's own average exposure. Price return, "
               "no dividends, as Parts 3 and 6. Premium = CAGR(mix) − CAGR(variant). Recovery = the drawdown "
               "avoided, |max drawdown(mix)| − |max drawdown(variant)|, in points (positive: the variant's "
               "drawdown is shallower).\n")
    out.append("| Strategy | CAGR | Ann. vol | Sharpe (excess of DTB3) | Max drawdown | Worst 20-session | Avg exposure | Ann. turnover | Premium | Recovery |")
    out.append("|---|---|---|---|---|---|---|---|---|---|")
    bh = stats(r - pd.Series(np.where(r.index == r.index[0], cost, 0.0), index=r.index))
    out.append(f"| Buy and hold | {bh[0]*100:.2f}% | {bh[1]*100:.2f}% | {bh[2]:.2f} | {bh[3]*100:.1f}% | "
               f"{bh[4]*100:.1f}% | 1.00 | 0.0x | — | — |")
    yrs = len(r) / 252
    res = {}
    for lbl, ex in expos.items():
        held = ex.shift(1).reindex(r.index)
        if held.isna().any():
            out.append(f"| {lbl} | gap ({int(held.isna().sum())} sessions without an exposure) | | | | | | | | |")
            continue
        to = held.diff().abs().fillna(held.iloc[0])
        x = held * r + (1 - held) * rf - to * cost
        a = stats(x)
        eb = float(held.mean())
        xm, tom = cm(eb)
        m = stats(xm)
        prem, rec = m[0] - a[0], abs(m[3]) - abs(a[3])
        res[lbl] = {"v": a, "m": m, "eb": eb, "to": to.sum() / yrs, "tom": tom.sum() / yrs,
                    "prem": prem, "rec": rec}
        out.append(f"| {lbl} | {a[0]*100:.2f}% | {a[1]*100:.2f}% | {a[2]:.2f} | {a[3]*100:.1f}% | {a[4]*100:.1f}% | "
                   f"{eb:.2f} | {to.sum()/yrs:.1f}x | {prem*100:+.2f}pp | {rec*100:+.1f}pp |")
        out.append(f"| — constant mix {eb:.2f} | {m[0]*100:.2f}% | {m[1]*100:.2f}% | {m[2]:.2f} | {m[3]*100:.1f}% | "
                   f"{m[4]*100:.1f}% | {eb:.2f} | {tom.sum()/yrs:.1f}x | | |")
    out.append("")
    out.append("### Part 9.1 Exposure on 5 Nov 2026\n")
    out.append("\"Held\" was set at the 4 Nov close and carried through 5 Nov; \"set\" is the exposure each rule sets "
               "at the 5 Nov close for 6 Nov. C's set value needs VIXCLS for 5 Nov, which FRED had not published "
               f"when the cache was pulled (last VIXCLS observation {vix.index[-1].date()}): gap, not carried.\n")
    out.append("| Variant | held on 2026-11-05 | set at the 2026-11-05 close |")
    out.append("|---|---|---|")
    t5 = pd.Timestamp("2026-11-05")
    t4 = pd.Timestamp("2026-11-04")
    expo_at = {}
    for lbl, ex in expos.items():
        if lbl.startswith("C."):
            vs = vx_strict.get(t4, np.nan)
            held_v = min(1.5, max(0.25, (12 / vs) ** 2)) if vs == vs else np.nan
            vs5 = vx_strict.get(t5, np.nan)
            set_v = min(1.5, max(0.25, (12 / vs5) ** 2)) if vs5 == vs5 else np.nan
        else:
            held_v = ex.get(t4, np.nan) if t5 in ex.index else np.nan
            set_v = ex.get(t5, np.nan)
        expo_at[lbl] = (held_v, set_v)
        out.append(f"| {lbl} | {fmt(held_v)} | {fmt(set_v)} |")
    out.append("")
    return {"res": res, "bh": bh, "expo": expo_at}


# ------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(REPO / "docs/studies/tail-days-2016-2026-data.md"))
    ap.add_argument("--cache", default=str(DEFAULT_CACHE),
                    help="pickle cache dir for the pulls (default ~/.cache/chester-study/tail_days; "
                         "'' for no cache)")
    a = ap.parse_args(argv)
    d = Data(Path(a.cache).expanduser() if a.cache else None)
    d.load()
    if "^GSPC" not in d.px:
        print("^GSPC unavailable:", d.errors.get("^GSPC"))
        return 1
    g = d.px["^GSPC"]
    out: list[str] = []
    out.append("# Tail days 2016–2026: data replay")
    out.append("")
    out.append(f"**Generated** {d.generated:%Y-%m-%d %H:%M} ET from data pulled {d.pulled_at:%Y-%m-%d %H:%M} ET by `tools/studies/tail_days.py` "
               "(branch `study/tail-days`). Companion to `docs/studies/tail-days-study-2026-11-05.md`. "
               "Study output only: no store, regime or report code was read or written.")
    out.append("")
    out.append("## 0. Sources and coverage\n")
    out.append("| Series | Source | First obs. | Last obs. (as of) |")
    out.append("|---|---|---|---|")
    for s in INDEX_SYMS + ETF_SYMS + CHECK_SYMS + EXTRA_SYMS:
        f, l = d.first_last(s) if s in d.px else ("gap", "gap")
        out.append(f"| {s} | Yahoo Finance via `altdata.sources.yfinance_source._fetch_symbol` "
                   f"(split-adj., dividends beside){' — ' + d.errors[s] if s in d.errors else ''} | {f} | {l} |")
    for fid in FRED_IDS:
        f, l = d.first_last(fid) if fid in d.fred else ("gap", "gap")
        out.append(f"| {fid} | {d.fred_via.get(fid, 'gap — ' + d.errors.get(fid, ''))} | {f} | {l} |")
    if d.ebp is not None:
        out.append(f"| EBP | Federal Reserve FEDS Notes CSV ({EBP_URL}) | {d.ebp.index[0]:%Y-%m} | {d.ebp.index[-1]:%Y-%m} |")
    else:
        out.append(f"| EBP | gap — {d.errors.get('EBP', '')} | gap | gap |")
    out.append("")
    last_gspc = g.index[-1].date().isoformat()
    missing = [x for x in BEST + WORST if pd.Timestamp(x) not in g.index]
    if missing:
        out.append(f"**Dates not in the ^GSPC series as pulled (last session {last_gspc}):** "
                   + ", ".join(missing) + ". Their own-day return prints \"gap\"; their T-1/T-5/T-20 rows "
                   "are computed on the trading calendar up to the last pulled session.\n")

    # ---------------- Part 1
    out.append("## 1. Condition replay\n")
    out.append("Each row is as of the close of the session k trading days before the tail day (T-k), on the "
               "^GSPC trading calendar. Columns: SPX = ^GSPC close; ret% = that session's return; DD% = drawdown "
               "from the trailing 252-session closing high; RV20 = annualised stdev of the last 20 daily log "
               "returns; >2%/20 = sessions with |ret| > 2% in the last 20 (inclusive); VIX = FRED VIXCLS; "
               "VIX-RV = VIX less RV20; VIX/3M = VIXCLS ÷ ^VIX3M; HY, IG = ICE BofA OAS via FRED "
               "(BAMLH0A0HYM2, BAMLC0A0CM) in bp, HYΔ20 its change over 20 observations; 10yΔ3/Δ5 = DGS10 "
               "change in bp over 3/5 observations; 2s10s = FRED T10Y2Y in bp; MOVE = ^MOVE; $Δ5% = DTWEXBGS "
               "5-observation change; RSP-SPY = 20-session total-return difference, pp; Sect>50d = sector SPDRs "
               "closing above their 50-session average / sectors with 50 sessions of history; Amihud pctl = "
               "SPY's 20-session mean of |ret| ÷ dollar volume, as a percentile of its own trailing 252 values "
               "(100 = least liquid). FRED values carry forward at most 5 calendar days; beyond that, \"gap\". "
               "OAS for a date is published the next morning.\n")
    out.append(f"Sources: Yahoo Finance via the repo's yfinance fetcher, last session {last_gspc}; FRED "
               f"({', '.join(sorted(set(d.fred_via.values())))}), each series' last observation in §0. "
               f"As of {d.pulled_at:%Y-%m-%d %H:%M} ET.\n")

    gi = g.index
    table = {}     # (side, date, k) -> row
    tday_ret = {}
    for side, dates in (("worst", WORST), ("best", BEST)):
        for ds in dates:
            dt = pd.Timestamp(ds)
            if dt in gi:
                pos = gi.get_loc(dt)
                tday_ret[ds] = g["ret"].iloc[pos] * 100
            else:
                pos = len(gi) if dt > gi[-1] else gi.searchsorted(dt)
                tday_ret[ds] = np.nan
            for k in OFFSETS:
                p = pos - k
                table[(side, ds, k)] = conditions(d, gi[p])
                table[(side, ds, k)]["_day"] = gi[p].date().isoformat()

    for k in OFFSETS:
        out.append(f"### 1.{OFFSETS.index(k)+1} T-{k}\n")
        hdr = ["Tail day", "side", "T ret", f"T-{k} date"] + [SHORT[c] for c in COLS]
        out.append("| " + " | ".join(hdr) + " |")
        out.append("|" + "---|" * len(hdr))
        for side, dates in (("worst", WORST), ("best", BEST)):
            for ds in dates:
                row = table[(side, ds, k)]
                out.append("| " + " | ".join([ds, side, fmt(tday_ret[ds], 2, sign=True), row["_day"]]
                                             + [cell(c, row[c]) for c in COLS]) + " |")
        out.append("")

    out.append("### 1.4 Medians across the ten worst and the ten best days\n")
    out.append("Median of the available values; n is the count of non-gap values behind each median "
               "(shown when below 10). Sect>50d is the median share in percent.\n")
    hdr = ["Group", "offset"] + [SHORT[c] for c in COLS]
    out.append("| " + " | ".join(hdr) + " |")
    out.append("|" + "---|" * len(hdr))
    medians = {}
    for side, dates in (("worst", WORST), ("best", BEST)):
        for k in OFFSETS:
            cells = []
            for c in COLS:
                vals = []
                for ds in dates:
                    v = table[(side, ds, k)][c]
                    if c == "Sectors >50d":
                        if v == "gap":
                            continue
                        a_, b_ = v.split("/")
                        v = int(a_) / int(b_) * 100
                    if v is None or (isinstance(v, float) and np.isnan(v)):
                        continue
                    vals.append(float(v))
                if not vals:
                    cells.append("gap")
                    continue
                m = float(np.median(vals))
                medians[(side, k, c)] = m
                nd = 0 if c in ("Sectors >50d", "|r|>2% days /20") else NDP.get(c, 2)
                s = fmt(m, nd) + ("%" if c == "Sectors >50d" else "")
                if len(vals) < len(dates):
                    s += f" (n={len(vals)})"
                cells.append(s)
            out.append("| " + " | ".join([f"ten {side}", f"T-{k}"] + cells) + " |")
    out.append("")

    # ---------------- Part 2 / 3
    out.append("## 2. Two-sided tail base rates, ^GSPC since 1950\n")
    p2 = part2(d, out)
    out.append("## 3. Vol-managed exposure backtest, ^GSPC since 1990\n")
    p3 = part3(d, out)

    # ---------------- spot checks feeding §4
    out.append("## 4. Spot checks against the study's approximate figures\n")
    out.append("Source: as §0. Each line is a figure the study marks (approx.) or states, and what the pulled data "
               "shows.\n")
    out.append("| Study figure | Data | Source |")
    out.append("|---|---|---|")
    vix = d.fred.get("VIXCLS")

    def gclose(ds):
        t = pd.Timestamp(ds)
        return g["close"].loc[t] if t in gi else np.nan

    def vx(ds):
        return asof(vix, pd.Timestamp(ds), 0)

    def hyv(ds):
        return asof(d.fred.get("BAMLH0A0HYM2"), pd.Timestamp(ds)) * 100

    chk = []
    chk.append(("2018: S&P ~20% below the 20 Sep high at the 24 Dec low",
                f"{(gclose('2018-12-24')/g['close'].loc['2018-09-20':'2018-09-21'].max()-1)*100:.1f}% (close to close, 20 Sep 2018 close {gclose('2018-09-20'):.2f}, 24 Dec {gclose('2018-12-24'):.2f})", "^GSPC"))
    chk.append(("2018: VIX ~36 at the low", f"VIXCLS 24 Dec 2018 = {fmt(vx('2018-12-24'))}", "VIXCLS"))
    chk.append(("2018: HY OAS ~530–540bp at the low", f"{fmt(hyv('2018-12-24'),0)} bp", "BAMLH0A0HYM2"))
    chk.append(("2020: VIX ~14 at the 19 Feb high", f"VIXCLS 19 Feb 2020 = {fmt(vx('2020-02-19'))}", "VIXCLS"))
    chk.append(("2020: HY OAS 350 → ~1,090bp by 23 Mar", f"19 Feb {fmt(hyv('2020-02-19'),0)} bp → 23 Mar {fmt(hyv('2020-03-23'),0)} bp", "BAMLH0A0HYM2"))
    chk.append(("2020: −12% week 24–28 Feb, VIX ~14 → ~40",
                f"^GSPC 21 Feb→28 Feb {(gclose('2020-02-28')/gclose('2020-02-21')-1)*100:.1f}%; VIX 21 Feb {fmt(vx('2020-02-21'))} → 28 Feb {fmt(vx('2020-02-28'))}", "^GSPC, VIXCLS"))
    chk.append(("2020: 23 Mar low 2,191 intraday", f"23 Mar close {gclose('2020-03-23'):.2f} (intraday low not pulled)", "^GSPC"))
    chk.append(("2020: VIX ~27 → 40 around 11 Jun", f"VIX 10 Jun {fmt(vx('2020-06-10'))}, 11 Jun {fmt(vx('2020-06-11'))}", "VIXCLS"))
    chk.append(("2022: 25% bear market to the 12 Oct low",
                f"{(gclose('2022-10-12')/g['close'].loc['2022-01-01':'2022-01-31'].max()-1)*100:.1f}% from the Jan 2022 closing high", "^GSPC"))
    chk.append(("2022: VIX ~26 and falling before 10 Nov", f"VIX 9 Nov {fmt(vx('2022-11-09'))}, 3 Nov {fmt(vx('2022-11-03'))}", "VIXCLS"))
    dl = d.fred.get("DGS10")
    chk.append(("2025: S&P ~8–10% below 19 Feb peak on 2 Apr",
                f"{(gclose('2025-04-02')/gclose('2025-02-19')-1)*100:.1f}%", "^GSPC"))
    chk.append(("2025: VIX ~21–22 on 2 Apr", f"VIX 2 Apr {fmt(vx('2025-04-02'))}", "VIXCLS"))
    chk.append(("2025: HY OAS ~260 → ~460bp by 7 Apr", f"19 Feb {fmt(hyv('2025-02-19'),0)} bp → 7 Apr {fmt(hyv('2025-04-07'),0)} bp", "BAMLH0A0HYM2"))
    chk.append(("2025: VIX 45 → ~60 intraday 7 Apr", f"VIX close 4 Apr {fmt(vx('2025-04-04'))}, 7 Apr {fmt(vx('2025-04-07'))}, 8 Apr {fmt(vx('2025-04-08'))}", "VIXCLS"))
    chk.append(("2025: 10y ~3.9% → ~4.5% in three sessions (8–9 Apr)",
                f"DGS10 4 Apr {fmt(asof(dl, pd.Timestamp('2025-04-04')))}%, 9 Apr {fmt(asof(dl, pd.Timestamp('2025-04-09')))}%, 11 Apr {fmt(asof(dl, pd.Timestamp('2025-04-11')))}%", "DGS10"))
    chk.append(("2026: 5 Nov −4.4% (Morningstar), S&P −4.1% intraday",
                f"^GSPC 5 Nov 2026 {fmt(tday_ret.get('2026-11-05'), 2, sign=True)}%", "^GSPC"))
    chk.append(("Pattern: 8 of 10 best days within a week of a worst day",
                f"^GSPC's own top/bottom 10: {p2['k_gspc']} of 10; on the study's twenty dates: {p2['k_mstar']} of 10", "^GSPC, §2.5"))
    # 2026 and the remaining claims
    def sret(sym, ds):
        p_ = d.px.get(sym)
        t = pd.Timestamp(ds)
        return p_["ret"].loc[t] * 100 if p_ is not None and t in p_.index else np.nan

    def cl(sym, ds):
        p_ = d.px.get(sym)
        t = pd.Timestamp(ds)
        return p_["close"].loc[t] if p_ is not None and t in p_.index else np.nan

    feb25 = vix.loc["2025-02-01":"2025-02-28"] if vix is not None else pd.Series(dtype=float)
    feb20 = vix.loc["2020-02-01":"2020-02-28"] if vix is not None else pd.Series(dtype=float)
    chk.append(("§3.1: first-day shocks came with VIX already 2–3x its February level",
                f"9 Mar 2020: T-1 VIX {fmt(vx('2020-03-06'))} vs Feb 2020 median {fmt(feb20.median())} "
                f"({vx('2020-03-06')/feb20.median():.1f}x); 3 Apr 2025: T-1 VIX {fmt(vx('2025-04-02'))} vs Feb 2025 "
                f"median {fmt(feb25.median())} ({vx('2025-04-02')/feb25.median():.1f}x)", "VIXCLS"))
    chk.append(("2020: 11 Jun came after a 45% rally",
                f"23 Mar close → 8 Jun close {(cl('^GSPC','2020-06-08')/cl('^GSPC','2020-03-23')-1)*100:+.1f}%", "^GSPC"))
    chk.append(("2025: 10y 3-session move into 9 Apr",
                "DGS10 " + ", ".join(f"{x[5:]} {fmt(asof(dl, pd.Timestamp(x), 0))}%" for x in
                                     ("2025-04-03", "2025-04-04", "2025-04-07", "2025-04-08", "2025-04-09",
                                      "2025-04-10", "2025-04-11")), "DGS10"))
    chk.append(("2026: 22 Oct −2.6% on AI-capex fears; 30 Oct \"worst day since June\"",
                f"^GSPC 22 Oct {fmt(sret('^GSPC','2026-10-22'),2,sign=True)}%, 30 Oct {fmt(sret('^GSPC','2026-10-30'),2,sign=True)}%; "
                f"^IXIC 22 Oct {fmt(sret('^IXIC','2026-10-22'),2,sign=True)}%, 30 Oct {fmt(sret('^IXIC','2026-10-30'),2,sign=True)}%", "^GSPC, ^IXIC"))
    ix = d.px.get("^IXIC")
    if ix is not None:
        oct_hi = ix["close"].loc["2026-10-01":"2026-10-31"]
        ytd_hi = ix["close"].loc["2026-01-01":"2026-11-05"]
        oct_m = (cl("^IXIC", "2026-10-30") / ix["close"].loc[:"2026-09-30"].iloc[-1] - 1) * 100
        chk.append(("2026: Nasdaq −11% from the 6 Oct record at 5 Nov; October its worst month in over a year",
                    f"^IXIC 5 Nov close {(cl('^IXIC','2026-11-05')/ytd_hi.max()-1)*100:.1f}% from its 2026 closing high "
                    f"({ytd_hi.idxmax().date()}); October 2026 {oct_m:+.1f}%", "^IXIC"))
    spx_oct = (cl("^GSPC", "2026-10-30") / g["close"].loc[:"2026-09-30"].iloc[-1] - 1) * 100
    chk.append(("2026 (context): S&P 500 in October", f"^GSPC October 2026 {spx_oct:+.1f}%", "^GSPC"))
    chk.append(("2026: 4 Nov index up while SPHB/SPLV fell 3.4%",
                f"^GSPC 4 Nov {fmt(sret('^GSPC','2026-11-04'),2,sign=True)}%; SPHB/SPLV 4 Nov "
                f"{fmt(((1+sret('SPHB','2026-11-04')/100)/(1+sret('SPLV','2026-11-04')/100)-1)*100,2,sign=True)}%", "^GSPC, SPHB, SPLV"))
    rank = int((r_all := g["ret"].loc["2016-11-07":"2026-11-05"]).rank().loc[pd.Timestamp("2026-11-05")]) \
        if pd.Timestamp("2026-11-05") in g.index else None
    chk.append(("2026: 5 Nov is the tenth-worst day of the decade (Morningstar)",
                f"on ^GSPC it ranks {rank} of {len(r_all):,} (1 = worst); 27 Feb 2020 ({fmt(sret('^GSPC','2020-02-27'),2,sign=True)}%) is ^GSPC's ninth"
                if rank else "gap", "^GSPC"))
    for a_, b_, c_ in chk:
        out.append(f"| {a_} | {b_} | {c_} |")
    out.append("")
    # ---------------- Parts 4-7 (the study's §6 replay parts)
    out.append("## Part 4. Vol-standardised tail base rates, ^GSPC since 1950\n")
    out.append("Parts 4–7 are numbered as the study's §6 cites them, apart from §§0–4 above.\n")
    part4(d, out)
    q90 = d.px["^GSPC"]["ret"].loc["1950-01-03":].dropna().quantile(0.90)
    out.append("## Part 5. Calm-surface openers, ^GSPC since 1990\n")
    p5 = part5(d, out, q90)
    out.append("## Part 6. Vol-managed exposure against a matched constant mix, ^GSPC since 1990\n")
    part6(d, out)
    out.append("## Part 7. Credit substitute: BAA10Y and the excess bond premium\n")
    part7(d, out)
    out.append("## Part 8. Internal-stress test (106c(ii), pre-registered in the study's §5)\n")
    p8 = part8(d, out, p5["q01"], q90)
    out.append("## Part 9. Vol-managed variants priced as premium and recovery (106g(i)), ^GSPC since 1990\n")
    p9 = part9(d, out)

    marker = "<!-- CONTRADICTS -->"
    cmark = "<!-- NEW-PARTS-CHANGE -->"
    m89 = "<!-- PARTS-8-9-CHANGE -->"
    keep, ckeep, keep89 = "", "", ""
    op = Path(a.out)
    if op.exists():                       # the hand-written sections survive a re-run
        old = op.read_text(encoding="utf-8")
        if marker in old:
            head, keep = old.split(marker, 1)
            keep = keep.lstrip("\n")
            if cmark in head:
                pre, ckeep = head.split(cmark, 1)
                ckeep = ckeep.strip("\n") + "\n"
                if m89 in pre:
                    keep89 = pre.split(m89, 1)[1].strip("\n") + "\n"
    out.append(m89)
    out.append(keep89 or "## What parts 8-9 change\n\n(hand-written; the script keeps this section when it "
               "is re-run)\n")
    out.append(cmark)
    out.append(ckeep or "## What the new parts change\n\n(hand-written; the script keeps this "
               "section when it is re-run)\n")
    out.append(marker)
    Path(a.out).write_text("\n".join(out) + "\n" + keep, encoding="utf-8")
    print(f"wrote {a.out}")
    for k_, v_ in d.errors.items():
        print(f"error {k_}: {v_}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
