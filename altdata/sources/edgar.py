"""
SEC EDGAR: filings for the universe.

    python -m altdata.sources.edgar probe
    python -m altdata.sources.edgar pull

-----------------------------------------------------------------------------
IT NEEDS A CONTACT ADDRESS, AND IT WILL NOT INVENT ONE
-----------------------------------------------------------------------------

EDGAR's access policy requires a User-Agent that identifies the requester WITH A
CONTACT ADDRESS, and it enforces it: every request with `chester-reports/1.0`
returns 403, with or without a URL in the string. Probed four forms; only a UA
carrying an email address is served.

So this module reads `CHESTER_SEC_CONTACT` through the secrets loader and stays
DORMANT until it is set, reporting `not_configured` with the line to add. It does
not fall back to a default address, for two reasons that point the same way: a
fabricated contact is a lie to a regulator's server, and a personal address
belongs in the operator's own config rather than in a repository or a transcript.

    # in .env, beside the keys -- not a secret, but personal data
    CHESTER_SEC_CONTACT=you@example.com

The address is used for ONE thing: the User-Agent header on requests to sec.gov.

-----------------------------------------------------------------------------
WHAT THE PROBE FOUND, 25 September 2026
-----------------------------------------------------------------------------

  company_tickers.json      10,413 companies, ticker -> CIK. SPY resolves (884394,
                            the trust), so an ETF in the universe is not a gap.
  submissions/CIK##########  1,000 recent filings per company, each with `form`,
                            `filingDate`, `acceptanceDateTime`, `accessionNumber`
                            and `primaryDocument`.

TWO DATES, AND THE FILING DATE IS THE WRONG ONE. A filing accepted after 17:30 ET
carries the NEXT business day as its filingDate, so a Thursday-evening 8-K is
dated Friday. `acceptanceDateTime` is the instant the document became public and
is what goes into observed_at; available_at stays our own ingest instant.
"""

from __future__ import annotations

import logging
from typing import Any, Iterable, Optional

from .. import events as ev_mod
from .. import secrets
from ._base import FetchError, http_get_json

log = logging.getLogger(__name__)

CONTACT_VAR = "CHESTER_SEC_CONTACT"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

# THE FORMS WORTH A ROW, and what each one means about why it arrived.
#
# An 8-K is the only one here that exists BECAUSE SOMETHING HAPPENED -- a material
# event the company had to disclose within four business days. The rest are
# calendar-driven: a 10-Q arrives because a quarter ended, a 13F because 45 days
# passed. Both are worth having and they answer different questions, so the form is
# in the payload and a reader is never left to infer it from a title.
FORMS = {
    "8-K": "a material event, disclosed within four business days",
    "8-K/A": "an amendment to a material-event disclosure",
    "10-Q": "the quarterly report -- calendar-driven",
    "10-K": "the annual report -- calendar-driven",
    "13F-HR": "a quarter-end institutional holdings report, filed up to 45 days "
              "after the date it describes",
}
# How far back a pull looks. The feed is ordered newest first, so this is a slice
# rather than a filter: 40 filings covers a quiet company for a year and a busy one
# for a month, and the dedupe index makes re-reading them free.
RECENT = 40


def contact() -> Optional[str]:
    """The operator's contact address, or None. Never a default."""
    try:
        return secrets.get(CONTACT_VAR)
    except Exception:                                          # noqa: BLE001
        return None


def user_agent() -> Optional[str]:
    c = contact()
    return f"chester-reports/1.0 ({c})" if c else None


def universe() -> list[str]:
    """The equity and ETF symbols the system tracks.

    Indices are excluded -- ^VIX has no CIK and never will -- by the one property
    that distinguishes them in this repo's symbol list rather than by a hand-kept
    second list.
    """
    from .yfinance_source import SYMBOLS
    out = []
    for sym in SYMBOLS:
        s = sym.upper()
        if s.startswith("^") or "=" in s or "-" in s:
            continue
        out.append(s)
    return sorted(set(out))


def cik_map(headers: dict) -> dict[str, str]:
    j = http_get_json(TICKERS_URL, headers=headers) if _accepts_headers() else {}
    if not j:
        import requests
        r = requests.get(TICKERS_URL, headers=headers, timeout=30)
        r.raise_for_status()
        j = r.json()
    return {str(v["ticker"]).upper(): str(v["cik_str"]).zfill(10)
            for v in j.values() if v.get("ticker")}


