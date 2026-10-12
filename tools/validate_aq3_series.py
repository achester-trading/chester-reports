"""
Validation gate for AQ-3 parts 1 and 2: the series writers for the Quarterly's
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
  D2 GLD DAILY   State Street's NAV-history workbook read by its header in any
                 sheet; www.ssga.com's robots.txt read each run, fetched when it
                 allows and not when it disallows; shares the workbook's own; the
                 forward ounces decayed at the expense ratio (the arithmetic
                 fixtured); a newer archive re-anchors as a revision
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

  PART 2 (11 Oct 2026):
  K  RATES       the Bundesbank's daily Bund read by its columns (another series
                 refused), available next weekday 12:00 Frankfurt; the ECB's
                 monthly Bund/OAT/BTP by REF_AREA; SLOOS in pp, the FRED legs
                 (CRE delinquency, Case-Shiller, policy rates, gilt) pulled
  L  NBS         releases found on the index by title; the 70-city table by its
                 caption (exactly 70 cities), the counts and mean computed; starts
                 and sales from the parent rows; available at the release hour
  M  COMPUTED    the ratios (XLRE, VNQ, EFA, VEA to SPY; HEFA to EFA); the
                 mortgage, UST-JGB, OAT-Bund and BTP-Bund spreads; the hedged
                 yields' arithmetic, a monthly leg carried at most 70 days
  N  THAILAND    BoT's MPC table (text and serial dates; the API only with
                 BOT_API_KEY, "no key" otherwise); TPSO's CPI (Buddhist-Era years);
                 MOTS's Grand Total; NESDC's SA chain-volume GDP from a zip of CSVs
                 by content; the SET forward-only; every Thai key under namespace
                 thailand, never trigger_eligible
  O  STALE       every part 2 writer's failed fetch writes nothing
  P  REGISTERED  full entries, sources, feeds groups, the roster, the basket of
                 58; no unit; the BoT key read from the environment only
"""

from __future__ import annotations

import datetime as dt
import io
import os
import re
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
from altdata.sources import (bot, bundesbank, cfets, cftc, cnh, ecb_irs,  # noqa: E402
                             eia_rigs, ishares_trusts, mots, nbs, nesdc, shfe,
                             spdr_gld, thai_set, tpso)
from altdata.sources import yfinance_source as yf_src         # noqa: E402
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
    saved_nav = spdr_gld.navhist
    spdr_gld.navhist = lambda: (None, "fixture: the daily workbook is offline")
    db = temp_store()
    try:
        r = spdr_gld.pull(db=db)
        check(r["status"] == "OK" and count(db, "etf.gld_shares") == 3
              and count(db, "etf.gld_share_flow") == 2,
              "the inbox file that reads as the archive is used, whatever its name; "
              "the misnamed non-archive beside it is ignored (the daily workbook "
              "offline: the archive alone)")
    finally:
        spdr_gld.navhist = saved_nav
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
# D2. GLD -- the daily workbook, the forward approximation, the re-anchor
# ---------------------------------------------------------------------------
NAV_HEAD = ["Date", "NAV", "Shares Outstanding", "Total Net Assets"]
NAV_SHARES = {"28-Sep-2026": 10_000_000, "30-Sep-2026": 10_100_000,
              "01-Oct-2026": 10_000_000, "02-Oct-2026": 10_150_000,
              "05-Oct-2026": 10_150_000, "08-Oct-2026": 10_250_000,
              "09-Oct-2026": 10_300_000}
SSGA_ALLOWS = ("User-agent: *\nDisallow: /weblogic/strategyDetailsPublic\n"
               "Disallow: /fd\nDisallow: /search-results\n")
SSGA_DISALLOWS = SSGA_ALLOWS + "Disallow: /us/en/intermediary/library-content/\n"


def gld_navhist(sheet: str = "navhist") -> bytes:
    """State Street's NAV-history workbook in its shape: a fund-name preamble,
    the header, rows NEWEST FIRST, a disclaimer line beneath."""
    rows = [["Fund Name:", "SPDR Gold Shares"], ["Ticker Symbol:", "GLD"], [],
            NAV_HEAD]
    for d in sorted(NAV_SHARES, key=lambda x: dt.datetime.strptime(x, "%d-%b-%Y"),
                    reverse=True):
        rows.append([d, 380.0, float(NAV_SHARES[d]), 380.0 * NAV_SHARES[d]])
    rows.append(["The information contained above is for illustrative purposes."])
    return _xlsx({sheet: rows})


def gld_archive_b() -> bytes:
    """A NEWER archive, through 9 Oct: the exact ounces the approximation stood
    in for."""
    rows = [GLD_HEAD,
            ["28-Sep-2026", 370.0, 0.0917, 1, 1, 1, 0, 1, 917000.0, 28.52, 1],
            ["30-Sep-2026", 371.0, 0.0917, 1, 1, 1, 0, 1, 926170.0, 28.81, 1],
            ["01-Oct-2026", 372.0, 0.0916, 1, 1, 1, 0, 1, 915084.0, 28.46, 1],
            ["02-Oct-2026", 372.0, 0.0916, 1, 1, 1, 0, 1, 929740.0, 28.92, 1],
            ["05-Oct-2026", 372.0, 0.0916, 1, 1, 1, 0, 1, 929700.0, 28.92, 1],
            ["08-Oct-2026", 372.0, 0.0916, 1, 1, 1, 0, 1, 938860.0, 29.20, 1],
            ["09-Oct-2026", 372.0, 0.0916, 1, 1, 1, 0, 1, 943440.0, 29.34, 1]]
    return _xlsx({"US GLD Historical Archive": rows})


