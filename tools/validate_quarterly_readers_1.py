"""
The Quarterly's readers, tranche 1 (b69-quarterly-readers-1, 25 Oct 2026; D34).

    python tools/validate_quarterly_readers_1.py

FIXTURES ONLY: no network, no live store. Each reader's parser runs on a small
payload in the source's own shape (the shapes probed once on 25 Oct 2026); its
pull runs against a temporary store with the fetch replaced.

  A  the parsers, on fixtures
  B  every key's unit and cadence, as registered
  C  the STALE path: a refusal writes nothing, and is not retried
  D  the one-request-a-day guard (PortWatch, the Riksbank)
  E  the attribution strings stored with the rows (PortWatch, the SNB, MoF)
  F  WASDE: projections kept apart from estimates
  G  the lag families, with their bounds
  H  no person's name or address in the readers
  I  keys registered, barred from the market-state object, and no regime import
  J  wired: the official roster, the FRED pull, the catalogue, the Quarterly
"""
from __future__ import annotations

import datetime as dt
import fnmatch
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import os as _gt_os                                            # noqa: E402
import sys as _gt_sys                                          # noqa: E402
_gt_dir = _gt_os.path.dirname(_gt_os.path.abspath(__file__))
_gt_sys.path.insert(0, _gt_dir if _gt_os.path.basename(_gt_dir) == "tools"
                    else _gt_os.path.join(_gt_dir, "tools"))
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
_TMP = gate_mkdtemp(prefix="validate_qr1_")
os.environ["CHESTER_STATE_DIR"] = _TMP

import yaml  # noqa: E402

from altdata import config, derived, feeds, observations, source_ids  # noqa: E402
from altdata.sources import _quarterly_common as qc  # noqa: E402
from altdata.sources import (boc_valet, cftc_grains, cpc_oni, eia_buffers,  # noqa: E402
                             esmis_crop_progress, esmis_wasde, mof_intervention,
                             portwatch, riksbank, snb_sight)
from altdata.sources._base import FetchError  # noqa: E402

READERS = [eia_buffers, portwatch, esmis_wasde, esmis_crop_progress, cpc_oni,
           cftc_grains, boc_valet, riksbank, snb_sight, mof_intervention]
PASS = FAIL = 0
LINE = "=" * 78


def ok(m):
    global PASS
    PASS += 1
    print(f"  PASS  {m}")


def bad(m):
    global FAIL
    FAIL += 1
    print(f"  FAIL  {m}")


def check(c, m):
    ok(m) if c else bad(m)


def head(t):
    print(f"{LINE}\n{t}\n{LINE}")


def temp_store():
    fd, path = tempfile.mkstemp(suffix=".sqlite", dir=_TMP)
    os.close(fd)
    os.unlink(path)
    return observations.ObservationStore(path)


def rows_of(db, key):
    return db.conn.execute("SELECT instrument, observed_at, value_num, source FROM "
                           "observations WHERE registry_key=? ORDER BY observed_at",
                           (key,)).fetchall()


def serial(d):
    return (dt.date.fromisoformat(d) - dt.date(1899, 12, 30)).days


# ---------------------------------------------------------------------------
# Fixtures, in each source's own shape
# ---------------------------------------------------------------------------
PW = {"features": [
    {"attributes": {"date": "2026-10-18", "portid": "chokepoint6", "n_total": 4, "n_tanker": 2}},
    {"attributes": {"date": "2026-10-18", "portid": "chokepoint1", "n_total": 31, "n_tanker": 9}},
    {"attributes": {"date": "2026-10-18", "portid": "chokepoint2", "n_total": 30, "n_tanker": 5}}]}

