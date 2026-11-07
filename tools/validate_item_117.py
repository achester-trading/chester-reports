"""
B135 (session B, 6 Nov 2026): signal-triage Batch 22 item 117, the AI
policy-restriction ledger (the order's 99), and section 0's O-2.

  A  THE SCHEMA. The table's columns and vocabularies; a row without a URL, with
     an instrument or stage outside the vocabulary, or a planned_build without its
     project, is refused; every row enters 'proposed'.
  B  APPEND-ONLY. UPDATE and DELETE are refused on the ledger and its reviews; a
     stage change is a new row naming the one it supersedes; a review is written
     once; a duplicate proposal writes nothing.
  C  THE DENOMINATOR AND THE FLAG. No accepted planned_build row: "the flag is not
     computed", never a share; with one, "denominator: n projects, X GW"; enacted
     and accepted restrictions at 10% fire it and 9.9% does not; a proposed or
     superseded row counts toward nothing; a reference row never counts.
  D  THE WRITERS. The news writer proposes a matching title from the voices scan's
     seen items once, classified by the declared keywords, and skips a title
     that does not match; the x-triage writer reads a digest's policy section,
     skipping a line without a URL or outside the vocabulary.
  E  THE SEED AND THE PRINTS. Every seed row has a URL and no person's name; the
     not-written list carries its reasons; the Factor I and VI lines, "no rows
     yet", the reaction column from the store, the close's line only when ON, the
     Weekly's every week, the Monthly's hook, the Themes refresh.
  F  HYGIENE. The config's threshold and review date; the query group sends
     nothing to a search; the gate in the list.

The clock is pinned to GATE_NOW. Synthetic fixtures only: no live store, no
network, no model.

    python tools/validate_item_117.py
"""

from __future__ import annotations

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

from altdata import observations  # noqa: E402
from altdata import policy_restrictions as pr  # noqa: E402

GATE_KIND = "code"
GATE_NOW = "2026-11-06T22:00:00+00:00"

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


def fresh(prefix: str) -> str:
    return str(Path(gate_tmp.mkdtemp(prefix)) / "chester.db")


def R(**kw) -> dict:
    base = {"row_type": "restriction", "jurisdiction": "Texas", "instrument": "executive order",
            "stage": "enacted", "stage_date": "2026-11-05", "title": "a fixture pause",
            "source_url": "https://example.gov/order/1"}
    return {**base, **kw}


def raises(fn, *a, **k) -> str:
    try:
        fn(*a, **k)
    except Exception as exc:                                    # noqa: BLE001
        return str(exc)
    return ""


def group_a() -> None:
    head("A. THE SCHEMA")
    conn = pr.connect(fresh("pr_schema_"))
    cols = [r[1] for r in conn.execute("PRAGMA table_info(policy_restrictions)")]
    check({"jurisdiction", "instrument", "stage", "stage_date", "capacity_mw", "capex_usd",
           "source_url", "status", "supersedes", "row_type", "project"} <= set(cols),
          f"the ledger's columns ({len(cols)})")
    check("URL" in raises(pr.propose, conn, R(source_url=""), "seed")
          and "instrument" in raises(pr.propose, conn, R(instrument="tweet"), "seed")
          and "stage" in raises(pr.propose, conn, R(stage="rumoured"), "seed")
          and "project" in raises(pr.propose, conn, R(row_type="planned_build"), "seed"),
          "no URL, an unknown instrument or stage, a build without its project: refused")
    i = pr.propose(conn, R(), "seed")
    check(conn.execute("SELECT status FROM policy_restrictions WHERE id=?", (i,)).fetchone()[0]
          == "proposed" and pr.rows(conn)[0]["state"] == "proposed",
          "every row enters 'proposed'")
    check("CHECK" in raises(conn.execute, "INSERT INTO policy_restrictions (row_type, "
                            "jurisdiction, instrument, stage, stage_date, title, source_url, "
                            "origin, status, proposed_at) VALUES ('restriction','x',"
                            "'ordinance','enacted','2026-11-05','t','https://a.b','seed',"
                            "'accepted','x')").upper(),
          "a row cannot be inserted already accepted: the review is the only promotion")


