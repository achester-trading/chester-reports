"""
The Weekly's lab line (X-1.11) -- the one line a report prints from the lab.

    Alpha Lab: +x.x% since <date> · n engines live · drawdown y% · loop events this week k

and "Alpha Lab: not yet live" until the first engine passes into paper (status
live or halved). Read from alpha.db READ-ONLY (`mode=ro`): a missing ledger is
"not yet live", never an error, and nothing here creates the file. The Weekly
calls weekly_line() once, from its one hook in daily_cascade/weekly_stack.py.

  +x.x% since <date>   the lab's equity against its notional, since the first
                       day an engine held an applied allocation
  n engines live       live or halved (a halved engine still trades)
  drawdown y%          the lab's, from its high-water mark (0.0% at the mark)
  loop events this week k   rows in loop_events written in the seven days to
                       the cutoff -- the loop's activity, not its success
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Optional

from . import config as acfg

NOT_LIVE = "Alpha Lab: not yet live"


def weekly_line(cutoff: str, path: Optional[str | Path] = None) -> str:
    """Never raises: the lab's failure never touches a report."""
    try:
        return _line(cutoff, path)
    except Exception as exc:                                  # noqa: BLE001
        return f"Alpha Lab: unavailable ({type(exc).__name__})"


def _line(cutoff: str, path: Optional[str | Path] = None) -> str:
    p = Path(path or acfg.ledger_path())
    if not p.is_file():
        return NOT_LIVE
    from .ledger import LAB, Ledger                             # noqa: PLC0415
    try:
        lg = Ledger(p, read_only=True)
    except Exception:                                         # noqa: BLE001
        return NOT_LIVE
    try:
        live = lg.q("SELECT id FROM engines WHERE status IN ('live','halved')")
        if not live:
            return NOT_LIVE
        day = cutoff[:10]
        eq = lg.one("SELECT equity, hwm, drawdown FROM equity WHERE engine_id=? AND "
                    "day<=? ORDER BY day DESC LIMIT 1", (LAB, day))
        first = lg.one("SELECT MIN(day) AS d FROM allocations WHERE kind='applied' "
                       "AND day<=?", (day,))
        notional = float(acfg.settings().get("notional_capital") or 0)
        since = (first or {}).get("d")
        from altdata.observations import canonical_instant      # noqa: PLC0415
        end = canonical_instant(cutoff)
        week0 = canonical_instant((dt.datetime.fromisoformat(end)
                                   - dt.timedelta(days=7)).isoformat())
        k = lg.one("SELECT COUNT(*) AS n FROM loop_events WHERE written_at>? AND "
                   "written_at<=?", (week0, end))["n"]
        if not eq or not since or not notional:
            perf = "no equity recorded yet"
        else:
            perf = f"{(float(eq['equity']) / notional - 1) * 100:+.1f}% since {since}"
        dd = f"drawdown {abs(float(eq['drawdown'])) * 100:.1f}%" if eq else "drawdown n/a"
        n = len(live)
        return (f"Alpha Lab: {perf} · {n} engine{'s' if n != 1 else ''} live · "
                f"{dd} · loop events this week {k}")
    finally:
        lg.close()
