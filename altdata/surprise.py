"""
Surprise v1: actual against a declared naive expectation, and the real one for
earnings.

    python -m altdata.surprise compute
    python -m altdata.surprise show --metric fred.cpi
    python -m altdata.surprise compute --dry-run

-----------------------------------------------------------------------------
TWO KINDS OF SURPRISE, AND THEY ARE NOT THE SAME MEASUREMENT
-----------------------------------------------------------------------------

  calc.surprise_vs_naive       MACRO. Actual minus a rule written down in advance
                               (config/naive_expectations.yaml). There is no free
                               macro consensus, so `calc.surprise_vs_consensus` is
                               not_yet_sourced rather than approximated -- and
                               every name, description and payload here says
                               `naive` so the two can never be quoted as one.

  calc.earnings_surprise_pct   EARNINGS. Actual minus the ANALYST MEAN, from
                               yfinance, which published it before the print. This
                               is a surprise in the ordinary sense.

The distinction is the whole point of the piece. A naive surprise measures whether
a series did what its own recent history implied; a consensus surprise measures
whether the market was wrong. Conflating them would let the first be read as the
second, which is a claim about other people's expectations that this system cannot
support.

-----------------------------------------------------------------------------
THE EXPECTATION IS COMPUTED FROM DATA STRICTLY BEFORE THE PRINT
-----------------------------------------------------------------------------

A "forecast" that can see the value it forecasts is not one. For each observation
the expectation is built from that series' PRIOR observations only, in observation
order, and the row's available_at is the ACTUAL's availability -- the instant the
surprise became computable. So:

    observed_at    = the period the actual describes
    available_at   = when the actual became knowable (inherited from it)
    ingested_at    = when this pass computed it

A revision is a second vintage of the actual, so recomputing gives a second
vintage of the surprise, with a later available_at and the same observed_at. That
is the same treatment every derived series gets here and it means "what did the
surprise look like at the time" stays answerable after a restatement.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from . import observations, session

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
NAIVE_PATH = REPO / "config" / "naive_expectations.yaml"

# PREFIXES, not keys: one metric per series, so each inherits its own units from
# the series it measures. `calc.surprise_vs_naive.cpi` is in index points and
# `calc.surprise_vs_naive.u3_rate` is in percentage points, and one registry entry
# could not have said both.
SURPRISE_PREFIX = "calc.surprise_vs_naive."
EXPECTATION_PREFIX = "calc.naive_expectation."
EARNINGS_KEY = "calc.earnings_surprise_pct"


def surprise_key(series_key: str) -> str:
    return SURPRISE_PREFIX + series_key


def expectation_key(series_key: str) -> str:
    return EXPECTATION_PREFIX + series_key

METHODS = ("last", "trend_3m")

_CFG: Optional[dict] = None


def config() -> dict:
    global _CFG
    if _CFG is None:
        import yaml
        with NAIVE_PATH.open(encoding="utf-8") as fp:
            _CFG = yaml.safe_load(fp) or {}
    return _CFG


def method_for(series_key: str) -> tuple[str, str]:
    """(method, why) for a bare series key such as `cpi`."""
    cfg = config()
    entry = (cfg.get("series") or {}).get(series_key)
    if entry:
        m = str(entry.get("method") or cfg.get("default") or "last")
        if m not in METHODS:
            raise ValueError(
                f"naive expectation method {m!r} for {series_key} is not one of "
                f"{METHODS} -- a method nothing implements would silently fall "
                f"back and the fallback would not be declared anywhere")
        return m, str(entry.get("because") or "")
    return str(cfg.get("default") or "last"), "the declared default"


def _expect(values: list[float], method: str, n_trend: int) -> Optional[float]:
    """The expectation for the NEXT observation, from prior ones only."""
    if not values:
        return None
    if method == "last":
        return values[-1]
    if len(values) < n_trend + 1:
        # NOT ENOUGH HISTORY FOR THE DECLARED METHOD, so no row rather than a
        # silent fall back to `last`: a surprise computed by a method other than
        # the one declared for the series is mislabelled, and mislabelled is worse
        # than absent.
        return None
    steps = [values[-i] - values[-i - 1] for i in range(1, n_trend + 1)]
    return values[-1] + sum(steps) / len(steps)


def macro_rows(db: observations.ObservationStore,
               as_of: Optional[str] = None,
               first_day: Optional[str] = None) -> list[dict]:
    """A surprise and an expectation row per observation of every tracked series."""
    from . import config as altconfig
    cfg = config()
    n_trend = int(cfg.get("trend_observations") or 3)
    rows: list[dict] = []
    for spec in altconfig.FRED_SERIES:
        metric = f"fred.{spec.key}"
        try:
            method, _why = method_for(spec.key)
        except ValueError as exc:
            log.warning("%s: %s", metric, exc)
            continue
        obs = [r for r in db.as_of(metric, as_of=as_of)
               if r["value_num"] is not None]
        if len(obs) < 2:
            continue
        values: list[float] = []
        for r in obs:
            day = str(r["observed_at"])[:10]
            expect = _expect(values, method, n_trend)
            values.append(float(r["value_num"]))
            if expect is None:
                continue
            if first_day and day < first_day:
                continue
            actual = float(r["value_num"])
            avail = str(r["available_at"])
            common = {"instrument": None, "observed_at": day,
                      "available_at": avail, "source": "calc",
                      "availability_kind": "ingest_instant"}
            rows.append(dict(common, registry_key=expectation_key(spec.key),
                             value=round(expect, 6)))
            rows.append(dict(common, registry_key=surprise_key(spec.key),
                             value=round(actual - expect, 6)))
    return rows


def earnings_rows(as_of: Optional[str] = None) -> list[dict]:
    """The REAL surprise, read out of the events table's earnings rows."""
    from . import events as ev_mod
    rows: list[dict] = []
    with ev_mod.EventStore() as ev:
        for e in ev.since("1990-01-01T00:00:00Z", as_of=as_of,
                          types=["earnings"]):
            pct = (e.get("payload") or {}).get("surprise_pct")
            sym = (e.get("payload") or {}).get("symbol")
            if pct is None or not sym:
                continue
            rows.append({"registry_key": EARNINGS_KEY, "instrument": sym,
                         "observed_at": str(e["observed_at"])[:10],
                         "available_at": str(e["available_at"]),
                         "value": round(float(pct), 6), "source": "yfinance",
                         "availability_kind": "ingest_instant"})
    return rows


