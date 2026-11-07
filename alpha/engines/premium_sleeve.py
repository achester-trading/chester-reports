"""
The premium sleeve -- Batch 19 item 100 (accepted 27 Oct 2026; B99). A paper
engine: SPX put credit spreads, gated by the regime, family_ref "KS options".

Its hypothesis, P-1, was committed BEFORE this module
(alpha/research/roster-2026-10-31-premium-sleeve.yaml), and every rule here is
config/alpha_premium_sleeve.yaml's pre-registered `spec`: check_spec() refuses a
spec that no longer hashes to the sha256 the registration quotes. Nothing in this
module reads a result, and nothing here can place an order: alpha/ imports no
order path (tools/validate_alpha_no_orders.py). Paper only; no live orders before
2027 (item 100). DISABLED in config/alpha_engines.yaml: no loop runs it until the
operator registers P-1 and enables it.

THE INPUTS, each read as knowable at the nightly decision (17:40 ET):
  VRP        yfinance.mkt_vix less calc.vol_spy_realized_20d, > 0
  IV rank    yfinance.mkt_vix over its last 252 stored sessions, >= 66.67
  dealer     exposure.net_gex > 0, or exposure.spot > exposure.gamma_flip (SPX)
  overlays   altdata/tb_harness.py's HY Spread Acceleration and Liquidity: stand
             down on FIRES, and on a state it cannot read
  the count  capitulation.count_band (B79 stores none yet) with
             top_bottom.verdict (no writer yet): stand down on surrender without a
             BOTTOM SIGNAL, and while the count is not stored ("count not stored")
  the chain  the vendor chain snapshots the system holds (SPX, data/chains), each
             row knowable at its fetched_at; a day without the expiry or the
             strikes trades nothing, logged "chain not stored"

THE FILLS are alpha/costs.py's, through the spread's own line
(config/alpha_costs.yaml index_option_spread): each leg at its executable side,
never the mid. THE BENCHMARK is the Cboe PUT index, not stored under D45's hold
(D2-74): returns are ledgered against cash until it is ruled.

A spread has two legs, so it is not a one-instrument signal for the paper book.
signal() returns none; the harness's hooks (refit_rows, strategy, coverage) carry
the rule, and position_record() writes a trade in the positions table's own shape
with its family_ref beside it.
"""

from __future__ import annotations

import csv
import datetime as dt
import math
import os
from pathlib import Path
from typing import Optional

import yaml

from altdata import session

from .. import config as acfg
from .. import manifest, pit
from .. import validate as av
from ..costs import CostModel
from ..engine import Engine, Instrument, Signal

CONFIG = acfg.REPO / "config" / "alpha_premium_sleeve.yaml"
COST_CLASS = "index_option_spread"
MAX_AGE_DAYS = 3
CHAIN_NOT_STORED = "chain not stored"
COUNT_NOT_STORED = "count not stored"


class SpecChanged(ValueError):
    """The spec no longer hashes to the sha256 its registration quotes."""


def load_config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8")) or {}


def spec_sha256(cfg: dict) -> str:
    return manifest.batch_sha256(cfg["spec"])


def check_spec(cfg: dict) -> dict:
    have = spec_sha256(cfg)
    if have != str(cfg.get("spec_sha256")):
        raise SpecChanged(f"config/alpha_premium_sleeve.yaml's spec hashes to {have}, "
                          f"not the {cfg.get('spec_sha256')} its registration quotes: a "
                          f"changed spec is a new hypothesis, registered by its own "
                          f"manifest")
    return cfg["spec"]


def put_delta(spot: float, strike: float, iv: float, years: float) -> Optional[float]:
    """|Black-Scholes put delta| at rate and dividend zero (the spec's)."""
    if not (spot > 0 and strike > 0 and iv and iv > 0 and years > 0):
        return None
    d1 = (math.log(spot / strike) + 0.5 * iv * iv * years) / (iv * math.sqrt(years))
    return 0.5 * math.erfc(d1 / math.sqrt(2.0))          # N(-d1)


def _f(x) -> Optional[float]:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


# ---------------------------------------------------------------------------
# The chain: the system's vendor snapshots, point in time
# ---------------------------------------------------------------------------
def chain_dir() -> Path:
    from altdata import config as aconfig                       # noqa: PLC0415
    p = Path(os.environ.get("CHESTER_CHAIN_DIR", aconfig.CHAIN_DIR)).expanduser()
    return p if p.is_absolute() else acfg.REPO / p


