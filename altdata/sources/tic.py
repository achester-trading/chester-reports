"""
Treasury International Capital (TIC) -- foreign holdings of Treasuries, and the
monthly cross-border flows table.

    python -m altdata.sources.tic            # one pull, summary to stdout

Signal-triage order ST-2, §2.2.1: ONE TIC FAMILY serving SR-3 (the China row),
SR-20 (monthly reserve-composition proxies), SR-26 (flow composition) and SR-27
(holder shares), and the absorber side of the Duration Absorption block.

-----------------------------------------------------------------------------
HOLDINGS -- MAJOR FOREIGN HOLDERS OF TREASURY SECURITIES
-----------------------------------------------------------------------------

SOURCE, two tab-separated files on ticdata.treasury.gov, no key, BILLIONS:
  mfhhis01.txt     history, one 12-month block per year back to 2000
  slt_table5.txt   SLT Table 5, the current table: the latest 13 months
(The older "mfh.txt" at the same address is FROZEN at January 2023 and is not
read -- measured 26 Sep 2026.)

STORED, in DOLLARS (billions x 1e9), observed_at = the month-end:
  tic.holdings_by_country    instrument = the country as the table names it
                             ("Japan", "China, Mainland", "Belgium", ...,
                             "All Other"). One series per country; the roster is
                             the table's, which changes as holders move in and
                             out of the published list. Table 5's residual is
                             "All Other (Table 5 roster)": it covers a shorter
                             list than the history file's "All Other".
  tic.holdings_total        Grand Total
  tic.official_holdings      "Of which: Foreign Official"
  tic.official_bills         its Treasury bills
  tic.official_bonds_notes   its Treasury bonds and notes
  tic.private_holdings       Grand Total minus Foreign Official -- the split the
                             table gives, as one subtraction within one month of
                             one table (the table prints the official leg only)

SERIES BREAKS. Before 2012 each year's block carries the break month twice
(June, or March in 2000): the first column continues the NEW series into the
following months and the second is the old series "shown for comparison only".
The first is stored; the comparison column is not.

-----------------------------------------------------------------------------
G-8 -- VINTAGES, AND WHICH ONE A READER GETS
-----------------------------------------------------------------------------

The annual benchmark survey (end-June positions, released the following
February-March) re-attributes holdings toward their ultimate owners, and Treasury
then RESTATES the affected months in both files. This writer never overwrites: a
restated value is written as a NEW ROW for the same observed_at month with the
file's later Last-Modified as its available_at, and the earlier value stays.
(Measured: August 2025 Japan reads 1,180.4 in the May 2026 CSV edition and 1,183.9
in the September 2026 text edition.)

  BY DEFAULT A READER GETS THE LATEST VINTAGE -- the benchmark-revised number,
  whenever the as-of cutoff is after the revision was published. A reader asking
  "what did we know on date D" (an as-of cutoff before the revision) gets the
  pre-revision number. Nothing selects a vintage by name; the as-of join does it.

Two limits. Pre-revision vintages exist only from this writer's FIRST RUN: the
history it backfills is whatever Treasury serves today, already revised. And the
write window is WINDOW_DAYS (three years) so a restatement reaching back beyond
the default 400 days is still recorded as a revision.

AVAILABILITY: each file's Last-Modified, `observed`. revision_policy: revised.
"""

from __future__ import annotations

import calendar
import datetime as dt
import logging
import re
from typing import Optional

from . import _publication as pub
from ._base import http_get_response

log = logging.getLogger(__name__)

SOURCE = "treasury_tic"
BASE = "https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/"
URL_HISTORY = BASE + "mfhhis01.txt"
URL_CURRENT = BASE + "slt_table5.txt"
WINDOW_DAYS = 3 * 365
BILLIONS = 1e9

COUNTRY_KEY = "tic.holdings_by_country"
TOTAL_KEY = "tic.holdings_total"
OFFICIAL_KEY = "tic.official_holdings"
OFFICIAL_BILLS_KEY = "tic.official_bills"
OFFICIAL_BONDS_KEY = "tic.official_bonds_notes"
PRIVATE_KEY = "tic.private_holdings"
HOLDINGS_KEYS = [COUNTRY_KEY, TOTAL_KEY, OFFICIAL_KEY, OFFICIAL_BILLS_KEY,
                 OFFICIAL_BONDS_KEY, PRIVATE_KEY]

MONTHS = {m: i for i, m in enumerate(calendar.month_abbr) if m}
_FOOTNOTE = re.compile(r"\s+\d+/\s*$")


def month_end(year: int, month: int) -> str:
    return dt.date(year, month, calendar.monthrange(year, month)[1]).isoformat()