def compute(as_of: Optional[str] = None, first_day: Optional[str] = None,
            store: Optional[observations.ObservationStore] = None,
            dry_run: bool = False) -> dict:
    own = store is None
    db = store or observations.ObservationStore()
    try:
        macro = macro_rows(db, as_of=as_of, first_day=first_day)
        earn = earnings_rows(as_of=as_of)
        rows = macro + earn
        written = 0 if dry_run else db.write_many(rows)
        by_key: dict[str, int] = {}
        for r in rows:
            by_key[r["registry_key"]] = by_key.get(r["registry_key"], 0) + 1
        return {"computed": len(rows), "written": written, "by_key": by_key,
                "macro_rows": len(macro), "earnings_rows": len(earn),
                "dry_run": dry_run}
    finally:
        if own:
            db.close()


def _main(argv: list[str]) -> int:
    import argparse
    from . import derived
    p = argparse.ArgumentParser(description="Surprise against a declared naive.")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compute")
    c.add_argument("--as-of", default=None)
    c.add_argument("--from", dest="first", default=None)
    c.add_argument("--dry-run", action="store_true")
    sh = sub.add_parser("show")
    sh.add_argument("--metric", default="fred.cpi")
    sh.add_argument("--as-of", default=None)
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    if a.cmd == "compute":
        r = compute(as_of=a.as_of, first_day=a.first, dry_run=a.dry_run)
        print(f"{r['computed']} rows ({r['macro_rows']} macro, "
              f"{r['earnings_rows']} earnings), {r['written']} written"
              + ("  (dry run)" if r["dry_run"] else ""))
        for k in sorted(r["by_key"]):
            print(f"  {k:32} {r['by_key'][k]:>6}")
        return 0

    key = a.metric.split(".", 1)[-1]
    method, why = method_for(key)
    print(f"{a.metric}: naive method `{method}` -- {why or 'the default'}")
    for mk in (expectation_key(key), surprise_key(key)):
        d = derived.derived_forms(mk, a.as_of)
        print(f"  {mk:32} level={d['level']}  pct={d['percentile']}  "
              f"n={d['n']}  observed={d['observed_at']}")
    return 0


if __name__ == "__main__":                                     # pragma: no cover
    import sys
    raise SystemExit(_main(sys.argv[1:]))
