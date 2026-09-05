"""
Portfolio Truth -- read-only IBKR account state into the observation store.

Architecture 26.11: before any order authority, IBKR is four read-only
services. This is the first of them. Positions, NAV, margin and buying power,
pulled from a local IB Gateway and written point-in-time.

-----------------------------------------------------------------------------
NO ORDER CAPABILITY. NOT DISABLED -- ABSENT.
-----------------------------------------------------------------------------

The architecture's Gate 1 wording is "no order capability in the code at all --
not disabled, not commented out, absent", and this module is written to that
literally. It never imports an order type, never constructs one, and never
calls placeOrder. Two things enforce it rather than assert it:

    * connect() passes readonly=True, so the API session itself rejects order
      submission at the socket. A bug here cannot place a trade.
    * tools/validate_ibkr_portfolio.py greps this module's own source for
      order-placing calls and fails the build if any appear.

The second exists because readonly=True is a runtime argument someone could
later change; the source check is what makes its absence structural.

-----------------------------------------------------------------------------
THE PORT IS THE MODE
-----------------------------------------------------------------------------

    4002  Gateway paper      <- the only port this module defaults to
    4001  Gateway live
    7497  TWS paper
    7496  TWS live

Paper and live differ by port, not by code, which is exactly why a mismatch is
dangerous and silent. `connect()` refuses to run against a LIVE port unless
`allow_live=True` is passed explicitly, and the source tag it writes
(`ibkr_paper` vs `ibkr_live`) is derived FROM the port rather than from a
constant, so a row can never claim to be paper while holding live balances.

-----------------------------------------------------------------------------
ERROR PATHS ARE DISTINCT BECAUSE THE FIXES ARE DIFFERENT
-----------------------------------------------------------------------------

    GatewayNotRunning       nothing is listening on the port. Start Gateway.
    GatewayNotResponding    something is listening but the handshake stalled.
                            Usually the API is not enabled, or the client ID
                            is already in use, or a dialog is blocking it.
    IbkrAuthError           connected, but the session is not logged in --
                            Gateway is up and signed out, which looks healthy
                            from the outside and returns nothing.
    IbkrApiError            anything else after a successful connect.

Collapsing these into "IBKR failed" is what makes a 6am timer failure take
twenty minutes to diagnose, so they are separate types with separate messages
and the wrapper script maps them to separate exit codes.

Usage:
    python -m altdata.sources.ibkr_portfolio            # sync once
    python -m altdata.sources.ibkr_portfolio --dry-run  # connect, print, no write
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Optional

from .. import session

log = logging.getLogger(__name__)

# Gateway paper. The port is the mode -- see the module docstring.
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 4002
DEFAULT_CLIENT_ID = 17          # arbitrary but fixed; a clash is a distinct error
DEFAULT_TIMEOUT = 15.0

PAPER_PORTS = {4002, 7497}
LIVE_PORTS = {4001, 7496}

# Account summary tags -> registry keys. Only what Portfolio Truth needs; the
# tag list IBKR serves is much longer and most of it is noise.
ACCOUNT_TAGS = {
    "NetLiquidation":     ("portfolio.nav", "usd"),
    "TotalCashValue":     ("portfolio.cash", "usd"),
    "BuyingPower":        ("portfolio.buying_power", "usd"),
    "GrossPositionValue": ("portfolio.gross_position_value", "usd"),
    "FullInitMarginReq":  ("portfolio.init_margin", "usd"),
    "FullMaintMarginReq": ("portfolio.maint_margin", "usd"),
    "ExcessLiquidity":    ("portfolio.excess_liquidity", "usd"),
    "AvailableFunds":     ("portfolio.available_funds", "usd"),
    "Cushion":            ("portfolio.cushion", "ratio"),
}

# Per-position metrics, read off the portfolio items.
POSITION_METRICS = ("portfolio.position_qty",
                    "portfolio.position_avg_cost",
                    "portfolio.position_market_value",
                    "portfolio.position_unrealized_pnl")


class IbkrError(Exception):
    """Base for every IBKR failure this module distinguishes."""


class GatewayNotRunning(IbkrError):
    """Nothing is listening on the port."""


class GatewayNotResponding(IbkrError):
    """Something is listening but the API handshake did not complete."""


class IbkrAuthError(IbkrError):
    """Connected, but the Gateway session is not logged in."""


class IbkrApiError(IbkrError):
    """Any other failure after a successful connect."""


def mode_for_port(port: int) -> str:
    """paper / live / unknown, derived from the port and never assumed."""
    if port in PAPER_PORTS:
        return "paper"
    if port in LIVE_PORTS:
        return "live"
    return "unknown"


def source_for_port(port: int) -> str:
    """The source tag written on every row. Derived, so it cannot lie."""
    return f"ibkr_{mode_for_port(port)}"


def connect(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
            client_id: int = DEFAULT_CLIENT_ID,
            timeout: float = DEFAULT_TIMEOUT,
            allow_live: bool = False, ib_factory=None):
    """Read-only connection to a local Gateway. Raises a SPECIFIC error.

    `ib_factory` exists so the validation gate can inject a fake IB without a
    Gateway. Production passes nothing and gets the real client.
    """
    mode = mode_for_port(port)
    if mode == "live" and not allow_live:
        raise IbkrApiError(
            f"port {port} is a LIVE port and allow_live is False. The port is "
            f"the mode; refusing to connect rather than silently reading a "
            f"live account into a store tagged paper.")

    if ib_factory is None:
        try:
            from ib_async import IB  # noqa: PLC0415 -- lazy: tests need no lib
        except ImportError as e:
            raise IbkrApiError(
                "ib_async is not installed. pip install -r requirements.txt. "
                "NOTE: ib_async, not ib_insync -- the latter is archived."
            ) from e
        ib_factory = IB

    ib = ib_factory()
    try:
        # readonly=True is the session-level guarantee that nothing here can
        # trade, independent of what this module does or does not call.
        ib.connect(host, port, clientId=client_id, timeout=timeout,
                   readonly=True)
    except ConnectionRefusedError as e:
        raise GatewayNotRunning(
            f"Gateway not running: nothing is listening on {host}:{port} "
            f"({mode} mode). Start IB Gateway and sign in, then retry."
        ) from e
    except (TimeoutError, __import__("asyncio").TimeoutError) as e:
        raise GatewayNotResponding(
            f"Gateway is listening on {host}:{port} but the API handshake did "
            f"not complete within {timeout:g}s. Usual causes: the API is not "
            f"enabled (Configure > Settings > API > Enable ActiveX and Socket "
            f"Clients), clientId {client_id} is already in use, or a dialog is "
            f"blocking the Gateway window."
        ) from e
    except OSError as e:
        # Connection refused surfaces as OSError on some platforms rather than
        # the dedicated subclass, so check the errno rather than trust the type.
        if getattr(e, "errno", None) in (61, 111, 10061):
            raise GatewayNotRunning(
                f"Gateway not running: connection refused on {host}:{port} "
                f"({mode} mode). Start IB Gateway and sign in, then retry."
            ) from e
        raise IbkrApiError(f"socket error connecting to {host}:{port}: {e}") from e
    except Exception as e:  # noqa: BLE001 -- classified below, never swallowed
        raise IbkrApiError(f"unexpected error connecting to {host}:{port}: "
                           f"{type(e).__name__}: {e}") from e
    return ib


def _num(v: Any) -> Optional[float]:
    try:
        f = float(v)
        return None if f != f else f
    except (TypeError, ValueError):
        return None


def read_state(ib, port: int = DEFAULT_PORT) -> dict:
    """Everything Portfolio Truth needs, from an already-connected client.

    Split from connect() so the validation gate can exercise the parsing
    against canned data without any connection at all.
    """
    # MICROSECONDS, not the default seconds. A portfolio snapshot IS its
    # instant -- observed_at and available_at are both the read time -- so two
    # reads a fraction of a second apart are two observations. At second
    # resolution they collapse to one identical vintage and the store's
    # idempotence index silently discards the second, which is right for a
    # re-pulled FRED series and wrong for a series of broker snapshots.
    read_at = session.utc_iso(timespec="microseconds")
    try:
        accounts = list(ib.managedAccounts() or [])
        summary = list(ib.accountSummary() or [])
        positions = list(ib.portfolio() or [])
    except Exception as e:  # noqa: BLE001
        raise IbkrApiError(f"reading account state failed: "
                           f"{type(e).__name__}: {e}") from e

    # An authenticated Gateway always reports at least one managed account.
    # None means it is running and SIGNED OUT, which looks healthy from the
    # outside and silently returns nothing -- the failure worth naming.
    if not accounts:
        raise IbkrAuthError(
            "connected to the Gateway but it reports no managed accounts. "
            "The session is almost certainly signed out -- Gateway can be "
            "running and logged out at the same time, which looks healthy "
            "from the outside. Sign in and retry.")

    values: dict[str, dict] = {}
    for av in summary:
        tag = getattr(av, "tag", None)
        if tag in ACCOUNT_TAGS:
            values.setdefault(getattr(av, "account", accounts[0]), {})[tag] = {
                "value": _num(getattr(av, "value", None)),
                "currency": getattr(av, "currency", None)}

    holdings = []
    for p in positions:
        contract = getattr(p, "contract", None)
        holdings.append({
            "account": getattr(p, "account", accounts[0]),
            "symbol": getattr(contract, "symbol", None),
            "local_symbol": getattr(contract, "localSymbol", None),
            "sec_type": getattr(contract, "secType", None),
            "currency": getattr(contract, "currency", None),
            "position": _num(getattr(p, "position", None)),
            "avg_cost": _num(getattr(p, "averageCost", None)),
            "market_value": _num(getattr(p, "marketValue", None)),
            "unrealized_pnl": _num(getattr(p, "unrealizedPNL", None)),
        })

    return {"read_at": read_at, "accounts": accounts, "mode": mode_for_port(port),
            "source": source_for_port(port), "account_values": values,
            "positions": holdings}


def to_observations(state: dict, run_id: Optional[str] = None) -> list[dict]:
    """Flatten broker state into point-in-time observation rows.

    Every row carries the producing run's run_id. Without it a Portfolio Truth
    row is unattributable the moment history accumulates: two syncs a minute
    apart are indistinguishable in the store, and no packet can claim lineage
    over rows it cannot identify as its own.

    observed_at == available_at == the read instant, and that is correct here
    rather than lazy: a broker balance has no release lag. The value is true at
    the moment it is read and knowable at the same moment. Contrast FRED, where
    the two differ by weeks and the gap is the entire point of the store.
    """
    read_at = state["read_at"]
    src = state["source"]
    run_id = run_id or state.get("run_id")
    rows: list[dict] = []

    for account, tags in (state.get("account_values") or {}).items():
        for tag, (key, _units) in ACCOUNT_TAGS.items():
            got = tags.get(tag)
            if not got or got["value"] is None:
                continue
            rows.append({"registry_key": key, "instrument": account,
                         "observed_at": read_at, "available_at": read_at,
                         "value": got["value"], "source": src,
                         "run_id": run_id})

    for h in state.get("positions") or []:
        # Instrument is the contract's local symbol where there is one -- an
        # option's localSymbol carries expiry and strike, which the bare symbol
        # does not, and two contracts on one underlying must not collide.
        inst = h.get("local_symbol") or h.get("symbol")
        if not inst:
            continue
        for key, field in (("portfolio.position_qty", "position"),
                           ("portfolio.position_avg_cost", "avg_cost"),
                           ("portfolio.position_market_value", "market_value"),
                           ("portfolio.position_unrealized_pnl", "unrealized_pnl")):
            if h.get(field) is None:
                continue
            rows.append({"registry_key": key, "instrument": inst,
                         "observed_at": read_at, "available_at": read_at,
                         "value": h[field], "source": src,
                         "run_id": run_id})
    return rows


def sync(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
         client_id: int = DEFAULT_CLIENT_ID, timeout: float = DEFAULT_TIMEOUT,
         allow_live: bool = False, dry_run: bool = False,
         db_path: Optional[str] = None, ib_factory=None,
         run_id: Optional[str] = None) -> dict:
    """Connect, read, write, disconnect. The whole job."""
    from .. import observations  # noqa: PLC0415

    # Generated per sync, not per row, so every row from one connection shares
    # one identity. Overridable so a wrapper can stamp its own.
    run_id = run_id or session.new_run_id("ibkr_portfolio")
    ib = connect(host, port, client_id, timeout, allow_live, ib_factory)
    try:
        state = read_state(ib, port)
    finally:
        try:
            ib.disconnect()
        except Exception:  # noqa: BLE001 -- a failed disconnect is not the story
            log.warning("disconnect failed; the read already succeeded")

    rows = to_observations(state, run_id)
    written = 0
    if not dry_run and rows:
        with observations.ObservationStore(db_path) as db:
            written = db.write_many(rows)

    return {"run_id": run_id, "read_at": state["read_at"], "mode": state["mode"],
            "source": state["source"], "accounts": state["accounts"],
            "positions": len(state["positions"]),
            "observations": len(rows), "written": written, "dry_run": dry_run,
            "account_values": state["account_values"]}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Portfolio Truth: read-only IBKR sync into the store")
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT,
                    help="4002 Gateway paper (default), 4001 live, "
                         "7497 TWS paper, 7496 TWS live")
    ap.add_argument("--client-id", type=int, default=DEFAULT_CLIENT_ID)
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    ap.add_argument("--allow-live", action="store_true",
                    help="Required to connect on a live port. Read-only either way.")
    ap.add_argument("--dry-run", action="store_true", help="Connect and print; write nothing")
    ap.add_argument("--db", default=None)
    ap.add_argument("--run-id", default=None,
                    help="Override the generated run id (default "
                         "ibkr_portfolio-<utc stamp>)")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    # Exit codes are the point of the distinct error types: a timer's alerting
    # can tell "start the Gateway" from "sign in" without reading a log.
    try:
        res = sync(args.host, args.port, args.client_id, args.timeout,
                   args.allow_live, args.dry_run, args.db, run_id=args.run_id)
    except GatewayNotRunning as e:
        print(f"\nGATEWAY NOT RUNNING\n  {e}", file=sys.stderr)
        return 3
    except GatewayNotResponding as e:
        print(f"\nGATEWAY NOT RESPONDING\n  {e}", file=sys.stderr)
        return 4
    except IbkrAuthError as e:
        print(f"\nNOT AUTHENTICATED\n  {e}", file=sys.stderr)
        return 5
    except IbkrError as e:
        print(f"\nIBKR API ERROR\n  {e}", file=sys.stderr)
        return 6

    print(f"\nPortfolio Truth -- {res['source']} ({res['mode']} mode)")
    print(f"  run id     : {res['run_id']}")
    print(f"  read at    : {res['read_at']}")
    print(f"  accounts   : {', '.join(res['accounts'])}")
    for account, tags in res["account_values"].items():
        for tag, (key, units) in ACCOUNT_TAGS.items():
            got = tags.get(tag)
            if got and got["value"] is not None:
                print(f"  {key:<34} {got['value']:>16,.2f} {units}")
    print(f"  positions  : {res['positions']}")
    print(f"  observations: {res['observations']}"
          + ("  (dry run -- nothing written)" if res["dry_run"]
             else f", {res['written']} new rows written"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
