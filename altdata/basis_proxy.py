"""
THE TREASURY BASIS-TRADE PROXY (SR-36; ST-B3-12) AND ITS CALIBRATION LEDGER
(ST-B3-14). Ruled 6 Oct 2026 (batch-3 change order, section 7 decisions 8, 9).

    python -m altdata.basis_proxy show   [--day 2026-10-06]   # the week's read
    python -m altdata.basis_proxy ledger [--out PATH]         # ST-B3-14

Config: config/basis_proxy.yaml. Source: the CFTC's Traders in Financial
Futures report, futures only, for TU, FV, TY, TN, US and WN -- stored by
altdata/sources/cftc.py (the one CFTC writer) as cftc.tff_* under instrument =
the contract. Nothing here fetches.

WHAT THE SERIES IS. The leveraged-fund short in Treasury futures is the futures
leg of the cash-futures basis trade: long cash Treasuries, repo-financed, short
futures -- duration-neutral by construction. It is NOT a directional short, and
it is never printed as one ("hedge funds are short bonds"). What it measures is
FRAGILITY: the size of the leveraged position sets how violent a vol or funding
shock becomes, because a forced unwind sells the repo-financed cash leg.

THE MEASURES.
  (a) leveraged-fund net short across the six contracts as a share of their
      combined open interest, contract-weighted and DV01-weighted (DV01 per
      contract: config, session-set, a CTD-duration approximation);
  (b) the asset-manager net long, the mirror, both weightings;
  (c) (a) and (b) per contract, for tenor concentration;
  (d) the week's change in the aggregate leveraged net short against the change
      in open interest, as a code-written label: "deleveraging" (short down, OI
      down), "covering" (short down, OI flat or up), "building" (short up, OI
      up), "adding" (short up, OI flat or down), "unchanged" (short flat);
  (e) five-year and full-history percentiles of both shares.
  TIERS: the 10-year at 35% "elevated" and 40% "extreme"; the aggregate at its
  own 90th and 97th full-history percentiles, from the history knowable that
  week -- never fixed numbers.
  BASIS-UNWIND WATCH: a COINCIDENCE flag only -- a level flag on either series
  plus at least two of: SR-35 at 2 sigma; MOVE's one-month change at 2 sigma;
  SOFR-IORB widening at 2 sigma (or a sponsored-repo shock); the 10-year swap
  spread's two-week change beyond 2 sigma; and, from Batch 5 item 27 (ST-R4.27a,
  16 Oct 2026), TLT's 20-session overnight leg at -2 sigma (altdata.batch5b,
  hooked by name). A co-signal not stored is absent and
  named. Every line it prints carries "(descriptive; unvalidated, n=0)".

REPORT-ONLY. No overlay wiring, no trigger, no book rule.
"""

from __future__ import annotations

import datetime as dt
import importlib
import math
import statistics
from pathlib import Path
from typing import Any, Optional

import yaml

from . import derived

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "basis_proxy.yaml"
TAG = "(descriptive; unvalidated, n=0)"
KEYS = {"lev_net": "cftc.tff_lev_money_net", "am_net": "cftc.tff_asset_mgr_net",
        "oi": "cftc.tff_open_interest"}


def load_config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _rows(st, key: str, cutoff: Optional[str], inst: Optional[str] = None
          ) -> dict[str, float]:
    out = {}
    for r in st.as_of(key, cutoff, inst):
        v = r.get("value_num")
        if v is not None:
            out[str(r["observed_at"])[:10]] = float(v)
    return out


# ---------------------------------------------------------------------------
# The weekly table: (a), (b), (c)
# ---------------------------------------------------------------------------
def share(num: float, den: float) -> Optional[float]:
    return None if not den else 100.0 * num / den


