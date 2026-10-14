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
    reference  0 (the frame) and 2a (the scenario sets to rewrite); 3 (why: the
               QTD/YTD table and the driver attribution); 3a; 4 (and oil's second
               half, currency's pair universe); 5; 6; 7; 8; 9; 10; 11 -- only the
               items the chapter's weight carries -- and the chapter's own panels
               (AQ-2 part 2: China's quote-only political sub-section, crypto's
               coin pages, Thailand's calendar, GTM-19's decomposition, ...)

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


def fmt_level(v: float, key: str, dp: Optional[int] = None) -> str:
    """A level as its table prints it; `dp` fixes the decimals (a currency
    pair's four)."""
    if dp is not None:
        return f"{v:,.{dp}f}"
    u = units(key)
    if u in ("%", "percent", "bps", "bp"):
        return f"{v:,.2f}%" if u in ("%", "percent") else f"{v:,.0f} bp"
    if u in ("count", "N"):
        return f"{v:,.0f}"
    if u == "usd" and abs(v) >= 1e6:
        # Reserves, holdings and market caps in dollars: $3.25tn, never
        # 3,248,000,000,000.0.
        for div, sfx in ((1e12, "tn"), (1e9, "bn"), (1e6, "mn")):
            if abs(v) >= div:
                return f"{'−' if v < 0 else ''}${abs(v) / div:,.2f}{sfx}"
    if abs(v) >= 1000:
        return f"{v:,.1f}"
    if 0 < abs(v) < 0.01:
        return f"{v:.4g}"
    return f"{v:,.2f}"


def _signed(v: float, mag: str, unit: str) -> str:
    """A signed figure, unsigned when it rounds to zero ("0.0%", never "−0.0%")."""
    if float(mag.replace(",", "")) == 0:
        return f"{mag}{unit}"
    return f"{'+' if v > 0 else '−'}{mag}{unit}"


def change_text(a: float, b: float, key: str) -> tuple[Optional[float], str]:
    """The change from b to a in the series' delta unit, printed signed."""
    from altdata import numeral_audit as na  # noqa: PLC0415
    du = derived.delta_unit_for(key)[0]
    u = units(key)
    if du == "bps":
        bp = (a - b) * (1.0 if u in ("bps", "bp") else 100.0)
        return bp, _signed(bp, f"{abs(bp):,.0f}", " bp")
    if du == "percent" and b:
        p = 100.0 * (a / b - 1.0)
        return p, _signed(p, f"{abs(p):,.1f}", "%")
    d = a - b
    disp = na.change_display(d, u)
    return d, disp or f"{'+' if d > 0 else '−' if d < 0 else ''}{abs(d):,.2f}"


def ordinal(x: float) -> str:
    n = int(math.floor(x + 0.5))
    sfx = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{sfx}"


# A row computed from two stored series (AQ-2 part 2), each leg a registry key:
#   diff:      a - b, in a's unit (a spread of two yields prints in percent and
#              moves in basis points: BB-CCC, the mortgage spread)
#   share:     100 x a / b (China's gold share of its reserves)
#   ratio_pct: 100 x (a / b - 1) (the CNY fixing gap against the +/-2% band)
# b is read as of each of a's days (its latest observation within 40 days), so a
# monthly leg pairs with a daily one.
DERIVED_KINDS = ("diff", "share", "ratio_pct")


def derived_kind(spec: dict) -> Optional[str]:
    return next((k for k in DERIVED_KINDS if spec.get(k)), None)


def spec_keys(spec: dict) -> list[str]:
    """Every registry key a row spec reads."""
    out = [spec["key"]] if spec.get("key") else []
    for k in DERIVED_KINDS:
        out += list(spec.get(k) or [])
    for k in ("rel_return", "corr"):
        if spec.get(k):
            out += [spec[k]["a"], spec[k]["b"]]
    return out


def spec_points(st, spec: dict, ctx: dict) -> list[tuple[str, float]]:
    kind = derived_kind(spec)
    if kind is None:
        return rows(st, spec["key"], ctx["now"], spec.get("instrument"), ctx["end"])
    a_key, b_key = spec[kind]
    pa = rows(st, a_key, ctx["now"], None, ctx["end"])
    pb = rows(st, b_key, ctx["now"], None, ctx["end"])
    out, j, last = [], 0, None
    for d, va in pa:
        while j < len(pb) and pb[j][0] <= d:
            last = pb[j]
            j += 1
        if last is None or (dt.date.fromisoformat(d)
                            - dt.date.fromisoformat(last[0])).days > 40:
            continue
        vb = last[1]
        if kind == "diff":
            out.append((d, va - vb))
        elif vb:
            out.append((d, 100.0 * va / vb if kind == "share"
                        else 100.0 * (va / vb - 1.0)))
    return out


def quarter_move(st, spec: dict, ctx: dict) -> Optional[dict]:
    kind = derived_kind(spec)
    key = spec.get("key") or (spec[kind][0] if kind else None)
    dp = spec.get("dp")
    pts = spec_points(st, spec, ctx)
    a, b = level_on(pts, ctx["end"]), level_on(pts, ctx["start"])
    if not a:
        return None
    pct_kind = kind in ("share", "ratio_pct")
    out = {"key": key, "label": spec.get("label") or key, "level": a[1],
           "as_of": a[0], "n": len(pts), "values": [v for _, v in pts],
           "level_text": (f"{a[1]:+.2f}%" if kind == "ratio_pct" else
                          f"{a[1]:.2f}%" if kind == "share" else
                          fmt_level(a[1], key, dp))}
    if b and b[0] != a[0]:
        if pct_kind:
            d = a[1] - b[1]
            out["change"] = d
            out["change_display"] = _signed(d, f"{abs(d):.2f}", " pp")
        else:
            out["change"], out["change_display"] = change_text(a[1], b[1], key)
            if dp is not None and derived.delta_unit_for(key)[0] not in (
                    "bps", "percent"):
                # A raw change at the row's own decimals (ZEC/BTC's 0.000012).
                d = a[1] - b[1]
                out["change_display"] = _signed(d, f"{abs(d):.{dp}f}", "")
        out["from"] = b[0]
    return out


def _month_closes(pts: list[tuple[str, float]]) -> list[tuple[str, float]]:
    last: dict[str, tuple[str, float]] = {}
    for d, v in pts:
        last[d[:7]] = (d, v)
    return [last[m] for m in sorted(last)]


def computed_value(st, spec: dict, ctx: dict) -> tuple[Optional[str], Optional[str], str]:
    """(value text, as of, why-not) for a one-figure computed row:
      rel_return {a, b, years}: a's annualised price return minus b's, in
                 percentage points a year, over `years` or the common span stored
      corr {a, b, months, bands?}: the correlation of monthly log returns over
                 `months`, with the paper's band named where `bands` is given."""
    if spec.get("rel_return"):
        p = spec["rel_return"]
        pa = rows(st, p["a"], ctx["now"], None, ctx["end"])
        pb = rows(st, p["b"], ctx["now"], None, ctx["end"])
        if not pa or not pb:
            return None, None, "a leg is not stored"
        end = min(pa[-1][0], pb[-1][0])
        want = (dt.date.fromisoformat(end)
                - dt.timedelta(days=int(365.25 * float(p["years"])))).isoformat()
        start = max(want, pa[0][0], pb[0][0])
        a0, a1 = level_on(pa, start) or pa[0], level_on(pa, end)
        b0, b1 = level_on(pb, start) or pb[0], level_on(pb, end)
        yrs = (dt.date.fromisoformat(end) - dt.date.fromisoformat(start)).days / 365.25
        if yrs < 1 or not (a0 and a1 and b0 and b1) or not a0[1] or not b0[1]:
            return None, None, f"under a year stored in common ({yrs:.1f})"
        ann = lambda x0, x1: (x1 / x0) ** (1.0 / yrs) - 1.0      # noqa: E731
        gap = 100.0 * (ann(a0[1], a1[1]) - ann(b0[1], b1[1]))
        span = (f"{p['years']} years" if start == want else
                f"{yrs:.1f} years stored of {p['years']} (from {start})")
        return f"{gap:+.1f} pp a year, price only, over {span}", end, ""
    if spec.get("corr"):
        p = spec["corr"]
        ma = dict(_month_closes(rows(st, p["a"], ctx["now"], None, ctx["end"])))
        mb = dict(_month_closes(rows(st, p["b"], ctx["now"], None, ctx["end"])))
        ka = {d[:7]: v for d, v in ma.items()}
        kb = {d[:7]: v for d, v in mb.items()}
        months = sorted(set(ka) & set(kb))
        xs, ys = [], []
        for m0, m1 in zip(months, months[1:]):
            if ka[m0] > 0 and ka[m1] > 0 and kb[m0] > 0 and kb[m1] > 0:
                xs.append(math.log(ka[m1] / ka[m0]))
                ys.append(math.log(kb[m1] / kb[m0]))
        want = int(p["months"])
        if len(xs) < 12:
            return None, None, f"{len(xs)} monthly returns stored in common, 12 needed"
        n = min(want, len(xs))
        xs, ys = xs[-n:], ys[-n:]
        mx, my = sum(xs) / n, sum(ys) / n
        sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
        sy = math.sqrt(sum((y - my) ** 2 for y in ys))
        if not sx or not sy:
            return None, None, "a series did not move over the window"
        r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)
        band = ""
        for b in p.get("bands") or []:
            if b["low"] <= r < b["high"]:
                band = f"; the paper's \"{b['name']}\" band ({b['low']}–{b['high']})"
        if p.get("bands") and not band:
            band = "; outside the paper's bands"
        span = f"{n} months" + ("" if n == want else f" stored of {want}")
        return f"{r:+.2f} over {span}{band}", months[-1], ""
    return None, None, "no rule"


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
    tracked = [s for s in specs if s.get("key") or derived_kind(s)]
    absent = [s for s in fam.get("structure") or [] if s.get("absent")]
    worst = None
    for s in tracked:
        pts = spec_points(st, s, ctx)
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
def resolve_hook(spec: dict) -> tuple[Optional[dict], Optional[str]]:
    """A row naming a key another branch registers (`hook_key` + `branch`): the
    row read as that key once the registry on this build holds it; until then
    None and "not yet: <branch>". Any other row passes through."""
    if not spec.get("hook_key"):
        return spec, None
    if not derived.registry_entry(spec["hook_key"]):
        return None, f"not yet: {spec['branch']}"
    return {**spec, "key": spec["hook_key"]}, None


