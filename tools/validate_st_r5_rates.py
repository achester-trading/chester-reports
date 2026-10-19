"""
Validation gate for signal-triage Batch 6, the rates-transmission cluster
(16 Oct 2026; docs/change-order-signal-triage-batch-6-2026-10-15.md, items 34,
36, 37 and 41, section 4 ruling 1; docs/briefs/st-r5-rates-notes.md).

FIXTURES only (tests/fixtures/st_r5_rates.json and rows built here), each in a
temporary store of its own -- no live store, no network, no model:

  A  THE WRITERS EXTENDED. The Bundesbank's 2-year read by its own series id (a
     response naming the 10-year is refused under the 2-year key) and one
     series failing does not stop the other; CFETS's curve stores the 2.0 and
     10.0 points; the fed funds pull reaches thirteen months; AAA and euro HY
     OAS join the FRED pull, percent and daily.
  B  THE HELD WRITERS. Redfin's files and the MBA release parse by column and by
     phrase ("NA" skipped; a changed template refused); the MBA robots check
     stops on a disallow; while HELD_FOR_D1C each pull fetches nothing and
     writes nothing, and neither is on a feeds roster; with the hold lifted (in
     a temporary store) each writes its rows.
  C  ST-R5.34a THE FLAG. +15/-15 bp fires with NFCI confirming; +10/-10 fires
     (at threshold); +9.9 or -9.9 does not (below); NFCI falling reads "not
     confirming"; the 12-month contract absent falls back to the longest
     horizon held at both ends and names it; no futures, or fewer than 28 days,
     is absent with its reason.
  D  ST-R5.34b THE PANEL. Eight rows in the order's order; Australia, Korea,
     Canada and the UK are gaps with their reasons and no figure; a country
     whose series is not stored says so; China, forward-only, is "short".
  E  ST-R5.36a HOUSING. Pending sales and their change on the year, active
     listings, months of supply ("NA" absent, never zero), metro breadth k of n,
     the mortgage rate, NAR by hand; with no Redfin rows, the hold's reason.
  F  ST-R5.37a MBA. The year-on-year change with its percentile, window and n;
     the level by hand against the 2023 floor; the close prints it on the
     release Wednesday only.
  G  ST-R5.41a THE QUALITY TAIL. CCC less BB and CCC less AAA; the co-signal at
     25 bp of excess fires, 24.9 does not, a narrowing CCC does not; each
     percentile prints its real window and n (three years on FRED's ICE
     series); the overlay is named as not built.
  H  THE DISPLAY. One "Rates transmission" sub-section in the Weekly's and the
     Monthly's Plumbing & rates; the close's items, the MBA line on Wednesday
     only; no week phrase at "monthly"; the filler, coincidence, readability and
     numeral audits on the printed lines; regime.py and this cluster do not
     touch each other.
  I  THE REGISTRY. Every key the cluster reads is registered with its units;
     the new keys carry a family and a long window; redfin and mba are
     registered sources, held; the catalogue names the three new commands.

    python tools/validate_st_r5_rates.py
"""

from __future__ import annotations

import datetime as dt
import inspect
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gate_tmp  # noqa: E402
import yaml  # noqa: E402

from altdata import observations  # noqa: E402
from altdata import st_r5_rates as rt  # noqa: E402
from daily_cascade import rates_transmission_block as blk  # noqa: E402

PASS = 0
FAIL = 0
LINE = "=" * 78
FIX = json.loads((REPO / "tests" / "fixtures" / "st_r5_rates.json")
                 .read_text(encoding="utf-8"))
CFG = rt.config()
NOW_DAY, BASE_DAY = "2026-10-09", "2026-09-11"          # 28 days apart
NOW = NOW_DAY + "T23:00:00+00:00"


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
    db = str(Path(gate_tmp.mkdtemp("str5_")) / "obs.db")
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


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------
def flag_rows(ten_bp: float, pol_bp: float, nfci: float = 0.05,
              futures: bool = True) -> list[tuple]:
    """10-year 4.00% on BASE_DAY; 12-month fed funds pricing 4.50%; NFCI -0.40.
    NOW_DAY moves each by the arguments."""
    rows = [("fred.yield_10y", None, BASE_DAY, 4.00),
            ("fred.yield_10y", None, NOW_DAY, 4.00 + ten_bp / 100.0),
            ("fred.nfci", None, BASE_DAY, -0.40),
            ("fred.nfci", None, NOW_DAY, -0.40 + nfci)]
    if futures:
        rows += [("fedfunds.futures_price", "2027-09", BASE_DAY, 95.50),
                 ("fedfunds.futures_price", "2027-10", NOW_DAY,
                  round(95.50 - pol_bp / 100.0, 4))]
    return rows


