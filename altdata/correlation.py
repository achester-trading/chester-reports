"""
The correlation layer (AQ-5): rolling return correlations across the alternative-
asset universe, the former report's break, a shift flag per pair, the named rows,
and the peer-pair divergences -- stored as calculated series, read by the Weekly
(one line, only in a week something fired) and the Monthly (a Correlations block
in the slow layers).

    python -m altdata.correlation compute                # the last few sessions
    python -m altdata.correlation compute --backfill     # every session (box, once)
    python -m altdata.correlation show [--as-of ...]
    python -m altdata.correlation peers [--as-of ...]

Everything it computes is declared in config/correlation.yaml and registered in
metrics_registry.yaml: rights ceiling NARROW FLAG, trigger_eligible false on every
entry, and nothing here enters a composite.

-----------------------------------------------------------------------------
WHY THIS IS NOT IN derived.py
-----------------------------------------------------------------------------

The change order puts the matrix "in altdata/derived.py". It lives beside it, for
the reason derived.py's own boundary gives: derived.py computes the standard FORMS
of a metric (its deltas, its percentile, its z) and is the only place those are
computed; a module that makes a NEW METRIC from other metrics' histories is
market_features' kind of module. A 60-day correlation has its own history and its
own distribution, so it is a series; its percentile is still derived.py's
(percentile_of, long_run_average, series_as_of), and nothing here re-implements one.

-----------------------------------------------------------------------------
THE ARITHMETIC
-----------------------------------------------------------------------------

A pair is read on its COMMON days -- the days both series printed -- and a return
spans two consecutive common days, so Bitcoin's Monday return against SPY's is
Friday to Monday for both. Prices are log returns; a yield (the 10-year) is its
change in its own units; USD/JPY and USD/CNY are inverted so the yen and the yuan
read as their own prices. A window is N common returns, never fewer: a window
that is not full writes nothing, so every flag is off where the history is
shorter than its window.

-----------------------------------------------------------------------------
POINT IN TIME
-----------------------------------------------------------------------------

Every input is read through ObservationStore.as_of(), so nothing later than the
cutoff is seen; every row's available_at is the MAXIMUM across every input row
its window touched (market_features' rule: a feature is never knowable before
the data it is made of), and its availability_kind the weakest of theirs.
tools/validate_correlation_layer.py recomputes each stored value from only the
rows knowable at its own available_at and requires the same number.
"""

from __future__ import annotations

import datetime as dt
import logging
import math
from pathlib import Path
from typing import Any, Optional

import numpy as np

from . import derived, observations, session

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "correlation.yaml"

_CFG: Optional[dict] = None


def config() -> dict:
    global _CFG
    if _CFG is None:
        import yaml  # noqa: PLC0415
        _CFG = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    return _CFG


# ---------------------------------------------------------------------------
# The universe and the keys
# ---------------------------------------------------------------------------
def assets(cfg: Optional[dict] = None) -> list[dict]:
    """The universe members with a price series in the store, in config order."""
    return [a for a in (cfg or config()).get("universe") or [] if a.get("key")]


def absent_assets(cfg: Optional[dict] = None) -> list[dict]:
    return [a for a in (cfg or config()).get("universe") or [] if not a.get("key")]


def inputs(cfg: Optional[dict] = None) -> dict[str, dict]:
    """Every readable input by id: the universe's present members and the extras."""
    c = cfg or config()
    return {a["id"]: a for a in assets(c) + list(c.get("extra_inputs") or [])}


def pairs(cfg: Optional[dict] = None) -> list[tuple[str, str]]:
    ids = [a["id"] for a in assets(cfg)]
    return [(ids[i], ids[j]) for i in range(len(ids)) for j in range(i + 1, len(ids))]


def pair_key(a: str, b: str, window: int) -> str:
    return f"corr.{a}__{b}.{window}d"


def shift_key(a: str, b: str) -> str:
    return f"corr.{a}__{b}.shift"


def break_key(asset: str, bench: str) -> str:
    return f"corr.{asset}__{bench}.break"


def stored_key(key: str, cfg: Optional[dict] = None) -> str:
    """The key a matrix cell is READ under: its alias where it has one."""
    al = (cfg or config()).get("aliases") or {}
    return al.get(key.removeprefix("corr."), key)


