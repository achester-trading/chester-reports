"""
Validation gate for SR-37 and SR-38 (signal-triage batch 4, ST4-01 and ST4-02):
the AI FCF-transfer panel, the return-attribution lens, the forward-EPS revision
line and EY minus the bill. On a synthetic store of its own; no network, no box.

  A  THE FCF PANEL (SR-37). Trailing twelve months per name from four
     consecutive reported quarters (FCF = operating cash flow + capex as
     published); the hyperscalers' and the semis' sums only when every name
     of the side is read, "k of n" otherwise; the change on the prior
     quarter's TTM; capex as a share of operating cash flow; the ratio, not
     defined while the hyperscalers' FCF is at or below zero; the threshold
     state "hyperscaler aggregate FCF < 0"; a gap in the quarters refuses the
     TTM; a quarter filed after the cutoff is not seen. Labelled trailing, the
     forward series named absent.
  B  THE ATTRIBUTION (SR-38). ln(P1/P0) = ln(E1/E0) + ln(M1/M0) over twelve
     months of the stored S&P price and trailing earnings: +10% price on +20%
     earnings is a multiple of -8.3%; EY minus the bill at the index's last
     close; the forward split "awaiting the first drop" (group F has the
     drops); EY minus Baa and the AI share named absent.
  C  THE REVISION LINE (SR-38). The AI names' stored forward EPS, 4- and
     13-week changes and their median, labelled as the names' and not the
     index's; a name without the history is counted, not guessed.
  D  PLACEMENT. The revision line in the Weekly's Mechanics; the FCF panel and
     the revision line in the Monthly's Mechanics; the attribution in the
     Monthly's What's priced; every printed line tagged "(descriptive;
     unvalidated, n=0)"; the printed figures in the section's data.
  E  RIGHTS AND THE WRITER. The fundamentals writer reads all nine names and
     every key it writes is registered, none trigger-eligible; neither module
     imports the market-state object.

    python tools/validate_ai_fcf.py
"""

from __future__ import annotations

import datetime as dt
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gate_tmp                                                 # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
TAG = "(descriptive; unvalidated, n=0)"
CUT = "2026-10-12T23:00:00+00:00"


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


QUARTERS = ["2025-06-30", "2025-09-30", "2025-12-31", "2026-03-31", "2026-06-30"]
# ticker -> (operating cash flow, capex) per quarter, $bn. The hyperscalers
# spend more than they earn in cash in the latest four quarters; the semis
# collect it.
HYPER = {"AMZN": (30, -40), "GOOGL": (35, -38), "META": (25, -30),
         "MSFT": (40, -42), "ORCL": (6, -12)}
SEMIS = {"NVDA": (45, -2), "MU": (8, -4), "AVGO": (15, -1), "AMAT": (6, -1)}


def obs(key, day, value, avail=None, inst=None, source="fixture"):
    return {"registry_key": key, "instrument": inst, "observed_at": day,
            "available_at": avail or (day + "T21:00:00+00:00"), "value": value,
            "source": source}


def seed(db: str) -> None:
    from altdata import observations
    from altdata.sources import fundamentals as fu
    rows = []
    for t, (o, c) in {**HYPER, **SEMIS}.items():
        for k, q in enumerate(QUARTERS):
            # The oldest quarter is cash-rich: the prior TTM is higher.
            bump = 10 if k == 0 else 0
            rows.append(obs(fu.key(t, "operating_cash_flow"), q, (o + bump) * 1e9))
            rows.append(obs(fu.key(t, "capex"), q, c * 1e9))
    # A quarter filed after the cutoff: never seen.
    rows.append(obs(fu.key("NVDA", "operating_cash_flow"), "2026-09-30", 999e9,
                    avail="2026-11-20T21:00:00+00:00"))
    rows.append(obs(fu.key("NVDA", "capex"), "2026-09-30", -1e9,
                    avail="2026-11-20T21:00:00+00:00"))
    # Shiller: 13 months, price 4000 -> 4400, trailing earnings 200 -> 240.
    months = [dt.date(2025, m, 1).isoformat() for m in range(6, 13)] + \
        [dt.date(2026, m, 1).isoformat() for m in range(1, 7)]
    for k, m in enumerate(months):
        rows.append(obs("shiller.sp_price", m, 4000 + 400 * k / 12))
        rows.append(obs("shiller.sp_earnings", m, 200 + 40 * k / 12))
    rows.append(obs("yfinance.mkt_gspc", "2026-10-09", 5000.0))
    rows.append(obs("fred.tbill_3m", "2026-10-09", 4.0))
    # Forward EPS, daily for 100 days: NVDA +0.1%/day; MSFT +0.05%/day; MU 10 days.
    end = dt.date(2026, 10, 12)
    for sym, g, n in (("NVDA", 0.001, 100), ("MSFT", 0.0005, 100), ("MU", 0.002, 10)):
        for i in range(n):
            d = (end - dt.timedelta(days=n - 1 - i)).isoformat()
            rows.append(obs("yf.forward_eps", d, 10 * (1 + g) ** i, inst=sym))
    with observations.ObservationStore(db) as st:
        st.write_many(rows)


