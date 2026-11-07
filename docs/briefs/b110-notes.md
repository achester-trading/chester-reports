# B110 notes: Foundations' Appendix C split (D48)

Paste B110 (`docs/pastes/B110.md`), 2 Nov 2026. Fetched first.

## The branch, and how it was found

**The paper.** The library guide calls Paper I "Foundations". Its file is
`docs/whitepapers/disruptive-themes-whitepaper.md`.

**The notes the paste names.** `docs/briefs/b88-notes.md` does not exist on
`origin/b88-library-rehearsal`; the branch carries `docs/briefs/b88-library-notes.md`,
which records no body conflict ("No conflict touched a paper's body"): B88 rehearsed
the library branches on main, which does not carry A68. The conflict is named in the
merge-week rehearsals instead: A99's N2 (`docs/briefs/a99-merge-week-script.md` on
`origin/a99-merge-week-rehearsal`) and A105's N2, unchanged
(`docs/briefs/a105-merge-week-script.md` on `origin/a105-merge-week-rehearsal-2`).

**Both sides of the conflict.**

| Side | Branch, tip | Its "Appendix B" in Foundations |
|---|---|---|
| The library's | `library-phase-3a` (`de217862`), rehearsed on `b88-library-rehearsal` (`4c734105`) | "Appendix B — Dated: the dispatches, the 2028 and 2036 horizons, and Factor IV's debt-cycle 101 (as of 29 August 2026)" |
| A68's | `a68-dated-appendix` (`f6abeca3`, commit `28e2160a`), carried by chain-8, `b86-chain-8-assembly` (`4e6814df`) | "Appendix B — Dated: Records from the signal-triage orders (as of 24 October 2026)" |

**The branch used: `b86-chain-8-assembly` at `4e6814df`.** It is "chain-8's line"
the ruling names. It is the base of both merge-week rehearsals (A99 and A105) and
step 1 of the merge order. The library PRs merge onto main after it, so this is
the copy of A68's text that the library PRs will meet. `a68-dated-appendix`
itself merges only through chain-8, and was not touched.

The paper on this branch has one "Appendix B" heading, so the rename was not
ambiguous.

## Part 1: the split

**The heading.**
- Before: `## Appendix B — Dated: Records from the signal-triage orders (as of 24 October 2026)`
- After: `## Appendix C — Dated: Records from the signal-triage orders (as of 24 October 2026)`

A68's appendix has no numbered sub-headings and no table labels: its three `###`
headings are dated titles, so nothing else in it was renumbered. No other line of
the paper names Appendix B.

**The files and lines changed: 6 lines in 4 files, plus the rebuilt edition.**

| File | Line | Change |
|---|---|---|
| `docs/whitepapers/disruptive-themes-whitepaper.md` | 742 | the heading, B to C |
| `docs/dated-appendix-queue.md` | 19 | "Disruptive Themes, Appendix B" to C (Batch 5 item 23's two notes) |
| `docs/dated-appendix-queue.md` | 25 | "Disruptive Themes, Appendix B, marked unverified" to C (Batch 15 item 76) |
| `docs/dated-appendix-queue/_preface.md` | 18 | as line 19 above |
| `docs/dated-appendix-queue/_preface.md` | 24 | as line 25 above |
| `tools/validate_batch15_1.py` | 475 | the docstring of `appendix_records()`, B to C. The gate finds the records by their `###` heading, not the letter, so no check changes |
| `docs/html/disruptive-themes-whitepaper.html` | (2 lines) | rebuilt by `tools/build_paper_html.py` |

**References left as they are.**
- `docs/briefs/a68-dated-appendix-notes.md`, lines 13, 31 and 70. They are A68's
  dated account of what it did on 24 Oct, and line 70 concerns Positioning and
  Flows' Appendix B, which is not part of this split.
- Positioning and Flows' and The Rate and Liquidity Machine's own "Appendix B".
  These are other papers' appendices, and nothing else claims their letter.

## Part 2: the proof (git merge-file, scratch copies only)

The three versions are:
- **base:** the merge base of this branch and `b88-library-rehearsal`, `422ea697`;
- **library:** `origin/b88-library-rehearsal`'s file;
- **this side:** the staged file (its LF blob).

**Before the split.** `merge-file` exited 1 with one conflict hunk. Inside that hunk
were the two different "Appendix B" headings.

**After the split, the result is still not clean.** `merge-file` exits 1, with one
conflict hunk; the letter alone cannot make it clean:
- Both sides append their appendix at the same point, after the base's last line
  (the end of Appendix A).
- git reports two insertions at one point as a conflict, whatever their headings say.
- Making it clean would mean moving A68's text, which the ruling does not allow.

**What the split does settle.** The hunk is now mechanical, and this was checked
byte for byte:
- Its one side is A68's Appendix C, whole (42 lines). Its other side is the
  library's Appendix B, whole.
- No line of either appendix is interleaved with the other, and the headings no
  longer collide.
- Resolving it as "the library's side, then A68's" gives exactly the library's file
  with A68's Appendix C appended.

The merged file's appendix headings, in order:

1. `## Appendix A — Dated: Evidence log, Factor I and Factor V (as of 19 October 2026)`
2. `## Appendix B — Dated: the dispatches, the 2028 and 2036 horizons, and Factor IV's debt-cycle 101 (as of 29 August 2026)`
3. `## Appendix C — Dated: Records from the signal-triage orders (as of 24 October 2026)`

**For the merge-week script (N2).** The script's rule "a paper body: stop, and abort"
would still stop at this file. The proposed amendment is one line:

> For `docs/whitepapers/disruptive-themes-whitepaper.md`'s one end-of-file hunk,
> keep both sides: the library's Appendix B first, then A68's Appendix C.

At the PR, main (with chain-8) is "ours" and the library branch is "theirs", so the
order is theirs, then ours. Any other hunk in a paper's body still aborts.

## Gates (one at a time)

| Gate | Tally |
|---|---|
| check_library | 27 papers, 0 failures, 0 warnings (dated-appendix check 14 included) |
| check_registry | OK |
| validate_batch15_1 (its docstring was edited) | 70/1 on the laptop. The one failure is "the Batch 15 order is on file at its SHA-256": the laptop's CRLF checkout of a file this paste did not touch. The committed blob hashes to the gate's `d5318a6d…`, so CI reads it clean. It is the class `b85-gitattributes-lf` fixes |
