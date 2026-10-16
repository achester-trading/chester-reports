"""
AQ-8a: the gold residual, the driver attribution and the yields-up/dollar-down
series -- stored as calculated series, read by the Monthly (the metals block and
one table in the slow layers; the fiscal_dollar theme's line) and the Weekly (one
line in Plumbing, only in a week the flag fired).

    python -m altdata.attribution compute                # the last few months/weeks
    python -m altdata.attribution compute --backfill     # every month and week (box, once)
    python -m altdata.attribution show [--as-of ...]

Everything it computes is declared in config/attribution.yaml and registered in
metrics_registry.yaml: rights ceiling NARROW FLAG, trigger_eligible false on every
entry, nothing here enters a composite. The two-bid decomposition's paper leg is
altdata/paper_bid.py's, read from the captured chains.

-----------------------------------------------------------------------------
WHAT IS COMPUTED
-----------------------------------------------------------------------------

  calc.gold_residual.*        gold's monthly log return on the 10-year real
                              yield's change (DFII10) and the broad dollar's log
                              return (DTWEXBGS), rolling 36 months: the two betas,
                              the explained share (R squared) and the residual --
                              this month's return less the window's fit, in
                              log-return percent. What real rates and the dollar
                              do not explain (arch Session 12).
  calc.driver_attribution.<family>.*
                              the same regression for every family in the
                              correlation layer's universe, on four common
                              factors (real yield, dollar, the growth and the
                              inflation surprise), rolling 60 months: explained
                              share, residual, each factor's STANDARDISED loading
                              (beta times the factor's sd over the return's, so
                              the four compare), and the sign-stability check
                              behind the section 5 kill condition.
  calc.yields_up_dollar_down.*
                              weekly: the 10-year yield up and the broad dollar
                              down in the same week, a 0/1 flag with each move
                              beside it; recurrence (flagged weeks in the trailing
                              13) and persistence (consecutive flagged weeks).

-----------------------------------------------------------------------------
THE SHARE IS PRINTED, NOT ASSERTED
-----------------------------------------------------------------------------

III Ch 7: "attributing a move to any one driver is guesswork". So nothing here
says WHICH factor moved a family; it prints how much of the window's variance the
factor set explains, the loading that is largest in standardised terms, and the
sign of what is left. The residual is the point of the method: the part of a
move the common factors cannot account for.

-----------------------------------------------------------------------------
POINT IN TIME
-----------------------------------------------------------------------------

Every input is read through ObservationStore.as_of(), so nothing later than the
cutoff is seen; a month (or week) is used only once its last observation is
final (config/attribution.yaml, "Months and weeks"); every row's available_at is
the MAXIMUM across every input row its window touched and its availability_kind
the weakest of theirs (market_features' rule). tools/validate_attribution.py
recomputes stored values from only the rows knowable at their own available_at.
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
CONFIG_PATH = REPO / "config" / "attribution.yaml"

_CFG: Optional[dict] = None


def config() -> dict:
    global _CFG
    if _CFG is None:
        import yaml  # noqa: PLC0415
        _CFG = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    return _CFG


# ---------------------------------------------------------------------------
# Keys
# ---------------------------------------------------------------------------
GOLD = "calc.gold_residual."
GOLD_KEYS = {
    "residual": GOLD + "residual",
    "explained_share": GOLD + "explained_share",
    "beta_real_yield": GOLD + "beta_real_yield",
    "beta_dollar": GOLD + "beta_dollar",
}
YUDD = "calc.yields_up_dollar_down."
YUDD_KEYS = {
    "flag": YUDD + "flag",
    "yield_change_bp": YUDD + "yield_change_bp",
    "dollar_change_pct": YUDD + "dollar_change_pct",
    "recurrence": YUDD + "recurrence_13w",
    "persistence": YUDD + "persistence_weeks",
}
DRIVER = "calc.driver_attribution."


def driver_key(family: str, field: str) -> str:
    return f"{DRIVER}{family}.{field}"


def loading_key(family: str, factor: str) -> str:
    return driver_key(family, f"loading.{factor}")


def sign_key(family: str, factor: str) -> str:
    return driver_key(family, f"sign_stable.{factor}")


# ---------------------------------------------------------------------------
# The driver attribution's universe: the correlation layer's (AQ-5)
# ---------------------------------------------------------------------------
def universe(cfg: Optional[dict] = None) -> tuple[list[dict], list[dict], Optional[str]]:
    """(families with a key, absent families, reason none are read).

    The universe is config/correlation.yaml's -- one list, owned by the
    correlation layer; a member joins the attribution by being given a `key`
    there. Where that file is not in the checkout the attribution computes
    nothing and says why, rather than carrying a second copy of the list."""
    c = cfg or config()
    da = c.get("driver_attribution") or {}
    if da.get("universe") is not None:                    # a gate's own universe
        u = list(da["universe"])
    else:
        path = REPO / str(da.get("universe_config") or "config/correlation.yaml")
        if not path.exists():
            return [], [], (f"{path.relative_to(REPO).as_posix()} is not in this "
                            f"checkout (the correlation layer, AQ-5)")
        import yaml  # noqa: PLC0415
        u = list((yaml.safe_load(path.read_text(encoding="utf-8")) or {})
                 .get("universe") or [])
    return [a for a in u if a.get("key")], [a for a in u if not a.get("key")], None


def driver_factors(cfg: Optional[dict] = None) -> list[str]:
    return list(((cfg or config()).get("driver_attribution") or {}).get("factors") or [])


def _series_registry(cfg: dict) -> tuple[dict, dict, dict, dict]:
    """(explained share, residual, loadings, sign stability): key -> description."""
    fams, _, _ = universe(cfg)
    flab = {k: v.get("label", k) for k, v in (cfg.get("factors") or {}).items()}
    ex, rs, ld, sg = {}, {}, {}, {}
    for a in fams:
        f, lab = a["id"], a.get("label") or a["id"]
        ex[driver_key(f, "explained_share")] = f"{lab}: explained share, 60 months"
        rs[driver_key(f, "residual")] = f"{lab}: this month's residual"
        for x in driver_factors(cfg):
            ld[loading_key(f, x)] = f"{lab}: standardised loading on {flab.get(x, x)}"
            sg[sign_key(f, x)] = f"{lab}: sign stability of the {flab.get(x, x)} loading"
    return ex, rs, ld, sg


# The registry's bulk blocks read these (members_are: keys). Built from the
# correlation universe at import, so a family given a key there is a member here.
try:
    DRIVER_EXPLAINED, DRIVER_RESIDUAL, DRIVER_LOADINGS, DRIVER_SIGNS = \
        _series_registry(config())
except Exception:                                                 # noqa: BLE001
    DRIVER_EXPLAINED, DRIVER_RESIDUAL, DRIVER_LOADINGS, DRIVER_SIGNS = {}, {}, {}, {}


def quadrant_factors(st, now: str) -> Optional[dict]:
    """THE NAMED HOOK for round 4 item 25's surprise quadrant: when it lands, its
    growth and inflation factors replace the two naive surprises in the driver
    attribution. Until then this returns None and the naive surprises stand.
    No stub data."""
    return None


def supply_proxy(family: str, cfg: Optional[dict] = None) -> Optional[str]:
    """THE NAMED HOOK for each family's supply proxy (section 5): a store key in
    config driver_attribution.supply_proxy joins that family's regression as a
    fifth factor. Empty for every family in v1."""
    sp = ((cfg or config()).get("driver_attribution") or {}).get("supply_proxy") or {}
    return sp.get(family) or None


# ---------------------------------------------------------------------------
# Reading the inputs, availabilities included
# ---------------------------------------------------------------------------
Series = dict[str, tuple[float, str, Optional[str]]]   # day -> (value, avail, kind)
Monthly = dict[str, tuple[float, str, Optional[str]]]  # 'YYYY-MM' -> (value, avail, kind)


def _load(db: observations.ObservationStore, key: str, as_of: Optional[str]) -> Series:
    out: Series = {}
    for r in db.as_of(key, as_of=as_of):
        v = r.get("value_num")
        if v is None or not math.isfinite(float(v)):
            continue
        out[str(r["observed_at"])[:10]] = (float(v), str(r["available_at"]),
                                           r.get("availability_kind"))
    return out


def _weakest(kinds) -> Optional[str]:
    ks = set(kinds)
    for weak in ("reconstructed", "ingest_instant", "observed"):
        if weak in ks:
            return weak
    return None


class Inputs:
    """Each input series loaded once per run, as known at the cutoff."""

    def __init__(self, db, as_of: Optional[str]) -> None:
        self.db, self.as_of = db, as_of
        self._cache: dict[str, Series] = {}

    def get(self, key: str) -> Series:
        if key not in self._cache:
            self._cache[key] = _load(self.db, key, self.as_of)
        return self._cache[key]


# ---------------------------------------------------------------------------
# Months and weeks
# ---------------------------------------------------------------------------
def month_of(day: str) -> str:
    return day[:7]


def add_months(m: str, n: int) -> str:
    y, mo = int(m[:4]), int(m[5:7]) - 1 + n
    return f"{y + mo // 12:04d}-{mo % 12 + 1:02d}"


def month_last_day(m: str) -> str:
    nxt = dt.date.fromisoformat(add_months(m, 1) + "-01")
    return (nxt - dt.timedelta(days=1)).isoformat()


def week_of(day: str) -> str:
    """The Friday of the Monday-to-Sunday week a day falls in."""
    d = dt.date.fromisoformat(day)
    return (d + dt.timedelta(days=4 - d.weekday())).isoformat()


def final_closes(s: Series, bucket, last_day) -> Monthly:
    """bucket -> the bucket's last observation, for every bucket whose last
    observation is FINAL: on the bucket's last calendar day, or followed by an
    observation in a later bucket (config/attribution.yaml, "Months and
    weeks"). `bucket(day)` names a day's bucket; `last_day(b)` its end.

    A close proved final by a later print is not knowable before that print:
    its availability is the later of its own and the first later print's, so a
    month read on a Friday is available when Monday's print is, not before."""
    days = sorted(s)
    by: dict[str, int] = {}
    for i, d in enumerate(days):
        by[bucket(d)] = i                       # the latest day in each bucket
    out: Monthly = {}
    for b, i in by.items():
        d = days[i]
        v, av, kd = s[d]
        if d >= last_day(b):
            out[b] = (v, av, kd)
        elif i + 1 < len(days):
            nxt = s[days[i + 1]]
            out[b] = (v, max(av, nxt[1]), _weakest([kd, nxt[2]]))
    return out


def month_closes(s: Series) -> Monthly:
    return final_closes(s, month_of, month_last_day)


def week_closes(s: Series) -> Monthly:
    return final_closes(s, week_of, lambda f: f)


def _ret(a: float, b: float, transform: str, invert: bool = False) -> Optional[float]:
    if transform == "diff":
        r = b - a
    else:
        if a <= 0 or b <= 0:
            return None
        r = math.log(b / a)
    return -r if invert else r


def changes(closes: Monthly, transform: str, invert: bool = False,
            step=add_months) -> Monthly:
    """Each bucket's change from the bucket before it (consecutive buckets only),
    available when the later of the two closes is."""
    out: Monthly = {}
    for b in sorted(closes):
        p = step(b, -1)
        if p not in closes:
            continue
        r = _ret(closes[p][0], closes[b][0], transform, invert)
        if r is None:
            continue
        out[b] = (r, max(closes[p][1], closes[b][1]),
                  _weakest([closes[p][2], closes[b][2]]))
    return out


def monthly_levels(s: Series, lag: int = 0) -> Monthly:
    """A monthly print (a surprise) as its month's value, moved forward `lag`
    months to the month the market met it. One print per reference month: the
    latest-dated in it."""
    out: Monthly = {}
    for d in sorted(s):
        out[add_months(month_of(d), lag)] = s[d]
    return out


def monthly_series(inp: Inputs, spec: dict) -> Monthly:
    """A factor or family's monthly series, from its declared transform."""
    s = inp.get(spec["key"])
    tr = spec.get("transform") or "log_return"
    if tr == "level":
        return monthly_levels(s, int(spec.get("release_lag_months") or 0))
    return changes(month_closes(s), tr, bool(spec.get("invert")))


# ---------------------------------------------------------------------------
# The regression
# ---------------------------------------------------------------------------
def ols(y: np.ndarray, X: np.ndarray) -> Optional[dict]:
    """y on an intercept and the columns of X. None where the fit is not
    determined (too few rows, a flat return or a flat factor)."""
    n, k = X.shape
    if n < k + 3:
        return None
    sy = float(np.std(y))
    sx = np.std(X, axis=0)
    if sy <= 1e-12 or np.any(sx <= 1e-12):
        return None
    A = np.column_stack([np.ones(n), X])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    fit = A @ coef
    res = y - fit
    sst = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - float((res ** 2).sum()) / sst if sst > 0 else None
    betas = coef[1:]
    return {"alpha": float(coef[0]), "betas": [float(b) for b in betas],
            "std": [float(b * s / sy) for b, s in zip(betas, sx)],
            "r2": r2, "resid": res, "fit": fit}


def _window(months: list[str], end: str, w: int) -> list[str]:
    """The w calendar months ending at `end`, or [] if any is missing."""
    want = [add_months(end, -i) for i in range(w - 1, -1, -1)]
    have = set(months)
    return want if all(m in have for m in want) else []


def rolling_fit(y: Monthly, xs: list[Monthly], w: int,
                first: Optional[str] = None) -> dict[str, dict]:
    """end month -> the fit over the w months ending there, for every end month
    (from `first`, where given) where the return and every factor are present
    in all w months."""
    common = sorted(set(y).intersection(*[set(x) for x in xs])) if xs else []
    out: dict[str, dict] = {}
    for end in common:
        if first is not None and end < first:
            continue
        ms = _window(common, end, w)
        if not ms:
            continue
        Y = np.array([y[m][0] for m in ms], dtype=float)
        X = np.array([[x[m][0] for x in xs] for m in ms], dtype=float)
        f = ols(Y, X)
        if f is None:
            continue
        used = [y[m] for m in ms] + [x[m] for x in xs for m in ms]
        f.update({"months": ms, "residual": float(f["resid"][-1]),
                  "available_at": max(u[1] for u in used),
                  "kind": _weakest([u[2] for u in used])})
        out[end] = f
    return out


# ---------------------------------------------------------------------------
# The regime splits and the sign-stability check (section 5's kill condition)
# ---------------------------------------------------------------------------
def split_labels(inp: Inputs, split: dict) -> Monthly:
    """month -> (1.0 or 0.0, avail, kind): which half of the split a month is in.

      change_12m_positive      the month-end level's 12-month change is > 0
      yoy_above_window_median  the 12-month log change, as a level; the median
                               is taken over each window at test time (this
                               returns the rate itself, not a 0/1)"""
    s = inp.get(split["key"])
    rule = split.get("rule")
    if rule == "change_12m_positive":
        cl = month_closes(s)
        out: Monthly = {}
        for m in sorted(cl):
            p = add_months(m, -12)
            if p in cl:
                out[m] = (1.0 if cl[m][0] - cl[p][0] > 0 else 0.0,
                          max(cl[m][1], cl[p][1]), _weakest([cl[m][2], cl[p][2]]))
        return out
    if rule == "yoy_above_window_median":
        lv = monthly_levels(s, int(split.get("release_lag_months") or 0))
        out = {}
        for m in sorted(lv):
            p = add_months(m, -12)
            if p in lv and lv[p][0] > 0 and lv[m][0] > 0:
                out[m] = (math.log(lv[m][0] / lv[p][0]), max(lv[m][1], lv[p][1]),
                          _weakest([lv[m][2], lv[p][2]]))
        return out
    raise ValueError(f"unknown split rule {rule!r}")


def _sign(v: float) -> int:
    return 1 if v > 0 else (-1 if v < 0 else 0)


def sign_stability(y: Monthly, xs: list[Monthly], months: list[str],
                   splits: list[tuple[dict, Monthly]], min_months: int,
                   full_betas: list[float]) -> tuple[list[Optional[bool]], list, list[str]]:
    """Per factor: True (one sign in the whole window and both halves of every
    testable split), False (the kill condition: no stable sign), None (no split
    testable). Also the input rows the test read, and the splits it tested."""
    k = len(xs)
    signs = [{_sign(b)} for b in full_betas]
    tested, used = [], []
    for spec, lab in splits:
        have = [m for m in months if m in lab]
        if not have:
            continue
        if spec.get("rule") == "yoy_above_window_median":
            med = float(np.median([lab[m][0] for m in have]))
            side = {m: lab[m][0] > med for m in have}
        else:
            side = {m: lab[m][0] >= 0.5 for m in have}
        halves = [[m for m in have if side[m]], [m for m in have if not side[m]]]
        if any(len(h) < max(min_months, k + 3) for h in halves):
            continue
        fits = []
        for h in halves:
            Y = np.array([y[m][0] for m in h], dtype=float)
            X = np.array([[x[m][0] for x in xs] for m in h], dtype=float)
            fits.append(ols(Y, X))
        if any(f is None for f in fits):
            continue
        tested.append(spec["id"])
        used += [lab[m] for m in have]
        for f in fits:
            for j in range(k):
                signs[j].add(_sign(f["betas"][j]))
    if not tested:
        return [None] * k, used, tested
    return [len(s) == 1 and 0 not in s for s in signs], used, tested


# ---------------------------------------------------------------------------
# Compute
# ---------------------------------------------------------------------------
def _row(key: str, month_or_day: str, value: float, avail: str,
         kind: Optional[str]) -> dict:
    day = month_last_day(month_or_day) if len(month_or_day) == 7 else month_or_day
    return {"registry_key": key, "instrument": None, "observed_at": day,
            "available_at": avail, "value": round(float(value), 8),
            "source": "calc", "availability_kind": kind}


def gold_returns(inp: Inputs, cfg: dict) -> tuple[Monthly, dict[str, str]]:
    """Gold's monthly log return: the front future's, GLD's where the front has
    none for the month. Each return is taken within one series."""
    g = cfg.get("gold_residual") or {}
    front = changes(month_closes(inp.get(g["gold"]["key"])), "log_return")
    fb = g.get("fallback") or {}
    back = changes(month_closes(inp.get(fb["key"])), "log_return") if fb.get("key") else {}
    out, src = dict(front), {m: g["gold"]["key"] for m in front}
    for m, v in back.items():
        if m not in out:
            out[m], src[m] = v, fb["key"]
    return out, src


def gold_rows(inp: Inputs, cfg: dict, first_month: Optional[str]) -> list[dict]:
    g = cfg.get("gold_residual") or {}
    facs = cfg.get("factors") or {}
    y, _ = gold_returns(inp, cfg)
    xs = [monthly_series(inp, facs[f]) for f in g.get("factors") or []]
    rows = []
    for end, f in rolling_fit(y, xs, int(g.get("window_months", 36)),
                              first_month).items():
        av, kd = f["available_at"], f["kind"]
        rows += [_row(GOLD_KEYS["residual"], end, 100.0 * f["residual"], av, kd),
                 _row(GOLD_KEYS["explained_share"], end, f["r2"], av, kd),
                 _row(GOLD_KEYS["beta_real_yield"], end, f["betas"][0], av, kd),
                 _row(GOLD_KEYS["beta_dollar"], end, f["betas"][1], av, kd)]
    return rows


def driver_rows(inp: Inputs, cfg: dict, first_month: Optional[str],
                st=None, now: Optional[str] = None) -> list[dict]:
    da = cfg.get("driver_attribution") or {}
    fams, _, _ = universe(cfg)
    facs = cfg.get("factors") or {}
    names = driver_factors(cfg)
    fx = {f: monthly_series(inp, facs[f]) for f in names}
    quad = quadrant_factors(st, now or "") if st is not None else None
    if quad:                                   # item 25 replaces the naive two
        fx.update({k: v for k, v in quad.items() if k in fx})
    w = int(da.get("window_months", 60))
    splits = [(s, split_labels(inp, s)) for s in da.get("regime_splits") or []]
    rows = []
    for a in fams:
        fam = a["id"]
        y = monthly_series(inp, {"key": a["key"], "transform": a.get("transform"),
                                 "invert": a.get("invert")})
        fnames = list(names)
        xs = [fx[f] for f in names]
        sp = supply_proxy(fam, cfg)
        if sp:
            fnames.append("supply_proxy")
            xs.append(monthly_series(inp, {"key": sp, "transform": "log_return"}))
        for end, f in rolling_fit(y, xs, w, first_month).items():
            av, kd = f["available_at"], f["kind"]
            rows += [_row(driver_key(fam, "explained_share"), end, f["r2"], av, kd),
                     _row(driver_key(fam, "residual"), end, 100.0 * f["residual"], av, kd)]
            for j, fn in enumerate(fnames[:len(names)]):
                rows.append(_row(loading_key(fam, fn), end, f["std"][j], av, kd))
            stab, used, _ = sign_stability(y, xs, f["months"], splits,
                                           int(da.get("min_months", 18)), f["betas"])
            if used:
                av2 = max([av] + [u[1] for u in used])
                kd2 = _weakest([kd] + [u[2] for u in used])
            else:
                av2, kd2 = av, kd
            for j, fn in enumerate(fnames[:len(names)]):
                if stab[j] is not None:
                    rows.append(_row(sign_key(fam, fn), end,
                                     1.0 if stab[j] else 0.0, av2, kd2))
    return rows


def _add_weeks(f: str, n: int) -> str:
    return (dt.date.fromisoformat(f) + dt.timedelta(weeks=n)).isoformat()


def yudd_rows(inp: Inputs, cfg: dict, first_week: Optional[str]) -> list[dict]:
    """The weekly flag, the two moves beside it, recurrence and persistence."""
    c = cfg.get("yields_up_dollar_down") or {}
    yc = week_closes(inp.get(c["yield"]["key"]))
    dc = week_closes(inp.get(c["dollar"]["key"]))
    ych = changes(yc, "diff", step=_add_weeks)
    dch = changes(dc, "log_return", step=_add_weeks)
    weeks = sorted(set(ych) & set(dch))
    flags: dict[str, tuple[int, str, Optional[str]]] = {}
    rows = []
    for wk in weeks:
        dy, dd = ych[wk], dch[wk]
        flag = 1 if (dy[0] > 0 and dd[0] < 0) else 0
        av, kd = max(dy[1], dd[1]), _weakest([dy[2], dd[2]])
        flags[wk] = (flag, av, kd)
        if first_week and wk < first_week:
            continue
        rows += [_row(YUDD_KEYS["flag"], wk, flag, av, kd),
                 _row(YUDD_KEYS["yield_change_bp"], wk, 100.0 * dy[0], av, kd),
                 _row(YUDD_KEYS["dollar_change_pct"], wk,
                      100.0 * (math.exp(dd[0]) - 1.0), av, kd)]
    n = int(c.get("recurrence_weeks", 13))
    for wk in weeks:
        if first_week and wk < first_week:
            continue
        span = [_add_weeks(wk, -i) for i in range(n - 1, -1, -1)]
        if all(s in flags for s in span):              # off below the window
            used = [flags[s] for s in span]
            rows.append(_row(YUDD_KEYS["recurrence"], wk, sum(u[0] for u in used),
                             max(u[1] for u in used), _weakest([u[2] for u in used])))
        run, p, used = 0, wk, []
        while p in flags and flags[p][0] == 1:
            run += 1
            used.append(flags[p])
            p = _add_weeks(p, -1)
        if p in flags:            # the run's start is in the history (or run 0)
            used.append(flags[p])
            rows.append(_row(YUDD_KEYS["persistence"], wk, run,
                             max(u[1] for u in used), _weakest([u[2] for u in used])))
    return rows


def compute_rows(db: observations.ObservationStore, as_of: Optional[str] = None,
                 first_month: Optional[str] = None, first_week: Optional[str] = None,
                 cfg: Optional[dict] = None) -> list[dict]:
    """Every AQ-8a row (gold residual, driver attribution, yields-up/dollar-down)
    for months >= first_month and weeks >= first_week (None: every one)."""
    c = cfg or config()
    inp = Inputs(db, as_of)
    rows = gold_rows(inp, c, first_month)
    rows += driver_rows(inp, c, first_month, db, as_of)
    rows += yudd_rows(inp, c, first_week)
    return rows


def default_firsts(as_of: Optional[str], cfg: Optional[dict] = None) -> tuple[str, str]:
    c = cfg or config()
    end = (as_of or session.utc_iso())[:10]
    fm = add_months(month_of(end), -int(c.get("recompute_months", 3)))
    fw = _add_weeks(week_of(end), -int(c.get("recompute_weeks", 6)))
    return fm, fw


def compute(as_of: Optional[str] = None, store: Optional[observations.ObservationStore] = None,
            dry_run: bool = False, backfill: bool = False) -> dict:
    """Compute and write. The daily pass writes the last few months and weeks;
    `backfill` writes every one the inputs support. Only a CHANGED value is
    written (observations.drop_unchanged): a re-run is a no-op."""
    own = store is None
    db = store or observations.ObservationStore()
    try:
        fm, fw = (None, None) if backfill else default_firsts(as_of)
        rows = compute_rows(db, as_of=as_of, first_month=fm, first_week=fw)
        fresh = observations.drop_unchanged(db, rows) if rows else []
        written = 0 if dry_run else db.write_many(fresh)
        by: dict[str, int] = {}
        for r in rows:
            fam = r["registry_key"].split(".")[1]
            by[fam] = by.get(fam, 0) + 1
        _, _, why = universe()
        return {"computed": len(rows), "changed": len(fresh), "written": written,
                "first_month": fm, "first_week": fw, "by_kind": by,
                "dry_run": dry_run, "universe_absent": why}
    finally:
        if own:
            db.close()


# ---------------------------------------------------------------------------
# Reading (the Monthly, the Weekly, the CLI)
# ---------------------------------------------------------------------------
FULL_HISTORY_DAYS = 36500
UNTIL_LENSES = "until the lenses"


def triple(st, key: str, now: str) -> Optional[dict]:
    """Latest / long-run average / percentile over the store's own full history
    (derived.long_run_average, derived.percentile_of); the five-year column
    waits for the metric lenses (6e). The correlation layer's triple, by the
    same rule."""
    rows = derived.series_as_of(key, as_of=now, window=FULL_HISTORY_DAYS, store=st)
    if not rows:
        return None
    lr = derived.long_run_average(key, now, store=st)
    vals = [v for _, v in rows]
    return {"key": key, "latest": rows[-1][1], "as_of": rows[-1][0],
            "mean": lr.get("mean"), "mean_n": lr.get("n"), "since": rows[0][0],
            "n": len(vals), "percentile": derived.percentile_of(vals, rows[-1][1])}


def _latest(st, key: str, now: str) -> Optional[tuple[str, float, str]]:
    rows = [r for r in st.as_of(key, now) if r.get("value_num") is not None]
    if not rows:
        return None
    r = max(rows, key=lambda r: str(r["observed_at"]))
    return str(r["observed_at"])[:10], float(r["value_num"]), str(r["available_at"])


def _at(st, key: str, now: str, day: str) -> Optional[float]:
    for r in st.as_of(key, now):
        if str(r["observed_at"])[:10] == day and r.get("value_num") is not None:
            return float(r["value_num"])
    return None


KILL_NONE = "no kill condition ruled (section 5: —)"


def gold_kill_state() -> str:
    return KILL_NONE


def yudd_kill_state() -> str:
    return KILL_NONE


def driver_kill_states(st, family: str, now: str, day: Optional[str] = None,
                       cfg: Optional[dict] = None) -> dict[str, str]:
    """factor -> 'stable' | 'no stable sign (kill condition met; not acted on)' |
    'untestable'. Read from the stored sign rows of the family's latest month."""
    out = {}
    for f in driver_factors(cfg):
        v = _at(st, sign_key(family, f), now, day) if day else None
        out[f] = ("untestable" if v is None else
                  "stable" if v >= 0.5 else
                  "no stable sign (kill condition met; not acted on)")
    return out


FACTOR_SHORT = {"real_yield": "real yield", "dollar": "dollar",
                "growth_surprise": "growth surprise",
                "inflation_surprise": "inflation surprise",
                "supply_proxy": "supply proxy"}


def driver_table(st, now: str, cfg: Optional[dict] = None) -> dict:
    """The Monthly's one table: per family, the explained share, the largest
    standardised loading, this month's residual sign, and the sign-stability
    state behind the kill condition. Families with no row say why."""
    c = cfg or config()
    fams, absent, why = universe(c)
    rows, data, nt = [], [], []
    if why:
        return {"rows": [], "data": [], "not_tracked": [
            f"the driver attribution: {why}; it reads that universe and computes "
            f"nothing until it is merged"], "universe_absent": why}
    for a in fams:
        fam, lab = a["id"], a.get("label") or a["id"]
        ex = _latest(st, driver_key(fam, "explained_share"), now)
        if ex is None:
            nt.append(f"{lab}: under 60 months of complete history at this cutoff")
            continue
        day = ex[0]
        res = _at(st, driver_key(fam, "residual"), now, day)
        loads = {f: _at(st, loading_key(fam, f), now, day) for f in driver_factors(c)}
        loads = {f: v for f, v in loads.items() if v is not None}
        big = max(loads, key=lambda f: abs(loads[f])) if loads else None
        ks = driver_kill_states(st, fam, now, day, c)
        failing = [FACTOR_SHORT.get(f, f) for f, s in ks.items() if s.startswith("no stable")]
        untest = all(s == "untestable" for s in ks.values())
        kill = ("untestable (no regime split long enough)" if untest else
                ("no stable sign: " + ", ".join(failing)) if failing else
                "every loading's sign stable")
        rows.append([lab, f"{100.0 * ex[1]:.0f}%",
                     (f"{FACTOR_SHORT.get(big, big)} ({loads[big]:+.2f})" if big else "—"),
                     ("—" if res is None else "positive" if res > 0 else
                      "negative" if res < 0 else "zero"),
                     kill, day[:7]])
        data.append({"family": fam, "label": lab, "month": day[:7],
                     "explained_share": ex[1], "residual_pct": res,
                     "loadings": loads, "largest": big, "kill_states": ks})
    for a in absent:
        nt.append(f"{a.get('label') or a['id']}: {a.get('absent') or 'no price feed'}")
    if quadrant_factors(st, now) is None:
        nt.append("the surprise quadrant in place of the two naive surprises "
                  "(round 4 item 25; not yet built)")
    if not any(supply_proxy(a["id"], c) for a in fams):
        nt.append("each family's supply proxy (a named hook, empty in v1)")
    return {"rows": rows, "data": data, "not_tracked": nt, "universe_absent": None}


DRIVER_COLUMNS = ["Family", "Explained share", "Largest loading (standardised)",
                  "Residual this month", "Sign stability (the kill condition)",
                  "Month"]
TRIPLE_COLUMNS = ["Series", "Latest (data as of)", "Long-run average (window)",
                  "Percentile, full history", "Percentile, five years"]

GOLD_LABELS = {
    "residual": ("Gold residual (log-return %, this month)", 2),
    "explained_share": ("Share explained by real yields and the dollar", 2),
    "beta_real_yield": ("Beta to the real yield's change", 3),
    "beta_dollar": ("Beta to the broad dollar", 2),
}


def triple_row(t: dict, label: str, dp: int = 2, share: bool = False) -> list[str]:
    """One triple-form row. `share`: a 0-1 fraction, printed as a percentage;
    `dp` 0: a count, printed with thousands separators."""
    def _ord(x: float) -> str:
        n = int(round(x))
        sfx = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{sfx}"

    def _v(x: float) -> str:
        if share:
            return f"{100.0 * x:.0f}%"
        return f"{x:+,.0f}" if dp == 0 else f"{x:+.{dp}f}"
    return [label, f"{_v(t['latest'])} ({t['as_of']})",
            (f"{_v(t['mean'])} (since {t['since']}, n={t['mean_n']:,})"
             if t.get("mean") is not None else "—"),
            (f"{_ord(t['percentile'])} (n={t['n']:,})"
             if t.get("percentile") is not None else "—"),
            UNTIL_LENSES]


def gold_block(st, now: str) -> dict:
    """The gold residual in the triple form, with its kill state."""
    rows, data, nt = [], {}, []
    for f, key in GOLD_KEYS.items():
        t = triple(st, key, now)
        lab, dp = GOLD_LABELS[f]
        if t is None:
            continue
        rows.append(triple_row(t, lab, dp, share=(f == "explained_share")))
        data[f] = t
    if not rows:
        nt.append("the gold residual: under 36 months of complete history at this cutoff")
    return {"rows": rows, "data": data, "not_tracked": nt,
            "kill_state": gold_kill_state()}


def yudd_week_line(st, now: str, then: str) -> Optional[dict]:
    """The Weekly's one line: a flagged week that became knowable in (then, now]
    -- the broad dollar posts a week late, so the week named is usually the one
    before -- or None, and the Weekly prints nothing."""
    hits = [r for r in st.as_of(YUDD_KEYS["flag"], now)
            if r.get("value_num") is not None and float(r["value_num"]) >= 0.5
            and str(r["available_at"]) > then]
    if not hits:
        return None
    r = max(hits, key=lambda r: str(r["observed_at"]))
    wk = str(r["observed_at"])[:10]
    dy = _at(st, YUDD_KEYS["yield_change_bp"], now, wk)
    dd = _at(st, YUDD_KEYS["dollar_change_pct"], now, wk)
    rec = _at(st, YUDD_KEYS["recurrence"], now, wk)
    per = _at(st, YUDD_KEYS["persistence"], now, wk)
    d = dt.date.fromisoformat(wk)
    parts = [f"Yields up, dollar down in the week to {d.day} {d:%b}: the 10-year "
             f"{dy:+.0f}bp, the broad dollar {dd:+.2f}%"]
    if rec is not None:
        parts.append(f"{rec:.0f} of the last 13 weeks")
    if per is not None and per >= 2:
        parts.append(f"{per:.0f} weeks running")
    return {"text": "; ".join(parts) + ".", "week": wk, "yield_change_bp": dy,
            "dollar_change_pct": dd, "recurrence_13w": rec, "persistence_weeks": per}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _main(argv: list[str]) -> int:
    import argparse  # noqa: PLC0415
    p = argparse.ArgumentParser(description="AQ-8a: gold residual, driver "
                                            "attribution, yields-up/dollar-down.")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compute")
    c.add_argument("--as-of", default=None)
    c.add_argument("--backfill", action="store_true",
                   help="write every month and week the inputs support (one-shot, box)")
    c.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("show")
    s.add_argument("--as-of", default=None)
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if a.cmd == "compute":
        r = compute(as_of=a.as_of, dry_run=a.dry_run, backfill=a.backfill)
        frm = (f"from {r['first_month']} (months) and {r['first_week']} (weeks)"
               if r["first_month"] else "from the first month and week")
        print(f"attribution: {r['computed']} rows computed {frm}, {r['changed']} "
              f"changed, {r['written']} written" + ("  (dry run)" if r["dry_run"] else ""))
        for k in sorted(r["by_kind"]):
            print(f"  {k:24} {r['by_kind'][k]:>8}")
        if r["universe_absent"]:
            print(f"  driver attribution: nothing computed -- {r['universe_absent']}")
        return 0
    now = a.as_of or session.utc_iso(timespec="microseconds")
    with observations.ObservationStore() as st:
        g = gold_block(st, now)
        print("gold residual" + ("" if g["rows"] else ": " + "; ".join(g["not_tracked"])))
        for r in g["rows"]:
            print(f"  {r[0]:48} {r[1]:24} mean {r[2]}  pct {r[3]}")
        print(f"  kill state: {g['kill_state']}")
        d = driver_table(st, now)
        print("driver attribution")
        for r in d["rows"]:
            print(f"  {r[0]:26} explained {r[1]:>4}  largest {r[2]:28} residual "
                  f"{r[3]:8}  {r[4]}  ({r[5]})")
        for n in d["not_tracked"]:
            print(f"  not tracked: {n}")
        lf = _latest(st, YUDD_KEYS["flag"], now)
        print("yields-up/dollar-down" + (
            f": week to {lf[0]} flag {lf[1]:.0f}" if lf else ": nothing stored"))
        print(f"  kill state: {yudd_kill_state()}")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
