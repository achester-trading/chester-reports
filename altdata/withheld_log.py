"""
The withheld-drafts log (EL-6, from 17 Oct 2026): one JSON line per paragraph an
audit withheld, written when an edition is archived.

    from altdata import withheld_log
    withheld_log.record_edition("daily_close", "daily_close_2026-10-19_stack.json", ed, archive_dir)
    lines = withheld_log.read(archive_dir)      # None when no log exists

WHY. Until now a withheld paragraph lived only on its section in the archived
edition JSON and as a line in a run log. The system-metrics block (EL-6) counts
them per month; it reads this file and says "not recorded" before it exists.

WHAT A LINE HOLDS: the instant, the report, the edition's archive name, the
section (and sub-section) id and the audit's reason, cut to 200 characters. No
draft text: the rejected draft stays where it always was, in the run log.

WHERE. `withheld_drafts.jsonl` in the archive directory beside the editions
(daily_cascade/deliver.archive_path). A write that fails is logged and never
fails the run that archived the edition.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)
NAME = "withheld_drafts.jsonl"


def path(archive_dir: Optional[str] = None) -> Path:
    from daily_cascade import deliver                           # noqa: PLC0415
    return Path(deliver.archive_path(NAME, archive_dir))


def withheld_in(ed: dict) -> list[tuple[str, str]]:
    """(section id, reason) for every section or sub-section the edition holds
    withheld."""
    out = []
    for s in ed.get("sections") or []:
        if s.get("withheld"):
            out.append((str(s.get("id")), str(s["withheld"])))
        for ss in s.get("subsections") or []:
            if isinstance(ss, dict) and ss.get("withheld"):
                out.append((f"{s.get('id')}/{ss.get('id') or ss.get('title')}",
                            str(ss["withheld"])))
    return out


def record_edition(report: str, edition: str, ed: dict,
                   archive_dir: Optional[str] = None, now: Optional[str] = None) -> int:
    """Append one line per withheld paragraph; the number written. Never raises."""
    rows = withheld_in(ed)
    if not rows:
        return 0
    try:
        from altdata import session                             # noqa: PLC0415
        at = now or session.utc_iso()
        p = path(archive_dir)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            for sec, why in rows:
                fh.write(json.dumps({"at": at, "report": report, "edition": edition,
                                     "section": sec, "reason": why[:200]},
                                    sort_keys=True) + "\n")
        return len(rows)
    except Exception as exc:                                    # noqa: BLE001
        log.warning("withheld-drafts log not written: %s", exc)
        return 0


def read(archive_dir: Optional[str] = None) -> Optional[list[str]]:
    """The log's lines, or None when there is no log."""
    try:
        p = path(archive_dir)
        return p.read_text(encoding="utf-8").splitlines() if p.exists() else None
    except OSError:
        return None