def five_lines(st, fam: dict, ctx: dict) -> tuple[list[str], list[dict], list[str]]:
    lines, moves, nt = [], [], []
    for raw in (fam.get("five_lines") or [])[:5]:
        spec, why = resolve_hook(raw)
        if spec is None:
            nt.append(f"{raw['label']}: {why}")
            continue
        if spec.get("absent"):
            nt.append(f"{spec['label']}: {spec['absent']}")
            continue
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
    resolved = [resolve_hook(s) for s in spec["series"]]
    gone = [f"{s['label']} ({s['absent']})" for s in spec["series"] if s.get("absent")]
    gone += [f"{s['label']} ({why})" for s, (r, why) in zip(spec["series"], resolved)
             if r is None]
    spec = {**spec, "series": [r for r, _ in resolved if r is not None]}
    if gone:
        return {"id": cid, "unavailable": f"{spec['title']}: not tracked — "
                                          + "; ".join(gone)}
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
    if not fam.get("horizon_family"):
        return {"id": cid, "unavailable": "the family's long frame: "
                                          + (fam.get("horizon_absent")
                                             or "no family in the horizon set")}
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
        cap = list((ctx.get("common") or {}).get("chains_captured") or [])
        why = ("" if sym in cap else f"; {sym} is not in the chain capture, which "
               f"logs {', '.join(cap) or 'nothing'} from AQ-8a")
        return None, (f"{sym}: no chain logged in the week to the quarter's end"
                      + (why or f" (the capture logs {', '.join(cap)} from AQ-8a)"))
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
    for raw in specs:
        # A key another branch registers (named, never imported): read once the
        # registry on this build holds it; until then "not yet: <branch>".
        s, why = resolve_hook(raw)
        if s is None:
            nt.append(f"{raw['label']}: {why}")
            continue
        if s.get("rel_return") or s.get("corr"):
            txt, asof, why = computed_value(st, s, ctx)
            if txt is None:
                nt.append(f"{s['label']}: {why}")
            else:
                rws.append([s["label"], f"{txt} ({asof})", "—", "—", five])
            continue
        if s.get("absent") or not (s.get("key") or derived_kind(s)):
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
    for raw in pr.get("deep") or []:
        p, why = resolve_hook(raw)
        if p is None or not p.get("key"):
            nt.append(f"{raw['pair']}: {why or raw.get('absent')}")
            continue
        m = quarter_move(st, {"key": p["key"], "label": p["pair"], "dp": 4}, ctx)
        if m is None:
            nt.append(f"{p['pair']}: nothing stored by the quarter's end")
            continue
        pc = derived.percentile_of(m["values"], m["level"]) if m["n"] >= 20 else None
        lo, hi = min(m["values"]), max(m["values"])
        deep.append([p["pair"], f"{m['level_text']} ({m['as_of']})",
                     m.get("change_display") or "—",
                     f"{ordinal(pc)} (n={m['n']:,})" if pc is not None else "—",
                     f"{lo:,.4g} to {hi:,.4g}"])
    scan = []
    for raw in pr.get("scan") or []:
        # The scan tier is one line a pair: the latest level and the quarter's
        # change where the key is stored, else "not tracked" and why.
        p, why = resolve_hook(raw)
        m = (quarter_move(st, {"key": p["key"], "label": p["pair"], "dp": 4}, ctx)
             if p is not None and p.get("key") else None)
        if m is None:
            scan.append([raw["pair"], "not tracked",
                         why or raw.get("absent")
                         or "nothing stored by the quarter's end"])
        else:
            scan.append([raw["pair"], f"{m['level_text']} ({m['as_of']})",
                         m.get("change_display") or "—"])
    out = {"title": "4c · The pair universe", "item": "pairs", "tier": REFERENCE,
           "not_tracked": nt,
           "lines": ["The deep basket, a pair each; the scan tier from FRED's H.10 "
                     "set. Priority is refreshed each quarter."]}
    if deep:
        out["table"] = {"columns": ["Pair (deep basket)", "Latest (as of)",
                                    "Change on the quarter",
                                    "Percentile, full history",
                                    "Stored envelope"], "rows": deep}
    out["tables"] = [{"columns": ["Pair (scan tier)", "Latest (as of), or not tracked",
                                    "Change on the quarter, or why"], "rows": scan}]
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
    for r in w.get("rules") or []:
        out += " " + r
    return out


