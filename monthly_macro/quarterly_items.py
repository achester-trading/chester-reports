"""
The Quarterly's chapter items, as builders the chapter shell calls (AQ-2 part 1;
change order of 10 Oct 2026, section 4.1 item by item).

Each builder returns sub-sections in the stack's form, and EVERY ONE DEGRADES:
an item whose source is absent prints its not-yet footnote with the reason,
never a blank and never an invented figure. What each item reads is declared in
config/quarterly_chapters.yaml; the hooks into the branches not merged under
this one (AQ-4's horizon charts, AQ-5's correlation layer, AQ-6's thesis
register, AQ-8a's attribution and paper bid) each name their module and print
"not yet -- <branch>" when it is absent.

    lead       the confidence and what-changed lines; 1, 2; 3 (the quarter's
               five lines and its three charts)
    reference  3 (why: the QTD/YTD table and the driver attribution); 3a; 4 (and
               oil's second half, currency's pair universe); 5; 6; 7; 8; 9; 10; 11

Everything a builder prints is read from the store as of the edition's cutoff
over the payload's quarter window, or from a hook's module; the two written
reads (item 5's paragraph and item 11's lines) go through the stack's writer and
its audit, and their frames offer no more figures than the item's budget.
"""

from __future__ import annotations

import datetime as dt
import importlib
import json
import logging
import math
import re
import sqlite3
from pathlib import Path
from typing import Any, Optional

from altdata import derived

log = logging.getLogger("monthly_macro.quarterly_items")

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "quarterly_chapters.yaml"
LEAD, REFERENCE = "lead", "reference"

# The hooks' modules, beside AQ-1's (quarterly.HOOK_MODULES). Named once so a
# gate can point one at a module that is absent and watch it degrade.
ITEM_MODULES = {"horizon": "tools.horizon_charts",
                "attribution": "altdata.attribution",
                "paper_bid": "altdata.paper_bid",
                "correlation": "altdata.correlation",
                "thesis": "altdata.thesis_register",
                "exposure": "tools.exposure_compute"}
WAITS = {"horizon": "AQ-4 (the horizon charts)",
         "attribution": "AQ-8a (the attribution layer)",
         "paper_bid": "AQ-8a (the paper bid)",
         "correlation": "AQ-5 (the correlation layer)",
         "thesis": "AQ-6 (the thesis register)",
         "exposure": "the chain store"}
AQ7 = "not yet — the quarterly scan (AQ-7)"


def load_config(path: Optional[Path] = None) -> dict:
    import yaml  # noqa: PLC0415
    with Path(path or CONFIG_PATH).open(encoding="utf-8") as fp:
        return yaml.safe_load(fp) or {}


def family_config(fam_id: str, cfg: Optional[dict] = None) -> Optional[dict]:
    """The filled chapter's block, or None for a chapter still on the shell."""
    c = cfg or load_config()
    f = (c.get("families") or {}).get(fam_id)
    return f if f and f.get("filled") else None


def module(kind: str):
    try:
        return importlib.import_module(ITEM_MODULES[kind])
    except ImportError:
        return None


def not_yet(kind: str) -> str:
    return f"not yet — {WAITS[kind]} is not on this build"


# ---------------------------------------------------------------------------
# Store reads, over the quarter window, as of the cutoff
# ---------------------------------------------------------------------------
def rows(st, key: str, now: str, inst: Optional[str] = None,
         end: Optional[str] = None) -> list[tuple[str, float]]:
    """(day, value) knowable at `now`, observed on or before `end`."""
    out = []
    for r in st.as_of(key, now, inst):
        if r.get("value_num") is None:
            continue
        d = str(r["observed_at"])[:10]
        if end is None or d <= end:
            out.append((d, float(r["value_num"])))
    out.sort()
    return out


def level_on(pts: list[tuple[str, float]], day: str) -> Optional[tuple[str, float]]:
    best = None
    for d, v in pts:
        if d <= day:
            best = (d, v)
    return best


def units(key: str) -> str:
    return str(derived.registry_entry(key).get("units") or "")


def fmt_level(v: float, key: str) -> str:
    u = units(key)
    if u in ("%", "percent", "bps", "bp"):
        return f"{v:,.2f}%" if u in ("%", "percent") else f"{v:,.0f} bp"
    if u in ("count", "N"):
        return f"{v:,.0f}"
    if abs(v) >= 1000:
        return f"{v:,.1f}"
    return f"{v:,.2f}"


def change_text(a: float, b: float, key: str) -> tuple[Optional[float], str]:
    """The change from b to a in the series' delta unit, printed signed."""
    from altdata import numeral_audit as na  # noqa: PLC0415
    du = derived.delta_unit_for(key)[0]
    u = units(key)
    if du == "bps":
        bp = (a - b) * (1.0 if u in ("bps", "bp") else 100.0)
        return bp, f"{'+' if bp > 0 else '−' if bp < 0 else ''}{abs(bp):,.0f} bp"
    if du == "percent" and b:
        p = 100.0 * (a / b - 1.0)
        return p, f"{'+' if p > 0 else '−' if p < 0 else ''}{abs(p):,.1f}%"
    d = a - b
    disp = na.change_display(d, u)
    return d, disp or f"{'+' if d > 0 else '−' if d < 0 else ''}{abs(d):,.2f}"


def ordinal(x: float) -> str:
    n = int(math.floor(x + 0.5))
    sfx = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{sfx}"