class FileChains:
    """The vendor chain snapshots under the chain directory, read-only. A
    snapshot is knowable at its rows' fetched_at; snapshot(day, as_of) is the
    session's last one knowable at as_of, or None."""

    def __init__(self, base: Optional[Path] = None, symbol: str = "SPX") -> None:
        self.base, self.symbol = Path(base) if base else chain_dir(), symbol

    def days(self) -> list[str]:
        if not self.base.is_dir():
            return []
        return sorted(p.name for p in self.base.iterdir()
                      if p.is_dir() and any(p.glob(f"{self.symbol}_*.csv")))

    def snapshot(self, day: str, as_of: str) -> Optional[list[dict]]:
        best, best_at = None, None
        for f in sorted((self.base / day).glob(f"{self.symbol}_*.csv")):
            with f.open(encoding="utf-8", newline="") as fp:
                rows = list(csv.DictReader(fp))
            if not rows or not rows[0].get("fetched_at"):
                continue
            at = pit.canon(rows[0]["fetched_at"])
            if at <= pit.canon(as_of) and (best_at is None or at > best_at):
                best, best_at = rows, at
        return parse_rows(best, best_at) if best else None


def parse_rows(rows: list[dict], fetched_at: Optional[str] = None) -> list[dict]:
    out = []
    for r in rows:
        out.append({"expiry": str(r.get("expiry"))[:10], "dte": int(_f(r.get("dte")) or 0),
                    "right": str(r.get("right") or "").upper()[:1],
                    "strike": _f(r.get("strike")), "bid": _f(r.get("bid")),
                    "ask": _f(r.get("ask")), "iv": _f(r.get("implied_vol")),
                    "spot": _f(r.get("spot")),
                    "fetched_at": fetched_at or pit.canon(r.get("fetched_at"))})
    return out


