"""
Signal-triage Batch 12, item 60.1-60.3 (ST-R6.60a/b; F3): implied forward growth,
the realised forecast error and the estimates-overshoot flag -- both of F3's
branches, the source named in config/eps_overshoot.yaml.

    from altdata import eps_overshoot as eo
    r = eo.read(st, cutoff, revisions_flag="on")
    eo.lines(r)

F3. S&P DJI's estimates file was withdrawn on 17 Oct (`spdji` retired), so the
forward-EPS legs have no stored source. The session probes Yardeni's public series
first; if it reads keylessly and simply, both series, the flag and the ledger are
built from it, labelled with the source; if not, both are listed gaps and the flag
does not print. The probe of 20 Oct 2026 failed the standing rule on sources (its
charts read from /api, which its robots.txt disallows, and its copyright clause
forbids any download or reuse without written consent), so `source` is null and
every reading here is the gap branch. The other branch is written and held by the
gate on a fixture, so the day a keyless source with vintages is named in config it
prints without a new build:

  implied forward growth   forward EPS (pushed 52 weeks ahead) over trailing actual
                           EPS, less 1, percent, with dual percentiles (five years
                           and the full stored history)
  realised forecast error  actual trailing EPS now against the forward EPS stored a
                           year earlier, percent, quarterly
  the flag                 the realised error negative while item 29's
                           revisions-turn flag is on

Report-only: a flag, no score, no composite.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Optional

from . import st_r5_rates as rt

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "eps_overshoot.yaml"
GAP = ("Implied forward growth and the realised forecast error: listed gaps (item 60, "
       "F3: no keyless forward-EPS source with vintages); the estimates-overshoot flag "
       "does not print.")
# Batch 14 item 67 (written as 60; F3, b55): PEG and LTEG have no keyless source,
# so neither prints; the chain carries this one listed-gap line wherever it prints.
# The note is docs/base-rate-notes/lteg-overshoot-2026-10.md.
PEG_GAP = "PEG and long-term growth: no keyless source; see the LTEG overshoot note."


def config(path: Optional[Path] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load((path or CONFIG).read_text(encoding="utf-8")) or {}


def _year_ago(day: str) -> str:
    d = dt.date.fromisoformat(day)
    try:
        return d.replace(year=d.year - 1).isoformat()
    except ValueError:
        return d.replace(year=d.year - 1, day=28).isoformat()


def implied_growth(fwd: list, trl: list) -> list[tuple[str, float]]:
    """(day, percent) where both are stored, trailing carried forward."""
    out, td = [], dict(trl)
    days = sorted(td)
    for d, f in fwd:
        prior = [x for x in days if x <= d]
        if prior and td[prior[-1]]:
            out.append((d, round((f / td[prior[-1]] - 1) * 100.0, 2)))
    return out


def forecast_error(fwd: list, trl: list) -> Optional[dict]:
    """The latest trailing actual against the forward stored a year earlier."""
    if not trl or not fwd:
        return None
    d, actual = trl[-1]
    then = [x for x in fwd if x[0] <= _year_ago(d)]
    if not then:
        return None
    return {"day": d, "forecast_day": then[-1][0], "forecast": then[-1][1],
            "actual": actual, "error_pct": round((actual / then[-1][1] - 1) * 100.0, 2)}


def read(st, cutoff: str, revisions_flag: Optional[str] = None,
         cfg: Optional[dict] = None) -> dict:
    cfg = cfg if cfg is not None else config()
    src = cfg.get("source")
    if not src:
        return {"state": "gap", "reason": cfg.get("gap_reason") or GAP, "flag": None}
    fwd = rt._pts(st, cfg["forward_eps_key"], cutoff)           # noqa: SLF001
    trl = rt._pts(st, cfg["trailing_eps_key"], cutoff)          # noqa: SLF001
    ig = implied_growth(fwd, trl)
    err = forecast_error(fwd, trl)
    flag = (None if err is None or revisions_flag in (None, "absent")
            else bool(err["error_pct"] < 0 and revisions_flag == "on"))
    return {"state": "ok" if ig else "absent", "source": src,
            "implied_growth": ig[-1] if ig else None,
            "lens": rt.lens(ig, int(cfg.get("lens_years", 5))) if ig else None,
            "error": err, "flag": flag}


def lines(r: dict) -> list[str]:
    return _lines(r) + [PEG_GAP]


def _lines(r: dict) -> list[str]:
    if r["state"] == "gap":
        return [r["reason"]]
    if r["state"] == "absent":
        return [f"Implied forward growth: not yet stored ({r['source']})."]
    d, g = r["implied_growth"]
    out = [f"Implied forward growth {g:+.1f}% ({d}; {rt.lens_text(r['lens'])}; "
           f"{r['source']})."]
    e = r["error"]
    out.append("Realised forecast error: not yet a year of forecasts stored."
               if e is None else
               f"Realised forecast error {e['error_pct']:+.1f}%: trailing EPS {e['actual']:.2f} "
               f"({e['day']}) against the forward {e['forecast']:.2f} stored "
               f"{e['forecast_day']} ({r['source']}).")
    if r["flag"] is True:
        out.append("Estimates-overshoot flag ON: the realised error is negative while "
                   "the revisions-turn flag is on. Descriptive, unvalidated.")
    elif r["flag"] is False:
        out.append("Estimates-overshoot flag off.")
    return out
