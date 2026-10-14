"""
The validation harness -- the evidence gate (X-1.6; the brief's section 4).

No engine trades paper capital until it has passed this, and the pass is
recorded. What a run does, in order:

1. POINT-IN-TIME ONLY. Every row the harness hands a fit or a test carries the
   instant its decision is taken (`decided_at`) and the instant its data became
   knowable (`available_at`); a row knowable only after its decision VOIDS the
   run (PointInTimeViolation) -- a backtest that touches a later vintage is not
   a weak result, it is no result. pit_series() builds such rows from the store
   by taking, for each period, the latest vintage knowable at its decision.
2. THE HOLD-OUT IS NEVER FITTED. Every row in a hold-out month (the
   constitution's every fourth calendar month: April, August, December) is
   removed before the walk-forward begins; no fit and no walk-forward test ever
   sees it. It is used once, at the end, for the final check before a promotion.
3. WALK-FORWARD WITH THE EMBARGO. Fit on a window, skip the embargo -- the
   constitution's one engine horizon, in rows -- test on the next window, roll.
   A fit never sees its test window's outcomes.
4. THE VARIANT COUNT. Every run adds one to its family's count in alpha.db
   BEFORE it is scored, and is deflated by the count including itself.
5. THE DEFLATED SHARPE (Bailey and Lopez de Prado). The out-of-sample Sharpe
   per signal is compared against the expected maximum Sharpe of N trials under
   the null, SR0 = sqrt(V) * ((1 - g) * Z(1 - 1/N) + g * Z(1 - 1/(N e))), V the
   variance of the Sharpe estimator at the sample's skew and kurtosis. The
   deflated Sharpe is (SR - SR0), annualised at the sample's own signal rate,
   and it must reach the constitution's deflated_sharpe_min (1.0). The
   probabilistic form, Prob(true SR > SR0), is recorded beside it.
6. THE MINIMUM SAMPLE: at least min_signals out-of-sample signals at the
   engine's horizon (daily 100, weekly 40, intraday 400).
7. THE PASS RECORD: the metrics and the parameter ranges the fits chose, on the
   engine's row in alpha.db, and a loop_events row for every run, pass or fail.

A strategy is two callables: fit(rows) -> params, and returns(rows, params) ->
the net-of-cost return of each signal taken on those rows.
"""

from __future__ import annotations

import datetime as dt
import math
import statistics
from dataclasses import dataclass, field
from typing import Callable, Optional

from . import config as acfg

EULER_GAMMA = 0.5772156649015329
HORIZON_ROWS = {"intraday": 1, "daily": 1, "weekly": 5}
_N = statistics.NormalDist()


class PointInTimeViolation(ValueError):
    """A row was used before it was knowable. The run is void."""


@dataclass
class Strategy:
    family: str
    horizon: str
    fit: Callable[[list[dict]], dict]
    returns: Callable[[list[dict], dict], list[float]]
    declared_ranges: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# The hold-out
# ---------------------------------------------------------------------------
def holdout_every(con: Optional[dict] = None) -> int:
    con = con or acfg.constitution()
    return int(con["holdout_months"]["every"])


def is_holdout(day: str, every: Optional[int] = None) -> bool:
    """Every fourth calendar month: a month whose number divides by four."""
    return int(str(day)[5:7]) % (every or holdout_every()) == 0


def holdout_months(first: str, last: str, every: Optional[int] = None) -> list[str]:
    every = every or holdout_every()
    y, m = int(first[:4]), int(first[5:7])
    out = []
    while (y, m) <= (int(last[:4]), int(last[5:7])):
        if m % every == 0:
            out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


# ---------------------------------------------------------------------------
# Point-in-time rows from the store
# ---------------------------------------------------------------------------
def pit_series(store, key: str, decided_at: Callable[[str], str],
               instrument: Optional[str] = None) -> list[dict]:
    """One row per stored period: the latest vintage knowable at that period's
    decision instant. A period with no vintage knowable by then is left out."""
    from altdata.observations import canonical_instant           # noqa: PLC0415
    by_period: dict[str, list[dict]] = {}
    for r in store.all_vintages(key, instrument):
        by_period.setdefault(str(r["observed_at"]), []).append(r)
    out = []
    for period in sorted(by_period):
        t = canonical_instant(decided_at(period))
        ok = [r for r in by_period[period] if str(r["available_at"]) <= t]
        if not ok:
            continue
        r = ok[-1]
        out.append({"day": period[:10], "observed_at": period, "decided_at": t,
                    "available_at": str(r["available_at"]), "value": r["value_num"]})
    return out


