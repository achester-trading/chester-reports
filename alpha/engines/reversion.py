"""
Engine 6 -- extremes reversion (X-3.3; the brief's roster item 6).

"After the move screen's base rates reach n >= 30 per bucket: fade the 2.5 sigma
prints whose own history reverses, at the horizon the history says." Registered
as `reversion` (config/alpha_engines.yaml); its hypothesis E-6 is pre-registered
by manifest (alpha/research/roster-2026-10-19-x3-3.yaml), and every rule below is
config/alpha_reversion.yaml's `spec`, whose sha256 the roster quotes.

NOT THE MOVE SCREEN'S BASE RATE. altdata/move_screen.py prints "false flag k/N"
with every past print identified against the whole five-year window's mean and
spread as known today: in-sample, so the engine never reads it. Here a print on
day t is a print only if its one-session log change is past `sigma` against the
changes of its own trailing window (`window_calendar_days`, at least
`min_observations` of them, today's excluded) AS KNOWN AT t's nightly decision;
its reversal is read at 1, 5, 10 and 20 sessions as known when its twentieth
session became knowable (the print is then "completed").

THE BUCKET is the series and the sign of its print. Its FORMATION SAMPLE is its
first 30 completed prints, in completion order; below 30 the bucket prints
"awaiting (n=k of 30)" and trades nothing. Once the thirtieth completes, the
horizon is the one of the four with the highest share of prints at least half
reversed in that sample only (ties to the shorter), and it is FROZEN: the sample
is fixed, so no later print moves it. The bucket trades only where that share is
at least `min_reversal_share`, and only prints identified after its formation
completed: the formation prints themselves are never traded.

THE TRADE fades the print (short an up-print, long a down-print) from the next
session's open where an open is stored, else from the next session's close, to
the close at the frozen horizon. The cost model sets no stop, so the horizon is
the only exit. Costs: the lab's cost model at the engine's own capital, a round
trip plus borrow, roll and funding over the calendar days held. The engine
writes nothing; promotion is the gate's (X-1.6, X-2.6).
"""

from __future__ import annotations

import bisect
import datetime as dt
import math
from pathlib import Path
from typing import Optional

import yaml

from altdata import session

from .. import config as acfg
from .. import manifest, pit, rules
from .. import validate as av
from ..engine import Engine, Instrument, Signal
from .events import round_trip
from .trend import cost_class as trend_cost_class
from .trend import tradable

CONFIG = acfg.REPO / "config" / "alpha_reversion.yaml"
FIT_ROWS = 60                          # alpha/research/workbench.py ENGINE_WINDOWS daily


class SpecChanged(ValueError):
    """The spec no longer hashes to the sha256 its manifest quotes."""


def load_config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8")) or {}


def spec_sha256(cfg: dict) -> str:
    return manifest.batch_sha256(cfg["spec"])


def check_spec(cfg: dict) -> dict:
    """The spec, or SpecChanged: the horizon rule, the gate and everything else
    stay what the manifest hashed."""
    have = spec_sha256(cfg)
    if have != str(cfg.get("spec_sha256")):
        raise SpecChanged(f"config/alpha_reversion.yaml's spec hashes to {have}, not "
                          f"the {cfg.get('spec_sha256')} its manifest quotes: a changed "
                          f"spec is a new hypothesis, registered by its own manifest")
    return cfg["spec"]


def _prefix(xs: list[float]) -> list[float]:
    out = [0.0]
    for x in xs:
        out.append(out[-1] + x)
    return out


class _Points:
    """One stored close, by its stored days: the first vintage of each day and
    the instant it became knowable, for the fast point-in-time path; days with a
    later vintage, and days knowable after a later day (a late backfill), take
    the exact path."""

    def __init__(self, s: pit.Series) -> None:
        self.s = s
        self.days: list[str] = []
        self.val: list[float] = []
        self.fa: list[str] = []
        multi: list[int] = []
        for d in s.days:
            v = s.by[d]
            if v[0][1] <= 0:
                continue
            self.days.append(d)
            self.val.append(v[0][1])
            self.fa.append(v[0][0])
            multi.append(1 if len(v) > 1 else 0)
        self.lv = [math.log(x) for x in self.val]
        self.chg = [0.0] + [self.lv[i] - self.lv[i - 1] for i in range(1, len(self.lv))]
        self.s1 = _prefix(self.chg)
        self.s2 = _prefix([c * c for c in self.chg])
        self.multi = _prefix([float(m) for m in multi])
        self.fmax: list[str] = []
        for a in self.fa:
            self.fmax.append(max(a, self.fmax[-1]) if self.fmax else a)

    def regular(self, i0: int, i1: int, t: str) -> bool:
        """True when every day in [i0, i1] has one vintage and was knowable by t."""
        return (self.multi[i1 + 1] - self.multi[i0] == 0) and self.fmax[i1] <= t


