"""
China State Administration of Foreign Exchange (SAFE) -- reserves, BOP, IIP.

    python -m altdata.sources.safe           # one pull, summary to stdout

Signal-triage order ST-2 (§2.2.3, SR-3 China external position): the official
side of the China panel -- reserves monthly, the balance of payments and the
international investment position quarterly. The panel is rendered later
(Appendix C); ST-2 fetches its inputs.

SOURCE. www.safe.gov.cn, ENGLISH SITE, OVER PLAIN HTTP. https:// timed out at 60s
from both test machines on 26 Sep 2026 while http:// answered in 1-3s, so this
module uses http. Every data file sits at a content-hash URL that changes with
each release, so the writer reads the FIXED article page and follows its link:
  reserves   index http://www.safe.gov.cn/en/ForexReserves/index.html lists one
             article per year, "Official Reserve Assets (YYYY)"; the current and
             previous years are read so that January still has December
  BOP        http://www.safe.gov.cn/en/2019/0329/1496.html, sheet quarterly(USD)
  IIP        http://www.safe.gov.cn/en/2018/0928/1459.html, sheet Quarterly(USD)
All three are .xlsx, read with the stdlib reader. Amounts are 100 MILLION USD
and are stored in DOLLARS (x1e8); gold volume is 万盎司 (ten thousand troy
ounces) and is stored in OUNCES.

STORED:
  monthly, observed_at = month-end (history from January 2021: the first run
  reads every year's article, and the earlier years' articles do not carry an
  .xlsx -- 2020's is a different format -- so they are skipped and logged):
    safe.fx_reserves              "1. 外汇储备 / Foreign currency reserves"
    safe.gold_reserves_usd        "4. 黄金 / Gold", valued
    safe.gold_reserves_oz         the gold volume line beneath it
    safe.official_reserves_total  "合计 / Total"
  quarterly, observed_at = quarter-end:
    safe.bop_current_account, safe.bop_capital_financial,
    safe.bop_financial_ex_reserves, safe.bop_reserve_assets,
    safe.bop_errors_omissions          (net, USD)
    safe.iip_net, safe.iip_assets, safe.iip_liabilities,
    safe.iip_reserve_assets            (positions, USD)

GOTCHAS, each handled: reserve values are TEXT with a trailing non-breaking
space; the reserves header writes months as "2026.01"; the IIP date header mixes
Excel serials, "31/03/2026", "31-12-2011" and "12-31-2013" in one row -- all are
quarter-ends, so a first field over 12 is a day and a second over 12 is a month.

AVAILABILITY. Each file's Last-Modified, `observed`. BOP and IIP are revised in
later releases; revision_policy: revised.
"""

from __future__ import annotations

import datetime as dt
import logging
import re
from typing import Any, Optional
from urllib.parse import urljoin

from .. import session
from . import _publication as pub
from ._base import http_get_response, http_get_text

log = logging.getLogger(__name__)

SOURCE = "safe_china"
HOST = "http://www.safe.gov.cn"
RESERVES_INDEX = HOST + "/en/ForexReserves/index.html"
BOP_PAGE = HOST + "/en/2019/0329/1496.html"
IIP_PAGE = HOST + "/en/2018/0928/1459.html"
HUNDRED_MILLION = 1e8
TEN_THOUSAND = 1e4
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; chester-reports)"}

RESERVE_ROWS = {"safe.fx_reserves": "外汇储备", "safe.gold_reserves_usd": "黄金",
                "safe.official_reserves_total": "合计"}
GOLD_OZ_KEY = "safe.gold_reserves_oz"
BOP_ROWS = {"safe.bop_current_account": "1. Current account",
            "safe.bop_capital_financial": "2. Capital and financial account",
            "safe.bop_financial_ex_reserves":
                "2.2.1 Financial account excluding reserve assets",
            "safe.bop_reserve_assets": "2.2.2 Reserve assets",
            "safe.bop_errors_omissions": "3.Net errors and omissions"}
IIP_ROWS = {"safe.iip_net": "Net International Investment Position",
            "safe.iip_assets": "Assets", "safe.iip_liabilities": "Liabilities",
            "safe.iip_reserve_assets": "5 Reserve assets"}
KEYS = list(RESERVE_ROWS) + [GOLD_OZ_KEY] + list(BOP_ROWS) + list(IIP_ROWS)


def _clean(cell: Any) -> str:
    return re.sub(r"\s+", " ", str(cell or "").replace("\xa0", " ")).strip()


def _amount(cell: Any) -> Optional[float]:
    if isinstance(cell, (int, float)) and not isinstance(cell, bool):
        return float(cell)
    text = _clean(cell).replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def _row(table, label: str, exact: bool = True) -> Optional[list]:
    for r in table:
        lab = _clean(r[0]) if r else ""
        if (lab == label) if exact else (label in lab):
            return r
    return None


