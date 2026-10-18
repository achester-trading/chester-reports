"""
SEC EDGAR XBRL frames -- the five hyperscalers' annual operating cash flow and
capital expenditure, for GTM-4's cash-flow bridge.

    python -m altdata.sources.edgar_xbrl          # one pull, summary to stdout

The J.P. Morgan Guide batch, part 2 (17 Oct 2026; change order of 3 Oct 2026,
GTM-4): operating cash flow less capex, 2019 to the latest filed year, beside the
Guide's consensus capex path (sourced figures, config/gtm.yaml).

SOURCE. https://data.sec.gov/api/xbrl/frames/us-gaap/<tag>/USD/CY<year>.json --
no key. One call per tag per calendar year returns every filer's one fact that
most closely fits the year (an annual duration of 365 days, +/- 30). The filers,
their CIKs and the tags are config/ai_buckets.yaml's `bridge`. A FISCAL year sits
in the calendar frame its larger part falls in, so Microsoft's year to June 2024
and Oracle's to May 2024 are in CY2023: the stored row keeps the fact's own end
date, and altdata/gtm_equities.py groups by the year of the period's midpoint,
which is the frame's year.

THE CONTACT. EDGAR serves only a User-Agent carrying a contact address, and this
module takes it from edgar.user_agent() (CHESTER_SEC_CONTACT) and nowhere else.
Without it the run is PENDING, "not configured", and fetches nothing.

STORED, dollars, instrument = the filer's ticker (Alphabet as GOOGL), observed_at
= the fact's period end:
  edgar.xbrl_operating_cash_flow   NetCashProvidedByUsedInOperatingActivities
  edgar.xbrl_capex                 PaymentsToAcquirePropertyPlantAndEquipment,
                                   else PaymentsToAcquireProductiveAssets
                                   (Amazon's purchases of property and equipment)
A filer with none of a field's tags in a year's frame writes nothing for it, and
the bridge prints "not stored" in its place.

WHICH YEARS. The first pull reads every year from `first_year` to last year; a
later pull reads the years not yet stored and the last two years again (a 10-K
filed in the spring, a restatement), so a run is a handful of calls. The frames
carry no publication instant, so available_at is the write instant
(`ingest_instant`): late but never early. revision_policy: revised.
"""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Optional

import yaml

from .. import observations, session
from . import _publication as pub
from . import edgar
from ._base import http_get_json

log = logging.getLogger(__name__)

SOURCE = "edgar_xbrl"
FRAMES_URL = "https://data.sec.gov/api/xbrl/frames/us-gaap/{tag}/USD/CY{year}.json"
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "ai_buckets.yaml"
OCF_KEY = "edgar.xbrl_operating_cash_flow"
CAPEX_KEY = "edgar.xbrl_capex"
FIELD_KEYS = {"operating_cash_flow": OCF_KEY, "capex": CAPEX_KEY}
KEYS = [OCF_KEY, CAPEX_KEY]
REFRESH_YEARS = 2


def bridge_config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return (yaml.safe_load(fh) or {}).get("bridge") or {}


def rows_from_frames(frames: dict[tuple[str, int], dict], cfg: dict,
                     available: str) -> list[dict]:
    """Observation rows from {(tag, year): frame JSON}. For each filer, field and
    year the FIRST tag in the field's list that carries the filer wins; a filer
    with none writes nothing."""
    by_cik = {int(f["cik"]): f["ticker"] for f in cfg["filers"]}
    years = sorted({y for _, y in frames})
    out = []
    for field, tags in cfg["tags"].items():
        key = FIELD_KEYS[field]
        for year in years:
            seen: set[str] = set()
            for tag in tags:
                fr = frames.get((tag, year)) or {}
                for d in fr.get("data") or []:
                    try:
                        tk = by_cik.get(int(d.get("cik")))
                        val = float(d.get("val"))
                    except (TypeError, ValueError):
                        continue
                    end = str(d.get("end") or "")[:10]
                    if not tk or tk in seen or len(end) != 10:
                        continue
                    seen.add(tk)
                    out.append({"registry_key": key, "instrument": tk,
                                "observed_at": end, "value": val,
                                "available_at": available,
                                "availability_kind": "ingest_instant"})
    return out


def years_to_read(db: Optional[observations.ObservationStore], cfg: dict,
                  today: Optional[dt.date] = None) -> list[int]:
    today = today or session.session_date_obj()
    last = today.year - 1
    first = int(cfg.get("first_year", 2019))
    held: set[int] = set()
    if db is not None:
        for (end,) in db.conn.execute(
                "SELECT DISTINCT observed_at FROM observations WHERE registry_key = ?",
                (OCF_KEY,)):
            # The frame's year: the year of the period's midpoint.
            d = dt.date.fromisoformat(str(end)[:10]) - dt.timedelta(days=182)
            held.add(d.year)
    return [y for y in range(first, last + 1)
            if y not in held or y > last - REFRESH_YEARS]


def fetch_frames(years: list[int], cfg: dict, headers: dict) -> dict:
    out = {}
    for tags in cfg["tags"].values():
        for tag in tags:
            for y in years:
                out[(tag, y)] = http_get_json(FRAMES_URL.format(tag=tag, year=y),
                                              headers=headers, timeout=60)
    return out


def pull(run_id: Optional[str] = None, db=None) -> dict:
    ua = edgar.user_agent()
    if not ua:
        return pub.pending(SOURCE, f"not configured: {edgar.CONTACT_VAR} is unset, "
                           f"and EDGAR serves no request without a contact", run_id)
    cfg = bridge_config()

    def produce() -> list[dict]:
        own = db is None
        store = db or observations.ObservationStore()
        try:
            years = years_to_read(store, cfg)
        finally:
            if own:
                store.close()
        frames = fetch_frames(years, cfg, {"User-Agent": ua})
        return rows_from_frames(frames, cfg, session.utc_iso(timespec="microseconds"))
    # The bridge reaches back to 2019: a backfilled year is older than the default
    # write window and must still land on the first run.
    return pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db, window_days=3700)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
