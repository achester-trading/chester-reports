"""
B134 (session B, 6 Nov 2026): signal-triage Batch 23 item 124c(i), the vol-state
read (the order's 106c(i)).

  A  ABSENCE. An empty store prints "not computed" and the hook "not built"; an
     input never stored prints "n/a (... not stored)" and leaves the mean; an
     input before its first day is n/a; fewer than two inputs give no state.
  B  THE RULE. The decile is the bin of the unweighted mean of the available
     percentiles (1 below 10 ... 10 at 90 and above); the percentile is the
     expanding own-history share at or below the day's value; nothing is
     weighted.
  C  THE CALIBRATION. On a hand fixture: n, hits, the Wilson interval by its
     formula, the 5- and 20-session transitions; the committed ledger's
     computation at the SHA-256 the config and the module carry, and the config's
     decile table equal to the ledger's.
  D  THE STORE AND THE PRINT. A seeded temporary store: compute writes the decile
     and the five percentiles, each available no earlier than its inputs; a dry
     run and a re-run write nothing; the close's block (after item 52's) carries
     the decile, the inputs with their windows, the calibrated probability with
     its n, the transitions and the hook's value; the Weekly's row.
  E  THE HOOK. vol_state_k reads config's table, None for no state, a floor no
     narrower in a higher decile.
  F  HYGIENE. The six keys registered, trigger-ineligible and barred from the
     market-state object (named in neither its config nor regime.py); the module
     fetches nothing outside its ledger's public path; the gate in the list.

The clock is pinned to GATE_NOW. Synthetic fixtures only: no live store, no
network, no model.

    python tools/validate_item_124_c1.py
"""

from __future__ import annotations

import datetime as dt
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gate_tmp  # noqa: E402

from altdata import derived, observations  # noqa: E402
from altdata import vol_state as vs  # noqa: E402

GATE_KIND = "code"
GATE_NOW = "2026-11-06T22:00:00+00:00"

PASS = FAIL = 0
LINE = "=" * 78
CFG = vs.config()


def pin_clock() -> None:
    from altdata import session                                 # noqa: PLC0415
    session.utc_now = lambda: dt.datetime.fromisoformat(GATE_NOW)


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


def weekdays(n: int, end: str = "2026-11-05") -> list[str]:
    out, d = [], dt.date.fromisoformat(end)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= dt.timedelta(days=1)
    return out[::-1]


def fixture(n: int = 400, end: str = "2026-11-05") -> dict[str, list[tuple]]:
    """A calm stretch, then a volatile one at the end; VIX tracks it."""
    days = weekdays(n, end)
    spx, vix, v3m, vvx = [], [], [], []
    px = 4000.0
    for i, d in enumerate(days):
        loud = i >= n - 15
        r = (0.025 if i % 2 else -0.024) if loud else 0.002 * math.sin(i)
        px *= 1 + r
        av = f"{d}T21:00:00+00:00"
        spx.append((d, px, av))
        vl = 30.0 + i % 3 if loud else 14.0 + (i % 7) * 0.2
        vix.append((d, vl, av))
        v3m.append((d, vl / (1.05 if loud else 0.88), av))
        vvx.append((d, 120.0 if loud else 85.0 + i % 5, av))
    return {"spx": spx, "vix": vix, "vix3m": v3m, "vvix": vvx}


def cfg_short(**over) -> dict:
    """The config with a short history and early `from` dates, for fixtures."""
    import copy                                                 # noqa: PLC0415
    c = copy.deepcopy(CFG)
    c["min_history"] = over.get("min_history", 50)
    for x in c["inputs"]:
        x["from"] = over.get("from", "2000-01-03")
    return c


