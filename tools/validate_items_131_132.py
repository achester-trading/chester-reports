"""
B139 (session B, 7 Nov 2026): signal-triage Batch 25 items 131 and 132's code
half (the order's 110 and 111), section 0's S3, S4 (O-111a) and S6.

  A  THE RATIO AND ITS LABEL. On a fixture store: the CCC/HY OAS ratio on the
     two series' common days, its percentile over its own history inside the
     asked five years, the window through derived.window_label ("5y asked, 3.4y
     stored"), the cycle series beside it (HY OAS and Baa less the 10-year in
     bp with their 20-observation changes) and CCC less BB's change, on one line.
  B  THE OMITTED CLAUSE. With no stored composition figure the clause is absent
     (no "n/a", no placeholder); a scan row of the declared family and metric
     prints with its as-of and URL; another family's row does not. A store with
     no credit series prints nothing.
  C  PLACEMENT AND RIGHTS. The line in the close's Plumbing & rates and in the
     Weekly's and the Monthly's (plumbing_week at both cadences, on the fixture
     store); a fault costs the line only; nothing in regime.py or
     config/market_state.yaml reads it; no flag word.
  D  THE ENTRY TYPE'S SCHEMA. Row one validates; a missing incentive tag, an
     engagement under O-111a without a ruling, a claim dated past 30 days and a
     malformed rule are refused; engagement over the threshold admits a row; no
     handle in any row; seeded PROPOSED with its 17 claims, a re-seed syncs and
     never duplicates, a call cannot be deleted.
  E  THE SCORING RULE. Before a claim's date nothing is written; after it: a
     one-day move, a move by a date, a level by a date and a move from the high
     scored hit or miss from the store as known at the cutoff; a claim without a
     rule is unresolved, the operator's ruled score in its place; a score is
     written once and never edited; the register's resolve_due runs the pass.
  F  THE TWO COUNTS. No rows: nothing stored and "no rows yet"; rows captured per
     ET day by direction, zeros from the first row; knowable at the day's end;
     a rejected row not counted; item 97's two inputs declared with no
     direction; the keys registered, barred and trigger-ineligible; O-111a's
     thresholds and review date; the gate in the list.

The clock is pinned to GATE_NOW. Synthetic fixtures only (invented figures): no
live store, no network, no model.

    python tools/validate_items_131_132.py
"""

from __future__ import annotations

import copy
import datetime as dt
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gate_tmp  # noqa: E402
import yaml  # noqa: E402

from altdata import credit_bifurcation as cb  # noqa: E402
from altdata import dated_calls as dc  # noqa: E402
from altdata import derived, observations  # noqa: E402

GATE_KIND = "code"
GATE_NOW = "2026-11-07T15:00:00+00:00"
AS_OF = "2026-11-05T22:00:00+00:00"
CALL = "x_funnel_15day_2026_11_05"

PASS = FAIL = 0
LINE = "=" * 78


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


def bdays(start: str, end: str) -> list[str]:
    d, e, out = dt.date.fromisoformat(start), dt.date.fromisoformat(end), []
    while d <= e:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def row(key, day, v, src="fred", avail=None):
    return {"registry_key": key, "instrument": None, "observed_at": day,
            "available_at": avail or f"{day}T21:00:00+00:00", "value": float(v),
            "source": src, "availability_kind": "observed"}


# Invented figures: HY OAS drifts 3.00-3.60%, CCC 9.0-13.5%, so the ratio rises
# to its highest on the last day; Baa-10y 140-152 bp; CCC-BB rises 40 bp in the
# last 20 observations.
DAYS = bdays("2023-06-01", "2026-11-04")


def credit_rows() -> list[dict]:
    rows, n = [], len(DAYS)
    for i, d in enumerate(DAYS):
        hy = 3.0 + 0.6 * i / (n - 1)
        ccc = 9.0 + 4.5 * (i / (n - 1)) ** 2
        rows += [row("fred.hy_oas", d, round(hy, 4)), row("fred.ccc_oas", d, round(ccc, 4)),
                 row("calc.baa_less_10y", d, 140 + 12 * i / (n - 1), "calc"),
                 row("calc.ccc_bb_oas_bp", d, 600 + (2.0 * (i - (n - 21)) if i > n - 21 else 0), "calc")]
    return rows


