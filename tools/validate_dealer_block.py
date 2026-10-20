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

  6b PART 2 (17 Oct 2026):
  K  THE CHARTS. D2, W12 and M12 render from the fixture profile under the cap
     and legible at 400 px; each figure reconciles with the tables (the OTM walls
     and zero-gamma level, the profile's at-spot point, the bands' masses, the
     roll-off as a size, the hedge book); stamped; unavailable with a reason;
     no direction or flag word in the figures' text; the plans hold the budgets
     (C2, W10 and M8 are what each sets aside).
  L  THE SENTENCES. The three sentences' facts are the tables' figures; the
     close's frame asks for them; the flag-word audit withholds a flag word
     without its True flag at the close, the Weekly and the Monthly, 'dampened'
     included.
  M  THE REGISTRATION. The ledger is unchanged (SHA-256) and the config mirrors
     it; Wilson by hand; the third Friday; eligibility None when ineligible;
     the floors (20 to print, 120 before a rate is a decision); none promoted.
  N  THE CAPTURES. A 09:45 capture writes the exposure JSON from its own
     snapshot, OI the prior close's, nothing on the release ladder; the 12:30
     gate opens on a crossing and stays closed otherwise, writing nothing and
     calling no model.

  PART 0 OF THE EL-4..6 PASTE (17 Oct 2026):
  O  THE 16 OCT WEEKLY'S TWO READINGS. 14 Oct's flip was crossed in the gap
     ("gapped through the flip", descriptive); flip_crossed reads the high and
     low; from 17 Oct the flags are the pre-registration's (ruling 7) and the
     Monthly counts from then; 16 Oct's IV gap is skew, both implied ranges
     leave the ratio tests unchanged, and a pre-close capture prints its time.
  P  EL-5, THE STATE VECTOR. Computed on fixture bars and a fixture capture, each
     leg by hand; None for a missing leg; no label (a fixture with one fails);
     one stored row per present field; the close's line and the Weekly's row;
     registered with units; no engine module imports it (a planted one fails).

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
          "is no expiry session under 'monthly' (ruled 17 Oct; it is under 'any'), "
          "and Friday's own settled expiry proposes nothing")
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
                     "Horizon matrix, SPY", "Decision summary, SPY"],
          "Mechanics carries T1, the quality panel, T4, T2, T3 (6b part 3, as lines) "
          "and the decision summary")
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
    check(html.count(conv) == 1 and len(chunks) == 6
          and all("inferred, not observed" in c for c in figured),
          f"rendered: six tables (four, T3's and the summary's lines), every one holding a "
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
    old = {k: v for k, v in cur.items() if k not in ("horizons", "bands")}
    ob = db.block(old, None, "no equivalent capture", CFG)
    check(ob["subsections"][0]["table"] is None
          and "before the horizon windows" in ob["subsections"][0]["lines"][0]
          and ob["subsections"][3]["table"],
          "a profile computed before 6b: T1 says it waits for the next capture; T2 "
          "and the rest still print")
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
          and row["is_expiry_session"] is True and row["carried_0dte"] is None,
          "flip_in_range (99.5 inside 99.0 to 100.9); regime_eligible False at 5% of "
          "gross; 16 Oct is the monthly third Friday, so an expiry session (ruled 17 "
          "Oct); carried_0dte None with no close profile")
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


# ===========================================================================
# 6b PART 2
# ===========================================================================
LEDGER = REPO / "docs" / "ledgers" / "dealer-scorecard-preregistration-2026-10.md"
# The registration's SHA-256 over LF, recorded when it was committed (17 Oct
# 2026). It is never edited: a change is a new registration in a new file.
LEDGER_SHA256 = "7f3e1f2493356011a72e33b6941e1a5952429d9db754c2de8a6ff1cda40b2717"
# H6, the level clusters (Batch 11 item 55, registered 19 Oct 2026, before its
# scoring code): its own file, never edited.
LEDGER_H6 = REPO / "docs" / "ledgers" / "dealer-scorecard-preregistration-2026-10-h6.md"
LEDGER_H6_SHA256 = "ec5691a650a6ebf4b33c337001efe2674b247562f93fe49feaf4c4a69e467216"


