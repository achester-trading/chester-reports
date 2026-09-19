"""
Retire this machine's local decision register after it has moved to the box.

    python tools/retire_local_register.py --check     # what would happen
    python tools/retire_local_register.py --apply

-----------------------------------------------------------------------------
RENAMING THE TABLE IS NOT ENOUGH, AND THE NAIVE VERSION IS WORSE THAN NOTHING
-----------------------------------------------------------------------------
The obvious move is `ALTER TABLE decisions RENAME TO decisions_migrated_...`, so
that nothing writes to the old rows. It does achieve that, and it creates two
problems that are strictly worse than the one it solves:

  A FRESH, EMPTY `decisions` APPEARS ON THE NEXT CONSTRUCTION. Register() runs
  `CREATE TABLE IF NOT EXISTS decisions`, finds no such table, and makes one.
  Writes then succeed silently into an empty local register -- which is a NEW
  fork of exactly the kind the consolidation existed to end, and this time with
  no history in it to make the mistake obvious.

  THAT NEW TABLE HAS NO BROOKFIELD TRIGGER. The compliance triggers are created
  `IF NOT EXISTS` and their NAMES survive the rename, still attached to the
  renamed table. So the schema script skips them, and the fresh `decisions`
  table is the one object in this system that can accept a restricted
  instrument. A retirement step that quietly disarms the compliance invariant is
  not an acceptable retirement step.

-----------------------------------------------------------------------------
SO THE NAME IS TAKEN, BY A VIEW THAT REFUSES WRITES AND SAYS WHERE TO GO
-----------------------------------------------------------------------------
After the rename, a VIEW called `decisions` takes the name. Three consequences,
all of them wanted:

  `CREATE TABLE IF NOT EXISTS decisions` is a no-op, because the name is taken.
  No empty table can appear, so no silent fork and no un-triggered table.

  READS STILL WORK. The history is queryable here -- `decide.py list`, an
  ad-hoc join, anything that only looks. Retiring the register should not mean
  losing the ability to read what it recorded.

  WRITES ABORT WITH AN INSTRUCTION. SQLite refuses to modify a view, but its
  own message ("cannot modify decisions because it is a view") explains the
  mechanism and not the situation. An INSTEAD OF trigger replaces it with one
  that names the box and the script to use, because the person who hits this
  will be mid-decision and needs the next step, not a lesson in SQLite.

The rows are not deleted, ever. They are the grading trail for four decisions and
the source the box's copy was verified against.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from register import store as reg_store             # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78
SUFFIX = "_migrated_2026_09_19"
TABLES = ("decisions", "decision_packets")

REDIRECT = (
    "this register was retired on 2026-09-19 and moved to the VPS. "
    "Write it with scripts/decide_remote.sh, which runs decide.py on the box "
    "against the one store that sits beside Portfolio Truth. "
    "The rows here are history and remain readable."
)


def objects(conn) -> dict[str, str]:
    return {r[0]: r[1] for r in conn.execute(
        "SELECT name, type FROM sqlite_master WHERE name LIKE 'decision%'")}


def plan(conn) -> tuple[list[str], list[str]]:
    """(what needs doing, what blocks it)."""
    obj = objects(conn)
    todo, blocked = [], []
    for t in TABLES:
        if obj.get(t) == "view":
            continue                                 # already retired
        if obj.get(t) != "table":
            blocked.append(f"{t}: expected a table, found {obj.get(t) or 'nothing'}")
            continue
        if t + SUFFIX in obj:
            blocked.append(f"{t}{SUFFIX} already exists; refusing to overwrite it")
            continue
        todo.append(t)
    return todo, blocked


def apply(conn, todo: list[str]) -> None:
    for t in todo:
        conn.execute(f"ALTER TABLE {t} RENAME TO {t}{SUFFIX}")
        conn.execute(f"CREATE VIEW {t} AS SELECT * FROM {t}{SUFFIX}")
        # One trigger per write verb. A view with no INSTEAD OF trigger already
        # refuses, but with SQLite's message rather than ours, and the whole
        # point is to hand the reader the next step.
        for verb in ("INSERT", "UPDATE", "DELETE"):
            conn.execute(
                f"CREATE TRIGGER {t}_retired_{verb.lower()} "
                f"INSTEAD OF {verb} ON {t} "
                f"BEGIN SELECT RAISE(ABORT, '{REDIRECT}'); END")
    conn.commit()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=None)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    db = args.db or reg_store.DEFAULT_DB
    print(f"{LINE}\nRetire the local register\n{LINE}")
    print(f"  db: {db}")
    conn = sqlite3.connect(db)
    try:
        todo, blocked = plan(conn)
        for t, kind in sorted(objects(conn).items()):
            print(f"    {kind:7} {t}")
        if blocked:
            print("\n  BLOCKED:")
            for b in blocked:
                print(f"    {b}")
            return 1
        if not todo:
            print("\n  Already retired; nothing to do.")
            return 0
        print(f"\n  Would rename and shadow: {', '.join(todo)}")
        if not args.apply:
            print("\n  --check only. Re-run with --apply to write.")
            return 0
        apply(conn, todo)
        print("\n  APPLIED.")
        for t, kind in sorted(objects(conn).items()):
            print(f"    {kind:7} {t}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
