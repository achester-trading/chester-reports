#!/usr/bin/env bash
#
# The heartbeat check, as a VPS timer runs it -- the missing caller.
#
# scripts/check_heartbeat.sh has existed since the calendar work and nothing has
# ever run it. That is the whole defect: run_eod_cron.sh writes the heartbeat
# faithfully on every clean exit, and no process on the box ever reads it. The
# inverted-heartbeat design says the ABSENCE of a signal raises the alarm, and
# an absence nobody looks for is not an alarm, it is a silence. The EOD pass
# could fail every night for six weeks exactly as the system narrative describes
# and the first symptom would be a report with a hole in it.
#
# So this is deliberately thin. It runs the checker, and then does the three
# things the checker cannot do for itself:
#
#   1. a DISTINCT LOG LINE, one per check, greppable by verdict
#   2. a STATE FILE whose age is readable -- heartbeat_check_last_ok is touched
#      only when the box is healthy, so its age IS the length of the outage,
#      the same trick sync_ibkr.sh uses for ibkr_sync_last_success
#   3. a MACHINE-READABLE ALERT the morning brief will read when D4 lands, at a
#      path fixed now so the Backdrop block has something to point at
#
# ...and then tries email, if the box can send it.
#
# THIS ONE DOES NOT GIT PULL, and that is deliberate. run_eod_cron.sh and
# sync_ibkr.sh both pull before running, per Part 25. A monitor is different: it
# must depend on as little of the machinery it watches as possible. A pull that
# hangs or fails would become a heartbeat failure, which is a monitor reporting
# on itself. The checker reads a local file and a local holiday table; it needs
# no fresher code than the box already has, and the EOD wrapper pulls anyway.
#
# EXIT CODES ARE THE CHECKER'S, PASSED THROUGH. Each maps to a different fix:
#   0 healthy
#   1 stale          -> the EOD pass has not completed inside its allowance
#   2 no heartbeat   -> it has NEVER completed cleanly on this box
#   3 last run failed-> it ran and exited non-zero; the status file says why
#   4 store diverged  -> the pipeline is fresh, but altdata/store.py recorded a
#                       swallowed dual-write failure: the CSV store has rows the
#                       database does not. Every run involved exited 0, which is
#                       exactly why this needs a channel of its own.
#   8 unit drift     -> the pipeline is healthy AND an installed systemd unit
#                       differs from its deploy/systemd/ copy, or carries a
#                       drop-in override. Reported here rather than in CI
#                       because no check in the repo can see a file the repo
#                       does not ship -- which is how the box ran a stale
#                       ibgateway.service for a week while the gate stayed
#                       green. A pipeline verdict always wins over this one.
#   9 check failed   -> the wrapper could not run the checker (env problem).
#                       Distinct from the four above: this is the monitor
#                       broken, not the pipeline.
#
# The unit declares SuccessExitStatus=0 ONLY, so 1/2/3/4/8/9 leave the unit in
# systemd's failed state on purpose. `systemctl --user list-units --failed` is
# a free fourth delivery channel and this is the one job where a red light is
# the product. That is the opposite of chester-ibkr-sync.service, which marks
# its failure codes as success -- there, the sync reporting a down Gateway is
# a working sync; here, the check reporting a dead pipeline is the alarm.
#
# Overridable:
#   CHESTER_REPO         repo checkout            (~/chester-reports)
#   CHESTER_LOG_DIR      log directory            (~/logs)
#   CHESTER_STATE_DIR    heartbeat/status dir     (~/.chester)
#   CHESTER_ALERT_DIR    alert drop for the brief ($CHESTER_STATE_DIR/alerts)
#   CHESTER_ALERT_EMAIL  address to mail on a non-healthy verdict (unset = none;
#                        falls back to SMTP_TO from the environment)
#   SMTP_USER/SMTP_PASSWORD/SMTP_HOST/SMTP_PORT   direct SMTP, used in
#                        preference to a local MTA when both are present
#   CHESTER_ALERT_EMAIL_ALWAYS=1   mail the healthy verdict too, for one day,
#                        to prove the channel works before trusting its silence
#   CHESTER_CHECK_DATE   passed through to the checker, for testing
#   CHESTER_CHECKER      checker path ($REPO/scripts/check_heartbeat.sh)
#   CHESTER_SYSTEMD_USER_DIR  installed units (~/.config/systemd/user)

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
ALERT_DIR="${CHESTER_ALERT_DIR:-$STATE_DIR/alerts}"
CHECKER="${CHESTER_CHECKER:-$REPO/scripts/check_heartbeat.sh}"
# SMTP_TO is the address the .env already carries for this box, so an
# operator who configured SMTP does not also have to restate the recipient.
# CHESTER_ALERT_EMAIL still wins where both are set.
ALERT_EMAIL="${CHESTER_ALERT_EMAIL:-${SMTP_TO:-}}"

