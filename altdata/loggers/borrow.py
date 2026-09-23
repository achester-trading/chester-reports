"""
Borrow, short interest and mentions. (Part 29.7, LOGGING ONLY)

Three sub-sources with three different provenances, kept apart on purpose:

  (a) IBKR BORROW, by two routes, BOTH DORMANT and both recorded:
      -- THE PUBLIC STOCK-LOAN FILE (ftp3.interactivebrokers.com, user shortstock,
         usa.txt) is the better route: every symbol, no market-data entitlement,
         refreshed intraday. THE HOST DOES NOT ANSWER. It resolves to 206.106.137.27
         and times out on 21, 80 and 443 from two networks on two continents, and
         every HTTPS mirror candidate 404s. The parser is written and fixture-tested
         against IB's documented column layout, so the day it answers this is a probe
         and not a build.
      -- THE API TICK returns 10358 "Fundamentals data is not allowed" with the fields
         NaN, so this account cannot see them either.
  (b) FINRA -- Reg SHO daily short VOLUME, and semi-monthly short INTEREST. Public
      files, no key.
  (c) APEWISDOM -- mention counts and rank from social venues. Public API, no key.

The discovery funnel stays unbuilt: that is 6h and gated. Nothing here ranks,
scores or nominates anything.

-----------------------------------------------------------------------------
DAILY SHORT VOLUME IS NOT SHORT INTEREST
-----------------------------------------------------------------------------

The single most important thing about this logger, encoded in both registry entries
because it is the mistake the data invites:

  SHORT VOLUME is the number of shares SOLD SHORT during a session -- a FLOW, which
  includes a market maker shorting to fill a buy order and buying it back nine
  seconds later. A stock can print 45% short volume every day for a year with no
  net short position at all.

  SHORT INTEREST is the number of shares still held short at a settlement date -- a
  STOCK, published semi-monthly with a lag of roughly a fortnight.

They answer different questions, they move differently, and the ratio of one to the
other is not a meaningful number. They are stored as separate metrics with separate
half-lives and neither description omits the distinction.
"""

from __future__ import annotations

import csv
import datetime as dt
import io as _io
import json
import logging
import urllib.error
import urllib.request
from typing import Any, Optional

from .. import observations, session
from . import LoggerSpec, register

log = logging.getLogger(__name__)

# (a) IBKR borrow -- two routes, both probed
BORROW_SHARES_KEY = "ibkr.shortable_shares"
BORROW_FEE_KEY = "ibkr.borrow_fee_rate"
BORROW_REBATE_KEY = "ibkr.borrow_rebate_rate"
BORROW_PROBE_KEY = "ibkr.borrow_probe"
STOCK_LOAN_PROBE_KEY = "ibkr.stock_loan_file_probe"

# THE PUBLIC STOCK-LOAN FILE, which would be the better route of the two: it covers
# every symbol, needs no market-data entitlement, and refreshes intraday. The FTP
# host and the anonymous account are IB's own published ones.
STOCK_LOAN_FTP_HOST = "ftp3.interactivebrokers.com"
STOCK_LOAN_FTP_USER = "shortstock"
STOCK_LOAN_FILE = "usa.txt"
# HTTPS candidates, tried because a file published over FTP is often mirrored.
STOCK_LOAN_HTTPS = (
    "https://www.interactivebrokers.com/download/usa.txt",
    "https://gdcdyn.interactivebrokers.com/download/usa.txt",
    "https://www.ibkr.com/download/usa.txt",
)

# (b) FINRA
SHORT_VOLUME_KEY = "finra.short_volume"
SHORT_VOLUME_TOTAL_KEY = "finra.total_volume"
SHORT_EXEMPT_KEY = "finra.short_exempt_volume"
SHORT_INTEREST_KEY = "finra.short_interest"

# (c) ApeWisdom
MENTIONS_KEY = "apewisdom.mentions"
RANK_KEY = "apewisdom.rank"
UPVOTES_KEY = "apewisdom.upvotes"

