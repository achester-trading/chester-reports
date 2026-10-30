"""
IMF PortWatch: daily transit calls through four chokepoints, for the Alternative
Assets Quarterly's oil chapter (the disruption line) and Factor III
(b69-quarterly-readers-1; D34 of 24 Oct 2026; B67 section 7).

    python -m altdata.sources.portwatch          # one pull, summary to stdout

TERMS (re-read 25 Oct 2026, https://www.imf.org/en/About/copyright-and-terms). The
IMF separates Content from Data. Content: "Copying or downloading IMF Content in
any systematic way" needs written permission. Data: "Users may download, extract,
copy, create derivative works, publish, distribute, and use Data obtained from IMF
Sites subject to these conditions", the first being attribution to the IMF. So
this reader takes the DATA service only, attributes every row ("IMF PortWatch" in
the row's source field, `imf_portwatch:IMF PortWatch`), and sends ONE request a
day (qc.DailyGuard): a request a day is not systematic downloading of Content.

SOURCE. PortWatch's own ArcGIS feature service, keyless (the layer the portal's
FAQ points to): services9.arcgis.com/weJ1QsnbMYJlCHdG/.../Daily_Chokepoints_Data
/FeatureServer/0. Its robots.txt answers 403, which RFC 9309 reads as no rules
(qc.robots_check). Probed once on 25 Oct 2026: HTTP 200, fields date (DateOnly),
portid, portname, n_total, n_tanker, capacity, ...; the newest row 2026-10-18 on a
25 Oct read (PortWatch states its data lags; a lag family covers it).

  imf.portwatch.transits.hormuz         chokepoint6, Strait of Hormuz
  imf.portwatch.transits.suez           chokepoint1, Suez Canal
  imf.portwatch.transits.bab_el_mandeb  chokepoint4, Bab el-Mandeb Strait
  imf.portwatch.transits.malacca        chokepoint5, Malacca Strait

Each the day's n_total (all five vessel classes), a count of transit calls, AIS-
modelled and revisable; tanker calls are kept under `.tanker`.

AVAILABILITY. The row's own date is observed_at; available_at is the instant this
reader read it (ingest_instant, an upper bound): the service publishes no release
time, and backdating a row to its date would claim knowledge the system did not
have. The first pull takes the history the query returns.
"""
from __future__ import annotations

import json
import logging
from typing import Optional
from urllib.parse import urlencode

from .. import session
from . import _publication as pub
from . import _quarterly_common as qc
from ._base import http_get_response, http_get_text

log = logging.getLogger(__name__)

SOURCE = "imf_portwatch"
ATTRIBUTION = "IMF PortWatch"
ROW_SOURCE = f"{SOURCE}:{ATTRIBUTION}"
BASE = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/ArcGIS/rest/services/"
        "Daily_Chokepoints_Data/FeatureServer/0/query")
CHOKEPOINTS = {"chokepoint6": "hormuz", "chokepoint1": "suez",
               "chokepoint4": "bab_el_mandeb", "chokepoint5": "malacca"}
KEYS = ["imf.portwatch.transits.hormuz", "imf.portwatch.transits.suez",
        "imf.portwatch.transits.bab_el_mandeb", "imf.portwatch.transits.malacca",
        "imf.portwatch.transits.hormuz.tanker", "imf.portwatch.transits.suez.tanker",
        "imf.portwatch.transits.bab_el_mandeb.tanker",
        "imf.portwatch.transits.malacca.tanker"]
RECORDS = 2000   # the service's page size; a first pull takes what one page holds


def _fetch(url: str, **kw):
    """Every request through THIS module's helpers (patchable by the gates)."""
    return qc.fetch(url, get=lambda u, **k: http_get_response(u, **k),
                    get_text=lambda u: http_get_text(u, timeout=30), **kw)


def _robots(url: str) -> str:
    return qc.robots_check(url, get_text=lambda u: http_get_text(u, timeout=30))
_guard = qc.DailyGuard(SOURCE)


def query_url() -> str:
    ids = ",".join(f"'{p}'" for p in CHOKEPOINTS)
    return BASE + "?" + urlencode({
        "where": f"portid IN ({ids})", "outFields": "date,portid,n_total,n_tanker",
        "orderByFields": "date DESC", "resultRecordCount": RECORDS,
        "returnGeometry": "false", "f": "json"})


def rows_from_payload(payload: dict, available_at: str) -> list[dict]:
    feats = payload.get("features")
    if not isinstance(feats, list):
        raise ValueError(f"the PortWatch response has no features "
                         f"({str(payload.get('error') or payload)[:120]})")
    out: list[dict] = []
    for f in feats:
        a = (f or {}).get("attributes") or {}
        slug = CHOKEPOINTS.get(str(a.get("portid")))
        day = str(a.get("date") or "")[:10]
        if not slug or len(day) != 10:
            continue
        for suffix, field in (("", "n_total"), (".tanker", "n_tanker")):
            v = a.get(field)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out.append({"registry_key": f"imf.portwatch.transits.{slug}{suffix}",
                            "instrument": None, "observed_at": day,
                            "available_at": available_at, "value": float(v),
                            "availability_kind": "ingest_instant",
                            "source": ROW_SOURCE})
    if feats and not out:
        raise ValueError("the PortWatch response carried no chokepoint rows -- "
                         "the layer changed shape")
    return out


def _produce() -> list[dict]:
    url = query_url()
    _robots(url)
    _guard.charge()                       # counted BEFORE the request is sent
    data, _h = _fetch(url, once=True, robots=False)
    return rows_from_payload(json.loads(data.decode("utf-8")),
                             session.utc_iso(timespec="microseconds"))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    raise SystemExit(qc.main(pull))
