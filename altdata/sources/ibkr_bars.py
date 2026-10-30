"""
The IBKR daily-bars writer: tranche 1 of the price-source migration (A93; the
brief docs/briefs/price-source-migration-brief-2026-10-25.md, ruled D38 on
26 Oct 2026). Built and SWITCHED OFF.

    python -m altdata.sources.ibkr_bars            # the routine pull (when enabled)
    python -m altdata.sources.ibkr_bars backfill   # five years, RECONSTRUCTED
    python -m altdata.sources.ibkr_bars plan       # what it would request; no request

Historical daily bars through the running IB Gateway, under NEW keys,
ibkr.<stem>_<field> (yfinance.mkt_spy -> ibkr.spy_close), never over yfinance's.
The cutover is the brief's section 4: twenty sessions in parallel beside the
yfinance pull, a cross-source pair per key (config/data_quality.yaml's
inactive_pairs until then), then the readers move family by family.

THE RULES IT HOLDS:
- OFF UNTIL ENABLED. config/ibkr_bars.yaml's `enabled: false` means no
  connection, no request, no row, and the feed run does not call it.
- CONTRACTS THROUGH THE SECURITY MASTER. Each instrument resolves by its Yahoo
  symbol to its entry, and the request names that entry's `ibkr_conid`. An
  instrument without one is skipped and named; a conid is never guessed.
- PACING IN CODE. At most 60 historical requests in any ten minutes (IBKR's
  limit, the brief's section 2a), held by `Pacer`, one request per contract per run.
- THE POINT-IN-TIME RULE. A daily bar is knowable at its session's close plus
  the declared delay: a live row is stamped no earlier than that and no earlier
  than its pull; a backfill row is stamped close + delay and marked
  RECONSTRUCTED, as tools/backfill_prices.py does.
- STALE, NEVER EMPTY. No gateway, no answer, or no subscription is a STALE with
  its reason ("market data subscription not present" when the gateway says so).
- READ-ONLY. The connection is the shared client's (`ibkr_portfolio.connect`,
  readonly=True, the paper port; the live port refused), on its own client id.
  Nothing here can place an order.
"""

from __future__ import annotations

import datetime as dt
import logging
import sys
import time
from collections import deque
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Optional

import yaml

from .. import observations, session
from ..ibkr_clients import CLIENT_IDS
from . import _publication as pub

log = logging.getLogger(__name__)

SOURCE = "ibkr_bars"
CONFIG = Path(__file__).resolve().parent.parent.parent / "config" / "ibkr_bars.yaml"
CLOSE_HOUR_ET = 16
NO_SUBSCRIPTION = "market data subscription not present"
# The gateway's words for a missing entitlement: error 354 ("Requested market
# data is not subscribed"), 162 with "No market data permissions", 10090, 10167.
_NO_SUB_CODES = {354, 10090, 10167}
_NO_SUB_WORDS = ("not subscribed", "no market data permissions", "market data subscription")


def config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8")) or {}


def enabled(cfg: Optional[dict] = None) -> bool:
    return bool((cfg or config()).get("enabled"))


def stem(symbol: str) -> str:
    """The key stem: the yfinance key's (mkt_spy -> spy), so the two sources'
    keys pair by name; a symbol the basket does not carry is named plainly."""
    from . import yfinance_source as yf                          # noqa: PLC0415
    k = yf.SYMBOLS.get(symbol)
    if k:
        return k[4:] if k.startswith("mkt_") else k
    return "".join(c for c in symbol.lower() if c.isalnum())


def instruments(cfg: Optional[dict] = None, every: bool = False) -> list[dict]:
    """The included families' instruments (all declared ones with `every`)."""
    c = cfg or config()
    out = []
    for fam, f in (c.get("families") or {}).items():
        if not (every or f.get("include")):
            continue
        for sym in f.get("symbols") or []:
            out.append({"family": fam, "symbol": sym, "stem": stem(sym),
                        "availability": f.get("availability") or "ny_close",
                        "what_to_show": f.get("what_to_show") or "TRADES"})
    return out


def keys_for(insts: list[dict], fields: list[str]) -> list[str]:
    return [f"ibkr.{i['stem']}_{f}" for i in insts for f in fields]


_CFG = config()
FIELDS: list[str] = list(_CFG.get("fields") or ["open", "high", "low", "close"])
KEYS: list[str] = keys_for(instruments(_CFG), FIELDS)
# Every declared family's keys, so the registry knows the next tranche's names.
DECLARED_KEYS: list[str] = keys_for(instruments(_CFG, every=True), FIELDS)


