"""
Signal triage Batch 14, Part A1 (a56, session A): items 64, 69 and 70.

  A  ITEM 64, THE EXCESS CAPE YIELD. 100 / CAPE less the month's mean DFII10,
     by hand on a fixture; dual percentiles (five years and full, each with n);
     labelled as not Shiller's own real rate; absent with its reason when CAPE
     is not stored; the forward version named as a listed gap.
  B  ITEM 69, THE HOUSING FOOTPRINT. The PMMS rate less the 10-year on the same
     day, bp, with dual percentiles; the current-coupon MBS spread and the GSE
     retained portfolios print "not tracked", each gap with its reason; the
     housing block prints them.
  C  ITEM 69, REAL HOME PRICES SINCE 1890. Shiller's housing sheet parsed
     (annual rows to 1952, monthly from 1953, 2026.375 = May); the percentile of
     the latest month among one point a year, by hand.
  D  ITEM 70, THE NOMINAL-GROWTH ANCHOR. The quarter's mean 10-year less the 10-
     and 5-year nominal GDP CAGR, bp, by hand, with dual percentiles; the
     fair-value range with and without the twin-deficit fit; the line prints in
     the 10-year attribution block.
  E  THE PROPOSAL PATH. The narrative entry validates, seeds into a scratch
     register as PROPOSED (origin config_proposal), carries F6's tag, and is not
     confirmed.
  F  PLACEMENT AND RIGHTS. The Monthly's slow layers carry the sub-section; item
     21's scorecard column is named "not built"; nothing here writes the store,
     reads a vendor value or a by-hand key, enters a composite or the
     market-state object, or names a person; the new key is registered.
  G  THE DATED APPENDIX. The 10-year record (5 Oct 2026's closes), the 8%
     forecast and item 20's housing intervention line are queued.

Synthetic fixtures only: no live store, no network, no model.

    python tools/validate_batch14_a1.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import datetime as dt
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
# The dated-appendix queue is a directory (S1 part 4): read the entries.
import appendix_queue_index                                 # noqa: E402
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gate_tmp  # noqa: E402
import yaml  # noqa: E402

from altdata import batch14_a1 as b14  # noqa: E402
from altdata import observations  # noqa: E402

PASS = FAIL = 0
LINE = "=" * 78
NOW = "2026-10-20T23:00:00+00:00"


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


def store(rows: list[tuple]) -> observations.ObservationStore:
    db = str(Path(gate_tmp.mkdtemp("b14a1_")) / "obs.db")
    with observations.ObservationStore(db) as st:
        st.write_many([{"registry_key": k, "instrument": None, "observed_at": d,
                        "available_at": d + "T21:00:00+00:00", "value": float(v),
                        "source": "fixture"} for k, d, v in rows])
    return observations.ObservationStore(db)


def months(y0: int, m0: int, n: int):
    for i in range(n):
        k = y0 * 12 + m0 - 1 + i
        yield f"{k // 12:04d}-{k % 12 + 1:02d}-01"


def group_a() -> None:
    head("A. ITEM 64, THE EXCESS CAPE YIELD")
    rows = []
    ms = list(months(2018, 1, 100))                       # Jan 2018 .. Apr 2026
    for i, m in enumerate(ms):
        rows.append(("shiller.cape", m, 20.0 + i * 0.1))
        for day in ("05", "15"):
            rows.append(("fred.tips_10y", m[:8] + day, 1.0 + i * 0.01 + (0.1 if day == "15" else 0)))
    st = store(rows)
    e = b14.excess_cape_yield(st, NOW)
    i = len(ms) - 1
    want = round(100.0 / (20.0 + i * 0.1) - (1.0 + i * 0.01 + 0.05), 4)
    check(not e["absent"] and e["month"] == "2026-04" and abs(e["value_pp"] - want) < 1e-9,
          f"100 / CAPE less the month's mean DFII10, by hand ({e.get('value_pp')} vs {want})")
    lz = e["lens"]
    check(lz["n_full"] == 100 and lz["n_window"] == 60 and lz["percentile_full"] is not None
          and lz["percentile_window"] is not None and not lz["same"],
          f"dual percentiles: five years (n={lz['n_window']}) and full (n={lz['n_full']})")
    line = b14.ecy_line(e)
    check("not Shiller's own real rate" in line and "percentile of 5 years" in line,
          f"the line labels it and prints both percentiles ({line[:110]}...)")
    e0 = b14.excess_cape_yield(store([("fred.tips_10y", "2026-01-05", 2.0)]), NOW)
    check(e0["absent"] and "CAPE is not stored" in b14.ecy_line(e0),
          "absent with its reason when CAPE is not stored")
    check("forward earnings yield" in b14.NOT_TRACKED["forward_ecy"],
          "the forward-earnings-yield version is a listed gap")


def group_b() -> None:
    head("B. ITEM 69, THE HOUSING FOOTPRINT")
    rows, d = [], dt.date(2019, 1, 3)
    while d.isoformat() <= "2026-10-15":
        k = (d - dt.date(2019, 1, 3)).days // 7
        rows.append(("fred.mortgage_30y", d.isoformat(), 6.0 + (k % 10) * 0.05))
        rows.append(("fred.yield_10y", d.isoformat(), 4.0 + (k % 7) * 0.03))
        d += dt.timedelta(days=7)
    st = store(rows)
    f = b14.footprint(st, NOW)
    m = f["mortgage_spread"]
    last_k = (dt.date.fromisoformat(m["as_of"]) - dt.date(2019, 1, 3)).days // 7
    want = round(((6.0 + (last_k % 10) * 0.05) - (4.0 + (last_k % 7) * 0.03)) * 100, 6)
    check(not m["absent"] and abs(m["spread_bp"] - want) < 1e-6,
          f"PMMS less the 10-year on the same day, bp ({m['spread_bp']:.1f} vs {want:.1f})")
    check(m["lens"]["n_window"] < m["lens"]["n_full"] and m["lens"]["percentile_window"] is not None,
          f"dual percentiles (n={m['lens']['n_window']} and {m['lens']['n_full']})")
    ls = b14.footprint_lines(f)
    check("The current-coupon MBS spread over the 10-year: not tracked." in ls
          and "GSE retained-portfolio holdings: not tracked." in ls
          and len(f["not_tracked"]) == 2 and all("keyless" in g for g in f["not_tracked"]),
          "the MBS spread and the GSE holdings print \"not tracked\", each gap with its reason")
    from daily_cascade import rates_transmission_block as blk
    src = Path(blk.__file__).read_text(encoding="utf-8")
    check("batch14_a1.footprint(st, now)" in src and "batch14_a1.footprint_lines" in src,
          "the housing block (Weekly and Monthly Plumbing) prints the footprint")
    m0 = b14.mortgage_spread(store([("fred.yield_10y", "2026-10-15", 4.0)]), NOW)
    check(m0["absent"] and "PMMS" in m0["reason"], "absent with its reason without PMMS")


def group_c() -> None:
    head("C. ITEM 69, REAL HOME PRICES SINCE 1890")
    from altdata.sources import shiller
    table = [["U.S. Home Price"], [""], [""], ["", "Real"], ["", "Home"], ["", "Price"],
             ["Date", "Index"], [1890.0, 100.0], [1952.0, 90.0],
             [1953.0 + 0.5 / 12, 91.0], [2026.375, 210.0]]
    rows = shiller.housing_rows(table, "2026-10-06T14:34:05+00:00", "observed")
    check([r["observed_at"] for r in rows] == ["1890-01-01", "1952-01-01", "1953-01-01",
                                                "2026-05-01"]
          and all(r["registry_key"] == "shiller.real_home_price" for r in rows),
          "the sheet parses: annual rows to 1952, monthly from 1953, 2026.375 = May")
    pts = [("shiller.real_home_price", f"{y}-01-01", 100.0 + (y - 1890) * 0.5)
           for y in range(1890, 1953)]
    for y in range(1953, 2026):
        for mm in (1, 7):
            pts.append(("shiller.real_home_price", f"{y}-{mm:02d}-01", 120.0 + (y - 1953)))
    pts.append(("shiller.real_home_price", "2026-07-01", 150.0))
    h = b14.real_home_price(store(pts), NOW)
    annual = [100.0 + (y - 1890) * 0.5 for y in range(1890, 1953)] + \
             [120.0 + (y - 1953) for y in range(1953, 2026)]
    ranked = annual + [150.0]
    want = 100.0 * sum(1 for v in ranked if v <= 150.0) / len(ranked)
    check(not h["absent"] and h["n_years"] == len(ranked) == 137
          and abs(h["percentile"] - want) < 0.05 and h["from"] == 1890,
          f"the latest month among one point a year since 1890, by hand "
          f"({h['percentile']:.1f} vs {want:.1f}, n={h['n_years']})")
    line = b14.home_line(h)
    check("since 1890" in line and "one point a year" in line, f"the line ({line})")


def group_d() -> None:
    head("D. ITEM 70, THE NOMINAL-GROWTH ANCHOR")
    rows = []
    for i in range(80):                                   # 2006Q3 .. 2026Q2
        k = 2006 * 4 + 2 + i
        q = f"{k // 4:04d}-{k % 4 * 3 + 1:02d}-01"
        rows.append(("fred.gdp_nominal", q, 10000.0 * 1.05 ** (i / 4)))
        for mm in range(3):
            rows.append(("fred.yield_10y", f"{k // 4:04d}-{k % 4 * 3 + 1 + mm:02d}-15", 6.0))
    rows.append(("fred.yield_10y", "2026-10-15", 5.5))
    st = store(rows)
    a = b14.nominal_growth_anchor(st, NOW)
    l10, l5 = a["legs"][10], a["legs"][5]
    check(not a["absent"] and abs(l10["cagr_pct"] - 5.0) < 1e-6 and abs(l5["cagr_pct"] - 5.0) < 1e-6
          and abs(l10["gap_bp"] - 100.0) < 0.06 and abs(l5["gap_bp"] - 100.0) < 0.06,
          f"10y less the 10- and 5-year CAGR, by hand (+{l10['gap_bp']} and +{l5['gap_bp']} bp)")
    check(l10["lens"]["n_full"] == 40 and l5["lens"]["n_full"] == 60
          and l5["lens"]["n_window"] == 20 and not l5["lens"]["same"],
          "quarterly, with dual percentiles (n per window)")
    fis = {"state": "ok", "us_fitted_pct": 4.4}
    ls = b14.anchor_lines(a, fis)
    rng = [x for x in ls if x.startswith("Fair-value range")]
    check(rng and "4.40% to 5.00%" in rng[0] and "twin-deficit fit 4.40%" in rng[0]
          and "against 5.50%" in rng[0] and "US macro r-g" in ls[0],
          f"the fair-value range beside the twin-deficit fit ({rng[0] if rng else None})")
    rng2 = [x for x in b14.anchor_lines(a, None) if x.startswith("Fair-value range")]
    check(rng2 and "twin-deficit fit is absent" in rng2[0],
          "without the twin-deficit fit, the range says so")
    from daily_cascade import batch5_block
    sub = batch5_block._attribution(st, NOW)                       # noqa: SLF001
    check(any(x.startswith("The 10-year less the 10-year nominal GDP CAGR") for x in sub["lines"]),
          "the anchor prints in the 10-year attribution block")


def group_e() -> None:
    head("E. THE PROPOSAL PATH")
    from altdata import narratives as nar
    cfg = yaml.safe_load((REPO / "config" / "narratives.yaml").read_text(encoding="utf-8"))
    spec = cfg["proposals"]["gse_mbs_purchase_floor"]
    check(nar.validate_config_story("gse_mbs_purchase_floor", spec) == [],
          "the entry validates as a config proposal")
    tag = "verified (announcement of 8 Jan 2026); the post's source is a promoter"
    check(tag in " ".join(str(spec["proposed_by"]).split()),
          "it carries F6's tag")
    db = str(Path(gate_tmp.mkdtemp("b14nar_")) / "nar.db")
    with nar.NarrativeRegister(db) as reg:
        reg.seed({"version": cfg.get("version"), "narratives": {},
                  "proposals": {"gse_mbs_purchase_floor": spec}})
    row = sqlite3.connect(db).execute(
        "SELECT status, origin FROM narratives WHERE narrative_id='gse_mbs_purchase_floor'"
    ).fetchone()
    check(row == ("proposed", "config_proposal"),
          f"seeded as PROPOSED through the existing path ({row}); confirming stays the operator's")


def group_f() -> None:
    head("F. PLACEMENT AND RIGHTS")
    st = store([("shiller.cape", "2026-04-01", 25.0), ("fred.tips_10y", "2026-04-10", 2.0),
                ("shiller.real_home_price", "2026-04-01", 200.0)])
    from daily_cascade import batch14_a1_block as blk
    sub = blk.slow_subsection(st, NOW)
    check(sub and sub["title"].startswith("The excess CAPE yield") and len(sub["lines"]) == 2
          and any("scorecard is not built" in g for g in sub["not_tracked"]),
          "the slow sub-section; item 21's scorecard column named \"not built\"")
    ms = (REPO / "monthly_macro" / "stack.py").read_text(encoding="utf-8")
    check(__import__('daily_cascade.stack_hooks').stack_hooks.wired("monthly", "slow", "daily_cascade.batch14_a1_block", "slow_subsection", ["st", "now"]),
          "the Monthly's slow layers carry it")
    files = [REPO / "altdata" / "batch14_a1.py", REPO / "daily_cascade" / "batch14_a1_block.py"]
    src = "\n".join(p.read_text(encoding="utf-8") for p in files)
    imports = "\n".join(l for l in src.splitlines() if re.match(r"\s*(from|import)\s", l))
    check(not re.search(r"\.write\(|write_many|INSERT", src)
          and "manual_input" not in src and "vendor." not in src
          and not re.search(r"regime|market_state|composite|manual_input", imports),
          "no store write, no by-hand key, no vendor value, no composite or market-state read")
    check(set(b14.KEYS.values()) <= {"shiller.cape", "fred.tips_10y", "fred.yield_10y",
                                     "fred.mortgage_30y", "fred.gdp_nominal",
                                     "shiller.real_home_price"},
          "every key read is FRED's or Shiller's")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    check("shiller.real_home_price" in (reg.get("metrics") or reg),
          "the new key, shiller.real_home_price, is registered")
    mine = src + (REPO / "config" / "narratives.yaml").read_text(encoding="utf-8").split(
        "gse_mbs_purchase_floor:")[1] + appendix_queue_index.queue_text(REPO).split("(Batch 14 item 64)")[1]
    check(not re.search(r"Bradshaw|Nobler|Pulte|Trump|Bilello|Varghese|@[A-Za-z]", mine),
          "no person's name or handle in the new code, proposal or appendix lines")


def group_g() -> None:
    head("G. THE DATED APPENDIX")
    q = appendix_queue_index.queue_text(REPO)
    check("(Batch 14 item 64)" in q and "5.31% on 5 Oct 2026" in q and "2.95%" in q
          and "14 May 2002" in q and "24 Nov 2008" in q,
          "the 10-year record: 5 Oct 2026's closes, highest since 2002 and 2008")
    check("(Batch 14 item 70)" in q and "8%" in q and "appendix only" in q,
          "the 8% forecast, appendix only")
    check("housing intervention" in q and "Dated 8 Jan 2026" in q and "https://" in q,
          "item 20's housing intervention line, dated, with its citation")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g):
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
