"""
Engine 2 -- cross-asset trend (X-2.2; the brief's roster item 2).

Two sleeves, each its own registered engine (config/alpha_engines.yaml), over
the stored price basket -- ETFs, futures, the crypto set, the FX pairs and the
single names the price feed keeps; the volatility indices and index levels,
which cannot be traded, and anything the blocklist names are left out:

  trend_ts   TIME-SERIES momentum: each instrument's blended sign of its 12-1,
             6-1 and 3-1 month returns (231, 105 and 42 sessions, each ending
             21 sessions back), long or short, weighted so each name targets the
             sleeve's volatility share; the `max_names` strongest |scores| kept.
  trend_xs   CROSS-SECTIONAL momentum: the blended 12-1/6-1/3-1 return ranked
             across the basket, long the top `top_frac`, short the bottom,
             equal risk.

Both are VOLATILITY-TARGETED per sleeve (`vol_target`, annual) on each name's
realised volatility over `vol_window` sessions (floored at `vol_floor`, 2% a
year, so a quiet series is never leverage), each name capped at `name_cap` (a
quarter of the sleeve) and the gross at 1 (no leverage). WEEKLY REBALANCE: decided at the Friday close (the nightly loop's
17:40 instant, the last session of the ISO week), filled at the next session's
close; each position's time stop is the session after the NEXT rebalance, so
the book rolls close to close. Costs: the lab's cost model, per name, at the
engine's own capital (its min_size of the lab's notional) -- honest about what
a small paper book pays.

THE RE-FIT HOOKS (X-2.4): strategy() fits `vol_window` and the sleeve's
breadth (`max_names` or `top_frac`) on a small declared grid; refit_rows() is
one row per rebalance week, point-in-time, carrying every grid value's
features so the walk-forward can test any of them without looking ahead.
"""

from __future__ import annotations

import datetime as dt
import math
import statistics
from typing import Optional

from altdata import observations, session

from .. import blocklist, rules
from .. import config as acfg
from .. import validate as av
from ..engine import Engine, Instrument, Signal

LOOKBACKS = (231, 105, 42)
SKIP = 21
GRID_VOL = (40, 60, 120)
GRID_NAMES = (10, 20, 30)
GRID_FRAC = (0.1, 0.2, 0.3)
NOT_TRADABLE = ("DX-Y.NYB",)


def tradable(sym: str) -> bool:
    if sym.startswith("^") or sym in NOT_TRADABLE:
        return False
    return blocklist.check(sym) is None


def cost_class(sym: str) -> str:
    if sym.endswith("=F"):
        return "future"
    if sym.endswith("=X"):
        return "fx_pair"
    if sym in ("BTC-USD", "ETH-USD"):
        return "perp"
    return "etf"


def rebalance_days(first: str, last: str) -> list[str]:
    """The last session of each ISO week in [first, last]."""
    d, d1, out = dt.date.fromisoformat(first), dt.date.fromisoformat(last), []
    sessions_: list[dt.date] = []
    while d <= d1:
        if session.is_trading_session(d):
            sessions_.append(d)
        d += dt.timedelta(days=1)
    for i, s in enumerate(sessions_):
        nxt = sessions_[i + 1] if i + 1 < len(sessions_) else None
        if nxt is None:
            if s.weekday() == 4:
                out.append(s.isoformat())
        elif nxt.isocalendar()[:2] != s.isocalendar()[:2]:
            out.append(s.isoformat())
    return out


def next_session(day: str, n: int = 1) -> str:
    d, k = dt.date.fromisoformat(day), 0
    while k < n:
        d += dt.timedelta(days=1)
        if session.is_trading_session(d):
            k += 1
    return d.isoformat()


def features(data: rules.Data, sym: str, day: str, t: str) -> Optional[dict]:
    """One name's point-in-time features at the decision (day, t)."""
    s = data.series(rules.resolve(sym))
    need = LOOKBACKS[0] + SKIP + 1
    xs = s.known(day, t, max(need, max(GRID_VOL) + 1))
    if len(xs) < need or xs[-1][0] < (dt.date.fromisoformat(day)
                                      - dt.timedelta(days=7)).isoformat():
        return None
    px = [x[1] for x in xs]
    end = px[-1 - SKIP]
    rets = [end / px[-1 - SKIP - lb] - 1 for lb in LOOKBACKS if px[-1 - SKIP - lb]]
    if len(rets) != len(LOOKBACKS):
        return None
    daily = [px[i] / px[i - 1] - 1 for i in range(1, len(px)) if px[i - 1]]
    vols = {}
    for w in GRID_VOL:
        seg = daily[-w:]
        vols[w] = statistics.stdev(seg) * math.sqrt(252) if len(seg) > 2 else None
    return {"score": statistics.fmean(1.0 if r > 0 else -1.0 for r in rets),
            "mom": statistics.fmean(rets), "vols": vols, "close": px[-1],
            "avail": max(x[2] for x in xs)}


