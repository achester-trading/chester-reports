"""
Validation gate for Layer X, the Alpha Lab, Tranche 1 (X-1.12). On a synthetic
store and a fixture ledger of its own; no network, no box, no live store.

  A  THE CONSTITUTION. config/alpha_constitution.yaml carries exactly the change
     order's section 2 values and no other key; its sha256 is recorded in
     docs/alpha-lab.md beside a ruling line, and the check fails on a copy whose
     hash is not; nothing in alpha/ writes a file at all (sqlite aside).
  B  THE LEDGER (X-1.1). alpha.db's tables, each row with as_of and written_at;
     its path beside the store; the nightly sweep snapshots it and never copies
     it raw; the blocklist refuses a Brookfield-complex instrument in Python and
     again in SQLite; loop_events is append-only; the variant count counts.
  C  THE STORE, READ-ONLY (X-1.2). The connection refuses a write; the subclass
     refuses write(); the store file's hash is unchanged after the nightly runs
     of group J.
  D  THE ENGINE INTERFACE (X-1.3). Abstract; the registry is empty; an engine
     outside alpha/ will not load (the gate's fixture is let in for the test).
  E  THE COST MODEL (X-1.4). Every class present; a buy fills above the
     reference and a sell below, never the mid; a stored quote is crossed at
     the ask or the bid; holding costs by side and days.
  F  SIMULATED EXECUTION (X-1.5). The next stored bar's open plus costs, never a
     price from before the signal; a stored quote; the bracket bar by bar -- a
     gap through the stop exits at the open, a bar touching both exits at the
     stop, the time stop at the close; marks; grades net of every cost.
  G  THE HARNESS (X-1.6). A synthetic series with a known edge passes and a null
     series fails; the deflated Sharpe falls as the variant count rises; every
     run counts one more variant; the hold-out months are never fitted or
     walk-forward tested; the embargo separates fit and test; a row knowable
     after its decision voids the run; the pass record.
  H  THE ALLOCATOR (X-1.7). Quarter-Kelly; min_size before the sample; the heat
     cap; correlated engines counted once; a halved engine at half.
  I  THE GOVERNOR (X-1.8). -10% halves and freezes, -20% stops (validation,
     frozen), a new high restores; the lab at -15% halts; a frozen engine is
     never re-fitted; every transition a loop_events row.
  J  THE NIGHTLY LOOP (X-1.9) end to end on the synthetic store with the fixture
     engine: fills, marks, grades, posteriors with the recorded shrinkage prior,
     attribution by regime key, weights, every change an event; a failure is an
     event, not an exception; the weekly loop applies the weights.
  K  THE WEEKLY'S LINE (X-1.11). "not yet live" with no ledger or no live
     engine; the fixture ledger's line exactly; the one hook in weekly_stack.
  L  UNITS AND TIMERS (X-1.10). The nightly after the close's capture, the
     weekly after the Weekly; neither in DEPLOY_TIMERS; the wrappers.
  M  NO ORDERS. tools/validate_alpha_no_orders.py's scan over alpha/.

Tranche 2 (X-2; change order sections 4 and 10):

  N  THE REGISTER (X-2.5). The first real batch (the inbox fixture) is valid
     v1 and its bytes are the pinned ones; a broken batch is refused field by
     field; the weekly brief's budgets; registering counts a variant; the idea
     is fixed and never deleted; duplicates by rule hash and by title, failures
     included; the harness refuses a hypothesis pre-registered after the run,
     an unregistered one and a closed one; a blocked instrument never reaches
     the register.

    python tools/validate_alpha.py
"""

from __future__ import annotations

import ast
import datetime as dt
import hashlib
import json
import math
import os
import random
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

_TMP = gate_mkdtemp(prefix="validate_alpha_")
os.environ["CHESTER_DB"] = os.path.join(_TMP, "store.sqlite")
os.environ.pop("ALPHA_DB", None)

import yaml  # noqa: E402

from altdata import observations  # noqa: E402

observations.DEFAULT_DB = os.environ["CHESTER_DB"]

from alpha import allocate, blocklist, book, governor, lab_line  # noqa: E402
from alpha import hypotheses as hyp  # noqa: E402
from alpha import config as acfg  # noqa: E402
from alpha import engine as engine_mod  # noqa: E402
from alpha import validate as av  # noqa: E402
from alpha.costs import COMPONENTS, CostModel  # noqa: E402
from alpha.engine import Instrument, Signal  # noqa: E402
from alpha.ledger import LAB, Ledger  # noqa: E402
from alpha.loops import nightly, weekly  # noqa: E402
from alpha.paper import Paper  # noqa: E402
from alpha.store import ReadOnlyStore, ReadOnlyStoreError  # noqa: E402

PASS = FAIL = 0
LINE = "=" * 78
FIXTURES = REPO / "tests" / "fixtures" / "alpha"
DOC = REPO / "docs" / "alpha-lab.md"

# The change order's section 2, as the file must carry it -- every key, and no
# other (ruled 12 Oct 2026).
EXPECTED_CONSTITUTION = {
    "objective": "maximise expected log growth of the lab's notional capital net "
                 "of modelled costs, subject to the governor",
    "kelly_fraction": 0.25,
    "governor": {"engine": {"halve_at": -0.10, "stop_at": -0.20},
                 "portfolio": {"stop_at": -0.15}},
    "validation": {"embargo": "one engine horizon between fit and test windows",
                   "embargo_horizons": 1,
                   "min_signals": {"daily": 100, "weekly": 40, "intraday": 400},
                   "deflated_sharpe_min": 1.0,
                   "min_size_period": "the first min_signals paper signals at "
                                      "minimum size regardless of backtest"},
    "kill": {"rule": "after min_signals: expectancy after modelled costs <= 0, or "
                     "realised Sharpe < 0.5 x the deflated Sharpe it was validated with",
             "expectancy_at_or_below": 0.0,
             "realised_sharpe_below_deflated_multiple": 0.5},
    "holdout_months": {"rule": "every fourth calendar month of history, never fitted "
                               "by any loop; used only for the final check before a "
                               "promotion", "every": 4},
    "refit": {"frozen_in_drawdown": True},
    "orders": {"value": "none", "rule": "alpha/ may not import any order, gate, "
                                        "broker or network module (static gate)"},
    "blocklist": {"rule": "the system's, applied at signal time; a blocked "
                          "instrument never reaches the ledger"},
}