def week_shares(per: dict[str, dict], dv01: dict[str, float]) -> dict:
    """One report week's shares from {contract: {lev_net, am_net, oi}}: the
    leveraged net SHORT (positive when short) and the asset-manager net long, as
    percent of open interest, summed contract-weighted and DV01-weighted, and per
    contract. Contracts missing that week are left out of both sums."""
    live = {c: v for c, v in per.items()
            if v.get("oi") and v.get("lev_net") is not None
            and v.get("am_net") is not None}
    oi = sum(v["oi"] for v in live.values())
    w = {c: float(dv01.get(c) or 0.0) for c in live}
    oi_w = sum(live[c]["oi"] * w[c] for c in live)
    lev_short = -sum(v["lev_net"] for v in live.values())
    am_long = sum(v["am_net"] for v in live.values())
    return {
        "contracts": sorted(live),
        "oi": oi,
        "lev_short": lev_short,
        "lev_short_oi": share(lev_short, oi),
        "lev_short_oi_dv01": share(-sum(live[c]["lev_net"] * w[c] for c in live), oi_w),
        "am_long_oi": share(am_long, oi),
        "am_long_oi_dv01": share(sum(live[c]["am_net"] * w[c] for c in live), oi_w),
        "per_contract": {c: {"lev_short_oi": share(-v["lev_net"], v["oi"]),
                             "am_long_oi": share(v["am_net"], v["oi"]),
                             "oi": v["oi"]} for c, v in sorted(live.items())},
    }


def history(st, cutoff: Optional[str] = None, cfg: Optional[dict] = None) -> list[dict]:
    """Every report week knowable at `cutoff`, oldest first, from the store:
    [{day, **week_shares}]."""
    cfg = cfg or load_config()
    dv01 = {c: v["usd_per_bp"] for c, v in
            ((cfg.get("dv01") or {}).get("per_contract") or {}).items()}
    raw: dict[str, dict[str, dict]] = {}
    for c in cfg.get("contracts") or []:
        for f, key in KEYS.items():
            for d, v in _rows(st, key, cutoff, c).items():
                raw.setdefault(d, {}).setdefault(c, {})[f] = v
    start = str(cfg.get("history_start") or "2010-03-02")
    return [{"day": d, **week_shares(raw[d], dv01)} for d in sorted(raw) if d >= start]


# ---------------------------------------------------------------------------
# (d) the OI-change label; (e) percentiles; the tiers
# ---------------------------------------------------------------------------
def oi_change_label(d_short: float, prev_short: float, d_oi: float, prev_oi: float,
                    flat_pct: float = 1.0) -> str:
    """The week's change in the leveraged net short against the change in open
    interest, as a code-written label."""
    def way(d, base):
        if not base or abs(d) < abs(base) * flat_pct / 100.0:
            return 0
        return 1 if d > 0 else -1
    s, o = way(d_short, prev_short), way(d_oi, prev_oi)
    if s == 0:
        return "unchanged"
    if s < 0:
        return "deleveraging" if o < 0 else "covering"
    return "building" if o > 0 else "adding"


def _pct(hist: list[float], x: Optional[float]) -> Optional[float]:
    if x is None or not hist:
        return None
    return derived.percentile_of(hist, x)


def _value_at(hist: list[float], pct: float) -> Optional[float]:
    """The `pct`th percentile of `hist`, nearest rank."""
    if not hist:
        return None
    s = sorted(hist)
    k = max(0, min(len(s) - 1, math.ceil(pct / 100.0 * len(s) - 1e-9) - 1))
    return s[k]


def ten_year_tier(share_: Optional[float], cfg: dict) -> Optional[str]:
    t = (cfg.get("tiers") or {}).get("ten_year") or {}
    if share_ is None:
        return None
    if share_ >= float(t.get("extreme", 40.0)):
        return "extreme"
    if share_ >= float(t.get("elevated", 35.0)):
        return "elevated"
    return None


def aggregate_tier(share_: Optional[float], hist: list[float], cfg: dict
                   ) -> tuple[Optional[str], dict]:
    """The aggregate's tier against its own full history, the 90th and 97th
    percentiles computed from `hist` (the history knowable that week)."""
    t = (cfg.get("tiers") or {}).get("aggregate") or {}
    p90 = _value_at(hist, float(t.get("elevated_percentile", 90)))
    p97 = _value_at(hist, float(t.get("extreme_percentile", 97)))
    th = {"p90": p90, "p97": p97}
    if share_ is None or p90 is None:
        return None, th
    if share_ >= p97:
        return "extreme", th
    if share_ >= p90:
        return "elevated", th
    return None, th