def group_k() -> None:
    head("K. THE CHARTS: D2, W12, M12 RENDER AND RECONCILE WITH THE TABLES")
    from daily_cascade import charts as ch, stack as stack_mod  # noqa: PLC0415
    from daily_cascade import weekly_stack as ws  # noqa: PLC0415
    from monthly_macro import charts as mch  # noqa: PLC0415
    p = prof(C.bs_chain(C.SETTLED))
    o = p["overall"]
    out = {cid: ch.dealer_chart(cid, p, f"t_{cid}", str(TD)) for cid in ("D2", "W12", "M12")}
    check(all(not c.get("unavailable") and 0 < c["png_bytes"] <= ch.MAX_PNG_BYTES
              and c["min_px_at_400"] >= ch.MIN_PX_AT_400 and c.get("svg_path")
              for c in out.values()),
          f"all three render under the 150 KB cap, legible at 400 px "
          f"({ {k: c.get('png_bytes') for k, c in out.items()} })")
    check(out["D2"]["figures"] == [2] and out["W12"]["figures"] == [2, 1, 3, 5]
          and out["M12"]["figures"] == [2, 1, 3, 4, 5],
          "D2 is figure 2; W12 figures 2, 1, 3 and 5; M12 figures 2, 1, 3, 4 and 5 "
          "(figure 5, 6b part 3)")
    d = out["M12"]["drawn"]
    f1, f2, f3, f4 = d["figure_1"], d["figure_2"], d["figure_3"], d["figure_4"]
    t1 = {r[0]: r for r in db.t1(p, CFG)["rows"]}
    check(f1["call_wall_otm"] == o["call_wall_otm"] and f1["put_wall_otm"] == o["put_wall_otm"]
          and t1["OTM call wall"][-1].startswith(db.price(f1["call_wall_otm"]))
          and f1["gamma_flip"] == o["gamma_flip"],
          "figure 1 draws T1's OTM walls and zero-gamma level, and no all-strike peak")
    check(close(f2["at_spot_m"], o["net_gex"] / 1e6) and f2["flip"] == o["gamma_flip"]
          and len(f2["spots"]) == len(p["gamma_profile"]["spots"]),
          "figure 2's at-spot point is the profile's net GEX; its curve the stored one")
    bands = p["bands"]
    check(f3["bands"] == list(bands) and all(
        close(v, (bands[b].get("call_gamma_per_1pct") or 0) / 1e9)
        for b, v in zip(f3["bands"], f3["call_bn"])),
          "figure 3's bars are the bands' call- and put-gamma masses")
    rel = p["expiration_release"][:10]
    check([round(x, 6) for x in f3["size_bn"]] ==
          [round(abs(e["dex_notional"]) / 1e9, 6) for e in rel]
          and all(x >= 0 for x in f3["size_bn"]),
          "figure 3's roll-off is the release ladder's size, never signed (F3)")
    check(close(f4["cumulative_bn"], sum(abs(e["dex_notional"]) for e in
                                         p["expiration_release"]) / 1e9)
          and close(f4["cumulative_bn"], abs(o["dex_notional"]) / 1e9, 1e-6),
          "figure 4 sums to the hedge book (T1's All column)")
    cap = out["W12"]["caption"]
    check("OI as of prior close" in cap and "inferred, not observed" in cap
          and "settled" in cap, f"stamped: capture, settled, OI vintage ({cap[:70]}...)")
    check(ch.dealer_chart("D2", None, "x", None).get("unavailable")
          and "predates" in ch.dealer_chart(
              "W12", {k: v for k, v in p.items() if k != "gamma_profile"}, "x",
              None)["unavailable"],
          "no profile, or one before the stored curve: unavailable with the reason")
    src = (REPO / "tools" / "dealer_charts.py").read_text(encoding="utf-8")
    body = src[src.index("def _stamp"):]
    check(not re.search(r"dealer_buys|dealer_sells|amplif|dampen|\bsupport\b|resistance",
                        body, re.I),
          "the figures' text carries no direction, no flag word, no support/resistance")
    sec = lambda **kw: dict({"id": "x", "depth_reason": None}, **kw)  # noqa: E731
    base = {"budget": {"charts": 3}, "sections": [
        sec(id="misfit", data={}), sec(id="plumbing", depth="light")]}
    check(stack_mod.chart_plan(base, {}) == ["C1", "C2"]
          and stack_mod.chart_plan(dict(base, dealer_computed_dir="d"), {})
          == ["C1", "D2", "C2"],
          "the close: D2 joins after C1 when the profiles are read; without them the "
          "plan is unchanged")
    c3 = {"budget": {"charts": 3}, "dealer_computed_dir": "d", "sections": [
        sec(id="misfit", data={"open_contradictions": [1]}), sec(id="plumbing")]}
    check(stack_mod.chart_plan(c3, {}) == ["C1", "C3", "D2"],
          "with C3 and no trigger, C2 is the one set aside")
    wed = {"budget": {"charts": 10}, "sections": [{"id": "misfit", "data": {}}]}
    plain = ws.chart_plan(wed)
    withd = ws.chart_plan(dict(wed, dealer_computed_dir="d"))
    check("W12" not in plain and withd[4] == "W12" and "W10" not in withd
          and len(withd) == 10 and ws.PLACE["W12"] == ("mechanics", None),
          "the Weekly: W12 in Mechanics after W7; at the cap it sets W10 aside")
    check(mch.plan({}) == list(mch.ORDER) and mch.plan({"dealer_computed_dir": "d"})
          == list(mch.ORDER) + ["M12"] and len(mch.ORDER) == 13,
          "the Monthly: M12 joins the thirteen (M13, ST-14, planned last) when the "
          "profiles are read")
    many = {k: {"id": k, "png": b"x"} for k in mch.ALL}
    check(mch.hold_cap(many, 12) == ["M13", "M8"],
          "fourteen rendered at the cap of 12: M13, the watch instrument's figure, then "
          "M8 are set aside (the chain-2 stitch: M13 first, ST-14's ruling)")


