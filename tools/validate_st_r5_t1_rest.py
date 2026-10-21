"""
Validation gate for the rest of signal-triage Batch 6's Tranche 1 (16 Oct 2026;
docs/change-order-signal-triage-batch-6-2026-10-15.md, items 31, 32, 38, 39, 42,
43 and 44; docs/briefs/st-r5-t1-rest-notes.md).

FIXTURES only, each in a temporary store of its own -- no live store, no network,
no model. Every expected figure is computed here, independently of the module:

  A  THE WRITERS EXTENDED. Nineteen FRED series join the pull (ids, units,
     cadence; 57 signal series, 159 pulled, with the GTM batch's five); the BIS writer reads every area into
     bis.policy_rate, and a failure of that request costs only its key.
  B  THE WRITERS, LIFTED (16 Oct 2026). SPY's holdings parse by column name (a
     class share to Yahoo's form, the cash and CVR lines skipped; a file without
     its columns or its date refused); a robots disallow stops the fetch; the WGC
     sentence parses and a changed one is refused; neither is held and both are
     on feeds.EXTERNAL_WRITERS with their keys on the external roster; each pull
     fetches its fixtures and writes in a temporary store; a member whose closes
     are not stored is asked for two years, one already held for ten days. Japan's
     CPI reader (item 39's gap) reads its fixture files by item code, computes the
     change on the year within one base, lets the newer base decide, refuses a
     file without its codes, stops on a robots disallow, and writes.
  C  ST-R5.31a THE PEAK-BAND FLAG. The ten largest ISSUERS (GOOGL with GOOG) at
     exactly 40.0% fire, 39.99% does not, 44.01% reads above the band; BofA's
     basket mapped against the same file; no holdings, or stale ones, is absent
     with its reason.
  D  ST-R5.44a THE HISTOGRAM AND THE GAP. Twenty members with set drawdowns: the
     four buckets (the 10% and 20% edges fall in the deeper bucket), the
     average-member drawdown and the gap against the index, hand-computed; 95%
     coverage prints, 90% says "awaiting constituent prices"; none stored says so.
  E  ST-R5.32a THE OIL-SHOCK SIGNATURE. The rolling correlation against a hand
     case; a supply-shock window reads ON; each leg fires AT its percentile
     threshold and not a hair beyond; the history shorter than 20 years is said.
  F  ST-R5.42a THE COMPOSITE. Each input's z against statistics.stdev over its own
     120 months; four inputs, three (one stale), and two (refused, "fewer than
     3"); the flag at its threshold and not below; DEANCHOR's first leg printed.
  G  ST-R5.39a REAL YIELDS. Real on core and on headline, the linker's monthly
     mean, the US-DE and US-JP differentials in bp (Japan on the Statistics
     Bureau's core); without Japan's CPI the gap carries into US-JP; a stale CPI
     is a gap, not a number; the EM rows on headline with the core gap named.
  H  ST-R5.38a GOLD AGAINST WORLD EQUITIES. Not tracked: no free source for world
     equity capitalisation (the by-hand ACWI key dropped, 16 Oct 2026), printed
     so; with a capitalisation key configured, the ratio by hand, a gold close
     more than five days off not used, the percentile's real window and n; WFE
     is a listed gap.
  I  ST-R5.43a DIFFUSION. Net share of 24 central banks by hand, a stale area
     dropped, the lead month, the CLI and the PMI; fewer than 20 is absent; the
     ahead line names the month the lead reaches.
  J  THE DISPLAY. Mechanics, Plumbing & rates, Positioning, Slow layers and Ahead
     carry their sub-sections at both cadences; no week phrase at "monthly"; no
     paragraph asked; every number in the sections' data has a typed field name;
     no filler, no causal claim; report-only (regime.py reads none of it, and the
     inflation dimension declares no driver).
  K  THE REGISTRY AND THE PURITY. Every key read is registered with its units;
     the new keys carry a family and a long window; the three sources are live;
     the catalogue names the commands; the dropped ACWI key is gone everywhere;
     the reads import no fetcher, store writer or model.

    python tools/validate_st_r5_t1_rest.py
"""

from __future__ import annotations

import ast
import copy
import datetime as dt
import inspect
import csv
import io
import math
import random
import re
import statistics
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gate_tmp  # noqa: E402
import yaml  # noqa: E402

from altdata import observations  # noqa: E402
from altdata import st_r5_t1_rest as tr  # noqa: E402
from daily_cascade import t1_rest_block as blk  # noqa: E402

PASS = 0
FAIL = 0
LINE = "=" * 78
CFG = tr.config()
NOW_DAY = "2026-10-09"
NOW = NOW_DAY + "T23:00:00+00:00"
WEEK_OK = re.compile(r"52-week|weekly", re.I)


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def store(rows: list[tuple]) -> str:
    """A temporary store holding (key, instrument, day, value) rows, each
    available at 21:00 UTC on its day."""
    db = str(Path(gate_tmp.mkdtemp("t1rest_")) / "obs.db")
    with observations.ObservationStore(db) as st:
        st.write_many([{"registry_key": k, "instrument": i, "observed_at": d,
                        "available_at": d + "T21:00:00+00:00", "value": float(v),
                        "source": "fixture"} for k, i, d, v in rows])
    return db


def open_store(db: str):
    return observations.ObservationStore(db)


def count(st) -> int:
    return st.conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]


def boom(*a, **k):
    raise AssertionError("a held writer fetched")


def weekdays(start: str, end: str) -> list[str]:
    d, e, out = dt.date.fromisoformat(start), dt.date.fromisoformat(end), []
    while d <= e:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def months(first: str, last: str) -> list[str]:
    y, m = int(first[:4]), int(first[5:7])
    out = []
    while f"{y:04d}-{m:02d}" <= last:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def xlsx(rows: list[list]) -> bytes:
    """A real, minimal one-sheet .xlsx (shared strings for text)."""
    strings: list[str] = []

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
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("xl/workbook.xml", f'<workbook xmlns="{ns}" xmlns:r="{rns}"><sheets>'
                   f'<sheet name="holdings" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/'
                   '2006/relationships"><Relationship Id="rId1" '
                   'Target="worksheets/sheet1.xml" Type="x"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml", f'<worksheet xmlns="{ns}"><sheetData>'
                   f'{"".join(body)}</sheetData></worksheet>')
        z.writestr("xl/sharedStrings.xml", f'<sst xmlns="{ns}">'
                   + "".join(f"<si><t>{s}</t></si>" for s in strings) + "</sst>")
    return buf.getvalue()


