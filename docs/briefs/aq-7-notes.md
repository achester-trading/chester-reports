# AQ-7 — the alternative-assets quarterly scan: build notes (12 Oct 2026)

Branch `aq-7-quarterly-scan`, from `origin/aq-2-chapters-2` at `833bf99`, not
merged. Built against the Alternative Assets Quarterly change order
(`docs/change-order-alternative-assets-quarterly-2026-10-10.md`): §8 (the scan's
three parts and their ingest mechanisms), §4.5 (China's political sub-section,
the ladder, the hierarchy), §4.10 (Thailand's hierarchy and isolation), and the
AQ-7 row of §11. The change order itself is not edited.

The scheduled task is **not created**. It is cloud-only and web-only, and it
writes only a file; the operator creates it from the prompt (Needs you 1).

## What was built

| Piece | Where |
|---|---|
| The task's prompt (2,080 words below its line) | `docs/scans/PROMPT-alt-assets-quarterly.md` |
| What the scan may read, and how it is classed | `config/alt_asset_scan.yaml` |
| The standing search list (22 gaps) | `config/alt_asset_gaps.yaml` |
| The ingest | `altdata/alt_scan.py` (new); `altdata/scans.py` (routing, isolation) |
| The Monthly's print of the agency tables | `monthly_macro/stack.py` `sourced_figures` |
| The task's row | `docs/scheduled-tasks.md` |
| The gate (50 checks), in the Makefile's list | `tools/validate_alt_asset_scan.py` |

**The prompt** is a complete standalone instruction for a fresh cloud session.
- **What it reads:** the two new configs, `voices_sources.yaml`,
  `source_tiers.yaml`, both political calendars and the previous quarter's scan.
- **What it writes:** one file, `docs/scans/alt-assets-YYYYqN.md`, in an exact
  shape. Its tables' headers are the ones the ingest reads, which the gate
  checks.
- **Part 1, the agency tables.** These are §8's ten publishers: WGC GDT by
  category and its central-bank statistics; the Silver Institute; ICSG; EIA STEO,
  IEA OMR and OPEC MOMR side by side; IMF COFER and the WEO vulnerability inputs
  for the EM chapter's countries; IIF flows; the BoT and NESDC series. Each figure
  carries its period, value as published, unit, vintage, published date and URL.
  A late publication is cited at the vintage it has (decision 6).
- **Part 2, the stories.**
  - **2a, stories per family:** voice, kind, outlet tier, class, a declared
    subject and direction only, and the gap it bears on.
  - **2b, China's measures on the ladder:** announced → authorised → funded →
    implemented, with each rung defined.
  - **2c, China's calendar proposals:** announced dates only.
  - **2d, Thailand's items and calendar proposals.**
  - Inflections from previously committed voices come first, found against last
    quarter's file but never labelled.
- **Part 3, candidates:** candidate series with their definitions (the intake
  template's rule).
- **Forbidden:** status words, status columns, recommendations, edits to any
  config or the register, and anything of the operator's private Thailand core.

**The ingest** (`altdata/alt_scan.py`) has two halves.
- **The store half** (`ingest_store`) is idempotent and writes no file, so
  `altdata.scans.ingest()`, which every Monthly run calls, the box included,
  runs it for each committed `alt-assets-*.md`.
  - **Part 1:** each figure goes to the scans ingest's own `scan_figures` (no
    stored source, not printed). Its identity is publisher, table, metric and
    period, so a later vintage of the same period is stored with the revision
    against the stored prior in `comparison`, for example "revised from 104.6
    mb/d (STEO Dec, read 2027-01-04): +0.3". The BoT's and NESDC's figures go to
    the isolated family `alt-assets-thailand`, which `scans.latest()` leaves out
    unless asked.
  - **Part 2:** each story is a voices row, its direction kept only on a declared
    subject. China's reporting is filed under `source_id` `china.<outlet>`, which
    the China chapter's political panel already reads.
  - **Status:** computed by the register's own `voices.compute_status` over the
    quarter against the one before. A declared status (a Status column, or a
    status word in any cell) refuses the row.
  - **Not stored:** rumour is never stored. Thailand's items are never voices
    rows.
- **The file half** (`write_files`, the CLI only, run in a session):
  - `docs/scans/proposals-YYYYqN.md` carries China's calendar proposals (marked
    proposable or "commentary; wait for an authoritative release"), the ladder
    table (with "counts as demand" only for funded and implemented), Thailand's
    items and proposals, the flagged rumours, the computed statuses and every
    refusal.
  - `docs/scans/intake-drafts-YYYYqN.md` carries each candidate on the signal
    intake template, as `SR-? (DRAFT)`, unnumbered.
  - Nothing here writes a config or the register. The gate holds both calendars
    byte-for-byte unchanged, and the register too.
- **Commands:** `python -m altdata.alt_scan check <file>` parses only;
  `ingest <file> [--no-files]` runs the store half and writes the two files.

**Routing.** `altdata.scans.ingest()` no longer reads `PROMPT-*`, `proposals-*` or
`intake-drafts-*`, none of which carries a reference table. It sends
`alt-assets-*` to the store half. `latest()` keys an alt-assets edition by its
read date, because its figures carry their publishers' own dates.

