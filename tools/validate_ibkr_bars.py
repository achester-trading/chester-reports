#!/usr/bin/env python3
"""
Validation gate: the IBKR daily-bars writer, tranche 1 of the price-source
migration (A93; the brief docs/briefs/price-source-migration-brief-2026-10-25.md,
ruled D38). Fixtures only: a fake client and a fake Security Master. Nothing
here imports ib_async or contacts a gateway.

  A  CONTRACTS      an instrument resolves to the Security Master's ibkr_conid; one
                    without a conid, unknown or restricted is skipped and named, never
                    guessed; the real master today carries none, so every one is named
  B  PACING         at most 60 requests in any ten minutes, held in code: the 61st
                    waits for the first to leave the window, and fetch() paces each
  C  POINT IN TIME  a live bar is knowable at its close plus the declared delay and
                    never before its pull; a backfill row is close + delay, marked
                    reconstructed; an FX bar closes at the end of the UTC day
  D  STALE          no subscription is STALE "market data subscription not present";
                    no gateway is STALE with its reason; a partial refusal names the
                    refused instrument and writes the rest
  E  SWITCHED OFF   disabled, the writer connects to nothing and writes nothing, and
                    the feed run's external step does not call it
  F  KEYS           every key is ibkr.<stem>_<field>, none is a yfinance key, and
                    each close pairs by stem with the yfinance close it would replace
"""

from __future__ import annotations

import copy
import datetime as dt
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

from altdata import observations                               # noqa: E402
from altdata.sources import ibkr_bars as ib                    # noqa: E402

TD = Path(gate_mkdtemp("ibkr_bars_"))
LINE = "=" * 78
PASS = FAIL = 0
CONIDS = {"SPY": 756733, "QQQ": 320227571, "IWM": 9579970, "DIA": 73128548,
          "RSP": 1001}                     # SYNTHETIC conids for the fixture


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


class FakeMaster:
    """The Security Master's resolve(), with conids where the fixture gives them."""

    def __init__(self, conids: dict, restricted=()) -> None:
        self.conids, self.restricted = conids, set(restricted)

    def resolve(self, ident, scheme, on=None):
        from altdata import security_master as sm               # noqa: PLC0415
        if ident not in self.conids and ident not in self.restricted:
            raise sm.NotFound(ident)
        ids = {"yahoo": ident}
        if self.conids.get(ident) is not None:
            ids["ibkr_conid"] = self.conids[ident]
        return {"id": f"SMFAKE{ident}", "identifiers": ids,
                "restricted": ident in self.restricted}


class FakeEvent(list):
    def __iadd__(self, fn):
        self.append(fn)
        return self


class FakeClient:
    """reqHistoricalData by conid; an entitlement refusal fires errorEvent."""

    def __init__(self, bars_by_conid: dict, refuse=()) -> None:
        self.bars, self.refuse = bars_by_conid, set(refuse)
        self.errorEvent = FakeEvent()
        self.requests, self.disconnected = [], False

    def reqHistoricalData(self, contract, **kw):
        self.requests.append((contract.conId, kw))
        if contract.conId in self.refuse:
            for fn in self.errorEvent:
                fn(1, 354, "Requested market data is not subscribed.", contract)
            return []
        return self.bars.get(contract.conId, [])

    def disconnect(self):
        self.disconnected = True


def bar(day: str, o, h, lo, c):
    return SimpleNamespace(date=dt.date.fromisoformat(day), open=o, high=h, low=lo,
                           close=c, volume=1000)


def cfg_on() -> dict:
    c = copy.deepcopy(ib.config())
    c["enabled"] = True
    return c


class Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def now(self) -> float:
        return self.t

    def sleep(self, s: float) -> None:
        self.t += s


def group_a() -> None:
    head("A. CONTRACTS")
    inst = {"symbol": "SPY", "stem": "spy", "availability": "ny_close",
            "what_to_show": "TRADES", "family": "us_index_funds"}
    conid, why = ib.resolve(inst, FakeMaster(CONIDS))
    check(conid == CONIDS["SPY"], f"SPY resolves to its conid through the master ({conid})")
    conid, why = ib.resolve(inst, FakeMaster({"SPY": None}))
    check(conid is None and "no ibkr_conid" in why, f"no conid: skipped, named ({why})")
    conid, why = ib.resolve(dict(inst, symbol="ZZZZ"), FakeMaster(CONIDS))
    check(conid is None and "not in the Security Master" in why, f"unknown: {why}")
    conid, why = ib.resolve(inst, FakeMaster({}, restricted={"SPY"}))
    check(conid is None and "restricted" in why, f"restricted: refused ({why})")
    plan = "\n".join(ib.plan())
    check("enabled: False" in plan and plan.count("SKIP:") == 5
          and "has no ibkr_conid" in plan,
          "the real Security Master carries no conid today: all five are named, none guessed")