def _z_exact(p: _Points, i: int, t: str, sp: dict) -> Optional[float]:
    """The print's z against its trailing window as known at t, vintage by vintage."""
    day = p.days[i]
    known = [(d, v) for d, v in p.s.known(t) if d <= day and v > 0]
    if not known or known[-1][0] != day:
        return None
    lo = (dt.date.fromisoformat(day)
          - dt.timedelta(days=int(sp["print"]["window_calendar_days"]))).isoformat()
    ch = [(known[k - 1][0], math.log(known[k][1] / known[k - 1][1]))
          for k in range(1, len(known))]
    hist = [c for d0, c in ch[:-1] if d0 >= lo]
    if len(hist) < int(sp["print"]["min_observations"]):
        return None
    mu = sum(hist) / len(hist)
    sd = math.sqrt(max(0.0, sum((c - mu) ** 2 for c in hist) / len(hist)))
    return (ch[-1][1] - mu) / sd if sd > 0 else None


def _close_at(p: _Points, i: int, t: str) -> Optional[float]:
    v = p.s.at(p.days[i], t)
    return v if v and v > 0 else None


def series_prints(p: _Points, symbol: str, sp: dict, as_of: str) -> list[dict]:
    """Every print of one series identified by as_of, point in time, each with its
    reversal at the spec's horizons where it has completed by as_of."""
    sig = float(sp["print"]["sigma"])
    need = int(sp["print"]["min_observations"])
    win = int(sp["print"]["window_calendar_days"])
    hs = [int(h) for h in sp["reversal"]["horizons_sessions"]]
    half = float(sp["reversal"]["half"])
    last = max(hs)
    cut = pit.canon(as_of)
    out = []
    for i in range(1, len(p.days)):
        if p.fa[i] > cut:
            break
        lo = (dt.date.fromisoformat(p.days[i]) - dt.timedelta(days=win)).isoformat()
        j0 = bisect.bisect_left(p.days, lo)
        n = i - 1 - j0
        fast = p.regular(j0, i, p.fa[i])
        if fast:
            if n < need:
                continue
            mu = (p.s1[i] - p.s1[j0 + 1]) / n
            var = (p.s2[i] - p.s2[j0 + 1]) / n - mu * mu
            sd = math.sqrt(var) if var > 0 else 0.0
            z = (p.chg[i] - mu) / sd if sd > 0 else None
            if z is None or abs(z) < sig:
                continue
        day_t, t = pit.nightly_after(p.fa[i])
        if t > cut:
            continue
        if not fast:
            z = _z_exact(p, i, t, sp)
            if z is None or abs(z) < sig:
                continue
        move = p.chg[i]
        if not fast:
            a, b = _close_at(p, i - 1, t), _close_at(p, i, t)
            move = math.log(b / a) if a and b else move
        sign = 1 if move > 0 else -1
        r = {"symbol": symbol, "bucket": f"{symbol}:{'+' if sign > 0 else '-'}",
             "sign": sign, "i": i, "day": p.days[i], "move": move, "z": z,
             "decided_day": day_t, "decided_at": t, "available_at": p.fa[i],
             "completed_at": None, "reversed": None}
        if i + last < len(p.days):
            _, tc = pit.nightly_after(p.fmax[i + last])
            if tc <= cut:
                if p.regular(i, i + last, tc):
                    base, at = p.lv[i], {h: p.lv[i + h] for h in hs}
                else:
                    b0 = _close_at(p, i, tc)
                    base = math.log(b0) if b0 else None
                    at = {h: (math.log(x) if (x := _close_at(p, i + h, tc)) else None)
                          for h in hs}
                if base is not None and all(v is not None for v in at.values()):
                    r["completed_at"] = tc
                    r["reversed"] = {h: sign * (base - at[h]) >= half * abs(move)
                                     for h in hs}
        out.append(r)
    return out


