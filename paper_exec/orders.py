"""
An intended entry, checked as a bracket and sized, before anything is built.

    intent = Intent(engine_id, signal_id, "MES", side=1, entry=6010.0, stop=5990.0,
                    target=6050.0)
    why = check(intent)                 # None, or the reason it is not sent
    qty, why = size(intent, contract, cfg, limits, open_risk, governor)

A BRACKET OR NOTHING. The entry is a limit; the stop and the target are both
attached, on the right sides of it (a long's stop below and target above; a
short's the other way). A parent without either is refused here and again at the
send (executor._send counts three orders, the children tied to the parent).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class Intent:
    engine_id: str
    signal_id: Optional[int]
    symbol: str
    side: int                     # +1 buy, -1 sell
    entry: Optional[float]
    stop: Optional[float]
    target: Optional[float]
    note: str = ""
    extra: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)


def check(i: Intent) -> Optional[str]:
    """None when the intent is a whole bracket; else why it is not sent."""
    if i.side not in (-1, 1):
        return f"side {i.side!r} is neither buy nor sell"
    if i.entry is None:
        return "no entry price: an entry is a limit order"
    if i.stop is None or i.target is None:
        return ("not a bracket: the stop and the target are both attached or the "
                "entry is not sent")
    if i.side == 1 and not (i.stop < i.entry < i.target):
        return f"a long's stop ({i.stop}) must be below its entry ({i.entry}) and its target ({i.target}) above"
    if i.side == -1 and not (i.target < i.entry < i.stop):
        return f"a short's stop ({i.stop}) must be above its entry ({i.entry}) and its target ({i.target}) below"
    return None


def risk_per_contract(i: Intent, multiplier: float) -> float:
    return abs(float(i.entry) - float(i.stop)) * float(multiplier)


def heat_budget(limits: dict) -> float:
    """The Doctrine's heat cap in dollars: heat_max_pct of capital_usd."""
    cap = float(((limits.get("capital_usd") or {}).get("value")) or 0)
    pct = float((((limits.get("limits") or {}).get("heat_max_pct") or {}).get("value"))
                or 0)
    return cap * pct / 100.0


def size(i: Intent, c: dict, cfg: dict, limits: dict, open_risk: float,
         governor: dict) -> tuple[int, str]:
    """(contracts, why): the config's ceiling, halved for a halved engine, then
    cut to what the heat cap leaves after the open paper risk. 0 means not
    sent, and `why` says which limit."""
    if governor.get("lab") == "halted":
        return 0, "the lab is halted (governor): the operator's resume lifts it"
    eng = governor.get("engine") or {}
    if eng.get("frozen") or eng.get("status") in ("validation", "retired"):
        return 0, f"engine {i.engine_id} is {eng.get('status')}{', frozen' if eng.get('frozen') else ''} (governor)"
    qty = int(cfg.get("max_contracts") or 0)
    why = f"the ceiling, {qty} contract(s)"
    if eng.get("status") == "halved":
        qty = int(math.floor(qty / 2))
        why = f"halved by the governor to {qty}"
    per = risk_per_contract(i, c["multiplier"])
    room = heat_budget(limits) - float(open_risk)
    fit = int(math.floor(room / per)) if per > 0 else 0
    if fit < qty:
        qty, why = max(fit, 0), (f"the heat cap leaves ${max(room, 0):,.0f} for "
                                 f"${per:,.0f} a contract")
    return qty, why
