"""
B76 (session B, 26 Oct 2026): signal-triage Batch 16 item 89(b), trend-signal
breadth (written as the triage chat's 82(b) in the round-7 order; ruled 26 Oct
2026).

  A  THE SIGNAL. A synthetic rising series reads +1 at all four lookbacks and
     "trending"; a falling one -1 and "trending"; under 250 closes "insufficient
     history"; the running mean and the window's availability by hand.
  B  REVERSING. A long rise turned down so the 20-session sign flips against the
     250-session: "reversing" inside five sessions, "mixed" after; the flips
     counted.
  C  THE STORE. A seeded temporary store: compute writes the signs, the week's
     flips and the share, each available no earlier than its inputs; a dry run
     and a re-run write nothing; the fallback key leads only when the first is
     absent; a market with no key prints "not stored" and leaves n ("of n held");
     the features pass computes recent days only, never the history.
  D  THE LEDGER. The pre-registration block at the SHA-256 the config records
     and the file prints; the edition grants nothing; the rule's INSUFFICIENT,
     PASS and FAIL on fixtures, the halves' sign condition included.
  E  PLACEMENT. The Weekly's and the Monthly's Positioning & flows carry the
     table (no paragraph), the daily close does not; the table's columns.
  F  HYGIENE. The 64 signs and the two breadth keys registered, trigger-
     ineligible and barred from the market-state object (named in neither its
     config nor regime.py); no fetch, vendor or new symbol in the module; the
     gate in the Makefile's list.

Synthetic fixtures only: no live store, no network, no model.

    python tools/validate_trend_breadth.py
"""

from __future__ import annotations

import datetime as dt
import hashlib
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gate_tmp  # noqa: E402

from altdata import derived, observations  # noqa: E402
from altdata import trend_breadth as tb  # noqa: E402

GATE_KIND = "code"

PASS = FAIL = 0
LINE = "=" * 78
CFG = tb.config()
LBS = tb.lookbacks(CFG)
NOW = "2026-10-26T23:00:00+00:00"
LEDGER = REPO / CFG["ledger"]["path"]


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


def weekdays(n: int, end: str = "2026-10-23") -> list[str]:
    out, d = [], dt.date.fromisoformat(end)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= dt.timedelta(days=1)
    return out[::-1]


def pts(values: list[float], days: list[str]) -> list[tuple]:
    return [(d, v, f"{d}T21:00:00+00:00", "observed") for d, v in zip(days, values)]


def rising(n: int) -> list[float]:
    return [100.0 + 0.1 * i for i in range(n)]


def turned(n: int, down: int) -> list[float]:
    """A steady rise, then `down` sessions falling hard enough to put the close
    under its 20-session mean while still over its 250-session one."""
    v = rising(n - down)
    for _ in range(down):
        v.append(v[-1] - 1.2)
    return v


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE SIGNAL")
    days = weekdays(300)
    up = tb.signs(pts(rising(300), days), LBS)
    check(all(up[-1]["s"][lb] == 1 for lb in LBS) and tb.state_at(up, len(up) - 1) == "trending",
          "a synthetic rising series reads + at 20, 60, 120 and 250 sessions: trending")
    dn = tb.signs(pts([200.0 - 0.1 * i for i in range(300)], days), LBS)
    check(all(dn[-1]["s"][lb] == -1 for lb in LBS) and tb.state_at(dn, len(dn) - 1) == "trending",
          "a falling one reads − at all four: trending (the direction is in the signs)")
    check(up[248]["s"][250] is None and tb.state_at(up, 248) == "insufficient history"
          and up[249]["s"][250] == 1,
          "under 250 closes the 250-session sign is absent: insufficient history")
    vals = [5.0, 7.0, 6.0, 9.0, 1.0]
    s = tb.signs(pts(vals, days[:5]), [3])
    check([r["s"][3] for r in s] == [None, None, 0, 1, -1],
          "the sign by hand: 6 against mean(5,7,6)=6 is 0; 9 against 7.33 is +; 1 against 5.33 is −")
    # A late vintage of the third close (available on 9 Nov) holds the window's
    # availability until it leaves the window.
    av = ["2026-11-01", "2026-11-02", "2026-11-09", "2026-11-03", "2026-11-04", "2026-11-05"]
    late = [(d, float(i), a, None) for i, (d, a) in enumerate(zip(days[:6], av))]
    s = tb.signs(late, [3])
    check(s[2]["avail"][3] == s[3]["avail"][3] == s[4]["avail"][3] == "2026-11-09"
          and s[5]["avail"][3] == "2026-11-05",
          "a sign is available when the latest close in its window is (the window's max)")
    check(CFG["version"] == "trend-breadth-v1" and LBS == [20, 60, 120, 250]
          and CFG["reversal_sessions"] == 5,
          "the declared lookbacks (20, 60, 120, 250) and the five-session reversal window")


