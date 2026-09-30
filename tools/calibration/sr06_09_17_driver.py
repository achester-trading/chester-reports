"""
SR-6 / SR-9 / SR-17 -- the rates driver's calibration study (signal-triage ST-3).

    python tools/calibration/sr06_09_17_driver.py                # writes the ledger
    python tools/calibration/sr06_09_17_driver.py --out PATH     # somewhere else
    python tools/calibration/sr06_09_17_driver.py --refresh      # re-download

The offline rule (tools/calibration/README.md): full history pulled straight from
each publisher, the observation store never read, one dated ledger per run.

RERUN 2 (30 Sep 2026) is judged against a pre-registration committed before its
code: docs/ledgers/rates-driver-2026-09-30-r2-preregistration.md. Rerun 1's
script is in git history (17e5882) with its ledger, rates-driver-2026-09.md.

WHAT IS CALIBRATED IS THE OBJECT'S OWN RULE. `regime.driver_cell` is imported --
the one thing this directory may take from regime -- and called on every session
with inputs rebuilt here from the published history. The INPUTS are rebuilt, not
read: each follows the definition of its calc.* series in
altdata/market_features.py (rates_rows) -- a window counted in the denominator's
own observations, same-day endpoints, no share below a 5bp denominator -- and the
rule spec is read from config/market_state.yaml as the object reads it.

THE PARSERS ARE THE FEEDS' OWN. The DKW CSV, the ACM workbook and the SF Fed
workbook are parsed by the same functions altdata/sources/ uses, so a shape
change breaks this script the way it breaks the feed, not differently.

WHAT THE HISTORY CANNOT TELL US, stated in the ledger rather than discovered by a
reader: the model term premia are TODAY'S re-estimates of the past, not what was
knowable then (no vintages are published); DFII10 starts in January 2003, so 1994
has no real/breakeven cut and no path-side cell can be tested there; TLT starts
July 2002, so correlation before it uses a constant-maturity duration proxy.
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from altdata.sources import acm, dkw, sffed          # noqa: E402  parsers only
from altdata.sources import _publication as pub      # noqa: E402  read_xlsx only
from altdata.sources._base import http_get_response  # noqa: E402
from regime import driver_cell                       # noqa: E402  the ONE import

CACHE = Path(tempfile.gettempdir()) / "chester-calibration"
LEDGER = REPO / "docs" / "ledgers" / "rates-driver-2026-09-30-r2.md"
PREREG = "rates-driver-2026-09-30-r2-preregistration.md"
CONFIG = REPO / "config" / "market_state.yaml"

# The features' own constants (altdata/market_features.py), restated because this
# script may not import that module's store-reading half. Checked against it at
# run time below, so a change there cannot pass silently here.
WINDOW = 60
SHORT = 20                  # H1's window: a member of ATTR_WINDOWS
MIN_MOVE_BP = 5.0
CORR_WINDOW = 60
FWD_3M, FWD_6M = 63, 126
# DKW's live lag: the Board republishes monthly and on 30 Sep 2026 the last row
# was 31 Aug. The "live" variant reads DKW as of this many sessions earlier.
DKW_LIVE_LAG = 21
# Before TLT exists, a constant-maturity 10-year bond's daily return from DGS10:
# carry minus duration x change. Duration 8.5 is a 10-year par bond near 4-6%.
PROXY_DURATION = 8.5

# ---------------------------------------------------------------------------
# THE EPISODES -- unchanged from rerun 1, as pre-registered. Windows run from the
# start of the yield move to its peak. "Q4 2018" is the order's label; the
# selloff leg it names ran from late August to the 8 Nov peak.
# ---------------------------------------------------------------------------
EPISODES = [
    {"id": "1994", "start": "1994-02-04", "end": "1994-11-07",
     "set": "bear_flattening", "expect": "fed_path", "sr17": False,
     "what": "Fed hikes from 3% to 5.5%; 10y 5.6% -> 8.0%, 2y faster"},
    {"id": "Q4 2018", "start": "2018-08-22", "end": "2018-11-08",
     "set": "bear_flattening", "expect": "fed_path", "sr17": True,
     "what": "the last leg of the 2015-18 cycle into the 3.24% peak"},
    {"id": "2022", "start": "2022-01-03", "end": "2022-10-21",
     "set": "bear_flattening", "expect": "fed_path", "sr17": True,
     "what": "the fastest hiking cycle since 1981; 2y leads, breakevens fall"},
    {"id": "2013", "start": "2013-05-02", "end": "2013-09-05",
     "set": "bear_steepening", "expect": "term_premium", "sr17": True,
     "what": "the taper tantrum: front end anchored at zero, long end reprices"},
    {"id": "Aug-Oct 2023", "start": "2023-07-31", "end": "2023-10-19",
     "set": "bear_steepening", "expect": "term_premium", "sr17": True,
     "what": "the refunding and term-premium selloff to 5%; Fed on hold"},
]
FULL_SAMPLE_FROM = "2003-06-01"          # first date every cut can exist
SIDE_BY_SIDE = ("2026-02-01", "2026-09-30")

GRID = {"share_min": (0.5, 0.6, 0.7), "move_floor_bp": (10, 15, 25),
        "front_anchored": (0.4, 0.5, 0.6)}


# ---------------------------------------------------------------------------
# Fetching -- straight from each publisher, cached for reruns
# ---------------------------------------------------------------------------
def _get(name: str, url: str, refresh: bool) -> bytes:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / name
    if f.exists() and not refresh:
        return f.read_bytes()
    data, _ = http_get_response(url, timeout=180)
    f.write_bytes(data)
    return data


def fred(series_id: str, refresh: bool) -> pd.Series:
    """Full history from FRED's public graph CSV (no key needed)."""
    raw = _get(f"fred_{series_id}.csv",
               f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}",
               refresh)
    df = pd.read_csv(io.BytesIO(raw), na_values=".")
    return pd.Series(df.iloc[:, 1].values, index=pd.to_datetime(df.iloc[:, 0]),
                     name=series_id, dtype=float).dropna()


