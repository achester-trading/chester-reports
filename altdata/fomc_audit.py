"""
The FOMC calendar audit (a55 round 2; ruled 21 Oct 2026, 00:41 ET: the history
is entered once as a claim, and a check audits it every so often).

    python -m altdata.fomc_audit check [--today YYYY-MM-DD] [--page FILE]

REPORT-ONLY. It reads the Board's meeting calendar (federalreserve.gov/
monetarypolicy/fomccalendars.htm: no robots.txt is served, and the site policy puts
its content in the public domain, cited to the Board) and compares it with the
FOMC dates in config/claims.yaml (cal.fomc_history's statements and each
cal.fomc_<year>'s decision days). It names:

  * MISSING  a meeting the page publishes that the file lacks -- the next year's
             calendar once the Board posts it, or an unscheduled meeting that
             ended in a statement;
  * CHANGED  a date that differs: the page and the file each hold one in the
             same month that the other does not;
  * SOON     the file's last meeting is less than SIX_MONTHS_DAYS away, so the
             next year's row is due.

A cancelled meeting and a notation vote are not meetings and are skipped, as the
claim leaves them out. It writes no data row and changes nothing; the heartbeat
runs it on the first of each month and prints its lines as WARNINGs, never
touching the verdict or the exit code. If the page cannot be read it says so,
and the SOON line still prints from the file alone.

Exit 0 clean, 1 a finding, 2 the page unreadable (with SOON when due).
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path
from typing import Callable, Optional

URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
# Half a year: the Board posts the next year's calendar by the summer, and six
# months leaves two of this audit's monthly runs to enter it before the rate
# path's four-meeting look-ahead runs past the file.
SIX_MONTHS_DAYS = 183
MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})


def parse_page(html: str) -> dict[int, list[dict]]:
    """{year: [{date, label}]} from the calendar page: the statement's date where
    the page links one, else the meeting's last day."""
    out: dict[int, list[dict]] = {}
    for blk in re.split(r"<h4[^>]*>", html)[1:]:
        ym = re.search(r"(\d{4}) FOMC Meetings", blk[:300])
        if not ym:
            continue
        y = int(ym.group(1))
        for r in re.split(r'<div class="[^"]*\brow fomc-meeting"', blk)[1:]:
            mon = re.search(r"fomc-meeting__month[^>]*>\s*(?:<strong>)?([^<]+)<", r)
            dat = re.search(r"fomc-meeting__date[^>]*>([^<]+)<", r)
            if not mon or not dat:
                continue
            label = f"{mon.group(1).strip()} {dat.group(1).strip()} {y}"
            if re.search(r"notation|cancel", label, re.I):
                continue
            st = re.search(r"pressreleases/monetary(\d{8})a\.htm", r)
            if st:
                d = dt.date(int(st.group(1)[:4]), int(st.group(1)[4:6]), int(st.group(1)[6:]))
            else:
                ms = [MONTHS[m.lower()] for m in re.findall(r"[A-Za-z]+", mon.group(1))
                      if m.lower() in MONTHS]
                days = re.findall(r"\d{1,2}", dat.group(1))
                if not ms or not days:
                    continue
                try:
                    d = dt.date(y, ms[-1], int(days[-1]))
                except ValueError:
                    continue
            out.setdefault(y, []).append({"date": d, "label": label})
    return out


def file_dates(claims: Optional[dict] = None) -> set[dt.date]:
    """Every FOMC date the claims file holds."""
    if claims is None:
        from . import claims as claims_mod                      # noqa: PLC0415
        claims = claims_mod.load(reload=True)["claims"]
    out: set[dt.date] = set()
    for cid, c in claims.items():
        if not (cid.startswith("cal.") and "fomc" in cid):
            continue
        det = c.get("detail") if isinstance(c.get("detail"), dict) else {}
        for d in [r.get("date") for r in det.get("statements") or []] + \
                list(det.get("decision_days") or []):
            if d is not None:
                out.add(d if isinstance(d, dt.date) else dt.date.fromisoformat(str(d)))
    return out


def compare(page: dict[int, list[dict]], have: set[dt.date]) -> dict:
    """{"missing": [(date, label)], "changed": [(file_date, page_date, label)]}."""
    missing, changed = [], []
    for y, rows in sorted(page.items()):
        pd = {r["date"] for r in rows}
        extra = sorted(d for d in have if d.year == y and d not in pd)
        for r in sorted(rows, key=lambda r: r["date"]):
            if r["date"] in have:
                continue
            twin = next((d for d in extra if d.month == r["date"].month), None)
            if twin:
                extra.remove(twin)
                changed.append((twin, r["date"], r["label"]))
            else:
                missing.append((r["date"], r["label"]))
    return {"missing": missing, "changed": changed}


def soon(have: set[dt.date], today: dt.date) -> Optional[str]:
    if not have:
        return "fomc audit: SOON the claims file holds no FOMC meeting"
    last = max(have)
    left = (last - today).days
    if left < SIX_MONTHS_DAYS:
        return (f"fomc audit: SOON the file's last meeting is {last.isoformat()}, "
                f"{left} days away (under {SIX_MONTHS_DAYS}): enter the next year's "
                f"calendar as a claim")
    return None


def run(today: dt.date, get: Optional[Callable[[str], bytes]] = None,
        claims: Optional[dict] = None) -> tuple[int, list[str]]:
    have = file_dates(claims)
    lines, rc = [], 0
    try:
        if get is None:
            from .sources._base import http_get_bytes            # noqa: PLC0415
            get = http_get_bytes
        page = parse_page(get(URL).decode("utf-8", errors="replace"))
        if not page:
            raise ValueError("no year of meetings found on the page")
    except Exception as exc:                                    # noqa: BLE001
        page, rc = None, 2
        lines.append(f"fomc audit: UNREADABLE the Board's calendar could not be read "
                     f"({type(exc).__name__}: {str(exc)[:120]}); the file was not compared")
    if page is not None:
        r = compare(page, have)
        for d, label in r["missing"]:
            lines.append(f"fomc audit: MISSING {d.isoformat()} ({label}) is on the "
                         f"Board's calendar and not in config/claims.yaml")
        for f, p, label in r["changed"]:
            lines.append(f"fomc audit: CHANGED the file holds {f.isoformat()}, the "
                         f"Board's calendar {p.isoformat()} ({label})")
        if r["missing"] or r["changed"]:
            rc = 1
    s = soon(have, today)
    if s:
        lines.append(s)
        rc = rc or 1
    if not lines:
        lines.append(f"fomc audit: clean -- {len(have)} dates in the file, last "
                     f"{max(have).isoformat()}")
    return rc, lines


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m altdata.fomc_audit")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--today", default=None)
    c.add_argument("--page", default=None, help="a saved copy of the page, not fetched")
    a = ap.parse_args(argv)
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    get = (lambda _u: Path(a.page).read_bytes()) if a.page else None
    rc, lines = run(today, get)
    print("\n".join(lines))
    return rc


if __name__ == "__main__":
    sys.exit(main())
