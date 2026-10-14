"""
Validation gate for SR-38's inbox reader (13 Oct 2026): S&P DJI's
`sp-500-eps-est.xlsx`, dropped monthly by the operator, read into the forward
twelve-month operating EPS and the index's revision line. On a synthetic store
and a SYNTHETIC workbook of its own; no network, no box.

THE FIXTURE IS SYNTHETIC. The workbook's host refuses non-browser clients, so no
real file was in hand: `synthetic_workbook()` below writes an xlsx in the layout
config/spdji_eps.yaml declares, its first cell saying so, with made-up figures.
The first real drop is the acceptance.

  A  THE PARSE. The as-of date from its cell; the estimates block between its
     markers, a quarter a row; the forward twelve months the first four
     estimated quarters ending after the as-of date; shared and inline strings,
     serial and printed dates.
  B  LOUD, NEVER A GUESS. Each layout fault names the sheet and the cell or
     range: no sheet, no as-of label, an as-of that is not a date, no header, a
     header split over two rows, no markers, no basis, an EPS cell that is not a
     number, fewer than four forward quarters, not an xlsx.
  C  THE ROWS AND THE CLOCKS. Every row observed on the as-of date; available_at
     the as-of date plus one business day (the next NYSE session, over a
     weekend and a holiday), at the end of that day in New York, kind
     `reconstructed` (ruled 13 Oct 2026); the drop record carries retrieved_at,
     the file's modification time, as its available_at. The writer writes
     through the publication runner. With no file and no drop stored it is
     PENDING, a clean empty run; once a drop is stored, a missing file is STALE.
  D  THE PRINTED LINES. Before a drop, "awaiting the first drop" in the
     Monthly's attribution and the Weekly's revision block; one drop, the
     forward EPS and P/E and "needs a second"; two drops, the forward split
     over their span and the index revision on the SAME four quarters.
  E  WIRING. A registered external writer; its keys and source registered;
     the module fetches nothing; the sweep brings the file in.
  F  THE HEARTBEAT BEFORE THE FIRST DROP (ruled 13 Oct 2026). Through the
     external pull and the freshness roster: the three keys are pending, "no
     file yet", not stale, and stay pending past any allowance; a layout fault
     is still stale; the first drop makes them fresh. AAII's STALE precedent
     is untouched.

    python tools/validate_sr38_inbox.py
"""

from __future__ import annotations

import datetime as dt
import io
import json
import math
import os
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

_TMP = gate_mkdtemp(prefix="validate_sr38_inbox_")
os.environ["CHESTER_DB"] = os.path.join(_TMP, "never.sqlite")
os.environ.setdefault("CHESTER_STATE_DIR", _TMP)

import yaml  # noqa: E402
from altdata import observations, return_attribution as ra  # noqa: E402
from altdata.sources import spdji  # noqa: E402

PASS = FAIL = 0
LINE = "=" * 78
TAG = "(descriptive; unvalidated, n=0)"


def check(c: bool, m: str) -> None:
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
# The synthetic workbook
# ---------------------------------------------------------------------------
def serial(d: str) -> float:
    return float((dt.date.fromisoformat(d) - dt.date(1899, 12, 30)).days)