def _accepts_headers() -> bool:
    """http_get_json predates the header argument; ask rather than assume."""
    import inspect
    return "headers" in inspect.signature(http_get_json).parameters


def filing_events(symbols: Optional[Iterable[str]] = None
                  ) -> tuple[list[ev_mod.Event], dict]:
    """Recent filings for the universe, as `filing` events."""
    ua = user_agent()
    if not ua:
        return [], {"state": "not_configured", "reason": (
            f"{CONTACT_VAR} is not set, and EDGAR returns 403 to any User-Agent "
            f"without a contact address (four forms probed). Add "
            f"`{CONTACT_VAR}=you@example.com` to .env; it is used only in the "
            f"User-Agent header on requests to sec.gov. This module does not "
            f"invent an address: a fabricated contact is a lie to a regulator's "
            f"server")}
    headers = {"User-Agent": ua}
    syms = list(symbols or universe())
    report: dict[str, Any] = {"state": "ok", "symbols": len(syms),
                              "resolved": 0, "missing": [], "failed": {}}
    try:
        ciks = cik_map(headers)
    except Exception as exc:                                   # noqa: BLE001
        return [], {"state": "failed",
                    "reason": f"ticker map: {type(exc).__name__}: {exc}"[:200]}
    out: list[ev_mod.Event] = []
    import requests
    for sym in syms:
        cik = ciks.get(sym)
        if not cik:
            report["missing"].append(sym)
            continue
        try:
            r = requests.get(SUBMISSIONS_URL.format(cik=cik), headers=headers,
                             timeout=30)
            r.raise_for_status()
            rec = (r.json().get("filings") or {}).get("recent") or {}
        except Exception as exc:                               # noqa: BLE001
            report["failed"][sym] = f"{type(exc).__name__}: {exc}"[:120]
            continue
        report["resolved"] += 1
        forms = rec.get("form") or []
        for i in range(min(RECENT, len(forms))):
            form = forms[i]
            if form not in FORMS:
                continue
            acc = (rec.get("accessionNumber") or [""])[i]
            accepted = (rec.get("acceptanceDateTime") or [""])[i]
            if not accepted:
                continue
            doc = (rec.get("primaryDocument") or [""])[i]
            url = (f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
                   f"{acc.replace('-', '')}/{doc}") if doc else None
            out.append(ev_mod.Event(
                type="filing", observed_at=accepted, source="sec_edgar",
                title=f"{sym} {form}", url=url, entities=[sym], key=acc,
                payload={"form": form, "why_it_arrived": FORMS[form],
                         "cik": cik, "accession": acc,
                         "filing_date": (rec.get("filingDate") or [None])[i],
                         "accepted_at": accepted,
                         "published_at": accepted}))
    return out, report


def pull(store: Optional[ev_mod.EventStore] = None,
         dry_run: bool = False) -> dict:
    own = store is None
    ev = store or ev_mod.EventStore()
    try:
        events, report = filing_events()
        wrote = ({"seen": len(events), "inserted": 0, "duplicates": 0}
                 if dry_run else ev.write_many(events))
        return {"edgar": report, "written": wrote, "dry_run": dry_run}
    finally:
        if own:
            ev.close()


def _main(argv: list[str]) -> int:
    import argparse
    import json
    p = argparse.ArgumentParser(description="SEC EDGAR filings.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe")
    pl = sub.add_parser("pull")
    pl.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO)

    if a.cmd == "probe":
        print(f"{CONTACT_VAR}: "
              + ("set" if contact() else "NOT SET -- EDGAR will stay dormant"))
        events, rep = filing_events()
        print(json.dumps(rep, indent=2, default=str)[:1200])
        for e in events[:6]:
            print(f"  {e.observed_at[:19]}  {e.title:<14} {e.url or ''}"[:120])
        print(f"{len(events)} filing event(s) ready")
        return 0
    print(json.dumps(pull(dry_run=a.dry_run), indent=2, default=str)[:1600])
    return 0


if __name__ == "__main__":                                     # pragma: no cover
    import sys
    raise SystemExit(_main(sys.argv[1:]))
