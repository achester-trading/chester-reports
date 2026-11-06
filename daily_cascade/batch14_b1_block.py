"""
Signal-triage Batch 14, Part B1 -- items 65 and 71 laid out (a57-batch14-b1, 23 Oct
2026; docs/change-order-signal-triage-batch-14-2026-10-20.md, F1-F8). The figures
are altdata/speed_attribution.py's, altdata/ai_trade.py's and
altdata/fragility.py's; this module computes nothing.

  THE CLOSE     Mechanics: the speed-flag attribution on a flag day (after item
                52's block when both fire, the cross-item note), and the fragility
                panel; Plumbing & rates: the attribution's one line; item 52's
                lens table: the report-only "liquidity" row; item 45's levels
                read: the flag's line.
  WEEKLY AND MONTHLY  Mechanics: the Broad-AI proxy line after item 31's
                concentration table (and GTM-3's twin), and the fragility panel.
  THE MONTHLY   Plumbing & rates: the AI-bottleneck PPI line, a panel of item 46's
                inflation block (daily_cascade/inflation_block.py).
  FACTOR I      the AI-credit gap line beside SR-16's neocloud line
                (daily_cascade/absorption_block.py).

Tables and code-written lines only: no paragraph is asked for, so no prose word
is added to any budget. A builder that faults is logged and prints nothing.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)

AI_TITLE = "Broad AI against the S&P without its technology sector (proxy)"


def _safe(fn: Callable, what: str, default: Any = None) -> Any:
    try:
        return fn()
    except Exception:                                           # noqa: BLE001
        log.warning("%s faulted", what, exc_info=True)
        return default


def _item(key: str, text: str, priority: int, value: Any = None) -> dict:
    from . import stack                                         # noqa: PLC0415
    return stack.item(key, text, priority, value)


def _last_day(st, cutoff: str) -> Optional[str]:
    from altdata import fragility                               # noqa: PLC0415
    pts = fragility._pts(st, fragility.config()["spy"]["close"], cutoff)
    return pts[-1][0] if pts else None


# ---------------------------------------------------------------------------
# Item 71: the fragility panel, the lens and the levels-read line
# ---------------------------------------------------------------------------
def fragility_read(st, day: Optional[str], cutoff: str) -> Optional[dict]:
    from altdata import fragility                               # noqa: PLC0415
    day = day or _last_day(st, cutoff)
    if not day:
        return None
    return _safe(lambda: fragility.build(st, day, cutoff), "the fragility read")


def fragility_panel(st, day: Optional[str], cutoff: str) -> Optional[dict]:
    from altdata import fragility                               # noqa: PLC0415
    ev = fragility_read(st, day, cutoff)
    return fragility.panel(ev) if ev else None


def liquidity_lens(st, day: str, cutoff: str) -> Optional[dict]:
    """Item 52's report-only "liquidity" row, or None when there is no read."""
    from altdata import fragility                               # noqa: PLC0415
    ev = fragility_read(st, day, cutoff)
    if not ev or ev["depth"]["amihud"].get("state") != "computed":
        return None
    return fragility.lens(ev)


def levels_line(st, day: str, cutoff: str) -> Optional[str]:
    """Item 45's levels read: the flag's line, or None with no read."""
    from altdata import fragility                               # noqa: PLC0415
    ev = fragility_read(st, day, cutoff)
    if not ev or ev["flag"]["state"] == "not read":
        return None
    return fragility.levels_line(ev)


# ---------------------------------------------------------------------------
# Item 65: the speed-flag attribution, the proxy line, the PPI panel
# ---------------------------------------------------------------------------
def speed_event(st, day: str, cutoff: str, screen: Optional[dict]) -> Optional[dict]:
    from altdata import speed_attribution as sa                  # noqa: PLC0415
    return _safe(lambda: sa.for_session(st, day, cutoff, screen), "the speed attribution")


def ai_proxy_subsection(st, cutoff: str) -> Optional[dict]:
    from altdata import ai_trade                                # noqa: PLC0415
    b = _safe(lambda: ai_trade.build(st, cutoff), "the AI proxy pair")
    if not b:
        return None
    return {"title": AI_TITLE, "paragraph_wanted": False,
            "lines": [ai_trade.proxy_line(b["proxy"])],
            "data": {"ai_proxy": {k: b["proxy"].get(k) for k in
                                  ("state", "as_of", "rel_1y_pp", "label")}}}


def ai_ppi_panel(st, cutoff: str) -> Optional[dict]:
    """The AI-bottleneck PPI line as a panel of item 46's inflation block; None
    when none of the three is stored (the slot prints nothing)."""
    from altdata import ai_trade                                # noqa: PLC0415
    cfg = ai_trade.config()
    r = ai_trade.ppi_read({s["key"]: ai_trade._pts(st, s["key"], cutoff)
                           for s in cfg.get("ppi") or []}, cfg)
    if not r["rows"]:
        return None
    return {"title": "The AI bottleneck in producer prices (item 65)",
            "paragraph_wanted": False, "lines": ai_trade.ppi_lines(r),
            "data": {"ai_ppi": [{k: x[k] for k in ("key", "month", "yoy_pct")}
                                for x in r["rows"]]}}


def credit_gap_line() -> str:
    from altdata import ai_trade                                # noqa: PLC0415
    return " ".join(str(ai_trade.config().get("credit_watch_gap") or "").split())


# ---------------------------------------------------------------------------
# Placement
# ---------------------------------------------------------------------------
def place(subs: list[dict], ai_sub: Optional[dict], frag: Optional[dict]) -> list[dict]:
    """The proxy line right after the concentration twin (GTM-3), else after item
    31's concentration table, else at the end; the fragility panel at the end."""
    from . import gtm_block, t1_rest_block                      # noqa: PLC0415
    out = list(subs)
    if ai_sub:
        at = next((i for i, x in enumerate(out) if x.get("title") == gtm_block.TWIN_TITLE),
                  next((i for i, x in enumerate(out)
                        if x.get("title") == t1_rest_block.CONC_TITLE), None))
        out.insert(len(out) if at is None else at + 1, ai_sub)
    if frag:
        out.append(frag)
    return out


def mechanics_subsections(subs: list[dict], st, cutoff: str) -> list[dict]:
    """The Weekly's and the Monthly's Mechanics, with both items placed."""
    return place(subs, ai_proxy_subsection(st, cutoff), fragility_panel(st, None, cutoff))


def close_extras(built: dict, st, day: str, cutoff: str, screen: Optional[dict]) -> None:
    """The close: the attribution after item 52's block (or first), its Plumbing
    line, and the fragility panel; the attribution's event is kept in the
    section's data for the close to store (`_speed_event`)."""
    from altdata import speed_attribution as sa                  # noqa: PLC0415
    mech = built.get("mechanics")
    if mech is None:
        return
    ev = speed_event(st, day, cutoff, screen)
    if ev and ev.get("fired"):
        sub = sa.block(ev)
        subs = mech.setdefault("subsections", [])
        at = next((i for i, x in enumerate(subs) if x.get("title") == "Volatility event"),
                  None)
        subs.insert(0 if at is None else at + 1, sub)
        mech["items"].append(_item("mech:speed_attribution", ev["line"], 1, ev["line"]))
        if built.get("plumbing") is not None:
            built["plumbing"]["items"].append(
                _item("plumb:speed_attribution", ev["line"], 2, ev["line"]))
        mech.setdefault("data", {})["_speed_event"] = ev
    frag = fragility_panel(st, day, cutoff)
    if frag:
        mech.setdefault("subsections", []).append(frag)
