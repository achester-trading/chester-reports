"""
The connection: a paper port, then a paper account, or nothing.

    ib = client.connect(cfg)          # raises; never returns a live session

The port is checked BEFORE connecting (a live port never sees a socket), and
the accounts AFTER: every account the gateway reports must begin with the
config's paper prefix ("DU"). A live account closes the session and raises
LiveAccount, its reason logged -- before any order object exists, since no
caller builds one until connect() has returned. In dry mode the session is
opened read-only, as the portfolio sync's is.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from . import config as pcfg

log = logging.getLogger(__name__)


class PaperOnly(RuntimeError):
    """A refusal that keeps the executor on paper."""


class LivePort(PaperOnly):
    pass


class LiveAccount(PaperOnly):
    pass


class Off(RuntimeError):
    """The executor is switched off: nothing connects."""


def check_port(cfg: dict) -> int:
    port = int(cfg.get("port") or 0)
    papers = {int(p) for p in cfg.get("paper_ports") or []}
    if port not in papers:
        why = (f"port {port} is not a paper port ({sorted(papers)}): refusing to "
               f"connect")
        log.error("paper_exec: %s", why)
        raise LivePort(why)
    return port


def check_accounts(accounts: list, cfg: dict) -> list[str]:
    prefix = str(cfg.get("paper_account_prefix") or "DU")
    accs = [str(a).strip() for a in accounts or [] if str(a).strip()]
    live = [a for a in accs if not a.startswith(prefix)]
    if not accs or live:
        why = ("the gateway reports no account" if not accs else
               f"the gateway reports a non-paper account ({', '.join(live)}): paper "
               f"accounts begin with {prefix!r}")
        log.error("paper_exec: aborting before any order is built: %s", why)
        raise LiveAccount(why)
    return accs


def connect(cfg: dict, ib_factory: Optional[Callable[[], Any]] = None):
    """The IB session on the paper port, its accounts checked. Raises Off,
    LivePort or LiveAccount; the gateway's own errors pass through."""
    mode = pcfg.mode(cfg)
    if mode == "off":
        raise Off("paper executor off")
    port = check_port(cfg)
    if ib_factory is None:
        from ib_async import IB                                 # noqa: PLC0415
        ib_factory = IB
    ib = ib_factory()
    ib.connect(str(cfg.get("host") or "127.0.0.1"), port,
               clientId=pcfg.client_id(cfg), timeout=float(cfg.get("timeout_s") or 15),
               readonly=(mode != "send"))
    try:
        check_accounts(list(ib.managedAccounts()), cfg)
    except PaperOnly:
        ib.disconnect()
        raise
    return ib
