"""
The Monthly's style-regime panel -- SR-1 (signal-triage ST-8; st-t3-calib,
18 Oct 2026), rendered because SR-1's gate passed
(docs/ledgers/sr-1-ledger-2026-10-18.md) and for no other item.

    subsection(st, now)    the Slow layers sub-section (lines only)

Reads the store as of the cutoff and fetches nothing: the growth and value ETFs'
closes and the distributions stored beside them (yfinance.mkt_<sym> and
yfinance.mkt_<sym>_dividend), through altdata/style_regime.py's one definition of
the rule, at config/style_regime.yaml's admitted thresholds. A pair whose closes
are not stored prints NOT AVAILABLE with its keys.

WHAT IT DISPLACES: nothing. It is lines only and asks no paragraph, so it adds no
word to the Monthly's 10,000-word budget and no chart to its cap; it sits after
the Factor lines in Slow layers.

NO FLAG WORD. The register's narrow flag ("Style regime -- growth extreme /
rotation triggered") is a right the gate's acceptance grants, and the gate status
is a rule-31 draft until the operator accepts it; so the panel prints the
readings, says whether a setup is live and whether this week breaks, and prints
no flag. SR-13's spread line, which the order rides on this panel, does not
render: its gate is INSUFFICIENT (docs/ledgers/sr-13-ledger-2026-10-18.md).
"""

from __future__ import annotations

import logging
from typing import Optional

log = logging.getLogger(__name__)

TITLE = "Style regime (SR-1)"
NA = "NOT AVAILABLE"
SR13_LINE = ("SR-13's tech/defensives spread: not rendered (its gate is INSUFFICIENT, "
             "docs/ledgers/sr-13-ledger-2026-10-18.md)")


def _closes(st, key: str, now: str) -> list[tuple[str, float]]:
    from altdata.absorption import series                       # noqa: PLC0415
    return [(d, v) for d, v, _ in series(st, key, now)]


def pair_line(st, now: str, growth: str, value: str, cfg: dict) -> str:
    from altdata import style_regime as SR                      # noqa: PLC0415
    keys = [f"yfinance.mkt_{s.lower()}" for s in (growth, value)]
    label = f"{growth}/{value} (growth over value, total return)"
    try:
        legs = []
        for k in keys:
            px = _closes(st, k, now)
            div = dict(_closes(st, k + "_dividend", now))
            legs.append(SR.total_return(px, div) if px else [])
        s = SR.weekly_state(legs[0], legs[1], cfg) if all(legs) else None
    except Exception:                                           # noqa: BLE001
        log.warning("style regime %s faulted", label, exc_info=True)
        s = None
    if s is None:
        return f"{label}: {NA} ({' and '.join(keys)}; Yahoo closes and distributions)"
    z = f"{s['z']:+.2f}" if s["z"] is not None else "n/a"
    return (f"{label}: z against its 10-year trend {z}; {s['off_high_pct']:.1f}% off its "
            f"52-week high; {s['vs_ma_pct']:+.1f}% against its 40-week mean (as of "
            f"{s['day']}); setup live (z above +{cfg['rule']['z_arm']:g} in the last "
            f"{cfg['rule']['arm_weeks']} weeks): {'yes' if s['setup_live'] else 'no'}; "
            f"this week a break while armed: {'yes' if s['break_now'] else 'no'}"
            + (f"; last trigger {s['last_trigger']}" if s["last_trigger"] else ""))


def lines(st, now: str) -> list[str]:
    from altdata import style_regime as SR                      # noqa: PLC0415
    cfg = SR.config()
    out = [f"Thresholds admitted by {cfg['admitted_by']} ({cfg['admitted_verdict']}, "
           f"{cfg['edition']}); display only, no flag word until the operator accepts "
           f"the gate status (rule 31)."]
    out += ["  " + pair_line(st, now, g, v, cfg) for g, v in cfg["pairs"]]
    out.append("  " + SR13_LINE)
    return out


def subsection(st, now: Optional[str]) -> dict:
    return {"title": TITLE, "lines": lines(st, now), "paragraph_wanted": False,
            "not_tracked": [],
            "table_note": ("Lines read from the store as of the cutoff; nothing fetched. "
                           "Lines only: no words of the budget and no chart, so it "
                           "displaces nothing (signal-triage ST-8)."),
            "data": {"lines": None, "cap": None}}
