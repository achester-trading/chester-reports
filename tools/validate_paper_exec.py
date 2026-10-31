#!/usr/bin/env python3
"""
Validation gate: the paper-only IBKR executor (A98; D43, 31 Oct 2026). Fixtures
only: a fake gateway, a temporary ledger and state directory. No connection is
made and no order is sent.

  A  OFF          enabled false: nothing connects; status says "paper executor off"
  B  PAPER ONLY   a live port never connects; a non-DU account aborts before any
                  order object is built
  C  DRY          dry by default: built and logged, nothing sent; sending needs
                  both flags
  D  BRACKETS     no entry without its stop and target; the send path refuses
                  anything but a whole, tied bracket
  E  SIZE         MES only (ES refused by contract); a missing conid is skipped and
                  named; the ceiling, the governor and the heat cap
  F  KILL         a kill file stops sending within one loop and stays until the
                  operator clears it
  G  LEDGER       the fill row's shape (source, venue order id, fill time); an older
                  ledger gains the fields in place; entry opens, exit closes and grades
  H  RECONCILE    a mismatch at start stops sending and names itself
  I  BOUNDARIES   the package sits outside alpha/; the order calls live in the one
                  send path; its client id; its commands are denied to sessions
"""

from __future__ import annotations

import copy
import datetime as dt
import os
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gate_tmp                                                 # noqa: E402

TD = Path(gate_tmp.mkdtemp("paper_exec_"))
os.environ["CHESTER_STATE_DIR"] = str(TD / "state")
os.environ["ALPHA_DB"] = str(TD / "alpha.db")

from paper_exec import client, contracts, executor, orders      # noqa: E402
from paper_exec import config as pcfg                           # noqa: E402
from paper_exec.state import State                              # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0


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


# ---------------------------------------------------------------------------
# The fakes
# ---------------------------------------------------------------------------
class FakeIB:
    """A gateway that records everything and sends nothing anywhere."""

    def __init__(self, accounts=("DU1234567",), positions=(), trades=(), fills=()):
        self.accounts = list(accounts)
        self._positions, self._trades, self._fills = list(positions), list(trades), list(fills)
        self.connected = None
        self.brackets = 0
        self.placed: list = []
        self.disconnected = False
        self.next_id = 100
        self.on_place = None

    def connect(self, host, port, clientId, timeout, readonly):
        self.connected = {"host": host, "port": port, "clientId": clientId,
                          "readonly": readonly}

    def managedAccounts(self):
        return self.accounts

    def positions(self):
        return self._positions

    def openTrades(self):
        return self._trades

    def fills(self):
        return self._fills

    def bracketOrder(self, action, qty, limit, take, stop):
        self.brackets += 1
        pid = self.next_id
        self.next_id += 3
        rev = "SELL" if action == "BUY" else "BUY"
        return [SimpleNamespace(orderId=pid, parentId=0, action=action, totalQuantity=qty,
                                lmtPrice=limit, orderRef=""),
                SimpleNamespace(orderId=pid + 1, parentId=pid, action=rev,
                                totalQuantity=qty, lmtPrice=take, orderRef=""),
                SimpleNamespace(orderId=pid + 2, parentId=pid, action=rev,
                                totalQuantity=qty, auxPrice=stop, orderRef="")]

    def placeOrder(self, contract, order):
        self.placed.append((contract, order))
        if self.on_place:
            self.on_place(self)

    def disconnect(self):
        self.disconnected = True


class FakeMaster:
    def __init__(self, conid="654321"):
        self.conid = conid

    def resolve(self, ident, scheme):
        if ident != "MES":
            raise KeyError(ident)
        ids = {"ticker": "MES"} | ({"ibkr_conid": self.conid} if self.conid else {})
        return {"id": "SM_TEST_MES", "identifiers": ids, "restricted": False}


def cfg(**kw) -> dict:
    c = copy.deepcopy(pcfg.load())
    c.update(kw)
    return c


LIMITS = {"capital_usd": {"value": 300000}, "limits": {"heat_max_pct": {"value": 6}}}


