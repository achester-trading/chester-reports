"""
Add the 6f tranche 4 columns to the live decision register (ruling 9a of 24 Oct
2026) -- THE OPERATOR'S, from the box sheet. Nothing runs it but the operator.

    python tools/migrate_alignment_weekly.py --dry-run
    python tools/migrate_alignment_weekly.py --apply --backup ~/backups/chester-pre-alignment-weekly.db

WHAT IT ADDS. Two nullable columns on `decisions` (register/store.py's
ALIGNMENT_WEEKLY_COLUMNS): alignment_weekly (aligned / neutral / counter, the
packet's direction against the object's weekly per-horizon trend read, stamped at
entry by tools/decide.py) and alignment_weekly_basis (why, and why it is absent
when it is). The register does NOT add them when it opens -- unlike the earlier
nullable columns -- so the schema changes only here, once, when the operator
says.

IT BACKFILLS NOTHING. A stamp is what was knowable at entry; computing one now
for an old row would be today's object restating a past decision. Every existing
row stays NULL and reads "entered before 6f" (register.store.PRE_6F).

SAFETY, as altdata/purge_synthetic.py's:
  * --dry-run (the default) changes nothing and prints what would be added and
    how many rows would read "entered before 6f".
  * --apply refuses unless --backup names a NEW path, which THIS RUN fills with an
    online-backup snapshot of the database and integrity-checks before the schema
    is touched. There is no flag to skip it.
  * It refuses to start the backup when the disk's free space is under the
    database's size.
  * Both ALTERs are one transaction: both columns or neither.
  * It is logged: one line to migrations.log beside the database.
  * Run twice, it finds the columns present and changes nothing.

Exit codes: 0 done (or the dry run printed, or already migrated); 2 refused (no
backup, the backup exists, the backup failed its check, no database, no
decisions table); 3 not enough free disk.
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import observations, session  # noqa: E402
from register import store as reg_store  # noqa: E402

LOG_NAME = "migrations.log"


def columns(conn) -> list[str]:
    return [r[1] for r in conn.execute("PRAGMA table_info(decisions)")]


def missing(conn) -> list[str]:
    have = set(columns(conn))
    return [c for c in reg_store.ALIGNMENT_WEEKLY_COLUMNS if c.split()[0] not in have]


def snapshot(src: Path, dest: Path) -> int:
    """An online-backup copy of the register (the API observations.snapshot_sqlite
    uses; that one counts observations, which a register-only file need not hold).
    Returns the decisions the copy holds."""
    conn = sqlite3.connect(f"file:{src.as_posix()}?mode=ro", uri=True)
    try:
        out = sqlite3.connect(str(dest))
        try:
            conn.backup(out)
            return out.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        finally:
            out.close()
    finally:
        conn.close()


def free_bytes(path: Path) -> int:
    return shutil.disk_usage(str(Path(path).resolve().parent)).free


def run(db_path: Optional[str] = None, apply: bool = False,
        backup: Optional[str] = None, out=print) -> int:
    src = Path(db_path or reg_store.DEFAULT_DB)
    if not src.is_file():
        out(f"no database at {src}")
        return 2
    conn = sqlite3.connect(str(src), isolation_level=None)
    try:
        if not columns(conn):
            out(f"REFUSED: {src} has no decisions table")
            return 2
        todo = missing(conn)
        rows = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        out(f"{'apply' if apply else 'dry run'}: {src}")
        out(f"  decisions: {rows:,} rows, {len(columns(conn))} columns")
        if not todo:
            out("  alignment_weekly and alignment_weekly_basis are present: nothing to do")
            return 0
        for c in todo:
            out(f"  would add: {c} (nullable)")
        out(f"  backfill: none; {rows:,} existing rows read {reg_store.PRE_6F!r}")
        if not apply:
            out("dry run: nothing changed")
            return 0
        if not backup:
            out("REFUSED: --apply needs --backup PATH; this run makes that backup "
                "and integrity-checks it before changing the schema")
            return 2
        dest = Path(backup).expanduser()
        if dest.exists():
            out(f"REFUSED: {dest} exists; the backup must be made by this run")
            return 2
        size = src.stat().st_size
        if free_bytes(dest.parent if dest.parent.exists() else src) < size:
            out(f"REFUSED: under {size:,} bytes free for the backup")
            return 3
        dest.parent.mkdir(parents=True, exist_ok=True)
        copied = snapshot(src, dest)
        problems = observations.integrity_check(dest)
        if problems:
            out(f"REFUSED: the backup at {dest} failed PRAGMA integrity_check: "
                f"{problems[:3]}")
            return 2
        if copied != rows:
            out(f"REFUSED: the backup holds {copied:,} decisions, the register {rows:,}")
            return 2
        out(f"backup ok: {dest} ({dest.stat().st_size:,} bytes, {copied:,} decisions, "
            f"integrity_check ok)")
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("BEGIN IMMEDIATE")
        try:
            for c in todo:
                conn.execute(f"ALTER TABLE decisions ADD COLUMN {c}")
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        left = missing(conn)
        line = (f"{session.utc_iso()} migrate_alignment_weekly {src}: added "
                f"{', '.join(c.split()[0] for c in todo)}; {rows} rows left NULL "
                f"({reg_store.PRE_6F}); backup {dest}")
        with open(src.parent / LOG_NAME, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        out(f"added {len(todo)} columns in one transaction; logged to "
            f"{src.parent / LOG_NAME}")
        if left:
            out(f"NOT CLEAN: still missing {left}")
            return 2
        return 0
    finally:
        conn.close()


def _main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python tools/migrate_alignment_weekly.py",
                                 description="Add the alignment_weekly columns")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", default=True)
    g.add_argument("--apply", action="store_true")
    ap.add_argument("--backup", help="a NEW path this run fills and checks first")
    ap.add_argument("--db", help="the register (default: register.store.DEFAULT_DB)")
    a = ap.parse_args(argv)
    return run(a.db, apply=a.apply, backup=a.backup)


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
