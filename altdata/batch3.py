"""
Signal-triage batch 3, Tranche A -- the reads, from the store, as of a cutoff.

    ST-B3-16  jgb_line       SR-32's early line: the 30y JGB against 4.40% / 4.5%
    ST-B3-03  eu_stress      SR-30: OAT-Bund and BTP-Bund, dual percentiles, the
                             two-tier flag; EUR/CHF as the transmission tell
    ST-B3-04  buybacks       SR-33: each operation's bought/max and the 30-year's
                             next-session change; the TGA; the lever modifier
    ST-B3-05  japan_funding  SR-34: Japan's reserves and the FIMA repo line
    ST-B3-02  tenor_lens     SR-6 by tenor: real against breakeven, expected rate
                             against term premium, at 2y / 5y / 10y / 30y

Change order: docs/change-order-signal-triage-batch-3-2026-10-02.md (ruled 6 Oct
2026). Config: config/batch3_tranche_a.yaml. Printed by
daily_cascade/batch3_block.py.

DESCRIPTIVE ONLY. Every read here is a narrow flag or a modifier line: nothing
enters the market-state object, a composite, a trigger or a decision, and no
read is causal. Percentiles go through altdata.derived.percentile_of, the one
place a percentile is computed; changes in bp are computed from the stored
percent levels (x100), the registry's unit for a rate. A read that cannot be
made returns its reason, never a zero.

SR-30'S LEGS ARE READ BY NAME. The OAT, BTP and Bund 10-year monthly series are
written by the ECB writer on `aq-3-series-2` (altdata/sources/ecb_irs.py, keys
ecb.irs_10y_{fr,it,de}); `sr-36-basis-proxy` and `sr-43-49-rates-anchor` carry
it too. This branch does not duplicate that writer: until it merges the block
prints that the legs are not yet stored.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Optional

import yaml

from . import derived

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "batch3_tranche_a.yaml"

# SR-30's legs: the ECB's monthly convergence 10-year yields (aq-3-series-2).
EU_LEGS = {"fr": "ecb.irs_10y_fr", "it": "ecb.irs_10y_it", "de": "ecb.irs_10y_de"}
EU_PAIRS = (("oat_bund", "OAT–Bund", "fr"), ("btp_bund", "BTP–Bund", "it"))
EU_WRITER = "the ECB writer (altdata/sources/ecb_irs.py, branch aq-3-series-2)"
EURCHF_KEY = "yfinance.mkt_eurchf"

BUYBACK_KEYS = ("treasury.buyback_max", "treasury.buyback_accepted")
RESERVE_KEYS = ("tic.jp_reserves_total", "tic.jp_reserves_fx_securities")
FIMA_KEYS = ("tic.fima_repo", "tic.fima_repo_weekavg")


def config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _pts(st, key: str, cutoff: str, instrument: Optional[str] = None
         ) -> list[tuple[str, float]]:
    rows = [(str(r["observed_at"])[:10], float(r["value_num"]))
            for r in st.as_of(key, cutoff, instrument)
            if r.get("value_num") is not None]
    return sorted(rows)


def _on_or_before(pts: list[tuple[str, float]], day: str) -> Optional[tuple[str, float]]:
    best = None
    for d, v in pts:
        if d <= day:
            best = (d, v)
        else:
            break
    return best


def _bp(a: float, b: float) -> float:
    return round((a - b) * 100.0, 1)


# ---------------------------------------------------------------------------
# ST-B3-16 -- the 30y JGB line
# ---------------------------------------------------------------------------
def jgb_state(level: Optional[float], cfg: dict) -> str:
    """below | approaching | flagged, on the stored close."""
    c = cfg.get("jgb_line") or {}
    if level is None:
        return "absent"
    if level >= float(c.get("flag_pct", 4.5)):
        return "flagged"
    if level >= float(c.get("approach_pct", 4.4)):
        return "approaching"
    return "below"


def jgb_line(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """{state, level, as_of, line}: `line` is None below the approach line."""
    cfg = cfg or config()
    c = cfg.get("jgb_line") or {}
    row = st.latest_as_of(c.get("key", "mof.jgb_30y"), cutoff)
    if not row or row.get("value_num") is None:
        return {"state": "absent", "level": None, "line": None,
                "reason": "the 30-year JGB is not stored (altdata/sources/mof.py)"}
    lvl, day = float(row["value_num"]), str(row["observed_at"])[:10]
    state = jgb_state(lvl, cfg)
    ap, fl = float(c.get("approach_pct", 4.4)), float(c.get("flag_pct", 4.5))
    line = None
    if state == "approaching":
        line = (f"30-year JGB {lvl:.3f}% (MoF, {day}): inside the approach band "
                f"{ap:.2f}–{fl:.2f}%, {round((fl - lvl) * 100)} bp below the "
                f"{fl:.1f}% line the market treats as lifers' forced-selling level.")
    elif state == "flagged":
        line = (f"30-year JGB {lvl:.3f}% (MoF, {day}): at or above the {fl:.1f}% "
                f"line — {c.get('mechanism')}.")
    return {"state": state, "level": lvl, "as_of": day, "line": line,
            "approach_pct": ap, "flag_pct": fl}


# ---------------------------------------------------------------------------
# ST-B3-03 -- SR-30, EU sovereign stress
# ---------------------------------------------------------------------------
def spread_series(st, cutoff: str, leg: str) -> list[tuple[str, float]]:
    """The <leg>-Bund spread in bp, per period both legs carry."""
    a = dict(_pts(st, EU_LEGS[leg], cutoff))
    b = dict(_pts(st, EU_LEGS["de"], cutoff))
    return [(d, _bp(a[d], b[d])) for d in sorted(set(a) & set(b))]


def tier_of(bp: Optional[float], cfg: dict) -> str:
    c = cfg.get("eu_stress") or {}
    if bp is None:
        return "absent"
    if bp >= float(c.get("crisis_bp", 190)):
        return "crisis"
    if bp >= float(c.get("watch_bp", 150)):
        return "watch"
    return "none"


def dual_percentiles(series: list[tuple[str, float]], years: tuple[int, ...]
                     ) -> dict:
    """{years: {pct, n, from}} for the latest value against each trailing window
    of `years` (through derived.percentile_of)."""
    if not series:
        return {}
    last_day, last = series[-1]
    end = dt.date.fromisoformat(last_day)
    out = {}
    for y in years:
        start = end.replace(year=end.year - y).isoformat()
        win = [v for d, v in series if d > start]
        out[y] = {"pct": derived.percentile_of(win, last), "n": len(win),
                  "from": next((d for d, _ in series if d > start), None)}
    return out


def crisis_level_from_store(st, cutoff: str, month: str = "2011-11") -> Optional[float]:
    """The OAT-Bund spread for November 2011 in the stored series: what
    config `eu_stress.crisis_bp` is set from (decision 2), recomputable here."""
    for d, v in spread_series(st, cutoff, "fr"):
        if d.startswith(month):
            return v
    return None


def eu_stress(st, cutoff: str, cfg: Optional[dict] = None, tell_days: int = 7) -> dict:
    cfg = cfg or config()
    c = cfg.get("eu_stress") or {}
    years = tuple(int(y) for y in c.get("windows_years") or (5, 20))
    # The tiers sit on the daily weekly close (ruled 13 Oct 2026): on the
    # monthly series every pair is untiered, and the label says which series.
    live = bool(c.get("tiers_live"))
    labels = c.get("series_labels") or {}
    pairs = []
    for pid, label, leg in EU_PAIRS:
        label = labels.get(pid) or label
        ser = spread_series(st, cutoff, leg)
        if not ser:
            pairs.append({"id": pid, "label": label, "absent": True,
                          "reason": f"not yet stored — the legs come from {EU_WRITER}"})
            continue
        day, bp = ser[-1]
        prior = ser[-2] if len(ser) > 1 else None
        pairs.append({"id": pid, "label": label, "bp": bp, "as_of": day,
                      "change_bp": None if not prior else round(bp - prior[1], 1),
                      "prior_as_of": prior[0] if prior else None,
                      "percentiles": dual_percentiles(ser, years),
                      "tier": tier_of(bp, cfg) if pid == "oat_bund" and live
                      else None,
                      "cadence": "monthly average (ECB)"})
    chf = _pts(st, EURCHF_KEY, cutoff)
    tell = None
    if chf:
        d, v = chf[-1]
        wk = _on_or_before(chf, (dt.date.fromisoformat(d)
                                 - dt.timedelta(days=tell_days)).isoformat())
        tell = {"level": v, "as_of": d, "since": wk[0] if wk else None,
                "week_change_pct": None if not wk else round((v / wk[1] - 1) * 100, 2)}
    oat = next((p for p in pairs if p["id"] == "oat_bund"), {})
    return {"pairs": pairs, "eurchf": tell, "tiers_live": live,
            "tier": (oat.get("tier", "absent") if live
                     else "absent" if not oat or oat.get("absent") else "untiered"),
            "watch_bp": float(c.get("watch_bp", 150)),
            "crisis_bp": float(c.get("crisis_bp", 190)),
            "unvalidated": c.get("unvalidated")}


# ---------------------------------------------------------------------------
# ST-B3-04 -- SR-33, Treasury buybacks
# ---------------------------------------------------------------------------
def _sector(instrument: str) -> str:
    return instrument.split(" | ")[-1] if instrument else instrument


def buyback_operations(st, cutoff: str, since: str, until: Optional[str] = None,
                       cfg: Optional[dict] = None) -> list[dict]:
    """Every stored operation dated in (since, until]: bought, maximum, the
    ratio, and the stored 30-year's change to the next session it carries."""
    cfg = cfg or config()
    c = cfg.get("buybacks") or {}
    until = until or cutoff[:10]
    long_end = set(c.get("long_end_buckets") or [])
    y30 = _pts(st, c.get("thirty_year_key", "fred.yield_30y"), cutoff)
    ops = []
    for inst in st.instruments(BUYBACK_KEYS[0]):
        mx = dict(_pts(st, BUYBACK_KEYS[0], cutoff, inst))
        acc = dict(_pts(st, BUYBACK_KEYS[1], cutoff, inst))
        for d in sorted(set(mx) & set(acc)):
            if not (since < d <= until):
                continue
            nxt = next(((dd, v) for dd, v in y30 if dd > d), None)
            on = _on_or_before(y30, d)
            ops.append({"date": d, "instrument": inst, "sector": _sector(inst),
                        "type": inst.split(" | ")[0],
                        "long_end": _sector(inst) in long_end,
                        "max": mx[d], "bought": acc[d],
                        "ratio": round(acc[d] / mx[d], 4) if mx[d] else None,
                        "y30_next_bp": (_bp(nxt[1], on[1]) if nxt and on and on[0] == d
                                        else None),
                        "y30_next_day": nxt[0] if nxt else None})
    return sorted(ops, key=lambda o: (o["date"], o["sector"]))


