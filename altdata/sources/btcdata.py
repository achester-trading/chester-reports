"""
bitcoin-data.com (BGeometrics) -- Bitcoin's long- and short-term-holder supply,
the `btcdata.*` family (SR-29; CD-12 of the crypto data-sources order; ruling 2
of 19 Oct 2026, alpha-lab-4).

    python -m altdata.sources.btcdata          # one pull (fetches nothing without the key)
    python -m altdata.sources.btcdata budget   # the requests spent this hour and day

A FREE KEY, READ FROM .env. The API is a free-key service (its terms, last updated
14 Oct 2026: "The BGeometrics Bitcoin Data API is available with a free API key").
The operator registers the key and puts it in .env as BITCOIN_DATA_API_KEY; this
module reads it through altdata.secrets and sends it as `Authorization: Bearer`,
never in a URL, so it never reaches a log. With no key it fetches nothing and the
series prints "not tracked (btcdata.lth_supply_share): no key in .env
(BITCOIN_DATA_API_KEY)".

    btcdata.lth_supply      BTC held by long-term holders (coins last moved more
                            than 155 days ago), /v1/long-term-hodler-supply-btc
    btcdata.sth_supply      BTC held by short-term holders (155 days or less),
                            /v1/short-term-hodler-supply-btc
    btcdata.supply_current  BTC in circulation, /v1/supply-current
    btcdata.lth_supply_share  lth_supply / supply_current x 100, on each day both
                            are stored -- computed here from the two rows just
                            read, never from a vendor's own ratio

POINT IN TIME. Every row's available_at is the pull's instant (ingest_instant):
the history the first pull reads is knowable from that pull, not from the day it
describes, so nothing here pretends to have been known earlier.

THE BUDGET. The terms' free tier is "8 requests per hour · 15 requests per day"
(the API's own description says 10 an hour; the stricter figure is the guard's).
`RateGuard` counts every request SENT, before it is sent, in a small state file
(~/.chester/btcdata_requests.json, or $CHESTER_STATE_DIR), over a rolling hour and
a rolling day, and refuses the ninth in an hour and the sixteenth in a day. There
is no retry: a retry is a request. One request per series a day, so a daily run
spends 3 of the 15; the first run reads the free tier's whole history (4 years,
about 1,460 days) in one page per series (size 2,000), so it spends 3 too, more
only if the API pages shorter, and a page the guard refuses waits for the next
run.

ITS SCHEDULE: a step of the crypto basket's daily run (scripts/
run_crypto_basket.sh, chester-crypto-basket.timer, 17:25 ET, which loads .env).
No new timer.

THE TERMS, re-read 19 Oct 2026 and quoted in source_registry.yaml
`bitcoin_data`: no clause forbids storing the data; redistribution to third
parties, by API, feed or download, is forbidden, and nothing here offers any;
publishing derived values is allowed for "personal and non-commercial"
publishing with BGeometrics credited, which every printed line does.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Optional

from .. import secrets
from . import _crypto as C
from . import _publication as pub
from . import user_agent

log = logging.getLogger(__name__)

SOURCE = "bitcoin_data"
KEY_ENV = "BITCOIN_DATA_API_KEY"
BASE = "https://api.bitcoin-data.com"
ENDPOINTS = {"btcdata.lth_supply": "/v1/long-term-hodler-supply-btc",
             "btcdata.sth_supply": "/v1/short-term-hodler-supply-btc",
             "btcdata.supply_current": "/v1/supply-current"}
SHARE = "btcdata.lth_supply_share"
KEYS = [*ENDPOINTS, SHARE]
CREDIT = "BGeometrics (bitcoin-data.com)"
NOT_TRACKED = f"not tracked ({SHARE}): no key in .env ({KEY_ENV})"

# The settings, session-set (config/crypto_sources.yaml `bitcoin_data` overrides).
DEFAULTS = {"per_hour": 8, "per_day": 15, "history_years": 4, "page_size": 2000,
            "margin_days": 7, "max_pages": 3}
META_FIELDS = {"d", "day", "date", "unixts", "unix_ts", "ts", "timestamp", "time", "t",
               "id", "delayed"}


class RateExceeded(RuntimeError):
    """A request the free tier's budget would not allow."""


