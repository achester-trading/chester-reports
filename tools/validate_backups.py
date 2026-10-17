"""
The audit's leftovers, part 1 (audit-leftovers-1, 17 Oct 2026): the encrypted
backups, the restore test, retention on both sides, the sweep's trees, the lock
helper and the append-only triggers -- the checks with no other home. (Incremental
pulls are validate_audit_1.py's group E; the heartbeat's restore field is
validate_heartbeat_caller.sh's; rclone's variables in the secrets scan are
validate_secrets.py's group I; the real crypt round trip, which needs rclone, is
the data gate validate_backup_crypt.py.) No network, no live store, no model, no
Google credential.

  G  THE CRYPT REMOTE COMES FROM THE ENVIRONMENT. scripts/rclone_crypt_env.sh
     reads CHESTER_RCLONE_BACKUP_REMOTE / _CRYPT_PASSWORD / _CRYPT_SALT only,
     obscures the two secrets from stdin (never argv), turns filename and
     directory encryption on, and refuses (CRYPT_ERR) when one is missing; run
     under bash with a fake rclone.
  H  THE RESTORE TEST on a fixture snapshot: restore_ok when the copy restores,
     passes integrity_check and holds the recorded observations count;
     restore_failed on a corrupted copy, a wrong count and a snapshot the record
     does not name; the status line written each time.
  I  RETENTION ON BOTH SIDES: one fixture listing pruned by the box's rule and by
     Drive's gives the same deletions; db/'s rule is unchanged.
  J  THE SWEEP: every tree, reports/ included, goes to the crypt remote; the
     plaintext remote is no longer a target; the snapshot's row count is recorded
     for the restore test; the inbox reads its own remote.
  K  THE LOCK HELPER: open_writer gives WAL, the busy timeout and the writer's
     name; every scheduled writer opens the store through it and no other way.
  L  THE APPEND-ONLY TRIGGERS on a fixture store: UPDATE and DELETE refused; the
     one maintenance path deletes, unseen by a second connection and gone after
     its commit; aud-1's compaction works through it; write throughput measured.

    python tools/validate_backups.py
"""

from __future__ import annotations

import gzip
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gate_tmp                   # noqa: E402  -- removed at exit

TD = Path(gate_tmp.mkdtemp("validate_backups_"))
os.environ["CHESTER_DB"] = str(TD / "default.db")
from altdata import observations  # noqa: E402

PASS = FAIL = 0
LINE = "=" * 78


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def fw(p) -> str:
    return str(p).replace("\\", "/")


def fixture_store(path: Path, n: int) -> None:
    st = observations.ObservationStore(str(path))
    try:
        st.write_many([{"registry_key": "fred.cpi", "instrument": None,
                        "observed_at": f"2020-01-{1 + i % 28:02d}",
                        "available_at": f"2026-10-{1 + i // 28 % 28:02d}T00:00:{i % 60:02d}+00:00",
                        "value": float(i), "source": "fixture"} for i in range(n)])
    finally:
        st.close()


