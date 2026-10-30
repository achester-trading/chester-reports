#!/usr/bin/env python3
"""
Validation gate: 6f tranche 2, the market-state object's calibration (a63;
rulings 7a and 8a of 24 Oct 2026; docs/briefs/6f-spec-draft-2026-10-24.md
section 3). Synthetic fixtures only: no network, no live store, no model.

  A  POINT IN TIME. A calibration read as of a cutoff uses no object computed
     after it: an object whose available_at is past the cutoff is not read, a
     pair whose t + h object is not yet knowable is not counted, a later vintage
     of a session is not read before it exists, and an object under another
     method version is never read.
  B  THE n-OF-30 RENDERING. Below 30 independent starts a row is the literal
     "uncalibrated (n = k of 30)", k by hand (starts at least h sessions apart);
     at 30 the row prints its probabilities, add-half smoothed, by hand, summing
     to 1; never an empty field.
  C  THE LEDGER. No row before calibration; a calibrated dial row writes one
     binary row per state, each with its resolution criterion, coherent; no
     dimension row ever; a due row resolves against the stored object and is
     scored by the existing tooling.
  D  WHERE IT PRINTS. The close's one line (every dial, every horizon), the
     Weekly's and the Monthly's table, the Monthly's unledgered dimension table,
     and the close writes the ledger after it stores the object.
  E  alignment_weekly AT ENTRY (6f tranche 4, A65; ruling 9a). The packet's
     direction against the weekly per-horizon read of the decision's session:
     aligned, counter and neutral on calibrated fixtures; absent with its reason
     when the read is uncalibrated ("uncalibrated (n = k of 30)"), when the read
     is absent, and when the session's object does not exist yet; the register
     writes the stamp and its basis, carries both forward on a supersession, and
     a register without the column records neither.
  F  THE MIGRATION (tools/migrate_alignment_weekly.py) on a scratch register:
     the dry run changes nothing; --apply refuses without a backup and with a
     backup path that exists; with a fresh backup it adds both columns in one
     transaction, backfills nothing, logs, and a second run does nothing.
  G  THE QUARTERLY'S CUT (register/scoreboard.alignment_split): counts and hit
     rates by horizon_alignment and by alignment_weekly over the previous
     quarter, a cell printed only at n >= 10, else "n < 10"; it prints in the
     Quarterly's register table and not in the Monthly's.

    python tools/validate_6f_calibration.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

TD = Path(gate_mkdtemp("6f_calibration_"))
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


def obj(day: str, macro: str, vol: str = "normal", gamma: str = "positive",
        method: str | None = None, dims: dict | None = None) -> dict:
    import regime
    return {"object": "market_state", "session": day,
            "method_version": method or regime.METHOD_VERSION,
            "dials": {"macro": {"state": macro}, "vol": {"state": vol},
                      "gamma": {"state": gamma}},
            "dimensions": {k: {"state": v} for k, v in (dims or {}).items()}}


def store_with(name: str, items: list[tuple[str, str, dict]]) -> str:
    """items: (session, available_at, object)."""
    from altdata import observations
    p = TD / f"{name}.db"
    with observations.ObservationStore(str(p)) as st:
        for day, avail, o in items:
            st.write("market_state", None, day, avail, json.dumps(o), source="derived_state")
    return str(p)


def evening(day: str) -> str:
    return f"{day}T21:30:00+00:00"


def group_a(days: list[str]) -> None:
    from altdata import observations, state_calibration as sc
    head("A. POINT IN TIME")
    items = [(d, evening(d), obj(d, "expansion")) for d in days[:40]]
    # A later vintage of session 10 that says otherwise, computed after the cutoff.
    late = "2026-10-24T12:00:00+00:00"
    items.append((days[10], late, obj(days[10], "contraction")))
    # An object under another method.
    items.append((days[11], evening(days[11]).replace("21:30", "21:31"), obj(days[11], "stagflation",
                                                   method="market-state-method-8")))
    db = store_with("pit", items)
    cut = evening(days[30])
    with observations.ObservationStore(db) as st:
        objs = sc.stored_objects(st, cut)
        m = sc.matrices(st, cut)
    check(max(objs) == days[30] and all(
        o["method_version"].endswith("method-11") for o in objs.values()),
        f"read as of session 31's evening: 31 objects, none after it, none of another "
        f"method ({len(objs)} read, last {max(objs)})")
    check(objs[days[10]]["dials"]["macro"]["state"] == "expansion",
          "a later vintage of a session is not read before it exists")
    t5 = m["dials"]["macro"][5]["expansion"]
    check(t5["n_pairs"] == 31 - 5 and all(s <= days[30 - 5] for s in t5["starts"]),
          f"a pair counts only when its t + 5 object is knowable at the cutoff "
          f"({t5['n_pairs']} pairs, the last starting {max(t5['starts'])})")
    with observations.ObservationStore(db) as st:
        m_late = sc.matrices(st, late)
        objs_late = sc.stored_objects(st, late)
    check(objs_late[days[10]]["dials"]["macro"]["state"] == "contraction"
          and m_late["dials"]["macro"][5].get("contraction"),
          "read after the later vintage exists, that vintage is the session's object")


def group_b(days: list[str]) -> None:
    from altdata import observations, state_calibration as sc
    head("B. THE n-OF-30 RENDERING")
    # 60 sessions all expansion: at h = 5, independent starts 0, 5, ..., 50 = 11.
    db = store_with("few", [(d, evening(d), obj(d, "expansion")) for d in days[:60]])
    with observations.ObservationStore(db) as st:
        m = sc.matrices(st, evening(days[59]))
    cur = obj(days[59], "expansion")
    r5 = sc.reads(m, cur)["macro"][5]
    k_hand = len(range(0, 60 - 5, 5))
    check(not r5["calibrated"] and r5["text"] == f"uncalibrated (n = {k_hand} of 30)",
          f"55 pairs, starts at least 5 apart: {k_hand} independent, printed "
          f"'{r5['text']}'")
    r63 = sc.reads(m, cur)["macro"][63]
    check(r63["text"] == "uncalibrated (n = 0 of 30)",
          f"63 sessions on a 60-session history: '{r63['text']}', never empty")
    # 400 sessions alternating in blocks: expansion for 10, contraction for 10.
    seq = ["expansion" if (i // 10) % 2 == 0 else "contraction" for i in range(400)]
    db2 = store_with("many", [(d, evening(d), obj(d, s)) for d, s in zip(days[:400], seq)])
    with observations.ObservationStore(db2) as st:
        m2 = sc.matrices(st, evening(days[399]))
    tr = m2["dials"]["macro"][5]["expansion"]
    pairs = [(i, seq[i + 5]) for i in range(395) if seq[i] == "expansion"]
    n_e = sum(1 for _, s in pairs if s == "expansion")
    n_c = sum(1 for _, s in pairs if s == "contraction")
    starts = [i for i, _ in pairs]
    k, last = 0, None
    for i in starts:
        if last is None or i - last >= 5:
            k, last = k + 1, i
    row = sc.reads(m2, obj(days[399], "expansion"))["macro"][5]
    states = sorted(set(sc.dial_states_declared("macro")) | {"expansion", "contraction"})
    tot = len(pairs) + 0.5 * len(states)
    pe = (n_e + 0.5) / tot
    check(tr["independent"] == k >= 30 and row["calibrated"]
          and abs(row["probs"]["expansion"] - pe) < 1e-12
          and abs(sum(row["probs"].values()) - 1.0) < 1e-12
          and all(0 < p < 1 for p in row["probs"].values()),
          f"{k} independent starts: calibrated; P(expansion) = ({n_e} + 0.5) / "
          f"({len(pairs)} + 0.5 x {len(states)}) = {pe:.4f} by hand; the row sums to 1, "
          f"no state at 0 or 1")


def group_c(days: list[str]) -> None:
    from altdata import observations, probability_ledger as pl, state_calibration as sc
    head("C. THE LEDGER: DIAL ROWS ONLY, AND ONLY ONCE CALIBRATED")
    db = store_with("few2", [(d, evening(d), obj(d, "expansion", dims={"credit": "easy"}))
                             for d in days[:60]])
    led = str(TD / "ledger_few.db")
    with observations.ObservationStore(db) as st, pl.ProbabilityLedger(led) as lg:
        m = sc.matrices(st, evening(days[59]))
        n = sc.write_ledger(obj(days[59], "expansion"), m, lg)
        rows = lg.all_rows()
    check(n == 0 and not rows, "an uncalibrated row writes nothing to the ledger")
    seq = ["expansion" if (i // 10) % 2 == 0 else "contraction" for i in range(400)]
    db2 = store_with("many2", [(d, evening(d), obj(d, s, dims={"credit": "easy"}))
                               for d, s in zip(days[:400], seq)])
    led2 = str(TD / "ledger_many.db")
    cur = obj(days[399], "expansion", dims={"credit": "easy"})
    with observations.ObservationStore(db2) as st, pl.ProbabilityLedger(led2) as lg:
        m2 = sc.matrices(st, evening(days[399]))
        n2 = sc.write_ledger(cur, m2, lg, emitted_at=evening(days[399]))
        rows2 = lg.all_rows()
        coh = lg.coherence()
    sets = {r["scenario_set"] for r in rows2}
    check(n2 > 0 and all(r["source"] == "market_state"
                         and str(r["scenario_set"]).split(":")[1] in sc.DIALS
                         and r["resolution_criterion"].startswith("the published state of the")
                         for r in rows2)
          and not any("credit" in str(r["scenario_set"]) for r in rows2),
          f"{n2} rows in {len(sets)} sets, every one a dial's, each with its resolution "
          f"criterion; no dimension row ever")
    check(not [c for c in coh if str(c.get("scenario_set", "")).startswith("state:")],
          "each set sums to 1 (the ledger's coherence check)")
    # Resolution against the stored object for the horizon date.
    hd = sc.horizon_date(days[399], 5)
    later = sc.session_days_after = None
    db3 = store_with("resolve", [(days[399], evening(days[399]), cur),
                                 (hd, evening(hd), obj(hd, "contraction"))])
    with observations.ObservationStore(db3) as st, pl.ProbabilityLedger(led2) as lg:
        nres = sc.resolve_due(st, lg, evening(hd))
        scored = [r for r in lg.all_rows() if r["brier"] is not None
                  and r["scenario_set"] == f"state:macro:5s:{days[399]}"]
        src = lg.score_by_source().get("market_state") or {}
    con = next((r for r in scored if r["claim"].startswith("the macro dial is contraction")), None)
    check(nres > 0 and con and con["outcome"] == 1
          and abs(con["brier"] - (con["probability"] - 1) ** 2) < 1e-12
          and src.get("n", 0) >= len(scored),
          f"the 5-session rows resolve against the stored object for {hd} (contraction: "
          f"outcome 1, Brier (p - 1)^2), scored by the ledger's own tooling "
          f"({nres} resolved)")


def group_d() -> None:
    from altdata import state_calibration as sc
    head("D. WHERE IT PRINTS")
    m = {"dials": {}, "dimensions": {"credit": {}}, "sessions": 0, "method": "x", "as_of": ""}
    cur = obj("2026-10-23", "expansion")
    ln = sc.close_line(m, cur)
    check(ln.startswith("Dial transitions -- ") and all(d in ln for d in sc.DIALS)
          and ln.count("uncalibrated (n = 0 of 30)") == 9,
          "the close's one line: three dials x three horizons, each 'uncalibrated "
          "(n = 0 of 30)' on an empty history")
    t = sc.table(m, cur)
    dt_ = sc.dimension_table(m, cur)
    check(len(t["rows"]) == 9 and len(dt_["rows"]) == 1,
          "the Weekly's and the Monthly's table (nine rows); the Monthly's dimension table")
    src = {f: (REPO / f).read_text(encoding="utf-8") for f in
           ("daily_cascade/close_report.py", "daily_cascade/stack.py",
            "daily_cascade/weekly_stack.py", "monthly_macro/stack.py")}
    check("_sc.write_ledger(obj, _m, _lg)" in src["daily_cascade/close_report.py"]
          and "dimensions=False" in src["daily_cascade/close_report.py"]
          and "state_v2_block.close_extras(built, st, cutoff)" in src["daily_cascade/stack.py"]
          and "state_v2_block.calibration_subsection(st, cutoff)" in src["daily_cascade/weekly_stack.py"]
          and "calibration_subsection(st, now, dimensions=True)" in src["monthly_macro/stack.py"],
          "the close writes the dial rows after it stores the object; the close, the "
          "Weekly and the Monthly print it")
    msrc = (REPO / "altdata" / "state_calibration.py").read_text(encoding="utf-8")
    check("import regime" in msrc and "regime.compute(" not in msrc,
          "the calibration reads stored objects and never recomputes one")


def hobj(day: str, weekly, absent: str | None = None) -> dict:
    """A stored object with the per-horizon block (weekly None = absent)."""
    o = obj(day, "expansion")
    w = {"horizon": "weekly", "state": weekly, "sessions": 20}
    if weekly is None:
        w["absent_reason"] = absent or "no observation for calc.trend_spy_vs_50d"
    o["horizons"] = {"weekly": w}
    return o


def scratch_register(name: str):
    from register.store import Register
    return Register(str(TD / f"{name}.db"),
                    entities_path=REPO / "config" / "tracked_entities.yaml")


BASE = dict(instrument="SPY", thesis="fixture", edge_type="e", horizon="swing",
            invalidation="a close below 95", status="draft")


def group_e() -> None:
    import importlib
    import sqlite3
    import regime
    from altdata import observations
    decide = importlib.import_module("decide")
    head("E. alignment_weekly AT ENTRY")
    days = regime.session_days("2023-06-01", "2026-10-23")
    now = "2026-10-23T23:59:00+00:00"            # 19:59 ET, Friday's close complete
    last = days[-1]

    def stamp(name, items, direction):
        db = store_with(name, items)
        with observations.ObservationStore(db) as st:
            return decide.alignment_weekly(direction, now=now, store=st)
    up = [(d, evening(d), hobj(d, "up")) for d in days]
    k_up = len(range(0, len(days) - 20, 20))
    check(k_up >= 30, f"the calibrated fixture: {len(days)} sessions, {k_up} independent "
                      f"starts at 20 sessions")
    for direction, want in (("long", "aligned"), ("short", "counter"), ("hedge", "neutral")):
        got, why = stamp(f"up_{direction}", up, direction)
        check(got == want and last in why,
              f"weekly read up, {direction} -> {want} ({why})")
    flat = [(d, evening(d), hobj(d, "flat")) for d in days]
    got, why = stamp("flat", flat, "long")
    check(got == "neutral", f"weekly read flat, long -> neutral ({why})")
    few = [(d, evening(d), hobj(d, "up")) for d in days[-60:]]
    got, why = stamp("few", few, "long")
    k_few = len(range(0, 60 - 20, 20))
    check(got is None and f"uncalibrated (n = {k_few} of 30)" in why,
          f"60 sessions: absent, uncalibrated, k = {k_few} by hand ({why})")
    gone = up[:-1] + [(last, evening(last),
                       hobj(last, None, "calc.trend_spy_vs_50d was last observed 2026-09-01"))]
    got, why = stamp("gone", gone, "long")
    check(got is None and "weekly read absent" in why and "2026-09-01" in why,
          f"the weekly read absent on the session's object: absent, its reason ({why})")
    got, why = stamp("early", up[:-1], "long")
    check(got is None and f"entered before the {last} object existed" in why
          and days[-2] in why,
          f"a decision entered before the session's object exists: absent ({why})")
    v1 = [(d, evening(d), obj(d, "expansion")) for d in days[-5:]]
    got, why = stamp("v1", v1, "long")
    check(got is None and "no per-horizon reads" in why,
          f"an object without horizons: absent ({why})")
    # The register: written beside horizon_alignment, absent as NULL with its basis.
    reg = scratch_register("reg_e")
    try:
        check(reg.has_alignment_weekly, "a new register carries the column")
        a = reg.record(direction="long", alignment_weekly="counter",
                       alignment_weekly_basis="direction long against the weekly read down",
                       horizon_alignment="aligned", **BASE)
        b = reg.record(direction="long", alignment_weekly=None,
                       alignment_weekly_basis="weekly read up, uncalibrated (n = 1 of 30)",
                       **BASE)
        ra, rb = reg.get(a), reg.get(b)
        check(ra["alignment_weekly"] == "counter" and ra["horizon_alignment"] == "aligned"
              and rb["alignment_weekly"] is None
              and "uncalibrated" in rb["alignment_weekly_basis"],
              "the register writes the stamp beside horizon_alignment, and an absent "
              "stamp as NULL with its basis")
        try:
            reg.record(direction="long", alignment_weekly="sideways", **BASE)
            ok = False
        except ValueError:
            ok = True
        check(ok, "a value outside aligned / neutral / counter is refused")
    finally:
        reg.close()
    src = (REPO / "tools" / "decide.py").read_text(encoding="utf-8")
    check('alignment_weekly=old_d.get("alignment_weekly")' in src
          and 'alignment_weekly_basis=old_d.get("alignment_weekly_basis")' in src,
          "a supersession carries both forward from the old row, never recomputed")
    # A live register as it stands before the migration: today's schema without
    # the two columns.
    scratch_register("reg_old").close()
    c = sqlite3.connect(str(TD / "reg_old.db"))
    c.execute("ALTER TABLE decisions DROP COLUMN alignment_weekly_basis")
    c.execute("ALTER TABLE decisions DROP COLUMN alignment_weekly")
    c.commit()
    c.close()
    reg = scratch_register("reg_old")
    try:
        d = reg.record(direction="long", alignment_weekly="aligned",
                       alignment_weekly_basis="x", **BASE)
        cols = [r[1] for r in reg.conn.execute("PRAGMA table_info(decisions)")]
        check(not reg.has_alignment_weekly and "alignment_weekly" not in cols
              and reg.get(d) is not None,
              "a register that predates the migration: opening it adds no column, and "
              "record() writes the row without the stamp")
    finally:
        reg.close()


def group_f() -> None:
    import sqlite3
    import migrate_alignment_weekly as mig
    head("F. THE MIGRATION, ON A SCRATCH REGISTER")
    db = TD / "mig.db"
    c = sqlite3.connect(str(db))
    c.execute("CREATE TABLE decisions (id TEXT PRIMARY KEY, created_at TEXT, "
              "horizon_alignment TEXT)")
    c.executemany("INSERT INTO decisions VALUES (?,?,?)",
                  [(f"d{i}", "2026-10-01", "aligned") for i in range(3)])
    c.commit()
    c.close()
    before = db.read_bytes()
    lines: list[str] = []
    rc = mig.run(str(db), out=lines.append)
    for ln in lines:
        print(f"    | {ln}")
    check(rc == 0 and db.read_bytes() == before
          and any("would add: alignment_weekly TEXT" in ln for ln in lines)
          and any("would add: alignment_weekly_basis TEXT" in ln for ln in lines)
          and any("3 existing rows read 'entered before 6f'" in ln for ln in lines),
          "the dry run (the default) prints both columns and the rows left before 6f, "
          "and changes nothing")
    out: list[str] = []
    rc = mig.run(str(db), apply=True, out=out.append)
    check(rc == 2 and any("REFUSED: --apply needs --backup" in ln for ln in out)
          and db.read_bytes() == before, "--apply without --backup is refused")
    taken = TD / "exists.db"
    taken.write_bytes(b"x")
    out = []
    rc = mig.run(str(db), apply=True, backup=str(taken), out=out.append)
    check(rc == 2 and any("exists" in ln for ln in out) and db.read_bytes() == before,
          "--apply with a backup path that exists is refused")
    bk = TD / "bk" / "pre.db"
    out = []
    rc = mig.run(str(db), apply=True, backup=str(bk), out=out.append)
    c = sqlite3.connect(str(db))
    cols = [r[1] for r in c.execute("PRAGMA table_info(decisions)")]
    vals = c.execute("SELECT alignment_weekly, alignment_weekly_basis FROM decisions").fetchall()
    c.close()
    logf = TD / mig.LOG_NAME
    log = logf.read_text(encoding="utf-8") if logf.exists() else ""
    check(rc == 0 and bk.is_file()
          and {"alignment_weekly", "alignment_weekly_basis"} <= set(cols)
          and vals == [(None, None)] * 3 and "migrate_alignment_weekly" in log,
          f"with a fresh backup: backed up and checked, both columns added, nothing "
          f"backfilled, logged ({out[-1] if out else ''})")
    out = []
    rc = mig.run(str(db), apply=True, backup=str(TD / "bk" / "again.db"), out=out.append)
    check(rc == 0 and any("nothing to do" in ln for ln in out)
          and not (TD / "bk" / "again.db").exists(), "a second run changes nothing")
    msrc = (REPO / "tools" / "migrate_alignment_weekly.py").read_text(encoding="utf-8")
    check("BEGIN IMMEDIATE" in msrc and "ROLLBACK" in msrc,
          "the ALTERs are one transaction: both columns or neither")
    ssrc = (REPO / "register" / "store.py").read_text(encoding="utf-8")
    start = ssrc.index('for col in ("signals_used TEXT"')
    alters = ssrc[start:ssrc.index("ALTER TABLE decisions ADD COLUMN {col}", start)]
    check("alignment_weekly" not in alters,
          "the register's open-time ALTER list does not carry the columns: the schema "
          "changes only through the operator's migration")


def group_g() -> None:
    from altdata import grader
    from register import scoreboard as sb
    head("G. THE QUARTERLY'S CUT")
    check(sb.previous_quarter("2026-10-24") == ("2026-07-01", "2026-09-30")
          and sb.previous_quarter("2027-01-05") == ("2026-10-01", "2026-12-31"),
          "the window is the previous calendar quarter")
    reg = scratch_register("reg_g")
    ids = {}
    try:
        # 12 aligned/aligned (8 hits), 4 counter/counter, 3 absent, 2 before 6f.
        spec = ([("aligned", "aligned", "w", 1.0)] * 8
                + [("aligned", "aligned", "w", -1.0)] * 4
                + [("counter", "counter", "w", 1.0)] * 4
                + [("neutral", None, "uncalibrated (n = 3 of 30)", 1.0)] * 3
                + [("aligned", None, None, 1.0)] * 2)
        for h, w, basis, ret in spec:
            ids[reg.record(direction="long", horizon_alignment=h, alignment_weekly=w,
                           alignment_weekly_basis=basis, **BASE)] = ret
    finally:
        reg.close()
    db = str(TD / "reg_g.db")
    with grader.GradeStore(db) as gs:
        for i, (did, ret) in enumerate(ids.items()):
            gs.write({"decision_id": did, "horizon": "swing",
                      "graded_at": f"2026-08-{10 + i % 15:02d}T21:00:00+00:00",
                      "horizon_date": "2026-08-01", "return_pct": ret,
                      "observations_json": "[]", "price_source": "fixture",
                      "method_version": grader.METHOD_VERSION})
        # A grade outside the quarter is not counted (it would also replace the
        # first decision's latest grade if it were).
        gs.write({"decision_id": next(iter(ids)), "horizon": "swing",
                  "graded_at": "2026-10-02T21:00:00+00:00", "horizon_date": "2026-10-01",
                  "return_pct": -5.0, "observations_json": "[]", "price_source": "fixture",
                  "method_version": grader.METHOD_VERSION})
    s = sb.alignment_split("2026-10-24T12:00:00+00:00", db_path=db)
    ha, aw = s["by_horizon_alignment"], s["by_alignment_weekly"]
    check(ha["aligned"]["n"] == 14 and ha["aligned"]["hits"] == 10 and ha["aligned"]["printed"]
          and ha["counter"]["n"] == 4 and not ha["counter"]["printed"],
          f"by horizon_alignment: aligned n=14, 10 hits, printed; counter n=4, not "
          f"printed ({ha})")
    check(aw["aligned"]["n"] == 12 and aw["aligned"]["hits"] == 8
          and abs(aw["aligned"]["hit_rate"] - 8 / 12) < 1e-12 and aw["aligned"]["printed"]
          and aw["absent at entry"]["n"] == 3 and aw["entered before 6f"]["n"] == 2
          and aw["neutral"]["n"] == 0,
          f"by alignment_weekly: aligned n=12, 8 hits (8/12 by hand); absent at entry 3; "
          f"entered before 6f 2; neutral 0 ({aw})")
    lines = sb.alignment_lines(s)
    check(len(lines) == 2 and "aligned: n=12, 8 hits (67%)" in lines[1]
          and "counter: n < 10" in lines[1] and "neutral: n < 10" in lines[1]
          and "entered before 6f: n < 10" in lines[1],
          f"the floor: a cell under 10 prints 'n < 10' and no figure ({lines[1]})")
    from monthly_macro import stack
    rm = {"state": "empty", "reason": "x"}
    mo = [t for t in stack.detail_tables({"register_month": rm}, set())
          if t["id"] == "register"][0]
    qu = [t for t in stack.detail_tables({"register_month": {**rm, "alignment_split": s}},
                                         set()) if t["id"] == "register"][0]
    check(not any("alignment_weekly" in ln for ln in mo["lines"])
          and any("alignment_weekly" in ln for ln in qu["lines"]),
          "the cut prints in the register table of a payload that carries it (the "
          "Quarterly's), and not in the Monthly's")
    psrc = (REPO / "monthly_macro" / "payload.py").read_text(encoding="utf-8")
    check('if period == "quarter":' in psrc and "scoreboard.alignment_split(cutoff)" in psrc,
          "only the Quarterly's payload (period quarter) builds the split")


def main() -> int:
    import regime
    days = regime.session_days("2024-06-03", "2026-10-23")
    for g in (lambda: group_a(days), lambda: group_b(days), lambda: group_c(days), group_d,
              group_e, group_f, group_g):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"a group raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
