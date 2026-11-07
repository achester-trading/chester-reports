# B135: item 117, the AI policy-restriction ledger (6 Nov 2026)

Paste B135 (`docs/pastes/B135.md`). Batch 22 item 117 (the order's 99) and
section 0's O-2, on `origin/b129-five-filings`
(`docs/change-order-signal-triage-batch-22-2026-11-05.md`). Its rights are an
input line and a flag. There is no composite change.

**The base.** `origin/main` at `ee04ba21`. `b135-item-117-policy-ledger` is a new
branch from it.

## The schema (`altdata/policy_restrictions.py`, in the register database)

**`policy_restrictions`** holds one row per measure at one stage. Its columns:
- `id`;
- `row_type`: restriction, planned_build or reference;
- `jurisdiction`;
- `instrument`: federal bill, state statute, local statute, ordinance, executive
  order, ballot measure, or unclassified;
- `stage`: introduced, passed, enacted, or unclassified;
- `stage_date` and `title`;
- `project`, `capacity_mw`, `capex_usd` and `announced_date`, null where not
  estimable;
- `source_url`, which is NOT NULL and must start with http(s): no row without
  one;
- `source_kind`;
- `origin`: seed, news_scan or x_triage;
- `status`, which is always 'proposed' at insert;
- `supersedes` (the row a stage change replaces), `note` and `proposed_at`.

**`policy_restriction_reviews`** holds one row per reviewed row: `row_id`,
`decision` (accepted or rejected), `decided_by` and `decided_at`.

- **Append-only.** Triggers refuse UPDATE and DELETE on both tables. A stage
  change is a new row naming the row it `supersedes`, and a review is written
  once.
- **Promotion is the operator's.** It is `python -m altdata.policy_restrictions
  review accept|reject <id>... --by NAME`, the needs-you accept-all, the same
  single human gate as the narrative register's confirm.
- **For the operator:** to add that command's verbs to `.claude/settings.json`'s
  deny list beside `altdata.narratives confirm`. This paste did not edit the
  settings.
- **The reaction column** is computed from the store when the ledger is read:
  the one-day move on the row's stage date. It is not written into the row,
  which would make it editable.
  - It reads SMH (`yfinance.mkt_smh`), labelled as the semiconductor proxy,
    because ^SOX is not stored and D33 bars a new Yahoo symbol. The S&P 500 is
    `yfinance.mkt_gspc`.
  - Either column prints "not stored" when the store holds no close for the day.

## The writers (no by-hand feed)

- **The news writer.** `config/story_queries.yaml` gains a `policy_restrictions`
  group.
  - It sends nothing to a search. Its subject and action terms filter the titles
    of the items the daily voices scan has already read (`voice_scan_seen`, the
    last three days, at most 20 a run).
  - A match is proposed with its URL, its instrument and stage classified by
    `config/policy_restrictions.yaml`'s declared keywords, otherwise
    "unclassified", and its jurisdiction "unclassified" for the operator.
- **The x-triage writer.** A digest's section whose name begins "policy", one
  row a line: `url | jurisdiction | instrument | stage | date | title [| MW]`.
  - A line without a URL, or outside the vocabularies, is skipped and never
    repaired.
  - The digest prompt that writes this section is the operator's chat's, so the
    format here is the contract that prompt fills.
- **When they run.** Both run after the 06:15 voices scan
  (`altdata/sources/voices_scan.py`'s main, never fatal), and the seed runs
  first. No new timer.

## The seed rows (V-99a), as judgment drafts for the accept-all (rule 31)

They are written PROPOSED on the box's first run. All are in
`config/policy_restrictions.yaml`.

**Found and written:**

| Row | Stage | Source |
|---|---|---|
| Ban Artificial Superintelligence Act of 2026, S. 5493 | introduced, 23 Sep 2026 | congress.gov, the bill's text |
| Ban Artificial Superintelligence Act of 2026, H.R. 10538 (the House companion) | introduced, 24 Sep 2026 | congress.gov, the bill's text |
| Wells, Maine, Article 5: a six-month data-center moratorium on the 3 Nov warrant | introduced (on the ballot), 3 Nov 2026 | the town's warrant (wellstown.org) |
| Goldman Sachs: up to 45% of planned US capacity could face temporary moratoria | reference, 4 Nov 2026 | reporting of the note (investinglive.com); the note itself not read |

**Not found, and left unwritten:**
- **The 3 Nov measures' results**, Wells' enacted stage among them. No
  jurisdiction's certified result was found from a primary source. The tallies
  (40 of 41 restrictive) are reporting and Ballotpedia.
- **The incoming governors' stated positions.** They are on campaign pages whose
  addresses carry the person's name, which stay chat-side (D38), and no official
  statement was found.
  - The order names Texas, Ohio and Georgia. Reporting of Goldman's note names
    Texas, Georgia and Michigan. Ohio is not confirmed.

**Names.** The sponsors' own press releases carry their names in their
addresses, so the bill cites congress.gov.

## The denominator and the flag (O-2)

- **The denominator** is "tracked planned capacity": the accepted `planned_build`
  rows' MW.
  - **Its state now is empty.** The seed carries no planned build: item 23's
    Census construction series names no projects, and none was proposed before
    the news writer runs.
  - So the flag prints "denominator: none (no accepted planned_build row); the
    flag is not computed".
- **The flag** fires when accepted, enacted, not-superseded restrictions cover
  10% or more of that MW. The threshold and its review date, 6 Feb 2027 (one
  quarter after the first row, the seed of 6 Nov), are in config. A reference row
  never counts.

## The prints

| Where | What |
|---|---|
| The close's Narratives | one line, only on a day the flag is ON |
| The Weekly's Narratives | the flag's line every week, with its denominator |
| The Monthly's slow layers | the Factor I input line, the Factor VI (Internal Order) input line, and the rows with their reaction columns |
| The Disruptive Themes refresh | the same two lines and table, through `themes_block` |

The Monthly takes them through `config/stack_hooks/monthly-slow-policy-restrictions.yaml`,
after the T&B harness.

## The gates

| Gate | Result |
|---|---|
| `validate_item_117` (new; clock pinned) | 39 passed, 0 failed |
| `validate_voices` | 73 passed, 0 failed |
| `validate_themes_panels` | 19 passed, 0 failed |
| `validate_stack` (in full) | 84 passed, 0 failed |
| `check_registry` | OK |
| `validate_gates` | 32 passed, 0 failed |
| `check_library` | 27 papers, 0 failures, 0 warnings |

Run as well: `validate_audit_3a` 88/0 (once the catalogue line and the count were
in), `validate_weekly_stack` 83/0, `validate_monthly_stack` 268/0,
`validate_tb_harness_fpr` 47/0 and `validate_st_t5_render` 46/0.

**Outside the paste's file list:**
- `config/catalogue_commands.yaml`: one line, which `validate_audit_3a` requires;
- CLAUDE.md's gate count, 167 to 168;
- the Monthly's hook file.

**For chain-13's merge.** B134 makes the same 167-to-168 edit, so whichever
branch merges second sets the count to 169 code gates (166 Python).

## Two faults the gate found and this paste fixed

- **A duplicate proposal held the write lock.** The failed UNIQUE insert's open
  transaction blocked the store's next writer. The writer now rolls back on that
  path, and on a repeated review.
- **Unfinished read cursors are now drained**, so a read never holds a shared
  lock.

## CI

Read once after the push.
