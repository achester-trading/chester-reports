"""
SR-37 -- THE AI FCF-TRANSFER PANEL (signal-triage batch 4, ST4-01).

    from altdata import ai_fcf
    r = ai_fcf.read(st, cutoff)           # the panel as knowable at the cutoff
    ai_fcf.lines(r); ai_fcf.table(r)      # what the Monthly's Mechanics prints

    python -m altdata.ai_fcf              # print the panel from the store

Config: config/ai_fcf.yaml (`fcf`).

THE CLAIM BEING WATCHED (the entry's source, BofA via a16z Growth, 30 Aug 2026):
hyperscaler 12-month-forward FCF fell from ~$275bn (2024) to ~-$25bn while the
semiconductor names' rose from ~$50bn to ~$420bn -- capex on one side is revenue
on the other.

WHAT IS BUILT, AND WHAT IT IS NOT. Forward consensus is not free, so this is the
TRAILING panel (batch-4 decision 2 as recommended), labelled trailing wherever it
prints:

  per name   the latest four consecutive reported quarters (fiscal calendars
             kept): TTM operating cash flow, TTM capex (as published, negative),
             TTM FCF = their sum; the TTM one quarter earlier where five
             quarters are stored
  per side   the five hyperscalers (AMZN GOOGL META MSFT ORCL) and the four
             semis (NVDA MU AVGO AMAT): the sums, ONLY when every name of the
             side has its TTM -- a partial sum prints "k of n" instead
  the ratio  the semis' TTM FCF over the hyperscalers', where the latter is
             positive; and the hyperscalers' capex as a share of their
             operating cash flow (the transfer's other face)
  the state  "hyperscaler aggregate FCF < 0", a defined threshold

Every input is read through ObservationStore.as_of(): nothing filed after the
cutoff is seen. Report-only (a modifier on Factor I's score); no trigger, no book
rule.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Optional

import yaml

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "ai_fcf.yaml"


def load_config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _key(ticker: str, field: str) -> str:
    from .sources import fundamentals                           # noqa: PLC0415
    return fundamentals.key(ticker, field)


def quarters(st, key: str, cutoff: Optional[str]) -> list[tuple[str, float]]:
    rows = {str(r["observed_at"])[:10]: float(r["value_num"])
            for r in st.as_of(key, cutoff) if r.get("value_num") is not None}
    return sorted(rows.items())


def _ttm(pts: dict, ends: list[str]) -> Optional[float]:
    return sum(pts[e] for e in ends) if all(e in pts for e in ends) else None


def _consecutive(ends: list[str], gap: int) -> bool:
    ds = [dt.date.fromisoformat(e) for e in ends]
    return all(0 < (b - a).days <= gap for a, b in zip(ds, ds[1:]))


def name_ttm(st, ticker: str, cutoff: Optional[str], cfg: dict) -> dict:
    gap = int((cfg.get("fcf") or {}).get("max_quarter_gap_days") or 100)
    ocf = dict(quarters(st, _key(ticker, "operating_cash_flow"), cutoff))
    cap = dict(quarters(st, _key(ticker, "capex"), cutoff))
    ends = sorted(set(ocf) & set(cap))
    out: dict[str, Any] = {"ticker": ticker, "quarters": len(ends), "fcf": None,
                           "ocf": None, "capex": None, "period_end": None,
                           "prior_fcf": None}
    if len(ends) < 4 or not _consecutive(ends[-4:], gap):
        out["reason"] = (f"{len(ends)} quarter(s) stored" if len(ends) < 4
                         else "a missing quarter in the latest four")
        return out
    last4 = ends[-4:]
    out.update({"ocf": _ttm(ocf, last4), "capex": _ttm(cap, last4),
                "period_end": last4[-1]})
    out["fcf"] = out["ocf"] + out["capex"]
    if len(ends) >= 5 and _consecutive(ends[-5:-1], gap):
        prev = ends[-5:-1]
        out["prior_fcf"] = _ttm(ocf, prev) + _ttm(cap, prev)
    return out


def side(names: list[dict]) -> dict:
    have = [n for n in names if n["fcf"] is not None]
    full = len(have) == len(names)
    s: dict[str, Any] = {"of": len(names), "covered": len(have),
                         "missing": [n["ticker"] for n in names if n["fcf"] is None]}
    s["fcf"] = sum(n["fcf"] for n in have) if full else None
    s["ocf"] = sum(n["ocf"] for n in have) if full else None
    s["capex"] = sum(n["capex"] for n in have) if full else None
    s["prior_fcf"] = (sum(n["prior_fcf"] for n in have)
                      if full and all(n["prior_fcf"] is not None for n in have)
                      else None)
    s["change"] = (None if s["fcf"] is None or s["prior_fcf"] is None
                   else s["fcf"] - s["prior_fcf"])
    s["capex_to_ocf"] = (abs(s["capex"]) / s["ocf"] if s["ocf"] else None) \
        if full else None
    s["latest_quarter"] = max((n["period_end"] for n in have), default=None)
    return s


def read(st, cutoff: Optional[str] = None, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or load_config()
    f = cfg.get("fcf") or {}
    hs = [{**name_ttm(st, t, cutoff, cfg), "side": "hyperscaler"}
          for t in f.get("hyperscalers") or []]
    se = [{**name_ttm(st, t, cutoff, cfg), "side": "semiconductor"}
          for t in f.get("semis") or []]
    h, s = side(hs), side(se)
    thr = float(f.get("threshold_usd") or 0)
    ratio = (s["fcf"] / h["fcf"]) if (h["fcf"] and h["fcf"] > 0
                                      and s["fcf"] is not None) else None
    state = None if h["fcf"] is None else h["fcf"] < thr
    return {"names": hs + se, "hyperscalers": h, "semis": s, "ratio": ratio,
            "below_zero": state, "tag": cfg.get("tag") or "",
            "forward_source": f.get("forward_source"),
            "config_version": cfg.get("version")}


def bn(x: Optional[float], signed: bool = False) -> str:
    if x is None:
        return "—"
    v = x / 1e9
    s = f"{abs(v):,.1f}"
    sign = "−" if v < 0 else ("+" if signed and v > 0 else "")
    return f"{sign}${s}bn"


def _side_line(label: str, s: dict) -> str:
    if s["fcf"] is None:
        return (f"{label}: {s['covered']} of {s['of']} carry four reported quarters "
                f"(missing {', '.join(s['missing'])}); no aggregate")
    out = (f"{label}: TTM free cash flow {bn(s['fcf'])} (operating cash flow "
           f"{bn(s['ocf'])}, capex {bn(s['capex'])}")
    if s["capex_to_ocf"] is not None:
        out += f"; capex {100 * s['capex_to_ocf']:.0f}% of operating cash flow"
    out += ")"
    if s["change"] is not None:
        out += f", {bn(s['change'], signed=True)} on the prior quarter's TTM"
    return out


def lines(r: dict) -> list[str]:
    h, s, tag = r["hyperscalers"], r["semis"], r["tag"]
    out = [_side_line("The five hyperscalers", h) + ".",
           _side_line("The four semiconductor names", s) + "."]
    if r["ratio"] is not None:
        out.append(f"The semis' TTM free cash flow is {r['ratio']:.2f}× the "
                   f"hyperscalers'.")
    elif h["fcf"] is not None and s["fcf"] is not None:
        out.append("The ratio is not defined: the hyperscalers' TTM free cash flow "
                   "is at or below zero.")
    if r["below_zero"] is None:
        out.append(f"Hyperscaler aggregate free cash flow below zero: not read "
                   f"(the aggregate needs all five) {tag}.")
    else:
        out.append(f"Hyperscaler aggregate free cash flow below zero: "
                   f"{'yes' if r['below_zero'] else 'no'} {tag}.")
    out.append(f"Trailing, from the quarterly filings; the source chart's forward "
               f"series is not available ({r['forward_source']}).")
    return tagged(out, tag)


def tagged(lines_: list[str], tag: str) -> list[str]:
    """Every printed line carries the tag, once."""
    return [ln if not tag or tag in ln else ln.rstrip(".") + f" {tag}."
            for ln in lines_]


def table(r: dict) -> dict:
    rows = [[n["ticker"], n["side"], n["period_end"] or n.get("reason") or "—",
             bn(n["ocf"]), bn(n["capex"]), bn(n["fcf"])] for n in r["names"]]
    return {"columns": ["Name", "Side", "Latest quarter", "TTM operating cash flow",
                        "TTM capex", "TTM free cash flow"], "rows": rows}


def data(r: dict) -> dict:
    """The printed figures, for the section's frame."""
    h, s = r["hyperscalers"], r["semis"]
    return {"hyperscaler_fcf": bn(h["fcf"]), "semis_fcf": bn(s["fcf"]),
            "hyperscaler_capex_to_ocf_pct": (None if h["capex_to_ocf"] is None
                                             else round(100 * h["capex_to_ocf"])),
            "ratio": None if r["ratio"] is None else round(r["ratio"], 2),
            "hyperscaler_fcf_below_zero": r["below_zero"], "basis": "trailing",
            "tag": r["tag"]}


def _main() -> int:
    from . import observations                                  # noqa: PLC0415
    with observations.ObservationStore() as st:
        r = read(st)
    for ln in lines(r):
        print(ln.encode("ascii", "replace").decode())
    return 0


if __name__ == "__main__":                                      # pragma: no cover
    raise SystemExit(_main())
