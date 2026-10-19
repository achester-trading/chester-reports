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
    # AUD-2 item 3: the cgroup memory caps, and item 2: the OOM killer's order.
    "MemoryHigh":             ({"Service"}, None),
    "MemoryMax":              ({"Service"}, None),
    "OOMScoreAdjust":         ({"Service"}, None),

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



# --- a unit whose code reads a secret must load the secrets file -----------
#
# No unit had EnvironmentFile= and no wrapper sourced .env, so anything read
# through os.environ WITHOUT a .env fallback saw nothing on the box:
# CHESTER_STATE_TOKEN and FRED_API_KEY both. The dashboard would have stayed
# blind to the job that runs every day, and the only symptom would have been an
# INFO line in a log nobody reads.
#
# The rule cannot be "every unit", because ibgateway-restart.service runs
# systemctl and ibgateway.service runs IBC, neither of which reads this repo's
# environment. So it is derived: follow each unit's ExecStart into the script,
# find the Python entry points that script invokes, and require the file only
# where a secret is actually reachable.

# Environment variables that are secrets or endpoints -- i.e. things .env
# carries. Deliberately not every CHESTER_* name: the path overrides are
# defaulted in code and a unit that never sets them still works.
SECRET_NAMES = (
    "FRED_API_KEY", "ANTHROPIC_API_KEY", "MASSIVE_API_KEY",
    "FLASHALPHA_API_KEY", "CHESTER_STATE_URL", "CHESTER_STATE_TOKEN",
    "SMTP_USER", "SMTP_PASSWORD", "SMTP_TO", "SMTP_RCPT",
)


def _repo_python_modules() -> dict[str, str]:
    """Every repo .py file's text, keyed by dotted module path."""
    out: dict[str, str] = {}
    for f in REPO.rglob("*.py"):
        if ".venv" in f.parts or "probe_output" in f.parts:
            continue
        rel = f.relative_to(REPO).with_suffix("")
        out[".".join(rel.parts)] = f.read_text(encoding="utf-8", errors="replace")
    return out


def _reads_secret(text: str) -> set[str]:
    return {n for n in SECRET_NAMES if n in text}


def check_environment_file() -> None:
    """Require EnvironmentFile= on any unit that can reach a secret."""
    print(f"{LINE}\nSecrets: a unit that reads one must load the secrets file\n{LINE}")
    modules = _repo_python_modules()

    for unit in sorted(UNIT_DIR.glob("*.service")):
        text = unit.read_text(encoding="utf-8")
        execs = [ln.split("=", 1)[1].strip()
                 for ln in text.splitlines()
                 if ln.startswith("ExecStart") and "=" in ln]
        # Only units that run something in this checkout are in scope.
        repo_targets = [e for e in execs if "%h/chester-reports/" in e]
        if not repo_targets:
            continue

        # Follow the wrapper into the modules it invokes, then union every
        # secret name reachable from there. One level of indirection is enough:
        # every wrapper calls `python -m <module>` or `python <file>` directly.
        reachable: set[str] = set()
        for target in repo_targets:
            rel = target.split("%h/chester-reports/", 1)[1].split()[0]
            script = REPO / rel
            if not script.exists():
                continue
            body = script.read_text(encoding="utf-8", errors="replace")
            reachable |= _reads_secret(body)
            for mod, src in modules.items():
                invoked = (f"-m {mod}" in body
                           or f"{mod.replace('.', '/')}.py" in body)
                if invoked:
                    reachable |= _reads_secret(src)
                    # And one level down: a runner imports its library.
                    for dep, dsrc in modules.items():
                        if f"import {dep}" in src or f"from {dep}" in src:
                            reachable |= _reads_secret(dsrc)

        has_env = any(ln.startswith("EnvironmentFile=") for ln in text.splitlines())
        if not reachable:
            ok(f"{unit.name}: reaches no secret; EnvironmentFile not required")
        elif has_env:
            ok(f"{unit.name}: loads .env, and reaches "
               f"{len(reachable)} secret name(s)")
        else:
            bad(f"{unit.name}: reaches {sorted(reachable)} but has no "
                f"EnvironmentFile= -- those read as unset on the box, and the "
                f"only symptom is a log line")

        # The file must be OPTIONAL. Without the leading `-` a box that has not
        # been given a .env yet fails to start the unit at all, which turns a
        # missing feature into a dead pipeline.
        for ln in text.splitlines():
            if ln.startswith("EnvironmentFile="):
                if ln.split("=", 1)[1].startswith("-"):
                    ok(f"{unit.name}: EnvironmentFile is optional (leading '-')")
                else:
                    bad(f"{unit.name}: EnvironmentFile is REQUIRED -- a box "
                        f"without .env would fail to start the unit entirely")
    print()

