"""
The allocator (X-1.7): fractional Kelly across engines.

    w = kelly_fraction x Sigma^-1 mu

over the engines' daily returns from the ledger: mu the SHRUNK mean (the same
shrinkage toward zero the posteriors use, so a lucky fortnight is not sized
up), Sigma their realised covariance over the trailing window. Then:

  * CORRELATED ENGINES COUNT ONCE. Engines whose returns correlate above the
    session-set threshold (config/alpha.yaml allocator.correlation_threshold)
    are joined into a cluster; the cluster is one bet, sized on its members'
    average return, and its weight is split equally among them.
  * NO SIZE ABOVE MINIMUM BEFORE THE SAMPLE. An engine with fewer graded signals
    than its horizon's min_signals is held at its min_size, whatever its
    returns say (the constitution's min_size_period).
  * A HALVED ENGINE carries half the weight the formula gives it.
  * NO SHORTING AN ENGINE. A negative Kelly weight is zero: the engine's own
    signals carry direction; the allocator only says how much.
  * THE HEAT CAP. If the absolute weights sum above heat_cap, every weight above
    minimum is scaled down until they fit.

The nightly loop PROPOSES weights; the weekly loop APPLIES them (rebalanced by
the weekly loop, never by hand). Weights are fractions of the lab's notional.
"""

from __future__ import annotations

import math
from typing import Optional

from . import config as acfg


def _mean(x: list[float]) -> float:
    return sum(x) / len(x) if x else 0.0


def _cov(a: list[float], b: list[float]) -> float:
    n = len(a)
    if n < 2:
        return 0.0
    ma, mb = _mean(a), _mean(b)
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (n - 1)


def correlation(a: list[float], b: list[float]) -> Optional[float]:
    va, vb = _cov(a, a), _cov(b, b)
    if va <= 0 or vb <= 0:
        return None
    return _cov(a, b) / math.sqrt(va * vb)


def _solve(m: list[list[float]], v: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting; a singular system raises."""
    n = len(v)
    a = [row[:] + [v[i]] for i, row in enumerate(m)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(a[r][c]))
        if abs(a[p][c]) < 1e-15:
            raise ValueError("singular covariance")
        a[c], a[p] = a[p], a[c]
        for r in range(n):
            if r != c:
                f = a[r][c] / a[c][c]
                a[r] = [x - f * y for x, y in zip(a[r], a[c])]
    return [a[i][n] / a[i][i] for i in range(n)]


def clusters(returns: dict[str, dict[str, float]], threshold: float,
             min_overlap: int) -> list[list[str]]:
    """Union-find over pairs whose correlation on their common days exceeds the
    threshold. `returns` maps engine -> {day: return}."""
    ids = sorted(returns)
    parent = {i: i for i in ids}

    def root(i: str) -> str:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            days = sorted(set(returns[a]) & set(returns[b]))
            if len(days) < min_overlap:
                continue
            c = correlation([returns[a][d] for d in days], [returns[b][d] for d in days])
            if c is not None and c > threshold:
                parent[root(b)] = root(a)
    out: dict[str, list[str]] = {}
    for i in ids:
        out.setdefault(root(i), []).append(i)
    return sorted(out.values())


def weights(engines: list[dict], returns: dict[str, dict[str, float]],
            graded: dict[str, int], con: Optional[dict] = None,
            cfg: Optional[dict] = None) -> dict:
    """{engine_id: {"weight", "cluster", "why"}} plus the run's parameters.

    `engines` are the ledger's engine rows (live and halved); `returns` each
    engine's daily returns; `graded` each engine's count of graded signals."""
    con = con or acfg.constitution()
    cfg = cfg or acfg.settings()
    al = cfg.get("allocator") or {}
    k = float(con["kelly_fraction"])
    thr = float(al.get("correlation_threshold", 0.7))
    cap = float(al.get("heat_cap", 1.0))
    n0 = float((cfg.get("shrinkage") or {}).get("prior_signals", 20))
    window = int(al.get("correlation_window_days", 120))
    overlap = int(al.get("min_overlap_days", 20))
    by_id = {e["id"]: e for e in engines}
    out: dict[str, dict] = {}
    sized: list[str] = []
    for e in engines:
        need = acfg.min_signals(e["horizon"], con)
        if graded.get(e["id"], 0) < need:
            out[e["id"]] = {"weight": float(e["min_size"]), "cluster": e["id"],
                            "why": f"min_size until {need} graded signals "
                                   f"(has {graded.get(e['id'], 0)})"}
        else:
            sized.append(e["id"])
    trimmed = {i: dict(sorted((returns.get(i) or {}).items())[-window:])
               for i in sized}
    groups = clusters(trimmed, thr, overlap) if sized else []
    # One series per cluster: the members' average return on their common days.
    series: dict[str, dict[str, float]] = {}
    for g in groups:
        days = sorted(set.intersection(*[set(trimmed[i]) for i in g])) if g else []
        series["+".join(g)] = {d: _mean([trimmed[i][d] for i in g]) for d in days}
    names = sorted(series)
    common = sorted(set.intersection(*[set(series[c]) for c in names])) if names else []
    kelly: dict[str, float] = {}
    if names and len(common) >= max(2, overlap):
        mats = {c: [series[c][d] for d in common] for c in names}
        n = len(common)
        mu = [_mean(mats[c]) * n / (n + n0) for c in names]
        sig = [[_cov(mats[a], mats[b]) for b in names] for a in names]
        try:
            f = _solve(sig, mu)
        except ValueError:
            f = [m / s[i] if s[i] > 0 else 0.0 for i, (m, s) in enumerate(zip(mu, sig))]
        kelly = {c: max(0.0, k * x) for c, x in zip(names, f)}
    for c in names:
        members = c.split("+")
        w = kelly.get(c, 0.0) / len(members)
        for i in members:
            e = by_id[i]
            why = (f"{k} Kelly on the cluster {c}" if len(members) > 1
                   else f"{k} Kelly")
            if c not in kelly:
                w_i, why = float(e["min_size"]), "min_size: too few common days to size"
            else:
                w_i = w
            if e["status"] == "halved":
                w_i *= 0.5
                why += "; halved by the governor"
            out[i] = {"weight": w_i, "cluster": c, "why": why}
    gross = sum(abs(v["weight"]) for v in out.values())
    if gross > cap:
        floor = sum(abs(v["weight"]) for i, v in out.items() if i not in sized)
        room = max(0.0, cap - floor)
        above = sum(abs(out[i]["weight"]) for i in sized)
        scale = room / above if above > 0 else 0.0
        for i in sized:
            out[i]["weight"] *= scale
            out[i]["why"] += f"; scaled x{scale:.3f} to the heat cap {cap}"
    return {"weights": out, "kelly_fraction": k, "correlation_threshold": thr,
            "heat_cap": cap, "clusters": groups,
            "gross": sum(abs(v["weight"]) for v in out.values())}