def read(st, day: Optional[str] = None, cutoff: Optional[str] = None,
         cfg: Optional[dict] = None, hist: Optional[list[dict]] = None) -> Optional[dict]:
    """The proxy as of report Tuesday `day` (the latest knowable when None):
    shares, percentiles, tiers, the OI-change label and the unwind watch."""
    cfg = cfg or load_config()
    hist = hist if hist is not None else history(st, cutoff, cfg)
    weeks = [w for w in hist if day is None or w["day"] <= day]
    if not weeks:
        return None
    w, prev = weeks[-1], (weeks[-2] if len(weeks) > 1 else None)
    five = (dt.date.fromisoformat(w["day"]) - dt.timedelta(
        days=int(cfg.get("five_year_days") or 1826))).isoformat()
    agg_full = [x["lev_short_oi"] for x in weeks if x["lev_short_oi"] is not None]
    agg_5y = [x["lev_short_oi"] for x in weeks if x["day"] >= five
              and x["lev_short_oi"] is not None]
    tc = ((cfg.get("tiers") or {}).get("ten_year") or {}).get("contract", "TY")
    ty = [(x["day"], (x["per_contract"].get(tc) or {}).get("lev_short_oi"))
          for x in weeks]
    ty_full = [v for _, v in ty if v is not None]
    ty_5y = [v for d, v in ty if v is not None and d >= five]
    ty_now = (w["per_contract"].get(tc) or {}).get("lev_short_oi")
    agg_t, th = aggregate_tier(w["lev_short_oi"], agg_full, cfg)
    label = None
    if prev:
        label = oi_change_label(w["lev_short"] - prev["lev_short"], prev["lev_short"],
                                w["oi"] - prev["oi"], prev["oi"],
                                float(cfg.get("flat_pct") or 1.0))
    out = {**w, "ten_year_contract": tc, "ten_year_short_oi": ty_now,
           "pct_full": _pct(agg_full, w["lev_short_oi"]),
           "pct_5y": _pct(agg_5y, w["lev_short_oi"]),
           "ten_year_pct_full": _pct(ty_full, ty_now),
           "ten_year_pct_5y": _pct(ty_5y, ty_now),
           "full_since": weeks[0]["day"],
           "ten_year_tier": ten_year_tier(ty_now, cfg),
           "aggregate_tier": agg_t, "aggregate_thresholds": th,
           "oi_change": label}
    out["level_flag"] = bool(out["ten_year_tier"] or out["aggregate_tier"])
    out["watch"] = unwind_watch(st, w["day"], cutoff, cfg, out["level_flag"])
    return out


# ---------------------------------------------------------------------------
# The basis-unwind watch: a coincidence flag
# ---------------------------------------------------------------------------
def _daily(st, key: str, cutoff: Optional[str], day: str) -> list[tuple[str, float]]:
    return sorted((d, v) for d, v in _rows(st, key, cutoff).items() if d <= day)


def change_z(pts: list[tuple[str, float]], sessions: int, history_days: int
             ) -> Optional[float]:
    """The last `sessions`-session change as a z on the window's changes of
    that length (the last excluded)."""
    if len(pts) <= sessions + 30:
        return None
    lo = (dt.date.fromisoformat(pts[-1][0]) - dt.timedelta(days=history_days)).isoformat()
    vals = [v for _, v in pts]
    hist = [vals[i] - vals[i - sessions] for i in range(sessions, len(vals) - 1)
            if pts[i - sessions][0] >= lo]
    if len(hist) < 30:
        return None
    sd = statistics.pstdev(hist)
    if not sd:
        return None
    return (vals[-1] - vals[-1 - sessions] - statistics.fmean(hist)) / sd


