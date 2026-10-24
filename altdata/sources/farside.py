"""
Farside Investors' spot ETF flow tables -- the `farside.*` family (DS-33; CD-4 of
the crypto data-sources order, D-3 ruled Farside; Batch 4 Tranche A part 2;
crypto-tranche-a-2, 17 Oct 2026). Config: config/crypto_sources.yaml `farside`.

    python -m altdata.sources.farside                      # the recent tables
    python -m altdata.sources.farside backfill [--dry-run] # the all-data pages

THE ONE SCRAPE IN THE ORDER. https://farside.co.uk/btc/ and /eth/ are plain HTML
tables, read with pandas.read_html. The order asks for a browser user-agent; the
one sent still names the project ("compatible; chester-reports/1.0"). robots.txt
names only Twitterbot, so no rule covers this agent (read with the wildcard-aware
reader, altdata/sources/aaii.robots_verdict, before every pull).

THE REFUSAL. On 17 Oct 2026 farside.co.uk answered the laptop 403 through
Cloudflare to both the project's and the browser user-agent. The writer is built;
a refusal is STALE with the last good date and nothing written, and nothing is
scraped around it (no proxy, no archive copy, no headless browser).

    farside.btc_total    the day's net flow across the US spot bitcoin ETFs, USD
                         (the page's US$ millions x 1e6), one row a session
    farside.eth_total    the same for the spot ether ETFs
    farside.btc_issuer   one issuer's net flow, USD; instrument = the ticker
    farside.eth_issuer   the same for ether

READING THE TABLE. The first column is the date ("17 Oct 2026"); a row whose
first cell is not a date -- the fee row, Total, Average, Maximum, Minimum -- is
dropped. "(71.8)" is -71.8; "-" or a blank is no figure (never a zero). THE
COLUMN-CHANGE DETECTOR: the issuer columns must be exactly config's list; a
table with a column added or removed is refused whole (STALE, the change named),
because a renamed fund would otherwise land under the wrong ticker.

observed_at is the session's date; available_at the pull instant.
"""

from __future__ import annotations

import datetime as dt
import io
import logging
import re
from typing import Any, Callable, Optional

from . import _crypto as C
from . import _publication as pub
from ._base import http_get_text

log = logging.getLogger(__name__)

SOURCE = "farside"
KEYS = ["farside.btc_total", "farside.eth_total", "farside.btc_issuer",
        "farside.eth_issuer"]
AGENT = "chester-reports"
DATE_RE = re.compile(r"^\s*(\d{1,2})\s+([A-Za-z]{3})[a-z]*\s+(\d{4})\s*$")


class HeaderChanged(ValueError):
    """The table's issuer columns are not the declared set."""


def _get(url: str) -> str:
    ua = (C.config().get("farside") or {}).get("user_agent")
    return http_get_text(url, timeout=60, headers={"User-Agent": ua} if ua else None)


def robots_ok(get: Optional[Callable[[str], str]] = None) -> tuple[bool, str]:
    from .aaii import robots_verdict                             # noqa: PLC0415
    from ._base import FetchError                                # noqa: PLC0415
    if get is None:
        def get(u: str) -> str:
            try:
                return http_get_text(u, timeout=30)
            except FetchError as exc:
                # A 4xx robots.txt is no rules (RFC 9309 2.3.1.3); anything
                # else is a failed read and the pull stops.
                if "HTTP 4" in str(exc):
                    return ""
                raise
    ok, rule = robots_verdict(get("https://farside.co.uk/robots.txt"), "/btc/", AGENT)
    return ok, ("" if ok else f"robots.txt refuses /btc/ ({rule})")


