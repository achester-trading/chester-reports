"""
Cboe's daily put/call ratios: equity, index and total (signal-triage Batch 17,
item 97(b)(i); B79, 26 Oct 2026). Family 2 of the Capitulation Count reads the
equity ratio's 20-session mean (altdata/capitulation_count.py).

    python -m altdata.sources.cboe_putcall [--date YYYY-MM-DD] [--backfill-from D] [--dry-run]

SOURCE (read 26 Oct 2026). Cboe's daily market statistics page
(www.cboe.com/us/options/market_statistics/daily/) is drawn from one JSON file a
session, cdn.cboe.com/data/us/options/market_statistics/daily/<YYYY-MM-DD>_daily_options,
no key. Its "ratios" list carries, by NAME, TOTAL PUT/CALL RATIO, INDEX PUT/CALL
RATIO and EQUITY PUT/CALL RATIO (with the ETP, VIX and SPX ratios, not stored).
The file for 23 Oct 2026 reads total 0.93, index 1.10, equity 0.67, the post's
figures (V1). Files answer from late 2019; earlier dates answer 403 (the CSV
archive of 2006-2019 is a separate file set, not read here).

ROBOTS (26 Oct 2026). www.cboe.com's robots.txt disallows /book/ and
/*market_statistics/volume_reports/ only; cdn.cboe.com's answers 403, which RFC
9309 (2.3.1.3) reads as no rules, the reading cboe_indices takes. Checked on every
pull by the wildcard-aware reader; a refusal writes nothing and is never retried
around.

TERMS (read 26 Oct 2026; www.cboe.com/terms, "Last Updated: November 16, 2022"):
"You may view, print and download one copy of the Materials for your personal
non-commercial use ... You may not otherwise copy, reproduce, alter, store either
in hard copy or in an electronic retrieval system ...". That is the clause the
CoinGecko retirement turned on (a point-in-time store), so this writer ships
SWITCHED OFF (`ENABLED` below) and stores nothing until the operator rules. With
the switch off, a pull returns STALE with that reason; family 2 prints as a gap.

STORED, observed_at = the session the file is for, available_at = the file's
Last-Modified (pub.availability):
  cboe.pc_equity, cboe.pc_index, cboe.pc_total     the three ratios
DERIVED COMPANIONS, computed at read time by `mean_and_percentiles()` (the
percentile through derived.percentile_of) and not stored, so a restated file
cannot leave a stale companion behind:
  calc.pc_equity_20d                               the equity ratio's 20-session mean
  calc.pc_equity_pct_1y, calc.pc_index_pct_1y,    each ratio's percentile in its
  calc.pc_total_pct_1y                             own trailing 252 sessions
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
from typing import Callable, Optional

from . import _publication as pub

log = logging.getLogger(__name__)

SOURCE = "cboe_putcall"
BASE = "https://cdn.cboe.com/data/us/options/market_statistics/daily/"
ROBOTS = ("https://www.cboe.com/robots.txt", "https://cdn.cboe.com/robots.txt")
AGENT = "chester-reports"
TERMS = ("https://www.cboe.com/terms (Last Updated 16 Nov 2022, read 26 Oct 2026): "
         "one copy for personal non-commercial use; no other storing in an "
         "electronic retrieval system")

# THE SWITCH. Off by ruling D40 (27 Oct 2026): the terms above fail the 16 Oct rule.
ENABLED = False
OFF_REASON = ("switched off: Cboe's terms forbid storing the data in an electronic "
              "retrieval system, which fails the 16 Oct 2026 rule (ruled D40, 27 Oct 2026)")

# the file's ratio name -> store key
RATIOS = {"EQUITY PUT/CALL RATIO": "cboe.pc_equity",
          "INDEX PUT/CALL RATIO": "cboe.pc_index",
          "TOTAL PUT/CALL RATIO": "cboe.pc_total"}
# A literal list: feeds.static_keys() reads it from source.
KEYS = ["cboe.pc_equity", "cboe.pc_index", "cboe.pc_total"]
DERIVED_KEYS = ["calc.pc_equity_20d", "calc.pc_equity_pct_1y",
                "calc.pc_index_pct_1y", "calc.pc_total_pct_1y"]
MEAN_SESSIONS = 20
PCT_SESSIONS = 252


def url(day: str) -> str:
    return f"{BASE}{day}_daily_options"


def rows_from_json(text: str, day: str, available: str, kind: str) -> list[dict]:
    """The three ratios of one session's file, found by name, never position."""
    doc = json.loads(text)
    found = {}
    for r in doc.get("ratios") or []:
        name = str(r.get("name", "")).strip().upper()
        if name in RATIOS:
            try:
                found[RATIOS[name]] = float(r.get("value"))
            except (TypeError, ValueError):
                continue                      # blank or malformed: skipped, never zero
    missing = [k for k in KEYS if k not in found]
    if missing:
        raise ValueError(f"{day}: the file lacks {', '.join(missing)}")
    return [{"registry_key": k, "instrument": None, "observed_at": day,
             "available_at": available, "value": found[k], "availability_kind": kind}
            for k in KEYS]


