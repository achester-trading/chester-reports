#!/usr/bin/env python3
"""
The metric lenses' gate (6e; the brief of 1 Oct 2026, ratified 4 Oct). A code
gate: fixture series in a temporary observation store, read through the real
registry's families. It never reads the live store, fetches or calls a model.

  A. The registry: every resolved series carries a family or a reason it has
     none; the vocabulary; the minutes' named assignments (6e); the windows (6c)
  B. A fixture series per family gives that family's forms
  C. A monthly release never shows a 20-session change, in the forms or the table
  D. The correction and bear flags at their thresholds (6a); widening per series
     (6b); the 5y/long disagreement (6d)
  E. A two-vintage fixture gives the revision line; the release reads
     point-in-time
  F. Both percentiles print with their window and n, and their ordinals
  G. A form that cannot be computed carries its reason; the Monthly v2 table
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp  # noqa: E402

from altdata import derived, observations  # noqa: E402

TMP = Path(mkdtemp("gate_lenses_"))
LINE = "=" * 78
PASSED = FAILED = 0
AS_OF = "2026-10-14T22:00:00+00:00"


def ok(m: str) -> None:
    global PASSED
    PASSED += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAILED
    FAILED += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    (ok if c else bad)(m)


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def bdays(first: dt.date, last: dt.date) -> list[dt.date]:
    out, d = [], first
    while d <= last:
        if d.weekday() < 5:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def months(first: dt.date, n: int) -> list[dt.date]:
    return [dt.date(first.year + (first.month - 1 + i) // 12, (first.month - 1 + i) % 12 + 1, 1)
            for i in range(n)]


def row(key, day, value, avail=None):
    a = avail or f"{day}T21:00:00+00:00"
    return {"registry_key": key, "instrument": None, "observed_at": str(day),
            "available_at": a, "value": float(value), "source": "fixture",
            "availability_kind": "reconstructed"}


END = dt.date(2026, 10, 14)


def build_store() -> observations.ObservationStore:
    st = observations.ObservationStore(str(TMP / "lenses.sqlite"))
    rows = []
    days = bdays(dt.date(2020, 1, 2), END)
    n = len(days)
    # price: SPY climbs to 100 in the last year, then ends exactly 10% off its high;
    # QQQ ends exactly 20% off; IWM a cent short of a correction.
    for key, last in (("yfinance.mkt_spy", 90.0), ("yfinance.mkt_qqq", 80.0),
                      ("yfinance.mkt_iwm", 90.01)):
        for i, d in enumerate(days):
            if i < n - 60:
                v = 60 + 40 * i / (n - 60) + ((0.4 if i % 2 else -0.4) if i < n - 300 else 0)
            elif i < n - 30:
                v = 100.0
            else:
                v = 100.0 + (last - 100.0) * (i - (n - 31)) / 30
            rows.append(row(key, d, v))
    # rate: thirty years, high in the 1990s, low lately: the 5y and long disagree
    ydays = bdays(dt.date(1996, 1, 2), END)
    for i, d in enumerate(ydays):
        v = 7.0 - 5.0 * min(1.0, i / 5000) + (0.5 if d.year >= 2022 else 0.0) + (i % 7) * 0.01
        if d == ydays[-1]:
            v = 3.0                    # the top of five years, mid-way in thirty
        rows.append(row("fred.yield_10y", d, v))
    # spreads: HY up 120 bp in three months (widening at 100), IG up 30 (not at 40)
    for key, base, up in (("fred.hy_oas", 3.0, 1.2), ("fred.ig_oas", 1.0, 0.3),
                          ("fred.aa_oas", 0.6, 0.2)):
        for i, d in enumerate(days):
            v = base + (i % 5) * 0.01 + (up * (i - (n - 63)) / 63 if i >= n - 63 else 0.0)
            rows.append(row(key, d, v))
    # conditions: VIX quiet, then a spike
    for i, d in enumerate(days):
        rows.append(row("fred.vix", d, 15 + (i % 10) * 0.3 + (12 if i == n - 1 else 0)))
    # quantity: the Fed's balance sheet, weekly, falling
    for i, d in enumerate([x for x in days if x.weekday() == 2]):
        rows.append(row("fred.fed_balance", d, 9_000_000 - i * 2_000))
    # ratio: bid-to-cover, monthly, rising lately
    for i, d in enumerate(months(dt.date(2004, 1, 1), 274)):
        rows.append(row("auction.bid_to_cover", d, 2.3 + max(0, i - 268) * 0.05 + (i % 4) * 0.001))
    # release: CPI, monthly, each print a month and ten days after its period at
    # 08:30 ET; August first printed 320.0 and revised to 320.5 with September's
    # print on 15 Oct. U-3: monthly, a percent.
    cpi_months = months(dt.date(2021, 1, 1), 69)          # to 2026-09-01
    for i, m in enumerate(cpi_months):
        pub = dt.date(m.year + (m.month == 12), m.month % 12 + 1, 11)
        if m == dt.date(2026, 9, 1):
            pub = dt.date(2026, 10, 15)
        v = 260.0 + i * 0.9
        if m == dt.date(2026, 8, 1):
            v = 320.0
        if m == dt.date(2026, 9, 1):
            v = 322.0
        rows.append(row("fred.cpi", m, v, f"{pub}T12:30:00+00:00"))
    rows.append(row("fred.cpi", dt.date(2026, 8, 1), 320.5, "2026-10-15T12:30:00+00:00"))
    for i, m in enumerate(months(dt.date(2021, 1, 1), 68)):
        pub = dt.date(m.year + (m.month == 12), m.month % 12 + 1, 5)
        rows.append(row("fred.u3_rate", m, 4.0 + (i % 12) * 0.05, f"{pub}T12:30:00+00:00"))
    st.write_many(rows)
    return st


def group_a() -> None:
    head("A. THE REGISTRY: A FAMILY ON EVERY SERIES, OR ITS REASON")
    reg = derived._load_registry()
    none = [k for k, e in reg.items() if not e.get("family") and not e.get("lens_excluded")]
    bad_fam = [k for k, e in reg.items() if e.get("family") and e["family"] not in derived.FAMILIES]
    check(not none and not bad_fam,
          f"all {len(reg)} resolved series carry a family from the vocabulary or a "
          f"reason they have none" + (f" -- {none[:4]} {bad_fam[:4]}" if none or bad_fam else ""))
    named = {"fred.u3_rate": "release", "fred.breakeven_10y": "rate", "fred.breakeven_5y5y": "rate",
             "fred.term_premium_kw": "rate", "fred.dxy": "price", "yfinance.mkt_dxy": "price",
             "yfinance.mkt_gld": "price", "fred.wti": "price", "yfinance.mkt_btc_usd": "price",
             "yfinance.mkt_xlk": "price", "fred.vix": "conditions", "yfinance.mkt_vix": "conditions",
             "calc.yield_curve_2s10s": "ratio", "calc.breadth_rsp_over_spy": "ratio",
             "shiller.cape": "ratio", "index.forward_pe": "ratio", "yfinance.mkt_tnx": "rate",
             "fred.hy_oas": "spread", "fred.fed_balance": "quantity"}
    wrong = {k: derived.family_of(k)[0] for k, f in named.items() if derived.family_of(k)[0] != f}
    check(not wrong, "the minutes' named assignments hold (6e: unemployment a release; "
                     "breakevens and the term premium rates; DXY, gold, oil, BTC, sectors "
                     "prices; VIX conditions; 2s10s, breadth, CAPE, forward P/E ratios)"
          + (f" -- {wrong}" if wrong else ""))
    lw = {k: derived.long_window_of(k, derived.family_of(k)[0])[0] for k in (
        "fred.hy_oas", "fred.yield_10y", "fred.cpi", "fred.u3_rate", "auction.bid_to_cover",
        "fred.fed_balance", "fred.vix", "shiller.cape", "fred.tips_5y", "calc.yield_curve_2s10s")}
    check(lw == {"fred.hy_oas": 20, "fred.yield_10y": "full", "fred.cpi": "full",
                 "fred.u3_rate": 20, "auction.bid_to_cover": 20, "fred.fed_balance": None,
                 "fred.vix": 20, "shiller.cape": "full", "fred.tips_5y": "full",
                 "calc.yield_curve_2s10s": 20},
          f"the long windows (6c): spreads and conditions 20y, rates and inflation full, "
          f"labour 20y, ratios 20y (valuation full), quantities none ({lw})")
    fl = derived.family_of("calc.yields_up_dollar_down.flag")
    check(fl[0] is None and "not a level series" in fl[1],
          "a family declared on a boolean flag reads as no lens, with its reason")


def group_b(st) -> dict:
    head("B. A FIXTURE SERIES PER FAMILY GIVES ITS FORMS")
    L = {k: derived.lens_forms(k, AS_OF, store=st) for k in (
        "yfinance.mkt_spy", "yfinance.mkt_qqq", "yfinance.mkt_iwm", "fred.yield_10y",
        "fred.hy_oas", "fred.ig_oas", "fred.aa_oas", "fred.cpi", "fred.u3_rate",
        "fred.fed_balance", "fred.vix", "auction.bid_to_cover")}
    want = {
        "price": ("return_1m", "return_3m", "return_12m", "return_ytd", "drawdown_52w",
                  "realized_vol_20d", "realized_vol_20d_pctile", "return_12m_pctile",
                  "move_1m_pctile"),
        "rate": ("change_1m_bp", "change_3m_bp", "change_12m_bp", "pctile_5y", "pctile_long"),
        "spread": ("pctile_5y", "pctile_long", "change_1m_bp", "change_3m_bp"),
        "release": ("yoy", "annualized_3m"),
        "quantity": ("yoy_pct", "change_3m_units", "direction"),
        "conditions": ("pctile_5y", "pctile_long", "z_5y", "spike_vs_1y_avg_pct"),
        "ratio": ("pctile_5y", "pctile_long", "trend_3m"),
    }
    for key, fam in (("yfinance.mkt_spy", "price"), ("fred.yield_10y", "rate"),
                     ("fred.hy_oas", "spread"), ("fred.cpi", "release"),
                     ("fred.fed_balance", "quantity"), ("fred.vix", "conditions"),
                     ("auction.bid_to_cover", "ratio")):
        f = L[key]["forms"]
        miss = [w for w in want[fam] if f.get(w) is None]
        check(L[key]["family"] == fam and not miss,
              f"{fam}: {key} gives {', '.join(want[fam])}" + (f" -- missing {miss}"
                                                               if miss else ""))
    q = L["fred.fed_balance"]["forms"]
    check(q["direction"] == "falling" and q["change_3m_units"] < 0 and q["yoy_pct"] < 0,
          f"quantity: the balance sheet's 3-month change in its units "
          f"({q['change_3m_units']:,.0f} {q.get('change_3m_units_unit')}) and its direction "
          f"({q['direction']})")
    c = L["fred.vix"]["forms"]
    check(c["spike_vs_1y_avg_pct"] > 50 and c["z_5y"] > 3,
          f"conditions: the spike against the 1-year average (+{c['spike_vs_1y_avg_pct']:.0f}%) "
          f"and its z ({c['z_5y']:.1f})")
    r = L["auction.bid_to_cover"]["forms"]
    check(r["trend_3m"] > 0 and r["trend_3m_direction"] == "up", "ratio: the 3-month trend, up")
    rate = L["fred.yield_10y"]["forms"]
    check(abs(rate["change_12m_bp"]) > 0 and isinstance(rate["change_1m_bp"], float),
          f"rate: changes in bp (12m {rate['change_12m_bp']:+.0f} bp)")
    return L


def group_c(L: dict) -> None:
    head("C. A MONTHLY RELEASE NEVER SHOWS A 20-SESSION CHANGE")
    f = L["fred.cpi"]["forms"]
    check(not any(re.search(r"20d|20_session|delta_20", k) for k in f)
          and not any(re.search(r"20d", k) for k in L["fred.u3_rate"]["forms"]),
          "the CPI and U-3 lenses carry no 20-session form")
    from monthly_macro.writer import render_v2  # noqa: PLC0415
    rows = [{"metric": "fred.cpi", "lens": L["fred.cpi"]},
            {"metric": "fred.u3_rate", "lens": L["fred.u3_rate"]}]
    t = "\n".join(render_v2.lens_tables(rows))
    check("20d" not in t and "| YoY | 3m ann. / 3m chg |" in t,
          "and the Monthly's release table has no 20-session column")


def group_d(L: dict) -> None:
    head("D. THE FLAGS AT THEIR THRESHOLDS")
    s, q, i = (L[k] for k in ("yfinance.mkt_spy", "yfinance.mkt_qqq", "yfinance.mkt_iwm"))
    check(derived.CORRECTION_PCT == -10.0 and derived.BEAR_PCT == -20.0
          and abs(s["forms"]["drawdown_52w"] + 10.0) < 1e-9
          and s["flags"]["correction"] and not s["flags"]["bear"],
          "6a: exactly -10% from the 52-week high is a correction, not a bear")
    check(abs(q["forms"]["drawdown_52w"] + 20.0) < 1e-9 and q["flags"]["bear"]
          and q["flags"]["correction"], "6a: exactly -20% is a bear")
    check(not i["flags"]["correction"] and i["forms"]["drawdown_52w"] > -10.0,
          f"a cent short of -10% ({i['forms']['drawdown_52w']:.4f}%) is no correction")
    hy, ig, aa = (L[k] for k in ("fred.hy_oas", "fred.ig_oas", "fred.aa_oas"))
    check(hy["flags"].get("widening") and hy["forms"]["widening_threshold_bp"] == 100.0
          and ig["flags"].get("widening") is False and ig["forms"]["widening_threshold_bp"] == 40.0
          and "widening" not in aa["flags"] and "6b" in aa["reasons"]["widening"],
          f"6b, per series: HY +{hy['forms']['change_3m_bp']:.0f} bp widens at 100; IG "
          f"+{ig['forms']['change_3m_bp']:.0f} bp does not at 40; AA has no ratified threshold")
    r = L["fred.yield_10y"]
    check(r["flags"]["percentiles_disagree"] and derived.DISAGREEMENT_POINTS == 30.0,
          f"6d: the 10-year at the {r['forms']['pctile_5y_ordinal']} of five years and the "
          f"{r['forms']['pctile_long_ordinal']} of its full history: flagged at 30 points")


def group_e(st) -> None:
    head("E. THE REVISION LINE, AND POINT-IN-TIME")
    after = derived.lens_forms("fred.cpi", "2026-10-15T13:00:00+00:00", store=st)
    before = derived.lens_forms("fred.cpi", "2026-10-15T12:00:00+00:00", store=st)
    check(after["forms"].get("revision") == "Aug revised 320.0 -> 320.5"
          and after["observed_at"] == "2026-09-01",
          f"two vintages of August: {after['forms'].get('revision')!r}, with September's print")
    check(before["observed_at"] == "2026-08-01" and before["level"] == 320.0
          and "revision" not in before["forms"],
          "half an hour before that print: August at its first value, and no revision")
    s = derived.lens_forms("fred.cpi", "2026-10-15T13:00:00+00:00", store=st,
                           consensus={"2026-09-01": 321.6})
    check(abs(s["forms"]["surprise"] - 0.4) < 1e-9 and "events table" in after["reasons"]["surprise"],
          "the surprise against consensus where one is held (+0.4); otherwise its reason")


def group_f(L: dict) -> None:
    head("F. BOTH PERCENTILES, WITH WINDOW AND n")
    for k in ("fred.yield_10y", "fred.hy_oas", "fred.vix", "auction.bid_to_cover", "fred.u3_rate"):
        f = L[k]["forms"]
        good = (f.get("pctile_5y") is not None and f.get("pctile_long") is not None
                and f.get("pctile_5y_n", 0) > 1 and f.get("pctile_long_n", 0) > 1
                and f.get("pctile_5y_window") and f.get("pctile_long_window")
                and re.fullmatch(r"\d+(st|nd|rd|th)", f.get("pctile_5y_ordinal") or ""))
        check(bool(good), f"{k}: {f.get('pctile_5y_ordinal')} ({f.get('pctile_5y_window')}, "
                          f"n={f.get('pctile_5y_n')}) beside {f.get('pctile_long_ordinal')} "
                          f"({f.get('pctile_long_window')}, n={f.get('pctile_long_n')})")


def group_g(L: dict, st) -> None:
    head("G. REASONS, AND THE MONTHLY V2 TABLE")
    q = L["fred.fed_balance"]
    check("pctile_long" not in q["forms"] and q["family"] == "quantity",
          "a quantity carries no level percentile (6c: quantities none)")
    check(all(v for v in L["fred.cpi"]["reasons"].values()),
          "every form not computed carries its reason, never a blank")
    from monthly_macro.writer import render_v2  # noqa: PLC0415
    rows = [{"metric": k, "lens": L[k]} for k in (
        "yfinance.mkt_spy", "yfinance.mkt_qqq", "fred.yield_10y", "fred.hy_oas", "fred.aa_oas",
        "fred.cpi", "fred.u3_rate", "fred.fed_balance", "fred.vix", "auction.bid_to_cover")]
    rows[5]["lens"] = derived.lens_forms("fred.cpi", "2026-10-15T13:00:00+00:00", store=st)
    t = "\n".join(render_v2.lens_tables(rows))
    fams = re.findall(r"^\*\*(\w+)\*\*$", t, re.M)
    check(fams == ["price", "rate", "spread", "release", "quantity", "conditions", "ratio"]
          and "**bear**" in t and "**widening**" in t and "n=" in t
          and "n/a: `fred.aa_oas`" not in t,
          "the Monthly v2 pillar table prints each family's forms, its flags, and both "
          "percentiles with n")
    check("Aug revised 320.0 -> 320.5" in t, "the revision line prints in the release table")
    u3 = next(ln for ln in t.splitlines() if ln.startswith("| `fred.u3_rate`"))
    cpi = next(ln for ln in t.splitlines() if ln.startswith("| `fred.cpi`"))
    check(re.search(r"\d+(st|nd|rd|th) \(5y, n=\d+\)", u3) and "| — |" in cpi,
          "6e: the unemployment rate carries a level percentile in the release table; "
          "CPI does not")
    src = (REPO / "monthly_macro" / "payload.py").read_text(encoding="utf-8")
    rsrc = (REPO / "monthly_macro" / "writer" / "render_v2.py").read_text(encoding="utf-8")
    check("derived.lens_forms(metric, as_of, store=db)" in src
          and "percentile_of" not in rsrc and "statistics." not in rsrc,
          "the forms are computed in altdata/derived.py alone; the renderer only prints")
    print("        sample (fixtures):")
    for ln in t.splitlines():
        print("          " + ln)


def main() -> int:
    st = build_store()
    try:
        group_a()
        L = group_b(st)
        group_c(L)
        group_d(L)
        group_e(st)
        group_f(L)
        group_g(L, st)
    finally:
        st.close()
    print(f"\n{PASSED} passed, {FAILED} failed")
    print(LINE)
    print("VALIDATION PASSED" if not FAILED else "VALIDATION FAILED")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
