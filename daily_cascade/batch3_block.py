"""
Signal-triage batch 3, Tranche A -- where each read prints.

    tape_items(st, cutoff)              the close's tape: the 30y JGB line
    weekly_subsections(st, now, then, cadence)
                                        Plumbing & rates: the JGB line, SR-30's
                                        narrow flag, SR-33's operations, SR-34's
                                        fast tells, SR-6 by tenor
    monthly_subsections(st, now, then)  the Monthly's Plumbing: the same, plus
                                        the Rate and Liquidity Machine's lever
                                        table with SR-33's modifier
    misfit_items(st, now)               the Monthly's "what doesn't fit": one
                                        sentence when SR-30 is at its crisis tier

The reads are altdata/batch3.py's; this module only lays them out. Every table
here carries its figures with their as-of dates, and no paragraph is asked of
these sub-sections (`paragraph_wanted: False`): the section's own prose reads the
section's table, under the audits it already runs.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from altdata import batch3

from . import readability as rd

TITLE_JGB = "Japan's 30-year and the 4.5% line (SR-32, early line)"
TITLE_EU = "EU sovereign stress: OAT–Bund and BTP–Bund (SR-30)"
TITLE_BUYBACKS = "Treasury buybacks (SR-33)"
TITLE_JAPAN = "Japan's intervention funding and FIMA (SR-34)"
TITLE_TENOR = "Rates by tenor: what moved each yield (SR-6)"
TITLE_LEVERS = "The Rate and Liquidity Machine: levers"


def _item(key: str, text: str, priority: int = 2, value=None) -> dict:
    from .stack import item                                     # noqa: PLC0415
    return item(key, text, priority, value)


def _ord(p: Optional[float]) -> str:
    if p is None:
        return "—"
    n = int(round(p))
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def _bp(v: Optional[float]) -> str:
    # weekly-fixes-7 item 12: rounded before the sign (no "-0.0 bp").
    return "—" if v is None else f"{v:+.1f} bp" if round(v, 1) else "0.0 bp"


def _usd_bn(v: Optional[float], dp: int = 1) -> str:
    return "—" if v is None else f"${v / 1e9:,.{dp}f}bn"


def _usd_bn_signed(v: Optional[float]) -> str:
    if v is None:
        return "—"
    if not round(v / 1e9, 1):
        return "unch"                       # weekly-fixes-7 item 12: no "−$0.0bn"
    return f"{'+' if v > 0 else '−' if v < 0 else ''}${abs(v) / 1e9:,.1f}bn"


# ---------------------------------------------------------------------------
# ST-B3-16 -- the JGB line, on the close's tape and in Plumbing
# ---------------------------------------------------------------------------
def tape_items(st, cutoff: str, cfg: Optional[dict] = None) -> list[dict]:
    """Nothing below the approach line; one line approaching; the line and the
    mechanism flagged."""
    j = batch3.jgb_line(st, cutoff, cfg)
    if not j.get("line"):
        return []
    return [_item("tape:jgb30_line", j["line"], 1 if j["state"] == "flagged" else 2,
                  (j["state"], j["level"]))]


def jgb_subsection(st, now: str, cfg: Optional[dict] = None) -> Optional[dict]:
    j = batch3.jgb_line(st, now, cfg)
    if not j.get("line"):
        return None
    return {"title": TITLE_JGB, "lines": [j["line"]], "paragraph_wanted": False,
            "data": {"jgb_line": j}}


# ---------------------------------------------------------------------------
# ST-B3-03 -- SR-30's narrow flag
# ---------------------------------------------------------------------------
def eu_subsection(st, now: str, cfg: Optional[dict] = None,
                  cadence: str = "weekly") -> dict:
    # EUR/CHF's change over the edition's own period (a Monthly prints no week).
    e = batch3.eu_stress(st, now, cfg, 30 if cadence == "monthly" else 7)
    live = e.get("tiers_live")
    rows, lines = [], []
    for p in e["pairs"]:
        if p.get("absent"):
            lines.append(f"{p['label']}: {p['reason']}.")
            continue
        pc = p["percentiles"]
        rows.append([p["label"], f"{p['bp']:.1f} bp", _bp(p["change_bp"]),
                     f"{_ord(pc.get(5, {}).get('pct'))} (n={pc.get(5, {}).get('n')})",
                     f"{_ord(pc.get(20, {}).get('pct'))} (n={pc.get(20, {}).get('n')})"]
                    + ([{"watch": f"WATCH (≥ {e['watch_bp']:.0f} bp)", "crisis": "CRISIS",
                         "none": "below the watch line"}.get(p.get("tier"), "—")
                        if p.get("tier") else "untiered"] if live else [])
                    + [p["as_of"]])
    if e.get("eurchf"):
        x = e["eurchf"]
        rows.append(["EUR/CHF (francs per euro), the transmission tell",
                     f"{x['level']:.4f}",
                     "—" if x["week_change_pct"] is None else f"{x['week_change_pct']:+.2f}%",
                     "—", "—"] + (["—"] if live else []) + [x["as_of"]])
    else:
        # weekly-fixes-7 item 11: the source and the date, no symbol string.
        lines.append(f"EUR/CHF: not yet stored ({rd.starts_line('Yahoo Finance', now)}).")
    tier = e["tier"]
    flag = {"watch": f"OAT–Bund at the watch tier (≥ {e['watch_bp']:.0f} bp)",
            "crisis": f"OAT–Bund at the crisis tier (≥ {e['crisis_bp']:.0f} bp)"}.get(tier)
    if flag:
        lines.insert(0, f"{flag} {e['unvalidated']}.")
    tiers = (f"Tiers on OAT–Bund only: watch {e['watch_bp']:.0f} bp, crisis "
             f"{e['crisis_bp']:.0f} bp." if live else
             "No tier prints: the tiers sit on a daily weekly close, which no free "
             "official source publishes yet.")
    return {"title": TITLE_EU,
            "table": {"columns": ["Spread", "Level", "Change on the prior period",
                                  "5-year percentile", "20-year percentile"]
                      + (["Tier"] if live else []) + ["As of"],
                      "rows": rows} if rows else None,
            "lines": lines, "paragraph_wanted": False,
            "table_note": (f"Spreads are the ECB's monthly-average 10-year yields (the "
                           f"convergence series), France or Italy less Germany: no free "
                           f"official source publishes a daily OAT or BTP. {tiers} "
                           f"{e['unvalidated']}"),
            "data": {"eu_stress": e}}


# ---------------------------------------------------------------------------
# ST-B3-04 -- SR-33's events block
# ---------------------------------------------------------------------------
def buyback_subsection(st, now: str, then: str, cfg: Optional[dict] = None) -> dict:
    ops = batch3.buyback_operations(st, now, then[:10], now[:10], cfg)
    t = batch3.tga(st, now, cfg)
    rows = [[o["date"], o["sector"] + ("" if o["type"] == "Liquidity Support"
                                       else f" ({o['type'].lower()})"),
             f"{_usd_bn(o['bought'], 2)} of {_usd_bn(o['max'], 2)}",
             "—" if o["ratio"] is None else f"{o['ratio']:.0%}",
             "not yet stored" if o["y30_next_bp"] is None
             else f"{_bp(o['y30_next_bp'])} ({o['y30_next_day']})"]
            for o in ops]
    lines = [] if rows else ["No buyback operation in the window."]
    if t:
        lines.append(f"TGA ${t['usd_bn']:,.1f}bn (FRED, {t['as_of']}).")
    return {"title": TITLE_BUYBACKS,
            "table": {"columns": ["Operation", "Sector", "Bought of the maximum",
                                  "Bought/max", "30-year, next session"],
                      "rows": rows} if rows else None,
            "lines": lines, "paragraph_wanted": False,
            "table_note": ("Treasury's buyback operations (Fiscal Data); the 30-year's "
                           "next-session change is the stored 30-year (DGS30) from the "
                           "operation's date to the next session it carries. "
                           "Descriptive; unvalidated, n=0."),
            "data": {"buybacks": ops, "tga": t}}


# ---------------------------------------------------------------------------
# ST-B3-05 -- SR-34's fast tells
# ---------------------------------------------------------------------------
def japan_subsection(st, now: str, cfg: Optional[dict] = None,
                     cadence: str = "weekly") -> dict:
    cfg = cfg or batch3.config()
    j = batch3.japan_funding(st, now)
    lines = []
    tot, sec = j["reserves_total"], j["reserves_securities"]
    if tot:
        lines.append(f"Japan's reserves {_usd_bn(tot['value'])}, "
                     f"{_usd_bn_signed(tot['change'])} on the month "
                     f"(MoF, month to {tot['as_of']})"
                     + (f"; foreign securities {_usd_bn(sec['value'])}, "
                        f"{_usd_bn_signed(sec['change'])} (to {sec['as_of']})" if sec else "")
                     + ".")
    else:
        lines.append("Japan's reserves: not yet stored "
                     f"({rd.starts_line("Japan's Ministry of Finance", now)}).")
    f = j["fima"]
    if f:
        wa = j["fima_weekavg"]
        lines.append(f"FIMA repo facility: {_usd_bn(f['value'])} outstanding on "
                     f"Wednesday {f['as_of']}"
                     + (f", week average {_usd_bn(wa['value'])}"
                        if wa and cadence != "monthly" else "")
                     + (" — in use" if f["value"] > 0 or (wa and wa["value"] > 0)
                        else "") + " (H.4.1).")
    else:
        lines.append("FIMA repo usage: not yet stored "
                     f"({rd.starts_line("the Fed's H.4.1", now)}).")
    lines.append(f"Both are {(cfg.get('japan_reserves') or {}).get('lag_line')}.")
    return {"title": TITLE_JAPAN, "lines": lines, "paragraph_wanted": False,
            "data": {"japan_funding": j}}


# ---------------------------------------------------------------------------
# ST-B3-02 -- SR-6 by tenor
# ---------------------------------------------------------------------------
def _cell(m: Optional[dict]) -> str:
    return "—" if not m else _bp(m["bp"])


def tenor_rows(lens: dict, window: str) -> list[list]:
    out = []
    for r in lens["rows"]:
        nom = r["nominal"]
        real = _cell(r["real"]) + (f" ({r['real_label']})" if r.get("real_label")
                                   and r["real"] else "")
        acm = (r["acm_note"],) * 2 if r.get("acm_note") else (
            _cell(r["expected_rate"]), _cell(r["term_premium"]))
        # weekly-fixes-7 item 3: the window prints INLINE, so the table is six
        # columns and the renderer's six-column rule no longer splits off a
        # second table holding only the dates.
        span = "" if not nom else f" ({_day_month(nom['from'])} to {_day_month(nom['to'])})"
        out.append([f"{r['tenor']}, {window}{span}", _cell(nom), real,
                    "—" if r["breakeven_bp"] is None else _bp(r["breakeven_bp"]),
                    acm[0], acm[1]])
    return out


def _day_month(d: str) -> str:
    x = dt.date.fromisoformat(str(d)[:10])
    return f"{x.day} {x:%b}"


def fred_lag_line(fred_to: Optional[str], tape_to: Optional[str]) -> Optional[str]:
    """Item 3: two "week" figures for the 10-year can sit in one edition -- the
    tape's (Yahoo's ^TNX closes) and SR-6's (FRED's legs, which publish later).
    The line names both windows' ends so a reader sees why they differ."""
    if not fred_to or not tape_to or str(fred_to)[:10] >= str(tape_to)[:10]:
        return None
    from altdata import session                                 # noqa: PLC0415
    a, b = dt.date.fromisoformat(str(fred_to)[:10]), dt.date.fromisoformat(str(tape_to)[:10])
    n, d = 0, a
    while d < b:
        d += dt.timedelta(days=1)
        try:
            n += 1 if session.is_trading_session(d) else 0
        except Exception:                                       # noqa: BLE001
            n += 1 if d.weekday() < 5 else 0
    words = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight",
             "nine", "ten")
    return (f"FRED's legs lag {words[n] if n < len(words) else n} "
            f"session{'s' if n != 1 else ''} (to {_day_month(a)}); "
            f"the nominal week in the tape runs to {_day_month(b)}.")


