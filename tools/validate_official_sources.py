"""
Validation gate for the published-file writers of the signal-triage order (ST-1).

    python tools/validate_official_sources.py

No network and no box: every fetch is replaced with an in-memory fixture, and
every write goes to a temporary observation store. The verdict is therefore the
same on a CI runner as on the laptop.

  A  THE PARSERS. ACM's daily sheet, the SF Fed workbook (built here as a real
     .xlsx and read through the stdlib reader) and the DKW CSV with its preamble
     produce the rows, keys, dates and UNITS they claim -- SF Fed's fractions
     arrive in the store as percent.
  B  A CHANGED SHAPE IS A FAILURE. A missing column raises, and a run over it
     returns STALE having written nothing.
  C  STALE, NOT EMPTY. With good rows already stored, a fetch failure returns
     STALE, writes zero rows, leaves every stored vintage in place, and reports
     the newest observed date it kept.
  D  IDENTITY AND TIME (30.2(a)). Every row carries the run's run_id;
     available_at is canonical microsecond UTC; Last-Modified becomes `observed`
     and its absence `ingest_instant`; a row dated after today's session is
     refused and nothing is written.
  E  A RE-READ IS NOT A REVISION, AND THE WINDOW HOLDS. A second identical pull
     writes zero rows; a re-estimated value inside the window is a new vintage;
     one outside it, after the backfill, is not written.
  F  REGISTERED. Every key has a metrics entry with the 26.4 fields and the
     rates_decomposition group; every source is in source_registry.yaml and its
     implemented_by file exists.
  G  WIRED, AND NOWHERE ELSE. The writers run as the `official` feed and sit in
     the freshness roster; no systemd unit was added for them; no report module,
     renderer or regime code imports them (30.4: reports never fetch).
"""

from __future__ import annotations

import datetime as dt
import io
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_TMP = tempfile.mkdtemp(prefix="validate_official_")
os.environ.setdefault("CHESTER_STATE_DIR", _TMP)

import yaml  # noqa: E402

from altdata import feeds, observations, session  # noqa: E402
from altdata.sources import _publication as pub  # noqa: E402
from altdata.sources import acm, dkw, sffed  # noqa: E402
from altdata.sources._base import FetchError  # noqa: E402

PASS = 0
FAIL = 0
LINE = "=" * 78

LM_HEADERS = {"last-modified": "Fri, 04 Sep 2026 14:00:17 GMT"}
LM_CANON = "2026-09-04T14:00:17.000000+00:00"