def _ticker(i: int) -> str:
    a = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "Z" + a[i // 26 % 26] + a[i % 26]


def spy_workbook(n: int = 410, as_of: str = "As of 08-Oct-2026",
                 header: tuple = ("Name", "Ticker", "Identifier", "SEDOL", "Weight",
                                  "Sector", "Shares Held", "Local Currency")) -> bytes:
    rows = [["Fund Name:", "SPDR S and P 500 ETF Trust"], ["Ticker Symbol:", "SPY"],
            ["Holdings:", as_of], list(header),
            ["NVIDIA CORP", "NVDA", "x", "x", 7.5, "-", 100.0, "USD"],
            ["BERKSHIRE HATHAWAY INC CL B", "BRK.B", "x", "x", 1.5, "-", 10.0, "USD"],
            ["US DOLLAR", "-", "x", "-", 0.3, "-", 1.0, "USD"],
            ["TPG INC", "2602335D", "x", "-", 0.000003, "-", 1.0, "USD"]]
    rows += [[f"CO {i}", _ticker(i), "x", "x", 0.2, "-", 1.0, "USD"] for i in range(n)]
    rows += [[None], ["Before investing in a fund, consider its objectives."]]
    return xlsx(rows)


WGC_HTML = ('<p><strong>Total above-ground stock (end-Q2 2026):</strong><br>222,600 '
            'tonnes, US$29.0tn</p><ol><li><strong>Jewellery</strong></li></ol>')
EM_CSV = ("FREQ,REF_AREA,TIME_PERIOD,OBS_VALUE\n"
          "M,BR,2026-08,15.0\nM,BR,2026-09,15.0\nM,MX,2026-09,7.5\n")
ALL_CSV = ("FREQ,REF_AREA,TIME_PERIOD,OBS_VALUE\n"
           "M,US,2026-08,4.25\nM,US,2026-09,4.0\nM,XM,2026-09,2.0\nM,DE,1998-12,3.0\n"
           "D,US,2026-09-15,4.0\nM,GB,2026-09,\n")


# ---------------------------------------------------------------------------
def group_a() -> None:
    print(f"\n{LINE}\nA. THE WRITERS EXTENDED: FRED AND THE BIS\n{LINE}")
    from altdata import config as acfg                          # noqa: PLC0415
    from altdata.sources import _publication as pub             # noqa: PLC0415
    from altdata.sources import bis_cbpol                       # noqa: PLC0415
    specs = {s.key: s for s in acfg.FRED_PULL_SERIES}
    want = {"expinf_10y": ("EXPINF10YR", "%"), "oecd_cli_g7": ("G7LOLITOAASTSAM", "idx"),
            "oecd_10y_mx": ("IRLTLT01MXM156N", "%"), "oecd_10y_za": ("IRLTLT01ZAM156N", "%"),
            "oecd_10y_kr": ("IRLTLT01KRM156N", "%")}
    for c in ("de", "fr", "it", "nl", "be", "se", "ch"):
        want[f"hicp_{c}"] = (f"CP0000{c.upper()}M086NEST", "idx")
        want[f"hicp_core_{c}"] = (f"00XEFD{c.upper()}M086NEST", "idx")
    bad = [k for k, (fid, u) in want.items()
           if k not in specs or specs[k].fred_id != fid or specs[k].units != u
           or specs[k].freq != "monthly"]
    check(len(want) == 19 and not bad,
          f"nineteen FRED series join the pull with their ids, units and cadence "
          f"(bad: {bad or 'none'})")
    # 57 / 159 since the GTM batch, part 1 (17 Oct 2026) added five; 63 / 165
    # since part 2 added GTM-12's six; 64 / 166 since ST-4 added FEDTARMD; 65 / 266
    # at the chain-2 stitch (Batch 5's three, 6e's, Group B's; two duplicates gone);
    # 65 / 267 since A51 added RSAFS (FRED_NOTES_SERIES, 19 Oct 2026); 65 / 277
    # since a53 added the bank-stress panel's ten (Batch 12 item 59; chain-4).
    check(len(acfg.FRED_SIGNAL_SERIES) == 65 and len(acfg.FRED_PULL_SERIES) == 277
          and len({s.key for s in acfg.FRED_PULL_SERIES}) == 277
          and len({s.fred_id for s in acfg.FRED_PULL_SERIES}) == 277,
          f"FRED_SIGNAL_SERIES 65, FRED_PULL_SERIES 277, no key or id twice "
          f"({len(acfg.FRED_SIGNAL_SERIES)}, {len(acfg.FRED_PULL_SERIES)})")
    s = bis_cbpol.parse_all(ALL_CSV)
    check(set(s) == {"US", "XM", "DE"} and s["US"] == {"2026-08-31": 4.25, "2026-09-30": 4.0},
          "the BIS all-areas parse keeps monthly rows of every area, skips blanks and "
          "daily rows")
    check(bis_cbpol.ALL_KEY in bis_cbpol.KEYS and len(bis_cbpol.KEYS) == 12,
          "the writer owns bis.policy_rate beside the scorecard's eleven")
    saved = bis_cbpol.http_get_response
    try:
        def half(url, params=None, timeout=None, headers=None):
            if url.endswith("/M."):
                raise RuntimeError("the all-areas request failed")
            return EM_CSV.encode(), {}

        def both(url, params=None, timeout=None, headers=None):
            return (ALL_CSV if url.endswith("/M.") else EM_CSV).encode(), {}
        bis_cbpol.http_get_response = half
        with open_store(store([])) as st:
            r = bis_cbpol.pull(db=st)
            em = st.instruments(bis_cbpol.ALL_KEY)
            nbr = len(st.as_of("em.bis.policy_rate.bra"))
        check(r["status"] == pub.OK and nbr == 2 and not em
              and bis_cbpol.ALL_KEY in r["keys_without_rows"],
              "a failure of the all-areas request costs only its key: the scorecard's "
              "rows still write")
        bis_cbpol.http_get_response = both
        with open_store(store([])) as st:
            r = bis_cbpol.pull(db=st)
            areas = st.instruments(bis_cbpol.ALL_KEY)
        check(r["status"] == pub.OK and areas == ["DE", "US", "XM"],
              f"with both, every area is stored under bis.policy_rate by its code "
              f"({areas})")
    finally:
        bis_cbpol.http_get_response = saved


# ---------------------------------------------------------------------------
def group_b() -> None:
    print(f"\n{LINE}\nB. THE WRITERS, LIFTED\n{LINE}")
    from altdata import feeds                                   # noqa: PLC0415
    from altdata.sources import sp500_members as sm             # noqa: PLC0415
    from altdata.sources import wgc_stock as wg                 # noqa: PLC0415
    day, mem = sm.parse_holdings(spy_workbook())
    tk = dict(mem)
    check(day == "2026-10-08" and len(mem) == 412 and tk.get("BRK-B") == 1.5
          and "-" not in tk and "2602335D" not in tk and tk["NVDA"] == 7.5,
          f"SPY's holdings by column name: the 'As of' day, a class share in Yahoo's "
          f"form (BRK-B), the cash and CVR lines skipped ({day}, {len(mem)} members)")
    for label, wb in (("no Weight column", spy_workbook(header=("Name", "Ticker", "X"))),
                      ("no 'As of' date", spy_workbook(as_of="today")),
                      ("too few members", spy_workbook(n=50))):
        try:
            sm.parse_holdings(wb)
            refused = False
        except ValueError:
            refused = True
        check(refused, f"a holdings file with {label} is refused, not half-read")
    robots_no = "User-agent: *\nDisallow: /us/en/intermediary/library-content/\n"
    saved = (sm.http_get_text, sm.http_get_response)
    try:
        sm.http_get_text, sm.http_get_response = (lambda *a, **k: robots_no), boom
        try:
            sm.fetch_holdings()
            stopped = False
        except PermissionError:
            stopped = True
        check(stopped, "a robots disallow stops the SPY fetch before the file is read")
    finally:
        sm.http_get_text, sm.http_get_response = saved
    check(wg.parse(WGC_HTML) == ("2026-06-30", 222600.0),
          "the WGC sentence parses: end-Q2 2026, 222,600 tonnes")
    try:
        wg.parse(WGC_HTML.replace("Total above-ground stock", "Above-ground gold"))
        refused = False
    except ValueError:
        refused = True
    check(refused, "a WGC page whose sentence changed is refused")
    check(not sm.HELD_FOR_D1C and not wg.HELD_FOR_D1C
          and {"sp500_members", "wgc_stock"} <= set(feeds.EXTERNAL_WRITERS)
          and set(sm.KEYS + wg.KEYS) <= set(feeds.external_keys()),
          "lifted (D1c ruled met for an append-only writer, 16 Oct 2026): both on "
          "feeds.EXTERNAL_WRITERS, their keys on the external freshness roster")
    saved = (sm.http_get_text, sm.http_get_response, sm.yahoo_closes,
             wg.http_get_text, wg.http_get_response)
    try:
        days = [d for d in weekdays("2026-09-28", "2026-10-08")]
        sm.http_get_text = wg.http_get_text = lambda *a, **k: "User-agent: *\nDisallow:\n"
        sm.http_get_response = lambda *a, **k: (spy_workbook(), {})
        asked: list[tuple[int, str]] = []

        def closes_fn(tickers, period):
            asked.append((len(tickers), period))
            return {t: [(d, 50.0 + i) for i, d in enumerate(days)]
                    for t in tickers if t in served}
        served = {"NVDA", "BRK-B", _ticker(0), _ticker(1), _ticker(2)}
        sm.yahoo_closes = closes_fn
        wg.http_get_response = lambda *a, **k: (WGC_HTML.encode(), {})
        with open_store(store([("sp500.member_close", "NVDA", "2026-09-25", 40.0),
                               ("sp500.member_close", "BRK-B", "2026-09-25", 40.0)])) as st:
            r1, r2 = sm.pull(db=st), wg.pull(db=st)
            closes = st.instruments(sm.CLOSE_KEY)
        check(r1["status"] == "OK" and r1["written"] == 412 + 5 * len(days)
              and r2["status"] == "OK" and r2["written"] == 1 and len(closes) == 5,
              f"each pull fetches its fixtures and writes in a temporary store "
              f"({r1['written']} weights and closes, {r2['written']} stock row)")
        check(sorted(asked) == [(2, sm.LATER_PERIOD), (410, sm.FIRST_PERIOD)],
              f"two years for the 410 members whose closes are not stored, ten days for "
              f"the 2 already held ({sorted(asked)})")
    finally:
        (sm.http_get_text, sm.http_get_response, sm.yahoo_closes,
         wg.http_get_text, wg.http_get_response) = saved


    jp_cpi_reader()
    uk_ca_cpi_readers()


def jp_csv(base: int, months_: list[str], codes=("0001", "0178", "0161"),
           level=lambda i, j: 100.0 + i * (j + 1) * 0.1) -> bytes:
    """A Statistics Bureau zmi<BASE>aa.csv in miniature: Shift-JIS, the six
    header rows (names, English names, codes, serials, weights), months down."""
    cols = ["0002", *codes, "0201"]
    head = [["\u985e\u30fb\u54c1\u76ee", *("x" for _ in cols)],
            ["Group/Item", *("x" for _ in cols)],
            ["\u985e\u30fb\u54c1\u76ee\u7b26\u53f7(Group/Item code)", *cols],
            ["Serial number", *("001" for _ in cols)],
            ["Weight", *("1" for _ in cols)],
            ["Weight per 10000", *("1" for _ in cols)]]
    body = [[m.replace("-", ""), *(f"{level(i, j):.3f}" for j, _ in enumerate(cols))]
            for i, m in enumerate(months_)]
    out = io.StringIO()
    csv.writer(out, lineterminator="\r\n").writerows(head + body)
    return out.getvalue().encode("cp932")


def ons_csv(cdid: str, months_: list[str], unit: str = "%",
            release: str = "16-09-2026") -> str:
    """The ONS generator's layout: labelled header rows, then annual, quarterly
    and monthly rows. Monthly values 2.0 + 0.1 per month."""
    names = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT",
             "NOV", "DEC")
    head = [("Title", f"FIXTURE {cdid}"), ("CDID", cdid), ("Source dataset ID", "MM23"),
            ("PreUnit", ""), ("Unit", unit), ("Release date", release),
            ("Next release", "21 October 2026"), ("Important notes", "")]
    body = [("2025", "3.0"), ("2025 Q4", "3.1")]
    body += [(f"{m[:4]} {names[int(m[5:]) - 1]}", f"{2.0 + 0.1 * i:.1f}")
             for i, m in enumerate(months_)]
    return "".join(f'"{a}","{b}"\n' for a, b in head + body)


