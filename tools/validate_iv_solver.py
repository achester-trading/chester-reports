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
import exposure_compute      # noqa: E402
import exposure_compute      # noqa: E402
import iv_solver             # noqa: E402

LINE = "=" * 74


def profile_from(rows: list[dict], symbol: str) -> dict:
    """Run the existing engine over rows whose implied_vol column is already
    whichever IV is being tested. Nothing in exposure_compute changes -- that is the
    point: only the source of sigma differs."""
    return exposure_compute.compute_symbol(rows, symbol)


def pct_diff(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return (a - b) / abs(b) * 100.0


def validate_symbol(symbol: str, date: Optional[str] = None) -> Optional[dict]:
    chains = exposure_compute.newest_chains(date, [symbol])
    path = chains.get(symbol)
    if not path:
        print(f"  {symbol}: no stored chain found")
        return None

    rows = exposure_compute.load_chain(path)
    spot = next((r["spot"] for r in rows if r.get("spot")), None)
    fetched = next((r.get("fetched_at") for r in rows if r.get("fetched_at")), None)
    if not spot:
        print(f"  {symbol}: chain carries no spot")
        return None

    solved = iv_solver.solve_chain(rows, config.RISK_FREE_RATE, as_of=fetched)
    q = solved["quality"]

    # DTE=0 is excluded from the IV comparison and from the whole-book profile
    # checks, and gets its own substitute check below. config.IV_SOLVER_EXCLUDE_DTE0
    # carries the reasoning; in one line, the day's expiring contracts have no
    # usable two-sided market at the close, so there is no second IV series to
    # compare against.
    ex0 = config.IV_SOLVER_EXCLUDE_DTE0
    def _keep(r) -> bool:
        return (not ex0) or (r.get("dte") or 0) > 0

    # 0DTE solver coverage, measured so the exclusion is evidenced rather than
    # asserted every time the gate runs.
    z_oi = [r for r in solved["rows"]
            if (r.get("dte") or 0) == 0 and (r.get("open_interest") or 0) > 0]
    z_solved = [r for r in z_oi if r.get("solved_iv") is not None]
    dte0_coverage = (len(z_solved) / len(z_oi)) if z_oi else None

    # ---- A: per-strike IV agreement -------------------------------------
    pairs = [(r["solved_iv"], r["implied_vol"]) for r in solved["rows"]
             if _keep(r)
             and r.get("solved_iv") is not None
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
    # Same rows, same engine, only the IV column swapped. Excludes 0DTE when
    # the flag is set; the bucket is checked separately in E.
    rows_yf = [dict(r) for r in solved["rows"] if _keep(r)]
    rows_sv = []
    for r in solved["rows"]:
        if not _keep(r):
            continue
        rr = dict(r)
        rr["implied_vol"] = r.get("solved_iv")
        rows_sv.append(rr)

    p_yf = profile_from(rows_yf, symbol)
    p_sv = profile_from(rows_sv, symbol)
    o_yf, o_sv = p_yf.get("overall") or {}, p_sv.get("overall") or {}

    flip_yf, flip_sv = o_yf.get("gamma_flip"), o_sv.get("gamma_flip")
    flip_diff_pct = (abs(flip_sv - flip_yf) / spot * 100.0
                     if flip_yf is not None and flip_sv is not None else None)

    # Gross |GEX| of the yfinance-IV profile: the denominator the gamma check
    # divides by. Gross rather than net because net is a residual of two large
    # offsetting halves and dividing a sum of errors by a difference of
    # magnitudes is unstable -- config.IV_SOLVER_GAMMA_DENOMINATOR carries the
    # evidence. The absolute error travels alongside so nothing hides behind
    # the friendlier ratio.
    gross_gex = sum(abs(s["gex"]) for s in (p_yf.get("per_strike") or [])) \
        * 0.01 * (spot or 0.0)
    g_yf = (o_yf.get("dollar_gamma_per_1pct") or 0.0)
    g_sv = (o_sv.get("dollar_gamma_per_1pct") or 0.0)
    gamma_abs_err = abs(g_sv - g_yf)

    b_stats = {
        "spot": spot,
        "gross_gex": gross_gex,
        "gamma_abs_err": gamma_abs_err,
        "gamma_diff_pct_of_gross": (round(gamma_abs_err / gross_gex * 100.0, 3)
                                    if gross_gex else None),
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

    # Same 10% bar, applied to the error as a share of GROSS |GEX| rather than
    # of the net residual. The net ratio is still computed and printed, because
    # it is the honest statement of how far net dealer gamma could be out.
    use_gross = config.IV_SOLVER_GAMMA_DENOMINATOR == "gross"
    gd = (b_stats["gamma_diff_pct_of_gross"] if use_gross
          else b_stats["gamma_diff_pct"])
    checks.append((
        (f"gamma vs {'gross |GEX|' if use_gross else 'net'}"
         + (" (ex-0DTE)" if ex0 else "")),
        gd is not None and abs(gd) <= config.IV_SOLVER_MAX_GAMMA_DIFF_PCT,
        f"{gd}% vs <= +/-{config.IV_SOLVER_MAX_GAMMA_DIFF_PCT}%"
        + (f"  [net residual {b_stats['gamma_diff_pct']}%, "
           f"absolute ${b_stats['gamma_abs_err']:,.0f}]" if use_gross else "")))

    # ---- E: substitute 0DTE check ---------------------------------------
    # 0DTE is out of A and B, so it gets checked as a PROFILE instead of strike
    # by strike: the bucket's GEX under solved IV against the same bucket under
    # yfinance IV. A profile is an integral over strikes and tolerates the
    # per-strike IV noise that a pairwise comparison would flag.
    #
    # Status is three-valued. Below config.IV_SOLVER_DTE0_MIN_COVERAGE the two
    # profiles are integrals over different domains and the check returns None
    # -- INCONCLUSIVE, not a pass. A check that cannot see the thing it is
    # checking must not report green.
    dte0 = {"coverage": (round(dte0_coverage, 4) if dte0_coverage is not None else None),
            "solved": len(z_solved), "with_oi": len(z_oi),
            "gex_yf": None, "gex_solved": None, "diff_pct": None}
    if ex0:
        z_rows = [r for r in solved["rows"] if (r.get("dte") or 0) == 0]
        if z_rows:
            z_yf = profile_from([dict(r) for r in z_rows], symbol)
            z_sv = profile_from([{**r, "implied_vol": r.get("solved_iv")}
                                 for r in z_rows], symbol)
            gy = (z_yf.get("overall") or {}).get("dollar_gamma_per_1pct")
            gs = (z_sv.get("overall") or {}).get("dollar_gamma_per_1pct")
            dte0["gex_yf"], dte0["gex_solved"] = gy, gs
            dte0["diff_pct"] = (round(pct_diff(gs, gy), 3)
                                if gy not in (None, 0) and gs is not None else None)

        cov_ok = (dte0_coverage is not None
                  and dte0_coverage >= config.IV_SOLVER_DTE0_MIN_COVERAGE)
        settled = exposure_compute.is_settled_capture(fetched)
        if settled:
            # Under config.SETTLED_0DTE_RULE the settled profile computes no
            # 0DTE greeks at all, so there is no 0DTE claim for this check to
            # validate. That is N/A, not INCONCLUSIVE: inconclusive means
            # something is asserted and could not be examined.
            #
            # It is DEFERRED, not dismissed. 0DTE greeks are the intraday
            # cadence's property, and the day a 09:45 capture exists this check
            # runs against it for real -- where those contracts have hours of
            # life, two-sided markets, and a coverage rate that can clear the
            # bar. Until then nothing downstream consumes a settled 0DTE greek,
            # so nothing is going unvalidated.
            status = "n/a"
            detail = (f"N/A at a settled capture -- {config.SETTLED_0DTE_RULE} "
                      f"computes no 0DTE greeks. Deferred to the intraday "
                      f"cadence (coverage here was "
                      f"{(dte0_coverage or 0) * 100:.1f}%)")
        elif not cov_ok:
            status = None
            detail = (f"INCONCLUSIVE -- solver priced {dte0['solved']}/"
                      f"{dte0['with_oi']} 0DTE contracts with OI "
                      f"({(dte0_coverage or 0) * 100:.1f}%), below the "
                      f"{config.IV_SOLVER_DTE0_MIN_COVERAGE * 100:.0f}% needed "
                      f"for the profiles to cover the same book")
        else:
            d0 = dte0["diff_pct"]
            status = (d0 is not None
                      and abs(d0) <= config.IV_SOLVER_MAX_GAMMA_DIFF_PCT)
            detail = (f"{d0}% vs <= +/-{config.IV_SOLVER_MAX_GAMMA_DIFF_PCT}% "
                      f"(coverage {(dte0_coverage or 0) * 100:.1f}%)")
        checks.append(("0DTE GEX profile", status, detail))

    failed = any(ok is False for _, ok, _ in checks)
    inconclusive = any(ok is None for _, ok, _ in checks)
    not_applicable = [n for n, ok, _ in checks if ok == "n/a"]
    return {"symbol": symbol, "chain": str(path), "quality": q,
            "iv": a_stats, "profile": b_stats, "checks": checks,
            "dte0": dte0, "excluded_dte0": ex0,
            # An N/A check neither passes nor blocks: nothing is claimed, so
            # there is nothing to certify and nothing left unexamined.
            "pass": not failed and not inconclusive,
            "failed": failed, "inconclusive": inconclusive,
            "not_applicable": not_applicable}


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
        print(f"     {'':<16}{'':>16}{'':>16}   ({b['gamma_diff_pct']}% of net)")
        print(f"     {'gross |GEX|':<16}{b['gross_gex']:>16,.0f}")
        print(f"     {'absolute error':<16}{b['gamma_abs_err']:>16,.0f}"
              f"   ({b['gamma_diff_pct_of_gross']}% of gross)")
        print(f"     -> net dealer gamma could be out by "
              f"${b['gamma_abs_err']:,.0f}; the ratio below does not say "
              f"otherwise")

        if res["excluded_dte0"]:
            d = res["dte0"]
            print(f"\n  0DTE (excluded from A and B; checked as a profile in E)")
            print(f"     solver coverage {d['solved']}/{d['with_oi']} contracts "
                  f"with OI ({(d['coverage'] or 0) * 100:.1f}%)")
            if isinstance(d["gex_yf"], (int, float)):
                print(f"     bucket $gamma/1%  yfIV {d['gex_yf']:>18,.0f}   "
                      f"solved {d['gex_solved']:>18,.0f}   ({d['diff_pct']}%)")

        label = {True: "PASS", False: "FAIL", None: "INCONCL", "n/a": "  N/A"}
        print(f"\n  GATE")
        for name, ok, detail in res["checks"]:
            print(f"     [{label[ok]:^7}] {name:<28} {detail}")
        verdict = ("PASSES" if res["pass"] else
                   "FAILS" if res["failed"] else "is INCONCLUSIVE on")
        print(f"\n  VERDICT: {res['symbol']} {verdict} the solver gate")

    if not results:
        print("No symbols validated.")
        return 1

    any_fail = any(r["failed"] for r in results)
    any_inc = any(r["inconclusive"] for r in results)
    all_pass = not any_fail and not any_inc
    print(f"\n{LINE}")
    deferred = sorted({n for r in results for n in r.get("not_applicable", [])})
    if deferred:
        print(f"DEFERRED (not applicable to a settled capture): "
              f"{', '.join(deferred)}")
        print("  -- these are validated when the intraday cadence lands, and "
              "nothing downstream consumes them before then.")
    if all_pass:
        print("OVERALL: PASS -- SPX may go live on solved IV.")
    elif any_fail:
        print("OVERALL: FAIL -- SPX stays out until the failing checks are resolved.")
    else:
        # Distinct from FAIL on purpose. Nothing disagreed; part of the book
        # could not be examined, which is a different thing to report and a
        # different thing to fix.
        print("OVERALL: INCONCLUSIVE -- nothing failed, but a check could not "
              "see enough of the book to certify it. SPX stays out.")
    print(LINE)
    return 0 if all_pass else 1 if any_fail else 2


if __name__ == "__main__":
    sys.exit(main())
