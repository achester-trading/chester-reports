"""
6i-2 -- the Top & Bottom harness's core (A77, 26 Oct 2026; altdata/tb_harness.py,
config/tb_episodes.yaml, docs/ledgers/tb-harness-2026-10-26.md).

    python tools/validate_tb_harness.py

Fixtures only (no store, no network):

  A  the episode set: the thirteen are three tops, six bottoms and four controls,
     each with its dates and its source passage, a session-set one with its basis;
     the extended set (8 bears, 6 near-misses, 5 pre-1970, the false bottoms) is
     flagged and never counted in the thirteen's record
  B  the fixture set classifies as its fixture says: a top an overlay fires on is
     called, an all-read quiet top missed, a quiet control refused, a firing control
     a false call, a bottom not scored, a top with too few triggers read unread
  C  point in time: a row not yet available at the decision date is not read; a
     series before it exists reads "not existent" (a pre-1970 episode, a post-1990
     input) and is never back-filled; before HY OAS is stored the credit leg
     reads not stored, with 6i-3's Baa proxy beside it; Shiller's months are lagged
  D  the pass rule's SHA-256 in the ledger's head is the config's; the rule is
     quoted verbatim; the ledger's own question is asked
  E  no composite: no top_bottom key in the registry, the store opened read-only,
     no write path in the module
"""

from __future__ import annotations

import ast
import datetime as dt
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

from altdata import derived                                    # noqa: E402
from altdata import tb_harness as tb                            # noqa: E402

