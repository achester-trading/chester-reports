"""
Validation gate for the data-quality check (AUD-3c, 15 Oct 2026;
altdata/quality.py, config/data_quality.yaml).

A SYNTHETIC STORE of its own -- about a year of business days, seeded here, no
network, no box, no model:

  A  THE CONFIG. The session-set numbers (6 sigma, 60 changes, the 99th
     percentile, five lines) each carry a reason; each pair is measured with its
     date and window, or says why it is not.
  B  OUTLIERS. A 10-sigma jump is flagged and a 3-sigma move is not -- on a price
     (log changes), on a yield (differences) and on the VIX (the move screen's
     pinned log basis). A key with fewer than 60 changes is skipped and named.
  C  REVISIONS. A FRED value that differs from the value stored earlier for the
     same observation date is listed as a revision with its old and new values,
     never flagged as an outlier, and sets no exit code.
  D  CROSS-SOURCE PAIRS. Each of the three pairs, inside and outside its
     tolerance; a pair with no measured tolerance prints "not measured" and never
     flags; the tolerance measure is the 99th percentile, floored.
  E  READ-ONLY. The store's bytes and its directory are unchanged; a store that
     cannot be opened exits 2; clean exits 0 and flags exit 1.
  F  THE CLOSE. On a flagged day the Warnings lines read "Data check: ..." -- at
     most five and a count; on a clean day nothing; produce() adds them read-only
     before it renders, and the Warnings table prints them.
  G  THE 15 OCT RULINGS. The VIX floor is a ruling; ^TNX and ^TYX wait for the
     box; a fred:backfill row is labelled backfill, never a revision, and never
     a new print; a policy rate's 25 bp step after sixty flat prints is an
     informational step line, never a flag, and never reaches the close.

    python tools/validate_quality.py
"""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import io
import math
import os
import random
import sys
from contextlib import redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from gate_tmp import mkdtemp as gate_mkdtemp                    # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78
DAY = "2026-10-14"


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


def bdays(end: str, n: int) -> list[str]:
    d, out = dt.date.fromisoformat(end), []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= dt.timedelta(days=1)
    return out[::-1]


def rows(key, days, vals, avail=None):
    return [{"registry_key": key, "instrument": None, "observed_at": d,
             "available_at": avail or f"{d}T21:00:00+00:00", "value": v,
             "source": "fixture"} for d, v in zip(days, vals)]


def walk(seed, n, sd, start, log=True):
    rnd = random.Random(seed)
    v, out = start, []
    for _ in range(n):
        v = v * math.exp(rnd.gauss(0, sd)) if log else v + rnd.gauss(0, sd)
        out.append(round(v, 6))
    return out


def with_last(vals, sds, sd, log=True):
    """vals with its last point replaced by the prior one moved `sds` standard
    deviations of the series' own recent changes."""
    q = __import__("altdata.quality", fromlist=["x"])
    hist = [q.change(a, b, "log" if log else "diff") for a, b in zip(vals[-62:-2],
                                                                     vals[-61:-1])]
    import statistics
    s = statistics.stdev(hist)
    out = list(vals)
    out[-1] = round(out[-2] * math.exp(sds * s) if log else out[-2] + sds * s, 6)
    return out


