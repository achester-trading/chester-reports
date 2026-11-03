# A117 notes: the attention ledgers' pending files

2 Nov 2026, session A. Branch `a117-attention-ledger-pending` off origin/main at
`422ea697`; main, not chain-10, so it merges the week after the merge week.
Paste committed first as `docs/pastes/A117.md`. No Drive read and no box.

## What was actually missing: two things, not one

**1. The sweep did not copy the pending files.** The paste expected
`scripts/rclone_sync.sh` to copy every file in `chester-vendor-checks/x-triage`.
It does list the folder, but its filter keeps only `x-attention-ledger.csv` and
`x-voices-ledger.csv`. That is true on main, on a99's rehearsal and on a105's
rehearsed merge-week tree (A92b widened only the digests' pattern). So neither
the pending files nor chapter B's `x-attention-ledger-eqmacro.csv` ever reached
the box, and fixing only the reader would have changed nothing there.
- **The change.** The filter now takes `x-voices-ledger.csv` and
  `^x-attention-ledger(-eqmacro)?(-pending-[0-9]{4}-[0-9]{2}-[0-9]{2})?\.csv$`,
  which is both chapters' main ledgers and their dated staging files, nothing
  else.
- **Unchanged:** the copy (`copyto` per file, each stamped `.copied_at`, never a
  sync).
- **The gate.** `validate_backup`'s X-pilot check named the old literal file. It
  now names the exact pattern, and a new case proves the pattern takes the four
  ledger names and refuses look-alikes (an undated file, a reversed date, a
  `.bak`, the voices ledger).
- **Merge risk.** a105's tree changes the digest line about 20 lines below,
  not this hunk.

**2. The reader ignored them.** The reader is `daily_cascade/digital_addendum.py`:
`attention_section` calls `read_ledger` for `x-attention-ledger.csv`.

**There is no chapter B reader** on main or on the rehearsed tree: nothing reads
`x-attention-ledger-eqmacro.csv`. The union is written for both names and
proved on both. The addendum still reads chapter A only. Adding chapter B to the
page is a separate decision, not made here.

## The reader change and the precedence rule

`read_ledger_union(path, cutoff)` returns the main ledger unioned with every
`<stem>-pending-YYYY-MM-DD.csv` beside it, in memory only:
- **Keyed by (date, theme).** A main-file row wins over a pending row for the
  same key, since the pending copy is the staging copy. Between two pending
  files, the earlier-dated one wins.
- **New keys are included.** Pending rows for dates the main file lacks, or for
  a new theme on a date it has, are added.
- **Visibility.** A pending file follows the main file's rule: its copy stamp
  must be at or before the cutoff.
- **Chapters stay apart.** The stem is matched whole, so chapter A never takes
  `-eqmacro-pending-` files.
- **Malformed files.** A pending file that is unreadable or lacks the date and
  theme columns is skipped, with a logged line: "attention ledger: skipped
  <file> (...)". Never fatal.
- **No main file.** If the main file is absent, the pending rows still count,
  and the provenance says "pending files only".
- **Nothing is written.** The inbox files are never rewritten; the chat-side
  task owns them.

The addendum's data gains `pending_files` and `pending_rows`. Its attention
statistics now see every day.

## The fixtures (`validate_digital_addendum` group D2, 9 cases)

| Case | Count |
|---|---|
| chapter A: main file (5 rows) + pending 27 Oct (2 rows, both main keys) + pending 30 Oct (2 rows, a new date) | 7 rows; 2 pending added, 2 shadowed |
| precedence | 27 Oct flows keeps the main file's URL and notes, not "PENDING MERGE" |
| a pending file stamped after the cutoff | not read |
| a malformed pending file (no date/theme columns) | skipped, the logged line captured |
| chapter B: eqmacro main (2) + eqmacro pending (1 duplicate, 1 new) | 3 rows; 1 added, 1 shadowed |
| pending file with no main file | 2 rows, "pending files only" |
| the addendum built on that inbox | flows on 3 days with 2 shock days, stablecoins added, 6 week rows |
| the inbox's bytes before and after | unchanged |

## For the chat-side task

The pending files should be a bridge, not a permanent second ledger. Once a
week, ideally the Saturday triage before the Sunday Weekly:
1. fold every `*-pending-YYYY-MM-DD.csv` row into its main ledger, keyed by
   (date, theme);
2. drop the "PENDING MERGE" note;
3. delete the pending files from Drive.

The box tolerates either state. A row in both places counts once (the main
copy), so folding never double-counts. If the main ledger outgrows the task's
rewrite limit, the better fix is a monthly file (`x-attention-ledger-2026-11.csv`)
than an ever-growing pending set. That needs its own paste: the reader and the
sweep both name the files.

## Gates (one at a time)

| Gate | Result |
|---|---|
| `validate_digital_addendum` | 103 passed, 0 failed (new group D2, 9 cases) |
| `validate_weekly_stack --group` | not run: B97's flag is not on main; the addendum's gate was run alone |
| `validate_backup` | 89 passed, 0 failed (its X-pilot check names the new pattern; one new case) |
| `check_registry` | OK |

## A125 (3 Nov 2026): stopped at the ruling search, nothing changed

Base `450455af`. Paste committed first as `docs/pastes/A125.md`.

**What was searched:**
- docs/ and config/, for "chapter A", "chapter B" and "eqmacro";
- the X pilot's change order, `docs/change-order-signal-triage-batch-8-2026-10-17.md`
  (items 50 and 51);
- the addendum's config, `config/digital_addendum.yaml`;
- the Reporting System paper, `docs/whitepapers/reporting-system-whitepaper.md`,
  which has no Appendix F.

**The ruling found.** Batch 8 says "Three items ruled 17 Oct 2026, all in the
digital-assets thread" and, under item 51, defines the page:

> *Weekly addendum (own page linked from the Sunday Weekly; ten-section stack in
> miniature, crypto only):* ... 6 narratives and attention -- the week's X
> attention map from the seven digests (themes, shocks, disagreement pairs, new
> voices) and the Saturday mechanism scan's output incl. PRL; ...

Chapter B is the triage's equities-and-macro chapter. A page ruled "crypto only"
shows chapter A's attention, so by the paste's first step A125 stops here.

**Unchanged:**
- the renderer (`daily_cascade/digital_addendum.py`'s `attention_section`);
- its fixtures and `scripts/rclone_sync.sh`;
- chapter A's output.

A117's union stays ready for chapter B if a later ruling places chapter B's
attention somewhere else, for example the Weekly's own narratives or the
Monthly's attention map.

**Gates:** none run, since no code changed. `check_registry` is OK.