def cosignals(st, day: str, cutoff: Optional[str], cfg: dict) -> dict[str, dict]:
    """The five co-signals on report Tuesday `day`: each {state: True, False or
    None (absent), why}."""
    u = cfg.get("unwind_watch") or {}
    sig = float(u.get("sigma") or 2.0)
    out: dict[str, dict] = {}
    # SR-35, by name.
    s = u.get("sr35") or {}
    try:
        mod = importlib.import_module(s.get("module") or "altdata.move_screen")
        fn = getattr(mod, s.get("function") or "companion_10y")
        res = fn(st, day, cutoff, mod.load_config())
        out["sr35"] = ({"state": None, "why": "the 10-year has too little history"}
                       if res is None else
                       {"state": bool(res.get("printed")), "why": res.get("line")})
    except (ImportError, AttributeError):
        out["sr35"] = {"state": None, "why": "absent: the move screen's SR-35 "
                                             "companion is not on this build"}
    # MOVE, one month.
    m = u.get("move") or {}
    pts = _daily(st, m.get("key") or "yfinance.mkt_move", cutoff, day)
    z = change_z(pts, int(m.get("sessions") or 21), int(m.get("history_days") or 1826))
    out["move"] = ({"state": None, "why": "absent: MOVE not stored for the window"}
                   if z is None else {"state": z >= sig, "z": round(z, 2),
                                      "why": f"MOVE one-month change {z:+.1f} sigma"})
    # SOFR less IORB, widening.
    f = u.get("funding") or {}
    sofr = dict(_daily(st, f.get("sofr") or "fred.sofr", cutoff, day))
    iorb = dict(_daily(st, f.get("iorb") or "fred.iorb", cutoff, day))
    spread = sorted((d, (sofr[d] - iorb[d]) * 100.0) for d in sofr if d in iorb)
    z = change_z(spread, int(f.get("sessions") or 10), int(f.get("history_days") or 1826))
    out["funding"] = ({"state": None, "why": "absent: SOFR or IORB not stored for "
                                             "the window (the sponsored-repo volume "
                                             "series is not stored)"}
                      if z is None else {"state": z >= sig, "z": round(z, 2),
                                         "why": f"SOFR less IORB two-week change "
                                                f"{z:+.1f} sigma"})
    # The 10-year swap spread.
    sw = u.get("swap_spread") or {}
    if not sw.get("key"):
        out["swap_spread"] = {"state": None, "why": "absent: the 10-year swap spread "
                                                   "is not stored"}
    else:
        pts = _daily(st, sw["key"], cutoff, day)
        z = change_z(pts, int(sw.get("sessions") or 10), int(sw.get("history_days") or 1826))
        out["swap_spread"] = ({"state": None, "why": "absent: the swap spread has too "
                                                    "little history"}
                              if z is None else {"state": abs(z) >= sig, "z": round(z, 2),
                                                 "why": f"10-year swap spread two-week "
                                                        f"change {z:+.1f} sigma"})
    # Batch 5 item 27 (ST-R4.27a): TLT's overnight leg, by name, like SR-35.
    o = u.get("overnight") or {}
    if o:
        try:
            mod = importlib.import_module(o.get("module") or "altdata.batch5b")
            out["overnight"] = getattr(mod, o.get("function") or "cosignal")(
                st, day, cutoff)
        except (ImportError, AttributeError):
            out["overnight"] = {"state": None, "why": "absent: the overnight split is "
                                                      "not on this build"}
    return out


def unwind_watch(st, day: str, cutoff: Optional[str], cfg: dict,
                 level_flag: bool) -> dict:
    sig = cosignals(st, day, cutoff, cfg)
    on = [k for k, v in sig.items() if v["state"] is True]
    absent = [k for k, v in sig.items() if v["state"] is None]
    need = int((cfg.get("unwind_watch") or {}).get("min_cosignals") or 2)
    return {"on": bool(level_flag and len(on) >= need), "level_flag": level_flag,
            "cosignals_on": on, "absent": absent, "detail": sig, "needed": need}