def group_d2() -> None:
    print(f"\n{LINE}\nD2. GLD -- THE DAILY WORKBOOK, THE APPROXIMATION, THE RE-ANCHOR\n{LINE}")
    pts = spdr_gld.navhist_points(gld_navhist("Sheet9"))
    check(pts[0] == ("2026-09-28", 10_000_000) and pts[-1] == ("2026-10-09", 10_300_000)
          and len(pts) == 7,
          "the workbook is read by its header (Date, Shares Outstanding) in any sheet, "
          "past the fund-name preamble and the disclaimer, oldest first")
    try:
        spdr_gld.navhist_points(_xlsx({"navhist": [["Date", "NAV"], ["09-Oct-2026", 1]]}))
        refused = False
    except ValueError:
        refused = True
    check(refused, "a workbook without Shares Outstanding is refused, whatever its name")

    # -- the robots verdict, both ways --------------------------------------
    saved = (spdr_gld.http_get_text, spdr_gld.http_get_response)
    fetched: list = []

    def resp(url, **k):
        fetched.append(url)
        return gld_navhist(), {"last-modified": "Fri, 09 Oct 2026 22:13:48 GMT"}
    try:
        spdr_gld.http_get_response = resp
        spdr_gld.http_get_text = lambda url, **k: SSGA_ALLOWS
        got, why = spdr_gld.navhist()
        check(got and fetched == [spdr_gld.NAVHIST_URL] and why is None
              and got[1].startswith("2026-10-09T22:13:48") and got[2] == "observed",
              "www.ssga.com's robots.txt (no rule matching the path; nearest "
              "Disallow: /fd) lets the workbook be fetched; it is available at its "
              "Last-Modified (observed)")
        fetched.clear()
        spdr_gld.http_get_text = lambda url, **k: SSGA_DISALLOWS
        got, why = spdr_gld.navhist()
        check(got is None and not fetched and "disallows" in why
              and "/us/en/intermediary/library-content/" in why,
              f"a robots.txt that disallows the path fetches nothing and says which "
              f"rule ({why[:70]}...)")
    finally:
        spdr_gld.http_get_text, spdr_gld.http_get_response = saved

    # -- the decay arithmetic ----------------------------------------------
    er = config.GLD_EXPENSE_RATIO
    ops8 = spdr_gld.ounces_per_share(0.0916, "2026-10-01", "2026-10-09", 0.004)
    ops365 = spdr_gld.ounces_per_share(0.0916, "2026-10-01", "2027-10-01", 0.004)
    check(er["ratio"] == 0.0040 and "ssga.com" in er["source"] and er["read"]
          and abs(ops8 - 0.0916 * (1 - 0.004 / 365) ** 8) < 1e-15
          and abs(ops365 / 0.0916 - 0.9960079) < 1e-6
          and spdr_gld.ounces_per_share(0.0916, "2026-10-01", "2026-10-01") == 0.0916,
          f"ounces per share decay at the expense ratio ({er['ratio']:.2%}, from the "
          f"fund page) a calendar day at a time: 8 days x(1 - 0.004/365)^8, a year "
          f"{ops365 / 0.0916:.6f} of the anchor; none on the anchor's own day")
    arch = (spdr_gld.archive_points(gld_archive()), "2026-10-02T00:00:00+00:00",
            "ingest_instant")
    nav = (spdr_gld.navhist_points(gld_navhist()), "2026-10-09T22:13:48+00:00",
           "observed")
    rows = spdr_gld.combine(arch, nav, ratio=0.004)
    by = {(r["registry_key"], r["observed_at"]): r for r in rows}
    oz9 = 10_300_000 * 0.0916 * (1 - 0.004 / 365) ** 8
    check(by[("etf.gld_oz", "2026-10-01")]["value"] == 915084.0
          and by[("etf.gld_tonnes", "2026-10-01")]["value"] == 28.46
          and abs(by[("etf.gld_oz", "2026-10-09")]["value"] - oz9) < 0.001
          and abs(by[("etf.gld_tonnes", "2026-10-09")]["value"]
                  - oz9 / 32150.7466) < 0.0001
          and by[("etf.gld_oz", "2026-10-09")]["available_at"] == nav[1]
          and ("etf.gld_oz", "2026-09-29") not in by,
          f"through the archive's last day the ounces and tonnes are its own; after "
          f"it, shares x the anchor's ounces per share decayed (9 Oct: "
          f"{oz9:,.1f} oz, {oz9 / 32150.7466:.4f} t), available when both sources are")
    check(by[("etf.gld_shares", "2026-10-01")]["value"] == 10_000_000
          and by[("etf.gld_share_flow", "2026-10-01")]["value"] == -100_000
          and by[("etf.gld_share_flow", "2026-10-02")]["value"] == 150_000
          and by[("etf.gld_shares", "2026-10-01")]["availability_kind"] == "observed",
          "shares are the workbook's own count wherever it has the day (1 Oct: "
          "10,000,000, not the archive's derived 9,990,000), and the flow is that "
          "count's change")
    only = spdr_gld.combine(None, nav)
    check(not any(r["registry_key"] in ("etf.gld_oz", "etf.gld_tonnes") for r in only)
          and sum(r["registry_key"] == "etf.gld_shares" for r in only) == 7,
          "with no archive yet: shares and flows only -- no ounces without an anchor")

    # -- the pull, then the re-anchor --------------------------------------
    inbox = Path(_TMP) / "inbox_etf_d2"
    inbox.mkdir()
    a = inbox / "historical-archive.xlsx"
    a.write_bytes(gld_archive())
    os.utime(a, (1_791_000_000, 1_791_000_000))
    saved_dir, saved_nav = spdr_gld.INBOX_DIR, spdr_gld.navhist
    spdr_gld.INBOX_DIR = str(inbox)
    spdr_gld.navhist = lambda: (nav, None)
    db = temp_store()
    try:
        r1 = spdr_gld.pull(db=db)
        approx = {x["observed_at"][:10]: x["value_num"] for x in db.as_of("etf.gld_oz")}
        check(r1["status"] == "OK" and len(approx) == 7
              and abs(approx["2026-10-09"] - round(oz9, 3)) < 1e-6,
              "the pull writes the archive's exact ounces and the approximation past "
              "it (four days)")
        b = inbox / "download (1).xlsx"
        b.write_bytes(gld_archive_b())
        # Its mtime (8 Oct 22:53, Drive's upload time, which rclone keeps) is
        # EARLIER than the workbook's Last-Modified the approximation carries (9
        # Oct 22:13): the sweep-and-run race. The re-anchor must still win.
        os.utime(b, (1_791_500_000, 1_791_500_000))
        r2 = spdr_gld.pull(db=db)
        vint = db.conn.execute("SELECT COUNT(*) FROM observations WHERE registry_key="
                               "'etf.gld_oz' AND observed_at LIKE '2026-10-09%'"
                               ).fetchone()[0]
        now = {x["observed_at"][:10]: x["value_num"] for x in db.as_of("etf.gld_oz")}
        shares_v = db.conn.execute("SELECT COUNT(*) FROM observations WHERE "
                                   "registry_key='etf.gld_shares'").fetchone()[0]
        check(r2["status"] == "OK" and vint == 2 and now["2026-10-09"] == 943440.0
              and now["2026-10-01"] == 915084.0 and shares_v == 7,
              f"a newer archive in the inbox re-anchors: 9 Oct's approximation "
              f"({approx['2026-10-09']:,.1f}) is revised to the archive's exact "
              f"943,440 oz as a new vintage -- even when the file is older than the "
              f"workbook read beside it; unchanged days and the shares are not "
              f"rewritten")
    finally:
        spdr_gld.INBOX_DIR, spdr_gld.navhist = saved_dir, saved_nav
        db.close()

    # -- the two sources together, robots both ways ------------------------
    for p in inbox.iterdir():
        p.unlink()
    saved = (spdr_gld.http_get_text, spdr_gld.http_get_response)
    spdr_gld.INBOX_DIR = str(inbox)
    fetched.clear()
    spdr_gld.http_get_text = lambda url, **k: (SSGA_ALLOWS if "ssga" in url
                                               else "User-agent: *\nDisallow: /\n")
    spdr_gld.http_get_response = resp
    db = temp_store()
    try:
        r = spdr_gld.pull(db=db)
        check(r["status"] == "OK" and fetched == [spdr_gld.NAVHIST_URL]
              and count(db, "etf.gld_shares") == 7 and count(db, "etf.gld_oz") == 0
              and "etf.gld_oz" in r["keys_without_rows"],
              "with no archive and the API disallowed, the workbook still writes the "
              "shares and the flow; ounces wait for the archive, named in the summary")
    finally:
        spdr_gld.http_get_text, spdr_gld.http_get_response = saved
        spdr_gld.INBOX_DIR = saved_dir
        db.close()


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


