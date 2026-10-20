"""
The volatile-day flag, all four of Doctrine 5.5's arms (A51, ruled 19 Oct 2026,
late evening; session A's a50-dealer-store). Until now the line coded only the
VIX arm (altdata/vol_event.consequence, Book C's rule).

    from daily_cascade import volatile_day
    flag = volatile_day.from_store(session, prior, cutoff, db_path, state_obj=...)
    flag = volatile_day.settle_gap(flag, gap_pct, at)        # the 09:50 open note

THE ARMS, worded as 5.5 words them ("The 0700 report raises the volatile-day flag
when any one of the following holds"):

  vix        the VIX is at or above 25, or has risen 20% or more over the prior
             session -- the stored closes (config vol_event book_c)
  overnight  the overnight range in the ES has exceeded 1.5 times the 20-day
             average true range -- the ES block's 5-minute bars: the futures
             day so far (18:00 ET the evening before to the cutoff) against the
             true range of the 20 complete futures sessions before it, as of 07:00
  gap        the gap at the open is 1% or more -- PROVISIONAL at 07:00, from the
             pre-market price (ES at the session basis, opening_setup's
             pre-market line) against SPY's stored prior close; SETTLED by the
             09:50 open note from SPY's 09:30 open
  gamma      the Gamma dial reads Negative -- read from the market-state object
             the anchor prints (regime.latest), never computed here
  calendar   the calendar shows a tier-1 event -- an FOMC decision, CPI, the
             employment report, or earnings from a name large enough to move the
             index (session-set: config vol_event volatile_day.index_movers)

Each arm prints with its reading and its as-of time. An arm whose input is not
stored says so and is not counted either way. The flag is raised when any arm
holds.

RIGHTS UNCHANGED: PRINTED, NEVER APPLIED. No size is halved anywhere and no
packet is refused: the Doctrine's automatic actions wait for Doctrine #2 and
Book C's activation. Nothing here writes the store, the register, a ledger, a
composite or the market-state object.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Any, Optional

log = logging.getLogger("daily_cascade.volatile_day")

ARMS = ("vix", "overnight", "gap", "gamma", "calendar")
WORDING = {
    "vix": "the VIX is at or above 25, or has risen 20% or more over the prior session",
    "overnight": "the overnight range in the ES has exceeded 1.5 times the 20-day "
                 "average true range",
    "gap": "the gap at the open is 1% or more",
    "gamma": "the Gamma dial reads Negative",
    "calendar": "the calendar shows a tier-1 event — an FOMC decision, CPI, the "
                "employment report, or earnings from a name large enough to move the "
                "index",
}
NOT_APPLIED = ("Printed, not applied: no size is halved and no packet is refused; the "
               "Doctrine's automatic actions wait for Doctrine #2 and Book C's "
               "activation.")


def config() -> dict:
    from altdata import vol_event                               # noqa: PLC0415
    cfg = vol_event.config()
    out = dict(cfg.get("volatile_day") or {})
    out["book_c"] = cfg.get("book_c") or {}
    return out


def _arm(arm: str, holds: Optional[bool], reading: str, as_of: Optional[str],
         **extra) -> dict:
    return {"arm": arm, "holds": holds, "reading": reading, "as_of": as_of,
            "wording": WORDING[arm], **extra}


def _hm(iso: Optional[str]) -> Optional[str]:
    if not iso:
        return None
    try:
        from altdata import session                             # noqa: PLC0415
        t = session.to_eastern(dt.datetime.fromisoformat(str(iso).replace("Z", "+00:00")))
        return f"{t:%Y-%m-%d %H:%M} ET"
    except (TypeError, ValueError):
        return str(iso)


# ---------------------------------------------------------------------------
# The arms, pure: each from its inputs
# ---------------------------------------------------------------------------
def vix_arm(vix: list, cfg: dict) -> dict:
    """`vix`: [(day, close)] to the prior session."""
    bc = cfg.get("book_c") or {}
    lvl, up = float(bc.get("vix_level", 25.0)), float(bc.get("vix_up_pct", 20.0))
    if len(vix) < 2:
        return _arm("vix", None, "not read: fewer than two stored VIX closes", None)
    (d0, v0), (d1, v1) = vix[-2], vix[-1]
    # Rounded before the comparison: 24 on 20 is +20%, not +19.999...%.
    pct = round((v1 / v0 - 1) * 100, 6) if v0 else 0.0
    holds = v1 >= lvl or pct >= up
    return _arm("vix", holds, f"VIX {v1:.2f} at the {d1} close, {pct:+.1f}% on the "
                f"{d0} close (thresholds {lvl:g}, +{up:g}%)", f"{d1} close",
                value=v1, change_pct=round(pct, 2))


def true_ranges(daily: list[dict]) -> list[float]:
    """Wilder's true range over consecutive daily bars (the first bar's own
    high-low has no prior close and is skipped)."""
    out = []
    for a, b in zip(daily, daily[1:]):
        pc = float(a["close"])
        out.append(max(float(b["high"]), pc) - min(float(b["low"]), pc))
    return out


def overnight_arm(hi: Optional[float], lo: Optional[float], daily: list[dict],
                  as_of: Optional[str], cfg: dict) -> dict:
    """`hi`/`lo`: the futures day so far; `daily`: the complete sessions before
    it, oldest first."""
    mult = float(cfg.get("overnight_atr_multiple", 1.5))
    n = int(cfg.get("atr_sessions", 20))
    need = int(cfg.get("min_atr_sessions", 15))
    if hi is None or lo is None:
        return _arm("overnight", None, "not read: no ES bars stored for the overnight "
                    "session", _hm(as_of))
    trs = true_ranges(daily)[-n:]
    if len(trs) < need:
        return _arm("overnight", None, f"not read: {len(trs)} complete ES sessions "
                    f"stored for the average true range (needs {need})", _hm(as_of))
    atr = sum(trs) / len(trs)
    rng = hi - lo
    ratio = round(rng / atr, 6) if atr else 0.0
    return _arm("overnight", ratio > mult,
                f"ES overnight range {rng:.2f} points ({lo:,.2f} to {hi:,.2f}) against "
                f"a {len(trs)}-day average true range of {atr:.2f}: {ratio:.2f} times "
                f"(threshold {mult:g})", _hm(as_of), range=round(rng, 2),
                atr=round(atr, 2), ratio=round(ratio, 3), atr_n=len(trs))


def gap_arm(price: Optional[float], prior_close: Optional[float], as_of: Optional[str],
            cfg: dict, provisional: bool = True, basis: str = "the pre-market price") -> dict:
    th = float(cfg.get("gap_pct", 1.0))
    if price is None or not prior_close:
        return _arm("gap", None, f"not read: {basis} or SPY's prior close not stored",
                    _hm(as_of), provisional=provisional)
    g = round((price / prior_close - 1) * 100, 6)
    word = "provisional, " if provisional else "settled, "
    return _arm("gap", abs(g) >= th,
                f"{word}{basis} {price:,.2f} against SPY's prior close "
                f"{prior_close:,.2f}: {g:+.2f}% (threshold {th:g}% either way)",
                _hm(as_of), provisional=provisional, gap_pct=round(g, 3))


def gamma_arm(state_obj: Optional[dict]) -> dict:
    """Read from the market-state object's Gamma dial; never computed here."""
    if not state_obj:
        return _arm("gamma", None, "not read: no market-state object for the prior "
                    "session", None)
    g = (state_obj.get("dials") or {}).get("gamma") or {}
    st = g.get("state")
    at = state_obj.get("session_date") or state_obj.get("session") or \
        state_obj.get("computed_at")
    if not st:
        return _arm("gamma", None, "not read: the Gamma dial carries no state ("
                    + str(g.get("absent_reason") or g.get("fault") or "absent") + ")",
                    str(at) if at else None)
    return _arm("gamma", str(st).lower() == "negative",
                f"the Gamma dial reads {str(st).capitalize()} (the market-state "
                f"object{', provisional' if g.get('provisional') else ''})",
                str(at) if at else None, state=st)


