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
from typing import Any, Optional

from . import observations, secrets, session
from .sources import yfinance_source as yf_src

log = logging.getLogger(__name__)

# HOW STALE A FEED MAY BE -- A MULTIPLE OF EACH SERIES' OWN ALLOWANCE, never a
# flat session count.
#
# This was `MAX_STALE_SESSIONS = 2`, and it made exactly the mistake that
# `max_staleness_sessions` made in the state object: a daily calendar applied to
# series that are not daily. The first successful FRED pull on the box proved it --
# 59 of 59 series fetched, every daily series current to the previous session, and
# the check reported 44 of 59 STALE, because a quarterly GDP print is 117 sessions
# old when it is perfectly on time and a monthly PCE print is 55.
#
# A heartbeat that says feed_stale on a healthy feed is worse than no check: it is
# an alarm that is always on. So each series is judged against its registry
# allowance -- information_half_life at its own cadence -- times the multiple.
#
# THE MULTIPLE IS READ FROM config/market_state.yaml rather than declared twice.
# "Is this series current enough to say something about today" is one question, and
# two numbers would be two answers to it.
STALENESS_MULTIPLE_FALLBACK = 3


def staleness_multiple() -> float:
    """The declared multiple, from the state object's config."""
    try:
        import regime
        return float((regime.load_config().get("defaults") or {}).get(
            "staleness_multiple") or STALENESS_MULTIPLE_FALLBACK)
    except Exception:                                         # noqa: BLE001
        return float(STALENESS_MULTIPLE_FALLBACK)

FEEDS = ("prices", "fred", "official", "loggers")

# THE PUBLISHED-FILE WRITERS (signal-triage order, ST-1). Official publications
# that are not on FRED: the NY Fed's ACM term premium, the SF Fed's term-premium
# model, the Board's DKW decomposition, TreasuryDirect's auction results and the
# Fiscal Data MSPD. One feed, run in the same step as prices
# and FRED -- 16:10 in chester-eod and the 06:45 correction pass -- rather than a
# unit of its own, because "which feeds run, in what order" lives in one place.
# Each is a module under altdata/sources/ exposing KEYS and pull(run_id).
OFFICIAL_WRITERS = ("acm", "sffed", "dkw", "treasury_auctions", "fiscaldata")


def _official_modules() -> list:
    from importlib import import_module
    out = []
    for name in OFFICIAL_WRITERS:
        try:
            out.append((name, import_module(f"{__package__}.sources.{name}")))
        except Exception as exc:                              # noqa: BLE001
            log.warning("official writer %s failed to import: %s", name, exc)
            out.append((name, None))
    return out


def official_keys() -> list[str]:
    keys: list[str] = []
    for _name, mod in _official_modules():
        if mod is not None:
            keys.extend(getattr(mod, "KEYS", []))
    return keys


def price_keys() -> list[str]:
    """Every close series the basket should carry."""
    return [f"yfinance.{k}" for k in yf_src.SYMBOLS.values()]


def fred_keys() -> list[str]:
    from . import config
    return [f"fred.{s.key}" for s in config.FRED_PULL_SERIES]


def logger_rosters() -> list[tuple[str, list[str]]]:
    """(name, keys) for every 6a logger that asked to be watched.

    THE WHOLE REASON THE ROSTER EXISTS: a dead logger looks exactly like a quiet
    one. A logger that stops writing has to reach the heartbeat, and the only way
    that happens is if something knows the keys it should be writing.

    A logger may declare `in_freshness=False` -- one awaiting an entitlement
    decision is dormant BY DESIGN and must not make the heartbeat red for it.

    AND IT MAY DECLARE `probe_keys`, which are excluded here. A probe row records
    "we asked and were refused"; on a working route there is nothing to record, so
    counting the empty key reports a stale feed for a feed that is fine -- which is
    what the VX curve did on its first evening, taking the heartbeat to exit 11
    with seven of eight keys fresh and 688 sessions just written.
    """
    from .loggers import load_all
    out = []
    for name, spec in sorted(load_all().items()):
        if not spec.in_freshness:
            continue
        try:
            probes = set(getattr(spec, "probe_keys", ()) or ())
            out.append((name, [k for k in spec.keys() if k not in probes]))
        except Exception as exc:                              # noqa: BLE001
            log.warning("logger %s could not list its keys: %s", name, exc)
    return out


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
    if not secrets.present("FRED_API_KEY"):
        # ONCE, at WARNING, AND EXIT 0. See the module docstring: a wrapper that
        # fails here turns a configuration gap into a red pipeline. The freshness
        # check is what surfaces it, and it surfaces it as the data going stale --
        # which is the true statement.
        # present() rather than get(): the verdict is logged, so the value must
        # never be in a string that reaches a log at all.
        log.warning("fred: %s is not configured (checked the environment AND "
                    ".env) -- skipping the pull. The series will go stale and the "
                    "heartbeat's freshness check will say so; this is not a "
                    "pipeline failure.", "FRED_API_KEY")
        return {"skipped": "key not configured", "total": 0, "success": 0,
                "failed": []}
    from .sources import fred as fred_src
    from .store import Store
    summary = fred_src.pull(Store())
    log.info("fred: %d/%d series, %d failed", summary.get("success", 0),
             summary.get("total", 0), len(summary.get("failed") or []))
    for key, err in summary.get("failed") or []:
        log.warning("fred: %s failed -- %s", key, err)
    return summary