def group_l() -> None:
    head("L. THE THREE SENTENCES AND THE FLAG-WORD AUDITS")
    from daily_cascade import stack_prose as sp  # noqa: PLC0415
    from monthly_macro import dealer as mdealer  # noqa: PLC0415
    p = prof(C.bs_chain(C.SETTLED))
    b = db.block(p, None, "no equivalent capture", CFG)
    s1, s2, s3 = (b["sentences"][k] for k in ("sentence_1", "sentence_2", "sentence_3"))
    t1 = {r[0]: r for r in db.t1(p, CFG)["rows"]}
    o, spot = p["overall"], p["spot"]
    check(s1["regime"] == t1["Regime (gated)"][-1]
          and s1["zero_gamma_level"] == db.price(o["gamma_flip"])
          and s1["net_to_gross"] == db.pct(o["net_to_gross"])
          and s1["net_gex_if_spot_up_1pct"] == db.usd(o["net_gex_up_1pct"] * 0.01
                                                      * spot * 1.01, True),
          f"sentence 1's facts: the gated regime, net-to-gross, the zero-gamma level, "
          f"the +/-1% asymmetry ({s1['net_gex_if_spot_down_1pct']} / "
          f"{s1['net_gex_if_spot_up_1pct']})")
    check(s2["otm_call_wall"] == db.price(o["call_wall_otm"])
          and s2["hedge_rolling_off_at_next_expiry"] == db.usd(
              abs(p["expiration_release"][0]["dex_notional"]))
          and s2["next_expiry"] == p["expiration_release"][0]["expiry"],
          "sentence 2's facts: the OTM walls, the peak strike and its expiry, the "
          "size rolling off at the next expiry")
    check(s3["setups"] == "no setup" and s3["for_session"] == "2026-10-19",
          "sentence 3's facts: no setup for Monday 19 Oct")
    ss = {"id": "mechanics", "title": "Mechanics", "depth": "deep",
          "data": {"dealer_sentences": b["sentences"]}, "items": []}
    from daily_cascade import narrative as base_mod  # noqa: PLC0415
    prompt = sp.section_prompt(ss, "daily", base_mod)
    check("THE THREE DEALER SENTENCES" in prompt and "pinned, held, amplified or "
          "dampened" in prompt,
          "the close's Mechanics frame asks for the three sentences, in the "
          "existing narrative step")
    check(sp.dealer_flag_faults("SPY pinned near 680.", {"sections": [ss]})
          and sp.dealer_flag_faults("The book dampened the day's moves.",
                                    {"sections": [ss]})
          and not sp.dealer_flag_faults("Net GEX is positive at 17% of gross.",
                                        {"sections": [ss]}),
          "the close carries no scored session at prose time: any flag word is "
          "withheld, 'dampened' included; plain prose passes")
    week = [{"session": "2026-10-14", "flags": {"pinned": True, "dampened": True,
                                                "call_wall_held": False}},
            {"session": "2026-10-15", "flags": {"pinned": False, "dampened": None}}]
    ed = {"sections": [{"id": "mechanics", "data": {"dealer_week": week}}]}
    check(not sp.dealer_flag_faults("SPY pinned on Wednesday, near 680.", ed)
          and not sp.dealer_flag_faults("The range was dampened on 14 Oct.", ed)
          and sp.dealer_flag_faults("SPY pinned on Thursday.", ed)
          and sp.dealer_flag_faults("The call wall held on Wednesday.", ed)
          and sp.dealer_flag_faults("Dealers dampened the week.", ed)
          and not sp.dealer_flag_faults("The relationships that held on Monday held "
                                        "at the week's end.", ed),
          "the Weekly: a flag word only beside a named session whose flag is True "
          "(Wednesday's pinned and dampened pass; Thursday's pinned, Wednesday's "
          "wall held and an unnamed 'dampened' are withheld; 'held' about no dealer "
          "level is ordinary English and passes)")
    retro = {"sessions": [{"session": "2026-09-14", "flags": {"dampened": True}}],
             "counts": {"dampened": 1}}
    check(not mdealer.flag_word_faults("SPY dampened on 14 Sep.", retro)
          and mdealer.flag_word_faults("Dealers dampened the month.", retro)
          and mdealer.flag_word_faults("SPY dampened on 15 Sep.", retro),
          "the Monthly's audit reads 'dampened' too")


def scored_cards() -> tuple[list, dict]:
    """25 sessions, 2 Sep to 6 Oct 2026: regime sessions alternate positive and
    negative; the walls are approached on known days; 18 Sep is the monthly
    third Friday."""
    from altdata import session  # noqa: PLC0415
    import datetime as dt  # noqa: PLC0415
    days, d = [], dt.date(2026, 8, 1)
    while len(days) < 50:
        if session.is_trading_session(d):
            days.append(d.isoformat())
        d += dt.timedelta(days=1)
    closes = {x: 600.0 + (i % 5) - 2 + 0.3 * i for i, x in enumerate(days)}
    cards = []
    for i, x in enumerate(days[20:45]):
        c = closes[x]
        cards.append({"session": x, "close": c, "prior_close": c - 0.5,
                      "session_high": c + (1.0 if i % 2 else 4.0),
                      "session_low": c - (1.0 if i % 2 else 4.0), "atm_iv_30d": 15.0,
                      "net_to_gross_morning": 0.2 if i % 3 else 0.05,
                      "net_gex_morning": 1e9 if i % 2 else -1e9,
                      # Approached on every fourth session: the high (close + 4)
                      # 0.17% under a wall at close + 5.
                      "call_wall_otm_morning": c + 5.0 if i % 4 == 0 else c + 20,
                      "put_wall_otm_morning": c - 30,
                      "peak_gex_strike_morning": round(c), "max_pain": round(c),
                      "flip_in_range": i % 5 == 0})
    return cards, closes


