"""
The system's blocklist, applied at signal time (constitution: `blocklist`).

THE SYSTEM'S, NOT A COPY. The rule lives in register/instruments.py (the
normalisation to an issuer root, and the name patterns) over
config/tracked_entities.yaml, and the lab applies that same code. It does NOT
import the `register` package to get it: register/__init__.py imports the
register's store -- the decision writer -- and alpha/ may not import the
register (tools/validate_alpha_no_orders.py). So the one module, which needs
nothing but `re` and `yaml`, is loaded from its file under a private name. The
register's code is the rule; this is only the way the lab reaches it.

TWO NETS, as in the register: `check()` refuses a blocked instrument before any
write, and alpha.db's triggers refuse it again for anything that bypasses this
module (alpha/ledger.py mirrors the roots into `restricted_instruments`).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
SOURCE = REPO / "register" / "instruments.py"
_NAME = "alpha._system_blocklist"


class BlockedInstrument(ValueError):
    """A Brookfield-complex instrument reached the lab. It never reaches the
    ledger."""


def _module():
    mod = sys.modules.get(_NAME)
    if mod is None:
        spec = importlib.util.spec_from_file_location(_NAME, SOURCE)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[_NAME] = mod
        spec.loader.exec_module(mod)                            # type: ignore[union-attr]
    return mod


def normalise(instrument: Optional[str]) -> str:
    return _module().normalise(instrument)


def restrictions():
    return _module().restrictions()


def check(instrument: Optional[str]) -> Optional[dict]:
    """The matching restriction, or None when the instrument is clear."""
    return restrictions().check(instrument)


def refuse(instrument: Optional[str]) -> str:
    """The normalised root; raises BlockedInstrument when restricted."""
    hit = check(instrument)
    if hit is not None:
        raise BlockedInstrument(
            f"restricted instrument {instrument!r} ({hit.get('entity') or hit.get('entity_id')}): "
            f"the Brookfield complex never reaches the lab's ledger")
    return normalise(instrument)


def roots() -> list[str]:
    return restrictions().all_roots()
