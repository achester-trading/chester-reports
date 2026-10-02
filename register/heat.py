"""
The heat/factor view across the books, and the order gate at entry that reads it.

    from register import heat
    v = heat.view(decisions, store=store)            # what the open book sums to
    g = heat.gate(candidate, decisions, store=store) # approve / resize / ... / reject

Phase 5 (Audit #3 §N: "heat/factor view"), made cross-book by EL-2
(docs/change-order-enterprise-layer-2026-09-27.md §3.2).

-----------------------------------------------------------------------------
WHY CROSS-BOOK
-----------------------------------------------------------------------------
Four sensible packets can be one trade: long NVDA in the tactical book, long QQQ in
the swing book, long NVDA again in the allocation book, and short Nasdaq volatility
in options. Each passes its own book's rules. Summed, they are a technology and a
vega concentration no single packet shows. The Doctrine names the same failure --
"four books, one trade, and a very bad day" -- and caps net beta across books for
it. This module sums every open decision across Books A-D and every options
expression and names what the sum is concentrated in.

-----------------------------------------------------------------------------
WHAT IS SUMMED, AND WHERE EACH NUMBER COMES FROM
-----------------------------------------------------------------------------
    beta-adjusted notional   notional x beta vs SPY, signed by direction. Beta is
                             COMPUTED from stored daily closes (yfinance.mkt_*),
                             one year of returns; a name the store does not carry
                             has no beta and the gate DELAYS rather than assume.
    sector                   notional x declared look-through weights
                             (config/instrument_reference.yaml).
    duration                 notional x declared duration / 100: dollars per 100bp.
    vega                     the decision's own vega_usd, dollars per vol point,
                             signed (negative when short volatility).

The limits are in config/risk_limits.yaml with their provenance. The net-beta cap
is the Doctrine's: the top of Book A's band plus 15 points. The band comes from
the Macro dial through a declared mapping, with the Doctrine's crossing rule.

Reads only. The view and the gate compute nothing that is written except by the
caller (tools/decide.py record), which stores the gate's outcome on the decision.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parent.parent
LIMITS_PATH = REPO / "config" / "risk_limits.yaml"
REFERENCE_PATH = REPO / "config" / "instrument_reference.yaml"

# Options families: an expression whose vega is part of the decision.
from register.store import EXPRESSION_FAMILIES, GATE_OUTCOMES  # noqa: E402

OPTION_FAMILIES = tuple(f for f in EXPRESSION_FAMILIES if f not in (
    "outright", "buffered_fund", "synthetic_ppn"))
BETA_WINDOW = 252
BETA_MIN_OBS = 60
# Below this share of the candidate's size a resize is not a trade any more.
MIN_RESIZE_FACTOR = 0.25


def _yaml(path: Path) -> dict:
    import yaml  # noqa: PLC0415
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_limits(path: Optional[Path] = None) -> dict:
    return _yaml(path or LIMITS_PATH)


def load_reference(path: Optional[Path] = None) -> dict:
    return _yaml(path or REFERENCE_PATH)


# ---------------------------------------------------------------------------
# Beta, from the store
# ---------------------------------------------------------------------------
def _price_key(root: str) -> Optional[str]:
    from altdata.sources import yfinance_source as yf  # noqa: PLC0415
    k = yf.SYMBOLS.get(root)
    return f"yfinance.{k}" if k else None


def _closes(store: Any, key: str, as_of: Optional[str]) -> dict[str, float]:
    out = {}
    for r in store.as_of(key, as_of=as_of):
        v = r.get("value_num")
        if v is not None:
            out[str(r["observed_at"])[:10]] = float(v)
    return out


def beta_vs_spy(root: str, store: Any, as_of: Optional[str] = None,
                window: int = BETA_WINDOW) -> dict:
    """{beta, n, reason}: OLS slope of daily returns on SPY's, last `window`."""
    if root == "SPY":
        return {"beta": 1.0, "n": None, "reason": "the benchmark itself"}
    key = _price_key(root)
    if not key:
        return {"beta": None, "n": 0,
                "reason": f"{root} is not in the price basket "
                          f"(altdata/sources/yfinance_source.py SYMBOLS)"}
    a = _closes(store, key, as_of)
    b = _closes(store, "yfinance.mkt_spy", as_of)
    days = sorted(set(a) & set(b))[-(window + 1):]
    ra, rb = [], []
    for d0, d1 in zip(days, days[1:]):
        if a[d0] and b[d0]:
            ra.append(a[d1] / a[d0] - 1.0)
            rb.append(b[d1] / b[d0] - 1.0)
    if len(ra) < BETA_MIN_OBS:
        return {"beta": None, "n": len(ra),
                "reason": f"{len(ra)} paired daily returns for {root} and SPY "
                          f"in the store, {BETA_MIN_OBS} needed -- backfill "
                          f"{key}"}
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    var = sum((y - mb) ** 2 for y in rb)
    if var == 0:
        return {"beta": None, "n": len(ra), "reason": "SPY returns do not vary"}
    return {"beta": round(cov / var, 4), "n": len(ra), "reason": None}


