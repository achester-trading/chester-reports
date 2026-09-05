"""
One-shot migration: the CSV store -> the SQLite point-in-time store.

Migration, NOT cutover. The CSV writers keep running -- altdata.store now
dual-writes -- and this backfills what the CSVs already hold so the new store
starts with history rather than from empty.

Idempotent: re-running inserts nothing new, because the vintage key already
covers every row it would write.

READ THE available_at CAVEAT BEFORE TRUSTING MIGRATED HISTORY. The CSVs carry
`as_of`, which is when the row was PULLED. That is an upper bound on when the
value became available, not the release time, and for any series revised
between its release and our pull it OVERSTATES how early we knew -- the
direction that leaks. Migrated rows are therefore tagged
source='<source>:csv_migrated' so they are distinguishable forever. Rows written
from now on carry a real available_at.

    python tools/migrate_store_to_sqlite.py
    python tools/migrate_store_to_sqlite.py --db /tmp/test.db --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from altdata import observations  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Migrate the CSV store to SQLite")
    ap.add_argument("--store-dir", default=None)
    ap.add_argument("--db", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.dry_run:
        print("dry run -- nothing written")
        return 0

    res = observations.migrate_csv_store(args.store_dir, args.db)
    print(f"files read     : {res['files']}")
    print(f"rows read      : {res['rows_read']:,}")
    print(f"rows written   : {res['rows_written']:,}  "
          f"(0 on a re-run means the migration is idempotent)")
    if res["unknown_keys"]:
        print(f"keys not in config.FRED_SERIES: {sorted(res['unknown_keys'])}")

    db = observations.ObservationStore(args.db)
    try:
        print(f"store total    : {db.count():,} observations across "
              f"{len(db.keys())} registry keys")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
