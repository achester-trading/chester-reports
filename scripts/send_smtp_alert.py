#!/usr/bin/env python3
"""
Deliver one alert by direct SMTP, for a box with no local mail transport.

WHY THIS EXISTS. check_heartbeat_cron.sh offers email as its fourth delivery
channel and reaches it through `mail` or `sendmail`. A stock VPS has neither,
so on this box that channel resolved to `delivery=no_mta` every time -- the
outcome was RECORDED, which is the point of that design, but recorded absence
is not delivery. Installing an MTA needs root. Sending SMTP directly does not,
and the operator already has to hold credentials somewhere for either path.

EVERYTHING COMES FROM THE ENVIRONMENT, NOTHING FROM argv. A password passed as
an argument is readable by every process on the box for as long as this one
runs (`ps auxww`), and lands in any shell history that echoes the command. The
repo's standing rule is that a secret which reaches a transcript is a leaked
secret; argv is a transcript. So the caller exports and this reads:

    SMTP_USER       account to authenticate as, and the From address
    SMTP_PASSWORD   its password or app-password -- never logged, never printed
    SMTP_RCPT       recipient (the caller resolves CHESTER_ALERT_EMAIL/SMTP_TO)
    SMTP_SUBJECT    subject line
    SMTP_BODY       plain-text body
    SMTP_HOST       default smtp.gmail.com
    SMTP_PORT       default 587 (STARTTLS)

EXIT CODES: 0 sent, 1 misconfigured (a required variable is missing), 2 the
send itself failed. The caller distinguishes them so the log can say which,
because "no credentials" and "the server refused us" need different fixes and
a single `smtp_failed` would hide that.

FAILURE MESSAGES ARE SCRUBBED. An SMTP server can quote what it was given back
at you in an error string, so the password is redacted out of any message this
prints rather than trusted not to appear in one.
"""

from __future__ import annotations

import os
import smtplib
import sys
from email.message import EmailMessage

REQUIRED = ("SMTP_USER", "SMTP_PASSWORD", "SMTP_RCPT")


def main() -> int:
    missing = [k for k in REQUIRED if not os.environ.get(k)]
    if missing:
        print(f"smtp: not configured -- missing {', '.join(missing)}",
              file=sys.stderr)
        return 1

    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    rcpt = os.environ["SMTP_RCPT"]
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))

    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = rcpt
    msg["Subject"] = os.environ.get("SMTP_SUBJECT", "[chester] alert")
    msg.set_content(os.environ.get("SMTP_BODY", ""))

    try:
        with smtplib.SMTP(host, port, timeout=30) as s:
            s.starttls()
            s.login(user, password)
            s.send_message(msg)
    except Exception as exc:                                  # noqa: BLE001
        # Redact before printing: the server's own error text may echo what we
        # sent it, and this string goes to the log the caller appends to.
        detail = str(exc).replace(password, "<redacted>")
        print(f"smtp: send failed via {host}:{port} -- "
              f"{type(exc).__name__}: {detail}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