def quarter_move(st, spec: dict, ctx: dict) -> Optional[dict]:
    key, inst = spec["key"], spec.get("instrument")
    pts = rows(st, key, ctx["now"], inst, ctx["end"])
    a, b = level_on(pts, ctx["end"]), level_on(pts, ctx["start"])
    if not a:
        return None
    out = {"key": key, "label": spec.get("label") or key, "level": a[1],
           "as_of": a[0], "level_text": fmt_level(a[1], key), "n": len(pts),
           "values": [v for _, v in pts]}
    if b and b[0] != a[0]:
        out["change"], out["change_display"] = change_text(a[1], b[1], key)
        out["from"] = b[0]
    return out


# ---------------------------------------------------------------------------
# The lead lines: confidence and what changed
# ---------------------------------------------------------------------------
def voices_rows(ctx: dict, subjects: list[str]) -> list[dict]:
    """The quarter's stored voices rows on the family's subjects."""
    try:
        from altdata import voices as vmod  # noqa: PLC0415
        with vmod.VoicesStore(ctx.get("db_path"), readonly=True) as vs:
            got = vs.rows(as_of=ctx["now"], since=ctx["start"],
                          until=(dt.date.fromisoformat(ctx["end"])
                                 + dt.timedelta(days=1)).isoformat())
    except Exception:                                           # noqa: BLE001
        return []
    out = []
    for r in got:
        ds = [d for d in r.get("directions") or [] if d.get("subject") in subjects]
        if ds:
            out.append({**r, "family_directions": ds})
    return out


def dissent_line(vrows: list[dict]) -> str:
    """The standing DISSENT: the latest view per voice on the family's subjects,
    and the minority direction named with its voice."""
    latest: dict[str, tuple] = {}
    for r in vrows:
        for d in r["family_directions"]:
            if d.get("direction") in ("bullish", "bearish"):
                latest[r["voice"]] = (d["direction"], r)
    sides: dict[str, list] = {"bullish": [], "bearish": []}
    for v, (d, r) in latest.items():
        sides[d].append(r)
    if not latest:
        return "Standing dissent: none — no stored voice took a side this quarter."
    if not sides["bullish"] or not sides["bearish"]:
        one = "bullish" if sides["bullish"] else "bearish"
        return (f"Standing dissent: none — every stored voice ({len(latest)}) "
                f"was {one}.")
    minority = "bearish" if len(sides["bullish"]) > len(sides["bearish"]) else (
        "bullish" if len(sides["bearish"]) > len(sides["bullish"]) else None)
    if minority is None:
        return "Standing dissent: the stored voices split evenly; no side dissents."
    r = sides[minority][-1]
    return (f"Standing dissent: {r['voice']} ({r.get('affiliation') or '—'}), "
            f"{minority}, {str(r.get('published_at'))[:10]} — against "
            f"{len(latest) - len(sides[minority])} on the other side.")


def brier_line(ch: dict, ctx: dict) -> str:
    tr = module("thesis")
    if tr is None:
        return f"Brier to date: {not_yet('thesis')}."
    try:
        gs = [g for g in tr.grades(ctx.get("db_path"), now=ctx["now"],
                                   family=ch.get("thesis_family"))
              if g.get("mean_brier") is not None]
    except Exception as exc:                                    # noqa: BLE001
        return f"Brier to date: FAULT (code, not data) -- {type(exc).__name__}."
    if not gs:
        return "Brier to date: no thesis of this chapter's is graded yet."
    n = sum(g["resolved"] for g in gs)
    b = sum(g["mean_brier"] * g["resolved"] for g in gs) / max(1, n)
    return f"Brier to date: {b:.4f} over {n} graded weights (a coin scores 0.25)."


def weakest_link(st, fam: dict, ctx: dict) -> str:
    specs = [s for s in fam.get("structure") or []] + list(fam.get("five_lines") or [])
    tracked = [s for s in specs if s.get("key")]
    absent = [s for s in fam.get("structure") or [] if s.get("absent")]
    worst = None
    for s in tracked:
        pts = rows(st, s["key"], ctx["now"], s.get("instrument"), ctx["end"])
        last = pts[-1][0] if pts else None
        age = ((dt.date.fromisoformat(ctx["end"]) - dt.date.fromisoformat(last)).days
               if last else 10 ** 6)
        if worst is None or age > worst[0]:
            worst = (age, s["label"], last)
    head = "Weakest link: "
    if worst is None:
        head += "no tracked series"
    elif worst[2] is None:
        head += f"{worst[1]}, nothing stored by the quarter's end"
    else:
        head += (f"{worst[1]}, last observed {worst[2]} ({worst[0]} days before the "
                 f"quarter's end)")
    n_struct = len(fam.get("structure") or [])
    return head + f"; {len(absent)} of {n_struct} structure series not tracked."


def lead_lines(st, ch: dict, fam: dict, ctx: dict, now_states: dict) -> dict:
    vrows = voices_rows(ctx, fam.get("voices_subjects") or [])
    conf = " ".join([weakest_link(st, fam, ctx), brier_line(ch, ctx),
                     dissent_line(vrows)])
    prior = (ctx.get("prior_chapters") or {}).get(ch["id"])
    if not prior:
        changed = ("What changed: the first Quarterly with this chapter filled — "
                   "nothing to compare against.")
    else:
        old = (prior.get("data") or {}).get("falsification") or {}
        moved = [f"{k}: {old[k]} to {v}" for k, v in now_states.items()
                 if k in old and old[k] != v]
        changed = ("What changed: " + "; ".join(moved) + "." if moved else
                   "What changed: no falsification test changed state since the "
                   "last Quarterly.")
    return {"title": "Confidence, and what changed", "item": "lead_lines",
            "tier": LEAD, "lines": [conf, changed]}


