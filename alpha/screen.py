"""
The lab's own move screen over the price basket -- one session's move per
stored symbol, as a z-score against that symbol's own trailing one-day moves
(up to five years), and the prints at or beyond 2.5 sigma.

altdata.move_screen (the store-wide screen, audit #4 item 1) is not built yet;
when it is, the agenda and the proposer's packet read its prints instead and
this stays as their fallback. Read-only, point-in-time: every value is the
latest vintage knowable at `as_of`.
"""

from __future__ import annotations

import statistics
from typing import Optional

from altdata import observations, session

from . import rules

SIGMA = 2.5
Z_WINDOW = 1260
MIN_HISTORY = 60


def moves(store, as_of: str, day: Optional[str] = None,
          data: Optional[rules.Data] = None) -> list[dict]:
    """Each stored symbol's move on `day` (default: as_of's session)."""
    t = observations.canonical_instant(as_of)
    day = day or session.session_date(as_of)
    data = data or rules.Data(store)
    out = []
    for sym, key in sorted(rules.price_symbols().items()):
        if not store.all_vintages(key):
            continue
        xs = data.series(key).known(day, t, Z_WINDOW + 1)
        if len(xs) < MIN_HISTORY + 1 or xs[-1][0] != day:
            continue
        r = [xs[i][1] / xs[i - 1][1] - 1 for i in range(1, len(xs)) if xs[i - 1][1]]
        hist, last = r[:-1], r[-1]
        sd = statistics.stdev(hist) if len(hist) > 2 else 0.0
        out.append({"symbol": sym, "day": day, "close": round(xs[-1][1], 4),
                    "change_pct": round(last * 100, 3),
                    "z": round((last - statistics.fmean(hist)) / sd, 2) if sd else None,
                    "history_days": len(hist)})
    return out


def prints(rows: list[dict], sigma: float = SIGMA) -> list[dict]:
    return [m for m in rows if m["z"] is not None and abs(m["z"]) >= sigma]