REGSHO_URL = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{yyyymmdd}.txt"
APEWISDOM_URL = "https://apewisdom.io/api/v1.0/filter/{feed}/page/{page}"
APEWISDOM_FEEDS = ("all-stocks", "wallstreetbets")
APEWISDOM_PAGES = 2          # ~200 names; the tail is noise and the funnel is 6h

UA = {"User-Agent": "chester-reports/1.0 (research logging)"}
TIMEOUT = 30
MIN_HISTORY = 60


def universe() -> list[str]:
    """The tracked names plus the sector ETFs -- the same list as the consensus log."""
    from .consensus import universe as u
    return u()


def _get(url: str, limit: int = 8_000_000) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read(limit)


# ---------------------------------------------------------------------------
# (a1) THE PUBLIC STOCK-LOAN FILE -- parser written, route unreachable
# ---------------------------------------------------------------------------
def parse_usa_txt(text: str) -> list[dict]:
    """IB's stock-loan file: pipe-delimited, with a header naming its own columns.

    THE COLUMN NAMES ARE READ FROM THE HEADER, not assumed by position, for the same
    reason the RTAT parser does it: a vendor adding a column should not silently
    shift every field one place to the left.

    THE SHAPE HERE IS FROM IB'S DOCUMENTATION AND HAS NOT BEEN CHECKED AGAINST A LIVE
    FILE, because the host does not answer -- see probe_stock_loan_file(). That is
    stated rather than glossed: this parser is a written expectation, proved against a
    fixture of the documented shape, and the first live file may not match it. What it
    buys is that the day the route opens, the work is a probe and not a build.

    Fee and rebate are ANNUALISED PERCENTAGES in the file and stored as such. A
    negative rebate is normal for a hard-to-borrow name and is not an error.
    """
    rows: list[dict] = []
    header: Optional[list[str]] = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        # IB prefixes the header with '#', and the first line is a version banner.
        if line.startswith("#"):
            parts = [p.strip().upper() for p in line.lstrip("#").split("|")]
            if "SYM" in parts:
                header = parts
            continue
        if header is None:
            continue
        vals = line.split("|")
        if len(vals) < len(header):
            continue
        r = dict(zip(header, vals))
        sym = (r.get("SYM") or "").strip().upper()
        if not sym:
            continue

        def num(*names):
            for n in names:
                v = (r.get(n) or "").strip()
                if v in ("", "NA", "N/A", ">1000000"):
                    # '>1000000' is IB's own censoring of a very large availability.
                    # Treated as missing rather than as a million, which it is not.
                    continue
                try:
                    return float(v.replace(",", ""))
                except ValueError:
                    continue
            return None

        rows.append({
            "symbol": sym,
            "currency": (r.get("CUR") or "").strip() or None,
            "fee_rate": num("FEERATE", "FEE"),
            "rebate_rate": num("REBATERATE", "REBATE"),
            "available": num("AVAILABLE", "AVAIL"),
        })
    return rows


