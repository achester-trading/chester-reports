"""
Level clusters: the dealer scorecard's H6 (Batch 11 item 55 and decision D3,
ruled 19 Oct 2026; registered in docs/ledgers/dealer-scorecard-preregistration-
2026-10-h6.md, committed before this module).

    from altdata import level_clusters as lc
    zones = lc.find_clusters(levels)                 # pure: three families in 0.2%
    lc.store_for_next(st, bst, "SPY", day, now)      # the close: the next session's zones
    lc.in_force(st, "SPY", day, cutoff)              # every zone frozen over 30 days
    lc.rates_from_store(st, bst, cutoff)             # H6s and H6f, as H1-H5 print

THE FOUR FAMILIES, OUR OWN LEVELS ONLY (D3: vendor levels never count; this
module reads no vendor key and the opening-setup grep covers it):
  positioning   the settled 16:10 capture's flip, OTM call wall, OTM put gamma
                wall, peak-gamma strike and max pain
  bands         the one- and five-session one-sigma edges around the close
                (the close x the 30-day ATM IV x sqrt(h/252))
  profile       VP-1's POC, VAH and VAL of the session and the 20-session
                window, and the 20-session window's high-volume nodes
  prior         the session's high, low and close, and (SPY) the overnight
                high and low that led into it, ES converted at the 23-hour
                chart's session basis

A CLUSTER is a set of levels from three or more families whose highest and lowest
lie within 0.2% of each other; its zone is [lowest, highest]. A zone is FROZEN for
30 calendar days from the session it is found for; a later zone overlapping one
in force is not stored again.

THE WRITER is the 16:45 close: after the 16:10 capture it finds the NEXT session's
zones from the levels known then, and stores them under `calc.level_zones`
(instrument = the symbol, observed_at = the session the zones are for), with
every member level beside them for the base rate. The 07:00 anchor reads them;
nothing recomputes them.
"""

from __future__ import annotations

import datetime as dt
import json
import math
from typing import Any, Optional

KEY = "calc.level_zones"
FAMILIES = ("positioning", "bands", "profile", "prior")
FAMILY_WORDS = {"positioning": "positioning", "bands": "implied bands",
                "profile": "volume profile", "prior": "the prior session"}
INSTRUMENTS = ("SPY", "QQQ", "IWM")
ROUND_STEP = {"SPY": 5.0, "QQQ": 5.0, "IWM": 2.5}
H6 = ("h6s", "h6f")
H6_LABELS = {"h6s": "H6s cluster held (session)", "h6f": "H6f cluster held (five sessions)"}


def config(cfg: Optional[dict] = None) -> dict:
    if cfg is None:
        from altdata import bars as bars_mod                    # noqa: PLC0415
        cfg = bars_mod.load_config()
    c = dict(cfg.get("level_clusters") or {})
    c.setdefault("cluster_pct", 0.2)
    c.setdefault("min_families", 3)
    c.setdefault("freeze_days", 30)
    c.setdefault("approach_pct", 0.25)
    c.setdefault("forward_sessions", 5)
    c.setdefault("registered_on", "2026-10-19")
    return c


# ---------------------------------------------------------------------------
# The cluster rule (pure)
# ---------------------------------------------------------------------------
def find_clusters(levels: list[dict], pct: float = 0.2, min_families: int = 3) -> list[dict]:
    """[{low, high, families, members}] from [{family, name, value}]: every maximal
    run of sorted levels whose highest is within `pct`% of its lowest and that
    covers `min_families` families; overlapping runs merge."""
    pts = sorted((l for l in levels if l.get("value") is not None
                  and l.get("family") in FAMILIES), key=lambda l: float(l["value"]))
    runs = []
    j = 0
    for i in range(len(pts)):
        j = max(j, i)
        while j + 1 < len(pts) and float(pts[j + 1]["value"]) <= float(pts[i]["value"]) * (1 + pct / 100.0):
            j += 1
        win = pts[i:j + 1]
        if len({l["family"] for l in win}) >= min_families:
            runs.append((i, j))
    zones: list[list[int]] = []
    for i, j in runs:
        if zones and i <= zones[-1][1]:
            zones[-1][1] = max(zones[-1][1], j)
        else:
            zones.append([i, j])
    out = []
    for i, j in zones:
        m = pts[i:j + 1]
        out.append({"low": float(m[0]["value"]), "high": float(m[-1]["value"]),
                    "families": sorted({l["family"] for l in m}, key=FAMILIES.index),
                    "members": [{"family": l["family"], "name": l["name"],
                                 "value": float(l["value"])} for l in m]})
    return out


