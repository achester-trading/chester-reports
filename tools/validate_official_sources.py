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
  H  TREASURY AUCTIONS. Shares of competitive accepted sum to one; coupons key
     on original term and bills on the term sold (a 13-week reopening of a
     26-week bill is not a 26-week auction); an unheld auction is skipped;
     available_at is 13:00 ET in both EDT and EST, `reconstructed`, on keys
     whose revision_policy permits it; the tail is registered not_yet_sourced
     and never written; the family is distinct from ibkr.auction_*.
  I  MSPD (G-14). Millions arrive as dollars; net issuance is the change in
     Total Marketable across CONSECUTIVE month-ends only; inflation-indexed
     classes sum into _tips; a response with no total is STALE; the decision
     is recorded under SR-23.
  J  manual_input. One observation with the note on the same row, the entry
     instant as available_at and a run_id; unregistered keys, out-of-range
     fractions, future dates, non-numbers and missing notes are refused; a
     correction is a new vintage that supersedes, not an edit; the order's six
     keys exist.
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
from altdata.sources import acm, dkw, fiscaldata, sffed  # noqa: E402
from altdata.sources import treasury_auctions  # noqa: E402
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
ORIGINAL_JSON = {m: m.http_get_json for m in (treasury_auctions, fiscaldata)}


def restore() -> None:
    for m, f in ORIGINAL.items():
        m._produce = f
    for m, f in ORIGINAL_FETCH.items():
        m.http_get_response = f
    for m, f in ORIGINAL_JSON.items():
        m.http_get_json = f


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
    # EVERY WRITER THE FEED KNOWS, not a list copied here -- ST-2 added fourteen,
    # and a guard that names only the first five stops guarding at the sixth.
    writers = list(feeds.OFFICIAL_WRITERS) + list(
        getattr(feeds, "EXTERNAL_WRITERS", ()))
    alt = "|".join(re.escape(w) for w in writers + ["_publication"])
    units = [p.name for p in (REPO / "deploy" / "systemd").iterdir()]
    check(not [u for u in units if re.search(
        rf"(?:{alt}|auction_results|official|external)", u.replace("-", "_"))],
          f"no systemd unit was added for any of the {len(writers)} writers -- "
          f"they ride the existing pull")
    pat = re.compile(r"sources\s*(import|\.)\s*\(?\s*[^\n]*\b(" + alt + r")\b")
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


# ---------------------------------------------------------------------------
def auction(day, typ, term, orig, cusip, btc="2.42", hy="5.0850",
            pd="5447550000", direct="13163710000", ind="24869544500",
            comp="43480804500"):
    return {"auctionDate": f"{day}T00:00:00", "type": typ, "securityType": typ,
            "securityTerm": term, "originalSecurityTerm": orig, "cusip": cusip,
            "bidToCoverRatio": btc, "highYield": hy if typ != "Bill" else "",
            "primaryDealerAccepted": pd, "directBidderAccepted": direct,
            "indirectBidderAccepted": ind, "competitiveAccepted": comp,
            "offeringAmount": "44000000000"}


def group_h() -> None:
    print(f"{LINE}\nH. TREASURY AUCTIONS\n{LINE}")
    recs = [auction("2020-09-24", "Note", "7-Year", "7-Year", "C7"),
            auction("2020-09-24", "Note", "9-Year 10-Month", "10-Year", "C10"),
            auction("2020-01-13", "Bill", "26-Week", "26-Week", "B26"),
            auction("2020-01-13", "Bill", "13-Week", "26-Week", "B13"),
            dict(auction("2020-09-29", "Note", "5-Year", "5-Year", "UNHELD"),
                 bidToCoverRatio="")]
    rows = treasury_auctions.rows_from_records(recs)
    insts = {r["instrument"] for r in rows}
    check(insts == {"Note:7-Year", "Note:10-Year", "Bill:26-Week",
                    "Bill:13-Week"},
          f"coupons by original term, bills by the term sold {sorted(insts)}")
    check(not any(r["value"] == "UNHELD" for r in rows),
          "an auction with no bid-to-cover (not yet held) is skipped")
    s7 = {r["registry_key"]: r["value"] for r in rows
          if r["instrument"] == "Note:7-Year"}
    tot = (s7["auction.dealer_share"] + s7["auction.direct_share"]
           + s7["auction.indirect_share"])
    check(abs(tot - 1.0) < 1e-6
          and abs(s7["auction.dealer_share"] - 0.12528632) < 1e-6,
          f"shares of competitive accepted sum to 1 (dealer "
          f"{s7['auction.dealer_share']:.4f}, the 24 Sep 2026 7-year's figures)")
    check(s7["auction.high_yield"] == 5.085 and not any(
        r["registry_key"] == "auction.high_yield"
        and r["instrument"].startswith("Bill") for r in rows),
          "high_yield on coupons only")
    edt = treasury_auctions.available_at("2020-09-24")
    est = treasury_auctions.available_at("2020-01-13")
    check(edt == "2020-09-24T17:00:00.000000+00:00"
          and est == "2020-01-13T18:00:00.000000+00:00",
          f"available_at = 13:00 ET in EDT ({edt}) and EST ({est})")
    check({r["availability_kind"] for r in rows} == {"reconstructed"},
          "marked reconstructed")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(
        encoding="utf-8"))["metrics"]
    check(all((reg.get(k) or {}).get("revision_policy")
              in observations.RECONSTRUCTABLE_POLICIES
              for k in treasury_auctions.KEYS),
          "every written auction key has a revision_policy that permits "
          "reconstruction")
    tail = reg.get("auction.tail_bp") or {}
    check(tail.get("status_extra") == "not_yet_sourced"
          and "auction.tail_bp" not in treasury_auctions.KEYS
          and not any(r["registry_key"] == "auction.tail_bp" for r in rows),
          "auction.tail_bp is registered not_yet_sourced and never written")
    check(all(k.startswith("auction.") for k in treasury_auctions.KEYS),
          "the family is auction.*, distinct from ibkr.auction_*")
    db = temp_store()
    try:
        treasury_auctions.http_get_json = lambda *a, **k: recs
        r = treasury_auctions.pull(db=db)
        n = count(db)
        check(r["status"] == pub.OK and n == len(rows),
              f"a pull writes every row ({n})")
        check(treasury_auctions.pull(db=db)["written"] == 0,
              "a second identical pull writes zero rows")

        def boom(*a, **k):
            raise FetchError("simulated TreasuryDirect outage")
        treasury_auctions.http_get_json = boom
        r = treasury_auctions.pull(db=db)
        check(r["status"] == pub.STALE and count(db) == n,
              "an outage is STALE and leaves every stored auction in place")
    finally:
        restore()
        db.close()


