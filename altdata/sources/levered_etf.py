"""
Levered- and inverse-ETF assets from the issuers' own pages and files (signal-
triage Batch 22 item 116, the order's 98.1; A127, 6 Nov 2026).

    python -m altdata.sources.levered_etf            # one pull, summary to stdout
    python -m altdata.sources.levered_etf --dry-run  # read, parse, print; write nothing

THE ONE KEY, EXTENDED, NOT DUPLICATED. levetf.aum is the existing key item 71's
fragility panel reads, written for ProShares' funds by altdata/sources/proshares.py
from the issuer's NAV history files. This writer fills the SAME key for the
roster's other issuers (config/levered_etf.yaml, `writer: levered_etf`), one row
per fund, instrument = the ticker, source `levered_etf:<issuer>`. ProShares'
funds stay on their writer, which the roster extends (USD, ROM).

HOW EACH ISSUER IS READ (V-98b, checked 6 Nov 2026), ONE REQUEST PER PAGE OR FILE:
  direxion_holdings  www.direxion.com/holdings/<T>.csv, keyless. HoldingsPercent
                     is each line's share of net assets, so net assets =
                     MarketValue x 100 / HoldingsPercent: the median over the lines
                     of 1% or more, which must agree within 0.1% or the fund is
                     refused. The file dated D carries D's previous session's
                     closing prices, so the row is observed at that session.
  granite_holdings   the fund page (graniteshares.com), whose link names the dated
                     holdings workbook; then the workbook: Shares Outstanding x
                     NAV/Share, observed at the session before its Position Date.
                     The page's own AUM comes from a signed endpoint, a key in
                     effect, which is never called. Two requests a fund.
  rex_page           www.rexshares.com/<t>/: "As of MM/DD/YYYY ... Fund Assets $n",
                     observed at the As-of date. The host's Crawl-delay (10 s) is
                     honoured between its requests.
  gap                no keyless reading (Tradr's pages fill AUM in the browser; the
                     aggregator checked forbids automated access): never
                     requested, named in the summary.

ROBOTS.TXT IS READ AT EVERY PULL, once per host per pull, through the wildcard-
aware reader (aaii.robots_verdict); 401/403/404/410 means no rules (RFC 9309); a
disallow is a refusal for that fund, never a retry. Every request carries the
generic project User-Agent (_base). A fund that fails is named with its reason and
the pull goes on; the pull is STALE only when no fund parsed.

AVAILABILITY. The pull instant (`observed`): the issuers republish in place and
state no publication time.

THE BLOCKLIST. Every ticker is checked against register/instruments.py before any
request, failing closed: a restricted name, or a blocklist that will not load, is
never requested or stored.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import logging
import re
import statistics
import time
from pathlib import Path
from typing import Callable, Optional

import yaml

from .. import session
from . import _publication as pub
from ._base import FetchError, http_get_response, http_get_text

log = logging.getLogger(__name__)

SOURCE = "levered_etf"
KEYS = ["levetf.aum"]
CONFIG = Path(__file__).resolve().parent.parent.parent / "config" / "levered_etf.yaml"
METHODS = ("direxion_holdings", "granite_holdings", "rex_page")
AGREE_TOL = 0.001            # Direxion's lines must agree within 0.1%


class Restricted(RuntimeError):
    """A roster ticker the blocklist names, or a blocklist that will not load."""


def config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8")) or {}


def assert_unrestricted(tickers, is_restricted: Optional[Callable[[str], bool]] = None
                        ) -> None:
    """Raise Restricted if any ticker is on the Brookfield blocklist. Fails CLOSED:
    a blocklist that cannot load refuses every ticker."""
    if is_restricted is None:
        try:
            from register import instruments                    # noqa: PLC0415
            is_restricted = instruments.restrictions().is_restricted
        except Exception as exc:                                # noqa: BLE001
            raise Restricted(f"the blocklist did not load ({exc}); nothing requested") \
                from exc
    bad = [t for t in tickers if is_restricted(t)]
    if bad:
        raise Restricted(f"restricted (the Brookfield complex): {bad}")


def own_funds(cfg: Optional[dict] = None) -> list[dict]:
    """The roster's funds this writer reads (gaps included, to be named)."""
    return [f for f in (cfg or config()).get("funds") or []
            if f.get("writer") == SOURCE]


