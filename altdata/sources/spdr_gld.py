"""
SPDR Gold Trust (GLD) -- tonnes held, shares outstanding, and the share flow.

    python -m altdata.sources.spdr_gld       # one pull, summary to stdout

AQ-3 part 1 (11 Oct 2026; the Quarterly's metals chapter, change order section
4.2, "gold ETF holdings (GLD/IAU tonnage)", and section 10A's standard: "ETF
flows from share counts, never from AUM; flow, position and price-driven AUM kept
apart"); the daily source added 12 Oct 2026 (the operator's ruling on part 1's
Needs you 1: no weekly manual step).

TWO SOURCES.

1. THE ARCHIVE -- a ONE-TIME history load, and the anchor. The trust's
   historical archive, an .xlsx of one row per business day since 18 Nov 2004:
   Date, Closing Price, Ounces of Gold per Share, NAV, ..., Total Ounces of Gold
   in the Trust, Tonnes of Gold, Total Net Asset Value. The site's historical-
   data page (www.spdrgoldshares.com/usa/historical-data/, robots.txt
   "Allow: /") links it at
     https://api.spdrgoldshares.com/api/v1/historical-archive?product=gld&exchange=NYSE&lang=en
   -- and api.spdrgoldshares.com's own robots.txt is "Disallow: /" for every
   agent (read 11 Oct 2026). So, as the AAII writer does, this one does NOT fetch
   a disallowed path. It reads, in order:
     a. THE INBOX: the archive as downloaded once in a browser, dropped in Drive
        under chester-vendor-checks/etf/ and copied by the nightly rclone sweep
        into ~/chester-data/inbox/etf/ (or at $GLD_ARCHIVE_FILE). Every file
        there is tried and the one that reads AS THE GLD ARCHIVE -- by its header
        row, never by its name -- with the latest date is used. available_at is
        the file's modification time (ingest_instant: an upper bound).
     b. The API URL, only while its robots.txt allows it -- read each run.

2. THE DAILY WORKBOOK -- State Street's own NAV history for GLD,
     https://www.ssga.com/us/en/intermediary/library-content/products/fund-data/etfs/us/navhist-us-en-gld.xlsx
   one sheet, newest first: Date, NAV, Shares Outstanding, Total Net Assets,
   back to 2004. www.ssga.com's robots.txt (read each run, 12 Oct 2026) has no
   rule matching the path: its nearest, "Disallow: /fd", is a prefix this path
   does not start with. available_at is the response's Last-Modified (observed).
   It carries NO gold in ounces.

STORED, observed_at = the business day:
  etf.gld_shares        shares outstanding: the workbook's own "Shares
                        Outstanding" wherever it has the day (the primary series
                        under section 10A -- flows from share counts); the
                        archive's total ounces / ounces per share for a day the
                        workbook lacks
  etf.gld_share_flow    the change in that count from the previous business day:
                        creations minus redemptions. A share count, never
                        dollars: AUM moves with the gold price, and a flow read
                        from AUM is mostly price
  etf.gld_oz            troy ounces in the trust: the archive's own figure
                        through the archive's last date; AFTER it, an
                        APPROXIMATION (ruled 12 Oct 2026) --
                          shares x the archive's latest ounces per share
                                 x (1 - ratio / 365) ^ (calendar days since it)
                        the Sponsor's fee, paid in gold, accrued daily at the
                        expense ratio in altdata.config.GLD_EXPENSE_RATIO
  etf.gld_tonnes        etf.gld_oz / 32,150.7466 after the archive's last date;
                        the archive's own column through it
RE-ANCHORING. Each run reads the newest archive in the inbox. When a newer one
appears, the days it now covers carry its exact figures; where those differ from
the approximation already stored, they are written as a revision -- a new vintage
at the file's time, or at this run's instant where the file is not later than
the workbook read beside it (rclone keeps Drive's upload time as the mtime, and
the revision must be the later vintage to win the as-of join) -- and the
approximation runs forward from the new anchor.
Holiday rows ("US Holiday" in every column) are skipped.

The archive's disclaimer forbids redistribution: the store keeps it for the
operator's own read, and the gate's fixtures are synthetic files in each
source's shape, never a cut of the real one.
"""

from __future__ import annotations

import datetime as dt
import logging
import os
from pathlib import Path
from typing import Optional