# ---------------------------------------------------------------------------
# The two Weekly lines, code-written
# ---------------------------------------------------------------------------
NAMES = {"sr35": "SR-35", "move": "MOVE", "funding": "SOFR less IORB",
         "swap_spread": "the swap spread", "overnight": "TLT's overnight leg"}


def _ordinal(p: Optional[float]) -> str:
    from .numeral_audit import percentile_ordinal               # noqa: PLC0415
    return "n/a" if p is None else percentile_ordinal(p)


def positioning_line(r: dict) -> str:
    """Positioning & flows: the size of the leveraged position. Four figures."""
    tier = r.get("ten_year_tier")
    agg = r.get("aggregate_tier")
    return (f"Treasury basis proxy, as of {r['day']}: leveraged funds' net short is "
            f"{r['ten_year_short_oi']:.1f}% of 10-year open interest"
            + (f" ({tier})" if tier else "")
            + f" and {r['lev_short_oi']:.1f}% across the six Treasury futures"
            + (f" ({agg})" if agg else "")
            + f", the {_ordinal(r.get('pct_full'))} percentile since "
              f"{r['full_since'][:4]}; {r.get('oi_change') or 'no prior week'} on the "
              f"week. The futures leg of the cash-futures basis trade: a fragility "
              f"read, not a direction {TAG}.")


def plumbing_line(r: dict) -> str:
    """Plumbing & rates: the coincidence flag and its co-signals."""
    w = r["watch"]
    on = [NAMES[k] for k in w["cosignals_on"]]
    absent = [NAMES[k] for k in w["absent"]]
    return ("Basis-unwind watch: " + ("ON" if w["on"] else "off") + " -- level flag "
            + ("on" if w["level_flag"] else "off") + "; co-signals at 2 sigma: "
            + (", ".join(on) if on else "none")
            + (f" (absent: {', '.join(absent)})" if absent else "")
            + f"; it needs a level flag and {w['needed']} co-signals together. A large "
              f"leveraged position sets how violent a vol or funding shock becomes "
              f"{TAG}.")


BASIS_NOTE = (
    "\n\nTHE TREASURY BASIS PROXY is the futures leg of the cash-futures basis "
    "trade -- long cash Treasuries, repo-financed, short futures, duration-"
    "neutral. Read it only as FRAGILITY: the size of the leveraged position sets "
    "how violent a vol or funding shock becomes. Never a directional reading: "
    "never 'hedge funds are short bonds', never a bet on yields, never a squeeze.")


# ---------------------------------------------------------------------------
# ST-B3-14: the calibration ledger
# ---------------------------------------------------------------------------
def _first(rows: list[dict], pred) -> Optional[str]:
    return next((r["day"] for r in rows if pred(r)), None)


def episode_verdict(rows: list[dict]) -> str:
    """Whether the unwind-watch flag led, coincided with or lagged the stress
    readings (MOVE, SOFR less IORB, the swap spread at 2 sigma) in one episode:
    the first week of each, compared. One line; no conclusion beyond it."""
    flag = _first(rows, lambda r: r["watch"]["on"])
    stress = _first(rows, lambda r: any(r["watch"]["detail"][k]["state"] is True
                                        for k in ("move", "funding", "swap_spread")))
    level = _first(rows, lambda r: r["level_flag"])
    absent = sorted({NAMES[k] for r in rows for k in r["watch"]["absent"]})
    tail = f" (absent: {', '.join(absent)})" if absent else ""
    lv = f"level flag first on {level}" if level else "no level flag"
    if stress is None and flag is None:
        return f"no stress reading and no unwind-watch flag in the episode; {lv}{tail}."
    if stress is None:
        return (f"the unwind-watch flag first on {flag}, no stress reading in the "
                f"episode; {lv}{tail}.")
    if flag is None:
        return (f"the unwind-watch flag did not fire; first stress reading {stress}; "
                f"{lv}{tail}.")
    rel = "led" if flag < stress else "coincided with" if flag == stress else "lagged"
    return (f"the unwind-watch flag {rel} the stress readings: flag first on {flag}, "
            f"first stress reading {stress}; {lv}{tail}.")


