# AQ-6 — the thesis register: build notes (10 Oct 2026)

Branch `aq-6-thesis-register`, built from the change order
`docs/change-order-alternative-assets-quarterly-2026-10-10.md`: §6, §4.1 items 1, 2
and 10, and the AQ-6 row of §11. Not merged.

## What was built

**The thesis file.** `config/alt_asset_theses/<YYYY>q<N>.yaml`, one per quarter,
written by the operator. Each family block carries:

- **The 12-month scenario set.** Each scenario has a name, a probability, a
  horizon date and a resolution criterion. The weights sum to one.
- **The 3-month thesis.** One measurable, with its probability, a falsifier (also
  a measurable) and the Book it informs.
- **The book.** Per horizon, either the register's draft fields or
  `no_draft: <reason>`. The draft fields are instrument, direction, thesis, edge,
  horizon, size, invalidation, counter-thesis, and the portfolio role in XVII's
  words.

A criterion is `{series, comparator, level, date}`:
- `series` is a registered store key (`metrics_registry.yaml`).
- `comparator` is one of `>=`, `>`, `<=`, `<` or `between`.

The 3-month thesis also takes §26.12's statement as optional fields: market
expectation, the Chester read, the difference, the evidence, and what changes the
view. `config/alt_asset_theses/TEMPLATE.yaml` ships the shape, with one worked
metals example. It is marked `example: true`, its numbers are illustrative, and
the loader refuses it outside `--dry-run`.

**The loader and the seed.** `altdata/thesis_register.py` holds the rules. The
command is:

```
python -m altdata.probability_ledger seed-alt-asset --file <yaml> [--dry-run]
```

It refuses, listing every reason rather than only the first:
- a prose criterion;
- an unregistered series;
- weights that don't sum to one (reported, never normalised);
- a date that is not in the future at `written_at`;
- a missing falsifier;
- a missing Book;
- a deep family that is absent or sits out;
- a Thailand draft.

Each probability is recorded with:
- `source = alt_asset:<family>`;
- `scenario_set = <family>-<YYYYqN>-12m` or `-3m`;
- `emitted_by = operator`;
- `emitted_at` = the file's `written_at`.

Idempotency comes from `probability_id`: re-running the same file writes nothing.

The file's vintage (sha256, name and `written_at`), the measurable's structure,
the falsifier and the value at emission go in `alt_asset_theses`. That table sits
beside the ledger's own, in the same database, and is immutable by trigger.

The dry run reads the ledger and the store read-only and writes neither. It also
runs every draft through the register's own write path, against a throwaway
register. So the Brookfield refusal and the currency guard speak at the dry run.

**Resolution by code.** `resolve-alt-asset` reads each due thesis's series through
`ObservationStore.as_of` at the resolution cutoff, and compares the last period
observed on or before the horizon date with the level.
- **When it resolves:** only once that period is final, meaning a later period is
  stored or the series' grace has passed (daily 7 days, weekly 14, monthly 50,
  quarterly 120).
- **Freshness:** the period must be fresh enough to stand for the date (daily 10
  days, weekly 14, monthly 45, quarterly 120).
- **Otherwise:** it waits and says why.
- **Replay:** the observation read goes into the ledger's `resolution_note`.

The one manual path is `resolve-manual --id --outcome --note`. The note is
required, every use is logged to `alt_asset_manual_resolutions`, and the grading
views mark the outcome as resolved by hand.

**Grading views.** `show --source alt_asset` reports, per family, quarter and
horizon:
- the Brier against the coin's 0.25;
- hit, miss or not yet due (a 3-month thesis is a hit when its probability was
  on the side of the outcome; p = 0.5 is "no call");
- for a 12-month set, the ordering-and-direction score: did the highest-weighted
  scenario occur, at what rank the scenario that occurred stood, and was the top
  scenario's direction from the emission value right;
- a flag when more than one scenario held.

**Two renderers.**
- **`graded_table(quarter)`: the Quarterly's chapter opener.** For the quarter's
  theses it gives the grade, the Brier and one line of why, written by code from
  the read. Earlier 12-month sets are carried while still open.
- **`seed_table(cutoff)`: the Monthly's slow layers.** It prints the theses the
  ledger holds for the coming quarter in the ledger's form ("The ledger holds n
  theses for 1Q27; …"), each weight beside its Brier where graded. It is wired
  after "Base rates: Top & Bottom", with no chart. The connection is read-only,
  so the Monthly never writes a weight, nor even the side table's schema.
- **Each fact printed once.** The Monthly v2 Ahead scenario list now leaves
  `alt_asset:*` rows to the seed table.

**The draft-per-horizon rule.** Each deep family (metals, oil, currency, em,
china, crypto) owes a book line per horizon: a draft or `no_draft: <reason>`.
- **Defaults:** a 3-month draft goes to Book B (`positional`), a 12-month draft
  to Book A (`strategic`). The time stop is the thesis date.