def side(zone: dict, prior_close: float) -> Optional[str]:
    if zone["low"] > prior_close:
        return "resistance"
    if zone["high"] < prior_close:
        return "support"
    return None


def approached(zone: dict, s: str, hi: float, lo: float, pct: float) -> bool:
    if s == "resistance":
        return hi >= zone["low"] * (1 - pct / 100.0)
    return lo <= zone["high"] * (1 + pct / 100.0)


def held_session(zone: dict, s: str, close: float) -> bool:
    return close <= zone["high"] if s == "resistance" else close >= zone["low"]


def held_forward(zone: dict, s: str, closes: list[float]) -> bool:
    if s == "resistance":
        return all(c <= zone["high"] for c in closes)
    return all(c >= zone["low"] for c in closes)


# ---------------------------------------------------------------------------
# Gathering the levels (reads only; our own)
# ---------------------------------------------------------------------------
def _num(x: Any) -> Optional[float]:
    try:
        return None if x is None else float(x)
    except (TypeError, ValueError):
        return None


def gather_levels(st, bst, sym: str, day: str, as_of: str,
                  computed_dir: Optional[str] = None) -> tuple[list[dict], Optional[float]]:
    """([{family, name, value}], the session's close) for `sym` after session
    `day`'s 16:10 capture: the levels in force for the NEXT session."""
    from altdata import bars as bars_mod, volume_profile as vp  # noqa: PLC0415
    from daily_cascade import dealer_block                      # noqa: PLC0415
    out: list[dict] = []
    prof = dealer_block.newest_settled(day, sym, computed_dir, lookback_days=0) or {}
    o = prof.get("overall") or {}
    for name, k in (("flip", "gamma_flip"), ("OTM call wall", "call_wall_otm"),
                    ("OTM put gamma wall", "put_wall_otm"),
                    ("peak-gamma strike", "peak_abs_gex_strike"), ("max pain", "max_pain")):
        if _num(o.get(k)) is not None:
            out.append({"family": "positioning", "name": name, "value": _num(o[k])})
    ib = bars_mod.intraday(bst, sym.lower(), day, as_of=as_of)
    b = ib.get("bars") or []
    close = _num(b[-1]["close"]) if b else None
    if b:
        out += [{"family": "prior", "name": "session high", "value": max(x["high"] for x in b)},
                {"family": "prior", "name": "session low", "value": min(x["low"] for x in b)},
                {"family": "prior", "name": "session close", "value": close}]
    if sym == "SPY":
        on = overnight_hl(bst, day, as_of)
        if on:
            out += [{"family": "prior", "name": "overnight high", "value": on[0]},
                    {"family": "prior", "name": "overnight low", "value": on[1]}]
    iv = _iv(st, sym, day, as_of)
    if close and iv:
        for h in (1, 5):
            s = close * iv / 100.0 * math.sqrt(h / 252.0)
            lab = "one-session" if h == 1 else "five-session"
            out += [{"family": "bands", "name": f"{lab} band, upper", "value": close + s},
                    {"family": "bands", "name": f"{lab} band, lower", "value": close - s}]
    for w in ("session", "20s"):
        for f in ("poc", "vah", "val"):
            r = st.latest_as_of(f"calc.vp_{sym.lower()}_{w}_{f}", as_of)
            if r and r.get("value_num") is not None and str(r["observed_at"])[:10] == day:
                out.append({"family": "profile", "name": f"{w} {f.upper()}",
                            "value": float(r["value_num"])})
    try:
        p20 = vp.window(bst, sym.lower(), "20s", day, as_of)
        for h in (p20 or {}).get("hvn") or []:
            out.append({"family": "profile", "name": "20-session HVN", "value": float(h)})
    except Exception:                                           # noqa: BLE001
        pass
    return out, close