def group_b() -> None:
    head("B. APPEND-ONLY")
    conn = pr.connect(fresh("pr_append_"))
    i = pr.propose(conn, R(stage="introduced"), "seed")
    check("append-only" in raises(conn.execute, "UPDATE policy_restrictions SET stage="
                                  "'enacted' WHERE id=?", (i,)),
          "an UPDATE is refused: a stage change is a new row")
    check("never deleted" in raises(conn.execute, "DELETE FROM policy_restrictions"),
          "a DELETE is refused")
    j = pr.propose(conn, R(stage="enacted", supersedes=i), "seed")
    check(j and j != i and pr.rows(conn)[1]["supersedes"] == i,
          "the enacted stage is a new row naming the one it supersedes")
    check(pr.propose(conn, R(stage="enacted", supersedes=i), "seed") is None,
          "the same source, type, stage and jurisdiction twice writes nothing")
    pr.review(conn, [i], "accepted", "the operator")
    check("already reviewed" in raises(pr.review, conn, [i], "rejected", "the operator")
          and "written once" in raises(conn.execute, "UPDATE policy_restriction_reviews "
                                       "SET decision='rejected'")
          and "never deleted" in raises(conn.execute, "DELETE FROM policy_restriction_reviews"),
          "a review is written once, never changed or deleted")
    check("who" in raises(pr.review, conn, [j], "accepted", ""),
          "a review records who made it")


def group_c() -> None:
    head("C. THE DENOMINATOR AND THE FLAG")
    conn = pr.connect(fresh("pr_flag_"))
    f0 = pr.flag(conn)
    check(f0["n_rows"] == 0 and "no rows yet" in pr.flag_line(f0),
          "an empty ledger prints 'no rows yet'")
    r1 = pr.propose(conn, R(capacity_mw=100.0), "seed")
    pr.review(conn, [r1], "accepted", "the operator")
    f1 = pr.flag(conn)
    check(not f1["computed"] and f1["share"] is None
          and "not computed" in pr.flag_line(f1),
          "an enacted restriction with no accepted planned build: not computed, no share")
    b = pr.propose(conn, R(row_type="planned_build", project="Fixture campus",
                           capacity_mw=1000.0, stage="unclassified",
                           instrument="unclassified", source_url="https://example.com/b"),
                   "news_scan")
    f2 = pr.flag(conn)
    check(not f2["computed"], "a proposed planned build is not yet in the denominator")
    pr.review(conn, [b], "accepted", "the operator")
    f3 = pr.flag(conn)
    check(f3["computed"] and abs(f3["share"] - 0.10) < 1e-12 and f3["fired"]
          and "denominator: 1 projects, 1.0 GW" in pr.flag_line(f3)
          and "flag ON" in pr.flag_line(f3),
          f"100 MW of 1,000 MW: 10% fires it ({pr.flag_line(f3)})")
    conn2 = pr.connect(fresh("pr_flag2_"))
    a = pr.propose(conn2, R(capacity_mw=99.0), "seed")
    bb = pr.propose(conn2, R(row_type="planned_build", project="P", capacity_mw=1000.0,
                             source_url="https://example.com/p"), "seed")
    pr.propose(conn2, R(capacity_mw=500.0, source_url="https://example.gov/2"), "seed")
    ref = pr.propose(conn2, R(row_type="reference", capacity_mw=450.0,
                              source_url="https://example.com/ref"), "seed")
    pr.review(conn2, [a, bb, ref], "accepted", "the operator")
    f4 = pr.flag(conn2)
    check(f4["computed"] and not f4["fired"] and abs(f4["share"] - 0.099) < 1e-12,
          "9.9% does not fire; a proposed row and a reference row count toward nothing")
    sup = pr.propose(conn2, R(stage="enacted", capacity_mw=0.0, supersedes=a,
                              jurisdiction="Texas (amended)"), "seed")
    pr.review(conn2, [sup], "accepted", "the operator")
    check(pr.flag(conn2)["enacted"] == 1, "a superseded row no longer counts; its successor does")
    check(pr.config()["flag"]["threshold"] == 0.10
          and pr.config()["flag"]["review_date"] == "2027-02-06",
          "the config carries 10% and its review date, a quarter after the first row")


