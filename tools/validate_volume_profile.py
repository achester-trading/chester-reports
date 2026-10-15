"""
Validation gate for the volume profile (VP-1, ruled 14 Oct 2026;
docs/volume-profile.md). FIXTURES ONLY: every store is the gate's own,
seeded in a temporary directory; no fetch, no model, no live store.

  A  A HAND-BUILT WINDOW whose bin width, POC, value area and nodes are worked
     out by hand in the comments, including a bar spread over two bins, a high on
     a bin edge and a tie for the POC.
  B  THE INVARIANTS. Total volume conserved; the POC inside the value area; the
     value area holds at least the share, and dropping its last-added pair falls
     below it; a constant price shift (a whole number of bins) moves POC, VAH and
     VAL by that constant; scaling volume changes nothing; a bar with high = low.
  C  ABSENT WITH THE REASON. An incomplete window names each session below the
     share; a window whose bars carry two sources is absent, never mixed.
  D  AS OF. A bar available after the cutoff leaves the result byte-identical.
  E  THE TABLES' RULES. Migration (higher, lower, unchanged, inside, outside,
     overlapping higher, overlapping lower) and close against value, on
     hand-built pairs; the table row a reader prints.
  F  THE LEVEL LIST. Six windows of POC, VAH and VAL for spy, qqq and iwm,
     appended after the existing types in order; statuses on the prior windows
     only; a window not computed absent with its reason; the flat row carries
     the fields.
  G  THE LABEL AUDIT. A wrong figure beside "the prior week's value-area high"
     fails, as the 30 Sep put wall did; the right one passes; a bare name binds
     to any window; "yesterday's" is the prior session's.
  H  THE STORED SERIES. calc.vp_<id>_session_* and _20s_*: a row's available_at
     is the max of its input bars'; 18 registry entries with the declared fields.
  I  THE SCANNER'S CLAUSE, on a fixture candidate: the base's POC and the
     nearest HVN between the entry and +1R, "approximated from daily bars"; the
     score is untouched.

    python tools/validate_volume_profile.py
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml  # noqa: E402

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


def pt(price: float, vol: float, close: float | None = None) -> dict:
    """A bar with high = low: all its volume in one bin."""
    return {"high": price, "low": price, "close": price if close is None else close,
            "volume": vol}


# THE HAND-BUILT WINDOW. Last close 100.00 at 5 bps is a raw width of 0.05, on
# the ladder: bins of 0.05 from 100.00. Bin i (i = 0..9) is [100.00 + 0.05i,
# 100.05 + 0.05i). Volumes by bin: 1 2 3 10 20 8 6 2 1 1 (total 54).
VOLS = [1, 2, 3, 10, 20, 8, 6, 2, 1, 1]


def hand_bars(shift: float = 0.0, scale: float = 1.0) -> list[dict]:
    out = [pt(round(100.01 + 0.05 * i + shift, 4), v * scale)
           for i, v in enumerate(VOLS) if i]
    # The LAST bar sets the width: its close is 100.00 (+ shift), in bin 0.
    out.append(pt(round(100.00 + shift, 4), VOLS[0] * scale))
    return out


def group_a(vp) -> None:
    head("A. A HAND-BUILT WINDOW")
    cfg = vp.load_config()
    check(vp.bin_width(100.0, 5, cfg["tick_ladder"]) == 0.05,
          "5 bps of 100.00 is 0.05, on the ladder")
    check(vp.bin_width(664.0, 5, cfg["tick_ladder"]) == 0.25,
          "5 bps of 664.00 is 0.332, rounded DOWN to 0.25")
    check(vp.bin_width(664.0, 25, cfg["tick_ladder"]) == 1.0,
          "25 bps of 664.00 (daily bars) is 1.66, rounded down to 1")
    check(vp.bin_width(3.0, 5, cfg["tick_ladder"]) == 0.01,
          "never below the ladder's first step")
    p = vp.profile(hand_bars(), 5, cfg)
    # POC: bin 4 (20) -> midpoint 100.225. Value area: 0.70 x 54 = 37.8.
    # From 20: above (bins 5, 6) = 14 against below (3, 2) = 13 -> above, 34.
    # Then above (7, 8) = 3 against below 13 -> below, 47 >= 37.8. Area bins
    # 2..6: VAL 100.10, VAH 100.35.
    check(p["bin_width"] == 0.05 and p["poc"] == 100.225,
          f"POC is bin 4's midpoint, 100.225 ({p['poc']})")
    check((p["val"], p["vah"]) == (100.10, 100.35),
          f"value area 100.10 to 100.35, built outward by pairs ({p['val']}, "
          f"{p['vah']})")
    check(p["va_steps"] == [14, 13],
          f"the steps added: the pair above (14), then the pair below (13) "
          f"({p['va_steps']})")
    # A bar over two bins: 10 shares over [100.00, 100.10] -> 5 and 5; the high
    # sits on bin 2's lower edge and puts nothing there.
    vap = vp.volume_at_price([{"high": 100.10, "low": 100.00, "close": 100.05,
                               "volume": 10}], 0.05)
    check({k: round(v, 9) for k, v in vap.items()} == {2000: 5.0, 2001: 5.0},
          f"a bar's volume spreads evenly over its range; a high on a bin edge "
          f"covers none of the bin above ({vap})")
    vap = vp.volume_at_price([{"high": 100.08, "low": 100.02, "close": 100.05,
                               "volume": 6}], 0.05)
    check({k: round(v, 9) for k, v in vap.items()} == {2000: 3.0, 2001: 3.0},
          "each bin takes the share of the range it covers (0.03 of 0.06 each)")
    # A tie: bins 1 and 7 at 10. The profile's mean price is nearer bin 7, so 7.
    tie = [pt(100.06, 10), pt(100.36, 10), pt(100.31, 4), pt(100.31, 4),
           pt(100.00, 1, 100.00)]
    pt_ = vp.profile(tie, 5, cfg)
    check(pt_["poc"] == 100.375,
          f"a tie goes to the bin nearest the volume-weighted mean ({pt_['poc']})")
    # Bins 1 and 3 at 10 each, nothing between: the mean (100.125) is exactly
    # between them. The last close, 100.16, keeps the width at 0.05.
    sym = [pt(100.06, 10), pt(100.16, 10)]
    ps = vp.profile(sym, 5, cfg)
    check(ps["poc"] == 100.075,
          f"and an exact tie at equal distance goes to the lower ({ps['poc']})")
    # Nodes: two humps. Bins 0..20 = 1 1 2 4 8 12 8 4 2 1 1 1 2 4 8 12 8 4 2 1 1.
    hump = [1, 1, 2, 4, 8, 12, 8, 4, 2, 1, 1, 1, 2, 4, 8, 12, 8, 4, 2, 1, 1]
    nb = [pt(round(100.01 + 0.05 * i, 4), v) for i, v in enumerate(hump) if i]
    nb.append(pt(100.00, hump[0]))
    pn = vp.profile(nb, 5, cfg)
    check(pn["hvn"] == [100.275, 100.775],
          f"the HVNs are the two humps' peaks, bins 5 and 15 ({pn['hvn']})")
    check(pn["lvn"] == [100.525],
          f"the LVN is the trough between them, bin 10 ({pn['lvn']}); the "
          f"profile's tails are not nodes")
    d = vp.daily_profile([{"observed_at": "2026-10-01", "high": 101, "low": 99,
                           "close": 100, "volume": 1e6}], cfg)
    check(d.get("note") == "approximated from daily bars" and d.get("daily"),
          "a profile from daily bars says it is approximated from daily bars")
    d2 = vp.daily_profile([{"observed_at": "2026-10-01", "high": 101, "low": 99,
                            "close": 100, "volume": None}], cfg)
    check("absent" in d2 and "volume not stored" in d2["absent"],
          f"a daily window without volume is absent with the reason ({d2})")


def group_b(vp) -> None:
    head("B. THE INVARIANTS")
    cfg = vp.load_config()
    bars = [{"high": 100 + (i % 7) * 0.13 + 0.4, "low": 100 + (i % 7) * 0.13,
             "close": 100 + (i % 7) * 0.13 + 0.2, "volume": 1000 + 37 * (i % 11)}
            for i in range(60)]
    p = vp.profile(bars, 5, cfg)
    tot = sum(b["volume"] for b in bars)
    check(abs(sum(p["volume"]) - tot) < 1e-6 * tot,
          f"total volume conserved ({sum(p['volume']):.4f} of {tot})")
    check(p["val"] <= p["poc"] <= p["vah"], "the POC is inside the value area")
    share = cfg["value_area_share"]
    check(p["value_area_volume"] >= share * tot - 1e-9 * tot,
          f"the value area holds at least {share:.0%} "
          f"({p['value_area_share']:.4f})")
    check(p["value_area_volume"] - p["va_steps"][-1] < share * tot,
          "and without its last-added pair it falls below the share")
    for sh in (0.50, 2.00):
        a, b = vp.profile(hand_bars(), 5, cfg), vp.profile(hand_bars(sh), 5, cfg)
        check(all(abs((b[k] - a[k]) - sh) < 1e-9 for k in ("poc", "vah", "val"))
              and b["bin_width"] == a["bin_width"],
              f"a shift of {sh:+.2f} (whole bins, same width) moves POC, VAH and "
              f"VAL by {sh:+.2f}")
    a, b = vp.profile(hand_bars(), 5, cfg), vp.profile(hand_bars(scale=7.3), 5, cfg)
    check(all(a[k] == b[k] for k in ("poc", "vah", "val", "hvn", "lvn")),
          "scaling every bar's volume changes nothing")
    one = vp.profile([pt(100.03, 500)], 5, cfg)
    check(one["poc"] == 100.025 and (one["val"], one["vah"]) == (100.0, 100.05)
          and sum(one["volume"]) == 500,
          "a lone bar with high = low: all its volume in its one bin, the value "
          "area that bin")
    check("absent" in vp.profile([pt(100, 0)], 5, cfg),
          "a window with no volume is absent")


# ---------------------------------------------------------------------------
# The seeded store: 5-minute bars for SPY, the gate's own file.
# ---------------------------------------------------------------------------
DAY = "2026-10-08"


def five_min(day: str, base: float, n: int | None = None, source: str = "yfinance",
             avail_lag_min: int = 20, instrument: str = "spy") -> list[dict]:
    from altdata import bars as bars_mod
    first, _, expected = bars_mod.session_window(instrument, day)
    t0 = dt.datetime.fromisoformat(first)
    out = []
    for j in range(expected if n is None else n):
        t = t0 + dt.timedelta(minutes=5 * j)
        px = base + 0.4 * ((j % 13) - 6) / 6
        out.append({"instrument": instrument, "symbol": instrument.upper(),
                    "interval": "5m", "observed_at": t.isoformat(),
                    "open": px, "high": px + 0.15, "low": px - 0.15,
                    "close": px + 0.05, "volume": 10000 + 500 * (j % 9),
                    "available_at": (t + dt.timedelta(minutes=5 + avail_lag_min)
                                     ).isoformat(),
                    "source": source})
    return out


def sessions(first: str, last: str) -> list[str]:
    from altdata import session
    d, out = dt.date.fromisoformat(first), []
    while d <= dt.date.fromisoformat(last):
        if session.is_trading_session(d):
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def seed(path: str, days: list[str], tweak=None) -> None:
    from altdata import bars as bars_mod
    with bars_mod.BarStore(path, create=True) as st:
        for k, d in enumerate(days):
            rows = five_min(d, 650.0 + 0.8 * k)
            if tweak:
                rows = tweak(d, rows)
            st.write_many(rows)


def group_c(vp, td: str) -> None:
    head("C. ABSENT WITH THE REASON: INCOMPLETE, MIXED SOURCES")
    from altdata import bars as bars_mod
    db = str(Path(td) / "c.db")
    seed(db, ["2026-10-05", "2026-10-06", "2026-10-07"],
         tweak=lambda d, r: r[:30] if d == "2026-10-07" else r)
    with bars_mod.BarStore(db) as st:
        w = vp.window(st, "spy", "week", "2026-10-07")
    check("absent" in w and w["absent"].startswith("bars incomplete (n=186 of 234)")
          and "2026-10-07 (30 of 78)" in w["absent"]
          and "2026-10-06" not in w["absent"],
          f"a window short of the share is absent, naming the session below it "
          f"({w.get('absent')})")
    with bars_mod.BarStore(db) as st:
        s = vp.window(st, "spy", "prior_session", "2026-10-07")
    check("poc" in s, "the complete session before it is computed")
    db2 = str(Path(td) / "c2.db")
    seed(db2, ["2026-10-05", "2026-10-06", "2026-10-07"],
         tweak=lambda d, r: [dict(x, source="ibkr") for x in r]
         if d == "2026-10-07" else r)
    with bars_mod.BarStore(db2) as st:
        w = vp.window(st, "spy", "week", "2026-10-07")
        s = vp.window(st, "spy", "session", "2026-10-07")
    check("absent" in w and "more than one source (ibkr, yfinance)" in w["absent"],
          f"a window whose bars carry two sources is absent, never mixed "
          f"({w.get('absent')})")
    check("poc" in s and s["source"] == "ibkr",
          "a window of one source is computed, and says which")


def group_d(vp, td: str) -> None:
    head("D. AS OF: A LATER BAR CHANGES NOTHING")
    from altdata import bars as bars_mod
    db = str(Path(td) / "d.db")
    days = sessions("2026-08-31", DAY)
    # The session's last bar is held back (77 of 78 is still complete) ...
    seed(db, days, tweak=lambda d, r: r[:-1] if d == DAY else r)
    cutoff = "2026-10-08T21:00:00+00:00"
    with bars_mod.BarStore(db) as st:
        before = json.dumps(vp.windows(st, "spy", DAY, as_of=cutoff), sort_keys=True)
    # ... and written afterwards, heavy, available only the next morning.
    with bars_mod.BarStore(db, create=True) as st:
        last = five_min(DAY, 650.0 + 0.8 * (len(days) - 1))[-1]
        st.write_many([dict(last, volume=9e9,
                            available_at="2026-10-09T13:00:00+00:00")])
    with bars_mod.BarStore(db) as st:
        after = json.dumps(vp.windows(st, "spy", DAY, as_of=cutoff), sort_keys=True)
        later = vp.window(st, "spy", "session", DAY,
                          as_of="2026-10-09T14:00:00+00:00")
    check(before == after,
          "a bar available after the cutoff leaves all six windows byte-identical")
    check(later.get("poc") is not None and later["poc"] != json.loads(before)
          ["session"]["poc"],
          "and read at a later cutoff it is there (the fixture bites)")


def group_e(vp) -> None:
    head("E. THE TABLES' RULES: MIGRATION, CLOSE AGAINST VALUE")
    prior = {"val": 100.0, "vah": 102.0}
    for cur, want in (({"val": 102.5, "vah": 104.0}, "higher"),
                      ({"val": 97.0, "vah": 99.5}, "lower"),
                      ({"val": 100.0, "vah": 102.0}, "unchanged"),
                      ({"val": 100.5, "vah": 101.5}, "inside"),
                      ({"val": 100.0, "vah": 101.0}, "inside"),
                      ({"val": 99.0, "vah": 103.0}, "outside"),
                      ({"val": 99.0, "vah": 102.0}, "outside"),
                      ({"val": 101.0, "vah": 103.0}, "overlapping higher"),
                      ({"val": 102.0, "vah": 103.0}, "overlapping higher"),
                      ({"val": 99.0, "vah": 101.0}, "overlapping lower"),
                      ({"val": 98.0, "vah": 100.0}, "overlapping lower")):
        got = vp.migration(cur, prior)
        check(got == want, f"{cur['val']}-{cur['vah']} against 100-102: {want} "
                           f"({got})")
    check(vp.migration({}, prior) is None, "no area, no migration")
    va = {"val": 100.0, "vah": 102.0}
    for c, want in ((102.5, "above the VAH"), (102.0, "inside"), (101.0, "inside"),
                    (100.0, "inside"), (99.9, "below the VAL")):
        check(vp.close_vs_value(c, va) == want, f"a close at {c}: {want}")
    inst = {"id": "spy", "label": "SPY", "frame": {"last": 103.0},
            "volume_profile": {"session": {"poc": 101.5, "val": 101.0, "vah": 103.0},
                               "prior_session": {"poc": 101.0, "val": 100.0,
                                                 "vah": 102.0}}}
    row = vp.table_row(inst, "session", "prior_session", unit="$")
    check(row == ["SPY", "$101.00–$103.00 (POC $101.50)",
                  "$100.00–$102.00 (POC $101.00)", "overlapping higher", "inside"],
          f"the row a table prints: Market | Value area (POC) | Prior | Migration | "
          f"Close vs value ({row})")
    inst2 = {"id": "qqq", "label": "QQQ", "frame": {"last": 500.0},
             "volume_profile": {"session": {"absent": "bars incomplete (n=3 of 78)"},
                                "prior_session": {"poc": 1, "val": 1, "vah": 2}}}
    r2 = vp.table_row(inst2, "session", "prior_session")
    check(r2[1] == "not computed" and r2[3] == "—" and r2[4] == "—",
          f"a window not computed prints so, and no migration is claimed ({r2})")
    t = vp.table([inst, inst2], "session", "prior_session")
    check(t["columns"] == ["Market", "Value area (POC)", "Prior session",
                           "Migration", "Close vs value"]
          and len(t["rows"]) == 2
          and any("QQQ session: bars incomplete" in x for x in t["not_tracked"]),
          "the table, five columns, its absences in not_tracked with the reason")


def seed_obs(path: str, days: list[str]) -> None:
    """Daily closes, highs, lows and volume for the tape's price instruments."""
    from altdata import observations
    rows = []
    with observations.ObservationStore(path) as st:
        for key, base in (("yfinance.mkt_spy", 650.0), ("yfinance.mkt_qqq", 590.0),
                          ("yfinance.mkt_iwm", 240.0)):
            for k, d in enumerate(days):
                c = base + 0.8 * k
                for suf, v in (("", c), ("_high", c + 1.2), ("_low", c - 1.1),
                               ("_volume", 5e7)):
                    rows.append({"registry_key": key + suf, "instrument": None,
                                 "observed_at": d, "available_at": d + "T21:00:00+00:00",
                                 "value": v, "source": "fixture"})
        st.write_many(rows)


