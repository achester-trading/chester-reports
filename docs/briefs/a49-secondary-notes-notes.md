# a49-secondary-notes: the 09:50 open note and the 21:30 evening note (session A, 19 Oct 2026)

**Base and boundaries.** This branch is cut from `a48-batch11`'s final tip, `c646aae` (after its CI-table commit), on the third chain.
- **Branch only.** This branch is pushed and nothing else. Nothing ran on the box, no unit was enabled or started, and nothing was merged to main.
- **chester-meme was not opened.** Its timing is taken from chester-reports' own notes and code (`scripts/run_meme_ingest.sh`, `altdata/meme_ingest.py`).
- **The specification** is `docs/change-order-secondary-notes-2026-10-19.md`, filed verbatim (ruled 19 Oct 2026, 14:14 ET).
- **Where the order and the code differ, the code wins.** Each difference is listed in section 7.

## The commits

| Commit | What |
|---|---|
| `52bffd8` | Part 0: the order filed verbatim; `docs/change-orders.md`, a new index of all eighteen orders (none existed; the signal-triage register's "Batch orders" row covers triage batches only) |
| `8ad2191` | Part 4: the two pre-registrations, before any scoring code |
| `68e1ab3` | Parts 1–3: the fetch steps, registry, wrappers and units; the open note and the evening note; the meme ingest to 21:15 |
| `9ab2d05` | Part 4: the two scoring scripts and their first editions |
| (this commit) | Part 5: `tools/validate_secondary_notes.py`, the Makefile, CLAUDE.md, the heartbeat's status warning, these notes |

## Part 1: the fetch steps, the registry, the wrappers and the units

### The fetch: `python -m altdata.note_fetch open|evening [--date D] [--dry-run]`

The fetch writes the store and the notes only read it (30.4).

**`open`, after the 09:45 capture.** It fetches:
- **5-minute bars from 08:00 ET** for SPY, ES=F, ZN=F, ZT=F, ^TNX, DX-Y.NYB and ^VIX;
- **a targeted FRED pull** of only the series behind today's 08:30 tier-1 and tier-2 releases, through the existing writer (`fred.pull(Store(), series=[...])`, which is vintage-keyed and append-only);
- **the news:** `events_ingest.pull(only=["news"])`;
- **one voices pass,** with a 120-second budget, inside the scan's own daily cap.

It then writes `calc.release_first_hour` for ES=F (percent) and ^TNX (bp): the last bar before 08:30 to the last before 09:45.

**`evening`, at 21:30.** It fetches:
- **5-minute bars from 15:30 ET** (on Sunday, from Friday 15:30) for ES=F, NQ=F, RTY=F, ZN=F, JPY=X, CNH=X, BTC-USD and ETH-USD;
- **5-minute bars for the four Asian indices from four days back,** so each one's prior close is in the window: ^N225, ^HSI, 000001.SS and ^KS11;
- **the CFETS fix**, through the existing writer;
- **the news and earnings:** `events_ingest.pull(only=["news", "earnings"])`;
- **after-hours prices:** yfinance's pre- and post-market bars for each captured name whose stored `release_at` is after 16:00 today, written as `calc.after_hours_move` (the regular close against the last after-hours trade);
- **one voices pass.**

**Every step is non-fatal and names its absence.** The fetch exits 0 when any bars were written and 1 when none were.

### The instruments and the registry

**The instruments** live in `config/reporting_stack.yaml` as `note_bars` (12 entries). They are kept apart from `tape` and `intraday_extra` on purpose: those join the 16:10 `bars` feed and its final-bar retry loop.
- **Storage:** they are stored in the bars table without volume.
- **Registry:** `note_bars_prices` (`members_from: altdata.bars.NOTE_BAR_PRICE_KEYS`, `expected_members: 12`).
- **Reused:** the tape's own `spy`, `y10`, `dxy` and `btc` and `intraday_extra`'s `es`.
- **Brookfield:** none of the symbols is a Brookfield instrument.

**The two own-reading keys** are registered with `units: label`, lens-excluded and trigger-ineligible, under a new source-registry id, `secondary_notes` (tier derived, own computation).

**AUD-3a's lists:**
- `note_bars_prices` joins `NEW_KEY_BLOCKS`;
- `altdata.note_fetch` has its line in `config/catalogue_commands.yaml`.

### The session guard

`python -m altdata.session evening-before [DATE]` exits 0 when the day after DATE is a session.

| Evening | Result |
|---|---|
| Thursday | runs |
| Sunday | runs |
| the eve of a half day | runs |
| Friday | skips |
| Thanksgiving's eve | skips |

### The wrappers

`scripts/run_open_note.sh` and `scripts/run_evening_note.sh` follow `run_dealer_capture.sh`'s shape: lock, `git pull --ff-only`, the guard, the fetch, then the note, then the status and heartbeat.
- **They exit 0 after a soft failure.** A failed `chester-*` unit would turn the heartbeat red (`unit_failed`, RC 13), and the notes are secondary. Each step's rc goes to `$STATE_DIR/<note>_status`.
- **The open note waits for the 09:45 capture.** It waits a bounded time (`capture_wait_minutes: 4`, session-set) by polling every 20 seconds, then prints "09:45 capture pending".

### The units

`chester-open-note.service/.timer` (Mon–Fri 09:50) and `chester-evening-note.service/.timer` (Sun..Thu 21:30).
- **AUD-2's conventions:**
  - `MemoryHigh=8%` and `MemoryMax=10%`;
  - `OOMScoreAdjust=500` (a report), added to `OOM_SCORES`;
  - `TimeoutStartSec` 12 and 15 minutes;
  - the sandbox;
  - `-%h/state` in `ReadWritePaths`.
- **The caps** are not in `MEMORY_CAPS`, whose sum is held under 150%. The new gate holds them instead.
- **The state-directory rule:** both are declared in `box-config.allow` (Environment).
- **Not in `DEPLOY_TIMERS`.** `deploy/systemd/README.md` has a section and a row in its memory table.

### The heartbeat warns and never fails

- **The anchor table:** two rows, `open_note_heartbeat` and `evening_note_heartbeat`, 100 hours each (a weekend plus a holiday).
- **The status files:** a new loop reads `open_note_status` and `evening_note_status` and names a non-zero rc the next morning.
- **Untouched:** the verdict and the exit code.

## Part 2: the open note (`python -m daily_cascade.open_note`)

**Its six blocks,** each with its as-of time:
1. **The 08:30 releases.** Each print is shown in the calendar's declared form, with its naive surprise (labelled naive) and lens 24's line where the release has one, then "No consensus: no free source serves a macro consensus, and the surprise index stores none."
2. **The reaction,** on release days only. Each move runs from the last bar before 08:30 to the last before 09:45:
   - ES and the dollar index in percent;
   - ^TNX in bp where its bars cover 08:25;
   - ZN and ZT in percent (ZT "not tracked" where no bars are served);
   - VIX in points and percent, from 09:30 and labelled where its bars start there;
   - "No intraday attribution".
3. **The open.**
   - **The gap:** SPY's 09:30 open against the stored prior close.
   - **The range:** the first fifteen minutes' high-low.
   - **Against the gauge:** both are set against the gauge's implied one-session move, read as the 07:00 anchor read it (`gauge_from_store` at a 07:00 cutoff, with the pre-market centre).
   - **Against the levels:** SPY is set against the flip and the OTM walls, both from the anchor's settled profile and from the 09:45 capture, or "09:45 capture pending".
   - **The convention:** the sign convention prints once, and "no vendor value is read or printed".
4. **News since 07:00.** At most five items: the agencies' press items and the voices scan's items, by publication time.
5. **Book C:** "No Book C drafts: the 07:00 setup list is not built." It never adds.
6. **What the close will check:** one line naming the levels and the release reactions.

**The gate opens on any of:**
- a tier-1 08:30 release;
- a gap or a range beyond the gauge's move;
- the 07:00 anchor's volatile-day trigger (the close's stored `vol.event_day` for the prior session, `fired`).