def store_with(rows: list[dict], tag: str) -> str:
    db = str(Path(gate_tmp.mkdtemp(f"b139_{tag}_")) / "chester.db")
    with observations.ObservationStore(db) as st:
        if rows:
            st.write_many(rows)
    return db


def group_a() -> None:
    head("A. THE RATIO AND ITS LABEL")
    db = store_with(credit_rows(), "ratio")
    with observations.ObservationStore(db) as st:
        r = cb.read(st, AS_OF, scan_rows=[])
        ln = cb.line(r)
    q = r["ratio"]
    n = len(DAYS)
    want = (9.0 + 4.5) / 3.6
    check(q is not None and abs(q["level"] - want) < 1e-3 and q["observed_at"] == "2026-11-04",
          f"the ratio: CCC OAS over HY OAS on their common day, {q and q['level']:.3f}x on 2026-11-04")
    check(q["percentile"] == 100.0 and q["n"] == n,
          f"its percentile over its own history in the window: 100th of n={n} (at its high)")
    held = (dt.date(2026, 11, 4) - dt.date(2023, 6, 1)).days
    check(q["window"] == derived.window_label(1826, held, start="2023-06-01")
          and q["window"] == "5y asked, 3.4y stored",
          f"the window through A126's window_label: {q['window']!r}")
    check(q["window_compact"] == "3.4y/5y", "and its compact form, 3.4y/5y")
    hy, baa = r["cycle"]
    check(round(hy["level_bp"]) == 360 and round(hy["change_bp"]) == round(0.6 * 20 / (n - 1) * 100),
          f"HY OAS in bp ({hy['level_bp']:.0f}) with its 20-observation change "
          f"({hy['change_bp']:+.1f} bp)")
    check(round(baa["level_bp"]) == 152 and baa["change_bp"] is not None,
          "Baa less the 10-year in bp (stored in bp, not rescaled)")
    check(r["tail"]["change_bp"] == 40.0, "CCC less BB +40 bp over 20 observations")
    print(f"        the line: {ln}")
    check(ln.startswith("Credit bifurcation (as of 2026-11-04): cycle -- HY OAS 360 bp")
          and "Baa less the 10-year 152 bp" in ln
          and "; idiosyncratic -- CCC/HY OAS 3.75x, 100th percentile of 5y asked, 3.4y stored "
              f"(n={n:,}), CCC less BB +40 bp" in ln
          and ln.endswith("Changes over 20 observations. Report only."),
          "one line: the cycle series beside the idiosyncratic ones, in that order")
    db2 = store_with([x for x in credit_rows() if x["observed_at"] >= "2021-01-01"
                      and x["registry_key"] != "fred.ccc_oas"]
                     + [row("fred.ccc_oas", "2026-11-04", 13.5)], "short")
    with observations.ObservationStore(db2) as st:
        r2 = cb.read(st, AS_OF, scan_rows=[])
    check(r2["ratio"]["percentile"] is None and "percentile withheld (1 observation(s)" in cb.line(r2),
          "one common day: the percentile is withheld and says why")


