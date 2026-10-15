# AUD-3d: the FRED history writer

**This branch builds on aud-1-data-fixes and merges after it.** Branch
`aud-3d-fred-history` is cut from `origin/aud-1-data-fixes` at **63ec6a8**, its
tip at the time. It needs aud-1's `drop_unchanged` FRED mirror (AUD-1 4a) and the
as-of joins (4c). The incremental pulls in the 07:26 paste wait for next week, as
the replacing paste rules.

Branch only: nothing merged, nothing deployed, nothing run on the box.

## What and why

- The live FRED pull reads 1,500 days and stamps every row available at the
  instant it was written (`ingest_instant`).
- So FRED history before about 2022 is missing. A deep pull stamped today would be
  invisible to every as-of query before today, and the Alpha Lab's long windows
  (H-002, H-004, H-005) would stay empty.
- `observations.py` already reserves `observed` for "ALFRED vintages", and
  `tools/backfill_prices.py` refuses revisable series because they get "ALFRED
  vintages or nothing". This branch builds that path.

## The build: `altdata/fred_history.py`

`python -m altdata.fred_history backfill --series KEY[,KEY] | --all [--from DATE] [--dry-run]`

1. **ALFRED's vintage history.** For each registered FRED series
   (`altdata.config.FRED_PULL_SERIES`, 129):
   - `series/vintagedates` is read in pages of 10,000;
   - then `series/observations` is read with `realtime_start`/`realtime_end` over
     at most 2,000 vintage dates a request (FRED's cap), in pages of 100,000.
   - A value is written once for each vintage in which it **changed**. FRED clips a
     carried-over period's `realtime_start` to the window, and its value is
     unchanged, so a window edge never invents a vintage.
2. **`available_at` is the vintage's first publication.**
   - The release time is used when the calendar holds it: `data/fred_release_map.json`
     (the box's cached series-to-release map, read only) names the release, and
     `config/release_calendar.yaml` gives its standard ET time.
   - Otherwise it is the **end of that day ET** (23:59:59.999999), so never earlier
     than the truth.
   - `availability_kind` is `observed`.
   - A revised value gets its own row from its own vintage date.
3. **Reconstructed availability is allowed only for `never` / `split_only` series
   without vintages.** It is the observation plus the declared latency: one
   business day, at the end of that day ET. A revisable series without vintages
   gets nothing, and is listed.
   - **All 129 registered FRED series are `revised` today,** so in practice every
     series takes ALFRED or nothing. The reconstructed path is built and gated for
     the day a `never` series is registered.
4. **The rows.**
   - Source `fred:backfill` (read as fred, per AUD-3a), with their own `run_id`
     (`fred_history:<UTC stamp>`).
   - Existing rows are never rewritten (the store's INSERT OR IGNORE).
   - **"A value equal to a stored vintage is not written again" is read as: the
     same value already stored for that period at the same or an EARLIER
     availability.** A value stored only *later*, the live pull's ingest instant
     of 2026, does not block the earlier, truer vintage. Otherwise the backfill
     would skip exactly the rows it exists to write (not named, chosen; needs-you
     2).
   - Rows go to the observation store only. The CSV copy (`data_store/`) is the
     live pull's, and is untouched.
5. **ICE BofA.** For the 8 `BAML…` series the dry run says FRED keeps only about
   three years of them, by licence, with the earliest held, as a note rather than
   a failure.
6. **`--dry-run`** prints, per series: status, vintages, rows, the earliest
   observation and the earliest availability. With more than one series it adds
   an estimate of rows, disk (at ~250 bytes a row) and run time (the dry run's
   fetch time plus a fifth for the writes). It writes nothing.

The FRED key is read through `altdata.secrets` and never printed. Fetch errors pass
through `secrets.redact`.

## The gate: `tools/validate_fred_history.py`, 25/0

A fake ALFRED answers in FRED's documented shapes. It clips `realtime_start` and
`realtime_end` to the requested window and pages by limit and offset. The gate
never fetches.

| Group | Fixture |
|---|---|
| A | **A revised series, as of three instants.** January 2020 prints 100 on 7 Feb and is revised to 105 on 6 Mar, both at 08:30 ET. As of 13:29:59 UTC on 7 Feb it sees **nothing**; from 13:30 it sees **100**, up to the revision; from 6 Mar 13:30 UTC it sees **105**. February goes unseen, then 200, then 203 (EDT). No row is available before its period's first publication, and FRED's `.` writes nothing |
| B | release times: 08:30 ET where the map and calendar hold it; the end of the day ET without; no map, then end of day |
| C | a `never` series without vintages reconstructs (Friday → the end of Monday ET, unseen before); a `revised` series without vintages is **refused**, listed, and writes nothing |
| D | paging: vintage dates in pages, observations over two-vintage windows, each paged; the period carried across the window edge is not a new vintage |
| E | source `fred:backfill`, its own run, kind `observed`; a re-run writes nothing; Feb's 200 stored earlier is not rewritten; Jan's 105 stored only by a later live pull still gets its 2020 vintage; today's read is unchanged |
| F | the dry run writes nothing and reports vintages, rows, earliest observation and availability; the estimate over several series; ICE BofA as a note |
| G | a full backfill with the network paths disabled; the key through altdata.secrets |

The Makefile gains the gate. CLAUDE.md is recounted from the Makefile: seventy-six
code gates (seventy-three Python, three shell) and six data gates. It also gains
one paragraph on the writer. check_library: 0 failures.

CI: the push's number is in the report.

## Box commands, printed for Ari, run by no session

Run these after aud-1-data-fixes and this branch are on main, and after the FRED
compaction. Use a weekday evening inside the window (17:20–23:30 ET), clear of the
02:30 sweep.

```bash
cd ~/chester-reports && git log -1 --oneline          # the merged tree
df -h ~/chester-reports/data                          # want 2 GB free or more
ls -lh ~/chester-reports/data/chester.db
free -m

# 0. the release map, if it is not cached yet (the release calendar's own pull: it writes
#    data/fred_release_map.json and the calendar events, as its scheduled pass does)
ls -l data/fred_release_map.json || .venv/bin/python -m altdata.sources.fred_releases pull

# 1. the dry run: writes nothing, prints per series and the estimate
.venv/bin/python -m altdata.fred_history backfill --all --dry-run 2>&1 | tee ~/logs/fred_history_dryrun.log

# 2. the run, after reading the dry run
.venv/bin/python -m altdata.fred_history backfill --all 2>&1 | tee ~/logs/fred_history.log
ls -lh ~/chester-reports/data/chester.db
```

## The dry run's estimate, before it is run

The box's dry run gives the exact figures. Until then, a reckoning from the
registry's frequencies (54 daily, 8 of them ICE BofA; 49 monthly; 18 quarterly;
8 weekly):

| | Estimate |
|---|---|
| rows | about **0.4–0.9 million**. Daily market series are rarely revised: about one row an observation over 25–60 years each. Monthly and quarterly series carry several vintages a period |
| disk | about **0.1–0.25 GB** at ~250 bytes a row |
| run time | about **10–25 minutes**: about 130 vintage-date reads and 300–600 observation requests at 0.6 s pacing, plus FRED's response time on large daily windows. The dry run takes about as long, since it fetches everything |

The sweep refuses to stage a snapshot with less than twice the database's size
free (`disk_low`), which is why the df check wants room to spare.

## Files shared with the other open branches

Each branch was compared with its merge base and aud-1's tip.

| Branch | Shared |
|---|---|
| aud-2-ops-security | CLAUDE.md (the count), Makefile (the gate list) |
| alpha-lab-2 | CLAUDE.md, Makefile |
| aud-3a-catalogue | CLAUDE.md, Makefile |
| aud-3b-security-master | CLAUDE.md, Makefile |
| aud-3c-quality | CLAUDE.md, Makefile |
| vp-1-volume-profile | CLAUDE.md, Makefile |

`altdata/fred_history.py` and its gate are new and shared with none. The refresh
recounts the gate total once every branch is in.

## Not named by the paste, so chosen here

1. **"Equal to a stored vintage"** is read as the same value at the same or an
   earlier availability (above).
2. **The reconstructed latency** is one business day, at the end of that day ET.
   No FRED series uses it today.
3. **The release time** comes from the cached release map plus the calendar's
   patterns. The map is never refreshed by this module.
4. **A missing ALFRED series** (an HTTP 400 on vintagedates) is read as "no
   vintages", so it is refused if revisable.
5. **Rows go to the observation store only, not the CSV copy.**

## Needs you

1. **The run, after the dry run:** box commands 1 and 2, on the ruled schedule.
   Paste the dry run's estimate line and its refused list.
2. **The reading of "a value equal to a stored vintage"** (not-named 1). keep /
   rule otherwise
3. **The release map on the box:** if `data/fred_release_map.json` is absent, every
   vintage is stamped at the end of its day. That is safe but later than the
   truth. Box command 0 caches it.
4. **AUD-3a's reading of `fred:backfill` as fred** is session A's. Until it lands,
   any reader that filters on `source = 'fred'` will not see these rows. The as-of
   join does not filter on source.
5. **The incremental pulls** (prices, FRED, CFTC, RTAT) wait for next week, as
   ruled.
