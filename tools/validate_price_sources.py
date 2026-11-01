#!/usr/bin/env python3
"""
Validation gate: the price sources' per-family switch (A96; tranche 2b of the
price-source migration, decisions 4 and 5 ruled D38). Fixtures only; a switched
family is a config held in memory, never the shipped file.

  A  THE DEFAULT     every family ships on yfinance, and every moved reader -- the
                     tape, the correlation universe, batch 3, the horizon charts, the
                     Quarterly's chapters, the move screen, the rates shape, the
                     consistency aliases -- gets the key it read before
  B  A SWITCH        a switched family resolves to the FRED key, its break label
                     carries the date and prints once per family, beneath the tape
                     table; unswitched, no label and no new field
  C  NO HARD CODE    no reader under daily_cascade/, monthly_macro/, altdata/ or
                     config/ names ^TNX's, ^TYX's or the dollar index's key, but for
                     the declared exemptions (the writer, the instrument identity, the
                     existing cross-source pairs, the switch file itself)
  D  NO SPLICE       across a switch a chart draws two series and the break, never
                     one series running through it
  E  PINS AND PAIRS  a pinned reference keeps its source; the inactive pairs resolve
                     and are not in the quality check's active list (A102: the 40
                     company-quarter pairs and the earnings events pair too)
  F  FUNDAMENTALS    (A102) the fundamentals family: 40 members, Yahoo's keys by
                     default and EDGAR's switched; the AI FCF panel and the capex
                     story's metrics move with it; no reader names a yfinance.fund_*
                     key outside the writer
  G  EARNINGS ROWS   (A102) the earnings_dates events family: unswitched, EDGAR's
                     parallel-run rows are invisible to every EventStore read and to
                     the direct SQL readers; switched, Yahoo's history before the
                     switch and EDGAR's from it, never both; every SQL read of the
                     earnings rows carries the clause; the forward-date gap line
  H  THE EDGAR WRITER (A102) a recorded company-facts response (synthetic): the tag
                     table, first tag wins, year-to-date quarters, the sign, net debt,
                     availability at the acceptance, the restatement as a vintage; the
                     8-K item 2.02 events with filed EPS, no consensus, no forward
                     date; switched off by default; the SEC caller's pacing
"""

from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from altdata import price_sources as ps                        # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
OLD = {"yfinance.mkt_tnx", "yfinance.mkt_tyx", "yfinance.mkt_dxy"}
# Where an old key may still be named, and why.
EXEMPT = {
    "altdata/sources/yfinance_source.py": "the writer of the keys",
    "config/security_master.yaml": "the instrument's identity (store_key)",
    "config/data_quality.yaml": "the existing ^TNX/DGS10 and ^TYX/DGS30 cross-source pairs",
    "config/price_sources.yaml": "the switch itself",
}


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def switched(*families: str, to: str = "fred") -> dict:
    c = copy.deepcopy(ps.config())
    for f in families:
        c["families"][f]["source"] = to
        c["families"][f]["switched_on"] = "2026-11-23"
    return c


class Using:
    """The resolver's cached config replaced for the block, then restored."""

    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg

    def __enter__(self):
        self.saved = ps._CFG                                    # noqa: SLF001
        ps._CFG = self.cfg                                      # noqa: SLF001
        return self

    def __exit__(self, *a):
        ps._CFG = self.saved                                    # noqa: SLF001


