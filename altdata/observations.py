"""
Point-in-time observation store (SQLite).

Replaces the per-series CSV store for reading. THE CSV WRITERS KEEP RUNNING --
this is a migration, not a cutover. Both stores are written this week; the CSVs
remain the human-readable, diff-friendly copy and the fallback if anything here
turns out wrong.

-----------------------------------------------------------------------------
THREE CLOCKS, AND WHY ONE IS NOT ENOUGH
-----------------------------------------------------------------------------

    observed_at   the period the value is ABOUT      (August payrolls)
    available_at  when we could first have KNOWN it  (the September release)
    ingested_at   when we wrote it down              (whenever the job ran)

The CSV store has `date` and `as_of`, which collapses the first two into an
ambiguous pair. That is not a cosmetic problem, it is a correctness one:

    FRED REVISES. GDP, payrolls and most of the macro set are restated, often
    more than once. A revision shares its observed_at with the original print
    and differs in available_at. The CSV store overwrites the file on every
    pull, so the original print is destroyed and any backtest silently sees
    numbers that did not exist at the time it claims to be trading.

Architecture 26.2 #2 makes this non-negotiable: every material record carries
available_at, and there is ONE canonical as-of join. This module is that join.

-----------------------------------------------------------------------------
THE JOIN FILTERS ON available_at ONLY
-----------------------------------------------------------------------------

Not on observed_at, and the distinction matters. Leakage is about when you
KNEW something, never about which period it describes. Forward-dated records
are legitimate and common here -- the expiration-release ladder is dated at
future expiries and was perfectly well known when it was computed. Filtering
observed_at <= as_of would quietly delete it.

For each period, the join returns the LATEST revision knowable at the cutoff.
A row whose available_at is after the cutoff is invisible, whatever else is
true about it.

Usage:
    from altdata import observations
    store = observations.ObservationStore()
    store.write("fred.nfp", None, "2026-08-01", "2026-09-04T12:30:00+00:00",
                159_432.0, source="fred")
    rows = store.as_of("fred.nfp", as_of="2026-09-05T00:00:00+00:00")
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

from . import session


def canonical_instant(ts: Optional[str]) -> Optional[str]:
    """Fixed-width UTC ISO-8601 with microseconds.

    THE AS-OF JOIN COMPARES available_at LEXICOGRAPHICALLY, because that is what
    lets SQLite use an index. String ordering only matches chronological
    ordering when every value has the SAME WIDTH, and ISO-8601 does not
    guarantee that: '2026-09-05T12:34:56.789012+00:00' sorts AFTER
    '2026-09-05T12:34:56+00:00' even though it is later by well under a second,
    because '.' (0x2E) sorts above '+' (0x2B).

    That is not hypothetical here. FRED rows are written at second resolution
    and broker snapshots at microsecond resolution, so without canonicalisation
    a microsecond row is invisible to any second-resolution cutoff -- it looks
    like it has not happened yet. Every instant is therefore normalised to one
    width on the way in and on the way to a query.

    An unparseable value is returned unchanged rather than dropped: it is
    somebody else's data problem, and silently discarding it would be worse.
    """
    if ts is None:
        return None
    text = str(ts).strip()
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc).isoformat(timespec="microseconds")

DEFAULT_DB = os.environ.get("CHESTER_DB", "data/chester.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
    id            INTEGER PRIMARY KEY,
    registry_key  TEXT NOT NULL,
    instrument    TEXT,
    observed_at   TEXT NOT NULL,
    available_at  TEXT NOT NULL,
    ingested_at   TEXT NOT NULL,
    value_num     REAL,
    value_text    TEXT,
    source        TEXT NOT NULL,
    run_id        TEXT,
    CHECK (value_num IS NOT NULL OR value_text IS NOT NULL)
);

-- Idempotence key, as an EXPRESSION index rather than a table UNIQUE, because
-- SQLite treats NULLs as distinct in a UNIQUE constraint. `instrument` is NULL
-- for every macro series, so a plain UNIQUE would have deduped nothing at all
-- for the majority of rows and a re-pull would have silently doubled the store.
-- COALESCE gives NULL a single canonical value so the constraint bites.
--
-- A re-pull of the same vintage is therefore idempotent; a REVISION differs in
-- available_at and is a NEW row rather than an overwrite. That is the point:
-- history accumulates instead of being replaced.
CREATE UNIQUE INDEX IF NOT EXISTS obs_vintage
    ON observations (registry_key, COALESCE(instrument, ''), observed_at,
                     available_at, source);

CREATE INDEX IF NOT EXISTS obs_asof
    ON observations (registry_key, instrument, observed_at, available_at);
CREATE INDEX IF NOT EXISTS obs_available
    ON observations (available_at);
"""

