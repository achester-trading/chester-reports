# A80 notes: Learning Loop v2, LL-2 and LL-4

**Session A, 26 Oct 2026, branch `a80-learning-loop-ll2-ll4`.** The paste is `docs/pastes/A80.md`. The ruling brief was read from its own branch without merging it (`git show origin/b65-learning-loop-v2:docs/briefs/learning-loop-v2-brief-2026-10-25.md`): sections 2.6, 2.7, 3, 4 and 6, and decisions 9, 10 and 11 as ruled on 25 Oct 2026.

**Base:** `origin/b73-learning-loop-ll1` at `94552ea0e1976776b70aae3016152881fa72bf05` (LL-1's decomposition and LL-3's error corpus).

Code, branch-only; merges after the 1 Nov Monthly. No box, no units, no `.env`, no register write. **S1 is not on this base:** there is no `tools/stitch_counts.py` and no `config/stack_hooks/`. So the two gates go into the Makefile's list directly, CLAUDE.md's count is recounted by hand, and LL-2 prints through the Monthly's existing Lab-report hook, as B73's did.

**Commits:**
1. `e785cb4b`: the paste.
2. `bbd64d59`: LL-2.
3. The LL-4 commit, which also carries these notes.

---

## LL-2: `altdata/value_of_information.py`

Computed at read from the stored rows, never stored, no model.

### The method (declared, not fitted)

- **The rows:** the probability ledger's resolved rows by the as-of, live sources only (`decision_quality.resolved_rows`), each with its Brier.
- **What was missing at a row's emission:** the row's own `missing_inputs`, united with the market-state object held at the emission instant (`regime.latest(as_of=emitted_at)`), whose absent dimensions are read by name and absent contradiction rows as `leg:<row>`.
  - A row with neither is **unrecorded** and enters no comparison. NULL is never read as "nothing missing".
  - The object is read through `alpha/store.py`'s `ReadOnlyStore` (`mode=ro`, no schema, no pragma), so a build leaves the database byte for byte.
- **The cell:** source family × horizon bucket, `decision_quality`'s own (1-7d, 8-31d, 32-92d, >92d).
- **The statistic,** for each input X missing anywhere in a cell: the mean Brier of the recorded rows missing X, less that of the recorded rows that had it. Positive means the absence cost accuracy. It is printed with n on both sides.
- **The interval:** a 95% percentile bootstrap.
  - **2,000 resamples**, each side resampled independently with replacement.
  - **Seed 20261025**, the ruling date, combined with the entry's name (`family|horizon|input`) in `random.Random`.
  - Each side is sorted before resampling, so neither the order entries are computed in nor the rows' storage order moves the interval.
