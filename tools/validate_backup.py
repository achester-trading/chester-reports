"""
Validation gate for the backup path -- audit finding P0-1.

THE STORE IS THE SYSTEM AND IT HAD ONE COPY. `data/chester.db` holds the
point-in-time observation history, the decision register and the immutable
packets that make a past run replayable; it is gitignored, so git has never
seen it, and until this work the only copy in existence lived on one VPS.

Four properties, each of which fails silently if it is merely intended:

  1. **THE DATABASE IS IN THE ZIP.** A backup that covers chains and omits the
     store protects the cheap asset and loses the expensive one. Asserted on a
     real archive built by the real function.

  2. **THE SNAPSHOT IS CONSISTENT, NOT A FILE COPY.** A live SQLite file read
     mid-write produces a database that OPENS CLEANLY and is missing rows -- a
     backup that looks valid and is not, which is worse than none because it is
     trusted. So the snapshot is taken with the online backup API and the copy
     is opened and counted, not merely sized.

  3. **A FAILED SNAPSHOT DOES NOT PRODUCE A COMPLETE-LOOKING ZIP.** The
     dangerous version of this failure is the archive that is written anyway,
     one file short, and reported ok. The failure path is exercised.

  4. **THE SWEEP COPIES AND NEVER SYNCS.** `rclone sync` makes the remote match
     the source, so a local deletion is replicated to the backup and the backup
     is gone at the moment it is needed. Checked in the script's own text,
     because this is the one line whose wrong version is indistinguishable from
     the right one until the day it matters.

No network, no rclone, no remote. Builds its own database in a temp directory.

    python tools/validate_backup.py
"""

from __future__ import annotations

import re
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import observations  # noqa: E402

PASS = 0
FAIL = 0
LINE = "=" * 78


