"""
What the five ST-7 studies share (signal-triage order row ST-7; st-t2-rates,
18 Oct 2026): month arithmetic, a 10-year par bond's monthly total return,
compounding, least squares with Newey-West standard errors, and the ledger's
write through altdata.ledgers (the form the sessions used this week: as-of,
window, n, the pass rule evaluated by code, a CSV of episodes beside the
Markdown).

The calibration rule (tools/calibration/README.md) holds here: every study pulls
full history from the public sources directly; none opens the observation store
or reads the market-state object. Each study is split in two -- load_public()
fetches, study(data) is arithmetic over plain series -- so a gate can hand
study() a fixture and reproduce a hand figure.

Verdict words: PASS, FAIL, INSUFFICIENT. Below a study's floor no rate is
printed (INSUFFICIENT), as the 18 Oct ruling accepted for the constituent
ledgers.
"""

from __future__ import annotations

import datetime as dt
import math
import statistics
import sys
from pathlib import Path
from typing import Optional, Sequence

REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from altdata import ledgers                                     # noqa: E402
from altdata.gtm import par_bond_price                          # noqa: E402

PASS, FAIL, INSUFFICIENT = "PASS", "FAIL", "INSUFFICIENT"
LAPTOP = "laptop run, public sources"
BOX = "box run, public sources"
RIGHTS_NOTE = ("Stated, not granted: the verdict reaches the register only as a "
               "rule-31 draft, and no right changes until the operator accepts it.")

Monthly = dict[str, float]          # {"YYYY-MM": value}
Daily = list[tuple[str, float]]     # [("YYYY-MM-DD", value)], ascending


# ---------------------------------------------------------------------------
# Months
# ---------------------------------------------------------------------------
def madd(m: str, k: int) -> str:
    y, mo = int(m[:4]), int(m[5:7])
    t = y * 12 + (mo - 1) + k
    return f"{t // 12:04d}-{t % 12 + 1:02d}"


def months(a: str, b: str) -> list[str]:
    out, m = [], a
    while m <= b:
        out.append(m)
        m = madd(m, 1)
    return out


def monthly_last(s: Sequence[tuple[str, float]]) -> Monthly:
    out: Monthly = {}
    for d, v in s:
        out[d[:7]] = v
    return out


def monthly_mean(s: Sequence[tuple[str, float]]) -> Monthly:
    acc: dict[str, list[float]] = {}
    for d, v in s:
        acc.setdefault(d[:7], []).append(v)
    return {m: sum(v) / len(v) for m, v in acc.items()}


def yoy_pct(s: Monthly) -> Monthly:
    return {m: 100.0 * (v / s[madd(m, -12)] - 1.0) for m, v in s.items()
            if s.get(madd(m, -12))}


# ---------------------------------------------------------------------------
# Returns
# ---------------------------------------------------------------------------
def bond_tr(gs10: Monthly, years: int = 10) -> Monthly:
    """{month: total return} of a `years` par bond bought at last month's yield
    and priced at this month's, plus a month's coupon (GTM-7's construction)."""
    out: Monthly = {}
    for m, y1 in gs10.items():
        y0 = gs10.get(madd(m, -1))
        if y0 is not None:
            out[m] = par_bond_price(y0 / 100, y1 / 100, years) - 1 + y0 / 100 / 12
    return out


def cash_tr(bill: Monthly) -> Monthly:
    """{month: return} earning last month's bill yield for a month."""
    return {m: bill[madd(m, -1)] / 100 / 12 for m in bill if madd(m, -1) in bill}


def equity_tr(price: Monthly, dividend: Monthly) -> Monthly:
    """Shiller's sheet: (P_m + D_m / 12) / P_{m-1} - 1."""
    out: Monthly = {}
    for m, p in price.items():
        p0 = price.get(madd(m, -1))
        if p0 and m in dividend:
            out[m] = (p + dividend[m] / 12.0) / p0 - 1
    return out


def compound(r: Monthly, start: str, n: int) -> Optional[float]:
    """The return over the n months after `start` (start's own month excluded):
    entry at the end of `start`."""
    g = 1.0
    for k in range(1, n + 1):
        x = r.get(madd(start, k))
        if x is None:
            return None
        g *= 1 + x
    return g - 1


def real(nominal: Optional[float], cpi: Monthly, start: str, n: int) -> Optional[float]:
    a, b = cpi.get(start), cpi.get(madd(start, n))
    if nominal is None or not a or b is None:
        return None
    return (1 + nominal) / (b / a) - 1


def fwd_change(s: Daily, i: int, k: int) -> Optional[float]:
    """s[i+k] - s[i] by observation count, or None past the end."""
    return s[i + k][1] - s[i][1] if i + k < len(s) else None


def index_on_or_before(s: Daily, day: str) -> Optional[int]:
    import bisect
    j = bisect.bisect_right([d for d, _ in s], day) - 1
    return j if j >= 0 else None


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------
def median(xs: Sequence[float]) -> Optional[float]:
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def share(xs: Sequence[bool]) -> Optional[float]:
    return sum(1 for x in xs if x) / len(xs) if xs else None