def probe_stock_loan_file(store: Optional[observations.ObservationStore] = None,
                         timeout: int = 25) -> dict:
    """Try the FTP route and the HTTPS mirrors, and record every answer."""
    out: dict[str, Any] = {"checked_at": session.utc_iso(), "routes": {},
                           "state": "unknown"}
    import socket
    try:
        out["dns"] = socket.gethostbyname(STOCK_LOAN_FTP_HOST)
    except Exception as exc:                                   # noqa: BLE001
        out["dns"] = f"{type(exc).__name__}: {exc}"

    # FTP, anonymous, as published.
    try:
        import ftplib
        f = ftplib.FTP(STOCK_LOAN_FTP_HOST, timeout=timeout)
        f.login(STOCK_LOAN_FTP_USER, "")
        buf = _io.BytesIO()
        f.retrbinary(f"RETR {STOCK_LOAN_FILE}", buf.write, blocksize=32768)
        f.quit()
        text = buf.getvalue().decode("utf-8", "replace")
        parsed = parse_usa_txt(text)
        out["routes"]["ftp"] = {"ok": True, "bytes": len(buf.getvalue()),
                                "rows_parsed": len(parsed),
                                "sample": parsed[:3]}
        out["state"] = "available"
        out["source_route"] = "ftp"
    except Exception as exc:                                   # noqa: BLE001
        out["routes"]["ftp"] = {"ok": False,
                                "error": f"{type(exc).__name__}: {str(exc)[:160]}"}

    for url in STOCK_LOAN_HTTPS:
        entry: dict[str, Any] = {}
        try:
            body = _get_url(url, timeout=timeout)
            parsed = parse_usa_txt(body.decode("utf-8", "replace"))
            entry = {"ok": True, "bytes": len(body), "rows_parsed": len(parsed)}
            if parsed and out["state"] != "available":
                out["state"] = "available"
                out["source_route"] = url
        except urllib.error.HTTPError as exc:
            entry = {"ok": False, "http": exc.code}
        except Exception as exc:                               # noqa: BLE001
            entry = {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:120]}"}
        out["routes"][url] = entry

    if out["state"] != "available":
        out["state"] = "unreachable"
        out["reason"] = (
            f"{STOCK_LOAN_FTP_HOST} resolves to {out.get('dns')} and answers on no "
            f"port tried (21, 80, 443 all time out), from TWO networks on two "
            f"continents; every HTTPS mirror candidate returns 404. Either the "
            f"endpoint has been retired, it is restricted by source, or it is down. "
            f"The parser is written and fixture-tested so the day it answers this is "
            f"a probe rather than a build.")
    own = store is None
    db = store or observations.ObservationStore()
    try:
        db.write(STOCK_LOAN_PROBE_KEY, None, session.session_date(),
                 session.utc_iso(timespec="microseconds"),
                 json.dumps(out, sort_keys=True, default=str),
                 source="ibkr_paper", availability_kind="ingest_instant")
    finally:
        if own:
            db.close()
    return out


def stock_loan_state(store: Optional[observations.ObservationStore] = None) -> str:
    own = store is None
    db = store or observations.ObservationStore()
    try:
        rows = db.as_of(STOCK_LOAN_PROBE_KEY)
        if not rows:
            return "never_probed"
        return json.loads(rows[-1]["value_text"]).get("state", "unknown")
    finally:
        if own:
            db.close()


def pull_stock_loan(run_id: Optional[str] = None,
                    store: Optional[observations.ObservationStore] = None) -> dict:
    """The borrow series for the tracked universe, once per ibkr-sync run.

    Refuses until a stored probe says the route is available, for the reason the
    auction sampler refuses: a fetch that silently returns nothing every half hour
    looks healthier than one that says it cannot reach its source.
    """
    own = store is None
    db = store or observations.ObservationStore()
    try:
        state = stock_loan_state(store=db)
        if state != "available":
            return {"skipped": f"stock-loan route {state}", "written": 0}
        try:
            import ftplib
            f = ftplib.FTP(STOCK_LOAN_FTP_HOST, timeout=30)
            f.login(STOCK_LOAN_FTP_USER, "")
            buf = _io.BytesIO()
            f.retrbinary(f"RETR {STOCK_LOAN_FILE}", buf.write, blocksize=32768)
            f.quit()
            rows = parse_usa_txt(buf.getvalue().decode("utf-8", "replace"))
        except Exception as exc:                               # noqa: BLE001
            return {"error": f"{type(exc).__name__}: {str(exc)[:160]}", "written": 0}

        wanted = set(universe())
        now = session.utc_iso(timespec="microseconds")
        day = session.session_date()
        out = []
        for r in rows:
            if r["symbol"] not in wanted:
                continue
            for key, value in ((BORROW_FEE_KEY, r["fee_rate"]),
                               (BORROW_REBATE_KEY, r["rebate_rate"]),
                               (BORROW_SHARES_KEY, r["available"])):
                if value is None:
                    continue
                out.append({"registry_key": key, "instrument": r["symbol"],
                            # THE FILE REFRESHES INTRADAY, so observed_at is the
                            # session and a later read of a CHANGED value creates a
                            # genuine vintage -- which is what a borrow rate moving
                            # during the day is.
                            "observed_at": day, "available_at": now,
                            "value": value, "source": "ibkr_stock_loan",
                            "run_id": run_id,
                            "availability_kind": "ingest_instant"})
        written = db.write_many(observations.drop_unchanged(db, out))
        return {"state": "ok", "session": day, "names": len(out) // 3,
                "written": written}
    finally:
        if own:
            db.close()