# ---------------------------------------------------------------------------
# The regime band: Macro dial -> Doctrine regime -> Book A band
# ---------------------------------------------------------------------------
def regime_band(store: Any, as_of: Optional[str] = None,
                limits: Optional[dict] = None) -> dict:
    """The Doctrine regime, Book A's band and the net-beta cap, or why not.

    THE CROSSING RULE: a Macro dial state that changed within the last
    `transition_sessions` objects maps to Transition -- the lower half of the band
    it is leaving. Read from stored objects, never recomputed.
    """
    import regime  # noqa: PLC0415
    lim = limits or load_limits()
    rm = lim.get("regime_mapping") or {}
    bands = {k: v for k, v in (lim.get("bands") or {}).items() if k != "source"}
    n = int(rm.get("transition_sessions") or 10)
    out: dict[str, Any] = {"mapping_version": rm.get("version"),
                           "mapping_proposed": bool(rm.get("proposed")),
                           "transition_sessions": n}
    # BOUNDED IN SQL: the object history is tens of kilobytes a session, and
    # as_of() over all of it is the 290MB read regime.prior_objects() learned
    # not to do.
    rows = store.rows_before(regime.STORE_KEY, "9999-12-31", as_of=as_of,
                             limit=n + 1)
    import json  # noqa: PLC0415
    states = []
    for r in rows:
        try:
            o = json.loads(r["value_text"])
        except Exception:                                     # noqa: BLE001
            continue
        states.append((o.get("session"),
                       ((o.get("dials") or {}).get("macro") or {}).get("state")))
    if not states or states[-1][1] is None:
        out.update({"regime": None, "band": None, "cap_pct": None,
                    "absent": True,
                    "reason": "no Macro dial state on the latest stored object"})
        return out
    cur = states[-1][1]
    out["dial_state"] = cur
    mapped = (rm.get("map") or {}).get(cur)
    prev = [s for _, s in states[:-1] if s is not None and s != cur]
    departing = None
    if mapped == "Transition" or prev:
        departing_state = prev[-1] if prev else None
        departing = (rm.get("map") or {}).get(departing_state)
        if departing == "Transition" or departing is None:
            # Transition from Transition, or no earlier state in the window:
            # the widest band is the only honest bound.
            lo = min(b[0] for b in bands.values())
            hi = max(b[1] for b in bands.values())
            band = [lo, (lo + hi) / 2]
        else:
            lo, hi = bands[departing]
            band = [lo, (lo + hi) / 2]
        out.update({"regime": "Transition", "departing": departing,
                    "departing_dial_state": departing_state})
    else:
        if mapped not in bands:
            out.update({"regime": None, "band": None, "cap_pct": None,
                        "absent": True,
                        "reason": f"dial state {cur!r} has no mapped band"})
            return out
        band = list(bands[mapped])
        out["regime"] = mapped
    over = float(((lim.get("limits") or {}).get("net_beta_over_band_top_pct")
                  or {}).get("value") or 15)
    out.update({"band": band, "cap_pct": band[1] + over, "floor_pct": band[0]})
    return out


# ---------------------------------------------------------------------------
# One decision's exposures
# ---------------------------------------------------------------------------
def _sign(direction: str) -> int:
    return {"long": 1, "short": -1, "hedge": -1}.get(str(direction), 0)