**Prose:** at most 250 words, through `narrative.generate` via `audit_retry` under `model_meter.scope(report="open_note")`, with the style guide `docs/narrative-template-notes.md`.
- **Over the cap:** a reply past its cap is withheld with its count and logged to the withheld log, never trimmed.
- **Gate shut:** no model call.

**The subject** is code-written from the payload and numeral-audited against it, for example "Open note: CPI +0.3% m/m; 10-year +9.0bp since 08:25; open outside the expected move". It has a figure-free fallback.
- The release's own row carries its headline print, so the name in the subject binds to the figure it cites.

**The chart:** ES since 08:25, on release days only.

**Dry runs:**
- **Before `live_from` (2026-10-26):** every run is a dry run, archived under `dryrun/` with its payload JSON and mailed with "[DRY RUN]".
- **`--dry-run` alone:** archives without mailing; add `--email` to mail it.

## Part 3: the evening note (`python -m daily_cascade.evening_note`)

**The blocks on a weekday:**
1. **US futures.** ES, NQ and RTY, each from the 16:00 close and from the last trade before the 17:00 halt.
   - ES is set against the gauge's implied one-session move (today's close).
   - ES is set against the ES block's levels as the close printed them (`es_ledger`, slot close).
   - "Dealer levels in ES: after the 6b engine (ST-R6.45c waits on 6b)".
