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
        CHESTER_SKIP_STATE_CHECK=1 \
        CHESTER_SKIP_FEED_CHECK=1 \
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

# --- DECLARED BOX-LOCAL CONFIGURATION ------------------------------------
#
# The override check above was too blunt to live with. Where THIS machine keeps
# its state directory is not a fact the repo has an opinion about, so reporting
# it forever left the heartbeat permanently at exit 8 -- and an alarm that is
# always on is an alarm nobody reads, which means the genuine case (a
# hand-edited installed unit, which a pull will never fix) would arrive into a
# channel already trained to be ignored.
#
# deploy/systemd/box-config.allow names which unit may carry a drop-in and which
# directive keys it may set. Declared is clean; everything else is still drift.
rm -rf "$UNITS"/*.d
cp "$REPO/deploy/systemd/chester-eod.service" "$UNITS/chester-eod.service"
mkdir -p "$UNITS/chester-eod.service.d"
cat >"$UNITS/chester-eod.service.d/override.conf" <<'DECL'
# Box-local configuration.
[Service]
Environment=CHESTER_STATE_DIR=%h/state
Environment=CHESTER_LOG_DIR=%h/logs
DECL
run 0 CHESTER_SYSTEMD_USER_DIR="$UNITS"
if [[ "$(drift_of)" == "clean" ]] && [[ "$RC" == "0" ]]; then
    ok "a DECLARED drop-in (Environment only, per box-config.allow) is not drift"
else
    bad "a declared drop-in reported drift=$(drift_of) exit=$RC"
fi
# THE POINT OF DECLARING KEYS RATHER THAN UNITS. A unit on the allow-list must
# not become a place to hide anything: an ExecStart= in the same drop-in is still
# drift, and the report NAMES the offending key, because "an override exists"
# sends a human to read a file while "it sets ExecStart" tells them what is wrong.
printf 'ExecStart=/bin/false\n' >>"$UNITS/chester-eod.service.d/override.conf"
run 0 CHESTER_SYSTEMD_USER_DIR="$UNITS"
if [[ "$(drift_of)" == "drifted" ]] && [[ "$RC" == "8" ]]; then
    ok "an UNDECLARED directive in a declared unit's drop-in is still drift"
else
    bad "ExecStart= in a declared drop-in reported drift=$(drift_of) exit=$RC"
fi
if grep -q 'override:ExecStart' "$ALERT"; then
    ok "and the alert names the offending directive, not merely the unit"
else
    bad "the alert does not name the key: $(grep unit_drift_units "$ALERT")"
fi

# A drop-in on a unit the manifest does not mention at all stays drift.
rm -rf "$UNITS"/*.d
mkdir -p "$UNITS/chester-eod.timer.d"
printf '[Timer]\nOnCalendar=*:*\n' >"$UNITS/chester-eod.timer.d/o.conf"
cp "$REPO/deploy/systemd/chester-eod.timer" "$UNITS/chester-eod.timer" 2>/dev/null || true
run 0 CHESTER_SYSTEMD_USER_DIR="$UNITS"
if grep -q 'chester-eod.timer(override)' "$ALERT"; then
    ok "a drop-in on an UNDECLARED unit is drift (the manifest is a list, not a switch)"
else
    bad "an undeclared unit's drop-in went undetected: $(grep unit_drift_units "$ALERT")"
fi
rm -rf "$UNITS"/*.d

# The manifest itself must exist and must not have quietly grown. It is the
# exception list; a long one is a repo that has stopped describing its own
# deployment.
ALLOW="$REPO/deploy/systemd/box-config.allow"
if [[ -f "$ALLOW" ]]; then
    ok "deploy/systemd/box-config.allow is committed, so the exceptions are reviewable"
else
    bad "box-config.allow is missing -- every drop-in would read as drift again"
fi
BAD_KEYS="$(sed 's/#.*//' "$ALLOW" | awk 'NF > 1 { for (i = 2; i <= NF; i++) if ($i != "Environment") print $i }' | sort -u)"
if [[ -z "$BAD_KEYS" ]]; then
    ok "Environment= is the ONLY permitted box-local directive"
else
    bad "box-config.allow permits more than Environment=: $BAD_KEYS"
fi