def intent(**kw) -> orders.Intent:
    base = dict(engine_id="eng_t", signal_id=1, symbol="MES", side=1, entry=6000.0,
                stop=5980.0, target=6040.0)
    base.update(kw)
    return orders.Intent(**base)


def ledger():
    from alpha.ledger import Ledger
    lg = Ledger(TD / f"alpha_{len(list(TD.glob('alpha_*.db')))}.db")
    lg.upsert_engine("eng_t", "trend", "daily", "live", 1.0, "2026-10-31T00:00:00+00:00",
                     validated_metrics={"expectancy": 0.004, "sd": 0.02, "n_signals": 400})
    for _ in range(2):          # signals 1 and 2: the lab's, which the intents name
        lg.add_signal("eng_t", "MES", 1, 0.1, "2026-10-31T00:00:00+00:00",
                      stop_price=5980.0, target_price=6040.0, params={"entry": 6000.0})
    return lg


def fresh_state() -> None:
    st = State(pcfg.state_dir(pcfg.load()))
    for p in (st.root.glob("*") if st.root.is_dir() else []):
        p.unlink()


def run(c, ints, ib=None, master=None, lg=None):
    ib = ib or FakeIB()
    lg = lg or ledger()
    made = []

    def factory():
        made.append(ib)
        return ib
    rep = executor.run(ints, c, lg, ib_factory=factory, master=master or FakeMaster(),
                       limits=LIMITS)
    return rep, ib, made, lg


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. OFF")
    shipped = pcfg.load()
    check(shipped.get("enabled") is False and shipped.get("dry_run") is True,
          "the shipped config: enabled false, dry_run true")
    rep, ib, made, _ = run(shipped, [intent()])
    check(rep["state"] == "paper executor off" and not made and ib.connected is None,
          "while off, nothing connects (the gateway is never even constructed)")
    from paper_exec.__main__ import status_lines
    check(status_lines(shipped) == ["paper executor off"],
          "the status command prints 'paper executor off'")
    try:
        client.connect(shipped, lambda: FakeIB())
        check(False, "connect() refuses while off")
    except client.Off:
        check(True, "connect() itself refuses while off")


def group_b() -> None:
    head("B. PAPER ONLY")
    fresh_state()
    for port in (4001, 7496):
        rep_ok = True
        made = []
        try:
            client.connect(cfg(enabled=True, port=port), lambda: made.append(1) or FakeIB())
            rep_ok = False
        except client.LivePort:
            pass
        check(rep_ok and not made, f"live port {port}: refused before any connection")
    for accts in (("U7654321",), ("DU1234567", "U7654321"), ()):
        ib = FakeIB(accounts=accts)
        try:
            run(cfg(enabled=True, dry_run=False), [intent()], ib=ib)
            refused = False
        except client.LiveAccount:
            refused = True
        check(refused and ib.disconnected and ib.brackets == 0 and not ib.placed,
              f"accounts {list(accts) or 'none'}: aborted and disconnected before any "
              f"order object is built")
    import logging
    rec: list = []
    h = logging.Handler()
    h.emit = lambda r: rec.append(r.getMessage())
    logging.getLogger("paper_exec.client").addHandler(h)
    try:
        client.check_accounts(["U1"], cfg(enabled=True))
    except client.LiveAccount:
        pass
    check(any("aborting before any order is built" in x and "U1" in x for x in rec),
          "the reason is logged")
    rep, ib, _, _ = run(cfg(enabled=True), [intent()])
    check(ib.connected and ib.connected["port"] == 4002 and ib.connected["clientId"] == 21
          and ib.connected["readonly"] is True,
          "a DU account on 4002 connects, client id 21, read-only while dry")