def group_b() -> None:
    head("B. PACING")
    clk = Clock()
    p = ib.Pacer(60, 600, clock=clk.now, sleep=clk.sleep)
    waits = [p.wait() for _ in range(60)]
    check(all(w == 0 for w in waits) and clk.t == 0, "sixty requests go at once")
    w = p.wait()
    check(w >= 600 and clk.t >= 600, f"the 61st waits for the first to leave the window ({w:.2f} s)")
    times = sorted(p.sent)
    check(all(sum(1 for x in times if s <= x < s + 600) <= 60 for s in times),
          "no ten-minute window holds more than sixty")
    clk2 = Clock()
    p2 = ib.Pacer(2, 600, clock=clk2.now, sleep=clk2.sleep)
    cli = FakeClient({c: [bar("2026-10-28", 1, 2, 0.5, 1.5)] for c in CONIDS.values()})
    ib.fetch(cfg_on(), cli, FakeMaster(CONIDS), p2, pulled_at="2026-10-29T01:00:00+00:00")
    check(len(cli.requests) == 5 and clk2.t >= 1200,
          f"fetch() paces every request (5 requests at 2 per window waited {clk2.t:.0f} s)")
    check(ib.config()["pacing"] == {"max_requests": 60, "window_seconds": 600},
          "the config's pacing is IBKR's limit: 60 in ten minutes")


def group_c() -> None:
    head("C. POINT IN TIME")
    # 28 Oct 2026 is EDT: the close is 20:00 UTC; the delay is the config's 30.
    early = ib.available_at("2026-10-28", "ny_close", 30, "2026-10-28T20:05:00+00:00")
    late = ib.available_at("2026-10-28", "ny_close", 30, "2026-10-29T01:00:00+00:00")
    recon = ib.available_at("2026-10-28", "ny_close", 30)
    check(early.startswith("2026-10-28T20:30"), f"a pull before close + delay is stamped at close + delay ({early})")
    check(late.startswith("2026-10-29T01:00"), f"a later pull is stamped at the pull ({late})")
    check(recon.startswith("2026-10-28T20:30"), f"a backfill row is close + delay ({recon})")
    winter = ib.available_at("2026-12-15", "ny_close", 30)
    check(winter.startswith("2026-12-15T21:30"), f"the close follows the clock change (EST: {winter})")
    fx = ib.available_at("2026-10-28", "utc_day", 30)
    check(fx.startswith("2026-10-29T00:30"), f"an FX bar closes at the end of the UTC day ({fx})")
    inst = ib.instruments(cfg_on())[0]
    live = ib.rows_from_bars(inst, [bar("2026-10-28", 1, 2, 0.5, 1.5)], ib.FIELDS, 30,
                             "2026-10-29T01:00:00+00:00", False)
    back = ib.rows_from_bars(inst, [bar("2026-10-28", 1, 2, 0.5, 1.5)], ib.FIELDS, 30,
                             "2026-10-29T01:00:00+00:00", True)
    check(len(live) == 4 and {r["availability_kind"] for r in live} == {"observed"}
          and {r["availability_kind"] for r in back} == {"reconstructed"}
          and all(r["available_at"] >= "2026-10-28T20:30" for r in live + back),
          "live rows are observed, backfill rows reconstructed; none before close + delay")


def store(name: str):
    return observations.ObservationStore(str(TD / f"{name}.db"))


def count(name: str) -> int:
    p = TD / f"{name}.db"
    if not p.exists():
        return 0
    with sqlite3.connect(p) as c:
        try:
            return c.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        except sqlite3.OperationalError:
            return 0


