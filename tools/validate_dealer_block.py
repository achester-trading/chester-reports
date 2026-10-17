"""
Validation gate for the dealer block, part 1 (6b; brief v2
docs/briefs/dealer-positioning-brief-2026-10-09.md, ratified 16 Oct 2026).

SYNTHETIC CHAINS (tests/fixtures/dealer_block/chains.py), a temporary computed
directory and no store: no gate reads the live store, fetches or calls a model.

  A  THE MASSES AND THE GATE. On a hand chain (vendor gamma) the call-gamma and
     put-gamma masses, gross and net-to-gross equal the hand figures and the
     masses sum to gross; the regime word gates at 0.10 both ways -- positive
     and negative at or above it, "indeterminate (net is x% of gross)" below.
  B  THE WALLS. The OTM call wall and the OTM put gamma wall are the walls; the
     all-strike extremes are stored and printed as peaks, never walls; the
     secondary concentrations are the next OTM strikes; T2 names each
     definition once.
  C  THE HORIZONS. The cumulative windows and exclusive bands follow
     config/reporting_stack.yaml; the bands reconcile with "All"; the windows
     nest; at a settled capture the 0DTE window and band are "settled,
     excluded", and an intraday 0DTE column carries "OI as of prior close".
  D  T1 AND THE QUALITY PANEL. T1's rows and four horizon columns; the panel's
     rows, the IV roughness marked provisional until 60 captures.
  E  T4. 16:10 finds the prior 16:10 and 09:45 the prior 09:45; an 11:00
     capture and a 16:10 with only a 09:45 before it print "no equivalent
     capture"; the change column equals the hand difference.
  F  THE DECISION SUMMARY. c_pin_fade, c_negative_gamma_continuation and
     d_forced_flow each fire on their fixture with a level, an invalidation and
     a time stop; "no setup" otherwise; the settled capture's summary is for the
     next session.
  G  NEVER PRINTED. No printed string carries "support" or "resistance", a flag
     word, a dealer buy/sell direction, or a 0DTE figure without its OI vintage.
  H  THE CLOSE. Mechanics carries the five sub-sections, the summary item and
     the sign convention once; every dealer table is stamped "inferred, not
     observed" and is at most six columns; the close reads the captures from
     the payload's computed_dir, and reads nothing when there is none.
  I  THE SCORECARD ROW. wall_approached_call / _put read the morning's OTM
     walls; flip_in_range; regime_eligible at the gate; gamma_regime None when
     net GEX is None.
  J  NO REGISTER, NO ORDER, NO NETWORK. dealer_block imports none of them.

    python tools/validate_dealer_block.py
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tests" / "fixtures" / "dealer_block"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import chains as C  # noqa: E402
import exposure_compute as ec  # noqa: E402
from gate_tmp import mkdtemp  # noqa: E402

from daily_cascade import dealer_block as db  # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
CFG = db.config()
TD = Path(mkdtemp("validate_dealer_block_"))


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


def close(a, b, tol=1e-6) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol * max(1.0, abs(b))


def prof(rows, sym="SPY") -> dict:
    return ec.compute_symbol(rows, sym)


def strings(b: dict) -> list[str]:
    """Every string the block prints: table heads and cells, lines, notes."""
    out = list(b.get("notes") or [])
    for ss in b.get("subsections") or []:
        out.append(ss.get("title") or "")
        t = ss.get("table") or {}
        out += [str(c) for c in t.get("columns") or []]
        out += [str(x) for r in t.get("rows") or [] for x in r]
        out += list(ss.get("lines") or [])
    return out


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE MASSES, GROSS, NET-TO-GROSS AND THE GATE (hand chain)")
    o = prof(C.hand_chain(500))["overall"]
    # Call 105: 0.02 x 1,000 x 100 x 100 = 200,000 notional; x 0.01 x 100.
    check(close(o["call_gamma_per_1pct"], 200_000.0)
          and close(o["put_gamma_per_1pct"], 150_000.0),
          f"call mass $200,000 and put mass $150,000 per 1%, by hand "
          f"({o['call_gamma_per_1pct']:,.0f}, {o['put_gamma_per_1pct']:,.0f})")
    check(close(o["gross_gamma_per_1pct"], 350_000.0)
          and close(o["call_gamma_per_1pct"] + o["put_gamma_per_1pct"],
                    o["gross_gamma_per_1pct"])
          and close(o["gross_gex_abs"], 350_000.0),
          "gross is the two masses' sum: $350,000 per 1% (gross_gex_abs 350,000)")
    check(close(o["dollar_gamma_per_1pct"], 50_000.0)
          and close(o["net_to_gross"], 50_000 / 350_000),
          f"net $50,000 per 1%, net-to-gross 50/350 = {50 / 350:.4f}")
    check(db.regime(o["net_gex"], o["net_to_gross"], CFG) == "positive gamma",
          "net-to-gross 14% is a regime: positive gamma")
    o6 = prof(C.hand_chain(600))["overall"]
    check(close(o6["net_to_gross"], 20_000 / 380_000)
          and db.regime(o6["net_gex"], o6["net_to_gross"], CFG)
          == "indeterminate (net is 5% of gross)",
          "put OI 600: net 20/380 = 5% of gross, so 'indeterminate (net is 5% of gross)'")
    o10 = prof(C.hand_chain(1000))["overall"]
    check(db.regime(o10["net_gex"], o10["net_to_gross"], CFG) == "negative gamma"
          and close(o10["net_to_gross"], 0.2),
          "put OI 1,000: net -100/500 = 20%, negative gamma")
    check(CFG.get("net_to_gross_min") == 0.10
          and db.regime(1.0, 0.10, CFG) == "positive gamma"
          and db.regime(-1.0, 0.10, CFG) == "negative gamma"
          and db.regime(1.0, 0.0999, CFG).startswith("indeterminate")
          and db.regime(-1.0, 0.0999, CFG) == "indeterminate (net is 10% of gross)",
          "the gate at 0.10 both ways: at 0.10 a regime of either sign, at 0.0999 "
          "indeterminate (RULED 16 Oct)")
    check(db.regime(None, None, CFG) == "no net GEX",
          "no net GEX prints no regime word")


def group_b() -> None:
    head("B. THE WALLS ARE THE OTM ONES; THE EXTREMES ARE PEAKS")
    p = prof(C.walls_chain())
    o = p["overall"]
    check(o["call_wall_otm"] == 105 and o["put_wall_otm"] == 95,
          "the OTM call wall is 105 and the OTM put gamma wall 95")
    check(o["peak_call_gex_strike"] == 98 and o["peak_put_gex_strike"] == 102
          and o["call_wall"] == 98 and o["put_wall"] == 102,
          "the all-strike extremes are 98 (an ITM call) and 102 (an ITM put): "
          "peak_call_gex_strike / peak_put_gex_strike, the legacy names alike")
    check(o["call_concentration_otm_2"] == 110 and o["put_concentration_otm_2"] == 90,
          "the secondary concentrations: 110 above, 90 below")
    t = db.t2(p, CFG)
    by = {r[0]: r for r in t["rows"]}
    check(by["OTM call wall"][1] == "105.00" and by["OTM put gamma wall"][1] == "95.00"
          and by["Peak call-GEX strike (all strikes)"][1] == "98.00"
          and "a peak, not a wall" in by["Peak put-GEX strike (all strikes)"][-1],
          "T2 prints the OTM walls as the walls and the extremes as peaks")
    names = [r[0] for r in t["rows"]]
    check(len(names) == len(set(names)) and not any(n == "Call wall" or n == "Put wall"
                                                    for n in names)
          and {"Peak put-gamma strike", "Put OI shelf", "OTM put gamma wall"} <= set(names),
          "one name per definition: OTM call wall, OTM put gamma wall, peak put-gamma "
          "strike, put OI shelf; no bare 'call wall' or 'put wall'")
    # 105: call 200,000 notional; share of gross 200,000 / 1,350,000.
    check(by["OTM call wall"][4] == db.pct(200_000 / 1_350_000, 1),
          f"the wall's rank is its share of GROSS, by hand: 200,000 / 1,350,000 = "
          f"{by['OTM call wall'][4]}")


def group_c() -> None:
    head("C. THE HORIZONS: WINDOWS, BANDS, RECONCILIATION")
    hz_cfg = CFG["horizon_windows"]
    check([w["id"] for w in hz_cfg["windows"]] == ["0dte", "le7", "le45", "all"]
          and [b["id"] for b in hz_cfg["bands"]] == ["b0", "b1_7", "b8_45", "b46"]
          and ec.horizon_windows_config() == hz_cfg,
          "the engine reads config/reporting_stack.yaml's horizon_windows (four "
          "windows, four bands)")
    s = prof(C.bs_chain(C.SETTLED))
    i = prof(C.bs_chain(C.AM_0945))
    for name, p in (("settled", s), ("intraday", i)):
        r = db.reconciliation(p)
        check(r["ok"], f"{name}: the live bands sum to All within 0.01% "
                       f"({db.reconciliation_line(p)[:90]}...)")
        w = p["horizons"]
        g = [w[k]["gross_gamma_per_1pct"] for k in ("le7", "le45", "all")]
        check(g[0] < g[1] < g[2] and close(w["all"]["gross_gamma_per_1pct"],
                                           p["overall"]["gross_gamma_per_1pct"]),
              f"{name}: the windows nest (≤ 7 < ≤ 45 < All) and All is the profile's own")
    check(s["horizons"]["0dte"]["excluded"] and s["bands"]["b0"]["excluded"]
          and s["horizons"]["0dte"]["status"] == "settled, excluded"
          and s["horizons"]["0dte"]["oi_total"] > 0,
          "settled: the 0DTE window and band are excluded, OI reported, no greek")
    iw = i["horizons"]
    check(not iw["0dte"]["excluded"] and close(
        iw["le7"]["call_gamma_per_1pct"],
        i["bands"]["b0"]["call_gamma_per_1pct"] + i["bands"]["b1_7"]["call_gamma_per_1pct"]),
          "intraday: ≤ 7 days is the 0DTE band plus the 1–7 band, by hand")
    check(s["buckets"].get("monthly") and set(s["horizons"]["le45"]["listing_buckets"])
          == {"weekly", "monthly", "other"},
          "the listing buckets stay as stored; each window records the ones it draws on")
    t_s, t_i = db.t1(s, CFG), db.t1(i, CFG)
    check(all(r[1] == "settled, excluded" for r in t_s["rows"]),
          "T1 at a settled capture: every 0DTE cell 'settled, excluded'")
    check(t_i["columns"][1] == "0DTE (OI as of prior close)",
          "T1 at an intraday capture: the 0DTE column says 'OI as of prior close'")


def group_d() -> None:
    head("D. T1 AND THE QUALITY PANEL")
    p = prof(C.bs_chain(C.SETTLED))
    t = db.t1(p, CFG)
    labels = [r[0] for r in t["rows"]]
    check(labels[:3] == ["Call-gamma mass ($/1%)", "Put-gamma mass ($/1%)",
                         "Zero-gamma (balance) level"]
          and labels.index("Net GEX ($/1%), net-to-gross") > 2
          and labels.index("Regime (gated)") > labels.index("Net GEX ($/1%), net-to-gross"),
          "the convention-free quantities first (the masses, the balance level), net "
          "GEX and the gated regime after")
    check({"OTM call wall", "OTM put gamma wall", "Hedge-book size (DEX)",
           "Share of the hedge book", "OI balance (Σ Δ·OI, calls − puts)"} <= set(labels)
          and len(t["columns"]) == 5 and "inferred, not observed" in t["columns"][0],
          "T1's rows, four horizon columns, the stamp in the head")
    le7_share = t["rows"][labels.index("Share of the hedge book")][2]
    check(le7_share == db.pct(p["horizons"]["le7"]["share_of_abs_dex"]),
          f"the ≤ 7-day share of the hedge book prints from the stored share ({le7_share})")
    q = {r[0]: r[1] for r in db.quality_panel(p, CFG)["rows"]}
    check({"Capture", "Convention", "Greeks source", "Rows", "Settled 0DTE rows excluded",
           "Data quality", "IV roughness", "OI concentration", "MIN_T load-bearing",
           "OI vintage", "Bands"} == set(q),
          "the panel: capture, convention, greeks source, rows, settled 0DTE, data "
          "quality, IV roughness, OI concentration, MIN_T, OI vintage, the bands")
    check("16:10 ET, settled" in q["Capture"] and q["Convention"] == "dealers-hand-v1"
          and q["OI vintage"] == "prior close"
          and "provisional until 60 captures are stored" in q["IV roughness"]
          and "effective strikes" in q["OI concentration"]
          and q["Settled 0DTE rows excluded"] == "34",
          f"the panel's readings ({q['IV roughness']})")
    bad = prof([C.row("C", 105, 1000, iv=None), C.row("P", 95, 0)])
    qb = {r[0]: r[1] for r in db.quality_panel(bad, CFG)["rows"]}
    check("2 skipped (no OI 1, no IV 1)" in qb["Rows"],
          f"rows skipped and why ({qb['Rows']})")


def write_caps(day_caps: dict) -> Path:
    root = TD / f"computed_{len(list(TD.iterdir()))}"
    for day, caps in day_caps.items():
        d = root / day
        d.mkdir(parents=True, exist_ok=True)
        for n, c in enumerate(caps):
            (d / f"{c['symbol']}_{n:02d}_exposure.json").write_text(
                json.dumps(c, default=str), encoding="utf-8")
    return root


def group_e() -> None:
    head("E. T4: THE EQUIVALENT CAPTURE")
    cur = prof(C.bs_chain(C.SETTLED, spot=680.0))
    am = prof(C.bs_chain(C.AM_0945, spot=679.0))
    odd = prof(C.bs_chain(C.AM_1100, spot=679.0))
    p_set = prof(C.bs_chain(C.PRIOR_SETTLED, spot=675.0, call_oi=3800.0))
    p_am = prof(C.bs_chain(C.PRIOR_0945, spot=674.0))
    check(db.slot_of(cur, CFG) == "16:10" and db.slot_of(am, CFG) == "09:45"
          and db.slot_of(odd, CFG) is None,
          "slots: settled is 16:10, 09:45 ET is 09:45, 11:00 ET has none")
    eq, _ = db.find_equivalent(cur, [p_am, p_set], CFG)
    check(eq is p_set, "16:10 finds the prior 16:10, not the prior 09:45")
    eq2, _ = db.find_equivalent(am, [p_am, p_set], CFG)
    check(eq2 is p_am, "09:45 finds the prior 09:45")
    eq3, why3 = db.find_equivalent(odd, [p_am, p_set], CFG)
    eq4, why4 = db.find_equivalent(cur, [p_am], CFG)
    check(eq3 is None and "no equivalent capture" in why3
          and eq4 is None and why4 == "no equivalent capture (no prior 16:10 capture)",
          f"misses: 11:00 ('{why3}'); a 16:10 with only a 09:45 before it ('{why4}')")
    t = db.t4(cur, p_set, "", CFG)["table"]
    by = {r[0]: r for r in t["rows"]}
    a = cur["overall"]["dollar_gamma_per_1pct"]
    b = p_set["overall"]["dollar_gamma_per_1pct"]
    check(by["Net GEX ($/1%)"][3] == db.usd(a - b, True)
          and t["columns"][0].startswith("Since 2026-10-15 16:10")
          and [r[0] for r in t["rows"]] == [x[1] for x in db.FIELDS_T4],
          f"the change is the hand difference ({by['Net GEX ($/1%)'][3]}), against the "
          f"capture it names; the brief's nine rows")
    miss = db.t4(cur, None, why4, CFG)
    check(miss["table"] is None and miss["lines"] == ["No equivalent capture (no prior "
                                                      "16:10 capture)."],
          "no equivalent: one line, no table")
    root = write_caps({"2026-10-16": [cur, am], "2026-10-15": [p_set, p_am]})
    blks = db.for_session("2026-10-16", base_dir=str(root), cfg=CFG)
    check(len(blks) == 1 and blks[0]["data"]["equivalent"] == p_set["fetched_at"]
          and blks[0]["data"]["slot"] == "16:10",
          "from stored captures: the newest of the session (16:10) against the prior "
          "16:10")


def pdict(**kw) -> dict:
    base = {"symbol": "SPY", "spot": 100.0, "session_date": C.SESSION,
            "capture": "intraday", "fetched_at": C.AM_0945, "buckets": {},
            "quality": {}, "max_pain": None, "expiration_release": [],
            "overall": {}}
    base.update(kw)
    return base


def group_f() -> None:
    head("F. THE DECISION SUMMARY: EACH SETUP ON ITS FIXTURE, OR NONE")
    o_pos = {"net_gex": 1.0, "net_to_gross": 0.3, "gamma_flip": 98.0,
             "peak_abs_gex_strike": 100.0, "call_wall_otm": 102.0, "put_wall_otm": 97.0}
    pin = pdict(spot=100.3, overall=o_pos, buckets={"0dte": {"expiries": [C.SESSION]}},
                max_pain=100.0)
    s = db.summary(pin, None, CFG)
    ids = [x["id"] for x in s["setups"]]
    pf = next(x for x in s["setups"] if x["id"] == "c_pin_fade")
    check("c_pin_fade" in ids and pf["level"] == 100.0
          and "98.00" in pf["invalidation"] and pf["time_stop"] == "the expiry session's close",
          f"c_pin_fade: an expiry session, positive gamma, spot 0.30% from the peak: level "
          f"100, invalidation through the zero-gamma level, time stop ({pf['why']})")
    far = db.summary(pdict(spot=101.0, overall=o_pos,
                           buckets={"0dte": {"expiries": [C.SESSION]}}), None, CFG)
    check("c_pin_fade" not in [x["id"] for x in far["setups"]],
          "spot 1% from the peak: no pin fade")
    o_ind = dict(o_pos, net_to_gross=0.05)
    ind = db.summary(pdict(spot=100.3, overall=o_ind,
                           buckets={"0dte": {"expiries": [C.SESSION]}}), None, CFG)
    check("c_pin_fade" not in [x["id"] for x in ind["setups"]],
          "indeterminate (5% of gross): no pin fade -- the gate holds the setups too")
    o_neg = {"net_gex": -1.0, "net_to_gross": 0.2, "gamma_flip": 100.0,
             "put_wall_otm": 95.0, "call_wall_otm": 105.0, "peak_abs_gex_strike": 100.0}
    prior = pdict(spot=100.5, overall=o_neg)
    cont = db.summary(pdict(spot=99.8, overall=o_neg), prior, CFG)
    c = next((x for x in cont["setups"] if x["id"] == "c_negative_gamma_continuation"), None)
    check(c is not None and c["level"] == 100.0 and "back through 100.00" in c["invalidation"]
          and c["time_stop"] == "two sessions" and "down through the zero-gamma level" in c["why"],
          "c_negative_gamma_continuation: negative gamma, spot 100.50 to 99.80 through "
          "the zero-gamma level at 100 (0.2% beyond): level, invalidation, time stop")
    thin = db.summary(pdict(spot=99.95, overall=o_neg), prior, CFG)
    check(not thin["setups"], "only 0.05% through the level: not confirmed, no setup")
    rel = db.summary(pdict(overall=o_pos), None, CFG, releases=["CPI"])
    r = next((x for x in rel["setups"] if x["id"] == "d_forced_flow"), None)
    check(r is not None and "release day: CPI" in r["why"] and r["level"] == 97.0
          and r["time_stop"] == "the release session's close",
          "d_forced_flow on a release day: the OTM walls, invalidation, time stop")
    exp = next((x for x in s["setups"] if x["id"] == "d_forced_flow"), None)
    check(exp is not None and exp["time_stop"] == "the closing auction"
          and "max pain 100.00 the control" in exp["level_name"],
          "d_forced_flow on an expiry session: the peak-gamma strike, max pain the control")
    none = db.summary(pdict(overall=o_pos), None, CFG)
    check(not none["setups"] and any(ln.startswith("No setup") for ln in none["lines"])
          and "The block proposes; the books decide" in none["lines"][-1]
          and "inferred, not observed" in none["lines"][-1],
          "none holds: 'No setup', and the books decide")
    thu = prof(C.bs_chain(C.PRIOR_SETTLED, expiries=C.EXPIRIES_THU))
    fx = next((x for x in db.summary(thu, None, CFG)["setups"]
               if x["id"] == "d_forced_flow"), None)
    check(db.target_session(thu) == "2026-10-16" and db.expiry_on_target(thu, CFG)
          and fx is not None and "2026-10-16 is an expiry session" in fx["why"]
          and db.summary(thu, None, CFG)["lines"][0].startswith("For 2026-10-16."),
          "the settled Thursday capture's summary is for Friday 16 Oct, an expiry "
          "session: d_forced_flow for Friday")
    fri = prof(C.bs_chain(C.SETTLED))
    check(db.target_session(fri) == "2026-10-19"
          and not db.expiry_on_target(fri, CFG)
          and db.expiry_on_target(fri, dict(CFG, expiry_sessions="any"))
          and not any(x["id"] in ("c_pin_fade", "d_forced_flow")
                      for x in db.summary(fri, None, CFG)["setups"]),
          "the settled Friday capture is for Monday 19 Oct: its listed Monday expiry "
          "is no expiry session under 'friday' (session-set; it is under 'any'), and "
          "Friday's own settled expiry proposes nothing")
    t2 = {r[0]: r for r in db.t2(fri, CFG)["rows"]}
    t2t = {r[0]: r for r in db.t2(thu, CFG)["rows"]}
    check(t2["Max pain"][1] == "not an expiry"
          and "Max pain (2026-10-16 expiry)" in t2t,
          "T2's max pain: 'not an expiry' for Monday; printed for Friday's expiry")


NEVER = [(re.compile(r"\b(support|resistance)\b", re.I), "support/resistance as a fact"),
         (re.compile(r"\b(pinned|pinning|held|amplif\w*|dampen\w*)\b", re.I), "a flag word"),
         (re.compile(r"dealer[_ ]?(buys|sells)|dealers? (?:will )?(?:buy|sell)\b"
                     r"|unwind", re.I), "a dealer buy/sell direction"),
         (re.compile(r"market direction", re.I), "a market direction")]


def group_g() -> None:
    head("G. NOTHING FROM THE 'NEVER PRINTED' LIST")
    blocks = [db.block(prof(C.bs_chain(C.SETTLED)), None, "no equivalent capture", CFG),
              db.block(prof(C.bs_chain(C.AM_0945)), prof(C.bs_chain(C.PRIOR_0945)), "", CFG),
              db.block(prof(C.walls_chain()), None, "no equivalent capture", CFG,
                       releases=["CPI"])]
    texts = [s for b in blocks for s in strings(b)]
    for rx, what in NEVER:
        hits = [t for t in texts if rx.search(t)]
        check(not hits, f"no {what} ({hits[:1]})")
    hedge = [r for b in blocks for ss in b["subsections"] if ss.get("table")
             for r in ss["table"]["rows"] if str(r[0]).startswith(("Hedge-book", "OI balance"))]
    check(hedge and not any(re.search(r"buy|sell|long|short", str(x), re.I)
                            for r in hedge for x in r[1:]),
          "the hedge book and the OI balance print sizes, never a direction")
    zero = []
    for b in blocks:
        t = b["subsections"][0]["table"]
        for n, col in enumerate(t["columns"]):
            if col.startswith("0DTE") and any("$" in str(r[n]) for r in t["rows"]):
                zero.append(col)
    check(zero and all("OI as of prior close" in c for c in zero),
          f"every 0DTE gamma figure sits under 'OI as of prior close' ({zero})")


def group_h() -> None:
    head("H. THE CLOSE: MECHANICS, THE STAMP, THE CONVENTION ONCE")
    from daily_cascade import readability as rd, stack as stack_mod  # noqa: PLC0415
    from daily_cascade import stack_render  # noqa: PLC0415
    cur = prof(C.bs_chain(C.SETTLED))
    blk = db.block(cur, prof(C.bs_chain(C.PRIOR_SETTLED, spot=675.0)), "", CFG)
    p = {"session": C.SESSION, "exposure": [
        {"symbol": "SPY", "spot": 680.0, "net_gex": 1e9, "net_to_gross": 0.04,
         "gamma_flip": 670.0, "call_wall": 690.0, "put_wall": 660.0,
         "call_wall_otm": 685.0, "put_wall_otm": 675.0, "max_pain": 675.0}],
         "pins": [], "market_state": {}}
    sec = stack_mod.mechanics_section(p, [blk])
    titles = [s["title"] for s in sec["subsections"]]
    check(titles == ["Dealer dashboard, SPY", "Chain quality, SPY",
                     "Changes since the equivalent capture, SPY", "Key levels, SPY",
                     "Decision summary, SPY"],
          "Mechanics carries T1, the quality panel, T4, T2 and the decision summary")
    line = next(i for i in sec["items"] if i["key"] == "mech:SPY")["text"]
    check("indeterminate (net is 4% of gross)" in line and "OTM call wall 685.0" in line
          and "net GEX positive" not in line,
          f"the per-symbol line gates the regime and names the OTM walls ({line[:80]}...)")
    dl = next((i for i in sec["items"] if i["key"] == "mech:dealer:SPY"), None)
    check(dl is not None and dl["priority"] == 1, "the decision summary's lead is an item")
    tables = [ss["table"] for ss in sec["subsections"] if ss.get("table")]
    check(all("inferred, not observed" in t["columns"][0] for t in tables)
          and len(tables) == 4,
          "every dealer table's head carries 'inferred, not observed'")
    check(all(len(t["columns"]) <= rd.MAX_TABLE_COLUMNS for t in tables + [sec["table"]]),
          f"no table wider than {rd.MAX_TABLE_COLUMNS} columns (the mobile rule)")
    cad = stack_render._cadence("daily")
    html = "".join(stack_render.subsection_html(ss, "session", cad)
                   for ss in sec["subsections"])
    html += stack_render.footnote({**sec, "items": sec["items"]}, "daily")
    conv = (CFG.get("convention_line") or "").split(".")[0]
    chunks = re.findall(r"<table.*?</table>", html, re.S)
    figured = [c for c in chunks if "$" in c or "%" in c]
    check(html.count(conv) == 1 and len(chunks) == 5
          and all("inferred, not observed" in c for c in figured),
          f"rendered: five tables (four, and the summary's lines), every one holding a "
          f"figure stamped 'inferred, not observed' ({len(figured)}), the sign "
          f"convention once")
    sec0 = stack_mod.mechanics_section(p)
    check(not sec0.get("subsections") and not sec0.get("notes"),
          "without a block (a gate's synthetic payload) Mechanics adds nothing")
    root = write_caps({"2026-10-16": [cur]})
    got = stack_mod.dealer_blocks({"session": C.SESSION, "computed_dir": str(root)},
                                  _NoEvents(), "2026-10-16T21:00:00+00:00",
                                  stack_mod.config())
    check(got and got[0].get("subsections"), "the close reads the captures from computed_dir")
    check(stack_mod.dealer_blocks({"session": C.SESSION}, None, "", {}) is None,
          "no computed_dir: nothing is read")
    absent = stack_mod.mechanics_section(p, [{"absent": "dealer block, SPY: no computed "
                                                        "profile for 2026-10-16"}])
    check(any("no computed profile" in x for x in absent["not_tracked"]),
          "an absent block says why, in the section's not-tracked line")


class _NoEvents:
    """A store stand-in: the events calendar opens a database at `path`, so it
    points into the gate's temporary directory (empty: no release)."""
    path = str(TD / "events.db")