def mspd(day, typ, cls, amt):
    return {"record_date": day, "security_type_desc": typ,
            "security_class_desc": cls, "debt_held_public_mil_amt": str(amt)}


def group_i() -> None:
    print(f"{LINE}\nI. MSPD (G-14)\n{LINE}")
    recs = []
    for day, total in (("2020-01-31", 1000.0), ("2020-02-29", 1100.0),
                       ("2020-03-31", 1150.0), ("2020-05-31", 1400.0)):
        recs += [mspd(day, "Marketable", "Bills", 400),
                 mspd(day, "Marketable", "Notes", 300),
                 mspd(day, "Marketable", "Bonds", 200),
                 mspd(day, "Marketable", "Treasury Inflation-Indexed Notes", 30),
                 mspd(day, "Marketable", "Treasury Inflation-Indexed Bonds", 20),
                 mspd(day, "Marketable", "Federal Financing Bank", 0),
                 mspd(day, "Total Marketable", "_", total)]
    rows = fiscaldata.rows_from_records(recs, LM_CANON)
    by = {(r["registry_key"], r["observed_at"]): r["value"] for r in rows}
    check(by[(fiscaldata.TOTAL_KEY, "2020-01-31")] == 1000.0 * 1e6,
          "millions arrive in the store as dollars")
    check(by[(fiscaldata.CLASS_KEYS["tips"], "2020-01-31")] == 50.0 * 1e6,
          "inflation-indexed notes and bonds sum into _tips")
    check(by.get((fiscaldata.NET_KEY, "2020-02-29")) == 100.0 * 1e6
          and by.get((fiscaldata.NET_KEY, "2020-03-31")) == 50.0 * 1e6,
          "net issuance is the change in Total Marketable month on month")
    check((fiscaldata.NET_KEY, "2020-05-31") not in by
          and (fiscaldata.NET_KEY, "2020-01-31") not in by,
          "no net figure across a missing month, and none for the first")
    try:
        fiscaldata.rows_from_records(
            [r for r in recs if r["security_type_desc"] != "Total Marketable"],
            LM_CANON)
        bad("a response without Total Marketable raised")
    except ValueError:
        ok("a response without Total Marketable raises")
    db = temp_store()
    try:
        fiscaldata.http_get_json = lambda *a, **k: {"data": [], "meta": {}}
        r = fiscaldata.pull(db=db)
        check(r["status"] == pub.STALE and count(db) == 0,
              "an empty response is STALE and writes nothing")
    finally:
        restore()
        db.close()
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(
        encoding="utf-8"))["metrics"]
    check(all((reg.get(k) or {}).get("units") == "usd"
              for k in fiscaldata.KEYS),
          "every fiscaldata key is registered in usd")
    text = (REPO / "docs" / "signal-triage-register.md").read_text(
        encoding="utf-8")
    sr23 = text.split("### SR-23", 1)[-1].split("### SR-24", 1)[0]
    check("G-14" in sr23 and "mspd_net_marketable_issuance" in sr23,
          "the G-14 decision is recorded under SR-23 in the register")


