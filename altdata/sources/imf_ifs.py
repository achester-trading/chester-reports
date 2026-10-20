"""
IMF International Financial Statistics -- central-bank gold, by country.

    python -m altdata.sources.imf_ifs            # one pull, summary to stdout
    python -m altdata.sources.imf_ifs crosscheck # China: SAFE against IFS

Ruled 10 Oct 2026: IMF IFS is the primary source for central-bank gold; the
login-gated wgc.* names are superseded by these (metrics_registry.yaml). The
two-bid decomposition's official leg (AQ-8a) reads the aggregate below.

SOURCE. The IMF's SDMX 3.0 API, api.imf.org (the legacy dataservices.imf.org
JSON service no longer answers; checked 10 Oct 2026). IFS is no longer one
database: its gold-volume line is in the International Liquidity dataflow,
IMF.STA:IL, indicator RGV_REVS "Gold reserves (volume)", unit FTO (fine troy
ounces), monthly. ONE request a pull, for the configured countries
(config/imf_ifs.yaml), returning each series' whole history -- so the first pull
is the backfill. No key: the endpoint answers anonymously. Attribution as the
IMF's terms require: "Source: International Monetary Fund, International
Liquidity (IL)".

STORED (ounces; tonnes are a display conversion, 32,150.7466 oz a tonne):
  imf.ifs.gold_reserves_oz.<iso3>        the month-end holding, observed
  imf.ifs.gold_net_purchases_oz.<iso3>   its change on the month before, derived
                                         here from the same response
  imf.ifs.gold_net_purchases_oz.total    the sum of the month's changes across
                                         the countries that reported both months
  imf.ifs.gold_net_purchases_count.total how many countries that sum covers --
                                         it grows as late reporters land, and
                                         each growth is a new vintage, never an
                                         overwrite
observed_at is the month-end. available_at is the dataset's own
PUBLICATION_DATE (the later of it and UPDATE_DATE), `observed`: the instant the
IMF published the vintage that carries the number. Where the response carries
neither, the ingest instant, `ingest_instant`. The IMF revises: a changed value
is a second vintage (observations.drop_unchanged), never an overwrite; after the
first write, only the last WRITE_WINDOW_DAYS are re-sent (_publication).

THE RESPONSE (SDMX-JSON 2.0): data.structures[0] names the series dimensions
(COUNTRY, INDICATOR, UNIT, FREQUENCY) and the observation dimension
(TIME_PERIOD, values like "2026-M06" -- NOT in chronological order); a series
key "0:0:0:0" indexes those lists; each observation is [OBS_VALUE, ...] with the
value a STRING in ounces (China "75440000"). The SCALE attribute ("6") is a
display hint, not a multiplier. A dataset attribute that is not enumerated
carries its value inline as a one-element list (the publication instant).

CHINA. SAFE (safe.gold_reserves_oz) stays China's primary: it publishes within
days, IL about three months later. IL is the cross-check; crosscheck() flags a
divergence over 1% on any month both hold (tools/validate_imf_china.py, a data
gate).
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any, Optional

from .. import observations, session
from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "imf_ifs"
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "imf_ifs.yaml"
LEVEL = "imf.ifs.gold_reserves_oz."
NET = "imf.ifs.gold_net_purchases_oz."
AGG_KEY = "imf.ifs.gold_net_purchases_oz.total"
AGG_COUNT_KEY = "imf.ifs.gold_net_purchases_count.total"
OZ_PER_TONNE = 32150.7466

# MIRRORED from config/imf_ifs.yaml (the feeds roster reads KEYS from this file
# without importing it, so the list must be a literal here); the gate fails if
# the two differ.
COUNTRIES = ("USA", "DEU", "ITA", "FRA", "CHN", "RUS", "CHE", "IND", "JPN", "TUR",
             "POL", "NLD", "UZB", "TWN", "PRT", "KAZ", "SAU", "GBR", "LBN", "ESP",
             "AUT", "THA", "BEL", "SGP", "IRQ", "CZE", "HUN")
# Stopped reporting the monthly series: pulled and stored, off the roster.
NOT_REPORTING = ("RUS", "LBN")

# The freshness roster: every reporting country's two series and the aggregate.
KEYS = ([LEVEL + c.lower() for c in COUNTRIES if c not in NOT_REPORTING]
        + [NET + c.lower() for c in COUNTRIES if c not in NOT_REPORTING]
        + [AGG_KEY, AGG_COUNT_KEY])

# The registry's bulk blocks read these (members_are: keys): every country,
# reporting or not.
LEVEL_SERIES = {LEVEL + c.lower(): f"{c} gold reserves, ounces" for c in COUNTRIES}
NET_SERIES = {NET + c.lower(): f"{c} gold net purchases, ounces" for c in COUNTRIES}


def config() -> dict:
    import yaml  # noqa: PLC0415
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}


def tonnes(oz: Optional[float]) -> Optional[float]:
    """Ounces to tonnes, for display only."""
    return None if oz is None else oz / OZ_PER_TONNE


def url(cfg: Optional[dict] = None, countries=COUNTRIES) -> tuple[str, dict]:
    a = (cfg or config())["api"]
    key = f"{'+'.join(countries)}.{a['indicator']}.*.{a['frequency']}"
    return (f"{a['base']}/data/dataflow/{a['dataflow']}/{key}",
            {"attributes": "all", "measures": "all"})


# ---------------------------------------------------------------------------
# Parsing the response
# ---------------------------------------------------------------------------
def _period_end(p: str) -> str:
    """'2026-M06' -> '2026-06-30'."""
    y, m = p.split("-M")
    return pub.month_end(int(y), int(m))


def _attr(spec: dict, v: Any) -> Optional[str]:
    """A dataset attribute's value: inline (a one-element list) or an index into
    the attribute's own values."""
    if v is None:
        return None
    if isinstance(v, list):
        return str(v[0]) if v else None
    vals = spec.get("values") or []
    if isinstance(v, int) and 0 <= v < len(vals):
        x = vals[v]
        return str(x.get("id") or x.get("value") or "") or None
    return str(v)


