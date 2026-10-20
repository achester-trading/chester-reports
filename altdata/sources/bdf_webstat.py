"""
Banque de France, Webstat -- the French 10-year (TEC 10), daily, from Webstat's
own keyless export of one series.

    python -m altdata.sources.bdf_webstat    # one pull

SR-30 daily (st-r5-audit, 16 Oct 2026; Batch 3 SR-30 as amended by Batch 5 item
28). The OAT-Bund tiers sit on the daily weekly close (ruled 13 Oct 2026), and
the order waited on a Banque de France Webstat key, which ruling (a) of 16 Oct
2026 sets aside (friction is a gap, not a key). The key turns out not to be
needed: the series page's own export is anonymous. Read by
altdata/batch3.py's eu_stress() through config/batch3_tranche_a.yaml.

  bdf.oat_tec10   PERCENT, daily: "Taux de l'Echeance Constante - 10 ans"
                  (FM.D.FR.EUR.FR2.BB.FRMOYTEC10.HSTA), the Banque de France's
                  constant-maturity 10-year French government yield, an
                  interpolation between the two OATs either side of ten years;
                  history from November 2004

SOURCE (checked 16 Oct 2026). https://webstat.banque-france.fr/export/csv/fr/
catalogue/FM/<series key>: semicolon-separated, decimal comma, newest first, one
row per business day. The same export is what data.gouv.fr republishes for
Webstat's FM dataset ("Ressource FM"). No key, no login, no browser:
webstat.banque-france.fr's robots.txt is "Allow: /", read each run, and the
fetch stops on a disallow. Webstat's API proper needs a key; this does not use it.

READ BY CONTENT. The columns are found by name (series_key, time_period,
obs_value, updated_at); every row must name this series, or the file is
refused; a file with no row is refused. A blank value is skipped.

AVAILABILITY, `observed`, from the file's own updated_at per row: the instant
the value as now stated was set. For the current days it is the publication
(the same day, about 11:00-13:00 UTC); for history reloaded later (2004-2024
rows carry 2 Dec 2024) it is later than the first publication, which is safe for
an as-of join; a revised value carries its revision's instant, never backdated.
Clamped to the write instant. observed_at = the business day.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import logging
from typing import Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "bdf_webstat"
SITE = "https://webstat.banque-france.fr"
SERIES = {"FM.D.FR.EUR.FR2.BB.FRMOYTEC10.HSTA": "bdf.oat_tec10"}
KEYS = list(SERIES.values())
COLUMNS = ("series_key", "time_period", "obs_value", "updated_at")


def url_of(series: str) -> str:
    return f"{SITE}/export/csv/fr/catalogue/FM/{series}"


def parse(text: str, series: str) -> list[tuple[str, float, str]]:
    """[(day, value, updated_at UTC)] for `series`. Refuses a file missing a
    column, carrying another series, or holding no row."""
    rd = csv.DictReader(io.StringIO(text.lstrip("﻿")), delimiter=";")
    missing = [c for c in COLUMNS if c not in (rd.fieldnames or [])]
    if missing:
        raise ValueError(f"the Webstat export lacks column(s) {missing}")
    out = []
    for r in rd:
        if r["series_key"] != series:
            raise ValueError(f"the Webstat export carries {r['series_key']!r}, "
                             f"not {series}")
        v = (r["obs_value"] or "").strip()
        if not v:
            continue
        day = dt.date.fromisoformat(r["time_period"]).isoformat()
        upd = dt.datetime.fromisoformat(r["updated_at"]).astimezone(dt.timezone.utc)
        out.append((day, float(v.replace(",", ".")), upd.isoformat(timespec="microseconds")))
    if not out:
        raise ValueError(f"the Webstat export for {series} holds no row")
    return sorted(out)


def rows_from(files: dict[str, str], now: Optional[str] = None) -> list[dict]:
    now = now or dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")
    rows = []
    for series, key in SERIES.items():
        rows += [{"registry_key": key, "instrument": None, "observed_at": day,
                  "available_at": min(upd, now), "value": v,
                  "availability_kind": "observed"}
                 for day, v, upd in parse(files[series], series)]
    return rows


def fetch_rows() -> list[dict]:
    files = {}
    for series in SERIES:
        url = url_of(series)
        allowed, rule = pub.robots_allows(SITE, url)
        if not allowed:
            raise PermissionError(f"webstat.banque-france.fr robots.txt disallows "
                                  f"{url} ({rule})")
        body, _ = http_get_response(url, timeout=120)
        files[series] = body.decode("utf-8")
    return rows_from(files)


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, fetch_rows, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
