#!/usr/bin/env python3
"""
Validation gate for the stacked Monthly, first half. (reporting-stack brief; T3)

    python tools/validate_monthly_stack.py

A SYNTHETIC SEPTEMBER 2026 in a temporary store -- a code gate never reads the
live store, and no figure here is real. The 1 Oct 2026 edition is built through
monthly_macro.stack with a fake model client:

  A STACK       ten sections in the brief's order at the matrix's Monthly
                column, then Slow layers, then the detail tables in the brief's
                order; the config carries the column, the budget and the three
                reading-time targets.
  B READING     the reading time is computed (prose words at 250 a minute plus 20
                seconds a chart) and printed in the header beside its target.
  C DEALER      the retrospective from the month's stored scorecard rows: flags,
                counts and hit rates over 20+ sessions; "insufficient sessions
                (n=...)" below 20, with no prose asked for; a flag word the
                per-session flags do not support is refused.
  D PHASE A     every Monthly v2 Phase A fact printed, each exactly once: no
                Phase A id twice, no table row twice, the takeaways once, the
                themes' first sentences not repeated as a summary.
  E BUDGET      7,000 prose words and 10 charts; words count prose only (a table
                adds none); over budget, paragraphs go, "(trimmed)" prints, and no
                claim, item or table is cut.
  F RETRY       a section the audit withholds is retried once with the reason fed
                back; a second failure is withheld with both reasons; a fault is
                not retried.
  G REGISTRY    the gate is in the Makefile's list.

SECOND HALF:

  H SCANS       the scans ingest: each docs/scans/*.md reference table stored as
                sourced figures (URL, the scan's own section, as-of; a slide only
                when recorded), idempotent, immutable, point in time by the read
                date; advice refused, nothing outside the reference table read;
                Slow layers prints them from the store only.
  I YTD         GTM-14: the cross-asset year to date from the store's proxies,
                ranked, total return with dividends unreinvested, cash at the
                bill; a class without a proxy or a close says why.
  J TRIPLE      the slow layers' level rows as latest / long-run average /
                percentile, the data-as-of date and each window printed; full
                history and five years until 6e; a short history says so.
  K CHARTS      M1-M9 by the Weekly's mechanics: the plan inside the cap, PNG by
                Content-ID and SVG on disk, the mobile rule, titles with span and
                dates, only listed levels drawn (one list with the prose), each
                in its section, unavailable with its reason, delivered from the
                archive.
  L READING     the Reading chapter between Narratives and Ahead (D1): the
                month's register entries in group order, hyperlinked title
                lines, stored summaries verbatim (no audit, no budget cut, in the
                reading time), list items' lines, withheld without a URL, shelf
                a voices URL match footnoted, the due list, the empty month.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import os
import re
import sys
import types
from pathlib import Path

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here if os.path.basename(_here) == "tools"
                else os.path.join(_here, "tools"))
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78
PASS = FAIL = 0
REPORT_DATE = "2026-10-01"
AS_OF = "2026-10-01T10:00:00+00:00"
M_START, M_END = "2026-08-31", "2026-09-30"
PREV = "2026-09-01"

# THE STORES ARE POINTED AWAY BEFORE ANY IMPORT THAT OPENS ONE.
TD = gate_mkdtemp(prefix="validate_monthly_stack_")
DB = str(Path(TD) / "monthly.db")
os.environ["CHESTER_DB"] = DB
os.environ["CHESTER_PIN_LOG_PATH"] = str(Path(TD) / "pin_log.csv")


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def weekdays(first: str, last: str) -> list[str]:
    d, out = dt.date.fromisoformat(first), []
    while d <= dt.date.fromisoformat(last):
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def point(db: str) -> None:
    from altdata import config, observations
    from register import store as register_store
    observations.DEFAULT_DB = register_store.DEFAULT_DB = db
    config.COMPUTED_DIR = str(Path(TD) / "computed")
    config.PIN_LOG_PATH = os.environ["CHESTER_PIN_LOG_PATH"]


def card(day: str, i: int) -> dict:
    """One synthetic scorecard row. Every third session closes at max pain
    (pinned); every fourth crosses the flip on a wide range (amplified)."""
    close = 600.0 + i
    mp = close if i % 3 == 0 else close + 6.0
    crossed = i % 4 == 0
    return {"session": day, "symbol": "SPY",
            "gamma_regime": "negative" if crossed else "positive",
            "net_gex_morning": (-2.0e9 if crossed else 3.0e9),
            "net_gex_close": (-1.5e9 if crossed else 2.5e9),
            "flip_morning": close - 1.0, "flip_crossed": crossed,
            "close": close, "prior_close": close - 1.0,
            "session_high": close + (6.0 if crossed else 1.0),
            "session_low": close - (6.0 if crossed else 1.0),
            "session_range_pct": 2.0 if crossed else 0.33,
            "session_return_pct": 1.8 if i == 7 else 0.2,
            "max_pain": mp, "call_wall_morning": close + 20.0,
            "put_wall_morning": close - 20.0, "atm_iv_30d": 15.0}


def months(first: str, last: str) -> list[str]:
    y, m = int(first[:4]), int(first[5:7])
    out = []
    while f"{y:04d}-{m:02d}-01" <= last:
        out.append(f"{y:04d}-{m:02d}-01")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def cape_series() -> list[tuple[str, float]]:
    """1990-01 to 2026-09: a slow wave, the latest month high in its five years."""
    ds = months("1990-01-01", "2026-09-01")
    return [(d, round(20.0 + 8.0 * math.sin(i / 30.0) + i / 40.0, 3))
            for i, d in enumerate(ds)]


def gld_series() -> list[tuple[str, float]]:
    return [(d, 100.0 + i) for i, d in enumerate(months("2015-01-01", "2026-09-01"))]


def seed(db: str, dealer_sessions: int) -> None:
    point(db)
    from altdata import events, narratives, observations, probability_ledger
    import regime
    now_iso = "2026-10-01T09:00:00+00:00"
    obs = []

    def put(key, inst, day, v):
        obs.append({"registry_key": key, "instrument": inst, "observed_at": day,
                    "available_at": f"{day}T21:00:00+00:00", "value": v,
                    "source": "synthetic"})
    # The scorecard's month-ends, and the plumbing and leadership legs.
    for key, a, b in (("yfinance.mkt_gspc", 5000.0, 5250.0),
                      ("yfinance.mkt_qqq", 480.0, 490.0),
                      ("fred.yield_2y", 3.90, 3.80), ("fred.yield_10y", 4.00, 4.25),
                      ("fred.yield_30y", 4.50, 4.60), ("fred.hy_oas", 3.00, 3.20),
                      ("calc.yield_curve_2s10s", 0.10, 0.45),
                      ("fred.breakeven_10y", 2.30, 2.35)):
        put(key, None, M_START, a)
        put(key, None, M_END, b)
    for i, s in enumerate(("xlk", "xlf", "xle", "xlv", "xli", "xlp", "xly", "xlu",
                           "xlb", "xlre", "xlc", "spy", "iwm", "rsp")):
        put(f"yfinance.mkt_{s}", None, M_START, 100.0)
        put(f"yfinance.mkt_{s}", None, M_END, 100.0 + (i % 7) - 3)
    # GTM-14's proxies: the prior year's last close, the month end, and HYG's
    # dividends (one inside the year, one before it). EEM has no year-start
    # close, so its class must say so; the bill accrues at 4.00% throughout.
    for s, a, b in (("spy", 90.0, None), ("iwm", 104.0, None), ("efa", 50.0, 55.0),
                    ("xlre", 88.0, None), ("hyg", 80.0, 82.0), ("agg", 100.0, 99.0)):
        put(f"yfinance.mkt_{s}", None, "2025-12-31", a)
        if b is not None:
            put(f"yfinance.mkt_{s}", None, M_END, b)
    put("yfinance.mkt_eem", None, M_END, 45.0)
    put("yfinance.mkt_hyg_dividend", None, "2025-12-15", 0.5)
    put("yfinance.mkt_hyg_dividend", None, "2026-03-02", 1.0)
    put("fred.tbill_3m", None, "2025-12-01", 4.0)
    put("fred.tbill_3m", None, M_END, 4.0)
    # THE SLOW LAYERS' TRIPLE: CAPE monthly over 36 years, a forward P/E with
    # one observation (a window shorter than five years), and GLD monthly.
    for d, v in cape_series():
        put("shiller.cape", None, d, v)
    obs.append({"registry_key": "damodaran.pe_forward", "instrument": "Total Market",
                "observed_at": "2026-01-05", "available_at": "2026-01-06T12:00:00+00:00",
                "value": 21.5, "source": "synthetic"})
    for d, v in gld_series():
        put("yfinance.mkt_gld", None, d, v)
    days = weekdays("2026-09-01", M_END)[:dealer_sessions]
    for i, d in enumerate(days):
        put("yfinance.mkt_vix", None, d, 16.0)
        obs.append({"registry_key": "dealer.scorecard_day", "instrument": "SPY",
                    "observed_at": d, "available_at": f"{d}T21:30:00+00:00",
                    "value": json.dumps(card(d, i), sort_keys=True),
                    "source": "synthetic"})
    with observations.ObservationStore(db) as st:
        st.write_many(obs)
        for day, credit in ((PREV, "easy"), (M_END, "stressed")):
            regime.store_object({
                "session": day, "computed_at": f"{day}T21:00:00+00:00",
                "config_version": "fixture", "method_version": "fixture",
                "dials": {"macro": {"state": "calm" if credit == "easy" else "mixed"},
                          "vol": {"state": "normal"}, "gamma": {"state": "positive"}},
                "dimensions": {"credit": {"state": credit, "percentile": 12.0,
                                          "members": []}},
                "contradictions": ([{"id": "equities_vs_credit", "open_state": "open",
                                     "magnitude": 2.4, "threshold_z": 2.0,
                                     "persistence_days": 6, "since": "2026-09-22"}]
                                   if credit == "stressed" else [])}, st)
    nr = narratives.NarrativeRegister(db)
    nr.conn.execute(
        "INSERT INTO narratives (narrative_id, name, status, state, direction,"
        " opened, linked_dimensions, implied_outcome, story_query, origin,"
        " created_at, updated_at) VALUES ('yen_carry', 'The yen carry',"
        " 'active', 'emerging', 'Yen-funded carry is being unwound.', ?,"
        " '{}', '{}', 'yen_carry', 'seed', ?, ?)", ("2026-09-15", now_iso, now_iso))
    nr.conn.commit()
    nr.close()
    es = events.EventStore(db)
    for i, (typ, at, source, title, pay) in enumerate([
            ("headline", "2026-09-18T12:00:00+00:00", "google_news",
             "Yen jumps as BoJ signals hike - Reuters",
             json.dumps({"query": "yen_carry"})),
            ("headline", "2026-09-18T13:00:00+00:00", "google_news",
             "Carry trade unwinds - Bloomberg.com", json.dumps({"query": "yen_carry"})),
            ("release", "2026-09-11T12:30:00+00:00", "bls_cpi",
             "Consumer Price Index -- August", "{}"),
            ("scheduled", "2026-10-28T18:00:00+00:00", "claims_registry",
             "FOMC statement -- 2026-10-28", "{}")]):
        es.conn.execute(
            "INSERT INTO events (content_hash, type, observed_at, available_at,"
            " ingested_at, source, title, payload) VALUES (?,?,?,?,?,?,?,?)",
            (f"fixture-{i}", typ, at, "2026-09-19T14:00:00+00:00", now_iso, source,
             title, pay))
    es.conn.commit()
    es.close()
    with probability_ledger.ProbabilityLedger(db) as led:
        led.record(source="narrative_register",
                   scenario_set="hypothesis:yen_carry:primary",
                   claim="USD/JPY is lower at the horizon (fixture).",
                   probability=0.55, emitted_at="2026-09-20T20:00:00+00:00",
                   horizon_date="2026-11-30",
                   resolution_criterion="fred.usd_jpy below its emission level")
        pid = led.record(source="monthly_macro", scenario_set="monthly_macro:2026-09",
                         claim="A resolved fixture weight.", probability=0.7,
                         emitted_at="2026-09-02T12:00:00+00:00",
                         horizon_date="2026-09-25", resolution_criterion="fixture")
        led.resolve(pid, 1, resolved_at="2026-09-25T21:00:00+00:00")


def build_payload() -> dict:
    """The Monthly's payload as of the 1 Oct cutoff, its clock pinned there."""
    from altdata import session
    from monthly_macro import payload
    saved = (session.session_date, session.session_date_obj, payload.previous_monthly)
    session.session_date = lambda *a, **k: REPORT_DATE
    session.session_date_obj = lambda *a, **k: dt.date.fromisoformat(REPORT_DATE)
    payload.previous_monthly = lambda as_of=None: PREV
    try:
        return payload.build(AS_OF, run_id="fixture-run")
    finally:
        session.session_date, session.session_date_obj, payload.previous_monthly = saved