def check_pit(rows: list[dict]) -> None:
    for r in rows:
        if r.get("available_at") and r.get("decided_at") and \
                str(r["available_at"]) > str(r["decided_at"]):
            raise PointInTimeViolation(
                f"row {r.get('day')}: available_at {r['available_at']} is after its "
                f"decision {r['decided_at']} -- the run is void")


# ---------------------------------------------------------------------------
# The statistics
# ---------------------------------------------------------------------------
def moments(x: list[float]) -> dict:
    n = len(x)
    if n < 2:
        return {"n": n, "mean": (x[0] if x else 0.0), "sd": 0.0, "skew": 0.0,
                "kurt": 3.0}
    mean = sum(x) / n
    sd = statistics.pstdev(x)
    if sd == 0:
        return {"n": n, "mean": mean, "sd": 0.0, "skew": 0.0, "kurt": 3.0}
    skew = sum((v - mean) ** 3 for v in x) / n / sd ** 3
    kurt = sum((v - mean) ** 4 for v in x) / n / sd ** 4
    return {"n": n, "mean": mean, "sd": statistics.stdev(x), "skew": skew,
            "kurt": kurt}


def expected_max_sharpe(n_trials: int, sr_var: float) -> float:
    """SR0: the expected maximum Sharpe of n_trials under the null."""
    if n_trials <= 1 or sr_var <= 0:
        return 0.0
    a = _N.inv_cdf(1.0 - 1.0 / n_trials)
    b = _N.inv_cdf(1.0 - 1.0 / (n_trials * math.e))
    return math.sqrt(sr_var) * ((1.0 - EULER_GAMMA) * a + EULER_GAMMA * b)


def deflated_sharpe(returns: list[float], n_trials: int,
                    periods_per_year: float) -> dict:
    """The deflated Sharpe of a return sample against n_trials variants."""
    m = moments(returns)
    n = m["n"]
    if n < 3 or m["sd"] == 0:
        return {**m, "sr": 0.0, "sr0": 0.0, "sr_ann": 0.0, "deflated_sharpe": 0.0,
                "dsr_prob": 0.0, "n_trials": n_trials,
                "periods_per_year": periods_per_year}
    sr = m["mean"] / m["sd"]
    v = max(1e-12, (1.0 - m["skew"] * sr + (m["kurt"] - 1.0) / 4.0 * sr * sr) / (n - 1))
    sr0 = expected_max_sharpe(n_trials, v)
    ann = math.sqrt(periods_per_year)
    return {**m, "sr": sr, "sr0": sr0, "sr_ann": sr * ann,
            "deflated_sharpe": (sr - sr0) * ann,
            "dsr_prob": _N.cdf((sr - sr0) / math.sqrt(v)),
            "n_trials": n_trials, "periods_per_year": periods_per_year}


def signal_rate(test_days: list[str], n_signals: int,
                fallback: float) -> float:
    """Signals per year over the span the out-of-sample tests covered."""
    if len(test_days) < 2 or n_signals < 2:
        return fallback
    span = (dt.date.fromisoformat(max(test_days)) -
            dt.date.fromisoformat(min(test_days))).days
    return fallback if span <= 0 else n_signals / (span / 365.25)


# ---------------------------------------------------------------------------
# The walk-forward
# ---------------------------------------------------------------------------
def walk_forward(rows: list[dict], strat: Strategy, fit_rows: int, test_rows: int,
                 con: Optional[dict] = None) -> dict:
    con = con or acfg.constitution()
    check_pit(rows)
    every = holdout_every(con)
    rows = sorted(rows, key=lambda r: r["day"])
    usable = [r for r in rows if not is_holdout(r["day"], every)]
    held = [r for r in rows if is_holdout(r["day"], every)]
    gap = int(con["validation"]["embargo_horizons"]) * HORIZON_ROWS[strat.horizon]
    windows, oos, test_days, fitted = [], [], [], []
    start = 0
    while start + fit_rows + gap + 1 <= len(usable):
        fit = usable[start:start + fit_rows]
        t0 = start + fit_rows + gap
        test = usable[t0:t0 + test_rows]
        if not test:
            break
        params = strat.fit(fit)
        r = list(strat.returns(test, params))
        windows.append({"fit": [fit[0]["day"], fit[-1]["day"]],
                        "test": [test[0]["day"], test[-1]["day"]],
                        "embargo_rows": gap, "params": params, "n": len(r)})
        fitted.append(params)
        oos.extend(r)
        test_days.extend(x["day"] for x in test)
        start += test_rows
    ranges: dict[str, list] = {}
    for p in fitted:
        for k, v in p.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                lo, hi = ranges.get(k, [v, v])
                ranges[k] = [min(lo, v), max(hi, v)]
    final = fitted[-1] if fitted else {}
    hold = list(strat.returns(held, final)) if (held and fitted) else []
    return {"windows": windows, "oos": oos, "test_days": test_days,
            "ranges": ranges, "final_params": final, "holdout_returns": hold,
            "holdout_rows": len(held), "usable_rows": len(usable)}