def group_d() -> None:
    head("D. STALE")
    cli = FakeClient({}, refuse=set(CONIDS.values()))
    with store("nosub") as st:
        r = ib.pull(db=st, client=cli, master=FakeMaster(CONIDS), cfg=cfg_on(),
                    pacer=ib.Pacer(60, 600, clock=lambda: 0.0, sleep=lambda s: None))
    check(r.get("status") == "STALE" and ib.NO_SUBSCRIPTION in str(r.get("reason")),
          f"no subscription: STALE with its reason ({r.get('status')}: {r.get('reason')})")

    def refused_factory():
        class NoGateway:
            def connect(self, *a, **k):
                raise ConnectionRefusedError("nothing listening")
        return NoGateway()
    with store("nogw") as st:
        r2 = ib.pull(db=st, cfg=cfg_on(), master=FakeMaster(CONIDS),
                     ib_factory=refused_factory)
    check(r2.get("status") == "STALE" and "no gateway" in str(r2.get("reason")),
          f"no gateway: STALE ({r2.get('reason')})")
    good = {c: [bar("2026-10-27", 1, 2, 0.5, 1.5), bar("2026-10-28", 1.5, 2.5, 1, 2)]
            for c in CONIDS.values()}
    cli3 = FakeClient(good, refuse={CONIDS["RSP"]})
    with store("partial") as st:
        r3 = ib.pull(db=st, client=cli3, master=FakeMaster(CONIDS), cfg=cfg_on(),
                     pacer=ib.Pacer(60, 600, clock=lambda: 0.0, sleep=lambda s: None))
    check(r3.get("status") == "OK" and r3.get("written") == 32
          and any("RSP" in s and ib.NO_SUBSCRIPTION in s for s in r3.get("skipped") or []),
          f"one refused, four written: 4 x 2 days x 4 fields = 32 rows, RSP named "
          f"({r3.get('written')}, {r3.get('skipped')})")


def group_e() -> None:
    head("E. SWITCHED OFF")
    check(ib.config()["enabled"] is False and not ib.enabled(),
          "config/ibkr_bars.yaml ships enabled: false")
    cli = FakeClient({c: [bar("2026-10-28", 1, 2, 0.5, 1.5)] for c in CONIDS.values()})
    with store("off") as st:
        r = ib.pull(db=st, client=cli, master=FakeMaster(CONIDS))
    check(r.get("status") == "DISABLED" and r.get("written") == 0 and not cli.requests
          and count("off") == 0,
          f"disabled: no request, no row ({r.get('status')}, {len(cli.requests)} requests)")
    from altdata import feeds                                   # noqa: PLC0415
    check(feeds._switched_writers() == [] and "ibkr_bars" not in feeds.EXTERNAL_WRITERS,  # noqa: SLF001
          "the feed run's external step does not call it, and it is on no roster")
    real = ib.enabled
    ib.enabled = lambda cfg=None: True
    try:
        on = [n for n, _ in feeds._switched_writers()]              # noqa: SLF001
    finally:
        ib.enabled = real
    check(on == ["ibkr_bars"], "enabled, the external step calls it")


def group_f() -> None:
    head("F. KEYS")
    from altdata.sources import yfinance_source as yf          # noqa: PLC0415
    yf_keys = {f"yfinance.{v}" for v in yf.SYMBOLS.values()}
    check(all(k.startswith("ibkr.") for k in ib.DECLARED_KEYS)
          and not (set(ib.DECLARED_KEYS) & yf_keys),
          f"{len(ib.DECLARED_KEYS)} declared keys, all ibkr.*, none a yfinance key")
    check(ib.KEYS == [f"ibkr.{s}_{f}" for s in ("spy", "qqq", "iwm", "dia", "rsp")
                      for f in ("open", "high", "low", "close")],
          "the first family is SPY, QQQ, IWM, DIA and RSP, open to close")
    pairs = {f"ibkr.{ib.stem(s)}_close": f"yfinance.{yf.SYMBOLS[s]}"
             for s in ("SPY", "QQQ", "IWM", "DIA", "RSP")}
    check(all(v in yf_keys for v in pairs.values()),
          "each close pairs by stem with the yfinance close it would replace")
    import yaml                                                 # noqa: PLC0415
    dq = yaml.safe_load((REPO / "config" / "data_quality.yaml").read_text(encoding="utf-8"))
    ip = (dq.get("inactive_pairs") or {}).get("list") or []
    active_ids = {p.get("b") for p in (dq.get("pairs") or {}).get("list") or []}
    check(len(ip) == 5 and all(p["active"] is False and "measured on the overlap" in p["tolerance"]
                               and pairs.get(p["b"]) == p["a"] for p in ip)
          and not any(str(b).startswith("ibkr.") for b in active_ids),
          "the five pairs are declared inactive, tolerance to be measured, none in the active list")
    from altdata import derived                                 # noqa: PLC0415
    e = derived.registry_entry("ibkr.spy_close")
    check(e.get("source") == "ibkr_bars" and e.get("status_extra") == "not_yet_sourced",
          f"the registry knows the keys, not yet sourced ({e.get('source')}, {e.get('status_extra')})")


def main() -> int:
    try:
        for g in (group_a, group_b, group_c, group_d, group_e, group_f):
            g()
    finally:
        import shutil                                           # noqa: PLC0415
        shutil.rmtree(TD, ignore_errors=True)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
