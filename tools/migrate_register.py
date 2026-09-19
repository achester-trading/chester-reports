"""
Move the decision register between machines, preserving ids, timestamps and
supersession chains exactly.

-----------------------------------------------------------------------------
WHY THE REGISTER MOVES TO THE BOX
-----------------------------------------------------------------------------
It was on the laptop and Portfolio Truth was on the VPS, and a register that
cannot see the positions it is about is a register that cannot check itself. Two
concrete failures came out of that split on 19 September: the close report's new
decision and invalidation columns were structurally empty on the box, and a
decision recorded for a position that demonstrably existed landed DECISION_BLOCKED
because the machine holding the register could not see the observation that proved
it. Neither is a bug in the code. Both are the split.

So there is one store, on the box, beside the thing it describes.

-----------------------------------------------------------------------------
WHAT "PRESERVING EXACTLY" HAS TO MEAN
-----------------------------------------------------------------------------
Not "the same decisions arrive". Every column, byte for byte -- ids, created_at,
decision_time, run_id, the packets and their hashes -- because the packet's whole
claim is that the decision REPLAYS from it, and a re-derived id or a re-stamped
clock would quietly destroy that claim while looking like a successful migration.
The verification is therefore not a row count: it is that every packet still
replays exactly on the target, which is a statement about content that no amount
of careful copying can fake.

-----------------------------------------------------------------------------
THE ORDER IS FORCED BY THE SCHEMA, AND THAT IS A FEATURE
-----------------------------------------------------------------------------
Two constraints shape the insert:

  FOREIGN KEYS. `superseded_by` points at another decision and
  `decision_packets.decision_id` points at one, so a naive insert in any order
  fails half the time.

  THE FREEZE TRIGGER. `decisions_superseded_frozen` aborts any UPDATE to a row
  whose superseded_by is already set. A superseded row can therefore be pointed
  exactly once, ever.

So: insert every decision with superseded_by NULL, insert the packets, then set
the pointers in one pass. That is the same sequence `Register.supersede()` uses at
write time, which means the migration walks the chain the way the chain was
built rather than around it -- and the freeze trigger stays armed throughout
instead of being disabled for the copy.

    python tools/migrate_register.py export --out register-export.json
    python tools/migrate_register.py import --in register-export.json
    python tools/migrate_register.py verify --against register-export.json
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from register import store as reg_store             # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78

# Tables that carry history and must move. restricted_instruments is deliberately
# NOT here: Register() rebuilds it from config/tracked_entities.yaml on every
# construction, so copying it would move a cache and risk it arriving stale.
TABLES = ("decisions", "decision_packets", "blocked_attempts")


def _dump(conn, table: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(f"SELECT * FROM {table}")]
    except sqlite3.OperationalError:
        return []


def export(db: str | None) -> dict:
    """Every row of every history table, with its columns as stored."""
    conn = sqlite3.connect(db or reg_store.DEFAULT_DB)
    try:
        out = {"source_db": str(db or reg_store.DEFAULT_DB),
               "tables": {t: _dump(conn, t) for t in TABLES}}
        out["counts"] = {t: len(rows) for t, rows in out["tables"].items()}
        return out
    finally:
        conn.close()


def do_import(payload: dict, db: str | None, *, force: bool = False) -> dict:
    """Insert into a register the schema of which already exists.

    Register() is constructed first and NOT bypassed: it creates the schema, runs
    the ALTER migrations for columns added since, arms the triggers and syncs the
    restriction table from the YAML. Importing into a hand-made schema would be
    the one way to end up with a register missing a constraint it is supposed to
    have.
    """
    reg = reg_store.Register(db)                     # schema, triggers, blocklist
    conn = reg.conn
    conn.row_factory = sqlite3.Row

    existing = {r["id"] for r in conn.execute("SELECT id FROM decisions")}
    if existing and not force:
        return {"ok": False,
                "error": f"the target register already holds {len(existing)} "
                         f"decision(s); refusing to merge. Use --force only if "
                         f"you have checked the ids do not collide."}

    decisions = payload["tables"].get("decisions") or []
    packets = payload["tables"].get("decision_packets") or []
    blocked = payload["tables"].get("blocked_attempts") or []

    # Only columns the target actually has. A source row from a newer schema
    # would otherwise fail the insert with a message about SQL rather than about
    # the schema drift that caused it -- so drift is reported by name instead.
    def cols_of(table):
        return [r["name"] for r in conn.execute(f"PRAGMA table_info({table})")]

    dcols, pcols, bcols = cols_of("decisions"), cols_of("decision_packets"), \
        cols_of("blocked_attempts")
    dropped = sorted({k for r in decisions for k in r} - set(dcols))

    inserted = {"decisions": 0, "decision_packets": 0, "blocked_attempts": 0}
    pointers: list[tuple[str, str]] = []

    with conn:
        # 1. decisions, with superseded_by held back. In created_at order so the
        #    chain is rebuilt the way it was written.
        for row in sorted(decisions, key=lambda r: r.get("created_at") or ""):
            if row.get("superseded_by"):
                pointers.append((row["superseded_by"], row["id"]))
            vals = {k: row.get(k) for k in dcols}
            vals["superseded_by"] = None
            conn.execute(
                f"INSERT INTO decisions ({','.join(dcols)}) "
                f"VALUES ({','.join('?' * len(dcols))})",
                [vals[k] for k in dcols])
            inserted["decisions"] += 1

        # 2. packets, which need their decision to exist.
        for row in packets:
            vals = [row.get(k) for k in pcols]
            conn.execute(
                f"INSERT INTO decision_packets ({','.join(pcols)}) "
                f"VALUES ({','.join('?' * len(pcols))})", vals)
            inserted["decision_packets"] += 1

        for row in blocked:
            keys = [k for k in bcols if k != "id"]
            conn.execute(
                f"INSERT INTO blocked_attempts ({','.join(keys)}) "
                f"VALUES ({','.join('?' * len(keys))})",
                [row.get(k) for k in keys])
            inserted["blocked_attempts"] += 1

        # 3. the pointers, exactly once each, with the freeze trigger armed.
        for target, owner in pointers:
            conn.execute("UPDATE decisions SET superseded_by = ? WHERE id = ?",
                         (target, owner))

    reg.close()
    return {"ok": True, "inserted": inserted, "pointers": len(pointers),
            "dropped_columns": dropped}


def verify(payload: dict, db: str | None) -> dict:
    """Every exported row must be present and byte-identical on the target."""
    conn = sqlite3.connect(db or reg_store.DEFAULT_DB)
    conn.row_factory = sqlite3.Row
    problems: list[str] = []
    checked = 0
    try:
        for table in ("decisions", "decision_packets"):
            src = payload["tables"].get(table) or []
            key = "id" if table == "decisions" else "packet_id"
            for row in src:
                got = conn.execute(
                    f"SELECT * FROM {table} WHERE {key} = ?", (row[key],)).fetchone()
                if got is None:
                    problems.append(f"{table}: {row[key]} is MISSING on the target")
                    continue
                got = dict(got)
                for col, want in row.items():
                    if col not in got:
                        continue          # column absent on the target schema
                    if got[col] != want:
                        problems.append(
                            f"{table}: {row[key]} column {col!r} differs "
                            f"(source {want!r} -> target {got[col]!r})")
                checked += 1
        extra = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] \
            - len(payload["tables"].get("decisions") or [])
        if extra:
            problems.append(f"decisions: the target holds {extra} row(s) the "
                            f"export does not")
    finally:
        conn.close()
    return {"ok": not problems, "rows_checked": checked, "problems": problems}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=("export", "import", "verify"))
    ap.add_argument("--db", default=None)
    ap.add_argument("--out", default="register-export.json")
    ap.add_argument("--in", dest="infile", default="register-export.json")
    ap.add_argument("--against", default=None)
    ap.add_argument("--force", action="store_true",
                    help="import into a register that is not empty")
    args = ap.parse_args()

    print(f"{LINE}\nRegister migration -- {args.mode}\n{LINE}")

    if args.mode == "export":
        data = export(args.db)
        Path(args.out).write_text(json.dumps(data, indent=2, sort_keys=True,
                                             default=str), encoding="utf-8")
        print(f"  from   : {data['source_db']}")
        for t, n in data["counts"].items():
            print(f"  {t:18} {n} row(s)")
        print(f"  written: {args.out}")
        return 0

    payload = json.loads(Path(args.infile if args.mode == "import"
                              else (args.against or args.infile))
                         .read_text(encoding="utf-8"))

    if args.mode == "import":
        res = do_import(payload, args.db, force=args.force)
        if not res["ok"]:
            print(f"  REFUSED: {res['error']}")
            return 1
        for t, n in res["inserted"].items():
            print(f"  {t:18} {n} row(s) inserted")
        print(f"  supersession       {res['pointers']} pointer(s) set")
        if res["dropped_columns"]:
            print(f"  WARNING columns present in the export but not on the "
                  f"target schema: {res['dropped_columns']}")
        print(f"\n  Now run:  python tools/migrate_register.py verify "
              f"--against {args.infile}")
        return 0

    res = verify(payload, args.db)
    print(f"  rows checked: {res['rows_checked']}")
    if res["ok"]:
        print(f"\n  VERIFIED -- every exported row is present and every column "
              f"identical.")
        return 0
    print(f"\n  PROBLEMS ({len(res['problems'])}):")
    for p in res["problems"][:20]:
        print(f"    {p}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
