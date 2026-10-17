"""
Validation gate for AQ-3 part 1: the series writers for the Quarterly's first
chapters (change order of 10 Oct 2026, section 11 row AQ-3, and section 10A's
flows-and-positioning standard).

    python tools/validate_aq3_series.py

No network and no box: every fetch is replaced by a fixture built here in the
source's own shape (synthetic values, never a cut of a publisher's file -- the
GLD archive forbids redistribution), every write goes to a temporary store, and
the session clock is pinned to 11 Oct 2026.

  A  CFTC        the disaggregated and TFF reports: long, short, net per
                 category; each as a share of open interest (the OI-share
                 arithmetic); a response without the category columns is a
                 changed shape; the legacy series untouched; the pull writes all
                 three reports, available Friday 15:30 ET
  B  FRED H.10   the scan tier: every pair registered with a declared unit, none
                 already held; the baht alone in its own list under namespace
                 thailand, trigger_eligible false; all in the one FRED pull
  C  RIGS        the EIA workbook parsed by its Sourcekey row; a workbook for
                 another series refused; monthly counts written with available_at
  D  GLD         the archive read BY CONTENT from the inbox (a file of any name;
                 a non-archive .xlsx beside it ignored); shares = ounces / ounces
                 per share; the flow a share-count change; holiday rows skipped;
                 with no inbox file a disallowing robots.txt fetches nothing and
                 the run is STALE with the reason
  E  ISHARES     IAU, SLV, IBIT read by key-fact name from the page; the first
                 run writes no flow, the next the share-count change
  F  SHFE        the weekly page read by content (title date, each metal's block
                 and its 总计 row); a missing metal raises; a 404 week falls back
                 to the Thursday; a run with no page read is STALE
  G  CNH         the New York close from hourly bars: the last bar opening
                 before 17:00 New York, weekends skipped, today's open session
                 never stored, available at the bar's end
  H  COMPUTED    the 3-2-1 crack's arithmetic; the CNY fix gap in bp and the
                 band position; CNH against the fix and against CNY; each row
                 available no earlier than its latest input
  I  STALE       with good rows held, every writer's failed fetch writes nothing
                 and keeps what is stored
  J  REGISTERED  every key registered with its fields, never trigger_eligible;
                 every source in source_registry with its implemented_by; every
                 writer in its feeds group, its KEYS readable from source; no
                 systemd unit added
"""

from __future__ import annotations

import datetime as dt
import io
import os
import sys
import zipfile
from pathlib import Path

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

_TMP = gate_mkdtemp(prefix="validate_aq3_")
os.environ["ALTDATA_STORE"] = str(Path(_TMP) / "store")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import yaml                                                    # noqa: E402

from altdata import config, derived, feeds, market_features as mf  # noqa: E402
from altdata import observations, session                     # noqa: E402
from altdata.sources import (cfets, cftc, cnh, eia_rigs, ishares_trusts,  # noqa: E402
                             shfe, spdr_gld)
from altdata.sources._base import FetchError                  # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
TODAY = "2026-10-11"


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def temp_store() -> observations.ObservationStore:
    import tempfile
    fd, path = tempfile.mkstemp(suffix=".sqlite", dir=_TMP)
    os.close(fd)
    os.unlink(path)
    return observations.ObservationStore(path)


def count(db, key=None) -> int:
    if key:
        return db.conn.execute("SELECT COUNT(*) FROM observations WHERE "
                               "registry_key=?", (key,)).fetchone()[0]
    return db.conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]


def values(db, key, inst=None) -> dict:
    q = ("SELECT observed_at, value_num, available_at FROM observations WHERE "
         "registry_key=?" + (" AND instrument=?" if inst else ""))
    args = (key, inst) if inst else (key,)
    return {str(d)[:10]: (v, a) for d, v, a in db.conn.execute(q, args)}


# The session clock, pinned: the fixtures are dated before it, and the writers'
# "no row after today" and write-window rules read it.
session.session_date = lambda *a, **k: TODAY
session.session_date_obj = lambda *a, **k: dt.date.fromisoformat(TODAY)
_real_utc = session.utc_iso
session.utc_iso = lambda *a, **k: "2026-10-11T22:00:00.000000+00:00"


