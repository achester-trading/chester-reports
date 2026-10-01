"""
DATA GATE: the Weekly Tactical's replay over the objects stored on this box.

Split out of tools/validate_weekly.py on 1 Oct 2026, under the rule that a code
gate never reads the live store. The code gate replays the test week against an
EMPTY temporary store, which proves the absence paths are deterministic; this
one replays it against the box's REAL market-state objects, grades and register,
which is the replay that makes "read the object, never recompute" checkable.

Both builds are pinned to the same cutoff, the Sunday-morning instant that
edition's timer fires at, so the comparison is of one instant. In a checkout
with no store (CI) it reports NOT VALIDATED and exits 1; like every data gate it
runs in `make data-gates` and does not set `make validate`'s exit code.

    python tools/validate_weekly_store.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import regime                                                  # noqa: E402
from altdata import observations                               # noqa: E402
from daily_cascade import weekly_payload as wp                 # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GATE_KIND = "data"

# The same week and cutoff as the code gate, so the two answer about one edition.
TEST_WEEK = "2026-09-18"
REPLAY_CUTOFF = "2026-09-20T09:00:00+00:00"
STAMPS = ("generated_at", "as_of", "run_id")
LINE = "=" * 78
PASS = 0
FAIL = 0


def check(c: bool, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def strip(d):
    if isinstance(d, dict):
        return {k: strip(v) for k, v in d.items() if k not in STAMPS}
    if isinstance(d, list):
        return [strip(v) for v in d]
    return d


def dump(d: dict) -> str:
    return json.dumps(strip(d), sort_keys=True, default=str)


def main() -> int:
    print(f"{LINE}\nWeekly Tactical replay over this box's store (data gate)\n{LINE}")
    with observations.ObservationStore() as st:
        n = len(list(st.as_of(regime.STORE_KEY, as_of=REPLAY_CUTOFF)))
        path = st.path
    if not n:
        print(f"  SKIPPED -- the store at {path} holds no {regime.STORE_KEY} "
              f"objects knowable at {REPLAY_CUTOFF}\n\nNOT VALIDATED (no data). "
              f"This gate runs on the box.")
        return 1
    a = wp.build(TEST_WEEK, as_of=REPLAY_CUTOFF, fetch=False)
    b = wp.build(TEST_WEEK, as_of=REPLAY_CUTOFF, fetch=False)
    check(dump(a) == dump(b),
          f"two builds of the week ending {TEST_WEEK} at {REPLAY_CUTOFF} agree "
          f"byte for byte ({len(dump(a)):,} chars, over {n} stored objects)")
    wis = a.get("week_in_state") or {}
    check(wis.get("state") not in (None, "absent", "not_yet_sourced"),
          f"and the week-in-state block was built from stored objects "
          f"(state {wis.get('state')!r}), so this replay read real history")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