def synthetic_workbook(as_of: str = "2026-09-30",
                       estimates: list | None = None,
                       cells: dict | None = None,
                       sheet: str = "ESTIMATES&PEs", shared: bool = True,
                       drop: tuple = ()) -> bytes:
    """An xlsx in the declared layout. `estimates` is [(quarter end, eps)];
    `cells` overrides any cell by reference (None deletes it); `drop` names
    cells to remove."""
    est = estimates if estimates is not None else [
        ("2027-12-31", 80.0), ("2027-09-30", 78.0), ("2027-06-30", 76.0),
        ("2027-03-31", 74.0), ("2026-12-31", 72.0), ("2026-09-30", 70.0)]
    grid: dict[str, object] = {
        "A1": "SYNTHETIC FIXTURE -- not S&P DJI data (validate_sr38_inbox)",
        "A2": "S&P 500 EARNINGS AND ESTIMATE REPORT",
        "A4": "Data as of the close of:", "B4": serial(as_of),
        "A6": "OPERATING EARNINGS: BOTTOM UP ESTIMATES",
        "A8": "QUARTER\nEND", "B8": "PRICE", "C8": "OPERATING\nEARNINGS\nPER SHR",
        "D8": "AS REPORTED\nEARNINGS\nPER SHR",
        "A9": "ESTIMATES",
    }
    r = 10
    for q, eps in est:
        grid[f"A{r}"] = serial(q)
        grid[f"C{r}"] = eps
        grid[f"D{r}"] = eps - 5
        r += 1
    grid[f"A{r}"] = "ACTUALS"
    grid[f"A{r + 1}"] = serial("2026-06-30")
    grid[f"B{r + 1}"] = 6000.0
    grid[f"C{r + 1}"] = 66.0
    for k, v in (cells or {}).items():
        if v is None:
            grid.pop(k, None)
        else:
            grid[k] = v
    for k in drop:
        grid.pop(k, None)

    strings: list[str] = []

    def cell_xml(refn: str, v: object) -> str:
        if isinstance(v, (int, float)):
            return f'<c r="{refn}"><v>{v}</v></c>'
        if shared:
            if v not in strings:
                strings.append(str(v))
            return f'<c r="{refn}" t="s"><v>{strings.index(str(v))}</v></c>'
        return f'<c r="{refn}" t="inlineStr"><is><t>{escape(str(v))}</t></is></c>'

    def key(refn: str) -> tuple:
        m = re.fullmatch(r"([A-Z]+)(\d+)", refn)
        return int(m.group(2)), spdji.col_index(m.group(1))
    rows: dict[int, list[str]] = {}
    for refn in sorted(grid, key=key):
        rows.setdefault(key(refn)[0], []).append(cell_xml(refn, grid[refn]))
    sheet_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/'
                 '2006/main"><sheetData>'
                 + "".join(f'<row r="{n}">{"".join(cs)}</row>'
                           for n, cs in sorted(rows.items()))
                 + "</sheetData></worksheet>")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.'
                   'openxmlformats.org/package/2006/content-types"/>')
        z.writestr("xl/workbook.xml",
                   '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://'
                   'schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http'
                   '://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                   f'<sheets><sheet name="README" sheetId="1" r:id="rId1"/>'
                   f'<sheet name="{escape(sheet)}" sheetId="2" r:id="rId2"/></sheets>'
                   '</workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http:'
                   '//schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="worksheet" '
                   'Target="worksheets/sheet1.xml"/>'
                   '<Relationship Id="rId2" Type="worksheet" '
                   'Target="worksheets/sheet2.xml"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml",
                   '<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://'
                   'schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
                   '<row r="1"><c r="A1" t="inlineStr"><is><t>SYNTHETIC</t></is></c>'
                   '</row></sheetData></worksheet>')
        z.writestr("xl/worksheets/sheet2.xml", sheet_xml)
        if shared:
            z.writestr("xl/sharedStrings.xml",
                       '<?xml version="1.0" encoding="UTF-8"?><sst xmlns="http://'
                       'schemas.openxmlformats.org/spreadsheetml/2006/main">'
                       + "".join(f"<si><t>{escape(x)}</t></si>" for x in strings)
                       + "</sst>")
    return buf.getvalue()