def expanding_z(x: Monthly, start: str, burn: int) -> Monthly:
    """{month: z of x against x's own mean and sd from `start` through that
    month}, once `burn` months are in the window (point in time: no month sees
    a later one)."""
    out: Monthly = {}
    hist: list[float] = []
    for m in sorted(k for k in x if k >= start):
        hist.append(x[m])
        if len(hist) >= burn:
            mu = sum(hist) / len(hist)
            sd = math.sqrt(sum((h - mu) ** 2 for h in hist) / (len(hist) - 1))
            if sd:
                out[m] = (x[m] - mu) / sd
    return out


def solve(a: list[list[float]], b: list[float]) -> list[float]:
    """Gauss-Jordan with partial pivoting."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        if abs(m[p][c]) < 1e-14:
            raise ValueError("singular design matrix")
        m[c], m[p] = m[p], m[c]
        piv = m[c][c]
        m[c] = [v / piv for v in m[c]]
        for r in range(n):
            if r != c and m[r][c]:
                f = m[r][c]
                m[r] = [vr - f * vc for vr, vc in zip(m[r], m[c])]
    return [m[i][n] for i in range(n)]


def inverse(a: list[list[float]]) -> list[list[float]]:
    n = len(a)
    cols = [solve(a, [1.0 if i == j else 0.0 for i in range(n)]) for j in range(n)]
    return [[cols[j][i] for j in range(n)] for i in range(n)]


def ols_nw(y: Sequence[float], xs: Sequence[Sequence[float]], lags: int) -> dict:
    """y = b0 + b1 x1 + ... by least squares, with Newey-West (Bartlett) standard
    errors at `lags` -- overlapping 12-month changes are autocorrelated by
    construction, so plain OLS errors would overstate every t."""
    n, k = len(y), len(xs) + 1
    if n <= k + 1:
        raise ValueError(f"ols_nw needs more than {k + 1} points, got {n}")
    X = [[1.0] + [x[i] for x in xs] for i in range(n)]
    xtx = [[sum(X[t][i] * X[t][j] for t in range(n)) for j in range(k)] for i in range(k)]
    xty = [sum(X[t][i] * y[t] for t in range(n)) for i in range(k)]
    b = solve(xtx, xty)
    e = [y[t] - sum(b[i] * X[t][i] for i in range(k)) for t in range(n)]
    s = [[sum(e[t] ** 2 * X[t][i] * X[t][j] for t in range(n)) for j in range(k)]
         for i in range(k)]
    for L in range(1, min(lags, n - 1) + 1):
        w = 1.0 - L / (lags + 1.0)
        for i in range(k):
            for j in range(k):
                s[i][j] += w * sum(e[t] * e[t - L] * (X[t][i] * X[t - L][j]
                                                      + X[t - L][i] * X[t][j])
                                   for t in range(L, n))
    inv = inverse(xtx)
    cov = [[sum(inv[i][p] * s[p][q] * inv[q][j] for p in range(k) for q in range(k))
            for j in range(k)] for i in range(k)]
    se = [math.sqrt(max(cov[i][i], 0.0)) for i in range(k)]
    my = sum(y) / n
    syy = sum((v - my) ** 2 for v in y)
    r2 = 1.0 - sum(v * v for v in e) / syy if syy else 0.0
    return {"b": b, "se": se, "t": [b[i] / se[i] if se[i] else float("nan")
                                    for i in range(k)], "n": n, "r2": r2,
            "lags": lags}


# ---------------------------------------------------------------------------
# The ledger
# ---------------------------------------------------------------------------
def f2(v: Optional[float], nd: int = 2, unit: str = "") -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "n/a"
    return f"{v:+.{nd}f}{unit}"


def pct(v: Optional[float], nd: int = 1) -> str:
    return "n/a" if v is None else f"{100 * v:+.{nd}f}%"


def sh(v: Optional[float], nd: int = 1) -> str:
    """A share, unsigned: 0.558 -> "55.8%"."""
    return "n/a" if v is None else f"{100 * v:.{nd}f}%"


def publish(r: dict, out: Optional[str], date: Optional[str]) -> None:
    md, cv = ledgers.write_ledger(r, Path(out) if out else None, date)
    print(f"{r['item']}: {r['verdict']}  (n {r['n']}; as of {r['as_of']})")
    print(f"  wrote {md.relative_to(REPO) if md.is_relative_to(REPO) else md}"
          + (f" and {cv.name}" if cv else ""))


def cli(item: str, load, study, argv=None) -> int:
    """`python tools/calibration/<script>.py [--box] [--out DIR] [--date D]`."""
    import argparse
    ap = argparse.ArgumentParser(description=f"{item} calibration study (ST-7)")
    ap.add_argument("--box", action="store_true",
                    help="label the edition a box run (same public sources)")
    ap.add_argument("--out", help="ledger directory (default docs/ledgers)")
    ap.add_argument("--date", help="edition date (default today)")
    a = ap.parse_args(argv)
    data = load()
    r = study(data, BOX if a.box else LAPTOP)
    publish(r, a.out, a.date or dt.date.today().isoformat())
    return 0