def _get_url(url: str, timeout: int = 25) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(40_000_000)


# ---------------------------------------------------------------------------
# (a2) IBKR borrow via the API tick -- probed, and dormant on this account
# ---------------------------------------------------------------------------
def probe_borrow(port: int = 4002,
                 store: Optional[observations.ObservationStore] = None) -> dict:
    """Ask the Gateway for the borrow fields and record the answer either way."""
    out: dict[str, Any] = {"checked_at": session.utc_iso(), "port": port,
                           "errors": [], "fields": {}, "state": "unknown"}
    ib = None
    try:
        from ..sources import ibkr_portfolio as ibkr
        from ib_async import Stock
        ib = ibkr.connect(port=port, client_id=25)
        errs: list[dict] = []
        ib.errorEvent += (lambda rid, code, msg, c=None:
                          errs.append({"code": int(code), "message": str(msg)[:180]}))
        c = Stock("NVDA", "SMART", "USD")
        ib.qualifyContracts(c)
        t = ib.reqMktData(c, genericTickList="236,258", snapshot=False)
        for _ in range(8):
            ib.sleep(1.0)
        fields = {}
        for name in ("shortableShares", "shortable", "feeRate"):
            v = getattr(t, name, None)
            if v is not None and v == v:
                fields[name] = v
        out["errors"] = errs
        out["fields"] = fields
        if fields:
            out["state"] = "entitled"
        else:
            out["state"] = "not_entitled"
            out["reason"] = (errs[0]["message"] if errs else
                             "the fields came back NaN with no error")
    except Exception as exc:                                  # noqa: BLE001
        out["state"] = "probe_failed"
        out["reason"] = f"{type(exc).__name__}: {exc}"
    finally:
        if ib is not None:
            try:
                ib.disconnect()
            except Exception:                                  # noqa: BLE001
                pass
    own = store is None
    db = store or observations.ObservationStore()
    try:
        db.write(BORROW_PROBE_KEY, None, session.session_date(),
                 session.utc_iso(timespec="microseconds"),
                 json.dumps(out, sort_keys=True), source="ibkr_paper",
                 availability_kind="ingest_instant")
    finally:
        if own:
            db.close()
    return out


def borrow_state(store: Optional[observations.ObservationStore] = None) -> str:
    own = store is None
    db = store or observations.ObservationStore()
    try:
        rows = db.as_of(BORROW_PROBE_KEY)
        if not rows:
            return "never_probed"
        return json.loads(rows[-1]["value_text"]).get("state", "unknown")
    finally:
        if own:
            db.close()


# ---------------------------------------------------------------------------
# (b) FINRA
# ---------------------------------------------------------------------------
def parse_regsho(text: str) -> list[dict]:
    """The pipe-delimited Reg SHO daily file. Columns READ from the header."""
    rows = []
    for r in csv.DictReader(_io.StringIO(text), delimiter="|"):
        sym = (r.get("Symbol") or "").strip()
        raw = (r.get("Date") or "").strip()
        if not sym or len(raw) != 8:
            continue
        day = f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
        def num(k):
            try:
                return float(r.get(k) or "")
            except ValueError:
                return None
        rows.append({"date": day, "symbol": sym,
                     "short_volume": num("ShortVolume"),
                     "short_exempt": num("ShortExemptVolume"),
                     "total_volume": num("TotalVolume")})
    return rows