# ===========================================================================
# AQ-3 PART 2 (11 Oct 2026): the remaining writers
# ===========================================================================
def bbk_csv(points: list) -> str:
    head = ("DATAFLOW;BBK_STD_FREQ;TIME_PERIOD;OBS_VALUE;BBK_ID;BBK_UNIT;"
            "BBK_TITLE;OBS_STATUS")
    rows = [f"BBK:BBSIS(1.0);D;{d};{v};{bundesbank.SERIES_ID};Prozent;"
            f"Zinsstrukturkurve 10,0 Jahr(e);" for d, v in points]
    return "﻿" + "\n".join([head] + rows) + "\n"


def ecb_csv(points: dict) -> str:
    head = "KEY,FREQ,REF_AREA,IR_TYPE,TIME_PERIOD,OBS_VALUE,OBS_STATUS"
    rows = [f"IRS.M.{c}.L.L40.CI.0000.EUR.N.Z,M,{c},L,{m},{v},A"
            for c, pts in points.items() for m, v in pts]
    return "\n".join([head] + rows) + "\n"


def _refused(fn, *args) -> bool:
    try:
        fn(*args)
    except ValueError:
        return True
    return False


def group_k() -> None:
    print(f"\n{LINE}\nK. GLOBAL RATES: THE BUNDESBANK'S DAILY BUND, THE ECB'S MONTHLY "
          f"BUND/OAT/BTP, FRED'S GILT\n{LINE}")
    now = dt.datetime(2026, 10, 11, 22, tzinfo=dt.timezone.utc)
    rows = bundesbank.rows_from_csv(
        bbk_csv([("2026-10-08", "2.61"), ("2026-10-09", "2.64"), ("2026-10-10", ".")]),
        now)
    by = {r["observed_at"]: r for r in rows}
    check(sorted(by) == ["2026-10-08", "2026-10-09"] and by["2026-10-09"]["value"] == 2.64
          and by["2026-10-08"]["available_at"].startswith("2026-10-09T10:00:00")
          and by["2026-10-09"]["available_at"][:19] == "2026-10-11T22:00:00"
          and all(r["availability_kind"] == "reconstructed" for r in rows),
          "the Bund read by its columns, a non-trading '.' skipped; available the next "
          "weekday 12:00 Frankfurt (Thursday's on Friday 10:00 UTC), never after the "
          "write instant")
    other = bbk_csv([("2026-10-08", "2.61")]).replace(bundesbank.SERIES_ID, "BBSIS.D.X")
    check(_refused(bundesbank.rows_from_csv, other, now)
          and _refused(bundesbank.rows_from_csv, "DATE;VALUE\n2026-10-08;2.6\n", now),
          "a response naming another series, or without TIME_PERIOD/OBS_VALUE, is "
          "refused")
    pts = {"DE": [("2026-07", "2.60"), ("2026-08", "2.70")],
           "FR": [("2026-07", "3.30"), ("2026-08", "3.42")],
           "IT": [("2026-07", "3.55"), ("2026-08", "3.61")]}
    rows = ecb_irs.rows_from_csv(ecb_csv(pts), "2026-09-10T08:00:00+00:00", "observed")
    got = {(r["registry_key"], r["observed_at"]): r["value"] for r in rows}
    check(len(rows) == 6 and got[("ecb.irs_10y_fr", "2026-08-01")] == 3.42
          and got[("ecb.irs_10y_it", "2026-07-01")] == 3.55
          and all(r["available_at"] == "2026-09-10T08:00:00+00:00" for r in rows),
          "the ECB's IRS rows stored by their REF_AREA, dated the month's first day, "
          "available at the response's Last-Modified")
    check(_refused(ecb_irs.rows_from_csv,
                   ecb_csv({"DE": pts["DE"], "ES": [("2026-08", "3.0")]}), "x", "observed")
          and _refused(ecb_irs.rows_from_csv, ecb_csv({"DE": pts["DE"]}), "x", "observed"),
          "a country not asked for, or a missing one, is refused")
    sl = {s.key: s for s in config.FRED_SLOOS_SERIES}
    ax = {s.key: s for s in config.FRED_AQ3_SERIES}
    pulled = {s.fred_id for s in config.FRED_PULL_SERIES}
    check({s.fred_id for s in sl.values()} == {"DRTSCILM", "DRTSCIS", "SUBLPDRCSC",
                                                "SUBLPDRCSN", "SUBLPDRCSM"}
          and all(derived.delta_unit_for(f"fred.{k}")[0] == "pp" for k in sl)
          and {s.fred_id for s in ax.values()} == {"DRCRELEXFACBS", "CSUSHPINSA",
                                                   "DFF", "ECBDFR", "IRSTCI01JPM156N",
                                                   "IRLTLT01GBM156N", "DTWEXEMEGS"}
          and derived.delta_unit_for("fred.dxy_em")[0] == "percent"
          and {s.fred_id for s in list(sl.values()) + list(ax.values())} <= pulled
          and all(derived.registry_entry(f"fred.{k}") for k in list(sl) + list(ax)),
          "SLOOS (C&I large and small, the three CRE lines) moves in percentage "
          "points, not bp; the CRE delinquency, Case-Shiller, the policy rates and "
          "the monthly gilt and the EM dollar index (DTWEXEMEGS, moving in percent) "
          "are in the one FRED pull and registered")