# ---------------------------------------------------------------------------
# Pacing
# ---------------------------------------------------------------------------
class Pacer:
    """At most `max_requests` in any `window_seconds`: `wait()` blocks until a
    slot is free, then records the request. The clock and the sleep are
    injected so the gate proves the limit without waiting ten minutes."""

    def __init__(self, max_requests: int = 60, window_seconds: float = 600.0,
                 clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self.max, self.window = int(max_requests), float(window_seconds)
        self.clock, self.sleep = clock, sleep
        self.sent: deque[float] = deque()

    def wait(self) -> float:
        """Block until a request may go; returns the seconds waited."""
        waited = 0.0
        while True:
            now = self.clock()
            while self.sent and now - self.sent[0] >= self.window:
                self.sent.popleft()
            if len(self.sent) < self.max:
                self.sent.append(now)
                return waited
            pause = self.window - (now - self.sent[0]) + 0.01
            self.sleep(pause)
            waited += pause


# ---------------------------------------------------------------------------
# Contracts, availability, rows
# ---------------------------------------------------------------------------
def resolve(inst: dict, master=None, on: Optional[str] = None) -> tuple[Optional[int], str]:
    """(conid, why): the Security Master's ibkr_conid for the instrument's Yahoo
    symbol, or None and the reason. Never guessed; a restricted instrument is
    refused here as at every writer."""
    from .. import security_master as sm                       # noqa: PLC0415
    m = master or sm.Master()
    try:
        e = m.resolve(inst["symbol"], "yahoo", on)
    except sm.NotFound:
        return None, f"{inst['symbol']} is not in the Security Master"
    except sm.Ambiguous as exc:
        return None, f"{inst['symbol']} is ambiguous in the Security Master ({exc})"
    if e.get("restricted"):
        return None, f"{inst['symbol']} is restricted"
    conid = (e.get("identifiers") or {}).get("ibkr_conid")
    if conid in (None, ""):
        return None, f"{inst['symbol']} ({e.get('id')}) has no ibkr_conid in the Security Master"
    try:
        return int(conid), f"{e.get('id')}"
    except (TypeError, ValueError):
        return None, f"{inst['symbol']} ({e.get('id')}) has an unreadable ibkr_conid"


def close_instant(day: str, availability: str) -> dt.datetime:
    """When the day's bar is complete: the New York close (16:00 ET, the zone
    resolved per date), or the end of the UTC day for an FX pair."""
    d = dt.date.fromisoformat(str(day)[:10])
    if availability == "utc_day":
        return dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc) + dt.timedelta(days=1)
    tz = session._eastern_tz()                                 # noqa: SLF001
    return dt.datetime(d.year, d.month, d.day, CLOSE_HOUR_ET, 0, tzinfo=tz)


def available_at(day: str, availability: str, delay_minutes: int,
                 pulled_at: Optional[str] = None) -> str:
    """The bar's knowable instant: its close plus the delay, and for a live row
    never earlier than the pull that read it."""
    t = close_instant(day, availability).astimezone(dt.timezone.utc) \
        + dt.timedelta(minutes=int(delay_minutes))
    if pulled_at:
        p = dt.datetime.fromisoformat(pulled_at.replace("Z", "+00:00"))
        t = max(t, p)
    return observations.canonical_instant(t.isoformat())


def _bar_day(b: Any) -> Optional[str]:
    d = getattr(b, "date", None)
    if isinstance(d, dt.datetime):
        return d.date().isoformat()
    if isinstance(d, dt.date):
        return d.isoformat()
    s = str(d or "")
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return s[:10] or None


def rows_from_bars(inst: dict, bars: list, fields: list[str], delay: int,
                   pulled_at: Optional[str], reconstructed: bool) -> list[dict]:
    out = []
    for b in bars or []:
        day = _bar_day(b)
        if not day:
            continue
        av = available_at(day, inst["availability"], delay,
                          None if reconstructed else pulled_at)
        for f in fields:
            v = getattr(b, f, None)
            if v is None or v != v or (f != "volume" and float(v) <= 0):
                continue
            out.append({"registry_key": f"ibkr.{inst['stem']}_{f}", "instrument": None,
                        "observed_at": day, "available_at": av, "value": float(v),
                        "availability_kind": "reconstructed" if reconstructed
                        else "observed"})
    return out


def _contract(conid: int):
    """The request's contract by conid alone (IBKR fills the rest)."""
    try:
        from ib_async import Contract                          # noqa: PLC0415
        return Contract(conId=conid, exchange="SMART")
    except ImportError:
        return SimpleNamespace(conId=conid, exchange="SMART")


class NoSubscription(RuntimeError):
    """The gateway answered that the account holds no entitlement for the data."""