def _windows(cfg: dict) -> dict:
    return cfg.get("windows") or {}


def break_assets(cfg: Optional[dict] = None) -> list[str]:
    c = cfg or config()
    benches = set((c.get("break") or {}).get("benchmarks") or [])
    return [a["id"] for a in assets(c) if a.get("former") and a["id"] not in benches]


def _series_registry(cfg: dict) -> tuple[dict, dict, dict]:
    """(pair series, shift flags, breaks): key -> description, for the registry."""
    labels = {a["id"]: a["label"] for a in assets(cfg)}
    al = cfg.get("aliases") or {}
    ps, sh, br = {}, {}, {}
    for a, b in pairs(cfg):
        for w in _windows(cfg).get("matrix") or []:
            k = pair_key(a, b, w)
            if k.removeprefix("corr.") in al:
                continue
            ps[k] = f"{labels[a]} against {labels[b]}, {w} common sessions"
        sh[shift_key(a, b)] = f"shift flag, {labels[a]} against {labels[b]}"
    for a in break_assets(cfg):
        for bench in (cfg.get("break") or {}).get("benchmarks") or []:
            br[break_key(a, bench)] = (f"{labels[a]}: 30-day minus 120-day "
                                       f"correlation to {bench.upper()}")
    return ps, sh, br


# The registry's bulk blocks read these (members_are: keys). Built from the config
# at import, so a member added to the universe is a registry member at once, and
# check_registry.py's expected_members makes the count change deliberate.
try:
    PAIR_SERIES, SHIFT_SERIES, BREAK_SERIES = _series_registry(config())
except Exception:                                                 # noqa: BLE001
    PAIR_SERIES, SHIFT_SERIES, BREAK_SERIES = {}, {}, {}


# ---------------------------------------------------------------------------
# Reading the inputs, availabilities included
# ---------------------------------------------------------------------------
Series = dict[str, tuple[float, str, Optional[str]]]   # day -> (value, avail, kind)


def _load(db: observations.ObservationStore, key: str,
          as_of: Optional[str]) -> Series:
    out: Series = {}
    for r in db.as_of(key, as_of=as_of):
        v = r.get("value_num")
        if v is None or not math.isfinite(float(v)):
            continue
        out[str(r["observed_at"])[:10]] = (float(v), str(r["available_at"]),
                                           r.get("availability_kind"))
    return out


def _ratio(num: Series, den: Series) -> Series:
    out: Series = {}
    for d in sorted(set(num) & set(den)):
        if den[d][0] > 0 and num[d][0] > 0:
            out[d] = (num[d][0] / den[d][0], max(num[d][1], den[d][1]),
                      _weakest([num[d][2], den[d][2]]))
    return out


def _weakest(kinds) -> Optional[str]:
    ks = set(kinds)
    for weak in ("reconstructed", "ingest_instant", "observed"):
        if weak in ks:
            return weak
    return None


class Inputs:
    """Each input series loaded once per run, as known at the cutoff."""

    def __init__(self, db, as_of: Optional[str], cfg: dict) -> None:
        self.db, self.as_of, self.cfg = db, as_of, cfg
        self.spec = inputs(cfg)
        self._cache: dict[str, Series] = {}

    def series(self, ref) -> tuple[Series, str, bool]:
        """(series, transform, invert) for an input id, or a [num, den] ratio."""
        if isinstance(ref, (list, tuple)):
            num, den = (self.series(r)[0] for r in ref)
            return _ratio(num, den), "log_return", False
        if ref not in self._cache:
            self._cache[ref] = _load(self.db, self.spec[ref]["key"], self.as_of)
        s = self.spec[ref]
        return self._cache[ref], s.get("transform") or "log_return", bool(s.get("invert"))


# ---------------------------------------------------------------------------
# Returns and rolling correlation
# ---------------------------------------------------------------------------
class Returns:
    """A pair's common-day returns: end days, the two return arrays, and each
    return's availability (the latest of the four input rows it spans)."""

    def __init__(self, days: list[str], x: np.ndarray, y: np.ndarray,
                 avail: list[str], kinds: list[Optional[str]]) -> None:
        self.days, self.x, self.y, self.avail, self.kinds = days, x, y, avail, kinds