# THE FX SERIES A NON-USD EXPRESSION CONVERTS AT (INC-6 follow-up). FRED quotes
# most pairs as local units per dollar and the euro as dollars per euro, so each
# says which way it reads.
FX_SERIES = {"MXN": ("fred.usd_mxn", "per_usd"), "JPY": ("fred.usd_jpy", "per_usd"),
             "CNY": ("fred.usd_cny", "per_usd"), "EUR": ("fred.usd_eur", "usd_per")}


def to_usd(amount: float, ccy: str, store: Any,
           as_of: Optional[str] = None) -> dict:
    """{usd, rate, series, observed_at} -- or {usd: None, reason} when no rate
    is stored. NEVER PARITY: an unconverted peso amount counted as dollars is
    the INC-6 error in the heat view's arithmetic."""
    ccy = str(ccy or "USD").upper()
    if ccy == "USD":
        return {"usd": float(amount), "rate": 1.0, "series": None}
    spec = FX_SERIES.get(ccy)
    if not spec:
        return {"usd": None, "reason": f"no FX series is declared for {ccy}"}
    key, quote = spec
    row = store.latest_as_of(key, as_of=as_of) if store is not None else None
    rate = (row or {}).get("value_num")
    if not rate:
        return {"usd": None, "series": key,
                "reason": f"no stored {key} rate at this cutoff -- not converted, "
                          f"parity is not assumed"}
    usd = float(amount) / rate if quote == "per_usd" else float(amount) * rate
    return {"usd": usd, "rate": rate, "series": key, "quote": quote,
            "observed_at": str(row.get("observed_at"))[:10]}


def exposure(dec: dict, store: Any, ref: dict,
             as_of: Optional[str] = None,
             _beta_cache: Optional[dict] = None) -> dict:
    """What one decision contributes, and every input it is missing."""
    from register import instruments  # noqa: PLC0415
    root = instruments.normalise(dec.get("instrument"))
    fam = dec.get("expression_family") or "outright"
    is_opt = fam in OPTION_FAMILIES
    notional = dec.get("notional_usd")
    out: dict[str, Any] = {"decision_id": dec.get("id"), "root": root,
                           "book": dec.get("book") or "unassigned",
                           "direction": dec.get("direction"),
                           "expression_family": fam, "options": is_opt,
                           "notional_usd": notional, "missing": []}
    sgn = _sign(dec.get("direction"))
    if notional is None:
        out["missing"].append("notional_usd (structured size) not recorded")
        notional = 0.0
    # A NON-USD EXPRESSION'S NOTIONAL IS IN ITS OWN CURRENCY, converted here at
    # a stored rate the view names -- or left out of the USD totals, saying so.
    ccy = str(dec.get("expression_currency") or "USD").upper()
    if ccy != "USD" and notional:
        fx = to_usd(float(notional), ccy, store, as_of)
        out["fx"] = {"currency": ccy, "notional_local": notional, **fx}
        if fx["usd"] is None:
            out["missing"].append(f"{ccy} exposure not in USD totals: "
                                  f"{fx['reason']}")
            notional = 0.0
        else:
            notional = fx["usd"]
            out["notional_usd"] = notional
    signed = sgn * float(notional)
    cache = _beta_cache if _beta_cache is not None else {}
    if root not in cache:
        cache[root] = beta_vs_spy(root, store, as_of)
    b = cache[root]
    out["beta"], out["beta_n"] = b["beta"], b["n"]
    if b["beta"] is None and signed != 0:
        out["missing"].append(f"beta: {b['reason']}")
    out["beta_adj_usd"] = (signed * b["beta"]) if b["beta"] is not None else None
    sec = dict((ref.get("sectors") or {}).get(root) or {})
    sec_proposed = bool(sec.pop("proposed", False))
    sec.pop("source", None)
    sec.pop("as_of", None)
    out["sectors_usd"] = {k: signed * float(w) for k, w in sec.items()}
    out["sector_weights_proposed"] = sec_proposed
    if not sec and signed != 0:
        out["missing"].append(f"sector: {root} has no weights in "
                              f"config/instrument_reference.yaml")
    dur = ((ref.get("durations") or {}).get(root) or {}).get("years")
    out["duration_usd_per_100bp"] = (signed * float(dur) / 100.0
                                     if dur is not None else 0.0)
    vega = dec.get("vega_usd")
    if is_opt and vega is None:
        out["missing"].append("vega_usd: an options expression records no vega")
    out["vega_usd"] = float(vega) if vega is not None else 0.0
    return out