def check(c: bool, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# The synthetic store
# ---------------------------------------------------------------------------
def sessions(first: str, n: int) -> list[str]:
    from altdata import session                                 # noqa: PLC0415
    d, out = dt.date.fromisoformat(first), []
    while len(out) < n:
        if session.is_trading_session(d):
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def seed_store(path: str, days: list[str]) -> None:
    """SPY daily OHLC (and volume), the market-state object per day, and a
    prediction-market contract's quote. All synthetic."""
    st = observations.ObservationStore(path)
    rows = []
    price = 600.0
    for i, d in enumerate(days):
        o = price * (1 + 0.004 * math.sin(i / 2.0))
        c = o * (1 + 0.006 * math.sin(i / 3.0 + 1))
        h, lo = max(o, c) * 1.004, min(o, c) * 0.996
        av_at = f"{d}T20:15:00+00:00"
        for k, v in (("", c), ("_open", o), ("_high", h), ("_low", lo),
                     ("_volume", 5.0e7)):
            rows.append({"registry_key": f"yfinance.mkt_spy{k}", "instrument": None,
                         "observed_at": d, "available_at": av_at, "value": v,
                         "source": "synthetic"})
        obj = {"object": "market_state", "session": d,
               "dials": {"macro": {"state": "Expansion"},
                         "vol": {"state": "calm" if i % 2 else "elevated"},
                         "gamma": {"state": "positive"}},
               "session_events": (["CPI"] if i % 5 == 0 else [])}
        rows.append({"registry_key": "market_state", "instrument": None,
                     "observed_at": d, "available_at": f"{d}T21:00:00+00:00",
                     "value": json.dumps(obj), "source": "synthetic"})
        price = c
    rows += [{"registry_key": "pm.bid", "instrument": "KX-TEST", "observed_at": days[3],
              "available_at": f"{days[3]}T22:00:00+00:00", "value": 0.40,
              "source": "synthetic"},
             {"registry_key": "pm.ask", "instrument": "KX-TEST", "observed_at": days[3],
              "available_at": f"{days[3]}T22:00:00+00:00", "value": 0.44,
              "source": "synthetic"}]
    st.write_many(rows)
    st.close()


DAYS = sessions("2026-08-03", 45)
STORE = os.environ["CHESTER_DB"]
seed_store(STORE, DAYS)


def asof(day: str) -> str:
    return f"{day}T21:40:00+00:00"


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE CONSTITUTION")
    con = acfg.constitution()
    check(con == EXPECTED_CONSTITUTION,
          "config/alpha_constitution.yaml carries exactly the section 2 values, "
          "and no other key")
    h = acfg.constitution_sha256()
    text = DOC.read_text(encoding="utf-8") if DOC.is_file() else ""
    check(recorded(text, h), f"its sha256 ({h[:16]}...) is recorded in "
          f"docs/alpha-lab.md beside a ruling line")
    alt = Path(_TMP) / "constitution_edited.yaml"
    alt.write_bytes(acfg.CONSTITUTION_PATH.read_bytes().replace(b"0.25", b"0.5"))
    check(not recorded(text, acfg.constitution_sha256(alt)),
          "an edit without a recorded ruling (kelly_fraction 0.25 -> 0.5) fails the "
          "hash check")
    check(not recorded(text.replace("Ruled", "Noted"), h),
          "and a recorded hash without a ruling line does not count")
    m = re.search(r"### The constitution, verbatim\s+```yaml\n(.*?)```", text, re.S)
    body = acfg.CONSTITUTION_PATH.read_text(encoding="utf-8").replace("\r\n", "\n")
    lines = body.split("\n")
    while lines and (lines[0].startswith("#") or not lines[0].strip()):
        lines.pop(0)
    check(m is not None and m.group(1).strip() == "\n".join(lines).strip(),
          "docs/alpha-lab.md prints the constitution verbatim (its header comment "
          "aside)")
    bad = file_writes()
    check(not bad, "nothing in alpha/ writes a file -- no open for writing, no "
          "write_text/write_bytes, no yaml dump, no shutil, no rename "
          + ("" if not bad else f"({bad[:4]})"))


def recorded(doc: str, digest: str) -> bool:
    """A table row carrying the hash in backticks and a 'Ruled' citation."""
    for ln in doc.splitlines():
        if f"`{digest}`" in ln and ln.lstrip().startswith("|") and "Ruled" in ln:
            return True
    return False


MODULE_WRITES = {"os": {"remove", "unlink", "rename", "replace", "rmdir",
                        "removedirs", "truncate"},
                 "shutil": None,                       # any shutil call
                 "yaml": {"dump", "safe_dump", "dump_all"},
                 "json": {"dump"}}


def file_writes() -> list[str]:
    """Every call in alpha/ that could write or remove a file. The one allowed:
    alpha/ledger.py's snapshot() clears its own destination before the backup."""
    out = []
    for p in sorted((REPO / "alpha").rglob("*.py")):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        rel = str(p.relative_to(REPO)).replace("\\", "/")
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else (
                fn.id if isinstance(fn, ast.Name) else "")
            owner = fn.value.id if (isinstance(fn, ast.Attribute)
                                    and isinstance(fn.value, ast.Name)) else None
            if name == "open":
                mode = (node.args[1].value if len(node.args) > 1 and isinstance(
                    node.args[1], ast.Constant) else next(
                    (k.value.value for k in node.keywords if k.arg == "mode"
                     and isinstance(k.value, ast.Constant)), "r"))
                if any(c in str(mode) for c in "wax+"):
                    out.append(f"{rel}:{node.lineno} open({mode!r})")
            elif name in ("write_text", "write_bytes"):
                out.append(f"{rel}:{node.lineno} {name}()")
            elif owner in MODULE_WRITES and (MODULE_WRITES[owner] is None
                                             or name in MODULE_WRITES[owner]):
                out.append(f"{rel}:{node.lineno} {owner}.{name}()")
            elif name == "unlink" and rel != "alpha/ledger.py":
                out.append(f"{rel}:{node.lineno} unlink()")
    return out


# ---------------------------------------------------------------------------
def group_b() -> None:
    head("B. THE LEDGER (X-1.1)")
    want = {"engines", "hypotheses", "hypothesis_batches", "inbox_log",
            "signals", "fills", "positions", "marks",
            "grades", "edge_posterior", "cost_calibration", "attribution",
            "loop_events", "variant_counts", "holdout", "allocations", "equity"}
    path = Path(_TMP) / "b.db"
    with Ledger(path) as lg:
        have = {r["name"] for r in lg.q("SELECT name FROM sqlite_master WHERE type='table'")}
        check(want <= have, f"alpha.db holds the change order's tables, plus "
              f"allocations and equity ({len(want & have)} of {len(want)})")
        cols_ok = all({"as_of", "written_at"} <= {c["name"] for c in lg.q(
            f"PRAGMA table_info({t})")} for t in want)
        check(cols_ok, "every one of them carries as_of and written_at")
        try:
            lg.add_signal("e1", "BN", 1, 0.01, asof(DAYS[0]))
            check(False, "the blocklist refuses BN at signal time")
        except blocklist.BlockedInstrument:
            check(True, "the blocklist refuses BN at signal time (the system's list)")
        try:
            lg.conn.execute(
                "INSERT INTO signals (engine_id, instrument, instrument_norm, direction,"
                " size_fraction, as_of, written_at) VALUES ('e1','BN.PR.A','BN',1,0.01,"
                "'x','y')")
            check(False, "and SQLite refuses it again for an insert that bypasses Python")
        except sqlite3.IntegrityError as exc:
            check("restricted instrument" in str(exc),
                  "and SQLite refuses it again for an insert that bypasses Python")
        n_sig = lg.one("SELECT COUNT(*) AS n FROM signals")["n"]
        check(n_sig == 0, "so a blocked instrument never reaches the ledger")
        eid = lg.event("nightly", "posterior", asof(DAYS[0]), "e1", before={"a": 1},
                       after={"a": 2})
        try:
            lg.conn.execute("UPDATE loop_events SET after='x' WHERE id=?", (eid,))
            check(False, "loop_events refuses an edit")
        except sqlite3.IntegrityError:
            check(True, "loop_events refuses an edit")
        try:
            lg.conn.execute("DELETE FROM loop_events WHERE id=?", (eid,))
            check(False, "and a delete")
        except sqlite3.IntegrityError:
            check(True, "and a delete")
        rid = lg.event("nightly", "reversal", asof(DAYS[0]), "e1")
        lg.reverse(eid, rid)
        try:
            lg.reverse(eid, rid)
            check(False, "an event is reversed once, by a new event")
        except sqlite3.IntegrityError:
            check(True, "an event is reversed once, by a new event")
        lg.conn.rollback()
        n1, n2 = lg.bump_variant("fam", "x"), lg.bump_variant("fam", "x")
        check((n1, n2, lg.variant_count("fam")) == (1, 2, 2),
              "the variant count counts every run of a family")
        ev = lg.one("SELECT version FROM loop_events WHERE id=?", (eid,))["version"]
        check(ev.endswith(acfg.constitution_sha256()[:12]),
              f"an event carries the code's and the constitution's version ({ev})")
    check(acfg.ledger_path() == Path(STORE).resolve().parent / "alpha.db",
          "alpha.db's path is beside the observation store (config/alpha.yaml)")
    os.environ["ALPHA_DB"] = str(Path(_TMP) / "elsewhere.db")
    check(acfg.ledger_path() == Path(_TMP) / "elsewhere.db", "and $ALPHA_DB overrides it")
    os.environ.pop("ALPHA_DB")
    sweep = (REPO / "scripts" / "rclone_sync.sh").read_text(encoding="utf-8")
    code = "\n".join(ln for ln in sweep.splitlines() if not ln.strip().startswith("#"))
    check('-m alpha.ledger snapshot "$ALPHA_SNAP" "$ALPHA_DB"' in code
          and '--exclude "/alpha.db*"' in code
          and 'integrity "$ALPHA_SNAP"' in code and 'cmp -s - "$ALPHA_SNAP"' in code,
          "the nightly sweep snapshots alpha.db (online backup, integrity, gzip round "
          "trip) and never uploads the live file raw")
    snap = Path(_TMP) / "snap.db"
    from alpha import ledger as ledger_mod                      # noqa: PLC0415
    info = ledger_mod.snapshot(path, snap)
    check(info["loop_events"] == 2 and observations.integrity_check(snap) == [],
          "the snapshot opens independently and passes integrity_check")


# ---------------------------------------------------------------------------
def group_c_static() -> None:
    head("C. THE STORE, READ-ONLY (X-1.2)")
    st = ReadOnlyStore(STORE)
    try:
        try:
            st.write("x", None, "2026-01-01", "2026-01-01T00:00:00+00:00", 1.0, "s")
            check(False, "ReadOnlyStore.write() refuses")
        except ReadOnlyStoreError:
            check(True, "ReadOnlyStore.write() refuses")
        try:
            st.conn.execute("INSERT INTO observations (registry_key, observed_at, "
                            "available_at, ingested_at, value_num, source) VALUES "
                            "('x','a','b','c',1,'s')")
            check(False, "and the connection itself refuses a write (mode=ro)")
        except sqlite3.OperationalError as exc:
            check("readonly" in str(exc).replace(" ", "").lower(),
                  "and the connection itself refuses a write (mode=ro)")
        b = st.daily_bars("yfinance.mkt_spy", asof(DAYS[5]))
        check(len(b) == 6 and b[-1]["day"] == DAYS[5],
              "it reads through the point-in-time join: six bars knowable at the "
              "sixth session's evening")
        check(st.regime_key(asof(DAYS[5]), DAYS[5]).startswith("macro=Expansion|vol="),
              "the regime key reads the stored object's dials")
    finally:
        st.close()
    try:
        ReadOnlyStore(Path(_TMP) / "absent.sqlite")
        check(False, "a missing store is not created")
    except FileNotFoundError:
        check(not (Path(_TMP) / "absent.sqlite").exists(), "a missing store is not created")


# ---------------------------------------------------------------------------
def group_d() -> None:
    head("D. THE ENGINE INTERFACE (X-1.3)")
    check(getattr(engine_mod.Engine, "__abstractmethods__", set()) ==
          {"universe", "signal", "size", "exits"},
          "Engine is abstract over universe, signal, size and exits")
    for a in ("engine_id", "family", "horizon", "cost_class", "validated_ranges",
              "kill_rule"):
        check(hasattr(engine_mod.Engine, a), f"and declares {a}")
    check(engine_mod.registered() == [],
          "config/alpha_engines.yaml registers no engine (Tranche 1)")
    entry = {"id": "fx", "class": "tests.fixtures.alpha.fixture_engine:FixtureEngine"}
    try:
        engine_mod.load(entry)
        check(False, "an engine outside alpha/engines/ will not load")
    except ValueError:
        check(True, "an engine outside alpha/engines/ will not load")


# ---------------------------------------------------------------------------
def group_e() -> None:
    head("E. THE COST MODEL (X-1.4)")
    cm = CostModel()
    classes = {"etf", "single_name", "index_option", "equity_option", "future", "perp",
               "prediction_market", "fx_pair"}
    check(set(cm.classes) == classes, "the eight cost classes are declared")
    buy = cm.fill("etf", 1, 100, 100.0)
    sell = cm.fill("etf", -1, 100, 100.0)
    check(buy.price > 100.0 > sell.price, f"a buy fills above the reference "
          f"({buy.price:.4f}) and a sell below ({sell.price:.4f}): never the mid")
    check(abs(buy.costs["spread"] - 100 * 100.0 * 3.0 / 1e4 / 2) < 1e-9,
          "half the spread estimate is crossed (3 bps -> 1.5 bps a side)")
    check(set(buy.costs) == set(COMPONENTS) and all(v >= 0 for v in buy.costs.values()),
          "every component is stated, and none is negative")
    q = {"bid": 0.40, "ask": 0.44}
    qb = cm.fill("prediction_market", 1, 10, 0.0, quote=q)
    qs = cm.fill("prediction_market", -1, 10, 0.0, quote=q)
    check(qb.kind == "quote" and qb.price >= 0.44 and qs.price <= 0.40,
          f"a stored quote is crossed: a buy at or above the ask ({qb.price:.4f}), a "
          f"sell at or below the bid ({qs.price:.4f})")
    h = cm.holding("etf", -1, 10000.0, 365)
    check(abs(h["borrow"] - 50.0) < 1e-9 and cm.holding("etf", 1, 10000.0, 365)["borrow"] == 0,
          "borrow is charged on a short only (50 bps a year on 10,000 = 50)")
    check(cm.holding("future", 1, 10000.0, 130)["roll"] == 2 * 10000 * 3.0 / 1e4,
          "a future rolls every 63 days held (two rolls in 130)")
    check(cm.holding("perp", 1, 10000.0, 10)["funding"] == 10000 * 1.0 / 1e4 * 10,
          "a perp pays funding either side")
    big = cm.fill("etf", 1, 1e6, 100.0, adv_notional=1e8)
    small = cm.fill("etf", 1, 10, 100.0, adv_notional=1e8)
    check(big.costs["slippage"] / 1e6 > small.costs["slippage"] / 10,
          "slippage grows with size against dollar ADV")


# ---------------------------------------------------------------------------
def group_f() -> None:
    head("F. SIMULATED EXECUTION (X-1.5)")
    path = Path(_TMP) / "f.db"
    st = ReadOnlyStore(STORE)
    lg = Ledger(path)
    try:
        p = Paper(lg, st)
        spy = Instrument(id="SPY", key="yfinance.mkt_spy", cost_class="etf")
        d0, d1 = DAYS[10], DAYS[11]
        bars = {b["day"]: b for b in st.daily_bars("yfinance.mkt_spy", asof(DAYS[-1]))}
        sid = p.queue("eng", Signal(instrument=spy, direction=1, as_of=asof(d0),
                                    stop=bars[d0]["close"] * 0.5,
                                    target=bars[d0]["close"] * 1.5), 1.0)
        none_yet = p.fill_pending(asof(d0), lambda e: 10000.0)
        check(none_yet == [], "no fill on the signal's own evening: the next bar is "
              "not yet stored")
        opened = p.fill_pending(asof(d1), lambda e: 10000.0)
        f = lg.one("SELECT * FROM fills WHERE signal_id=?", (sid,))
        check(len(opened) == 1 and f["filled_at"] == d1
              and abs(f["reference_price"] - bars[d1]["open"]) < 1e-9
              and f["modelled_price"] > f["reference_price"],
              f"filled at the NEXT stored bar's open ({d1}) plus costs "
              f"({f['reference_price']:.3f} -> {f['modelled_price']:.3f})")
        check(f["cost_total"] > 0 and abs(f["cost_total"] - sum(
            f[f"cost_{c}"] for c in COMPONENTS)) < 1e-9,
              "the fill carries every cost component and their total")
        pos = lg.open_positions()[0]
        # The bracket, on synthetic bars.
        from alpha.engine import Bar                            # noqa: PLC0415
        long_ = {"direction": 1, "stop_price": 98.0, "target_price": 103.0}
        check(Paper.bracket(long_, Bar("d", 97.0, 99.0, 96.0, 98.5), False)
              == ("stop", 97.0, "bar_open"),
              "a bar that opens through the stop exits at its open (the gap)")
        check(Paper.bracket(long_, Bar("d", 100.0, 103.5, 97.5, 101.0), False)
              == ("stop", 98.0, "bar_level"),
              "a bar that reaches both stop and target exits at the STOP")
        check(Paper.bracket(long_, Bar("d", 100.0, 103.5, 99.0, 101.0), False)
              == ("target", 103.0, "bar_level"), "a bar that reaches the target alone")
        short = {"direction": -1, "stop_price": 102.0, "target_price": 97.0}
        check(Paper.bracket(short, Bar("d", 103.0, 104.0, 100.0, 101.0), False)
              == ("stop", 103.0, "bar_open"), "and the mirror for a short")
        n = p.mark(asof(DAYS[12]))
        m = lg.one("SELECT * FROM marks WHERE position_id=?", (pos["id"],))
        check(n == 1 and m["day"] == DAYS[12], "an open position is marked at the "
              "latest stored close")
        # The time stop: a five-day stop on a fresh signal.
        sid2 = p.queue("eng", Signal(instrument=spy, direction=-1, as_of=asof(DAYS[20]),
                                     time_stop_days=5), 1.0)
        p.fill_pending(asof(DAYS[21]), lambda e: 10000.0)
        closed = p.evaluate_exits(asof(DAYS[30]))
        pos2 = lg.one("SELECT * FROM positions WHERE signal_id=?", (sid2,))
        g = lg.one("SELECT * FROM grades WHERE position_id=?", (pos2["id"],))
        stop_day = (dt.date.fromisoformat(DAYS[20]) + dt.timedelta(days=5)).isoformat()
        check(pos2["status"] == "closed" and pos2["exit_reason"] == "time"
              and pos2["closed_at"] >= stop_day and pos2["id"] in closed,
              f"the time stop exits at the close of the first bar on or after "
              f"{stop_day} ({pos2['closed_at']})")
        check(g is not None and abs(g["net_pnl"] - (g["gross_pnl"] - g["costs"])) < 1e-9
              and g["costs"] > 0 and g["regime_key"].startswith("macro="),
              "graded once, net of both fills' costs, with its exit day's regime key")
        # A stored quote fills at the ask.
        pm = Instrument(id="KX-TEST", key="pm.last", cost_class="prediction_market",
                        quote_keys=("pm.bid", "pm.ask"), store_instrument="KX-TEST")
        sid3 = p.queue("eng", Signal(instrument=pm, direction=1, as_of=asof(DAYS[2])),
                       0.01)
        p.fill_pending(asof(DAYS[4]), lambda e: 10000.0)
        f3 = lg.one("SELECT * FROM fills WHERE signal_id=?", (sid3,))
        check(f3 is not None and f3["fill_kind"] == "quote" and f3["modelled_price"] >= 0.44,
              "where a quote is stored after the signal, the fill crosses it at the ask")
    finally:
        lg.close()
        st.close()


# ---------------------------------------------------------------------------
def synthetic_rows(edge: float, years: int = 8, seed: int = 7) -> list[dict]:
    rnd = random.Random(seed)
    d, rows = dt.date(2016, 1, 4), []
    while d.year < 2016 + years:
        if d.weekday() < 5:
            x = rnd.gauss(0, 1)
            r = edge * (1 if x > 0 else -1) + rnd.gauss(0, 0.01)
            day = d.isoformat()
            rows.append({"day": day, "decided_at": f"{day}T21:00:00.000000+00:00",
                         "available_at": f"{day}T20:30:00.000000+00:00", "x": x,
                         "r": r})
        d += dt.timedelta(days=1)
    return rows


SEEN_FIT: list[str] = []


def strategy(cost: float = 0.0002) -> av.Strategy:
    def fit(rows):
        SEEN_FIT.extend(r["day"] for r in rows)
        xs = sorted(r["x"] for r in rows)
        return {"theta": xs[len(xs) // 2]}

    def rets(rows, params):
        return [r["r"] - cost for r in rows if r["x"] > params.get("theta", 0.0)]
    return av.Strategy(family="synthetic", horizon="daily", fit=fit, returns=rets,
                       declared_ranges={"theta": [-1.0, 1.0]})


def group_g() -> None:
    head("G. THE VALIDATION HARNESS (X-1.6)")
    path = Path(_TMP) / "g.db"
    with Ledger(path) as lg:
        edge = av.run(lg, "known_edge", strategy(), synthetic_rows(0.003), "2026-10-13",
                      fit_rows=250, test_rows=60, min_size=0.01)
        m = edge["metrics"]
        check(edge["passed"], f"a synthetic series with a known edge PASSES (deflated "
              f"Sharpe {m['deflated_sharpe']:.2f}, n={m['n_signals']}, "
              f"hold-out expectancy {m['holdout_expectancy']:.5f})")
        null = av.run(lg, "null", strategy(), synthetic_rows(0.0, seed=11), "2026-10-13",
                      fit_rows=250, test_rows=60)
        check(not null["passed"], f"a null series FAILS ({'; '.join(null['reasons'])})")
        x = strategy().returns(synthetic_rows(0.003), {"theta": 0.0})
        ds = [av.deflated_sharpe(x, n, 252)["deflated_sharpe"] for n in (1, 10, 100, 1000)]
        check(all(a > b for a, b in zip(ds, ds[1:])),
              "the deflated Sharpe falls as the variant count rises "
              f"({', '.join(f'{v:.2f}' for v in ds)} at N = 1, 10, 100, 1000)")
        check(lg.variant_count("synthetic") == 2 and m["n_trials"] == 1
              and null["metrics"]["n_trials"] == 2,
              "every run counts one more variant, and is deflated by the count "
              "including itself")
        SEEN_FIT.clear()
        wf = av.walk_forward(synthetic_rows(0.003), strategy(), 250, 60)
        tested = [d for w in wf["windows"] for d in w["test"]]
        check(SEEN_FIT and not any(av.is_holdout(d) for d in SEEN_FIT),
              f"no fit ever sees a hold-out month (April, August, December): "
              f"{len(SEEN_FIT)} fitted rows, none held out")
        check(not any(av.is_holdout(d) for d in tested) and wf["holdout_rows"] > 0,
              f"and no walk-forward test does; the {wf['holdout_rows']} hold-out rows "
              f"are used once, for the final check")
        usable = [r["day"] for r in synthetic_rows(0.003) if not av.is_holdout(r["day"])]
        w0 = wf["windows"][0]
        gap = usable.index(w0["test"][0]) - usable.index(w0["fit"][1]) - 1
        check(gap == 1 and w0["embargo_rows"] == 1,
              "the embargo: one engine horizon (one row, daily) between fit and test")
        bad = synthetic_rows(0.003)
        bad[300]["available_at"] = "2099-01-01T00:00:00.000000+00:00"
        try:
            av.run(lg, "void", strategy(), bad, "2026-10-13", 250, 60)
            check(False, "a row knowable after its decision voids the run")
        except av.PointInTimeViolation:
            ev = lg.one("SELECT kind FROM loop_events WHERE engine='void'")
            check(ev and ev["kind"] == "validation_void",
                  "a row knowable after its decision voids the run, and says so")
        e = lg.engine("known_edge")
        check(e and e["validated_at"] and e["validated_metrics"]["deflated_sharpe"] >= 1.0
              and "theta" in e["validated_ranges"] and e["status"] == "candidate"
              and e["kill_rule"]["realised_sharpe_below"] == 0.5 * m["deflated_sharpe"],
              "the pass record: metrics, the ranges the fits chose, the kill rule at "
              "birth; promotion is left to X-2.6")
        check(lg.engine("null") is None, "a failed run writes no pass record")
        kinds = [r["kind"] for r in lg.q("SELECT kind FROM loop_events ORDER BY id")]
        check(kinds.count("validation_pass") == 1 and kinds.count("validation_fail") == 1,
              "every run, pass or fail, is a loop event")
        # pit_series picks the vintage knowable at the decision, not a revision.
        sp = Path(_TMP) / "pit.sqlite"
        s = observations.ObservationStore(str(sp))
        s.write_many([{"registry_key": "k", "instrument": None, "observed_at": "2020-01-01",
                       "available_at": "2020-01-02T00:00:00+00:00", "value": 1.0,
                       "source": "s"},
                      {"registry_key": "k", "instrument": None, "observed_at": "2020-01-01",
                       "available_at": "2020-03-01T00:00:00+00:00", "value": 2.0,
                       "source": "s"}])
        s.close()
        ro = ReadOnlyStore(sp)
        rows = av.pit_series(ro, "k", lambda period: "2020-01-05T00:00:00+00:00")
        ro.close()
        check(rows and rows[0]["value"] == 1.0,
              "pit_series takes the vintage knowable at the decision, never the later "
              "revision")
        check(av.refit_allowed({"status": "live", "frozen": 0})
              and not av.refit_allowed({"status": "halved", "frozen": 1})
              and not av.refit_allowed({"status": "validation", "frozen": 1}),
              "no re-fit inside a drawdown: a halved or stopped engine is frozen")


# ---------------------------------------------------------------------------
def group_h() -> None:
    head("H. THE ALLOCATOR (X-1.7)")
    rnd = random.Random(3)
    days = sessions("2026-01-05", 120)
    a = {d: 0.002 + rnd.gauss(0, 0.01) for d in days}
    b = {d: 0.001 + rnd.gauss(0, 0.01) for d in days}
    twin = {d: a[d] + rnd.gauss(0, 0.001) for d in days}
    live = lambda i, st="live", h="daily": {"id": i, "status": st, "horizon": h,  # noqa: E731
                                           "min_size": 0.01}
    # The formula checks run with the heat cap out of the way; the cap has its own.
    wide = acfg.settings()
    wide["allocator"] = {**wide["allocator"], "heat_cap": 100.0}
    res = allocate.weights([live("a")], {"a": a}, {"a": 500}, cfg=wide)
    n = len(days)
    xs = [a[d] for d in days]
    mu = sum(xs) / n * n / (n + 20)
    var = sum((v - sum(xs) / n) ** 2 for v in xs) / (n - 1)
    check(abs(res["weights"]["a"]["weight"] - 0.25 * mu / var) < 1e-9,
          f"one engine: w = 0.25 x shrunk mu / sigma^2 "
          f"({res['weights']['a']['weight']:.3f}; shrinkage {n}/({n}+20))")
    young = allocate.weights([live("a")], {"a": a}, {"a": 50})
    check(young["weights"]["a"]["weight"] == 0.01,
          "below min_signals (50 < 100) an engine is held at min_size")
    pair = allocate.weights([live("a"), live("t")], {"a": a, "t": twin},
                            {"a": 500, "t": 500}, cfg=wide)
    one = allocate.weights([live("a")], {"a": {d: (a[d] + twin[d]) / 2 for d in days}},
                           {"a": 500}, cfg=wide)
    check(pair["clusters"] == [["a", "t"]]
          and abs(sum(v["weight"] for v in pair["weights"].values())
                  - one["weights"]["a"]["weight"]) < 1e-9,
          "two engines correlated above 0.7 are one cluster, sized once and split")
    two = allocate.weights([live("a"), live("b")], {"a": a, "b": b}, {"a": 500, "b": 500})
    check(len(two["clusters"]) == 2, "uncorrelated engines are sized separately")
    cfg = acfg.settings()
    cfg["allocator"] = {**cfg["allocator"], "heat_cap": 0.05}
    capped = allocate.weights([live("a"), live("b")], {"a": a, "b": b},
                              {"a": 500, "b": 500}, cfg=cfg)
    check(abs(capped["gross"] - 0.05) < 1e-9, "the heat cap bounds the gross weight")
    halved = allocate.weights([live("a", "halved")], {"a": a}, {"a": 500}, cfg=wide)
    check(abs(halved["weights"]["a"]["weight"] - 0.5 * 0.25 * mu / var) < 1e-9,
          "a halved engine carries half")
    neg = allocate.weights([live("a")], {"a": {d: -v for d, v in a.items()}}, {"a": 500},
                           cfg=wide)
    check(neg["weights"]["a"]["weight"] == 0.0, "a negative Kelly weight is zero")


# ---------------------------------------------------------------------------
def group_i() -> None:
    head("I. THE GOVERNOR (X-1.8)")
    path = Path(_TMP) / "i.db"
    with Ledger(path) as lg:
        for eid in ("g1", "g2"):
            lg.upsert_engine(eid, "fam", "daily", "live", 0.01, "x")
        cap = {"g1": 1000.0, "g2": 1000.0}
        governor.step(lg, "t0", "2026-10-01", {"g1": 0.0, "g2": 0.0}, cap)
        governor.step(lg, "t1", "2026-10-02", {"g1": -110.0, "g2": 0.0}, cap)
        e = lg.engine("g1")
        check(e["status"] == "halved" and e["frozen"] == 1,
              "-11% from its high-water mark: the engine halves and is frozen")
        out = governor.step(lg, "t2", "2026-10-05", {"g1": -110.0, "g2": 0.0}, cap)
        e = lg.engine("g1")
        check(e["status"] == "validation" and e["frozen"] == 1 and "g1" in out["stop"],
              "-20.8%: it stops -- status validation, frozen, its positions to be exited")
        governor.step(lg, "t3", "2026-10-06", {"g2": -60.0}, cap)
        governor.step(lg, "t4", "2026-10-07", {"g2": -60.0}, cap)
        check(lg.engine("g2")["status"] == "halved", "a second engine halves at -12%")
        governor.step(lg, "t5", "2026-10-08", {"g2": 200.0}, cap)
        check(lg.engine("g2")["status"] == "live" and lg.engine("g2")["frozen"] == 0,
              "and is restored, unfrozen, at a new high-water mark")
        kinds = [r["kind"] for r in lg.q("SELECT kind FROM loop_events WHERE "
                                         "loop='governor' ORDER BY id")]
        check(kinds == ["halve", "stop", "halve", "restore"],
              f"every transition is a loop_events row ({kinds})")
    with Ledger(Path(_TMP) / "i2.db") as lg:
        lg.upsert_engine("g", "fam", "daily", "live", 0.5, "x")
        governor.step(lg, "t0", "2026-10-01", {"g": 0.0}, {"g": 50000.0})
        out = governor.step(lg, "t1", "2026-10-02", {"g": -16000.0}, {"g": 50000.0})
        check(out["lab_halt"] and governor.lab_status(lg) == "halted",
              "the lab at -16% from its high-water mark halts for the operator's review")
        ev = lg.one("SELECT after FROM loop_events WHERE kind='lab_halt'")
        check(json.loads(ev["after"])["threshold"] == -0.15, "at the constitution's -15%")


# ---------------------------------------------------------------------------
def group_j() -> None:
    head("J. THE NIGHTLY LOOP, END TO END (X-1.9)")
    before = sha(Path(STORE))
    reg = Path(_TMP) / "registry.yaml"
    reg.write_text(yaml.safe_dump({"engines": [
        {"id": "fixture_trend", "class": "tests.fixtures.alpha.fixture_engine:FixtureEngine",
         "family": "fixture", "horizon": "daily", "cost_class": "etf", "min_size": 0.01},
        {"id": "fixture_blocked",
         "class": "tests.fixtures.alpha.fixture_engine:BlockedEngine",
         "family": "fixture", "horizon": "daily", "cost_class": "etf", "min_size": 0.01},
    ]}), encoding="utf-8")
    saved = engine_mod.ENGINE_PACKAGES
    engine_mod.ENGINE_PACKAGES = saved + ("tests.fixtures.alpha.",)
    ledger = Path(_TMP) / "j.db"
    try:
        out = nightly.run(asof(DAYS[1]), STORE, ledger, reg)
        with Ledger(ledger) as lg:
            check(lg.engine("fixture_trend")["status"] == "candidate",
                  "a registered engine enters the ledger as a candidate, and trades "
                  "nothing before it passes")
            for eid in ("fixture_trend", "fixture_blocked"):
                lg.set_engine(eid, "x", status="live",
                              validated_metrics={"deflated_sharpe": 1.2,
                                                 "periods_per_year": 252})
        runs = [nightly.run(asof(d), STORE, ledger, reg) for d in DAYS[2:40]]
        check(all(not r["failures"] for r in [out] + runs),
              f"38 nightly runs, every step clean")
        with Ledger(ledger) as lg:
            n = {t: lg.one(f"SELECT COUNT(*) AS n FROM {t}")["n"] for t in (
                "signals", "fills", "positions", "marks", "grades", "edge_posterior",
                "attribution", "equity", "allocations", "holdout")}
            check(n["signals"] > 10 and n["fills"] > 10 and n["grades"] > 5
                  and n["marks"] > 5, f"signals, fills, marks and grades accumulate ({n})")
            sig = lg.q("SELECT instrument FROM signals")
            check(all(s["instrument"] != "BN" for s in sig)
                  and any("BN" in (r["after"] or "") for r in lg.q(
                      "SELECT after FROM loop_events WHERE kind='signals'")),
                  "the blocked engine's BN signals were refused and recorded, never "
                  "written")
            post = lg.one("SELECT * FROM edge_posterior WHERE engine_id='fixture_trend' "
                          "ORDER BY day DESC LIMIT 1")
            check(post and post["prior_strength"] == 20 and post["prior_win_rate"] == 0.5
                  and abs(post["exp_mean"] - post["n"] * post["raw_expectancy"]
                          / (post["n"] + 20)) < 1e-12,
                  f"the posterior shrinks toward zero with the recorded prior (n={post['n']}, "
                  f"strength 20)")
            keys = {r["regime_key"] for r in lg.q("SELECT regime_key FROM attribution")}
            check(any("vol=calm" in k for k in keys) and any("vol=elevated" in k for k in keys)
                  and any("event=1" in k for k in keys),
                  f"P&L is attributed by regime key ({len(keys)} keys)")
            hm = lg.holdout_months()
            check(hm and all(int(m[5:7]) % 4 == 0 for m in hm) and "2026-08" in hm,
                  f"the hold-out months are recorded ({len(hm)}, every fourth month)")
            w = lg.q("SELECT * FROM allocations WHERE kind='proposed' AND day=?",
                     (DAYS[39],))
            check(w and all(abs(x["weight"] - 0.01) < 1e-12 for x in w),
                  "the weights are proposed, at min_size before the sample")
            kinds = {r["kind"] for r in lg.q("SELECT kind FROM loop_events")}
            check({"registered", "paper", "posterior", "weights_proposed", "attribution",
                   "signals", "run"} <= kinds, f"every change is a loop event ({sorted(kinds)})")
        wk = weekly.run(asof(DAYS[39]).replace("21:40", "23:00"), ledger)
        with Ledger(ledger) as lg:
            ap = lg.q("SELECT * FROM allocations WHERE kind='applied'")
            check(not wk["failures"] and len(ap) == 2
                  and lg.one("SELECT COUNT(*) AS n FROM loop_events WHERE kind='rebalance'")["n"] == 1,
                  "the weekly loop applies the proposed weights, one rebalance event")
        line = lab_line.weekly_line(asof(DAYS[39]), ledger)
        check(re.fullmatch(r"Alpha Lab: [+-]\d+\.\d% since \d{4}-\d{2}-\d{2} · 2 engines "
                           r"live · drawdown \d+\.\d% · loop events this week \d+", line)
              is not None, f"the lab line once engines are live: {line}")
        broken = nightly.run(asof(DAYS[40]), Path(_TMP) / "no_store.sqlite", ledger, reg)
        with Ledger(ledger) as lg:
            ev = lg.one("SELECT after FROM loop_events WHERE kind='failure' ORDER BY id "
                        "DESC LIMIT 1")
        check(broken["failures"] == ["open_store"] and ev and "open_store" in ev["after"],
              "a loop that cannot open the store writes its failure to loop_events and "
              "returns; it raises nothing into anything")
    finally:
        engine_mod.ENGINE_PACKAGES = saved
    after = sha(Path(STORE))
    check(before == after, f"THE STORE FILE'S HASH IS UNCHANGED after the full nightly "
          f"and weekly runs ({after[:16]}...)")
    wal = Path(STORE + "-wal")
    check(not wal.exists() or wal.stat().st_size == 0,
          "and nothing is pending in its write-ahead log")


# ---------------------------------------------------------------------------
def group_k() -> None:
    head("K. THE WEEKLY'S LAB LINE (X-1.11)")
    check(lab_line.weekly_line("2026-10-09T22:00:00+00:00", Path(_TMP) / "none.db")
          == "Alpha Lab: not yet live", "no ledger: 'Alpha Lab: not yet live'")
    check(not (Path(_TMP) / "none.db").exists(), "and reading it created nothing")
    fx = json.loads((FIXTURES / "ledger_fixture.json").read_text(encoding="utf-8"))
    path = Path(_TMP) / "k.db"
    with Ledger(path) as lg:
        lg.upsert_engine("only", "f", "daily", "candidate", 0.01, "x")
    check(lab_line.weekly_line("2026-10-09T22:00:00+00:00", path) == lab_line.NOT_LIVE,
          "a candidate is not live: still 'not yet live'")
    with Ledger(path) as lg:
        for e in fx["engines"]:
            lg.upsert_engine(e["id"], e["family"], e["horizon"], e["status"],
                             e["min_size"], "x")
        for a in fx["allocations"]:
            lg.put("allocations", {**a, "cluster": a["engine_id"], "detail": "",
                                   "as_of": "x"})
        hwm = 0.0
        for d, eq in fx["lab_equity"]:
            hwm = max(hwm, eq)
            lg.put("equity", {"engine_id": LAB, "day": d, "equity": eq, "hwm": hwm,
                              "drawdown": eq / hwm - 1, "as_of": "x"})
        for ev in fx["events"]:
            lg.conn.execute("INSERT INTO loop_events (loop, kind, version, as_of, "
                            "written_at) VALUES (?,?,?,?,?)",
                            (ev["loop"], ev["kind"], "fixture", "x", ev["written_at"]))
        lg.conn.commit()
    line = lab_line.weekly_line("2026-10-09T22:00:00+00:00", path)
    check(line == fx["expect_line"], f"the fixture ledger's line: {line}")
    src = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    check(src.count("from alpha") == 1 and src.count("import alpha") == 0
          and src.count("from alpha.lab_line import weekly_line") == 1
          and src.count("weekly_line(") == 1
          and 'ed["alpha_lab"] = weekly_line(now' in src
          and "stack_render.esc(ed[\"alpha_lab\"])" in src,
          "weekly_stack.py holds one hook, reading alpha.db beside the store")
    from daily_cascade import stack_render                      # noqa: PLC0415
    h = stack_render.page_header("Weekly", "stamp", 5, [], None,
                                 extra_html=f' &middot; {stack_render.esc(line)}')
    check(stack_render.esc(line) in h and "<h1" in h,
          "the line prints in the Weekly's header block")


# ---------------------------------------------------------------------------
def _calendar(path: Path) -> str:
    m = re.search(r"^OnCalendar=(.+)$", path.read_text(encoding="utf-8"), re.M)
    return m.group(1).strip() if m else ""


def group_l() -> None:
    head("L. UNITS AND TIMERS (X-1.10)")
    sd = REPO / "deploy" / "systemd"
    names = ["chester-alpha-nightly.service", "chester-alpha-nightly.timer",
             "chester-alpha-weekly.service", "chester-alpha-weekly.timer"]
    check(all((sd / n).is_file() for n in names), "the four unit files exist")
    nt, ct = _calendar(sd / "chester-alpha-nightly.timer"), _calendar(sd / "chester-daily-close.timer")
    check(nt == "Mon-Fri 17:40 America/New_York" and ct == "Mon-Fri 16:45 America/New_York",
          f"the nightly fires weekdays at 17:40 ET, after the 16:45 close ({nt})")
    close = (sd / "chester-daily-close.service").read_text(encoding="utf-8")
    tmo = re.search(r"^TimeoutStartSec=(\d+)min", close, re.M)
    check(tmo and 16 * 60 + 45 + 1 + int(tmo.group(1)) < 17 * 60 + 40,
          "and after the close's whole budget (16:45 + 60 s jitter + its 10-minute cap)")
    wt, wk = _calendar(sd / "chester-alpha-weekly.timer"), _calendar(sd / "chester-weekly.timer")
    wsvc = (sd / "chester-weekly.service").read_text(encoding="utf-8")
    wtmo = int(re.search(r"^TimeoutStartSec=(\d+)min", wsvc, re.M).group(1))
    check(wt == "Sun 06:00 America/New_York" and wk == "Sun 05:00 America/New_York"
          and 5 * 60 + 1 + wtmo < 6 * 60,
          "the weekly fires Sunday 06:00 ET, after the Weekly's 05:00 run and its cap")
    remote = (REPO / "scripts" / "deploy_remote.sh").read_text(encoding="utf-8")
    timers = re.search(r'DEPLOY_TIMERS="([^"]*)"', remote, re.S).group(1).split()
    check("chester-alpha-nightly.timer" not in timers
          and "chester-alpha-weekly.timer" not in timers,
          "neither is in DEPLOY_TIMERS: the deploy copies them, enabling is the operator's")
    for n, mod in (("nightly", "alpha.loops.nightly"), ("weekly", "alpha.loops.weekly")):
        svc = (sd / f"chester-alpha-{n}.service").read_text(encoding="utf-8")
        w = REPO / "scripts" / f"run_alpha_{n}.sh"
        body = w.read_text(encoding="utf-8")
        check(f"ExecStart=%h/chester-reports/scripts/run_alpha_{n}.sh" in svc
              and f'-m {mod}' in body and "git pull --ff-only" in body
              and "EnvironmentFile" not in svc.split("[Service]")[1].split("#")[0],
              f"chester-alpha-{n} runs scripts/run_alpha_{n}.sh -> {mod}, and loads no "
              f"secrets")
    check("altdata.session is-session" in (REPO / "scripts" / "run_alpha_nightly.sh")
          .read_text(encoding="utf-8"), "the nightly wrapper asks the session calendar")


# ---------------------------------------------------------------------------
def group_m() -> None:
    head("M. NO ORDERS (the static gate's scan, X-1.5)")
    import validate_alpha_no_orders as vno                     # noqa: PLC0415
    bad = []
    for p in sorted((REPO / "alpha").rglob("*.py")):
        rel = p.relative_to(REPO)
        pkg = ".".join(rel.with_suffix("").parts[:-1])
        bad += vno.scan(p.read_text(encoding="utf-8"), str(rel), pkg)
    check(not bad, "alpha/ imports no order, gate, broker or network module and uses "
          "no requests, urllib or socket" + (f": {bad[:3]}" if bad else ""))


# ---------------------------------------------------------------------------
SEED_BATCH = FIXTURES / "inbox" / "hypotheses-2026-10-14.yaml"
SEED_SHA256 = "6fdc4dc7a32d659375e22e0dbe1293b480b4c0877c48174a8cc8272d14446626"
SEED_CREATED = "2026-10-14T09:26:23.000Z"


def seed_doc() -> dict:
    return hyp.load_batch(SEED_BATCH.read_bytes().decode("utf-8"))


def group_n() -> None:
    head("N. THE HYPOTHESIS REGISTER (X-2.5)")
    raw = SEED_BATCH.read_bytes()
    check(len(raw) == 8047 and hashlib.sha256(raw).hexdigest() == SEED_SHA256,
          "the first batch is the pinned file: 8,047 bytes, sha256 6fdc4dc7...")
    doc = seed_doc()
    check(hyp.validate_batch(doc) == [] and hyp.budget_errors(doc) == [],
          "it is valid alpha-lab-hypotheses/v1, inside the weekly brief's budgets")
    check([h["local_id"] for h in doc["hypotheses"]] ==
          ["H-001", "H-002", "H-003", "H-004", "H-005"]
          and doc["source"] == "model" and doc["model_idea_rule"] is True,
          "five hypotheses, source model, the model-idea rule declared")
    bad = json.loads(json.dumps(doc))
    bad["schema"] = "v0"
    del bad["hypotheses"][0]["mechanism"]
    bad["hypotheses"][1]["horizon_sessions"] = 0
    bad["hypotheses"][2]["local_id"] = "H-002"
    bad["written_at"] = "2026-10-14T05:17:00"
    errs = hyp.validate_batch(bad)
    check(len(errs) >= 5 and any("schema" in e for e in errs)
          and any("missing mechanism" in e for e in errs)
          and any("horizon_sessions" in e for e in errs)
          and any("repeated" in e for e in errs)
          and any("written_at" in e for e in errs),
          f"a broken batch is refused field by field ({len(errs)} errors)")
    over = json.loads(json.dumps(doc))
    over["hypotheses"] = [dict(over["hypotheses"][0], local_id=f"S-{i}",
                               family=f"f{i % 2}") for i in range(6)]
    be = hyp.budget_errors(over)
    check(any("5 short" in w for _, w in be) and any("family" in w for _, w in be),
          "the weekly brief: at most 5 short-term, at most 2 of a family a batch")
    path = Path(_TMP) / "n.db"
    with Ledger(path) as lg:
        reg = hyp.Register(lg)
        reg.record_batch(doc, hyp.instant(SEED_CREATED), "t")
        ids = [reg.register(h, doc, hyp.instant(SEED_CREATED), "t", "needs_code",
                            "rule in text") for h in doc["hypotheses"]]
        check(ids == [f"HYP-{i:04d}" for i in range(1, 6)]
              and reg.by_local(doc["batch_id"], "H-004")["id"] == "HYP-0004",
              "local ids map to register ids HYP-0001..0005")
        check(all(lg.variant_count(h["family"]) == 1 for h in doc["hypotheses"]),
              "registering counts one variant in each family (10.2 c)")
        for sql, what in (("UPDATE hypotheses SET rule_text='x' WHERE id='HYP-0001'",
                           "the rule"),
                          ("UPDATE hypotheses SET pre_registered_at='2027' WHERE id='HYP-0001'",
                           "the pre-registration instant"),
                          ("DELETE FROM hypotheses WHERE id='HYP-0001'", "the row")):
            try:
                lg.conn.execute(sql)
                check(False, f"{what} cannot be changed")
            except sqlite3.DatabaseError:
                check(True, f"{what} cannot be changed or removed")
        reg.set_status("HYP-0002", "failed", "t", "fixture", result={"n": 3})
        dup = reg.duplicate_of(dict(doc["hypotheses"][1]))
        check(dup and dup[0] == "HYP-0002" and "failed" in dup[1],
              f"a duplicate rule is caught against a FAILED idea too: {dup}")
        near = dict(doc["hypotheses"][3], rule_text="something else entirely",
                    title="A quality split in credit leaks into high-yield before IG")
        d2 = reg.duplicate_of(near)
        check(d2 and d2[0] == "HYP-0004", f"and a near title: {d2}")
        h5 = reg.get("HYP-0005")
        try:
            hyp.refuse_if_unregistered(h5, "2026-10-14T09:00:00+00:00")
            check(False, "the harness refuses a run before the pre-registration")
        except hyp.PreRegistrationViolation:
            check(True, "the harness refuses a run before the pre-registration "
                  "(05:00 ET against the 05:26 ET Drive created time)")
        try:
            hyp.refuse_if_unregistered(h5, "2026-10-14T21:40:00+00:00")
            check(True, "and allows one after it")
        except hyp.PreRegistrationViolation:
            check(False, "and allows one after it")
        for h, what in ((None, "an unregistered rule"),
                        (reg.get("HYP-0002"), "a failed (closed) idea")):
            try:
                hyp.refuse_if_unregistered(h, "2027-01-01T00:00:00+00:00")
                check(False, f"it refuses {what}")
            except hyp.PreRegistrationViolation:
                check(True, f"it refuses {what}")
        bn = dict(doc["hypotheses"][1], local_id="H-BN", universe=["BN"],
                  title="Brookfield fixture")
        try:
            reg.register(bn, doc, hyp.instant(SEED_CREATED), "t", "registered")
            check(False, "a blocked instrument never reaches the register")
        except blocklist.BlockedInstrument:
            check(lg.one("SELECT COUNT(*) AS n FROM hypotheses")["n"] == 5,
                  "a blocked instrument (BN) never reaches the register")
    old = Path(_TMP) / "n_old.db"
    con = sqlite3.connect(old)
    con.execute("CREATE TABLE hypotheses (id TEXT PRIMARY KEY, mechanism TEXT)")
    con.commit()
    con.close()
    with Ledger(old) as lg:
        cols = {r["name"] for r in lg.q("PRAGMA table_info(hypotheses)")}
    check("batch_id" in cols, "an empty Tranche 1 hypotheses table is replaced by "
          "the register's")


GROUPS = [group_a, group_b, group_c_static, group_d, group_e, group_f, group_g,
          group_h, group_i, group_j, group_k, group_l, group_m, group_n]


def main() -> int:
    print(f"{LINE}\nLAYER X, THE ALPHA LAB -- TRANCHES 1 AND 2 (SYNTHETIC STORE, FIXTURES)\n{LINE}")
    for g in GROUPS:
        g()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
