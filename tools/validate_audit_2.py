"""
Validation gate for AUD-2, the parts that fit no existing gate. (ruled 14 Oct 2026;
docs/briefs/aud-2-notes.md)

The settings rules are validate_deploy's (group J); the units, their memory caps
and the backup's end are validate_systemd_units's; the meter's rows and the close's
line are validate_stack's (group M), the Monthly's lines validate_monthly_stack's.
What is left lives here, on fixtures only -- no live store, no fetch, no model:

  A  THE AUCTION SAMPLER NEVER STARTS THE GATEWAY. With the operator's stop marker
     present it returns "Gateway stopped by operator" without connecting; with
     nothing listening on the port, likewise; with both clear it goes on to its
     own probe rule. The connection function is a trap that fails the gate if
     called.
  B  ONE CLIENT, AND NO SCOPE NO ROW. The shared client is built with timeout=90
     and max_retries=1, once; a call outside a report's scope writes nothing; a
     section's attempts count up; every model path routes through the meter.
  C  THE RESTORE DRILL, against a fake remote directory holding gzipped fixture
     databases: the newest snapshot is restored into a temporary directory,
     integrity-checked, counted beside the live store (opened read-only), and the
     directory removed; only `rclone lsf` and `rclone copy` are run; the remote and
     the live store are byte-identical afterwards; a corrupt snapshot fails with
     rc 2; the drill's unit is never in DEPLOY_TIMERS.

    python tools/validate_audit_2.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import gzip
import hashlib
import importlib.util
import shutil
import sqlite3
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gate_tmp import mkdtemp as gate_mkdtemp  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78


def check(c: bool, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def group_a(td: str) -> None:
    head("A. THE AUCTION SAMPLER NEVER STARTS THE GATEWAY (item 2)")
    from altdata import observations
    from altdata.loggers import auction
    connected = []

    def trap(*a, **k):
        connected.append(1)
        raise AssertionError("the sampler tried to connect")
    real = auction._connect                                     # noqa: SLF001
    auction._connect = trap                                     # noqa: SLF001
    try:
        marker = Path(td) / "state" / "gateway.stopped_by_operator"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("", encoding="utf-8")
        with observations.ObservationStore(str(Path(td) / "a.db")) as st:
            r = auction.sample(store=st, marker=marker, listening=lambda p: True,
                               force=True)
            check(r == {"skipped": "Gateway stopped by operator", "written": 0},
                  f"the stop marker present: \"Gateway stopped by operator\", nothing "
                  f"written ({r})")
            marker.unlink()
            r = auction.sample(store=st, marker=marker, listening=lambda p: False,
                               force=True)
            check(r.get("skipped", "").startswith("Gateway not up")
                  and "never starts it" in r["skipped"],
                  f"nothing listening on 4002: it steps aside ({r.get('skipped')})")
            check(not connected, "and in neither case did it connect")
            r = auction.sample(store=st, marker=marker, listening=lambda p: True)
            check(r.get("skipped", "").startswith("probe state")
                  and not connected,
                  f"both clear: it goes on to its own entitlement rule ({r})")
    finally:
        auction._connect = real                                 # noqa: SLF001
    import os
    os.environ["GATEWAY_INTENT_FILE"] = str(Path(td) / "elsewhere")
    check(auction.intent_file() == Path(td) / "elsewhere",
          "the marker path is the watchdog's (GATEWAY_INTENT_FILE, else "
          "~/state/gateway.stopped_by_operator)")
    del os.environ["GATEWAY_INTENT_FILE"]
    check(auction.intent_file() == Path.home() / "state" / "gateway.stopped_by_operator",
          "and its default is the same literal path ibgateway.service names")


def group_b(td: str) -> None:
    head("B. ONE CLIENT, AND NO SCOPE NO ROW (item 4)")
    from altdata import model_meter as mm
    from altdata import secrets
    built = []

    class FakeAnthropic:
        def __init__(self, **kw):
            built.append(kw)
    saved = (sys.modules.get("anthropic"), secrets.present, mm._CLIENT)  # noqa: SLF001
    sys.modules["anthropic"] = types.SimpleNamespace(Anthropic=FakeAnthropic)
    secrets.present = lambda name: True
    mm._CLIENT = None                                           # noqa: SLF001
    try:
        c1, why1 = mm.client()
        c2, _ = mm.client()
        check(isinstance(c1, FakeAnthropic) and c1 is c2 and len(built) == 1,
              "one client per process, built once")
        check(built == [{"timeout": 90, "max_retries": 1}],
              f"with timeout=90 and max_retries=1 ({built})")
    finally:
        if saved[0] is None:
            sys.modules.pop("anthropic", None)
        else:
            sys.modules["anthropic"] = saved[0]
        secrets.present = saved[1]
        mm._CLIENT = saved[2]                                   # noqa: SLF001
    resp = types.SimpleNamespace(model="m", usage=types.SimpleNamespace(
        input_tokens=10, output_tokens=2))
    db = str(Path(td) / "meter.db")
    check(mm.record(resp) is False, "a call outside any report's scope writes nothing")
    with mm.scope(report="weekly", run_id="r1", db_path=db):
        for sec in ("tape", "tape", "read"):
            with mm.scope(section=sec):
                mm.record(resp)
    rows = sqlite3.connect(db).execute(
        "SELECT run_id, report, section, attempt FROM model_calls ORDER BY id").fetchall()
    check(rows == [("r1", "weekly", "tape", 1), ("r1", "weekly", "tape", 2),
                   ("r1", "weekly", "read", 1)],
          f"inside a scope: one row a call, attempts counted per section ({rows})")
    calls = []
    fake = types.SimpleNamespace(messages=types.SimpleNamespace(
        create=lambda **k: calls.append(k) or resp))
    with mm.scope(report="monthly", db_path=db):
        out = mm.create(fake, model="m", max_tokens=5, messages=[])
    check(out is resp and calls and sqlite3.connect(db).execute(
        "SELECT COUNT(*) FROM model_calls WHERE report='monthly'").fetchone()[0] == 1,
        "create() makes the call through the client given and records it")
    # Every report path reaches the model through the meter: no module but the
    # meter builds a client, and no messages.create is called outside it.
    import re
    offenders = []
    for path in list((REPO / "altdata").rglob("*.py")) + list(
            (REPO / "daily_cascade").rglob("*.py")) + list(
            (REPO / "monthly_macro").rglob("*.py")):
        rel = path.relative_to(REPO).as_posix()
        if rel in ("altdata/model_meter.py",) or rel.startswith("altdata/report/"):
            continue
        code = re.sub(r"#.*", "", path.read_text(encoding="utf-8"))
        if re.search(r"\.messages\.create\(|anthropic\.Anthropic\(|Anthropic\(\)", code):
            offenders.append(rel)
    check(not offenders,
          f"every report path calls the model through altdata/model_meter.py "
          f"({offenders or 'none outside it'}; altdata/report/ is content, not a "
          f"pipeline)")
    # And every edition opens its report's scope, or its calls go uncounted: the
    # Quarterly arrived with Friday's tip writing through the meter with no scope.
    unscoped = []
    for rel, report in (("daily_cascade/stack_close.py", "daily_close"),
                        ("daily_cascade/weekly_stack.py", "weekly"),
                        ("monthly_macro/stack.py", "monthly"),
                        ("monthly_macro/quarterly.py", "quarterly")):
        src = (REPO / rel).read_text(encoding="utf-8")
        if not re.search(r'@model_meter\.metered\("' + report + r'"\)\s*\ndef produce\(',
                         src):
            unscoped.append(rel)
    check(not unscoped,
          f"each edition's produce() is metered under its report "
          f"({unscoped or 'close, Weekly, Monthly, Quarterly'})")


def _fixture_db(path: Path, rows: int) -> None:
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE observations (k TEXT, v REAL)")
    conn.execute("CREATE TABLE register (id TEXT)")
    conn.executemany("INSERT INTO observations VALUES (?, ?)",
                     [(f"k{i}", float(i)) for i in range(rows)])
    conn.execute("INSERT INTO register VALUES ('d1')")
    conn.commit()
    conn.close()


def _tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        h.update(p.relative_to(root).as_posix().encode())
        if p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()


def group_c(td: str) -> None:
    head("C. THE RESTORE DRILL (item 5)")
    spec = importlib.util.spec_from_file_location("restore_drill",
                                                  REPO / "tools" / "restore_drill.py")
    rd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rd)
    remote = Path(td) / "fake-remote"
    (remote / "db").mkdir(parents=True)
    (remote / "data").mkdir()
    for day, n in (("2026-10-12", 5), ("2026-10-13", 7)):
        raw = Path(td) / f"chester-{day}.db"
        _fixture_db(raw, n)
        with open(raw, "rb") as s, gzip.open(remote / "db" / f"chester-{day}.db.gz",
                                             "wb") as d:
            shutil.copyfileobj(s, d)
    (remote / "db" / "notes.txt").write_text("not a snapshot", encoding="utf-8")
    live = Path(td) / "live.db"
    _fixture_db(live, 9)
    before = (_tree_hash(remote), live.read_bytes())
    verbs = []

    def runner(args):
        verbs.append(args[0])
        if args[0] == "lsf":
            return "\n".join(p.name for p in (Path(args[1].replace(
                "fake:", str(remote) + "/"))).iterdir() if p.is_file())
        if args[0] == "copy":
            src = Path(args[1].replace("fake:", str(remote) + "/"))
            shutil.copy(src, Path(args[2]) / src.name)
            return ""
        raise AssertionError(f"the drill ran rclone {args[0]}")
    r = rd.drill("fake:", str(live), runner, today="2026-10-14")
    check(r.get("ok") and r["rc"] == 0 and r["snapshot"] == "chester-2026-10-13.db.gz"
          and r["age_days"] == 1,
          f"the newest snapshot is restored ({r.get('snapshot')}, "
          f"{r.get('age_days')} day old)")
    check(r.get("integrity") == "ok", "and passes integrity_check")
    t = {x["table"]: (x["restored"], x["live"]) for x in r.get("tables") or []}
    check(t == {"observations": (7, 9), "register": (1, 1)},
          f"row counts beside the live store's ({t})")
    check(r.get("tmp_removed") is True and not Path(r["tmp"]).exists(),
          "the temporary directory is removed at the end")
    check(set(verbs) == {"lsf", "copy"},
          f"only rclone lsf and copy were run ({verbs})")
    check((_tree_hash(remote), live.read_bytes()) == before,
          "the remote and the live store are byte-identical afterwards")
    txt = rd.report(r)
    check("RESULT: restorable" in txt and "observations" in txt and "+2" in txt,
          "the printed report names each table and the gap a restore would lose")
    (remote / "db" / "chester-2026-10-14.db.gz").write_bytes(b"not gzip at all")
    bad = rd.drill("fake:", str(live), runner, today="2026-10-14")
    check(not bad["ok"] and bad["rc"] == 2 and bad.get("tmp_removed"),
          f"a corrupt newest snapshot fails with rc 2, and still cleans up "
          f"({bad.get('error')})")
    empty = Path(td) / "empty-remote"
    (empty / "db").mkdir(parents=True)
    none = rd.drill("fake:", str(live), lambda a: "" if a[0] == "lsf" else None)
    check(none["rc"] == 2 and "no chester-" in none["error"],
          "no snapshot at all is rc 2 with the reason")
    try:
        rd.rclone(["delete", "x"])
        check(False, "the real runner refuses a write verb")
    except ValueError:
        check(True, "the real runner refuses any verb but lsf and copy")
    # Ruling 6 (19 Oct 2026): the weekly restore test superseded the monthly drill.
    # The drill's units, wrapper and allow entry are gone; the test is the one
    # restore check, and it runs this module through the crypt remote.
    units = REPO / "deploy" / "systemd"
    remote_sh = (REPO / "scripts" / "deploy_remote.sh").read_text(encoding="utf-8")
    allow = (units / "box-config.allow").read_text(encoding="utf-8")
    check(not (units / "chester-restore-drill.service").exists()
          and not (units / "chester-restore-drill.timer").exists()
          and not (REPO / "scripts" / "run_restore_drill.sh").exists()
          and "chester-restore-drill" not in allow and "restore-drill" not in remote_sh,
          "the monthly drill is retired: no unit, no wrapper, no allow entry")
    svc = (units / "chester-restore-test.service").read_text(encoding="utf-8")
    wrapper = (REPO / "scripts" / "run_restore_test.sh").read_text(encoding="utf-8")
    restore_units = sorted(p.name for p in units.glob("*restore*"))
    check("scripts/run_restore_test.sh" in svc and "-m tools.restore_drill" in wrapper
          and '"$CRYPT_REMOTE"' in wrapper
          and "git pull" not in wrapper.split("set -uo", 1)[-1]
          and restore_units == ["chester-restore-test.service", "chester-restore-test.timer"]
          and "chester-restore-test.timer" not in remote_sh,
          f"chester-restore-test is the one restore check: it runs the drill module "
          f"through the crypt remote and is never in DEPLOY_TIMERS ({restore_units})")
    check((REPO / "docs" / "runbooks" / "restore.md").exists(),
          "docs/runbooks/restore.md exists")


def main() -> int:
    td = gate_mkdtemp(prefix="validate_audit_2_")
    group_a(td)
    group_b(td)
    group_c(td)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
