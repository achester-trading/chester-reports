"""
Validation gate for T2.3 -- Weekly completeness (ruled 4 Oct 2026).

    python tools/validate_weekly_complete.py

On the Weekly gate's synthetic week and the stack gate's synthetic session, plus
this gate's own fixtures; a code gate never reads the live store and never opens a
socket.

  A REGISTRY     every new series has a registry entry with units and a family
                 from the declared vocabulary; ES=F is an intraday-only instrument
                 with the 23-hour session.
  B OVERNIGHT    overnight (prior close -> open) and intraday (open -> close)
                 returns from a fixture, the week compounded; the close's line.
  C PLUMBING     net liquidity with its week change, the H.4.1 legs in the right
                 units, SOFR less IORB, IG and CCC and CCC less BB, the week's
                 auctions, copper and gold/copper; the repo footnote replaced;
                 Global rates and FX with the Bund noted as not tracked.
  D VOLATILITY   six rows and the paragraph asked for; the daily move priced and
                 realized.
  E BREADTH      the sector table carries the week, one and three months, and the
                 count above the 50- and 200-day.
  F HEADER       "Changed since last Weekly" under the header before The read;
                 the reading time printed.
  G MOBILE       no table wider than six columns in the Weekly or the daily close;
                 every chart legible at 400 px (smallest text at least 8 px);
                 images scale to the width.
  H EARNINGS     in season by the stored dates: a confirmed date (or a reported
                 result) within seven days; the fixed windows only when no date is
                 stored; silent out of season; "no universe name reported", or a
                 reporter with beat/miss and the next day's reaction. The writer
                 marks a confirmed date.
  H2 CUTOFF      a --week-ending dry run reads as the scheduled run would: Sunday
                 05:00 ET after the week.
  I W7 AND THE RECORD  the overnight drawn from ES scaled by the basis; the
                 attention-log line.
  J AUDIT        the prose may quote the T2.3 tables: every unit-bearing cell,
                 quoted verbatim, passes the real numeral audit; a wrong unit
                 still fails (5 Oct: the first live render withheld three
                 sections because a cell was typed by its `rows` key).
  K BARS         the bars backfill stamps a bar at its close plus the delay and a
                 re-run moves the stamp earlier without a second row.
  L NOISE        yfinance's NumPy DeprecationWarnings are filtered at their source,
                 proven in a fresh interpreter under the real import order (T2.6).
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

TD = gate_mkdtemp("validate_weekly_complete_")
os.environ.setdefault("CHESTER_DB", str(Path(TD) / "default.db"))

LINE = "=" * 78
PASS = FAIL = 0


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def tables(html: str) -> list[int]:
    """The column count of every table's header row in an HTML edition."""
    out = []
    for t in re.findall(r"<table.*?</table>", html, re.S):
        first = re.search(r"<tr>(.*?)</tr>", t, re.S)
        out.append(len(re.findall(r"<t[hd][ >]", first.group(1))) if first else 0)
    return out