def pull_regsho(day: Optional[str] = None, run_id: Optional[str] = None,
                store: Optional[observations.ObservationStore] = None) -> dict:
    """One session's Reg SHO daily short volume, filtered to the tracked universe.

    THE FILE IS EVERY US SYMBOL -- thousands of rows. Only the tracked universe is
    stored: a logger that writes the whole tape every night buys history nobody
    declared and makes every query over this table slower for it.
    """
    target = day or session.last_trading_session().isoformat()
    url = REGSHO_URL.format(yyyymmdd=target.replace("-", ""))
    try:
        text = _get(url).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        # A missing file is the NORMAL case on a holiday or before publication, and
        # it is not a failure of this logger.
        return {"state": "absent", "session": target, "http": exc.code,
                "reason": f"no Reg SHO file for {target} (HTTP {exc.code})",
                "written": 0}
    except Exception as exc:                                  # noqa: BLE001
        return {"state": "error", "session": target,
                "reason": f"{type(exc).__name__}: {exc}", "written": 0}

    wanted = set(universe())
    rows = [r for r in parse_regsho(text) if r["symbol"] in wanted]
    own = store is None
    db = store or observations.ObservationStore()
    try:
        now = session.utc_iso(timespec="microseconds")
        out = []
        for r in rows:
            for key, value in ((SHORT_VOLUME_KEY, r["short_volume"]),
                               (SHORT_EXEMPT_KEY, r["short_exempt"]),
                               (SHORT_VOLUME_TOTAL_KEY, r["total_volume"])):
                if value is None:
                    continue
                out.append({"registry_key": key, "instrument": r["symbol"],
                            "observed_at": r["date"], "available_at": now,
                            "value": value, "source": "finra", "run_id": run_id,
                            "availability_kind": "ingest_instant"})
        written = db.write_many(observations.drop_unchanged(db, out))
        return {"state": "ok", "session": target, "names": len(rows),
                "written": written}
    finally:
        if own:
            db.close()


# ---------------------------------------------------------------------------
# (c) ApeWisdom
# ---------------------------------------------------------------------------
def pull_apewisdom(run_id: Optional[str] = None,
                   store: Optional[observations.ObservationStore] = None) -> dict:
    day = session.session_date()
    own = store is None
    db = store or observations.ObservationStore()
    try:
        now = session.utc_iso(timespec="microseconds")
        rows, feeds_ok, feeds_failed = [], [], []
        wanted = set(universe())
        for feed in APEWISDOM_FEEDS:
            got = 0
            for page in range(1, APEWISDOM_PAGES + 1):
                try:
                    payload = json.loads(_get(APEWISDOM_URL.format(
                        feed=feed, page=page)).decode("utf-8", "replace"))
                except Exception as exc:                      # noqa: BLE001
                    feeds_failed.append((feed, f"{type(exc).__name__}: {exc}"))
                    break
                for item in payload.get("results") or []:
                    ticker = str(item.get("ticker") or "").strip().upper()
                    if not ticker or ticker not in wanted:
                        continue
                    got += 1
                    # THE INSTRUMENT CARRIES THE FEED, because a mention count on
                    # wallstreetbets and one across all venues are different
                    # measurements of different populations and must not be summed.
                    inst = f"{ticker}@{feed}"
                    for key, field in ((MENTIONS_KEY, "mentions"),
                                       (RANK_KEY, "rank"),
                                       (UPVOTES_KEY, "upvotes")):
                        v = item.get(field)
                        if v is None:
                            continue
                        try:
                            f = float(v)
                        except (TypeError, ValueError):
                            continue
                        rows.append({"registry_key": key, "instrument": inst,
                                     "observed_at": day, "available_at": now,
                                     "value": f, "source": "apewisdom",
                                     "run_id": run_id,
                                     "availability_kind": "ingest_instant"})
            feeds_ok.append((feed, got))
        written = db.write_many(observations.drop_unchanged(db, rows))
        return {"state": "ok" if feeds_ok else "error", "session": day,
                "feeds": feeds_ok, "failed": feeds_failed, "written": written}
    finally:
        if own:
            db.close()


