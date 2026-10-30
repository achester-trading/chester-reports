#!/usr/bin/env python3
"""
THE ONE GATE LIST, read from the gates' own declarations (S1 part 2; the
cloud-sessions brief, section 2.2, decision 2).

A gate declares itself in its own file, so no branch edits a shared list:

    GATE_KIND = "code"      a Python code gate: decides the build
    GATE_KIND = "data"      a Python data gate: reports, never decides
    # GATE_KIND: shell      a shell code gate (a comment line, run through bash)

    python tools/gate_list.py --kind code|data|shell

prints one path a line, sorted by path, so every caller sees the same order.
The Makefile builds PY_VALIDATORS, SH_VALIDATORS and DATA_GATES from it,
scripts/make.sh reads them the same way, and validate_audit_3a, validate_deploy
and validate_gates count from it. smoke_test.py is EXTRA, kept in the Makefile.

Read as text, never imported: importing a gate runs its module-level code, and
a list has no business doing that. Standard library only, because the Makefile
calls it before anything has said which interpreter has PyYAML.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KINDS = ("code", "data", "shell")
PY_DECL = re.compile(r"^GATE_KIND\s*=\s*[\"'](\w+)[\"']", re.M)
SH_DECL = re.compile(r"^#\s*GATE_KIND:\s*(\w+)\b", re.M)


def declared(p: Path) -> str | None:
    """The kind a file declares, or None for a file that is not a gate."""
    text = p.read_text(encoding="utf-8", errors="replace")
    m = (PY_DECL if p.suffix == ".py" else SH_DECL).search(text)
    return m.group(1) if m else None


def gates(kind: str, root: Path = REPO) -> list[str]:
    if kind not in KINDS:
        raise ValueError(f"unknown kind {kind!r}: one of {KINDS}")
    suffix = ".sh" if kind == "shell" else ".py"
    out = []
    for p in sorted((root / "tools").glob(f"*{suffix}")):
        k = declared(p)
        if k == kind:
            out.append(p.relative_to(root).as_posix())
    return out


def by_kind(root: Path = REPO) -> dict[str, list[str]]:
    return {k: gates(k, root) for k in KINDS}


def makefile_text(root: Path = REPO) -> str:
    """The Makefile as a gate reads it to ask "am I in the list": its text, and
    after it every declared gate, one a line. Before S1 the paths were in the
    Makefile itself; a gate that checks its own wiring reads this instead."""
    text = (root / "Makefile").read_text(encoding="utf-8")
    return (text + "\n# THE DECLARED GATES (tools/gate_list.py)\n"
            + "".join(f"{g}\n" for k in KINDS for g in gates(k, root)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="the gate list, by declared kind")
    ap.add_argument("--kind", required=True, choices=KINDS)
    ap.add_argument("--root", default=str(REPO))
    a = ap.parse_args(argv)
    for g in gates(a.kind, Path(a.root)):
        print(g)
    return 0


if __name__ == "__main__":
    sys.exit(main())
