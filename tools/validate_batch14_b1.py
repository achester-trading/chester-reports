"""
Signal-triage Batch 14, Part B1 (items 65 and 71, written as 58 and 64;
docs/change-order-signal-triage-batch-14-2026-10-20.md, ruled 20 Oct 2026 with
filing amendments F1-F8; session A's a57-batch14-b1).

  A  THE SPEED-FLAG ATTRIBUTION (item 65, F5): the trigger on a printed SR-35
     companion (its lead horizon) and silent otherwise; the split by hand; the
     models' leg, agreement and disagreement; "awaiting" with no model input on the
     day, and partial with one; the ledger row, and resolve writing the
     attribution as a new vintage once the inputs land; the close's sub-section
     after item 52's block, its Plumbing line, and the row the close stores.
  B  ONE BIG AI TRADE (item 65): the PPI line's year-on-year change and dual
     percentiles by hand, a line not stored listed; its panel in item 46's
     inflation block, Monthly only; the proxy pair's relative return by hand, the
     "proxy" label wherever it prints, absent with its reason on short history;
     the AI-credit gap line beside SR-16's neocloud line (F2).
  C  THE FRAGILITY PANEL (item 71): the Amihud measure and the range per volume by
     hand; margin debt's share (Z.1 millions to dollars, marked to SPX); the
     leveraged-ETF rebalance by hand (L x (L - 1), an inverse fund too); dealer
     gamma's hedging only when negative; ES depth "not tracked"; the uncovered
     funds listed; the panel silent with no volume stored.
  D  THE FLAG: both arms on, either off, "not read"; the stand-in labelled; flag
     rights only.
  E  THE LENS AND THE LEVELS READ (F5): the report-only liquidity row after item
     52's ten, outside the attribution the ledger counts; the flag's line.
  F  THE SOURCES AND REGISTRATION: the four FRED ids through the existing pull;
     AIQ and SPXT in the basket and the Security Master; every new key, the
     source and the commands registered; no Brookfield instrument among the
     proxies or the funds; the voices entry (F4) with its tier and its crawl
     delay honoured.
  G  THE LEDGERS: both pre-registrations at their SHA-256, the scripts opening no
     store, each rule applied on fixtures, the first editions on file with their
     verdicts as printed.
  H  NO VENDOR VALUE, NO BY-HAND KEY, NO WRITE beyond the ledger row; no
     composite, market-state object, register or order path; no person's name in
     the new files.

Synthetic fixtures only: no live store, no network, no model.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tools" / "calibration"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp                                    # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
TD = Path(mkdtemp("batch14-b1-gate-"))
LIVE_DB = REPO / "data" / "chester.db"
LIVE_DB_AT_START = LIVE_DB.exists()
PREREGS = {
    "docs/ledgers/speed-attribution-preregistration-2026-10.md":
        "922fdd2d696f7ab5ffb5426e51fb8dc77c54cd8f2422b5ccaa4f9bced6ad3628",
    "docs/ledgers/air-pocket-preregistration-2026-10.md":
        "dd999eb51a1f7165a479478de4f86ce6b8b03d01bf4f4b9c38bbd60a00772e08",
}
NEW_MODULES = ("altdata/speed_attribution.py", "altdata/ai_trade.py", "altdata/fragility.py",
               "daily_cascade/batch14_b1_block.py",
               "tools/calibration/st_r6_65a_speed_attribution.py",
               "tools/calibration/st_r6_71d_air_pockets.py")
NEW_FILES = NEW_MODULES + ("config/ai_trade.yaml", "config/fragility.yaml",
                           "config/speed_attribution.yaml") + tuple(PREREGS)


def check(ok: bool, what: str) -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS  {what}")
    else:
        FAIL += 1
        print(f"  FAIL  {what}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def weekdays(start: str, n: int) -> list[str]:
    d, out = dt.date.fromisoformat(start), []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def put(rows: list, key: str, day: str, v, inst=None, src: str = "fred") -> None:
    rows.append({"registry_key": key, "instrument": inst, "observed_at": day,
                 "available_at": f"{day}T22:00:00+00:00", "value": v, "source": src})


# ---------------------------------------------------------------------------
# A. The speed-flag attribution
# ---------------------------------------------------------------------------
SCREEN = {"companion_10y": {"printed": True, "z10": -2.4, "z21": 1.1,
                            "line": "10-year Treasury, the speed of the move: two-week -25 bp (-2.4σ)"}}


def group_a() -> None:
    head("A. THE SPEED-FLAG ATTRIBUTION (item 65, F5)")
    from altdata import speed_attribution as sa
    cfg = sa.config()
    tr = sa.trigger(SCREEN)
    check(tr["fired"] and tr["horizon"] == 10 and tr["z"] == -2.4,
          "the trigger fires on SR-35's printed companion, lead horizon the larger |z| (10)")
    check(not sa.trigger({"companion_10y": {"printed": False, "z10": 1.0}})["fired"]
          and not sa.trigger(None)["fired"]
          and not sa.evaluate({}, {"companion_10y": {"printed": False}}, "2026-10-16")["fired"],
          "silent when the companion did not print, or no screen")
    days = weekdays("2026-09-28", 15)
    day = days[-1]
    y = [(d, 5.30 - 0.025 * i) for i, d in enumerate(days)]      # -25 bp over 10 sessions
    ser = {"yield": y, "kw": [(d, 0.80 - 0.02 * i) for i, d in enumerate(days)],
           "acm": [(d, 0.60 - 0.005 * i) for i, d in enumerate(days)]}
    ev = sa.evaluate(ser, SCREEN, day, cfg)
    att = ev["attribution"]
    kw = next(m for m in att["models"] if m["model"] == "kw")
    acm = next(m for m in att["models"] if m["model"] == "acm")
    check(att["move_bp"] == -25.0 and kw["premium_bp"] == -20.0 and kw["path_bp"] == -5.0
          and kw["premium_share"] == 0.8 and kw["carried"] == "the term premium",
          "KW by hand: the 10-year -25 bp, its premium -20 bp, path -5 bp, share 0.80 -> the "
          "term premium")
    check(acm["premium_bp"] == -5.0 and acm["premium_share"] == 0.2
          and acm["carried"] == "expected short rates" and "disagree" in att["line"],
          "ACM by hand: premium -5 bp, share 0.20 -> expected short rates; the models disagree")
    ser2 = dict(ser, acm=[(d, 0.60 - 0.02 * i) for i, d in enumerate(days)])
    a2 = sa.evaluate(ser2, SCREEN, day, cfg)["attribution"]
    check(a2["state"] == "computed" and a2["line"].startswith("the term premium carried")
          and "agree" in a2["line"], "both lean the same way: the leg named, 'agree'")
    ser3 = dict(ser, kw=ser["kw"][:-1], acm=[])
    e3 = sa.evaluate(ser3, SCREEN, day, cfg)
    check(e3["state"] == "awaiting" and "awaiting" in e3["line"]
          and f"stored through {days[-2]}" in e3["line"],
          "F5: no model input stored for the day prints 'awaiting', naming how far each is stored")
    e4 = sa.evaluate(dict(ser, acm=ser["acm"][:-1]), SCREEN, day, cfg)
    check(e4["state"] == "partial" and "awaiting ACM" in e4["line"],
          "one model read and one awaiting: partial, the awaiting model named")
    row = sa.ledger_row(e3, f"{day}T21:00:00+00:00")
    body = json.loads(row["value"])
    check(row["registry_key"] == "rates.speed_event_ledger" and row["instrument"] == day
          and body["state"] == "awaiting" and row["source"] == "speed_attribution",
          "the ledger row: the flag day, 'awaiting', its source")
    fwd = weekdays(days[-1], 22)[1:]
    yfull = y + [(d, y[-1][1] - 0.01 * (i + 1)) for i, d in enumerate(fwd)]
    late = {**ser, "yield": yfull}
    res = sa.resolve_rows([body], late, cfg, "2026-11-20T21:00:00+00:00")
    nb = json.loads(res[0]["value"]) if res else {}
    check(len(res) == 1 and nb["state"] == "computed" and nb["outcomes"]["resolved"]
          and nb["outcomes"]["y10_20d_bp"] == -20.0 and nb["outcomes"]["continued"] is True,
          "resolve: the attribution written once the inputs land, the 20-session outcome by "
          "hand (-20 bp, continued), a new vintage")
    check(sa.resolve_rows([nb], late, cfg, "x") == []
          or json.loads(sa.resolve_rows([nb], late, cfg, "x")[0]["value"]) != nb,
          "resolve writes nothing for a row that is unchanged")
    # The close: after item 52's block, a Plumbing line, the event kept to store.
    from daily_cascade import batch14_b1_block as bb
    from altdata import observations
    db = TD / "speed.db"
    rows = []
    for d, v in y:
        put(rows, "fred.yield_10y", d, v)
    for d, v in ser["kw"]:
        put(rows, "fred.term_premium_kw", d, v)
    with observations.ObservationStore(str(db)) as st:
        st.write_many(rows)
        built = {"mechanics": {"items": [], "subsections": [{"title": "Volatility event"},
                                                           {"title": "Other"}], "data": {}},
                 "plumbing": {"items": []}}
        bb.close_extras(built, st, day, f"{day}T23:00:00+00:00", SCREEN)
    subs = [s["title"] for s in built["mechanics"]["subsections"]]
    check(subs[:2] == ["Volatility event", sa.TITLE]
          and any(i["key"] == "plumb:speed_attribution" for i in built["plumbing"]["items"])
          and built["mechanics"]["data"]["_speed_event"]["fired"],
          "the close: the attribution right after item 52's block, its Plumbing line, the "
          "event kept for the close to store")
    src = (REPO / "daily_cascade" / "stack_close.py").read_text(encoding="utf-8")
    check('pop("_speed_event"' in src and "sa.ledger_row(spd" in src and "not dry_run" in src,
          "the close stores the flag day's ledger row, never on a dry run")
    sh = (REPO / "scripts" / "run_eod_cron.sh").read_text(encoding="utf-8")
    check("-m altdata.speed_attribution resolve" in sh and "WARN speed_attribution" in sh,
          "the EOD pass resolves the ledger after item 52's, warn-only")


# ---------------------------------------------------------------------------
# B. One big AI trade
# ---------------------------------------------------------------------------
def group_b() -> None:
    head("B. ONE BIG AI TRADE (item 65)")
    from altdata import ai_trade
    cfg = ai_trade.config()
    months = [f"{y}-{m:02d}-01" for y in range(2019, 2027) for m in range(1, 13)
              if f"{y}-{m:02d}-01" <= "2026-09-01"]
    pcb = [(d, 100.0 * 1.02 ** i) for i, d in enumerate(months)]
    r = ai_trade.ppi_read({"fred.ppi_pcb_assembly": pcb}, cfg)
    row = r["rows"][0]
    check(row["month"] == "2026-09" and row["yoy_pct"] == round((1.02 ** 12 - 1) * 100, 1),
          f"the PPI line's year-on-year change by hand ({row['yoy_pct']}%)")
    lz = row["lens"]
    check(lz["n_full"] == len(pcb) - 12 and lz["n_window"] == 60 and not lz["same"]
          and "percentile of 5 years" in row["lens_text"],
          "dual percentiles: five years and the full history, each with its n")
    check({m["name"] for m in r["missing"]} == {"computer storage devices", "semiconductors"}
          and "Not read" in ai_trade.ppi_lines(r)[-1],
          "a line not stored is listed as not read, never zero")
    from daily_cascade import inflation_block as ib
    check(("ai_ppi", ib._ai_ppi_panel) in ib.PANELS and "ai_ppi" in ib.MONTHLY_ONLY,
          "the panel in item 46's inflation block, Monthly only (monthly, as ruled)")
    days = weekdays("2024-01-01", 400)
    ai = [(d, 100.0 * 1.001 ** i) for i, d in enumerate(days)]
    ex = [(d, 100.0) for d in days]
    p = ai_trade.proxy_read(ai, ex, cfg)
    want = (1.001 ** 252 - 1) * 100
    check(p["state"] == "computed" and abs(p["rel_1y_pp"] - round(want, 1)) < 1e-9,
          f"the proxy's one-year relative return by hand ({p['rel_1y_pp']} pp)")
    line = ai_trade.proxy_line(p)
    check("(proxy)" in line and "AIQ against SPXT" in line and line.count("proxy") >= 1
          and "Goldman" not in line, "labelled 'proxy', the pair named, the cited index never named")
    short = ai_trade.proxy_read(ai[:50], ex[:50], cfg)
    check(short["state"] == "absent" and "backfill" in short["reason"]
          and "proxy" in ai_trade.proxy_line(short),
          "short history: absent with its reason, still labelled")
    from daily_cascade import absorption_block as ab
    src = (REPO / "daily_cascade" / "absorption_block.py").read_text(encoding="utf-8")
    check("CoreWeave, Oracle and" in ab.AI_CREDIT_LINE and "NOT TRACKED" in ab.AI_CREDIT_LINE
          and src.index("{NEOCLOUD_LINE}") < src.index("{AI_CREDIT_LINE}")
          and ab.AI_CREDIT_LINE.startswith(" ".join(cfg["credit_watch_gap"].split())[:40]),
          "the AI-credit watch: a listed gap beside SR-16's neocloud line, no by-hand path (F2)")


# ---------------------------------------------------------------------------
# C, D. The fragility panel and the flag
# ---------------------------------------------------------------------------
def seed_fragility(db: Path, n: int = 1400, spike: bool = True, gamma: float = -2e9,
                   volume: bool = True) -> str:
    from altdata import observations
    rows = []
    days = weekdays("2021-01-04", n)
    p = q = 400.0
    for i, d in enumerate(days):
        last = i >= n - 25
        r = (0.004 if i % 2 else -0.004) * (3.0 if (spike and last) else 1.0)
        p, q = p * (1 + r), q * (1 + 1.2 * r)
        put(rows, "yfinance.mkt_spy", d, p, src="yfinance")
        put(rows, "yfinance.mkt_spy_high", d, p * 1.006, src="yfinance")
        put(rows, "yfinance.mkt_spy_low", d, p * 0.994, src="yfinance")
        if volume:
            put(rows, "yfinance.mkt_spy_volume", d, 6e7 if (spike and last) else 8e7,
                src="yfinance")
        put(rows, "yfinance.mkt_qqq", d, q, src="yfinance")
        put(rows, "yfinance.mkt_gspc", d, p * 10, src="yfinance")
        for t in ("TQQQ", "SQQQ", "QLD", "UPRO", "SPXU", "SSO", "SDS"):
            put(rows, "levetf.aum", d, 2e10 * (2.0 if (spike and last) else 1.0), t,
                "proshares")
    put(rows, "dealer.window_gamma", days[-1], gamma, "SPY:all", "daily_close")
    for y in range(2021, 2027):
        for m in range(1, 13):
            me = (dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)).isoformat()
            if me <= days[-1]:
                put(rows, "finra.margin_debit", me, 8e11, src="finra_margin")
            if m in (1, 4, 7, 10) and f"{y}-{m:02d}-01" < days[-1][:8] + "01":
                put(rows, "fred.z1_equities_mv", f"{y}-{m:02d}-01", 5e7)
    with observations.ObservationStore(str(db)) as st:
        st.write_many(rows)
    return days[-1]


def group_c() -> None:
    head("C. THE FRAGILITY PANEL (item 71)")
    from altdata import fragility as fr, observations
    close = [("2026-10-01", 100.0), ("2026-10-02", 101.0)]
    dep = fr.daily_depth(close, [("2026-10-02", 102.0)], [("2026-10-02", 99.0)],
                         [("2026-10-02", 1e7)])
    dv = 101.0 * 1e7 / 1e9
    check(len(dep) == 1 and abs(dep[0][1] - abs(math.log(1.01)) * 1e4 / dv) < 1e-9
          and abs(dep[0][2] - 3.0 / 100.0 * 1e4 / dv) < 1e-9,
          "Amihud and range per volume by hand: bp per $1bn of close x shares")
    check(fr.rolling_mean([("a", 1.0), ("b", None), ("c", 3.0)], 3, 2) == [("c", 2.0)],
          "the 20-session mean's rule: a value missing is skipped, the floor holds")
    sh = fr.margin_share_series([("2026-05-31", 8e11), ("2026-06-30", 8e11)],
                                [("2026-01-01", 5e7)],
                                [("2026-03-31", 100.0), ("2026-05-29", 110.0),
                                 ("2026-06-30", 120.0)], 1e6)
    check(sh[0] == ("2026-05-31", 8e11 / (5e13 * 1.1) * 100, True)
          and abs(sh[1][1] - 8e11 / (5e13 * 1.2) * 100) < 1e-12,
          "margin debt's share by hand: Z.1 millions to dollars, marked to SPX past the "
          "quarter's end, labelled marked")
    funds = [{"ticker": "UP", "leverage": 3, "proxy": "spy"},
             {"ticker": "DN", "leverage": -3, "proxy": "spy"}]
    reb = fr.rebalance_series({"UP": [("2026-10-01", 1e9)], "DN": [("2026-10-01", 1e9)]},
                              {"spy": [("2026-10-01", 100.0), ("2026-10-02", 98.0)]}, funds, 5)
    check(len(reb) == 1 and reb[0][0] == "2026-10-02" and reb[0][2] == ["UP", "DN"]
          and abs(reb[0][1] - (1e9 * 6 * -0.02 + 1e9 * 12 * -0.02)) < 1e-3,
          "the rebalance by hand: AUM x L x (L - 1) x the return, the inverse fund trading "
          "with the move too")
    ff = fr.forced_flow([("d1", -1e8, []), ("d2", -1e8, [])], {"d1": -2e9, "d2": 3e9},
                        {"d1": -0.01, "d2": -0.01})
    check(ff == [("d1", 1e8 + 2e9, True), ("d2", 1e8, True)],
          "dealer gamma's hedging counts only when negative: |gamma| x the move in percent")
    db = TD / "frag.db"
    day = seed_fragility(db)
    with observations.ObservationStore(str(db)) as st:
        ev = fr.build(st, day, f"{day}T23:00:00+00:00")
    pn = fr.panel(ev)
    rows = {r[0]: r for r in pn["table"]["rows"]}
    check(ev["depth"]["amihud"]["state"] == "computed"
          and "of 5 years" in ev["depth"]["amihud"]["lens_text"]
          and ev["depth"]["range"]["state"] == "computed",
          "the depth proxies with dual percentiles, from the stored daily bars")
    check(rows["ES top-of-book depth"][1] == "NOT TRACKED"
          and "check 8" in rows["ES top-of-book depth"][2]
          and "NOT TRACKED" in ev["es_depth_gap"],
          "ES top-of-book depth prints 'not tracked' (section 5 check 8)")
    check(any(k.startswith("FINRA margin debt") for k in rows)
          and "(marked)" in rows["Margin debt, share of Z.1 equity market value"][1],
          "margin debt as a level and as a share, marked between Z.1 releases")
    gaps = next(x for x in pn["lines"] if x.startswith("Leveraged ETFs not covered"))
    check(all(t in gaps for t in ("SPXL", "SPXS", "TNA", "TZA"))
          and not any(t in gaps for t in ("QID", "UDOW", "SDOW", "URTY", "SRTY")),
          "every major fund the writer does not cover is a listed gap (Direxion's four; "
          "ProShares' five are covered since ruling D13)")
    from altdata.sources import proshares as _ps
    lev = {f["ticker"]: f["leverage"] for f in fr.config()["leveraged_etfs"]["covered"]}
    want = {"QID": -2, "UDOW": 3, "SDOW": -3, "URTY": 3, "SRTY": -3}
    check(all(lev.get(t) == L and t in _ps.FUNDS for t, L in want.items()),
          "ruling D13: QID -2, UDOW 3, SDOW -3, URTY 3, SRTY -3 in the writer's FUNDS and the "
          "rebalance estimate")
    check(ev["flow"]["dealer"]["regime"] == "negative"
          and "(6b, as stored)" in " ".join(r[0] for r in pn["table"]["rows"]),
          "dealer gamma read as 6b stored it, never recomputed")
    db2 = TD / "frag-novol.db"
    d2 = seed_fragility(db2, n=300, volume=False)
    with observations.ObservationStore(str(db2)) as st:
        ev2 = fr.build(st, d2, f"{d2}T23:00:00+00:00")
    check(fr.panel(ev2) is None and ev2["flag"]["state"] == "not read",
          "no SPY volume stored: the panel prints nothing and the flag is not read")
    return ev


def group_d(ev: dict) -> None:
    head("D. THE FLAG (item 71)")
    from altdata import fragility as fr
    cfg = fr.config()
    on_d = {"amihud": {"state": "computed", "lens": {"percentile_window": 92.0}}}
    off_d = {"amihud": {"state": "computed", "lens": {"percentile_window": 89.0}}}
    on_f = {"forced": {"state": "computed", "dealer_read": True,
                       "lens": {"percentile_window": 95.0}}}
    at_f = {"forced": {"state": "computed", "dealer_read": False,
                       "lens": {"percentile_window": 90.0}}}
    a = fr.flag(on_d, on_f, cfg)
    check(a["state"] == "on" and "ON" in a["line"] and fr.STAND_IN in a["line"],
          "both arms: ON, the depth arm labelled as the Amihud stand-in")
    b = fr.flag(off_d, on_f, cfg)
    c = fr.flag(on_d, at_f, cfg)
    check(b["state"] == "off" and c["state"] == "off"
          and "leveraged-ETF arm alone" in c["line"],
          "either arm off: off (the forced-flow arm needs ABOVE its 90th; dealer gamma's "
          "absence said)")
    d = fr.flag({"amihud": {"state": "absent"}}, on_f, cfg)
    check(d["state"] == "not read" and "Flag rights only" in a["line"],
          "an arm without a reading: 'not read'; flag rights only, said on the line")
    check(cfg["flag"]["amihud_pct"] == 90 and cfg["flag"]["forced_flow_pct"] == 90
          and cfg["flag"]["depth_pct"] == 10,
          "the ruled thresholds: depth below its 10th (the stand-in at its 90th), forced "
          "flow above its 90th")
    check(ev["flag"]["state"] in ("on", "off"), f"the fixture's flag reads ({ev['flag']['state']})")


# ---------------------------------------------------------------------------
# E. The lens and the levels read
# ---------------------------------------------------------------------------
def group_e(ev: dict) -> None:
    head("E. THE LENS COLUMN AND THE LEVELS READ (F5)")
    from altdata import fragility as fr, vol_event as ve
    lens = fr.lens(ev)
    fired = {"fired": True, "day": "2026-10-16",
             "table": {"rows": [[ve.LENS_TITLES[k], "x", "—"] for k in ve.LENS_ORDER]},
             "trigger": {"direction": "up", "arms": {}, "level": {"value": 22.0}},
             "lenses": {k: {"line": "x"} for k in ve.LENS_ORDER}}
    ve.with_liquidity(fired, lens)
    check(len(fired["table"]["rows"]) == len(ve.LENS_ORDER) + 1
          and fired["table"]["rows"][-1][0] == "Liquidity (report only)"
          and "report only" in fired["table"]["rows"][-1][1],
          "the liquidity lens: a report-only row after item 52's ten")
    body = json.loads(ve.ledger_row(fired, "t", None)["value"])
    check(len(body["attribution"]) == len(ve.LENS_ORDER)
          and "Liquidity (report only)" in body["report_only"],
          "the ledger's attribution keeps its ten; the lens rides under report_only")
    quiet = {"fired": False, "table": {"rows": []}}
    check(ve.with_liquidity(quiet, lens) == {"fired": False, "table": {"rows": []}},
          "a quiet session gets no row")
    src = (REPO / "daily_cascade" / "stack.py").read_text(encoding="utf-8")
    check("ve.with_liquidity(ev, batch14_b1_block.liquidity_lens(" in src,
          "the close attaches the lens to a fired event")
    ln = fr.levels_line(ev)
    sc = (REPO / "daily_cascade" / "stack_close.py").read_text(encoding="utf-8")
    check(ln.startswith("Liquidity: The fragility flag is")
          and "batch14_b1_block.levels_line(" in sc and 'es_sub["lines"]' in sc,
          "the flag's line in item 45's levels read")


# ---------------------------------------------------------------------------
# F. Sources and registration
# ---------------------------------------------------------------------------
def group_f() -> None:
    head("F. THE SOURCES AND REGISTRATION")
    from altdata import config as acfg, derived, source_ids
    from altdata.sources import yfinance_source as yf
    ids = {s.key: s.fred_id for s in acfg.FRED_BATCH14_B1_SERIES}
    check(ids == {"ppi_pcb_assembly": "PCU334418334418",
                  "ppi_storage_devices": "PCU334112334112",
                  "ppi_semiconductors": "PCU334413334413",
                  "z1_equities_mv": "BOGZ1LM893064105Q"}
          and set(acfg.FRED_BATCH14_B1_SERIES) <= set(acfg.FRED_PULL_SERIES),
          "the four FRED ids (check 1 and the capitalisation), through the existing pull")
    check(acfg.SERIES_BY_KEY["z1_equities_mv"].units == "M"
          and __import__("altdata.fragility").fragility.config()["margin"]["market_value_scale"]
          == 1e6, "Z.1's market value is MILLIONS, scaled to dollars before the share")
    check(yf.SYMBOLS.get("AIQ") == "mkt_aiq" and yf.SYMBOLS.get("SPXT") == "mkt_spxt"
          and yf.resolve_basket(yf.SYMBOLS) == yf.SYMBOLS,
          "AIQ and SPXT join the basket, resolved through the Security Master")
    keys = ([f"fred.{k}" for k in ids] + ["yfinance.mkt_aiq", "yfinance.mkt_spxt",
                                          "rates.speed_event_ledger"])
    check(all(derived.registry_entry(k) for k in keys)
          and source_ids.canonical("speed_attribution") == "speed_attribution",
          f"every new key registered ({len(keys)}), and the ledger's source")
    import yaml
    cat = yaml.safe_load((REPO / "config" / "catalogue_commands.yaml").read_text(encoding="utf-8"))
    flat = json.dumps(cat)
    check(all(m in flat for m in ("altdata.speed_attribution", "altdata.ai_trade",
                                  "altdata.fragility")),
          "the three commands in the catalogue")
    from register import instruments
    from altdata import fragility as fr
    tick = (["AIQ", "SPXT"] + [f["ticker"] for f in fr.config()["leveraged_etfs"]["covered"]])
    bad = [t for t in tick if instruments.restrictions().is_restricted(t)]
    check(not bad, f"no Brookfield instrument among the proxies or the funds ({bad or 'none'})")
    vs = yaml.safe_load((REPO / "config" / "voices_sources.yaml").read_text(encoding="utf-8"))
    src = next((s for s in vs["sources"] if s["id"] == "carson_group"), {})
    from altdata import source_tiers
    check(src.get("method") == "rss" and src.get("default_voice") == "Carson Group"
          and src.get("pause_seconds") == 10 and src.get("default_kind") in vs["kinds"]
          and source_tiers.tier_of("x - Carson Group") == 2,
          "F4: the firm's public blog by its feed, tier 2, its crawl delay as pause_seconds")
    from altdata.sources import voices_scan as vsc
    f = vsc.Fetcher("ua", pause=2.0, opener=lambda u, h: b"")
    f.host_pause["www.carsongroup.com"] = 10.0
    slept = []
    import time as _t
    real = _t.sleep
    _t.sleep = lambda s: slept.append(s)
    try:
        f.get("https://www.carsongroup.com/feed/")
        f.get("https://www.carsongroup.com/a/")
    finally:
        _t.sleep = real
    check(slept and slept[0] > 9.0, "the scan honours a host's longer pause (the crawl delay)")


# ---------------------------------------------------------------------------
# G. The ledgers
# ---------------------------------------------------------------------------
def group_g() -> None:
    head("G. THE LEDGERS")
    for rel, sha in PREREGS.items():
        raw = (REPO / rel).read_bytes().replace(b"\r\n", b"\n")
        check(hashlib.sha256(raw).hexdigest() == sha and b"Never edited" in raw,
              f"{rel.split('/')[-1]} on file at its SHA-256 (LF bytes), 'Never edited'")
    for rel, pre in (("tools/calibration/st_r6_65a_speed_attribution.py", list(PREREGS)[0]),
                     ("tools/calibration/st_r6_71d_air_pockets.py", list(PREREGS)[1])):
        s = (REPO / rel).read_text(encoding="utf-8")
        check("ObservationStore" not in s and "import regime" not in s and pre in s,
              f"{rel.split('/')[-1]} opens no store and names its registration")
    import st_r6_65a_speed_attribution as S
    # The flag's prefix-sum window against move_screen.screen_points itself.
    from altdata import move_screen
    days = weekdays("2001-01-01", 400)
    y = [(d, 5.0 + 0.3 * math.sin(i / 7.0) + (0.6 if i > 390 else 0.0))
         for i, d in enumerate(days)]
    reads = {r["day"]: r for r in S.flags(y)}
    ref = move_screen.screen_points(y, "diff", {"min_observations": 30, "sigma": 2.0},
                                    history_days=7305, horizons=[10, 21])
    check(reads[days[-1]]["z"][10] == ref["z10"] and reads[days[-1]]["z"][21] == ref["z21"],
          f"the ledger's flag reproduces the live screen's z (10: {ref['z10']}, 21: {ref['z21']})")

    def rows(prem, path, cont_p, cont_h):
        out = []
        for k in range(prem):
            out.append({"day": f"2000-01-{k + 1:02d}", "leg": S.PREMIUM, "continued": k < cont_p})
        for k in range(path):
            out.append({"day": f"2000-02-{k + 1:02d}", "leg": S.PATH, "continued": k < cont_h})
        return sorted(out, key=lambda r: r["day"])
    days2 = ["d"] * 30

    def v(rs):
        for r in rs:
            r.update(horizon=10, z=2.1, move_bp=50.0, kw_share=0.6, acm_share=0.6,
                     y10_5s_bp=1.0, y10_20s_bp=1.0)
        return S.verdict(rs, {"yield": [], "kw": [], "acm": []}, "fixture", days2)["verdict"]
    check(v(rows(14, 20, 7, 10)).startswith("INSUFFICIENT"), "14 in a group: INSUFFICIENT")
    mixed = rows(16, 16, 0, 0)
    for r in mixed:
        r["continued"] = r["leg"] == S.PREMIUM
    check(v([dict(r, day=f"{i:04d}") for i, r in enumerate(
        sorted(mixed, key=lambda r: (r["day"][-2:], r["leg"])))]).startswith("PASS"),
          "16 and 16, premium always continuing, path never, in both halves: PASS")
    check(v(rows(16, 16, 8, 8)).startswith("FAIL"), "equal shares: FAIL")
    import st_r6_71d_air_pockets as P
    check(P.FALL == -0.025 and P.POCKET_MONTHS == ("2018-02", "2024-08", "2025-04")
          and P.MIN_ON == 20 and P.ARM_PCT == 90.0 and P.SAMPLE_FROM == "2015-01-02",
          "the air-pocket ledger's registered constants")
    pts = [(f"2020-01-{i:02d}", float(i)) for i in range(1, 11)]
    check(P.pct_series(pts)["2020-01-10"] == 100.0 and P.pct_series(pts)["2020-01-01"] == 100.0
          and P.pct_series([("2014-01-01", 5.0), ("2020-01-01", 1.0)])["2020-01-01"] == 100.0,
          "the percentile: at or below, itself included, five calendar years back")
    for name, word, n in (("st-r6.65a-ledger-2026-10-23.md", "INSUFFICIENT", "28"),
                          ("st-r6.71d-ledger-2026-10-23.md", "FAIL", "2965")):
        led = (REPO / "docs" / "ledgers" / name).read_text(encoding="utf-8")
        check(f"| Verdict | **{word}" in led and f"| n | {n} |" in led,
              f"{name}: the first edition on file, its verdict as printed ({word}, n {n})")


# ---------------------------------------------------------------------------
# H. Nothing else
# ---------------------------------------------------------------------------
def group_h() -> None:
    head("H. NO VENDOR VALUE, NO BY-HAND KEY, NO WRITE BEYOND THE LEDGER ROW")
    bad = []
    for rel in NEW_MODULES:
        src = re.sub(r'"""[\s\S]*?"""', "", (REPO / rel).read_text(encoding="utf-8"))
        if re.search(r"manual\.|manual_input|flashalpha|vendor\.|data/vendor", src, re.I):
            bad.append(rel)
    check(not bad, f"no new module reads a vendor value or a by-hand key ({bad or 'none'})")
    bad = []
    for rel in ("altdata/ai_trade.py", "altdata/fragility.py", "daily_cascade/batch14_b1_block.py"):
        src = (REPO / rel).read_text(encoding="utf-8")
        if re.search(r"write_many|open_writer|market_state|import regime|register\.|place_?order",
                     src):
            bad.append(rel)
    check(not bad, f"the reads write nothing: no store write, register, composite or "
                   f"market-state object ({bad or 'none'})")
    sa = (REPO / "altdata" / "speed_attribution.py").read_text(encoding="utf-8")
    check(sa.count("write_many") == 2 and "market_state" not in sa and "import regime" not in sa,
          "the attribution writes only its ledger rows, from its seed and resolve commands")
    names = ("Varghese", "Cembalest", "Lemand", "Bilello", "Monchau", "Goldman",
             "ZeroHedge", "Kim-Wright", "@")
    hits = [(rel, n) for rel in NEW_FILES for n in names
            if n in (REPO / rel).read_text(encoding="utf-8")]
    check(not hits, f"no person's name, handle or the cited index's house in the new files "
                    f"({hits or 'none'})")


def main() -> int:
    ev = None
    for g in (group_a, group_b, group_c):
        try:
            out = g()
            ev = out if out is not None else ev
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    for g in (group_d, group_e):
        try:
            if ev is None:
                raise RuntimeError("group C produced no fixture read")
            g(ev)
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    for g in (group_f, group_g, group_h):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    head("THE GATE RUN")
    check(LIVE_DB.exists() == LIVE_DB_AT_START, "this gate run created no data/chester.db")
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