def formation(prints: list[dict], sp: dict) -> dict:
    """One bucket's state from its prints: awaiting below the gate; else the
    frozen horizon from its formation sample, its shares, and whether it fades."""
    k = int(sp["data_gate"]["min_formation_prints"])
    hs = [int(h) for h in sp["reversal"]["horizons_sessions"]]
    done = sorted((x for x in prints if x["completed_at"]),
                  key=lambda x: (x["completed_at"], x["day"]))
    if len(done) < k:
        return {"open": False, "n": len(done), "need": k,
                "line": f"awaiting (n={len(done)} of {k})"}
    form = done[:k]
    shares = {h: sum(1 for x in form if x["reversed"][h]) / k for h in hs}
    h = max(hs, key=lambda x: (shares[x], -x))
    fades = shares[h] >= float(sp["min_reversal_share"])
    line = (f"open: horizon {h} sessions, {shares[h]:.0%} of its formation prints at "
            f"least half reversed (n={k}); " +
            ("it fades" if fades else
             f"under {float(sp['min_reversal_share']):.0%}, it trades nothing"))
    return {"open": True, "n": len(done), "need": k, "horizon": h, "shares": shares,
            "fades": fades, "open_at": form[-1]["completed_at"],
            "formation_days": [x["day"] for x in form], "line": line}


