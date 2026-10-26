"""
6i-3 and 6i-4 -- the T&B harness's continuous false-positive rate, its long credit
proxy, and the reports that read it (A79, 26 Oct 2026; altdata/tb_harness.py,
config/tb_episodes.yaml, docs/ledgers/tb-harness-fpr-2026-10-26.md).

    python tools/validate_tb_harness_fpr.py

Fixtures only (no live store, no network):

  A  the pre-registration: the FPR rule's SHA-256 at the ledger's head is the
     config's, the rule is quoted verbatim there, the window is the config's,
     and the result sits below the marker, never in the head
  B  the rule: a fired reading with no episode start inside the window is a false
     positive; one with a top inside it is not; one whose window runs past the
     last session with no start is censored; runs count consecutive fires; the
     episode starts are the tops only (controls begin none)
  C  end to end on a fixture: the Baa proxy fires before the 2007 top (true) and
     in a quiet year (false); the cached reader's join is the store's join, row
     for row, vintages included; before DBAA exists the proxy reads BAA's monthly,
     before 1962 it is not existent; the proxy is printed, never counted in the
     calibration's record
  D  the long proxy: DBAA and BAA in the FRED pull with their ids and cadences;
     calc.baa_less_10y and _m registered, calculated, barred from the market-state
     object, each matched by its own lag family; computed same-session (daily)
     and against the month's mean 10-year (monthly), knowable no earlier than its
     inputs
  E  the reports (6i-4): the Monthly's hook prints the three overlays' states
     with their trigger counts, the episode record k of n per class and the
     false-positive rate per overlay with n, and no composite; the Quarterly's
     credit row "HY spread acceleration" reads the overlay, not its old reason
"""

from __future__ import annotations

import datetime as dt
import sqlite3
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

from altdata import derived                                    # noqa: E402
from altdata import tb_harness as tb                            # noqa: E402

LEDGER = REPO / "docs" / "ledgers" / "tb-harness-fpr-2026-10-26.md"
PASS = FAIL = 0
NOW = "2026-10-26T12:00:00+00:00"


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


def bdays(start: str, end: str) -> list[str]:
    d, out = dt.date.fromisoformat(start), []
    while d <= dt.date.fromisoformat(end):
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def avail(day: str) -> str:
    return f"{(dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat()}T21:00:00+00:00"


# ---------------------------------------------------------------------------
def group_a(cfg: dict) -> None:
    print("A. the pre-registration")
    if not LEDGER.exists():
        check(False, f"{LEDGER.relative_to(REPO)} exists")
        return
    text = LEDGER.read_text(encoding="utf-8")
    check(tb.FPR_MARKER in text, "the ledger carries the marker between head and result")
    head = text.split(tb.FPR_MARKER)[0]
    h = tb.fpr_hash(cfg)
    check(h in head, f"the FPR rule's SHA-256 at the ledger's head is the config's ({h[:12]})")
    check(" ".join(str(cfg["fpr_rule"]).split()) in " ".join(head.split()),
          "the rule is quoted verbatim at the head")
    check(f"{cfg['fpr']['window_days']} calendar days" in head,
          f"the head states the config's window ({cfg['fpr']['window_days']} days)")
    check("## Result" not in head and "## Result" in text.split(tb.FPR_MARKER)[1],
          "the result is below the marker, never in the head")
    check(tb.prereg_head(cfg) == head and cfg["fpr"]["preregistration"].endswith(LEDGER.name),
          "the run reads its head from this pre-registration")
    csvp = LEDGER.with_suffix(".csv")
    check(csvp.exists() and csvp.read_text(encoding="utf-8").splitlines()[0]
          == ",".join(tb.FPR_COLUMNS), "its CSV carries the registered columns")


def group_b(cfg: dict) -> None:
    print("B. the rule")
    starts = ["2007-10-09"]
    c = tb.classify_fired(["2015-03-02"], starts, "2026-09-21", 365)
    check(c == {"true_positive": 0, "false_positive": 1, "censored": 0},
          f"a fired reading with no episode in the window counts as a false positive ({c})")
    c = tb.classify_fired(["2007-01-10"], starts, "2026-09-21", 365)
    check(c == {"true_positive": 1, "false_positive": 0, "censored": 0},
          f"a fired reading with a top inside the window does not ({c})")
    c = tb.classify_fired(["2006-10-01"], starts, "2026-09-21", 365)
    check(c["false_positive"] == 1, "a top 373 days later is outside a 365-day window")
    c = tb.classify_fired(["2026-03-02"], starts, "2026-09-21", 365)
    check(c == {"true_positive": 0, "false_positive": 0, "censored": 1},
          f"a fire whose window runs past the last session, no start in it, is censored ({c})")
    seq = [("2010-01-04", tb.FIRES), ("2010-01-05", tb.FIRES), ("2010-01-06", tb.CLEAR),
           ("2010-01-07", tb.FIRES), ("2010-01-08", tb.UNREAD),
           ("2010-01-11", tb.OVERLAY_NOT_EXISTENT)]
    r = tb.fpr_from_states({"x": seq}, [], "2026-09-21", 365)[0]
    check(r["runs"] == 2 and r["fired"] == 3 and r["scored"] == 4
          and r["unread"] == 1 and r["not_existent"] == 1,
          f"runs count consecutive fires; unread and not existent never score ({r})")
    st = tb.episode_starts(cfg)
    controls = {d for e in cfg["calibration"] if e["class"] == "control" for d in e["dates"]}
    check(len(st) == 13 and "2007-10-09" in st and "1929-09-16" in st
          and not (controls & set(st)),
          f"the episode starts are the tops only: {len(st)}, no control date among them")