def _xlsx(sheets: dict) -> bytes:
    """A real, minimal .xlsx (as validate_official_sources builds one)."""
    strings: list = []

    def sidx(s: str) -> int:
        if s not in strings:
            strings.append(s)
        return strings.index(s)

    def col(i: int) -> str:
        s, i = "", i + 1
        while i:
            i, r = divmod(i - 1, 26)
            s = chr(65 + r) + s
        return s
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    xmls = []
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
        xmls.append(f'<worksheet xmlns="{ns}"><sheetData>{"".join(body)}'
                    f'</sheetData></worksheet>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        names = list(sheets)
        z.writestr("xl/workbook.xml", f'<workbook xmlns="{ns}" xmlns:r="{rns}">'
                   "<sheets>" + "".join(f'<sheet name="{n}" sheetId="{i+1}" '
                                        f'r:id="rId{i+1}"/>'
                                        for i, n in enumerate(names))
                   + "</sheets></workbook>")
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<Relationships xmlns="http://schemas.openxmlformats.org/'
                   'package/2006/relationships">'
                   + "".join(f'<Relationship Id="rId{i+1}" Target="worksheets/'
                             f'sheet{i+1}.xml" Type="x"/>' for i in range(len(names)))
                   + "</Relationships>")
        for i, x in enumerate(xmls):
            z.writestr(f"xl/worksheets/sheet{i+1}.xml", x)
        z.writestr("xl/sharedStrings.xml", f'<sst xmlns="{ns}">' + "".join(
            f"<si><t>{s}</t></si>" for s in strings) + "</sst>")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# A. CFTC
# ---------------------------------------------------------------------------
DIS_REC = {"cftc_contract_market_code": "088691",
           "report_date_as_yyyy_mm_dd": "2026-09-29T00:00:00.000",
           "open_interest_all": "400000",
           "prod_merc_positions_long": "20000", "prod_merc_positions_short": "60000",
           "swap_positions_long_all": "80000", "swap__positions_short_all": "180000",
           "m_money_positions_long_all": "120000", "m_money_positions_short_all": "40000",
           "other_rept_positions_long": "100000", "other_rept_positions_short": "50000"}
TFF_REC = {"cftc_contract_market_code": "099741",
           "report_date_as_yyyy_mm_dd": "2026-09-29T00:00:00.000",
           "open_interest_all": "800000",
           "dealer_positions_long_all": "100000", "dealer_positions_short_all": "300000",
           "asset_mgr_positions_long": "400000", "asset_mgr_positions_short": "100000",
           "lev_money_positions_long": "80000", "lev_money_positions_short": "200000",
           "other_rept_positions_long": "60000", "other_rept_positions_short": "40000"}
LEG_REC = {"cftc_contract_market_code": "097741",
           "report_date_as_yyyy_mm_dd": "2026-09-29T00:00:00.000",
           "noncomm_positions_long_all": "50000", "noncomm_positions_short_all": "80000",
           "open_interest_all": "300000"}


def group_a() -> None:
    print(f"\n{LINE}\nA. CFTC -- DISAGGREGATED AND TFF, SCALED TO OPEN INTEREST\n{LINE}")
    rows = cftc.category_rows([DIS_REC], "dis", cftc.DISAGG_CONTRACTS,
                              cftc.DISAGG_CATEGORIES)
    by = {r["registry_key"]: r["value"] for r in rows}
    check(by["cftc.dis_managed_money_long"] == 120000
          and by["cftc.dis_managed_money_net"] == 80000
          and by["cftc.dis_swap_short"] == 180000
          and by["cftc.dis_open_interest"] == 400000
          and all(r["instrument"] == "GOLD" for r in rows),
          "the disaggregated record: long, short and net per category (the "
          "two-underscore swap-short column read), instrument GOLD")
    check(by["cftc.dis_managed_money_long_oi"] == 30.0
          and by["cftc.dis_managed_money_net_oi"] == 20.0
          and by["cftc.dis_prod_merc_net_oi"] == -10.0
          and abs(by["cftc.dis_swap_short_oi"] - 45.0) < 1e-9,
          "the OI share: 120,000 of 400,000 is 30.0%, net 80,000 is 20.0%, "
          "producer net -40,000 is -10.0%")
    t = {r["registry_key"]: r["value"] for r in cftc.category_rows(
        [TFF_REC], "tff", cftc.TFF_CONTRACTS, cftc.TFF_CATEGORIES)}
    check(t["cftc.tff_asset_mgr_net"] == 300000 and t["cftc.tff_asset_mgr_net_oi"] == 37.5
          and t["cftc.tff_lev_money_net_oi"] == -15.0 and t["cftc.tff_open_interest"] == 800000,
          "TFF: asset managers net 300,000 of 800,000 = 37.5%; leveraged funds -15.0%")
    check(cftc.oi_share(5, 0) is None and cftc.oi_share(None, 10) is None,
          "no OI, or no position, is no share -- never a zero")
    try:
        cftc.category_rows([LEG_REC | {"cftc_contract_market_code": "088691"}],
                           "dis", cftc.DISAGG_CONTRACTS, cftc.DISAGG_CATEGORIES)
        raised = False
    except ValueError:
        raised = True
    check(raised, "a response carrying none of the categories' columns raises: a "
                  "changed shape, not a quiet week")
    check(cftc.LEGACY_KEYS == ["cftc.noncomm_long", "cftc.noncomm_short",
                               "cftc.noncomm_net", "cftc.open_interest"]
          and cftc.KEYS[:4] == cftc.LEGACY_KEYS,
          "the legacy non-commercial keys are untouched and first")

    def fake(url, params=None, **k):
        if (params or {}).get("$offset"):
            return []
        code = (params or {}).get("cftc_contract_market_code")
        if url == cftc.DISAGG_URL:
            return [dict(DIS_REC, cftc_contract_market_code=code)]
        if url == cftc.TFF_URL:
            return [dict(TFF_REC, cftc_contract_market_code=code)]
        return [dict(LEG_REC, cftc_contract_market_code=code)]
    saved = cftc.http_get_json
    cftc.http_get_json = fake
    db = temp_store()
    try:
        s = cftc.pull(db=db)
        mm = values(db, "cftc.dis_managed_money_net_oi", "COPPER")
        aud = values(db, "cftc.tff_asset_mgr_long", "AUD")
        check(s["status"] == "OK" and mm.get("2026-09-29", (None,))[0] == 20.0
              and aud and count(db, "cftc.noncomm_net") == len(cftc.CONTRACTS)
              and mm["2026-09-29"][1].startswith("2026-10-02T19:30:00"),
              f"the pull writes the three reports -- every contract of each -- "
              f"available Friday 15:30 ET ({s['status']}, {s.get('written')} rows)")
    finally:
        cftc.http_get_json = saved
        db.close()