class ReversionEngine(Engine):
    family = "reversion"
    horizon = "daily"
    cost_class = "etf"
    validated_ranges: dict = {}
    grid_size = 1

    def __init__(self, params: Optional[dict] = None) -> None:
        super().__init__(params)
        self.cfg = load_config(self.params.get("config"))
        self._symbols = self.params.get("symbols")
        self._opens: dict[str, pit.Series] = {}

    @property
    def spec(self) -> dict:
        return check_spec(self.cfg)

    # -- the universe -------------------------------------------------------
    def symbols(self) -> list[str]:
        from ..costs import CostModel                           # noqa: PLC0415
        classes = CostModel().classes
        syms = self._symbols or sorted(rules.price_symbols())
        return [s for s in syms if tradable(s) and trend_cost_class(s) in classes]

    def _instrument(self, sym: str) -> Instrument:
        return Instrument(id=sym, key=rules.resolve(sym), cost_class=trend_cost_class(sym),
                          meta={"fill_at": ("open" if sym in rules.ohlc_symbols()
                                            else "close")})

    def universe(self) -> list[Instrument]:
        return [self._instrument(s) for s in self.symbols()]

    def capital(self) -> float:
        return float(acfg.settings().get("notional_capital") or 100000) * \
            float(self.min_size or 0.02)

    # -- the buckets --------------------------------------------------------
    def _load(self, store) -> dict[str, _Points]:
        out = {}
        for s in self.symbols():
            ser = pit.Series(store, rules.resolve(s))
            if ser:
                out[s] = _Points(ser)
        return out

    def scan(self, store, as_of: str, pts: Optional[dict] = None) -> dict:
        """{bucket: {state..., "prints": [...]}} as knowable at as_of."""
        sp = self.spec
        pts = pts if pts is not None else self._load(store)
        by: dict[str, list[dict]] = {}
        for sym, p in pts.items():
            for r in series_prints(p, sym, sp, as_of):
                by.setdefault(r["bucket"], []).append(r)
        return {b: {**formation(xs, sp), "prints": xs} for b, xs in sorted(by.items())}

    def lines(self, store, as_of: str) -> list[str]:
        return [f"{b} {st['line']}" for b, st in self.scan(store, as_of).items()]

    # -- the trades ---------------------------------------------------------
    def _trade(self, p: _Points, r: dict, h: int, sym: str, store) -> Optional[dict]:
        i = r["i"]
        fill = "open" if sym in rules.ohlc_symbols() else "close"
        if i + 1 >= len(p.days):
            return None
        if fill == "open":
            if sym not in self._opens:
                self._opens[sym] = pit.Series(store, rules.resolve(sym, "open"))
            o = self._opens[sym].latest(p.days[i + 1])
            k_exit = i + h
            entry = o
        else:
            k_exit = i + 1 + h
            entry = p.s.latest(p.days[i + 1])
        if k_exit >= len(p.days) or not entry:
            return None
        ex = p.s.latest(p.days[k_exit])
        d = -r["sign"]
        days = (dt.date.fromisoformat(p.days[k_exit])
                - dt.date.fromisoformat(p.days[i + 1])).days
        return {"day": p.days[i + 1], "decided_at": r["decided_at"],
                "decided_day": r["decided_day"], "available_at": r["available_at"],
                "symbol": sym, "bucket": r["bucket"], "direction": d, "horizon": h,
                "print_day": r["day"], "z": r["z"], "fill_at": fill,
                "exit_day": p.days[k_exit], "price": entry, "exit_price": ex,
                "hold_days": days, "ret": d * (ex / entry - 1),
                "cost": self.cost(trend_cost_class(sym), d, entry, days)}

    def cost(self, cc: str, direction: int, px: float, days: float) -> float:
        """A trade's modelled cost as a fraction of notional: the round trip
        (half spread, slippage, commission each way) and the holding costs."""
        from ..costs import CostModel                           # noqa: PLC0415
        cm = CostModel()
        cap = self.capital()
        hold = cm.holding(cc, direction, 1.0, days)
        return round_trip(cm, cc, px, cap) + sum(hold.values())

    def refit_rows(self, store, as_of: str) -> list[dict]:
        """One row per traded print, point in time: prints of open, fading buckets
        identified after their formation completed, whose exit is knowable."""
        pts = self._load(store)
        today = session.session_date(as_of)
        rows = []
        for b, st in self.scan(store, as_of, pts).items():
            if not (st["open"] and st["fades"]):
                continue
            sym = b.rsplit(":", 1)[0]
            for r in st["prints"]:
                if r["decided_at"] <= st["open_at"]:
                    continue
                t = self._trade(pts[sym], r, st["horizon"], sym, store)
                if t and t["exit_day"] <= today:
                    rows.append(t)
        return sorted(rows, key=lambda x: (x["day"], x["symbol"]))

    def signal(self, as_of: str, store) -> list[Signal]:
        """Tonight's fades: prints identified today in open, fading buckets."""
        today = session.session_date(as_of)
        out = []
        for b, st in self.scan(store, as_of).items():
            if not (st["open"] and st["fades"]):
                continue
            sym = b.rsplit(":", 1)[0]
            for r in st["prints"]:
                if r["decided_day"] != today or r["decided_at"] <= st["open_at"]:
                    continue
                h = int(st["horizon"])
                fill = "open" if sym in rules.ohlc_symbols() else "close"
                stop = pit.next_session(r["day"], h if fill == "open" else h + 1)
                out.append(Signal(instrument=self._instrument(sym), direction=-r["sign"],
                                  as_of=as_of, strength=1.0,
                                  params={"time_stop_date": stop, "bucket": b,
                                          "horizon": h, "print_day": r["day"]}))
        for s in out:
            s.strength = 1.0 / len(out)
        return out

    def size(self, signal: Signal, risk_budget: float) -> float:
        return float(signal.strength)

    def exits(self, position: dict, bar) -> Optional[str]:
        return None

    # -- the harness's hooks ------------------------------------------------
    def strategy(self) -> av.Strategy:
        return av.Strategy(family=self.family, horizon=self.horizon,
                           fit=lambda rows: {},
                           returns=lambda rows, p: [r["ret"] - r["cost"] for r in rows])

    def coverage(self, store, as_of: str) -> dict:
        sc = self.scan(store, as_of)
        rows = self.refit_rows(store, as_of)
        need = acfg.min_signals(self.horizon)
        opened = [b for b, s in sc.items() if s["open"] and s["fades"]]
        ok = len(rows) >= need + FIT_ROWS
        lines = [f"{b} {s['line']}" for b, s in sc.items()]
        return {"n": len(rows), "need": need, "ok": ok, "wait": not ok,
                "buckets": {b: {k: v for k, v in s.items() if k != "prints"}
                            for b, s in sc.items()},
                "lines": lines,
                "why": ("history window met" if ok else
                        f"insufficient history: {len(rows)} traded prints in "
                        f"{len(opened)} open buckets; the harness needs {need} "
                        f"out-of-sample after a {FIT_ROWS}-trade fit; every other "
                        f"bucket is awaiting its 30 formation prints")}
