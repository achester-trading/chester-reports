"""
Validation gate for Batch 9 item 52, the volatility event flag and attribution
(docs/change-order-signal-triage-batch-9-2026-10-17.md; altdata/vol_event.py).

SYNTHETIC SERIES, built here: no gate reads the live store, fetches or calls a
model. The fixture day is shaped like 16 Oct 2026: VIX 19.98, up 3.53 points
(+21.5%) from 16.45; SPX down 1.09%; VVIX up 18.7%; SKEW up 5.1%; MOVE down
1.4%; VIX9D 20.12, VIX3M 20.50, VIX6M 21.67.

  A  THE TRIGGER, EACH ARM AT ITS THRESHOLD AND NOT BELOW, BOTH WAYS. One day:
     +15.0% and -15.0% fire, +14.9% does not; +3.0 and -3.0 points fire, 2.9 does
     not. Five days: past the 95th percentile of its own 20-year |log change|
     fires, inside it does not, either sign. A band crossing up and down fires;
     a move inside a band does not. Compression: three sessions within 5% of the
     six-month low fire, two do not. Level and change print as separate fields,
     each with its 5- and 20-year percentile.
  B  THE LENSES ON THE 16 OCT FIXTURE, BY HAND. Spot-vol: beta -0.80 VIX points
     per 1%, SPX -1.09% explains +0.872 of +3.53 (24.7%, "roughly a quarter"),
     the residual +2.658 the vol bid. Term structure: front-led, VIX3M/VIX
     1.026 from 1.143, contango. Tail: VVIX +17.1% and SKEW +5.0% in log terms
     against the VIX's +19.4%; VVIX/VIX 5.50. Cross-asset: MOVE -1.4% log, HY
     +5 bp: equity-specific. Realised against implied, positioning, breadth
     (awaiting item 18), the dealer lens from a fixture profile, the catalyst
     (an outlet's attribution, or "not established").
  C  THE BLOCK. Mechanics carries the sub-section first, its trigger line as an
     item and the paragraph's facts; nothing without the payload's flag; the
     anchor prints the stored event and is silent without one; the regime
     consequence names the band and Book C's rule, printed, not applied; the
     compression read and its stored flag.
  D  THE BASE RATE. Prior up moves of the same size from the same band, counted
     by hand, with n printed; "too few to read" under the floor.
  E  THE LEDGER. A resolved event's 5- and 20-session outcomes by hand; an
     unresolved one is None; rows observed on the session, available when
     written; no modifier right before 30 events.
  F  THE 12:30 GATE. Upward only: +15.5% opens it with the trigger line and the
     intraday lenses; +3.3% and a 20% fall keep it closed; no 12:30 quote keeps
     it closed. Registered beside the dealer gate; no model path.
  G  NOTHING FROM THE BRIEF'S "NEVER PRINTED" LIST: no support or resistance, no
     flag word, no dealer buy/sell direction, in any printed line.

    python tools/validate_vol_event.py
"""

from __future__ import annotations

import datetime as dt
import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tests" / "fixtures" / "dealer_block"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from altdata import vol_event as ve  # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
CFG = ve.config()
BANDS = ve.level_bands()
DAY = "2026-10-16"
PREV = "2026-10-15"


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


def weekdays(end: str, n: int) -> list[str]:
    d, out = dt.date.fromisoformat(end), []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= dt.timedelta(days=1)
    return out[::-1]


def wiggle(i: int) -> float:
    """A bounded, deterministic wiggle: 0.6 * sin, so a one-day change stays
    under 3 points and 15%."""
    return 0.6 * math.sin(i * 0.7)


