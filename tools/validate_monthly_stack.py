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
  E BUDGET      10,000 prose words (T3.1 item 22; 7,000 before) and 10 charts;
                words count prose only (a table
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
  M DRY RUN     --dry-run [--email] on monthly_macro.run: every write under
                reports/dryrun/ and nowhere else, the prior read from the real
                archive, no snapshot, no state record, one "[DRY RUN]" copy
                with --email, --email alone refused.

T3.1, THE OPERATOR'S NOTES ON THE FIRST DRY RUN (docs/briefs/
t3-1-monthly-notes-brief-2026-10-09.md), one group per ruling or set of them:

  N1 PHONE      text cells wrap, numbers do not, a table wider than six columns
                lays out fixed -- at the Monthly's cadence only; the email
                attaches the edition's HTML with its charts embedded.

T3.2, THE FIXES FROM THE FIRST REAL DRY RUN (box, 10 Oct 2026):

  O CAP/UNITS   the per-paragraph figure cap is the cadence's (6, 6, 8) and every
                Monthly frame states it, the summary's three; one half-up rule
                for every ordinal a table prints and its _ordinal; a cell's
                "a / b pts" pair and "percent" typed as they are; Plumbing's
                level differences carried with their signed forms.
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
    # T3.1 item 8: Plumbing's buckets -- liquidity, metals and global rates.
    for key, a, b in (("fred.sofr", 4.30, 4.33), ("fred.iorb", 4.40, 4.40),
                      ("calc.net_liquidity", 5.9e12, 5.8e12),
                      ("yfinance.mkt_copper_front", 4.50, 4.60),
                      ("yfinance.mkt_gold_front", 2600.0, 2700.0),
                      ("yfinance.mkt_usdjpy", 145.0, 148.0)):
        put(key, None, M_START, a)
        put(key, None, M_END, b)
    # T3.1 item 2: the tape's year to date -- the 10-year's 2025 year-end close,
    # and an S&P 500 close too old to be the year-end's (it must print a dash).
    put("fred.yield_10y", None, "2025-12-31", 4.40)
    put("yfinance.mkt_gspc", None, "2025-12-10", 4800.0)
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
    # T3.1 items 16-17: three voices, two on the yen carry (one each side) and
    # one on no story; the register's first row is 18 Sep, younger than the
    # three-month window.
    from altdata import voices as vmod
    with vmod.VoicesStore(db) as vs:
        for voice, url, day, side, view in (
                ("Alpha Strategist", "https://fixture.example/v1", "2026-09-18",
                 "for", "Expects the yen to keep strengthening as carry unwinds."),
                ("Bravo Economist", "https://fixture.example/v2", "2026-09-25",
                 "against", "Sees the carry trade holding while rate gaps stay wide."),
                ("Charlie Analyst", "https://fixture.example/v3", "2026-09-22",
                 None, "Expects equities to grind higher into year-end.")):
            vs.write({"voice": voice, "affiliation": "Fixture Bank",
                      "kind": "sell_side", "view": view, "outlet": "Goldman Sachs",
                      "source_url": url, "published_at": day,
                      "retrieved_at": f"{day}T11:00:00+00:00", "tier": 2,
                      "directions": [{"subject": "us_equities",
                                      "direction": "bullish"}],
                      "source_id": "fixture", "origin": "scan",
                      **({"stories": [{"story": "yen_carry", "side": side}]}
                         if side else {})}, stories={"yen_carry"})
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
    got = {r[1]: (r[0], r[2], r[4]) for r in rows}

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
          and [pct(r[4]) for r in rows]
          == sorted(want.values(), reverse=True),
          "ranked, best first")
    mo = {r[1]: (r[3], r[5]) for r in rows}
    bill_m = 100.0 * ((1 + 0.04 / 360) ** 30 - 1)
    check(sub and sub["table"]["columns"] == ["Rank", "Asset class", "Proxy",
                                              "The month", "Year to date",
                                              "Twelve months"]
          and mo.get("U.S. large cap", ("",))[0] == "+1.00%"
          and mo.get("U.S. small cap", ("",))[0] == "+2.00%",
          f"N2 (item 4): the month beside the year to date, by the same rule (SPY "
          f"100 to 101: {mo.get('U.S. large cap')})")
    check(mo.get("High-yield bonds", ("",))[0] == "—"
          and all(v[1] == "—" for v in mo.values())
          and abs(pct(mo.get("Cash", ("+0%",))[0]) - round(bill_m, 2)) < 0.006,
          "N2 (item 4): a window the store cannot span prints a dash -- HYG has no "
          "month-start close, and no class a close a year back; cash accrues the "
          "month at the bill")
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
        return float(re.sub(r"(?<=\d)(st|nd|rd|th)$", "",
                            x.split(" (")[0].replace(",", "").replace("−", "-")))
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
    alt = subs.get("Themes: metals") or {}
    arow = next((r for r in (alt.get("table") or {}).get("rows") or []
                 if r[0] == "yfinance.mkt_gld"), None)
    g = gld_series()
    gmean = sum(v for _, v in g) / len(g)
    check(arow and alt["table"]["columns"][1:] == ["Latest (data as of)",
                                                   "20-day change",
                                                   "Long-run average (window)",
                                                   "Percentile (window)"]
          and abs(num(arow[3]) - gmean) < 0.006 and num(arow[4]) == 100
          and "5 years" in arow[4],
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
    # T3.1 item 10: a positioning series whose history is too short to place.
    for i, d in enumerate(("2026-08-14", "2026-08-29", "2026-09-15")):
        put("finra.short_interest_days_to_cover", "SPY", d, 1.5 + i / 10.0)
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
          == 12, f"the plan is {', '.join(mch.ORDER)}; the cap of 12 holds on what "
                 f"prints")
    check(mch.cap_of({"budget": {"charts": 3}, "sections": [{"depth_reason": None}]})
          == 3 and mch.cap_of({"budget": {"charts": 3},
                               "sections": [{"depth_reason": "CPI released"}]}) == 4,
          "the cap is the budget's, and a fired trigger lifts it by one")
    many = {k: {"id": k, "png": b"x"} for k in mch.ORDER}
    aside = mch.hold_cap(many, 10)
    check(aside == ["M8"] and "cap of 10" in many["M8"]["unavailable"]
          and sum(1 for c in many.values() if not c.get("unavailable")) == 10,
          "the fallback: over a cap (here 10), M8 is set aside first and says why "
          "(its content arrives with scenario set #1); ten print")
    bad = {k: c.get("unavailable") for k, c in charts.items() if c.get("unavailable")}
    nch = ed["chart_count"]
    check(set(bad) == {"M10"} and "not tracked" in bad["M10"]
          and nch == len(mch.ORDER) - 1 and not ed.get("charts_over_cap"),
          f"with history stored, all but M10 render ({nch}); the fixture stores no "
          f"fed funds contracts, and M10 says so"
          + (f" -- unavailable: {bad}" if set(bad) != {"M10"} else ""))
    ok_ids = [k for k, c in charts.items() if not c.get("unavailable")]
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
          and "M0" in charts and "three months" in charts["M0"]["title"]
          and "twenty years" in charts["M5"]["title"],
          "the spans are the brief's: three months daily, three years weekly, ten "
          "years monthly, twenty years of the spread")
    book = ed.get("levels") or {}
    check(all(mch.drawn_levels_ok(c, book) for c in ok)
          and {d["type"] for d in charts["M1"]["drawn"]} == {"ma_40w"}
          and {d["type"] for d in charts["M2"]["drawn"]} <= {"ma_10m", "ma_20m"}
          and charts["M2"]["drawn"],
          "M1 and M2 draw only levels from the level list: the 40-week; the 10- and "
          "20-month")
    tape0 = next(s for s in ed["sections"] if s["id"] == "tape")
    check(tape0.get("charts_rendered", [])[:3] == ["M0", "M1", "M2"]
          and charts["M0"]["drawn"]
          and {d["type"] for d in charts["M0"]["drawn"]} <= {"ma_50d", "ma_200d"}
          and len(charts["M0"]["series"]) == 63,
          "N2 (item 6): M0, three months of daily bars with the 50- and 200-day "
          "from the level list, prints first in the tape -- daily, weekly, monthly")
    check("drawdown from the high" in charts["M1"]["caption"]
          and charts["M1"].get("drawdown_pct") is not None,
          "N2 (item 5): the 156-week chart carries the % from high underlay, M2's "
          "construction")
    pos = next(s for s in ed["sections"] if s["id"] == "positioning")
    hist = {h["series"]: h for h in pos["data"].get("history") or []}
    m6s = charts["M6"].get("series") or []
    check(len(m6s) >= 2 and [x["z"] for x in m6s] == sorted(x["z"] for x in m6s)
          and {x["series"] for x in m6s} == {k for k, h in hist.items()
                                             if h.get("z_two_years") is not None}
          and "highest" in charts["M6"]["caption"],
          f"N5 (item 11): one ranked bar chart of every positioning series' current "
          f"z replaces the ten small panels ({len(m6s)} series)")
    spy = hist.get("SPY days to cover") or {}
    check(spy.get("history") == "history too short (n=3)"
          and "SPY days to cover" in charts["M6"]["caption"]
          and "SPY days to cover" not in {x["series"] for x in m6s},
          "N5 (item 10): a series with too short a history says so, and is named "
          "in the chart's caption rather than drawn")
    cf = hist.get("CFTC S&P 500 futures") or {}
    check(cf.get("z_two_years") is not None and "over two years" in cf["history"],
          f"and a series with two years of history carries its z ({cf.get('history')})")
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
    check(where == {"M0": "tape", "M1": "tape", "M2": "tape", "M3": "mechanics",
                    "M4": "plumbing/Yields & spreads",
                    "M5": "plumbing/Yields & spreads", "M6": "positioning",
                    "M7": "priced/Breakevens",
                    "M10": "priced/FOMC pricing: the fed-funds path",
                    "M8": "ahead/Scenarios, and what would change our mind",
                    "M9": "book"},
          "each prints in its section: the long frame in the tape, the "
          "retrospective in Mechanics, the weights beside Ahead's scenarios")
    em, ar = out["html_email"], out["html_archive"]
    check(all(f"cid:{k.lower()}@chester" in em for k in ok_ids)
          and {c for c, _ in out["inline_images"]} == {f"{k.lower()}@chester"
                                                      for k in ok_ids},
          "the email references each PNG by Content-ID, and carries exactly those "
          "images")
    check(all(Path(c["svg_path"]).name in ar for c in ok) and "cid:" not in ar,
          "the archived HTML references the SVGs on disk")
    check(all(f"]({Path(c['svg_path']).name})" in out["markdown"] for c in ok),
          "the Markdown carries each chart with its caption as the alt text")
    check(ed["reading_minutes"] == max(1, math.ceil(
              (ed["words"] + rd.stored_words(ed)) / rd.WORDS_PER_MINUTE
              + nch * rd.SECONDS_PER_CHART / 60.0)),
          f"the reading time counts the {nch} charts at 20 seconds each")
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
          == sorted(f"{k.lower()}@chester" for k in ok_ids)
          and all(b[:4] == b"\x89PNG" for _, b in sent["inline_images"]),
          "delivery reads the archived PNGs back and sends them by Content-ID with "
          "the archived HTML")
    att = {a[0]: a for a in sent.get("attachments") or []}
    page = att.get(f"monthly_macro_{stamp}.html")
    check(f"monthly_macro_{stamp}.md" in att and page and page[2] == "html"
          and "cid:" not in page[1]
          and page[1].count("data:image/png;base64,") == len(ok_ids),
          "N1: the email attaches the edition's HTML beside the Markdown, every "
          "chart embedded in it, so Safari can lay it out to the phone")


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
                                      "detail": e2["detail"],
                                      "summary": e2.get("summary")})
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


