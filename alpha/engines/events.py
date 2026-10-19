"""
Engine 4 -- scheduled events (X-3.1; the brief's roster item 4), the engine half.
The base rates come first (alpha/event_rates.py); each setup here is its own
registered engine (config/alpha_engines.yaml) and its own pre-registered
hypothesis (alpha/research/roster-2026-10-17-x3.yaml, registered by manifest):

  events_macro   CPI and payrolls: SPY's open-to-close in the first session the
                 nightly loop can enter after the print became knowable, long or
                 short by the sign of that surprise bucket's mean in the fit
                 window (a bucket with fewer than `min_bucket` events trades
                 nothing). The surprise is the NAIVE one (alpha_events.yaml).
  events_fomc    the same after an FOMC statement, bucketed by stored
                 positioning (no FOMC surprise is stored)
  events_pead    earnings in the 29-name universe: long a positive surprise, short
                 a negative one, from the close of the first session the loop can
                 enter to 20 sessions later -- the post-announcement drift, a
                 fixed rule with nothing fitted
  events_crush   the volatility crush after the print: a DATA GAP -- no tradable
                 volatility instrument is stored (no option quotes per strike, no
                 volatility ETP), so its coverage check says so and nothing runs

Every row is point in time: decided at the first nightly loop after its inputs
were all knowable, traded in the next session; an event whose inputs were
ingested more than five sessions after it (a backfill) is left out. Costs: the
lab's cost model, a round trip at the engine's own capital. Promotion is the
gate's (X-1.6, X-2.6), never this module's; it writes nothing itself.
"""

from __future__ import annotations

import statistics
from typing import Optional

from altdata import session

from .. import blocklist, event_rates, pit
from .. import config as acfg
from .. import validate as av
from ..engine import Engine, Instrument, Signal

KINDS = ("macro", "fomc", "pead", "crush")
FIT_EVENTS = 60                        # alpha/research/workbench.py ENGINE_WINDOWS daily


def round_trip(cm, cost_class: str, px: float, notional: float) -> float:
    """A round trip's cost as a fraction of notional: spread, slippage and the
    commission (with its minimum), each way."""
    if not px or notional <= 0:
        return 0.0
    one = (cm.half_spread(cost_class, px) / px
           + cm.slippage_bps(cost_class, notional, None) / 1e4
           + cm.commission(cost_class, notional / px, notional) / notional)
    return 2.0 * one