def settings() -> dict:
    try:
        cfg = C.config().get("bitcoin_data") or {}
    except Exception:                                         # noqa: BLE001
        cfg = {}
    return {**DEFAULTS, **{k: cfg[k] for k in DEFAULTS if k in cfg}}


def state_path() -> Path:
    root = os.environ.get("CHESTER_STATE_DIR") or str(Path.home() / ".chester")
    return Path(root).expanduser() / "btcdata_requests.json"


class RateGuard:
    """Every request sent, over a rolling hour and a rolling day, persisted so a
    second run in the day counts the first's."""

    def __init__(self, path: Optional[Path] = None, per_hour: int = 8, per_day: int = 15,
                 clock: Callable[[], float] = time.time) -> None:
        self.path, self.clock = Path(path or state_path()), clock
        self.per_hour, self.per_day = int(per_hour), int(per_day)
        try:
            self.sent = [float(x) for x in json.loads(self.path.read_text(encoding="utf-8"))]
        except (OSError, ValueError, TypeError):
            self.sent = []

    def counts(self) -> tuple[int, int]:
        now = self.clock()
        return (sum(1 for t in self.sent if now - t < 3600),
                sum(1 for t in self.sent if now - t < 86400))

    def charge(self) -> None:
        """Count one request, or refuse it. Called BEFORE the request is sent."""
        now = self.clock()
        self.sent = [t for t in self.sent if now - t < 86400]
        hour, day = self.counts()
        if day + 1 > self.per_day:
            raise RateExceeded(f"bitcoin-data.com: a request would make {day + 1} in a "
                               f"day; the free tier allows {self.per_day}")
        if hour + 1 > self.per_hour:
            raise RateExceeded(f"bitcoin-data.com: a request would make {hour + 1} in an "
                               f"hour; the free tier allows {self.per_hour}")
        self.sent.append(now)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".part")
        tmp.write_text(json.dumps(self.sent), encoding="utf-8")
        os.replace(tmp, self.path)


def _http(url: str, params: dict, key: str) -> Any:
    """ONE GET, no retry (a retry is a request the budget must count)."""
    import requests                                             # noqa: PLC0415
    secrets.remember(key)
    try:
        r = requests.get(url, params=params, timeout=60,
                         headers={"Authorization": f"Bearer {key}",
                                  "User-Agent": user_agent.generic(), "Accept": "application/json"})
    except Exception as exc:                                  # noqa: BLE001
        raise RuntimeError(secrets.redact(f"{type(exc).__name__}: {exc}")) from None
    if r.status_code != 200:
        raise RuntimeError(secrets.redact(f"HTTP {r.status_code} from {url}: "
                                          f"{r.text[:160]}"))
    return r.json()


def items_of(doc: Any) -> list[dict]:
    """The rows of a response: a list, or a page object's list."""
    if isinstance(doc, list):
        return [x for x in doc if isinstance(x, dict)]
    if isinstance(doc, dict):
        for k in ("content", "data", "items", "results"):
            if isinstance(doc.get(k), list):
                return [x for x in doc[k] if isinstance(x, dict)]
        if any(k in doc for k in ("d", "day", "date")):
            return [doc]
    raise ValueError(f"bitcoin-data.com: an unrecognised response ({type(doc).__name__})")


def parse(doc: Any, today: str) -> list[tuple[str, float]]:
    """(UTC day, value) per row. The day is the row's `d` (or day/date); the
    value is its one numeric field that is not a day, a time or an id. A row with
    two such fields is refused rather than guessed."""
    out: dict[str, float] = {}
    for r in items_of(doc):
        day = next((str(r[k])[:10] for k in ("d", "day", "date") if r.get(k)), None)
        if day is None:
            ts = next((r[k] for k in ("unixTs", "unix_ts", "timestamp") if r.get(k)), None)
            day = C.utc_day(ts) if ts is not None else None
        if day is None:
            continue
        vals = [(k, C.num(v)) for k, v in r.items()
                if k.lower() not in META_FIELDS and C.num(v) is not None
                and not isinstance(v, bool)]
        if len(vals) > 1:
            raise ValueError(f"bitcoin-data.com: row {day} has {len(vals)} numeric fields "
                             f"({', '.join(k for k, _ in vals)}); refused, not guessed")
        if vals and day <= today:
            out[day] = vals[0][1]
    return sorted(out.items())