- **The share:** rows missing X over the cell's recorded rows.
- **From the error corpus:** how many stored misses recorded X missing at emission, ledger rows and grades together.
- **The ranked list:** every entry with at least **30** rows missing the input (the brief's section 5) and at least one row that had it, by the Brier difference, largest first. Ties go by the interval's lower end, then by rows affected. An entry below 30 prints as accruing and is not ranked.

### Where it prints

- **The Monthly's Lab report:** `monthly_macro/run.py` calls `value_of_information.with_lab_report` right after decision quality's hook, which never raises. With no lab, the section is its own attachment, `value_of_information_<YYYY-MM>.md`.
- **The Doctrine pack:** `python -m altdata.value_of_information pack`. There is no pack renderer in code (B73's notes, needs-you 1), so the pack's author pastes the section.
- **Also:** `list` (the line and the table) and `json`.

### The key

`learning.value_of_information` (`derived_probability`, `trigger_eligible: false`) is added to B73's `market_state_barred` entry. It is computed at read, so `check_store_registry` on the box will list it among the registered keys with no rows, as with LL-1's keys.

### `missing_inputs` at emission

B73 had already given every ledger write path the field, so none was left lacking. Most of those writes are `[]`, and one of them was hiding real absences:

| Source | Change | missing_inputs now |
|---|---|---|
| `book_b_candidate` (`altdata/book_b_scanner.py`) | the candidate carries `missing_inputs_of(confs, pv, adv)`; the ledger write passes it (one line each) | `confirmation:<family>` for each confirmation family it could not read, `volume` when the volume leg is unconfirmed, `dollar_adv` when the 20-session dollar ADV is not stored |

The rest stay as B73 left them:
- `market_state` carries its object's absent dimensions.
- `daily_close_outlook`, `weekly_stance`, `narrative_register`, `alt_asset:<family>` and `monthly_macro` are computed rows with nothing recorded missing, so `[]`.
- The operator's by-hand `record` and every older row stay NULL. For those, LL-2 still reads the object held at their emission.

## LL-4: `altdata/postmortem.py` and `altdata/redteam_shadow.py`

### The post-mortem

`python -m altdata.postmortem week [--saturday D] [--db PATH] [--out-root DIR] [--dry-run] [--shorten]`

- **Which misses:** every error-corpus row whose outcome landed in the seven days ending the Saturday (its `resolved_at`, or its `graded_at`). The default Saturday is the one on or before today, UTC.
- **Which file:** one per row, `<out-root>/docs/postmortems/<saturday>/<corpus_id>.md`. The default out-root is the checkout.
- A hit is not in the corpus, so it gets no file.
- An existing file is never rewritten, because the operator may have stamped it.

**The template**, every line read from a stored row:

```
# Post-mortem <corpus_id>
Code-built (postmortem-v1) from the error corpus row ... Nothing below is a model's;
nothing below names a cause. The operator's answers are the cause field.

## 1. What was said            the said_json fields as stored
## 2. What happened            the happened_json fields; the margin (its unit)
## 3. What was missing at emission
   - the source's missing inputs / the object's absent dimensions / awaiting legs
     ("not recorded" where NULL) / the object read
## 4. The decision it fed      for a grade, the register's row: book, instrument,
                               direction, horizon, status, operator_action,
                               decision_time, thesis, invalidation, falsifiers,
                               counter_thesis, setup_id; for a ledger row, "none
                               recorded" (the ledger records no link)
## The operator's stamp (Doctrine 9.2; blank until the Sunday session)
| Field | Question | Answer |
| thesis | Was the thesis wrong? | |
| timing | Was the timing wrong? | |
| expression | Was the expression wrong? | |
| size | Was the size wrong? | |
| regime | Did the regime change during the trade? | |
| signal | Was the signal itself degraded (...)? | |
| rule_broken | Was any rule broken, and which? (the seventh field) | |
| note | One-line note | |
```

**The shortening (`--shorten`, off by default).**
- One call per file through `model_meter` (report `postmortem`, section `shorten`), with `daily_cascade.narrative.DEFAULT_MODEL`. The model sees parts 1 to 4, never the stamp.
- Its paragraph is **refused**, and the file keeps the code-built parts with the reason, in two cases:
  - it names a cause: a `Cause:` field, or the declared causal wording (`because`, `due to`, `driven by`, `led to`, `caused`, `explains` and the like, `CAUSE_WORDS`);
  - it carries a figure the rows do not hold (`numeral_audit.audit` over the corpus row and the decision).
- A clean paragraph prints above the stamp under "Shortened". The stamp stays blank.

### The shadow Red Team

`python -m altdata.redteam_shadow run [--date D] [--db PATH] [--out-root DIR] [--dry-run]`

- **A material packet:** a decision with a replay packet in `decision_packets` (26.2 #3), the packet created on the date (UTC).
- **Blinded.** It is shown the instrument, direction, book, horizon, setup, engine, edge type, decision time, entry condition, invalidation, time stop, risk budget, expected return and downside, benchmark, horizon alignment, size, the packet's cutoff and its data manifest's input paths. It is never shown the thesis, counter-thesis, falsifiers, mechanism, operator action, status, thesis state, `review_changed`, `red_team`, the outcome or the falsifier date.
- **One call per packet** through `model_meter` (report `redteam_shadow`, section the packet id), with the narrative step's model. A packet whose file exists is not called again.
- **The write path:** `<out-root>/docs/redteam/shadow/<date>-<packet>.md`, and nothing else.
  - `shadow_path()` keeps any packet id inside that directory and refuses an undated target.
  - The register is opened `mode=ro`, and the module carries no SQL write and no register writer.
  - The gate proves the database is byte for byte unchanged after a run, with `review_changed` and `red_team` still NULL.
- **EL-9's gate is unchanged:** Gate 1.5 complete and 30 graded packets.

**The prompt, verbatim** (`SHADOW_PROMPT`; the blinded evidence follows as JSON):

```
You are a red team reviewing a proposed position before entry. You are shown the evidence the position was entered on. Its thesis is withheld from you on purpose.

From the evidence alone:
1. State the strongest case AGAINST taking this position, in at most five sentences.
2. Name up to three observable conditions that, if they occurred before the horizon, would show the position wrong.
3. Say whether the stated invalidation and time stop are consistent with the horizon, in one sentence.

Rules, every one binding: use no number that is not in the evidence; do not guess the thesis; do not recommend a size, an order or a trade; write no preamble.

THE EVIDENCE (JSON):
```

## Box commands and timers (the operator's)

Run inside the windows, after the merge. These are commands only. No unit file is added on this branch, and enabling a timer is the operator's.

```
cd ~/chester-reports
.venv/bin/python -m altdata.error_corpus backfill --dry-run       # B73's; the corpus first
.venv/bin/python -m altdata.error_corpus backfill
.venv/bin/python -m altdata.value_of_information list             # the box's search order
.venv/bin/python -m altdata.postmortem week --dry-run --out-root ~/chester-data/outbox/learning
.venv/bin/python -m altdata.postmortem week --out-root ~/chester-data/outbox/learning
.venv/bin/python -m altdata.redteam_shadow run --dry-run --out-root ~/chester-data/outbox/learning
.venv/bin/python -m altdata.redteam_shadow run --out-root ~/chester-data/outbox/learning
```

**The timer lines, for a later unit paste:**
- **Post-mortems:** `OnCalendar=Sat *-*-* 18:00 America/New_York`. The Saturday before the Sunday session, after Friday's grades, clear of the Sunday 05:00 Weekly. The step is `error_corpus backfill` then `postmortem week`.
- **Shadow Red Team:** `OnCalendar=Mon..Fri *-*-* 23:00 America/New_York`. After the day's packets, inside the 17:20–23:30 window. The step is `redteam_shadow run`.

## Gates and the count

- **`tools/validate_value_of_information.py`**, 28 checks:
  - the fixture where credit carries all the error ranks it first, with a difference of 0.4651 against the closed form and an interval excluding zero;
  - an input whose rows forecast well ranks below with a negative difference;
  - 29 affected rows accrue;
  - unrecorded rows are excluded;
  - the seed, the resamples and order-independence;
  - an input that costs nothing has an interval holding zero;
  - the object union and NULL;
  - the corpus counts;
  - the Lab hook, the pack, the database unchanged, no model, no write;
  - the key barred, the catalogue line, Book B's legs.
- **`tools/validate_postmortems.py`**, 37 checks:
  - a miss yields a file with the six blank fields, the seventh and the note; a hit and an out-of-week miss yield none;
  - the six are 9.2's words;
  - no rewrite, and a dry run writes nothing;
  - the shortening is off by default, and refuses a cause (three wordings) and a figure not in the record;
  - the shadow pass: one file under the shadow directory and nothing else; the register byte for byte; `review_changed` and `red_team` NULL; blinded; no second call; the path guard; no SQL write; `mode=ro`; `model_meter`;
  - the catalogue lines and the imports.
- **The count by hand** (S1 absent): code gates 142 → 144, Python gates 139 → 141. LL-2's commit carries 143/140.

**Run on the laptop, one at a time:**

| Gate | Result |
|---|---|
| validate_value_of_information | 28/0 |
| validate_postmortems | 37/0 |
| validate_decision_quality | 35/0 |
| validate_error_corpus | 28/0 |
| validate_register | 180/0 (2 skipped) |
| check_registry | OK |
| check_library | 0 failures, 0 warnings |
| validate_audit_3a (the count, the catalogue) | 88/0 |
| validate_gates | 32/0 |
| check_master_guide | 12/0 |
| validate_book_b_scanner (the candidate's new field) | 63/0 |

The Monthly's stack gates were not run locally. The one change on that path is the Lab report hook's two lines in `monthly_macro/run.py`, after the stack has rendered, so those gates are CI only.

**The laptop's search order: none.** The laptop's store (`data/chester.db`, 15 Oct) holds **0** ledger rows, so there are 0 resolved rows, 0 entries and no top three. The box's run is the first that can rank anything.

## Needs you

1. **Where the files land on the box.** The paste names `docs/postmortems/` and `docs/redteam/shadow/`, and those are the defaults. On the box, that writes untracked files into the checkout the wrappers `git pull --ff-only`. The box commands above use `--out-root ~/chester-data/outbox/learning`. Rule which: the outbox, with the files brought back to a branch by a session, or the checkout.
2. **The two timers.** The lines above are proposals; no unit file was written. Say if a unit paste should add them, and when.
3. **What counts as a material packet.** I took every decision with a replay packet (26.2 #3). If EL-9 means only Books B and C, or a risk floor, say so (one line in `material_packets`).
4. **`CAUSE_WORDS` is a session-set list.** A shortening that says "because" in a non-causal sense is refused too. The cost is one paragraph, never the file.