def group_m() -> None:
    head("M. THE PRE-REGISTRATION, THE ELIGIBILITY FIELDS AND THE RATE PRINTER")
    import hashlib  # noqa: PLC0415
    from altdata import dealer_scorecard as dsc  # noqa: PLC0415
    from daily_cascade import weekly_sections as wsec  # noqa: PLC0415
    raw = LEDGER.read_bytes().replace(b"\r\n", b"\n")
    check(hashlib.sha256(raw).hexdigest() == LEDGER_SHA256,
          "the registration is unchanged since 17 Oct 2026 (its recorded SHA-256)")
    raw6 = LEDGER_H6.read_bytes().replace(b"\r\n", b"\n")
    t6 = raw6.decode("utf-8")
    check(hashlib.sha256(raw6).hexdigest() == LEDGER_H6_SHA256
          and "Never edited." in t6 and "three or more families" in t6
          and "**0.2%**" in t6 and "**30 calendar days**" in t6 and "**0.25%**" in t6
          and "Vendor levels never count" in t6 and "q = 0.10" in t6,
          "H6's registration is unchanged since 19 Oct 2026 (its recorded SHA-256): three "
          "families within 0.2%, frozen 30 days, the 0.25% approach, vendor levels never "
          "counted, Benjamini-Hochberg at 0.10")
    text = raw.decode("utf-8")
    sc = dsc.config()
    check(sc.get("registration") == "docs/ledgers/dealer-scorecard-preregistration-2026-10.md"
          and "17 Oct 2026" in text and "**0.10**" in text and "0.8 ×" in text
          and "1.2 ×" in text and "**0.25%**" in text and "**120**" in text
          and "q = 0.10" in text and "below **20**" in text
          and "monthly third-Friday expiry only" in text
          and sc["net_to_gross_min"] == 0.10 and sc["dampened_ratio"] == 0.8
          and sc["amplified_ratio"] == 1.2 and sc["wall_pct"] == 0.25
          and sc["pin_pct"] == 0.25 and sc["formation_sessions"] == 120
          and sc["print_floor_sessions"] == 20 and sc["bh_q"] == 0.10,
          "the config mirrors the registration: 0.10, 0.8x / 1.2x, 0.25%, the third "
          "Friday, 120 / 120, the floor of 20, Benjamini-Hochberg at 0.10")
    check(all(h in text for h in ("H1 — dampened", "H2 — amplified", "H3a — call wall held",
                                  "H3b — put wall held", "H4 — pinned", "H5 — flip crossing"))
          and all(w in text for w in ("**Mechanism:**", "**Eligibility:**", "**Outcome:**",
                                      "**Window:**", "**Base rate:**", "**Baseline")),
          "each hypothesis: mechanism, eligibility, outcome, window, base rate, baseline")
    lo, hi = dsc.wilson(7, 20)
    check(round(lo, 3) == 0.181 and round(hi, 3) == 0.567 and dsc.wilson(0, 0) is None,
          f"Wilson 95% for 7/20, by hand: 0.181 to 0.567 ({lo:.3f}, {hi:.3f})")
    check(dsc.is_monthly_expiry("2026-10-16") and not dsc.is_monthly_expiry("2026-10-09")
          and not dsc.is_monthly_expiry("2026-10-23"),
          "the monthly third Friday (16 Oct) is an expiry session; weekly Fridays are not")
    cards, closes = scored_cards()
    rows = dsc.score(cards, closes, sc)
    by = {r["session"]: r["h"] for r in rows}
    first = by[cards[0]["session"]]
    check(first["dampened"]["eligible"] is None and first["amplified"]["eligible"] is None,
          "a session under the net-to-gross gate is ineligible for H1 and H2: None")
    i1 = by[cards[1]["session"]]
    check(i1["dampened"]["eligible"] is True and i1["amplified"]["eligible"] is None
          and i1["dampened"]["outcome"] is True,
          "a positive regime session is H1-eligible (range 2.00 under 0.8 x the "
          "implied) and not H2-eligible")
    check(all(by[c["session"]]["call_wall_held"]["eligible"] is (True if i % 4 == 0 else None)
              for i, c in enumerate(cards)),
          "the call wall is eligible exactly on the approach days; otherwise None, "
          "never False")
    fri = [c["session"] for c in cards if dsc.is_monthly_expiry(c["session"])]
    check(fri == ["2026-09-18"] and by["2026-09-18"]["pinned"]["eligible"] is True
          and all(by[c["session"]]["pinned"]["eligible"] is None for c in cards
                  if c["session"] != "2026-09-18"),
          "pinned is eligible on the monthly third Friday only (18 Sep)")
    last = cards[20]["session"]
    check(by[last]["flip_crossing"]["eligible"] is True
          and by[last]["flip_crossing"]["outcome"] is not None
          and dsc._flip_outcome(max(closes), sorted(closes), closes) is None,
          "flip crossing resolves once three later closes are stored; the newest "
          "session is unresolved (None)")
    r = dsc.rate(rows, "dampened", sc)
    elig = [c for c in cards if c["net_to_gross_morning"] >= 0.10 and c["net_gex_morning"] > 0]
    check(r["n"] == len(elig) and r["n"] < 20 and not r["printable"]
          and "under the printing floor of 20" in dsc.rate_line(r),
          f"H1: {r['n']} scored sessions, under the floor of 20: no count prints")
    big = dsc.score(cards * 2, closes, sc)
    for i, row in enumerate(big):
        row["session"] = f"x{i:03d}"
    rb = dsc.rate(big, "call_wall_held", sc)
    line = dsc.rate_line(dict(rb, n=24, k=9, printable=True, interval=dsc.wilson(9, 24)))
    check("9/24" in line and "95% interval" in line and "base rate" in line
          and "baseline" in line and "episodes" in line and "no rate is a decision" in line,
          f"at 20+ scored and under 120 eligible: k/n, the interval, the base rate, "
          f"the baseline, sessions and episodes, 'no rate is a decision' ({line[:70]}...)")
    t = dsc.rates_table(rows, sc)
    check(t["registered"] == 6 and t["promoted"] == 0 and len(t["lines"]) == 6,
          "six registered tests, none promoted: nothing grants a reading in T3")
    fc = {"dealer_flags": {"pinned_pct": 0.25, "wall_pct": 0.25,
                           "amplified_range_ratio": 1.2, "dampened_range_ratio": 0.8}}
    card = {"close": 700.0, "prior_close": 700.0, "session_high": 701.0,
            "session_low": 699.0, "regime_eligible": True, "net_gex_morning": 1e9}
    check(wsec.flags_for(card, 20.0, fc)["dampened"] is True
          and wsec.flags_for(dict(card, regime_eligible=False), 20.0, fc)["dampened"] is None
          and wsec.flags_for(dict(card, net_gex_morning=-1e9), 20.0, fc)["dampened"] is None,
          "the Weekly's dampened flag: True on a positive regime session inside 0.8x; "
          "None when the session is not eligible")