def _iv(st, sym: str, day: str, as_of: str) -> Optional[float]:
    if sym == "SPY":
        r = st.latest_as_of("chain.spy_atm_iv_30d", as_of)
    else:
        r = st.latest_as_of("chain.iv30_atm", as_of, sym)
    if r and r.get("value_num") is not None and str(r["observed_at"])[:10] == day:
        return float(r["value_num"])
    return None


def overnight_hl(bst, day: str, as_of: str) -> Optional[tuple[float, float]]:
    """The overnight that led into `day` (18:00 ET the evening before to 09:30),
    ES's high and low converted to SPY at the 23-hour chart's session basis (the
    newest session before `day` with both 09:30 opens)."""
    from altdata import session                                 # noqa: PLC0415
    from daily_cascade.charts import es_at_open                 # noqa: PLC0415
    d = dt.date.fromisoformat(day)
    first = (d - dt.timedelta(days=10)).isoformat()
    es5 = bst.read("es", "5m", first, as_of, as_of)
    spy5 = bst.read("spy", "5m", first, as_of, as_of)
    start = dt.datetime.combine(d - dt.timedelta(days=1), dt.time(18, 0),
                                tzinfo=session._eastern_tz())   # noqa: SLF001
    end = dt.datetime.combine(d, dt.time(9, 30), tzinfo=session._eastern_tz())  # noqa: SLF001
    on = [b for b in es5 if start <= session.to_eastern(
        dt.datetime.fromisoformat(b["observed_at"])) < end]
    if not on:
        return None
    for x in sorted({str(b["observed_at"])[:10] for b in spy5 if str(b["observed_at"])[:10] < day},
                    reverse=True):
        so, eo = es_at_open(spy5, x), es_at_open(es5, x)
        if so and eo:
            basis = so / eo
            return max(b["high"] for b in on) * basis, min(b["low"] for b in on) * basis
    return None


# ---------------------------------------------------------------------------
# Store and read (the close writes; the anchor and the Weekly read)
# ---------------------------------------------------------------------------
def in_force(st, sym: str, day: str, cutoff: str, cfg: Optional[dict] = None) -> list[dict]:
    """Every stored zone for `sym` found for a session within `freeze_days` up to
    `day`, frozen at its edges, oldest first."""
    c = config() if cfg is None else cfg
    lo = (dt.date.fromisoformat(day) - dt.timedelta(days=int(c["freeze_days"]) - 1)).isoformat()
    out = []
    for r in sorted(st.as_of(KEY, cutoff, sym), key=lambda r: str(r["observed_at"])):
        found = str(r["observed_at"])[:10]
        if not (lo <= found <= day):
            continue
        try:
            rec = json.loads(r["value_text"])
        except (TypeError, ValueError):
            continue
        for z in rec.get("zones") or []:
            out.append({**z, "found_for": found})
    return out


def next_session(day: str) -> str:
    from altdata import session                                 # noqa: PLC0415
    d = dt.date.fromisoformat(day) + dt.timedelta(days=1)
    while not session.is_trading_session(d):
        d += dt.timedelta(days=1)
    return d.isoformat()