def proxy_fixture() -> FakeStore:
    """Baa less the 10-year, daily 2006-2016: quiet at 180bp, widening into the
    2007 top (from June 2007), and once more in a quiet 2015."""
    rows = []
    for d in bdays("2006-01-02", "2016-12-30"):
        v = 180.0
        if "2007-06-01" <= d <= "2007-12-31":
            v = 180.0 + 1.5 * (dt.date.fromisoformat(d) - dt.date(2007, 6, 1)).days
        if "2015-06-01" <= d <= "2015-09-30":
            v = 180.0 + 1.5 * (dt.date.fromisoformat(d) - dt.date(2015, 6, 1)).days
        rows.append((d, v, avail(d)))
    month = [("1970-%02d-01" % m, 120.0, "1970-%02d-03T21:00:00+00:00" % (m + 1))
             for m in range(1, 12)]
    return FakeStore({("calc.baa_less_10y", None): rows,
                      ("calc.baa_less_10y_m", None): month})


def group_c(cfg: dict) -> None:
    print("C. end to end on a fixture")
    st = proxy_fixture()
    days = [d for d in bdays("2006-01-02", "2016-12-30") if d.endswith(("-02", "-15"))]
    cfg2 = {**cfg, "fpr": {**cfg["fpr"], "overlays": ["hy_accel_baa"]}}
    res = tb.run_fpr(st, cfg2, NOW, sessions=days)
    r = res["rows"][0]
    check(r["true_positive"] > 0 and r["false_positive"] > 0,
          f"the proxy fires before the 2007 top (true) and in 2015 (false) "
          f"({r['true_positive']} true, {r['false_positive']} false)")
    check(r["rate"] is not None and abs(r["rate"] - r["false_positive"] / r["n"]) < 1e-12,
          f"the rate is false over true plus false, with n ({tb.rate_text(r)})")
    ov = {o["id"]: o for o in tb.overlays_at(st, cfg, "1970-06-20", NOW)}
    b = ov["hy_accel_baa"]
    check(any(t["state"] in ("fires", "quiet") and "1970-0" in t["shown"] for t in b["triggers"]),
          f"before DBAA exists the proxy reads BAA's monthly ({tb.state_text(b)})")
    old = {o["id"]: o for o in tb.overlays_at(st, cfg, "1955-06-15", NOW)}["hy_accel_baa"]
    check(old["state"] == tb.OVERLAY_NOT_EXISTENT,
          f"before 1962 the proxy is not existent ({tb.state_text(old)})")
    check([o["id"] for o in tb.scored(list(ov.values()))] == ["concentration", "hy_accel", "liquidity"],
          "the calibration's record counts the three overlays, never the proxy")
    fires = [[{"id": "hy_accel_baa", "state": tb.FIRES, "proxy_of": "hy_accel"},
              {"id": "hy_accel", "state": tb.CLEAR}]]
    check(tb.classify("top", fires) == "missed",
          "a top only the proxy fires on is not called (A77's pass rule is unchanged)")
    # The cached reader's join is the store's own, vintages and the cutoff included.
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "t.db"
        c = sqlite3.connect(p)
        c.execute("CREATE TABLE observations (registry_key TEXT, instrument TEXT, "
                  "observed_at TEXT, value_num REAL, value_text TEXT, source TEXT, "
                  "available_at TEXT, run_id TEXT, availability_kind TEXT)")
        rows = [("calc.baa_less_10y", None, d, 200.0 + i, None, "calc", avail(d), "r", "observed")
                for i, d in enumerate(bdays("2008-01-01", "2008-03-31"))]
        rows.append(("calc.baa_less_10y", None, "2008-02-01", 999.0, None, "calc",
                     "2008-03-10T21:00:00+00:00", "r2", "observed"))
        c.executemany("INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?)", rows)
        c.commit()
        c.close()
        base = tb.Reader(str(p))
        cr = tb.CachedReader(base)
        same = True
        for cut in ("2008-02-15T21:00:00+00:00", "2008-03-15T21:00:00+00:00"):
            for frm in (None, "2008-01-20"):
                a = [(r["observed_at"], r["value_num"]) for r in base.as_of("calc.baa_less_10y", cut, None, frm)]
                b2 = [(r["observed_at"], r["value_num"]) for r in cr.as_of("calc.baa_less_10y", cut, None, frm)]
                same = same and a == b2 and bool(a)
        v_before = dict((r["observed_at"], r["value_num"])
                        for r in cr.as_of("calc.baa_less_10y", "2008-02-15T21:00:00+00:00"))
        v_after = dict((r["observed_at"], r["value_num"])
                       for r in cr.as_of("calc.baa_less_10y", "2008-03-15T21:00:00+00:00"))
        cr.close()
    check(same, "the cached reader returns the store's join row for row")
    check(v_before.get("2008-02-01") != 999.0 and v_after.get("2008-02-01") == 999.0,
          "a revision is read only once it is knowable")


