"""
DATA GATE: the market-state objects actually stored on this box.

Split out of tools/validate_regime.py on 1 Oct 2026, under the rule that a code
gate never reads the live store. These three checks ask about the box's own
history, not about the commit, so their verdict moves when the store does:

  A  EXACT REPLAY OF THE REAL OBJECTS, scoped by both versions. A stored object,
     recomputed at its own cutoff and its own compute instant, must equal the
     stored version field for field -- but only objects computed under the
     current config_version AND method_version are compared, because a
     deliberate change to the rules or to the code is not a regression. A store
     where every object is superseded is a store whose history no longer matches
     its own rules, and that fails.
  D  `contradicting` IS NEVER EMPTY BY OMISSION on any stored object.
  J  NO STORED OBJECT under the current method names an exception class in a
     reason -- a fault printed as an absence.

The same arithmetic on a seeded store, and the source-hash pin, stay in the
code gate. In a checkout with no store (CI) this gate reports NOT VALIDATED and
exits 1; like every data gate it runs in `make data-gates` and does not set
`make validate`'s exit code.

    python tools/validate_regime_store.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import regime                            # noqa: E402
from altdata import observations         # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GATE_KIND = "data"

PASS = 0
FAIL = 0
LINE = "=" * 78


def check(c: bool, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def group_a(store, all_rows: list) -> None:
    print(f"{LINE}\nA. EXACT REPLAY OF THE STORED OBJECTS\n{LINE}")
    current = (regime.load_config() or {}).get("version")
    current_method = regime.METHOD_VERSION
    rows = [r for r in all_rows
            if (json.loads(r["value_text"]).get("config_version") == current
                and json.loads(r["value_text"]).get("method_version")
                == current_method)]
    superseded = len(all_rows) - len(rows)
    if superseded:
        print(f"        {superseded} object(s) were computed under an earlier "
              f"config or method version and are not replayed against "
              f"{current}/{current_method}; re-run `regime backfill` to bring "
              f"them forward")
    check(bool(rows),
          f"{len(rows)} of {len(all_rows)} objects were computed under the current "
          f"config {current!r} AND method {current_method!r}, so there is "
          f"something to replay")
    check(all(json.loads(r["value_text"]).get("method_version") for r in all_rows),
          "every stored object records a method_version at all -- an object that "
          "does not cannot be told from one computed under any other method")
    # The newest and the oldest: the oldest has no history, the newest has
    # predecessors, and persistence is the part most likely to replay differently.
    for label, row in (("newest", rows[-1:]), ("oldest", rows[:1])):
        if not row:
            continue
        stored = json.loads(row[0]["value_text"])
        again = regime.compute(as_of=stored["as_of"],
                               session_day=stored["session"],
                               computed_at=stored["computed_at"], store=store)
        a, b = regime.replay_fields(stored), regime.replay_fields(again)
        diffs = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
        check(a == b, f"the {label} object ({stored['session']}) replays EXACTLY "
                      f"from the store"
                      + (f"; fields differing: {diffs}" if diffs else ""))


def group_d(all_rows: list) -> None:
    print(f"\n{LINE}\nD. `contradicting` IS NEVER EMPTY BY OMISSION\n{LINE}")
    bad_rows, stated, with_list = [], 0, 0
    for r in all_rows:
        obj = json.loads(r["value_text"])
        for name, d in (obj.get("dimensions") or {}).items():
            if d.get("state") is None:
                continue
            c = d.get("contradicting")
            if c == [] or c is None:
                bad_rows.append((obj["session"], name))
            elif c == regime.NONE_FOUND:
                stated += 1
            else:
                with_list += 1
    check(not bad_rows,
          f"across {len(all_rows)} stored objects, no dimension with a state has "
          f"an empty or missing `contradicting` "
          f"({stated} say 'none found', {with_list} name metrics)"
          + (f" -- offenders: {bad_rows[:5]}" if bad_rows else ""))
    check(stated + with_list > 0,
          "and there were dimensions with states to check, so this is not "
          "vacuously true")


def group_j(all_rows: list) -> None:
    print(f"\n{LINE}\nJ. NO STORED REASON NAMES AN EXCEPTION\n{LINE}")
    import validate_regime as vr             # noqa: PLC0415 -- the one detector
    cur = regime.METHOD_VERSION
    objs = [json.loads(r["value_text"]) for r in all_rows]
    objs = [o for o in objs if o.get("method_version") == cur]
    hits = [(o.get("session"), h) for o in objs
            for h in vr.exception_names_in_reasons(o)]
    check(not hits,
          f"no stored {cur} object ({len(objs)}) names an exception class in a "
          f"reason" + (f": {hits[:3]}" if hits else ""))


def main() -> int:
    print(f"{LINE}\nThe market-state objects on this box (data gate)\n{LINE}")
    sys.path.insert(0, str(REPO / "tools"))
    store = observations.ObservationStore()
    try:
        all_rows = list(store.as_of(regime.STORE_KEY))
        if not all_rows:
            print(f"  SKIPPED -- the store at {store.path} holds no "
                  f"{regime.STORE_KEY} objects\n\nNOT VALIDATED (no data). This "
                  f"gate runs on the box, where the 16:45 close writes them.")
            return 1
        group_a(store, all_rows)
        group_d(all_rows)
        group_j(all_rows)
    finally:
        store.close()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    # In CI: "skipped: box-only", exit 0 (tools/box_only.py). Elsewhere: the gate.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from box_only import ci_skip  # noqa: E402
    _skip = ci_skip(__file__)
    sys.exit(main() if _skip is None else _skip)