def ok(m: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {m}")


def _count(db: Path) -> int:
    """Row count from an independent open, with the handle CLOSED after.

    The close is not tidiness. On Windows an open sqlite handle keeps the file
    locked, so a leaked connection makes TemporaryDirectory cleanup raise
    PermissionError and the whole validator dies on teardown rather than on an
    assertion -- which this file did, on its first run, on the authoring
    machine. A validator that cannot run everywhere it is authored is a
    validator that gets skipped.
    """
    conn = sqlite3.connect(str(db))
    try:
        return conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    finally:
        conn.close()


def _seed_db(path: Path, rows: int = 25) -> None:
    with observations.ObservationStore(str(path)) as db:
        db.write_many([
            {"registry_key": "test.metric", "instrument": None,
             "observed_at": f"2026-01-{i % 28 + 1:02d}",
             "available_at": f"2026-02-01T00:00:{i % 60:02d}Z",
             "value": float(i), "source": "test"}
            for i in range(rows)])


def group_a() -> None:
    """The snapshot is consistent and countable."""
    print(f"{LINE}\nA. snapshot_sqlite -- a copy that can be opened and counted\n{LINE}")
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "src.db"
        dest = Path(d) / "snap.db"
        _seed_db(src, 25)
        info = observations.snapshot_sqlite(src, dest)
        if info["observations"] == 25:
            ok("snapshot reports the row count it actually copied (25)")
        else:
            bad(f"snapshot counted {info['observations']}, wanted 25")

        # Open the copy independently. A torn file can be the right size.
        n = _count(dest)
        if n == 25:
            ok("the snapshot opens independently with all 25 rows")
        else:
            bad(f"the snapshot holds {n} rows on independent open")

        # A snapshot taken while a connection is open must still be complete.
        # This is the case a file copy gets wrong.
        with observations.ObservationStore(str(src)) as live:
            live.write("test.metric", None, "2026-03-01",
                       "2026-03-01T00:00:00Z", 99.0, "test")
            info2 = observations.snapshot_sqlite(src, Path(d) / "snap2.db")
        if info2["observations"] == 26:
            ok("a snapshot taken with a live connection open sees all 26 rows")
        else:
            bad(f"snapshot under a live connection saw {info2['observations']}")

        # Destination is replaced, not appended to or left stale.
        info3 = observations.snapshot_sqlite(src, dest)
        if info3["observations"] == 26:
            ok("re-snapshotting overwrites rather than leaving a stale copy")
        else:
            bad(f"re-snapshot left {info3['observations']} rows")

    # A missing source must raise, not return an empty database.
    with tempfile.TemporaryDirectory() as d:
        try:
            observations.snapshot_sqlite(Path(d) / "nope.db", Path(d) / "o.db")
            bad("snapshotting a missing database returned instead of raising")
        except Exception:  # noqa: BLE001
            ok("a missing source raises rather than yielding an empty backup")


def group_wal() -> None:
    """Both stores open in WAL with a busy timeout -- P0-3."""
    print(f"\n{LINE}\nA2. Concurrency pragmas on every connection (P0-3)\n{LINE}")
    sys.path.insert(0, str(REPO))
    from register.store import Register  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as d:
        for cls, name in ((observations.ObservationStore, "ObservationStore"),
                          (Register, "Register")):
            s = cls(str(Path(d) / "t.db"))
            try:
                jm = s.conn.execute("PRAGMA journal_mode").fetchone()[0]
                bt = s.conn.execute("PRAGMA busy_timeout").fetchone()[0]
            finally:
                s.conn.close()
            # WAL persists in the file header, so the second class inherits it
            # -- which is itself the point: one database, one journal mode, no
            # way for two openers to disagree about it.
            if str(jm).lower() == "wal":
                ok(f"{name} opens in WAL, so a reader is not blocked by a writer")
            else:
                bad(f"{name} journal_mode={jm}; a reader fails while the sync writes")
            if bt >= 5000:
                ok(f"{name} busy_timeout={bt}ms -- a collision waits, not errors")
            else:
                bad(f"{name} busy_timeout={bt}; SQLite's default 0 fails instantly")


def group_b() -> None:
    """The EOD zip carries the database and the pin log."""
    print(f"\n{LINE}\nB. backup_chains -- the store is in the archive\n{LINE}")
    import run_eod  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        chains = root / "chains" / "2026-01-02"
        chains.mkdir(parents=True)
        (chains / "SPY_1.csv").write_text("a,b\n1,2\n", encoding="utf-8")
        (chains / "QQQ_1.csv").write_text("a,b\n3,4\n", encoding="utf-8")
        db = root / "chester.db"
        _seed_db(db, 7)
        pin = root / "pin_log.csv"
        pin.write_text("date,symbol\n2026-01-02,SPY\n", encoding="utf-8")

        old_chain, old_db, old_pin = (run_eod.config.CHAIN_DIR,
                                      observations.DEFAULT_DB,
                                      run_eod.config.PIN_LOG_PATH)
        run_eod.config.CHAIN_DIR = str(root / "chains")
        observations.DEFAULT_DB = str(db)
        run_eod.config.PIN_LOG_PATH = str(pin)
        try:
            out = run_eod.backup_chains("2026-01-02", str(root / "out"))
        finally:
            run_eod.config.CHAIN_DIR = old_chain
            observations.DEFAULT_DB = old_db
            run_eod.config.PIN_LOG_PATH = old_pin

        if not out.get("ok"):
            bad(f"backup failed: {out.get('error')}")
            return
        names = zipfile.ZipFile(out["dest"]).namelist()
        for want, why in (("db/chester.db", "the database is in the zip"),
                          ("state/pin_log.csv", "the pin log is in the zip")):
            if want in names:
                ok(why)
            else:
                bad(f"{want} missing from the archive: {names}")
        if len(names) == 4:
            ok("the archive holds exactly the 2 chains + 2 extras it claims")
        else:
            bad(f"archive holds {len(names)} entries, wanted 4: {names}")

        # The zipped database must itself be readable. A zip entry of the right
        # name proves nothing about the bytes inside it.
        with tempfile.TemporaryDirectory() as x:
            zipfile.ZipFile(out["dest"]).extract("db/chester.db", x)
            n = _count(Path(x) / "db" / "chester.db")
            if n == 7:
                ok("the database extracted from the zip holds all 7 rows")
            else:
                bad(f"extracted database holds {n} rows, wanted 7")


def group_c() -> None:
    """A failed snapshot must not yield a zip that looks complete."""
    print(f"\n{LINE}\nC. The failure path -- no complete-looking partial archive\n{LINE}")
    import run_eod  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        chains = root / "chains" / "2026-01-02"
        chains.mkdir(parents=True)
        (chains / "SPY_1.csv").write_text("a\n1\n", encoding="utf-8")
        # A file that exists and is not a database: the snapshot must fail.
        db = root / "chester.db"
        db.write_text("this is not a database", encoding="utf-8")

        old_chain, old_db = run_eod.config.CHAIN_DIR, observations.DEFAULT_DB
        run_eod.config.CHAIN_DIR = str(root / "chains")
        observations.DEFAULT_DB = str(db)
        try:
            out = run_eod.backup_chains("2026-01-02", str(root / "out"))
        finally:
            run_eod.config.CHAIN_DIR = old_chain
            observations.DEFAULT_DB = old_db

        if not out.get("ok") and "snapshot failed" in str(out.get("error", "")):
            ok("an unreadable database fails the backup instead of omitting it")
        else:
            bad(f"a corrupt database produced ok={out.get('ok')}: {out}")
        if not (root / "out").exists() or not list((root / "out").glob("*.zip")):
            ok("no archive was written at all -- nothing looks complete")
        else:
            bad("a partial archive was written to the backup folder")


def group_d() -> None:
    """The sweep copies, and never syncs."""
    print(f"\n{LINE}\nD. rclone_sync.sh -- copy semantics and its own failures\n{LINE}")
    s = (REPO / "scripts/rclone_sync.sh").read_text(encoding="utf-8")
    code = "\n".join(ln for ln in s.splitlines() if not ln.strip().startswith("#"))

    # ANYWHERE in the executable text, not anchored to the line start. The
    # first version of this check used `^\s*rclone sync` and a mutation test
    # walked straight past it -- `if rclone sync "$srcdir"` is not at a line
    # start. A check for the one line whose wrong version is invisible cannot
    # itself have a blind spot.
    if re.search(r"\brclone\s+sync\b", code):
        bad("the sweep uses `rclone sync` -- a local deletion would be "
            "replicated to the backup, destroying it exactly when needed")
    else:
        ok("no `rclone sync` anywhere in the executable text")
    if "rclone copy" in code:
        ok("the sweep uses `rclone copy` -- the remote only ever grows")
    else:
        bad("no `rclone copy` found; what is this script doing?")

    if "altdata.observations snapshot" in code:
        ok("the database goes through the shared snapshot CLI, not `cp`")
    else:
        bad("the sweep copies the database some other way")
    if re.search(r'CHESTER_RCLONE_REMOTE:-', code) and "no_remote" in code:
        ok("an unconfigured remote exits loudly rather than sweeping nothing")
    else:
        bad("an unset remote could pass silently")
    if "$(date +%Y-%m-%d)" in code:
        ok("the staged snapshot is dated, so the remote accumulates history")
    else:
        bad("the snapshot name is not dated -- copy semantics would keep one file")

    u = (REPO / "deploy/systemd/chester-backup.service").read_text(encoding="utf-8")
    if not re.search(r"^SuccessExitStatus", u, re.M):
        ok("no SuccessExitStatus -- a backup that did not happen shows red")
    else:
        bad("the unit forgives a failed sweep")
    t = (REPO / "deploy/systemd/chester-backup.timer").read_text(encoding="utf-8")
    if "America/New_York" in t:
        ok("the timer is zone-pinned")
    else:
        bad("the backup timer is not zone-pinned")
    if re.search(r"^Persistent=true", t, re.M):
        ok("Persistent=true -- a box that was down still sweeps when it returns")
    else:
        bad("a missed backup window is never made up")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    group_a()
    group_wal()
    group_b()
    group_c()
    group_d()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
