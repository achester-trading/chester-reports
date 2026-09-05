#!/usr/bin/env bash
#
# Heartbeat staleness check for the EOD pass.
#
# A pipeline that stops running looks exactly like one with nothing to report,
# which is why state/emit.py already refuses to let producers claim their own
# freshness. Same principle on the box: the run writes a heartbeat only on a
# clean exit, and this reads its age. Nothing here trusts the pipeline's
# opinion of itself.
#
# WEEKEND AWARENESS. The timer runs Mon-Fri at 16:10 ET, so the gap from
# Friday's run to Monday's is ~72h and a flat 26h threshold would alarm every
# single weekend. The allowance widens on Sat, Sun, and Monday before the run
# window, and is tight the rest of the time.
#
# Exit codes, suitable for a monitor or a cron alert:
#   0 healthy · 1 stale · 2 no heartbeat at all · 3 last run failed
#
# Overridable:
#   CHESTER_STATE_DIR   (~/.chester)
#   CHESTER_MAX_AGE_H   weekday allowance in hours (26)
#   CHESTER_WEEKEND_H   weekend/Monday-morning allowance in hours (74)

set -uo pipefail

STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
HEARTBEAT="$STATE_DIR/eod_heartbeat"
STATUS="$STATE_DIR/eod_status"
MAX_AGE_H="${CHESTER_MAX_AGE_H:-26}"
WEEKEND_H="${CHESTER_WEEKEND_H:-74}"

# Decide the allowance in market time, not the box's timezone. The box may well
# run UTC; the schedule is ET, and the weekend it needs to tolerate is ET's.
ET_DOW=$(TZ=America/New_York date +%u)     # 1=Mon .. 7=Sun
ET_HOUR=$(TZ=America/New_York date +%-H)
ET_NOW=$(TZ=America/New_York date '+%Y-%m-%d %H:%M %Z')

if [[ $ET_DOW -ge 6 ]] || { [[ $ET_DOW -eq 1 ]] && [[ $ET_HOUR -lt 17 ]]; }; then
    ALLOWED_H=$WEEKEND_H
    WINDOW="weekend/Monday-morning"
else
    ALLOWED_H=$MAX_AGE_H
    WINDOW="weekday"
fi

echo "EOD heartbeat check  ($ET_NOW, $WINDOW window: ${ALLOWED_H}h)"

if [[ ! -f "$HEARTBEAT" ]]; then
    echo "  CRITICAL no heartbeat file at $HEARTBEAT"
    echo "           the EOD pass has never completed cleanly on this box"
    [[ -f "$STATUS" ]] && echo "           last status: $(cat "$STATUS")"
    exit 2
fi

NOW_EPOCH=$(date +%s)
HB_EPOCH=$(stat -c %Y "$HEARTBEAT" 2>/dev/null || echo 0)
AGE_S=$(( NOW_EPOCH - HB_EPOCH ))
AGE_H=$(( AGE_S / 3600 ))
AGE_M=$(( (AGE_S % 3600) / 60 ))

echo "  last clean run : $(TZ=America/New_York date -d "@$HB_EPOCH" '+%Y-%m-%d %H:%M %Z')"
echo "  age            : ${AGE_H}h ${AGE_M}m"
echo "  heartbeat says : $(cat "$HEARTBEAT" 2>/dev/null | tr -d '\n')"
[[ -f "$STATUS" ]] && echo "  last status    : $(cat "$STATUS" | tr -d '\n')"

# A failing run leaves the heartbeat untouched, so age alone eventually catches
# it -- but the status file knows sooner, and says why.
if [[ -f "$STATUS" ]] && grep -q '^rc=[^0]' "$STATUS" 2>/dev/null; then
    RC=$(sed -n 's/^rc=\([0-9]*\).*/\1/p' "$STATUS")
    case "$RC" in
        1) WHY="no chains captured -- the irreplaceable stage failed" ;;
        2) WHY="compute failed (chains are stored; rerun with --skip-fetch)" ;;
        3) WHY="pin scoring failed (chains and profiles are stored)" ;;
        4) WHY="ran clean but the off-box backup failed -- data has one copy" ;;
        *) WHY="unknown failure" ;;
    esac
    echo "  WARN last run exited $RC: $WHY"
    exit 3
fi

if [[ $AGE_H -gt $ALLOWED_H ]]; then
    echo "  STALE ${AGE_H}h exceeds the ${ALLOWED_H}h $WINDOW allowance"
    exit 1
fi

echo "  OK"
exit 0
