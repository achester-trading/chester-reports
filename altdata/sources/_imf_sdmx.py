"""
The IMF's SDMX 3.0 API: one request, one parsed response. (AQ-9a, 11 Oct 2026)

Shared by the EM scorecard's IMF writers (imf_weo.py, imf_em.py). The model is
altdata/sources/imf_ifs.py (branch imf-ifs-gold, the central-bank gold writer),
generalised: that writer parses one indicator of one dataflow; this parses any
dataflow's series into {dimension: code} and {period: value}, so each writer
states only which series it wants and what it stores them as. imf_ifs can move
onto it once both are on main; nothing here imports it.

ENDPOINT. https://api.imf.org/external/sdmx/3.0, anonymous (no key). The legacy
dataservices.imf.org service no longer answers. A request names the dataflow
("IMF.RES/WEO/+") and a key of dot-separated dimension filters, `+` between
codes ("BRA+CHN.BCA_NGDPD.A").

THE RESPONSE (SDMX-JSON 2.0): data.structures[0] names the series dimensions and
the observation dimension (TIME_PERIOD, values "2026-M06", "2026-Q1" or "2025",
NOT in chronological order); a series key "0:1:0" indexes those lists; each
observation is [OBS_VALUE, ...] with the value a STRING. The dataset attributes
PUBLICATION_DATE and UPDATE_DATE carry their value inline as a one-element list;
the later of the two is the instant the response's numbers were knowable.

A RESPONSE OF ANOTHER SHAPE RAISES: a file that changed shape is a failure, not
a quiet day (sources/_publication.py, STALE not empty).

Attribution, as the IMF's terms require: "Source: International Monetary Fund".
"""

from __future__ import annotations

import json
import math
from typing import Any, Optional

from . import _publication as pub
from ._base import http_get_response

BASE = "https://api.imf.org/external/sdmx/3.0"
ACCEPT = "application/vnd.sdmx.data+json;version=2.0.0"


def url(dataflow: str, key: str, base: str = BASE) -> tuple[str, dict]:
    return (f"{base}/data/dataflow/{dataflow}/{key}",
            {"attributes": "all", "measures": "all"})


def fetch(dataflow: str, key: str, base: str = BASE, accept: str = ACCEPT,
          get=None) -> dict:
    """One request, parsed. `get` is the HTTP function (the writer's own
    module attribute, so an outage test that patches the writer reaches it)."""
    u, params = url(dataflow, key, base)
    body, _headers = (get or http_get_response)(u, params=params, timeout=120,
                                                headers={"Accept": accept})
    return parse(json.loads(body.decode("utf-8")))


def period_end(p: str) -> str:
    """'2026-M06' -> '2026-06-30'; '2026-Q1' -> '2026-03-31'; '2025' ->
    '2025-12-31'; '2026-09' (a BIS month) -> '2026-09-30'."""
    p = str(p).strip()
    if "-M" in p:
        y, m = p.split("-M")
        return pub.month_end(int(y), int(m))
    if "-Q" in p or "Q" in p:
        y, q = p.replace("-Q", "Q").split("Q")
        return pub.month_end(int(y), 3 * int(q))
    if len(p) == 7 and p[4] == "-":
        return pub.month_end(int(p[:4]), int(p[5:7]))
    if len(p) == 4 and p.isdigit():
        return f"{p}-12-31"
    raise ValueError(f"unrecognised period {p!r}")


def _attr(spec: dict, v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, list):
        return str(v[0]) if v else None
    vals = spec.get("values") or []
    if isinstance(v, int) and 0 <= v < len(vals):
        x = vals[v]
        return str(x.get("id") or x.get("value") or "") or None
    return str(v)


def parse(payload: dict) -> dict:
    """{published, dims, series: [{dims: {dimension: code}, obs: {period: float}}]}.

    A missing value, an empty string, NaN or an infinity is skipped -- a gap,
    never a zero."""
    data = payload["data"]
    s, ds = data["structures"][0], data["dataSets"][0]
    sdims = s["dimensions"]["series"]
    ids = [d["id"] for d in sdims]
    if "COUNTRY" not in ids:
        raise ValueError(f"IMF response: no COUNTRY series dimension (have {ids})")
    odim = s["dimensions"]["observation"]
    if not odim or odim[0]["id"] != "TIME_PERIOD":
        raise ValueError("IMF response: the observation dimension is not TIME_PERIOD")
    periods = [v["value"] for v in odim[0]["values"]]
    meas = [m["id"] for m in (s.get("measures") or {}).get("observation") or []]
    if meas and meas[0] != "OBS_VALUE":
        raise ValueError(f"IMF response: first measure is {meas[0]!r}, not OBS_VALUE")
    stamps = {}
    for spec, v in zip(s["attributes"].get("dataSet") or [], ds.get("attributes") or []):
        if spec["id"] in ("PUBLICATION_DATE", "UPDATE_DATE"):
            stamps[spec["id"]] = _attr(spec, v)
    series = []
    for key, ser in (ds.get("series") or {}).items():
        ix = [int(x) for x in key.split(":")]
        dims = {sdims[p]["id"]: sdims[p]["values"][ix[p]]["id"] for p in range(len(ix))}
        obs = {}
        for i, o in (ser.get("observations") or {}).items():
            raw = o[0] if o else None
            if raw in (None, "", "NaN"):
                continue
            x = float(raw)
            if not math.isfinite(x):
                continue
            obs[periods[int(i)]] = x
        series.append({"dims": dims, "obs": obs})
    published = max((v for v in stamps.values() if v), default=None)
    return {"published": published, "dims": ids, "series": series}


def availability(published: Optional[str], now: str) -> tuple[str, str]:
    """(available_at, kind): the response's own publication instant, `observed`,
    never later than now; the ingest instant where it carries none."""
    from .. import observations                                 # noqa: PLC0415
    pubd = observations.canonical_instant(published) if published else None
    nowc = observations.canonical_instant(now)
    if pubd and pubd <= nowc:
        return pubd, "observed"
    return nowc, "ingest_instant"
