#!/usr/bin/env bash
#
# The restore drill's wrapper (AUD-2 item 5): chester-restore-drill.service runs
# this, monthly, once the operator has enabled the timer.
#
# Deliberately thinner than the report wrappers: NO git pull. The drill's unit
# holds the checkout read-only, and the drill should test the backup with the
# code that is on the box, not change it first. The output goes to the journal
# and to a monthly log; the exit code is the drill's own (0 restorable, 1 no
# remote or no rclone, 2 no snapshot or a failed check).

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/restore_drill-$(date +%Y-%m).log"

cd "$REPO" || { echo "FATAL cannot cd $REPO"; exit 1; }
PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
[[ -x "$PY" ]] || { echo "FATAL no interpreter at $PY"; exit 1; }

# audit-leftovers-1: the backup is encrypted, so the drill reads it through the
# crypt remote (scripts/rclone_crypt_env.sh) unless a --remote is given.
if [[ $# -eq 0 ]] && command -v rclone >/dev/null 2>&1; then
    # shellcheck source=scripts/rclone_crypt_env.sh
    . "$REPO/scripts/rclone_crypt_env.sh"
    if crypt_env; then
        set -- --remote "$CRYPT_REMOTE"
    else
        echo "restore drill: $CRYPT_ERR"
        exit 1
    fi
fi
OUT="$("$PY" -m tools.restore_drill "$@" 2>&1)"
RC=$?
{ printf '%s restore drill rc=%s\n' "$(date --iso-8601=seconds)" "$RC"
  printf '%s\n' "$OUT" | sed 's/^/  /'; } >>"$LOG"
printf '%s\n' "$OUT"
exit $RC
