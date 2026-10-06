"""
Every feed in altdata/feeds.py FEEDS has a scheduled runner that does not skip it.

INC-9, AND WHY THIS IS A GATE RATHER THAN A COMMENT.

The loggers -- borrow, consensus, vxcurve, shielded, rtat -- ran nowhere from
30 Sep to 6 Oct 2026. Nothing broke. Two scripts each said the other ran them:

  * scripts/run_eod_cron.sh pulls `--skip loggers`, with a comment saying
    "they run in the overnight pass";
  * scripts/fetch_overnight.sh, since 30 Sep, pulls `--early`, whose fixed set
    (feeds.EARLY_SKIP) also skips them.

Each statement was true when it was written. Together they scheduled nothing,
and a logger that does not run looks exactly like a quiet one -- the rows it
would have written are point-in-time captures that cannot be fetched later.

The lesson recorded in docs/incidents.md is that a feed is not scheduled until a
gate says so. This is that gate.

-----------------------------------------------------------------------------
WHAT COUNTS AS A SCHEDULED RUNNER
-----------------------------------------------------------------------------

A `.service` in deploy/systemd/ that

  1. has a `.timer` of the same name, AND
  2. whose timer is in scripts/deploy_remote.sh DEPLOY_TIMERS -- the list the
     deploy actually enables. A timer file the deploy never enables schedules
     nothing on the box, which is the same silence one level up;

and the runner is its ExecStart script plus every scripts/*.sh that script
calls, transitively.

In each runner, every non-comment `-m altdata.feeds pull ...` is read for
`--only`, `--skip` and `--early`, and the feeds it runs are asked of
feeds.selection() -- the function pull() itself uses -- so this gate holds no
second copy of what `--early` leaves out. An invocation whose arguments are
not literal (a shell variable) is not counted: the gate cannot say what it
runs, and counting it would be the gate certifying a guess.

A CODE GATE: it reads the repo only, never the store or the box.

    python tools/validate_feeds_scheduled.py
"""

from __future__ import annotations

import re
import shlex
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

UNIT_DIR = REPO / "deploy" / "systemd"
SCRIPTS = REPO / "scripts"
DEPLOY_REMOTE = SCRIPTS / "deploy_remote.sh"

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


def check(cond: bool, m: str) -> None:
    (ok if cond else bad)(m)


def code_lines(text: str) -> str:
    """The script with whole-line comments removed."""
    return "\n".join(ln for ln in text.splitlines()
                     if not ln.lstrip().startswith("#"))


def deploy_timers(text: str | None = None) -> list[str]:
    text = DEPLOY_REMOTE.read_text(encoding="utf-8") if text is None else text
    m = re.search(r'^DEPLOY_TIMERS="([^"]*)"', text, re.M)
    return m.group(1).split() if m else []


def scheduled_units(timers: list[str]) -> dict[str, str]:
    """{service name: repo-relative ExecStart script} for every service whose
    timer exists AND is in DEPLOY_TIMERS."""
    out: dict[str, str] = {}
    for svc in sorted(UNIT_DIR.glob("*.service")):
        timer = svc.with_suffix(".timer").name
        if not (UNIT_DIR / timer).is_file() or timer not in timers:
            continue
        for raw in svc.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\s*ExecStart\s*=\s*(.*)$", raw)
            if not m:
                continue
            for tok in m.group(1).split():
                if "%h/chester-reports/" in tok:
                    out[svc.name] = tok.split("%h/chester-reports/", 1)[1]
                    break
    return out


def called_scripts(rel: str, texts: dict[str, str],
                   seen: set[str] | None = None) -> list[str]:
    """`rel` and every scripts/*.sh it calls, transitively, in visit order."""
    seen = set() if seen is None else seen
    if rel in seen or rel not in texts:
        return []
    seen.add(rel)
    found = [rel]
    for name in re.findall(r"scripts/([\w.-]+\.sh)\b", code_lines(texts[rel])):
        found += called_scripts(f"scripts/{name}", texts, seen)
    return found


def feeds_invocations(text: str) -> list[str]:
    """The argument string of every non-comment `-m altdata.feeds pull`."""
    return [re.sub(r"\s*\d*>.*$", "", m.group(1)) for m in re.finditer(
        r'-m\s+altdata\.feeds\s+pull\b([^\n"\)|;&]*)', code_lines(text))]


def feeds_run_by(args: str):
    """The feeds an argument string runs, or None when it cannot be read."""
    from altdata import feeds
    try:
        toks = shlex.split(args)
    except ValueError:
        return None
    if any("$" in t for t in toks):
        return None
    only, skip, early = None, (), False
    it = iter(toks)
    for t in it:
        if t == "--early":
            early = True
        elif t in ("--only", "--skip"):
            v = next(it, "")
            if t == "--only":
                only = v
            else:
                skip = tuple(x.strip() for x in v.split(",") if x.strip())
        elif t.startswith("--only="):
            only = t.split("=", 1)[1]
        elif t.startswith("--skip="):
            skip = tuple(x.strip() for x in t.split("=", 1)[1].split(",")
                         if x.strip())
    return set(feeds.selection(only=only, skip=skip, early=early))


