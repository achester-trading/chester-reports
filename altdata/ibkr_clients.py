"""
Every IBKR API client id this repo connects with, in one table. (AUD-3a item 7,
14 Oct 2026)

The Gateway allows one session per client id: a second connection on an id in
use is refused, and two tools sharing one cannot be told apart in the Gateway's
own log. The data and architecture audit found the watchdog's probe and the
what-if tool both on 18, so a what-if run at the wrong moment either failed or
knocked the watchdog's probe off, and the watchdog's next verdict could read a
healthy Gateway as down. The what-if tool now has its own id.

Each user reads its default from here, except the two shell wrappers (which
carry the number as their default) and altdata/loggers/borrow.py (aud-1-data-
fixes's file tonight, so its literal stays): tools/validate_audit_3a.py reads
those three and fails when any differs from this table, or when two entries
share an id.
"""

from __future__ import annotations

CLIENT_IDS: dict[str, int] = {
    "portfolio_sync": 17,   # altdata/sources/ibkr_portfolio.py; scripts/sync_ibkr.sh
    "watchdog": 18,         # scripts/ibgateway_watchdog.sh -- the health probe
    "costs": 19,            # altdata/sources/ibkr_costs.py
    "whatif": 20,           # altdata/sources/ibkr_whatif.py; tools/decide.py preview
    "auction": 23,          # altdata/loggers/auction.py
    "borrow": 25,           # altdata/loggers/borrow.py
    "bars": 27,             # altdata/sources/ibkr_bars.py (A93; built, switched off)
}
