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
          and aa["flags"].get("widening") is False and aa["forms"]["widening_threshold_bp"] == 25.0
          and "session-set" in aa["forms"]["widening_threshold_basis"],
          f"6b, per series: HY +{hy['forms']['change_3m_bp']:.0f} bp widens at 100; IG "
          f"+{ig['forms']['change_3m_bp']:.0f} bp does not at 40; AA "
          f"+{aa['forms']['change_3m_bp']:.0f} bp does not at its session-set 25 "
          f"(config/metric_lenses.yaml, ruling (d)4)")
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
    check(abs(s["forms"]["surprise"] - 0.4) < 1e-9
          and after["forms"].get("surprise_state") == "no consensus"
          and "no free consensus source" in after["reasons"]["surprise"],
          "the surprise against consensus where one is held (+0.4); otherwise "
          "'no consensus' with its reason (ruling (d)6)")


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


# ---------------------------------------------------------------------------
# 6e, THE REST (16 Oct 2026)
# ---------------------------------------------------------------------------
OAS8 = ("fred.hy_oas", "fred.bb_oas", "fred.ccc_oas", "fred.ig_oas", "fred.aa_oas",
        "fred.bbb_oas", "fred.em_corp_oas", "fred.em_hy_oas")


def _oas_store(name: str, short_bp: float) -> observations.ObservationStore:
    """Each OAS flat at 2.00% for a year, its last print up its threshold less
    `short_bp` basis points."""
    st = observations.ObservationStore(str(TMP / f"oas_{name}.sqlite"))
    days = bdays(dt.date(2025, 9, 1), END)
    rows = []
    for k in OAS8:
        th, _ = derived.widening_threshold(k)
        for d in days:
            rows.append(row(k, d, 2.0 + ((th - short_bp) / 100.0 if d == days[-1] else 0.0)))
    st.write_many(rows)
    return st


def group_h() -> None:
    head("H. THE WIDENING THRESHOLDS, CONFIG AND RULING (d)4: AT THEIR VALUE, NOT BELOW")
    cfg = derived.lens_config().get("widening_bp_3m") or {}
    want = {"fred.hy_oas": 100, "fred.bb_oas": 100, "fred.ccc_oas": 100, "fred.ig_oas": 40,
            "fred.aa_oas": 25, "fred.bbb_oas": 50, "fred.em_corp_oas": 75,
            "fred.em_hy_oas": 150}
    got = {k: v["bp"] for k, v in cfg.items()}
    check(got == want and all(cfg[k]["basis"].startswith("ratified") for k in OAS8[:4])
          and all(cfg[k]["basis"].startswith("session-set") for k in OAS8[4:]),
          f"eight series in config/metric_lenses.yaml, each with its basis: the four "
          f"ratified unchanged, AA 25, BBB 50, EM corporate 75, EM high yield 150 "
          f"session-set ({got})")
    with _oas_store("at", 0.0) as at, _oas_store("below", 1.0) as below:
        fire = {k: derived.lens_forms(k, AS_OF, store=at)["flags"].get("widening") for k in OAS8}
        quiet = {k: derived.lens_forms(k, AS_OF, store=below)["flags"].get("widening") for k in OAS8}
    check(all(fire.values()), f"each fires at exactly its threshold ({fire})")
    check(not any(quiet.values()), f"and none fires a basis point below it ({quiet})")
    reg = derived._load_registry()
    lwr = sorted(k for k, e in reg.items() if str(e.get("long_window")) == "ratio")
    fallback = [k for k in lwr
                if "not a window" in derived.long_window_of(k, derived.family_of(k)[0])[1]
                and derived.long_window_of(k, derived.family_of(k)[0])[0]
                == derived.LONG_WINDOW.get(derived.family_of(k)[0] or "")]
    check(len(lwr) == 19 and fallback == lwr,
          f"ruling (d)2: the {len(lwr)} `long_window: ratio` values read as their "
          f"family's default, with the reason")
    for k in lwr:
        print(f"          long_window ratio -> family default: {k} "
              f"({derived.family_of(k)[0]}, {derived.long_window_of(k, derived.family_of(k)[0])[0]})")


def group_i(L: dict) -> None:
    head("I. THE SURPRISE PRINTS 'NO CONSENSUS', RULING (d)6")
    from daily_cascade import lens_cells  # noqa: PLC0415
    from monthly_macro.writer import render_v2  # noqa: PLC0415
    cpi = L["fred.cpi"]
    t = "\n".join(render_v2.lens_tables([{"metric": "fred.cpi", "lens": cpi}]))
    line = next(ln for ln in t.splitlines() if ln.startswith("| `fred.cpi`"))
    check(lens_cells.cell(cpi, "surprise") == "no consensus" and "| no consensus |" in line
          and "Surprise: " not in t,
          "the release table's Surprise cell reads 'no consensus', never a guess, a "
          "blank or a zero")


