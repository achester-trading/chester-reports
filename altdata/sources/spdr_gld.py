"""
SPDR Gold Trust (GLD) -- tonnes held, shares outstanding, and the share flow.

    python -m altdata.sources.spdr_gld       # one pull, summary to stdout

AQ-3 part 1 (11 Oct 2026; the Quarterly's metals chapter, change order section
4.2, "gold ETF holdings (GLD/IAU tonnage)", and section 10A's standard: "ETF
flows from share counts, never from AUM; flow, position and price-driven AUM kept
apart"). The trust's own daily record, back to its first day (18 Nov 2004).

SOURCE. The trust's historical archive, an .xlsx of one row per business day:
Date, Closing Price, Ounces of Gold per Share, NAV, ..., Total Ounces of Gold in
the Trust, Tonnes of Gold, Total Net Asset Value. The site's historical-data page
(www.spdrgoldshares.com/usa/historical-data/, robots.txt "Allow: /") links it at
  https://api.spdrgoldshares.com/api/v1/historical-archive?product=gld&exchange=NYSE&lang=en
-- and api.spdrgoldshares.com's own robots.txt is "Disallow: /" for every agent
(read 11 Oct 2026). So, as the AAII writer does, this one does NOT fetch a
disallowed path. It reads, in order:

  1. THE INBOX: the archive as downloaded in a browser from the historical-data
     page, placed in ~/chester-data/inbox/etf/ (or at $GLD_ARCHIVE_FILE). Every
     file there is tried and the one that reads AS THE GLD ARCHIVE -- by its
     header row, never by its name -- with the latest date is used.
     available_at is the file's modification time (ingest_instant: an upper
     bound, safe for an as-of join).
  2. The API URL, only while its robots.txt allows it -- read each run, so the
     writer fetches by itself if the rule is lifted.
With neither, the run is STALE with the reason and writes nothing.

STORED, observed_at = the archive's date:
  etf.gld_oz            troy ounces of gold in the trust
  etf.gld_tonnes        tonnes of gold in the trust (the archive's own column)
  etf.gld_shares        shares outstanding = total ounces / ounces per share,
                        rounded to the share -- both the trust's own columns
  etf.gld_share_flow    the change in shares outstanding from the previous
                        business day in the file: creations minus redemptions.
                        A share count, never dollars: AUM moves with the gold
                        price, and a flow read from AUM is mostly price.
Holiday rows ("US Holiday" in every column) are skipped.

The archive's disclaimer forbids redistribution: the store keeps it for the
operator's own read, and the gate's fixture is a synthetic file in its shape,
never a cut of the real one.
"""

from __future__ import annotations

import datetime as dt
import logging
import os
from pathlib import Path
from typing import Optional

from . import _publication as pub
from ._base import http_get_response, http_get_text
from .aaii import robots_verdict

log = logging.getLogger(__name__)

SOURCE = "spdr_gld"
URL = ("https://api.spdrgoldshares.com/api/v1/historical-archive"
       "?product=gld&exchange=NYSE&lang=en")
ROBOTS_URL = "https://api.spdrgoldshares.com/robots.txt"
OZ_KEY, TONNES_KEY = "etf.gld_oz", "etf.gld_tonnes"
SHARES_KEY, FLOW_KEY = "etf.gld_shares", "etf.gld_share_flow"
KEYS = [OZ_KEY, TONNES_KEY, SHARES_KEY, FLOW_KEY]
FILE_VAR = "GLD_ARCHIVE_FILE"
INBOX_DIR = "~/chester-data/inbox/etf"
ZIP_MAGIC = b"PK\x03\x04"
# The archive's own column heads, matched case-insensitively and by prefix.
COL_DATE = "date"
COL_OZ_PER_SHARE = "ounces of gold per share"
COL_TOTAL_OZ = "total ounces of gold in the trust"
COL_TONNES = "tonnes of gold"


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