def movers(cfg: dict) -> set[str]:
    """The names large enough to move the index (session-set)."""
    im = cfg.get("index_movers") or {}
    if im.get("symbols"):
        return {str(s).upper() for s in im["symbols"]}
    from . import ahead                                         # noqa: PLC0415
    acfg = ahead.load_config()
    ranks = (acfg.get("earnings") or {}).get("index_weight_rank") or []
    out = {str(s).upper() for s in ranks + list((acfg.get("earnings") or {})
                                                 .get("hyperscalers") or [])
           if ahead.earnings_class(str(s), acfg) == str(im.get("class", "earnings_mega"))}
    try:
        from register import instruments                        # noqa: PLC0415
        r = instruments.restrictions()
        out = {s for s in out if not r.is_restricted(s)}         # the blocklist stands
    except Exception:                                           # noqa: BLE001
        pass
    return out


def calendar_arm(rows: list[dict], day: str, as_of: Optional[str], cfg: dict,
                 names: Optional[set] = None) -> dict:
    """`rows`: the events calendar's rows from the prior evening to the session's
    end. A tier-1 release on the session's ET day; an index mover's earnings on
    the session's ET day or after the prior session's 16:00 close."""
    from altdata import session                                 # noqa: PLC0415
    titles = [str(t) for t in cfg.get("tier1_events") or []]
    names = names if names is not None else movers(cfg)
    found: list[str] = []
    for r in rows:
        try:
            t = session.to_eastern(dt.datetime.fromisoformat(
                str(r.get("observed_at")).replace("Z", "+00:00")))
        except (TypeError, ValueError):
            continue
        title = str(r.get("title") or "")
        if t.date().isoformat() == day:
            for k in titles:
                if k.lower() in title.lower() and k not in found:
                    found.append(k)
        p = r.get("payload")
        if isinstance(p, str):
            try:
                p = json.loads(p)
            except ValueError:
                p = {}
        p = p or {}
        sym = str(p.get("symbol") or "").upper()
        if (p.get("kind") == "earnings" or "earnings" in title.lower()) and sym in names:
            prior_eve = t.date() < dt.date.fromisoformat(day) and t.hour >= 16
            if (t.date().isoformat() == day or prior_eve) and f"{sym} earnings" not in found:
                found.append(f"{sym} earnings")
    if found:
        return _arm("calendar", True, "tier-1 on the calendar: " + ", ".join(found),
                    _hm(as_of), events=found)
    return _arm("calendar", False, "no tier-1 event on the calendar (an FOMC decision, "
                "CPI, the employment report, or an index mover's earnings)", _hm(as_of),
                events=[])


