# A103 notes: the seven places the Weekly of w/e 30 Oct 2026 contradicted itself

**Branch.** `a103-weekly-consistency`, from `origin/a95-monthly-first-edition`
at `a2737d15` (A95's tip, on A97's line). It merges with the rest, for the
Weekly of 8 Nov if the merge week allows, else 15 Nov.

**A95's CI, recorded here** because this branch is the next on its line: run
41380917709 (A95's steps 3-4) failed on five gates. All five are the same on the
unchanged base locally:

- `validate_audit_fixes`: B84's expectation, fixed on A90's branch;
- `validate_monthly`: the refunding window, which depends on the date;
- `validate_voices`: 72/1 on both;
- `validate_alpha_proposer`: 41/1 on both;
- `validate_st_t5_render`: passes locally on both and fails in CI.

The last three are date drift, which B101 pins. A95's notes push is CI queued,
run 41383386271.

**Findings, fixes and checks.** `docs/briefs/letter-findings.md` (the W rows)
carries the table. Every case is in `validate_weekly_readability` group D, over
`tests/fixtures/weekly_consistency_2026-10-30.json`.

**How the findings were reproduced.** Synthetic fragments in the edition's own
shapes. The edition and its payload are on the box, and the laptop's store copy
ends 30 Sep 2026, before the week. Each case rebuilds the two prints the finding
names.

| Row | The two prints | Which was right | The fix, in a word |
|---|---|---|---|
| W1 | The précis's sign word; the tape's Week column | The tape | The précis's block carries the tape's signed week; its audit holds the week's sign word to it |
| W2 | The précis's gamma story; the session table | The table's five-session summary | The précis's block carries that summary, and the week-end reading apart under its own name |
| W3 | Plumbing's term-premium change; the attribution table's | Plumbing's (since the last edition) | The attribution reads the same `change_over` |
| W4 | The gap table's "Direction"; the week's prints | The week, of the printed z | `period_direction`, one rule for both editions |
| W5 | The narratives commentary's counts; the stories table | The table (by event cluster) | The table's count in the data block, the register's under its own name; a pair the table does not print is withheld |
| W6 | The FOMC decision; nowhere | The calendar (tier 1) | `tier1_headlines` gains the FOMC statement: the target range's two limits; the dissents a listed gap |
| W7 | "What would change our mind"; the calendar | The calendar | The précis's block carries the calendar; a CHANGE date against it is withheld |

**W6, which writer and why.** The Weekly records a policy decision through its
tier-1 release rows (`weekly_stack.tier1_releases`, which feed The read's
week-by-day table and Plumbing). Those print only a release named in
`config/release_calendar.yaml` `tier1_headlines`. The FOMC statement is tier 1
in the calendar's own rows but had no headline entry, so the miss was the
writer's configuration, not the events feed and not the window. The rows now
de-duplicate by series and form, so "FOMC Meeting" and "FOMC statement" in one
week print the decision once.

**The commits.** One per finding, except W1, W2 and W7, which share one: their
change is one data block and one audit in `daily_cascade/precis.py`, and a hunk
cannot be split by finding.

| Commit | What |
|---|---|
| the paste | `docs/pastes/A103.md` |
| `2d291083` | W1, W2, W7 |
| W3 | the attribution's change (`batch5_block`; `validate_st_r4_t1`'s wiring string now allows the added argument) |
| W4 | `period_direction` |
| W5 | the narratives' counts |
| W6 | the FOMC headline |
| the last | the fixture, gate group D, the W rows and these notes |

**For the merge sheet.** This branch touches
`daily_cascade/weekly_stack.py` (`misfit_week`, `tier1_releases`,
`plumbing_week`'s batch-5 call, the narratives' data), `daily_cascade/precis.py`,
`daily_cascade/stack_prose.py` (the Weekly's `checks`),
`daily_cascade/batch5_block.py`, `daily_cascade/weekly_sections.py`
(`gap_table`), `monthly_macro/stack.py` (`month_direction`) and
`config/release_calendar.yaml`. All of these are on A97's line already, and A90
touches none.

## The gates

Run one at a time. `validate_weekly_stack` and `validate_monthly_stack` outrun
the foreground limit; each ran whole, alone, in the background.

| Gate | Result |
|---|---|
| `validate_weekly_readability` | 64/0 (group D added: W1-W7) |
| `validate_weekly` | 101/0, 1 skipped |
| `validate_weekly_calendar` | 44/0 |
| `validate_numeral_audit` | 181/0 |
| `validate_weekly_edits` | 91/0 |
| `validate_st_r4_t1` | 49/0 (after the wiring string) |
| `validate_monthly_frames` | 48/0 |
| `validate_audit_fixes` | 135/1: B84's expectation, the same on the base |
| `validate_monthly` | 370 passed, 1 failed, 1 skipped: the refunding window, the same on the base |
| `validate_readability` | 67/0 |
| `validate_weekly_opener` | 46/0 |
| `validate_weekly_fixes_8` | 67/0 |
| `validate_weekly_storyline` | 31/0 |
| `validate_weekly_stack` | 83/0, whole |
| `validate_monthly_stack` | 267/0, whole |

No gate was added.
