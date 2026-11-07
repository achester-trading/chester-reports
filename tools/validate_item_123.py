"""
B136 (session B, 6 Nov 2026): signal-triage Batch 22 item 123, the AI
infrastructure cash-cycle scorecard (the order's 105), section 0's O-4 and
V-105a to V-105d.

  A  THE FORMULAS. On fixture facts: cloud growth on the year; the four-quarter
     incremental margin as the sum of the changes in operating income over the
     sum of the changes in revenue, "insufficient" without eight quarters;
     capex / OCF and FCF after leases over four consecutive quarters.
  B  THE TREADMILL. Capex growing faster than revenue in both of the last two
     quarters while the four-quarter incremental margin falls fires it; one
     quarter short, or the margin rising, does not; too few quarters is
     "insufficient".
  C  THE PATHS. No signal-scan file: "no confirmed rows" and "no signal-scan
     file proposes any yet"; a scan's Financing section is read as proposed, a
     line without its URL skipped; the GPU row prints "gap" with V-105a's
     candidates; the useful-life row's cross-reference; the dated records print
     "dated record" with their URLs, and every one carries a filed URL.
  D  THE SR-16 FOLD. Row 6's line sits in SR-16's Factor I lines, after the
     AI-credit line, and in the panel; Oracle's spread "not tracked" with no key.
  E  THE READERS. An instance with and without the xbrli prefix; a segment's
     context with the operating-segments qualifier kept, any other second
     dimension refused; year-to-date facts differenced to quarters; the store
     read at a cutoff sees only the vintages accepted by then.
  F  PLACEMENT AND HYGIENE. The Monthly's hook after the capex chain, the Themes
     refresh, nothing in the Weekly; the 48 keys registered, barred from the
     market-state object, trigger-ineligible; the two narrative proposals; the
     module fetches nothing; the gate in the list.

The clock is pinned to GATE_NOW. Synthetic fixtures only: no live store, no
network, no model.

    python tools/validate_item_123.py
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

import gate_tmp  # noqa: E402

from altdata import cash_cycle as cc  # noqa: E402
from altdata import derived, observations  # noqa: E402
from altdata.sources import edgar_xbrl as ex  # noqa: E402

GATE_KIND = "code"
GATE_NOW = "2026-11-06T22:00:00+00:00"

PASS = FAIL = 0
LINE = "=" * 78
QE = ["2024-09-30", "2024-12-31", "2025-03-31", "2025-06-30", "2025-09-30",
      "2025-12-31", "2026-03-31", "2026-06-30", "2026-09-30"]


def pin_clock() -> None:
    from altdata import session                                 # noqa: PLC0415
    session.utc_now = lambda: dt.datetime.fromisoformat(GATE_NOW)


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


def group_a() -> None:
    head("A. THE FORMULAS")
    rev = dict(zip(QE, [10, 11, 12, 13, 14, 15, 16, 17, 18.0]))
    oi = dict(zip(QE, [3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7.0]))
    check(abs(cc.growth(rev) - (18 / 14 - 1)) < 1e-12,
          "cloud growth: the latest quarter over the same quarter a year before")
    want = sum(oi[QE[i]] - oi[QE[i - 4]] for i in range(5, 9)) / \
        sum(rev[QE[i]] - rev[QE[i - 4]] for i in range(5, 9))
    check(abs(cc.incremental_margin(rev, oi) - want) < 1e-12 and abs(want - 0.5) < 1e-12,
          "incremental margin: the sum of four quarters' changes in operating income over "
          "the sum of the changes in revenue (0.50)")
    short = {k: v for k, v in rev.items() if k >= "2025-09-30"}
    check(cc.incremental_margin(short, oi) is None,
          "fewer than eight quarters: no four-quarter figure")
    capex = dict(zip(QE[-4:], [5, 5, 6, 6.0]))
    check(cc.trailing(capex) == 22.0 and cc.trailing({QE[0]: 1, QE[3]: 1, QE[6]: 1, QE[8]: 1}) is None,
          "four consecutive quarters summed; a gappy set is not four quarters")
    db = str(Path(gate_tmp.mkdtemp("cc_formulas_")) / "chester.db")
    rows = []

    def put(key, vals, avail="2026-10-30T20:00:00+00:00"):
        for e, v in vals.items():
            rows.append({"registry_key": key, "instrument": None, "observed_at": e,
                         "available_at": avail, "value": float(v), "source": "edgar_xbrl",
                         "availability_kind": "observed"})
    put(cc.seg_key("AMZN", "revenue"), {k: v * 1e9 for k, v in rev.items()})
    put(cc.seg_key("AMZN", "operating_income"), {k: v * 1e9 for k, v in oi.items()})
    put(cc.cc_key("AMZN", "capex"), {k: v * 1e9 for k, v in capex.items()})
    put(cc.cc_key("AMZN", "operating_cash_flow"), {k: 8e9 for k in QE[-4:]})
    put(cc.cc_key("AMZN", "finance_lease_principal"), {k: 1e9 for k in QE[-4:]})
    put(cc.cc_key("GOOGL", "rpo"), {"2025-09-30": 100e9, "2026-09-30": 150e9})
    put(cc.cc_key("GOOGL", "capex"), {k: 10e9 for k in QE[-4:]})
    with observations.ObservationStore(db) as st:
        st.write_many(rows)
        r = cc.read(st, GATE_NOW)
    a = next(f for f in r["filers"] if f["ticker"] == "AMZN")
    g = next(f for f in r["filers"] if f["ticker"] == "GOOGL")
    check(abs(a["capex_ocf"] - 22 / 32) < 1e-12 and abs(a["fcf_leases"] - (32 - 22 - 4) * 1e9) < 1,
          "capex / OCF (0.69x) and FCF after leases (OCF less capex less finance-lease "
          "principal, four quarters) from the store")
    check(abs(g["rpo_growth"] - 0.5) < 1e-12 and abs(g["rpo_cover"] - 150 / 40) < 1e-12,
          "backlog: RPO's growth on the year and its cover of four quarters' capex")
    t = cc.table(r)
    check(t["rows"][0][0] == "AMZN" and "RPO not tagged" in t["rows"][0][3]
          and "−$" not in t["rows"][0][5] and "not stored" in t["rows"][3][4],
          "the table: an untagged RPO and an unstored figure say so")


def group_b() -> None:
    head("B. THE TREADMILL")
    qb = ["2024-06-30"] + QE          # ten quarters: the earlier quarter's margin too
    rev = dict(zip(qb, [9, 10, 11, 12, 13, 14, 15, 16, 17, 18.0]))
    oi = dict(zip(qb, [2.5, 3, 3.5, 4, 4.5, 5, 5.4, 5.7, 5.9, 6.0]))   # margin falling
    capex = dict(zip(qb, [5, 5, 5, 5, 5, 5, 6, 7, 8, 9.0]))            # +60%, +80% late
    tr = cc.treadmill(rev, oi, capex)
    check(tr["fired"] and tr["state"] == "ON" and len(tr["checks"]) == 2
          and all(c["capex_g"] > c["rev_g"] and c["im"] < c["im_prev"] for c in tr["checks"]),
          "capex outgrowing revenue in both quarters while the margin falls: ON")
    slow = dict(capex, **{QE[-2]: 5.0})
    check(not cc.treadmill(rev, oi, slow)["fired"], "one quarter short: off")
    rising = dict(zip(qb, [2.5, 3, 3.5, 4, 4.5, 5, 6, 7, 8, 9.0]))
    check(not cc.treadmill(rev, rising, capex)["fired"], "the margin rising: off")
    few = {k: v for k, v in rev.items() if k >= "2026-03-31"}
    check(cc.treadmill(few, oi, capex)["state"] == "insufficient",
          "too few quarters: insufficient, never a verdict")
    check(cc.config()["treadmill"]["quarters"] == 2
          and cc.config()["treadmill"]["capex_series"] == "actual",
          "two quarters; the capex series is actual, said so")


def group_c() -> None:
    head("C. THE PATHS")
    empty = Path(gate_tmp.mkdtemp("cc_noscan_"))
    f0 = cc.scan_financing(GATE_NOW, empty)
    r = {"filers": [], "financing": f0, "confirmed": []}
    ls = cc.lines(r)
    fin = next(x for x in ls if x.startswith("Financing-structure ledger"))
    check("no confirmed rows" in fin and "no signal-scan file proposes any yet" in fin,
          "no scan: 'no confirmed rows'")
    d = Path(gate_tmp.mkdtemp("cc_scan_"))
    (d / "signal-scan-2026-11.md").write_text(
        "# Signal scan\n## 3. Financing\n"
        "- F1 | ORCL | lease | a developer | $10bn | https://www.sec.gov/x\n"
        "- F2 | META | joint venture | a fund | $27bn | no url\n## 4. Other\n- x\n",
        encoding="utf-8")
    f1 = cc.scan_financing(GATE_NOW, d)
    check(f1["file"] == "signal-scan-2026-11.md" and [x["id"] for x in f1["proposed"]] == ["F1"],
          "a scan's Financing section: one row proposed, the URL-less line skipped")
    ls = cc.lines({"filers": [], "financing": f1, "confirmed": []})
    check(any("no confirmed rows; 1 proposed in signal-scan-2026-11.md" in x for x in ls),
          "proposed is not confirmed: O-4's sitting confirms")
    gpu = next(x for x in ls if x.startswith("GPU rental"))
    check("gap" in gpu and "Ornn" in gpu and "gpu.ai" in gpu,
          "the GPU row prints 'gap' naming V-105a's candidates")
    ul = next(x for x in ls if x.startswith("Useful lives"))
    check("83(b)" in ul and "not tracked" in ul, "the useful-life cross-reference")
    recs = cc.config()["dated_records"]
    check(recs and all(re.match(r"https://www\.sec\.gov/", x["url"]) for x in recs)
          and any("dated record" in x and "578 billion" in x for x in ls),
          "dated records carry their filed URLs and print 'dated record'")


def group_d() -> None:
    head("D. THE SR-16 FOLD")
    from daily_cascade import absorption_block as ab            # noqa: PLC0415
    src = (REPO / "daily_cascade" / "absorption_block.py").read_text(encoding="utf-8")
    i, j = src.index("f\"  {AI_CREDIT_LINE}\""), src.index("_private_credit_line()}")
    check(i < j, "row 6 sits in SR-16's Factor I lines, after the AI-credit line")
    pl = ab._private_credit_line()                              # noqa: SLF001
    check(pl.startswith("Private-credit window (item 123 row 6, folded into SR-16)")
          and "Oracle's spread: NOT TRACKED" in pl and "no dated record filed" in pl,
          "Oracle's spread 'not tracked' with no key; the undated records say so")
    ls = cc.lines({"filers": [], "financing": {"file": None, "proposed": []}, "confirmed": []})
    check(pl in ls, "and the panel prints the same line")


XML = """<xbrl>
<{p}context id="c1"><{p}entity><{p}segment><xbrldi:explicitMember dimension="us-gaap:StatementBusinessSegmentsAxis">x:CloudMember</xbrldi:explicitMember></{p}segment></{p}entity><{p}period><{p}startDate>2026-01-01</{p}startDate><{p}endDate>2026-06-30</{p}endDate></{p}period></{p}context>
<{p}context id="c2"><{p}entity><{p}segment><xbrldi:explicitMember dimension="us-gaap:StatementBusinessSegmentsAxis">x:CloudMember</xbrldi:explicitMember><xbrldi:explicitMember dimension="srt:ConsolidationItemsAxis">us-gaap:OperatingSegmentsMember</xbrldi:explicitMember></{p}segment></{p}entity><{p}period><{p}startDate>2026-04-01</{p}startDate><{p}endDate>2026-06-30</{p}endDate></{p}period></{p}context>
<{p}context id="c3"><{p}entity><{p}segment><xbrldi:explicitMember dimension="us-gaap:StatementBusinessSegmentsAxis">x:CloudMember</xbrldi:explicitMember><xbrldi:explicitMember dimension="srt:ProductOrServiceAxis">x:GpuMember</xbrldi:explicitMember></{p}segment></{p}entity><{p}period><{p}startDate>2026-04-01</{p}startDate><{p}endDate>2026-06-30</{p}endDate></{p}period></{p}context>
<{p}context id="c4"><{p}entity><{p}segment><xbrldi:explicitMember dimension="us-gaap:StatementBusinessSegmentsAxis">x:CloudMember</xbrldi:explicitMember></{p}segment></{p}entity><{p}period><{p}startDate>2026-01-01</{p}startDate><{p}endDate>2026-03-31</{p}endDate></{p}period></{p}context>
<us-gaap:Revenues contextRef="c1" unitRef="usd">25</us-gaap:Revenues>
<us-gaap:Revenues contextRef="c4" unitRef="usd">12</us-gaap:Revenues>
<us-gaap:Revenues contextRef="c3" unitRef="usd">999</us-gaap:Revenues>
<us-gaap:OperatingIncomeLoss contextRef="c2" unitRef="usd">4</us-gaap:OperatingIncomeLoss>
</xbrl>"""


def group_e() -> None:
    head("E. THE READERS")
    for p in ("", "xbrli:"):
        x = XML.format(p=p)
        rev = ex.instance_facts(x, ["us-gaap:Revenues"], ["x:CloudMember"],
                                "us-gaap:StatementBusinessSegmentsAxis", "2026-07-30T20:00:00+00:00")
        oi = ex.instance_facts(x, ["us-gaap:OperatingIncomeLoss"], ["x:CloudMember"],
                               "us-gaap:StatementBusinessSegmentsAxis", "2026-07-30T20:00:00+00:00")
        check(set(rev) == {("2026-01-01", "2026-06-30"), ("2026-01-01", "2026-03-31")}
              and set(oi) == {("2026-04-01", "2026-06-30")},
              f"prefix {p or '(none)'}: the segment's contexts, the operating-segments "
              f"qualifier kept, a product axis refused (999 never read)")
    q = ex.quarterly_flow(rev, "2026-01-01")
    check([(e, v) for e, _i, v, _k in q] == [("2026-03-31", 12.0), ("2026-06-30", 13.0)],
          "a half-year less its first quarter is the second quarter (25 - 12 = 13)")
    db = str(Path(gate_tmp.mkdtemp("cc_pit_")) / "chester.db")
    k = cc.seg_key("AMZN", "revenue")
    with observations.ObservationStore(db) as st:
        st.write_many([{"registry_key": k, "instrument": None, "observed_at": "2026-06-30",
                        "available_at": a, "value": v, "source": "edgar_xbrl",
                        "availability_kind": "observed"}
                       for a, v in (("2026-07-30T20:00:00+00:00", 13.0),
                                    ("2026-10-30T20:00:00+00:00", 13.5))])
        s1 = cc.series(st, k, "2026-08-01T00:00:00+00:00")
        s2 = cc.series(st, k, GATE_NOW)
    check(s1 == {"2026-06-30": 13.0} and s2 == {"2026-06-30": 13.5},
          "point in time: a cutoff sees only the vintage accepted by then")


def group_f() -> None:
    head("F. PLACEMENT AND HYGIENE")
    from daily_cascade import stack_hooks                       # noqa: PLC0415
    order = stack_hooks.ids("monthly", "slow", "sourced_figures")
    check(stack_hooks.wired("monthly", "slow", "altdata.cash_cycle", "slow_subsection",
                            ["st", "now"])
          and order.index("monthly-slow-cash-cycle") == order.index("monthly-slow-capex-chain") + 1,
          "the Monthly's hook, right after the AI capex chain")
    tb = (REPO / "daily_cascade" / "themes_block.py").read_text(encoding="utf-8")
    wk = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    check("cash_cycle.slow_subsection(st, now)" in tb and "cash_cycle" not in wk,
          "the Themes refresh prints it; the Weekly prints nothing")
    keys = ex.CC_KEYS
    reg = {k: derived.registry_entry(k) for k in keys}
    check(len(keys) == 48 and all(reg.values())
          and all(e.get("trigger_eligible") is False for e in reg.values())
          and all(derived.market_state_barred(e) for e in reg.values()),
          "the 48 keys registered, trigger-ineligible and barred from the market-state object")
    from altdata import narratives as nr                        # noqa: PLC0415
    p = nr.load_config().get("proposals") or {}
    check(all(k in p and not nr.validate_config_story(k, p[k])
              for k in ("ai_capex_j_curve", "ai_capex_treadmill"))
          and "semiconductor and hardware franchise" in p["ai_capex_j_curve"]["direction"]
          and "Bull Rebuttal" in p["ai_capex_treadmill"]["direction"],
          "the two PROPOSED entries: the J-curve with its incentive tag, the house Bull Rebuttal")
    code = (REPO / "altdata" / "cash_cycle.py").read_text(encoding="utf-8")
    check(not re.search(r"requests|urllib|http_get|_sec_get|import_yfinance|flashalpha", code),
          "the scorecard reads the store only, fetches nothing, reads no vendor")
    mk = __import__("gate_list").makefile_text(REPO)
    check("tools/validate_item_123.py" in mk, "the gate is in the list")


def main() -> int:
    pin_clock()
    print(f"the gate's clock is pinned to {GATE_NOW}")
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
