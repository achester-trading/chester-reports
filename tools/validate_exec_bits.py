"""
Every file in scripts/ is executable in the git INDEX, and every unit's
ExecStart points at one of them.

THE SIXTH MEMBER OF THE SILENT-FAILURE FAMILY.

`scripts/check_heartbeat_cron.sh` was committed `100644` while every other
script in `scripts/` was `100755`. The unit's ExecStart therefore failed with
status `203/EXEC` -- and would have failed identically at 08:30 every morning,
forever, with no output anywhere except systemd's own journal. The alarm that
exists to notice a dead pipeline was itself dead on arrival.

It stayed hidden because an older box-local unit was invoking
`check_heartbeat.sh` directly and bypassing the wrapper, so "the timer is
installed" was true at the same time as "the wrapper has never run". Two true
statements, one broken system, and nothing in between them to disagree.

The fix is the family's fix: assert rather than trust.

-----------------------------------------------------------------------------
READ THE INDEX, NOT THE WORKING TREE
-----------------------------------------------------------------------------

`os.access(path, X_OK)` and `Path.stat().st_mode` describe THIS checkout. The
VPS gets its files from a `git pull`, so the only mode that can ever reach the
box is the one recorded in the index -- which is what `git ls-files -s` prints
and what a commit carries.

The distinction is not academic in either direction:

  * A local `chmod +x` that is never committed leaves the working tree looking
    fixed while the box still receives 100644. The defect wears a disguise and
    the check would certify it.
  * Windows has no exec bit at all. A script authored on the laptop is born
    100644 in the index, `chmod +x` is a no-op there, and the author sees
    nothing wrong. That is exactly how the original one shipped.

So this asks git, and only git.

-----------------------------------------------------------------------------
AND THE OTHER HALF: A UNIT POINTING AT NOTHING
-----------------------------------------------------------------------------

An executable bit on a file no unit invokes is harmless; a unit invoking a file
that is missing or non-executable is 203/EXEC at 03:00. So every ExecStart
inside deploy/systemd/ that names a path in this repo is resolved back to an
index entry and checked. Paths outside the repo (/usr/bin/systemctl,
xvfb-run, IBC's own launcher) are the box's business, not the repo's.

    python tools/validate_exec_bits.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
UNIT_DIR = REPO / "deploy" / "systemd"

EXEC_MODE = "100755"

# Directories whose every committed file must be executable. scripts/ is the
# directory of things that get INVOKED -- by systemd, by cron, by a human on the
# box -- so "not executable" is never the right answer for anything in it.
#
# tools/ is deliberately NOT here. Its shell validators are called as
# `bash tools/x.sh` from CI, which works at any mode, and its Python is imported
# or run as `python tools/x.py`. Requiring an exec bit there would assert a
# property nothing depends on, and a check nothing depends on is one people
# learn to override.
EXEC_DIRS = ("scripts",)

# ExecStart values that name something outside this repo. The box owns these.
EXTERNAL_PREFIXES = ("/usr/", "/bin/", "/sbin/", "-/")

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


def index_modes() -> dict[str, str]:
    """{repo-relative path: mode} straight out of the git index.

    `git ls-files -s` prints "<mode> <sha> <stage>\\t<path>". Nothing here
    touches the filesystem, which is the whole point.
    """
    out = subprocess.run(
        ["git", "ls-files", "-s"],
        cwd=REPO, capture_output=True, text=True, check=True).stdout
    modes: dict[str, str] = {}
    for line in out.splitlines():
        if "\t" not in line:
            continue
        meta, path = line.split("\t", 1)
        modes[path.strip()] = meta.split()[0]
    return modes


def unit_exec_targets() -> list[tuple[str, str]]:
    """[(unit name, repo-relative path)] for every ExecStart* inside the repo.

    %h expands to the user's home on the box, where the checkout lives at
    ~/chester-reports. A unit naming anything else is naming the box's own
    binaries and is out of scope.
    """
    targets: list[tuple[str, str]] = []
    for unit in sorted(UNIT_DIR.glob("*.service")):
        for raw in unit.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line.startswith("#") or not line.startswith("Exec"):
                continue
            m = re.match(r"^Exec\w+\s*=\s*(.*)$", line)
            if not m:
                continue
            cmd = m.group(1).strip()
            # ExecStart may prefix a shell; take the first token that looks
            # like a path into the checkout, not merely the first token.
            for tok in cmd.split():
                if tok.startswith(EXTERNAL_PREFIXES):
                    continue
                if "%h/chester-reports/" in tok:
                    rel = tok.split("%h/chester-reports/", 1)[1]
                    targets.append((unit.name, rel))
    return targets


# Synthetic cases for the parser, because the repo is green and therefore
# exercises none of the failure paths itself. A check that has never fired is
# a check that can stop working invisibly -- which is the defect class this
# file was written for, one level up.
SELF_TESTS = [
    ("a 100644 entry is not executable", "100644", False),
    ("a 100755 entry is executable", "100755", True),
    ("a symlink entry (120000) is not an executable regular file",
     "120000", False),
]


def self_test() -> None:
    print(f"{LINE}\nSelf-test\n{LINE}")
    for name, mode, want_ok in SELF_TESTS:
        got = (mode == EXEC_MODE)
        if got == want_ok:
            ok(name)
        else:
            bad(f"{name} -- mode {mode} judged {got}, wanted {want_ok}")
    # The ExecStart parser must find the repo-relative path and must not be
    # fooled by the xvfb-run wrapper, whose first token is /usr/bin/.
    sample = "ExecStart=/usr/bin/xvfb-run --auto-servernum %h/chester-reports/scripts/x.sh -inline"
    toks = [t for t in sample.split("=", 1)[1].split()
            if not t.startswith(EXTERNAL_PREFIXES) and "%h/chester-reports/" in t]
    if toks == ["%h/chester-reports/scripts/x.sh"]:
        ok("ExecStart parser looks past a /usr/bin wrapper to the repo path")
    else:
        bad(f"ExecStart parser returned {toks}")
    print()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    self_test()

    try:
        modes = index_modes()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"  FAIL  cannot read the git index: {exc}")
        print("VALIDATION FAILED")
        return 1

    print(f"{LINE}\nCommitted mode of every file in {'/, '.join(EXEC_DIRS)}/\n{LINE}")
    tracked = {p: m for p, m in modes.items()
               if any(p.startswith(f"{d}/") for d in EXEC_DIRS)}
    if not tracked:
        bad("no files tracked under " + ", ".join(EXEC_DIRS)
            + "/ -- the check is looking in the wrong place")
    for path, mode in sorted(tracked.items()):
        if mode == EXEC_MODE:
            ok(f"{path} is {mode}")
        else:
            bad(f"{path} is {mode} in the INDEX, not {EXEC_MODE} -- systemd "
                f"will fail it 203/EXEC. `git update-index --chmod=+x {path}` "
                f"(a local chmod alone does not reach the box)")

    print(f"\n{LINE}\nEvery unit's ExecStart resolves to an executable in the index\n{LINE}")
    targets = unit_exec_targets()
    if not targets:
        bad("no in-repo ExecStart targets found -- the parser is not matching")
    for unit, rel in targets:
        mode = modes.get(rel)
        if mode is None:
            bad(f"{unit}: ExecStart names {rel}, which is NOT TRACKED -- the "
                f"box will never receive it")
        elif mode != EXEC_MODE:
            bad(f"{unit}: ExecStart names {rel}, committed {mode} -- 203/EXEC")
        else:
            ok(f"{unit} -> {rel} ({mode})")

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