# AUD-2 (ruled 14 Oct 2026), sized for the 8 GB box (CX33, from 17 Oct). The
# values are SESSION-SET; deploy/systemd/README.md and docs/briefs/aud-2-notes.md
# carry them and why. (MemoryHigh, MemoryMax) per heavy unit.
# THE CAPS FOLLOW THE MACHINE (6b part 3; ruled 17 Oct 2026: the rescale did not
# happen, the box stays at 4 GB). Each cap is a PERCENTAGE of physical memory; the
# 8 GB case each equals -- AUD-2's absolute figures -- is kept beside it, and the
# rule is checked at 4 GB and at 8 GB. (MemoryHigh %, MemoryMax %, 8 GB high,
# 8 GB max)
MEMORY_CAPS = {
    "chester-eod.service":         ("20%", "25%", "1.6G", "2G"),
    "chester-daily-close.service": ("20%", "25%", "1.6G", "2G"),
    "chester-weekly.service":      ("25%", "31%", "2G", "2.5G"),
    "chester-monthly.service":     ("25%", "31%", "2G", "2.5G"),
    "chester-voices.service":      ("10%", "12%", "0.8G", "1G"),
    "chester-backup.service":      ("15%", "19%", "1.2G", "1.5G"),
}
MACHINES_GB = (4, 8)
# The heavy units' caps may sum past the machine (they never all run at once) but
# not past 1.5 times it -- AUD-2's plausibility bound, now in percent.
CAP_SUM_LIMIT_PCT = 150.0


def _pct(v: str) -> float:
    m = re.fullmatch(r"([\d.]+)%", v or "")
    return float(m.group(1)) if m else float("nan")


def cap_at(v: str, gb: float) -> float:
    """A cap in GiB on a machine of `gb`: a percentage scales, a size does not."""
    return _pct(v) / 100.0 * gb if str(v).endswith("%") else _gib(v)
# THE OOM ORDER (ruled 14 Oct 2026 evening). A report can be rendered again; a
# day's chains cannot be fetched again; the Gateway needs Ari's supervised login.
# So the kernel, if the caps are not enough, takes a report first, the EOD capture
# next, the Gateway last. Raising a score needs no privilege, so the order holds
# even if a --user unit is refused the Gateway's -500.
OOM_SCORES = {
    "ibgateway.service":             -500,
    "chester-eod.service":            300,
    "chester-daily-close.service":    500,
    "chester-weekly.service":         500,
    "chester-monthly.service":        500,
    "chester-voices.service":         500,
    "chester-backup.service":         500,
    "chester-restore-drill.service":  500,
}
REPORT_UNITS = [u for u, v in OOM_SCORES.items()
                if u not in ("ibgateway.service", "chester-eod.service")]
# THE INTRADAY DEALER CAPTURES (6b part 2, session-set): capped and scored as
# captures (a chain cannot be fetched again: 300, as the EOD pass), checked unit
# by unit and kept OUT of the sum above -- they run at 09:45 and 12:30, when no
# heavy unit runs. Their timers are not in DEPLOY_TIMERS: enabling them is the
# operator's. (unit, (MemoryHigh, MemoryMax), timer's OnCalendar)
CAPTURE_UNITS = {
    "chester-dealer-0945.service": (("10%", "12%"), "Mon-Fri 09:45 America/New_York"),
    "chester-dealer-1230.service": (("10%", "12%"), "Mon-Fri 12:30 America/New_York"),
    # M-3 (18 Oct 2026): the vendor chains at 16:31, after SPX's 16:15 close with
    # Massive's 15-minute delay, before the 16:45 close.
    "chester-vendor-chains.service": (("10%", "12%"), "Mon-Fri 16:31 America/New_York"),
}
# THE VENDOR WRITER (6b part 3): 16:25 ET, a report's OOM score, not deployed.
VENDOR_UNIT = ("chester-flashalpha.service", ("4%", "5%"), "Mon-Fri 16:25 America/New_York")
SANDBOX = ("NoNewPrivileges=true", "PrivateTmp=true", "ProtectSystem=strict")