def group_c() -> None:
    head("C. DRY BY DEFAULT")
    fresh_state()
    c = cfg(enabled=True)
    c.pop("dry_run", None)
    check(pcfg.mode(c) == "dry" and pcfg.mode(cfg(enabled=True, dry_run=True)) == "dry"
          and pcfg.mode(cfg(enabled=False, dry_run=False)) == "off"
          and pcfg.mode(cfg(enabled=True, dry_run=False)) == "send",
          "enabled without dry_run is dry; sending needs both flags (enabled true, "
          "dry_run false)")
    rep, ib, _, _ = run(c, [intent()])
    st = State(pcfg.state_dir(c))
    log = st.orders()
    check(rep["results"][0]["state"].startswith("dry") and not ib.placed and ib.brackets == 0,
          "dry: nothing sent, no order object built at the gateway")
    o = (log[-1] if log else {}).get("order") or {}
    check(log and log[-1]["state"] == "dry" and o.get("conid") == 654321
          and o.get("side") == "BUY" and o.get("qty") == 1 and o.get("entry_limit") == 6000.0
          and o.get("stop") == 5980.0 and o.get("target") == 6040.0,
          "the intended order is logged: contract, side, size, entry, stop, target")


def group_d() -> None:
    head("D. BRACKETS ONLY")
    fresh_state()
    for bad, label in ((intent(stop=None), "no stop"), (intent(target=None), "no target"),
                       (intent(stop=6010.0), "a long's stop above entry"),
                       (intent(side=-1), "a short with a long's levels"),
                       (intent(entry=None), "no entry price")):
        rep, ib, _, _ = run(cfg(enabled=True, dry_run=False), [bad])
        check(rep["results"][0]["state"].startswith("refused") and not ib.placed
              and ib.brackets == 0, f"{label}: refused, nothing built or sent")
    ib = FakeIB()
    two = ib.bracketOrder("BUY", 1, 6000, 6040, 5980)[:2]
    loose = ib.bracketOrder("BUY", 1, 6000, 6040, 5980)
    loose[2].parentId = 999
    for legs, label in ((two, "a parent with one child"), (loose[:1], "a parent alone"),
                        (loose, "a child not tied to the parent")):
        try:
            executor._send(ib, object(), legs, "paper_exec:x")      # noqa: SLF001
            ok = False
        except executor.NotABracket:
            ok = True
        check(ok and not ib.placed, f"the send path refuses {label}")
    rep, ib, _, _ = run(cfg(enabled=True, dry_run=False), [intent()])
    kids = [o for _, o in ib.placed[1:]]
    check(rep["results"][0]["state"] == "sent" and len(ib.placed) == 3
          and all(k.parentId == ib.placed[0][1].orderId for k in kids)
          and all(o.orderRef == "paper_exec:eng_t:1" for _, o in ib.placed),
          "with both flags, a whole bracket goes as three tied orders (fake gateway)")


def group_e() -> None:
    head("E. SIZE AND CONTRACT")
    fresh_state()
    rep, ib, _, _ = run(cfg(enabled=True, dry_run=False), [intent(symbol="ES")])
    check("ES is refused by contract" in rep["results"][0]["state"] and not ib.placed,
          "ES is refused by contract (MES only in this tranche)")
    rep, _, _, _ = run(cfg(enabled=True, dry_run=False), [intent(symbol="NQ")])
    check(rep["results"][0]["state"].startswith("refused: NQ is not an instrument"),
          "an instrument outside the tranche is refused")
    rep, ib, _, _ = run(cfg(enabled=True, dry_run=False), [intent()],
                        master=FakeMaster(conid=None))
    check(rep["results"][0]["state"] == "skipped: MES (SM_TEST_MES) has no ibkr_conid in "
          "the Security Master" and not ib.placed, "a missing conid is skipped and named")
    gv = {"lab": "running", "engine": {"status": "live", "frozen": 0}}
    c = {"multiplier": 5.0}
    i = intent()
    check(orders.size(i, c, cfg(max_contracts=3), LIMITS, 0.0, gv)[0] == 3,
          "the config's ceiling (3 here) when nothing else binds")
    check(orders.size(i, c, cfg(max_contracts=3), LIMITS, 0.0,
                      {"lab": "running", "engine": {"status": "halved"}})[0] == 1
          and orders.size(i, c, cfg(max_contracts=1), LIMITS, 0.0,
                          {"lab": "running", "engine": {"status": "halved"}})[0] == 0,
          "a halved engine halves (3 -> 1; 1 -> 0, not sent)")
    q, why = orders.size(i, c, cfg(max_contracts=3), LIMITS, 0.0,
                         {"lab": "halted", "engine": {"status": "live"}})
    check(q == 0 and "halted" in why, "a halted lab sends nothing")
    q, why = orders.size(i, c, cfg(max_contracts=3), LIMITS, 0.0,
                         {"lab": "running", "engine": {"status": "live", "frozen": 1}})
    check(q == 0 and "frozen" in why, "a frozen engine sends nothing")
    wide = intent(stop=4000.0, target=8000.0)       # $10,000 a contract to the stop
    q, why = orders.size(wide, c, cfg(max_contracts=3), LIMITS, 0.0, gv)
    q2, _ = orders.size(wide, c, cfg(max_contracts=3), LIMITS, 15000.0, gv)
    check(orders.heat_budget(LIMITS) == 18000.0 and q == 1 and "heat cap" in why and q2 == 0,
          "the Doctrine's heat cap (6% of $300,000) cuts the size; open risk counts")
    lg = ledger()
    lg.set_engine("eng_t", "2026-10-31T00:00:00+00:00", status="halved", frozen=False)
    rep, ib, _, _ = run(cfg(enabled=True, dry_run=False, max_contracts=1), [intent()], lg=lg)
    check(rep["results"][0]["state"].startswith("refused: size 0") and not ib.placed,
          "through the executor, the lab's governor reads the engine from the ledger")


