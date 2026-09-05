"""
Validation gate: is the IV solver good enough to run SPX on?

SPX has no independent IV to check against -- that is the whole reason the
solver exists -- so the solver is validated on SPY, where yfinance supplies an
IV we did not compute. If solved IV reproduces yfinance IV, and the GEX profile
built from solved IV reproduces the profile built from yfinance IV, then the
solver is not introducing error and can be trusted on a symbol where nothing is
available to compare against.

This is the same discipline the vendor cross-check applied to the GEX engine:
validate the new component against an independent computation of the same
quantity, on an instrument where both exist, before relying on it where only
one does.

TWO COMPARISONS, because passing one and failing the other means different
things:

    A  per-strike IV      solved vs yfinance, on the eligible OTM wing.
                          Tests the solver in isolation.
    B  the GEX profile    flip, walls and dollar gamma per 1%, computed twice
                          from the same chain with only the IV column swapped.
                          Tests what actually matters downstream -- IV error
                          that cancels out in aggregate is not a problem, and
                          IV error concentrated at high-gamma strikes is.

Tolerances come from config and were declared before this was first run.

Usage:
    python tools/validate_iv_solver.py
    python tools/validate_iv_solver.py --symbols SPY QQQ --date 2026-09-04
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from altdata import config   # noqa: E402
from altdata import session  # noqa: E402
import gex_compute           # noqa: E402
import iv_solver             # noqa: E402

LINE = "=" * 74


def profile_from(rows: list[dict], symbol: str) -> dict:
    """Run the existing engine over rows whose implied_vol column is already
    whichever IV is being tested. Nothing in gex_compute changes -- that is the
    point: only the source of sigma differs."""
    return gex_compute.compute_symbol(rows, symbol)


def pct_diff(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return (a - b) / abs(b) * 100.0


def validate_symbol(symbol: str, date: Optional[str] = None) -> Optional[dict]:
    chains = gex_compute.newest_chains(date, [symbol])
    path = chains.get(symbol)
    if not path:
        print(f"  {symbol}: no stored chain found")
        return None

    rows = gex_compute.load_chain(path)
    spot = next((r["spot"] for r in rows if r.get("spot")), None)
    fetched = next((r.get("fetched_at") for r in rows if r.get("fetched_at")), None)
    if not spot:
        print(f"  {symbol}: chain carries no spot")
        return None

    solved = iv_solver.solve_chain(rows, config.RISK_FREE_RATE, as_of=fetched)
    q = solved["quality"]

    # ---- A: per-strike IV agreement -------------------------------------
    pairs = [(r["solved_iv"], r["implied_vol"]) for r in solved["rows"]
             if r.get("solved_iv") is not None
             and r.get("implied_vol") is not None
             and 0 < r["implied_vol"] < 5.0]
    diffs = [a - b for a, b in pairs]
    abs_diffs = [abs(d) for d in diffs]

    a_stats = {
        "compared": len(pairs),
        "median_abs_diff": round(statistics.median(abs_diffs), 5) if abs_diffs else None,
        "mean_signed_diff": round(statistics.fmean(diffs), 5) if diffs else None,
        "p90_abs_diff": (round(sorted(abs_diffs)[int(len(abs_diffs) * 0.9)], 5)
                         if len(abs_diffs) >= 10 else None),
        "max_abs_diff": round(max(abs_diffs), 5) if abs_diffs else None,
    }

    # ---- B: profile agreement -------------------------------------------
    # Same rows, same engine, only the IV column swapped.
    rows_yf = [dict(r) for r in rows]
    rows_sv = []
    for r in solved["rows"]:
        rr = dict(r)
        rr["implied_vol"] = r.get("solved_iv")
        rows_sv.append(rr)

    p_yf = profile_from(rows_yf, symbol)
    p_sv = profile_from(rows_sv, symbol)
    o_yf, o_sv = p_yf.get("overall") or {}, p_sv.get("overall") or {}

    flip_yf, flip_sv = o_yf.get("gamma_flip"), o_sv.get("gamma_flip")
    flip_diff_pct = (abs(flip_sv - flip_yf) / spot * 100.0
                     if flip_yf is not None and flip_sv is not None else None)

    b_stats = {
        "spot": spot,
        "flip_yf": flip_yf, "flip_solved": flip_sv,
        "flip_diff_pct_of_spot": round(flip_diff_pct, 4) if flip_diff_pct is not None else None,
        "call_wall_yf": o_yf.get("call_wall"), "call_wall_solved": o_sv.get("call_wall"),
        "put_wall_yf": o_yf.get("put_wall"), "put_wall_solved": o_sv.get("put_wall"),
        "gamma_yf": o_yf.get("dollar_gamma_per_1pct"),
        "gamma_solved": o_sv.get("dollar_gamma_per_1pct"),
        "gamma_diff_pct": (round(pct_diff(o_sv.get("dollar_gamma_per_1pct"),
                                          o_yf.get("dollar_gamma_per_1pct")), 3)
                           if o_yf.get("dollar_gamma_per_1pct") else None),
        "max_pain_yf": p_yf.get("max_pain"), "max_pain_solved": p_sv.get("max_pain"),
    }

    # ---- gate ------------------------------------------------------------
    checks: list[tuple[str, bool, str]] = []

    sr = q.get("solve_rate_of_eligible")
    checks.append(("solve rate (eligible OTM)",
                   sr is not None and sr >= config.IV_SOLVER_MIN_SOLVE_RATE,
                   f"{sr} vs >= {config.IV_SOLVER_MIN_SOLVE_RATE}"))

    md = a_stats["median_abs_diff"]
    checks.append(("median |IV diff|",
                   md is not None and md <= config.IV_SOLVER_MAX_MEDIAN_IV_DIFF,
                   f"{md} vs <= {config.IV_SOLVER_MAX_MEDIAN_IV_DIFF}"))

    checks.append(("gamma flip",
                   flip_diff_pct is not None
                   and flip_diff_pct <= config.IV_SOLVER_MAX_FLIP_DIFF_PCT,
                   f"{b_stats['flip_diff_pct_of_spot']}% vs <= "
                   f"{config.IV_SOLVER_MAX_FLIP_DIFF_PCT}%"))

    if config.IV_SOLVER_WALLS_MUST_MATCH_EXACTLY:
        walls_ok = (b_stats["call_wall_yf"] == b_stats["call_wall_solved"]
                    and b_stats["put_wall_yf"] == b_stats["put_wall_solved"])
        checks.append(("walls match exactly", walls_ok,
                       f"call {b_stats['call_wall_yf']}/{b_stats['call_wall_solved']} "
                       f"put {b_stats['put_wall_yf']}/{b_stats['put_wall_solved']}"))

    gd = b_stats["gamma_diff_pct"]
    checks.append(("dollar gamma/1%",
                   gd is not None and abs(gd) <= config.IV_SOLVER_MAX_GAMMA_DIFF_PCT,
                   f"{gd}% vs <= +/-{config.IV_SOLVER_MAX_GAMMA_DIFF_PCT}%"))

    passed = all(ok for _, ok, _ in checks)
    return {"symbol": symbol, "chain": str(path), "quality": q,
            "iv": a_stats, "profile": b_stats, "checks": checks, "pass": passed}


def main() -> int:
    ap = argparse.ArgumentParser(description="IV solver validation gate")
    ap.add_argument("--symbols", nargs="*", default=["SPY"])
    ap.add_argument("--date", default=None)
    args = ap.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print(f"IV solver validation gate   {session.describe()}")
    print(f"  calibration instrument(s): {', '.join(args.symbols)}")
    print(f"  r = {config.RISK_FREE_RATE}   iv_source = {iv_solver.IV_SOURCE}\n")

    results = []
    for sym in args.symbols:
        res = validate_symbol(sym, args.date)
        if not res:
            continue
        results.append(res)
        q, a, b = res["quality"], res["iv"], res["profile"]

        print(f"{LINE}\n{res['symbol']}\n{LINE}")
        print(f"  solve: {q['solved']}/{q['rows_in']} rows  "
              f"eligible-OTM rate {q['solve_rate_of_eligible']}")
        print(f"  rejects: {q['rejects']}")
        print(f"\n  A. per-strike IV vs yfinance ({a['compared']} strikes)")
        print(f"     median |diff| {a['median_abs_diff']}   p90 {a['p90_abs_diff']}   "
              f"max {a['max_abs_diff']}")
        print(f"     mean signed  {a['mean_signed_diff']}  "
              f"({'solver reads higher' if (a['mean_signed_diff'] or 0) > 0 else 'solver reads lower'})")
        print(f"\n  B. GEX profile, same engine, IV column swapped")
        print(f"     {'':<16}{'yfinance':>16}{'solved':>16}")
        print(f"     {'gamma flip':<16}{b['flip_yf']!s:>16}{b['flip_solved']!s:>16}"
              f"   ({b['flip_diff_pct_of_spot']}% of spot)")
        print(f"     {'call wall':<16}{b['call_wall_yf']!s:>16}{b['call_wall_solved']!s:>16}")
        print(f"     {'put wall':<16}{b['put_wall_yf']!s:>16}{b['put_wall_solved']!s:>16}")
        print(f"     {'max pain':<16}{b['max_pain_yf']!s:>16}{b['max_pain_solved']!s:>16}")
        gy, gs = b["gamma_yf"], b["gamma_solved"]
        print(f"     {'$gamma/1%':<16}{gy:>16,.0f}{gs:>16,.0f}"
              if isinstance(gy, (int, float)) and isinstance(gs, (int, float))
              else f"     $gamma/1%       {gy}  {gs}")
        print(f"     {'':<16}{'':>16}{'':>16}   ({b['gamma_diff_pct']}%)")

        print(f"\n  GATE")
        for name, ok, detail in res["checks"]:
            print(f"     [{'PASS' if ok else 'FAIL'}] {name:<28} {detail}")
        print(f"\n  VERDICT: {res['symbol']} "
              f"{'PASSES' if res['pass'] else 'FAILS'} the solver gate")

    if not results:
        print("No symbols validated.")
        return 1

    all_pass = all(r["pass"] for r in results)
    print(f"\n{LINE}")
    print(f"OVERALL: {'PASS' if all_pass else 'FAIL'} -- "
          + ("SPX may go live on solved IV."
             if all_pass else
             "SPX stays out until the failing checks are resolved."))
    print(LINE)
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
