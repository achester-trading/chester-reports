"""
Validation gate for SR-36: the Treasury basis-trade proxy (ST-B3-12) and its
calibration ledger (ST-B3-14) -- altdata/basis_proxy.py over the CFTC TFF rows
altdata/sources/cftc.py stores for TU, FV, TY, TN, US and WN.

A SYNTHETIC TFF HISTORY of its own (weekly, 2018 to 6 Oct 2026, built as the
CFTC API's records and stored through the one CFTC writer's category_rows),
with MOVE, SOFR and IORB beside it. No network, no box.

  A  THE WRITER. The six Treasury codes map to TU..WN in the TFF writer, and a
     record stores the leveraged-fund and asset-manager net with their OI share.
  B  THE SHARE ARITHMETIC. One week by hand: the leveraged net short and the
     asset-manager net long as a share of combined open interest, contract-
     weighted and DV01-weighted, and per contract.
  C  THE TIERS. The 10-year at 35% "elevated" and 40% "extreme", exactly at the
     line and just under it; the aggregate at its own 90th and 97th
     percentiles, computed from the history passed, never a fixed number.
  D  THE OI-CHANGE READ. Short down with OI down "deleveraging"; short down
     with OI flat "covering"; short up with OI up "building"; short up with OI
     flat "adding"; a flat short "unchanged".
  E  THE COINCIDENCE FLAG. A level flag plus two co-signals is ON; a level flag
     plus one is off; four co-signals with no level flag are off; a co-signal
     not stored is absent and named (SR-35 where the move screen is not built,
     the swap spread).
  F  THE TWO WEEKLY LINES. Positioning & flows and Plumbing & rates each print
     one code-written line, inside the paragraph's figure budget, ending
     "(descriptive; unvalidated, n=0)".
  G  THE BANNED READING. "Hedge funds are short bonds", a bet on yields and a
     squeeze withhold the paragraph; the fragility reading passes.
  H  THE LEDGER. The episode line says led, coincided or lagged from the first
     week of each; the ledger over the synthetic store gives four dated
     episodes, each with its rows and its one line.

    python tools/validate_basis_proxy.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import datetime as dt
import os
import sys
from pathlib import Path

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

_TMP = gate_mkdtemp(prefix="validate_basis_proxy_")
os.environ["ALTDATA_STORE"] = str(Path(_TMP) / "store")
os.environ["CHESTER_DB"] = str(Path(_TMP) / "chester.db")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from altdata import basis_proxy as bp, observations            # noqa: E402
from altdata.sources import cftc                               # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
LAST = "2026-10-06"                      # the last report Tuesday
CUTOFF = "2026-10-09T23:00:00+00:00"     # after that Friday's release
CODES = {"TU": "042601", "FV": "044601", "TY": "043602", "TN": "043607",
         "US": "020601", "WN": "020604"}
OI = {"TU": 4_000_000, "FV": 6_000_000, "TY": 5_000_000, "TN": 2_000_000,
      "US": 1_800_000, "WN": 1_900_000}


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def tuesdays(first: str, last: str) -> list[str]:
    d, e = dt.date.fromisoformat(first), dt.date.fromisoformat(last)
    out = []
    while d <= e:
        out.append(d.isoformat())
        d += dt.timedelta(days=7)
    return out


def weekdays(first: str, last: str) -> list[str]:
    d, e = dt.date.fromisoformat(first), dt.date.fromisoformat(last)
    out = []
    while d <= e:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def record(code: str, day: str, oi: int, lev_net: int, am_net: int) -> dict:
    """One TFF record as the API returns it (strings)."""
    lev_long = int(oi * 0.05)
    am_short = int(oi * 0.10)
    return {"cftc_contract_market_code": code,
            "report_date_as_yyyy_mm_dd": f"{day}T00:00:00.000",
            "open_interest_all": str(oi),
            "dealer_positions_long_all": "1000", "dealer_positions_short_all": "1000",
            "asset_mgr_positions_long": str(am_short + am_net),
            "asset_mgr_positions_short": str(am_short),
            "lev_money_positions_long": str(lev_long),
            "lev_money_positions_short": str(lev_long - lev_net),
            "other_rept_positions_long": "500", "other_rept_positions_short": "500"}


def ty_share(i: int, n: int) -> float:
    """The 10-year's net short share: 15% rising to 37% over the history."""
    return 15.0 + 22.0 * i / max(1, n - 1)