# ---------------------------------------------------------------------------
# Item 6: the analyses
# ---------------------------------------------------------------------------
def branch_module(spec: dict):
    """A module another branch builds, named by its branch: the module, or None
    while that branch is not merged under this build."""
    try:
        return importlib.import_module(spec["module"])
    except ImportError:
        return None


def analysis_state(st, a: dict, ctx: dict) -> str:
    if a.get("waits"):
        return f"not yet — {a['waits']}"
    if a.get("rel_return") or a.get("corr"):
        txt, asof, why = computed_value(st, a, ctx)
        return f"{txt} ({asof})" if txt else f"not computed — {why}"
    if a.get("branch"):
        m = branch_module(a)
        if m is None or not hasattr(m, a.get("reader") or ""):
            return f"not yet: {a['branch']}"
        try:
            if a["reader"] == "breaks_between":
                assets = set(ctx.get("correlation_assets") or [])
                got = [b for b in m.breaks_between(st, ctx["start"], ctx["now"])
                       if b["asset"] in assets]
                esc = m.credit_escalation(got) if hasattr(m, "credit_escalation") else []
                if not got:
                    return "no break fired this quarter"
                return ("; ".join(f"{b['asset']} against {b['benchmark']} "
                                  f"{b['direction']} ({b['delta']:+.2f}, {b['day']})"
                                  for b in got)
                        + (f"; credit-sensitive escalation: {', '.join(esc)}"
                           if esc else ""))
            out = getattr(m, a["reader"])(st, ctx["now"])
            return "; ".join(str(x) for x in (out.get("lines") or [])) or "computed"
        except Exception as exc:                                # noqa: BLE001
            return f"FAULT (code, not data) -- {type(exc).__name__}"
    if derived_kind(a):
        m = quarter_move(st, {**a, "label": a["title"]}, ctx)
        if m is None:
            return "nothing stored at this cutoff"
        return (f"{m['level_text']} ({m['as_of']})"
                + (f", {m['change_display']} on the quarter"
                   if m.get("change_display") else ""))
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
                # A key the hook's module owns is named through it (AQ-8a's
                # YUDD_KEYS), so this config names no key the registry on this
                # branch does not hold (validate_config_refs).
                key = a.get("key") or (getattr(m, "YUDD_KEYS", None) or {}).get(
                    a.get("module_key"))
                if not key:
                    return f"not yet — {a['module']} names no {a.get('module_key')}"
                t = m.triple(st, key, ctx["now"])
                return (f"{t['latest']:+.2f} ({t['as_of']})" if t else
                        f"no {key} row stored at this cutoff")
        except Exception as exc:                                # noqa: BLE001
            return f"FAULT (code, not data) -- {type(exc).__name__}"
    vals = []
    for k in a.get("series") or []:
        pts = rows(st, k, ctx["now"], None, ctx["end"])
        if pts:
            vals.append(f"{fmt_level(pts[-1][1], k)} ({pts[-1][0]})")
    return "; ".join(vals) if vals else "nothing stored at this cutoff"