def _ret(a: float, b: float, transform: str, invert: bool) -> Optional[float]:
    if transform == "diff":
        r = b - a
    else:
        if a <= 0 or b <= 0:
            return None
        r = math.log(b / a)
    return -r if invert else r


def returns(sa: Series, sb: Series, ta: str = "log_return", tb: str = "log_return",
            ia: bool = False, ib: bool = False) -> Returns:
    common = sorted(set(sa) & set(sb))
    days, xs, ys, av, kd = [], [], [], [], []
    for p, d in zip(common, common[1:]):
        rx = _ret(sa[p][0], sa[d][0], ta, ia)
        ry = _ret(sb[p][0], sb[d][0], tb, ib)
        if rx is None or ry is None:
            continue
        days.append(d)
        xs.append(rx)
        ys.append(ry)
        av.append(max(sa[p][1], sa[d][1], sb[p][1], sb[d][1]))
        kd.append(_weakest([sa[p][2], sa[d][2], sb[p][2], sb[d][2]]))
    return Returns(days, np.array(xs, dtype=float), np.array(ys, dtype=float), av, kd)


def rolling_corr(x: np.ndarray, y: np.ndarray, w: int) -> np.ndarray:
    """Pearson correlation over each run of w consecutive returns: element i is
    the window ENDING at return i + w - 1. NaN where a leg is flat. Computed on
    each window directly (no running sums), in chunks so a long history does
    not hold an n-by-w matrix at once."""
    n = len(x)
    if n < w or w < 2:
        return np.array([], dtype=float)
    from numpy.lib.stride_tricks import sliding_window_view  # noqa: PLC0415
    X, Y = sliding_window_view(x, w), sliding_window_view(y, w)
    out = np.empty(X.shape[0], dtype=float)
    step = 2048
    for s in range(0, X.shape[0], step):
        xa, ya = X[s:s + step], Y[s:s + step]
        xm = xa - xa.mean(axis=1, keepdims=True)
        ym = ya - ya.mean(axis=1, keepdims=True)
        vx, vy = (xm * xm).sum(axis=1), (ym * ym).sum(axis=1)
        cov = (xm * ym).sum(axis=1)
        with np.errstate(invalid="ignore", divide="ignore"):
            c = cov / np.sqrt(vx * vy)
        flat = (vx <= 1e-18) | (vy <= 1e-18)
        c[flat] = np.nan
        out[s:s + step] = np.clip(c, -1.0, 1.0)
    return out


def _window_max(vals: list[str], w: int) -> list[str]:
    """The latest instant in each run of w consecutive entries (aligned with
    rolling_corr's output)."""
    if len(vals) < w:
        return []
    rank = {v: i for i, v in enumerate(sorted(set(vals)))}
    inv = sorted(rank, key=rank.get)
    from numpy.lib.stride_tricks import sliding_window_view  # noqa: PLC0415
    r = sliding_window_view(np.array([rank[v] for v in vals]), w).max(axis=1)
    return [inv[i] for i in r]


def _window_kind(kinds: list[Optional[str]], w: int) -> list[Optional[str]]:
    if len(kinds) < w:
        return []
    out = []
    for i in range(w - 1, len(kinds)):
        out.append(_weakest(kinds[i + 1 - w:i + 1]))
    return out


def corr_series(r: Returns, w: int) -> dict[str, tuple[float, str, Optional[str]]]:
    """day -> (correlation, available_at, kind) for every full w-return window."""
    c = rolling_corr(r.x, r.y, w)
    if not len(c):
        return {}
    av = _window_max(r.avail, w)
    kd = _window_kind(r.kinds, w)
    out = {}
    for i, v in enumerate(c):
        if math.isfinite(v):
            out[r.days[i + w - 1]] = (float(v), av[i], kd[i])
    return out


# ---------------------------------------------------------------------------
# The shift flag and the break
# ---------------------------------------------------------------------------
def _sign(v: float) -> int:
    return 1 if v > 0 else (-1 if v < 0 else 0)