def _label(cell: str) -> str:
    text = cell.strip().strip('"').strip()
    return _FOOTNOTE.sub("", text).strip()


def _num(cell: str) -> Optional[float]:
    try:
        return float(cell.strip().replace(",", ""))
    except (ValueError, AttributeError):
        return None


def _summary_key(label: str) -> Optional[str]:
    low = label.lower()
    if low.startswith("grand total"):
        return TOTAL_KEY
    if "official" in low and "bill" in low:
        return OFFICIAL_BILLS_KEY
    if "official" in low and ("bond" in low or "note" in low):
        return OFFICIAL_BONDS_KEY
    if low in ("treasury bills",):
        return OFFICIAL_BILLS_KEY          # history file: indented under Official
    if low in ("t-bonds & notes",):
        return OFFICIAL_BONDS_KEY
    if "official" in low:
        return OFFICIAL_KEY
    return None


def parse_holdings(text: str) -> dict[tuple[str, Optional[str], str], float]:
    """{(key, instrument, month_end): billions} from either file's layout.

    Handles both: the history file's per-year blocks (a month-name row, then a
    "Country<TAB>year..." row) and Table 5's single "Country<TAB>YYYY-MM..." row.
    """
    out: dict[tuple[str, Optional[str], str], float] = {}
    lines = [ln.rstrip("\r\n") for ln in text.splitlines()]
    months_row: Optional[list[str]] = None
    cols: Optional[list[Optional[str]]] = None       # month-end per column
    after_total = False
    for ln in lines:
        cells = ln.split("\t")
        first = _label(cells[0]) if cells else ""
        rest = [c.strip() for c in cells[1:]]
        if not first and any(c in MONTHS for c in rest):
            months_row = rest
            continue
        if first == "Country":
            cols, seen = [], set()
            for i, c in enumerate(rest):
                end = None
                m = re.fullmatch(r"(\d{4})-(\d{2})", c)
                if m:
                    end = month_end(int(m.group(1)), int(m.group(2)))
                elif re.fullmatch(r"\d{4}", c) and months_row and i < len(months_row) \
                        and months_row[i] in MONTHS:
                    end = month_end(int(c), MONTHS[months_row[i]])
                # SERIES BREAK: the first column for a month is the continuing
                # series; a repeat is the comparison column and is dropped.
                if end in seen:
                    end = None
                if end:
                    seen.add(end)
                cols.append(end)
            after_total = False
            continue
        if not cols or not first:
            continue
        vals = [_num(c) for c in rest]
        if not any(v is not None for v in vals):
            continue
        summary = _summary_key(first)
        if summary is None and (after_total or first.lower().startswith("of which")):
            continue
        for i, v in enumerate(vals):
            if v is None or i >= len(cols) or not cols[i]:
                continue
            if summary:
                out[(summary, None, cols[i])] = v
            else:
                out[(COUNTRY_KEY, first, cols[i])] = v
        if summary == TOTAL_KEY:
            after_total = True
    return out


# "ALL OTHER" IS A RESIDUAL OVER A ROSTER, AND THE TWO FILES' ROSTERS DIFFER.
# Table 5 lists about twenty holders, the history file about forty, so for the
# same month Table 5's "All Other" is larger. Stored under one name, that
# difference would read as a benchmark revision when it is only a different list.
# Table 5's residual is therefore stored under its own instrument name.
TABLE5_RESIDUAL = "All Other (Table 5 roster)"


def holdings_rows(text: str, available_at: str, kind: str,
                  current_table: bool = False) -> list[dict]:
    parsed = parse_holdings(text)
    if current_table:
        parsed = {((k, TABLE5_RESIDUAL, d) if (k == COUNTRY_KEY and i == "All Other")
                   else (k, i, d)): v for (k, i, d), v in parsed.items()}
    if not any(k[0] == TOTAL_KEY for k in parsed):
        raise ValueError("no Grand Total row in the TIC holdings file")
    rows = []
    for (key, inst, day), v in sorted(parsed.items(), key=lambda x: x[0][2]):
        rows.append({"registry_key": key, "instrument": inst, "observed_at": day,
                     "available_at": available_at, "value": round(v * BILLIONS, 2),
                     "availability_kind": kind})
    for (key, _inst, day), total in parsed.items():
        if key != TOTAL_KEY:
            continue
        official = parsed.get((OFFICIAL_KEY, None, day))
        if official is not None:
            rows.append({"registry_key": PRIVATE_KEY, "instrument": None,
                         "observed_at": day, "available_at": available_at,
                         "value": round((total - official) * BILLIONS, 2),
                         "availability_kind": kind})
    return rows