# For each (registry_key, instrument, observed_at), the row with the greatest
# available_at that is still <= the cutoff. Correlated rather than a window
# function so it runs on any SQLite build the VPS happens to ship.
AS_OF_SQL = """
SELECT observed_at, value_num, value_text, source, available_at, run_id
  FROM observations o
 WHERE registry_key = :key
   AND instrument IS :instrument
   AND available_at <= :as_of
   AND available_at = (
        SELECT MAX(available_at) FROM observations
         WHERE registry_key = o.registry_key
           AND instrument IS o.instrument
           AND observed_at = o.observed_at
           AND available_at <= :as_of)
 ORDER BY observed_at
"""


def snapshot_sqlite(src: Path, dest: Path) -> dict:
    """Consistent copy of a LIVE SQLite database, via the online backup API.

    NOT shutil.copy2, and the difference is not pedantry. The EOD pass runs at
    16:10, inside the Portfolio Truth sync window (Mon-Fri 09:00-17:00 every 30
    minutes), and the nightly off-box sweep runs while nothing guarantees the
    database is idle either. A plain file copy taken mid-transaction produces a
    file that OPENS CLEANLY and is missing rows -- a backup that looks valid and
    is not, which is worse than no backup because it is trusted.

    sqlite3's backup() holds a read lock for the duration and is the supported
    way to snapshot a database that may have a writer. It lives here, in the
    module that owns the database, so the EOD zip and the rclone sweep cannot
    drift into copying it two different ways.

    Raises on failure. A caller that wants a backup failure to be non-fatal
    catches it and says so; silence is not on offer.
    """
    src = Path(src)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.unlink(missing_ok=True)
    conn = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    try:
        out = sqlite3.connect(str(dest))
        try:
            conn.backup(out)
            rows = out.execute(
                "SELECT COUNT(*) FROM observations").fetchone()[0]
        finally:
            out.close()
    finally:
        conn.close()
    return {"src": str(src), "dest": str(dest),
            "bytes": dest.stat().st_size, "observations": rows}


class ObservationStore:
    """Append-only point-in-time store. Never updates, never deletes."""

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = Path(path or DEFAULT_DB)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "ObservationStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- write ------------------------------------------------------------
    def write(self, registry_key: str, instrument: Optional[str],
              observed_at: str, available_at: str, value: Any,
              source: str, run_id: Optional[str] = None) -> int:
        """One observation. Returns rows inserted (0 if already present)."""
        return self.write_many([{
            "registry_key": registry_key, "instrument": instrument,
            "observed_at": observed_at, "available_at": available_at,
            "value": value, "source": source, "run_id": run_id}])

    def write_many(self, rows: Iterable[dict]) -> int:
        """Batch insert. Duplicate vintages are ignored, not errors.

        A re-run pulling the same data must be a no-op rather than a failure --
        the pipeline re-runs constantly and a crash on re-ingest would make
        recovery harder than the problem it warns about.
        """
        ingested = session.utc_iso()
        payload = []
        for r in rows:
            v = r.get("value")
            num = v if isinstance(v, (int, float)) and not isinstance(v, bool) else None
            txt = None if num is not None else (None if v is None else str(v))
            if num is None and txt is None:
                continue          # a value-less row carries nothing; skip it
            payload.append((r["registry_key"], r.get("instrument"),
                            r["observed_at"], canonical_instant(r["available_at"]),
                            r.get("ingested_at") or ingested, num, txt,
                            r["source"], r.get("run_id")))
        if not payload:
            return 0
        cur = self.conn.executemany(
            "INSERT OR IGNORE INTO observations "
            "(registry_key, instrument, observed_at, available_at, ingested_at,"
            " value_num, value_text, source, run_id) "
            "VALUES (?,?,?,?,?,?,?,?,?)", payload)
        self.conn.commit()
        return cur.rowcount

    # -- read -------------------------------------------------------------
    def as_of(self, registry_key: str, as_of: Optional[str] = None,
              instrument: Optional[str] = None) -> list[dict]:
        """Every period's latest value KNOWABLE at `as_of`.

        This is the canonical join. `as_of` defaults to now, which is the right
        default for a live run and the wrong one for a historical study --
        pass the cutoff explicitly whenever reproducing a past decision.
        """
        # Microseconds, not the default seconds. Truncating "now" to the
        # second and then padding it to .000000 puts the cutoff EARLIER than
        # any row written later in that same second, which would hide a
        # just-written observation from the query that follows it.
        cutoff = canonical_instant(as_of or session.utc_iso(timespec="microseconds"))
        cur = self.conn.execute(AS_OF_SQL, {"key": registry_key,
                                            "instrument": instrument,
                                            "as_of": cutoff})
        return [dict(r) for r in cur.fetchall()]

    def latest_as_of(self, registry_key: str, as_of: Optional[str] = None,
                     instrument: Optional[str] = None) -> Optional[dict]:
        """The most recent period knowable at the cutoff, or None."""
        rows = self.as_of(registry_key, as_of, instrument)
        return rows[-1] if rows else None

    def vintages(self, registry_key: str, observed_at: str,
                 instrument: Optional[str] = None) -> list[dict]:
        """Every vintage of one period, oldest first. The revision trail."""
        cur = self.conn.execute(
            "SELECT available_at, value_num, value_text, source, ingested_at "
            "FROM observations WHERE registry_key = ? AND instrument IS ? "
            "AND observed_at = ? ORDER BY available_at",
            (registry_key, instrument, observed_at))
        return [dict(r) for r in cur.fetchall()]

    def instruments(self, registry_key: str) -> list[str]:
        """Every non-null instrument this key has been written for.

        as_of() matches `instrument IS :instrument`, which is exact by design
        -- a query for SPY must not silently return the macro row keyed on
        NULL. That leaves no way to ask "which symbols do I hold", which is
        precisely what a positions block needs, so it is a separate question
        with a separate method rather than a looser join.
        """
        cur = self.conn.execute(
            "SELECT DISTINCT instrument FROM observations "
            " WHERE registry_key = ? AND instrument IS NOT NULL ORDER BY 1",
            (registry_key,))
        return [r[0] for r in cur.fetchall()]

    def keys(self) -> list[str]:
        cur = self.conn.execute(
            "SELECT DISTINCT registry_key FROM observations ORDER BY 1")
        return [r[0] for r in cur.fetchall()]

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]


