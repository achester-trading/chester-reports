"""
"What's carrying the index" and the allocation block -- the reads.

    python -m altdata.st_r5_index show [--as-of ISO] [--json]

Signal-triage Batch 6 items 40, 35 and 30, and Batch 5 item 29
(docs/change-order-signal-triage-batch-6-2026-10-15.md, section 4 rulings 2 and
3). One question, which leg is carrying the index: the standing decomposition
(40) shows the result, r-g (29) the condition, the corporate-price/ULC gap (35)
the mechanism behind both the earnings and the yields. The allocation block
(30) is the positioning side of the same top-side condition. Tranche 1 only:

    decomposition(st, cutoff)   ST-R5.40a  price = EPS x P/E in log shares at
                                three anchors (the 12 Oct 2022 cycle low, twelve
                                months, year to date), forward and trailing
    r_minus_g(st, cutoff)       ST-R4.29a  the 10-year less g, and the
                                revisions-turn flag
    price_ulc(st, cutoff)       ST-R5.35a  the gap, its closing flag and the
                                margin-source line
    allocation(st, cutoff)      ST-R5.30a  equities, bonds, cash (Z.1); AAII and
                                ICI listed gaps (the by-hand audit, 16 Oct 2026)

THE DATA, all already stored or added to the FRED pull on this branch: the S&P
500 close (yfinance.mkt_gspc); S&P DJI's forward operating EPS and quarterly
estimates (altdata/sources/spdji.py, the operator's drop -- nothing fetches the
workbook, and until the first drop the forward legs print "awaiting the
estimates workbook (drop pending)"); Shiller's trailing earnings (the trailing
version, as SR-38 labels it); FRED's 10-year, PPI, ULC and Z.1 rows. SR-38's identity and its constant-quarter revisions
(altdata/return_attribution.py) are reused, not rebuilt.

Every read is as of the cutoff. Every percentile names its real window and n
(altdata/st_r5_rates.lens).
"""

from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path
from typing import Any, Optional

import yaml

from .st_r5_rates import _on_or_before, _pts, _years_back, change, lens, lens_text

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "st_r5_index.yaml"


def config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _months_back(day: str, n: int) -> str:
    d = dt.date.fromisoformat(day)
    y, m = divmod(d.year * 12 + d.month - 1 - n, 12)
    last = [31, 29 if (y % 4 == 0 and (y % 100 or y % 400 == 0)) else 28, 31, 30, 31,
            30, 31, 31, 30, 31, 30, 31][m]
    return dt.date(y, m + 1, min(d.day, last)).isoformat()


def quarter_name(day: str) -> str:
    d = dt.date.fromisoformat(day)
    return f"Q{(d.month - 1) // 3 + 1} {d.year}"


# ---------------------------------------------------------------------------
# ST-R5.40a -- the standing decomposition
# ---------------------------------------------------------------------------
ANCHOR_LABELS = {"cycle_low": "Since the 12 Oct 2022 low",
                 "twelve_months": "Twelve months", "ytd": "Year to date"}


def anchor_days(latest: str, cfg: dict) -> dict[str, str]:
    a = (cfg.get("decomposition") or {}).get("anchors") or {}
    out = {}
    if a.get("cycle_low"):
        out["cycle_low"] = str(a["cycle_low"])
    if a.get("twelve_months"):
        out["twelve_months"] = _months_back(latest, int(a["twelve_months"]))
    if a.get("ytd"):
        out["ytd"] = f"{int(latest[:4]) - 1}-12-31"
    return out


def carrier(le: float, lm: float, lp: float, min_move: float) -> str:
    """Which leg carries the move, in the price's direction."""
    if abs(lp) < min_move:
        return "neither: the index is flat over the span"
    s = 1.0 if lp > 0 else -1.0
    ce, cm = le * s, lm * s
    move = "gain" if lp > 0 else "fall"
    if ce > 0 and cm <= 0:
        return f"earnings carry the {move}; the multiple works against it"
    if cm > 0 and ce <= 0:
        return f"the multiple carries the {move}; earnings work against it"
    return (f"earnings carry most of the {move}" if ce >= cm
            else f"the multiple carries most of the {move}")