def group_a() -> None:
    head("A. THE DEFAULT")
    ps.reset()
    fams = ps.config()["families"]
    check(all(f["source"] == "yfinance" for f in fams.values()),
          f"every family ships on yfinance ({sorted(fams)})")
    check(ps.key("us_yields", "y10") == "yfinance.mkt_tnx"
          and ps.key("us_yields", "y30") == "yfinance.mkt_tyx"
          and ps.key("dollar_index", "dxy") == "yfinance.mkt_dxy",
          "the three keys resolve to Yahoo's, as read before")
    from altdata import bars, batch3, correlation           # noqa: PLC0415
    tape = {t["id"]: t.get("daily") for t in bars.tape()}
    check(tape.get("y10") == "yfinance.mkt_tnx" and tape.get("y30") == "yfinance.mkt_tyx"
          and tape.get("dxy") == "yfinance.mkt_dxy", "the tape's loader resolves them")
    correlation._CFG = None                                     # noqa: SLF001
    uni = {u["id"]: u.get("key") for u in correlation.config().get("universe") or []}
    check(uni.get("dxy") == "yfinance.mkt_dxy", "the correlation universe resolves the dollar")
    check((batch3.config().get("buybacks") or {}).get("thirty_year_tape")
          == "yfinance.mkt_tyx", "batch 3's thirty-year tape resolves")
    import horizon_charts as hc                                 # noqa: PLC0415
    hcfg = hc.load_config()
    uni2, _origin = hc.universe(hcfg)
    keys = [u.get("key") for u in uni2] + [
        s.get("key") for blk in (hcfg.get("panels") or {}).values() if isinstance(blk, dict)
        for s in (blk.get("series") or []) if isinstance(s, dict)]
    check("yfinance.mkt_dxy" in keys and not any(str(k).startswith("price:") for k in keys),
          "the horizon charts' config and universe resolve")
    from monthly_macro import quarterly_items as qi             # noqa: PLC0415
    qtxt = str(qi.load_config())
    check("price:" not in qtxt and "yfinance.mkt_dxy" in qtxt and "fred.dxy" in qtxt,
          "the Quarterly's chapters resolve, the twin chart keeping both indices")
    from altdata import rates_shape                             # noqa: PLC0415
    from daily_cascade import consistency                       # noqa: PLC0415
    check(rates_shape.ten_year_legs() == (("fred.yield_10y", "FRED"),
                                         ("yfinance.mkt_tnx", "Yahoo Finance"))
          and consistency.ALIASES["y10"] == ("y10", "yfinance.mkt_tnx", "fred.yield_10y")
          and consistency.ALIASES["y30"] == ("y30", "yfinance.mkt_tyx", "fred.yield_30y"),
          "the rates shape's legs and the consistency aliases are as they were")
    from daily_cascade import weekly_sections as ws              # noqa: PLC0415
    tt = ws.tape_table({"instruments": []})
    check("break_labels" not in tt["table"], "unswitched, the tape table carries no new field")


def group_b() -> None:
    head("B. A SWITCH")
    with Using(switched("us_yields")):
        check(ps.key("us_yields", "y10") == "fred.yield_10y"
              and ps.resolve("price:us_yields.y30") == "fred.yield_30y"
              and ps.key("dollar_index", "dxy") == "yfinance.mkt_dxy",
              "a switched family resolves to FRED; the other is untouched")
        lab = ps.break_label("us_yields")
        check(lab and lab.startswith("series change 2026-11-23: FRED's constant-maturity")
              and lab.endswith("not spliced"), f"the label carries the date ({lab})")
        labs = ps.labels_for(["yfinance.mkt_tnx", "fred.yield_30y", "fred.yield_10y"])
        check(labs == [lab], "a block printing both yields owes the label once")
        from daily_cascade import weekly_sections as ws          # noqa: PLC0415
        from daily_cascade import stack_render as sr             # noqa: PLC0415
        tt = ws.tape_table({"instruments": []})
        check(tt["table"].get("break_labels") == [lab],
              "the tape table carries the label")
        html = sr._table({"columns": ["Market", "Last"], "rows": [["10-year", "4.20%"]],  # noqa: SLF001
                          "break_labels": [lab]})
        check(html.index("4.20%") < html.index("series change") and html.count("series change") == 1,
              "it prints once, beneath the table holding the first figure")
        segs = ps.segments("us_yields", "y10")
        check([s["key"] for s in segs] == ["yfinance.mkt_tnx", "fred.yield_10y"]
              and segs[0]["to"] == segs[1]["from"] == "2026-11-23",
              "history: the old key up to the switch, the new key from it")
    check(ps.break_label("us_yields") is None, "back on yfinance, no label")