**The Monthly** prints the agency tables in its sourced-figures slow layer with
each row's own source, vintage and date, and the revision against the prior
vintage. The Guide's single-source note did not fit a table of ten publishers.

**The chapters.** Item 9's "not yet — the quarterly scan (AQ-7)" line now prints
only in a quarter with no stored story for the family.

**Gates re-run here:**
- `validate_alt_asset_scan` 50/0;
- `validate_config_refs` 29/0;
- `check_library` 26 papers, 0 failures;
- `validate_gates` 31/0;
- `validate_monthly_stack` 261/0;
- `validate_quarterly_stack` 94/0. Its Thailand-isolation check caught the
  ingest naming the Thai calendar's file in its prose. The ingest never read it,
  but no longer names it either; this gate now holds that too.

## What waits, and for what

- **The task itself.** The operator creates it from the prompt (Needs you 1).
  Its first run is Mon 4 Jan 2027, for the 9 Jan edition. A December dry run of
  the prompt by hand would show the shape holds against live sources before the
  first real one.
- **Committing and ingesting the scan, every quarter.**
  1. A human commits the scan's file.
  2. A session runs `python -m altdata.alt_scan ingest docs/scans/alt-assets-YYYYqN.md`
     and commits the two files it writes.
  3. The operator seeds the calendars by hand from the proposals and rules on
     the drafts.
  4. The box's next Monthly run (or the Quarterly's) stores the figures and
     voices.

  The Quarterly's run calls `scans.ingest()` only through the Monthly's path
  today. Whether `run --cadence quarterly` should call it too is for AQ-11's dry
  run.
- **The chapters' remaining "AQ-7" lines** come from the stored rows once a scan
  is ingested: the stories (item 9) and China's political reporting. Four do not
  read the store yet:
  - the agency figures the metals and oil chapters name as arriving with the
    scan (the Silver Institute's balance in a falsification test's reason, OPEC+
    output against quota in a structure row);
  - the consensus against spot in item 3a;
  - the ladder table in China's political panel;
  - the Thailand chapter's agency figures (`alt-assets-thailand`).

  Each needs its chapter wired to read the stored rows, a few lines apiece. They
  are not wired here, because the shape of the stored rows should be seen
  against a real scan first.
- **The voices subjects.** China, real estate, Thailand and agriculture have no
  declared subject in `config/voices_sources.yaml`, and metals is gold alone. Their
  stories are stored without a direction, so they can be NEW or REITERATED but
  never INFLECTED (Needs you 2).

## Choices made for the operator to overrule

1. **YYYYqN is the quarter the edition covers,** the one just ended. The 4 Jan 2027
   run writes `alt-assets-2026q4.md`.
2. **The gaps list is compiled, not copied.** The structural papers carry no
   section headed "Gaps"; the Disruptive Themes paper's 7.6 Gaps Register is the
   only formal one. The 22 entries are each paper's own statements of what it
   does not measure ("What is uncertain", "Nobody's model contained …", "is
   unknown"), plus the gaps the change order names. Each `passage` is verbatim
   and the gate finds it under its section. Entries leave the list by a commit,
   never by the scan.
3. **The prompt lives in the repository.** `docs/scheduled-tasks.md` says prompts
   live in the scheduler, so the two cannot drift. This one is in the repo
   because the brief asked for it, and the gate holds its table shapes to the
   ingest's. The scheduler's copy is the text below its line. If the prompt
   changes, the scheduler is updated from the file.
4. **Thailand's items are never voices rows.** The voices register prints in the
   close, the Weekly and the Monthly, and the Thailand chapter feeds nothing
   (§4.10). Its figures are stored, but isolated, and its items go to the
   proposals file only.
5. **Rumour is listed and never stored.** "Rumour flagged" is read as visible to
   the operator, invisible to every report.
6. **A calendar proposal needs an announced date;** an expected date is refused.
   This is the calendar's own rule.
7. **A declared status refuses the row,** rather than being stripped and the row
   kept. A scan that declares status is a scan to fix, and the refusal list says
   so.
8. **The fire time is 06:30 ET,** proposed, a slot clear of the other tasks.

## Needs you

1. Create the scheduled task "Alternative assets — quarterly scan" from docs/scans/PROMPT-alt-assets-quarterly.md (the text below its line), cloud-only and web-only, 06:30 ET on Mon 4 Jan, 5 Apr, 5 Jul and 4 Oct 2027? yes / no
2. Declare voices subjects for the families that have none — `china`, `real_estate`, `agriculture`, and `silver` and `copper` beside `gold` — in config/voices_sources.yaml (this also widens the daily voices scan's subjects)? yes / no
3. Name the file for the quarter the edition covers (the 4 Jan 2027 run writes alt-assets-2026q4.md)? yes / no
4. Accept the gaps list as compiled from the papers' in-place statements, or commission Gaps sections in the family papers from a library session? accept / commission
5. Accept choices 4–7 (Thailand never in voices; rumour never stored; announced dates only; a declared status refuses the row)? yes / no
6. Merge order, inside windows: AQ-2 part 2, then this branch? yes / no