def fails(data: bytes) -> str:
    try:
        spdji.parse(data)
    except spdji.LayoutError as exc:
        return str(exc)
    return ""


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE PARSE")
    p = spdji.parse(synthetic_workbook())
    check(p["as_of"] == "2026-09-30" and p["as_of_cell"] == "B4"
          and p["sheet"] == "ESTIMATES&PEs",
          f"the as-of date from its cell ({p['as_of']} at {p['as_of_cell']})")
    check([q for q, _, _ in p["quarters"]]
          == ["2027Q4", "2027Q3", "2027Q2", "2027Q1", "2026Q4", "2026Q3"]
          and "2026Q2" not in [q for q, _, _ in p["quarters"]],
          "the estimates block, a quarter a row, between its markers (the actuals "
          "are not read)")
    check(p["forward"]["quarters"] == ["2026Q4", "2027Q1", "2027Q2", "2027Q3"]
          and p["forward"]["eps"] == 72.0 + 74.0 + 76.0 + 78.0,
          f"the forward twelve months: the first four quarters ending after the "
          f"as-of date, summed ({p['forward']['eps']:.2f}); the quarter ending ON "
          f"the as-of date is not forward")
    q = spdji.parse(synthetic_workbook(shared=False, cells={
        "B4": None, "A4": "Data as of the close of: 09/30/2026",
        "A10": "12/31/2027 (prel.)"}))
    check(q == {**p, "as_of_cell": "A4"},
          "inline strings, a printed date in the label's own cell and a printed "
          "quarter date read the same")


def group_b() -> None:
    head("B. LOUD, NEVER A GUESS")
    cases = [
        ("no sheet", synthetic_workbook(sheet="Estimates"),
         "no sheet 'ESTIMATES&PEs' (the workbook has 'README', 'Estimates')"),
        ("no as-of label", synthetic_workbook(drop=("A4",)),
         "sheet 'ESTIMATES&PEs', range A1:L20: no cell contains "
         "'data as of the close of'"),
        ("an as-of that is not a date", synthetic_workbook(cells={"B4": "TBD"}),
         "sheet 'ESTIMATES&PEs', cell B4: the 'as of' date is not a date"),
        ("no EPS header", synthetic_workbook(drop=("C8",)),
         "sheet 'ESTIMATES&PEs', range A1:Z120: no cell reads "
         "'OPERATING EARNINGS PER SHR'"),
        ("the header split over two rows",
         synthetic_workbook(cells={"C8": None, "C7": "OPERATING EARNINGS PER SHR"}),
         "the header labels sit on different rows ('QUARTER END' at A8, "
         "'OPERATING EARNINGS PER SHR' at C7)"),
        ("no ESTIMATES marker", synthetic_workbook(drop=("A9",)),
         "column A below A8: no 'ESTIMATES' marker"),
        ("no ACTUALS marker", synthetic_workbook(drop=("A16",)),
         "no 'ACTUALS' marker closing the estimates block"),
        ("no basis", synthetic_workbook(cells={"A6": "OPERATING EARNINGS"}),
         "no cell contains 'BOTTOM UP' above the estimates block"),
        ("an EPS cell that is not a number", synthetic_workbook(cells={"C12": "n/a"}),
         "sheet 'ESTIMATES&PEs', cell C12: expected an operating EPS figure under "
         "'OPERATING EARNINGS PER SHR' for 2027Q2, found 'n/a'"),
        ("a quarter cell that is not a date", synthetic_workbook(cells={"A11": "Q3"}),
         "sheet 'ESTIMATES&PEs', cell A11: expected a quarter-end date"),
        ("fewer than four forward quarters",
         synthetic_workbook(estimates=[("2027-03-31", 74.0), ("2026-12-31", 72.0),
                                       ("2026-09-30", 70.0)]),
         "2 estimated quarter(s) end after the as-of date 2026-09-30; the forward "
         "twelve months need 4"),
        ("two cells reading the same label",
         synthetic_workbook(cells={"E8": "QUARTER END"}),
         "2 cells read 'QUARTER END' (A8, E8); the layout expects one"),
        ("not an xlsx", b"PK-not-really",
         "not an xlsx workbook (no zip container)"),
    ]
    for name, data, want in cases:
        got = fails(data)
        check(want in got, f"{name}: {got[:110] or 'NOT REFUSED'}")


def store(name: str) -> observations.ObservationStore:
    return observations.ObservationStore(os.path.join(_TMP, f"{name}.sqlite"))


def drop_file(name: str, data: bytes, mtime: str) -> Path:
    d = Path(_TMP) / name
    d.mkdir(exist_ok=True)
    p = d / "sp-500-eps-est.xlsx"
    p.write_bytes(data)
    t = dt.datetime.fromisoformat(mtime).timestamp()
    os.utime(p, (t, t))
    return p