# ---------------------------------------------------------------------------
# FLOWS -- "TIC monthly reports on Cross-Border Portfolio Financial Flows"
# ---------------------------------------------------------------------------
#
# SOURCE. npr_history.txt, tab-separated, MILLIONS, not seasonally adjusted, one
# row per month ("2026-Jul"), newest first, back to 1978-May. (npr_history.csv is
# stale and is not read.) Revised in place; each republication's Last-Modified is
# its vintage, exactly as for holdings.
#
# 32 LINES, NOT 22. The order names "lines 1-22"; the press-release table was
# expanded in 2023 (when Form SLT replaced Form S, February 2023) and the history
# file now carries 32 numbered columns for every month, the old ones restated into
# the new layout per the file's own footnotes. All 32 are stored: lines 1-22 of the
# current table are the ones the order describes, and 23-32 split bills, other
# negotiable securities and banks' own dollar liabilities into private and
# official, which SR-26/27 read. A column position is trusted only after the file's
# column-number row ("1 2 ... 32") has been found and matches.
FLOWS_URL = BASE + "npr_history.txt"
MILLIONS = 1e6
FLOW_LINES: dict[int, str] = {
    1: "tic.flow_gross_us_sales_domestic",
    2: "tic.flow_gross_us_purchases_domestic",
    3: "tic.flow_net_domestic",
    4: "tic.flow_private_net_domestic",
    5: "tic.flow_private_treasuries",
    6: "tic.flow_private_agency",
    7: "tic.flow_private_corporate",
    8: "tic.flow_private_equity",
    9: "tic.flow_official_net_domestic",
    10: "tic.flow_official_treasuries",
    11: "tic.flow_official_agency",
    12: "tic.flow_official_corporate",
    13: "tic.flow_official_equity",
    14: "tic.flow_gross_us_sales_foreign",
    15: "tic.flow_gross_us_purchases_foreign",
    16: "tic.flow_net_foreign",
    17: "tic.flow_net_foreign_bonds",
    18: "tic.flow_net_foreign_equity",
    19: "tic.flow_net_lt_securities",
    20: "tic.flow_other_acquisitions",
    21: "tic.flow_net_lt_acquisitions",
    22: "tic.flow_bills_other_custody",
    23: "tic.flow_bills_total",
    24: "tic.flow_bills_private",
    25: "tic.flow_bills_official",
    26: "tic.flow_other_negotiable_total",
    27: "tic.flow_other_negotiable_private",
    28: "tic.flow_other_negotiable_official",
    29: "tic.flow_banks_own_dollar_liabilities",
    30: "tic.flow_total",
    31: "tic.flow_total_private",
    32: "tic.flow_total_official",
}
FLOW_KEYS = list(FLOW_LINES.values())


def flow_rows(text: str, available_at: str, kind: str) -> list[dict]:
    """Rows from npr_history.txt. Raises if the column-number row is missing."""
    lines = [ln.rstrip("\r\n").split("\t") for ln in text.splitlines()]
    numrow = next((i for i, c in enumerate(lines)
                   if [x.strip() for x in c[1:33]] == [str(n) for n in range(1, 33)]),
                  None)
    if numrow is None:
        raise ValueError("npr_history.txt: no '1..32' column-number row -- the "
                         "table layout changed")
    out: list[dict] = []
    for cells in lines[numrow + 1:]:
        m = re.fullmatch(r"(\d{4})-([A-Z][a-z]{2})", cells[0].strip()) if cells else None
        if not m or m.group(2) not in MONTHS:
            continue
        day = month_end(int(m.group(1)), MONTHS[m.group(2)])
        for n, key in FLOW_LINES.items():
            v = _num(cells[n]) if n < len(cells) else None
            if v is not None:
                out.append({"registry_key": key, "instrument": None,
                            "observed_at": day, "available_at": available_at,
                            "value": v * MILLIONS, "availability_kind": kind})
    return out


KEYS = list(HOLDINGS_KEYS) + FLOW_KEYS


def _produce() -> list[dict]:
    rows: list[dict] = []
    for url in (URL_HISTORY, URL_CURRENT):
        data, headers = http_get_response(url, timeout=90)
        available_at, kind = pub.availability(headers)
        rows.extend(holdings_rows(data.decode("utf-8", errors="replace"),
                                  available_at, kind,
                                  current_table=(url == URL_CURRENT)))
    data, headers = http_get_response(FLOWS_URL, timeout=90)
    rows.extend(flow_rows(data.decode("utf-8", errors="replace"),
                          *pub.availability(headers)))
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db,
                   window_days=WINDOW_DAYS)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