def tga(st, cutoff: str, cfg: Optional[dict] = None) -> Optional[dict]:
    cfg = cfg or config()
    row = st.latest_as_of((cfg.get("buybacks") or {}).get("tga_key", "fred.tga"), cutoff)
    if not row or row.get("value_num") is None:
        return None
    # MILLIONS (CLAUDE.md: WTREGEN is in millions) -> $bn.
    return {"usd_bn": round(float(row["value_num"]) / 1000.0, 1),
            "as_of": str(row["observed_at"])[:10]}


def lever_modifier(ops: list[dict], cfg: Optional[dict] = None) -> str:
    """The modifier line on the long-end supply read (the Monthly's lever table)."""
    cfg = cfg or config()
    soft = float((cfg.get("buybacks") or {}).get("soft_ratio", 0.9))
    le = [o for o in ops if o["long_end"] and o["ratio"] is not None]
    if not le:
        return "no long-end buyback operation in the window"
    bought = sum(o["bought"] for o in le) / 1e9
    mx = sum(o["max"] for o in le) / 1e9
    soft_n = sum(1 for o in le if o["ratio"] < soft)
    moves = [o["y30_next_bp"] for o in le if o["y30_next_bp"] is not None]
    return (f"{len(le)} long-end buyback operation(s): ${bought:,.2f}bn bought of "
            f"${mx:,.2f}bn of maximums ({bought / mx:.0%} taken up); "
            f"{soft_n} below {soft:.0%} of its maximum"
            + (f"; the 30-year's next-session change averaged "
               f"{sum(moves) / len(moves):+.1f} bp" if moves else "")
            + " — descriptive; unvalidated, n=0.")


