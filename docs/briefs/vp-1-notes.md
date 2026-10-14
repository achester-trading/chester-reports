# VP-1 — the volume profile (session A, 14 Oct 2026)

Branch `vp-1-volume-profile`, from main at `cc91752`. Branch-only: pushed, not
merged, not deployed, nothing run on the box. The ruling is the operator's, 04:39
CT on 14 Oct. The branch merges in the week of 19 Oct, after a later paste merges
the new main into it. The definition is `docs/volume-profile.md`.

**What it is, and what it is not.** The reports print the profile as data:
- tables;
- one chart panel (W7) and one shaded band (C1);
- listed levels;
- one clause on each Book B candidate line.

None of them says a level will hold or a node will be crossed. Those claims are
H-006 to H-008 in the Alpha Lab, and no backtest was run here. No code was
copied from OpenChart or any other project; the module is written from the
paste's definition.

## The nine

### 1. The module and its config

`altdata/volume_profile.py` and `config/volume_profile.yaml`, every value marked
session-set. The definition is as the paste gives it.
- **Bins:** at `bin_bps` of the window's last close, rounded down to the ladder.
- **Volume at price:** each bar's volume spread evenly over its range.
- **The POC:** ties go to the bin nearest the volume-weighted mean, then the
  lower.
- **The 70% value area:** built by pairs.
- **The nodes:** HVN and LVN on the centred 5-bin mean, at its 80th and 20th
  percentiles.
- **Completeness:** `bars.complete_share`, in aggregate, naming every session
  below it.
- **One source per window.**
- **As-of reads** throughout.
- **"approximated from daily bars"** on every daily profile.

Three things are mine, where the paste was silent:
- **The volume-weighted mean** for the POC tie is the profile's own: each bin's
  midpoint weighted by its volume. The window's bars give no other single price
  that a daily profile could share.
- **Nodes are interior bins only.** A tail bin has one neighbour, and calling a
  profile's thin edge an "LVN" would list every window's extremes. A plateau
  counts once, at its first bin.
- **A high exactly on a bin edge** covers none of the bin above it. Otherwise a
  bar from 100.00 to 100.10 would put a zero-width share into a third bin.

Fixtures, all in `tools/validate_volume_profile.py`:
- **A.** A hand-built window with every number worked out in the comments:
  - the bin width, on four last closes;
  - the POC at 100.225 and the value area 100.10–100.35, by steps of 14 then 13;
  - a bar spread over two bins, and a high on a bin edge;
  - a tie won by the mean, and an exact tie won by the lower bin;
  - two humps giving two HVNs and one LVN;
  - a daily profile's note, and its absence without volume.
- **B.** The invariants: volume conserved; POC inside the area; the area at
  least the share, and below it without its last pair; a whole-bin price shift;
  volume scaling; high = low; no volume.
- **C.** An incomplete week, named session by session, and a mixed-source week,
  each absent with its reason.
- **D.** All six windows byte-identical when a heavy bar is written after the
  cutoff, and changed when read at a later cutoff, which shows the fixture bites.

### 2. The level list

`altdata/levels.py`: for spy, qqq and iwm, the POC, VAH and VAL of six windows:
the session, the prior session, the week to date, the prior week, the month to
date and the prior month.
- They are appended after `ma_20m`, so every existing level keeps its place, and
  labelled by window ("prior week's value-area high").
- Only the prior windows carry a status (`status_of`); the current windows join
  `NO_STATUS` with the session high and low.
- A window not computed is absent with its reason.
- The flat row carries `vp_<window>_<field>`, and each instrument also carries
  `volume_profile`, a summary of each window, which the tables read.
- `figure_budget.tape_levels` is unchanged.

Fixture **F**:
- the order of the types;
- the labels;
- all 18 levels on a seeded SPY;
- statuses on the prior windows only;
- the flat row;
- qqq configured but with no bars, each window absent with its reason;
- the 10-year neither listing nor missing them.

### 3. The label audit

`altdata/numeral_audit.py` gains the three names (point of control or POC,
value-area high or VAH, value-area low or VAL), each in its six qualified forms
and bare.
- The qualifiers: "the session's" (or "today's"), "the prior session's" (or
  "previous session's", or "yesterday's"), "the week's", "the prior week's" (or
  "last week's"), "the month's", "the prior month's" (or "last month's").
- The prior forms are matched first, so "the prior week's VAH" is never read as
  "the week's VAH".