WASDE = b"""<?xml version="1.0" encoding="utf-8"?>
<Report Name="wasde">
 <sr11><Report Name="sr11" Report_Month="October 2026" sub_report_title="U.S. Wheat Supply and Use">
  <matrix1>
   <attribute1 attribute1="Use, Total">
    <m1_year_group market_year1="2025/26 Est."><m1_month_group forecast_month1=""><Cell cell_value1="2,049"/></m1_month_group></m1_year_group>
    <m1_year_group market_year1="2026/27 Proj."><m1_month_group forecast_month1="Sep"><Cell cell_value1="1,874"/></m1_month_group></m1_year_group>
    <m1_year_group market_year1="2026/27 Proj."><m1_month_group forecast_month1="Oct"><Cell cell_value1="1,859"/></m1_month_group></m1_year_group>
   </attribute1>
   <attribute1 attribute1="Ending Stocks">
    <m1_year_group market_year1="2024/25"><m1_month_group forecast_month1=""><Cell cell_value1="855"/></m1_month_group></m1_year_group>
    <m1_year_group market_year1="2025/26 Est."><m1_month_group forecast_month1=""><Cell cell_value1="920"/></m1_month_group></m1_year_group>
    <m1_year_group market_year1="2026/27 Proj."><m1_month_group forecast_month1="Sep"><Cell cell_value1="717"/></m1_month_group></m1_year_group>
    <m1_year_group market_year1="2026/27 Proj."><m1_month_group forecast_month1="Oct"><Cell cell_value1="740"/></m1_month_group></m1_year_group>
   </attribute1>
  </matrix1>
 </Report></sr11>
</Report>
"""

CROP = """Crop Progress
Released October 19, 2026, by the National Agricultural Statistics Service
Corn Condition - Selected States: Week Ending October 18, 2026
      State     : Very poor :   Poor    :   Fair    :   Good    : Excellent
Iowa ...........:      1           7          20          58          14
18 States ......:      5          12          27          43          13
Previous week ..:      5          12          27          44          12
Cotton Condition - Selected States: Week Ending October 18, 2026
15 States ......:     10          16          39          29           6
"""

ONI = """ SEAS  YR   TOTAL   ANOM
  DJF 1950   24.72   -1.53
  NDJ 2025   26.10   -0.55
"""

CFTC = [{"cftc_contract_market_code": "002602", "report_date_as_yyyy_mm_dd": "2026-10-13T00:00:00.000",
         "m_money_positions_long_all": "250000", "m_money_positions_short_all": "150000",
         "open_interest_all": "1600000"},
        {"cftc_contract_market_code": "088691", "report_date_as_yyyy_mm_dd": "2026-10-13T00:00:00.000",
         "m_money_positions_long_all": "1", "m_money_positions_short_all": "1",
         "open_interest_all": "2"}]

BOC = {"terms": {"url": "https://www.bankofcanada.ca/terms/"},
       "observations": [{"d": "2026-10-22", "BD.CDN.2YR.DQ.YLD": {"v": "3.22"}},
                        {"d": "2026-10-21", "BD.CDN.2YR.DQ.YLD": {"v": ""}}]}

RIKS = [{"date": "2026-10-01", "value": 2.735}, {"date": "2026-10-02", "value": 2.658}]

SNB = ('﻿"CubeId";"snbgwdchfsgw"\n"PublishingDate";"2026-10-19 10:00"\n\n'
       '"Date";"D0";"Value"\n"2026-10-09";"GI";"435000"\n"2026-10-09";"TG";"456000"\n'
       '"2026-10-15";"TG";\n"2026-10-16";"GI";"435355"\n"2026-10-16";"UEB";"21661"\n'
       '"2026-10-16";"TG";"457015"\n')

MOF_PAGE = ("<html><body><p>Total amount of foreign exchange intervention operations "
            "for the period from August 27, 2026 through September 28, 2026</p>"
            "<p>&yen; 0</p></body></html>")
MOF_BIG = ("<p>Total amount of foreign exchange intervention operations for the period "
           "from April 26, 2024 through May 29, 2024</p><p>&yen; 9,788.5 billion</p>")
MOF_INDEX = '<a href="20260930e.html">x</a><a href="20260828e.html">y</a>'


