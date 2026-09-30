# Shared guard, concatenated IN FRONT of steps 4-6 on the laptop, so each step
# is still one ssh connection:
#   & "C:\Program Files\Git\bin\bash.exe" -c "cat docs/runbooks/push-day-2026-10-01/guard.inc.sh docs/runbooks/push-day-2026-10-01/04-regime-backfill.sh | ssh vps 'bash -s'"
#
# REFUSES to run inside a pass's window or while any writing unit is active.
# FORCE_WINDOW=1 skips the clock check only; the active-unit check always runs.
set -euo pipefail
cd ~/chester-reports

et_hm=$((10#$(TZ=America/New_York date +%H%M)))
et_dow=$(TZ=America/New_York date +%u)          # 1 = Monday .. 7 = Sunday
ok_window=0
if [ "$et_dow" -le 5 ]; then
  # Weekdays, ET. Outside: overnight 06:45 + anchor 07:00 + Monthly 07:30 (the
  # 1st) + heartbeat 08:30; the auction sampler 15:49; EOD 16:10 + close 16:45.
  if { [ "$et_hm" -ge 905 ] && [ "$et_hm" -le 1540 ]; } ||
     { [ "$et_hm" -ge 1720 ] && [ "$et_hm" -le 2330 ]; }; then ok_window=1; fi
else
  # Weekends: anything but the Sunday 05:00 Weekly and the 02:30 backup.
  if [ "$et_hm" -ge 600 ] && [ "$et_hm" -le 2330 ]; then ok_window=1; fi
fi
if [ "$ok_window" -ne 1 ] && [ "${FORCE_WINDOW:-0}" != "1" ]; then
  echo "REFUSED: $(TZ=America/New_York date '+%a %H:%M ET') is outside the allowed windows"
  echo "  weekdays 09:05-15:40 and 17:20-23:30 ET"
  exit 10
fi

busy=""
for u in chester-overnight chester-morning-anchor chester-monthly chester-eod \
         chester-daily-close chester-weekly chester-ibkr-sync chester-auction \
         chester-backup; do
  if systemctl --user is-active --quiet "$u.service"; then busy="$busy $u"; fi
done
if [ -n "$busy" ]; then
  echo "REFUSED: running now:$busy -- wait for it to finish"
  exit 11
fi
echo "== guard: $(TZ=America/New_York date '+%a %H:%M ET'), no writing unit active"
