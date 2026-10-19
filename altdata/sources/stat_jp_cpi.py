"""
Statistics Bureau of Japan -- the national CPI, change on a year earlier, from
the Bureau's own keyless CSV files.

    python -m altdata.sources.stat_jp_cpi    # one pull

ST-R5 fixes (16 Oct 2026; Batch 6 item 39's gap, needs-you 5 of the t1-rest
notes): FRED's OECD CPI for Japan stopped at June 2021, so the real-yield panel's
Japan row and the US-JP real differential were gaps. Read by
altdata/st_r5_t1_rest.py's real_yields() through config/st_r5_t1_rest.yaml.

  jp.cpi_yoy             All items (code 0001), % on a year earlier
  jp.cpi_core_yoy        All items, less fresh food and energy (code 0178), the
                         aggregate closest to the US core (less food and
                         energy); the real differential's core leg
  jp.cpi_less_fresh_yoy  All items, less fresh food (code 0161): the Bank of
                         Japan's "core", printed beside it

SOURCE (checked 16 Oct 2026). https://www.stat.go.jp/data/cpi/<BASE>/csv/
zmi<BASE>aa.csv, one file per index base, linked from /data/cpi/1.html: the
2025 base from January 2025 and the 2020 base from January 2020, both running to
the newest month (August 2026, Last-Modified 17 Sep 2026 23:31 GMT, the release
at 08:30 JST). Shift-JIS, items across, months down; the column is found by its
Group/Item code (row 3), never by position or by name. www.stat.go.jp's
robots.txt disallows only /library/opac/; it is read each run with the
wildcard-aware reader and the fetch stops on a disallow. No key, no e-Stat API
(which needs an application id).

THE CHANGE ON THE YEAR is computed from the published index, within one base
file (a month and the month a year earlier from the same file, so no base is
chained). Where both files hold a month, the newer base decides. Two decimals:
the release's own rate is computed the same way, from the index, and can differ
from this by rounding only.

AVAILABILITY. Each file's Last-Modified (`observed`), else the write instant.
observed_at is the month's first day, as the other monthly CPI keys.
"""

from __future__ import annotations

import csv
import io
import logging
from typing import Optional

from . import _publication as pub
from ._base import http_get_response, http_get_text
from .aaii import robots_verdict

log = logging.getLogger(__name__)

SOURCE = "stat_jp_cpi"
SITE = "https://www.stat.go.jp"
ROBOTS_URL = SITE + "/robots.txt"
BASES = ("2025", "2020")                 # newest first: the newer base decides
CODES = {"0001": "jp.cpi_yoy", "0178": "jp.cpi_core_yoy",
         "0161": "jp.cpi_less_fresh_yoy"}
KEYS = list(CODES.values())
CODE_ROW = "Group/Item code"


def url_of(base: str) -> str:
    return f"{SITE}/data/cpi/{base}/csv/zmi{base}aa.csv"


def parse(data: bytes) -> dict[str, dict[str, float]]:
    """{store key: {YYYY-MM: index}} for the three codes. Refuses a file without
    its code row or any of the codes, rather than half-reading it."""
    rows = list(csv.reader(io.StringIO(data.decode("cp932"))))
    code_row = next((r for r in rows[:10] if r and CODE_ROW in r[0]), None)
    if code_row is None:
        raise ValueError("the CPI file carries no Group/Item code row")
    col = {}
    for code, key in CODES.items():
        if code not in code_row:
            raise ValueError(f"the CPI file has no column for item code {code}")
        col[key] = code_row.index(code)
    out: dict[str, dict[str, float]] = {k: {} for k in KEYS}
    for r in rows:
        if not r or len(r[0]) != 6 or not r[0].isdigit():
            continue
        month = f"{r[0][:4]}-{r[0][4:]}"
        for key, j in col.items():
            v = r[j].strip() if j < len(r) else ""
            if v:
                out[key][month] = float(v)
    if not any(out.values()):
        raise ValueError("the CPI file parsed to no months")
    return out


def yoy(index: dict[str, float]) -> dict[str, float]:
    """{YYYY-MM: % on the same month a year earlier}, within one file."""
    out = {}
    for m, v in index.items():
        prior = index.get(f"{int(m[:4]) - 1}{m[4:]}")
        if prior:
            out[m] = round((v / prior - 1) * 100, 2)
    return out


def rows_from(files: list[tuple[bytes, str, str]]) -> list[dict]:
    """files: (body, available_at, kind), newest base first."""
    taken: dict[tuple[str, str], dict] = {}
    for body, available, kind in files:
        for key, index in parse(body).items():
            for m, v in yoy(index).items():
                taken.setdefault((key, m), {
                    "registry_key": key, "instrument": None, "observed_at": f"{m}-01",
                    "available_at": available, "value": v, "availability_kind": kind})
    return sorted(taken.values(), key=lambda r: (r["registry_key"], r["observed_at"]))


def fetch_rows() -> list[dict]:
    robots = http_get_text(ROBOTS_URL, timeout=30)
    files = []
    for base in BASES:
        url = url_of(base)
        allowed, rule = robots_verdict(robots, url)
        if not allowed:
            raise PermissionError(f"www.stat.go.jp robots.txt disallows {url} ({rule})")
        body, headers = http_get_response(url, timeout=60)
        available, kind = pub.availability(headers)
        files.append((body, available, kind))
    return rows_from(files)


def pull(run_id: Optional[str] = None, db=None) -> dict:
    return pub.run(SOURCE, KEYS, fetch_rows, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