def group_b() -> None:
    head("B. REVERSING")
    days = weekdays(310)
    s = tb.signs(pts(turned(305, 4), days[:305]), LBS)
    t = len(s) - 1
    check(s[t]["s"][20] == -1 and s[t]["s"][250] == 1 and tb.state_at(s, t) == "reversing",
          f"a flip of the 20-session sign against the 250 inside five sessions: reversing "
          f"({s[t]['s']})")
    flat = turned(305, 4) + [turned(305, 4)[-1] - 0.01 * i for i in range(1, 6)]
    s2 = tb.signs(pts(flat, days), LBS)
    t2 = len(s2) - 1
    check(s2[t2]["s"][20] == -1 and s2[t2]["s"][250] == 1 and tb.state_at(s2, t2) == "mixed",
          "the same split with the flip six or more sessions back: mixed")
    fl = tb.flips(s, LBS)
    check(any(d == s[t - 3]["day"] and lb == 20 for d, lb, _ in fl)
          or any(lb == 20 for d, lb, _ in fl if d >= s[t - 3]["day"]),
          "the flip is counted, on its own day and lookback")
    series = {"a": s, "b": tb.signs(pts(rising(300), days[:300]), LBS)}
    b = tb.breadth_on(series, s[t]["day"])
    check(b and b["n"] == 2 and b["reversing"] == 1 and abs(b["share"] - 50.0) < 1e-9
          and b["flips"] >= 1,
          f"the reversing share across held markets: 1 of 2, 50% ({b})")
    stale = tb.breadth_on({"a": s}, (dt.date.fromisoformat(s[t]["day"])
                                     + dt.timedelta(days=8)).isoformat())
    check(stale is None, "a close more than seven days old carries no state that day")


def _seed(db: str, with_yf_eur: bool = False) -> None:
    days = weekdays(320)
    rows = []
    for d, v in zip(days, rising(320)):
        rows.append({"registry_key": "fred.yield_10y", "instrument": None, "observed_at": d,
                     "available_at": f"{d}T21:00:00+00:00", "value": v / 25.0, "source": "fred"})
    for d, v in zip(days, turned(320, 3)):
        rows.append({"registry_key": "fred.usd_eur", "instrument": None, "observed_at": d,
                     "available_at": f"{d}T21:30:00+00:00", "value": v / 100.0, "source": "fred"})
    if with_yf_eur:
        for d, v in zip(days, rising(320)):
            rows.append({"registry_key": "yfinance.mkt_eurusd", "instrument": None,
                         "observed_at": d, "available_at": f"{d}T22:00:00+00:00",
                         "value": v / 100.0, "source": "yfinance"})
    with observations.ObservationStore(db) as st:
        st.write_many(rows)