class Resp:
    def __init__(self, t):
        self.content = [types.SimpleNamespace(type="text", text=t)]
        self.model = "fixture-model"
        self.stop_reason = "end_turn"


def plain(system: str) -> str:
    """A clean reply naming its own section, so no two sections print the same
    sentence (The read's sentences are withheld where another section repeats
    them)."""
    m = re.search(r"THE SECTION: (.+?)\.", system)
    # No digits: a section title such as "Looking ahead, 2-3 months" would put
    # figures in the reply that its data does not carry.
    name = (re.sub(r"[\d,\-–]+", " ", m.group(1)).split("  ")[0].strip()
            if m else "This section")
    return (f"{name} moved little over the month.\n\nFor {name}, that argues "
            f"for reading the next prints before drawing a conclusion.")


def client(calls: list, script: dict):
    """`script`: a marker in the system prompt -> a list of replies, served in
    turn (the last repeats); anything else gets plain(). A reply that is an
    Exception is raised, as a failed API call would be."""
    served: dict = {}

    def create(**k):
        sysp = k["system"]
        calls.append(sysp)
        for mark, replies in script.items():
            if mark in sysp:
                n = served.get(mark, 0)
                served[mark] = n + 1
                r = replies[min(n, len(replies) - 1)]
                if isinstance(r, Exception):
                    raise r
                return Resp(r)
        return Resp(plain(sysp))
    return types.SimpleNamespace(messages=types.SimpleNamespace(create=create))


def printed_rows(ed: dict) -> list[tuple]:
    """Every table row the edition prints, with where it prints."""
    out = []

    def tabs(b):
        return [b.get("table")] + list(b.get("tables") or [])
    for s in list(ed["sections"]) + list(ed.get("detail") or []):
        if s.get("empty"):
            continue
        for t in tabs(s):
            out += [(tuple(map(str, r)), s["id"]) for r in (t or {}).get("rows") or []]
        for ss in s.get("subsections") or []:
            for t in tabs(ss):
                out += [(tuple(map(str, r)), f"{s['id']}/{ss.get('title')}")
                        for r in (t or {}).get("rows") or []]
    return out


FIXTURE_SCAN = """# Fixture Guide -- quarterly read

**Edition:** Fixture Guide, 3Q 2026 -- data as of 30 June 2026 (40 slides).
**Read on:** 5 July 2026. **Source:** https://example.org/fixture-guide.pdf (stable URL).

## 1. The read

We would overweight duration here. This sentence is ours and is never ingested.

## 6. Reference table -- 3Q 2026 (as of 30 Jun 2026)

| Metric | Value | Long-run comparison |
|---|---|---|
| Forward P/E | 18.1x (slide 5) | 30-yr avg 16.9x |
| Duration call | overweight long duration | — |
| Credit | IG OAS 90bp | avg 140bp |

## 7. After the table

| Metric | Value | Long-run comparison |
|---|---|---|
| Not ingested | 1 | — |
"""