def group_f(vp, td: str) -> dict:
    head("F. THE LEVEL LIST")
    from altdata import bars as bars_mod, levels
    old = ("prior_close", "session_high", "session_low", "vwap", "week_high",
           "week_low", "ma_20d", "ma_50d", "ma_200d", "high_52w", "low_52w",
           "gamma_flip", "call_wall", "put_wall", "max_pain", "ma_40w", "ma_10m",
           "ma_20m")
    types = [k for k, _ in levels.LEVEL_TYPES]
    check(tuple(types[:len(old)]) == old and len(types) == len(old) + 18,
          "the 18 profile levels are appended after the existing types, in order")
    check(levels.LABEL["vp_prior_week_vah"] == "prior week's value-area high"
          and levels.LABEL["vp_session_poc"] == "session's point of control",
          "labelled by window: \"prior week's value-area high\"")
    db = str(Path(td) / "f.db")
    days = sessions("2026-08-31", DAY)
    seed(db, days)
    seed_obs(db, days)
    with bars_mod.BarStore(db) as st:
        book = levels.compute(DAY, store=st, as_of="2026-10-08T23:00:00+00:00")
    spy = next(i for i in book["instruments"] if i["id"] == "spy")
    qqq = next(i for i in book["instruments"] if i["id"] == "qqq")
    y10 = next(i for i in book["instruments"] if i["id"] == "y10")
    vps = [lv for lv in spy["levels"] if lv["type"].startswith("vp_")]
    check(len(vps) == 18, f"SPY lists all 18 profile levels ({len(vps)})")
    prior_ok = all("status" in lv for lv in vps
                   if lv["type"].split("_")[1] == "prior")
    cur_none = all("status" not in lv for lv in vps
                   if lv["type"].split("_")[1] != "prior")
    check(prior_ok and cur_none,
          "only the prior windows' levels carry a status; the session's, week's "
          "and month's carry none, like the session high and low")
    check(all(lv["status"] in ("held", "broke", "untested") for lv in vps
              if "status" in lv), "statuses by the declared rule (status_of)")
    check(spy["row"].get("vp_prior_week_vah") == next(
              lv["value"] for lv in vps if lv["type"] == "vp_prior_week_vah"),
          "the flat row carries the levels under their field names")
    check(not any(lv["type"].startswith("vp_") for lv in qqq["levels"])
          and qqq["absent"].get("vp_session_poc", "").startswith("bars incomplete"),
          f"a configured instrument without bars: each window absent with its "
          f"reason ({qqq['absent'].get('vp_session_poc')})")
    check(not any(k.startswith("vp_") for k in y10["absent"])
          and not any(lv["type"].startswith("vp_") for lv in y10["levels"]),
          "an instrument outside v1 (the 10-year) neither lists nor misses them")
    check(set(spy["volume_profile"]) == set(vp.WINDOW_IDS),
          "the instrument carries its six windows for the readers' tables")
    return book


