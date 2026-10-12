"""
Validation gate for the store-wide move screen and the EM screen (Audit #4
Part III, Category 1 items 1 and 5; SR-46 b-d; altdata/move_screen.py).

A SYNTHETIC STORE of its own -- six years of business days, seeded here, no
network, no box:

  A  A 2.5-SIGMA PRINT IS FLAGGED, A NORMAL DAY IS NOT. SPY falls 6% on the last
     session against 1% days: flagged, ranked, printed "<series> -x.xσ 1-day /
     -x.xσ 5-day · false flag k/N". QQQ's ordinary day: not flagged. A series
     with fewer than 500 observations is skipped and named. Written, it reads
     back the same, with available_at.
  B  THE BASE RATE'S ARITHMETIC. A constructed history with four past spikes,
     three of them more than half reversed within five sessions and one not:
     "false flag 3/4".
  C  THE UNIT RULE. A price moves by its log change; a rate, a spread, an EM
     currency's dollar rate (a price), a probability: by the registry's unit.
  D  WHAT IT SUBSUMES. SR-35: the 10-year's one-month change at 2 sigma on a
     twenty-year window prints as the 10-year row's companion. The prediction-
     market shock: a contract's 5-day move against its family's pooled moves,
     printed with its family name.
  E  DISPERSION AGAINST CO-MOVEMENT. The basket together is systemic ("dollar/
     risk-off; Factor IV's business"); one country alone is idiosyncratic ("a
     candidate for the narrative register"); two countries are mixed.
  F  THE CONTAGION WINDOW. A shock passes to the basket or to EM spreads inside
     five sessions, or lapses; the close prints every shock, the Weekly only
     one that passed.
  G  THE WEEKLY'S LINES. What doesn't fit prints the top five by |z|, the
     companion beside the 10-year, "n more past 2.5σ -- in the tables", and the
     reference tier lists every flag; the EM calendar template is empty and
     prints nothing, a seeded entry prints in its quarter.
  H  THE QUARTERLY'S HOOK. quarter_episodes(st, now): a member's shock is one
     episode (its 5-day run collapsed), idiosyncratic with contagion passed;
     the spread's widening is one contagion event; oldest first; [] before it.

    python tools/validate_move_screen.py
"""

from __future__ import annotations

import datetime as dt
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from gate_tmp import mkdtemp as gate_mkdtemp                    # noqa: E402

from altdata import move_screen as ms, observations             # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78
DAY = "2026-10-09"
QEND = "2026-09-30"        # group H: the quarter ending here
QSHOCK = "2026-08-12"
CUT = "2026-10-09T22:00:00+00:00"