def run(ledger, engine_id: str, strat: Strategy, rows: list[dict], as_of: str,
        fit_rows: int, test_rows: int, min_size: float = 0.0,
        con: Optional[dict] = None, cfg: Optional[dict] = None) -> dict:
    """One validation run: count it, walk it forward, deflate it, record it."""
    con = con or acfg.constitution()
    cfg = cfg or acfg.settings()
    n_trials = ledger.bump_variant(strat.family, as_of)
    try:
        wf = walk_forward(rows, strat, fit_rows, test_rows, con)
    except PointInTimeViolation as exc:
        ledger.event("validate", "validation_void", as_of, engine_id,
                     after={"why": str(exc), "n_trials": n_trials})
        raise
    ppy = signal_rate(wf["test_days"], len(wf["oos"]),
                      acfg.periods_per_year(strat.horizon, cfg))
    ds = deflated_sharpe(wf["oos"], n_trials, ppy)
    hold = moments(wf["holdout_returns"])
    need = acfg.min_signals(strat.horizon, con)
    floor = float(con["validation"]["deflated_sharpe_min"])
    reasons = []
    if ds["n"] < need:
        reasons.append(f"sample {ds['n']} < min_signals {need}")
    if ds["mean"] <= 0:
        reasons.append("expectancy after costs <= 0")
    if ds["deflated_sharpe"] < floor:
        reasons.append(f"deflated Sharpe {ds['deflated_sharpe']:.2f} < {floor}")
    if wf["holdout_returns"] and hold["mean"] <= 0:
        reasons.append("the hold-out's expectancy <= 0")
    if not wf["holdout_returns"]:
        reasons.append("no hold-out rows to check")
    passed = not reasons
    metrics = {"n_signals": ds["n"], "expectancy": ds["mean"], "sd": ds["sd"],
               "sr": ds["sr"], "sr_ann": ds["sr_ann"], "sr0": ds["sr0"],
               "deflated_sharpe": ds["deflated_sharpe"], "dsr_prob": ds["dsr_prob"],
               "skew": ds["skew"], "kurt": ds["kurt"], "n_trials": n_trials,
               "periods_per_year": ppy, "windows": len(wf["windows"]),
               "holdout_n": hold["n"], "holdout_expectancy": hold["mean"],
               "min_signals": need, "deflated_sharpe_min": floor}
    ranges = {k: v for k, v in wf["ranges"].items()}
    for k, v in (strat.declared_ranges or {}).items():
        ranges.setdefault(k, v)
    result = {"engine_id": engine_id, "family": strat.family, "passed": passed,
              "reasons": reasons, "metrics": metrics, "ranges": ranges,
              "final_params": wf["final_params"], "windows": wf["windows"]}
    ledger.event("validate", "validation_pass" if passed else "validation_fail",
                 as_of, engine_id, after={"metrics": metrics, "reasons": reasons,
                                          "ranges": ranges})
    if passed:
        record_pass(ledger, engine_id, strat, metrics, ranges, as_of, min_size, con)
    return result


def record_pass(ledger, engine_id: str, strat: Strategy, metrics: dict,
                ranges: dict, as_of: str, min_size: float,
                con: Optional[dict] = None) -> None:
    """The pass record on the engine's row: the metrics and the ranges the
    parameters were validated over. Its status is not changed here: promotion
    into paper at min_size is X-2.6's, on the loop's authority."""
    con = con or acfg.constitution()
    have = ledger.engine(engine_id)
    kill = {"rule": con["kill"]["rule"], "after_signals": metrics["min_signals"],
            "expectancy_at_or_below": con["kill"]["expectancy_at_or_below"],
            "realised_sharpe_below": con["kill"]["realised_sharpe_below_deflated_multiple"]
            * metrics["deflated_sharpe"]}
    if have is None:
        ledger.upsert_engine(engine_id, strat.family, strat.horizon, "candidate",
                             min_size, as_of, kill_rule=kill, validated_at=as_of,
                             validated_metrics=metrics, validated_ranges=ranges)
    else:
        ledger.set_engine(engine_id, as_of, validated_at=as_of,
                          validated_metrics=metrics, validated_ranges=ranges,
                          kill_rule=kill)


def refit_allowed(engine: dict, con: Optional[dict] = None) -> bool:
    """No re-fitting inside a drawdown (constitution refit.frozen_in_drawdown):
    a halved or stopped engine is frozen and no loop re-fits it."""
    con = con or acfg.constitution()
    if not con["refit"]["frozen_in_drawdown"]:
        return True
    return not (engine.get("frozen") or engine.get("status") in ("halved", "validation"))