def statcan_json(months_: list[str], vectors=(41690973, 41691233)) -> bytes:
    """Statistics Canada's WDS layout: one SUCCESS block per vector, each point
    with its month, index and releaseTime (local Ottawa)."""
    blocks = []
    for j, vid in enumerate(vectors):
        pts = [{"refPer": f"{m}-01", "value": 150.0 + i * 0.3 + j,
                "releaseTime": f"{m}-28T08:30"} for i, m in enumerate(months_)]
        blocks.append({"status": "SUCCESS",
                       "object": {"vectorId": vid, "vectorDataPoint": pts}})
    import json as _json                                         # noqa: PLC0415
    return _json.dumps(blocks).encode()


def uk_ca_cpi_readers() -> None:
    """The by-hand audit's two CPI readers (16 Oct 2026): fixtures, refusals,
    a robots disallow, and a pull into a temporary store."""
    from altdata import feeds                                   # noqa: PLC0415
    from altdata.sources import _base as base                   # noqa: PLC0415
    from altdata.sources import ons_cpi as oc                   # noqa: PLC0415
    from altdata.sources import statcan_cpi as sc               # noqa: PLC0415
    mm = months("2025-01", "2026-08")
    rows = oc.rows_from({"D7G7": ons_csv("D7G7", mm), "DKO8": ons_csv("DKO8", mm)})
    by = {(r["registry_key"], r["observed_at"]): r for r in rows}
    aug = by[("uk.cpi_core_yoy", "2026-08-01")]
    check(len(rows) == 2 * len(mm) and aug["value"] == round(2.0 + 0.1 * 19, 1)
          and aug["available_at"] == "2026-09-16T06:00:00.000000+00:00"
          and aug["availability_kind"] == "observed"
          and ("uk.cpi_yoy", "2025-01-01") in by,
          "the ONS file: monthly rows only (annual and quarterly skipped), the "
          "rate as published, stamped at the release date's 07:00 UK (06:00 UTC)")
    for text, why in ((ons_csv("DKO8", mm), "another series under the asked CDID"),
                      (ons_csv("D7G7", mm, unit="Index"), "another unit"),
                      (ons_csv("D7G7", mm, release=""), "no release date"),
                      (ons_csv("D7G7", mm, release="16-09-2099"), "a release in the future"),
                      (ons_csv("D7G7", []), "no monthly row")):
        try:
            oc.parse(text, "D7G7")
            check(False, f"the ONS reader refuses {why}")
        except ValueError:
            check(True, f"the ONS reader refuses {why}")
    srows = sc.rows_from(statcan_json(mm))
    sby = {(r["registry_key"], r["observed_at"]): r for r in srows}
    # Aug 2026 (i = 19) over Aug 2025 (i = 7): (150 + 5.7 + j) / (150 + 2.1 + j).
    want = round(((150.0 + 19 * 0.3 + 1) / (150.0 + 7 * 0.3 + 1) - 1) * 100, 1)
    got = sby[("ca.cpi_core_yoy", "2026-08-01")]
    check(got["value"] == want and got["available_at"] == "2026-08-28T12:30:00.000000+00:00"
          and min(d for k, d in sby if k == "ca.cpi_yoy") == "2026-01-01",
          f"Statistics Canada: the change on the year from the index, by hand "
          f"({want}%), stamped at the month's releaseTime (08:30 Ottawa); no month "
          f"without its year-earlier month")
    for data, why in ((statcan_json(mm, vectors=(41690973,)), "a missing vector"),
                      (statcan_json(mm, vectors=(41690973, 99999999)), "another vector"),
                      (statcan_json([]), "a vector with no point")):
        try:
            sc.rows_from(data)
            check(False, f"the Statistics Canada reader refuses {why}")
        except ValueError:
            check(True, f"the Statistics Canada reader refuses {why}")
    check({"ons_cpi", "statcan_cpi"} <= set(feeds.EXTERNAL_WRITERS)
          and set(oc.KEYS + sc.KEYS) <= set(feeds.external_keys()),
          "both on feeds.EXTERNAL_WRITERS, their four keys on the external roster")
    saved = (base.http_get_text, oc.http_get_response, sc.http_get_response)
    try:
        def no_robots(*a, **k):
            raise base.FetchError("HTTP 404 from https://www.ons.gov.uk/robots.txt: x")
        base.http_get_text = lambda *a, **k: "User-agent: *\nDisallow: /generator\n"
        oc.http_get_response = boom
        with open_store(store([])) as st:
            r0 = oc.pull(db=st)
        check(r0["status"] != "OK" and "robots" in str(r0.get("reason", "")),
              "an ONS robots disallow stops the fetch before any file is read")
        base.http_get_text = no_robots
        files = {oc.url_of("D7G7"): ons_csv("D7G7", mm).encode(),
                 oc.url_of("DKO8"): ons_csv("DKO8", mm).encode()}
        oc.http_get_response = lambda url, **k: (files[url], {})
        base_text = lambda *a, **k: "User-agent: *\nDisallow: /t1/tbl1/\n"
        with open_store(store([])) as st:
            r1 = oc.pull(db=st)
            base.http_get_text = base_text
            sc.http_get_response = lambda url, **k: (statcan_json(mm), {})
            r2 = sc.pull(db=st)
            n = count(st)
        check(r1["status"] == "OK" and r1["written"] == 2 * len(mm)
              and r2["status"] == "OK" and r2["written"] == 2 * (len(mm) - 12)
              and n == r1["written"] + r2["written"],
              f"robots.txt answered 404 is no rules (RFC 9309): the ONS pull writes "
              f"{r1['written']} rows, Statistics Canada {r2['written']}, in a temporary store")
    finally:
        base.http_get_text, oc.http_get_response, sc.http_get_response = saved