# ---------------------------------------------------------------------------
# Item 3: the quarter
# ---------------------------------------------------------------------------
def five_lines(st, fam: dict, ctx: dict) -> tuple[list[str], list[dict], list[str]]:
    lines, moves, nt = [], [], []
    for spec in (fam.get("five_lines") or [])[:5]:
        m = quarter_move(st, spec, ctx)
        if m is None:
            nt.append(f"{spec['label']}: nothing stored by the quarter's end")
            continue
        moves.append(m)
        ch_ = (f", {m['change_display']} on the quarter (from {m['from']})"
               if m.get("change_display") else ", no prior level in the window")
        lines.append(f"{m['label']}: {m['level_text']} at {m['as_of']}{ch_}.")
    return lines, moves, nt


def _chart_series(st, spec: dict, ctx: dict, years: int = 5) -> list[tuple[str, float]]:
    since = (dt.date.fromisoformat(ctx["end"])
             - dt.timedelta(days=int(365.25 * years))).isoformat()
    return [(d, v) for d, v in rows(st, spec["key"], ctx["now"], spec.get("instrument"),
                                    ctx["end"]) if d >= since]


def structure_chart(st, spec: dict, cid: str, ctx: dict) -> dict:
    """One of the chapter's two structure charts, five years to the quarter's
    end, in the house style (daily_cascade.charts)."""
    try:
        from daily_cascade import charts as chm  # noqa: PLC0415
        legs = [(s, _chart_series(st, s, ctx)) for s in spec["series"]]
        short = [s["label"] for s, pts in legs if len(pts) < 20]
        if short:
            return {"id": cid, "unavailable": f"{spec['title']}: under 20 observations "
                                              f"stored for {', '.join(short)}"}
        fig, ax = chm._base(f"{spec['title']}, five years to {ctx['end']}")
        colours = ("#0d2b45", "#d97706")
        (s0, p0) = legs[0]
        x0 = [dt.date.fromisoformat(d) for d, _ in p0]
        ax.plot(x0, [v for _, v in p0], color=colours[0], linewidth=0.9,
                label=s0["label"])
        ax.set_ylabel(s0["label"], fontsize=7, color=colours[0])
        if len(legs) > 1:
            s1, p1 = legs[1]
            tgt = ax.twinx() if spec.get("kind") == "twin" else ax
            x1 = [dt.date.fromisoformat(d) for d, _ in p1]
            tgt.plot(x1, [v for _, v in p1], color=colours[1], linewidth=0.9,
                     label=s1["label"])
            if tgt is not ax:
                tgt.set_ylabel(s1["label"], fontsize=7, color=colours[1])
                tgt.tick_params(labelsize=7)
                if s1.get("invert"):
                    tgt.invert_yaxis()
                for side in ("top",):
                    tgt.spines[side].set_visible(False)
        out = chm._finish(fig, f"{ctx['prefix']}_{cid.lower()}", ctx.get("out_dir"))
        last = [f"{s['label']} {fmt_level(pts[-1][1], s['key'])} ({pts[-1][0]})"
                for s, pts in legs]
        return {"id": cid, "title": spec["title"],
                "caption": f"{spec['title']}, five years to {ctx['end']}; latest "
                           + "; ".join(last), **out}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": cid, "unavailable": f"{type(exc).__name__}: {exc}"}


def long_frame_chart(st, fam: dict, cid: str, ctx: dict) -> dict:
    """The family's long frame, from AQ-4's horizon charts."""
    hc = module("horizon")
    if hc is None:
        return {"id": cid, "unavailable": f"the family's long frame: {not_yet('horizon')}"}
    try:
        cfg = hc.load_config()
        res = hc.compute(st, cfg, ctx["end"])
        d = Path(ctx.get("out_dir") or ".")
        path, info = hc.draw_frame(res, cfg, fam["horizon_family"], d)
        if not path:
            return {"id": cid, "unavailable": f"the family's long frame: "
                                              f"{(info or {}).get('reason') or 'nothing stored'}"}
        png = Path(path).read_bytes()
        return {"id": cid, "title": f"{fam['horizon_family']} long frame",
                "caption": f"The family's twenty-year frame, rebased, to {ctx['end']} "
                           f"(AQ-4)", "png": png, "png_bytes": len(png),
                "svg_path": None}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": cid, "unavailable": f"the family's long frame: FAULT "
                                          f"{type(exc).__name__}"}


def horizon_table(st, fam: dict, ctx: dict) -> dict:
    hc = module("horizon")
    if hc is None:
        return {"not_tracked": [f"the QTD/YTD table: {not_yet('horizon')}"]}
    try:
        res = hc.compute(st, hc.load_config(), ctx["end"])
    except Exception as exc:                                    # noqa: BLE001
        return {"notes": [f"the QTD/YTD table: FAULT (code, not data) -- "
                          f"{type(exc).__name__}"]}
    rws = []
    for a in res.get("assets") or []:
        if a.get("family") != fam["horizon_family"]:
            continue
        q, y = a.get("qtd") or {}, a.get("ytd") or {}
        rws.append([a.get("label") or a.get("id"),
                    f"{100 * q['value']:+.1f}%" if q.get("value") is not None else "—",
                    f"{100 * y['value']:+.1f}%" if y.get("value") is not None else "—"])
    return ({"table": {"columns": ["Asset", "Quarter to date", "Year to date"],
                       "rows": rws}} if rws else
            {"lines": ["No asset of this family is in the horizon table at this cutoff."]})