def group_c() -> None:
    head("C. NO HARD CODE")
    rx = re.compile("|".join(re.escape(k) for k in OLD))
    hits = []
    for d in ("daily_cascade", "monthly_macro", "altdata", "config"):
        for f in (REPO / d).rglob("*"):
            if f.suffix not in (".py", ".yaml", ".sh") or "__pycache__" in f.parts:
                continue
            rel = f.relative_to(REPO).as_posix()
            if rel in EXEMPT:
                continue
            for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{rel}:{n}")
    check(not hits, f"no reader names the three keys outside the exemptions ({hits[:6]})")
    check(all((REPO / p).exists() for p in EXEMPT),
          f"each exemption is a real file: {sorted(EXEMPT)}")


def group_d() -> None:
    head("D. NO SPLICE")
    old = [("2026-11-18", 99.1), ("2026-11-19", 99.3), ("2026-11-20", 99.0),
           ("2026-11-23", 98.9)]
    new = [("2026-11-19", 121.0), ("2026-11-20", 121.2), ("2026-11-23", 121.1),
           ("2026-11-24", 121.4)]
    sp = ps.split_points(old, new, "2026-11-23")
    check(len(sp["series"]) == 2 and sp["break"] == "2026-11-23"
          and all(d < "2026-11-23" for d, _ in sp["series"][0])
          and all(d >= "2026-11-23" for d, _ in sp["series"][1]),
          "across a switch: two series, the old before the break, the new from it")
    check(ps.split_points(old, new, None) == {"series": [old], "break": None},
          "unswitched: the one series as it was")
    import matplotlib                                           # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt                             # noqa: PLC0415
    fig, ax = plt.subplots()
    drawn = ps.plot_split(ax, sp, ("DXY", "Broad dollar"))
    xs = [[str(x) for x in ln.get_xdata()] for ln in drawn]
    check(len(drawn) == 2 and not any(any(x < "2026-11-23" for x in a) and
                                      any(x >= "2026-11-23" for x in a) for a in xs)
          and any(ln.get_linestyle() == "--" for ln in ax.lines),
          "the chart draws two lines and a dashed break; no line crosses the break")
    plt.close(fig)
    with Using(switched("dollar_index")):
        check(ps.switch_date_of("yfinance.mkt_dxy") == "2026-11-23"
              and ps.switch_date_of("yfinance.mkt_tnx") is None,
              "a chart leg knows its family's switch date, and only its own")


def group_e() -> None:
    head("E. PINS AND PAIRS")
    with Using(switched("dollar_index")):
        check(ps.resolve("price:dollar_index.dxy@yfinance") == "yfinance.mkt_dxy"
              and ps.resolve("price:dollar_index.dxy") == "fred.dxy",
              "switched, a pinned reference keeps Yahoo's key; the plain one moves")
    import yaml                                                 # noqa: PLC0415
    dq = yaml.safe_load((REPO / "config" / "data_quality.yaml").read_text(encoding="utf-8"))
    ip = dq.get("inactive_pairs_fred") or []
    resolved = [(ps.resolve(p["a"]), ps.resolve(p["b"])) for p in ip]
    active = {(p.get("a"), p.get("b")) for p in (dq.get("pairs") or {}).get("list") or []}
    check(len(ip) == 3 and all(p["active"] is False and "measured on the overlap" in p["tolerance"]
                               for p in ip)
          and resolved == [("yfinance.mkt_dxy", "fred.dxy"),
                           ("yfinance.mkt_tnx", "fred.yield_10y"),
                           ("yfinance.mkt_tyx", "fred.yield_30y")]
          and not any(str(a).startswith("price:") for a, _ in active),
          "the three inactive pairs resolve, tolerance to be measured, none in the active list")
    ie = dq.get("inactive_pairs_edgar") or []
    kp = [p for p in ie if p.get("kind") != "events"]
    check(len(kp) == 40 and len(ie) == 41 and all(p["active"] is False for p in ie)
          and all(ps.resolve(p["a"]).startswith("yfinance.fund_")
                  and ps.resolve(p["b"]).startswith("edgar.fund_") for p in kp)
          and all("measured on the overlap" in p["tolerance"] for p in ie),
          "A102's 41 inactive pairs: 40 company-quarter pairs resolve Yahoo against EDGAR, "
          "one events pair; none active")