# ---------------------------------------------------------------------------
def group_g() -> None:
    head("G. THE CRYPT REMOTE COMES FROM THE ENVIRONMENT")
    sh = (REPO / "scripts" / "rclone_crypt_env.sh").read_text(encoding="utf-8")
    check("printf '%s' \"$pw\" | rclone obscure -" in sh
          and "printf '%s' \"$salt\" | rclone obscure -" in sh
          and not re.search(r"rclone obscure\s+[\"'$]", sh),
          "the password and salt reach rclone obscure on stdin, never as an argument")
    check("FILENAME_ENCRYPTION=standard" in sh and "DIRECTORY_NAME_ENCRYPTION=true" in sh,
          "file and directory names are encrypted as well as contents")
    reads = set(re.findall(r"\$\{(CHESTER_\w+)", sh))
    check(reads == {"CHESTER_RCLONE_BACKUP_REMOTE", "CHESTER_RCLONE_CRYPT_PASSWORD",
                    "CHESTER_RCLONE_CRYPT_SALT"},
          f"it reads exactly the three settings, from the environment ({sorted(reads)})")
    bash = shutil.which("bash")
    if not bash:
        print("  NOTE  no bash here: the behaviour half of G runs in CI")
        return
    bin_ = TD / "g_bin"
    bin_.mkdir(exist_ok=True)
    fake = bin_ / "rclone"
    fake.write_text("#!/usr/bin/env bash\n[[ \"$1\" == obscure ]] && { read -r x; "
                    "echo \"OBSCURED(${#x})\"; exit 0; }\nexit 1\n", encoding="utf-8",
                    newline="\n")
    fake.chmod(0o755)
    script = (f'. "{fw(REPO / "scripts" / "rclone_crypt_env.sh")}"; '
              'if crypt_env; then echo "OK $CRYPT_REMOTE"; '
              'env | grep "^RCLONE_CONFIG_CHESTERCRYPT_" | sort; '
              'else echo "ERR $CRYPT_ERR"; fi')
    base = {**os.environ, "PATH": f"{fw(bin_)}{os.pathsep}{os.environ.get('PATH', '')}"}
    for k in ("CHESTER_RCLONE_BACKUP_REMOTE", "CHESTER_RCLONE_CRYPT_PASSWORD",
              "CHESTER_RCLONE_CRYPT_SALT"):
        base.pop(k, None)
    full = {**base, "CHESTER_RCLONE_BACKUP_REMOTE": "chesterbak:chester-backups",
            "CHESTER_RCLONE_CRYPT_PASSWORD": "fixture-pass-12",
            "CHESTER_RCLONE_CRYPT_SALT": "fixture-salt-1"}
    r = subprocess.run([bash, "-c", script], env=full, capture_output=True, text=True,
                       timeout=60)
    out = r.stdout
    check(out.startswith("OK chestercrypt:chester")
          and "RCLONE_CONFIG_CHESTERCRYPT_TYPE=crypt" in out
          and "RCLONE_CONFIG_CHESTERCRYPT_REMOTE=chesterbak:chester-backups" in out
          and "RCLONE_CONFIG_CHESTERCRYPT_PASSWORD=OBSCURED(15)" in out
          and "RCLONE_CONFIG_CHESTERCRYPT_PASSWORD2=OBSCURED(14)" in out
          and "fixture-pass" not in out and "fixture-salt" not in out,
          f"with all three set: the crypt remote, its secrets only obscured "
          f"({out.splitlines()[0] if out else r.stderr[:120]})")
    for drop, why in (("CHESTER_RCLONE_BACKUP_REMOTE", "BACKUP_REMOTE is unset"),
                      ("CHESTER_RCLONE_CRYPT_SALT", "CRYPT_SALT is unset")):
        env = {k: v for k, v in full.items() if k != drop}
        r = subprocess.run([bash, "-c", script], env=env, capture_output=True,
                           text=True, timeout=60)
        check(r.stdout.startswith("ERR") and why in r.stdout
              and "RCLONE_CONFIG_CHESTERCRYPT" not in r.stdout,
              f"without {drop}: refused, by name, and no remote is defined")