class _FakePull:
    """options_chain.pull's shape: each symbol's snapshot written to `root`."""

    def __init__(self, root, fetched):
        self.root, self.fetched, self.calls = root, fetched, 0

    def __call__(self, symbols=None, **kw):
        import csv  # noqa: PLC0415
        from altdata.sources import options_chain as oc  # noqa: PLC0415
        self.calls += 1
        out = {"total": len(symbols), "success": 0, "failed": [], "symbols": {}}
        for s in symbols:
            rows = [{k: r.get(k) for k in oc.CHAIN_COLUMNS}
                    for r in C.bs_chain(self.fetched)]
            for r in rows:
                r["symbol"] = s
            path = Path(self.root) / f"{s}_fixture.csv"
            with path.open("w", newline="", encoding="utf-8") as fp:
                w = csv.DictWriter(fp, fieldnames=oc.CHAIN_COLUMNS)
                w.writeheader()
                w.writerows(rows)
            out["symbols"][s] = {"csv": str(path), "rows": len(rows)}
            out["success"] += 1
        return out


def group_n() -> None:
    head("N. THE CAPTURES AND THE 12:30 GATE")
    import os  # noqa: PLC0415
    from altdata import dealer_capture as dc  # noqa: PLC0415
    from daily_cascade import midday_gate as mg  # noqa: PLC0415
    chains_dir = TD / "chains"
    chains_dir.mkdir(exist_ok=True)
    comp = TD / "computed_cap"
    pull = _FakePull(chains_dir, C.AM_0945)
    vend = []
    res = dc.run("0945", symbols=["SPY"], pull=pull,
                 vendor_pull=lambda **k: vend.append(k) or {"success": 0},
                 out_dir=str(comp))
    path = res["computed"]["SPY"]
    rec = json.loads(Path(path).read_text(encoding="utf-8")) if path.endswith(".json") else {}
    check(res["captured"] == 1 and rec.get("capture") == "intraday"
          and rec.get("oi_vintage") == "prior_close" and rec.get("horizons")
          and rec.get("gamma_profile", {}).get("spots") and not vend,
          "a 09:45 capture writes the engine's exposure JSON from the snapshot it just "
          "wrote: intraday, OI the prior close's, the horizons and the profile; "
          "--symbols narrows the vendor pull away")
    ec_src = (REPO / "altdata" / "dealer_capture.py").read_text(encoding="utf-8")
    check("append_release" not in ec_src and "release_rows" not in ec_src,
          "the release ladder stays the 16:10 pass's: the capture appends nothing to it")
    cfg = CFG
    o_pos = {"net_gex": 1e9, "net_to_gross": 0.3}
    morning = {"symbol": "SPY", "spot": 682.0, "overall": dict(o_pos, gamma_flip=680.0)}
    mid = lambda s, ntg=0.3: {"symbol": "SPY", "spot": s,  # noqa: E731
                              "overall": {"net_gex": -1e9, "net_to_gross": ntg}}
    alerts = TD / "alerts"
    calls = []
    real = mg.dealer_block.regime

    def spy(*a, **k):
        calls.append(a)
        return real(*a, **k)
    sent = []
    fake = lambda subj, body: sent.append((subj, body)) or ("sent", "fake")  # noqa: E731
    opened = mg.run("2026-10-16", out_dir=alerts,
                    ctx={"cfg": cfg, "midday": mid(678.0), "morning": morning},
                    send=fake)
    again = mg.run("2026-10-16", out_dir=alerts,
                   ctx={"cfg": cfg, "midday": mid(678.0), "morning": morning},
                   send=fake)
    rec = json.loads(Path(opened["alert"]).read_text(encoding="utf-8"))
    check(len(sent) == 1 and sent[0][0] == "12:30 alert: " + rec["lines"][0]
          and opened["mail"]["state"] == "sent"
          and again["mail"]["state"] == "already_sent"
          and rec["mail"]["state"] == "already_sent" and Path(again["alert"]).exists()
          and "detail" not in rec["mail"],
          "ruling 2: the open alert is mailed once, subject '12:30 alert: <the trigger "
          "line>'; a second run that session sends nothing; the outbox copy is kept "
          "and carries the mail state, never the recipient")
    boom = mg.mail_alert("2026-10-15", ["x"], alerts,
                         send=lambda s, b: (_ for _ in ()).throw(OSError("down")))
    check(boom["state"] == "send_failed",
          "a send that raises is recorded as send_failed, never raised")
    check(opened["opened"] == ["dealer_flip_cross"] and opened["alert"]
          and Path(opened["alert"]).exists() and not opened["model_called"]
          and "down through the morning zero-gamma level 680.00" in
          json.loads(Path(opened["alert"]).read_text(encoding="utf-8"))["lines"][0],
          "spot 0.29% through the morning zero-gamma level at 12:30, both regimes "
          "gated: the gate opens and writes the alert, code-written; no model call")
    shut = mg.run("2026-10-16", out_dir=TD / "alerts2",
                  ctx={"cfg": cfg, "midday": mid(679.5), "morning": morning})
    ind = mg.run("2026-10-16", out_dir=TD / "alerts3",
                 ctx={"cfg": cfg, "midday": mid(678.0, ntg=0.05), "morning": morning})
    none = mg.run("2026-10-16", out_dir=TD / "alerts4",
                  ctx={"cfg": cfg, "midday": None, "morning": morning})
    check(not shut["opened"] and shut["alert"] is None
          and not (TD / "alerts2").exists() and not ind["opened"]
          and "indeterminate" in ind["gates"][0]["why"]
          and not none["opened"] and none["gates"][0]["why"] == "no 12:30 capture",
          "it stays closed 0.07% through, under the net-to-gross gate, and with no "
          "12:30 capture -- and then writes nothing")
    src = (REPO / "daily_cascade" / "midday_gate.py").read_text(encoding="utf-8")
    check(not re.search(r"^\s*(?:from|import)\s.*(?:anthropic|model_meter|narrative)"
                        r"|generate\(", src, re.M)
          and mg.GATES[0] is mg.dealer_flip_cross
          and [g.__name__ for g in mg.GATES] == ["dealer_flip_cross", "_vol_gate",
                                                 "_yen_unwind", "_deval_trip",
                                                 "_crypto_leverage"],
          "the 12:30 slot imports no model path; the dealer gate first, Batch 9 item "
          "52's VIX gate beside it")
    os.environ.pop("CHESTER_ALERT_DIR", None)

