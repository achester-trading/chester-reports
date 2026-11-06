"""
The dealer block, part 1 (6b; brief v2 `docs/briefs/dealer-positioning-brief-
2026-10-09.md`, ratified 16 Oct 2026): T1 with its quality panel, T4, T2 and the
decision summary, as views of the engine's exposure JSON.

    from daily_cascade import dealer_block
    blk = dealer_block.block(profile, prior, cfg=None, releases=[])
    python -m daily_cascade.dealer_block show [--date D] [--symbol SPY]

WHAT IT IS. Every figure here is read from one computed profile
(tools/exposure_compute.py, dealers-hand-v1): `overall`, the horizon windows and
bands (`horizons`, `bands`), `per_strike`, `quality` and `gates`. NOTHING
RECOMPUTES: a table is a view, and the only arithmetic is a distance from spot,
a difference between two stored captures, and the bands' reconciliation sum.

WHAT IT MAY SAY (brief section 1). The convention-free quantities print first:
the call-gamma and put-gamma masses and the zero-gamma (balance) level. Net GEX
and the regime word print second, the word gated on net-to-gross at or above
`dealer_block.net_to_gross_min` (0.10, RULED): below it, "indeterminate (net is
x% of gross)". "inferred, not observed" heads every dealer table, and the sign
convention prints once per edition (the section's note). Never printed: a
direction for DEX or the roll-off (the hedge book is a size and a tenor);
"support" or "resistance" as facts; a horizon rule as a reading before it is
promoted; a 0DTE gamma figure without "OI as of prior close". The gate
(tools/validate_dealer_block.py) reads every printed string for those.

THE DECISION SUMMARY proposes the setups whose conditions hold, from
config/setups.yaml, each with its level, invalidation and time stop. The books
decide. This module imports no register, ledger or order path and writes
nothing; the three fixed sentences of the brief's section 4 are part 2's (their
slot is `sentences`, None here).
"""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Optional

from altdata.numeral_audit import ordinal as _ordinal

REPO = Path(__file__).resolve().parent.parent

FIELDS_T4 = (("call_gamma_per_1pct", "Call-gamma mass ($/1%)", "usd"),
             ("put_gamma_per_1pct", "Put-gamma mass ($/1%)", "usd"),
             ("dollar_gamma_per_1pct", "Net GEX ($/1%)", "usd"),
             ("net_to_gross", "Net-to-gross", "share"),
             ("gamma_flip", "Zero-gamma level", "price"),
             ("call_wall_otm", "OTM call wall", "price"),
             ("put_wall_otm", "OTM put gamma wall", "price"),
             ("dex_notional", "Hedge-book size (DEX)", "usd"),
             ("peak_abs_gex_strike", "Peak-gamma strike", "price"))


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
def config() -> dict:
    """`dealer_block` and `horizon_windows` from config/reporting_stack.yaml."""
    import yaml                                                 # noqa: PLC0415
    raw = yaml.safe_load((REPO / "config" / "reporting_stack.yaml")
                         .read_text(encoding="utf-8")) or {}
    out = dict(raw.get("dealer_block") or {})
    out["horizon_windows"] = raw.get("horizon_windows") or {}
    return out


def setup_names() -> dict:
    import yaml                                                 # noqa: PLC0415
    s = yaml.safe_load((REPO / "config" / "setups.yaml").read_text(encoding="utf-8"))
    return {k: v for k, v in (s.get("setups") or {}).items()}


# ---------------------------------------------------------------------------
# Formatting (the printed forms; no arithmetic beyond a distance)
# ---------------------------------------------------------------------------
def usd(v: Optional[float], signed: bool = False) -> str:
    if v is None:
        return "n/a"
    s = f"{abs(v) / 1e9:,.2f}"
    sign = ("+" if v > 0 else "−" if v < 0 else "") if signed else ("−" if v < 0 else "")
    return f"{sign}${s}bn"


def price(v: Optional[float]) -> str:
    return "n/a" if v is None else f"{v:,.2f}"


def pct(v: Optional[float], dp: int = 0) -> str:
    return "n/a" if v is None else f"{v * 100:.{dp}f}%"


def dist(level: Optional[float], spot: Optional[float]) -> str:
    """Spot's distance to a level, as the level's place against spot."""
    if level is None or not spot:
        return "n/a"
    d = (level / spot - 1.0) * 100.0
    return f"{'+' if d > 0 else '−' if d < 0 else ''}{abs(d):.2f}%"


def shares(v: Optional[float]) -> str:
    if v is None:
        return "n/a"
    return f"{'+' if v > 0 else '−' if v < 0 else ''}{abs(v) / 1e6:,.1f}m shares"


def regime(net: Optional[float], ntg: Optional[float], cfg: dict) -> str:
    """The regime word, gated (RULED 16 Oct 2026)."""
    if net is None or ntg is None:
        return "no net GEX"
    if ntg < float(cfg.get("net_to_gross_min", 0.10)):
        return f"indeterminate (net is {ntg * 100:.0f}% of gross)"
    return "positive gamma" if net > 0 else "negative gamma"


def regime_sign(net: Optional[float], ntg: Optional[float], cfg: dict) -> Optional[str]:
    """'positive' / 'negative' when the gate passes, else None."""
    w = regime(net, ntg, cfg)
    return w.split()[0] if w in ("positive gamma", "negative gamma") else None


def _et(iso: Optional[str]) -> Optional[dt.datetime]:
    if not iso:
        return None
    from altdata import session                                 # noqa: PLC0415
    return session.to_eastern(iso)