def group_j() -> None:
    head("J. THE CORE CPI LESS CORE PCE GAP: A LENS, AND ITS SIGN FLIP")
    st = observations.ObservationStore(str(TMP / "gap.sqlite"))
    ms = months(dt.date(2015, 1, 1), 141)                 # to 2026-09-01
    st.write_many([row("calc.core_cpi_pce_gap", m, 0.4 + (i % 5) * 0.02 if i < 138 else -0.3 - i * 0.001)
                   for i, m in enumerate(ms)])
    g = derived.lens_forms("calc.core_cpi_pce_gap", AS_OF, store=st)
    st2 = observations.ObservationStore(str(TMP / "gap_pos.sqlite"))
    st2.write_many([row("calc.core_cpi_pce_gap", m, 0.4 + (i % 5) * 0.02) for i, m in enumerate(ms)])
    pos = derived.lens_forms("calc.core_cpi_pce_gap", AS_OF, store=st2)
    st.close()
    st2.close()
    check(g["family"] == "ratio" and g["flags"].get("sign_flipped") is True
          and g["forms"].get("sign_since") == "2026-07-01"
          and pos["flags"].get("sign_flipped") is False,
          f"a ratio-family lens; three negative months flag the flip, dated from "
          f"{g['forms'].get('sign_since')}; a positive gap does not")
    from monthly_macro.writer import render_v2  # noqa: PLC0415
    t = "\n".join(render_v2.lens_tables([{"metric": "calc.core_cpi_pce_gap", "lens": g}]))
    check("**sign flipped**" in t and "Pctile 5y" in t,
          "the Monthly table prints its percentiles, its trend and the flag")


def group_k() -> None:
    head("K. THE 10-YEAR'S ANCHORS AND FAIR VALUE (SR-43; BATCH 4 SECTION 4.1)")
    from altdata import rates_anchors  # noqa: PLC0415
    from daily_cascade import lens_cells  # noqa: PLC0415
    st = observations.ObservationStore(str(TMP / "anchors.sqlite"))
    rows = []
    cpi = 100.0
    for i, m in enumerate(months(dt.date(1990, 1, 1), 441)):   # to 2026-09-01
        cpi *= 1.0 + (0.0015 + 0.0015 * ((i // 24) % 3)) # inflation regimes
        rows.append(row("fred.cpi", m, cpi))
        rows.append(row("fred.yield_10y", m + dt.timedelta(days=14),
                        2.0 + 0.6 * ((i // 24) % 3) + (i % 3) * 0.05))
    rows.append(row("fred.yield_10y", dt.date(2026, 10, 14), 4.80))
    st.write_many(rows)
    lens = derived.lens_forms("fred.yield_10y", AS_OF, store=st)
    ia = rates_anchors.inflation_anchor(st, AS_OF)
    st.close()
    f, r = lens["forms"], lens["reasons"]
    check(lens["family"] == "rate"
          and abs(f["inflation_anchor_gap_bp"] - round(100 * (4.80 - ia["anchor_pct"]), 1)) < 1e-6
          and abs(f["fair_value_inflation_pct"] - round(ia["fitted_pct"], 4)) < 1e-9
          and abs(f["fair_value_inflation_gap_bp"] - round(ia["residual_bp"], 1)) < 1e-9,
          f"rates family: the SR-43 inflation anchor ({f['inflation_anchor_pct']:.2f}%, "
          f"gap {f['inflation_anchor_gap_bp']:+.0f} bp) and the inflation fit's fair value "
          f"({f['fair_value_inflation_pct']:.2f}%), as rates_anchors computes them")
    check("fair_value_fiscal_pct" not in f and "twin-deficit fit needs" in r["fair_value_fiscal_pct"]
          and "term_premium_pct" in r,
          "the twin-deficit fit and the term premium absent with their reasons")
    al = lens_cells.anchor_line(lens) or ""
    check("inflation anchor" in al and "(descriptive; unvalidated, n=0)" in al
          and "twin-deficit fit n/a" in al,
          "one printed line, tagged descriptive and unvalidated")


def group_l(L: dict, st) -> None:
    head("L. THE WEEKLY AND THE CLOSE PRINT THE MONTHLY'S FORMS (A SHARED FIXTURE)")
    from daily_cascade import lens_cells  # noqa: PLC0415
    keys = [("fred.yield_10y", "10-year"), ("fred.hy_oas", "High-yield OAS"),
            ("fred.cpi", "CPI"), ("yfinance.mkt_spy", "SPY")]
    sub = lens_cells.lens_table(st, AS_OF, keys)
    data = sub["data"]["lenses"]
    same = all(data[label]["forms"] == L[k]["forms"] for k, label in keys)
    check(same, "the lens table reads lens_forms() at the same cutoff: every form equal "
                "to the Monthly's on the same fixture")
    rows = {r[0]: r for r in sub["table"]["rows"]}
    y = L["fred.yield_10y"]["forms"]
    check(y["pctile_5y_ordinal"] in rows["10-year"][2] and y["pctile_long_ordinal"] in rows["10-year"][2]
          and lens_cells.cell(L["fred.hy_oas"], "change_3m_bp") in rows["High-yield OAS"][2]
          and lens_cells.cell(L["fred.cpi"], "yoy") in rows["CPI"][2]
          and "widening" in rows["High-yield OAS"][3] and "correction" in rows["SPY"][3],
          f"each compact cell is the Monthly's cells, flags beside them "
          f"({rows['10-year'][2]}; {rows['High-yield OAS'][2]})")
    check(sub["table"]["columns"] == ["Series", "Family", "Lens", "Flags"]
          and not sub.get("paragraph") and sub.get("paragraph_wanted") is False,
          "a table, no paragraph: no prose word for either budget")


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
        group_h()
        group_i(L)
        group_j()
        group_k()
        group_l(L, st)
    finally:
        st.close()
    print(f"\n{PASSED} passed, {FAILED} failed")
    print(LINE)
    print("VALIDATION PASSED" if not FAILED else "VALIDATION FAILED")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