FUND_EXEMPT = {
    "altdata/sources/fundamentals.py": "the writer of the keys",
    "altdata/sources/edgar_xbrl.py": "derives its twins' names from the writer's",
    "config/price_sources.yaml": "the switch itself",
}


def group_f() -> None:
    head("F. FUNDAMENTALS (A102)")
    from altdata.sources import edgar_xbrl, fundamentals         # noqa: PLC0415
    mem = ps.config()["families"]["fundamentals"]["members"]
    check(len(mem) == 40 and sorted(m["yfinance"] for m in mem.values()) == sorted(fundamentals.KEYS)
          and sorted(m["edgar"] for m in mem.values()) == sorted(edgar_xbrl.FUND_KEYS),
          "40 members, Yahoo's keys and their EDGAR twins, member for member")
    from altdata import ai_fcf, narratives                       # noqa: PLC0415
    check(ai_fcf._key("AMZN", "capex") == "yfinance.fund_amzn_capex"   # noqa: SLF001
          and ai_fcf._key("MU", "inventory") == "yfinance.fund_mu_inventory",  # noqa: SLF001
          "the AI FCF panel reads Yahoo's keys by default, as before")
    io = next((v.get("implied_outcome") for v in
               (narratives.load_config().get("narratives") or {}).values()
               if isinstance(v, dict) and "_capex" in str(v.get("implied_outcome"))), {}) or {}
    check(io.get("metrics") == ["yfinance.fund_amzn_capex", "yfinance.fund_googl_capex",
                                "yfinance.fund_msft_capex", "yfinance.fund_meta_capex"],
          f"the capex story's metrics resolve to the keys it named before ({io.get('metrics')})")
    with Using(switched("fundamentals", to="edgar")):
        check(ai_fcf._key("AMZN", "capex") == "edgar.fund_amzn_capex",   # noqa: SLF001
              "switched, the AI FCF panel reads EDGAR's key")
        lab = ps.break_label("fundamentals")
        check(bool(lab) and lab.startswith("series change 2026-11-23: EDGAR's filed XBRL")
              and "leases excluded" in lab and lab.endswith("not spliced"),
              f"the label names the definitional change ({(lab or '')[:70]}...)")
    rx = re.compile(r"yfinance\.fund_")
    hits = []
    for d in ("daily_cascade", "monthly_macro", "altdata", "config", "alpha"):
        for f in (REPO / d).rglob("*"):
            if f.suffix not in (".py", ".yaml", ".sh") or "__pycache__" in f.parts:
                continue
            rel = f.relative_to(REPO).as_posix()
            if rel in FUND_EXEMPT:
                continue
            for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{rel}:{n}")
    check(not hits, f"no reader names a yfinance.fund_* key outside the exemptions ({hits[:6]})")
    check(all((REPO / p).exists() for p in FUND_EXEMPT),
          f"each exemption is a real file: {sorted(FUND_EXEMPT)}")


