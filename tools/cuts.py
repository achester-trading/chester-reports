"""
The cuts -- graded decisions sliced, every figure with its n and its interval.

-----------------------------------------------------------------------------
THE INTERVAL IS PRINTED BEFORE THE POINT
-----------------------------------------------------------------------------
Evidence and Inference Chapter 1 is explicit and this module is its
implementation: "every figure the register prints carries its sample size AND its
interval, and the interval is read before the point."

    For an average of n observations with spread sigma, the standard error is
    sigma / sqrt(n). Trading results have a per-decision spread close to one R,
    so the standard error of measured expectancy is roughly 1 / sqrt(n) in R.
    The ninety-five percent interval is about twice that on either side.

So the output puts n and the interval to the LEFT of the mean, in reading order,
because a 0.4R expectancy on n=3 and a 0.4R expectancy on n=400 are different
claims and only the interval says so. The paper's own table is the calibration:
at n=200, roughly a year, a true 0.2R edge is known only to lie between +0.06R
and +0.34R -- positive, magnitude unknown by a factor of six. A cut printed
without its interval invites exactly the conclusion the paper exists to forbid.

sigma IS MEASURED, not assumed. The paper's 1R is a calibration figure for its
table; a real cut has the sample and should use it. Below n=2 there is no spread
to measure and the interval is reported as unavailable rather than as the
paper's approximation dressed up as a measurement.

-----------------------------------------------------------------------------
EXPECTANCY IS COMPUTED ON THE RULED R
-----------------------------------------------------------------------------
r_multiple_ruled, not r_multiple. The ruled column is what an operator who
honoured his own invalidation actually earned; the thesis column is what the idea
was worth if held through the stop. Both are reported per cut, because the GAP
between them is the cost of where the invalidations are being placed -- and that
gap is a finding about the operator's risk geometry rather than about his theses.

-----------------------------------------------------------------------------
THE CUTS, AND WHY THESE FIVE
-----------------------------------------------------------------------------
    status           taken / declined / draft. The operator's filter, measured.
    owning report    from the horizon, via Part 7's owner column.
    book             the Doctrine's A/B/C/D, derived from the horizon.
    mechanism group  which cluster of evidence the decision rested on.
    regime           SPY gamma sign at entry -- the ONE regime variable that
                     exists today. Named as such rather than implying a richer
                     regime model than the system has.

    python tools/cuts.py
    python tools/cuts.py --json
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any, Callable, Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import grader  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78

# The Doctrine's Part IV books, mapped from the register's horizon. Two
# taxonomies for one thing, and the map is stated here rather than inferred at
# each use: Book A is the monthly allocation stance, B the swing book, C the
# tactical day book, D the opportunistic layer with no fixed horizon.
HORIZON_BOOK = {
    "intraday": "C (tactical, 1-5 days)",
    "swing": "B (swing, 1-6 weeks)",
    "positional": "A (allocation, 1-6 months)",
    "strategic": "A (allocation, 1-6 months)",
    "structural": "D (no fixed horizon)",
}

# 95% is about +/- 1.96 standard errors. The paper rounds this to "about twice",
# and the rounding is kept visible rather than silently applied.
Z95 = 1.96


def interval(values: list[float]) -> dict:
    """n, mean, measured sigma, standard error and the 95% interval.

    Returns the interval as None when n < 2. There is no spread to measure from
    one observation, and substituting the paper's 1R approximation would present
    a calibration constant as a measurement of this sample.
    """
    n = len(values)
    out: dict[str, Any] = {"n": n, "mean": None, "sigma": None, "se": None,
                           "lo": None, "hi": None,
                           "note": "" if n >= 2 else
                                   "n < 2: no spread to measure, so no interval"}
    if not n:
        out["note"] = "no graded decisions in this cut"
        return out
    out["mean"] = statistics.fmean(values)
    if n < 2:
        return out
    out["sigma"] = statistics.stdev(values)
    out["se"] = out["sigma"] / math.sqrt(n)
    out["lo"] = out["mean"] - Z95 * out["se"]
    out["hi"] = out["mean"] + Z95 * out["se"]
    # The paper's own yardstick, alongside the measurement, so a reader can see
    # when the sample's spread is unusual rather than only its mean.
    out["paper_se_1r"] = 1.0 / math.sqrt(n)
    return out


def _vals(rows: list[dict], field: str) -> list[float]:
    return [r[field] for r in rows
            if isinstance(r.get(field), (int, float)) and r[field] is not None]


def summarise(rows: list[dict]) -> dict:
    """One cut's figures. Expectancy on the RULED R; the thesis R beside it."""
    ruled = _vals(rows, "r_multiple_ruled")
    thesis = _vals(rows, "r_multiple")
    hits = [r for r in rows if r.get("invalidation_hit") == 1]
    wins = [v for v in ruled if v > 0]
    out = {
        "decisions": len(rows),
        "expectancy_ruled": interval(ruled),
        "thesis_r": interval(thesis),
        "return_pct": interval(_vals(rows, "return_pct")),
        "mae_close_pct": interval(_vals(rows, "mae_close_pct")),
        "invalidation_hit_rate": (len(hits) / len(rows)) if rows else None,
        "invalidations_hit": len(hits),
        "win_rate_ruled": (len(wins) / len(ruled)) if ruled else None,
        "no_r": len(rows) - len(ruled),
    }
    # The gap: what honouring the invalidation cost, or saved, in R per decision.
    if ruled and thesis and len(ruled) == len(thesis):
        out["rule_cost_r"] = interval([t - r for t, r in zip(thesis, ruled)])
    else:
        out["rule_cost_r"] = interval([])
    return out