def group_j() -> None:
    print(f"{LINE}\nJ. manual_input\n{LINE}")
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "manual_input", REPO / "tools" / "manual_input.py")
    mi = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mi)
    required = {"manual.sep_median_next2", "manual.sep_median_12m",
                "manual.fedwatch_next_meeting_prob", "manual.cbo_deficit_path",
                "manual.ig_nic_median_bp", "manual.ig_cover_median"}
    keys = mi.manual_keys()
    check(required <= set(keys),
          f"the order's six keys are registered "
          f"(missing {sorted(required - set(keys))})")
    fd, path = tempfile.mkstemp(suffix=".sqlite", dir=_TMP)
    os.close(fd)
    os.unlink(path)
    mi.write("manual.sep_median_12m", "3.625", "2020-09-16",
             "SEP Sep 2020 -- fixture", db_path=path)
    with observations.ObservationStore(path) as db:
        got = db.conn.execute(
            "SELECT value_num, value_text, run_id, source, available_at "
            "FROM observations").fetchall()
        check(len(got) == 1 and got[0][0] == 3.625
              and got[0][1] == "SEP Sep 2020 -- fixture",
              "one observation, the number and its note on the same row")
        check(got[0][2].startswith("manual_input-")
              and got[0][3] == "manual_input",
              f"run_id and source stamped ({got[0][2]})")
        check(bool(re.match(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}\+00:00$",
                            got[0][4]))
              and got[0][4][:10] >= session.utc_iso()[:10],
              "available_at is the ENTRY instant, canonical microsecond UTC, "
              "not the observed date")
        mi.write("manual.sep_median_12m", "3.375", "2020-09-16",
                 "SEP Sep 2020 -- corrected", db_path=path)
        last = db.latest_as_of("manual.sep_median_12m")
        check(count(db, "manual.sep_median_12m") == 2
              and last["value_num"] == 3.375,
              "a correction is a second vintage that supersedes; the first "
              "stays on record")
    tomorrow = (session.session_date_obj() + dt.timedelta(days=1)).isoformat()
    cases = ((("manual.nope", "1", "2020-01-01", "n"), "an unregistered key"),
             (("manual.fedwatch_next_meeting_prob", "72", "2020-01-01", "n"),
              "a fraction entered as a percent"),
             (("manual.sep_median_12m", "3.5", tomorrow, "n"), "a future date"),
             (("manual.sep_median_12m", "3.5", "2020-01-01", "  "), "no note"),
             (("manual.sep_median_12m", "abc", "2020-01-01", "n"),
              "a non-number"),
             (("manual.sep_median_12m", "nan", "2020-01-01", "n"), "NaN"))
    for args, why in cases:
        try:
            mi.write(*args, db_path=path)
            bad(f"refuses {why}")
        except mi.Refused:
            ok(f"refuses {why}")
    with observations.ObservationStore(path) as db:
        check(count(db) == 2, "and a refusal writes nothing")
    check(mi.main(["manual.nope", "1", "2020-01-01", "n", "--db", path]) == 2,
          "the CLI exits 2 on a refusal")


# ===========================================================================
# ST-2
# ===========================================================================
def _writer_modules() -> list:
    import importlib
    names = list(feeds.OFFICIAL_WRITERS) + list(getattr(feeds, "EXTERNAL_WRITERS", ()))
    return [(n, importlib.import_module(f"altdata.sources.{n}")) for n in names]


def _tsv(rows: list[list]) -> str:
    return "\n".join("\t".join(str(c) for c in r) for r in rows) + "\n"


def tic_history(japan_aug: float = 1183.9) -> str:
    """A two-year slice of mfhhis01.txt's layout, with a June series break."""
    months = ["Dec", "Nov", "Oct", "Sep", "Aug", "Jul", "Jun", "Jun", "May"]
    return _tsv([["MAJOR FOREIGN HOLDERS"], [""] + months, ["Country"] + ["2025"] * 9,
                 ["Japan"] + [900, 901, 902, 903, japan_aug, 905, 906, 999, 907],
                 ['"China, Mainland"'] + [1100] * 9,
                 ["All Other"] + [50] * 9,
                 ["Grand Total"] + [2000] * 9, ["Of which:"],
                 ["For. Official"] + [1500] * 9, ["Treasury Bills"] + [100] * 9,
                 ["T-Bonds & Notes"] + [1400] * 9])


def tic_table5() -> str:
    return _tsv([["Table 5: Major Foreign Holders of Treasury Securities"],
                 ["Country", "2025-12", "2025-11"], ["Japan", 900, 901],
                 ["All Other", 70, 71], ["Grand Total", 2000, 2000],
                 ["Of Which: Foreign Official", 1500, 1500],
                 ["Of Which: Foreign Official Treasury Bills", 100, 100],
                 ["Of Which: Foreign Official T-Bonds & Notes", 1400, 1400]])


def tic_flows() -> str:
    head = [["TIC monthly reports"], [""] + [str(n) for n in range(1, 33)]]
    return _tsv(head + [["2025-Dec"] + [n * 10 for n in range(1, 33)],
                        ["2025-Nov"] + [n * 2 for n in range(1, 33)]])


