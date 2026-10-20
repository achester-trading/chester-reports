"""
One stored record per earnings print: the implied move at the close before the
report and the realised move after it (signal-triage Batch 11 item 57, ruled 19 Oct
2026).

    from altdata import earnings_moves as em
    em.record_due(st, "2026-10-29", now, events_db=db)   # the close after a report

KEY `calc.earnings_move`, instrument the symbol, observed_at the report date,
value_text {implied_pct, implied_label, realised_pct, close_before, close_after,
before, after}. WRITTEN ONCE, by the 16:45 close of the first session after the
report (the reaction rule of OS-11: the close before the report date to the close
after it); a report already recorded is skipped. The implied move is the Ahead
matrix's own (daily_cascade.ahead.implied_move: the event-only move where an
expiry before the report exists, else the full straddle, labelled), read from the
chain captured on the session before the report. READ by the Ahead rows
(opening_setup.with_pricing) and offered to the Alpha Lab's engine 4 (session B's
line), which does not read it yet. Report-only: no flag, no decision.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Optional

log = logging.getLogger(__name__)
KEY = "calc.earnings_move"


def _closes(st, sym: str, now: str) -> dict[str, float]:
    return {str(r["observed_at"])[:10]: float(r["value_num"])
            for r in st.as_of(f"yfinance.mkt_{sym.lower()}", now)
            if r.get("value_num") is not None}


def due(events: list[dict], today: str, universe: list[str]) -> list[dict]:
    """The reports whose first session after the report date is `today`."""
    from altdata import session                                 # noqa: PLC0415
    out = []
    for e in events:
        pl = e.get("payload") or {}
        if isinstance(pl, str):
            try:
                pl = json.loads(pl or "{}")
            except ValueError:
                pl = {}
        sym = str(pl.get("symbol") or "").upper()
        d = str(e.get("observed_at"))[:10]
        if sym not in universe or not d or d >= today:
            continue
        nxt = dt.date.fromisoformat(d) + dt.timedelta(days=1)
        while not session.is_trading_session(nxt):
            nxt += dt.timedelta(days=1)
        if nxt.isoformat() == today:
            out.append({"symbol": sym, "date": d, "time": pl.get("time")})
    return out


def record(st, sym: str, d: str, today: str, now: str, chain_base=None,
           time: Optional[str] = None) -> Optional[dict]:
    """The row for one print, or None when a close is not stored."""
    from altdata import session                                 # noqa: PLC0415
    from daily_cascade import ahead                             # noqa: PLC0415
    import re                                                   # noqa: PLC0415
    closes = _closes(st, sym, now)
    before = max((x for x in closes if x < d), default=None)
    if before is None or today not in closes:
        return None
    b_sess = session.previous_trading_session(d).isoformat()
    label = ahead.implied_move(sym, d, f"{b_sess}T21:30:00+00:00", chain_base,
                               days_back=0, time=time)
    m = re.search(r"±\s*([\d.]+)%", label or "")
    val = {"implied_pct": float(m.group(1)) if m else None, "implied_label": label,
           "realised_pct": round(100.0 * (closes[today] / closes[before] - 1.0), 3),
           "close_before": closes[before], "close_after": closes[today],
           "before": before, "after": today}
    return {"registry_key": KEY, "instrument": sym, "observed_at": d,
            "available_at": now, "value": json.dumps(val, sort_keys=True),
            "source": "daily_close"}


def record_due(st, today: str, now: str, events_db: Optional[str] = None,
               chain_base=None, universe: Optional[list[str]] = None) -> int:
    """The close's step: write each due print's record once. Never raises."""
    from altdata import config as acfg, events as ev_mod        # noqa: PLC0415
    try:
        uni = universe or acfg.chain_universe()
        first = (dt.date.fromisoformat(today) - dt.timedelta(days=10)).isoformat()
        with ev_mod.EventStore(events_db) as ev:
            evs = [r for r in ev.calendar(first, today, as_of=now)
                   if r.get("type") == "earnings"]
        rows = []
        for x in due(evs, today, uni):
            # Written once: a print already recorded is skipped (read per symbol --
            # as_of without an instrument reads only rows that carry none).
            if any(str(r["observed_at"])[:10] == x["date"]
                   for r in st.as_of(KEY, now, x["symbol"])):
                continue
            row = record(st, x["symbol"], x["date"], today, now, chain_base, x.get("time"))
            if row:
                rows.append(row)
        if rows:
            st.write_many(rows)
        return len(rows)
    except Exception:                                           # noqa: BLE001
        log.warning("the earnings-move records faulted", exc_info=True)
        return 0
