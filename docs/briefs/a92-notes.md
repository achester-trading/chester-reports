# A92 notes: DTH-1's box pieces (D41)

**Branch.** `a92-dth1-box-pieces`, from origin/main at `422ea697`.

**Merge timing.** Branch-only; it merges after chain-8 next week.

**Ruling D41 (27 Oct 2026; `docs/briefs/rulings-2026-10-25-27.md`).**

- The DTH-1 manual ledger, the brief and the playbook live outside this public
  repo.
- The Weekly prints aggregates only.
- Orders and sizes print on the chat-side card only, never in a box report.
- The box pieces are the checklist in the anchors and a ledger reader for the
  Weekly.

## Part 1: the checklist in the 07:00 anchor

**Where it prints.** `daily_cascade/morning_render.py` prints it straight after
the ES read, in the HTML and the text edition alike. `morning_payload.py` carries
it as `dth1_checklist`, read from `config/dth1.yaml`, which holds the wording and
the switch (`checklist.enabled: false` prints nothing). It is text only.

**What it prints:**

```
Day-trade rules (DTH-1)
  - Stop on the right side of the structure.
  - Size within the day's risk budget.
  - Re-screen the position after each fill.
  - No re-entry within 60 minutes of a stop-out.
  - Promotion test to Book C at 15:45 ET: up at least +1R, holding beyond the range edge, 2R of room to the next level, and the backdrop agrees.
```

The HTML edition adds the footer "Rules only: no prices, no sizes, no orders."

## Part 2: the ledger reader

**What it reads.** `altdata/dth1_ledger.py` reads
`~/chester-data/inbox/dth1/dth1-manual-ledger.csv`. Columns are read by header
name (`config/dth1.yaml` `ledger.columns`). The required fields are date, result
in R and the rule-broken flag; status and promoted are optional.

**What it prints.** Aggregates only, counts and R, never a currency or a row:

- trades this week (the seven days ending on the edition's Sunday) and to date;
- no rule broken k of n;
- mean and median R;
- win rate;
- largest loss in R;
- promotions to Book C ("not tracked (no column)" without that column).

**The other cases:**

- A row with a status of verify/pending or a blank result is counted as "k
  row(s) awaiting the statement" and never scored.
- A missing required column is named, and nothing is scored.
- With no file the block prints "DTH-1 ledger not stored."
- It writes nothing to the store.

**What the Weekly prints** (the synthetic fixture, week ending 1 Nov 2026):

```
DTH-1 (manual): 2 trade(s) this week, 4 to date; no rule broken in 3 of 4 (75%); R per trade mean +0.50R, median +0.50R; win rate 50% (2 of 4); largest loss −1.00R; promotions to Book C: 1.
2 row(s) awaiting the statement.
```

**Where it prints.** The Weekly's book section, as a subsection after Book B's.
The builder is `weekly_sections.dth1_subsection`; the one call that appends it is
in `weekly_stack.book_week`.

**Files touched outside the paste's list:**

- `daily_cascade/weekly_stack.py`, the one call: the book section is built there,
  not in `weekly_sections.py` as the paste assumed.
- `tools/validate_backup.py`: its declared list of inbound files gains the one
  file the paste added.
- `config/catalogue_commands.yaml`: one line, since `validate_audit_3a` requires
  every command module to have one.

**The sweep.** `scripts/rclone_sync.sh` gains `pull_inbox_file dth1
dth1-manual-ledger.csv || true` beside the aaii line, with a comment naming the
folder generically.

## Part 3: the gate

**`tools/validate_dth1.py`, 22/0, on synthetic fixtures.** The fixtures are in
`tests/fixtures/dth1/`; their README says they are invented. It checks:

- **A:** the checklist renders after the ES read and the switch turns it off.
- **B:** the aggregates match a hand computation; verify and blank rows wait; a
  row after the week is not counted; a missing column is named; no file prints
  "not stored".
- **C, privacy:** no currency, no price, no row's date and no side reaches the
  text or the section's data; the reader imports no store and writes nothing; no
  file named like the real ledger is in the repo.
- **D, the wiring.**

**Counts.** One Makefile line. The gate count in CLAUDE.md goes from 135/132 to
136/133, changed by hand once: main has no stitch tools.
`validate_audit_3a.py`, which holds that count to the Makefile, passes.

**The other gates** (one at a time, foreground):

| Gate | Result |
|---|---|
| `validate_morning_anchor.py` | 71/0 |
| `validate_weekly_stack.py` | 83/0 |
| `validate_weekly_edits.py` | 91/0 |
| `validate_readability.py` | 67/0 |
| `check_registry` | OK |
| `validate_backup.py` | 88/0 |
| `validate_audit_3a.py` | 88/0 |
| `validate_gates.py` | 32/0 |

## What the box needs after the merge

**The file.** Put the ledger in the operator's main Drive (the inbox remote) at
`chester-vendor-checks/dth1/dth1-manual-ledger.csv`. The nightly sweep copies it
to `~/chester-data/inbox/dth1/dth1-manual-ledger.csv`.

**Its header.** The first row names the columns. The reader recognises:

- Date
- Result R (or "R multiple")
- Rule broken
- Status (optional)
- Promoted (optional)

**Nothing else.** No new timer, unit or key. Until the file lands, the Weekly
prints "DTH-1 ledger not stored."

## A92b (1 Nov 2026): the ledger's single home, the archive copies, the X patterns, AAII's weekly folder

**Base.** `origin/a92-dth1-box-pieces` at `c566dcd9`. Main is still at
`422ea697`, already in this branch, so nothing was merged in. The paste is
`docs/pastes/A92b.md`, the recreated text of 1 Nov 22:10 ET; no earlier A92b
had run.

**Part 1: the ledger's home (D52).**

- The sweep reads `chester-cards/dth1-manual-ledger.csv`, a top-level Drive
  folder named by path, and lands it unchanged at
  `~/chester-data/inbox/dth1/dth1-manual-ledger.csv`.
- `pull_inbox_file` assumed the `chester-vendor-checks/` prefix. So
  `pull_inbox_path <folder by path> <file> <inbox folder>` is the variant, and
  `pull_inbox_file` now calls it with the prefix, so its other callers are
  unchanged.
- `config/dth1.yaml` documents the canonical header: date, time_et, instrument,
  side, entry, stop, target, contracts, risk_usd, exit, result_r, result_usd,
  status, rule_broken, notes.
- **Header aliases.** The reader already reads a header by name, lower-cased with
  non-alphanumerics as "_". So "Date" / "date", "Result R" / "result_r", "Rule
  broken" / "rule_broken" and "Status" / "status" are the same column, and no
  code alias was needed; the gate proves both spellings.
- **Open rows.** A status of "open" is excluded from the closed-trade aggregates
  and printed as "k open, not scored." (`open_words`).
- **Awaiting the statement.** "FILL FROM STATEMENT" joins `awaiting_words`. A
  non-numeric or blank result already waited for the statement, as A92 ruled.

**Part 2: the archive copies (D54).** `pull_folder` does an `rclone copy` of a
folder's top-level files, every type, never a sync. Each copy is capped by
`timeout`, logged by count, and skipped with a log line when the folder is
absent. It never touches the sweep's RC.

- `chester-letters/` goes to `~/chester-data/inbox/letters/`.
- `chester-cards/` goes to `~/chester-data/inbox/cards/`.
- **Nothing in the repo reads either.**
- **The backup's include list.** The trees copy `chester-data` whole, with no
  exclude (`copy_tree "$DATA_DIR" "chester-data" 15`), so both folders, and
  AAII's `weekly/`, fall inside the encrypted backup. The inbox pulls run after
  the trees, so a night's new files are backed up by the next night's sweep.

**Part 3: the X patterns.**

- The digest's pattern takes `x-digest-YYYY-MM-DD.md`,
  `x-digest-eqmacro-YYYY-MM-DD.md` and `x-digest-evening-YYYY-MM-DD.md`.
  Nothing on the box reads the B or the evening file; they are archive only.
- One log line counts the top-level Drive folders named `chester-x-digest`, so a
  second one shows in the sweep's log.

**Part 4: AAII's weekly folder.**

- **The finding.** B102 established that since 24 Oct the AAII task writes one
  file a week to `chester-vendor-checks/aaii/weekly/YYYY-MM-DD.csv`, and that
  the sweep pulled only `aaii-weekly.csv` (one row, 14 Oct), on main and on b82
  alike. The box's AAII history stopped at that file.
- **(a) The sweep.** `pull_folder chester-vendor-checks/aaii/weekly aaii/weekly`.
- **(b) The reader.** `altdata/sources/aaii.py`:
  - `weekly_files()` gives the old file first, then `weekly/*.csv` in name
    order;
  - `weekly_rows()` reads each with `rows_from_weekly` and unions by (key,
    Reported Date). For a week in two files, the row with the newest
    retrieved_at wins. A "disagrees" cross-check stays on the row as
    `crosscheck` and in the run log; the row is never dropped. The store has no
    flag column, and no store key was added;
  - `_produce` calls it, and the history file still wins on a shared date
    (`union`).
- **(c) The gate.** The writer's gate is `tools/validate_official_sources.py`,
  new group W. Its fixture holds the old file, two weekly files and one week in
  both. The module also points the weekly folder at nothing for every other
  group, so a machine whose inbox holds it cannot change their verdicts.
- **b82, for the merge sheet.** b82 (`b82-aaii-bearish-share`) changes the end
  of `rows_from_weekly`, `union`, `_from_file` and `_produce`, giving the parsers
  a `keys` argument. This branch adds new functions and changes two lines of
  `_produce`, so the two meet there. The resolution:
  - keep b82's body;
  - call `weekly_rows(KEYS)` in place of b82's `rows_from_weekly(w.read_bytes(),
    KEYS)` (the arguments pass through);
  - change b82's `union`, keyed on (key, date), not at all.

  Both branches also add a group to `validate_official_sources` (b82's V, this
  branch's W), meeting on `main()`'s group list: keep both.

**Gates.** Run one at a time in the foreground:

| Gate | Result |
|---|---|
| `validate_dth1` | 27/0 (group E added: the canonical header, the open and awaiting rows, no unread column in the text, the old spellings) |
| `validate_official_sources` (the AAII writer's gate) | 344/0 (group W added) |
| `bash -n scripts/rclone_sync.sh` | ok (shellcheck is not installed on the laptop) |
| `check_registry` | OK |
| `validate_secrets` | 58/0. It scans for keys and secrets; the currency, price and row-date scan of the DTH-1 text is `validate_dth1` group C, with E's synthetic values |
| `validate_backups` | 29/0 (the inbound pulls that read the inbox remote are now five) |
| `validate_backup` | 89/0 (the X pattern, the pull_inbox_path body, the folder copies) |
| `validate_deploy` | 154/0 |

No gate was added.