def panel_rows_fixture(drop: str = "") -> list[tuple]:
    rows = flag_rows(15, -15)
    legs = {"ea": ("bbk.bund_2y", "bbk.bund_10y", 2.10, -12, 2.60, 12),
            "us": ("fred.yield_2y", None, 3.90, -12, None, None),
            "jp": ("mof.jgb_2y", "mof.jgb_10y", 0.90, 3, 1.60, 4)}
    for cid, (k2, k10, lv2, d2, lv10, d10) in legs.items():
        if cid == drop:
            continue
        rows += [(k2, None, BASE_DAY, lv2), (k2, None, NOW_DAY, lv2 + d2 / 100.0)]
        if k10:
            rows += [(k10, None, BASE_DAY, lv10), (k10, None, NOW_DAY, lv10 + d10 / 100.0)]
    rows += [("cfets.cgb_2y", None, NOW_DAY, 1.258), ("cfets.cgb_10y", None, NOW_DAY, 1.67)]
    return rows


def spread_rows(ccc_bp: float, bb_bp: float, start: str = "2023-10-16",
                end: str = NOW_DAY) -> list[tuple]:
    """CCC 9.00% and BB 2.00% (a small deterministic wiggle, flat for the last
    60 days) through the day before NOW_DAY, then moved by the arguments on NOW_DAY."""
    rows = []
    days = weekdays(start, end)
    calm = (dt.date.fromisoformat(end) - dt.timedelta(days=60)).isoformat()
    for i, d in enumerate(days):
        # The wiggle stops 60 days before the end, so the 28-day base is flat.
        w = ((i * 7) % 11 - 5) / 1000.0 if d < calm else 0.0
        if d == days[-1]:
            ccc, bb = 9.00 + ccc_bp / 100.0, 2.00 + bb_bp / 100.0
        else:
            ccc, bb = 9.00 + w, 2.00 + w / 2
        rows += [("fred.ccc_oas", None, d, ccc), ("fred.bb_oas", None, d, bb),
                 ("fred.aaa_oas", None, d, 0.45), ("fred.hy_oas", None, d, 3.20 + w),
                 ("fred.euro_hy_oas", None, d, 3.40 - w)]
    return rows


def redfin_rows() -> list[tuple]:
    from altdata.sources import redfin                          # noqa: PLC0415
    out = []
    for r in (redfin.country_rows(FIX["redfin_country_csv"], "x", "observed")
              + redfin.metro_rows(FIX["redfin_metro_csv"], "x", "observed")):
        out.append((r["registry_key"], r["instrument"], r["observed_at"], r["value"]))
    return out


def mba_rows(n_weeks: int = 110, last_yoy: float = -12.0) -> list[tuple]:
    end = dt.date.fromisoformat(NOW_DAY)
    rows = []
    for i in range(n_weeks):
        d = (end - dt.timedelta(days=7 * (n_weeks - 1 - i))).isoformat()
        rows.append(("mba.purchase_nsa_yoy", None, d,
                     last_yoy if i == n_weeks - 1 else float((i * 5) % 21 - 10)))
    rows.append(("mba.purchase_sa_wow", None, NOW_DAY, -3.0))
    return rows