def group_f() -> None:
    head("F. THE KILL SWITCH")
    fresh_state()
    c = cfg(enabled=True, dry_run=False)
    st = State(pcfg.state_dir(c))
    st.root.mkdir(parents=True, exist_ok=True)
    (st.root / "kill").write_text("operator: stop", encoding="utf-8")
    rep, ib, made, _ = run(c, [intent()])
    check(rep["state"].startswith("killed") and not made, "a kill file: nothing connects")
    (st.root / "kill").unlink()
    rep, ib, made, _ = run(c, [intent()])
    check(rep["state"].startswith("killed") and not made and st.killed(),
          "the kill state is sticky: removing the file does not clear it")
    try:
        st.clear_kill("  ")
        ok = False
    except ValueError:
        ok = True
    check(ok and st.killed(), "a clear without the operator's reason is refused")
    check(st.clear_kill("reviewed the fills") and not st.killed()
          and "reviewed the fills" in (st.root / "cleared.jsonl").read_text(encoding="utf-8"),
          "the operator's clear lifts it and is recorded with its reason")
    ib = FakeIB()
    ib.on_place = lambda _ib: (st.root / "kill").write_text("mid-loop", encoding="utf-8")
    rep, ib, _, _ = run(c, [intent(), intent(signal_id=2)], ib=ib)
    check(rep["results"][0]["state"] == "sent" and rep["results"][1]["state"] == "killed"
          and len(ib.placed) == 3, "a kill file written mid-loop stops the very next send")
    st.clear_kill("fixture reset")