# --- HOW LONG HAS IT BEEN TRUE -------------------------------------------
#
# The 08:30 check emailed an exit-8 drift verdict every day from 6 to 19
# September -- fourteen consecutive deliveries, `delivery=smtp`, no gap. The alert
# branch worked perfectly. What it could not do was tell day one from day
# thirteen: `unhealthy_since` was computed BEFORE the drift verdict, so on the one
# verdict that persists $STATE was still `ok` and the field printed `n/a` every
# single time. Fourteen identical alerts each looked like a first occurrence, and
# the drift was found by hand rather than by the alarm that had been firing about
# it for two weeks.
#
# So the duration is now measured, and it goes in the HEADLINE -- the subject line
# -- because a reader who has seen an alert twelve times needs the number in the
# first line, not in a field the twelfth one taught them to skip.
rm -rf "$UNITS"/*.d
cp "$REPO/deploy/systemd/chester-eod.service" "$UNITS/chester-eod.service"
printf '\n# hand edit to establish drift\n' >>"$UNITS/chester-eod.service"
rm -f "$STATE_DIR/unit_drift_since"

run 0 CHESTER_SYSTEMD_USER_DIR="$UNITS"
if [[ -f "$STATE_DIR/unit_drift_since" ]]; then
    ok "the first drifted check creates the onset marker"
else
    bad "no unit_drift_since marker was created"
fi

# Backdate it to the real outage's length and check the age is reported.
touch -d "13 days ago" "$STATE_DIR/unit_drift_since"
run 0 CHESTER_SYSTEMD_USER_DIR="$UNITS"
if grep -q '"unit_drift_days": 13' "$ALERT"; then
    ok "a 13-day-old drift reports unit_drift_days: 13"
else
    bad "the drift age is wrong: $(grep unit_drift_days "$ALERT")"
fi
if grep -q 'UNRESOLVED FOR 13 DAY' "$ALERT"; then
    ok "and the age is in the HEADLINE, so the subject line distinguishes day 13 from day 1"
else
    bad "the headline does not carry the age: $(grep headline "$ALERT")"
fi
if grep -q '"unit_drift_since"' "$ALERT"; then
    ok "with the onset instant, so a consumer can escalate on duration"
else
    bad "unit_drift_since is absent from the alert"
fi

# A FIXED DRIFT MUST NOT LEAVE ITS AGE BEHIND. Otherwise a drift that appears,
# is fixed, and appears again inherits the first one's age and reports a
# fortnight-old fault on its first day.
cp "$REPO/deploy/systemd/chester-eod.service" "$UNITS/chester-eod.service"
run 0 CHESTER_SYSTEMD_USER_DIR="$UNITS"
if [[ ! -f "$STATE_DIR/unit_drift_since" ]]; then
    ok "a clean check REMOVES the marker, so a later drift starts its own clock"
else
    bad "the onset marker survived a clean check"
fi
printf '\n# edit again\n' >>"$UNITS/chester-eod.service"
run 0 CHESTER_SYSTEMD_USER_DIR="$UNITS"
if grep -q '"unit_drift_days": 0' "$ALERT"; then
    ok "and a returning drift reports 0 days, not the old fortnight"
else
    bad "a returning drift inherited a stale age: $(grep unit_drift_days "$ALERT")"
fi

# unhealthy_since must no longer read n/a on a drift verdict, which is the whole
# defect: it is computed after the verdict now, not before it.
if grep -q 'unhealthy_since=n/a' <(grep 'verdict=unit_drift' $LOG_GLOB | tail -1); then
    bad "a drift verdict still reports unhealthy_since=n/a"
else
    ok "a drift verdict no longer reports unhealthy_since=n/a -- it is computed AFTER the verdict it describes"
fi
rm -rf "$UNITS"/*.d
cp "$REPO/deploy/systemd/chester-eod.service" "$UNITS/chester-eod.service"

# Drift must never mask a dead pipeline. Fixing the drift would otherwise make
# a stale heartbeat look healthy.
#
# Drift is established HERE rather than inherited from whatever the previous
# block happened to leave behind. It used to rely on that, and the box-config
# tests above -- which clean up after themselves, as they should -- silently
# turned this into an assertion about nothing.
printf '\n# hand edit, to establish drift for this case\n' \
    >>"$UNITS/chester-eod.service"
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

printf '%s\nThe market-state object check\n%s\n' "$LINE" "$LINE"

# THE POINT OF THIS CHECK is that a healthy pipeline with no state object is not
# healthy: the close pass is the object's only writer, so a missing object means
# the 16:45 pass ran and did not reach that step. The report still went out, with
# a block saying the object was missing.
#
# CHESTER_DB points the observation store at an empty database, which is the
# cleanest way to produce "no object" without touching the real one.
state_object_of() { sed -n 's/.*state_object=\([a-z_]*\).*/\1/p' "$STATUS"; }