# ---------------------------------------------------------------------------
# B. FRED H.10
# ---------------------------------------------------------------------------
def group_b() -> None:
    print(f"\n{LINE}\nB. THE FX SCAN TIER FROM FRED H.10\n{LINE}")
    scan, thai = config.FRED_FX_SCAN_SERIES, config.FRED_THAILAND_SERIES
    held = {"DEXUSEU", "DEXJPUS", "DEXCHUS", "DEXMXUS"}
    ids = [s.fred_id for s in scan]
    check(len(scan) == 18 and not (set(ids) & held) and len(set(ids)) == 18
          and all(i.startswith("DEX") for i in ids),
          f"eighteen H.10 pairs, none the store already held ({len(scan)})")
    check([s.fred_id for s in thai] == ["DEXTHUS"] and "DEXTHUS" not in ids,
          "the baht is alone in its own list, not in the scan tier")
    pulled = {s.fred_id for s in config.FRED_PULL_SERIES}
    check(set(ids) | {"DEXTHUS"} <= pulled
          and all(f"fred.{s.key}" in feeds.fred_keys() for s in scan + thai),
          "all nineteen ride the one FRED pull and its freshness roster")
    bad = [s.key for s in scan + thai if derived.DELTA_UNITS.get(s.units) != "percent"
           or not derived.registry_entry(f"fred.{s.key}")]
    check(not bad, f"every pair is registered and moves in percent of itself ({bad})")
    th = derived.registry_entry("fred.usd_thb")
    leak = [s.key for s in scan if derived.registry_entry(f"fred.{s.key}").get(
        "namespace") == "thailand"]
    check(th.get("namespace") == "thailand" and th.get("trigger_eligible") is False
          and not leak,
          "fred.usd_thb is under namespace thailand, never trigger_eligible; no scan "
          "pair is")
    usd_per = {s.key for s in scan if s.units == "$"}
    check(usd_per == {"usd_aud", "usd_nzd", "usd_gbp"},
          "the quote convention is the unit: AUD, NZD and GBP are US dollars per unit, "
          "the rest units per dollar")


# ---------------------------------------------------------------------------
# C. Rigs
# ---------------------------------------------------------------------------
class _Sheet:
    def __init__(self, rows):
        self.rows, self.nrows = rows, len(rows)

    def row_values(self, r):
        return self.rows[r]


class _Book:
    def __init__(self, rows):
        self._s = _Sheet(rows)

    def sheet_by_name(self, name):
        if name != "Data 1":
            raise KeyError(name)
        return self._s


def rig_table(sid: str, n: float) -> list:
    return [["Back to Contents", f"Data 1: {sid}"], ["Sourcekey", sid],
            ["Date", "Rigs (Count)"], [46157.0, n], [46188.0, n + 3],
            [46218.0, ""], [46249.0, n + 5]]