def _tape_to(st, now: str) -> Optional[str]:
    try:
        from altdata import levels                              # noqa: PLC0415
        rows, _ = levels.daily_bars(levels.tape_spec("y10"), now[:10], now, st)
        return str(rows[-1]["observed_at"])[:10] if rows else None
    except Exception:                                           # noqa: BLE001
        return None


def tenor_frame(lens: dict, window: str) -> Optional[str]:
    """Which tenor moved most and which leg was larger -- no cause."""
    if not lens.get("led"):
        return None
    r = next(x for x in lens["rows"] if x["tenor"] == lens["led"])
    parts = []
    if r.get("leg"):
        parts.append(f"its {r['leg']} leg was the larger of real and breakeven")
    if r.get("acm_leg"):
        parts.append(f"in ACM's split the {r['acm_leg']} was the larger")
    return (f"Over the {window}, the {r['tenor']} moved most "
            f"({_bp(r['nominal']['bp'])})" + ("; " + "; ".join(parts) if parts else "")
            + ".")


def tenor_subsection(st, now: str, then_week: str, then_month: str,
                     cfg: Optional[dict] = None, cadence: str = "weekly") -> dict:
    """The week's and the month's split on the Weekly; the month's alone on the
    Monthly, which prints no week phrase (validate_stack_cadence)."""
    wk = None if cadence == "monthly" else batch3.tenor_lens(st, now, then_week, cfg)
    mo = batch3.tenor_lens(st, now, then_month, cfg)
    rows = (tenor_rows(wk, "week") if wk else []) + tenor_rows(mo, "month")
    lines = [x for x in ((tenor_frame(wk, "week") if wk else None),
                         tenor_frame(mo, "month")) if x]
    if wk:
        ten = next((r for r in wk["rows"] if r["tenor"] == "10y" and r["nominal"]), None)
        lag = fred_lag_line(ten["nominal"]["to"] if ten else None, _tape_to(st, now))
        if lag:
            lines.append(lag)
    return {"title": TITLE_TENOR,
            "table": {"columns": ["Tenor and window (from and to)", "Nominal",
                                  "Real yield", "Breakeven",
                                  "Expected short rate (ACM)",
                                  "Term premium (ACM)"], "rows": rows},
            "lines": lines, "paragraph_wanted": False,
            "table_note": ("Breakeven is the nominal move less the real yield's, so the "
                           "two sum to the move; the 2-year has no TIPS series and reads "
                           "the 5-year's, labelled. Expected short rate and term premium "
                           "are ACM's (a model's split of its own fitted yield, not of "
                           "the quoted one); ACM does not publish past ten years. The "
                           "10-year attribution block's models (DKW, Kim-Wright, ACM) "
                           "are the rates attribution block's. Descriptive: which tenor "
                           "moved most and which leg was larger, nothing causal."),
            "data": {"tenor_week": wk, "tenor_month": mo}}


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def _month_before(now: str) -> str:
    d = dt.date.fromisoformat(now[:10])
    return (d - dt.timedelta(days=30)).isoformat() + "T23:59:59+00:00"