# ---------------------------------------------------------------------------
class _CardStore:
    """as_of over a few stored rows -- the scorecard cards and the VIX."""
    def __init__(self, rows):
        self.rows = rows

    def as_of(self, key, cutoff, instrument=None):
        return [r for r in self.rows if r["k"] == key
                and (instrument is None or r.get("i") == instrument)]


def group_o() -> None:
    head("O. THE 16 OCT WEEKLY'S TWO READINGS (Part 0, 17 Oct 2026)")
    from daily_cascade import weekly_sections as wsec  # noqa: PLC0415
    from monthly_macro import dealer as mdealer  # noqa: PLC0415
    from daily_cascade import stack as stack_mod  # noqa: PLC0415
    cfg = stack_mod.config()
    # 14 OCT, AS THE BARS HAD IT: prior close 778.04, morning flip 777.25, cash
    # high 776.35 -- the flip crossed in the gap, never in the session.
    wed = {"session": "2026-10-14", "prior_close": 778.04, "close": 769.61,
           "session_high": 776.35, "session_low": 766.71, "flip_morning": 777.25,
           "flip_crossed": False, "atm_iv_30d": 13.3}
    f = wsec.flags_for(wed, 16.87, cfg)
    check(f["actual_range"] == 9.64 and f["amplified"] is False
          and f["gapped_through_flip"] is True and f["definitions"] == "descriptive",
          f"14 Oct: range {f['actual_range']}, the flip in the overnight gap -- not "
          f"amplified under the descriptive rule (the session never crossed it), "
          f"flagged 'gapped through the flip'")
    cross = wsec.flags_for(dict(wed, session_high=778.5, flip_crossed=True), 16.87, cfg)
    check(cross["amplified"] is True and cross["gapped_through_flip"] is False,
          "the same day with the cash high through the flip: amplified, not gapped")
    import inspect  # noqa: PLC0415
    from daily_cascade import stack_close  # noqa: PLC0415
    src = inspect.getsource(stack_close.scorecard_row)
    check('"flip_crossed": (bool(lo <= flip <= hi)' in src,
          "flip_crossed tests the session's high and low against the flip, never "
          "the close")
    # FROM 17 OCT (ruling 7): the registered outcomes.
    mon = dict(wed, session="2026-10-19", net_to_gross_morning=0.25,
               net_gex_morning=-2e9)
    g = wsec.flags_for(mon, 16.87, cfg)
    check(g["definitions"] == "preregistration" and g["amplified"] is True,
          "a session from 17 Oct takes H2: a regime session in negative gamma with "
          "range >= 1.2x implied is amplified, flip or no flip")
    h = wsec.flags_for(dict(mon, net_gex_morning=2e9), 16.87, cfg)
    p = wsec.flags_for(dict(mon, max_pain=769.5), 16.87, cfg)
    check(h["amplified"] is None and p["pinned"] is None,
          "positive gamma: amplified is ineligible (None); pinned is None off the "
          "monthly expiry, max pain or not")
    # 16 OCT: the IV check. SPY's own chain 14.443 against the VIX 19.98 (Cboe's published close), on a
    # prior close of 771.71; the actual range 12.61.
    fri = {"session": "2026-10-16", "prior_close": 771.71, "close": 763.31,
           "session_high": 773.25, "session_low": 760.64, "atm_iv_30d": 14.443,
           "atm_iv_capture_at": "2026-10-16T20:10:31+00:00"}
    own = wsec.flags_for(fri, 19.98, cfg)
    vx = wsec.flags_for(dict(fri, atm_iv_30d=None), 19.98, cfg)
    check(own["implied_range"] == 7.02 and vx["implied_range"] == 9.71
          and own["iv_check"] and own["iv_captured"] is None,
          f"16 Oct: implied {own['implied_range']} from SPY's 14.4 and "
          f"{vx['implied_range']} from the VIX; the check marks the gap; a 16:10 "
          f"capture prints no time")
    check(own["actual_range"] / own["implied_range"] >= 1.2
          and vx["actual_range"] / vx["implied_range"] >= 1.2,
          "12.61 is past 1.2x either implied range (1.80x and 1.30x): no ratio test "
          "on 16 Oct turns on which figure is used")
    mid = wsec.flags_for(dict(fri, atm_iv_capture_at="2026-10-16T16:31:00Z"), 19.98, cfg)
    st = _CardStore([{"k": "dealer.scorecard_day", "i": "SPY",
                      "observed_at": "2026-10-16", "value_text": json.dumps(
                          dict(fri, atm_iv_capture_at="2026-10-16T16:31:00Z"))},
                     {"k": "yfinance.mkt_vix", "observed_at": "2026-10-16",
                      "value_num": 19.98}])
    wk = wsec.dealer_week(st, ["2026-10-16"], "2026-10-17T00:00:00Z", cfg)
    cell = wk["ranges_table"]["rows"][0][2]
    check(mid["iv_captured"] == "12:31 ET" and "captured 12:31 ET" in cell
          and "VIX 20.0: check" in cell,
          f"a chain captured before the close prints its time beside the IV ({cell})")
    # THE MONTHLY COUNTS FROM 17 OCT; earlier sessions are not restated.
    rows = [{"k": "dealer.scorecard_day", "i": "SPY", "observed_at": d,
             "value_text": json.dumps(dict(wed, session=d))}
            for d in ("2026-10-14", "2026-10-15", "2026-10-19", "2026-10-20")]
    r = mdealer.retrospective(_CardStore(rows), "2026-10-01", "2026-10-31",
                              "2026-11-01T00:00:00Z", cfg)
    sep = mdealer.retrospective(_CardStore([dict(x, observed_at="2026-09-1" + x[
        "observed_at"][-1]) for x in rows]), "2026-09-01", "2026-09-30",
        "2026-10-01T00:00:00Z", cfg)
    check(r["counts"]["sessions"] == 2 and r["counts"]["excluded_before_definitions"] == 2
          and any("not restated" in ln for ln in r["lines"])
          and sep["counts"]["sessions"] == 4,
          "October counts its two sessions from 17 Oct with the dated note; a month "
          "wholly before the date counts as it was published")