# ---------------------------------------------------------------------------
def group_a() -> None:
    print(f"\n{LINE}\nA. THE WRITERS EXTENDED\n{LINE}")
    from altdata import config as acfg, fed_funds, feeds        # noqa: PLC0415
    from altdata.sources import bundesbank as bbk, cfets        # noqa: PLC0415
    now = dt.datetime(2026, 10, 11, 22, tzinfo=dt.timezone.utc)

    def csv_for(series_id: str, pts) -> str:
        head = "DATAFLOW;BBK_STD_FREQ;TIME_PERIOD;OBS_VALUE;BBK_ID;BBK_UNIT;BBK_TITLE;OBS_STATUS"
        return "﻿" + "\n".join([head] + [f"BBK:BBSIS(1.0);D;{d};{v};{series_id};Prozent;x;"
                                             for d, v in pts]) + "\n"
    two = csv_for(bbk.SERIES_ID_2Y, FIX["bbk_2y_points"])
    rows = bbk.rows_from_csv(two, now, bbk.SERIES_ID_2Y, bbk.KEY_2Y)
    check(len(rows) == 2 and {r["registry_key"] for r in rows} == {"bbk.bund_2y"}
          and rows[-1]["value"] == 2.01
          and all(r["availability_kind"] == "reconstructed" for r in rows),
          "the Bund 2-year reads by its own id (R02XX), '.' skipped, reconstructed")
    try:
        bbk.rows_from_csv(csv_for(bbk.SERIES_ID, FIX["bbk_2y_points"]), now,
                          bbk.SERIES_ID_2Y, bbk.KEY_2Y)
        refused = False
    except ValueError:
        refused = True
    check(refused, "a response naming the 10-year is refused under the 2-year key")
    check(bbk.KEYS == ["bbk.bund_10y", "bbk.bund_2y"]
          and feeds.static_keys("bundesbank") == bbk.KEYS
          and feeds.static_keys("cfets") == cfets.KEYS,
          "both writers' KEYS read the same from source (the freshness roster)")
    saved = bbk.http_get_response
    ten = csv_for(bbk.SERIES_ID, [("2026-10-09", "2.60")])

    def half(url, params=None, timeout=None, headers=None, **k):
        if url == bbk.URL_2Y:
            raise OSError("simulated 2-year outage")
        return ten.encode("utf-8"), {}
    try:
        bbk.http_get_response = half
        with open_store(store([])) as st:
            r = bbk.pull(db=st)
            held = {k for k, in st.conn.execute(
                "SELECT DISTINCT registry_key FROM observations")}
        check(r["status"] == "OK" and held == {"bbk.bund_10y"},
              "the 2-year failing does not stop the 10-year (each series on its own)")
        bbk.http_get_response = boom
        with open_store(store([])) as st:
            r = bbk.pull(db=st)
            check(r["status"] == "STALE" and count(st) == 0,
                  "both failing: STALE, nothing written")
    finally:
        bbk.http_get_response = saved
    g = cfets.cgb_rows(FIX["cfets_curve"], "2026-10-09T08:00:00+00:00")
    got = {r["registry_key"]: r["value"] for r in g}
    check(got == {"cfets.cgb_10y": 1.6737, "cfets.cgb_2y": 1.258}
          and "cfets.cgb_2y" in cfets.KEYS,
          "CFETS stores the curve's 2.0 and 10.0 points (and nothing else)")
    months = [f"{y:04d}-{m:02d}" for y, m in
              fed_funds.months_from(dt.date(2026, 10, 16), fed_funds.CONTRACT_MONTHS)]
    check(fed_funds.CONTRACT_MONTHS >= 13 and "2027-10" in months,
          f"the fed funds pull reaches the contract 12 months ahead "
          f"({fed_funds.CONTRACT_MONTHS} months, to {months[-1]})")
    specs = {s.key: s for s in acfg.FRED_PULL_SERIES}
    check(specs.get("aaa_oas") and specs["aaa_oas"].fred_id == "BAMLC0A1CAAA"
          and specs.get("euro_hy_oas") and specs["euro_hy_oas"].fred_id == "BAMLHE00EHYIOAS"
          and all(specs[k].units == "%" and specs[k].freq == "daily"
                  for k in ("aaa_oas", "euro_hy_oas")),
          "AAA and euro HY OAS join the FRED pull, percent and daily")