# THE KILL STATE (AQ-10): every analysis prints one of these beside its
# reading. "not measured" always carries its reason.
KILL_STATES = ("holds", "strained", "killed")
KILL_NONE_RULED = "not measured — no kill condition was ruled (section 5: —)"
ANALYSIS_COLUMNS = ["Analysis", "State", "Kill condition (as ruled)", "Kill state"]


def none_ruled(kill: Optional[str]) -> bool:
    return str(kill or "").strip().lower().startswith("none ruled")


def kill_vocab(text: str) -> str:
    """A module's own kill-state wording, in the gate's four words. AQ-8a's
    readers say "stable", "no stable sign (kill condition met; not acted on)",
    "kill test waits: n of 12 months", "no kill condition ruled ..."."""
    t = " ".join(str(text or "").split())
    low = t.lower()
    if low.split(" — ")[0] in KILL_STATES:
        return t
    if "kill condition met" in low:
        return f"killed — {t}"
    if low == "stable" or low.startswith("stable "):
        return f"holds — {t}"
    return f"not measured — {t}" if t else "not measured — the reader returned nothing"


def kill_state(st, a: dict, ctx: dict) -> str:
    """holds / strained / killed / not measured — <reason>, for one analysis.
    Computed, never declared: from `kill_measurable` (met = killed, the item 7
    rule), from `kill_reader` on the analysis's own module, or not measured
    with the reason. An analysis whose config carries no kill condition at all
    prints so -- and fails AQ-10's gate."""
    kill = str(a.get("kill") or "").strip()
    if not kill:
        return "not measured — no kill condition in config"
    if none_ruled(kill):
        return KILL_NONE_RULED
    if a.get("kill_measurable"):
        r = evaluate(st, a["kill_measurable"], ctx)
        if r.get("met") is None:
            return f"not measured — {r.get('missing') or 'no reading'}"
        return ("killed" if r["met"] else "strained" if r.get("strained")
                else "holds") + (f" — {r['evidence']}" if r.get("evidence") else "")
    if a.get("kill_reader"):
        kind = {"altdata.attribution": "attribution", "altdata.paper_bid": "paper_bid",
                "altdata.correlation": "correlation"}.get(a.get("module") or "")
        m = module(kind) if kind else branch_module(a) if a.get("module") else None
        if m is None or not hasattr(m, a["kill_reader"]):
            return (f"not measured — {not_yet(kind)}" if kind else
                    f"not measured — not yet: {a.get('branch') or a.get('module')}")
        try:
            fn = getattr(m, a["kill_reader"])
            args = list(a.get("kill_args") or [])
            got = fn(st, *args, ctx["now"]) if args else fn()
        except Exception as exc:                                # noqa: BLE001
            return f"not measured — FAULT (code, not data) -- {type(exc).__name__}"
        return kill_vocab(got)
    if a.get("waits"):
        return f"not measured — the analysis waits: {a['waits']}"
    return "not measured — the kill condition has no measurable in config yet"


def item_analyses(st, fam: dict, ctx: dict) -> dict:
    rws = [[a["title"], analysis_state(st, a, ctx), a.get("kill") or "—",
            kill_state(st, a, ctx)]
           for a in fam.get("analyses") or []]
    out = {"title": "6 · The analyses", "item": "analyses", "tier": REFERENCE}
    if rws:
        out["table"] = {"columns": list(ANALYSIS_COLUMNS), "rows": rws}
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
    if kind in ("correlation_at_most", "correlation_in_band"):
        r, miss = _daily_corr(st, p, ctx)
        if r is None:
            return {"met": None, "missing": miss}
        w = int(p["window"])
        if kind == "correlation_in_band":
            # One quarter in the band is strained; failing needs the paper's
            # longer span, which code does not declare.
            inside = float(p["low"]) <= r <= float(p["high"])
            return {"met": False, "strained": inside,
                    "evidence": f"{w}-session correlation {r:+.2f} against the "
                                f"{p['low']}–{p['high']} band"}
        return {"met": r <= float(p["at_most"]),
                "strained": r <= float(p.get("strained_at_most", p["at_most"])),
                "evidence": f"{w}-session correlation {r:+.2f}"}
    if kind == "change_above":
        m = quarter_move(st, {"key": p["series"], "label": p["series"]}, ctx)
        if not m or m.get("change") is None:
            return {"met": None, "missing": f"{p['series']}: no change over the quarter"}
        tag = f" ({p['label']})" if p.get("label") else ""
        return {"met": m["change"] > float(p["above"]), "strained": False,
                "evidence": f"{p['series']}{tag} {m['change_display']} on the "
                            f"quarter against {p['above']:+,}"}
    if kind == "not_tightened":
        # SLOOS: the net percentage of banks tightening, quarterly. The leg is met
        # (no tightening) when no print in the last `quarters` is above zero. The
        # series is another branch's key: until it is registered, "not yet".
        key = p["hook_series"]
        if not derived.registry_entry(key):
            return {"met": None, "missing": f"{key}: not yet: {p['branch']}"}
        since = (dt.date.fromisoformat(end)
                 - dt.timedelta(days=92 * int(p["quarters"]))).isoformat()
        got = [(d, v) for d, v in rows(st, key, ctx["now"], None, end) if d > since]
        if len(got) < int(p["quarters"]):
            return {"met": None, "missing": f"{key}: {len(got)} of {p['quarters']} "
                                            f"quarterly prints stored"}
        got = got[-int(p["quarters"]):]
        return {"met": all(v <= 0 for _, v in got), "strained": False,
                "evidence": f"{key} net tightening "
                            + ", ".join(f"{v:+.1f} ({d[:7]})" for d, v in got)}
    if kind == "drawdown_at_least":
        pts = rows(st, p["series"], ctx["now"], None, end)
        if p.get("lookback_days"):
            since = (dt.date.fromisoformat(end)
                     - dt.timedelta(days=int(p["lookback_days"]))).isoformat()
            pts = [x for x in pts if x[0] >= since]
        if len(pts) < 20:
            return {"met": None, "missing": f"{p['series']}: {len(pts)} observations"}
        peak = max(pts, key=lambda x: x[1])
        dd = 100.0 * (1.0 - pts[-1][1] / peak[1]) if peak[1] else 0.0
        return {"met": dd >= float(p["at_least"]),
                "strained": dd >= float(p.get("strained_at_least", p["at_least"])),
                "evidence": f"{p['series']} {dd:.1f}% below its peak of {peak[0]} "
                            f"at {pts[-1][0]}, against {p['at_least']}%"}
    if kind == "unmeasured":
        return {"met": None, "missing": p["reason"]}
    return {"met": None, "missing": f"unknown rule {kind}"}


