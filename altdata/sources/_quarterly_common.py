"""
What the Quarterly's readers share (b69-quarterly-readers-1, D34 of 24 Oct 2026):
the robots read at every pull, the one-request-a-day guard, and the terms each
reader was built under.

Not a writer: no KEYS and no pull(). The writers that import it are named in
altdata/feeds.py OFFICIAL_WRITERS.

THE 16 OCT RULE, IN CODE. Every reader reads its host's robots.txt before its
data request, through the wildcard-aware reader (aaii.robots_verdict). A file
answered 401, 403, 404 or 410 is "unavailable" and means no rules (RFC 9309,
section 2.3.1.3) -- the reading cboe_indices and listings already take. Any other
failure to read it is a refusal to guess: the pull raises, and _publication.run
turns that into STALE with the reason. A disallow is STALE, never a retry.

A REFUSAL IS NEVER RETRIED AROUND. Every data request goes through
_base.http_get_response, which raises on any 4xx at once; the one-a-day readers
also pass max_retries=1, so a 5xx is not retried either.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
from pathlib import Path
from typing import Callable, Optional

from .. import session
from ._base import FetchError, http_get_response, http_get_text


class Refused(RuntimeError):
    """A robots disallow, or a guard that has spent its request."""


def _host(url: str) -> str:
    m = re.match(r"(https?://[^/]+)", url)
    if not m:
        raise ValueError(f"not an absolute URL: {url}")
    return m.group(1)


def robots_check(url: str, get_text: Optional[Callable[[str], str]] = None) -> str:
    """The deciding rule for `url`, or raise Refused. Reads robots.txt now."""
    from .aaii import robots_verdict
    get_text = get_text or (lambda u: http_get_text(u, timeout=30))
    robots = _host(url) + "/robots.txt"
    try:
        text = get_text(robots)
    except FetchError as exc:
        if re.match(r"HTTP 4(01|03|04|10)\b", str(exc)):
            return f"robots.txt {str(exc)[:8]}: unavailable, no rules (RFC 9309 2.3.1.3)"
        raise
    allowed, rule = robots_verdict(text, url)
    if not allowed:
        raise Refused(f"robots.txt disallows {url} ({rule}); not requested")
    return rule or "no matching rule"


def state_path(name: str) -> Path:
    root = os.environ.get("CHESTER_STATE_DIR") or str(Path.home() / ".chester")
    return Path(root) / f"quarterly_reader_{name}.json"


class DailyGuard:
    """ONE DATA REQUEST A CALENDAR DAY (ET), counted before it is sent.

    PortWatch's terms (the IMF's: "Copying or downloading IMF Content in any
    systematic way" needs permission; Data may be downloaded with attribution)
    and the Riksbank's per-IP limit are honoured by sending at most one request a
    day per source, whatever the timer does. The official feed runs twice a day
    (16:10 and 06:45); the second run of a day finds the guard spent and returns
    STALE with that reason, writing nothing.
    """

    def __init__(self, name: str, path: Optional[Path] = None,
                 today: Optional[Callable[[], str]] = None) -> None:
        self.name = name
        self.path = Path(path or state_path(name))
        self.today = today or (lambda: dt.datetime.now(session._eastern_tz()).date().isoformat())

    def _read(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def spent(self) -> bool:
        return self._read().get("last_request_day") == self.today()

    def charge(self) -> None:
        if self.spent():
            raise Refused(f"{self.name}: today's one request is already spent "
                          f"({self.today()}); not requested again")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"last_request_day": self.today()}),
                             encoding="utf-8")


def fetch(url: str, *, once: bool = False, timeout: float = 60, robots: bool = True,
          get: Optional[Callable[..., tuple]] = None,
          get_text: Optional[Callable[[str], str]] = None) -> tuple[bytes, dict]:
    """GET after the robots check. `once` means no retry of any kind; `robots`
    False only where the caller has just read robots.txt itself (the guarded
    readers read it before spending their request). `get` and `get_text` are the
    CALLING MODULE'S own http helpers, so a gate that replaces a writer's helpers
    (validate_official_sources' outage test) reaches this request too."""
    if robots:
        robots_check(url, get_text=get_text)
    getter = get or http_get_response
    return getter(url, timeout=timeout, max_retries=1 if once else 3)


def et_instant(day: str, hhmm: str) -> str:
    """`day` at `hhmm` ET, as canonical UTC."""
    from .. import observations
    h, m = (int(x) for x in hhmm.split(":"))
    local = dt.datetime.combine(dt.date.fromisoformat(day), dt.time(h, m),
                                tzinfo=session._eastern_tz())
    return observations.canonical_instant(local.astimezone(dt.timezone.utc).isoformat())


def main(pull: Callable[..., dict], argv=None, **extra: tuple) -> int:
    """The readers' command line: one pull, or `--dry-run` into a throwaway store.

    A dry run makes the real requests (robots first, the guard charged) and
    writes ONLY a temporary store, removed after; the summary shows what a real
    pull would write. `extra` names an integer option per reader, e.g.
    releases=(1, "WASDE releases to read").
    """
    import argparse
    import logging
    import shutil
    import tempfile
    from .. import observations
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="write a temporary store only, and print the summary")
    for name, (default, helptext) in extra.items():
        ap.add_argument(f"--{name}", type=int, default=default, help=helptext)
    a = ap.parse_args(argv)
    kw = {n: getattr(a, n) for n in extra}
    if a.dry_run:
        tmp = tempfile.mkdtemp(prefix="quarterly_reader_dry_")
        db = observations.ObservationStore(str(Path(tmp) / "dry.sqlite"))
        try:
            out = pull(db=db, **kw)
            out["dry_run"] = "a temporary store only; nothing written to the live store"
        finally:
            db.close()
            shutil.rmtree(tmp, ignore_errors=True)
    else:
        out = pull(**kw)
    print(json.dumps(out, indent=2, sort_keys=True, default=str))
    return 0 if out.get("status") == "OK" else 1