# ---------------------------------------------------------------------------
# ST-B3-05 -- SR-34, Japan's reserves and FIMA
# ---------------------------------------------------------------------------
def _latest_change(st, key: str, cutoff: str) -> Optional[dict]:
    pts = _pts(st, key, cutoff)
    if not pts:
        return None
    d, v = pts[-1]
    prior = pts[-2] if len(pts) > 1 else None
    return {"value": v, "as_of": d, "change": None if not prior else v - prior[1],
            "prior_as_of": prior[0] if prior else None}


def japan_funding(st, cutoff: str) -> dict:
    return {"reserves_total": _latest_change(st, RESERVE_KEYS[0], cutoff),
            "reserves_securities": _latest_change(st, RESERVE_KEYS[1], cutoff),
            "fima": _latest_change(st, FIMA_KEYS[0], cutoff),
            "fima_weekavg": _latest_change(st, FIMA_KEYS[1], cutoff)}


# ---------------------------------------------------------------------------
# ST-B3-02 -- SR-6 by tenor
# ---------------------------------------------------------------------------
def _move(st, key: Optional[str], cutoff: str, then: str) -> Optional[dict]:
    """The bp change from the last value on or before `then` to the latest at
    the cutoff, with both dates."""
    if not key:
        return None
    pts = _pts(st, key, cutoff)
    if not pts:
        return None
    a = pts[-1]
    b = _on_or_before(pts, then[:10])
    if not b or b[0] >= a[0]:
        return None
    return {"bp": _bp(a[1], b[1]), "from": b[0], "to": a[0], "level": a[1]}