def group_d(cfg: dict) -> None:
    print("D. the long proxy")
    from altdata import config as acfg
    from altdata import market_features as mf
    ids = {s.key: s for s in acfg.FRED_PULL_SERIES}
    check(ids.get("dbaa") and ids["dbaa"].fred_id == "DBAA" and ids["dbaa"].freq == "daily"
          and ids.get("baa") and ids["baa"].fred_id == "BAA" and ids["baa"].freq == "monthly",
          "DBAA (daily) and BAA (monthly) are in the FRED pull")
    for k in ("fred.dbaa", "fred.baa", "calc.baa_less_10y", "calc.baa_less_10y_m"):
        check(bool(derived.registry_entry(k)), f"{k} is registered")
    for k in ("calc.baa_less_10y", "calc.baa_less_10y_m"):
        e = derived.registry_entry(k) or {}
        check(e.get("observation_type") == "calculated" and e.get("trigger_eligible") is False
              and k in mf.MACRO_FEATURES, f"{k}: calculated, not trigger-eligible, computed")
    import yaml
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    barred = {k for b in reg.get("market_state_barred") or [] for k in b.get("keys") or []}
    check({"fred.dbaa", "fred.baa", "calc.baa_less_10y", "calc.baa_less_10y_m"} <= barred,
          "all four are barred from the market-state object")
    ms = (REPO / "config" / "market_state.yaml").read_text(encoding="utf-8")
    check("baa" not in ms.lower(), "the market-state config names none of them")
    for k, fam in (("fred.dbaa", "fred_moodys_daily"), ("fred.baa", "fred_moodys_monthly"),
                   ("calc.baa_less_10y", "fred_moodys_daily"),
                   ("calc.baa_less_10y_m", "fred_moodys_monthly")):
        _, why = derived.staleness_allowance(k)
        check(fam in str(why), f"{k} takes its lag family {fam} ({why})")

    class DB:
        def __init__(self, data):
            self.data = data

        def as_of(self, key, as_of=None):
            return [{"observed_at": d, "value_num": v, "available_at": a,
                     "availability_kind": "observed"} for d, v, a in self.data.get(key, [])]

    y10 = [(d, 4.0, avail(d)) for d in bdays("2008-01-01", "2008-02-29")]
    y10[5] = (y10[5][0], 4.0, "2008-01-25T21:00:00+00:00")
    db = DB({"fred.yield_10y": y10,
             "fred.dbaa": [(d, 6.5, avail(d)) for d in bdays("2008-01-01", "2008-01-31")],
             "fred.baa": [("2008-01-01", 6.6, "2008-02-01T21:00:00+00:00"),
                          ("2008-02-01", 6.7, "2008-03-03T21:00:00+00:00")]})
    rows = [r for r in mf.macro_rows(db) if r["registry_key"].startswith("calc.baa")]
    d = [r for r in rows if r["registry_key"] == "calc.baa_less_10y"]
    m = {r["observed_at"]: r for r in rows if r["registry_key"] == "calc.baa_less_10y_m"}
    check(len(d) == len(bdays("2008-01-01", "2008-01-31")) and all(abs(r["value"] - 250.0) < 1e-9 for r in d),
          f"the daily is DBAA less DGS10 the same session, in bp ({len(d)} rows, 250bp)")
    check(set(m) == {"2008-01-01", "2008-02-01"} and abs(m["2008-01-01"]["value"] - 260.0) < 1e-9,
          f"the monthly is BAA less the month's mean DGS10, in bp ({sorted(m)})")
    check(m and m["2008-01-01"]["available_at"] >= "2008-02-01T21:00:00+00:00",
          "the monthly is knowable no earlier than BAA's print and the month's last 10-year")
    late = next((r for r in d if r["observed_at"] == y10[5][0]), None)
    check(late is not None and late["available_at"] == "2008-01-25T21:00:00+00:00",
          "a daily row takes its later leg's availability")


