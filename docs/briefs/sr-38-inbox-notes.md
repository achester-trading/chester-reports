# SR-38 inbox: S&P DJI's EPS workbook, by drop (13 Oct 2026)

Branch `sr-38-inbox`, from `origin/sr-37-38-ai-fcf` at `2e8cfb4`. It answers SR-37/38's Needs you 3 (ruled: inbox). **It merges after SR-37/38.**

## What was built

**`altdata/sources/spdji.py` is the inbox reader,** on the AAII pattern.

- It reads `~/chester-data/inbox/spdji/sp-500-eps-est.xlsx` (`$SPDJI_EPS_FILE` overrides the path) and **fetches nothing**.
- It is a registered external writer (`altdata/feeds.py` `EXTERNAL_WRITERS`), so it runs in the same pass as AAII.
- The xlsx is read with the standard library (zipfile and ElementTree). xlrd 2.x reads only `.xls`, and a reader this small doesn't justify a new dependency on the box.

**What a drop writes.** There is one vintage per drop, and every figure is observed on the workbook's own "as of" date.

| Key | What |
|---|---|
| `spdji.op_eps_est_q` | the bottom-up operating EPS estimate per quarter (instrument `2027Q2`), from the estimates block |
| `spdji.fwd12m_op_eps` | the forward twelve months: the first four estimated quarters ending after the as-of date, summed |
| `spdji.eps_drop` | the drop's record: file, sha256, as_of, `retrieved_at`, the four quarters, the layout version |

