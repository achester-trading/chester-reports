#!/usr/bin/env bash
#
# Validation gate for the trading-calendar guard.
#
# What this proves, end to end and with no network:
#
#   1. altdata.session's table agrees with the NYSE calendar on the dates that
#      matter -- holidays, early closes (which ARE sessions), weekends, and the
#      fail-open behaviour past the table's last year.
#   2. scripts/run_eod_cron.sh takes the skip path on Labor Day 2026-09-07 and
#      the run path on Tuesday 2026-09-08, and the skip touches NEITHER the
#      heartbeat nor the status file.
#   3. scripts/check_heartbeat.sh reads the SAME table, so the Tuesday-morning
#      check after a Labor Day skip is healthy on a Friday heartbeat -- the
#      ~96h gap that a fixed 74h weekend allowance would have called STALE.
#   4. A genuinely missed weekday run is still caught. A monitor that cannot
#      fail is not a monitor.
#
# Dates are injected through CHESTER_SESSION_DATE and CHESTER_CHECK_DATE rather
# than by moving anybody's clock, so this is safe to run at any time on any box
# and gives the same answer.
#
# The wrapper runs against a sandbox HOME and a throwaway git repo; the real
# checkout is never touched and `git pull` never reaches the network. The
# interpreter is a stub that answers calendar queries for real and pretends to
# be run_eod.py for everything else, so no chain is ever fetched.
#
#   bash tools/validate_session_calendar.sh
#
# Exit 0 = every check passed. Exit 1 = at least one failed; each line says
# which. Nothing is skipped silently.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PASS=0
FAIL=0

ok()   { printf '  PASS  %s\n' "$*"; PASS=$((PASS + 1)); }
bad()  { printf '  FAIL  %s\n' "$*"; FAIL=$((FAIL + 1)); }
head_() { printf '\n%s\n' "$*"; }

# The interpreter that runs the real calendar. Prefer a venv on either layout
# -- Linux .venv/bin, Windows .venv/Scripts -- then fall back to whatever
# python3 is on PATH.
if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
    PY="$REPO_ROOT/.venv/bin/python"
elif [[ -x "$REPO_ROOT/.venv/Scripts/python.exe" ]]; then
    PY="$REPO_ROOT/.venv/Scripts/python.exe"
else
    PY="$(command -v python3 || command -v python)"
fi
[[ -n "$PY" ]] || { echo "no python interpreter found"; exit 1; }

SANDBOX="$(mktemp -d)"
trap 'rm -rf "$SANDBOX"' EXIT

# ---------------------------------------------------------------------------
# 1. The table itself
# ---------------------------------------------------------------------------
head_ "1. altdata.session trading calendar"

# expect_session <date> <yes|no> <description>
expect_session() {
    local day="$1" want="$2" what="$3" got line
    line="$(cd "$REPO_ROOT" && "$PY" -m altdata.session is-session "$day" 2>&1)"
    if [[ $? -eq 0 ]]; then got=yes; else got=no; fi
    if [[ "$got" == "$want" ]]; then
        ok "$day session=$got  $what"
    else
        bad "$day session=$got want=$want  $what  [$line]"
    fi
}

expect_session 2026-09-07 no  "Labor Day 2026 -- the date this guard exists for"
expect_session 2026-09-08 yes "Tuesday after Labor Day"
expect_session 2026-09-04 yes "the Friday before"
expect_session 2026-09-05 no  "Saturday"
expect_session 2026-09-06 no  "Sunday"
expect_session 2026-01-01 no  "New Year's Day 2026"
expect_session 2026-04-03 no  "Good Friday 2026 -- a market holiday, not a federal one"
expect_session 2026-07-03 no  "July 4 2026 observed on the preceding Friday"
expect_session 2026-11-26 no  "Thanksgiving 2026"
expect_session 2026-11-27 yes "day after Thanksgiving -- EARLY CLOSE, still a session"
expect_session 2026-12-24 yes "Christmas Eve 2026 -- early close, still a session"
expect_session 2026-12-25 no  "Christmas Day 2026"
expect_session 2027-06-18 no  "Juneteenth 2027 observed on the preceding Friday"
expect_session 2027-07-05 no  "July 4 2027 observed on the following Monday"
expect_session 2027-12-24 no  "Christmas 2027 observed on the preceding Friday"
expect_session 2029-01-01 yes "past the table -- fails OPEN, a lost session beats a wasted fetch"