# ---------------------------------------------------------------------------
def group_a():
    head("A. THE PARSERS, ON FIXTURES")
    t = [["h"], ["h"], ["h"], [serial("2026-10-16"), 409.1], [serial("2026-10-09"), 408.0]]
    s = eia_buffers.series_from_table(t, 1000.0)
    check(s == {"2026-10-16": 409100.0, "2026-10-09": 408000.0},
          "EIA: the 'Data 1' sheet parses, thousand barrels to barrels")
    r = eia_buffers.rows_for("eia.spr_stocks", {"2026-10-16": 1.0})[0]
    check(r["available_at"].startswith("2026-10-21T14:30"),
          "EIA: the SPR row is available the Wednesday 10:30 ET after the week")
    r = eia_buffers.rows_for("eia.gas_storage", {"2026-10-16": 1.0})[0]
    check(r["available_at"].startswith("2026-10-22T14:30"),
          "EIA: gas storage is available the Thursday 10:30 ET after the week")
    r = eia_buffers.rows_for("eia.lng_exports", {"2026-08-01": 1.0})[0]
    check(r["available_at"].startswith("2026-10-31T20:00"),
          "EIA: LNG exports are available at the end of the second month after")
    rows = portwatch.rows_from_payload(PW, "2026-10-25T12:00:00Z")
    keys = {(x["registry_key"], x["value"]) for x in rows}
    check(("imf.portwatch.transits.hormuz", 4.0) in keys
          and ("imf.portwatch.transits.suez.tanker", 9.0) in keys
          and not any("panama" in k for k, _ in keys),
          "PortWatch: the four chokepoints' total and tanker calls, others ignored")
    try:
        portwatch.rows_from_payload({"error": {"code": 400}}, "x")
        bad("PortWatch: an error payload was accepted")
    except ValueError:
        ok("PortWatch: an error payload raises (STALE), never an empty reading")
    w = esmis_wasde.rows_from_xml(WASDE, "2026-10-09T16:00:00Z", "observed")
    got = {(x["registry_key"], x["instrument"]): x["value"] for x in w}
    check(got.get(("usda.wasde.wheat.ending_stocks", "2026/27 proj")) == 740.0
          and got.get(("usda.wasde.wheat.ending_stocks", "2025/26 est")) == 920.0
          and got.get(("usda.wasde.wheat.ending_stocks", "2024/25")) == 855.0
          and abs(got.get(("usda.wasde.wheat.stocks_to_use", "2026/27 proj")) - 39.8063) < 1e-3,
          "WASDE: ending stocks per marketing year, this month's projection (Oct over "
          "Sep), stocks-to-use computed")
    check(all(x["observed_at"] == "2026-10-01" for x in w),
          "WASDE: observed at the release's report month")
    c = esmis_crop_progress.rows_from_text(CROP)
    check(len(c) == 1 and c[0]["registry_key"] == "usda.crop_progress.corn"
          and c[0]["value"] == 56.0 and c[0]["observed_at"] == "2026-10-18"
          and c[0]["available_at"].startswith("2026-10-19T20:00"),
          "Crop Progress: the all-states row, good + excellent (43 + 13), at the "
          "release date 16:00 ET; a crop with no table writes nothing")
    o = cpc_oni.rows_from_text(ONI)
    check([(x["observed_at"], x["value"]) for x in o] == [("1950-01-01", -1.53),
                                                          ("2025-12-01", -0.55)],
          "ONI: each season at its centre month, the anomaly column")
    check(cpc_oni.season_dates("NDJ", 2025)[1].startswith("2026-02-15"),
          "ONI: a season is available on the 15th after its last month")
    g = cftc_grains.rows_from_records(CFTC)
    gk = {x["registry_key"]: x["value"] for x in g}
    check(gk.get("cftc.disagg.corn.managed_money_net") == 100000.0
          and abs(gk.get("cftc.disagg.corn.managed_money_net_oi") - 6.25) < 1e-9
          and len(gk) == 2,
          "CFTC grains: managed money net and its share of open interest; gold ignored")
    b = boc_valet.rows_from_payload(BOC)
    check(len(b) == 1 and b[0]["value"] == 3.22, "Bank of Canada: Valet observations, "
          "a blank value skipped")
    k = riksbank.rows_from_payload(RIKS)
    check([x["value"] for x in k] == [2.735, 2.658], "Riksbank: the SWEA list")
    sn = snb_sight.rows_from_csv(SNB)
    newest = [x for x in sn if x["observed_at"] == "2026-10-16"]
    check(len(sn) == 4 and all(x["availability_kind"] == "observed" for x in newest)
          and newest[0]["available_at"].startswith("2026-10-19T08:00"),
          "SNB: TG and GI rows, a blank skipped, UEB ignored, the newest at PublishingDate")
    m0 = mof_intervention.row_from_page("20260930e.html", MOF_PAGE)
    m1 = mof_intervention.row_from_page("20240531e.html", MOF_BIG)
    check(m0["value"] == 0.0 and m0["observed_at"] == "2026-09-28"
          and m1["value"] == 9788.5e9,
          "MoF: the period's total, zero and a 'billion' figure scaled to yen")
    check(mof_intervention.page_links(MOF_INDEX) == ["20260930e.html", "20260828e.html"],
          "MoF: the index's monthly pages, newest first")