- **Fields:** `engine_id` is `operator`. The note carries the portfolio role and
  a `[counter-structural]` tag where the file says so.
- **Packet:** an immutable packet pins the thesis file and carries the cost row.
- **Status:** the writer hard-codes `status="draft"` and asserts the entry reads
  back as draft. A `status:` key in the file is ignored, and promotion stays the
  operator's, through `decide.py`.
- **The record:** both drafts and no-draft lines are recorded in
  `alt_asset_books`.
- **Light families and Thailand:** a light family's book is optional. Thailand's
  may only say `no_draft` (the §4.10 isolation).

**The cost row.** It comes from `altdata/sources/ibkr_costs.estimate`, the rate
card, and never contacts a broker.
- **What it prices:** commission, when the draft carries a `quantity`. The price
  is read from `price_series` at emission.
- **What it does not:** spread, roll, borrow and FX hedge are named as not priced
  (schedule_v1 prices commission and margin only).
- **Margin:** stays None, because without an account read there is no baseline.

**Gate.** `tools/validate_thesis_register.py`, 66 checks, fixtures only, never
the live store. It covers:
- the loader's refusals;
- the seed and its idempotency;
- the draft rule and its gate;
- resolution from a synthetic store;
- the manual path;
- Brier and ordering against hand-computed values;
- both renderers' shapes, and the Monthly wiring;
- coherence on every alt_asset set;
- the CLI.

It is in the Makefile's list.

## Choices made in the build, for the operator to overrule

1. **A 3-month thesis is a one-row set, `<family>-<q>-3m`, as the brief names.**
   The ledger's `coherence()` now treats a one-row set whose id ends `-3m` as a
   binary claim with its complement implicit, so it is coherent at any
   probability. Two rows under such an id still fail.
2. **One file per quarter.** A second `written_at` for a quarter already seeded
   is refused, because two sets under one id would sum to two. A revision is the
   next quarter's file; an edited forecast under the same `written_at` is refused
   too.
3. **The backdating guard.** A first seeding more than 7 days after `written_at`
   is refused. A `written_at` after the seeding instant is refused.
4. **Horizon typo guards.** 3-month: up to 200 days from emission (the 1Q27
   thesis written 7 Nov runs about 144). 12-month: 180 to 550 days.
5. **The family list.** It is the brief's eleven. China is a family of its own
   beside EM, and it is deep.

## Seeding at Doctrine #2 (Sat 7 – Sun 8 Nov)

1. **Write the file.** Copy `config/alt_asset_theses/TEMPLATE.yaml` to
   `config/alt_asset_theses/2027q1.yaml`, delete `example: true`, and set
   `quarter: 2027q1` and `written_at` to the instant the theses are written
   (ISO, with offset). Write each family from drivers before looking at the
   prior. All six deep families are required. A light family may say
   `not_this_quarter: <reason>`.
2. **Commit it and merge it to main inside a window.** A merge is a box write.
   The box's wrappers pull it at the next timer.
3. **On the box, dry run first:**
   ```
   cd ~/chester-reports
   .venv/bin/python -m altdata.probability_ledger seed-alt-asset \
       --file config/alt_asset_theses/2027q1.yaml --dry-run
   ```
   Every refusal prints, and the exit is 2 on any refusal. The dry run shows each
   forecast with its value at emission, and each book line with its cost row.
4. **Seed within 7 days of `written_at`:** the same command without `--dry-run`.
   It records the forecasts and writes the draft register entries (status draft).
5. **Check:** `.venv/bin/python -m altdata.probability_ledger show --source alt_asset`.
6. **Promoting a draft:** that is `decide.py`, by hand, as for any decision.
7. **What happens next:** the 1 Dec Monthly prints the set in its slow layers.
   The January Quarterly grades it.

## What waits for AQ-1 (the `quarterly` cadence) and after

- **The chapter opener's placement.** `graded_table()` is a function with a
  fixture. AQ-1/AQ-2 put it on each chapter's lead page, with the falsification
  lines beside it.
- **Scheduled resolution.** Nothing runs `resolve-alt-asset` on a timer yet. The
  first horizons are 31 Mar 2027 (3-month) and the end of 2027 (12-month).
  - Intended design: the Quarterly's run calls `resolve_due()` before its opener.
  - Until then, the operator runs it.
- **The confidence line's "Brier of the chapter's theses to date".** It reads
  `grades()`; it belongs to AQ-2.
- **The Quarterly's draft slate in the book section.** It reads `alt_asset_books`;
  it belongs to AQ-2.
- **AQ-10's draft-per-horizon gate over a rendered edition.** The rule's own gate
  is here, at load.
