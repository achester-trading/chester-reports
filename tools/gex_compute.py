"""
Compatibility shim -- this module is now tools/exposure_compute.py.

The file grew from gamma-only to four Greeks (GEX, DEX, VEX, CHEX) and the name
stopped describing it. Renaming a module that three callers import by name is a
gratuitous break, so the old name keeps working and forwards everything.

Nothing here has its own behaviour. `import gex_compute` and
`import exposure_compute` give the same functions, the same constants and the
same results; the only difference is which name appears in a traceback.

New code should import exposure_compute. This shim stays until the last caller
moves, and it is deleted rather than left to rot -- a shim nobody is waiting on
is just a second name for the same thing.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import exposure_compute as _exposure_compute      # noqa: E402
from exposure_compute import *                    # noqa: E402,F401,F403

# `import *` skips underscore-prefixed names, and _profile is used by callers
# that reach past the public surface. Re-exported explicitly so the shim is a
# complete substitute rather than a mostly-complete one.
from exposure_compute import (                    # noqa: E402,F401
    _d1_d2, _empty_greek_aggregates, _profile, _third_friday, _to_float,
)


def main() -> int:
    """Delegate, so `python tools/gex_compute.py` still runs the tool."""
    return _exposure_compute.main()


if __name__ == "__main__":
    sys.exit(main())
