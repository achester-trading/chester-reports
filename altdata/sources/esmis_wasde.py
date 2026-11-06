"""
USDA's World Agricultural Supply and Demand Estimates, through the National
Agricultural Library's release service (ESMIS), for the Alternative Assets
Quarterly's agriculture section (b69-quarterly-readers-1; D34 of 24 Oct 2026;
B67 section 25).

    python -m altdata.sources.esmis_wasde               # the newest release
    python -m altdata.sources.esmis_wasde --releases 12 # the listing's releases

TERMS (re-read 25 Oct 2026). www.usda.gov answers 403 to every request from this
project (B67), so the release service is read instead: esmis.nal.usda.gov's
robots.txt allows /publication/ and /sites/default/release-files/. ESMIS publishes
no terms page of its own (/about answered 404 on 25 Oct 2026; none is linked). The
WASDE is a work of the United States Government, which is not subject to copyright
(17 U.S.C. 105); the World Agricultural Outlook Board is cited on every row's key
description. Recorded for the operator in the notes (needs-you).

SOURCE. Each release's XML (wasdeMMYY.xml), linked from the publication page. Its
three US tables: wheat (sr11, matrix1), feed grains and corn (sr12, matrix2: corn,
million bushels) and soybeans (sr15, matrix1). The XML's attribute suffix differs
by table (attribute1, attribute4); the reader matches by prefix.

  usda.wasde.<crop>.ending_stocks   million bushels
  usda.wasde.<crop>.stocks_to_use   ending stocks / total use, percent

PROJECTIONS ARE KEPT APART FROM OBSERVED. The instrument names the marketing year
AND its status as the release printed it: "2026/27 proj", "2025/26 est", "2024/25"
(a closed year). A projection and an estimate never share an instrument, so no
read can mix them; a projection's revisions are its own instrument's vintages.
Where a release prints two forecast months for the projected year (last month's
and this month's), only this month's is stored.

observed_at = the first day of the release's report month. available_at = the
file's Last-Modified (observed), else the read instant (ingest_instant).
"""
from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from typing import Optional

from . import _publication as pub
from . import _quarterly_common as qc
from ._base import http_get_response, http_get_text

log = logging.getLogger(__name__)

SOURCE = "usda_esmis"
LISTING = "https://esmis.nal.usda.gov/publication/world-agricultural-supply-and-demand-estimates"
TABLES = {"wheat": ("sr11", "matrix1"), "corn": ("sr12", "matrix2"),
          "soybeans": ("sr15", "matrix1")}
KEYS = ["usda.wasde.wheat.ending_stocks", "usda.wasde.wheat.stocks_to_use",
        "usda.wasde.corn.ending_stocks", "usda.wasde.corn.stocks_to_use",
        "usda.wasde.soybeans.ending_stocks", "usda.wasde.soybeans.stocks_to_use"]
MONTHS = {m: i for i, m in enumerate(
    ("January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"), 1)}


def _fetch(url: str, **kw):
    """Every request through THIS module's helpers (patchable by the gates)."""
    return qc.fetch(url, get=lambda u, **k: http_get_response(u, **k),
                    get_text=lambda u: http_get_text(u, timeout=30), **kw)


def _robots(url: str) -> str:
    return qc.robots_check(url, get_text=lambda u: http_get_text(u, timeout=30))


def _attr(e: ET.Element, prefix: str) -> Optional[str]:
    for k, v in e.attrib.items():
        if k.startswith(prefix) and not k.startswith(prefix + "_"):
            return v
    return None


def _num(s: Optional[str]) -> Optional[float]:
    if s is None:
        return None
    t = s.replace(",", "").strip()
    try:
        return float(t)
    except ValueError:
        return None


def status_of(market_year: str) -> str:
    """'2026/27 proj', '2025/26 est' or '2024/25': the year and its printed status."""
    y = re.match(r"\s*(\d{4}/\d{2})", market_year or "")
    if not y:
        raise ValueError(f"no marketing year in {market_year!r}")
    low = market_year.lower()
    tag = " proj" if "proj" in low else " est" if "est" in low else ""
    return y.group(1) + tag


def table_values(matrix: ET.Element, line: str, month_abbr: str) -> dict[str, float]:
    """{instrument: value} for one line ('Ending Stocks', 'Use, Total')."""
    out: dict[str, float] = {}
    for a in matrix.iter():
        name = _attr(a, "attribute")
        if not name or re.sub(r"\s+", " ", name).strip() != line:
            continue
        for y in a.iter():
            my = _attr(y, "market_year")
            if my is None:
                continue
            for mg in y.iter():
                fm = _attr(mg, "forecast_month")
                if fm is None:
                    continue
                for c in mg.iter("Cell"):
                    v = _num(_attr(c, "cell_value"))
                    if v is None:
                        continue
                    inst = status_of(my)
                    # a projected year printed for two months: this month's wins
                    if fm and fm.strip()[:3] != month_abbr and inst in out:
                        continue
                    out[inst] = v
    return out


def rows_from_xml(data: bytes, available_at: str, kind: str) -> list[dict]:
    root = ET.fromstring(data)
    rows: list[dict] = []
    seen = set()
    for crop, (rep_name, mtag) in TABLES.items():
        rep = next((r for r in root.iter("Report") if r.get("Name") == rep_name), None)
        if rep is None:
            continue
        month = rep.get("Report_Month") or ""
        m = re.match(r"(\w+)\s+(\d{4})", month)
        if not m or m.group(1) not in MONTHS:
            raise ValueError(f"{rep_name}: no report month in {month!r}")
        observed = f"{m.group(2)}-{MONTHS[m.group(1)]:02d}-01"
        matrix = rep.find(mtag)
        if matrix is None:
            raise ValueError(f"{rep_name}: no {mtag} -- the release changed shape")
        abbr = m.group(1)[:3]
        ending = table_values(matrix, "Ending Stocks", abbr)
        use = table_values(matrix, "Use, Total", abbr)
        for inst, v in ending.items():
            seen.add(crop)
            base = {"instrument": inst, "observed_at": observed,
                    "available_at": available_at, "availability_kind": kind}
            rows.append(dict(base, registry_key=f"usda.wasde.{crop}.ending_stocks",
                             value=v))
            if use.get(inst):
                rows.append(dict(base, registry_key=f"usda.wasde.{crop}.stocks_to_use",
                                 value=round(100.0 * v / use[inst], 4)))
    if not seen:
        raise ValueError("no US wheat, corn or soybean table in the WASDE XML")
    return rows


def release_links(html: str) -> list[str]:
    return list(dict.fromkeys(re.findall(
        r'href="([^"]*/release-files/\d+/wasde\d{4}\.xml)"', html)))


def _produce(releases: int = 1) -> list[dict]:
    from urllib.parse import urljoin
    page, _h = _fetch(LISTING)
    links = release_links(page.decode("utf-8", "replace"))[:releases]
    if not links:
        raise ValueError("no WASDE XML linked on the ESMIS publication page")
    rows: list[dict] = []
    for href in links:
        data, headers = _fetch(urljoin(LISTING, href))
        at, kind = pub.availability(headers)
        rows += rows_from_xml(data, at, kind)
    return rows


def pull(run_id: Optional[str] = None, db=None, releases: int = 1) -> dict:
    return pub.run(SOURCE, KEYS, lambda: _produce(releases), run_id=run_id, db=db)


if __name__ == "__main__":
    raise SystemExit(qc.main(pull, releases=(1, "WASDE releases to read, newest first")))