def fetch(cfg: dict, client, master=None, pacer: Optional[Pacer] = None,
          backfill: bool = False, pulled_at: Optional[str] = None
          ) -> tuple[list[dict], list[str]]:
    """(rows, skipped): one historical request per resolved contract, paced.
    Raises NoSubscription when every request the gateway answered was refused
    for want of an entitlement."""
    p = cfg.get("pacing") or {}
    pacer = pacer or Pacer(p.get("max_requests", 60), p.get("window_seconds", 600))
    fields = list(cfg.get("fields") or FIELDS)
    delay = int(cfg.get("delay_minutes") or 0)
    dur = (cfg.get("duration") or {}).get("backfill" if backfill else "routine", "10 D")
    errors: list[tuple[int, str]] = []

    def on_error(req_id, code, msg, *_a):
        errors.append((int(code or 0), str(msg or "")))
    try:
        client.errorEvent += on_error
    except (AttributeError, TypeError):
        pass
    rows, skipped, refused, asked = [], [], 0, 0
    for inst in instruments(cfg):
        conid, why = resolve(inst, master)
        if conid is None:
            skipped.append(why)
            continue
        pacer.wait()
        asked += 1
        before = len(errors)
        bars = client.reqHistoricalData(
            _contract(conid), endDateTime="", durationStr=dur,
            barSizeSetting=cfg.get("bar_size", "1 day"),
            whatToShow=inst["what_to_show"], useRTH=bool(cfg.get("use_rth", True)),
            formatDate=1)
        new = errors[before:]
        if not bars and any(c in _NO_SUB_CODES or any(w in m.lower() for w in _NO_SUB_WORDS)
                            for c, m in new):
            refused += 1
            skipped.append(f"{inst['symbol']}: {NO_SUBSCRIPTION}")
            continue
        if not bars:
            skipped.append(f"{inst['symbol']}: no bars served"
                           + (f" ({new[-1][0]}: {new[-1][1]})" if new else ""))
            continue
        rows += rows_from_bars(inst, list(bars), fields, delay, pulled_at, backfill)
    if asked and refused == asked:
        raise NoSubscription(NO_SUBSCRIPTION)
    return rows, skipped


# ---------------------------------------------------------------------------
# The writer step
# ---------------------------------------------------------------------------
def _connect(ib_factory=None):
    from . import ibkr_portfolio as ibkr                       # noqa: PLC0415
    return ibkr.connect(host=ibkr.DEFAULT_HOST, port=ibkr.DEFAULT_PORT,
                        client_id=CLIENT_IDS["bars"], ib_factory=ib_factory)


def pull(run_id: Optional[str] = None, db=None, client=None, master=None,
         pacer: Optional[Pacer] = None, cfg: Optional[dict] = None,
         backfill: bool = False, ib_factory=None) -> dict:
    """The writer step. Disabled: nothing at all. Enabled: rows, or STALE with
    its reason. Never raises."""
    c = cfg or config()
    if not c.get("enabled"):
        return {"status": "DISABLED", "written": 0,
                "reason": f"config/ibkr_bars.yaml enabled: false (since {c.get('disabled_since')})"}
    run_id = run_id or session.new_run_id(SOURCE)
    keys = keys_for(instruments(c), list(c.get("fields") or FIELDS))
    own = client is None
    try:
        client = client or _connect(ib_factory)
    except Exception as exc:                                    # noqa: BLE001
        return pub.stale(SOURCE, keys, f"no gateway: {type(exc).__name__}: {exc}",
                         db=db, run_id=run_id)
    skipped: list[str] = []
    try:
        def produce() -> list[dict]:
            rows, sk = fetch(c, client, master, pacer, backfill,
                             pulled_at=session.utc_iso(timespec="seconds"))
            skipped.extend(sk)
            return rows
        try:
            rows = produce()
        except NoSubscription:
            return pub.stale(SOURCE, keys, NO_SUBSCRIPTION, db=db, run_id=run_id)
        except Exception as exc:                                # noqa: BLE001
            return pub.stale(SOURCE, keys, f"{type(exc).__name__}: {exc}", db=db,
                             run_id=run_id)
        out = pub.run(SOURCE, keys, lambda: rows, run_id=run_id, db=db,
                      window_days=(366 * 6 if backfill else pub.WRITE_WINDOW_DAYS))
    finally:
        if own:
            try:
                client.disconnect()
            except Exception:                                   # noqa: BLE001
                pass
    if skipped:
        out["skipped"] = skipped
    return out


def plan(cfg: Optional[dict] = None, master=None) -> list[str]:
    """What a pull would request, resolved; no connection, no request."""
    c = cfg or config()
    lines = [f"enabled: {bool(c.get('enabled'))}"]
    for inst in instruments(c):
        conid, why = resolve(inst, master)
        lines.append(f"  {inst['family']:18} {inst['symbol']:8} -> "
                     f"{'conid ' + str(conid) if conid else 'SKIP: ' + why}; keys "
                     f"ibkr.{inst['stem']}_{{{','.join(c.get('fields') or FIELDS)}}}")
    return lines


def _main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    cmd = argv[0] if argv else "pull"
    if cmd == "plan":
        print("\n".join(plan()))
        return 0
    r = pull(backfill=(cmd == "backfill"))
    print({k: v for k, v in r.items() if k != "rows"})
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