def capture_label(p: dict) -> str:
    t = _et(p.get("fetched_at"))
    kind = "settled" if p.get("capture") == "settled_eod" else "intraday"
    return (f"{t:%Y-%m-%d %H:%M} ET, {kind}" if t else f"time not stamped, {kind}")


def slot_of(p: dict, cfg: dict) -> Optional[str]:
    """The capture's slot: a settled capture is 16:10; an intraday one takes the
    nearest declared slot within the tolerance, else None."""
    slots = list(cfg.get("capture_slots") or ["09:45", "12:30", "16:10"])
    if p.get("capture") == "settled_eod":
        return "16:10" if "16:10" in slots else None
    t = _et(p.get("fetched_at"))
    if t is None:
        return None
    tol = float(cfg.get("slot_tolerance_min", 20))
    best = None
    for s in slots:
        if s == "16:10":
            continue
        h, m = (int(x) for x in s.split(":"))
        gap = abs((t.hour * 60 + t.minute) - (h * 60 + m))
        if gap <= tol and (best is None or gap < best[0]):
            best = (gap, s)
    return best[1] if best else None


def is_expiry(p: dict) -> Optional[bool]:
    """The capture carried DTE 0 rows: an expiry session for this symbol."""
    if not p or p.get("error"):
        return None
    q = p.get("quality") or {}
    return bool((p.get("buckets") or {}).get("0dte")
                or (q.get("settled_0dte_excluded_rows") or 0) > 0)


def target_session(p: dict) -> Optional[str]:
    """The session a capture's decision summary is FOR. An intraday capture
    (09:45, 12:30) reads its own session; the settled 16:10 capture is taken
    after its session ended, so it reads the NEXT trading session -- its own
    expiry has already settled and cannot be a setup."""
    sess = p.get("session_date")
    if not sess or p.get("capture") != "settled_eod":
        return sess
    from altdata import session                                 # noqa: PLC0415
    d = dt.date.fromisoformat(sess) + dt.timedelta(days=1)
    while not (session.is_trading_session(d) if session.calendar_covers(d)
               else d.weekday() < 5):
        d += dt.timedelta(days=1)
    return d.isoformat()


def expiry_on_target(p: dict, cfg: Optional[dict] = None) -> Optional[bool]:
    """An expiry session on the target session: for an intraday capture, the
    capture carried DTE 0 rows; for the settled capture, a listed expiry falls
    on the next trading session (from the stored release ladder and buckets).
    Under `expiry_sessions: monthly` (ruled 17 Oct 2026) the target must be the
    monthly third Friday -- SPY lists an expiry every weekday."""
    if not p or p.get("error"):
        return None
    tgt = target_session(p)
    if p.get("capture") != "settled_eod":
        listed = bool(is_expiry(p))
    else:
        exps = {e.get("expiry") for e in p.get("expiration_release") or []}
        for b in (p.get("buckets") or {}).values():
            exps |= set(b.get("expiries") or [])
        listed = tgt in exps
    if not listed:
        return False
    rule = str((cfg or {}).get("expiry_sessions") or "monthly")
    if rule == "any" or not tgt:
        return rule == "any"
    d = dt.date.fromisoformat(tgt)
    if rule == "friday":
        return d.weekday() == 4
    # "monthly" (ruled 17 Oct 2026): the monthly third Friday only.
    first = d.replace(day=1)
    return d == first + dt.timedelta(days=(4 - first.weekday()) % 7 + 14)


def _stamp(head: str, cfg: dict) -> str:
    return f"{head} ({cfg.get('inferred_stamp') or 'inferred, not observed'})"


# ---------------------------------------------------------------------------
# T1 -- the dashboard, and the quality panel
# ---------------------------------------------------------------------------
def _windows(p: dict, cfg: dict) -> list[dict]:
    order = [w["id"] for w in (cfg.get("horizon_windows") or {}).get("windows") or []]
    hz = p.get("horizons") or {}
    return [hz[i] for i in (order or list(hz)) if i in hz]


def _col_head(w: dict) -> str:
    # A 0DTE gamma figure never prints without its OI vintage (brief section 1).
    return (f"{w['label']} (OI as of prior close)" if w.get("max_dte") == 0
            and not w.get("excluded") else w["label"])


def t1(p: dict, cfg: dict) -> dict:
    ws = _windows(p, cfg)
    spot = p.get("spot")

    def cell(w: dict, fn) -> str:
        return "settled, excluded" if w.get("excluded") else fn(w)

    def lvl(key):
        return lambda w: (f"{price(w.get(key))} ({dist(w.get(key), spot)})"
                          if w.get(key) is not None else "none in range")

    def flip(w):
        if w.get("gamma_flip") is None:
            return f"none ({str(w.get('flip_reason') or 'no crossing').replace('_', ' ')})"
        return f"{price(w['gamma_flip'])} ({dist(w['gamma_flip'], spot)})"

    rows = [
        ["Call-gamma mass ($/1%)"] + [cell(w, lambda w: usd(w.get("call_gamma_per_1pct")))
                                      for w in ws],
        ["Put-gamma mass ($/1%)"] + [cell(w, lambda w: usd(w.get("put_gamma_per_1pct")))
                                     for w in ws],
        ["Zero-gamma (balance) level"] + [cell(w, flip) for w in ws],
        ["Net GEX ($/1%), net-to-gross"] + [
            cell(w, lambda w: f"{usd(w.get('dollar_gamma_per_1pct'), True)} "
                              f"({pct(w.get('net_to_gross'))})") for w in ws],
        ["Regime (gated)"] + [cell(w, lambda w: regime(w.get("net_gex"),
                                                       w.get("net_to_gross"), cfg))
                              for w in ws],
        ["OTM call wall"] + [cell(w, lvl("call_wall_otm")) for w in ws],
        ["OTM put gamma wall"] + [cell(w, lvl("put_wall_otm")) for w in ws],
        ["Hedge-book size (DEX)"] + [cell(w, lambda w: usd(w.get("dex_notional")))
                                     for w in ws],
        ["Share of the hedge book"] + [cell(w, lambda w: pct(w.get("share_of_abs_dex")))
                                       for w in ws],
        ["OI balance (Σ Δ·OI, calls − puts)"] + [
            cell(w, lambda w: shares(w.get("oi_delta_balance_shares"))) for w in ws],
    ]
    head = _stamp(f"{p.get('symbol')} at {price(spot)}", cfg)
    return {"columns": [head] + [_col_head(w) for w in ws], "rows": rows}