def group_c() -> None:
    print(f"\n{LINE}\nC. RIGS -- BAKER HUGHES' MONTHLY COUNT, AS THE EIA REPUBLISHES IT\n{LINE}")
    s = eia_rigs.series_from_table(rig_table("E_ERTRRO_XR0_NUS_C", 400.0),
                                   "E_ERTRRO_XR0_NUS_C")
    check(s == {"2026-05-15": 400.0, "2026-06-15": 403.0, "2026-08-15": 405.0},
          "the sheet's dated counts, the blank month skipped")
    try:
        eia_rigs.series_from_table(rig_table("E_ERTRRG_XR0_NUS_C", 1.0),
                                   "E_ERTRRO_XR0_NUS_C")
        refused = False
    except ValueError:
        refused = True
    check(refused, "a workbook naming another series in its Sourcekey row is refused")
    import xlrd
    saved_open, saved_get = xlrd.open_workbook, eia_rigs.http_get_response
    sid_of = {}

    def get(url, **k):
        sid = url.rsplit("/", 1)[1][:-5]
        sid_of["last"] = sid
        return sid.encode(), {"last-modified": "Fri, 25 Sep 2026 14:00:00 GMT"}
    xlrd.open_workbook = lambda file_contents=None, **k: _Book(
        rig_table(file_contents.decode(), 500.0))
    eia_rigs.http_get_response = get
    db = temp_store()
    try:
        r = eia_rigs.pull(db=db)
        tot = values(db, "eia.rigs_total")
        check(r["status"] == "OK" and tot["2026-08-15"][0] == 505.0
              and tot["2026-08-15"][1].startswith("2026-09-25T14:00:00")
              and count(db, "eia.rigs_gas") == 3,
              "the pull writes the three series, available at the workbook's "
              "Last-Modified (observed)")
    finally:
        xlrd.open_workbook, eia_rigs.http_get_response = saved_open, saved_get
        db.close()


# ---------------------------------------------------------------------------
# D. GLD
# ---------------------------------------------------------------------------
GLD_HEAD = ["Date", "Closing Price", "Ounces of Gold per Share", "NAV/Share",
            "Indicative Price", "Mid point", "Premium/Discount", "Daily Share Volume",
            "Total Ounces of Gold in the Trust", "Tonnes of Gold",
            "Total Net Asset Value in the Trust"]


def gld_archive() -> bytes:
    rows = [GLD_HEAD,
            ["28-Sep-2026", 370.0, 0.0917, 1, 1, 1, 0, 1, 917000.0, 28.52, 1],
            ["29-Sep-2026", "US Holiday"] + ["US Holiday"] * 9,
            ["30-Sep-2026", 371.0, 0.0917, 1, 1, 1, 0, 1, 926170.0, 28.81, 1],
            ["01-Oct-2026", 372.0, 0.0916, 1, 1, 1, 0, 1, 915084.0, 28.46, 1]]
    return _xlsx({"Disclaimer": [["SPDR GOLD SHARES HISTORICAL DATA"]],
                  "US GLD Historical Archive": rows})


def group_d() -> None:
    print(f"\n{LINE}\nD. GLD -- THE ARCHIVE, BY CONTENT, FROM THE INBOX\n{LINE}")
    rows = spdr_gld.rows_from_archive(gld_archive(), "2026-10-02T00:00:00+00:00",
                                      "ingest_instant")
    by = {(r["registry_key"], r["observed_at"]): r["value"] for r in rows}
    check(by[("etf.gld_shares", "2026-09-28")] == 10_000_000
          and by[("etf.gld_shares", "2026-09-30")] == 10_100_000
          and by[("etf.gld_tonnes", "2026-10-01")] == 28.46,
          "shares outstanding = total ounces / ounces per share (917,000 / 0.0917 = "
          "10,000,000); tonnes are the archive's own column")
    check(by[("etf.gld_share_flow", "2026-09-30")] == 100_000
          and by[("etf.gld_share_flow", "2026-10-01")] == -110_000
          and ("etf.gld_share_flow", "2026-09-28") not in by
          and not any(d == "2026-09-29" for _k, d in by),
          "the flow is the share-count change across the holiday (+100,000, then "
          "-110,000), never dollars; the holiday row and the first day carry none")
    inbox = Path(_TMP) / "inbox_etf"
    inbox.mkdir()
    (inbox / "download (3).bin").write_bytes(gld_archive())
    (inbox / "GLD_archive.xlsx").write_bytes(_xlsx({"Sheet1": [["Not", "it"], [1, 2]]}))
    (inbox / "notes.txt").write_text("hello", encoding="utf-8")
    saved_dir = spdr_gld.INBOX_DIR
    spdr_gld.INBOX_DIR = str(inbox)
    db = temp_store()
    try:
        r = spdr_gld.pull(db=db)
        check(r["status"] == "OK" and count(db, "etf.gld_shares") == 3
              and count(db, "etf.gld_share_flow") == 2,
              "the inbox file that reads as the archive is used, whatever its name; "
              "the misnamed non-archive beside it is ignored")
    finally:
        db.close()
    for p in inbox.iterdir():
        p.unlink()
    saved_text = spdr_gld.http_get_text
    saved_resp = spdr_gld.http_get_response
    fetched = []
    spdr_gld.http_get_text = lambda url, **k: "User-agent: *\nDisallow: /\n"
    spdr_gld.http_get_response = lambda url, **k: fetched.append(url) or (b"", {})
    db = temp_store()
    try:
        r = spdr_gld.pull(db=db)
        check(r["status"] == "STALE" and "disallows" in r["reason"]
              and "inbox" in r["reason"] and not fetched and count(db) == 0,
              f"with no inbox file, robots.txt's Disallow: / fetches nothing; STALE "
              f"with the reason ({r['reason'][:70]}...)")
    finally:
        spdr_gld.http_get_text, spdr_gld.http_get_response = saved_text, saved_resp
        spdr_gld.INBOX_DIR = saved_dir
        db.close()