def driver_row(st, ch: dict, ctx: dict) -> dict:
    at = module("attribution")
    if at is None:
        return {"not_tracked": [f"the driver attribution: {not_yet('attribution')}"]}
    try:
        t = at.driver_table(st, ctx["now"])
    except Exception as exc:                                    # noqa: BLE001
        return {"notes": [f"the driver attribution: FAULT (code, not data) -- "
                          f"{type(exc).__name__}"]}
    assets = set(ch.get("correlation_assets") or [])
    keep = [r for r, d in zip(t.get("rows") or [], t.get("data") or [])
            if d.get("family") in assets]
    if not keep:
        return {"lines": ["No driver-attribution row is stored for this chapter's "
                          "assets at this cutoff."]}
    cols = ["Family", "Explained share", "Largest loading", "Residual's sign",
            "Sign stability", "Month"]
    return {"table": {"columns": cols, "rows": keep}}


def item_quarter(st, ch: dict, fam: dict, ctx: dict) -> list[dict]:
    lines, moves, nt = five_lines(st, fam, ctx)
    charts = [long_frame_chart(st, fam, ctx["next_cid"](), ctx)]
    for spec in (fam.get("structure_charts") or [])[:2]:
        charts.append(structure_chart(st, spec, ctx["next_cid"](), ctx))
    for c in charts:
        ctx["charts"][c["id"]] = c
    lead = {"title": "3 · The quarter", "item": "quarter", "tier": LEAD,
            "lines": lines, "not_tracked": nt,
            "charts_rendered": [c["id"] for c in charts],
            "data": {"moves": [{k: m[k] for k in ("label", "level_text", "as_of",
                                                  "change_display") if k in m}
                               for m in moves]}}
    why = {"title": "3 · The quarter: why", "item": "quarter_why", "tier": REFERENCE,
           "lines": [], "not_tracked": [], "notes": []}
    for part in (horizon_table(st, fam, ctx), driver_row(st, ch, ctx)):
        if part.get("table") and why.get("table"):
            why.setdefault("tables", []).append(part["table"])
        elif part.get("table"):
            why["table"] = part["table"]
        why["lines"] += part.get("lines") or []
        why["not_tracked"] += part.get("not_tracked") or []
        why["notes"] += part.get("notes") or []
    ctx["moves"] = moves
    return [lead, why]


# ---------------------------------------------------------------------------
# Item 3a: what's priced
# ---------------------------------------------------------------------------
def implied_range(sym: str, ctx: dict) -> tuple[Optional[list], Optional[str]]:
    ex = module("exposure")
    if ex is None:
        return None, f"{sym}: {not_yet('exposure')}"
    end = dt.date.fromisoformat(ctx["end"])
    path = None
    for back in range(8):
        day = (end - dt.timedelta(days=back)).isoformat()
        got = ex.newest_chains(date=day, symbols=[sym],
                               base_dir=ctx.get("chain_dir"))
        if got.get(sym):
            path = got[sym]
            break
    if path is None:
        return None, (f"{sym}: no chain logged in the week to the quarter's end "
                      f"(the capture logs GLD, SLV, USO from AQ-8a; FXE and FXY are "
                      f"not captured)")
    rc = ctx["common"].get("implied_range") or {}
    rws = [r for r in ex.load_chain(path) if r.get("implied_vol") and r.get("strike")
           and (r.get("dte") or 0) >= int(rc.get("min_days") or 7)]
    if not rws:
        return None, f"{sym}: the logged chain carries no implied volatility"
    target = int(rc.get("target_days") or 91)
    dte = min({r["dte"] for r in rws}, key=lambda d: abs(d - target))
    exp = [r for r in rws if r["dte"] == dte]
    spot = next((r["spot"] for r in exp if r.get("spot")), None)
    if not spot:
        return None, f"{sym}: the logged chain carries no spot"
    k = min({r["strike"] for r in exp}, key=lambda s: abs(s - spot))
    ivs = [r["implied_vol"] for r in exp if r["strike"] == k]
    iv = sum(ivs) / len(ivs)
    t = dte / 365.0
    lo, hi = spot * math.exp(-iv * math.sqrt(t)), spot * math.exp(iv * math.sqrt(t))
    return [sym, f"{spot:,.2f}", f"{100 * iv:.1f}%", f"{dte} days",
            f"{lo:,.2f} to {hi:,.2f}", str(path.parent.name)], None


def item_priced(st, fam: dict, ctx: dict) -> dict:
    out = {"title": "3a · What's priced", "item": "priced", "tier": REFERENCE,
           "lines": [], "not_tracked": []}
    cv = fam.get("curve") or {}
    if cv.get("key"):
        pts = rows(st, cv["key"], ctx["now"], None, ctx["end"])
        if pts:
            out["lines"].append(f"The curve's one stored point: "
                                f"{derived.registry_entry(cv['key']).get('description') or cv['key']} "
                                f"{fmt_level(pts[-1][1], cv['key'])} ({pts[-1][0]}).")
    out["not_tracked"].append(f"the curve against spot and the roll: "
                              f"{cv.get('waits') or 'arrives with 6b'}")
    rng, gaps = [], []
    for sym in fam.get("implied_range_symbols") or []:
        row, why = implied_range(sym, ctx)
        if row:
            rng.append(row)
        else:
            gaps.append(why)
    if rng:
        out["table"] = {"columns": ["Fund", "Spot", "ATM implied vol", "Expiry",
                                    "One-sigma range to expiry", "Chain day"],
                        "rows": rng}
    out["not_tracked"] += [f"the options-implied range, {g}" for g in gaps]
    out["not_tracked"].append(f"the consensus and agency forecasts against spot: {AQ7}")
    return out