def series_16oct() -> dict:
    """1,600 sessions to 16 Oct 2026. VIX near 16 with a wiggle, 15 Oct 16.45,
    16 Oct 19.98. SPX: each of the last 61 sessions' VIX change is exactly -0.8
    x the SPX % change (the beta by construction); 16 Oct SPX -1.09%."""
    days = weekdays(DAY, 1600)
    vix = [16.0 + wiggle(i) for i in range(len(days))]
    vix[-2], vix[-1] = 16.45, 19.98
    spx = [5000.0]
    for i in range(1, len(days)):
        if i == len(days) - 1:
            pct = -1.09
        elif i >= len(days) - 62:
            pct = -(vix[i] - vix[i - 1]) / 0.8
        else:
            pct = 0.05
        spx.append(spx[-1] * (1 + pct / 100.0))
    s = {"vix": list(zip(days, vix)), "spx": list(zip(days, spx))}
    for key, prior, now in (("vix9d", 15.90, 20.12), ("vix3m", 18.80, 20.50),
                            ("vix6m", 20.90, 21.67), ("vvix", 92.59, 109.90),
                            ("skew", 160.42, 168.60), ("move", 102.54, 101.10),
                            ("hy_oas", 2.90, 2.95)):
        s[key] = [(PREV, prior), (DAY, now)]
    s["cftc_net"] = [("2026-10-06", -45000.0), ("2026-10-13", -52000.0)]
    return s


def arm_series(last_two: tuple[float, float], n: int = 300) -> list:
    days = weekdays(DAY, n)
    vals = [20.0 + 0.3 * math.sin(i) for i in range(n)]
    vals[-2], vals[-1] = last_two
    return list(zip(days, vals))


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE TRIGGER: EACH ARM AT ITS THRESHOLD AND NOT BELOW, BOTH WAYS")
    t = lambda s: ve.trigger(s, DAY, CFG, BANDS)  # noqa: E731
    # From a VIX of 10, so the points arm (3.0) cannot fire: +-1.5 points.
    up15, dn15 = t(arm_series((10.0, 11.50))), t(arm_series((10.0, 8.50)))
    up149 = t(arm_series((10.0, 11.49)))
    check(up15["arms"]["one_day"]["fired"] and dn15["arms"]["one_day"]["fired"]
          and not up149["arms"]["one_day"]["fired"],
          "one day: +15.0% and -15.0% fire from 10.00 (1.50 points, under the points "
          "arm); +14.9% does not")
    p3u, p3d = t(arm_series((26.0, 29.0))), t(arm_series((29.0, 26.0)))
    p29 = t(arm_series((26.0, 28.9)))
    check(p3u["arms"]["one_day"]["fired"] and p3d["arms"]["one_day"]["fired"]
          and not p29["arms"]["one_day"]["fired"],
          "one day: +3.0 and -3.0 points fire (11.5%, under the percent arm); +2.9 "
          "points (11.2%) does not")
    small = t(arm_series((20.0, 22.8)))
    check(not small["arms"]["one_day"]["fired"]
          and round(small["change"]["pct"], 2) == 14.0,
          "+2.8 points, +14.0%: neither one-day arm")
    # Five days: a history whose 5-session |log change| is bounded by the wiggle.
    days = weekdays(DAY, 1300)
    base = [16.0 + wiggle(i) for i in range(len(days))]
    hist5 = [abs(math.log(base[i] / base[i - 5])) for i in range(5, len(base) - 1)]
    p95 = sorted(hist5)[math.ceil(0.95 * len(hist5)) - 1]
    for sign in (1, -1):
        hi = base[:-1] + [base[-6] * math.exp(sign * p95 * 1.05)]
        lo = base[:-1] + [base[-6] * math.exp(sign * p95 * 0.95)]
        fh, fl = t(list(zip(days, hi))), t(list(zip(days, lo)))
        check(fh["arms"]["five_day"]["fired"] and not fl["arms"]["five_day"]["fired"]
              and close(fh["arms"]["five_day"]["threshold"], p95),
              f"five days, {'up' if sign > 0 else 'down'}: past its own 95th "
              f"percentile ({p95 * 100:.1f}% log) fires, inside it does not")
    bu, bd, bn = t(arm_series((19.9, 20.1))), t(arm_series((20.1, 19.9))), \
        t(arm_series((19.0, 19.9)))
    check(bu["arms"]["band"]["fired"] and bu["band"] == "elevated"
          and bd["arms"]["band"]["fired"] and bd["band"] == "normal"
          and not bn["arms"]["band"]["fired"],
          "a band crossing fires up (normal to elevated) and down; a move inside the "
          "band does not")
    cd = weekdays(DAY, 200)
    # Settled onto the floor: 12.0 the six-month low, then a slow drift down to
    # it over the last 30 sessions, so no other arm fires.
    cv = [14.0 + 0.5 * math.sin(i / 9.0) for i in range(170)] +         [13.5 - 0.045 * k for k in range(30)]
    cv[100] = 12.0
    low = 12.0
    held3 = cv[:-3] + [low * 1.045, low * 1.04, low * 1.049]
    held2 = cv[:-3] + [low * 1.06, low * 1.04, low * 1.049]
    c3, c2 = t(list(zip(cd, held3))), t(list(zip(cd, held2)))
    check(c3["arms"]["compression"]["fired"] and c3["direction"] == "compression"
          and not c2["arms"]["compression"]["fired"],
          "compression: three sessions within 5% of the six-month low fire; two do not")
    ev = t(series_16oct()["vix"])
    lv, ch = ev["level"], ev["change"]
    check(close(lv["value"], 19.98) and close(ch["points"], 3.53)
          and round(ch["pct"], 1) == 21.5 and "pct_5y" in lv and "pct_20y" in lv
          and "pct_5y" in ch and "pct_20y" in ch and lv["n_5y"] == 1260,
          "level and change are separate fields, each with its 5- and 20-year "
          "percentile (the 5-year window holds 1,260 sessions)")
    line = ve.trigger_line(ev)
    check("VIX 19.98 (+3.53 points, +21.5%)" in line and "Level:" in line
          and "Change:" in line and "the one-day move" in line,
          f"the trigger line ({line[:90]}...)")