def group_b() -> None:
    print(f"\n{LINE}\nB. THE HELD WRITERS\n{LINE}")
    from altdata import feeds                                   # noqa: PLC0415
    from altdata.sources import mba, redfin                     # noqa: PLC0415
    c = redfin.country_rows(FIX["redfin_country_csv"], "2026-10-12T11:46:15+00:00",
                            "observed")
    by = {(r["registry_key"], r["observed_at"]): r["value"] for r in c}
    check(len(c) == 11 and by[("redfin.pending_sales", "2026-09-01")] == 320000
          and ("redfin.months_of_supply", "2026-09-01") not in by
          and by[("redfin.months_of_supply", "2026-08-01")] == 4.0,
          "Redfin national rows by column name; an 'NA' month is absent, never zero")
    m = redfin.metro_rows(FIX["redfin_metro_csv"], "x", "observed")
    check(len(m) == 6 and {r["instrument"] for r in m} == {"101", "102", "103"},
          "the metro rows carry the region id as instrument; 'NA' skipped")
    try:
        redfin.country_rows("\"PERIOD BEGIN\",\"REGION TYPE\"\n", "x", "observed")
        refused = False
    except ValueError:
        refused = True
    check(refused, "a Redfin file without its columns is refused")
    want = {"mba_release_decrease": ("2026-10-09", -3.0, -12.0),
            "mba_release_increase": ("2026-10-02", 5.0, 4.0),
            "mba_release_unchanged": ("2026-09-25", 0.0, -7.0)}
    got = {k: tuple(mba.parse_release(FIX[k]).values()) for k in want}
    check(got == want, f"the MBA headline read by phrase: decreased, increased, "
                       f"remained unchanged ({got})")
    try:
        mba.parse_release(FIX["mba_release_changed_template"])
        refused = False
    except ValueError:
        refused = True
    check(refused, "a release whose sentences changed is refused, not half-read")
    check(mba.latest_link(FIX["mba_newsroom_html"]).endswith(
        "/2026/10/14/mortgage-applications-decrease-in-latest-mba-weekly-survey")
          and mba.latest_link(FIX["mba_newsroom_html"]).startswith("https://www.mba.org/"),
          "the newest weekly-survey release is picked from the newsroom")
    url = mba.latest_link(FIX["mba_newsroom_html"])
    check(mba.robots_ok(FIX["mba_robots_allow"], url)
          and not mba.robots_ok(FIX["mba_robots_disallow"], url),
          "robots.txt read with its wildcards: the newsroom allowed, then disallowed")
    saved_t, saved_r = mba.http_get_text, mba.http_get_response
    try:
        mba.http_get_text = lambda *a, **k: FIX["mba_robots_disallow"]
        mba.http_get_response = boom
        try:
            mba.fetch_rows()
            stopped = False
        except PermissionError:
            stopped = True
        check(stopped, "a disallow stops the MBA fetch before the newsroom is read")
    finally:
        mba.http_get_text, mba.http_get_response = saved_t, saved_r
    rosters = [v for k, v in vars(feeds).items() if k.isupper()
               and isinstance(v, (tuple, list)) and all(isinstance(x, str) for x in v)]
    on = [w for w in ("redfin", "mba") if any(w in r for r in rosters)]
    check(redfin.HELD_FOR_D1C and mba.HELD_FOR_D1C and not on,
          f"both are HELD for D1c and on no feeds roster ({on or 'none'})")
    saved = (redfin.http_get_response, mba.http_get_text, mba.http_get_response)
    try:
        redfin.http_get_response = mba.http_get_text = mba.http_get_response = boom
        with open_store(store([])) as st:
            r1, r2 = redfin.pull(db=st), mba.pull(db=st)
            n = count(st)
        check(r1["status"] == r2["status"] == "HELD" and r1["written"] == r2["written"] == 0
              and n == 0 and "D1c" in r1["reason"],
              "while held, each pull fetches nothing and writes nothing, and says why")

        def rf(url, timeout=None, **k):
            text = (FIX["redfin_country_csv"] if url == redfin.COUNTRY_URL
                    else FIX["redfin_metro_csv"])
            return text.encode("utf-8"), {"Last-Modified": "Mon, 12 Oct 2026 11:46:15 GMT"}

        def mr(url, timeout=None, **k):
            body = FIX["mba_newsroom_html"] if url == mba.NEWSROOM_URL \
                else FIX["mba_release_decrease"]
            return body.encode("utf-8"), {}
        redfin.http_get_response, mba.http_get_response = rf, mr
        mba.http_get_text = lambda *a, **k: FIX["mba_robots_allow"]
        redfin.HELD_FOR_D1C = mba.HELD_FOR_D1C = False
        with open_store(store([])) as st:
            r1, r2 = redfin.pull(db=st), mba.pull(db=st)
        check(r1["status"] == "OK" and r1["written"] == 17
              and r2["status"] == "OK" and r2["written"] == 2,
              f"with the hold lifted (a temporary store), each writes its rows "
              f"({r1['written']}, {r2['written']})")
    finally:
        redfin.HELD_FOR_D1C = mba.HELD_FOR_D1C = True
        redfin.http_get_response, mba.http_get_text, mba.http_get_response = saved


# ---------------------------------------------------------------------------
def flag(rows) -> dict:
    with open_store(store(rows)) as st:
        return rt.tightening(st, NOW, CFG)


