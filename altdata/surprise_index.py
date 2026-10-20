"""
THE SURPRISE INDEX (Batch 7 item 48, lens 23: ST-R6.48f; lenses-group-b, 18 Oct
2026, session B). Config: config/releases.yaml `surprise_index:`.

For every release a consensus is stored for: the actual less the consensus, in
the release's own units, and that surprise STANDARDISED BY THE RELEASE'S OWN
HISTORY of surprises -- over the standard deviation of its earlier surprises
(the latest `window`, at least `min_prior` of them), with its percentile among
them. THE ORDER DEFINES NO COMPOSITE, so none is built: each release prints its
own surprise and nothing is summed, weighted or averaged across releases.

THE SOURCE IS THE CONSENSUS LOGGER'S (ruled 18 Oct 2026). Its library, yfinance
as pinned, serves the analyst mean before each earnings print and no consensus
for a macro release, so:

  earnings   the reported EPS against the analyst mean, as the earnings writer
             stored it (calc.earnings_surprise_pct, per name, percent of the
             estimate), standardised by the NAME'S own earlier surprises:
             calc.consensus_surprise_z.earnings, one row per name and report
  macro      read BY KEY NAME from `consensus.<id>` (config `macro:`). None is
             stored, so each prints "no consensus" with the reason -- the payroll
             and FOMC surprises among them, listed as gaps under ruling 5 of
             18 Oct. When a source writes `consensus.<id>`, its rows are
             calc.consensus_surprise.<id> (own units) and
             calc.consensus_surprise_z.<id>, with no code change.

POINT IN TIME. A macro surprise's actual is the release's FIRST print, read as of
that print's availability, and the row's available_at is the later of the print
and the consensus; an earnings row inherits the stored surprise's. A
standardisation reads only surprises knowable before the one it scores.

THE FOMC SURPRISE IS MARKET-IMPLIED, NOT A SURVEY CONSENSUS (ruling 1 of 18 Oct
2026, on the lenses-group-b report). For each decision day the store can see: the
decision (the change in the target range's midpoint, in bp) less the change the
fed funds futures implied for that meeting at the prior session's close (the
newest settlement observed before the decision day and available before the
14:00 decision, through altdata.fed_funds.implied_path), standardised as above.
It lives under its own keys, calc.market_implied_surprise.fomc and _z.fomc, so no
survey consensus is ever mixed with it; consensus.fomc stays a gap. Payrolls stay
a gap, the key named.

The rows ride `python -m altdata.surprise compute` (the same step, the same
writer), so no writer is added to the roster. Engine 4 (alpha/event_rates.py)
reads calc.consensus_surprise.<id> by name ahead of the naive surprise; for FOMC
its fallback is the market-implied key, under its own label.
"""

from __future__ import annotations

import datetime as dt
import statistics
from typing import Any, Optional

from . import derived, observations
from .releases import config, mm

PREFIX = "calc.consensus_surprise."
Z_PREFIX = "calc.consensus_surprise_z."
EARNINGS_SOURCE = "calc.earnings_surprise_pct"
EARNINGS_Z = Z_PREFIX + "earnings"
MI_PREFIX = "calc.market_implied_surprise."
MI_Z_PREFIX = "calc.market_implied_surprise_z."
MARKET_IMPLIED = "market-implied, not a survey consensus"
# Ruling 3 of 18 Oct 2026: the first z an edition prints says what it is against.
Z_AGAINST = "against the release's own surprise history"


def surprise_key(rid: str) -> str:
    return PREFIX + rid


def z_key(rid: str) -> str:
    return Z_PREFIX + rid


def standardise(prior: list[float], x: float, min_prior: int, window: int) -> dict:
    """x against the release's earlier surprises: z over their standard deviation
    and the percentile among them, each with its n; None below min_prior."""
    xs = prior[-window:]
    out: dict[str, Any] = {"n_prior": len(xs)}
    if len(xs) < min_prior:
        out.update(z=None, pctile=None,
                   reason=f"{len(xs)} earlier surprise(s); {min_prior} needed")
        return out
    sd = statistics.stdev(xs)
    out["z"] = round(x / sd, 4) if sd > 0 else None
    out["pctile"] = derived.percentile_of(xs, x)
    out["sd"] = round(sd, 6)
    if sd <= 0:
        out["reason"] = "the earlier surprises do not vary"
    return out