def _cell(x) -> str:
    return f'<td><p><span style="font-family:Arial">{x}</span></p></td>'


def city70_page(n: int = 70) -> str:
    cities = [(f"City{i}", 99.5 if i < 40 else (100.0 if i < 50 else 100.3),
               97.0 if i < 60 else 100.5) for i in range(n)]
    body = "".join("<tr>" + "".join(_cell(c) for c in (a[0], a[1], a[2], 99.0,
                                                        b[0], b[1], b[2], 99.0)) + "</tr>"
                   for a, b in zip(cities[0::2], cities[1::2]))
    return ("<p><span>Sales Price Indices of Second-hand Residential Buildings</span>"
            "</p><table><tr>" + _cell("Cities") + "</tr></table>"
            "<p><span>Sales Price Indices of Newly Constructed Commercial Residential "
            "Buildings in 70 Large and Medium-Sized Cities</span></p><p>Table I</p>"
            "<div class=\"ue_table\"><table><tr>" + _cell("Cities") + _cell("M/M")
            + "</tr>" + body + "</table></div>")


def redev_page() -> str:
    return ("<p><span>Table 1 Real Estate Development and Sales from January to August "
            "2026</span></p><table>"
            + "".join("<tr>" + _cell(a) + _cell(b) + _cell(c) + "</tr>" for a, b, c in (
                ("Indicator", "Absolute Value", "Growth Rate Y/Y (%)"),
                ("Floor space of buildings newly started (10,000 sq.m)", "29894", "-24.8"),
                ("Of which: Residential buildings", "21840", "-25.4"),
                ("Floor space of newly built commercial buildings sold (10,000 sq.m)",
                 "49880", "−12.1"),
                ("Sales of newly built commercial buildings (100 million yuan)",
                 "47,470", "-13.0"))) + "</table>")


NBS_INDEX = ('<a href="./" title="Latest Releases">x</a>'
             '<a target="_blank" title="Sales Prices of Commercial Residential Buildings '
             'in 70 Medium and Large-sized Cities in August 2026" '
             'href="./202609/t20260915_1965314.html">Sales Prices...</a>'
             '<a target="_blank" title="Investment in Real Estate Development from '
             'January to August 2026" href="./202609/t20260916_1965342.html">I...</a>'
             '<a target="_blank" title="Purchasing Managers’ Index for September '
             '2026" href="./202610/t20261008_1965466.html">P...</a>')