def tree(root: Path) -> dict[str, str]:
    """Every file under `root`, by relative path, with its content hash."""
    import hashlib
    return {str(f.relative_to(root)).replace("\\", "/"):
            hashlib.sha256(f.read_bytes()).hexdigest()
            for f in root.rglob("*") if f.is_file()}


def dryrun_group(p: dict, prior: dict) -> None:
    """M: the real dry run (--dry-run [--email]) on monthly_macro.run."""
    import copy
    import sys as _sys
    from monthly_macro import run as run_mod, snapshot as snap_mod
    from monthly_macro import stack as ms
    print(f"\n{LINE}\nM. THE DRY RUN: WRITES ONLY reports/dryrun/, READS THE REAL "
          f"ARCHIVE\n{LINE}")
    root = Path(TD)
    reports = root / "box" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (root / "box" / "store").mkdir(exist_ok=True)
    (root / "box" / "snapshots").mkdir(exist_ok=True)
    # The real archive holds the prior Monthly the marks compare against.
    ms.save_edition(dict(prior, report_date=PREV), str(reports))
    emitted: list = []
    sent: list = []
    saved = (run_mod.payload_mod.build, run_mod.emit, run_mod.delivery.send_html,
             snap_mod.SNAPSHOT_DIR, os.environ.get("ALTDATA_STORE"), _sys.argv)
    run_mod.payload_mod.build = lambda as_of=None, run_id=None: copy.deepcopy(p)
    run_mod.emit = lambda *a, **k: emitted.append(k)
    run_mod.delivery.send_html = (lambda subject, html, **k:
                                  sent.append((subject, html, k)) or ("sent", "ok"))
    snap_mod.SNAPSHOT_DIR = root / "box" / "snapshots"
    os.environ["ALTDATA_STORE"] = str(root / "box" / "store")

    def run(*argv: str) -> int:
        _sys.argv = ["monthly_macro.run", "--out-dir", str(reports), *argv]
        try:
            return run_mod.main()
        except SystemExit as exc:
            return int(exc.code or 0)

    try:
        rc_refused = run("--email", "--skip-narrative")
        sent_refused = len(sent)
        before = tree(root)
        rc = run("--dry-run", "--email", "--skip-narrative")
        after = tree(root)
        rc_quiet = run("--dry-run", "--skip-narrative")
    finally:
        (run_mod.payload_mod.build, run_mod.emit, run_mod.delivery.send_html,
         snap_mod.SNAPSHOT_DIR, store_env, _sys.argv) = saved
        if store_env is None:
            os.environ.pop("ALTDATA_STORE", None)
        else:
            os.environ["ALTDATA_STORE"] = store_env
    check(rc_refused == 1 and sent_refused == 0,
          "--email without --dry-run is refused and sends nothing")
    dry = "box/reports/dryrun/"
    changed = sorted(k for k in set(before) | set(after)
                     if before.get(k) != after.get(k))
    outside = [k for k in changed if not k.startswith(dry)]
    check(rc == 0 and changed and not outside,
          f"--dry-run writes nothing outside reports/dryrun/ ({len(changed)} "
          f"file(s) written there; outside: {outside or 'none'})")
    check(not any(k.startswith("box/snapshots/") for k in after) and not emitted,
          "no snapshot and no state record")
    stack_json = reports / "dryrun" / f"monthly_macro_{REPORT_DATE}_stack.json"
    ed = json.loads(stack_json.read_text(encoding="utf-8")) if stack_json.exists() else {}
    check(ed.get("prior_session") == PREV,
          f"it reads the real archive: the change marks compare against the prior "
          f"Monthly of {PREV} ({ed.get('prior_session')})")
    check(len(sent) == 1 and sent[0][0].startswith("[DRY RUN] ")
          and sent[0][1] == (reports / "dryrun" / f"monthly_macro_{REPORT_DATE}.html"
                             ).read_text(encoding="utf-8"),
          f"--email sends one copy, \"[DRY RUN]\" in the subject, byte-identical to "
          f"the dry-run archive ({sent[0][0] if sent else 'nothing sent'})")
    check(rc_quiet == 0 and len(sent) == 1,
          "without --email the dry run sends nothing")


