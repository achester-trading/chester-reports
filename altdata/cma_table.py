"""
Signal-triage Batch 14, item 62 (written as 55; ST-R6.62a): the cross-house
capital-market-assumptions table -- report only.

    from altdata import cma_table as cma
    r = cma.read(cutoff, db_path)
    cma.lead(r); cma.table(r); cma.book_a_line(r)
    python -m altdata.cma_table show [--as-of 2026-10-31]

F2 of the order: the table is not updated by hand. The chat-side publication
watch writes each house's edition as a scan file (docs/scans/cma-<house>-
<YYYY>q<N>.md) whose reference table carries the 10-year expected return per
asset, each row with its own source URL; `python -m altdata.scans ingest` stores
them as sourced figures; this module reads the store and computes, per asset
and per basis (ruling D17 of 24 Oct 2026: two medians, never mixed):

  median       nominal and real, each of the current houses on that basis
  dispersion   the highest less the lowest on each basis, and its count of houses
  dropped      an edition whose data as-of is more than `stale_months` before the
               cutoff is left out, and the count says so

An edition's basis is its scan's "Basis" row: "real" or "nominal" (as a word); a
basis that is neither is in neither median and the read says so. Each house's
figure prints on its own basis beside the medians, its horizon as published and
labelled. A house with no stored edition prints "no edition stored", never a
recalled figure.

Reads only (scans.latest opens the store read-only). No composite, no
market-state object, no decision: item 30's Book A line prints the nominal
US-equity median -- the real one, labelled, when fewer than two nominal houses
have a current edition -- and nothing reads it back.
"""

from __future__ import annotations

import datetime as dt
import re
import statistics
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "cma_table.yaml"
NUMBER = re.compile(r"[-+]?\d+(?:\.\d+)?")
BASES = ("nominal", "real")