def seed(path: str) -> list[str]:
    weeks = tuesdays("2018-01-02", LAST)
    recs = []
    for i, d in enumerate(weeks):
        for c, code in CODES.items():
            sh = ty_share(i, len(weeks)) if c == "TY" else 10.0 + 8.0 * i / len(weeks)
            oi = OI[c]
            recs.append(record(code, d, oi, -int(oi * sh / 100.0), int(oi * 0.30)))
    rows = [dict(r, source=cftc.SOURCE) for r in
            cftc.category_rows(recs, "tff", cftc.TFF_CONTRACTS, cftc.TFF_CATEGORIES)]
    days =weekdays("2019-01-01", "2026-10-09")
    daily = []
    for i, d in enumerate(days):
        tail = len(days) - i
        move = 100.0 + (1.0 if i % 2 else -1.0) + (2.0 * (22 - tail) if tail <= 21 else 0.0)
        sofr = 4.38 + (0.01 if i % 2 else -0.01) + (0.02 * (11 - tail) if tail <= 10 else 0.0)
        for key, v in (("yfinance.mkt_move", move), ("fred.sofr", sofr),
                       ("fred.iorb", 4.40)):
            daily.append({"registry_key": key, "instrument": None, "observed_at": d,
                          "available_at": f"{d}T21:00:00+00:00", "value": round(v, 4),
                          "source": "fixture"})
    st = observations.ObservationStore(path)
    try:
        st.write_many(rows)
        st.write_many(daily)
    finally:
        st.close()
    return weeks


def group_a() -> None:
    print(f"\n{LINE}\nA. THE WRITER\n{LINE}")
    check(all(cftc.TFF_CONTRACTS.get(code) == c for c, code in CODES.items()),
          "the six Treasury codes map to TU, FV, TY, TN, US, WN in the TFF writer")
    rows = cftc.category_rows([record("043602", "2026-10-06", 5_742_990, -2_139_785,
                                      2_828_139)], "tff", cftc.TFF_CONTRACTS,
                              cftc.TFF_CATEGORIES)
    v = {r["registry_key"]: r["value"] for r in rows if r["instrument"] == "TY"}
    check(v.get("cftc.tff_lev_money_net") == -2_139_785
          and abs(v.get("cftc.tff_lev_money_net_oi") + 37.259) < 0.01
          and v.get("cftc.tff_open_interest") == 5_742_990,
          f"a TY record stores the leveraged net and its OI share "
          f"({v.get('cftc.tff_lev_money_net_oi')}%)")


def group_b() -> None:
    print(f"\n{LINE}\nB. THE SHARE ARITHMETIC, BOTH WEIGHTINGS\n{LINE}")
    per = {"TU": {"lev_net": -400, "am_net": 300, "oi": 2000},
           "TY": {"lev_net": -300, "am_net": 500, "oi": 1000}}
    dv = {"TU": 40.0, "TY": 60.0}
    w = bp.week_shares(per, dv)
    # Contract-weighted: 700 / 3000. DV01: (400*40 + 300*60) / (2000*40 + 1000*60)
    # = 34000 / 140000. Mirror: 800 / 3000 and (300*40 + 500*60) / 140000.
    check(abs(w["lev_short_oi"] - 100 * 700 / 3000) < 1e-9
          and abs(w["lev_short_oi_dv01"] - 100 * 34000 / 140000) < 1e-9,
          f"leveraged net short: {w['lev_short_oi']:.3f}% contract-weighted, "
          f"{w['lev_short_oi_dv01']:.3f}% DV01-weighted")
    check(abs(w["am_long_oi"] - 100 * 800 / 3000) < 1e-9
          and abs(w["am_long_oi_dv01"] - 100 * 42000 / 140000) < 1e-9,
          f"the asset-manager mirror: {w['am_long_oi']:.3f}% and "
          f"{w['am_long_oi_dv01']:.3f}%")
    check(w["per_contract"]["TU"]["lev_short_oi"] == 20.0
          and w["per_contract"]["TY"]["lev_short_oi"] == 30.0
          and w["per_contract"]["TY"]["am_long_oi"] == 50.0,
          "per contract, for tenor concentration: TU 20%, TY 30% short; TY 50% long")
    cfg = bp.load_config()
    check(set((cfg["dv01"]["per_contract"])) == set(CODES)
          and "session-set" in cfg["dv01"]["source"]
          and "CTD-duration approximation" in cfg["dv01"]["source"],
          "DV01 per contract is config, labelled a session-set CTD-duration "
          "approximation")