def seed(path: str, *, flagged: bool = True) -> dict:
    """The fixture store. With `flagged`, three 10-sigma jumps on DAY, a revision,
    and a VIX gap past its tolerance; without, the same keys all clean."""
    from altdata import observations
    days = bdays(DAY, 260)
    spy = walk(1, 260, 0.01, 500.0)
    qqq = walk(2, 260, 0.012, 400.0)
    y10 = walk(3, 260, 0.04, 4.2, log=False)
    vix = walk(4, 260, 0.05, 18.0)
    tnx = list(y10)
    if flagged:
        spy = with_last(spy, 10.0, 0.01)
        y10 = with_last(y10, 10.0, 0.04, log=False)
        vix = with_last(vix, 10.0, 0.05)
    qqq = with_last(qqq, 3.0, 0.012)
    vixcls = list(vix)
    if flagged:
        vixcls[-1] = round(vix[-1] + 0.80, 6)            # the pair's gap: 0.8 points
    st = observations.ObservationStore(path)
    try:
        st.write_many(rows("yfinance.mkt_spy", days, spy))
        st.write_many(rows("yfinance.mkt_qqq", days, qqq))
        st.write_many(rows("fred.yield_10y", days, y10))
        st.write_many(rows("yfinance.mkt_tnx", days, tnx))
        st.write_many(rows("yfinance.mkt_vix", days, vix))
        st.write_many(rows("fred.vix", days, vixcls))
        # A short series: 30 observations, not judged.
        st.write_many(rows("yfinance.mkt_iwm", days[-30:], walk(5, 30, 0.01, 200.0)))
        # U-3, monthly: 70 months, then a revision written on DAY.
        months = []
        d = dt.date(2020, 8, 1)
        while len(months) < 70:
            months.append(d.isoformat())
            d = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
        u3 = walk(6, 70, 0.1, 4.0, log=False)
        st.write_many(rows("fred.u3_rate", months, u3,
                           avail="2026-10-03T13:00:00+00:00"))
        if flagged:
            st.write_many([{"registry_key": "fred.u3_rate", "instrument": None,
                            "observed_at": months[-1],
                            "available_at": f"{DAY}T14:00:00+00:00",
                            "value": round(u3[-1] + 0.3, 6), "source": "fixture"}])
    finally:
        st.close()
    return {"spy": spy, "y10": y10, "vix": vix, "vixcls": vixcls, "u3": u3,
            "u3_month": months[-1]}


def group_a() -> None:
    head("A. THE CONFIG")
    from altdata import quality
    cfg = quality.load_config()
    o, p = cfg["outliers"], cfg["pairs"]
    check(o["sigma"] == 6 and o["window"] == 60 and p["percentile"] == 99
          and cfg["close_lines"] == 5,
          "the session-set numbers: 6 sigma, 60 changes, the 99th percentile, five "
          "lines")
    check(all(len(str(x or "")) > 40 for x in (o.get("sigma_reason"),
                                              o.get("window_reason"),
                                              p.get("percentile_reason"),
                                              p.get("floor_reason"),
                                              cfg.get("close_lines_reason"))),
          "each with its reason, in the one config file")
    ids = [x["id"] for x in p["list"]]
    check(ids == ["tnx_dgs10", "tyx_dgs30", "vix_vixcls"],
          f"the three pairs the brief names ({ids})")
    ok = all((x.get("tolerance") is not None and x.get("measured_on")
              and x.get("measured_window"))
             or (x.get("tolerance") is None and len(str(x.get("unmeasured_reason")
                                                       or "")) > 40)
             for x in p["list"])
    check(ok, "each pair carries its tolerance with the date and window it was "
          "measured, or the reason it is not yet measured")


def group_b(db: str, s: dict) -> dict:
    head("B. OUTLIERS")
    from altdata import quality
    r = quality.check(db, DAY)
    fl = {f["key"]: f for f in r["outliers"]}
    check("yfinance.mkt_spy" in fl and fl["yfinance.mkt_spy"]["basis"] == "log"
          and fl["yfinance.mkt_spy"]["sigmas"] > 9.5,
          f"SPY's 10-sigma jump, measured in log changes: flagged "
          f"({fl.get('yfinance.mkt_spy', {}).get('sigmas')})")
    check("fred.yield_10y" in fl and fl["fred.yield_10y"]["basis"] == "diff",
          "the 10-year's 10-sigma jump, measured in differences: flagged")
    check("yfinance.mkt_vix" in fl and fl["yfinance.mkt_vix"]["basis"] == "log",
          "the VIX's, on the move screen's pinned log basis: flagged")
    check("yfinance.mkt_qqq" not in fl,
          "QQQ's 3-sigma move is not flagged")
    check(any(k["key"] == "yfinance.mkt_iwm" and "30" in k["why"] for k in r["skipped"]),
          "a key with 30 observations is skipped and named, not judged")
    check("fred.u3_rate" not in fl,
          "U-3's revised value is not an outlier")
    return r