2. **After-hours earnings.** Captured names less the index funds and restricted names. For each:
   - EPS against the analyst mean once yfinance serves it;
   - the after-hours move against `ahead.implied_move`;
   - "Never a recommendation".
3. **Asia's open.** The Nikkei, Hang Seng, Shanghai Composite and KOSPI, each against its prior close.
   - Open times in ET come from zoneinfo. Before 1 Nov: Tokyo and Seoul at 20:00, Hong Kong and Shanghai at 21:30.
   - "not yet open" or "no bars served yet (Yahoo's delay)" as the case is.
4. **Currencies.**
   - Dollar-yen and offshore dollar-yuan since 16:00.
   - The PBoC fix for the next Beijing date against the prior onshore close.
   - The yen-unwind and devaluation hooks evaluated on the 21:30 quotes, "Descriptive only; no new flag".
5. **Crypto since 16:45.** BTC and ETH, and OI-weighted perp funding as last stored. "ETF flows: gap" while Farside is not stored.
6. **News since 16:45.**
7. **Book D.** Tonight's `meme_drafts`, awaiting, ingested since 17:00 ET: their count and names, read-only. "Decided at 07:00".

**The Sunday edition (D7)** opens with the futures open against Friday:
- **The futures:** ES, NQ, RTY and ZN, each from Friday's 16:00 price and its last trade before the halt to the first bar after 18:00, with the high, low and latest since.
- **Against the gauge:** the one- and five-session moves as of Friday's close.
- **The currency gap:** dollar-yen's weekend gap.

It then prints the weekend's news in two parts, by publication time:
- **First, since the 05:00 Weekly;**
- **then Friday 16:45 to Sunday 05:00.**

The block states once that every item was ingested at 21:30.

**The gate.**
- **Weekdays.** It opens on an earnings night, ES or NQ beyond 0.75%, dollar-yen beyond 1%, an Asian index beyond 1.5%, or a hook tripped. Otherwise there is no prose and the note prints "Nothing to do tonight; the 07:00 anchor re-reads all of this."
- **Sundays:** always open.

**Prose:** at most 150 words on a weekday and 400 on a Sunday.
**The chart:** on Sunday, ES since 18:00; on a weekday, ES since 16:00 when the gate is open.
**Subjects:** "Evening note: quiet", "Evening note: ES +0.9% since 16:00; ...", "Sunday night: ES +0.3% vs Friday; N items since the Weekly".

### Does any feed roll before Sunday evening? (measured 19 Oct 2026, laptop)

A note at Sunday 21:30 needs about 53 hours of items (from Friday 16:10). Each feed's oldest item, by hours before the probe:

| Feed | Items | Oldest item, hours back |
|---|---|---|
| fed_press | 20 | 917 |
| fed_monetary | 15 | 4,153 |
| bea_news | 48 | over 100,000 |
| fed_speeches | 15 | 750 |
| sf_fed | 10 | 7,345 |
| dallas_fed | 100 | over 100,000 |
| ecb | 15 | 438 |
| boe | 50 | 6,223 |