class EventEngine(Engine):
    family = "events"
    horizon = "daily"
    cost_class = "etf"
    validated_ranges: dict = {}
    grid_size = 1

    def __init__(self, params: Optional[dict] = None) -> None:
        super().__init__(params)
        self.kind = str(self.params.get("kind", "macro"))
        if self.kind not in KINDS:
            raise ValueError(f"an event engine's kind is one of {KINDS}")
        if self.kind == "pead":
            self.cost_class = "single_name"
        self.cfg = event_rates.load_config()

    # -- the interface ------------------------------------------------------
    def symbols(self) -> list[str]:
        if self.kind == "pead":
            return [s for s in (self.cfg.get("earnings") or {}).get("universe") or []
                    if blocklist.check(s) is None]
        return [self.cfg["price"]["symbol"]]

    def _instrument(self, sym: str) -> Instrument:
        from .. import rules                                    # noqa: PLC0415
        return Instrument(id=sym, key=rules.price_symbols()[sym.upper()],
                          cost_class=self.cost_class,
                          meta={"close_only": self.kind == "pead",
                                "fill_at": "close" if self.kind == "pead" else "open"})

    def universe(self) -> list[Instrument]:
        return [self._instrument(s) for s in self.symbols()]

    def capital(self) -> float:
        return float(acfg.settings().get("notional_capital") or 100000) * \
            float(self.min_size or 0.01)

    def signal(self, as_of: str, store) -> list[Signal]:
        """Tonight's decisions: the events whose decision day is today, sized
        from the rows decided before it (the same fit the walk-forward uses)."""
        if self.kind == "crush":
            return []
        today = session.session_date(as_of)
        rows = self.refit_rows(store, as_of)
        past = [r for r in rows if r["decided_day"] < today]
        now = [r for r in rows if r["decided_day"] == today]
        if not now:
            return []
        p = self.strategy().fit(past)
        out = []
        for r in now:
            d = r["sign"] if self.kind == "pead" else (p.get("signs") or {}).get(r["bucket"], 0)
            if not d:
                continue
            out.append(Signal(instrument=self._instrument(r["symbol"]), direction=int(d),
                              as_of=as_of, strength=1.0 / len(now),
                              params={"time_stop_date": r["exit_day"],
                                      "event": r.get("event"), "bucket": r["bucket"]}))
        return out

    def size(self, signal: Signal, risk_budget: float) -> float:
        return float(signal.strength)

    def exits(self, position: dict, bar) -> Optional[str]:
        return None

    # -- the harness's hooks ------------------------------------------------
    def refit_rows(self, store, as_of: str) -> list[dict]:
        if self.kind == "crush":
            return []
        if self.kind == "pead":
            return self._pead_rows(store, as_of)
        names = ("cpi", "payrolls") if self.kind == "macro" else ("fomc",)
        col = "surprise_bucket" if self.kind == "macro" else "positioning_bucket"
        ev = event_rates.macro_rows(store, self.cfg, as_of)
        rows = []
        for n in names:
            for r in ev.get(n) or []:
                if r["stale"] or r["next_session_drift_pct"] is None:
                    continue
                if r["trade_day"] > session.session_date(as_of):
                    continue
                rows.append({"day": r["trade_day"], "decided_at": r["decided_at"],
                             "decided_day": pit.et_date(r["decided_at"]),
                             "available_at": r["available_at"], "event": n,
                             "symbol": self.cfg["price"]["symbol"], "bucket": r[col],
                             "ret": r["next_session_drift_pct"] / 100.0,
                             "exit_day": r["trade_day"],
                             "price": r.get("trade_open")})
        return sorted(rows, key=lambda x: x["day"])

    def _pead_rows(self, store, as_of: str) -> list[dict]:
        hold = int(((self.cfg.get("engine") or {}).get("hold_sessions") or {})
                   .get("pead", 20))
        last = session.session_date(as_of)
        series: dict[str, pit.Series] = {}
        rows = []
        for r in event_rates.earnings_rows(store, self.cfg, as_of):
            if r["stale"] or not r["surprise_pct"] or r["symbol"] not in self.symbols():
                continue
            s = series.setdefault(r["key"], pit.Series(store, r["key"]))
            entry_day = r["trade_day"]
            exit_day = pit.next_session(entry_day, hold)
            if exit_day > last:
                continue
            a, b = s.latest(entry_day), s.latest(exit_day)
            if not a or not b:
                continue
            sign = 1 if r["surprise_pct"] > 0 else -1
            rows.append({"day": entry_day, "decided_at": r["decided_at"],
                         "decided_day": pit.et_date(r["decided_at"]),
                         "available_at": r["available_at"], "symbol": r["symbol"],
                         "bucket": "pead", "sign": sign, "ret": sign * (b / a - 1),
                         "exit_day": exit_day, "price": a})
        return sorted(rows, key=lambda x: (x["day"], x["symbol"]))

    def _returns(self, rows: list[dict], p: dict) -> list[float]:
        from ..costs import CostModel                           # noqa: PLC0415
        cm = CostModel()
        cap = self.capital()
        out = []
        for r in rows:
            if self.kind == "pead":
                ret = r["ret"]
            else:
                d = (p.get("signs") or {}).get(r["bucket"], 0)
                if not d:
                    continue
                ret = d * r["ret"]
            out.append(ret - round_trip(cm, self.cost_class, r.get("price") or 0.0, cap))
        return out

    def strategy(self) -> av.Strategy:
        mb = int((self.cfg.get("engine") or {}).get("min_bucket", 6))

        def fit(rows: list[dict]) -> dict:
            if self.kind == "pead":
                return {}
            by: dict[str, list[float]] = {}
            for r in rows:
                by.setdefault(r["bucket"], []).append(r["ret"])
            return {"signs": {b: (1 if statistics.fmean(x) > 0 else -1)
                              for b, x in by.items()
                              if len(x) >= mb and b != event_rates.AWAITING
                              and statistics.fmean(x) != 0}}
        return av.Strategy(family=self.family, horizon=self.horizon, fit=fit,
                           returns=lambda rows, p: self._returns(rows, p))

    def coverage(self, store, as_of: str) -> dict:
        if self.kind == "crush":
            return {"n": 0, "need": None, "ok": False, "wait": False,
                    "why": ("a data gap: no tradable volatility instrument is stored -- "
                            "the crush needs option quotes per strike (6b's chain "
                            "history) or a volatility ETP; its base rate is in "
                            "event_base_rates (vix_change_pts)")}
        rows = self.refit_rows(store, as_of)
        need = acfg.min_signals(self.horizon)
        ok = len(rows) >= need + FIT_EVENTS
        return {"n": len(rows), "need": need, "ok": ok, "wait": not ok,
                "why": (f"insufficient history: {len(rows)} events with knowable inputs; "
                        f"the harness needs {need} out-of-sample after a "
                        f"{FIT_EVENTS}-event fit")}
