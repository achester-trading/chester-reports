"""
The restore drill: prove last night's backup restores. (AUD-2 item 5, ruled 14 Oct
2026; docs/runbooks/restore.md)

    python -m tools.restore_drill                  # CHESTER_RCLONE_REMOTE's db/
    python -m tools.restore_drill --remote gdrive:chester-backups --live data/chester.db

No restore had ever been tested. A backup nobody has restored is a hope, so this
does the restore on a schedule and says what it found:

  1. lists the remote's db/ (rclone lsf) and picks the newest dated snapshot,
     chester-YYYY-MM-DD.db.gz, the name scripts/rclone_sync.sh stages;
  2. copies that one file into a temporary directory (rclone copy, REMOTE ->
     LOCAL only: the remote is never written, listed beyond db/, or pruned);
  3. gunzips it there and runs altdata.observations.integrity_check on it;
  4. prints each table's row count beside the live store's, the live store opened
     read-only (SQLite mode=ro), so the gap a restore would lose is visible;
  5. deletes the temporary directory, whatever happened.

It writes nothing outside that directory. The two rclone verbs are the only ones
it will run; anything else raises before rclone is called.

Exit codes: 0 restored and clean; 1 environment (no remote configured, no rclone);
2 no snapshot found, or the restored copy failed integrity_check.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Optional

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

SNAPSHOT = re.compile(r"^chester-(\d{4}-\d{2}-\d{2})\.db\.gz$")
READ_VERBS = ("lsf", "copy")

Runner = Callable[[list], str]


def rclone(args: list) -> str:
    """The real runner. Only the two read verbs; the remote is the SOURCE of a
    copy, never its destination (checked by drill() before this is called)."""
    if not args or args[0] not in READ_VERBS:
        raise ValueError(f"the drill runs only rclone {READ_VERBS}, not {args[:1]}")
    if shutil.which("rclone") is None:
        raise FileNotFoundError("rclone is not installed")
    out = subprocess.run(["rclone", *args], capture_output=True, text=True,
                         timeout=30 * 60)
    if out.returncode:
        raise RuntimeError(f"rclone {args[0]} exited {out.returncode}: "
                           f"{out.stderr.strip()[:300]}")
    return out.stdout


def newest(listing: str) -> Optional[tuple[str, str]]:
    """(file name, date) of the newest dated snapshot in an lsf listing."""
    found = [(m.group(1), n.strip()) for n in listing.splitlines()
             if (m := SNAPSHOT.match(n.strip()))]
    if not found:
        return None
    d, name = max(found)
    return name, d


def table_counts(path: Path, ro: bool = True) -> dict[str, int]:
    uri = f"file:{path}?mode=ro" if ro else str(path)
    conn = sqlite3.connect(uri, uri=ro)
    try:
        names = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE "
            "'sqlite_%' ORDER BY name")]
        return {n: conn.execute(f'SELECT COUNT(*) FROM "{n}"').fetchone()[0]
                for n in names}
    finally:
        conn.close()


def drill(remote: str, live: Optional[str], runner: Runner = rclone,
          today: Optional[str] = None) -> dict:
    """The drill. Never writes outside its temporary directory, which it removes."""
    from altdata import observations                            # noqa: PLC0415
    out: dict = {"remote": remote, "ok": False}
    listing = runner(["lsf", f"{remote}/db", "--files-only"])
    pick = newest(listing)
    if pick is None:
        out["error"] = f"no chester-YYYY-MM-DD.db.gz under {remote}/db"
        out["rc"] = 2
        return out
    name, day = pick
    today = today or dt.date.today().isoformat()
    out.update(snapshot=name, snapshot_date=day,
               age_days=(dt.date.fromisoformat(today) - dt.date.fromisoformat(day)).days)
    tmp = Path(tempfile.mkdtemp(prefix="restore_drill_"))
    out["tmp"] = str(tmp)
    try:
        runner(["copy", f"{remote}/db/{name}", str(tmp)])
        gz = tmp / name
        db = tmp / name[:-3]
        with gzip.open(gz, "rb") as src, open(db, "wb") as dst:
            shutil.copyfileobj(src, dst)
        out["restored_bytes"] = db.stat().st_size
        problems = observations.integrity_check(db)
        out["integrity"] = "ok" if not problems else "; ".join(problems[:5])
        if problems:
            out["rc"] = 2
            return out
        restored = table_counts(db)
        live_counts: dict[str, int] = {}
        if live and Path(live).exists():
            try:
                live_counts = table_counts(Path(live))
            except sqlite3.Error as exc:
                out["live_error"] = f"{type(exc).__name__}: {exc}"
        out["tables"] = [{"table": t, "restored": restored.get(t),
                          "live": live_counts.get(t)}
                         for t in sorted(set(restored) | set(live_counts))]
        out["ok"], out["rc"] = True, 0
        return out
    except (OSError, EOFError, gzip.BadGzipFile, sqlite3.Error) as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
        out["rc"] = 2
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        out["tmp_removed"] = not tmp.exists()


def report(r: dict) -> str:
    lines = [f"restore drill: remote {r['remote']}"]
    if r.get("snapshot"):
        lines.append(f"  newest snapshot {r['snapshot']} ({r['age_days']} day(s) old)"
                     f", {r.get('restored_bytes', 0):,} bytes restored")
    if r.get("integrity"):
        lines.append(f"  integrity_check: {r['integrity']}")
    if r.get("error"):
        lines.append(f"  FAILED: {r['error']}")
    if r.get("live_error"):
        lines.append(f"  live store not read: {r['live_error']}")
    if r.get("tables"):
        w = max(len(t["table"]) for t in r["tables"])
        lines.append(f"  {'table':<{w}}  {'restored':>12}  {'live':>12}  {'live - restored':>16}")
        for t in r["tables"]:
            a, b = t["restored"], t["live"]
            gap = "" if a is None or b is None else f"{b - a:+,}"
            lines.append(f"  {t['table']:<{w}}  {'-' if a is None else f'{a:,}':>12}  "
                         f"{'-' if b is None else f'{b:,}':>12}  {gap:>16}")
    lines.append(f"  temporary directory removed: {r.get('tmp_removed')}")
    lines.append("  RESULT: " + ("restorable" if r.get("ok") else "NOT restorable"))
    return "\n".join(lines)


def main(argv: Optional[list] = None) -> int:
    from altdata import observations, secrets                   # noqa: PLC0415
    ap = argparse.ArgumentParser(description="Restore last night's db/ snapshot "
                                             "into a temporary directory and check it.")
    ap.add_argument("--remote", default=None,
                    help="rclone remote and path (default CHESTER_RCLONE_REMOTE)")
    ap.add_argument("--live", default=None,
                    help="the live store to compare against, read-only "
                         "(default the observations store)")
    a = ap.parse_args(argv)
    remote = a.remote or secrets.get("CHESTER_RCLONE_REMOTE")
    if not remote:
        print("restore drill: CHESTER_RCLONE_REMOTE is unset and no --remote given")
        return 1
    try:
        r = drill(remote.rstrip("/"), a.live or str(observations.DEFAULT_DB))
    except FileNotFoundError as exc:
        print(f"restore drill: {exc}")
        return 1
    except Exception as exc:                                    # noqa: BLE001
        print(f"restore drill: FAILED {type(exc).__name__}: {exc}")
        return 2
    print(report(r))
    return int(r.get("rc", 2))


if __name__ == "__main__":
    raise SystemExit(main())
