# B102 notes: the chat-side register brought up to date; the readable editions recorded

Paste B102 (`docs/pastes/B102.md`, its order beside it as
`docs/pastes/B102-attachment-readable-editions.md`), 1 Nov 2026. Branch
`b102-readable-editions-register`, base origin/main at `422ea697`. This is the record
only: nothing in the repo reads a Letter, a card or a map, and nothing here adds a
reader. No prompt text, no figure from a Letter or card, no handle, no account value.

## What changed, file by file

| File | Lines (now; added / removed) | What |
|---|---|---|
| `docs/master-guide/chat-tasks.yaml` | 203; +97 / -36 | Version 2, updated 2026-11-01, the new dst_note. Rows: 13 before, 19 after (the edits are listed below) |
| `docs/master-guide.md` | 916; +54 / -15 | Table 2 refreshed from the register, with its intro's daylight-saving sentence and the FlashAlpha paragraph brought to the winter and retired states. The two Letters in "The reports at a glance". "The week at a glance". Table 4's last row. The new Part 2 subsection, "The readable editions". Part 7's three checklists. "Landing next", re-dated to 1 November, with one row |
| `docs/figures/master-guide/fig-02-clock.svg` | 255; +125 / -109 | Figure 2, regenerated |
| `tools/figures/master_guide.py` | 427; +9 / -6 | The one code change, for legibility (below) |
| `docs/html/master-guide.html` | rebuilt | `tools/build_paper_html.py docs/master-guide.md`, for check_library's check 10 |
| `docs/scheduled-tasks.md` | 46; +10 / -3 | Seven rows added. The FlashAlpha pair marked retired and kept. AAII's "Delivers" changed to the weekly folder |
| `docs/chester-reports-architecture-v3.md` | +10 / -0 | One dated paragraph, "(1 November 2026)", at the end of Part 4. Nothing else in the file was edited |
| `docs/change-order-readable-editions-2026-11-01.md` | 65, new | The attachment, filed, with its status (below) |
| `docs/briefs/letter-findings.md` | 36, new | The defect list: M1-M7 (A95 Part 6) and W1-W7 (A103), all open |
| `docs/briefs/b102-notes.md` | new | This file |

### The register's rows

Rows changed:
- **The morning Grok digests.** The row is renamed "Grok X digests, morning (the
  operator's automations)" and covers the A and B files, each with its Principals
  section.
- **The morning triage.** Renamed "X digest triage, morning". It now runs at 07:17
  and writes the triage file and four ledgers.
- **AAII.** It now writes the weekly folder. Its consumer names the sweep's real
  path (the finding below).
- **The two UTC tasks** are printed at their winter times, and their `when` times
  follow: 07:00 and 08:00.
- **The FlashAlpha pair:** status retired. The rows are kept, but Figure 2 leaves
  retired rows off, as it always has.
- **The MSTR / MSCI watch:** the 1 Dec read is not yet scheduled, and the label no
  longer names it.

Rows added:
- after the X rows: the evening Grok digest (planned) and the evening triage
  (planned);
- under the "readable editions" comment: the Weekly Letter, the Monthly Letter, the
  ES day-trading card and the ES Sunday map.

**One optional field added, `notes`,** and declared in the header. It holds the
evening triage's "created 30 Oct, paused 1 Nov until its Grok input exists" and the
Monthly Letter's "first edition, October 2026, written by hand on 1 Nov; first
scheduled run 1 Dec". Table 2 prints a note in brackets after the status word.

**Names.**
- The header's two mentions and the two rewritten X rows now say "the operator"; this
  includes the triage's rights, whose wording is otherwise unchanged.
- Five lines in rows the paste said to keep unchanged still carry the operator's
  first name: the crypto scan's consumer, the publication watch, the signal scan (two
  lines) and the JPM read. I left them, as instructed. Stripping them is a
  one-line-each follow-up if the D38 rule should reach them.

## Figure 2 and Table 2: the commands

1. `python tools/figures/master_guide.py` writes `fig-02-clock.svg` and
   `fig-05-library.svg`. Figure 5's rewrite was line endings only, and I dropped it.