def group_c() -> None:
    head("C. THE ROWS AND THE CLOCKS")
    data = synthetic_workbook()
    p = drop_file("c", data, "2026-10-03T14:05:00+00:00")
    rows = spdji.read_drop(p)
    by = {}
    for r in rows:
        by.setdefault(r["registry_key"], []).append(r)
    check(set(by) == set(spdji.KEYS) and len(by[spdji.QUARTER_KEY]) == 6,
          "one row a quarter, the forward sum, and the drop record")
    av = spdji.available_at("2026-09-30")
    check(av == "2026-10-02T03:59:59.000000+00:00"
          and all(r["observed_at"] == "2026-09-30" and r["available_at"] == av
                  and r["availability_kind"] == "reconstructed"
                  for r in by[spdji.QUARTER_KEY] + by[spdji.FORWARD_KEY]),
          f"every figure observed on the as-of date (Wed 30 Sep), available at the "
          f"end of the next business day in New York ({av}), kind reconstructed")
    check(spdji.posted_on("2026-10-09") == dt.date(2026, 10, 12)
          and spdji.posted_on("2026-11-25") == dt.date(2026, 11, 27)
          and spdji.posted_on("2026-12-24") == dt.date(2026, 12, 28),
          "plus one BUSINESS day: a Friday as-of is Monday's; over Thanksgiving "
          "and Christmas, the next session")
    check(spdji.available_at("2026-10-09") == "2026-10-13T03:59:59.000000+00:00",
          "a Friday as-of is available at the end of Monday in New York")
    rec = by[spdji.DROP_KEY][0]
    meta = json.loads(rec["value"])
    check(rec["available_at"] == meta["retrieved_at"]
          == "2026-10-03T14:05:00.000000+00:00"
          and rec["availability_kind"] == "ingest_instant"
          and meta["sha256"] and meta["as_of"] == "2026-09-30"
          and meta["forward_quarters"] == ["2026Q4", "2027Q1", "2027Q2", "2027Q3"],
          "the drop record: retrieved_at is the file's modification time (the drop), "
          "and its own available_at")
    os.environ[spdji.FILE_VAR] = str(Path(_TMP) / "absent.xlsx")
    empty = store("c_empty")
    try:
        w = spdji.pull(run_id="gate0", db=empty)
        n = empty.conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        check(w.get("status") == "PENDING" and w.get("written") == 0
              and "awaiting the first drop" in (w.get("reason") or "") and n == 0,
              f"no file and no drop stored: PENDING, a clean empty run that writes "
              f"nothing ({w.get('status')})")
    finally:
        empty.close()
    os.environ[spdji.FILE_VAR] = str(p)
    db = store("c")
    try:
        out = spdji.pull(run_id="gate", db=db)
        check(out.get("status") == "OK" and out.get("written") == 8,
              f"the writer writes through the publication runner "
              f"({out.get('status')}, {out.get('written')} rows)")
        again = spdji.pull(run_id="gate2", db=db)
        check(again.get("written") == 0, "the same drop read twice writes nothing")
        os.environ[spdji.FILE_VAR] = str(Path(_TMP) / "absent.xlsx")
        none = spdji.pull(run_id="gate3", db=db)
        check(none.get("status") == "STALE"
              and "awaiting the first drop" in json.dumps(none),
              f"a drop stored, then no file: STALE, not pending "
              f"({none.get('status')})")
        bad = drop_file("c_bad", synthetic_workbook(cells={"C12": "n/a"}),
                        "2026-10-03T14:05:00+00:00")
        os.environ[spdji.FILE_VAR] = str(bad)
        b = spdji.pull(run_id="gate4", db=db)
        check(b.get("status") != "OK" and "cell C12" in json.dumps(b)
              and "sp-500-eps-est.xlsx" in json.dumps(b),
              "a layout fault: STALE with the file, the sheet and the cell")
    finally:
        os.environ.pop(spdji.FILE_VAR, None)
        db.close()