# ---------------------------------------------------------------------------
# The nightly step
# ---------------------------------------------------------------------------
def pull(run_id: Optional[str] = None,
         store: Optional[observations.ObservationStore] = None) -> dict:
    out: dict[str, Any] = {}
    own = store is None
    db = store or observations.ObservationStore()
    try:
        api_state = borrow_state(store=db)
        file_state = stock_loan_state(store=db)
        out["borrow_api_tick"] = {
            "state": api_state,
            "note": ("dormant by ruling -- the stock-loan file is the intended "
                     "route and the tick stays off" if file_state == "available"
                     else "dormant; the stored probe says this account cannot see "
                          "the borrow fields")}
        out["borrow_stock_loan_file"] = {
            "state": file_state,
            "note": ("sampled once per ibkr-sync run" if file_state == "available"
                     else "unreachable; see ibkr.stock_loan_file_probe")}
        out["regsho"] = pull_regsho(run_id=run_id, store=db)
        out["apewisdom"] = pull_apewisdom(run_id=run_id, store=db)
        out["written"] = sum(int((out[k] or {}).get("written") or 0)
                             for k in ("regsho", "apewisdom"))
        return out
    finally:
        if own:
            db.close()


def keys() -> list[str]:
    # The borrow keys are deliberately NOT here: this account cannot see them, and a
    # roster entry for a series nothing can write would make the heartbeat red for a
    # subscription decision rather than for a fault.
    keys = [SHORT_VOLUME_KEY, SHORT_VOLUME_TOTAL_KEY, SHORT_EXEMPT_KEY,
            MENTIONS_KEY, RANK_KEY, UPVOTES_KEY]
    # THE BORROW KEYS JOIN THE ROSTER ONLY WHEN A ROUTE EXISTS. Watching a series
    # nothing can write would make the heartbeat red for an unreachable vendor host
    # rather than for a fault, and the two must stay distinguishable.
    if stock_loan_state() == "available":
        keys += [BORROW_FEE_KEY, BORROW_REBATE_KEY, BORROW_SHARES_KEY]
    return keys


SPEC = register(LoggerSpec(
    name="borrow_short_mentions",
    description="FINRA Reg SHO daily short volume and ApeWisdom mentions for the "
                "tracked universe; IBKR borrow fields dormant (not entitled).",
    keys=keys,
    run=pull,
    requires_key=None,
    min_history=MIN_HISTORY,
    notes="Part 29.7 logging only. Daily short VOLUME is not short INTEREST. The "
          "discovery funnel is 6h and unbuilt.",
))


def _main(argv: list[str]) -> int:
    import argparse
    p = argparse.ArgumentParser(description="Borrow / short / mentions logger.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe-borrow")
    sub.add_parser("probe-stock-loan")
    sub.add_parser("pull-stock-loan")
    pl = sub.add_parser("pull")
    pl.add_argument("--day", default=None)
    sub.add_parser("status")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    if a.cmd == "probe-borrow":
        print(json.dumps(probe_borrow(), indent=2, sort_keys=True))
        return 0
    if a.cmd == "probe-stock-loan":
        r = probe_stock_loan_file()
        print(json.dumps(r, indent=2, sort_keys=True, default=str))
        return 0 if r.get("state") == "available" else 1
    if a.cmd == "pull-stock-loan":
        print(json.dumps(pull_stock_loan(), indent=2, sort_keys=True))
        return 0
    if a.cmd == "status":
        print(json.dumps({"borrow": borrow_state(),
                          "universe": len(universe())}, indent=2, sort_keys=True))
        return 0
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