def t31_phone_group(ed: dict, out: dict) -> None:
    """N1: text wraps on the phone (T3.1 item 1)."""
    from daily_cascade import stack_render as sr
    print(f"\n{LINE}\nN1. T3.1 ITEM 1: TEXT WRAPS ON THE PHONE\n{LINE}")
    html = out["html_email"]
    check(sr.TDL_WRAP in html and sr.TDL + '"' not in html,
          "at the Monthly's cadence every text cell wraps (overflow-wrap:anywhere)")
    check(f'<td style="{sr.TD}">' in html and "nowrap" not in sr.TDL_WRAP,
          "and only a numeric cell keeps nowrap")
    wide = {"columns": [f"c{i}" for i in range(8)], "rows": [["a"] * 8]}
    check(sr.TBL_FIXED in sr._table(wide, True)
          and sr.TBL_FIXED not in sr._table(dict(wide, columns=wide["columns"][:5],
                                                  rows=[["a"] * 5]), True),
          "a table wider than six columns lays out fixed; a narrower one does not")
    sec = next(s for s in ed["sections"] if s["id"] == "tape")
    weekly = sr.section_html(sec, 2, {}, "email", "weekly")
    daily = sr.section_html(sec, 2, {}, "email", "daily")
    check(sr.TDL_WRAP not in weekly and sr.TDL_WRAP not in daily
          and sr.TBL_FIXED not in sr._table(wide),
          "the close and the Weekly render as before: the switch is the Monthly "
          "cadence's (config `mobile_tables`)")


def t31_tape_group(ed: dict, out: dict) -> None:
    """N2: the tape (T3.1 items 2-4; the charts, items 5-6, in K)."""
    print(f"\n{LINE}\nN2. T3.1 ITEMS 2-6: THE TAPE\n{LINE}")
    tape = next(s for s in ed["sections"] if s["id"] == "tape")
    t = tape.get("table") or {}
    rows = {r[0]: r for r in t.get("rows") or []}
    norm = lambda x: str(x).replace("−", "-")                    # noqa: E731
    check(t.get("columns") == ["Market", f"Close, {M_END}", "Move", "Year to date",
                               "Level, 5y percentile"]
          and not any(f"Close, {M_START}" in c for c in t.get("columns") or []),
          "item 2: the first table is the close and the move, plus the year to date; "
          "the prior month-end's close is gone")
    iwm = rows.get("Russell 2000 (IWM)") or []
    y10 = rows.get("10-year Treasury") or []
    spx = rows.get("S&P 500") or []
    check(iwm and norm(iwm[3]) == f"{100 * (102 / 104 - 1):+.2f}%"
          and y10 and norm(y10[3]) == "-15 bp",
          f"the year to date in the row's own unit, from the prior year-end close: "
          f"IWM {iwm[3] if iwm else None}, the 10-year {y10[3] if y10 else None}")
    check(spx and spx[3] == "—",
          "a close more than a week before the year's end is not the year-end's: "
          "the S&P 500 prints a dash")
    lf = next((ss for ss in tape["subsections"]
               if ss["title"].startswith("The long frame")), {})
    cols = (lf.get("table") or {}).get("columns") or []
    check(cols[2:5] == ["40-week (≈200-day) average", "10-month (≈210-day) average",
                        "20-month (≈400-day) average"],
          "item 3: the long frame keeps its ruled averages, each labelled with its "
          "daily equivalent")
    check("Year to date" in out["markdown"] and "Year to date" in out["html_email"],
          "the year to date prints in the HTML and the Markdown")


