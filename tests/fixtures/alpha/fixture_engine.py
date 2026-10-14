"""
A FIXTURE ENGINE for tools/validate_alpha.py -- not an engine, and never
registered in config/alpha_engines.yaml (Tranche 1 registers none).

It goes long SPY after an up close, with a bracket (stop 2% below the close,
target 3% above) and a five-day time stop, and short after a down close the
other way round. It exists so the nightly loop can be run end to end on a
synthetic store: fill, mark, grade, govern, learn.
"""

from __future__ import annotations

from typing import Optional

from alpha.engine import Bar, Engine, Instrument, Signal

SPY = Instrument(id="SPY", key="yfinance.mkt_spy", cost_class="etf")


class FixtureEngine(Engine):
    engine_id = "fixture_trend"
    family = "fixture"
    horizon = "daily"
    cost_class = "etf"
    validated_ranges = {"stop_pct": [0.02, 0.02], "target_pct": [0.03, 0.03]}
    min_size = 0.01

    def universe(self) -> list[Instrument]:
        return [SPY]

    def signal(self, as_of: str, store) -> list[Signal]:
        bars = store.daily_bars(SPY.key, as_of)
        if len(bars) < 2:
            return []
        prev, last = bars[-2]["close"], bars[-1]["close"]
        if last == prev:
            return []
        d = 1 if last > prev else -1
        stop = float(self.params.get("stop_pct", 0.02))
        tgt = float(self.params.get("target_pct", 0.03))
        return [Signal(instrument=SPY, direction=d, as_of=as_of,
                       stop=last * (1 - d * stop), target=last * (1 + d * tgt),
                       time_stop_days=5)]

    def size(self, signal: Signal, risk_budget: float) -> float:
        return 1.0

    def exits(self, position: dict, bar: Bar) -> Optional[str]:
        return None


class BlockedEngine(FixtureEngine):
    """Signals on a Brookfield-complex ticker: the lab must refuse it."""
    engine_id = "fixture_blocked"

    def signal(self, as_of: str, store) -> list[Signal]:
        return [Signal(instrument=Instrument(id="BN", key="yfinance.mkt_spy",
                                             cost_class="single_name"),
                       direction=1, as_of=as_of)]


class RefitEngine(FixtureEngine):
    """Exposes the weekly loop's re-fit hooks (X-2.4) over SPY's stored closes:
    a momentum sign over `lookback` sessions, validated over lookback [10, 40].
    Its fit returns `fit_to` (a param), so the gate can ask for an in-range and
    an out-of-range re-fit and watch what the loop does with each."""
    engine_id = "fixture_refit"
    validated_ranges = {"lookback": [10, 40]}
    refit_test_rows = 60

    def refit_rows(self, store, as_of: str) -> list[dict]:
        from altdata import observations                        # noqa: PLC0415
        bars = store.daily_bars(SPY.key, as_of)
        t = observations.canonical_instant(as_of)
        rows = []
        closes = [b["close"] for b in bars]
        for i in range(60, len(bars) - 1):
            rows.append({"day": bars[i]["day"], "decided_at": t,
                         "available_at": f"{bars[i]['day']}T20:20:00.000000+00:00",
                         "past": closes[i - 60:i + 1],
                         "next_ret": closes[i + 1] / closes[i] - 1})
        return rows

    def strategy(self):
        from alpha import validate as av                        # noqa: PLC0415
        fit_to = int(self.params.get("fit_to", 20))

        def returns(rows, p):
            k = int(p.get("lookback", 20))
            out = []
            for r in rows:
                if len(r["past"]) <= k:
                    continue
                d = 1 if r["past"][-1] > r["past"][-1 - k] else -1
                out.append(d * r["next_ret"] - 0.0002)
            return out
        return av.Strategy(family=self.family, horizon=self.horizon,
                           fit=lambda rows: {"lookback": fit_to}, returns=returns)