def group_g() -> None:
    head("G. THE LEDGER ROW")
    fresh_state()
    lg = ledger()
    c = cfg(enabled=True, dry_run=False)
    rep, ib, _, _ = run(c, [intent()], lg=lg)
    pid = ib.placed[0][1].orderId
    t0 = dt.datetime(2026, 11, 2, 14, 31, 5, tzinfo=dt.timezone.utc)
    entry = SimpleNamespace(execution=SimpleNamespace(orderId=pid, time=t0, side="BOT",
                                                      shares=1.0, price=6000.25),
                            commissionReport=SimpleNamespace(commission=0.62))
    pos_obj = SimpleNamespace(contract=SimpleNamespace(symbol="MES"), position=1.0)
    ib2 = FakeIB(fills=[entry], positions=[pos_obj])
    rep2, _, _, _ = run(c, [], ib=ib2, lg=lg)
    check(rep2["state"] == "done" and not rep2["reconcile"],
          "a fill since the last pass is captured before reconciling: the gateway's "
          "new position is not a mismatch")
    row = lg.one("SELECT * FROM fills WHERE id=?", (rep2["fills"][0],)) if rep2["fills"] else {}
    check(row and row["source"] == "paper_exec" and row["venue_order_id"] == str(pid)
          and row["venue_fill_time"] == t0.isoformat() and row["fill_kind"] == "quote"
          and row["purpose"] == "entry" and row["cost_commission"] == 0.62
          and row["engine_id"] == "eng_t" and row["signal_id"] == 1,
          "a paper fill: source paper_exec, the venue's order id and the fill's time, "
          "commission as its cost")
    pos = lg.open_positions("eng_t")
    check(len(pos) == 1 and pos[0]["entry_price"] == 6000.25 and pos[0]["stop_price"] == 5980.0,
          "the parent's fill opens the position with its bracket's stop")
    exitf = SimpleNamespace(execution=SimpleNamespace(
        orderId=pid + 1, time=t0 + dt.timedelta(hours=3), side="SLD", shares=1.0,
        price=6040.0), commissionReport=SimpleNamespace(commission=0.62))
    rep3, _, _, _ = run(c, [], ib=FakeIB(fills=[entry, exitf], positions=[]), lg=lg)
    g = lg.one("SELECT * FROM grades")
    gross = 1 * 1 * 5 * (6040.0 - 6000.25)
    check(len(rep3["fills"]) == 1 and g and abs(g["gross_pnl"] - gross) < 1e-9
          and abs(g["net_return"] - (gross - 1.24) / (6000.25 * 5)) < 1e-12
          and not lg.open_positions("eng_t"),
          "the target's fill closes and grades it by the lab's rule (net over notional); "
          "the entry is not written twice")
    try:
        lg.add_fill({**{k: row[k] for k in row if k not in ("id", "instrument_norm",
                                                              "written_at")},
                     "venue_order_id": None})
        ok = False
    except sqlite3.IntegrityError:
        ok = True
    check(ok, "the ledger refuses a paper_exec fill without the venue's order id")
    old = TD / "old_shape.db"
    con = sqlite3.connect(old)
    con.execute("CREATE TABLE fills (id INTEGER PRIMARY KEY, signal_id INTEGER, position_id "
                "INTEGER, engine_id TEXT NOT NULL, instrument TEXT NOT NULL, instrument_norm "
                "TEXT NOT NULL, purpose TEXT NOT NULL, side INTEGER NOT NULL, qty REAL NOT NULL,"
                " fill_kind TEXT NOT NULL, reference_price REAL NOT NULL, modelled_price REAL "
                "NOT NULL, stored_quote TEXT, cost_class TEXT NOT NULL, cost_spread REAL NOT NULL,"
                " cost_slippage REAL NOT NULL, cost_commission REAL NOT NULL, cost_borrow REAL "
                "NOT NULL, cost_roll REAL NOT NULL, cost_funding REAL NOT NULL, cost_fx REAL NOT "
                "NULL, cost_total REAL NOT NULL, filled_at TEXT NOT NULL, as_of TEXT NOT NULL, "
                "written_at TEXT NOT NULL)")
    con.execute("INSERT INTO fills VALUES (1,NULL,NULL,'e','SPY','SPY','entry',1,1,'bar_open',"
                "1,1,NULL,'equity',0,0,0,0,0,0,0,0,'d','d','d')")
    con.commit()
    con.close()
    from alpha.ledger import Ledger
    with Ledger(old) as lg2:
        cols = {r[1] for r in lg2.conn.execute("PRAGMA table_info(fills)")}
        kept = lg2.one("SELECT * FROM fills WHERE id=1")
    check({"source", "venue_order_id", "venue_fill_time"} <= cols and kept
          and kept["source"] == "model" and kept["fill_kind"] == "bar_open",
          "an older ledger gains the three fields in place; its rows stay, read as 'model'")