- **Every feed the laptop can read holds weeks.** So no Saturday pull is proposed.
- **Unmeasured from the laptop:** BLS's two feeds answer 403 here (known), and Yahoo Finance's RSS answers 404. Yahoo is the one fast-rolling feed in the list.
- **The listing pages** (the desks') hold weeks of links.
- **If the first Sunday dry run's Yahoo items stop short of Friday,** the proposal is a Saturday 12:00 `events_ingest pull --only news` plus a voices pass, for Ari's yes. It is not built.

## Part 4: the two ledgers

**The pre-registrations** were committed in `8ad2191`, before any scoring code, and are never edited. The gate pins them by SHA-256 of their LF bytes:

| Pre-registration | SHA-256 |
|---|---|
| `release-first-hour-preregistration-2026-10.md` | `b62b0d1b5f738d891ba1352106d6e537a7a1f5c86b886d7c7947811871cdc4e7` |
| `after-hours-earnings-preregistration-2026-10.md` | `e88a6cbf3414db26d7e3e4222656beb1ba8b7533de8a8364753b1a24484308ae` |

**SN-1, the release-day first hour** (`tools/calibration/sn1_release_first_hour.py`). First edition `docs/ledgers/sn-1-ledger-2026-10-19.md`:
- **Verdict: FAIL.** None of the 4 cells with 20 or more days passes. CPI ES 10/21, PCE ES 8/20, PPI ES 10/20, claims ES 26/53; every share is near half.
- **Every ^TNX day is not scored.** Yahoo's hourly bars for the yield index start at 08:20 ET and are aligned at :20, so the registered 07:00–08:00 bar never exists. The registration is not changed. The open note's own 5-minute readings are the sample that can score the 10-year.

**SN-2, after-hours earnings** (`tools/calibration/sn2_after_hours_earnings.py`). First edition `docs/ledgers/sn-2-ledger-2026-10-19.md`:
- **Verdict: FAIL.** 107 of 193 continue (55%), with a Wilson interval of 48–62%.
- **Per name:** descriptive rows. GLD, SLV, IBIT and USO have no earnings.

**Both are report-only and grant nothing.**

## Part 5

- **The meme ingest moves to 21:15.** This covers the timer, the wrapper's and module's text, `validate_meme_ingest`'s pin and CLAUDE.md.
  - **Safe:** it shares no lock and no input with the note.
  - **Timing:** its two-minute random delay ends before 21:30.
  - **It takes effect** when Ari reloads and restarts the timer (box commands below).
- **`tools/validate_secondary_notes.py`** is in the Makefile: 87 checks in groups A to H, both SHA-256s pinned. It seeds its own stores; no network and no model.
- **The other gates changed:**
  - `validate_events`: the notes added to its no-fetch files and its socket-less run;
  - `validate_systemd_units`: OOM scores;
  - `validate_meme_ingest`: 21:15;
  - `validate_audit_3a`: the new block and the catalogue line;
  - `validate_monthly_stack`: the reading-targets pin narrowed to the four cadences, because the notes add keys.
- **CLAUDE.md:** a paragraph on the notes, the meme time, and the recount. The base had 120 code gates (117 Python, 3 shell); this branch has 121 (118 Python).
- **The Master Guide:** `tools/check_master_guide.py` does not exist on this base, so the rows are below for whichever branch merges second.

### The Master Guide rows (for session B's `master-guide`)

| Report | Time | Status | Rights | Unit |
|---|---|---|---|---|
| Open note | 09:50 ET, trading days | Secondary; built on a49-secondary-notes, dry runs to 25 Oct, live from 26 Oct | The Doctrine's 1000-report right only: confirm or cancel Book C's 07:00 drafts, never add (none exist yet) | `chester-open-note.timer`, enabled by hand |
| Evening note | 21:30 ET, Sun–Thu (the evening before a session) | Secondary; as above | None | `chester-evening-note.timer`, enabled by hand |

**The Guide's list of Doctrine gaps:** "the 1000 report" is no longer unruled. It is ruled as the open note, and the Doctrine's text waits on Doctrine #2.

## 7. Where the order and the code differ (the code wins)

1. **Book C has no 07:00 setup list and no draft object.** Block 5 prints the not-built line. The confirm-or-cancel right is printed and never exercised.
2. **There is no macro consensus.** The note prints "No consensus" with the gap named, plus the naive surprise, labelled.
3. **PPI and retail sales have no declared form** in `release_calendar.yaml`'s `tier1_headlines`. Their days print "no declared form in the release calendar; the print is not read", and the targeted FRED pull covers only declared series.
   - **For Ari:** declare their forms (e.g. `fred.ppi_final_demand` mom; retail sales mom) in a later ruling.
4. **Lens 24 lines exist** for CPI, payrolls, PPI and GDP only.
5. **The 10-year's reaction** is ^TNX where its 5-minute bars cover 08:25. Yahoo's hourly ^TNX starts at 08:20, so the first-edition ledger cannot score it at all (Part 4).
6. **The CNH hourly bars:** `altdata/sources/cnh.py` stores only the daily close. The evening fetch therefore writes CNH=X's own 5-minute bars (note id `cnh`).
7. **The devaluation hook needs an onshore CNY quote at the same instant.** The onshore market is shut at 21:30 and the fetch takes none, so the hook prints "not tripped (no 21:30 CNH or CNY quote)". The yen hook evaluates on the 21:30 quote. The hooks' fixed "12:30" wording is relabelled "21:30".
8. **The volatile-day trigger** the open note reads is the close's stored `vol.event_day` for the prior session, the row the 07:00 anchor prints. Only its VIX arms are coded; the Doctrine's ATR, gap, Negative-gamma and tier-1 triggers are not.
9. **The ES levels for tomorrow** are read from `es_ledger`, which the close writes only on a live run. During dry-run weeks the line reads "not stored".
10. **"ETF flows: gap" while Farside is not stored.** The crypto order's evening refresh lives here as that line.
11. **The voices cap is counted per UTC day.** A 21:30 ET pass counts against the next UTC day's 60 calls, shared with the 06:15 ET scan. Each note's pass is held to 120 seconds.
12. **"Whether the futures open is consistent with each item" (Sunday)** is said in the Sunday prose only. The code prints each item with its time and cannot judge consistency.
13. **No state record is emitted.** No state key is reserved for a note, and `state/emit.py:VALID_KEYS` is unchanged.
14. **SN-1's first edition reads FRED's keyless release-calendar page** (`fred.stlouisfed.org/releases/calendar`; robots allow it with a 1-second delay). The API route the registration names wants a key the laptop does not hold.
    - The refunding is not a FRED release, so its days are not read.
    - A day with several releases counts under its highest tier, and within a tier under the order the registration lists them.
15. **The open note's capture wait is four minutes,** session-set. The order says only "a bounded time".

**Session-set values for Ari's review:**
- the evening thresholds: 0.75%, 1% and 1.5%;
- the capture wait: 4 min;
- `news_max`: 5 and 8;
- the heartbeat allowance: 100 h;
- the caps: 8% and 10%;
- the timeouts: 12 and 15 min;
- the voices pass: 120 s.

## The merge sheet: box commands (Ari's; printed, never run here)

Inside the deploy windows, after the merge:

```
# 1. The units arrive with the self-deploy (or bash scripts/deploy.sh); then the state drop-ins:
mkdir -p ~/.config/systemd/user/chester-open-note.service.d ~/.config/systemd/user/chester-evening-note.service.d
printf '[Service]\nEnvironment=CHESTER_STATE_DIR=%%h/state\n' > ~/.config/systemd/user/chester-open-note.service.d/override.conf
printf '[Service]\nEnvironment=CHESTER_STATE_DIR=%%h/state\n' > ~/.config/systemd/user/chester-evening-note.service.d/override.conf
systemctl --user daemon-reload
# 2. A dry run of each by hand first (live_from makes it a dry run anyway):
CHESTER_FORCE_RUN=1 ~/chester-reports/scripts/run_open_note.sh
CHESTER_FORCE_RUN=1 ~/chester-reports/scripts/run_evening_note.sh
# 3. Enable both timers:
systemctl --user enable --now chester-open-note.timer chester-evening-note.timer
# 4. The meme ingest at 21:15 (its unit changed):
systemctl --user restart chester-meme-ingest.timer
systemctl --user list-timers 'chester-*note*' chester-meme-ingest.timer
```

**If the third chain merges after Thursday 22 Oct,** move `secondary_notes.live_from` later in the merge commit. At least two weekday dry runs of each note and one Sunday dry run must come first.

## Doctrine #2 (7–8 Nov), listed and not edited

- **The 1000 report:** the Doctrine's text becomes the open note's, by Ari's ruling.
- **The mandatory touch:** once Book C activates, is the open note mandatory on volatile-protocol days, as the Doctrine's 1000 touch is?
- **The Book D touch:** the Doctrine names the 1000 report as a Book D touch. The open note carries no Book D block.

## Needs you

1. **The box commands above,** after the merge, inside the windows.
2. **Read the dry runs** (the 21–23 Oct weekday and 25 Oct Sunday editions under `reports/dryrun/`) and move `live_from` if needed.
3. **The session-set thresholds:** keep or rule them.
4. **Declared forms for PPI and retail sales** (difference 3).
5. **The Yahoo RSS window** on the first Sunday dry run, and the Saturday pull only if it rolls.

## CI

| Push | Run | Result |
|---|---|---|
| (pending) | | |
