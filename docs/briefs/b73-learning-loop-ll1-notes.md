# B73 — Learning Loop v2, LL-1 and LL-3: build notes

**Branch** `b73-learning-loop-ll1`, from `origin/chain-7-main` at
`dfa14a5433c32018c586b56fdf3c04d318e27492`. Code, branch-only; merges after the 1 Nov
Monthly. The paste is `docs/pastes/B73.md` (the directory is new on this base). The
ruling brief was read from its own branch without merging it
(`git show origin/b65-learning-loop-v2:docs/briefs/learning-loop-v2-brief-2026-10-25.md`).

**S1 is not on this base**, so the two gates are added to the Makefile's list
directly (no `GATE_KIND`: code gates carry none), CLAUDE.md's count is recounted by
hand (142 code gates, 139 Python, 3 shell; 8 data gates), and the print goes through
the Monthly's existing Lab-report hook rather than a `config/stack_hooks/` file.

No model call anywhere in this paste (R-4). No store write in LL-1; one new table,
append-only, in LL-3.

## LL-1: `altdata/decision_quality.py`

All of it computed at read from the stored rows, as of an instant. Dry-run sources
(`dryrun.`) are never counted.

### The decomposition, as coded

Over the `probabilities` rows resolved by the as-of. Ten bins of width 0.1 on the
stated probability (`min(int(10p), 9)`, so 1.0 is in the top bin).

    BS  = (1/N) Σ (p_i − o_i)²
    REL = (1/N) Σ_k n_k (f̄_k − ō_k)²        reliability (lower is better)
    RES = (1/N) Σ_k n_k (ō_k − ō)²          resolution (higher is better)
    UNC = ō (1 − ō)                          uncertainty
    W   = BS − (REL − RES + UNC)             the within-bin term

W is zero when every forecast in a bin is equal; it is printed so the four always
add to the printed Brier. Cells: source family (the source to its first colon) ×
horizon bucket (days from emission to the horizon date: 1–7, 8–31, 32–92, >92). A
cell under 100 resolved rows prints `accruing (n=k of 100)` and no figure.

### The counterfactual ledger, three definitions

One grade per decision, its latest under the grader's current method, joined to the
decision's book.