# ---------------------------------------------------------------------------
# Parsers (pure; the gate drives them on fixtures)
# ---------------------------------------------------------------------------
def _num(s: str) -> float:
    return float(str(s).replace(",", "").replace("$", "").strip())


def _prev_session(day: dt.date) -> str:
    return session.previous_trading_session(day).isoformat()


def parse_direxion(text: str, ticker: str) -> tuple[str, float]:
    """(observed session, net assets) from a Direxion holdings file."""
    lines = text.lstrip("﻿").splitlines()
    try:
        i = next(k for k, ln in enumerate(lines) if ln.startswith('"TradeDate"'))
    except StopIteration as exc:
        raise ValueError(f"{ticker}: no holdings header in the file") from exc
    implied, trade = [], None
    for rec in csv.DictReader(lines[i:]):
        try:
            mv, pc = _num(rec["MarketValue"]), _num(rec["HoldingsPercent"])
        except (KeyError, ValueError, TypeError):
            continue
        trade = trade or (rec.get("TradeDate") or "").split()[0]
        if abs(pc) >= 1.0:
            implied.append(mv * 100.0 / pc)
    if not implied or not trade:
        raise ValueError(f"{ticker}: no line of 1% or more to imply net assets from")
    med = statistics.median(implied)
    if med <= 0 or max(abs(v / med - 1.0) for v in implied) > AGREE_TOL:
        raise ValueError(f"{ticker}: the lines' implied net assets disagree by more "
                         f"than {AGREE_TOL:.1%}")
    day = dt.datetime.strptime(trade, "%m/%d/%Y").date()
    return _prev_session(day), med


def granite_link(page_html: str, ticker: str) -> str:
    m = re.search(r"/media/[A-Za-z0-9]+/" + re.escape(ticker.lower())
                  + r"_holdings_file_\d{8}\.xlsx?", page_html)
    if not m:
        raise ValueError(f"{ticker}: the page links no holdings workbook")
    return "https://graniteshares.com" + m.group(0)


def parse_granite(rows: list[dict], ticker: str) -> tuple[str, float]:
    """(observed session, AUM) from the workbook's rows (header-keyed dicts)."""
    for r in rows:
        try:
            so, nav = _num(r["Shares Outstanding"]), _num(r["NAV/Share"])
            pos = r["Position Date"]
        except (KeyError, ValueError, TypeError):
            continue
        if so > 0 and nav > 0:
            day = (pos.date() if hasattr(pos, "date") else
                   dt.date.fromisoformat(str(pos)[:10]))
            return _prev_session(day), so * nav
    raise ValueError(f"{ticker}: no row carries shares outstanding and NAV/Share")


def granite_rows(data: bytes) -> list[dict]:
    import pandas as pd                                         # noqa: PLC0415
    df = pd.read_excel(io.BytesIO(data))
    return df.to_dict("records")


def parse_rex(page_html: str, ticker: str) -> tuple[str, float]:
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", page_html))
    m = re.search(r"As of (\d{2}/\d{2}/\d{4}) NAV \$[\d,.]+ .{0,400}?Fund Assets "
                  r"\$([\d,.]+)", text)
    if not m:
        raise ValueError(f"{ticker}: no 'As of ... Fund Assets' on the page")
    day = dt.datetime.strptime(m.group(1), "%m/%d/%Y").date().isoformat()
    return day, _num(m.group(2))