def group_g() -> None:
    head("G. THE LABEL AUDIT: A PROFILE LEVEL UNDER THE WRONG NAME")
    from altdata import numeral_audit as na
    payload = {"levels": [{"symbol": "SPY", "name": "SPY",
                           "vp_prior_week_vah": 664.25, "vp_week_vah": 667.0,
                           "vp_prior_week_poc": 661.5, "vp_session_poc": 668.75,
                           "vp_prior_session_val": 659.0, "vp_month_val": 655.0,
                           "vp_prior_month_val": 652.0},
                          {"symbol": "QQQ", "name": "QQQ", "vp_prior_week_vah": 667.0}]}
    r = na.audit("SPY held the prior week's value-area high at 667.00.", payload)
    check(not r.passed and r.unmatched and r.unmatched[0].label_conflict
          and "664.25" in r.unmatched[0].label_conflict,
          f"a wrong figure beside \"the prior week's value-area high\" FAILS: 667 is "
          f"the week's VAH and QQQ's, never SPY's prior week's ({r.reason()})")
    for text, want, why in (
            ("SPY held the prior week's value-area high at 664.25.", True,
             "the right figure passes"),
            ("SPY held the prior week's VAH at 667.00.", False,
             "the abbreviation binds the same way"),
            ("SPY's value-area high at 667.00 held.", True,
             "a bare name binds to that field in any window: the week's is 667"),
            ("SPY's value-area high at 668.75 held.", False,
             "but not to another field: 668.75 is a POC"),
            ("SPY traded through the POC at 661.50.", True,
             "a bare POC binds to any window's point of control"),
            ("SPY's point of control at 668.75 for the session.", True,
             "the long name too"),
            ("SPY held yesterday's value-area low at 659.00.", True,
             "\"yesterday's\" is the prior session's"),
            ("SPY held yesterday's value-area low at 655.00.", False,
             "and not the month's"),
            ("SPY held the month's VAL at 655.00.", True, "the month's"),
            ("SPY held the prior month's VAL at 655.00.", False,
             "the prior month's is not the month's"),
            ("SPY's session's POC at 668.75.", True, "the session's"),
            ("SPY tested the week's value-area high at 664.25.", False,
             "the week's is not the prior week's")):
        rr = na.audit(text, payload)
        check(rr.passed == want, f"{text!r} {'passes' if want else 'FAILS'}: {why}"
              + ("" if rr.passed == want else f" ({rr.reason()})"))