def pull_official(run_id: Optional[str] = None) -> dict:
    """Every published-file writer, each isolated from the others.

    A writer that fails returns STALE and writes nothing (see
    sources/_publication.py); one that raises past that is caught here, so a
    broken NY Fed workbook never costs the Board's CSV.
    """
    out: dict[str, Any] = {"ran": [], "total": 0, "written": 0, "stale": []}
    for name, mod in _official_modules():
        out["ran"].append(name)
        out["total"] += 1
        if mod is None:
            out[name] = {"status": "STALE", "reason": "module failed to import",
                         "written": 0}
            out["stale"].append(name)
            continue
        try:
            r = mod.pull(run_id=run_id)
        except Exception as exc:                              # noqa: BLE001
            log.exception("%s raised", name)
            r = {"status": "STALE", "reason": f"{type(exc).__name__}: {exc}",
                 "written": 0}
        out[name] = r
        out["written"] += int(r.get("written") or 0)
        if r.get("status") != "OK":
            out["stale"].append(name)
    return out


def pull_loggers(run_id: Optional[str] = None) -> dict:
    """Every 6a logger, each isolated from the others.

    ONE LOGGER NEVER TAKES ANOTHER DOWN. They share a step because they share a
    cadence, not because they share a fate: a vendor outage in one must not cost
    the night's rows in four others, and every day not logged is history that
    cannot be bought back.
    """
    from .loggers import load_all
    out: dict[str, Any] = {"ran": [], "total": 0, "written": 0}
    for name, spec in sorted(load_all().items()):
        if spec.requires_key and not secrets.present(spec.requires_key):
            out[name] = {"skipped": f"{spec.requires_key} not configured"}
            out["ran"].append(name)
            log.warning("%s: %s is not configured -- built but dormant; the "
                        "freshness roster reports it as the series going stale",
                        name, spec.requires_key)
            continue
        try:
            r = spec.run(run_id=run_id)
            out[name] = r
            out["written"] += int(r.get("written") or 0)
        except Exception as exc:                              # noqa: BLE001
            log.exception("%s raised", name)
            out[name] = {"error": f"{type(exc).__name__}: {exc}"}
        out["ran"].append(name)
        out["total"] += 1
    return out


