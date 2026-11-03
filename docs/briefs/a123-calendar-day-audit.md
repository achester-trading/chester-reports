# A123: the calendar-day audit (3 Nov 2026)

Session A. Branch `a119-clock-burn-down-1` at A122's tip (`2f87ca2c`); paste
committed first as `docs/pastes/A123.md`. **Read-only: this brief is the only
file changed, and no decision is taken. The Doctrine #2 sitting (7-8 Nov)
rules.**

## The window is 19:00-24:00 ET this winter, not 20:00

The box runs on UTC. Its "today" is the UTC date, so for part of every evening
it is already on tomorrow's date. How long that part lasts depends on daylight
saving:
- **EDT (summer), UTC-4:** the UTC date turns over at 20:00 ET, which is the
  paste's window.
- **EST (since 1 Nov 2026), UTC-5:** it turns over at **19:00 ET**, so the
  window is 19:00-24:00 ET until 14 Mar 2027.

Every row below uses the winter window.

## What was read

1. **`session.local_today()`, A119's helper:** 21 call sites in the modules A119
   converted (this branch).
2. **The 8 modules A119 left OUT,** read on origin/a105-merge-week-rehearsal-2.
   Nothing there was changed.
3. **Every other read in the code under test that yields a date:**
   `utc_now().date()`, a UTC instant sliced to a date, `utc_stamp()`. tools/ is
   excluded: gates are not box outputs.
4. **The shell's `date` in scripts/.**
5. **Every systemd timer** in `deploy/systemd/`. All are written in
   `America/New_York`, so they fire at ET wall times.

**What a verdict means:**
- **handled**: the site already uses the ET date (`session_date()`, or
  `TZ=America/New_York date`), or uses the UTC day on purpose.
- **harmless**: the UTC date is either equal to the ET date when the site runs,
  or a one-day difference changes nothing a reader sees.
- **wrong**: the ET date is meant, and the UTC date can reach an output in the
  window.

## The table