# ---------------------------------------------------------------------------
# Item 4: structure, with dual percentiles
# ---------------------------------------------------------------------------
STRUCTURE_COLUMNS = ["Series", "Latest (as of)", "Change on the quarter",
                     "Percentile, full history", "Percentile, five years"]


def structure_rows(st, specs: list[dict], ctx: dict) -> tuple[list, list, dict]:
    rws, nt, pct = [], [], {}
    five = ctx["common"].get("five_year_column") or "until the lenses"
    for s in specs:
        if s.get("absent") or not s.get("key"):
            nt.append(f"{s['label']}: {s.get('absent') or 'no key'}")
            continue
        m = quarter_move(st, s, ctx)
        if m is None:
            nt.append(f"{s['label']}: nothing stored by the quarter's end")
            continue
        p = derived.percentile_of(m["values"], m["level"]) if m["n"] >= 20 else None
        pct[s["label"]] = None if p is None else round(p)
        rws.append([s["label"], f"{m['level_text']} ({m['as_of']})",
                    m.get("change_display") or "—",
                    (f"{ordinal(p)} (n={m['n']:,})" if p is not None
                     else f"— (n={m['n']:,})"), five])
    return rws, nt, pct


def item_structure(st, fam: dict, ctx: dict) -> dict:
    rws, nt, pct = structure_rows(st, fam.get("structure") or [], ctx)
    out = {"title": "4 · Structure", "item": "structure", "tier": REFERENCE,
           "not_tracked": nt, "data": {"percentiles": pct}}
    if rws:
        out["table"] = {"columns": STRUCTURE_COLUMNS, "rows": rws}
    else:
        out["lines"] = ["No structure series is stored at this cutoff."]
    return out


def item_second_half(st, fam: dict, ctx: dict, states: dict) -> Optional[dict]:
    sh = fam.get("second_half")
    if not sh:
        return None
    rws, nt, _ = structure_rows(st, sh.get("structure") or [], ctx)
    tests = {t["id"]: t for t in fam.get("falsification") or []}
    lines = [f"{states.get(i, {}).get('state', 'not measured')}: "
             f"{tests[i]['statement']}" for i in sh.get("tests") or [] if i in tests]
    out = {"title": f"4b · {sh['title']}", "item": "second_half", "tier": REFERENCE,
           "not_tracked": nt, "lines": lines}
    if rws:
        out["table"] = {"columns": STRUCTURE_COLUMNS, "rows": rws}
    return out


def item_pairs(st, fam: dict, ctx: dict) -> Optional[dict]:
    pr = fam.get("pairs")
    if not pr:
        return None
    deep, nt = [], []
    for p in pr.get("deep") or []:
        if not p.get("key"):
            nt.append(f"{p['pair']}: {p.get('absent')}")
            continue
        m = quarter_move(st, {"key": p["key"], "label": p["pair"]}, ctx)
        if m is None:
            nt.append(f"{p['pair']}: nothing stored by the quarter's end")
            continue
        pc = derived.percentile_of(m["values"], m["level"]) if m["n"] >= 20 else None
        lo, hi = min(m["values"]), max(m["values"])
        deep.append([p["pair"], f"{m['level_text']} ({m['as_of']})",
                     m.get("change_display") or "—",
                     f"{ordinal(pc)} (n={m['n']:,})" if pc is not None else "—",
                     f"{lo:,.4g} to {hi:,.4g}"])
    scan = [[p["pair"], "not tracked", p.get("absent") or "—"]
            for p in pr.get("scan") or []]
    out = {"title": "4c · The pair universe", "item": "pairs", "tier": REFERENCE,
           "not_tracked": nt,
           "lines": ["The deep basket, a pair each; the scan tier from FRED's H.10 "
                     "set. Priority is refreshed each quarter."]}
    if deep:
        out["table"] = {"columns": ["Pair (deep basket)", "Latest (as of)",
                                    "Change on the quarter",
                                    "Percentile, full history",
                                    "Stored envelope"], "rows": deep}
    out["tables"] = [{"columns": ["Pair (scan tier)", "State", "Why"], "rows": scan}]
    return out


# ---------------------------------------------------------------------------
# Item 5: supply and demand -- the agency tables, and one written read
# ---------------------------------------------------------------------------
_MASK = re.compile(r"[+\-−±]?\$?\d[\d,]*(?:\.\d+)?(?:\s?(?:%|(?:bps|bp|tn|bn|mn|k)\b))?")


def mask(text: Optional[str]) -> str:
    """A voice's view with its figures masked: the paragraph cites the stored
    figures, never a number retyped from a quoted view."""
    return _MASK.sub("[n]", str(text or ""))


