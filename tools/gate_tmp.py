"""
A gate's temporary directory, removed when the gate exits. (PB-1, 5 Oct 2026)

    import gate_tmp
    td = gate_tmp.mkdtemp("validate_x_")

Every code gate seeds a temporary store of its own; with tempfile.mkdtemp those
directories outlived the run, and /tmp on the box filled with validate_*
directories. This returns the path of a tempfile.TemporaryDirectory that is kept
alive for the life of the process and cleaned up at exit -- the same path-string
interface mkdtemp had, so a gate changes one call and nothing else.
ignore_cleanup_errors: on Windows a SQLite file still open at exit cannot be
removed, and a failed cleanup must never turn a passing gate red.
"""

from __future__ import annotations

import atexit
import tempfile

_KEEP: list = []


def mkdtemp(prefix: str = "gate_") -> str:
    td = tempfile.TemporaryDirectory(prefix=prefix, ignore_cleanup_errors=True)
    _KEEP.append(td)
    return td.name


@atexit.register
def _cleanup() -> None:
    while _KEEP:
        _KEEP.pop().cleanup()
