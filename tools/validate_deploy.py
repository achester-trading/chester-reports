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
     reviewed is the whole risk of an allowlist, so a twelfth entry fails this
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
    m = re.search(r"^deploy:\n((?:\t.*\n|\n)*)", MAKEFILE.read_text(encoding="utf-8"),
                  re.M)
    return m.group(1) if m else ""


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
    recipe = deploy_recipe()
    check(bool(recipe), "the deploy: target was found in the Makefile")

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
    recipe = deploy_recipe()
    steps = [
        ("1. pull", r"1\. pull"),
        ("2. copy units", r"2\. copy units"),
        ("3. daemon-reload", r"3\. daemon-reload"),
        ("4. enable", r"4\. enable"),
        ("5. drift/heartbeat", r"5\. drift check and heartbeat"),
        ("6. roster", r"6\. timer roster"),
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
    m = re.search(r"^DEPLOY_TIMERS\s*:?=\s*((?:.*?\\\n)*.*)$", mk, re.M)
    check(m is not None, "DEPLOY_TIMERS is a declared list")
    timers = [t for t in (m.group(1).replace("\\\n", " ").split() if m else [])]
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


def group_c() -> None:
    print(f"\n{LINE}\nC. THE ALLOW LIST IS EXACTLY THE REVIEWED ONE\n{LINE}")
    check(SETTINGS.is_file(), f"{SETTINGS.relative_to(REPO)} exists")
    s = settings()
    perms = s.get("permissions") or {}
    allow = list(perms.get("allow") or [])
    check(allow == EXPECTED_ALLOW,
          f"the allow list is exactly the 11 reviewed entries "
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


def main() -> int:
    print(f"{LINE}\nThe unattended deploy, and the permissions that allow it\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f):
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