def jp_cpi_reader() -> None:
    from altdata import feeds                                   # noqa: PLC0415
    from altdata.sources import stat_jp_cpi as jc               # noqa: PLC0415
    m20 = months("2024-01", "2026-08")
    m25 = months("2025-01", "2026-08")
    f20 = jp_csv(2020, m20, level=lambda i, j: 100.0 + i * 0.2)
    f25 = jp_csv(2025, m25, level=lambda i, j: 99.0 + i * 0.3 + j)
    p = jc.parse(f25)
    check(set(p) == set(jc.KEYS) and len(p["jp.cpi_core_yoy"]) == len(m25),
          "Japan's CPI file read by item code (0001, 0178, 0161), months down")
    rows = jc.rows_from([(f25, "2026-09-18T00:00:00+00:00", "observed"),
                         (f20, "2026-09-17T00:00:00+00:00", "observed")])
    by = {(r["registry_key"], r["observed_at"]): r for r in rows}
    # 2026-08 from the 2025 base: index 99 + 19 x 0.3 + j over 99 + 7 x 0.3 + j.
    want_aug = round(((99.0 + 19 * 0.3 + 2) / (99.0 + 7 * 0.3 + 2) - 1) * 100, 2)
    # 2025-08 only in the 2020 base: 100 + 19 x 0.2 over 100 + 7 x 0.2.
    want_25 = round(((100.0 + 19 * 0.2) / (100.0 + 7 * 0.2) - 1) * 100, 2)
    got_aug = by[("jp.cpi_core_yoy", "2026-08-01")]
    check(got_aug["value"] == want_aug and got_aug["available_at"].startswith("2026-09-18")
          and by[("jp.cpi_core_yoy", "2025-08-01")]["value"] == want_25,
          f"the change on the year within one base, by hand: Aug 2026 {want_aug}% from the "
          f"2025 base (the newer decides), Aug 2025 {want_25}% from the 2020 base")
    check(min(d for k, d in by if k == "jp.cpi_yoy") == "2025-01-01",
          "no month without its year-earlier month in the same file (2025-01 first)")
    try:
        jc.parse(jp_csv(2025, m25, codes=("0001", "0161", "0999")))
        refused = False
    except ValueError:
        refused = True
    check(refused, "a file without one of the item codes is refused, not half-read")
    check("stat_jp_cpi" in feeds.EXTERNAL_WRITERS and set(jc.KEYS) <= set(feeds.external_keys()),
          "on feeds.EXTERNAL_WRITERS, its three keys on the external roster")
    saved = (jc.http_get_text, jc.http_get_response)
    try:
        jc.http_get_text = lambda *a, **k: "User-agent: *\nDisallow: /data/cpi/\n"
        jc.http_get_response = boom
        with open_store(store([])) as st:
            r0 = jc.pull(db=st)
        check(r0["status"] != "OK" and "robots" in str(r0.get("reason", "")),
              "a robots disallow stops the fetch before any file is read")
        jc.http_get_text = lambda *a, **k: "User-agent: *\nDisallow: /library/opac/\n"
        files = {jc.url_of("2025"): f25, jc.url_of("2020"): f20}
        jc.http_get_response = lambda url, **k: (
            files[url], {"Last-Modified": "Thu, 17 Sep 2026 23:31:21 GMT"})
        with open_store(store([])) as st:
            r = jc.pull(db=st)
            n = count(st)
        check(r["status"] == "OK" and r["written"] == n == 3 * (len(m20) - 12),
              f"on its fixture files it writes {n} rows in a temporary store")
    finally:
        jc.http_get_text, jc.http_get_response = saved


# ---------------------------------------------------------------------------
BIG = {"NVDA": 8.0, "AAPL": 7.0, "MSFT": 6.0, "AMZN": 4.0, "GOOGL": 2.0, "GOOG": 2.0,
       "AVGO": 3.0, "META": 3.0, "TSLA": 2.0, "MU": 1.5, "LLY": 1.5}


def weight_rows(w: dict, day: str = NOW_DAY) -> list[tuple]:
    small = {f"S{i:02d}": 0.5 for i in range(30)}
    return [("sp500.member_weight", t, day, v) for t, v in {**w, **small}.items()]


def conc(rows) -> dict:
    with open_store(store(rows)) as st:
        return tr.concentration(st, NOW, CFG)


def group_c() -> None:
    print(f"\n{LINE}\nC. ST-R5.31a THE PEAK-BAND FLAG\n{LINE}")
    c = conc(weight_rows(BIG))
    issuers = sorted({"NVDA": 8, "AAPL": 7, "MSFT": 6, "AMZN": 4, "GOOGL": 4, "AVGO": 3,
                      "META": 3, "TSLA": 2, "MU": 1.5, "LLY": 1.5}.values())
    check(c["state"] == "read" and c["top_share_pct"] == sum(issuers) == 40.0
          and "GOOG" not in c["top_names"] and c["flag"] and c["where"] == "inside the band",
          f"the ten largest issuers (GOOGL with GOOG) at exactly 40.0% fire the flag, "
          f"inside the band ({c.get('top_share_pct')}; ten LINES would be 38.5)")
    c2 = conc(weight_rows({**BIG, "LLY": 1.49}))
    check(c2["top_share_pct"] == 39.99 and not c2["flag"] and c2["where"] == "below the band",
          "39.99% does not fire: below the band")
    c3 = conc(weight_rows({**BIG, "NVDA": 12.01}))
    check(c3["top_share_pct"] == 44.01 and c3["flag"] and c3["where"] == "above the band",
          "44.01% reads above the band, the flag still on")
    basket = 8 + 6 + 7 + 4 + 2 + 2 + 3 + 2 + 3 + 1.5
    check(c["basket_share_pct"] == basket and c["basket_missing"] == ["AMD"],
          f"BofA's basket is mapped against the same file ({c['basket_share_pct']}%; "
          f"AMD absent from the fixture is named)")
    line = tr.concentration_line(c)
    check("40.0%" in line and "peak-band flag is on" in line
          and "overlay is not built" in line and "no weight" in line,
          "the line prints the share, the flag, and that the overlay it calibrates is "
          "not built and gets no weight")
    a = conc([])
    check(a["state"] == "absent" and "awaiting constituent holdings" in a["reason"],
          f"no holdings stored: absent, 'awaiting constituent holdings' ({a['reason'][:60]})")
    s = conc(weight_rows(BIG, "2026-09-30"))
    check(s["state"] == "absent" and "9 days old" in s["reason"],
          f"holdings older than a week are absent with their age ({s['reason']})")


# ---------------------------------------------------------------------------
DDS = [0, 0, -5, -5, -9.99, -10, -12, -15, -19.99, -20, -25, -30, -35, -3, -1, -8,
       -18, -22, -40, -50]


def breadth_rows(drop: int = 0, closes: bool = True) -> list[tuple]:
    days = weekdays("2025-09-01", NOW_DAY)
    rows = [("yfinance.mkt_gspc", None, d, 4000.0) for d in days[:-1]]
    rows.append(("yfinance.mkt_gspc", None, days[-1], 3900.0))
    for i, dd in enumerate(DDS):
        tk = f"M{i:02d}"
        rows.append(("sp500.member_weight", tk, NOW_DAY, 5.0))
        if not closes or i < drop:
            continue
        rows += [("sp500.member_close", tk, d, 100.0) for d in days[:-1]]
        last = 101.0 if dd == 0 else round(100.0 * (1 + dd / 100.0), 6)
        rows.append(("sp500.member_close", tk, days[-1], last))
    return rows


