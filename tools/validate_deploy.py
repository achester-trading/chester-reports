"""
Validation gate for the unattended deploy and the permission allowlist.

Two things are pinned here and they are the same claim from two sides: that
`make deploy` cannot take a running unit down, and that the permission rules
which let it run unattended cannot be widened by accident.

  A  THE DEPLOY EXECUTES NO DESTRUCTIVE VERB. stop, disable, restart, kill and
     mask appear in the recipe only inside echoed text -- the deploy PRINTS the
     restart command and never runs it. Checked line by line rather than by
     grepping the whole recipe, because the remediation message necessarily
     contains the word "restart" and a naive check would either fail on it or be
     deleted for failing on it.
  B  THE SEQUENCE IS THE DECLARED ONE. Six steps, in order, and a declared timer
     list rather than a glob over the unit directory.
  C  THE ALLOW LIST IS EXACTLY THE REVIEWED ONE. Not a superset. An entry nobody
     reviewed is the whole risk of an allowlist, so a fifteenth entry fails this
     gate until somebody updates the expected list on purpose.
  D  THE DENY PATTERNS ACTUALLY MATCH. Every dangerous command shape is run
     against the real patterns with fnmatch -- the same glob semantics Claude
     Code applies -- so this tests the rules rather than their presence. A deny
     list full of near-miss patterns looks identical to a working one in a diff.
  E  DENY BEATS ALLOW WHERE THEY OVERLAP, demonstrated on the overlaps that
     actually exist: `make deploy*` is allowed while a deploy containing a
     restart is denied, and `ssh vps cat *` is allowed while reading .env is
     denied.
  F  CLAUDE.md DOCUMENTS EVERY DENY CATEGORY, because a rule whose reason is
     not written down is a rule the next person removes.
  G  EVERY make ENTRY IS REACHABLE WITHOUT make. `make` is absent on the authoring
     laptop, so an allow entry that only matches a make command grants nothing
     there -- the gate run or the deploy falls back to a prompt and the allowlist
     is decoration. Each make entry is asserted to travel with the spelling that
     actually runs, and scripts/make.sh is audited the same way the deploy is.
  H  ONE ssh CONNECTION. The box-side work runs in scripts/deploy_remote.sh,
     shipped over a single `ssh ... 'bash -s' < deploy_remote.sh` -- fifteen
     connections a minute timed out on port 22 on 28 Sep 2026. Asserted
     statically (one executed ssh, no ControlMaster, the body parsed whole before
     it runs) and by BEHAVIOUR: deploy.sh run against a fake ssh returns 0, 3, 4
     and 1 in exactly the old cases and prints the restart command without
     running it.
  I  THE BOX'S SELF-DEPLOY NEVER RESTARTS (A-4, 9 Oct 2026). chester-deploy.timer
     runs scripts/run_self_deploy.sh, which runs the box half above when main's
     deploy/systemd/ has changed. Held here: the unit runs that wrapper and
     nothing else, and its timer is in DEPLOY_TIMERS; the wrapper executes no
     systemctl at all and the restart-pending ledger only is-active and show;
     every timer firing, plus its delay, falls inside CLAUDE.md's operating
     windows, and the wrapper's own ET guard agrees with them minute by minute;
     and END TO END on a scratch box: outside the window it touches nothing,
     inside it copies a changed unit, writes "restart pending: <unit>" for one
     that was running, does nothing on an unchanged tree, prunes the line once
     the unit has stopped, and never sends systemctl a destructive verb.

    python tools/validate_deploy.py
"""

from __future__ import annotations

import fnmatch
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MAKEFILE = REPO / "Makefile"
# The deploy's BODY lives in the script; the Makefile only delegates to it. Both
# are checked: the script for what it does, the Makefile for the fact that it
# adds nothing of its own.
DEPLOY_SH = REPO / "scripts" / "deploy.sh"
# ... and the box-side half it ships over one ssh connection. Part of the same
# fixed body: every rule below that reads "the deploy" reads both files.
DEPLOY_REMOTE = REPO / "scripts" / "deploy_remote.sh"
# The make targets, for machines without make -- allowlisted, so audited here too.
MAKE_SH = REPO / "scripts" / "make.sh"
# The box's self-deploy (A-4): its wrapper, the restart-pending ledger, its units.
SELF_DEPLOY = REPO / "scripts" / "run_self_deploy.sh"
LEDGER = REPO / "scripts" / "restart_pending.sh"
DEPLOY_SERVICE = REPO / "deploy" / "systemd" / "chester-deploy.service"
DEPLOY_TIMER = REPO / "deploy" / "systemd" / "chester-deploy.timer"
SETTINGS = REPO / ".claude" / "settings.json"
CLAUDE_MD = REPO / "CLAUDE.md"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78

# Exactly what was reviewed. A superset is a widening nobody signed off on, so
# this is compared for EQUALITY and not containment.
EXPECTED_ALLOW = [
    "Bash(make validate)",
    "Bash(make html)",
    "Bash(make deploy*)",
    # The same three, spelled the way they run on a machine without make. See
    # group G: a make entry without its mirror grants nothing on the laptop.
    "Bash(bash scripts/make.sh validate)",
    "Bash(bash scripts/make.sh html)",
    "Bash(bash scripts/deploy.sh*)",
    "Bash(git add*)",
    "Bash(git commit*)",
    "Bash(git push*)",
    "Bash(git pull*)",
    "Bash(ssh vps systemctl --user is-active*)",
    "Bash(ssh vps systemctl --user list-timers*)",
    "Bash(ssh vps cat *)",
    "Bash(ssh vps tail *)",
]