def ok(m: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    ok(m) if c else bad(m)


def temp_store() -> observations.ObservationStore:
    fd, path = tempfile.mkstemp(suffix=".sqlite", dir=_TMP)
    os.close(fd)
    os.unlink(path)
    return observations.ObservationStore(path)


def count(db, key=None) -> int:
    if key:
        return db.conn.execute("SELECT COUNT(*) FROM observations "
                               "WHERE registry_key=?", (key,)).fetchone()[0]
    return db.conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def acm_table(dates: list[str]) -> list[list]:
    header = ["DATE"] + [f"ACMY{i:02d}" for i in range(1, 11)] \
        + [f"ACMTP{i:02d}" for i in range(1, 11)] \
        + [f"ACMRNY{i:02d}" for i in range(1, 11)]
    rows = [header]
    for n, d in enumerate(dates):
        day = dt.date.fromisoformat(d).strftime("%d-%b-%Y")
        y = [4.0 + i / 10 + n / 100 for i in range(10)]
        tp = [0.1 * i + n / 100 for i in range(1, 11)]
        rny = [a - b for a, b in zip(y, tp)]
        rows.append([day] + y + tp + rny)
    return rows


def _xlsx(sheets: dict[str, list[list]]) -> bytes:
    """A real, minimal .xlsx: shared strings for text, numbers inline."""
    strings: list[str] = []

    def sidx(s: str) -> int:
        if s not in strings:
            strings.append(s)
        return strings.index(s)

    def col(i: int) -> str:
        s = ""
        i += 1
        while i:
            i, r = divmod(i - 1, 26)
            s = chr(65 + r) + s
        return s

    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    sheet_xml = []
    for rows in sheets.values():
        body = []
        for ri, row in enumerate(rows, start=1):
            cells = []
            for ci, v in enumerate(row):
                ref = f"{col(ci)}{ri}"
                if isinstance(v, str):
                    cells.append(f'<c r="{ref}" t="s"><v>{sidx(v)}</v></c>')
                elif v is not None:
                    cells.append(f'<c r="{ref}"><v>{v}</v></c>')
            body.append(f'<row r="{ri}">{"".join(cells)}</row>')
        sheet_xml.append(f'<worksheet xmlns="{ns}"><sheetData>{"".join(body)}'
                         f'</sheetData></worksheet>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        names = list(sheets)
        z.writestr("xl/workbook.xml",
                   f'<workbook xmlns="{ns}" xmlns:r="{rns}"><sheets>'
                   + "".join(f'<sheet name="{n}" sheetId="{i+1}" r:id="rId{i+1}"/>'
                             for i, n in enumerate(names))
                   + "</sheets></workbook>")
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<Relationships xmlns="http://schemas.openxmlformats.org/'
                   'package/2006/relationships">'
                   + "".join(f'<Relationship Id="rId{i+1}" Target="worksheets/'
                             f'sheet{i+1}.xml" Type="x"/>' for i in range(len(names)))
                   + "</Relationships>")
        for i, xml in enumerate(sheet_xml):
            z.writestr(f"xl/worksheets/sheet{i+1}.xml", xml)
        z.writestr("xl/sharedStrings.xml",
                   f'<sst xmlns="{ns}">'
                   + "".join(f"<si><t>{s}</t></si>" for s in strings) + "</sst>")
    return buf.getvalue()


def serial(d: str) -> int:
    return (dt.date.fromisoformat(d) - dt.date(1899, 12, 30)).days


def sffed_xlsx(dates: list[str]) -> bytes:
    def sheet(prefix: str, base: float) -> list[list]:
        rows = [["DATE"] + [f"{prefix}{i:02d}YR" for i in range(1, 11)]]
        for n, d in enumerate(dates):
            rows.append([serial(d)] + [base + i / 1000 + n / 10000
                                       for i in range(1, 11)])
        return rows
    return _xlsx({"Contents": [["FRBSF Term Premium Model Data"]],
                  "Fit Treasury Yields": sheet("FYIELD", 0.04),
                  "Fit Term Premium": sheet("FTERMP", 0.0),
                  "Fit Avg Expected Rate": sheet("FEXPTR", 0.03)})


def dkw_csv(dates: list[str]) -> str:
    cols = ["exp.real.short.rate.5", "exp.inflation.5", "real.term.prem.5",
            "inflation.risk.prem.5", "tips.liq.prem.5",
            "exp.real.short.rate.10", "exp.inflation.10", "real.term.prem.10",
            "inflation.risk.prem.10", "tips.liq.prem.10"]
    lines = ['"Components of 5- and 10-year nominal yields ..."', '" "',
             '"Notes: "', '"Data are updated monthly; all rates are in '
             'percentage points."', '" "',
             ",".join(f'"{c}"' for c in ["date"] + cols)]
    for n, d in enumerate(dates):
        lines.append(",".join([d] + [str(round(1 + i / 10 + n / 100, 4))
                                      for i in range(len(cols))]))
    return "\n".join(lines) + "\n"


def patch_fetch(mod, body, headers=None, fail: bool = False) -> None:
    def fake(url, *a, **k):
        if fail:
            raise FetchError(f"simulated outage for {url}")
        return body, dict(headers or {})
    mod.http_get_response = fake


def patch_xlrd_free_acm(table) -> None:
    """ACM's _produce reads a BIFF file through xlrd; the parser is what is under
    test, so the fixture enters one step later -- at the table."""
    def produce():
        return acm.rows_from_table(table, *pub.availability({}))
    acm._produce = produce


ORIGINAL = {m: m._produce for m in (acm, sffed, dkw)}
ORIGINAL_FETCH = {m: m.http_get_response for m in (acm, sffed, dkw)}


def restore() -> None:
    for m, f in ORIGINAL.items():
        m._produce = f
    for m, f in ORIGINAL_FETCH.items():
        m.http_get_response = f


DATES = ["2020-01-02", "2020-01-03", "2020-01-06"]


# ---------------------------------------------------------------------------
def group_a() -> None:
    print(f"{LINE}\nA. THE PARSERS\n{LINE}")
    rows = acm.rows_from_table(acm_table(DATES), LM_CANON, "observed")
    check(len(rows) == len(DATES) * len(acm.KEYS),
          f"ACM: {len(DATES)} days x {len(acm.KEYS)} keys (got {len(rows)})")
    tp10 = [r for r in rows if r["registry_key"] == "acm.term_premium_10y"]
    check(tp10[0]["observed_at"] == "2020-01-02"
          and abs(tp10[0]["value"] - 1.0) < 1e-9,
          "ACM: dd-Mon-yyyy parsed; ACMTP10 read as percent (1.0)")

    book = pub.read_xlsx(sffed_xlsx(DATES))
    check("Fit Term Premium" in book and book["Fit Term Premium"][0][0] == "DATE",
          "the stdlib .xlsx reader returns sheets by name with shared strings")
    rows = sffed.rows_from_workbook(book, LM_CANON, "observed")
    check(len(rows) == len(DATES) * len(sffed.KEYS),
          f"SF Fed: {len(DATES)} days x {len(sffed.KEYS)} keys (got {len(rows)})")
    tp10 = [r for r in rows if r["registry_key"] == "sffed.term_premium_10y"][0]
    check(tp10["observed_at"] == "2020-01-02",
          "SF Fed: Excel serial day converted to the calendar date")
    check(abs(tp10["value"] - 1.0) < 1e-9,
          f"SF Fed: fraction 0.010 stored as PERCENT 1.0 (got {tp10['value']})")

    rows = dkw.rows_from_csv(dkw_csv(DATES), LM_CANON, "observed")
    check(len(rows) == len(DATES) * len(dkw.KEYS),
          f"DKW: preamble skipped, {len(DATES)} days x {len(dkw.KEYS)} keys "
          f"(got {len(rows)})")
    rtp = [r for r in rows if r["registry_key"] == "dkw.real_term_premium_10y"][0]
    check(abs(rtp["value"] - 1.7) < 1e-9,
          "DKW: real.term.prem.10 read from its own column, percentage points")


def group_b() -> None:
    print(f"{LINE}\nB. A CHANGED SHAPE IS A FAILURE\n{LINE}")
    table = acm_table(DATES)
    table[0] = [("ACMTP10X" if h == "ACMTP10" else h) for h in table[0]]
    try:
        acm.rows_from_table(table, LM_CANON, "observed")
        bad("ACM: a renamed column raised")
    except ValueError:
        ok("ACM: a renamed column raises rather than parsing around it")
    text = dkw_csv(DATES).replace("tips.liq.prem.10", "tips.liquidity.10")
    try:
        dkw.rows_from_csv(text, LM_CANON, "observed")
        bad("DKW: a missing column raised")
    except ValueError:
        ok("DKW: a missing column raises")
    db = temp_store()
    try:
        patch_fetch(dkw, text.encode(), LM_HEADERS)
        r = dkw.pull(db=db)
        check(r["status"] == pub.STALE and r["written"] == 0 and count(db) == 0,
              f"a run over the changed file is STALE and writes nothing "
              f"({r['status']}, {r.get('reason')})")
        patch_fetch(dkw, b"no header here\n", LM_HEADERS)
        r = dkw.pull(db=db)
        check(r["status"] == pub.STALE and count(db) == 0,
              "a file with no data rows is STALE, not an empty success")
    finally:
        restore()
        db.close()


def group_c() -> None:
    print(f"{LINE}\nC. STALE, NOT EMPTY\n{LINE}")
    db = temp_store()
    try:
        patch_fetch(sffed, sffed_xlsx(DATES), LM_HEADERS)
        r = sffed.pull(db=db)
        before = count(db)
        check(r["status"] == pub.OK and before == len(DATES) * len(sffed.KEYS),
              f"seeded: {before} rows from a good pull")
        patch_fetch(sffed, b"", fail=True)
        r = sffed.pull(db=db)
        check(r["status"] == pub.STALE, "a fetch failure returns STALE")
        check(r["written"] == 0 and count(db) == before,
              "and writes nothing -- the stored vintages are all still there")
        check("simulated outage" in (r.get("reason") or ""),
              "and names the reason")
        check(r["last_observed"].get("sffed.term_premium_10y") == DATES[-1],
              f"and reports the newest date it kept "
              f"({r['last_observed'].get('sffed.term_premium_10y')})")
        nulls = db.conn.execute("SELECT COUNT(*) FROM observations WHERE "
                                "value_num IS NULL").fetchone()[0]
        check(nulls == 0, "no null or placeholder row was written for the outage")

        patch_fetch(dkw, b"", fail=True)
        r = dkw.pull(db=db)
        check(r["status"] == pub.STALE and r["last_observed"].get(
            "dkw.real_term_premium_10y") is None,
              "a writer that never succeeded is STALE with nothing to keep")
    finally:
        restore()
        db.close()


def group_d() -> None:
    print(f"{LINE}\nD. IDENTITY AND TIME (30.2(a))\n{LINE}")
    db = temp_store()
    try:
        patch_fetch(dkw, dkw_csv(DATES).encode(), LM_HEADERS)
        r = dkw.pull(db=db)
        runs = {x[0] for x in db.conn.execute(
            "SELECT DISTINCT run_id FROM observations")}
        check(runs == {r["run_id"]} and r["run_id"].startswith("frb_dkw-"),
              f"every row carries the run's run_id ({r['run_id']})")
        check(re.match(r"frb_dkw-\d{8}T\d{6}\.\d{6}Z$", r["run_id"] or ""),
              "run_id is session.new_run_id's microsecond form")
        avail = {x[0] for x in db.conn.execute(
            "SELECT DISTINCT available_at FROM observations")}
        check(avail == {LM_CANON},
              f"available_at = Last-Modified, canonical microsecond UTC {avail}")
        kinds = {x[0] for x in db.conn.execute(
            "SELECT DISTINCT availability_kind FROM observations")}
        check(kinds == {"observed"}, "and availability_kind is `observed`")
        check(r["session"] == session.session_date(),
              "the run is filed under session.session_date()")
        a, k = pub.availability({})
        check(k == "ingest_instant" and a,
              "no Last-Modified: the write instant, marked ingest_instant")
    finally:
        restore()
        db.close()

    db = temp_store()
    try:
        tomorrow = (session.session_date_obj() + dt.timedelta(days=3)).isoformat()
        patch_fetch(dkw, dkw_csv(DATES + [tomorrow]).encode(), LM_HEADERS)
        r = dkw.pull(db=db)
        check(r["status"] == pub.STALE and count(db) == 0,
              f"a row dated after today's session ({tomorrow}) is refused and "
              f"nothing is written")
    finally:
        restore()
        db.close()


def group_e() -> None:
    print(f"{LINE}\nE. A RE-READ IS NOT A REVISION, AND THE WINDOW HOLDS\n{LINE}")
    today = session.session_date_obj()
    old = (today - dt.timedelta(days=pub.WRITE_WINDOW_DAYS + 30)).isoformat()
    recent = (today - dt.timedelta(days=10)).isoformat()
    key = "acm.term_premium_10y"
    db = temp_store()
    try:
        table = acm_table([old, recent])
        patch_xlrd_free_acm(table)
        r1 = acm.pull(db=db)
        n1 = count(db, key)
        check(r1["status"] == pub.OK and n1 == 2,
              f"first write is the backfill: both periods stored ({n1})")
        r2 = acm.pull(db=db)
        check(r2["written"] == 0, "an identical second pull writes zero rows")
        tp = table[0].index("ACMTP10")
        table[1][tp] += 0.25          # old period re-estimated
        table[2][tp] += 0.25          # recent period re-estimated
        r3 = acm.pull(db=db)
        per = dict(db.conn.execute(
            "SELECT observed_at, COUNT(*) FROM observations WHERE registry_key=? "
            "GROUP BY observed_at", (key,)).fetchall())
        check(per.get(recent) == 2,
              "a re-estimated value inside the window is a second vintage")
        check(per.get(old) == 1,
              f"one outside the {pub.WRITE_WINDOW_DAYS}-day window, after the "
              f"backfill, is not written")
    finally:
        restore()
        db.close()


def group_f() -> None:
    print(f"{LINE}\nF. REGISTERED\n{LINE}")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(
        encoding="utf-8"))
    src = yaml.safe_load((REPO / "source_registry.yaml").read_text(
        encoding="utf-8"))["sources"]
    metrics = reg.get("metrics") or {}
    for mod in (acm, sffed, dkw):
        for k in mod.KEYS:
            m = metrics.get(k) or {}
            have = all(m.get(f) for f in ("units", "information_half_life",
                                          "revision_policy", "mechanism_group"))
            check(have and m.get("mechanism_group") == "rates_decomposition"
                  and m.get("source") == mod.SOURCE,
                  f"{k}: registered, rates_decomposition, source {mod.SOURCE}")
        s = src.get(mod.SOURCE) or {}
        impl = s.get("implemented_by")
        check(bool(s) and impl and (REPO / impl).is_file(),
              f"source {mod.SOURCE}: in source_registry, implemented_by exists")


