# B118 notes: the Doctrine #2 pack's evidence refreshed and proof-read

Paste B118 (`docs/pastes/B118.md`), 2 Nov 2026. Branch `b96-doctrine-2-pack-refresh`,
continued from `origin/b96-doctrine-2-pack-refresh` at `c23c6413` (B104 and B105's
D2-90). Options only: no recommendation became a ruling, and no Doctrine or config
file was edited.

## Part 1: Part 10's addendum of 2 Nov

The addendum is a table at the end of Part 10. Each row is cited to its file, the
branch it is on and the branch's tip; every figure is printed as its source prints
it, and none comes from a Letter.

| Item | Source |
|---|---|
| The first stacked Monthly: 88 calls; 45 of 61 published (33 of 48 body sections, 12 of 13 summary paragraphs); 6,916 words; A97's replay, 5 of the 16 withheld would have published | `docs/briefs/a95-notes.md`, `a95-monthly-first-edition` at `a2737d15` |
| A103's seven Weekly findings, W1–W7 | `docs/briefs/a103-notes.md`, `a103-weekly-consistency` at `b3a1b9f5` |
| B106: 23 gates (4 already pinned, 1 pinned by B106, 18 reading today on purpose); 42 files of code under test; the sixth failure, `validate_alpha_proposer` (run 41379176410) | `docs/briefs/b106-notes.md`, `b101-date-drift-gates` at `666611e1` |
| B107: 134.5 job-minutes, 41.5 minutes of wall time, parallelism 3.8; the install step 53.2 job-minutes (40%); queues of 14.1, 55.7 and 13.6 minutes | `docs/briefs/b107-ci-time-audit.md`, `b100-hygiene` at `72406edd` |
| B108 and B115: 17 rows by batch; placeable on 23 Nov; the five disagreements as B115 settled them | `docs/briefs/audit-5-placement-pack.md`, `b108-notes.md`, `b95-batch-21-filing` at `c72f4f38` |
| B109 and B111: 414 hits in 170 files, then 33 in 20, then 8 in 8 (3 allowlisted) | `docs/briefs/b109-notes.md`, `b109-names-gate` at `46da3bb5` |
| A105 and A106: A105's run green (41393587121); the count 167; the laptop green; A106's run 41522379720 queued at its read, and at B118's read listed by GitHub as cancelled (superseded) | `docs/briefs/a105-merge-week-script.md`, `a105-merge-week-rehearsal-2` at `b8023fba` |
| A110's sweep | **pending:** no A110 branch was pushed |

**Two differences from the paste's wording:**
- The source does not print "CI green on the rehearsed tree" for A106's run. A105's
  run is the green one. A106's run was queued at its one read, and GitHub now lists
  it as cancelled. The addendum says exactly that.
- No ledger edition has been written on any branch since 31 Oct, so Part 10's
  ledger tables are unchanged and the addendum says so.

## Part 2: Part 12 checked (D2-84 to D2-90)

**Every source cell was checked** with `git cat-file -e` on the branch it names:
- on `b102-readable-editions-register`: the order
  `docs/change-order-readable-editions-2026-11-01.md`,
  `docs/master-guide/chat-tasks.yaml`, `docs/briefs/letter-findings.md`, the Master
  Guide and the Reporting System paper;
- `docs/pastes/A95.md` on `a95-monthly-first-edition`, and A95's commit `ba1d289b`
  on that branch;
- `docs/briefs/a92-notes.md` on `a92-dth1-box-pieces`;
- `docs/briefs/b91-notes.md` on `b91-batch-19-filing`;
- `altdata/move_screen.py`'s `contagion_states` on main.

**Two cells needed a fix (mechanical, made):**
- **D2-89's source** said A95's notes were "not yet pushed". They are:
  `docs/briefs/a95-notes.md` on `a95-monthly-first-edition` at `a2737d15`.
- **D2-85's ledger** `x-attention-ledger-eqmacro.csv` is not a committed file. It is
  a Drive ledger, named in the register's `writes` line on b102, and the pointer now
  says so.

**Every option is still open.**
- No ruling since 1 Nov touches D2-84 to D2-90; the 2 Nov rulings were CI and the
  names gate.
- No `a112-em-shock-screen-amendment` branch has been pushed, so D2-90 is unbuilt.
- D2-84's "the rulings record under `docs/briefs/` does not yet carry them" still
  holds: no rulings file on main, b95, b102 or chain-8 names D50–D56.

**Part 11's line still holds:** "D2-85 before any X-layer build; D2-86 before Audit
#5's agenda". No X-layer build has been pushed, and Audit #5's agenda is not set.

## Part 3: the proof-read

| Check | Result |
|---|---|
| Each D2-n in the decision list | D2-1 to D2-90, each defined once. The five apparent repeats (D2-22, 29, 33, 45, 68) are Part 9's amend notes ("read with …"), not second definitions |
| Cross-references | Parts 1–12 and Annexes A and B all resolve; Part 8 is the decision list's own section. Tables 1.1 to 7.1 all exist. "Part 16" is a quote of the Doctrine's text (T8-8) |
| SHAs | 8 cited; each is on the branch it names, and seven are that branch's tip. `ba1d289b` is a named commit on A95's branch |
| Tables | 34 tables, every row's cells equal to its header's. D2-90's row carries escaped pipes (`\|z1\|`), which GitHub's Markdown renders as text |
| Reading time | The block now matches; see below |

**The new word totals** (230 words a minute):

| Span | Words | Minutes |
|---|---|---|
| The whole pack, by `wc -w` | **21,969** (was 21,270) | about 96 |
| The decision list | 4,903 (was 4,898; the D2-89 fix) | about 21 |
| Parts 1–12 | 8,564 (was 7,899) | about 37 |
| B118's addition | 699 | about 3 |

**For the operator (not changed: not mechanical):**
1. **25 decisions have no mention by number outside the decision list:** D2-2, 3,
   12–15, 19, 24, 37, 42–44, 46, 48, 51–57, 59–61 and 71. Their evidence is in
   Parts 1–8 by subject, and in Annex A by the 20 Oct pack's item codes (T8-n, V-n,
   W-n). That is the pack's design, not a fault. A cross-reference column would be a
   new edition, not a fix.
2. **The operator's first name appears on three lines** (22, 65 and 547), each
   inside a quoted ruling. The names gate (B109) will flag them when this branch
   reaches the docs tranche's sweep. A quote was not edited here.

## Gates

| Gate | Tally |
|---|---|
| check_library (the pack is linked from the index's paths) | 27 papers, 0 failures, 0 warnings |
| check_registry | OK |
| The word count | `wc -w` 21,969, as the block prints |