def profile():
    import exposure_compute as ec  # noqa: PLC0415
    import chains as C  # noqa: PLC0415
    return ec.compute_symbol(C.bs_chain(C.SETTLED), "SPY")


def group_b() -> None:
    head("B. THE LENSES ON THE 16 OCT FIXTURE, BY HAND")
    s = series_16oct()
    att = [{"outlet": "CNBC", "market": "US stocks", "claim": "regional bank credit "
            "worries", "source_url": "https://fixture.example/cnbc"}]
    ls = ve.lenses(s, DAY, CFG, profile(), att)
    sv = ls["spot_vol"]
    check(close(sv["beta"], -0.8, 1e-6) and close(sv["explained"], 0.872, 1e-6)
          and round(sv["share"] * 100, 1) == 24.7 and close(sv["residual"], 3.53 - 0.872, 1e-6),
          f"spot-vol: beta -0.80, SPX -1.09% explains +0.872 of +3.53 points "
          f"({sv['share'] * 100:.1f}%), residual +{sv['residual']:.3f}: the vol bid")
    ts = ls["term_structure"]
    check(ts["shape"] == "front-led" and round(ts["ratio_3m"], 3) == 1.026
          and round(ts["ratio_3m_prior"], 3) == 1.143 and ts["contango"] == "contango",
          f"term structure: front-led (VIX9D +4.22 against VIX6M +0.77), VIX3M/VIX "
          f"1.026 from 1.143, contango ({ts['line'][-60:]})")
    tl = ls["tail"]
    check(round(tl["vvix_log"], 1) == round(math.log(109.9 / 92.59) * 100, 1) == 17.1
          and round(tl["skew_log"], 1) == 5.0 and round(tl["vix_log"], 1) == 19.4
          and round(tl["vvix_over_vix"], 2) == 5.50 and "log" in tl["line"],
          "tail and vol-of-vol: VVIX +17.1% and SKEW +5.0% (log, the move screen's "
          "units) against the VIX's +19.4%; VVIX/VIX 5.50")
    cx = ls["cross_asset"]
    check(not cx["systemic"] and "MOVE 101.1 (−1.4% log)" in cx["line"]
          and "+5 bp" in cx["line"] and "equity-specific" in cx["line"]
          and "G10 FX vol: a listed gap" in cx["line"] and "DVOL awaiting" in cx["line"],
          "cross-asset: MOVE -1.4% log, HY +5 bp: equity-specific; DVOL awaiting, "
          "G10 FX vol a listed gap")
    dl = ls["dealer"]
    check(dl["state"] == "computed" and "zero-gamma level" in dl["line"]
          and "Inferred, not observed" in dl["line"] and "vanna" in dl["line"]
          and "0DTE settled, excluded" in dl["line"],
          f"dealer positioning from the engine's profile ({dl['line'][:70]}...)")
    rl = ls["realised"]
    check(rl["rv10"] is not None and rl["rv20"] is not None
          and close(rl["vrp"], 19.98 - rl["rv20"]) and "VRP" in rl["line"],
          f"realised against implied: 10- and 20-day realised SPX vol, the VRP "
          f"({rl['line'][:80]})")
    check(ls["breadth"]["state"] == "awaiting" and "item 18" in ls["breadth"]["line"],
          "breadth: awaiting item 18's dispersion panel, by key name")
    ps = ls["positioning"]
    check(ps["net"] == -52000 and "−7,000 on the week" in ps["line"]
          and "VIX ETP vega" in ps["line"],
          "positioning: the CFTC VIX net (weekly) with its change; ETP vega a gap")
    check(ls["catalyst"]["line"].startswith("CNBC attributed the move to:")
          and "not ours" in ls["catalyst"]["line"]
          and ve.lens_catalyst([], CFG)["line"] == "not established",
          "the catalyst is the outlet's attribution, or 'not established'")
    aw = ve.lenses({"vix": s["vix"], "spx": s["spx"]}, DAY, CFG)
    check(aw["term_structure"]["state"] == "awaiting" and "VIX9D" in aw["term_structure"]["line"]
          and aw["tail"]["state"] == "awaiting" and aw["dealer"]["state"] == "absent",
          "a lens with no stored input says so; none is guessed")