def group_d() -> None:
    head("D. THE WRITERS")
    db = fresh("pr_news_")
    conn = pr.connect(db)
    vconn = sqlite3.connect(db)
    vconn.row_factory = sqlite3.Row
    vconn.execute("CREATE TABLE voice_scan_seen (source_id TEXT, item_url TEXT, "
                  "first_seen TEXT, status TEXT, published_at TEXT, title TEXT, reason TEXT)")
    items = [("https://news.example/a", "County approves data center moratorium",
              "2026-11-04T15:00:00+00:00"),
             ("https://news.example/b", "Fed holds rates steady", "2026-11-04T16:00:00+00:00"),
             ("https://news.example/c", "Senator introduces AI bill to ban superintelligence",
              "2026-11-05T12:00:00+00:00")]
    vconn.executemany("INSERT INTO voice_scan_seen VALUES ('s', ?, ?, 'extracted', ?, ?, NULL)",
                      [(u, p, p, t) for u, t, p in items])
    vconn.commit()
    ids = pr.propose_from_news(conn, vconn, "2026-11-03")
    rs = {r["source_url"]: r for r in pr.rows(conn)}
    check(len(ids) == 2 and "https://news.example/b" not in rs,
          "two matching titles proposed; the non-matching one skipped")
    a = rs["https://news.example/a"]
    c = rs["https://news.example/c"]
    check((a["instrument"], a["stage"]) == ("ordinance", "enacted")
          and (c["instrument"], c["stage"]) == ("unclassified", "introduced")
          and a["origin"] == "news_scan" and a["state"] == "proposed",
          "classified by the declared keywords, else 'unclassified'; PROPOSED")
    check(pr.propose_from_news(conn, vconn, "2026-11-03") == [],
          "a second run proposes nothing new")
    inbox = Path(gate_tmp.mkdtemp("pr_inbox_"))
    (inbox / "x-digest").mkdir()
    (inbox / "x-digest" / "x-digest-2026-11-05.md").write_text(
        "## 1. Summary\nnothing\n## 4. Policy\n"
        "- https://legis.example/hb1 | Ohio | state statute | passed | 2026-11-05 | HB 1 data-center pause | 1,200\n"
        "- no url here | Ohio | ordinance | enacted | 2026-11-05 | x\n"
        "- https://legis.example/x | Ohio | rumour | enacted | 2026-11-05 | bad vocabulary\n",
        encoding="utf-8")
    # The cutoff is after the file's own copy time (the reader's visibility rule).
    got = pr.propose_from_digests(conn, inbox, "2026-11-01", "2026-11-07",
                                  "2099-01-01T00:00:00+00:00")
    row = next(r for r in pr.rows(conn) if r["id"] == got[0]) if got else {}
    check(len(got) == 1 and row.get("capacity_mw") == 1200.0
          and row.get("origin") == "x_triage" and row.get("stage") == "passed",
          "the digest's policy section: one row proposed, the URL-less and the "
          "out-of-vocabulary lines skipped")