def group_b() -> None:
    head("B. THE OMITTED CLAUSE")
    db = store_with(credit_rows(), "comp")
    with observations.ObservationStore(db) as st:
        none = cb.line(cb.read(st, AS_OF, scan_rows=[]))
        other = cb.line(cb.read(st, AS_OF, scan_rows=[{
            "family": "jpm-gtm", "metric": "Share of the CCC index below $60", "value": "20%",
            "as_of": "2026-10-03", "source_url": "https://example.org/x"}]))
        got = cb.read(st, AS_OF, scan_rows=[{
            "family": "credit-ccc", "metric": "Share of the CCC index below $60",
            "value": "about 20%", "as_of": "2026-10-03",
            "source_url": "https://example.org/fixture-scan"}])
        some = cb.line(got)
        db_none = cb.read(st, AS_OF, db_path=None)["composition"]
    check("composition" not in none and "n/a" not in none and "below $60" not in none,
          "no stored composition figure: the clause is absent, no n/a, no placeholder")
    check("composition" not in other, "a row of another scan family is not read")
    check("; composition: share of the CCC index below $60 about 20% (as of 2026-10-03, "
          "https://example.org/fixture-scan)." in some,
          "a stored scan row prints with its as-of and its URL")
    check(db_none == [], "no store path named: the scans store is not read (never the live default)")
    empty = store_with([], "empty")
    with observations.ObservationStore(empty) as st:
        check(cb.line(cb.read(st, AS_OF, scan_rows=[])) is None
              and cb.subsection(st, AS_OF) is None,
              "no credit series stored: no line, no sub-section")
    cfg = cb.config()
    check(cfg["composition"]["family"] == "credit-ccc" and cfg["change_observations"] == 20
          and cfg["ratio"]["window_days"] == 1826,
          "config: the composition's scan family, 20 observations, five years asked")


def group_c() -> None:
    head("C. PLACEMENT AND RIGHTS")
    src_close = (REPO / "daily_cascade" / "stack.py").read_text(encoding="utf-8")
    m = re.search(r"def plumbing_section\(.*?\n(?=def )", src_close, re.S)
    check(m and "credit_bifurcation.subsection(st, cutoff)" in m.group(0),
          "the close: plumbing_section carries the line as a sub-section")
    from daily_cascade import weekly_stack as ws                 # noqa: PLC0415
    db = store_with(credit_rows(), "place")
    then = "2026-10-30T21:00:00+00:00"
    with observations.ObservationStore(db) as st:
        for cad in ("weekly", "monthly"):
            try:
                pw = ws.plumbing_week(st, AS_OF, then, None, cadence=cad)
                titles = [s.get("title") for s in pw.get("subsections") or []]
                check(cb.TITLE in titles, f"the {cad} plumbing carries '{cb.TITLE}'")
            except Exception as exc:                            # noqa: BLE001
                check(False, f"the {cad} plumbing built: {type(exc).__name__}: {exc}")
        real = cb.read
        cb.read = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("fixture fault"))
        try:
            check(cb.subsection(st, AS_OF) is None, "a fault costs the line only (None, logged)")
        finally:
            cb.read = real
    reg = (REPO / "regime.py").read_text(encoding="utf-8")
    ms = (REPO / "config" / "market_state.yaml").read_text(encoding="utf-8")
    msy = yaml.safe_load(ms)
    cred = [m["metric"] for m in
            (msy.get("dimensions") or {}).get("credit", {}).get("members") or []]
    check("credit_bifurcation" not in reg and "credit_bifurcation" not in ms
          and "ccc_hy" not in ms and "ccc_bb" not in ms
          and cred == ["fred.hy_oas", "fred.bb_oas", "fred.ccc_oas", "fred.ig_oas"],
          "nothing enters the credit dimension: its members unchanged (HY, BB, CCC, IG), "
          "and neither regime.py nor config/market_state.yaml reads the line, the ratio or CCC-BB")
    src = (REPO / "altdata" / "credit_bifurcation.py").read_text(encoding="utf-8")
    code = "\n".join(x for x in src.splitlines() if not x.lstrip().startswith("#"))
    check(not re.search(r"\b(flag|fires|alert)\s*=", code) and "requests" not in code
          and "urlopen" not in code,
          "report line: no flag is set and nothing is fetched")