def seed_t23(db: str, sessions: list[str]) -> None:
    from altdata import observations, bars as bars_mod, events as ev_mod
    rows = []

    def put(key, d, v, inst=None):
        rows.append({"registry_key": key, "instrument": inst, "observed_at": d,
                     "available_at": f"{d}T21:00:00+00:00", "value": v,
                     "source": "fixture"})
    then = sessions[0]
    prev = (dt.date.fromisoformat(then) - dt.timedelta(days=3)).isoformat()
    for d, scale in ((prev, 1.0), (sessions[-1], 1.0)):
        last = d == sessions[-1]
        put("calc.net_liquidity", d, 5.87e12 if last else 5.80e12)
        put("fred.bank_reserves", d, 3200000.0 if last else 3150000.0)
        put("fred.tga", d, 830296.0 if last else 800000.0)
        put("fred.rrp", d, 120.0 if last else 140.0)
        put("fred.sofr", d, 4.40 if last else 4.36)
        put("fred.iorb", d, 4.40 if last else 4.40)
        put("fred.ig_oas", d, 0.95 if last else 0.92)
        put("fred.ccc_oas", d, 7.10 if last else 6.80)
        put("fred.bb_oas", d, 1.90 if last else 1.85)
        put("yfinance.mkt_copper_front", d, 4.50 if last else 4.40)
        put("yfinance.mkt_usdjpy", d, 150.0 if last else 148.5)
        put("yfinance.mkt_eurusd", d, 1.10 if last else 1.11)
        put("yfinance.mkt_skew", d, 140.0)
        put("yfinance.mkt_move", d, 105.0)
        put("calc.vol_spy_realized_20d", d, 10.3)
        put("yfinance.mkt_vix", d, 15.6)
    put("auction.high_yield", sessions[2], 4.112, "Note:10-Year")
    put("auction.bid_to_cover", sessions[2], 2.51, "Note:10-Year")
    put("auction.dealer_share", sessions[2], 0.14, "Note:10-Year")
    # Earnings: JPM reports mid-week; its closes around the print.
    for d, v in ((sessions[1], 200.0), (sessions[2], 200.0), (sessions[3], 206.0)):
        put("yfinance.mkt_jpm", d, v)
    with observations.ObservationStore(db) as st:
        st.write_many(rows)
    with ev_mod.EventStore(db) as ev:
        ev.write_many([ev_mod.Event(
            type="earnings", observed_at=f"{sessions[2]}T12:00:00+00:00",
            source="yfinance", title="JPM reported",
            payload={"symbol": "JPM", "reported_eps": 4.50, "eps_estimate": 4.20})],
            available_at=f"{sessions[2]}T13:00:00+00:00")
    # ES overnight bars for the last two sessions.
    with bars_mod.BarStore(db, create=True) as bst:
        bs = []
        for s in sessions[-2:]:
            a, _, n = bars_mod.session_window("es", s)
            t0 = dt.datetime.fromisoformat(a)
            for k in range(n):
                px = 7000.0 + (k % 7)
                bs.append({"instrument": "es", "symbol": "ES=F", "interval": "5m",
                           "observed_at": (t0 + dt.timedelta(minutes=5 * k)).isoformat(),
                           "open": px, "high": px + 1, "low": px - 1, "close": px,
                           "volume": 10.0, "available_at": f"{s}T21:00:00+00:00"})
        bst.write_many(bs)