# --- reserves --------------------------------------------------------------
def reserve_rows(table: list[list[Any]], available_at: str,
                 kind: str) -> list[dict]:
    hdr = next((i for i, r in enumerate(table)
                if r and _clean(r[0]).startswith("项目")), None)
    if hdr is None:
        raise ValueError("reserves sheet: no '项目 Item' header")
    months: dict[int, str] = {}
    for j, c in enumerate(table[hdr]):
        text = f"{c:.2f}" if isinstance(c, float) else _clean(c)
        m = re.fullmatch(r"(\d{4})\.(\d{2})", text)
        if m:
            months[j] = pub.month_end(int(m.group(1)), int(m.group(2)))
    if not months:
        raise ValueError("reserves sheet: no YYYY.MM month columns")
    out: list[dict] = []

    def add(key, j, v):
        out.append({"registry_key": key, "instrument": None,
                    "observed_at": months[j], "available_at": available_at,
                    "value": v, "availability_kind": kind})
    for key, needle in RESERVE_ROWS.items():
        row = _row(table[hdr:], needle, exact=False)
        if row is None:
            raise ValueError(f"reserves sheet: no row containing {needle!r}")
        for j in months:
            v = _amount(row[j]) if j < len(row) else None
            if v is not None:
                add(key, j, round(v * HUNDRED_MILLION, 2))
        if key == "safe.gold_reserves_usd":
            idx = next(i for i, r in enumerate(table) if r is row)
            for r in table[idx + 1:idx + 4]:
                cells = {j: _clean(r[j]) for j in months if j < len(r)}
                if any("万盎司" in c for c in cells.values()):
                    for j, c in cells.items():
                        m = re.match(r"([\d.]+)万盎司", c)
                        if m:
                            add(GOLD_OZ_KEY, j, float(m.group(1)) * TEN_THOUSAND)
                    break
    return out


# --- quarterly tables --------------------------------------------------------
def _quarter_end(cell: Any) -> Optional[str]:
    if isinstance(cell, float):
        return pub.excel_serial_date(cell)
    text = _clean(cell)
    m = re.fullmatch(r"(\d{4})Q([1-4])", text)
    if m:
        y, q = int(m.group(1)), int(m.group(2))
        return pub.month_end(y, q * 3)
    m = re.fullmatch(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", text)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        day, month = (a, b) if a > 12 or b <= 12 and a > b else (b, a)
        try:
            return dt.date(y, month, day).isoformat()
        except ValueError:
            return None
    return None


def quarterly_rows(table: list[list[Any]], wanted: dict[str, str],
                   available_at: str, kind: str) -> list[dict]:
    hdr = next((i for i, r in enumerate(table) if r and _clean(r[0]) == "Item"),
               None)
    if hdr is None:
        raise ValueError("quarterly sheet: no 'Item' header")
    cols = {j: _quarter_end(c) for j, c in enumerate(table[hdr]) if j}
    cols = {j: d for j, d in cols.items() if d}
    if not cols:
        raise ValueError("quarterly sheet: no dated columns")
    out: list[dict] = []
    for key, label in wanted.items():
        row = _row(table[hdr + 1:], label)
        if row is None:
            raise ValueError(f"quarterly sheet: no row {label!r}")
        for j, day in cols.items():
            v = _amount(row[j]) if j < len(row) else None
            if v is not None:
                out.append({"registry_key": key, "instrument": None,
                            "observed_at": day, "available_at": available_at,
                            "value": round(v * HUNDRED_MILLION, 2),
                            "availability_kind": kind})
    return out


# --- fetch -------------------------------------------------------------------
def _file_on(page: str) -> tuple[bytes, dict]:
    html = http_get_text(page, headers=HEADERS, timeout=60)
    m = re.search(r'href="([^"]+\.xlsx)"', html)
    if not m:
        raise ValueError(f"no .xlsx link on {page}")
    return http_get_response(urljoin(page, m.group(1)), timeout=90,
                             headers=HEADERS)


def _reserve_pages(backfill: bool) -> list[str]:
    """This year's and last year's articles; on the FIRST run, every year listed.

    One article per year (2015 onward on the index), so the backfill is a dozen
    small files once, and every later run reads two.
    """
    html = http_get_text(RESERVES_INDEX, headers=HEADERS, timeout=60)
    year = session.session_date_obj().year
    years = range(2015, year + 1) if backfill else (year - 1, year)
    pages = []
    for y in years:
        m = re.search(r'href="([^"]+\.html)"[^>]*>\s*Official Reserve Assets \('
                      + str(y) + r'\)', html)
        if m:
            pages.append(urljoin(RESERVES_INDEX, m.group(1)))
    if not pages:
        raise ValueError("no 'Official Reserve Assets (YYYY)' article on the index")
    return pages


def _produce(backfill: bool) -> list[dict]:
    rows: list[dict] = []
    pages = _reserve_pages(backfill)
    for i, page in enumerate(pages):
        # THE LATEST YEAR MUST PARSE; AN OLD ONE MAY NOT. Some early articles
        # (2020's, for one) publish a format other than .xlsx. A backfill year
        # that cannot be read is logged and skipped -- losing it costs history,
        # while failing on it would cost the current month too.
        try:
            data, headers = _file_on(page)
            sheet = next(t for t in pub.read_xlsx(data).values() if t)
            rows.extend(reserve_rows(sheet, *pub.availability(headers)))
        except Exception as exc:                              # noqa: BLE001
            if i == len(pages) - 1:
                raise
            log.warning("safe: reserves backfill skipped %s (%s: %s)", page,
                        type(exc).__name__, exc)
    for page, sheet_name, wanted in ((BOP_PAGE, "quarterly(USD)", BOP_ROWS),
                                     (IIP_PAGE, "Quarterly(USD)", IIP_ROWS)):
        data, headers = _file_on(page)
        rows.extend(quarterly_rows(pub.read_xlsx(data)[sheet_name], wanted,
                                   *pub.availability(headers)))
    return rows


def pull(run_id: Optional[str] = None, db=None) -> dict:
    from .. import observations
    own = db is None
    store = db or observations.ObservationStore()
    try:
        backfill = not pub.newest_observed(store, ["safe.fx_reserves"]).get(
            "safe.fx_reserves")
    finally:
        if own:
            store.close()
    return pub.run(SOURCE, KEYS, lambda: _produce(backfill), run_id=run_id,
                   db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
