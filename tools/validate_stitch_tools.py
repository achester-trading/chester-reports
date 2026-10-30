#!/usr/bin/env python3
"""
Validation gate: the stitch's tools (S1 part 7). Fixtures only; no network, no
model, no live store. Each tool is run on a fixture tree with a known drift:
--check fails, --write repairs it, --check passes.

  A  stitch_counts.py. CLAUDE.md, the architecture document and the registry,
     copied and planted with a stale count each: a count in words, a numeral in
     the store box and a block's expected_members. --write sets each to the
     code's in the sentence's own form (words stay words, numerals numerals,
     the registry line's comment kept); a sentence that is gone is a fault
     --write cannot repair.
  B  change_orders_index.py. An index missing an order and a register cell
     missing a batch: --write adds the row from the order's first heading in
     date order, keeps a hand-written summary, and appends the batch.
  C  appendix_queue_index.py. Entry files under two slugs and a stale index:
     --write regenerates it as the generated-by line, the preface and the
     entries in (date, id) order, byte for byte.

    python tools/validate_stitch_tools.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

import appendix_queue_index as aqi                              # noqa: E402
import change_orders_index as coi                               # noqa: E402
import stitch_counts as sc                                      # noqa: E402

TD = Path(gate_mkdtemp("stitch_tools_"))
LINE = "=" * 78
PASS = FAIL = 0


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def drift(rows) -> list:
    return [r for r in rows if r["action"].startswith(("->", "FAULT"))]


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. stitch_counts: A PLANTED COUNT IS CAUGHT, REWRITTEN IN ITS FORM")
    root = TD / "counts"
    (root / "docs").mkdir(parents=True)
    for rel in ("CLAUDE.md", "metrics_registry.yaml", sc.ARCH.as_posix()):
        shutil.copy(REPO / rel, root / rel)
    counts = sc.A3.code_counts()
    rows, _ = sc.run(root, write=False, counts=counts)
    check(not drift(rows), "the copied tree agrees with the code before any plant")
    cl = root / "CLAUDE.md"
    text = cl.read_text(encoding="utf-8")
    m = re.search(r"runs every gate\*\* — (\S+(?: \S+)*?) code gates", text)
    printed = m.group(1)
    wrong = sc.words(counts["code_gates"] - 3)
    cl.write_text(text.replace(f"— {printed} code gates", f"— {wrong} code gates", 1),
                  encoding="utf-8")
    arch = root / sc.ARCH
    at = arch.read_text(encoding="utf-8")
    at2 = re.sub(r"(pull walks )\d+( FRED series)", r"\g<1>7\g<2>", at, count=1)
    arch.write_text(at2, encoding="utf-8")
    reg = root / "metrics_registry.yaml"
    rt = reg.read_text(encoding="utf-8")
    m2 = re.search(r"^(    expected_members: )(\d+)(.*)$", rt, re.M)
    rt2 = rt[:m2.start(2)] + "3" + rt[m2.end(2):]
    reg.write_text(rt2, encoding="utf-8")
    check(at2 != at and rt2 != rt, "three counts planted: words, a numeral, a registry")
    rows, _ = sc.run(root, write=False, counts=counts)
    bad = {r["what"] for r in drift(rows)}
    check({"code gates", "arch: FRED pull"} <= bad and len(bad) == 3,
          f"--check finds the three ({sorted(bad)})")
    rows, written = sc.run(root, write=True, counts=counts)
    check(sorted(written) == sorted(["CLAUDE.md", sc.ARCH.as_posix(),
                                     "metrics_registry.yaml"]),
          f"--write rewrites the three files ({written})")
    new = cl.read_text(encoding="utf-8")
    check(f"— {printed} code gates" in new and not re.search(
        r"— \d+ code gates", new), f"a count in words is written back in words ({printed})")
    check(re.search(rf"pull walks {counts['fred_pull']} FRED series",
                    arch.read_text(encoding="utf-8")) is not None,
          "a numeral is written back as a numeral")
    check(reg.read_text(encoding="utf-8") == rt,
          "the registry's expected_members is restored, its comment kept")
    rows, _ = sc.run(root, write=False, counts=counts)
    check(not drift(rows), "and --check passes after it")
    cl.write_text(new.replace("market symbols", "symbols in the basket"),
                  encoding="utf-8")
    rows, _ = sc.run(root, write=True, counts=counts)
    check(any(r["action"].startswith("FAULT: the sentence is gone") for r in rows),
          "a reworded sentence is a fault --write reports and cannot repair")
    check(sc.words(140) == "one hundred and forty" and sc.words(88) == "eighty-eight"
          and all(sc.A3.number(sc.words(n)) == n for n in range(0, 200)),
          "the words read back to the same number (0 to 199)")


# ---------------------------------------------------------------------------
def group_b() -> None:
    head("B. change_orders_index: A MISSING ORDER AND BATCH ARE ADDED")
    root = TD / "orders"
    d = root / "docs"
    d.mkdir(parents=True)
    (d / "change-order-signal-triage-batch-3-2026-10-02.md").write_text(
        "# Change order — Signal triage Batch 3\n", encoding="utf-8")
    (d / "change-order-signal-triage-batch-4-2026-10-06.md").write_text(
        "# Change Order — Signal Triage Batch 4\n", encoding="utf-8")
    (d / "change-order-alpha-2026-10-04.md").write_text(
        "# Change order — The fixture lab\n", encoding="utf-8")
    (d / "change-orders.md").write_text(
        "# Change orders\n\nThe index.\n\n| Date | Order | What it rules |\n"
        "|---|---|---|\n"
        "| 2 Oct 2026 | [change-order-signal-triage-batch-3-2026-10-02.md]"
        "(change-order-signal-triage-batch-3-2026-10-02.md) | Batch 3, by hand |\n"
        "| 6 Oct 2026 | [change-order-signal-triage-batch-4-2026-10-06.md]"
        "(change-order-signal-triage-batch-4-2026-10-06.md) | Batch 4, by hand |\n"
        "\nAfter the table.\n", encoding="utf-8")
    (d / "signal-triage-register.md").write_text(
        "# Register\n\n| | |\n|---|---|\n| Batch orders | [Batch 3]"
        "(change-order-signal-triage-batch-3-2026-10-02.md). Items 16 onward keep "
        "their numbers as IDs |\n", encoding="utf-8")
    check(sorted(coi.run(root, write=False)) == ["docs/change-orders.md",
                                                 "docs/signal-triage-register.md"],
          "--check finds the index and the cell out of date")
    coi.run(root, write=True)
    idx = (d / "change-orders.md").read_text(encoding="utf-8")
    lines = [ln for ln in idx.split("\n") if ln.startswith("| ") and "[" in ln]
    check([re.search(r"\[([^\]]+)\]", ln).group(1) for ln in lines] == [
        "change-order-signal-triage-batch-3-2026-10-02.md",
        "change-order-alpha-2026-10-04.md",
        "change-order-signal-triage-batch-4-2026-10-06.md"],
          "the missing order is added in date order")
    check("| 4 Oct 2026 |" in idx and "| The fixture lab |" in idx
          and "| Batch 3, by hand |" in idx and "After the table." in idx,
          "its row comes from its first heading; hand-written rows and the text "
          "around the table are kept")
    cell = next(ln for ln in (d / "signal-triage-register.md").read_text(
        encoding="utf-8").split("\n") if ln.startswith("| Batch orders"))
    check("[4](change-order-signal-triage-batch-4-2026-10-06.md) (Signal Triage "
          "Batch 4). Items 16 onward" in cell and cell.startswith(
              "| Batch orders | [Batch 3]"),
          "the missing batch is appended to the cell before its closing sentence")
    check(coi.run(root, write=False) == [], "and --check passes after it")
    # D42.10 (29 Oct 2026): a filed record whose name carries a suffix after its
    # date (A70's "...-2026-09-13-record.md") is an order the index keeps, never
    # dropped by --write; a name with no date stays outside the pattern.
    (d / "change-order-amendment-3-2026-09-13-record.md").write_text(
        "# Change order — Amendment 3, record only\n", encoding="utf-8")
    (d / "change-order-notes-undated.md").write_text("# Not an order\n",
                                                     encoding="utf-8")
    check("change-order-amendment-3-2026-09-13-record.md" in coi.orders(root)
          and "change-order-notes-undated.md" not in coi.orders(root),
          "a dated record with a suffix is an order; an undated name is not")
    coi.run(root, write=True)
    idx = (d / "change-orders.md").read_text(encoding="utf-8")
    names = [re.search(r"\[([^\]]+)\]", ln).group(1)
             for ln in idx.split("\n") if ln.startswith("| ") and "[" in ln]
    check(names[0] == "change-order-amendment-3-2026-09-13-record.md"
          and "| 13 Sep 2026 |" in idx and coi.run(root, write=False) == [],
          "--write indexes it in date order (13 Sep first) and --check passes")


# ---------------------------------------------------------------------------
def group_c() -> None:
    head("C. appendix_queue_index: THE INDEX IS THE ENTRIES, BYTE FOR BYTE")
    root = TD / "queue"
    q = root / "docs" / "dated-appendix-queue"
    (q / "paper-b").mkdir(parents=True)
    (q / "paper-a").mkdir()
    (q / "_preface.md").write_text("# Queue\n\nPreface.\n\n", encoding="utf-8")
    (q / "paper-b" / "2026-10-09-01-first.md").write_text("## First\n\nOne.\n\n",
                                                          encoding="utf-8")
    (q / "paper-a" / "2026-10-20-01-third.md").write_text("## Third\n\nThree.\n",
                                                          encoding="utf-8")
    (q / "paper-a" / "2026-10-09-02-second.md").write_text("## Second\n\nTwo.\n\n",
                                                           encoding="utf-8")
    (root / aqi.INDEX).write_text("# Queue\n\nstale\n", encoding="utf-8")
    check(aqi.run(root, write=False), "--check finds the index stale")
    aqi.run(root, write=True)
    got = (root / aqi.INDEX).read_text(encoding="utf-8")
    want = (aqi.GENERATED + "# Queue\n\nPreface.\n\n## First\n\nOne.\n\n"
            "## Second\n\nTwo.\n\n## Third\n\nThree.\n")
    check(got == want, "--write: the generated-by line, the preface, the entries "
          "in (date, id) order across slugs, byte for byte")
    check(not aqi.run(root, write=False), "and --check passes after it")
    (q / "paper-a" / "notes.md").write_text("x", encoding="utf-8")
    try:
        aqi.entries(root)
        named = False
    except ValueError:
        named = True
    check(named, "an entry file not named <date>-<id>.md is refused")


def main() -> int:
    try:
        group_a()
        group_b()
        group_c()
    finally:
        shutil.rmtree(TD, ignore_errors=True)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