def group_c() -> None:
    print(f"\n{LINE}\nC. ST-R5.34a THE MARKET DOES THE TIGHTENING\n{LINE}")
    t = flag(flag_rows(15, -15))
    ln = rt.tightening_line(t)
    check(t["state"] == "on" and t["confirms"] is True and t["ten_bp"] == 15.0
          and t["policy_bp"] == -15.0 and t["policy"]["contract"] == "2027-10"
          and t["policy"]["base_contract"] == "2027-09",
          "10-year +15 bp, 12-month pricing -15 bp: on, NFCI confirming; the "
          "constant horizon rolls 2027-09 to 2027-10")
    check("doing the tightening" in ln and "(descriptive; unvalidated, n=0)" in ln
          and "confirming" in ln and "over 28 days" in ln, f"the line: {ln[:90]}")
    check(flag(flag_rows(10, -10))["state"] == "on", "at threshold (+10/-10 bp): on")
    check(flag(flag_rows(9.9, -10))["state"] == "off"
          and flag(flag_rows(10, -9.9))["state"] == "off"
          and flag(flag_rows(-15, -15))["state"] == "off",
          "below either threshold, or the 10-year falling: off")
    off = flag(flag_rows(9.9, -10))
    check("flag off" in rt.tightening_line(off) and "fires at" in rt.tightening_line(off),
          "the off line names the thresholds")
    nc = flag(flag_rows(15, -15, nfci=-0.05))
    check(nc["state"] == "on" and nc["confirms"] is False
          and "not confirming" in rt.tightening_line(nc),
          "NFCI easing: still on, printed as not confirming")
    a = flag(flag_rows(15, -15, futures=False))
    check(a["state"] == "absent" and "no fed funds futures" in a["reason"]
          and "not read" in rt.tightening_line(a),
          "no futures stored: absent, with its reason")
    rows = flag_rows(15, -15, futures=False) + [
        ("fedfunds.futures_price", "2027-08", BASE_DAY, 95.50),
        ("fedfunds.futures_price", "2027-09", NOW_DAY, 95.65)]
    fb = flag(rows)
    check(fb["state"] == "on" and fb["policy"]["horizon_months"] == 11
          and "11-month (the 12-month contract is not yet held)" in rt.tightening_line(fb),
          "the 12-month contract absent: the longest horizon held at both ends, named")
    short = flag_rows(15, -15, futures=False) + [
        ("fedfunds.futures_price", "2027-10", "2026-10-01", 95.5),
        ("fedfunds.futures_price", "2027-10", NOW_DAY, 95.6)]
    s = flag(short)
    check(s["state"] == "absent" and "28 days are not yet held" in s["reason"],
          "fewer than 28 days of futures: absent, with its reason")


def group_d() -> None:
    print(f"\n{LINE}\nD. ST-R5.34b THE G8 2-YEAR PANEL\n{LINE}")
    with open_store(store(panel_rows_fixture())) as st:
        rows = rt.panel(st, NOW, CFG)
    ids = [r["id"] for r in rows]
    check(ids == ["au", "ea", "kr", "ca", "us", "jp", "uk", "cn"],
          f"eight rows in the order's order ({ids})")
    gaps = {r["id"]: r for r in rows if r["state"] == "gap"}
    check(set(gaps) == {"au", "kr", "ca", "uk"}
          and all(r.get("reason") and "yield_pct" not in r for r in gaps.values())
          and "key" in gaps["kr"]["reason"] and "robots" in gaps["uk"]["reason"]
          and "D1c" in gaps["au"]["reason"] and "D1c" in gaps["ca"]["reason"],
          "Australia, Korea, Canada and the UK are gaps with their reasons, no figure")
    by = {r["id"]: r for r in rows}
    check(by["ea"]["state"] == "tightening" and by["ea"]["two_bp"] == -12.0
          and by["ea"]["ten_bp"] == 12.0 and by["jp"]["state"] == "not"
          and by["us"]["state"] == "tightening",
          "the euro area and the US read tightening (10-year up, 2-year down); Japan not")
    check(by["cn"]["state"] == "short" and "28 days" in by["cn"]["reason"],
          "China, forward-only, says it does not yet hold 28 days")
    table = blk.panel_rows(rows)
    au = table[0]
    check(au[1] == "gap" and au[2] == au[3] == "—" and "RBA" in au[4],
          "the table prints a gap as 'gap' with its reason and no figure")
    with open_store(store(panel_rows_fixture(drop="jp"))) as st:
        jp = next(r for r in rt.panel(st, NOW, CFG) if r["id"] == "jp")
    check(jp["state"] == "absent" and jp["reason"] == "its 2-year is not stored yet"
          and not re.search(r"\b(?:fred|mof|bbk|cfets)\.", jp["reason"]),
          "a country whose series is not stored says so, by name, never by store id")