EARLY="$(cd "$REPO_ROOT" && "$PY" -c "import altdata.session as s; print(s.is_early_close('2026-11-27'), s.is_trading_session('2026-11-27'))")"
if [[ "$EARLY" == "True True" ]]; then
    ok "early closes are flagged AND counted as sessions ($EARLY)"
else
    bad "early-close handling: got '$EARLY', want 'True True'"
fi

PREV="$(cd "$REPO_ROOT" && "$PY" -m altdata.session prev-session 2026-09-08)"
if [[ "$PREV" == "2026-09-04" ]]; then
    ok "prev-session 2026-09-08 -> 2026-09-04, stepping over both the weekend and Labor Day"
else
    bad "prev-session 2026-09-08 -> '$PREV', want 2026-09-04"
fi

# ---------------------------------------------------------------------------
# 2. The wrapper's skip path
# ---------------------------------------------------------------------------
head_ "2. scripts/run_eod_cron.sh"

BOX="$SANDBOX/box"
FAKE_REPO="$BOX/repo"
mkdir -p "$FAKE_REPO" "$BOX/logs" "$BOX/state" "$BOX/backups" "$SANDBOX/bin"

# A throwaway checkout: the wrapper insists on $REPO/.git, and pointing it at
# the real one would let `git pull --ff-only` run against the actual working
# tree during a test.
git init -q "$FAKE_REPO"
git -C "$FAKE_REPO" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
cp -r "$REPO_ROOT/altdata" "$FAKE_REPO/altdata"
rm -rf "$FAKE_REPO/altdata/__pycache__" "$FAKE_REPO/altdata/sources/__pycache__"

# Stand-in interpreter: real Python for calendar queries, a no-op for the run
# itself. This is what keeps the test off the network.
cat >"$SANDBOX/bin/stub_python" <<STUB
#!/usr/bin/env bash
if [[ "\${1:-}" == "-m" ]]; then
    exec "$PY" "\$@"
fi
echo "STUB run_eod.py invoked: \$*"
exit 0
STUB
chmod +x "$SANDBOX/bin/stub_python"

# Git Bash has no flock; the VPS does. Supply a permissive stand-in only where
# it is missing, so the lock path is exercised for real on Linux.
if ! command -v flock >/dev/null 2>&1; then
    printf '#!/usr/bin/env bash\nexit 0\n' >"$SANDBOX/bin/flock"
    chmod +x "$SANDBOX/bin/flock"
    PATH="$SANDBOX/bin:$PATH"
fi

# run_wrapper <ET date> -> sets WRAP_RC and WRAP_LOG
run_wrapper() {
    rm -rf "$BOX/logs" "$BOX/state"
    mkdir -p "$BOX/logs" "$BOX/state"
    CHESTER_REPO="$FAKE_REPO" \
    CHESTER_LOG_DIR="$BOX/logs" \
    CHESTER_STATE_DIR="$BOX/state" \
    CHESTER_BACKUP_DIR="$BOX/backups" \
    CHESTER_PYTHON="$SANDBOX/bin/stub_python" \
    CHESTER_SESSION_DATE="$1" \
        bash "$REPO_ROOT/scripts/run_eod_cron.sh" >/dev/null 2>&1
    WRAP_RC=$?
    WRAP_LOG="$(cat "$BOX"/logs/*.log 2>/dev/null)"
}

run_wrapper 2026-09-07
[[ $WRAP_RC -eq 0 ]] \
    && ok "Labor Day: exit 0 (a closed market is not a failure)" \
    || bad "Labor Day: exit $WRAP_RC, want 0"
grep -q 'SKIP non_session' <<<"$WRAP_LOG" \
    && ok "Labor Day: logged the non_session skip" \
    || bad "Labor Day: no 'SKIP non_session' line in the log"
grep -q 'Labor Day' <<<"$WRAP_LOG" \
    && ok "Labor Day: the log names the holiday, not just the verdict" \
    || bad "Labor Day: the skip line does not say which holiday"
