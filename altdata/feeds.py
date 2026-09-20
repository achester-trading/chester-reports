"""
The scheduled feeds: one entry point, two timers.

The market-state object is computed at 16:45 from whatever is in the store, and
before Phase 2b the store held no prices at all and, on the box, no FRED rows
either. This module is what fills it, and it exists as ONE entry point because two
wrappers call it and a second copy of "which feeds run, in what order, and what
counts as a failure" would drift the way the validator list once did.

    python -m altdata.feeds pull            # every enabled feed
    python -m altdata.feeds pull --only prices
    python -m altdata.feeds check           # freshness; exit 1 when stale

-----------------------------------------------------------------------------
WHEN IT RUNS, AND WHY TWICE
-----------------------------------------------------------------------------

  16:10 ET, in chester-eod, BEFORE the 16:45 object computes. This is the pull
         that matters: the object is only as current as the feed that preceded
         it.
  06:45 ET, in chester-overnight. The CORRECTION pass. It exists because the
         16:10 pull can be wrong in two ways that the evening cannot fix: a
         close revised after 16:10 (a late print, an exchange correction), and a
         session missed entirely because the box was down. The morning pull
         re-reads the last two years, so a gap heals itself on the next
         successful run rather than needing a human to notice it.

Two pulls a day of the same window is deliberate duplication, and it is cheap:
the observation store is append-only with a vintage key, so a re-pull of an
unchanged close writes nothing at all. Only an actual revision creates a row.

-----------------------------------------------------------------------------
A MISSING KEY IS NOT A FAILURE, AND IS NOT SILENCE EITHER
-----------------------------------------------------------------------------

FRED needs FRED_API_KEY. When it is absent this logs once at WARNING and exits 0,
because a wrapper that fails on a missing key turns one configuration gap into a
red pipeline and trains the reader to ignore the light. The gap is surfaced by the
FRESHNESS CHECK instead, which the heartbeat reads: the series go stale, the
heartbeat says which, and the reason is in the log. A configuration problem should
show up as the data going stale, not as a crash.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from . import observations, session
from .sources import yfinance_source as yf_src

log = logging.getLogger(__name__)

# HOW STALE A FEED MAY BE before the heartbeat calls it stale, in sessions. Two
# is one session's grace: the check runs in the morning, so the last completed
# session's bars must be present, and a single missed pull is reported rather
# than tolerated.
MAX_STALE_SESSIONS = 2

FEEDS = ("prices", "fred")


def price_keys() -> list[str]:
    """Every close series the basket should carry."""
    return [f"yfinance.{k}" for k in yf_src.SYMBOLS.values()]


def fred_keys() -> list[str]:
    from . import config
    return [f"fred.{s.key}" for s in config.FRED_SERIES]


# ---------------------------------------------------------------------------
# Pull
# ---------------------------------------------------------------------------
def pull_prices(run_id: Optional[str] = None) -> dict:
    """The 28-symbol basket into the observation store (and the CSV copy)."""
    from .store import Store
    try:
        csv_store: Optional[Store] = Store()
    except Exception as exc:                                  # noqa: BLE001
        log.warning("CSV store unavailable (%s); writing observations only", exc)
        csv_store = None
    summary = yf_src.pull(store=csv_store, run_id=run_id)
    log.info("prices: %d/%d symbols, %d failed", summary["success"],
             summary["total"], len(summary["failed"]))
    for key, err in summary["failed"]:
        log.warning("prices: %s failed -- %s", key, err)
    return summary


def pull_fred(run_id: Optional[str] = None) -> dict:
    """The FRED set into the store, or a stated skip when the key is absent."""
    if not os.environ.get("FRED_API_KEY"):
        # ONCE, at WARNING, AND EXIT 0. See the module docstring: a wrapper that
        # fails here turns a configuration gap into a red pipeline. The freshness
        # check is what surfaces it, and it surfaces it as the data going stale --
        # which is the true statement.
        log.warning("fred: FRED_API_KEY is not set -- skipping the pull. The "
                    "series will go stale and the heartbeat's freshness check "
                    "will say so; this is not a pipeline failure.")
        return {"skipped": "no FRED_API_KEY", "total": 0, "success": 0,
                "failed": []}
    from .sources import fred as fred_src
    from .store import Store
    summary = fred_src.pull(Store())
    log.info("fred: %d/%d series, %d failed", summary.get("success", 0),
             summary.get("total", 0), len(summary.get("failed") or []))
    for key, err in summary.get("failed") or []:
        log.warning("fred: %s failed -- %s", key, err)
    return summary


def pull(only: Optional[str] = None, run_id: Optional[str] = None) -> dict:
    out: dict[str, Any] = {"ran": [], "skipped": []}
    for name, fn in (("prices", pull_prices), ("fred", pull_fred)):
        if only and only != name:
            out["skipped"].append(name)
            continue
        try:
            out[name] = fn(run_id=run_id)
            out["ran"].append(name)
        except Exception as exc:                              # noqa: BLE001
            # ONE FEED NEVER TAKES THE OTHER DOWN. The whole point of running
            # both from one step is that the step is not all-or-nothing.
            log.exception("%s pull raised", name)
            out[name] = {"error": f"{type(exc).__name__}: {exc}"}
            out["ran"].append(name)
    return out


# ---------------------------------------------------------------------------
# Freshness -- the heartbeat's data gate
# ---------------------------------------------------------------------------
def freshness(as_of: Optional[str] = None,
              store: Optional[observations.ObservationStore] = None) -> dict:
    """Which feeds are current, which are stale, and which are absent.

    A DATA GATE AND NOT A CI JOB, for the reason the iv-solver split established:
    this verdict depends on the data on the box at the moment it runs, so a CI
    runner -- which has neither the box's store nor its network -- could only ever
    report on a fixture. The question "are today's bars present" can only be asked
    where the store is.
    """
    own = store is None
    db = store or observations.ObservationStore()
    try:
        last = session.last_trading_session().isoformat()
        out: dict[str, Any] = {"session": last, "as_of": as_of, "feeds": {}}
        for name, keys in (("prices", price_keys()), ("fred", fred_keys())):
            absent, stale, fresh = [], [], []
            for k in keys:
                rows = db.as_of(k, as_of=as_of)
                if not rows:
                    absent.append(k)
                    continue
                newest = str(rows[-1]["observed_at"])[:10]
                n, _ = _sessions_between(newest, last)
                (fresh if n <= MAX_STALE_SESSIONS else stale).append(k)
            out["feeds"][name] = {
                "expected": len(keys), "fresh": len(fresh),
                "stale": len(stale), "absent": len(absent),
                "stale_keys": sorted(stale)[:8],
                "absent_keys": sorted(absent)[:8],
                "ok": not stale and not absent}
        out["ok"] = all(f["ok"] for f in out["feeds"].values())
        out["max_stale_sessions"] = MAX_STALE_SESSIONS
        return out
    finally:
        if own:
            db.close()


def _sessions_between(a: str, b: str) -> tuple[int, str]:
    from . import derived
    return derived.sessions_between(a, b)


def format_freshness(r: dict) -> str:
    bits = []
    for name, f in (r.get("feeds") or {}).items():
        bits.append(f"{name}={f['fresh']}/{f['expected']}"
                    + (f" stale:{f['stale']}" if f["stale"] else "")
                    + (f" absent:{f['absent']}" if f["absent"] else ""))
    return f"session={r.get('session')} " + " ".join(bits)


def _main(argv: list[str]) -> int:
    import argparse
    import json
    p = argparse.ArgumentParser(description="The scheduled feeds.")
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("pull", help="run the feeds")
    pl.add_argument("--only", choices=FEEDS, default=None)
    pl.add_argument("--run-id", default=None)
    pl.add_argument("--json", action="store_true")

    ck = sub.add_parser("check", help="freshness; exit 1 when a feed is stale")
    ck.add_argument("--as-of", default=None)
    ck.add_argument("--json", action="store_true")

    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    if a.cmd == "pull":
        r = pull(only=a.only, run_id=a.run_id)
        if a.json:
            print(json.dumps(r, indent=2, sort_keys=True, default=str))
        else:
            for name in r["ran"]:
                d = r.get(name) or {}
                if d.get("skipped"):
                    print(f"  {name:7} SKIPPED -- {d['skipped']}")
                elif d.get("error"):
                    print(f"  {name:7} ERROR -- {d['error']}")
                else:
                    print(f"  {name:7} {d.get('success', 0)}/"
                          f"{d.get('total', 0)} ok, "
                          f"{len(d.get('failed') or [])} failed")
        return 0                      # a feed failure is stale data, not a crash

    r = freshness(as_of=a.as_of)
    print(json.dumps(r, indent=2, sort_keys=True) if a.json
          else format_freshness(r))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