def weights(feats: dict[str, dict], sleeve: str, p: dict) -> dict[str, float]:
    """The sleeve's target weights (fractions of its capital, signed)."""
    vw = int(p.get("vol_window", 60))
    target = float(p.get("vol_target", 0.10))
    floor = float(p.get("vol_floor", 0.02))       # a quiet series is not leverage
    cap = float(p.get("name_cap", 0.25))          # no one name above a quarter
    live = {k: {**f, "vols": {**f["vols"], vw: max(floor, f["vols"][vw])}}
            for k, f in feats.items() if f and f["vols"].get(vw) is not None}
    if not live:
        return {}
    w: dict[str, float] = {}
    if sleeve == "ts":
        n = int(p.get("max_names", 20))
        keep = sorted(live, key=lambda k: -abs(live[k]["score"]))[:n]
        keep = [k for k in keep if live[k]["score"] != 0]
        if not keep:
            return {}
        per = target / math.sqrt(len(keep))
        for k in keep:
            w[k] = live[k]["score"] * per / live[k]["vols"][vw]
    else:
        frac = float(p.get("top_frac", 0.2))
        ranked = sorted(live, key=lambda k: live[k]["mom"])
        m = max(1, int(len(ranked) * frac))
        if len(ranked) < 2 * m:
            return {}
        per = target / math.sqrt(2 * m)
        for k in ranked[-m:]:
            w[k] = per / live[k]["vols"][vw]
        for k in ranked[:m]:
            w[k] = -per / live[k]["vols"][vw]
    w = {k: max(-cap, min(cap, v)) for k, v in w.items()}
    gross = sum(abs(v) for v in w.values())
    if gross > 1.0:
        w = {k: v / gross for k, v in w.items()}
    return w