mkdir -p "$LOG_DIR" "$STATE_DIR" "$ALERT_DIR"
LOG="$LOG_DIR/heartbeat_check-$(date +%Y-%m).log"
STATUS="$STATE_DIR/heartbeat_check_status"
LAST_OK="$STATE_DIR/heartbeat_check_last_ok"
ALERT="$ALERT_DIR/eod_heartbeat.json"
HEARTBEAT="$STATE_DIR/eod_heartbeat"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

NOW_ISO="$(date --iso-8601=seconds)"

# ---- run the checker -------------------------------------------------------
#
# No lock. The check is read-only and takes under a second; two overlapping
# copies would each write the same verdict, which is harmless, and a lock here
# would only add a way for the monitor to skip itself.

if [[ ! -x "$CHECKER" ]]; then
    RC=9
    OUT="no checker at $CHECKER"
else
    OUT="$("$CHECKER" 2>&1)"
    RC=$?
fi

case $RC in
    0) STATE=ok;               HEADLINE="OK the EOD pass is inside its allowance" ;;
    1) STATE=stale;            HEADLINE="STALE the EOD pass has not completed inside its allowance" ;;
    2) STATE=no_heartbeat;     HEADLINE="CRITICAL the EOD pass has NEVER completed cleanly on this box" ;;
    3) STATE=last_run_failed;  HEADLINE="FAILED the last EOD run exited non-zero -- see eod_status" ;;
    4) STATE=store_diverged;   HEADLINE="DIVERGED the CSV and SQLite stores disagree -- a dual-write failed" ;;
    8) STATE=unit_drift;       HEADLINE="DRIFT installed units differ from the repo" ;;
    9) STATE=check_failed;     HEADLINE="BROKEN the heartbeat check itself could not run" ;;
    *) STATE=unknown;          HEADLINE="UNKNOWN checker exited $RC" ;;
esac

# ---- the numbers, measured here rather than parsed out of the checker's prose
#
# The checker prints an age for a human. Reading it back with sed would couple
# this file to that file's output format, which is the kind of coupling that
# breaks quietly the first time someone improves the wording. stat is the fact.

if [[ -f "$HEARTBEAT" ]]; then
    HB_EPOCH=$(stat -c %Y "$HEARTBEAT" 2>/dev/null || echo 0)
    AGE_H=$(( ( $(date +%s) - HB_EPOCH ) / 3600 ))
    HB_AT="$(date -d "@$HB_EPOCH" --iso-8601=seconds 2>/dev/null || echo unknown)"
else
    AGE_H=-1
    HB_AT="never"
fi

# How long has the box been unhealthy? The age of last_ok, which is only ever
# touched on a healthy check. Absent means it has never been healthy here.
if [[ "$STATE" == "ok" ]]; then
    UNHEALTHY_SINCE=""
elif [[ -f "$LAST_OK" ]]; then
    UNHEALTHY_SINCE="$(date -d "@$(stat -c %Y "$LAST_OK")" --iso-8601=seconds 2>/dev/null || echo unknown)"
else
    UNHEALTHY_SINCE="never_healthy"
fi

# ---- the unit drift check --------------------------------------------------
#
# WHY THIS LIVES IN THE HEARTBEAT AND NOT IN CI. The repo's units were correct
# and the box's were not, at the same time, for days. `validate_systemd_units.py`
# reads deploy/systemd/ and was green throughout; the journal was printing
# "Unknown key name ... ignoring" on every load of an installed unit that
# predated the fix. Nothing in this repository can assert against a file it does
# not ship, so the assertion has to run where the stale file is.
#
# Two kinds of divergence, and the second is the one that hid for a week:
#
#   DRIFT     an installed unit whose bytes differ from deploy/systemd/. The box
#             is running something the repo did not write, and `git pull` will
#             never fix it because a pull does not touch ~/.config/systemd/user.
#   OVERRIDE  a <unit>.d/ drop-in. The unit file matches perfectly and systemd
#             is still doing something else -- an override.conf is invisible to
#             any comparison of the unit file alone, which is precisely how a
#             box-local workaround outlives the defect it worked around.
#
# NOT drift: a unit in deploy/systemd/ with no installed copy. Most of them are
# deliberately not installed -- the whole enable gate depends on that -- so
# reporting it would train the reader to ignore this section.
#
# Comparison is `cmp -s` on the bytes. A semantic diff would need a systemd
# parser and would forgive whitespace; whitespace in a unit file is not
# meaningful to systemd but a byte difference is still a file the repo did not
# write, and "close enough" is how the installed copy drifted in the first
# place.

