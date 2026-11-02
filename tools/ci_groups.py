"""ci_groups -- the Gates workflow's jobs, generated from config/ci_groups.yaml (B122).

The workflow ran one job per code gate (about 165 a run, B107). This tool groups the
fast gates into a few jobs and leaves the slow ones alone, so the runner start,
checkout and interpreter are paid once a group instead of once a gate. No gate
changes, none leaves CI, and each still reports by name.

The gate list always comes from the caller, one path per line on stdin -- in CI,
`make list-code` -- so this tool never holds a list of its own, and the Makefile
(or whatever `make list-code` reads) stays the one place the list lives.

  make list-code | python tools/ci_groups.py matrix [--docs]
        two JSON lines for $GITHUB_OUTPUT: alone=[gates...] and groups=[names...]
        (--docs: the docs-only push, B111 -- no lone gates, one group `docs`)
  make list-code | python tools/ci_groups.py --by-group
        each job and its gates, with counts: every gate appears exactly once
  make list-code | python tools/ci_groups.py run <group>
        runs the group's gates one at a time (python, or bash for .sh), prints a
        one-line verdict per gate with its name and tally, writes the same lines to
        $GITHUB_STEP_SUMMARY when set, and exits 1 if any gate failed
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "ci_groups.yaml"
DOCS_GROUP = "docs"
GATE_TIMEOUT_S = 600  # the per-gate job's old ten-minute allowance, per gate


def load(path: Path = CONFIG) -> dict:
    import yaml
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def read_gates(stream) -> list[str]:
    """The gate list as given: one path per line, .py or .sh, CR and blanks dropped."""
    out = []
    for line in stream:
        g = line.strip().replace("\r", "")
        if g.endswith((".py", ".sh")) and g not in out:
            out.append(g)
    return out


def assign(gates: list[str], cfg: dict) -> dict[str, list[str]]:
    """Each gate to exactly one job: its own (`alone`), else the first group whose
    pattern matches its file name, else the default group. Keys keep the config's
    order; a lone gate's key is its path."""
    alone = set(cfg.get("alone") or [])
    jobs: dict[str, list[str]] = {}
    for g in gates:
        if g in alone:
            jobs[g] = [g]
            continue
        name = g.split("/")[-1]
        for grp in cfg["groups"]:
            if any(fnmatch.fnmatch(name, p) for p in grp["match"]):
                jobs.setdefault(grp["name"], []).append(g)
                break
        else:
            jobs.setdefault(cfg["default"], []).append(g)
    return jobs


def lone_and_groups(gates: list[str], cfg: dict) -> tuple[list[str], list[str]]:
    jobs = assign(gates, cfg)
    alone = [k for k in jobs if k in set(cfg.get("alone") or [])]
    order = [g["name"] for g in cfg["groups"]] + [cfg["default"]]
    groups = [n for n in order if n in jobs]
    return alone, groups


def members(group: str, gates: list[str], cfg: dict) -> list[str]:
    if group == DOCS_GROUP:
        return [g for g in cfg["docs_set"] if g in gates]
    return assign(gates, cfg).get(group, [])


# The summary forms the gates print, most specific first.
_TALLIES = [re.compile(p) for p in (
    r".*\b\d+ passed, \d+ failed\b.*",
    r".*\bpapers checked\b.*",
    r".*\b(skipped|NOT VALIDATED)\b.*",
    r"^OK\b.*",
    r".*\bVALIDATION (PASSED|FAILED)\b.*",
    r".*\bALL .*PASSED\b.*",
)]


def tally(stdout: str) -> str:
    """The gate's own summary line, read from its stdout (stderr's warnings can
    follow it): the most specific summary form in its last 15 lines, else its last
    line."""
    lines = [l.strip() for l in stdout.splitlines() if l.strip() and not set(l.strip()) <= set("=-")]
    tail = lines[-15:]
    for rx in _TALLIES:
        for l in reversed(tail):
            if rx.fullmatch(l):
                return l[:120]
    return (lines[-1][:120] if lines else "(no output)")


def run_group(group: str, gates: list[str], cfg: dict) -> int:
    todo = members(group, gates, cfg)
    if not todo:
        print(f"group {group!r}: no gates -- refusing to pass an empty job", file=sys.stderr)
        return 2
    in_ci = bool(os.environ.get("GITHUB_ACTIONS"))
    rows, failed = [], 0
    for g in todo:
        cmd = ["bash", g] if g.endswith(".sh") else [sys.executable, g]
        t0 = time.monotonic()
        try:
            r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=GATE_TIMEOUT_S)
            code, so, out = r.returncode, r.stdout or "", (r.stdout or "") + (r.stderr or "")
        except subprocess.TimeoutExpired as e:
            so = e.stdout.decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
            code, out = 124, f"{so}\nTIMEOUT after {GATE_TIMEOUT_S} s"
            so = f"TIMEOUT after {GATE_TIMEOUT_S} s"
        secs = time.monotonic() - t0
        ok = code == 0
        failed += not ok
        # The gate's whole output, folded in the CI log, then its one-line verdict.
        print(f"::group::{g}" if in_ci else f"--- {g}")
        print(out.rstrip())
        print("::endgroup::" if in_ci else "---")
        t = tally(so)
        print(f"{'PASS' if ok else 'FAIL'}  {g}  ({t}; exit {code}; {secs:.0f} s)", flush=True)
        rows.append((ok, g, t, code, secs))
    print(f"\ngroup {group}: {len(todo) - failed} of {len(todo)} gates passed")
    for ok, g, t, code, secs in rows:
        print(f"  {'PASS' if ok else 'FAIL'}  {g}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(f"### Group `{group}`: {len(todo) - failed} of {len(todo)} passed\n\n")
            f.write("| Verdict | Gate | Tally | Seconds |\n|---|---|---|---|\n")
            for ok, g, t, code, secs in rows:
                t = t.replace("|", "\\|")
                f.write(f"| {'PASS' if ok else '**FAIL**'} | `{g}` | {t} | {secs:.0f} |\n")
            f.write("\n")
    return 1 if failed else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", nargs="?", choices=["matrix", "run"])
    ap.add_argument("group", nargs="?")
    ap.add_argument("--docs", action="store_true", help="the docs-only push's matrix")
    ap.add_argument("--by-group", action="store_true", help="list each job and its gates")
    a = ap.parse_args(argv)
    cfg = load()
    gates = read_gates(sys.stdin)
    if not gates:
        print("no gates on stdin (pipe `make list-code` in)", file=sys.stderr)
        return 2
    if a.by_group:
        jobs = assign(gates, cfg)
        alone, groups = lone_and_groups(gates, cfg)
        print(f"{len(gates)} gates in {len(alone) + len(groups)} jobs: "
              f"{len(alone)} alone, {len(groups)} groups")
        for k in alone:
            print(f"  alone  {k}")
        for n in groups:
            print(f"  group  {n} ({len(jobs[n])}): " + ", ".join(g.split('/')[-1] for g in jobs[n]))
        return 0
    if a.cmd == "matrix":
        if a.docs:
            alone, groups = [], [DOCS_GROUP]
        else:
            alone, groups = lone_and_groups(gates, cfg)
        print("alone=" + json.dumps(alone))
        print("groups=" + json.dumps(groups))
        return 0
    if a.cmd == "run" and a.group:
        return run_group(a.group, gates, cfg)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
