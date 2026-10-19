"""
Engine 5 -- crypto carry and basis (X-3.2; the brief's roster item 5).

"After the S-3 funding and open-interest series are stored: perp funding harvest
and spot-perp basis on BTC and ETH, delta-neutral, with the funding regime as the
switch." Registered as `crypto_carry` (config/alpha_engines.yaml), its hypothesis
pre-registered by manifest (alpha/research/roster-2026-10-17-x3.yaml).

THE SWITCH (config/alpha_crypto_venues.yaml `switch:`), decided weekly at the last
session of the ISO week from S-3's series, each read as knowable at the decision:
ON when the trailing 7-day mean of calc.funding_agg (OI-weighted, annualised %)
is at or above 10% and calc.leverage_z is below +2; OFF when the mean falls below
3% or leverage_z reaches +2 (a crowded long is a squeeze risk, not a carry).
Between the two thresholds the state holds.

THE TRADE, while ON: long spot, short the perp on the venue paying the highest
stored funding at entry, equal notional (the perp's margin out of the sleeve:
`perp_margin_frac`), held until OFF. Funding is received (or paid, when it turns
negative) per day from that venue's stored daily funding, annualised % / 365.
Costs: each venue's published taker fee as a dated constant, the spot leg's too,
and the cost model's `perp` spread and slippage on both legs, entering and
leaving. THE BASIS IS A LISTED GAP: no perp mark price is stored, so both legs are
priced at the spot close and the basis is assumed unchanged over the hold; every
result says so.

THE HISTORY WINDOW. The z-scores mature in December: S-3's aggregate needs two
venues on the same day and its z 60 of 90 days. Until the store holds the
manifest's window (`min_history_weeks` weekly decisions with the switch
computable), coverage() prints "insufficient history" and nothing runs; the
hypothesis stays registered and the nightly harness looks again.

THE PAPER BOOK'S CRYPTO ROWS. Live (after the gate, never before), the nightly
loop calls carry(): it opens and closes rows in alpha.db's carry_book with the
venue, the leg sizes and the entry and exit costs, and accrues each day's funding
in carry_accruals. Paper only: nothing here can reach a venue.
"""

from __future__ import annotations

import datetime as dt
import statistics
from pathlib import Path
from typing import Optional

import yaml

from altdata import session

from .. import config as acfg
from .. import pit
from .. import validate as av
from ..engine import Engine, Instrument, Signal
from .trend import rebalance_days

CONFIG = acfg.REPO / "config" / "alpha_crypto_venues.yaml"
AGG, LEVZ = "calc.funding_agg", "calc.leverage_z"
MAX_AGE_DAYS = 3


def load_config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8")) or {}


def _d(s: str) -> dt.date:
    return dt.date.fromisoformat(s[:10])