def split(p0: float, p1: float, e0: float, e1: float, min_move: float) -> dict:
    lp, le = math.log(p1 / p0), math.log(e1 / e0)
    lm = lp - le
    ok = abs(lp) >= min_move
    return {"price_pct": round(100 * (math.exp(lp) - 1), 2),
            "eps_pct": round(100 * (math.exp(le) - 1), 2),
            "pe_change_pct": round(100 * (math.exp(lm) - 1), 2),
            "pe_start": round(p0 / e0, 2), "pe_end": round(p1 / e1, 2),
            "eps_share_pct": round(100 * le / lp, 1) if ok else None,
            "pe_share_pct": round(100 * lm / lp, 1) if ok else None,
            "log_price": round(lp, 6), "log_eps": round(le, 6), "log_pe": round(lm, 6),
            "carrier": carrier(le, lm, lp, min_move)}


def decomposition(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    c = cfg.get("decomposition") or {}
    mm = float(c.get("min_log_move", 0.01))
    idx = _pts(st, c.get("index_key", "yfinance.mkt_gspc"), cutoff)
    out: dict[str, Any] = {"awaiting": c.get("awaiting"), "versions": {}}
    if not idx:
        return dict(out, absent=True, reason="no S&P 500 close is stored")
    d1, p1 = idx[-1]
    days = anchor_days(d1, cfg)
    out.update(absent=False, end_day=d1, index_end=p1, anchors=days)
    for ver, key in (("forward", c.get("forward_eps_key", "spdji.fwd12m_op_eps")),
                     ("trailing", c.get("trailing_eps_key", "shiller.sp_earnings"))):
        eps = _pts(st, key, cutoff)
        v: dict[str, Any] = {"key": key, "anchors": {}}
        last = _on_or_before(eps, d1) if eps else None
        if not last:
            v.update(state="awaiting" if ver == "forward" else "absent",
                     reason=(c.get("awaiting") if ver == "forward" else
                             "no trailing earnings stored (Shiller)"))
            out["versions"][ver] = v
            continue
        v.update(state="read", eps_end=last[1], eps_as_of=last[0])
        for aid, aday in days.items():
            p0 = _on_or_before(idx, aday)
            e0 = _on_or_before(eps, aday)
            if not p0:
                v["anchors"][aid] = {"absent": True, "reason": f"no close on or "
                                     f"before {aday}"}
            elif not e0:
                v["anchors"][aid] = {"absent": True, "reason": (
                    f"no {'S&P DJI drop' if ver == 'forward' else 'trailing earnings'} "
                    f"stored on or before {aday} (the first is {eps[0][0]})")}
            elif e0[1] <= 0 or last[1] <= 0:
                v["anchors"][aid] = {"absent": True, "reason": "non-positive earnings"}
            else:
                v["anchors"][aid] = dict(split(p0[1], p1, e0[1], last[1], mm),
                                         absent=False, anchor=aday, start_day=p0[0],
                                         eps_start_as_of=e0[0], index_start=p0[1])
        out["versions"][ver] = v
    return out


def read_line(d: dict, anchor: str = "twelve_months") -> str:
    """The one-line read: which leg is carrying the index, forward if the drops
    reach the anchor, else trailing, labelled."""
    if d.get("absent"):
        return f"What's carrying the index: not read — {d['reason']}."
    for ver in ("forward", "trailing"):
        v = d["versions"].get(ver) or {}
        a = (v.get("anchors") or {}).get(anchor) or {}
        if v.get("state") == "read" and not a.get("absent") and a:
            lab = ANCHOR_LABELS.get(anchor, anchor).lower()
            share = ("" if a["eps_share_pct"] is None else
                     f", earnings {a['eps_share_pct']:.0f}% of it in log terms")
            caveat = ("" if ver == "forward" else
                      f" (trailing earnings as of {v['eps_as_of'][:7]}; the forward "
                      f"split: {forward_state(d)})")
            return (f"What's carrying the index, {lab} ({a['start_day']} to "
                    f"{d['end_day']}): the S&P 500 {a['price_pct']:+.1f}%, {ver} EPS "
                    f"{a['eps_pct']:+.1f}% and the {ver} P/E {a['pe_change_pct']:+.1f}%"
                    f"{share} — {a['carrier']}{caveat}.")
    return f"What's carrying the index: not read — {forward_state(d)}."


def chart_series(st, cutoff: str, anchor: str = "twelve_months",
                 cfg: Optional[dict] = None) -> dict:
    """The standing chart's three lines, each indexed to 100 at the anchor: the
    S&P 500, EPS and the P/E, one point per earnings observation (a drop, or a
    trailing month) from the anchor on. Forward EPS where a drop reaches the
    anchor, else trailing, and the result names which."""
    cfg = cfg or config()
    c = cfg.get("decomposition") or {}
    idx = _pts(st, c.get("index_key", "yfinance.mkt_gspc"), cutoff)
    if not idx:
        return {"absent": True, "reason": "no S&P 500 close is stored"}
    aday = anchor_days(idx[-1][0], cfg).get(anchor)
    for ver, key in (("forward", c.get("forward_eps_key", "spdji.fwd12m_op_eps")),
                     ("trailing", c.get("trailing_eps_key", "shiller.sp_earnings"))):
        eps = _pts(st, key, cutoff)
        e0 = _on_or_before(eps, aday) if eps and aday else None
        p0 = _on_or_before(idx, aday) if aday else None
        if not (e0 and p0) or e0[1] <= 0:
            continue
        pts = [(aday, e0[1])] + [(d, v) for d, v in eps if d > aday and v > 0]
        # The last point is the latest close, with the latest EPS carried to it.
        if idx[-1][0] > pts[-1][0]:
            pts.append((idx[-1][0], pts[-1][1]))
        lines: dict[str, list] = {"S&P 500": [], f"{ver.capitalize()} EPS": [],
                                  f"{ver.capitalize()} P/E": []}
        for d, e in pts:
            p = _on_or_before(idx, d)
            if not p:
                continue
            lines["S&P 500"].append((d, round(100 * p[1] / p0[1], 2)))
            lines[f"{ver.capitalize()} EPS"].append((d, round(100 * e / e0[1], 2)))
            lines[f"{ver.capitalize()} P/E"].append(
                (d, round(100 * (p[1] / e) / (p0[1] / e0[1]), 2)))
        return {"absent": False, "version": ver, "anchor": anchor, "anchor_day": aday,
                "first": pts[0][0], "last": pts[-1][0], "n": len(lines["S&P 500"]),
                "series": lines}
    return {"absent": True, "reason": f"no earnings stored on or before the anchor "
            f"{aday}, forward or trailing"}


def forward_state(d: dict) -> str:
    v = (d.get("versions") or {}).get("forward") or {}
    if v.get("state") != "read":
        return v.get("reason") or d.get("awaiting") or "not read"
    return f"latest drop as of {v['eps_as_of']}"


# ---------------------------------------------------------------------------
# ST-R4.29a -- r-g and the revisions-turn flag
# ---------------------------------------------------------------------------
def growth(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """g from the latest drop: the four quarters after the forward four, against
    the forward four."""
    cfg = cfg or config()
    c = cfg.get("r_minus_g") or {}
    recs = [(str(r["observed_at"])[:10], r.get("value_text"))
            for r in st.as_of(c.get("drop_key", "spdji.eps_drop"), cutoff)]
    recs = [x for x in recs if x[1]]
    if not recs:
        return {"absent": True, "reason": (cfg.get("decomposition") or {}).get("awaiting")}
    day, rec = recs[-1]
    four = json.loads(rec).get("forward_quarters") or []
    qkey = c.get("quarter_key", "spdji.op_eps_est_q")
    held = {}
    for q in st.instruments(qkey):
        v = dict(_pts(st, qkey, cutoff, q)).get(day)
        if v is not None:
            held[q] = v
    later = sorted(q for q in held if four and q > four[-1])[:4]
    need = int(c.get("quarters_ahead", 8))
    if len(four) + len(later) < need or any(q not in held for q in four):
        return {"absent": True, "drop": day, "reason": f"the {day} drop holds "
                f"{len(four) + len(later)} estimated quarters ahead; g needs {need}"}
    e1, e2 = sum(held[q] for q in four), sum(held[q] for q in later)
    return {"absent": False, "drop": day, "year1": four, "year2": later,
            "eps_year1": round(e1, 4), "eps_year2": round(e2, 4),
            "g_pct": round(100 * (e2 / e1 - 1), 2)}


def r_minus_g(st, cutoff: str, cfg: Optional[dict] = None,
              gap: Optional[dict] = None) -> dict:
    from . import return_attribution as ra                      # noqa: PLC0415
    cfg = cfg or config()
    c = cfg.get("r_minus_g") or {}
    ten_pts = _pts(st, c.get("ten_year_key", "fred.yield_10y"), cutoff)
    g = growth(st, cutoff, cfg)
    out: dict[str, Any] = {"g": g, "unvalidated": cfg.get("unvalidated"),
                           "flat_max_pct": float(c.get("flat_max_pct", 0.25)),
                           "ten_year_up_bp": float(c.get("ten_year_up_bp", 10)),
                           "window_days": int(c.get("window_days", 28))}
    if ten_pts:
        out.update(ten_pct=ten_pts[-1][1], ten_as_of=ten_pts[-1][0])
    if ten_pts and not g["absent"]:
        out["r_minus_g_pp"] = round(ten_pts[-1][1] - g["g_pct"], 2)
    ten = change(ten_pts, out["window_days"], 100.0)
    rev = ra.index_revisions(st, cutoff)
    w = (rev.get("windows") or {}).get("1-month") or {}
    out.update(ten_change_bp=None if ten is None else ten["change"],
               revision_pct=None if w.get("pct") is None else round(w["pct"], 2),
               revision_since=w.get("since"))
    if rev.get("state") != "read" or w.get("pct") is None or ten is None:
        why = (rev.get("reason") if rev.get("state") == "awaiting" else
               "revisions need a second drop" if rev.get("state") == "one_drop" else
               w.get("why") or "the 10-year does not hold the window")
        out.update(flag="absent", flag_reason=why)
    else:
        fired = out["revision_pct"] <= out["flat_max_pct"] and \
            out["ten_change_bp"] >= out["ten_year_up_bp"]
        out["flag"] = "on" if fired else "off"
    out["leading"] = None if gap is None else gap.get("closing")
    return out


def r_minus_g_lines(r: dict) -> list[str]:
    lines = []
    g = r["g"]
    if g["absent"]:
        lines.append(f"r−g: not read — {g['reason']}"
                     + (f"; the 10-year {r['ten_pct']:.2f}% ({r['ten_as_of']})."
                        if r.get("ten_pct") is not None else "."))
    elif r.get("r_minus_g_pp") is not None:
        lines.append(f"r−g {r['r_minus_g_pp']:+.2f} pp: the 10-year {r['ten_pct']:.2f}% "
                     f"({r['ten_as_of']}) against g {g['g_pct']:.2f}%, the estimates' "
                     f"growth into the second forward year ({g['year2'][0]}–"
                     f"{g['year2'][-1]} over {g['year1'][0]}–{g['year1'][-1]}, S&P DJI "
                     f"drop of {g['drop']}).")
    lead = {True: "the price–ULC gap is closing from above (a leading input)",
            False: "the price–ULC gap is not closing", None: "the price–ULC gap is not read"
            }[r.get("leading")]
    if r["flag"] == "absent":
        lines.append(f"Revisions-turn flag: not read — {r['flag_reason']}; {lead}.")
    elif r["flag"] == "on":
        lines.append(f"Revisions turn: forward EPS revised {r['revision_pct']:+.2f}% since "
                     f"the {r['revision_since']} drop while the 10-year moved "
                     f"{r['ten_change_bp']:+.0f} bp over {r['window_days']} days; {lead} "
                     f"{r['unvalidated']}.")
    else:
        lines.append(f"Revisions-turn flag off: forward EPS {r['revision_pct']:+.2f}%, the "
                     f"10-year {r['ten_change_bp']:+.0f} bp over {r['window_days']} days "
                     f"(it fires at revisions ≤ +{r['flat_max_pct']:.2f}% with the 10-year "
                     f"≥ +{r['ten_year_up_bp']:.0f} bp); {lead}.")
    return lines


# ---------------------------------------------------------------------------
# ST-R5.35a -- the corporate-price/ULC gap
# ---------------------------------------------------------------------------
def yoy(pts: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """Change on the year, in percent, for every period a year after a held one."""
    have = dict(pts)
    out = []
    for d, v in pts:
        base = have.get(_years_back(d, 1))
        if base:
            out.append((d, round(100 * (v / base - 1), 4)))
    return out


def price_ulc(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    c = cfg.get("price_ulc") or {}
    ppi = yoy(_pts(st, c.get("ppi_key", "fred.ppi_fd_core_ex_trade"), cutoff))
    ulc = yoy(_pts(st, c.get("ulc_key", "fred.ulc_nfb"), cutoff))
    out: dict[str, Any] = {"closing_pp": float(c.get("closing_pp", 1.0)),
                           "peak_window_months": int(c.get("peak_window_months", 6)),
                           "unvalidated": cfg.get("unvalidated")}
    if not ppi or not ulc:
        return dict(out, absent=True, reason="the PPI (WPSFD49116) or ULC (ULCNFB) "
                    "year-on-year change is not stored yet", closing=None)
    gap = []
    for d, p in ppi:
        u = _on_or_before(ulc, d)
        if u:
            gap.append((d, round(p - u[1], 4), u[0], u[1], p))
    if not gap:
        return dict(out, absent=True, reason="no PPI month on or after a ULC quarter",
                    closing=None)
    d, g, uq, u, p = gap[-1]
    recent = [x[1] for x in gap[-out["peak_window_months"]:]]
    peak = max(recent)
    closing = g > 0 and (peak - g) >= out["closing_pp"]
    return dict(out, absent=False, month=d, gap_pp=g, ppi_yoy_pct=p, ulc_yoy_pct=u,
                ulc_quarter=uq, carried=uq[:7] != d[:7], peak_pp=peak,
                off_peak_pp=round(peak - g, 4), closing=closing,
                lens=lens([(x[0], x[1]) for x in gap], 5))


def price_ulc_lines(g: dict) -> list[str]:
    if g.get("absent"):
        return [f"Corporate price less unit labor cost: not read — {g['reason']}."]
    mon = dt.date.fromisoformat(g["month"]).strftime("%B %Y")
    ulc = (f"unit labor costs {g['ulc_yoy_pct']:+.1f}% ({quarter_name(g['ulc_quarter'])}"
           + (", carried forward to the next print)" if g["carried"] else ")"))
    lines = [f"Corporate price less unit labor cost, {mon}: {g['gap_pp']:+.1f} pp — PPI "
             f"final demand less foods, energy and trade services {g['ppi_yoy_pct']:+.1f}% "
             f"on the year, {ulc}; the gap at the {lens_text(g['lens'])}."]
    if g["closing"]:
        lines.append(f"The gap is closing from above: {g['off_peak_pp']:.1f} pp below its "
                     f"{g['peak_window_months']}-month peak of {g['peak_pp']:+.1f} pp, a "
                     f"leading input to the revisions-turn flag {g['unvalidated']}.")
    else:
        lines.append(f"Gap-closing flag off: {g['off_peak_pp']:.1f} pp below its "
                     f"{g['peak_window_months']}-month peak (it fires above zero at "
                     f"{g['closing_pp']:.1f} pp off the peak).")
    return lines


def margin_line(g: dict) -> str:
    """The margin-source attribution line, for the earnings block."""
    if g.get("absent"):
        return f"Margin source: not read — {g['reason']}."
    side = ("pricing ahead of cost: the margin's source is price"
            if g["gap_pp"] > 0 else
            "cost ahead of pricing: the margin is being squeezed"
            if g["gap_pp"] < 0 else "pricing and cost level")
    return (f"Margin source ({g['month'][:7]}): selling prices {g['ppi_yoy_pct']:+.1f}% "
            f"against unit labor costs {g['ulc_yoy_pct']:+.1f}% on the year — {side}.")


# ---------------------------------------------------------------------------
# ST-R5.30a -- the allocation block
# ---------------------------------------------------------------------------
def _share(num: list[tuple[str, float]], den: list[tuple[str, float]]
           ) -> list[tuple[str, float]]:
    dd = dict(den)
    return [(d, round(100 * v / dd[d], 4)) for d, v in num if dd.get(d)]


def allocation(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    c = cfg.get("allocation") or {}
    years = (c.get("windows_years") or [5])[0]
    assets = _pts(st, c.get("assets_key", "fred.hh_fin_assets"), cutoff)
    series = {
        "equities": (_pts(st, c.get("equity_share_key", "fred.hh_equity_share"), cutoff),
                     "Equities (directly and indirectly held, % of financial assets)"),
        "bonds": (_share(_pts(st, c.get("bonds_key", "fred.hh_debt_securities"), cutoff),
                         assets),
                  "Bonds (debt securities directly held, % of financial assets)"),
        "cash": (_share(_pts(st, c.get("cash_key", "fred.hh_deposits"), cutoff), assets),
                 "Cash (currency, deposits and money funds, % of financial assets)")}
    panels = {}
    for pid, (pts, label) in series.items():
        if not pts:
            panels[pid] = {"absent": True, "label": label,
                           "reason": "the Z.1 rows are not stored yet"}
            continue
        prev = pts[-2] if len(pts) > 1 else None
        panels[pid] = {"absent": False, "label": label, "share_pct": pts[-1][1],
                       "quarter": pts[-1][0],
                       "change_pp": None if prev is None else round(pts[-1][1] - prev[1], 2),
                       "lens": lens(pts, years)}
    return {"panels": panels, "aaii_gap": c.get("aaii_gap"), "ici_gap": c.get("ici_gap"),
            "base_rate": c.get("base_rate"), "years": years}


def allocation_rows(a: dict) -> list[list[str]]:
    """One row per panel held; an absent panel is the block's footnote
    (allocation_absent), never an empty row asking for a read."""
    rows = []
    for pid in ("equities", "bonds", "cash"):
        p = a["panels"][pid]
        if p["absent"]:
            continue
        lz = p["lens"]
        pct = (f"{lens_text(lz)}")
        rows.append([p["label"], f"{p['share_pct']:.1f}%", quarter_name(p["quarter"]),
                     "—" if p["change_pp"] is None else
                     f"{(p['change_pp'] if round(p['change_pp'], 1) else 0.0):+.1f} pp", pct])
    return rows


def allocation_absent(a: dict) -> list[str]:
    return [f"{p['label']}: {p['reason']}" for p in a["panels"].values() if p["absent"]]


def allocation_lines(a: dict) -> list[str]:
    lines = []
    eq = a["panels"]["equities"]
    if not eq["absent"]:
        lines.append(f"Equities panel: {a['base_rate']}.")
    lines.append(f"{a['aaii_gap']}.")
    lines.append(f"{a['ici_gap']}.")
    return lines


# ---------------------------------------------------------------------------
def build(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    gap = price_ulc(st, cutoff, cfg)
    return {"block": "index_carry", "descriptive": True, "as_of": cutoff,
            "header": cfg.get("header"),
            "decomposition": decomposition(st, cutoff, cfg),
            "r_minus_g": r_minus_g(st, cutoff, cfg, gap), "price_ulc": gap,
            "allocation": allocation(st, cutoff, cfg)}


def main(argv: Optional[list[str]] = None) -> int:
    import argparse

    from . import observations, session
    ap = argparse.ArgumentParser(prog="python -m altdata.st_r5_index")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show", help="print the cluster as of a cutoff")
    s.add_argument("--as-of", default=None)
    s.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    cutoff = a.as_of or session.utc_iso()
    with observations.ObservationStore() as st:
        b = build(st, cutoff)
    if a.json:
        print(json.dumps(b, indent=2, default=str))
        return 0
    print(str(b["header"]).upper())
    print(read_line(b["decomposition"]))
    for ln in (r_minus_g_lines(b["r_minus_g"]) + price_ulc_lines(b["price_ulc"])
               + [margin_line(b["price_ulc"])] + allocation_lines(b["allocation"])):
        print(ln)
    for r in allocation_rows(b["allocation"]):
        print("  " + " | ".join(r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