def _pivot(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    out = df.pivot_table(index="observed_at", columns="registry_key",
                         values="value", aggfunc="last")
    out.index = pd.to_datetime(out.index)
    return out.sort_index()


def fetch_dkw(refresh: bool) -> pd.DataFrame:
    raw = _get("dkw.csv", dkw.URL, refresh)
    return _pivot(dkw.rows_from_csv(raw.decode("utf-8", errors="replace"),
                                    "n/a", "calibration"))


def fetch_acm(refresh: bool) -> pd.DataFrame:
    import xlrd
    raw = _get("acm.xls", acm.URL, refresh)
    sheet = xlrd.open_workbook(file_contents=raw).sheet_by_name(acm.SHEET)
    table = [sheet.row_values(r) for r in range(sheet.nrows)]
    return _pivot(acm.rows_from_table(table, "n/a", "calibration"))


def fetch_sffed(refresh: bool) -> pd.DataFrame:
    raw = _get("sffed.xlsx", sffed.URL, refresh)
    return _pivot(sffed.rows_from_workbook(pub.read_xlsx(raw), "n/a",
                                           "calibration"))


def fetch_prices(refresh: bool) -> pd.DataFrame:
    f = CACHE / "prices.csv"
    if f.exists() and not refresh:
        return pd.read_csv(f, index_col=0, parse_dates=True)
    import yfinance as yf
    px = yf.download(["SPY", "TLT", "^GSPC"], start="1990-01-01",
                     auto_adjust=True, progress=False)["Close"]
    px.columns = [c.replace("^", "") for c in px.columns]
    CACHE.mkdir(parents=True, exist_ok=True)
    px.to_csv(f)
    return px


# ---------------------------------------------------------------------------
# The inputs, rebuilt on market_features' definitions
# ---------------------------------------------------------------------------
def window_change(num: pd.Series, den: pd.Series, w: int) -> pd.Series:
    """Δnum/Δden over `w` of the pair's common observations, in bp both.

    Common days only, and the window counted in them: the features' rule that
    both series must be on both endpoints, with no carry-forward.
    """
    df = pd.concat([num.rename("n"), den.rename("d")], axis=1).dropna()
    dd = (df["d"] - df["d"].shift(w)) * 100.0
    dn = (df["n"] - df["n"].shift(w)) * 100.0
    return (dn / dd).where(dd.abs() >= MIN_MOVE_BP)


def build_inputs(d: dict) -> pd.DataFrame:
    """One row per 10-year session: every number driver_cell() is handed."""
    y10 = d["DGS10"]
    move = (y10 - y10.shift(WINDOW)) * 100.0
    move20 = (y10 - y10.shift(SHORT)) * 100.0
    real = window_change(d["DFII10"], y10, WINDOW).reindex(move.index)
    real20 = window_change(d["DFII10"], y10, SHORT).reindex(move.index)
    curve = window_change(d["DGS2"], y10, WINDOW).reindex(move.index)
    kw_share = window_change(d["THREEFYTP10"], y10, WINDOW)
    a = d["acm"]
    acm_share = window_change(a["acm.term_premium_10y"],
                              a["acm.fitted_yield_10y"], WINDOW)
    # (a): path and premium as shares of THEIR OWN SUM, liquidity left out --
    # and, like the feature, on the days path and premium exist. The liquidity
    # column starts in 1999 while path and premium start in 1983; requiring it
    # here (as the first draft of this rerun did) silently removed DKW from 1994.
    k = d["dkw"][["dkw.exp_real_short_rate_10y",
                  "dkw.real_term_premium_10y"]].dropna()
    dk = k - k.shift(WINDOW)
    pp = dk["dkw.exp_real_short_rate_10y"] + dk["dkw.real_term_premium_10y"]
    ok = (pp.abs() * 100.0) >= MIN_MOVE_BP
    dkw_path = (dk["dkw.exp_real_short_rate_10y"] / pp).where(ok)
    dkw_prem = (dk["dkw.real_term_premium_10y"] / pp).where(ok)
    # Diagnosis only: the liquidity leg's share of the whole real move, 1999 on.
    k3 = d["dkw"][["dkw.exp_real_short_rate_10y", "dkw.real_term_premium_10y",
                   "dkw.tips_liquidity_premium_10y"]].dropna()
    whole = (k3 - k3.shift(WINDOW)).sum(axis=1)
    dkw_liq = ((k3 - k3.shift(WINDOW))["dkw.tips_liquidity_premium_10y"]
               / whole).where((whole.abs() * 100.0) >= MIN_MOVE_BP)

    def model_change(s: pd.Series, h: int) -> pd.Series:
        s = s.dropna()
        return (s - s.shift(h)) * 100.0

    models = {
        "kw": model_change(d["THREEFYTP10"], 60),
        "acm": model_change(a["acm.term_premium_10y"], 60),
        "sffed": model_change(d["sffed"]["sffed.term_premium_10y"], 12),
        "dkw": model_change(d["dkw"]["dkw.real_term_premium_10y"], 60),
    }

    px = d["prices"]
    both = px[["SPY", "TLT"]].dropna()
    r = np.log(both).diff()
    corr_live = r["SPY"].rolling(CORR_WINDOW).corr(r["TLT"])
    g = px["GSPC"].dropna()
    y = y10.reindex(g.index).ffill()
    bond = (y.shift(1) / 100.0 / 252.0) - PROXY_DURATION * (y - y.shift(1)) / 100.0
    corr_proxy = np.log(g).diff().rolling(CORR_WINDOW).corr(bond)
    corr = corr_live.combine_first(corr_proxy[corr_proxy.index < both.index[0]])

    idx = move.index

    def at(s: pd.Series, lag: int = 0) -> pd.Series:
        """The latest value at or before each session, optionally `lag` back.
        A series whose history has not started is ABSENT, not carried back."""
        s = s.dropna()
        out = s.reindex(idx.union(s.index)).ffill().reindex(idx)
        if len(s):
            out[out.index < s.index.min()] = np.nan
        return out.shift(lag) if lag else out

    frame = pd.DataFrame({
        "move": move, "move20": move20, "real": real, "real20": real20,
        "curve": curve,
        "dkw_path": at(dkw_path), "dkw_prem": at(dkw_prem), "dkw_liq": at(dkw_liq),
        "dkw_path_live": at(dkw_path, DKW_LIVE_LAG),
        "dkw_prem_live": at(dkw_prem, DKW_LIVE_LAG),
        "kw_share": at(kw_share), "acm_share": at(acm_share),
        "m_kw": at(models["kw"]), "m_acm": at(models["acm"]),
        "m_sffed": at(models["sffed"]), "m_dkw": at(models["dkw"]),
        "m_dkw_live": at(models["dkw"], DKW_LIVE_LAG),
        "corr": at(corr), "gspc": at(px["GSPC"]),
    }, index=idx)
    frame["be60"] = frame["move"] * (1.0 - frame["real"]) * np.sign(frame["move"])
    frame["be20"] = frame["move20"] * (1.0 - frame["real20"]) * np.sign(frame["move"])
    frame["fwd_3m"] = frame["gspc"].shift(-FWD_3M) / frame["gspc"] - 1.0
    frame["fwd_6m"] = frame["gspc"].shift(-FWD_6M) / frame["gspc"] - 1.0
    return frame


def _v(x) -> float | None:
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else float(x)


def inputs_for(row: pd.Series, live: bool = False) -> dict:
    """The dict driver_cell() takes, from one session's row."""
    def lv(x, metric):
        x = _v(x)
        return ({"metric": metric, "level": x} if x is not None else
                {"metric": metric, "level": None,
                 "absent_reason": f"{metric} has no value in the history here"})
    pp = row["dkw_path_live" if live else "dkw_path"]
    pq = row["dkw_prem_live" if live else "dkw_prem"]
    primary = ({"model": "dkw", "path_share": _v(pp), "premium_share": _v(pq)}
               if _v(pp) is not None and _v(pq) is not None else
               {"model": "dkw", "path_share": None, "premium_share": None,
                "absent_reason": "no DKW split at this session"})
    ties = []
    for m, col in (("kw", "kw_share"), ("acm", "acm_share")):
        q = _v(row[col])
        ties.append({"model": m, "premium_share": q,
                     **({} if q is not None else
                        {"absent_reason": f"no {m} share at this session"})})
    models = []
    for name, col in (("kw", "m_kw"), ("acm", "m_acm"), ("sffed", "m_sffed"),
                      ("dkw", "m_dkw_live" if live else "m_dkw")):
        c = _v(row[col])
        models.append({"name": name, "change_bp": c, "arbiter": name == "dkw",
                       **({} if c is not None else
                          {"absent_reason": f"no {name} reading"})})
    return {"move": lv(row["move"], "move"), "real_share": lv(row["real"], "real"),
            "curve_share": lv(row["curve"], "curve"),
            f"move_{SHORT}d": lv(row["move20"], "move20"),
            f"real_share_{SHORT}d": lv(row["real20"], "real20"),
            "primary": primary, "tie_breakers": ties, "models": models,
            "evidence": [lv(row["corr"], "calc.corr_spy_tlt_60d")]}


_INPUTS: dict[tuple[int, bool], list] = {}


def replay(frame: pd.DataFrame, spec: dict, live: bool = False) -> pd.DataFrame:
    """driver_cell() on every session. The inputs are built once per frame and
    variant and reused across the grid -- only the thresholds change."""
    key = (id(frame), live)
    if key not in _INPUTS:
        _INPUTS[key] = [(day, inputs_for(row, live))
                        for day, row in frame.iterrows()
                        if _v(row["move"]) is not None]
    rows = []
    for day, inp in _INPUTS[key]:
        c = driver_cell(inp, spec)
        rows.append({"day": day, "cell": c["raw_state"] or "not_determined",
                     "direction": c.get("direction"),
                     "decided_by": c.get("decided_by"),
                     "arbitrated": bool(c.get("arbitration")),
                     "why": (c.get("undecided_reason")
                             or c.get("not_determined_reason") or c["raw_state"])})
    return pd.DataFrame(rows).set_index("day")


# ---------------------------------------------------------------------------
# The pass rule, exactly as pre-registered (c)
# ---------------------------------------------------------------------------
def agreement(frame: pd.DataFrame, ep: dict, share_min: float) -> dict:
    """Per episode: each available decomposition's side from its MEDIAN share."""
    seg = frame.loc[ep["start"]:ep["end"]]
    paths = {"dkw": seg["dkw_path"], "kw": 1.0 - seg["kw_share"],
             "acm": 1.0 - seg["acm_share"]}
    sides, meds = {}, {}
    for m, s in paths.items():
        s = s.dropna()
        if not len(s):
            continue
        p = float(s.median())
        meds[m] = p
        sides[m] = ("path" if p >= share_min else
                    "premium" if (1.0 - p) >= share_min else None)
    named = set(sides.values())
    agree = bool(sides) and None not in named and len(named) == 1
    return {"sides": sides, "median_path": meds, "agree": agree,
            "side": named.pop() if agree else None}


def score_episode(cells: pd.DataFrame, ep: dict, agree: bool) -> dict:
    w = cells.loc[ep["start"]:ep["end"]]
    counts = w["cell"].value_counts()
    det = w[w["cell"] != "not_determined"]
    ok_cells = {ep["expect"]} if agree else {ep["expect"], "mixed"}
    if len(det):
        vc = det["cell"].value_counts()
        top = vc[vc == vc.max()].index.tolist()
        modal = top[0] if len(top) == 1 else " / ".join(sorted(top))
        passed = all(t in ok_cells for t in top)
    else:
        modal, passed = None, False
    share = (det["cell"] == ep["expect"]).mean() if len(det) else float("nan")
    return {"n": len(w), "determined": len(det), "counts": counts.to_dict(),
            "modal": modal, "expected_share": share, "pass": passed,
            "ok_cells": sorted(ok_cells)}


def pct(x: float) -> str:
    return "—" if x is None or x != x else f"{100 * x:.0f}%"


def spec_with(base: dict, **th) -> dict:
    return {**base, "thresholds": {**base["thresholds"], **th}}


def score_all(cells, frame, spec) -> dict:
    sm = float(spec["thresholds"]["share_min"])
    out = {}
    for e in EPISODES:
        ag = agreement(frame, e, sm)
        out[e["id"]] = {**score_episode(cells, e, ag["agree"]), "agreement": ag}
    return out


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--out", default=str(LEDGER))
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing ledger (a rerun writes a NEW one)")
    a = ap.parse_args(argv)
    out = Path(a.out)
    if out.exists() and not a.force:
        print(f"{out} exists; ledgers are never edited. Pass --out for a new one.")
        return 2
    if not (REPO / "docs" / "ledgers" / PREREG).exists():
        print(f"the pre-registration {PREREG} is missing; refusing to run")
        return 4

    feat = (REPO / "altdata" / "market_features.py").read_text(encoding="utf-8")
    for needle in (f"\nMODEL_WINDOW = {WINDOW}", f"\nATTR_MIN_MOVE_BP = {MIN_MOVE_BP}",
                   f"\nCORR_WINDOW = {CORR_WINDOW}", f"ATTR_WINDOWS = (5, {SHORT}, 60)",
                   "d_sum = d_ers + d_rtp\n"):
        if needle not in feat:
            print(f"market_features no longer has {needle.strip()!r}; update this script")
            return 3

    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    spec = cfg["dimensions"]["rates"]["driver"]
    print(f"config {cfg['version']}: thresholds {spec['thresholds']}")
    print(f"rules {spec['rules']}")

    print("fetching ...")
    d = {sid: fred(sid, a.refresh)
         for sid in ("DGS10", "DGS2", "DFII10", "THREEFYTP10")}
    d["dkw"], d["acm"], d["sffed"] = (fetch_dkw(a.refresh), fetch_acm(a.refresh),
                                      fetch_sffed(a.refresh))
    d["prices"] = fetch_prices(a.refresh)
    spans = {k: (v.index.min().date(), v.index.max().date(), len(v))
             for k, v in (("DGS10", d["DGS10"]), ("DGS2", d["DGS2"]),
                          ("DFII10", d["DFII10"]),
                          ("THREEFYTP10 (Kim-Wright)", d["THREEFYTP10"]),
                          ("DKW", d["dkw"]), ("ACM", d["acm"]),
                          ("SF Fed", d["sffed"].dropna(how="all")),
                          ("SPY", d["prices"]["SPY"].dropna()),
                          ("TLT", d["prices"]["TLT"].dropna()),
                          ("^GSPC", d["prices"]["GSPC"].dropna()))}

    # 1990 on: the 1994 episode's window reaches back into 1993.
    frame = build_inputs(d).loc["1990-01-01":]
    base = replay(frame, spec)
    live = replay(frame, spec, live=True)
    res = score_all(base, frame, spec)
    res_live = score_all(live, frame, spec)
    print(f"replayed {len(base)} sessions")

    grid_pass = {e["id"]: 0 for e in EPISODES}
    n_grid, all_five = 0, 0
    for sm in GRID["share_min"]:
        for mf_ in GRID["move_floor_bp"]:
            for fa in GRID["front_anchored"]:
                n_grid += 1
                sp = spec_with(spec, share_min=sm, move_floor_bp=mf_,
                               front_anchored=fa)
                r = score_all(replay(frame, sp), frame, sp)
                for k, v in r.items():
                    grid_pass[k] += bool(v["pass"])
                all_five += all(v["pass"] for v in r.values())

    n_agree = sum(r["agreement"]["agree"] for r in res.values())
    p_agree = sum(r["pass"] for r in res.values() if r["agreement"]["agree"])
    n_dis = len(EPISODES) - n_agree
    p_dis = sum(r["pass"] for r in res.values() if not r["agreement"]["agree"])
    gate = all(r["pass"] for r in res.values())

    fs = base.loc[FULL_SAMPLE_FROM:].join(frame[["corr", "fwd_3m", "fwd_6m"]])
    by_cell = fs.groupby("cell").agg(
        sessions=("corr", "size"), corr_mean=("corr", "mean"),
        corr_pos=("corr", lambda s: (s > 0).mean()),
        fwd3_mean=("fwd_3m", "mean"), fwd6_mean=("fwd_6m", "mean"),
        fwd6_med=("fwd_6m", "median"),
        fwd6_pos=("fwd_6m", lambda s: (s.dropna() > 0).mean()))
    by_cell_dir = fs.groupby(["cell", "direction"]).size().unstack(fill_value=0)
    decided = fs[fs["cell"] != "not_determined"]
    arb_rate = decided["arbitrated"].mean() if len(decided) else float("nan")

    sbs = frame.loc[SIDE_BY_SIDE[0]:SIDE_BY_SIDE[1],
                    ["move", "m_kw", "m_acm", "m_sffed", "m_dkw"]]
    month_end = sbs.groupby(sbs.index.to_period("M")).tail(1)
    b26 = base.loc[SIDE_BY_SIDE[0]:SIDE_BY_SIDE[1]]
    db = spec["thresholds"]["sign_deadband_bp"]

    def sgn(x):
        x = _v(x)
        return "—" if x is None else ("0" if abs(x) < db else ("+" if x > 0 else "−"))

    # --- the ledger --------------------------------------------------------------
    today = dt.date.today().isoformat()
    L: list[str] = []
    w = L.append
    w("# Rates driver — calibration ledger, rerun 2 (SR-6, SR-9, SR-17)")
    w("")
    w(f"*Run {today} by `tools/calibration/sr06_09_17_driver.py` against config "
      f"`{cfg['version']}`. Judged against the pre-registration "
      f"[{PREREG}]({PREREG}), committed before this rerun's code. Dated; never "
      "edited.*")
    w("")
    w(f"## Verdict: the gate {'PASSES' if gate else 'FAILS'}")
    w("")
    w(f"- **{sum(r['pass'] for r in res.values())} of {len(EPISODES)}** episodes "
      "pass under the pre-registered rule (c); the gate needs all five.")
    w(f"- Models **agree** on the driver in {n_agree} episode(s): **{p_agree} "
      f"pass** (the modal cell must be the expected one).")
    w(f"- Models **disagree** in {n_dis} episode(s): **{p_dis} pass** (the "
      "expected cell or `mixed` counts).")
    w(f"- Robustness only, not the verdict: {all_five} of {n_grid} grid points "
      "pass all five.")
    w("")
    w("## What changed since rerun 1 — as pre-registered, and one disclosure")
    w("")
    w("- **(a)** DKW's shares are of path + premium; the TIPS liquidity premium is "
      "out of the denominator.")
    w(f"- **(b) H1**: `fed_path` tests breakevens over {SHORT} sessions, signed to "
      "the 60-session move. `growth` keeps the 60-session breakevens. Thresholds "
      "are v1.11's, unchanged.")
    w("- **(c)** The pass rule below.")
    w("- **Disclosed, beyond H1's letter** (commit 12f4fdd): a rule with a "
      "condition *known false* now fails even when another of its inputs is "
      "absent. Before H1 all of a rule's conditions read one window, so this "
      "could not arise. With every input present, outcomes are unchanged.")
    w("")
    w("## SR-6's episode sets under rule (c)")
    w("")
    w("Agreement is per episode: each available decomposition's **median** "
      "60-session path share over the window names a side (`path` ≥ share_min, "
      "`premium` when 1 − path ≥ share_min, else none). Agree means every "
      "available decomposition names the same side.")
    w("")
    w("| Episode | Set | Expected | DKW / KW / ACM median path share | Sides | Agree | Determined / sessions | Cells | Modal | Passing cells | Base | Live DKW lag | Grid (of "
      f"{n_grid}) |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for e in EPISODES:
        r, ag = res[e["id"]], res[e["id"]]["agreement"]
        meds = " / ".join(f"{ag['median_path'][m]:.2f}" if m in ag["median_path"]
                          else "—" for m in ("dkw", "kw", "acm"))
        sides = ", ".join(f"{m} {s or 'none'}" for m, s in ag["sides"].items())
        cells = ", ".join(f"{k} {v}" for k, v in sorted(r["counts"].items(),
                                                          key=lambda kv: -kv[1]))
        w(f"| {e['id']} | {e['set'].replace('_', ' ')} | {e['expect']} | {meds} "
          f"| {sides} | {'yes' if ag['agree'] else 'no'} "
          f"| {r['determined']} / {r['n']} | {cells} | {r['modal'] or '—'} "
          f"| {', '.join(r['ok_cells'])} | {'PASS' if r['pass'] else 'FAIL'} "
          f"| {'PASS' if res_live[e['id']]['pass'] else 'FAIL'} "
          f"({res_live[e['id']]['modal'] or '—'}) | {grid_pass[e['id']]} |")
    w("")
    for e in EPISODES:
        w(f"- **{e['id']}** ({e['start']} → {e['end']}) — {e['what']}.")
    w("")
    w("## Inside each episode")
    w("")
    w("Medians over the window. `be 60` / `be 20` are breakevens' change, in bp, "
      "signed to the 60-session move (negative = against it; H1 reads `be 20`). "
      "`dkw liq` is the liquidity leg's share of the whole real move, now outside "
      "the denominator.")
    w("")
    w("| Episode | Δ10y | be 60 | be 20 | curve share | dkw path | dkw prem | dkw liq | be 20 against, % of sessions |")
    w("|---|---|---|---|---|---|---|---|---|")
    th = spec["thresholds"]
    for e in EPISODES:
        seg = frame.loc[e["start"]:e["end"]]
        m = seg.median(numeric_only=True)
        against = (seg["be20"] < -th["be_flat_bp"]).where(seg["be20"].notna())

        def g(x, f="{:.2f}"):
            x = _v(x)
            return "—" if x is None else f.format(x)
        w(f"| {e['id']} | {g(m['move'], '{:+.0f}')} | {g(m['be60'], '{:+.0f}')} "
          f"| {g(m['be20'], '{:+.0f}')} | {g(m['curve'])} | {g(m['dkw_path'])} "
          f"| {g(m['dkw_prem'])} | {g(m['dkw_liq'])} "
          f"| {pct(against.dropna().mean()) if against.notna().any() else '—'} |")
    w("")
    w("What decided each session:")
    w("")
    for e in EPISODES:
        seg = base.loc[e["start"]:e["end"]]
        why = seg["why"].fillna("—").str.split(" -- ").str[0].str.split(" \\(").str[0]
        why = why.where(~why.str.contains("move floor"),
                        f"below the {th['move_floor_bp']}bp move floor")
        vc = why.value_counts()
        w(f"- **{e['id']}**: " + "; ".join(f"{k} ({v})" for k, v in vc.items()))
    w("")
    w("## Data source and vintage")
    w("")
    w("| Series | From | To | n |")
    w("|---|---|---|---|")
    for k, (s, e_, n) in spans.items():
        w(f"| {k} | {s} | {e_} | {n:,} |")
    w("")
    w(f"Downloaded {today}; the publishers' own files, parsed by the feeds' "
      "parsers. **Model term premia are today's re-estimates of the past**, not "
      "what was knowable then. DFII10 starts January 2003, so 1994 cannot test a "
      "path-side cell. Before TLT (July 2002) the correlation uses ^GSPC against "
      f"a constant-maturity 10-year (carry less {PROXY_DURATION} × Δyield).")
    w("")
    w("## SR-17: forward equity outcomes by cell inside its four episodes")
    w("")
    w("Base rate only. ^GSPC forward returns; overlapping windows.")
    w("")
    w("| Episode | Cell | Sessions | Fwd 3m mean | Fwd 6m mean | Fwd 6m > 0 |")
    w("|---|---|---|---|---|---|")
    for e in [x for x in EPISODES if x["sr17"]]:
        seg = base.loc[e["start"]:e["end"]].join(frame[["fwd_3m", "fwd_6m"]])
        for c, g_ in seg.groupby("cell"):
            w(f"| {e['id']} | {c} | {len(g_)} | {pct(g_['fwd_3m'].mean())} "
              f"| {pct(g_['fwd_6m'].mean())} "
              f"| {pct((g_['fwd_6m'].dropna() > 0).mean())} |")
    w("")
    w(f"## The full sample, {FULL_SAMPLE_FROM} to the last session")
    w("")
    w("| Cell | Sessions | Share | Corr mean | Corr > 0 | Fwd 3m mean | Fwd 6m mean | Fwd 6m median | Fwd 6m > 0 |")
    w("|---|---|---|---|---|---|---|---|---|")
    tot = by_cell["sessions"].sum()
    for c, r in by_cell.sort_values("sessions", ascending=False).iterrows():
        w(f"| {c} | {int(r['sessions']):,} | {pct(r['sessions'] / tot)} "
          f"| {r['corr_mean']:+.2f} | {pct(r['corr_pos'])} | {pct(r['fwd3_mean'])} "
          f"| {pct(r['fwd6_mean'])} | {pct(r['fwd6_med'])} | {pct(r['fwd6_pos'])} |")
    w("")
    cols = list(by_cell_dir.columns)
    w("| Cell | " + " | ".join(str(c) for c in cols) + " |")
    w("|---|" + "---|" * len(cols))
    for c, r in by_cell_dir.iterrows():
        w(f"| {c} | " + " | ".join(f"{int(r[x]):,}" for x in cols) + " |")
    w("")
    w(f"The models disagreed on sign and DKW arbitrated on {pct(arb_rate)} of "
      "determined sessions.")
    w("")
    w(f"## SR-6: the four models side by side, {SIDE_BY_SIDE[0]} to {SIDE_BY_SIDE[1]}")
    w("")
    w("60-observation term-premium change in bp (SF Fed: 12 weekly prints) at each "
      "month's last session; sign outside the 5 bp dead-band. DKW's last row is "
      "31 Aug, so September carries August forward, as the live object would.")
    w("")
    w("| Month end | Δ10y | Kim-Wright | ACM | SF Fed | DKW (real) | Cell |")
    w("|---|---|---|---|---|---|---|")
    for day, r in month_end.iterrows():
        def f(x):
            x = _v(x)
            return "—" if x is None else f"{x:+.0f} ({sgn(x)})"
        mv = _v(r["move"])
        w(f"| {day.date()} | {'—' if mv is None else f'{mv:+.0f}'} "
          f"| {f(r['m_kw'])} | {f(r['m_acm'])} | {f(r['m_sffed'])} "
          f"| {f(r['m_dkw'])} | {b26['cell'].get(day, '—')} |")
    w("")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {out}")
    print(f"GATE {'PASSES' if gate else 'FAILS'}: "
          f"{sum(r['pass'] for r in res.values())}/5; agree {p_agree}/{n_agree}, "
          f"disagree {p_dis}/{n_dis}")
    for e in EPISODES:
        r = res[e["id"]]
        print(f"  {e['id']:13} agree={r['agreement']['agree']!s:5} modal={r['modal']!s:14} "
              f"{'PASS' if r['pass'] else 'FAIL'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
