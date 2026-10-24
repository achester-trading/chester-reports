"""
Signal triage Batch 14, Part B2 (b55, session B): items 62, 67 and 68.

  A  THE SHELF. HSBC AM's Capital Market Assumptions and Vanguard's Capital
     Markets Model forecasts are on docs/reading/watchlist.json in the existing
     schema (every key its neighbours carry, a declared group and depth, months
     and a window), and the Reading chapter's due list names them.
  B  ITEM 62, THE CMA TABLE. Fixture CMA scans ingested by the scans ingest
     into a scratch store, each row with its own URL, idempotently; the median,
     the high less low and the count by hand; an edition older than 15 months
     dropped and counted; a house with nothing stored printing "no edition
     stored"; a scan not yet read at the cutoff not counted; the real scans
     directory carrying no CMA edition, so nothing is recalled.
  C  PLACEMENT. The Monthly's slow layers carry the table (its read first, as a
     lead, then the table, then each edition's line) and the CMA families are
     left out of the sourced figures so each figure prints once; item 30's Book
     A line reads the median, and says "no CMA edition stored" otherwise, and
     reads no store it was not given.
  D  ITEM 67, PEG AND LTEG. No PEG or LTEG value anywhere: no key, no source;
     the one listed-gap line closes every branch of item 60's lines.
  E  THE LTEG NOTE. Every claim carries a title and a URL; the 2021 figure is
     not written because no citation was found; every percentage sits in a
     paragraph with a source URL.
  F  THE PROPOSAL. "The market is cheap on PEG" validates, carries its caveat
     (the inflated long-term growth denominator), resolves on a registered
     metric, and seeds into a scratch register as PROPOSED, origin
     config_proposal.
  G  ITEM 68, THE PER-HOUSEHOLD LINE. Redfin's pending sales over the Census
     household estimates, per 1,000 households, by hand, with the latest
     estimate carried forward; its dual percentiles by hand; printed after the
     raw level; absent with its reason when the households are not stored.
  H  THE DATED APPENDIX. NAR's 66.0 print, dated 20 Oct 2026, with its source
     line, at the end of the queue.
  I  HYGIENE. The new key is registered and pulled; the new modules write no
     store, read no vendor value or by-hand key, import no composite or
     market-state object; no person's name, handle or email in the new code,
     config, note, proposal or appendix lines.

Synthetic fixtures only: no live store, no network, no model.

    python tools/validate_batch14_b2.py
"""

from __future__ import annotations

import json
import re
import sqlite3
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gate_tmp  # noqa: E402
import yaml  # noqa: E402

from altdata import cma_table as cma  # noqa: E402
from altdata import observations, scans  # noqa: E402

PASS = FAIL = 0
LINE = "=" * 78
NOW = "2026-10-31T23:00:00+00:00"
FIX = REPO / "tests" / "fixtures" / "batch14_b2"
NOTE = REPO / "docs" / "base-rate-notes" / "lteg-overshoot-2026-10.md"


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


def scratch(prefix: str) -> str:
    return str(Path(gate_tmp.mkdtemp(prefix)) / "chester.db")


def cma_db() -> str:
    db = scratch("b14b2cma_")
    scans.ingest(sorted(FIX.glob("cma-*.md")), db)
    return db


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE SHELF")
    wl = json.loads((REPO / "docs" / "reading" / "watchlist.json").read_text(encoding="utf-8"))
    items = {i["id"]: i for i in wl["items"]}
    ref = items["jpm-ltcma"]
    for wid in ("hsbc-cma", "vanguard-vcmm"):
        it = items.get(wid)
        check(it is not None, f"{wid} is on the shelf")
        if not it:
            continue
        check(set(ref) <= set(it) and it["group"] in wl["groups"]
              and it["depth"] in ("deep", "skim", "list")
              and str(it["index_url"]).startswith("https://")
              and isinstance(it["expected"], dict) and it["expected"].get("months")
              and it["expected"].get("window"),
              f"{wid} carries the schema's keys, a declared group and depth, an https "
              f"index page, months and a window ({it['cadence']})")
    check(items["hsbc-cma"]["expected"]["months"] == [10]
          and items["vanguard-vcmm"]["expected"]["months"] == [1, 4, 7, 10],
          "the cadences from the source checks: HSBC annual in October, Vanguard at "
          "least quarterly (each quarter-end run)")
    from monthly_macro import reading
    due = {d["publication"] for d in reading.due(wl, "2026-09-20")}
    check(items["hsbc-cma"]["publication"] in due
          and items["vanguard-vcmm"]["publication"] in due,
          "the Reading chapter's due list names both before an October Monthly")
    check(not any("Vanguard outlooks," in s for s in wl["not_on_the_shelf"]),
          "the not-on-the-shelf note no longer excludes Vanguard's model forecasts")


