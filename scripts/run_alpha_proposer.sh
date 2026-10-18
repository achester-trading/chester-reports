#!/usr/bin/env bash
#
# The Alpha Lab's daily proposer (X-2.10b; change order 10.2 a), as
# chester-alpha-proposer.timer runs it.
#
#   git pull --ff-only -> calendar guard -> venv alpha_proposer -> log -> status
#
# 18:10 ET, AFTER THE NIGHTLY LOOP. One model call over a code-built observation
# packet; at most three hypotheses, written as ONE batch file into
# ~/chester-data/inbox/lab with a manifest line, for the next nightly loop to
# ingest. It reads the store and alpha.db read-only and writes nothing else but
# its own decision log (~/logs/alpha_proposer-YYYY-MM.jsonl).
#
# THE CALENDAR GUARD, the same one-call question the nightly wrapper asks: on a
# holiday there is no session to propose from. Exit 0, log the skip.
#
# Exit codes are the proposer's: 0 written / skipped / nothing to write, 1 the
# call failed or the batch failed its own checks (see the decision log).
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
export CHESTER_LOG_DIR="$LOG_DIR"

mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/alpha_proposer-$(date +%Y-%m).log"
STATUS="$STATE_DIR/alpha_proposer_status"
LOCK="$STATE_DIR/alpha_proposer.lock"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

# One proposer at a time: two would race on the day's batch file.
exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another proposer run holds the lock"
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

log "=== alpha proposer start sha=$SHA"
"$PY" -m alpha_proposer >>"$LOG" 2>&1
RC=$?
STATE=ok
[[ $RC -ne 0 ]] && STATE=failed
printf 'state=%s rc=%s sha=%s at=%s\n' "$STATE" "$RC" "$SHA" \
    "$(date --iso-8601=seconds)" >"$STATUS"
log "=== alpha proposer end rc=$RC"
exit "$RC"
