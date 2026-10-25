"""
Remove the smoke test's synthetic rows from the live store (b51, 21 Oct 2026) --
ONE OF THE OPERATOR'S TWO CHOICES, built so it can be run; nothing runs it but the operator.

    python -m altdata.purge_synthetic --dry-run
    python -m altdata.purge_synthetic --apply --backup ~/backups/chester-pre-purge-synthetic.db

WHAT HAPPENED. Until 5.2 (26d020e, 23 Sep 2026) smoke_test.py pointed the CSV
store at a temporary directory (ALTDATA_STORE) and wrote the Monthly's 59 FRED
series into it with source "synthetic". altdata/store.Store.write_observations'
DUAL WRITE then mirrored each one into the observation store under
"<source>.<key>" -- and it opened the DEFAULT database, not a temporary one. So
every run of the smoke test on the box wrote synthetic.<key> rows into the live
chester.db. The box's store check of 20 Oct 2026 counted them: 28,980 rows under
59 keys, source 'synthetic'. 5.2 moved the smoke test onto a temporary
ObservationStore, so no new row has been written since.

NOTHING READS THEM. No module names a synthetic.* key: the registry declares
none, every report reads registered keys, and tools/validate_b51_registry_html.py
holds the repository's source to that. They cost space and a line in the store
check, nothing else.

SCOPE: rows whose registry_key starts "synthetic." AND whose source is
"synthetic" -- both, so no other row can be in scope.

SAFETY, as altdata/compact_fred.py's:
  * --dry-run (the default) changes nothing and prints the rows per key that
    would go.
  * --apply refuses unless --backup names a NEW path, which THIS RUN fills with an
    online-backup snapshot of the live database and integrity-checks before a
    single row is deleted. There is no flag to skip it.
  * It refuses to start the backup when the disk's free space is under the
    database's size.
  * The delete is one transaction, through observations.maintenance(), the store's
    one audited exception to its append-only triggers; the lift is logged.
  * After the delete it counts again: zero rows in scope, or it says so.

Exit codes: 0 done (or the dry run printed); 2 refused (no backup, the backup
exists, the backup failed its check, no database); 3 not enough free disk.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Optional

from . import observations

PREFIX = "synthetic."
SOURCE = "synthetic"
SCOPE_SQL = ("registry_key >= ? AND registry_key < ? AND source = ?")
SCOPE_ARGS = (PREFIX, PREFIX[:-1] + "/", SOURCE)    # "/" sorts right after "."


def in_scope(conn) -> dict[str, int]:
    """{key: rows} in scope."""
    return {k: n for k, n in conn.execute(
        f"SELECT registry_key, COUNT(*) FROM observations WHERE {SCOPE_SQL} "
        f"GROUP BY registry_key ORDER BY registry_key", SCOPE_ARGS)}


def free_bytes(path: Path) -> int:
    return shutil.disk_usage(str(Path(path).resolve().parent)).free


def run(db_path: Optional[str] = None, apply: bool = False,
        backup: Optional[str] = None, out=print) -> int:
    src = Path(db_path or observations.DEFAULT_DB)
    if not src.is_file():
        out(f"no database at {src}")
        return 2
    size = src.stat().st_size
    if apply:
        if not backup:
            out("REFUSED: --apply needs --backup PATH; this run makes that backup "
                "and integrity-checks it before deleting anything")
            return 2
        dest = Path(backup).expanduser()
        if dest.exists():
            out(f"REFUSED: {dest} exists; the backup must be made by this run")
            return 2
        if free_bytes(dest.parent if dest.parent.exists() else src) < size:
            out(f"REFUSED: under {size:,} bytes free for the backup")
            return 3
        dest.parent.mkdir(parents=True, exist_ok=True)
        observations.snapshot_sqlite(src, dest)
        problems = observations.integrity_check(dest)
        if problems:
            out(f"REFUSED: the backup at {dest} failed PRAGMA integrity_check: "
                f"{problems[:3]}")
            return 2
        out(f"backup ok: {dest} ({dest.stat().st_size:,} bytes, integrity_check ok)")
    with observations.ObservationStore(str(src)) as db:
        counts = in_scope(db.conn)
        rows = sum(counts.values())
        total = db.conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        out(f"{'apply' if apply else 'dry run'}: {rows:,} synthetic rows of "
            f"{total:,}, in {len(counts)} keys (registry_key {PREFIX}*, source "
            f"{SOURCE!r})")
        for k, n in counts.items():
            out(f"  {k:48} {n:>9,}")
        if not apply:
            out("dry run: nothing deleted")
            return 0
        with observations.maintenance(db.conn, "purge_synthetic"):
            db.conn.execute(f"DELETE FROM observations WHERE {SCOPE_SQL}", SCOPE_ARGS)
        after = db.conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        left = sum(in_scope(db.conn).values())
        out(f"deleted {total - after:,} rows ({after:,} remain; {left} in scope)")
        if left:
            out("NOT CLEAN: rows remain in scope")
            return 2
    return 0


def _main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m altdata.purge_synthetic",
                                 description="Remove the smoke test's synthetic rows")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", default=True)
    g.add_argument("--apply", action="store_true")
    ap.add_argument("--backup", help="a NEW path this run fills and checks first")
    ap.add_argument("--db", help="the database (default: the observation store)")
    a = ap.parse_args(argv)
    return run(a.db, apply=a.apply, backup=a.backup)


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