def _actual_at(st, rel: dict, observed_at: str, at: str) -> Optional[float]:
    """The release's figure for one period as printed at `at` (its first print)."""
    rows = st.as_of(rel["actual"], at)
    s = {str(x["observed_at"])[:7]: float(x["value_num"]) for x in rows
         if x.get("value_num") is not None}
    m = str(observed_at)[:7]
    if m not in s:
        return None
    t = rel.get("transform", "level")
    if t == "level":
        return s[m]
    if t == "mm_pct":
        return mm(s, m)
    if t == "change":
        from .releases import shift                             # noqa: PLC0415
        p = s.get(shift(m, -1))
        return None if p is None else s[m] - p
    raise ValueError(f"unknown transform {t!r} for {rel['id']}")


def macro_series(st, rel: dict, cutoff: str, cfg: dict) -> dict:
    """One macro release's consensus surprises knowable at the cutoff."""
    si = cfg["surprise_index"]
    base = {"id": rel["id"], "name": rel["name"], "units": rel["units"],
            "consensus_key": rel["consensus"]}
    cons = st.as_of(rel["consensus"], cutoff)
    if not cons or not rel.get("actual"):
        return dict(base, state="no consensus",
                    reason=f"{si['gap']} (key {rel['consensus']})", rows=[])
    cut = observations.canonical_instant(cutoff)
    out, prior = [], []
    for c in cons:
        if c.get("value_num") is None:
            continue
        first = next((v for v in st.vintages(rel["actual"], c["observed_at"])
                      if v.get("value_num") is not None
                      and str(v["available_at"]) <= cut), None)
        if first is None:
            continue
        actual = _actual_at(st, rel, c["observed_at"], str(first["available_at"]))
        if actual is None:
            continue
        x = actual - float(c["value_num"])
        z = standardise(prior, x, int(si["min_prior"]), int(si["window"]))
        out.append({"observed_at": str(c["observed_at"])[:10], "actual": round(actual, 6),
                    "consensus": float(c["value_num"]), "surprise": round(x, 6),
                    "available_at": max(str(first["available_at"]), str(c["available_at"])),
                    **z})
        prior.append(x)
    return dict(base, state="read" if out else "no consensus",
                reason=None if out else "no period has both a consensus and a print",
                rows=out)


def _midpoint(st, keys: list[str], cutoff: str) -> dict[str, tuple[float, str]]:
    """{day: (target midpoint %, available_at)} as of the cutoff, from the range's
    upper and lower limits; a day needs both."""
    legs = []
    for k in keys:
        legs.append({str(x["observed_at"])[:10]: (float(x["value_num"]), str(x["available_at"]))
                     for x in st.as_of(k, cutoff) if x.get("value_num") is not None})
    days = set(legs[0]).intersection(*legs[1:])
    return {d: (sum(leg[d][0] for leg in legs) / len(legs),
                max(leg[d][1] for leg in legs)) for d in days}


def _decision_instant(day: dt.date, at: str) -> str:
    """The decision's instant in UTC: `at` (HH:MM, Eastern) on the day."""
    from . import session                                       # noqa: PLC0415
    hh, mm_ = (int(x) for x in at.split(":"))
    t = dt.datetime.combine(day, dt.time(hh, mm_), tzinfo=session._eastern_tz())
    return observations.canonical_instant(t.astimezone(dt.timezone.utc).isoformat())


def implied_before(st, md: dt.date, meetings: list[dt.date], at: str) -> Optional[dict]:
    """The change the futures implied for the meeting on `md` at the prior
    session's close: each contract's newest settlement observed before `md` and
    available before the decision. None when the path cannot reach the meeting."""
    from . import fed_funds                                     # noqa: PLC0415
    inst = _decision_instant(md, at)
    prices, seen = {}, None
    for c in st.instruments(fed_funds.KEY):
        rs = [x for x in st.as_of(fed_funds.KEY, inst, instrument=c)
              if x.get("value_num") is not None and str(x["observed_at"])[:10] < md.isoformat()]
        if rs:
            prices[c] = float(rs[-1]["value_num"])
            seen = max(seen or "", str(rs[-1]["observed_at"])[:10])
    p = fed_funds.implied_path(prices, meetings, md, n_meetings=1)["meetings"]
    if not p or p[0]["meeting"] != md.isoformat():
        return None
    return {"implied_bp": p[0]["change_bp"], "settled": seen}