def seed(db: str, series: dict) -> None:
    keymap = {"spx": "yfinance.mkt_gspc", "vix": "fred.vix",
              "vix3m": "yfinance.mkt_vix3m", "vvix": "yfinance.mkt_vvix"}
    rows = []
    for name, pts in series.items():
        for d, v, a in pts:
            rows.append({"registry_key": keymap[name], "instrument": None,
                         "observed_at": d, "available_at": a, "value": v,
                         "source": "fred" if name == "vix" else "yfinance",
                         "availability_kind": "observed"})
    with observations.ObservationStore(db) as st:
        st.write_many(rows)


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. ABSENCE")
    db = str(Path(gate_tmp.mkdtemp("vol_state_empty_")) / "chester.db")
    with observations.ObservationStore(db) as st:
        r = vs.read(st, GATE_NOW)
    b = vs.block(r)
    check(r["decile"] is None and "not computed" in b["lines"][0]
          and vs.DECILE_KEY in b["lines"][0],
          "an empty store prints 'not computed', naming the key")
    check(vs.vol_state_k(None) is None and vs.NOT_BUILT == "not built",
          "no state, no ATR multiple: the hook's 'not built' stands")
    s = fixture()
    s.pop("vvix")
    t = vs.daily_table(s, cfg_short())
    last = t[-1]
    check(last["pct"]["vvix"] is None and last["raw"]["vvix"] is None
          and last["decile"] is not None,
          "an input never stored is n/a and the state is the mean of the rest")
    db2 = str(Path(gate_tmp.mkdtemp("vol_state_novvix_")) / "chester.db")
    seed(db2, s)
    with observations.ObservationStore(db2) as st:
        vs.compute(as_of=GATE_NOW, store=st)
        r2 = vs.read(st, GATE_NOW)
    row = next(x for x in r2["inputs"] if x["id"] == "vvix")
    check(row["pct"] is None and "not stored" in row["why"]
          and "yfinance.mkt_vvix" in row["why"],
          "the read prints 'n/a (yfinance.mkt_vvix not stored)' for it")
    t3 = vs.daily_table(fixture(), cfg_short(**{"from": "2026-10-01"}))
    early = next(x for x in t3 if x["day"] < "2026-10-01")
    check(all(v is None for v in early["pct"].values()) and early["decile"] is None,
          "before an input's first day it is n/a; no inputs, no state")
    check(vs.combine({"vix": 50.0, "rv20": None}, CFG) == (None, None),
          "one available input is below min_inputs: no state")


def group_b() -> None:
    head("B. THE RULE")
    check([vs.decile_of(x) for x in (0, 9.99, 10, 55, 89.99, 90, 100)]
          == [1, 1, 2, 6, 9, 10, 10] and vs.decile_of(None) is None,
          "the decile is the score's bin: 1 below 10 ... 10 at 90 and above")
    s, d = vs.combine({"vix": 80.0, "rv20": 60.0, "term": None, "vvix": 100.0,
                       "bigmove": 40.0}, CFG)
    check(s == 70.0 and d == 8, "the score is the unweighted mean of the available "
          "percentiles (80, 60, 100, 40 -> 70, decile 8)")
    check(CFG["rule"]["combine"] == "mean_of_available" and "weights" not in CFG["rule"],
          "the config declares the mean and carries no weights")
    c = cfg_short(min_history=3)
    days = weekdays(30)
    spx = [(d, 100.0 + i, f"{d}T21:00:00+00:00") for i, d in enumerate(days)]
    vixv = [12, 14, 13, 20, 11]
    vix = [(d, float(vixv[i % 5]), f"{d}T21:00:00+00:00") for i, d in enumerate(days)]
    t = vs.daily_table({"spx": spx, "vix": vix}, c)
    hist = [float(vixv[i % 5]) for i in range(4)]
    want = sum(1 for x in hist if x <= hist[-1]) / 4 * 100
    check(t[1]["pct"]["vix"] is None and t[2]["pct"]["vix"] is not None
          and abs(t[3]["pct"]["vix"] - want) < 1e-9,
          f"the percentile is the expanding own-history share at or below the "
          f"day's value ({want:.0f} on the fourth day; n/a before min_history)")
    r = [x for x in t if x["raw"]["rv20"] is not None][0]
    lr = [math.log(spx[i + 1][1] / spx[i][1]) for i in range(20)]
    m = sum(lr) / 20
    sd = math.sqrt(sum((x - m) ** 2 for x in lr) / 19) * math.sqrt(252) * 100
    check(abs(r["raw"]["rv20"] - sd) < 1e-9 and r["day"] == days[20],
          "rv20 is the 20 log returns' sample sd, annualised, from the 21st close")


