"""
A long gate's groups: --group, --list-groups and a timing line per group.
(B97, 31 Oct 2026)

    GATE_GROUPS = "A B C D"          # in the gate, read as text by gate_list.py
    import gate_groups
    G = gate_groups.Groups(GATE_GROUPS)
    ...
    print(f"\\n{LINE}\\nA. THE STACK\\n{LINE}")
    G.mark("A")
    if G.on("A"):
        ...the group's checks...

    python tools/validate_x.py                  every group, as before
    python tools/validate_x.py --group C        group C only (repeatable; or C,E)
    python tools/validate_x.py --list-groups    the names, one a line

With no flag every group runs, in the order it always ran, so a whole run's
checks and tally are what they were; the timing line is the only new output.
A selected group runs its own setup, and setup that every group needs runs
once whatever is selected. The tally lines ("N passed, M failed",
"VALIDATION PASSED") and the exit code keep their form, so CI and the counting
tools read a group's run the same way. A timing line starts "  time ", never
"  PASS" or "  FAIL", so nothing that counts checks counts it.

`scripts/make.sh validate-group <gate> <group>` is the laptop's spelling.
"""

from __future__ import annotations

import sys
import time


class Groups:
    def __init__(self, names: str, argv: list[str] | None = None):
        self.names = names.split()
        self._upper = {n.upper(): n for n in self.names}
        self.t0 = time.monotonic()
        self.last: tuple[str, float] | None = None
        args = list(sys.argv[1:] if argv is None else argv)
        if "--list-groups" in args:
            print("\n".join(self.names))
            sys.exit(0)
        picked: list[str] = []
        while "--group" in args:
            i = args.index("--group")
            if i + 1 >= len(args):
                sys.exit("--group needs a name: " + " ".join(self.names))
            picked += [x for x in args[i + 1].split(",") if x]
            del args[i:i + 2]
        bad = [x for x in picked if x.upper() not in self._upper]
        if bad:
            sys.exit(f"unknown group(s) {bad}: one of {' '.join(self.names)}")
        self.selected = {self._upper[x.upper()] for x in picked} or None
        if self.selected:
            print(f"  time  running group(s) {', '.join(n for n in self.names if n in self.selected)}"
                  f" of {' '.join(self.names)}")

    def on(self, *names: str) -> bool:
        """True when any of these groups runs (always, with no --group)."""
        return self.selected is None or any(n in self.selected for n in names)

    def mark(self, name: str) -> None:
        """The timing line under a group's header: when it began, and how long
        the group before it took. A header inside a group is marked
        "<group>: <header>" and belongs to that group."""
        now = time.monotonic() - self.t0
        prev = (f"; {self.last[0]} took {now - self.last[1]:.1f} s"
                if self.last else "")
        state = "" if self.on(name.split(":")[0]) else ", not selected"
        print(f"  time  {name} at {now:.1f} s{prev}{state}")
        self.last = (name, now)

    def done(self) -> None:
        """The last timing line, before the tally."""
        now = time.monotonic() - self.t0
        prev = (f"; {self.last[0]} took {now - self.last[1]:.1f} s"
                if self.last else "")
        print(f"  time  total {now:.1f} s{prev}")