2. **Table 2** has no generator. I rewrote its block between
   `<!-- table:chat-tasks -->` and `<!-- /table -->` from the register, one row per
   task in the file's order: name, cadence, writes, consumer, rights and status.
3. `python tools/figures/master_guide.py --check` exits 0.
4. `python tools/check_master_guide.py`: VALIDATION PASSED, 0 failures and 1
   warning. The warning is the standing "the Guide is as of 2026-10-23, older than
   the newest change order (2026-11-01): refresh it at the next chain merge"; the
   merge week's refresh clears it.

**What it took to fit the new rows (widened by labels, no row dropped).**
- The figure tool printed a daily task's full name in a 336-pixel column. "06:00 Grok
  X digests, morning (the operator's automations)" ran into the right-hand column,
  and the evening digest ran off the edge.
- The register already carries a short `when.label` for each of these rows, and the
  week and month lists already printed it. The tool now prints it in the weekday list
  too.
- A day range ("Mon-Fri", the ES card) prints whole instead of as "Mon".
- The footer said a UTC task "moves an hour when daylight saving ends on 1 Nov". It
  now says the two UTC tasks print their winter ET times.
- Rendered with headless Edge at 720 by 1974, every label fits its column. These are
  the only code lines touched, and the paste's Part 1 allowed changing the figure
  rather than dropping a row.
- **Still open:** in the week strip, the ES card's dot sits on Monday only. The
  listed line says Mon-Fri.

## The AAII sweep finding (a gap for the merge week)

- **The sweep pulls one file only.** `scripts/rclone_sync.sh` on main pulls
  `chester-vendor-checks/aaii/aaii-weekly.csv` and nothing else
  (`pull_inbox_file aaii aaii-weekly.csv`, line 510).
- **b82 doesn't change that.** On `origin/b82-aaii-bearish-share`, the branch that
  carries the AAII change, the line is the same: that branch changes
  `altdata/sources/aaii.py` and its gate, not the sweep.
- **b82's reader** still reads only `aaii-weekly.csv` from the inbox.
- **So nothing pulls the weekly folder.** Since 24 Oct the chat task writes
  `chester-vendor-checks/aaii/weekly/YYYY-MM-DD.csv`, one file a week, and no branch
  pulls `aaii/weekly/`. The box's AAII history stops at the last row appended to the
  old file.
- **Not changed here,** as ruled. The merge week needs:
  - the sweep to pull the folder;
  - the reader to union the weekly files with the history.

## The order's status

- **No rulings record yet.** This base has no
  `docs/briefs/rulings-2026-10-28-31.md` and no successor, so the filed order's
  status reads "Rulings D50-D56: pending". It names the order's own sign-off
  (section 5, "accept all", 1 Nov 2026 12:11 ET) as where the ruling stands quoted.
  No ruling was invented.
- **One change to the attachment.** Finding F1 gave the original X digest folder's
  Drive id. The filed order and the paste's copy say the id is not recorded, because
  the operator's Drive folders are named by path only.

## Other notes

- **`docs/scheduled-tasks.md` had no X triage row at all.** "The morning X triage's
  time and files corrected" is therefore a new row, with 07:17 and the four ledgers.
  The morning Grok automation, the Alpha Lab brief and the MSTR / MSCI watch still
  have no row there. They are in the register; the paste did not ask for them here.
- **Two findings quote the edition's own figures.** M6 and W1 carry the figures the
  paste gave. They are figures printed by the edition, not by a Letter.
- **Who reads `docs/scheduled-tasks.md`.** validate_official_sources does not
  (no reference on main). validate_alt_asset_scan does: it holds the alternative
  assets scan's row, which is unchanged, and it passes at 50/0.

## Gates (one at a time, foreground)

| Gate | Tally |
|---|---|
| tools/check_master_guide.py | VALIDATION PASSED: 12 self-tests passed; 0 failures, 1 warning (the as-of, above) |
| tools/figures/master_guide.py --check | exit 0 |
| tools/check_registry.py | OK |
| tools/check_library.py | 27 papers, 0 failures, 0 warnings (after the Guide's HTML was rebuilt) |
| tools/validate_alt_asset_scan.py (reads docs/scheduled-tasks.md) | 50 passed, 0 failed |
| validate_official_sources | not run: it does not read docs/scheduled-tasks.md |