def _event_fixture(path: str) -> None:
    from altdata import events as ev                             # noqa: PLC0415
    E = ev.Event
    with ev.EventStore(path) as st:
        st.write_many([
            E("earnings", "2026-10-30T20:05:00Z", "yfinance", "AAPL reported EPS 1.6",
              entities=["AAPL"], key="y1", payload={"symbol": "AAPL", "reported_eps": 1.6}),
            E("earnings", "2026-10-30T20:05:00Z", "sec_edgar", "AAPL reported EPS 1.61",
              entities=["AAPL"], key="e1", payload={"symbol": "AAPL", "reported_eps": 1.61}),
            E("earnings", "2026-12-01T21:00:00Z", "yfinance", "ORCL reported EPS 1.4",
              entities=["ORCL"], key="y2", payload={"symbol": "ORCL", "reported_eps": 1.4}),
            E("earnings", "2026-12-01T21:00:00Z", "sec_edgar", "ORCL reported EPS 1.41",
              entities=["ORCL"], key="e2", payload={"symbol": "ORCL", "reported_eps": 1.41}),
            E("scheduled", "2027-01-29T21:00:00Z", "yfinance", "AAPL earnings (confirmed)",
              entities=["AAPL"], key="c1", payload={"kind": "earnings", "symbol": "AAPL"}),
            E("earnings", "2026-10-29T20:00:00Z", "fixture", "MSFT reported EPS 3.1",
              entities=["MSFT"], key="f1", payload={"symbol": "MSFT", "reported_eps": 3.1}),
            E("filing", "2026-10-30T20:05:00Z", "sec_edgar", "AAPL 8-K",
              entities=["AAPL"], key="0000320193-26-000001", payload={"form": "8-K"}),
        ], available_at="2026-10-01T00:00:00Z")


def group_g() -> None:
    head("G. EARNINGS ROWS (A102)")
    import sqlite3                                               # noqa: PLC0415
    import gate_tmp                                              # noqa: PLC0415
    from altdata import events as ev                             # noqa: PLC0415
    tmp = gate_tmp.mkdtemp("a102_ev_")
    path = str(Path(tmp) / "ev.db")
    _event_fixture(path)
    cut = "2027-02-01T00:00:00Z"

    def seen() -> tuple:
        with ev.EventStore(path) as st:
            past = {(r["source"], r["title"]) for r in st.since("2026-01-01", as_of=cut)}
            ahead = {(r["source"], r["title"])
                     for r in st.calendar("2027-01-01", "2027-02-28", as_of=cut)}
        return past, ahead

    past, ahead = seen()
    check(("sec_edgar", "AAPL reported EPS 1.61") not in past
          and ("yfinance", "AAPL reported EPS 1.6") in past
          and ("fixture", "MSFT reported EPS 3.1") in past
          and ("sec_edgar", "AAPL 8-K") in past
          and ("yfinance", "AAPL earnings (confirmed)") in ahead,
          "unswitched: EDGAR's earnings rows are invisible to since() and calendar(); "
          "Yahoo's, a fixture's and EDGAR's filings are read as before")
    con = sqlite3.connect(path)
    sql, prm = ps.events_clause()
    n_all = con.execute("SELECT COUNT(*) FROM events WHERE type='earnings'").fetchone()[0]
    n_ok = con.execute("SELECT COUNT(*) FROM events WHERE type='earnings'" + sql, prm).fetchone()[0]
    rows = [dict(zip(("type", "source", "observed_at", "payload"), r)) for r in
            con.execute("SELECT type, source, observed_at, payload FROM events")]
    check(n_all == 5 and n_ok == 3,
          f"a direct SQL read with the clause: {n_ok} of {n_all} earnings rows")
    check(sum(ps.event_ok(r) for r in rows) == 5,
          "event_ok() mirrors the SQL row for row (3 earnings, the forward date, the filing)")
    from daily_cascade import opening_setup                      # noqa: PLC0415
    reps = opening_setup.reactions(con, "AAPL", "2027-01-01", cut)
    check(len(reps) == 1, f"the Ahead's reactions read carries the clause ({len(reps)} AAPL report)")
    with Using(switched("earnings_dates", to="edgar")):
        past, ahead = seen()
        check(("yfinance", "AAPL reported EPS 1.6") in past
              and ("sec_edgar", "AAPL reported EPS 1.61") not in past
              and ("sec_edgar", "ORCL reported EPS 1.41") in past
              and ("yfinance", "ORCL reported EPS 1.4") not in past
              and not ahead and ("fixture", "MSFT reported EPS 3.1") in past,
              "switched on 2026-11-23: Yahoo's history before, EDGAR's from it, never "
              "both; no forward date")
        sql, prm = ps.events_clause()
        n_ok = con.execute("SELECT COUNT(*) FROM events WHERE type='earnings'" + sql,
                           prm).fetchone()[0]
        check(n_ok == 3 and sum(ps.event_ok(r) for r in rows) == 4,
              "the direct SQL clause and event_ok() agree, switched")
        gap = ps.gap("earnings_dates", "next_date")
        check(gap == "next report date: not tracked (no keyless source)"
              and ps.gap("earnings_dates", "consensus").startswith("surprise: not tracked")
              and ps.gap("earnings_dates", "history") is None,
              f"the forward-date gap line ({gap})")
        from daily_cascade import ahead as ah                    # noqa: PLC0415
        b = ah.build({"window": ["2026-11-23", "2026-11-28"], "rows": []},
                     {"week_ending": "2026-11-21"}, None, "2026-11-22T10:00:00Z", cfg={})
        check(f"Earnings: {gap}." in b["notes"], "the Weekly's Ahead prints it once, in its notes")
    con.close()
    check(ps.gap("earnings_dates", "next_date") is None, "unswitched, no gap line")
    from daily_cascade import ahead as ah                        # noqa: PLC0415
    b = ah.build({"window": ["2026-11-23", "2026-11-28"], "rows": []},
                 {"week_ending": "2026-11-21"}, None, "2026-11-22T10:00:00Z", cfg={})
    check(not any(str(n).startswith("Earnings:") for n in b["notes"]),
          "unswitched, the Ahead's notes are as they were")
    rx = re.compile(r"type\s*=\s*'earnings'|type='earnings'")
    bare = []
    for d in ("daily_cascade", "monthly_macro", "altdata", "alpha"):
        for f in (REPO / d).rglob("*.py"):
            if "__pycache__" in f.parts:
                continue
            src = f.read_text(encoding="utf-8", errors="replace")
            if rx.search(src) and "events_clause" not in src:
                bare.append(f.relative_to(REPO).as_posix())
    check(not bare, f"every module reading the earnings rows by SQL applies the clause ({bare})")