def _daily_corr(st, p: dict, ctx: dict) -> tuple[Optional[float], str]:
    """The correlation of a's daily log returns against b's daily changes (b's
    log returns where `b_change: log`) over the last `window` paired sessions."""
    ra = dict(rows(st, p["a"], ctx["now"], None, ctx["end"]))
    rb = dict(rows(st, p["b"], ctx["now"], None, ctx["end"]))
    days = sorted(set(ra) & set(rb))
    xs, ys = [], []
    log_b = p.get("b_change") == "log"
    for d0, d1 in zip(days, days[1:]):
        if ra[d0] and ra[d0] > 0 and ra[d1] > 0:
            if log_b:
                if not (rb[d0] and rb[d0] > 0 and rb[d1] > 0):
                    continue
                ys.append(math.log(rb[d1] / rb[d0]))
            else:
                ys.append(rb[d1] - rb[d0])
            xs.append(math.log(ra[d1] / ra[d0]))
    w = int(p["window"])
    if len(xs) < w:
        return None, f"{len(xs)} paired sessions of {p['a']} and {p['b']}, {w} needed"
    xs, ys = xs[-w:], ys[-w:]
    mx, my = sum(xs) / w, sum(ys) / w
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if not sx or not sy:
        return None, "a series did not move over the window"
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy), ""


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


NO_PAPER = "no owning paper — not stated"


def item_falsify(fam: dict, states: dict) -> dict:
    out = {"title": "7 · Falsification tests", "item": "falsify", "tier": REFERENCE,
           "lines": []}
    rws = []
    for t in fam.get("falsification") or []:
        s = states[t["id"]]
        rws.append([t["statement"], s["state"], s["evidence"]])
    if rws:
        out["table"] = {"columns": [f"The {fam.get('paper')} paper's test",
                                    "This quarter", "Evidence"], "rows": rws}
    else:
        # A chapter no paper owns states no tests: none is invented here.
        out["lines"].append(f"Falsification tests: {fam.get('falsification_note') or NO_PAPER}.")
    rel = fam.get("related_tests") or []
    if rel:
        out["lines"].append("Read beside them, from a paper that does not own this "
                            "chapter (its own words; not graded here):")
        out["lines"] += [f"{t['paper']}, {t['section']}: {t['statement']}" for t in rel]
    return out


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
        # The scan's stories are stored (AQ-7): the not-yet line is for a
        # quarter with none.
        out["not_tracked"] = []
    else:
        out["lines"].append("No stored voice on this family this quarter.")
    return out


# ---------------------------------------------------------------------------
# Item 10: the book
# ---------------------------------------------------------------------------
def item_book(ch: dict, ctx: dict, fam: Optional[dict] = None) -> dict:
    out = {"title": "10 · The book", "item": "book", "tier": REFERENCE}
    rule = (fam or {}).get("book_rule") or {}
    if rule.get("no_draft"):
        # An isolated chapter writes no draft at all: it feeds nothing.
        out["lines"] = [f"No draft, by rule: {rule['no_draft']}"]
        return out
    if rule.get("line"):
        out["lines"] = [f"By rule: {rule['line']}"]
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
                "SELECT horizon_kind, kind, decision_id, reason, portfolio_role, "
                "cost_json FROM alt_asset_books WHERE family = ? AND quarter = ? "
                "ORDER BY horizon_kind, written_at",
                (ch.get("thesis_family"), q)).fetchall()
        finally:
            conn.close()
    except Exception:                                           # noqa: BLE001
        got = []
    if not got:
        out["lines"] = out.get("lines", []) + [f"No book line for {q[-1]}Q{q[2:4]} is seeded for this "
                        f"chapter yet."]
        return out
    out["table"] = {"columns": list(BOOK_COLUMNS),
                    "rows": book_rows(got, rule, ch.get("weight"))}
    return out


BOOK_COLUMNS = ["Horizon", "Line", "Portfolio role", "Cost row", "Decision or reason"]
HORIZONS = ("3m", "12m")
COST_GAP_NAMES = (("spread", "spread"), ("roll", "roll"), ("borrow", "borrow"),
                  ("fx_hedge", "FX hedge"))


def cost_text(cost: Optional[dict]) -> str:
    """A draft's cost row in one cell, from the IBKR costs writer's rate card
    (AQ-6's cost_row): the commission where it is priced, its reason where it
    is not, and the components the writer does not price, named."""
    if not cost:
        return ""
    gaps = [lab for k, lab in COST_GAP_NAMES if k in cost]
    tail = f"; {', '.join(gaps)} not priced" if gaps else ""
    if cost.get("available") and cost.get("commission") is not None:
        return (f"commission ${float(cost['commission']):,.2f} (rate card"
                f"{', a floor' if cost.get('is_floor_not_all_in') else ''}){tail}")
    return f"commission not priced: {cost.get('reason') or 'no reason given'}{tail}"