# ---------------------------------------------------------------------------
# E. iShares
# ---------------------------------------------------------------------------
def fact_json(name: str, label: str, value: str, asof: str) -> str:
    return ('{"visible":true,"label":"' + label + '","formattedValue":"' + value
            + '","sortOrder":46,"prefix":null,"infoBubble":"One metric tonne is '
              'equivalent to 1,000 kilograms.","formattedAsOfDate":"' + asof
            + '","name":"' + name + '"}')


def ishares_page(shares: str, asof: str, metal: bool = True) -> str:
    facts = [fact_json("sharesOutstanding", "Shares Outstanding", shares, asof)]
    if metal:
        facts += [fact_json("ounces", "Ounces in Trust", "1,000,000.50", asof),
                  fact_json("tonnes", "Tonnes in Trust", "31.10", asof)]
    raw = '<div data-facts="{' + ",".join(facts) + '}"></div>'
    return raw.replace('"', "&quot;").replace('<div data-facts=&quot;', '<div data-facts="')


def group_e() -> None:
    print(f"\n{LINE}\nE. ISHARES -- IAU, SLV, IBIT BY KEY-FACT NAME\n{LINE}")
    v, day = ishares_trusts.fact(ishares_page("793,450,000", "Oct 09, 2026"),
                                 "sharesOutstanding")
    check(v == 793_450_000 and day == "2026-10-09",
          "a key fact is read by its name, with its as-of date")
    pages = {"1": {"iau": ishares_page("100,000,000", "Oct 08, 2026"),
                   "slv": ishares_page("50,000,000", "Oct 08, 2026"),
                   "ibit": ishares_page("1,000,000,000", "Oct 08, 2026", metal=False)},
             "2": {"iau": ishares_page("100,250,000", "Oct 09, 2026"),
                   "slv": ishares_page("49,900,000", "Oct 09, 2026"),
                   "ibit": ishares_page("1,002,000,000", "Oct 09, 2026", metal=False)}}
    run = {"n": "1"}

    def get(url, **k):
        t = next(t for t, (u, _f) in ishares_trusts.TRUSTS.items() if u == url)
        return pages[run["n"]][t]
    saved = ishares_trusts.http_get_text
    ishares_trusts.http_get_text = get
    db = temp_store()
    try:
        r1 = ishares_trusts.pull(db=db)
        first_flow = count(db, "etf.iau_share_flow")
        run["n"] = "2"
        r2 = ishares_trusts.pull(db=db)
        flows = {t: values(db, f"etf.{t}_share_flow").get("2026-10-09", (None,))[0]
                 for t in ("iau", "slv", "ibit")}
        check(r1["status"] == "OK" and first_flow == 0 and r2["status"] == "OK"
              and flows == {"iau": 250_000.0, "slv": -100_000.0, "ibit": 2_000_000.0}
              and values(db, "etf.slv_tonnes")["2026-10-09"][0] == 31.1
              and count(db, "etf.ibit_oz") == 0,
              f"the first run writes no flow; the next writes each trust's share-count "
              f"change ({flows}); IBIT carries shares only")
        run["n"] = "1"
        pages["1"]["slv"] = "<html>a redesigned page</html>"
        r3 = ishares_trusts.pull(db=db)
        check(r3["status"] == "STALE" and "sharesOutstanding" in r3["reason"],
              "a page without its key facts is a changed shape: STALE, nothing written")
    finally:
        ishares_trusts.http_get_text = saved
        db.close()


# ---------------------------------------------------------------------------
# F. SHFE
# ---------------------------------------------------------------------------
def _tr(*cells) -> str:
    return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"


