"""
Engine 7 -- intraday dealer regimes (X-3.4; the brief's roster item 7).

"After 6b's intraday captures and the state vector exist: opening-range and VWAP
behaviour conditioned on the gamma regime and 0DTE flow. The Enterprise Layer's
own dealer engine stays the Doctrine's, under Part VIII's rules; this is the
lab's." Registered as `intraday_dealer` (config/alpha_engines.yaml); its
hypothesis E-7 is pre-registered by manifest (alpha/research/
roster-2026-10-19-x3-4.yaml), and every rule below is
config/alpha_intraday_dealer.yaml's `spec`, whose sha256 the roster quotes.

WHAT IT READS, all our own: the 09:45 captures' computed exposure profiles (the
gamma regime as 6b's keys define it: net GEX's sign where net-to-gross is at least
0.10), each capture's spot print, the session's stored open and close, the
5-minute bars, and the 0DTE share of the captured volume, labelled "no side". No
vendor value: no FlashAlpha key, no data/vendor file.

WHAT IT CANNOT READ, and says so: VWAP and a finer opening range need intraday
bars knowable at the decision, and the bars table is written after the close.
Those legs print "not tracked"; the writer they need is listed, not built.

THE CLOCKS. A capture is knowable at its computed_at; one computed after the
slot's decision deadline (10:15 ET) is never read. A price is read at its market
time: the open at 09:30 ET, a bar at its start. The entry is the open of the first
stored 5-minute bar starting at or after the decision, within 10 minutes, else no
trade -- never a price observed before the decision.

THE BUCKET is the symbol, the 09:45 gamma regime and the sign of the open-to-09:45
move. Its formation sample is its first 30 completed sessions, counted from the
captures' first day; below 30 it prints "awaiting (n=k of 30)" and trades nothing.
At 30, the side (continuation or reversal) and the exit (12:30 or the close) with
the best mean net of costs in that sample is frozen, and only later sessions trade,
and only where that mean is above zero.

A RESEARCH ENGINE. The nightly loop cannot act at 09:45, so signal() queues
nothing; the record is the point-in-time backtest through the harness until an
intraday fill path exists. The engine writes nothing; promotion is the gate's.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
from pathlib import Path
from typing import Optional

import yaml

from altdata import session

from .. import config as acfg
from .. import manifest, pit, rules
from .. import validate as av
from ..engine import Engine, Instrument, Signal
from .events import round_trip

CONFIG = acfg.REPO / "config" / "alpha_intraday_dealer.yaml"
FIT_ROWS = 60
ET = "America/New_York"
COMBOS = (("reversal", "exit_1230"), ("continuation", "exit_1230"),
          ("reversal", "exit_close"), ("continuation", "exit_close"))


class SpecChanged(ValueError):
    """The spec no longer hashes to the sha256 its manifest quotes."""


def load_config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8")) or {}


def spec_sha256(cfg: dict) -> str:
    return manifest.batch_sha256(cfg["spec"])


def check_spec(cfg: dict) -> dict:
    have = spec_sha256(cfg)
    if have != str(cfg.get("spec_sha256")):
        raise SpecChanged(f"config/alpha_intraday_dealer.yaml's spec hashes to {have}, "
                          f"not the {cfg.get('spec_sha256')} its manifest quotes: a "
                          f"changed spec is a new hypothesis, registered by its own "
                          f"manifest")
    return cfg["spec"]


def computed_dir() -> Path:
    """The captures' computed directory (CHESTER_COMPUTED_DIR, as altdata/config.py
    reads it), never a vendor directory."""
    raw = os.environ.get("CHESTER_COMPUTED_DIR", "data/computed")
    p = Path(raw).expanduser()
    return p if p.is_absolute() else acfg.REPO / p


def _et(instant: str) -> dt.datetime:
    from zoneinfo import ZoneInfo                               # noqa: PLC0415
    return dt.datetime.fromisoformat(str(instant).replace("Z", "+00:00")).astimezone(
        ZoneInfo(ET))


def _at_et(day: str, hhmm: str) -> str:
    from zoneinfo import ZoneInfo                               # noqa: PLC0415
    h, m = (int(x) for x in hhmm.split(":"))
    local = dt.datetime.combine(dt.date.fromisoformat(day), dt.time(h, m), ZoneInfo(ET))
    return pit.canon(local.isoformat())


def zero_dte_share(chain_csv: Optional[str]) -> Optional[float]:
    """The dte-0 rows' share of the capture's volume; None where unreadable."""
    if not chain_csv or not Path(chain_csv).is_file():
        return None
    tot = zero = 0.0
    with open(chain_csv, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            try:
                v = float(r.get("volume") or 0)
                d = int(float(r.get("dte") or -1))
            except ValueError:
                continue
            tot += v
            zero += v if d == 0 else 0.0
    return zero / tot if tot > 0 else None


def regime(doc: dict, sp: dict) -> Optional[str]:
    ov = doc.get("overall") or {}
    g, r = ov.get("net_gex"), ov.get("net_to_gross")
    if g is None or r is None or abs(float(r)) < float(sp["gamma_regime"]["min_net_to_gross"]):
        return None
    if float(g) > 0:
        return "positive"
    if float(g) < 0:
        return "negative"
    return None


def captures(sym: str, sp: dict, root: Optional[Path] = None) -> dict[str, dict]:
    """{session: the 09:45 capture usable for its decision}: the earliest file in
    the slot's window whose computed_at is at or before the deadline. A capture
    computed after the deadline is never read."""
    root = Path(root or computed_dir())
    lo, hi = sp["slot"]["window_et"]
    out: dict[str, dict] = {}
    if not root.is_dir():
        return out
    for day_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        day = day_dir.name
        dead = _at_et(day, sp["slot"]["decision_deadline_et"])
        for f in sorted(day_dir.glob(f"{sym}_*_exposure.json")) + \
                sorted(day_dir.glob(f"{sym}_*_gex.json")):
            try:
                doc = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            fa, ca = doc.get("fetched_at"), doc.get("computed_at")
            if not fa or not ca or doc.get("capture") == "settled_eod":
                continue
            t = _et(fa).strftime("%H:%M")
            if not (lo <= t <= hi) or pit.canon(ca) > dead:
                continue
            if day in out and out[day]["computed_at"] <= pit.canon(ca):
                continue
            out[day] = {"session": day, "file": str(f), "fetched_at": pit.canon(fa),
                        "computed_at": pit.canon(ca), "spot": doc.get("spot"),
                        "regime": regime(doc, sp),
                        "zero_dte_share": zero_dte_share(doc.get("source_chain"))}
    return out


class IntradayDealerEngine(Engine):
    family = "intraday_dealer"
    horizon = "daily"
    cost_class = "etf"
    validated_ranges: dict = {}
    grid_size = 1

    def __init__(self, params: Optional[dict] = None) -> None:
        super().__init__(params)
        self.cfg = load_config(self.params.get("config"))
        self.root = self.params.get("computed_dir")

    @property
    def spec(self) -> dict:
        return check_spec(self.cfg)

    def symbols(self) -> list[str]:
        return [str(s).upper() for s in self.spec["instruments"]]

    def universe(self) -> list[Instrument]:
        return [Instrument(id=s, key=rules.resolve(s), cost_class="etf",
                           meta={"fill_at": "intraday 5-minute bar open"})
                for s in self.symbols()]

    def capital(self) -> float:
        return float(acfg.settings().get("notional_capital") or 100000) * \
            float(self.min_size or 0.02)

    def cost(self, px: float) -> float:
        """One session's round trip as a fraction of notional (etf class; no
        holding cost)."""
        from ..costs import CostModel                           # noqa: PLC0415
        return round_trip(CostModel(), "etf", px, self.capital())

    # -- one session --------------------------------------------------------
    def session_row(self, store, sym: str, cap: dict, as_of: str) -> Optional[dict]:
        sp = self.spec
        day = cap["session"]
        if not cap["regime"] or not cap.get("spot"):
            return None
        op = pit.Series(store, rules.resolve(sym, "open")).first_vintage(day)
        cl = pit.Series(store, rules.resolve(sym)).first_vintage(day)
        if not op or not cl or not op[0]:
            return None
        move = float(cap["spot"]) - float(op[0])
        if move == 0:
            return None
        sign = 1 if move > 0 else -1
        bars = store.intraday_bars(sym.lower(), "5m", cap["computed_at"],
                                   _at_et(day, "16:00"), as_of)
        wait = dt.timedelta(minutes=int(sp["max_entry_wait_minutes"]))
        entry = next((b for b in bars if pit.canon(b["observed_at"]) >= cap["computed_at"]),
                     None)
        if entry is None or entry.get("open") is None or (
                dt.datetime.fromisoformat(pit.canon(entry["observed_at"]))
                - dt.datetime.fromisoformat(cap["computed_at"])) > wait:
            return {"session": day, "symbol": sym, "complete": False,
                    "why": "no stored price near the decision"}
        t1230 = _at_et(day, "12:30")
        b1230 = next((b for b in bars if pit.canon(b["observed_at"]) >= t1230), None)
        if b1230 is None or b1230.get("open") is None:
            return {"session": day, "symbol": sym, "complete": False,
                    "why": "no stored 12:30 bar"}
        px = float(entry["open"])
        c = self.cost(px)
        exits = {"exit_1230": float(b1230["open"]), "exit_close": float(cl[0])}
        rets = {}
        for side, ex in COMBOS:
            d = sign if side == "continuation" else -sign
            rets[f"{side}|{ex}"] = d * (exits[ex] / px - 1.0) - c
        return {"session": day, "symbol": sym, "complete": True,
                "bucket": f"{sym}:{cap['regime']}:{'+' if sign > 0 else '-'}",
                "decided_at": cap["computed_at"], "capture": cap["file"],
                "entry_bar": pit.canon(entry["observed_at"]), "entry": px,
                "exits": exits, "net": rets, "cost": c, "sign": sign,
                "zero_dte_share": cap.get("zero_dte_share"), "zero_dte_label": "no side"}

    def scan(self, store, as_of: str) -> dict:
        """{bucket: state and its completed sessions} as knowable at as_of."""
        sp = self.spec
        k = int(sp["data_gate"]["min_formation_sessions"])
        today = session.session_date(as_of)
        by: dict[str, list[dict]] = {}
        for sym in self.symbols():
            for day, cap in sorted(captures(sym, sp, self.root).items()):
                if day > today:
                    continue
                r = self.session_row(store, sym, cap, as_of)
                if r and r.get("complete"):
                    by.setdefault(r["bucket"], []).append(r)
        out = {}
        for b, rows in sorted(by.items()):
            rows.sort(key=lambda x: x["session"])
            if len(rows) < k:
                out[b] = {"open": False, "n": len(rows), "line": f"awaiting (n={len(rows)} of {k})",
                          "rows": rows}
                continue
            form = rows[:k]
            means = {f"{s}|{e}": sum(x["net"][f"{s}|{e}"] for x in form) / k for s, e in COMBOS}
            best = max(COMBOS, key=lambda c: (means[f"{c[0]}|{c[1]}"], -COMBOS.index(c)))
            key = f"{best[0]}|{best[1]}"
            trades = means[key] > 0
            out[b] = {"open": True, "n": len(rows), "side": best[0], "exit": best[1],
                      "mean": means[key], "means": means, "trades": trades,
                      "open_after": form[-1]["session"], "rows": rows,
                      "line": (f"open: {best[0]} to {best[1]}, formation mean "
                               f"{means[key]:+.4%} net of costs (n={k}); "
                               + ("it trades" if trades else "not above 0, it trades nothing"))}
        return out

    def lines(self, store, as_of: str) -> list[str]:
        sp = self.spec
        out = [f"{b} {s['line']}" for b, s in self.scan(store, as_of).items()]
        return out + [f"{k}: {v}" for k, v in sp["not_tracked"].items()]

    def refit_rows(self, store, as_of: str) -> list[dict]:
        rows = []
        for b, st in self.scan(store, as_of).items():
            if not (st["open"] and st["trades"]):
                continue
            key = f"{st['side']}|{st['exit']}"
            for r in st["rows"]:
                if r["session"] <= st["open_after"]:
                    continue
                rows.append({"day": r["session"], "decided_at": r["decided_at"],
                             "available_at": r["decided_at"], "symbol": r["symbol"],
                             "bucket": b, "side": st["side"], "exit": st["exit"],
                             "ret": r["net"][key] + r["cost"], "cost": r["cost"],
                             "zero_dte_share": r["zero_dte_share"]})
        return sorted(rows, key=lambda x: (x["day"], x["symbol"]))

    def signal(self, as_of: str, store) -> list[Signal]:
        """None: the nightly loop cannot act at 09:45 (the spec's `paper`)."""
        return []

    def size(self, signal: Signal, risk_budget: float) -> float:
        return float(signal.strength or 0.0)

    def exits(self, position: dict, bar) -> Optional[str]:
        return None

    def strategy(self) -> av.Strategy:
        return av.Strategy(family=self.family, horizon=self.horizon,
                           fit=lambda rows: {},
                           returns=lambda rows, p: [r["ret"] - r["cost"] for r in rows])

    def coverage(self, store, as_of: str) -> dict:
        sc = self.scan(store, as_of)
        rows = self.refit_rows(store, as_of)
        need = acfg.min_signals(self.horizon)
        ok = len(rows) >= need + FIT_ROWS
        return {"n": len(rows), "need": need, "ok": ok, "wait": not ok,
                "buckets": {b: {k: v for k, v in s.items() if k != "rows"}
                            for b, s in sc.items()},
                "lines": self.lines(store, as_of),
                "why": ("history window met" if ok else
                        f"insufficient history: {len(rows)} traded sessions; the "
                        f"harness needs {need} out-of-sample after a {FIT_ROWS}-trade "
                        f"fit; every other bucket is awaiting its 30 formation sessions")}


def _main(argv: list[str]) -> int:
    """python -m alpha.engines.intraday_dealer lines [--store PATH] [--as-of ISO]:
    each bucket's state and the legs not tracked, read-only."""
    import argparse                                             # noqa: PLC0415
    import sys                                                  # noqa: PLC0415
    from ..store import ReadOnlyStore                           # noqa: PLC0415
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m alpha.engines.intraday_dealer")
    ap.add_argument("cmd", choices=["lines"])
    ap.add_argument("--store")
    ap.add_argument("--as-of")
    a = ap.parse_args(argv)
    st = ReadOnlyStore(a.store)
    try:
        out = IntradayDealerEngine().lines(st, a.as_of or session.utc_iso(
            timespec="microseconds"))
    finally:
        st.close()
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(_main(_sys.argv[1:]))