def group_k() -> None:
    from altdata.sources import tic
    print(f"{LINE}\nK. TIC -- HOLDINGS, FLOWS AND THE G-8 VINTAGE RULE\n{LINE}")
    p = tic.parse_holdings(tic_history())
    check(p.get((tic.COUNTRY_KEY, "Japan", "2025-06-30")) == 906,
          "a series-break month keeps the FIRST column (the continuing series), "
          "not the comparison column")
    check(p.get((tic.COUNTRY_KEY, "China, Mainland", "2025-12-31")) == 1100,
          "quoted country names are unquoted")
    check(p.get((tic.OFFICIAL_BILLS_KEY, None, "2025-12-31")) == 100
          and p.get((tic.OFFICIAL_BONDS_KEY, None, "2025-12-31")) == 1400,
          "the official bills / bonds-and-notes lines are read in both layouts")
    rows = tic.holdings_rows(tic_table5(), LM_CANON, "observed", current_table=True)
    insts = {r["instrument"] for r in rows if r["registry_key"] == tic.COUNTRY_KEY}
    check(tic.TABLE5_RESIDUAL in insts and "All Other" not in insts,
          "Table 5's residual is stored under its own roster name")
    priv = [r for r in rows if r["registry_key"] == tic.PRIVATE_KEY]
    check(priv and priv[0]["value"] == 500 * 1e9,
          "private = Grand Total minus Foreign Official, in dollars")
    fl = tic.flow_rows(tic_flows(), LM_CANON, "observed")
    by = {(r["registry_key"], r["observed_at"]): r["value"] for r in fl}
    check(len(tic.FLOW_LINES) == 32 and by[("tic.flow_total_official", "2025-12-31")]
          == 320 * 1e6,
          "all 32 flow lines, line 32 read from column 32, millions to dollars")
    try:
        tic.flow_rows(tic_flows().replace("\t32\n", "\t33\n", 1), LM_CANON, "observed")
        bad("a flows file without its 1..32 column-number row raised")
    except ValueError:
        ok("a flows file without its 1..32 column-number row raises")

    lm1 = {"last-modified": "Mon, 18 May 2026 20:00:27 GMT"}
    lm2 = {"last-modified": "Wed, 16 Sep 2026 20:01:58 GMT"}
    db = temp_store()
    orig = tic.http_get_response
    try:
        def serve(hist, headers):
            def fake(url, *a, **k):
                if url == tic.URL_HISTORY:
                    return hist.encode(), headers
                if url == tic.URL_CURRENT:
                    return tic_table5().encode(), headers
                return tic_flows().encode(), headers
            return fake
        tic.http_get_response = serve(tic_history(1180.4), lm1)
        tic.pull(db=db)
        tic.http_get_response = serve(tic_history(1183.9), lm2)
        tic.pull(db=db)
        n = db.conn.execute(
            "SELECT COUNT(*) FROM observations WHERE registry_key=? AND "
            "instrument='Japan' AND observed_at='2025-08-31'",
            (tic.COUNTRY_KEY,)).fetchone()[0]
        check(n == 2, "G-8: a benchmark restatement is a SECOND vintage of the "
                      "same month, never an overwrite")
        latest = {r["observed_at"]: r["value_num"] for r in
                  db.as_of(tic.COUNTRY_KEY, instrument="Japan")}
        check(latest["2025-08-31"] == 1183.9 * 1e9,
              "by default the reader gets the LATEST (benchmark-revised) vintage")
        early = {r["observed_at"]: r["value_num"] for r in
                 db.as_of(tic.COUNTRY_KEY, as_of="2026-06-01T00:00:00Z",
                          instrument="Japan")}
        check(early["2025-08-31"] == 1180.4 * 1e9,
              "an as-of cutoff before the revision still gets the earlier one")
        m = db.conn.execute(
            "SELECT COUNT(*) FROM observations WHERE registry_key=? AND "
            "instrument='Japan' AND observed_at='2025-12-31'",
            (tic.COUNTRY_KEY,)).fetchone()[0]
        check(m == 1, "a month both files state identically is ONE row, not "
                      "a vintage per file")
    finally:
        tic.http_get_response = orig
        db.close()


def group_l() -> None:
    from altdata.sources import safe
    print(f"{LINE}\nL. SAFE -- THE FORMAT TRAPS\n{LINE}")
    table = [["项目\xa0\xa0Item", "2026.01", None, "2026.02", None],
             [None, "亿美元", "亿SDR", "亿美元", "亿SDR"],
             ["1.\xa0\xa0外汇储备", "33990.78\xa0", "24597.67\xa0", "34278.07\xa0", "1"],
             ["4.\xa0\xa0黄金", "3695.82\xa0", "2674.51\xa0", "3875.88\xa0", "1"],
             [None, "7419万盎司", "7419万盎司", "7422万盎司", "7422万盎司"],
             ["\xa0\xa0\xa0\xa0合计", "38362.81\xa0", "1", "38826.93\xa0", "1"]]
    rows = safe.reserve_rows(table, LM_CANON, "observed")
    by = {(r["registry_key"], r["observed_at"]): r["value"] for r in rows}
    check(by.get(("safe.fx_reserves", "2026-01-31")) == 3399078000000.0,
          "text values with a trailing NBSP parse; 100 million USD to dollars; "
          "the SDR columns are not read")
    check(by.get(("safe.gold_reserves_oz", "2026-02-28")) == 74220000.0,
          "gold volume 万盎司 is stored in ounces")
    cases = {40633.0: "2011-03-31", "31-12-2011": "2011-12-31",
             "12-31-2013": "2013-12-31", "31/03/2026": "2026-03-31",
             "2026Q1": "2026-03-31", "1998Q4": "1998-12-31"}
    got = {k: safe._quarter_end(k) for k in cases}
    check(got == cases, f"the IIP header's four date spellings all parse {got}")