# ---------------------------------------------------------------------------
# The flag
# ---------------------------------------------------------------------------
def flag(arms: list[dict], at: Optional[str] = None) -> dict:
    held = [a["arm"] for a in arms if a["holds"]]
    unread = [a["arm"] for a in arms if a["holds"] is None]
    provisional = any(a.get("provisional") for a in arms if a["arm"] == "gap")
    out = {"arms": arms, "raised": bool(held), "held": held, "not_read": unread,
           "gap_provisional": provisional, "as_of": _hm(at), "applied": False}
    out["lines"] = lines(out)
    return out


def headline(f: dict) -> str:
    if f["raised"]:
        return (f"Volatile-day flag RAISED ({', '.join(f['held'])})"
                + (", the gap provisional until the open" if f["gap_provisional"]
                   and "gap" in f["held"] else "") + ".")
    return ("Volatile-day flag not raised: no arm holds"
            + (f" ({', '.join(f['not_read'])} not read)" if f["not_read"] else "")
            + (", the gap provisional until the open" if f["gap_provisional"] else "")
            + ".")


def lines(f: dict) -> list[str]:
    out = [headline(f)]
    for a in f["arms"]:
        mark = "holds" if a["holds"] else ("not read" if a["holds"] is None else "does not hold")
        out.append(f"{a['wording'][0].upper()}{a['wording'][1:]}: {mark} -- {a['reading']}"
                   + (f" (as of {a['as_of']})" if a.get("as_of") else "") + ".")
    out.append(NOT_APPLIED)
    return out


def settle_gap(f: dict, open_price: Optional[float], prior_close: Optional[float],
               at: Optional[str], cfg: Optional[dict] = None) -> dict:
    """The 09:50 open note: the gap arm settled from SPY's 09:30 open, the flag
    re-read, and whether it is now raised."""
    cfg = cfg if cfg is not None else config()
    was = bool(f.get("raised"))
    arms = [a for a in f.get("arms") or [] if a["arm"] != "gap"]
    g = gap_arm(open_price, prior_close, at, cfg, provisional=False,
                basis="SPY's 09:30 open")
    arms.insert(min(2, len(arms)), g)
    out = flag(arms, at)
    out["was_raised_at_0700"] = was
    out["settled_line"] = (
        f"The gap settled at the open ({g['reading']}): the flag is "
        + ("now raised" if out["raised"] and not was else
           "still raised" if out["raised"] else
           "no longer raised" if was else "not raised") + ".")
    out["lines"].insert(1, out["settled_line"])
    return out