def scans_group(p: dict, cfg: dict, ed: dict, out: dict) -> None:
    """H: the scans ingest (T3 second half, step 1)."""
    import sqlite3
    from altdata import scans
    from monthly_macro import stack as ms
    from daily_cascade import cadence as cadence_mod, stack_render as sr
    print(f"\n{LINE}\nH. THE SCANS INGEST: SOURCED FIGURES, NO STORED SOURCE NOT "
          f"PRINTED\n{LINE}")
    jpm = REPO / "docs" / "scans" / "jpm-gtm-2026q4.md"
    sdir = Path(TD) / "scans"
    sdir.mkdir(exist_ok=True)
    fx = sdir / "fixture-guide-2026q3.md"
    fx.write_text(FIXTURE_SCAN, encoding="utf-8")
    nourl = sdir / "nourl-guide-2026q3.md"
    nourl.write_text(FIXTURE_SCAN.replace("https://example.org/fixture-guide.pdf",
                                          "(no link recorded)"), encoding="utf-8")
    db = str(Path(TD) / "scans.db")
    first = scans.ingest([jpm, fx, nourl], db_path=db)
    again = scans.ingest([jpm, fx, nourl], db_path=db)
    by = {s["scan_id"]: s for s in first["scans"]}
    check(by["jpm-gtm-2026q4"]["figures"] == 44 and by["jpm-gtm-2026q4"]["added"] == 44
          and again["added"] == 0,
          f"the JPM Guide's §6 reference table stores 44 figures, and a re-ingest "
          f"adds none ({again['added']})")
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM scan_figures WHERE scan_id = 'jpm-gtm-2026q4'")]
    check(rows and all(r["source_url"].startswith("https://am.jpmorgan.com/")
                       and r["section_ref"] == "§6" and r["as_of"] == "2026-09-30"
                       and r["read_on"] == "2026-10-03" for r in rows),
          "each carries the URL, the scan's own section (§6) and the as-of date "
          "(30 Sep 2026), read 3 Oct")
    check(all(r["slide"] is None for r in rows),
          "the JPM scan recorded no slide numbers, and none is stored: ingested as "
          "it stands")
    fxr = {r["metric"]: dict(r) for r in conn.execute(
        "SELECT * FROM scan_figures WHERE scan_id = 'fixture-guide-2026q3'")}
    check(fxr.get("Forward P/E", {}).get("slide") == 5
          and scans.source_ref(fxr["Forward P/E"]) == "§6, slide 5"
          and fxr.get("Credit", {}).get("slide") is None,
          "a slide the scan recorded is stored and printed as \"§6, slide 5\"; a "
          "row without one has none")
    refused = {(r["scan_id"], r["metric"]): r["reason"] for r in first["refused"]}
    check("Duration call" not in fxr
          and "recommendation" in refused.get(("fixture-guide-2026q3",
                                               "Duration call"), ""),
          "a reference-table row that reads as advice (\"overweight\") is refused "
          "and named, never stored")
    check("Not ingested" not in fxr and not any(
              "duration here" in json.dumps(r) for r in fxr.values()),
          "only the reference-table section is read: the scan's own read and a "
          "later table are not ingested")
    check(not conn.execute("SELECT COUNT(*) FROM scan_figures WHERE scan_id = "
                           "'nourl-guide-2026q3'").fetchone()[0]
          and refused.get(("nourl-guide-2026q3", "Credit")) == "no source URL",
          "a scan with no source URL stores nothing: every row refused, \"no "
          "source URL\"")
    try:
        conn.execute("INSERT INTO scan_figures (scan_id, family, title, metric, "
                     "value, source_url, section_ref, as_of, read_on, scan_path, "
                     "ingested_at) VALUES ('x','x','x','m','1','','§6','2026-09-30',"
                     "'2026-10-03','x','now')")
        schema_refuses = False
    except sqlite3.IntegrityError:
        schema_refuses = True
    try:
        conn.execute("UPDATE scan_figures SET value = '0' WHERE id = 1")
        immutable = False
    except sqlite3.DatabaseError:
        immutable = True
    conn.close()
    check(schema_refuses and immutable,
          "the schema refuses a row without a URL underneath the writer, and a "
          "stored figure is never edited")
    check(not [r for r in scans.latest("2026-10-02", db) if r["family"] == "jpm-gtm"]
          and [r["family"] for r in scans.latest("2026-10-02", db)] == ["fixture-guide"] * 2
          and len([r for r in scans.latest("2026-10-31", db)
                   if r["family"] == "jpm-gtm"]) == 44,
          "point in time: a cutoff before the read (2 Oct) sees no JPM figure; the "
          "1 Nov Monthly's (31 Oct) sees all 44")
    sl = next(s for s in ed["sections"] if s["id"] == "slow")
    check(not any(ss["title"].startswith("Sourced figures") for ss in sl["subsections"])
          and "no scan ingested by this edition's cutoff" in json.dumps(sl),
          "the fixture's 1 Oct edition prints no scan figure (none ingested in its "
          "store) and says so")
    slow = ms.slow_layers(p, cfg, None, "2026-11-01T10:00:00+00:00", db)
    subs = [ss for ss in slow["subsections"]
            if ss["title"] == "Sourced figures: Guide to the Markets, U.S., 4Q 2026"]
    printed = {tuple(r[:2]) for r in (subs[0]["table"]["rows"] if subs else [])}
    stored = {(r["metric"], r["value"]) for r in scans.latest("2026-10-31", db)
              if r["family"] == "jpm-gtm"}
    check(subs and printed == stored and len(printed) == 44,
          "in Slow layers, the JPM figures print in their own sub-section, every "
          "printed row exactly a stored row")
    page = (sr.subsection_html(subs[0], "month", cadence_mod.get("monthly"))
            if subs else "")
    check("am.jpmorgan.com" in page and "data as of 2026-09-30" in page
          and "recommendations are not printed" in page and "CAPE" in page,
          "with its source line: the URL, §6, the as-of and read dates")
    # Phrases from the scan's own read and borrow list, outside its §6.
    ours = ["a sector trade wearing a regional label", "Bull Rebuttal gate",
            "Tier 1 — build into the pipeline"]
    scan_text = jpm.read_text(encoding="utf-8")
    check(all(x in scan_text for x in ours)
          and not any(x in page or x in json.dumps(slow) for x in ours),
          "nothing outside the reference table -- our read, the borrow list, any "
          "recommendation -- reaches the page")
    rp = (REPO / "monthly_macro" / "run.py").read_text(encoding="utf-8")
    check("scans.ingest()" in rp and "if not args.skip_fetch:" in rp.split(
              "scans.ingest()")[0][-900:],
          "the Monthly run ingests the scans before it builds (skipped with "
          "--skip-fetch, which renders from the store as it stands)")
    del out


def ytd_group(cfg: dict, ed: dict, out: dict) -> None:
    """I: GTM-14, the cross-asset year to date (T3 second half, step 2)."""
    print(f"\n{LINE}\nI. GTM-14: THE CROSS-ASSET YEAR TO DATE, FROM THE STORE'S "
          f"PROXIES\n{LINE}")
    tape = next(s for s in ed["sections"] if s["id"] == "tape")
    sub = next((ss for ss in tape["subsections"]
                if ss["title"] == "Across assets, year to date"), None)
    rows = (sub or {}).get("table", {}).get("rows") or []
    got = {r[1]: (r[0], r[2], r[3]) for r in rows}

    def pct(x: str) -> float:                    # the polish prints U+2212
        return float(x.rstrip("%").replace("−", "-"))
    days = (dt.date(2026, 9, 30) - dt.date(2025, 12, 31)).days
    cash = 100.0 * ((1 + 0.04 / 360) ** days - 1)
    # SPY 90 -> 101, IWM 104 -> 102 and XLRE 88 -> 99: the month-ends the
    # sector and scorecard legs seed (100 + i % 7 - 3).
    want = {"U.S. large cap": round(100 * (101 / 90 - 1), 2),
            "Developed ex-U.S. equity": 10.0,
            "High-yield bonds": round(100 * ((82 + 1.0) / 80 - 1), 2),
            "U.S. small cap": round(100 * (102 / 104 - 1), 2),
            "U.S. aggregate bonds": -1.0, "REITs": 12.5,
            "Cash": round(cash, 2)}
    check(sub and {k: pct(v[2]) for k, v in got.items()} == want,
          f"each class's total return from the 31 Dec 2025 close to the 30 Sep "
          f"close, as hand-computed ({len(got)} classes)")
    check([r[0] for r in rows] == list(range(1, len(rows) + 1))
          and [pct(r[3]) for r in rows]
          == sorted(want.values(), reverse=True),
          "ranked, best first")
    check(got.get("High-yield bonds", (0, ""))[1] == "HYG"
          and want["High-yield bonds"] == 3.75,
          "a dividend inside the year is added on its ex-date and not reinvested; "
          "one before the start is not (HYG +3.75%)")
    check(got.get("Cash", (0, ""))[1] == "3-month T-bill"
          and abs(want["Cash"] - 3.08) < 0.01,
          f"cash accrues at the 3-month bill as Book Z's does, rate x days / 360 "
          f"(+{want['Cash']:.2f}% over {days} days)")
    nt = " ".join((sub or {}).get("not_tracked") or [])
    check("Emerging-market equity" in nt and "no close at both" in nt
          and "Emerging-market equity" not in got,
          "a class whose proxy has no year-start close says so and is not ranked")
    check("Commodities year to date: no broad commodity index" in nt
          and "Commodities" not in got,
          "a class with no proxy in the store says why rather than borrowing one")
    check(any("not reinvested" in x and "GTM-14" in x for x in sub.get("notes") or [])
          and "Across assets, year to date" in out["html_email"]
          and "Across assets, year to date" in out["markdown"],
          "the method prints beneath the table, in the HTML and the Markdown")
    proxies = [c.get("key") for c in cfg.get("monthly_cross_asset_ytd") or []]
    check(len(proxies) == 9 and "yfinance.mkt_agg" in proxies
          and "fred.tbill_3m" in proxies,
          "the classes and proxies are configuration (monthly_cross_asset_ytd)")
    check(tape["depth"] == "light" and tape["data"].get("cross_asset_ytd"),
          "The tape stays light: the ranking is a table and in the section's data, "
          "not prose")