def seed(db, key, pts, inst=None):
    db.write_many([{"registry_key": key, "instrument": inst, "observed_at": d,
                    "available_at": f"{d}T21:00:00+00:00", "value": float(v),
                    "source": "synthetic", "availability_kind": "ingest_instant"}
                   for d, v in pts])


def group_d() -> None:
    head("D. THE PRINTED LINES")
    from daily_cascade import weekly_stack as ws
    db = store("d")
    try:
        seed(db, "yfinance.mkt_gspc", [("2026-08-31", 6000), ("2026-09-30", 6300)])
        cut = "2026-10-12T00:00:00+00:00"
        a = ra.attribution(db, cut)
        al = ra.attribution_lines(a)
        v = ra.revisions(db, cut)
        rv, _ = ws.ai_revisions_block(db, cut)
        check(al[2] == f"The forward split: {spdji.AWAITING} {TAG}."
              and "Trailing, not forward" in al[3],
              "before a drop: the Monthly's forward line is 'awaiting the first drop'")
        check(rv and rv["lines"][0].startswith("S&P 500 forward-EPS revisions: "
                                               "awaiting the first drop")
              and rv["lines"][1].startswith("Forward-EPS revisions, the nine AI names'"),
              "and the Weekly's revision block opens on the index line, awaiting")
        # The first drop (as of 31 Aug).
        first = synthetic_workbook(as_of="2026-08-31", estimates=[
            ("2027-09-30", 77.0), ("2027-06-30", 75.0), ("2027-03-31", 73.0),
            ("2026-12-31", 71.0), ("2026-09-30", 69.0)])
        db.write_many([dict(r, source="spdji") for r in spdji.read_drop(
            drop_file("d1", first, "2026-09-02T12:00:00+00:00"))])
        a = ra.attribution(db, cut)
        fl = ra.forward_line(a["forward"], TAG)
        v = ra.revisions(db, cut)
        il = ra.index_revision_line(v["index"], TAG)
        e1 = 69.0 + 71.0 + 73.0 + 75.0
        check(fl == (f"S&P 500 forward twelve-month operating EPS (S&P DJI, bottom-up, "
                     f"as of 2026-08-31): ${e1:.2f}, a forward P/E of "
                     f"{6000 / e1:.1f} at the 2026-08-31 close; the forward split "
                     f"needs a second drop {TAG}."),
              f"one drop: the forward EPS and P/E, and 'needs a second' ({fl[:80]}...)")
        check(il.endswith(f"the first drop; revisions need a second {TAG}.")
              and "2026Q3 to 2027Q2" in il,
              "one drop: the index line names its four quarters and needs a second")
        # The second drop (as of 30 Sep), the same quarters revised up.
        db.write_many([dict(r, source="spdji") for r in spdji.read_drop(
            drop_file("d2", synthetic_workbook(), "2026-10-03T14:05:00+00:00"))])
        a = ra.attribution(db, cut)
        fw = a["forward"]
        e2 = 72.0 + 74.0 + 76.0 + 78.0
        lp, le = math.log(6300 / 6000), math.log(e2 / e1)
        check(fw["state"] == "split" and fw["start"] == "2026-08-31"
              and abs(fw["earnings_pct"] - 100 * (e2 / e1 - 1)) < 1e-9
              and abs(fw["multiple_pct"] - 100 * (math.exp(lp - le) - 1)) < 1e-9
              and not fw["full_year"],
              f"two drops: the forward split over their span, exact in logs "
              f"(earnings {fw['earnings_pct']:+.2f}%, multiple "
              f"{fw['multiple_pct']:+.2f}%)")
        fl = ra.forward_line(fw, TAG)
        check("Over 30 days (the stored drops' span, not yet twelve months) from the "
              "2026-08-31 drop" in fl, "and says the span is not yet twelve months")
        v = ra.revisions(db, cut)
        ix = v["index"]
        same = 71.0 + 73.0 + 75.0 + 77.0          # 2026Q4..2027Q3 in the 31 Aug drop
        w = ix["windows"]["1-month"]
        check(ix["quarters"] == ["2026Q4", "2027Q1", "2027Q2", "2027Q3"]
              and abs(w["pct"] - 100 * (e2 / same - 1)) < 1e-9
              and w["since"] == "2026-08-31",
              f"the index revision reads the SAME four quarters in the earlier drop "
              f"({w['pct']:+.2f}%), not the rolled window "
              f"({100 * (e2 / e1 - 1):+.2f}%)")
        check(ix["windows"]["3-month"] == {"pct": None, "why": "no drop that old"},
              "a window with no drop that old is not read, and says why")
        il = ra.index_revision_line(ix, TAG)
        check(il == ("S&P 500 forward-EPS revisions (S&P DJI, bottom-up, the four "
                     "quarters 2026Q4 to 2027Q3, as of 2026-09-30): 1-month "
                     f"{100 * (e2 / same - 1):+.1f}% (since the 2026-08-31 drop); "
                     f"3-month not read (no drop that old) {TAG}."), f"the line: {il}")
        al = ra.attribution_lines(a)
        check(al[2] == fl and al[3].startswith("The twelve-month split above is "
                                               "trailing. Not available: "),
              "the Monthly prints the forward line and no longer lists the forward "
              "series as not available")
        d = ra.data(a, v)
        check(d["forward_eps"] == round(e2, 2) and d["index_revision"]["1-month"]
              == round(100 * (e2 / same - 1), 1),
              "the printed figures are in the section's data")
        old = ra.attribution(db, "2026-09-15T00:00:00+00:00")
        check(old["forward"]["state"] == "one_drop"
              and old["forward"]["end"] == "2026-08-31",
              "as of a cutoff before the second drop's as-of day, one drop is seen")
        eve = ra.attribution(db, "2026-10-01T03:30:00+00:00")
        nxt = ra.attribution(db, "2026-10-02T04:30:00+00:00")
        check(eve["forward"]["state"] == "one_drop"
              and nxt["forward"]["state"] == "split",
              "the as-of evening does not see the 30 Sep drop; the evening of the "
              "next business day does")
    finally:
        db.close()


