"""
The delivery layer. Built once, before any report content, per architecture 32.3.

    "The operator's binding constraint is time, and a report that must be
     opened is a report that will be read late or not at all."

So reports are PUSHED. HTML in the message body — not an attachment, not a link
to a file on a box, because both of those are "opened later" wearing a
disguise.

-----------------------------------------------------------------------------
FOUR RULES, EACH FROM 32.3, EACH LOAD-BEARING
-----------------------------------------------------------------------------

1. **THE ARCHIVE IS WRITTEN FIRST, AND THE SEND CANNOT AFFECT IT.** 32.3 wants
   the record not to depend on an inbox. Writing the file before opening a
   socket is the difference between "the report exists and was not delivered"
   and "the report is gone" — and only the first of those is recoverable. The
   archive path is returned whatever happens to the send.

2. **A SEND FAILURE NEVER FAILS THE RUN THAT PRODUCED THE REPORT.** The report
   is the product; SMTP is transport. An exception here would throw away work
   that already succeeded, which is the same mistake as letting a git push
   failure discard a generated artifact.

3. **BUT IT IS RECORDED, DISTINCTLY.** "Never fails the run" and "nobody finds
   out" are different designs and only one of them is honest. Every outcome is
   a NAMED state — sent / not_configured / send_failed / archive_failed — in
   the return value, the log, and the state record. This is the sixth instance
   of a delivery path that could look wired and do nothing; the heartbeat
   caller learned it first.

4. **CREDENTIALS COME FROM THE ENVIRONMENT OR .env, NEVER FROM argv.** argv is
   readable by every process on the box (`ps auxww`) and lands in shell
   history. The repo's standing rule is that a secret reaching a transcript is
   a leaked secret, and argv is a transcript. The variable names are the ones
   scripts/send_smtp_alert.py already uses, so one credential set serves both
   the alert path and the report path rather than two that can drift.

        SMTP_USER      account to authenticate as, and the From address
        SMTP_PASSWORD  password or app-password. Never logged, never printed.
        SMTP_RCPT / CHESTER_ALERT_EMAIL / SMTP_TO   recipient, in that order of
                       precedence -- the heartbeat path resolves the same three,
                       so a box configured for alerts is configured for reports
        SMTP_HOST      default smtp.gmail.com
        SMTP_PORT      default 587 (STARTTLS)

   Sending through the operator's own authenticated relay rather than direct
   from the box is deliberate: a cloud host sending its own mail lands in spam,
   and a report in a spam folder is a report that was not delivered.
"""

from __future__ import annotations

import logging
import os
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import session  # noqa: E402

log = logging.getLogger("daily_cascade.deliver")

REQUIRED = ("SMTP_USER", "SMTP_PASSWORD")

# The recipient, in precedence order. The box's .env already carries SMTP_TO --
# scripts/check_heartbeat_cron.sh resolves CHESTER_ALERT_EMAIL then SMTP_TO and
# passes the winner in as SMTP_RCPT -- so reading only SMTP_RCPT here would have
# meant a box configured for alerts silently reporting `not_configured` for
# reports. One credential set, or they drift; and drift between two delivery
# paths is discovered during the outage that needed both.
RCPT_KEYS = ("SMTP_RCPT", "CHESTER_ALERT_EMAIL", "SMTP_TO")
ARCHIVE_DIR = os.environ.get("CHESTER_REPORTS_DIR", "reports")


def _dotenv() -> dict[str, str]:
    """.env as a dict. Same ten lines as altdata.sources.massive_chain.

    Duplicated rather than imported for the reason stated there: altdata is the
    library and this is a report package, so importing a private helper across
    that line would point the dependency the wrong way for the sake of ten
    lines.
    """
    env: dict[str, str] = {}
    path = REPO / ".env"
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def smtp_config() -> tuple[Optional[dict], list[str]]:
    """(config, missing). Config is None when anything required is absent."""
    env = _dotenv()

    def get(key: str, default: str = "") -> str:
        return os.environ.get(key) or env.get(key) or default

    missing = [k for k in REQUIRED if not get(k)]
    rcpt = next((get(k) for k in RCPT_KEYS if get(k)), "")
    if not rcpt:
        missing.append(" or ".join(RCPT_KEYS))
    if missing:
        return None, missing
    return {
        "user": get("SMTP_USER"),
        "password": get("SMTP_PASSWORD"),
        "rcpt": rcpt,
        "host": get("SMTP_HOST", "smtp.gmail.com"),
        "port": int(get("SMTP_PORT", "587")),
    }, []


def archive(html: str, name: str, archive_dir: Optional[str] = None) -> Optional[str]:
    """Write the permanent copy. Returns the path, or None if it could not."""
    try:
        d = Path(archive_dir or ARCHIVE_DIR)
        d.mkdir(parents=True, exist_ok=True)
        p = d / name
        p.write_text(html, encoding="utf-8")
        return str(p)
    except OSError as exc:
        log.warning("archive failed for %s: %s", name, exc)
        return None


def send_html(subject: str, html: str, text_fallback: str = "") -> tuple[str, str]:
    """(state, detail). Never raises.

    States: sent · not_configured · send_failed. `not_configured` is a real
    answer and not an error -- a box without credentials is a box that has not
    been set up yet, and it must say so rather than look like a delivery.
    """
    cfg, missing = smtp_config()
    if cfg is None:
        return "not_configured", f"missing {', '.join(missing)}"

    msg = EmailMessage()
    msg["From"] = cfg["user"]
    msg["To"] = cfg["rcpt"]
    msg["Subject"] = subject
    # A plain-text part first, then HTML as the alternative. A client that
    # cannot render HTML gets something readable rather than markup, and some
    # spam filters score a multipart/alternative better than HTML alone.
    msg.set_content(text_fallback or "This report is HTML; see the HTML part.")
    msg.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=30) as s:
            s.starttls()
            s.login(cfg["user"], cfg["password"])
            s.send_message(msg)
    except Exception as exc:  # noqa: BLE001 -- transport must never kill a report
        # Redact before this reaches a log: an SMTP server can quote what it
        # was given back in an error string.
        detail = str(exc).replace(cfg["password"], "<redacted>")
        return "send_failed", f"{type(exc).__name__}: {detail}"
    return "sent", f"{cfg['rcpt']} via {cfg['host']}:{cfg['port']}"


def deliver(subject: str, html: str, archive_name: str,
            text_fallback: str = "",
            archive_dir: Optional[str] = None) -> dict:
    """Archive, then send. Returns the outcome; raises nothing.

    Order matters and is the point of rule 1: the file is on disk before a
    socket is opened, so a mail server having a bad day costs the delivery and
    never the record.
    """
    path = archive(html, archive_name, archive_dir)
    state, detail = send_html(subject, html, text_fallback)

    if path is None:
        # The one case where the transport succeeding is not the whole story:
        # the mail went out and nothing was kept. Say so distinctly rather than
        # reporting the send and letting the missing archive be discovered
        # months later by someone looking for the record.
        log.error("archive FAILED; delivery=%s", state)
        archived_state = "archive_failed"
    else:
        archived_state = "archived"
        log.info("archived %s", path)

    if state == "sent":
        log.info("delivered: %s", detail)
    else:
        log.warning("NOT delivered (%s): %s", state, detail)

    return {"archive_state": archived_state, "archive_path": path,
            "delivery": state, "delivery_detail": detail,
            "delivered_at": session.utc_iso()}