def shift_eval(c60: dict, c252: dict, cfg: Optional[dict] = None,
               only_days: Optional[set] = None) -> dict[str, dict]:
    """day -> {flag, rule, gap, iqr, score, available_at, kind} on each day both
    windows are full.

    THE TWO ARMS (section 9). CROSSING: |60d - 252d| exceeds the 60-day's own
    five-year interquartile range, and the 60-day sat on the OTHER side of the
    252-day at least once in the last `cross_lookback` sessions -- it crossed, and
    has gone past by more than its IQR. Off while fewer than `iqr_min` 60-day
    values exist to take an IQR over. SIGN: the 60-day has held one sign for
    `sign_hold` sessions after a session of the other sign -- true on the session
    the hold completes. `score` is |gap| / IQR, the Monthly's ranking.

    The row's availability is the latest across every 60-day and 252-day value the
    evaluation read (the IQR window covers the lookback and the hold)."""
    sc = (cfg or config()).get("shift") or {}
    iqr_n = int(sc.get("iqr_years", 5)) * 252
    iqr_min = int(sc.get("iqr_min", 252))
    look = int(sc.get("cross_lookback", 60))
    hold = int(sc.get("sign_hold", 20))
    days = sorted(c60)
    idx = {d: i for i, d in enumerate(days)}
    vals = np.array([c60[d][0] for d in days], dtype=float)
    out: dict[str, dict] = {}
    gaps: dict[str, float] = {d: c60[d][0] - c252[d][0] for d in days if d in c252}
    for d in days:
        if d not in c252 or (only_days is not None and d not in only_days):
            continue
        i = idx[d]
        lo = max(0, i + 1 - iqr_n)
        hist = vals[lo:i + 1]
        gap = gaps[d]
        iqr = (float(np.percentile(hist, 75) - np.percentile(hist, 25))
               if len(hist) >= iqr_min else None)
        crossed = False
        if iqr is not None and abs(gap) > iqr and _sign(gap) != 0:
            for p in days[max(0, i - look):i]:
                g = gaps.get(p)
                if g is not None and _sign(g) == -_sign(gap):
                    crossed = True
                    break
        flipped = False
        if i >= hold:
            run = vals[i + 1 - hold:i + 1]
            s = _sign(float(run[0]))
            if s != 0 and all(_sign(float(v)) == s for v in run) \
                    and _sign(float(vals[i - hold])) == -s:
                flipped = True
        used = [c60[p] for p in days[min(lo, max(0, i - hold)):i + 1]] \
            + [c252[p] for p in days[max(0, i - look):i + 1] if p in c252]
        rule = ("crossing and sign" if crossed and flipped else
                "crossing" if crossed else "sign held" if flipped else None)
        out[d] = {"flag": bool(crossed or flipped), "rule": rule,
                  "gap": gap, "iqr": iqr,
                  "score": (abs(gap) / iqr) if iqr else None,
                  "c60": c60[d][0], "c252": c252[d][0],
                  "available_at": max(u[1] for u in used),
                  "kind": _weakest([u[2] for u in used])}
    return out


def is_break(delta: Optional[float], cfg: Optional[dict] = None) -> bool:
    """signals.py's CorrelationBreak.is_break: |delta| >= CORR_BREAK_DELTA."""
    thr = float(((cfg or config()).get("break") or {}).get("delta", 0.30))
    return delta is not None and abs(delta) >= thr


def direction(delta: float) -> str:
    """signals.py's direction: 'toward' when the change is positive, else 'away'."""
    return "toward" if delta > 0 else "away"


