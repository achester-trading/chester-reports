"""
Validation gate for SR-43 and SR-49 (signal-triage batch 4: ST4-08, ST4-09,
ST4-15) -- the 10-year's anchors, the twin-deficit fit, the selloff-shape axis and
the selloff's composition, and the four voices adjudicated by those measures.
Synthetic stores only; no network, no box.

  A  THE INFLATION ANCHOR. The trailing ten-year average of CPI year on year,
     against an independent computation; the fit's slope and intercept recovered
     from a series built on them; the residual printed in bp.
  B  THE TWIN-DEFICIT FIT, on a fixture of the WEO writer's documented output
     (em.weo.fiscal_gdp.<iso3>, em.weo.ca_gdp.<iso3>; altdata/sources/imf_weo.py
     on aq-9a-em-scorecard): the OLS recovered, the US fitted-less-paid gap; with
     the writer's keys absent, the fit degrades to a sentence with its count.
  C  THE SHAPE AXIS: a correlated fixture (every market rising together), a
     divergent one (the focal sovereign up, the Bund down) and a mixed one.
  D  THE COMPOSITION: breakeven-led, real-yield-led and term-premium-led
     selloffs, each classified by what moved; a rise under the threshold is no
     selloff.
  E  THE FOUR VOICES: each verdict from its rule; untestable when the measure is
     absent.
  F  THE PRINT AND THE RIGHTS. Plumbing & rates carries both lines and the
     voices table, every line tagged "(descriptive; unvalidated, n=0)"; the
     market-state object declares no driver and regime.py imports neither module;
     the OECD series are on the FRED pull.

    python tools/validate_rates_anchors.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import datetime as dt
import math
import os
import statistics
import sys
from pathlib import Path

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
CUT = "2026-10-09T21:00:00+00:00"
TAG = "(descriptive; unvalidated, n=0)"


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def row(key, day, v, inst=None):
    return {"registry_key": key, "instrument": inst, "observed_at": day,
            "available_at": f"{day}T22:00:00+00:00", "value": v, "source": "fixture"}


def months(start=(1990, 1), end=(2026, 9)):
    y, m = start
    while (y, m) <= end:
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


def month_end(y, m):
    nxt = dt.date(y + (m == 12), m % 12 + 1, 1)
    return (nxt - dt.timedelta(days=1)).isoformat()


def store(td, name):
    from altdata import observations
    return observations.ObservationStore(str(Path(td) / f"{name}.db"))


def seed_inflation(st):
    """CPI whose year-on-year inflation swings on a 12-year sine; a monthly
    10-year exactly 1.5 + 0.8 x the trailing-decade average, except the last
    month, half a point above its fitted yield."""
    rows, cpi, infl = [], 100.0, {}
    ms = list(months((1980, 1), (2026, 9)))
    for i, (y, m) in enumerate(ms):
        pi = 3.0 + 2.0 * math.sin(2 * math.pi * i / 144.0)
        infl[(y, m)] = pi
        cpi *= (1 + pi / 100.0) ** (1 / 12.0)
        rows.append(row("fred.cpi", month_end(y, m), cpi))
    st.write_many(rows)
    return ms


def trailing_anchor(st):
    from altdata.rates_anchors import _monthly, _points
    c = _monthly(_points(st, "fred.cpi", CUT))
    ks = sorted(c)
    yoy = [100 * (c[ks[i]] / c[ks[i - 12]] - 1) for i in range(12, len(ks))]
    return {ks[i + 12]: statistics.fmean(yoy[i - 119: i + 1])
            for i in range(119, len(yoy))}


def main() -> int:
    from altdata import config, rates_anchors as ra, rates_shape as rs
    print(f"{LINE}\nSR-43 / SR-49 -- THE 10-YEAR'S ANCHORS AND THE SELLOFF'S SHAPE\n{LINE}")
    td = gate_mkdtemp(prefix="validate_rates_anchors_")
    cfg = ra.load_config()

    # --- A ------------------------------------------------------------------
    print(f"\n{LINE}\nA. THE INFLATION ANCHOR\n{LINE}")
    with store(td, "infl") as st:
        seed_inflation(st)
        anc = trailing_anchor(st)
        rows = []
        last = max(anc)
        for mth, a in anc.items():
            y = 1.5 + 0.8 * a + (0.5 if mth == last else 0.0)
            yy, mm = int(mth[:4]), int(mth[5:7])
            rows.append(row("fred.yield_10y", month_end(yy, mm), y))
        st.write_many(rows)
        r = ra.inflation_anchor(st, CUT, cfg)
    check(r["state"] == "ok" and abs(r["anchor_pct"] - anc[last]) < 1e-9,
          f"the anchor is the trailing ten-year average of CPI YoY "
          f"({r.get('anchor_pct'):.3f}% against {anc[last]:.3f}%)")
    f = r.get("fit") or {}
    check(abs(f.get("b", 0) - 0.8) < 0.01 and abs(f.get("a", 0) - 1.5) < 0.05,
          f"the fit recovers the 10-year's slope and intercept on the anchor "
          f"(b {f.get('b')}, a {f.get('a')})")
    check(abs(r["residual_bp"] - 50.0) < 3.0
          and abs(r["gap_bp"] - 100 * (1.5 + 0.8 * anc[last] + 0.5 - anc[last])) < 1e-6,
          f"the residual prints in bp: {r['residual_bp']:+.1f} bp against the fitted "
          f"yield; the gap to the anchor itself beside it")

    # --- B ------------------------------------------------------------------
    print(f"\n{LINE}\nB. THE TWIN-DEFICIT FIT (on the WEO writer's documented keys)\n{LINE}")
    fa = cfg["fiscal_anchor"]
    with store(td, "fiscal") as st:
        r0 = ra.fiscal_anchor(st, CUT, cfg)
        check(r0["state"] == "absent" and r0["n"] == 0
              and "needs 10 countries" in r0["reason"],
              f"with the WEO writer's keys absent the fit degrades, with its count "
              f"({r0['reason']})")
        rows = []
        for i, c in enumerate(fa["countries"]):
            bal, ca = -6.0 + 0.7 * i, -2.0 + 0.4 * (i % 5)
            twin = bal + ca
            y = 4.0 - 0.15 * twin
            if c["iso3"] == "usa":
                bal, ca = -7.0, -3.5
                twin = bal + ca
                y = 4.0 - 0.15 * twin - 0.5           # paid half a point under
            rows += [row(fa["weo_balance"].format(iso3=c["iso3"]), "2025-12-31", bal),
                     row(fa["weo_current_account"].format(iso3=c["iso3"]),
                         "2025-12-31", ca),
                     row(c["yield"], "2026-09-30", y)]
        st.write_many(rows)
        r1 = ra.fiscal_anchor(st, CUT, cfg)
    us_twin = -10.5
    check(r1["state"] == "ok" and r1["n"] == 14,
          f"fourteen developed markets in the cross-section (n={r1.get('n')})")
    fit = r1["fit"]
    check(abs(r1["us_fitted_pct"] - (fit["a"] + fit["b"] * us_twin)) < 1e-9
          and abs(r1["gap_bp"] - 100 * (r1["us_fitted_pct"] - r1["us_market_pct"]))
          < 1e-9 and r1["gap_bp"] > 25,
          f"the US fitted yield {r1['us_fitted_pct']:.2f}% against "
          f"{r1['us_market_pct']:.2f}% paid: fitted less paid "
          f"{r1['gap_bp']:+.0f} bp")
    xs = [p["twin"] for p in r1["points"]]
    ys = [p["yield"] for p in r1["points"]]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    check(abs(r1["fit"]["b"] - b) < 1e-9 and 0 < r1["fit"]["r2"] <= 1,
          f"the OLS slope matches an independent computation ({b:.4f}); R² "
          f"{r1['fit']['r2']:.2f}")

    # --- C ------------------------------------------------------------------
    print(f"\n{LINE}\nC. THE SHAPE AXIS\n{LINE}")
    end = dt.date.fromisoformat(CUT[:10])
    days = [(end - dt.timedelta(days=k)).isoformat() for k in range(120, -1, -1)]
    with store(td, "corr") as st:
        rows = []
        for i, d in enumerate(days):
            wig = 0.03 * math.sin(i / 3.0)
            for k, base in (("fred.yield_10y", 4.0), ("bbk.bund_10y", 2.5),
                            ("mof.jgb_10y", 1.2)):
                rows.append(row(k, d, base + 0.006 * i + wig))
        st.write_many(rows)
        sc = rs.shape(st, CUT, cfg)
    check(sc["state"] == "correlated" and sc["mean_corr"] > 0.5,
          f"correlated: every market rising together ({sc['why']})")
    with store(td, "div") as st:
        rows = []
        for i, mth in enumerate(("2026-05-31", "2026-06-30", "2026-07-31",
                                 "2026-08-31", "2026-09-30")):
            rows += [row("fred.oecd_10y_fr", mth, 3.2 + 0.15 * i),
                     row("fred.oecd_10y_de", mth, 2.6 - 0.05 * i)]
        for i, d in enumerate(days):
            rows += [row("fred.yield_10y", d, 4.0 + 0.002 * i),
                     row("bbk.bund_10y", d, 2.6 - 0.002 * i)]
        st.write_many(rows)
        sd = rs.shape(st, CUT, cfg)
    check(sd["state"] == "divergent" and "France" in sd["why"],
          f"divergent: the focal sovereign up while the Bund falls ({sd['why']})")
    with store(td, "mixed") as st:
        rows = []
        for i, d in enumerate(days):
            rows += [row("fred.yield_10y", d, 4.0 + 0.03 * math.sin(i / 2.0)),
                     row("bbk.bund_10y", d, 2.5 + 0.03 * math.cos(i / 1.3)),
                     row("mof.jgb_10y", d, 1.2 - 0.001 * i)]
        st.write_many(rows)
        sm = rs.shape(st, CUT, cfg)
        se = rs.shape(store(td, "empty").__enter__(), CUT, cfg)
    check(sm["state"] == "mixed", f"mixed: neither ({sm['why']})")
    check(se["state"] is None and "too few" in se["why"],
          "with no yields stored the shape is not read, and says so")

    # --- D ------------------------------------------------------------------
    print(f"\n{LINE}\nD. THE COMPOSITION OF EACH SELLOFF\n{LINE}")
    sess = [d for d in [(end - dt.timedelta(days=k)) for k in range(400, -1, -1)]
            if d.weekday() < 5]
    lab = {}
    for lead in ("breakeven", "real", "term_premium"):
        with store(td, f"so_{lead}") as st:
            rows = []
            n = len(sess)
            for i, d in enumerate(sess):
                ramp = max(0, i - (n - 21)) / 20.0          # the last 20 sessions
                be = 2.3 + (0.25 if lead == "breakeven" else 0.08) * ramp
                rl = 1.8 + (0.25 if lead == "real" else 0.07) * ramp
                tp = 0.5 + (0.40 if lead == "term_premium" else 0.05) * ramp
                rows += [row("fred.breakeven_10y", d.isoformat(), be),
                         row("fred.tips_10y", d.isoformat(), rl),
                         row("acm.term_premium_10y", d.isoformat(), tp),
                         row("fred.yield_10y", d.isoformat(), be + rl + tp - 0.5)]
            st.write_many(rows)
            lab[lead] = rs.selloffs(st, CUT, cfg)
    got = {k: (v["latest"] or {}).get("label") for k, v in lab.items()}
    check(got == {"breakeven": "breakeven-led", "real": "real-yield-led",
                  "term_premium": "term-premium-led"},
          f"each selloff classified by what moved ({got})")
    lt = lab["breakeven"]["latest"]
    check(lt["rise_bp"] >= 25 and all(abs(lt["shares"][k] - lt["moves_bp"][k]
                                          / lt["rise_bp"]) < 1e-12
                                      for k in lt["moves_bp"])
          and max(lt["moves_bp"], key=lt["moves_bp"].get) == "breakeven",
          f"each leg's move and its share of the 10-year's "
          f"({lt['moves_bp']}, rise {lt['rise_bp']:.0f} bp)")
    with store(td, "quiet") as st:
        st.write_many([row("fred.yield_10y", d.isoformat(), 4.0 + 0.0005 * i)
                       for i, d in enumerate(sess)])
        q = rs.selloffs(st, CUT, cfg)
    check(not q["episodes"], "a rise under 25 bp in 20 sessions is no selloff")

    # --- E ------------------------------------------------------------------
    print(f"\n{LINE}\nE. THE FOUR VOICES\n{LINE}")
    anchors = {"inflation": {"ten_year_pct": 5.30}, "fiscal": r1}
    v = {x["voice"]: x["verdict"] for x in rs.adjudicate(
        {"state": "correlated"}, {"current": None}, anchors, cfg)}
    check(v == {"outlet not named in the order (post cited)": "consistent",
                "Société Générale (an idea, via a post)": "consistent",
                "Arkevium": "consistent",
                "Sarmaya Partners": "outside these measures"},
          f"each verdict from its rule ({v})")
    v2 = {x["voice"]: x["verdict"] for x in rs.adjudicate(
        {"state": "divergent"}, {"current": {"label": "breakeven-led"}},
        {"inflation": {"ten_year_pct": 5.8}, "fiscal": {"state": "absent"}}, cfg)}
    check(v2["outlet not named in the order (post cited)"] == "not consistent"
          and v2["Société Générale (an idea, via a post)"] == "not testable yet"
          and v2["Arkevium"] == "not settled",
          f"divergent refutes the 1994 read; an absent fit is not testable; above "
          f"the band without a term-premium-led selloff is not settled ({v2})")
    v3 = {x["voice"]: x["verdict"] for x in rs.adjudicate(
        {"state": "mixed"}, {"current": {"label": "term-premium-led"}},
        {"inflation": {"ten_year_pct": 5.9}, "fiscal": r1}, cfg)}
    check(v3["Arkevium"] == "consistent" and v3["outlet not named in the order (post cited)"] == "not settled",
          "above the band with a term-premium-led selloff reads as the spiral path")
    check(set(v.values()) | set(v2.values()) | set(v3.values()) <= set(rs.VERDICTS),
          "every verdict is in the vocabulary")

    # --- F ------------------------------------------------------------------
    print(f"\n{LINE}\nF. THE PRINT AND THE RIGHTS\n{LINE}")
    from daily_cascade import weekly_stack as ws
    with store(td, "infl") as st:
        pw = ws.plumbing_week(st, CUT, "2026-10-02T21:00:00+00:00")
    subs = {s["title"]: s for s in pw.get("subsections") or []}
    a_ = subs.get("The 10-year's anchors and the selloff's shape") or {}
    vt = subs.get("The 10-year top: four voices, read against the measures") or {}
    check(len(a_.get("lines") or []) == 2 and all(x.endswith(TAG + ".") or
                                                  x.endswith(TAG)
                                                  for x in a_["lines"]),
          f"Plumbing & rates prints the anchors line and the shape line, each tagged "
          f"({(a_.get('lines') or [''])[0][:90]}...)")
    check((vt.get("table") or {}).get("columns") == ["Voice", "Claim (6 Oct 2026)",
                                                    "The measure", "Verdict"]
          and len(vt["table"]["rows"]) == 4 and TAG in (vt.get("lines") or [""])[0],
          "and the four voices' table, its verdicts tagged as declared-rule reads")
    check("rates_anchors" in (pw.get("data") or {}),
          "the section's data carries the printed figures for its frame")
    import regime
    rtext = Path(regime.__file__).read_text(encoding="utf-8")
    check("driver" not in (regime.load_config()["dimensions"]["rates"] or {})
          and "rates_shape" not in rtext and "rates_anchors" not in rtext,
          "nothing enters the market-state object: no driver, and regime.py "
          "imports neither module")
    ids = {s.fred_id for s in config.FRED_PULL_SERIES}
    check({f"IRLTLT01{c}M156N" for c in ("US", "CA", "DE", "FR", "IT", "ES", "NL",
                                         "BE", "AU", "NZ", "CH", "SE", "GB", "JP")}
          <= ids, "the fourteen OECD 10-year series are on the FRED pull")

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