def reconciliation(p: dict) -> dict:
    """The exclusive bands against "All": each additive figure's band sum, the
    All figure and the gap. A settled capture's 0DTE band is excluded from both,
    so the live bands must sum to All by construction; a gap is a fault."""
    bands = [b for b in (p.get("bands") or {}).values() if not b.get("excluded")]
    whole = (p.get("horizons") or {}).get("all") or {}
    out = {}
    for k in ("call_gamma_per_1pct", "put_gamma_per_1pct", "dex_notional"):
        tot = sum(b.get(k) or 0.0 for b in bands)
        ref = whole.get(k)
        out[k] = {"bands": tot, "all": ref,
                  "gap_pct": (abs(tot - ref) / abs(ref) * 100.0) if ref else None}
    out["ok"] = all(v["gap_pct"] is None or v["gap_pct"] < 0.01
                    for v in out.values() if isinstance(v, dict))
    return out


def reconciliation_line(p: dict) -> str:
    r = reconciliation(p)
    live = [b["label"] for b in (p.get("bands") or {}).values() if not b.get("excluded")]
    gone = [b["label"] for b in (p.get("bands") or {}).values() if b.get("excluded")]
    parts = [f"{lab} {usd(r[k]['bands'])} of {usd(r[k]['all'])}"
             for k, lab in (("call_gamma_per_1pct", "call mass"),
                            ("put_gamma_per_1pct", "put mass"),
                            ("dex_notional", "hedge book"))]
    return (f"The bands ({', '.join(live)}"
            + (f"; {', '.join(gone)} settled, excluded" if gone else "")
            + f") sum to All: {'; '.join(parts)}"
            + ("." if r["ok"] else " -- THEY DO NOT RECONCILE."))


def quality_panel(p: dict, cfg: dict) -> dict:
    q, g = p.get("quality") or {}, p.get("gates") or {}
    liq, ivd = g.get("liquidity_floor") or {}, g.get("iv_dispersion") or {}
    hhi = g.get("oi_concentration") or {}
    skipped = {"no OI": q.get("skipped_no_oi", 0), "no IV": q.get("skipped_no_iv", 0),
               "IV above 500%": q.get("skipped_insane_iv", 0)}
    n_skip = sum(skipped.values())
    why = ", ".join(f"{k} {v:,}" for k, v in skipped.items() if v)
    rough = ivd.get("roughness")
    if rough is None:
        rough_s = f"not measured ({ivd.get('reason') or 'no series'})"
    else:
        verdict = ("within" if ivd.get("pass") else "above")
        rough_s = (f"{rough:.3f}, {verdict} the provisional {ivd.get('threshold')} "
                   f"(provisional until 60 captures are stored)")
    load = [k for k, b in (p.get("buckets") or {}).items() if b.get("min_t_load_bearing")]
    rows = [
        ["Capture", capture_label(p)],
        ["Convention", str(p.get("convention_version") or "n/a")],
        ["Greeks source", str(p.get("greeks_source") or "n/a")],
        ["Rows", f"{q.get('rows_in', 0):,} in; {q.get('exposure_rows', 0):,} exposure "
                 f"rows; {n_skip:,} skipped" + (f" ({why})" if why else "")],
        ["Settled 0DTE rows excluded", f"{q.get('settled_0dte_excluded_rows', 0):,}"],
        ["Data quality", f"{g.get('data_quality') or 'n/a'}; "
                         + ("liquidity floor passed" if liq.get("pass")
                            else "liquidity floor: " + "; ".join(liq.get("reasons") or
                                                                 ["not evaluated"]))],
        ["IV roughness", rough_s],
        ["OI concentration", (f"{hhi['effective_strikes']:,.1f} effective strikes"
                              if hhi.get("effective_strikes") else "n/a")],
        ["MIN_T load-bearing", ("yes: " + ", ".join(load)) if load else "no"],
        ["OI vintage", "prior close"],
        ["Bands", reconciliation_line(p)],
    ]
    return {"columns": [_stamp("Chain quality", cfg), "Reading"], "rows": rows}


# ---------------------------------------------------------------------------
# T4 -- changes since the equivalent capture
# ---------------------------------------------------------------------------
def _field(p: dict, key: str) -> Optional[float]:
    return (p.get("overall") or {}).get(key)


def find_equivalent(p: dict, earlier: list[dict], cfg: dict) -> tuple[Optional[dict], str]:
    """The prior capture in the same slot: `earlier` is every capture of the
    symbol on the prior sessions, any order. (profile or None, why)."""
    slot = slot_of(p, cfg)
    if slot is None:
        return None, "no equivalent capture (this capture has no declared slot)"
    sess = p.get("session_date") or ""
    cands = [e for e in earlier if not e.get("error")
             and (e.get("session_date") or "") < sess and slot_of(e, cfg) == slot]
    if not cands:
        return None, f"no equivalent capture (no prior {slot} capture)"
    return max(cands, key=lambda e: (e.get("session_date"), e.get("fetched_at") or "")), slot