def directives(path: Path) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";", "[")) or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out.setdefault(k.strip(), []).append(v.strip())
    return out


def _gib(v: str) -> float:
    m = re.fullmatch(r"([\d.]+)([KMG]?)", v)
    if not m:
        return float("nan")
    return float(m.group(1)) * {"K": 1 / 1048576, "M": 1 / 1024, "G": 1.0, "": 1 / 2**30}[m.group(2)]


def _minutes(span: str) -> float:
    """A systemd time span (2h, 2h30min, 5min, 780) in minutes."""
    total = 0.0
    for n, u in re.findall(r"([\d.]+)\s*(h|min|m|s)?", span):
        total += float(n) * {"h": 60, "min": 1, "m": 1, "s": 1 / 60, "": 1 / 60}[u or ""]
    return total


def check_aud2(unit_dir: Path = UNIT_DIR) -> list[str]:
    """The AUD-2 unit rules; returns the faults (empty when all hold)."""
    faults = []
    for name, (high, mx, h8, m8) in MEMORY_CAPS.items():
        d = directives(unit_dir / name)
        if d.get("MemoryHigh") != [high] or d.get("MemoryMax") != [mx]:
            faults.append(f"{name}: MemoryHigh/MemoryMax {d.get('MemoryHigh')}/"
                          f"{d.get('MemoryMax')}, want {high}/{mx} (percentages: the "
                          f"caps follow the machine)")
        elif not _pct(high) < _pct(mx):
            faults.append(f"{name}: MemoryHigh must sit below MemoryMax")
        # The 8 GB case the percentages equal is AUD-2's, within a rounding step.
        elif abs(cap_at(mx, 8) - _gib(m8)) > 0.05 or abs(cap_at(high, 8) - _gib(h8)) > 0.05:
            faults.append(f"{name}: {high}/{mx} at 8 GB is not AUD-2's {h8}/{m8}")
    for gb in MACHINES_GB:
        total = sum(cap_at(mx, gb) for _, mx, _, _ in MEMORY_CAPS.values())
        if total > gb * CAP_SUM_LIMIT_PCT / 100.0:
            faults.append(f"the caps sum to {total:.2f}G, implausible on a {gb} GB box")
    # No capped unit carries an absolute cap: the rule is that every cap follows
    # the machine.
    for p in sorted(unit_dir.glob("*.service")):
        d = directives(p)
        for k in ("MemoryHigh", "MemoryMax"):
            for v in d.get(k, []):
                if not str(v).endswith("%"):
                    faults.append(f"{p.name}: {k}={v} is absolute; the caps follow "
                                  f"the machine (a percentage)")
    auc = directives(unit_dir / "chester-auction.service")
    if any("ibgateway" in v for k in ("Wants", "Requires", "BindsTo")
           for v in auc.get(k, [])):
        faults.append("chester-auction.service still pulls in ibgateway.service")
    for kv in SANDBOX:
        k, v = kv.split("=")
        if auc.get(k) != [v]:
            faults.append(f"chester-auction.service lacks {kv}")
    # The narrowest it can run with: its log, its status and lock (~/.chester),
    # and the checkout (the wrapper's git pull; data/chester.db). Nothing else.
    rw = " ".join(auc.get("ReadWritePaths", []))
    if sorted(rw.split()) != sorted(["%h/logs", "%h/.chester", "%h/chester-reports"]):
        faults.append(f"chester-auction.service ReadWritePaths not narrow ({rw!r})")
    score: dict = {}
    for name, want in OOM_SCORES.items():
        got = directives(unit_dir / name).get("OOMScoreAdjust")
        try:
            score[name] = int(got[0]) if got and len(got) == 1 else None
        except ValueError:
            score[name] = None
        if score[name] != want:
            faults.append(f"{name}: OOMScoreAdjust {got}, want {want}")
    # The order itself, so a re-tuned value cannot quietly invert it: the Gateway
    # lowest of all, the EOD capture below every report.
    gw, eod = score["ibgateway.service"], score["chester-eod.service"]
    if gw is not None and any(v is not None and v <= gw for k, v in score.items()
                              if k != "ibgateway.service"):
        faults.append("the Gateway's OOM score is not the lowest")
    if eod is not None and any(score[u] is not None and score[u] <= eod
                               for u in REPORT_UNITS):
        faults.append("the EOD capture's OOM score is not below every report's")
    faults += check_captures(unit_dir, score)
    bk = directives(unit_dir / "chester-backup.service")
    bt = directives(unit_dir / "chester-backup.timer")
    wk = directives(unit_dir / "chester-weekly.timer")
    if bk.get("TimeoutStartSec") != ["2h"]:
        faults.append(f"chester-backup.service TimeoutStartSec "
                      f"{bk.get('TimeoutStartSec')}, want 2h")
    start = re.search(r"(\d\d):(\d\d)", (bt.get("OnCalendar") or [""])[0])
    wstart = re.search(r"(\d\d):(\d\d)", (wk.get("OnCalendar") or [""])[0])
    if start and wstart:
        end = (int(start[1]) * 60 + int(start[2])
               + _minutes((bt.get("RandomizedDelaySec") or ["0"])[0])
               + _minutes((bk.get("TimeoutStartSec") or ["0"])[0]))
        if end >= int(wstart[1]) * 60 + int(wstart[2]):
            faults.append(f"the backup can run to {int(end // 60):02d}:"
                          f"{int(end % 60):02d}, into the Weekly at "
                          f"{wstart[1]}:{wstart[2]}")
    else:
        faults.append("could not read the backup's or the Weekly's OnCalendar")
    return faults