# ---------------------------------------------------------------------------
# Compute
# ---------------------------------------------------------------------------
def compute_rows(db: observations.ObservationStore, as_of: Optional[str] = None,
                 first_day: Optional[str] = None,
                 cfg: Optional[dict] = None) -> list[dict]:
    """Every correlation-layer row for days >= first_day (None: every day)."""
    c = cfg or config()
    inp = Inputs(db, as_of, c)
    win = _windows(c)
    al = c.get("aliases") or {}
    rows: list[dict] = []

    def emit(key: str, day: str, value: float, avail: str,
             kind: Optional[str]) -> None:
        if first_day and day < first_day:
            return
        if value is None or not math.isfinite(value):
            return
        rows.append({"registry_key": key, "instrument": None, "observed_at": day,
                     "available_at": avail, "value": round(float(value), 6),
                     "source": "calc", "availability_kind": kind})

    def pair_returns(a, b) -> Returns:
        sa, ta, ia = inp.series(a)
        sb, tb, ib = inp.series(b)
        return returns(sa, sb, ta, tb, ia, ib)

    # --- the matrix, the shift flags, and the average pairwise ---------------
    c60_all: dict[tuple, dict] = {}
    for a, b in pairs(c):
        r = pair_returns(a, b)
        by_w = {w: corr_series(r, w) for w in win.get("matrix") or []}
        for w, s in by_w.items():
            k = pair_key(a, b, w)
            if k.removeprefix("corr.") in al:
                continue
            for d, (v, av, kd) in s.items():
                emit(k, d, v, av, kd)
        c60, c252 = by_w.get(60) or {}, by_w.get(252) or {}
        c60_all[(a, b)] = c60
        only = None if not first_day else {d for d in c60 if d >= first_day}
        for d, e in shift_eval(c60, c252, c, only).items():
            emit(shift_key(a, b), d, 1.0 if e["flag"] else 0.0,
                 e["available_at"], e["kind"])

    ap = c.get("average_pairwise") or {}
    if ap.get("key") and c60_all:
        for d, (v, av, kd) in average_pairwise(c60_all, int(ap.get("carry_sessions", 5)),
                                               first_day).items():
            emit(ap["key"], d, v, av, kd)

    # --- the former report's break --------------------------------------------
    bw, lw = int(win.get("break_short", 30)), int(win.get("break_long", 120))
    for a in break_assets(c):
        for bench in (c.get("break") or {}).get("benchmarks") or []:
            r = pair_returns(a, bench)
            s, l = corr_series(r, bw), corr_series(r, lw)
            for d in l:
                if d in s:
                    emit(break_key(a, bench), d, s[d][0] - l[d][0],
                         max(s[d][1], l[d][1]), _weakest([s[d][2], l[d][2]]))

    # --- the named rows -------------------------------------------------------
    for n in c.get("named") or []:
        r = pair_returns(n["a"], n["b"])
        for d, (v, av, kd) in corr_series(r, int(n["window"])).items():
            emit(n["key"], d, v, av, kd)
    for q in c.get("ratios") or []:
        for d, (v, av, kd) in _ratio(inp.series(q["num"])[0],
                                     inp.series(q["den"])[0]).items():
            emit(q["key"], d, v, av, kd)
    return rows


def average_pairwise(c60_all: dict, carry: int = 5,
                     first_day: Optional[str] = None) -> dict[str, tuple]:
    """day -> (mean |60-day correlation| across every pair, available_at, kind).

    THE MEAN OF ABSOLUTE VALUES, because the liquidation signature is everything
    moving together (II S2, M1: "correlation spikes without news"), and the VIX,
    the dollar and TLT move together with the rest by moving AGAINST it: a signed
    mean would let those pairs cancel the spike it is meant to show.

    Every pair whose history has begun must contribute -- a pair's latest value
    carries at most `carry` days of the union calendar to a day it did not print
    (VIXCLS lands the next morning); a day missing one is not written, because a
    partial sample's mean moves with its membership."""
    union = sorted({d for s in c60_all.values() for d in s})
    pos = {d: i for i, d in enumerate(union)}
    keyed = {p: sorted(s) for p, s in c60_all.items() if s}
    out: dict[str, tuple] = {}
    import bisect  # noqa: PLC0415
    for d in union:
        if first_day and d < first_day:
            continue
        vals, used = [], []
        complete = True
        for p, ds in keyed.items():
            if ds[0] > d:
                continue                    # this pair's history has not begun
            j = bisect.bisect_right(ds, d) - 1
            last = ds[j]
            if pos[d] - pos[last] > carry:
                complete = False
                break
            vals.append(abs(c60_all[p][last][0]))
            used.append(c60_all[p][last])
        if not complete or len(vals) < 2:
            continue
        out[d] = (sum(vals) / len(vals), max(u[1] for u in used),
                  _weakest([u[2] for u in used]))
    return out