from .. import session
from . import _publication as pub
from ._base import http_get_response, http_get_text
from .aaii import robots_verdict

log = logging.getLogger(__name__)

SOURCE = "spdr_gld"
URL = ("https://api.spdrgoldshares.com/api/v1/historical-archive"
       "?product=gld&exchange=NYSE&lang=en")
ROBOTS_URL = "https://api.spdrgoldshares.com/robots.txt"
NAVHIST_URL = ("https://www.ssga.com/us/en/intermediary/library-content/products/"
               "fund-data/etfs/us/navhist-us-en-gld.xlsx")
NAVHIST_ROBOTS_URL = "https://www.ssga.com/robots.txt"
OZ_KEY, TONNES_KEY = "etf.gld_oz", "etf.gld_tonnes"
SHARES_KEY, FLOW_KEY = "etf.gld_shares", "etf.gld_share_flow"
KEYS = [OZ_KEY, TONNES_KEY, SHARES_KEY, FLOW_KEY]
FILE_VAR = "GLD_ARCHIVE_FILE"
INBOX_DIR = "~/chester-data/inbox/etf"
ZIP_MAGIC = b"PK\x03\x04"
OZ_PER_TONNE = 32150.7466
# The archive's own column heads, matched case-insensitively and by prefix.
COL_DATE = "date"
COL_OZ_PER_SHARE = "ounces of gold per share"
COL_TOTAL_OZ = "total ounces of gold in the trust"
COL_TONNES = "tonnes of gold"
# The workbook's.
COL_SHARES = "shares outstanding"