def group_d() -> None:
    head("D. THE ENTRY TYPE'S SCHEMA")
    cfg = dc.config()
    one = cfg["calls"][CALL]
    check(dc.validate_call(CALL, one, cfg) == [], "row one validates")
    check(set(cfg["entry_type"]["fields"]) >= {"claims", "incentive_tags",
                                               "engagement_at_capture", "score", "expiry"}
          and cfg["entry_type"]["scores"] == ["hit", "miss", "unresolved"],
          "the type's fields: claims with dates, incentive tags, engagement at capture, a score")
    bad = copy.deepcopy(one)
    del bad["incentive_tags"]["position_disclosed"]
    check(any("position_disclosed" in e for e in dc.validate_call("b", bad, cfg)),
          "a missing incentive tag is refused")
    low = copy.deepcopy(one)
    low.pop("admitted_by")
    low["engagement_at_capture"] = {"views": 9000, "reposts": 40}
    check(any("O-111a" in e for e in dc.validate_call("b", low, cfg)),
          "engagement under O-111a without a ruling is refused")
    hi = copy.deepcopy(low)
    hi["engagement_at_capture"] = {"views": 12000, "reposts": None}
    hi2 = copy.deepcopy(low)
    hi2["engagement_at_capture"] = {"views": None, "reposts": 100}
    check(dc.validate_call("b", hi, cfg) == [] and dc.validate_call("b", hi2, cfg) == [],
          "10,000 views or 100 reposts admits a row (either one)")
    far = copy.deepcopy(one)
    far["expiry"] = "2026-12-31"
    far["claims"][0]["date"] = "2026-12-08"
    check(any("30 days" in e for e in dc.validate_call("b", far, cfg)),
          "a claim dated more than 30 days after capture is refused")
    rb = copy.deepcopy(one)
    rb["claims"][7]["rule"] = {"kind": "move_by", "metric": "yfinance.mkt_qqq", "pct": -20}
    check(any("baseline_date" in e for e in dc.validate_call("b", rb, cfg)),
          "a rule without its baseline is refused")
    text = (REPO / "config" / "dated_calls.yaml").read_text(encoding="utf-8")
    check("@" not in text and one["forecaster"] == "an X membership-funnel account",
          "no handle in any row: the forecaster is described by kind")
    check(one["status"] == "proposed" and len(one["claims"]) == 17
          and str(one["expiry"]) == "2026-11-20",
          "row one: PROPOSED (the operator's accept-all), 17 claims, expiry 20 Nov 2026")
    db = str(Path(gate_tmp.mkdtemp("b139_seed_")) / "chester.db")
    r1 = dc.seed(db, cfg, now=GATE_NOW)
    r2 = dc.seed(db, cfg, now=GATE_NOW)
    conn = sqlite3.connect(db)
    try:
        st_row = conn.execute("SELECT status, direction FROM dated_calls").fetchall()
        n = conn.execute("SELECT count(*) FROM dated_call_claims").fetchone()[0]
        try:
            conn.execute("DELETE FROM dated_calls")
            deleted = True
        except sqlite3.DatabaseError:
            deleted = False
    finally:
        conn.close()
    check(r1["inserted"] == [CALL] and r2["synced"] == [CALL] and st_row == [("proposed", "down")]
          and n == 17, "seeded PROPOSED with 17 claims; a re-seed syncs and never duplicates")
    check(not deleted, "a call cannot be deleted (reject it instead)")


def price_rows() -> list[dict]:
    rows = []
    def put(key, vals):
        for d, v in vals.items():
            rows.append(row(key, d, v, "yfinance"))
    days = bdays("2025-11-03", "2026-11-20")
    # QQQ: 100 to 4 Nov, -7% on 5 Nov, then to 82 by 11 Nov (-18%: the -20% misses)
    q = {d: 100.0 for d in days if d <= "2026-11-04"}
    q.update({"2026-11-05": 93.0, "2026-11-06": 90.0, "2026-11-09": 86.0,
              "2026-11-10": 84.0, "2026-11-11": 82.0, "2026-11-12": 79.0})
    put("yfinance.mkt_qqq", q)
    g = {d: 6000.0 for d in days if d <= "2026-11-04"}
    g.update({"2026-11-05": 5800.0, "2026-11-06": 5600.0, "2026-11-20": 5390.0})
    put("yfinance.mkt_gspc", g)
    put("yfinance.mkt_btc_usd", {"2026-11-04": 80000.0, "2026-11-10": 71000.0,
                                 "2026-11-18": 69500.0, "2026-11-21": 72000.0})
    s = {d: 300.0 for d in days if d <= "2026-11-04"}
    s["2026-06-01"] = 400.0
    s.update({"2026-11-13": 260.0, "2026-11-20": 250.0})
    put("yfinance.mkt_smh", s)
    put("yfinance.mkt_ewy", {"2026-11-04": 70.0, "2026-11-21": 60.0})
    return rows