def book_rows(got: list, rule: dict, weight: Optional[str]) -> list[list[str]]:
    """The book table: one row per stored book line, plus a no-draft line for a
    horizon with none. A draft on an instrument the chapter's rule does not
    name as understood (agriculture, section 4.11) prints as a no draft."""
    import json as _json  # noqa: PLC0415
    understood = rule.get("understood_instruments")
    out, seen = [], set()
    for h, k, did, why, role, cj in got:
        seen.add(h)
        try:
            cost = _json.loads(cj) if cj else None
        except ValueError:
            cost = None
        inst = str((cost or {}).get("instrument") or "")
        if k == "draft" and understood is not None and inst not in understood:
            out.append([h, "no draft", "—", "—",
                        f"thin or poorly understood contract, a no draft by rule "
                        f"(section 4.11): {inst or 'unnamed instrument'}"])
            continue
        if k == "draft":
            out.append([h, "draft", role or "—", cost_text(cost),
                        f"{inst or 'unnamed instrument'} · {(did or '')[:8]}"])
        else:
            out.append([h, "no draft", "—", "—", why or "—"])
    if weight == "deep":
        for h in HORIZONS:
            if h not in seen:
                out.append([h, "no draft", "—", "—",
                            "no book line was written for this horizon"])
    return sorted(out, key=lambda r: HORIZONS.index(r[0]) if r[0] in HORIZONS else 9)


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
    if not fam.get("ten_questions"):
        lines.append(f"The ten questions: {fam.get('questions_note') or NO_PAPER}.")
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


# ---------------------------------------------------------------------------
# AQ-2 part 2: the frame, the scenario sets, and the chapter's own panels
# ---------------------------------------------------------------------------
def item_frame(fam: dict) -> Optional[dict]:
    """The chapter's frame: the owning paper's, or -- where the paper is not yet
    filed -- the change order's interim paragraph with its citations, said so."""
    fr = fam.get("frame")
    if not fr:
        return None
    lines = [fr["status"]]
    if fr.get("interim"):
        lines.append(f"The interim frame, from the change order "
                     f"{fr.get('from') or ''}: {fr['interim']}")
    if fr.get("citations"):
        lines.append("Its citations: " + "; ".join(fr["citations"]) + ".")
    iso = fam.get("isolation")
    if iso:
        lines.append(f"Isolation: namespace: {iso['namespace']}, trigger_eligible: "
                     f"{str(iso['trigger_eligible']).lower()}, feeds "
                     f"{', '.join(iso.get('feeds') or []) or 'nothing'}. "
                     f"{iso.get('note') or ''}".strip())
    return {"title": "0 · The frame", "item": "frame", "tier": REFERENCE,
            "lines": lines, "not_tracked": list(fr.get("not_tracked") or [])}


def item_scenarios(fam: dict) -> Optional[dict]:
    """The scenario sets the chapter rewrites each quarter: each row with the
    paper's prior, and this quarter's probability from the thesis register (AQ-6)
    -- never a weight typed here. A set its paper has not yet supplied says so."""
    sets = fam.get("scenarios") or []
    if not sets:
        return None
    now_col = ("in item 2, from the ledger" if module("thesis") is not None
               else not_yet("thesis"))
    rws, lines = [], []
    for s in sets:
        if s.get("pending"):
            lines.append(f"{s['name']} ({s['horizon']}): not yet — {s['pending']}.")
            continue
        for r in s["rows"]:
            rws.append([f"{s['name']} ({s['horizon']})", r["name"],
                        r.get("prior") or "—", now_col])
        lines.append(f"{s['name']}: {s['source']}.")
    out = {"title": "2a · The scenario sets to rewrite", "item": "scenarios",
           "tier": REFERENCE, "lines": lines, "not_tracked": []}
    if rws:
        out["table"] = {"columns": ["Set", "Scenario", "The paper's prior",
                                    "This quarter"], "rows": rws}
    return out


def _panel_head(p: dict) -> dict:
    return {"title": f"{p['n']} · {p['title']}", "item": p["id"],
            "tier": p.get("tier") or REFERENCE, "panel": p["kind"],
            "lines": list(p.get("lines") or []), "not_tracked": []}


def panel_series(st, p: dict, ctx: dict) -> dict:
    out = _panel_head(p)
    rws, nt, pct = structure_rows(st, p.get("rows") or [], ctx)
    out["not_tracked"] = nt
    if rws:
        out["table"] = {"columns": STRUCTURE_COLUMNS, "rows": rws}
        out["data"] = {"percentiles": pct}
    elif not out["lines"]:
        out["lines"] = ["No series of this panel is stored at this cutoff."]
    return out


def panel_matrix(p: dict) -> dict:
    """A table whose cells are named series not yet stored: printed so the
    reader sees the shape the chapter will fill, the gap with its reason."""
    out = _panel_head(p)
    cols = p["columns"]
    rws = []
    for r in p["rows"]:
        cells = r.get("cells") or {}
        rws.append([r["name"]] + [cells.get(c, "not tracked") for c in cols])
    out["table"] = {"columns": [p.get("row_head") or ""] + cols, "rows": rws}
    out["not_tracked"] = [f"every cell marked not tracked: {p['absent']}"]
    return out