# ---------------------------------------------------------------------------
# Parse -- pure, on tests/fixtures/farside/
# ---------------------------------------------------------------------------
def _cell(v: Any) -> Optional[float]:
    s = str(v if v is not None else "").strip().replace(",", "")
    if s in ("", "-", "–", "—", "nan", "NaN", "None"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        f = float(s)
    except ValueError:
        return None
    return -f if neg else f


def _date(v: Any) -> Optional[str]:
    m = DATE_RE.match(str(v or ""))
    if not m:
        return None
    try:
        return dt.datetime.strptime(f"{m.group(1)} {m.group(2).title()} {m.group(3)}",
                                    "%d %b %Y").date().isoformat()
    except ValueError:
        return None


def _flat(col: Any) -> str:
    if isinstance(col, tuple):
        parts = [str(c).strip() for c in col if str(c).strip()
                 and not str(c).startswith("Unnamed")]
        return parts[-1] if parts else ""
    return str(col).strip()


def parse_table(html: str, coin: str, expected: list[str]) -> list[dict]:
    """One page -> [{date, total, issuers{ticker: $m}}]. Raises HeaderChanged when
    the issuer columns are not `expected` exactly."""
    import pandas as pd                                          # noqa: PLC0415
    tables = pd.read_html(io.StringIO(html))
    tbl = next((t for t in tables if any(_flat(c).lower() == "total"
                                         for c in t.columns)), None)
    if tbl is None:
        raise ValueError(f"farside {coin}: no table with a Total column")
    cols = [_flat(c) for c in tbl.columns]
    tot = next(i for i, c in enumerate(cols) if c.lower() == "total")
    issuers = [c for i, c in enumerate(cols) if i not in (0, tot) and c]
    if issuers != list(expected):
        added = [c for c in issuers if c not in expected]
        gone = [c for c in expected if c not in issuers]
        raise HeaderChanged(f"farside {coin}: the issuer columns changed (added "
                            f"{added or 'none'}; removed {gone or 'none'}; order "
                            f"{'same' if not added and not gone else 'n/a'}) -- "
                            f"refused whole")
    out = []
    for _, r in tbl.iterrows():
        vals = list(r.values)
        day = _date(vals[0])
        if not day:
            continue
        out.append({"date": day, "total": _cell(vals[tot]),
                    "issuers": {c: _cell(vals[i]) for i, c in enumerate(cols)
                                if c in expected}})
    return out


def rows_from(parsed: list[dict], coin: str, now: str, today: str) -> list[dict]:
    rows = []
    for p in parsed:
        if p["date"] > today:
            continue
        if p["total"] is not None:
            rows.append(C.row(f"farside.{coin}_total", p["date"],
                              round(p["total"] * 1e6, 2), now, SOURCE))
        for tick, v in p["issuers"].items():
            if v is not None:
                rows.append(C.row(f"farside.{coin}_issuer", p["date"],
                                  round(v * 1e6, 2), now, SOURCE, tick))
    return rows


# ---------------------------------------------------------------------------
def collect(get: Callable[[str], str] = _get, *, pages: str = "pages",
            robots: Optional[Callable[[], tuple]] = None,
            today: Optional[str] = None, now: Optional[str] = None
            ) -> tuple[list[dict], dict]:
    cfg = C.config().get("farside") or {}
    today = today or C.today_utc()
    now = now or C.now_iso()
    rows: list[dict] = []
    summary: dict = {"series": {}, "failed": []}
    ok, why = (robots or robots_ok)()
    if not ok:
        summary["failed"].append(("robots", why))
        return rows, summary
    for coin, url in (cfg.get(pages) or {}).items():
        try:
            parsed = parse_table(get(url), coin, (cfg.get("columns") or {})[coin])
            got = rows_from(parsed, coin, now, today)
            rows += got
            days = sorted(p["date"] for p in parsed)
            summary["series"][coin] = {"rows": len(got), "first": days[0] if days else None,
                                       "last": days[-1] if days else None}
        except Exception as exc:                                # noqa: BLE001
            summary["failed"].append((coin, f"{type(exc).__name__}: {exc}"[:300]))
    return rows, summary


def pull(run_id: Optional[str] = None, db=None, **kw) -> dict:
    # REFUSED (the feed repair of 24 Oct 2026): farside.co.uk answers HTTP 403
    # with a Cloudflare challenge; the source registry declares it and nothing is
    # asked. Never worked around.
    r = pub.refused(SOURCE, run_id)
    if r:
        return r
    """STALE-not-empty: any failure (a refusal, a changed header, an empty page)
    writes nothing for that coin and the summary names the last good date."""
    state: dict = {}

    def produce() -> list[dict]:
        rows, s = collect(**kw)
        state.update(s)
        if not rows and s["failed"]:
            raise RuntimeError("; ".join(f"{k}: {v}" for k, v in s["failed"])[:400])
        return rows
    out = pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db)
    out["failed_series"] = state.get("failed") or []
    if out.get("status") == pub.STALE:
        last = {k: v for k, v in (out.get("last_observed") or {}).items() if v}
        out["last_good"] = max(last.values()) if last else None
    return out


def backfill(run_id: Optional[str] = None, db=None, dry_run: bool = False,
             **kw) -> dict:
    """The all-data pages, from the ETFs' first session (Jan 2024), point in time."""
    rows, s = collect(pages="all_data", **kw)
    start = str((C.config().get("farside") or {}).get("backfill_from") or "2024-01-11")
    rows = [r for r in rows if r["observed_at"] >= start]
    if dry_run:
        return {"status": "DRY_RUN", "parsed": len(rows), **s}
    if not rows:
        return pub.stale(SOURCE, KEYS, "; ".join(f"{k}: {v}" for k, v in s["failed"])
                         or "nothing parsed", db=db, run_id=run_id)
    out = pub.write_rows(SOURCE, rows, KEYS, run_id or "farside_backfill", db=db,
                         window_days=100_000)
    return {**out, "failed_series": s["failed"]}


if __name__ == "__main__":
    import json
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if sys.argv[1:2] == ["backfill"]:
        print(json.dumps(backfill(dry_run="--dry-run" in sys.argv), indent=2, default=str))
    else:
        print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