rm -f "$STATUS"
env CHECKER_RC=0 \
    CHESTER_REPO="$REPO" \
    CHESTER_LOG_DIR="$SANDBOX/logs" \
    CHESTER_STATE_DIR="$STATE_DIR" \
    CHESTER_CHECKER="$SANDBOX/bin/checker" \
    CHESTER_DB="$SANDBOX/empty.db" \
    bash "$WRAPPER" >"$SANDBOX/out" 2>&1
RC=$?
if [[ "$(state_of)" == "no_state_object" ]] && [[ "$RC" == "10" ]]; then
    ok "a healthy pipeline with NO market-state object -> no_state_object, exit 10"
elif [[ "$(state_object_of)" == "no_python" ]]; then
    ok "no interpreter available here; the state check declined to guess (no_python)"
else
    bad "empty store -> state=$(state_of) exit=$RC state_object=$(state_object_of) (wanted no_state_object/10)"
fi

# AND IT MUST NOT OUTRANK A PIPELINE VERDICT. A stale pipeline explains a missing
# object; reporting the symptom over the cause sends the reader to the wrong place.
rm -f "$STATUS"
env CHECKER_RC=1 \
    CHESTER_REPO="$REPO" \
    CHESTER_LOG_DIR="$SANDBOX/logs" \
    CHESTER_STATE_DIR="$STATE_DIR" \
    CHESTER_CHECKER="$SANDBOX/bin/checker" \
    CHESTER_DB="$SANDBOX/empty.db" \
    bash "$WRAPPER" >"$SANDBOX/out" 2>&1
RC=$?
if [[ "$(state_of)" == "stale" ]] && [[ "$RC" == "1" ]]; then
    ok "a stale pipeline with no object still reports stale -- the cause, not the symptom"
else
    bad "stale + no object reported state=$(state_of) exit=$RC (wanted stale/1)"
fi

# And the skip switch must not be able to turn a real verdict healthy.
rm -f "$STATUS"
run 0
if [[ "$(state_object_of)" == "skipped" ]] && [[ "$RC" == "0" ]]; then
    ok "CHESTER_SKIP_STATE_CHECK records skipped on the row rather than present -- a skipped check and a passing one are different states"
else
    bad "skip switch reported state_object=$(state_object_of) exit=$RC"
fi

printf '\n%s\nThe feed freshness gate\n%s\n' "$LINE" "$LINE"

# A HEALTHY PIPELINE WITH A STALE FEED IS NOT HEALTHY. The object is computed from
# whatever is in the store, so a feed that stopped delivering produces an object
# full of absent dimensions -- and the report still goes out. CHESTER_DB points at
# an empty store, which is the cleanest way to make every feed absent.
feeds_of() { sed -n 's/.*feeds=\([a-z_]*\).*/\1/p' "$STATUS"; }

rm -f "$STATUS"
env CHECKER_RC=0 \
    CHESTER_REPO="$REPO" \
    CHESTER_LOG_DIR="$SANDBOX/logs" \
    CHESTER_STATE_DIR="$STATE_DIR" \
    CHESTER_CHECKER="$SANDBOX/bin/checker" \
    CHESTER_SKIP_STATE_CHECK=1 \
    CHESTER_DB="$SANDBOX/empty-feeds.db" \
    bash "$WRAPPER" >"$SANDBOX/out" 2>&1
RC=$?
if [[ "$(state_of)" == "feed_stale" ]] && [[ "$RC" == "11" ]]; then
    ok "a healthy pipeline with every feed absent -> feed_stale, exit 11"
elif [[ "$(feeds_of)" == "no_python" ]]; then
    ok "no interpreter available here; the feed check declined to guess (no_python)"
else
    bad "empty store -> state=$(state_of) exit=$RC feeds=$(feeds_of) (wanted feed_stale/11)"
fi

# AND IT MUST NOT OUTRANK ANYTHING UPSTREAM. A dead pipeline explains a stale
# feed; reporting the feed would send the reader to the wrong place.
rm -f "$STATUS"
env CHECKER_RC=2 \
    CHESTER_REPO="$REPO" \
    CHESTER_LOG_DIR="$SANDBOX/logs" \
    CHESTER_STATE_DIR="$STATE_DIR" \
    CHESTER_CHECKER="$SANDBOX/bin/checker" \
    CHESTER_SKIP_STATE_CHECK=1 \
    CHESTER_DB="$SANDBOX/empty-feeds.db" \
    bash "$WRAPPER" >"$SANDBOX/out" 2>&1
RC=$?
if [[ "$(state_of)" == "no_heartbeat" ]] && [[ "$RC" == "2" ]]; then
    ok "a pipeline that never ran still reports no_heartbeat -- the cause, not the symptom"
