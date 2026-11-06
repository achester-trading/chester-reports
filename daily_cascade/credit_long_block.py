"""
The Monthly's one slow-read line on the excess bond premium (item 124, Tranche 0,
step 5; D60, 6 Nov 2026; A126).

The Federal Reserve's excess bond premium and GZ spread (fed.ebp, fed.gz_spread,
altdata/sources/fed_ebp.py) are monthly, so the Monthly prints them, once, in its
slow layers after the Top & Bottom harness's credit lines
(config/stack_hooks/monthly-slow-credit-ebp.yaml). One line: the latest month's EBP
and GZ spread with the EBP's percentile over twenty years, its window through
derived.window_label. "not yet pulled" until the first pull lands. Report only:
nothing here enters the market-state object, a composite or an overlay, and the
line computes nothing the store does not hold.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

log = logging.getLogger(__name__)

TITLE = "Credit: the excess bond premium"
EBP, GZ = "fed.ebp", "fed.gz_spread"
WINDOW_DAYS = 7305                       # twenty years, the spread family's long window
NOT_PULLED = ("Excess bond premium (the Fed's FEDS Notes, fed.ebp): not yet pulled "
              "(the fed_ebp writer's one-time --backfill, on the box).")


def _ord(p: Any) -> str:
    from monthly_macro.stack import _ord as ordinal              # noqa: PLC0415
    return ordinal(p)


def ebp_line(st, now: str) -> str:
    from altdata import derived                                  # noqa: PLC0415
    e = derived.derived_forms(EBP, now, window=WINDOW_DAYS, store=st)
    if e.get("level") is None:
        return NOT_PULLED
    g = derived.derived_forms(GZ, now, window=WINDOW_DAYS, store=st)
    month = str(e["observed_at"])[:7]
    gz = ("GZ spread not held" if g.get("level") is None or g.get("observed_at") != e["observed_at"]
          else f"GZ spread {g['level']:.2f} pp")
    pct = (f"; {_ord(e['percentile'])} percentile of {e.get('window_label')} "
           f"(n={e['n']:,})" if e.get("percentile") is not None and (e.get("n") or 0) >= 2
           else "")
    return (f"Excess bond premium {e['level']:+.2f} pp for {month} (the Fed's FEDS "
            f"Notes, fed.ebp), {gz}{pct}. Report only.")


def slow_subsection(st, now: str) -> Optional[dict]:
    try:
        line = ebp_line(st, now)
    except Exception:                                           # noqa: BLE001
        log.warning("the excess bond premium line faulted", exc_info=True)
        return None
    return {"title": TITLE, "lines": [line], "paragraph_wanted": False,
            "table_note": ("Report-only (D60, 6 Nov 2026): the excess bond premium and "
                           "the GZ spread enter no composite, overlay or the "
                           "market-state object."),
            "data": {"ebp_line": line}}