def check_captures(unit_dir: Path, score: dict) -> list[str]:
    """6b part 2's capture units: caps, the OOM order (below every report,
    above the Gateway), the sandbox, the wrapper, the calendar, and their timers
    left out of DEPLOY_TIMERS."""
    faults = []
    remote = (Path(__file__).resolve().parent.parent / "scripts" / "deploy_remote.sh")
    timers = remote.read_text(encoding="utf-8") if remote.exists() else ""
    for name, ((high, mx), cal) in CAPTURE_UNITS.items():
        p = unit_dir / name
        if not p.exists():
            faults.append(f"{name}: missing")
            continue
        d = directives(p)
        if d.get("MemoryHigh") != [high] or d.get("MemoryMax") != [mx]:
            faults.append(f"{name}: MemoryHigh/MemoryMax {d.get('MemoryHigh')}/"
                          f"{d.get('MemoryMax')}, want {high}/{mx}")
        oom = d.get("OOMScoreAdjust")
        try:
            v = int(oom[0]) if oom and len(oom) == 1 else None
        except ValueError:
            v = None
        gw = score.get("ibgateway.service")
        if v is None or (gw is not None and v <= gw) or any(
                score.get(u) is not None and score[u] <= v for u in REPORT_UNITS):
            faults.append(f"{name}: OOMScoreAdjust {oom}: must sit above the Gateway "
                          f"and below every report")
        for kv in SANDBOX:
            k, val = kv.split("=")
            if d.get(k) != [val]:
                faults.append(f"{name} lacks {kv}")
        slot = name.split("-")[-1].split(".")[0]
        if d.get("ExecStart") != [f"%h/chester-reports/scripts/run_dealer_capture.sh {slot}"]:
            faults.append(f"{name}: ExecStart {d.get('ExecStart')}")
        if d.get("EnvironmentFile") != ["-%h/chester-reports/.env"]:
            faults.append(f"{name}: EnvironmentFile not the optional repo one")
        t = directives(p.with_suffix(".timer"))
        if t.get("OnCalendar") != [cal]:
            faults.append(f"{name[:-8]}.timer: OnCalendar {t.get('OnCalendar')}, want {cal}")
        if t.get("Persistent") != ["false"]:
            faults.append(f"{name[:-8]}.timer: Persistent must be false")
        if p.with_suffix(".timer").name in timers:
            faults.append(f"{p.with_suffix('.timer').name} is in DEPLOY_TIMERS: enabling "
                          f"it is the operator's")
    vname, (vh, vm), vcal = VENDOR_UNIT
    vp = unit_dir / vname
    if not vp.exists():
        faults.append(f"{vname}: missing")
    else:
        d = directives(vp)
        t = directives(vp.with_suffix(".timer"))
        if d.get("MemoryHigh") != [vh] or d.get("MemoryMax") != [vm]:
            faults.append(f"{vname}: caps {d.get('MemoryHigh')}/{d.get('MemoryMax')}")
        if d.get("OOMScoreAdjust") != ["500"]:
            faults.append(f"{vname}: OOMScoreAdjust must be a report's 500")
        if d.get("EnvironmentFile") != ["-%h/chester-reports/.env"]:
            faults.append(f"{vname}: EnvironmentFile not the optional repo one")
        if t.get("OnCalendar") != [vcal] or t.get("Persistent") != ["false"]:
            faults.append(f"chester-flashalpha.timer: {t.get('OnCalendar')} / "
                          f"Persistent {t.get('Persistent')}")
        if "chester-flashalpha.timer" in timers:
            faults.append("chester-flashalpha.timer is in DEPLOY_TIMERS")
    return faults