def group_e() -> None:
    head("E. THE SCORING RULE")
    cfg = dc.config()
    db = store_with(price_rows(), "score")
    dc.seed(db, cfg, now=GATE_NOW)
    before = dc.grade_due("2026-11-05T12:00:00+00:00", db, cfg)
    check(before["scored"] == [] and before["waiting"] == 17,
          "before any claim's date has passed: nothing written, 17 waiting")
    mid = dc.grade_due("2026-11-12T23:00:00+00:00", db, cfg)
    got = {x["claim_id"]: x for x in mid["scored"]}
    check(got.get("c01", {}).get("score") == "hit" and "-7.00%" in got["c01"]["detail"],
          "a one-day move: QQQ -7.00% on 5 Nov against -6.4% is a hit")
    check(got.get("c08", {}).get("score") == "miss" and "-18.00%" in got["c08"]["detail"],
          "a move by a date: QQQ at most -18% by 11 Nov against -20% is a miss "
          "(the 12 Nov close is after the date)")
    check(got.get("c02", {}).get("score") == "unresolved" and got["c02"]["by"] == "grading_pass",
          "a claim without a rule is unresolved, left for the operator")
    check("c10" not in got and "c15" not in got,
          "claims dated 20 Nov are not scored on 12 Nov")
    late = dc.grade_due("2026-11-21T23:00:00+00:00", db, cfg)
    g2 = {x["claim_id"]: x for x in late["scored"]}
    check(g2.get("c10", {}).get("score") == "hit",
          "the S&P 500 -10.17% from the 4 Nov close by 20 Nov: a hit")
    check(g2.get("c11", {}).get("score") == "hit" and "69,500.00" in g2["c11"]["detail"],
          "a level by a date: bitcoin's low 69,500 under 70,000 by 20 Nov: a hit (the 21 Nov close is after it)")
    check(g2.get("c15", {}).get("score") == "miss" and "-37.50%" in g2["c15"]["detail"],
          "a move from the high: SMH at most -37.5% from its 400 high against -38%: a miss")
    check("c16" in g2 and g2["c16"]["score"] == "unresolved",
          "EWY with no close inside the window by 20 Nov: unresolved, never a guess")
    again = dc.grade_due("2026-11-25T23:00:00+00:00", db, cfg)
    check(again["scored"] == [], "a second pass writes nothing: each score is written once")
    conn = sqlite3.connect(db)
    try:
        try:
            conn.execute("UPDATE dated_call_scores SET score='hit' WHERE claim_id='c08'")
            edited = True
        except sqlite3.DatabaseError:
            edited = False
    finally:
        conn.close()
    check(not edited, "a score is never edited (trigger)")
    ruled = copy.deepcopy(cfg)
    ruled["calls"][CALL]["claims"][1]["operator_score"] = "hit"
    db2 = store_with(price_rows(), "ruled")
    dc.seed(db2, ruled, now=GATE_NOW)
    gr = {x["claim_id"]: x for x in dc.grade_due("2026-11-07T00:00:00+00:00", db2, ruled)["scored"]}
    check(gr.get("c02", {}).get("score") == "hit" and gr["c02"]["by"] == "operator",
          "the operator's ruled score is written in place of unresolved")
    from altdata import narratives                               # noqa: PLC0415
    db3 = store_with(price_rows(), "resolve")
    dc.seed(db3, cfg, now=GATE_NOW)
    rr = narratives.resolve_due("2026-11-07T00:00:00+00:00", db_path=db3)
    check(len((rr.get("dated_calls") or {}).get("scored") or []) == 3,
          "the register's resolve_due runs the pass (3 claims dated 5-6 Nov scored)")