def triple_group(cfg: dict, ed: dict, out: dict) -> None:
    """J: the slow layers in triple form (T3 second half, step 3)."""
    print(f"\n{LINE}\nJ. THE SLOW LAYERS' TRIPLE: LATEST, LONG-RUN AVERAGE, "
          f"PERCENTILE\n{LINE}")
    slow = next(s for s in ed["sections"] if s["id"] == "slow")
    subs = {ss["title"]: ss for ss in slow["subsections"]}
    val = subs.get("Valuation") or {}
    rows = {r[0]: r for r in (val.get("table") or {}).get("rows") or []}
    now_day = dt.date.fromisoformat(ed["window"]["now"][:10])
    cape = cape_series()
    mean = sum(v for _, v in cape) / len(cape)
    win = [v for d, v in cape if dt.date.fromisoformat(d) >= now_day - dt.timedelta(days=1825)]
    pct = 100.0 * sum(1 for v in win if v <= cape[-1][1]) / len(win)
    c = rows.get("CAPE (Shiller P/E10)") or []

    def num(x: str) -> float:
        return float(x.split(" (")[0].replace(",", "").replace("−", "-"))
    check(val.get("table", {}).get("columns") == ["Series", "Latest (data as of)",
                                                  "Long-run average (window)",
                                                  "Percentile (window)"],
          "the valuation table carries the triple, each column naming its window")
    check(c and num(c[1]) == round(cape[-1][1], 1) and "(2026-09-01)" in c[1],
          f"CAPE's latest with its data-as-of date: {c[1] if c else None}")
    check(c and abs(num(c[2]) - mean) < 0.051
          and f"full history since 1990-01-01, n={len(cape)}" in c[2],
          f"the long-run average over the store's full history, the window "
          f"printed beside it ({c[2] if c else None})")
    check(c and abs(num(c[3]) - pct) < 0.51 and f"5 years, n={len(win)}" in c[3],
          f"the percentile over five years, its window and n beside it "
          f"({c[3] if c else None}; by hand {pct:.1f})")
    f = rows.get("Forward P/E, total market (Damodaran)") or []
    check(f and "since 2026-01-05, n=1; under 5 years" in f[3]
          and "full history since 2026-01-05, n=1" in f[2],
          "a series with less than five years prints its own start and n rather "
          "than claiming the window")
    nt = " ".join(val.get("not_tracked") or [])
    check("Trailing P/E, total market (Damodaran): no observation" in nt
          and "equity risk premium" in nt,
          "a configured series the store lacks says so; the ERP waits for 6e")
    alt = subs.get("Themes: alternative assets") or {}
    arow = next((r for r in (alt.get("table") or {}).get("rows") or []
                 if r[1] == "yfinance.mkt_gld"), None)
    g = gld_series()
    gmean = sum(v for _, v in g) / len(g)
    check(arow and alt["table"]["columns"][2:] == ["Latest (data as of)",
                                                   "20-day change",
                                                   "Long-run average (window)",
                                                   "Percentile (window)"]
          and abs(num(arow[4]) - gmean) < 0.006 and num(arow[5]) == 100
          and "5 years" in arow[5],
          "the alternative assets carry the same triple (GLD: full-history "
          "average, the latest at the top of five years)")
    check(any("until the metric lenses (6e)" in x for x in val.get("notes") or [])
          and "Long-run average (window)" in out["markdown"],
          "the interim windows are stated beneath the table and print in the "
          "edition")
    tc = cfg.get("monthly_slow_triple") or {}
    check(tc.get("percentile_window_days") == 1825
          and [v["key"] for v in tc.get("valuation") or []][:1] == ["shiller.cape"],
          "the window and the series are configuration (monthly_slow_triple)")
    from altdata import derived
    check(callable(getattr(derived, "long_run_average", None)),
          "the average is computed in altdata/derived.py, where every derived form "
          "is")


def seed_chart_history(db: str) -> None:
    """Enough history for M1-M9 to render: SPY daily for ten years (close only,
    the fixture's own month-end closes kept), weekly yields and the ACM term
    premium for five years, HY OAS monthly for twenty, two CFTC contracts weekly
    for five, Book Z's ledgers and the account NAV since 1 Sep."""
    from altdata import observations
    obs = []

    def put(key, inst, day, v):
        obs.append({"registry_key": key, "instrument": inst, "observed_at": day,
                    "available_at": f"{day}T21:00:00+00:00", "value": v,
                    "source": "synthetic"})
    keep = {"2025-12-31", M_START, M_END}
    for i, d in enumerate(weekdays("2016-10-03", M_END)):
        if d not in keep:
            put("yfinance.mkt_spy", None, d, round(40.0 + i * 0.022
                                                   + 3.0 * math.sin(i / 40.0), 3))
    for i, d in enumerate(weekdays("2021-10-01", M_END)[::5]):
        put("fred.yield_10y", None, d, round(2.0 + i / 120.0, 3))
        put("acm.term_premium_10y", None, d, round(-0.5 + i / 260.0, 3))
        for inst, base in (("SP500", 50_000.0), ("UST10Y", -200_000.0)):
            put("cftc.noncomm_net", inst, d, base + 3_000.0 * math.sin(i / 9.0))
    for i, d in enumerate(months("2006-10-01", "2026-09-01")):
        put("fred.hy_oas", None, d, round(4.5 + 2.0 * math.sin(i / 14.0), 3))
    for i, d in enumerate(weekdays("2026-09-01", M_END)):
        for lg, step in (("cash", 0.011), ("spy", 0.05), ("sixty_forty", 0.03)):
            put("paper.benchmark", lg, d, round(100.0 + i * step, 4))
        put("portfolio.nav", None, d, 1_000_000.0 + 900.0 * i)
    with observations.ObservationStore(db) as st:
        st.write_many(obs)