def group_d() -> None:
    print(f"\n{LINE}\nD. ST-R5.44a THE HISTOGRAM AND THE GAP\n{LINE}")
    with open_store(store(breadth_rows())) as st:
        b = tr.breadth(st, NOW, CFG)
    want = {"record_n": sum(1 for v in DDS if v >= 0),
            "within_10_n": sum(1 for v in DDS if -10 < v < 0),
            "off_10_20_n": sum(1 for v in DDS if -20 < v <= -10),
            "off_20_plus_n": sum(1 for v in DDS if v <= -20)}
    check(b["state"] == "read" and b["bucket_counts"] == want
          and want == {"record_n": 2, "within_10_n": 6, "off_10_20_n": 5,
                       "off_20_plus_n": 7},
          f"the four buckets by hand, the 10% and 20% edges in the deeper bucket "
          f"({b.get('bucket_counts')})")
    avg = round(statistics.mean(DDS), 2)
    check(b["avg_member_dd_pct"] == avg == -16.45 and b["index_dd_pct"] == -2.5
          and b["gap_pct"] == round(avg + 2.5, 2),
          f"the average member {avg}% off its 52-week high, the index -2.5%, the gap "
          f"{b.get('gap_pct')} pp")
    check([r[0] for r in tr.breadth_rows(b)] == [lab for _, lab in tr.BUCKET_LABELS]
          and tr.breadth_rows(b)[3][1:] == ["7", "35%"],
          "the histogram's rows: four buckets, members and share")
    with open_store(store(breadth_rows(drop=1))) as st:
        b95 = tr.breadth(st, NOW, CFG)
    with open_store(store(breadth_rows(drop=2))) as st:
        b90 = tr.breadth(st, NOW, CFG)
    check(b95["state"] == "read" and b95["coverage_pct"] == 95.0
          and b90["state"] == "absent"
          and b90["reason"] == "awaiting constituent prices (18 of 20 members hold a "
                               "year of closes)",
          f"95% coverage prints; 90% says 'awaiting constituent prices' ({b90['reason']})")
    with open_store(store(breadth_rows(closes=False))) as st:
        b0 = tr.breadth(st, NOW, CFG)
    check(b0["state"] == "absent" and b0["reason"].startswith("awaiting constituent prices")
          and "awaiting constituent prices" in tr.breadth_line(b0),
          "no closes stored: the histogram and the gap print 'awaiting constituent prices'")


# ---------------------------------------------------------------------------
def oil_rows(seed: int = 7) -> list[tuple]:
    rnd = random.Random(seed)
    days = weekdays("2023-09-01", NOW_DAY)
    b, s, t = 80.0, 4500.0, 4.0
    rows = [("fred.brent", None, days[0], b), ("yfinance.mkt_gspc", None, days[0], s),
            ("fred.yield_10y", None, days[0], t)]
    for i, d in enumerate(days[1:], start=1):
        e = rnd.gauss(0, 0.02)
        late = i > len(days) - 127
        rs = (-0.8 * e if late else 0.0) + rnd.gauss(0, 0.01)
        rt_ = (0.8 * e * 5 if late else 0.0) + rnd.gauss(0, 0.05)
        b, s, t = b * math.exp(e), s * math.exp(rs), t + rt_
        rows += [("fred.brent", None, d, b), ("yfinance.mkt_gspc", None, d, s),
                 ("fred.yield_10y", None, d, t)]
    return rows


def group_e() -> None:
    print(f"\n{LINE}\nE. ST-R5.32a THE OIL-SHOCK SIGNATURE\n{LINE}")
    days = ["d1", "d2", "d3", "d4"]
    up = tr.rolling_corr(dict(zip(days, [1, 2, 3, 4])), dict(zip(days, [2, 4, 6, 8])),
                         days, 4, 4)
    dn = tr.rolling_corr(dict(zip(days, [1, 2, 3, 4])), dict(zip(days, [8, 6, 4, 2])),
                         days, 4, 4)
    check(len(up) == 1 and abs(up[0][1] - 1) < 1e-12 and abs(dn[0][1] + 1) < 1e-12,
          "the rolling correlation against a hand case: +1 and -1, one full window")
    db = store(oil_rows())
    with open_store(db) as st:
        o = tr.oil_shock(st, NOW, CFG)
        ps, pt = o["percentile_brent_spx"], o["percentile_brent_10y"]
        check(o["state"] == "read" and o["supply_shock"] and ps <= 20 and pt >= 80
              and o["brent_spx_corr_ratio"] < 0 < o["brent_10y_corr_ratio"],
              f"a supply-shock window reads ON (Brent-SPX {o['brent_spx_corr_ratio']:+.2f} "
              f"at the {ps:.1f}th, Brent-10y {o['brent_10y_corr_ratio']:+.2f} at the {pt:.1f}th)")
        res = {}
        for name, (ks, kt) in {"at": (ps, pt), "spx_beyond": (ps - 1e-4, pt),
                               "ten_beyond": (ps, pt + 1e-4)}.items():
            c = copy.deepcopy(CFG)
            c["oil_shock"]["spx_below_pct"], c["oil_shock"]["ten_year_above_pct"] = ks, kt
            res[name] = tr.oil_shock(st, NOW, c)
    check(res["at"]["spx_leg"] and res["at"]["ten_year_leg"] and res["at"]["supply_shock"],
          "each leg fires AT its threshold (the percentile equal to it)")
    check(not res["spx_beyond"]["spx_leg"] and not res["spx_beyond"]["supply_shock"]
          and not res["ten_beyond"]["ten_year_leg"] and not res["ten_beyond"]["supply_shock"],
          "and not a hair beyond it: either leg off turns the signature off")
    line = tr.oil_shock_line(o)
    check("shorter than 20 years" in line and f"n={o['n_windows']:,}" in line
          and "supply-shock signature is ON" in line,
          "the line names a history shorter than 20 years, with its n of windows")
    with open_store(store([r for r in oil_rows() if r[0] != "fred.brent"])) as st:
        a = tr.oil_shock(st, NOW, CFG)
    check(a["state"] == "absent" and a["reason"] == "Brent not stored",
          "no Brent stored: absent with its reason")


# ---------------------------------------------------------------------------
EXP_KEYS = {"breakeven_5y5y": "fred.breakeven_5y5y", "cleveland_10y": "fred.expinf_10y",
            "sce_3y": "nyfed.sce_3y", "umich_5_10y": "umich.expect_5_10y"}


def exp_series(k: int, n: int = 129) -> list[float]:
    return [2.0 + 0.1 * k + 0.05 * ((i * (k + 3)) % 7) + (0.6 if i == n - 1 else 0.0)
            for i in range(n)]


def exp_rows(stale: tuple = (), absent: tuple = ()) -> list[tuple]:
    ms = months("2016-01", "2026-09")
    rows = []
    for k, (iid, key) in enumerate(EXP_KEYS.items()):
        if iid in absent:
            continue
        vals = exp_series(k, len(ms))
        use = ms[:-4] if iid in stale else ms
        rows += [(key, None, m + "-01", v) for m, v in zip(use, vals)]
    return rows


def exp_z(k: int, stale: bool = False) -> float:
    ms = months("2016-01", "2026-09")
    vals = exp_series(k, len(ms))
    if stale:
        vals = vals[:-4]
    win = vals[-120:]
    return round((win[-1] - statistics.mean(win)) / statistics.stdev(win), 2)


def group_f() -> None:
    print(f"\n{LINE}\nF. ST-R5.42a THE COMPOSITE\n{LINE}")
    with open_store(store(exp_rows())) as st:
        e = tr.expectations(st, NOW, CFG)
    zs = [exp_z(k) for k in range(4)]
    got = [r["z_score"] for r in e["inputs"]]
    check(got == zs and all(r["months_n"] == 120 for r in e["inputs"]),
          f"each input's z against statistics.stdev over its own 120 months ({got})")
    check(e["n_present"] == 4 and e["composite_z_score"] == round(sum(zs) / 4, 2),
          f"four inputs: the composite is their mean ({e['composite_z_score']})")
    with open_store(store(exp_rows(stale=("umich_5_10y",)))) as st:
        e3 = tr.expectations(st, NOW, CFG)
    mi = next(r for r in e3["inputs"] if r["id"] == "umich_5_10y")
    check(e3["n_present"] == 3 and e3["composite_z_score"] == round(sum(zs[:3]) / 3, 2)
          and not mi["present"] and "5 months old" in mi["reason"],
          f"Michigan stale (latest May 2026): three inputs, the composite on three "
          f"({mi['reason']})")
    with open_store(store(exp_rows(stale=("umich_5_10y",), absent=("sce_3y",)))) as st:
        e2 = tr.expectations(st, NOW, CFG)
    lines = tr.expectations_lines(e2)
    check(e2["composite_z_score"] is None and not e2["flag"]
          and "not printed -- 2 of 4 inputs present, fewer than 3" in lines[0],
          f"two inputs: the composite is refused ({lines[0][:70]})")
    comp = e["composite_z_score"]
    with open_store(store(exp_rows())) as st:
        c = copy.deepcopy(CFG)
        c["expectations"]["flag_z"] = comp
        on = tr.expectations(st, NOW, c)
        c["expectations"]["flag_z"] = comp + 0.01
        off = tr.expectations(st, NOW, c)
    check(on["flag"] and not off["flag"],
          f"the flag fires at its threshold ({comp:+.2f}) and not below it")
    dl = [x for x in tr.expectations_lines(e) if "2022 high" in x]
    hi22 = max(v for m, v in zip(months("2016-01", "2026-09"), exp_series(0))
               if m.startswith("2022"))
    check(dl and f"{hi22:.2f}%" in dl[0] and "not built" in dl[0],
          f"DEANCHOR's first leg prints against the 2022 high ({hi22:.2f}%), the flag "
          f"named as a definition only")


