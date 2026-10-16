"""
Validation gate for the standing three-timeframe ES block (ST-R6.45, Batch 6
item 45; docs/briefs/st-r6-45-notes.md). FIXTURES ONLY: every store is the
gate's own, seeded in a temporary directory; no fetch, no model (a stub client
stands in), no live store.

  A  THE CONTRACT. CME's rule: ESZ6 for 16 Oct 2026, its roll on 10 Dec, ESH7
     from that session; Yahoo's forms normalised; a pull's recorded Yahoo
     contract outranks the rule.
  B  THE INDICATORS by hand: the seeded EMA, MACD on a flat series, money flow
     on three bars, VWAP, the least-squares trend line.
  C  A SYNTHETIC ES DAY gives the three windows' numbers: the session's open,
     high, low, last, change and VWAP worked out in the comments; twelve 2-hour
     bars a day; the position window's n and its absence below the minimum; the
     levels nearest above and below, merged within the distance.
  D  A ROLL DAY keeps the contract right: ESZ6 to ESH7 on 10 Dec with a 50-point
     gap and no real move -- the swing window is shifted across it (a flat
     trend, not a 50-point rally), the roll and its gap printed; Yahoo's later
     switch moves the roll; a print across the roll is not scored.
  E  THE 07:00 BLOCK READS ONLY STORED BARS: yfinance poisoned, the block
     built; a bar stored after the cutoff changes nothing; the prior full
     session's value area and POC are its reference; the 06:45 pull keeps
     18:00 ET onward, drops a bar still open and records the contract.
  F  THE READ CARRIES ITS LEAN: the LEAN line split off before the audit and
     returned beside the prose; a reply without it, or with a forecast, is
     withheld; a figure not in the data is withheld by the numeral audit.
  G  THE LEDGER scores a held, a broken and an untested level, and a resolved
     and an unresolved lean, on the bars after the print; a re-run writes
     nothing; a scored row is never rewritten; a withheld read logs no lean;
     the 16:45 block's "since 07:00" review scores the morning's print in
     memory and writes nothing.
  H  THE PRINT: the read first, then the levels table with the price now in
     the middle, the windows, the contract and the dealer row "after the 6b
     engine"; the read counts in the prose budget; no chart; the Weekly's
     panel carries the position window and the week's ledger.

    python tools/validate_es_block.py
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gate_tmp import mkdtemp as gate_mkdtemp  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78


def check(c: bool, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def session_bars(day: str, price, vol=100.0, avail_lag_min: int = 1,
                 step: float = 0.25) -> list[dict]:
    """The futures day's 276 five-minute bars for `day`; `price(i)` is bar i's
    open. close = open + step (0.25), high = open + 0.75, low = open - 0.5."""
    from altdata import bars as bars_mod
    first, last, n = bars_mod.session_window("es", day)
    t0 = dt.datetime.fromisoformat(first)
    out = []
    for i in range(n):
        t = t0 + dt.timedelta(minutes=5 * i)
        o = float(price(i))
        out.append({"instrument": "es", "symbol": "ES=F", "interval": "5m",
                    "observed_at": t.isoformat(), "open": o, "high": o + 0.75,
                    "low": o - 0.5, "close": o + step,
                    "volume": float(vol(i)) if callable(vol) else float(vol),
                    "available_at": (t + dt.timedelta(minutes=5 + avail_lag_min)).isoformat(),
                    "source": "yfinance"})
    return out


def seeded_store(td: str, name: str, days: dict):
    """A bars store holding {day: rows}."""
    from altdata import bars as bars_mod
    st = bars_mod.BarStore(str(Path(td) / name), create=True)
    for rows in days.values():
        st.write_many(rows)
    return st


def sessions_back(day: str, n: int) -> list[str]:
    from altdata import volume_profile as vp
    return vp.trailing_sessions(day, n)


# ---------------------------------------------------------------------------
def group_a(es) -> None:
    head("A. THE CONTRACT")
    c = es.contract_for("2026-10-16")
    check(c["contract"] == "ESZ6" and c["roll_date"] == "2026-12-10"
          and c["expiry"] == "2026-12-18" and c["next"] == "ESH7",
          f"16 Oct 2026: ESZ6, expiring 18 Dec, rolling 10 Dec (eight days "
          f"before), then ESH7 ({c})")
    check(es.contract_for("2026-12-09")["contract"] == "ESZ6"
          and es.contract_for("2026-12-10")["contract"] == "ESH7",
          "the session dated on the roll date is the next contract's")
    h7 = es.contract_for("2026-12-10")
    check(h7["roll_date"] == "2027-03-11" and h7["next"] == "ESM7",
          f"ESH7 expires 19 Mar 2027 and rolls 11 Mar ({h7['roll_date']})")
    check([es._normalise_yahoo(x) for x in ("ESZ26.CME", "ESZ6", "ESH2027", "SPY", None)]
          == ["ESZ6", "ESZ6", "ESH7", None, None],
          "Yahoo's contract forms normalise to ESZ6; anything else is not a contract")
    conn = sqlite3.connect(":memory:")
    es.record_contract(conn, "2026-12-10", "ESZ26.CME", "2026-12-10T10:45:00+00:00")
    got = es.contracts_of(["2026-12-09", "2026-12-10", "2026-12-11"], conn,
                          "2026-12-11T00:00:00+00:00")
    check(got["2026-12-10"] == {"contract": "ESZ6", "source": "yahoo"}
          and got["2026-12-11"]["source"] == "rule",
          "a pull's recorded Yahoo contract outranks CME's rule for its session")
    early = es.contracts_of(["2026-12-10"], conn, "2026-12-10T10:00:00+00:00")
    check(early["2026-12-10"]["source"] == "rule",
          "and only once it was recorded: an as-of read before the pull sees the rule")


def group_b(es) -> None:
    head("B. THE INDICATORS, BY HAND")
    # EMA(3) of 1..5: seed mean(1,2,3) = 2; k = 0.5; 4*0.5 + 2*0.5 = 3; 5*0.5 + 3*0.5 = 4.
    check(es.ema([1, 2, 3, 4, 5], 3) == [None, None, 2.0, 3.0, 4.0],
          "EMA(3) of 1..5 is seeded with the mean of the first three: -, -, 2, 3, 4")
    m = es.macd([100.0] * 40)
    check(abs(m["macd"]) < 1e-9 and abs(m["hist"]) < 1e-9,
          "MACD(12,26,9) of a flat series is zero, line and histogram")
    check("absent" in es.macd([1.0] * 33) and "absent" not in es.macd([1.0] * 34),
          "MACD needs 26 + 9 - 1 = 34 closes; 33 is absent with the reason")
    # Three bars, h = l = c: typical 10, 11, 10.5; volume 100, 200, 300; period 2.
    # Up 11*200 = 2200; down 10.5*300 = 3150; MFI = 100 - 100/(1 + 2200/3150) = 41.12.
    bars = [{"high": p, "low": p, "close": p, "volume": v}
            for p, v in ((10, 100), (11, 200), (10.5, 300))]
    mf = es.money_flow(bars, 2)
    check(abs(mf["value"] - 41.1215) < 1e-3, f"money flow on three bars: 41.12 ({mf})")
    check("absent" in es.money_flow(bars, 14), "money flow needs period + 1 bars")
    # VWAP of 10 x 100 and 20 x 300 = 7000 / 400 = 17.5.
    check(es.vwap([{"high": 10, "low": 10, "close": 10, "volume": 100},
                   {"high": 20, "low": 20, "close": 20, "volume": 300}]) == 17.5,
          "VWAP: 10 on 100 and 20 on 300 is 17.5")
    t = es.trend([1.0, 3.0, 5.0, 7.0])
    check(abs(t["slope"] - 2) < 1e-12 and abs(t["value"] - 7) < 1e-12
          and abs(t["r2"] - 1) < 1e-12,
          "the trend line through 1, 3, 5, 7: slope 2 a bar, 7 at the last bar, R² 1")


def group_c(es, td: str) -> None:
    head("C. A SYNTHETIC ES DAY: THE THREE WINDOWS' NUMBERS")
    day = "2026-10-16"
    days = sessions_back(day, 40)
    # Every session opens at 7700 and rises 0.25 a bar, constant volume 100.
    data = {d: session_bars(d, lambda i: 7700 + 0.25 * i) for d in days}
    st = seeded_store(td, "c.db", data)
    cutoff = "2026-10-16T21:30:00+00:00"          # 17:30 ET: the day is whole
    blk = es.compute(st, day, cutoff, slot="close")
    s = blk["windows"]["session"]
    # 276 bars; open 7700; last close 7700 + 0.25*275 + 0.25 = 7769.00; high
    # 7700 + 68.75 + 0.75 = 7769.50; low 7699.50; change 69.00. Typical price =
    # open + (0.75 - 0.5 + 0.25)/3 = open + 0.1667, constant volume, so VWAP =
    # mean(open) + 0.1667 = 7700 + 0.25*137.5 + 0.1667 = 7734.54.
    check((s["n_bars"], s["open"], s["high"], s["low"], s["last"], s["change"])
          == (276, 7700.0, 7769.5, 7699.5, 7769.0, 69.0),
          f"session: 276 bars, open 7700, high 7769.50, low 7699.50, last 7769, "
          f"+69 ({s.get('n_bars')}, {s.get('open')}, {s.get('high')}, {s.get('low')}, "
          f"{s.get('last')}, {s.get('change')})")
    check(s["vwap"] == 7734.54, f"session VWAP 7734.54 ({s['vwap']})")
    check(s["profile"].get("poc") is not None and s["profile"]["val"] < s["profile"]["poc"]
          < s["profile"]["vah"], f"session profile from VP-1: POC inside the value area "
          f"({s['profile'].get('val')}, {s['profile'].get('poc')}, {s['profile'].get('vah')})")
    check(s["macd"].get("hist") is not None and s["money_flow"] is not None,
          f"session MACD and money flow present (hist {s['macd'].get('hist')}, "
          f"MF {s['money_flow']})")
    w = blk["windows"]["swing"]
    check(w["n_bars"] == 60 and w["bar_hours"] == 2 and len(w["sessions"]) == 5,
          f"swing: five sessions of twelve 2-hour bars (the 23-hour day's last is "
          f"one hour) = 60 ({w['n_bars']})")
    two = es.buckets(data[day], 2, day)
    check(len(two) == 12 and two[0]["open"] == 7700.0 and two[-1]["close"] == 7769.0
          and two[0]["volume"] == 2400.0 and two[-1]["volume"] == 1200.0,
          "2-hour bars anchored at 18:00 ET: 24 bars in the first, 12 in the last")
    check(w["trend"]["value"] is not None and "slope" in w["trend"],
          f"swing trend line: value {w['trend'].get('value')}, slope "
          f"{w['trend'].get('slope')} a bar, R² {w['trend'].get('r2')}")
    p = blk["windows"]["position"]
    check(p.get("n_sessions") == 40 and p["sessions_wanted"] == 63
          and p["profile"].get("note") == "approximated from daily bars",
          f"position: 40 of 63 sessions stored, its profile approximated from daily "
          f"bars ({p.get('n_sessions')})")
    st.close()
    st2 = seeded_store(td, "c2.db", {d: data[d] for d in days[-30:]})
    p2 = es.compute(st2, day, cutoff)["windows"]["position"]
    check(p2.get("absent") == "30 complete sessions of 63 stored; the position window "
          "needs 35", f"below 35 sessions the position window is absent ({p2.get('absent')})")
    st2.close()
    lv = blk["levels"]
    check(len(lv["above"]) <= 3 and len(lv["below"]) <= 3
          and all(r["price"] > blk["last"] for r in lv["above"])
          and all(r["price"] < blk["last"] for r in lv["below"])
          and [r["price"] for r in lv["below"]] == sorted([r["price"] for r in lv["below"]],
                                                       reverse=True),
          f"at most three levels above and three below the last price, nearest first "
          f"({[r['price'] for r in lv['above']]} / {[r['price'] for r in lv['below']]})")
    hand = {"session": {"profile": {"poc": 100.0, "vah": 104.0, "val": 96.0},
                        "vwap": 101.0},
            "swing": {"profile": {"poc": 110.0, "vah": 120.0, "val": 90.0,
                                  "hvn": [97.0], "lvn": []},
                      "trend": {"value": 111.5}}}
    got = es.levels(hand, 102.0, es.load_config())
    check([r["price"] for r in got["above"]] == [104.0, 110.75, 120.0]
          and got["above"][1]["sources"] == ["swing POC", "swing trend line"]
          and [r["price"] for r in got["below"]] == [100.5, 96.5, 90.0],
          f"levels within 2 points merge, every source named (above "
          f"{[(r['price'], r['label']) for r in got['above']]}; below "
          f"{[(r['price'], r['label']) for r in got['below']]})")
    check(blk["dealer"] == "dealer levels in ES: after the 6b engine",
          "the dealer row waits for the 6b engine (ST-R6.45c)")


def group_d(es, td: str) -> None:
    head("D. A ROLL DAY KEEPS THE CONTRACT RIGHT")
    day = "2026-12-11"
    days = sessions_back(day, 15)
    # Flat at 7800 under ESZ6; flat at 7850 from the 10 Dec session (ESH7): the
    # 50 points are the calendar spread, not a move.
    # Flat bars (close = open), so the gap at the switch is the spread exactly.
    data = {d: session_bars(d, (lambda i: 7800.0) if d < "2026-12-10" else (lambda i: 7850.0),
                            step=0.0)
            for d in days}
    st = seeded_store(td, "d.db", data)
    blk = es.compute(st, day, "2026-12-11T23:00:00+00:00", slot="close")
    c = blk["contract"]
    check(c["in_force"] == "ESH7" and c["source"] == "rule" and c["agree"],
          f"11 Dec 2026: ESH7 in force by CME's rule ({c})")
    w = blk["windows"]["swing"]
    rolls = w.get("rolls") or []
    check(len(rolls) == 1 and rolls[0]["from"] == "ESZ6" and rolls[0]["to"] == "ESH7"
          and rolls[0]["session"] == "2026-12-10" and rolls[0]["gap"] == 50.0,
          f"the swing window names the roll: ESZ6 to ESH7 on 10 Dec, gap +50 ({rolls})")
    check(abs(w["trend"]["slope"]) < 1e-6 and w["open"] == 7850.0 and w["change"] == 0.0,
          f"shifted across the roll: a flat trend and no 50-point rally (slope "
          f"{w['trend']['slope']}, open {w['open']}, change {w['change']})")
    check(abs(w["macd"]["hist"]) < 1e-6,
          f"and MACD reads no move ({w['macd'].get('hist')})")
    from daily_cascade import es_read
    ln = " ".join(es_read.lines(blk))
    check("spans the ESZ6 to ESH7 roll on 2026-12-10: earlier bars shifted +50.00" in ln,
          "the roll and its gap print beside the window")
    # Yahoo still served ESZ6 on the 10th: the switch moves to the 11th, where
    # the fixture shows no gap (its 10 Dec bars are already at the new price).
    es.record_contract(st.conn, "2026-12-10", "ESZ26.CME", "2026-12-10T11:45:00+00:00")
    blk2 = es.compute(st, day, "2026-12-11T23:00:00+00:00", slot="close")
    r2 = blk2["windows"]["swing"].get("rolls") or []
    check([x["session"] for x in r2] == ["2026-12-11"] and r2[0]["gap"] == 0.0,
          f"Yahoo's recorded contract moves the switch to the session it changed "
          f"({r2})")
    st.close()
    # A print on the 9th (ESZ6) scored on the 10th (ESH7): not scored.
    st3 = seeded_store(td, "d3.db", data)
    blk9 = es.compute(st3, "2026-12-09", "2026-12-09T22:00:00+00:00", slot="close")
    n = es.record(blk9, "up", "run-d", conn=st3.conn, printed_at="2026-12-09T21:45:00+00:00")
    es.resolve_due("2026-12-10T23:00:00+00:00", conn=st3.conn, store=st3)
    oc = {r[0] for r in st3.conn.execute("SELECT outcome FROM es_ledger")}
    check(n > 1 and oc == {"not_scored"},
          f"a print across the roll is not scored: its levels are the old contract's "
          f"({n} rows, outcomes {oc})")
    st3.close()


def group_e(es, td: str) -> None:
    head("E. THE 07:00 BLOCK READS ONLY STORED BARS")
    import altdata

    def poisoned(*a, **k):
        raise AssertionError("the 07:00 block fetched")
    saved = altdata.import_yfinance
    altdata.import_yfinance = poisoned
    sys.modules["yfinance"] = None                 # an import now raises
    try:
        day = "2026-10-16"
        days = sessions_back(day, 40)
        data = {d: session_bars(d, lambda i: 7700 + 0.25 * i) for d in days}
        st = seeded_store(td, "e.db", data)
        cutoff = "2026-10-16T11:00:00+00:00"       # 07:00 ET
        blk = es.compute(st, day, cutoff, slot="morning")
        s = blk["windows"]["session"]
        # 18:00 ET (22:00Z) to 07:00 ET: 13 hours, 156 slots; the 06:55 bar is
        # available at 07:01 (close + 1 minute), after the cutoff: 155 bars.
        check(blk["state"] == "ok" and s["n_bars"] == 155,
              f"built without a fetch: the overnight session so far, 155 bars "
              f"({blk['state']}, {s.get('n_bars')})")
        pr = blk["windows"]["prior_session"]
        check(pr["sessions"] == ["2026-10-15"] and pr["profile"].get("poc") is not None,
              f"the prior full session's value area and POC are the reference "
              f"({pr['profile'].get('val')}-{pr['profile'].get('vah')}, POC "
              f"{pr['profile'].get('poc')})")
        cands = [lab for _, lab in es._candidates(blk["windows"])]
        check({"prior session POC", "prior session value-area high",
               "prior session value-area low"} <= set(cands),
              "the prior session's POC and value area enter the levels' candidates")
        # A bar stored later, available after the cutoff, changes nothing.
        late = session_bars(day, lambda i: 9000.0)[200:201]
        late[0]["available_at"] = "2026-10-16T12:00:00+00:00"
        st.write_many([{**late[0], "observed_at": "2026-10-16T10:58:00+00:00"}])
        again = es.compute(st, day, cutoff, slot="morning")
        check(json.dumps(again, sort_keys=True, default=str)
              == json.dumps(blk, sort_keys=True, default=str),
              "a bar available after the cutoff leaves the block byte-identical")
        st.close()
    finally:
        altdata.import_yfinance = saved
        sys.modules.pop("yfinance", None)
    # The 06:45 pull: a fake source with bars from 17:00 ET the evening before
    # (outside the window) to a bar still open at the fetch.
    import pandas as pd
    from altdata import bars as bars_mod
    idx = pd.date_range("2026-10-15T21:00:00Z", "2026-10-16T10:45:00Z", freq="5min")
    df = pd.DataFrame({"Open": 7700.0, "High": 7701.0, "Low": 7699.0, "Close": 7700.5,
                       "Volume": 10.0}, index=idx)
    st = bars_mod.BarStore(str(Path(td) / "pull.db"), create=True)
    rep = bars_mod.pull_overnight("2026-10-16", store=st,
                                  fetcher=lambda sym, **kw: df,
                                  contract_fetcher=lambda sym: "ESZ26.CME",
                                  fetched_at="2026-10-16T10:47:00+00:00")
    r = rep["instruments"]["es"]
    # 22:00Z (18:00 ET) to 10:40Z inclusive = 153 bars; 10:45Z is still open.
    check(r.get("5m") == 153 and r.get("dropped_still_open") == 1
          and r.get("first") == "2026-10-15T22:00:00+00:00",
          f"the 06:45 pull keeps 18:00 ET onward and drops the bar still open ({r})")
    rows = st.read("es", "5m")
    check(len(rows) == 153 and {x["available_at"] for x in rows}
          == {"2026-10-16T10:47:00+00:00"}, "stamped at the fetch")
    cr = [tuple(x) for x in st.conn.execute(
        "SELECT rule_contract, roll_date, yahoo_contract FROM es_contract")]
    check(cr == [("ESZ6", "2026-12-10", "ESZ26.CME")] and r["contract"]["rule"] == "ESZ6",
          f"and records the contract in force, its roll date and Yahoo's report ({cr})")
    st.close()


class Stub:
    """A model that answers with fixed text and records the prompt."""

    def __init__(self, texts):
        self.texts = list(texts)
        self.calls = 0
        outer = self

        class _M:
            @staticmethod
            def create(**kw):
                outer.calls += 1
                t = outer.texts[min(outer.calls - 1, len(outer.texts) - 1)]

                class _B:
                    type = "text"
                    text = t

                class _R:
                    content = [_B()]
                    model = "stub"
                    stop_reason = "end_turn"
                    usage = None
                return _R()
        self.messages = _M()


def _small_block(es):
    """A hand block: last 7769, levels 7800 above and 7734.54 below."""
    return {"state": "ok", "slot": "close", "session": "2026-10-16", "last": 7769.0,
            "contract": {"in_force": "ESZ6", "source": "rule", "rule": "ESZ6",
                         "roll_date": "2026-12-10", "next": "ESH7",
                         "next_roll_date": "2026-12-10", "agree": True},
            "windows": {"session": {"window": "session", "last": 7769.0, "vwap": 7734.54,
                                    "profile": {"poc": 7740.0, "vah": 7760.0, "val": 7720.0},
                                    "macd": {"hist": 1.2, "hist_prev": 0.8},
                                    "money_flow": 66.0},
                        "swing": {"window": "swing", "absent": "bars incomplete (n=1 of 60)"},
                        "position": {"window": "position", "absent": "n=30"}},
            "levels": {"above": [{"price": 7800.0, "label": "swing POC", "distance": 31.0,
                                  "side": "above", "sources": ["swing POC"]}],
                       "below": [{"price": 7734.54, "label": "session VWAP",
                                  "distance": -34.46, "side": "below",
                                  "sources": ["session VWAP"]}]},
            "dealer": es.DEALER_PENDING, "reasons": []}


def group_f(es) -> None:
    head("F. THE READ CARRIES ITS LEAN")
    from daily_cascade import es_read
    check(es_read.split_lean("Price sits above VWAP.\nLEAN: up") ==
          ("Price sits above VWAP.", {"lean": "up"}),
          "the LEAN line is split off the prose")
    check(es_read.split_lean("Price sits above VWAP.")[1].get("lean") is None,
          "no LEAN line: no lean")
    blk = _small_block(es)
    good = ("ES at 7769 sits above the session VWAP at 7734.54, with the session "
            "MACD histogram rising; the swing POC at 7800 is the level above.\nLEAN: up")
    r = es_read.write(blk, client=Stub([good]))
    check(r["published"] and r["lean"] == "up" and "LEAN" not in r["text"],
          f"published with its lean beside the prose ({r.get('state')}: "
          f"{r.get('reason')})")
    stub = Stub(["ES at 7769 sits above the session VWAP at 7734.54."])
    r2 = es_read.write(blk, client=stub)
    check(not r2["published"] and "no LEAN line" in r2["reason"] and stub.calls == 2,
          f"a reply without the LEAN line is withheld after one retry ({r2['reason']})")
    r3 = es_read.write(blk, client=Stub([
        "ES at 7769 sits above VWAP; the swing POC at 7800 will hold as resistance.\n"
        "LEAN: down"]))
    check(not r3["published"] and "forecast" in r3["reason"],
          f"a forecast is withheld ({r3['reason']})")
    r4 = es_read.write(blk, client=Stub(["ES at 7769 sits 41.7 points under 7810.5.\n"
                                         "LEAN: none"]))
    check(not r4["published"] and r4["state"] in ("audit_failed",),
          f"a figure not in the data is withheld by the numeral audit ({r4['state']})")
    r5 = es_read.write({"state": "absent", "reason": "no bars"})
    check(not r5["published"] and r5["lean"] is None, "an absent block writes no read")


def group_g(es, td: str) -> None:
    head("G. THE LEDGER")
    day = "2026-10-16"
    prev = "2026-10-15"
    # The target session: open 7750, rises to 7790 by the end; one bar closes at
    # 7690 (below 7700) at bar 100.
    def px(i):
        return 7690.0 if i == 100 else 7750 + 40 * i / 275
    data = {day: session_bars(day, px)}
    st = seeded_store(td, "g.db", data)
    conn = st.conn
    base = {"state": "ok", "last": 7750.0, "contract": {"in_force": "ESZ6"}}
    # Evening print on the 15th (target the 16th): 7800 above (high reaches
    # 7790.75: within 1 point? no -- 9 points short: untested), 7700 below
    # (bar 100 closes 7690.25: broke), lean down.
    b1 = {**base, "session": prev, "slot": "close",
          "levels": {"above": [{"price": 7800.0, "label": "swing POC"}],
                     "below": [{"price": 7700.0, "label": "position VAL"}]}}
    # Morning print on the 16th: 7790.5 above (tested at 7790.75, no close
    # through 7791.0: held), lean up.
    b2 = {**base, "session": day, "slot": "morning",
          "levels": {"above": [{"price": 7790.5, "label": "session VAH"}], "below": []}}
    n1 = es.record(b1, "down", "r1", conn=conn, printed_at="2026-10-15T20:45:00+00:00")
    n2 = es.record(b2, "up", "r2", conn=conn, printed_at="2026-10-16T11:00:00+00:00")
    check((n1, n2) == (3, 2), f"each level and the lean logged unscored ({n1}, {n2})")
    check(es.record(b2, "up", "r2", conn=conn) == 0, "a re-run of the same edition writes nothing")
    tg = dict(conn.execute("SELECT slot, target_session FROM es_ledger WHERE kind='lean'"))
    check(tg == {"close": day, "morning": day},
          "the 16:45 print is scored on the next session, the 07:00 print on the one it opens")
    # 16:45, before the ledger is scored: the morning's print reviewed in memory.
    sm = es.since_morning(st, day, "2026-10-16T20:45:00+00:00", 7790.25, conn=conn)
    check(sm["ref_price"] == 7750.0 and sm["change"] == 40.25 and sm["lean"] == "up"
          and sm["lean_so_far"] == "resolved"
          and sm["levels"] == [{"label": "session VAH", "level": 7790.5, "side": "above",
                                "so_far": "held"}]
          and conn.execute("SELECT COUNT(*) FROM es_ledger WHERE outcome IS NOT NULL"
                           ).fetchone()[0] == 0,
          f"what changed since 07:00: +40.25, the lean resolved so far, the VAH held "
          f"so far -- in memory, nothing written ({sm})")
    from daily_cascade import es_read
    ln = " ".join(es_read.lines({"since_morning": sm, "windows": {}}))
    check("Since 07:00: +40.25 from 7,750.00; the morning's lean up, resolved so far."
          in ln, "and the close prints it")
    res = es.resolve_due("2026-10-16T21:30:00+00:00", conn=conn, store=st)
    got = {(r[0], r[1]): r[2] for r in conn.execute(
        "SELECT label, slot, outcome FROM es_ledger")}
    # Last close 7790.25 against 7750: +0.52% -- up resolves, down does not.
    check(got[("session VAH", "morning")] == "held"
          and got[("position VAL", "close")] == "broke"
          and got[("swing POC", "close")] == "untested",
          f"levels: held, broke and untested by the declared rules ({got})")
    check(got[("lean", "morning")] == "resolved" and got[("lean", "close")] == "unresolved",
          "leans: up resolved (+0.52% against a 0.25% band), down unresolved")
    check(res == {"scored": 5, "waiting": 0}, f"five rows scored ({res})")
    conn.execute("UPDATE es_ledger SET detail='kept' WHERE label='session VAH'")
    es.resolve_due("2026-10-16T22:30:00+00:00", conn=conn, store=st)
    check(conn.execute("SELECT detail FROM es_ledger WHERE label='session VAH'"
                       ).fetchone()[0] == "kept", "a scored row is never rewritten")
    n3 = es.record({**b2, "session": "2026-10-19"}, None, "r3", conn=conn)
    check(n3 == 1 and conn.execute("SELECT COUNT(*) FROM es_ledger WHERE kind='lean' AND "
                                   "printed_session='2026-10-19'").fetchone()[0] == 0,
          "a withheld read logs its levels and no lean")
    waiting = es.resolve_due("2026-10-19T21:30:00+00:00", conn=conn, store=st)
    check(waiting["waiting"] == 1, "a session with no bars waits for the next close")
    summ = es.ledger_summary(conn, [day, prev])
    check(summ["levels"] == {"held": 1, "broke": 1, "untested": 1}
          and summ["leans"] == {"resolved": 1, "unresolved": 1},
          f"the week's summary counts them ({summ})")
    st.close()


def group_h(es, td: str) -> None:
    head("H. THE PRINT")
    from daily_cascade import es_read, stack as stack_mod, stack_render
    blk = _small_block(es)
    read = {"published": True, "text": "ES at 7769 sits above the session VWAP.",
            "lean": "up", "state": "published"}
    ss = es_read.subsection(blk, read)
    rows = ss["table"]["rows"]
    check([r[0] for r in rows] == ["swing POC", "price now", "session VWAP"],
          "levels table: above, the price now in the middle, below")
    html = stack_render.subsection_html(ss, "session", stack_render._cadence("daily"))
    i_lead, i_tab = html.find("ES at 7769 sits above"), html.find("<table")
    check(0 <= i_lead < i_tab, "the read prints first, then the tables")
    check("dealer levels in ES: after the 6b engine" in html
          and "Contract in force ESZ6" in html,
          "the contract and the dealer row print under the tables")
    sec = {"claim": None, "paragraphs": [], "subsections": [ss]}
    check(stack_mod.section_words(sec) == stack_mod.words(read["text"]),
          "the read counts in the prose budget")
    check(not ss.get("charts_rendered") and "<img" not in html,
          "no chart: the close's chart budget is unchanged")
    wd = es_read.subsection(blk, {"published": False, "state": "audit_failed",
                                  "reason": "withheld: 1 figure", "lean": None})
    check(wd["lead"].startswith("The read was withheld")
          and stack_mod.section_words({"subsections": [wd]}) == 0,
          "a withheld read says so, and its note is not counted as prose")
    md = stack_render._md_sub(ss, stack_render._cadence("daily"), None)
    check(any("ES at 7769" in x for x in md), "the Markdown edition carries the read")
    from daily_cascade import morning_render
    mh = morning_render.es_section({"es_block": blk}, read)
    check(mh.find("ES at 7769") < mh.find("<table"), "the 07:00 section: the read, then the tables")
    # The Weekly's panel, over a seeded store.
    day = "2026-10-16"
    days = sessions_back(day, 40)
    st = seeded_store(td, "h.db", {d: session_bars(d, lambda i: 7700 + 0.25 * i)
                                    for d in days})
    es.record({**_small_block(es), "slot": "close"}, "up", "rw", conn=st.conn)
    wk = es_read.weekly_subsection(st, days[-5:], "2026-10-16T22:00:00+00:00")
    check(wk["table"]["rows"][0][0].startswith("Position (3 months, daily), n=40 of 63")
          and wk["tables"][0]["rows"][-1] == ["pending", 3],
          f"the Weekly's panel: the position window and the week's ledger "
          f"({wk['table']['rows'][0][0]}; {wk['tables'][0]['rows'][-1]})")
    st.close()
    src = (REPO / "altdata" / "es_block.py").read_text(encoding="utf-8") + (
        REPO / "daily_cascade" / "es_read.py").read_text(encoding="utf-8")
    check("import_yfinance" not in src and "yfinance" not in src.replace(
        "Yahoo", ""), "neither module can fetch")


def main() -> int:
    from altdata import es_block as es
    td = gate_mkdtemp(prefix="validate_es_block_")
    group_a(es)
    group_b(es)
    group_c(es, td)
    group_d(es, td)
    group_e(es, td)
    group_f(es)
    group_g(es, td)
    group_h(es, td)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
