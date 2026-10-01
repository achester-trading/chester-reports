#!/usr/bin/env bash
#
# The Monthly Regime & Allocation report, as the 1st-of-the-month timer runs it.
#
#   git pull --ff-only -> venv monthly_macro.run -> log -> status -> heartbeat
#
# NO CALENDAR GUARD, for the same reason the weekly has none: the 1st can be a
# Sunday and the report reads stored data. Waiting for the first business day would
# let the report's date and the month it describes disagree.
#
# IT WRITES A HEARTBEAT. A monthly that silently stops is invisible for a MONTH,
# which is long enough for the scenario weights, the Brier ledger and the pillar
# deltas to go unread without anybody noticing -- and long enough that the operator
# would find out from the absence of an email rather than from a check.
#
# THE SCHEDULER IS THIS BOX NOW. .github/workflows/monthly-report.yml lost its
# `schedule:` block when this landed and keeps workflow_dispatch as the manual
# fallback; cron-job.org is deleted by the operator on 30 September 2026.
#
# Exit codes are monthly_macro.run's, passed through -- the Weekly's set:
#   0 built, archived and delivered
#   1 the run failed -- an empty store or an unreadable one
#   2 built and ARCHIVED but NOT delivered -- the report is on disk
#
# DELIVERY (1 Oct 2026). The 1 Oct edition built and archived and nobody received
# it: this wrapper had no delivery step and its log said "built and archived" as
# though that were the whole job. The Monthly now mails itself through
# daily_cascade/deliver -- the Weekly's and the close's transport, on the SMTP
# credentials the heartbeat's alerts use -- and every run logs a `delivery=` line.
# rc=2 still stamps the heartbeat (the report exists), with state=not_delivered,
# which is what the heartbeat's anchor check reports.
#
# Overridable:
#   CHESTER_REPO           repo checkout    (~/chester-reports)
#   CHESTER_LOG_DIR        log directory    (~/logs)
#   CHESTER_STATE_DIR      status dir       -- MANDATORY, see below
#   CHESTER_PYTHON         interpreter      ($REPO/.venv/bin/python)
#   CHESTER_MONTHLY_AS_OF      point-in-time cutoff, for replaying a past month
#   CHESTER_MONTHLY_FETCH=1        pull FRED and prices first (see below)
#   CHESTER_MONTHLY_NO_NARRATIVE=1 ship the data-only edition
#   CHESTER_MONTHLY_DELIVER_ONLY=YYYY-MM-DD  re-send that archived edition and
#                                  build nothing (a missed delivery, by hand)

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"

# MANDATORY, for the reason the heartbeat scripts give at length: a status file
# written where nobody reads it is a report that looks missing. Unlike those two
# this script WRITES rather than reads, so the wrong directory loses the record
# instead of inventing an outage -- still worth refusing rather than guessing.
if [[ -z "${CHESTER_STATE_DIR:-}" ]]; then
    printf '%s\n' \
        "FATAL run_monthly.sh: CHESTER_STATE_DIR is unset, and there is no safe" \
        "default -- the status and heartbeat files must land where the monitor" \
        "reads them." \
        "  systemd:  Environment=CHESTER_STATE_DIR=%h/state (a drop-in)" \
        "  by hand:  CHESTER_STATE_DIR=\"\$HOME/state\" ./scripts/run_monthly.sh" >&2
    exit 1
fi
STATE_DIR="$CHESTER_STATE_DIR"
export CHESTER_STATE_DIR

mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/monthly-$(date +%Y).log"
STATUS="$STATE_DIR/monthly_status"
HEARTBEAT="$STATE_DIR/monthly_heartbeat"
LOCK="$STATE_DIR/monthly.lock"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

# One report per month. A second copy racing the first would write the archive and
# the snapshot twice, and next month's comparison would read whichever won.
exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another monthly run holds the lock"
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

# IT DOES NOT PULL. The Monthly carried its own FRED and yfinance fetch because a
# GitHub runner starts with an empty store and has to fill one; this box does not.
# The 06:45 overnight pass owns the pull, and the point is not the saved fetch --
# which was idempotent and cheap -- but that with two pullers a stale store could be
# either of them, and a Monthly that quietly patches over a broken overnight pass is
# how a feed outage stays invisible for a month. If the store is short, the payload
# says which series and as-of when, which is the report the operator should get.
#
# CHESTER_MONTHLY_FETCH=1 restores the pull, for a checkout with no feeds behind it.
ARGS=()
[[ -n "${CHESTER_MONTHLY_AS_OF:-}" ]] && ARGS+=(--as-of "$CHESTER_MONTHLY_AS_OF")
[[ -z "${CHESTER_MONTHLY_FETCH:-}" ]] && ARGS+=(--skip-fetch)
[[ -n "${CHESTER_MONTHLY_NO_NARRATIVE:-}" ]] && ARGS+=(--skip-narrative)
if [[ -n "${CHESTER_MONTHLY_DELIVER_ONLY:-}" ]]; then
    ARGS=(--deliver-only "$CHESTER_MONTHLY_DELIVER_ONLY")
fi

log "=== monthly start sha=$SHA pull=$PULL_STATUS ${ARGS[*]:-live}"
START=$(date +%s)
"$PY" -m monthly_macro.run "${ARGS[@]}" >>"$LOG" 2>&1
RC=$?
ELAPSED=$(( $(date +%s) - START ))

case $RC in
    0) STATE=ok;            DELIVERY="smtp ok";     MSG="monthly built, archived and delivered" ;;
    1) STATE=failed;        DELIVERY="none";        MSG="RUN FAILED -- an empty or unreadable store; see the log" ;;
    2) STATE=not_delivered; DELIVERY="smtp failed"; MSG="built and ARCHIVED but delivery failed -- the report is on disk" ;;
    *) STATE=error;         DELIVERY="none";        MSG="monthly report failed rc=$RC" ;;
esac
# A RE-SEND BUILDS NOTHING, and the log must not say it did: the 1 Oct re-send
# logged "built, archived and delivered" for a two-second run that only mailed
# the archive, which a later reader would take for a second edition.
if [[ -n "${CHESTER_MONTHLY_DELIVER_ONLY:-}" ]]; then
    case $RC in
        0) MSG="re-delivered (no build) the archived edition of $CHESTER_MONTHLY_DELIVER_ONLY" ;;
        2) MSG="re-delivery FAILED (no build) for $CHESTER_MONTHLY_DELIVER_ONLY -- the archive is unchanged" ;;
    esac
fi
log "$MSG (rc=$RC, ${ELAPSED}s)"
# The python's own `delivery=smtp ok|failed state=... -- detail` line is above in
# this log; this one is the wrapper's verdict, on one line a month greps into.
log "delivery=$DELIVERY"

printf 'state=%s rc=%s delivery=%s sha=%s pull=%s elapsed=%s at=%s\n' \
    "$STATE" "$RC" "${DELIVERY// /_}" "$SHA" "$PULL_STATUS" "$ELAPSED" \
    "$(date --iso-8601=seconds)" >"$STATUS"

# THE HEARTBEAT IS WRITTEN ONLY ON A RUN THAT PRODUCED A REPORT. Stamping it for a
# failed run would let a broken month look current for four weeks. A delivery
# failure DID produce one, so rc=2 stamps it -- with its state first, which is
# what the heartbeat's anchor check reads to report monthly=not_delivered.
if [[ "$RC" -eq 0 || "$RC" -eq 2 ]]; then
    printf '%s sha=%s rc=%s at=%s\n' "$STATE" "$SHA" "$RC" \
        "$(date --iso-8601=seconds)" >"$HEARTBEAT"
fi

exit $RC
