"""
The wealth-effect impulse and the net-transmission line (signal-triage Batch 14,
item 66 -- written as 59; ST-R6.66a; ruled 20 Oct 2026, filed with F1-F8;
b52-batch14-a2). Reads the store as of the cutoff and decides nothing.

    impulse(st, cutoff, cfg)   monthly: Z.1's household equity share x SPX's
                               year-on-year return, in pp of household financial
                               assets; between Z.1 releases the share is marked to
                               SPX from its quarter's end (labelled), since ICI's
                               allocation proxy refuses an identified client
    net(st, cutoff, cfg)       the tightening legs (items 34, 36, 41: the
                               rates-transmission cluster's reads, altdata/
                               st_r5_rates.py) beside this loosening leg, each in
                               its own units and on its own scale, never weighted
                               or summed
    python -m altdata.transmission show [--as-of ISO] [--db PATH]

REPORT ONLY. Nothing here enters a composite or the market-state object.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Any, Optional

from altdata import st_r5_rates as rt
from altdata.numeral_audit import ordinal

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "transmission.yaml"


def config(path: Optional[Path] = None) -> dict:
    import yaml  # noqa: PLC0415
    return yaml.safe_load(Path(path or CONFIG_PATH).read_text(encoding="utf-8")) or {}


def quarter_end(first_day: str) -> str:
    """FRED dates a quarter by its first day; its level is the quarter's end."""
    d = dt.date.fromisoformat(first_day[:10])
    k = d.year * 12 + (d.month - 1) + 3            # the month after the quarter
    nxt = dt.date(k // 12, k % 12 + 1, 1)
    return (nxt - dt.timedelta(days=1)).isoformat()


def month_ends(pts: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """The last close of each calendar month, dated by that close."""
    by: dict[str, tuple[str, float]] = {}
    for d, v in pts:
        by[d[:7]] = (d, v)
    return [by[k] for k in sorted(by)]


def marked(share_pct: float, r: float) -> float:
    """The equity share after equities return r and the rest stays flat."""
    s = share_pct / 100.0
    return (s * (1.0 + r)) / (1.0 + s * r) * 100.0


def series(share: list[tuple[str, float]], index: list[tuple[str, float]]
           ) -> list[dict]:
    """The monthly impulse. Each month-end close m reads the latest Z.1 quarter
    whose end is on or before m; the share is the quarter's own when m closes
    that quarter, else marked to the index from the quarter's end. The year-on-
    year return is m's close against the month-end close twelve months back."""
    if not share or not index:
        return []
    q = sorted((quarter_end(d), v) for d, v in share)
    me = month_ends(index)
    by_month = {d[:7]: (d, v) for d, v in me}
    out = []
    for d, v in me:
        # By month: a quarter ending 30 June closes with June's last session.
        prior = [x for x in q if x[0][:7] <= d[:7]]
        if not prior:
            continue
        qe, s = prior[-1]
        y, mo = int(d[:4]) - 1, int(d[5:7])
        back = by_month.get(f"{y:04d}-{mo:02d}")
        if back is None or back[1] <= 0:
            continue
        is_q = qe[:7] == d[:7]
        if is_q:
            share_m = s
        else:
            base = [c for c in me if c[0][:7] <= qe[:7]]
            if not base or base[-1][1] <= 0:
                continue
            share_m = marked(s, v / base[-1][1] - 1.0)
        yoy = (v / back[1] - 1.0) * 100.0
        out.append({"month": d[:7], "close_day": d, "share_pct": round(share_m, 3),
                    "quarter_end": qe, "marked": not is_q,
                    "spx_yoy_pct": round(yoy, 2),
                    "impulse_pp": round(share_m * yoy / 100.0, 3)})
    return out


def impulse(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    cfg = cfg if cfg is not None else config()
    c = cfg.get("impulse") or {}
    share = rt._pts(st, c.get("share_key", "fred.hh_equity_share"), cutoff)  # noqa: SLF001
    index = rt._pts(st, c.get("index_key", "yfinance.mkt_gspc"), cutoff)    # noqa: SLF001
    s = series(share, index)
    gap = " ".join(str(c.get("ici_gap") or "").split())
    if not s:
        why = ("Z.1's equity share is not stored" if not share else
               "SPX's closes are not stored" if not index else
               "no month holds both a Z.1 quarter and a year of SPX")
        return {"absent": True, "reason": why, "ici_gap": gap}
    last = s[-1]
    years = (c.get("windows_years") or [5])[0]
    lz = rt.lens([(x["close_day"], x["impulse_pp"]) for x in s], years)
    return {"absent": False, "latest": last, "lens": lz, "n": len(s),
            "from": s[0]["month"], "ici_gap": gap, "series": s}


def _yoy(pts: list[tuple[str, float]]) -> list[tuple[str, float]]:
    d = dict(pts)
    out = []
    for day, v in pts:
        back = d.get(f"{int(day[:4]) - 1:04d}{day[4:]}")
        if back:
            out.append((day, round((v / back - 1.0) * 100.0, 2)))
    return out


def net(st, cutoff: str, cfg: Optional[dict] = None, rcfg: Optional[dict] = None) -> dict:
    """The legs side by side. Each says how it is scaled; none is weighted."""
    cfg = cfg if cfg is not None else config()
    n = cfg.get("net") or {}
    lo, hi = float(n.get("tight_low_pctile", 20)), float(n.get("tight_high_pctile", 80))
    rcfg = rcfg if rcfg is not None else rt.config()
    t = rt.tightening(st, cutoff, rcfg)
    h = rt.housing(st, cutoff, rcfg)
    q = rt.quality_tail(st, cutoff, rcfg)
    w = impulse(st, cutoff, cfg)
    legs: list[dict[str, Any]] = []
    # Item 34: a flag, so it is read as a flag (on, off or absent), never ranked.
    legs.append({"item": 34, "side": "tightening", "label": "the market's tightening flag",
                 "scale": "a flag (the 10-year up and 12-month policy pricing down over its window)",
                 "state": t.get("state"),
                 "tight": None if t.get("state") == "absent" else t.get("state") == "on",
                 "text": rt.tightening_line(t)})
    # Item 36: pending sales' year-on-year change, placed by its own history.
    hk = (rcfg.get("housing") or {}).get("pending_key", "redfin.pending_sales")
    hy = _yoy(rt._pts(st, hk, cutoff))                           # noqa: SLF001
    hl = rt.lens(hy) if hy else None
    hp = (hl or {}).get("percentile_window") if hl and not hl.get("same") else \
        (hl or {}).get("percentile_full")
    legs.append({"item": 36, "side": "tightening", "label": "housing: pending sales, year on year",
                 "scale": "its own-history percentile (Redfin, single-source)",
                 "value": None if h.get("absent") else h.get("pending_yoy_pct"),
                 "lens": hl, "tight": None if hp is None else hp <= lo,
                 "text": (f"pending sales {h['pending_yoy_pct']:+.1f}% on the year, "
                          f"{rt.lens_text(hl)}") if hl and not h.get("absent")
                 and h.get("pending_yoy_pct") is not None else
                 f"housing: {h.get('reason', 'not stored')}"})
    # Item 41: the quality tail, CCC less BB, placed by its own history.
    ql = q.get("ccc_bb_lens") if not q.get("absent") else None
    qp = None if not ql else (ql.get("percentile_window") if not ql.get("same")
                              else ql.get("percentile_full"))
    legs.append({"item": 41, "side": "tightening", "label": "the quality tail: CCC less BB",
                 "scale": "its own-history percentile (ICE BofA OAS via FRED)",
                 "value": q.get("ccc_bb_bp"), "lens": ql,
                 "tight": None if qp is None else qp >= hi,
                 "text": (f"CCC less BB {q['ccc_bb_bp']:.0f} bp, {rt.lens_text(ql)}")
                 if ql else f"quality tail: {q.get('reason', 'not stored')}"})
    # Item 66: the loosening leg.
    wl = w.get("lens") if not w.get("absent") else None
    wp = None if not wl else (wl.get("percentile_window") if not wl.get("same")
                              else wl.get("percentile_full"))
    legs.append({"item": 66, "side": "loosening", "label": "the wealth-effect impulse",
                 "scale": "its own-history percentile (Z.1 share x SPX year on year)",
                 "value": None if w.get("absent") else w["latest"]["impulse_pp"],
                 "lens": wl, "loose": None if wp is None else wp >= hi,
                 "tight": None if wp is None else wp <= lo,
                 "text": impulse_line(w)})
    read_t = [x for x in legs if x["side"] == "tightening" and x["tight"] is not None]
    return {"legs": legs, "bands": [lo, hi], "impulse": w,
            "tight_count": sum(1 for x in read_t if x["tight"]), "read_count": len(read_t),
            "k_shape_gap": " ".join(str(n.get("k_shape_gap") or "").split()),
            "report_only": True}


def _month(m: str) -> str:
    return dt.date.fromisoformat(m + "-01").strftime("%b %Y")


def impulse_line(w: dict) -> str:
    if w.get("absent"):
        return f"Wealth-effect impulse: not built ({w['reason']})."
    x = w["latest"]
    how = (f"the Z.1 share of {x['share_pct']:.1f}% marked to SPX from the quarter "
           f"ending {_month(x['quarter_end'][:7])}" if x["marked"] else
           f"the Z.1 share of {x['share_pct']:.1f}% for the quarter")
    return (f"Wealth-effect impulse, {_month(x['month'])}: {x['impulse_pp']:+.2f} pp of "
            f"household financial assets ({how}, times SPX {x['spx_yoy_pct']:+.1f}% on "
            f"the year), {rt.lens_text(w['lens'])}.")


def net_lines(b: dict) -> list[str]:
    lo, hi = b["bands"]
    out = [f"Net transmission, side by side (no leg is weighted or summed; each is "
           f"scaled on its own, and a level leg reads tight past its {ordinal(lo)} or "
           f"{ordinal(hi)} percentile): tightening legs reading tight, {b['tight_count']} "
           f"of {b['read_count']} read."]
    for x in b["legs"]:
        mark = ("loose" if x.get("loose") else "tight" if x.get("tight") else
                "not read" if x.get("tight") is None else "neither")
        out.append(f"Item {x['item']} ({x['side']}; {x['scale']}), {mark}: "
                   f"{x['text'].rstrip('.')}.")
    out.append(f"{b['k_shape_gap'][0].upper()}{b['k_shape_gap'][1:]}.")
    return out


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m altdata.transmission")
    ap.add_argument("cmd", choices=["show"])
    ap.add_argument("--as-of")
    ap.add_argument("--db")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from altdata import observations, session  # noqa: PLC0415
    with observations.ObservationStore(a.db) as st:
        for ln in net_lines(net(st, a.as_of or session.utc_iso())):
            print(ln)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
