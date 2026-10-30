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

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

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
    """The EOD zip carries the chains and the pin log -- and, since AUD-1 1a,
    NOT the database: the nightly sweep's verified db/ snapshot is its backup."""
    print(f"\n{LINE}\nB. backup_chains -- the chains and the pin log, not the store "
          f"(AUD-1 1a)\n{LINE}")
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
        if "state/pin_log.csv" in names:
            ok("the pin log is in the zip")
        else:
            bad(f"state/pin_log.csv missing from the archive: {names}")
        if not any(n.startswith("db/") or n.endswith(".db") for n in names):
            ok("AUD-1 1a: the database is NOT in the zip -- the sweep's db/ snapshot "
               "is its backup, and a full copy a session was the space leak")
        else:
            bad(f"the zip still carries a database: {names}")
        if len(names) == 3 and zipfile.ZipFile(out["dest"]).testzip() is None:
            ok("the archive holds exactly the 2 chains + the pin log, CRC clean")
        else:
            bad(f"archive holds {len(names)} entries, wanted 3: {names}")


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

        # AUD-1 1a: the zip no longer reads the database at all, so a corrupt
        # one cannot fail it, and nothing of it reaches the archive. The
        # database's own backup is the sweep's snapshot, integrity-checked there.
        names = (zipfile.ZipFile(out["dest"]).namelist()
                 if out.get("ok") and out.get("dest") else [])
        if out.get("ok") and names == ["SPY_1.csv"]:
            ok("AUD-1 1a: a corrupt database no longer touches the chain zip, which "
               "holds the chains alone")
        else:
            bad(f"the chain zip read the database: {out}")


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

    # B-1. THE UNIT STARTS IN $HOME, where `-m altdata...` finds no package: every
    # 02:30 sweep that reached the snapshot died there with ModuleNotFoundError,
    # and the only sweeps that ever succeeded were run by hand from the repo.
    # Every other script wraps its module calls the same way (check_heartbeat.sh).
    wrapped = re.compile(r'\(cd "\$REPO" && "\$PY" -m altdata\.observations snapshot')

    def snapshot_wrapped(text: str) -> bool:
        return all(wrapped.search(ln) for ln in text.splitlines()
                   if "altdata.observations snapshot" in ln
                   and not ln.strip().startswith("#"))
    unwrapped = code.replace('(cd "$REPO" && "$PY" -m altdata.observations',
                             '"$PY" -m altdata.observations')
    if snapshot_wrapped(code) and not snapshot_wrapped(unwrapped):
        ok('the snapshot runs as (cd "$REPO" && "$PY" -m altdata.observations '
           'snapshot ...) -- and the check fails on the unwrapped call')
    else:
        bad('the snapshot is not wrapped in (cd "$REPO" && ...): under the unit, '
            'which starts in $HOME, `-m altdata` does not resolve')
    # audit-leftovers-1: the target is the crypt remote; without its settings
    # the sweep exits 1 (no_crypt) and never falls back to the plaintext remote.
    if "crypt_env || finish no_crypt 1" in code and 'REMOTE="$CRYPT_REMOTE"' in code \
            and code.index("crypt_env || finish no_crypt 1") < code.index("copy_tree \"$STAGE\""):
        ok("an unconfigured (crypt) remote exits loudly rather than sweeping nothing "
           "or sweeping plaintext")
    else:
        bad("an unset crypt remote could pass silently, or fall back to plaintext")
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