def charts_group(cfg: dict) -> None:
    """K: the Monthly's charts, M1-M9 (T3 second half, step 4)."""
    from daily_cascade import charts as dch, readability as rd
    from monthly_macro import charts as mch, run as run_mod, stack as ms
    print(f"\n{LINE}\nK. THE CHARTS, M1-M9: THE WEEKLY'S MECHANICS AT THE MONTHLY'S "
          f"SPANS\n{LINE}")
    db3 = str(Path(TD) / "charts.db")
    seed(db3, dealer_sessions=21)
    seed_chart_history(db3)
    point(db3)
    p3 = build_payload()
    arch = str(Path(TD) / "chart_reports")
    out = ms.produce(p3, archive_dir=arch, client=client([], {}), db_path=db3)
    point(DB)
    ed = out["edition"]
    charts = out["charts"]
    check(ed.get("chart_plan") == list(mch.ORDER) and cfg["budget"]["monthly"]["charts"]
          == 10, "the plan is M1-M9, inside the Monthly's cap of 10")
    tiny = mch.plan({"budget": {"charts": 3}, "sections": [{"depth_reason": None}]})
    lifted = mch.plan({"budget": {"charts": 3},
                       "sections": [{"depth_reason": "CPI released"}]})
    check(tiny == ["M1", "M2", "M3"] and len(lifted) == 4,
          "the cap is the budget's, and a fired trigger lifts it by one")
    bad = {k: c.get("unavailable") for k, c in charts.items() if c.get("unavailable")}
    check(not bad and ed["chart_count"] == 9,
          f"with history stored, all nine render ({ed['chart_count']})"
          + (f" -- unavailable: {bad}" if bad else ""))
    ok = [c for c in charts.values() if not c.get("unavailable")]
    check(ok and all(c["png_bytes"] <= dch.MAX_PNG_BYTES and c["png"][:4] == b"\x89PNG"
                     for c in ok),
          f"each a PNG of at most 150 KB for the email (largest "
          f"{max((c['png_bytes'] for c in ok), default=0):,} bytes)")
    check(ok and all(c.get("svg_path") and Path(c["svg_path"]).exists()
                     and Path(c["svg_path"]).parent == Path(arch) for c in ok),
          "and an SVG on disk beside the archived edition")
    check(ok and all(c["min_px_at_400"] >= dch.MIN_PX_AT_400 for c in ok),
          "the mobile rule: no text below 8 px at 400 px wide")
    span = re.compile(r"\d{4}-\d{2}(-\d{2})? to \d{4}-\d{2}(-\d{2})?")
    check(all(span.search(str(c.get("title") or "")) for c in ok)
          and all(re.search(r"\(.+\)", str(c.get("title") or "")) for c in ok),
          "every title names its count, its plain span and its dates")
    check("M2" in charts and "ten years" in charts["M2"]["title"]
          and "M1" in charts and "three years" in charts["M1"]["title"]
          and "twenty years" in charts["M5"]["title"],
          "the spans are the brief's: three years weekly, ten years monthly, "
          "twenty years of the spread")
    book = ed.get("levels") or {}
    check(all(mch.drawn_levels_ok(c, book) for c in ok)
          and {d["type"] for d in charts["M1"]["drawn"]} == {"ma_40w"}
          and {d["type"] for d in charts["M2"]["drawn"]} <= {"ma_10m", "ma_20m"}
          and charts["M2"]["drawn"],
          "M1 and M2 draw only levels from the level list: the 40-week; the 10- and "
          "20-month")
    tape = next(s for s in ed["sections"] if s["id"] == "tape")
    prose_levels = {(k, v) for lv in tape["data"]["levels"] for k, v in lv.items()
                    if k not in ("symbol", "name")}
    check(all((d["label"], d["value"]) in prose_levels
              for c in (charts["M1"], charts["M2"]) for d in c["drawn"]),
          "and the same list is the one the tape's prose is given: one level list")
    dd = mch.drawdowns([{"close": x} for x in (100.0, 110.0, 99.0, 121.0, 108.9)])
    check([round(x, 2) for x in dd] == [0.0, 0.0, -10.0, 0.0, -10.0]
          and "drawdown from the high" in charts["M2"]["caption"],
          "M2's drawdown is each month's close against the highest close before it")
    where = {}
    for s in ed["sections"]:
        for c in s.get("charts_rendered") or []:
            where[c] = s["id"]
        for ss in s.get("subsections") or []:
            for c in ss.get("charts_rendered") or []:
                where[c] = f"{s['id']}/{ss['title']}"
    check(where == {"M1": "tape", "M2": "tape", "M3": "mechanics", "M4": "plumbing",
                    "M5": "plumbing", "M6": "positioning", "M7": "priced",
                    "M8": "ahead/Scenarios, and what would change our mind",
                    "M9": "book"},
          "each prints in its section: the long frame in the tape, the "
          "retrospective in Mechanics, the weights beside Ahead's scenarios")
    em, ar = out["html_email"], out["html_archive"]
    check(all(f"cid:{k.lower()}@chester" in em for k in charts)
          and {c for c, _ in out["inline_images"]} == {f"{k.lower()}@chester"
                                                      for k in charts},
          "the email references each PNG by Content-ID, and carries exactly those "
          "images")
    check(all(Path(c["svg_path"]).name in ar for c in ok) and "cid:" not in ar,
          "the archived HTML references the SVGs on disk")
    check(all(f"]({Path(c['svg_path']).name})" in out["markdown"] for c in ok),
          "the Markdown carries each chart with its caption as the alt text")
    check(ed["reading_minutes"] == max(1, math.ceil(
              (ed["words"] + rd.stored_words(ed)) / rd.WORDS_PER_MINUTE
              + 9 * rd.SECONDS_PER_CHART / 60.0)),
          "the reading time counts the nine charts at 20 seconds each")
    hist = mch.scenario_history([
        {"source": "monthly_macro", "scenario_set": "monthly_macro:2026-09",
         "claim": "a", "probability": 0.7, "emitted_at": "2026-09-02",
         "brier": 0.09, "resolved_at": "2026-09-25"},
        {"source": "monthly_macro", "scenario_set": "monthly_macro:2026-09",
         "claim": "b", "probability": 0.3, "emitted_at": "2026-09-02",
         "brier": 0.09, "resolved_at": "2026-10-05"},
        {"source": "other", "scenario_set": "x", "claim": "c", "probability": 0.5,
         "emitted_at": "2026-09-02"}], "2026-10-01")
    check(hist == [{"edition": "2026-09", "weights": [("a", 0.7), ("b", 0.3)],
                    "n_resolved": 1, "brier": 0.09}],
          "M8 reads the Monthly's own scenario sets, and a Brier only once resolved "
          "by the cutoff")
    check("Book Z: cash" in json.dumps(charts["M9"].get("series"))
          and "Paper account NAV" in json.dumps(charts["M9"].get("series"))
          and "not marked separately" in charts["M9"]["caption"],
          "M9: Book Z's three ledgers against the account's NAV, and it says the "
          "books are not yet marked one by one")
    pthin = ms.produce(build_payload(), archive_dir=None, client=client([], {}),
                       db_path=DB)
    check("Chart unavailable: " in pthin["html_email"]
          and "weekly bars stored, 20 needed" in pthin["html_email"],
          "a chart the store cannot support prints \"Chart unavailable: <reason>\" "
          "in its place")
    stamp = REPORT_DATE
    mch.archive_pngs(charts, stamp, arch)
    (Path(arch) / f"monthly_macro_{stamp}.html").write_text(em, encoding="utf-8")
    (Path(arch) / f"monthly_macro_{stamp}.md").write_text(out["markdown"],
                                                          encoding="utf-8")
    sent = {}
    saved = run_mod.delivery.send_html
    run_mod.delivery.send_html = lambda *a, **k: (sent.update(k) or ("sent", "ok"))
    try:
        run_mod.deliver_edition(stamp, arch)
    finally:
        run_mod.delivery.send_html = saved
    check(sorted(c for c, _ in sent.get("inline_images") or [])
          == sorted(f"{k.lower()}@chester" for k in charts)
          and all(b[:4] == b"\x89PNG" for _, b in sent["inline_images"]),
          "delivery reads the archived PNGs back and sends them by Content-ID with "
          "the archived HTML")


SUMMARY_DEEP = ("The fixture chartbook, data as of 31 August 2026, argues earnings "
                "did the work: EPS +31.6% with margins at 15.9%, the forward yield "
                "minus Baa at -1.0%, and 2s10s - 5 bp because the long end sold "
                "off. Exhibits 4 and 11 are worth the time.")
SUMMARY_SKIM = ("The fixture stability report, published 12 September 2026, finds "
                "leverage in non-banks at a record 41% of credit and says so twice.")


def reading_fixture(d: Path) -> tuple[Path, Path]:
    reg = {"entries": [
        {"id": "fx-deep-2026-09", "watch_id": "fx-deep", "group": "chartbook",
         "publication": "Fixture Chartbook — September 2026", "publisher": "Fixture AM",
         "published": "2026-09-10", "as_of": "2026-08-31",
         "url": "https://example.org/deep.pdf", "scan": "docs/scans/fx-deep.md",
         "status": "read", "line": "Lead line.", "summary": SUMMARY_DEEP,
         "themes": ["a theme tag"], "candidates": ["FX-CAND-1"]},
        {"id": "fx-skim-2026-09", "watch_id": "fx-skim", "group": "plumbing",
         "publication": "Fixture Stability Report", "publisher": "Fixture Bank",
         "published": "2026-09-12", "as_of": "2026-09-12",
         "url": "https://example.org/skim.pdf", "scan": None, "status": "read",
         "line": "Skim lead.", "summary": SUMMARY_SKIM, "themes": [], "candidates": []},
        {"id": "fx-list-2026-09", "watch_id": "fx-list", "group": "history",
         "publication": "Fixture Yearbook", "publisher": "Fixture Uni",
         "published": "2026-09-30", "as_of": None, "url": "https://example.org/list",
         "scan": None, "status": "listed", "line": "Equities beat bills in 7 of 10 "
         "decades.", "summary": None, "themes": [], "candidates": []},
        {"id": "fx-nourl", "watch_id": "fx-v", "group": "voices", "publication":
         "Unsourced Letter", "publisher": "Nobody", "published": "2026-09-16",
         "url": None, "status": "listed", "line": "x", "summary": None},
        {"id": "fx-pending", "watch_id": "fx-v", "group": "voices", "publication":
         "Pending Letter", "publisher": "Nobody", "published": "2026-09-17",
         "url": "https://example.org/pending", "status": "pending", "line": "x",
         "summary": None},
        {"id": "fx-old", "watch_id": "fx-v", "group": "voices", "publication":
         "August Letter", "publisher": "Nobody", "published": "2026-08-31",
         "url": "https://example.org/old", "status": "listed", "line": "x",
         "summary": None},
        {"id": "fx-dup", "watch_id": "fx-v", "group": "voices", "publication":
         "Scanned Letter", "publisher": "Desk", "published": "2026-09-20",
         "url": "https://example.org/dup", "status": "read", "line": None,
         "summary": "The scanned letter's stored summary."},
        {"id": "fx-voice", "watch_id": "fx-v", "group": "voices", "publication":
         "Shelf Letter", "publisher": "Desk", "published": "2026-09-21",
         "url": "https://example.org/voice", "status": "listed", "line": "A letter.",
         "summary": None}]}
    wl = {"groups": {"chartbook": "Chartbooks", "plumbing": "Plumbing",
                     "history": "History", "voices": "Letters"},
          "items": [
              {"id": "due-oct", "publication": "October Outlook", "publisher": "P1",
               "expected": {"months": [10], "window": "mid-October"},
               "index_url": "https://example.org/oct"},
              {"id": "due-nov", "publication": "November Outlook", "publisher": "P2",
               "expected": {"months": [11], "window": "November"},
               "index_url": "https://example.org/nov"},
              {"id": "irr", "publication": "Irregular Notes", "publisher": "P3",
               "expected": "irregular", "index_url": "https://example.org/irr"}]}
    r, w = d / "register.json", d / "watchlist.json"
    r.write_text(json.dumps(reg), encoding="utf-8")
    w.write_text(json.dumps(wl), encoding="utf-8")
    return r, w


