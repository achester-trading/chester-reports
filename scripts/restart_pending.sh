#!/usr/bin/env bash
#
# THE RESTART-PENDING LEDGER (A-4, 9 Oct 2026). One file, three verbs:
#
#     restart_pending.sh <state_dir> record <unit>...   a deploy copied these while running
#     restart_pending.sh <state_dir> prune              drop the lines that are resolved
#     restart_pending.sh <state_dir> list               print the units still pending
#
# WHY IT EXISTS. daemon-reload re-reads a unit file, but an ACTIVE unit keeps
# running the old one -- a live timer keeps its computed next-elapse, a running
# service keeps its old ExecStart. A deploy that copies a running unit is therefore
# incomplete until somebody restarts it, and no deploy here may: the restart is the
# operator's (CLAUDE.md, "What runs without asking"). The laptop deploy says so by
# exiting 3 to a human who is watching. The box's self-deploy has nobody watching,
# so it writes the fact HERE, and the 08:30 heartbeat names it in its verdict until
# it is resolved.
#
# THE FILE is $STATE_DIR/alerts/restart_pending, beside the heartbeat's own alert,
# one line per unit:
#
#     restart pending: <unit> copied_at=<epoch> (<iso>) commit=<sha>
#
# RESOLVED, and only then dropped, when the unit is no longer active (its next
# start loads the new file) or became active AFTER the copy (somebody restarted
# it). Read live from systemd every time -- never from the file alone, which only
# says what was true when the deploy wrote it. A timestamp that cannot be read
# keeps the line: an unanswerable question is not a resolution.
#
# READS systemd and NEVER CHANGES IT: is-active and show are the only verbs, and
# tools/validate_deploy.py group I holds that line by line.

set -uo pipefail

STATE_DIR="${1:?usage: restart_pending.sh <state_dir> record|prune|list [unit...]}"
VERB="${2:?usage: restart_pending.sh <state_dir> record|prune|list [unit...]}"
shift 2
FILE="$STATE_DIR/alerts/restart_pending"

# resolved <unit> <copied_epoch> -> 0 when the unit no longer runs the old file
resolved() {
    local unit="$1" copied="$2" enter enter_s
    systemctl --user is-active --quiet "$unit" 2>/dev/null || return 0
    enter="$(systemctl --user show -p ActiveEnterTimestamp --value "$unit" 2>/dev/null)"
    [[ -z "$enter" ]] && return 1
    enter_s="$(date -d "$enter" +%s 2>/dev/null)" || return 1
    [[ "$enter_s" -gt "$copied" ]]
}

# pending_lines -> the file's lines whose unit is not yet resolved
pending_lines() {
    [[ -f "$FILE" ]] || return 0
    local line unit copied
    while IFS= read -r line; do
        unit="$(printf '%s\n' "$line" | sed -n 's/^restart pending: \([^ ]*\) .*/\1/p')"
        copied="$(printf '%s\n' "$line" | sed -n 's/.* copied_at=\([0-9]*\).*/\1/p')"
        [[ -z "$unit" || -z "$copied" ]] && continue
        resolved "$unit" "$copied" || printf '%s\n' "$line"
    done <"$FILE"
}

case "$VERB" in
    record)
        [[ $# -eq 0 ]] && exit 0
        mkdir -p "$STATE_DIR/alerts" || exit 1
        now_s="$(date +%s)"
        now_iso="$(date -d "@$now_s" --iso-8601=seconds)"
        sha="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
        tmp="$(mktemp)"
        # A unit recorded again replaces its old line: the newer copy is the one
        # a restart has to come after.
        if [[ -f "$FILE" ]]; then
            grep -v -F -f <(printf 'restart pending: %s \n' "$@") "$FILE" >"$tmp" || true
        fi
        for u in "$@"; do
            printf 'restart pending: %s copied_at=%s (%s) commit=%s\n' \
                "$u" "$now_s" "$now_iso" "$sha" >>"$tmp"
        done
        mv "$tmp" "$FILE"
        ;;
    prune)
        [[ -f "$FILE" ]] || exit 0
        tmp="$(mktemp)"
        pending_lines >"$tmp"
        if [[ -s "$tmp" ]]; then mv "$tmp" "$FILE"; else rm -f "$tmp" "$FILE"; fi
        ;;
    list)
        pending_lines | sed -n 's/^restart pending: \([^ ]*\) .*/\1/p'
        ;;
    *)
        echo "restart_pending.sh: unknown verb $VERB (record|prune|list)" >&2
        exit 2
        ;;
esac
exit 0