def group_f() -> None:
    head("F. THE TWO COUNTS")
    cfg = dc.config()
    empty = store_with([], "nocount")
    with observations.ObservationStore(empty) as st:
        check(dc.count_rows(st, GATE_NOW, cfg=cfg) == [], "no table: nothing to store")
        dc.connect(empty).close()
        check(dc.count_rows(st, GATE_NOW, cfg=cfg) == [], "an empty register: nothing stored")
        check(dc.count_line(st, GATE_NOW, cfg) == "Viral calls captured: no rows yet (the X-digest triage writes them).",
              "the no-rows path prints 'no rows yet'")
    db = store_with([], "count")
    two = copy.deepcopy(cfg)
    up = copy.deepcopy(two["calls"][CALL])
    up.update(direction="up", captured_at="2026-11-07T02:00:00Z")      # 6 Nov 21:00 ET
    rej = copy.deepcopy(up)
    rej.update(status="rejected")
    two["calls"]["fixture_up_call"] = up
    two["calls"]["fixture_rejected"] = rej
    dc.seed(db, two, now=GATE_NOW)
    with observations.ObservationStore(db) as st:
        rows = dc.count_rows(st, GATE_NOW, cfg=two)
        st.write_many(rows)
        line = dc.count_line(st, GATE_NOW, two)
    by = {(r["registry_key"].rsplit(".", 1)[1], r["observed_at"]): r for r in rows}
    check(by[("down", "2026-11-06")]["value"] == 1.0 and by[("up", "2026-11-06")]["value"] == 1.0,
          "6 Nov ET: one crash call, one melt-up call (02:00Z on 7 Nov is 6 Nov ET); the rejected one not counted")
    check(by[("down", "2026-11-07")]["value"] == 0.0 and min(d for _, d in by) == "2026-11-06",
          "zeros from the first captured row, nothing before it")
    check(by[("down", "2026-11-06")]["available_at"] == "2026-11-07T04:59:59Z"
          and by[("down", "2026-11-07")]["available_at"] == GATE_NOW,
          "a day's count is knowable at its ET end; today's at the cutoff")
    check(line == "Viral calls captured on 2026-11-07: crash calls 0, melt-up calls 0 (attention, no direction).",
          f"the stored counts read back: {line!r}")
    inp = cfg["capitulation_count_inputs"]
    check([i["key"] for i in inp] == ["calc.viral_call_count.down", "calc.viral_call_count.up"]
          and all(i["direction"] == "none" and i["scores"] is False and i["empty"] == "no rows yet"
                  for i in inp),
          "item 97's two inputs: the two counts, no direction, no family scored, 'no rows yet'")
    cap = cfg["capture"]
    check(cap["min_views"] == 10000 and cap["min_reposts"] == 100 and cap["max_claim_days"] == 30
          and str(cap["review_on"]) == "2026-12-06",
          "O-111a's thresholds (10,000 views or 100 reposts, 30 days) and their review date")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    ents = [reg["metrics"].get(k) if "metrics" in reg else None for k in
            ("calc.viral_call_count.down", "calc.viral_call_count.up")]
    if not any(ents):
        txt = (REPO / "metrics_registry.yaml").read_text(encoding="utf-8")
        ok = all(f"  {k}:\n" in txt for k in ("calc.viral_call_count.down", "calc.viral_call_count.up"))
    else:
        ok = all(e and e.get("trigger_eligible") is False for e in ents)
    barred = any("calc.viral_call_count.*" in (b.get("keys") or [])
                 for b in reg.get("market_state_barred") or [])
    check(ok and barred, "both keys registered, trigger-ineligible, barred from the market-state object")
    import subprocess                                           # noqa: PLC0415
    lst = subprocess.run([sys.executable, str(REPO / "tools" / "gate_list.py"), "--kind", "code"],
                         capture_output=True, text=True, cwd=REPO).stdout
    check("tools/validate_items_131_132.py" in lst, "the gate is in the list (tools/gate_list.py)")


def main() -> int:
    pin_clock()
    print(f"the gate's clock is pinned to {GATE_NOW}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback                                    # noqa: PLC0415
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