def group_c(r: dict, s: dict) -> None:
    head("C. REVISIONS")
    rv = [x for x in r["revisions"] if x["key"] == "fred.u3_rate"]
    check(len(rv) == 1 and rv[0]["observed_at"] == s["u3_month"]
          and abs(rv[0]["old"] - s["u3"][-1]) < 1e-9
          and abs(rv[0]["new"] - (s["u3"][-1] + 0.3)) < 1e-6,
          f"U-3's restated month is listed as a revision, old and new ({rv})")
    from altdata import quality
    rep = quality.report(r)
    check("revision" in rep.lower() and "fred.u3_rate" in rep,
          "and the table prints it under revisions")
    check(all(f.get("key") != "fred.u3_rate" for f in r["flags"]),
          "a revision is never a flag")


def group_d(db: str) -> None:
    head("D. CROSS-SOURCE PAIRS")
    from altdata import quality
    cfg = quality.load_config()
    r = quality.check(db, DAY, cfg=cfg)
    pr = {p["id"]: p for p in r["pairs"]}
    v = pr.get("vix_vixcls") or {}
    check(v.get("flagged") and abs(v.get("gap") - 0.8) < 1e-6,
          f"^VIX against VIXCLS 0.8 points apart, past its 0.01-point tolerance: "
          f"flagged ({v.get('gap')})")
    t = pr.get("tnx_dgs10") or {}
    check(t.get("state") == "not measured" and not t.get("flagged"),
          f"^TNX against DGS10 with no measured tolerance: 'not measured', never "
          f"flagged ({t.get('state')})")
    check((pr.get("tyx_dgs30") or {}).get("state") in ("not measured", "absent"),
          "^TYX against DGS30 likewise (and absent where a leg is not stored)")
    # Each pair inside and outside a tolerance, by the same rule.
    for pid, a, b, inside, outside in (("tnx_dgs10", 4.25, 4.27, 0.03, 0.01),
                                       ("tyx_dgs30", 4.80, 4.75, 0.06, 0.04),
                                       ("vix_vixcls", 21.3, 22.1, 1.0, 0.4)):
        pc = next(x for x in cfg["pairs"]["list"] if x["id"] == pid)
        hi = quality.pair_verdict(dict(pc, tolerance=inside), a, b, DAY)
        lo = quality.pair_verdict(dict(pc, tolerance=outside), a, b, DAY)
        check(not hi["flagged"] and lo["flagged"],
              f"{pid}: a {abs(a - b):.2f} gap is inside a {inside} tolerance and "
              f"outside {outside}")
    line = quality.pair_line(quality.pair_verdict(
        dict(next(x for x in cfg["pairs"]["list"] if x["id"] == "vix_vixcls"),
             tolerance=0.4), 21.3, 22.1, DAY))
    check(line == "Data check: ^VIX 21.3 vs VIXCLS 22.1 on 14 Oct, beyond its "
                  "0.4-point tolerance",
          f"the brief's line, word for word: '{line}'")
    yl = quality.pair_line(quality.pair_verdict(
        dict(next(x for x in cfg["pairs"]["list"] if x["id"] == "tnx_dgs10"),
             tolerance=0.03), 4.25, 4.31, DAY))
    check(yl == "Data check: ^TNX 4.25 vs DGS10 4.31 on 14 Oct, beyond its "
                "3 bp tolerance", f"a yield pair's line prints in bp: '{yl}'")
    # The measure: the 99th percentile of the absolute gaps, floored.
    gaps = [0.0] * 98 + [0.5, 2.0]
    m = quality.measure_gaps(gaps, 99, 0.01)
    check(abs(m["p99"] - 0.515) < 1e-9 and abs(m["tolerance"] - 0.515) < 1e-9,
          f"the tolerance is the 99th percentile of the gaps ({m})")
    m0 = quality.measure_gaps([0.0] * 100, 99, 0.01)
    check(m0["tolerance"] == 0.01 and m0["floored"],
          "and a percentile below the quote's precision is floored at it")


