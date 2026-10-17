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

THE ALPHA LAB'S SNAPSHOTS (ruling 8, 14 Oct 2026). The same rule applies to
`alpha-YYYY-MM-DD.db[.gz]`, the lab ledger's nightly snapshots, under
`--prefix alpha`: by exact name, each family judged on its own, the newest of
each never pruned. A run with one prefix never plans a name of the other.

Exit codes: 0 plan printed (possibly empty) · 2 usage · 3 --require is not in
the listing (nothing printed, nothing deleted).

TWO MORE MODES (AUD-1 items 1b and 1c, the audit of 14 Oct 2026: the EOD zips
were never pruned, on the box or on Drive):

  --mode zips          Drive's backups/chains/ tree: `chains_YYYY-MM-DD.zip`
                       beyond the newest LOCAL_KEEP (14) goes -- THE SAME RULE
                       AS THE BOX'S (audit-leftovers-1: until then Drive kept 30
                       days and the box 14, and the mirror grew past the box) --
                       by exact name, as db/'s do; never one dated after --today,
                       never the newest, and nothing unless --require (the newest
                       local zip) is in the listing.
  --mode local-chains  the box's ~/backups/chains: stdin is the LOCAL listing as
                       `size;name` lines, --remote a file holding the remote's
                       `rclone lsf --format sp --separator ';'` listing. The
                       newest LOCAL_KEEP (14) session zips are kept; an older
                       one is printed for deletion only when the remote holds
                       THAT EXACT FILE -- the same name and the same size -- the
                       rule db/'s prune already follows (confirm, then delete).
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, timedelta

PREFIXES = ("chester", "alpha")
PATTERN = re.compile(r"^chester-(\d{4})-(\d{2})-(\d{2})\.db(\.gz)?$")


def pattern(prefix: str = "chester") -> re.Pattern:
    if prefix not in PREFIXES:
        raise ValueError(f"no retention rule for {prefix!r}")
    return re.compile(rf"^{prefix}-(\d{{4}})-(\d{{2}})-(\d{{2}})\.db(\.gz)?$")

DAILY_DAYS = 14
WEEKLY_WEEKS = 8


def _dated(names: list[str], prefix: str = "chester") -> list[tuple[date, str]]:
    out = []
    pat = pattern(prefix)
    for n in names:
        m = pat.match(n)
        if not m:
            continue
        try:
            out.append((date(int(m[1]), int(m[2]), int(m[3])), n))
        except ValueError:           # chester-2026-02-31.db: not ours to judge
            continue
    return sorted(out)


def plan(names: list[str], today: date,
         prefix: str = "chester") -> tuple[list[str], list[str]]:
    """(keep, delete) over the names that match the prefix's pattern; others
    are ignored."""
    dated = _dated(names, prefix)
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


ZIP_PATTERN = re.compile(r"^chains_(\d{4})-(\d{2})-(\d{2})\.zip$")
ZIP_KEEP_DAYS = 30
LOCAL_KEEP = 14


def _zips(names) -> list[tuple[date, str]]:
    out = []
    for n in names:
        m = ZIP_PATTERN.match(n)
        if not m:
            continue
        try:
            out.append((date(int(m[1]), int(m[2]), int(m[3])), n))
        except ValueError:
            continue
    return sorted(out)


def plan_zips(names: list[str], today: date, keep: int = LOCAL_KEEP) -> list[str]:
    """Drive's zips beyond the newest `keep` -- the box's own rule, so both sides
    hold the same set -- never the newest, never one dated after `today`."""
    dated = [x for x in _zips(names) if x[0] <= today]
    if not dated:
        return []
    newest = dated[-1][1]
    old = dated[:-keep] if len(dated) > keep else []
    return [n for _, n in old if n != newest]


def _sized(lines: list[str]) -> dict[str, int]:
    out = {}
    for ln in lines:
        if ";" not in ln:
            continue
        size, name = ln.split(";", 1)
        name = name.strip().split("/")[-1]
        try:
            out[name] = int(size.strip())
        except ValueError:
            continue
    return out


def plan_local(local: dict[str, int], remote: dict[str, int],
               keep: int = LOCAL_KEEP) -> list[str]:
    """Local zips beyond the newest `keep`, each only if the remote holds the
    exact file (same name, same size)."""
    dated = _zips(local)
    old = dated[:-keep] if len(dated) > keep else []
    return [n for _, n in old if remote.get(n) == local[n]]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--mode", default="db", choices=("db", "zips", "local-chains"))
    ap.add_argument("--today", help="YYYY-MM-DD (db, zips)")
    ap.add_argument("--require",
                    help="tonight's upload; nothing is deleted unless it is listed")
    ap.add_argument("--prefix", default="chester", choices=PREFIXES)
    ap.add_argument("--remote", help="local-chains: the remote's size;name listing")
    try:
        a = ap.parse_args(argv)
        today = date.fromisoformat(a.today) if a.today else None
    except (SystemExit, ValueError):
        return 2
    lines = [ln.strip() for ln in sys.stdin.read().splitlines() if ln.strip()]
    if a.mode == "local-chains":
        if not a.remote:
            return 2
        try:
            with open(a.remote, encoding="utf-8") as fh:
                remote = _sized(fh.read().splitlines())
        except OSError:
            print("refusing to prune: the remote listing is unreadable",
                  file=sys.stderr)
            return 3
        for n in plan_local(_sized(lines), remote):
            print(n)
        return 0
    if today is None or not a.require:
        return 2
    names = lines
    if a.require not in names or (a.mode == "db"
                                  and not pattern(a.prefix).match(a.require)):
        print(f"refusing to prune: {a.require} is not on the remote",
              file=sys.stderr)
        return 3
    if a.mode == "zips":
        for n in plan_zips(names, today):
            print(n)
        return 0
    _, delete = plan(names, today, a.prefix)
    for n in delete:
        print(n)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