def _facts() -> dict:
    """A recorded company-facts response, synthetic, in AMZN's shape."""
    def f(start, end, val, accn, filed):
        d = {"end": end, "val": val, "accn": accn, "filed": filed}
        if start:
            d["start"] = start
        return d

    def usd(*fs):
        return {"units": {"USD": list(fs)}}
    return {"cik": 1018724, "facts": {"us-gaap": {
        "NetCashProvidedByUsedInOperatingActivities": usd(
            f("2025-01-01", "2025-03-31", 100.0, "A1", "2025-05-01"),
            f("2025-01-01", "2025-06-30", 250.0, "A2", "2025-08-01"),
            f("2025-01-01", "2025-03-31", 110.0, "A2", "2025-08-01"),   # restated in the next 10-Q
            f("2025-01-01", "2025-09-30", 450.0, "A3", "2025-10-31"),
            f("2025-01-01", "2025-12-31", 700.0, "A4", "2026-02-06"),   # not in the index
            f("2017-01-01", "2017-03-31", 9.0, "A0", "2017-04-28")),    # before quarters_from
        "PaymentsToAcquireProductiveAssets": usd(
            f("2025-01-01", "2025-03-31", 40.0, "A1", "2025-05-01")),
        "PaymentsToAcquirePropertyPlantAndEquipment": usd(),
        "LongTermDebt": usd(f(None, "2025-03-31", 500.0, "A1", "2025-05-01")),
        "CashAndCashEquivalentsAtCarryingValue": usd(
            f(None, "2025-03-31", 200.0, "A1", "2025-05-01")),
        "InventoryNet": usd(f(None, "2025-03-31", 80.0, "A1", "2025-05-01")),
        "CostOfRevenue": usd(f("2025-01-01", "2025-03-31", 61.0, "A1", "2025-05-01")),
        "CostOfGoodsAndServicesSold": usd(f("2025-01-01", "2025-03-31", 60.0, "A1", "2025-05-01")),
        "EarningsPerShareDiluted": {"units": {"USD/shares": [
            f("2025-01-01", "2025-03-31", 1.25, "A1", "2025-05-01")]}},
    }}}