def group_e(td: str, db: str) -> None:
    head("E. READ-ONLY, AND THE EXIT CODES")
    from altdata import quality
    before = (hashlib.sha256(Path(db).read_bytes()).hexdigest(), Path(db).stat().st_size)
    files = sorted(os.listdir(td))
    for _ in range(2):
        quality.check(db, DAY)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = quality.main(["check", "--date", DAY, "--db", db])
    after = (hashlib.sha256(Path(db).read_bytes()).hexdigest(), Path(db).stat().st_size)
    check(before == after, "the store's bytes are unchanged after three checks")
    new = [f for f in sorted(os.listdir(td)) if f not in files]
    check(all(f.endswith(("-shm", "-wal")) for f in new),
          f"and nothing new beside it but SQLite's own side files on a read-only "
          f"open ({new or 'none'})")
    check(rc == 1 and "FLAGS" in buf.getvalue(), f"flags exit 1 (exit {rc})")
    with redirect_stdout(io.StringIO()):
        rc2 = quality.main(["check", "--date", DAY, "--db",
                            str(Path(td) / "no_such.db")])
    check(rc2 == 2 and not (Path(td) / "no_such.db").exists(),
          f"a store that cannot be opened exits 2 and is not created (exit {rc2})")
    clean = str(Path(td) / "clean.db")
    seed(clean, flagged=False)
    with redirect_stdout(io.StringIO()):
        rc0 = quality.main(["check", "--date", DAY, "--db", clean])
    check(rc0 == 0, f"a clean store exits 0 (exit {rc0})")
    src = (REPO / "altdata" / "quality.py").read_text(encoding="utf-8")
    check("mode=ro" in src and not any(w in src for w in (
        "INSERT ", "UPDATE ", "DELETE ", "write_many", ".write(")),
          "the module opens the store mode=ro and holds no write statement")


def group_f(td: str, db: str) -> None:
    head("F. THE CLOSE'S WARNINGS")
    from altdata import quality
    lines = quality.close_warnings(DAY, db)
    check(lines and all(x.startswith("Data check: ") for x in lines)
          and any("^VIX" in x and "VIXCLS" in x for x in lines),
          f"a flagged day: one 'Data check:' line per flag ({len(lines)})")
    check(len(lines) <= 5, "at most five")
    r = quality.check(db, DAY)
    many = copy.deepcopy(r)
    many["flags"] = r["flags"] * 3
    cl = quality.close_lines(many, 5)
    check(len(cl) == 6 and cl[:5] == [quality.flag_line(f) for f in many["flags"][:5]]
          and cl[5].startswith(f"and {len(many['flags']) - 5} more data-check flag"),
          f"past five: five lines and a count ('{cl[-1]}')")
    clean = str(Path(td) / "clean.db")
    check(quality.close_warnings(DAY, clean) == [], "a clean day prints nothing")
    check(quality.close_warnings(DAY, str(Path(td) / "absent.db")) == [],
          "a store the close cannot open prints nothing and raises nothing")
    from daily_cascade import stack_render
    html = stack_render.lines_table(lines, "Warnings")
    check("Warnings" in html and stack_render.esc(lines[0]) in html,
          "the Warnings table prints the line")
    sc = (REPO / "daily_cascade" / "stack_close.py").read_text(encoding="utf-8")
    i_q = sc.find("quality.close_warnings(")
    i_r = sc.find("stack_render.render(p, ed, charts")
    check(0 < i_q < i_r, "produce() adds the lines before it renders the close")


