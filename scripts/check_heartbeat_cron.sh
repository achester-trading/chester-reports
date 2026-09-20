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
#  10 no state object -> the pipeline is healthy AND the most recently completed
#                       session has no market-state object. The close pass is the
#                       only writer of it (audit §K: one object, every report
#                       reads it), so a missing object means the 16:45 pass did
#                       not reach that step -- and the 07:00 anchor, which reads
#                       and never recomputes, opens on an absent state block.
#                       Ranked below the pipeline verdicts for the same reason
#                       drift is: a stale pipeline EXPLAINS a missing object, and
#                       reporting the symptom over the cause sends the reader to
#                       the wrong place.
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
    5) STATE=morning_missed;   HEADLINE="MISSED the 07:00 morning anchor has not run -- each missed morning is a pre-open read that cannot be rebuilt" ;;
    8) STATE=unit_drift;       HEADLINE="DRIFT installed units differ from the repo" ;;
   10) STATE=no_state_object;  HEADLINE="NO STATE the last completed session has no market-state object" ;;
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

# UNHEALTHY_SINCE IS COMPUTED BELOW, AFTER THE DRIFT VERDICT.
#
# It used to be computed here, and on the one verdict that persists it was always
# wrong. Exit 8 means "the pipeline is healthy AND units have drifted", so at this
# point in the script $STATE is still `ok` -- the drift check has not run yet --
# and the first branch set UNHEALTHY_SINCE to empty, which prints as `n/a`.
#
# The box then sat at exit 8 for thirteen consecutive days, from 7 to 19 September,
# and emailed the verdict every one of them. Every email said `unhealthy_since=n/a`.
# So fourteen identical alerts each looked like a first occurrence, nothing in any
# of them said the condition was almost two weeks old, and the drift was ignored
# until it was found by hand. The alert branch worked perfectly; what it could not
# do was tell day one from day thirteen, which is the whole of why it was ignored.
#
# See the block after the drift check.

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
# A THIRD CATEGORY, ADDED BECAUSE THE SECOND WAS TOO BLUNT. Some configuration is
# genuinely box-local -- where THIS machine keeps its state directory is not a
# fact the repo has any opinion about. Reporting that forever left the heartbeat
# permanently at exit 8, and an alarm that is always on is an alarm nobody reads,
# so the real case (somebody hand-edited an installed unit, and a pull will never
# fix it) would arrive into a channel already trained to be ignored.
#
#   DECLARED  a drop-in on a unit named in deploy/systemd/box-config.allow, whose
#             every directive key is one that file permits for that unit. Counted
#             and logged, never alarmed.
#
# Undeclared is still drift, and so is a declared unit's drop-in that sets
# something the manifest does not list. A switch that merely turned the override
# check off would be worse than the noise it removed.
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

BOX_ALLOW="$UNIT_SRC/box-config.allow"
DECLARED_COUNT=0

# allowed_keys <unit> -> the directive keys the manifest permits, or empty.
# Empty means the unit is not declared at all, which is a different state from
# declared-with-no-keys and is why this prints nothing rather than failing.
allowed_keys() {
    [[ -f "$BOX_ALLOW" ]] || return 0
    sed 's/#.*//' "$BOX_ALLOW" | awk -v u="$1" '$1 == u { $1 = ""; print }'
}

