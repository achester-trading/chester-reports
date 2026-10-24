"""
Signal-triage Batch 6, the rates-transmission cluster -- the reads.

    python -m altdata.st_r5_rates show [--as-of ISO] [--json]

Change order docs/change-order-signal-triage-batch-6-2026-10-15.md, items 34,
36, 37 and 41, section 4's cross-item ruling 1: one mechanism, the long end
doing the tightening, measured through policy pricing (34), housing (36, 37)
and the credit tail (41), printed together under one "Rates transmission"
header in Plumbing & rates. Tranche 1 only:

    tightening(st, cutoff)      ST-R5.34a  the "market does the tightening" flag:
                                the 10-year up while 12-month fed funds pricing
                                is down over four weeks, NFCI confirming
    panel(st, cutoff)           ST-R5.34b  the G8 2-year panel; a country without
                                a free source is a listed gap, never a guess
    housing(st, cutoff)         ST-R5.36a  the monthly housing block (Redfin, the
                                30-year mortgage rate, metro breadth, NAR by hand)
    mba(st, cutoff)             ST-R5.37a  the MBA purchase index, the weekly line
    quality_tail(st, cutoff)    ST-R5.41a  CCC less BB and CCC less AAA, euro HY,
                                the CCC-faster-than-BB co-signal

WHERE THE FLAG LIVES. The order puts item 34's flag "in rates.driver". That
sub-state was withdrawn from the market-state object on 30 Sep after failing its
calibration gate twice, and tools/validate_regime.py group L holds it withdrawn.
So the flag is computed here, report-only, beside altdata/rates_attribution.py,
as SR-49's shape axis was (docs/briefs/sr-43-49-notes.md); regime.py imports
nothing from this module. Whether it should become a declared sub-state at
v1.13 is the operator's (docs/briefs/st-r5-rates-notes.md, needs-you).

Every read is as of the cutoff, through the observation store's as-of join.
Percentiles go through derived.percentile_of and print the window they really
cover and its n: FRED serves the ICE BofA spreads from October 2023 only
(filing note 3), so a "five-year" percentile on them is a three-year one, and
says so.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Optional

import yaml

from . import derived

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "st_r5_rates.yaml"


def config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _pts(st, key: str, cutoff: str, instrument: Optional[str] = None
         ) -> list[tuple[str, float]]:
    rows = [(str(r["observed_at"])[:10], float(r["value_num"]))
            for r in st.as_of(key, cutoff, instrument)
            if r.get("value_num") is not None]
    return sorted(rows)


def _on_or_before(pts: list[tuple[str, float]], day: str
                  ) -> Optional[tuple[str, float]]:
    best = None
    for d, v in pts:
        if d <= day:
            best = (d, v)
        else:
            break
    return best


def _back(day: str, days: int) -> str:
    return (dt.date.fromisoformat(day) - dt.timedelta(days=days)).isoformat()


def _years_back(day: str, years: int) -> str:
    d = dt.date.fromisoformat(day)
    try:
        return d.replace(year=d.year - years).isoformat()
    except ValueError:                                        # 29 February
        return d.replace(year=d.year - years, day=28).isoformat()


def _bp(a: float, b: float) -> float:
    return round((a - b) * 100.0, 1)


def change(pts: list[tuple[str, float]], days: int, scale: float = 1.0
           ) -> Optional[dict]:
    """The latest point against the point on or before `days` earlier:
    {now, then, now_day, then_day, change} with change scaled (100 for a yield
    in percent to bp). None when either end is missing."""
    if not pts:
        return None
    now_day, now = pts[-1]
    base = _on_or_before(pts, _back(now_day, days))
    if base is None:
        return None
    return {"now": now, "then": base[1], "now_day": now_day, "then_day": base[0],
            "change": round((now - base[1]) * scale, 2)}


def lens(series: list[tuple[str, float]], years: int = 5) -> dict:
    """The latest value's percentile over `years` and over the full stored
    history, each with its real window and n (the metric-lens rule). When the
    stored history is shorter than `years`, the two windows are the same
    observations and `same` is True: one percentile prints, with the window it
    really covers."""
    if not series:
        return {"percentile": None, "n": 0, "same": True, "from": None}
    last_day, last = series[-1]
    first = series[0][0]
    start = _years_back(last_day, years)
    window = [v for d, v in series if d > start]
    full = [v for _, v in series]
    return {"years": years,
            "percentile_window": derived.percentile_of(window, last), "n_window": len(window),
            "percentile_full": derived.percentile_of(full, last), "n_full": len(full),
            "percentile": derived.percentile_of(full, last), "n": len(full),
            "from": first, "same": first > start}


def ordinal(p: Optional[float]) -> str:
    if p is None:
        return "—"
    n = int(round(p))
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def lens_text(lz: dict) -> str:
    """'64th percentile since 2023-10-16 (n=752; FRED serves three years)' or
    '64th of five years (n=1,260), 71st since 1997-08-01 (n=7,300)'."""
    if not lz.get("n"):
        return "no percentile (nothing stored)"
    if lz["same"]:
        return (f"{ordinal(lz['percentile_full'])} percentile of its stored history since "
                f"{lz['from']} (n={lz['n_full']:,}; shorter than {lz['years']} years)")
    return (f"{ordinal(lz['percentile_window'])} percentile of {lz['years']} years "
            f"(n={lz['n_window']:,}), {ordinal(lz['percentile_full'])} since {lz['from']} "
            f"(n={lz['n_full']:,})")


# ---------------------------------------------------------------------------
# ST-R5.34a -- 12-month policy pricing and the flag
# ---------------------------------------------------------------------------
def _add_months(year: int, month: int, n: int) -> str:
    k = year * 12 + (month - 1) + n
    return f"{k // 12:04d}-{k % 12 + 1:02d}"


def futures_by_day(st, cutoff: str, key: str) -> dict[str, dict[str, float]]:
    """{close day: {"YYYY-MM": settlement price}} as of the cutoff."""
    out: dict[str, dict[str, float]] = {}
    for inst in st.instruments(key):
        for d, v in _pts(st, key, cutoff, inst):
            out.setdefault(d, {})[inst] = v
    return out


def policy_12m(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """12-month policy pricing and its four-week change, from the fed funds
    futures: 100 less the contract `horizon_months` ahead of each close's month
    (a constant horizon, so the contract rolls as the month turns). When the
    12-month contract is not stored at both ends, the longest horizon of at
    least six months held at both is read instead and named."""
    cfg = cfg or config()
    c = cfg.get("tightening") or {}
    by_day = futures_by_day(st, cutoff, c.get("futures_key", "fedfunds.futures_price"))
    if not by_day:
        return {"absent": True, "reason": "no fed funds futures stored "
                "(altdata/fed_funds.py)"}
    window = int(c.get("window_days", 28))
    days = sorted(by_day)
    now_day = days[-1]
    base_day = next((d for d in reversed(days) if d <= _back(now_day, window)), None)
    if base_day is None:
        return {"absent": True, "reason": f"fed funds futures stored only since "
                f"{days[0]}: {window} days are not yet held"}

    def at(day: str, h: int) -> Optional[tuple[str, float]]:
        d = dt.date.fromisoformat(day)
        k = _add_months(d.year, d.month, h)
        p = by_day[day].get(k)
        return None if p is None else (k, round(100.0 - p, 4))

    want = int(c.get("horizon_months", 12))
    for h in range(want, 5, -1):
        a, b = at(now_day, h), at(base_day, h)
        if a and b:
            return {"absent": False, "horizon_months": h, "full_horizon": h == want,
                    "contract": a[0], "rate_pct": a[1], "day": now_day,
                    "base_contract": b[0], "base_rate_pct": b[1], "base_day": base_day,
                    "change_bp": _bp(a[1], b[1])}
    return {"absent": True, "reason": f"no fed funds contract six to {want} months "
            f"ahead is stored on both {base_day} and {now_day}"}


def tightening(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """The flag: on when the 10-year rose at least `ten_year_up_bp` and 12-month
    policy pricing fell at least `policy_down_bp` over the window; NFCI's change
    over the same window confirms it or not. Never a zero for a missing leg."""
    cfg = cfg or config()
    c = cfg.get("tightening") or {}
    days = int(c.get("window_days", 28))
    up, down = float(c.get("ten_year_up_bp", 10)), float(c.get("policy_down_bp", 10))
    ten = change(_pts(st, c.get("ten_year_key", "fred.yield_10y"), cutoff), days, 100.0)
    pol = policy_12m(st, cutoff, cfg)
    nf = change(_pts(st, c.get("nfci_key", "fred.nfci"), cutoff), days)
    out: dict[str, Any] = {"ten_year_up_bp": up, "policy_down_bp": down,
                           "window_days": days, "ten": ten, "policy": pol, "nfci": nf,
                           "unvalidated": cfg.get("unvalidated")}
    if ten is None:
        return dict(out, state="absent", reason=f"the 10-year does not hold "
                    f"{days} days")
    if pol.get("absent"):
        return dict(out, state="absent", reason=pol["reason"])
    fired = ten["change"] >= up and pol["change_bp"] <= -down
    confirms = None if nf is None else nf["change"] > float(c.get("nfci_confirm_above", 0.0))
    return dict(out, state="on" if fired else "off", confirms=confirms,
                ten_bp=ten["change"], policy_bp=pol["change_bp"],
                nfci_change=None if nf is None else nf["change"],
                as_of=ten["now_day"])


def tightening_line(t: dict) -> str:
    if t["state"] == "absent":
        return f"Market-does-the-tightening flag: not read — {t['reason']}."
    pol = t["policy"]
    hz = ("12-month" if pol["full_horizon"] else
          f"{pol['horizon_months']}-month (the 12-month contract is not yet held)")
    nf = t["nfci"]
    nf_txt = ("NFCI not held over the window" if nf is None else
              f"NFCI {nf['change']:+.2f} over the window "
              f"({'confirming' if t['confirms'] else 'not confirming'}, {nf['now_day']})")
    if t["state"] == "on":
        return (f"The market is doing the tightening: the 10-year {t['ten_bp']:+.0f} bp "
                f"over {t['window_days']} days while {hz} fed funds pricing moved "
                f"{t['policy_bp']:+.0f} bp ({pol['contract']} contract, "
                f"{pol['base_day']} to {pol['day']}); {nf_txt} {t['unvalidated']}.")
    return (f"Market-does-the-tightening flag off: the 10-year {t['ten_bp']:+.0f} bp and "
            f"{hz} fed funds pricing {t['policy_bp']:+.0f} bp over {t['window_days']} days (it fires "
            f"at 10-year ≥ +{t['ten_year_up_bp']:.0f} bp with pricing ≤ "
            f"−{t['policy_down_bp']:.0f} bp); {nf_txt}.")


# ---------------------------------------------------------------------------
# ST-R5.34b -- the G8 2-year panel
# ---------------------------------------------------------------------------
def panel(st, cutoff: str, cfg: Optional[dict] = None) -> list[dict]:
    """One row per country in the order's order. A gap row carries its reason
    and no figure; a row whose series do not hold four weeks says so."""
    cfg = cfg or config()
    c = cfg.get("tightening") or {}
    days = int(c.get("window_days", 28))
    up, down = float(c.get("ten_year_up_bp", 10)), float(c.get("policy_down_bp", 10))
    rows = []
    for p in cfg.get("panel") or []:
        r = {"id": p["id"], "label": p["label"]}
        if p.get("gap"):
            rows.append(dict(r, state="gap", reason=p["gap"]))
            continue
        two_pts = _pts(st, p["two_year_key"], cutoff)
        ten_pts = _pts(st, p["ten_year_key"], cutoff)
        if not two_pts:
            rows.append(dict(r, state="absent", source=p.get("source"),
                             reason="its 2-year is not stored yet"))
            continue
        two, ten = change(two_pts, days, 100.0), change(ten_pts, days, 100.0)
        r.update(source=p.get("source"), yield_pct=two_pts[-1][1], as_of=two_pts[-1][0],
                 two_bp=None if two is None else two["change"],
                 ten_bp=None if ten is None else ten["change"])
        if two is None or ten is None:
            r.update(state="short", reason=f"{days} days not yet held")
        else:
            r["state"] = ("tightening" if ten["change"] >= up and two["change"] <= -down
                          else "not")
        rows.append(r)
    return rows


# ---------------------------------------------------------------------------
# ST-R5.36a -- the housing block
# ---------------------------------------------------------------------------
def _month_back(day: str, months: int) -> str:
    d = dt.date.fromisoformat(day)
    return _add_months(d.year, d.month, -months) + "-01"


def metro_breadth(st, cutoff: str, key: str, month: str) -> dict:
    """The share of stored metros whose pending sales in `month` are below the
    same month a year earlier (seasonality cancels on the year)."""
    year_ago = _month_back(month, 12)
    falling = n = 0
    for inst in st.instruments(key):
        pts = dict(_pts(st, key, cutoff, inst))
        if month in pts and year_ago in pts:
            n += 1
            falling += pts[month] < pts[year_ago]
    return {"month": month, "falling": falling, "n": n,
            "share": None if not n else round(falling / n, 4)}


def housing(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    c = cfg.get("housing") or {}
    pend = _pts(st, c.get("pending_key", "redfin.pending_sales"), cutoff)
    mort = _pts(st, c.get("mortgage_key", "fred.mortgage_30y"), cutoff)
    # Redfin alone, single-source (ruled 16 Oct 2026: no recurring by-hand line
    # without Ari's yes, so NAR's index, which has no free series, is dropped).
    out: dict[str, Any] = {
        "single_source": True,
        "mortgage": None if not mort else {"rate": mort[-1][1], "as_of": mort[-1][0],
                                           "change_28d_bp": (change(mort, 28, 100.0) or {}).get("change")}}
    if not pend:
        return dict(out, absent=True, reason=c.get("absent_reason", "Redfin is not stored"))
    month, level = pend[-1]
    prior = dict(pend).get(_month_back(month, 12))

    def latest(k):
        p = _pts(st, c.get(k), cutoff)
        return dict(p).get(month)
    out.update(absent=False, month=month, pending=level,
               pending_yoy_pct=None if not prior else round((level / prior - 1) * 100, 2),
               active=latest("active_key"), inventory=latest("inventory_key"),
               months_supply=latest("months_supply_key"),
               breadth=metro_breadth(st, cutoff, c.get("metro_key", "redfin.metro_pending_sales"),
                                     month),
               universe=int(c.get("metro_universe", 50)))
    return out


def housing_lines(h: dict) -> list[str]:
    lines = []
    if h.get("absent"):
        lines.append(f"Housing (Redfin): not read — {h['reason']}.")
    else:
        mon = dt.date.fromisoformat(h["month"]).strftime("%B %Y")
        yoy = ("" if h["pending_yoy_pct"] is None else
               f", {h['pending_yoy_pct']:+.1f}% on the year")
        sup = []
        if h.get("active") is not None:
            sup.append(f"active listings {h['active']:,.0f}")
        if h.get("months_supply") is not None:
            sup.append(f"months of supply {h['months_supply']:.1f}")
        lines.append(f"Pending home sales (Redfin, single-source, {mon}): "
                     f"{h['pending']:,.0f}{yoy}"
                     + (f"; {', '.join(sup)}" if sup else "") + ".")
        b = h["breadth"]
        if b["n"]:
            lines.append(f"Metro breadth: {b['falling']} of {b['n']} top metros with "
                         f"pending sales below a year earlier ({mon}).")
        else:
            lines.append("Metro breadth: not read — no metro holds the month and the "
                         "month a year earlier.")
    m = h.get("mortgage")
    if m:
        ch = ("" if m.get("change_28d_bp") is None else
              f", {m['change_28d_bp']:+.0f} bp over 28 days")
        lines.append(f"30-year mortgage rate {m['rate']:.2f}% (Freddie Mac via FRED, "
                     f"{m['as_of']}{ch}).")
    return lines


# ---------------------------------------------------------------------------
# ST-R5.37a -- the MBA weekly line
# ---------------------------------------------------------------------------
def mba(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    c = cfg.get("mba") or {}
    yoy = _pts(st, c.get("yoy_key", "mba.purchase_nsa_yoy"), cutoff)
    wow = dict(_pts(st, c.get("wow_key", "mba.purchase_sa_wow"), cutoff))
    out: dict[str, Any] = {}
    from . import refusals                                      # noqa: PLC0415
    gap = refusals.text("mba")
    if gap:
        return dict(out, absent=True, reason=gap)
    if not yoy:
        return dict(out, absent=True, reason=c.get("absent_reason", "MBA is not stored"))
    week, y = yoy[-1]
    years = (c.get("windows_years") or [5])[0]
    chain = chained_index(sorted(wow.items()), int(c.get("max_gap_days", 10)),
                          float(c.get("chain_base", 100.0)))
    return dict(out, absent=False, week=week, yoy_pct=y, wow_pct=wow.get(week),
                lens=lens(yoy, years),
                chain=None if not chain else
                {"level": round(chain[-1][1], 4), "base_week": chain[0][0], "weeks_n": len(chain),
                 "lens": lens(chain, years)})


def chained_index(wow: list[tuple[str, float]], max_gap_days: int = 10,
                  base: float = 100.0) -> list[tuple[str, float]]:
    """A level built from the weekly SA changes: `base` at the first stored week,
    then each later week times (1 + its change). The release prints changes only
    and no free series carries the level (ruled 16 Oct 2026: no by-hand level), so
    this is the level the store can make. A gap of more than `max_gap_days`
    between stored weeks breaks the chain; the run after the last break is kept,
    so a missed week never compounds a wrong level."""
    out: list[tuple[str, float]] = []
    prev = None
    for d, v in wow:
        if prev and (dt.date.fromisoformat(d) - dt.date.fromisoformat(prev)).days > max_gap_days:
            out = []
        out.append((d, base if not out else out[-1][1] * (1 + v / 100.0)))
        prev = d
    return out


def mba_prints_on(session_day: str, m: dict, cfg: Optional[dict] = None) -> bool:
    """The close prints the line on the release weekday (Wednesday), when the
    stored week ended within the seven days before the session."""
    cfg = cfg or config()
    d = dt.date.fromisoformat(session_day[:10])
    if m.get("absent") or d.weekday() != int((cfg.get("mba") or {}).get("release_weekday", 2)):
        return False
    return 0 <= (d - dt.date.fromisoformat(m["week"])).days <= 7


def mba_line(m: dict) -> str:
    if m.get("absent"):
        return f"MBA purchase index (weekly): not read — {m['reason']}."
    ch = m.get("chain")
    level = ("" if not ch else
             f" Chained from the weekly changes since {ch['base_week']} (100 = that "
             f"week): {ch['level']:.1f}, the {lens_text(ch['lens'])}.")
    wk = ("" if m.get("wow_pct") is None else
          f"{m['wow_pct']:+.0f}% on the prior survey (SA), ")
    return (f"MBA purchase index, weekly survey dated {m['week']}: {wk}"
            f"{m['yoy_pct']:+.0f}% on the year (NSA); the year-on-year change at the "
            f"{lens_text(m['lens'])}.{level}")


# ---------------------------------------------------------------------------
# ST-R5.41a -- the quality tail
# ---------------------------------------------------------------------------
def spread_bp(a: list[tuple[str, float]], b: list[tuple[str, float]]
              ) -> list[tuple[str, float]]:
    bd = dict(b)
    return [(d, _bp(v, bd[d])) for d, v in a if d in bd]


def quality_tail(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    c = cfg.get("quality_tail") or {}
    days = int(c.get("window_days", 28))
    years = (c.get("windows_years") or [5])[0]
    ccc = _pts(st, c.get("ccc_key", "fred.ccc_oas"), cutoff)
    bb = _pts(st, c.get("bb_key", "fred.bb_oas"), cutoff)
    aaa = _pts(st, c.get("aaa_key", "fred.aaa_oas"), cutoff)
    hy = _pts(st, c.get("hy_key", "fred.hy_oas"), cutoff)
    eu = _pts(st, c.get("euro_hy_key", "fred.euro_hy_oas"), cutoff)
    out: dict[str, Any] = {"overlay": c.get("overlay"),
                           "overlay_built": bool(c.get("overlay_built")),
                           "ccc_excess_bp": float(c.get("ccc_excess_bp", 25)),
                           "window_days": days, "unvalidated": cfg.get("unvalidated"),
                           "euro_leg": c.get("euro_leg_label")}
    if not ccc or not bb:
        return dict(out, absent=True, reason="CCC or BB OAS is not stored (FRED)")
    cb = spread_bp(ccc, bb)
    ca = spread_bp(ccc, aaa)
    dccc, dbb = change(ccc, days, 100.0), change(bb, days, 100.0)
    out.update(absent=False, as_of=cb[-1][0] if cb else None,
               ccc_bb_bp=cb[-1][1] if cb else None, ccc_bb_lens=lens(cb, years),
               ccc_aaa_bp=ca[-1][1] if ca else None,
               ccc_aaa_lens=lens(ca, years) if ca else None,
               ccc_change_bp=None if dccc is None else dccc["change"],
               bb_change_bp=None if dbb is None else dbb["change"],
               euro_hy=None if not eu else {"oas_bp": round(eu[-1][1] * 100, 1),
                                            "as_of": eu[-1][0], "lens": lens(eu, years)},
               us_hy=None if not hy else {"oas_bp": round(hy[-1][1] * 100, 1),
                                          "as_of": hy[-1][0], "lens": lens(hy, years)})
    if dccc is None or dbb is None:
        out.update(cosignal="absent", cosignal_reason=f"{days} days of CCC and BB not yet held")
    else:
        excess = round(dccc["change"] - dbb["change"], 1)
        out.update(excess_bp=excess,
                   cosignal="on" if dccc["change"] > 0 and excess >= out["ccc_excess_bp"]
                   else "off")
    return out


def quality_tail_lines(q: dict) -> list[str]:
    from . import labels                                        # noqa: PLC0415
    if q.get("absent"):
        return [f"Quality tail: not read — {q['reason']}."]
    lines = [f"Quality tail (ICE BofA via FRED, {q['as_of']}): CCC less BB "
             f"{q['ccc_bb_bp']:,.0f} bp, the {lens_text(q['ccc_bb_lens'])}"
             + ("" if q.get("ccc_aaa_bp") is None else
                f"; CCC less AAA {q['ccc_aaa_bp']:,.0f} bp, the "
                f"{lens_text(q['ccc_aaa_lens'])}") + "."]
    over = (f"a co-signal to {q['overlay']}" if q["overlay_built"] else
            f"recorded as a co-signal to {q['overlay']}, which is not built on this "
            f"report, so it is attached to nothing")
    if q["cosignal"] == "absent":
        lines.append(f"CCC-faster-than-BB: not read — {q['cosignal_reason']}.")
    elif q["cosignal"] == "on":
        lines.append(f"CCC widening faster than BB: CCC {q['ccc_change_bp']:+.0f} bp "
                     f"against BB {q['bb_change_bp']:+.0f} bp over {q['window_days']} days, "
                     f"{q['excess_bp']:+.0f} bp more ({over}) {q['unvalidated']}.")
    else:
        lines.append(f"CCC-faster-than-BB off: CCC {q['ccc_change_bp']:+.0f} bp, BB "
                     f"{q['bb_change_bp']:+.0f} bp over {q['window_days']} days (it fires when CCC "
                     f"widens at least {q['ccc_excess_bp']:.0f} bp more than BB).")
    eu, us = q.get("euro_hy"), q.get("us_hy")
    if eu and us:
        lines.append(f"Europe against the US: euro HY OAS {eu['oas_bp']:,.0f} bp "
                     f"({q.get('euro_leg') or 'the proxy for euro CCC'}) at the "
                     f"{lens_text(eu['lens'])}; US HY ({labels.HY_SERIES}) {us['oas_bp']:,.0f} bp at the "
                     f"{lens_text(us['lens'])} ({eu['as_of']}).")
    elif not eu:
        lines.append("Euro HY OAS: not stored yet.")
    return lines


# ---------------------------------------------------------------------------
# The whole cluster
# ---------------------------------------------------------------------------
def build(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    return {"block": "rates_transmission", "descriptive": True, "as_of": cutoff,
            "header": cfg.get("header", "Rates transmission"),
            "tightening": tightening(st, cutoff, cfg), "panel": panel(st, cutoff, cfg),
            "housing": housing(st, cutoff, cfg), "mba": mba(st, cutoff, cfg),
            "quality_tail": quality_tail(st, cutoff, cfg)}


def main(argv: Optional[list[str]] = None) -> int:
    import argparse
    import json

    from . import observations, session
    ap = argparse.ArgumentParser(prog="python -m altdata.st_r5_rates")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show", help="print the cluster as of a cutoff")
    s.add_argument("--as-of", default=None)
    s.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    cutoff = a.as_of or session.utc_iso()
    with observations.ObservationStore() as st:
        b = build(st, cutoff)
    if a.json:
        print(json.dumps(b, indent=2, default=str))
        return 0
    print(b["header"].upper())
    print(tightening_line(b["tightening"]))
    for r in b["panel"]:
        print(f"  {r['label']}: {r.get('reason') or r.get('state')}")
    for ln in housing_lines(b["housing"]) + [mba_line(b["mba"])] + \
            quality_tail_lines(b["quality_tail"]):
        print(ln)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