def by(rows: list[dict], key: Callable[[dict], Optional[str]]) -> dict:
    groups: dict[str, list[dict]] = {}
    for r in rows:
        k = key(r) or "(unrecorded)"
        groups.setdefault(str(k), []).append(r)
    return {k: summarise(v) for k, v in sorted(groups.items())}


def status_of(r: dict) -> str:
    """taken / declined / draft, as the question is actually asked.

    `status` and `operator_action` are different axes and the cut wants the
    operator's decision: a row is TAKEN when he took it, DECLINED when he passed,
    and otherwise it is a draft the system recorded and nobody promoted.
    """
    action = (r.get("operator_action") or "").upper()
    if action == "TAKE":
        return "taken"
    if action == "DECLINE":
        return "declined"
    if action == "MODIFY":
        return "taken (modified)"
    return f"draft ({r.get('status') or 'unknown'})"


def all_cuts(db_path: Optional[str] = None) -> dict:
    with grader.GradeStore(db_path) as store:
        rows = store.all_grades()
    return {
        "method_version": grader.METHOD_VERSION,
        "total": len(rows),
        "overall": summarise(rows),
        "by_status": by(rows, status_of),
        "by_owning_report": by(rows, lambda r: grader.HORIZON_OWNER.get(
            r.get("horizon"), f"(no owner for horizon {r.get('horizon')!r})")),
        "by_book": by(rows, lambda r: HORIZON_BOOK.get(
            r.get("horizon"), f"(no book for horizon {r.get('horizon')!r})")),
        "by_mechanism_group": by(rows, lambda r: r.get("mechanism_group")
                                 or "(not recorded on the grade)"),
        "by_regime_spy_gamma": by(rows, lambda r: r.get("spy_gamma_sign")),
    }


def _fmt_interval(iv: dict, unit: str = "R") -> str:
    """n and the interval FIRST, the point last. See the module docstring."""
    n = iv["n"]
    if not n:
        return f"n=0    {iv['note']}"
    if iv["lo"] is None:
        return f"n={n:<4} interval unavailable ({iv['note']})   mean {iv['mean']:+.3f}{unit}"
    return (f"n={n:<4} 95% [{iv['lo']:+.3f}, {iv['hi']:+.3f}]{unit}"
            f"   mean {iv['mean']:+.3f}{unit}"
            f"   sigma {iv['sigma']:.3f}  se {iv['se']:.3f}")


def print_cuts(res: dict) -> None:
    print(f"{LINE}\nGRADED DECISIONS -- cuts, each with n and interval\n{LINE}")
    print(f"  method: {res['method_version']}   graded rows: {res['total']}")
    print(f"\n  Per Evidence and Inference Ch. 1, the interval is printed BEFORE")
    print(f"  the point. A 0.4R mean on n=3 and on n=400 are different claims and")
    print(f"  only the interval says which one is in front of you. At n=200 -- about")
    print(f"  a year -- a true 0.2R edge is known only to lie in [+0.06, +0.34].")

    if not res["total"]:
        print(f"\n{LINE}")
        print("  NO GRADED DECISIONS YET. Every cut below would be n=0, so none is")
        print("  printed: a table of zeros invites a reader to treat the structure")
        print("  as a result. The grader reports per decision why each is not yet")
        print("  gradeable -- run `python -m altdata.grader`.")
        print(LINE)
        return

    o = res["overall"]
    print(f"\n  OVERALL")
    print(f"    expectancy (ruled)  {_fmt_interval(o['expectancy_ruled'])}")
    print(f"    thesis R            {_fmt_interval(o['thesis_r'])}")
    print(f"    cost of the rule    {_fmt_interval(o['rule_cost_r'])}")
    print(f"    return              {_fmt_interval(o['return_pct'], '%')}")
    print(f"    MAE (closes only)   {_fmt_interval(o['mae_close_pct'], '%')}")
    wr = o["win_rate_ruled"]
    hr = o["invalidation_hit_rate"]
    print(f"    win rate (ruled)    {'n/a' if wr is None else f'{wr:.0%}'}"
          f"   invalidation hit {'n/a' if hr is None else f'{hr:.0%}'}"
          f"   without an R: {o['no_r']}")

    for title, key in (("BY STATUS -- the operator's filter, measured", "by_status"),
                       ("BY OWNING REPORT (Part 7's owner column)", "by_owning_report"),
                       ("BY BOOK (the Doctrine's Part IV)", "by_book"),
                       ("BY MECHANISM GROUP", "by_mechanism_group"),
                       ("BY REGIME -- SPY gamma sign at entry, the one regime "
                        "variable that exists today", "by_regime_spy_gamma")):
        print(f"\n  {title}")
        for k, v in res[key].items():
            print(f"    {k:<28} {_fmt_interval(v['expectancy_ruled'])}")
    print(f"\n{LINE}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Cuts over graded decisions")
    ap.add_argument("--db", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    res = all_cuts(args.db)
    if args.json:
        print(json.dumps(res, indent=2, sort_keys=True, default=str))
        return 0
    print_cuts(res)
    return 0


if __name__ == "__main__":
    sys.exit(main())
