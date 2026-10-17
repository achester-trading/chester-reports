"""
The EM scorecard's derived lenses, from the stored inputs. (AQ-9a, 11 Oct 2026)

    python -m altdata.sources.em_lenses      # one pass, summary to stdout

Runs in the feeds' official group AFTER the four source writers (imf_weo,
imf_em, bis_cbpol, wb_qeds -- altdata/feeds.py OFFICIAL_WRITERS is ordered), and
reads only the store. Five lenses per country, each a stored series:

  em.lens.reserves_import_months.<iso3>  total reserves (IL) over the trailing
                                         twelve months' average goods imports
                                         (ITG); month-end; needs all twelve months
  em.lens.reserves_st_debt.<iso3>        total reserves at the quarter-end over
                                         short-term external debt (QEDS); times
  em.lens.ext_debt_gdp.<iso3>            gross external debt (QEDS) over GDP in US
                                         dollars (WEO), percent -- GDP of the
                                         quarter's year where stored, else the
                                         latest full year before it (the WEO's
                                         current year is a projection and is not
                                         stored)
  em.lens.real_policy_rate.<iso3>        the BIS policy rate less CPI inflation,
                                         year on year, same month-end; points
  em.lens.inflation_gap.<iso3>           CPI inflation less the configured target
                                         (config/em_scorecard.yaml); points. The
                                         target is today's, applied to the whole
                                         history -- a past target change is not
                                         modelled, and the notes say so

POINT IN TIME. A lens row's available_at is the LATEST of its inputs' -- a ratio
is knowable when the last number in it was -- and its availability_kind the least
observed of theirs (reconstructed, then ingest_instant, then observed), the rule
altdata/market_features.py keeps. Inputs are read as of now; an input revised
later gives the lens a new vintage at the revision's instant. Nothing is
estimated: a month or quarter missing an input has no lens row.

A pass with no input stored at all is STALE (writes nothing), as a writer whose
source failed would be.
"""

from __future__ import annotations

import logging
from typing import Optional

from .. import observations, session
from . import _publication as pub

log = logging.getLogger(__name__)

SOURCE = "em_lenses"
IMPORT_MONTHS = "em.lens.reserves_import_months."
RES_ST = "em.lens.reserves_st_debt."
EXT_GDP = "em.lens.ext_debt_gdp."
REAL_RATE = "em.lens.real_policy_rate."
INFL_GAP = "em.lens.inflation_gap."

# MIRRORED from config/em_scorecard.yaml and the source writers' coverage; the
# gate fails if they differ. A lens is on the roster only where its inputs exist.
COUNTRIES = ("CHN", "TWN", "IND", "KOR", "BRA", "SAU", "ZAF", "MEX", "ARE", "MYS",
             "IDN", "POL", "THA")
WITH_IMPORTS = ("CHN", "TWN", "IND", "KOR", "BRA", "SAU", "MEX", "MYS", "IDN", "POL", "THA")
WITH_QEDS = ("CHN", "IND", "KOR", "BRA", "SAU", "ZAF", "MEX", "MYS", "IDN", "POL", "THA")
WITH_RATE_AND_CPI = ("CHN", "IND", "KOR", "BRA", "SAU", "ZAF", "MEX", "MYS", "IDN", "POL", "THA")
WITH_TARGET = ("CHN", "IND", "KOR", "BRA", "ZAF", "MEX", "IDN", "POL", "THA")

KEYS = ([IMPORT_MONTHS + c.lower() for c in WITH_IMPORTS]
        + [RES_ST + c.lower() for c in WITH_QEDS]
        + [EXT_GDP + c.lower() for c in WITH_QEDS]
        + [REAL_RATE + c.lower() for c in WITH_RATE_AND_CPI]
        + [INFL_GAP + c.lower() for c in WITH_TARGET])

KIND_ORDER = ("reconstructed", "ingest_instant", "observed")


def config() -> dict:
    from ..em_scorecard import config as cfg                    # noqa: PLC0415
    return cfg()


def _series(st, key: str, now: str) -> dict[str, tuple]:
    """day -> (value, available_at, kind) for the latest vintage knowable now."""
    out = {}
    for r in st.as_of(key, now):
        if r.get("value_num") is None:
            continue
        out[str(r["observed_at"])[:10]] = (float(r["value_num"]),
                                           observations.canonical_instant(r["available_at"]),
                                           r.get("availability_kind"))
    return out


def _stamp(*inputs) -> tuple[str, str]:
    av = max(i[1] for i in inputs)
    kinds = {i[2] for i in inputs}
    kind = next((k for k in KIND_ORDER if k in kinds), "observed")
    return av, kind


def _row(key: str, day: str, v: float, *inputs) -> dict:
    av, kind = _stamp(*inputs)
    return {"registry_key": key, "instrument": None, "observed_at": day,
            "available_at": av, "value": v, "availability_kind": kind}


def _month_ends_back(day: str, n: int) -> list[str]:
    y, m = int(day[:4]), int(day[5:7])
    out = []
    for _ in range(n):
        out.append(pub.month_end(y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return out


def compute(st, now: Optional[str] = None, cfg: Optional[dict] = None) -> list[dict]:
    """Every lens row the stored inputs support, as of now."""
    now = now or session.utc_iso(timespec="microseconds")
    targets = {c["iso3"]: c.get("target") for c in (cfg or config())["countries"]}
    rows: list[dict] = []
    for c in COUNTRIES:
        lc = c.lower()
        res = _series(st, f"em.ifs.reserves_usd.{lc}", now)
        imp = _series(st, f"em.itg.imports_usd.{lc}", now)
        cpi = _series(st, f"em.cpi.yoy.{lc}", now)
        pol = _series(st, f"em.bis.policy_rate.{lc}", now)
        ext = _series(st, f"em.qeds.ext_debt_usd.{lc}", now)
        std = _series(st, f"em.qeds.st_debt_usd.{lc}", now)
        gdp = _series(st, f"em.weo.gdp_usd.{lc}", now)
        if c in WITH_IMPORTS:
            for d in sorted(res):
                months = _month_ends_back(d, 12)
                if not all(m in imp for m in months):
                    continue
                avg = sum(imp[m][0] for m in months) / 12.0
                if avg > 0:
                    rows.append(_row(IMPORT_MONTHS + lc, d, res[d][0] / avg, res[d],
                                     *(imp[m] for m in months)))
        if c in WITH_QEDS:
            for q in sorted(std):
                if q in res and std[q][0] > 0:
                    rows.append(_row(RES_ST + lc, q, res[q][0] / std[q][0], res[q], std[q]))
            for q in sorted(ext):
                y = int(q[:4])
                g = gdp.get(f"{y}-12-31") or gdp.get(f"{y - 1}-12-31")
                if g and g[0] > 0:
                    rows.append(_row(EXT_GDP + lc, q, 100.0 * ext[q][0] / g[0], ext[q], g))
        if c in WITH_RATE_AND_CPI:
            for d in sorted(set(pol) & set(cpi)):
                rows.append(_row(REAL_RATE + lc, d, pol[d][0] - cpi[d][0], pol[d], cpi[d]))
        if c in WITH_TARGET and targets.get(c) is not None:
            for d in sorted(cpi):
                rows.append(_row(INFL_GAP + lc, d, cpi[d][0] - float(targets[c]), cpi[d]))
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    """One pass over the store. STALE when no input is stored at all."""
    def produce() -> list[dict]:
        own = db is None
        st = db or observations.open_writer(__name__)
        try:
            return compute(st)
        finally:
            if own:
                st.close()
    return pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, default=str))