def t4(p: dict, prior: Optional[dict], why: str, cfg: dict) -> dict:
    if prior is None:
        return {"lines": [why[:1].upper() + why[1:] + "."], "table": None}
    rows = []
    for key, lab, kind in FIELDS_T4:
        a, b = _field(p, key), _field(prior, key)
        if kind == "usd":
            fa, fb = usd(a, key == "dollar_gamma_per_1pct"), usd(b, key == "dollar_gamma_per_1pct")
            ch = usd(a - b, True) if None not in (a, b) else "n/a"
        elif kind == "share":
            fa, fb = pct(a), pct(b)
            ch = (f"{'+' if a >= b else '−'}{abs(a - b) * 100:.0f} pp"
                  if None not in (a, b) else "n/a")
        else:
            fa, fb = price(a), price(b)
            ch = (f"{'+' if a > b else '−' if a < b else ''}{abs(a - b):,.2f}"
                  if None not in (a, b) else ("new" if a is not None else "n/a"))
        rows.append([lab, fa, fb, ch])
    head = _stamp(f"Since {prior.get('session_date')} {slot_of(prior, cfg)}", cfg)
    return {"lines": [], "table": {"columns": [head, "This capture", "Equivalent",
                                               "Change"], "rows": rows}}


# ---------------------------------------------------------------------------
# T3 -- the horizon matrix (6b part 3; brief v2 section 2)
# ---------------------------------------------------------------------------
WINDOW_KEY = "dealer.window_gamma"


def implied_range(spot: Optional[float], iv_pct: Optional[float]) -> Optional[float]:
    """spot x IV x sqrt(1/252): the implied one-day range, in points."""
    if not spot or not iv_pct:
        return None
    return spot * iv_pct / 100.0 * (1.0 / 252.0) ** 0.5


def _nearest_level(w: dict, spot: float) -> tuple[Optional[str], Optional[float]]:
    lv = [(n, w.get(k)) for n, k in (("the OTM call wall", "call_wall_otm"),
                                     ("the OTM put gamma wall", "put_wall_otm"),
                                     ("the zero-gamma level", "gamma_flip"))
          if w.get(k) is not None]
    if not lv or not spot:
        return None, None
    return min(lv, key=lambda x: abs(x[1] - spot))


def t3(p: dict, cfg: dict, history: Optional[dict] = None,
       iv: Optional[tuple] = None, registered: int = 6, promoted: int = 0) -> dict:
    """Per horizon: the gamma sign with net-to-gross (gated), the magnitude
    against the series' own five-year percentile (with its n), the nearest
    major level and its distance, and the implied one-day range. `history`
    maps window id -> the stored $/1% values before this capture; `iv` is
    (iv_pct, source). No synthesis sentence until a registered hypothesis is
    promoted: until then the matrix ends on that line."""
    spot = p.get("spot")
    iv_pct, iv_src = (iv or (None, None))
    rng = implied_range(spot, iv_pct)
    rows, lines = [], []
    for w in _windows(p, cfg):
        if w.get("excluded"):
            rows.append([w["label"], "settled, excluded", "—", "—", "—"])
            lines.append(f"{w['label']}: settled, excluded.")
            continue
        reg = regime(w.get("net_gex"), w.get("net_to_gross"), cfg)
        mag = w.get("dollar_gamma_per_1pct")
        hist = [abs(x) for x in (history or {}).get(w["id"], []) if x is not None]
        n5 = hist[-1260:]
        pct_ = (round(100.0 * sum(1 for x in n5 if x <= abs(mag)) / len(n5))
                if n5 and mag is not None else None)
        mag_s = (f"{usd(mag, True)} per 1%"
                 + (f", {_ordinal(pct_)} percentile of {len(n5)} stored" if pct_ is not None
                    else ", no stored history yet"))
        name, lvl = _nearest_level(w, spot)
        near = f"{name} {price(lvl)} ({dist(lvl, spot)})" if name else "none in range"
        rng_s = (f"±{rng:.2f} ({iv_src})" if rng else "n/a")
        rows.append([w["label"], f"{reg} ({pct(w.get('net_to_gross'))})", mag_s, near, rng_s])
        lines.append(f"{w['label']}: {reg}; {mag_s}; nearest level {near}; implied "
                     f"one-day range {rng_s}.")
    tail = f"registered hypotheses: {registered}, none promoted" if not promoted else \
        f"registered hypotheses: {registered}, {promoted} promoted"
    # The stamp, and the OI vintage every 0DTE gamma figure carries (brief v2
    # section 1), on the lines as on the table's head.
    lines.insert(0, "Every level here is inferred, not observed; OI as of prior close.")
    lines.append(tail[0].upper() + tail[1:] + ".")
    return {"table": {"columns": [_stamp(f"Horizon, {p.get('symbol')}", cfg),
                                  "Gamma (net-to-gross)", "Magnitude ($/1%)",
                                  "Nearest level", "Implied one-day range"],
                      "rows": rows},
            "lines": lines, "tail": tail}


def t2_by_horizon(p: dict, cfg: dict) -> dict:
    """T2 per horizon (the Weekly): each window's OTM walls, zero-gamma level
    and peak-gamma strike -- the levels the windows store."""
    spot = p.get("spot")
    rows = []
    for w in _windows(p, cfg):
        if w.get("excluded"):
            rows.append([w["label"], "settled, excluded", "—", "—", "—"])
            continue
        cell = lambda k: (f"{price(w.get(k))} ({dist(w.get(k), spot)})"  # noqa: E731
                          if w.get(k) is not None else "none")
        rows.append([w["label"], cell("call_wall_otm"), cell("put_wall_otm"),
                     cell("gamma_flip"), cell("peak_abs_gex_strike")])
    return {"columns": [_stamp(f"Key levels by horizon, {p.get('symbol')}", cfg),
                        "OTM call wall", "OTM put gamma wall", "Zero-gamma",
                        "Peak-gamma strike"], "rows": rows}