def main() -> int:
    from altdata import ai_fcf, observations, return_attribution as ra
    tmp = gate_tmp.mkdtemp("aifcf_")
    db = os.path.join(tmp, "store.db")
    seed(db)
    with observations.ObservationStore(db) as st:
        r = ai_fcf.read(st, CUT)
        a = ra.attribution(st, CUT)
        v = ra.revisions(st, CUT)

    print(f"\n{LINE}\nA. THE FCF PANEL (SR-37)\n{LINE}")
    h, s = r["hyperscalers"], r["semis"]
    check(h["fcf"] == -104e9 and h["ocf"] == 544e9 and h["capex"] == -648e9,
          f"hyperscalers: TTM FCF = TTM operating cash flow + TTM capex "
          f"(4 x (136 - 162) = -$104bn) ({ai_fcf.bn(h['fcf'])})")
    check(s["fcf"] == 264e9 and h["covered"] == 5 and s["covered"] == 4,
          f"semis: 4 x (74 - 8) = $264bn, every name read ({ai_fcf.bn(s['fcf'])})")
    check(h["change"] == -50e9 and s["change"] == -40e9,
          "the change on the prior quarter's TTM (the cash-rich quarter rolls off)")
    check(abs(h["capex_to_ocf"] - 648 / 544) < 1e-9,
          "capex as a share of operating cash flow")
    check(r["below_zero"] is True and r["ratio"] is None,
          "the threshold state 'hyperscaler aggregate FCF < 0' reads yes; the ratio "
          "is not defined while that FCF is at or below zero")
    nv = next(n for n in r["names"] if n["ticker"] == "NVDA")
    check(nv["period_end"] == "2026-06-30" and nv["fcf"] == 4 * 43e9,
          "a quarter filed after the cutoff is not seen")
    ln = ai_fcf.lines(r)
    check(ln[0].startswith("The five hyperscalers: TTM free cash flow −$104.0bn "
                           "(operating cash flow $544.0bn, capex −$648.0bn; capex "
                           "119% of operating cash flow), −$50.0bn on the prior "
                           "quarter's TTM")
          and "Hyperscaler aggregate free cash flow below zero: yes" in ln[3]
          and "The ratio is not defined" in ln[2],
          f"the lines ({ln[0][:90]}...)")
    check(all(TAG in x for x in ln) and "Trailing, from the quarterly filings" in ln[-1]
          and "no free feed" in ln[-1],
          "every line tagged; labelled trailing, the forward series named absent")
    t = ai_fcf.table(r)
    check(len(t["columns"]) <= 6 and len(t["rows"]) == 9
          and t["rows"][0][:2] == ["AMZN", "hyperscaler"]
          and t["rows"][5][:2] == ["NVDA", "semiconductor"],
          "one row a name, six columns at most")
    # A missing name, and a gap in the quarters.
    with observations.ObservationStore(db) as st:
        r2 = ai_fcf.read(st, "2026-06-15T00:00:00+00:00")       # 2026-06-30 unseen
        cfg = ai_fcf.load_config()
        cfg["fcf"]["semis"] = ["NVDA", "MU", "AVGO", "AMAT", "TSM"]
        r3 = ai_fcf.read(st, CUT, cfg)
        cfg2 = ai_fcf.load_config()
        cfg2["fcf"]["max_quarter_gap_days"] = 80
        r4 = ai_fcf.read(st, CUT, cfg2)
    check(r2["hyperscalers"]["fcf"] == 4 * -26e9 + 50e9 and
          r2["hyperscalers"]["change"] is None,
          "as of an earlier cutoff, the earlier four quarters; no prior TTM with "
          "four quarters stored")
    check(r3["semis"]["fcf"] is None and "4 of 5 carry four reported quarters "
          "(missing TSM)" in ai_fcf.lines(r3)[1],
          "a name without four quarters: no aggregate, 'k of n' printed")
    check(all(n["fcf"] is None and n["reason"] == "a missing quarter in the latest four"
              for n in r4["names"]),
          "a gap in the quarters refuses the TTM (three quarters wearing four)")

    print(f"\n{LINE}\nB. THE ATTRIBUTION (SR-38)\n{LINE}")
    sp = a["split"]
    check(sp and sp["start"] == "2025-06-01" and sp["end"] == "2026-06-01"
          and abs(sp["price_pct"] - 10) < 1e-9 and abs(sp["earnings_pct"] - 20) < 1e-9
          and abs(sp["multiple_pct"] - (100 * (1.1 / 1.2 - 1))) < 1e-9,
          f"+10% price on +20% earnings is a multiple of "
          f"{sp and sp['multiple_pct']:.1f}%, exact in logs")
    al = ra.attribution_lines(a)
    check(al[0].startswith("The S&P 500 over the 12 months to June 2026: price +10.0%, "
                           "of which trailing earnings +20.0% and the multiple -8.3% "
                           "(trailing P/E 20.0 to 18.3); earnings growth is 191% of "
                           "the return in logs"),
          f"the split line ({al[0][:100]}...)")
    ey = a["ey"]
    check(ey and abs(ey["ey_pct"] - 4.8) < 1e-9 and abs(ey["gap_pp"] - 0.8) < 1e-9
          and "Trailing earnings yield 4.80%" in al[1] and "+0.80 percentage points" in al[1],
          "EY minus the bill: 240 / 5000 = 4.80% less the bill's 4.00%, +0.80 pp")
    check(all(TAG in x for x in al)
          and al[2].startswith("The forward split: not tracked (source withdrawn)")
          and "Trailing, not forward" in al[3]
          and "no Baa yield is stored" in al[3]
          and "index weights are not stored" in al[3],
          "every line tagged; the forward split awaits the first drop; EY minus Baa "
          "and the AI share named absent, each with its reason")
    with observations.ObservationStore(db) as st:
        a0 = ra.attribution(st, "2026-01-15T00:00:00+00:00")
    check(a0["split"] is None and "do not span 12 months" in ra.attribution_lines(a0)[0],
          "fewer than 13 stored months: the split is not read, and says so")

    print(f"\n{LINE}\nC. THE REVISION LINE (SR-38)\n{LINE}")
    nv = next(n for n in v["names"] if n["symbol"] == "NVDA")
    mu = next(n for n in v["names"] if n["symbol"] == "MU")
    check(abs(nv["4-week"] - 100 * (1.001 ** 28 - 1)) < 1e-6
          and abs(nv["13-week"] - 100 * (1.001 ** 91 - 1)) < 1e-6,
          "a name's 4- and 13-week change in its stored forward EPS")
    check(mu["4-week"] is None and mu["n"] == 10 and v["covered"]["4-week"] == 2,
          "a name without the history is counted, not guessed")
    rl = ra.revision_line(v)
    check(rl.startswith("Forward-EPS revisions, the nine AI names' consensus (not the "
                        "index's): 4-week median +2.1% (2 of 9 names); 13-week median")
          and TAG in rl, f"the line ({rl[:110]}...)")

    print(f"\n{LINE}\nD. PLACEMENT\n{LINE}")
    from daily_cascade import weekly_stack as ws
    from monthly_macro import stack as mstack
    with observations.ObservationStore(db) as st:
        mw = ws.mechanics_week(st, [], CUT, {})
        mm = mstack.mechanics_section(st, "2026-09-01", "2026-09-30", CUT,
                                      __import__("daily_cascade.stack",
                                                 fromlist=["x"]).config())
        att, att_data = ws.attribution_block(st, CUT)
    wt = [x.get("title") for x in mw["subsections"]]
    mt = [x.get("title") for x in mm["subsections"]]
    check(ws.AI_REVISIONS_TITLE in wt and ws.AI_FCF_TITLE not in wt
          and mw["data"]["ai_revisions"]["median"]["4-week"] is not None,
          "the Weekly's Mechanics: the revision line (weekly), with its figures in "
          "the section's data")
    check(ws.AI_FCF_TITLE in mt and ws.AI_REVISIONS_TITLE in mt
          and mm["data"]["ai_fcf"]["hyperscaler_fcf_below_zero"] is True,
          "the Monthly's Mechanics: the FCF panel and the revision line")
    check(att and att["title"] == ws.ATTRIBUTION_TITLE and att_data["multiple_pct"] == -8.3
          and "ws.attribution_block(st, now)" in Path(mstack.__file__).read_text(
              encoding="utf-8"),
          "the Monthly's What's priced: the attribution and EY minus the bill")
    allines = [x for ss in mm["subsections"] if ss.get("title") in
               (ws.AI_FCF_TITLE, ws.AI_REVISIONS_TITLE) for x in ss["lines"]] \
        + att["lines"]
    check(allines and all(TAG in x for x in allines)
          and all(not ss.get("paragraph_wanted") for ss in mm["subsections"]
                  if ss.get("title") in (ws.AI_FCF_TITLE, ws.AI_REVISIONS_TITLE)),
          "every printed line tagged; code-written, no paragraph of their own")

    print(f"\n{LINE}\nE. RIGHTS AND THE WRITER\n{LINE}")
    import yaml
    from altdata.sources import fundamentals as fu
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    entries = reg.get("metrics") or reg
    keys = [fu.key(t, f) for t in ("NVDA", "AVGO", "AMAT")
            for f in ("operating_cash_flow", "capex", "net_debt", "cogs")]
    check(set(HYPER) | set(SEMIS) <= set(fu.TICKERS)
          and all(k in fu.KEYS for k in keys),
          "the fundamentals writer reads all nine names")
    check(all(k in entries and entries[k].get("trigger_eligible") is False
              for k in keys),
          "every new key is registered, none trigger-eligible")
    src = (REPO / "altdata" / "ai_fcf.py").read_text(encoding="utf-8") + \
        (REPO / "altdata" / "return_attribution.py").read_text(encoding="utf-8")
    check("import regime" not in src and "regime." not in src,
          "neither module reads or writes the market-state object (report-only)")

    print(f"\n{LINE}\nRESULT: {PASS} passed, {FAIL} failed\n{LINE}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