def ledger(st, cutoff: Optional[str] = None, cfg: Optional[dict] = None) -> list[dict]:
    """Every episode: its weekly rows and its one line."""
    cfg = cfg or load_config()
    hist = history(st, cutoff, cfg)
    out = []
    for ep in cfg.get("episodes") or []:
        days = [w["day"] for w in hist if w["day"] >= ep["start"]
                and (ep.get("end") is None or w["day"] <= ep["end"])]
        rows = [read(st, d, cutoff, cfg, hist) for d in days]
        rows = [r for r in rows if r]
        out.append({**ep, "rows": rows,
                    "line": episode_verdict(rows) if rows else
                    "no stored TFF history for the episode."})
    return out


def _f(v: Optional[float], fmt: str = "{:.1f}") -> str:
    return "—" if v is None else fmt.format(v)


def _co(r: dict, k: str) -> str:
    d = r["watch"]["detail"][k]
    if d["state"] is None:
        return "absent"
    if d.get("z") is None:
        return "✓" if d["state"] else "no"
    return f"{d['z']:+.1f}σ" + (" ✓" if d["state"] else "")


def ledger_markdown(eps: list[dict], generated: str, provenance: str) -> str:
    lines = ["# SR-36 calibration ledger (ST-B3-14)", "",
             f"Generated {generated} by `python -m altdata.basis_proxy ledger`. "
             f"{provenance}", "",
             "Shares are the leveraged-fund net short as a percent of open interest "
             "(contract-weighted; DV01-weighted in brackets); percentiles are over the "
             "full history since 2010 knowable that week. Tiers per the 6 Oct ruling. "
             "Co-signal cells are the z of the change at that report Tuesday; ✓ is at "
             "2σ (the swap spread either way). Descriptive; unvalidated, n=0.", ""]
    for ep in eps:
        lines += [f"## {ep['title']}", "", f"**{ep['title']}:** {ep['line']}", ""]
        if not ep["rows"]:
            continue
        lines += ["| Report Tuesday | Six-contract share | Pctile | Tier | 10-year share "
                  "| Pctile | Tier | OI read | SR-35 | MOVE 1m | SOFR–IORB 2w | Swap spread "
                  "| Watch |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in ep["rows"]:
            lines.append(
                f"| {r['day']} | {_f(r['lev_short_oi'])}% ({_f(r['lev_short_oi_dv01'])}%) "
                f"| {_ordinal(r['pct_full'])} | {r['aggregate_tier'] or '—'} "
                f"| {_f(r['ten_year_short_oi'])}% | {_ordinal(r['ten_year_pct_full'])} "
                f"| {r['ten_year_tier'] or '—'} | {r['oi_change'] or '—'} "
                f"| {_co(r, 'sr35')} | {_co(r, 'move')} | {_co(r, 'funding')} "
                f"| {_co(r, 'swap_spread')} | {'ON' if r['watch']['on'] else 'off'} |")
        lines.append("")
    return "\n".join(lines)


def _main(argv: list[str]) -> int:
    import argparse
    import json
    from . import observations
    ap = argparse.ArgumentParser(prog="altdata.basis_proxy")
    ap.add_argument("cmd", choices=["show", "ledger"])
    ap.add_argument("--day")
    ap.add_argument("--db")
    ap.add_argument("--out")
    ap.add_argument("--provenance", default="Computed from the stored history.")
    a = ap.parse_args(argv)
    st = observations.ObservationStore(a.db)
    try:
        if a.cmd == "show":
            r = read(st, a.day)
            if r is None:
                print("no TFF Treasury history stored")
                return 1
            print(positioning_line(r))
            print(plumbing_line(r))
            print(json.dumps({k: v for k, v in r.items() if k != "watch"},
                             indent=1, default=str))
            return 0
        eps = ledger(st)
        md = ledger_markdown(eps, dt.date.today().isoformat(), a.provenance)
        if a.out:
            Path(a.out).write_text(md + "\n", encoding="utf-8")
        else:
            print(md)
        for ep in eps:
            print(f"{ep['title']}: {ep['line']}")
        return 0
    finally:
        st.close()


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