def window_rows(p: dict, now: str) -> list[dict]:
    """The capture's per-window $/1% as stored series (T3's percentile history):
    instrument '<symbol>:<window>', observed on the session."""
    out = []
    for w in (p.get("horizons") or {}).values():
        if w.get("excluded") or w.get("dollar_gamma_per_1pct") is None:
            continue
        out.append({"registry_key": WINDOW_KEY, "instrument": f"{p['symbol']}:{w['id']}",
                    "observed_at": p.get("session_date"), "available_at": now,
                    "value": float(w["dollar_gamma_per_1pct"]), "source": "daily_close"})
    return out


def window_history(st, cutoff: str, p: dict) -> dict:
    """{window id: [stored $/1% values before this capture's session]}."""
    out = {}
    for wid in (p.get("horizons") or {}):
        out[wid] = [float(r["value_num"]) for r in
                    st.as_of(WINDOW_KEY, cutoff, f"{p['symbol']}:{wid}")
                    if r.get("value_num") is not None
                    and str(r["observed_at"])[:10] < str(p.get("session_date"))]
    return out


def implied_vol(st, cutoff: str) -> tuple:
    """(IV %, source): SPY's own ATM 30-day IV, else the VIX labelled proxy."""
    for key, src in (("chain.spy_atm_iv_30d", "SPY ATM 30-day IV"),
                     ("yfinance.mkt_vix", "VIX as proxy")):
        r = st.latest_as_of(key, cutoff, "SPY" if key.startswith("chain.") else None)
        if r and r.get("value_num"):
            return float(r["value_num"]), src
    return None, None


# ---------------------------------------------------------------------------
# T2 -- key levels (the close: all expiries)
# ---------------------------------------------------------------------------
def t2(p: dict, cfg: dict) -> dict:
    o, spot = p.get("overall") or {}, p.get("spot")
    gross = o.get("gross_gex_abs")
    per = {s["strike"]: s for s in p.get("per_strike") or []}
    rd = cfg.get("readings") or {}
    expiry = expiry_on_target(p, cfg)

    def gam(k):
        s = per.get(k)
        if s is None or not spot:
            return "n/a"
        return (f"{usd(s.get('call_gex', 0.0) * 0.01 * spot)} / "
                f"{usd(abs(s.get('put_gex', 0.0)) * 0.01 * spot)}")

    def share(k):
        s = per.get(k)
        if s is None or not gross:
            return "n/a"
        return pct((s.get("call_gex", 0.0) + abs(s.get("put_gex", 0.0))) / gross, 1)

    def row(name, k, rid):
        if k is None:
            return [name, "none", "n/a", "n/a", "n/a", rd.get(rid, "")]
        return [name, price(k), gam(k), dist(k, spot), share(k), rd.get(rid, "")]

    rows = [row("OTM call wall", o.get("call_wall_otm"), "call_wall_otm"),
            row("Secondary call concentration", o.get("call_concentration_otm_2"),
                "call_concentration_2"),
            ["Zero-gamma level", price(o.get("gamma_flip")) if o.get("gamma_flip")
             else "none", "—", dist(o.get("gamma_flip"), spot), "—",
             rd.get("gamma_flip", "")],
            ["Spot", price(spot), "—", "—", "—", rd.get("spot", "")],
            row("Secondary put concentration", o.get("put_concentration_otm_2"),
                "put_concentration_2"),
            row("OTM put gamma wall", o.get("put_wall_otm"), "put_wall_otm"),
            row("Peak-gamma strike", o.get("peak_abs_gex_strike"), "peak_abs_gex_strike"),
            row("Peak put-gamma strike", o.get("put_wall_gamma"), "peak_put_gamma_strike"),
            row("Put OI shelf", o.get("put_wall_oi"), "put_oi_shelf"),
            (row(f"Max pain ({target_session(p)} expiry)", p.get("max_pain"), "max_pain")
             if expiry else ["Max pain", "not an expiry", "—", "—", "—",
                             rd.get("max_pain", "")]),
            row("Peak call-GEX strike (all strikes)", o.get("peak_call_gex_strike"),
                "peak_abs_gex_strike"),
            row("Peak put-GEX strike (all strikes)", o.get("peak_put_gex_strike"),
                "peak_abs_gex_strike")]
    # The all-strike extremes are peaks, never walls (audit F5): their reading
    # says so rather than borrowing the peak-gamma strike's.
    for r in rows[-2:]:
        r[-1] = "an all-strike extreme: a peak, not a wall (audit F5)"
    return {"columns": [_stamp(f"Key levels, {p.get('symbol')}", cfg), "Strike",
                        "Call / put gamma ($/1%)", "From spot", "Share of gross",
                        "Reading"], "rows": rows}