def group_h(vp, td: str) -> None:
    head("H. THE STORED SERIES")
    from altdata import bars as bars_mod
    db = str(Path(td) / "h.db")
    days = sessions("2026-09-08", DAY)
    # One session inside the composite was fetched a week late: the composite's
    # available_at is then that session's last bar, later than DAY's own.
    lag = {d: 20 + 3 * k for k, d in enumerate(days)}
    lag[days[-5]] = 7 * 24 * 60
    from altdata import bars as bm
    with bm.BarStore(db, create=True) as st:
        for k, d in enumerate(days):
            st.write_many(five_min(d, 650.0 + 0.8 * k, avail_lag_min=lag[d]))
    with bars_mod.BarStore(db) as st:
        rows = vp.calc_rows(st, [DAY], instruments=["spy"])
        want_sess = max(b["available_at"] for b in st.read(
            "spy", "5m", *bars_mod.session_window("spy", DAY)[:2]))
        twenty = vp.trailing_sessions(DAY, 20)
        want_20 = max(b["available_at"] for d in twenty for b in st.read(
            "spy", "5m", *bars_mod.session_window("spy", d)[:2]))
    by = {r["registry_key"]: r for r in rows}
    check(set(by) == {f"calc.vp_spy_{w}_{f}" for w in ("session", "20s")
                      for f in ("poc", "vah", "val")},
          f"six series per instrument: session and 20-session POC, VAH, VAL "
          f"({sorted(by)})")
    check(all(r["observed_at"] == DAY and r["source"] == "calc" for r in rows),
          "stamped with the session and the calc source")
    check(by["calc.vp_spy_session_poc"]["available_at"] == want_sess,
          f"a session row's available_at is the max of its input bars' "
          f"({by['calc.vp_spy_session_poc']['available_at']})")
    check(by["calc.vp_spy_20s_vah"]["available_at"] == want_20
          and want_20 > want_sess,
          "the 20-session composite's is the max over all twenty sessions' bars")
    short = vp.calc_rows(bars_mod.BarStore(db), ["2026-09-10"], instruments=["spy"])
    check(not any("_20s_" in r["registry_key"] for r in short)
          and any("_session_" in r["registry_key"] for r in short),
          "with fewer than twenty sessions stored the composite is not written")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    m = reg.get("metrics") or {}
    keys = [f"calc.vp_{i}_{w}_{f}" for i in ("spy", "qqq", "iwm")
            for w in ("session", "20s") for f in ("poc", "vah", "val")]
    want = {"source": "derived_state", "observation_type": "calculated",
            "revision_policy": "recomputed", "units": "price",
            "native_horizon": "daily", "information_half_life": "session"}
    check(all(k in m and all(m[k].get(f) == v for f, v in want.items())
              for k in keys),
          "18 registry entries: derived_state, calculated, recomputed, price, "
          "daily, session")
    check(all(m[k].get("trigger_eligible") is False for k in keys),
          "none is trigger-eligible: what the profile predicts is H-006 to H-008's")
    sh = (REPO / "scripts" / "run_eod_cron.sh").read_text(encoding="utf-8")
    i_feat = sh.find("-m altdata.market_features compute")
    i_vp = sh.find("-m altdata.volume_profile compute")
    check(0 < i_feat < i_vp and "WARN volume_profile exited" in sh,
          "the EOD wrapper runs the compute after the derived features, never fatal")