def group_c() -> None:
    head("C. THE CALIBRATION")
    days = weekdays(40)
    dec = [10] * 5 + [1] * 35
    rets = [0.0] * 40
    rets[3] = 0.04                       # a 3% day inside the first rows' window
    table = [{"day": d, "decile": dec[i], "ret": rets[i]} for i, d in enumerate(days)]
    cal = vs.calibrate(table, CFG, since=days[0])
    t10, t1 = cal["deciles"][10], cal["deciles"][1]
    check(t10["n"] == 5 and t10["k"] == 3 and t1["n"] == 25 and t1["k"] == 0,
          "n and hits per decile: |r| >= 3% within the next ten sessions")
    lo, hi = vs.wilson(3, 5)
    z = 1.959964
    p = 0.6
    c0 = (p + z * z / 10) / (1 + z * z / 5)
    check(abs(t10["lo"] - lo) < 1e-12 and abs((lo + hi) / 2 - c0) < 1e-9
          and lo < p < hi, "the Wilson 95% interval, by its formula")
    o5 = t10["t5_odds"]
    check(o5 == {"same": 0.0, "higher": 0.0, "lower": 1.0}
          and t1["t20_odds"]["same"] == 1.0,
          "transitions: decile 10 five on is lower in every row; decile 1 stays")
    ledger = REPO / CFG["calibration"]["ledger"]
    text = ledger.read_text(encoding="utf-8")
    check(vs.ledger_sha(text) == vs.computation_sha256()
          == CFG["calibration"]["computation_sha256"],
          "the ledger's computation is at the SHA-256 the config and the module carry")
    lt = vs.ledger_config_block(text)
    ct = {int(k): v for k, v in CFG["calibration"]["deciles"].items()}
    check({int(k): v for k, v in lt.items()} == ct and len(ct) == 10,
          "the config's decile table equals the ledger's, all ten rows")
    ps = [ct[d]["p"] for d in range(6, 11)]
    check(all(a <= b for a, b in zip(ps, ps[1:])),
          f"the committed calibration rises through the top half ({ps})")
    check("never edited by hand" in text and "Pass rule" in text
          and "Wilson" in text, "the ledger's head: written once, no pass rule invented")


def group_d() -> None:
    head("D. THE STORE AND THE PRINT")
    db = str(Path(gate_tmp.mkdtemp("vol_state_store_")) / "chester.db")
    s = fixture()
    seed(db, s)
    import copy                                                 # noqa: PLC0415
    with observations.ObservationStore(db) as st:
        dry = vs.compute(as_of=GATE_NOW, store=st, dry_run=True)
        n0 = st.conn.execute("SELECT COUNT(*) FROM observations WHERE registry_key "
                             "LIKE 'calc.vol_state.%'").fetchone()[0]
        r1 = vs.compute(as_of=GATE_NOW, store=st)
        r2 = vs.compute(as_of=GATE_NOW, store=st)
        rows = st.conn.execute("SELECT registry_key, observed_at, available_at FROM "
                               "observations WHERE registry_key LIKE 'calc.vol_state.%'"
                               ).fetchall()
        rd = vs.read(st, GATE_NOW)
        wk = vs.week_row(st, GATE_NOW, weekdays(5))
        from daily_cascade import vol_state_block as vb         # noqa: PLC0415
        built = {"mechanics": {"items": [], "subsections": [
            {"title": "Dealer T1"}, {"title": "Volatility event"}, {"title": "Fragility"}]}}
        vb.close_extras(built, st, GATE_NOW)
        ws = vb.weekly_subsection(st, GATE_NOW, weekdays(5))
    check(dry["computed"] > 0 and n0 == 0, "a dry run computes and writes nothing")
    check(r1["written"] == r1["computed"] > 0 and r2["written"] == 0,
          "compute writes the rows once; a re-run writes nothing")
    keys = {k for k, _, _ in rows}
    check(keys == set(vs.KEYS), "the decile and the five percentiles are stored")
    check(all(a >= f"{d}T21:00:00+00:00" for _, d, a in rows),
          "each row is available no earlier than the inputs it read")
    b = vs.block(rd)
    txt = " ".join(b["lines"])
    check(rd["decile"] is not None and f"decile {rd['decile']} of 10" in txt
          and "session-set" in txt, "the block opens on today's decile and its rule")
    check("P(|return| ≥ 3% within 10 sessions" in txt and "n " in txt
          and "95% interval" in txt and "in 5 sessions" in txt and "in 20 sessions" in txt,
          "the calibrated probability with its n and interval, and both transitions")
    check(f"ATR multiple {vs.vol_state_k(rd['decile']):g}" in txt,
          "the sizing hook's value prints")
    cols = b["table"]["columns"]
    check(cols == ["Input", "Percentile", "Window"] and len(b["table"]["rows"]) == 5
          and all("full history from" in r[2] for r in b["table"]["rows"]),
          "the five inputs with their percentiles and stored windows")
    subs = built["mechanics"]["subsections"]
    check([x["title"] for x in subs] == ["Dealer T1", "Volatility event", "Vol state",
                                         "Fragility"]
          and built["mechanics"]["items"][0]["key"] == "mech:vol_state",
          "the close's block sits directly after item 52's")
    nb = {"mechanics": {"items": [], "subsections": [{"title": "Dealer T1"}]}}
    with observations.ObservationStore(db) as st:
        vb.close_extras(nb, st, GATE_NOW)
    check(nb["mechanics"]["subsections"][0]["title"] == "Vol state",
          "with no item-52 block it leads Mechanics")
    check(wk.startswith("Vol state, the week (decile of 10): ")
          and wk.count("·") == 4 and ws and ws[0]["paragraph_wanted"] is False,
          f"the Weekly's one row ({wk})")
    c2 = copy.deepcopy(CFG)
    c2["calibration"]["deciles"] = {}
    b2 = vs.block(dict(rd, calibration=None))
    check(any("not in config" in x for x in b2["lines"]),
          "a missing calibration table says so, never a figure")
    src = (REPO / "daily_cascade" / "stack.py").read_text(encoding="utf-8")
    i, j = src.index("batch14_b1_block.close_extras"), src.index("vol_state_block.close_extras")
    check(i < j, "in the close it runs after item 65's extras, so it lands after them")
    wsrc = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    check("vol_state_block.weekly_subsection" in wsrc, "the Weekly reads the row")
    mf = (REPO / "altdata" / "market_features.py").read_text(encoding="utf-8")
    check("vol_state.compute(" in mf and "vol_state.default_first_day" in mf,
          "the features pass computes recent days, never the history")


