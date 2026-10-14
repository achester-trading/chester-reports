"""
The engine interface (X-1.3).

An engine is a module with a fixed interface and nothing else: what it trades
(`universe`), when (`signal`), how much (`size`), when it leaves (`exits`),
what that costs (`cost_class`), the parameter ranges it was validated over and
the kill rule it is born with. Engines are independent of each other; the
allocator combines them.

THE REGISTRY IS THE ONLY PLACE AN ENGINE IS NAMED. config/alpha_engines.yaml
lists each engine's id, family, horizon, its class as a dotted path, its
min_size and its parameters; `registered()` loads them, and no loop or report
names an engine any other way. Tranche 1 registers none.

An engine reads the store only through the ReadOnlyStore it is handed, at the
as-of instant it is handed; it never opens a connection, never fetches and never
writes. It does not size above its minimum before its sample: the allocator
decides that, from the ledger's posterior.
"""

from __future__ import annotations

import abc
import importlib
from dataclasses import dataclass, field
from typing import Any, Optional

from . import config as acfg

# Where an engine's module may live: inside alpha/, so tools/validate_alpha_no_orders.py
# reads it. (The gates add their fixture's package for the length of a test.)
ENGINE_PACKAGES: tuple[str, ...] = ("alpha.engines.",)


@dataclass
class Instrument:
    """One tradable thing: its id (what the blocklist checks), the store key its
    prices live under, and its cost class (config/alpha_costs.yaml)."""
    id: str
    key: str
    cost_class: str
    quote_keys: Optional[tuple[str, str]] = None   # (bid key, ask key), if stored
    store_instrument: Optional[str] = None         # the store's instrument column
    meta: dict = field(default_factory=dict)


@dataclass
class Signal:
    """An engine's intent at an as-of instant. direction +1 long, -1 short."""
    instrument: Instrument
    direction: int
    as_of: str
    strength: float = 1.0
    stop: Optional[float] = None
    target: Optional[float] = None
    time_stop_days: Optional[int] = None
    params: dict = field(default_factory=dict)


@dataclass
class Bar:
    day: str
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None


class Engine(abc.ABC):
    """The abstract base. Concrete engines set the class attributes and
    implement the four methods."""

    engine_id: str = ""
    family: str = ""
    horizon: str = "daily"                # intraday | daily | weekly
    cost_class: str = "etf"
    validated_ranges: dict = {}           # parameter -> [low, high]
    kill_rule: dict = {}                  # the constitution's, plus any stricter
    min_size: float = 0.0

    def __init__(self, params: Optional[dict] = None) -> None:
        self.params = dict(params or {})
        if self.horizon not in acfg.HORIZONS:
            raise ValueError(f"{self.engine_id}: horizon {self.horizon!r} is not "
                             f"one of {acfg.HORIZONS}")

    @abc.abstractmethod
    def universe(self) -> list[Instrument]:
        """What the engine may trade."""

    @abc.abstractmethod
    def signal(self, as_of: str, store) -> list[Signal]:
        """Signals knowable at `as_of`, from the ReadOnlyStore handed in."""

    @abc.abstractmethod
    def size(self, signal: Signal, risk_budget: float) -> float:
        """A fraction of the engine's capital, given the allocator's budget."""

    @abc.abstractmethod
    def exits(self, position: dict, bar: Bar) -> Optional[str]:
        """An exit reason for this bar beyond the bracket (stop, target, time),
        or None to hold. The bracket itself is alpha/paper.py's."""


def registered(path=None) -> list[dict]:
    """The registry's entries, as written."""
    return acfg.engines(path)


def load(entry: dict) -> Engine:
    """Instantiate one registry entry: `class` is `module:Class` or
    `module.Class`, `params` its parameters. The module must live under
    ENGINE_PACKAGES -- inside alpha/, where the no-orders gate reads it."""
    target = str(entry["class"])
    mod_name, _, cls_name = (target.partition(":") if ":" in target
                             else target.rpartition("."))
    if not any(mod_name.startswith(p) for p in ENGINE_PACKAGES):
        raise ValueError(f"engine {entry.get('id')}: {mod_name} is outside "
                         f"{ENGINE_PACKAGES} -- an engine lives in alpha/engines/")
    cls = getattr(importlib.import_module(mod_name), cls_name)
    eng = cls(entry.get("params") or {})
    eng.engine_id = str(entry.get("id") or eng.engine_id)
    for k in ("family", "horizon", "cost_class"):
        if entry.get(k) is not None:
            setattr(eng, k, entry[k])
    if entry.get("min_size") is not None:
        eng.min_size = float(entry["min_size"])
    return eng


def load_all(path=None) -> list[Engine]:
    return [load(e) for e in registered(path)]


def registry_entry(eng: Engine) -> dict[str, Any]:
    return {"id": eng.engine_id, "family": eng.family, "horizon": eng.horizon,
            "cost_class": eng.cost_class, "min_size": eng.min_size,
            "validated_ranges": eng.validated_ranges, "kill_rule": eng.kill_rule}