def group_b():
    head("B. EVERY KEY'S UNIT AND CADENCE, AS REGISTERED")
    expect = {"eia.spr_stocks": ("count", "weekly"), "eia.refinery_util": ("percent_share", "weekly"),
              "eia.gas_storage": ("count", "weekly"), "eia.lng_exports": ("count", "monthly"),
              "imf.portwatch.transits.hormuz": ("count", "daily"),
              "usda.wasde.corn.ending_stocks": ("count", "monthly"),
              "usda.wasde.corn.stocks_to_use": ("percent_share", "monthly"),
              "usda.crop_progress.corn": ("percent_share", "weekly"),
              "noaa.oni": ("index_points", "monthly"),
              "cftc.disagg.corn.managed_money_net": ("count", "weekly"),
              "cftc.disagg.corn.managed_money_net_oi": ("percent_share", "weekly"),
              "boc.yield_2y": ("percent_rate", "daily"), "riksbank.yield_2y": ("percent_rate", "daily"),
              "snb.sight_deposits_total": ("count", "weekly"),
              "jp.mof.intervention_jpy": ("count", "monthly")}
    wrong = []
    for k, (u, h) in expect.items():
        e = derived.registry_entry(k) or {}
        if e.get("units") != u or e.get("native_horizon") != h:
            wrong.append((k, e.get("units"), e.get("native_horizon")))
    check(not wrong, f"each reader's key carries its unit and cadence {wrong or ''}")
    fam = derived.registry_entry("fred.ovx") or {}
    check(bool(fam), "fred.ovx resolves through the fred_6i block")


def group_c():
    head("C. THE STALE PATH: A REFUSAL WRITES NOTHING, AND IS NOT RETRIED")
    calls = []

    def refuse(url, **kw):
        calls.append(url)
        raise FetchError(f"HTTP 403 from {url}: forbidden")
    db = temp_store()
    saved = boc_valet._fetch
    try:
        boc_valet._fetch = refuse
        out = boc_valet.pull(db=db)
    finally:
        boc_valet._fetch = saved
    check(out["status"] == "STALE" and "403" in out["reason"] and not rows_of(db, "boc.yield_2y"),
          "a 403 returns STALE with the reason and writes nothing")
    check(len(calls) == 1, "and it was asked once: no retry around a refusal")
    db.close()
    texts = {"https://x.example/robots.txt": "User-agent: *\nDisallow: /data\n"}
    try:
        qc.robots_check("https://x.example/data/file.csv", get_text=lambda u: texts[u])
        bad("a robots disallow was not refused")
    except qc.Refused as e:
        ok(f"a robots disallow refuses the request ({str(e)[:50]})")

    def forbidden(u):
        raise FetchError(f"HTTP 403 from {u}")

    def broken(u):
        raise FetchError(f"Giving up on {u} after 3 retries")
    check("no rules" in qc.robots_check("https://y.example/q", get_text=forbidden),
          "robots.txt answered 403 is unavailable: no rules (RFC 9309 2.3.1.3)")
    try:
        qc.robots_check("https://y.example/q", get_text=broken)
        bad("an unreadable robots.txt was guessed at")
    except FetchError:
        ok("a robots.txt that cannot be read raises: no guess")


