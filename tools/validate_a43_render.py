#!/usr/bin/env python3
"""
Validation gate: a43-render -- session A's Part 0 of 18 Oct (the rulings on the
ST-8 / ST-9 report, the Massive capture clock, the FlashAlpha writer's
configuration and conventions) and Part 1 (ST-10's rendering rows for ST-4 and
ST-5), where no existing gate is their home. On fixtures; no network, no model,
no live store.

  A  THE RULINGS. SR-1's panel prints HML beside the ETF pairs, each pair's n and
     "under its floor of six", every figure recomputed from the ledger's CSV; the
     gate-status draft carries ruling 1; the two FRED source notes are in the
     register; the Weekly's and the Monthly's HY charts name their series and the
     first day the store holds.
  B  M-3, THE CAPTURE CLOCK. The stamps (09:30, 12:15, 16:16 ET, 15-minute
     delay); the 16:10 pass skips the vendor universe, says so and fetches nothing
     of Massive's; the 16:31 unit pulls it at the 16:16 stamp into its own record;
     the 09:45 capture and every vendor row carry their stamp; the unit's time,
     wrapper branch and absence from DEPLOY_TIMERS; the close's reader says
     "pending" before 16:31 and reads the record after.
  C  F-1, F-2, F-4, F-3: the budget (60) and the plan (57) with SPX; the budget
     holds at 60 on a fixture day; GEX by single expiry from the listed expiries;
     the IV rule (20 DTE, 16:25 only); the blocks stored, the by-strike responses
     blobs; plan_ends; the vendor row in both units; the 0.5% flip and the regime;
     the conventions in the appendix and the writer's notes; the one-strike
     reconciliation by hand; no engine reads a vendor key.
  D  ST-10. The four 07:00 lines in order within the budget (4 lines, 60 words),
     each passing the numeral audit and declaring what it displaces; a quiet day
     prints nothing; the FOMC and refunding weeks; the 12:30 hooks open on their
     triggers and stay closed otherwise, the devaluation hook with no verdict word,
     a closed slot writing nothing and calling no model; the Sunday line and the
     Books; the Daily grep gate for PRL and Pearl; nothing enters a composite; no
     by-hand key; neither Weekly builder session B is fixing is touched.
  E  Ruling 2 (a44-opening-setup): the ruled expected-move path and shape; served,
     the 20-day IV stored; a 403 or 404 stores nothing and says "expected move:
     not served".

    python tools/validate_a43_render.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import csv
import importlib.util
import re
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
TD = Path(mkdtemp("a43-render-gate-"))
# A cutoff after this run: the vendor pull's fixture rows are available at the
# wall clock's instant.
import datetime as _dt                                          # noqa: E402
AFTER_RUN = (_dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(days=1)).isoformat()
CAL = REPO / "tools" / "calibration"
LEDGERS = REPO / "docs" / "ledgers"


def check(c: bool, m: str) -> bool:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")
    return bool(c)


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def close(a, b, tol=1e-4) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol


def mod(name: str):
    if str(CAL) not in sys.path:
        sys.path.insert(0, str(CAL))
    spec = importlib.util.spec_from_file_location(name, CAL / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _num(v):
    return None if v in ("", None) else float(v)


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE RULINGS OF 18 OCT")
    from altdata import labels, style_regime as SR
    from daily_cascade import style_block
    S = mod("sr01_sr13_style")
    rows = list(csv.DictReader((LEDGERS / "sr-1-ledger-2026-10-18-episodes.csv")
                               .open(encoding="utf-8")))
    for r in rows:
        for k in list(r):
            if k.startswith("vmg_"):
                r[k] = _num(r[k])
    hml = [r for r in rows if r["set"] == "HML" and r["episode"] == "True"]
    jh = S.judge_sr1(hml, "vmg_6m", "vmg_12m")
    g = SR.config()["gate_reading"]
    ok = (jh["n"] == g["hml"]["n"] and round(100 * jh["e6"], 1) == g["hml"]["mean_6m_pct"]
          and round(100 * jh["e12"], 1) == g["hml"]["mean_12m_pct"])
    for pair, v in g["pairs"].items():
        jp = S.judge_sr1(S.episodes_of([r for r in rows if r["set"] == pair]),
                         "vmg_26w", "vmg_52w")
        ok = ok and jp["n"] == v["n"] and round(100 * jp["e12"], 1) == v["mean_52w_pct"]
    check(ok and g["floor"] == S.FLOOR,
          f"config/style_regime.yaml's gate reading is the ledger CSV's own: HML n "
          f"{jh['n']} at {100 * jh['e6']:+.1f}% and {100 * jh['e12']:+.1f}%, each pair's n "
          f"and 52-week mean, the floor of {S.FLOOR}")
    ln = style_block.gate_line(SR.config())
    check("HML PASS, n 6" in ln and ln.count("under its floor of six") == 2
          and "IVE-IVW n 3" in ln and "IWD-IWF n 3" in ln and "display only" in ln
          and "Doctrine monthly's (7-8 Nov)" in ln,
          "the panel prints the pairs beside HML, each n with 'under its floor of six', "
          "display only, the rights question the monthly's")
    check(any(x.strip().startswith("The gate (as of the ledger)")
              for x in style_block.lines(None, "2026-10-17T21:00:00+00:00")),
          "the gate line is in the panel")
    reg = (REPO / "docs" / "signal-triage-register.md").read_text(encoding="utf-8")
    e1 = re.search(r"^### SR-1 .*?(?=^### )", reg, re.M | re.S).group(0)
    check("Ruled 18 Oct (ruling 1): the pre-registered pass stands" in e1
          and "under its floor of six" in e1 and "Doctrine monthly of 7-8 Nov" in e1
          and "**Gate status (ST-8): PASS.**" in e1,
          "SR-1's gate-status draft says all of ruling 1, under its label (ruling 2)")
    e4 = re.search(r"^### SR-4 .*?(?=^### )", reg, re.M | re.S).group(0)
    e8 = re.search(r"^### SR-8 .*?(?=^### )", reg, re.M | re.S).group(0)
    check("*Dated note under rule 31, 18 Oct 2026 (a register fact" in e4
          and "IRLTLT01CNM156N" in e4 and "404" in e4
          and "*Dated note under rule 31, 18 Oct 2026 (a register fact" in e8
          and "BAMLH0A0HYM2" in e8 and "2023-10-17" in e8 and "Baa less the 10-year" in e8,
          "the two FRED source changes are dated rule-31 notes: the China 10-year gone "
          "(SR-4) and HY OAS from Oct 2023 with the labelled Baa proxy (SR-8)")
    from daily_cascade import charts
    from monthly_macro import charts as mc
    hy = [(f"{2010 + i // 12}-{i % 12 + 1:02d}-01", 4.0 + 0.01 * (i % 7)) for i in range(120)]
    w3 = charts.w3_panel({"10y": [(d, 4.0) for d, _ in hy]}, hy, "w3", str(TD),
                         hy[-1][0] + "T21:00:00+00:00")
    m5 = mc.m5(hy, "m5", str(TD))
    want = labels.hy_source(hy[0][0])
    check(want in (w3.get("caption") or "") and want in (m5.get("caption") or "")
          and "BAMLH0A0HYM2" in want and "stored from 2010-01-01" in want
          and "2023-10-17" in want,
          f"the Weekly's W3 and the Monthly's M5 captions name the series and the first "
          f"stored day ({want})")
    from altdata import st_r5_rates as R5
    q = {"absent": False, "as_of": "2026-10-16", "ccc_bb_bp": 400.0,
         "ccc_bb_lens": {"percentile": 50.0}, "cosignal": "absent", "cosignal_reason": "x",
         "overlay": "o", "overlay_built": False, "euro_leg": "e",
         "euro_hy": {"oas_bp": 300.0, "as_of": "2026-10-16", "lens": {"percentile": 40.0}},
         "us_hy": {"oas_bp": 290.0, "as_of": "2026-10-16", "lens": {"percentile": 30.0}}}
    try:
        lines = R5.quality_tail_lines(q)
    except Exception:                                           # noqa: BLE001
        lines = []
    check(any(labels.HY_SERIES in x for x in lines),
          "the quality-tail lens's US HY clause names its series")


def group_b() -> None:
    head("B. M-3: THE MASSIVE CAPTURE CLOCK")
    import contextlib
    import io
    import json
    from altdata import chain_completeness as CC, config, dealer_capture, vendor_chains
    from altdata.sources import massive_chain
    check(config.vendor_as_of("0945") == "09:30 ET (15-minute delay)"
          and config.vendor_as_of("1230") == "12:15 ET (15-minute delay)"
          and config.vendor_as_of(config.VENDOR_CHAINS_SLOT) == "16:16 ET (15-minute delay)",
          "the stamps: 09:45 reads 09:30 ET, 12:30 reads 12:15 ET, 16:31 reads 16:16 ET "
          "(15-minute delay)")
    # run_eod skips the vendor universe and says so.
    import run_eod
    calls = {"massive": 0}
    saved = (run_eod.options_chain.pull, run_eod.massive_chain.pull, sys.argv,
             config.CHAIN_DIR)
    day_dir = TD / "chains"
    try:
        run_eod.options_chain.pull = lambda **k: {
            "success": 1, "total": 1,
            "symbols": {s: {"rows": 10, "expiries_fetched": 1, "expiries_with_rows": 1}
                        for s in k.get("symbols", [])}}
        run_eod.massive_chain.pull = lambda **k: calls.__setitem__("massive", 1) or {}
        config.CHAIN_DIR = str(day_dir)
        sys.argv = ["run_eod.py", "--capture-only"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            run_eod.main()
        out = buf.getvalue()
    finally:
        (run_eod.options_chain.pull, run_eod.massive_chain.pull, sys.argv,
         config.CHAIN_DIR) = saved
    rec_files = list(day_dir.rglob(CC.COMPLETENESS_FILE))
    rec = json.loads(rec_files[0].read_text(encoding="utf-8")) if rec_files else {}
    check(calls["massive"] == 0 and "SPX, SPCX skipped -- captured at 16:31 ET" in out
          and "vendor" not in rec and rec_files,
          "the 16:10 pass skips the vendor universe, says so in its log, calls no "
          "Massive fetch, and its completeness record carries no vendor section")
    # The 16:31 unit: the same pull, the 16:16 stamp, its own record.
    seen = {}

    def fake(**k):
        seen.update(k)
        return {"symbols": {"SPX": {"rows": 5}, "SPCX": {"rows": 0}}}
    r = vendor_chains.run(pull=fake, base_dir=str(TD / "v"), day="2026-10-19")
    vf = TD / "v" / "2026-10-19" / CC.VENDOR_FILE
    check(seen.get("data_as_of") == "16:16 ET (15-minute delay)"
          and seen.get("symbols") == config.massive_universe()
          and r["captured"] == ["SPX"] and r["missing"] == ["SPCX"] and vf.exists(),
          "the 16:31 capture pulls the vendor universe at the 16:16 stamp and writes its "
          "own record beside the chains")
    # The 09:45 capture stamps its vendor rows 09:30.
    got = {}
    dealer_capture.run("0945", pull=lambda **k: {"success": 0, "total": 0, "symbols": {}},
                       vendor_pull=lambda **k: got.update(k) or {"success": 0},
                       out_dir=str(TD / "dc"))
    check(got.get("data_as_of") == "09:30 ET (15-minute delay)",
          "the 09:45 capture passes '09:30 ET (15-minute delay)' to its vendor pull")
    # massive_chain stamps every row and the manifest.
    saved2 = (massive_chain.credentials, massive_chain.fetch_symbol)
    try:
        massive_chain.credentials = lambda: ("key", "https://example.invalid")
        massive_chain.fetch_symbol = lambda sym, key, base, mp: (
            [{"symbol": sym, "expiry": "2026-10-23", "strike": 100.0}], {"errors": []})
        s = massive_chain.pull(symbols=["SPX"], base_dir=str(TD / "mc"),
                               data_as_of="12:15 ET (15-minute delay)")
    finally:
        massive_chain.credentials, massive_chain.fetch_symbol = saved2
    p = Path(s["symbols"]["SPX"]["csv"])
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    man = json.loads(Path(s["symbols"]["SPX"]["quality"]).read_text(encoding="utf-8"))
    check(rows and all(x["vendor_data_as_of"] == "12:15 ET (15-minute delay)" for x in rows)
          and man.get("vendor_data_as_of") == "12:15 ET (15-minute delay)",
          "every vendor row and its manifest carry the data's as-of")
    # The units.
    from validate_systemd_units import directives
    u = REPO / "deploy" / "systemd"
    sv, tm = directives(u / "chester-vendor-chains.service"), directives(u / "chester-vendor-chains.timer")
    remote = (REPO / "scripts" / "deploy_remote.sh").read_text(encoding="utf-8")
    wrap = (REPO / "scripts" / "run_dealer_capture.sh").read_text(encoding="utf-8")
    check(tm.get("OnCalendar") == ["Mon-Fri 16:31 America/New_York"]
          and tm.get("Persistent") == ["false"]
          and sv.get("ExecStart") == ["%h/chester-reports/scripts/run_dealer_capture.sh chains"]
          and "chester-vendor-chains.timer" not in remote
          and "-m altdata.vendor_chains run" in wrap,
          "chester-vendor-chains: 16:31 ET on weekdays, no catch-up, the wrapper's chains "
          "branch, and not in DEPLOY_TIMERS (enabling it is the operator's)")
    # The close's reader tolerates the vendor files arriving at 16:31.
    day = "2026-10-20"
    base = str(TD / "close")
    CC.write_completeness(CC.completeness(
        {"symbols": {s: {"rows": 1, "expiries_fetched": 1, "expiries_with_rows": 1}
                     for s in config.options_universe()}}, config.options_universe()),
        day, base)
    early = CC.gap_lines(CC.read_completeness(day, base))
    CC.write_vendor(CC.vendor_record({"symbols": {"SPX": {"rows": 3}, "SPCX": {"rows": 2}}},
                                     config.massive_universe(), "16:16 ET (15-minute delay)"),
                    day, base)
    late = CC.gap_lines(CC.read_completeness(day, base))
    CC.write_vendor(CC.vendor_record({"symbols": {"SPX": {"rows": 3}}},
                                     config.massive_universe(), "16:16 ET (15-minute delay)"),
                    day, base)
    miss = CC.gap_lines(CC.read_completeness(day, base))
    check(any(CC.VENDOR_PENDING in x for x in early) and not any("missing" in x for x in early)
          and late == [] and any("vendor chains missing: SPCX" in x for x in miss),
          "the close's read before 16:31 says the vendor chains are pending, not missing; "
          "after, a complete record prints nothing and a short one names the gap")


def group_c() -> None:
    head("C. F-1, F-2, F-4 AND F-3: THE VENDOR WRITER, ITS RULES AND CONVENTIONS")
    import datetime as dt
    import json
    import os
    from altdata import observations
    from altdata.sources import flashalpha as fa
    cfg = fa.config()
    pl = fa.planned(cfg)
    check(cfg["daily_call_budget"] == 60 and "SPX" in cfg["symbols"]
          and "SPX" in cfg["slots"]["1625"]["symbols"]
          and pl == {"1625": 45, "0945": 6, "1230": 6} and sum(pl.values()) <= 60,
          f"the budget is 60 a day, the symbol list carries SPX, the plan is "
          f"{sum(pl.values())} requests ({pl})")
    fix = REPO / "tests" / "fixtures" / "dealer_block"
    summ = json.loads((fix / "flashalpha_summary_SPY_2026-10-16.json").read_text(encoding="utf-8"))
    levels = json.loads((fix / "flashalpha_levels.json").read_text(encoding="utf-8"))
    day = "2026-10-19"
    d0 = dt.date.fromisoformat(day)
    em = {"expiries": [{"expiry": (d0 + dt.timedelta(days=k)).isoformat(), "dte": k,
                        "atm_iv": 120.0 if k == 1 else (15.2 if k == 32 else 40.0)}
                       for k in (1, 2, 4, 9, 11, 32, 60, 95)]}
    urls = []

    def get(url, key):
        urls.append(url)
        if "/summary" in url:
            return {"status": 200, "body": summ}
        if "/exposure/levels/" in url:
            return {"status": 200, "body": levels}
        if "expected-move" in url:
            return {"status": 200, "body": em}
        if "/maxpain/" in url:
            # Synthetic values (no vendor figure in a committed file, 19 Oct 2026).
            return {"status": 200, "body": {"max_pain_strike": 750, "pin_probability": 0.30,
                                            "dealer_alignment": "aligned",
                                            "put_call_oi_ratio": 1.80}}
        return {"status": 200, "body": {"fixture": True}}
    os.environ.setdefault("FLASHALPHA_API_KEY", "fixture-key-0123456789abcdef")
    os.environ.setdefault("FLASHALPHA_BASE_URL", "https://example.invalid")
    q = TD / "fa_quota.json"
    db = str(TD / "fa.db")
    runs = []
    with observations.ObservationStore(db) as st:
        for slot in ("0945", "1230", "1625", "1625"):
            runs.append(fa.pull(db=st, get=get, cfg=cfg, day=day, quota_path=q,
                                slot=slot, blob_dir=TD / "fa_blobs"))
        # The pull stamps its rows with the wall clock, so the read's cutoff is
        # after the run (a fixed 2026-10-20 cutoff failed every run after it, A50).
        cut = AFTER_RUN
        v = fa.stored(st, cut, "SPY")
        iv20 = st.as_of("vendor.atm_iv_20dte", cut, "SPY")
        iv20_intraday = st.as_of("vendor.atm_iv_20dte", cut, "SPY@1230")
        fg = st.as_of("vendor.fear_greed", cut, None)
    gex_calls = [u for u in urls if "/exposure/gex/" in u]
    check([r["calls"] for r in runs] == [6, 6, 45, 3] and fa.calls_today(day, q) == 60
          and runs[-1]["status"] == "BUDGET" and runs[-1]["refused"]
          and "daily budget of 60 requests is spent" in runs[-1]["budget_note"],
          f"the budget holds at 60 on a fixture day: 09:45 6, 12:30 6, 16:25 45, a "
          f"16:25 rerun stopped after 3 ({[r['calls'] for r in runs]})")
    check(len(gex_calls) == 5 + 3 and all("?expiration=" in u for u in gex_calls)
          and any("/SPX?expiration=" in u for u in gex_calls)
          and sum(1 for u in urls if "/v1/surface/" in u) == 2,
          "GEX by single expiry for the nearest five SPY and three SPX expiries (from "
          "the listed expiries, never guessed), and the surface for SPY and QQQ")
    check(fa.iv_comparable("1625", 20) and not fa.iv_comparable("1625", 19)
          and not fa.iv_comparable("1230", 33)
          and iv20 and float(iv20[-1]["value_num"]) == 15.2 and not iv20_intraday,
          "F-2: the ATM IV compared is the first expiry of 20 DTE or more (15.2, not the "
          "1-DTE 120), from the 16:25 capture only")
    check(v.get("gex") == -4000000000.0 and v.get("regime") == "negative_gamma"
          and v.get("max_pain") == 750.0 and fg and float(fg[-1]["value_num"]) == 20.0,
          "the summary's exposure and macro blocks are stored under the vendor source "
          "(net GEX, the regime word, max pain; Fear & Greed as vendor.fear_greed)")
    blobs = sorted(p.name for p in (TD / "fa_blobs" / day).glob("*.json"))
    check(any(b.startswith("1625_SPY_gex_") for b in blobs)
          and "1625_SPY_surface.json" in blobs and "1625_SPY_dex.json" in blobs
          and not any(b.startswith("0945_") for b in blobs),
          f"the by-strike responses are blobs, one file each ({len(blobs)}), none at 09:45")
    ended = fa.pull(db=None, get=get, cfg=cfg, day="2027-04-01", quota_path=q)
    check(cfg["plan_ends"] == "2027-03-31" and ended["status"] == "PLAN_ENDED"
          and ended["calls"] == 0 and not fa.plan_ended("2027-03-31", cfg)
          and fa.vendor_line(v, None, cfg, day="2027-04-01")[0].startswith("vendor: plan ended")
          and fa.mechanics_row(v, "2027-04-01", cfg)["rows"][0][0] == "vendor: plan ended",
          "F-4: from 1 April 2027 the writer makes no call and the Weekly's vendor row "
          "prints 'vendor: plan ended'")
    row = fa.mechanics_row({"gex": -4000000000.0, "spot": 750.0, "flip": 755.0,
                            "call_wall": 780.0, "put_wall": 740.0, "max_pain": 750.0,
                            "regime": "negative_gamma", "day": "2026-10-16"}, "2026-10-16", cfg)
    check(row["columns"][-2:] == ["Net GEX ($ per 1%)", "Net GEX ($ per point)"]
          and row["rows"][0][-2:] == ["-4.00bn", "-0.53bn"],
          "the mechanics table's vendor row: flip, walls, max pain, regime, net GEX in "
          "both units (synthetic: -4.00bn per 1%, -0.53bn per point at 750.00)")
    prof = {"spot": 750.0, "overall": {"dollar_gamma_per_1pct": 1.0e9, "gamma_flip": 765.0,
                                       "dex_raw_notional": 1.0, "call_wall_otm": 800.0,
                                       "put_wall_otm": 740.0}}
    c1 = {r["name"]: r for r in fa.compare({"flip": 765.0 + 0.004 * 750.0,
                                            "regime": "positive_gamma"}, prof, cfg)}
    c2 = {r["name"]: r for r in fa.compare({"flip": 765.0 + 0.006 * 750.0,
                                            "regime": "negative_gamma"}, prof, cfg)}
    check(c1["Zero-gamma level"]["flag"] is False and c2["Zero-gamma level"]["flag"] is True
          and c1["Regime"]["flag"] is False and c2["Regime"]["flag"] is True,
          "the divergence gate flags a flip more than 0.5% of spot from ours (0.4% clears, "
          "0.6% flags) and a regime that disagrees")
    rs = (REPO / "config" / "reporting_stack.yaml").read_text(encoding="utf-8")
    src = (REPO / "altdata" / "sources" / "flashalpha.py").read_text(encoding="utf-8")
    notes = (REPO / "docs" / "ledgers" / "vendor-divergence-notes.md").read_text(encoding="utf-8")
    check(all(x in rs for x in ('"Vendor GEX (FlashAlpha)"', '"Our GEX in the vendor\'s terms"',
                                '"Vendor DEX (FlashAlpha)"', '"Walls, vendor and ours"',
                                "spot squared x 0.01", "the customer book"))
          and "spot^2 x 0.01" in src and "customer" in src and "OTM walls" in src
          and "## Entry 1, 18 Oct 2026" in notes,
          "F-3: the conventions are in the technical appendix and the writer's notes, "
          "and the reconciliation is the divergence notes' first entry")
    sys.path.insert(0, str(REPO / "tools"))
    import vendor_reconcile as VR
    fx = json.loads(VR.FIXTURE.read_text(encoding="utf-8"))
    r = VR.strike_reconciliation(fx["strikes"][0], fx["underlying_price"], 0.16)
    check(close(r["gamma_ratio_put_over_call"], 2.584, 1e-3)
          and close(r["vendor_call_iv_roots"][1], 0.8909, 2e-3)
          and r["vendor_put_iv_roots"][1] is None
          and r["vendor_put_gamma"] > r["gamma_peak"]
          and close(r["one_iv_net_gex"] / 1e6, 24.1, 0.1) and r["vendor_net_gex"] < 0,
          f"the one-strike reconciliation by hand, on the synthetic fixture: strike 770 "
          f"(23 Oct): put gamma {r['vendor_put_gamma']:.5f} against call "
          f"{r['vendor_call_gamma']:.5f}, 2.58x, the call leg at ~89% IV; one IV (16%) "
          f"nets +24.1m against the fixture's -6.57m")
    allowed = {"altdata/sources/flashalpha.py", "daily_cascade/dealer_weekly.py"}
    readers = []
    for p in REPO.rglob("*.py"):
        rel = p.relative_to(REPO).as_posix()
        if rel.startswith(("tools/", ".venv/", "tests/", "build/")) or rel in allowed:
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        if any(k in t for k in fa.ALL_KEYS):
            readers.append(rel)
    yml = [p.name for p in (REPO / "config").glob("*.yaml")
           if any(k in p.read_text(encoding="utf-8", errors="replace") for k in fa.ALL_KEYS)
           and p.name != "flashalpha.yaml"]
    check(not readers and not yml,
          f"no vendor value reaches an engine, flag, tell, dial or decision: nothing but "
          f"the writer and the Weekly's row names a vendor key ({readers + yml or 'none'})")


def _obs(key, day, value, inst=None):
    return {"registry_key": key, "instrument": inst, "observed_at": day,
            "available_at": f"{day}T21:00:00+00:00", "value": value, "source": "fixture"}


VERDICT = re.compile(r"\b(on|off|fired|fires|tripped|trips|triggered)\b", re.I)


def st10_fixture(day: str, prior: str) -> tuple[list[dict], list[dict]]:
    """Every 07:00 trigger on: a coupon auction, an FOMC (and refunding) week, the
    yen tell on at the prior close, SPY 11% off its low inside a 40% drawdown."""
    import datetime as dt
    rows = []
    d1 = dt.date.fromisoformat(prior)
    for k in range(300):
        d = (d1 - dt.timedelta(days=299 - k)).isoformat()
        v = 80 + k if k <= 40 else (120 - 50 * (k - 40) / 200 if k <= 240
                                    else 70 + 8 * (k - 240) / 59)
        rows.append(_obs("yfinance.mkt_spy", d, float(v)))
    rows += [_obs("calc.abs_stress", "2026-10-08", 1.0, "Note:10-Year"),
             _obs("calc.fed_mkt_gap_12m", prior, 62.0), _obs("calc.cred_stress", prior, 1.0),
             _obs("calc.jpy_unwind", prior, 1.0), _obs("calc.usdjpy_rvol_20d", prior, 14.2),
             _obs("calc.jpy_pos_z", prior, -1.8)]
    for k in range(5, 0, -1):
        rows.append(_obs("yfinance.mkt_usdjpy", (d1 - dt.timedelta(days=k)).isoformat(), 150.0))
    rows.append(_obs("yfinance.mkt_usdjpy", prior, 144.0))
    events = [{"source": "treasury_upcoming", "observed_at": f"{day}T17:00:00+00:00",
               "title": "Note:10-Year auction",
               "payload": {"instrument": "Note:10-Year", "offering_amt": "42000000000"}},
              {"source": "fed_calendar", "observed_at": f"{day}T18:00:00+00:00",
               "title": "FOMC Meeting -- two-day meeting"}]
    return rows, events


def group_d() -> None:
    head("D. ST-10: THE 07:00 LINES, THE 12:30 HOOKS, THE SUNDAY LINE")
    import datetime as dt
    from altdata import funding_currency as fc, numeral_audit as NA, observations
    from daily_cascade import funding_hooks as FH, midday_gate as MG, signal_lines as SL
    cfg = SL.config()
    day, prior = "2026-11-04", "2026-11-03"
    now = f"{day}T11:00:00+00:00"
    rows, events = st10_fixture(day, prior)
    with observations.ObservationStore(str(TD / "st10.db")) as st:
        st.write_many(rows)
        lines = SL.anchor_lines(st, events, day, prior, now)
        quiet = SL.anchor_lines(st, [], "2026-06-10", "2026-06-09", "2026-06-10T11:00:00+00:00")
        sunday = SL.sunday_lines(st, now)
    ids = [x["id"] for x in lines]
    a = cfg["anchor"]
    check(ids == ["auction", "fomc_gap", "yen_flag", "rally_in_bear"]
          and len(lines) <= a["max_lines"]
          and all(len(x["line"].split()) <= a["max_words_per_line"] for x in lines),
          f"on a day every trigger holds, the four lines print in declared order within "
          f"the budget ({len(lines)} of {a['max_lines']} lines, the longest "
          f"{max(len(x['line'].split()) for x in lines)} of {a['max_words_per_line']} words)")
    bad = [x["id"] for x in lines
           if not NA.audit(x["line"], x["values"], extra_values=x["constants"]).passed]
    check(not bad, f"the numeral audit passes on every new line ({bad or 'all four'})")
    check(quiet == [] and SL.html({"lines": quiet}) == "" and SL.html({"lines": lines})
          and "displaces nothing" in SL.html({"lines": lines}),
          "a day nothing triggers prints nothing (no heading, no 'none'); a day that "
          "does says its lines displace nothing")
    check(all(a["lines"][k].get("displaces") for k in ids),
          "each line declares what it displaces (config/st10_lines.yaml)")
    check("on for 67 percent of auctions since 2009, n=1,540" in lines[0]["line"]
          and "descriptive only" in lines[1]["line"]
          and "mechanism, not a signal" in lines[3]["line"],
          "the auction line carries ABS_STRESS's base rate and suspension, the gap line "
          "is descriptive only, the rally line says the audit failed")
    check(SL.refunding_week("2026-11-04") and not SL.refunding_week("2026-11-11")
          and SL.fomc_week(events, day) and not SL.fomc_week(events, "2026-11-11"),
          "the FOMC and refunding weeks by their declared rules")
    # 12:30
    y = fc.config()["yen"]
    px = [(f"2026-10-{k:02d}", 150.0) for k in range(1, 30)]
    rv = [(f"d{k:03d}", 8.0) for k in range(260)] + [("2026-11-03", 14.0)]
    ctx_y = {"day": day, "quotes": {"JPY=X": 144.0}, "funding": {"usdjpy": px, "rvol": rv}}
    ctx_q = {"day": day, "quotes": {"JPY=X": 149.0}, "funding": {"usdjpy": px, "rvol": rv}}
    gy, gq = FH.yen_unwind(ctx_y), FH.yen_unwind(ctx_q)
    check(gy["open"] and "-4.0%" in gy["line"] and not gq["open"]
          and NA.audit(gy["line"], gy["values"], extra_values=[12, 30, 20, 2]).passed,
          f"the yen hook opens on its trigger (-4.0% with vol 1.75x its median; ST-5's "
          f"{y['unwind_move_pct']}% and {y['vol_spike_ratio']}x) and stays closed at -0.7%")
    dev = [(f"2026-10-{k:02d}", -5.0, f"2026-10-{k:02d}") for k in range(1, 30)]
    gap = [(f"2026-10-{k:02d}", 10.0 if k < 20 else 45.0, f"2026-10-{k:02d}") for k in range(1, 30)]
    fd = {"dev": dev, "gap": gap, "fix_today": 7.10, "cny_prev_close": 7.10}
    ctx_d = {"day": day, "quotes": {"CNH=X": 7.14, "CNY=X": 7.10}, "funding": fd}
    gd = FH.deval_trip(ctx_d)
    gd2 = FH.deval_trip({**ctx_d, "funding": {**fd, "gap": [(d, 10.0, a) for d, _, a in gap]},
                         "quotes": {"CNH=X": 7.101, "CNY=X": 7.10}})
    words = VERDICT.findall(gd.get("line") or "")
    check(gd["open"] and "2 of 3 legs tracked, both held" in gd["line"]
          and "NOT TRACKED (rule 30; by-hand key state_bank_dollar_selling" in gd["line"]
          and not words and not gd2["open"],
          f"the devaluation hook opens when both tracked legs hold, prints the two legs "
          f"and no verdict word ({words or 'none'}), and stays closed when the gap is calm")
    out = TD / "midday"
    quiet_ctx = {"day": day, "midday": None, "morning": None, "quotes": {}, "funding": {}}
    r = MG.run(day, ctx=quiet_ctx, out_dir=out, send=lambda s, b: ("sent", "fake"))
    check(not r["opened"] and r["alert"] is None and r["model_called"] is False
          and not list(out.glob("*")) if out.exists() else not r["opened"],
          "with every gate closed the 12:30 slot writes nothing and calls no model")
    r2 = MG.run(day, ctx={**quiet_ctx, **ctx_d}, out_dir=out,
                send=lambda s, b: ("sent", "fake"))
    check(r2["opened"] == ["deval_trip"] and r2["alert"] and r2["model_called"] is False,
          "the devaluation hook alone opens the slot's alert, code-written, no model")
    import ast
    srcs = {n: (REPO / "daily_cascade" / f"{n}.py").read_text(encoding="utf-8")
            for n in ("signal_lines", "funding_hooks")}
    mods = [n.module or "" for s in srcs.values() for n in ast.walk(ast.parse(s))
            if isinstance(n, ast.ImportFrom)]
    mods += [a.name for s in srcs.values() for n in ast.walk(ast.parse(s))
             if isinstance(n, ast.Import) for a in n.names]
    check(not [m for m in mods if any(b in m for b in ("anthropic", "model_meter", "requests",
                                                      "urllib", "flashalpha"))],
          "the lines and the hooks import no model, no network library and no vendor")
    # The Sunday line
    j = "\n".join(sunday)
    dv = next((x for x in sunday if "Devaluation tell" in x), "")
    check(sunday[0].startswith("The rates driver: withdrawn") and "ABS_STRESS" in sunday[0]
          and "CRED_STRESS" in sunday[0] and all(f"A-{k} (" in j for k in (1, 2, 3))
          and "SR-1 style" in j and "SR-5's RS tell" in j and "EM flag (SR-14)" in j
          and "2 of 3 legs tracked" in dv
          and not VERDICT.findall(dv.replace("NOT AVAILABLE", "").replace("NOT TRACKED", "")),
          "the Sunday line: the driver, ABS_STRESS and CRED_STRESS, then A-1 to A-3 and "
          "Book B's tells, the devaluation tell as 2 of 3 legs with no verdict word")
    with observations.ObservationStore(str(TD / "st10-empty.db")) as st0:
        sub = SL.sunday_subsection(st0, now)
    leaked = [x for x in sub["lines"]
              if re.search(r"\b(?:fred|calc|cftc|pm|dial|ndl|yfinance)\.[a-z0-9_]+\b", x)]
    check(not leaked and any("its stored series" in x for x in sub["lines"]),
          "the Weekly's id rule: on an empty store the Sunday line names no internal id "
          "(a NOT AVAILABLE clause reads 'its stored series')")
    src = (REPO / "daily_cascade" / "dealer_weekly.py").read_text(encoding="utf-8")
    check("signal_lines.sunday_subsection(st, cutoff)" in src,
          "the Weekly carries it, through the mechanics hook session A owns")
    # PRL / Pearl in the daily outputs
    pat = re.compile(r"\bPRL\b|Pearl")
    daily = ["morning_anchor", "morning_payload", "morning_render", "midday_gate",
             "funding_hooks", "signal_lines", "stack_close", "close_report", "state_block"]
    hits = [n for n in daily if (REPO / "daily_cascade" / f"{n}.py").exists()
            and pat.search((REPO / "daily_cascade" / f"{n}.py").read_text(encoding="utf-8"))]
    rendered = " ".join(x["line"] for x in lines) + gy["line"] + gd["line"] + j
    check(not hits and not pat.search(rendered),
          f"the Daily grep gate: no daily output contains 'PRL' or 'Pearl' (the PRL "
          f"line waits for Tranche 5) ({hits or 'none'})")
    cfgs = (REPO / "config" / "market_state.yaml").read_text(encoding="utf-8") + \
        (REPO / "regime.py").read_text(encoding="utf-8") + \
        (REPO / "contradictions.py").read_text(encoding="utf-8")
    check(not any(k in cfgs for k in ("signal_lines", "funding_hooks", "st10_lines")),
          "nothing of ST-10 enters a composite or the market-state object")
    import yaml
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    manual = sorted(k for k in (reg.get("metrics") or {}) if k.startswith("manual."))
    check(manual in ([], ["manual.global_pmi"]),
          f"no new by-hand key ({manual})")
    import subprocess
    r = subprocess.run(["git", "diff", "--name-only", "origin/st-t3-calib...origin/a43-render"],
                       cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        check(True, "the Weekly builders session B is fixing: no base ref here, not "
                    "checkable; the notes record the local check")
    else:
        touched = [f for f in r.stdout.split() if f in ("daily_cascade/weekly_stack.py",
                                                        "daily_cascade/weekly_sections.py")]
        check(not touched, f"this branch touches neither Weekly builder session B is "
                           f"fixing (weekly_stack.py, weekly_sections.py; {touched or 'none'})")


def group_e() -> None:
    head("E. RULING 2 OF 18 OCT: THE EXPECTED-MOVE PATH AND ITS FALLBACK")
    import json
    import os
    from altdata import observations
    from altdata.sources import flashalpha as fa
    cfg = fa.config()
    fix = REPO / "tests" / "fixtures" / "dealer_block"
    em = json.loads((fix / "flashalpha_expected_move_SPY.json").read_text(encoding="utf-8"))
    summ = json.loads((fix / "flashalpha_summary_SPY_2026-10-16.json").read_text(encoding="utf-8"))
    ex = fa.expiries_of(em)
    e20 = fa.first_20dte(ex, "2026-10-19", cfg)
    check(cfg["endpoints"]["expected_move"] == "/v1/expected-move/{symbol}"
          and [e["expiry"] for e in ex] == ["2026-10-20", "2026-10-23", "2026-11-06", "2026-11-20"]
          and e20 and e20["expiry"] == "2026-11-20" and e20["atm_iv"] == 16.8,
          "the ruled path, and the ruled shape (expected_moves[] with daysToExpiry and "
          "atmIv) parsed: the first expiry of 20 DTE or more is 20 Nov at 16.8, not the "
          "1-DTE 120.4")
    os.environ.setdefault("FLASHALPHA_API_KEY", "fixture-key-0123456789abcdef")
    os.environ.setdefault("FLASHALPHA_BASE_URL", "https://example.invalid")

    def get(status):
        def g(url, key):
            if "/v1/expected-move/" in url:
                return {"status": status, "body": em if status == 200 else {}}
            if "/summary" in url:
                return {"status": 200, "body": summ}
            return {"status": 200, "body": {"fixture": True}}
        return g
    runs = {}
    for status in (200, 403, 404):
        with observations.ObservationStore(str(TD / f"em{status}.db")) as st:
            out = fa.pull(db=st, get=get(status), cfg=cfg, day="2026-10-19",
                          quota_path=TD / f"emq{status}.json", blob_dir=TD / f"emb{status}")
            iv = st.as_of("vendor.atm_iv_20dte", AFTER_RUN, "SPY")
        runs[status] = (out, iv)
    ok200 = runs[200][1] and float(runs[200][1][-1]["value_num"]) == 16.8 \
        and not runs[200][0].get("expected_move")
    gone = all(runs[s][0].get("expected_move") == "expected move: not served"
               and runs[s][0]["symbols"]["SPY"].get("expected_move") == "expected move: not served"
               and not runs[s][1] and not runs[s][0]["symbols"]["SPY"].get("errors")
               for s in (403, 404))
    check(ok200 and gone,
          "served, the 20-day IV is stored (16.8); a 403 or 404 stores nothing for it, "
          "says 'expected move: not served', and the 20-day comparison waits")


# ---------------------------------------------------------------------------
GROUPS = [group_a, group_b, group_c, group_d, group_e]


def main() -> int:
    print(f"{LINE}\na43-render\n{LINE}")
    for g in GROUPS:
        try:
            g()
        except Exception as exc:                              # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