# ---------------------------------------------------------------------------
# The decision summary
# ---------------------------------------------------------------------------
def setups(p: dict, prior: Optional[dict], cfg: dict,
           releases: Optional[list[str]] = None) -> list[dict]:
    """The setups whose conditions hold, each with its level, invalidation and
    time stop. [] when none does."""
    o, spot = p.get("overall") or {}, p.get("spot")
    sc = cfg.get("setups") or {}
    sign = regime_sign(o.get("net_gex"), o.get("net_to_gross"), cfg)
    flip = o.get("gamma_flip")
    out: list[dict] = []
    expiry = expiry_on_target(p, cfg)
    tgt = target_session(p)
    peak = o.get("peak_abs_gex_strike")
    pf = sc.get("c_pin_fade") or {}
    if expiry and sign == "positive" and peak and spot \
            and abs(spot / peak - 1.0) * 100.0 <= float(pf.get("near_peak_pct", 0.5)):
        out.append({"id": "c_pin_fade", "level": peak,
                    "level_name": "the peak-gamma strike",
                    "why": (f"{tgt} is an expiry session, gamma is positive, and the "
                            f"peak-gamma strike is {dist(peak, spot)} from spot"),
                    "invalidation": (f"spot through the zero-gamma level at {price(flip)}"
                                     if flip else "the regime turning indeterminate or "
                                     "negative"),
                    "time_stop": pf.get("time_stop", "the expiry session's close")})
    nc = sc.get("c_negative_gamma_continuation") or {}
    if sign == "negative" and prior and prior.get("spot") and spot:
        conf = float(nc.get("confirm_pct", 0.10)) / 100.0
        for key in nc.get("levels") or ["gamma_flip", "put_wall_otm", "call_wall_otm"]:
            lv = o.get(key)
            if lv is None:
                continue
            was, now = prior["spot"], spot
            down = was >= lv and now <= lv * (1.0 - conf)
            up = was <= lv and now >= lv * (1.0 + conf)
            if down or up:
                names = {"gamma_flip": "the zero-gamma level", "put_wall_otm":
                         "the OTM put gamma wall", "call_wall_otm": "the OTM call wall"}
                out.append({"id": "c_negative_gamma_continuation", "level": lv,
                            "level_name": names.get(key, key),
                            "why": (f"negative gamma, and spot {'down' if down else 'up'} "
                                    f"through {names.get(key, key)} since the equivalent "
                                    f"capture ({price(was)} to {price(now)})"),
                            "invalidation": f"spot back through {price(lv)}",
                            "time_stop": nc.get("time_stop", "two sessions")})
                break
    ff = sc.get("d_forced_flow") or {}
    if expiry and peak:
        mp = p.get("max_pain")
        near = float(pf.get("near_peak_pct", 0.5))
        out.append({"id": "d_forced_flow", "level": peak,
                    "level_name": "the peak-gamma strike"
                                  + (f"; max pain {price(mp)} the control" if mp else ""),
                    "why": f"{tgt} is an expiry session",
                    "invalidation": (f"the session trading more than {near:g}% from "
                                     f"{price(peak)} into the final hour"),
                    "time_stop": ff.get("time_stop_expiry", "the closing auction")})
    if releases:
        walls = [x for x in (o.get("put_wall_otm"), o.get("call_wall_otm")) if x]
        out.append({"id": "d_forced_flow", "level": walls[0] if walls else None,
                    "level_name": ("the OTM walls " + " and ".join(price(w) for w in walls)
                                   if walls else "no OTM wall in range"),
                    "why": f"{tgt} is a release day: " + ", ".join(releases),
                    "invalidation": "spot beyond either wall",
                    "time_stop": ff.get("time_stop_release", "the release session's close")})
    return out


def summary(p: dict, prior: Optional[dict], cfg: dict,
            releases: Optional[list[str]] = None) -> dict:
    o, spot = p.get("overall") or {}, p.get("spot")
    names = setup_names()
    reg = regime(o.get("net_gex"), o.get("net_to_gross"), cfg)
    flip = o.get("gamma_flip")
    lines = [f"For {target_session(p)}. Regime: {reg}; "
             + (f"the zero-gamma level {price(flip)} is {dist(flip, spot)} from spot."
                if flip else "no zero-gamma level within 15% of spot."),
             f"Walls: OTM call wall {price(o.get('call_wall_otm'))} "
             f"({dist(o.get('call_wall_otm'), spot)}), OTM put gamma wall "
             f"{price(o.get('put_wall_otm'))} ({dist(o.get('put_wall_otm'), spot)})."]
    found = setups(p, prior, cfg, releases)
    for s in found:
        n = names.get(s["id"]) or {}
        lines.append(f"Setup {s['id']} ({n.get('name', s['id'])}, Book {n.get('book')}): "
                     f"{s['why']}; level {price(s['level'])} ({s['level_name']}); "
                     f"invalidation: {s['invalidation']}; time stop: {s['time_stop']}.")
    if not found:
        lines.append("No setup: none of c_pin_fade, c_negative_gamma_continuation or "
                     "d_forced_flow holds.")
    lines.append("Every level here is inferred, not observed. The block proposes; the "
                 "books decide; nothing here writes the register.")
    return {"lines": lines, "setups": found, "regime": reg}


