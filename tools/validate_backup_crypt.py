"""
The encrypted backup's round trip, through REAL rclone (audit-leftovers-1). A DATA
GATE (GATE_KIND = "data"): it needs the rclone binary, which the box and the
laptop have and CI does not, so under GitHub Actions it is "skipped: box-only"
(tools/box_only.py) and anywhere without rclone it prints NOT VALIDATED. No
Google credential: the crypt remote sits on rclone's LOCAL backend, in a
temporary directory, configured exactly as the sweep configures it -- through
scripts/rclone_crypt_env.sh, from environment variables, with an empty
rclone.conf.

  1  a fixture snapshot (a real observation store, snapshot_sqlite, gzip) copied
     through the crypt remote lands as ciphertext: no plaintext byte and no
     plaintext file or directory name on the base remote;
  2  the restore test (tools/restore_drill.py --expect --status, the weekly
     test's own call) restores it through the crypt remote and writes restore_ok;
  3  the same test on a corrupted copy (bytes of the encrypted file flipped on the
     base remote) writes restore_failed with the reason;
  4  the crypt remote with the wrong password cannot read the backup.

    python tools/validate_backup_crypt.py
"""

from __future__ import annotations

import gzip
import os
import shutil
import subprocess
import sys
from pathlib import Path

GATE_KIND = "data"

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78
PASS = FAIL = 0


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def fw(p) -> str:
    return str(p).replace("\\", "/")


def crypt_environment(base: str, password: str, salt: str, conf: Path) -> dict:
    """The environment the sweep builds: rclone_crypt_env.sh's crypt_env, run
    under bash, its RCLONE_CONFIG_CHESTERCRYPT_* exported back to this process."""
    env = {**os.environ, "CHESTER_RCLONE_BACKUP_REMOTE": base,
           "CHESTER_RCLONE_CRYPT_PASSWORD": password, "CHESTER_RCLONE_CRYPT_SALT": salt,
           "RCLONE_CONFIG": fw(conf), "RCLONE_CONFIG_TLOCAL_TYPE": "local"}
    r = subprocess.run([shutil.which("bash"), "-c",
                        f'. "{fw(REPO / "scripts" / "rclone_crypt_env.sh")}"; '
                        f'crypt_env || {{ echo "ERR $CRYPT_ERR"; exit 1; }}; '
                        f'echo "REMOTE=$CRYPT_REMOTE"; env | grep "^RCLONE_CONFIG_CHESTERCRYPT_"'],
                       env=env, capture_output=True, text=True, timeout=120)
    if r.returncode:
        raise RuntimeError(r.stdout + r.stderr)
    for ln in r.stdout.splitlines():
        k, _, v = ln.partition("=")
        if k.startswith("RCLONE_CONFIG_CHESTERCRYPT_"):
            env[k] = v
        elif k == "REMOTE":
            env["_CRYPT_REMOTE"] = v
    for k in ("CHESTER_RCLONE_CRYPT_PASSWORD", "CHESTER_RCLONE_CRYPT_SALT"):
        env.pop(k)
    return env


def main() -> int:
    print(f"{LINE}\nTHE ENCRYPTED BACKUP'S ROUND TRIP (real rclone, local backend)\n{LINE}")
    if shutil.which("rclone") is None or shutil.which("bash") is None:
        print("NOT VALIDATED -- rclone (or bash) is not installed here; this gate runs "
              "on the box and on the laptop")
        return 0
    import gate_tmp                                             # noqa: PLC0415
    from altdata import observations                            # noqa: PLC0415
    td = Path(gate_tmp.mkdtemp("validate_backup_crypt_"))
    os.environ["CHESTER_DB"] = str(td / "default.db")
    conf = td / "rclone.conf"
    conf.write_text("", encoding="utf-8")
    base_dir = td / "base"
    base_dir.mkdir()
    env = crypt_environment(f"tlocal:{fw(base_dir)}", "fixture-pass-not-a-secret",
                            "fixture-salt-not-a-secret", conf)
    remote = env["_CRYPT_REMOTE"]

    # A fixture snapshot, as the sweep stages it.
    live = td / "live.db"
    st = observations.ObservationStore(str(live))
    try:
        st.write_many([{"registry_key": "fred.cpi", "instrument": None,
                        "observed_at": f"2020-{1 + i // 28 % 12:02d}-{1 + i % 28:02d}",
                        "available_at": "2026-10-18T06:30:00+00:00",
                        "value": float(i), "source": "fixture"} for i in range(300)])
    finally:
        st.close()
    stage = td / "stage"
    stage.mkdir()
    snap = stage / "chester-2026-10-18.db"
    info = observations.snapshot_sqlite(live, snap)
    with open(snap, "rb") as fi, gzip.open(stage / (snap.name + ".gz"), "wb") as fo:
        shutil.copyfileobj(fi, fo)
    snap.unlink()
    record = td / "backup_snapshot"
    record.write_text(f"name={snap.name}.gz observations={info['observations']} "
                      f"at=2026-10-18T02:31:00-04:00\n", encoding="utf-8")

    def rclone(*args, e=env):
        return subprocess.run(["rclone", *args], env=e, capture_output=True, text=True,
                              timeout=300)
    r = rclone("copy", fw(stage), f"{remote}/db")
    files = [p for p in base_dir.rglob("*") if p.is_file()]
    plain = b"SQLite format 3"
    leaked = [p for p in files if plain in p.read_bytes()
              or "chester" in p.name or "db" == p.parent.name]
    check(r.returncode == 0 and files and not leaked and conf.read_text() == "",
          f"1: the snapshot crosses the crypt remote as ciphertext -- no plaintext byte, "
          f"file name or directory name on the base, rclone.conf still empty "
          f"({len(files)} file(s); rc {r.returncode})")

    def restore(e) -> tuple[int, str, str]:
        status = td / "restore_test_status"
        status.unlink(missing_ok=True)
        p = subprocess.run([sys.executable, "-m", "tools.restore_drill", "--remote",
                            remote, "--live", fw(live), "--expect", fw(record),
                            "--status", fw(status)],
                           cwd=REPO, env=e, capture_output=True, text=True, timeout=600)
        return p.returncode, p.stdout, (status.read_text(encoding="utf-8")
                                        if status.exists() else "")
    rc, out, st_line = restore(env)
    check(rc == 0 and st_line.startswith("state=restore_ok ") and "RESULT: restorable" in out,
          f"2: the restore test restores it through the crypt remote: restore_ok "
          f"({st_line.strip()[:80]})")

    wrong = crypt_environment(f"tlocal:{fw(base_dir)}", "the-wrong-password",
                              "fixture-salt-not-a-secret", conf)
    rc4, out4, st4 = restore(wrong)
    check(rc4 != 0 and st4.startswith("state=restore_failed "),
          f"4: with the wrong password the backup cannot be read ({st4.strip()[:90]})")

    enc = max(files, key=lambda p: p.stat().st_size)
    data = bytearray(enc.read_bytes())
    for i in range(64, min(len(data), 4096), 97):
        data[i] ^= 0xFF
    enc.write_bytes(bytes(data))
    rc3, out3, st3 = restore(env)
    check(rc3 != 0 and st3.startswith("state=restore_failed ") and "detail=" in st3,
          f"3: a corrupted copy fails the restore test, with the reason "
          f"({st3.strip()[:100]})")

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    from box_only import ci_skip  # noqa: E402
    _skip = ci_skip(__file__)
    sys.exit(main() if _skip is None else _skip)