# ---------------------------------------------------------------------------
def ry_rows() -> list[tuple]:
    r = [("fred.oecd_10y_us", None, "2026-08-01", 4.8), ("fred.oecd_10y_us", None, "2026-09-01", 4.9),
         ("fred.core_cpi", None, "2025-09-01", 100.0), ("fred.core_cpi", None, "2026-09-01", 103.0),
         ("fred.cpi", None, "2025-09-01", 100.0), ("fred.cpi", None, "2026-09-01", 102.5),
         ("fred.tips_10y", None, "2026-09-10", 1.8), ("fred.tips_10y", None, "2026-09-24", 1.9),
         ("fred.oecd_10y_de", None, "2026-09-01", 3.4),
         ("fred.hicp_core_de", None, "2025-09-01", 100.0), ("fred.hicp_core_de", None, "2026-09-01", 102.2),
         ("fred.hicp_de", None, "2025-09-01", 100.0), ("fred.hicp_de", None, "2026-09-01", 102.0),
         ("fred.jp_10y", None, "2026-09-01", 3.0),
         ("jp.cpi_core_yoy", None, "2026-08-01", 1.9), ("jp.cpi_yoy", None, "2026-08-01", 1.6),
         ("fred.oecd_10y_fr", None, "2026-09-01", 4.4),
         ("fred.hicp_core_fr", None, "2025-04-01", 100.0), ("fred.hicp_core_fr", None, "2026-04-01", 101.5),
         ("fred.oecd_10y_mx", None, "2026-09-01", 9.35),
         ("em.cpi.yoy.mex", None, "2026-09-01", 3.8)]
    return r


def group_g() -> None:
    print(f"\n{LINE}\nG. ST-R5.39a REAL YIELDS\n{LINE}")
    with open_store(store(ry_rows())) as st:
        ry = tr.real_yields(st, NOW, CFG)
    by = {r["id"]: r for r in ry["rows"]}
    us, de = by["US"], by["DE"]
    check(us["nominal_pct"] == 4.9 and us["real_core_pct"] == round(4.9 - 3.0, 2)
          and us["real_headline_pct"] == round(4.9 - 2.5, 2) and us["linker_pct"] == 1.85,
          f"the US: real on core {us.get('real_core_pct')}%, on headline "
          f"{us.get('real_headline_pct')}%, the TIPS month's mean {us.get('linker_pct')}%")
    check(de["real_core_pct"] == round(3.4 - 2.2, 2) and de["real_headline_pct"] == round(3.4 - 2.0, 2)
          and "linker" in de.get("linker_gap", ""),
          "Germany on Eurostat's HICP, core and headline; its linker a named gap")
    jp = by["JP"]
    check(jp["real_core_pct"] == round(3.0 - 1.9, 2) and jp["real_headline_pct"] == round(3.0 - 1.6, 2)
          and jp["core_cpi_month"] == "2026-08" and not jp.get("em_core_gap"),
          "Japan on the Statistics Bureau's CPI: real on core (less fresh food and "
          "energy) and on headline, August's CPI against September's yield")
    d = {x["pair"]: x for x in ry["differentials"]}
    check(d["US-DE"]["spread_bp"] == round((1.9 - 1.2) * 100) == 70
          and d["US-JP"]["spread_bp"] == round((1.9 - 1.1) * 100) == 80,
          "US less DE, real on core: +70 bp by hand; US less JP +80 bp by hand")
    lines = tr.differential_lines(ry)
    check(lines == ["Real 10-year differential, US less DE, on core CPI: +70 bp (Sep 2026).",
                    "Real 10-year differential, US less JP, on core CPI: +80 bp (Sep 2026)."],
          f"the Currencies lines ({lines})")
    with open_store(store([r for r in ry_rows() if not r[0].startswith("jp.")])) as st:
        ry0 = tr.real_yields(st, NOW, CFG)
    d0 = {x["pair"]: x for x in ry0["differentials"]}
    check(d0["US-JP"]["spread_bp"] is None and "Japan" in d0["US-JP"]["reason"],
          "without Japan's CPI stored, US less JP is a gap, Japan named")
    uk_ca = ry_rows() + [("fred.gilt_10y", None, "2026-09-15", 4.6),
                         ("uk.cpi_core_yoy", None, "2026-08-01", 2.6),
                         ("uk.cpi_yoy", None, "2026-08-01", 3.1),
                         ("fred.oecd_10y_ca", None, "2026-09-01", 3.4),
                         ("ca.cpi_core_yoy", None, "2026-08-01", 2.1),
                         ("ca.cpi_yoy", None, "2026-08-01", 3.0)]
    with open_store(store(uk_ca)) as st:
        ry2 = tr.real_yields(st, NOW, CFG)
    b2 = {r["id"]: r for r in ry2["rows"]}
    gb, ca = b2["GB"], b2["CA"]
    check(gb.get("real_core_pct") == round(4.6 - 2.6, 2)
          and gb.get("real_headline_pct") == round(4.6 - 3.1, 2)
          and ca.get("real_core_pct") == round(3.4 - 2.1, 2)
          and ca.get("real_headline_pct") == round(3.4 - 3.0, 2),
          f"the UK on the ONS's CPI and Canada on Statistics Canada's: real on core "
          f"and on headline, by hand (GB {gb.get('real_core_pct')}%, CA "
          f"{ca.get('real_core_pct')}%) -- no longer gaps (the by-hand audit)")
    fr = by["FR"]
    check("real_core_pct" not in fr and "its core CPI is stale against the yield" in fr["gaps"],
          "France's HICP five months behind its yield: a gap, not a stale real yield")
    mx = by["MX"]
    check(mx["real_headline_pct"] == round(9.35 - 3.8, 2) and "real_core_pct" not in mx
          and mx.get("em_core_gap"),
          "Mexico on headline (IMF), the core gap named")
    ab = tr.real_yield_absent(ry)
    check(any(x.startswith("Brazil: no OECD 10-year") for x in ab)
          and any(x.startswith("Canada: its 10-year is not stored yet") for x in ab)
          and any(x.startswith("Linker real yields: the US's only; none on FRED for "
                               "United Kingdom, Japan, Germany, France, Italy") for x in ab)
          and any(x.startswith("Core CPI for Brazil, Mexico") and "headline" in x
                  for x in ab),
          "a country with no FRED series is a listed gap with its reason; the linker "
          "and EM-core gaps print once each")
    rows = tr.real_yield_rows(ry)
    check([r[0] for r in rows] == ["United States", "Japan", "Germany", "France", "Mexico"]
          and rows[0] == ["United States", "4.90%", "Sep 2026", "1.90%", "2.40%", "1.85%"],
          "the table: one row per country with a nominal yield, in the panel's order")