def zones_for_next(st, bst, sym: str, day: str, as_of: str,
                   computed_dir: Optional[str] = None, cfg: Optional[dict] = None) -> dict:
    """{for, levels, zones}: the next session's new zones (overlaps with a zone
    in force dropped), and every level for the base rate."""
    c = config() if cfg is None else cfg
    levels, close = gather_levels(st, bst, sym, day, as_of, computed_dir)
    nxt = next_session(day)
    held = in_force(st, sym, nxt, as_of, c)
    new = [z for z in find_clusters(levels, float(c["cluster_pct"]), int(c["min_families"]))
           if not any(z["low"] <= h["high"] and h["low"] <= z["high"] for h in held)]
    return {"for": nxt, "levels": levels, "close": close, "zones": new}


def store_for_next(st, bst, sym: str, day: str, now: str,
                   computed_dir: Optional[str] = None) -> Optional[dict]:
    rec = zones_for_next(st, bst, sym, day, now, computed_dir)
    if not rec["levels"]:
        return None
    st.write_many([{"registry_key": KEY, "instrument": sym, "observed_at": rec["for"],
                    "available_at": now,
                    "value": json.dumps(rec, sort_keys=True, default=str),
                    "source": "daily_close"}])
    return rec


def sessions_between(first: str, last: str) -> list[str]:
    from altdata import session                                 # noqa: PLC0415
    d, out = dt.date.fromisoformat(first), []
    end = dt.date.fromisoformat(last)
    while d <= end:
        if session.is_trading_session(d):
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def zones_in_force_all(st, day: str, cutoff: str) -> dict[str, list[dict]]:
    return {sym: in_force(st, sym, day, cutoff) for sym in INSTRUMENTS}


def anchor_block(st, day: str, cutoff: str, db_path: Optional[str] = None) -> dict:
    """The 07:00 anchor's lines: at most two zones in force today, read only.
    Never raises."""
    from altdata import bars as bars_mod                        # noqa: PLC0415
    try:
        zones = zones_in_force_all(st, day, cutoff)
        pcs = {}
        with bars_mod.BarStore(db_path) as bst:
            from altdata import session                         # noqa: PLC0415
            prev = session.previous_trading_session(day).isoformat()
            for sym in INSTRUMENTS:
                b = bars_mod.intraday(bst, sym.lower(), prev, as_of=cutoff).get("bars") or []
                if b:
                    pcs[sym] = float(b[-1]["close"])
        return {"title": "Level clusters (H6, registered)",
                "lines": anchor_lines(zones, pcs), "paragraph_wanted": False}
    except Exception as exc:                                    # noqa: BLE001
        return {"title": "Level clusters (H6, registered)",
                "lines": [f"Level clusters: not read ({type(exc).__name__})."],
                "paragraph_wanted": False}


def close_item_text(st, bst, day: str, cutoff: str) -> Optional[str]:
    """The 16:45 close's one outcome line over today's zones in force."""
    zones = zones_in_force_all(st, day, cutoff)
    from altdata import session                                 # noqa: PLC0415
    prev = session.previous_trading_session(day).isoformat()
    ohlc = {}
    for sym in INSTRUMENTS:
        o = daily_ohlc(bst, sym, [prev, day], cutoff)
        if day in o:
            ohlc[sym] = o[day]
    return close_line(zones, ohlc)


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------
def _fmt(v: float) -> str:
    return f"{v:,.2f}"


def anchor_lines(zones_by_sym: dict[str, list[dict]], prior_close: dict[str, float],
                 spx_ratio: Optional[float] = None, es_basis: Optional[float] = None,
                 n: int = 2) -> list[str]:
    """At most `n` zones, nearest the prior close first, one line each with its
    families named; SPY's also in SPX and ES terms when the ratios are given."""
    cand = []
    for sym, zs in zones_by_sym.items():
        pc = prior_close.get(sym)
        for z in zs:
            s = side(z, pc) if pc else None
            if not s:
                continue
            dist = (z["low"] / pc - 1) if s == "resistance" else (z["high"] / pc - 1)
            cand.append((abs(dist), sym, z, s))
    out = []
    for _, sym, z, s in sorted(cand, key=lambda x: x[0])[:n]:
        fams = ", ".join(FAMILY_WORDS[f] for f in z["families"])
        line = (f"Level cluster ({sym}, {s}): {_fmt(z['low'])} to {_fmt(z['high'])}; "
                f"{len(z['families'])} families ({fams}), found for {z['found_for']}, "
                f"frozen 30 days")
        if sym == "SPY" and spx_ratio:
            line += f"; SPX {_fmt(z['low'] * spx_ratio)} to {_fmt(z['high'] * spx_ratio)}"
        if sym == "SPY" and es_basis:
            line += f"; ES {_fmt(z['low'] / es_basis)} to {_fmt(z['high'] / es_basis)}"
        out.append(line + ". Registered (H6), not a reading.")
    return out