def group_m() -> None:
    from altdata import config
    from altdata.sources import cfets, cftc, mof
    print(f"{LINE}\nM. RATES, THE FIX AND POSITIONING -- AVAILABILITY RULES\n{LINE}")
    text = ("Interest Rate,,,,\nDate,1Y,2Y,5Y,10Y,30Y\n1986/7/5,5.1,5.2,5.3,5.4,-\n")
    rows = mof.rows_from_csv(text, LM_CANON, "observed")
    keys = {r["registry_key"] for r in rows}
    check("mof.jgb_30y" not in keys and "mof.jgb_10y" in keys
          and rows[0]["observed_at"] == "1986-07-05",
          "MoF: YYYY/M/D parses; a '-' tenor (not yet issued) is skipped, not zero")
    check(cfets.fix_available_at("2026-09-24") == "2026-09-24T01:15:00.000000+00:00",
          "CFETS fix: available at 09:15 Beijing (01:15 UTC)")
    curve = {"records": [{"newDateValueCN": "2026-09-24", "yearTermStr": "7.0",
                          "maturityYieldStr": "1.50"},
                         {"newDateValueCN": "2026-09-24", "yearTermStr": "10.0",
                          "maturityYieldStr": "1.6737"}]}
    g = cfets.cgb_rows(curve, LM_CANON)
    check(len(g) == 1 and g[0]["value"] == 1.6737,
          "CFETS curve: the 10.0-year point is the one stored")
    check(cftc.available_at("2026-09-22") == "2026-09-25T19:30:00.000000+00:00",
          "CFTC: Tuesday positions available Friday 15:30 ET")
    r = cftc.rows_from_records([{"cftc_contract_market_code": "097741",
                                 "report_date_as_yyyy_mm_dd": "2026-09-22T00:00:00.000",
                                 "noncomm_positions_long_all": "192274",
                                 "noncomm_positions_short_all": "120292",
                                 "open_interest_all": "378701"}])
    net = [x for x in r if x["registry_key"] == "cftc.noncomm_net"][0]
    check(net["value"] == 71982 and net["instrument"] == "JPY",
          "CFTC: net = long - short, instrument JPY")
    check(config.ENABLED_SOURCES.get("cftc") is True, "the cftc switch is ON")
    db = temp_store()
    try:
        config.ENABLED_SOURCES["cftc"] = False
        s = cftc.pull(db=db)
        check(s["status"] == pub.STALE and "switch" in (s.get("reason") or ""),
              "and when it is off the writer is STALE with that reason, not silent")
    finally:
        config.ENABLED_SOURCES["cftc"] = True
        db.close()


NOT_SOURCED_ST2 = ["hktma.cnh_hibor_on", "hktma.cnh_hibor_1w",
                   "hktma.cnh_hibor_1m", "hktma.cnh_hibor_3m"]


def group_n() -> None:
    print(f"{LINE}\nN. EVERY WRITER: REGISTERED, AND STALE-NOT-EMPTY OFFLINE\n{LINE}")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(
        encoding="utf-8"))["metrics"]
    src = yaml.safe_load((REPO / "source_registry.yaml").read_text(
        encoding="utf-8"))["sources"]
    mods = _writer_modules()
    all_keys = set()
    for name, mod in mods:
        keys = list(getattr(mod, "KEYS", []))
        all_keys |= set(keys)
        missing = [k for k in keys if not all((reg.get(k) or {}).get(f) for f in (
            "units", "information_half_life", "revision_policy", "mechanism_group"))]
        s = src.get(getattr(mod, "SOURCE", ""), {})
        check(keys and not missing and s.get("implemented_by")
              and (REPO / s["implemented_by"]).is_file(),
              f"{name}: {len(keys)} keys registered with the four fields; source "
              f"{getattr(mod, 'SOURCE', '?')} registered {missing}")

    def boom(*a, **k):
        raise FetchError("simulated outage")
    saved = {}
    for name, mod in mods:
        # fetch_frames: fundamentals.py reads yfinance, not the HTTP helpers, and
        # an outage test that left it live reached the network and wrote rows.
        for attr in ("http_get_response", "http_get_json", "http_get_text",
                     "fetch_frames"):
            if hasattr(mod, attr):
                saved[(mod, attr)] = getattr(mod, attr)
                setattr(mod, attr, boom)
    saved_find = pub.find_link
    pub.find_link = boom
    db = temp_store()
    try:
        for name, mod in mods:
            before = count(db)
            r = mod.pull(db=db)
            check(r["status"] == pub.STALE and r["written"] == 0
                  and count(db) == before,
                  f"{name}: an outage is STALE and writes nothing")
    finally:
        for (mod, attr), fn in saved.items():
            setattr(mod, attr, fn)
        pub.find_link = saved_find
        db.close()
    ns = [k for k in NOT_SOURCED_ST2 + list(globals().get("NOT_SOURCED_ST2_STEP2", []))]
    check(all((reg.get(k) or {}).get("status_extra") == "not_yet_sourced" for k in ns)
          and not (set(ns) & all_keys),
          f"{len(ns)} not_yet_sourced keys are registered and no writer claims them")


NOT_SOURCED_ST2_STEP2 = ["oil.prompt_spread", "wgc.cb_gold_holdings_t",
                         "wgc.cb_net_purchases_t", "sifma.corp_issuance_by_maturity"]


