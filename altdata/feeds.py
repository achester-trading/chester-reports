"""
The scheduled feeds: one entry point, two timers.

The market-state object is computed at 16:45 from whatever is in the store, and
before Phase 2b the store held no prices at all and, on the box, no FRED rows
either. This module is what fills it, and it exists as ONE entry point because two
wrappers call it and a second copy of "which feeds run, in what order, and what
counts as a failure" would drift the way the validator list once did.

    python -m altdata.feeds pull            # every enabled feed
    python -m altdata.feeds pull --only prices
    python -m altdata.feeds pull --early    # the 06:45 correction set
    python -m altdata.feeds check           # freshness; exit 1 when stale

-----------------------------------------------------------------------------
WHEN IT RUNS, AND WHY TWICE
-----------------------------------------------------------------------------

  16:10 ET, in chester-eod, BEFORE the 16:45 object computes. This is the pull
         that matters: the object is only as current as the feed that preceded
         it.
  06:45 ET, in chester-overnight. The CORRECTION pass, `pull --early`: the
         prices, plus the official writers that publish between the evening
         pull and 06:45 (EARLY_WRITERS). The prices are there because the
         16:10 pull can be wrong in two ways the evening cannot fix: a close
         revised after 16:10 (a late print, an exchange correction), and a
         session missed entirely because the box was down. The pull re-reads
         the last two years, so a gap heals itself on the next successful run.
         Until 30 Sep 2026 this was the WHOLE pull, and once ST-1/ST-2 grew it
         to 79 FRED series and 22 writers it overran the unit's five minutes
         every session from 28 Sep: systemd killed the pass before the
         overnight fetch it exists for ever ran. FRED and the other writers
         publish in the US day, so the 16:10 pull is the one that sees them.
         Then, in the same pass, `pull --only loggers` -- the loggers' ONE
         scheduled run. 16:10 skips them and so does --early, and from 30 Sep
         to 6 Oct that left them running nowhere (INC-9).
         tools/validate_feeds_scheduled.py fails a commit in which any feed in
         FEEDS has no scheduled runner.

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

FEEDS = ("prices", "fred", "official", "external", "loggers", "bars",
         "prediction_markets", "fed_funds")

# THE PUBLISHED-FILE WRITERS (signal-triage order, ST-1). Official publications
# that are not on FRED: the NY Fed's ACM term premium, the SF Fed's term-premium
# model, the Board's DKW decomposition, TreasuryDirect's auction results and the
# Fiscal Data MSPD. One feed, run in the same step as prices
# and FRED -- 16:10 in chester-eod and the 06:45 correction pass -- rather than a
# unit of its own, because "which feeds run, in what order" lives in one place.
# Each is a module under altdata/sources/ exposing KEYS and pull(run_id).
OFFICIAL_WRITERS = ("acm", "sffed", "dkw", "treasury_auctions", "fiscaldata",
                    # ST-2: the external position and the funding-currency stack
                    "tic", "safe", "mof", "cfets", "cftc",
                    # ST-2: oil stocks and the expectations surveys
                    "eia", "fedboard", "nyfed_sce")

# THE EARLY WRITERS -- the official writers whose publisher releases between the
# 16:10 pull and 06:45 ET, so the morning correction pass is the first pull that
# can see the row. MoF's JGB curve is added in the Tokyo evening (early morning
# ET); CFETS fixes USD/CNY at 09:15 Beijing (21:15 ET the evening before). Every
# other official writer publishes in the US day. A subset of OFFICIAL_WRITERS,
# never a writer of its own: same module, same keys, same family.
EARLY_WRITERS = ("mof", "cfets")

# THE EXTERNAL WRITERS (ST-2). The same contract as OFFICIAL_WRITERS -- a module
# under altdata/sources/ with KEYS and pull(run_id), STALE-not-empty on failure --
# for publishers that are not official statistical agencies: a university survey,
# the academic reference libraries, a benchmark administrator, FINRA, an ETF
# issuer. A separate group so the freshness roster reports them separately: a
# stale Ken French file is not the same news as a stale TIC release. Same step,
# same pass, same entry point; no second unit.
# LBMA left on 9 Oct 2026 (A-4): prices.lbma.org.uk answers 403 and its
# robots.txt 401, and FRED dropped the IBA gold series in January 2022. Its
# parser stays, unscheduled; the themes read the COMEX front future
# (yfinance.mkt_gold_front) under its own name.
EXTERNAL_WRITERS = ("umich", "french", "damodaran", "shiller", "worldbank",
                    "finra", "proshares",
                    # ST-2 step 3: quarterly fundamentals for the AI-capex six
                    "fundamentals",
                    # T2.2 (4 Oct 2026): the AAII bull-bear spread, a W9 gauge
                    "aaii")


def _writer_modules(names: tuple[str, ...]) -> list:
    from importlib import import_module
    out = []
    for name in names:
        try:
            out.append((name, import_module(f"{__package__}.sources.{name}")))
        except Exception as exc:                              # noqa: BLE001
            log.warning("writer %s failed to import: %s", name, exc)
            out.append((name, None))
    return out


def _official_modules() -> list:
    return _writer_modules(OFFICIAL_WRITERS)


def static_keys(name: str) -> list[str]:
    """A writer's KEYS read from its source file, for a module that will not
    import. (H-1 item 2.) An import failure used to take the writer's keys off
    the roster entirely, so the one failure that stops every row of a writer was
    the one the freshness check could not see. Only a literal list or tuple of
    strings is read; anything computed yields [] and says so in the log."""
    import ast
    from pathlib import Path as _P
    src = _P(__file__).resolve().parent / "sources" / f"{name}.py"
    try:
        tree = ast.parse(src.read_text(encoding="utf-8"))
    except Exception as exc:                                  # noqa: BLE001
        log.warning("writer %s: KEYS unreadable from source (%s)", name, exc)
        return []
    # MOST WRITERS COMPUTE KEYS from module constants -- `list(COLUMNS)`,
    # `list(HOLDINGS_KEYS) + FLOW_KEYS` -- so a literal-only read finds nothing.
    # The module's top-level assignments and function definitions are run in
    # order, WITHOUT its imports (the import is what failed) and with a small
    # set of builtins; a statement that needs an imported name is skipped. KEYS
    # resolves whenever it is built from the module's own constants.
    import builtins as _b
    safe = {n: getattr(_b, n) for n in (
        "list", "tuple", "dict", "set", "sorted", "str", "int", "float", "len",
        "range", "enumerate", "zip", "min", "max", "any", "all", "reversed")}
    ns: dict = {"__builtins__": safe, "__name__": f"static.{name}"}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.FunctionDef)):
            continue
        try:
            exec(compile(ast.Module(body=[node], type_ignores=[]),  # noqa: S102
                         str(src), "exec"), ns)
        except Exception:                                      # noqa: BLE001
            continue
    keys = ns.get("KEYS")
    if keys is None:
        log.warning("writer %s: KEYS could not be read without importing the "
                    "module -- its keys are off the roster until it imports", name)
        return []
    return [str(k) for k in keys]


def _keys(mods: list) -> list[str]:
    keys: list[str] = []
    for name, mod in mods:
        ks = (getattr(mod, "KEYS", []) if mod is not None else static_keys(name))
        keys.extend(k for k in ks if k not in keys)
    return keys


def official_keys() -> list[str]:
    return _keys(_official_modules())


def external_keys() -> list[str]:
    return _keys(_writer_modules(EXTERNAL_WRITERS))


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
# What each family's last pull ATTEMPTED (H-1 item 2: absent is not stale)
# ---------------------------------------------------------------------------
# A key that has never been written is PENDING, not stale, until its family's
# pull has completed at least once since the key was registered: a series added
# to the roster this afternoon is not a feed that failed. The pull records the
# keys it tried in $STATE_DIR/feeds_attempted.json, one list per family; the check
# reads it. An absent key its family tried is STALE -- the pull ran and nothing
# was written. With no file, every absent key is pending.
#
# A pull that ran and FAILED still attempted: a writer whose module will not
# import contributes its KEYS (read from source), and a pull skipped for a
# missing key counts too -- the module's rule is that a missing FRED_API_KEY
# surfaces as the series going stale, and "pending" would hide it forever.
#
# NOT YET DUE IS PENDING (T2.6, 8 Oct 2026). The published-file writers (official,
# external) also record, per key, the FIRST attempt and whether the writer FAILED
# (a fetch error, a parse error, an import failure: status not OK). An absent key
# whose writer failed is STALE, with the writer's reason -- AAII's HTTP 403 is a
# fault, not a calendar. An absent key whose writer ran cleanly is the source not
# having published it yet: PENDING, until a full staleness allowance (the key's
# own cadence x the multiple) has passed since its first attempt, after which it
# is STALE ("no row in N sessions of clean pulls"). A family that records no
# outcomes (prices, FRED, the loggers) keeps the rule above.
ATTEMPTED_FILE = "feeds_attempted.json"


def _state_dir():
    import os
    from pathlib import Path as _P
    return _P(os.environ.get("CHESTER_STATE_DIR") or (_P.home() / ".chester"))


def read_attempted() -> Optional[dict]:
    """{family: [keys]} from the last pulls, or None when no pull has recorded."""
    import json
    p = _state_dir() / ATTEMPTED_FILE
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except Exception as exc:                                  # noqa: BLE001
        log.warning("%s unreadable (%s) -- treating every absent key as pending",
                    p, exc)
        return None
    return {k: list((v or {}).get("keys") or []) for k, v in d.items()}


def read_attempt_outcomes() -> dict:
    """{family: {"first": {key: iso}, "failed": {key: reason}, "outcomes": bool}}
    for the families that record outcomes; {} when nothing is recorded."""
    import json
    try:
        d = json.loads((_state_dir() / ATTEMPTED_FILE).read_text(encoding="utf-8"))
    except Exception:                                         # noqa: BLE001
        return {}
    return {k: {"first": dict((v or {}).get("first") or {}),
                "failed": dict((v or {}).get("failed") or {}),
                "outcomes": bool((v or {}).get("outcomes"))}
            for k, v in d.items() if isinstance(v, dict)}


def writer_failures(mods: list, out: dict) -> dict:
    """{key: reason} for every key of a writer whose pull did not return OK."""
    failed: dict[str, str] = {}
    for name, mod in mods:
        r = out.get(name) or {}
        if r.get("status") == "OK":
            continue
        why = f"{name}: {r.get('reason') or 'status ' + str(r.get('status'))}"
        for k in _keys([(name, mod)]):
            failed[k] = why[:160]
    return failed


def record_attempted(family: str, keys: list[str], merge: bool = False,
                     failed: Optional[dict] = None) -> None:
    """Merge one family's attempted keys into the file. Never raises: a pull that
    wrote its rows must not fail on its bookkeeping.

    merge=True ADDS to the family's recorded keys instead of replacing them. A
    partial pull (the 06:45 early writers) attempted a subset; replacing the list
    with that subset would turn every other writer's absent key back into
    `pending` until 16:10 -- hiding a stale feed for most of the day."""
    import json
    try:
        d = _state_dir()
        d.mkdir(parents=True, exist_ok=True)
        p = d / ATTEMPTED_FILE
        try:
            cur = json.loads(p.read_text(encoding="utf-8"))
        except Exception:                                     # noqa: BLE001
            cur = {}
        was = cur.get(family) or {}
        prior = set(was.get("keys") or []) if merge else set()
        now = session.utc_iso()
        entry = {"keys": sorted(prior | set(keys)), "at": now}
        if failed is not None:
            # OUTCOMES (T2.6): the first attempt per key is kept across pulls; the
            # failures are this pull's, merged over the prior ones for the keys a
            # partial pull did not try.
            first = dict(was.get("first") or {})
            for k in keys:
                first.setdefault(k, now)
            old = dict(was.get("failed") or {}) if merge else {}
            for k in keys:
                old.pop(k, None)
            old.update(failed)
            entry.update({"outcomes": True, "first": first, "failed": old})
        cur[family] = entry
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(cur, indent=1, sort_keys=True), encoding="utf-8")
        tmp.replace(p)
    except Exception as exc:                                  # noqa: BLE001
        log.warning("could not record %s's attempted keys: %s", family, exc)


# ---------------------------------------------------------------------------
# Pull
# ---------------------------------------------------------------------------
def pull_prices(run_id: Optional[str] = None) -> dict:
    """The price basket (yfinance_source.SYMBOLS) into both stores."""
    from .store import Store
    try:
        csv_store: Optional[Store] = Store()
    except Exception as exc:                                  # noqa: BLE001
        log.warning("CSV store unavailable (%s); writing observations only", exc)
        csv_store = None
    summary = yf_src.pull(store=csv_store, run_id=run_id)
    record_attempted("prices", price_keys())
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
        # ATTEMPTED, so the series read stale rather than pending forever.
        record_attempted("fred", fred_keys())
        return {"skipped": "key not configured", "total": 0, "success": 0,
                "failed": []}
    from .sources import fred as fred_src
    from .store import Store
    summary = fred_src.pull(Store())
    record_attempted("fred", fred_keys())
    log.info("fred: %d/%d series, %d failed", summary.get("success", 0),
             summary.get("total", 0), len(summary.get("failed") or []))
    for key, err in summary.get("failed") or []:
        log.warning("fred: %s failed -- %s", key, err)
    return summary


def pull_official(run_id: Optional[str] = None,
                  names: Optional[tuple[str, ...]] = None) -> dict:
    """Every published-file writer, each isolated from the others -- or, with
    `names`, just those (the 06:45 EARLY_WRITERS).

    A writer that fails returns STALE and writes nothing (see
    sources/_publication.py); one that raises past that is caught here, so a
    broken NY Fed workbook never costs the Board's CSV.
    """
    mods = _official_modules() if names is None else _writer_modules(names)
    out = _pull_writers(mods, run_id)
    record_attempted("official", _keys(mods), merge=names is not None,
                     failed=writer_failures(mods, out))
    return out


def pull_external(run_id: Optional[str] = None) -> dict:
    """The external writers, on the same terms as the official ones."""
    mods = _writer_modules(EXTERNAL_WRITERS)
    out = _pull_writers(mods, run_id)
    record_attempted("external", _keys(mods), failed=writer_failures(mods, out))
    return out


def _pull_writers(mods: list, run_id: Optional[str]) -> dict:
    out: dict[str, Any] = {"ran": [], "total": 0, "written": 0, "stale": []}
    for name, mod in mods:
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

    def _attempted(name: str, spec) -> None:
        try:
            record_attempted(name, list(spec.keys()))
        except Exception as exc:                              # noqa: BLE001
            log.warning("logger %s could not list its keys: %s", name, exc)

    for name, spec in sorted(load_all().items()):
        if spec.requires_key and not secrets.present(spec.requires_key):
            out[name] = {"skipped": f"{spec.requires_key} not configured"}
            out["ran"].append(name)
            log.warning("%s: %s is not configured -- built but dormant; the "
                        "freshness roster reports it as the series going stale",
                        name, spec.requires_key)
            _attempted(name, spec)
            continue
        try:
            r = spec.run(run_id=run_id)
            out[name] = r
            out["written"] += int(r.get("written") or 0)
        except Exception as exc:                              # noqa: BLE001
            log.exception("%s raised", name)
            out[name] = {"error": f"{type(exc).__name__}: {exc}"}
        _attempted(name, spec)
        out["ran"].append(name)
        out["total"] += 1
    return out


def pull_bars(run_id: Optional[str] = None) -> dict:
    """THE TAPE SET'S BARS (reporting-stack T1, ruled 2 Oct 2026): the session's
    5-minute bars and recent daily bars, into the `bars` table this feed creates
    and owns. In the 16:10 eod run only -- the 06:45 early set skips it and the
    16:45 close runs prices alone -- because the close reads bars and never
    fetches them (30.4). Retries a missing final bar for up to five minutes."""
    from . import bars as bars_mod                             # noqa: PLC0415
    out = bars_mod.pull()
    short = {k: v for k, v in out["instruments"].items()
             if v.get("error") or not v.get("final_bar")}
    for k, v in short.items():
        log.warning("bars: %s short -- %s", k, v.get("error") or
                    f"{v.get('5m')} bars, final bar missing after "
                    f"{v.get('attempts')} attempt(s)")
    log.info("bars: %d instruments, %d short", len(out["instruments"]), len(short))
    return out


# 6d. The venues' keys the heartbeat watches: pm.market is written only when a
# description changes, so it is not a freshness key.
PREDICTION_KEYS = ("pm.probability", "pm.volume")


def pull_prediction_markets(run_id: Optional[str] = None) -> dict:
    """KALSHI AND POLYMARKET (6d): the watch list and the discovery slice, read
    from public endpoints into the store. In the 16:10 eod run AND the 06:45
    early set (brief section 4), so the close prints the day's change. An outage
    is recorded as attempted, so the heartbeat reads a dead venue as stale rather
    than pending."""
    from .sources import prediction_markets as pm_src         # noqa: PLC0415
    out = pm_src.pull(run_id=run_id)
    record_attempted("prediction_markets", list(PREDICTION_KEYS))
    for k, v in (out.get("errors") or {}).items():
        log.warning("prediction_markets: %s -- %s", k, v)
    log.info("prediction_markets: %s markets, %s written", out.get("markets"),
             out.get("written"))
    return out


def pull_fed_funds(run_id: Optional[str] = None) -> dict:
    """FED FUNDS FUTURES (6d rate path, brief 2.4): the next ten monthly
    contracts from yfinance. In the 16:10 eod run only -- a settlement, like a
    close, is a 16:00 fact."""
    from . import fed_funds                                   # noqa: PLC0415
    out = fed_funds.pull(run_id=run_id)
    record_attempted("fed_funds", [fed_funds.KEY])
    log.info("fed_funds: served %s; failed %s", out.get("served"),
             sorted(out.get("failed") or {}))
    return out


# THE EARLY SET'S SKIPS. Named rather than inlined in pull() so that
# tools/validate_feeds_scheduled.py can ask what `--early` leaves out instead of
# keeping its own copy -- a fixed set that silently dropped the loggers is the
# reason that gate exists (INC-9).
EARLY_SKIP = ("fred", "external", "loggers", "bars", "fed_funds")


def selection(only: Optional[str] = None, skip: tuple[str, ...] = (),
              early: bool = False) -> tuple[str, ...]:
    """The feeds a pull with these arguments runs, in FEEDS order. The one
    answer to "does this invocation run feed X", shared by pull() and the
    scheduling gate."""
    if early:
        only, skip = None, EARLY_SKIP
    return tuple(n for n in FEEDS
                 if not (only and only != n) and n not in skip)


def pull(only: Optional[str] = None, run_id: Optional[str] = None,
         skip: tuple[str, ...] = (), early: bool = False) -> dict:
    """Run the feeds. `early` is the 06:45 correction set: the prices and the
    EARLY_WRITERS, nothing else (see the module docstring)."""
    out: dict[str, Any] = {"ran": [], "skipped": []}
    if early:
        only = None
        skip = EARLY_SKIP
    for name, fn in (("prices", pull_prices), ("fred", pull_fred),
                     ("official", (lambda run_id: pull_official(run_id, EARLY_WRITERS))
                      if early else pull_official),
                     ("external", pull_external), ("loggers", pull_loggers),
                     ("bars", pull_bars),
                     ("prediction_markets", pull_prediction_markets),
                     ("fed_funds", pull_fed_funds)):
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
                   ("official", official_keys()),
                   ("external", external_keys())]
        rosters += logger_rosters()
        from . import fed_funds as _ff                         # noqa: PLC0415
        rosters += [("prediction_markets", list(PREDICTION_KEYS)),
                    ("fed_funds", [_ff.KEY])]
        attempted = read_attempted()
        outcomes = read_attempt_outcomes()
        out["attempted_recorded"] = attempted is not None
        for name, keys in rosters:
            absent, stale, fresh, pending = [], [], [], []
            detail, pdetail = {}, {}
            tried = set((attempted or {}).get(name) or [])
            oc = outcomes.get(name) or {}
            if not keys:
                out["feeds"][name] = {"expected": 0, "fresh": 0, "stale": 0,
                                      "absent": 0, "pending": 0, "stale_keys": [],
                                      "stale_detail": {}, "absent_keys": [],
                                      "pending_keys": [], "ok": True,
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
                        # ABSENT IS NOT STALE until the family's pull has tried.
                        if k not in tried:
                            pending.append(k)
                            pdetail[k] = "no pull has tried it yet"
                        elif not oc.get("outcomes"):
                            stale.append(k)
                            detail[k] = "attempted, nothing written"
                        elif k in oc["failed"]:
                            stale.append(k)
                            detail[k] = f"never written; the writer failed ({oc['failed'][k]})"
                        else:
                            # THE WRITER RAN CLEANLY: the source has not
                            # published it. Pending while its next release is
                            # not yet due -- one allowance since the first try.
                            first = str(oc["first"].get(k) or "")[:10]
                            allow, _w = derived.staleness_allowance(k)
                            lim = None if allow is None else int(round(allow * multiple))
                            n = (_sessions_between(first, last)[0]
                                 if first and first <= last else 0)
                            if lim is not None and first and n > lim:
                                stale.append(k)
                                detail[k] = (f"never written; no row in {n} sessions "
                                             f"of clean pulls, limit {lim}")
                            else:
                                pending.append(k)
                                pdetail[k] = (f"not yet published; first tried "
                                              f"{first or 'n/a'}, due within "
                                              f"{lim if lim is not None else 'any'} "
                                              f"sessions")
                        continue
                    rows = [{"observed_at": newest_any}]
                newest = str(rows[-1]["observed_at"])[:10]
                n, _ = _sessions_between(newest, last)
                allow, _why = derived.staleness_allowance(k)
                # half_life permanent cannot go stale -- a graded outcome does not
                # decay -- so such a series is fresh by definition rather than by
                # a number nobody can choose.
                limit = None if allow is None else int(round(allow * multiple))
                if limit is not None and n > limit:
                    stale.append(k)
                    detail[k] = f"{n} sessions, limit {limit}"
                else:
                    fresh.append(k)
            out["feeds"][name] = {
                "expected": len(keys), "fresh": len(fresh),
                "stale": len(stale), "absent": len(absent),
                "pending": len(pending),
                "stale_keys": sorted(stale)[:8],
                "stale_detail": {k: detail[k] for k in sorted(detail)[:8]},
                "absent_keys": sorted(absent)[:8],
                "pending_keys": sorted(pending)[:8],
                "pending_detail": {k: pdetail[k] for k in sorted(pdetail)[:8]},
                # OK = NO STALE KEYS. A pending key is a key no pull has tried.
                "ok": not stale}
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
    """The one-line summary: per family, fresh of expected, then the counts."""
    bits = []
    for name, f in (r.get("feeds") or {}).items():
        bits.append(f"{name}={f['fresh']}/{f['expected']}"
                    + (f" stale:{f['stale']}" if f["stale"] else "")
                    + (f" absent:{f['absent']}" if f["absent"] else "")
                    + (f" pending:{f.get('pending', 0)}" if f["absent"] else ""))
    return f"session={r.get('session')} " + " ".join(bits)


def named_keys(r: dict) -> list[str]:
    """THE SERIES BEHIND THE COUNTS (T2.6): one line per stale key and per
    pending key, family first, with why -- what the 08:30 verdict names. The
    vocabulary is this module's and only this module's: STALE (due and not
    current, or a writer that failed), PENDING (not yet due, or never tried).
    An absent key is one or the other, and says which. At most eight per family
    (the JSON's own cap); the counts above carry the rest."""
    out = []
    for name, f in (r.get("feeds") or {}).items():
        absent = set(f.get("absent_keys") or [])
        for k in f.get("stale_keys") or []:
            out.append(f"stale {name} {k}"
                       + (" (absent)" if k in absent else "")
                       + f": {(f.get('stale_detail') or {}).get(k) or 'stale'}")
        for k in f.get("pending_keys") or []:
            out.append(f"pending {name} {k} (absent): "
                       f"{(f.get('pending_detail') or {}).get(k) or 'pending'}")
    return out


def _main(argv: list[str]) -> int:
    import argparse
    import json
    p = argparse.ArgumentParser(description="The scheduled feeds.")
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("pull", help="run the feeds")
    pl.add_argument("--only", choices=FEEDS, default=None)
    pl.add_argument("--skip", default="",
                    help="comma-separated feeds to skip, e.g. loggers")
    pl.add_argument("--early", action="store_true",
                    help="the 06:45 correction set: prices + EARLY_WRITERS")
    pl.add_argument("--run-id", default=None)
    pl.add_argument("--json", action="store_true")

    ck = sub.add_parser("check", help="freshness; exit 1 when a feed is stale")
    ck.add_argument("--as-of", default=None)
    ck.add_argument("--json", action="store_true")

    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    if a.cmd == "pull":
        if a.early and (a.only or a.skip):
            p.error("--early is a fixed set; it takes neither --only nor --skip")
        r = pull(only=a.only, run_id=a.run_id, early=a.early,
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
                elif name in ("official", "external"):
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
    if a.json:
        print(json.dumps(r, indent=2, sort_keys=True))
    else:
        # THE SUMMARY, THEN THE NAMES (T2.6): the heartbeat logs every line and
        # puts the first in its verdict, with the stale names after it.
        print(format_freshness(r))
        for ln in named_keys(r):
            print(f"  {ln}")
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