def start_day(since: Optional[str], today: str, cfg: dict) -> str:
    if since:
        return since
    t = dt.date.fromisoformat(today)
    return t.replace(year=t.year - int(cfg["history_years"])).isoformat() \
        if not (t.month == 2 and t.day == 29) else \
        dt.date(t.year - int(cfg["history_years"]), 2, 28).isoformat()


def collect(get: Callable[[str, dict], Any], guard: RateGuard,
            since: Optional[dict] = None, today: Optional[str] = None,
            now: Optional[str] = None, cfg: Optional[dict] = None) -> tuple[list[dict], list[str]]:
    """Rows for every series, and the notes of what was not read (a refused
    request waits for the next run)."""
    cfg = cfg or settings()
    today = today or C.today_utc()
    now = now or C.now_iso()
    since = since or {}
    got: dict[str, dict[str, float]] = {}
    notes: list[str] = []
    for k, path in ENDPOINTS.items():
        params = {"startday": start_day(since.get(k), today, cfg), "endday": today,
                  "size": int(cfg["page_size"]), "page": 0}
        pts: dict[str, float] = {}
        for page in range(int(cfg["max_pages"])):
            params["page"] = page
            try:
                guard.charge()
            except RateExceeded as exc:
                notes.append(f"{k}: {exc}; the rest waits for the next run")
                break
            doc = get(BASE + path, dict(params))
            rows = items_of(doc)
            pts.update(dict(parse(doc, today)))
            if len(rows) < int(cfg["page_size"]):
                break
        got[k] = pts
    out = [C.row(k, d, v, now, SOURCE) for k, pts in got.items() for d, v in sorted(pts.items())]
    lth, cur = got.get("btcdata.lth_supply") or {}, got.get("btcdata.supply_current") or {}
    for d in sorted(set(lth) & set(cur)):
        if cur[d]:
            out.append(C.row(SHARE, d, round(100.0 * lth[d] / cur[d], 6), now, SOURCE))
    return out, notes


def pull(run_id: Optional[str] = None, db=None, get=None, guard: Optional[RateGuard] = None,
         **kw) -> dict:
    """One pull. Without the key, nothing is fetched and the summary says so."""
    key = secrets.get(KEY_ENV)
    if not key or key.strip().lower() in secrets.PLACEHOLDERS:
        log.info("%s: %s -- nothing fetched", SOURCE, NOT_TRACKED)
        return {"source": SOURCE, "status": "NOT_TRACKED", "reason": NOT_TRACKED,
                "written": 0, "run_id": run_id, "requests": 0}
    cfg = settings()
    guard = guard or RateGuard(per_hour=cfg["per_hour"], per_day=cfg["per_day"])
    get = get or (lambda url, params: _http(url, params, key))
    margin = int(cfg["margin_days"])
    since = {k: pub.since([k], margin, db=db) for k in ENDPOINTS}
    notes: list[str] = []

    def produce() -> list[dict]:
        rows, n = collect(get=get, guard=guard, since=since, cfg=cfg, **kw)
        notes.extend(n)
        return rows
    out = pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db)
    out["requests_today"] = guard.counts()[1]
    out["notes"] = notes
    out["credit"] = CREDIT
    return out


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if sys.argv[1:] == ["budget"]:
        c = settings()
        g = RateGuard(per_hour=c["per_hour"], per_day=c["per_day"])
        h, d = g.counts()
        print(f"bitcoin-data.com requests: {h} of {c['per_hour']} this hour, "
              f"{d} of {c['per_day']} today; key {'present' if secrets.present(KEY_ENV) else 'absent'}")
        sys.exit(0)
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