def group_e() -> None:
    head("E. WIRING")
    from altdata import feeds
    check("spdji" in feeds.EXTERNAL_WRITERS, "a registered external writer")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    mets = reg.get("metrics") or reg
    check(all(k in mets and mets[k]["source"] == "spdji"
              and mets[k]["trigger_eligible"] is False for k in spdji.KEYS),
          "every key it writes is registered, sourced spdji, none trigger-eligible")
    srcs = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))
    check("spdji" in srcs["sources"]
          and "Nothing is fetched" in srcs["sources"]["spdji"]["license"],
          "the source is registered and says nothing is fetched")
    body = (REPO / "altdata" / "sources" / "spdji.py").read_text(encoding="utf-8")
    # (The xlsx's XML namespaces are http:// strings; they are not fetches.)
    check(not re.search(r"import requests|http_get|urllib\.request|urlopen|socket",
                        body),
          "the reader fetches nothing")
    sweep = (REPO / "scripts" / "rclone_sync.sh").read_text(encoding="utf-8")
    unit = (REPO / "deploy" / "systemd" / "chester-backup.service").read_text(
        encoding="utf-8")
    check("pull_inbox_file spdji sp-500-eps-est.xlsx || true" in sweep
          and "-%h/chester-data/inbox/spdji" in unit,
          "the sweep copies chester-vendor-checks/spdji/sp-500-eps-est.xlsx into "
          "~/chester-data/inbox/spdji, which its unit may write")
    lay = spdji.layout()
    check(lay["sheet"] == "ESTIMATES&PEs" and lay["forward_quarters"] == 4
          and spdji.inbox_path().name == "sp-500-eps-est.xlsx",
          "the layout is declared in config/spdji_eps.yaml")


