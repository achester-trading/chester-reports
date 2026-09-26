"""
Earnings dates, estimates and the real surprise, from yfinance.

    python -m altdata.sources.earnings probe
    python -m altdata.sources.earnings pull

-----------------------------------------------------------------------------
TWO ROUTES, AND ONE OF THEM NEEDS A DEPENDENCY THIS REPO DOES NOT HAVE
-----------------------------------------------------------------------------

  Ticker.calendar          WORKS TODAY, no extra dependency. Gives the NEXT
                           earnings date plus `Earnings Average / High / Low` --
                           an analyst consensus, which is the thing a naive
                           expectation is not. Forward-looking only.

  Ticker.get_earnings_dates  The history: date, EPS estimate, REPORTED EPS and
                           `Surprise(%)` per past quarter. It scrapes, so it
                           raises `ImportError: Missing optional dependency
                           'lxml'` -- which is not installed here.

So: `lxml` is added to requirements.txt and this module uses the history route
WHEN IT IMPORTS and the calendar route always. A missing dependency costs the
past, not the present, and it says so in the report rather than looking like a
quiet quarter.

-----------------------------------------------------------------------------
THE SURPRISE HERE IS A REAL SURPRISE
-----------------------------------------------------------------------------

This is why earnings and macro releases are different metrics with different
names. `Earnings Average` is a mean of analyst estimates: a published consensus
that existed BEFORE the print, so actual-minus-consensus is a surprise in the
ordinary sense. For a macro release this system has no consensus at all, so
`calc.surprise_vs_naive_*` measures actual against a DECLARED NAIVE expectation
and is labelled as such everywhere it appears. Calling both of them "surprise"
without the qualifier is the error the naming exists to prevent.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Iterable, Optional

from .. import events as ev_mod

log = logging.getLogger(__name__)

# The names the universe actually reports for. The tracked symbols are ETFs and
# indices, which do not report earnings -- so the universe for THIS source is the
# story queries' own entity lists, which is where the single names live.
def universe() -> list[str]:
    """Single names from config/story_queries.yaml, which is where they are."""
    from .news import load_queries
    out: set[str] = set()
    for spec in (load_queries().get("queries") or {}).values():
        for e in spec.get("entities") or []:
            s = str(e)
            if "." not in s and s.isupper():
                out.add(s)
    return sorted(out)


def _iso(value: Any) -> Optional[str]:
    """A date or timestamp from pandas/yfinance, as UTC ISO. None if unusable."""
    if value is None:
        return None
    try:
        if isinstance(value, dt.datetime):
            d = value if value.tzinfo else value.replace(
                tzinfo=dt.timezone.utc)
            return d.astimezone(dt.timezone.utc).isoformat()
        if isinstance(value, dt.date):
            # A DATE WITH NO TIME IS 13:30 UTC, not midnight: US earnings land
            # before the open or after the close, and midnight would put a report
            # in the wrong session. 13:30Z is the open, which is the earliest
            # instant a same-day report could be public.
            return dt.datetime(value.year, value.month, value.day, 13, 30,
                               tzinfo=dt.timezone.utc).isoformat()
        ts = getattr(value, "to_pydatetime", None)
        if ts is not None:
            return _iso(ts())
    except Exception:                                          # noqa: BLE001
        return None
    return None


def events_for(symbol: str) -> tuple[list[ev_mod.Event], dict]:
    """One symbol: the next date with its consensus, and the reported history."""
    import yfinance as yf
    out: list[ev_mod.Event] = []
    rep: dict[str, Any] = {"symbol": symbol}
    t = yf.Ticker(symbol)

    # --- FORWARD: the next date, with the analyst consensus ------------------
    try:
        cal = t.calendar or {}
        dates = cal.get("Earnings Date") or []
        when = _iso(dates[0] if isinstance(dates, list) and dates else dates)
        if when:
            out.append(ev_mod.Event(
                type="scheduled", observed_at=when, source="yfinance",
                title=f"{symbol} earnings (expected)", entities=[symbol],
                key=f"earnings-cal-{symbol}-{when[:10]}",
                payload={"kind": "earnings", "symbol": symbol,
                         "eps_estimate": cal.get("Earnings Average"),
                         "eps_estimate_high": cal.get("Earnings High"),
                         "eps_estimate_low": cal.get("Earnings Low"),
                         "revenue_estimate": cal.get("Revenue Average"),
                         "consensus": "analyst mean (yfinance)"}))
            rep["next"] = when[:10]
            rep["eps_estimate"] = cal.get("Earnings Average")
    except Exception as exc:                                   # noqa: BLE001
        rep["calendar_error"] = f"{type(exc).__name__}: {exc}"[:120]

    # --- HISTORY: reported, estimate and the real surprise ------------------
    try:
        df = t.get_earnings_dates(limit=12)
    except Exception as exc:                                   # noqa: BLE001
        rep["history"] = f"unavailable: {type(exc).__name__}: {exc}"[:140]
        return out, rep
    if df is None or not len(df):
        rep["history"] = "empty"
        return out, rep
    cols = {str(c).lower(): c for c in df.columns}
    est_c = cols.get("eps estimate")
    rep_c = cols.get("reported eps")
    sur_c = cols.get("surprise(%)") or cols.get("surprise (%)")
    kept = 0
    for idx, row in df.iterrows():
        when = _iso(idx)
        reported = row.get(rep_c) if rep_c else None
        if when is None or reported is None or reported != reported:
            continue                      # NaN reported == not reported yet
        est = row.get(est_c) if est_c else None
        sur = row.get(sur_c) if sur_c else None
        out.append(ev_mod.Event(
            type="earnings", observed_at=when, source="yfinance",
            title=f"{symbol} reported EPS {reported}", entities=[symbol],
            key=f"earnings-{symbol}-{when[:10]}",
            payload={"symbol": symbol, "reported_eps": float(reported),
                     "eps_estimate": (float(est) if est is not None
                                      and est == est else None),
                     "surprise_pct": (float(sur) if sur is not None
                                      and sur == sur else None),
                     "consensus": "analyst mean (yfinance)",
                     "surprise_kind": "vs_consensus"}))
        kept += 1
    rep["history"] = f"{kept} reported quarter(s)"
    return out, rep


def earnings_events(symbols: Optional[Iterable[str]] = None
                    ) -> tuple[list[ev_mod.Event], dict]:
    syms = list(symbols or universe())
    out: list[ev_mod.Event] = []
    report: dict[str, Any] = {"state": "ok", "symbols": syms, "per_symbol": {}}
    if not syms:
        return [], {"state": "empty", "reason": (
            "no single names declared. The tracked price universe is ETFs and "
            "indices, which do not report; the names come from the story "
            "queries' entity lists in config/story_queries.yaml")}
    for sym in syms:
        try:
            evs, rep = events_for(sym)
        except Exception as exc:                               # noqa: BLE001
            report["per_symbol"][sym] = {
                "error": f"{type(exc).__name__}: {exc}"[:140]}
            continue
        out.extend(evs)
        report["per_symbol"][sym] = rep
    return out, report


def pull(store: Optional[ev_mod.EventStore] = None,
         dry_run: bool = False) -> dict:
    own = store is None
    ev = store or ev_mod.EventStore()
    try:
        events, report = earnings_events()
        wrote = ({"seen": len(events), "inserted": 0, "duplicates": 0}
                 if dry_run else ev.write_many(events))
        return {"earnings": report, "written": wrote, "dry_run": dry_run}
    finally:
        if own:
            ev.close()


def _main(argv: list[str]) -> int:
    import argparse
    import json
    p = argparse.ArgumentParser(description="Earnings dates and surprises.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe")
    pl = sub.add_parser("pull")
    pl.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    if a.cmd == "probe":
        events, rep = earnings_events()
        print(json.dumps(rep, indent=2, default=str)[:1800])
        for e in events[:8]:
            print(f"  {e.observed_at[:10]}  {e.type:<10} {e.title[:44]:<46}"
                  f"{ {k: v for k, v in e.payload.items() if 'eps' in k or 'surprise' in k} }"[:150])
        print(f"{len(events)} earnings event(s) ready")
        return 0
    print(json.dumps(pull(dry_run=a.dry_run), indent=2, default=str)[:1800])
    return 0


if __name__ == "__main__":                                     # pragma: no cover
    import sys
    raise SystemExit(_main(sys.argv[1:]))
