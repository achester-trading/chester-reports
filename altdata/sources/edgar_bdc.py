"""
Business development companies' filed facts through the existing EDGAR client,
quarterly, for the Alternative Assets Quarterly's credit chapter (the private-
credit section) (b70-quarterly-readers-2; D34 of 24 Oct 2026; B67 section 20).

    python -m altdata.sources.edgar_bdc [--dry-run]

TERMS. SEC EDGAR, the existing `sec_edgar` source: the fair-access rule needs a
contact, CHESTER_SEC_CONTACT from the environment (edgar.user_agent(), never a
literal in the tree). Without it this reader is PENDING and sends nothing, as
edgar_xbrl is.

THE NAMES. Five of the largest listed BDCs: ARCC, FSK, BXSL, OBDC and MAIN. The
Brookfield blocklist is applied at write time like every writer's
(register/instruments.restrictions): OCSL, Oaktree's BDC, is on it (tier 4) and is
not read; a restricted name in NAMES is refused and logged, never stored.

  edgar.bdc.<ticker>.investments_fv   total investments at fair value, USD (us-gaap
                                      InvestmentOwnedAtFairValue; the older
                                      InvestmentsFairValueDisclosure as fallback)
  edgar.bdc.<ticker>.nav_per_share    net asset value per share, USD (us-gaap
                                      NetAssetValuePerShare)

NON-ACCRUALS ARE A LISTED GAP. No standard us-gaap tag carries a BDC's non-accrual
investments; the companies file them in their own extension tags or in prose.
`edgar.bdc.<ticker>.nonaccrual_fv` is registered not_yet_sourced, and NONACCRUAL_TAGS
is empty until a reading on the box names a tag a filing carries (needs-you).

The company-concept files (data.sec.gov/api/xbrl/companyconcept), the CIK from
SEC's company_tickers.json (edgar.cik_map). observed_at = the balance-sheet date;
available_at = the read instant (ingest_instant, an upper bound), as edgar_xbrl.
"""
from __future__ import annotations

import logging
from typing import Optional

from .. import session
from . import _publication as pub
from . import _quarterly_common as qc
from . import edgar
from ._base import http_get_response, http_get_text

log = logging.getLogger(__name__)

SOURCE = "sec_edgar"
NAMES = ("ARCC", "FSK", "BXSL", "OBDC", "MAIN")
FACT_TAGS = {"investments_fv": ("InvestmentOwnedAtFairValue",
                                "InvestmentsFairValueDisclosure"),
             "nav_per_share": ("NetAssetValuePerShare",)}
UNITS = {"investments_fv": "USD", "nav_per_share": "USD/shares"}
NONACCRUAL_TAGS: tuple = ()
CONCEPT_URL = ("https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/"
               "{tag}.json")
QUARTERS = 20
KEYS = [f"edgar.bdc.{t.lower()}.{f}" for t in NAMES for f in FACT_TAGS]


def _get(url: str, headers: dict):
    return qc.fetch(url, get=lambda u, **k: http_get_response(u, headers=headers, **k),
                    get_text=lambda u: http_get_text(u, timeout=30, headers=headers))


def cik_map(headers: dict) -> dict[str, str]:
    """ticker -> ten-digit CIK, from SEC's company_tickers.json, through THIS
    module's helpers (edgar.cik_map's reading, kept here so the gates reach it)."""
    import json
    data, _h = _get(edgar.TICKERS_URL, headers)
    j = json.loads(data.decode("utf-8"))
    return {str(v["ticker"]).upper(): str(v["cik_str"]).zfill(10)
            for v in j.values() if v.get("ticker")}


def allowed(names=NAMES) -> list[str]:
    from register import instruments
    out = []
    for t in names:
        if instruments.restrictions().is_restricted(t):
            log.warning("edgar_bdc: %s is on the Brookfield blocklist; refused, not read", t)
            continue
        out.append(t)
    return out


def rows_from_concept(concept: dict, key: str, ticker: str, unit: str,
                      available_at: str, quarters: int = QUARTERS) -> list[dict]:
    """The newest `quarters` balance-sheet instants; a period filed twice keeps the
    later filing."""
    best: dict[str, tuple[str, float]] = {}
    for f in ((concept.get("units") or {}).get(unit) or []):
        end = str(f.get("end") or "")[:10]
        if len(end) != 10 or f.get("start"):
            continue
        try:
            v = float(f.get("val"))
        except (TypeError, ValueError):
            continue
        filed = str(f.get("filed") or "")
        if end not in best or filed >= best[end][0]:
            best[end] = (filed, v)
    return [{"registry_key": key, "instrument": None, "observed_at": e,
             "value": best[e][1], "available_at": available_at,
             "availability_kind": "ingest_instant"} for e in sorted(best)[-quarters:]]


def _produce(ua: str) -> list[dict]:
    import json
    headers = {"User-Agent": ua}
    ciks = cik_map(headers)
    now = session.utc_iso(timespec="microseconds")
    rows: list[dict] = []
    for t in allowed():
        cik = ciks.get(t)
        if not cik:
            log.warning("edgar_bdc: %s has no CIK in company_tickers.json", t)
            continue
        for fact, tags in FACT_TAGS.items():
            for tag in tags:
                try:
                    data, _h = _get(CONCEPT_URL.format(cik=cik, tag=tag), headers)
                except Exception as exc:                         # noqa: BLE001
                    if "HTTP 404" in str(exc):
                        continue                                  # the tag is not filed
                    raise
                got = rows_from_concept(json.loads(data.decode("utf-8")),
                                        f"edgar.bdc.{t.lower()}.{fact}", t,
                                        UNITS[fact], now)
                if got:
                    rows += got
                    break
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    ua = edgar.user_agent()
    if not ua:
        return pub.pending(SOURCE, f"not configured: {edgar.CONTACT_VAR} is unset, "
                           f"and EDGAR serves no request without a contact", run_id)
    return pub.run(SOURCE, KEYS, lambda: _produce(ua), run_id=run_id, db=db,
                   window_days=3700)


if __name__ == "__main__":
    raise SystemExit(qc.main(pull))