def _subs() -> dict:
    return {"filings": {"recent": {
        "accessionNumber": ["E1", "A1", "X5", "A2", "A3", "E4", "A4b", "E9"],
        "form": ["8-K", "10-Q", "8-K", "10-Q", "10-Q", "8-K", "10-K", "8-K"],
        "items": ["2.02,9.01", "", "5.02", "", "", "2.02,9.01", "", "2.02"],
        "reportDate": ["", "2025-03-31", "", "2025-06-30", "2025-09-30", "", "2025-12-31", ""],
        "acceptanceDateTime": ["2025-04-30T20:05:00.000Z", "2025-05-01T20:00:00.000Z",
                               "2025-06-02T12:00:00.000Z", "2025-08-01T20:00:00.000Z",
                               "2025-10-31T20:00:00.000Z", "2026-02-05T21:00:00.000Z",
                               "2026-02-06T21:00:00.000Z", "2026-04-29T20:05:00.000Z"]}}}


def group_h() -> None:
    head("H. THE EDGAR WRITER (A102)")
    import yaml                                                  # noqa: PLC0415
    from altdata import observations                             # noqa: PLC0415
    from altdata.sources import edgar_xbrl as x                  # noqa: PLC0415
    cfgall = yaml.safe_load((REPO / "config" / "edgar_xbrl.yaml").read_text(encoding="utf-8"))
    fc, ec = cfgall["fundamentals"], cfgall["earnings"]
    fields = fc["fields"]
    ntags = sum(len(s.get("tags") or []) + len(s.get("debt") or []) + len(s.get("cash") or [])
                for s in fields.values())
    check(set(fields) == set(x.FUND_FIELDS) and all(s.get("cite") for s in fields.values())
          and ntags == 10 and len(fc["filers"]) == 9,
          f"the tag table: 5 fields, {ntags} us-gaap tags, each field cited, nine filers")
    check(fc["enabled"] is False and ec["enabled"] is False
          and 0 < float(fc["request_pause_s"]) and 1 / float(fc["request_pause_s"]) < 10,
          "both parts ship switched off; the pacing is under the SEC's ten a second")
    C = observations.canonical_instant
    acc = x.acceptance_map(_subs())
    rows = x.fundamentals_rows("AMZN", _facts(), acc, fc)
    by: dict = {}
    for r in rows:
        by.setdefault(r["registry_key"], []).append(
            (r["observed_at"], r["value"], r["available_at"], r["availability_kind"]))
    ocf = by.get("edgar.fund_amzn_operating_cash_flow") or []
    check(ocf[:2] == [("2025-03-31", 100.0, C("2025-05-01T20:00:00.000Z"), "observed"),
                      ("2025-03-31", 110.0, C("2025-08-01T20:00:00.000Z"), "observed")],
          "a quarter filed as three months, at its acceptance; the restatement a vintage at its own")
    check(("2025-06-30", 140.0, C("2025-08-01T20:00:00.000Z"), "observed") in ocf
          and ("2025-09-30", 200.0, C("2025-10-31T20:00:00.000Z"), "observed") in ocf,
          "Q2 and Q3 from year-to-date less the previous year-to-date, at the later acceptance")
    q4 = [o for o in ocf if o[0] == "2025-12-31"]
    check(len(q4) == 1 and q4[0][1] == 250.0 and q4[0][3] == "reconstructed"
          and q4[0][2] == C("2026-02-07T04:59:59+00:00"),
          f"Q4 = the year less nine months; an accession not in the index takes its filed "
          f"day's end in ET, reconstructed ({q4})")
    check(not any(o[0] < "2019-01-01" for o in ocf), "nothing before quarters_from")
    check(by.get("edgar.fund_amzn_capex")
          == [("2025-03-31", -40.0, C("2025-05-01T20:00:00.000Z"), "observed")],
          "capex: the second tag fills where the first is empty; stored negative, as Yahoo publishes it")
    check([v for _e, v, _a, _k in by.get("edgar.fund_amzn_cogs") or []] == [60.0]
          and [v for _e, v, _a, _k in by.get("edgar.fund_amzn_net_debt") or []] == [300.0]
          and [v for _e, v, _a, _k in by.get("edgar.fund_amzn_inventory") or []] == [80.0],
          "cost of goods: the first tag wins; net debt is debt less cash; inventory as filed")
    check(not any(r["registry_key"] == "edgar.fund_meta_inventory"
                  for r in x.fundamentals_rows("META", _facts(), acc, fc)),
          "inventory only for the four names Yahoo carries it for")
    check({r["registry_key"] for r in rows} <= set(x.FUND_KEYS),
          "every row's key is a registered twin")
    ev = x.earnings_events("AMZN", _subs(), _facts(), ec)
    got = [(e.observed_at, a, e.payload["reported_eps"], e.payload["period_end"]) for a, e in ev]
    check(got == [(C("2025-04-30T20:05:00.000Z"), C("2025-05-01T20:00:00.000Z"), 1.25, "2025-03-31"),
                  (C("2026-02-05T21:00:00.000Z"), C("2026-02-06T21:00:00.000Z"), None, "2025-12-31")],
          "the 8-K item 2.02 acceptance is the report instant; available once the quarter's "
          "10-Q/10-K is accepted; an item-5.02 8-K is not a report")
    p0, p1 = ev[0][1].payload, ev[1][1].payload
    check(ev[0][1].type == "earnings" and ev[0][1].source == "sec_edgar"
          and p0["eps_estimate"] is None and p0["surprise_pct"] is None
          and "consensus was Yahoo's" in p0["consensus"]
          and p1["eps_note"] == "not filed as a quarter",
          "no consensus, so no surprise; a fourth quarter carries no EPS rather than a subtraction")
    check(not any(a.startswith("2026-04") or e.observed_at.startswith("2026-04") for a, e in ev),
          "a report whose quarter's 10-Q is not yet accepted is not written yet")
    import gate_tmp                                              # noqa: PLC0415
    from altdata import events as evm                            # noqa: PLC0415
    path = str(Path(gate_tmp.mkdtemp("a102_w_")) / "ev.db")
    with evm.EventStore(path) as st:
        w = x.write_earnings(ev, st)
        kinds = {r[0] for r in st.conn.execute("SELECT availability_kind FROM events")}
        avail = sorted(r[0] for r in st.conn.execute("SELECT available_at FROM events"))
        w2 = x.write_earnings(ev, st)
    check(w["inserted"] == 2 and w2["inserted"] == 0 and kinds == {"observed"}
          and avail == sorted(a for a, _e in ev),
          "written at each event's own acceptance, availability observed; a re-pull writes nothing")
    import time                                                  # noqa: PLC0415
    from unittest import mock                                    # noqa: PLC0415
    calls = []
    with mock.patch.object(x, "http_get_json",
                           lambda url, **k: calls.append(time.monotonic()) or {}):
        x._LAST_CALL[0] = 0.0                                    # noqa: SLF001
        for _ in range(3):
            x._sec_get("https://data.sec.gov/x", {}, 0.15)       # noqa: SLF001
    check(len(calls) == 3 and all(b - a >= 0.149 for a, b in zip(calls, calls[1:])),
          "the SEC caller is paced: no two requests closer than request_pause_s")
    with mock.patch.object(x.edgar, "contact", lambda: None):
        r = x.pull_a102("fundamentals", dry_run=True)
    check("not configured" in str(r),
          "without the SEC contact the command fetches nothing")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h):
        g()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