def group_g(td: str) -> None:
    head("G. THE 15 OCT RULINGS")
    from altdata import observations, quality
    cfg = quality.load_config()
    p = cfg["pairs"]
    check("RULED 15 Oct 2026" in p["floor_reason"]
          and next(x for x in p["list"] if x["id"] == "vix_vixcls")["tolerance"] == 0.01,
          "the VIX pair keeps its 0.01 floor, and the config says it is a ruling")
    check(all("week of 19 Oct" in x["unmeasured_reason"] or "As ^TNX" in
              x["unmeasured_reason"] for x in p["list"] if x["tolerance"] is None)
          and [x["id"] for x in p["list"] if x["tolerance"] is None]
          == ["tnx_dgs10", "tyx_dgs30"],
          "^TNX and ^TYX wait for the box, after the backfills (not measured)")
    sk = quality.step_keys(cfg)
    check({"fred.iorb", "fred.ecb_dfr", "fred.jp_call_rate"} <= sk
          and all(len(str(s.get("why") or "")) > 10 for s in cfg["steps"]["series"]),
          f"the ruled policy rates are declared step series, each with why ({sorted(sk)})")
    check(cfg.get("backfill_sources") == ["fred:backfill"],
          "fred:backfill is the declared backfill string")
    db = str(Path(td) / "rulings.db")
    days = bdays(DAY, 80)
    iorb = [4.65] * 79 + [4.40]                         # sixty-plus flat, then -25 bp
    ff = [4.33] * 40 + [4.58] * 39 + [4.33]             # one earlier step in the window
    y30 = walk(7, 80, 0.04, 4.8, log=False)
    st = observations.ObservationStore(db)
    try:
        st.write_many(rows("fred.iorb", days, iorb))
        st.write_many(rows("fred.effr_daily", days, ff))
        # The 30-year: its history, then on DAY the backfill restates one day and
        # writes an older day for the first time; no revision, no new print.
        st.write_many(rows("fred.yield_30y", days[:-1], y30[:-1]))
        st.write_many([{"registry_key": "fred.yield_30y", "instrument": None,
                        "observed_at": days[-10], "available_at": f"{DAY}T14:00:00+00:00",
                        "value": round(y30[-10] + 0.5, 6), "source": "fred:backfill"},
                       {"registry_key": "fred.yield_30y", "instrument": None,
                        "observed_at": days[-1], "available_at": f"{DAY}T14:00:00+00:00",
                        "value": round(y30[-2] + 3.0, 6), "source": "fred:backfill"},
                       # U-3: one ordinary revision on the same day, for contrast.
                       {"registry_key": "fred.u3_rate", "instrument": None,
                        "observed_at": "2026-08-01", "available_at": "2026-09-05T13:00:00+00:00",
                        "value": 4.2, "source": "fred"},
                       {"registry_key": "fred.u3_rate", "instrument": None,
                        "observed_at": "2026-08-01", "available_at": f"{DAY}T13:00:00+00:00",
                        "value": 4.3, "source": "fred"}])
    finally:
        st.close()
    r = quality.check(db, DAY)
    bf = [x for x in r["backfill"] if x.get("key") == "fred.yield_30y"]
    check(any(x.get("old") is not None and abs(x["new"] - x["old"] - 0.5) < 1e-6
              for x in bf)
          and not any(x["key"] == "fred.yield_30y" for x in r["revisions"]),
          "a fred:backfill restatement is labelled backfill, never a revision")
    check(any(x.get("first_written") == 1 for x in bf)
          and not any(f.get("key") == "fred.yield_30y" for f in r["flags"]),
          "and the backfill's first-written day, 3 points off, is not judged as a "
          "new print")
    check([x["key"] for x in r["revisions"]] == ["fred.u3_rate"],
          "while the pull's own restatement of U-3 is still a revision")
    steps = {s["key"]: s for s in r["steps"]}
    s = steps.get("fred.iorb") or {}
    check(s.get("change") == -25.0 and s.get("unit") == "bp"
          and not any(f.get("key") == "fred.iorb" for f in r["flags"]),
          f"IORB's -25 bp after sixty flat prints is a step, not a flag ({s})")
    check("fred.effr_daily" in steps
          and not any(f.get("key") == "fred.effr_daily" for f in r["flags"]),
          "the daily effective rate's step back down likewise")
    line = quality.step_line(s) if s else ""
    check(line.startswith("Data check (step): ") and "a step of −25 bp" in line
          and line.endswith("informational, never a flag"),
          f"the step line: '{line}'")
    check("steps (policy rates; informational, never flags): 2" in quality.report(r)
          and "backfill (the history writer's rows; never revisions)" in quality.report(r),
          "the table prints both sections")
    check(not any("(step)" in x for x in quality.close_warnings(DAY, db)),
          "a step never reaches the close's Warnings table")


def main() -> int:
    print(f"{LINE}\nAUD-3c: the data-quality check, on a synthetic store\n{LINE}")
    td = gate_mkdtemp("validate_quality_")
    db = str(Path(td) / "store.db")
    s = seed(db)
    group_a()
    r = group_b(db, s)
    group_c(r, s)
    group_d(db)
    group_e(td, db)
    group_f(td, db)
    group_g(td)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