def group_c() -> None:
    head("C. THE BLOCK: MECHANICS, THE ANCHOR, THE CONSEQUENCE, COMPRESSION")
    from daily_cascade import morning_render as mr, stack as stack_mod  # noqa: PLC0415
    s = series_16oct()
    ev = ve.evaluate(s, DAY, CFG, profile(), [], BANDS)
    check(ev["fired"] and ev["table"]["rows"][0][0] == "Spot-vol"
          and len(ev["table"]["rows"]) == 9 and len(ev["table"]["columns"]) == 2,
          "a fired event: nine lenses, one line each, two columns")
    check("XIII band is normal" in ev["consequence"]
          and "condition holds (VIX 19.98, +21.5%)" in ev["consequence"]
          and "halved" in ev["consequence"]
          and "Printed, not applied." in ev["consequence"],
          "the consequence: the XIII band is normal; Book C's VIX condition (25, or "
          "+20% on the day) holds on +21.5%, so the volatile-day protocol's rule is "
          "printed -- not applied")
    calm = dict(ev["trigger"], level={"value": 19.0}, change={"pct": 12.0, "points": 2.0})
    check("does not hold" in ve.consequence(calm, CFG),
          "at 19.00 and +12% the condition does not hold, and the line says so")
    sec = stack_mod.mechanics_section({"session": DAY, "exposure": [], "pins": []},
                                      None, ev)
    check(sec["subsections"][0]["title"] == "Volatility event"
          and any(i["key"] == "mech:vol_event" for i in sec["items"])
          and sec["data"]["vol_event"]["trigger"] == ev["trigger_line"],
          "Mechanics: the sub-section first, its trigger line an item, the facts for "
          "the paragraph")
    quiet = ve.evaluate({"vix": s["vix"][:-1], "spx": s["spx"][:-1]}, PREV, CFG,
                        bands=BANDS)
    sq = stack_mod.mechanics_section({"session": PREV, "exposure": [], "pins": []},
                                     None, quiet)
    check(not quiet["fired"] and not sq["subsections"]
          and not any(i["key"] == "mech:vol_event" for i in sq["items"]),
          "a session with no event is silent")
    check(stack_mod.vol_event_for({"session": DAY}, None, "") is None,
          "without the payload's flag nothing is read (a gate's synthetic payload)")
    stored = ve._slim(ev)
    html = mr.vol_event_html({"vol_event": stored})
    check("Volatility event" in html and "VIX 19.98" in html and "Spot-vol" in html
          and mr.vol_event_html({"vol_event": ve._slim(quiet)}) == ""
          and mr.vol_event_html({}) == "",
          "the 07:00 anchor prints the stored event; silent without one")
    cd = weekdays(DAY, 200)
    cv = [14.0 + 0.5 * math.sin(i / 9.0) for i in range(170)] +         [13.5 - 0.045 * k for k in range(30)]
    cv[100] = 12.0
    cv = cv[:-3] + [12.0 * 1.045, 12.0 * 1.04, 12.0 * 1.049]
    comp = ve.evaluate({"vix": list(zip(cd, cv))}, DAY, CFG, bands=BANDS)
    rows = ve.event_rows(comp, "2026-10-16T21:00:00+00:00")
    flag = next(r for r in rows if r["registry_key"] == ve.COMPRESSION_KEY)
    check(comp.get("complacency", "").startswith("Complacency:") and flag["value"] == 1.0
          and "Concentration & Complacency" in comp["complacency"],
          "compression prints the complacency read and stores calc.vol_compression = 1 "
          "for the overlay's VIX input; no new overlay")
    big = dict(ev["trigger"], level={"value": 26.0}, change={"pct": 2.0, "points": 0.5})
    check("condition holds" in ve.consequence(big, CFG),
          "at VIX 26.00 the level arm alone holds the condition")