# ---------------------------------------------------------------------------
# The view
# ---------------------------------------------------------------------------
def view(decisions: list[dict], store: Any, as_of: Optional[str] = None,
         limits: Optional[dict] = None, ref: Optional[dict] = None) -> dict:
    """Every open decision summed across books, against the limits."""
    lim = limits or load_limits()
    ref = ref or load_reference()
    cap_usd = float((lim.get("capital_usd") or {}).get("value") or 0)
    rb = regime_band(store, as_of, lim)
    cache: dict = {}
    rows = [exposure(d, store, ref, as_of, cache) for d in decisions]
    net_beta = sum(r["beta_adj_usd"] or 0.0 for r in rows)
    by_book: dict[str, float] = {}
    for r in rows:
        by_book[r["book"]] = by_book.get(r["book"], 0.0) + (r["beta_adj_usd"] or 0.0)
    sectors: dict[str, float] = {}
    for r in rows:
        for s, v in r["sectors_usd"].items():
            sectors[s] = sectors.get(s, 0.0) + v
    duration = sum(r["duration_usd_per_100bp"] for r in rows)
    vega = sum(r["vega_usd"] for r in rows)
    vega_by_root: dict[str, float] = {}
    for r in rows:
        if r["vega_usd"]:
            vega_by_root[r["root"]] = vega_by_root.get(r["root"], 0.0) + r["vega_usd"]

    L = lim.get("limits") or {}

    def pct(x: float) -> Optional[float]:
        return round(100.0 * x / cap_usd, 2) if cap_usd else None

    checks = []

    def add(name: str, value_usd: float, limit_pct: Optional[float],
            spec: dict, what: str) -> None:
        if limit_pct is None:
            checks.append({"limit": name, "what": what, "value_usd": value_usd,
                           "value_pct": pct(value_usd), "limit_pct": None,
                           "breached": False, "proposed": bool(spec.get("proposed")),
                           "reason": "limit not set"})
            return
        breached = abs(pct(value_usd) or 0) > float(limit_pct) + 1e-9
        checks.append({"limit": name, "what": what, "value_usd": round(value_usd, 2),
                       "value_pct": pct(value_usd), "limit_pct": float(limit_pct),
                       "limit_usd": round(cap_usd * float(limit_pct) / 100, 2),
                       "breached": breached,
                       "proposed": bool(spec.get("proposed")),
                       "source": spec.get("source")})

    add("net_beta", net_beta, rb.get("cap_pct"),
        L.get("net_beta_over_band_top_pct") or {},
        "net beta-adjusted notional vs SPY, all books")
    sec_spec = L.get("sector_max_pct") or {}
    for s, v in sorted(sectors.items(), key=lambda kv: -abs(kv[1])):
        add(f"sector:{s}", v, (sec_spec or {}).get("value"), sec_spec,
            f"{s} exposure, look-through")
    vspec = L.get("vega_max_pct_per_vol_pt") or {}
    add("vega", vega, vspec.get("value"), vspec,
        "net vega, dollars per vol point, all options expressions")
    dspec = L.get("duration_max_pct_per_100bp") or {}
    add("duration", duration, dspec.get("value"), dspec,
        "net dollar duration per 100bp, rate instruments")

    concentrations = []
    for c in checks:
        if c["limit"].startswith("sector:") and c["limit_pct"] is not None and \
                abs(c["value_pct"] or 0) >= 0.8 * c["limit_pct"]:
            concentrations.append(
                f"{c['limit'].split(':', 1)[1]} {c['value_pct']:.1f}% of capital "
                f"(limit {c['limit_pct']:g}%"
                + (", proposed" if c["proposed"] else "") + ")")
        if c["limit"] == "vega" and c["limit_pct"] is not None and \
                abs(c["value_pct"] or 0) >= 0.8 * c["limit_pct"]:
            where = ", ".join(f"{k} {v:+,.0f}" for k, v in
                              sorted(vega_by_root.items(), key=lambda kv: kv[1]))
            concentrations.append(
                f"vega {c['value_usd']:+,.0f}/vol pt ({c['value_pct']:.2f}% of "
                f"capital, limit {c['limit_pct']:g}%) in {where}")
        if c["limit"] == "net_beta" and c["limit_pct"] is not None and \
                abs(c["value_pct"] or 0) >= 0.8 * c["limit_pct"]:
            concentrations.append(
                f"net beta {c['value_pct']:.1f}% of capital (cap {c['limit_pct']:g}%)")
    missing = [f"{r['root']} ({r['book']}): {m}" for r in rows for m in r["missing"]]
    return {"capital_usd": cap_usd, "regime": rb, "positions": rows,
            "net_beta_usd": round(net_beta, 2), "net_beta_pct": pct(net_beta),
            "beta_by_book_usd": {k: round(v, 2) for k, v in sorted(by_book.items())},
            "sectors_usd": {k: round(v, 2) for k, v in sorted(sectors.items())},
            "duration_usd_per_100bp": round(duration, 2),
            "vega_usd": round(vega, 2),
            "vega_by_root_usd": {k: round(v, 2) for k, v in vega_by_root.items()},
            "checks": checks, "breaches": [c for c in checks if c["breached"]],
            "concentrations": concentrations, "missing": missing,
            "limits_version": lim.get("version"),
            "reference_version": ref.get("version")}


