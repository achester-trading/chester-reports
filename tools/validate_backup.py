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
    if deletes and all('rclone deletefile "$REMOTE/db/$name"' in ln for ln in deletes):
        ok("the only removal is `rclone deletefile \"$REMOTE/db/$name\"`")
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
    copies = [ln for ln in code.splitlines() if re.search(r"\brclone\s+copy\b", ln)]
    prev = code.splitlines()
    capped = all(
        re.search(r'timeout --kill-after=\S+ "\$\{mins\}m"',
                  prev[prev.index(ln) - 1] + ln) for ln in copies)
    if copies and capped and "$RCLONE_LIMITS" in copies[0]:
        ok("every rclone copy runs under its own timeout and the stall limits")
    else:
        bad("an rclone copy can run uncapped")
    caps = [int(x) for x in re.findall(r'^\s*(?:if\s+)?copy_tree "[^"]+"\s+"[\w-]+"\s+(\d+)',
                                        code, re.M)]
    u = (REPO / "deploy/systemd/chester-backup.service").read_text(encoding="utf-8")
    tm = re.search(r"^TimeoutStartSec=(?:(\d+)h)?(?:(\d+)min)?\s*$", u, re.M)
    ceiling = (int(tm.group(1) or 0) * 60 + int(tm.group(2) or 0)) if tm else 0
    if len(caps) == 5 and ceiling > sum(caps) + 5 + 10:
        ok(f"TimeoutStartSec {ceiling}m sits above the tree caps "
           f"({'+'.join(map(str, caps))}={sum(caps)}m) plus the prune")
    else:
        bad(f"TimeoutStartSec {ceiling}m does not clear the caps {caps}")
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

    # 10 Oct 2026: the one inbound file, the AAII weekly row.
    pulls = [ln for ln in code.splitlines() if re.search(r"\brclone\s+copyto\b", ln)]
    body = code[code.find("pull_aaii_weekly() {"):code.find("pull_aaii_weekly || true")]
    if (len(pulls) == 1 and '"$src" "$dest"' in pulls[0]
            and 'src="$rname:chester-vendor-checks/aaii/aaii-weekly.csv"' in body
            and 'dest="$DATA_DIR/inbox/aaii/aaii-weekly.csv"' in body
            and 'rname="${REMOTE%%:*}"' in body):
        ok("the AAII pull is one `rclone copyto` of one named file, the remote's "
           "name with its path replaced, into the inbox")
    else:
        bad(f"the AAII pull is not a single named copyto ({pulls})")
    if body and "RC=" not in body and "finish " not in body \
            and code.find("pull_aaii_weekly || true") > code.find('log "  prune: $PRUNE"') \
            and code.find("pull_aaii_weekly || true") < code.find("finish ok 0"):
        ok("it runs after the trees and the prune and never sets the sweep's exit")
    else:
        bad("the AAII pull can change the sweep's exit, or runs before the trees")
    if "absent" in body and "lsf" in body:
        ok("an absent remote file is a skip with a log line")
    else:
        bad("an absent AAII file is not handled as a skip")
    u = (REPO / "deploy/systemd/chester-backup.service").read_text(encoding="utf-8")
    m = re.search(r"^ReadWritePaths=(.*)$", u, re.M)
    if m and "-%h/chester-data/inbox/aaii" in m.group(1).split():
        ok("the sweep's unit may write the AAII inbox and nothing else of ~/chester-data")
    else:
        bad("under ProtectSystem=strict the AAII pull cannot write its inbox")


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
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