# dropin_verdict <unit> -> declared | undeclared | <the first offending key>
#
# Reads every .conf in the drop-in directory and checks each directive key
# against the manifest. Section headers, comments and blank lines carry no
# directive and are skipped. A key is the text left of the first '='.
dropin_verdict() {
    local unit="$1" keys line key
    keys="$(allowed_keys "$unit")"
    [[ -n "${keys// /}" ]] || { printf 'undeclared'; return; }
    while IFS= read -r line; do
        line="${line%%#*}"
        line="$(printf '%s' "$line" | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        [[ -z "$line" ]] && continue
        case "$line" in
            '['*']') continue ;;
        esac
        key="${line%%=*}"
        key="$(printf '%s' "$key" | sed 's/[[:space:]]*$//')"
        [[ "$key" == "$line" ]] && { printf '%s' "$key"; return; }   # no '='
        case " ${keys} " in
            *" $key "*) ;;
            *) printf '%s' "$key"; return ;;
        esac
    done < <(cat "$UNIT_DST/$unit.d"/*.conf 2>/dev/null)
    printf 'declared'
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
        # nothing on its own. What the drop-in SETS decides whether it is drift.
        if compgen -G "$UNIT_DST/$unit.d/*.conf" >/dev/null 2>&1; then
            VERDICT="$(dropin_verdict "$unit")"
            case "$VERDICT" in
                declared)
                    DECLARED_COUNT=$((DECLARED_COUNT + 1))
                    log "  box-config: $unit has a DECLARED drop-in (permitted:$(allowed_keys "$unit"))"
                    ;;
                undeclared)
                    drift_note override "$unit"
                    ;;
                *)
                    # Declared unit, undeclared directive. Named, because "an
                    # override exists" sends a human to read a file while
                    # "it sets ExecStart" tells them what is wrong.
                    drift_note "override:$VERDICT" "$unit"
                    ;;
            esac
        fi
    done
    if [[ $DRIFT_COUNT -gt 0 ]]; then
        DRIFT_STATE=drifted
    elif [[ $INSTALLED -eq 0 ]]; then
        DRIFT_STATE=none_installed
    fi
    log "unit drift: $DRIFT_STATE ($INSTALLED installed, $DRIFT_COUNT divergent, $DECLARED_COUNT declared box-config)"
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

# ---- the market-state object ----------------------------------------------
#
# ON A SESSION DAY, THE LAST COMPLETED SESSION MUST HAVE AN OBJECT. The close pass
# computes it and nothing else does (audit §K: one object, one writer, every report
# reads it), so its absence is the only way to notice that the 16:45 pass ran but
# did not reach that step. The report would still have been delivered, opening on a
# state block that says the object is missing -- and a block that says nothing
# happened is a block nobody reads twice.
#
# WHY `regime show` AND NOT A FRESH COMPUTE. A monitor that computed the object in
# order to check whether it exists would create the thing it is testing for, and
# would report healthy forever. `show` reads, and exits 1 when there is nothing to
# read.
#
# A NON-SESSION DAY IS NOT A FAILURE: last_trading_session() returns the previous
# session on a Saturday, so the check asks about a day that did have a close pass.
STATE_OBJECT=unknown
STATE_SESSION=""
if [[ -x "$REPO/.venv/bin/python" ]]; then
    STATE_PY="$REPO/.venv/bin/python"
else
    STATE_PY="$(command -v python3 || command -v python || true)"
fi
if [[ -n "${CHESTER_SKIP_STATE_CHECK:-}" ]]; then
    STATE_OBJECT=skipped
elif [[ -z "$STATE_PY" ]]; then
    STATE_OBJECT=no_python
    log "  market state: no interpreter found; not checked"
else
    STATE_SESSION="$(cd "$REPO" && "$STATE_PY" -c 'from altdata import session; print(session.last_trading_session().isoformat())' 2>/dev/null || true)"
    if [[ -z "$STATE_SESSION" ]]; then
        STATE_OBJECT=no_session
        log "  market state: could not resolve the last trading session"
    elif (cd "$REPO" && "$STATE_PY" -m regime show --session "$STATE_SESSION" >/dev/null 2>&1); then
        STATE_OBJECT=present
        log "  market state: object present for $STATE_SESSION"
    else
        STATE_OBJECT=missing
        log "  market state: NO OBJECT for $STATE_SESSION -- the close pass is its"
        log "               only writer, so that step did not run"
    fi
fi

# Ranked below the pipeline verdicts AND below drift, on the argument each of
# those is ranked on: a stale pipeline explains a missing object.
if [[ "$STATE" == "ok" ]] && [[ "$STATE_OBJECT" == "missing" ]]; then
    STATE=no_state_object
    RC=10
    HEADLINE="NO STATE no market-state object for $STATE_SESSION -- the 16:45 close pass did not compute one"
fi

# ---- how long has this been true? -----------------------------------------
#
# Computed HERE, after the verdict, because the verdict is what it is about. See
# the note where this used to live.
#
# Two different durations, and the drift one needs its own marker. last_ok is
# touched on a healthy check, so on a run that is healthy-but-drifted it is NOT
# touched (the STATE check below sees unit_drift) -- which makes it a correct
# answer for "how long since the box was fully healthy". It is not an answer for
# "how long has THIS drift been present", because a drift that appears and is
# fixed and appears again would inherit the first one's age.
DRIFT_SINCE_FILE="$STATE_DIR/unit_drift_since"

if [[ "$STATE" == "ok" ]]; then
    UNHEALTHY_SINCE=""
elif [[ -f "$LAST_OK" ]]; then
    UNHEALTHY_SINCE="$(date -d "@$(stat -c %Y "$LAST_OK")" --iso-8601=seconds 2>/dev/null || echo unknown)"
else
    UNHEALTHY_SINCE="never_healthy"
fi

# The drift marker: created the first time drift is seen, removed the moment it
# is clean. Its mtime is therefore the onset, and a cleared drift cannot leave a
# stale age behind to be reported as a new one.
DRIFT_SINCE=""
DRIFT_DAYS=""
if [[ "$DRIFT_STATE" == "drifted" ]]; then
    [[ -f "$DRIFT_SINCE_FILE" ]] || printf '%s\n' "$NOW_ISO" >"$DRIFT_SINCE_FILE"
    DRIFT_EPOCH=$(stat -c %Y "$DRIFT_SINCE_FILE" 2>/dev/null || echo 0)
    if [[ "$DRIFT_EPOCH" != "0" ]]; then
        DRIFT_SINCE="$(date -d "@$DRIFT_EPOCH" --iso-8601=seconds 2>/dev/null || echo unknown)"
        DRIFT_DAYS=$(( ( $(date +%s) - DRIFT_EPOCH ) / 86400 ))
    fi
    # THE AGE GOES IN THE HEADLINE, which is the subject line of the email. A
    # reader who has seen this alert twelve times needs the number in the first
    # line, not in a field further down that the twelfth one taught them to skip.
    if [[ -n "$DRIFT_DAYS" ]] && [[ "$DRIFT_DAYS" -gt 0 ]]; then
        HEADLINE="$HEADLINE -- UNRESOLVED FOR ${DRIFT_DAYS} DAY(S)"
    fi
else
    rm -f "$DRIFT_SINCE_FILE"
fi

# ---- 1. the distinct log line ---------------------------------------------
#
# One line per check, verdict first, so `grep -c 'verdict=ok'` over a month is
# an uptime figure and `grep -v 'verdict=ok'` is the incident list. The
# checker's full output follows, indented, for the check that found something.

log "verdict=$STATE rc=$RC heartbeat_age_h=$AGE_H unhealthy_since=${UNHEALTHY_SINCE:-n/a} drift=$DRIFT_STATE drift_since=${DRIFT_SINCE:-n/a} drift_days=${DRIFT_DAYS:-0} state_object=$STATE_OBJECT -- $HEADLINE"
if [[ "$STATE" != "ok" ]]; then
    printf '%s\n' "$OUT" | sed 's/^/    /' >>"$LOG"
fi

# ---- 2. the state files ----------------------------------------------------

printf 'state=%s rc=%s heartbeat_age_h=%s drift=%s state_object=%s at=%s\n' \
    "$STATE" "$RC" "$AGE_H" "$DRIFT_STATE" "$STATE_OBJECT" "$NOW_ISO" >"$STATUS"

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
    # How long, not just what. A consumer that wants to escalate on a condition
    # that has persisted needs the duration as a number, not as prose.
    printf '  "unit_drift_since": %s,\n' \
        "$([[ -z "$DRIFT_SINCE" ]] && echo null || printf '"%s"' "$DRIFT_SINCE")"
    printf '  "unit_drift_days": %s,\n' "${DRIFT_DAYS:-0}"
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
unit drift        : ${DRIFT_STATE}${DRIFT_SINCE:+ since $DRIFT_SINCE (${DRIFT_DAYS:-0} day(s))}

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