def group_d() -> None:
    head("D. THE BASE RATE, FROM THE HISTORY, WITH n")
    days = weekdays(DAY, 400)
    vals = [16.0 + 0.2 * math.sin(i) for i in range(400)]
    jumps = [30, 55, 80, 105, 130, 155, 180, 205, 230, 255, 280, 305]
    for j in jumps:
        vals[j] = vals[j - 1] * 1.20            # +20%, from the normal band
    vals[370] = vals[369] * 1.50                # +50%: another bucket
    vals[-2], vals[-1] = 16.45, 19.98
    spx = [(d, 5000.0 + i) for i, d in enumerate(days)]
    s = {"vix": list(zip(days, vals)), "spx": spx}
    tr = ve.trigger(s["vix"], DAY, CFG, BANDS)
    br = ve.base_rate(s["vix"], spx, tr, CFG, BANDS)
    same = [j for j in jumps if ve.band_of(vals[j], BANDS) == "normal"]
    check(br["n"] == len(same) and f"(n={br['n']})" in br["line"]
          and br["bucket"] == ("pct", 15.0, 25.0),
          f"prior +15-25% moves in the normal band, counted by hand: n={len(same)} "
          f"({br['line'][:90]}...)")
    f5 = br["forward"][5]
    check(close(f5["spx_median_pct"], (5005.0 / 5000.0 - 1) * 100, 1e-2)
          and f5["spx_up_share"] == 1.0,
          "the forward SPX path, five sessions on: +0.1% on the fixture, up in all")
    few = ve.base_rate(s["vix"][:200] + s["vix"][-2:], spx, tr, CFG, BANDS)
    check(few["n"] < 10 and "too few to read" in few["line"],
          f"under the floor of 10: n={few['n']}, too few to read")


def group_e() -> None:
    head("E. THE LEDGER: RESOLVED AND UNRESOLVED")
    days = weekdays("2026-12-31", 120)
    vix = [(d, 16.0 + i * 0.05) for i, d in enumerate(days)]
    spx = [(d, 5000.0 + i * 10) for i, d in enumerate(days)]
    early, late = days[40], days[-3]
    oc = ve.outcomes(early, vix, spx, CFG)
    check(oc["resolved"] and close(oc["spx_5d_pct"], round(50 / (5000 + 400) * 100, 3))
          and close(oc["vix_20d_points"], 1.0),
          f"a resolved event: SPX +{oc['spx_5d_pct']}% over 5 sessions and VIX "
          f"+1.00 over 20, by hand")
    ou = ve.outcomes(late, vix, spx, CFG)
    check(not ou["resolved"] and ou["spx_5d_pct"] is None and ou["vix_20d_points"] is None,
          "an unresolved event: its horizons are None until the sessions are stored")
    ev = ve.evaluate(series_16oct(), DAY, CFG, profile(), [], BANDS)
    rows = ve.event_rows(ev, "2026-10-16T21:00:00+00:00")
    keys = [r["registry_key"] for r in rows]
    led = next(r for r in rows if r["registry_key"] == ve.LEDGER_KEY)
    body = json.loads(led["value"])
    check(keys == [ve.EVENT_KEY, ve.COMPRESSION_KEY, ve.LEDGER_KEY]
          and all(r["observed_at"] == DAY and r["available_at"] == "2026-10-16T21:00:00+00:00"
                  for r in rows)
          and led["instrument"] == DAY and body["outcomes"] is None
          and len(body["attribution"]) == 9,
          "a fired event writes the event day, the compression flag and a ledger row: "
          "observed on the session, available when written, its attribution and no "
          "outcome yet")
    st = ve.ledger_status([{"outcomes": oc}, {"outcomes": ou}], CFG)
    check(st == "event ledger: 2 events, 1 resolved; no modifier right before 30 events",
          f"the ledger line ({st})")