[[ ! -f "$BOX/state/eod_heartbeat" ]] \
    && ok "Labor Day: heartbeat NOT touched" \
    || bad "Labor Day: heartbeat was written on a non-session day"
[[ ! -f "$BOX/state/eod_status" ]] \
    && ok "Labor Day: status NOT touched -- no fake failure state" \
    || bad "Labor Day: status was written: $(cat "$BOX/state/eod_status")"
grep -q 'STUB run_eod.py' <<<"$WRAP_LOG" \
    && bad "Labor Day: run_eod.py was invoked anyway" \
    || ok "Labor Day: run_eod.py never invoked"

LABOR_HB_ABSENT=1

run_wrapper 2026-09-08
[[ $WRAP_RC -eq 0 ]] \
    && ok "Tuesday: exit 0" \
    || bad "Tuesday: exit $WRAP_RC, want 0"
grep -q 'SKIP non_session' <<<"$WRAP_LOG" \
    && bad "Tuesday: skipped a real session" \
    || ok "Tuesday: no skip"
grep -q 'STUB run_eod.py' <<<"$WRAP_LOG" \
    && ok "Tuesday: run_eod.py invoked" \
    || bad "Tuesday: run_eod.py was never invoked"
[[ -f "$BOX/state/eod_heartbeat" ]] \
    && ok "Tuesday: heartbeat touched" \
    || bad "Tuesday: heartbeat missing after a clean run"
grep -q '^rc=0' "$BOX/state/eod_status" 2>/dev/null \
    && ok "Tuesday: status records rc=0" \
    || bad "Tuesday: status is $(cat "$BOX/state/eod_status" 2>/dev/null)"

# The forced override, so a manual holiday rerun stays possible.
rm -rf "$BOX/logs" "$BOX/state"; mkdir -p "$BOX/logs" "$BOX/state"
CHESTER_REPO="$FAKE_REPO" CHESTER_LOG_DIR="$BOX/logs" CHESTER_STATE_DIR="$BOX/state" \
CHESTER_BACKUP_DIR="$BOX/backups" CHESTER_PYTHON="$SANDBOX/bin/stub_python" \
CHESTER_SESSION_DATE=2026-09-07 CHESTER_FORCE_RUN=1 \
    bash "$REPO_ROOT/scripts/run_eod_cron.sh" >/dev/null 2>&1