def group_e() -> None:
    print(f"\n{LINE}\nE. ST-R5.36a THE HOUSING BLOCK\n{LINE}")
    rows = redfin_rows() + [("fred.mortgage_30y", None, "2026-09-10", 7.10),
                            ("fred.mortgage_30y", None, "2026-10-08", 7.42)]
    with open_store(store(rows)) as st:
        h = rt.housing(st, NOW, CFG)
    check(not h["absent"] and h["month"] == "2026-09-01" and h["pending"] == 320000
          and h["pending_yoy_pct"] == round((320000 / 340000 - 1) * 100, 2)
          and h["active"] == 1500000 and h["months_supply"] is None,
          "September's pending sales, their change on the year, active listings; "
          "months of supply 'NA' is absent")
    b = h["breadth"]
    check(b["falling"] == 2 and b["n"] == 3,
          "metro breadth: 2 of the 3 metros holding both months are below a year earlier")
    lines = rt.housing_lines(h)
    txt = " ".join(lines)
    check("2 of 3 top metros" in txt and "7.42%" in txt and "+32 bp over 28 days" in txt
          and "months of supply" not in txt
          and "NAR pending home sales index: by hand, not entered" in txt,
          "the lines: breadth, the mortgage rate and its change, NAR not entered")
    with open_store(store(rows + [("manual.nar_phsi", None, "2026-09-01", 71.4)])) as st:
        h2 = rt.housing(st, NOW, CFG)
    check("NAR pending home sales index 71.4 (2026-09-01, entered by hand)"
          in " ".join(rt.housing_lines(h2)), "NAR's index by hand, as the cross-check")
    with open_store(store([])) as st:
        e = rt.housing(st, NOW, CFG)
    check(e["absent"] and "held until D1c" in rt.housing_lines(e)[0],
          "no Redfin rows: the hold's reason prints, not a blank")


def group_f() -> None:
    print(f"\n{LINE}\nF. ST-R5.37a THE MBA WEEKLY LINE\n{LINE}")
    with open_store(store(mba_rows())) as st:
        m = rt.mba(st, NOW, CFG)
    ln = rt.mba_line(m)
    check(not m["absent"] and m["week"] == NOW_DAY and m["yoy_pct"] == -12.0
          and m["wow_pct"] == -3.0 and m["lens"]["n_full"] == 110,
          "the latest survey's changes and its year-on-year history (n=110)")
    check("n=110" in ln and "shorter than 5 years" in ln and "since" in ln
          and "weekly survey" in ln,
          f"the percentile prints its real window and n: {ln[60:170]}")
    check("by hand, not entered" in ln and "~127" in ln,
          "no level entered: says so, with the 2023 floor")
    with open_store(store(mba_rows() + [("manual.mba_purchase_index", None,
                                         NOW_DAY, 139.0)])) as st:
        lv = rt.mba_line(rt.mba(st, NOW, CFG))
    check("Level 139.0" in lv and "+12.0 against the 2023 floor of ~127" in lv,
          "the level by hand against the 2023 floor")
    check(rt.mba_prints_on("2026-10-14", m, CFG) and not rt.mba_prints_on("2026-10-13", m, CFG)
          and not rt.mba_prints_on("2026-10-21", m, CFG),
          "the close prints it on the release Wednesday only, and not a stale week")
    with open_store(store([])) as st:
        a = rt.mba(st, NOW, CFG)
    check(a["absent"] and "held until D1c" in rt.mba_line(a),
          "no MBA rows: the hold's reason")


def tail(rows) -> dict:
    with open_store(store(rows)) as st:
        return rt.quality_tail(st, NOW, CFG)