def tenor_lens(st, cutoff: str, then: str, cfg: Optional[dict] = None) -> dict:
    """Per tenor: the nominal move split into real and breakeven (breakeven =
    nominal less real, so the two sum to the move by construction), and ACM's
    expected short rate against its term premium where ACM publishes the tenor.
    The frame may say which tenor moved most and which leg was larger; nothing
    causal."""
    cfg = cfg or config()
    nope = cfg.get("tenor_not_published") or "not published at this tenor"
    rows = []
    for t in cfg.get("tenor_lens") or []:
        nom = _move(st, t["nominal"], cutoff, then)
        real = _move(st, t.get("real"), cutoff, then)
        be = (round(nom["bp"] - real["bp"], 1)
              if nom and real and nom["from"] == real["from"] and nom["to"] == real["to"]
              else None)
        rny = _move(st, t.get("rny"), cutoff, then)
        tp = _move(st, t.get("tp"), cutoff, then)
        rows.append({"tenor": t["tenor"], "nominal": nom, "real": real,
                     "breakeven_bp": be, "real_label": t.get("real_label"),
                     "expected_rate": rny, "term_premium": tp,
                     "acm": None if not t.get("rny") else "published",
                     "acm_note": None if t.get("rny") else nope,
                     "leg": (None if be is None or real is None else
                             ("real" if abs(real["bp"]) >= abs(be) else "breakeven")),
                     "acm_leg": (None if not rny or not tp else
                                 ("expected rate" if abs(rny["bp"]) >= abs(tp["bp"])
                                  else "term premium"))})
    moved = [r for r in rows if r["nominal"]]
    led = max(moved, key=lambda r: abs(r["nominal"]["bp"])) if moved else None
    return {"rows": rows, "led": led["tenor"] if led else None,
            "led_leg": led.get("leg") if led else None,
            "led_acm_leg": led.get("acm_leg") if led else None}