1. **Declined** (the operator's filter): `operator_action` DECLINE or status
   `declined`. Mean ruled R and mean return, with n.
2. **Draft** (the cost of abstention): status `draft`, never acted on. The same.
3. **The stack's implied stance against Book Z**: each resolved Weekly stance row
   (source `weekly_stance`) read as long SPY above 0.5 and cash below it (0.5 is no
   stance and is skipped). Its week's return comes from Book Z's own marks
   (`paper.benchmark`, read as of), and it is set beside the cash, SPY and 60/40
   ledgers over the same weeks. A week without marks at both ends is counted as
   unmarked, never guessed.

Taken (TAKE or MODIFY, `register/scoreboard._taken`) prints beside the declined and
draft cells. A cell under the scoreboard's `min_n` (10) prints `accruing (n=k)`.

### The one line

The system Brier with its decomposition, and the system expectancy in ruled R (the
taken decisions' latest grades), each over the last 13 and 52 weeks against the
window of the same length before it, each with its n. The Brier floor is 100; the
expectancy floor is `min_n` 10.

### Where it prints

- **The Monthly's Lab report:** `monthly_macro/run.py` appends the section to the
  Lab report attachment through `decision_quality.with_lab_report`, which never
  raises. With no `alpha.db`, the section goes as its own attachment,
  `decision_quality_<YYYY-MM>.md`. It is appended outside `alpha/` because
  `validate_alpha_no_orders` bars the lab from importing the ledgers.
- **The Doctrine pack:** there is no pack renderer in code (the pack is a
  session-written document), so `python -m altdata.decision_quality pack` prints
  the pack's section for the session that writes the pack.
- **The Weekly** gains nothing.

### Keys

All three are barred from the market-state object (one `market_state_barred` entry,
citing the brief):

- `brier.decomposition` (`derived_probability`);
- `grade.counterfactual` (`derived_grade`);
- `learning.error_corpus` (`derived_probability`).

The two LL-1 keys are computed at read and never stored as observations, so
`check_store_registry` on the box will list them among the registered keys with no
rows. That is expected.

## LL-3: `altdata/error_corpus.py` and the `error_corpus` table

### What a miss is (declared)

- **A ledger row:** resolved, live source, Brier above 0.25 (the forecast was on the
  wrong side of one half). The margin is the Brier less 0.25.
- **A grade:** under the current method, ruled R below zero; where no R exists, the
  return in the decision's direction below zero. The margin is that R, or that
  return in percent.
- **Never a miss:** a flat or hedge grade (neither figure), a hit, an unresolved row.

### Schema (chester.db; append-only; UPDATE and DELETE refused by trigger)

| Column | Meaning |
|---|---|
| corpus_id TEXT PK | sha256(kind, ref_id)[:32]: one row per miss, so a rebuild writes nothing |
| kind | `probability` or `decision` |
| source | the ledger source, or `register:<book>` |
| ref_id | probability_id; or `decision_id|horizon|graded_at` |
| emitted_at | the emission's as-of (a grade: its decision_time) |
| said_json | the stored row as stored (claim, probability, criterion…; or the decision's fields on the grade) |
| happened_json | the resolution (outcome, resolved_at, brier) or the grade (prices, return, R, invalidation) |
| margin, margin_unit | `brier_over_coin`, `r_ruled` or `return_pct` |
| absent_dimensions | JSON, from the market-state object held at the emission instant (`regime.latest(as_of=emitted_at)`); NULL when none was held |
| awaiting_legs | JSON, that object's `absent_contradictions`; NULL likewise |
| missing_inputs | JSON, the ledger row's own field; NULL = not recorded |
| object_session | the object read |
| recorded_at, method_version | `error-corpus-v1` |

### The `missing_inputs` field at emission

`probabilities` gains a nullable `missing_inputs TEXT` column, added by `ALTER` when
the ledger opens. A trigger, `probabilities_missing_inputs_immutable`, refuses any
change once it is written. `ProbabilityLedger.record(..., missing_inputs=)` writes it:
`None` stores NULL ("not recorded"), and `[]` means none recorded missing.

Each source passes it with a one-line addition:

| Source (ledger `source`) | Write path | missing_inputs |
|---|---|---|
| `market_state` | `altdata/state_calibration.py` `write_ledger` | the object's `absent_dimensions` |
| `daily_close_outlook` | `daily_cascade/outlooks.py` | `[]` (only computed rows are written) |
| `weekly_stance` | `daily_cascade/precis.py` | `[]` |
| `book_b_candidate` | `altdata/book_b_scanner.py` | `[]` |
| `narrative_register` (claims) | `altdata/narratives.py` (implied outcome) | `[]` |
| `narrative_register` (hypotheses) | `altdata/narratives.py` (hypothesis entry) | `[]` |
| `alt_asset:<family>` | `altdata/thesis_register.py` | `[]` |
| `monthly_macro` | `altdata/probability_ledger.py` `seed_from_monthly` | `[]` |

Two writes are left NULL: the operator's by-hand `python -m altdata.probability_ledger
record` (an operator-entered forecast records nothing about its inputs), and every
row written before this branch. Grades carry no `missing_inputs`, because the register
records no such field. Their absent dimensions and legs come from the object at the
decision time.

### Not wired to a timer

The corpus is built by its command and printed nowhere. LL-5's critic reads it, and
the critic paste should decide whether the build rides the EOD pass after the grader.

## Gates

- `tools/validate_decision_quality.py`, 35 checks:
  - the closed-form fixture: 50 at 0.2 with 10 resolved 1, and 50 at 0.8 with 30
    resolved 1, gives REL 0.0200, RES 0.0400, UNC 0.2400, Brier 0.2200 and W
    0.0000, each to four decimals;
  - the floor (99 accrues, 100 prints);
  - the four trend windows and their counts;
  - the counterfactual ledger and the stance by hand;
  - the hook, the pack and the Weekly's silence;
  - no model import, read-only.
- `tools/validate_error_corpus.py`, 28 checks: a miss becomes a row and a hit does
  not; append-only (a second build is a no-op, UPDATE and DELETE are refused, a dry
  run creates nothing); missing_inputs round-trips (list, `[]` and NULL) and is
  immutable in the ledger; the object columns; every write path; no model.

Run locally, all passing: the two new gates, validate_grader, validate_register,
check_registry, check_library, validate_audit_3a (after the catalogue lines for the
two command modules), validate_gates and check_master_guide.

**The laptop's store:** 0 resolved ledger rows, 0 grades, so 0 corpus rows
(`backfill --dry-run`: 0 misses). Every cell prints accruing.

## Box commands (for chain-8's box sheet)

    cd ~/chester-reports
    .venv/bin/python -m altdata.error_corpus backfill --dry-run     # counts, writes nothing
    .venv/bin/python -m altdata.error_corpus backfill               # then writes
    .venv/bin/python -m altdata.error_corpus count
    .venv/bin/python -m altdata.decision_quality line               # the box's line, read-only
    .venv/bin/python -m altdata.decision_quality pack               # the pack's section

The first ledger open after the merge adds the `missing_inputs` column and its
trigger: an additive `ALTER`, with no existing row edited.

## Needs you

1. **The Doctrine pack:** no renderer exists in code. Is the `pack` command enough,
   with the pack's author pasting its output, or should a later paste build a pack
   renderer?
2. **When the corpus builds:** it has no timer, by the paste's rule ("prints nowhere
   yet"). Should LL-5 put it in the EOD pass after the grader?
3. **The stance's short side:** the Weekly stance is read as long SPY or cash. If a
   stance below 0.5 should be read as short SPY instead, say so (one line).