def budget_moves(moves: list[dict], n: int) -> tuple[list[dict], list[str]]:
    """T3.4's rule at the frame: the largest moves, at most `n`, each with its
    display; the rest by name only."""
    def size(m):
        try:
            return abs(float(m.get("change") or 0.0)) / (abs(float(m["level"])) or 1.0)
        except (TypeError, ValueError):
            return 0.0
    ranked = sorted([m for m in moves if m.get("change_display")], key=size,
                    reverse=True)
    take = ranked[:max(0, n)]
    return ([{"series": m["label"], "change_display": m["change_display"]}
             for m in take],
            [m["label"] for m in moves if m not in take])


FOUR_QUESTIONS = ("who is the marginal buyer and the marginal seller this quarter; "
                  "what is the buffer or the effective float; what binds -- the "
                  "constraint that sets price; what would make the marginal buyer "
                  "step away")


def item_supply(ch: dict, fam: dict, ctx: dict) -> dict:
    out = {"title": "5 · Supply and demand", "item": "supply", "tier": REFERENCE,
           "not_tracked": [f"the agency balances (WGC, Silver Institute, ICSG, EIA "
                           f"STEO, IEA OMR, OPEC MOMR, COFER, as the chapter needs): "
                           f"{AQ7}"], "lines": []}
    vrows = voices_rows(ctx, fam.get("voices_subjects") or [])
    if not vrows:
        out["lines"].append("The four questions: no stored source, not printed — no "
                            "stored voice on this family this quarter.")
        return out
    cap = int((fam.get("figure_budget") or {}).get("supply", 4))
    cite, names = budget_moves(ctx.get("moves") or [], cap)
    out["phase"] = f"block:quarterly:{ch['id']}:supply"
    out["prose"] = {"words": "80 to 120", "figures": cap,
                    "scope": ("answer the four questions every chapter answers -- "
                              + FOUR_QUESTIONS + " -- ONLY from the figures given and "
                              "the stored voices' views; a question the data cannot "
                              "answer is said to be unanswered"),
                    "note": banned_note(fam)}
    out["data"] = {"figures_you_may_cite": cite, "also_moved": names,
                   "voices": [{"voice": r["voice"],
                               "affiliation": r.get("affiliation"),
                               "published": str(r.get("published_at"))[:10],
                               "view": mask(r.get("view")),
                               "direction": [d.get("direction")
                                             for d in r["family_directions"]]}
                              for r in vrows[-8:]]}
    return out


def banned_note(fam: dict) -> str:
    w = fam.get("words") or {}
    out = ""
    if w.get("banned"):
        out += " Never write in this chapter: " + "; ".join(
            f"'{x}'" for x in w["banned"]) + "."
    if w.get("permitted"):
        out += " The chapter's own terms, used as the paper uses them: " + "; ".join(
            w["permitted"]) + "."
    return out


# ---------------------------------------------------------------------------
# Item 6: the analyses
# ---------------------------------------------------------------------------
def analysis_state(st, a: dict, ctx: dict) -> str:
    if a.get("waits"):
        return f"not yet — {a['waits']}"
    if a.get("module"):
        kind = {"altdata.attribution": "attribution", "altdata.paper_bid": "paper_bid",
                "altdata.correlation": "correlation"}[a["module"]]
        m = module(kind)
        if m is None:
            return not_yet(kind)
        try:
            if a.get("reader") == "gold_block":
                b = m.gold_block(st, ctx["now"])
                r = (b.get("rows") or [None])[0]
                return (f"{r[0]}: {r[1]}" if r else
                        "no gold-residual row stored at this cutoff")
            if a.get("reader") == "two_bid":
                s = m.two_bid_state(st, ctx["now"])
                return " ".join(m.two_bid_lines(s)) or "no two-bid state yet"
            if a.get("reader") in ("corr_triple", "attr_triple"):
                t = m.triple(st, a["key"], ctx["now"])
                return (f"{t['latest']:+.2f} ({t['as_of']})" if t else
                        f"no {a['key']} row stored at this cutoff")
        except Exception as exc:                                # noqa: BLE001
            return f"FAULT (code, not data) -- {type(exc).__name__}"
    vals = []
    for k in a.get("series") or []:
        pts = rows(st, k, ctx["now"], None, ctx["end"])
        if pts:
            vals.append(f"{fmt_level(pts[-1][1], k)} ({pts[-1][0]})")
    return "; ".join(vals) if vals else "nothing stored at this cutoff"


def item_analyses(st, fam: dict, ctx: dict) -> dict:
    rws = [[a["title"], analysis_state(st, a, ctx), a.get("kill") or "—"]
           for a in fam.get("analyses") or []]
    out = {"title": "6 · The analyses", "item": "analyses", "tier": REFERENCE}
    if rws:
        out["table"] = {"columns": ["Analysis", "State", "Kill condition (as ruled)"],
                        "rows": rws}
    else:
        out["not_tracked"] = ["no analysis is ruled for this chapter"]
    return out