def aud2() -> None:
    print(f"\n{LINE}\nAUD-2: memory caps, the auction unit, the Gateway's OOM order, "
          f"the backup's end\n{LINE}")
    faults = check_aud2()
    if faults:
        for f in faults:
            bad(f)
    else:
        ok(f"the six heavy units carry their caps as percentages ({', '.join(f'{k.split('.')[0]} {h}/{m}' for k, (h, m, _, _) in MEMORY_CAPS.items())}); "
           f"at 4 GB they sum to {sum(cap_at(m, 4) for _, m, _, _ in MEMORY_CAPS.values()):.2f}G "
           f"and at 8 GB to {sum(cap_at(m, 8) for _, m, _, _ in MEMORY_CAPS.values()):.2f}G, "
           f"each 8 GB figure AUD-2's; "
           f"the auction unit neither wants nor starts the Gateway and runs "
           f"sandboxed; the OOM order holds (Gateway -500 < EOD 300 < the reports "
           f"500); the backup ends by 04:35, "
           f"before the 05:00 Weekly")
    # The rules are themselves checked: each defect, alone, is caught.
    import shutil
    import tempfile
    for label, unit, old, new in (
            ("a missing cap", "chester-weekly.service", "MemoryMax=31%", ""),
            ("an absolute cap back", "chester-weekly.service", "MemoryMax=31%",
             "MemoryMax=2.5G"),
            ("a percentage off the 8 GB case", "chester-eod.service", "MemoryMax=25%",
             "MemoryMax=40%"),
            ("the Gateway wanted again", "chester-auction.service",
             "[Unit]", "[Unit]\nWants=ibgateway.service"),
            ("no OOM order", "ibgateway.service", "OOMScoreAdjust=-500", ""),
            ("the Gateway above the capture", "ibgateway.service",
             "OOMScoreAdjust=-500", "OOMScoreAdjust=400"),
            ("the capture level with the reports", "chester-eod.service",
             "OOMScoreAdjust=300", "OOMScoreAdjust=500"),
            ("a report below the capture", "chester-voices.service",
             "OOMScoreAdjust=500", "OOMScoreAdjust=200"),
            ("a report with no score", "chester-restore-drill.service",
             "OOMScoreAdjust=500", ""),
            ("the old 2h30 timeout", "chester-backup.service",
             "TimeoutStartSec=2h", "TimeoutStartSec=2h30min"),
            # 6b part 2: the capture units.
            ("a capture without its cap", "chester-dealer-0945.service",
             "MemoryMax=12%", ""),
            ("the vendor writer at the wrong minute", "chester-flashalpha.timer",
             "OnCalendar=Mon-Fri 16:25", "OnCalendar=Mon-Fri 16:05"),
            ("a capture level with the reports", "chester-dealer-1230.service",
             "OOMScoreAdjust=300", "OOMScoreAdjust=500"),
            ("a capture timer that catches up", "chester-dealer-1230.timer",
             "Persistent=false", "Persistent=true"),
            ("a capture at the wrong minute", "chester-dealer-0945.timer",
             "OnCalendar=Mon-Fri 09:45", "OnCalendar=Mon-Fri 09:30")):
        with tempfile.TemporaryDirectory() as td:
            for f in UNIT_DIR.iterdir():
                if f.is_file():
                    shutil.copy(f, td)
            p = Path(td) / unit
            p.write_text(p.read_text(encoding="utf-8").replace(old, new, 1),
                         encoding="utf-8")
            check(bool(check_aud2(Path(td))), f"and {label} in {unit} is caught")


def check(c: bool, m: str) -> None:
    ok(m) if c else bad(m)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    self_test()
    check_environment_file()
    aud2()
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
