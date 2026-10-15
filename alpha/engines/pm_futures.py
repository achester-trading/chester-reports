"""
Engine 3 -- prediction markets against fed funds futures (X-2.3; the brief's
roster item 3). Depends on the W-1.1 contract record (pm.bid, pm.ask, pm.volume,
pm.market), which is merged.

For each contract config/alpha_pm_map.yaml maps to an FOMC meeting and outcome,
and the operator has CONFIRMED (`confirmed: true`, ruling 18 -- a drafted entry
from alpha/pm_map.py is confirmed: false and is ignored):

  futures   the outcome's probability implied by the stored fed funds futures
            (altdata.fed_funds.implied_path: the move to each meeting, as the
            probability of a 25 bp move in its direction, from the stored
            contract prices -- computed here, never fetched)
  venue     the contract's stored bid and ask; their mid is the venue's odds
  enter     when |venue mid - futures| exceeds the contract's THRESHOLD, set
            from its own stored history (a quantile of the gap, never below
            min_points), and its stored volume clears the liquidity floor: buy
            YES at the ask when the venue is cheap, sell YES at the bid when it
            is rich -- the executable side, never the mid
  exit      convergence inside the band (the engine's exits), else held to the
            meeting: graded on the contract's last stored price

coverage() first: the sample the store actually holds -- contracts mapped,
sessions with a quote and a futures path -- against min_signals.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Optional

import yaml

from altdata import fed_funds, session

from .. import config as acfg
from ..engine import Engine, Instrument, Signal

MAP_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "alpha_pm_map.yaml"


def mapping(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or MAP_PATH).read_text(encoding="utf-8")) or {}


def implied(prices: dict, meeting: str, outcome: str, today: str) -> Optional[float]:
    """The futures-implied probability of `outcome` at `meeting`, in points."""
    res = fed_funds.implied_path(prices, fed_funds.meeting_days(),
                                 dt.date.fromisoformat(today))
    for r in res.get("meetings") or []:
        if r["meeting"] == meeting:
            p = float(r["move_probability_25bp"])
            if outcome == "hold":
                return 100.0 * (1.0 - p)
            return 100.0 * (p if r["direction"] == outcome else 0.0)
    return None


def points(x: float) -> float:
    """A stored probability in points: 0..1 is scaled, 0..100 is kept."""
    return 100.0 * x if abs(x) <= 1.0 else x


class PredictionFuturesEngine(Engine):
    family = "pm-futures"
    horizon = "daily"
    cost_class = "prediction_market"

    def __init__(self, params: Optional[dict] = None) -> None:
        super().__init__(params)
        self.map_path = self.params.get("map_path")

    def cfg(self) -> dict:
        return mapping(Path(self.map_path) if self.map_path else None)

    def contracts(self) -> list[dict]:
        """Only the entries the operator confirmed (ruling 18): a drafted line
        (alpha/pm_map.py, confirmed: false) maps nothing and trades nothing."""
        return [c for c in (self.cfg().get("contracts") or [])
                if c.get("confirmed") is True]

    def universe(self) -> list[Instrument]:
        return [self._instrument(c) for c in self.contracts()]

    def _instrument(self, c: dict) -> Instrument:
        return Instrument(id=str(c["contract"]), key="pm.probability",
                          cost_class="prediction_market",
                          quote_keys=("pm.bid", "pm.ask"),
                          store_instrument=str(c["contract"]),
                          meta={"close_only": True, "meeting": c["meeting"],
                                "outcome": c["outcome"]})

    def gap_history(self, store, c: dict, as_of: str) -> list[tuple[str, float]]:
        """(day, venue mid - futures implied, in points) per stored session."""
        bids = {str(r["observed_at"])[:10]: r for r in store.as_of("pm.bid", as_of,
                                                                  c["contract"])}
        asks = {str(r["observed_at"])[:10]: r for r in store.as_of("pm.ask", as_of,
                                                                  c["contract"])}
        out = []
        for d in sorted(set(bids) & set(asks)):
            b, a = bids[d].get("value_num"), asks[d].get("value_num")
            if b is None or a is None:
                continue
            t = max(str(bids[d]["available_at"]), str(asks[d]["available_at"]))
            prices, _ = fed_funds.stored_prices(store, t)
            imp = implied(prices, c["meeting"], c["outcome"], d)
            if imp is None:
                continue
            out.append((d, (points(float(b)) + points(float(a))) / 2 - imp))
        return out

    def threshold(self, gaps: list[float]) -> Optional[float]:
        th = self.cfg().get("threshold") or {}
        if len(gaps) < int(th.get("min_history", 10)):
            return None
        xs = sorted(abs(g) for g in gaps)
        q = xs[min(len(xs) - 1, int(float(th.get("quantile", 0.9)) * len(xs)))]
        return max(float(th.get("min_points", 10)), q)

    def signal(self, as_of: str, store) -> list[Signal]:
        out = []
        day = session.session_date(as_of)
        floor = float(self.cfg().get("liquidity_floor", 0))
        for c in self.contracts():
            if day >= str(c["meeting"]):
                continue
            hist = self.gap_history(store, c, as_of)
            if not hist or hist[-1][0] != day:
                continue
            thr = self.threshold([g for _, g in hist[:-1]])
            vol = store.latest_as_of("pm.volume", as_of, c["contract"])
            liquid = vol is None or vol.get("value_num") is None or \
                float(vol["value_num"]) >= floor
            if thr is None or not liquid or abs(hist[-1][1]) <= thr:
                continue
            gap = hist[-1][1]
            out.append(Signal(instrument=self._instrument(c),
                              direction=-1 if gap > 0 else 1, as_of=as_of,
                              params={"gap_points": round(gap, 2),
                                      "threshold": round(thr, 2),
                                      "time_stop_date": str(c["meeting"])}))
        return out

    def size(self, signal: Signal, risk_budget: float) -> float:
        return 1.0 / max(1, len(self.contracts()))

    def bind_store(self, store) -> None:
        """The nightly loop hands the read-only store in, for the exits."""
        self.store = store

    def exits(self, position: dict, bar) -> Optional[str]:
        """Convergence: the gap back inside the band. The bar is the contract's
        stored probability that day; the futures side is read as of the bar's
        day, never later."""
        store = getattr(self, "store", None)
        c = next((x for x in self.contracts()
                  if str(x["contract"]) == position["instrument"]), None)
        if store is None or c is None:
            return None
        day = str(bar.day)[:10]
        prices, _ = fed_funds.stored_prices(store, f"{day}T23:59:59+00:00")
        imp = implied(prices, str(c["meeting"]), c["outcome"], day)
        if imp is None:
            return None
        band = float(self.cfg().get("band_points", 3))
        return "convergence" if abs(points(float(bar.close)) - imp) <= band else None

    # -- the harness's hooks -------------------------------------------------
    def refit_rows(self, store, as_of: str) -> list[dict]:
        """Every trade the rule would have taken, replayed over the stored
        history contract by contract: entered at the NEXT stored session's ask
        (buying YES) or bid (selling it) after a gap beyond the threshold known
        then, exited at the first stored mid inside the band or the last stored
        mid before the meeting, net of the prediction-market cost class."""
        from ..costs import CostModel                           # noqa: PLC0415
        cm = CostModel()
        band = float(self.cfg().get("band_points", 3))
        rows = []
        for c in self.contracts():
            hist = self.gap_history(store, c, as_of)
            bids = {str(r["observed_at"])[:10]: points(float(r["value_num"])) / 100
                    for r in store.as_of("pm.bid", as_of, c["contract"])
                    if r.get("value_num") is not None}
            asks = {str(r["observed_at"])[:10]: points(float(r["value_num"])) / 100
                    for r in store.as_of("pm.ask", as_of, c["contract"])
                    if r.get("value_num") is not None}
            i = 0
            while i < len(hist) - 1:
                thr = self.threshold([g for _, g in hist[:i]])
                d, gap = hist[i]
                if thr is None or abs(gap) <= thr or d >= str(c["meeting"]):
                    i += 1
                    continue
                direction = -1 if gap > 0 else 1
                e_day = hist[i + 1][0]
                entry = asks[e_day] if direction > 0 else bids[e_day]
                j = i + 1
                while j < len(hist) - 1 and abs(hist[j][1]) > band and \
                        hist[j + 1][0] < str(c["meeting"]):
                    j += 1
                x_day = hist[j][0]
                exit_ = bids[x_day] if direction > 0 else asks[x_day]
                # The spread is crossed both ways already (ask in, bid out, or the
                # reverse); commission and slippage each way on top, at the size a
                # new engine trades.
                base = entry if direction > 0 else 1 - entry
                notional = float(acfg.settings().get("notional_capital") or 100000) * 0.01
                qty = notional / max(base, 1e-6)
                fees = 2 * (cm.commission("prediction_market", qty, notional) / notional
                            + cm.slippage_bps("prediction_market", notional, None) / 1e4)
                net = direction * (exit_ - entry) / max(base, 1e-6) - fees
                rows.append({"day": d, "decided_at": f"{d}T23:59:59.000000+00:00",
                             "available_at": f"{d}T00:00:00.000000+00:00",
                             "net": net, "contract": c["contract"], "exit_day": x_day})
                i = j + 1
        return rows

    def strategy(self):
        from .. import validate as av                           # noqa: PLC0415
        return av.Strategy(family=self.family, horizon=self.horizon,
                           fit=lambda rows: {},
                           returns=lambda rows, p: [float(r["net"]) for r in rows])

    def coverage(self, store, as_of: str) -> dict:
        cs = self.contracts()
        n = sum(len(self.gap_history(store, c, as_of)) for c in cs)
        need = acfg.min_signals(self.horizon)
        return {"n": n, "need": need, "ok": bool(cs) and n >= need,
                "why": (f"{len(cs)} contract(s) mapped in config/alpha_pm_map.yaml; "
                        f"{n} contract-sessions with a stored quote and a futures "
                        f"path; the harness needs {need} independent signals")}
