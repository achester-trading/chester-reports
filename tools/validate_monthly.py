#!/usr/bin/env python3
"""
Validation gate for the Monthly. (Phase 4b; Audit #3 section G, N, O 7/8/10)

    python tools/validate_monthly.py

Group A is the phase's first ruling: the pillars are SUBORDINATE to the dials, with
a stated mapping, and no pillar computes a regime of its own. The rest of the groups
land with the report's other pieces.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from monthly_macro import pillars                              # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78
PASS = 0
FAIL = 0
SKIPPED: list[str] = []

# The object's eight dimensions. A pillar may only claim to read one of these.
DIMENSIONS = ("growth", "inflation", "rates", "liquidity", "credit", "trend",
              "breadth", "volatility")


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


def group_a() -> None:
    print(f"\n{LINE}\nA. PILLARS SUBORDINATE TO THE DIALS, WITH A MAPPING\n{LINE}")
    reg = pillars.load()
    ps = reg["pillars"]
    print(f"  {len(ps)} pillars, version {reg['version']}")

    check(len(ps) == 11,
          f"eleven pillars are declared (got {len(ps)}) -- the number the "
          f"architecture names, including the one that was relocated")
    check(set(ps) == {str(i) for i in range(1, 12)},
          f"numbered 1 to 11 with no gaps ({sorted(ps, key=int)})")

    # --- EVERY PILLAR MAPPED --------------------------------------------------
    for num, p in sorted(ps.items(), key=lambda kv: int(kv[0])):
        dial = p.get("dial")
        if dial is None:
            check(bool(p.get("from_object_absent_reason")),
                  f"pillar {num} ({p.get('name')}) feeds no dial AND says why "
                  f"({str(p.get('from_object_absent_reason'))[:52]}...)")
        else:
            check(dial in pillars.DIALS,
                  f"pillar {num} feeds a declared dial ({dial})")
        check(p.get("weight") is not None,
              f"pillar {num} declares a weight ({p.get('weight')})")
        check(bool(p.get("name")), f"pillar {num} is named")
        dim = p.get("from_object")
        if dim is None:
            check(bool(p.get("from_object_absent_reason")),
                  f"pillar {num} reads no dimension AND records the reason")
        else:
            check(dim in DIMENSIONS,
                  f"pillar {num} reads the object's `{dim}` dimension")

    # --- WEIGHTS SUM, PER DIAL ------------------------------------------------
    for dial in ("macro", "vol"):
        total = pillars.weight_total(dial)
        check(abs(total - 1.0) < 1e-9,
              f"the {dial} dial's pillar weights sum to 1.0 (got {total})")
    check(pillars.weight_total("gamma") == 0
          and not pillars.for_dial("gamma"),
          "THE GAMMA DIAL HAS NO PILLAR INPUTS, and the mapping says so rather "
          "than leaving a row that looks forgotten: gamma is dealer positioning "
          "from the chain, and no macro series bears on it")

    # --- NO PILLAR COMPUTES A REGIME OF ITS OWN -------------------------------
    src = (REPO / "config" / "pillars.yaml").read_text(encoding="utf-8")
    stateful = [num for num, p in ps.items()
                if any(k in p for k in ("state", "score", "reading", "verdict"))]
    check(not stateful,
          f"no pillar declares a state, a score or a verdict"
          + (f" -- {stateful}" if stateful else "")
          + ": a pillar is an input, and regime.py is the only writer of a state")
    check("NO PILLAR COMPUTES A REGIME OF ITS OWN" in src,
          "and the file says so in the one place a reader would look")
    reader = (REPO / "monthly_macro" / "pillars.py").read_text(encoding="utf-8")
    for banned in ("def compute", "def score", "def state_of"):
        check(banned not in reader,
              f"the reader offers no {banned!r} -- it maps and reads, and computing "
              f"a pillar state here is the defect the mapping exists to remove")

    # --- THE GAPS ARE DECLARED, NOT SILENT ------------------------------------
    gaps = pillars.unsourced()
    check(len(gaps) >= 3,
          f"{len(gaps)} pillar gaps are declared with what each needs")
    for g in gaps:
        check(bool(g.get("needs")) and bool(g.get("why")),
              f"pillar {g['pillar']}'s gap names its inputs and why it matters "
              f"({g['what']})")
    zero = [n for n, p in ps.items()
            if float(p.get("weight") or 0) == 0 and p.get("dial")]
    check(zero,
          f"a pillar with no metrics carries weight ZERO rather than being deleted "
          f"({zero}) -- zero is the honest weight for a pillar that cannot move a "
          f"view, and the row stays visible")
    check(pillars.load()["pillars"]["11"].get("status") == "relocated"
          and pillars.load()["pillars"]["11"].get("relocated_to"),
          "and the eleventh pillar resolves to where it went rather than to "
          "nothing")


def main() -> int:
    print(f"{LINE}\nThe Monthly -- Phase 4b\n{LINE}")
    group_a()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed"
          + (f", {len(SKIPPED)} skipped" if SKIPPED else "") + f"\n{LINE}")
    for s in SKIPPED:
        print(f"  SKIPPED: {s}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
