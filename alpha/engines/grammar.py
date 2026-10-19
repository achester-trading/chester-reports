"""
A promoted grammar rule, traded in paper (X-2.6).

A hypothesis whose rule is in the grammar (alpha/rules.py) and that passed the
harness is promoted by the loop on its own authority: written to `engines` at
min_size, and traded from the next nightly loop by this one engine class, with
the rule as its parameters. No code is written for it, and the rule is the one
that was registered and tested -- read from the register, never edited here.

THE REGISTER NAMES IT. config/alpha_engines.yaml is the only place a CODED
engine is named; a promoted grammar rule is named by its register id (HYP-xxxx)
in alpha.db, because promotion is the loop's (X-2.6) and the loop cannot commit
a config file. The nightly loop loads both.

PAPER FROM THE RULE, AS THE BACKTEST READ IT:
  * the rule decides at the nightly loop's instant on its cadence day, reading
    only what the store knows then (the same evaluation as the backtest);
  * next_open fills at the next stored open; next_close at the next close;
    this_close is decided the evening before and filled at the next close;
    a close-only instrument fills and exits on its closes;
  * the time stop is the session date the backtest would exit on;
  * a stop or target in pct, R or ATR is set from the decision day's close (the
    entry price is not yet known when the signal is written) -- the one reading
    the paper book adds, declared here;
  * a pair is two signals, one a leg, sized by the leg weights;
  * one position at a time, and the rule's cooldown, from the ledger.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from altdata import session

from .. import rules
from ..engine import Engine, Instrument, Signal


def _sessions_after(day: str, n: int) -> str:
    d, k = dt.date.fromisoformat(day), 0
    while k < n:
        d += dt.timedelta(days=1)
        if session.is_trading_session(d):
            k += 1
    return d.isoformat()


class GrammarEngine(Engine):
    family = "grammar"
    horizon = "daily"
    cost_class = "etf"

    def __init__(self, params: Optional[dict] = None) -> None:
        super().__init__(params)
        self.rule = dict(self.params["rule"])
        self.cmp = rules.compile_rule(self.rule)
        self.horizon = self.cmp.horizon
        self.ledger = None

    def bind_ledger(self, ledger) -> None:
        """The nightly loop hands the ledger in, read for this engine's own open
        positions, pending signals and last signal (one at a time, the cooldown)."""
        self.ledger = ledger

    def _instrument(self, sym: str) -> Instrument:
        close_only = sym not in rules.ohlc_symbols()
        fill_at = "close" if (self.rule["entry"] != "next_open" or close_only) else "open"
        return Instrument(id=sym, key=rules.resolve(sym),
                          cost_class=rules._cost_class(self.cmp, sym),
                          meta={"close_only": close_only, "fill_at": fill_at})

    def universe(self) -> list[Instrument]:
        return [self._instrument(s) for s in self.cmp.instruments]

    def _busy(self, day: str) -> bool:
        if self.ledger is None:
            return False
        if self.ledger.open_positions(self.engine_id) or \
                self.ledger.pending_signals(self.engine_id):
            return True
        # As the backtest: no new trigger on the session a position exits.
        if self.ledger.one("SELECT 1 AS x FROM positions WHERE engine_id=? AND "
                           "substr(closed_at,1,10)>=?", (self.engine_id, day)):
            return True
        cd = int(self.rule.get("cooldown") or 0)
        if cd:
            last = self.ledger.one("SELECT MAX(as_of) AS a FROM signals WHERE "
                                   "engine_id=?", (self.engine_id,))
            if last and last["a"]:
                if day <= _sessions_after(session.session_date(last["a"]), cd):
                    return True
        return False

    def signal(self, as_of: str, store) -> list[Signal]:
        day = session.session_date(as_of)
        data = rules.Data(store)
        entry = self.rule["entry"]
        decide_day = day
        if entry == "this_close":
            decide_day = _sessions_after(day, 1)
        if decide_day not in rules.cadence_days(self.cmp, data, decide_day, decide_day):
            return []
        if self._busy(day):
            return []
        ok, _, _ = rules._signal(self.cmp, data, decide_day, as_of, self.rule["trigger"])
        if not ok:
            return []
        # grammar v2: every `when` item read as knowable now, else no signal
        if self.cmp.when and not rules.when_ok(self.cmp, data, decide_day, as_of)[0]:
            return []
        d = self.rule["direction"]
        if isinstance(d, dict):
            hit, _, _ = rules.holds(d["if"], data, decide_day, as_of)
            if hit is None:
                return []
            direction = 1 if (d["then"] if hit else d["else"]) == "long" else -1
        else:
            direction = 1 if d == "long" else -1
        ex = self.rule["exits"]
        t = int(ex["time"])
        first = _sessions_after(day, 1)
        tstop = _sessions_after(first, t - 1) if entry == "next_open" else \
            _sessions_after(first, t)
        ins = self.rule["instrument"]
        if isinstance(ins, dict):
            pr = ins["pair"]
            legs = [(str(pr["long"]).upper(), direction), (str(pr["short"]).upper(), -direction)]
            weights = {"long": 0.5, "short": 0.5}
            if pr.get("weight") == "vol_matched":
                vl = rules._vol(data.series(rules.resolve(legs[0][0])), day, as_of, int(pr["n"]))
                vs = rules._vol(data.series(rules.resolve(legs[1][0])), day, as_of, int(pr["n"]))
                if not vl or not vs:
                    return []
                weights = {"long": (1 / vl) / (1 / vl + 1 / vs),
                           "short": (1 / vs) / (1 / vl + 1 / vs)}
            return [Signal(instrument=self._instrument(legs[0][0]), direction=legs[0][1],
                           as_of=as_of, strength=weights["long"],
                           params={"time_stop_date": tstop, "leg": "long"}),
                    Signal(instrument=self._instrument(legs[1][0]), direction=legs[1][1],
                           as_of=as_of, strength=weights["short"],
                           params={"time_stop_date": tstop, "leg": "short"})]
        sym = str(ins).upper()
        p = rules.Prices(data, sym)
        last = p.close.known(day, as_of, 1)
        if not last:
            return []
        ref = last[-1][1]
        stop, target, _ = rules._levels(self.cmp, data, p, day, as_of, ref, direction, ex)
        return [Signal(instrument=self._instrument(sym), direction=direction,
                       as_of=as_of, stop=stop, target=target,
                       params={"time_stop_date": tstop})]

    def size(self, signal: Signal, risk_budget: float) -> float:
        """The engine's whole capital on one instrument, or split by the pair's
        leg weights."""
        return float(signal.strength or 1.0)

    def exits(self, position: dict, bar) -> Optional[str]:
        return None