# Command shapes that MUST be denied, grouped by the reason they are denied. The
# grouping is what group F checks against CLAUDE.md, so the two cannot drift.
MUST_DENY = {
    "unit lifecycle": [
        "ssh vps systemctl --user stop ibgateway",
        "ssh vps 'systemctl --user disable chester-eod.timer'",
        "ssh vps systemctl --user restart chester-heartbeat.service",
        "ssh vps systemctl --user kill ibgateway.service",
        "systemctl --user stop chester-eod.timer",
        "systemctl --user restart ibgateway",
        "cd /x && ssh vps systemctl --user disable chester-backup.timer",
    ],
    "state and data deletion": [
        "ssh vps rm ~/state/eod_heartbeat",
        "ssh vps 'rm -rf ~/state'",
        "rm data/chester.db",
        "rm -rf data/chains",
        "ssh vps rm /home/ari/state/morning_heartbeat",
        "rm data/pin_log.csv",
    ],
    "register writes": [
        "python tools/decide.py record --instrument SPY --direction long",
        "python tools/decide.py set-status --id abc --status closed",
        "bash scripts/decide_remote.sh record --instrument QQQ",
        "scripts/decide_remote.sh set-status --id x --status active",
        "python tools/migrate_register.py import --in x.json",
        # 6c-2: confirming or rejecting a PROPOSED narrative is the narrative
        # register's one human gate, on the same argument as a decision write.
        "python -m altdata.narratives confirm dollar_funding_squeeze",
        "ssh vps '.venv/bin/python -m altdata.narratives reject some_story'",
    ],
    "privilege escalation": [
        "sudo apt install x",
        "ssh vps sudo systemctl restart something",
    ],
    "order placement": [
        "python -c 'ib.placeOrder(c, o)'",
        "python tools/place_order.py --symbol SPY",
        "python -m altdata.sources.ibkr_orders",
        "python x.py --allow-live",
        "python -c 'ib.bracketOrder(...)'",
        "python -m order_router",
    ],
    "secrets": [
        "ssh vps cat ~/chester-reports/.env",
        "ssh vps tail -5 /home/ari/chester-reports/.env",
        "ssh vps cat ~/ibc/config.ini",
        "echo $ANTHROPIC_API_KEY",
    ],
}

# Shapes that MUST remain allowed. A deny list that also blocks the work is a
# deny list somebody switches off wholesale.
MUST_NOT_DENY = [
    "make validate",
    "make html",
    "make deploy",
    "bash scripts/make.sh validate",
    "bash scripts/make.sh html",
    "bash scripts/deploy.sh",
    "git add -A",
    "git commit -q -F -",
    "git push",
    "git pull --ff-only",
    "ssh vps systemctl --user is-active ibgateway",
    "ssh vps systemctl --user list-timers --all",
    "ssh vps cat /home/ari/logs/run_eod-2026-09.log",
    "ssh vps tail -20 /home/ari/logs/daily_close-2026-09.log",
]