def group_c() -> None:
    head("C. THE STORE")
    db = str(Path(gate_tmp.mkdtemp("trend_breadth_")) / "chester.db")
    _seed(db)
    with observations.ObservationStore(db) as st:
        dry = tb.compute(as_of=NOW, store=st, dry_run=True)
        check(dry["written"] == 0 and dry["computed"] > 0 and st.latest_as_of(tb.SHARE_KEY, NOW) is None,
              f"the backfill's dry run counts ({dry['computed']} rows) and writes nothing")
        r = tb.compute(as_of=NOW, store=st)
        check(r["written"] == r["computed"] and set(r["by_key"]) >= {
            "trend.ust_10y.20", "trend.ust_10y.250", "trend.eurusd.250", tb.SHARE_KEY, tb.FLIPS_KEY},
            "the backfill writes the signs, the share and the week's flips")
        again = tb.compute(as_of=NOW, store=st)
        check(again["written"] == 0, "a re-run writes nothing (unchanged rows are dropped)")
        last = st.latest_as_of("trend.ust_10y.250", NOW)
        src = st.latest_as_of("fred.yield_10y", NOW)
        check(last["observed_at"][:10] == src["observed_at"][:10]
              and last["available_at"] >= src["available_at"] and last["source"] == "calc",
              "a sign is observed on its close's day and available no earlier than it")
        rd = tb.read(st, NOW)
        by = {m["id"]: m for m in rd["markets"]}
        check(by["ust_10y"]["state"] == "trending" and by["eurusd"]["state"] == "reversing"
              and by["eurusd"]["key"] == "fred.usd_eur",
              "the read: the 10-year trending, EUR/USD reversing from H.10 (the fallback key)")
        check(by["audusd"]["state"] == tb.NOT_STORED and rd["held"] == 2 and rd["named"] == 16
              and rd["with_state"] == 2,
              "a market with no stored key prints 'not stored' and leaves n (2 held of 16)")
        ln = tb.lines(rd)
        check(any("1 of 2 held" in x and "(50% stored on" in x for x in ln)
              and any(x.startswith("Not stored: ") and "the count is of 2 held, not 16" in x
                      for x in ln)
              and any("History from" in x and "n = 2" in x for x in ln),
              f"the lines print the share 'of n held', the gaps, the window and n ({ln[0][:90]})")
        t = tb.table(rd)
        check(t["columns"] == ["Market", "20-session", "60-session", "120-session",
                               "250-session", "State", "As of"]
              and len(t["rows"]) == 16 and t["rows"][1][1:5] == ["+", "+", "+", "+"],
              "the table: each market's four signs, its state and its day")
    db2 = str(Path(gate_tmp.mkdtemp("trend_breadth_yf_")) / "chester.db")
    _seed(db2, with_yf_eur=True)
    with observations.ObservationStore(db2) as st:
        key, _ = tb.closes(st, next(m for m in CFG["markets"] if m["id"] == "eurusd"), NOW)
        check(key == "yfinance.mkt_eurusd", "the first declared key leads when it is stored")
        first = tb.default_first_day(st, NOW)
        check(first == "2026-09-26", f"with nothing stored the features pass starts 30 days "
                                     f"back, never the whole history ({first})")
        from altdata import market_features as mf               # noqa: PLC0415
        out = mf.compute(as_of=NOW, store=st, dry_run=True)
        tbr = out.get("trend_breadth") or {}
        check(not tbr.get("error") and tbr.get("first_day") == first and tbr.get("written") == 0,
              f"it rides the features pass after ST-5's, recent days only ({tbr.get('first_day')})")
    ro = tb.open_ro(db2)
    try:
        try:
            ro.conn.execute("CREATE TABLE x (a)")
            wrote = True
        except Exception:                                       # noqa: BLE001
            wrote = False
        check(not wrote, "show and ledger open the store read-only")
    finally:
        ro.conn.close()