def weekly_subsections(st, now: str, then: str, cadence: str = "weekly",
                       cfg: Optional[dict] = None) -> list[dict]:
    """Plumbing & rates' Tranche A sub-sections, in order. A read that faults is
    left out and logged, never allowed to take the section down."""
    import logging                                              # noqa: PLC0415
    cfg = cfg or batch3.config()
    month = then if cadence == "monthly" else _month_before(now)
    week = (then if cadence != "monthly" else
            (dt.date.fromisoformat(now[:10]) - dt.timedelta(days=7)).isoformat()
            + "T23:59:59+00:00")
    out = []
    for fn in (lambda: jgb_subsection(st, now, cfg),
               lambda: eu_subsection(st, now, cfg, cadence),
               lambda: buyback_subsection(st, now, then, cfg),
               lambda: japan_subsection(st, now, cfg, cadence),
               lambda: tenor_subsection(st, now, week, month, cfg, cadence)):
        try:
            s = fn()
        except Exception:                                       # noqa: BLE001
            logging.getLogger(__name__).warning("batch 3 block faulted", exc_info=True)
            continue
        if s:
            out.append(s)
    return out


def levers_subsection(st, now: str, then: str, cfg: Optional[dict] = None) -> dict:
    """The Monthly's lever table: the long-end supply read with SR-33's
    modifier line (the change order, SR-33 Rights)."""
    ops = batch3.buyback_operations(st, now, then[:10], now[:10], cfg)
    mod = batch3.lever_modifier(ops, cfg)
    return {"title": TITLE_LEVERS,
            "table": {"columns": ["Lever", "This month", "Modifier"],
                      "rows": [["Long-end supply (coupon issuance less Treasury's "
                                "long-end buybacks)",
                                f"{sum(1 for o in ops if o['long_end'])} long-end "
                                f"operation(s)", mod]]},
            "paragraph_wanted": False, "data": {"modifier": mod}}


def monthly_subsections(st, now: str, then: str, cfg: Optional[dict] = None
                        ) -> list[dict]:
    return weekly_subsections(st, now, then, "monthly", cfg) + [
        levers_subsection(st, now, then, cfg)]


def misfit_items(st, now: str, cfg: Optional[dict] = None) -> list[dict]:
    """One sentence in the Monthly's "what doesn't fit" at SR-30's crisis tier,
    and none below it (decision 2)."""
    e = batch3.eu_stress(st, now, cfg)
    if e["tier"] != "crisis":
        return []
    p = next(x for x in e["pairs"] if x["id"] == "oat_bund")
    return [_item("misfit:sr30_crisis",
                  f"OAT–Bund at {p['bp']:.1f} bp (ECB monthly, {p['as_of']}) is at "
                  f"SR-30's crisis tier, the November 2011 peak of its own series, "
                  f"in the core rather than the periphery {e['unvalidated']}.", 1,
                  (p["bp"], p["as_of"]))]