def check(c: bool, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def bdays(end: str, years: float) -> list[str]:
    e = dt.date.fromisoformat(end)
    d = e - dt.timedelta(days=int(365.25 * years))
    out = []
    while d <= e:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def rows(key, inst, days, vals, source="fixture"):
    return [{"registry_key": key, "instrument": inst, "observed_at": d,
             "available_at": f"{d}T21:00:00+00:00", "value": v, "source": source}
            for d, v in zip(days, vals)]


def price_walk(seed, days, sd, last=None, start=100.0):
    rnd = random.Random(seed)
    v, out = start, []
    for _ in days:
        v *= math.exp(rnd.gauss(0, sd))
        out.append(v)
    if last is not None:
        out[-1] = out[-2] * math.exp(last)
    return out


def seed_store(path: str) -> None:
    days = bdays(DAY, 6)
    st = observations.ObservationStore(path)
    try:
        st.write_many(rows("yfinance.mkt_spy", None, days,
                           price_walk(1, days, 0.01, last=math.log(0.94))))
        st.write_many(rows("yfinance.mkt_qqq", None, days,
                           price_walk(2, days, 0.012, last=0.004)))
        # The 10-year: ordinary days, then +60 bp over the last month.
        rnd = random.Random(3)
        v, ten = 4.0, []
        for i, _ in enumerate(days):
            v += rnd.gauss(0, 0.05) + (0.03 if i >= len(days) - 21 else 0.0)
            ten.append(round(v, 4))
        st.write_many(rows("fred.yield_10y", None, days, ten))
        short = days[-300:]
        st.write_many(rows("fred.usd_brl", None, short, price_walk(4, short, 0.008,
                                                                  start=5.2)))
        # A prediction-market family: three contracts, ~220 sessions each, pooled
        # past 500; the last contract jumps 30 points over the last five sessions.
        rnd = random.Random(5)
        for n in range(3):
            ds = days[-(220 - n):]
            p, vals = 0.5, []
            for i, _ in enumerate(ds):
                p = min(0.97, max(0.03, p + rnd.gauss(0, 0.012)))
                vals.append(round(p, 4))
            if n == 2:
                for j in range(1, 6):
                    vals[-j] = round(min(0.97, vals[-6] + 0.30 * (6 - j) / 5), 4)
            inst = f"kalshi:CPI-{n}"
            st.write_many(rows("pm.probability", inst, ds, vals))
            st.write_many([{"registry_key": "pm.market", "instrument": inst,
                            "observed_at": ds[0], "available_at": f"{ds[0]}T21:00:00+00:00",
                            "value": ('{"event_title": "CPI in September", '
                                      '"question": "CPI above 0.%d%%?", '
                                      '"watch_id": "cpi_monthly"}' % n),
                            "source": "fixture"}])
    finally:
        st.close()


def group_a(path: str) -> dict:
    print(f"\n{LINE}\nA. A 2.5σ PRINT IS FLAGGED; A NORMAL DAY IS NOT\n{LINE}")
    with observations.ObservationStore(path) as st:
        res = ms.screen(st, DAY, CUT)
    flags = {f["series"]: f for f in res["flags"]}
    spy = flags.get("yfinance.mkt_spy")
    check(spy is not None and spy["z1"] < -2.5,
          f"SPY -6% on the session: flagged ({spy and spy['z1']:+.1f}σ 1-day)")
    check("yfinance.mkt_qqq" not in flags, "QQQ's ordinary session is not flagged")
    check(any(s["series"] == "fred.usd_brl" and s["n"] == 300 for s in res["skipped"]),
          "a series with 300 observations is skipped and named")
    line = ms.flag_line(spy)
    check(line.startswith(spy["label"] + " -") and "σ 1-day / " in line
          and "σ 5-day · false flag " in line,
          f"one line per flag: '{line}'")
    zs = [f["max_abs_z"] for f in res["flags"]]
    check(zs == sorted(zs, reverse=True), "ranked by |z|")
    with observations.ObservationStore(path) as st:
        out = ms.write(st, DAY, CUT)
        back = ms.read(st, DAY)
        stored = st.as_of("screen.move", None, "yfinance.mkt_spy")
    check(out["written"] >= 3 and back and back.get("stored")
          and {f["series"] for f in back["flags"]} == set(flags),
          f"written ({out['written']} rows) and read back with the same flags")
    check(stored and str(stored[-1]["available_at"]) > DAY
          and str(stored[-1]["observed_at"])[:10] == DAY,
          "each stored row: observed_at the session, available_at the compute instant")
    return res


def group_b() -> None:
    print(f"\n{LINE}\nB. THE FALSE-FLAG BASE RATE, ON A CONSTRUCTED HISTORY\n{LINE}")
    days = bdays(DAY, 3)
    diffs = [1.0 if i % 2 else -1.0 for i in range(len(days))]
    spikes = {200: True, 350: True, 500: True, 650: False}
    for i, reverts in spikes.items():
        diffs[i] = 10.0
        if reverts:
            for j in (1, 2, 3):
                diffs[i + j] = -2.0
    diffs[-1] = 10.0
    v, vals = 50.0, []
    for d in diffs:
        v += d
        vals.append(v)
    res = ms.screen_points(list(zip(days, vals)), "diff", ms.load_config())
    check(res["flagged"] and res["lead_horizon"] == 1 and res["z1"] > 2.5,
          f"today's +10 is flagged on the 1-day horizon ({res['z1']:+.1f}σ)")
    check(res["false_flag"] == {"k": 3, "n": 4},
          f"four past spikes, three more than half reversed within five sessions: "
          f"false flag {res['false_flag']['k']}/{res['false_flag']['n']}")
    check(ms.flag_line({"label": "Fixture", **res}).endswith("false flag 3/4"),
          "printed 'false flag 3/4'")


def group_c() -> None:
    print(f"\n{LINE}\nC. THE UNIT RULE\n{LINE}")
    check(ms.unit_rule("yfinance.mkt_spy") == "log" and ms.unit_rule("yfinance.mkt_ewz")
          == "log", "a price, a country ETF: log change")
    check(ms.unit_rule("fred.yield_10y") == "diff" and ms.unit_rule("fred.ig_oas") == "diff"
          and ms.unit_rule("fred.em_corp_oas") == "diff",
          "a rate and a spread: simple difference")
    check(ms.unit_rule("fred.usd_brl") == "log" and ms.unit_rule("yfinance.mkt_usdtry")
          == "log", "an EM currency per dollar is a price: log change")
    check(ms.unit_rule("pm.probability") == "diff", "a probability: simple difference")
    check(abs(ms.change(100.0, 110.0, "log") - math.log(1.1)) < 1e-12
          and ms.change(4.0, 4.25, "diff") == 0.25 and ms.change(0, 1, "log") is None,
          "the arithmetic: ln(b/a), b-a, and no log of a non-positive level")


def group_d(path: str, res: dict) -> None:
    print(f"\n{LINE}\nD. WHAT IT SUBSUMES: SR-35 AND THE PREDICTION-MARKET SHOCK\n{LINE}")
    c = res.get("companion_10y") or {}
    check(c.get("printed") and (c.get("z21") or 0) >= 2.0
          and "one-month" in c["line"] and "twenty-year window" in c["line"],
          f"the 10-year's companion at 2σ: '{c.get('line')}'")
    pm = [f for f in res["flags"] if f.get("kind") == "prediction_market"]
    check(len(pm) == 1 and pm[0]["family"] == "cpi_monthly"
          and pm[0]["label"].startswith("CPI in September:") and pm[0]["z5"] > 2.5,
          f"a contract's 5-day move against its family's pooled moves, with its family "
          f"name ({pm and pm[0]['label']}, {pm and pm[0]['z5']:+.1f}σ)")
    src = (REPO / "altdata" / "move_screen.py").read_text(encoding="utf-8")
    check("def sr35" not in src.lower() and "def em_move_screen" not in src,
          "no separate code path for SR-35 or SR-46(a): the basket members are store "
          "series like any other")


def m(country, kind, s5, flagged=False):
    return {"country": country, "kind": kind, "available": True, "stress5": s5,
            "flagged": flagged}


COUNTRIES = ["Brazil", "Mexico", "South Africa", "India", "Korea", "Taiwan",
             "Thailand", "China", "Turkey", "Indonesia"]


def group_e() -> None:
    print(f"\n{LINE}\nE. DISPERSION AGAINST CO-MOVEMENT\n{LINE}")
    cfg = ms.load_config()
    together = [m(c, k, 1.6 + 0.05 * i) for i, c in enumerate(COUNTRIES)
                for k in ("fx", "etf")]
    c = ms.classify(together, cfg)
    check(c["state"] == "systemic" and c["co_movement"] == 1.0,
          f"the basket together: systemic ({c['co_movement']:.0%} co-moving, median "
          f"{c['median_stress_z5']:+.1f}σ)")
    check("systemic -- dollar/risk-off; Factor IV's business" in ms.em_line(c),
          f"'{ms.em_line(c)}'")
    alone = [m(c_, k, (3.1 if c_ == "Brazil" else (0.3 if i % 2 else -0.4)),
               flagged=c_ == "Brazil")
             for i, c_ in enumerate(COUNTRIES) for k in ("fx", "etf")]
    c = ms.classify(alone, cfg)
    check(c["state"] == "idiosyncratic" and c["countries_flagged"] == ["Brazil"],
          "Brazil alone past 2.5σ: idiosyncratic")
    check(ms.em_line(c).startswith("Brazil alone past 2.5σ")
          and "a candidate for the narrative register" in ms.em_line(c),
          f"'{ms.em_line(c)}' (printed only; the register write is the operator's)")
    two = [m(c_, k, (3.0 if c_ in ("Brazil", "Turkey") else (0.3 if i % 2 else -0.4)),
             flagged=c_ in ("Brazil", "Turkey"))
           for i, c_ in enumerate(COUNTRIES) for k in ("fx", "etf")]
    check(ms.classify(two, cfg)["state"] == "mixed", "two countries without the basket: mixed")
    check(ms.classify(together[:3], cfg)["state"] == "insufficient",
          "fewer than four members stored: no classification")
    src = (REPO / "altdata" / "move_screen.py").read_text(encoding="utf-8")
    check("narratives confirm" not in src and "register.store" not in src
          and "decide.py" not in src, "the screen writes nothing to any register")


def group_f() -> None:
    print(f"\n{LINE}\nF. THE CONTAGION WINDOW\n{LINE}")
    days = [f"2026-10-{d:02d}" for d in (1, 2, 5, 6, 7, 8, 9, 12, 13, 14)]

    def day(i, state="quiet", c=None, widen=False):
        return {"day": days[i], "state": state, "countries_flagged": c or [],
                "spread_widening": widen}
    seq = [day(0, "idiosyncratic", ["Brazil"]), day(1), day(2), day(3, "systemic"),
           day(4), day(5), day(6), day(7), day(8), day(9)]
    s = ms.contagion_states(seq, 5)[0]
    check(s["status"] == "passed" and s["passed_on"] == days[3]
          and s["passed_to"] == "the basket",
          f"Brazil's shock of {days[0]} passed to the basket on {days[3]}, inside five "
          f"sessions")
    seq = [day(0, "idiosyncratic", ["Turkey"])] + [day(i) for i in range(1, 6)]
    s = ms.contagion_states(seq, 5)[0]
    check(s["status"] == "lapsed" and s["window_end"] == days[5],
          "five quiet sessions: the shock lapses at the window's end")
    seq = [day(0, "idiosyncratic", ["India"]), day(1), day(2, widen=True)]
    s = ms.contagion_states(seq, 5)[0]
    check(s["status"] == "passed" and s["passed_to"] == "EM spreads",
          "an EM spread widening at 2σ inside the window: passed to EM spreads")
    seq = [day(0, "idiosyncratic", ["Korea"]), day(1), day(2)]
    w = ms.contagion_states(seq, 5)[0]
    check(w["status"] == "watching" and w["window_end"] is None,
          "two sessions in: still watching")
    check(ms.contagion_line(w) and not ms.contagion_line(w, weekly=True)
          and ms.contagion_line(s, weekly=True),
          "the close prints every shock; the Weekly and Monthly only one that passed")


def group_g(res: dict) -> None:
    print(f"\n{LINE}\nG. THE WEEKLY'S LINES, WITHIN THE BUDGET\n{LINE}")
    from daily_cascade import stack as stack_mod, weekly_stack as ws, stack_render
    fake = dict(res)
    extra = [{"series": f"fixture.s{i}", "label": f"Series {i}", "kind": "series",
              "z1": 3.0 - 0.01 * i, "z5": 1.0, "max_abs_z": 3.0 - 0.01 * i,
              "flagged": True, "false_flag": {"k": i, "n": 9}, "n": 1500}
             for i in range(7)]
    fake["flags"] = sorted(res["flags"] + extra, key=lambda f: -f["max_abs_z"])
    fake["flags"].insert(1, {"series": "fred.yield_10y", "label": "10-year Treasury",
                             "kind": "series", "z1": 2.6, "z5": 2.1, "max_abs_z": 2.6,
                             "flagged": True, "false_flag": {"k": 2, "n": 7}, "n": 1500})
    fake["contagion"] = [{"country": "Brazil", "shock_date": "2026-10-06",
                          "status": "passed", "passed_on": "2026-10-08",
                          "passed_to": "the basket"},
                         {"country": "Korea", "shock_date": "2026-10-08",
                          "status": "watching", "passed_on": None, "passed_to": None}]
    wk = ws.misfit_week({}, None, {}, screen=fake)
    texts = [i["text"] for i in wk["items"] if i["key"].startswith("misfit:")]
    moves = [t for t in texts if " 1-day / " in t]
    check(len(moves) == 5, f"the top five flags by |z| ({len(moves)})")
    comp = next((n for n, t in enumerate(texts) if "the speed of the move" in t), None)
    ten = next((n for n, t in enumerate(texts) if t.startswith("10-year Treasury +")), None)
    check(comp is not None and ten is not None and comp == ten + 1,
          "SR-35's companion prints beside the 10-year's row")
    n_more = len(fake["flags"]) - 5
    check(f"{n_more} more past 2.5σ -- in the tables." in texts,
          f"the rest counted: '{n_more} more past 2.5σ -- in the tables.'")
    check(any("Brazil: the shock of 2026-10-06 passed to the basket" in t for t in texts)
          and not any(t.startswith("Korea") for t in texts),
          "the Weekly prints the shock that passed, not the one still watching")
    det = stack_mod.move_screen_detail(fake, "weekly")
    check(det and len(det[0]["table"]["rows"]) == len(fake["flags"])
          and "Moves past 2.5σ" in stack_render.details_html(det, "weekly"),
          f"the reference tier lists every flag ({len(fake['flags'])})")
    close = stack_mod.misfit_section({"market_state": {}}, None, fake)
    ct = [i["text"] for i in close["items"]]
    check(sum(1 for t in ct if " 1-day / " in t) == 3
          and any(t.startswith("Korea: a single-country shock") for t in ct),
          "the close prints its top three and every shock, watching included")
    from daily_cascade import readability
    check(all(readability.figure_count(t) <= 6 for t in moves),
          "each line is a handful of figures, inside a paragraph's budget")
    check(ms.em_calendar(DAY) == [], "the EM calendar is a template: nothing prints")
    td = Path(gate_mkdtemp("validate_move_screen_cal_"))
    cal = td / "em_calendar.yaml"
    cal.write_text("entries:\n  - {date: 2026-10-26, country: Brazil, event: Runoff, "
                   "pm_market_id: null, source: TSE}\n  - {date: 2027-01-05, country: "
                   "Chile, event: Rate decision, pm_market_id: null, source: BCCh}\n",
                   encoding="utf-8")
    got = ms.em_calendar(DAY, cal)
    check(len(got) == 1 and got[0]["country"] == "Brazil"
          and ms.calendar_line(got[0]) == "2026-10-26: Brazil -- Runoff [TSE].",
          "a seeded entry prints in its quarter; next quarter's does not")


def group_h() -> None:
    """H: the Quarterly's hook. A three-country basket that alternates (z = +/-1
    every session, never systemic), Brazil's ETF falls 8% mid-quarter, and the EM
    corporate spread widens 30 bp two sessions later: one member episode
    (idiosyncratic, contagion passed) and one spread event, oldest first; a
    quarter that ends before the shock has none."""
    print("\n-- H  the quarter's EM episodes (the Quarterly's hook)")
    td = gate_mkdtemp("validate_move_screen_q_")
    path = str(Path(td) / "store.db")
    days = bdays(QEND, 3)
    shock = days.index(QSHOCK)
    st = observations.ObservationStore(path)
    try:
        for n, (key, kind) in enumerate([
                ("fred.usd_brl", "fx"), ("yfinance.mkt_ewz", "etf"),
                ("fred.usd_mxn", "fx"), ("yfinance.mkt_eww", "etf"),
                ("fred.usd_zar", "fx"), ("yfinance.mkt_eza", "etf")]):
            v, vals = 10.0 + n, []
            for i, _ in enumerate(days):
                v *= math.exp(0.01 if i % 2 else -0.01)
                if key == "yfinance.mkt_ewz" and i == shock:
                    v *= math.exp(-0.08)
                vals.append(v)
            st.write_many(rows(key, None, days, vals))
        v, oas = 2.0, []
        for i, _ in enumerate(days):
            v += 0.01 if i % 2 else -0.01
            if i == shock + 2:
                v += 0.30
            oas.append(round(v, 4))
        st.write_many(rows("fred.em_corp_oas", None, days, oas))
    finally:
        st.close()
    st = observations.ObservationStore(path)
    try:
        eps = ms.quarter_episodes(st, f"{QEND}T23:00:00+00:00")
        before = ms.quarter_episodes(st, days[shock - 10])
    finally:
        st.close()
    keys = {"date", "series", "horizon", "z", "false_flag", "classification",
            "contagion_passed"}
    check(all(keys <= set(e) for e in eps),
          "every episode carries date, series, horizon, z, false_flag, "
          "classification, contagion_passed")
    mem = [e for e in eps if e["kind"] == "member"]
    spr = [e for e in eps if e["kind"] == "spread"]
    check(len(mem) == 1 and mem[0]["series"] == "yfinance.mkt_ewz"
          and mem[0]["date"] == QSHOCK and mem[0]["horizon"] in (1, 5)
          and mem[0]["z"] < -2.5,
          f"one member episode: EWZ on {QSHOCK}, its peak z past -2.5 "
          f"(the 5-day run after it is the same episode) -- {mem}")
    check(mem and mem[0]["classification"] == "idiosyncratic"
          and mem[0]["contagion_passed"] is True,
          "the shock is idiosyncratic and its contagion passed")
    check(len(spr) == 1 and spr[0]["series"] == "fred.em_corp_oas"
          and spr[0]["date"] == days[shock + 2] and spr[0]["contagion_passed"]
          and spr[0]["false_flag"] is None,
          f"one EM-spread contagion event, on the widening session -- {spr}")
    check([e["date"] for e in eps] == sorted(e["date"] for e in eps),
          "episodes are oldest first")
    check(before == [], "a quarter ending before the shock has no episodes")

def main() -> int:
    print(f"{LINE}\nTHE STORE-WIDE MOVE SCREEN AND THE EM SCREEN\n{LINE}")
    td = gate_mkdtemp("validate_move_screen_")
    path = str(Path(td) / "store.db")
    seed_store(path)
    res = group_a(path)
    group_b()
    group_c()
    group_d(path, res)
    group_e()
    group_f()
    group_g(res)
    group_h()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
