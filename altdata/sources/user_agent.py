"""
The project's one identity on the wire (ruled 17 Oct 2026).

Every outbound request carries a generic User-Agent naming the project and its
repository, never a person or an address. The SEC alone gets the contact form,
`edgar.user_agent()` (CHESTER_SEC_CONTACT), because its fair-access rule
requires one; `for_url` routes a request to the right one by host, and a non-SEC
caller never imports edgar's.

`browser_like()` is the same identity in the `Mozilla/5.0 (compatible; ...)`
shape, for the hosts that answer a bare product token with a 403 (the voices
scan's desks, CFETS, iShares, SAFE). It still names the project and the
repository; it does not pass for a browser.

tools/validate_secrets.py group J holds it: no User-Agent string in the tree
carries an "@" or a person's name, and no non-SEC caller imports edgar's.
"""

from __future__ import annotations

import urllib.parse
from typing import Optional

PROJECT = "chester-reports"
VERSION = "1.0"
REPO_URL = "https://github.com/achester-trading/chester-reports"

# The hosts whose fair-access rule asks for a contact: sec.gov and its
# subdomains (www., data., efts.).
SEC_HOSTS = ("sec.gov",)


def generic() -> str:
    """`chester-reports/1.0 (+<repository>)`: the project and its repository."""
    return f"{PROJECT}/{VERSION} (+{REPO_URL})"


def browser_like() -> str:
    """The same identity in the compatible-browser shape some hosts require."""
    return f"Mozilla/5.0 (compatible; {PROJECT}/{VERSION}; +{REPO_URL})"


def is_sec_host(url_or_host: str) -> bool:
    """True for sec.gov and its subdomains, from a URL or a bare host."""
    s = str(url_or_host or "")
    host = urllib.parse.urlsplit(s).hostname if "//" in s else s.split(":")[0]
    host = (host or "").lower().rstrip(".")
    return any(host == h or host.endswith("." + h) for h in SEC_HOSTS)


def for_url(url: str, *, browser: bool = False) -> Optional[str]:
    """The User-Agent for one request: the SEC's contact form for an SEC host
    (None when CHESTER_SEC_CONTACT is unset -- never a guess), else the generic
    project string."""
    if is_sec_host(url):
        from . import edgar  # noqa: PLC0415
        return edgar.user_agent()
    return browser_like() if browser else generic()
