#!/usr/bin/env bash
#
# Validation gate for scripts/check_heartbeat_cron.sh.
#
# This wrapper is the delivery path for the one alarm that says the pipeline
# died, so its failure mode is the worst kind available: it reports healthy, or
# it reports nothing, and either way the silence reads as "all clear". The
# checker itself is already covered by tools/validate_session_calendar.sh; what
# is untested is the translation from the checker's exit code into a verdict, a
# state file, an alert file and a delivery attempt.
#
# Four properties, each of which has a plausible way of being quietly wrong:
#
#   1. Every checker exit code maps to its own verdict. A collision here means
#      a stale heartbeat and a healthy one produce the same state string.
#   2. The status and alert files are written on EVERY run, healthy included.
#      A brief that only ever sees a file when something is wrong cannot
#      distinguish "all clear" from "the monitor stopped", which is the exact
#      distinction an inverted heartbeat exists to make.
#   3. last_ok is touched ONLY on a healthy check. Its age is the outage
#      length; touch it unconditionally and the outage becomes invisible.
#   4. A failed or impossible delivery is RECORDED, not swallowed. A box with
#      no MTA must say so in the log and in the alert file rather than during
#      an outage.
#
# The checker is stubbed, so this tests the wrapper's policy and never the
# calendar. Runs anywhere -- no systemd, no mail, no heartbeat.
#
#   bash tools/validate_heartbeat_caller.sh

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WRAPPER="$REPO/scripts/check_heartbeat_cron.sh"
PASS=0
FAIL=0
LINE="=============================================================================="

ok()  { printf '  PASS  %s\n' "$*"; PASS=$((PASS + 1)); }
bad() { printf '  FAIL  %s\n' "$*"; FAIL=$((FAIL + 1)); }

SANDBOX="$(mktemp -d)"
trap 'rm -rf "$SANDBOX"' EXIT
mkdir -p "$SANDBOX/logs" "$SANDBOX/state" "$SANDBOX/bin"

# --- the stub checker -------------------------------------------------------
# Exits with CHECKER_RC and prints something recognisable, standing in for
# scripts/check_heartbeat.sh without needing a heartbeat or a holiday table.
cat >"$SANDBOX/bin/checker" <<'STUB'
#!/usr/bin/env bash
echo "stub checker output rc=${CHECKER_RC:-0}"
exit "${CHECKER_RC:-0}"
STUB
chmod +x "$SANDBOX/bin/checker"

STATE_DIR="$SANDBOX/state"
STATUS="$STATE_DIR/heartbeat_check_status"
LAST_OK="$STATE_DIR/heartbeat_check_last_ok"
ALERT="$STATE_DIR/alerts/eod_heartbeat.json"
LOG_GLOB="$SANDBOX/logs/heartbeat_check-*.log"

# run <checker_rc> [extra env assignments...] -> sets RC
run() {
    local rc="$1"; shift
    env CHECKER_RC="$rc" \
        CHESTER_REPO="$REPO" \
        CHESTER_LOG_DIR="$SANDBOX/logs" \
        CHESTER_STATE_DIR="$STATE_DIR" \
        CHESTER_CHECKER="$SANDBOX/bin/checker" \
        "$@" \
        bash "$WRAPPER" >"$SANDBOX/out" 2>&1
    RC=$?
}

state_of() { sed -n 's/^state=\([a-z_]*\).*/\1/p' "$STATUS"; }

printf '%s\ncheck_heartbeat_cron.sh -- verdict mapping\n%s\n' "$LINE" "$LINE"

# --- 1. every exit code gets its own verdict, and is passed through ---------
declare -A EXPECT=([0]=ok [1]=stale [2]=no_heartbeat [3]=last_run_failed [4]=store_diverged)
for rc in 0 1 2 3 4; do
    run "$rc"
    got="$(state_of)"
    if [[ "$got" == "${EXPECT[$rc]}" ]] && [[ "$RC" == "$rc" ]]; then
        ok "checker exit $rc -> state=$got, exit passed through"
    else
        bad "checker exit $rc -> state=$got exit=$RC (wanted ${EXPECT[$rc]}/$rc)"
    fi
done

# A missing checker is the monitor being broken, which must not look like any
# pipeline verdict -- otherwise "the check could not run" reads as "the run
# failed" and somebody debugs the wrong machine.
run 0 CHESTER_CHECKER="$SANDBOX/bin/does_not_exist"
if [[ "$(state_of)" == "check_failed" ]] && [[ "$RC" == "9" ]]; then
    ok "missing checker -> state=check_failed exit=9, distinct from 1/2/3"
else
    bad "missing checker -> state=$(state_of) exit=$RC (wanted check_failed/9)"
fi

printf '\n%s\nFiles written on every run, healthy included\n%s\n' "$LINE" "$LINE"

rm -f "$STATUS" "$ALERT"; rm -rf "$STATE_DIR/alerts"
run 0
[[ -f "$STATUS" ]] && ok "healthy check writes the status file" \
                   || bad "healthy check left no status file"