# ---------------------------------------------------------------------------
# The whole block, for the close's Mechanics section
# ---------------------------------------------------------------------------
def block(p: dict, prior: Optional[dict], why: str = "no equivalent capture",
          cfg: Optional[dict] = None, releases: Optional[list[str]] = None,
          t3ctx: Optional[dict] = None) -> dict:
    """{"subsections", "summary", "notes", "fingerprint", "data"} for one
    symbol's capture, or {"absent": reason} when the profile cannot carry it."""
    cfg = cfg if cfg is not None else config()
    sym = p.get("symbol") if p else None
    if not p or p.get("error"):
        return {"absent": f"dealer block, {sym or 'SPY'}: "
                          f"{(p or {}).get('error') or 'no computed profile'}"}
    s = summary(p, prior, cfg, releases)
    four = t4(p, prior, why, cfg)
    # A profile computed before 6b carries no horizon windows: T1 says so and
    # waits for the next capture, rather than printing an empty table.
    dash = ({"title": f"Dealer dashboard, {sym}", "table": t1(p, cfg)}
            if p.get("horizons") else
            {"title": f"Dealer dashboard, {sym}", "table": None,
             "lines": ["This capture was computed before the horizon windows "
                       "existed (6b); the next capture carries them."]})
    subs = [dash,
            {"title": f"Chain quality, {sym}", "table": quality_panel(p, cfg)},
            {"title": f"Changes since the equivalent capture, {sym}",
             "table": four["table"], "lines": four["lines"]},
            {"title": f"Key levels, {sym}", "table": t2(p, cfg)}]
    # T3, THE HORIZON MATRIX (6b part 3): the close prints it as lines.
    if p.get("horizons"):
        m = t3(p, cfg, (t3ctx or {}).get("history"), (t3ctx or {}).get("iv"))
        subs.append({"title": f"Horizon matrix, {sym}", "table": None,
                     "lines": m["lines"]})
    subs.append({"title": f"Decision summary, {sym}", "lines": s["lines"]})
    o = p.get("overall") or {}
    return {"subsections": subs, "summary": s,
            "notes": [cfg.get("convention_line") or ""],
            # The three fixed sentences' facts (brief v2 section 4): the model
            # writes them in the section's paragraph, behind the audits.
            "sentences": sentence_facts(p, s, cfg),
            "fingerprint": [o.get(k) for k in ("net_gex", "gamma_flip", "call_wall_otm",
                                               "put_wall_otm", "peak_abs_gex_strike")]
                           + [x["id"] for x in s["setups"]],
            "data": {"symbol": sym, "capture": capture_label(p),
                     "target_session": target_session(p),
                     "slot": slot_of(p, cfg), "regime": s["regime"],
                     "setups": s["setups"], "equivalent": (prior or {}).get("fetched_at"),
                     "reconciliation": reconciliation(p)}}


# ---------------------------------------------------------------------------
# The three fixed sentences' facts, and the flag-word audit (6b part 2)
# ---------------------------------------------------------------------------
def sentence_facts(p: dict, s: dict, cfg: dict) -> dict:
    """What the three fixed sentences of the brief's section 4 may cite, each
    figure exactly as the tables print it: (1) the regime with net-to-gross,
    the zero-gamma level's distance and the +/-1% asymmetry; (2) the two OTM
    walls, the peak-gamma strike, which expiry carries it and the size rolling
    off at the next expiry; (3) the setups whose conditions hold, or none, with
    the invalidating level. The model writes them in the existing narrative
    step, behind the numeral and flag-word audits."""
    o, spot = p.get("overall") or {}, p.get("spot")
    up, dn = o.get("net_gex_up_1pct"), o.get("net_gex_down_1pct")
    rel = (p.get("expiration_release") or [None])[0] or {}
    return {
        "sentence_1": {"regime": s["regime"], "net_to_gross": pct(o.get("net_to_gross")),
                       "zero_gamma_level": price(o.get("gamma_flip")),
                       "zero_gamma_from_spot": dist(o.get("gamma_flip"), spot),
                       "net_gex_at_spot": usd((o.get("net_gex") or 0) * 0.01 * spot, True)
                       if o.get("net_gex") is not None and spot else "n/a",
                       "net_gex_if_spot_up_1pct": usd(up * 0.01 * spot * 1.01, True)
                       if up is not None and spot else "n/a",
                       "net_gex_if_spot_down_1pct": usd(dn * 0.01 * spot * 0.99, True)
                       if dn is not None and spot else "n/a"},
        "sentence_2": {"otm_call_wall": price(o.get("call_wall_otm")),
                       "otm_put_gamma_wall": price(o.get("put_wall_otm")),
                       "peak_gamma_strike": price(o.get("peak_abs_gex_strike")),
                       "expiry_carrying_the_peak": p.get("expiry_type") or "n/a",
                       "next_expiry": rel.get("expiry") or "n/a",
                       "hedge_rolling_off_at_next_expiry": usd(abs(rel["dex_notional"]))
                       if rel.get("dex_notional") is not None else "n/a"},
        "sentence_3": {"setups": [{"setup": x["id"], "level": price(x["level"]),
                                   "invalidation": x["invalidation"]}
                                  for x in s["setups"]] or "no setup",
                       "for_session": target_session(p)},
    }


FLAG_WORD = re.compile(r"\b(pinned|pinning|held|amplif(?:ied|ies|y|ying)"
                       r"|dampen(?:ed|s|ing)?)\b", re.I)
# "held" is ordinary English ("the relationships that held"); it is the flag
# word only about a dealer level -- a wall, the flip, a strike, max pain.
_DEALER_LEVEL = re.compile(r"\b(walls?|flip|zero-gamma|strike|max pain|peak|"
                           r"gamma level|shelf)\b", re.I)
_MON = "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
_WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday")


def _flag_kind(word: str) -> str:
    w = word.lower()
    return ("pinned" if w.startswith("pin") else "amplified" if w.startswith("amplif")
            else "dampened" if w.startswith("dampen") else "held")


def _named_sessions(sentence: str, sessions: list[dict]) -> list[dict]:
    """The sessions a sentence names: an ISO date, '16 Oct' / 'Oct 16', or a
    weekday (the week's own)."""
    out = []
    for r in sessions:
        d = dt.date.fromisoformat(str(r["session"])[:10])
        forms = [d.isoformat(), f"{d.day} {d:%b}", f"{d:%b} {d.day}",
                 _WEEKDAYS[d.weekday()] if d.weekday() < 5 else "\0"]
        if any(re.search(rf"\b{re.escape(f)}\b", sentence, re.I) for f in forms):
            out.append(r)
    return out