def group_f() -> None:
    head("F. THE 12:30 GATE: UPWARD ONLY")
    from daily_cascade import midday_gate as mg  # noqa: PLC0415
    s = series_16oct()
    hist = {k: v[:-1] for k, v in s.items()}
    ctx = {"vol_cfg": CFG, "vol_series": hist, "day": DAY, "midday": profile()}
    opened = ve.vol_gate(dict(ctx, quotes={"^VIX": 19.0, "^VIX9D": 19.4, "^VIX3M": 19.9,
                                          "^VIX6M": 21.2, "^GSPC": 4960.0}))
    check(opened["open"] and "the 12:30 vol gate opens" in opened["line"]
          and "Spot-vol:" in opened["line"] and "Term structure:" in opened["line"]
          and "Dealer positioning:" in opened["line"],
          "VIX 19.00 against 16.45 (+15.5%) opens it, with the intraday lenses")
    for q, why in ((17.0, "+0.55 points"), (13.0, "a 21% fall")):
        r = ve.vol_gate(dict(ctx, quotes={"^VIX": q}))
        check(not r["open"], f"{why} keeps it closed (upward only)")
    check(not ve.vol_gate(dict(ctx, quotes={}))["open"], "no 12:30 quote: closed")
    check([g.__name__ for g in mg.GATES][:2] == ["dealer_flip_cross", "_vol_gate"],
          "registered beside the dealer gate (ST-10's funding hooks follow it)")
    res = mg.run(DAY, out_dir=Path(REPO / "build" / "vol_gate_test"),
                 ctx={"cfg": None, "midday": None, "morning": None},
                 extra={"vol_cfg": CFG, "vol_series": hist, "day": DAY,
                        "quotes": {"^VIX": 16.6}})
    check(not res["opened"] and res["alert"] is None and not res["model_called"]
          and not (REPO / "build" / "vol_gate_test").exists(),
          "closed, the slot writes nothing and calls nothing")
    src = (REPO / "altdata" / "vol_event.py").read_text(encoding="utf-8")
    check(not re.search(r"^\s*(?:from|import)\s.*(?:anthropic|model_meter|narrative)",
                        src, re.M),
          "the vol module imports no model path")


NEVER = [(re.compile(r"\b(support|resistance)\b", re.I), "support/resistance"),
         (re.compile(r"\b(pinned|pinning|held|amplif\w*|dampen\w*)\b", re.I), "a flag word"),
         (re.compile(r"dealer[_ ]?(buys|sells)|dealers? (?:will )?(?:buy|sell)\b", re.I),
          "a dealer buy/sell direction")]


def group_g() -> None:
    head("G. NOTHING FROM THE BRIEF'S 'NEVER PRINTED' LIST")
    ev = ve.evaluate(series_16oct(), DAY, CFG, profile(), [], BANDS)
    texts = [ev["trigger_line"], ev["consequence"], ev["base_rate"]["line"]] + \
        [c for r in ev["table"]["rows"] for c in r]
    for rx, what in NEVER:
        hits = [x for x in texts if rx.search(x)]
        check(not hits, f"no {what} ({hits[:1]})")


def main() -> int:
    print(f"{LINE}\nBATCH 9 ITEM 52: THE VOLATILITY EVENT FLAG AND ATTRIBUTION\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g):
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
