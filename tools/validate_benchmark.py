"""
Validation gate for Book Z -- the benchmark ledgers (EL-3, P5-B).

  A  START. The register's first packet date, or 1 Sep 2026 if earlier.
  B  THE ARITHMETIC. Every ledger starts at 100.0; SPY buy-and-hold is units x
     close plus dividend cash; cash accrues DTB3 x days / 360 from the previous
     session's rate; 60/40 rebalances at the close of the first session of each
     month and nowhere else.
  C  POINT-IN-TIME, NEVER RECOMPUTED. A later vintage of a close does not touch a
     stored mark; a rerun writes nothing; the next session adds one row per
     ledger; catch-up rows say `reconstructed` and the pass's own session
     `ingest_instant`, and no available_at is backdated.
  D  ABSENCE. A session without AGG leaves the 60/40 unmarked that day and the
     others marked; the line says what is missing rather than printing a zero.
  E  WIRING. AGG in the basket, paper.benchmark registered, the 16:45 pass runs
     the marker after its price pull and before the report, and the Weekly and
     Monthly carry the line beside each book.

    python tools/validate_benchmark.py
"""

from __future__ import annotations

import datetime as dt
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import benchmark as bz, observations, session   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = FAIL = 0
LINE = "=" * 78


def check(c: bool, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def sessions(first: str, last: str) -> list[str]:
    d, out = dt.date.fromisoformat(first), []
    while d <= dt.date.fromisoformat(last):
        if session.is_trading_session(d.isoformat()):
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def seed(st, key, days, values):
    st.write_many([{"registry_key": key, "instrument": None, "observed_at": d,
                    "available_at": f"{d}T20:20:00+00:00", "value": float(v),
                    "source": "synthetic", "availability_kind": "reconstructed"}
                   for d, v in zip(days, values)])


def marks(st) -> dict:
    out: dict = {ld: {} for ld in bz.LEDGERS}
    for ld in bz.LEDGERS:
        for r in st.as_of(bz.KEY, instrument=ld):
            out[ld][str(r["observed_at"])[:10]] = (json.loads(r["value_text"]), r)
    return out


def main() -> int:
    print(f"{LINE}\nBook Z -- the benchmark ledgers\n{LINE}")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        reg_db = str(Path(td) / "reg.db")
        obs_db = str(Path(td) / "obs.db")

        # --- A. start ------------------------------------------------------------
        print(f"\n{LINE}\nA. START\n{LINE}")
        from register.store import Register
        with Register(reg_db):
            pass
        check(bz.start_date(reg_db) == dt.date(2026, 9, 1),
              "an empty register starts Book Z on 1 Sep 2026")
        with Register(reg_db) as reg:
            reg.conn.execute(
                "INSERT INTO decisions (id, created_at, decision_time, instrument,"
                " instrument_norm, direction, thesis, edge_type, horizon,"
                " invalidation, status) VALUES ('d0','2026-08-20T14:00:00+00:00',"
                "'2026-08-20T14:00:00+00:00','SPY','SPY','long','t','e','swing',"
                "'x','draft')")
            reg.conn.execute(
                "INSERT INTO decision_packets (packet_id, decision_id, created_at,"
                " run_id, decision_time, available_at_cutoff, git_sha,"
                " code_dirty, data_manifest_json, data_manifest_hash,"
                " metrics_registry_version, source_registry_version,"
                " output_hash, volatile_fields) VALUES ('p0','d0',"
                "'2026-08-20T14:00:00+00:00','r','2026-08-20T14:00:00+00:00',"
                "'2026-08-20T14:00:00+00:00','x',0,'{}','h','1','1','o','[]')")
            reg.conn.commit()
        check(bz.start_date(reg_db) == dt.date(2026, 8, 20),
              "a first packet on 20 Aug moves the start to 20 Aug (the earlier)")
        empty_reg = str(Path(td) / "reg_empty.db")
        with Register(empty_reg):
            pass

        # --- B. arithmetic -----------------------------------------------------------
        # EVERY DATE IN THE PAST. A close dated after today is not knowable today
        # and is -- correctly -- not marked, so the fixture runs August: Book Z
        # starts at a first packet on 3 Aug, and 1 Sep is the month boundary.
        print(f"\n{LINE}\nB. THE ARITHMETIC\n{LINE}")
        aug_reg = str(Path(td) / "reg_aug.db")
        with Register(aug_reg) as reg:
            reg.conn.execute(
                "INSERT INTO decisions (id, created_at, decision_time, instrument,"
                " instrument_norm, direction, thesis, edge_type, horizon,"
                " invalidation, status) VALUES ('d1','2026-08-03T14:00:00+00:00',"
                "'2026-08-03T14:00:00+00:00','SPY','SPY','long','t','e','swing',"
                "'x','draft')")
            reg.conn.execute(
                "INSERT INTO decision_packets (packet_id, decision_id, created_at,"
                " run_id, decision_time, available_at_cutoff, git_sha,"
                " code_dirty, data_manifest_json, data_manifest_hash,"
                " metrics_registry_version, source_registry_version,"
                " output_hash, volatile_fields) VALUES ('p1','d1',"
                "'2026-08-03T14:00:00+00:00','r','2026-08-03T14:00:00+00:00',"
                "'2026-08-03T14:00:00+00:00','x',0,'{}','h','1','1','o','[]')")
            reg.conn.commit()
        days = sessions("2026-08-03", "2026-09-02")
        spy = [600.0 + 2.0 * i for i in range(len(days))]
        agg = [100.0 - 0.1 * i for i in range(len(days))]
        with observations.ObservationStore(obs_db) as st:
            seed(st, bz.SPY, days, spy)
            seed(st, bz.AGG, days, agg)
            seed(st, bz.TBILL, days, [4.0] * len(days))
            seed(st, bz.SPY + "_dividend", ["2026-08-21"], [2.0])
        with observations.ObservationStore(obs_db) as st:
            r1 = bz.mark(through="2026-08-31", store=st, register_db=aug_reg)
            m = marks(st)
        n_aug = len(sessions("2026-08-03", "2026-08-31"))
        check(r1["start"] == "2026-08-03"
              and all(len(m[ld]) == n_aug for ld in bz.LEDGERS),
              f"one mark per session per ledger, 3-31 Aug ({n_aug} each)")
        check(all(m[ld]["2026-08-03"][0]["value"] == 100.0 for ld in bz.LEDGERS),
              "every ledger is 100.0 at the start date's close")
        i20 = days.index("2026-08-20")
        want = 100.0 / spy[0] * spy[i20]
        got = m["spy"]["2026-08-20"][0]["value"]
        check(abs(got - want) < 1e-5,
              f"SPY buy-and-hold before the dividend is units x close "
              f"({got:.6f} vs {want:.6f})")
        i31 = days.index("2026-08-31")
        want = 100.0 / spy[0] * spy[i31] + 100.0 / spy[0] * 2.0
        got = m["spy"]["2026-08-31"][0]["value"]
        check(abs(got - want) < 1e-5,
              f"and after the 21 Aug ex-date it holds the dividend as cash "
              f"({got:.6f} vs {want:.6f})")
        c1 = m["cash"]["2026-08-04"][0]["value"]
        check(abs(c1 - 100.0 * (1 + 0.04 * 1 / 360)) < 1e-5,
              f"cash accrues DTB3 x days / 360 over one calendar day ({c1:.6f})")
        c_mon = m["cash"]["2026-08-10"][0]
        check(c_mon["days"] == 3 and c_mon["from"] == "2026-08-07",
              "and over a weekend accrues three calendar days from the Friday")
        rebal = sorted(d for d, (p, _) in m["sixty_forty"].items() if p["rebalanced"])
        check(rebal == ["2026-08-03"],
              f"through August the 60/40 rebalanced only at the start ({rebal})")
        p0 = m["sixty_forty"]["2026-08-03"][0]
        check(abs(p0["units_spy"] * spy[0] - 60.0) < 1e-9
              and abs(p0["units_agg"] * agg[0] - 40.0) < 1e-9,
              "at the start it holds 60 of SPY and 40 of AGG")

        # --- C. point-in-time ---------------------------------------------------------
        print(f"\n{LINE}\nC. POINT-IN-TIME, NEVER RECOMPUTED\n{LINE}")
        stored = m["spy"]["2026-08-20"][0]["value"]
        with observations.ObservationStore(obs_db) as st:
            st.write_many([{"registry_key": bz.SPY, "instrument": None,
                            "observed_at": "2026-08-20",
                            "available_at": "2026-09-29T12:00:00+00:00",
                            "value": 999.0, "source": "synthetic",
                            "availability_kind": "observed"}])
            r2 = bz.mark(through="2026-08-31", store=st, register_db=aug_reg)
            m2 = marks(st)
        check(r2["written"] == 0 and m2["spy"]["2026-08-20"][0]["value"] == stored,
              "a later vintage of a close changes no stored mark, and a rerun "
              "writes nothing")
        with observations.ObservationStore(obs_db) as st:
            r3 = bz.mark(through="2026-09-01", store=st, register_db=aug_reg)
            m3 = marks(st)
        check(r3["written"] == 3 and all("2026-09-01" in m3[ld] for ld in bz.LEDGERS),
              f"the next session adds exactly one row per ledger ({r3['written']})")
        sep1 = m3["sixty_forty"]["2026-09-01"][0]
        check(sep1["rebalanced"] is True
              and abs(sep1["units_spy"] * sep1["close_spy"]
                      / sep1["value"] - 0.60) < 1e-9,
              "1 Sep, the first session of the month, rebalances back to 60/40")
        live = m3["spy"]["2026-09-01"][1]
        check(live["availability_kind"] == "ingest_instant"
              and m3["spy"]["2026-08-14"][1]["availability_kind"] == "reconstructed",
              "catch-up rows are labelled reconstructed; the pass's own session "
              "ingest_instant")
        today = session.utc_iso()[:10]
        check(all(str(r["available_at"])[:10] >= today
                  for _, (p, r) in m3["spy"].items()),
              "no available_at is backdated: every mark is stamped when it was "
              "computed")

        # --- D. absence -----------------------------------------------------------------
        print(f"\n{LINE}\nD. ABSENCE\n{LINE}")
        gap_db = str(Path(td) / "gap.db")
        with observations.ObservationStore(gap_db) as st:
            d2 = sessions("2026-09-01", "2026-09-10")
            seed(st, bz.SPY, d2, [600.0] * len(d2))
            seed(st, bz.TBILL, d2, [4.0] * len(d2))
            seed(st, bz.AGG, [d for d in d2 if d != "2026-09-04"],
                 [100.0] * (len(d2) - 1))
            bz.mark(through="2026-09-10", store=st, register_db=empty_reg)
            mg = marks(st)
            ln = bz.line(store=st)
        check("2026-09-04" not in mg["sixty_forty"] and "2026-09-04" in mg["spy"]
              and "2026-09-08" in mg["sixty_forty"],
              "a session without AGG leaves the 60/40 unmarked that day, the other "
              "ledgers marked, and the next session resumes")
        with observations.ObservationStore(str(Path(td) / "none.db")) as st:
            ln0 = bz.line(store=st)
        check(ln0["text"] is None and "has not run" in (ln0["absent_reason"] or ""),
              "with no mark stored the line is absent with its reason, not a zero")

        # --- the line --------------------------------------------------------------------
        with observations.ObservationStore(obs_db) as st:
            ln = bz.line(store=st)
        check(ln["text"].startswith("vs cash +") and " / SPY +" in ln["text"]
              and " / 60-40 " in ln["text"] and "since 2026-08-03" in ln["text"],
              f"the line: {ln['text']}")

        # --- E. wiring -------------------------------------------------------------------
        print(f"\n{LINE}\nE. WIRING\n{LINE}")
        from altdata.sources import yfinance_source as yf
        from altdata import derived
        check(yf.SYMBOLS.get("AGG") == "mkt_agg", "AGG is in the price basket")
        e = derived.registry_entry("yfinance.mkt_agg")
        check(bool(e) and e.get("information_half_life") == "session",
              "and registered through the price block")
        e = derived.registry_entry(bz.KEY)
        check(bool(e) and e.get("revision_policy") == "never"
              and e.get("trigger_eligible") is False,
              "paper.benchmark is registered: never revised, not trigger-eligible")
        sh = (REPO / "scripts" / "run_daily_close.sh").read_text(encoding="utf-8")
        i_px = sh.find("feeds: price pull")
        i_bz = sh.find("altdata.benchmark mark")
        i_rep = sh.find("=== close report start")
        check(0 <= i_px < i_bz < i_rep,
              "the 16:45 pass marks Book Z after its price pull and before the "
              "report")
        from daily_cascade import weekly_payload as wp
        with observations.ObservationStore(obs_db) as st:
            # A week ending TODAY: the marks were computed today, and a Weekly
            # reads Book Z as of its own week's end -- an earlier week could not
            # have known them.
            wk = wp.books_vs_benchmark(session.utc_iso()[:10], st)
        check(set(wk["books"]) == {"A", "B", "C", "D"} and wk["line"]
              and all(v["paper_equity"] is None for v in wk["books"].values()),
              "the Weekly carries the line beside each of Books A-D, whose own "
              "paper equity says not yet sourced")
        from monthly_macro.writer import render_v2
        md = render_v2.register_section({"register_month": {
            "state": "empty", "reason": "r", "window": ["a", "b"],
            "books_vs_benchmark": {"line": ln["text"],
                                   "books": {b: "not yet sourced"
                                             for b in "ABCD"}}}})
        check(md.count(ln["text"]) == 4 and "### Books vs Book Z" in md,
              "the Monthly prints it beside each book")

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
