"""
Engine 1 -- the dealer-conditioned, defined-risk volatility risk premium (X-2.1;
the brief's roster item 1). THE COVERAGE CHECK COMES FIRST: until the store can
reach the minimum sample, the engine is a DATA GAP, registered and said so.

What it needs, stored and point-in-time:
  * option quotes -- bid and ask per strike and expiry -- for SPY and QQQ at the
    daily and weekly expiries (6b's chain history, from the week of 19 Oct, or
    FlashAlpha's historical quotes where the plan serves them), to price an
    iron condor or a vertical at the executable side;
  * the dealer regime: the gamma sign and level, vanna and charm into expiry
    (the exposure.* series);
  * realised volatility (the stored closes) against the implied.

coverage() counts the sessions on which ALL of that is stored, against
min_signals. It reads the store only -- the chain files the EOD pass keeps on
disk are not the store -- and decides nothing else. The engine trades nothing:
signal() returns no signal until a coded pricer replaces this module, which the
research sitting queues once coverage() passes.
"""

from __future__ import annotations

from typing import Optional

from .. import config as acfg
from ..engine import Engine, Instrument, Signal

OPTION_KEY_PREFIXES = ("option.", "options.", "chain.", "opt.", "flashalpha.quote")
DEALER_KEYS = ("exposure.net_gex", "exposure.gamma_flip")
UNDERLYINGS = ("SPY", "QQQ")


def _sessions(store, prefixes: tuple, instrument: Optional[str] = None) -> set:
    q = ("SELECT DISTINCT substr(observed_at,1,10) FROM observations WHERE ("
         + " OR ".join("registry_key LIKE ?" for _ in prefixes) + ")")
    args: list = [p + "%" for p in prefixes]
    if instrument:
        q += " AND (instrument = ? OR instrument LIKE ?)"
        args += [instrument, instrument + " %"]
    return {r[0] for r in store.conn.execute(q, args).fetchall()}


class DealerVRPEngine(Engine):
    family = "vrp"
    horizon = "daily"
    cost_class = "index_option"

    def universe(self) -> list[Instrument]:
        return []

    def signal(self, as_of: str, store) -> list[Signal]:
        return []

    def size(self, signal: Signal, risk_budget: float) -> float:
        return 0.0

    def exits(self, position: dict, bar) -> Optional[str]:
        return None

    def coverage(self, store, as_of: str) -> dict:
        need = acfg.min_signals(self.horizon)
        dealer = _sessions(store, DEALER_KEYS)
        per = {}
        for u in UNDERLYINGS:
            quotes = _sessions(store, OPTION_KEY_PREFIXES, u)
            per[u] = {"option_quote_sessions": len(quotes),
                      "dealer_sessions": len(dealer), "both": len(quotes & dealer)}
        n = sum(v["both"] for v in per.values())
        return {"n": n, "need": need, "ok": n >= need, "per_underlying": per,
                "why": ("stored sessions with option quotes AND the dealer series: "
                        + ", ".join(f"{u} {v['both']} (quotes "
                                    f"{v['option_quote_sessions']}, dealer "
                                    f"{v['dealer_sessions']})" for u, v in per.items())
                        + f"; the harness needs {need} independent signals. A data gap "
                          f"until 6b's chain history or FlashAlpha's historical quotes "
                          f"are stored")}