def ok(m: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    ok(m) if c else bad(m)


def deploy_recipe() -> str:
    """The Makefile's deploy recipe -- which should be a delegation, nothing more."""
    m = re.search(r"^deploy:\n((?:\t.*\n|\n)*)", MAKEFILE.read_text(encoding="utf-8"),
                  re.M)
    return m.group(1) if m else ""


def deploy_body() -> str:
    """The fixed deploy body: the laptop half, then the box half it ships."""
    return (DEPLOY_SH.read_text(encoding="utf-8") + "\n"
            + DEPLOY_REMOTE.read_text(encoding="utf-8"))


def _executed_lines(text: str) -> list[str]:
    """Lines that RUN something: not comments, not inside echo/printf."""
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.append(re.sub(r"""\b(echo|printf)\b[^;]*""", "", line))
    return out


def settings() -> dict:
    return json.loads(SETTINGS.read_text(encoding="utf-8"))


def bash_patterns(rules: list) -> list[str]:
    """The inner pattern of every Bash(...) rule."""
    out = []
    for r in rules:
        m = re.fullmatch(r"Bash\((.*)\)", str(r).strip(), re.S)
        if m:
            out.append(m.group(1))
    return out


def matches_any(cmd: str, patterns: list[str]) -> list[str]:
    """Which patterns match this command, under glob semantics."""
    return [p for p in patterns if fnmatch.fnmatch(cmd, p)]


def group_a() -> None:
    print(f"{LINE}\nA. THE DEPLOY EXECUTES NO DESTRUCTIVE VERB\n{LINE}")
    check(DEPLOY_SH.is_file(), f"{DEPLOY_SH.relative_to(REPO)} exists")
    recipe = deploy_body()
    make_recipe = deploy_recipe()
    check(bool(make_recipe), "the deploy: target was found in the Makefile")
    check("scripts/deploy.sh" in make_recipe,
          "and it DELEGATES to the script rather than reimplementing it -- the "
          "recipe was unrunnable from either machine, since make is absent on the "
          "laptop and the box cannot resolve the laptop's ssh alias for itself")
    check(len([l for l in make_recipe.splitlines() if l.strip()]) == 1,
          "the recipe is one line, so there is no second copy of the logic to "
          "drift from the first")

    # Line by line, and only lines that RUN something. The remediation message
    # has to contain "restart" -- that is its entire job -- so a whole-recipe
    # grep would either fail on the correct implementation or get deleted.
    offenders = []
    for raw in recipe.splitlines():
        line = raw.strip().rstrip("\\").strip()
        if not line:
            continue
        # Strip everything inside an echo/printf: that is printed text, not a
        # command. Crude but exactly right for this recipe's shape.
        exec_part = re.sub(r"""\b(echo|printf)\b[^;]*""", "", line)
        for verb in ("stop", "disable", "restart", "kill", "mask"):
            if re.search(rf"systemctl[^;]*\b{verb}\b", exec_part):
                offenders.append((verb, line[:80]))
    check(not offenders,
          f"no systemctl stop/disable/restart/kill/mask is EXECUTED "
          f"({offenders or 'none'})")

    # And the verbs DO appear, in echoes, because the deploy's job when it cannot
    # act is to hand over the exact command.
    check("systemctl --user restart" in recipe,
          "the restart command IS present -- printed for the operator, which is "
          "the whole point of exiting 3 instead of acting")
    check(re.search(r"echo .*systemctl --user restart", recipe) is not None,
          "and it appears inside an echo rather than as a command")

    check("exit 3" in recipe or "rc=3" in recipe,
          "a changed running unit exits 3")
    check("--ff-only" in recipe,
          "the pull is --ff-only: no merge commit on a box whose rule is that it "
          "runs code and never edits it")


def group_b() -> None:
    print(f"\n{LINE}\nB. THE SEQUENCE IS THE DECLARED ONE\n{LINE}")
    recipe = deploy_body()
    # Anchored on the ECHOED banners ("-- 1. pull"), not on the numbered list in
    # the script's header comment. The header says the same six things in the same
    # order, so matching it would let the order check pass on a header a reordered
    # body had outgrown -- which is exactly the drift worth catching.
    steps = [
        ("1. pull", r"-- 1\. pull"),
        ("2. copy units", r"-- 2\. copy units"),
        ("3. daemon-reload", r"-- 3\. daemon-reload"),
        ("4. enable", r"-- 4\. enable"),
        ("5. drift/heartbeat", r"-- 5\. drift check and heartbeat"),
        ("6. roster", r"-- 6\. timer roster"),
    ]
    positions = []
    for label, pat in steps:
        m = re.search(pat, recipe)
        check(m is not None, f"step present: {label}")
        positions.append(m.start() if m else -1)
    check(positions == sorted(positions) and -1 not in positions,
          f"and the six steps run IN ORDER ({positions})")

    check("daemon-reload" in recipe, "daemon-reload is run")
    check("list-timers" in recipe, "the roster is printed")
    check("check_heartbeat_cron.sh" in recipe,
          "the heartbeat checker is the box's own wrapper, so the deploy reads "
          "the same verdict the timer writes rather than a second opinion")

    mk = MAKEFILE.read_text(encoding="utf-8")
    m = re.search(r'DEPLOY_TIMERS="([^"]*)"', recipe, re.S)
    check(m is not None, "DEPLOY_TIMERS is a declared list")
    timers = (m.group(1).split() if m else [])
    check(bool(timers) and all(t.endswith(".timer") for t in timers),
          f"and holds only .timer units ({len(timers)} of them)")
    check(not re.search(r"enable[^;]*\*\.timer", recipe),
          "the enable loop is NOT a glob over the unit directory -- ibgateway's "
          "units are held back behind a witnessed clean start and a glob would "
          "enable them on the first deploy")
    check("ibgateway.timer" not in timers and
          "ibgateway-restart.timer" not in timers,
          "and the held-back Gateway timers are absent from the list")
    check(re.search(r"is-enabled", recipe) is not None,
          "enable --now is guarded by is-enabled, so it only ever ADDS a timer")
    check(".PHONY" in mk and re.search(r"^\.PHONY:.*\bdeploy\b", mk, re.M),
          "deploy is in .PHONY")

    # THE MAKEFILE DECLARES NO DEPLOY SETTINGS OF ITS OWN. It used to carry
    # DEPLOY_HOST, DEPLOY_REPO, DEPLOY_UNIT_DIR, DEPLOY_STATE_DIR and a second copy
    # of DEPLOY_TIMERS. Once the recipe became a delegation they were all inert --
    # make does not export its variables to a recipe's child process, so
    # `make deploy DEPLOY_HOST=other` read like an override and still deployed to
    # vps -- and the duplicated timer list was a second place to edit and forget.
    stale = [v for v in ("DEPLOY_HOST", "DEPLOY_REPO", "DEPLOY_UNIT_DIR",
                         "DEPLOY_STATE_DIR", "DEPLOY_TIMERS")
             if re.search(rf"^{v}\s*[?:]?=", mk, re.M)]
    check(not stale,
          f"and the Makefile declares no deploy setting of its own -- a make "
          f"variable is not exported to the delegated script, so one here would "
          f"read like an override and do nothing ({stale or 'none'})")


def group_c() -> None:
    print(f"\n{LINE}\nC. THE ALLOW LIST IS EXACTLY THE REVIEWED ONE\n{LINE}")
    check(SETTINGS.is_file(), f"{SETTINGS.relative_to(REPO)} exists")
    s = settings()
    perms = s.get("permissions") or {}
    allow = list(perms.get("allow") or [])
    check(allow == EXPECTED_ALLOW,
          f"the allow list is exactly the {len(EXPECTED_ALLOW)} reviewed entries "
          f"(extra: {sorted(set(allow) - set(EXPECTED_ALLOW))}, "
          f"missing: {sorted(set(EXPECTED_ALLOW) - set(allow))})")
    check(bool(perms.get("deny")), "a deny list is present")
    # An allowlist whose deny list is shorter than its allow list is usually a
    # deny list that was not thought about.
    check(len(perms["deny"]) >= len(allow),
          f"and is not an afterthought ({len(perms['deny'])} deny vs "
          f"{len(allow)} allow)")


def group_d() -> None:
    print(f"\n{LINE}\nD. THE DENY PATTERNS ACTUALLY MATCH\n{LINE}")
    deny = bash_patterns(settings()["permissions"]["deny"])

    for reason, cmds in MUST_DENY.items():
        unmatched = [c for c in cmds if not matches_any(c, deny)]
        check(not unmatched,
              f"{reason}: all {len(cmds)} shape(s) denied "
              f"({unmatched or 'none slipped through'})")

    allow = bash_patterns(settings()["permissions"]["allow"])
    still_denied = [c for c in MUST_NOT_DENY if matches_any(c, deny)]
    check(not still_denied,
          f"and the work is NOT blocked -- a deny list that stops the job is one "
          f"somebody switches off wholesale ({still_denied or 'all clear'})")
    unallowed = [c for c in MUST_NOT_DENY if not matches_any(c, allow)]
    check(not unallowed,
          f"every intended command is matched by an allow rule "
          f"({unallowed or 'all matched'})")


def group_e() -> None:
    print(f"\n{LINE}\nE. DENY BEATS ALLOW WHERE THEY OVERLAP\n{LINE}")
    p = settings()["permissions"]
    allow, deny = bash_patterns(p["allow"]), bash_patterns(p["deny"])

    # The two overlaps that actually exist in this file. Both are cases where the
    # allow rule is deliberately broad and the deny rule is what makes it safe.
    overlaps = [
        ("a deploy that grew a restart",
         "make deploy && ssh vps systemctl --user restart ibgateway"),
        ("reading the secrets file through the allowed cat",
         "ssh vps cat /home/ari/chester-reports/.env"),
        ("reading IBC's credentials through the allowed cat",
         "ssh vps cat /home/ari/ibc/config.ini"),
    ]
    for label, cmd in overlaps:
        a, d = matches_any(cmd, allow), matches_any(cmd, deny)
        check(bool(d),
              f"{label}: denied by {d[:1] or 'NOTHING'}"
              + (f", and an allow rule {a[:1]} would otherwise have permitted it"
                 if a else " (no allow rule reaches it either)"))

    check(any("env" in x for x in deny),
          "the secrets deny exists at all -- `ssh vps cat *` is allowed, so "
          "without it an unattended read of .env is permitted, against "
          "CLAUDE.md's own standing rule on secrets")


def group_f() -> None:
    print(f"\n{LINE}\nF. CLAUDE.md DOCUMENTS EVERY DENY CATEGORY\n{LINE}")
    text = CLAUDE_MD.read_text(encoding="utf-8")
    check("What runs without asking" in text,
          "the section exists, named as asked")
    section = text.split("What runs without asking", 1)[-1]
    # Stop at the next top-level heading so a later section cannot satisfy this.
    section = re.split(r"\n## ", section)[0]

    for reason in MUST_DENY:
        key = reason.split()[0].lower()
        check(key in section.lower(),
              f"the '{reason}' deny is explained in that section")
    for word in ("stop", "disable", "restart", "kill", "sudo", "decide.py",
                 "order", "deny"):
        check(word.lower() in section.lower(),
              f"the section mentions {word!r}")
    check("precedence" in section.lower() or "takes precedence" in section.lower(),
          "and states that deny takes precedence over allow")
    check("exit 3" in section or "exits 3" in section,
          "and documents the exit-3 handover")


def group_g() -> None:
    print(f"\n{LINE}\nG. EVERY make ENTRY IS REACHABLE WITHOUT make\n{LINE}")
    allow = list((settings().get("permissions") or {}).get("allow") or [])
    pats = bash_patterns(allow)

    # `make` is absent on the authoring laptop, so an allow entry that only ever
    # matches a make command grants nothing there: the gate run or the deploy goes
    # back to a prompt, and an allowlist that does not reach the real command is
    # decoration. Each make entry therefore needs the spelling that runs.
    mirrors = {
        "make validate": "bash scripts/make.sh validate",
        "make html": "bash scripts/make.sh html",
        "make deploy": "bash scripts/deploy.sh",
    }
    for make_form, real_form in mirrors.items():
        has_make = any(fnmatch.fnmatch(make_form, p) for p in pats)
        has_real = any(fnmatch.fnmatch(real_form, p) for p in pats)
        check(has_make == has_real,
              f"{make_form!r} and {real_form!r} are allowed together -- neither "
              f"machine is left having to type the other one")
        check(has_real, f"{real_form!r} is allowed")

    check(MAKE_SH.is_file(), f"{MAKE_SH.relative_to(REPO)} exists")
    shim = MAKE_SH.read_text(encoding="utf-8")

    # The shim runs gates and rebuilds HTML. It has no business touching a unit or
    # deleting anything, and it is allowlisted, so this is asserted rather than
    # assumed.
    offenders = [
        v for v in ("systemctl", "rm -rf", "placeOrder", "decide.py", "sudo")
        if re.search(rf"^\s*[^#\n]*{re.escape(v)}", shim, re.M)
    ]
    check(not offenders,
          f"and executes nothing that touches a unit, a register or a file it "
          f"cannot rebuild ({offenders or 'clean'})")

    # THE POINT OF THE MAKEFILE IS ONE LIST. A shim carrying its own copy of the
    # validator names would be the third place the list lives, which is how four
    # gates drifted out of CI while still passing locally.
    check("mk_list" in shim and "Makefile" in shim,
          "the shim READS the gate list out of the Makefile rather than keeping "
          "its own copy -- one list is the Makefile's entire reason to exist")
    for name in ("PY_VALIDATORS", "EXTRA", "SH_VALIDATORS", "DATA_GATES"):
        check(re.search(rf'mk_list {name}\b', shim) is not None,
              f"and reads {name} from it")
    check(not re.search(r"^\s*PY_VALIDATORS=[\"']?tools/", shim, re.M),
          "and hardcodes no validator path of its own")
    # figures has an ADOPT=1 mode that overwrites the committed Currencies
    # figures, which CLAUDE.md says not to run yet.
    check("figures)" not in shim,
          "and does not wrap 'figures', whose ADOPT=1 mode overwrites the "
          "committed figures CLAUDE.md holds canonical")

    # The deploy stays one shape. Two ways to spell it is two shapes to allowlist.
    check("deploy.sh" not in shim.split("# The deploy is NOT here")[-1].split("set -uo")[-1],
          "and does not also wrap the deploy, which keeps the deploy one shape")


def group_h() -> None:
    print(f"\n{LINE}\nH. ONE ssh CONNECTION, SAME EXIT CODES\n{LINE}")
    import os
    import shutil
    import subprocess
    import tempfile
    check(DEPLOY_REMOTE.is_file(), f"{DEPLOY_REMOTE.relative_to(REPO)} exists")
    local = DEPLOY_SH.read_text(encoding="utf-8")
    remote = DEPLOY_REMOTE.read_text(encoding="utf-8")
    ssh_calls = [l for l in _executed_lines(local) if re.search(r"(^|\s)ssh\s", l)]
    check(len(ssh_calls) == 1,
          f"deploy.sh executes exactly ONE ssh -- fifteen a minute timed out on "
          f"port 22 on 28 Sep ({len(ssh_calls)}: {ssh_calls})")
    check(bool(ssh_calls) and "bash -s" in ssh_calls[0]
          and re.search(r'<\s*"\$REMOTE"', local) is not None,
          "and that one call ships deploy_remote.sh over stdin to `bash -s`")
    check(not [l for l in _executed_lines(remote) if re.search(r"(^|\s)ssh\s", l)],
          "the box half opens no ssh of its own")
    check(not [l for l in _executed_lines(local + "\n" + remote)
               if re.search(r"Control(Master|Path|Persist)", l)],
          "no ssh ControlMaster -- not available from the Windows laptop")
    check("BatchMode=yes" in local,
          "BatchMode: a deploy never waits at a password prompt")
    check(re.search(r"^deploy_main\s*</dev/null", remote, re.M) is not None
          and re.search(r"^deploy_main\(\)\s*\{", remote, re.M) is not None,
          "the box half is ONE function called with </dev/null -- parsed whole "
          "before it runs, so no command inside can read the rest of the script "
          "off the ssh pipe as its input")
    check(len(re.findall(r'^DEPLOY_TIMERS="', local + "\n" + remote, re.M)) == 1
          and 'DEPLOY_TIMERS="' in remote,
          "the timer list is declared once, in the half that enables timers")
    check(all(m in remote for m in ("@@NEEDS", "@@DRIFT", "@@HB"))
          and "grep -v '^@@'" in local,
          "the box half reports through three markers the laptop half parses and "
          "does not print")

    bash = shutil.which("bash")
    if not bash:
        ok("no bash here; the behavioural half of H runs where bash exists")
        return
    canned = {
        "clean": ("-- 1. pull --ff-only\n@@NEEDS \n@@DRIFT clean\n@@HB 0\n", 0),
        "needs": ("-- 1. pull --ff-only\n@@NEEDS  chester-eod.timer\n"
                  "@@DRIFT clean\n@@HB 0\n", 0),
        "drift": ("-- 1. pull --ff-only\n@@NEEDS \n@@DRIFT dropin\n@@HB 8\n", 0),
        "fail":  ("-- 1. pull --ff-only\nfatal: not possible to fast-forward\n", 1),
        "noconn": ("", 255),
    }
    want = {"clean": 0, "needs": 3, "drift": 4, "fail": 1, "noconn": 1}
    with tempfile.TemporaryDirectory() as td:
        fake = Path(td) / "ssh"
        fake.write_text(
            "#!/usr/bin/env bash\n"
            "cat >/dev/null\n"                       # consume the shipped script
            'printf "%b" "$FAKE_OUT"\n'
            'echo "$@" >> "$FAKE_LOG"\n'
            'exit "$FAKE_RC"\n', encoding="utf-8", newline="\n")
        fake.chmod(0o755)
        for mode, (outp, rc) in canned.items():
            log = Path(td) / f"{mode}.log"
            env = {**os.environ, "PATH": f"{td}{os.pathsep}{os.environ.get('PATH', '')}",
                   "FAKE_OUT": outp, "FAKE_RC": str(rc), "FAKE_LOG": str(log)}
            r = subprocess.run([bash, str(DEPLOY_SH)], capture_output=True,
                               text=True, env=env, cwd=str(REPO))
            calls = (log.read_text().splitlines() if log.exists() else [])
            check(r.returncode == want[mode] and len(calls) <= 1
                  and "@@" not in r.stdout,
                  f"{mode}: exit {r.returncode} (want {want[mode]}), "
                  f"{len(calls)} ssh call(s), no marker printed")
            if mode == "needs":
                check("ssh vps 'systemctl --user restart chester-eod.timer'"
                      in r.stdout,
                      "a changed running unit PRINTS its restart command -- and the "
                      "fake ssh saw one call, so it was not run")
            if mode == "clean":
                check("DEPLOY CLEAN." in r.stdout and "-- 1. pull" in r.stdout,
                      "a clean run streams the box's sections and ends DEPLOY CLEAN")

    # THE BOX HALF, END TO END, READ FROM STDIN as ssh delivers it: a scratch
    # clone, a fake systemctl that logs every call, a fake heartbeat. It must
    # pull, copy, report the changed ACTIVE unit, enable only the timer not yet
    # enabled, and never send systemctl a destructive verb.
    git = shutil.which("git")
    if not git:
        ok("no git here; the end-to-end half of H runs where git exists")
        return
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        org = t / "origin"
        (org / "deploy" / "systemd").mkdir(parents=True)
        (org / "scripts").mkdir()
        (org / "deploy" / "systemd" / "a.service").write_text(
            "[Unit]\n", encoding="utf-8", newline="\n")
        (org / "deploy" / "systemd" / "chester-eod.timer").write_text(
            "[Timer]\n", encoding="utf-8", newline="\n")
        hb = org / "scripts" / "check_heartbeat_cron.sh"
        hb.write_text(
            "#!/usr/bin/env bash\n"
            'echo "state=ok drift=clean" > "$CHESTER_STATE_DIR/heartbeat_check_status"\n'
            "exit 0\n", encoding="utf-8", newline="\n")
        hb.chmod(0o755)
        g = {"cwd": str(org), "capture_output": True, "text": True}
        subprocess.run([git, "init", "-q"], **g)
        subprocess.run([git, "add", "-A"], **g)
        subprocess.run([git, "-c", "user.email=t@t", "-c", "user.name=t",
                        "-c", "core.autocrlf=false", "commit", "-qm", "init"], **g)
        subprocess.run([git, "clone", "-q", str(org), str(t / "box")],
                       capture_output=True, text=True)
        for d in ("bin", "units", "state", "home"):
            (t / d).mkdir()
        (t / "units" / "a.service").write_text("[Unit]\nold\n", encoding="utf-8")
        sysctl = t / "bin" / "systemctl"
        sysctl.write_text(
            "#!/usr/bin/env bash\n"
            'echo "$*" >> "$SYSLOG"\n'
            'case "$*" in *is-active*) exit 0;; *is-enabled*chester-eod*) exit 1;;'
            " *is-enabled*) exit 0;; esac\nexit 0\n", encoding="utf-8", newline="\n")
        sysctl.chmod(0o755)
        slog = t / "sys.log"
        env = {**os.environ, "HOME": str(t / "home"), "SYSLOG": str(slog),
               "PATH": f"{t / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}"}
        with open(DEPLOY_REMOTE, "rb") as script:
            r = subprocess.run([bash, "-s", "--", str(t / "box"), str(t / "units"),
                                str(t / "state")], stdin=script,
                               capture_output=True, env=env)
        out = r.stdout.decode("utf-8", "replace")
        calls = slog.read_text().splitlines() if slog.exists() else []
        check(r.returncode == 0 and "-- 6. timer roster" in out
              and "@@NEEDS  a.service" in out and "@@DRIFT clean" in out,
              f"read from stdin, the box half runs all six steps and reports the "
              f"changed ACTIVE unit (exit {r.returncode})")
        check(calls.count("--user enable --now chester-eod.timer") == 1
              and sum("enable --now" in c for c in calls) == 1,
              "it enables only the declared timer that was not enabled")
        check(not [c for c in calls if re.search(
                  r"\b(stop|disable|restart|kill|mask)\b", c)],
              f"and systemctl never receives a destructive verb "
              f"({len(calls)} calls, all read/reload/enable)")


DESTRUCTIVE = ("stop", "disable", "restart", "kill", "mask")


def window_open(dow: int, sec: int) -> bool:
    """CLAUDE.md's operating windows, ET: weekdays 09:05-15:40 and 17:20-23:30;
    weekends open, clear of the Sunday 05:00 Weekly (04:00-06:59). `dow` is ISO
    (1 = Monday), `sec` seconds after midnight."""
    hm = lambda h, m: (h * 60 + m) * 60                         # noqa: E731
    if dow <= 5:
        return hm(9, 5) <= sec <= hm(15, 40) or hm(17, 20) <= sec <= hm(23, 30)
    if dow == 7 and hm(4, 0) <= sec < hm(7, 0):
        return False
    return True


def _expand(field: str, top: int) -> list[int]:
    """One OnCalendar time field as this timer writes it: '*', 'N', 'a..b' and
    comma lists of those."""
    if field == "*":
        return list(range(top))
    out: list[int] = []
    for part in field.split(","):
        a, _, b = part.partition("..")
        out += list(range(int(a), int(b or a) + 1))
    return out


def calendar_firings(text: str) -> list[tuple[int, int]]:
    """(ISO weekday, seconds after midnight) for every OnCalendar line, in the
    timer's own zone. Refuses a shape it does not parse rather than guessing."""
    days = {"Mon": 1, "Tue": 2, "Wed": 3, "Thu": 4, "Fri": 5, "Sat": 6, "Sun": 7}
    out = []
    for line in re.findall(r"^OnCalendar=(.+)$", text, re.M):
        m = re.fullmatch(r"(\w{3})(?:-(\w{3}))? \*-\*-\* ([\d.,*]+):([\d.,]+):00 "
                         r"America/New_York", line.strip())
        if not m:
            raise ValueError(f"unparsed OnCalendar: {line}")
        d0, d1 = days[m.group(1)], days[m.group(2) or m.group(1)]
        for d in range(d0, d1 + 1):
            for h in _expand(m.group(3), 24):
                for mi in _expand(m.group(4), 60):
                    out.append((d, (h * 60 + mi) * 60))
    return sorted(set(out))


def _seconds(v: str) -> int:
    m = re.fullmatch(r"(\d+)\s*(s|sec|min|m)?", v.strip())
    if not m:
        raise ValueError(f"unparsed duration: {v}")
    return int(m.group(1)) * (60 if m.group(2) in ("min", "m") else 1)


def group_i() -> None:
    print(f"\n{LINE}\nI. THE BOX'S SELF-DEPLOY NEVER RESTARTS (A-4)\n{LINE}")
    import os
    import shutil
    import subprocess
    import tempfile
    for p in (SELF_DEPLOY, LEDGER, DEPLOY_SERVICE, DEPLOY_TIMER):
        check(p.is_file(), f"{p.relative_to(REPO)} exists")
    svc = DEPLOY_SERVICE.read_text(encoding="utf-8")
    tmr = DEPLOY_TIMER.read_text(encoding="utf-8")
    wrapper = SELF_DEPLOY.read_text(encoding="utf-8")
    ledger = LEDGER.read_text(encoding="utf-8")
    remote = DEPLOY_REMOTE.read_text(encoding="utf-8")

    execs = re.findall(r"^Exec\w*=(.*)$", svc, re.M)
    check(execs == ["%h/chester-reports/scripts/run_self_deploy.sh"],
          f"chester-deploy.service runs the wrapper and nothing else ({execs})")
    m = re.search(r'DEPLOY_TIMERS="([^"]*)"', remote, re.S)
    check(m is not None and "chester-deploy.timer" in m.group(1).split(),
          "chester-deploy.timer is in DEPLOY_TIMERS, so the operator's next deploy "
          "enables it and no glob ever does")
    check("scripts/deploy_remote.sh" in wrapper,
          "the wrapper runs the SAME box half the laptop ships, not a copy of it")

    # NO DESTRUCTIVE VERB, and tighter than group A: the wrapper executes no
    # systemctl at all, and the ledger only reads.
    wr_sys = [l for l in _executed_lines(wrapper) if re.search(r"\bsystemctl\b", l)]
    check(not wr_sys, f"the wrapper executes no systemctl of its own ({wr_sys or 'none'})")
    verbs = set()
    for l in _executed_lines(ledger):
        verbs |= set(re.findall(r"systemctl\s+--user\s+([\w-]+)", l))
    check(verbs == {"is-active", "show"},
          f"the ledger's systemctl verbs are is-active and show only ({sorted(verbs)})")
    offenders = [(v, l[:70]) for t in (wrapper, ledger, svc)
                 for l in _executed_lines(t) for v in DESTRUCTIVE
                 if re.search(rf"systemctl[^;]*\b{v}\b", l)]
    check(not offenders, f"no stop/disable/restart/kill/mask is executed by the "
                         f"wrapper, the ledger or the unit ({offenders or 'none'})")
    check(re.search(r"^self_deploy_main\s*</dev/null", wrapper, re.M) is not None,
          "the wrapper is one function, parsed whole before the pull can rewrite it")
    check("--ff-only" in wrapper, "the wrapper's pull is --ff-only")

    # THE CALENDAR, firing by firing.
    claude = CLAUDE_MD.read_text(encoding="utf-8")
    check("weekdays 09:05–15:40 and 17:20–23:30 ET" in claude
          and "Sunday 05:00" in claude,
          "the windows checked below are CLAUDE.md's, as written there")
    try:
        fires = calendar_firings(tmr)
        delay = (_seconds(re.search(r"^RandomizedDelaySec=(.+)$", tmr, re.M).group(1))
                 + _seconds(re.search(r"^AccuracySec=(.+)$", tmr, re.M).group(1)))
    except (ValueError, AttributeError) as exc:
        bad(f"the timer's calendar parses ({exc})")
        return
    outside = [(d, s // 60) for d, s in fires
               if not (window_open(d, s) and window_open(d, s + delay))]
    check(bool(fires) and not outside,
          f"all {len(fires)} firings a week, each plus its {delay}s delay, fall "
          f"inside the operating windows (outside: {outside[:5] or 'none'})")
    gaps = {d: sorted(s for dd, s in fires if dd == d) for d in range(1, 8)}
    steps = {b - a for d in gaps for a, b in zip(gaps[d], gaps[d][1:])
             if window_open(d, a) and all(window_open(d, x) for x in range(a, b, 60))}
    check(steps == {1800},
          f"inside a window the firings are every 30 minutes ({sorted(steps)} s)")
    check(len(gaps[1]) == 27 and len(gaps[6]) == 48 and len(gaps[7]) == 42,
          f"27 on a weekday, 48 on Saturday, 42 on Sunday "
          f"({len(gaps[1])}, {len(gaps[6])}, {len(gaps[7])})")
    check(re.search(r"^Persistent=false$", tmr, re.M) is not None,
          "Persistent=false: a missed tick is never caught up at boot, whenever "
          "boot is")

    bash = shutil.which("bash")
    if not bash:
        ok("no bash here; the behavioural half of I runs where bash exists")
        return
    # THE WRAPPER'S OWN GUARD, minute by minute against the same windows.
    fn = re.search(r"^in_window\(\) \{.*?^\}", wrapper, re.M | re.S)
    check(fn is not None, "the wrapper declares in_window()")
    if fn:
        # No subshell per minute: ten thousand forks take minutes under Git Bash.
        prog = (fn.group(0) + "\nfor d in {1..7}; do for h in {0..23}; do "
                "for m in {0..59}; do printf -v t '%02d%02d' $h $m; "
                "in_window $d $t && echo \"$d $t\"; done; done; done\n")
        r = subprocess.run([bash, "-c", prog], capture_output=True, text=True)
        got = set(r.stdout.split("\n")) - {""}
        want = {f"{d} {h:02d}{m:02d}" for d in range(1, 8) for h in range(24)
                for m in range(60) if window_open(d, (h * 60 + m) * 60)}
        check(got == want,
              f"the wrapper's ET guard opens on exactly CLAUDE.md's minutes "
              f"({len(got)} vs {len(want)}; differ: "
              f"{sorted(got ^ want)[:4] or 'none'})")

    git = shutil.which("git")
    if not git:
        ok("no git here; the end-to-end half of I runs where git exists")
        return
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        org = t / "origin"
        (org / "deploy" / "systemd").mkdir(parents=True)
        (org / "scripts").mkdir()
        for p in (SELF_DEPLOY, LEDGER, DEPLOY_REMOTE):
            (org / "scripts" / p.name).write_bytes(
                p.read_bytes().replace(b"\r\n", b"\n"))
        unit = org / "deploy" / "systemd" / "a.service"
        unit.write_text("[Unit]\nnew\n", encoding="utf-8", newline="\n")
        (org / "deploy" / "systemd" / "chester-eod.timer").write_text(
            "[Timer]\n", encoding="utf-8", newline="\n")
        hb = org / "scripts" / "check_heartbeat_cron.sh"
        hb.write_text("#!/usr/bin/env bash\n"
                      'echo "state=ok drift=clean" > "$CHESTER_STATE_DIR/heartbeat_check_status"\n'
                      "exit 0\n", encoding="utf-8", newline="\n")
        hb.chmod(0o755)
        g = {"cwd": str(org), "capture_output": True, "text": True}
        commit = [git, "-c", "user.email=t@t", "-c", "user.name=t",
                  "-c", "core.autocrlf=false", "commit", "-qm"]
        subprocess.run([git, "init", "-q"], **g)
        subprocess.run([git, "add", "-A"], **g)
        subprocess.run(commit + ["init"], **g)
        subprocess.run([git, "clone", "-q", str(org), str(t / "box")],
                       capture_output=True, text=True)
        for d in ("bin", "units", "state", "logs", "home"):
            (t / d).mkdir()
        installed = t / "units" / "a.service"
        installed.write_text("[Unit]\nold\n", encoding="utf-8")
        sysctl = t / "bin" / "systemctl"
        sysctl.write_text(
            "#!/usr/bin/env bash\n"
            'echo "$*" >> "$SYSLOG"\n'
            'case "$*" in\n'
            '  *is-active*) [[ -n "${FAKE_ACTIVE:-}" && "$*" == *"$FAKE_ACTIVE"* ]] ;;\n'
            '  *ActiveEnterTimestamp*) echo "${FAKE_ENTER:-}" ;;\n'
            "  *is-enabled*) exit 0 ;;\n"
            "  *) exit 0 ;;\n"
            "esac\n", encoding="utf-8", newline="\n")
        sysctl.chmod(0o755)
        slog = t / "sys.log"
        ledger_file = t / "state" / "alerts" / "restart_pending"
        last_tree = t / "state" / "self_deploy_last_tree"

        def run(clock: str, **extra) -> subprocess.CompletedProcess:
            env = {**os.environ, "HOME": str(t / "home"), "SYSLOG": str(slog),
                   "PATH": f"{t / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}",
                   "CHESTER_REPO": str(t / "box"), "CHESTER_LOG_DIR": str(t / "logs"),
                   "CHESTER_STATE_DIR": str(t / "state"),
                   "CHESTER_SYSTEMD_USER_DIR": str(t / "units"),
                   "CHESTER_DEPLOY_CLOCK": clock, **extra}
            return subprocess.run([bash, str(t / "box" / "scripts" / "run_self_deploy.sh")],
                                  capture_output=True, text=True, env=env)

        def calls() -> list[str]:
            return slog.read_text().splitlines() if slog.exists() else []

        r = run("1 1630", FAKE_ACTIVE="a.service")
        check(r.returncode == 0 and not calls() and not last_tree.exists()
              and "old" in installed.read_text(),
              f"16:30 on a Monday: exit {r.returncode}, no systemctl call, nothing "
              f"copied, nothing recorded -- the close's window is never touched")
        r = run("1 1005", FAKE_ACTIVE="a.service")
        line = ledger_file.read_text() if ledger_file.exists() else ""
        check(r.returncode == 0 and "new" in installed.read_text()
              and last_tree.exists()
              and re.match(r"restart pending: a\.service copied_at=\d+ ", line)
              is not None,
              f"10:05 with a changed RUNNING unit: copied, the tree recorded, and "
              f"'restart pending: a.service' written to alerts/restart_pending "
              f"(exit {r.returncode}; ledger {line.strip()[:60]!r})")
        n = len(calls())
        r = run("6 1205", FAKE_ACTIVE="a.service")
        check(r.returncode == 0 and not [c for c in calls()[n:] if "daemon-reload" in c]
              and ledger_file.exists(),
              "an unchanged deploy/systemd/ deploys nothing (no daemon-reload), and "
              "a unit still running the old file stays pending")
        unit.write_text("[Unit]\nnewer\n", encoding="utf-8", newline="\n")
        subprocess.run([git, "add", "-A"], **g)
        subprocess.run(commit + ["change"], **g)
        r = run("3 2105")
        check(r.returncode == 0 and "newer" in installed.read_text()
              and not ledger_file.exists(),
              f"a new commit is pulled and copied, and the line is pruned once the "
              f"unit is no longer running (exit {r.returncode})")
        bad_calls = [c for c in calls()
                     if re.search(r"\b(stop|disable|restart|kill|mask)\b", c)]
        check(not bad_calls,
              f"across every run systemctl never receives a destructive verb "
              f"({len(calls())} calls: {bad_calls or 'read/reload/enable only'})")


def main() -> int:
    print(f"{LINE}\nThe unattended deploy, and the permissions that allow it\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g,
              group_h, group_i):
        try:
            g()
        except FileNotFoundError as exc:
            bad(f"{g.__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
