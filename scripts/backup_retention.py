#!/usr/bin/env python3
"""
Retention plan for the off-box `db/` snapshots -- names in, names to delete out.

    rclone lsf "$REMOTE/db" --files-only \
        | python scripts/backup_retention.py --today 2026-09-30 --require chester-2026-09-30.db.gz

Prints one filename per line: the snapshots the rule does not keep. Deletes
nothing itself. `scripts/rclone_sync.sh` deletes each printed name with
`rclone deletefile "$REMOTE/db/<name>"`, one named file at a time, after
re-checking the name against the same pattern. It is the one removal the sweep
makes, and it is confined to `db/`: every other tree only ever grows.

THE RULE (ruled 29 Sep 2026):
  - every snapshot dated in the last 14 days (today and the 13 before it);
  - the newest snapshot of each of the last 8 ISO weeks (this week and 7 back);
  - the newest snapshot of every calendar month, indefinitely;
  - the newest snapshot on the remote, always.
Everything else matching the pattern goes. Roughly 14 + 6 + one a month kept.

WHAT IT REFUSES TO DO:
  - touch a name that does not match `chester-YYYY-MM-DD.db[.gz]` -- anything a
    human put in db/ is not this script's to judge;
  - delete anything dated after --today (a clock that is wrong is not a reason
    to lose a backup);
  - delete anything at all unless --require names a file that IS in the
    listing -- tonight's upload must be on the remote before an old copy goes,
    so a sweep that failed to upload can never also prune.

Exit codes: 0 plan printed (possibly empty) · 2 usage · 3 --require is not in
the listing (nothing printed, nothing deleted).
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, timedelta

PATTERN = re.compile(r"^chester-(\d{4})-(\d{2})-(\d{2})\.db(\.gz)?$")

DAILY_DAYS = 14
WEEKLY_WEEKS = 8


def _dated(names: list[str]) -> list[tuple[date, str]]:
    out = []
    for n in names:
        m = PATTERN.match(n)
        if not m:
            continue
        try:
            out.append((date(int(m[1]), int(m[2]), int(m[3])), n))
        except ValueError:           # chester-2026-02-31.db: not ours to judge
            continue
    return sorted(out)


def plan(names: list[str], today: date) -> tuple[list[str], list[str]]:
    """(keep, delete) over the names that match the pattern; others are ignored."""
    dated = _dated(names)
    if not dated:
        return [], []
    keep: set[str] = set()

    # Newest per week / per month: iterate oldest-first so the last write wins.
    newest_week: dict[tuple[int, int], str] = {}
    newest_month: dict[tuple[int, int], str] = {}
    for d, n in dated:
        newest_week[d.isocalendar()[:2]] = n
        newest_month[(d.year, d.month)] = n

    this_monday = today - timedelta(days=today.weekday())
    oldest_week_monday = this_monday - timedelta(weeks=WEEKLY_WEEKS - 1)
    oldest_daily = today - timedelta(days=DAILY_DAYS - 1)

    for d, n in dated:
        if d > today:                                    # future: keep
            keep.add(n)
        elif d >= oldest_daily:                          # 14 daily
            keep.add(n)
        elif (d - timedelta(days=d.weekday()) >= oldest_week_monday
              and newest_week[d.isocalendar()[:2]] == n):  # 8 weekly
            keep.add(n)
        elif newest_month[(d.year, d.month)] == n:       # monthly, forever
            keep.add(n)
    keep.add(dated[-1][1])                               # the newest, always

    delete = [n for _, n in dated if n not in keep]
    return sorted(keep), delete


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--today", required=True, help="YYYY-MM-DD")
    ap.add_argument("--require", required=True,
                    help="tonight's upload; nothing is deleted unless it is listed")
    try:
        a = ap.parse_args(argv)
        today = date.fromisoformat(a.today)
    except (SystemExit, ValueError):
        return 2
    names = [ln.strip() for ln in sys.stdin.read().splitlines() if ln.strip()]
    if a.require not in names:
        print(f"refusing to prune: {a.require} is not on the remote",
              file=sys.stderr)
        return 3
    _, delete = plan(names, today)
    for n in delete:
        print(n)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
