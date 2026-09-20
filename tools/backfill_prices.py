"""
One-time price backfill: five years, every symbol, availability RECONSTRUCTED.

A live pull stamps `available_at` with the write instant, which is honest because
it is an upper bound -- we certainly knew the close by the time we wrote it down.
A BACKFILL CANNOT DO THAT. Writing today's instant onto a 2022 close would say the
system did not know that price until 2026, and every as-of-correct computation
before today would then find nothing. That is exactly what the FRED history does,
and it is why the market-state backfill could only reach back to 30 May.

So this tool RECONSTRUCTS the availability: a session's close was knowable at the
close plus a declared latency
(`yfinance_source.RECONSTRUCTED_LATENCY_MINUTES`), and every row it writes is
flagged `availability_kind = reconstructed` so a reader can tell a reconstructed
availability from an observed one.

-----------------------------------------------------------------------------
THE RULE, AND WHY IT IS ENFORCED HERE RATHER THAN REMEMBERED
-----------------------------------------------------------------------------

**Reconstructed availability is permitted only for series whose
`revision_policy` is `never` or `split_only`.**

A daily close is knowable at the close and is never restated except by a split,
so reconstructing when it was knowable RECOVERS the truth. A REVISABLE series is
the opposite: FRED's August payrolls exist in three vintages, and stamping "known
at the release" on what is actually the third revision would hand a backtest a
number that did not exist for months -- a leak that no as-of join can catch,
because the join would be working correctly on a lie.

Revisable series get ALFRED vintages or nothing.

This tool reads `revision_policy` out of the registry and REFUSES any metric that
is not reconstructable. tools/validate_prices.py asserts the refusal.

    python tools/backfill_prices.py --years 5            # all symbols
    python tools/backfill_prices.py --years 5 --dry-run
    python tools/backfill_prices.py --symbols SPY,RSP
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import derived, observations, session          # noqa: E402
from altdata.sources import yfinance_source as yf_src       # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 16:00 ET, as a UTC hour. EDT is UTC-4 and EST is UTC-5, so the close is 20:00
# or 21:00 UTC depending on the date. Resolved per-session through the session
# module rather than assumed, because a fixed offset would put half the year's
# reconstructed availabilities an hour before the close they describe.
CLOSE_HOUR_ET = 16


def reconstructed_available_at(day: str,
                               latency_minutes: Optional[int] = None) -> str:
    """When a session's close was knowable: the close plus a declared latency."""
    mins = (yf_src.RECONSTRUCTED_LATENCY_MINUTES if latency_minutes is None
            else latency_minutes)
    d = dt.date.fromisoformat(day[:10])
    naive = dt.datetime(d.year, d.month, d.day, CLOSE_HOUR_ET, 0)
    tz = session._eastern_tz()                                # noqa: SLF001
    eastern = naive.replace(tzinfo=tz) if tz is not None else naive.replace(
        tzinfo=dt.timezone(dt.timedelta(hours=-4)))
    utc = eastern.astimezone(dt.timezone.utc) + dt.timedelta(minutes=mins)
    return observations.canonical_instant(utc.isoformat())


def reconstructable(metric_id: str) -> tuple[bool, str]:
    """Whether a reconstructed availability is permitted for this metric."""
    e = derived.registry_entry(metric_id)
    if not e:
        return False, (f"{metric_id} has no registry entry, so its revision "
                       f"policy is unknown -- and an unknown policy is not a "
                       f"reconstructable one")
    policy = e.get("revision_policy")
    if policy in observations.RECONSTRUCTABLE_POLICIES:
        return True, f"revision_policy {policy!r}"
    return False, (f"{metric_id} has revision_policy {policy!r}; reconstructed "
                   f"availability is permitted only for "
                   f"{list(observations.RECONSTRUCTABLE_POLICIES)}. A revisable "
                   f"series needs ALFRED vintages or nothing")


def backfill(symbols: Optional[dict[str, str]] = None, years: int = 5,
             dry_run: bool = False,
             store: Optional[observations.ObservationStore] = None) -> dict:
    basket = symbols or yf_src.SYMBOLS
    own = store is None
    db = store or observations.ObservationStore()
    out: dict = {"symbols": len(basket), "written": 0, "refused": [],
                 "failed": [], "series": {}, "dry_run": dry_run}
    try:
        for symbol, key in basket.items():
            metric = f"yfinance.{key}"
            allowed, why = reconstructable(metric)
            if not allowed:
                out["refused"].append((metric, why))
                print(f"  REFUSED {metric}: {why}")
                continue
            try:
                parsed = yf_src._fetch_symbol(symbol, period=f"{years}y")  # noqa: SLF001
            except Exception as exc:                          # noqa: BLE001
                out["failed"].append((key, str(exc)))
                print(f"  FAILED  {symbol}: {exc}")
                continue
            closes, dropped = yf_src.drop_non_session_bars(
                symbol, parsed["closes"])
            if dropped:
                print(f"  {symbol:<8} dropped {len(dropped)} non-session bar(s): "
                      f"{dropped[-3:]}")
            rows = []
            for suffix, series in (("", closes),
                                   (yf_src.DIVIDEND_SUFFIX, parsed["dividends"]),
                                   (yf_src.SPLIT_SUFFIX, parsed["splits"])):
                rows += [{"registry_key": f"{metric}{suffix}", "instrument": None,
                          "observed_at": d,
                          "available_at": reconstructed_available_at(d),
                          "value": v, "source": "yfinance",
                          "availability_kind": "reconstructed"}
                         for d, v in series]
            n = 0 if dry_run else db.write_many(rows)
            out["written"] += n
            out["series"][key] = {
                "closes": len(closes),
                "dropped_non_session": len(dropped),
                "dividends": len(parsed["dividends"]),
                "splits": len(parsed["splits"]),
                "rows_written": n,
                "first": closes[0][0] if closes else None,
                "last": closes[-1][0] if closes else None}
            print(f"  {symbol:<8} {len(closes):>5} closes  "
                  f"{len(parsed['dividends']):>3} div  "
                  f"{len(parsed['splits']):>2} split  -> {n} rows"
                  + ("  (dry run)" if dry_run else ""))
    finally:
        if own:
            db.close()
    return out


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("--years", type=int, default=5)
    p.add_argument("--symbols", default=None,
                   help="comma-separated tickers (default: the whole basket)")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)

    basket = yf_src.SYMBOLS
    if a.symbols:
        want = {s.strip().upper() for s in a.symbols.split(",") if s.strip()}
        basket = {k: v for k, v in yf_src.SYMBOLS.items() if k.upper() in want}
        missing = want - {k.upper() for k in basket}
        if missing:
            print(f"not in the basket: {sorted(missing)}")
            return 2

    print(f"price backfill -- {len(basket)} symbols, {a.years}y, availability "
          f"RECONSTRUCTED as the close + "
          f"{yf_src.RECONSTRUCTED_LATENCY_MINUTES} minutes")
    r = backfill(basket, years=a.years, dry_run=a.dry_run)
    print(f"\n{r['written']} rows written across {len(r['series'])} series; "
          f"{len(r['refused'])} refused, {len(r['failed'])} failed")
    for m, why in r["refused"]:
        print(f"  refused {m}: {why}")
    return 1 if r["failed"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
