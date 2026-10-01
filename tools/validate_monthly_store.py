"""
DATA GATE: the Monthly's payload built from this box's real store.

Split out of tools/validate_monthly.py on 1 Oct 2026, under the rule that a code
gate never reads the live store. The code gate builds from a seeded temporary
store; this one runs the same three groups over the box's real history:

  B  PAYLOAD COMPLETENESS -- every section, every absence with its reason, the
     derived macro series, print precision.
  C  EVERY SCENARIO WEIGHT BESIDE ITS BRIER, on the real ledger.
  D  A PAST MONTH REPLAYS AS-OF ITS CUTOFF over real observations: nothing after
     the cutoff reaches the payload, and two builds agree.

In a checkout with no market-state object (CI) it reports NOT VALIDATED and exits
1; like every data gate it runs in `make data-gates` and does not set
`make validate`'s exit code.

    python tools/validate_monthly_store.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import validate_monthly as vm                                   # noqa: E402

GATE_KIND = "data"


def main() -> int:
    L = vm.LINE
    print(f"{L}\nThe Monthly over this box's store (data gate)\n{L}")
    import regime                                               # noqa: PLC0415
    from altdata import observations                            # noqa: PLC0415
    from monthly_macro import payload                           # noqa: PLC0415
    with observations.ObservationStore() as st:
        n = len(list(st.as_of(regime.STORE_KEY)))
        path = st.path
    if not n:
        print(f"  SKIPPED -- the store at {path} holds no {regime.STORE_KEY} "
              f"objects\n\nNOT VALIDATED (no data). This gate runs on the box.")
        return 1
    built = payload.build()
    vm.group_b(built)
    vm.group_c(built)
    vm.group_d(live=True)
    print(f"\n{L}\n{vm.PASS} passed, {vm.FAIL} failed"
          + (f", {len(vm.SKIPPED)} skipped" if vm.SKIPPED else "") + f"\n{L}")
    for s in vm.SKIPPED:
        print(f"  SKIPPED: {s}")
    print("VALIDATION PASSED" if vm.FAIL == 0 else "VALIDATION FAILED")
    return 1 if vm.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
