"""
The Weekly's lab line (X-1.11) -- the one line a report prints from the lab.

    Alpha Lab: +x.x% since <date> · n engines live · drawdown y% (z% since inception)
               · loop events this week k

and "Alpha Lab: not yet live" until the first engine passes into paper (status
live or halved). Read from alpha.db READ-ONLY (`mode=ro`): a missing ledger is
"not yet live", never an error, and nothing here creates the file. The Weekly
calls weekly_line() once, from its one hook in daily_cascade/weekly_stack.py.

  +x.x% since <date>   the lab's equity against its notional, since the first
                       day an engine held an applied allocation
  n engines live       live or halved (a halved engine still trades)
  drawdown y%          the lab's, from its high-water mark (0.0% at the mark)
  (z% since inception) from the ALL-TIME high (the notional, or the highest equity
                       ever recorded), which no operator resume re-bases -- so a
                       resume never hides a loss (15 Oct 2026)
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
        if eq:
            peak = lg.one("SELECT MAX(equity) AS m FROM equity WHERE engine_id=? AND "
                          "day<=?", (LAB, day))["m"]
            peak = max(float(peak or 0), notional)
            inc = max(0.0, 1 - float(eq["equity"]) / peak) if peak else 0.0
            dd = (f"drawdown {abs(float(eq['drawdown'])) * 100:.1f}% "
                  f"({inc * 100:.1f}% since inception)")
        else:
            dd = "drawdown n/a"
        n = len(live)
        return (f"Alpha Lab: {perf} · {n} engine{'s' if n != 1 else ''} live · "
                f"{dd} · loop events this week {k}")
    finally:
        lg.close()


# ---------------------------------------------------------------------------
# The Daily close's line (change order 10.2 d, ruled 14 Oct 2026)
# ---------------------------------------------------------------------------
NOT_LIVE_DAILY = "Alpha Lab today: not yet live"


def daily_line(cutoff: str, path: Optional[str | Path] = None) -> str:
    """The close's one line from the lab, read-only, never raising:

        Alpha Lab today: n proposed · k screened out · j testing · m promoted
                         · lab equity x% · drawdown y%

      n proposed     hypotheses registered in the 24 hours to the cutoff, from
                     every channel (the inbox, the proposer's batches, the
                     workbench)
      k screened out of those, screened out (a duplicate, a budget)
      j testing      hypotheses the harness has now
      m promoted     promotions in the 24 hours to the cutoff
      lab equity     the lab's equity against its notional, at its latest record
      drawdown       the lab's, from its high-water mark

    "Alpha Lab today: not yet live" while alpha.db does not exist or holds
    neither a hypothesis nor an engine."""
    try:
        return _daily(cutoff, path)
    except Exception as exc:                                  # noqa: BLE001
        return f"Alpha Lab today: unavailable ({type(exc).__name__})"


def _daily(cutoff: str, path: Optional[str | Path] = None) -> str:
    p = Path(path or acfg.ledger_path())
    if not p.is_file():
        return NOT_LIVE_DAILY
    from altdata.observations import canonical_instant          # noqa: PLC0415
    from .ledger import LAB, Ledger                             # noqa: PLC0415
    lg = Ledger(p, read_only=True)
    try:
        has = {r["name"] for r in lg.q("SELECT name FROM sqlite_master WHERE type='table'")}
        if "hypotheses" not in has or "batch_id" not in {
                r["name"] for r in lg.q("PRAGMA table_info(hypotheses)")}:
            return NOT_LIVE_DAILY
        end = canonical_instant(cutoff)
        day0 = canonical_instant((dt.datetime.fromisoformat(end)
                                  - dt.timedelta(hours=24)).isoformat())
        n_h = lg.one("SELECT COUNT(*) AS n FROM hypotheses")["n"]
        n_e = lg.one("SELECT COUNT(*) AS n FROM engines")["n"]
        if not n_h and not n_e:
            return NOT_LIVE_DAILY
        # The registration EVENT, not the row's written_at, which a status change
        # rewrites: loop_events is append-only, so "registered today" is exact.
        import json                                             # noqa: PLC0415
        new = [json.loads(r["after"]) for r in lg.q(
            "SELECT after FROM loop_events WHERE kind='hypothesis_registered' AND "
            "written_at>? AND written_at<=?", (day0, end))]
        k = sum(1 for r in new if r.get("status") == "screened_out")
        j = lg.one("SELECT COUNT(*) AS n FROM hypotheses WHERE status='testing'")["n"]
        m = lg.one("SELECT COUNT(*) AS n FROM loop_events WHERE kind='promotion' AND "
                   "written_at>? AND written_at<=?", (day0, end))["n"]
        eq = lg.one("SELECT equity, drawdown FROM equity WHERE engine_id=? AND day<=? "
                    "ORDER BY day DESC LIMIT 1", (LAB, cutoff[:10]))
        notional = float(acfg.settings().get("notional_capital") or 0)
        if eq and notional:
            tail = (f"lab equity {(float(eq['equity']) / notional - 1) * 100:+.1f}% · "
                    f"drawdown {abs(float(eq['drawdown'])) * 100:.1f}%")
        else:
            tail = "lab equity n/a · drawdown n/a"
        return (f"Alpha Lab today: {len(new)} proposed · {k} screened out · {j} testing · "
                f"{m} promoted · {tail}")
    finally:
        lg.close()