# ---------------------------------------------------------------------------
# The gate at entry
# ---------------------------------------------------------------------------
def gate(candidate: dict, open_decisions: list[dict], store: Any,
         as_of: Optional[str] = None, limits: Optional[dict] = None,
         ref: Optional[dict] = None) -> dict:
    """The gate's outcome for one candidate against the open book.

    DETERMINISTIC, in this order:
      delay        the candidate lacks an input the view needs (a size, a beta,
                   a sector, a vega) or the regime band is unreadable
      approve      no limit is breached after it, or none it makes worse
      restructure  it worsens the vega limit: change the expression, not the size
      resize       it worsens a sector, duration or net-beta limit and a size of at
                   least 25% of the request fits every such limit
      hedge        it worsens the net-beta limit and no such size fits: the book
                   needs an offset, not a smaller trade
      reject       it worsens a sector or duration limit and no such size fits
    """
    lim = limits or load_limits()
    ref = ref or load_reference()
    before = view(open_decisions, store, as_of, lim, ref)
    after = view(open_decisions + [candidate], store, as_of, lim, ref)
    cand = after["positions"][-1]
    out: dict[str, Any] = {"view_after": after, "candidate": cand,
                           "resize_factor": None, "reasons": []}
    if cand["missing"]:
        out["outcome"] = "delay"
        out["reasons"] = [f"missing input -- {m}" for m in cand["missing"]]
        return out
    if after["regime"].get("cap_pct") is None:
        out["outcome"] = "delay"
        out["reasons"] = [f"regime band unreadable -- "
                          f"{after['regime'].get('reason')}"]
        return out
    was = {c["limit"]: c for c in before["checks"]}
    worse = []
    for c in after["breaches"]:
        b = was.get(c["limit"])
        if b is None or abs(c["value_usd"]) > abs(b["value_usd"]) + 1e-6:
            worse.append((c, b))
    if not worse:
        out["outcome"] = "approve"
        pre = [c["limit"] for c in after["breaches"]]
        out["reasons"] = (["no limit breached"] if not pre else
                          [f"limits already breached before it and not worsened: "
                           f"{', '.join(pre)}"])
        return out
    names = [c["limit"] for c, _ in worse]
    out["reasons"] = [
        f"{c['limit']}: {c['value_pct']:.2f}% of capital after, limit "
        f"{c['limit_pct']:g}%" + (" (proposed)" if c["proposed"] else "")
        for c, _ in worse]
    if "vega" in names:
        out["outcome"] = "restructure"
        out["reasons"].insert(0, "the expression adds vega past the limit -- "
                                 "change the structure (defined wings, less vega), "
                                 "not the size")
        return out

    # The largest share of the request that fits every worsened limit.
    f = 1.0
    for c, b in worse:
        lim_usd = c["limit_usd"]
        before_v = (b or {}).get("value_usd", 0.0)
        contrib = c["value_usd"] - before_v
        room = lim_usd - abs(before_v)
        f = min(f, max(0.0, room / abs(contrib)) if contrib else 0.0)
    f = math.floor(f * 100) / 100
    out["resize_factor"] = f
    if f >= MIN_RESIZE_FACTOR:
        out["outcome"] = "resize"
        out["reasons"].insert(0, f"fits at {f:.0%} of the requested size "
                                 f"(notional {cand['notional_usd'] * f:,.0f})")
    elif "net_beta" in names:
        out["outcome"] = "hedge"
        out["reasons"].insert(0, "net beta across books is past the Doctrine cap "
                                 "and no useful size fits: offset it first")
    else:
        out["outcome"] = "reject"
        out["reasons"].insert(0, "no useful size fits the limits it breaches")
    assert out["outcome"] in GATE_OUTCOMES
    return out