def group_d():
    head("D. THE ONE-REQUEST-A-DAY GUARD")
    path = Path(_TMP) / "guard_test.json"
    day = ["2026-10-25"]
    g = qc.DailyGuard("t", path=path, today=lambda: day[0])
    g.charge()
    try:
        g.charge()
        bad("a second request the same day was allowed")
    except qc.Refused:
        ok("a second request the same ET day is refused before it is sent")
    day[0] = "2026-10-26"
    g.charge()
    ok("the next day's request is allowed")
    sent = []

    def fake(url, **kw):
        sent.append(url)
        return json.dumps(PW).encode(), {}
    saved = (portwatch._fetch, portwatch._guard, qc.robots_check)
    try:
        portwatch._fetch = fake
        portwatch._guard = qc.DailyGuard("pw", path=Path(_TMP) / "pw.json",
                                         today=lambda: "2026-10-25")
        portwatch.qc.robots_check = lambda url, get_text=None: "test"
        db = temp_store()
        first = portwatch.pull(db=db)
        second = portwatch.pull(db=db)
    finally:
        portwatch._fetch, portwatch._guard, qc.robots_check = saved
        portwatch.qc.robots_check = saved[2]
    check(first["status"] == "OK" and second["status"] == "STALE"
          and "already spent" in second["reason"] and len(sent) == 1,
          "PortWatch: the timer's second run of a day sends nothing and says why")
    sent.clear()
    saved = (riksbank._fetch, riksbank._guard)
    try:
        riksbank._fetch = lambda url, **kw: (sent.append(url) or (json.dumps(RIKS).encode(), {}))
        riksbank._guard = qc.DailyGuard("rb", path=Path(_TMP) / "rb.json",
                                        today=lambda: "2026-10-25")
        riksbank.qc.robots_check = lambda url, get_text=None: "test"
        db2 = temp_store()
        a, b = riksbank.pull(db=db2), riksbank.pull(db=db2)
    finally:
        riksbank._fetch, riksbank._guard = saved
        riksbank.qc.robots_check = qc.robots_check
    check(a["status"] == "OK" and b["status"] == "STALE" and len(sent) == 1,
          "Riksbank: one request a day, the per-IP limit honoured")
    db.close()
    db2.close()


def group_e():
    head("E. THE ATTRIBUTION STRINGS, STORED WITH THE ROWS")
    pw = portwatch.rows_from_payload(PW, "2026-10-25T12:00:00Z")
    check(all(r["source"] == "imf_portwatch:IMF PortWatch" for r in pw),
          "PortWatch rows carry 'IMF PortWatch' in the source field")
    check(all(r["source"] == "snb:Swiss National Bank" for r in snb_sight.rows_from_csv(SNB)),
          "SNB rows carry 'Swiss National Bank'")
    check(mof_intervention.row_from_page("20260930e.html", MOF_PAGE)["source"]
          == "mof_intervention:Ministry of Finance, Japan",
          "MoF rows cite the Ministry (PDL 1.0)")
    check(all(source_ids.canonical(s) == s.split(":")[0] for s in (
        "imf_portwatch:IMF PortWatch", "snb:Swiss National Bank",
        "mof_intervention:Ministry of Finance, Japan")),
          "each attributed source string reads as its registered id (<id>:<variant>)")
    db = temp_store()
    saved = snb_sight._fetch
    try:
        snb_sight._fetch = lambda url, **kw: (SNB.encode(), {})
        snb_sight.pull(db=db)
    finally:
        snb_sight._fetch = saved
    srcs = {r[3] for r in rows_of(db, "snb.sight_deposits_total")}
    check(srcs == {"snb:Swiss National Bank"}, "and the store keeps it on the written rows")
    db.close()


def group_f():
    head("F. WASDE: PROJECTIONS KEPT APART FROM ESTIMATES")
    w = esmis_wasde.rows_from_xml(WASDE, "2026-10-09T16:00:00Z", "observed")
    insts = {x["instrument"] for x in w}
    proj = {i for i in insts if i.endswith(" proj")}
    est = {i for i in insts if i.endswith(" est")}
    check(proj == {"2026/27 proj"} and est == {"2025/26 est"} and "2024/25" in insts,
          "every row names its marketing year and printed status; none is shared")
    check(esmis_wasde.status_of("2026/27 Proj.") != esmis_wasde.status_of("2026/27 Est."),
          "the same year projected and estimated are two instruments")