# ---------------------------------------------------------------------------
def _sv_bars(day: str, open_: float, step: float, n: int = 78, vol: float = 1000.0):
    """n synthetic 5-minute SPY bars from 09:30 ET (13:30Z in October)."""
    import datetime as _dt  # noqa: PLC0415
    t0 = _dt.datetime.fromisoformat(f"{day}T13:30:00+00:00")
    out, px = [], open_
    for i in range(n):
        o, c = px, px + step
        out.append({"observed_at": (t0 + _dt.timedelta(minutes=5 * i)).isoformat(),
                    "open": o, "high": max(o, c) + 0.1, "low": min(o, c) - 0.1,
                    "close": c, "volume": vol})
        px = c
    return out


class _SvBars:
    def __init__(self, by_day):
        self.by_day = by_day

    def read(self, instrument, interval, first="", last="9999", as_of=None):
        return [b for bs in self.by_day.values() for b in bs
                if first <= b["observed_at"] <= last]


class _SvStore:
    def __init__(self, vals, regime_obj=None):
        self.vals, self.obj = vals, regime_obj

    def latest_as_of(self, k, as_of=None):
        if k == "market_state":
            return {"value_text": json.dumps(self.obj)} if self.obj else None
        v = self.vals.get(k)
        return {"value_num": v} if v is not None else None

    def as_of(self, k, cutoff=None, instrument=None):
        v = self.vals.get(k)
        return [{"value_num": v, "observed_at": "2026-10-14"}] if v is not None else []


class _SvEvents:
    def calendar(self, first, last, as_of=None):
        return [{"type": "release", "observed_at": "2026-10-15T12:30:00+00:00"},
                {"type": "headline", "observed_at": "2026-10-14T21:00:00+00:00"}]

    def close(self):
        pass