def format_view(v: dict) -> str:
    """The view as the terminal and the close print it."""
    rb = v.get("regime") or {}
    L = [f"HEAT / FACTOR VIEW  capital ${v['capital_usd']:,.0f}  limits "
         f"{v.get('limits_version')}  reference {v.get('reference_version')}"]
    if rb.get("band"):
        L.append(f"  regime   : dial {rb.get('dial_state')} -> {rb.get('regime')}"
                 + (f" (leaving {rb.get('departing')})" if rb.get("departing") else "")
                 + f"; band {rb['band'][0]:g}-{rb['band'][1]:g}%, net-beta cap "
                   f"{rb['cap_pct']:g}%  [mapping {rb.get('mapping_version')}"
                 + (", PROPOSED" if rb.get("mapping_proposed") else "") + "]")
    else:
        L.append(f"  regime   : ABSENT -- {rb.get('reason')}")
    L.append(f"  positions: {len(v['positions'])} open decision(s)")
    for p in v["positions"]:
        L.append(f"    {p['root']:<6} book {p['book']:<10} {p['direction']:<6} "
                 f"{p['expression_family']:<16} notional "
                 + (f"{p['notional_usd']:>11,.0f}" if p['notional_usd'] is not None
                    else f"{'unrecorded':>11}")
                 + f"  beta {p['beta'] if p['beta'] is not None else 'n/a'}"
                 + (f"  [{p['fx']['notional_local']:,.0f} {p['fx']['currency']} at "
                    f"{p['fx']['series']} {p['fx']['rate']:g} "
                    f"({p['fx']['observed_at']})]"
                    if (p.get("fx") or {}).get("usd") is not None else
                    f"  [{p['fx']['currency']} NOT CONVERTED: no stored rate]"
                    if p.get("fx") else ""))
    L.append(f"  net beta : {v['net_beta_usd']:+,.0f} ({v['net_beta_pct']}% of "
             f"capital); by book "
             + ", ".join(f"{k} {x:+,.0f}" for k, x in v["beta_by_book_usd"].items()))
    if v["sectors_usd"]:
        L.append("  sectors  : " + ", ".join(
            f"{k} {x:+,.0f}" for k, x in sorted(v["sectors_usd"].items(),
                                                 key=lambda kv: -abs(kv[1]))))
    L.append(f"  duration : {v['duration_usd_per_100bp']:+,.0f} per 100bp;  "
             f"vega {v['vega_usd']:+,.0f} per vol pt")
    for c in v["checks"]:
        if c["limit_pct"] is None:
            continue
        L.append(f"    {'BREACH' if c['breached'] else 'ok    '} {c['limit']:<24} "
                 f"{c['value_pct']:>7.2f}% vs {c['limit_pct']:g}%"
                 + ("  (limit PROPOSED, unratified)" if c["proposed"] else ""))
    for c in v["concentrations"]:
        L.append(f"  CONCENTRATION: {c}")
    for m in v["missing"]:
        L.append(f"  MISSING  : {m}")
    return "\n".join(L)


def _main(argv: list[str]) -> int:
    import argparse  # noqa: PLC0415
    import sys  # noqa: PLC0415
    ap = argparse.ArgumentParser(description="The cross-book heat/factor view.")
    ap.add_argument("--db", default=None)
    ap.add_argument("--as-of", default=None)
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from altdata import observations  # noqa: PLC0415
    from register.store import Register  # noqa: PLC0415
    with Register(a.db) as reg:
        decs = reg.open_decisions()
    st = observations.ObservationStore(a.db)
    try:
        print(format_view(view(decs, st, a.as_of)))
    finally:
        st.close()
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