def rows_from_archive(data: bytes, available_at: str, kind: str) -> list[dict]:
    """Every dated row of the archive, from whichever sheet carries its header.
    Raises when no sheet does -- a file that is not the GLD archive."""
    sheets = pub.read_xlsx(data)
    for table in sheets.values():
        for h, head in enumerate(table[:20]):
            names = [str(c or "").strip().lower() for c in head]

            def col(want: str) -> Optional[int]:
                return next((i for i, n in enumerate(names) if n.startswith(want)),
                            None)
            idx = {k: col(k) for k in (COL_DATE, COL_OZ_PER_SHARE, COL_TOTAL_OZ,
                                       COL_TONNES)}
            if None in idx.values():
                continue
            out: list[dict] = []
            prev_shares: Optional[int] = None
            for row in table[h + 1:]:
                if len(row) <= max(idx.values()):
                    continue
                day = _day(row[idx[COL_DATE]])
                ops = _num(row[idx[COL_OZ_PER_SHARE]])
                oz = _num(row[idx[COL_TOTAL_OZ]])
                t = _num(row[idx[COL_TONNES]])
                if day is None or not ops or oz is None or t is None:
                    continue
                shares = int(round(oz / ops))
                base = {"instrument": None, "observed_at": day,
                        "available_at": available_at, "availability_kind": kind}
                out += [dict(base, registry_key=OZ_KEY, value=oz),
                        dict(base, registry_key=TONNES_KEY, value=t),
                        dict(base, registry_key=SHARES_KEY, value=shares)]
                if prev_shares is not None:
                    out.append(dict(base, registry_key=FLOW_KEY,
                                    value=shares - prev_shares))
                prev_shares = shares
            if not out:
                raise ValueError("the GLD archive's header was found but no dated "
                                 "row read")
            return out
    raise ValueError("no sheet carries the GLD archive's header (Date, Ounces of "
                     "Gold per Share, Total Ounces of Gold in the Trust, Tonnes of "
                     "Gold)")


def inbox_files() -> list[Path]:
    if os.environ.get(FILE_VAR):
        return [Path(os.environ[FILE_VAR]).expanduser()]
    d = Path(INBOX_DIR).expanduser()
    return sorted(p for p in d.iterdir() if p.is_file()) if d.is_dir() else []


def from_inbox() -> Optional[list[dict]]:
    """The newest-dated file in the inbox that reads as the archive, or None."""
    best: Optional[list[dict]] = None
    for p in inbox_files():
        data = p.read_bytes() if p.is_file() else b""
        if data[:4] != ZIP_MAGIC:
            continue
        when = dt.datetime.fromtimestamp(p.stat().st_mtime, dt.timezone.utc)
        try:
            rows = rows_from_archive(data, when.isoformat(timespec="microseconds"),
                                     "ingest_instant")
        except ValueError:
            continue
        last = max(r["observed_at"] for r in rows)
        if best is None or last > max(r["observed_at"] for r in best):
            best = rows
    return best


def _produce() -> list[dict]:
    got = from_inbox()
    if got:
        return got
    try:
        allowed, rule = robots_verdict(http_get_text(ROBOTS_URL, timeout=30), URL)
    except Exception as exc:                                    # noqa: BLE001
        raise PermissionError(
            f"api.spdrgoldshares.com refused robots.txt ({str(exc)[:60]}); not "
            f"fetched. Place the archive, downloaded in a browser from "
            f"spdrgoldshares.com/usa/historical-data/, in {INBOX_DIR}") from None
    if not allowed:
        raise PermissionError(
            f"api.spdrgoldshares.com robots.txt disallows the archive ({rule}); not "
            f"fetched. Place it, downloaded in a browser from "
            f"spdrgoldshares.com/usa/historical-data/, in {INBOX_DIR} (or "
            f"${FILE_VAR})")
    data, headers = http_get_response(URL, timeout=60)
    return rows_from_archive(data, *pub.availability(headers))


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