def group_l() -> None:
    print(f"\n{LINE}\nL. CHINA'S PROPERTY: THE NBS RELEASES, FOUND BY TITLE, READ BY "
          f"CONTENT\n{LINE}")
    rel = [(t_, u, nbs.release_month(t_)) for t_, u in
           nbs.releases(NBS_INDEX, nbs.INDEX_URLS[0])]
    kinds = {k[0]: u for _, u, k in rel if k}
    check(len(rel) == 3 and set(kinds) == {"city70", "redev"}
          and kinds["city70"].endswith("/202609/t20260915_1965314.html")
          and all(k[1] == "2026-08-01" for _, _, k in rel if k),
          "the index's releases matched on the title attribute (spaces normalised), "
          "the reference month read from it; the PMI is passed over")
    rows = nbs.city70_rows(city70_page(), "2026-08-01", "2026-09-15T01:30:00+00:00")
    v = {r["registry_key"]: r["value"] for r in rows}
    exp_mm = round((40 * 99.5 + 10 * 100.0 + 20 * 100.3) / 70 - 100, 4)
    check(v["nbs.city70_new_mm_down"] == 40 and v["nbs.city70_new_mm_up"] == 20
          and v["nbs.city70_new_yy_down"] == 60
          and abs(v["nbs.city70_new_mm_avg"] - exp_mm) < 1e-9,
          "the 70-city table found by its caption, not its position: 40 cities down "
          "on the month, 20 up, 10 flat (neither); 60 below a year earlier; the "
          "unweighted mean change computed here (the English edition prints none)")
    check(_refused(nbs.city70_rows, city70_page(68), "2026-08-01", "x"),
          "a table without exactly 70 cities is refused")
    rows = nbs.redev_rows(redev_page(), "2026-08-01", "2026-09-16T02:00:00+00:00")
    v = {r["registry_key"]: r["value"] for r in rows}
    check(v == {"nbs.re_starts_ytd": 29894.0, "nbs.re_starts_ytd_yoy": -24.8,
                "nbs.re_sold_area_ytd": 49880.0, "nbs.re_sold_area_ytd_yoy": -12.1,
                "nbs.re_sales_ytd": 47470.0, "nbs.re_sales_ytd_yoy": -13.0},
          "starts, floor space sold and sales value, year to date with their y/y, "
          "from the parent rows (never 'Of which'), a minus sign of either kind")
    check(nbs.release_available(kinds["city70"], nbs.CITY70_HOUR)
          == "2026-09-15T01:30:00.000000+00:00"
          and nbs.release_available(kinds["redev"], nbs.REDEV_HOUR)
          == "2026-09-16T02:00:00.000000+00:00",
          "available at the release date in its URL, 09:30 and 10:00 Beijing")
    saved = nbs.http_get_response
    pages = {nbs.INDEX_URLS[0]: NBS_INDEX, nbs.INDEX_URLS[1]: "",
             "https://www.stats.gov.cn/english/PressRelease/202609/t20260915_1965314.html":
                 city70_page(),
             "https://www.stats.gov.cn/english/PressRelease/202609/t20260916_1965342.html":
                 redev_page()}
    nbs.http_get_response = lambda url, **k: (pages[url].encode("utf-8"), {})
    db = temp_store()
    try:
        r = nbs.pull(db=db)
        ok = (r["status"] != "STALE" and count(db, "nbs.re_starts_ytd") == 1
              and count(db, "nbs.city70_new_mm_down") == 1)
    finally:
        nbs.http_get_response = saved
        db.close()
    check(ok, "the pull reads the index's two pages and writes both releases")


def group_m() -> None:
    print(f"\n{LINE}\nM. COMPUTED: THE RATIOS, THE SPREADS, THE HEDGED YIELDS\n{LINE}")
    check(abs(mf.hedged_yield(2.60, 4.10, 2.00) - 0.50) < 1e-12
          and abs(mf.spread_bp(0.50, 4.20) + 370.0) < 1e-9,
          "the hedged yield: a 2.60% Bund less (4.10% EFFR - 2.00% ECB deposit) is "
          "0.50%; against a 4.20% Treasury, -370 bp")

    def put(db, key, day, v, av):
        db.write_many([{"registry_key": key, "instrument": None, "observed_at": day,
                        "available_at": av, "value": v, "source": "fixture",
                        "availability_kind": "reconstructed"}])
    db = temp_store()
    try:
        d, a = "2026-10-08", "2026-10-08T21:00:00+00:00"
        for k, v in (("yfinance.mkt_spy", 500.0), ("yfinance.mkt_xlre", 40.0),
                     ("yfinance.mkt_vnq", 90.0), ("yfinance.mkt_efa", 80.0),
                     ("yfinance.mkt_vea", 50.0), ("yfinance.mkt_hefa", 36.0),
                     ("fred.yield_10y", 4.20), ("fred.mortgage_30y", 6.30),
                     ("mof.jgb_10y", 1.60), ("bbk.bund_10y", 2.60),
                     ("fred.effr_daily", 4.10), ("fred.ecb_dfr", 2.00)):
            put(db, k, d, v, a)
        put(db, "fred.jp_call_rate", "2026-08-01", 0.50, "2026-10-09T13:00:00+00:00")
        put(db, "fred.jp_call_rate", "2026-05-01", 0.40, "2026-07-09T13:00:00+00:00")
        for c, v in (("de", 2.70), ("fr", 3.42), ("it", 3.61)):
            put(db, f"ecb.irs_10y_{c}", "2026-08-01", v, "2026-09-10T08:00:00+00:00")
        rows = mf.aq3b_rows(db)
    finally:
        db.close()
    v = {r["registry_key"]: r for r in rows}
    val = lambda k: round(v[k]["value"], 6)                     # noqa: E731
    check(val("calc.xlre_spy") == 0.08 and val("calc.vnq_spy") == 0.18
          and val("calc.efa_spy") == 0.16 and val("calc.vea_spy") == 0.1
          and val("calc.hefa_efa") == 0.45,
          "XLRE, VNQ, EFA and VEA against SPY, HEFA against EFA: the close ratios")
    check(val("calc.mortgage_spread_10y_bp") == 210.0
          and val("calc.us_jgb_10y_bp") == 260.0
          and val("calc.oat_bund_bp") == 72.0 and val("calc.btp_bund_bp") == 91.0,
          "the mortgage spread 6.30 - 4.20 = 210 bp; UST-JGB 260 bp; OAT-Bund 72 bp "
          "and BTP-Bund 91 bp from the one ECB method")
    check(val("calc.bund_hedged_yield") == 0.5
          and val("calc.bund_hedged_spread_bp") == -370.0
          and val("calc.jgb_hedged_yield") == -2.0
          and val("calc.jgb_hedged_spread_bp") == -620.0
          and v["calc.jgb_hedged_yield"]["available_at"].startswith("2026-10-09T13:00:00"),
          "the Bund hedged 0.50% (-370 bp to the Treasury); the JGB hedged with "
          "August's call rate carried forward (-2.00%, -620 bp), available when that "
          "monthly print was")
    stale = temp_store()
    try:
        put(stale, "mof.jgb_10y", d, 1.6, a)
        put(stale, "fred.yield_10y", d, 4.2, a)
        put(stale, "fred.effr_daily", d, 4.1, a)
        put(stale, "fred.jp_call_rate", "2026-05-01", 0.4, a)
        none = [r for r in mf.aq3b_rows(stale)
                if r["registry_key"].startswith("calc.jgb_hedged")]
    finally:
        stale.close()
    check(not none, f"a monthly leg older than {mf.CARRY_DAYS} days is not carried: "
                    f"no hedged yield on a stale policy rate")
    check(set(mf.AQ3B_FEATURES) == set(v)
          and all(derived.registry_entry(k) for k in mf.AQ3B_FEATURES)
          and all("APPROXIMATION" in derived.registry_entry(k).get("description", "")
                  for k in mf.AQ3B_FEATURES if "hedged" in k),
          "every computed series is declared and registered; the hedged yields are "
          "labelled an approximation, with their method")


