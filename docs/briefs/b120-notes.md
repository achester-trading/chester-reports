# B120 notes: the Doctrine #2 sitting's agenda and minutes template

Paste B120 (`docs/pastes/B120.md`), 2 Nov 2026. Branch `b96-doctrine-2-pack-refresh`,
continued from `fe4bc74c`. Nothing is ruled.

## The files

- `docs/briefs/doctrine-2-sitting-2026-11-agenda.md`: nine blocks over two days, built
  from the pack's Part 11 and its decision list. The October agenda's shape is kept:
  one heading per block, its items, and what is asked.
- `docs/briefs/doctrine-2-sitting-2026-11-minutes.md`: the template. It has one row
  per decision, 90 rows in the agenda's order, with these columns:
  - the number;
  - the title;
  - the pack's recommendation, quoted (Parts 9 and 12 quote their options, since they
    are options only);
  - the ruling and the operator's words, both blank;
  - what it releases, quoted from Part 11 or Part 12, or "—" where the pack names
    nothing;
  - the date.

  Each block also has an accept-all line. The closing sections hold the new rulings,
  the incidents and the next sitting's date.
- The pack: one line at the end of Part 11, pointing at the agenda. The pack's
  reading-time block now reads 8,586 words for Parts 1–12 and 21,991 in all by
  `wc -w`, which matches.

## The blocks

| Block | Day | D2 | Reading (min) | Sitting (min) |
|---|---|---|---|---|
| 0 | before | the preamble, Part 10, Part 11 | 7.6 | — |
| 1. Releases builds | Sat | D2-73 to 76, 79 to 83, 85, 86 | 9.5 | 85 |
| 2. Values and structure | Sat | D2-1 to D2-10 | 12.2 | 15 |
| 3. Standing rules | Sat | D2-11 to D2-17 | 2.8 | 5 |
| 4. Regime and calibration | Sat | D2-18 to D2-21 | 2.3 | 7 |
| 5. The register | Sat | D2-22 to D2-25 | 6.5 | 5 |
| 6. Attention budget | Sun | D2-26 to D2-28 | 1.9 | 15 |
| 7. Calendar | Sun | D2-29 to D2-31 | 2.0 | 5 |
| 8. Part 12 and D2-90 | Sun | D2-84, 87 to 90 | 9.2 | 10 |
| 9. Carried, and Part 9's records | Sun | D2-32 to D2-72, 77, 78 | 4.7 | 90 |
| **Total** | | 90 decisions, each once | **58.6** (13,489 words) | **237** |

**The two days hold it.** The sitting takes 117 minutes on Saturday and 120 on
Sunday, against 120 each. The 58.6 minutes of reading match the pack's block:
4,903 words of decision list and 8,586 of Parts 1–12, at 230 words a minute.

**Where the agenda departs from the paste's nine blocks:**
- **Part 2** (D2-5 to D2-10) is not among the nine, so it joins block 2.
- **D2-79** (the DTH-1 scope) releases the Book B scanner's candidates (Part 11), so
  it joins block 1.
- **D2-77 and D2-78**, Part 9's records, join block 9.
- **Block 9's own order:** Part 11 placed its build-holding items on Saturday (Gate
  C's list, D2-35 and D2-39). The paste orders Part 8 last, so they come first inside
  block 9, on Sunday.

## The last D-number

- `docs/briefs/rulings-2026-10-28-31.md` (on `b95-batch-21-filing`) ends at **D48**.
- The 1 Nov order (on `b102-readable-editions-register`) rules **D50 to D56** and
  names **D57** as proposed.
- **D49 is on no branch** (main, b95, b102, chain-8): a gap for the operator to
  record or explain.
- The sitting's rulings start at **D58**.

## Gates

| Gate | Tally |
|---|---|
| check_library | 27 papers, 0 failures, 0 warnings |
| check_registry | OK |
| The agenda's minutes against the pack's block | 13,489 words = 4,903 + 8,586; 58.6 minutes both ways |
