#!/usr/bin/env python3
"""
Validation gate for tools/base_rates.py. (31.1)

    python tools/validate_base_rates.py

Three properties, and the third is the one that would otherwise go unchecked:

  A. DETERMINISM. Recomputing a table twice from the same store gives a
     BYTE-IDENTICAL result once the provenance stamps are removed. A base rate
     cited in a packet is only replayable if this holds, and the failure mode it
     guards against is a library's percentile definition changing under us --
     which is why base_rates.pctile() is written out rather than imported.

  B. THE PAPER'S HEADLINE FIGURES, printed BESIDE the computed ones whether they
     pass or fail. The gate's output is the comparison table: a reader should be
     able to see that the -5% frequency is 3.42 against the paper's 3-4 without
     running anything. A figure outside its declared tolerance fails the gate.

  C. THE CITATION RULES. Every table carries the registry fields 31.1 names, the
     mechanism group is base_rate and nothing in it is trigger_eligible, the two
     drawdown definitions are both present and differ (a single definition
     silently answering both questions is the defect), and the not_yet_sourced
     gaps say what they need.

WHY A SEPARATE GATE AND NOT A GROUP IN validate_derived.py. These tables are a
different kind of artefact: they are recomputed once a year, they are cited by id
from decision packets, and their correctness is checked against a document rather
than against arithmetic. A failure here means a cited base rate has moved or a
paper and the code disagree, which is a different conversation from a delta unit
being wrong.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import derived, observations                      # noqa: E402
from tools import base_rates as br                             # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78
PASS = 0
FAIL = 0


def ok(msg: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {msg}")


def bad(msg: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {msg}")


def check(cond: bool, msg: str) -> bool:
    (ok if cond else bad)(msg)
    return bool(cond)


def strip_provenance(table: dict) -> dict:
    """The table minus the stamps that must differ between two computations."""
    return {k: v for k, v in table.items()
            if k not in ("computed_at", "as_of")}


def group_a(tables: dict, again: dict) -> None:
    print(f"\n{LINE}\nA. A RECOMPUTE IS IDENTICAL\n{LINE}")
    for key in br.TABLE_KEYS:
        a = json.dumps(strip_provenance(tables[key]), sort_keys=True)
        b = json.dumps(strip_provenance(again[key]), sort_keys=True)
        check(a == b, f"{key} recomputes byte-identically ({len(a)} chars)")
    check(tables[br.TABLE_KEYS[0]].get("computed_at")
          != again[br.TABLE_KEYS[0]].get("computed_at"),
          "and the two runs DID have different computed_at stamps, so the "
          "comparison above is not vacuously true")


def group_b(tables: dict) -> None:
    print(f"\n{LINE}\nB. THE PAPER'S FIGURES, BESIDE THE COMPUTED ONES\n{LINE}")
    print(f"  {'figure':<56}{'computed':>10}{'paper':>10}{'tol':>7}")
    for key, path, paper, tol, note in br.PAPER_FIGURES:
        got = br.dig(tables.get(key) or {}, path)
        if got is None:
            print(f"  {note:<56}{'absent':>10}{paper:>10.3f}{tol:>7.3f}")
            bad(f"{note} -- the field {path} is absent from {key}")
            continue
        inside = abs(float(got) - paper) <= tol
        print(f"  {note:<56}{float(got):>10.3f}{paper:>10.3f}{tol:>7.3f}"
              f"  {'' if inside else '<-- OUTSIDE'}")
        if not inside:
            bad(f"{note}: computed {float(got):.3f}, paper {paper}, tolerance "
                f"{tol}")
    if FAIL == 0:
        ok(f"all {len(br.PAPER_FIGURES)} headline figures land inside their "
           f"declared tolerance of the paper")


def group_c(tables: dict) -> None:
    print(f"\n{LINE}\nC. THE REGISTRY FIELDS 31.1 NAMES\n{LINE}")
    want = {"observation_type": "calculated",
            "information_half_life": "permanent",
            "revision_policy": "recomputed",
            "mechanism_group": "base_rate",
            "native_horizon": "structural"}
    for key in br.TABLE_KEYS + (br.REVIEW_KEY,):
        e = derived.registry_entry(key)
        if not check(bool(e), f"{key} has a registry entry"):
            continue
        wrong = {k: e.get(k) for k, v in want.items() if e.get(k) != v}
        check(not wrong, f"{key} carries the declared fields"
                         + (f" -- got {wrong}" if wrong else ""))
        check(e.get("trigger_eligible") is False,
              f"{key} is NOT trigger_eligible -- a base rate is a denominator "
              f"and can never say that something is happening now")
    check(len(br.TABLE_KEYS) == 6,
          f"six tables are declared (got {len(br.TABLE_KEYS)})")


def group_d(tables: dict) -> None:
    print(f"\n{LINE}\nD. THE TWO DRAWDOWN DEFINITIONS ARE BOTH PRESENT\n{LINE}")
    t = tables["baserate.drawdown_by_depth"]
    defs = t.get("definitions") or {}
    check(set(defs) >= {"from_running_max", "threshold_swings",
                        "which_the_paper_uses"},
          "both definitions are named on the table, and which one the paper's "
          "frequency column counts")
    band = (t.get("bands") or {}).get("-5%") or {}
    rm = ((band.get("from_running_max") or {}).get("postwar") or {}).get("per_year")
    sw = ((band.get("threshold_swings") or {}).get("postwar") or {}).get("per_year")
    check(rm is not None and sw is not None,
          f"-5% carries both frequencies (running max {rm}/yr, swings {sw}/yr)")
    if rm and sw:
        check(sw > rm * 1.5,
              f"and they genuinely differ ({sw}/yr against {rm}/yr) -- if one "
              f"definition could answer both questions there would be no reason "
              f"to store two, and citing either as 'the' -5% frequency would be "
              f"safe. It is not.")

    print(f"\n{LINE}\nE. WHAT IS ABSENT SAYS WHAT IT NEEDS\n{LINE}")
    s = tables["baserate.streaks_and_gaps"]
    for field in ("gaps", "overnight_vs_intraday"):
        blk = s.get(field) or {}
        check(blk.get("state") == "not_yet_sourced",
              f"{field} reports not_yet_sourced rather than a figure computed "
              f"from the wrong series")
        check(bool(blk.get("needs")) and bool(blk.get("reason")),
              f"and names what it needs ({blk.get('needs')})")
    c = tables["baserate.correlation_by_regime"]
    proxies = c.get("proxies") or {}
    p = proxies.get("avg_pairwise_sector_correlation") or {}
    check(p.get("proxy_for") and p.get("direction"),
          "the pairwise correlation declares what it proxies for AND which way "
          "the proxy errs -- a proxy whose direction is unknown cannot be read")

    print(f"\n{LINE}\nF. THE DRIFT FLAG FIRES, AND NOT ACROSS METHODS\n{LINE}")
    key = "baserate.intra_year_drawdown"
    cur = tables[key]
    moved = json.loads(json.dumps(cur))
    moved["distribution"]["median"] = (cur["distribution"]["median"] or 0) - 9.0
    flags = br.drift(cur, moved, key)
    check(any(f["field"] == "distribution.median" for f in flags),
          "a 9-point move in the intra-year median is flagged for review")
    check(not br.drift(cur, json.loads(json.dumps(cur)), key),
          "and an unchanged table flags nothing")
    other = json.loads(json.dumps(moved))
    other["method_version"] = "base-rates-method-99"
    across = br.drift(cur, other, key)
    check(len(across) == 1 and across[0]["field"] == "method_version",
          "a method change is reported as a method change and NOT as drift -- a "
          "deliberate redefinition is not a moving base rate")

    print(f"\n{LINE}\nG. THE MOVE PERCENTILE READS THE STORED GRID\n{LINE}")
    r = br.percentile_of_move(-2.0, "daily", table=cur if False else
                              tables["baserate.returns_by_frequency"])
    check(r is not None and r.get("percentile") is not None,
          f"a -2% session places in the long-run distribution "
          f"({(r or {}).get('percentile')}th percentile of "
          f"{(r or {}).get('n')} sessions)")
    up = br.percentile_of_move(+2.0, "daily",
                               table=tables["baserate.returns_by_frequency"])
    check((up or {}).get("percentile", 0) > (r or {}).get("percentile", 100),
          "and a +2% session places above a -2% one")
    far = br.percentile_of_move(-50.0, "daily",
                                table=tables["baserate.returns_by_frequency"])
    check((far or {}).get("beyond_grid") == "below",
          "a move beyond the stored grid says so rather than inventing a "
          "percentile the grid cannot support")


def main() -> int:
    print(f"{LINE}\nbase_rates.py -- 31.1\n{LINE}")
    db = observations.ObservationStore()
    try:
        tables = br.compute(store=db)
        again = br.compute(store=db)
    finally:
        db.close()
    if not tables[br.TABLE_KEYS[0]].get("method_version"):
        print("  FAIL  no tables computed at all")
        return 1
    absent = [k for k in br.TABLE_KEYS if tables[k].get("state") == "absent"]
    if absent:
        print(f"\n  SKIPPED -- {len(absent)} table(s) have no input data in this "
              f"store:\n    {tables[absent[0]].get('absent_reason')}")
        print(f"\n{LINE}\nNOT VALIDATED (no data). Run "
              f"tools/backfill_prices.py --period max --symbols ^GSPC,^VIX\n{LINE}")
        return 1
    group_a(tables, again)
    group_b(tables)
    group_c(tables)
    group_d(tables)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
