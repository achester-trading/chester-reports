"""
Disruptive Themes, Stage 1: the instrument panels, as a slow layer of the
Alternative Assets Quarterly (6i-5; A77, 26 Oct 2026).

The architecture's Part 28.3: "Stage 1 instrument panels auto-refresh from the
store, gaps render as GAP cells, never pretended." The brief's decision 4 (ruled
25 Oct 2026) puts them in the Alternative Assets Quarterly from its 9 Jan 2027
edition, as a slow layer after the eleven family chapters; they join through
config/stack_hooks/quarterly-slow-themes-panels.yaml, so the Monthly and the
Weekly never print them.

config/themes_panels.yaml declares the panels and their rows. A row reads one
stored key (with its instrument where the key is per-instrument) as of the
edition's cutoff, or is a GAP with its reason: never a blank, never a proxy. The
inputs the change orders carried "into the next Disruptive Themes refresh brief"
enter here as rows, UNSCORED: no factor score, no composite, no delta.

Stages 2 to 4 are 6i-6 (decisions 7 and 8): nothing here calls a model, writes a
draft or touches the standing text. Report-only: nothing enters a composite, the
market-state object, a dial, a band or a packet.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import yaml

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "themes_panels.yaml"
GAP = "GAP"
COLUMNS = ["Input", "Latest (as of)", "Change on the quarter", "The order that queued it"]

log = logging.getLogger("daily_cascade.themes_block")


def config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8"))


def _row(st, spec: dict, ctx: dict) -> tuple[list[str], bool]:
    """One panel row and whether it is a GAP. A key the store holds nothing for
    by the cutoff is a GAP that says so; a declared gap prints its reason."""
    from monthly_macro import quarterly_items as qi              # noqa: PLC0415
    src = spec.get("queued") or "—"
    if spec.get("gap"):
        return [spec["label"], f"{GAP} — {spec['gap']}", "—", src], True
    m = qi.quarter_move(st, {"key": spec["key"], "label": spec["label"],
                             "instrument": spec.get("instrument"), "dp": spec.get("dp")}, ctx)
    if m is None:
        inst = f" [{spec['instrument']}]" if spec.get("instrument") else ""
        return [spec["label"], f"{GAP} — {spec['key']}{inst}: nothing stored by "
                                f"{ctx['end']}", "—", src], True
    return [spec["label"], f"{m['level_text']} ({m['as_of']})",
            m.get("change_display") or "—", src], False


def panels(st, now: str, end: str, cfg: Optional[dict] = None) -> list[dict]:
    """The panels as sub-sections, every row a value or a GAP cell."""
    cfg = cfg or config()
    start = _quarter_start(end)
    ctx = {"now": now, "start": start, "end": end}
    out = []
    for p in cfg["panels"]:
        rows, gaps = [], 0
        for spec in p["rows"]:
            r, g = _row(st, spec, ctx)
            rows.append(r)
            gaps += g
        out.append({"title": p["title"], "item": f"themes_{p['id']}", "tier": "reference",
                    "table": {"columns": list(COLUMNS), "rows": rows},
                    "lines": list(p.get("lines") or [])
                    + [f"{len(rows) - gaps} of {len(rows)} inputs read from the store; "
                       f"{gaps} GAP."],
                    "not_tracked": [], "paragraph_wanted": False,
                    "data": {"panel": p["id"], "rows": len(rows), "gaps": gaps}})
    return out


def _quarter_start(end: str) -> str:
    """The day before the quarter that `end` closes began: the change's base."""
    import datetime as dt                                       # noqa: PLC0415
    d = dt.date.fromisoformat(str(end)[:10])
    first = d.replace(month=3 * ((d.month - 1) // 3) + 1, day=1)
    return (first - dt.timedelta(days=1)).isoformat()


def quarterly_section(st, now: str, end: str) -> Optional[dict]:
    """The Quarterly's slow layer: one reference-tier section, never a chapter
    (a chapter is summarised by a model; this layer calls none)."""
    try:
        cfg = config()
        subs = panels(st, now, end, cfg)
    except Exception:                                           # noqa: BLE001
        log.warning("the Themes panels faulted", exc_info=True)
        return None
    gaps = sum(s["data"]["gaps"] for s in subs)
    n = sum(s["data"]["rows"] for s in subs)
    return {"id": "themes_panels", "title": cfg["title"], "subtitle": cfg.get("subtitle"),
            "tier": "reference", "depth": "medium", "depth_reason": None,
            "items": [], "table": None, "charts": [], "legend": None,
            "lines": list(cfg.get("lines") or []), "not_tracked": [],
            "print_items": False, "subsections": subs, "collapsed": False,
            "claim": None, "paragraphs": [], "trimmed": False, "period": "quarter",
            "phase_a": [], "notes": [], "prose_wanted": False, "empty": False,
            "data": {"stage": 1, "rows": n, "gaps": gaps, "scored": False}}