# ---------------------------------------------------------------------------
# The engine
# ---------------------------------------------------------------------------
class PremiumSleeveEngine(Engine):
    family = "KS options"            # B98: the variant count keys on the family_ref
    family_ref = "KS options"
    horizon = "daily"
    cost_class = COST_CLASS
    validated_ranges: dict = {}

    def __init__(self, params: Optional[dict] = None) -> None:
        super().__init__(params)
        self.cfg = load_config(self.params.get("config"))
        self.spec = dict(check_spec(self.cfg))
        for k, v in (self.params.get("variant") or {}).items():
            self.spec[k] = v                 # a counted variant's one change
        self.grid_size = 1 + len(self.spec.get("variants") or [])
        self.chains = FileChains(self.params.get("chain_dir"), self.spec["underlying"])
        self.overlay_reader = None           # (store, day, t) -> {id: state}; the gate's
        self.costs = CostModel()
        self.log: list[dict] = []

    # -- the reads ----------------------------------------------------------------
    def _last(self, ser: pit.Series, day: str, t: str) -> Optional[tuple[str, float]]:
        k = [x for x in ser.known(t) if x[0] <= day]
        if not k or (dt.date.fromisoformat(day) - dt.date.fromisoformat(k[-1][0])).days \
                > MAX_AGE_DAYS:
            return None
        return k[-1]

    def series(self, store) -> dict:
        g = self.spec["gates"]
        dk = g["dealer"]["keys"]
        inst = g["dealer"]["instrument"]
        return {"vix": pit.Series(store, g["vrp"]["implied_key"]),
                "rv": pit.Series(store, g["vrp"]["realised_key"]),
                "ivr": pit.Series(store, g["iv_rank"]["key"]),
                "gex": pit.Series(store, dk["net_gex"], inst),
                "flip": pit.Series(store, dk["flip"], inst),
                "spot": pit.Series(store, dk["spot"], inst),
                "settle": pit.Series(store, "yfinance.mkt_gspc")}

    def overlays(self, store, day: str, t: str) -> dict[str, str]:
        if self.overlay_reader is not None:
            return dict(self.overlay_reader(store, day, t))
        try:
            from altdata import tb_harness                      # noqa: PLC0415
            cfg = tb_harness.config()
            return {o["id"]: o["state"] for o in tb_harness.overlays_at(store, cfg, day, t)}
        except Exception as exc:                                # noqa: BLE001
            return {i: f"UNREAD ({type(exc).__name__})"
                    for i in self.spec["stand_downs"]["overlays"]["ids"]}

    def _text_at(self, store, key: str, day: str, t: str) -> Optional[str]:
        rows = [r for r in store.all_vintages(key)
                if str(r["observed_at"])[:10] <= day and pit.canon(r["available_at"]) <= pit.canon(t)]
        if not rows:
            return None
        r = rows[-1]
        if r.get("value_text"):
            return str(r["value_text"])
        v = r.get("value_num")
        return None if v is None else ("surrender" if float(v) >= 4 else
                                       "oversold" if float(v) >= 2 else "none")

    def inputs(self, store, day: str, t: str, s: Optional[dict] = None) -> dict:
        """Every gate's and stand-down's reading for session `day` at `t`."""
        s = s or self.series(store)
        g = self.spec["gates"]
        out: dict = {"day": day, "decided_at": t, "avail": []}
        vix, rv = self._last(s["vix"], day, t), self._last(s["rv"], day, t)
        out["vrp"] = (vix[1] - rv[1]) if vix and rv else None
        hist = [v for d, v in s["ivr"].known(t) if d <= day][-int(g["iv_rank"]["window_sessions"]):]
        if len(hist) >= int(g["iv_rank"]["window_sessions"]) and max(hist) > min(hist):
            out["iv_rank"] = (hist[-1] - min(hist)) / (max(hist) - min(hist)) * 100.0
        else:
            out["iv_rank"] = None
        gx, fl, sp = (s[k].at(day, t) for k in ("gex", "flip", "spot"))
        out["net_gex"], out["flip"], out["spot"] = gx, fl, sp
        for ser, d in ((s["vix"], vix), (s["rv"], rv)):
            if d:
                out["avail"].append(ser.avail(d[0]))
        out["overlays"] = self.overlays(store, day, t)
        sd = self.spec["stand_downs"]["capitulation"]
        out["count_band"] = self._text_at(store, sd["count_key"], day, t)
        out["tb_verdict"] = self._text_at(store, sd["verdict_key"], day, t)
        return out

    def gates_failed(self, inp: dict) -> list[str]:
        out = []
        if inp["vrp"] is None or not inp["vrp"] > 0:
            out.append("vrp" if inp["vrp"] is not None else "vrp: not stored")
        if inp["iv_rank"] is None or inp["iv_rank"] < 200.0 / 3.0:
            out.append("iv_rank" if inp["iv_rank"] is not None else "iv_rank: under 252 sessions")
        gx, fl, sp = inp["net_gex"], inp["flip"], inp["spot"]
        dealer_ok = (gx is not None and gx > 0) or (sp is not None and fl is not None and sp > fl)
        if not dealer_ok:
            out.append("dealer" if gx is not None or fl is not None else "dealer: not stored")
        return out

    def stand_downs(self, inp: dict) -> list[str]:
        out = []
        sd = self.spec["stand_downs"]
        for i in sd["overlays"]["ids"]:
            st = str(inp["overlays"].get(i) or "UNREAD")
            if st != "CLEAR":
                out.append(f"{i}: {st}")
        band = inp.get("count_band")
        if band is None:
            out.append(COUNT_NOT_STORED)
        elif band == "surrender" and str(inp.get("tb_verdict") or "") != "BOTTOM SIGNAL":
            out.append("capitulation: surrender without a BOTTOM SIGNAL")
        return out

    # -- the chain -------------------------------------------------------------
    def choose(self, rows: Optional[list[dict]]) -> tuple[Optional[dict], str]:
        """(the spread, "") from one snapshot, or (None, why)."""
        if not rows:
            return None, CHAIN_NOT_STORED
        sp = self.spec
        puts = [r for r in rows if r["right"] == "P" and r["strike"] and r["bid"] is not None
                and r["ask"] is not None and r["ask"] > 0]
        lo, hi = sp["dte_window"]
        exp = sorted({(r["expiry"], r["dte"]) for r in puts if lo <= r["dte"] <= hi})
        if not exp:
            return None, f"{CHAIN_NOT_STORED}: no expiry {lo}-{hi} days out"
        mid = (lo + hi) / 2.0
        expiry, dte = min(exp, key=lambda e: (abs(e[1] - mid), e[1]))
        legs = [r for r in puts if r["expiry"] == expiry]
        spot = next((r["spot"] for r in legs if r["spot"]), None)
        dlo, dhi = sp["short_delta_band"]
        cands = []
        for r in legs:
            d = put_delta(spot or 0.0, r["strike"], r["iv"] or 0.0, dte / 365.0)
            if d is not None and dlo <= d <= dhi:
                cands.append((abs(d - (dlo + dhi) / 2.0), -r["strike"], r, d))
        if not cands:
            return None, f"{CHAIN_NOT_STORED}: no strike at |delta| {dlo}-{dhi}"
        _, _, short, delta = min(cands, key=lambda c: (c[0], c[1]))
        floor = short["strike"] - float(sp["width_points"])
        below = [r for r in legs if r["strike"] <= floor]
        if not below:
            return None, f"{CHAIN_NOT_STORED}: no long strike at or below {floor:g}"
        long = max(below, key=lambda r: r["strike"])
        return {"expiry": expiry, "dte": dte, "short": short, "long": long,
                "short_delta": delta, "spot": spot}, ""

    def leg(self, side: int, row: dict, qty: float):
        """One leg's fill at its executable side: side -1 sells at the bid, +1
        buys at the ask, through the spread's cost line. Never the mid."""
        return self.costs.fill(COST_CLASS, side, qty, reference_price=0.0,
                               quote={"bid": row["bid"], "ask": row["ask"]})

    def open_price(self, sprd: dict, qty: float) -> dict:
        s, l = self.leg(-1, sprd["short"], qty), self.leg(+1, sprd["long"], qty)
        return {"credit": s.price - l.price, "commission": s.costs["commission"]
                + l.costs["commission"], "fills": (s, l)}

    def close_price(self, short: dict, long: dict, qty: float) -> dict:
        s, l = self.leg(+1, short, qty), self.leg(-1, long, qty)
        return {"debit": s.price - l.price, "commission": s.costs["commission"]
                + l.costs["commission"], "fills": (s, l)}

    def capital(self) -> float:
        return float(acfg.settings().get("notional_capital") or 100000) * \
            float(self.min_size or 0.05)

    # -- the rule, over the stored history ---------------------------------
    def simulate(self, store, as_of: str, days: Optional[list[str]] = None) -> list[dict]:
        """Every trade the rule makes over the sessions with a stored snapshot,
        point in time. Logs each day it cannot trade, with why."""
        self.log = []
        s = self.series(store)
        sp = self.spec
        mult = self.costs.multiplier(COST_CLASS)
        last = session.session_date(as_of)
        days = days or [d for d in self.chains.days() if d <= last]
        trades, pos, pending = [], None, None
        for d in days:
            t = pit.decision_instant(d)
            snap = self.chains.snapshot(d, t)
            # 1. A pending entry fills at this session's snapshot.
            if pending and pos is None:
                rows = snap
                sprd = None
                if rows:
                    by = {(r["expiry"], r["strike"], r["right"]): r for r in rows}
                    sh = by.get((pending["expiry"], pending["short"]["strike"], "P"))
                    lg = by.get((pending["expiry"], pending["long"]["strike"], "P"))
                    if sh and lg and None not in (sh["bid"], sh["ask"], lg["bid"], lg["ask"]):
                        sprd = dict(pending, short=sh, long=lg)
                if sprd is None:
                    self.log.append({"day": d, "why": f"{CHAIN_NOT_STORED}: the entry's legs"})
                else:
                    width = sprd["short"]["strike"] - sprd["long"]["strike"]
                    px1 = self.open_price(sprd, 1)
                    max_loss = (width - px1["credit"]) * mult
                    qty = math.floor(self.capital() / max_loss) if max_loss > 0 else 0
                    if qty < 1 or px1["credit"] <= 0:
                        self.log.append({"day": d, "why": "under one spread at the sleeve's capital"
                                         if qty < 1 else "no credit at the executable sides"})
                    else:
                        px = self.open_price(sprd, qty)
                        pos = {"signal_day": pending["signal_day"], "decided_at": pending["decided_at"],
                               "available_at": pending["available_at"], "entry_day": d,
                               "expiry": sprd["expiry"], "short_k": sprd["short"]["strike"],
                               "long_k": sprd["long"]["strike"], "width": width, "qty": qty,
                               "credit": px["credit"], "entry_commission": px["commission"],
                               "short_delta": pending["short_delta"]}
                pending = None
            # 2. An open spread: settle, take profit, or the 21-DTE close.
            if pos and d != pos["entry_day"]:
                dte = (dt.date.fromisoformat(pos["expiry"]) - dt.date.fromisoformat(d)).days
                exit_ = None
                if d >= pos["expiry"]:
                    px_close = s["settle"].latest(pos["expiry"])
                    if px_close is not None:
                        intr = (max(pos["short_k"] - px_close, 0) - max(pos["long_k"] - px_close, 0))
                        exit_ = ("expiry", intr, 0.0)
                elif snap:
                    by = {(r["expiry"], r["strike"], r["right"]): r for r in snap}
                    sh = by.get((pos["expiry"], pos["short_k"], "P"))
                    lg = by.get((pos["expiry"], pos["long_k"], "P"))
                    if sh and lg and None not in (sh["bid"], sh["ask"], lg["bid"], lg["ask"]):
                        cp = self.close_price(sh, lg, pos["qty"])
                        if cp["debit"] <= float(sp["take_profit_frac"]) * pos["credit"]:
                            exit_ = ("take_profit", cp["debit"], cp["commission"])
                        elif dte <= int(sp["exit_dte"]):
                            exit_ = ("dte_21", cp["debit"], cp["commission"])
                    elif dte <= int(sp["exit_dte"]):
                        self.log.append({"day": d, "why": f"{CHAIN_NOT_STORED}: the exit's legs"})
                if exit_:
                    reason, debit, comm = exit_
                    pnl = ((pos["credit"] - debit) * mult * pos["qty"]
                           - pos["entry_commission"] - comm)
                    trades.append(dict(pos, exit_day=d, exit_reason=reason, debit=debit,
                                       exit_commission=comm, net_usd=pnl,
                                       net=pnl / self.capital(), family_ref=self.family_ref))
                    pos = None
            # 3. The night's decision: a new entry, filled at the next snapshot.
            if pos is None and pending is None:
                inp = self.inputs(store, d, t, s)
                why = self.gates_failed(inp) + self.stand_downs(inp)
                if why:
                    self.log.append({"day": d, "why": "; ".join(why)})
                    continue
                sprd, miss = self.choose(snap)
                if sprd is None:
                    self.log.append({"day": d, "why": miss})
                    continue
                pending = dict(sprd, signal_day=d, decided_at=t,
                               available_at=max([a for a in inp["avail"] if a]
                                                + [sprd["short"]["fetched_at"]]))
        return trades

    # -- the harness's hooks --------------------------------------------------
    def refit_rows(self, store, as_of: str) -> list[dict]:
        return [{"day": x["signal_day"], "decided_at": x["decided_at"],
                 "available_at": x["available_at"], "net": x["net"], "trade": x}
                for x in self.simulate(store, as_of)]

    def strategy(self) -> av.Strategy:
        # The spec was fixed when the registration was written; nothing is fitted.
        return av.Strategy(family=self.family, horizon=self.horizon, fit=lambda rows: {},
                           returns=lambda rows, p: [float(r["net"]) for r in rows])

    def coverage(self, store, as_of: str) -> dict:
        need = acfg.min_signals(self.horizon)
        days = self.chains.days()
        trades = self.simulate(store, as_of) if days else []
        n = len(trades)
        ok = n >= need
        return {"n": n, "need": need, "ok": ok, "wait": not ok,
                "chain_days": len(days), "benchmark": self.spec["benchmark"]["state"],
                "why": ("the sample is met" if ok else
                        f"insufficient history: {n} completed spreads over {len(days)} "
                        f"stored SPX snapshot sessions; the harness needs {need}")}

    def position_record(self, trade: dict, as_of: str) -> dict:
        """A closed trade in the positions table's own shape, its family_ref beside
        it (the positions table has no family column)."""
        inst = (f"SPX {trade['expiry']} P{trade['short_k']:g}/P{trade['long_k']:g} "
                f"put credit spread")
        return {"row": {"engine_id": self.engine_id or "premium_sleeve", "signal_id": None,
                        "instrument": inst, "instrument_norm": "SPX", "cost_class": COST_CLASS,
                        "direction": -1, "qty": float(trade["qty"]), "entry_fill_id": None,
                        "entry_price": trade["credit"], "stop_price": None,
                        "target_price": float(self.spec["take_profit_frac"]) * trade["credit"],
                        "time_stop": f"{self.spec['exit_dte']} days to expiry",
                        "opened_at": trade["entry_day"], "status": "closed",
                        "exit_fill_id": None, "exit_price": trade["debit"],
                        "exit_reason": trade["exit_reason"], "closed_at": trade["exit_day"],
                        "as_of": as_of},
                "family_ref": trade.get("family_ref") or self.family_ref}

    # -- the interface ------------------------------------------------------
    def universe(self) -> list[Instrument]:
        return [Instrument(id="SPX", key="yfinance.mkt_gspc", cost_class=COST_CLASS,
                           meta={"structure": "put credit spread", "multiplier": 100})]

    def signal(self, as_of: str, store) -> list[Signal]:
        """None into the one-instrument paper book: a two-leg spread is the
        engine's own record (position_record), as engine 5's carry is."""
        return []

    def size(self, signal: Signal, risk_budget: float) -> float:
        return 0.0

    def exits(self, position: dict, bar) -> Optional[str]:
        return None