def market_implied_series(st, cutoff: str, cfg: dict,
                          meetings: Optional[list[dt.date]] = None) -> dict:
    """The FOMC surprise, market-implied (ruling 1 of 18 Oct 2026): each decision
    the store can see at the cutoff, the decision's bp less the futures' implied
    bp at the prior session's close, standardised by the earlier ones."""
    si = cfg["surprise_index"]
    mi = si["market_implied"]
    base = {"id": mi["id"], "name": mi["name"], "units": "bp", "label": MARKET_IMPLIED}
    if meetings is None:
        from . import fed_funds                                 # noqa: PLC0415
        meetings = fed_funds.meeting_days()
    meetings = sorted(meetings)
    mid = _midpoint(st, mi["target"], cutoff)
    days = sorted(mid)
    out, prior, why = [], [], []
    cut_day = observations.canonical_instant(cutoff)[:10]
    for md in meetings:
        if md.isoformat() > cut_day:
            break
        pre = [d for d in days if d < md.isoformat()]
        horizon = (md + dt.timedelta(days=int(mi.get("effective_within_days", 5)))).isoformat()
        post = [d for d in days if md.isoformat() < d <= horizon]
        if not pre or not post:
            why.append(f"{md}: the target range is not stored on both sides of the decision")
            continue
        imp = implied_before(st, md, meetings, mi.get("decision_time", "14:00"))
        if imp is None:
            why.append(f"{md}: the stored futures do not reach the meeting")
            continue
        decision = derived.rate_bp_change(mid[post[-1]][0], mid[pre[-1]][0])
        x = round(decision - imp["implied_bp"], 2)
        z = standardise(prior, x, int(si["min_prior"]), int(si["window"]))
        out.append({"observed_at": md.isoformat(), "decision_bp": decision,
                    "implied_bp": imp["implied_bp"], "settled": imp["settled"],
                    "surprise": x, "available_at": mid[post[-1]][1], **z})
        prior.append(x)
    return dict(base, state="read" if out else "no surprise",
                reason=None if out else ("; ".join(why) or "no decision day at the cutoff"),
                skipped=why, rows=out)


def earnings_series(st, cutoff: str, cfg: dict) -> dict[str, list[dict]]:
    """{symbol: [rows]}: each stored earnings surprise, standardised by the
    name's own earlier ones."""
    si = cfg["surprise_index"]
    out: dict[str, list[dict]] = {}
    for sym in st.instruments(EARNINGS_SOURCE):
        prior, rows = [], []
        for x in st.as_of(EARNINGS_SOURCE, cutoff, instrument=sym):
            if x.get("value_num") is None:
                continue
            v = float(x["value_num"])
            rows.append({"observed_at": str(x["observed_at"])[:10], "surprise_pct": v,
                         "available_at": str(x["available_at"]),
                         **standardise(prior, v, int(si["min_prior"]), int(si["window"]))})
            prior.append(v)
        if rows:
            out[sym] = rows
    return out


def index(st, cutoff: str, cfg: Optional[dict] = None,
          meetings: Optional[list[dt.date]] = None) -> dict:
    """Every release's surprises at the cutoff; no composite (the order defines
    none). The market-implied FOMC surprise sits apart from the consensus ones."""
    cfg = cfg or config()
    return {"as_of": cutoff, "composite": None,
            "composite_reason": "the order defines no composite surprise index",
            "macro": [macro_series(st, rel, cutoff, cfg)
                      for rel in cfg["surprise_index"]["macro"]],
            "market_implied": market_implied_series(st, cutoff, cfg, meetings),
            "earnings": earnings_series(st, cutoff, cfg)}


