"""
Forward-only loggers: the roster, and the pattern every one of them follows.

Audit sub-phase 6a. These write history and nothing else. No lifecycle machine, no
absorption hypotheses, no meme board, no theme block -- those are 6g and 6h and are
gated on evidence these loggers do not yet have. The bar here is "writes rows
tonight", because every day a logger is not running is a day of history that cannot
be recovered at any price.

-----------------------------------------------------------------------------
THE PATTERN, AND WHY EACH PART OF IT IS THERE
-----------------------------------------------------------------------------

  PROBE FIRST. Nothing is built against a documented API; it is built against one
  that answered. A probe result is stored even when it fails, because "we asked and
  were refused" is a fact worth keeping and is the difference between a dormant
  logger and a forgotten one.

  OBSERVATIONS WITH THE THREE CLOCKS. Everything lands in the observation store with
  observed_at, available_at and ingested_at, so a logger's history is as-of
  correct from its first row rather than from the day someone remembers to fix it.

  REGISTRY ENTRIES, trigger_eligible: false, with the right half_life. A metric with
  no entry has no delta semantics, no staleness allowance and no revision policy --
  and a logger that writes unregistered keys is writing numbers nothing can read.

  DERIVED METRICS READ `insufficient_history` UNTIL THE DECLARED MINIMUM EXISTS.
  Not None, not zero, not a number computed from four observations: a STRING that
  cannot be mistaken for a reading. A concentration index over six days is not a
  small sample, it is not a measurement.

  DECLARED TO THE FRESHNESS ROSTER, so a logger that stops emails instead of
  silently stopping. This is the whole reason the roster exists: a dead logger looks
  exactly like a quiet one.

  SECRETS THROUGH altdata.secrets, never committed, never printed. A logger whose
  key is absent BUILDS ANYWAY, logs once at WARNING, exits 0, and goes stale --
  because a configuration gap that reads as a crash trains the reader to ignore the
  light.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

log = logging.getLogger(__name__)

# The string a derived metric returns before its logger has enough history. A
# string, deliberately: None reads as "missing" and 0.0 reads as a measurement, and
# this is neither.
INSUFFICIENT = "insufficient_history"


@dataclass(frozen=True)
class LoggerSpec:
    """One logger, as the roster knows it."""

    name: str
    description: str
    # The metric ids it writes. A callable, because some are computed from a
    # universe that lives in config.
    keys: Callable[[], list[str]]
    # The nightly step. Returns a summary dict; never raises past its own boundary.
    run: Callable[..., dict]
    # The secret it needs, if any. Absent means dormant-but-built, not broken.
    requires_key: Optional[str] = None
    # Rows of history before its derived metrics stop reading insufficient_history.
    min_history: int = 60
    # Whether freshness should alarm on it yet. A logger awaiting an entitlement
    # decision is dormant by design and must not make the heartbeat red.
    in_freshness: bool = True
    notes: str = ""


ROSTER: dict[str, LoggerSpec] = {}


def register(spec: LoggerSpec) -> LoggerSpec:
    """Add a logger to the roster. Called at import time by each module."""
    if spec.name in ROSTER:
        raise ValueError(f"logger {spec.name!r} is already registered")
    ROSTER[spec.name] = spec
    return spec


def load_all() -> dict[str, LoggerSpec]:
    """Import every logger module so the roster is complete.

    Imported lazily and defensively: a logger that fails to import must not take
    down the freshness check that would have told you about it.
    """
    from importlib import import_module
    for mod in ("rtat", "consensus", "auction", "borrow", "shielded"):
        try:
            import_module(f"{__name__}.{mod}")
        except Exception as exc:                              # noqa: BLE001
            log.warning("logger module %s failed to import: %s", mod, exc)
    return ROSTER


def enough_history(key: str, minimum: int, store=None,
                   instrument: Optional[str] = None) -> tuple[bool, int]:
    """(has enough, how many). The gate every derived metric asks before computing."""
    from .. import observations
    own = store is None
    db = store or observations.ObservationStore()
    try:
        n = len(db.as_of(key, instrument=instrument))
        return n >= minimum, n
    finally:
        if own:
            db.close()


def enough_days(key: str, minimum: int, store=None) -> tuple[bool, int]:
    """(has enough, how many) counting DISTINCT OBSERVED DATES, across instruments.

    THE MEASURE THAT MATTERS FOR A PER-TICKER LOGGER, and the first version of this
    got it wrong in a way that looked right: it counted rows for one arbitrary
    instrument, and for RTAT10 -- where the visible set turns over and 536 tickers
    have appeared across a decade -- the alphabetically first ticker had ONE day. A
    logger with ten years of history reported insufficient_history:1/60.

    The question a derived metric is asking is "how many days of this series do I
    have", not "how many rows does one member have".
    """
    from .. import observations
    own = store is None
    db = store or observations.ObservationStore()
    try:
        n = db.conn.execute(
            "SELECT COUNT(DISTINCT observed_at) FROM observations "
            " WHERE registry_key = ?", (key,)).fetchone()[0]
        return n >= minimum, int(n)
    finally:
        if own:
            db.close()


def guarded_days(key: str, minimum: int, compute: Callable[[], object],
                 store=None) -> object:
    """`compute()` if the logger has enough DAYS, else the marker with its count."""
    ok, n = enough_days(key, minimum, store=store)
    if not ok:
        return f"{INSUFFICIENT}:{n}/{minimum}"
    return compute()


def guarded(key: str, minimum: int, compute: Callable[[], object],
            store=None, instrument: Optional[str] = None) -> object:
    """`compute()` if the history is there, else the INSUFFICIENT marker.

    The marker carries the count, so a reader sees how far off it is rather than
    only that it is not ready.
    """
    ok, n = enough_history(key, minimum, store=store, instrument=instrument)
    if not ok:
        return f"{INSUFFICIENT}:{n}/{minimum}"
    return compute()