def bot_table() -> list:
    return [["ครั้งที่", "วันที่", "Date", "การประชุม", "Meeting", "มติ กนง.", "Decision",
             "อัตราดอกเบี้ยนโยบาย\nPolicy rate\n(%)", "Balance of votes"],
            [None, None, None, None, None, None, None, None, "Hold"],
            ["1/2556", "28-29 พ.ค. 56", "28-29 May 2013", "กนง.", "MPC", "", "Cut 25 bps", 2.5, None],
            ["1/2560", 42774.0, "8-Feb-2017", "กนง.", "MPC", "", "Hold", 1.5, None],
            ["4/2569", 46260.0, 46260.0, "กนง.", "MPC", "", "Hold", 1.0, "66/"],
            [None] * 9,
            ["หมายเหตุ: 1/ remarks", None, None, None, None, None, None, None, None]]


def tpso_payload() -> list:
    def month(m, idx, yy, typ="TG"):
        return {"month": m, "type": typ, "index": idx, "change": 0.1, "changeYear": yy}
    return [{"commodityCode": "00010", "commodityNameEN": "FOOD", "years": []},
            {"commodityCode": "00000", "commodityNameEN": "ALL COMMODITIES",
             "years": [{"year": 2569, "months": [month(9, 102.93, 2.82),
                                                  month(9, 99.0, 1.0, typ="10"),
                                                  month(8, 102.67, 2.53)]}]}]


def mots_table() -> list:
    return [[None] * 8,
            ["จำนวนนักท่องเที่ยว ปี 2569P", None, None, None, None, None, None, None],
            ["Country of", "2026p", None, None, "2025p", None, None, "Country of"],
            ["Nationality", "Jan", "Feb", "YTD (Jan-Feb)", "Jan", "Feb", "YTD (Jan-Feb)",
             "Nationality"],
            ["Asia and the Pacific", 1.0e6, 1.1e6, 2.1e6, 1.2e6, 1.0e6, 2.2e6, "Asia"],
            ["Grand Total", 3277908.0, 3263802.0, 6541710.0, 3709102.0, 3119445.0,
             6828547.0, "Grand Total"]]


def nesdc_zip() -> bytes:
    def table(title, unit):
        return (f'"{title}",,,\n{unit},,,\n,,(1) Agriculture,(3) Gross Domestic Product '
                f'(CVM) (25)\n1993,Q1,"100,103","1,043,940"\n2026,Q1r,"187,671",'
                f'"2,938,332"\n2026,Q2,"188,468","2,932,896"\n,,,\n"p = preliminary",,,\n')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("Table 1.csv", "﻿" + table("Table 1 : Gross domestic product, "
                                                   "current market prices", "Unit : Million Baht"))
        z.writestr("Table 6.1.csv", "﻿" + table(
            "Table 6.1 : Gross domestic product, chain volume measures (Seasonally "
            "Adjusted) growth", "Unit : Percentage"))
        z.writestr("Table 6.csv", "﻿" + table(
            "Table 6 :  Gross domestic product, chain volume measures [reference year = "
            "2002] (Seasonally Adjusted)", "Unit : Million Baht"))
    return buf.getvalue()


THAI_WRITERS = ("bot", "tpso", "mots", "nesdc", "thai_set")