def coverage(texts: dict[str, str], timers: list[str]) -> dict[str, list[str]]:
    """{feed: [where it runs]} for every feed in FEEDS."""
    from altdata import feeds
    cov: dict[str, list[str]] = {f: [] for f in feeds.FEEDS}
    for unit, rel in scheduled_units(timers).items():
        for script in called_scripts(rel, texts):
            for args in feeds_invocations(texts[script]):
                run = feeds_run_by(args)
                if run is None:
                    print(f"  note  {unit} -> {script}: `feeds pull{args}` "
                          f"has non-literal arguments; not counted")
                    continue
                for f in run:
                    if f in cov:
                        cov[f].append(f"{unit} -> {script} (pull{args})")
    return cov


def repo_scripts() -> dict[str, str]:
    return {f"scripts/{p.name}": p.read_text(encoding="utf-8")
            for p in sorted(SCRIPTS.glob("*.sh"))}


def self_test() -> None:
    """The failure paths, on synthetic input. A gate that has only ever seen a
    green repo is a gate nobody knows still fires."""
    print(f"{LINE}\nSelf-test\n{LINE}")
    from altdata import feeds
    check("loggers" not in feeds.selection(early=True),
          "the --early set does not run the loggers (the half of INC-9 that "
          "fetch_overnight.sh inherited on 30 Sep)")
    check(feeds_run_by(" --skip loggers") == set(feeds.FEEDS) - {"loggers"},
          "`--skip loggers` runs every feed but the loggers")
    check(feeds_run_by(" --only loggers") == {"loggers"},
          "`--only loggers` runs the loggers and nothing else")
    check(feeds_run_by(' $ARGS') is None,
          "a non-literal argument list is unreadable, not assumed")

    texts = repo_scripts()
    timers = deploy_timers()
    # INC-9 AS IT STOOD: the overnight pass with no loggers line.
    inc9 = dict(texts)
    inc9["scripts/fetch_overnight.sh"] = "\n".join(
        ln for ln in texts["scripts/fetch_overnight.sh"].splitlines()
        if not re.search(r"altdata\.feeds\s+pull\b.*--only\s+loggers", ln))
    check(not coverage(inc9, timers)["loggers"],
          "with fetch_overnight.sh as it stood 30 Sep - 6 Oct, the loggers have "
          "no runner -- the gate fires on INC-9")
    # A runner whose timer the deploy never enables does not count.
    check(not coverage(texts, [t for t in timers
                               if t != "chester-overnight.timer"])["loggers"],
          "with chester-overnight.timer out of DEPLOY_TIMERS, the loggers have no "
          "runner -- a timer the deploy never enables schedules nothing")
    # A call through a helper script is followed.
    helper = dict(texts)
    helper["scripts/_t_outer.sh"] = '"$REPO/scripts/_t_inner.sh"\n'
    helper["scripts/_t_inner.sh"] = '"$PY" -m altdata.feeds pull --only loggers\n'
    check(called_scripts("scripts/_t_outer.sh", helper)
          == ["scripts/_t_outer.sh", "scripts/_t_inner.sh"],
          "a script called by a unit's script is followed")
    check(not feeds_invocations("# \"$PY\" -m altdata.feeds pull --only loggers\n"),
          "a commented-out pull is not a runner")
    print()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from altdata import feeds
    import inspect

    self_test()

    print(f"{LINE}\nThe pull handles exactly FEEDS\n{LINE}")
    handled = re.findall(r'\("(\w+)",\s*(?:pull_|\()', inspect.getsource(feeds.pull))
    check(set(handled) == set(feeds.FEEDS),
          f"pull()'s dispatch names the same feeds as FEEDS "
          f"(dispatch {sorted(handled)}, FEEDS {sorted(feeds.FEEDS)})")

    print(f"\n{LINE}\nEvery feed has a scheduled runner that does not skip it\n{LINE}")
    timers = deploy_timers()
    check(bool(timers), f"DEPLOY_TIMERS read from {DEPLOY_REMOTE.relative_to(REPO)} "
                        f"({len(timers)} timers)")
    units = scheduled_units(timers)
    check(bool(units), f"{len(units)} scheduled units resolved to a script")
    cov = coverage(repo_scripts(), timers)
    for f in feeds.FEEDS:
        where = cov[f]
        if where:
            ok(f"{f}: {'; '.join(where)}")
        else:
            bad(f"{f}: NO scheduled runner runs it -- every unit with a deployed "
                f"timer either never pulls feeds or skips `{f}`. Nothing writes "
                f"its keys, and a feed that does not run looks like a quiet one "
                f"(INC-9)")

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