grep -q 'STUB run_eod.py' "$BOX"/logs/*.log 2>/dev/null \
    && ok "CHESTER_FORCE_RUN=1 overrides the guard on a holiday" \
    || bad "CHESTER_FORCE_RUN=1 did not force the run"

# ---------------------------------------------------------------------------
# 3. The checker's allowance
# ---------------------------------------------------------------------------
head_ "3. scripts/check_heartbeat.sh"

CHECK_STATE="$SANDBOX/check_state"
mkdir -p "$CHECK_STATE"

# check_at <heartbeat ET instant> <check ET instant> -> CHK_RC, CHK_OUT
check_at() {
    rm -f "$CHECK_STATE/eod_heartbeat" "$CHECK_STATE/eod_status"
    printf 'ok test\n' >"$CHECK_STATE/eod_heartbeat"
    touch -d "$(TZ=America/New_York date -d "$1" '+%Y-%m-%d %H:%M:%S %z')" \
        "$CHECK_STATE/eod_heartbeat"
    CHK_OUT="$(CHESTER_STATE_DIR="$CHECK_STATE" CHESTER_REPO="$FAKE_REPO" \
        CHESTER_CHECK_DATE="$2" \
        bash "$REPO_ROOT/scripts/check_heartbeat.sh" 2>&1)"
    CHK_RC=$?
}

# The checker resolves its interpreter as $REPO/.venv/bin/python or python3.
# On a box where neither exists it would take the fallback path and this
# section would prove nothing, so say so rather than pass vacuously.
if [[ -x "$FAKE_REPO/.venv/bin/python" ]] || command -v python3 >/dev/null 2>&1; then
    mkdir -p "$FAKE_REPO/.venv/bin"
    cp "$SANDBOX/bin/stub_python" "$FAKE_REPO/.venv/bin/python" 2>/dev/null || true

    # Friday 2026-09-04 16:15 ET heartbeat, checked Tuesday 2026-09-08 09:00 ET.
    # That is an 88h-old heartbeat on a perfectly healthy box: Monday was Labor
    # Day. The old fixed 74h weekend window called this STALE.
    check_at "2026-09-04 16:15" "2026-09-08 09:00"
    if [[ $CHK_RC -eq 0 ]]; then
        ok "Tuesday 09:00 after a Labor Day skip: healthy on Friday's heartbeat"
    else
        bad "Tuesday after Labor Day: exit $CHK_RC, want 0"
        printf '%s\n' "$CHK_OUT" | sed 's/^/        /'
    fi
    grep -q 'due after the 2026-09-04 session' <<<"$CHK_OUT" \
        && ok "checker names the session the run was actually due after" \
        || bad "checker did not derive 2026-09-04 as the due session: $(head -2 <<<"$CHK_OUT" | tr '\n' ' ')"

    # Same holiday-aware allowance must still catch a real miss: Tuesday ran,
    # Wednesday did not, checked Thursday morning.
    check_at "2026-09-08 16:15" "2026-09-10 09:00"
    [[ $CHK_RC -eq 1 ]] \
        && ok "a genuinely missed Wednesday run is still STALE (exit 1)" \
        || bad "missed Wednesday: exit $CHK_RC, want 1"

    # An ordinary weekday, an hour after a clean run.
    check_at "2026-09-08 16:15" "2026-09-08 18:00"
    [[ $CHK_RC -eq 0 ]] \
        && ok "ordinary weekday, fresh heartbeat: healthy" \
        || bad "ordinary weekday: exit $CHK_RC, want 0"

    # Saturday on Friday's heartbeat -- the case the original weekend window
    # existed for, which must not regress.
    check_at "2026-09-04 16:15" "2026-09-05 10:00"
    [[ $CHK_RC -eq 0 ]] \
        && ok "Saturday on Friday's heartbeat: healthy" \
        || bad "Saturday: exit $CHK_RC, want 0"
else
    bad "no interpreter for the checker to read the calendar with -- section skipped"
fi


head_ "4. dual-write divergence is its own verdict"

# altdata/store.py swallows a SQLite failure so it cannot cost the CSV write
# that already succeeded, and appends to ~/.chester/dual_write_failed instead.
# If the checker did not read that record the swallow would be silent again --
# which is the defect, not the fix. A fresh heartbeat must NOT report OK while
# the two stores disagree.
DW_SB="$(mktemp -d)"
mkdir -p "$DW_SB/state"
printf 'rc=0 sha=test at=%s\n' "$(date --iso-8601=seconds)" >"$DW_SB/state/eod_heartbeat"
CHESTER_REPO="$REPO_ROOT" CHESTER_STATE_DIR="$DW_SB/state" \
    bash "$REPO_ROOT/scripts/check_heartbeat.sh" >/dev/null 2>&1
rc_clean=$?
printf '2026-01-01T00:00:00Z fred.vix OperationalError: database is locked\n' \
    >"$DW_SB/state/dual_write_failed"
out_div="$(CHESTER_REPO="$REPO_ROOT" CHESTER_STATE_DIR="$DW_SB/state" \
    bash "$REPO_ROOT/scripts/check_heartbeat.sh" 2>&1)"
rc_div=$?
rm -rf "$DW_SB"

[[ $rc_clean -eq 0 ]] \
    && ok "a fresh heartbeat with no dual-write record is healthy (exit 0)" \
    || bad "a clean box reported exit $rc_clean"
[[ $rc_div -eq 4 ]] \
    && ok "a recorded dual-write failure -> exit 4, distinct from stale/failed" \
    || bad "divergence reported exit $rc_div, wanted 4"
grep -q "DIVERGED" <<<"$out_div" \
    && ok "the checker names the divergence" \
    || bad "the divergence verdict is not in the output"
grep -q "dual_write_failed" <<<"$out_div" \
    && ok "and names the file to clear once the pull is re-run" \
    || bad "the output does not say how to clear it"

# ---------------------------------------------------------------------------
head_ "$PASS passed, $FAIL failed"
if [[ $FAIL -eq 0 ]]; then
    echo "VALIDATION PASSED"
    exit 0
fi
echo "VALIDATION FAILED"
exit 1