# ---------------------------------------------------------------------------
# The pull
# ---------------------------------------------------------------------------
class _Robots:
    """robots.txt read once per host per pull; verdicts per URL; Crawl-delay."""

    def __init__(self, get_text: Callable[[str], str]) -> None:
        self.get_text = get_text
        self.texts: dict[str, Optional[str]] = {}
        self.last: dict[str, float] = {}

    @staticmethod
    def host(url: str) -> str:
        return re.match(r"(https?://[^/]+)", url).group(1)

    def _text(self, host: str) -> Optional[str]:
        if host not in self.texts:
            try:
                self.texts[host] = self.get_text(host + "/robots.txt")
            except FetchError as exc:
                if re.match(r"HTTP 4(01|03|04|10)\b", str(exc)):
                    self.texts[host] = None        # no rules (RFC 9309 2.3.1.3)
                else:
                    raise
        return self.texts[host]

    def check(self, url: str) -> None:
        from .aaii import robots_verdict                        # noqa: PLC0415
        text = self._text(self.host(url))
        if text is None:
            return
        allowed, rule = robots_verdict(text, url)
        if not allowed:
            raise PermissionError(f"robots.txt disallows {url} ({rule}); not requested")

    def delay(self, url: str) -> float:
        text = self._text(self.host(url)) or ""
        m = re.search(r"(?im)^\s*crawl-delay\s*:\s*([\d.]+)", text)
        return float(m.group(1)) if m else 0.0


def read_fund(f: dict, robots: _Robots, get: Callable[..., tuple],
              sleep: Callable[[float], None] = time.sleep) -> tuple[str, float]:
    """(observed session, AUM) for one fund, or raise with the reason."""
    method = f.get("method")
    if method not in METHODS:
        raise ValueError(f"no keyless reading ({f.get('gap') or method})")

    def fetch(url: str) -> bytes:
        robots.check(url)
        h = robots.host(url)
        wait = robots.delay(url) - (time.monotonic() - robots.last.get(h, -1e9))
        if wait > 0:
            sleep(wait)
        robots.last[h] = time.monotonic()
        data, _ = get(url, timeout=60, max_retries=1)
        return data

    t = f["ticker"]
    if method == "direxion_holdings":
        return parse_direxion(fetch(f["aum_page"]).decode("utf-8", "replace"), t)
    page = fetch(f["aum_page"]).decode("utf-8", "replace")
    if method == "rex_page":
        return parse_rex(page, t)
    return parse_granite(granite_rows(fetch(granite_link(page, t))), t)


def produce(cfg: Optional[dict] = None, get: Optional[Callable[..., tuple]] = None,
            get_text: Optional[Callable[[str], str]] = None,
            now: Optional[str] = None, sleep: Callable[[float], None] = time.sleep,
            is_restricted: Optional[Callable[[str], bool]] = None
            ) -> tuple[list[dict], dict[str, str]]:
    """(rows, {ticker: why not read}). Raises Restricted before any request."""
    funds = own_funds(cfg)
    assert_unrestricted([f["ticker"] for f in funds], is_restricted)
    robots = _Robots(get_text or (lambda u: http_get_text(u, timeout=30)))
    get = get or http_get_response
    at = now or session.utc_iso()
    rows, missed = [], {}
    for f in funds:
        try:
            day, aum = read_fund(f, robots, get, sleep)
        except Exception as exc:                                # noqa: BLE001
            missed[f["ticker"]] = f"{type(exc).__name__}: {exc}"[:200]
            log.warning("levered_etf: %s not read -- %s", f["ticker"], missed[f["ticker"]])
            continue
        rows.append({"registry_key": "levetf.aum", "instrument": f["ticker"],
                     "observed_at": day, "available_at": at, "value": aum,
                     "availability_kind": "observed",
                     "source": f"{SOURCE}:{str(f['issuer']).lower()}"})
    return rows, missed


def pull(run_id: Optional[str] = None, db=None) -> dict:
    missed: dict[str, str] = {}

    def _produce() -> list[dict]:
        rows, m = produce()
        missed.update(m)
        return rows

    out = pub.run(SOURCE, KEYS, _produce, run_id=run_id, db=db)
    out["not_read"] = missed
    return out


def _main(argv=None) -> int:
    import argparse                                             # noqa: PLC0415
    import json                                                 # noqa: PLC0415
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dry-run", action="store_true",
                    help="read and parse every page; write nothing")
    a = ap.parse_args(argv)
    if a.dry_run:
        rows, missed = produce()
        print(json.dumps({"rows": rows, "not_read": missed}, indent=2, default=str))
        return 0 if rows else 1
    out = pull()
    print(json.dumps(out, indent=2, sort_keys=True, default=str))
    return 0 if out.get("status") == pub.OK else 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    raise SystemExit(_main())
