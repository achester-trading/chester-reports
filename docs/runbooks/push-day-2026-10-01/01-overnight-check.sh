#!/usr/bin/env bash
# Push day 2026-10-01, step 1 -- READ ONLY. Did 4a22aa4's overnight fix hold?
# Run from the laptop's repo root (PowerShell):
#   & "C:\Program Files\Git\bin\bash.exe" -c "ssh vps 'bash -s' < docs/runbooks/push-day-2026-10-01/01-overnight-check.sh"
set -u
cd ~/chester-reports || { echo "no checkout"; exit 1; }
MONTH=$(date +%Y-%m)

echo "== box HEAD (expect 4a22aa4 before the push)"
git log --oneline -1

echo
echo "== last run of each morning unit (healthy: Result=success, ExecMainStatus=0)"
for u in chester-overnight chester-morning-anchor chester-monthly chester-heartbeat; do
  printf '  %-24s %s\n' "$u" "$(systemctl --user show "$u.service" \
      -p Result -p ExecMainStatus -p ExecMainStartTimestamp -p ExecMainExitTimestamp \
      | tr '\n' ' ')"
done

echo
echo "== overnight log, today's step lines (healthy: 'overnight fetch start' FIRST, then the correction pull, all inside 10 min)"
# The step lines only: yfinance's DeprecationWarnings would bury them, and a JSON
# summary ends without a newline, so a step line can follow a '}' on one line.
grep -v -e DeprecationWarning -e last_rows_same_interval ~/logs/overnight-"$MONTH".log 2>/dev/null \
  | grep -oE "$(date -u +%Y-%m-%d)T[0-9:]+\+00:00 .*" | cut -c1-160 | tail -n 20 \
  || echo "  no overnight step lines today"

echo
echo "== status files (healthy: overnight_status dated TODAY -- a killed run writes none)"
for d in ~/state ~/.chester; do
  for f in overnight_status morning_anchor_status monthly_status; do
    [ -f "$d/$f" ] && printf '  %s: %s\n' "$d/$f" "$(tr '\n' ' ' < "$d/$f")"
  done
done

echo
echo "== heartbeat, last verdict line (after 08:30 ET; healthy: verdict=ok and units=ok, not units=failed:...)"
grep 'verdict=' ~/logs/heartbeat_check-"$MONTH".log 2>/dev/null | tail -n 1 | cut -c1-400 \
  || echo "  no heartbeat verdict for $MONTH yet"

echo
echo "== feeds freshness"
.venv/bin/python -m altdata.feeds check 2>&1 | tail -n 20

echo
echo "== the store move (healthy: first count > 0, second count 0)"
m=~/chester-data/.migrated
echo "  new store, files written since migration:  $(find ~/chester-data/data_store -type f -newer "$m" | wc -l)"
echo "  repo data_store, written since migration: $(find ~/chester-reports/data_store -type f -newer "$m" | wc -l)"
echo "  repo data_store, untracked/changed:        $(git status --porcelain -uall data_store | wc -l)"
