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
them as sourced figures; this module reads the store and computes, per asset:

  median       of the houses with a current edition
  dispersion   the highest less the lowest, and the count of houses
  dropped      an edition whose data as-of is more than `stale_months` before the
               cutoff is left out, and the count says so

A house with no stored edition prints "no edition stored", never a recalled
figure. Each edition's horizon and basis (nominal or real) are its scan's own
rows and print beside it; the median is taken across them as published, with no
conversion, and the table says so.

Reads only (scans.latest opens the store read-only). No composite, no
market-state object, no decision: item 30's Book A line prints the median and
nothing reads it back.
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
            "figures": {a["id"]: by[a["metric"]] for a in cfg["assets"]
                        if a["metric"] in by}})
    current = [h for h in houses if h["state"] == "current"]
    assets = []
    for a in cfg["assets"]:
        vals = []
        for h in current:
            f = h["figures"].get(a["id"])
            v = None if f is None else number(f["value"])
            if v is not None:
                vals.append((h["id"], v))
        nums = [v for _, v in vals]
        assets.append({
            **a, "values": dict(vals), "n": len(nums),
            "median": None if not nums else round(statistics.median(nums), 2),
            "dispersion": None if len(nums) < 2 else round(max(nums) - min(nums), 2)})
    return {"as_of": str(cutoff)[:10], "floor": floor, "houses": houses,
            "assets": assets, "current": len(current),
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
    return f["value"]


def table(r: dict) -> dict:
    """One row per asset: each house's figure as stored, then the median, the
    dispersion and the count."""
    cols = (["Asset"] + [h["id"].upper() if len(h["id"]) <= 4 else h["id"].title()
                         for h in r["houses"]]
            + ["Median", "High less low", "Houses"])
    rows = []
    for a in r["assets"]:
        rows.append([a["label"]]
                    + [_house_cell(h, a["id"], r["no_edition"]) for h in r["houses"]]
                    + [_pct(a["median"]),
                       "—" if a["dispersion"] is None else f"{a['dispersion']:.1f} pp",
                       str(a["n"])])
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
    parts = [f"{n} of {len(r['houses'])} houses have a current edition"
             + (f" ({k} dropped as older than {r['stale_months']} months)" if k else "")
             + "."]
    if us and us["median"] is not None and exus and exus["median"] is not None:
        gap = round(exus["median"] - us["median"], 2)
        parts.append(f"The median 10-year expected return for ex-US developed equity "
                     f"is {exus['median']:.1f}% against {us['median']:.1f}% for US "
                     f"equity ({gap:+.1f} pp).")
    widest = max((a for a in r["assets"] if a["dispersion"] is not None),
                 key=lambda a: a["dispersion"], default=None)
    if widest:
        parts.append(f"The houses disagree most on {widest['label']} "
                     f"({widest['dispersion']:.1f} pp from high to low, "
                     f"n={widest['n']}).")
    parts.append("Horizons and bases are each house's own, printed below; the median "
                 "is taken as published, with no conversion.")
    return " ".join(parts)


def book_a_line(r: Optional[dict]) -> str:
    """Item 30's Book A long-horizon expected-return line. Report only."""
    if not r:
        return ("Book A long-horizon expected return (cross-house CMA median): "
                "no CMA edition stored.")
    a = next((x for x in r["assets"] if x["id"] == r["book_a_asset"]), None)
    if a is None or a["median"] is None:
        return ("Book A long-horizon expected return (cross-house CMA median): "
                "no CMA edition stored.")
    disp = ("" if a["dispersion"] is None else
            f", {a['dispersion']:.1f} pp from high to low")
    return (f"Book A long-horizon expected return (cross-house CMA median, "
            f"{a['label']}): {a['median']:.1f}% a year over each house's horizon "
            f"(n={a['n']} houses{disp}; as published, report only).")


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
