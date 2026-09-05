"""
register -- the decision register, its packets, and the restrictions it enforces.

Architecture 26.2 #3 and #4, and Part 11's hard restriction. The one thing to
know before using it: `Register.record()` REFUSES restricted instruments by
raising, and a SQLite trigger refuses them again for anything that bypasses
this module. Neither is a filter and neither is a warning.
"""

from .store import (                    # noqa: F401
    DIRECTIONS, HORIZONS, OPERATOR_ACTIONS, STATUSES, THESIS_STATES,
    Register, RestrictedInstrumentError,
)
from .instruments import (              # noqa: F401
    Restrictions, normalise, restrictions,
)

__all__ = [
    "Register", "RestrictedInstrumentError", "Restrictions",
    "normalise", "restrictions",
    "DIRECTIONS", "HORIZONS", "STATUSES", "OPERATOR_ACTIONS", "THESIS_STATES",
]