[[ -f "$ALERT" ]]  && ok "healthy check writes the alert file" \
                   || bad "healthy check left no alert file -- silence is unreadable"
if grep -q '"healthy": true' "$ALERT" && grep -q '"state": "ok"' "$ALERT"; then
    ok "alert file carries healthy=true and state=ok"
else
    bad "alert file does not state the healthy verdict: $(cat "$ALERT")"
fi
if grep -q '"checked_at"' "$ALERT"; then
    ok "alert file carries checked_at, so a reader can age THIS file"
else
    bad "alert file has no checked_at -- a stale monitor would read as all-clear"
fi

rm -f "$ALERT"
run 1
if [[ -f "$ALERT" ]] && grep -q '"healthy": false' "$ALERT"; then
    ok "stale check writes the alert file with healthy=false"
else
    bad "stale check did not write a readable alert"
fi

printf '\n%s\nlast_ok is the outage clock\n%s\n' "$LINE" "$LINE"

rm -f "$LAST_OK"
run 1
[[ -f "$LAST_OK" ]] && bad "a STALE check touched last_ok -- the outage is now invisible" \
                    || ok "stale check leaves last_ok untouched"

run 0
[[ -f "$LAST_OK" ]] && ok "healthy check writes last_ok" \
                    || bad "healthy check did not write last_ok"

BEFORE="$(stat -c %Y "$LAST_OK")"
run 2
AFTER="$(stat -c %Y "$LAST_OK")"
if [[ "$BEFORE" == "$AFTER" ]]; then
    ok "a later CRITICAL check does not refresh last_ok"
else
    bad "last_ok was refreshed by a failing check -- outage length is wrong"
fi
if grep -q '"unhealthy_since"' "$ALERT" && ! grep -q '"unhealthy_since": null' "$ALERT"; then
    ok "alert reports unhealthy_since once last_ok exists"
else
    bad "alert did not report unhealthy_since: $(cat "$ALERT")"
fi

rm -f "$LAST_OK"
run 2
if grep -q 'never_healthy' "$ALERT"; then
    ok "no last_ok at all reports never_healthy, not a null gap"
else
    bad "a box that has never been healthy does not say so"
fi

printf '\n%s\nUnit drift, checked where the stale file actually lives\n%s\n' "$LINE" "$LINE"

# The repo's units were correct and the box's were not, at the same time, for a
# week: validate_systemd_units.py reads deploy/systemd/ and was green while the
# journal printed "Unknown key name ... ignoring" on every load of an installed
# unit that predated the fix. No check in this repository can assert against a
# file the repository does not ship, so the assertion has to run on the box.
UNITS="$SANDBOX/units"
mkdir -p "$UNITS"

drift_of() { sed -n 's/.*drift=\([a-z_]*\).*/\1/p' "$STATUS"; }