def group_e() -> None:
    head("E. THE SEED AND THE PRINTS")
    cfg = pr.config()
    seeds = cfg["seed"]
    check(seeds and all(re.match(r"https?://", s["source_url"]) for s in seeds)
          and not pr.validate({**seeds[0], "origin": "seed"}),
          f"every seed row carries a URL and validates ({len(seeds)})")
    names = re.compile(r"sanders|casar|hinojosa|abbott|mills|kemp|dewine", re.I)
    text = (REPO / "config" / "policy_restrictions.yaml").read_text(encoding="utf-8")
    check(not names.search(text), "no person's name in the seed or its URLs")
    check(any("Superintelligence" in s["title"] and s["stage"] == "introduced"
              and s["stage_date"] == "2026-09-23" for s in seeds)
          and any(s["row_type"] == "reference" and "45%" in s["title"] for s in seeds),
          "the bill at the introduced stage (23 Sep 2026) and the 45% reference row")
    check(len(cfg["not_written"]) >= 2 and all("source not found" in x["reason"]
                                                for x in cfg["not_written"]),
          "the rows not written, each 'source not found' with its reason")
    db = fresh("pr_seed_")
    # The box's store is already WAL; open it first, as production finds it.
    with observations.ObservationStore(db):
        pass
    conn = pr.connect(db)
    s1, s2 = pr.seed(conn), pr.seed(conn)
    check(len(s1["written"]) == len(seeds) and not s2["written"]
          and len(s2["present"]) == len(seeds), "the seed writes once, PROPOSED")
    lines = pr.factor_lines(conn)
    check(lines[0].startswith("Factor I input, AI policy restrictions (item 117): ")
          and lines[1].startswith("Factor VI (Internal Order)")
          and "not computed" in lines[0],
          "the Factor I and Factor VI input lines")
    empty = pr.connect(fresh("pr_empty_"))
    check(all("no rows yet" in x for x in pr.factor_lines(empty)), "no rows: 'no rows yet'")
    # the reaction column from the store
    rows = []
    for key, vals in (("yfinance.mkt_smh", (100.0, 95.0)), ("yfinance.mkt_gspc", (5000.0, 4950.0))):
        for d, v in zip(("2026-09-22", "2026-09-23"), vals):
            rows.append({"registry_key": key, "instrument": None, "observed_at": d,
                         "available_at": f"{d}T21:00:00+00:00", "value": v,
                         "source": "yfinance", "availability_kind": "observed"})
    with observations.ObservationStore(db) as st:
        st.write_many(rows)
        rx = pr.reaction(st, "2026-09-23")
        tbl = pr.table(conn, st)
        sub = pr.slow_subsection(st, GATE_NOW)
        built = {"narratives": {"items": []}}
        pr.close_extras(built, st)
        wk = {"items": []}
        pr.weekly_narratives(wk, st, GATE_NOW)
    check(abs(rx["semis"] + 5.0) < 1e-9 and abs(rx["spx"] + 1.0) < 1e-9,
          "the reaction column: the one-day move on the stage date, from the store")
    bill = next(r for r in tbl["rows"] if "S. 5493" in r[6])
    check("-5.00%" in bill and "-1.00%" in bill and "not stored" in tbl["rows"][0],
          "the table prints it, 'not stored' where the store holds no close")
    check(sub and sub["paragraph_wanted"] is False and len(sub["lines"]) == 2,
          "the Monthly's sub-section: two lines and the table, no paragraph")
    check(built["narratives"]["items"] == [], "the close prints nothing while the flag is off")
    check(wk["subsections"][0]["lines"][0].startswith("AI policy restrictions (item 117)"),
          "the Weekly prints the flag's line every week")
    from daily_cascade import stack_hooks                       # noqa: PLC0415
    check(stack_hooks.wired("monthly", "slow", "altdata.policy_restrictions",
                            "slow_subsection", ["st", "now"]),
          "the Monthly joins it through its hook file")
    src = {p: (REPO / p).read_text(encoding="utf-8") for p in
           ("daily_cascade/stack.py", "daily_cascade/weekly_stack.py",
            "daily_cascade/themes_block.py", "altdata/sources/voices_scan.py")}
    check("_pr.close_extras(built, st)" in src["daily_cascade/stack.py"]
          and "_pr.weekly_narratives(" in src["daily_cascade/weekly_stack.py"]
          and "pr.slow_subsection(st, now)" in src["daily_cascade/themes_block.py"]
          and '_pr._main(["propose"])' in src["altdata/sources/voices_scan.py"],
          "wired: the close, the Weekly, the Themes refresh, the scan's writers")


def group_f() -> None:
    head("F. HYGIENE")
    g = pr.query_group()
    check(g.get("subject") and g.get("action") and "query" not in g
          and "feeds" not in g, "the query group filters seen titles and sends no search")
    code = (REPO / "altdata" / "policy_restrictions.py").read_text(encoding="utf-8")
    check(not re.search(r"requests|urllib|http_get|import_yfinance|anthropic|model_meter", code),
          "the module fetches nothing and calls no model")
    check("def review" in code and "accept" not in pr.propose.__code__.co_names,
          "only the operator's review promotes a row")
    mk = __import__("gate_list").makefile_text(REPO)
    check("tools/validate_item_117.py" in mk, "the gate is in the list")


def main() -> int:
    pin_clock()
    print(f"the gate's clock is pinned to {GATE_NOW}")
    for gr in (group_a, group_b, group_c, group_d, group_e, group_f):
        try:
            gr()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{gr.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