def reading_group(cfg: dict) -> None:
    """L: the Reading chapter (T3 second half, step 5)."""
    import html as htmlmod
    from monthly_macro import reading, stack as ms
    from daily_cascade import cadence as cadence_mod, readability as rd
    from daily_cascade import stack as sm, stack_render as sr
    print(f"\n{LINE}\nL. THE READING CHAPTER: AFTER NARRATIVES, STORED TEXT VERBATIM\n"
          f"{LINE}")
    reg, wl = reading_fixture(Path(TD))
    saved = (reading.REGISTER, reading.WATCHLIST)
    reading.REGISTER, reading.WATCHLIST = reg, wl
    calls: list = []
    try:
        out = ms.produce(build_payload(), archive_dir=None, client=client(calls, {}),
                         db_path=DB)
    finally:
        reading.REGISTER, reading.WATCHLIST = saved
    ed, page, md = out["edition"], out["html_email"], out["markdown"]
    ids = [s["id"] for s in ed["sections"]]
    sec = next(s for s in ed["sections"] if s["id"] == "reading")
    spec = next(s for s in cfg["sections"] if s["id"] == "reading")
    check(ids.index("reading") == ids.index("narratives") + 1
          and ids.index("ahead") == ids.index("reading") + 1,
          "Reading sits immediately after Narratives and before Ahead (D1)")
    check(spec.get("monthly") == "deep" and "daily" not in spec and "weekly" not in spec
          and sec["depth"] == "deep",
          "config/reporting_stack.yaml carries a reading row in the Monthly's "
          "column only")
    check(not any("THE SECTION: Reading" in c for c in calls)
          and not sec["paragraphs"] and sec["prose_wanted"] is False,
          "no model call: the chapter is the register's text and code-written "
          "lines")
    groups = [ss["title"] for ss in sec["subsections"]]
    check(groups == ["Chartbooks", "Plumbing", "History", "Letters",
                     "Due before the next Monthly"],
          f"published this month, in the watchlist's group order ({groups})")
    shown = [e["id"] for ss in sec["subsections"] for e in ss.get("entries") or []
             if e.get("id")]
    check(shown == ["fx-deep-2026-09", "fx-skim-2026-09", "fx-list-2026-09",
                    "fx-dup", "fx-voice"],
          "the month is (31 Aug, 30 Sep]: the 31 Aug edition is last month's, the "
          "30 Sep one is this month's; pending never prints")
    check(htmlmod.escape(SUMMARY_DEEP) in page and SUMMARY_DEEP in md
          and htmlmod.escape(SUMMARY_SKIM) in page and SUMMARY_SKIM in md,
          "each stored summary prints verbatim in the HTML (escaped) and the "
          "Markdown: no polish, no minus-sign rewrite, no trim")
    check("because the long end" in page and not sec.get("withheld")
          and "Commentary withheld" not in page.split(">Reading<")[-1].split(
              ">Ahead<")[0],
          "the audits do not apply: a motive word in a stored summary is not "
          "withheld")
    check('<a href="https://example.org/deep.pdf"' in page
          and "**[Fixture Chartbook — September 2026](https://example.org/deep.pdf)**"
          in md,
          "the title line is hyperlinked to the stored URL")
    check("published 10 Sep 2026 (data as of 31 Aug 2026)" in page
          and "published 12 Sep 2026 (data as of" not in page,
          "the data-as-of date prints where it differs from the published date")
    check(f'{cfg["monthly_reading"]["repo_blob_url"]}/docs/scans/fx-deep.md' in page,
          "the scan line links the scan at an absolute address an email can follow")
    check("Fixture Yearbook</a></strong>" in page and "Equities beat bills" in page
          and "Lead line." not in page,
          "a list item prints its one-liner on the title line; a summarised item "
          "prints its summary, not its line")
    check("1 entry withheld: no stored source." in page
          and "Unsourced Letter" not in page and "Pending Letter" not in page,
          "an entry without a URL is withheld and counted in the footnote")
    check("FX-CAND-1" not in page and "a theme tag" not in page,
          "no candidate or theme prints")
    due = next(ss for ss in sec["subsections"]
               if ss["title"] == "Due before the next Monthly")
    check([e["publication"] for e in due["entries"]] == ["October Outlook"]
          and 'href="https://example.org/oct"' in page and "Irregular Notes" not in page,
          "due before the next Monthly: the coming month's expected items, linked "
          "to their index pages; irregular items left out")
    data = reading.section("2026-08-31T23:59:59+00:00", "2026-09-30",
                           "2026-10-01T10:00:00+00:00",
                           reading.voices_urls({"table": {"rows": [
                               ["Desk", "Outlet, 20 Sep 2026, https://example.org/dup"]]}}),
                           cfg, reg, wl)
    rs = reading.stack_section(data, spec, None)
    dup = [e for g in data["entries_by_group"] for e in g["entries"]
           if e["id"] == "fx-dup"]
    check(len(dup) == 1 and dup[0]["summary"] == "The scanned letter's stored summary."
          and "Also in Narratives' voices" in " ".join(rs["notes"])
          and "Scanned Letter" in " ".join(rs["notes"])
          and "Also in Narratives' voices" not in " ".join(
              reading.stack_section(reading.section(
                  "2026-08-31T23:59:59+00:00", "2026-09-30",
                  "2026-10-01T10:00:00+00:00", set(), cfg, reg, wl),
                  spec, None)["notes"]),
          "a shelf voices entry sharing a URL with a scan voice: the scan row stands, "
          "the shelf summary still prints, and the footnote names the match")
    e2 = json.loads(json.dumps(ed))
    before = sm.edition_words(e2)
    rs_only = {"sections": [s for s in e2["sections"] if s["id"] == "reading"]}
    check(before == sm.edition_words({"sections": [dict(s, subsections=[])
                                                   if s["id"] == "reading" else s
                                                   for s in e2["sections"]],
                                      "detail": e2["detail"]})
          and rd.stored_words(e2) == rd.stored_words(rs_only)
          and rd.stored_words(e2) > 50,
          f"the summaries are not this edition's prose: no budget word "
          f"({rd.stored_words(e2)} stored words counted in the reading time instead)")
    ms.enforce_budget(e2)
    sm.trim_to_budget(e2, 10)
    rs2 = next(s for s in e2["sections"] if s["id"] == "reading")
    check([ss.get("entries") for ss in rs2["subsections"]]
          == [ss.get("entries") for ss in sec["subsections"]],
          "over budget, the budget never cuts or trims a stored summary")
    check(ed["reading_minutes"] == max(1, math.ceil(
              (ed["words"] + rd.stored_words(ed)) / 250.0 + ed["chart_count"] / 3.0)),
          "and the reading time counts them")
    empty = reading.stack_section(reading.section(
        "2026-05-31T23:59:59+00:00", "2026-06-30", "2026-07-01T10:00:00+00:00", set(),
        cfg, reg, wl), spec, None)
    sub_html = "".join(sr.subsection_html(ss, "month", cadence_mod.get("monthly"))
                       for ss in empty["subsections"])
    check(empty["claim"] == reading.EMPTY_LINE and not empty.get("empty")
          and "Nothing on the shelf is due" in sub_html,
          "an empty month prints \"Nothing on the shelf was published this month.\" "
          "and the due list")
    live = reading.section("2026-09-30T23:59:59+00:00", "2026-10-31",
                           "2026-11-01T10:00:00+00:00", set(), cfg)
    check([e["id"] for g in live["entries_by_group"] for e in g["entries"]][:1]
          == ["jpm-gtm-2026q4"] and any(
              e.get("summary", "").startswith("JPM's 71-slide quarterly chartbook")
              for g in live["entries_by_group"] for e in g["entries"]),
          "against the committed register, the 1 Nov Monthly opens the chapter with "
          "the JPM Guide and its stored summary")