# ---------------------------------------------------------------------------
def group_h() -> None:
    print(f"\n{LINE}\nH. ST-R5.38a GOLD AGAINST WORLD EQUITIES\n{LINE}")
    rows = [("wgc.above_ground_t", None, "2026-06-30", 222600.0),
            ("yfinance.mkt_gold_front", None, "2026-08-31", 3900.0),
            ("yfinance.mkt_gold_front", None, "2026-09-30", 4000.0),
            ("fixture.world_cap_usd_bn", None, "2026-07-31", 105000.0),
            ("fixture.world_cap_usd_bn", None, "2026-08-31", 108000.0),
            ("fixture.world_cap_usd_bn", None, "2026-09-30", 110000.0)]
    with open_store(store(rows)) as st:
        nt = tr.gold_equity(st, NOW, CFG)
    check(CFG["gold_equity"].get("cap_key") is None and nt["state"] == "not_tracked"
          and tr.gold_equity_line(nt) == ("Gold against world equities — not tracked: no "
                                          "free source for world equity capitalisation."),
          "no free denominator: the line prints 'not tracked: no free source for world "
          "equity capitalisation' (the by-hand ACWI key dropped, 16 Oct 2026)")
    cfg2 = copy.deepcopy(CFG)
    cfg2["gold_equity"]["cap_key"] = "fixture.world_cap_usd_bn"
    with open_store(store(rows)) as st:
        g = tr.gold_equity(st, NOW, cfg2)
    want = round(100.0 * 222600 * 32150.7466 * 4000 / (110000 * 1e9), 3)
    check(g["state"] == "read" and g["ratio_pct"] == want and g["day"] == "2026-09-30",
          f"the ratio by hand: {want}% (222,600 t x 32,150.7466 oz/t x $4,000 over "
          f"$110,000bn), once a capitalisation key is configured")
    check(g["lens"]["n"] == 2 and g["lens"]["same"],
          "July's cap has no gold close within five days and is not used: n=2")
    line = tr.gold_equity_line(g)
    check("(n=2; shorter than 10 years)" in line,
          f"the percentile prints its real window and n ({line[-70:]})")
    with open_store(store(rows[1:])) as st:
        a = tr.gold_equity(st, NOW, cfg2)
    check(a["state"] == "absent" and "WGC above-ground stock" in a["reason"],
          f"no WGC stock stored: absent, named ({a['reason'][:70]})")
    with open_store(store(rows)) as st:
        subs = blk.slow_subsections(st, NOW)
    gs = next(s for s in subs if s["title"] == blk.GOLD_TITLE)
    check(any("WFE" in x and "login" in x for x in gs["not_tracked"])
          and gs["lines"] == [tr.gold_equity_line(nt)],
          "the quarterly WFE line is a listed gap; the sub-section prints the not-tracked "
          "line")


# ---------------------------------------------------------------------------
def diffusion_rows(n_areas: int = 24) -> list[tuple]:
    rows = []
    ms = months("2023-01", "2026-09")
    for a in range(n_areas):
        rate = 3.0
        for m in ms:
            if a == 23 and m > "2026-04":
                break
            if a < 10 and m == "2024-01":
                rate += 0.25
            if a < 10 and m == "2026-06":
                rate -= 0.25
            if 10 <= a < 16 and m == "2026-03":
                rate += 0.25
            rows.append(("bis.policy_rate", f"A{a:02d}", m + "-28", rate))
    rows += [("fred.oecd_cli_g7", None, "2026-09-01", 100.94),
             ("manual.global_pmi", None, "2026-09-01", 50.2)]
    return rows


def group_i() -> None:
    print(f"\n{LINE}\nI. ST-R5.43a GLOBAL POLICY DIFFUSION\n{LINE}")
    with open_store(store(diffusion_rows())) as st:
        d = tr.diffusion(st, NOW, CFG)
        ds = tr.diffusion_series(st, NOW, CFG)
    check(d["state"] == "read" and d["month"] == "2026-09" and d["areas_n"] == 23
          and d["cuts_n"] == 10 and d["hikes_n"] == 6
          and d["net_pct"] == round(100.0 * (10 - 6) / 23, 1),
          f"Sep 2026: 10 cut, 6 hiked, 23 counted (the area five months stale dropped): "
          f"net {d.get('net_pct')}%")
    jan = ds["months"]["2026-01"]
    check(jan == {"net_pct": round(-1000 / 24, 1), "cuts_n": 0, "hikes_n": 10, "areas_n": 24}
          and d["net_at_lead_pct"] == jan["net_pct"] and d["lead_from"] == "2026-01",
          f"eight months back (Jan 2026): ten last hiked, none cut, 24 counted, net "
          f"{jan['net_pct']}%")
    lines = tr.diffusion_lines(d)
    check(len(lines) == 2 and "100.94" in lines[1] and "50.2" in lines[1]
          and "Report-only until its lead is ledgered" in lines[1]
          and re.search(r"\(n=\d+; shorter than 10 years\)", lines[0]),
          "the lines: the index with its percentile's n, the CLI and the PMI at the lead, "
          "report-only")
    al = tr.ahead_line(d)
    check(al and "May 2027" in al and "unvalidated" in al,
          f"the ahead line names the month the lead reaches ({al})")
    with open_store(store(diffusion_rows(5))) as st:
        a = tr.diffusion(st, NOW, CFG)
    check(a["state"] == "absent" and "fewer than 20" in a["reason"],
          f"fewer than 20 central banks counted: absent ({a['reason']})")
    with open_store(store([])) as st:
        z = tr.diffusion(st, NOW, CFG)
    check(z["state"] == "absent" and "not stored yet" in z["reason"]
          and tr.ahead_line(z) is None, "nothing stored: absent, and no ahead line")


# ---------------------------------------------------------------------------
def strings(v) -> list[str]:
    if isinstance(v, str):
        return [v]
    if isinstance(v, dict):
        return [s for k, x in v.items() if k not in ("key", "fingerprint")
                for s in strings(x)]
    if isinstance(v, (list, tuple)):
        return [s for x in v for s in strings(x)]
    return []


def numeric_leaves(v, key: str = "") -> list[tuple[str, float]]:
    if isinstance(v, bool) or v is None:
        return []
    if isinstance(v, (int, float)):
        return [(key, v)]
    if isinstance(v, dict):
        return [x for k, y in v.items() for x in numeric_leaves(y, str(k))]
    if isinstance(v, (list, tuple)):
        return [x for y in v for x in numeric_leaves(y, key)]
    return []


def all_rows() -> list[tuple]:
    return (weight_rows(BIG) + breadth_rows() + exp_rows() + ry_rows()
            + diffusion_rows()
            + [("wgc.above_ground_t", None, "2026-06-30", 222600.0),
               ("yfinance.mkt_gold_front", None, "2026-09-30", 4000.0),
               ("jp.cpi_core_yoy", None, "2026-08-01", 1.9),
               ("jp.cpi_yoy", None, "2026-08-01", 1.6)])