def t31_misfit_group(ed: dict, out: dict) -> None:
    """N3: What doesn't fit as headers, a sentence and bullets (T3.1 item 7)."""
    from daily_cascade import stack_render as sr, weekly_stack as ws
    print(f"\n{LINE}\nN3. T3.1 ITEM 7: WHAT DOESN'T FIT, HEADERS AND BULLETS\n{LINE}")
    mis = next(s for s in ed["sections"] if s["id"] == "misfit")
    pts = mis.get("points") or []
    gt = (mis.get("data") or {}).get("gap_table") or {}
    check(not mis.get("table") and gt.get("rows") and len(pts) == len(gt["rows"]),
          f"the gap table no longer prints; each of its {len(gt.get('rows') or [])} "
          f"row(s) is a point, and the table stays in the section's data")
    p0 = pts[0] if pts else {}
    check(p0.get("head") and p0.get("sentence") and p0.get("sentence").endswith(".")
          and any(b.startswith("z +2.4") for b in p0.get("bullets") or [])
          and any("session" in b for b in p0.get("bullets") or []),
          f"a point is a short header, one sentence on the mechanism, and the "
          f"figures as bullets ({p0.get('head')}: {p0.get('bullets')})")
    html = out["html_email"]
    mark = "&middot; What doesn"
    block = (html.split(mark)[1].split("&middot; Plumbing")[0] if mark in html
             else "")
    check(f'<p style="{sr.POINT_HEAD}">' in block and f'<ul style="{sr.BULLETS}">' in block
          and "What each side is saying" not in block,
          "the page prints them as header, paragraph and bullets, not the table")
    check(f"**{p0.get('head')}**" in out["markdown"],
          "and the Markdown the same way")
    dis = next((ss for ss in mis["subsections"]
                if ss["title"] == "Dissent and corrections this month"), {})
    check(not dis.get("table") and (dis.get("points") or dis.get("lines")),
          "the dissent and corrections print as points too, or say there were none")
    check(any(i["key"].startswith("misfit:gap:") and i.get("show") is False
              for i in mis["items"]),
          "each gap row stays in the fingerprint as a hidden item, so the change "
          "marks still see it")
    wk = ws.misfit_week({"contradictions": [{"id": "equities_vs_credit",
                                             "open_state": "open", "magnitude": 2.4,
                                             "persistence_days": 6}]}, None, {})
    check(wk.get("table") and not wk.get("points"),
          "the Weekly's builder is unchanged: its gap table prints as a table")


def t31_plumbing_group(cfg: dict, ed: dict, out: dict) -> None:
    """N4: Plumbing & rates in six buckets (T3.1 item 8)."""
    from altdata import derived
    from monthly_macro import stack as ms
    print(f"\n{LINE}\nN4. T3.1 ITEM 8: PLUMBING & RATES IN SIX BUCKETS\n{LINE}")
    bcfg = cfg.get("monthly_plumbing_buckets") or {}
    pl = next(s for s in ed["sections"] if s["id"] == "plumbing")
    titles = [ss["title"] for ss in pl["subsections"]]
    want = [bcfg["titles"][b] for b in bcfg.get("order") or []]
    check(titles[:6] == want and bcfg["order"] == ["yields", "macro", "liquidity",
                                                    "auctions", "metals", "global"],
          f"six buckets in the ruled order: {titles}")
    check(not pl.get("table") and (pl["data"].get("table") or {}).get("rows"),
          "the one table no longer prints; it stays in the section's data")
    by = {ss.get("bucket"): ss for ss in pl["subsections"]}
    rows = lambda b: [r[0] for r in (by.get(b, {}).get("table") or {}).get("rows") or []]  # noqa: E731
    check("30-year" in rows("yields") and "SOFR" in rows("liquidity")
          and any(x.startswith("Net liquidity") for x in rows("liquidity"))
          and any(x.startswith("Copper") for x in rows("metals"))
          and any(x.startswith("Gold over copper") for x in rows("metals"))
          and any(x.startswith("USD/JPY") for x in rows("global"))
          and any("auction" in x for x in rows("auctions")),
          "each row in its bucket: the 30-year in yields & spreads, SOFR and net "
          "liquidity in liquidity, copper in metals, USD/JPY in global rates, the "
          "month's auctions in auction results")
    other = pl["data"].get("other_rows")
    check(other == [] and pl["data"]["buckets"].get("other") is None,
          f"no fixture row falls to \"other\" (the gate counts them: {other})")
    check(ms.bucket_of("Mystery series", None, bcfg) == "other"
          and ms.bucket_of("SOFR less IORB (funding pressure when above zero)", None,
                           bcfg) == "liquidity"
          and ms.bucket_of("10-Year note auction (2026-09-10): high yield 4.1%", None,
                           bcfg) == "auctions"
          and ms.bucket_of("Payrolls", "fred.nfp", bcfg) == "macro",
          "a row is bucketed by its series key, else by a label pattern, else "
          "\"other\"")
    saved = derived.registry_entry
    derived.registry_entry = lambda k: {"family": "fx"} if k == "x.fx" else saved(k)
    try:
        fam = ms.bucket_of("A cross", "x.fx", dict(bcfg, families={"fx": "global"}))
    finally:
        derived.registry_entry = saved
    check(fam == "global", "and by the registry's family first, where it declares one")
    sub_n = [ss for ss in pl["subsections"] if (ss.get("table") or {}).get("rows")]
    check(sub_n and all(ss.get("paragraphs") for ss in sub_n)
          and all(f"block:plumbing:{ss['bucket']}" in out["written"] for ss in sub_n),
          f"each bucket with rows carries one written takeaway through the section "
          f"writer ({len(sub_n)} buckets)")
    empty = [ss for ss in pl["subsections"] if not (ss.get("table") or {}).get("rows")]
    check(all(ss.get("lines") and not ss.get("paragraphs") for ss in empty),
          "a bucket with nothing stored says so and asks for no paragraph")
    check(pl.get("claim") and not pl.get("paragraphs"),
          "the section's own call writes the claim line alone: the reads are the "
          "buckets'")
    from daily_cascade import cadence as cadence_mod, stack_render as sr
    ss = dict(by.get("yields") or {}, charts_rendered=["M4"])
    fake = {"M4": {"id": "M4", "caption": "fixture chart", "svg_path": "m4.svg"}}
    mon = cadence_mod.get("monthly")
    after = sr.subsection_html(ss, "month", mon, charts=fake, mode="archive")
    before = sr.subsection_html(dict(ss, charts_after_prose=False), "month", mon,
                                charts=fake, mode="archive")
    para = (ss.get("paragraphs") or ["~"])[0][:30]
    check(after.find(para) < after.find("<figure")
          and before.find("<figure") < before.find(para),
          "the charts print under their bucket's paragraph (a sub-section without "
          "the flag keeps them above)")
    check((by.get("yields") or {}).get("charts_rendered") == ["M4", "M5"],
          "M4 and M5 are placed in the yields & spreads bucket")


