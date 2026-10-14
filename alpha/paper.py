"""
Simulated execution -- ledger-paper, never orders (X-1.5).

A signal is a row in alpha.db. It becomes a FILL only against a price the store
already holds, knowable at the run's as-of instant:

  * at the stored bid/ask where a quote exists after the signal (the
    prediction-market contract record, pm.bid/pm.ask; 6b's chain history and
    venue prices when they are stored) -- a buy at the ask, a sell at the bid;
  * otherwise at the NEXT stored bar's open after the signal, plus the cost
    model (alpha/costs.py): half the spread estimate, slippage, commission.

A signal is never filled at a price from before it, and never at the mid.

EXITS ARE EVALUATED BAR BY BAR, BRACKET-STYLE, every bar after the entry knowable
at the as-of instant, in order:
  1. a bar that OPENS through the stop (or the target) exits at its open -- the gap
     is the position's, not the model's;
  2. a bar whose range reaches the stop exits at the stop; whose range reaches the
     target, at the target -- and where one bar reaches both, THE STOP, because a
     daily bar does not say which came first and the conservative order is the
     one that costs;
  3. the engine's own exits(position, bar), at the bar's close;
  4. the time stop, at the close of the first bar on or after it;
  5. a governor stop or a lab halt, at the open of the first bar after it.
The entry bar itself is checked from step 2: its open is the entry.

MARKS DAILY from the store: each open position at the latest stored close, net of
its entry costs. A closed position is graded once (`grades`): gross P&L on the
reference prices, every modelled cost (both fills, and borrow, roll, funding over
the days held), net P&L and net return, and the regime key of its exit day.

Nothing here sends anything anywhere. tools/validate_alpha_no_orders.py holds
alpha/ to no order, gate, broker or network import.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import asdict
from typing import Callable, Optional

from altdata import session

from . import costs as costs_mod
from .engine import Bar, Engine, Signal

MAX_WAIT_BARS = 5


def decision_day(as_of: str) -> str:
    """The ET session date an as-of instant decides on."""
    return session.session_date(as_of)


def _days_between(a: str, b: str) -> int:
    return (dt.date.fromisoformat(b[:10]) - dt.date.fromisoformat(a[:10])).days


class Paper:
    def __init__(self, ledger, store, cost_model: Optional[costs_mod.CostModel] = None):
        self.ledger = ledger
        self.store = store
        self.costs = cost_model or costs_mod.CostModel()

    # -- prices -------------------------------------------------------------
    def bars(self, inst: dict, as_of: str, after: str = "",
             through: str = "9999") -> list[Bar]:
        """Bars strictly after `after` and on or before `through`, as-of."""
        if inst.get("meta", {}).get("intraday"):
            rows = self.store.intraday_bars(inst["meta"]["bars_id"], "5m",
                                            after, through, as_of)
            out = [Bar(day=str(r["observed_at"]), open=r["open"], high=r["high"],
                       low=r["low"], close=r["close"], volume=r.get("volume"))
                   for r in rows if str(r["observed_at"]) > after]
        else:
            rows = self.store.daily_bars(inst["key"], as_of, last=through)
            out = [Bar(**r) for r in rows if r["day"] > after]
        return out

    def adv_notional(self, inst: dict, as_of: str, through: str,
                     n: int = 20) -> Optional[float]:
        if inst.get("meta", {}).get("intraday"):
            return None
        rows = [r for r in self.store.daily_bars(inst["key"], as_of, last=through)
                if r.get("volume")][-n:]
        if not rows:
            return None
        mult = self.costs.multiplier(inst["cost_class"], inst.get("meta"))
        return sum(r["volume"] * r["close"] * mult for r in rows) / len(rows)

    # -- entry --------------------------------------------------------------
    def queue(self, engine_id: str, sig: Signal, size_fraction: float) -> int:
        """Write the signal (the blocklist refuses a restricted one first). It is
        filled by fill_pending() once a later price is stored."""
        inst = asdict(sig.instrument)
        tstop = None
        if sig.time_stop_days:
            tstop = (dt.date.fromisoformat(decision_day(sig.as_of))
                     + dt.timedelta(days=int(sig.time_stop_days))).isoformat()
        return self.ledger.add_signal(
            engine_id, sig.instrument.id, sig.direction, size_fraction, sig.as_of,
            strength=sig.strength, stop_price=sig.stop, target_price=sig.target,
            time_stop=tstop, params={"instrument": inst, **(sig.params or {})})

    def fill_pending(self, as_of: str,
                     capital_for: Callable[[str], float]) -> list[int]:
        """Fill every pending signal that now has a later stored price."""
        opened = []
        for s in self.ledger.pending_signals():
            inst = s["params"]["instrument"]
            day = decision_day(s["as_of"])
            mult = self.costs.multiplier(inst["cost_class"], inst.get("meta"))
            quote = None
            if inst.get("quote_keys"):
                q = self.store.quote(inst["quote_keys"][0], inst["quote_keys"][1],
                                     inst.get("store_instrument"), as_of)
                if q and q["available_at"] > s["as_of"]:
                    quote = q
            bars = [] if quote else self.bars(inst, as_of, after=day)
            if quote is None and not bars:
                waited = len([d for d in self._sessions_since(day, as_of)])
                if waited > MAX_WAIT_BARS:
                    self.ledger.set_signal_state(s["id"], "expired")
                    self.ledger.event("paper", "signal_expired", as_of, s["engine_id"],
                                      before={"signal": s["id"]},
                                      after={"state": "expired",
                                             "why": f"no stored price in {waited} sessions"})
                continue
            if quote is not None:
                ref, when = (quote["bid"] + quote["ask"]) / 2, quote["observed_at"]
            else:
                ref, when = bars[0].open, bars[0].day
            capital = float(capital_for(s["engine_id"]))
            qty = abs(s["size_fraction"]) * capital / (ref * mult) if ref else 0.0
            if qty <= 0:
                self.ledger.set_signal_state(s["id"], "cancelled")
                continue
            f = self.costs.fill(inst["cost_class"], s["direction"], qty, ref,
                                quote=quote,
                                adv_notional=self.adv_notional(inst, as_of, day),
                                meta=inst.get("meta"))
            fid = self._book_fill(s["engine_id"], s["id"], inst, "entry",
                                  s["direction"], qty, f, when, as_of)
            pid = self.ledger.open_position({
                "engine_id": s["engine_id"], "signal_id": s["id"],
                "instrument": inst["id"], "cost_class": inst["cost_class"],
                "direction": s["direction"], "qty": qty, "entry_fill_id": fid,
                "entry_price": f.reference_price, "stop_price": s["stop_price"],
                "target_price": s["target_price"], "time_stop": s["time_stop"],
                "opened_at": when, "as_of": as_of})
            self.ledger.link_fill(fid, pid)
            self.ledger.set_signal_state(s["id"], "filled")
            opened.append(pid)
        return opened

    def _sessions_since(self, day: str, as_of: str) -> list[str]:
        end = decision_day(as_of)
        d, out = dt.date.fromisoformat(day), []
        while d.isoformat() < end:
            d += dt.timedelta(days=1)
            if session.is_trading_session(d):
                out.append(d.isoformat())
        return out

    def _book_fill(self, engine_id: str, signal_id: Optional[int], inst: dict,
                   purpose: str, side: int, qty: float, f: costs_mod.Fill,
                   when: str, as_of: str) -> int:
        c = f.costs
        return self.ledger.add_fill({
            "signal_id": signal_id, "engine_id": engine_id,
            "instrument": inst["id"], "purpose": purpose, "side": side,
            "qty": qty, "fill_kind": f.kind, "reference_price": f.reference_price,
            "modelled_price": f.price, "stored_quote": f.quote,
            "cost_class": inst["cost_class"],
            "cost_spread": c.get("spread", 0.0), "cost_slippage": c.get("slippage", 0.0),
            "cost_commission": c.get("commission", 0.0), "cost_borrow": c.get("borrow", 0.0),
            "cost_roll": c.get("roll", 0.0), "cost_funding": c.get("funding", 0.0),
            "cost_fx": c.get("fx", 0.0), "cost_total": f.total,
            "filled_at": when, "as_of": as_of})

    # -- exits --------------------------------------------------------------
    def _inst(self, pos: dict) -> dict:
        s = self.ledger.one("SELECT params FROM signals WHERE id=?", (pos["signal_id"],))
        return json.loads(s["params"])["instrument"]

    @staticmethod
    def bracket(pos: dict, bar: Bar, entry_bar: bool) -> Optional[tuple[str, float, str]]:
        """(reason, price, kind) for this bar, or None. Stop before target."""
        d, stop, tgt = pos["direction"], pos.get("stop_price"), pos.get("target_price")
        if not entry_bar:
            if stop is not None and (bar.open - stop) * d <= 0:
                return "stop", bar.open, "bar_open"
            if tgt is not None and (bar.open - tgt) * d >= 0:
                return "target", bar.open, "bar_open"
        worst = bar.low if d > 0 else bar.high
        best = bar.high if d > 0 else bar.low
        if stop is not None and (worst - stop) * d <= 0:
            return "stop", stop, "bar_level"
        if tgt is not None and (best - tgt) * d >= 0:
            return "target", tgt, "bar_level"
        return None

    def evaluate_exits(self, as_of: str, engines: Optional[dict] = None,
                       force: Optional[dict] = None) -> list[int]:
        """Walk each open position's bars after its entry, knowable at `as_of`.
        `force` maps engine_id (or '*') -> (reason, since_as_of): a governor stop
        or a lab halt, which exits at the open of the first bar after it."""
        engines, force = engines or {}, force or {}
        closed = []
        for pos in self.ledger.open_positions():
            inst = self._inst(pos)
            entry_day = str(pos["opened_at"])
            bars = [b for b in self.bars(inst, as_of, after="")
                    if b.day >= entry_day]
            hit = None
            fz = force.get(pos["engine_id"]) or force.get("*")
            eng: Optional[Engine] = engines.get(pos["engine_id"])
            for b in bars:
                first = b.day == entry_day
                if fz and not first and b.day > decision_day(fz[1]):
                    hit = (fz[0], b.open, "bar_open", b)
                    break
                br = self.bracket(pos, b, first)
                if br:
                    hit = (*br, b)
                    break
                if eng is not None and not first:
                    why = eng.exits(pos, b)
                    if why:
                        hit = (str(why), b.close, "bar_level", b)
                        break
                if pos.get("time_stop") and b.day[:10] >= pos["time_stop"]:
                    hit = ("time", b.close, "bar_level", b)
                    break
            if hit:
                self._close(pos, inst, hit, as_of)
                closed.append(pos["id"])
        return closed

    def _close(self, pos: dict, inst: dict, hit: tuple, as_of: str) -> None:
        reason, level, kind, bar = hit
        f = self.costs.fill(inst["cost_class"], -pos["direction"], pos["qty"], level,
                            adv_notional=self.adv_notional(inst, as_of, bar.day[:10]),
                            meta=inst.get("meta"), kind=kind)
        mult = self.costs.multiplier(inst["cost_class"], inst.get("meta"))
        notional = pos["qty"] * pos["entry_price"] * mult
        held = self.costs.holding(inst["cost_class"], pos["direction"], notional,
                                  _days_between(pos["opened_at"], bar.day))
        f.costs.update({k: f.costs.get(k, 0.0) + v for k, v in held.items()})
        fid = self._book_fill(pos["engine_id"], pos["signal_id"], inst, "exit",
                              -pos["direction"], pos["qty"], f, bar.day, as_of)
        self.ledger.link_fill(fid, pos["id"])
        self.ledger.close_position(pos["id"], fid, f.reference_price, reason, bar.day)
        entry = self.ledger.one("SELECT cost_total FROM fills WHERE id=?",
                                (pos["entry_fill_id"],))
        gross = pos["direction"] * pos["qty"] * mult * (f.reference_price - pos["entry_price"])
        cost = float(entry["cost_total"]) + f.total
        net = gross - cost
        self.ledger.add_grade({
            "position_id": pos["id"], "engine_id": pos["engine_id"],
            "day": bar.day[:10], "gross_pnl": gross, "costs": cost, "net_pnl": net,
            "net_return": net / notional if notional else 0.0, "win": int(net > 0),
            "regime_key": self.store.regime_key(as_of, bar.day[:10]),
            "as_of": as_of})

    # -- marks --------------------------------------------------------------
    def mark(self, as_of: str) -> int:
        """Each open position at the latest stored close, net of entry costs."""
        n = 0
        for pos in self.ledger.open_positions():
            inst = self._inst(pos)
            bars = self.bars(inst, as_of, after="", through=decision_day(as_of)
                             if not inst.get("meta", {}).get("intraday") else "9999")
            if not bars:
                continue
            b = bars[-1]
            mult = self.costs.multiplier(inst["cost_class"], inst.get("meta"))
            entry = self.ledger.one("SELECT cost_total FROM fills WHERE id=?",
                                    (pos["entry_fill_id"],))
            unreal = (pos["direction"] * pos["qty"] * mult * (b.close - pos["entry_price"])
                      - float(entry["cost_total"]))
            self.ledger.add_mark(pos["id"], pos["engine_id"], b.day[:10], b.close,
                                 unreal, as_of)
            n += 1
        return n