LEDGER = REPO / "docs" / "ledgers" / "tb-harness-2026-10-26.md"
CSV = REPO / "docs" / "ledgers" / "tb-harness-2026-10-26-episodes.csv"
PASS = FAIL = 0


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  ok    {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


class FakeStore:
    """as_of over {(key, instrument): [(observed, value, available)]}, honouring
    the cutoff and observed_from as the store's own join does."""

    def __init__(self, data: dict) -> None:
        self.data = data

    def as_of(self, key, as_of=None, instrument=None, observed_from=None):
        cut = as_of or "9999"
        out = {}
        for obs, v, avail in self.data.get((key, instrument), []):
            if avail <= cut and (not observed_from or obs >= observed_from):
                out[obs] = {"observed_at": obs, "value_num": v, "available_at": avail}
        return [out[k] for k in sorted(out)]


def daily(start: str, end: str, value, lag_days: int = 0) -> list:
    """A business-daily series, each row available `lag_days` after its day.
    `value` is a constant or a function of the day's index."""
    d, i, out = dt.date.fromisoformat(start), 0, []
    stop = dt.date.fromisoformat(end)
    while d <= stop:
        if d.weekday() < 5:
            v = value(i) if callable(value) else value
            out.append((d.isoformat(), float(v),
                        f"{(d + dt.timedelta(days=lag_days)).isoformat()}T21:00:00+00:00"))
            i += 1
        d += dt.timedelta(days=1)
    return out


def monthly(start: str, end: str, value) -> list:
    """Shiller-like: month-start rows all stamped with one recent file instant."""
    d, out = dt.date.fromisoformat(start), []
    while d <= dt.date.fromisoformat(end):
        out.append((d.isoformat(), float(value), "2026-10-01T00:00:00+00:00"))
        d = tb._add_months(d, 1)
    return out


def store(hot: bool) -> FakeStore:
    """2021-2022, every input stored. `hot` sets the Concentration overlay to fire
    (CAPE 38, ERP below 1.5, VIX 14); otherwise every trigger is quiet."""
    s, e = "2020-06-01", "2022-12-30"
    return FakeStore({
        ("shiller.cape", None): monthly("2019-01-01", "2022-12-01", 38 if hot else 22),
        ("shiller.gs10", None): monthly("2019-01-01", "2022-12-01", 1.5),
        ("index.forward_pe", None): daily(s, e, 22 if hot else 15),
        ("yfinance.mkt_vix", None): daily(s, e, 14 if hot else 25),
        ("fred.hy_oas", None): daily(s, e, 3.5),
        ("fred.ig_oas", None): daily(s, e, 0.9),
        ("calc.net_liquidity", None): daily(s, e, 6.0e12),
        ("fred.bank_reserves", None): daily(s, e, 3.4e6),
        ("fred.sofr", None): daily(s, e, 0.05),
        ("fred.iorb", None): daily(s, e, 0.15),
        ("fred.rrp", None): daily(s, e, 1500.0),
        ("fred.tga", None): daily(s, e, 700000.0),
    })


def group_a(cfg: dict) -> None:
    print("A. the episode set")
    cal = cfg["calibration"]
    by = {c: [e for e in cal if e["class"] == c] for c in ("top", "bottom", "control")}
    check(len(cal) == 13 and [len(by[c]) for c in by] == [3, 6, 4],
          f"the thirteen: three tops, six bottoms, four controls "
          f"({[len(by[c]) for c in by]})")
    check(all(e.get("dates") and e.get("source") for e in cal)
          and all(len(e["dates"]) == 2 for e in by["control"]),
          "each names its decision dates and its source passage; a control has its "
          "high and its low")
    check(all(e.get("basis") for e in cal if e.get("session_set")),
          f"every session-set episode states its basis "
          f"({sum(1 for e in cal if e.get('session_set'))} session-set)")
    check([e["id"] for e in by["top"]] == ["top_2000", "top_2007", "top_2022"]
          and any(e["id"] == "control_2018" and e["dates"][-1] == "2018-12-24"
                  and not e["session_set"] for e in cal),
          "the papers' own fixes: the 2000, 2007 and 2022 tops; 24 Dec 2018 a control")
    ex = cfg["extended"]
    n = {k: len(ex[k]["episodes"]) for k in ("bears", "near_misses", "pre_1970", "false_bottoms")}
    check(n == {"bears": 8, "near_misses": 6, "pre_1970": 5, "false_bottoms": 12},
          f"the extended set: 8 bears, 6 near-misses, 5 pre-1970, 12 false bottoms ({n})")
    cal_ids = {e["id"] for e in cal}
    check(not cal_ids & {x["id"] for x in tb.extended_dates(cfg)},
          "the extended set shares no id with the thirteen")
    fake = [{"id": e["id"], "class": e["class"], "classification":
             {"top": "called", "control": "refused", "bottom": "not scored"}[e["class"]]}
            for e in cal]
    rec = tb.record(fake)
    check(rec["top"]["n"] == 3 and rec["control"]["n"] == 4 and rec["bottom"]["n"] == 6,
          "the record counts the thirteen alone: the extended set never enters it")


def group_b(cfg: dict) -> None:
    print("B. the fixture set classifies as its fixture says")
    now = "2026-10-26T12:00:00+00:00"
    hot, cold = store(True), store(False)
    day = "2022-06-15"

    def cls(st, c, dates):
        return tb.classify(c, [tb.overlays_at(st, cfg, d, now) for d in dates])
    ovs = {o["id"]: o for o in tb.overlays_at(hot, cfg, day, now)}
    check(ovs["concentration"]["state"] == tb.FIRES and ovs["concentration"]["fired"] >= 3,
          f"the hot fixture fires Concentration ({tb.state_text(ovs['concentration'])})")
    cold_ovs = {o["id"]: o for o in tb.overlays_at(cold, cfg, day, now)}
    check(all(o["state"] == tb.CLEAR for o in tb.scored(list(cold_ovs.values()))),
          f"the cold fixture reads every overlay CLEAR "
          f"({[tb.state_text(o) for o in cold_ovs.values()]})")
    check(cls(hot, "top", [day]) == "called", "a top an overlay fires on is called")
    check(cls(cold, "top", [day]) == "missed", "an all-read quiet top is missed")
    check(cls(cold, "control", [day, "2022-06-30"]) == "refused",
          "a control with no overlay firing at either date is refused")
    check(cls(hot, "control", [day, "2022-06-30"]) == "false call",
          "a control an overlay fires on is a false call")
    check(cls(hot, "bottom", [day]) == "not scored",
          "a bottom is not scored by the top-side overlays")
    check(cls(FakeStore({}), "top", [day]) == "unread",
          "a top with too few triggers read is unread, never missed")
    trs = {t["id"]: t for t in ovs["concentration"]["triggers"]}
    check(abs(trs["erp"]["value"] - (100 / 38 - 1.5)) < 1e-9,
          f"ERP is 100/CAPE less the 10-year, as the config defines it ({trs['erp']['shown']})")
    lq = {t["id"]: t for t in cold_ovs["liquidity"]["triggers"]}
    check(abs(lq["sofr_iorb"]["value"] - (-10.0)) < 1e-6 and lq["sofr_iorb"]["state"] == "quiet",
          f"SOFR less IORB is read in bp over five common sessions ({lq['sofr_iorb']['shown']})")
    hy = {t["id"]: t for t in cold_ovs["hy_accel"]["triggers"]}
    check(hy["ig_level"]["value"] == 90.0 and hy["ig_level"]["state"] == "quiet",
          "OAS is read in bp (IG 0.9% is 90bp, quiet against 110bp)")


def group_c(cfg: dict) -> None:
    print("C. point in time")
    now = "2026-10-26T12:00:00+00:00"
    late = FakeStore({("yfinance.mkt_vix", None): daily("2022-01-03", "2022-06-30", 30, lag_days=1)})
    r = tb.read_input(late, cfg, "vix", "2022-06-15", now)
    check(r["state"] == "read" and r["pts"][-1][0] == "2022-06-14",
          f"a row available the day after its date is not read at that date "
          f"(latest knowable {r['pts'][-1][0] if r['pts'] else None})")
    pre = tb.trigger(store(True), cfg, next(t for o in cfg["overlays"] for t in o["triggers"]
                                            if t["id"] == "vix"), "1929-09-16", now)
    check(pre["state"] == tb.NOT_EXISTENT and "not existent before 1990-01-02" in pre["shown"],
          f"a pre-1970 episode reads a post-1990 input as not existent ({pre['shown']!r})")
    ovs = {o["id"]: o for o in tb.overlays_at(store(True), cfg, "1929-09-16", now)}
    check(ovs["hy_accel"]["state"] == tb.OVERLAY_NOT_EXISTENT,
          f"an overlay too few of whose triggers existed is NOT EXISTENT "
          f"({tb.state_text(ovs['hy_accel'])})")
    hy = next(t for t in ovs["hy_accel"]["triggers"] if t["id"] == "hy_30d")
    check(hy["state"] == tb.NOT_EXISTENT and "not existent before 1996-12-31" in hy["shown"],
          f"the credit leg before HY OAS exists reads it as not existent; 6i-3's Baa "
          f"proxy prints beside it ({hy['shown']!r})")
    gap = tb.read_input(FakeStore({}), cfg, "hy_oas", "2010-06-15", now)
    check(gap["state"] == "not stored" and "not stored as of 2010-06-15" in gap["text"],
          "and after HY OAS exists but before the store holds it, not stored, with why")
    sh = FakeStore({("shiller.cape", None): [("2022-05-01", 30.0, "2026-10-01T00:00:00+00:00"),
                                             ("2022-03-01", 31.0, "2026-10-01T00:00:00+00:00")]})
    r = tb.read_input(sh, cfg, "cape", "2022-06-15", now)
    check(r["state"] == "read" and r["pts"][-1] == ("2022-06-01", 31.0),
          f"Shiller's months are lagged {cfg['point_in_time']['shiller_lag_months']}: "
          f"in mid-June 2022 March's CAPE is the newest knowable ({r['pts'][-1] if r['pts'] else None})")
    check(not cfg["inputs"]["hy_oas"].get("pending")
          and any(o.get("proxy_of") == "hy_accel" for o in cfg["overlays"]),
          "6i-3 resolved the pending credit leg: the Baa proxy overlay sits beside HY "
          "Spread Acceleration (validate_tb_harness_fpr.py holds it)")


def group_d(cfg: dict) -> None:
    print("D. the ledger's head")
    if not LEDGER.exists():
        check(False, f"{LEDGER.relative_to(REPO)} exists")
        return
    text = LEDGER.read_text(encoding="utf-8")
    m = re.search(r"\| Pass rule SHA-256 \| `([0-9a-f]{64})` \|", text)
    check(m and m.group(1) == tb.rule_hash(cfg),
          f"the pass rule's SHA-256 at the ledger's head is the config's "
          f"({m.group(1)[:12] if m else None} against {tb.rule_hash(cfg)[:12]})")
    check(f"> {' '.join(str(cfg['pass_rule']).split())}" in text,
          "the rule is quoted verbatim at the head")
    check("Does the harness reproduce \"tops 0/3, bottoms 4/6, controls 4/4\"?" in text
          and re.search(r"\| Verdict \| \*\*(PASS|FAIL|INSUFFICIENT)", text),
          "the ledger asks its own question and states a verdict under the rule")
    check(CSV.exists() and CSV.read_text(encoding="utf-8").count("\ncalibration,") == 17,
          "its episodes CSV carries the thirteen's 17 decision dates")


def group_e() -> None:
    print("E. no composite, no write")
    reg = derived._load_registry()
    bad = sorted(k for k in reg if k.startswith(("top_bottom", "tb.", "calc.tb_")))
    check(not bad, f"no top_bottom composite or harness key is registered {bad[:3]}")
    src = (REPO / "altdata" / "tb_harness.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    calls = {n.func.attr for n in ast.walk(tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    check(not calls & {"open_writer", "write_rows", "insert", "executemany", "commit"},
          "the module calls no store writer")
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "s.db"
        c = sqlite3.connect(p)
        c.execute("CREATE TABLE observations (x)")
        c.commit()
        c.close()
        r = tb.Reader(str(p))
        try:
            r.conn.execute("INSERT INTO observations VALUES (1)")
            ro = False
        except sqlite3.OperationalError:
            ro = True
        r.close()
    check(ro, "the harness's reader opens the store read-only (mode=ro)")


def main() -> int:
    line = "=" * 72
    print(f"{line}\n6i-2 -- the T&B harness core (fixtures)\n{line}")
    cfg = tb.config()
    group_a(cfg)
    group_b(cfg)
    group_c(cfg)
    group_d(cfg)
    group_e()
    print(f"\n{line}\n{PASS} passed, {FAIL} failed\n{line}")
    print("VALIDATION FAILED" if FAIL else "VALIDATION PASSED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
