#!/usr/bin/env bash
#
# The Alpha Lab's nightly loop (X-1.9, X-1.10), as chester-alpha-nightly.timer
# runs it.
#
#   git pull --ff-only -> calendar guard -> venv alpha.loops.nightly -> log -> status
#
# 17:40 ET, AFTER THE DAILY CLOSE'S CAPTURE. The 16:45 close pass
# (run_daily_close.sh) pulls the settled prices and computes the session's
# market-state object -- the bars the lab fills against and the dials its
# attribution keys on. It runs within TimeoutStartSec=10min, so it is done by
# 16:56 at the latest; the Portfolio Truth sync's last slot is 17:30. 17:40 is
# after both, and before the 17:50 self-deploy tick.
#
# NEVER INSIDE A REPORT'S RUN, AND NEVER A REPORT'S FAILURE. This loop reads the
# observation store read-only and writes alpha.db only. A failure is written to
# alpha.db's loop_events by the loop itself and to this wrapper's status file;
# no report reads either to decide anything.
#
# THE CALENDAR GUARD, the same one-call question run_daily_close.sh asks: on a
# holiday there is no new bar to fill against or mark at. Exit 0, log the skip.
#
# Exit codes are the loop's: 0 every step ran, 1 a step failed (see loop_events).
#
# Overridable:
#   CHESTER_REPO          repo checkout           (~/chester-reports)
#   CHESTER_LOG_DIR       log directory           (~/logs)
#   CHESTER_STATE_DIR     status dir              (~/.chester)
#   CHESTER_PYTHON        interpreter             ($REPO/.venv/bin/python)
#   CHESTER_SESSION_DATE  evaluate the guard against this ET date
#   CHESTER_FORCE_RUN=1   run even on a non-session day

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"

mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/alpha_nightly-$(date +%Y-%m).log"
STATUS="$STATE_DIR/alpha_nightly_status"
LOCK="$STATE_DIR/alpha_nightly.lock"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

# One loop at a time: two would fill the same pending signals twice.
exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another nightly loop holds the lock"
    exit 0
fi

if [[ ! -d "$REPO/.git" ]]; then
    log "FATAL no git checkout at $REPO"
    printf 'state=no_repo at=%s\n' "$(date --iso-8601=seconds)" >"$STATUS"
    exit 1
fi
cd "$REPO" || { log "FATAL cannot cd $REPO"; exit 1; }

git pull --ff-only >>"$LOG" 2>&1 || log "WARN git pull --ff-only failed; running the checkout as it is"
SHA="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"

PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
if [[ ! -x "$PY" ]]; then
    log "FATAL no interpreter at $PY"
    printf 'state=no_venv sha=%s at=%s\n' "$SHA" "$(date --iso-8601=seconds)" >"$STATUS"
    exit 1
fi

SESSION_ARG="${CHESTER_SESSION_DATE:-}"
GUARD_LINE="$("$PY" -m altdata.session is-session ${SESSION_ARG:+"$SESSION_ARG"} 2>&1)"
GUARD_RC=$?
case $GUARD_RC in
    0) log "calendar ok -- $GUARD_LINE" ;;
    1)
        if [[ "${CHESTER_FORCE_RUN:-}" == "1" ]]; then
            log "non_session but CHESTER_FORCE_RUN=1 -- running anyway ($GUARD_LINE)"
        else
            log "SKIP non_session -- $GUARD_LINE (status untouched)"
            exit 0
        fi
        ;;
    *) log "WARN calendar guard unusable (rc=$GUARD_RC: $GUARD_LINE) -- running anyway" ;;
esac

log "=== alpha nightly start sha=$SHA"
"$PY" -m alpha.loops.nightly >>"$LOG" 2>&1
RC=$?
STATE=ok
[[ $RC -ne 0 ]] && STATE=failed
printf 'state=%s rc=%s sha=%s at=%s\n' "$STATE" "$RC" "$SHA" \
    "$(date --iso-8601=seconds)" >"$STATUS"
log "=== alpha nightly end rc=$RC"
exit "$RC"
