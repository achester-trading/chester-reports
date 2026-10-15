"""
The cost model (X-1.4). Every ledger fill carries its modelled costs, component
by component, and the edge an engine claims is stated after them or not at all.

NEVER THE MID. Where a quote is stored the fill crosses half the quoted spread (a
buy at the ask, a sell at the bid); where none is, half of the class's fixed
spread estimate around the reference price (the next bar's open). Slippage,
commission and -- over the holding period -- borrow, roll, funding and FX are
added on top, each a non-negative cost. config/alpha_costs.yaml holds the
numbers and its header says how each is applied.

THE CALIBRATION is the nightly loop's: it compares the modelled spread against
the spread the store actually quoted where a quote exists (cost_calibration in
alpha.db). It writes the comparison; it does not rewrite this model -- a change
to the numbers is a commit.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from . import config as acfg

COMPONENTS = ("spread", "slippage", "commission", "borrow", "roll", "funding", "fx")


@dataclass
class Fill:
    """A modelled fill. `price` is what the ledger books; `costs` the dollar
    cost of each component (all >= 0); `spread_cost` included in `price`."""
    price: float
    reference_price: float
    kind: str                          # bar_open | quote | bar_level
    costs: dict = field(default_factory=dict)
    quote: Optional[dict] = None

    @property
    def total(self) -> float:
        return sum(self.costs.values())


class CostModel:
    def __init__(self, cfg: Optional[dict] = None) -> None:
        self.cfg = cfg or acfg.costs()
        self.classes = dict(self.cfg.get("classes") or {})

    def spec(self, cost_class: str) -> dict:
        if cost_class not in self.classes:
            raise KeyError(f"cost class {cost_class!r} is not in config/alpha_costs.yaml")
        return self.classes[cost_class]

    def multiplier(self, cost_class: str, meta: Optional[dict] = None) -> float:
        m = (meta or {}).get("multiplier")
        return float(m if m is not None else self.spec(cost_class).get("multiplier") or 1)

    def half_spread(self, cost_class: str, price: float) -> float:
        """Half the class's fixed spread estimate, in price units."""
        est = self.spec(cost_class).get("spread_estimate") or {}
        if "abs" in est:
            return float(est["abs"]) / 2.0
        return abs(price) * float(est.get("bps", 0.0)) / 1e4 / 2.0

    def slippage_bps(self, cost_class: str, notional: float,
                     adv_notional: Optional[float]) -> float:
        s = self.spec(cost_class)
        if not adv_notional or adv_notional <= 0:
            return float(s.get("no_adv_slippage_bps", 0.0))
        impact = float(s.get("impact_bps", 0.0)) * math.sqrt(abs(notional) / adv_notional)
        return max(float(s.get("min_slippage_bps", 0.0)), impact)

    def commission(self, cost_class: str, qty: float, notional: float) -> float:
        s = self.spec(cost_class)
        c = (abs(notional) * float(s.get("commission_bps", 0.0)) / 1e4
             + abs(qty) * float(s.get("commission_per_unit", 0.0)))
        return max(float(s.get("commission_min", 0.0)), c)

    def fill(self, cost_class: str, side: int, qty: float, reference_price: float,
             quote: Optional[dict] = None, adv_notional: Optional[float] = None,
             meta: Optional[dict] = None, kind: str = "bar_open") -> Fill:
        """One fill. side +1 buys, -1 sells; qty > 0 in units."""
        if side not in (-1, 1):
            raise ValueError("side is +1 (buy) or -1 (sell)")
        mult = self.multiplier(cost_class, meta)
        if quote is not None:
            bid, ask = float(quote["bid"]), float(quote["ask"])
            mid = (bid + ask) / 2.0
            ref, half, kind = mid, (ask - bid) / 2.0, "quote"
        else:
            ref = float(reference_price)
            half = self.half_spread(cost_class, ref)
        notional = abs(qty) * ref * mult
        slip_bps = self.slippage_bps(cost_class, notional, adv_notional)
        slip = abs(ref) * slip_bps / 1e4
        price = ref + side * (half + slip)
        costs = {k: 0.0 for k in COMPONENTS}
        costs["spread"] = half * abs(qty) * mult
        costs["slippage"] = slip * abs(qty) * mult
        costs["commission"] = self.commission(cost_class, qty, notional)
        fxb = float(self.spec(cost_class).get("fx_bps", 0.0))
        if fxb and str((meta or {}).get("currency") or "USD").upper() != "USD":
            costs["fx"] = notional * fxb / 1e4
        return Fill(price=price, reference_price=ref, kind=kind, costs=costs,
                    quote=quote)

    def holding(self, cost_class: str, direction: int, notional: float,
                days: float) -> dict:
        """Borrow, roll and funding over `days` calendar days held."""
        s = self.spec(cost_class)
        days = max(0.0, float(days))
        out = {"borrow": 0.0, "roll": 0.0, "funding": 0.0}
        if direction < 0:
            out["borrow"] = abs(notional) * float(s.get("borrow_bps_per_year", 0.0)) / 1e4 * days / 365.0
        every = float(s.get("roll_every_days") or 0)
        if every:
            out["roll"] = abs(notional) * float(s.get("roll_bps", 0.0)) / 1e4 * math.floor(days / every)
        out["funding"] = abs(notional) * float(s.get("funding_bps_per_day", 0.0)) / 1e4 * days
        return out

    def modelled_spread_bps(self, cost_class: str, price: float) -> float:
        """The full spread the model assumes where no quote is stored, in bps --
        what the calibration compares a stored quote's spread against."""
        if not price:
            return float("nan")
        return 2.0 * self.half_spread(cost_class, price) / abs(price) * 1e4