def default_first_day(as_of: Optional[str], cfg: Optional[dict] = None) -> str:
    days = int((cfg or config()).get("recompute_days", 14))
    end = dt.date.fromisoformat((as_of or session.utc_iso())[:10])
    return (end - dt.timedelta(days=days)).isoformat()


def compute(as_of: Optional[str] = None, first_day: Optional[str] = None,
            store: Optional[observations.ObservationStore] = None,
            dry_run: bool = False, backfill: bool = False) -> dict:
    """Compute and write. The daily pass writes from `recompute_days` back;
    `backfill` writes every session the inputs support. Only a CHANGED value is
    written (observations.drop_unchanged): a re-run is a no-op."""
    own = store is None
    db = store or observations.ObservationStore()
    try:
        fd = None if backfill else (first_day or default_first_day(as_of))
        rows = compute_rows(db, as_of=as_of, first_day=fd)
        fresh = observations.drop_unchanged(db, rows) if rows else []
        written = 0 if dry_run else db.write_many(fresh)
        by_key: dict[str, int] = {}
        for r in rows:
            fam = r["registry_key"].rsplit(".", 1)[-1]
            by_key[fam] = by_key.get(fam, 0) + 1
        return {"computed": len(rows), "changed": len(fresh), "written": written,
                "first_day": fd, "by_kind": by_key, "dry_run": dry_run}
    finally:
        if own:
            db.close()


# ---------------------------------------------------------------------------
# Reading (the Weekly, the Monthly, the CLI)
# ---------------------------------------------------------------------------
def _stored(st, key: str, now: str) -> list[tuple[str, float, str]]:
    return sorted((str(r["observed_at"])[:10], float(r["value_num"]),
                   str(r["available_at"]))
                  for r in st.as_of(stored_key(key), now)
                  if r.get("value_num") is not None)


def breaks_between(st, start: str, now: str, cfg: Optional[dict] = None) -> list[dict]:
    """Every break that fired on a session in (start, now], the latest per
    asset and benchmark: {asset, benchmark, delta, direction, day}."""
    c = cfg or config()
    out = []
    for a in break_assets(c):
        for bench in (c.get("break") or {}).get("benchmarks") or []:
            hits = [(d, v) for d, v, _ in _stored(st, break_key(a, bench), now)
                    if d > start[:10] and is_break(v, c)]
            if hits:
                d, v = hits[-1]
                out.append({"asset": a, "benchmark": bench, "delta": v,
                            "direction": direction(v), "day": d})
    return out


def credit_escalation(breaks: list[dict], cfg: Optional[dict] = None) -> list[str]:
    """signals.py's escalation condition: a credit-sensitive asset breaking AWAY
    from SPY. A flag, printed; it escalates no trigger here."""
    cs = set(((cfg or config()).get("break") or {}).get("credit_sensitive") or [])
    return sorted({b["asset"] for b in breaks if b["asset"] in cs
                   and b["benchmark"] == "spy" and b["direction"] == "away"})


def weekly_shift_pairs(cfg: Optional[dict] = None) -> list[tuple]:
    """The pairs whose shifts the Weekly may print: config weekly.shift_pairs,
    the named rows' matrix pairs. All-pairs shifts are the Monthly's."""
    c = cfg or config()
    want = {tuple(p.split("__")) for p in (c.get("weekly") or {}).get("shift_pairs") or []}
    return [p for p in pairs(c) if p in want or p[::-1] in want]