def _day(v) -> Optional[str]:
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return pub.excel_serial_date(v)
    t = str(v or "").strip()
    for fmt in ("%d-%b-%Y", "%d-%b-%y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return dt.datetime.strptime(t, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _num(v) -> Optional[float]:
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    try:
        return float(str(v).replace(",", "").strip())
    except ValueError:
        return None


def _header(table: list, want: tuple[str, ...]) -> Optional[tuple[int, dict]]:
    """(row index, {column head: index}) of the first row in the sheet's top
    twenty that carries every head in `want` (case-insensitive, by prefix)."""
    for h, head in enumerate(table[:20]):
        names = [str(c or "").strip().lower() for c in head]
        idx = {w: next((i for i, n in enumerate(names) if n.startswith(w)), None)
               for w in want}
        if None not in idx.values():
            return h, idx
    return None


# ---------------------------------------------------------------------------
# The archive: the one-time history and the anchor
# ---------------------------------------------------------------------------
def archive_points(data: bytes) -> list[dict]:
    """Every dated row of the archive, oldest first: {day, ops, oz, tonnes,
    shares}. Raises when no sheet carries its header -- a file that is not the
    GLD archive."""
    for table in pub.read_xlsx(data).values():
        got = _header(table, (COL_DATE, COL_OZ_PER_SHARE, COL_TOTAL_OZ, COL_TONNES))
        if got is None:
            continue
        h, idx = got
        out = []
        for row in table[h + 1:]:
            if len(row) <= max(idx.values()):
                continue
            day = _day(row[idx[COL_DATE]])
            ops = _num(row[idx[COL_OZ_PER_SHARE]])
            oz = _num(row[idx[COL_TOTAL_OZ]])
            t = _num(row[idx[COL_TONNES]])
            if day is None or not ops or oz is None or t is None:
                continue
            out.append({"day": day, "ops": ops, "oz": oz, "tonnes": t,
                        "shares": int(round(oz / ops))})
        if not out:
            raise ValueError("the GLD archive's header was found but no dated "
                             "row read")
        return sorted(out, key=lambda p: p["day"])
    raise ValueError("no sheet carries the GLD archive's header (Date, Ounces of "
                     "Gold per Share, Total Ounces of Gold in the Trust, Tonnes of "
                     "Gold)")


def _flows(shares: list[tuple[str, int, str, str]]) -> list[dict]:
    """The flow rows over (day, count, available_at, kind), oldest first: each
    day's change from the one before, available when both counts are."""
    out = []
    for (d0, s0, a0, _k0), (d1, s1, a1, k1) in zip(shares, shares[1:]):
        out.append({"registry_key": FLOW_KEY, "instrument": None, "observed_at": d1,
                    "available_at": max(a0, a1), "availability_kind": k1,
                    "value": s1 - s0})
    return out


def rows_from_archive(data: bytes, available_at: str, kind: str) -> list[dict]:
    """The archive alone, as rows: ounces, tonnes, shares, and the flow."""
    pts = archive_points(data)
    out = []
    for p in pts:
        base = {"instrument": None, "observed_at": p["day"],
                "available_at": available_at, "availability_kind": kind}
        out += [dict(base, registry_key=OZ_KEY, value=p["oz"]),
                dict(base, registry_key=TONNES_KEY, value=p["tonnes"]),
                dict(base, registry_key=SHARES_KEY, value=p["shares"])]
    return out + _flows([(p["day"], p["shares"], available_at, kind) for p in pts])


def inbox_files() -> list[Path]:
    if os.environ.get(FILE_VAR):
        return [Path(os.environ[FILE_VAR]).expanduser()]
    d = Path(INBOX_DIR).expanduser()
    return sorted(p for p in d.iterdir() if p.is_file()) if d.is_dir() else []


def archive_from_inbox() -> Optional[tuple[list[dict], str, str]]:
    """(points, available_at, kind) of the newest-dated file in the inbox that
    reads as the archive, or None."""
    best = None
    for p in inbox_files():
        data = p.read_bytes() if p.is_file() else b""
        if data[:4] != ZIP_MAGIC:
            continue
        try:
            pts = archive_points(data)
        except ValueError:
            continue
        when = dt.datetime.fromtimestamp(p.stat().st_mtime, dt.timezone.utc)
        if best is None or pts[-1]["day"] > best[0][-1]["day"]:
            best = (pts, when.isoformat(timespec="microseconds"), "ingest_instant")
    return best


def archive() -> tuple[Optional[tuple[list[dict], str, str]], Optional[str]]:
    """The archive from the inbox, else from the API while its robots.txt allows
    -- ((points, available_at, kind), None), or (None, why not)."""
    got = archive_from_inbox()
    if got is not None:
        return got, None
    try:
        allowed, rule = robots_verdict(http_get_text(ROBOTS_URL, timeout=30), URL)
    except Exception as exc:                                    # noqa: BLE001
        return None, (f"api.spdrgoldshares.com refused robots.txt "
                      f"({str(exc)[:60]}); the archive was not fetched")
    if not allowed:
        return None, (f"api.spdrgoldshares.com robots.txt disallows the archive "
                      f"({rule}); not fetched. Place it, downloaded in a browser "
                      f"from spdrgoldshares.com/usa/historical-data/, in Drive "
                      f"chester-vendor-checks/etf/ (the rclone sweep copies it to "
                      f"{INBOX_DIR}) or at ${FILE_VAR}")
    data, headers = http_get_response(URL, timeout=60)
    return (archive_points(data), *pub.availability(headers)), None


# ---------------------------------------------------------------------------
# The daily workbook
# ---------------------------------------------------------------------------
def navhist_points(data: bytes) -> list[tuple[str, int]]:
    """(day, shares outstanding), oldest first, from State Street's NAV-history
    workbook. Read by its header row (Date, Shares Outstanding), never by the
    file's name; raises when no sheet carries it."""
    for table in pub.read_xlsx(data).values():
        got = _header(table, (COL_DATE, COL_SHARES))
        if got is None:
            continue
        h, idx = got
        out = {}
        for row in table[h + 1:]:
            if len(row) <= max(idx.values()):
                continue
            day = _day(row[idx[COL_DATE]])
            n = _num(row[idx[COL_SHARES]])
            if day is None or n is None or n <= 0:
                continue
            out[day] = int(round(n))
        if not out:
            raise ValueError("the NAV-history header was found but no dated row read")
        return sorted(out.items())
    raise ValueError("no sheet carries the NAV-history header (Date, Shares "
                     "Outstanding)")


def navhist() -> tuple[Optional[tuple[list[tuple[str, int]], str, str]], Optional[str]]:
    """The daily workbook, fetched only while www.ssga.com's robots.txt allows
    its path -- ((points, available_at, kind), None), or (None, why not)."""
    try:
        allowed, rule = robots_verdict(http_get_text(NAVHIST_ROBOTS_URL, timeout=30),
                                       NAVHIST_URL)
    except Exception as exc:                                    # noqa: BLE001
        return None, (f"www.ssga.com refused robots.txt ({str(exc)[:60]}); the "
                      f"daily workbook was not fetched")
    if not allowed:
        return None, (f"www.ssga.com robots.txt disallows the daily workbook "
                      f"({rule}); not fetched")
    try:
        data, headers = http_get_response(NAVHIST_URL, timeout=60)
        return (navhist_points(data), *pub.availability(headers)), None
    except Exception as exc:                                    # noqa: BLE001
        return None, f"the daily workbook: {type(exc).__name__}: {str(exc)[:80]}"


# ---------------------------------------------------------------------------
# The forward approximation
# ---------------------------------------------------------------------------
def expense_ratio() -> float:
    from .. import config                                       # noqa: PLC0415
    return float(config.GLD_EXPENSE_RATIO["ratio"])


def ounces_per_share(anchor_ops: float, anchor_day: str, day: str,
                     ratio: Optional[float] = None) -> float:
    """The anchor's ounces per share carried to `day`, less the Sponsor's fee
    accrued daily: ops x (1 - ratio / 365) ^ calendar days."""
    r = expense_ratio() if ratio is None else ratio
    days = (dt.date.fromisoformat(day) - dt.date.fromisoformat(anchor_day)).days
    return anchor_ops * (1.0 - r / 365.0) ** days


def combine(arch: Optional[tuple[list[dict], str, str]],
            nav: Optional[tuple[list[tuple[str, int]], str, str]],
            ratio: Optional[float] = None) -> list[dict]:
    """Every row the two sources make together. Shares: the workbook's where it
    has the day, else the archive's. Ounces and tonnes: the archive's through
    its last day, the approximation after it (the workbook's days only)."""
    shares: dict[str, tuple[int, str, str]] = {}
    out: list[dict] = []
    if arch is not None:
        pts, a_at, a_kind = arch
        # THE RE-ANCHOR MUST WIN THE AS-OF JOIN. rclone keeps Drive's upload time
        # as the file's mtime, and a run between the upload and the nightly sweep
        # stamps its approximation with the workbook's Last-Modified -- which can
        # be the later instant, and the join would then keep the approximation
        # over the exact figure for good. So where the file is not later than the
        # workbook read beside it, the exact ounces carry this run's instant
        # (ingest_instant): strictly later than any approximation an earlier run
        # stamped, and still an upper bound. Unchanged rows are never rewritten,
        # so only a revision ever carries it.
        ex_at, ex_kind = a_at, a_kind
        if nav is not None and a_at <= nav[1]:
            ex_at, ex_kind = session.utc_iso(timespec="microseconds"), "ingest_instant"
        for p in pts:
            shares[p["day"]] = (p["shares"], a_at, a_kind)
            base = {"instrument": None, "observed_at": p["day"],
                    "available_at": ex_at, "availability_kind": ex_kind}
            out += [dict(base, registry_key=OZ_KEY, value=p["oz"]),
                    dict(base, registry_key=TONNES_KEY, value=p["tonnes"])]
    if nav is not None:
        npts, n_at, n_kind = nav
        for d, n in npts:
            shares[d] = (n, n_at, n_kind)
        if arch is not None:
            anchor = arch[0][-1]
            for d, n in npts:
                if d <= anchor["day"]:
                    continue
                oz = n * ounces_per_share(anchor["ops"], anchor["day"], d, ratio)
                base = {"instrument": None, "observed_at": d,
                        # Made of both sources: knowable when the later one is.
                        "available_at": max(n_at, arch[1]),
                        "availability_kind": n_kind}
                out += [dict(base, registry_key=OZ_KEY, value=round(oz, 3)),
                        dict(base, registry_key=TONNES_KEY,
                             value=round(oz / OZ_PER_TONNE, 4))]
    seq = [(d, *shares[d]) for d in sorted(shares)]
    out += [{"registry_key": SHARES_KEY, "instrument": None, "observed_at": d,
             "available_at": at, "availability_kind": k, "value": n}
            for d, n, at, k in seq]
    return out + _flows(seq)


def _produce() -> list[dict]:
    arch, why_a = archive()
    nav, why_n = navhist()
    if arch is None and nav is None:
        raise PermissionError(f"{why_n}; {why_a}")
    if nav is None:
        log.warning("%s: %s -- the archive alone this run", SOURCE, why_n)
    if arch is None:
        log.warning("%s: %s -- shares and flows only; no ounces without an anchor",
                    SOURCE, why_a)
    return combine(arch, nav)


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