def _robots_text(robots_url: str) -> str:
    import requests                                             # noqa: PLC0415
    r = requests.get(robots_url, timeout=30, headers={"User-Agent": AGENT})
    if 400 <= r.status_code < 500:
        return ""                    # unavailable: no rules (RFC 9309, 2.3.1.3)
    r.raise_for_status()
    return r.text


def robots_ok(get: Optional[Callable[[str], str]] = None) -> tuple[bool, str]:
    """Both hosts: the page's and the file's, by the wildcard-aware reader."""
    from .aaii import robots_verdict                            # noqa: PLC0415
    get = get or _robots_text
    paths = {ROBOTS[0]: "https://www.cboe.com/us/options/market_statistics/daily/",
             ROBOTS[1]: f"{BASE}2026-10-23_daily_options"}
    for ru, path in paths.items():
        ok, rule = robots_verdict(get(ru), path, AGENT)
        if not ok:
            return False, f"{ru} refuses it ({rule})"
    return True, ""


def fetch_rows(days: list[str], get=None, robots=None, enabled: Optional[bool] = None) -> list[dict]:
    """Every requested session's rows. Raises (the run goes STALE, nothing written)
    on the switch, on robots, or on a 4xx: one attempt each, no retry around a
    refusal."""
    if not (ENABLED if enabled is None else enabled):
        raise PermissionError(OFF_REASON)
    ok, why = robots_ok(robots)
    if not ok:
        raise PermissionError(f"robots.txt: {why}")
    if get is None:
        from ._base import http_get_response                    # noqa: PLC0415
        get = lambda u: http_get_response(u, timeout=60, max_retries=1)  # noqa: E731
    rows: list[dict] = []
    for day in days:
        data, headers = get(url(day))
        available, kind = pub.availability(headers)
        rows.extend(rows_from_json(data.decode("utf-8", errors="replace"), day,
                                   available, kind))
    return rows


def mean_and_percentiles(pts: dict[str, list[tuple[str, float]]]) -> list[tuple[str, str, float]]:
    """(key, day, value) for the derived companions, from each ratio's sorted points."""
    from altdata import derived                                 # noqa: PLC0415
    out = []
    eq = pts.get("cboe.pc_equity") or []
    for i in range(MEAN_SESSIONS - 1, len(eq)):
        win = [v for _, v in eq[i - MEAN_SESSIONS + 1:i + 1]]
        out.append(("calc.pc_equity_20d", eq[i][0], sum(win) / len(win)))
    for key in KEYS:
        s = pts.get(key) or []
        name = key.split(".")[1].replace("pc_", "")
        for i in range(PCT_SESSIONS - 1, len(s)):
            win = [v for _, v in s[i - PCT_SESSIONS + 1:i + 1]]
            p = derived.percentile_of(win, s[i][1])
            if p is not None:
                out.append((f"calc.pc_{name}_pct_1y", s[i][0], p))
    return out


def sessions(start: str, end: str) -> list[str]:
    from altdata import session                                 # noqa: PLC0415
    d, e, out = dt.date.fromisoformat(start), dt.date.fromisoformat(end), []
    while d <= e:
        if session.is_trading_session(d):
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def pull(days: list[str], run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, lambda: fetch_rows(days), run_id=run_id, db=db)


def _main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Cboe daily put/call ratios (item 97(b)(i))")
    ap.add_argument("--date", help="one session (default: the last completed session)")
    ap.add_argument("--backfill-from", help="every session from this date to --date")
    ap.add_argument("--dry-run", action="store_true", help="fetch and parse; write nothing")
    a = ap.parse_args(argv)
    from altdata import session                                 # noqa: PLC0415
    end = a.date or str(session.last_completed_session())
    days = sessions(a.backfill_from, end) if a.backfill_from else [end]
    if a.dry_run:
        try:
            rows = fetch_rows(days)
        except Exception as exc:                                # noqa: BLE001
            print(f"STALE: {type(exc).__name__}: {exc}")
            return 1
        print(json.dumps(rows[:6], indent=2))
        print(f"{len(rows)} rows parsed over {len(days)} sessions; nothing written")
        return 0
    print(json.dumps(pull(days), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    sys.exit(_main(sys.argv[1:]))