def group_b() -> None:
    head("B. ITEM 62, THE CMA TABLE")
    db = cma_db()
    conn = sqlite3.connect(db)
    rows = conn.execute("SELECT family, metric, value, source_url FROM scan_figures "
                        "ORDER BY id").fetchall()
    fams = {r[0] for r in rows}
    check(fams == {"cma-hsbc", "cma-vanguard", "cma-aqr", "cma-gmo"} and len(rows) == 36,
          f"four fixture editions ingested as sourced figures, nine rows each ({len(rows)})")
    us = [r for r in rows if r[0] == "cma-hsbc" and r[1] == "US equity"][0]
    check(us[3] == "https://example.org/fixture/hsbc-cma#0",
          "a row's own source URL is stored, not the header's")
    again = scans.ingest(sorted(FIX.glob("cma-*.md")), db)
    check(again["added"] == 0, "a re-ingest adds nothing")
    conn.close()

    r = cma.read(NOW, db)
    st = {h["id"]: h["state"] for h in r["houses"]}
    check(st == {"jpm": "none", "aqr": "current", "gmo": "stale", "ra": "none",
                 "hsbc": "current", "vanguard": "current"},
          f"three current, GMO's March 2025 edition stale at a 31 Oct 2026 cutoff "
          f"(floor {r['floor']}), two with nothing stored ({st})")
    check(r["floor"] == "2025-07-31" and r["dropped"] == ["gmo"] and r["current"] == 3,
          "the 15-month floor is 31 Jul 2025 and the drop is counted")
    a = {x["id"]: x for x in r["assets"]}
    us_vals = [5.0, 4.0, 4.6]
    em_vals = [8.0, 7.0, 6.4]
    check(a["us_equity"]["median"] == statistics.median(us_vals) == 4.6
          and a["us_equity"]["dispersion"] == round(max(us_vals) - min(us_vals), 2) == 1.0
          and a["us_equity"]["n"] == 3,
          "US equity: median of 5.0, 4.0, 4.6 is 4.6; high less low 1.0; n=3 (GMO's "
          "-1.0 dropped)")
    check(a["em_equity"]["median"] == 7.0 and a["em_equity"]["dispersion"] == 1.6,
          "EM equity: median 7.0, high less low 1.6 (8.0 - 6.4)")
    check(a["sixty_forty"]["median"] == 4.5 and a["sixty_forty"]["n"] == 3,
          "60/40: median of 5.0, 4.4, 4.5 is 4.5")
    t = cma.table(r)
    jpm_col = t["columns"].index("JPM")
    gmo_col = t["columns"].index("GMO")
    check(all(row[jpm_col] == "no edition stored" for row in t["rows"])
          and all(row[gmo_col] == "dropped (stale)" for row in t["rows"])
          and t["rows"][0][-3:] == ["4.6%", "1.0 pp", "3"],
          "the table: JPM 'no edition stored', GMO 'dropped (stale)', US equity's "
          "median, spread and count")
    lead = cma.lead(r)
    check("3 of 6 houses" in lead and "1 dropped" in lead and "+2.0 pp" in lead
          and "no conversion" in lead,
          f"the read names the count, the drop and the ex-US gap (6.6 less 4.6) "
          f"({lead[:90]}...)")
    ed = cma.edition_lines(r)
    check(any(l.startswith("J.P. Morgan AM") and "no edition stored" in l for l in ed)
          and any("5 to 10 years; real" in l for l in ed)
          and any("Dropped: older than 15 months" in l for l in ed),
          "each edition line carries its horizon and basis; the stale one says why")
    early = cma.read("2026-10-15T12:00:00+00:00", db)
    check({h["id"]: h["state"] for h in early["houses"]}["vanguard"] == "none",
          "an edition read after the cutoff (Vanguard's, read 20 Oct) is not counted at 15 Oct")
    live = list(scans.SCANS_DIR.glob("cma-*.md"))
    check(not live, "docs/scans carries no CMA edition yet: every house prints 'no "
                    "edition stored' until the watch writes one")
    empty = cma.read(NOW, scratch("b14b2empty_"))
    check(empty["current"] == 0 and len(empty["missing"]) == 6
          and "no median prints" in cma.lead(empty),
          "an empty store: six houses with nothing stored, no median")