def group_e() -> None:
    """29 Sep 2026: what goes off-box, db/ retention, and stalls that fail fast."""
    print(f"\n{LINE}\nE. The 29 Sep fix -- excludes, verified snapshot, retention, "
          f"stall limits\n{LINE}")
    s = (REPO / "scripts/rclone_sync.sh").read_text(encoding="utf-8")
    code = "\n".join(ln for ln in s.splitlines() if not ln.strip().startswith("#"))

    # -- what goes off-box ---------------------------------------------------
    def data_excludes_db(text: str) -> bool:
        return bool(re.search(r'copy_tree "\$REPO/data".*--exclude "/chester\.db\*"', text))

    def state_excludes_stage(text: str) -> bool:
        return bool(re.search(r'copy_tree "\$STATE_DIR".*--exclude "/backup_stage/\*\*"', text))
    if data_excludes_db(code) and not data_excludes_db(
            code.replace(' --exclude "/chester.db*"', "")):
        ok("data/ excludes chester.db* -- the live file never leaves the box raw")
    else:
        bad("data/ would upload the live chester.db, a torn copy that looks valid")
    if state_excludes_stage(code) and not state_excludes_stage(
            code.replace(' --exclude "/backup_stage/**"', "")):
        ok("state/ excludes backup_stage/ -- the snapshot uploads once, to db/")
    else:
        bad("state/ re-uploads the staged snapshot db/ already carries")

    # -- the snapshot is verified before it is uploaded ----------------------
    order = [code.find(k) for k in (
        "altdata.observations snapshot", "altdata.observations integrity",
        'gzip -c "$SNAP"', 'gzip -dc "$UPLOAD" | cmp -s - "$SNAP"',
        'copy_tree "$STAGE" "db"')]
    if -1 not in order and order == sorted(order):
        ok("snapshot -> integrity_check -> gzip -> byte-for-byte round trip -> upload, "
           "in that order")
    else:
        bad(f"the verify-before-upload sequence is missing or out of order: {order}")

    with tempfile.TemporaryDirectory() as d:
        src, snap = Path(d) / "src.db", Path(d) / "snap.db"
        _seed_db(src, 5)
        observations.snapshot_sqlite(src, snap)
        if observations.integrity_check(snap) == []:
            ok("integrity_check passes a clean snapshot")
        else:
            bad("integrity_check rejected a clean snapshot")
        # Corrupt a page past the header: the file still opens by name.
        raw = bytearray(snap.read_bytes())
        for i in range(4096, min(len(raw), 8192)):
            raw[i] = 0xFF
        bad_db = Path(d) / "bad.db"
        bad_db.write_bytes(bytes(raw))
        try:
            flagged = observations.integrity_check(bad_db) != []
        except sqlite3.DatabaseError:
            flagged = True
        if flagged:
            ok("integrity_check refuses a snapshot with a corrupted page")
        else:
            bad("a corrupted snapshot passed integrity_check")
        rc = observations._main(["integrity", str(bad_db)])
        if rc == 2:
            ok("the `integrity` CLI exits 2 on it, which the sweep maps to rc 2")
        else:
            bad(f"the integrity CLI exited {rc} on a corrupted snapshot")

    # -- nothing removed but named db/ snapshots -----------------------------
    for pat, why in ((r"\brclone\s+(delete|purge|rmdir|rmdirs|cleanup|dedupe)\b",
                      "no bulk removal verb (delete/purge/rmdir/cleanup/dedupe)"),
                     (r"--delete-", "no --delete-* flag"),
                     (r"--drive-use-trash=false|--drive-use-trash\s+false",
                      "Drive's trash is not bypassed")):
        if re.search(pat, code):
            bad(f"the sweep carries a forbidden removal: {pat}")
        else:
            ok(why)
    deletes = [ln for ln in code.splitlines() if re.search(r"\brclone\s+deletefile\b", ln)]
    allowed = ('rclone deletefile "$REMOTE/db/$name"',
               # AUD-1 1c: Drive's chain zips past the newest 14 (one rule since
               # audit-leftovers-1), by exact name
               'rclone deletefile "$REMOTE/backups/chains/$name"')
    if deletes and all(any(a in ln for a in allowed) for ln in deletes):
        ok("the only removals are `rclone deletefile` of one named file in db/ or "
           "backups/chains/")
    else:
        bad(f"a deletefile reaches outside db/: {deletes}")
    guard = code.find(r'^chester-[0-9]{4}-[0-9]{2}-[0-9]{2}\.db(\.gz)?$')
    if deletes and 0 <= guard < code.find("rclone deletefile"):
        ok("each name is re-matched against the snapshot pattern in the shell first")
    else:
        bad("the shell deletes names it has not itself matched")
    if "--require" in code and 'if copy_tree "$STAGE" "db"' in code:
        ok("prune runs only after the db/ upload succeeded, and names tonight's file")
    else:
        bad("a failed upload could still prune")
    guard_a = code.find(r'^alpha-[0-9]{4}-[0-9]{2}-[0-9]{2}\.db(\.gz)?$')
    blk = code[code.find('if copy_tree "$STAGE" "db"'):]
    # Stitching, week of 19 Oct (meeting b): the alpha prune also waits for the
    # budget -- reached only past the "no alpha snapshot tonight" branch, and only
    # through can_housekeep, like every other prune.
    if (0 <= guard_a < code.find("rclone deletefile")
            and (re.search(r'if \[\[ "\$ALPHA" == "ok" \]\]; then\s+prune_db alpha', blk)
                 or re.search(r'if \[\[ "\$ALPHA" != "ok" \]\]; then\s+'
                              r'ALPHA_PRUNE="not run[^"]*"\s+'
                              r'elif can_housekeep "alpha prune"; then\s+prune_db alpha',
                              blk))):
        ok("ruling 8: the alpha-* snapshots prune by their own exact-name pattern, "
           "and only on a night tonight's alpha snapshot was staged")
    else:
        bad("the alpha-* prune is missing, unguarded, or matches loosely")

    # -- the retention rule itself -------------------------------------------
    import importlib.util  # noqa: PLC0415
    spec = importlib.util.spec_from_file_location(
        "backup_retention", REPO / "scripts" / "backup_retention.py")
    br = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(br)
    from datetime import date, timedelta  # noqa: PLC0415

    today = date(2026, 9, 30)
    days = [today - timedelta(days=i) for i in range(400)]
    names = [f"chester-{d.isoformat()}.db.gz" for d in days]
    names += ["chester-2026-09-28.db", "notes.txt", "chester-latest.db",
              "chester-2026-10-05.db.gz"]           # raw 28 Sep, strays, future
    keep, delete = br.plan(names, today)
    keep_d = {n for n in keep if n.endswith(".db.gz")}
    daily = {f"chester-{(today - timedelta(days=i)).isoformat()}.db.gz" for i in range(14)}
    if daily <= keep_d:
        ok("the last 14 days are all kept")
    else:
        bad(f"a daily snapshot inside 14 days would go: {sorted(daily - keep_d)[:3]}")
    monday = today - timedelta(days=today.weekday())
    weekly = set()
    for w in range(8):
        sunday = monday - timedelta(weeks=w) + timedelta(days=6)
        weekly.add(f"chester-{min(sunday, today).isoformat()}.db.gz")
    if weekly <= keep_d:
        ok("the newest snapshot of each of the last 8 ISO weeks is kept")
    else:
        bad(f"a weekly snapshot would go: {sorted(weekly - keep_d)[:3]}")
    oldest = min(days)
    months, d0 = set(), date(oldest.year, oldest.month, 1)
    while d0 <= today:
        nxt = date(d0.year + (d0.month == 12), d0.month % 12 + 1, 1)
        last = min(nxt - timedelta(days=1), today)
        months.add(f"chester-{last.isoformat()}.db.gz")
        d0 = nxt
    if months <= keep_d:
        ok(f"the newest snapshot of every month is kept ({len(months)} months, forever)")
    else:
        bad(f"a monthly snapshot would go: {sorted(months - keep_d)[:3]}")
    if not any(n in delete for n in ("notes.txt", "chester-latest.db")):
        ok("names outside the pattern are never planned for deletion")
    else:
        bad("the plan would delete a file it does not recognise")
    if "chester-2026-10-05.db.gz" not in delete:
        ok("a future-dated snapshot is kept -- a wrong clock loses nothing")
    else:
        bad("a future-dated snapshot would be deleted")
    expected_keep = len(daily | weekly | months | {"chester-2026-10-05.db.gz"})
    if len(keep_d) == expected_keep and len(delete) == len(names) - 2 - len(keep):
        ok(f"everything else goes: {len(keep)} kept of {len(names) - 2} snapshots")
    else:
        bad(f"kept {len(keep_d)} (wanted {expected_keep}), deleting {len(delete)}")

    # -- ruling 8: the lab ledger's alpha-* snapshots, the same rule apart ------
    a_names = [f"alpha-{d.isoformat()}.db.gz" for d in days]
    mixed = names + a_names + ["alpha-latest.db", "alpha-2026-09-30.db.bak"]
    a_keep, a_del = br.plan(mixed, today, "alpha")
    c_keep, c_del = br.plan(mixed, today)
    if (sorted(n.replace("alpha-", "chester-") for n in a_keep if n.endswith(".gz"))
            == sorted(keep_d - {"chester-2026-10-05.db.gz"})
            and all(n.startswith("alpha-") for n in a_keep + a_del)):
        ok(f"alpha-* snapshots keep by the same rule ({len(a_keep)} kept of "
           f"{len(a_names)}), and an alpha plan names no chester file")
    else:
        bad("the alpha-* plan differs from chester's rule or crosses families")
    if (not any(n.startswith("alpha-") for n in c_keep + c_del)
            and set(c_del) == set(delete)):
        ok("chester's plan is unchanged by alpha names beside it")
    else:
        bad("alpha names leak into chester's plan")
    if not any(n in a_del for n in ("alpha-latest.db", "alpha-2026-09-30.db.bak")):
        ok("alpha names outside the exact pattern are never planned")
    else:
        bad("the alpha plan would delete an unrecognised name")
    lone = [f"alpha-{(today - timedelta(days=500)).isoformat()}.db.gz",
            f"alpha-{(today - timedelta(days=499)).isoformat()}.db.gz"]
    lk, _ld = br.plan(lone, today, "alpha")
    if lone[1] in lk:
        ok("the newest alpha snapshot is never pruned, however old")
    else:
        bad("the newest alpha snapshot would be pruned")

    import contextlib  # noqa: PLC0415
    import io  # noqa: PLC0415
    old_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO("\n".join(names))
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            rc = br.main(["--today", "2026-09-30",
                          "--require", "chester-2026-10-01.db.gz"])
    finally:
        sys.stdin = old_stdin
    if rc == 3 and out.getvalue() == "":
        ok("tonight's snapshot missing from the listing -> exit 3, nothing printed")
    else:
        bad(f"a missing upload still produced a prune plan (rc={rc})")

    # -- stalls fail fast ----------------------------------------------------
    m = re.search(r'^RCLONE_LIMITS="([^"]*)"', code, re.M)
    limits = m.group(1) if m else ""
    for flag in ("--timeout", "--contimeout", "--low-level-retries", "--retries ",
                 "--tpslimit", "--stats "):
        if flag in limits:
            ok(f"rclone runs with {flag.strip()}")
        else:
            bad(f"RCLONE_LIMITS lacks {flag.strip()}")
    if "CHESTER_RCLONE_LIMITS" not in code:
        ok("the stall limits are not env-overridable (tuning cannot drop them)")
    else:
        bad("the stall limits can be overridden away")
    # Every rclone copy that RUNS (comments aside): under a coreutils timeout with
    # a kill-after -- copy_tree's "${mins}m", the lab's "${LAB_CAP}m" (its 5m cut
    # to the budget; stitching, week of 19 Oct), or a fixed cap on the copy's own
    # line -- and with the stall limits.
    lines = code.splitlines()
    copies = [i for i, ln in enumerate(lines)
              if re.search(r"\brclone\s+copy\b", ln) and not ln.lstrip().startswith("#")]
    capped = all(
        re.search(r'timeout --kill-after=\S+ (?:"\$\{mins\}m"|"\$\{LAB_CAP\}m"|\d+m)\s',
                  lines[i - 1] + " " + lines[i]) for i in copies)
    limited = all("$RCLONE_LIMITS" in lines[i] for i in copies)
    if copies and capped and limited:
        ok("every rclone copy runs under its own timeout and the stall limits")
    else:
        bad("an rclone copy can run uncapped")
    # ONE BUDGET (14 Oct 2026), in place of a sum of caps: the budget, the
    # kill-after and ten minutes of slack fit inside the unit's TimeoutStartSec,
    # read from the unit file -- 2h30 on this branch, 2h once aud-2 merges.
    u = (REPO / "deploy/systemd/chester-backup.service").read_text(encoding="utf-8")
    tm = re.search(r"^TimeoutStartSec=(?:(\d+)h)?(?:(\d+)min)?\s*$", u, re.M)
    ceiling = (int(tm.group(1) or 0) * 60 + int(tm.group(2) or 0)) if tm else 0
    bm = re.search(r'^SWEEP_BUDGET_MIN="\$\{CHESTER_SWEEP_BUDGET_MIN:-(\d+)\}"', code, re.M)
    km = re.search(r"timeout --kill-after=(\d+)s", code)
    budget = int(bm.group(1)) if bm else 0
    kill = -(-int(km.group(1)) // 60) if km else 0
    if budget and kill and budget + kill + 10 <= ceiling:
        ok(f"the sweep budget {budget}m + kill-after {kill}m + 10m fits inside "
           f"TimeoutStartSec {ceiling}m")
    else:
        bad(f"the sweep budget {budget}m + kill-after {kill}m + 10m does not fit "
            f"inside TimeoutStartSec {ceiling}m")
    if re.search(r"^trap '.*finish killed 4.*' TERM", code, re.M):
        ok("a SIGTERM from systemd writes state=killed rc=4 before exit")
    else:
        bad("a killed sweep leaves the previous night's status standing")
    # 30 Sep 2026: the live CSV store moved out of the checkout to ~/chester-data.
    if re.search(r'^copy_tree "\$DATA_DIR"\s+"chester-data"', code, re.M) \
            and 'DATA_DIR="${CHESTER_DATA_DIR:-$HOME/chester-data}"' in code:
        ok("the live CSV store (~/chester-data) is swept as its own tree")
    else:
        bad("the live CSV store outside the checkout is not backed up")
    if 'LOG="$LOG_DIR/rclone_sync-$TODAY.log"' in code:
        ok("one log file per run")
    else:
        bad("the sweep's log is not per run")

    # 10 Oct 2026: the inbound files -- the AAII weekly row; 13 Oct 2026 S&P
    # DJI's EPS workbook -- through one function, one copyto of one named file;
    # 12 Oct 2026: and the GLD archive's folder, each file by name (its own copyto).
    pulls = [ln for ln in code.splitlines() if re.search(r"\brclone\s+copyto\b", ln)]
    body = code[code.find("pull_inbox_file() {"):code.find("pull_inbox_file aaii")]
    calls = re.findall(r"^pull_inbox_file (\S+) (\S+) \|\| true$", code, re.M)
    if (len(pulls) == 3 and all('"$src" "$dest"' in x for x in pulls)
            and 'src="$rname:chester-vendor-checks/$folder/$name"' in body
            and 'dest="$DATA_DIR/inbox/$folder/$name"' in body
            and 'rname="$INBOX_RNAME"' in body):
        ok("an inbox pull is one `rclone copyto` of one named file, from the inbox "
           "remote (the main Drive, read-only; never the backup remote), into the inbox")
    else:
        bad(f"the inbox pull is not a single named copyto ({pulls})")
    # S&P DJI's workbook is withdrawn (item 40's forward leg, ruled 17 Oct 2026),
    # so one named file comes back.
    if calls == [("aaii", "aaii-weekly.csv")]:
        ok("one named file comes back: AAII's weekly row (S&P DJI's workbook is "
           "withdrawn)")
    else:
        bad(f"the inbound files are not the one named one ({calls})")
    first = code.find("pull_inbox_file aaii")
    if body and "RC=" not in body and "finish " not in body \
            and first > code.find('log "  prune: $PRUNE"') \
            and code.find("pull_inbox_file aaii") < code.find("finish ok 0"):
        ok("they run after the trees and the prune and never set the sweep's exit")
    else:
        bad("an inbox pull can change the sweep's exit, or runs before the trees")
    if "absent" in body and "lsf" in body:
        ok("an absent remote file is a skip with a log line")
    else:
        bad("an absent inbox file is not handled as a skip")
    eb = code[code.find("pull_etf_archive() {"):code.find("pull_etf_archive || true")]
    if (eb and 'srcdir="$rname:chester-vendor-checks/etf"' in eb
            and 'dir="$DATA_DIR/inbox/etf"' in eb and 'dest="$dir/$f"' in eb
            and "--files-only --max-depth 1" in eb and "rclone sync" not in code
            and "RC=" not in eb and "finish " not in eb and "absent" in eb
            and code.find("pull_etf_archive || true") > code.find('log "  prune: $PRUNE"')
            and code.find("pull_etf_archive || true") < code.find("finish ok 0")):
        ok("the GLD archive pull copies each file of Drive chester-vendor-checks/etf/ "
           "by name into the ETF inbox (copyto, never a sync), after the trees, "
           "never setting the sweep's exit; an empty folder is a skip")
    else:
        bad("the GLD archive pull is not a per-file copyto into the ETF inbox")
    # 17 Oct 2026 (Batch 8 items 50-51): the X pilot's ledgers and digests, each
    # file by name (copyto), stamped with its copy instant, never a sync.
    xb = code[code.find("pull_x_pilot() {"):code.find("pull_x_pilot || true")]
    if (xb and '"$rname:chester-vendor-checks/x-triage/$f"' in xb
            and '"$DATA_DIR/inbox/x-triage/$f"' in xb
            and '"$rname:chester-x-digest/$f"' in xb
            and '"$DATA_DIR/inbox/x-digest/$f"' in xb
            and "x-attention-ledger.csv" in xb and "x-voices-ledger.csv" in xb
            and r"^x-digest-[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$" in xb
            and '>"$dest.copied_at"' in xb and "sha256sum" in xb
            and "RC=" not in xb and "finish " not in xb and "absent" in xb
            and code.find("pull_x_pilot || true") > code.find('log "  prune: $PRUNE"')
            and code.find("pull_x_pilot || true") < code.find("finish ok 0")):
        ok("the X pilot's two ledgers and daily digests come back by name into "
           "inbox/x-triage and inbox/x-digest (copyto, never a sync), each stamped "
           "with its copy instant when its bytes changed, after the trees, never "
           "setting the sweep's exit")
    else:
        bad("the X pilot pull is not a stamped per-file copyto into its inboxes")
    u = (REPO / "deploy/systemd/chester-backup.service").read_text(encoding="utf-8")
    m = re.search(r"^ReadWritePaths=(.*)$", u, re.M)
    rw = m.group(1).split() if m else []
    # The Alpha Lab's inbox (X-2.11) joins w-1-3c's three at the merge of 14 Oct.
    inboxes = ("-%h/chester-data/inbox/aaii", "-%h/chester-data/inbox/spdji",
               "-%h/chester-data/inbox/etf", "-%h/chester-data/inbox/x-triage",
               "-%h/chester-data/inbox/x-digest", "-%h/chester-data/inbox/lab")
    if all(x in rw for x in inboxes) and not [x for x in rw if "chester-data" in x
                                              and x not in inboxes]:
        ok("the sweep's unit may write the six inboxes (AAII, S&P DJI, ETF, the X "
           "pilot's two, the lab's) and nothing else of ~/chester-data")
    else:
        bad("under ProtectSystem=strict an inbox pull cannot write its inbox")


def group_f() -> None:
    """30 Sep 2026: where the live CSV store resolves, so the sweep's tree is it."""
    print(f"\n{LINE}\nF. The CSV store's location -- environment, then .env, then ./data_store\n{LINE}")
    import os  # noqa: PLC0415
    from altdata import secrets, store  # noqa: PLC0415

    old_env, old_path = os.environ.pop("ALTDATA_STORE", None), secrets.ENV_PATH
    try:
        with tempfile.TemporaryDirectory() as d:
            env = Path(d) / "box.env"   # any name: ENV_PATH is patched to it
            env.write_text("FRED_API_KEY=PLACEHOLDER\n"
                           "ALTDATA_STORE=~/chester-data/data_store\n", encoding="utf-8")
            secrets.ENV_PATH = env
            want = os.path.expanduser("~/chester-data/data_store")
            got = store.default_store_dir()
            if got == want:
                ok("with no environment variable, .env's ALTDATA_STORE is used and ~ "
                   "expanded -- a by-hand run from an ssh shell writes where the units do")
            else:
                bad(f"ALTDATA_STORE in the env file was not honoured: {got!r}")
            os.environ["ALTDATA_STORE"] = "data_store"
            if store.default_store_dir() == "data_store":
                ok("the environment wins over .env (CI's explicit data_store, smoke_test)")
            else:
                bad("a .env line overrode the environment")
            del os.environ["ALTDATA_STORE"]
            secrets.ENV_PATH = Path(d) / "absent.env"
            if store.default_store_dir() == "data_store":
                ok("no environment and no .env: ./data_store, as before")
            else:
                bad("the default moved without configuration")
    finally:
        secrets.ENV_PATH = old_path
        os.environ.pop("ALTDATA_STORE", None)
        if old_env is not None:
            os.environ["ALTDATA_STORE"] = old_env

    writers = ["chester-daily-close", "chester-eod", "chester-ibkr-sync",
               "chester-monthly", "chester-morning-anchor", "chester-overnight",
               "chester-weekly"]
    missing = []
    for u in writers:
        t = (REPO / "deploy/systemd" / f"{u}.service").read_text(encoding="utf-8")
        m = re.search(r"^ReadWritePaths=(.*)$", t, re.M)
        if not m or "-%h/chester-data" not in m.group(1).split():
            missing.append(u)
    if not missing:
        ok(f"all {len(writers)} writing units may write ~/chester-data (-%h/chester-data); "
           "under ProtectSystem=strict a store outside the list is read-only")
    else:
        bad(f"these units cannot write the moved store: {missing}")


def group_aud1() -> None:
    """AUD-1 items 1b-1e: the zips pruned on both sides, the disk guard, the
    report archive as its own tree."""
    print(f"\n{LINE}\nAUD-1 1b-1e. THE SPACE LEAK\n{LINE}")
    import subprocess as sp_
    br = REPO / "scripts" / "backup_retention.py"

    def plan(mode_args, stdin):
        r = sp_.run([sys.executable, str(br)] + mode_args, input=stdin,
                    capture_output=True, text=True, timeout=60)
        return r.returncode, [x for x in r.stdout.splitlines() if x.strip()]
    # audit-leftovers-1: Drive keeps the newest 14, the box's own rule.
    zips = [f"chains_2026-09-{d:02d}.zip" for d in range(1, 18)] + ["chains_2026-10-13.zip"]
    names = "\n".join(zips) + "\nREADME.txt\nchains_2026-12-01.zip\n"
    rc, out = plan(["--mode", "zips", "--today", "2026-10-14",
                    "--require", "chains_2026-10-13.zip"], names)
    if rc == 0 and out == zips[:4]:
        ok("1c: Drive's chain zips beyond the newest 14 go by exact name; a future-"
           "dated zip and anything not a dated zip stay")
    else:
        bad(f"1c: the newest-14 plan was {rc} {out}")
    rc, out = plan(["--mode", "zips", "--today", "2026-10-14",
                    "--require", "chains_2026-10-14.zip"], names)
    if rc == 3 and not out:
        ok("1c: nothing is pruned on Drive unless the newest local zip is listed there")
    else:
        bad(f"1c: a missing newest zip still pruned ({rc} {out})")
    local = [f"chains_2026-09-{d:02d}.zip" for d in range(1, 18)]   # 17 zips
    local_lines = "\n".join(f"100;{n}" for n in local)
    with tempfile.TemporaryDirectory() as d:
        rf = Path(d) / "remote.lsf"
        # the remote holds the oldest exactly, the second at a different size,
        # and not the third
        rf.write_text(f"100;{local[0]}\n999;{local[1]}\n100;{local[3]}\n",
                      encoding="utf-8")
        rc, out = plan(["--mode", "local-chains", "--remote", str(rf)], local_lines)
    if rc == 0 and out == [local[0]]:
        ok("1b: the box keeps its newest 14 zips; of the 3 older, only the one the "
           "remote holds as the exact file (same name, same size) is deleted")
    else:
        bad(f"1b: the local plan was {rc} {out}")
    sweep = (REPO / "scripts" / "rclone_sync.sh").read_text(encoding="utf-8")
    if ("finish disk_low 5" in sweep and "(( FREE_BYTES < 2 * DB_BYTES ))" in sweep
            and sweep.index("finish disk_low 5") < sweep.index("altdata.observations snapshot")):
        ok("1d: the sweep refuses to stage a snapshot with under twice the "
           "database's size free, with a named exit (5, disk_low), before staging")
    else:
        bad("1d: the sweep has no disk guard ahead of the snapshot")
    if 'REPORTS_DIR="${CHESTER_REPORTS_DIR:-$REPO/reports}"' in sweep \
            and 'copy_tree "$REPORTS_DIR" "reports"' in sweep:
        ok("1e: the report archive is its own copy tree (CHESTER_REPORTS_DIR)")
    else:
        bad("1e: the report archive is not swept")
    readme = (REPO / "deploy" / "systemd" / "README.md").read_text(encoding="utf-8")
    if "Until AUD-1 they were NOT swept" in readme:
        ok("1e: the README's claim that the archive was already swept is corrected")
    else:
        bad("1e: the README still claims the archive was swept")
    block = sweep[sweep.index("prune_zips() {"):sweep.index("prune_zips || true")]
    if ("rclone deletefile" in block and "rclone delete " not in block
            and "purge" not in block and "sync" not in block
            and block.count("=~ ^chains_[0-9]{4}-[0-9]{2}-[0-9]{2}") == 2):
        ok("1b/1c: both prunes delete one re-checked, exactly named file at a time")
    else:
        bad("1b/1c: a prune deletes by something other than an exact name")

# --- THE SWEEP BUDGET, ON A FAKE CLOCK (14 Oct 2026) -------------------------
# The real rclone_sync.sh, run end to end against a fake rclone that copies
# local trees (honouring --exclude) and advances CHESTER_SWEEP_CLOCK by a set
# number of minutes per tree, so a night of two hours takes a second and nothing
# sleeps. A fake interpreter stands in for the snapshot and the retention plan.
FAKE_RCLONE = r"""#!/usr/bin/env bash
echo "$*" >> "$FAKE_LOG"
verb="$1"; shift
# The crypt remote (audit-leftovers-1) resolves through its base, as rclone does:
# chestercrypt:chester/<x> is <x> under RCLONE_CONFIG_CHESTERCRYPT_REMOTE.
unwrap() {
  local r="$1"
  if [[ "$r" == chestercrypt:* ]]; then
    r="${r#chestercrypt:}"; r="${r#chester}"; r="${r#/}"
    r="${RCLONE_CONFIG_CHESTERCRYPT_REMOTE}/$r"
  fi
  echo "${r%/}"
}
map() { local r; r="$(unwrap "$1")"; echo "$FAKE_ROOT/${r#*:}"; }
case "$verb" in
  obscure)
    cat >/dev/null; echo "obscured"
    ;;
  copy)
    src="$1"; dst="$(map "$2")"; sub="$(unwrap "$2")"; sub="${sub#*:}"; sub="${sub#remote/}"; shift 2
    ex=()
    while (($#)); do
      if [[ "$1" == --exclude ]]; then ex+=("${2#/}"); shift; fi
      shift
    done
    mkdir -p "$dst"
    while IFS= read -r rel; do
      skip=0
      for p in "${ex[@]}"; do [[ "$rel" == $p ]] && skip=1; done
      if ((skip == 0)); then
        mkdir -p "$dst/$(dirname "$rel")"; cp "$src/$rel" "$dst/$rel"
      fi
    done < <(cd "$src" && find . -type f | sed 's|^\./||')
    adv=1
    for pair in ${FAKE_TREE_MIN:-}; do [[ "${pair%%=*}" == "$sub" ]] && adv="${pair#*=}"; done
    echo $(( $(cat "$FAKE_CLOCK") + adv * 60 )) > "$FAKE_CLOCK"
    ;;
  lsf)
    d="$(map "$1")"
    [[ -d "$d" ]] || exit 0
    if [[ " $* " == *" sp "* ]]; then
      for f in "$d"/*; do [[ -f "$f" ]] && echo "$(stat -c %s "$f");$(basename "$f")"; done
    else
      ls -1 "$d"
    fi
    ;;
esac
exit 0
"""
FAKE_PY = r"""#!/usr/bin/env bash
case "$*" in
  *"altdata.observations snapshot"*) printf 'SQLite format 3 fake' > "${@: -1}" ;;
  *"alpha.ledger snapshot"*) printf 'SQLite format 3 alpha' > "${@: -2:1}" ;;
  *"altdata.observations integrity"*) : ;;
  *backup_retention.py*) cat >/dev/null ;;
esac
exit 0
"""


def _sweep(td: Path, tree_min: str, budget: int = 105,
           lab: bool = False) -> tuple[int, str, str, str]:
    import os  # noqa: PLC0415
    import shutil  # noqa: PLC0415
    import subprocess  # noqa: PLC0415
    fw = lambda x: str(x).replace("\\", "/")   # noqa: E731 -- bash wants slashes
    if td.exists():
        shutil.rmtree(td)
    for d in ("bin", "repo/.git", "repo/data/chains", "repo/reports", "backups/chains",
              "state", "logs", "chester-data/inbox/aaii", "remote"):
        (td / d).mkdir(parents=True, exist_ok=True)
    for rel, body in (("repo/data/chester.db", "live"), ("repo/data/chester.db-wal", "w"),
                      ("repo/data/chains/SPY.json", "{}"), ("repo/reports/a.html", "<p>"),
                      ("backups/chains/chains_2026-10-13.zip", "zip"),
                      ("backups/chester-pre-compact-2026-10-20.db", "raw"),
                      ("chester-data/store.csv", "d"), ("state/heartbeat", "hb")):
        (td / rel).write_text(body, encoding="utf-8")
    if lab:
        # The Alpha Lab's parts (alpha-lab-2): its ledger beside chester.db, and
        # the inbox and outbox the sweep copies each way.
        for d in ("chester-data/inbox/lab", "chester-data/outbox/lab"):
            (td / d).mkdir(parents=True, exist_ok=True)
        (td / "repo/data/alpha.db").write_text("alpha", encoding="utf-8")
        (td / "chester-data/outbox/lab/lab-verdicts-2026-10-17.md").write_text(
            "v", encoding="utf-8")
    for name, body in (("rclone", FAKE_RCLONE), ("flock", "#!/usr/bin/env bash\nexit 0\n"),
                       ("python", FAKE_PY)):
        f = td / "bin" / name
        f.write_text(body, encoding="utf-8", newline="\n")
        f.chmod(0o755)
    (td / "clock").write_text("1800000000\n", encoding="utf-8")
    env = {**os.environ,
           "PATH": f"{td / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}",
           "CHESTER_REPO": fw(td / "repo"), "CHESTER_LOG_DIR": fw(td / "logs"),
           "CHESTER_STATE_DIR": fw(td / "state"), "CHESTER_BACKUP_DIR": fw(td / "backups"),
           "CHESTER_DATA_DIR": fw(td / "chester-data"),
           "CHESTER_PYTHON": fw(td / "bin" / "python"),
           # audit-leftovers-1: the backup goes through the crypt remote over
           # fake:remote; the inbox is read from its own remote.
           "CHESTER_RCLONE_BACKUP_REMOTE": "fake:remote",
           "CHESTER_RCLONE_CRYPT_PASSWORD": "fixture-only",
           "CHESTER_RCLONE_CRYPT_SALT": "fixture-only",
           "CHESTER_RCLONE_INBOX_REMOTE": "fake:remote",
           # The lab outbox's own drive.file remote (ruling 1 of 17 Oct 2026).
           "CHESTER_RCLONE_OUTBOX_REMOTE": "fake:remote",
           "CHESTER_SWEEP_BUDGET_MIN": str(budget),
           "CHESTER_SWEEP_CLOCK": fw(td / "clock"), "FAKE_CLOCK": fw(td / "clock"),
           "FAKE_ROOT": fw(td), "FAKE_LOG": fw(td / "rclone.log"),
           "FAKE_TREE_MIN": tree_min}
    env.pop("CHESTER_REPORTS_DIR", None)
    r = subprocess.run([shutil.which("bash"), fw(REPO / "scripts" / "rclone_sync.sh")],
                       env=env, capture_output=True, text=True, timeout=300)
    logs = list((td / "logs").glob("rclone_sync-*.log"))
    log = logs[0].read_text(encoding="utf-8") if logs else r.stderr
    st = td / "state" / "rclone_sync_status"
    return r.returncode, log, st.read_text(encoding="utf-8") if st.exists() else "", fw(td)


def group_budget() -> None:
    """14 Oct 2026: one budget for the sweep, on a fake clock."""
    print(f"\n{LINE}\nBUDGET. One budget for the sweep, on a fake clock (14 Oct 2026)"
          f"\n{LINE}")
    import shutil  # noqa: PLC0415
    if not shutil.which("bash"):
        ok("no bash here; the fake-clock nights run where bash exists")
        return
    with tempfile.TemporaryDirectory() as d:
        td = Path(d) / "night"
        # 1. a normal night: everything runs, in the declared order.
        rc, log, st, _ = _sweep(td, "")
        starts = re.findall(r"  start (\S+) \(cap", log)
        if rc == 0 and st.startswith("state=ok") and starts == [
                "db", "data", "chester-data", "state", "reports", "backups"]:
            ok("a normal night copies every tree, db, data, chester-data, state, "
               "reports, then the zips' backups/ last")
        else:
            bad(f"a normal night: rc {rc}, status {st.strip()!r}, order {starts}")
        if ("prune: ok" in log and "zips: ok" in log and "aaii inbox: skip" in log
                and "deferred" not in log):
            ok("on a normal night the db/ prune, the zip prune and the inbox pulls run")
        else:
            bad("a normal night skipped its housekeeping:\n" + log[-800:])
        rb = td / "remote" / "backups"
        if (rb / "chains" / "chains_2026-10-13.zip").exists() \
                and not (rb / "chester-pre-compact-2026-10-20.db").exists() \
                and (td / "backups" / "chester-pre-compact-2026-10-20.db").exists():
            ok("backups/ excludes /chester-pre-compact-*.db: the compaction's raw "
               "safety copy stays on the box, the zips go up")
        else:
            bad("the compaction's safety copy reached the remote, or the zips did not")
        if not (td / "remote" / "data" / "chester.db").exists() \
                and (td / "remote" / "data" / "chains" / "SPY.json").exists():
            ok("data/ still excludes the live chester.db (run, not read)")
        else:
            bad("data/ uploaded the live chester.db")

        # 2. a tree past the budget: db eats 80 minutes, data's cap is cut to the
        # 23 left less 2 and it uses them; everything after is skipped and named.
        rc, log, st, _ = _sweep(td, "db=80 data=23")
        if "start data (cap 23m, 25m of the budget left)" in log:
            ok("a tree's cap is the smaller of its own (40m) and the minutes left "
               "less 2 (25 - 2 = 23m)")
        else:
            bad("the cap was not cut to the budget:\n" + log[-800:])
        named = "chester-data(budget) state(budget) reports(budget) backups(budget)"
        if rc == 3 and st.startswith("state=partial rc=3") and named in st \
                and log.count("-- sweep budget spent") >= 4 \
                and "SKIP backups -- sweep budget spent" in log:
            ok("with under 3 minutes left a tree is skipped, logged 'SKIP <tree> -- "
               "sweep budget spent' and named <tree>(budget), rc 3")
        else:
            bad(f"a spent budget: rc {rc}, status {st.strip()!r}")
        if "zips: deferred to the next night" in log \
                and "aaii inbox: deferred to the next night" in log:
            ok("the zip prune and the inbox pull wait for the next night")
        else:
            bad("housekeeping ran on a spent budget")

        # 3. a prune with 9 minutes left is deferred, and is not a failure.
        rc, log, st, _ = _sweep(td, "db=96")
        if "prune: deferred to the next night (9m of the sweep budget left)" in log \
                and "rclone lsf fake:remote/db" not in (td / "rclone.log").read_text() \
                and rc == 0 and "db/ prune: deferred to the next night" in st:
            ok("the db/ prune with 9 minutes left is deferred to the next night, "
               "is never listed, and the sweep still exits 0")
        else:
            bad(f"a 9-minute prune: rc {rc}, status {st.strip()!r}\n" + log[-800:])

        # 4. the budget override: a 5-minute budget runs db and data, then stops.
        rc, log, st, _ = _sweep(td, "", budget=5)
        if rc == 3 and "data(budget)" not in st and "state(budget)" in st \
                and "budget=5m" in log:
            ok("CHESTER_SWEEP_BUDGET_MIN overrides the budget (5m: db, data and "
               "chester-data a minute each, then state onward named)")
        else:
            bad(f"the budget override: rc {rc}, status {st.strip()!r}")


def group_lab_budget() -> None:
    """Stitching, week of 19 Oct (meeting b): the Alpha Lab's inbox and outbox
    copies and its alpha-* snapshot prune under the sweep's 105-minute budget."""
    print(f"\n{LINE}\nLAB BUDGET. The Alpha Lab's sweep parts under the budget "
          f"(stitching, week of 19 Oct)\n{LINE}")
    import shutil  # noqa: PLC0415
    if not shutil.which("bash"):
        ok("no bash here; the fake-clock nights run where bash exists")
        return
    with tempfile.TemporaryDirectory() as d:
        td = Path(d) / "night"
        # 1. a normal night with the lab: both prunes, both copies, nothing named.
        rc, log, st, _ = _sweep(td, "", lab=True)
        if (rc == 0 and st.startswith("state=ok") and "alpha prune: ok" in log
                and "start lab-inbox (cap 5m," in log and "lab inbox: ok" in log
                and "start lab-outbox (cap 5m," in log and "lab outbox: ok" in log
                and "lab skipped" not in st
                and (td / "remote" / "db").exists()
                and any(p.name.startswith("alpha-") for p in (td / "remote" / "db").iterdir())
                and not (td / "remote" / "data" / "alpha.db").exists()):
            ok("a normal night: the alpha snapshot goes to db/, its prune runs, the lab "
               "inbox and outbox copy under their own 5-minute caps, nothing is named")
        else:
            bad(f"a normal night with the lab: rc {rc}, status {st.strip()!r}\n"
                + log[-900:])
        # 2. a short night: 3 minutes left at the inbox -- its cap is cut to 1m;
        # the copy takes that minute and the outbox, at 2 left, is skipped, named.
        rc, log, st, _ = _sweep(td, "db=97", lab=True)
        if ("start lab-inbox (cap 1m, 3m of the budget left)" in log
                and "SKIP lab-outbox -- sweep budget spent" in log
                and "lab skipped: lab-outbox(budget)" in st and rc == 0):
            ok("with 3 minutes left the lab inbox runs under a 1-minute cap (left less "
               "2); the outbox, at 2, is skipped and named lab-outbox(budget) in the "
               "status line, and the sweep still exits 0 -- the lab never touches RC")
        else:
            bad(f"a short night: rc {rc}, status {st.strip()!r}\n" + log[-900:])
        # 3. a spent night: both copies skipped and named; both prunes deferred.
        rc, log, st, _ = _sweep(td, "db=100", lab=True)
        if ("SKIP lab-inbox -- sweep budget spent" in log
                and "lab skipped: lab-inbox(budget) lab-outbox(budget)" in st
                and "alpha prune: deferred to the next night" in log
                and "prune: deferred to the next night" in log
                and "rclone lsf fake:remote/db" not in (td / "rclone.log").read_text()):
            ok("a spent night: the lab inbox and outbox are skipped and named, and the "
               "chester and alpha prunes are both deferred to the next night, unlisted")
        else:
            bad(f"a spent night: rc {rc}, status {st.strip()!r}\n" + log[-900:])


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    group_a()
    group_wal()
    group_b()
    group_c()
    group_d()
    group_e()
    group_f()
    group_aud1()
    group_budget()
    group_lab_budget()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