def group_f() -> None:
    head("F. THE HEARTBEAT BEFORE THE FIRST DROP")
    from altdata import feeds
    names = ("CHESTER_STATE_DIR", spdji.FILE_VAR)
    saved = (feeds.EXTERNAL_WRITERS, {k: os.environ.get(k) for k in names},
             observations.DEFAULT_DB)
    sd = Path(_TMP) / "f_state"
    sd.mkdir(exist_ok=True)
    # The store's default path is read at import, so the writer's store is set
    # there: the writer and the roster both open the default.
    observations.DEFAULT_DB = os.path.join(_TMP, "f.sqlite")
    os.environ["CHESTER_STATE_DIR"] = str(sd)
    os.environ[spdji.FILE_VAR] = str(Path(_TMP) / "absent.xlsx")
    feeds.EXTERNAL_WRITERS = ("spdji",)

    def roster() -> dict:
        db = observations.ObservationStore()
        try:
            return feeds.freshness(as_of="2026-10-13T12:30:00+00:00",
                                   store=db)["feeds"]["external"]
        finally:
            db.close()

    try:
        out = feeds.pull_external(run_id="gate_f")
        check(out["pending"] == ["spdji"] and out["stale"] == [],
              "the external pull counts the never-dropped writer pending, not stale")
        f = roster()
        check(sorted(f["pending_keys"]) == sorted(spdji.KEYS)
              and not f["stale_keys"] and f["ok"]
              and all(f["pending_detail"][k].startswith(
                  "no file yet (spdji: awaiting the first drop") for k in spdji.KEYS),
              f"the 08:30 heartbeat lists the three keys under pending, 'no file "
              f"yet', and none stale (stale {f['stale_keys']})")
        lines = [ln for ln in feeds.named_keys({"feeds": {"external": f}})
                 if "spdji." in ln]
        check(len(lines) == 3 and all(ln.startswith("pending external spdji.")
                                      for ln in lines),
              "and the verdict names them as pending")
        att = sd / feeds.ATTEMPTED_FILE
        d = json.loads(att.read_text(encoding="utf-8"))
        d["external"]["first"] = {k: "2025-01-02T00:00:00+00:00" for k in spdji.KEYS}
        att.write_text(json.dumps(d), encoding="utf-8")
        f = roster()
        check(sorted(f["pending_keys"]) == sorted(spdji.KEYS) and not f["stale_keys"],
              "no allowance runs: first tried over a year ago, still pending until "
              "the first drop")
        bad = drop_file("f_bad", synthetic_workbook(cells={"C12": "n/a"}),
                        "2026-10-03T14:05:00+00:00")
        os.environ[spdji.FILE_VAR] = str(bad)
        out = feeds.pull_external(run_id="gate_f2")
        f = roster()
        check(out["stale"] == ["spdji"]
              and sorted(f["stale_keys"]) == sorted(spdji.KEYS)
              and "cell C12" in f["stale_detail"][spdji.FORWARD_KEY],
              "a file that will not parse is a fault: stale, naming the cell")
        good = drop_file("f_good", synthetic_workbook(),
                         "2026-10-03T14:05:00+00:00")
        os.environ[spdji.FILE_VAR] = str(good)
        out = feeds.pull_external(run_id="gate_f3")
        f = roster()
        check(out["stale"] == [] and out["pending"] == []
              and not f["pending_keys"] and not f["stale_keys"]
              and f["fresh"] == len(spdji.KEYS),
              f"the first drop: the three keys are fresh ({f['fresh']})")
        st = {"aaii": {"status": "STALE", "reason": "no file"}}
        check(feeds.writer_awaiting([("aaii", None)], st) == {}
              and feeds.writer_failures([("aaii", None)], st),
              "AAII's precedent is untouched: a STALE writer is failed, never awaiting")
    finally:
        feeds.EXTERNAL_WRITERS = saved[0]
        observations.DEFAULT_DB = saved[2]
        for k, v in saved[1].items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def main() -> int:
    print(f"{LINE}\nSR-38: S&P DJI'S EPS WORKBOOK, FROM THE INBOX (SYNTHETIC FIXTURE)\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f):
        g()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
