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
# NON-SESSION AWARENESS. The timer runs Mon-Fri at 16:10 ET, so the gap from
# Friday's run to Monday's is ~72h and a flat 26h threshold would alarm every
# single weekend. Market holidays make that worse, not merely longer: Labor Day
# stretches Friday-to-Tuesday to ~96h, which a fixed "weekend" allowance of 74h
# would call STALE on a box that is behaving perfectly.
#
# So the allowance is not a table of special cases, it is derived. Ask the
# calendar -- altdata.session, the same holiday table run_eod_cron.sh consults
# before deciding to skip -- when the last run was actually DUE, and allow that
# gap plus a grace period. Weekends, holidays, and holiday-extended weekends
# all fall out of the one calculation, and a genuinely missed weekday run is
# caught a couple of hours after its window instead of a day later.
#
# The old fixed windows survive as the fallback for a box that cannot reach the
# calendar (no interpreter, no checkout). That path is weekend-aware only, and
# says so in its output rather than quietly being less careful.
#
# DUAL-WRITE FAILURES ARE A HEALTH FACT TOO. altdata/store.py writes every
# series to the CSV store and to SQLite; a SQLite failure there is deliberately
# swallowed so it cannot cost the CSV write that already succeeded, and it
# appends a line to ~/.chester/dual_write_failed instead. That file existing
# means the two stores have DIVERGED -- the CSV has rows the database does not
# -- which is a data-integrity failure that no amount of heartbeat freshness
# would reveal, because the run that caused it exited 0.
#
# Exit codes, suitable for a monitor or a cron alert:
#   0 healthy · 1 stale · 2 no heartbeat at all · 3 last run failed
#   4 the pipeline is fresh but the CSV and SQLite stores have diverged
#
# Overridable:
#   CHESTER_STATE_DIR   (~/.chester)
#   CHESTER_REPO        checkout to read the calendar from (~/chester-reports)
#   CHESTER_MAX_AGE_H   floor on the allowance, in hours (26)
#   CHESTER_GRACE_H     slack past the moment a run was due, in hours (2)
#   CHESTER_WEEKEND_H   fallback-only weekend allowance in hours (74)
#   CHESTER_CHECK_DATE  evaluate against this ET instant ("YYYY-MM-DD HH:MM")
#                       instead of now, for testing

set -uo pipefail

STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
REPO="${CHESTER_REPO:-$HOME/chester-reports}"
HEARTBEAT="$STATE_DIR/eod_heartbeat"
STATUS="$STATE_DIR/eod_status"
DUAL_WRITE="$STATE_DIR/dual_write_failed"
MAX_AGE_H="${CHESTER_MAX_AGE_H:-26}"
GRACE_H="${CHESTER_GRACE_H:-2}"
WEEKEND_H="${CHESTER_WEEKEND_H:-74}"

# Evaluate in market time, not the box's timezone. The box may well run UTC;
# the schedule is ET, and the calendar it has to respect is the exchange's.
FAKE_NOW="${CHESTER_CHECK_DATE:-}"
if [[ -n "$FAKE_NOW" ]]; then
    NOW_EPOCH=$(TZ=America/New_York date -d "$FAKE_NOW" +%s)
else
    NOW_EPOCH=$(date +%s)
fi
ET_DOW=$(TZ=America/New_York date -d "@$NOW_EPOCH" +%u)     # 1=Mon .. 7=Sun
ET_HOUR=$(TZ=America/New_York date -d "@$NOW_EPOCH" +%-H)
ET_DATE=$(TZ=America/New_York date -d "@$NOW_EPOCH" +%F)
ET_NOW=$(TZ=America/New_York date -d "@$NOW_EPOCH" '+%Y-%m-%d %H:%M ET')

# The interpreter that owns the holiday table. Preferring the venv keeps this
# on the same Python the pipeline runs; python3 is enough for a stdlib module.
CAL_PY=""
if [[ -x "$REPO/.venv/bin/python" ]]; then
    CAL_PY="$REPO/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    CAL_PY="python3"
fi

# Which session should have produced the newest heartbeat? Today's, once
# today's 16:10 run has had time to finish; otherwise the last session before
# today. A non-session today -- Saturday or Labor Day alike -- takes the same
# branch, which is precisely the "treat a skipped holiday like a weekend"
# behaviour the wrapper's skip path depends on.
DUE_SESSION=""
if [[ -n "$CAL_PY" ]] && [[ -d "$REPO" ]]; then
    if [[ $ET_HOUR -ge 17 ]] && (cd "$REPO" && "$CAL_PY" -m altdata.session is-session "$ET_DATE" >/dev/null 2>&1); then
        DUE_SESSION="$ET_DATE"
    else
        DUE_SESSION=$( (cd "$REPO" && "$CAL_PY" -m altdata.session prev-session "$ET_DATE") 2>/dev/null )
    fi
    # Anything unexpected on stdout means the calendar did not answer; an empty
    # DUE_SESSION drops us into the fallback rather than into date arithmetic
    # on a garbage string.
    [[ "$DUE_SESSION" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || DUE_SESSION=""
fi

if [[ -n "$DUE_SESSION" ]]; then
    # Runs start at 16:10 ET and take minutes, so 17:00 is when one is owed.
    DUE_EPOCH=$(TZ=America/New_York date -d "$DUE_SESSION 17:00" +%s)
    GAP_H=$(( (NOW_EPOCH - DUE_EPOCH) / 3600 ))
    [[ $GAP_H -lt 0 ]] && GAP_H=0
    ALLOWED_H=$(( GAP_H + GRACE_H ))
    [[ $ALLOWED_H -lt $MAX_AGE_H ]] && ALLOWED_H=$MAX_AGE_H
    WINDOW="due after the $DUE_SESSION session"
elif [[ $ET_DOW -ge 6 ]] || { [[ $ET_DOW -eq 1 ]] && [[ $ET_HOUR -lt 17 ]]; }; then
    ALLOWED_H=$WEEKEND_H
    WINDOW="fallback weekend/Monday-morning, NO holiday table"
else
    ALLOWED_H=$MAX_AGE_H
    WINDOW="fallback weekday, NO holiday table"
fi

echo "EOD heartbeat check  ($ET_NOW)"
echo "  allowance      : ${ALLOWED_H}h  ($WINDOW)"

if [[ ! -f "$HEARTBEAT" ]]; then
    echo "  CRITICAL no heartbeat file at $HEARTBEAT"
    echo "           the EOD pass has never completed cleanly on this box"
    [[ -f "$STATUS" ]] && echo "           last status: $(cat "$STATUS")"
    exit 2
fi

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
    echo "  STALE ${AGE_H}h exceeds the ${ALLOWED_H}h allowance ($WINDOW)"
    exit 1
fi

# Freshness was the only question this file used to answer. It is not the only
# way the store can be wrong: a swallowed dual-write leaves the CSV and SQLite
# copies divergent while every run exits 0 and the heartbeat stays warm.
# Reported LAST, so a stale or failed pipeline still wins the verdict -- that is
# the more urgent fault, and collapsing the two would let fixing one hide the
# other.
if [[ -s "$DUAL_WRITE" ]]; then
    DW_N=$(wc -l <"$DUAL_WRITE" | tr -d ' ')
    echo "  DIVERGED ${DW_N} dual-write failure(s) recorded"
    echo "           last: $(tail -1 "$DUAL_WRITE")"
    echo "           the CSV store has rows the database does not. Re-run the"
    echo "           affected pull, then clear $DUAL_WRITE"
    exit 4
fi

echo "  OK"
exit 0