def group_c() -> None:
    print(f"\n{LINE}\nC. THE TIERS\n{LINE}")
    cfg = bp.load_config()
    check([bp.ten_year_tier(x, cfg) for x in (34.99, 35.0, 39.99, 40.0, 45.0)]
          == [None, "elevated", "elevated", "extreme", "extreme"],
          "the 10-year: under 35% none, 35% elevated, 40% extreme")
    hist = [float(i) for i in range(1, 101)]
    t89, th = bp.aggregate_tier(89.9, hist, cfg)
    t90, _ = bp.aggregate_tier(90.0, hist, cfg)
    t97, _ = bp.aggregate_tier(97.0, hist, cfg)
    check(th == {"p90": 90.0, "p97": 97.0} and (t89, t90, t97) == (None, "elevated",
                                                                     "extreme"),
          f"the aggregate: its own 90th and 97th percentiles ({th}) -- 89.9 none, "
          f"90 elevated, 97 extreme")
    _, th2 = bp.aggregate_tier(20.0, [x / 10 for x in hist], cfg)
    check(th2 == {"p90": 9.0, "p97": 9.7},
          "computed from the history passed, never a fixed number")


def group_d() -> None:
    print(f"\n{LINE}\nD. THE OI-CHANGE READ\n{LINE}")
    lab = bp.oi_change_label
    cases = {"deleveraging": lab(-50, 1000, -200, 10000),
             "covering": lab(-50, 1000, 20, 10000),
             "building": lab(50, 1000, 200, 10000),
             "adding": lab(50, 1000, -20, 10000),
             "unchanged": lab(5, 1000, -200, 10000)}
    check(all(k == v for k, v in cases.items()),
          f"short down + OI down, short down + OI flat, short up + OI up, short "
          f"up + OI flat, short flat: {list(cases.values())}")
    check(lab(-50, 1000, 300, 10000) == "covering",
          "short down with OI rising reads covering too")


def group_e(path: str) -> None:
    print(f"\n{LINE}\nE. THE COINCIDENCE FLAG\n{LINE}")
    st = observations.ObservationStore(path)
    try:
        r = bp.read(st, cutoff=CUTOFF)
        sig = bp.cosignals(st, LAST, CUTOFF, bp.load_config())
        check(r["day"] == LAST and r["ten_year_tier"] == "elevated"
              and r["level_flag"],
              f"the 10-year at {r['ten_year_short_oi']:.1f}% of OI: elevated, a level "
              f"flag")
        check(sig["move"]["state"] is True and sig["funding"]["state"] is True,
              f"MOVE's one-month change ({sig['move'].get('z')} sigma) and SOFR less "
              f"IORB's two-week widening ({sig['funding'].get('z')} sigma) at 2 sigma")
        check(sig["swap_spread"]["state"] is None and "not stored"
              in sig["swap_spread"]["why"] and sig["sr35"]["state"] is None,
              f"absent and named: the swap spread; SR-35 ({sig['sr35']['why'][:60]})")
        check(r["watch"]["on"] and r["watch"]["cosignals_on"] == ["move", "funding"],
              "a level flag plus two co-signals: the unwind watch is ON")
        cfg = bp.load_config()
        orig = bp.cosignals

        def fake(states):
            return lambda *a, **k: {k2: {"state": v, "why": ""} for k2, v in
                                    zip(("sr35", "move", "funding", "swap_spread"), states)}
        bp.cosignals = fake([True, False, None, None])
        one = bp.unwind_watch(st, LAST, CUTOFF, cfg, True)
        bp.cosignals = fake([True, True, True, True])
        none_level = bp.unwind_watch(st, LAST, CUTOFF, cfg, False)
        bp.cosignals = orig
        check(not one["on"] and not none_level["on"],
              "a level flag plus one co-signal is off; four co-signals with no level "
              "flag are off")
    finally:
        st.close()