def group_e(cfg: dict) -> None:
    print("E. the reports (6i-4)")
    try:
        from daily_cascade import tb_harness_block as blk
    except ImportError as exc:
        check(False, f"daily_cascade.tb_harness_block imports ({exc})")
        return
    with tempfile.TemporaryDirectory() as tmp:
        ld = Path(tmp)
        (ld / "tb-harness-2026-10-26-episodes.csv").write_text(
            "set,episode,class,date,spx_check,concentration,hy_accel,liquidity,classification\n"
            "calibration,top_2000,top,2000-03-24,x,a,b,c,called\n"
            "calibration,top_2007,top,2007-10-09,x,a,b,c,missed\n"
            "calibration,top_2022,top,2022-01-03,x,a,b,c,unread\n"
            "calibration,bottom_2009,bottom,2009-03-09,x,a,b,c,not scored\n"
            "calibration,control_2018,control,2018-09-20,x,a,b,c,refused\n"
            "calibration,control_2018,control,2018-12-24,x,a,b,c,\n"
            "calibration,control_2024,control,2024-07-16,x,a,b,c,false call\n"
            "extended:bears,bear_1973,top,1973-01-11,x,a,b,c,\n", encoding="utf-8")
        (ld / "tb-harness-fpr-2026-10-26.csv").write_text(
            ",".join(tb.FPR_COLUMNS) + "\n"
            "concentration,100,80,10,6,4,0,2,0.400000\n"
            "hy_accel,100,5,0,0,0,0,0,\n"
            "hy_accel_baa,100,90,20,5,15,0,3,0.750000\n"
            "liquidity,100,0,0,0,0,0,0,\n", encoding="utf-8")
        sub = blk.slow_subsection(FakeStore({}), NOW, ledger_dir=ld)
    lines = (sub or {}).get("lines") or []
    text = " ".join(lines)
    check(len(lines) == 3, f"the Monthly's hook prints three lines ({len(lines)})")
    check(all(o["title"] in lines[0] for o in cfg["overlays"]) and "/" in lines[0],
          "line one: each overlay's state with its trigger counts, the Baa proxy beside")
    check("tops 1 of 3 called" in lines[1] and "controls 1 of 2 refused" in lines[1]
          and "bottoms not scored" in lines[1],
          f"line two: the episode record, k of n per class ({lines[1] if len(lines) > 1 else ''})")
    check("40.0% (n=10" in lines[2] and "75.0% (n=20" in lines[2] and "n=0" in lines[2],
          f"line three: the false-positive rate per overlay with n")
    check("composite" not in text.lower().replace("no composite", ""),
          "no composite is printed")
    check("top_bottom.composite" not in str((sub or {}).get("data")),
          "and none is carried in its data")
    import yaml
    hook = yaml.safe_load((REPO / "config" / "stack_hooks" / "monthly-slow-tb-harness.yaml")
                          .read_text(encoding="utf-8"))
    check(hook["cadence"] == "monthly" and hook["module"] == "daily_cascade.tb_harness_block",
          "the section joins the Monthly through its hook file")
    qc = yaml.safe_load((REPO / "config" / "quarterly_chapters.yaml").read_text(encoding="utf-8"))
    rows = [r for ch in (qc.get("chapters") or {}).values() if isinstance(ch, dict)
            for r in ch.get("structure") or [] if r.get("label") == "HY spread acceleration"]
    if not rows:
        rows = [r for r in _walk(qc) if r.get("label") == "HY spread acceleration"]
    check(len(rows) == 1 and rows[0].get("harness_overlay") == "hy_accel" and not rows[0].get("absent"),
          "the Quarterly's credit row names the harness's overlay, not its old reason")
    from monthly_macro import quarterly_items as qi
    rws, nt, _ = qi.structure_rows(FakeStore({}), rows[:1], {"now": NOW, "end": "2026-09-30",
                                                             "start": "2026-07-01", "common": {}})
    shown = " ".join(" ".join(map(str, r)) for r in rws) + " ".join(nt)
    check("not on this build" not in shown and "HY Spread Acceleration" in shown
          and "Baa proxy" in shown,
          f"and prints its state at the quarter's end, the Baa proxy beside ({shown[:120]})")


def _walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from _walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from _walk(v)


def main() -> int:
    line = "=" * 72
    print(f"{line}\n6i-3 and 6i-4 -- the T&B harness's FPR, the Baa proxy, the reports\n{line}")
    cfg = tb.config()
    group_a(cfg)
    group_b(cfg)
    group_c(cfg)
    group_d(cfg)
    group_e(cfg)
    print(f"\n{line}\n{PASS} passed, {FAIL} failed\n{line}")
    print("VALIDATION FAILED" if FAIL else "VALIDATION PASSED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