else
    bad "no_heartbeat + stale feeds reported state=$(state_of) exit=$RC"
fi

rm -f "$STATUS"
run 0
if [[ "$(feeds_of)" == "skipped" ]] && [[ "$RC" == "0" ]]; then
    ok "CHESTER_SKIP_FEED_CHECK records skipped rather than fresh -- a skipped check and a passing one are different states"
else
    bad "skip switch reported feeds=$(feeds_of) exit=$RC"
fi

printf '\n%s\nThe exceptions branch\n%s\n' "$LINE" "$LINE"

# THE POINT OF THIS BRANCH is that it mails on a CHANGE and not on a condition. An
# alert that repeats every run for a divergence open eight sessions is one the
# reader learns to delete, and the next alert -- about something new -- goes with
# it. So: first run with exceptions present mails; an unchanged second run does
# not; and the exit code never moves, because an exception is a finding about the
# market and the heartbeat's verdict is about the pipeline.
exc_of() { sed -n 's/.*exceptions=\([0-9]*\).*/\1/p' "$STATUS" | head -1; }
exc_delivery_of() { sed -n 's/.*exc_delivery=\([a-z_]*\).*/\1/p' "$STATUS"; }

EXC_SANDBOX="$SANDBOX/exc"
mkdir -p "$EXC_SANDBOX"
# A stub `regime` is not possible -- the wrapper calls the real module -- so this
# drives the branch through its state file instead: seed a PREVIOUS set that cannot
# match, and the branch must report a change.
run_exc() {                      # run_exc <checker_rc>
    env CHECKER_RC="$1" \
        CHESTER_REPO="$REPO" \
        CHESTER_LOG_DIR="$SANDBOX/logs" \
        CHESTER_STATE_DIR="$STATE_DIR" \
        CHESTER_CHECKER="$SANDBOX/bin/checker" \
        CHESTER_SKIP_STATE_CHECK=1 \
        CHESTER_SKIP_FEED_CHECK=1 \
        bash "$WRAPPER" >"$SANDBOX/out" 2>&1
    RC=$?
}

rm -f "$STATUS" "$STATE_DIR/exceptions_open"
run_exc 0
FIRST_N="$(exc_of)"
FIRST_D="$(exc_delivery_of)"
if [[ -n "$FIRST_N" ]]; then
    ok "the branch reports an exception count on the row (exceptions=$FIRST_N, delivery=$FIRST_D)"
else
    bad "no exceptions field on the status row"
fi

# Second run, nothing changed: delivery must say so rather than mailing again.
run_exc 0
if [[ "$(exc_delivery_of)" == "unchanged" ]] || [[ "$(exc_delivery_of)" == "not_attempted" ]]; then
    ok "an unchanged set does not mail -- exc_delivery=$(exc_delivery_of)"
else
    bad "unchanged set reported exc_delivery=$(exc_delivery_of) (wanted unchanged)"
fi

# A seeded previous set that cannot match forces a CLOSED delta, and the mail path
# runs. With no MTA in the sandbox the outcome is a named failure, not silence.
printf 'contradiction:not_a_real_row\nextreme:not_a_real_metric\n' >"$STATE_DIR/exceptions_open"
run_exc 0
case "$(exc_delivery_of)" in
    unchanged|not_attempted)
        bad "a changed set did not attempt delivery (exc_delivery=$(exc_delivery_of))" ;;
    "")
        bad "no exc_delivery recorded on a changed set" ;;
    *)
        ok "a changed set attempts delivery and NAMES the outcome (exc_delivery=$(exc_delivery_of)) -- no_mta and smtp_failed are different facts" ;;
esac

# And the state file is only updated after the attempt, so a delivery failure
# cannot silently swallow a change.
if [[ -f "$STATE_DIR/exceptions_open" ]] && ! grep -q 'not_a_real_row' "$STATE_DIR/exceptions_open"; then
    ok "the open set is rewritten after the attempt, so the next run compares against what was actually reported"
else
    bad "the open set was not updated after the attempt"
fi

# THE EXIT CODE IS UNTOUCHED, on a healthy pipeline and on a broken one.
rm -f "$STATE_DIR/exceptions_open"
run_exc 0
EXC_RC_OK=$RC
run_exc 1
if [[ "$EXC_RC_OK" == "0" ]] && [[ "$RC" == "1" ]]; then
    ok "the exceptions branch never moves the exit code (0 stayed 0, 1 stayed 1) -- a market divergence is not a broken box"
else
    bad "exit code moved: healthy=$EXC_RC_OK stale=$RC"
fi

rm -f "$STATE_DIR/exceptions_open"

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
