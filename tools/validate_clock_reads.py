"""
Validation gate: no new direct clock read outside altdata.session (A116).

The code under test reads the clock through `altdata.session` (`utc_now()` and
its helpers), so that a gate's pin, a replay and the as-of discipline hold. A
direct read -- `datetime.now()`, `datetime.utcnow()`, `datetime.today()`,
`date.today()`, `time.time()`, `time.time_ns()`, `pandas.Timestamp.now()` /
`.utcnow()` / `.today()`, `pandas.Timestamp("now")`, `pandas.to_datetime("now")`,
`numpy.datetime64("now")` -- anywhere in the scanned packages is a finding
unless `config/clock_reads_allowlist.yaml` lists it.

The scan is static and by AST, not regex: a string or a comment mentioning
"now" is no hit, and an alias (`import datetime as dt`, `from time import time`,
`import pandas as pd`) is resolved from the file's own imports. tools/ is not
scanned: the gates' pins are B106's and B110's business.

The allowlist names, per module, how many reads of each call it carries (B106's
inventory of 1 Nov 2026 as its seed; line numbers kept for reference only, since
lines drift). The gate:

  A  THE ALLOWLIST. Every entry names a scanned file, its calls and counts, and
     a burn-down note: what routing it through altdata.session would take.
  B  THE SCAN ON THIS TREE. A read not covered by the allowlist FAILS, printed
     as file:line and the call. An entry whose reads are gone is reported
     "burned down, remove from the allowlist" and does not fail; one with fewer
     reads than listed is "partly burned down".
  C  THE SCANNER ITSELF, on scratch sources: each listed call spelling is a
     hit, a string mentioning now is not, session.utc_now() is not, and the
     allowlist logic fails a new read and names a burned-down one.

    python tools/validate_clock_reads.py
"""

from __future__ import annotations

import ast
import sys
from collections import Counter
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
ALLOWLIST = REPO / "config" / "clock_reads_allowlist.yaml"

# What is scanned: the packages the paste names. weekly* and paper_exec/ are
# globbed, so a package of that name is scanned the day it exists.
SCAN_ROOTS = ("altdata", "daily_cascade", "monthly_macro", "alpha", "paper_exec",
              "scripts")
SCAN_GLOBS = ("weekly*",)
EXEMPT = {"altdata/session.py"}           # the one place the clock is read

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78

# Canonical names of a direct read. A call matches on its resolved dotted name;
# those in NEEDS_NOW_ARG match only with a first argument "now" or "today".
DIRECT = {
    "datetime.datetime.now", "datetime.datetime.utcnow", "datetime.datetime.today",
    "datetime.date.today",
    "time.time", "time.time_ns",
    "pandas.Timestamp.now", "pandas.Timestamp.utcnow", "pandas.Timestamp.today",
}
NEEDS_NOW_ARG = {"pandas.Timestamp", "pandas.to_datetime", "numpy.datetime64"}


def check(cond: bool, label: str) -> bool:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {label}")
    else:
        FAIL += 1
        print(f"  FAIL  {label}")
    return bool(cond)


def head(t: str) -> None:
    print(f"\n{t}")