**The clocks.**
- **`available_at`** is the as-of cell, taken as the end of that day in New York, with availability kind `observed` (the source's own date, as ruled).
- **`retrieved_at`** is the drop time: the inbox file's modification time, which `rclone copyto` carries over from Drive.
- **The store has no `retrieved_at` column,** so `retrieved_at` is kept in `spdji.eps_drop`. That record's own `available_at` is the drop time. `ingested_at` stays the write instant.

**The layout is declared in `config/spdji_eps.yaml`,** not discovered:
- the sheet `ESTIMATES&PEs`;
- the "Data as of the close of" cell, searched in A1:L20;
- the header labels `QUARTER END` and `OPERATING EARNINGS PER SHR`, on one row;
- the `ESTIMATES` … `ACTUALS` markers in the quarter column;
- a `BOTTOM UP` cell above the block, so the basis is stated, not assumed;
- four forward quarters.

Labels match with whitespace collapsed and case ignored, so a header printed over three lines still matches.

**It fails loudly, naming the sheet and the cell or range, and never guesses.** A layout fault raises `LayoutError` with the file, the sheet and the cell, for example: `sp-500-eps-est.xlsx: sheet 'ESTIMATES&PEs', cell C12: expected an operating EPS figure under 'OPERATING EARNINGS PER SHR' for 2027Q2, found 'n/a'`. The writer then goes STALE with that reason and writes nothing.

`python -m altdata.sources.spdji --check FILE` parses one workbook and writes nothing. Use it on the first drop.

**The printed lines** (`altdata/return_attribution.py`):

- **The forward split** is a new line in the Monthly's What's priced, after the trailing split:
  - before a drop: "The forward split: awaiting the first drop of S&P DJI's EPS workbook …";
  - one drop: the forward EPS and the forward P/E, then "the forward split needs a second drop";
  - two or more drops: the same log identity as the trailing split, over the latest drop against the one nearest twelve months before it. Until a drop that old exists, it uses the earliest drop and prints the span ("Over 30 days (the stored drops' span, not yet twelve months)").
  - Once a drop exists, the "Not available" list no longer names the forward series.
- **The index revision line** opens the Weekly's revision block in Mechanics, above the AI names' line, which is unchanged:
  - before a drop: "awaiting the first drop";
  - one drop: "the first drop; revisions need a second";
  - after that: 1-month and 3-month windows, each comparing the latest drop's four forward quarters against **the same four quarters** in the earlier drop. That is a revision, not the window rolling onto a later quarter. The fixture shows the two differ.
  - A window with no drop that old says so.
- Both figures go into the section's data (`forward_eps`, `forward_pe`, `forward_split`, `index_revision`).

**The sweep** (`scripts/rclone_sync.sh`):
- The AAII pull is generalised to `pull_inbox_file <folder> <name>`, still one `rclone copyto` of one named file.
- It is called for `aaii aaii-weekly.csv` and `spdji sp-500-eps-est.xlsx`.
- It runs after the trees and the prune, and never sets the sweep's exit code.
- `deploy/systemd/chester-backup.service` gains `-%h/chester-data/inbox/spdji` in `ReadWritePaths`. `deploy/systemd/README.md` says so.

**The fixture is synthetic.** The host refuses non-browser clients, so no real workbook was in hand. `tools/validate_sr38_inbox.py` builds an xlsx in the declared layout whose first cell reads "SYNTHETIC FIXTURE -- not S&P DJI data", with made-up figures. **The first real drop is the acceptance.**

## Gates

| Gate | Result |
|---|---|
| validate_sr38_inbox (new, in the Makefile) | 42/0 |
| validate_ai_fcf | 27/0 (one check updated: "awaiting the first drop" replaces the 403 absence) |
| validate_backup | 64/0 (the inbox checks now cover both files) |
| validate_gates | 31/0 |
| validate_deploy | 118/0 |
| validate_feeds_scheduled | 19/0 |
| validate_official_sources | 251/0 |
| validate_aq3_series | 73/0 |
| validate_prediction_markets | 52/0 |
| validate_stack | 66/0 |
| validate_weekly_edits | 89/0 |
| validate_weekly_stack | 68/0 |
| validate_monthly_stack | 261/0 |
| check_registry | OK |
| check_library | 0 failures |

CLAUDE.md's gate count is now fifty-one code gates, forty-eight of them Python.

**The `validate_sr38_inbox` groups:**
- A, the parse: as-of, block, forward four, both string kinds and both date forms;
- B, 13 refusals, each naming its sheet and cell or range;
- C, the rows and clocks, the writer through the publication runner, an idempotent re-read, STALE with no file, STALE on a layout fault;
- D, the printed lines at zero, one and two drops, with the forward split exact in logs and the same-quarter revision against the rolled window;
- E, wiring.

## For Ari: the steps (printed, not run)

**Once, on the box, inside the windows:**

```bash
mkdir -p ~/chester-data/inbox/spdji
# after this branch merges, the self-deploy copies the changed chester-backup.service;
# it is a oneshot, so the next nightly sweep picks it up (no restart needed unless the
# heartbeat names restart_pending: chester-backup.service)
```

**Monthly, after S&P DJI updates the workbook:**

1. In a browser, open S&P DJI's S&P 500 page (spglobal.com/spdji, S&P 500, the "Additional Info" / "Index Earnings" link). Download `sp-500-eps-est.xlsx`.
2. Drop it **unrenamed** into the Drive folder `chester-vendor-checks/spdji`, replacing last month's file.
3. Nothing else. The nightly sweep copies it to `~/chester-data/inbox/spdji/`, and the next writer pass reads it.

**The first drop is the acceptance.** On the box, after the sweep has copied it:

```bash
cd ~/chester-reports && .venv/bin/python -m altdata.sources.spdji --check ~/chester-data/inbox/spdji/sp-500-eps-est.xlsx
```

It either prints the as-of date, the quarters and the forward four, or names the sheet and cell it could not read. If it names one, the fix is the label in `config/spdji_eps.yaml`: send me the message and the cell's actual text.

## Choices made for the operator to overrule

- **`retrieved_at` lives in the drop record, not on each row,** because the store has no such column. The alternatives were a schema change or overloading `ingested_at`, and both are bigger than this item.
- **The as-of date is used as available, as ruled.** S&P DJI typically posts a day or more after the as-of close, so a backtest cut at the as-of evening sees a figure not yet public. The kind is `observed` (the source's own date).
- **The forward four quarters exclude the quarter ending on the as-of date.** At a quarter-end as-of, that quarter is all but reported.
- **The revision windows** are 1 month (28 days) and 3 months (91 days), read against monthly drops. They are in `config/ai_fcf.yaml` under `forward:`.

## Needs you

1. **Merge order:** SR-37/38, then this branch, inside the windows. yes / no
2. **The heartbeat before the first drop.** Until a file is dropped, the writer is STALE ("awaiting the first drop", the AAII precedent), so the 08:30 heartbeat names the three `spdji.*` keys stale. Accept it until the first drop, or make "no file yet" a clean empty run (PENDING)? accept / pending
3. **`available_at` = the as-of date** (ruled). Keep it, or add a declared one-business-day latency for posting (`reconstructed`)? keep / latency
4. **The layout's labels** (`config/spdji_eps.yaml`) are written from the workbook's documented layout, not from a file. The first drop's `--check` confirms or corrects them. ok