def group_h() -> None:
    head("H. RECONCILIATION")
    fresh_state()
    c = cfg(enabled=True, dry_run=False)
    pos_obj = SimpleNamespace(contract=SimpleNamespace(symbol="MES"), position=2.0)
    rep, ib, _, _ = run(c, [intent()], ib=FakeIB(positions=[pos_obj]))
    st = State(pcfg.state_dir(c))
    check(rep["state"].startswith("reconciliation mismatch") and ib.brackets == 0
          and not ib.placed and any("MES: the gateway holds +2, the ledger +0" in x
                                    for x in rep["reconcile"])
          and st.reconcile_block(),
          "a position the ledger does not hold: sending stops, the mismatch is named")
    trade = SimpleNamespace(order=SimpleNamespace(orderId=7, orderRef="by hand"))
    rep, ib, _, _ = run(c, [intent()], ib=FakeIB(trades=[trade]))
    check(rep["state"].startswith("reconciliation mismatch") and not ib.placed
          and any("did not send: id 7" in x for x in rep["reconcile"]),
          "an open order this executor did not send stops it too")
    rep, ib, _, _ = run(c, [intent()])
    check(rep["state"] == "done" and not st.reconcile_block(),
          "a clean reconciliation clears the block")
    from paper_exec.__main__ import status_lines
    run(c, [], ib=FakeIB(positions=[pos_obj]))
    check(any(x.startswith("reconciliation: STOPPED") for x in status_lines(c)),
          "the status command prints the block")


def group_i() -> None:
    head("I. BOUNDARIES")
    import ast
    import json
    import re
    order_calls = ("placeOrder", "bracketOrder")
    hits: dict = {}
    for f in sorted((REPO / "paper_exec").glob("*.py")):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Attribute) and sub.attr in order_calls:
                        hits.setdefault(sub.attr, set()).add(f"{f.name}:{node.name}")
    check(hits.get("placeOrder") == {"executor.py:_send"}
          and hits.get("bracketOrder") == {"executor.py:run"},
          f"the order calls live in the one send path ({ {k: sorted(v) for k, v in hits.items()} })")
    alpha_src = "\n".join(p.read_text(encoding="utf-8") for p in (REPO / "alpha").rglob("*.py"))
    check(not re.search(r"^\s*(from|import)\s+paper_exec", alpha_src, re.M),
          "the package sits outside alpha/, and alpha/ never imports it")
    from altdata.ibkr_clients import CLIENT_IDS
    check(CLIENT_IDS["paper_exec"] == 21 and len(set(CLIENT_IDS.values())) == len(CLIENT_IDS),
          "its client id, 21, is its own")
    deny = json.loads((REPO / ".claude" / "settings.json").read_text(encoding="utf-8"))[
        "permissions"]["deny"]
    check({"Bash(*paper_exec run*)", "Bash(*paper_exec clear-kill*)",
           "Bash(*paper_exec resume*)"} <= set(deny),
          "its run, clear-kill and resume commands are denied to sessions")
    units = [p.name for p in (REPO / "deploy" / "systemd").glob("*") if "paper" in p.name]
    check(not units, "no unit and no timer in this tranche")


def _paper_trades(lg, rets, engine="eng_t", start=1000):
    """Closed paper trades with the given net returns (synthetic)."""
    for k, r in enumerate(rets):
        t = f"2026-11-{(k % 27) + 1:02d}T15:{k % 60:02d}:00+00:00"
        fid = lg.add_fill({
            "signal_id": None, "engine_id": engine, "instrument": "MES", "purpose": "entry",
            "side": 1, "qty": 1.0, "fill_kind": "quote", "reference_price": 6000.0,
            "modelled_price": 6000.0, "stored_quote": None, "cost_class": "future",
            "cost_spread": 0, "cost_slippage": 0, "cost_commission": 0, "cost_borrow": 0,
            "cost_roll": 0, "cost_funding": 0, "cost_fx": 0, "cost_total": 0,
            "filled_at": t, "as_of": t, "source": "paper_exec",
            "venue_order_id": str(start + k), "venue_fill_time": t})
        pid = lg.open_position({"engine_id": engine, "signal_id": None, "instrument": "MES",
                                "cost_class": "future", "direction": 1, "qty": 1.0,
                                "entry_fill_id": fid, "entry_price": 6000.0,
                                "opened_at": t, "as_of": t})
        lg.close_position(pid, fid, 6000.0, "paper target", t)
        lg.add_grade({"position_id": pid, "engine_id": engine, "day": t[:10],
                      "gross_pnl": 0, "costs": 0, "net_pnl": r, "net_return": r,
                      "win": int(r > 0), "regime_key": None, "as_of": t})