def group_e() -> None:
    head("E. THE HOOK")
    ks = [vs.vol_state_k(d) for d in range(1, 11)]
    check(all(isinstance(k, float) for k in ks)
          and ks == [float(CFG["k_table"][d]) for d in range(1, 11)],
          f"vol_state_k reads config's table ({ks})")
    check(all(a <= b for a, b in zip(ks, ks[1:])) and ks[-1] > ks[0],
          "a floor no narrower in a higher decile, and wider at the top")
    check(vs.vol_state_k("7") == float(CFG["k_table"][7]),
          "a decile given as text reads the same row")


def group_f() -> None:
    head("F. HYGIENE")
    reg = {k: derived.registry_entry(k) for k in vs.KEYS}
    check(all(reg.values()) and all(e.get("trigger_eligible") is False for e in reg.values()),
          "the six keys registered, none trigger-eligible")
    check(all(derived.market_state_barred(e) for e in reg.values()),
          "every calc.vol_state.* key barred from the market-state object")
    ms = (REPO / "config" / "market_state.yaml").read_text(encoding="utf-8")
    rg = (REPO / "regime.py").read_text(encoding="utf-8")
    check("vol_state" not in ms and "vol_state" not in rg,
          "named in neither the market-state config nor regime.py")
    code = (REPO / "altdata" / "vol_state.py").read_text(encoding="utf-8")
    body = code.split("def public_series", 1)[0]
    check(not re.search(r"import_yfinance|requests|urllib|http_get|vendor|flashalpha|_fetch_symbol", body),
          "outside the ledger's public path the module fetches nothing and reads no vendor")
    used = {k for x in CFG["inputs"] for k in x["keys"]}
    check(all(derived.registry_entry(k) for k in used),
          f"every declared input key is already registered ({sorted(used)})")
    mk = __import__("gate_list").makefile_text(REPO)
    check("tools/validate_item_124_c1.py" in mk, "the gate is in the list")


def main() -> int:
    pin_clock()
    print(f"the gate's clock is pinned to {GATE_NOW}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