def group_p() -> None:
    head("P. EL-5: THE STATE VECTOR (numbers only; no engine reads it)")
    from altdata import state_vector as sv  # noqa: PLC0415
    day = "2026-10-14"
    today = _sv_bars(day, 774.92, -0.08)
    prior = {d: _sv_bars(d, 777.0, 0.0134) for d in
             ("2026-10-13", "2026-10-12", "2026-10-09", "2026-10-08", "2026-10-07",
              "2026-10-06", "2026-10-05", "2026-10-02", "2026-10-01", "2026-09-30",
              "2026-09-29", "2026-09-28", "2026-09-25", "2026-09-24", "2026-09-23",
              "2026-09-22", "2026-09-21", "2026-09-18", "2026-09-17", "2026-09-16")}
    bst = _SvBars({day: today, **prior})
    st = _SvStore({"chain.spy_atm_iv_30d": 13.3, "calc.breadth_sector_above_50d": 45.0,
                   "yfinance.mkt_vix": 16.87, "yfinance.mkt_vix3m": 18.79,
                   "yfinance.mkt_vix9d": 14.59},
                  {"dimensions": {"trend": {"percentile": 72.0}}})
    cap = {"capture": "settled_eod", "fetched_at": "2026-10-14T20:10:00+00:00",
           "spot": 768.7, "overall": {"gamma_flip": 777.25, "net_gex": -2.1e9,
                                      "net_to_gross": 0.18}}
    g = sv.gather(st, bst, _SvEvents(), cap, day)
    v = g["vector"]
    pc = prior["2026-10-13"][-1]["close"]
    check(g["slot"] == "1610" and abs(v["gap_pct"] - round(100 * (774.92 - pc) / pc, 4)) < 1e-9
          and v["or_high"] == round(max(b["high"] for b in today[:6]), 2)
          and v["or_break"] == -1 and v["net_gex_sign"] == -1
          and v["flip_dist_pct"] == round(100 * (768.7 - 777.25) / 768.7, 4)
          and v["vix3m_over_vix"] == round(18.79 / 16.87, 4)
          and v["vix9d_over_vix"] == round(14.59 / 16.87, 4),
          f"the 16:10 vector on fixture bars: gap {v['gap_pct']}%, opening range "
          f"{v['or_low']}-{v['or_high']} broken below, flip {v['flip_dist_pct']}%, "
          f"the two VIX legs, each by hand")
    check(v["event_hours"] == 16.33 and v["volume_ratio_20d"] == 1.0
          and v["trend_alignment"] == -1 and v["breadth_50d"] == 45.0
          and v["rv_iv_ratio"] == round(v["rv_pct"] / 13.3, 4),
          f"the next release 16.33 h after the capture (a headline is not a release); "
          f"volume 1.00x the prior 20 sessions to the same clock; a down day against "
          f"an up trend aligns -1; RV/IV {v['rv_iv_ratio']}")
    mid = sv.gather(st, bst, None, dict(cap, capture="intraday",
                                        fetched_at="2026-10-14T13:50:00+00:00"), day)
    m = mid["vector"]
    check(mid["slot"] == "0950" and m["or_high"] is None and m["or_break"] is None
          and m["rv_pct"] is None and m["event_hours"] is None and m["gap_pct"] is not None,
          "an intraday capture before the opening range completes: the range, its "
          "break and realised vol are None, and no events store means no event hours")
    bare = sv.compute({"bars": [], "profile": {}})
    check(all(x is None for x in bare.values()) and not sv.check(bare),
          "nothing stored: every leg is None, never a guess")
    check(not sv.check(v) and sv.check(dict(v, regime="negative gamma"))
          and sv.check(dict(v, gap_pct="gap up")) and sv.check(dict(v, or_break=True)),
          "the vector holds numbers and None only: a label field, a string value or a "
          "boolean verdict fails")
    rows = sv.rows(g, "2026-10-14T20:45:00+00:00")
    check(all(r["instrument"] == "SPY:1610" and r["observed_at"] == day
              and r["registry_key"].startswith("state.") for r in rows)
          and len(rows) == sum(1 for x in v.values() if x is not None)
          and not sv.rows(dict(g, vector=bare), "x"),
          "stored one row per field present, instrument SPY:1610; a None field "
          "writes nothing")
    import yaml  # noqa: PLC0415
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    miss = [f for f, (u, _d) in sv.FIELDS.items()
            if (reg["metrics"].get(sv.key(f)) or {}).get("units") != u]
    cat = (REPO / "config" / "catalogue_commands.yaml").read_text(encoding="utf-8")
    check(not miss and "altdata.state_vector:" in cat,
          f"every field registered with its units, and the catalogue line ({miss[:3]})")
    from daily_cascade import stack as stack_mod  # noqa: PLC0415
    mech = stack_mod.mechanics_section({"exposure": [], "pins": []}, None, None, [g])
    ss = next((s for s in mech["subsections"] if s["title"] == "State vector, SPY"), None)
    check(ss and ss["lines"][0].startswith("16:10: gap ") and "trend alignment -1" in ss["lines"][0]
          and mech["data"].get("_state_vectors") == [g],
          f"the close prints one compact line per capture ({(ss or {}).get('lines', [''])[0][:70]})")
    wr = sv.weekly_row("Wed 14", {**v, "or_break": -1.0, "net_gex_sign": -1.0})
    check(len(wr) == 6 == len(sv.WEEKLY_COLUMNS) and wr[2].startswith("-1 /"),
          "the Weekly's row per session: six columns, a stored sign prints as an integer")
    # NO ENGINE READS IT (until EL-12).
    hits = sv_engine_imports([REPO / "alpha", REPO / "alpha_proposer"])
    fake = TD / "engine_fixture"
    fake.mkdir(exist_ok=True)
    (fake / "engine.py").write_text("from altdata import state_vector\n", encoding="utf-8")
    (fake / "engine2.py").write_text("import altdata.state_vector as s\n", encoding="utf-8")
    (fake / "ok.py").write_text("from altdata import observations\n", encoding="utf-8")
    planted = sv_engine_imports([fake])
    check(not hits and sorted(p.name for p in planted) == ["engine.py", "engine2.py"],
          f"no module in alpha/ or alpha_proposer/ imports the state vector; a planted "
          f"engine import is caught ({[p.name for p in planted]})")


def sv_engine_imports(roots) -> list:
    """Every .py under `roots` that imports altdata.state_vector (by AST)."""
    out = []
    for root in roots:
        for p in sorted(Path(root).rglob("*.py")):
            try:
                tree = ast.parse(p.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue
            for n in ast.walk(tree):
                if isinstance(n, ast.Import) and any(
                        a.name == "altdata.state_vector" for a in n.names):
                    out.append(p)
                    break
                if isinstance(n, ast.ImportFrom) and (
                        n.module == "altdata.state_vector"
                        or (n.module == "altdata" and any(a.name == "state_vector"
                                                          for a in n.names))):
                    out.append(p)
                    break
    return out


def main() -> int:
    print(f"{LINE}\nTHE DEALER BLOCK, PARTS 1 AND 2 (6b; brief v2, ratified 16 Oct "
          f"2026)\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h,
              group_i, group_j, group_k, group_l, group_m, group_n, group_o,
              group_p):
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