# ---------------------------------------------------------------------------
# From the store (read only)
# ---------------------------------------------------------------------------
def _es_inputs(day: str, cutoff: str, db_path: Optional[str], cfg: dict):
    from altdata import bars as bars_mod, es_block              # noqa: PLC0415
    ecfg = es_block.load_config()
    n = int(cfg.get("atr_sessions", 20))
    share = None
    try:
        from altdata import volume_profile as vp                # noqa: PLC0415
        share = vp.complete_share()
    except Exception:                                           # noqa: BLE001
        share = 0.9
    with bars_mod.BarStore(db_path) as bst:
        sessions = es_block._sessions_back(day, n + 2)          # noqa: SLF001
        per = es_block.read_sessions(bst, sessions, cutoff, ecfg.get("instrument", "es"))
        per, _ = es_block.roll_adjust(per, es_block.contracts_of(
            sessions, getattr(bst, "conn", None), cutoff, ecfg))
    cur = per[-1]
    hi = max((float(b["high"]) for b in cur["bars"]), default=None)
    lo = min((float(b["low"]) for b in cur["bars"]), default=None)
    kept = [x for x in per[:-1] if x["expected"]
            and es_block._complete([x], share) is None]         # noqa: SLF001
    daily = [b for b in (es_block.daily_bar(x) for x in kept) if b]
    return hi, lo, daily


def _prior_close(st, prior: str, cutoff: str) -> Optional[float]:
    rows = [r for r in st.as_of("yfinance.mkt_spy", cutoff)
            if str(r["observed_at"])[:10] <= prior and r.get("value_num") is not None]
    return float(rows[-1]["value_num"]) if rows else None


def from_store(day: str, prior: str, cutoff: str, db_path: Optional[str] = None,
               state_obj: Optional[dict] = None, premarket: Optional[dict] = None,
               cfg: Optional[dict] = None) -> dict:
    """The 07:00 flag, every arm read as of the cutoff. Never raises: an arm
    whose read faults is "not read" with the fault named."""
    cfg = cfg if cfg is not None else config()
    from altdata import events, observations, vol_event          # noqa: PLC0415
    try:
        with observations.ObservationStore(db_path) as st:
            vix = [(d, v) for d, v in vol_event.read_series(st, cutoff)["vix"]
                   if str(d)[:10] <= prior]
            pc = _prior_close(st, prior, cutoff)
    except Exception:                                           # noqa: BLE001
        log.warning("volatile-day flag: the store faulted", exc_info=True)
        vix, pc = [], None
    arms = [vix_arm(vix, cfg)]
    try:
        hi, lo, daily = _es_inputs(day, cutoff, db_path, cfg)
        arms.append(overnight_arm(hi, lo, daily, cutoff, cfg))
    except Exception as exc:                                    # noqa: BLE001
        arms.append(_arm("overnight", None, f"not read: the ES bars faulted "
                         f"({type(exc).__name__})", _hm(cutoff)))
    spy = ((premarket or {}).get("values") or {}).get("spy")
    arms.append(gap_arm(spy, pc, cutoff, cfg, provisional=True))
    arms.append(gamma_arm(state_obj))
    try:
        eve = (dt.date.fromisoformat(day) - dt.timedelta(days=4)).isoformat()
        with events.EventStore(db_path) as ev:
            rows = ev.calendar(eve, day, as_of=cutoff)
        arms.append(calendar_arm(rows, day, cutoff, cfg))
    except Exception as exc:                                    # noqa: BLE001
        arms.append(_arm("calendar", None, f"not read: the events calendar faulted "
                         f"({type(exc).__name__})", _hm(cutoff)))
    return flag(arms, cutoff)


def for_open_note(day: str, prior: str, at: str, open_price: Optional[float],
                  prior_close: Optional[float], db_path: Optional[str] = None) -> dict:
    """The 07:00 flag as the anchor read it (every arm as of 07:00 ET, the object
    the anchor printed), then its gap settled from SPY's 09:30 open."""
    from altdata import observations, session                   # noqa: PLC0415
    from . import opening_setup                                 # noqa: PLC0415
    import regime                                               # noqa: PLC0415
    seven = dt.datetime.combine(dt.date.fromisoformat(day), dt.time(7, 0),
                                tzinfo=session._eastern_tz())   # noqa: SLF001
    c7 = seven.astimezone(dt.timezone.utc).isoformat()
    try:
        with observations.ObservationStore(db_path) as st:
            obj = regime.latest(store=st, session_day=prior)
    except Exception:                                           # noqa: BLE001
        obj = None
    pm = opening_setup.premarket_from_store(day, c7, db_path)
    return settle_gap(from_store(day, prior, c7, db_path, state_obj=obj, premarket=pm),
                      open_price, prior_close, at)


def html(f: Optional[dict]) -> str:
    from html import escape                                     # noqa: PLC0415
    if not f or not f.get("lines"):
        return ""
    return ('<p style="font-size:13px;margin:6px 0"><b>' + escape(f["lines"][0]) + "</b></p>"
            + "".join(f'<p style="font-size:12px;margin:2px 0">{escape(x)}</p>'
                      for x in f["lines"][1:]))