class CarryEngine(Engine):
    family = "carry"
    horizon = "weekly"
    cost_class = "perp"
    validated_ranges: dict = {}
    grid_size = 1

    def __init__(self, params: Optional[dict] = None) -> None:
        super().__init__(params)
        self.cfg = load_config(self.params.get("config"))
        self.coins = list(self.cfg.get("coins") or ["BTC", "ETH"])
        self.margin = float(self.params.get("perp_margin_frac", 0.25))

    # -- costs ----------------------------------------------------------------
    def leg_cost(self, venue: str, px: float, notional: float) -> float:
        """One motion (enter or leave) on both legs, as a fraction of the leg
        notional: the spot taker and the venue's perp taker, plus the cost
        model's perp spread and slippage on each leg."""
        from ..costs import CostModel                           # noqa: PLC0415
        cm = CostModel()
        fees = (float(self.cfg["spot_leg"]["taker_bps"])
                + float(self.cfg["perp_venues"][venue]["taker_bps"])) / 1e4
        if not px or notional <= 0:
            return fees
        friction = 2 * (cm.half_spread("perp", px) / px
                        + cm.slippage_bps("perp", notional, None) / 1e4)
        return fees + friction

    def capital(self) -> float:
        return float(acfg.settings().get("notional_capital") or 100000) * \
            float(self.min_size or 0.01)

    # -- the reads --------------------------------------------------------------
    def _series(self, store, coin: str) -> dict:
        v = self.cfg["perp_venues"]
        return {"agg": pit.Series(store, AGG, coin), "levz": pit.Series(store, LEVZ, coin),
                "spot": pit.Series(store, self.cfg["spot_leg"]["price_keys"][coin]),
                "venues": {n: pit.Series(store, x["funding_key"], coin)
                           for n, x in v.items()}}

    def switch_inputs(self, s: dict, decided_at: str) -> Optional[dict]:
        """The switch's inputs knowable at the decision, or None."""
        sw = self.cfg.get("switch") or {}
        today = _d(pit.et_date(decided_at))
        since = (today - dt.timedelta(days=int(sw.get("mean_days", 7)) - 1)).isoformat()
        agg = s["agg"].known(decided_at, since=since)
        lz = s["levz"].known(decided_at, 1)
        if not agg or not lz or (today - _d(lz[0][0])).days > MAX_AGE_DAYS:
            return None
        venues = {}
        for n, ser in s["venues"].items():
            k = ser.known(decided_at, 1)
            if k and (today - _d(k[0][0])).days <= MAX_AGE_DAYS:
                venues[n] = k[0][1]
        if not venues:
            return None
        avail = [s["agg"].avail(d) for d, _ in agg] + [s["levz"].avail(lz[0][0])]
        return {"mean": statistics.fmean(v for _, v in agg), "levz": lz[0][1],
                "venue": max(venues, key=lambda n: venues[n]), "venues": venues,
                "available_at": max(a for a in avail if a)}

    def state(self, inp: dict, was_on: bool) -> bool:
        sw = self.cfg.get("switch") or {}
        if inp["levz"] >= float(sw.get("crowded_z", 2.0)):
            return False
        if inp["mean"] >= float(sw.get("on_annual_pct", 10.0)):
            return True
        if inp["mean"] < float(sw.get("off_annual_pct", 3.0)):
            return False
        return was_on

    # -- the harness's hooks ------------------------------------------------
    def refit_rows(self, store, as_of: str) -> list[dict]:
        """One row per coin per weekly decision with the switch computable:
        the state, the venue held, the week's funding on that venue (received
        while ON) and the costs of any entry or exit, point in time."""
        last = session.session_date(as_of)
        rows = []
        for coin in self.coins:
            s = self._series(store, coin)
            if not s["agg"]:
                continue
            first = s["agg"].days[0]
            days = rebalance_days(first, last)
            on, venue = False, None
            for i, d in enumerate(days):
                t = pit.decision_instant(d)
                inp = self.switch_inputs(s, t)
                if inp is None:
                    continue
                now_on = self.state(inp, on)
                held = venue if (on and now_on) else (inp["venue"] if now_on else venue)
                nxt = days[i + 1] if i + 1 < len(days) else None
                fund = None
                if now_on and held and nxt:
                    fund, k = 0.0, _d(d) + dt.timedelta(days=1)
                    while k <= _d(nxt):
                        f = s["venues"][held].latest(k.isoformat())
                        fund += (f or 0.0) / 100.0 / 365.0
                        k += dt.timedelta(days=1)
                px = s["spot"].latest(d) or 0.0
                rows.append({"day": d, "decided_at": t, "available_at": inp["available_at"],
                             "coin": coin, "on": now_on, "was_on": on,
                             "venue": held if now_on else venue, "funding": fund,
                             "mean": inp["mean"], "levz": inp["levz"], "price": px,
                             "complete": nxt is not None})
                on, venue = now_on, (held if now_on else None)
        return sorted(rows, key=lambda r: (r["day"], r["coin"]))

    def _returns(self, rows: list[dict], p: dict) -> list[float]:
        """Each active week's net return on the sleeve: the funding received on
        the leg notional, less the entry or exit costs that week, the leg notional
        being the sleeve less the perp's margin."""
        cap = self.capital() / max(1, len(self.coins))
        lev = 1.0 / (1.0 + self.margin)
        out = []
        for r in rows:
            if not r["complete"] or not (r["on"] or r["was_on"]):
                continue
            notional = cap * lev
            x = 0.0
            if r["on"]:
                x += (r["funding"] or 0.0)
                if not r["was_on"]:
                    x -= self.leg_cost(r["venue"], r["price"], notional)
            elif r["was_on"] and r["venue"]:
                x -= self.leg_cost(r["venue"], r["price"], notional)
            out.append(x * lev)
        return out

    def strategy(self) -> av.Strategy:
        # The switch's thresholds were fixed when the manifest was written; the
        # walk-forward tests the rule as registered, nothing is fitted.
        return av.Strategy(family=self.family, horizon=self.horizon,
                           fit=lambda rows: {},
                           returns=lambda rows, p: self._returns(rows, p))

    def coverage(self, store, as_of: str) -> dict:
        need = int(self.cfg.get("min_history_weeks", 92))
        rows = self.refit_rows(store, as_of)
        weeks = {c: len([r for r in rows if r["coin"] == c]) for c in self.coins}
        n = max(weeks.values()) if weeks else 0
        ok = n >= need
        return {"n": n, "need": need, "by_coin": weeks, "ok": ok, "wait": not ok,
                "basis": self.cfg.get("basis_gap"),
                "why": ("history window met" if ok else
                        f"insufficient history: {n} of {need} weekly decisions with "
                        f"calc.funding_agg and calc.leverage_z knowable (the manifest's "
                        f"window); nothing runs until it is met")}

    # -- the interface ------------------------------------------------------
    def universe(self) -> list[Instrument]:
        return [Instrument(id=f"{c}-USD", key=self.cfg["spot_leg"]["price_keys"][c],
                           cost_class="perp", meta={"legs": ["spot", "perp"]})
                for c in self.coins]

    def signal(self, as_of: str, store) -> list[Signal]:
        """None into the one-instrument paper book: a two-leg carry is booked by
        carry(), in the carry_book rows."""
        return []

    def size(self, signal: Signal, risk_budget: float) -> float:
        return 0.0

    def exits(self, position: dict, bar) -> Optional[str]:
        return None

    # -- the paper book's crypto rows (live only, after the gate) -----------
    def carry(self, ledger, store, as_of: str, capital: float) -> dict:
        """Open, accrue and close this engine's carry_book rows for the night."""
        day = session.session_date(as_of)
        is_decision = day in rebalance_days(day, day)
        cap = capital / max(1, len(self.coins))
        lev = 1.0 / (1.0 + self.margin)
        out = {"opened": [], "closed": [], "accrued": 0}
        for coin in self.coins:
            s = self._series(store, coin)
            row = ledger.one("SELECT * FROM carry_book WHERE engine_id=? AND coin=? "
                             "AND status='open'", (self.engine_id, coin))
            if row:
                out["accrued"] += self._accrue(ledger, s, row, as_of)
            if not is_decision:
                continue
            t = pit.decision_instant(day)
            inp = self.switch_inputs(s, t)
            if inp is None:
                continue
            now_on = self.state(inp, bool(row))
            # The latest spot close knowable now: a coin's daily close lands at
            # midnight UTC, after the 17:40 ET loop.
            k = s["spot"].known(as_of, 1)
            if not k or (_d(day) - _d(k[0][0])).days > MAX_AGE_DAYS:
                continue
            px = k[0][1]
            if now_on and not row:
                notional = cap * lev
                cid = ledger._insert("carry_book", {
                    "engine_id": self.engine_id, "coin": coin, "venue": inp["venue"],
                    "opened_day": day, "spot_qty": notional / px,
                    "perp_qty": -notional / px, "notional": notional, "entry_price": px,
                    "entry_costs": notional * self.leg_cost(inp["venue"], px, notional),
                    "funding_accrued": 0.0, "status": "open",
                    "basis_note": self.cfg.get("basis_gap"), "as_of": as_of})
                out["opened"].append({"coin": coin, "venue": inp["venue"], "id": cid})
            elif row and not now_on:
                exit_costs = row["notional"] * self.leg_cost(row["venue"], px,
                                                             row["notional"])
                acc = ledger.one("SELECT COALESCE(SUM(accrued),0) AS s FROM "
                                 "carry_accruals WHERE carry_id=?", (row["id"],))["s"]
                net = float(acc) - float(row["entry_costs"]) - exit_costs
                ledger.conn.execute(
                    "UPDATE carry_book SET status='closed', closed_day=?, exit_price=?, "
                    "exit_costs=?, net_pnl=?, funding_accrued=?, as_of=? WHERE id=?",
                    (day, px, exit_costs, net, float(acc), as_of, row["id"]))
                ledger.conn.commit()
                out["closed"].append({"coin": coin, "id": row["id"], "net_pnl": net})
        if out["opened"] or out["closed"]:
            ledger.event("nightly", "carry", as_of, self.engine_id, after=out)
        return out

    def _accrue(self, ledger, s: dict, row: dict, as_of: str) -> int:
        """Each calendar day since the last accrual through the session's date,
        at the held venue's funding knowable now. The walk stops at the first day
        with no stored funding yet, so a later night accrues it once it lands."""
        last = ledger.one("SELECT MAX(day) AS d FROM carry_accruals WHERE carry_id=?",
                          (row["id"],))["d"] or row["opened_day"]
        k, end, n = _d(last) + dt.timedelta(days=1), _d(pit.et_date(as_of)), 0
        ser = s["venues"][row["venue"]]
        while k <= end:
            f = ser.at(k.isoformat(), as_of)
            if f is None:
                break
            ledger._insert("carry_accruals", {
                "carry_id": row["id"], "engine_id": self.engine_id,
                "day": k.isoformat(), "venue": row["venue"], "funding_pct": f,
                "accrued": row["notional"] * f / 100.0 / 365.0, "as_of": as_of})
            n += 1
            k += dt.timedelta(days=1)
        if n:
            acc = ledger.one("SELECT COALESCE(SUM(accrued),0) AS s FROM carry_accruals "
                             "WHERE carry_id=?", (row["id"],))["s"]
            ledger.conn.execute("UPDATE carry_book SET funding_accrued=? WHERE id=?",
                                (float(acc), row["id"]))
            ledger.conn.commit()
        return n