def migrate_csv_store(store_dir: Optional[str] = None,
                      db_path: Optional[str] = None,
                      source_default: str = "fred") -> dict:
    """Copy the CSV store into SQLite. Idempotent; safe to re-run.

    AVAILABLE_AT FOR HISTORICAL ROWS IS AN ESTIMATE AND IS LABELLED AS ONE.
    The CSVs carry `as_of` -- when the row was PULLED -- which is an upper
    bound on when it became available, not the release time. For a series
    revised between its release and our pull, this over-states how early we
    knew, which is the direction that leaks. So migrated rows are marked
    source='<source>:csv_migrated' and anything doing serious point-in-time
    work should treat pre-migration history as approximate. Rows written from
    here on carry a real available_at.
    """
    from . import config, store as csv_store  # noqa: PLC0415

    src_dir = Path(store_dir or csv_store.DEFAULT_STORE_DIR)
    known = {s.key for s in config.FRED_SERIES}
    out = {"files": 0, "rows_read": 0, "rows_written": 0, "unknown_keys": []}
    if not src_dir.exists():
        return out

    db = ObservationStore(db_path)
    try:
        import csv as csvmod
        for path in sorted(src_dir.glob("*.csv")):
            key = path.stem
            if key not in known:
                out["unknown_keys"].append(key)
            out["files"] += 1
            batch = []
            with path.open(encoding="utf-8", newline="") as fp:
                for rec in csvmod.DictReader(fp):
                    out["rows_read"] += 1
                    raw = rec.get("value")
                    try:
                        val = float(raw)
                        if val != val:          # NaN: a real FRED gap
                            continue
                    except (TypeError, ValueError):
                        continue
                    batch.append({
                        "registry_key": f"fred.{key}",
                        "instrument": None,
                        "observed_at": rec.get("date"),
                        "available_at": rec.get("as_of") or rec.get("date"),
                        "value": val,
                        "source": f"{rec.get('source') or source_default}:csv_migrated",
                    })
            out["rows_written"] += db.write_many(batch)
    finally:
        db.close()
    return out


def _main(argv) -> int:
    """`python -m altdata.observations snapshot <dest>` for the backup sweep.

    A CLI rather than an inline `python -c` in the shell script, so the
    snapshot rule has exactly one implementation and the script cannot quietly
    fall back to `cp` the next time somebody edits it.
    """
    if len(argv) >= 1 and argv[0] == "snapshot":
        dest = Path(argv[1]) if len(argv) > 1 else Path("chester_snapshot.db")
        src = Path(argv[2]) if len(argv) > 2 else Path(DEFAULT_DB)
        if not src.exists():
            print(f"no database at {src}")
            return 1
        try:
            info = snapshot_sqlite(src, dest)
        except Exception as exc:  # noqa: BLE001 -- the caller is a shell script
            print(f"snapshot failed: {type(exc).__name__}: {exc}")
            return 2
        print(f"snapshot ok {info['dest']} "
              f"({info['bytes']:,} bytes, {info['observations']:,} observations)")
        return 0
    print("usage: python -m altdata.observations snapshot <dest> [src]")
    return 2


if __name__ == "__main__":
    import sys as _sys
    raise SystemExit(_main(_sys.argv[1:]))