def group_g() -> None:
    print(f"\n{LINE}\nG. ST-R5.41a THE QUALITY TAIL\n{LINE}")
    q = tail(spread_rows(40, 15))
    check(q["cosignal"] == "on" and q["excess_bp"] == 25.0
          and q["ccc_bb_bp"] == 725.0 and q["ccc_aaa_bp"] == 895.0,
          "CCC +40 bp against BB +15 bp: 25 bp of excess, the co-signal on; CCC less "
          "BB 725 bp, CCC less AAA 895 bp")
    check(tail(spread_rows(39.9, 15))["cosignal"] == "off",
          "24.9 bp of excess: off (below threshold)")
    check(tail(spread_rows(-10, -40))["cosignal"] == "off",
          "CCC narrowing, less than BB: off (CCC must widen)")
    lines = rt.quality_tail_lines(q)
    txt = " ".join(lines)
    check("shorter than 5 years" in txt and "n=" in txt and "since 2023-10-16" in txt,
          "three years of FRED's ICE series: the percentile names that window and n")
    check("which is not built" in txt and "HY Spread Acceleration" in txt
          and "(descriptive; unvalidated, n=0)" in txt,
          "the co-signal is named against an overlay not built")
    check("Europe against the US" in txt and "Euro CCC: by hand when reported" in txt,
          "the US-Europe line and the euro CCC by hand")
    long = tail(spread_rows(40, 15, start="2019-01-02"))
    lt = " ".join(rt.quality_tail_lines(long))
    check(not long["ccc_bb_lens"]["same"] and "of 5 years (n=" in lt and "since 2019-01-02" in lt,
          "with more than five years stored, both windows print, each with its n")
    with open_store(store([])) as st:
        e = rt.quality_tail(st, NOW, CFG)
    check(e["absent"] and "not read" in rt.quality_tail_lines(e)[0],
          "no CCC or BB: absent, with its reason")


# ---------------------------------------------------------------------------
# validate_regime group L's two retired words, spelled apart so that this gate,
# which checks for them, does not itself trip that group's search of tracked .py.
RETIRED_WORDS = ("fed" + "_path", "driver" + "_cell")
WEEK_OK = re.compile(r"the week before the month|Week change|weekly|52-week", re.I)


def strings(v) -> list[str]:
    if isinstance(v, str):
        return [v]
    if isinstance(v, dict):
        return [s for k, x in v.items() if k not in ("key", "fingerprint")
                for s in strings(x)]
    if isinstance(v, (list, tuple)):
        return [s for x in v for s in strings(x)]
    return []


def group_h() -> None:
    print(f"\n{LINE}\nH. THE DISPLAY AND THE EXISTING AUDITS\n{LINE}")
    from altdata import numeral_audit as na                     # noqa: PLC0415
    from daily_cascade import readability                       # noqa: PLC0415
    from daily_cascade import stack as stack_mod                # noqa: PLC0415
    from daily_cascade import stack_prose as sp                 # noqa: PLC0415
    from daily_cascade import weekly_stack as ws                # noqa: PLC0415
    from monthly_macro import stack as mstack                   # noqa: PLC0415
    rows = (panel_rows_fixture() + spread_rows(40, 15) + redfin_rows() + mba_rows()
            + [("fred.mortgage_30y", None, NOW_DAY, 7.42)])
    db = store(rows)
    then = "2026-10-02T23:00:00+00:00"
    with open_store(db) as st:
        wk = ws.plumbing_week(st, NOW, then)
        mo = mstack.plumbing_section(st, NOW, "2026-09-09T23:00:00+00:00", set(),
                                     mstack.stack_mod.config())
        sub_m = blk.subsection(st, NOW, "monthly")
        wed = blk.close_items(st, "2026-10-14T23:00:00+00:00", "2026-10-14")
        tue = blk.close_items(st, "2026-10-13T23:00:00+00:00", "2026-10-13")
    wt = [s for s in wk["subsections"] if s.get("title") == blk.TITLE]
    check(len(wt) == 1 and len(wt[0]["table"]["rows"]) == 8
          and wt[0]["table"]["columns"] == blk.COLUMNS
          and "Australia, Korea, Canada, United Kingdom" in wt[0]["table_note"],
          "the Weekly's Plumbing & rates carries one 'Rates transmission' sub-section, "
          "the panel its table, the gaps named in its note")
    check([s.get("title") for s in mo["subsections"]].count(blk.TITLE) == 1,
          "the Monthly's Plumbing (bucketed) carries it once")
    bad = [s for s in strings(sub_m) if "week" in s.lower() and not WEEK_OK.search(s)]
    check(not bad, f"at 'monthly' it prints no week phrase ({bad[:2]})")
    keys = [i["key"] for i in wed]
    check(keys == ["plumb:rt_tightening", "plumb:rt_quality_tail", "plumb:rt_mba"]
          and "plumb:rt_mba" not in [i["key"] for i in tue],
          "the close: the flag and the quality tail daily, the MBA line on Wednesday only")
    src = inspect.getsource(stack_mod.build)
    check("rates_transmission_block.close_items" in src,
          "the close's build appends them to Plumbing & rates")
    lines = wt[0]["lines"] + [i["text"] for i in wed]
    check(lines and not [x for x in lines if sp.filler_faults(x)],
          f"no printed line is filler ({len(lines)} lines)")
    causal = [x for x in lines if re.search(r"\b(because|drove|driven by|due to|caused|"
                                            r"on the back of|in response to|reacting to)\b",
                                            x, re.I)]
    check(not causal, f"no printed line claims a cause ({causal[:1]})")
    check(all(readability.figures(x) is not None for x in lines),
          "the readability figure count reads every line")
    b = wt[0]["data"]["rates_transmission"]
    t = b["tightening"]
    first = rt.tightening_line(t).split(";")[0]
    r = na.audit(first, na.with_signed({"ten_bp": t["ten_bp"], "policy_bp": t["policy_bp"],
                                        "window_days": t["window_days"],
                                        "horizon_months": t["policy"]["horizon_months"],
                                        "contract": t["policy"]["contract"],
                                        "base_day": t["policy"]["base_day"],
                                        "day": t["policy"]["day"],
                                        "series_kind": "yield"}))
    check(r.passed, f"the numeral audit finds the flag's figures in its data ({r.reason()[:90]})")
    q = b["quality_tail"]
    co = rt.quality_tail_lines(q)[1].split(" (")[0]
    r = na.audit(co, na.with_signed({"ccc_change_bp": q["ccc_change_bp"],
                                     "bb_change_bp": q["bb_change_bp"],
                                     "excess_bp": q["excess_bp"],
                                     "window_days": q["window_days"],
                                     "series_kind": "spread"}))
    check(r.passed, f"the numeral audit finds the co-signal's figures in its data "
                    f"({r.reason()[:90]})")
    wrong = f"The spread read {q['ccc_bb_bp']:.0f}%."
    check(na.audit(wrong, wt[0]['data']).n_unmatched >= 1
          and na.audit(f"The spread read {q['ccc_bb_bp']:.0f} bp.", wt[0]['data']).passed,
          "every figure in the data names its unit: CCC less BB quoted as a percent is "
          "refused, in bp it passes (validate_weekly_complete J audits the section)")
    regime_src = (REPO / "regime.py").read_text(encoding="utf-8")
    mine = "".join((REPO / p).read_text(encoding="utf-8") for p in
                   ("altdata/st_r5_rates.py", "daily_cascade/rates_transmission_block.py"))
    ms = yaml.safe_load((REPO / "config" / "market_state.yaml").read_text(encoding="utf-8"))
    check("st_r5_rates" not in regime_src and "rates_transmission" not in regime_src
          and not re.search(r"^\s*(from|import)\s+regime\b", mine, re.M)
          and not any(w in mine for w in RETIRED_WORDS)
          and "driver" not in ms["dimensions"]["rates"],
          "report-only: regime.py reads none of it, it reads no regime, and the rates "
          "dimension still declares no driver")