def flag_word_faults(text: Optional[str], sessions: Optional[list[dict]]) -> list[str]:
    """THE FLAG-WORD AUDIT (brief v2 section 4, extended to 'dampened' in 6b
    part 2): 'pinned', 'held', 'amplified' and 'dampened' only in a sentence
    that names a session whose flag for that word is True. 'held' is the flag
    word only in a sentence about a dealer level (a wall, the flip, a strike,
    max pain); elsewhere it is ordinary English. `sessions` are the
    scored rows ({"session", "flags"}); None or empty -- the close, whose
    session's flags are computed after its prose -- withholds every flag word."""
    out = []
    for s in re.split(r"(?<=[.!?])\s+", text or ""):
        kinds = {_flag_kind(m.group(1)) for m in FLAG_WORD.finditer(s)}
        if "held" in kinds and not _DEALER_LEVEL.search(s):
            kinds.discard("held")
        if not kinds:
            continue
        named = _named_sessions(s, sessions or [])
        for k in sorted(kinds):
            ok = any(bool((r.get("flags") or {}).get(k)) if k != "held" else
                     bool((r.get("flags") or {}).get("call_wall_held")
                          or (r.get("flags") or {}).get("put_wall_held"))
                     for r in named)
            if not ok:
                out.append(f"flag word '{k}' without a session whose {k} flag is set: "
                           f"'{s[:100]}'")
    return out


# ---------------------------------------------------------------------------
# IO: the stored captures (read-only)
# ---------------------------------------------------------------------------
def captures_on(day: str, symbol: str, base_dir: Optional[str] = None) -> list[dict]:
    """Every computed profile of `symbol` stored for session `day`."""
    from altdata import config as acfg                          # noqa: PLC0415
    d = Path(base_dir or acfg.COMPUTED_DIR) / day
    out = []
    for f in sorted([*d.glob(f"{symbol}_*_exposure.json"), *d.glob(f"{symbol}_*_gex.json")]):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if (rec.get("session_date") or day) == day:
            out.append(rec)
    return out


def chart_dir(computed_dir: Optional[str], day: Optional[str],
              lookback_days: int = 7) -> Optional[str]:
    """`computed_dir` when it holds a settled SPY capture on or before `day`
    (within `lookback_days`), else None: a dealer chart enters a plan only
    when there is a profile to draw."""
    if not computed_dir or not day:
        return None
    try:
        return computed_dir if newest_settled(str(day)[:10], "SPY", computed_dir,
                                              lookback_days) else None
    except Exception:                                           # noqa: BLE001
        return None


def newest_settled(day: str, symbol: str = "SPY", base_dir: Optional[str] = None,
                   lookback_days: int = 7) -> Optional[dict]:
    """The newest settled capture of `symbol` on `day` or the days before it
    (up to `lookback_days`): the Weekly's and the Monthly's dealer charts read
    the period's last close. None when there is none."""
    d = dt.date.fromisoformat(day[:10])
    for _ in range(lookback_days + 1):
        caps = [c for c in captures_on(d.isoformat(), symbol, base_dir)
                if not c.get("error") and c.get("capture") == "settled_eod"]
        if caps:
            return max(caps, key=lambda c: c.get("fetched_at") or "")
        d -= dt.timedelta(days=1)
    return None


def for_session(sess: str, base_dir: Optional[str] = None,
                releases: Optional[list[str]] = None,
                cfg: Optional[dict] = None, st=None,
                cutoff: Optional[str] = None) -> list[dict]:
    """The block for each configured symbol's newest capture of `sess`, with
    its equivalent capture found on the prior sessions. `releases` are the
    tier-1 releases on the capture's TARGET session (target_session)."""
    from altdata import session                                 # noqa: PLC0415
    cfg = cfg if cfg is not None else config()
    out = []
    for sym in cfg.get("symbols") or ["SPY"]:
        caps = [c for c in captures_on(sess, sym, base_dir) if not c.get("error")]
        if not caps:
            out.append({"absent": f"dealer block, {sym}: no computed profile for {sess}"})
            continue
        cur = max(caps, key=lambda c: c.get("fetched_at") or "")
        earlier, d = [], dt.date.fromisoformat(sess)
        for _ in range(int(cfg.get("equivalent_lookback_sessions", 3))):
            d = session.previous_trading_session(d.isoformat())
            earlier += captures_on(d.isoformat(), sym, base_dir)
        prior, why = find_equivalent(cur, earlier, cfg)
        t3ctx = None
        if st is not None and cutoff:
            # T3's history and IV; a store that cannot answer leaves T3 with
            # "no stored history yet" rather than the block absent.
            try:
                t3ctx = {"history": window_history(st, cutoff, cur),
                         "iv": implied_vol(st, cutoff)}
            except Exception:                                   # noqa: BLE001
                t3ctx = None
        b = block(cur, prior, why if prior is None else "", cfg, releases, t3ctx)
        b["_window_rows"] = cur
        out.append(b)
    return out


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    from altdata import session                                 # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m daily_cascade.dealer_block")
    ap.add_argument("cmd", choices=["show"])
    ap.add_argument("--date", default=None)
    a = ap.parse_args(argv)
    sess = a.date or session.session_date()
    for b in for_session(sess):
        if b.get("absent"):
            print(b["absent"])
            continue
        for ss in b["subsections"]:
            print(f"\n{ss['title']}")
            t = ss.get("table")
            if t:
                print(" | ".join(t["columns"]))
                for r in t["rows"]:
                    print(" | ".join(str(x) for x in r))
            for ln in ss.get("lines") or []:
                print(ln)
        print("\n" + "\n".join(b["notes"]))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_main(sys.argv[1:]))