def group_o() -> None:
    from altdata.sources import (damodaran, eia, fedboard, finra, french, lbma,
                                 nyfed_sce, proshares, shiller, umich, worldbank)
    print(f"{LINE}\nO. SURVEYS, OIL, REFERENCE LIBRARIES, LEVERAGE -- PARSERS AND "
          f"CONVENTIONS\n{LINE}")
    # dating: stocks at month-end, averages and surveys at the month's first day
    check(pub.month_start(2026, 9) == "2026-09-01" and pub.month_end(2026, 9)
          == "2026-09-30", "month_start / month_end")
    u = umich.rows_from_csv("Month,YYYY,PX_MD,PX5_MD\nSeptember,2026,4.6,3.4\n"
                            "March,1979,8.8,\n", LM_CANON, "observed")
    check(len(u) == 1 and u[0]["observed_at"] == "2026-09-01",
          "UMich: dated at the survey month's first day (never in the future); a "
          "blank PX5_MD is skipped")
    check(nyfed_sce._yyyymm(202608.0) == "2026-08-01", "SCE: YYYYMM to month start")
    c = fedboard.rows_from_csv("﻿period,CIE_spf,CIE_mich\n6/30/2026,2.23,3.17\n",
                               LM_CANON, "observed")
    check({(r["instrument"], r["observed_at"]) for r in c}
          == {("spf", "2026-06-30"), ("mich", "2026-06-30")},
          "CIE: BOM stripped, M/D/YYYY quarter-end, both variants as instruments")
    # oil
    check(eia.available_at("2026-09-18") == "2026-09-23T14:30:00.000000+00:00",
          "EIA: week-ending Friday available the following Wednesday 10:30 ET")
    tab = [["Back to Contents"], ["Sourcekey"], ["Date"], [46283.0, 426398.0]]
    s = eia.series_from_table(tab)
    check(list(s.values()) == [426398000.0], "EIA: thousand barrels stored as barrels")
    rows = eia.rows_from_series({"eia.crude_stocks": {"2026-09-18": 4.0e8},
                                 "eia.total_stocks": {"2026-09-18": 1.25e9}})
    prod = [r for r in rows if r["registry_key"] == "eia.product_stocks"]
    check(prod and prod[0]["value"] == 8.5e8, "EIA: products = total - crude")
    check("oil.prompt_spread" not in eia.KEYS, "G-11: the prompt spread is not written")
    # reference libraries
    factors = ("This file was created using the 202608 CRSP database.\n"
               "The 1-month TBill rate data until 202405 are from Ibbotson, then ICE.\n"
               "\n,Mkt-RF,SMB,HML,RF\n202607,1.0,2.0,-3.54,0.3\n202608,1.0,2.0,-99.99,0.3\n"
               "\n Annual Factors: January-December \n,Mkt-RF,SMB,HML,RF\n2025,1,2,3,4\n")
    h = french.rows_from_factors(factors, LM_CANON, "observed")
    check(len(h) == 1 and h[0]["value"] == -3.54 and h[0]["observed_at"] == "2026-07-31",
          "French: a preamble line with commas is not a header; -99.99 is missing; "
          "the annual table is not read as months")
    check(french.crsp_vintage(factors) == "CRSP 202608", "French: CRSP vintage logged")
    ind = ("  Average Value Weighted Returns -- Monthly\n,Agric,Chips\n202608,1.5,-2.0\n"
           "\n  Sum of BE / Sum of ME\n,Agric,Chips\n2026,0.5,0.12\n")
    ir = french.rows_from_industries(ind, LM_CANON, "observed")
    be = [r for r in ir if r["registry_key"] == "french.ind49_beme"]
    check(len(be) == 2 and be[0]["observed_at"] == "2026-06-30",
          "French: BE/ME dated at the June formation, never a future 31 December")
    check(shiller._month(2026.1) == "2026-10-01" and shiller._month(2026.09)
          == "2026-09-01", "Shiller: 2026.1 is OCTOBER, not January")
    hdr = [[""] * 13 for _ in range(4)]
    hdr[2][12], hdr[3][12] = "P/E10 or", "CAPE"
    sh = shiller.rows_from_table(hdr + [["Date"] + [""] * 12,
                                        [2026.09, 7631.47, "", "", 333.9, 0, 4.75,
                                         0, 0, 0, 0, 0, 40.58]], LM_CANON, "observed")
    cape = [r for r in sh if r["registry_key"] == "shiller.cape"]
    check(cape and cape[0]["value"] == 40.58 and not any(
        r["registry_key"] == "shiller.sp_earnings" for r in sh),
          "Shiller: CAPE from column 12; a blank (lagged) earnings cell is skipped")
    hdr[3][12] = "Something else"
    hdr[2][12] = ""
    try:
        shiller.rows_from_table(hdr + [["Date"]], LM_CANON, "observed")
        bad("Shiller: a moved CAPE column raised")
    except ValueError:
        ok("Shiller: a moved CAPE column raises rather than storing the wrong series")
    wbt = [["Updated on September 02, 2026"],
           [None, "Total Index", "Energy", "Non-energy **", "Precious Metals"],
           [None, None, None, None, None, "Metals  & Minerals"],
           ["2026M08", 121.8, 118.4, 128.6, 345.2, 146.2]]
    w, upd = worldbank.rows_from_table(wbt, LM_CANON, "observed")
    wm = {r["registry_key"]: r["value"] for r in w}
    check(wm.get("worldbank.cmo_metals") == 146.2 and wm.get("worldbank.cmo_precious")
          == 345.2 and w[0]["observed_at"] == "2026-08-01" and upd,
          "World Bank: columns found by label (double space tolerated), month start")
    dtab = [["Date updated:", 46027.0], ["Industry Name", "Number of firms",
            "EV/EBITDA", "EV/EBITDA"], ["Chips", 70.0, 20.0, 25.0]]
    d, ed = damodaran.rows_from_table(dtab, {"damodaran.ev_ebitda": ("EV/EBITDA", -1)},
                                      LM_CANON, "observed")
    check(ed == "2026-01-05" and d[0]["value"] == 25.0,
          "Damodaran: edition date from 'Date updated'; the ALL-FIRMS (last) "
          "EV/EBITDA block")
    lb = lbma.rows_from_json([{"d": "2026-09-25", "v": [4261.05, 3200, 3700]},
                              {"d": "2026-09-26", "v": [None, None, None]}],
                             LM_CANON, "observed")
    check(len(lb) == 1 and lb[0]["value"] == 4261.05, "LBMA: USD leg; empty day skipped")
    fr = finra.rows_from_table(
        [["Year-Month", "Debit Balances in Customers' Securities Margin Accounts",
          "Free Credit Balances in Customers' Cash Accounts",
          "Free Credit Balances in Customers' Securities Margin Accounts"],
         ["2026-08", 1453832.0, 207641.0, 217499.0]], LM_CANON, "observed")
    fd = {r["registry_key"]: r for r in fr}
    check(fd["finra.margin_debit"]["value"] == 1453832.0 * 1e6
          and fd["finra.margin_debit"]["observed_at"] == "2026-08-31",
          "FINRA: millions to dollars, month-end (a balance, not an average)")
    ps = proshares.rows_from_csv(
        "Date,ProShares Name,Ticker,NAV,Prior NAV,NAV Change (%),NAV Change ($),"
        "Shares Outstanding (000),Assets Under Management\n"
        "09/25/2026,ProShares UltraPro QQQ,TQQQ,79.5962,78.6662,1.18,0.93,486100,"
        "38691712820\n", "TQQQ", LM_CANON, "observed")
    pd_ = {r["registry_key"]: r["value"] for r in ps}
    check(pd_["levetf.shares_outstanding"] == 486100000.0
          and pd_["levetf.aum"] == 38691712820.0,
          "ProShares: shares in thousands to shares; AUM as published")
    # the logged vintage is deduplicated like any other row
    db = temp_store()
    orig = french.http_get_response
    try:
        import io as _io
        import zipfile as _zip

        def zipped(text):
            buf = _io.BytesIO()
            with _zip.ZipFile(buf, "w") as z:
                z.writestr("x.csv", text)
            return buf.getvalue()
        french.http_get_response = lambda url, *a, **k: (
            zipped(factors if url == french.FACTORS else ind), LM_HEADERS)
        r1 = french.pull(db=db)
        v = db.conn.execute("SELECT value_text FROM observations WHERE "
                            "registry_key=?", (pub.VINTAGE_KEY,)).fetchall()
        r2 = french.pull(db=db)
        check(r1["status"] == pub.OK and [x[0] for x in v] == ["CRSP 202608"]
              and r2["written"] == 0,
              "reference.file_vintage is written once per edition and not again")
    finally:
        french.http_get_response = orig
        db.close()
    from altdata import config, derived
    check(config.ENABLED_SOURCES.get("eia") is True, "the eia switch is ON")
    check(derived.staleness_allowance("damodaran.pe_forward")[0]
          == derived.FREQ_SESSIONS["annual"],
          "an annual table gets the annual staleness allowance, not the monthly")
    check("external" in feeds.FEEDS and set(feeds.EXTERNAL_WRITERS) >= {
        "umich", "french", "damodaran", "shiller", "worldbank", "lbma", "finra",
        "proshares"}, "the external writers run as the `external` feed")