def group_c() -> None:
    head("C. PLACEMENT")
    db = cma_db()
    from daily_cascade import batch14_b2_block as blk
    sub = blk.slow_subsection(NOW, db)
    check(sub and sub["lead"].startswith("3 of 6 houses") and sub["table"]["rows"]
          and len(sub["lines"]) == 6 and sub["paragraph_wanted"] is False,
          "the slow sub-section: its read as a lead (before the table), the table, "
          "six edition lines, no paragraph")
    ms = (REPO / "monthly_macro" / "stack.py").read_text(encoding="utf-8")
    check("batch14_b2_block.slow_subsection(now, db_path)" in ms
          and 'not str(r["family"]).startswith("cma-")' in ms,
          "the Monthly's slow layers carry it, and the sourced figures leave the CMA "
          "families out")
    from monthly_macro import stack
    subs, _items, _data = stack.sourced_figures(NOW, db)
    check(not any("Fixture CMA" in str(s.get("title")) for s in subs),
          "no CMA edition prints again among the sourced figures")
    r = cma.read(NOW, db)
    line = cma.book_a_line(r)
    check("4.6%" in line and "n=3 houses" in line and "report only" in line,
          f"item 30's Book A line reads the US-equity median ({line})")
    check(cma.book_a_line(None).endswith("no CMA edition stored.")
          and cma.book_a_line(cma.read(NOW, scratch("b14b2e2_"))).endswith(
              "no CMA edition stored."),
          "and says 'no CMA edition stored' otherwise")

    class NoPath:
        pass
    check(blk.book_a_line(NoPath(), NOW).endswith("no CMA edition stored."),
          "given a store without a path, it reads nothing (never the default database)")
    obs_db = scratch("b14b2obs_")
    with observations.ObservationStore(obs_db) as st:
        pass
    from daily_cascade import index_carry_block as icb
    with observations.ObservationStore(obs_db) as st:
        sub2 = icb.positioning_subsection(st, NOW)
    check(sub2 and sub2["lines"][-1].startswith("Book A long-horizon expected return"),
          "the allocation block prints the Book A line last")


def group_d() -> None:
    head("D. ITEM 67, PEG AND LTEG")
    from altdata import eps_overshoot as eo
    want = "PEG and long-term growth: no keyless source; see the LTEG overshoot note."
    src = (REPO / "altdata" / "eps_overshoot.py").read_text(encoding="utf-8")
    check(eo.PEG_GAP == want and "docs/base-rate-notes/lteg-overshoot-2026-10.md" in src,
          "the listed-gap line, as the paste words it; the module names the note's path")
    gap = eo.read(None, NOW, "on")
    check(eo.lines(gap)[-1] == want and eo.lines({"state": "absent", "source": "x"})[-1] == want,
          "it closes every branch of item 60's lines")
    icb = (REPO / "daily_cascade" / "index_carry_block.py").read_text(encoding="utf-8")
    check("eo.lines(eo.read(" in icb, "item 60's block prints those lines")
    cfg = yaml.safe_load((REPO / "config" / "eps_overshoot.yaml").read_text(encoding="utf-8"))
    reg = (REPO / "metrics_registry.yaml").read_text(encoding="utf-8")
    check(not any(re.search(r"peg|lteg", str(k), re.I) for k in cfg)
          and not re.search(r"^\s+[a-z_.]*\b(peg|lteg)\w*:", reg, re.I | re.M)
          and not NOTE.read_text(encoding="utf-8").count("PEG is 0.")
          and NOTE.exists() and (REPO / "docs" / "base-rate-notes").is_dir(),
          "no PEG or LTEG key, source or value anywhere (F3)")