def group_d() -> None:
    head("D. THE LEDGER")
    text = LEDGER.read_text(encoding="utf-8")
    sha = hashlib.sha256(tb.prereg_bytes(text)).hexdigest()
    check(sha == CFG["ledger"]["prereg_sha256"] and f"`{sha}`" in text,
          f"the pre-registration block at the SHA-256 the config records and the file prints ({sha[:12]})")
    blk = tb.prereg_bytes(text).decode("utf-8")
    check("20.0%" in blk and "at least 30 weeks" in blk and "2.0" in blk and "at least 5 markets" in blk
          and "never edited" in blk and "Rights: none" in blk,
          "the block states the rule's numbers as the config holds them, and grants nothing")
    check(CFG["ledger"]["high_share"] == 20.0 and CFG["ledger"]["min_weeks"] == 30
          and CFG["ledger"]["t_pass"] == 2.0 and CFG["ledger"]["min_markets"] == 5,
          "the config's numbers are the block's")
    check("**Rights:** none." in text and "## Edition: laptop first edition" in text
          and re.search(r"\*\*n:\*\* \d+ weeks; markets held \d+ of 16", text),
          "the first edition prints its n, the markets held and grants nothing")
    days = weekdays(200)

    def sample(n_hi: int, n_lo: int, hi_ret: float, lo_ret: float, flip_half: bool = False):
        out = []
        for i in range(n_hi + n_lo):
            hi = i % 2 == 0 if i < 2 * min(n_hi, n_lo) else n_hi > n_lo
            noise = 0.3 * ((i * 7) % 5 - 2)
            ret = (hi_ret if hi else lo_ret) + noise
            if flip_half and i >= (n_hi + n_lo) // 2:
                ret = (lo_ret if hi else hi_ret) + noise
            row = {"day": days[i], "share": 40.0 if hi else 0.0}
            for o in CFG["ledger"]["outcomes"]:
                for h in CFG["ledger"]["horizons"]:
                    row[f"{o['id']}_{h}"] = ret
            out.append(row)
        return out
    st = tb.ledger_stats(sample(20, 60, 3.0, 0.0))
    check(st["verdict"] == "INSUFFICIENT" and st["primary"] == "spx_20",
          "fewer than 30 high weeks: INSUFFICIENT (the rule's cell is the S&P 500 at +20)")
    st = tb.ledger_stats(sample(40, 40, 3.0, 0.0))
    check(st["verdict"] == "PASS" and st["by"]["spx_20"]["t"] > 2,
          f"30 a side, |t| past 2, one sign in both halves: PASS (t {st['by']['spx_20']['t']:.1f})")
    st = tb.ledger_stats(sample(40, 40, 3.0, 0.0, flip_half=True))
    check(st["verdict"] == "FAIL", "the difference changing sign between the halves: FAIL")
    st = tb.ledger_stats(sample(40, 40, 0.05, 0.0))
    check(st["verdict"] == "FAIL", "a difference inside the noise: FAIL")
    check(tb.welch_t([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == 0.0
          and abs(tb.welch_t([2.0, 3.0, 4.0], [1.0, 2.0, 3.0]) - 1.2247) < 1e-3,
          "Welch's t by hand")


def group_e() -> None:
    head("E. PLACEMENT")
    from daily_cascade import trend_breadth_block as tbb       # noqa: PLC0415
    src = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    i = src.index("ITEM 89(b)")
    check('if cadence in ("weekly", "monthly"):' in src[i:i + 400]
          and "trend_breadth_block.positioning_subsection" in src[i:i + 600],
          "the Weekly's Positioning & flows carries the table; the Monthly reads the same one")
    close = (REPO / "daily_cascade" / "stack_close.py").read_text(encoding="utf-8")
    check("trend_breadth" not in close, "nothing in the daily close")
    db = str(Path(gate_tmp.mkdtemp("trend_breadth_place_")) / "chester.db")
    _seed(db)
    with observations.ObservationStore(db) as st:
        tb.compute(as_of=NOW, store=st)
        ss = tbb.positioning_subsection(st, NOW)
    check(ss and ss["paragraph_wanted"] is False and ss["table"]["columns"][0] == "Market"
          and ss["title"] == tbb.TITLE and "Report only" in ss["table_note"],
          "a table and code-written lines: no paragraph, no chart")
    empty = str(Path(gate_tmp.mkdtemp("trend_breadth_empty_")) / "chester.db")
    with observations.ObservationStore(empty) as st:
        r = tb.read(st, NOW)
    check(r["held"] == 0 and "not computed yet" in tb.lines(r)[0],
          "before the backfill the share prints 'not computed yet'")


def group_f() -> None:
    head("F. HYGIENE")
    keys = tb.SIGN_KEYS + [tb.FLIPS_KEY, tb.SHARE_KEY]
    reg = {k: derived.registry_entry(k) for k in keys}
    check(len(tb.SIGN_KEYS) == 64 and all(reg.values())
          and all(e.get("trigger_eligible") is False for e in reg.values()),
          "the 64 signs and the two breadth keys registered, none trigger-eligible")
    check(all(derived.market_state_barred(e) for e in reg.values()),
          "every trend.* key barred from the market-state object in the registry")
    ms = (REPO / "config" / "market_state.yaml").read_text(encoding="utf-8")
    rg = (REPO / "regime.py").read_text(encoding="utf-8")
    named = re.compile(r"(?<![\w.])trend\.|trend_breadth")
    check(not named.search(ms) and not named.search(rg),
          "named in neither the market-state config nor regime.py")
    code = (REPO / "altdata" / "trend_breadth.py").read_text(encoding="utf-8")
    check(not re.search(r"import_yfinance|requests|urllib|http_get|vendor|flashalpha", code),
          "the module fetches nothing and reads no vendor value")
    keys_used = {k["key"] for m in CFG["markets"] for k in m["keys"]}
    check(len(CFG["markets"]) == 16 and all(derived.registry_entry(k) for k in keys_used),
          "every declared source key is already registered: stored keys only, no new symbol (D33)")
    mk = __import__("gate_list").makefile_text(REPO)
    check("tools/validate_trend_breadth.py" in mk, "the gate is in the Makefile's list")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