def shifts_between(st, start: str, now: str, cfg: Optional[dict] = None,
                   only: Optional[list] = None) -> list[dict]:
    """Every pair (or every pair in `only`) whose stored shift flag was on at a
    session in (start, now], with the evaluation on its strongest flagged day,
    strongest first."""
    c = cfg or config()
    out = []
    for a, b in (pairs(c) if only is None else only):
        on = [d for d, v, _ in _stored(st, shift_key(a, b), now)
              if d > start[:10] and v >= 0.5]
        if not on:
            continue
        c60 = {d: (v, av, None) for d, v, av in _stored(st, pair_key(a, b, 60), now)}
        c252 = {d: (v, av, None) for d, v, av in _stored(st, pair_key(a, b, 252), now)}
        ev = shift_eval(c60, c252, c, set(on))
        best = None
        for d in on:
            e = ev.get(d)
            if not e:
                continue
            s = e["score"] if e["score"] is not None else 0.0
            if best is None or s > best[0]:
                best = (s, d, e)
        if best:
            out.append({"pair": (a, b), "day": best[1], **best[2]})
    out.sort(key=lambda x: -(x.get("score") or 0.0))
    return out


def label(aid: str, cfg: Optional[dict] = None) -> str:
    sp = inputs(cfg)
    return (sp.get(aid) or {}).get("label") or aid


def weekly_line(st, now: str, then: str, cfg: Optional[dict] = None) -> Optional[dict]:
    """The Weekly's one line: only in a week a break or a shift OF A NAMED ROW
    (weekly.shift_pairs) fired; None otherwise, and the Weekly then prints
    nothing. All-pairs shifts are the Monthly's top five, never this line."""
    c = cfg or config()
    wk = c.get("weekly") or {}
    nb, ns = int(wk.get("breaks_shown", 3)), int(wk.get("shifts_shown", 2))
    brk = breaks_between(st, then, now, c)
    sh = shifts_between(st, then, now, c, only=weekly_shift_pairs(c))
    if not brk and not sh:
        return None
    parts = []
    if brk:
        brk.sort(key=lambda b: -abs(b["delta"]))
        shown = ", ".join(f"{label(b['asset'], c)} {b['direction']}"
                          f"{' from' if b['direction'] == 'away' else ''} "
                          f"{b['benchmark'].upper()} ({b['delta']:+.2f})"
                          for b in brk[:nb])
        more = f" and {len(brk) - nb} more" if len(brk) > nb else ""
        parts.append(f"30-day against 120-day break{'s' if len(brk) > 1 else ''}: "
                     f"{shown}{more}")
    if sh:
        shown = ", ".join(f"{label(s['pair'][0], c)}-{label(s['pair'][1], c)} "
                          f"(60d {s['c60']:+.2f} against 252d {s['c252']:+.2f}, "
                          f"{s['rule']})" for s in sh[:ns])
        more = f" and {len(sh) - ns} more" if len(sh) > ns else ""
        parts.append(f"shift{'s' if len(sh) > 1 else ''}: {shown}{more}")
    cr = credit_escalation(brk, c)
    if cr:
        parts.append("credit-sensitive decoupling from SPY: "
                     + ", ".join(label(x, c) for x in cr))
    return {"text": "Correlations: " + "; ".join(parts) + ".",
            "breaks": brk, "shifts": [shift_record(s) for s in sh],
            "credit_sensitive_away": cr}


def shift_record(s: dict) -> dict:
    """A shift as an edition's data carries it."""
    return {"pair": list(s["pair"]), "day": s["day"], "rule": s["rule"],
            "c60": s["c60"], "c252": s["c252"], "gap": round(s["gap"], 6),
            "iqr": None if s["iqr"] is None else round(s["iqr"], 6),
            "score": None if s["score"] is None else round(s["score"], 4)}


FULL_HISTORY_DAYS = 36500


def triple(st, key: str, now: str) -> Optional[dict]:
    """Latest / long-run average / percentile over the store's own full history
    (derived.long_run_average, derived.percentile_of). The five-year column waits
    for the metric lenses (6e)."""
    k = stored_key(key)
    rows = derived.series_as_of(k, as_of=now, window=FULL_HISTORY_DAYS, store=st)
    if not rows:
        return None
    lr = derived.long_run_average(k, now, store=st)
    vals = [v for _, v in rows]
    return {"key": key, "latest": rows[-1][1], "as_of": rows[-1][0],
            "mean": lr.get("mean"), "mean_n": lr.get("n"),
            "since": rows[0][0], "n": len(vals),
            "percentile": derived.percentile_of(vals, rows[-1][1])}