def shfe_page(day: str, drop: str = "") -> str:
    blocks = []
    for name, base in (("铝", 266000), ("铜", 58000), ("锌", 146000), ("铜(BC)", 999),
                       ("黄金", 7000)):
        if name == drop:
            continue
        unit = "单位：千克" if name == "黄金" else "单位：吨"
        blocks += [_tr(name, unit), _tr("上海", "某仓库", 1, 1, 1, 1, 0, 0, 9, 9, 0),
                   _tr("合计", 10, 5, 11, 6, 1, 1, 9, 9, 0),
                   _tr("总计", base - 100, base // 3, base, base // 4, 100, 0, 9, 9, 0)]
    head = [_tr(f"{day} 2026年 第(39)期,总第1406期"),
            _tr("地区", "仓库", "上周库存", "本周库存", "库存增减", "可用库容量")]
    return "<table>" + "".join(head + blocks) + "</table>"


def group_f() -> None:
    print(f"\n{LINE}\nF. SHFE -- THE WEEKLY STOCK PAGE, BY CONTENT\n{LINE}")
    rows = shfe.rows_from_page(shfe_page("2026-10-09"))
    by = {(r["registry_key"], r["instrument"]): r["value"] for r in rows}
    check(by == {("shfe.stocks_t", "ALUMINIUM"): 266000.0,
                 ("shfe.warrants_t", "ALUMINIUM"): 66500.0,
                 ("shfe.stocks_t", "COPPER"): 58000.0,
                 ("shfe.warrants_t", "COPPER"): 14500.0,
                 ("shfe.stocks_t", "ZINC"): 146000.0,
                 ("shfe.warrants_t", "ZINC"): 36500.0}
          and all(r["observed_at"] == "2026-10-09" for r in rows)
          and rows[0]["available_at"].startswith("2026-10-09T08:00:00"),
          "each metal's 总计 row by its block, in any order; bonded copper and gold "
          "not read; the title's date; available 16:00 Beijing")
    try:
        shfe.rows_from_page(shfe_page("2026-10-09", drop="锌"))
        raised = False
    except ValueError as exc:
        raised = "ZINC" in str(exc)
    check(raised, "a page missing a metal's block raises, naming it")
    served = {"20261008": shfe_page("2026-10-08")}
    asked = []

    def get(url, **k):
        ymd = url.split("weeklystock_")[1][:8]
        asked.append(ymd)
        if ymd in served:
            return served[ymd].encode("utf-8"), {}
        if ymd == "20261009":
            raise FetchError(f"HTTP 404 from {url}: not found")
        raise FetchError(f"Giving up on {url} after 2 retries: connection reset")
    saved_get, saved_pause = shfe.http_get_response, shfe.PAUSE_SECONDS
    shfe.http_get_response, shfe.PAUSE_SECONDS = get, 0
    db = temp_store()
    try:
        r = shfe.pull(db=db)
        check(r["status"] == "OK" and asked[:2] == ["20261009", "20261008"]
              and values(db, "shfe.stocks_t", "COPPER").get("2026-10-08")
              and count(db) == 6,
              "a 404 Friday falls back to the Thursday; the weeks that reset are kept "
              "from earlier runs and the run writes what it read")
        served.clear()
        r2 = shfe.pull(db=db)
        check(r2["status"] == "STALE" and "no SHFE weekly page" in r2["reason"]
              and count(db) == 6,
              "a run that reads no page is STALE and the stored weeks stay")
    finally:
        shfe.http_get_response, shfe.PAUSE_SECONDS = saved_get, saved_pause
        db.close()


# ---------------------------------------------------------------------------
# G. CNH
# ---------------------------------------------------------------------------
def group_g() -> None:
    print(f"\n{LINE}\nG. CNH -- THE NEW YORK CLOSE FROM HOURLY BARS\n{LINE}")
    utc = dt.timezone.utc
    bars = []
    # Thursday 8 Oct and Friday 9 Oct (EDT, UTC-4): bars on the hour, 18:00 UTC
    # (14:00 NY) to 23:00 UTC (19:00 NY); Saturday 10 Oct one stray bar; Monday
    # 12 Oct a session in progress at the pinned now.
    for day, base in (("2026-10-08", 6.70), ("2026-10-09", 6.69)):
        for h in range(18, 24):
            bars.append((dt.datetime.fromisoformat(f"{day}T{h:02d}:00:00").replace(
                tzinfo=utc), base + h / 1000))
    bars.append((dt.datetime(2026, 10, 10, 14, tzinfo=utc), 6.5))
    bars.append((dt.datetime(2026, 10, 12, 14, tzinfo=utc), 6.6))
    now = dt.datetime(2026, 10, 12, 15, tzinfo=utc)
    rows = cnh.closes_from_bars(bars, now)
    by = {r["observed_at"]: r for r in rows}
    check(sorted(by) == ["2026-10-08", "2026-10-09"]
          and abs(by["2026-10-09"]["value"] - (6.69 + 20 / 1000)) < 1e-9
          and by["2026-10-09"]["available_at"].startswith("2026-10-09T21:00:00"),
          "the close is the last bar opening before 17:00 New York (20:00 UTC, the "
          "16:00 bar), available at its end, 21:00 UTC; the weekend bar is skipped and "
          "Monday's session in progress is not stored")
    est = cnh.closes_from_bars([(dt.datetime(2026, 12, 1, 21, tzinfo=utc), 6.8),
                                (dt.datetime(2026, 12, 1, 22, tzinfo=utc), 6.9)],
                               dt.datetime(2026, 12, 2, 12, tzinfo=utc))
    check(len(est) == 1 and est[0]["value"] == 6.8,
          "in winter (EST, UTC-5) the 21:00 UTC bar is 16:00 New York -- the close; "
          "22:00 UTC is after the cut")


# ---------------------------------------------------------------------------
# H. Computed
# ---------------------------------------------------------------------------
def group_h() -> None:
    print(f"\n{LINE}\nH. THE CRACK, THE FIX GAP AND THE BAND\n{LINE}")
    check(abs(mf.crack_321(80.0, 2.50, 3.00) - 32.0) < 1e-9,
          "the 3-2-1 crack: (2 x 2.50 x 42 + 3.00 x 42 - 3 x 80) / 3 = $32.00 a barrel")
    check(abs(cfets.gap_bp(7.20, 7.10) - 140.8450704) < 1e-6
          and abs(cfets.band_position(7.242, 7.10) - 1.0) < 1e-9
          and abs(cfets.band_position(6.958, 7.10) + 1.0) < 1e-9
          and cfets.band_position(7.10, 7.10) == 0.0,
          "the gap: 7.20 against 7.10 is +140.8 bp; the band position is +1 at the "
          "fix x 1.02, -1 at x 0.98, 0 at the fix")
    db = temp_store()
    try:
        def put(key, day, v, av):
            db.write_many([{"registry_key": key, "instrument": None, "observed_at": day,
                            "available_at": av, "value": v, "source": "fixture",
                            "availability_kind": "reconstructed"}])
        put("yfinance.mkt_wti_front", "2026-10-08", 80.0, "2026-10-08T20:30:00+00:00")
        put("yfinance.mkt_rb_front", "2026-10-08", 2.50, "2026-10-08T20:31:00+00:00")
        put("yfinance.mkt_ho_front", "2026-10-08", 3.00, "2026-10-08T21:10:00+00:00")
        put("yfinance.mkt_rb_front", "2026-10-07", 2.40, "2026-10-07T20:31:00+00:00")
        put("cfets.cny_fix", "2026-10-08", 7.10, "2026-10-08T01:15:00+00:00")
        put("yfinance.mkt_usdcny", "2026-10-08", 7.20, "2026-10-08T22:00:00+00:00")
        put("cnh.usdcnh", "2026-10-08", 7.21, "2026-10-08T21:00:00+00:00")
        rows = mf.aq3_rows(db)
        by = {r["registry_key"]: r for r in rows}
        check(len([r for r in rows if r["registry_key"] == "calc.crack_321"]) == 1
              and by["calc.crack_321"]["value"] == 32.0
              and by["calc.crack_321"]["available_at"].startswith("2026-10-08T21:10:00"),
              "the crack is written only on a session all three legs closed, available "
              "at the latest leg's instant")
        check(round(by["calc.cny_fix_gap_bp"]["value"], 4) == 140.8451
              and round(by["calc.cny_band_position"]["value"], 4) == 0.7042
              and round(by["calc.cnh_fix_gap_bp"]["value"], 4) == 154.9296
              and round(by["calc.cnh_cny_bp"]["value"], 4) == 13.8889
              and by["calc.cny_fix_gap_bp"]["available_at"].startswith(
                  "2026-10-08T22:00:00"),
              "CNY +140.8 bp off the fix, 0.70 of the way to the weak edge; CNH +154.9 bp "
              "off the fix and +13.9 bp over CNY; each available at its later input")
        check(set(mf.AQ3_FEATURES) == {r["registry_key"] for r in rows}
              and all(derived.registry_entry(k) for k in mf.AQ3_FEATURES),
              "every computed series is declared and registered")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# I. STALE, not empty
# ---------------------------------------------------------------------------
def group_i() -> None:
    print(f"\n{LINE}\nI. STALE, NOT EMPTY\n{LINE}")
    held_row = {"instrument": None, "observed_at": "2026-09-01",
                "available_at": "2026-09-02T00:00:00+00:00", "value": 1.0,
                "source": "fixture", "availability_kind": "reconstructed"}

    def boom(*a, **k):
        raise FetchError("simulated outage")
    cases = [(cftc, "http_get_json", "cftc.dis_open_interest"),
             (eia_rigs, "http_get_response", "eia.rigs_oil"),
             (ishares_trusts, "http_get_text", "etf.iau_shares"),
             (shfe, "http_get_response", "shfe.stocks_t"),
             (spdr_gld, "http_get_text", "etf.gld_shares")]
    bad = []
    for mod, fn, key in cases:
        saved = getattr(mod, fn)
        setattr(mod, fn, boom)
        db = temp_store()
        try:
            db.write_many([dict(held_row, registry_key=key)])
            pause = getattr(mod, "PAUSE_SECONDS", None)
            if pause is not None:
                mod.PAUSE_SECONDS = 0
            r = mod.pull(db=db)
            if pause is not None:
                mod.PAUSE_SECONDS = pause
            if not (r["status"] == "STALE" and r["written"] == 0 and count(db) == 1
                    and r["last_observed"].get(key)):
                bad.append(mod.SOURCE)
        finally:
            setattr(mod, fn, saved)
            db.close()
    saved_bars = cnh.fetch_frames
    cnh.fetch_frames = lambda period: (_ for _ in ()).throw(RuntimeError("no bars"))
    db = temp_store()
    try:
        db.write_many([dict(held_row, registry_key="cnh.usdcnh")])
        r = cnh.pull(db=db)
        if not (r["status"] == "STALE" and count(db) == 1):
            bad.append("yahoo_cnh")
    finally:
        cnh.fetch_frames = saved_bars
        db.close()
    check(not bad, f"every writer's failed fetch writes nothing, keeps the stored row "
                   f"and reports it -- cftc, eia_rigs, ishares_trusts, shfe, spdr_gld, "
                   f"yahoo_cnh ({bad})")


# ---------------------------------------------------------------------------
# J. Registered and wired
# ---------------------------------------------------------------------------
NEW_WRITERS = {"eia_rigs": "official", "spdr_gld": "external",
               "ishares_trusts": "external", "shfe": "external", "cnh": "external"}


def group_j() -> None:
    print(f"\n{LINE}\nJ. REGISTERED, WIRED, AND NO UNIT ADDED\n{LINE}")
    import importlib
    mods = {w: importlib.import_module(f"altdata.sources.{w}") for w in NEW_WRITERS}
    keys = (cftc.DISAGG_KEYS + cftc.TFF_KEYS + [k for m in mods.values() for k in m.KEYS]
            + list(mf.AQ3_FEATURES))
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    metrics = reg.get("metrics") or {}
    fields = ("source", "mechanism_group", "native_horizon", "units",
              "information_half_life", "revision_policy", "observation_type",
              "description")
    missing = [k for k in keys if not all((metrics.get(k) or {}).get(f) for f in fields)]
    eligible = [k for k in keys if (metrics.get(k) or {}).get("trigger_eligible")]
    check(not missing and not eligible,
          f"every new key ({len(keys)}) has a full registry entry and none is "
          f"trigger_eligible ({missing[:3]}{eligible[:3]})")
    src = yaml.safe_load((REPO / "source_registry.yaml").read_text(
        encoding="utf-8"))["sources"]
    srcs = [m.SOURCE for m in mods.values()]
    gone = [s for s in srcs if not (src.get(s) or {}).get("implemented_by")
            or not (REPO / src[s]["implemented_by"]).is_file()]
    check(not gone and all(metrics[k]["source"] in src for k in keys),
          f"every source is in source_registry with its implemented_by ({gone})")
    groups = {"official": feeds.OFFICIAL_WRITERS, "external": feeds.EXTERNAL_WRITERS}
    misplaced = [w for w, g in NEW_WRITERS.items() if w not in groups[g]]
    statics = [w for w, m in mods.items() if feeds.static_keys(w) != list(m.KEYS)]
    check(not misplaced and not statics and feeds.static_keys("cftc") == cftc.KEYS,
          f"each writer sits in its feeds group and its KEYS read from source "
          f"({misplaced}{statics})")
    roster = set(feeds.official_keys()) | set(feeds.external_keys())
    check(set(keys) - set(mf.AQ3_FEATURES) <= roster,
          "and every written key is on the freshness roster")
    units = [p.name for p in (REPO / "deploy" / "systemd").iterdir()]
    added = [u for u in units if any(w.replace("_", "") in u.replace("-", "").replace(
        "_", "") for w in NEW_WRITERS)]
    check(not added, f"no systemd unit was added: the writers ride the existing "
                     f"pulls ({added})")


def main() -> int:
    print(f"{LINE}\nAQ-3 part 1 -- the Quarterly's series writers (fixtures, no "
          f"network)\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g,
              group_h, group_i, group_j):
        g()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