| # | Module:line | What the date is used for | Meant | What the box writes 19:00-24:00 ET | Verdict |
|---|---|---|---|---|---|
| 1 | alpha/report.py:446 | the Lab report CLI's default month | ET | runs at 07:30 on the 1st (the Monthly passes it): same date | harmless |
| 2 | altdata/basis_proxy.py:493 | the ledger's run date (file name, header) | ET | operator CLI, not scheduled; an evening run would name tomorrow | harmless (not in the window) |
| 3-4 | altdata/chain_metrics.py:496, 534 | a CLI window's start (`days` back) | either | one day's shift in a look-back | harmless |
| 5 | altdata/claims.py:155 | default as-of when none is passed | ET | read by the close (16:45) and the Weekly: same date | harmless |
| 6 | altdata/events_ingest.py:166 | the year for a calendar line printed without one | ET | runs in the 16:10 EOD pass; only 31 Dec evening could differ | harmless |
| 7 | altdata/fomc_audit.py:174 | `--today` default | ET | the heartbeat passes `CHESTER_FOMC_AUDIT_TODAY` from `TZ=America/New_York date +%F` | handled |
| 8 | altdata/fred_history.py:255 | the current vintage's date in an ALFRED request | ET (US) | operator backfill, not scheduled; an evening run would ask a vintage dated tomorrow | harmless (not in the window) |
| 9-11 | altdata/fx_charts.py:117, 247, 400 | the cache's age, the 5.6-year window, the caption date | ET | `make figures` on the laptop (ET): same date | harmless |
| 12 | altdata/ledgers/__init__.py:231 | a ledger edition's run date (file name) | ET | written by sessions on the laptop (ET) | harmless |
| 13 | altdata/meme_ingest.py:319 | the status line's "today" (unexpired drafts, refusal window) | ET | printed by the 07:00 anchor and the 16:45 close only; the 21:15 ingest writes instants | harmless |
| 14 | altdata/paper_bid.py:239 | a CLI window's start | either | one day's shift | harmless |
| 15 | altdata/report/signals.py:235 | an empty panel's as-of fallback | ET | content, not a pipeline (nothing schedules it) | harmless |
| 16-17 | altdata/report/__main__.py:41, 50 | the output file names | ET | content, not a pipeline | harmless |
| 18 | altdata/sources/statcan_cpi.py:133 | the request's end month | either | a month too far on a month's last evening returns nothing extra | harmless |
| 19 | altdata/sources/upcoming_auctions.py:61 | the request window's start (7 days back) | either | one day's shift | harmless |
| 20-21 | altdata/voices.py:846, 863 | CLI defaults (`--end`, the `since` window) | either | operator CLI | harmless |
| 22 | altdata/events.py:473 (OUT) | the CLI's default `since` | either | operator CLI | harmless |
| 23 | **altdata/security_master.py:99 (OUT), `_day(None)`** | **the as-of date `resolve()` uses when none is given: an identifier names an instrument only inside its window** | **ET** | **an undated resolve in the window uses tomorrow's date. The only scheduled job there that pulls is the evening note's fetch (21:30). Impact only on a ticker-change day, when the new listing starts "the day after the previous snapshot"** | **wrong (rare)** |
| 24-25 | altdata/sources/aaii.py:191, 293 (OUT) | a future-date guard (+7 days) | either | one day on a seven-day tolerance | harmless |
| 26 | altdata/sources/fed_calendar.py:53 (OUT) | which calendar entries are upcoming | ET | called only from the events ingest in the 16:10 EOD pass | harmless |
| 27 | altdata/sources/voices_scan.py:838 (OUT) | the year-ago bound on a source's history | either | reached by the evening note's voices pass; one day on 365 | harmless |
| 28-29 | altdata/sources/_crypto.py:42, llama.py:282 | the UTC day, deliberately (crypto's daily bars close at 00:00 UTC) | UTC | the UTC day, as meant | handled |
| 30-31 | altdata/sources/massive_chain.py:400, options_chain.py:247 | a chain file's tag, `utc_stamp()` (`...Z`) | an instant | an instant marked Z, not a date | harmless |
| 32 | scripts/rclone_sync.sh:167 (`TODAY`: the run log, the alpha snapshot, the retention `--today`) and :242 (the db snapshot's name) | the nightly sweep's file names and its retention cut | ET | runs at 02:30 ET (07:30 UTC): **the same date**. Only a manual evening run would be named tomorrow, consistently across its log, snapshots and retention | harmless |
| 33 | scripts/ibgateway_watchdog.sh:119-127 (`RESTART_DAY`) | the per-day restart counter | either | every 5 minutes: the counter resets at 19:00 ET, not at midnight ET | harmless |
| 34 | 24 wrappers' log names, `$(date +%Y-%m)` (or `+%Y`) | which monthly log a line goes to | either | on a month's last evening, that evening's lines go to next month's log (the evening note, meme ingest, self-deploy, watchdog, heartbeat cron) | harmless |
| 35 | scripts/check_heartbeat.sh:87-90, 121, 228 | the verdict's date, hour, weekday | ET | `TZ=America/New_York date` | handled |
| 36 | scripts/check_heartbeat_cron.sh:1107 | the FOMC audit's day | ET | `TZ=America/New_York date +%F` | handled |
| 37 | scripts/run_self_deploy.sh:74 | the operating-window check | ET | `TZ=America/New_York date +'%u %H%M'` | handled |

Every `$(date --iso-8601=seconds)` in the wrappers' status and heartbeat files
is an instant carrying its offset (`+00:00`), not a date, and every reader
compares instants. They are not counted as sites.

**Counts: 37 sites. 1 wrong, 31 harmless, 5 handled.** The 37 rows break down
as 21 `local_today()` sites, 6 direct date reads in OUT modules, 4 UTC days or
instants, and 6 shell rows.

## The timers, against the UTC date

| Timer | ET | UTC date then (EST) | In the window? |
|---|---|---|---|
| chester-backup | 02:30 daily | the same date | no |
| ibgateway-restart | 01:00 daily | the same date | no |
| chester-weekly | Sun 05:00 | the same date | no |
| chester-alpha-weekly, chester-prices-saturday, chester-quarterly | Sun 06:00, Sat 06:00, Sat 06:00 | the same date | no |
| chester-voices, chester-overnight, chester-morning-anchor | 06:15, 06:45, 07:00 | the same date | no |
| chester-monthly | the 1st, 07:30 | the same date | no |
| chester-heartbeat | 08:30 | the same date | no |
| chester-dealer-0945, chester-open-note, chester-dealer-1230 | 09:45, 09:50, 12:30 | the same date | no |
| chester-ibkr-sync | 09:00-17:00 every 30 min | the same date | no |
| chester-restore-test | Sun 10:15 | the same date | no |
| chester-auction, chester-eod, chester-flashalpha, chester-vendor-chains, chester-daily-close | 15:49 to 16:45 | the same date | no |
| chester-crypto-basket | 17:25 | the same date (22:25 UTC) | no |
| chester-alpha-nightly, chester-alpha-proposer | 17:40, 18:10 | the same date (23:10 UTC) | no |
| **chester-meme-ingest** | **Mon-Fri and Sun, 21:15** | **tomorrow** | **yes** |
| **chester-evening-note** | **Mon-Thu and Sun, 21:30** | **tomorrow** | **yes** |
| **chester-deploy** | **weekdays 19:20-22:50 and 23:20; Sat all day; Sun 00:05-03:35 and 07:05-23:35** | **tomorrow, for the ticks from 19:00** | **yes** |
| **ibgateway-watchdog** | **every 5 minutes** | **tomorrow, from 19:00** | **yes** |

**What the four in the window stamp today:**
- **The evening note (21:30).**
  - Its edition, its subject and its guard all use `session.session_date()`,
    the ET date: handled.
  - Its fetch stamps rows with instants. Its voices pass reaches row 27
    (harmless), and any undated security-master resolve reaches row 23 (wrong,
    rare).
  - Its wrapper's log name follows row 34 (harmless).
- **The meme ingest (21:15).** Rows are stamped with instants (`seen_at`); the
  status line is not printed in the window (row 13); the log name follows row
  34. Harmless.
- **The self-deploy ticks.** The window check is ET (row 37, handled);
  `restart_pending` and the status files carry instants; the log name follows
  row 34. Harmless.
- **The gateway watchdog.** The restart counter's day is the UTC day (row 33,
  harmless); the log name follows row 34.

**The outputs stamped with the UTC date in the window, by name:**
1. **Monthly log file names** of the evening note, meme ingest, self-deploy,
   watchdog and heartbeat cron, on a month's last evening: **harmless**.
2. **The watchdog's restart-counter day:** **harmless**.
3. **The security master's default as-of date, inside an undated `resolve()`
   during the evening note's fetch:** **wrong (rare)**. It reaches an output
   only on a ticker-change day.
4. **The evening note's own date:** **handled**, already the ET date.
5. **The nightly sweep's snapshot and log names:** not in the window. The sweep
   runs at 02:30 ET, so they are **harmless**.

## The readers

- **The chat-side tasks** (the X triage, the digests) write file names with
  their own ET dates. The box reads them by those names (the addendum's
  `digest_files`) against ET session dates, and dates each file by its
  `.copied_at` instant. Both sides use ET; nothing converts.
- **The Letters.** No module or config in the repo or the rehearsed tree reads a
  "Letters" prompt. Their prompts live outside the repo, so the audit cannot see
  them. Nothing the box writes in the window is a dated file a prompt would read.
- **The sweep's folder names.** The Drive folders are fixed names; the dated
  names are the snapshots (row 32), written at 02:30 ET.
- **The registry's and the store's as-of dates.** `observed_at` is a session or
  observation date and `available_at` an instant. Neither comes from a box
  "today", so no stored as-of date takes the UTC day.

**Nothing downstream reads a UTC-dated stamp from the window as an ET date.** The
one wrong site (23) is internal: the security master answers with tomorrow's
issuer on the rare evening a ticker changes hands.

## The two options for the sitting (no recommendation)

**(a) The box's day is the UTC day, stated as the convention.**
- The Reporting System paper states it: a box "today" is the UTC date, and any
  output a reader sees as a trading date uses `session_date()` (ET). The code
  needs nothing new, because every reader-facing date already does this (rows
  7, 35-37, the evening note).
- **Cost:**
  - The paper's text.
  - One change: `security_master._day(None)` must use the session date, since a
    resolve is reader-facing. It is in an OUT module, so not before the merge
    week.
  - Every new site must choose, `local_today()` or `session_date()`, with a
    review line saying which.
  - The 24 monthly log names keep their month-end evening spill.

**(b) "Today" is the ET date everywhere, at a named cut-over.**
- `local_today()` becomes the ET date (or its 21 sites move to
  `session_date_obj()`), and the shell's `date +%F` / `%Y-%m` become
  `TZ=America/New_York date`, from a named session, for example the first
  session after the merge week.
- **Cost:**
  - About 21 Python sites and 26 shell sites (24 log names, the sweep's
    `TODAY`, the watchdog's day), each needing a check that nothing compares old
    names with new ones.
  - **On the switch day:**
    - Any run between 19:00 and 24:00 ET that day writes the date it already
      wrote that morning, not tomorrow's. The month-end evening log lines go
      back into the current month's file.
    - The sweep's snapshot name does not change at 02:30 ET, so retention
      (14 daily, 8 weekly, monthly) sees no duplicate and no gap.
    - The watchdog's counter resets at midnight ET from that day.
  - No stored row changes: `observed_at` and `available_at` never used the box
    "today".

## Needs-you

- **`altdata/security_master.py:99`, `_day(None)` uses `date.today()`.** It is
  plainly the ET date that is meant, and the fix is cheap:
  `session.session_date()`. But the module is in A119's OUT list, because the
  rehearsed merge-week tree changes it. Name it for the burn-down paste after
  the merge week. Not fixed here.

Nothing else found is plainly wrong today.

## Gates

| Gate | Result |
|---|---|
| `check_registry` | OK |