rm -f "$UNITS"/*.service "$UNITS"/*.timer
run 0 CHESTER_SYSTEMD_USER_DIR="$UNITS"
if [[ "$(drift_of)" == "none_installed" ]] && [[ "$RC" == "0" ]]; then
    ok "no installed units -> none_installed, not a false alarm"
else
    bad "empty unit dir reported drift=$(drift_of) exit=$RC"
fi

cp "$REPO"/deploy/systemd/*.service "$REPO"/deploy/systemd/*.timer "$UNITS/"
run 0 CHESTER_SYSTEMD_USER_DIR="$UNITS"
if [[ "$(drift_of)" == "clean" ]] && [[ "$RC" == "0" ]]; then
    ok "installed units matching the repo -> clean, exit 0"
else
    bad "identical units reported drift=$(drift_of) exit=$RC"
fi

echo "# a box-local edit" >>"$UNITS/chester-eod.service"
run 0 CHESTER_SYSTEMD_USER_DIR="$UNITS"
if [[ "$(drift_of)" == "drifted" ]] && [[ "$RC" == "8" ]]; then
    ok "a modified installed unit -> drifted, exit 8"
else
    bad "modified unit reported drift=$(drift_of) exit=$RC (wanted drifted/8)"
fi
if grep -q 'chester-eod.service(modified)' "$ALERT"; then
    ok "the alert names the unit and how it diverged"
else
    bad "the alert does not name the drifted unit"
fi

# The case that actually hid: the unit file matches perfectly and a drop-in
# changes what systemd does. A comparison of unit files alone sees nothing.
cp "$REPO/deploy/systemd/chester-eod.service" "$UNITS/chester-eod.service"
mkdir -p "$UNITS/ibgateway.service.d"
echo "[Service]" >"$UNITS/ibgateway.service.d/override.conf"
run 0 CHESTER_SYSTEMD_USER_DIR="$UNITS"
if grep -q 'ibgateway.service(override)' "$ALERT"; then
    ok "a .d/ drop-in is drift even when the unit file matches byte for byte"
else
    bad "an override.conf went undetected: $(grep unit_drift_units "$ALERT")"
fi

# Drift must never mask a dead pipeline. Fixing the drift would otherwise make
# a stale heartbeat look healthy.
run 1 CHESTER_SYSTEMD_USER_DIR="$UNITS"
if [[ "$RC" == "1" ]] && [[ "$(state_of)" == "stale" ]] && [[ "$(drift_of)" == "drifted" ]]; then
    ok "a stale pipeline outranks drift; drift is still recorded alongside it"
else
    bad "pipeline verdict was overwritten: state=$(state_of) exit=$RC drift=$(drift_of)"
fi
rm -rf "$UNITS/ibgateway.service.d"

printf '\n%s\nDelivery outcome is recorded, never swallowed\n%s\n' "$LINE" "$LINE"

# No address configured. This is the default state of a fresh box and it must
# be visible: "nobody is being told" is a finding, not a blank.
run 1
if grep -q '"delivery": "no_address"' "$ALERT" && grep -q 'delivery=no_address' $LOG_GLOB; then
    ok "unconfigured email -> delivery=no_address in both alert and log"
else
    bad "unconfigured email did not record no_address"
fi

# A working transport. Prepending the sandbox bin keeps the rest of PATH
# intact -- an earlier version of this test replaced PATH wholesale, which took
# `bash` itself out of scope so the wrapper never ran and the assertion passed
# against the PREVIOUS run's alert file. A test that cannot fail is worse than
# no test, and this one had to be caught by disbelieving a green line.
cat >"$SANDBOX/bin/mail" <<'STUB'
#!/usr/bin/env bash
echo "$*" >>"$MAIL_CALLS"
cat >>"$MAIL_CALLS"
exit "${MAIL_RC:-0}"
STUB
chmod +x "$SANDBOX/bin/mail"
export MAIL_CALLS="$SANDBOX/mail.calls"

: >"$MAIL_CALLS"
run 1 CHESTER_ALERT_EMAIL="ops@example.invalid" PATH="$SANDBOX/bin:$PATH" MAIL_RC=0
if grep -q '"delivery": "mail"' "$ALERT" && grep -q 'ops@example.invalid' "$MAIL_CALLS"; then
    ok "working transport -> delivery=mail, addressed to the configured recipient"
else
    bad "a sent mail was not recorded as sent: $(grep delivery "$ALERT")"
fi
if grep -q 'STALE' "$MAIL_CALLS" || grep -q 'stale' "$MAIL_CALLS"; then
    ok "the mail body carries the verdict, not just a subject"
else
    bad "the mail body does not name the verdict"
fi

# A transport that is present and fails. This is the failure this repo keeps
# discovering the hard way: the channel is configured, looks wired, delivers
# nothing.
: >"$MAIL_CALLS"
run 1 CHESTER_ALERT_EMAIL="ops@example.invalid" PATH="$SANDBOX/bin:$PATH" MAIL_RC=1
if grep -q '"delivery": "mail_failed"' "$ALERT"; then
    ok "a transport that exits non-zero records mail_failed, not success"
else
    bad "a failed send reported as delivered: $(grep delivery "$ALERT")"
fi

# Whatever this box actually has, the outcome is always a named one. The point
# is that "nobody was told" can never be blank.
run 1 CHESTER_ALERT_EMAIL="ops@example.invalid"
if grep -qE '"delivery": "(mail|sendmail|mail_failed|sendmail_failed|no_mta)"' "$ALERT"; then
    ok "on any box, a non-healthy verdict records a named delivery outcome"
else
    bad "delivery outcome was unnamed: $(grep delivery "$ALERT")"
fi

# A healthy check attempts no delivery unless explicitly asked, so the channel
# does not become a daily mail nobody reads.
run 0 CHESTER_ALERT_EMAIL="ops@example.invalid"
if grep -q '"delivery": "not_attempted"' "$ALERT"; then
    ok "healthy check sends nothing by default"
else
    bad "healthy check attempted a delivery: $(grep delivery "$ALERT")"
fi

run 0 CHESTER_ALERT_EMAIL="ops@example.invalid" CHESTER_ALERT_EMAIL_ALWAYS=1
if grep -qv '"delivery": "not_attempted"' "$ALERT"; then
    ok "ALWAYS=1 forces a delivery attempt on a healthy check, to prove the channel"
else
    bad "ALWAYS=1 did not force an attempt"
fi

printf '\n%s\nThe log line is greppable by verdict\n%s\n' "$LINE" "$LINE"
if grep -q 'verdict=ok ' $LOG_GLOB && grep -q 'verdict=stale ' $LOG_GLOB; then
    ok "log carries verdict=<state> so a month greps into an uptime figure"
else
    bad "log lines are not verdict-keyed"
fi
if grep -q 'heartbeat_age_h=' $LOG_GLOB; then
    ok "log carries the heartbeat age, measured by stat rather than parsed"
else
    bad "log does not carry the heartbeat age"
fi

printf '\n%s\n%d passed, %d failed\n%s\n' "$LINE" "$PASS" "$FAIL" "$LINE"
if [[ $FAIL -gt 0 ]]; then
    echo "VALIDATION FAILED"
    exit 1
fi
echo "VALIDATION PASSED"