def group_j() -> None:
    head("J. THE EDGE-DECAY PAUSE (D43)")
    import math
    from paper_exec import pause
    fresh_state()
    c = cfg(enabled=True, dry_run=False)
    st = State(pcfg.state_dir(c))
    lg = ledger()                     # backtest: expectancy 0.004, sd 0.02, n 400
    _paper_trades(lg, [-0.01] * 19)
    f = pause.figures(lg, "eng_t", c)
    check(f["state"] == "accruing (n=19)" and not pause.evaluate(lg, st, "eng_t", c)["paused"],
          "below 20 closed paper trades: accruing (n=19), never a pause")
    rets = [-0.01] * 19 + [0.002]
    lg2 = ledger()
    _paper_trades(lg2, rets)
    f = pause.figures(lg2, "eng_t", c)
    mean = sum(rets) / 20
    sd = math.sqrt(sum((r - mean) ** 2 for r in rets) / 19)
    se = math.sqrt(sd ** 2 / 20 + (0.02 / math.sqrt(400)) ** 2)
    z = (mean - 0.004) / se
    check(abs(f["paper_mean"] - mean) < 1e-12 and abs(f["se"] - se) < 1e-12
          and abs(f["z"] - z) < 1e-9 and f["backtest_se"] == 0.001 and f["state"] == "trip",
          f"the arithmetic: mean {mean:+.4f} against 0.0040, SE {se:.5f} (paper sd/sqrt20 "
          f"and the backtest's sd/sqrt(n_signals)), z {z:+.2f} <= -2: trips")
    check("validated_metrics.expectancy" in f["fields"],
          "the backtest fields are named: engines.validated_metrics.expectancy, .sd, .n_signals")
    lg3 = ledger()
    _paper_trades(lg3, [0.004 + 0.0005 * ((-1) ** k) for k in range(20)])
    check(pause.figures(lg3, "eng_t", c)["state"] == "within",
          "a paper record matching the backtest does not trip")
    ev = pause.evaluate(lg2, st, "eng_t", c)
    rep, ib, _, _ = run(c, [intent()], lg=lg2)
    check(ev["paused"] and st.pause("eng_t") and rep["results"][0]["state"].startswith("paused")
          and not ib.placed, "a tripped pause is written to state, and the engine sends nothing")
    _paper_trades(lg2, [0.05] * 20, start=5000)
    check(pause.figures(lg2, "eng_t", c)["state"] == "within"
          and pause.evaluate(lg2, st, "eng_t", c)["paused"] and st.pause("eng_t"),
          "it never clears itself: twenty good trades later it is still paused")
    from paper_exec.__main__ import status_lines
    check(any(x.startswith("PAUSED eng_t") and "standard errors" in x for x in status_lines(c)),
          "the status command prints the pause with its figures")
    try:
        pause.resume(st, "eng_t", "")
        ok = False
    except ValueError:
        ok = True
    check(ok and pause.resume(st, "eng_t", "reviewed the fills") and not st.pause("eng_t")
          and "reviewed the fills" in (st.root / "resumed.jsonl").read_text(encoding="utf-8"),
          "only the operator's resume, with a reason, lifts it; the resume is recorded")