- A bare name binds to that field in any window.

Fixtures:
- **G** in the new gate, twelve sentences. "SPY held the prior week's
  value-area high at 667.00" fails, with "the payload holds as 664.25; 667.00
  is vp_week_vah", exactly as the 30 Sep put wall failed.
- Five more in `validate_numeral_audit` group H.

### 4. The stored series

`calc.vp_<id>_session_{poc,vah,val}` and `calc.vp_<id>_20s_{poc,vah,val}` for
spy, qqq and iwm.
- **Registry:** 18 entries in `metrics_registry.yaml` with the paste's fields:
  derived_state, calculated, recomputed, price, daily, session. Mechanism group
  `equity_tape`, beside the other SPY tape features. None is trigger-eligible.
- **The writer:** `python -m altdata.volume_profile compute [--from DATE|first]`.
  Each row's `available_at` is the max of its input bars'. A window not computed
  writes nothing, so the composite needs twenty complete sessions.
- **The EOD wiring:** `scripts/run_eod_cron.sh` runs it after the derived-features
  step, on the same never-fatal pattern (`WARN volume_profile exited N --
  continuing`). With no `--from`, it recomputes the last seven calendar days'
  sessions, so a missed pass is caught up by the next.

Fixture **H**:
- six series per instrument;
- a session row's `available_at` equal to its bars' maximum;
- the composite's equal to the maximum over all twenty sessions, with one
  session fetched a week late to make the difference visible;
- no composite on a short history;
- the 18 registry entries;
- the wrapper's order.

### 5. The two measurements

`coverage` and `compare`. Both read only, write nothing, and were never run
here. The commands are below.

`compare`'s window is the 20-session composite ending at each of the last N
sessions. A single session's daily-bar profile is one bar, so it would compare
nothing. It reports:
- the POC distance, in the daily profile's bins;
- the value areas' overlap, as intersection over union.

### 6. The close

`daily_cascade/stack.py` `tape_section` carries a second table: Market | Value
area (POC) | Prior session | Migration | Close vs value.
- **The rules:** `vp.migration` and `vp.close_vs_value`, the paste's seven
  migrations in its order.
- **Absent windows:** the row prints "not computed", the migration and close
  print "—", and the reason goes to the section's footnote.
- **The tape's lines** keep their old tested levels: the profile's levels are
  kept out of the "held / broke" tail, so no existing sentence changes.
- **`assemble`** now carries a section's `tables` (it dropped them before) and
  counts them in the fingerprint.
- **C1** shades the prior session's value area (`charts.shade_value_area`,
  clipped to the chart's range so it never rescales the candles), returns its
  VAL and VAH in `drawn`, and names them in the caption.

Fixture: `validate_stack` group V.
- On the existing fixture (no prior-session bars): the table, its "not
  computed" with the reason in the footnote, its print in the edition, and the
  unchanged tape lines.
- With the prior session seeded: a migration and close by rule, and C1's
  `drawn` carrying the prior VAL and VAH as listed levels, with its caption.

### 7. The Weekly

**The table** is the week against the prior week, a sub-section titled "Value
area: the week against the prior week", right after Levels. The Weekly calls
`tape_section(book, vp_windows=None)`, so the close's session table does not
also print.

**W7** gains a volume-at-price panel on the same price axis:
- **Layout:** `make_axes_locatable` on the same figure, so W7 is still one chart
  and one PNG, and the cap of ten is untouched.
- **Data:** the sessions W7 draws. This week's sessions stack in a darker blue
  over the earlier sessions' lighter blue, on one grid from the module.
- **The week:** its POC is marked and its value area shaded when the week is
  computed. Otherwise the panel says why in the caption.
- **Legend and caption:** a legend, and a caption written from the data.
- **The mobile rule:** `legibility_floor` applies to the panel's text as to the
  rest.

Fixture: `validate_weekly_stack` group V.
- The sub-section and its place.
- No session table.
- W7 over ten fixture sessions: one chart under the size cap; the panel
  splitting five and five; the week's POC inside its area; the caption's
  figures; the mobile floor.

### 8. The Monthly

**The table** is the month against the prior month, a sub-section of the month
in markets, after the long frame. It is data only: it carries no `prose` spec,
so no paragraph is asked for.

