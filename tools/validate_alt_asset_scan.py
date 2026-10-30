"""
Validation gate for AQ-7: the alternative-assets quarterly scan -- its prompt,
its config, its standing search list and its ingest (change order of 10 Oct
2026, sections 8, 4.5 and 4.10).

Synthetic scan files only, written to a temporary directory, ingested into a
temporary store. It never reads the live store and never writes docs/ or config/.

  A CONFIG     the agencies section 8 names; the ladder's four rungs; the two
               source hierarchies; the eleven families against the chapters and
               their voices subjects; the four fire dates are Mondays.
  B GAPS       every standing gap's passage is its source's own words, under the
               section it names; ids unique.
  C PROMPT     standalone: the output path, the three parts, the agencies, the
               gaps list, the ladder, both hierarchies, the fire dates, the
               no-status and no-recommendation rules; its word count.
  D PARTS      the three parts (and part 2's four sections) present, or the file
               is refused whole; "Nothing this quarter." stands for an empty one.
  E FIGURES    every stored figure has a source and a date; a row without either,
               without a vintage, from a publisher section 8 does not name, or
               reading as advice is refused; a later vintage of the same period
               is stored as a revision against the prior; Thailand's figures are
               isolated; the Monthly prints each row with its own source.
  F STATUS     a declared status is refused; NEW, REITERATED and INFLECTED are
               computed by the voices register across two quarters' scans.
  G CALENDAR   a calendar entry never lands in config: both calendars unchanged
               byte for byte; the proposals file carries them; an expected date
               is no entry; rumour is flagged and never stored.
  H LADDER     only announced / authorised / funded / implemented; only the last
               two count as demand; authoritative only from the hierarchy.
  I INTAKE     part 3 becomes DRAFT, unnumbered intake entries; the register is
               untouched; a candidate without a definition is refused.
  J ROUTING    altdata.scans.ingest skips the prompt and the generated files and
               routes the scan through its own ingest; the scheduled-tasks row.

    python tools/validate_alt_asset_scan.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import datetime as dt
import hashlib
import os
import re
import sqlite3
import sys
from pathlib import Path

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import gate_tmp                                                # noqa: E402

TMP = Path(gate_tmp.mkdtemp("alt_scan_"))
os.environ["ALTDATA_STORE"] = str(TMP / "csv")

import yaml                                                    # noqa: E402

from altdata import alt_scan, scans, voices                    # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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


# ---------------------------------------------------------------------------
# The synthetic scan
# ---------------------------------------------------------------------------
URL = "https://example.org/fixture"
FIG_HEAD = ("| Publisher | Table | Metric | Period | Value | Unit | Vintage | Published "
            "| Source |\n|---|---|---|---|---|---|---|---|---|")
STORY_HEAD = ("| Family | Voice | Affiliation | Kind | Outlet | Tier | Class | Published "
              "| Subject | Direction | View | Gap | Source |\n"
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|")
LADDER_HEAD = ("| Measure | Body | Rung | Class | Outlet | Published | Source |\n"
               "|---|---|---|---|---|---|---|")
CAL_HEAD = ("| Date | Body | Event | Class | Outlet | Published | Source |\n"
            "|---|---|---|---|---|---|---|")
THAI_HEAD = ("| Date | Body | Event or item | Class | Outlet | Published | Source |\n"
             "|---|---|---|---|---|---|---|")
CAND_HEAD = ("| Candidate | Family | Gap | Definition | Source | Cost | Cadence | Why |\n"
             "|---|---|---|---|---|---|---|---|")


def figs(q: str, steo: str = "104.6") -> list[str]:
    return [
        f"| WGC | Gold Demand Trends by category | Central banks, tonnes | 3Q26 | 220.1 | t "
        f"| GDT Q3 2026 | 2026-10-29 | {URL}/wgc/gdt-q3 |",
        f"| EIA | Short-Term Energy Outlook | World liquids demand | 2027 | {steo} | mb/d "
        f"| STEO {'Dec' if q.endswith('q4') else 'Mar'} | "
        f"{'2026-12-09' if q.endswith('q4') else '2027-03-10'} | {URL}/eia/steo |",
        f"| IMF | COFER | USD share of allocated reserves | 2026Q2 | 56.3 | % "
        f"| COFER 2026Q2 | 2026-09-30 | {URL}/imf/cofer |",
        f"| BoT | Policy rate and statistics | Policy rate | Dec 2026 | 1.50 | % "
        f"| MPC Dec 2026 | 2026-12-17 | {URL}/bot/rate |",
    ]


def stories(direction: str = "bullish", pub: str = "2026-11-12") -> list[str]:
    return [
        f"| metals | Fixture Strategist | Fixture Bank | sell_side | Fixture Wire | 2 "
        f"| commentary | {pub} | gold | {direction} | Gold's official bid holds as "
        f"reserve managers diversify. | cb_unreported_buying | {URL}/story/gold |",
        f"| china | People's Bank of China | PBOC | official | People's Bank of China | 1 "
        f"| authoritative | 2026-11-20 | — | — | The PBOC announced a cut in the "
        f"reserve requirement ratio. | — | {URL}/pboc/rrr |",
        f"| thailand | Bank of Thailand | BoT | official | Bank of Thailand | 2 "
        f"| authoritative | 2026-12-17 | — | — | The MPC held the policy rate. | — "
        f"| {URL}/bot/mpc |",
        f"| china | Anonymous | Unknown | independent | Fixture Forum | 3 | rumour "
        f"| 2026-12-01 | — | — | A stimulus package is said to be coming. | — "
        f"| {URL}/rumour |",
    ]


def scan_text(q: str = "2026q4", read_on: str = "2027-01-04", *, fig_rows=None,
              story_rows=None, ladder_rows=None, cal_rows=None, thai_rows=None,
              cand_rows=None, drop: str = "", story_head: str = STORY_HEAD) -> str:
    fig_rows = figs(q) if fig_rows is None else fig_rows
    story_rows = stories() if story_rows is None else story_rows
    ladder_rows = ([f"| Special bond quota for property | NPC Standing Committee | "
                    f"authorised | authoritative | State Council | 2026-11-08 | "
                    f"{URL}/sc/quota |",
                    f"| Consumer trade-in subsidy | Ministry of Finance | funded | "
                    f"authoritative | Ministry of Finance | 2026-10-15 | {URL}/mof/tradein |"]
                   if ladder_rows is None else ladder_rows)
    cal_rows = ([f"| 2027-03-05 | National People's Congress | annual session opens | "
                 f"authoritative | Xinhua | 2026-12-28 | {URL}/xinhua/npc |"]
                if cal_rows is None else cal_rows)
    thai_rows = ([f"| 2027-02-11 | Bank of Thailand MPC | policy meeting | authoritative "
                  f"| Bank of Thailand | 2026-12-01 | {URL}/bot/calendar |"]
                 if thai_rows is None else thai_rows)
    cand_rows = ([f"| Unreported central-bank gold | metals | china_true_gold | WGC "
                  f"unreported-buying estimate, tonnes a quarter, as published | "
                  f"{URL}/wgc/unreported | free | quarterly | Sizes the official bid "
                  f"the disclosed figures miss. |"]
                 if cand_rows is None else cand_rows)

    def table(h, rows):
        return h + "\n" + "\n".join(rows) if rows else "Nothing this quarter."
    parts = {
        "1": f"## 1. Agency reference tables\n\n{table(FIG_HEAD, fig_rows)}\n",
        "2": (f"## 2. Emerging stories and issues\n\n"
              + ("" if drop == "2a" else
                 f"### 2a. Stories by family\n\n{table(story_head, story_rows)}\n\n")
              + f"### 2b. China: the policy ladder\n\n{table(LADDER_HEAD, ladder_rows)}\n\n"
              + ("" if drop == "2c" else
                 f"### 2c. China: political calendar proposals\n\n"
                 f"{table(CAL_HEAD, cal_rows)}\n\n")
              + f"### 2d. Thailand: items and calendar proposals\n\n"
                f"{table(THAI_HEAD, thai_rows)}\n"),
        "3": f"## 3. Candidate series and analytics\n\n{table(CAND_HEAD, cand_rows)}\n",
    }
    body = "\n".join(v for k, v in parts.items() if k != drop)
    return (f"# Alternative assets — quarterly scan, {alt_scan.quarter_label(q)}\n\n"
            f"**Quarter:** {q}\n**Read on:** {read_on}\n"
            f"**Prompt:** docs/scans/PROMPT-alt-assets-quarterly.md v1.0\n"
            f"**Gaps list:** config/alt_asset_gaps.yaml v1.0\n\n{body}")


def write(name: str, text: str, d: Path = TMP / "scans") -> Path:
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(text, encoding="utf-8", newline="\n")
    return p


def refused_for(p: dict, part: str, needle: str) -> bool:
    return any(r["part"] == part and needle in r["reason"] for r in p["refused"])


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
def group_a(cfg: dict) -> None:
    head("A. THE CONFIG")
    check(list(cfg["agencies"]) == ["WGC", "Silver Institute", "ICSG", "EIA", "IEA",
                                    "OPEC", "IMF", "IIF", "BoT", "NESDC"]
          and [k for k, v in cfg["agencies"].items() if v.get("isolated")]
          == ["BoT", "NESDC"],
          "part 1's publishers are section 8's ten; the BoT's and NESDC's are isolated")
    check(cfg["ladder"] == ["announced", "authorised", "funded", "implemented"]
          and cfg["classes"] == ["authoritative", "commentary", "rumour"],
          "the ladder's four rungs and the three classes of evidence")
    ch, th = cfg["hierarchies"]["china"], cfg["hierarchies"]["thailand"]
    check(all(x in ch for x in ("National Bureau of Statistics", "People's Bank of China",
                                "Ministry of Finance", "SAFE", "General Administration "
                                "of Customs", "State Council"))
          and all(x in th for x in ("Bank of Thailand", "Ministry of Finance", "NESDC",
                                    "Ministry of Commerce", "Customs Department",
                                    "Board of Investment", "Election Commission",
                                    "Parliament", "Royal Thai Government",
                                    "Ministry of Foreign Affairs", "IMF Article IV")),
          "the China hierarchy (section 4.5) and the Thai (section 4.10), body by body")
    from daily_cascade import stack as stack_mod
    chapters = [c["id"] for c in stack_mod.config()["quarterly_chapters"]]
    qc = yaml.safe_load((REPO / "config" / "quarterly_chapters.yaml")
                        .read_text(encoding="utf-8"))["families"]
    declared = set(voices.subjects())
    check(list(cfg["families"]) == chapters
          and all(set(v["subjects"]) <= declared for v in cfg["families"].values())
          and all(cfg["families"][f]["subjects"] == (qc[f].get("voices_subjects") or [])
                  for f in chapters),
          "the eleven families are the chapters, each with the voices subjects its "
          "chapter reads, all declared")
    fires = cfg["fires"]
    check([f["run"] for f in fires] == ["2027-01-04", "2027-04-05", "2027-07-05",
                                       "2027-10-04"]
          and all(dt.date.fromisoformat(f["run"]).weekday() == 0 for f in fires)
          and all((dt.date.fromisoformat(f["edition"])
                   - dt.date.fromisoformat(f["run"])).days == 5 for f in fires)
          and [f["quarter"] for f in fires] == ["2026q4", "2027q1", "2027q2", "2027q3"],
          "it fires the Monday of each edition's week -- 4 Jan, 5 Apr, 5 Jul, 4 Oct "
          "2027 -- for the quarter just ended")


def group_b() -> None:
    head("B. THE STANDING SEARCH LIST")
    g = alt_scan.load_gaps()["gaps"]

    def norm(t: str) -> str:
        return " ".join(t.replace("\\$", "$").replace("**", "").replace("*", "").split())
    bad = []
    for e in g:
        text = (REPO / e["source"]).read_text(encoding="utf-8")
        if norm(e["passage"]) not in norm(text):
            bad.append(f"{e['id']}: passage")
        if e["section"] not in text:
            bad.append(f"{e['id']}: section")
    fams = set(alt_scan.load_config()["families"])
    check(len(g) >= 20 and not bad and len({e["id"] for e in g}) == len(g)
          and all(e["family"] in fams and e.get("search") for e in g),
          f"{len(g)} gaps, each its source's own words under the section it names, "
          f"each with a family and what to search for ({bad[:3]})")
    srcs = {Path(e["source"]).name for e in g}
    check({"metals-whitepaper.md", "energy-whitepaper.md", "currencies-whitepaper.md",
           "digital-assets-whitepaper.md", "credit-whitepaper.md",
           "disruptive-themes-whitepaper.md"} <= srcs,
          "compiled from the family papers and the Disruptive Themes paper's Gaps "
          "Register")


def group_c(cfg: dict) -> int:
    head("C. THE PROMPT")
    p = REPO / "docs" / "scans" / "PROMPT-alt-assets-quarterly.md"
    t = p.read_text(encoding="utf-8")
    body = t.split("\n---\n", 1)[1]
    words = len(body.split())
    need = (["docs/scans/alt-assets-YYYYqN.md", "## 1. Agency reference tables",
             "## 2. Emerging stories and issues", "## 3. Candidate series and analytics",
             "### 2a.", "### 2b.", "### 2c.", "### 2d.", "config/alt_asset_gaps.yaml",
             "config/alt_asset_scan.yaml", "announced", "authorised", "funded",
             "implemented", "Nothing this quarter.", "Mon 4 Jan", "5 Apr", "5 Jul",
             "4 Oct 2027", "IMF's Article IV", "State Council"]
            + list(cfg["agencies"]))
    miss = [x for x in need if x not in t]
    check(not miss, f"the prompt names the file, the three parts and part 2's four "
                    f"sections, the config and the gaps list, the ladder, the ten "
                    f"publishers, both hierarchies and the fire dates ({miss})")
    flat = " ".join(body.split())
    check("No status words" in flat and "No recommendations" in flat
          and "write exactly **one file**" in flat
          and "do not edit `config/china_political_calendar.yaml`" in flat
          and "Do not assign SR numbers" in flat,
          "it forbids a declared status and advice, writes one file, edits no "
          "calendar and numbers no intake entry")
    for col in (FIG_HEAD, STORY_HEAD, LADDER_HEAD, CAL_HEAD, THAI_HEAD, CAND_HEAD):
        if col.split("\n")[0] not in body:
            miss.append(col.split("\n")[0][:40])
    check(not miss, "every table's header in the prompt is the one the ingest reads "
                    "(this gate's fixture uses the same)")
    print(f"        the prompt: {words} words below its line")
    return words


def group_d() -> None:
    head("D. THE THREE PARTS")
    ok = alt_scan.load(write("alt-assets-2026q4.md", scan_text()))
    check(ok["figures"] and ok["stories"] and ok["candidates"],
          "the passing fixture: three parts, part 2's four sections")
    for drop, why in (("1", "part 1"), ("2", "part 2"), ("3", "part 3"),
                      ("2a", "section 2a"), ("2c", "section 2c")):
        p = write(f"alt-assets-2026q4.md", scan_text(drop=drop), TMP / f"drop{drop}")
        try:
            alt_scan.load(p)
            got = None
        except alt_scan.AltScanError as exc:
            got = str(exc)
        check(got and (f"part {drop}" in got or f"section {drop}" in got),
              f"a file without {why} is refused whole ({got and got[:60]})")
    empty = alt_scan.load(write("alt-assets-2026q4.md",
                                scan_text(ladder_rows=[], cand_rows=[]), TMP / "empty"))
    check(not empty["ladder"] and not empty["candidates"],
          "\"Nothing this quarter.\" stands for an empty section or part")
    bad = write("alt-assets-2026q4.md", scan_text().replace("**Read on:** 2027-01-04\n", ""),
                TMP / "noread")
    try:
        alt_scan.load(bad)
        r = None
    except alt_scan.AltScanError as exc:
        r = str(exc)
    check(r and "Read on" in r, "a file with no read-on date is refused")


def group_e(db: str) -> None:
    head("E. FIGURES: SOURCED, DATED, REVISED, ISOLATED")
    p = alt_scan.ingest_store(write("alt-assets-2026q4.md", scan_text()), db)
    conn = sqlite3.connect(db)
    rows = [dict(zip([c[0] for c in conn.execute("SELECT * FROM scan_figures").description], r))
            for r in conn.execute("SELECT * FROM scan_figures")]
    conn.close()
    check(len(rows) == 4 and all(r["source_url"].startswith("https://") and
                                 len(r["as_of"]) == 10 and r["edition"] for r in rows),
          f"every stored figure carries its source URL, its published date and its "
          f"vintage ({len(rows)} stored)")
    cases = [
        ("no source", "| EIA | STEO | Demand | 2027 | 104 | mb/d | STEO Dec | 2026-12-09 | — |",
         "no source URL"),
        ("no date", f"| EIA | STEO | Demand | 2027 | 104 | mb/d | STEO Dec | — | {URL}/x |",
         "no published date"),
        ("no vintage", f"| EIA | STEO | Demand | 2027 | 104 | mb/d | — | 2026-12-09 | {URL}/x |",
         "no vintage"),
        ("an unnamed publisher", f"| Goldman Sachs | Outlook | Gold | 2027 | 4000 | $ "
         f"| Dec | 2026-12-09 | {URL}/x |", "is not one section 8 names"),
        ("advice", f"| IEA | OMR | We prefer longs | 2027 | 1 | — | OMR Dec | 2026-12-09 "
         f"| {URL}/x |", "reads as a recommendation"),
        ("a date after the read", f"| EIA | STEO | Demand | 2027 | 104 | mb/d | STEO Jan "
         f"| 2027-01-12 | {URL}/x |", "after the scan's read"),
    ]
    for why, row, reason in cases:
        q = alt_scan.load(write("alt-assets-2026q4.md", scan_text(fig_rows=[row]),
                                TMP / "e"))
        check(not q["figures"] and refused_for(q, "1", reason),
              f"a figure with {why} is refused: \"{reason}\"")
    again = alt_scan.ingest_store(write("alt-assets-2026q4.md", scan_text()), db)
    check(again["figures_added"] == 0 and again["voices_added"] == 0,
          "a re-ingest of the same scan adds nothing")
    first = {r["metric"]: r for r in rows}
    steo_key = "EIA · Short-Term Energy Outlook · World liquids demand · 2027"
    check(first[steo_key]["comparison"] == "first stored vintage",
          "a figure's first vintage says so")
    q2 = alt_scan.ingest_store(write("alt-assets-2027q1.md",
                                     scan_text("2027q1", "2027-04-05",
                                               fig_rows=figs("2027q1", "104.9"),
                                               story_rows=[], cal_rows=[], thai_rows=[],
                                               ladder_rows=[], cand_rows=[])), db)
    conn = sqlite3.connect(db)
    c = conn.execute("SELECT comparison FROM scan_figures WHERE metric = ? AND read_on = "
                     "'2027-04-05'", (steo_key,)).fetchone()[0]
    c2 = conn.execute("SELECT comparison FROM scan_figures WHERE metric LIKE 'WGC%' AND "
                      "read_on = '2027-04-05'").fetchone()[0]
    conn.close()
    check(c.startswith("revised from 104.6 mb/d (STEO Dec") and c.endswith("+0.3")
          and c2.startswith("unrevised from GDT Q3 2026"),
          f"the next quarter's vintage of the same period is a revision against the "
          f"stored one (\"{c}\"); an unchanged figure says unrevised")
    lat = scans.latest("2027-04-30", db)
    fams = {r["family"] for r in lat}
    lat_all = scans.latest("2027-04-30", db, include_isolated=True)
    check("alt-assets-thailand" not in fams and "alt-assets" in fams
          and any(r["family"] == "alt-assets-thailand" for r in lat_all)
          and len([r for r in lat if r["family"] == "alt-assets"]) == 3
          and all(r["read_on"] == "2027-04-05" for r in lat if r["family"] == "alt-assets"),
          "the BoT's figure is stored under the isolated family, returned only when "
          "asked; the newest read's three figures print together, whatever their "
          "publishers' dates")
    from monthly_macro import stack as ms
    subs, _, _ = ms.sourced_figures("2027-04-30T12:00:00+00:00", db)
    alt = next((s for s in subs if "quarterly scan" in s["title"]), None)
    check(alt and all(URL in row[3] for row in alt["table"]["rows"])
          and alt["table"]["columns"][2] == "Against the prior vintage"
          and not any("bot" in row[3] for row in alt["table"]["rows"]),
          "the Monthly prints each figure with its own source and vintage, the "
          "revision beside it, and no Thai figure")
    _ = (p, q2)


def group_f(db: str) -> None:
    head("F. STATUS: COMPUTED, NEVER DECLARED")
    decl = STORY_HEAD.replace("| Source |\n", "| Status | Source |\n").replace(
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    rows = [r.rsplit("|", 2)[0] + "| NEW |" + r.rsplit("|", 2)[1] + "|"
            for r in stories()]
    q = alt_scan.load(write("alt-assets-2026q4.md", scan_text(story_rows=rows,
                                                               story_head=decl),
                            TMP / "f"))
    check(not q["stories"] and refused_for(q, "2", "declares a status"),
          "a Status column: every row of the table is refused, nothing stored")
    q = alt_scan.load(write("alt-assets-2026q4.md",
                            scan_text(story_rows=[stories()[0].replace(
                                "| cb_unreported_buying |", "| INFLECTED |")]),
                            TMP / "f2"))
    check(not q["stories"] and refused_for(q, "2", "declares a status"),
          "a status word in any cell is refused")
    db2 = str(TMP / "status.db")
    a = alt_scan.ingest_store(write("alt-assets-2026q4.md", scan_text(), TMP / "s1"), db2)
    st = {s["row"]["voice"]: s["status"] for s in a["statuses"]}
    check(st.get("Fixture Strategist") == "NEW" and st.get("People's Bank of China") == "NEW",
          f"the first quarter's voices are NEW, computed by the register ({st})")
    with voices.VoicesStore(db2, readonly=True) as vs:
        stored = vs.rows()
    check(stored and all("status" not in r for r in stored)
          and {r["source_id"] for r in stored} == {"altscan.metals", "china.people-s-bank-of-china"},
          "no stored voices row carries a status; China's reporting is filed under "
          "china.<outlet>, where the chapter reads it")
    same = alt_scan.ingest_store(write("alt-assets-2027q1.md", scan_text(
        "2027q1", "2027-04-05", story_rows=[stories(pub="2027-02-10")[0]
                                            .replace("/story/gold", "/story/gold-2")]),
        TMP / "s2"), db2)
    flip = alt_scan.ingest_store(write("alt-assets-2027q2.md", scan_text(
        "2027q2", "2027-07-05", story_rows=[stories("bearish", "2027-05-10")[0]
                                            .replace("/story/gold", "/story/gold-3")]),
        TMP / "s3"), db2)
    s2 = {s["row"]["voice"]: s for s in same["statuses"]}
    s3 = {s["row"]["voice"]: s for s in flip["statuses"]}
    check(s2["Fixture Strategist"]["status"] == "REITERATED"
          and s3["Fixture Strategist"]["status"] == "INFLECTED"
          and s3["Fixture Strategist"]["subjects"][0].get("was") == "bullish",
          "the same voice the next quarter in the same direction is REITERATED; "
          "turned bearish the quarter after, INFLECTED (was bullish)")


def group_g(db: str) -> None:
    head("G. CALENDARS: PROPOSED, NEVER SEEDED")
    cals = [REPO / "config" / "china_political_calendar.yaml",
            REPO / "config" / "thailand_political_calendar.yaml"]
    before = [sha(c) for c in cals]
    out = TMP / "out"
    p = alt_scan.ingest(write("alt-assets-2026q4.md", scan_text(), TMP / "g"), db,
                        out_dir=out)
    after = [sha(c) for c in cals]
    prop = (out / "proposals-2026q4.md").read_text(encoding="utf-8")
    check(before == after and yaml.safe_load(cals[0].read_text(encoding="utf-8"))
          ["entries"] == [],
          "both political calendars are byte-for-byte unchanged after the ingest; "
          "China's still has no entries")
    check("| 2027-03-05 | National People's Congress | annual session opens |" in prop
          and "Nothing here is seeded" in prop and "| 2027-02-11 |" in prop,
          "the China and Thailand proposals are in docs/scans/proposals-YYYYqN.md, "
          "for the operator to seed by hand")
    src = (REPO / "altdata" / "alt_scan.py").read_text(encoding="utf-8")
    writes = re.findall(r"(\w+)\.write_text\(", src)
    check("political_calendar" not in src
          and writes == ["a", "b"] and "proposals-" in src and "intake-drafts-" in src,
          "the ingest never names either calendar file, and its only file writes are "
          "the proposals and the intake drafts")
    q = alt_scan.load(write("alt-assets-2026q4.md", scan_text(cal_rows=[
        f"| — | Politburo | expected December meeting | commentary | Fixture Wire "
        f"| 2026-11-01 | {URL}/exp |"]), TMP / "g2"))
    check(not q["china_calendar"] and refused_for(q, "2", "expected date is not an entry"),
          "a calendar row without an announced date is refused: an expected date is "
          "no entry")
    with voices.VoicesStore(db, readonly=True) as vs:
        stored = vs.rows()
    check(len(p["rumours"]) == 1 and "RUMOUR" in prop
          and not any("stimulus package" in r["view"] for r in stored),
          "rumour is flagged in the proposals and never stored as a voice")


def group_h() -> None:
    head("H. THE LADDER AND THE HIERARCHY")
    p = alt_scan.load(write("alt-assets-2026q4.md", scan_text(ladder_rows=[
        f"| A measure | State Council | promised | authoritative | State Council "
        f"| 2026-11-01 | {URL}/l |"]), TMP / "h"))
    check(not p["ladder"] and refused_for(p, "2", "is not on the ladder"),
          "a rung outside announced / authorised / funded / implemented is refused")
    p = alt_scan.load(write("alt-assets-2026q4.md", scan_text(), TMP / "h2"))
    md = alt_scan.proposals_md({**p, "statuses": []})
    check("| Special bond quota for property | NPC Standing Committee | authorised | no |" in md
          and "| Consumer trade-in subsidy | Ministry of Finance | funded | yes |" in md,
          "each measure on its rung; only funded and implemented count as demand")
    p = alt_scan.load(write("alt-assets-2026q4.md", scan_text(story_rows=[
        stories()[1].replace("| official | People's Bank of China |",
                             "| official | Fixture Wire |")]), TMP / "h3"))
    check(not p["stories"] and refused_for(p, "2", "is not on the china source hierarchy"),
          "\"authoritative\" from an outlet off the China hierarchy is refused")
    p = alt_scan.load(write("alt-assets-2026q4.md", scan_text(thai_rows=[
        f"| — | A columnist | the coalition is fragile | authoritative | Fixture Daily "
        f"| 2026-12-01 | {URL}/t |"]), TMP / "h4"))
    check(refused_for(p, "2", "is not on the thailand source hierarchy"),
          "and off the Thai hierarchy")
    p = alt_scan.load(write("alt-assets-2026q4.md", scan_text(), TMP / "h5"))
    check(not any(s["family"] == "thailand" for s in p["stories"])
          and any(t.get("voice") == "Bank of Thailand" for t in p["thailand"]),
          "Thailand's story is never a voices row; it goes to the proposals only")


def group_i(db: str) -> None:
    head("I. CANDIDATES: DRAFT INTAKE ENTRIES")
    reg = REPO / "docs" / "signal-triage-register.md"
    before = sha(reg)
    out = TMP / "out_i"
    alt_scan.ingest(write("alt-assets-2026q4.md", scan_text(), TMP / "i"), db, out_dir=out)
    d = (out / "intake-drafts-2026q4.md").read_text(encoding="utf-8")
    check(sha(reg) == before and "### SR-? (DRAFT) Unreported central-bank gold" in d
          and "DRAFT — not filed; numbered at ruling" in d
          and "china_true_gold" in d and not re.search(r"### SR-\d", d),
          "a candidate becomes an unnumbered DRAFT entry on the intake template; the "
          "register is untouched")
    p = alt_scan.load(write("alt-assets-2026q4.md", scan_text(cand_rows=[
        f"| A series | metals | — | — | {URL}/c | free | monthly | Because. |"]), TMP / "i2"))
    check(not p["candidates"] and refused_for(p, "3", "the definition rule"),
          "a candidate without its definition is refused")
    p = alt_scan.load(write("alt-assets-2026q4.md", scan_text(cand_rows=[
        f"| A series | metals | no_such_gap | ratio of a to b, monthly | {URL}/c | free "
        f"| monthly | Because. |"]), TMP / "i3"))
    check(refused_for(p, "3", "is not in config/alt_asset_gaps.yaml"),
          "a candidate naming a gap the list does not hold is refused")


def group_j() -> None:
    head("J. ROUTING AND THE SCHEDULED TASK")
    d = TMP / "route"
    write("alt-assets-2026q4.md", scan_text(), d)
    write("PROMPT-alt-assets-quarterly.md", "# a prompt\n", d)
    write("proposals-2026q4.md", "# proposals\n", d)
    write("intake-drafts-2026q4.md", "# drafts\n", d)
    saved = scans.SCANS_DIR
    scans.SCANS_DIR = d
    try:
        out = scans.ingest(db_path=str(TMP / "route.db"))
    finally:
        scans.SCANS_DIR = saved
    check([s["scan_id"] for s in out["scans"]] == ["alt-assets-2026q4"]
          and out["added"] == 4 and out["scans"][0]["voices"] == 2
          and not any("reference-table" in r["reason"] for r in out["refused"]),
          "altdata.scans.ingest skips the prompt and the generated files and stores "
          "the scan's figures and voices through its own ingest")
    t = (REPO / "docs" / "scheduled-tasks.md").read_text(encoding="utf-8")
    row = next((ln for ln in t.splitlines()
                if ln.startswith("| Alternative assets — quarterly scan |")), "")
    check(row and "docs/scans/alt-assets-YYYYqN.md" in row and "operator creates it" in row
          and "PROMPT-alt-assets-quarterly.md" in row and "4 Jan" in row,
          "docs/scheduled-tasks.md carries the task's row: cadence, what it reads and "
          "writes, and that the operator creates it")


def main() -> int:
    print(f"{LINE}\nAQ-7 -- the alternative-assets quarterly scan (synthetic)\n{LINE}")
    cfg = alt_scan.load_config()
    group_a(cfg)
    group_b()
    words = group_c(cfg)
    group_d()
    db = str(TMP / "store.db")
    group_e(db)
    group_f(db)
    group_g(str(TMP / "g.db"))
    group_h()
    group_i(str(TMP / "i.db"))
    group_j()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed (the prompt: {words} words)\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