def group_k() -> None:
    head("K. 'WHY THIS COULD FAIL' (D43)")
    import json
    import yaml
    from alpha import critique
    from alpha_proposer import critic
    h = {"id": "H-0001", "title": "t", "family": "trend", "mechanism": "m",
         "rule_text": "buy MES on a 20-day high", "rule_dsl": '{"x": 1}', "instruments": '["MES"]',
         "status": "failed", "status_reason": "holdout", "result": '{"expectancy": -0.01}',
         "engine_id": "eng_t", "expected_size": 0.01, "spec": "{}", "pre_registered_at": "x"}
    inp = critique.inputs(h)
    check(set(inp) <= set(critique.INPUT_FIELDS) and not critique.leaks(inp)
          and inp["rule_dsl"] == {"x": 1} and "result" not in inp and "status" not in inp,
          "the critic's inputs are the hypothesis's text and rule only: no result field")
    check(critique.leaks({"a": [{"expectancy": 1}]}) == ["expectancy"],
          "the leak check finds a result field anywhere in a payload")
    from alpha.ledger import Ledger
    lg = Ledger(TD / "critic.db")
    lg._insert("hypotheses", {                                   # noqa: SLF001
        "id": "H-0001", "batch_id": "B", "local_id": "1", "title": "t", "family": "trend",
        "mechanism": "m", "rule_text": "buy MES on a 20-day high", "rule_hash": "h",
        "needs_code": 0, "spec": "{}", "source": "operator", "channel": "c",
        "model_idea_rule": 0, "pre_registered_at": "2026-10-31T00:00:00+00:00",
        "status": "failed", "result": '{"expectancy": -0.01}', "as_of": "x"})
    inbox, logs = TD / "inbox", TD / "logs"
    seen: list = []
    reply = json.dumps({"modes": [{"mode": "cost", "sentence": "below the cost cliff"},
                                  {"mode": "regime", "sentence": "trend-only"}]})
    rec0 = critic.run(lg, "2026-10-31T23:00:00+00:00", cfg={"critic": {"daily_call_budget": 0}},
                      call=lambda i: seen.append(i) or (reply, "m"), inbox=inbox, log_dir=logs)
    check(critic.budget() == 0 and rec0["called"] == 0 and not seen
          and rec0["state"] == "budget 0: no call made",
          "the budget ships at 0 (config/alpha.yaml): no call is made")
    rec = critic.run(lg, "2026-10-31T23:00:00+00:00", cfg={"critic": {"daily_call_budget": 5}},
                     call=lambda i: seen.append(i) or (reply, "m"), inbox=inbox, log_dir=logs)
    check(rec["called"] == 1 and len(seen) == 1 and not critique.leaks(seen[0])
          and "result" not in json.dumps(seen[0]) and "failed" not in json.dumps(seen[0]),
          "with a budget, one call per hypothesis, its inputs free of any result "
          "(the hypothesis's 'failed' and its result never reach it)")
    f = inbox / "critiques-2026-10-31.yaml"
    doc = yaml.safe_load(f.read_text(encoding="utf-8")) if f.exists() else {}
    man = (inbox / "manifest-proposer.jsonl").read_text(encoding="utf-8") if f.exists() else ""
    check(doc.get("schema") == critique.SCHEMA and doc["critiques"][0]["hypothesis_id"] == "H-0001"
          and f.name in man, "written as the proposer writes: an inbox file with its manifest line")
    check(critic.calls_today("2026-10-31", logs) == 1
          and critic.run(lg, "2026-10-31T23:30:00+00:00", cfg={"critic": {"daily_call_budget": 1}},
                         call=lambda i: (reply, "m"), inbox=inbox, log_dir=logs)["called"] == 0,
          "the day's calls count against the budget")
    from alpha import inbox as ib_mod
    res = ib_mod.ingest(lg, None, "2026-11-01T00:00:00+00:00", inbox=inbox)
    row = lg.one("SELECT * FROM hypothesis_critiques WHERE hypothesis_id='H-0001'")
    check(row and json.loads(row["modes"])[0]["mode"] == "cost" and row["author"] == "critic"
          and any(x["file"] == f.name for x in res["ingested"]),
          "the nightly ingestion stores the critique beside the hypothesis")
    try:
        lg.conn.execute("UPDATE hypothesis_critiques SET modes='[]'")
        ok = False
    except sqlite3.IntegrityError:
        ok = True
    again = critique.ingest(lg, doc, "x.yaml", "y")
    check(ok and not again["stored"] and "written once" in again["refused"][0]["why"],
          "a critique is written once: no update, and a second one is refused")
    bad = critique.check([{"mode": "vibes", "sentence": "x"}, {"mode": "cost", "sentence": "y"}])
    check(bad and "vocabulary" in bad and critique.check([{"mode": "cost", "sentence": "y"}]),
          "the closed vocabulary, and two to five modes")
    src = (REPO / "alpha_proposer" / "critic.py").read_text(encoding="utf-8")
    check("model_meter.scope(report=REPORT" in src and "model_meter.create(" in src
          and "Ledger(" not in src,
          "the call is metered (report alpha_critic), and the package never writes alpha.db")


def main() -> int:
    for g in GROUPS:
        g()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


GROUPS = [group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h, group_i,
          group_j, group_k]

if __name__ == "__main__":
    sys.exit(main())