def panel_hook(st, p: dict, ctx: dict) -> dict:
    """A block another branch builds, named by branch and module and imported
    only at run time: "not yet: <branch>" until that branch is merged."""
    out = _panel_head(p)
    m = branch_module(p)
    fn = getattr(m, p["reader"], None) if m is not None else None
    if fn is None:
        out["not_tracked"] = [f"{p['title']}: not yet: {p['branch']}"]
        return out
    try:
        got = fn(st, ctx["now"]) or {}
    except Exception as exc:                                    # noqa: BLE001
        out["notes"] = [f"{p['title']}: FAULT (code, not data) -- "
                        f"{type(exc).__name__}"]
        return out
    for k in ("table", "notes", "data"):
        if got.get(k):
            out[k] = got[k]
    out["lines"] += list(got.get("lines") or [])
    out["not_tracked"] += list(got.get("not_tracked") or [])
    if not (out.get("table") or out["lines"] or out.get("notes")):
        out["lines"].append("The block returned nothing at this cutoff.")
    return out


def load_calendar(path: str) -> dict:
    import yaml  # noqa: PLC0415
    with (REPO / path).open(encoding="utf-8") as fp:
        return yaml.safe_load(fp) or {}


def panel_calendar(p: dict, ctx: dict) -> dict:
    """A hand-seeded calendar (date, body, event, source): the quarter ahead's
    entries, or the template's own line while nothing is seeded."""
    out = _panel_head(p)
    cal = load_calendar(p["path"])
    end = dt.date.fromisoformat(ctx["end"])
    ahead = (end + dt.timedelta(days=int(p.get("days_ahead") or 120))).isoformat()
    got = [e for e in cal.get("entries") or []
           if ctx["end"] < str(e.get("date"))[:10] <= ahead]
    if got:
        out["table"] = {"columns": ["Date", "Body", "Event", "Source"],
                        "rows": [[str(e["date"])[:10], e["body"], e["event"],
                                  e["source"]] for e in got]}
    else:
        out["lines"].append(f"No entry seeded for the quarter ahead — the calendar "
                            f"({p['path']}) is maintained by hand.")
    return out


def quarter_voices(ctx: dict) -> list[dict]:
    """Every stored voices row published in the quarter, knowable at the cutoff."""
    try:
        from altdata import voices as vmod  # noqa: PLC0415
        with vmod.VoicesStore(ctx.get("db_path"), readonly=True) as vs:
            return vs.rows(as_of=ctx["now"], since=ctx["start"],
                           until=(dt.date.fromisoformat(ctx["end"])
                                  + dt.timedelta(days=1)).isoformat())
    except Exception:                                           # noqa: BLE001
        return []


def panel_political(p: dict, ctx: dict) -> list[dict]:
    """China's local political environment, QUOTE-ONLY (decision 4): the
    operator's note and the stored reporting are quoted, attributed and dated;
    the chapter writes no political judgment of its own, and no model is asked
    for one -- neither sub-section carries a prose frame. Two sub-sections: the
    rules, the calendar and the operator's note; then the stored reporting."""
    out = _panel_head(p)
    out["quote_only"] = True
    out["lines"] = [f"Rule: {r}" for r in p.get("rules") or []]
    cal = panel_calendar({**p, "lines": [], "path": p["calendar"]}, ctx)
    if cal.get("table"):
        out["tables"] = [cal["table"]]
    out["lines"] += cal["lines"]
    vrows = quarter_voices(ctx)
    notes = [r for r in vrows if r.get("source_id") == p["note_source_id"]]
    for r in notes:
        out["lines"].append(f"The operator's political note, "
                            f"{str(r['published_at'])[:10]}: \"{r['view']}\" — "
                            f"{r['voice']} ({r['source_url']})")
    if not notes:
        out["not_tracked"].append("the operator's political note: none stored for "
                                  "this quarter (written by hand, stored as an "
                                  "operator voices row)")
    out["not_tracked"] += list(p.get("not_tracked") or [])
    rpt = {"title": f"{p.get('reporting_n') or p['n']} · The stored reporting, quoted",
           "item": f"{p['id']}_reporting",
           "tier": out["tier"], "panel": p["kind"], "quote_only": True,
           "lines": [], "not_tracked": []}
    auth = [a.lower() for a in p.get("authoritative") or []]
    rep = [r for r in vrows if str(r.get("source_id") or "").startswith(
        p["reporting_prefix"])]
    if rep:
        rpt["table"] = {"columns": ["Published", "Outlet", "Class", "As stored",
                                    "Source"],
                        "rows": [[str(r["published_at"])[:10], r["outlet"],
                                  ("authoritative release"
                                   if any(a in str(r["outlet"]).lower() for a in auth)
                                   else "commentary"),
                                  f"\"{r['view']}\"", r["source_url"]] for r in rep]}
    else:
        rpt["not_tracked"].append(f"the stored reporting on China's politics: no "
                                  f"row this quarter ({AQ7})")
    return [out, rpt]


def panel_light_tier(p: dict) -> dict:
    out = _panel_head(p)
    out["table"] = {"columns": ["Name", "What it is read for", "State"],
                    "rows": [[c["name"], c["why"],
                              "pending MW-6 promotion"
                              if c.get("light_tier_pending_promotion") else
                              "promoted (MW-6)"] for c in p["coins"]]}
    return out


def panel_return_decomp(st, p: dict, ctx: dict) -> dict:
    """GTM-19's return decomposition, built with what the store holds: each
    proxy fund's quarter in USD split into price and dividends (on their
    ex-dates, not reinvested); the currency, multiple and earnings terms and the
    local-currency return wait for the series named."""
    out = _panel_head(p)
    rws = []
    for f in p["proxies"]:
        pts = rows(st, f["key"], ctx["now"], None, ctx["end"])
        a, b = level_on(pts, ctx["end"]), level_on(pts, ctx["start"])
        if not a or not b or not b[1] or a[0] == b[0]:
            out["not_tracked"].append(f"{f['label']}: no quarter stored")
            continue
        divs = sum(v for d, v in rows(st, f["key"] + "_dividend", ctx["now"], None,
                                      ctx["end"]) if b[0] < d <= a[0])
        pr, dv = 100.0 * (a[1] / b[1] - 1.0), 100.0 * divs / b[1]
        rws.append([f["label"], _signed(pr, f"{abs(pr):.1f}", "%"),
                    _signed(dv, f"{abs(dv):.1f}", "%"),
                    _signed(pr + dv, f"{abs(pr + dv):.1f}", "%")]
                   + ["not stored"] * 4)
    if rws:
        out["table"] = {"columns": ["Proxy (USD)", "Price", "Dividends", "Total",
                                    "Currency", "Multiple", "Earnings",
                                    "Local-currency return"], "rows": rws}
    out["not_tracked"] += list(p.get("lacks") or [])
    return out


