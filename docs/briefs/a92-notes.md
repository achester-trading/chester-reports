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
