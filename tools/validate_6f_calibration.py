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

    python tools/validate_6f_calibration.py
"""

from __future__ import annotations

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


def main() -> int:
    import regime
    days = regime.session_days("2024-06-03", "2026-10-23")
    for g in (lambda: group_a(days), lambda: group_b(days), lambda: group_c(days), group_d):
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
