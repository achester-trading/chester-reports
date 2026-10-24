"""
Signal-triage Batch 15, item 75 (written as 68; ST-R6.75a): the AI-lab
financials ledger and its links -- report only.

    from altdata import ai_lab_ledger as al
    rows = al.load()                  # docs/ledgers/ai-lab-financials-ledger.md
    al.latest(rows); al.measures(row)
    al.unit_economics_line(rows); al.sr16_line(rows); al.ipo_watch_lines()
    python -m altdata.ai_lab_ledger show

THE LEDGER is a Markdown table under docs/ledgers/, one row per lab and period,
its figures entered as published with the row's source and URL (G3: the first
row is a provisional dated record; later quarterly rows wait on the operator's
yes). THE RATIOS ARE COMPUTED HERE from the entered figures, never typed:

  revenue growth             revenue / revenue a year earlier - 1
  compute share of revenue   compute and infrastructure / revenue
  burn ex non-cash charges   net loss - non-cash financing charges (a loss measure,
                             labelled; not the cash-flow statement)
  commitments / TTM revenue  forward commitments / TTM revenue, only when TTM
                             revenue is in the row
  top-two concentration      as entered

THE LINKS. Item 47's AI unit-economics line and SR-16's AI-credit absorption
entry each print the latest row's measures, or "no ledger entry". The mega-IPO
watch (config/ai_lab_ledger.yaml) prints each watched name's float, index-
inclusion timing and lock-ups as "not yet public" until a filing gives them.

Reads files only: no store, no network, no composite.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "docs" / "ledgers" / "ai-lab-financials-ledger.md"
CONFIG = REPO / "config" / "ai_lab_ledger.yaml"
NO_ENTRY = "no ledger entry"
NOT_PUBLIC = "not yet public"

COLUMNS = {
    "lab": "lab", "period": "period", "period end": "period_end",
    "reported": "reported", "status": "status",
    "revenue ($bn)": "revenue", "revenue a year earlier ($bn)": "revenue_prior",
    "compute and infrastructure ($bn)": "compute",
    "net loss ($bn)": "net_loss",
    "non-cash financing charges ($bn)": "noncash_charges",
    "forward commitments ($bn)": "commitments", "ttm revenue ($bn)": "ttm_revenue",
    "top-two customers (% of revenue)": "top_two_pct",
    "source": "source", "url": "url"}
NUMERIC = ("revenue", "revenue_prior", "compute", "net_loss", "noncash_charges",
           "commitments", "ttm_revenue", "top_two_pct")


def config(path: Optional[Path] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8")) or {}


def _num(cell: str) -> Optional[float]:
    s = str(cell or "").strip().replace(",", "")
    if not s:
        return None
    m = re.fullmatch(r"[-+]?\d+(?:\.\d+)?", s)
    return float(s) if m else None


def parse(text: str) -> list[dict]:
    """The rows of the '## Entries' table. A row without a URL is refused (no
    stored source, not printed)."""
    lines = text.splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.strip().lower() == "## entries")
    except StopIteration:
        return []
    cols: list[str] = []
    out = []
    for ln in lines[start + 1:]:
        if ln.startswith("## "):
            break
        if not ln.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if not cols:
            cols = [COLUMNS.get(c.lower(), c.lower()) for c in cells]
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        row: dict[str, Any] = dict(zip(cols, cells))
        for k in NUMERIC:
            row[k] = _num(row.get(k, ""))
        if not str(row.get("url") or "").startswith("http"):
            continue
        out.append(row)
    return out


def load(path: Optional[Path] = None) -> list[dict]:
    p = Path(path or LEDGER)
    return parse(p.read_text(encoding="utf-8")) if p.exists() else []


def latest(rows: list[dict], lab: Optional[str] = None) -> Optional[dict]:
    rs = [r for r in rows if lab is None or r.get("lab") == lab]
    return max(rs, key=lambda r: (str(r.get("period_end")), str(r.get("reported"))),
               default=None)


def _ratio(a: Optional[float], b: Optional[float]) -> Optional[float]:
    return None if a is None or not b else a / b


def measures(r: dict) -> dict:
    g = _ratio(r.get("revenue"), r.get("revenue_prior"))
    cs = _ratio(r.get("compute"), r.get("revenue"))
    burn = (None if r.get("net_loss") is None or r.get("noncash_charges") is None
            else round(r["net_loss"] - r["noncash_charges"], 4))
    ct = _ratio(r.get("commitments"), r.get("ttm_revenue"))
    return {"growth_pct": None if g is None else round((g - 1) * 100.0, 2),
            "compute_share_pct": None if cs is None else round(cs * 100.0, 2),
            "burn_ex_noncash_bn": burn,
            "commitments_over_ttm": None if ct is None else round(ct, 2),
            "top_two_pct": r.get("top_two_pct")}


def _head(r: dict) -> str:
    st = r.get("status") or "entered"
    return f"{r['lab']}, {r['period']} ({st}; reported {r.get('reported')})"


def unit_economics_line(rows: list[dict]) -> str:
    """Item 47's AI unit-economics line, from the ledger's latest row."""
    r = latest(rows)
    if not r:
        return f"AI unit economics (item 47, the AI-lab ledger): {NO_ENTRY}."
    m = measures(r)
    parts = []
    if m["growth_pct"] is not None:
        parts.append(f"revenue ${r['revenue']:,.1f}bn, {m['growth_pct']:+,.0f}% on the "
                     f"year")
    if m["compute_share_pct"] is not None:
        parts.append(f"compute and infrastructure {m['compute_share_pct']:.0f}% of "
                     f"revenue")
    if m["burn_ex_noncash_bn"] is not None:
        parts.append(f"loss excluding non-cash financing charges "
                     f"${m['burn_ex_noncash_bn']:,.1f}bn (a cash-burn measure)")
    if m["top_two_pct"] is not None:
        parts.append(f"top two customers {m['top_two_pct']:.0f}% of revenue")
    return (f"AI unit economics (item 47, the AI-lab ledger): {_head(r)}: "
            + ("; ".join(parts) or "no measure computable from the entry") + ".")


def sr16_line(rows: list[dict]) -> str:
    """SR-16's AI-credit absorption entry: commitments against revenue."""
    r = latest(rows)
    if not r:
        return f"AI-lab commitments (SR-16, the AI-lab ledger): {NO_ENTRY}."
    m = measures(r)
    if r.get("commitments") is None:
        body = "forward commitments not in the entry"
    elif m["commitments_over_ttm"] is None:
        body = (f"forward commitments ${r['commitments']:,.0f}bn; over TTM revenue: not "
                f"computed (TTM revenue not in the entry)")
    else:
        body = (f"forward commitments ${r['commitments']:,.0f}bn, "
                f"{m['commitments_over_ttm']:.1f}x TTM revenue")
    return f"AI-lab commitments (SR-16, the AI-lab ledger): {_head(r)}: {body}."


def ipo_watch_lines(cfg: Optional[dict] = None) -> list[str]:
    cfg = cfg if cfg is not None else config()
    out = []
    for w in cfg.get("mega_ipo_watch") or []:
        f = [f"{lab} {w.get(k) or NOT_PUBLIC}" for k, lab in
             (("expected_float", "expected float:"),
              ("index_inclusion", "index-inclusion timing:"),
              ("lockups", "lock-ups:"))]
        out.append(f"Mega-IPO watch, {w['name']} ({w.get('note')}): " + "; ".join(f) + ".")
    return out


def lines(rows: Optional[list] = None, cfg: Optional[dict] = None) -> list[str]:
    rows = load() if rows is None else rows
    return [unit_economics_line(rows), sr16_line(rows)] + ipo_watch_lines(cfg)


def _main(argv: list[str]) -> int:
    for ln in lines():
        print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