Fixture: `validate_monthly_stack`:
- the columns, one row per instrument;
- "not computed" where the fixture's bars don't cover the month;
- the reasons in the footnote;
- its print.

### 9. The scanner

`book_b_scanner.volume_readings`, called from `draft()`:
- **The base's POC**, from the base's own N sessions.
- **The nearest HVN** strictly between the entry and +1R (entry + direction ×
  risk), from the last 252 sessions, with its price and distance from the
  entry, or "none".

Both come from daily bars through the module, at 25 bps. They print as one
clause on `book_b.candidate_line`, "volume profile (approximated from daily
bars): base POC …; nearest HVN toward +1R …". The score's five components, the
gates, the timing and the grading do not read them.

Fixtures:
- **I** in the new gate: a shelf traded at 112–113 is the HVN between 108 and
  114; "none" beyond it; "none" for a short whose path is clear; each reading
  absent with "volume not stored" when no volume is stored.
- `validate_book_b_scanner`: every fixture candidate carries the readings, the
  clause prints, and the components are still the five.

## Gates

**New:** `tools/validate_volume_profile.py`, nine groups (A–I), fixtures only,
86/0. It is added to the Makefile, and CLAUDE.md's count goes to fifty-eight code
gates, fifty-five Python.

**Extended:** `validate_stack` (V), `validate_weekly_stack` (V),
`validate_monthly_stack` (item 8), `validate_book_b_scanner` (item 9), and
`validate_numeral_audit` (group H, the label audit).

Local results are in the session report and in "The gates, as run" at the foot
of this file. CI is the validate.

## The box commands, for Ari (none run here)

1. **The one-time history**, after the merge, inside the operating windows. It
   writes `calc.vp_*` from the first stored 5-minute bar onward:

       cd ~/chester-reports && .venv/bin/python -m altdata.volume_profile compute --from first

   `--from first` resolves to the earliest stored 5-minute bar of spy, qqq and
   iwm. Add `--dry-run` first to see the row counts without writing. The
   20-session composite starts twenty complete sessions after that first bar.
2. **Coverage** (read-only):

       .venv/bin/python -m altdata.volume_profile coverage --instrument spy --sessions 40

3. **Compare** (read-only):

       .venv/bin/python -m altdata.volume_profile compare --instrument spy --sessions 40

The last two write nothing, so they can run at any hour. The first is a store
write, so it runs inside the windows.

## Files shared with the branches named

`git diff --name-only` between each branch and its merge-base with main
(`cc91752` for all), intersected with this branch's own changes. Friday's
stitched branches are cumulative, each merged onto the one before, so the lists
only grow down the order.

| Branch | Shared files |
|---|---|
| aq-5-correlation-layer | CLAUDE.md, Makefile, daily_cascade/weekly_stack.py, metrics_registry.yaml, monthly_macro/stack.py, tools/validate_book_b_scanner.py |
| aq-8a-gold-residual … sr-38-inbox (branches 2–13) | the above plus scripts/run_eod_cron.sh, tools/validate_monthly_stack.py |
| b3-tranche-a … lib-aq14-em-paper (14–21) | the above plus daily_cascade/stack.py |
| el-1-packets, el-2-3-rollup (22, 23) | the above plus tools/validate_weekly_stack.py |
| w-1-3c-weekly-polish (now carrying 1–21) | the above plus altdata/book_b_scanner.py, altdata/numeral_audit.py, tools/validate_numeral_audit.py, tools/validate_weekly_stack.py |
| alpha-lab-2 | CLAUDE.md, Makefile, daily_cascade/weekly_stack.py |

The likely conflicts when the new main is merged in:
- **CLAUDE.md's gate count.** Main will be 74/71 or more after Friday, so this
  becomes plus one.
- **The Makefile's gate list:** one line, at the end.
- **`metrics_registry.yaml`:** a block before `bulk_imports:`. The stitched
  branches splice there too.
- **`scripts/run_eod_cron.sh`:** AQ-8a onwards add steps around the
  derived-features step.

The rest are edits to different functions in the same files.

## Found that the paste did not name

1. **H-006 to H-008 are not in this repository**, neither on main nor on
   `alpha-lab-2`. The docs here cite them by number only. If the lab's
   pre-registration should be readable from this repo, it needs a pointer.