def group_i() -> None:
    print(f"\n{LINE}\nI. THE REGISTRY\n{LINE}")
    from altdata import catalogue, derived                      # noqa: PLC0415
    keys = set()
    for sec in ("tightening", "housing", "mba", "quality_tail"):
        keys |= {v for k, v in (CFG.get(sec) or {}).items() if k.endswith("_key")}
    for p in CFG.get("panel") or []:
        keys |= {p[k] for k in ("two_year_key", "ten_year_key") if p.get(k)}
    unreg = sorted(k for k in keys if not (derived.registry_entry(k) or {}).get("units"))
    check(len(keys) >= 25 and not unreg,
          f"every key the cluster reads is registered with its units "
          f"({len(keys)} keys; unregistered {unreg or 'none'})")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    new = ["bbk.bund_2y", "cfets.cgb_2y", "fred.aaa_oas", "fred.euro_hy_oas",
           "redfin.pending_sales", "redfin.months_of_supply", "mba.purchase_nsa_yoy"]
    check(all(k in reg["families"] and k in reg["long_windows"] for k in new),
          "the new series carry a family and a long window (the metric-lens rule)")
    src = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))["sources"]
    check(all(src.get(s, {}).get("status") == "held"
              and src[s].get("implemented_by") == f"altdata/sources/{s}.py"
              for s in ("redfin", "mba")),
          "redfin and mba are registered sources, status held")
    cmds = catalogue.commands()
    check(all(m in cmds for m in ("altdata.st_r5_rates", "altdata.sources.redfin",
                                  "altdata.sources.mba")),
          "the catalogue names the three new commands")


def main() -> int:
    print(f"{LINE}\nSignal-triage Batch 6: the rates-transmission cluster\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h,
              group_i):
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