def t31_positioning_group(ed: dict, out: dict) -> None:
    """N5: Positioning at the Monthly's horizons, with a read on every
    sub-section (T3.1 items 9-10; the chart, item 11, in K)."""
    from altdata import observations
    from daily_cascade import weekly_sections as wsec
    print(f"\n{LINE}\nN5. T3.1 ITEMS 9-11: POSITIONING & FLOWS\n{LINE}")
    pos = next(s for s in ed["sections"] if s["id"] == "positioning")
    subs = {ss["title"]: ss for ss in pos["subsections"]}
    sec = subs.get("Sector rotation and leadership") or {}
    check((sec.get("table") or {}).get("columns") == ["Sector or pair", "The month",
                                                     "Three months", "Twelve months"],
          "item 9: the sector table's horizons are the month, three months and "
          "twelve months; the trailing 22 sessions are gone")
    with observations.ObservationStore(DB) as st:
        wk = wsec.sector_table(st, ed["window"]["now"], ed["window"]["then"], [])
    check(wk["table"]["columns"] == ["Sector or pair", "Week", "One month",
                                     "Three months"],
          "the Weekly's sector table is unchanged: the switch is the cadence")
    want = ["sectors", "cftc", "short", "retail", "tic"]
    check([ss.get("phase") for ss in pos["subsections"]]
          == [f"block:positioning:{g}" for g in want],
          "item 10: each of the five sub-sections -- sectors, CFTC, short interest, "
          "retail sentiment, TIC -- is set up for its own written read")
    with_rows = [ss for ss in pos["subsections"] if (ss.get("table") or {}).get("rows")]
    check(with_rows and all(ss.get("prose") and ss.get("paragraphs") for ss in with_rows)
          and all(ss.get("prose") is None for ss in pos["subsections"]
                  if not (ss.get("table") or {}).get("rows")),
          f"a sub-section with figures carries its paragraph ({len(with_rows)}); one "
          f"without asks for none")
    from monthly_macro import stack as ms
    check("prior month" in ms.READ_SCOPE and "own history" in ms.READ_SCOPE
          and "history too short" in ms.READ_SCOPE
          and all((ss.get("prose") or {}).get("scope") == ms.READ_SCOPE
                  for ss in with_rows if ss["title"] != "Sector rotation and leadership"),
          "the read is asked for the level, the change on the prior month and the "
          "level's place in its own history, or \"history too short\"")
    check(pos.get("claim_only") and not pos.get("paragraphs"),
          "the section's own call writes the claim line alone (here it faulted, F)")


def t31_priced_group(ed: dict, out: dict) -> None:
    """N6: What's priced in blocks, each with its read (T3.1 items 12-13)."""
    from monthly_macro import prose as prose_mod, stack as ms
    print(f"\n{LINE}\nN6. T3.1 ITEMS 12-13: WHAT'S PRICED, BLOCK BY BLOCK\n{LINE}")
    pr = next(s for s in ed["sections"] if s["id"] == "priced")
    titles = [ss["title"] for ss in pr["subsections"]]
    check(titles[:4] == ["FOMC pricing: the fed-funds path", "Breakevens",
                         "Prediction markets: the FOMC", "Prediction markets: the rest"],
          f"item 12: FOMC pricing and the breakevens are two blocks; item 13: the "
          f"prediction markets are the FOMC's and the rest ({titles[:4]})")
    subs = {ss["title"]: ss for ss in pr["subsections"]}
    be = subs["Breakevens"]
    check((be.get("table") or {}).get("rows") and be.get("paragraphs")
          and "block:priced:breakevens" in out["written"]
          and all(not str(r[0]).startswith("FOMC") for r in be["table"]["rows"]),
          "the breakevens block carries its rows and its own read")
    fo = subs["FOMC pricing: the fed-funds path"]
    check(not (fo.get("table") or {}).get("rows") and fo.get("prose") is None
          and "fed funds futures" in " ".join(fo.get("not_tracked") or []),
          "with no rate path stored, the FOMC block asks for no read and says why")
    rows = [["FOMC 2026-10-28: hold", "90%", "88%", "—", "—"],
            ["Recession in 2026 (Yes)", "20%", "22%", "—", "—"]]
    check(ms._split_rows(rows, True) == rows[:1] and ms._split_rows(rows, False)
          == rows[1:], "a row is the FOMC's when its item names an FOMC meeting")
    fake = {"month": "September 2026", "sections": [{
        "id": "priced", "title": "What's priced", "empty": False,
        "subsections": [{"title": "Prediction markets: the rest",
                         "phase": "block:priced:pm_rest",
                         "table": {"columns": ["Item"], "rows": [rows[1][:1]]},
                         "prose": {"words": "60 to 100", "scope": "x",
                                   "note": ms.PM_CHANNEL_NOTE}}]}]}
    plan = prose_mod.block_plan(fake)
    check(len(plan) == 1 and "MARKET CHANNEL" in plan[0]["system"]
          and "60 to 100 words" in plan[0]["system"]
          and plan[0]["slice"]["table"]["rows"] == [rows[1][:1]],
          "the rest are read for their market channel -- what a change in the odds "
          "would move, and through what -- over their own rows only")
    check(pr.get("claim") and not pr.get("paragraphs"),
          "the section's own call writes the claim line alone")


def t31_ahead_group(ed: dict) -> None:
    """N7: Ahead's weekday and 1-5 significance rank (T3.1 item 14)."""
    from daily_cascade import events_block as eb
    print(f"\n{LINE}\nN7. T3.1 ITEM 14: AHEAD, WEEKDAY AND SIGNIFICANCE\n{LINE}")
    ah = next(s for s in ed["sections"] if s["id"] == "ahead")
    rows = [r for ss in ah["subsections"] for r in (ss.get("table") or {}).get("rows")
            or [] if (ss.get("table") or {}).get("columns", [""])[0] == "Date"]
    fomc = next((r for r in rows if str(r[2]).startswith("FOMC statement")), None)
    check(fomc and fomc[1] == "Wed" and str(fomc[3]) == "5"
          and fomc[4] == "the rate decision itself",
          f"every calendar row carries its weekday and its rank, with a one-clause "
          f"reason at 4-5 ({fomc})")
    cases = {"Consumer Price Index -- September": 5, "FOMC minutes": 4,
             "Note:10-Year auction": 4, "ISM Manufacturing PMI": 3,
             "Industrial Production": 2, "A conference nobody lists": 1,
             "TRIPLE_WITCHING": 5}
    got = {t: eb.significance(t)["rank"] for t in cases}
    check(got == cases,
          f"the rank is read from the tiers: tier 1 is 5, tier 2 is 4 on the "
          f"Plumbing trigger's list and 3 off it, a named tier 3 is 2, the rest 1 "
          f"({got})")
    check(eb.significance("ISM Manufacturing PMI")["why"] is None
          and eb.significance("Note:10-Year auction")["why"],
          "a reason prints only beside a rank of 4 or 5")