def group_i() -> None:
    head("I. THE SCORECARD ROW'S ELIGIBILITY FIELDS")
    from daily_cascade import stack_close  # noqa: PLC0415
    bars = [{"high": 100.0 + 0.009 * k, "low": 99.0 + 0.01 * k, "close": 99.5 + 0.01 * k}
            for k in range(100)]
    saved = stack_close.bars_mod.intraday
    stack_close.bars_mod.intraday = lambda *a, **k: {"bars": bars, "complete": True,
                                                     "n": len(bars)}
    try:
        p = {"session": C.SESSION, "exposure": [{"symbol": "SPY", "net_gex": None}],
             "pins": []}
        book = {"instruments": [{"id": "spy", "levels": [{"type": "prior_close",
                                                          "value": 100.0}], "frame": {}}]}
        morning = {"call_wall_otm": 101.0, "put_wall_otm": 95.0, "call_wall": 120.0,
                   "put_wall": 99.2, "gamma_flip": 99.5, "net_to_gross": 0.05}
        row = stack_close.scorecard_row(p, book, None, morning, None)
    finally:
        stack_close.bars_mod.intraday = saved
    check(row["gamma_regime"] is None, "net GEX None: gamma_regime None, never 'negative'")
    # high 100.891: within 0.25% of the OTM call wall 101 (0.108%).
    check(row["wall_approached_call"] is True and row["wall_approached_put"] is False
          and row["call_wall_otm_morning"] == 101.0,
          "wall_approached_call reads the morning OTM call wall (101, approached); the "
          "put side reads the OTM put gamma wall (95, not approached), not the "
          "all-strike 99.2")
    check(row["flip_in_range"] is True and row["regime_eligible"] is False
          and "is_expiry_session" in row,
          "flip_in_range (99.5 inside 99.0 to 100.9); regime_eligible False at 5% of "
          "gross; is_expiry_session carried")
    check("call_wall_approached" not in row and "put_wall_approached" not in row,
          "the old names are gone; the brief's names replace them")


def group_j() -> None:
    head("J. NO REGISTER, NO LEDGER, NO ORDER PATH, NO NETWORK")
    tree = ast.parse((REPO / "daily_cascade" / "dealer_block.py").read_text(encoding="utf-8"))
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            mods |= {f"{n.module}.{a.name}" if n.module else a.name for a in n.names}
    bad = [m for m in mods if re.search(
        r"register|ledger|decide|order|ibkr|requests|urllib|socket|http|anthropic|"
        r"model_meter|subprocess", m, re.I)]
    check(not bad, f"dealer_block imports none of them ({sorted(mods)})")
    src = (REPO / "daily_cascade" / "dealer_block.py").read_text(encoding="utf-8")
    check(".write(" not in src and "write_many" not in src and "write_text" not in src,
          "and writes nothing")


def main() -> int:
    print(f"{LINE}\nTHE DEALER BLOCK, PART 1 (6b; brief v2, ratified 16 Oct 2026)\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h,
              group_i, group_j):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback                                    # noqa: PLC0415
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
