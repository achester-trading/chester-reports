"""
Signal-triage Batch 17, item 97(b) (docs/change-order-signal-triage-batch-17-
2026-10-26.md; B79, b79-capitulation-count, 26 Oct 2026): the Capitulation Count's
three feeds.

  A  CBOE PUT/CALL, THE PARSER on the stored file of 23 Oct 2026: equity 0.67,
     index 1.10, total 0.93, found by name (a shuffled list reads the same); a
     file missing the equity ratio is refused, never zero-filled.
  B  THE REFUSAL PATH: the switch off returns STALE with its reason and writes
     nothing; a robots refusal raises before any file is requested; a 4xx is
     requested once and never retried.
  C  THE DERIVED COMPANIONS: the equity ratio's 20-session mean and each ratio's
     one-year percentile through derived.percentile_of, not stored.
  D  FRED: VXNCLS and VXVCLS in the pull as fred.vxn and fred.vix3m; the VIX/VIX3M
     ratio read from FRED's pair first, else calc.vix3m_over_vix inverted.
  E  FLOWS: every fund leg and ICI listed with its robots and terms verdict and the
     state "gap"; no flows writer exists.
  F  REGISTERED: the keys, the source block (built, switched off), the lag family,
     the market-state bar.

Synthetic fixtures and one stored public file only: no live store, no network.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp                                    # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
TD = Path(mkdtemp("capitulation-feeds-gate-"))
LIVE_DB = REPO / "data" / "chester.db"
LIVE_DB_AT_START = LIVE_DB.exists()
FIXTURE = REPO / "tests" / "fixtures" / "capitulation" / "cboe_daily_options_2026-10-23.json"


def check(ok: bool, what: str) -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS  {what}")
    else:
        FAIL += 1
        print(f"  FAIL  {what}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def group_a():
    head("A  CBOE PUT/CALL: THE PARSER")
    from altdata.sources import cboe_putcall as pc
    text = FIXTURE.read_text(encoding="utf-8")
    rows = pc.rows_from_json(text, "2026-10-23", "2026-10-23T21:30:00+00:00", "observed")
    got = {r["registry_key"]: r["value"] for r in rows}
    check(got == {"cboe.pc_equity": 0.67, "cboe.pc_index": 1.10, "cboe.pc_total": 0.93},
          f"23 Oct 2026: equity 0.67, index 1.10, total 0.93 (got {got})")
    check(all(r["observed_at"] == "2026-10-23" for r in rows), "observed_at is the file's session")
    doc = json.loads(text)
    doc["ratios"] = list(reversed(doc["ratios"]))
    rows2 = pc.rows_from_json(json.dumps(doc), "2026-10-23", "x", "observed")
    check({r["registry_key"]: r["value"] for r in rows2} == got, "found by name: a shuffled list reads the same")
    doc["ratios"] = [r for r in doc["ratios"] if r["name"] != "EQUITY PUT/CALL RATIO"]
    try:
        pc.rows_from_json(json.dumps(doc), "2026-10-23", "x", "observed")
        check(False, "a file without the equity ratio is refused")
    except ValueError:
        check(True, "a file without the equity ratio is refused, never zero-filled")


def group_b():
    head("B  THE REFUSAL PATH: STALE WITH ITS REASON, NO RETRY")
    from altdata import observations
    from altdata.sources import _publication as pub
    from altdata.sources import cboe_putcall as pc
    check(pc.ENABLED is False, "the writer ships switched off (pending the ruling on Cboe's terms)")
    db = observations.ObservationStore(str(TD / "feeds.db"))
    try:
        out = pub.run(pc.SOURCE, pc.KEYS, lambda: pc.fetch_rows(["2026-10-23"]), db=db)
        n = db.conn.execute("SELECT count(*) FROM observations").fetchone()[0]
    finally:
        db.close()
    check(out["status"] == pub.STALE and "switched off" in out["reason"] and out["written"] == 0 and n == 0,
          f"switched off: STALE, '{out.get('reason', '')[:50]}...', nothing written")
    calls = []

    def get(u):
        calls.append(u)
        raise RuntimeError("must not be called")
    refuse = lambda ru: "User-agent: *\nDisallow: /us/options/\nDisallow: /data/\n"  # noqa: E731
    try:
        pc.fetch_rows(["2026-10-23"], get=get, robots=refuse, enabled=True)
        check(False, "a robots refusal raises")
    except PermissionError as exc:
        check("robots.txt" in str(exc) and not calls,
              "a robots refusal raises before any file is requested")
    from altdata.sources._base import FetchError
    tries = []

    def get403(u):
        tries.append(u)
        raise FetchError(f"HTTP 403 for {u}")
    try:
        pc.fetch_rows(["2026-10-23"], get=get403, robots=lambda ru: "", enabled=True)
        check(False, "a 4xx raises")
    except FetchError:
        check(len(tries) == 1, "a 4xx is requested once and never retried around")
    src = (REPO / "altdata" / "sources" / "cboe_putcall.py").read_text(encoding="utf-8")
    check("max_retries=1" in src, "the live fetch is one attempt (max_retries=1)")


def group_c():
    head("C  THE DERIVED COMPANIONS")
    from altdata.sources import cboe_putcall as pc
    days = [f"2026-{m:02d}-{d:02d}" for m in range(1, 13) for d in range(1, 29)][:300]
    eq = [(d, 0.5 + (i % 10) / 20) for i, d in enumerate(days)]
    out = pc.mean_and_percentiles({"cboe.pc_equity": eq})
    means = [(d, v) for k, d, v in out if k == "calc.pc_equity_20d"]
    want = sum(v for _, v in eq[-20:]) / 20
    check(abs(means[-1][1] - want) < 1e-12 and means[0][0] == eq[19][0],
          "the 20-session mean starts at the 20th session and equals the window's mean")
    pcts = [(d, v) for k, d, v in out if k == "calc.pc_equity_pct_1y"]
    check(len(pcts) == len(eq) - 251 and all(0 <= v <= 100 for _, v in pcts),
          "the one-year percentile starts at the 252nd session, 0 to 100")
    check(set(pc.DERIVED_KEYS) >= {k for k, _, _ in out}, "only the declared companions are computed")


def group_d():
    head("D  FRED: VXN AND VIX3M; THE RATIO")
    from altdata import config
    ids = {s.fred_id: s.key for s in config.FRED_PULL_SERIES}
    check(ids.get("VXNCLS") == "vxn" and ids.get("VXVCLS") == "vix3m",
          "VXNCLS -> fred.vxn and VXVCLS -> fred.vix3m are in the pull")
    import yaml
    cfg = yaml.safe_load((REPO / "config" / "capitulation_count.yaml").read_text(encoding="utf-8"))
    vol = cfg["feeds"]["vol_indices"]
    check(vol["ratio_from"] == ["fred.vix3m", "fred.vix"] and vol["ratio_fallback"] == "calc.vix3m_over_vix",
          "the ratio: FRED's pair first, else calc.vix3m_over_vix inverted (no new stored series)")


def group_e():
    head("E  FLOWS: EVERY LEG LISTED, NONE BUILT")
    import yaml
    cfg = yaml.safe_load((REPO / "config" / "capitulation_count.yaml").read_text(encoding="utf-8"))
    flows = {f["fund"].split()[0]: f for f in cfg["feeds"]["flows"]}
    check(set(flows) >= {"SPY", "QQQ", "IWM", "SMH", "ICI"}, "SPY, QQQ, IWM, SMH and ICI are each listed")
    check(all(f.get("state") == "gap" and f.get("robots") and f.get("terms") for f in flows.values()),
          "each carries its robots and terms verdict and the state 'gap'")
    built = [p.name for p in (REPO / "altdata" / "sources").glob("*.py")
             if "etf_flows" in p.name or "fund_flows" in p.name]
    check(not built, "no flows writer exists")


def group_f():
    head("F  REGISTERED")
    import yaml
    reg = (REPO / "metrics_registry.yaml").read_text(encoding="utf-8")
    for k in ("cboe.pc_equity", "cboe.pc_index", "cboe.pc_total"):
        check(f"\n  {k}:\n    source: cboe_putcall" in reg.replace("\r\n", "\n"), f"{k} is registered to cboe_putcall")
    check("fred_batch17:" in reg and "fred.vxn: conditions" in reg, "the FRED block fred_batch17 carries fred.vxn and fred.vix3m")
    src = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))
    block = (src.get("sources") or src).get("cboe_putcall") or {}
    check(block.get("status") == "built" and "TERMS" in str(block.get("license")),
          "the source block: built, with its robots and terms readings")
    lags = yaml.safe_load((REPO / "config" / "publication_lags.yaml").read_text(encoding="utf-8"))
    check(any(f.get("id") == "cboe_putcall" for f in lags["families"]), "a publication-lag family for cboe_putcall")
    barred = yaml.safe_load(reg)["market_state_barred"]
    check(any("cboe.pc_*" in b.get("keys", []) and "fred.vxn" in b.get("keys", []) for b in barred),
          "the feeds are barred from the market-state object")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    head("THE GATE RUN")
    check(LIVE_DB.exists() == LIVE_DB_AT_START, "this gate run created no data/chester.db")
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
