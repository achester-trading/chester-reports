"""
Validation gate for every systemd unit this repo ships.

WHY THIS EXISTS. Silent-ignore is now a four-time pattern, and every instance
cost a deployment to find:

  1. StartLimitIntervalSec / StartLimitBurst in [Service] on ibgateway.service.
     systemd moved them to [Unit] in v230 and ignores them under [Service] with
     no warning -- the restart-storm guard was never in force.
  2. ProtectHome=read-write on chester-eod.service. Not a valid value;
     ProtectHome takes yes|no|read-only|tmpfs. Ignored.
  3. ...which hid a second defect: ProtectSystem=strict makes the whole tree
     read-only, so the unit needed ReadWritePaths and had none. It would have
     failed on its first real write.
  4. Environment=DISPLAY=:0 under xvfb-run -- valid systemd, wrong value, and
     it presented as the credential hang.

The common shape is that systemd accepts the file and does something other than
what the file appears to say. `systemd-analyze verify` catches some of this but
needs systemd, which the machine these are AUTHORED on does not have. So this
checks what can be checked from the text: every directive we ship is known, in
a section systemd reads it from, and carries a value from its enumeration.

AND THE CHECKS ARE THEMSELVES CHECKED. Every unit this repo ships is green by
design, so the real corpus exercises none of the failure paths -- a check that
quietly stopped firing would look exactly like a clean build. SELF_TESTS drives
synthetic units carrying one defect each through the same scanner, so the
wrong-section check in particular is proved to fire on every run rather than
the last time somebody tried it by hand.

DELIBERATELY A CLOSED ALLOWLIST. An unrecognised directive FAILS rather than
being skipped. That is the point: a typo and a directive nobody vetted look
identical from here, and the vetting is the value. Adding a directive means
adding a line to KNOWN below, which is a small deliberate act -- exactly the
review step whose absence produced the four above.

    python tools/validate_systemd_units.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
UNIT_DIR = REPO / "deploy" / "systemd"

BOOL = {"yes", "no", "true", "false", "on", "off", "1", "0"}

# directive -> (allowed sections, allowed values or None for free-form)
KNOWN: dict[str, tuple[set[str], set[str] | None]] = {
    # [Unit]
    "Description":            ({"Unit"}, None),
    "Documentation":          ({"Unit"}, None),
    "After":                  ({"Unit"}, None),
    "Before":                 ({"Unit"}, None),
    "Wants":                  ({"Unit"}, None),
    "Requires":               ({"Unit"}, None),
    "BindsTo":                ({"Unit"}, None),
    "ConditionPathExists":    ({"Unit"}, None),
    # These two live in [Unit]. Under [Service] systemd IGNORES them silently.
    "StartLimitIntervalSec":  ({"Unit"}, None),
    "StartLimitBurst":        ({"Unit"}, None),

    # [Service]
    "Type": ({"Service"},
             {"simple", "exec", "forking", "oneshot", "dbus", "notify", "idle"}),
    "ExecStart":              ({"Service"}, None),
    "ExecStartPre":           ({"Service"}, None),
    "ExecStartPost":          ({"Service"}, None),
    "ExecStop":               ({"Service"}, None),
    "Environment":            ({"Service"}, None),
    "EnvironmentFile":        ({"Service"}, None),
    "WorkingDirectory":       ({"Service"}, None),
    "Restart": ({"Service"},
                {"no", "on-success", "on-failure", "on-abnormal",
                 "on-watchdog", "on-abort", "always"}),
    "RestartSec":             ({"Service"}, None),
    "TimeoutStartSec":        ({"Service"}, None),
    "TimeoutStopSec":         ({"Service"}, None),
    "KillSignal":             ({"Service"}, None),
    "SuccessExitStatus":      ({"Service"}, None),
    "RemainAfterExit":        ({"Service"}, BOOL),
    "NoNewPrivileges":        ({"Service"}, BOOL),
    "PrivateTmp":             ({"Service"}, BOOL),
    "ProtectSystem":          ({"Service"}, {"yes", "no", "full", "strict"}),
    # NOT read-write. That was defect 2.
    "ProtectHome":            ({"Service"}, {"yes", "no", "read-only", "tmpfs"}),
    "ReadWritePaths":         ({"Service"}, None),
    "ReadOnlyPaths":          ({"Service"}, None),
    "ProtectKernelTunables":  ({"Service"}, BOOL),
    "ProtectControlGroups":   ({"Service"}, BOOL),
    "RestrictSUIDSGID":       ({"Service"}, BOOL),

    # [Timer]
    "OnCalendar":             ({"Timer"}, None),
    "OnActiveSec":            ({"Timer"}, None),
    "OnUnitActiveSec":        ({"Timer"}, None),
    "AccuracySec":            ({"Timer"}, None),
    "RandomizedDelaySec":     ({"Timer"}, None),
    "Persistent":             ({"Timer"}, BOOL),
    "Unit":                   ({"Timer"}, None),

    # [Install]
    "WantedBy":               ({"Install"}, None),
    "RequiredBy":             ({"Install"}, None),
}

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


def scan(text: str) -> tuple[int, list[str]]:
    """Directives seen, and everything wrong with them.

    Split out from check_unit so the SELF-TESTS below can drive it with
    synthetic units. A validator whose own checks are never exercised is a
    validator that can lose one silently -- which is the same failure class it
    exists to catch.
    """
    section = None
    seen = 0
    problems: list[str] = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        # A commented-out [Install] is the enable gate, not a section.
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        m = re.match(r"^\[(\w+)\]$", line)
        if m:
            section = m.group(1)
            continue
        m = re.match(r"^([A-Za-z][A-Za-z0-9]*)\s*=\s*(.*)$", line)
        if not m:
            problems.append(f"line {n}: not a directive or section: {line!r}")
            continue
        key, value = m.group(1), m.group(2).strip()
        seen += 1

        if key not in KNOWN:
            problems.append(
                f"line {n}: unknown directive {key!r} -- if it is real, add it "
                f"to KNOWN in this file so somebody has vetted it")
            continue
        sections, values = KNOWN[key]
        if section not in sections:
            problems.append(
                f"line {n}: {key}= is in [{section}] but systemd reads it from "
                f"[{'/'.join(sorted(sections))}] -- it is IGNORED here, silently")
        if values is not None and value.lower() not in values:
            problems.append(
                f"line {n}: {key}={value!r} is not one of "
                f"{sorted(values)} -- systemd ignores or rejects it")

    return seen, problems


def check_unit(path: Path) -> None:
    seen, problems = scan(path.read_text(encoding="utf-8"))
    if problems:
        for p in problems:
            bad(f"{path.name}: {p}")
    else:
        ok(f"{path.name}: {seen} directives, all known, sited and valued")


# Synthetic units carrying one defect each. The wrong-section case is the
# reason this block exists: the four silent-ignore incidents that produced this
# validator were ALL a directive systemd reads from somewhere else, and a check
# for that which quietly stopped working would look exactly like a clean build.
# The unit files are green by design, so nothing in the real corpus exercises
# these paths -- these do.
SELF_TESTS: list[tuple[str, str, str]] = [
    ('StartLimit* under [Service] is caught (defect 1, the original)',
     "[Unit]\nDescription=x\n[Service]\nStartLimitIntervalSec=1h\nExecStart=/bin/true\n",
     'systemd reads it from [Unit]'),
    ('StartLimitBurst under [Service] is caught too, not just its sibling',
     "[Unit]\nDescription=x\n[Service]\nStartLimitBurst=4\nExecStart=/bin/true\n",
     'systemd reads it from [Unit]'),
    ('a [Service] directive under [Unit] is caught in the other direction',
     "[Unit]\nDescription=x\nExecStart=/bin/true\n",
     'systemd reads it from [Service]'),
    ('a [Timer] directive in a [Service] section is caught',
     "[Unit]\nDescription=x\n[Service]\nOnCalendar=daily\n",
     'systemd reads it from [Timer]'),
    ('ProtectHome=read-write is caught (defect 2: valid directive, dead value)',
     "[Unit]\nDescription=x\n[Service]\nProtectHome=read-write\nExecStart=/bin/true\n",
     'is not one of'),
    ('an unknown directive fails rather than being skipped',
     "[Unit]\nDescription=x\n[Service]\nProtectEverything=yes\nExecStart=/bin/true\n",
     'unknown directive'),
    ('a directive before any section header is not silently accepted',
     "ExecStart=/bin/true\n",
     'IGNORED here'),
    ('a correct unit produces no problems at all',
     "[Unit]\nDescription=x\nStartLimitBurst=4\n[Service]\nType=oneshot\nExecStart=/bin/true\nProtectHome=no\n",
     ''),
]


def self_test() -> None:
    """Prove the checks fire, before trusting them on the real units."""
    print(f"{LINE}\nSelf-test: the checks themselves\n{LINE}")
    for name, text, expect in SELF_TESTS:
        _, problems = scan(text)
        if not expect:
            if problems:
                bad(f"{name} -- but got: {problems}")
            else:
                ok(name)
            continue
        if any(expect in p for p in problems):
            ok(name)
        else:
            bad(f"{name} -- expected {expect!r}, got: {problems or 'nothing'}")
    print()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    self_test()
    units = sorted(list(UNIT_DIR.glob("*.service")) + list(UNIT_DIR.glob("*.timer")))
    print(f"{LINE}\nsystemd units shipped in deploy/systemd/\n{LINE}")
    if not units:
        print("  no unit files found")
        return 1
    for u in units:
        check_unit(u)

    # Every .timer must name a .service that exists, or it fires into nothing.
    print(f"\n{LINE}\nTimer -> service pairing\n{LINE}")
    for t in sorted(UNIT_DIR.glob("*.timer")):
        svc = t.with_suffix(".service")
        if svc.exists():
            ok(f"{t.name} -> {svc.name} exists")
        else:
            bad(f"{t.name} has no matching {svc.name} and would fire into nothing")

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
