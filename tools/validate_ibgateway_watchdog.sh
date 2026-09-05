#!/usr/bin/env bash
#
# Validation gate for scripts/ibgateway_watchdog.sh.
#
# The watchdog RESTARTS A SERVICE, which makes its decision logic the most
# consequential shell in the repo: a wrong branch either restarts nothing when
# the Gateway is wedged, or restarts forever against credentials no restart can
# fix. Both failures are quiet. So the branches are tested rather than read.
#
# Everything is stubbed -- systemctl, flock, and the probe itself -- so this
# runs anywhere, including a Windows laptop with no systemd and no Gateway.
# It tests the POLICY, not the connection; the connection is
# tools/validate_ibkr_portfolio.py's job and the live check is the VPS's.
#
#   bash tools/validate_ibgateway_watchdog.sh

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WATCHDOG="$REPO/scripts/ibgateway_watchdog.sh"
PASS=0
FAIL=0

ok()  { printf '  PASS  %s\n' "$*"; PASS=$((PASS + 1)); }
bad() { printf '  FAIL  %s\n' "$*"; FAIL=$((FAIL + 1)); }

SANDBOX="$(mktemp -d)"
trap 'rm -rf "$SANDBOX"' EXIT
BIN="$SANDBOX/bin"
mkdir -p "$BIN" "$SANDBOX/logs" "$SANDBOX/state"

# --- stubs ----------------------------------------------------------------
# systemctl records what it was asked to do so the test can assert on it.
cat >"$BIN/systemctl" <<'STUB'
#!/usr/bin/env bash
printf '%s\n' "$*" >>"$SYSTEMCTL_CALLS"
case "$*" in
    *is-active*) [[ "${UNIT_ACTIVE:-1}" == "1" ]] && exit 0 || exit 3 ;;
    *MemoryCurrent*) echo "308281344"; exit 0 ;;
    *restart*) [[ "${RESTART_OK:-1}" == "1" ]] && exit 0 || exit 1 ;;
esac
exit 0
STUB

# flock is absent on Git Bash; the VPS has a real one and exercises it there.
printf '#!/usr/bin/env bash\nexit 0\n' >"$BIN/flock"

# The probe. Exits with whatever PROBE_RC says, standing in for the sync.
cat >"$BIN/fake_python" <<'STUB'
#!/usr/bin/env bash
echo "fake probe: rc=${PROBE_RC:-0}"
exit "${PROBE_RC:-0}"
STUB
chmod +x "$BIN/systemctl" "$BIN/flock" "$BIN/fake_python"

export SYSTEMCTL_CALLS="$SANDBOX/systemctl.calls"
export PATH="$BIN:$PATH"

# run <probe_rc> -> RC, and STATE/LOG readable afterwards
run() {
    : >"$SYSTEMCTL_CALLS"
    PROBE_RC="$1" \
    CHESTER_REPO="$REPO" \
    CHESTER_LOG_DIR="$SANDBOX/logs" \
    CHESTER_STATE_DIR="$SANDBOX/state" \
    CHESTER_PYTHON="$BIN/fake_python" \
    FAILURES_BEFORE_RESTART=3 \
    MAX_RESTARTS_PER_DAY=3 \
    UNIT_ACTIVE="${UNIT_ACTIVE:-1}" \
    RESTART_OK="${RESTART_OK:-1}" \
        bash "$WATCHDOG" >/dev/null 2>&1
    RC=$?
    HEALTH="$(cat "$SANDBOX/state/ibgateway_health" 2>/dev/null)"
    restarted() { grep -q "restart ibgateway.service" "$SYSTEMCTL_CALLS"; }
}

reset_state() { rm -f "$SANDBOX/state/ibgateway_watchdog.state" \
                      "$SANDBOX/state/ibgateway_health"; }

echo "=============================================================================="
echo "IB Gateway watchdog policy"
echo "=============================================================================="

# --- a deliberately stopped Gateway is not a fault ------------------------
reset_state
UNIT_ACTIVE=0 run 3
[[ $RC -eq 0 ]] && ok "unit inactive -> exit 0 (stopped on purpose is not a fault)" \
                || bad "unit inactive -> exit $RC, want 0"
restarted && bad "unit inactive -> must NOT restart a human's decision" \
           || ok "unit inactive -> no restart issued"
UNIT_ACTIVE=1

# --- healthy --------------------------------------------------------------
reset_state
run 0
[[ $RC -eq 0 ]] && ok "probe ok -> exit 0" || bad "probe ok -> exit $RC"
grep -q "state=ok" <<<"$HEALTH" && ok "health file says state=ok" \
                                || bad "health file: $HEALTH"

# --- hysteresis: two failures do not restart ------------------------------
reset_state
run 3
[[ $RC -eq 1 ]] && ok "failure 1 of 3 -> exit 1, watching" || bad "failure 1 -> exit $RC"
restarted && bad "failure 1 must not restart" || ok "failure 1 -> no restart"
grep -q "state=not_listening" <<<"$HEALTH" \
    && ok "exit 3 maps to not_listening (the hang signature)" \
    || bad "health: $HEALTH"
run 3
restarted && bad "failure 2 must not restart" || ok "failure 2 of 3 -> still no restart"

# --- the third consecutive failure restarts -------------------------------
run 3
restarted && ok "failure 3 of 3 -> RESTART issued" || bad "failure 3 -> no restart"
[[ $RC -eq 1 ]] && ok "restart path -> exit 1" || bad "restart path -> exit $RC"