2. **The Daily Cascade paper files the volume profile as Tier 3.**
   `docs/whitepapers/daily-cascade-whitepaper.md` lists it among the Tier 3
   items "gated on 150 graded decisions across two regimes". The paper also
   proposes it as "first-class ladder rows" and a Globex overnight POC. This
   ruling brings it in now, as data, and v1 leaves out ES, so the Globex POC is
   not built. The paper is unchanged; whether it needs a line is a library
   question.
3. **`stack.assemble` dropped a section's `tables`.** Only sub-sections and
   detail blocks could carry further tables. It now passes them through. No
   existing section set `tables` at the top level, so nothing else prints
   differently.
4. **`paragraph_wanted` is read by nothing.** The Weekly's sub-sections set it,
   but whether a sub-section gets prose is decided by its `prose` and `phase`.
   The profile's sub-sections set neither, so no paragraph is asked for.
5. **`validate_book_b_scanner` crashes in a Windows console.** It prints "≤"
   without reconfiguring stdout. That was already so on main. It passes under
   `PYTHONIOENCODING=utf-8` and in CI, and I didn't change it.
6. **A heredoc on this laptop halves backslashes.** Two of my scripted edits
   broke on it: a `\n` became a real newline in `charts.py`, which was caught by
   the gates' import. Later edits went through the Edit tool. Nothing broken was
   committed.
7. **The level list now reads up to about 38 sessions of 5-minute bars per
   instrument per edition**, for the prior month. That is three instruments and
   about 114 reads of the bars table, and it is fast on SQLite, but the close's
   16:45 build now does that work.

## Needs you: every session-set value

All are in `config/volume_profile.yaml`.

| Setting | Value | Note |
|---|---|---|
| `instruments` | spy, qqq, iwm | the paste's v1 set |
| `bin_bps.five_minute` | 5 | the paste's |
| `bin_bps.daily` | 25 | the paste's |
| `tick_ladder` | 0.01 … 10 | the paste's |
| `value_area_share` | 0.70 | the paste's |
| `node_smoothing_bins` | 5 | the paste's |
| `hvn_percentile` / `lvn_percentile` | 80 / 20 | the paste's |
| `composite_sessions` | 20 | the paste's |
| `scanner_hvn_sessions` | 252 | the paste's |
| `compute_lookback_days` | 7 | **mine**: how far back the nightly compute recomputes |

Also decided by the session, and not in config:
- **The POC tie's mean** is the profile's own volume-weighted bin midpoint.
- **Nodes** are interior bins only, a plateau counting once.
- **`compare`'s window** is the 20-session composite ending at each session.
- **The label qualifiers** accept "today's", "previous", "last week's" and "last
  month's" besides the paste's forms.
- **W7's two blues** (#1d4ed8 and #93c5fd) and C1's amber band (#f59e0b at
  12%).

Say if any should change.

## More found while gating

8. **On the Weekly, "beside the levels table" lands differently.** The
   storyline (W-1.2, `storyline.move_daily_tables`) moves the tape's "Levels"
   sub-section into the detail tables at the end of the edition, as "The tape:
   named levels". The value-area table stays in the tape section, where the
   week's prices are, so in the printed Weekly it does not sit next to Levels.
   Say if it should follow Levels into the detail tables.
9. **`validate_weekly_stack` still reaches the laptop's store on this branch.**
   That is W-1.3c's finding 9: Book B's fixture calls `book_week` with no week
   ending and no database path. It logs two caught tracebacks here. The fix is
   on `w-1-3c-weekly-polish` and arrives when the new main is merged in.

## The gates, as run (laptop, one at a time)

| Gate | Result |
|---|---|
| validate_volume_profile (new) | 86/0 |
| validate_numeral_audit | 164/0 |
| validate_book_b_scanner | 63/0 (under `PYTHONIOENCODING=utf-8`, see 5) |
| validate_stack | 75/0 |
| validate_weekly_stack | 76/0 |
| validate_monthly_stack | 264/0 |
| check_registry | OK |
| check_library | 0 failures, 0 warnings |
| validate_gates | 31/0 |
| validate_feeds_scheduled | 19/0 |
| validate_deploy | 118/0 |
| validate_session_calendar.sh | 47/0 |

W7 with its panel was also rendered from fixture bars and looked at: two blues
stacked by week, the week's POC line and value-area band, the legend under the
panel, and the candles unchanged.

**CI:** #388 on `c9d5193` passed every check, the full validate on Linux.

## 14 Oct evening: Friday's tip, the table's move, the paper's line

### The tip merged

