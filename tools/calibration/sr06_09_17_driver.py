"""
SR-6 / SR-9 / SR-17 -- the rates driver's calibration study (signal-triage ST-3).

    python tools/calibration/sr06_09_17_driver.py                # writes the ledger
    python tools/calibration/sr06_09_17_driver.py --out PATH     # somewhere else
    python tools/calibration/sr06_09_17_driver.py --refresh      # re-download

The offline rule (tools/calibration/README.md): full history pulled straight from
each publisher, the observation store never read, one dated ledger per run.

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
reader: the three model term premia are TODAY'S re-estimates of the past, not
what was knowable then (no vintages are published); DFII10 and T10YIE start in
January 2003, so 1994 has no real/breakeven cut and can reach a path-side cell
only never; DKW starts in 1999; TLT in July 2002, so correlation before it uses a
constant-maturity duration proxy on DGS10.
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
LEDGER = REPO / "docs" / "ledgers" / "rates-driver-2026-09.md"
CONFIG = REPO / "config" / "market_state.yaml"

# The features' own constants (altdata/market_features.py), restated because this
# script may not import that module's store-reading half. Checked against it at
# run time below, so a change there cannot pass silently here.
WINDOW = 60
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
# THE EPISODES. SR-6's two sets and SR-17's four. Windows run from the start of
# the yield move to its peak, the sessions the driver is asked to classify.
# "Q4 2018" is the order's label; the selloff leg it names ran from late August
# to the 8 Nov peak -- after it the 10-year fell for the rest of the quarter,
# which is a rally, not the bear flattening the set is about.
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
    s = pd.Series(df.iloc[:, 1].values, index=pd.to_datetime(df.iloc[:, 0]),
                  name=series_id, dtype=float).dropna()
    return s


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
def window_change(num: pd.Series, den: pd.Series, w: int, scale_num: float = 100.0,
                  scale_den: float = 100.0) -> tuple[pd.Series, pd.Series]:
    """(Δden in bp, Δnum/Δden) over `w` of the pair's common observations.

    Common days only, and the window counted in them: the features' rule that
    both series must be on both endpoints, with no carry-forward.
    """
    df = pd.concat([num.rename("n"), den.rename("d")], axis=1).dropna()
    dd = (df["d"] - df["d"].shift(w)) * scale_den
    dn = (df["n"] - df["n"].shift(w)) * scale_num
    share = (dn / dd).where(dd.abs() >= MIN_MOVE_BP)
    return dd, share


def build_inputs(d: dict) -> pd.DataFrame:
    """One row per 10-year session: every number driver_cell() is handed."""
    y10 = d["DGS10"]
    move = (y10 - y10.shift(WINDOW)) * 100.0
    _, real = window_change(d["DFII10"], y10, WINDOW)
    # the features require BOTH endpoints on the 10-year's own days
    real = real.reindex(move.index)
    _, curve = window_change(d["DGS2"], y10, WINDOW)
    curve = curve.reindex(move.index)
    _, kw_share = window_change(d["THREEFYTP10"], y10, WINDOW)
    a = d["acm"]
    _, acm_share = window_change(a["acm.term_premium_10y"],
                                 a["acm.fitted_yield_10y"], WINDOW)
    k = d["dkw"][["dkw.exp_real_short_rate_10y", "dkw.real_term_premium_10y",
                  "dkw.tips_liquidity_premium_10y"]].dropna()
    dk = k - k.shift(WINDOW)
    dsum = dk.sum(axis=1)
    ok = (dsum.abs() * 100.0) >= MIN_MOVE_BP
    dkw_path = (dk["dkw.exp_real_short_rate_10y"] / dsum).where(ok)
    dkw_prem = (dk["dkw.real_term_premium_10y"] / dsum).where(ok)
    # THE SENSITIVITY: path and premium as shares of THEIR OWN sum, the TIPS
    # liquidity premium left out. Not the object's definition (v1.11 divides by
    # the model's whole real move); reported because the liquidity leg is what
    # keeps the declared shares from reaching share_min -- see the ledger.
    d2 = dk["dkw.exp_real_short_rate_10y"] + dk["dkw.real_term_premium_10y"]
    ok2 = (d2.abs() * 100.0) >= MIN_MOVE_BP
    dkw_path_xl = (dk["dkw.exp_real_short_rate_10y"] / d2).where(ok2)
    dkw_prem_xl = (dk["dkw.real_term_premium_10y"] / d2).where(ok2)
    dkw_liq = (dk["dkw.tips_liquidity_premium_10y"] / dsum).where(ok)

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
    # THE PROXY, before TLT: S&P against a constant-maturity 10-year.
    g = px["GSPC"].dropna()
    y = y10.reindex(g.index).ffill()
    bond = (y.shift(1) / 100.0 / 252.0) - PROXY_DURATION * (y - y.shift(1)) / 100.0
    corr_proxy = np.log(g).diff().rolling(CORR_WINDOW).corr(bond)
    corr = corr_live.combine_first(corr_proxy[corr_proxy.index < both.index[0]])

    idx = move.index

    def at(s: pd.Series, lag: int = 0) -> pd.Series:
        """The latest value at or before each session, optionally `lag` back."""
        s = s.dropna()
        out = s.reindex(idx.union(s.index)).ffill().reindex(idx)
        return out.shift(lag) if lag else out

    frame = pd.DataFrame({
        "move": move, "real": real, "curve": curve,
        "dkw_path": at(dkw_path), "dkw_prem": at(dkw_prem),
        "dkw_path_xl": at(dkw_path_xl), "dkw_prem_xl": at(dkw_prem_xl),
        "dkw_liq": at(dkw_liq),
        "dkw_path_live": at(dkw_path, DKW_LIVE_LAG),
        "dkw_prem_live": at(dkw_prem, DKW_LIVE_LAG),
        "kw_share": at(kw_share), "acm_share": at(acm_share),
        "m_kw": at(models["kw"]), "m_acm": at(models["acm"]),
        "m_sffed": at(models["sffed"]), "m_dkw": at(models["dkw"]),
        "m_dkw_live": at(models["dkw"], DKW_LIVE_LAG),
        "corr": at(corr), "gspc": at(px["GSPC"]),
    }, index=idx)
    # A model whose history has not started is ABSENT, not carried back.
    for col, s in (("dkw_path", dkw_path), ("dkw_prem", dkw_prem),
                   ("dkw_path_xl", dkw_path_xl), ("dkw_prem_xl", dkw_prem_xl),
                   ("dkw_liq", dkw_liq),
                   ("kw_share", kw_share), ("acm_share", acm_share),
                   ("m_kw", models["kw"]), ("m_acm", models["acm"]),
                   ("m_sffed", models["sffed"]), ("m_dkw", models["dkw"])):
        first = s.dropna().index.min()
        if first is not None and first == first:
            frame.loc[frame.index < first, col] = np.nan
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
            "curve_share": lv(row["curve"], "curve"), "primary": primary,
            "tie_breakers": ties, "models": models,
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
                     "signs": c.get("model_signs") or {}})
    return pd.DataFrame(rows).set_index("day")


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
def score_episode(cells: pd.DataFrame, ep: dict) -> dict:
    w = cells.loc[ep["start"]:ep["end"]]
    counts = w["cell"].value_counts()
    det = w[w["cell"] != "not_determined"]
    modal = det["cell"].value_counts().idxmax() if len(det) else None
    share = (det["cell"] == ep["expect"]).mean() if len(det) else float("nan")
    return {"n": len(w), "determined": len(det), "counts": counts.to_dict(),
            "modal": modal, "expected_share": share,
            "pass": modal == ep["expect"]}


def pct(x: float) -> str:
    return "—" if x is None or x != x else f"{100 * x:.0f}%"


def spec_with(base: dict, **th) -> dict:
    s = {**base, "thresholds": {**base["thresholds"], **th}}
    return s


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

    # The features' constants, checked against the module that defines them.
    feat = (REPO / "altdata" / "market_features.py").read_text(encoding="utf-8")
    for name, val in (("MODEL_WINDOW", WINDOW), ("ATTR_MIN_MOVE_BP", MIN_MOVE_BP),
                      ("CORR_WINDOW", CORR_WINDOW)):
        if f"\n{name} = {val:g}" not in feat and f"\n{name} = {val}" not in feat:
            print(f"market_features.{name} is no longer {val}; update this script")
            return 3

    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    spec = cfg["dimensions"]["rates"]["driver"]
    print(f"config {cfg['version']}: thresholds {spec['thresholds']}")

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
    for k, (s, e, n) in spans.items():
        print(f"  {k:26} {s} .. {e}  n={n}")

    # 1990 on: the 1994 episode's window reaches back into 1993, and nothing the
    # study reports needs the 1960s -- only the 10-year and ACM go back that far.
    frame = build_inputs(d).loc["1990-01-01":]
    base = replay(frame, spec)
    live = replay(frame, spec, live=True)
    print(f"replayed {len(base)} sessions")

    ep_base = {e["id"]: score_episode(base, e) for e in EPISODES}
    ep_live = {e["id"]: score_episode(live, e) for e in EPISODES}

    # The ex-liquidity sensitivity, at each share_min of the grid.
    xl = frame.copy()
    xl["dkw_path"], xl["dkw_prem"] = frame["dkw_path_xl"], frame["dkw_prem_xl"]
    xl_runs = {sm: {e["id"]: score_episode(
        replay(xl, spec_with(spec, share_min=sm)), e) for e in EPISODES}
        for sm in GRID["share_min"]}

    # Why: each episode's inputs at their medians, and its undecided reasons.
    diag = {}
    for e in EPISODES:
        seg = frame.loc[e["start"]:e["end"]]
        reasons: dict[str, int] = {}
        for _, row in seg.iterrows():
            if _v(row["move"]) is None:
                continue
            r = driver_cell(inputs_for(row), spec)
            why = (r.get("undecided_reason") or r.get("not_determined_reason")
                   or r["raw_state"])
            why = why.split(" -- ")[0].split(" (")[0]
            if "move floor" in why:
                why = f"below the {spec['thresholds']['move_floor_bp']}bp move floor"
            reasons[why] = reasons.get(why, 0) + 1
        diag[e["id"]] = {"med": seg[["move", "real", "curve", "dkw_path",
                                     "dkw_prem", "dkw_liq", "dkw_path_xl",
                                     "kw_share", "acm_share"]].median(),
                         "reasons": sorted(reasons.items(), key=lambda kv: -kv[1])}

    # THE GRID. Every point replays the whole history; the question is how many
    # of the 27 neighbours of the declared thresholds keep each episode's verdict.
    grid_pass = {e["id"]: 0 for e in EPISODES}
    grid_all = []
    n_grid = 0
    for sm in GRID["share_min"]:
        for mf_ in GRID["move_floor_bp"]:
            for fa in GRID["front_anchored"]:
                n_grid += 1
                cells = replay(frame, spec_with(spec, share_min=sm,
                                                move_floor_bp=mf_,
                                                front_anchored=fa))
                res = {e["id"]: score_episode(cells, e) for e in EPISODES}
                for k, r in res.items():
                    grid_pass[k] += bool(r["pass"])
                grid_all.append(((sm, mf_, fa), sum(bool(r["pass"])
                                                    for r in res.values()), res))
    print("episodes (base):", {k: (v["modal"], v["pass"]) for k, v in ep_base.items()})

    # --- the full sample -------------------------------------------------------
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
    by_whom = decided["decided_by"].fillna("—").value_counts()

    # --- the four models, Feb-Sep 2026 -----------------------------------------
    sbs = frame.loc[SIDE_BY_SIDE[0]:SIDE_BY_SIDE[1],
                    ["move", "m_kw", "m_acm", "m_sffed", "m_dkw"]]
    month_end = sbs.groupby(sbs.index.to_period("M")).tail(1)
    b26 = base.loc[SIDE_BY_SIDE[0]:SIDE_BY_SIDE[1]]

    def sgn(x):
        x = _v(x)
        return "—" if x is None else ("0" if abs(x) < spec["thresholds"]
                                      ["sign_deadband_bp"] else ("+" if x > 0 else "−"))

    agree = []
    for _, r in sbs.iterrows():
        ss = {sgn(r[c]) for c in ("m_kw", "m_acm", "m_sffed", "m_dkw")} - {"—", "0"}
        if ss:
            agree.append(len(ss) == 1)

    # --- write the ledger --------------------------------------------------------
    today = dt.date.today().isoformat()
    L: list[str] = []
    w = L.append
    w("# Rates driver — calibration ledger (SR-6, SR-9, SR-17)")
    w("")
    w(f"*Run {today} by `tools/calibration/sr06_09_17_driver.py` against config "
      f"`{cfg['version']}`. Dated; never edited — a rerun writes a new ledger.*")
    w("")
    w("The rule calibrated is the market-state object's own: `regime.driver_cell` is "
      "imported and called on every session. Its inputs are rebuilt from the "
      "publishers' full histories on the definitions of the `calc.attr_*` series in "
      "`altdata/market_features.py` (a window of 60 of the denominator's own "
      "observations, same-day endpoints, no share below a 5 bp denominator). The "
      "observation store is not read.")
    w("")
    w("## Data source and vintage")
    w("")
    w("| Series | Source | From | To | n |")
    w("|---|---|---|---|---|")
    src = {"DGS10": "FRED", "DGS2": "FRED", "DFII10": "FRED",
           "THREEFYTP10 (Kim-Wright)": "FRED (Board, re-estimated)",
           "DKW": "Federal Reserve Board CSV (re-estimated monthly)",
           "ACM": "NY Fed workbook, daily sheet (re-estimated)",
           "SF Fed": "FRBSF workbook, fitted term premium (weekly)",
           "SPY": "yfinance, adjusted", "TLT": "yfinance, adjusted",
           "^GSPC": "yfinance"}
    for k, (s, e, n) in spans.items():
        w(f"| {k} | {src[k]} | {s} | {e} | {n:,} |")
    w("")
    w(f"Vintage: downloaded {today}. **The three model term premia (Kim-Wright, ACM, "
      "DKW) and SF Fed are today's re-estimates of the past, not what was "
      "knowable at the time** — no publisher keeps vintages of them. The ledger "
      "therefore measures whether the rule classifies the episodes as the models "
      "now describe them, which is a weaker claim than live performance. DKW's "
      "publication lag is modelled as a variant (read 21 sessions late); ACM's is "
      "not.")
    w("")
    w("Before TLT (July 2002) the stock-bond correlation uses ^GSPC against a "
      f"constant-maturity 10-year from DGS10 (carry less {PROXY_DURATION} x the "
      "yield change). DFII10 starts January 2003, so **1994 has no real/breakeven "
      "cut**: a path-side cell cannot be tested there, and the episode can only "
      "come out `term_premium`, `mixed` or not determined.")
    w("")
    w("## Thresholds under test")
    w("")
    w("| Threshold | Declared (v1.11) | Grid |")
    w("|---|---|---|")
    for k, v in spec["thresholds"].items():
        w(f"| `{k}` | {v} | {', '.join(str(x) for x in GRID.get(k, ())) or '—'} |")
    w("")
    w("## SR-6's episode sets and SR-17's four episodes")
    w("")
    w("Gate (signal-triage order §9, ST-3): *the ledger reproduces SR-6's episode "
      "sets and SR-17's four episodes*. Scored here as: **the modal cell among the "
      "episode's determined sessions is the set's expected cell** — `fed_path` for "
      "bear flattening, `term_premium` for bear steepening.")
    w("")
    w("| Episode | Set | Window | Sessions | Determined | Cells (base) | Modal | Expected share | Base | Live DKW lag | Grid (of "
      f"{n_grid}) |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    for e in EPISODES:
        b, lv_ = ep_base[e["id"]], ep_live[e["id"]]
        cells = ", ".join(f"{k} {v}" for k, v in sorted(b["counts"].items(),
                                                          key=lambda kv: -kv[1]))
        w(f"| {e['id']} | {e['set'].replace('_', ' ')} | {e['start']} → {e['end']} "
          f"| {b['n']} | {b['determined']} | {cells} | {b['modal'] or '—'} "
          f"| {pct(b['expected_share'])} | {'PASS' if b['pass'] else 'FAIL'} "
          f"| {'PASS' if lv_['pass'] else 'FAIL'} ({lv_['modal'] or '—'}) "
          f"| {grid_pass[e['id']]} |")
    w("")
    for e in EPISODES:
        w(f"- **{e['id']}** — {e['what']}.")
    w("")
    n_pass = sum(bool(v["pass"]) for v in ep_base.values())
    best = max(grid_all, key=lambda g: g[1])
    w(f"**Base thresholds: {n_pass} of {len(EPISODES)} episodes pass.** Best grid "
      f"point: share_min {best[0][0]}, move_floor_bp {best[0][1]}, "
      f"front_anchored {best[0][2]} — {best[1]} of {len(EPISODES)}. Grid points "
      f"passing all five: {sum(1 for g in grid_all if g[1] == len(EPISODES))} of "
      f"{n_grid}.")
    w("")
    w("## Why the episodes fail")
    w("")
    w("Each episode's inputs at their in-window medians. `dkw path` / `dkw prem` / "
      "`dkw liq` are the v1.11 shares of the model's whole real move; `dkw path xl` "
      "is path / (path + premium), the TIPS liquidity premium left out.")
    w("")
    w("| Episode | Δ10y bp | real share | curve share | dkw path | dkw prem | dkw liq | dkw path xl | KW prem | ACM prem |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for e in EPISODES:
        m = diag[e["id"]]["med"]

        def g(x, f="{:.2f}"):
            x = _v(x)
            return "—" if x is None else f.format(x)
        w(f"| {e['id']} | {g(m['move'], '{:+.0f}')} | {g(m['real'])} "
          f"| {g(m['curve'])} | {g(m['dkw_path'])} | {g(m['dkw_prem'])} "
          f"| {g(m['dkw_liq'])} | {g(m['dkw_path_xl'])} | {g(m['kw_share'])} "
          f"| {g(m['acm_share'])} |")
    w("")
    w("What decided each session at the declared thresholds:")
    w("")
    for e in EPISODES:
        w(f"- **{e['id']}**: " + "; ".join(f"{k} ({v})"
                                            for k, v in diag[e['id']]['reasons']))
    w("")
    w("### Sensitivity: DKW shares without the liquidity premium")
    w("")
    w("The same rule with DKW's path and premium measured as shares of their own "
      "sum. **Not the object's definition** — reported because it isolates the "
      "one definitional choice the diagnosis points at.")
    w("")
    w("| share_min | " + " | ".join(e["id"] for e in EPISODES) + " | Passing |")
    w("|---|" + "---|" * (len(EPISODES) + 1))
    for sm, res in xl_runs.items():
        w(f"| {sm} | " + " | ".join(
            f"{res[e['id']]['modal'] or '—'} ({pct(res[e['id']]['expected_share'])})"
            for e in EPISODES)
          + f" | {sum(bool(r['pass']) for r in res.values())} of {len(EPISODES)} |")
    w("")
    w("## SR-17: forward equity outcomes by cell inside its four episodes")
    w("")
    w("Base rate only (SR-17 carries no rights). ^GSPC forward return from each "
      "session in the cell; overlapping windows, so the sessions are not "
      "independent draws.")
    w("")
    w("| Episode | Cell | Sessions | Fwd 3m mean | Fwd 6m mean | Fwd 6m > 0 |")
    w("|---|---|---|---|---|---|")
    for e in [x for x in EPISODES if x["sr17"]]:
        seg = base.loc[e["start"]:e["end"]].join(frame[["fwd_3m", "fwd_6m"]])
        for c, g in seg.groupby("cell"):
            w(f"| {e['id']} | {c} | {len(g)} | {pct(g['fwd_3m'].mean())} "
              f"| {pct(g['fwd_6m'].mean())} "
              f"| {pct((g['fwd_6m'].dropna() > 0).mean())} |")
    w("")
    w(f"## The full sample, {FULL_SAMPLE_FROM} to the last session")
    w("")
    w("SR-9's correlation member by cell, and the forward S&P base rate by cell.")
    w("")
    w("| Cell | Sessions | Share | Corr mean | Corr > 0 | Fwd 3m mean | Fwd 6m mean | Fwd 6m median | Fwd 6m > 0 |")
    w("|---|---|---|---|---|---|---|---|---|")
    tot = by_cell["sessions"].sum()
    for c, r in by_cell.sort_values("sessions", ascending=False).iterrows():
        w(f"| {c} | {int(r['sessions']):,} | {pct(r['sessions'] / tot)} "
          f"| {r['corr_mean']:+.2f} | {pct(r['corr_pos'])} | {pct(r['fwd3_mean'])} "
          f"| {pct(r['fwd6_mean'])} | {pct(r['fwd6_med'])} | {pct(r['fwd6_pos'])} |")
    w("")
    w("By direction:")
    w("")
    cols = list(by_cell_dir.columns)
    w("| Cell | " + " | ".join(str(c) for c in cols) + " |")
    w("|---|" + "---|" * len(cols))
    for c, r in by_cell_dir.iterrows():
        w(f"| {c} | " + " | ".join(f"{int(r[x]):,}" for x in cols) + " |")
    w("")
    w(f"Among determined sessions, the side was decided by: "
      + ", ".join(f"{k} {v:,}" for k, v in by_whom.items())
      + f". The models disagreed on sign and DKW arbitrated on {pct(arb_rate)} of "
        "them.")
    w("")
    w(f"## SR-6: the four models side by side, {SIDE_BY_SIDE[0]} to "
      f"{SIDE_BY_SIDE[1]}")
    w("")
    w("60-observation term-premium change in bp (SF Fed: 12 weekly prints), at each "
      "month's last session in the history; the sign outside the 5 bp dead-band. "
      "DKW's last row is 31 Aug, so its September reading is August's carried "
      "forward -- which is what the live object would see.")
    w("")
    w("| Month end | Δ10y | Kim-Wright | ACM | SF Fed | DKW (real) | Cell |")
    w("|---|---|---|---|---|---|---|")
    for day, r in month_end.iterrows():
        cell = b26["cell"].get(day, "—")

        def f(x):
            x = _v(x)
            return "—" if x is None else f"{x:+.0f} ({sgn(x)})"
        mv = _v(r["move"])
        w(f"| {day.date()} | {'—' if mv is None else f'{mv:+.0f}'} "
          f"| {f(r['m_kw'])} | {f(r['m_acm'])} "
          f"| {f(r['m_sffed'])} | {f(r['m_dkw'])} | {cell} |")
    w("")
    w(f"Sessions where at least one model has a sign: {len(agree)}; all signed "
      f"models agree on {pct(sum(agree) / len(agree) if agree else float('nan'))} of "
      "them. Where they disagree, the object lets DKW arbitrate (§2.1.1, SR-17); "
      "SR-6's own text named the curve decomposition as the arbiter, and the "
      "integration ruling replaced it with DKW.")
    w("")
    w("## Verdict")
    w("")
    L.append("VERDICT_PLACEHOLDER")
    text = "\n".join(L) + "\n"

    verdict = [f"- Base thresholds (v1.11): **{n_pass} of {len(EPISODES)}** "
               "episodes reproduce their set's cell."]
    for e in EPISODES:
        b = ep_base[e["id"]]
        verdict.append(
            f"- {e['id']}: {'PASS' if b['pass'] else 'FAIL'} — modal "
            f"{b['modal'] or 'none'} ({pct(b['expected_share'])} of determined "
            f"sessions {e['expect']}); holds at {grid_pass[e['id']]} of {n_grid} "
            "grid points.")
    text = text.replace("VERDICT_PLACEHOLDER", "\n".join(verdict))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {out}")
    for v in verdict:
        print(v)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