def group_p() -> None:
    import importlib.util
    from altdata.sources import fundamentals as fu
    from altdata.sources import yfinance_source as yf_src
    print(f"{LINE}\nP. SYMBOLS, FUNDAMENTALS AND THE ST-2 MANUAL KEYS\n{LINE}")
    added = {"IVW", "IVE", "IWF", "IWD", "VWO", "ACWX", "EMXC", "GUNR", "CNH=X"}
    check(added <= set(yf_src.SYMBOLS) and {"GLD", "EEM"} <= set(yf_src.SYMBOLS),
          "the nine ST-2 symbols are on the price pass; GLD and EEM were already")
    check(yf_src.SYMBOLS["CNH=X"] == "mkt_usdcnh" and "CNH=X"
          in yf_src.CONTINUOUS_SYMBOLS,
          "USD/CNH is declared continuous: its US-holiday quotes are real")
    # fundamentals
    frames = {"cashflow": {"Operating Cash Flow": {"2026-03-31": 26.0e9},
                           "Capital Expenditure": {"2026-03-31": -44.2e9}},
              "balance": {"Total Debt": {"2026-03-31": 209.9e9, "2025-12-31": float("nan")},
                          "Cash And Cash Equivalents": {"2026-03-31": 101.8e9,
                                                        "2025-12-31": 86.8e9},
                          "Inventory": {"2026-03-31": 36.5e9},
                          "Net Debt": {"2026-03-31": 17.3e9}},
              "income": {"Cost Of Revenue": {"2026-06-30": float("nan"),
                                             "2026-03-31": 87.5e9}}}
    v = fu.values_from_frames("AMZN", frames)
    nd = v.get((fu.key("AMZN", "net_debt"), "2026-03-31"))
    check(nd is not None and abs(nd - 108.1e9) < 1e6
          and (fu.key("AMZN", "net_debt"), "2025-12-31") not in v,
          "net debt = Total Debt - Cash from one balance sheet (not yfinance's "
          "sparse Net Debt row); a NaN leg writes nothing")
    check((fu.key("AMZN", "cogs"), "2026-06-30") not in v
          and v[(fu.key("AMZN", "capex"), "2026-03-31")] == -44.2e9,
          "a NaN cell writes nothing; capex keeps its published (negative) sign")
    check(fu.key("META", "inventory") not in fu.KEYS
          and fu.key("MU", "inventory") in fu.KEYS,
          "inventory keys exist only for the filers that report it")
    now = "2026-05-10T00:00:00.000000+00:00"
    acc = "2026-05-01T20:05:00.000000+00:00"
    rows = fu.stamp({(fu.key("AMZN", "cogs"), "2026-03-31"): 87.5e9,
                     (fu.key("AMZN", "capex"), "2026-03-31"): -44.2e9,
                     (fu.key("AMZN", "cogs"), "2025-12-31"): 110e9},
                    {"2026-03-31": acc, "2025-12-31": "2026-02-06T21:00:00Z"},
                    {(fu.key("AMZN", "capex"), "2026-03-31")}, now)
    got = {(r["registry_key"], r["observed_at"]): (r["available_at"],
                                                   r["availability_kind"]) for r in rows}
    check(got[(fu.key("AMZN", "cogs"), "2026-03-31")] == (acc, "observed"),
          "a quarter first seen within 14 days of its 10-Q takes the acceptance "
          "instant")
    check(got[(fu.key("AMZN", "capex"), "2026-03-31")] == (now, "ingest_instant"),
          "an already-held quarter (a possible restatement) takes the write instant")
    check(got[(fu.key("AMZN", "cogs"), "2025-12-31")] == (now, "ingest_instant"),
          "a quarter filed long before first capture (the backfill) takes the "
          "write instant -- never a restated value dated at the original filing")
    # manual keys
    spec = importlib.util.spec_from_file_location(
        "manual_input", REPO / "tools" / "manual_input.py")
    mi = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mi)
    want = {"manual.aaii_stocks_pct", "manual.aaii_bonds_pct", "manual.aaii_cash_pct",
            "manual.msci_em_usd", "manual.msci_em_local", "manual.msci_world_usd",
            "manual.msci_acwi_exus_usd", "manual.oecd_days_cover",
            "manual.global_visible_stocks_bbl", "manual.cofer_usd_share",
            "manual.cofer_usd_share_constant_fx", "manual.gold_share_total_reserves",
            "manual.mu_hbm_share", "manual.dram_contract_dir",
            "manual.g4_issuance_gap_gdp", "manual.panda_bond_issuance",
            "manual.state_bank_dollar_selling"}
    keys = mi.manual_keys()
    check(want <= set(keys) and all(keys[k].get("units") and keys[k].get("description")
                                    for k in want),
          f"the 17 ST-2 manual keys are registered with units and a description "
          f"(missing {sorted(want - set(keys))})")
    check(keys["manual.aaii_stocks_pct"].get("delta_unit") == "pp",
          "a share in percent moves in points (delta_unit pp), not basis points")
    fd, path = tempfile.mkstemp(suffix=".sqlite", dir=_TMP)
    os.close(fd)
    os.unlink(path)
    mi.write("manual.state_bank_dollar_selling", "Yes", "2020-01-02",
             "fixture -- G-21 by hand", db_path=path)
    mi.write("manual.dram_contract_dir", "down", "2020-01-31", "fixture", db_path=path)
    with observations.ObservationStore(path) as db:
        sb = db.latest_as_of("manual.state_bank_dollar_selling")
        dr = db.latest_as_of("manual.dram_contract_dir")
    check(sb["value_num"] == 1.0 and sb["value_text"] == "fixture -- G-21 by hand"
          and dr["value_num"] == -1.0,
          "a coded label stores its code (yes=1, down=-1) and keeps the note")
    for bad_value in ("maybe", "1"):
        try:
            mi.write("manual.state_bank_dollar_selling", bad_value, "2020-01-02",
                     "n", db_path=path)
            bad(f"refuses the label {bad_value!r}")
        except mi.Refused:
            ok(f"refuses the label {bad_value!r} -- only yes / no / unknown")


def main() -> int:
    print(f"{LINE}\nThe published-file writers (ST-1, ST-2) -- offline\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g,
              group_h, group_i, group_j, group_k, group_l, group_m, group_o,
              group_p, group_n):
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