def t31_narratives_group(ed: dict, out: dict) -> None:
    """N8: the Narratives' longer horizons and the voices as prose (T3.1
    items 16-17)."""
    print(f"\n{LINE}\nN8. T3.1 ITEMS 16-17: NARRATIVES\n{LINE}")
    nar = next(s for s in ed["sections"] if s["id"] == "narratives")
    subs = {ss["title"]: ss for ss in nar["subsections"]}
    roll = next((ss for t, ss in subs.items() if t.startswith("The four weeks")), {})
    cols = (roll.get("table") or {}).get("columns") or []
    rows = {r[0]: r for r in (roll.get("table") or {}).get("rows") or []}
    yen = rows.get("The yen carry") or []
    check(cols[-2:] == ["Three months", "Since the register began (18 Sep)"],
          f"item 16: the story table gains the three months and the register's "
          f"whole span ({cols[-2:]})")
    check(yen and yen[-2] == "since 18 Sep: 1 for / 1 against"
          and yen[-1] == "1 for / 1 against",
          f"where the register is younger than the window the cell says \"since 18 "
          f"Sep\" with the count it has, never a blank ({yen[-2:] if yen else None})")
    check(not any((ss.get("table") or {}).get("columns", [""])[0] == "Voice"
                  for ss in nar["subsections"]),
          "item 17: the voices table no longer prints")
    vy = next((ss for t, ss in subs.items() if t.startswith("Voices: The yen carry")),
              {})
    pt = (vy.get("points") or [{}])[0]
    b = pt.get("bullets") or []
    check(pt.get("head", "").startswith("The yen carry")
          and "1 for and 1 against this month; 1 for and 1 against over three "
              "months" in pt.get("head", "")
          and "dissent from" not in pt.get("head", "")
          and len(b) == 2 and all(isinstance(x, dict) and x["source"].startswith(
              "Source: Goldman Sachs, ") and "https://fixture.example/" in x["source"]
              for x in b),
          "per story: who said what as bullets, each with its source line beneath")
    check(all("Status this month" in x["text"] and "over three months" in x["text"]
              and "(since 18 Sep)" in x["text"] for x in b),
          "each voice carries its status this month and over three months, the "
          "latter \"since 18 Sep\"")
    check(vy.get("paragraphs") and "block:voices:yen_carry" in out["written"],
          "and one short written paragraph per story, through the section writer")
    vo = subs.get("Voices on no story") or {}
    check([p["head"] for p in vo.get("points") or []]
          == ["Charlie Analyst, Fixture Bank (sell-side strategist)"]
          or any("Charlie Analyst" in p["head"] for p in vo.get("points") or []),
          "a voice heard on no story prints after the stories, with its status and "
          "source")
    html = out["html_email"]
    check(sr_bullet_source_in(html) and "Consensus against contrarian" in html,
          "the page prints the bullets with their source lines, and the consensus "
          "line")


def sr_bullet_source_in(html: str) -> bool:
    from daily_cascade import stack_render as sr
    return f'<br><span style="{sr.BULLET_SOURCE}">Source: Goldman Sachs' in html


def t31_scenarios_themes_group(ed: dict, out: dict) -> None:
    """N9: the scenarios' new shape (item 18) and a paragraph per alternative-
    asset family (item 19)."""
    from monthly_macro import stack as ms
    print(f"\n{LINE}\nN9. T3.1 ITEMS 18-19: SCENARIOS, AND THE THEMES BY FAMILY\n{LINE}")
    ah = next(s for s in ed["sections"] if s["id"] == "ahead")
    sc = next(ss for ss in ah["subsections"]
              if ss["title"] == "Scenarios, and what would change our mind")
    pts = sc.get("points") or []
    check(not sc.get("table") and pts
          and all(p["sentence"] == ms.SCENARIO_SUMMARY_PENDING for p in pts)
          and all(p["more"][0].startswith(ms.SCENARIO_MIND_PENDING) for p in pts),
          f"item 18: each scenario prints as its header, a summary and what would "
          f"change our mind -- the placeholders until scenario set #1 ({len(pts)})")
    full = ms.scenario_point({"claim": "Soft landing", "probability": 0.55,
                              "brier": None, "resolve_by": "2026-12-31",
                              "summary": "Growth slows without breaking.",
                              "change_our_mind": "Two payroll prints below zero. "
                                                 "Credit spreads past their 90th."})
    check(full["head"].startswith("Soft landing — p 0.550, Brier pending")
          and full["sentence"] == "Growth slows without breaking."
          and full["more"] == ["What would change our mind: Two payroll prints "
                               "below zero. Credit spreads past their 90th."],
          "with the content in place, the summary and the sentences print as stored")
    check("Summary to come" in out["html_email"] and "What would change our mind"
          in out["markdown"], "the placeholder prints in the page and the Markdown")
    sl = next(s for s in ed["sections"] if s["id"] == "slow")
    fam = [ss for ss in sl["subsections"] if ss["title"].startswith("Themes: ")]
    names = [ss["title"] for ss in fam]
    check(names == ["Themes: digital", "Themes: energy", "Themes: metals",
                    "Themes: real assets"],
          f"item 19: one block per alternative-asset family ({names})")
    met = next(ss for ss in fam if ss["title"] == "Themes: metals")
    check(met.get("paragraphs") and "block:slow:metals" in out["written"]
          and (met.get("prose") or {}).get("scope", "").startswith("what moved"),
          "a family with rows carries its paragraph: what moved, the long frame, "
          "the takeaway")
    ra = next(ss for ss in fam if ss["title"] == "Themes: real assets")
    check(not ra.get("prose") and "Not yet sourced" in " ".join(ra.get("lines") or []),
          "a family not yet sourced says what it needs, and asks for no paragraph")


def t31_summary_group(ed: dict, out: dict) -> None:
    """N10: the executive summary (T3.1 item 20) and the budget (item 22)."""
    from daily_cascade import stack as stack_mod, stack_render as sr
    from monthly_macro import prose as prose_mod, stack as ms
    print(f"\n{LINE}\nN10. T3.1 ITEMS 20 AND 22: THE EXECUTIVE SUMMARY, THE BUDGET\n{LINE}")
    summ = ed.get("summary") or []
    check([e["id"] for e in summ] == [s["id"] for s in ed["sections"]],
          f"item 20: one summary paragraph per section, in stack order, the read "
          f"to Slow layers ({len(summ)})")
    sw = out.get("summary_written") or {}
    live = [s["id"] for s in ed["sections"] if not s.get("empty")]
    check(sorted(k.split(":", 1)[1] for k in sw) == sorted(live)
          and all(e.get("note") for e in summ if e["id"] not in live),
          "one audited call per section with something to say; an empty section "
          "prints its empty note")
    tape = next(e for e in summ if e["id"] == "tape")
    check(not tape["text"] and tape["note"] == prose_mod.SUMMARY_WITHHELD
          and "999" in str(sw["summary:tape"].get("first_reason"))
          and sw["summary:tape"]["attempts"] == 2,
          "a paragraph the audit withholds, after its one retry, prints \"(summary "
          "withheld — audit)\" rather than an unaudited sentence")
    plan = {x["key"]: x for x in prose_mod.summary_plan(ed)}
    sl = (plan.get("summary:plumbing") or {}).get("slice") or {}
    check(sl.get("section") == "Plumbing & rates" and "subsections" in sl
          and not any(k in json.dumps(sl) for k in ("month_in_markets",
                                                     "looking_back")),
          "each call sees its finished section -- claim, paragraphs, tables, lines, "
          "points -- never the raw payload")
    html, md = out["html_email"], out["markdown"]
    check("Executive summary" in html and html.index("Executive summary")
          < html.index("1 &middot; The read") and prose_mod.SUMMARY_WITHHELD in html
          and md.index("## Executive summary") < md.index("## 1 · The read"),
          "it opens the edition, before section 1, in the HTML and the Markdown")
    check(ed.get("summary_minutes") and f"About {ed['summary_minutes']} minute"
          in html and "with section 1" in md,
          f"the short path prints its own reading time, the summary with section 1 "
          f"({ed.get('summary_minutes')} min)")
    n = sum(stack_mod.words(e.get("text")) for e in summ)
    check(n and ed["words"] == stack_mod.edition_words(ed)
          and stack_mod.edition_words(dict(ed, summary=[])) == ed["words"] - n,
          f"the summary is prose and counts in the budget ({n} of {ed['words']} "
          f"words)")
    check(ms.apply_summary({"sections": ed["sections"]}, {}, False)["summary"] == []
          and not sr.summary_html({"summary": []}),
          "with no narrative step there is no summary, and the page prints none")
    check(ed.get("budget") == {"words": 10000, "charts": 12}
          and ed.get("reading_target_minutes") == 55,
          "item 22: the Monthly's budget is 10,000 words and its target 55 minutes; "
          "the chart cap is 12 (ruled 9 Oct 2026)")
    from monthly_macro import charts as mch
    check(mch.m8([], "x", None) == {"id": "M8",
                                    "unavailable": "not yet: scenario set #1"},
          "M8 prints \"not yet: scenario set #1\" while the ledger holds no Monthly "
          "weight, and counts only once it draws")