def parse(payload: dict, indicator: str = "RGV_REVS") -> dict:
    """{published, series: {iso3: {month_end: ounces}}} from one SDMX-JSON
    response. A response of another shape raises: a file that changed shape is a
    failure, not a quiet day."""
    data = payload["data"]
    s, ds = data["structures"][0], data["dataSets"][0]
    sdims = s["dimensions"]["series"]
    ids = [d["id"] for d in sdims]
    for need in ("COUNTRY", "INDICATOR", "UNIT", "FREQUENCY"):
        if need not in ids:
            raise ValueError(f"IL response: no {need} series dimension (have {ids})")
    odim = s["dimensions"]["observation"]
    if not odim or odim[0]["id"] != "TIME_PERIOD":
        raise ValueError("IL response: the observation dimension is not TIME_PERIOD")
    periods = [v["value"] for v in odim[0]["values"]]
    meas = [m["id"] for m in (s.get("measures") or {}).get("observation") or []]
    if meas and meas[0] != "OBS_VALUE":
        raise ValueError(f"IL response: first measure is {meas[0]!r}, not OBS_VALUE")
    dattr = s["attributes"].get("dataSet") or []
    stamps = {}
    for spec, v in zip(dattr, ds.get("attributes") or []):
        if spec["id"] in ("PUBLICATION_DATE", "UPDATE_DATE"):
            stamps[spec["id"]] = _attr(spec, v)
    pos = {k: ids.index(k) for k in ("COUNTRY", "INDICATOR", "UNIT", "FREQUENCY")}
    series: dict[str, dict[str, float]] = {}
    for key, ser in (ds.get("series") or {}).items():
        ix = [int(x) for x in key.split(":")]
        val = {k: sdims[p]["values"][ix[p]]["id"] for k, p in pos.items()}
        if val["INDICATOR"] != indicator or val["UNIT"] != "FTO" or val["FREQUENCY"] != "M":
            raise ValueError(f"IL response: unexpected series {val}")
        out = series.setdefault(val["COUNTRY"], {})
        for i, obs in (ser.get("observations") or {}).items():
            raw = obs[0] if obs else None
            if raw in (None, "", "NaN"):
                continue
            x = float(raw)
            if not math.isfinite(x) or x < 0:
                continue
            out[_period_end(periods[int(i)])] = x
    published = max((v for v in stamps.values() if v), default=None)
    return {"published": published, "series": series}


# ---------------------------------------------------------------------------
# Rows
# ---------------------------------------------------------------------------
def _prev_month_end(day: str) -> str:
    y, m = int(day[:4]), int(day[5:7]) - 1
    if m == 0:
        y, m = y - 1, 12
    return pub.month_end(y, m)


