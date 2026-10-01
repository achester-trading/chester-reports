"""
DATA GATE: the base-rate tables computed from this box's real ^GSPC and ^VIX.

Split out of tools/validate_base_rates.py on 1 Oct 2026, under the rule that a
code gate never reads the live store. The code gate computes from a seeded
synthetic history, which proves everything that holds on any history. What is
left is about the REAL one, and its verdict moves when the store does:

  B  THE PAPER'S HEADLINE FIGURES, printed BESIDE the computed ones whether they
     pass or fail; a figure outside its declared tolerance fails.
  E  THE BEAR COUNT IS ONE NUMBER: the claims warning's "N bear markets is a
     sample of N" is the computed count, in words.
  and the code gate's D, E and F structure, re-run on the real tables.

In a checkout with no ^GSPC (CI) this gate reports NOT VALIDATED and exits 1;
like every data gate it runs in `make data-gates` and does not set
`make validate`'s exit code.

    python tools/validate_base_rates_store.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import validate_base_rates as vbr                              # noqa: E402
from altdata import observations                               # noqa: E402
from tools import base_rates as br                             # noqa: E402

GATE_KIND = "data"


def main() -> int:
    L = vbr.LINE
    print(f"{L}\nbase_rates.py -- the tables from this box's store (data gate)\n{L}")
    db = observations.ObservationStore()
    try:
        tables = br.compute(store=db)
    finally:
        db.close()
    absent = [k for k in br.TABLE_KEYS if tables[k].get("state") == "absent"]
    if absent:
        print(f"\n  SKIPPED -- {len(absent)} table(s) have no input data in this "
              f"store:\n    {tables[absent[0]].get('absent_reason')}")
        print(f"\n{L}\nNOT VALIDATED (no data). Run "
              f"tools/backfill_prices.py --period max --symbols ^GSPC,^VIX\n{L}")
        return 1
    vbr.group_b(tables)
    vbr.group_d(tables)
    vbr.group_e(tables, live=True)
    vbr.group_f(tables)
    print(f"\n{L}\n{vbr.PASS} passed, {vbr.FAIL} failed\n{L}")
    print("VALIDATION PASSED" if vbr.FAIL == 0 else "VALIDATION FAILED")
    return 1 if vbr.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