ORDINAL = re.compile(r"\b\d{1,3}(?:st|nd|rd|th)\b")


def _tables_with_data(ed: dict):
    """(where, table, the data its section and sub-section carry) for every
    table the Monthly's sections print."""
    for s in ed.get("sections") or []:
        if s.get("table"):
            yield s["id"], s["table"], [s.get("data") or {}]
        for ss in s.get("subsections") or []:
            if ss.get("table"):
                yield (f"{s['id']}/{ss.get('title')}", ss["table"],
                       [ss.get("data") or {}, s.get("data") or {}])


def t32_group(ed: dict, out: dict) -> None:
    """O: the fixes from the first real dry run (T3.2, 10 Oct 2026)."""
    from altdata import numeral_audit as na
    from daily_cascade import cadence as cad_mod, stack_prose as sp
    from monthly_macro import prose as prose_mod, stack as ms
    print(f"\n{LINE}\nO. T3.2: THE FIXES FROM THE FIRST REAL DRY RUN\n{LINE}")

    # O1 -- the paragraph figure cap.
    caps = {c: cad_mod.figure_cap(cad_mod.get(c)) for c in cad_mod.NAMES}
    check(caps == {"daily": 6, "weekly": 6, "monthly": 8}
          and prose_mod.figure_cap() == 8,
          f"O1 item 1: the per-paragraph figure cap is the cadence's -- the close "
          f"and the Weekly 6, the Monthly 8 ({caps})")
    seven = ("SPY rose. It closed at 512.30, up 1.2%, with QQQ up 1.5%, IWM down "
             "0.4%, the 10-year at 4.12% and the 30-year at 4.61%, while HY OAS "
             "sat at 3.10%.")
    nine = seven[:-1] + ", gold at 2,401 and oil at 71.20."
    check(sp.figure_faults(seven) and not sp.figure_faults(seven, 8)
          and sp.figure_faults(nine, 8)
          and "at most 8 -- the tables carry the rest" in sp.figure_faults(nine, 8)[0],
          "seven figures pass the Monthly's guard and fail the close's; nine fail "
          "both, the reason naming the cap")
    plans = (prose_mod.stack_plan(ed) + prose_mod.block_plan(ed))
    frames = [x["system"] for x in plans] + [prose_mod.system_prompt("T", "S")]
    check(plans and all("EIGHT figures" in f and "the tables carry the rest" in f
                        for f in frames),
          f"every Monthly section, block and v2 frame states the cap of eight and "
          f"that the tables carry the rest ({len(frames)} frames)")
    summ = prose_mod.summary_plan(ed)
    check(summ and all("at most three figures per paragraph" in x["system"]
                       and "EIGHT" not in x["system"].split("SHAPE.", 1)[1]
                                                      .split("THE TAPE'S", 1)[0]
                       for x in summ),
          f"the executive summary's frames say \"at most three figures per "
          f"paragraph\" ({len(summ)} frames)")
    wk = sp.section_prompt({"id": "tape", "title": "The tape", "depth": "medium"},
                           "weekly")
    dl = sp.section_prompt({"id": "tape", "title": "The tape", "depth": "medium"},
                           "daily")
    check("cite at most SIX figures in it.\n" in wk and "EIGHT" not in wk
          and "cite at most SIX figures in it.\n" in dl,
          "the close's and the Weekly's prompts are unchanged: six figures")
    written = out.get("written") or {}
    over = [k for k, r in written.items()
            if "at most 6 --" in str(r.get("reason")) + str(r.get("first_reason"))]
    check(not over, f"no Monthly paragraph is held to six ({over[:3]})")

    # O2 -- one rounding rule for the ordinals.
    check(ms._ord(98.5) == "99th" and ms._ord(99.95) == "100th"
          and ms._ord(51.7) == "52nd" and ms._ord(32.5) == "33rd"
          and ms._ord(None) == "—"
          and na.with_ordinals({"percentile": 98.5})["percentile_ordinal"] == "99th"
          and f"{98.5:.0f}" == "98",
          "O2 item 2: a table's percentile is the half-up ordinal the payload's "
          "_ordinal fields use (98.5 -> 99th, 99.95 -> 100th), where the old "
          "format printed 98")
    printed, bad = 0, []
    for where, t, data in _tables_with_data(ed):
        cols = [i for i, c in enumerate(t.get("columns") or [])
                if "percentile" in str(c).lower()]
        if not cols:
            continue
        held = set()
        for d in data:
            held |= na.stored_ordinals(na.with_ordinals(d))
        for r in t.get("rows") or []:
            for i in cols:
                for o in ORDINAL.findall(str(r[i]) if i < len(r) else ""):
                    printed += 1
                    if o.lower() not in held:
                        bad.append((where, r[0], o))
    check(printed and not bad,
          f"every ordinal printed in a Monthly table's percentile column equals "
          f"its _ordinal ({printed} printed" + (f"; unmatched {bad[:3]})" if bad
                                                else ")"))
    tape = next(s for s in ed["sections"] if s["id"] == "tape")
    pair = [(r[4], m.get("level_percentile_5y_ordinal")) for r, m in
            zip(tape["table"]["rows"], tape["data"]["moves"])]
    check(pair and all(a == (b or "—") for a, b in pair)
          and all(not re.search(r"\d\.\d", a) for a, _ in pair),
          f"the tape's percentile column is its rows' _ordinal, row for row, never "
          f"a decimal ({pair[:2]})")
    check(all(prose_mod.ORDINAL_RULE.strip() in f for f in frames)
          and all(prose_mod.ORDINAL_RULE.strip() in x["system"] for x in summ),
          "and every Monthly frame says to copy an ordinal exactly as printed")

    # O3 -- units at the source.
    ct = na.cell_types
    check(ct("+35.5 / +38.0 pts") == [(35.5, "price"), (38.0, "price")]
          and ct("+2.0 / — pts") == [(2.0, "price")]
          and ct("−5.40 percent") == [(-5.4, "percent")]
          and ct("+44.00 bps") == [(44.0, "bp")]
          and ct("12 / 30") == [(12.0, "count"), (30.0, "count")]
          and ct("prior 200,500") == [(200500.0, "count")],
          "O3 item 3: a cell's \"a / b pts\" pair is two figures in points, "
          "\"percent\" is a percent; a figure with no unit word is still a count")
    sl = {"table": {"columns": ["Item", "Week change"],
                    "rows": [["FOMC hold", "+35.5 / +38.0 pts"],
                             ["Shutdown", "+2.0 / — pts"]]},
          "rows": [{"series": "WTI", "change_20d_pct": -6.03}]}
    ok = [na.audit(t, na.with_signed(sl)).passed for t in (
        "The hold rose +35.5 points.", "The shutdown rose +2.0 points.",
        "WTI fell −6.03%.")]
    no = [na.audit(t, na.with_signed(sl)).passed for t in (
        "The hold rose +35.5 sessions.", "WTI fell −6.03 bp.", "WTI fell 6.03%.")]
    check(all(ok) and not any(no),
          f"the figures the 10 Oct run withheld now pass in their true unit, and the "
          f"audit is no looser: a wrong unit word or a dropped sign still fails "
          f"({ok}, {no})")
    slow = next(s for s in ed["sections"] if s["id"] == "slow")
    fam = [(r, row) for ss in slow.get("subsections") or [] if ss.get("family")
           for r, row in zip((ss.get("table") or {}).get("rows") or [],
                             (ss.get("data") or {}).get("rows") or [])]
    moved = [(r, d) for r, d in fam if r[2] != "—"]
    typed = [(r, d) for r, d in moved if d.get("change_20d_pct") is not None
             and r[2] == f"{d['change_20d_pct']:+.2f} percent"]
    fc = ms.family_change
    uso = {"family": "energy", "series": "yfinance.mkt_uso",
           **fc({"delta_20d": -5.4, "delta_unit": "percent"})}
    check(fam and len(typed) == len(moved)
          and fc({"delta_20d": -5.4, "delta_unit": "percent"})
          == {"change_20d_pct": -5.4}
          and fc({"delta_20d": 12.0, "delta_unit": "bps"}) == {"change_20d_bp": 12.0}
          and fc({"delta_20d": -6000.0, "delta_unit": "raw"}) == {}
          and fc({"delta_20d": None, "delta_unit": "percent"}) == {}
          and na.audit("USO fell −5.40 percent.", na.with_signed(uso)).passed
          and not na.audit("USO fell −5.40 bp.", na.with_signed(uso)).passed,
          f"each slow-layer family row with a 20-day change carries it in a field "
          f"typed by the registry's delta unit -- percent or bp, a raw change "
          f"nothing ({len(typed)} of {len(moved)} moved in the fixture, "
          f"{len(fam)} rows)")

    # O4 -- Plumbing's level differences.
    pl = next(s for s in ed["sections"] if s["id"] == "plumbing")
    liq = next(ss for ss in pl["subsections"] if ss.get("bucket") == "liquidity")
    ch = (liq.get("data") or {}).get("changes") or []
    cells = {r[0]: r[2] for r in liq["table"]["rows"]}
    check(ch and all(c["change_dollars_signed"] == cells.get(c["series"])
                     for c in ch),
          f"O4 item 4: the liquidity bucket's month changes ride in its data in "
          f"dollars, each with the signed form its table prints "
          f"({[(c['series'][:14], c['change_dollars_signed']) for c in ch][:3]})")
    neg = next((c for c in ch if c["change_dollars"] < 0), None)
    if neg:
        sl = na.with_signed(liq["data"])
        mag = neg["change_dollars_signed"].lstrip("−")
        r_bad = na.audit(f"It fell {mag}.", sl)
        r_ok = na.audit(f"It moved {neg['change_dollars_signed']}.", sl)
        check(not r_bad.passed and "change_dollars_signed" in r_bad.reason()
              and r_ok.passed,
              f"the bare magnitude ({mag}) is still withheld, now naming the field "
              f"to copy; the signed form passes")
    else:
        check(False, "the fixture's liquidity bucket has a negative change to test")
    import inspect
    from daily_cascade import weekly_sections as wsec, weekly_stack as wst
    check(((pl.get("data") or {}).get("plumbing") or {}).get("liquidity")
          and inspect.signature(wsec.plumbing_rows).parameters["liquidity_deltas"]
          .default is False
          and inspect.signature(wst.plumbing_week).parameters["liquidity_deltas"]
          .default is False,
          "the Monthly asks for the deltas; the Weekly's builders carry them only "
          "when asked (liquidity_deltas defaults off)")


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
        # N10: the tape's summary paragraph cites a figure its section does not
        # print, twice -- withheld, and the page says so in its place.
        '"The tape". A reader': ["The tape moved 999 points.",
                                 "The tape moved 998 points."],
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
    check(cfg["budget"]["monthly"] == {"words": 10000, "charts": 12}
          and cfg.get("reading_targets_minutes") == {"daily": 5, "weekly": 20,
                                                     "monthly": 55},
          "the Monthly budget (10,000 words, 12 charts; T3.1) and the three "
          "reading targets (5, 20, 55 minutes) are configuration")
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
          and "target 55 minutes" in out["html_email"]
          and f"about {rd.plural(mins, 'minute')} to read" in out["markdown"],
          "the header prints it the way the Weekly's does, beside its 55-minute "
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
    check(ed["words"] <= 10000 and ed["chart_count"] <= 12,
          f"{ed['words']} prose words of 10,000 and {ed['chart_count']} charts of 12")
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

    t31_phone_group(ed, out)
    t31_tape_group(ed, out)
    t31_misfit_group(ed, out)
    t31_plumbing_group(cfg, ed, out)
    t31_positioning_group(ed, out)
    t31_priced_group(ed, out)
    t31_ahead_group(ed)
    t31_narratives_group(ed, out)
    t31_scenarios_themes_group(ed, out)
    t31_summary_group(ed, out)
    t32_group(ed, out)
    scans_group(p, cfg, ed, out)
    ytd_group(cfg, ed, out)
    triple_group(cfg, ed, out)
    charts_group(cfg)
    reading_group(cfg)
    dryrun_group(p, ed)

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
