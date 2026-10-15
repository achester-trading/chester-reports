"""
Compact the FRED re-stamps (AUD-1 item 4b; the data and architecture audit of
14 Oct 2026, ruled 09:27 ET).

    python -m altdata.compact_fred --dry-run
    python -m altdata.compact_fred --apply --backup ~/backups/chester-pre-compact.db

WHAT HAPPENED. Until AUD-1 4a the FRED pull's dual write skipped drop_unchanged,
so every session re-stored five years of each series under a new available_at --
about 33,000 rows a session -- and every series DERIVED from FRED inherited the
new stamps (its availability is the latest of its inputs'). Nothing read wrong:
the as-of join returns the latest vintage, and an identical one is still the same
value. But the store grew by a copy of the history every night.

WHAT THIS DOES. For every key in SCOPE, per (key, instrument, observed_at), the
vintages in availability order: the FIRST of each run of identical values is kept
and the later identical ones are deleted. A vintage whose value differs from the
one before it is NEVER deleted -- that is a revision, and revisions are the point
of the store. So A A A B A keeps A (the first), B and the last A.

SCOPE (the keys that took the re-stamps):
  * every fred.* key;
  * the surprise module's calc.surprise_vs_naive.* and calc.naive_expectation.*
    (derived from FRED actuals);
  * the FRED-derived calc.* of altdata.market_features: MACRO_FEATURES and
    RATES_FEATURES (the price-derived FEATURES never read FRED and are left alone).

SAFETY.
  * --dry-run (the default) changes nothing and prints the rows per key that
    would go.
  * --apply refuses unless --backup names a NEW path, which THIS RUN fills with an
    online-backup snapshot of the live database and integrity-checks before a
    single row is deleted. There is no flag to skip it.
  * It refuses to start the backup when the disk's free space is under the
    database's size, and runs VACUUM afterwards only when free space exceeds
    twice the database's size (VACUUM writes a full copy); otherwise it says so,
    and the freed pages are reused in place.
  * The delete is one transaction.

Exit codes: 0 done (or the dry run printed); 2 refused (no backup, the backup
exists, the backup failed its check); 3 not enough free disk for the backup.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Optional

from . import observations

SURPRISE_PREFIXES = ("calc.surprise_vs_naive.", "calc.naive_expectation.")


def derived_keys() -> list[str]:
    """The FRED-derived calc.* keys of market_features."""
    from . import market_features as mf                          # noqa: PLC0415
    return sorted(set(mf.MACRO_FEATURES) | set(mf.RATES_FEATURES))


def scope_clause() -> tuple[str, list]:
    keys = derived_keys()
    where = ["(registry_key >= 'fred.' AND registry_key < 'fred/')"]
    args: list = []
    for p in SURPRISE_PREFIXES:
        where.append("(registry_key >= ? AND registry_key < ?)")
        args += [p, p + "￿"]
    where.append("registry_key IN (" + ",".join("?" for _ in keys) + ")")
    args += keys
    return "(" + " OR ".join(where) + ")", args


# Each vintage beside the one before it for the same period: LAG over the period,
# in availability order. A row equal to the row before it is the second (or later)
# member of a run of identical values.
REDUNDANT_SQL = """
SELECT rowid AS rid, registry_key FROM (
  SELECT rowid, registry_key, value_num, value_text,
         LAG(value_num)  OVER w AS prev_num,
         LAG(value_text) OVER w AS prev_text,
         ROW_NUMBER()    OVER w AS n
    FROM observations
   WHERE {scope}
  WINDOW w AS (PARTITION BY registry_key, COALESCE(instrument, ''), observed_at
               ORDER BY available_at, rowid))
 WHERE n > 1
   AND ((value_num IS NOT NULL AND prev_num IS NOT NULL
         AND abs(value_num - prev_num) < 1e-12)
        OR (value_num IS NULL AND prev_num IS NULL AND value_text IS prev_text))
"""


def redundant(conn) -> list[tuple[int, str]]:
    where, args = scope_clause()
    return [(r[0], r[1]) for r in
            conn.execute(REDUNDANT_SQL.format(scope=where), args).fetchall()]


def per_key(rows: list[tuple[int, str]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for _, k in rows:
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


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
        rows = redundant(db.conn)
        counts = per_key(rows)
        total = db.conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        out(f"{'apply' if apply else 'dry run'}: {len(rows):,} redundant vintages of "
            f"{total:,} rows, in {len(counts)} keys")
        for k, n in counts.items():
            out(f"  {k:48} {n:>9,}")
        if not apply:
            out("dry run: nothing deleted")
            return 0
        ids = [r[0] for r in rows]
        with db.conn:
            for i in range(0, len(ids), 5000):
                chunk = ids[i:i + 5000]
                db.conn.execute(f"DELETE FROM observations WHERE rowid IN "
                                f"({','.join('?' for _ in chunk)})", chunk)
        after = db.conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        out(f"deleted {total - after:,} rows ({after:,} remain)")
    free = free_bytes(src)
    if free > 2 * size:
        import sqlite3                                            # noqa: PLC0415
        conn = sqlite3.connect(str(src))
        try:
            conn.execute("VACUUM")
        finally:
            conn.close()
        out(f"VACUUM done ({src.stat().st_size:,} bytes now)")
    else:
        out(f"VACUUM skipped: {free:,} bytes free, under twice the database's "
            f"{size:,}; the freed pages are reused in place")
    return 0


def _main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m altdata.compact_fred",
                                 description="Compact the FRED re-stamps")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", default=True)
    g.add_argument("--apply", action="store_true")
    ap.add_argument("--backup", help="a NEW path this run fills and checks first")
    ap.add_argument("--db", help="the database (default: the observation store)")
    ap.add_argument("--list-scope", action="store_true",
                    help="print the derived keys in scope and exit")
    a = ap.parse_args(argv)
    if a.list_scope:
        print("fred.*")
        for p in SURPRISE_PREFIXES:
            print(p + "*")
        for k in derived_keys():
            print(k)
        return 0
    return run(a.db, apply=a.apply, backup=a.backup)


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