COIN_FIELDS = (
    ("definition", "Asset definition and token rights"),
    ("supply", "Supply and holders — the effective float"),
    ("economics", "Protocol economics and value capture"),
    ("usage", "Usage and revenue, organic against subsidised"),
    ("security", "Security, governance and operations"),
    ("market", "Market structure and liquidity by venue"),
    ("derivatives", "Derivatives and flows"),
    ("regulation", "Regulation and custody by jurisdiction"),
    ("catalysts", "Catalysts"),
    ("cases", "Bull / base / bear"),
    ("falsifiers", "Measurable falsifiers"),
    ("log", "Source and vintage log"),
)


def _cases(case_key: Optional[str]) -> Optional[dict]:
    if not case_key:
        return None
    try:
        from altdata.report import cases_and_positioning as cp  # noqa: PLC0415
    except ImportError:
        return None
    return (cp.CASES_AND_POSITIONING.get(case_key) or {}).get("cases")


def _latest(st, key: str, ctx: dict) -> Optional[dict]:
    got = [r for r in st.as_of(key, ctx["now"], None)
           if r.get("value_num") is not None
           and str(r["observed_at"])[:10] <= ctx["end"]]
    return max(got, key=lambda r: str(r["observed_at"])) if got else None


def coin_page(st, coin: dict, fam: dict, ctx: dict, states: dict) -> dict:
    """One deep-tier coin in the fixed shape of section 4.6: twelve fields in
    one order for every coin. Each reads a stored series, the vendored case file
    or the chapter's tests -- or prints its not-yet reason."""
    rws, used = [], []
    tests = {t["id"]: t for t in fam.get("falsification") or []}
    for fid, label in COIN_FIELDS:
        spec = (coin.get("fields") or {}).get(fid) or {}
        if fid == "cases":
            cs = _cases(coin.get("cases_key"))
            if cs:
                txt = " | ".join(f"{name}: " + "; ".join(cs.get(k) or ["—"])
                                 for name, k in (("bull", "bull"),
                                                 ("base (range-bound)", "flat"),
                                                 ("bear", "bear")))
                txt += " (altdata/report/cases_and_positioning.py, vendored 3 Sep 2026)"
            else:
                txt = (f"not yet — {coin['name']} is not in "
                       f"altdata/report/cases_and_positioning.py")
        elif fid == "falsifiers":
            parts = [f"{tests[t]['statement']} [{states.get(t, {}).get('state', 'not measured')}]"
                     for t in spec.get("tests") or []]
            parts += list(spec.get("lines") or [])
            txt = " ".join(parts) or f"not yet — {spec.get('absent') or 'none stated'}"
        elif fid == "log":
            txt = "; ".join(used) or "no stored series on this page"
        elif spec.get("keys"):
            vals = []
            for k in spec["keys"]:
                r = _latest(st, k, ctx)
                if r is None:
                    vals.append(f"{k}: nothing stored")
                    continue
                d = str(r["observed_at"])[:10]
                vals.append(f"{k} {fmt_level(float(r['value_num']), k)} ({d})")
                used.append(f"{k} — {r.get('source') or 'source not recorded'}, "
                            f"observed {d}, available {str(r.get('available_at'))[:16]}")
            txt = "; ".join(vals)
            if spec.get("absent"):
                txt += f"; the rest not yet — {spec['absent']}"
        elif spec.get("paper"):
            txt = f"see {spec['paper']} (not restated)"
            if spec.get("absent"):
                txt += f"; not yet — {spec['absent']}"
        else:
            txt = f"not yet — {spec.get('absent') or 'no source named'}"
        rws.append([label, txt])
    return {"title": f"6a · The coin page: {coin['name']}",
            "item": f"coin_{coin['id']}", "tier": REFERENCE, "panel": "coin",
            "lines": [], "not_tracked": [],
            "table": {"columns": ["Field", coin["name"]], "rows": rws},
            "data": {"fields": [f for f, _ in COIN_FIELDS]}}


def panel_subsections(st, fam: dict, ctx: dict, states: dict) -> list[dict]:
    """The chapter's own panels (config `panels`), each placed after the
    template item it names (`after`)."""
    out = []
    for p in fam.get("panels") or []:
        k = p["kind"]
        if k == "coins":
            for c in p["coins"]:
                out.append({**coin_page(st, c, fam, ctx, states), "after": p["after"]})
            continue
        if k == "series":
            sub = panel_series(st, p, ctx)
        elif k == "matrix":
            sub = panel_matrix(p)
        elif k == "hook":
            sub = panel_hook(st, p, ctx)
        elif k == "calendar":
            sub = panel_calendar(p, ctx)
        elif k == "lines":
            sub = _panel_head(p)
        elif k == "political":
            out += [{**x, "after": p["after"]} for x in panel_political(p, ctx)]
            continue
        elif k == "light_tier":
            sub = panel_light_tier(p)
        elif k == "return_decomp":
            sub = panel_return_decomp(st, p, ctx)
        else:
            sub = {**_panel_head(p), "notes": [f"unknown panel kind {k}"]}
        sub["after"] = p["after"]
        out.append(sub)
    return out