def group_e() -> None:
    head("E. THE LTEG NOTE")
    t = NOTE.read_text(encoding="utf-8")
    paras = [p for p in re.split(r"\n\s*\n", t)]
    claims = [p for p in paras if re.match(r"\s*(\d\.|- \*\*20)", p)]
    check(len(claims) == 5, f"three studies and two peaks ({len(claims)})")
    cited = [p for p in claims if "Source:" in p and re.search(r"https?://\S+", p)
             and re.search(r"\"[^\"]{10,}\"", p)]
    not_written = [p for p in claims if "Not written" in p]
    check(len(cited) == 4 and len(not_written) == 1 and "2021" in not_written[0],
          "every claim carries a quoted title and a URL; 2021 is 'Not written' for want "
          "of a citation")
    figs = [p for p in paras if re.search(r"\d+(?:\.\d+)?%", p)]
    check(figs and all(re.search(r"https?://", p) for p in figs),
          "every percentage sits in a paragraph with its source URL")
    for url in ("https://doi.org/10.1111/1540-6261.00540",
                "https://doi.org/10.1111/j.1540-6261.1996.tb05223.x",
                "https://doi.org/10.1086/727713"):
        check(url in t, f"cited: {url}")


def group_f() -> None:
    head("F. THE PROPOSAL")
    from altdata import derived
    from altdata import narratives as nar
    cfg = yaml.safe_load((REPO / "config" / "narratives.yaml").read_text(encoding="utf-8"))
    spec = cfg["proposals"]["market_cheap_on_peg"]
    check(nar.validate_config_story("market_cheap_on_peg", spec) == [],
          "the entry validates as a config proposal")
    d = " ".join(str(spec["direction"]).split())
    check("inflated long-term growth estimate" in d and "lteg-overshoot" in d,
          "its caveat is in the text: the denominator is an inflated long-term growth "
          "estimate, with the note")
    check(all(derived.registry_entry(m) for m in spec["implied_outcome"]["metrics"])
          and spec["implied_outcome"]["horizon_days"] == 182,
          "its outcome resolves on a registered metric, two quarters on")
    check("chart-house" in str(spec["proposed_by"]), "the source is a chart-house post, tagged")
    db = scratch("b14b2nar_")
    with nar.NarrativeRegister(db) as reg:
        reg.seed({"version": cfg.get("version"), "narratives": {},
                  "proposals": {"market_cheap_on_peg": spec}})
    row = sqlite3.connect(db).execute(
        "SELECT status, origin, state FROM narratives "
        "WHERE narrative_id='market_cheap_on_peg'").fetchone()
    check(row == ("proposed", "config_proposal", "emerging"),
          f"seeded PROPOSED through the existing path ({row}); confirming stays the operator's")
    check(len(cfg["proposals"]) == 7, "the proposals pin is seven")


def months(y0: int, m0: int, n: int) -> list[str]:
    out = []
    y, m = y0, m0
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}-01")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def group_g() -> None:
    head("G. ITEM 68, THE PER-HOUSEHOLD LINE")
    from altdata import st_r5_rates as rt
    ms = months(2019, 1, 93)                    # Jan 2019 .. Sep 2026
    pend = [(d, 400000.0 - 1000.0 * i) for i, d in enumerate(ms)]
    hh = [("2018-12-01", 128000.0), ("2023-01-01", 131000.0), ("2026-06-01", 133971.0)]
    rows = ([("redfin.pending_sales", d, v) for d, v in pend]
            + [("fred.households", d, v) for d, v in hh])
    db = scratch("b14b2hh_")
    with observations.ObservationStore(db) as st:
        st.write_many([{"registry_key": k, "instrument": None, "observed_at": d,
                        "available_at": d + "T21:00:00+00:00", "value": v,
                        "source": "fixture"} for k, d, v in rows])
    with observations.ObservationStore(db) as st:
        h = rt.housing(st, NOW)
        ph = h["per_household"]
        want = round(308000.0 / 133971.0, 4)
        check(not ph["absent"] and ph["month"] == "2026-09-01" and ph["value"] == want
              and ph["households_k"] == 133971.0 and ph["households_as_of"] == "2026-06-01",
              f"Sep 2026: 308,000 over 133,971 thousand = {want} per 1,000 households, the "
              f"June estimate carried forward")
        mid = rt.per_household(pend, hh)
        check(dict(mid)["2022-12-01"] == round((400000.0 - 1000.0 * 47) / 128000.0, 4)
              and dict(mid)["2023-01-01"] == round((400000.0 - 1000.0 * 48) / 131000.0, 4),
              "each month takes the latest estimate on or before it (Dec 2022 on the 2018 "
              "estimate, Jan 2023 on the new one)")
        lz = ph["lens"]
        check(lz["n_window"] == 60 and lz["percentile_window"] == round(100.0 / 60, 4)
              and lz["n_full"] == 93 and lz["percentile_full"] == round(100.0 / 93, 4)
              and not lz["same"],
              "dual percentiles by hand: the series' low, 1 of 60 over five years and 1 of "
              "93 over the stored history")
        ls = rt.housing_lines(h)
        i_raw = next(i for i, l in enumerate(ls) if l.startswith("Pending home sales"))
        check(ls[i_raw + 1].startswith("Pending sales per 1,000 households (Redfin over "
                                       "the Census household estimates via FRED, "
                                       "single-source, September 2026): 2.30"),
              f"printed beside the raw level, labelled single-source ({ls[i_raw + 1][:80]})")
    db2 = scratch("b14b2hh2_")
    with observations.ObservationStore(db2) as st:
        st.write_many([{"registry_key": "redfin.pending_sales", "instrument": None,
                        "observed_at": d, "available_at": d + "T21:00:00+00:00",
                        "value": v, "source": "fixture"} for d, v in pend])
    with observations.ObservationStore(db2) as st:
        h2 = rt.housing(st, NOW)
        line = rt.per_household_line(h2["per_household"], "September 2026")
    check(h2["per_household"]["absent"] and "TTLHHM156N" in line and "not read" in line,
          "without the households: 'not read' with its reason")


