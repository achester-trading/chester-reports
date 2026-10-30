#!/usr/bin/env python3
"""
The change-order index and the register's "Batch orders" cell, written by a
tool (S1 part 3; the cloud-sessions brief, section 2.2). Builders never edit
either: they file an order, and the stitcher runs

    python tools/change_orders_index.py --check     # the files agree with the tree
    python tools/change_orders_index.py --write     # regenerate them

THE INDEX (docs/change-orders.md) has one row per docs/change-order-*.md, oldest
first, the date read from the filename. A row already in the index keeps its
"What it rules" cell, which was written by hand and says more than a heading;
an order not yet indexed gets a row from its first heading. The text above the
table is kept as it stands.

THE CELL (docs/signal-triage-register.md, "| Batch orders |") lists every
signal-triage batch order. An entry already in the cell keeps its own words; a
batch order missing from it is appended, "[N](file) (its first heading)",
before the cell's closing sentence.

--write on a tree that is already complete changes nothing.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INDEX = Path("docs") / "change-orders.md"
REGISTER = Path("docs") / "signal-triage-register.md"
ORDER_RX = re.compile(r"^change-order-.*-(\d{4}-\d{2}-\d{2})\.md$")
BATCH_RX = re.compile(r"^change-order-signal-triage-batch-(\d+)-\d{4}-\d{2}-\d{2}\.md$")
ROW_RX = re.compile(r"^\| ([^|]+) \| \[([^\]]+)\]\(([^)]+)\) \| (.*) \|\s*$")
CELL_TAIL = ". Items 16 onward keep their numbers"


def _read(p: Path) -> tuple[str, bool]:
    raw = p.read_bytes()
    return raw.decode("utf-8").replace("\r\n", "\n"), b"\r\n" in raw


def _write(p: Path, text: str, crlf: bool) -> None:
    p.write_bytes((text.replace("\n", "\r\n") if crlf else text).encode("utf-8"))


def orders(root: Path) -> list[str]:
    return sorted(p.name for p in (root / "docs").glob("change-order-*.md")
                  if ORDER_RX.match(p.name))


def heading(root: Path, name: str) -> str:
    text, _ = _read(root / "docs" / name)
    first = next((ln for ln in text.split("\n") if ln.startswith("# ")), f"# {name}")
    # "# Change order — Signal triage Batch 16 (...)" -> "Signal triage Batch 16 (...)"
    return re.sub(r"^#\s*Change [Oo]rder\s*[—–-]+\s*", "", first).lstrip("# ").strip()


def _date(name: str) -> dt.date:
    return dt.date.fromisoformat(ORDER_RX.match(name).group(1))


def index_text(root: Path) -> str:
    text, _ = _read(root / INDEX)
    lines = text.split("\n")
    start = next(i for i, ln in enumerate(lines) if ln.startswith("| Date |"))
    end = start + 2
    while end < len(lines) and lines[end].startswith("|"):
        end += 1
    kept = {}
    order_seen = []
    for ln in lines[start + 2:end]:
        m = ROW_RX.match(ln)
        if m:
            kept[m.group(3)] = m.group(4)
            order_seen.append(m.group(3))
    names = orders(root)
    rank = {n: i for i, n in enumerate(order_seen)}
    names.sort(key=lambda n: (_date(n), rank.get(n, len(rank)), n))
    rows = []
    for n in names:
        d = _date(n)
        what = kept.get(n) or heading(root, n)
        rows.append(f"| {d.day} {d:%b} {d.year} | [{n}]({n}) | {what} |")
    return "\n".join(lines[:start + 2] + rows + lines[end:])


def register_text(root: Path) -> str:
    text, _ = _read(root / REGISTER)
    lines = text.split("\n")
    i = next(k for k, ln in enumerate(lines) if ln.startswith("| Batch orders |"))
    cell = lines[i]
    have = set(re.findall(r"\]\((change-order-signal-triage-batch-[^)]+\.md)\)", cell))
    missing = sorted((n for n in orders(root) if BATCH_RX.match(n) and n not in have),
                     key=lambda n: int(BATCH_RX.match(n).group(1)))
    if missing:
        add = "".join(f"; [{BATCH_RX.match(n).group(1)}]({n}) ({heading(root, n)})"
                      for n in missing)
        at = cell.find(CELL_TAIL)
        cell = (cell[:at] + add + cell[at:]) if at >= 0 else \
            cell.rstrip().rstrip("|").rstrip() + add + " |"
        lines[i] = cell
    return "\n".join(lines)


def run(root: Path, write: bool) -> list[str]:
    """The files that differ from what the tool would write (and, with
    `write`, are rewritten)."""
    out = []
    for rel, fn in ((INDEX, index_text), (REGISTER, register_text)):
        p = root / rel
        now, crlf = _read(p)
        new = fn(root)
        if new != now:
            out.append(rel.as_posix())
            if write:
                _write(p, new, crlf)
    return out


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="the change-order index (S1 part 3)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--write", action="store_true")
    ap.add_argument("--root", default=str(REPO))
    a = ap.parse_args(argv)
    diff = run(Path(a.root), a.write)
    if a.write:
        print(f"wrote {', '.join(diff) if diff else 'nothing'}")
        return 0
    print("index and register cell agree with the tree" if not diff
          else f"out of date: {', '.join(diff)} (run --write)")
    return 1 if diff else 0


if __name__ == "__main__":
    sys.exit(main())