# ---------------------------------------------------------------------------
# The scanner
# ---------------------------------------------------------------------------
def _aliases(tree: ast.AST) -> dict[str, str]:
    """Local name -> canonical dotted name, from every import in the file
    (function-local imports included: a read inside a function counts)."""
    m: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.asname:
                    m[a.asname] = a.name
                else:
                    m.setdefault(a.name.split(".")[0], a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            for a in node.names:
                m[a.asname or a.name] = f"{node.module}.{a.name}"
    return m


def _dotted(node: ast.AST) -> Optional[list[str]]:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return parts[::-1]
    return None


def _canonical(func: ast.AST, aliases: dict[str, str]) -> Optional[str]:
    parts = _dotted(func)
    if not parts:
        return None
    root = aliases.get(parts[0], parts[0])
    return ".".join([root] + parts[1:])


def hits_in_source(src: str, rel: str = "<scratch>") -> list[tuple[int, str]]:
    """[(line, canonical call)] for every direct clock read in one source."""
    tree = ast.parse(src, filename=rel)
    aliases = _aliases(tree)
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _canonical(node.func, aliases)
        if not name:
            continue
        if name in DIRECT:
            out.append((node.lineno, name))
        elif name in NEEDS_NOW_ARG and node.args:
            a0 = node.args[0]
            if (isinstance(a0, ast.Constant) and isinstance(a0.value, str)
                    and a0.value.strip().lower() in ("now", "today")):
                out.append((node.lineno, f'{name}("{a0.value.strip().lower()}")'))
    return sorted(out)


def scanned_files(repo: Path = REPO) -> list[Path]:
    files: list[Path] = []
    roots = [repo / r for r in SCAN_ROOTS]
    for g in SCAN_GLOBS:
        roots += [p for p in repo.glob(g)]
    for r in roots:
        if r.is_file() and r.suffix == ".py":
            files.append(r)
        elif r.is_dir():
            files += sorted(r.rglob("*.py"))
    return [f for f in files
            if f.relative_to(repo).as_posix() not in EXEMPT
            and "__pycache__" not in f.parts]


def scan(repo: Path = REPO) -> dict[str, list[tuple[int, str]]]:
    out = {}
    for f in scanned_files(repo):
        rel = f.relative_to(repo).as_posix()
        h = hits_in_source(f.read_text(encoding="utf-8"), rel)
        if h:
            out[rel] = h
    return out


def load_allowlist(path: Path = ALLOWLIST) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def compare(hits: dict[str, list[tuple[int, str]]], allow: dict) -> dict:
    """The scan against the allowlist: new reads (fail), burned-down entries and
    partly burned-down ones (reported, never fail)."""
    mods = allow.get("modules") or {}
    new, burned, partly, moved = [], [], [], []
    for rel, hs in sorted(hits.items()):
        have = Counter(c for _l, c in hs)
        listed = Counter((mods.get(rel) or {}).get("calls") or {})
        for call, n in have.items():
            if n > listed.get(call, 0):
                extra = n - listed.get(call, 0)
                lines = [ln for ln, c in hs if c == call]
                new.append({"file": rel, "call": call, "lines": lines, "extra": extra,
                            "listed": listed.get(call, 0)})
    for rel, ent in sorted(mods.items()):
        have = Counter(c for _l, c in hits.get(rel, []))
        calls = (ent or {}).get("calls") or {}
        if not any(have.get(c) for c in calls):
            burned.append(rel)
            continue
        for call, n in calls.items():
            if have.get(call, 0) < int(n):
                partly.append({"file": rel, "call": call, "listed": int(n),
                               "found": have.get(call, 0)})
        lines_now = sorted(ln for ln, _c in hits.get(rel, []))
        if ent.get("lines_b106") and lines_now != sorted(ent["lines_b106"]):
            moved.append({"file": rel, "b106": ent["lines_b106"], "now": lines_now})
    return {"new": new, "burned": burned, "partly": partly, "moved": moved}


def report(cmp: dict) -> list[str]:
    out = []
    for n in cmp["new"]:
        out.append(f"  NEW READ  {n['file']}:{','.join(map(str, n['lines']))}  {n['call']}"
                   f"  ({n['listed']} allowlisted, {n['listed'] + n['extra']} found)")
    for b in cmp["burned"]:
        out.append(f"  burned down, remove from the allowlist: {b}")
    for p in cmp["partly"]:
        out.append(f"  partly burned down: {p['file']} {p['call']} "
                   f"({p['found']} of {p['listed']} remain)")
    return out


# ---------------------------------------------------------------------------
# The groups
# ---------------------------------------------------------------------------
def group_a(allow: dict) -> None:
    head("A. THE ALLOWLIST")
    mods = allow.get("modules") or {}
    in_scope = {f.relative_to(REPO).as_posix() for f in scanned_files()}
    check(bool(mods) and all(rel in in_scope for rel in mods),
          f"every entry names a scanned file ({len(mods)} modules)")
    check(all((e or {}).get("calls") and all(int(v) > 0 for v in e["calls"].values())
              and len(str(e.get("burn_down") or "")) > 20 for e in mods.values()),
          "each carries its calls with counts and a burn-down note")
    b106 = [r for r, e in mods.items() if e.get("source") == "B106"]
    a116 = [r for r, e in mods.items() if e.get("source") == "A116 scan"]
    check(len(b106) + len(a116) == len(mods),
          f"each says where it came from: B106's inventory ({len(b106)}) or "
          f"this gate's first scan ({len(a116)})")
    out = allow.get("b106_outside_scope") or {}
    check(all(not str(r).startswith(SCAN_ROOTS) for r in out),
          f"B106's modules outside the scanned packages are listed apart, never "
          f"scanned ({sorted(out)})")


def group_b(allow: dict) -> None:
    head("B. THE SCAN ON THIS TREE")
    hits = scan()
    total = sum(len(v) for v in hits.values())
    listed = sum(int(n) for e in (allow.get("modules") or {}).values()
                 for n in (e.get("calls") or {}).values())
    cmp = compare(hits, allow)
    for line in report(cmp):
        print(line)
    print(f"  ({total} direct reads in {len(hits)} files; the allowlist carries "
          f"{listed} in {len(allow.get('modules') or {})} files)")
    if cmp["moved"]:
        print(f"  ({len(cmp['moved'])} allowlisted modules' lines moved since B106's "
              f"inventory, counts unchanged: "
              f"{', '.join(m['file'] for m in cmp['moved'][:6])}"
              f"{' ...' if len(cmp['moved']) > 6 else ''})")
    check(not cmp["new"], f"no direct clock read outside the allowlist "
          f"({len(cmp['new'])} new)")


def group_c(allow: dict) -> None:
    head("C. THE SCANNER ITSELF")
    src = '''
import datetime as dt
import time as _t
from datetime import datetime, date
from time import time
import pandas as pd
import numpy as np
from altdata import session

a = dt.datetime.now(dt.timezone.utc)
b = datetime.utcnow()
c = date.today()
d = _t.time()
e = time()
f = pd.Timestamp.now()
g = pd.Timestamp("now")
h = np.datetime64("now")
i = pd.to_datetime("today")
s = "datetime.now() in a string is not a read"
# datetime.now() in a comment is not a read
j = session.utc_now()
k = dt.datetime.fromisoformat("2026-11-02")
l = pd.Timestamp("2026-11-02")
'''
    h = hits_in_source(src)
    want = [(10, "datetime.datetime.now"), (11, "datetime.datetime.utcnow"),
            (12, "datetime.date.today"), (13, "time.time"), (14, "time.time"),
            (15, "pandas.Timestamp.now"), (16, 'pandas.Timestamp("now")'),
            (17, 'numpy.datetime64("now")'), (18, 'pandas.to_datetime("today")')]
    check(h == want, f"each spelling of a direct read is a hit, aliases resolved; "
          f"strings, comments, session.utc_now() and a dated parse are not ({h})")
    hits = {"altdata/x.py": [(3, "datetime.datetime.now"), (9, "time.time")]}
    al = {"modules": {"altdata/x.py": {"calls": {"datetime.datetime.now": 1}},
                      "altdata/y.py": {"calls": {"time.time": 1}}}}
    cmp = compare(hits, al)
    rep = report(cmp)
    check([n["file"] + ":" + str(n["lines"]) for n in cmp["new"]] == ["altdata/x.py:[9]"]
          and any("NEW READ  altdata/x.py:9  time.time" in r for r in rep),
          f"a read not in the allowlist fails, printed with its line ({rep[:1]})")
    check(cmp["burned"] == ["altdata/y.py"]
          and "  burned down, remove from the allowlist: altdata/y.py" in rep,
          "an entry whose reads are gone says 'burned down, remove from the allowlist'")
    cmp2 = compare({"altdata/x.py": [(3, "datetime.datetime.now")]},
                   {"modules": {"altdata/x.py": {"calls": {"datetime.datetime.now": 2}}}})
    check(not cmp2["new"] and cmp2["partly"] and not cmp2["burned"],
          "fewer reads than listed is 'partly burned down', not a failure")


def main() -> int:
    print(LINE)
    print("validate_clock_reads -- no new direct clock read outside altdata.session")
    print(LINE)
    allow = load_allowlist()
    group_a(allow)
    group_b(allow)
    group_c(allow)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
