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

The rows ride `python -m altdata.surprise compute` (the same step, the same
writer), so no writer is added to the roster. Engine 4 (alpha/event_rates.py)
reads calc.consensus_surprise.<id> by name ahead of the naive surprise.
"""

from __future__ import annotations

import statistics
from typing import Any, Optional

from . import derived, observations
from .releases import config, mm

PREFIX = "calc.consensus_surprise."
Z_PREFIX = "calc.consensus_surprise_z."
EARNINGS_SOURCE = "calc.earnings_surprise_pct"
EARNINGS_Z = Z_PREFIX + "earnings"


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
        return dict(base, state="no consensus", reason=si["gap"], rows=[])
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


def index(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """Every release's surprises at the cutoff; no composite (the order defines
    none)."""
    cfg = cfg or config()
    return {"as_of": cutoff, "composite": None,
            "composite_reason": "the order defines no composite surprise index",
            "macro": [macro_series(st, rel, cutoff, cfg)
                      for rel in cfg["surprise_index"]["macro"]],
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


def note(sur: dict) -> str:
    """The release-day line's surprise clause: the surprise and its percentile
    among the release's own earlier surprises, or the reason there is none."""
    if sur.get("state") != "read":
        return "surprise: no consensus"
    p = sur.get("pctile")
    pct = (f", {derived._ord(p)} percentile of its surprises (n={sur['n_prior']})"
           if p is not None else f" ({sur.get('reason')})")
    return f"surprise: {sur['surprise']:+.2f} {sur['units']} against consensus{pct}"


def rows(st, as_of: Optional[str] = None, cfg: Optional[dict] = None) -> list[dict]:
    """The stored rows, for altdata.surprise.compute: the macro surprises in own
    units and standardised, and the earnings surprises standardised."""
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