def group_n() -> None:
    print(f"\n{LINE}\nN. THAILAND: BOT, TPSO, MOTS, NESDC, THE SET -- ISOLATED\n{LINE}")
    now = dt.datetime(2026, 10, 11, 22, tzinfo=dt.timezone.utc)
    rows = bot.rows_from_table(bot_table(), now)
    by = {r["observed_at"]: r for r in rows}
    check(sorted(by) == ["2013-05-29", "2017-02-08", "2026-08-26"]
          and by["2026-08-26"]["value"] == 1.0
          and by["2026-08-26"]["available_at"].startswith("2026-08-26T07:05:00"),
          "the BoT's MPC table read by its header: a serial date, a text date and a "
          "two-day meeting (its last day); the remarks passed over; each decision "
          "available 14:05 Bangkok")
    saved = {n: getattr(bot, n) for n in ("http_get_text", "http_get_response")}
    page = ('<a href="/content/dam/bot/documents/en/our-roles/monetary-policy/'
            'mpc-publication/policy-interest-rate/table-mpc-2026-4-Abc.xlsx">x</a>')
    calls = []

    def fake_resp(url, **k):
        calls.append((url, k.get("headers")))
        if "gateway.api" in url:
            return (b'{"result":{"data":"0.75","announcement_date":"2026-10-08"}}', {})
        return _xlsx({"Sheet1": bot_table()}), {}
    bot.http_get_text = lambda url, **k: page
    bot.http_get_response = fake_resp
    old_key = os.environ.pop(bot.KEY_ENV, None)
    db = temp_store()
    try:
        r1 = bot.pull(db=db)
        no_key = count(db, bot.KEY) == 3 and not any("gateway" in u for u, _ in calls)
        os.environ[bot.KEY_ENV] = "fixture-key-not-a-secret"
        r2 = bot.pull(db=db)
        api = [h for u, h in calls if "gateway" in u]
        keyed = (count(db, bot.KEY) == 4 and api
                 and api[0] == {"Authorization": "fixture-key-not-a-secret"}
                 and "fixture-key" not in str(r2))
    finally:
        for n, f in saved.items():
            setattr(bot, n, f)
        os.environ.pop(bot.KEY_ENV, None)
        if old_key is not None:
            os.environ[bot.KEY_ENV] = old_key
        db.close()
    check(no_key and r1["status"] != "STALE" and keyed,
          "with no BOT_API_KEY the table alone is read and the API is never called "
          "(\"no key\"); with one, the key goes in the Authorization header, adds the "
          "decision the table lacks, and appears in no summary")
    rows = tpso.rows_from_payload(tpso_payload(), now)
    v = {(r["registry_key"], r["observed_at"]): r for r in rows}
    check(len(rows) == 4 and v[("thai.cpi", "2026-09-01")]["value"] == 102.93
          and v[("thai.cpi_yoy", "2026-08-01")]["value"] == 2.53
          and v[("thai.cpi", "2026-09-01")]["available_at"].startswith("2026-10-10T03:30")
          and tpso.body((1976, 1), (2026, 10))["Period"]["StartYear"] == 2519,
          "TPSO: the ALL COMMODITIES series, whole-kingdom months only, Buddhist-Era "
          "years less 543; available the 10th of the next month by rule; the query "
          "asks in Buddhist-Era years")
    check(_refused(tpso.rows_from_payload, tpso_payload()[:1], now),
          "a response without the 00000 series is refused")
    rows = mots.rows_from_sheet(mots_table(), "2026-10-01T03:40:30+00:00", "observed")
    got = {r["observed_at"]: r["value"] for r in rows}
    check(got == {"2026-01-01": 3277908.0, "2026-02-01": 3263802.0,
                  "2025-01-01": 3709102.0, "2025-02-01": 3119445.0},
          "MOTS: the Grand Total line, each month under its year group (2026p and the "
          "prior year's 2025p); the YTD and %-change columns passed over")
    idx = ('<a href="/news/category/805">สถิติ ปี 2568 (Tourism Statistics 2025)</a>'
           '<a href="/news/category/816"><span>สถิติ ปี 2569 (Tourism Statistics 2026)'
           '</span></a>')
    yr = '<a href="/news/category/817">(International Tourist Arrivals to Thailand 2026P)</a>'
    wb = '<a href="https://www.mots.go.th/images/v2022_abc-123.xlsx">Sep 2026P</a>'
    check(mots.year_category(idx, 2026) == "https://www.mots.go.th/news/category/816"
          and mots.arrivals_category(yr, "https://www.mots.go.th/news/category/816")
          == "https://www.mots.go.th/news/category/817"
          and mots.workbook_link(wb, "x") == "https://www.mots.go.th/images/v2022_abc-123.xlsx",
          "each hop found by its text -- the year, the arrivals category, the "
          "workbook -- never by an id")
    series = nesdc.series_from_zip(nesdc_zip())
    rows = nesdc.rows_from_series(series, "2026-08-17T02:33:24+00:00", "observed")
    q = {r["observed_at"]: r["value"] for r in rows if r["registry_key"] == nesdc.QOQ}
    check(series == {"1993-01-01": 1043940.0, "2026-01-01": 2938332.0,
                     "2026-04-01": 2932896.0}
          and round(q["2026-04-01"], 4) == round(100 * (2932896 / 2938332 - 1), 4),
          "NESDC: the SA chain-volume table found by its title and its Million Baht "
          "unit (its percent twin and the current-price table passed over); a revised "
          "'Q1r' read as Q1; the q/q change computed")
    feed = ('<rss><item><title>Infographic</title><link>https://x/a</link></item><item>'
            '<title>ตารางสถิติ ผลิตภัณฑ์มวลรวมในประเทศ รายไตรมาส (CSV)</title>'
            '<link>https://www.nesdc.go.th/download/csv-tables/</link></item></rss>')
    check(nesdc.csv_page(feed) == "https://www.nesdc.go.th/download/csv-tables/"
          and nesdc.zip_link('<a href="https://www.nesdc.go.th/?p=1&amp;ddl=2">d</a>',
                             "x") == "https://www.nesdc.go.th/?p=1&ddl=2",
          "the feed item and its download link found by their text")
    bars = [(dt.date(2026, 10, 9), 1577.65), (dt.date(2026, 10, 12), 1580.0)]
    rows = thai_set.rows_from_bars(bars, now)
    check(len(rows) == 1 and rows[0]["observed_at"] == "2026-10-09"
          and rows[0]["available_at"].startswith("2026-10-09T10:00:00"),
          "the SET: a session's bar stored once 17:00 Bangkok has passed, never before")
    import importlib
    keys = [k for w in THAI_WRITERS
            for k in importlib.import_module(f"altdata.sources.{w}").KEYS]
    bad = [k for k in keys if not (derived.registry_entry(k).get("namespace") == "thailand"
                                   and derived.registry_entry(k).get("trigger_eligible")
                                   is False and k.startswith("thai."))]
    check(not bad and len(keys) == 7,
          f"every new Thai key ({len(keys)}) is thai.*, under namespace thailand, never "
          f"trigger_eligible ({bad})")