def group_i(vp) -> None:
    head("I. THE SCANNER'S CLAUSE")
    from altdata import book_b_scanner as bbs
    from daily_cascade import book_b
    n = 300
    days = [(dt.date(2025, 8, 1) + dt.timedelta(days=k)).isoformat() for k in range(n)]
    close = [100.0 + 0.02 * k for k in range(n)]
    # A heavy shelf at 112-113 traded 120-60 sessions back: an HVN above the entry.
    vol = {d: (9e6 if 180 <= k < 240 else 1e6) for k, d in enumerate(days)}
    high = [c + (0.6 if 180 <= k < 240 else 0.8) for k, c in enumerate(close)]
    low = [c - (0.6 if 180 <= k < 240 else 0.8) for k, c in enumerate(close)]
    for k in range(180, 240):
        close[k], high[k], low[k] = 112.5, 113.0, 112.0
    inst = {"symbol": "TEST", "days": days, "close": close, "high": high, "low": low,
            "volume": vol, "has_range": True}
    E = n - 1
    base = {"n": 20, "end": E - 1, "high": max(high[E - 20:E]),
            "low": min(low[E - 20:E]), "range_pct": 1.0}
    entry = close[E]
    # The background trades 100.2 to 106.8; the shelf 112 to 113. A long from 108
    # with 6 of risk aims at 114: the shelf is the only volume in between.
    r = bbs.volume_readings(inst, E, base, entry=108.0, risk=6.0, d=1,
                            cfg=bbs.load_config())
    check(r["note"] == "approximated from daily bars"
          and isinstance(r["base_poc"], float)
          and min(low[E - 20:E]) <= r["base_poc"] <= max(high[E - 20:E]),
          f"the base's POC, from its own {base['n']} sessions ({r['base_poc']})")
    check(r["hvn"] is not None and 112.0 <= r["hvn"] <= 113.0,
          f"the nearest HVN between the entry (108) and +1R (114): the shelf at "
          f"112-113 ({r['hvn']})")
    r_up = bbs.volume_readings(inst, E, base, entry=113.5, risk=5.0, d=1,
                               cfg=bbs.load_config())
    check(r_up["hvn"] is None and r_up["hvn_text"] == "none",
          f"a long from 113.5 toward 118.5: nothing traded there, \"none\" "
          f"({r_up['hvn_text']})")
    r_dn = bbs.volume_readings(inst, E, base, entry=111.5, risk=4.0, d=-1,
                               cfg=bbs.load_config())
    check(r_dn["hvn"] is None,
          f"a short from 111.5 toward 107.5: the shelf is behind it, not in the way "
          f"({r_dn['hvn_text']})")
    c = {"instrument": "TEST", "direction": "long", "thesis": "breakout",
         "volume_profile": r, "score": 0.61}
    line = book_b.candidate_line(1, c)
    check("volume profile (approximated from daily bars): base POC" in line
          and f"nearest HVN toward +1R {r['hvn']:,.2f}" in line
          and line.endswith("(scanner score 0.61)."),
          f"one clause on the candidate line, labelled; the score unchanged "
          f"({line[line.find('volume profile'):][:160]})")
    nov = dict(inst, volume={})
    r0 = bbs.volume_readings(nov, E, base, entry=108.0, risk=6.0, d=1,
                             cfg=bbs.load_config())
    check(r0["base_poc"] is None and "volume not stored" in r0["base_text"],
          f"without daily volume each reading is absent with the reason "
          f"({r0['base_text']})")


def main() -> int:
    from altdata import volume_profile as vp
    td = gate_mkdtemp(prefix="validate_volume_profile_")
    group_a(vp)
    group_b(vp)
    group_c(vp, td)
    group_d(vp, td)
    group_e(vp)
    group_f(vp, td)
    group_g()
    group_h(vp, td)
    group_i(vp)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