def pull(only: Optional[str] = None, run_id: Optional[str] = None,
         skip: tuple[str, ...] = ()) -> dict:
    out: dict[str, Any] = {"ran": [], "skipped": []}
    for name, fn in (("prices", pull_prices), ("fred", pull_fred),
                     ("official", pull_official), ("loggers", pull_loggers)):
        if (only and only != name) or name in skip:
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
        from . import derived
        # THE LAST SESSION WHOSE DATA SHOULD EXIST, not the latest on the calendar.
        # Before today's close, today's bars do not exist and their absence is not
        # staleness -- it is the afternoon not having happened yet.
        last = session.last_completed_session().isoformat()
        multiple = staleness_multiple()
        out: dict[str, Any] = {"session": last, "as_of": as_of, "feeds": {}}
        rosters = [("prices", price_keys()), ("fred", fred_keys()),
                   ("official", official_keys())]
        rosters += logger_rosters()
        for name, keys in rosters:
            absent, stale, fresh = [], [], []
            detail = {}
            if not keys:
                out["feeds"][name] = {"expected": 0, "fresh": 0, "stale": 0,
                                      "absent": 0, "stale_keys": [],
                                      "stale_detail": {}, "absent_keys": [],
                                      "ok": True,
                                      "note": "declares no keys yet"}
                continue
            for k in keys:
                rows = db.as_of(k, as_of=as_of)
                if not rows:
                    # INSTRUMENT-KEYED SERIES. as_of() matches instrument exactly
                    # and most macro rows carry NULL, so a per-ticker logger looks
                    # empty on the default join. Ask which instruments exist and
                    # take the freshest of them: the question here is "did this
                    # logger write last night", not "did it write for SPY".
                    insts = db.instruments(k)
                    newest_any = None
                    for inst in insts:
                        r2 = db.as_of(k, as_of=as_of, instrument=inst)
                        if r2:
                            d = str(r2[-1]["observed_at"])[:10]
                            newest_any = max(newest_any or d, d)
                    if newest_any is None:
                        absent.append(k)
                        continue
                    rows = [{"observed_at": newest_any}]
                newest = str(rows[-1]["observed_at"])[:10]
                n, _ = _sessions_between(newest, last)
                own, _why = derived.staleness_allowance(k)
                # half_life permanent cannot go stale -- a graded outcome does not
                # decay -- so such a series is fresh by definition rather than by
                # a number nobody can choose.
                limit = None if own is None else int(round(own * multiple))
                if limit is not None and n > limit:
                    stale.append(k)
                    detail[k] = f"{n} sessions, limit {limit}"
                else:
                    fresh.append(k)
            out["feeds"][name] = {
                "expected": len(keys), "fresh": len(fresh),
                "stale": len(stale), "absent": len(absent),
                "stale_keys": sorted(stale)[:8],
                "stale_detail": {k: detail[k] for k in sorted(detail)[:8]},
                "absent_keys": sorted(absent)[:8],
                "ok": not stale and not absent}
        out["ok"] = all(f["ok"] for f in out["feeds"].values())
        out["staleness_multiple"] = multiple
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
    pl.add_argument("--skip", default="",
                    help="comma-separated feeds to skip, e.g. loggers")
    pl.add_argument("--run-id", default=None)
    pl.add_argument("--json", action="store_true")

    ck = sub.add_parser("check", help="freshness; exit 1 when a feed is stale")
    ck.add_argument("--as-of", default=None)
    ck.add_argument("--json", action="store_true")

    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    if a.cmd == "pull":
        r = pull(only=a.only, run_id=a.run_id,
                 skip=tuple(x.strip() for x in a.skip.split(",") if x.strip()))
        if a.json:
            print(json.dumps(r, indent=2, sort_keys=True, default=str))
        else:
            for name in r["ran"]:
                d = r.get(name) or {}
                if d.get("skipped"):
                    print(f"  {name:7} SKIPPED -- {d['skipped']}")
                elif d.get("error"):
                    print(f"  {name:7} ERROR -- {d['error']}")
                elif name == "official":
                    for wn in d.get("ran") or []:
                        sub = d.get(wn) or {}
                        note = (f"{sub.get('written', 0)} rows"
                                if sub.get("status") == "OK"
                                else f"STALE -- {sub.get('reason')}")
                        print(f"  writer  {wn:24} {note}")
                    print(f"  {name:7} {d.get('total', 0)} ran, "
                          f"{d.get('written', 0)} rows written, "
                          f"{len(d.get('stale') or [])} stale")
                elif name == "loggers":
                    # THE LOGGER STEP HAS A DIFFERENT SHAPE from a feed's, and
                    # printing it through the feed template reported "0/5 ok" for a
                    # step in which four loggers wrote 2,900 rows. A summary that
                    # understates a success is a summary that gets ignored when it
                    # reports a failure.
                    for ln in sorted(d.get("ran") or []):
                        sub = d.get(ln) or {}
                        note = (sub.get("skipped") or sub.get("error")
                                or f"{sub.get('written', 0)} rows")
                        print(f"  logger  {ln:24} {note}")
                    print(f"  {name:7} {d.get('total', 0)} ran, "
                          f"{d.get('written', 0)} rows written")
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
