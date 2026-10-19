#!/usr/bin/env bash
#
# The weekly restore test (audit-leftovers-1): chester-restore-test.service runs
# this on Sundays, after the night's backup, once the operator has enabled the
# timer (it is NOT in DEPLOY_TIMERS: enabled before the encrypted backup exists, it
# could only fail).
#
# It pulls the newest db/ snapshot THROUGH THE CRYPT REMOTE (scripts/
# rclone_crypt_env.sh) into a temporary directory, decompresses it, runs PRAGMA
# integrity_check, and compares its observations count with the count the sweep
# recorded at snapshot time ($STATE_DIR/backup_snapshot). It writes
#     $STATE_DIR/restore_test_status   state=restore_ok|restore_failed at= ...
# which the heartbeat's backup field reads. It is the system's one restore check
# (ruling 6, 19 Oct 2026: it superseded the monthly drill). NO git pull -- the
# test should prove the backup with the code that is on the box.
# $STATE_DIR is CHESTER_STATE_DIR: ~/state on this box, through the unit's
# declared drop-in (ruling 7, 19 Oct 2026); ~/.chester only by default.

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
STATUS="$STATE_DIR/restore_test_status"
mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/restore_test-$(date +%Y-%m).log"

fail() {   # fail <detail>: the status line the heartbeat reads, then exit 1
    printf 'state=restore_failed at=%s snapshot=none detail=%s\n' \
        "$(date --iso-8601=seconds)" "$1" >"$STATUS"
    printf '%s restore test FAILED: %s\n' "$(date --iso-8601=seconds)" "$1" >>"$LOG"
    echo "restore test: $1"
    exit 1
}

cd "$REPO" || fail "cannot cd $REPO"
PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
[[ -x "$PY" ]] || fail "no interpreter at $PY"
command -v rclone >/dev/null 2>&1 || fail "rclone is not installed"
# shellcheck source=scripts/rclone_crypt_env.sh
. "$REPO/scripts/rclone_crypt_env.sh"
crypt_env || fail "$CRYPT_ERR"

OUT="$("$PY" -m tools.restore_drill --remote "$CRYPT_REMOTE" \
        --expect "$STATE_DIR/backup_snapshot" --status "$STATUS" 2>&1)"
RC=$?
{ printf '%s restore test rc=%s\n' "$(date --iso-8601=seconds)" "$RC"
  printf '%s\n' "$OUT" | sed 's/^/  /'; } >>"$LOG"
printf '%s\n' "$OUT"
exit $RC