def group_f(path: str) -> None:
    print(f"\n{LINE}\nF. THE TWO WEEKLY LINES\n{LINE}")
    from daily_cascade import cadence as cadence_mod
    from daily_cascade import readability as rd
    from daily_cascade import weekly_stack as ws
    cap = cadence_mod.figure_cap(cadence_mod.get("weekly"))
    st = observations.ObservationStore(path)
    try:
        then = "2026-10-02T23:00:00+00:00"
        pos = ws.positioning_week(st, CUTOFF, then)
        pl = ws.plumbing_week(st, CUTOFF, then)
    finally:
        st.close()
    pline = next((ln for ss in pos["subsections"] if ss.get("title", "").startswith(
        "Speculative positioning") for ln in ss.get("lines") or []), None)
    uline = next((ln for ss in pl["subsections"] if "basis proxy" in
                  str(ss.get("title")) for ln in ss.get("lines") or []), None)
    for name, ln in (("Positioning & flows", pline), ("Plumbing & rates", uline)):
        check(ln and ln.endswith(f"{bp.TAG}.") and rd.figure_count(ln) <= cap,
              f"{name}: one line, {rd.figure_count(ln or '')} figures inside the cap "
              f"of {cap}, tagged -- {str(ln)[:110]}")
    check(pline and "fragility" in pline and "elevated" in pline,
          "the positioning line reads the tier and names the fragility reading")
    check(uline and uline.startswith("Basis-unwind watch: ON") and "absent:" in uline,
          "the plumbing line prints the watch and names the absent co-signals")
    check(pos["data"].get("basis_proxy", {}).get("ten_year_tier") == "elevated"
          and pl["data"].get("basis_unwind_watch", {}).get("unwind_watch") == "on",
          "and each section's data carries what its line prints")


def group_g() -> None:
    print(f"\n{LINE}\nG. THE BANNED READING\n{LINE}")
    from daily_cascade import stack as stack_mod
    from daily_cascade import stack_prose as sp
    cfg = stack_mod.config()
    bad = ["Hedge funds are short bonds, and record short positioning keeps yields high.",
           "Leveraged funds are net short Treasuries into the auction.",
           "Speculators are betting on higher yields.",
           "A bond squeeze could follow if they cover."]
    for t in bad:
        f = sp.style_faults(t, cfg)
        check(any("directional reading" in x for x in f), f"withheld: {t}")
    ok = ("The leveraged position in Treasury futures sits at 37.3% of open interest, "
          "a size that sets how violent a vol or funding shock becomes.")
    check(not any("directional reading" in x for x in sp.style_faults(ok, cfg)),
          "the fragility reading passes")
    check("hedge funds are short bonds" in sp.SECTION_NOTES["positioning"]
          and "FRAGILITY" in sp.SECTION_NOTES["plumbing"],
          "the frame states the fence in Positioning and in Plumbing")


def group_h(path: str) -> None:
    print(f"\n{LINE}\nH. THE CALIBRATION LEDGER\n{LINE}")

    def row(day, on, stress, level=True):
        det = {k: {"state": None} for k in ("sr35", "move", "funding", "swap_spread")}
        if stress:
            det["move"] = {"state": True, "z": 2.5}
        return {"day": day, "level_flag": level,
                "watch": {"on": on, "detail": det, "absent": ["swap_spread"]}}
    led = bp.episode_verdict([row("2020-02-25", True, False), row("2020-03-03", True, True)])
    co = bp.episode_verdict([row("2020-02-25", False, False), row("2020-03-03", True, True)])
    lag = bp.episode_verdict([row("2020-02-25", False, True), row("2020-03-03", True, True)])
    check(" led " in led and "coincided with" in co and " lagged " in lag,
          f"led / coincided / lagged from the first week of each: {co}")
    check("absent: the swap spread" in led, "the absent co-signals are named in the line")
    st = observations.ObservationStore(path)
    try:
        cfg = bp.load_config()
        cfg = {**cfg, "history_start": "2018-01-02", "episodes": [
            {"id": "a", "title": "Episode A", "start": "2020-01-07", "end": "2020-05-26"},
            {"id": "b", "title": "Episode B", "start": "2025-02-25", "end": "2025-06-24"},
            {"id": "c", "title": "Episode C", "start": "2025-07-01", "end": "2025-11-25"},
            {"id": "d", "title": "Episode D", "start": "2026-01-06", "end": None}]}
        eps = bp.ledger(st, CUTOFF, cfg)
    finally:
        st.close()
    check(len(eps) == 4 and all(ep["rows"] and ep["line"] for ep in eps)
          and eps[3]["rows"][-1]["day"] == LAST,
          f"four dated episodes, session by session, each with its line "
          f"({[len(ep['rows']) for ep in eps]} weeks)")
    md = bp.ledger_markdown(eps, "2026-10-11", "Fixture.")
    check(md.count("| Report Tuesday |") == 4 and "Episode D:**" in md
          and "unvalidated, n=0" in md,
          "the markdown ledger: a dated table per episode, its line beside it")


def main() -> int:
    print(f"{LINE}\nSR-36 -- THE TREASURY BASIS-TRADE PROXY AND ITS LEDGER\n{LINE}")
    path = os.environ["CHESTER_DB"]
    seed(path)
    group_a()
    group_b()
    group_c()
    group_d()
    group_e(path)
    group_f(path)
    group_g()
    group_h(path)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