def close_line(zones_by_sym: dict[str, list[dict]], ohlc: dict[str, dict]) -> Optional[str]:
    """The 16:45 close's one outcome line over the session's zones in force."""
    parts = []
    for sym, zs in zones_by_sym.items():
        o = ohlc.get(sym) or {}
        if None in (o.get("high"), o.get("low"), o.get("close"), o.get("prior_close")):
            continue
        for z in zs:
            s = side(z, o["prior_close"])
            if not s:
                continue
            if approached(z, s, o["high"], o["low"], 0.25):
                word = "held" if held_session(z, s, o["close"]) else "broke"
            else:
                word = "not reached"
            parts.append(f"{sym} {_fmt(z['low'])} to {_fmt(z['high'])} {word}")
    if not parts:
        return None
    return "Level clusters today: " + "; ".join(parts) + " (H6, registered, not a reading)."


# ---------------------------------------------------------------------------
# The rates (as H1-H5 print)
# ---------------------------------------------------------------------------
def score_zone_sessions(zone: dict, days: list[str], ohlc: dict[str, dict],
                        pct: float, fwd: int) -> list[dict]:
    """Per session in the zone's 30 days: eligible, h6s outcome, h6f outcome (on
    the first approach in each five-session window)."""
    out, last_f = [], None
    for i, d in enumerate(days):
        o = ohlc.get(d) or {}
        if None in (o.get("high"), o.get("low"), o.get("close"), o.get("prior_close")):
            continue
        s = side(zone, o["prior_close"])
        if not s:
            continue
        el = approached(zone, s, o["high"], o["low"], pct)
        rec = {"session": d, "eligible": el,
               "h6s": held_session(zone, s, o["close"]) if el else None, "h6f": None,
               "h6f_eligible": False}
        if el and (last_f is None or i - last_f >= fwd):
            last_f = i
            nxt = [(ohlc.get(x) or {}).get("close") for x in days[i:i + fwd]]
            rec["h6f_eligible"] = True
            rec["h6f"] = (held_forward(zone, s, nxt)
                          if len(nxt) == fwd and None not in nxt else None)
        out.append(rec)
    return out


def rate_h6(recs: list[dict], base: list[dict], baseline: list[dict], h: str,
            cfg: dict, label: Optional[str] = None) -> dict:
    """A rate dict in dealer_scorecard.rate's shape, for dsc.rate_line."""
    from altdata import dealer_scorecard as dsc                 # noqa: PLC0415
    key_el = "eligible" if h == "h6s" else "h6f_eligible"
    elig = [r for r in recs if r[key_el]]
    scored = [r for r in elig if r[h] is not None]
    k, n = sum(1 for r in scored if r[h]), len(scored)
    b = [r[h] for r in base if r[key_el] and r[h] is not None]
    bl = [r[h] for r in baseline if r[key_el] and r[h] is not None]
    floor, decide = int(cfg.get("print_floor_sessions", 20)), int(cfg.get("decision_floor_eligible", 120))
    form = int(cfg.get("formation_sessions", 120))
    out = {"hypothesis": h, "label": label or H6_LABELS[h], "k": k, "n": n,
           "eligible": len(elig), "episodes": len({r.get("zone_id") for r in elig}),
           "base_rate": (sum(b) / len(b)) if b else None, "base_n": len(b),
           "baseline": (sum(bl) / len(bl)) if bl else None, "baseline_n": len(bl),
           "printable": n >= floor, "decision": len(elig) >= decide}
    out["interval"] = dsc.wilson(k, n) if out["printable"] else None
    e = len(elig)
    out["phase"] = (f"forming: {e} of {form} eligible sessions" if e < form else
                    f"testing: {min(e - form, form)} of {form}" if e < 2 * form else
                    "formation and test complete: promotion by the registration's rule")
    return out