`origin/w-1-3c-weekly-polish` at **`fb67bf3`** (it had not moved), merged as
`cc3d998` and pushed on its own. Three conflicts, all resolved by keeping both
sides:

- **metrics_registry.yaml:** both sides appended to the end of `metrics:`, and
  git interleaved the two appends into 18 hunks. I rebuilt the file as the tip's
  version with VP-1's block inserted unchanged after the tip's last metric,
  before `bulk_imports:`. The block is all 223 lines, from the "THE VOLUME
  PROFILE (VP-1" comment through the 18 entries.
  - The diff against the tip is that one insertion.
  - `check_registry` passes.
- **Makefile:** the tip's six new gates, then `validate_volume_profile.py`.
- **CLAUDE.md:** the gate total, recounted from the Makefile: **75 code gates**
  (72 Python, counting `smoke_test.py` as the Makefile's `EXTRA` does, and 3
  shell) and **six data gates**. The tip's prose says five data gates, but its
  Makefile lists six (`validate_imf_china.py`).

On the merge alone these gates passed locally:

| Gate | Result |
|---|---|
| check_registry | OK |
| validate_volume_profile | 86/0 |
| validate_gates | passed |
| validate_numeral_audit | passed |
| validate_stack | 75/0 |
| validate_weekly_stack | 78/0 |
| validate_monthly_stack | 265/0 |
| validate_book_b_scanner | 63/0 (needs `PYTHONIOENCODING=utf-8`; the known cp1252 console issue) |
| check_library | 27 papers, 0 failures |

"More found" item 9 (finding 9) is closed by the merge, since the fix arrived
with the tip. The Weekly gate no longer reaches the laptop's store.

### The changes

1. **The Weekly's value-area table moved into the detail tables** (ruled
   14:04 ET; "More found" item 8).
   - `storyline.move_daily_tables` takes the tape's "Value area: the week against
     the prior week" sub-section and prints it directly after "The tape: named
     levels" as **"The tape: value area, the week against the prior week"**.
   - The windows the profile could not compute still print in the tape
     section's "Not yet tracked" line, where they printed before. Only the table
     moves.
   - W7's side panel stays where it is.
   - Gates:
     - `validate_weekly_stack` group V now pins the table in the detail tables,
       directly after the named levels, gone from the tape, with its gaps in the
       tape's own `not_tracked`, and printed after the named levels in the
       archive's HTML.
     - `validate_weekly_storyline` group G gains a fixture of the move: order,
       removal, gaps kept.
   - `docs/volume-profile.md` says where the table now sits.
2. **The Daily Cascade paper.** After Chapter 24's backlog table, where row
   15–20 lists the volume profile among the Tier 3 items gated on 150 graded
   decisions, one dated italic line now reads:
   > *14 Oct 2026 — the volume profile entered the reports as data only: the
   > session and 20-session POC, VAH and VAL for SPY, QQQ and IWM, approximated
   > where built from daily bars. The claims it invites are tested in the Alpha
   > Lab as H-006 to H-008. The Globex overnight POC is not built, because v1
   > carries no ES.*

   - Nothing else in the paper changed.
   - `docs/html/daily-cascade-whitepaper.html` was rebuilt from it alone with
     `tools/build_paper_html.py <the .md>`. The diff is that paragraph and the
     source hash.
   - Chapter 1's "Add the Globex volume profile POC" and Chapter 3's "Add the
     full volume profile" are v1's backlog wording and were left as written.
3. **Looked at.**
   - I rendered the fixture Weekly from the gate's own seed and payload, into a
     scratch store, and saved the archive HTML.
   - The detail tables print in this order: the crypto basket, "The tape: named
     levels", the value-area table immediately under it, then the technical
     appendix.
   - The fixture's weeks are not stored whole, so its three rows read "not
     computed", and the tape's foot names each window and why.
   - The page was screenshotted with headless Edge. There is no PDF rasteriser
     on the laptop.

### Gates (local, one at a time)

| Gate | Result |
|---|---|
| validate_weekly_stack | 81/0 |
| validate_weekly_storyline | 31/0 |
| validate_weekly_edits | 90/0 |
| validate_volume_profile | 86/0 |
| check_library | 27 papers, 0 failures, 0 warnings |

### CI

- **#401** (`cc3d998`, the merge): green.
- **#402** (`7676110`, the table's move and the paper's line): green.
