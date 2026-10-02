"""
The data gates' CI rule: skip explicitly, never fail and be ignored. (6d, 2 Oct 2026)

A data gate (GATE_KIND = "data") is about the box's real store. A CI runner has no
store, so until 2 Oct 2026 the five of them failed there on every push and the
workflow hid it with continue-on-error -- five red legs a reader learned to look
past, which is the habit that lets a real red leg go unread. Now each calls
`ci_skip()` first: under GitHub Actions it prints "skipped: box-only" with the
reason and exits 0. Everywhere else -- the box, the laptop -- it returns None and
the gate runs exactly as before, NOT VALIDATED included where there is no data.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def in_ci() -> bool:
    return os.environ.get("GITHUB_ACTIONS") == "true"


def ci_skip(gate_file: str) -> Optional[int]:
    """0 (after printing the skip) under GitHub Actions; None anywhere else."""
    if not in_ci():
        return None
    print(f"skipped: box-only -- {Path(gate_file).name} is a data gate: its verdict "
          f"is about the box's store, which a CI runner does not have. It runs on "
          f"the box in `make data-gates`.")
    return 0