def daily_ohlc(bst, sym: str, days: list[str], as_of: str) -> dict[str, dict]:
    from altdata import bars as bars_mod                        # noqa: PLC0415
    out, prev = {}, None
    for d in days:
        b = bars_mod.intraday(bst, sym.lower(), d, as_of=as_of).get("bars") or []
        if not b:
            prev = None
            continue
        rec = {"high": max(x["high"] for x in b), "low": min(x["low"] for x in b),
               "close": float(b[-1]["close"]), "prior_close": prev}
        out[d] = rec
        prev = rec["close"]
    return out


def rates_from_store(st, bst, cutoff: str, sessions: list[str],
                     cfg: Optional[dict] = None, sc_cfg: Optional[dict] = None) -> dict:
    """H6s and H6f over every stored zone set, for SPY, QQQ and IWM: the test
    sample (sessions from the registration) and the rest beside it."""
    from altdata import dealer_scorecard as dsc                 # noqa: PLC0415
    c = config() if cfg is None else cfg
    scc = sc_cfg if sc_cfg is not None else dsc.config()
    pct, fwd = float(c["approach_pct"]), int(c["forward_sessions"])
    reg = str(c["registered_on"])[:10]
    recs, base, base_l = [], [], []
    for sym in INSTRUMENTS:
        ohlc = daily_ohlc(bst, sym, sessions, cutoff)
        for r in st.as_of(KEY, cutoff, sym):
            try:
                rec = json.loads(r["value_text"])
            except (TypeError, ValueError):
                continue
            found = str(r["observed_at"])[:10]
            win = [d for d in sessions if found <= d < (dt.date.fromisoformat(found)
                   + dt.timedelta(days=int(c["freeze_days"]))).isoformat()]
            for zi, z in enumerate(rec.get("zones") or []):
                for x in score_zone_sessions(z, win, ohlc, pct, fwd):
                    recs.append({**x, "zone_id": f"{sym}:{found}:{zi}", "sym": sym})
            # The base rate: every single level not in a cluster, a zone of one.
            inz = {(m["name"], m["value"]) for z in rec.get("zones") or [] for m in z["members"]}
            for li, lv in enumerate(rec.get("levels") or []):
                if (lv["name"], lv["value"]) in inz:
                    continue
                one = {"low": lv["value"], "high": lv["value"]}
                base += [{**x, "zone_id": f"b{sym}{found}{li}"}
                         for x in score_zone_sessions(one, win[:1], ohlc, pct, fwd)]
            # The baseline: the round numbers above and below the close.
            pc = rec.get("close")
            if pc:
                stp = ROUND_STEP[sym]
                for v in (math.ceil(pc / stp) * stp, math.floor(pc / stp) * stp):
                    one = {"low": v, "high": v}
                    base_l += [{**x, "zone_id": f"r{sym}{found}{v}"}
                               for x in score_zone_sessions(one, win[:1], ohlc, pct, fwd)]
    test = [r for r in recs if r["session"] >= reg]
    rest = [r for r in recs if r["session"] < reg]
    rates = [rate_h6(test, base, base_l, h, scc) for h in H6]
    before = [rate_h6(rest, base, base_l, h, scc) for h in H6]
    lines = []
    for t, b in zip(rates, before):
        lines += [dsc.rate_line(t), dsc.descriptive_line({**b, "backfilled_n": 0})]
    return {"rates": rates, "before": before, "lines": lines, "registered": len(H6),
            "zones": len({r["zone_id"] for r in recs})}