# ---------------------------------------------------------------------------
def group_h() -> None:
    from tools import restore_drill as rd
    head("H. THE RESTORE TEST ON A FIXTURE SNAPSHOT")
    src = TD / "h_live.db"
    fixture_store(src, 500)
    remote = TD / "h_remote" / "db"
    remote.mkdir(parents=True)
    snap = TD / "h_stage" / "chester-2026-10-18.db"
    snap.parent.mkdir()
    info = observations.snapshot_sqlite(src, snap)
    with open(snap, "rb") as fi, gzip.open(remote / (snap.name + ".gz"), "wb") as fo:
        shutil.copyfileobj(fi, fo)
    record = {"name": snap.name + ".gz", "observations": info["observations"]}

    def runner_for(root: Path):
        def run(args):
            if args[0] == "lsf":
                return "\n".join(p.name for p in sorted(root.iterdir()))
            if args[0] == "copy":
                shutil.copy(root / Path(args[1]).name, args[2])
                return ""
            raise ValueError(args)
        return run
    r = rd.drill("crypt:chester", str(src), runner=runner_for(remote), expect=record,
                 today="2026-10-18")
    status = TD / "h_status"
    rd.write_status(str(status), r)
    st = status.read_text(encoding="utf-8")
    check(r["ok"] and r["restored_observations"] == 500 == r["expected_observations"]
          and st.startswith("state=restore_ok ") and "snapshot=chester-2026-10-18.db.gz" in st
          and r["tmp_removed"],
          f"the snapshot restores, passes integrity_check and holds the 500 "
          f"observations recorded at snapshot time; restore_ok written")
    bad = TD / "h_bad" / "db"
    bad.mkdir(parents=True)
    raw = (remote / (snap.name + ".gz")).read_bytes()
    (bad / (snap.name + ".gz")).write_bytes(raw[: len(raw) // 2] + b"\x00" * 64)
    r = rd.drill("crypt:chester", None, runner=runner_for(bad), expect=record,
                 today="2026-10-18")
    rd.write_status(str(status), r)
    st = status.read_text(encoding="utf-8")
    check(not r["ok"] and st.startswith("state=restore_failed ") and "detail=" in st,
          f"a corrupted copy fails, and restore_failed carries the reason "
          f"({(r.get('error') or r.get('integrity') or '')[:60]})")
    r = rd.drill("crypt:chester", None, runner=runner_for(remote),
                 expect={**record, "observations": 499}, today="2026-10-18")
    check(not r["ok"] and "500 restored against 499 recorded" in str(r.get("error")),
          "a count that does not match the record fails, saying both counts")
    r = rd.drill("crypt:chester", None, runner=runner_for(remote),
                 expect={**record, "name": "chester-2026-10-19.db.gz"}, today="2026-10-19")
    check(not r["ok"] and "recorded chester-2026-10-19.db.gz" in str(r.get("error")),
          "a remote whose newest snapshot is not the one recorded fails")
    rec = TD / "h_record"
    rec.write_text("name=chester-2026-10-18.db.gz observations=500 at=2026-10-18T02:31:00-04:00\n",
                   encoding="utf-8")
    check(rd.read_record(str(rec)) == {"name": "chester-2026-10-18.db.gz",
                                       "observations": 500,
                                       "at": "2026-10-18T02:31:00-04:00"}
          and rd.read_record(str(TD / "absent")) is None,
          "the sweep's record reads back (name, observations, at)")


# ---------------------------------------------------------------------------
def group_i() -> None:
    import importlib.util
    head("I. RETENTION: THE SAME RULE ON BOTH SIDES")
    spec = importlib.util.spec_from_file_location(
        "backup_retention", REPO / "scripts" / "backup_retention.py")
    br = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(br)
    import datetime as dt
    names = [f"chains_2026-09-{d:02d}.zip" for d in range(1, 31)]
    local = {n: 100 for n in names}
    remote = dict(local)
    on_box = br.plan_local(local, remote)
    on_drive = br.plan_zips(names, dt.date(2026, 10, 1))
    check(on_box == on_drive == names[:16],
          f"one listing of 30 zips: the box and Drive delete the same 16, keeping the "
          f"newest {br.LOCAL_KEEP} on each side")
    check(br.plan_zips(names + ["chains_2026-11-30.zip"], dt.date(2026, 10, 1)) == names[:16]
          and br.plan_local({**local, names[0]: 99}, remote) == names[1:16],
          "Drive never deletes a future-dated zip; the box never deletes one Drive does "
          "not hold exactly")
    keep, delete = br.plan([f"chester-2026-{m:02d}-{d:02d}.db.gz"
                            for m in (8, 9, 10) for d in range(1, 29)], dt.date(2026, 10, 28))
    check(delete and "chester-2026-10-28.db.gz" in keep
          and "chester-2026-08-28.db.gz" in keep and "chester-2026-08-02.db.gz" in delete,
          "db/'s 14 daily / 8 weekly / monthly rule is unchanged")


# ---------------------------------------------------------------------------
def group_j() -> None:
    head("J. THE SWEEP: ENCRYPTED, EVERY TREE, THE RECORD")
    sw = (REPO / "scripts" / "rclone_sync.sh").read_text(encoding="utf-8")
    trees = re.findall(r'^copy_tree "\$([^"]+)"\s+"([\w-]+)"', sw, re.M)
    check('if copy_tree "$STAGE" "db" 20; then' in sw
          and [t for _, t in trees] == ["data", "chester-data", "state", "reports",
                                        "backups"]
          and ("REPORTS_DIR", "reports") in trees,
          f"the sweep's trees, db/ first and reports/ among them "
          f"({['db'] + [t for _, t in trees]})")
    check('REMOTE="$CRYPT_REMOTE"' in sw and "CHESTER_RCLONE_REMOTE:-}\"\n" not in sw
          and not re.search(r'^REMOTE="\$\{CHESTER_RCLONE_REMOTE', sw, re.M)
          and sw.index("crypt_env || finish no_crypt 1") < sw.index('copy_tree "$STAGE"'),
          "every tree goes to the crypt remote; the plaintext remote is no longer a "
          "target, and without the crypt settings the sweep exits before copying")
    check("SNAP_RECORD=\"$STATE_DIR/backup_snapshot\"" in sw
          and "printf 'name=%s observations=%s at=%s\\n'" in sw,
          "the snapshot's row count is recorded for the restore test")
    bash = shutil.which("bash")
    if bash:
        sample = "snapshot ok /x/chester-2026-10-18.db (123,456 bytes, 98,765 observations)"
        line = re.search(r"SNAP_ROWS=\"\$\(printf '%s\\n' \"\$SNAP_OUT\" \| (.*)\)\"", sw)
        r = subprocess.run([bash, "-c", f"printf '%s\\n' '{sample}' | {line.group(1)}"],
                           capture_output=True, text=True, timeout=30) if line else None
        check(r is not None and r.stdout.strip() == "98765",
              f"the record's count is parsed from the snapshot line "
              f"({r.stdout.strip() if r else 'no SNAP_ROWS line'})")
    check(sw.count('rname="$INBOX_RNAME"') == 3 and "${REMOTE%%:*}" not in sw,
          "the three inbound pulls read the inbox remote, never the backup remote")
    unit = (REPO / "deploy" / "systemd" / "chester-backup.service").read_text(encoding="utf-8")
    check("EnvironmentFile=-%h/chester-reports/.env" in unit,
          "the backup unit reads the crypt settings from .env")


# ---------------------------------------------------------------------------
def scheduled_writer_files() -> list[str]:
    """The modules the scheduled pulls run, which must open the store through
    observations.open_writer: every official and external writer, the price, FRED
    and prediction-market writers, the CSV store's dual write, the publication
    runner, fed funds, the loggers, and the derived passes the pulls run."""
    from altdata import feeds
    files = {f"altdata/sources/{n}.py" for n in feeds.OFFICIAL_WRITERS + feeds.EXTERNAL_WRITERS}
    files |= {"altdata/sources/yfinance_source.py", "altdata/sources/fred.py",
              "altdata/sources/prediction_markets.py", "altdata/store.py",
              "altdata/sources/_publication.py", "altdata/fed_funds.py",
              "altdata/market_features.py", "altdata/correlation.py",
              "altdata/crypto_basket.py", "altdata/macro_6e.py",
              "altdata/sources/llama.py", "altdata/sources/fedboard.py"}
    files |= {p.relative_to(REPO).as_posix() for p in (REPO / "altdata" / "loggers").glob("*.py")}
    return sorted(f for f in files if (REPO / f).exists())


def group_k() -> None:
    head("K. THE LOCK HELPER, AND EVERY SCHEDULED WRITER THROUGH IT")
    st = observations.open_writer("validate_backups", str(TD / "k.db"))
    try:
        mode = st.conn.execute("PRAGMA journal_mode").fetchone()[0]
        busy = st.conn.execute("PRAGMA busy_timeout").fetchone()[0]
        check(mode == "wal" and busy == observations.BUSY_TIMEOUT_MS == 5000
              and st.writer == "validate_backups",
              f"open_writer: WAL ({mode}), busy timeout {busy} ms, the writer's name")
    finally:
        st.close()
    files = scheduled_writer_files()
    offenders = []
    for f in files:
        for n, line in enumerate((REPO / f).read_text(encoding="utf-8").splitlines(), 1):
            s = line.strip()
            if s.startswith("#"):
                continue
            if re.search(r"\bObservationStore\(|sqlite3\.connect\(", s):
                offenders.append(f"{f}:{n}")
    check(len(files) > 50 and not offenders,
          f"all {len(files)} scheduled writer modules open the store through "
          f"open_writer, none another way" + (f"; offenders {offenders[:6]}" if offenders else ""))
    probe = TD / "k_probe.py"
    probe.write_text("from altdata import observations\nst = observations.ObservationStore()\n",
                     encoding="utf-8")
    hit = any(re.search(r"\bObservationStore\(", ln)
              for ln in probe.read_text(encoding="utf-8").splitlines())
    check(hit, "and the scan catches a direct open (a probe file)")


# ---------------------------------------------------------------------------
def group_l() -> None:
    head("L. THE APPEND-ONLY TRIGGERS")
    path = TD / "l.db"
    fixture_store(path, 50)
    conn = sqlite3.connect(str(path))
    observations.install_append_only(conn)
    check(observations.append_only_installed(conn), "the migration installs both triggers")

    def refused(sql: str) -> bool:
        try:
            conn.execute(sql)
            conn.commit()
            return False
        except sqlite3.DatabaseError as exc:
            conn.rollback()
            return "append-only" in str(exc)
    check(refused("UPDATE observations SET value_num = 0 WHERE rowid = 1")
          and refused("DELETE FROM observations WHERE rowid = 1"),
          "a fixture UPDATE and a fixture DELETE are refused")
    n0 = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    seen_by_other = None
    with observations.maintenance(conn, "validate_backups"):
        conn.execute("DELETE FROM observations WHERE rowid IN (1, 2)")
        other = sqlite3.connect(str(path), timeout=0.2)
        try:
            seen_by_other = other.execute(
                f"SELECT COUNT(*) FROM {observations.MAINTENANCE_TABLE}").fetchone()[0]
        finally:
            other.close()
    n1 = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    left = conn.execute(f"SELECT COUNT(*) FROM {observations.MAINTENANCE_TABLE}").fetchone()[0]
    check(n1 == n0 - 2 and seen_by_other == 0 and left == 0
          and refused("DELETE FROM observations WHERE rowid = 3"),
          "the one maintenance path deletes; a second connection never sees its row; "
          "the row is gone after the commit, and the triggers stand again")
    conn.close()
    # aud-1's compaction tool, through the path, on a store with the triggers.
    from altdata import compact_fred
    cpath = TD / "l_compact.db"
    st = observations.ObservationStore(str(cpath))
    try:
        st.write_many([{"registry_key": "fred.cpi", "instrument": None,
                        "observed_at": "2026-09-01", "available_at": f"2026-10-{d:02d}T00:00:00+00:00",
                        "value": 1.0, "source": "fred"} for d in range(1, 6)])
        observations.install_append_only(st.conn)
    finally:
        st.close()
    rc = compact_fred._main(["--apply", "--db", str(cpath),  # noqa: SLF001
                             "--backup", str(TD / "l_compact_backup.db")])
    c = sqlite3.connect(str(cpath))
    try:
        rows = c.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        intact = observations.append_only_installed(c)
    finally:
        c.close()
    check(rc == 0 and rows == 1 and intact,
          f"the compaction path still works with the triggers installed (rc {rc}, "
          f"5 vintages of one value -> {rows})")
    # Throughput: an INSERT fires neither trigger.
    timings: dict = {}
    for label, install, rep in [(lb, ins, k) for k in range(3)
                                for lb, ins in (("without", False), ("with", True))]:
        p = TD / f"l_speed_{label}_{rep}.db"
        s = observations.ObservationStore(str(p))
        try:
            if install:
                observations.install_append_only(s.conn)
            rows_ = [{"registry_key": "bench.x", "instrument": None,
                      "observed_at": f"2026-{1 + i // 28 % 12:02d}-{1 + i % 28:02d}",
                      "available_at": f"2026-10-18T{i // 3600 % 24:02d}:{i // 60 % 60:02d}:{i % 60:02d}+00:00",
                      "value": float(i), "source": "bench"} for i in range(20000)]
            t = time.perf_counter()
            s.write_many(rows_)
            # The best of three a side: the floor is the cost, the rest is noise.
            timings[label] = min(timings.get(label, 1e9), time.perf_counter() - t)
        finally:
            s.close()
    ratio = timings["with"] / max(timings["without"], 1e-9)
    print(f"  NOTE  20,000 inserts: {timings['without']:.3f}s without the triggers, "
          f"{timings['with']:.3f}s with (ratio {ratio:.2f})")
    check(ratio < 1.5, f"write throughput is unchanged within noise (ratio {ratio:.2f})")


def main() -> int:
    print(f"{LINE}\nAUDIT-LEFTOVERS-1: BACKUPS, THE RESTORE TEST, THE LOCK HELPER, THE "
          f"TRIGGERS\n{LINE}")
    for g in (group_g, group_h, group_i, group_j, group_k, group_l):
        try:
            g()
        except Exception as exc:                              # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
