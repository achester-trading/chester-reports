# W-1.1b: the Monthly's prose path (13 Oct 2026)

Branch `w-1-1b-monthly-prose`, from `origin/w-1-1a-audit-fixes` at `ced02e2`. It answers W-1.1a's Needs you 3 (ruled: yes). **It merges after W-1.1a.**

## What was built

**`monthly_macro/prose.py`** now runs W-1.1a's three checks, the way `daily_cascade/stack_prose.write` runs them for the Weekly and the close. A section is withheld on the same messages, and retried with them under the Monthly's existing three attempts.

- **The direction audit** is `direction_faults(text, sec, ed)`.
  - It calls `direction.faults` over `direction.edition_moves(ed, sec["sid"], MONTH_COLUMN)`.
  - It reads the moves from the Monthly's period column ("The month") rather than "Week".
  - It covers every stack frame: a section's, a block's and a summary's. A block or summary reads its parent section's moves, because its `sid` is the parent's.
  - A frame with no edition has nothing to hold a direction to, so it is not audited.
- **The stance check** (`readability.stance_faults`) refuses "bullish/bearish on <macro variable>" and "marked broke".
  - It runs in the stack frames' fault chain (`_stack_faults`).
  - It also runs on the Monthly v2 sections (the fallback), because it needs no edition.
- **The sign rewrite** (`readability.unsign_after_verbs`) turns "fell -3 bp" into "fell 3 bp".
  - It runs after every audit, on every published Monthly section, v2 included.
  - Each result carries `unsigned_rewrites`, as the Weekly's does, and the word count is taken after the rewrite.

## Fixtures

`tools/validate_audit_fixes.py` gains group G. The figures are run 5's (`tests/fixtures/weekly_run5_2026-10-12.json`), placed in a Monthly section whose change column is "The month". It uses no store, no network and no model, and `_market_states` is stubbed so nothing reads the live object.

- **The direction audit fails.** "the dollar softened" against DXY +0.27% is withheld on the Weekly's own message, and the retry prompt carries it. "firmed" then prints. A draft that fails all three attempts prints nothing.
- **"bullish on inflation"** is withheld and the retry writes what is expected. A v2 section is held to the same check.
- **"fell -3 bp"** prints "fell 3 bp" (three rewrites counted), in a stack frame and in a v2 section.
- **A block frame** reads its parent section's moves, and with no edition there is no audit.

## Gates

| Gate | Result |
|---|---|
| validate_audit_fixes | 59/0 (8 new, in group G) |
| validate_monthly | 350/0, 1 skipped |
| validate_monthly_stack | 261/0 |
| validate_monthly_frames | 32/0 |
| validate_readability | 63/0 |

## Choices made for the operator to overrule

- **v2 sections get the stance check and the sign rewrite, not the direction audit.** The v2 fallback has no edition tables to read a sign from. Auditing it would need its payload's moves read a second way.
- **A summary frame is held to its own section's moves**, not the whole edition's.

## Needs you

1. **Merge order:** W-1.1a, then this branch, inside the windows. The only file both touch is `tools/validate_audit_fixes.py`, and this branch is built on W-1.1a's version. yes / no
2. **The acceptance** is a Monthly dry run after both merge (yours, on the box). It shows whether any live Monthly paragraph now trips the direction audit on a month-column sign.