def surprise_quadrant(st, now: str) -> Optional[dict]:
    """THE NAMED HOOK for the surprise quadrant (round 4 item 25): the growth and
    inflation surprise mix a correlation shift is read against (section 9,
    "Mechanism beside arithmetic"). Item 25 builds it; until then this returns
    None and the Monthly says the quadrant is not yet built. No stub data."""
    return None


def peer_table(st, now: str, cfg: Optional[dict] = None) -> list[dict]:
    """Each asset's textbook pairs: the 60-day correlation against its own full-
    history median, and the divergence between them. An absent leg says why."""
    c = cfg or config()
    present = {a["id"] for a in assets(c)}
    reasons = {a["id"]: a.get("absent") for a in absent_assets(c)}
    order = [a["id"] for a in assets(c)]
    out = []
    for aid, peers in (c.get("peers") or {}).items():
        for p in peers or []:
            b = p["peer"]
            row = {"asset": aid, "peer": b, "rationale": p.get("rationale")}
            miss = [x for x in (aid, b) if x not in present]
            if miss:
                row["absent_reason"] = "; ".join(f"{x}: {reasons.get(x) or 'not in the universe'}"
                                                 for x in miss)
                out.append(row)
                continue
            x, y = sorted((aid, b), key=order.index)
            rows = _stored(st, pair_key(x, y, 60), now)
            if not rows:
                row["absent_reason"] = "no 60-day correlation stored at this cutoff"
                out.append(row)
                continue
            vals = [v for _, v, _ in rows]
            med = float(np.median(vals))
            row.update({"latest": rows[-1][1], "as_of": rows[-1][0], "median": med,
                        "divergence": rows[-1][1] - med, "n": len(vals)})
            out.append(row)
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _main(argv: list[str]) -> int:
    import argparse
    p = argparse.ArgumentParser(description="The correlation layer (AQ-5).")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compute")
    c.add_argument("--as-of", default=None)
    c.add_argument("--from", dest="first", default=None)
    c.add_argument("--backfill", action="store_true",
                   help="write every session the inputs support (one-shot, box)")
    c.add_argument("--dry-run", action="store_true")
    for name in ("show", "peers"):
        s = sub.add_parser(name)
        s.add_argument("--as-of", default=None)
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    if a.cmd == "compute":
        r = compute(as_of=a.as_of, first_day=a.first, dry_run=a.dry_run,
                    backfill=a.backfill)
        print(f"correlation: {r['computed']} rows computed from "
              f"{r['first_day'] or 'the first session'}, {r['changed']} changed, "
              f"{r['written']} written" + ("  (dry run)" if r["dry_run"] else ""))
        for k in sorted(r["by_kind"]):
            print(f"  {k:10} {r['by_kind'][k]:>8}")
        return 0
    now = a.as_of or session.utc_iso(timespec="microseconds")
    with observations.ObservationStore() as st:
        if a.cmd == "peers":
            for r in peer_table(st, now):
                if r.get("absent_reason"):
                    print(f"  {r['asset']:8} {r['peer']:8} absent: {r['absent_reason']}")
                else:
                    print(f"  {r['asset']:8} {r['peer']:8} 60d {r['latest']:+.2f} "
                          f"median {r['median']:+.2f} divergence {r['divergence']:+.2f}"
                          f"  ({r['as_of']}, n={r['n']})")
            return 0
        for n in config().get("named") or []:
            t = triple(st, n["key"], now)
            print(f"  {n['key']:34} " + ("absent" if t is None else
                  f"{t['latest']:+.3f} ({t['as_of']})  mean {t['mean']:+.3f}  "
                  f"pct {t['percentile']:.0f} (n={t['n']})"))
        month = (dt.date.fromisoformat(now[:10]) - dt.timedelta(days=31)).isoformat()
        for b in breaks_between(st, month, now):
            print(f"  break  {b['asset']:8} {b['direction']:6} {b['benchmark']} "
                  f"{b['delta']:+.2f} ({b['day']})")
        for s in shifts_between(st, month, now)[:10]:
            print(f"  shift  {s['pair'][0]}-{s['pair'][1]} {s['rule']} "
                  f"60d {s['c60']:+.2f} 252d {s['c252']:+.2f} ({s['day']})")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
