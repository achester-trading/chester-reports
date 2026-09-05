# VPS runtime install — EOD options pass

Part 25 ruling: **the VPS runs code, it never edits code.** Everything here is
pulled from the repo. The only things created on the box are directories, the
`.env` secrets file, and the two symlinks/copies systemd needs.

These are **user** units, not system units. The job runs as your user, out of
your home directory, against your `.env` — running it as root would buy nothing
and would put a secrets file in root's home.

## 1. Prerequisites on the box

```bash
sudo apt update && sudo apt install -y git python3-venv
git clone https://github.com/achester-trading/chester-reports.git ~/chester-reports
cd ~/chester-reports
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/python smoke_test.py          # no network needed; must print PASSED
```

## 2. Secrets

```bash
install -m 600 /dev/null ~/chester-reports/.env
nano ~/chester-reports/.env             # type real values; never paste keys into a chat
chmod 600 ~/chester-reports/.env        # belt and braces
```

`.env` is gitignored. It is the one file the box owns and the repo never sees.

## 3. Directories the wrapper expects

```bash
mkdir -p ~/logs ~/backups/chains ~/.chester
chmod +x ~/chester-reports/scripts/*.sh
```

## 4. Install the timer

```bash
mkdir -p ~/.config/systemd/user
cp ~/chester-reports/deploy/systemd/chester-eod.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now chester-eod.timer
```

**Enable lingering, or the timer only runs while you are logged in:**

```bash
sudo loginctl enable-linger "$USER"
```

This is the single most common way a user timer silently never fires.

## 5. Verify

```bash
systemctl --user list-timers chester-eod.timer     # check NEXT is 16:10 ET
systemctl --user cat chester-eod.timer             # confirm what is installed
systemd-analyze calendar 'Mon-Fri 16:10 America/New_York' --iterations=5
```

That last command is the one that proves DST is handled: it prints the next
five firings as real UTC instants, so you can see the hour shift across a DST
boundary rather than trusting it.

## 6. Run once by hand before trusting the timer

```bash
~/chester-reports/scripts/run_eod_cron.sh; echo "exit=$?"
tail -40 ~/logs/run_eod-$(date +%Y-%m).log
~/chester-reports/scripts/check_heartbeat.sh; echo "health=$?"
```

## Health checking

`scripts/check_heartbeat.sh` exits `0` healthy, `1` stale, `2` no heartbeat
ever, `3` last run failed.

It does not use a fixed threshold. It asks `altdata.session` when a run was
last *due* — the most recent trading session, holidays included — and allows
that gap plus `CHESTER_GRACE_H` (2h), with a floor of `CHESTER_MAX_AGE_H`
(26h). Weekends, holidays, and holiday-extended weekends all fall out of that
one calculation, so nothing needs widening by hand: the Friday-to-Tuesday gap
around Labor Day is ~96h and is healthy, while a weekday run that simply did
not happen is stale a couple of hours after its window.

If the box cannot reach the calendar (no interpreter, no checkout) it falls
back to the old fixed weekend/weekday windows and prints `NO holiday table` in
its allowance line. That line is the tell: a checker showing it is holiday-blind
and will cry stale the morning after the next market holiday.

## Market holidays

`scripts/run_eod_cron.sh` consults the same table before running. On a weekend
or an NYSE holiday it logs a `SKIP non_session` line, exits `0`, and touches
neither the heartbeat nor the status file — so a closed market looks exactly
like a Saturday to the checker rather than like a failure. Early closes
(13:00 ET) are sessions and do run; the 16:10 timer simply fires later after
the close, which is harmless for settled-OI chain data.

The table lives in `altdata/session.py` and **covers 2026 and 2027 only**. Past
its last year the guard fails *open* — it runs on unknown weekdays rather than
skipping them, because a wasted holiday fetch is cheap and a skipped real
session is unrecoverable. Extend `NYSE_HOLIDAYS` during 2027 from
<https://www.nyse.com/markets/hours-calendars>.

To force a run on a holiday (a deliberate manual rerun):

```bash
CHESTER_FORCE_RUN=1 ~/chester-reports/scripts/run_eod_cron.sh
```

To check the whole guard without waiting for a holiday:

```bash
bash ~/chester-reports/tools/validate_session_calendar.sh
```

That drives both scripts against injected dates in a sandbox — no network, no
clock changes, and the real checkout is untouched.

Wire it to whatever alerts you; a second user timer running it each morning is
the obvious next step, and is deliberately not installed here — an alerting
path nobody reads is worse than none.

## Exit codes from the pass itself

| code | meaning |
|---|---|
| 0 | clean; heartbeat touched |
| 1 | no chains captured — the irreplaceable stage failed |
| 2 | compute failed; chains are stored, rerun with `--skip-fetch` |
| 3 | pin scoring failed; chains and profiles are stored |
| 4 | ran fine but the off-box backup failed — the data has one copy |

Only `0` touches the heartbeat. `4` is deliberately not a success: the chains
cannot be re-fetched, so a single copy is not a healthy state.

## Timezone note

The box may run UTC — that is fine and expected. The timer names
`America/New_York` explicitly and `check_heartbeat.sh` evaluates its weekend
window in ET, so neither depends on the host timezone. Do **not** "fix" this by
setting the box to ET; that would make every other UTC-reasoning tool on the
machine wrong instead.