def group_g():
    head("G. THE LAG FAMILIES, WITH THEIR BOUNDS")
    lags = yaml.safe_load((REPO / "config" / "publication_lags.yaml").read_text(encoding="utf-8"))
    fam = {f["id"]: f for f in lags["families"]}
    for fid, key in (("imf_portwatch", "imf.portwatch.transits.hormuz"),
                     ("eia_ng_monthly", "eia.lng_exports"), ("noaa_oni", "noaa.oni")):
        f = fam.get(fid) or {}
        _n, why = derived.staleness_allowance_of(derived.registry_entry(key), key)
        check(f and 0 < f["lag_sessions"] <= f["max_lag"] and f.get("reason")
              and fid in why, f"{fid}: a documented lag within its bound, and {key} reads it")
    ids = [f["id"] for f in lags["families"]]
    check(ids.index("imf_portwatch") < ids.index("imf"),
          "PortWatch's family comes before the imf.* glob, so it wins")


def group_h():
    head("H. NO PERSON'S NAME OR ADDRESS IN THE READERS")
    offenders = []
    for m in READERS + [qc]:
        src = Path(m.__file__).read_text(encoding="utf-8")
        if re.search(r"[\w.]+@[\w-]+\.\w+", src) or re.search(r"User-Agent\"?\s*:", src):
            offenders.append(m.__name__)
    check(not offenders, f"no address and no literal User-Agent in a reader {offenders or ''}")


def group_i():
    head("I. REGISTERED, BARRED FROM THE OBJECT, NO REGIME IMPORT")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    globs = [g for e in reg["market_state_barred"] for g in (e.get("keys") or [])]
    keys = [k for m in READERS for k in m.KEYS] + ["fred.ovx"]
    unreg = [k for k in keys if not derived.registry_entry(k)]
    unbarred = [k for k in keys if not any(fnmatch.fnmatch(k, g) for g in globs)]
    check(not unreg, f"every key is registered {unreg or ''}")
    check(not unbarred, f"every key is barred from the market-state object {unbarred or ''}")
    names = "|".join(m.__name__.split(".")[-1] for m in READERS)
    hits = [p for p in ("regime.py", "contradictions.py")
            if re.search(rf"\b({names})\b", (REPO / p).read_text(encoding="utf-8"))]
    check(not hits, f"regime.py and contradictions.py import no reader {hits or ''}")


def group_j():
    head("J. WIRED: THE ROSTER, THE FRED PULL, THE CATALOGUE, THE QUARTERLY")
    names = [m.__name__.split(".")[-1] for m in READERS]
    check(set(names) <= set(feeds.OFFICIAL_WRITERS),
          "the ten readers run in the official feed")
    check(all(list(feeds.static_keys(n)) == list(m.KEYS) for n, m in zip(names, READERS)),
          "each reader's KEYS read from source match the module's")
    check([s.fred_id for s in config.FRED_6I_SERIES] == ["OVXCLS"]
          and any(s.fred_id == "OVXCLS" for s in config.FRED_PULL_SERIES),
          "OVXCLS rides the existing FRED pull (with the key), never the graph CSV")
    cat = yaml.safe_load((REPO / "config" / "catalogue_commands.yaml").read_text(encoding="utf-8"))
    check(all(f"altdata.sources.{n}" in cat["commands"] for n in names),
          "each reader has its catalogue line")
    qtxt = (REPO / "config" / "quarterly_chapters.yaml").read_text(encoding="utf-8")
    wired = ["eia.spr_stocks", "eia.refinery_util", "eia.gas_storage", "eia.lng_exports",
             "fred.ovx", "imf.portwatch.transits.hormuz.tanker", "usda.wasde.corn.stocks_to_use",
             "usda.crop_progress.corn", "noaa.oni", "cftc.disagg.corn.managed_money_net_oi",
             "boc.yield_2y", "riksbank.yield_2y", "snb.sight_deposits_total",
             "jp.mof.intervention_jpy"]
    missing = [k for k in wired if f"key: {k}," not in qtxt and f"key: {k} " not in qtxt]
    check(not missing, f"each reader prints in its Quarterly chapter {missing or ''}")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g,
              group_h, group_i, group_j):
        try:
            g()
        except Exception as exc:                              # noqa: BLE001
            bad(f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
