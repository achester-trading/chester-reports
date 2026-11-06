# B121 notes: the merge-week sheet filed as a runbook

Paste B121 (`docs/pastes/B121.md`), 2 Nov 2026. Branch
`b102-readable-editions-register`, continued from `f6bdc7c3`.

**The paste's copy.** The instructions are kept verbatim. Its attachment is not
repeated: it points at the runbook, which holds the sheet. In both, the laptop's
checkout path, which carries the login, is replaced by "<the laptop's checkout>".

## What was filed

**`docs/runbooks/merge-week-2026-11-03.md`.** The sheet's text is kept as written,
apart from the checkout path. Its sections:
1. **A header** (B121):
   - the sheet was written on 2 Nov from A105's and A106's scripts;
   - the chains are the real merges' vehicle, as chain-7 and chain-8 were;
   - who "you" and "me" are;
   - **the chain pastes by id, with their `docs/pastes/` paths:** A107, A108, B112,
     A109, B113, B114. Each file is committed by its session and reaches main with
     its chain.
2. What this is, why chains, the rules for the day, the three PowerShell moves and
   the deploy.
3. **Tuesday evening**, steps 1–15.
4. **Wednesday**, steps 16–22, with the box steps of step 17.
5. **If something breaks.**
6. **Outcome** (new, empty): one row per chain (9, 8, 10, 11, 12) and B114's sweep,
   with the PR, merge commit, CI run and deploy time, for the session that closes
   the week.

The PR bodies are kept whole. The sheet carries no name and no secret: the key and
the names list are placeholders (`<the key>`, `<name>`).

**`docs/runbooks/README.md`** is new: no runbooks index existed. It has one line per
runbook (restore, push day, the merge week). The merge week's line:

> `merge-week-2026-11-03.md` (linked): the merge week of 3–4 Nov 2026. Five chains (9, 8, 10, 11, 12), then B114's names sweep, with four deploys and an Outcome section for the session that closes the week (B121).

## For the operator: three places the sheet disagrees with itself (kept as written)

1. **The deploys.** "Deploy at the three points marked", but the sheet has four
   deploy steps: 11, 14, 17 and 20.
2. **Session B.** Step 2 says to keep session B idle "until step 8", but B's next
   paste is B112 at step 12.
3. **The gate count.** Step 16's PR body says "166 code gates after chain-12", while
   A106's script makes the count 167 after b99 (step 22c). The count after chain-12
   is the stitch tool's to print at the merge.

## Gates

| Gate | Tally |
|---|---|
| check_library (checks every link under `docs/`, the runbooks included) | 27 papers, 0 failures, 0 warnings (after one fix: the index line quoted here was a relative link, now quoted as code) |
| check_registry | OK |
