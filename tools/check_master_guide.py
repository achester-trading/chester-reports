#!/usr/bin/env python3
"""
The Master Guide's gate (docs/master-guide.md; the specification of 19 Oct 2026,
section 6). It keeps the front door in step with what the code holds:

  1  TIMERS     every timer in deploy/systemd appears in Table 1, its OnCalendar
                cell matching the unit's OnCalendar (OnUnitActiveSec for one with
                none), and no row names a timer that does not exist -- except a
                row marked "ruled, not built", which is allowed until its unit
                file exists and must carry its schedule from then
  2  REPORTS    every report entry point has a card: the 07:00 anchor, the 12:30
                slot, the 16:45 close, the Weekly, the Monthly and the Quarterly;
                and a card ruled but not built (the 09:50 open note, the 21:30
                evening note) is required, without "ruled, not built", once its
                unit file exists
  3  CHAT       every task in docs/master-guide/chat-tasks.yaml appears in Table
                2 by name, with its status
  4  PAPERS     every paper in the library guide's roster appears in Table 9 by
                its numeral and file
  5  LEDGERS    every ledger in docs/ledgers/ appears in Table 7, with the verdict
                word its own table records (PASS, FAIL, INSUFFICIENT, NO GATE), or
                "diagnostic" for a file without a verdict row
  6  FIGURES    every figure the Guide links exists
  7  AS OF      a WARNING (never a failure) when the Guide's "As of" date is older
                than the newest change order filed in docs/
  8  GENERATED  figures 2 and 5 match what tools/figures/master_guide.py draws
                from today's timers, chat-tasks.yaml and roster

A machine-checked table sits between `<!-- table:NAME -->` and `<!-- /table -->`.
The gate reads files only: no store, no network, no model. `--root` points it at a
synthetic tree, which the gate's own
`--selftest` builds.

    python tools/check_master_guide.py [--root PATH] [--selftest]
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import argparse
import datetime as dt
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GUIDE = Path("docs/master-guide.md")
TASKS = Path("docs/master-guide/chat-tasks.yaml")
LIBRARY = Path("docs/white-paper-library-guide.md")
LEDGERS = Path("docs/ledgers")
UNITS = Path("deploy/systemd")
# The report entry points, each with the card heading it must have.
REPORT_CARDS = {
    "daily_cascade/morning_anchor.py": "The 07:00 anchor",
    "daily_cascade/midday_gate.py": "The 12:30 alert",
    "daily_cascade/close_report.py": "The 16:45 close",
    "daily_cascade/weekly_report.py": "The Weekly",
    "monthly_macro/run.py": "The Monthly",
    "monthly_macro/quarterly.py": "The Alternative Assets Quarterly",
}
# The reports ruled but not built (the secondary-notes order of 19 Oct 2026):
# timer -> the card heading they must have once the unit file exists.
PLANNED_CARDS = {
    "chester-open-note": "The 09:50 open note",
    "chester-evening-note": "The 21:30 evening note",
}
RULED = "ruled, not built"
VERDICTS = ("PASS", "FAIL", "INSUFFICIENT", "NO GATE")
MONTHS = {m: i for i, m in enumerate(
    "January February March April May June July August September October "
    "November December".split(), 1)}


def block(text: str, name: str) -> str:
    m = re.search(rf"<!-- table:{re.escape(name)} -->(.*?)<!-- /table -->", text, re.S)
    return m.group(1) if m else ""


def rows(tbl: str) -> list[list[str]]:
    out = []
    for ln in tbl.splitlines():
        ln = ln.strip()
        if not ln.startswith("|") or re.match(r"^\|\s*:?-{3,}", ln):
            continue
        out.append([c.strip() for c in ln.strip("|").split("|")])
    return out[1:] if out else []


def code_cells(cell: str) -> list[str]:
    return re.findall(r"`([^`]+)`", cell)


def timer_schedule(path: Path) -> str:
    keys = [ln.split("=", 1)[1].strip() for ln in path.read_text(encoding="utf-8").splitlines()
            if ln.startswith("OnCalendar=")]
    if not keys:
        keys = [ln.split("=", 1)[1].strip() for ln in path.read_text(encoding="utf-8").splitlines()
                if ln.startswith("OnUnitActiveSec=")]
        keys = [f"every {k}" for k in keys]
    return "; ".join(keys)


def verdict_of(path: Path) -> str:
    for ln in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| Verdict \| \**([A-Z][A-Z ]+)", ln)
        if m:
            w = m.group(1).strip()
            for v in VERDICTS:
                if w.startswith(v):
                    return v
    # a ledger written before the table form says it in words (the rates driver)
    if re.search(r"(?im)^#*\s*verdict:\s*the gate fails|^\**the gate fails", path.read_text(
            encoding="utf-8")):
        return "FAIL"
    return "diagnostic"


def as_of(text: str):
    m = re.search(r"\*\*As of:\*\* (\d{1,2}) ([A-Z][a-z]+) (\d{4})", text)
    return dt.date(int(m.group(3)), MONTHS[m.group(2)], int(m.group(1))) if m else None


def check(root: Path) -> tuple[list[str], list[str]]:
    import yaml
    fails: list[str] = []
    warns: list[str] = []
    gp = root / GUIDE
    if not gp.is_file():
        return [f"{GUIDE} does not exist"], warns
    text = gp.read_text(encoding="utf-8")

    # 1. timers
    t1 = {}
    for r in rows(block(text, "timers")):
        names = code_cells(r[0])
        if names:
            t1[names[0]] = code_cells(r[1])[0] if len(r) > 1 and code_cells(r[1]) else ""
    units = {p.stem: timer_schedule(p) for p in sorted((root / UNITS).glob("*.timer"))}
    for name, sched in units.items():
        if name not in t1:
            fails.append(f"[timers] {name}.timer is not in Table 1")
        elif t1[name] == RULED:
            fails.append(f"[timers] {name}.timer now exists: replace Table 1's "
                         f"'{RULED}' row with its schedule ({sched!r})")
        elif t1[name] != sched:
            fails.append(f"[timers] {name}: Table 1 says {t1[name]!r}, the unit says {sched!r}")
    for name in t1:
        if name not in units and t1[name] != RULED:
            fails.append(f"[timers] Table 1 names {name}, which has no timer in {UNITS}")

    # 2. report cards
    heads = re.findall(r"^### Card: (.+?)\s*$", text, re.M)
    # a card ruled but not built is not required until its unit file exists;
    # from then it is required, and may no longer say "ruled, not built"
    for timer, card in PLANNED_CARDS.items():
        if not (root / UNITS / f"{timer}.timer").exists():
            continue
        mine = [h for h in heads if h.startswith(card)]
        if not mine:
            fails.append(f"[reports] {timer}.timer exists, and there is no card for {card}")
        elif any(RULED in h for h in mine):
            fails.append(f"[reports] {timer}.timer exists: the card for {card} still says "
                         f"'{RULED}'")
    for entry, card in REPORT_CARDS.items():
        if not (root / entry).exists():
            continue
        if not any(h.startswith(card) for h in heads):
            fails.append(f"[reports] no card for {card} ({entry})")
        elif f"`{entry}`" not in text:
            fails.append(f"[reports] the card for {card} does not name its entry point {entry}")

    # 3. chat-side tasks
    t2 = {r[0].strip("*"): r for r in rows(block(text, "chat-tasks"))}
    tasks = (yaml.safe_load((root / TASKS).read_text(encoding="utf-8")) or {}).get("tasks") \
        if (root / TASKS).is_file() else None
    if tasks is None:
        fails.append(f"[chat] {TASKS} does not exist")
    for t in tasks or []:
        r = t2.get(t["name"])
        if r is None:
            fails.append(f"[chat] {t['name']!r} is not in Table 2")
        elif str(t.get("status")) not in " ".join(r):
            fails.append(f"[chat] {t['name']!r}: Table 2 does not print its status "
                         f"{t.get('status')!r}")
    for name in t2:
        if tasks is not None and name not in {t["name"] for t in tasks}:
            fails.append(f"[chat] Table 2 names {name!r}, which chat-tasks.yaml does not")

    # 4. papers
    t9 = block(text, "papers")
    lib = (root / LIBRARY).read_text(encoding="utf-8") if (root / LIBRARY).is_file() else ""
    roster = re.findall(r"^\|[^|]*\| \*\*([IVX]+)\*\*", lib, re.M)
    sys.path.insert(0, str(REPO / "tools"))
    import check_library                                        # noqa: PLC0415
    for num in roster:
        slug = check_library.REGISTRY.get(num)
        if f"| {num} |" not in t9 and f"| **{num}** |" not in t9:
            fails.append(f"[papers] {num} ({slug}) is not in Table 9")
        elif slug and f"{slug}-whitepaper.md" not in t9:
            fails.append(f"[papers] Table 9's row for {num} does not link {slug}-whitepaper.md")

    # 5. ledgers
    t7 = rows(block(text, "ledgers"))
    listed = {}
    for r in t7:
        for c in code_cells(r[0]):
            listed[c] = " ".join(r[1:])
    for p in sorted((root / LEDGERS).glob("*.md")):
        if p.name == "README.md":
            continue
        word = verdict_of(p)
        if p.name not in listed:
            fails.append(f"[ledgers] {p.name} is not in Table 7")
        elif word not in listed[p.name]:
            fails.append(f"[ledgers] {p.name}: Table 7 does not carry its verdict {word!r}")

    # 6. figures
    for f in re.findall(r"!\[[^\]]*\]\(([^)]+\.svg)\)", text):
        if not (gp.parent / f).resolve().is_file():
            fails.append(f"[figures] {f} does not exist")

    # 8. the generated figures are current (the repo's own tree only: the
    # generator reads the repo's timers, tasks and roster)
    if root.resolve() == REPO.resolve():
        sys.path.insert(0, str(REPO / "tools" / "figures"))
        import master_guide as figs                             # noqa: PLC0415
        for name, body in (("fig-02-clock.svg", figs.clock_svg()),
                           ("fig-05-library.svg", figs.library_svg())):
            p = figs.OUT / name
            if not p.is_file() or p.read_text(encoding="utf-8") != body + "\n":
                fails.append(f"[figures] {name} is stale: run tools/figures/master_guide.py")

    # 7. as of
    a = as_of(text)
    orders = sorted((root / "docs").glob("change-order-*.md"))
    newest = None
    for p in orders:
        m = re.search(r"(\d{4}-\d{2}-\d{2})", p.name)
        if m:
            d = dt.date.fromisoformat(m.group(1))
            newest = max(newest, d) if newest else d
    if a is None:
        fails.append("[as of] the Guide carries no '**As of:** D Month YYYY' line")
    elif newest and newest > a:
        warns.append(f"[as of] the Guide is as of {a}, older than the newest change order "
                     f"({newest}): refresh it at the next chain merge")
    return fails, warns


# ---------------------------------------------------------------------------
# The self-test: a synthetic tree that passes, then one plant per check
# ---------------------------------------------------------------------------
def _fixture(root: Path) -> None:
    (root / UNITS).mkdir(parents=True)
    (root / UNITS / "chester-x.timer").write_text("[Timer]\nOnCalendar=Mon-Fri 07:00 America/New_York\n",
                                                  encoding="utf-8")
    (root / UNITS / "dog.timer").write_text("[Timer]\nOnBootSec=2min\nOnUnitActiveSec=5min\n",
                                            encoding="utf-8")
    (root / "daily_cascade").mkdir()
    (root / "daily_cascade" / "morning_anchor.py").write_text("", encoding="utf-8")
    (root / TASKS.parent).mkdir(parents=True)
    (root / TASKS).write_text("tasks:\n  - {name: Task one, status: active}\n", encoding="utf-8")
    (root / LEDGERS).mkdir(parents=True)
    (root / LEDGERS / "sr-1-ledger-2026-10-18.md").write_text(
        "# x\n| | |\n|---|---|\n| Verdict | **PASS -- fine** |\n", encoding="utf-8")
    (root / LEDGERS / "notes.md").write_text("# a diagnostic\n", encoding="utf-8")
    (root / LIBRARY).write_text("| Layer | # | Paper |\n|---|---|---|\n| x | **XVIII** | the Doctrine |\n",
                                encoding="utf-8")
    (root / "docs" / "change-order-x-2026-10-12.md").write_text("", encoding="utf-8")
    (root / GUIDE).write_text("\n".join([
        "**As of:** 19 October 2026",
        "<!-- table:timers -->", "| Timer | OnCalendar |", "|---|---|",
        "| `chester-x` | `Mon-Fri 07:00 America/New_York` |", "| `dog` | `every 5min` |",
        "| `chester-open-note` | `ruled, not built` |",
        "<!-- /table -->",
        "### Card: The 07:00 anchor", "Entry: `daily_cascade/morning_anchor.py`.",
        "### Card: The 09:50 open note (ruled, not built)", "Entry point: none yet.",
        "<!-- table:chat-tasks -->", "| Task | Status |", "|---|---|", "| Task one | active |",
        "<!-- /table -->",
        "<!-- table:papers -->", "| # | Paper |", "|---|---|",
        "| XVIII | [the Doctrine](whitepapers/operating-doctrine-whitepaper.md) |",
        "<!-- /table -->",
        "<!-- table:ledgers -->", "| Ledger | Verdict |", "|---|---|",
        "| `sr-1-ledger-2026-10-18.md` | PASS |", "| `notes.md` | diagnostic |",
        "<!-- /table -->", ""]), encoding="utf-8")


def selftest() -> int:
    ok = 0
    bad = 0

    def expect(cond: bool, what: str) -> None:
        nonlocal ok, bad
        print(f"  {'PASS' if cond else 'FAIL'}  {what}")
        ok, bad = ok + bool(cond), bad + (not cond)

    with tempfile.TemporaryDirectory(prefix="check_master_guide_") as td:
        root = Path(td)
        _fixture(root)
        f, w = check(root)
        expect(f == [] and w == [], f"a synthetic tree in step passes ({f} {w})")
        g = root / GUIDE
        base = g.read_text(encoding="utf-8")
        plants = [
            ("`Mon-Fri 07:00 America/New_York`", "`Mon-Fri 07:05 America/New_York`",
             "[timers] chester-x: Table 1 says", "a timer whose schedule moved"),
            ("| `dog` | `every 5min` |\n", "", "[timers] dog.timer is not in Table 1",
             "a timer missing from Table 1"),
            ("### Card: The 07:00 anchor", "### Card: Something", "[reports] no card",
             "a report without a card"),
            ("| Task one | active |", "| Task one | retired |", "[chat] 'Task one': Table 2",
             "a chat task whose status changed"),
            ("| XVIII |", "| XIX |", "[papers] XVIII", "a paper missing from Table 9"),
            ("| `sr-1-ledger-2026-10-18.md` | PASS |", "| `sr-1-ledger-2026-10-18.md` | FAIL |",
             "[ledgers] sr-1-ledger", "a ledger whose verdict is misprinted"),
        ]
        for old, new, needle, what in plants:
            g.write_text(base.replace(old, new), encoding="utf-8")
            f, _ = check(root)
            expect(any(needle in x for x in f), f"the gate fails on {what}")
        g.write_text(base.replace("![", "![").replace("**As of:** 19 October 2026",
                                                       "**As of:** 1 October 2026"),
                     encoding="utf-8")
        f, w = check(root)
        expect(f == [] and any("[as of]" in x for x in w),
               "an as-of older than the newest change order warns and does not fail")
        g.write_text(base + "\n![Figure](figures/master-guide/none.svg)\n", encoding="utf-8")
        f, _ = check(root)
        expect(any("[figures]" in x for x in f), "a figure link that does not resolve fails")
        # ruled, not built: required once its unit file exists
        g.write_text(base, encoding="utf-8")
        unit = root / UNITS / "chester-open-note.timer"
        unit.write_text("[Timer]\nOnCalendar=Mon-Fri 09:50 America/New_York\n",
                        encoding="utf-8")
        f, _ = check(root)
        expect(any("chester-open-note.timer now exists" in x for x in f)
               and any("still says 'ruled, not built'" in x for x in f),
               "a timer and card marked 'ruled, not built' (allowed while no unit exists) "
               "become required once the unit file exists")
        g.write_text(base.replace("| `chester-open-note` | `ruled, not built` |",
                                  "| `chester-open-note` | `Mon-Fri 09:50 America/New_York` |")
                     .replace("### Card: The 09:50 open note (ruled, not built)",
                              "### Card: The 09:50 open note"), encoding="utf-8")
        f, _ = check(root)
        expect(f == [], f"and pass again once the row and the card are brought up to date ({f})")
        unit.unlink()
        g.write_text(base.replace("| `chester-open-note` | `ruled, not built` |",
                                  "| `chester-open-note` | `Mon-Fri 09:50 America/New_York` |"),
                     encoding="utf-8")
        f, _ = check(root)
        expect(any("Table 1 names chester-open-note" in x for x in f),
               "a row that claims a schedule for a timer with no unit still fails")
    print(f"\n{ok} passed, {bad} failed")
    return 0 if bad == 0 else 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="tools/check_master_guide.py")
    ap.add_argument("--root", default=str(REPO))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    print("SELF-TEST, on a synthetic tree")
    rc = selftest()
    if a.selftest:
        return rc
    print("\nTHE GUIDE, against the tree")
    fails, warns = check(Path(a.root))
    for x in warns:
        print(f"  WARN  {x}")
    for x in fails:
        print(f"  FAIL  {x}")
    print(f"\n{len(fails)} failure(s), {len(warns)} warning(s)")
    ok = rc == 0 and not fails
    print("VALIDATION PASSED" if ok else "VALIDATION FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
