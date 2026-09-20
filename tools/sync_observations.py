"""
Move observations between stores with the clocks preserved.

Built for one job: the FRED history lives in the laptop's store (20,372 rows) and
the box's store has none, and the box is where the 16:45 object is computed. So the
box computed eight absent dimensions while the history sat on a machine that does
not run the close pass.

    # on the laptop
    python tools/sync_observations.py export --prefix fred. --out fred.jsonl
    # on the box
    python tools/sync_observations.py import --in fred.jsonl
    # either side
    python tools/sync_observations.py count --prefix fred.

-----------------------------------------------------------------------------
WHICH CLOCKS MOVE, AND WHICH ONE DOES NOT
-----------------------------------------------------------------------------

`observed_at` and `available_at` are carried across UNCHANGED, and that is the
whole point. They are statements about the world -- which period a value describes,
and when it could first have been known -- and they do not become different
statements because the row moved machine. Rewriting either would make every
as-of-correct computation on the box disagree with the same computation on the
laptop, which is exactly the class of bug the three clocks exist to prevent.

`ingested_at` IS REWRITTEN to the import instant, and that is equally deliberate:
it means "when this store wrote this row down", and the box wrote it down today. A
copied ingested_at would claim the box had the row in May.

`availability_kind` travels too, so a reconstructed availability stays flagged as
reconstructed on the far side rather than arriving as though it had been observed.

IDEMPOTENT. The import goes through write_many(), whose vintage key ignores a row
that is already present -- so a re-run is a no-op and an interrupted transfer is
resumed by running it again. The count subcommand is what proves the two sides
agree; it is not implied by a successful import.

THE FILE IS JSONL, one row per line, because the transfer is over ssh and a
line-oriented format can be counted with `wc -l` on both sides before anything is
parsed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import observations, session          # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FIELDS = ("registry_key", "instrument", "observed_at", "available_at",
          "value_num", "value_text", "source", "run_id", "availability_kind")


def counts(prefix: Optional[str] = None,
           store: Optional[observations.ObservationStore] = None) -> dict:
    """Row and key counts, and the observed/available span. Both sides run this."""
    own = store is None
    db = store or observations.ObservationStore()
    try:
        where, args = "", []
        if prefix:
            where = " WHERE registry_key LIKE ?"
            args = [f"{prefix}%"]
        row = db.conn.execute(
            f"SELECT COUNT(*), COUNT(DISTINCT registry_key), "
            f"MIN(observed_at), MAX(observed_at), "
            f"MIN(available_at), MAX(available_at) "
            f"FROM observations{where}", args).fetchone()
        kinds = dict(db.conn.execute(
            f"SELECT COALESCE(availability_kind, 'null'), COUNT(*) "
            f"FROM observations{where} GROUP BY 1", args).fetchall())
        return {"prefix": prefix, "rows": row[0], "keys": row[1],
                "observed_first": row[2], "observed_last": row[3],
                "available_first": row[4], "available_last": row[5],
                "availability_kinds": kinds, "db": str(db.path)}
    finally:
        if own:
            db.close()


def export_rows(prefix: Optional[str], out: Path,
                store: Optional[observations.ObservationStore] = None) -> int:
    own = store is None
    db = store or observations.ObservationStore()
    try:
        where, args = "", []
        if prefix:
            where = " WHERE registry_key LIKE ?"
            args = [f"{prefix}%"]
        cur = db.conn.execute(
            f"SELECT {', '.join(FIELDS)} FROM observations{where} "
            f"ORDER BY registry_key, observed_at, available_at", args)
        n = 0
        with out.open("w", encoding="utf-8", newline="\n") as fp:
            for r in cur:
                fp.write(json.dumps(dict(zip(FIELDS, r)), sort_keys=True) + "\n")
                n += 1
        return n
    finally:
        if own:
            db.close()


def import_rows(src: Path,
                store: Optional[observations.ObservationStore] = None) -> dict:
    own = store is None
    db = store or observations.ObservationStore()
    ingested = session.utc_iso(timespec="microseconds")
    read = written = skipped = 0
    batch: list[dict] = []
    try:
        with src.open(encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                read += 1
                r = json.loads(line)
                value = r.get("value_num")
                if value is None:
                    value = r.get("value_text")
                if value is None:
                    skipped += 1
                    continue
                batch.append({
                    "registry_key": r["registry_key"],
                    "instrument": r.get("instrument"),
                    "observed_at": r["observed_at"],
                    # UNCHANGED. See the module docstring: this is a statement
                    # about the world, not about this store.
                    "available_at": r["available_at"],
                    # REWRITTEN: this store wrote the row down now.
                    "ingested_at": ingested,
                    "value": value,
                    "source": r.get("source") or "sync",
                    "run_id": r.get("run_id"),
                    "availability_kind": r.get("availability_kind")})
                if len(batch) >= 5000:
                    written += db.write_many(batch)
                    batch = []
        if batch:
            written += db.write_many(batch)
        return {"read": read, "written": written, "skipped_valueless": skipped,
                "already_present": read - skipped - written,
                "ingested_at": ingested}
    finally:
        if own:
            db.close()


def _print_counts(c: dict) -> None:
    print(f"  store   {c['db']}")
    print(f"  rows    {c['rows']}  across {c['keys']} keys"
          + (f"  (prefix {c['prefix']!r})" if c["prefix"] else ""))
    print(f"  observed  {c['observed_first']} .. {c['observed_last']}")
    print(f"  available {str(c['available_first'])[:19]} .. "
          f"{str(c['available_last'])[:19]}")
    print(f"  availability_kind {c['availability_kinds']}")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Move observations, clocks preserved.")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("export")
    e.add_argument("--prefix", default=None, help="registry_key prefix, e.g. fred.")
    e.add_argument("--out", required=True)

    i = sub.add_parser("import")
    i.add_argument("--in", dest="src", required=True)

    c = sub.add_parser("count")
    c.add_argument("--prefix", default=None)

    a = p.parse_args(argv)

    if a.cmd == "count":
        _print_counts(counts(a.prefix))
        return 0

    if a.cmd == "export":
        out = Path(a.out)
        before = counts(a.prefix)
        n = export_rows(a.prefix, out)
        print(f"exported {n} rows to {out} ({out.stat().st_size} bytes)")
        _print_counts(before)
        return 0

    src = Path(a.src)
    if not src.is_file():
        print(f"no such file: {src}")
        return 2
    r = import_rows(src)
    print(f"read {r['read']} rows, wrote {r['written']}, "
          f"{r['already_present']} already present, "
          f"{r['skipped_valueless']} value-less and skipped")
    print(f"ingested_at set to {r['ingested_at']} -- observed_at and "
          f"available_at carried across unchanged")
    _print_counts(counts(None))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