def latest(st, rid: str, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """The newest surprise of one macro release, for the release-day line."""
    cfg = cfg or config()
    rel = next((x for x in cfg["surprise_index"]["macro"] if x["id"] == rid), None)
    if rel is None:
        return {"state": "no consensus",
                "reason": f"{rid} is not in the surprise index's releases"}
    s = macro_series(st, rel, cutoff, cfg)
    if not s["rows"]:
        return {"state": s["state"], "reason": s["reason"]}
    return dict(s["rows"][-1], state="read", units=rel["units"])


def z_clause(sur: dict, first_z: bool = True) -> str:
    """", z +1.23" and, the first time an edition prints one, what it is
    against (ruling 3 of 18 Oct 2026); empty without a z."""
    z = sur.get("z")
    if z is None:
        return ""
    return f", z {z:+.2f}" + (f" {Z_AGAINST}" if first_z else "")


def note(sur: dict, first_z: bool = True) -> str:
    """The release-day line's surprise clause: the surprise and its percentile
    among the release's own earlier surprises, then its z, or the reason there
    is none."""
    if sur.get("state") != "read":
        return "surprise: no consensus"
    p = sur.get("pctile")
    pct = (f", {derived._ord(p)} percentile of its surprises (n={sur['n_prior']})"
           if p is not None else f" ({sur.get('reason')})")
    return (f"surprise: {sur['surprise']:+.2f} {sur['units']} against consensus{pct}"
            f"{z_clause(sur, first_z)}")


def market_note(sur: dict, first_z: bool = True) -> str:
    """The FOMC surprise's clause, labelled market-implied wherever it prints."""
    if sur.get("state") != "read":
        return f"surprise ({MARKET_IMPLIED}): not available ({sur.get('reason')})"
    p = sur.get("pctile")
    pct = (f", {derived._ord(p)} percentile of its surprises (n={sur['n_prior']})"
           if p is not None else f" ({sur.get('reason')})")
    return (f"surprise: {sur['surprise']:+.0f} bp, {MARKET_IMPLIED} (the decision "
            f"{sur['decision_bp']:+.0f} bp less the {sur['implied_bp']:+.0f} bp fed funds "
            f"futures implied at the prior session's close){pct}{z_clause(sur, first_z)}")


def latest_market_implied(st, cutoff: str, cfg: Optional[dict] = None,
                          meetings: Optional[list[dt.date]] = None) -> dict:
    """The newest market-implied FOMC surprise at the cutoff."""
    cfg = cfg or config()
    s = market_implied_series(st, cutoff, cfg, meetings)
    if not s["rows"]:
        return {"state": s["state"], "reason": s["reason"]}
    return dict(s["rows"][-1], state="read", units="bp")


def rows(st, as_of: Optional[str] = None, cfg: Optional[dict] = None,
         meetings: Optional[list[dt.date]] = None) -> list[dict]:
    """The stored rows, for altdata.surprise.compute: the macro surprises in own
    units and standardised, the market-implied FOMC surprise under its own keys,
    and the earnings surprises standardised."""
    from . import session                                       # noqa: PLC0415
    cutoff = as_of or session.utc_iso(timespec="microseconds")
    cfg = cfg or config()
    out = []
    for rel in cfg["surprise_index"]["macro"]:
        for x in macro_series(st, rel, cutoff, cfg)["rows"]:
            common = {"instrument": None, "observed_at": x["observed_at"],
                      "available_at": x["available_at"], "source": "calc",
                      "availability_kind": "ingest_instant"}
            out.append(dict(common, registry_key=surprise_key(rel["id"]),
                            value=x["surprise"]))
            if x.get("z") is not None:
                out.append(dict(common, registry_key=z_key(rel["id"]), value=x["z"]))
    mid = cfg["surprise_index"]["market_implied"]["id"]
    for x in market_implied_series(st, cutoff, cfg, meetings)["rows"]:
        common = {"instrument": None, "observed_at": x["observed_at"],
                  "available_at": x["available_at"], "source": "calc",
                  "availability_kind": "ingest_instant"}
        out.append(dict(common, registry_key=MI_PREFIX + mid, value=x["surprise"]))
        if x.get("z") is not None:
            out.append(dict(common, registry_key=MI_Z_PREFIX + mid, value=x["z"]))
    for sym, xs in earnings_series(st, cutoff, cfg).items():
        for x in xs:
            if x.get("z") is None:
                continue
            out.append({"registry_key": EARNINGS_Z, "instrument": sym,
                        "observed_at": x["observed_at"], "available_at": x["available_at"],
                        "value": x["z"], "source": "calc",
                        "availability_kind": "ingest_instant"})
    return out


def _main(argv: list[str]) -> int:
    """`show`: the index at the cutoff, as JSON. Reads only."""
    import argparse
    import json

    from . import session
    ap = argparse.ArgumentParser(prog="python -m altdata.surprise_index")
    ap.add_argument("cmd", choices=["show"])
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--db", default=None)
    a = ap.parse_args(argv)
    cutoff = a.as_of or session.utc_iso(timespec="microseconds")
    with observations.ObservationStore(a.db) as st:
        print(json.dumps(index(st, cutoff), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_main(sys.argv[1:]))