def group_o() -> None:
    print(f"\n{LINE}\nO. STALE, NOT EMPTY -- PART 2's WRITERS\n{LINE}")

    def boom(*a, **k):
        raise FetchError("simulated outage")
    held = {"instrument": None, "observed_at": "2026-09-01",
            "available_at": "2026-09-02T00:00:00+00:00", "value": 1.0,
            "source": "fixture", "availability_kind": "reconstructed"}
    cases = [(bundesbank, "bbk.bund_10y"), (ecb_irs, "ecb.irs_10y_de"),
             (nbs, "nbs.re_starts_ytd"), (bot, "thai.bot_policy_rate"),
             (tpso, "thai.cpi"), (mots, "thai.tourist_arrivals"),
             (nesdc, "thai.gdp_real_sa"), (thai_set, "thai.set_index")]
    bad = []
    for mod, key in cases:
        saved = {}
        for attr in ("http_get_response", "http_get_text", "http_post_json",
                     "fetch_frames"):
            if hasattr(mod, attr):
                saved[attr] = getattr(mod, attr)
                setattr(mod, attr, boom)
        db = temp_store()
        try:
            db.write_many([dict(held, registry_key=key)])
            r = mod.pull(db=db)
            if not (r["status"] == "STALE" and r["written"] == 0 and count(db) == 1):
                bad.append(mod.SOURCE)
        finally:
            for attr, f in saved.items():
                setattr(mod, attr, f)
            db.close()
    check(not bad, f"every new writer's failed fetch writes nothing and keeps the stored "
                   f"row -- bundesbank, ecb, nbs, bot, tpso, mots, nesdc, yahoo_set ({bad})")


PART2_WRITERS = {"bundesbank": "official", "ecb_irs": "official", "nbs": "official",
                 "bot": "official", "tpso": "official", "mots": "official",
                 "nesdc": "official", "thai_set": "external"}


def group_p() -> None:
    print(f"\n{LINE}\nP. PART 2 REGISTERED, WIRED, AND NO UNIT ADDED\n{LINE}")
    import importlib
    mods = {w: importlib.import_module(f"altdata.sources.{w}") for w in PART2_WRITERS}
    fred = ([f"fred.{s.key}" for s in config.FRED_SLOOS_SERIES + config.FRED_AQ3_SERIES])
    keys = [k for m in mods.values() for k in m.KEYS] + list(mf.AQ3B_FEATURES)
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    metrics = reg.get("metrics") or {}
    fields = ("source", "mechanism_group", "native_horizon", "units",
              "information_half_life", "revision_policy", "observation_type",
              "description")
    missing = [k for k in keys if not all((metrics.get(k) or {}).get(f) for f in fields)]
    eligible = [k for k in keys + fred if derived.registry_entry(k).get("trigger_eligible")]
    check(not missing and not eligible and all(derived.registry_entry(k) for k in fred),
          f"every new key ({len(keys)} written, {len(fred)} FRED) has a full registry "
          f"entry and none is trigger_eligible ({missing[:3]}{eligible[:3]})")
    src = yaml.safe_load((REPO / "source_registry.yaml").read_text(
        encoding="utf-8"))["sources"]
    gone = [m.SOURCE for m in mods.values()
            if not (src.get(m.SOURCE) or {}).get("implemented_by")
            or not (REPO / src[m.SOURCE]["implemented_by"]).is_file()]
    check(not gone, f"every source is in source_registry with its implemented_by ({gone})")
    groups = {"official": feeds.OFFICIAL_WRITERS, "external": feeds.EXTERNAL_WRITERS}
    misplaced = [w for w, g in PART2_WRITERS.items() if w not in groups[g]]
    statics = [w for w, m in mods.items() if feeds.static_keys(w) != list(m.KEYS)]
    roster = set(feeds.official_keys()) | set(feeds.external_keys()) | set(feeds.fred_keys())
    check(not misplaced and not statics and set(keys + fred) - set(mf.AQ3B_FEATURES)
          <= roster and len(yf_src.SYMBOLS) == 58
          and {"VNQ", "VEA", "HEFA"} <= set(yf_src.SYMBOLS),
          f"each writer in its feeds group, its KEYS read from source, on the "
          f"freshness roster; VNQ, VEA and HEFA in the price basket "
          f"({misplaced}{statics})")
    units = [p.name for p in (REPO / "deploy" / "systemd").iterdir()]
    added = [u for u in units if any(w.replace("_", "") in u.replace("-", "").replace(
        "_", "") for w in PART2_WRITERS)]
    check(not added, f"no systemd unit added: the writers ride the existing pulls "
                     f"({added})")
    secrets = [p for p in (REPO / "altdata" / "sources").glob("bot.py")
               if re.search(r"BOT_API_KEY\s*=\s*['\"][^'\"]+['\"]", p.read_text(
                   encoding="utf-8"))]
    check(not secrets and bot.KEY_ENV == "BOT_API_KEY",
          "the BoT key is read from the environment (BOT_API_KEY) and never written "
          "in the source")


def main() -> int:
    print(f"{LINE}\nAQ-3 part 1 -- the Quarterly's series writers (fixtures, no "
          f"network)\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_d2, group_e, group_f, group_g,
              group_h, group_i, group_j, group_k, group_l, group_m,
              group_n, group_o, group_p):
        g()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