def config(path: Optional[Path] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8")) or {}


def _months_back(day: str, months: int) -> str:
    d = dt.date.fromisoformat(day[:10])
    y, m = divmod(d.month - 1 - months, 12)
    year, month = d.year + y, m + 1
    for dd in (d.day, 30, 29, 28):
        try:
            return dt.date(year, month, dd).isoformat()
        except ValueError:
            continue
    return dt.date(year, month, 28).isoformat()


def number(value: str) -> Optional[float]:
    """'6.1%' / '6.1' / '+6.1 %' -> 6.1; a value with no number -> None."""
    m = NUMBER.search(str(value or "").replace(",", ""))
    return float(m.group(0)) if m else None


def basis_of(text: Optional[str]) -> Optional[str]:
    """An edition's Basis row -> 'nominal' or 'real' (as a word), else None."""
    t = str(text or "").lower()
    if re.search(r"\breal\b", t):
        return "real"
    if re.search(r"\bnominal\b", t):
        return "nominal"
    return None


def _stats(vals: list[tuple[str, float]]) -> dict:
    nums = [v for _, v in vals]
    return {"values": dict(vals), "n": len(nums),
            "median": None if not nums else round(statistics.median(nums), 2),
            "dispersion": None if len(nums) < 2 else round(max(nums) - min(nums), 2)}


def read(cutoff: str, db_path: Optional[str] = None, cfg: Optional[dict] = None,
         rows: Optional[list] = None) -> dict:
    """Every house's newest stored edition readable at the cutoff, and the
    per-asset median and dispersion across the current ones. `rows` (the shape
    scans.latest returns) is for a gate; otherwise the store is read."""
    cfg = cfg or config()
    if rows is None:
        from . import scans                                     # noqa: PLC0415
        rows = scans.latest(cutoff, db_path)
    prefix = cfg.get("family_prefix", "cma-")
    floor = _months_back(str(cutoff)[:10], int(cfg.get("stale_months", 15)))
    houses = []
    for h in cfg["houses"]:
        fam = f"{prefix}{h['id']}"
        rs = [r for r in rows if r.get("family") == fam]
        if not rs:
            houses.append({**h, "state": "none"})
            continue
        by = {r["metric"]: r for r in rs}
        as_of = max(r["as_of"] for r in rs)
        houses.append({
            **h, "state": "stale" if as_of < floor else "current",
            "edition": rs[0].get("edition") or rs[0].get("title"), "as_of": as_of,
            "read_on": rs[0].get("read_on"),
            "horizon": (by.get(cfg.get("horizon_metric", "Horizon")) or {}).get("value"),
            "basis": (by.get(cfg.get("basis_metric", "Basis")) or {}).get("value"),
            "basis_kind": basis_of((by.get(cfg.get("basis_metric", "Basis")) or {}).get("value")),
            "figures": {a["id"]: by[a["metric"]] for a in cfg["assets"]
                        if a["metric"] in by}})
    current = [h for h in houses if h["state"] == "current"]
    assets = []
    for a in cfg["assets"]:
        by_basis: dict[str, list] = {b: [] for b in BASES}
        for h in current:
            f = h["figures"].get(a["id"])
            v = None if f is None else number(f["value"])
            if v is not None and h["basis_kind"] in by_basis:
                by_basis[h["basis_kind"]].append((h["id"], v))
        assets.append({**a, **{b: _stats(by_basis[b]) for b in BASES}})
    return {"as_of": str(cutoff)[:10], "floor": floor, "houses": houses,
            "assets": assets, "current": len(current),
            "unclassified": [h["id"] for h in current if h["basis_kind"] is None],
            "dropped": [h["id"] for h in houses if h["state"] == "stale"],
            "missing": [h["id"] for h in houses if h["state"] == "none"],
            "no_edition": cfg.get("no_edition", "no edition stored"),
            "book_a_asset": cfg.get("book_a_asset", "us_equity"),
            "stale_months": int(cfg.get("stale_months", 15))}


def _pct(v: Optional[float]) -> str:
    return "—" if v is None else f"{v:.1f}%"


def _house_cell(h: dict, aid: str, no_edition: str) -> str:
    if h["state"] == "none":
        return no_edition
    if h["state"] == "stale":
        return "dropped (stale)"
    f = h["figures"].get(aid)
    if f is None:
        return "not in the edition"
    basis = h.get("basis_kind") or "basis not stated"
    horizon = h.get("horizon") or "horizon not stated"
    return f"{f['value']} ({basis}, {horizon})"


def _median_cell(s: dict) -> str:
    if s["median"] is None:
        return "—"
    return _pct(s["median"]) + ("" if s["dispersion"] is None else
                                f" ({s['dispersion']:.1f} pp high less low)")


def table(r: dict) -> dict:
    """One row per asset: each house's figure on its own basis and horizon, then
    the nominal and the real median, each with its spread and its count."""
    cols = (["Asset"] + [h["id"].upper() if len(h["id"]) <= 4 else h["id"].title()
                         for h in r["houses"]]
            + ["Median, nominal", "Houses, nominal", "Median, real", "Houses, real"])
    rows = []
    for a in r["assets"]:
        rows.append([a["label"]]
                    + [_house_cell(h, a["id"], r["no_edition"]) for h in r["houses"]]
                    + [_median_cell(a["nominal"]), str(a["nominal"]["n"]),
                       _median_cell(a["real"]), str(a["real"]["n"])])
    return {"columns": cols, "rows": rows}


def edition_lines(r: dict) -> list[str]:
    """Each house's edition, its horizon and basis, its as-of and source; or why
    it is not in the median."""
    out = []
    for h in r["houses"]:
        if h["state"] == "none":
            out.append(f"{h['name']}: {r['no_edition']}.")
            continue
        url = next((f["source_url"] for f in h["figures"].values()), None)
        hz = h.get("horizon") or "horizon not stated"
        bs = h.get("basis") or "basis not stated"
        tail = (f" Dropped: older than {r['stale_months']} months at this cutoff."
                if h["state"] == "stale" else "")
        out.append(f"{h['name']}: {h['edition']}, data as of {h['as_of']} "
                   f"({hz}; {bs}){'; ' + url if url else ''}.{tail}")
    return out


def lead(r: dict) -> str:
    """The code-written read, printed before the table."""
    n, k = r["current"], len(r["dropped"])
    if not n:
        base = (f"No house's capital market assumptions are stored with a current "
                f"edition ({len(r['missing'])} of {len(r['houses'])} have none"
                + (f"; {k} dropped as older than {r['stale_months']} months" if k else "")
                + "), so no median prints.")
        return base
    us = next((a for a in r["assets"] if a["id"] == "us_equity"), None)
    exus = next((a for a in r["assets"] if a["id"] == "exus_dev_equity"), None)
    nb = {b: sum(1 for h in r["houses"]
                 if h["state"] == "current" and h.get("basis_kind") == b) for b in BASES}
    u = len(r.get("unclassified") or [])
    parts = [f"{n} of {len(r['houses'])} houses have a current edition"
             + (f" ({k} dropped as older than {r['stale_months']} months)" if k else "")
             + f": {nb['nominal']} nominal, {nb['real']} real"
             + (f", {u} with no stated basis and in neither median" if u else "") + "."]
    for b in BASES:
        if us and us[b]["median"] is not None and exus and exus[b]["median"] is not None:
            gap = round(exus[b]["median"] - us[b]["median"], 2)
            parts.append(f"The {b} median expected return for ex-US developed equity "
                         f"is {exus[b]['median']:.1f}% against {us[b]['median']:.1f}% for "
                         f"US equity ({gap:+.1f} pp).")
            break
    cands = [(a, b) for a in r["assets"] for b in BASES if a[b]["dispersion"] is not None]
    widest = max(cands, key=lambda x: x[0][x[1]]["dispersion"], default=None)
    if widest:
        a, b = widest
        parts.append(f"The houses disagree most on {a['label']}, {b} "
                     f"({a[b]['dispersion']:.1f} pp from high to low, n={a[b]['n']}).")
    parts.append("Nominal and real are two medians, never mixed; each house prints on "
                 "its own basis and horizon, as published, with no conversion.")
    return " ".join(parts)


def book_a_basis(a: dict) -> Optional[str]:
    """Ruling D17: the nominal median; the real one when fewer than two nominal
    houses have a current edition; the one nominal house when there is no real
    one (SESSION-SET: the ruling does not name that case); else None."""
    if a["nominal"]["n"] >= 2:
        return "nominal"
    if a["real"]["n"] >= 1:
        return "real"
    if a["nominal"]["n"] == 1:
        return "nominal"
    return None


def book_a_line(r: Optional[dict]) -> str:
    """Item 30's Book A long-horizon expected-return line. Report only."""
    none = ("Book A long-horizon expected return (cross-house CMA median): "
            "no CMA edition stored.")
    if not r:
        return none
    a = next((x for x in r["assets"] if x["id"] == r["book_a_asset"]), None)
    b = None if a is None else book_a_basis(a)
    if b is None:
        return none
    s = a[b]
    disp = ("" if s["dispersion"] is None else
            f", {s['dispersion']:.1f} pp from high to low")
    why = ("" if b == "nominal" else
           f"; real because fewer than two nominal houses have a current edition "
           f"(n={a['nominal']['n']})")
    return (f"Book A long-horizon expected return (cross-house CMA median, "
            f"{a['label']}, {b}): {s['median']:.1f}% a year over each house's horizon "
            f"(n={s['n']} houses{disp}{why}; as published, report only).")


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415

    from . import session                                       # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.cma_table")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show", help="print the table as of a cutoff (read-only)")
    s.add_argument("--as-of")
    a = ap.parse_args(argv)
    r = read(a.as_of or session.utc_iso())
    print(lead(r))
    t = table(r)
    print(" | ".join(t["columns"]))
    for row in t["rows"]:
        print(" | ".join(row))
    for ln in edition_lines(r) + [book_a_line(r)]:
        print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