def main() -> int:
    seed(DB, dealer_sessions=21)
    import yaml
    from daily_cascade import readability as rd
    from daily_cascade import stack as stack_mod
    from monthly_macro import dealer, prose as prose_mod, stack as ms
    print(f"{LINE}\nThe stacked Monthly, first half (T3) -- synthetic September 2026\n"
          f"{LINE}")
    p = build_payload()
    calls: list = []
    script = {
        # F: withheld once by the tape rules, clean on the retry.
        "THE SECTION: Plumbing & rates": [
            "Yields rose because of the month's supply.\n\nThe curve steepened.",
            "Plumbing moved with the curve this month.\n\nThe long end led."],
        # F: a figure the slice lacks, twice -- withheld after the retry.
        "THE SECTION: Credit Cycle": [
            "Credit widened by 999 basis points.\n\nThat is not in the data.",
            "Credit widened by 998 basis points.\n\nStill not in the data."],
        # F: a fault is not retried.
        "THE SECTION: Positioning & flows": [RuntimeError("fixture API outage")],
    }
    arch = str(Path(TD) / "reports")
    out = ms.produce(p, archive_dir=arch, client=client(calls, script), db_path=DB)
    ed = out["edition"]
    written = out["written"]
    sec = {s["id"]: s for s in ed["sections"]}
    cfg = stack_mod.config()

    # --- A. STACK --------------------------------------------------------------
    print(f"\n{LINE}\nA. TEN SECTIONS AT MONTHLY DEPTH, THEN SLOW LAYERS AND THE "
          f"DETAIL TABLES\n{LINE}")
    ten = list(stack_mod.SECTION_ORDER)
    order = ten[:ten.index("narratives") + 1] + ["reading"] \
        + ten[ten.index("narratives") + 1:] + ["slow"]
    check([s["id"] for s in ed["sections"]] == order,
          "the ten sections in the brief's order, Reading between Narratives and "
          "Ahead (D1), Slow layers last")
    want = {"read": "deep", "tape": "light", "mechanics": "deep", "misfit": "deep",
            "plumbing": "deep", "positioning": "medium", "priced": "deep",
            "narratives": "deep", "reading": "deep", "ahead": "deep",
            "book": "medium", "slow": "deep"}
    got = {k: sec[k]["depth"] for k in want}
    check(got == want, f"each at the matrix's Monthly depth ({got})")
    declared = {s["id"]: s.get("monthly") for s in cfg["sections"]}
    check(all(declared[k] == v for k, v in want.items() if k != "slow")
          and (cfg.get("monthly_slow_layers") or {}).get("monthly") == "deep",
          "and the depths are read from config/reporting_stack.yaml's Monthly column")
    check([d["id"] for d in ed["detail"]] == ["regime", "scenarios", "register",
                                              "appendix"],
          "the old record follows as the detail tables, in order: regime, scenario "
          "record, the register's month, the appendix")
    check(cfg["budget"]["monthly"] == {"words": 7000, "charts": 10}
          and cfg.get("reading_targets_minutes") == {"daily": 5, "weekly": 20,
                                                     "monthly": 40},
          "the Monthly budget (7,000 words, 10 charts) and the three reading "
          "targets (5, 20, 40 minutes) are configuration")
    check(all(s.get("claim") for s in ed["sections"] if not s.get("empty")
              and s["id"] not in ("positioning",)),
          "every non-empty section opens with a claim line (Positioning's call "
          "faulted, F)")
    ms.save_edition(ed, arch)
    p2 = dict(p, report_date="2026-11-01")
    prior = ms.load_prior("2026-11-01", arch)
    ed2 = ms.build(p2, prior, DB)
    check(prior and prior.get("report_date") == REPORT_DATE
          and ms.load_prior(REPORT_DATE, arch) is None,
          "the prior edition is the previous Monthly's, never this one")
    check(any(s.get("collapsed") for s in ed2["sections"])
          and not next(s for s in ed2["sections"] if s["id"] == "read")["collapsed"],
          "an unchanged section collapses against the prior Monthly; The read never "
          "does")

    # --- B. READING TIME ---------------------------------------------------------
    print(f"\n{LINE}\nB. THE READING TIME, COMPUTED AND PRINTED\n{LINE}")
    words = stack_mod.edition_words(ed)
    mins = max(1, math.ceil((words + rd.stored_words(ed)) / rd.WORDS_PER_MINUTE
                            + int(ed["chart_count"]) * rd.SECONDS_PER_CHART / 60.0))
    check(ed["words"] == words and ed["reading_minutes"] == mins,
          f"{words} prose words and {ed['chart_count']} charts read in "
          f"{ed['reading_minutes']} minute(s), by the Weekly's formula")
    check(f"about {rd.plural(mins, 'minute')} to read" in out["html_email"]
          and "target 40 minutes" in out["html_email"]
          and f"about {rd.plural(mins, 'minute')} to read" in out["markdown"],
          "the header prints it the way the Weekly's does, beside its 40-minute "
          "target, in the HTML and the Markdown")
    check("Changed since last Monthly" in out["html_email"],
          "and the header carries what changed since the last Monthly")

    # --- C. DEALER ---------------------------------------------------------------
    print(f"\n{LINE}\nC. THE DEALER RETROSPECTIVE\n{LINE}")
    retro = ms.build(p, None, DB)["_retro"]
    c = retro["counts"]
    check(c["sessions"] == 21 and not retro["insufficient"]
          and c["pinned"] == 7 and c["pinned_scored"] == 21
          and retro["rates"]["pinned"] == round(100 * 7 / 21, 1),
          f"21 stored sessions: pinned {c['pinned']} of {c['pinned_scored']} "
          f"({retro['rates']['pinned']}%), from the stored rows by the Weekly's rule")
    check(c["amplified"] == 6 and c["flip_crossed"] == 6
          and c["largest_move"]["return_pct"] == 1.8,
          f"amplified {c['amplified']}, flip crossed {c['flip_crossed']}, the "
          f"largest move with its regime and morning net GEX")
    mech = sec["mechanics"]
    titles = [ss["title"] for ss in mech["subsections"]]
    check("The month's counts and hit rates" in titles
          and any("Hit rate" in (ss.get("table") or {}).get("columns", [])
                  for ss in mech["subsections"])
          and len((mech.get("table") or {}).get("rows") or []) == 21,
          "Mechanics prints the per-session table and the month's counts and hit "
          "rates")
    check(any(k == "stack:mechanics" for k in written),
          "and its prose is asked for at 20+ sessions")
    db2 = str(Path(TD) / "thin.db")
    seed(db2, dealer_sessions=12)
    point(db2)
    p_thin = build_payload()
    calls2: list = []
    out2 = ms.produce(p_thin, archive_dir=None, client=client(calls2, {}), db_path=db2)
    m2 = next(s for s in out2["edition"]["sections"] if s["id"] == "mechanics")
    check("insufficient sessions (n=12)" in json.dumps(m2)
          and "insufficient sessions (n=12)" in out2["html_email"],
          "12 stored sessions print \"insufficient sessions (n=12)\"")
    check("stack:mechanics" not in out2["written"]
          and not any("THE SECTION: Mechanics" in x for x in calls2)
          and (m2.get("claim") or "").startswith("Insufficient sessions (n=12)")
          and not m2.get("paragraphs"),
          "no prose is asked for: the claim is the count, written by code")
    check(not any(ss.get("table") and "Hit rate" in ss["table"]["columns"]
                  for ss in m2["subsections"]),
          "and no hit rate prints below the threshold")
    check(cfg.get("dealer_retrospective_min_sessions") == 20
          and dealer.min_sessions(cfg) == 20
          and dealer.min_sessions({"dealer_retrospective_min_sessions": 25}) == 25
          and retro["min_sessions"] == 20,
          "the threshold is configuration (dealer_retrospective_min_sessions: 20, "
          "ruled 8 Oct), read by the code rather than written into it")
    point(DB)
    pinned_day = next(r for r in retro["sessions"] if r["flags"]["pinned"])
    free_day = next(r for r in retro["sessions"] if r["flags"]["pinned"] is False)
    fmt = lambda d: f"{int(d[8:10])} Sep"                      # noqa: E731
    check(not dealer.flag_word_faults(f"SPY pinned on {fmt(pinned_day['session'])}.",
                                      retro),
          "a session whose flag is set may be called pinned")
    check(dealer.flag_word_faults(f"SPY pinned on {fmt(free_day['session'])}.", retro),
          "a session whose flag is not set may not")
    check(not dealer.flag_word_faults("The close pinned to max pain on 7 sessions.",
                                      retro)
          and dealer.flag_word_faults("Dealers amplified the month's moves.", retro),
          "the month's own count may be stated; a bare flag word is refused")
    calls3: list = []
    bad = f"SPY pinned on {fmt(free_day['session'])}.\n\nThe flip held."
    out3 = ms.produce(p, archive_dir=None, db_path=DB,
                      client=client(calls3, {"THE SECTION: Mechanics": [bad]}))
    w3 = out3["written"]["stack:mechanics"]
    check(not w3["published"] and w3["attempts"] == 2
          and "flag is not set" in str(w3["reason"]),
          "in the pipeline, Mechanics prose that calls an unflagged session "
          "pinned is withheld, after its one retry")

    # --- D. PHASE A, ONCE ----------------------------------------------------------
    print(f"\n{LINE}\nD. MONTHLY v2 PHASE A: NOTHING LOST, NOTHING TWICE\n{LINE}")
    ids = [i for s in ed["sections"] for i in s.get("phase_a") or []] \
        + [i for d in ed["detail"] for i in d.get("phase_a") or []] \
        + list(ed.get("changed_since_phase_a") or [])
    dup = sorted({i for i in ids if ids.count(i) > 1})
    check(ids and not dup, f"{len(ids)} Phase A facts placed, none twice"
                           + (f" (twice: {dup[:4]})" if dup else ""))
    expect = {"month_in_markets:prose", "month_in_one_page:takeaways",
              "looking_ahead:prose", "our_read:prose", "our_read:bound",
              "regime:dials", "regime:dimensions", "register_month"}
    expect |= {f"month_in_markets:row:{r['id']}"
               for r in p["month_in_markets"]["rows"]}
    expect |= {f"theme:{t['theme']}:prose" for t in p["looking_back"]["themes"]}
    expect |= {f"looking_back:{t['theme']}:item:{n}"
               for t in p["looking_back"]["themes"]
               for n, _ in enumerate(t.get("items") or [])}
    expect |= {f"looking_ahead:scenario:{n}"
               for n, _ in enumerate(p["looking_ahead"]["scenarios"])}
    expect |= {f"looking_back:what_changed:{n}" for n, _ in enumerate(
        p["looking_back"]["what_changed"]["rows"])}
    lost = sorted(expect - set(ids))
    check(not lost and p["month_in_markets"]["rows"]
          and p["looking_back"]["what_changed"]["rows"]
          and p["looking_ahead"]["scenarios"],
          f"every Phase A part is placed: the scorecard ({len(p['month_in_markets']['rows'])} "
          f"rows), the takeaways, the themes, what changed, the look-ahead and its "
          f"weights, our read" + (f" (lost: {lost[:4]})" if lost else ""))
    rows = printed_rows(ed)
    seen: dict = {}
    twice = []
    for r, where in rows:
        if r in seen and seen[r] != where:
            twice.append((r[:2], seen[r], where))
        seen.setdefault(r, where)
    check(not twice, f"{len(rows)} table rows printed, none in two places"
                     + (f" ({twice[:2]})" if twice else ""))
    pm = [k for k, _ in ed.get("printed_metrics") or []]
    again = sorted({k for k in pm if pm.count(k) > 1})
    pl_rows = [r[0] for r in (sec["plumbing"].get("table") or {}).get("rows") or []]
    check(pm and not again and "10-year" not in pl_rows
          and "fred.yield_10y" in dict(ed["printed_metrics"])
          and dict(ed["printed_metrics"])["fred.yield_10y"] == "tape",
          f"each series' month prints in one table: the 10-year's in The tape, not "
          f"again in Plumbing or under a theme ({len(pm)} series)"
          + (f" (twice: {again})" if again else ""))
    html = out["html_email"]
    for t in p["month_in_one_page"]["takeaways"]:
        n = html.count(rd.polish(t["text"]) or "") + html.count(t["text"])
        check(n <= 2 and json.dumps(ed).count(t["text"]) <= 2,
              f"takeaway {t['n']} prints once: {t['text'][:50]}")
    check("In one line each" not in out["markdown"]
          and "In one line each" not in html,
          "the themes' first sentences are not printed a second time as a summary")
    nk = [k for k in written if k.startswith("theme:")]
    check(nk and all(next(ss for s in ed["sections"] for ss in s["subsections"]
                          if ss.get("phase") == k).get("paragraphs")
                     or not written[k]["published"] for k in nk),
          f"each theme's prose sits in its Narratives sub-section ({len(nk)})")
    rp = sec["read"]
    check(rp.get("claim") and not any(rp["claim"] in x for x in rp["paragraphs"]),
          "The read's claim is the month-in-markets prose's first sentence, and "
          "is not printed again in its paragraphs")
    check("## 1. The month in markets" not in out["markdown"]
          and "Where our read lands" in out["markdown"]
          and "The month in one page" in out["markdown"],
          "the six-part storyline prints inside the stack, not beside it")

    # --- E. BUDGET -------------------------------------------------------------------
    print(f"\n{LINE}\nE. THE BUDGET, PROSE ONLY\n{LINE}")
    check(ed["words"] <= 7000 and ed["chart_count"] <= 10,
          f"{ed['words']} prose words of 7,000 and {ed['chart_count']} charts of 10")
    e = json.loads(json.dumps(ed))
    before = stack_mod.edition_words(e)
    e["sections"][1]["table"]["rows"] += [["filler"] * 5] * 200
    check(stack_mod.edition_words(e) == before, "a 200-row table adds no words: tables "
                                         "are data")
    deep = next(s for s in e["sections"] if s["id"] == "narratives")
    deep["subsections"][0]["paragraphs"] = ["Prose for the budget to take. " * 8] * 4
    n_items = sum(len(s["items"]) for s in e["sections"])
    n_rows = len(printed_rows(e))
    claims = [s.get("claim") for s in e["sections"]]
    e["budget"] = {"words": stack_mod.edition_words(e) - 40, "charts": 10}
    ms.enforce_budget(e)
    stack_mod.trim_to_budget(e, e["budget"]["words"])
    e["words"] = stack_mod.edition_words(e)
    check(e["words"] <= e["budget"]["words"]
          and any(s.get("trimmed") for s in e["sections"] + e["detail"]),
          f"over budget, paragraphs go until it fits ({e['words']} of "
          f"{e['budget']['words']})")
    check(sum(len(s["items"]) for s in e["sections"]) == n_items
          and len(printed_rows(e)) == n_rows
          and [s.get("claim") for s in e["sections"]] == claims,
          "and no item, table row or claim line is cut")
    check("(trimmed)" in ms.html(e), "the cut section prints \"(trimmed)\"")

    # --- F. THE ONE RETRY --------------------------------------------------------------
    print(f"\n{LINE}\nF. THE ONE RETRY, IN THE MONTHLY'S SECTION WRITER\n{LINE}")
    pl = written.get("stack:plumbing") or {}
    check(pl.get("published") and pl.get("attempts") == 2,
          "a section the audit withheld (a motive word) is retried once and "
          "publishes")
    retry_prompt = [x for x in calls if "THE SECTION: Plumbing & rates" in x]
    check(len(retry_prompt) == 2 and "WITHHELD BY THE AUDIT" in retry_prompt[1]
          and "because" in retry_prompt[1],
          "with the audit's reason fed back")
    cc = written.get("theme:credit_cycle") or {}
    check(not cc.get("published") and cc.get("attempts") == 2
          and "999" in str(cc.get("first_reason")) and "998" in str(cc.get("reason")),
          "a Phase A section that fails twice is withheld, both reasons kept")
    pos = written.get("stack:positioning") or {}
    check(pos.get("state") == "call_failed" and pos.get("attempts") == 1
          and sum(1 for x in calls if "THE SECTION: Positioning & flows" in x) == 1,
          "a fault (the API) is not retried")
    check(all(r.get("attempts") == 1 for k, r in written.items()
              if r.get("published") and k not in ("stack:plumbing",)),
          "and a section published first time is called once")

    scans_group(p, cfg, ed, out)
    ytd_group(cfg, ed, out)
    triple_group(cfg, ed, out)
    charts_group(cfg)
    reading_group(cfg)

    # --- G. REGISTRY ---------------------------------------------------------------------
    print(f"\n{LINE}\nG. THE GATE IS REGISTERED\n{LINE}")
    mk = (REPO / "Makefile").read_text(encoding="utf-8")
    check("tools/validate_monthly_stack.py" in mk, "the Makefile's list carries it")
    del yaml
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