class TrendEngine(Engine):
    family = "trend"
    horizon = "weekly"
    cost_class = "etf"
    validated_ranges: dict = {}
    refit_test_rows = 40
    grid_size = len(GRID_VOL) * 3          # the fitting grid, counted on a first run

    def __init__(self, params: Optional[dict] = None) -> None:
        super().__init__(params)
        self.sleeve = str(self.params.get("sleeve", "ts"))
        if self.sleeve not in ("ts", "xs"):
            raise ValueError("a trend sleeve is ts or xs")

    def symbols(self) -> list[str]:
        return [s for s in sorted(rules.price_symbols()) if tradable(s)]

    def _instrument(self, sym: str) -> Instrument:
        return Instrument(id=sym, key=rules.resolve(sym), cost_class=cost_class(sym),
                          meta={"close_only": sym not in rules.ohlc_symbols(),
                                "fill_at": "close"})

    def universe(self) -> list[Instrument]:
        return [self._instrument(s) for s in self.symbols()]

    def _feats(self, store, day: str, t: str, data=None) -> dict[str, dict]:
        data = data or rules.Data(store)
        out = {}
        for s in self.symbols():
            if not data.series(rules.resolve(s)).days:     # loaded once per Data
                continue
            f = features(data, s, day, t)
            if f:
                out[s] = f
        return out

    def signal(self, as_of: str, store) -> list[Signal]:
        day = session.session_date(as_of)
        if day not in rebalance_days(day, day):
            return []
        w = weights(self._feats(store, day, as_of), self.sleeve, self.params)
        nxt = rebalance_days(next_session(day), next_session(day, 10))
        hold_to = next_session(nxt[0]) if nxt else next_session(day, 6)
        return [Signal(instrument=self._instrument(s), direction=1 if v > 0 else -1,
                       as_of=as_of, strength=abs(v),
                       params={"time_stop_date": hold_to, "weight": v})
                for s, v in sorted(w.items()) if abs(v) > 1e-6]

    def size(self, signal: Signal, risk_budget: float) -> float:
        return float(signal.strength)

    def exits(self, position: dict, bar) -> Optional[str]:
        return None

    # -- the harness's and the weekly re-fit's hooks -------------------------
    def capital(self) -> float:
        return float(acfg.settings().get("notional_capital") or 100000) * \
            float(self.min_size or 0.01)

    def refit_rows(self, store, as_of: str, first: Optional[str] = None) -> list[dict]:
        """One row per rebalance week: every name's features at the decision,
        and its return from the next session's close to the session after the
        next rebalance (the paper book's roll). Point-in-time at each decision."""
        data = rules.Data(store)
        last = session.session_date(as_of)
        spy = data.series(rules.resolve("SPY")).days
        first = first or (spy[LOOKBACKS[0] + SKIP + 5] if len(spy) > 300 else last)
        days = rebalance_days(first, last)
        rows = []
        for i in range(len(days) - 1):
            d = days[i]
            t = rules.decision_instant(d, "next_close")
            fe = self._feats(store, d, t, data)
            e0, e1 = next_session(d), next_session(days[i + 1])
            nxt = {}
            for s in fe:
                ser = data.series(rules.resolve(s))
                a, b = ser.first(e0), ser.first(e1)
                if a and b:
                    nxt[s] = b / a - 1
            if not fe or not nxt:
                continue
            rows.append({"day": d, "decided_at": t,
                         "available_at": max(f["avail"] for f in fe.values()),
                         "feats": fe, "next": nxt,
                         "days_held": (dt.date.fromisoformat(e1)
                                       - dt.date.fromisoformat(e0)).days})
        return rows

    def _returns(self, rows: list[dict], p: dict) -> list[float]:
        """The sleeve's net weekly return per rebalance, as a fraction of its
        capital: gross, less each name's one-way cost on its turnover at the
        notional it actually trades (spread, slippage, the commission and its
        minimum), less borrow on the shorts over the week held."""
        from ..costs import CostModel                           # noqa: PLC0415
        cm = CostModel()
        cap = self.capital()
        out, prev = [], {}
        for r in rows:
            w = weights(r["feats"], self.sleeve, {**self.params, **p})
            gross = sum(v * r["next"].get(k, 0.0) for k, v in w.items())
            cost = 0.0
            for k in set(w) | set(prev):
                turn = abs(w.get(k, 0.0) - prev.get(k, 0.0))
                f = r["feats"].get(k)
                if turn <= 0 or not f or not f["close"]:
                    continue
                cc, px = cost_class(k), f["close"]
                notional = cap * turn
                one_way = (cm.half_spread(cc, px) / px
                           + cm.slippage_bps(cc, notional, None) / 1e4
                           + cm.commission(cc, notional / px, notional) / notional)
                cost += turn * one_way
            for k, v in w.items():
                if v < 0:
                    cost += abs(v) * sum(cm.holding(cost_class(k), -1, 1.0,
                                                    r["days_held"]).values())
            out.append(gross - cost)
            prev = w
        return out

    def strategy(self) -> av.Strategy:
        grid_b = GRID_NAMES if self.sleeve == "ts" else GRID_FRAC
        key_b = "max_names" if self.sleeve == "ts" else "top_frac"

        def fit(rows: list[dict]) -> dict:
            best, best_sr = None, -math.inf
            for vw in GRID_VOL:
                for b in grid_b:
                    p = {"vol_window": vw, key_b: b}
                    x = self._returns(rows, p)
                    if len(x) < 3:
                        continue
                    sd = statistics.stdev(x)
                    sr = statistics.fmean(x) / sd if sd else -math.inf
                    if sr > best_sr:
                        best, best_sr = p, sr
            return best or {"vol_window": 60, key_b: grid_b[1]}
        return av.Strategy(family=self.family, horizon=self.horizon, fit=fit,
                           returns=lambda rows, p: self._returns(rows, p),
                           declared_ranges={"vol_window": [min(GRID_VOL), max(GRID_VOL)],
                                            key_b: [min(grid_b), max(grid_b)]})

    def coverage(self, store, as_of: str) -> dict:
        rows = self.refit_rows(store, as_of)
        need = acfg.min_signals(self.horizon)
        return {"n": len(rows), "need": need, "ok": len(rows) >= need + 52,
                "why": f"{len(rows)} rebalance weeks with features (the harness needs "
                       f"{need} out-of-sample after a year's fit)"}
