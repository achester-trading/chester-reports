"""
ST-10's rendering rows for the features ST-4, ST-5 and ST-9 built: the 07:00
anchor's four lines and the Weekly's Sunday line (the signal-triage order's
section 7; a43-render, 18 Oct 2026). The 12:30 hooks are
daily_cascade/funding_hooks.py.

    build(session, prior, cutoff, db_path)   the anchor's block (payload data)
    html(block)                              its HTML; "" on a day nothing triggers
    sunday_subsection(st, now)               the Weekly's Sunday line and Books A/B

THE 07:00 LINES (config/st10_lines.yaml, each with its trigger and what it
displaces): the auction line on coupon-auction days (SR-22), the Fed-market gap
in FOMC and refunding weeks (SR-21/23), the yen carry flag when the unwind tell is
on (SR-2), and the rally-inside-bear line (SR-8, after the audit). At most four
lines, each under its word cap; a day none triggers prints nothing.

Every line is a dict {id, line, values, constants}: `values` holds every number
the line prints and `constants` the numerals of its names (SR-21, a 12-month leg,
a 20-session vol, 18 Oct), the numeral audit's extra_values, so the audit (D3)
can hold the line to them. Reads the store and
the events table as of the cutoff; fetches nothing; calls no model. DISPLAY AND
MODIFIER ONLY: nothing here enters a composite or the market-state object, and
no vendor value is read. The devaluation tell, wherever it prints here, prints
its two tracked legs and no verdict word (ruling 6 of 18 Oct 2026).
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

import yaml

log = logging.getLogger(__name__)

CONFIG = Path(__file__).resolve().parent.parent / "config" / "st10_lines.yaml"
COUPON = ("Note", "Bond", "TIPS")


def config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def _latest(st, key, now, inst=None):
    from . import absorption_block as B                         # noqa: PLC0415
    return B.latest(st, key, now, inst)


def _series(st, key, now, inst=None) -> list[tuple[str, float]]:
    from altdata.absorption import series                       # noqa: PLC0415
    try:
        return [(d, v) for d, v, _ in series(st, key, now, inst)]
    except Exception:                                           # noqa: BLE001
        return []


def _flag(v: float) -> str:
    return "ON" if v >= 0.5 else "off"


# ---------------------------------------------------------------------------
# The four 07:00 lines
# ---------------------------------------------------------------------------
def auction_line(st, events: list[dict], day: str, now: str) -> Optional[dict]:
    """SR-22: a coupon auction today, with ABS_STRESS as it stands (its base rate
    beside it and its modifier suspended, ruling 3 of 18 Oct)."""
    from altdata import absorption                              # noqa: PLC0415
    todays = []
    for e in events:
        p = e.get("payload") or {}
        inst = str(p.get("instrument") or "")
        if (e.get("source") == "treasury_upcoming" and str(e.get("observed_at"))[:10] == day
                and inst.split(":")[0] in COUPON):
            todays.append((inst, p))
    if not todays:
        return None
    inst, p = sorted(todays)[0]
    typ, term = inst.split(":", 1)
    vals: dict[str, Any] = {}
    size = ""
    try:
        amt = float(str(p.get("offering_amt") or "").replace(",", "").replace("$", ""))
        vals["offering_usd"] = amt
        size = f", ${amt / 1e9:,.0f}bn offered"
    except ValueError:
        pass
    last = _latest(st, "calc.abs_stress", now, inst)
    b = absorption.ABS_STRESS_BASE
    vals.update(base_pct=round(100 * b["on"] / b["n"]), base_since=b["since"],
                base_n=b["n"])
    stress = (f"ABS_STRESS at its last {term} {typ.lower()} auction ({last[0]}): "
              f"{_flag(last[1])}" if last else "ABS_STRESS: no prior auction of the tenor stored")
    more = f" ({len(todays) - 1} more today)" if len(todays) > 1 else ""
    if len(todays) > 1:
        vals["more"] = len(todays) - 1
    line = (f"Coupon auction today: the {term} {typ.lower()}{size}{more}. {stress}; "
            f"{absorption.abs_stress_base_rate()}; display only, its modifier suspended "
            f"until the Doctrine monthly.")
    if last:
        vals["last_day"] = last[0]
    return {"id": "auction", "line": line, "values": vals, "constants": []}


def _week(day: str) -> tuple[dt.date, dt.date]:
    d = dt.date.fromisoformat(day)
    mon = d - dt.timedelta(days=d.weekday())
    return mon, mon + dt.timedelta(days=4)


def refunding_week(day: str, months=(2, 5, 8, 11)) -> bool:
    """The week holding the first Wednesday of a refunding month."""
    mon, fri = _week(day)
    for d in (mon + dt.timedelta(days=k) for k in range(5)):
        if d.month in months and d.weekday() == 2 and d.day <= 7:
            return True
    return False


def fomc_week(events: list[dict], day: str) -> bool:
    mon, fri = _week(day)
    for e in events:
        w = str(e.get("observed_at"))[:10]
        if (e.get("source") == "fed_calendar" and mon.isoformat() <= w <= fri.isoformat()
                and "fomc" in str(e.get("title") or "").lower()
                and "meeting" in str(e.get("title") or "").lower()):
            return True
    return False


def fomc_gap_line(st, events: list[dict], day: str, now: str, cfg: dict) -> Optional[dict]:
    """SR-21/23: the Fed-market gap in FOMC and refunding weeks, descriptive only
    (SR-21's gate failed; ruling 2 of 18 Oct)."""
    months = tuple((cfg["anchor"]["lines"]["fomc_gap"]).get("refunding_months") or ())
    fomc, refund = fomc_week(events, day), refunding_week(day, months)
    if not (fomc or refund):
        return None
    which = "FOMC and refunding week" if fomc and refund else (
        "FOMC week" if fomc else "Refunding week")
    g, c = _latest(st, "calc.fed_mkt_gap_12m", now), _latest(st, "calc.cred_stress", now)
    if not g:
        return {"id": "fomc_gap", "values": {}, "constants": [],
                "line": f"{which}: the Fed-market gap is NOT AVAILABLE (calc.fed_mkt_gap_12m; "
                        f"fed funds futures and FRED FEDTARMD); descriptive only."}
    vals = {"gap_bp": g[1], "as_of": g[0]}
    cs = f"; CRED_STRESS {_flag(c[1])} on the 12-month leg" if c else ""
    return {"id": "fomc_gap", "values": vals, "constants": [12, 21, 18],
            "line": (f"{which}: the Fed-market gap, twelve months, is {g[1]:+.0f} bp (as of "
                     f"{g[0]}){cs}; descriptive only (SR-21's gate failed; ruling of 18 Oct).")}


def yen_line(st, prior: str, now: str) -> Optional[dict]:
    """SR-2: the unwind tell on at the prior close. Display only: SR-2's gate
    failed and ST-5's thresholds stay session-set."""
    from altdata import funding_currency as fc                  # noqa: PLC0415
    uw = _latest(st, "calc.jpy_unwind", now)
    if not uw or uw[0] > prior or uw[1] < 0.5:
        return None
    y = fc.config()["yen"]
    px = [x for x in _series(st, "yfinance.mkt_usdjpy", now) if x[0] <= uw[0]]
    n = int(y["unwind_sessions"])
    vals: dict[str, Any] = {"day": uw[0], "sessions": n}
    move = ""
    if len(px) > n:
        m = 100.0 * (px[-1][1] / px[-1 - n][1] - 1.0)
        vals["move_pct"] = m
        move = f"USDJPY {m:+.1f}% over {n} sessions"
    rv = _latest(st, "calc.usdjpy_rvol_20d", now)
    if rv:
        vals["rvol"] = rv[1]
        move += (", " if move else "") + f"20-session vol {rv[1]:.1f}%"
    z = _latest(st, "calc.jpy_pos_z", now)
    if z:
        vals["pos_z"] = z[1]
    line = (f"Yen carry: the unwind tell is ON at the {uw[0]} close"
            + (f" ({move})" if move else "")
            + (f"; positioning z {z[1]:+.2f}" if z else "")
            + "; display only (SR-2's gate failed; ST-5's thresholds are session-set).")
    return {"id": "yen_flag", "line": line, "values": vals, "constants": [20, 2, 5]}


def bear_state(px: list[tuple[str, float]], c: dict) -> Optional[dict]:
    """The audit's candidate bottom, read live: a 20% drawdown from the 252-session
    closing high inside the last 252 sessions, a close below a falling 200-day,
    and a 10% rally from the lowest close since that high. None when not met."""
    hs, sm, sl = int(c["high_sessions"]), int(c["sma_sessions"]), int(c["slope_sessions"])
    if len(px) < max(hs, sm + sl) + 1:
        return None
    vals = [v for _, v in px]
    i = len(vals) - 1
    win = vals[i - hs + 1:i + 1]
    k_hi = max(range(len(win)), key=win.__getitem__) + (i - hs + 1)
    hi = vals[k_hi]
    after = vals[k_hi:i + 1]
    k_lo = min(range(len(after)), key=after.__getitem__) + k_hi
    lo = vals[k_lo]
    dd = 100.0 * (1 - lo / hi)
    sma = sum(vals[i - sm + 1:i + 1]) / sm
    sma0 = sum(vals[i - sl - sm + 1:i - sl + 1]) / sm
    rally = 100.0 * (vals[i] / lo - 1)
    if dd < float(c["drawdown_pct"]) or not (vals[i] < sma < sma0) \
            or rally < float(c["rally_pct"]):
        return None
    return {"high_day": px[k_hi][0], "low_day": px[k_lo][0], "drawdown_pct": dd,
            "rally_pct": rally, "below_high_pct": 100.0 * (1 - vals[i] / hi),
            "day": px[i][0]}


def rally_line(st, now: str, cfg: dict) -> Optional[dict]:
    """SR-8: a rally inside a bear. The audit FAILed (one confirmation element
    discriminates), so the line says the rally is a mechanism, not a signal."""
    c = cfg["anchor"]["lines"]["rally_in_bear"]
    px = _series(st, "yfinance.mkt_spy", now)
    # A stale series reads no state: SPY's newest close within a week of the read.
    if not px or (dt.date.fromisoformat(now[:10]) - dt.date.fromisoformat(px[-1][0])).days > 7:
        return None
    b = bear_state(px, c)
    if not b:
        return None
    line = (f"Rally inside a bear: SPY {b['rally_pct']:+.1f}% off its low of {b['low_day']}, "
            f"still {b['below_high_pct']:.1f}% below its high of {b['high_day']}, below a "
            f"falling 200-day (as of {b['day']}). The false-bottom audit found one "
            f"confirmation that discriminates and failed its rule, so a rally here is a "
            f"mechanism, not a signal; display only.")
    vals = dict(b, sma=c["sma_sessions"])
    return {"id": "rally_in_bear", "line": line, "values": vals, "constants": [200]}


def anchor_lines(st, events: list[dict], day: str, prior: str, now: str,
                 cfg: Optional[dict] = None) -> list[dict]:
    """The block's lines in declared order, inside its budget."""
    cfg = cfg or config()
    out = []
    for build in (lambda: auction_line(st, events, day, now),
                  lambda: fomc_gap_line(st, events, day, now, cfg),
                  lambda: yen_line(st, prior, now),
                  lambda: rally_line(st, now, cfg)):
        try:
            x = build()
        except Exception:                                       # noqa: BLE001
            log.warning("an ST-10 line faulted", exc_info=True)
            x = None
        if x:
            out.append(x)
    a = cfg["anchor"]
    return [x for x in out[:int(a["max_lines"])]
            if len(x["line"].split()) <= int(a["max_words_per_line"])]


def _calendar(day: str, cutoff: str, db_path: Optional[str]) -> list[dict]:
    from altdata import events as ev_mod                        # noqa: PLC0415
    mon, fri = _week(day)
    with ev_mod.EventStore(db_path) as ev:
        rows = ev.calendar(mon.isoformat(), (fri + dt.timedelta(days=1)).isoformat(),
                           as_of=cutoff)
    out = []
    for r in rows:
        r = dict(r)
        if isinstance(r.get("payload"), str):
            try:
                r["payload"] = json.loads(r["payload"])
            except ValueError:
                r["payload"] = {}
        out.append(r)
    return out


def build(day: str, prior: str, cutoff: str, db_path: Optional[str] = None) -> dict:
    """The anchor's ST-10 block as payload data. Never raises."""
    from altdata import observations                            # noqa: PLC0415
    try:
        events = _calendar(day, cutoff, db_path)
    except Exception:                                           # noqa: BLE001
        log.warning("the events calendar is unreachable for the ST-10 lines", exc_info=True)
        events = []
    try:
        with observations.ObservationStore(db_path) as st:
            lines = anchor_lines(st, events, day, prior, cutoff)
    except Exception:                                           # noqa: BLE001
        log.warning("the ST-10 block faulted", exc_info=True)
        lines = []
    return {"lines": lines, "budget": config()["anchor"]}


def html(block: Optional[dict]) -> str:
    """Nothing on a day nothing triggers; otherwise a heading and the lines."""
    from html import escape                                     # noqa: PLC0415
    lines = (block or {}).get("lines") or []
    if not lines:
        return ""
    items = "".join(f"<li>{escape(x['line'])}</li>" for x in lines)
    return ("<h2 style=\"font-size:15px;margin:18px 0 6px 0\">Signal lines</h2>"
            f"<ul style=\"margin:0;padding-left:18px\">{items}</ul>"
            "<p style=\"font-size:11px;color:#64748b\">Each line prints only on its "
            "trigger and displaces nothing else in the anchor; display only.</p>")


# ---------------------------------------------------------------------------
# The Weekly's Sunday line and the Books' status (section 7's Sunday row)
# ---------------------------------------------------------------------------
def sunday_lines(st, now: str) -> list[str]:
    from . import absorption_block as B, style_block            # noqa: PLC0415
    from altdata import style_regime                            # noqa: PLC0415
    rm = B.rate_machine(st, now)
    cred = next((x for x in rm if x.startswith("CRED_STRESS")), None)
    one = (f"The rates driver: withdrawn (the ruling of 30 Sep), so no cell prints. "
           f"{B.abs_stress_line(st, now)}. " + (cred or "CRED_STRESS: NOT AVAILABLE "
                                                 "(calc.fed_mkt_gap_12m)") + ".")
    a1 = ("A-1 (hedge substitution): not determinable -- the driver is withdrawn and "
          "the correlation leg's word prints in Plumbing & rates.")
    spy = _series(st, "yfinance.mkt_spy", now)
    c = config()["anchor"]["lines"]["rally_in_bear"]
    below = None
    if len(spy) > c["sma_sessions"] + c["slope_sessions"]:
        vals = [v for _, v in spy]
        sm, sl = int(c["sma_sessions"]), int(c["slope_sessions"])
        sma = sum(vals[-sm:]) / sm
        sma0 = sum(vals[-sl - sm:-sl]) / sm
        below = vals[-1] < sma < sma0
    a2 = ("A-2 (bear-regime re-entry): T&B's top side is not built; SPY "
          + ("is" if below else "is not" if below is not None else "cannot be read as")
          + " below a falling 200-day; the false-bottom audit failed its rule, so no "
            "count of confirmations binds (the Doctrine monthly's).")
    a3 = ("A-3 (duration tilt): unmet -- the bond allocation and the Treasuries z are "
          "not determinable, the driver is withdrawn, and ABS_STRESS's modifier is "
          "suspended.")
    try:
        sc = style_regime.config()
        pairs = [style_block.pair_line(st, now, g, v, sc) for g, v in sc["pairs"]]
        b1 = ("Book B, SR-1 style (display only; no flag word until the gate status is "
              "accepted): " + "; ".join(pairs))
    except Exception:                                           # noqa: BLE001
        b1 = "Book B, SR-1 style: NOT AVAILABLE (yfinance.mkt_ivw and yfinance.mkt_ive)"
    b2 = ("Book B, SR-5's RS tell: not live -- SR-5's gate is the box's first-print "
          "edition, and the tell is not built.")
    b3 = B.deval_line(st, now)
    b4 = ("The EM flag (SR-14): display only -- its gate is INSUFFICIENT on our n, so "
          "no flag is rendered as a right.")
    return [one, "Book A's rules:", "  " + a1, "  " + a2, "  " + a3,
            "Book B's tells:", "  " + b1, "  " + b2, "  " + b3, "  " + b4]


# THE WEEKLY'S ID RULE: no internal id reaches the rendered edition, so a key the
# shared line builders name in a NOT AVAILABLE clause prints as "its stored series".
ID_RE = re.compile(r"\b(?:fred|calc|cftc|pm|dial|ndl|yfinance|cfets|cnh|mof|dealer)"
                   r"\.[a-z0-9_]+\b")


def no_ids(line: str) -> str:
    out = ID_RE.sub("its stored series", line)
    return re.sub(r"(its stored series)( and its stored series)+", r"\1", out)


def sunday_subsection(st, now: str) -> dict:
    return {"title": config()["sunday"]["title"], "table": None,
            "lines": [no_ids(x) for x in sunday_lines(st, now)], "paragraph_wanted": False,
            "table_note": ("Read from the store as of the cutoff; nothing fetched. "
                           "Display and modifier only (signal-triage ST-10).")}