def group_g() -> None:
    print(f"{LINE}\nG. WIRED, AND NOWHERE ELSE\n{LINE}")
    check("official" in feeds.FEEDS and set(feeds.OFFICIAL_WRITERS)
          >= {"acm", "sffed", "dkw"},
          "the writers run as the `official` feed of altdata.feeds pull")
    check(set(acm.KEYS + sffed.KEYS + dkw.KEYS) <= set(feeds.official_keys()),
          "and every key is on the freshness roster")
    db = temp_store()
    try:
        f = feeds.freshness(store=db)
        check("official" in f["feeds"] and f["feeds"]["official"]["absent"]
              == len(feeds.official_keys()),
              "an empty store reports the official feed ABSENT, not fine")
    finally:
        db.close()
    units = [p.name for p in (REPO / "deploy" / "systemd").iterdir()]
    check(not [u for u in units if re.search(
        r"acm|sffed|dkw|auction_results|fiscal|official", u)],
          "no systemd unit was added for them -- they ride the existing pull")
    pat = re.compile(r"sources\s*(import|\.)\s*\(?\s*[^\n]*\b(acm|sffed|dkw|"
                     r"treasury_auctions|fiscaldata|_publication)\b")
    offenders = []
    for root in ("monthly_macro", "daily_cascade"):
        for p in (REPO / root).rglob("*.py"):
            if pat.search(p.read_text(encoding="utf-8", errors="replace")):
                offenders.append(str(p.relative_to(REPO)))
    for p in (REPO / "regime.py", REPO / "contradictions.py"):
        if p.is_file() and pat.search(p.read_text(encoding="utf-8",
                                                  errors="replace")):
            offenders.append(p.name)
    check(not offenders,
          f"no report, renderer or regime module imports a writer {offenders}")


def main() -> int:
    print(f"{LINE}\nThe published-file writers (ST-1) -- offline\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g):
        try:
            g()
        except Exception as exc:                              # noqa: BLE001
            bad(f"{g.__name__} raised {type(exc).__name__}: {exc}")
        finally:
            restore()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