def rows_from(parsed: dict, now: Optional[str] = None) -> list[dict]:
    """Level, net-purchase and aggregate rows from one parsed response. The
    publication instant is the response's own, never later than now."""
    now = now or session.utc_iso(timespec="microseconds")
    pubd = observations.canonical_instant(parsed["published"]) if parsed.get("published") else None
    if pubd and pubd <= observations.canonical_instant(now):
        av, kind = pubd, "observed"
    else:
        av, kind = observations.canonical_instant(now), "ingest_instant"
    rows: list[dict] = []
    agg: dict[str, list[float]] = {}

    def add(key: str, day: str, v: float) -> None:
        rows.append({"registry_key": key, "instrument": None, "observed_at": day,
                     "available_at": av, "value": float(v),
                     "availability_kind": kind})

    for c in COUNTRIES:
        s = (parsed.get("series") or {}).get(c) or {}
        for day in sorted(s):
            add(LEVEL + c.lower(), day, s[day])
            p = _prev_month_end(day)
            if p in s:
                d = s[day] - s[p]
                add(NET + c.lower(), day, d)
                agg.setdefault(day, []).append(d)
    for day in sorted(agg):
        add(AGG_KEY, day, sum(agg[day]))
        add(AGG_COUNT_KEY, day, len(agg[day]))
    return rows


def _produce(cfg: Optional[dict] = None) -> list[dict]:
    c = cfg or config()
    u, params = url(c)
    body, _headers = http_get_response(u, params=params, timeout=120,
                                       headers={"Accept": c["api"]["accept"]})
    import json  # noqa: PLC0415
    parsed = parse(json.loads(body.decode("utf-8")), c["api"]["indicator"])
    got = [k for k in COUNTRIES if parsed["series"].get(k)]
    if not got:
        raise ValueError("IL response carried none of the configured countries")
    missing = sorted(set(COUNTRIES) - set(got))
    if missing:
        log.warning("imf_ifs: no series for %s in this response", ", ".join(missing))
    return rows_from(parsed)


def pull(run_id: Optional[str] = None, db=None) -> dict:
    """One pull. The first one writes every month the IMF serves (the backfill);
    later ones re-send the last WRITE_WINDOW_DAYS, and only a changed value is a
    new vintage. STALE, never empty, on any failure."""
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


# ---------------------------------------------------------------------------
# China: SAFE against IFS
# ---------------------------------------------------------------------------
def crosscheck(st, now: Optional[str] = None, max_frac: Optional[float] = None,
               months: int = 24) -> dict:
    """Every month both SAFE and IL hold for China (the last `months`), with the
    fractional gap; `flagged` lists those over the tolerance (1%)."""
    tol = float(max_frac if max_frac is not None else
                config().get("china_divergence_max", 0.01))
    now = now or session.utc_iso(timespec="microseconds")

    def series(key: str) -> dict[str, float]:
        return {str(r["observed_at"])[:10]: float(r["value_num"])
                for r in st.as_of(key, now) if r.get("value_num") is not None}
    safe = series("safe.gold_reserves_oz")
    ifs = series(LEVEL + "chn")
    common = sorted(set(safe) & set(ifs))[-months:]
    rows = []
    for d in common:
        gap = (ifs[d] - safe[d]) / safe[d] if safe[d] else None
        rows.append({"month": d, "safe": safe[d], "ifs": ifs[d], "gap": gap,
                     "flag": gap is not None and abs(gap) > tol})
    return {"tolerance": tol, "months": rows,
            "flagged": [r for r in rows if r["flag"]],
            "latest_common": common[-1] if common else None,
            "safe_latest": max(safe) if safe else None,
            "ifs_latest": max(ifs) if ifs else None}


if __name__ == "__main__":
    import json
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if len(sys.argv) > 1 and sys.argv[1] == "crosscheck":
        with observations.open_writer(__name__) as _st:
            r = crosscheck(_st)
        for m in r["months"]:
            print(f"  {m['month']}  SAFE {m['safe']:>14,.0f}  IFS {m['ifs']:>14,.0f}  "
                  f"gap {100 * (m['gap'] or 0):+.2f}%" + ("  FLAG" if m["flag"] else ""))
        print(f"{len(r['flagged'])} month(s) over {100 * r['tolerance']:.0f}%; latest "
              f"common {r['latest_common']}; SAFE to {r['safe_latest']}, IFS to "
              f"{r['ifs_latest']}")
        raise SystemExit(0)
    print(json.dumps(pull(), indent=2, default=str))