def main() -> int:
    import validate_weekly_stack as vws
    import validate_weekly_edits as vwe
    from altdata import config, derived, labels, bars as bars_mod
    from daily_cascade import (charts as charts_mod, stack as stack_mod,
                               weekly_sections as wsec, weekly_stack as ws)
    import yaml
    config.COMPUTED_DIR = str(Path(TD) / "computed")

    # --- A. REGISTRY --------------------------------------------------------
    print(f"\n{LINE}\nA. EVERY NEW SERIES IS REGISTERED, WITH UNITS AND A FAMILY\n{LINE}")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    fams = reg.get("families") or {}
    vocab = set((reg.get("vocabularies") or {}).get("family") or [])
    new = ["fred.sofr", "fred.iorb", "yfinance.mkt_copper_front",
           "yfinance.mkt_usdjpy", "yfinance.mkt_eurusd"]
    for k in new:
        e = derived.registry_entry(k)
        check(e and e.get("units") and fams.get(k) in vocab,
              f"{k}: units {e.get('units') if e else None!r}, family {fams.get(k)!r}")
    check(vocab == {"price", "rate", "spread", "release", "quantity", "conditions",
                    "ratio"}, "the family vocabulary is the metric-lenses brief's")
    es = [t for t in bars_mod.intraday_instruments() if t["id"] == "es"]
    w = bars_mod.session_window("es", "2026-10-05")
    check(es and es[0]["bars"] == "ES=F" and w[2] == 276
          and w[0] == "2026-10-04T22:00:00+00:00"
          and not any(t["id"] == "es" for t in bars_mod.tape()),
          "ES=F is an intraday-only instrument with the 23-hour session (276 bars, "
          "18:00 ET the evening before)")

    # --- the fixture Weekly, with this gate's seed ----------------------------
    db = str(Path(TD) / "weekly.db")
    arch = str(Path(TD) / "reports")
    logp = Path(TD) / "attention-log.md"
    logp.write_text("| date | kind | minutes | note |\n|---|---|---|---|\n", encoding="utf-8")
    seeded = vws.seed(db)
    p = vws.payload(seeded)
    sessions = p.get("sessions_in_week") or vws.weekdays(vws.ENDING, 5)
    vwe.seed_extras(db, vws.ENDING, sessions)
    seed_t23(db, sessions)
    calls: list = []
    out = ws.produce(p, archive_dir=arch, client=vws.client(calls), db_path=db,
                     log_path=logp)
    ed = out["edition"]
    sec = {s["id"]: s for s in ed["sections"]}
    html = out["html_email"]

    # --- B. OVERNIGHT -------------------------------------------------------
    print(f"\n{LINE}\nB. OVERNIGHT AGAINST THE CASH SESSION\n{LINE}")
    from altdata import observations
    with observations.ObservationStore(db) as st:
        oi = wsec.overnight_intraday(st, sessions, vws.ENDING, vws.AS_OF)
    ok = True
    from altdata import levels
    with observations.ObservationStore(db) as st:
        rows, _ = levels.daily_bars(levels.tape_spec("spy"), vws.ENDING, vws.AS_OF, st)
    byd = {str(r["observed_at"])[:10]: r for r in rows}
    allc = [str(r["observed_at"])[:10] for r in rows]
    for r in oi["rows"]:
        i = allc.index(r["day"])
        pr, o, c = rows[i - 1]["close"], byd[r["day"]]["open"], byd[r["day"]]["close"]
        ok &= (abs(r["overnight_pct"] - round(100 * (o / pr - 1), 2)) < 1e-9
               and abs(r["intraday_pct"] - round(100 * (c / o - 1), 2)) < 1e-9)
    tot = 1.0
    for r in oi["rows"]:
        tot *= 1 + r["overnight_pct"] / 100
    check(oi["rows"] and ok and abs(oi["totals"]["overnight_pct"] - round(100 * (tot - 1), 2))
          < 1e-9, f"overnight and intraday returns from the stored OHLC, the week "
                  f"compounded ({len(oi['rows'])} sessions, {oi['totals']})")
    tsubs = {ss["title"]: ss for ss in sec["tape"]["subsections"]}
    check("SPY overnight against the cash session" in tsubs
          and tsubs["SPY overnight against the cash session"]["table"]["rows"][-1][0]
          == "The week" and tsubs["SPY overnight against the cash session"]["table"]
          ["rows"][-1][3] != "—", "the tape carries the table with the week's totals, "
          "close to close included")
    book = {"instruments": [{"id": "spy", "ohlc": {"open": 701.0},
                             "frame": {"last": 700.0},
                             "levels": [{"type": "prior_close", "value": 697.0}]}]}
    line = wsec.overnight_line(book)
    check(line and "the overnight carried +0.57% of the day's +0.43%" in line,
          f"the daily close's line ({line})")
    import inspect
    check("tape:overnight" in inspect.getsource(stack_mod.tape_section),
          "the close's tape section carries the line")

    # --- C. PLUMBING --------------------------------------------------------
    print(f"\n{LINE}\nC. PLUMBING, MADE PLUMBING\n{LINE}")
    prow = {r[0]: r for r in sec["plumbing"]["table"]["rows"]}
    check(prow.get("Net liquidity (Fed balance sheet less TGA and RRP)", [None, None])[1]
          == "$5.87tn" and prow["Net liquidity (Fed balance sheet less TGA and RRP)"][2]
          == "+$70bn", f"net liquidity in dollars, with its week change "
                      f"({prow.get('Net liquidity (Fed balance sheet less TGA and RRP)')})")
    check(prow.get("Treasury General Account (H.4.1)", [0, 0])[1] == "$830bn"
          and prow.get("Bank reserves (H.4.1)", [0, 0])[1] == "$3.20tn",
          f"the H.4.1 legs in their own units: TGA millions, reserves billions ({[r for r in sec['plumbing']['table']['rows'] if 'H.4.1' in r[0] or 'auction' in r[0].lower()]})")
    sp = prow.get("SOFR less IORB (funding pressure when above zero)")
    check(sp and sp[1] == "+0 bp" and sp[2] == "+4 bp",
          f"SOFR less IORB in basis points, with its week change ({sp})")
    check(not any("repo-market" in x for x in sec["plumbing"]["not_tracked"]),
          "the repo footnote is replaced by SOFR against IORB")
    cb = prow.get("CCC less BB (stress inside high yield)")
    check(cb and cb[1] == "520 bp" and cb[2] == "+25 bp" and "CCC OAS" in prow
          and "Investment-grade OAS" in prow, f"IG, CCC and CCC less BB ({cb})")
    auc = [r for r in sec["plumbing"]["table"]["rows"] if "auction" in r[0]]
    with observations.ObservationStore(db) as st:
        quiet = wsec.plumbing_rows(st, "2026-08-08T09:00:00+00:00",
                                   "2026-08-01T09:00:00+00:00")
    check(any(r[:2] == ["Treasury coupon auctions this week", "none held"]
              for r in quiet["rows"]), "a week without a coupon auction says so")
    check(auc and "bid-to-cover 2.51" in auc[0][1] and "dealers took 14%" in auc[0][2]
          and auc[0][3] == "tail not stored", f"the week's auctions ({auc[:1]})")
    check("Copper, front future ($/lb; a growth gauge)" in prow
          and "Gold over copper (rises when growth fears rise)" in prow,
          "copper and gold/copper as growth rows")
    fx = next(ss for ss in sec["plumbing"]["subsections"]
              if ss["title"] == "Global rates and FX")
    check([r[0] for r in fx["table"]["rows"]][:2] == ["USD/JPY (yen per dollar)",
                                                       "EUR/USD (dollars per euro)"]
          and any("Bund" in x and "ECB" in x for x in fx["not_tracked"]),
          "Global rates and FX: the yen and the euro, the Bund not yet tracked with "
          "the ECB named as the source to add")

    # --- D. VOLATILITY ------------------------------------------------------
    print(f"\n{LINE}\nD. VOLATILITY\n{LINE}")
    vol = next(ss for ss in sec["mechanics"]["subsections"] if ss["title"] == "Volatility")
    check(len(vol["table"]["rows"]) <= 6 and vol["table"]["rows"],
          f"a table of at most six rows ({len(vol['table']['rows'])})")
    # T2.5 item 2: one paragraph per section; the volatility read sits inside it.
    mcalls = [c for c in calls if "THE SECTION: Mechanics." in c]
    check(mcalls and "ONE paragraph" in mcalls[0] and "[A]" not in mcalls[0]
          and "THE VOLATILITY READ, inside the one paragraph" in mcalls[0]
          and "Daily move priced, and realized" in mcalls[0],
          "Mechanics: ONE paragraph, the volatility read stated from the daily move")

    # --- E. BREADTH ---------------------------------------------------------
    print(f"\n{LINE}\nE. LEADERSHIP AND BREADTH\n{LINE}")
    srt = sec["positioning"]["subsections"][0]
    check(srt["table"]["columns"] == ["Sector or pair", "Week", "One month",
                                      "Three months"]
          and any(" (XL" in r[0] for r in srt["table"]["rows"]),
          "the sector table: the week, one month, three months; names from the labels")
    check(not srt.get("lines") or re.match(
        r"Sectors above their 50-day average: \d+ of \d+; above their 200-day: \d+ of "
        r"\d+\.", srt["lines"][0]), f"the 50/200-day count ({srt.get('lines')})")

    # --- F. HEADER ----------------------------------------------------------
    print(f"\n{LINE}\nF. THE HEADER\n{LINE}")
    i_changed = html.find("Changed since last Weekly")
    i_read = html.find("&middot; The read")
    check(0 < i_changed < i_read and ed.get("changed_since"),
          f"'Changed since last Weekly' under the header, before The read "
          f"({ed.get('changed_since')[:2]})")
    m = re.search(r"about\s+([\d.]+) minutes? to read", html)
    check(m and abs(float(m.group(1)) - wsec.reading_minutes(ed, ed["chart_count"]))
          < 0.05, f"the reading time (prose / 250 + 20 s a chart): {m and m.group(1)}")

    # --- G. MOBILE ----------------------------------------------------------
    print(f"\n{LINE}\nG. THE MOBILE RULE\n{LINE}")
    tw = tables(html)
    check(tw and max(tw) <= 6, f"the Weekly: no table wider than six columns "
                               f"(widest {max(tw) if tw else None})")
    import validate_stack as vst
    from daily_cascade import stack_close
    sdb = str(Path(TD) / "close.db")
    vst.SESSION = vws.ENDING
    sd = vst.seed(sdb)
    sp_ = vst.payload(sd["market_state"])
    co = stack_close.produce(sp_, archive_dir=str(Path(TD) / "close"), dry_run=True,
                             client=vst.client({}, []), db_path=sdb)
    stack_part = co["html_email"]
    tw2 = tables(stack_part)
    check(tw2 and max(tw2) <= 6, f"the daily close, detail tables included: no table wider than six "
                                 f"columns (widest {max(tw2) if tw2 else None})")
    imgs = re.findall(r"<img[^>]*>", html)
    check(imgs and all("max-width:100%" in i for i in imgs),
          f"every chart image scales to the width ({len(imgs)} images)")
    small = {k: c.get("min_px_at_400") for k, c in out["charts"].items()
             if not c.get("unavailable")}
    check(small and all(v >= charts_mod.MIN_PX_AT_400 for v in small.values()),
          f"every chart legible at 400 px: smallest text {min(small.values())} px "
          f"(floor {charts_mod.MIN_PX_AT_400})")

    # --- H. EARNINGS --------------------------------------------------------
    print(f"\n{LINE}\nH. EARNINGS, IN SEASON BY THE STORED DATES\n{LINE}")
    from altdata import events as ev_mod

    def season_db(name, evs):
        path = str(Path(TD) / name)
        with observations.ObservationStore(path):
            pass
        with ev_mod.EventStore(path) as ev:
            for e, avail in evs:
                ev.write_many([e], available_at=avail)
        return path

    def sched(sym, day, confirmed):
        return ev_mod.Event(
            type="scheduled", observed_at=f"{day}T20:00:00+00:00", source="yfinance",
            title=f"{sym} earnings ({'confirmed' if confirmed else 'expected'})",
            entities=[sym], key=f"cal-{sym}-{day}-{confirmed}",
            payload={"kind": "earnings", "symbol": sym, "date_confirmed": confirmed})

    def block(path, ending):
        now = f"{(dt.date.fromisoformat(ending) + dt.timedelta(days=2)).isoformat()}" \
              f"T09:00:00+00:00"
        with observations.ObservationStore(path) as st:
            return (wsec.earnings_block(st, ending, now, ws.week_ago(now)),
                    wsec.earnings_season(st, ending, now))
    none_db = season_db("e_none.db", [])
    off, s_off = block(none_db, "2026-09-25")
    fall, s_fall = block(none_db, "2026-10-23")
    check(off is None and fall and fall["lines"] == ["No universe name reported this week."]
          and s_fall["basis"].startswith("fixed windows"),
          "no earnings date stored: the fixed windows decide (25 Sep out, 23 Oct in)")
    exp_db = season_db("e_expected.db", [(sched("MSFT", "2026-10-21", False),
                                          "2026-09-01T00:00:00+00:00")])
    e_blk, e_s = block(exp_db, "2026-10-16")
    check(e_blk is None and not e_s["in_season"],
          "an expected (unconfirmed) date does not open the season, even inside the "
          "fixed window")
    conf_db = season_db("e_confirmed.db", [
        (sched("MSFT", "2026-10-21", True), "2026-09-01T00:00:00+00:00"),
        (sched("AAPL", "2026-11-05", True), "2026-09-01T00:00:00+00:00")])
    c_blk, c_s = block(conf_db, "2026-10-16")
    far, f_s = block(conf_db, "2026-09-25")
    check(c_blk and c_blk["lines"] == ["No universe name reported this week."]
          and c_s["names"] == ["MSFT"],
          "a confirmed date within seven days opens it; no reporter yet: 'no universe "
          "name reported'")
    check(far is None and not f_s["in_season"],
          "a confirmed date more than seven days away does not (and the fixed window "
          "is not consulted while dates are stored)")
    late_db = season_db("e_late.db", [(sched("MSFT", "2026-10-21", False),
                                       "2026-09-01T00:00:00+00:00"),
                                      (sched("MSFT", "2026-10-21", True),
                                       "2026-10-20T00:00:00+00:00")])
    l_blk, _ = block(late_db, "2026-10-16")
    check(l_blk is None, "a date confirmed after the cutoff is not used before it")
    with observations.ObservationStore(db) as st:
        hit = wsec.earnings_block(st, sessions[-1], vws.AS_OF, ws.week_ago(vws.AS_OF))
    row = (hit or {}).get("table", {}).get("rows", [[]])[0] if hit else []
    check(row and row[0] == "JPM" and row[2] == "beat" and row[4] == "+3.00%",
          f"a reporter opens the season and prints: EPS against consensus, beat or "
          f"miss, the next day ({row})")
    import types
    from altdata.sources import earnings as earn_src

    class FakeTicker:
        def __init__(self, sym):
            self.calendar = {"Earnings Date": WHEN[sym], "Earnings Average": 1.0}

        def get_earnings_dates(self, limit=12):
            raise RuntimeError("no history in the fixture")
    WHEN = {"ONE": [dt.date(2026, 10, 21)],
            "TWO": [dt.date(2026, 10, 20), dt.date(2026, 10, 24)]}
    saved = sys.modules.get("yfinance")
    sys.modules["yfinance"] = types.SimpleNamespace(Ticker=FakeTicker)
    try:
        one, _ = earn_src.events_for("ONE")
        two, _ = earn_src.events_for("TWO")
    finally:
        if saved is not None:
            sys.modules["yfinance"] = saved
        else:
            sys.modules.pop("yfinance", None)
    check(one and one[0].payload["date_confirmed"] is True
          and one[0].title.endswith("(confirmed)")
          and two and two[0].payload["date_confirmed"] is False
          and two[0].title.endswith("(expected)")
          and one[0].content_hash != ev_mod.Event(
              type="scheduled", observed_at=one[0].observed_at, source="yfinance",
              title="ONE earnings (expected)", entities=["ONE"],
              key=f"earnings-cal-ONE-{one[0].observed_at[:10]}").content_hash,
          "the writer marks a single calendar date confirmed and a window expected; "
          "the confirmed date is its own row")

    # --- H2. THE DRY RUN'S CUTOFF -------------------------------------------
    print(f"\n{LINE}\nH2. A --week-ending DRY RUN READS AS THE SCHEDULED RUN WOULD\n{LINE}")
    from daily_cascade import weekly_payload as wp, weekly_report as wr
    check(wp.scheduled_run_utc("2026-10-02") == "2026-10-04T09:00:00+00:00"
          and wp.scheduled_run_utc("2026-01-02") == "2026-01-04T10:00:00+00:00"
          and wp.scheduled_run_utc("2026-10-09", "2026-10-06T12:00:00+00:00")
          == "2026-10-06T12:00:00+00:00",
          "the cutoff is Sunday 05:00 ET after the week (EDT and EST), never later "
          "than the real clock")
    src = inspect.getsource(wr.main)
    check("args.dry_run and args.week_ending and not args.as_of" in src
          and "args.as_of = payload_mod.scheduled_run_utc(args.week_ending)" in src,
          "weekly_report applies it to a --week-ending dry run without --as-of")

    # --- I. W7 AND THE RECORD -----------------------------------------------
    print(f"\n{LINE}\nI. W7 OVER 23 HOURS, AND THE RECORD\n{LINE}")
    w7 = out["charts"].get("W7") or {}
    check(not w7.get("unavailable") and w7.get("overnight_sessions") == 2
          and "scaled to SPY by each session's basis" in w7.get("caption", ""),
          f"W7 draws the overnight from ES scaled by the basis "
          f"({w7.get('overnight_sessions')} sessions)")
    check(ed["chart_count"] <= 11, f"the chart count is unchanged in kind "
                                   f"({ed['chart_count']} within the cap)")
    att = ws.read_attention_log()
    check(any(e["date"] == "2026-10-04" and e["minutes"] == 15 and "T2.3" in e["note"]
              for e in att), "the attention log carries the T2.3 line")

    # --- J. THE AUDIT READS A TABLE CELL'S OWN UNIT ---------------------------
    print(f"\n{LINE}\nJ. THE PROSE MAY QUOTE THE T2.3 TABLES (5 Oct, the first live render)\n{LINE}")
    from altdata import numeral_audit as na
    unit_re = re.compile(r"(%|\bbps?\b|\bpoints?\b|\bpts\b)")

    def quoted_cells(tbl):
        return [c for r in tbl["rows"] for c in r[1:]
                if isinstance(c, str) and unit_re.search(c)]
    probes = {
        "plumbing": sec["plumbing"]["table"],
        "tape": tsubs["SPY overnight against the cash session"]["table"],
        "mechanics": vol["table"],
    }
    for sid, tbl in probes.items():
        cells = quoted_cells(tbl)
        text = " ".join(f"The row read {c}." for c in cells)
        r = na.audit(text, sec[sid])
        check(cells and r.n_unmatched == 0,
              f"{sid}: every unit-bearing cell of its T2.3 table, quoted verbatim, "
              f"passes the real audit ({len(cells)} cells; {r.reason()[:120] if r.n_unmatched else 'clean'})")
    bp_cell = next(r[1] for r in sec["plumbing"]["table"]["rows"]
                   if r[0].startswith("CCC less BB"))
    wrong = bp_cell.replace(" bp", "%")
    check(na.audit(f"The spread read {wrong}.", sec["plumbing"]).n_unmatched >= 1,
          f"and the audit still refuses a wrong unit ({bp_cell!r} quoted as {wrong!r})")
    check(na.cell_types("2026-10-02") == [(2026.0, "count"), (10.0, "count"), (2.0, "count")]
          and na.cell_types("bid-to-cover 2.51") == [(2.51, "count")]
          and na.cell_types("+29k") == [(29000.0, "any")],
          "a cell with no unit word stays a count; a date keeps its date reading; a "
          "scaled figure carries its own")
    for c in ("29,000", "29k"):
        check(na.audit(f"Payrolls rose by {c}.", {"table": {"rows": [["Payrolls", "+29k"]]}}
                       ).n_unmatched == 0, f"payrolls printed +29k may be quoted as {c}")

    # --- K. THE BARS BACKFILL'S AVAILABILITY ------------------------------------
    print(f"\n{LINE}\nK. A BACKFILLED BAR IS KNOWN AT ITS CLOSE PLUS THE DELAY\n{LINE}")
    from altdata.sources import yfinance_source as yf_src
    bar = {"instrument": "spy", "symbol": "SPY", "interval": "5m", "open": 1.0,
           "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0}
    rows = [{**bar, "observed_at": "2026-10-02T13:30:00+00:00"},
            {**bar, "observed_at": "2026-10-02T19:55:00+00:00"},
            {**bar, "observed_at": "2026-10-02T20:10:00+00:00"}]
    kept, still_open = bars_mod.reconstruct_availability(rows, "2026-10-02T20:12:00+00:00")
    check(yf_src.RECONSTRUCTED_LATENCY_MINUTES == 20 and still_open == 1
          and [k["available_at"] for k in kept] == ["2026-10-02T13:55:00+00:00",
                                                    "2026-10-02T20:12:00+00:00"],
          f"close + 20 minutes, or the fetch if that came first; a bar still open at "
          f"the fetch is dropped ({[k['available_at'] for k in kept]}, {still_open} dropped)")
    rdb = str(Path(TD) / "restamp.db")
    first = {**bar, "observed_at": "2026-10-02T13:30:00+00:00",
             "available_at": "2026-10-05T23:40:00+00:00"}
    with bars_mod.BarStore(rdb, create=True) as bst:
        bst.write_many([first])
        n1 = bst.restamp_many([{**first, "available_at": "2026-10-02T13:55:00+00:00"}])
        n2 = bst.restamp_many([{**first, "available_at": "2026-10-03T00:00:00+00:00"}])
        got = bst.conn.execute("SELECT COUNT(*), MIN(available_at) FROM bars").fetchone()
    check(n1 == 1 and n2 == 0 and tuple(got) == (1, "2026-10-02T13:55:00+00:00"),
          f"a re-run moves a stored bar's availability earlier, never later, and never "
          f"writes a second row ({tuple(got)}, restamped {n1} then {n2})")
    import inspect as _inspect
    check("restamp_many" in _inspect.getsource(bars_mod.backfill)
          and "reconstruct_availability" in _inspect.getsource(bars_mod.backfill),
          "the backfill writes through both")

    # --- L. THE YFINANCE WARNING NOISE ------------------------------------------
    print(f"\n{LINE}\nL. YFINANCE'S NUMPY WARNINGS ARE SILENCED, OURS ARE NOT\n{LINE}")
    import warnings
    import altdata                                               # noqa: F401
    hits = [f for f in warnings.filters if f[0] == "ignore" and f[2] is DeprecationWarning
            and f[3] is not None and f[3].pattern.startswith("yfinance")]
    check(hits and hits[0][3].match("yfinance.utils") and hits[0][3].match("yfinance")
          and not hits[0][3].match("altdata.fx_charts"),
          "a filter on yfinance's own modules only")
    # UNDER THE REAL IMPORT ORDER (T2.6). The filter above was present on 6 Oct and
    # the box still printed thirteen warnings: yfinance's own __init__ inserts a
    # 'default' rule for its modules AT THE FRONT when it is imported, after
    # ours. So the proof is a FRESH interpreter, no -W, importing the package
    # first as `python -m altdata.bars` does, then yfinance through a production
    # import site, then calling the two yfinance lines that warned
    # (utils.py:432 and :612). The control -- the same calls after a BARE
    # `import yfinance` -- shows the check can see the warning at all.
    import subprocess
    probe = ("import pandas as pd\n"
             "import altdata.bars\n"
             "{imp}\n"
             "import yfinance.utils as u\n"
             "u._interval_to_timedelta('5m')\n"
             "u._dts_in_same_interval(pd.Timestamp('2026-10-01 10:00'), "
             "pd.Timestamp('2026-10-01 10:30'), '1h')\n"
             "print('probe ok')\n")
    env = {k: v for k, v in os.environ.items() if k != "PYTHONWARNINGS"}

    def run_probe(imp: str) -> tuple[str, str]:
        r = subprocess.run([sys.executable, "-c", probe.format(imp=imp)],
                           cwd=str(REPO), capture_output=True, text=True, env=env,
                           timeout=180)
        return r.stdout, r.stderr
    out_c, err_c = run_probe("import yfinance")
    control = "DeprecationWarning" in err_c and "yfinance" in err_c
    out_p, err_p = run_probe("from altdata.sources import overnight\n"
                             "assert overnight._yf() is not None")
    check("probe ok" in out_p and "DeprecationWarning" not in err_p,
          "a fresh interpreter importing yfinance through the repo's import site "
          "prints no yfinance DeprecationWarning from utils.py:432 or :612"
          + (f" -- stderr: {err_p.strip()[-300:]}" if err_p.strip() else ""))
    if control:
        check(True, "and the control prints it after a bare `import yfinance` -- "
                    "yfinance's own filter wins there, which is why the helper exists")
    else:
        print("  NOTE  the control printed no warning: this yfinance no longer "
              "raises it, so the silence above is not yet tested against it")
    root = REPO
    bare = []
    for f in list(root.glob("*.py")) + [p for d in ("altdata", "daily_cascade",
                                                     "monthly_macro", "tools", "scripts")
                                        for p in (root / d).rglob("*.py")]:
        if f.as_posix().endswith("altdata/__init__.py") or ".venv" in f.parts:
            continue
        for n, ln in enumerate(f.read_text(encoding="utf-8", errors="replace")
                               .splitlines(), 1):
            if re.match(r"\s*(import yfinance\b|from yfinance\b)", ln):
                bare.append(f"{f.relative_to(root).as_posix()}:{n}")
    check(not bare, "every import of yfinance goes through altdata.import_yfinance()"
          + (f"; bare imports at {bare}" if bare else ""))

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
