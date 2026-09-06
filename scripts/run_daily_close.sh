#!/usr/bin/env bash
#
# The 16:30 close debrief, as the VPS timer runs it.
#
#   git pull --ff-only -> calendar guard -> venv close_report -> log -> status
#
# TWENTY MINUTES AFTER THE EOD PASS, AND THAT SPACING IS THE DESIGN. The 16:10
# run fetches chains, computes the dealer surface, scores the pin log and
# writes the store. This fetches nothing at all (30.4 -- reports never fetch);
# it reads what that produced. So a failure here is a report-layer failure and
# nothing else, which is exactly why 32.4 makes this the first cascade run to
# be built.
#
# THE CALENDAR GUARD, same table as run_eod_cron.sh. On a holiday the EOD pass
# skips, so there is no new session to debrief -- and a report that arrived
# anyway would show the previous session's numbers under today's date, which is
# worse than no report because it is a report that looks fine. Exit 0, touch
# nothing, log the skip, same as a Saturday.
#
# NO HEARTBEAT. Unlike run_eod_cron.sh this writes no heartbeat file, because a
# missed report is not a missed capture: the data it reads is already stored and
# the report can be regenerated for any past session with --session. There is
# nothing irreplaceable to alarm about. The status file still records the last
# outcome so a gap stays visible.
#
# Exit codes are close_report.py's, passed through:
#   0 report built (and delivered, or dry-run)
#   1 no payload -- nothing computed for the session; the EOD pass is the
#     place to look, not this one
#   2 built and archived but DELIVERY FAILED -- the report exists on disk
#
# Overridable:
#   CHESTER_REPO          repo checkout           (~/chester-reports)
#   CHESTER_LOG_DIR       log directory           (~/logs)
#   CHESTER_STATE_DIR     status dir              (~/.chester)
#   CHESTER_PYTHON        interpreter             ($REPO/.venv/bin/python)
#   CHESTER_SESSION_DATE  evaluate the guard against this ET date
#   CHESTER_FORCE_RUN=1   run even on a non-session day
#   CHESTER_CLOSE_DRY_RUN=1  build and archive, send nothing

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"

mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/daily_close-$(date +%Y-%m).log"
STATUS="$STATE_DIR/daily_close_status"
LOCK="$STATE_DIR/daily_close.lock"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

# One report per session. A second copy racing the first would email twice and
# write the archive twice, and the reader would have no way to tell which.
exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another close report holds the lock"
    exit 0
fi

if [[ ! -d "$REPO/.git" ]]; then
    log "FATAL no git checkout at $REPO"
    printf 'state=no_repo at=%s\n' "$(date --iso-8601=seconds)" >"$STATUS"
    exit 1
fi
cd "$REPO" || { log "FATAL cannot cd $REPO"; exit 1; }

PULL_STATUS=ok
git pull --ff-only >>"$LOG" 2>&1 || PULL_STATUS=failed
SHA="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"

PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
if [[ ! -x "$PY" ]]; then
    log "FATAL no interpreter at $PY"
    printf 'state=no_venv sha=%s at=%s\n' "$SHA" "$(date --iso-8601=seconds)" >"$STATUS"
    exit 1
fi

# --- the calendar guard ---------------------------------------------------
# Asked AFTER the pull, so the box decides with the freshest holiday table it
# can have (Part 25). Fails OPEN: if the guard cannot answer, run and send --
# a redundant report costs an email, a suppressed one costs the day's record.
#
# ONE call, exactly as run_eod_cron.sh does it: `is-session` prints the reason
# and carries the verdict in its exit code, so nothing is parsed and the two
# wrappers cannot drift into asking the calendar different questions.
SESSION_ARG="${CHESTER_SESSION_DATE:-}"
GUARD_LINE="$("$PY" -m altdata.session is-session ${SESSION_ARG:+"$SESSION_ARG"} 2>&1)"
GUARD_RC=$?

case $GUARD_RC in
    0)
        log "calendar ok -- $GUARD_LINE"
        ;;
    1)
        if [[ "${CHESTER_FORCE_RUN:-}" == "1" ]]; then
            log "non_session but CHESTER_FORCE_RUN=1 -- running anyway ($GUARD_LINE)"
        else
            # Status untouched, so the last REAL run's verdict survives the
            # holiday. A quiet Monday must not erase a Friday failure.
            log "SKIP non_session -- $GUARD_LINE (status untouched)"
            exit 0
        fi
        ;;
    *)
        log "WARN calendar guard unusable (rc=$GUARD_RC: $GUARD_LINE) -- running anyway"
        ;;
esac

DRY=""
[[ "${CHESTER_CLOSE_DRY_RUN:-0}" == "1" ]] && DRY="--dry-run"

log "=== close report start sha=$SHA pull=$PULL_STATUS ${DRY:-live}"
"$PY" -m daily_cascade.close_report $DRY >>"$LOG" 2>&1
RC=$?

case $RC in
    0) STATE=ok;            MSG="report built and delivered" ;;
    1) STATE=no_payload;    MSG="NO PAYLOAD -- nothing computed for the session; check the EOD pass" ;;
    2) STATE=not_delivered; MSG="built and ARCHIVED but delivery failed -- the report is on disk" ;;
    *) STATE=error;         MSG="close report failed rc=$RC" ;;
esac
log "$MSG"

printf 'state=%s rc=%s sha=%s at=%s\n' \
    "$STATE" "$RC" "$SHA" "$(date --iso-8601=seconds)" >"$STATUS"

exit $RC