def group_h() -> None:
    head("H. THE DATED APPENDIX")
    q = (REPO / "docs" / "dated-appendix-queue.md").read_text(encoding="utf-8")
    tail = q.split("(Batch 14 item 68)")[-1]
    check("(Batch 14 item 68)" in q and "Dated 20 Oct 2026" in tail and "66.0" in tail
          and "7.3%" in tail and "11.3%" in tail
          and "https://www.nar.realtor/newsroom/pending-home-sales-decreased-7-3-percent-in-september"
          in tail,
          "NAR's 66.0 print, dated, with its source line")
    # Appended at the end when b55 wrote it; later branches append after it (the
    # chain-6 stitch), so the check is that it follows every earlier entry.
    sec = q.index("(Batch 14 item 68)")
    check(sec > q.index("(Batch 14 item 63)")
          and "pending-home-sales-decreased-7-3-percent-in-september" in q[sec:],
          "appended after the entries before it, its source line inside its section")


def group_i() -> None:
    head("I. HYGIENE")
    from altdata import config as acfg
    from altdata import derived
    check(derived.registry_entry("fred.households") is not None
          and any(s.key == "households" and s.fred_id == "TTLHHM156N"
                  for s in acfg.FRED_PULL_SERIES),
          "the new key, fred.households (TTLHHM156N), is registered and pulled")
    code = [REPO / "altdata" / "cma_table.py", REPO / "daily_cascade" / "batch14_b2_block.py"]
    src = "\n".join(p.read_text(encoding="utf-8") for p in code)
    imports = "\n".join(l for l in src.splitlines() if re.match(r"\s*(from|import)\s", l))
    check(not re.search(r"\.write\(|write_many|INSERT|ingest\(", src)
          and "manual_input" not in src and "vendor" not in src
          and not re.search(r"regime|market_state|composite|manual_input|register", imports),
          "the new modules write no store, read no vendor value or by-hand key, and import "
          "no composite, market-state object or register")
    nar_txt = (REPO / "config" / "narratives.yaml").read_text(encoding="utf-8")
    queue = (REPO / "docs" / "dated-appendix-queue.md").read_text(encoding="utf-8")
    mine = "\n".join([
        src, (REPO / "config" / "cma_table.yaml").read_text(encoding="utf-8"),
        NOTE.read_text(encoding="utf-8"),
        nar_txt.split("market_cheap_on_peg:")[1],
        queue.split("(Batch 14 item 68)")[1],
        "\n".join(p.read_text(encoding="utf-8") for p in FIX.glob("*.md"))])
    people = (r"Joe Little|Monchau|Gerli|Yardeni|Varghese|Lemand|Declercq|Bilello|"
              r"Bradshaw|Nobler|Lamont|Karceski|Lakonishok|La Porta|Bordalo|Gennaioli|"
              r"Shleifer|Lawrence Yun|Owenomics")
    check(not re.search(people, mine), "no person's name in the new code, config, note, "
                                       "proposal or appendix lines")
    check(not re.search(r"(?<![\w.])@[A-Za-z_]\w+|[\w.+-]+@[\w-]+\.[\w.]+", mine),
          "no handle and no email address")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h,
              group_i):
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
