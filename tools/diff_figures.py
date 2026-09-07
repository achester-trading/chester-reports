#!/usr/bin/env python3
"""Compare two directories of figures and say what actually changed.

WHY THIS EXISTS. `make figures` regenerates the Currencies charts, and the
question after it runs is never "are the bytes equal" -- they never are, since
every matplotlib release moves glyph metrics and every run stamps new element
ids. The question is whether the *chart* changed: different data, different
axes, different annotations. So this compares what a reader would see -- the
text labels drawn on the figure and the number of nodes in its plotted paths --
and reports the labels that differ.

That distinction has already mattered once. The committed Currencies figures
are an anchor reconstruction of ~180 path nodes per chart; a regenerated set
drawn from live daily FRED history has ~1,300, and USD/THB's thirty-year range
annotation moves from "25.3 to 55.8 (~75% of the midpoint)" to "22.75 to 56.1
(~85%)". Bytes would have told you they differ. This tells you why.

Exit status is 0 whether or not anything differs: this reports, it does not
gate.

Usage:
    python tools/diff_figures.py <committed-dir> <built-dir> [--labels N]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

TEXT = re.compile(r"<text\b[^>]*>.*?</text>", re.S)
TAGS = re.compile(r"<[^>]+>")
PATH_D = re.compile(r'\sd="([^"]+)"')


def labels(svg: str) -> list[str]:
    out = []
    for t in TEXT.findall(svg):
        s = re.sub(r"\s+", " ", TAGS.sub("", t)).strip()
        if s:
            out.append(s)
    return out


def nodes(svg: str) -> int:
    """Rough size of the plotted geometry: move/line commands across all paths."""
    return sum(d.count("M") + d.count("L") for d in PATH_D.findall(svg))


def compare(a: Path, b: Path, show: int):
    at, bt = labels(a.read_text(encoding="utf-8")), labels(b.read_text(encoding="utf-8"))
    an, bn = nodes(a.read_text(encoding="utf-8")), nodes(b.read_text(encoding="utf-8"))
    only_a = [t for t in at if t not in bt]
    only_b = [t for t in bt if t not in at]
    trivial = not only_a and not only_b and an == bn
    print("  %-14s %s  labels %d→%d  nodes %d→%d"
          % (a.name, "same chart" if trivial else "CHANGED", len(at), len(bt), an, bn))
    if trivial:
        return False
    for tag, items in (("only committed", only_a), ("only built    ", only_b)):
        if items:
            head = ", ".join(repr(t) for t in items[:show])
            more = "" if len(items) <= show else "  (+%d more)" % (len(items) - show)
            print("      %s: %s%s" % (tag, head, more))
    return True


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    show = 4
    if "--labels" in argv:
        i = argv.index("--labels")
        show = int(argv[i + 1])
        del argv[i:i + 2]
    if len(argv) != 2:
        print(__doc__.strip().split("Usage:")[-1].strip())
        return 2
    old, new = Path(argv[0]), Path(argv[1])
    files = sorted(new.glob("fig-*.svg"))
    if not files:
        print("no fig-*.svg in %s" % new)
        return 0
    print("comparing %s (committed) against %s (built):" % (old, new))
    changed = 0
    for f in files:
        prev = old / f.name
        if not prev.exists():
            print("  %-14s NEW (no committed counterpart)" % f.name)
            changed += 1
            continue
        changed += compare(prev, f, show)
    print("\n%d of %d figure(s) changed beyond ids and glyph metrics."
          % (changed, len(files)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