# --- recovery clears the failure counter ----------------------------------
run 0
[[ $RC -eq 0 ]] && ok "recovery -> exit 0" || bad "recovery -> exit $RC"
run 3; restarted && bad "post-recovery failure 1 restarted immediately" \
                 || ok "recovery reset the consecutive-failure counter"

# --- the daily restart budget, and that it STOPS --------------------------
# This is the case the cap exists for: bad credentials, which no restart fixes.
reset_state
restarts=0
for i in $(seq 1 12); do
    run 5                       # signed_out, forever, as bad creds behave
    restarted && restarts=$((restarts + 1))
done
[[ $restarts -eq 3 ]] \
    && ok "12 consecutive failures -> exactly 3 restarts, then it STOPS" \
    || bad "restart budget: $restarts restarts issued, want 3"
[[ $RC -eq 2 ]] && ok "past the budget -> exit 2 (human required)" \
               || bad "past the budget -> exit $RC, want 2"
grep -q "restart suppressed" <<<"$HEALTH" \
    && ok "health file says restart suppressed" || bad "health: $HEALTH"
grep -q "config.ini" "$SANDBOX/logs"/ibgateway_watchdog-*.log \
    && ok "the log names config.ini credentials as the likely cause" \
    || bad "suppression log does not point at the real fault"

# --- signed_out is distinguished from not_listening -----------------------
reset_state
run 5
grep -q "state=signed_out" <<<"$HEALTH" \
    && ok "exit 5 maps to signed_out, distinct from not_listening" \
    || bad "health: $HEALTH"
reset_state
run 4
grep -q "state=not_responding" <<<"$HEALTH" \
    && ok "exit 4 maps to not_responding, distinct again" || bad "health: $HEALTH"

# --- a failed restart command is escalated, not swallowed -----------------
reset_state
RESTART_OK=0
run 3; run 3; run 3
[[ $RC -eq 2 ]] && ok "a FAILED restart command -> exit 2, not a silent 1" \
               || bad "failed restart -> exit $RC, want 2"
RESTART_OK=1

# --- the units themselves --------------------------------------------------
echo
echo "=============================================================================="
echo "Unit files"
echo "=============================================================================="
for u in ibgateway.service ibgateway-watchdog.timer ibgateway-restart.timer; do
    f="$REPO/deploy/systemd/$u"
    if grep -qE '^\[Install\]' "$f"; then
        bad "$u has a LIVE [Install] -- the enable gate is not held"
    else
        ok "$u has no live [Install] (enable is gated)"
    fi
done
grep -q 'America/New_York' "$REPO/deploy/systemd/ibgateway-restart.timer" \
    && ok "daily restart is pinned to America/New_York, not UTC" \
    || bad "restart timer is not zone-pinned"
grep -qE 'OnCalendar=\*-\*-\* 01:00:00' "$REPO/deploy/systemd/ibgateway-restart.timer" \
    && ok "restart at 01:00 ET -- clear of IBKR's 23:45-00:45 reset window" \
    || bad "restart time is not 01:00"
grep -q 'WATCHDOG_CLIENT_ID:-18' "$WATCHDOG" \
    && ok "watchdog probes on clientId 18, not the sync's 17" \
    || bad "watchdog shares a clientId with the sync"

# The three defects the VPS drop-in had to work around. Every one of them
# failed SILENTLY -- a wrong DISPLAY, a missing flag, and a stanza in a section
# systemd ignores. None produces an error message, which is why a real
# deployment found them and reading the file did not.
GW="$REPO/deploy/systemd/ibgateway.service"

# Anchored, so it reads the DIRECTIVE and not the comment that explains why the
# directive is absent. A check that trips on its own explanation is a check
# somebody eventually deletes.
grep -qE '^Environment=DISPLAY' "$GW" \
    && bad "DISPLAY is set by hand -- that overrides xvfb-run's own display" \
    || ok "no hand-set DISPLAY directive; xvfb-run exports its own"
grep -q 'xvfb-run' "$GW" \
    && ok "ExecStart goes through xvfb-run (a headless box has no :0)" \
    || bad "no xvfb-run -- IBC's GUI would have no X server to attach to"
grep -q 'auto-servernum' "$GW" \
    && ok "--auto-servernum picks a free display rather than assuming one" \
    || bad "xvfb-run without --auto-servernum"
grep -q 'gatewaystart.sh -inline' "$GW" \
    && ok "-inline passed: IBC stays in the foreground for Type=simple" \
    || bad "-inline missing -- gatewaystart.sh backgrounds and the unit flaps"

# StartLimit* belong in [Unit]; systemd IGNORES them under [Service], silently.
UNIT_SECTION="$(sed -n '/^\[Unit\]/,/^\[Service\]/p' "$GW")"
SVC_SECTION="$(sed -n '/^\[Service\]/,$p' "$GW")"
grep -q 'StartLimitIntervalSec' <<<"$UNIT_SECTION" \
    && ok "StartLimitIntervalSec is in [Unit], where systemd actually reads it" \
    || bad "StartLimitIntervalSec is not in [Unit]"
grep -q 'StartLimitBurst' <<<"$UNIT_SECTION" \
    && ok "StartLimitBurst is in [Unit]" || bad "StartLimitBurst is not in [Unit]"
grep -qE '^StartLimit' <<<"$SVC_SECTION" \
    && bad "a StartLimit* directive is still in [Service], where it is IGNORED" \
    || ok "no StartLimit* left in [Service] (there it would be silently ignored)"

echo
echo "=============================================================================="
echo "$PASS passed, $FAIL failed"
echo "=============================================================================="
[[ $FAIL -eq 0 ]] && { echo "VALIDATION PASSED"; exit 0; }
echo "VALIDATION FAILED"; exit 1