UNIT_SRC="$REPO/deploy/systemd"
UNIT_DST="${CHESTER_SYSTEMD_USER_DIR:-$HOME/.config/systemd/user}"
DRIFT_COUNT=0
DRIFT_NAMES=""
DRIFT_STATE=clean

drift_note() {           # drift_note <kind> <unit>
    DRIFT_COUNT=$((DRIFT_COUNT + 1))
    DRIFT_NAMES="${DRIFT_NAMES:+$DRIFT_NAMES }$2($1)"
    log "  DRIFT $1: $2"
}

if [[ ! -d "$UNIT_DST" ]]; then
    DRIFT_STATE=no_unit_dir
    log "unit drift: no installed-unit directory at $UNIT_DST"
elif [[ ! -d "$UNIT_SRC" ]]; then
    DRIFT_STATE=no_repo_units
    log "unit drift: no repo unit directory at $UNIT_SRC"
else
    INSTALLED=0
    for src in "$UNIT_SRC"/*.service "$UNIT_SRC"/*.timer; do
        [[ -e "$src" ]] || continue
        unit="$(basename "$src")"
        dst="$UNIT_DST/$unit"
        [[ -e "$dst" ]] || continue          # not installed is not drift
        INSTALLED=$((INSTALLED + 1))
        if ! cmp -s "$src" "$dst"; then
            drift_note modified "$unit"
        fi
        # A drop-in wins over the unit file, so a matching unit file proves
        # nothing on its own.
        if compgen -G "$UNIT_DST/$unit.d/*.conf" >/dev/null 2>&1; then
            drift_note override "$unit"
        fi
    done
    if [[ $DRIFT_COUNT -gt 0 ]]; then
        DRIFT_STATE=drifted
    elif [[ $INSTALLED -eq 0 ]]; then
        DRIFT_STATE=none_installed
    fi
    log "unit drift: $DRIFT_STATE ($INSTALLED installed, $DRIFT_COUNT divergent)"
fi

# Drift does NOT overwrite the pipeline verdict. A dead pipeline is more urgent
# than a stale unit file, and collapsing the two would mean fixing the drift
# made the pipeline look healthy. So the verdict stays the checker's, and drift
# only speaks when the checker had nothing to say:
#
#   exit 8  the pipeline is healthy AND units have drifted
#
# 8 is outside the checker's 0-3 and distinct from 9 (the monitor itself broke),
# so `systemctl --user list-units --failed` goes red for a reason that can be
# read off the exit code alone.
if [[ "$STATE" == "ok" ]] && [[ "$DRIFT_STATE" == "drifted" ]]; then
    STATE=unit_drift
    RC=8
    HEADLINE="DRIFT installed units differ from the repo: $DRIFT_NAMES"
fi

# ---- 1. the distinct log line ---------------------------------------------
#
# One line per check, verdict first, so `grep -c 'verdict=ok'` over a month is
# an uptime figure and `grep -v 'verdict=ok'` is the incident list. The
# checker's full output follows, indented, for the check that found something.

log "verdict=$STATE rc=$RC heartbeat_age_h=$AGE_H unhealthy_since=${UNHEALTHY_SINCE:-n/a} drift=$DRIFT_STATE -- $HEADLINE"
if [[ "$STATE" != "ok" ]]; then
    printf '%s\n' "$OUT" | sed 's/^/    /' >>"$LOG"
fi

# ---- 2. the state files ----------------------------------------------------

printf 'state=%s rc=%s heartbeat_age_h=%s drift=%s at=%s\n' \
    "$STATE" "$RC" "$AGE_H" "$DRIFT_STATE" "$NOW_ISO" >"$STATUS"

if [[ "$STATE" == "ok" ]]; then
    printf 'state=ok rc=0 heartbeat_age_h=%s at=%s\n' "$AGE_H" "$NOW_ISO" >"$LAST_OK"
fi

# ---- 3. the alert file the morning brief will read -------------------------
#
# JSON, at a path fixed now, because D4's Backdrop block should not have to
# parse a log or invent a location. Written on EVERY check including healthy
# ones: a brief that only sees a file when something is wrong cannot tell "all
# clear" from "the monitor stopped running", and that distinction is the entire
# point of an inverted heartbeat. The brief reads `checked_at` and applies its
# own staleness rule to THIS file, exactly as it would to any other source.

python_json() {
    printf '{\n'
    printf '  "source": "chester-heartbeat",\n'
    printf '  "state": "%s",\n' "$STATE"
    printf '  "exit_code": %s,\n' "$RC"
    printf '  "healthy": %s,\n' "$([[ "$STATE" == "ok" ]] && echo true || echo false)"
    printf '  "headline": "%s",\n' "$HEADLINE"
    printf '  "checked_at": "%s",\n' "$NOW_ISO"
    printf '  "heartbeat_at": "%s",\n' "$HB_AT"
    printf '  "heartbeat_age_hours": %s,\n' "$AGE_H"
    printf '  "unhealthy_since": %s,\n' \
        "$([[ -z "$UNHEALTHY_SINCE" ]] && echo null || printf '"%s"' "$UNHEALTHY_SINCE")"
    printf '  "unit_drift": "%s",\n' "$DRIFT_STATE"
    printf '  "unit_drift_count": %s,\n' "$DRIFT_COUNT"
    printf '  "unit_drift_units": "%s",\n' "$DRIFT_NAMES"
    printf '  "delivery": "%s"\n' "$1"
    printf '}\n'
}

# ---- the notification channel ---------------------------------------------
#
# Cheapest thing that exists on a stock box. Attempted only on a non-healthy
# verdict, because a daily "everything is fine" mail is a mail nobody reads by
# week three, and an unread channel is worse than no channel -- it feels like
# coverage. CHESTER_ALERT_EMAIL_ALWAYS=1 forces one through so the channel can
# be PROVEN before its silence is trusted.
#
# DELIVERY OUTCOME IS RECORDED, not assumed. A notification path that fails
# quietly is this repo's signature defect -- five silently-ignored systemd
# directives and counting -- so "there is no MTA on this box" lands in the log
# and in the alert file rather than being discovered during an outage.

DELIVERY=not_attempted
if [[ "$STATE" != "ok" ]] || [[ "${CHESTER_ALERT_EMAIL_ALWAYS:-0}" == "1" ]]; then
    if [[ -z "$ALERT_EMAIL" ]]; then
        DELIVERY=no_address
    else
        SUBJECT="[chester] EOD heartbeat: $STATE"
        BODY="$HEADLINE

checked at        : $NOW_ISO
heartbeat state   : $STATE (checker exit $RC)
last clean run    : $HB_AT (${AGE_H}h ago)
unhealthy since   : ${UNHEALTHY_SINCE:-n/a}

--- checker output ---
$OUT"
        # DIRECT SMTP FIRST, when it is configured. Not because it is better
        # than a local MTA -- it is worse, it holds a password in the process
        # environment -- but because an operator who put SMTP credentials in
        # .env chose this path deliberately, and a half-configured local MTA
        # that accepts mail and drops it is exactly the silent channel this
        # whole block exists to refuse. Explicit configuration beats whatever
        # happens to be on PATH.
        if [[ -n "${SMTP_USER:-}" && -n "${SMTP_PASSWORD:-}" ]]; then
            # Secrets travel in the environment, never in argv: argv is world-
            # readable through `ps` for the life of the call.
            SMTP_RCPT="$ALERT_EMAIL" SMTP_SUBJECT="$SUBJECT" SMTP_BODY="$BODY" \
                python3 "$REPO/scripts/send_smtp_alert.py" 2>>"$LOG"
            case $? in
                0) DELIVERY=smtp ;;
                1) DELIVERY=smtp_unconfigured ;;
                *) DELIVERY=smtp_failed ;;
            esac
        elif command -v mail >/dev/null 2>&1; then
            if printf '%s\n' "$BODY" | mail -s "$SUBJECT" "$ALERT_EMAIL" 2>>"$LOG"; then
                DELIVERY=mail
            else
                DELIVERY=mail_failed
            fi
        elif command -v sendmail >/dev/null 2>&1; then
            if { printf 'To: %s\nSubject: %s\n\n%s\n' \
                    "$ALERT_EMAIL" "$SUBJECT" "$BODY"; } \
                 | sendmail -t 2>>"$LOG"; then
                DELIVERY=sendmail
            else
                DELIVERY=sendmail_failed
            fi
        else
            DELIVERY=no_mta
        fi
    fi
    log "delivery=$DELIVERY to=${ALERT_EMAIL:-none}"
fi

python_json "$DELIVERY" >"$ALERT"

# stdout for `systemctl --user status` and for a human running it by hand.
printf '%s\n' "$OUT"
printf 'verdict=%s delivery=%s alert=%s\n' "$STATE" "$DELIVERY" "$ALERT"

exit $RC