def group_j() -> None:
    print(f"\n{LINE}\nJ. THE DISPLAY\n{LINE}")
    from altdata import numeral_audit as na                     # noqa: PLC0415
    from daily_cascade import stack_prose as sp                 # noqa: PLC0415
    from daily_cascade import weekly_stack as ws                # noqa: PLC0415
    from monthly_macro import stack as mstack                   # noqa: PLC0415
    db = store(all_rows())
    then = "2026-10-02T23:00:00+00:00"
    with open_store(db) as st:
        mech_w = ws.mechanics_week(st, [], NOW, {})
        plumb_w = ws.plumbing_week(st, NOW, then)
        pos_w = ws.positioning_week(st, NOW, then)
        mech_m = mstack.mechanics_section(st, "2026-09-01", "2026-09-30", NOW,
                                          mstack.stack_mod.config())
        plumb_m = mstack.plumbing_section(st, NOW, "2026-09-09T23:00:00+00:00", set(),
                                          mstack.stack_mod.config())
        ahead_m = mstack._with_growth_lead({"subsections": []}, st, NOW)
        slow = blk.slow_subsections(st, NOW)
        mech_mo = blk.mechanics_subsections(st, NOW, "monthly")
        plumb_mo = blk.plumbing_subsections(st, NOW, "monthly")
    tw = [s["title"] for s in mech_w["subsections"]]
    tm = [s["title"] for s in mech_m["subsections"]]
    check(tw.count(blk.CONC_TITLE) == tw.count(blk.OIL_TITLE) == 1
          and tm.count(blk.CONC_TITLE) == tm.count(blk.OIL_TITLE) == 1,
          "Mechanics, Weekly and Monthly: 'Concentration and breadth' and 'The oil-shock "
          "signature', once each")
    pw = [s["title"] for s in plumb_w["subsections"]]
    pm = [s["title"] for s in plumb_m["subsections"]]
    check(pw.count(blk.EXP_TITLE) == pw.count(blk.REAL_TITLE) == 1
          and pm.count(blk.EXP_TITLE) == pm.count(blk.REAL_TITLE) == 1,
          "Plumbing & rates, Weekly and Monthly: the composite and the real-yield panel")
    fx = next(s for s in plumb_w["subsections"] if s["title"] == "Global rates and FX")
    glob = next((s for s in plumb_m["subsections"] if s.get("bucket") == "global"), {})
    check(any("US less DE" in x for x in fx.get("lines") or [])
          and any("US less DE" in x for x in glob.get("lines") or []),
          "the US-DE and US-JP lines print in the Currencies read (the Weekly's Global "
          "rates and FX, the Monthly's global bucket)")
    alloc = next((s for s in pos_w["subsections"]
                  if s["title"].startswith("Investor allocation")), {})
    check(any(x.startswith("Gold against world equities — not tracked") for x in
              alloc.get("lines") or []),
          "item 38 prints beside item 30's allocation block (not tracked, said so)")
    check(any("US less JP, on core CPI" in x for x in fx.get("lines") or []),
          "the US-JP real differential prints in the Currencies read")
    check([s["title"] for s in slow] == [blk.GOLD_TITLE, blk.DIFF_TITLE]
          and "blk.slow_subsections" not in inspect.getsource(mstack.slow_layers)
          and "t1_rest_block.slow_subsections" in inspect.getsource(mstack.slow_layers),
          "the Monthly's Slow layers carry Factor V's line and the diffusion index")
    check([s["title"] for s in ahead_m["subsections"]] == [blk.AHEAD_TITLE]
          and "t1_rest_block.ahead_subsection(st, now)" in inspect.getsource(ws),
          "Ahead carries the growth lead's line, Weekly and Monthly")
    mine = mech_mo + plumb_mo + slow
    check(all(s.get("paragraph_wanted") is False for s in mine),
          "no sub-section asks the model for a paragraph")
    bad = [x for x in strings(mine) if "week" in x.lower() and not WEEK_OK.search(x)]
    check(not bad, f"at 'monthly' no week phrase ({bad[:2]})")
    untyped = sorted({k for s in mine for k, _ in numeric_leaves(s.get("data") or {})
                      if na.type_of_key(k) == na.TYPE_ANY})
    check(not untyped, f"every number in the sections' data has a typed field name "
                       f"(untyped: {untyped or 'none'})")
    lines = [x for s in mine for x in s.get("lines") or []]
    check(lines and not [x for x in lines if sp.filler_faults(x)],
          f"no printed line is filler ({len(lines)} lines)")
    causal = [x for x in lines if re.search(r"\b(because|drove|driven by|due to|caused|"
                                            r"on the back of|in response to)\b", x, re.I)]
    check(not causal, f"no printed line claims a cause ({causal[:1]})")
    regime_src = (REPO / "regime.py").read_text(encoding="utf-8")
    src = "".join((REPO / p).read_text(encoding="utf-8") for p in
                  ("altdata/st_r5_t1_rest.py", "daily_cascade/t1_rest_block.py"))
    ms = yaml.safe_load((REPO / "config" / "market_state.yaml").read_text(encoding="utf-8"))
    check("st_r5_t1_rest" not in regime_src and "t1_rest_block" not in regime_src
          and not re.search(r"^\s*(from|import)\s+regime\b", src, re.M)
          and "driver" not in ms["dimensions"]["inflation"]
          and ms["version"] == "market-state-v1.10",
          "report-only: regime.py reads none of it, it reads no regime, and the inflation "
          "dimension declares no driver (the object stays v1.10)")


# ---------------------------------------------------------------------------
def group_k() -> None:
    print(f"\n{LINE}\nK. THE REGISTRY AND THE PURITY\n{LINE}")
    from altdata import catalogue, derived                      # noqa: PLC0415
    keys = set()

    def walk(v):
        if isinstance(v, dict):
            for k, x in v.items():
                if isinstance(x, str) and (k.endswith("_key") or k in (
                        "key", "nominal", "core", "headline", "headline_yoy",
                        "core_yoy", "linker")):
                    keys.add(x)
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(CFG)
    unreg = sorted(k for k in keys if not (derived.registry_entry(k) or {}).get("units"))
    check(len(keys) >= 45 and not unreg,
          f"every key the reads use is registered with its units ({len(keys)} keys; "
          f"unregistered {unreg or 'none'})")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    new = ["sp500.member_weight", "sp500.member_close", "wgc.above_ground_t",
           "bis.policy_rate", "jp.cpi_core_yoy", "manual.global_pmi",
           "fred.expinf_10y", "fred.oecd_cli_g7", "fred.hicp_core_de", "fred.oecd_10y_kr",
           "uk.cpi_yoy", "uk.cpi_core_yoy", "ca.cpi_yoy", "ca.cpi_core_yoy"]
    check(all(k in reg["families"] and k in reg["long_windows"] for k in new),
          "the new series carry a family and a long window (the metric-lens rule)")
    check(derived.registry_entry("sp500.member_weight").get("units") == "percent_share"
          and derived.registry_entry("bis.policy_rate").get("units") == "percent_rate"
          and derived.registry_entry("manual.global_pmi").get("units") == "index_points",
          "units by meaning: a weight a share, a policy rate a rate, the PMI points")
    src = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))["sources"]
    check(all(src.get(s, {}).get("status") == "live"
              and src[s].get("implemented_by") == f"altdata/sources/{s}.py"
              for s in ("sp500_members", "wgc_stock", "stat_jp_cpi", "ons_cpi",
                        "statcan_cpi")),
          "sp500_members, wgc_stock, stat_jp_cpi, ons_cpi and statcan_cpi are "
          "registered sources, status live")
    cmds = catalogue.commands()
    check(all(m in cmds for m in ("altdata.st_r5_t1_rest", "altdata.sources.sp500_members",
                                  "altdata.sources.wgc_stock",
                                  "altdata.sources.stat_jp_cpi",
                                  "altdata.sources.ons_cpi",
                                  "altdata.sources.statcan_cpi")),
          "the catalogue names the six commands")
    import manual_input                                         # noqa: PLC0415
    gone = "manual.msci_acwi_mcap_usd_bn"
    readers = [str(p.relative_to(REPO)) for p in
               list(REPO.glob("**/*.py")) + list(REPO.glob("**/*.yaml"))
               if not any(x in p.parts for x in (".venv", ".git", "docs"))
               and not p.name.startswith("validate_st_r5")
               and gone in p.read_text(encoding="utf-8", errors="replace")]
    check(gone not in reg["metrics"] and gone not in reg["families"]
          and gone not in reg["long_windows"] and gone not in catalogue.resolved()
          and gone not in manual_input.manual_keys() and not readers,
          f"dropped (ruled 16 Oct 2026): {gone} -- not in the registry, the catalogue or "
          f"manual_input, and nothing reads it {readers or ''}")
    banned = {"anthropic", "requests", "urllib", "httpx", "yfinance"}
    bad = []
    for rel in ("altdata/st_r5_t1_rest.py", "daily_cascade/t1_rest_block.py"):
        tree = ast.parse((REPO / rel).read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            names = ([a.name for a in n.names] if isinstance(n, ast.Import) else
                     [n.module or ""] if isinstance(n, ast.ImportFrom) else [])
            for nm in names:
                if (nm.split(".")[0] in banned or "sources" in nm or "model_meter" in nm
                        or nm.endswith("_base")):
                    bad.append(f"{rel}: {nm}")
        txt = (REPO / rel).read_text(encoding="utf-8")
        if re.search(r"\.(write_many|write)\(", txt):
            bad.append(f"{rel}: writes the store")
    check(not bad, f"the reads import no fetcher or model and write no store ({bad or 'none'})")


def main() -> int:
    print(f"{LINE}\nSignal-triage Batch 6: the rest of Tranche 1 (31, 32, 38, 39, 42, 43, 44)\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h,
              group_i, group_j, group_k):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback                                    # noqa: PLC0415
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