# ---------------------------------------------------------------------------
# Item 7: falsification tests, computed by code
# ---------------------------------------------------------------------------
def _quarter_ends(end: str, n: int) -> list[str]:
    d = dt.date.fromisoformat(end)
    out = [d]
    for _ in range(n):
        first = d.replace(month=3 * ((d.month - 1) // 3) + 1, day=1)
        d = first - dt.timedelta(days=1)
        out.append(d)
    return [x.isoformat() for x in out]


def _leaf(st, kind: str, p: dict, ctx: dict) -> dict:
    end = ctx["end"]
    if kind == "quarters_negative":
        pts = rows(st, p["series"], ctx["now"], None, end)
        ends = _quarter_ends(end, int(p["quarters"]))
        lv = [level_on(pts, e) for e in ends]
        if any(x is None for x in lv):
            return {"met": None, "missing": f"{p['series']}: not stored across "
                                            f"{p['quarters']} quarter(s)"}
        chg = [lv[i][1] - lv[i + 1][1] for i in range(len(lv) - 1)]
        neg = [c < 0 for c in chg]
        return {"met": all(neg), "strained": bool(neg and neg[0]),
                "evidence": f"{p['series']} quarterly changes "
                            + ", ".join(f"{c:+,.1f}" for c in chg)}
    if kind == "pace_below":
        pts = rows(st, p["series"], ctx["now"], None, end)
        since = (dt.date.fromisoformat(end)
                 - dt.timedelta(days=31 * int(p["months"]))).isoformat()
        got = [v for d, v in pts if d > since]
        if len(got) < int(p["months"]):
            return {"met": None, "missing": f"{p['series']}: {len(got)} of "
                                            f"{p['months']} monthly prints stored"}
        pace = sum(got[-int(p["months"]):]) * float(p.get("annualise") or 1)
        return {"met": pace < float(p["below"]), "strained": False,
                "evidence": f"{p['series']} annualised {pace:,.0f} against "
                            f"{p['below']:,}"}
    if kind == "change_below":
        m = quarter_move(st, {"key": p["series"], "label": p["series"]}, ctx)
        if not m or m.get("change") is None:
            return {"met": None, "missing": f"{p['series']}: no change over the quarter"}
        return {"met": m["change"] < float(p["below"]), "strained": False,
                "evidence": f"{p['series']} {m['change_display']} on the quarter"}
    if kind == "level_above":
        pts = rows(st, p["series"], ctx["now"], None, end)
        if not pts:
            return {"met": None, "missing": f"{p['series']}: not stored"}
        return {"met": pts[-1][1] > float(p["above"]), "strained": False,
                "evidence": f"{p['series']} {fmt_level(pts[-1][1], p['series'])} "
                            f"({pts[-1][0]}) against {p['above']}"}
    if kind == "below_year_mean":
        pts = rows(st, p["series"], ctx["now"], None, end)
        yr = [v for d, v in pts if d.startswith(str(p["year"]))]
        if not pts or len(yr) < 20:
            return {"met": None, "missing": f"{p['series']}: {p['year']} is not "
                                            f"stored ({len(yr)} observations)"}
        mean = sum(yr) / len(yr)
        return {"met": pts[-1][1] < mean, "strained": False,
                "evidence": f"{p['series']} {fmt_level(pts[-1][1], p['series'])} "
                            f"against its {p['year']} mean "
                            f"{fmt_level(mean, p['series'])}"}
    if kind == "correlation_at_most":
        ra = dict(rows(st, p["a"], ctx["now"], None, end))
        rb = dict(rows(st, p["b"], ctx["now"], None, end))
        days = sorted(set(ra) & set(rb))
        xs, ys = [], []
        for d0, d1 in zip(days, days[1:]):
            if ra[d0] and ra[d0] > 0 and ra[d1] > 0:
                xs.append(math.log(ra[d1] / ra[d0]))
                ys.append(rb[d1] - rb[d0])
        w = int(p["window"])
        if len(xs) < w:
            return {"met": None, "missing": f"{len(xs)} paired sessions of {p['a']} "
                                            f"and {p['b']}, {w} needed"}
        xs, ys = xs[-w:], ys[-w:]
        mx, my = sum(xs) / w, sum(ys) / w
        sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
        sy = math.sqrt(sum((y - my) ** 2 for y in ys))
        if not sx or not sy:
            return {"met": None, "missing": "a series did not move over the window"}
        r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)
        return {"met": r <= float(p["at_most"]),
                "strained": r <= float(p.get("strained_at_most", p["at_most"])),
                "evidence": f"{w}-session correlation {r:+.2f}"}
    return {"met": None, "missing": f"unknown rule {kind}"}


def evaluate(st, m: dict, ctx: dict) -> dict:
    """{met, strained, evidence, missing} for a measurable."""
    if "all" in m or "any" in m:
        legs = [evaluate(st, x, ctx) for x in (m.get("all") or m.get("any"))]
        ev = "; ".join(x.get("evidence") or x.get("missing") or "" for x in legs)
        known = [x for x in legs if x.get("met") is not None]
        if "all" in m:
            if any(x.get("met") is None for x in legs) and not any(
                    x.get("met") is False for x in known):
                miss = [x["missing"] for x in legs if x.get("met") is None]
                return {"met": None, "missing": "; ".join(miss), "evidence": ev}
            met = bool(known) and all(x["met"] for x in legs)
            return {"met": met, "strained": any(x.get("met") or x.get("strained")
                                                for x in known), "evidence": ev}
        if not known:
            return {"met": None, "missing": "; ".join(x["missing"] for x in legs),
                    "evidence": ev}
        return {"met": any(x["met"] for x in known),
                "strained": any(x.get("strained") for x in known), "evidence": ev}
    (kind, p), = m.items()
    return _leaf(st, kind, p, ctx)


def test_states(st, fam: dict, ctx: dict) -> dict:
    out = {}
    for t in fam.get("falsification") or []:
        if not t.get("measurable"):
            out[t["id"]] = {"state": f"not measured — {t.get('not_measured')}",
                            "evidence": "—"}
            continue
        r = evaluate(st, t["measurable"], ctx)
        if r.get("met") is None:
            out[t["id"]] = {"state": f"not measured — {r.get('missing')}",
                            "evidence": "—"}
        else:
            out[t["id"]] = {"state": ("failed" if r["met"] else
                                      "strained" if r.get("strained") else "holds"),
                            "evidence": r.get("evidence") or "—"}
    return out


def item_falsify(fam: dict, states: dict) -> dict:
    rws = []
    for t in fam.get("falsification") or []:
        s = states[t["id"]]
        rws.append([t["statement"], s["state"], s["evidence"]])
    return {"title": "7 · Falsification tests", "item": "falsify", "tier": REFERENCE,
            "table": {"columns": [f"The {fam.get('paper')} paper's test",
                                  "This quarter", "Evidence"], "rows": rws}}


# ---------------------------------------------------------------------------
# Item 9: emerging stories, and what changed in the world
# ---------------------------------------------------------------------------
def item_stories(fam: dict, ctx: dict) -> dict:
    vrows = voices_rows(ctx, fam.get("voices_subjects") or [])
    common = ctx["common"]
    line = (f"Structural change this quarter — {common.get('structural_default')} "
            f"({common.get('structural_waits')}).")
    out = {"title": "9 · Emerging stories, and what changed in the world",
           "item": "stories", "tier": REFERENCE, "lines": [line],
           "not_tracked": [f"the quarterly scan's stories for the family: {AQ7}"]}
    if vrows:
        out["table"] = {"columns": ["Published", "Voice", "Direction", "View", "Source"],
                        "rows": [[str(r.get("published_at"))[:10], r["voice"],
                                  ", ".join(d.get("direction") or "—"
                                            for d in r["family_directions"]),
                                  r.get("title") or r.get("view") or "—",
                                  r.get("source_url") or "—"] for r in vrows[-12:]]}
    else:
        out["lines"].append("No stored voice on this family this quarter.")
    return out


# ---------------------------------------------------------------------------
# Item 10: the book
# ---------------------------------------------------------------------------
def item_book(ch: dict, ctx: dict) -> dict:
    out = {"title": "10 · The book", "item": "book", "tier": REFERENCE}
    tr = module("thesis")
    if tr is None:
        out["not_tracked"] = [f"the draft slate: {not_yet('thesis')}"]
        return out
    q = ctx["next_quarter"]
    try:
        p = Path(ctx.get("db_path") or "")
        if not p.exists():
            raise FileNotFoundError(str(p))
        conn = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
        try:
            got = conn.execute(
                "SELECT horizon_kind, kind, decision_id, reason, portfolio_role FROM "
                "alt_asset_books WHERE family = ? AND quarter = ? ORDER BY "
                "horizon_kind", (ch.get("thesis_family"), q)).fetchall()
        finally:
            conn.close()
    except Exception:                                           # noqa: BLE001
        got = []
    if not got:
        out["lines"] = [f"No book line for {q[-1]}Q{q[2:4]} is seeded for this "
                        f"chapter yet."]
        return out
    out["table"] = {"columns": ["Horizon", "Line", "Portfolio role", "Decision or reason"],
                    "rows": [[h, "draft" if k == "draft" else "no draft",
                              role or "—", (did or "")[:8] if k == "draft" else (why or "—")]
                             for h, k, did, why, role in got]}
    return out


# ---------------------------------------------------------------------------
# Item 11: the ten questions -- one audited line each
# ---------------------------------------------------------------------------
def question_secs(st, ch: dict, fam: dict, ctx: dict, system_for) -> tuple[dict, list]:
    """(the item's sub-section with each question's placeholder, the writer calls
    to make). A question whose series nothing stores is answered by code: "not
    answered -- no stored source"; the rest get one audited call each, its frame
    offering at most the item's figure budget."""
    cap = int((fam.get("figure_budget") or {}).get("questions", 2))
    lines, secs = [], []
    for q in fam.get("ten_questions") or []:
        moves = []
        for k in q.get("series") or []:
            m = quarter_move(st, {"key": k, "label": derived.registry_entry(k).get(
                "description") or k}, ctx)
            if m:
                moves.append(m)
        if not moves:
            lines.append(f"{q['n']}. {q['text']} Not answered: no stored source.")
            continue
        cite, names = budget_moves(moves, cap)
        if not cite:
            cite = [{"series": m["label"], "level": m["level_text"],
                     "as_of": m["as_of"]} for m in moves[:cap]]
        key = f"q11:{ch['id']}:{q['n']}"
        lines.append({"key": key, "n": q["n"], "text": q["text"]})
        secs.append({"key": key, "title": f"{ch['title']}: question {q['n']}",
                     "kind": "stack", "sid": ch["id"],
                     "system": system_for({**q, "end": ctx["end"],
                                           "chapter": ch["title"]}, fam),
                     "max_chars": 600,
                     "slice": {"question": q["text"], "figures_you_may_cite": cite,
                               "also_relevant": names, "quarter_end": ctx["end"]}})
    sub = {"title": "11 · The ten questions", "item": "questions", "tier": REFERENCE,
           "lines": lines}
    return sub, secs


def apply_questions(sub: dict, written: dict) -> None:
    out = []
    for x in sub.get("lines") or []:
        if isinstance(x, str):
            out.append(x)
            continue
        r = written.get(x["key"]) or {}
        if r.get("published") and r.get("text"):
            ans = " ".join(str(r["text"]).split())
            out.append(f"{x['n']}. {x['text']} {ans}")
        else:
            out.append(f"{x['n']}. {x['text']} Answer withheld by the audit.")
    sub["lines"] = out
