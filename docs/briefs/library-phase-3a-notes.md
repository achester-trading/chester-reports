# Library Phase 3a: Foundations split, The Twenty-Five contracted (B71, session B, 25 Oct 2026)

*On branch `library-phase-3a` from `origin/main` (`4180398`), in a library worktree. These are the two Phase 3 restructures Audit 2 ruled on 7 Sep 2026:*
- *"split I into timeless body + dated appendix";*
- *"contract II", whose 25 seven-element treatments move to a companion appendix maintained with the Monthly's Part 16.*

*Text is moved, not rewritten. Every moved section keeps its number and its date. Nothing is deleted. This branch merges only by its own pull request, after the operator reads it.*

## Commits

| Commit | What |
|---|---|
| `8faffdd` | Foundations: the body, Appendix B, v1.1, its HTML edition rebuilt, guide row I and its one-page entry |
| `71a9d0b` | The Twenty-Five: the body, the companion appendix, v1.1, its HTML edition rebuilt, guide row II and its one-page entry |
| this commit | these notes |

**Words, whitespace-split as the library gate counts them:**
- **Foundations (I):** 21,863 before and 22,140 after. The timeless body is 16,023. Appendix A, unchanged, is 184; Appendix B, new, is 5,933. **Moved: 5,720 words in 16 sections.**
- **The Twenty-Five (II):** 24,865 before. The body is now 8,036, and the companion appendix 17,223. **Moved: 17,053 words in 25 sections.**

A line-by-line check against `HEAD` found every original non-blank line in the new files. The only lines that differ are the three version lines.

## Every section moved

**Foundations: from the body to Appendix B** (each section's heading one level down, so the dated appendix holds it):

| Section | Words |
|---|---|
| 1.3 The present moment — a dispatch | 377 |
| 1.4 The two-to-three-year horizon (through year-end 2028) | 379 |
| 1.5 The ten-year horizon (2036) — scenario families | 344 |
| 2.3 The present moment — a dispatch | 264 |
| 2.4 The two-to-three-year horizon (through year-end 2028) | 268 |
| 2.5 The ten-year horizon (2036) — scenario families | 239 |
| 3.3 The present moment — a dispatch | 289 |
| 3.4 The two-to-three-year horizon (through year-end 2028) | 511 |
| 3.6 The ten-year horizon (2036) — scenario families | 457 |
| 4.1 The 101 — how the dynamic works (Factor IV's debt-cycle 101; its heading stays in the body with the pointer) | 743 |
| 4.3 The present moment — a dispatch | 383 |
| 4.4 The two-to-three-year horizon (through year-end 2028) | 361 |
| 4.5 The ten-year horizon (2036) — scenario families | 295 |
| 5.3 The present moment — a dispatch | 234 |
| 5.4 The two-to-three-year horizon (through year-end 2028) | 293 |
| 5.5 The ten-year horizon (2036) — scenario families | 283 |

Chapter 3's 3.5, "The wider board — theaters over the decade", stays in the body: it is the decade's structure, not a dispatch or a dated horizon.

**The Twenty-Five: from the body to `docs/whitepapers/companions/tail-scenarios-companion-appendix.md`**, in the families' order, each with all seven elements:

| Family | Scenarios (words) |
|---|---|
| A | 1 (1,416), 19 (798), 9 (672), 2 (596), 11 (485) |
| B | 6 (765), 14 (608), 5 (312) |
| C | 3 (1,130), 20 (612) |
| D | 7 (822), 8 (954), 12 (418), 17 (540) |
| E | 16 (942), 10 (645), 15 (312) |
| F | 4 (848), 18 (515), 13 (745) |
| G | 24 (710), 22 (660), 23 (540), 21 (449), 25 (559) |

**What the body keeps:**
- Part 0;
- the seven family headings and their introductions;
- Part 2, the operations: the routing matrix, the clustering map, the coverage audit and the re-specification log;
- Part 3, the mutation scan.

## The joining sentences (the only new prose)

1. **Foundations 4.1, under its kept heading:** "The debt-cycle mechanism this factor reads is taught in Debt Cycles, Regimes, and Environments, in its chapters "The short debt cycle", "The long debt cycle" and "Financial repression, fiscal dominance, yield-curve control and capital controls"; this paper's original 101 is kept, unchanged, in Appendix B." The three chapter titles are XXVII's, read from `origin/library-xxvii` (Chapters 1, 2 and 3 of Part I); they are cited by name, not number.
2. **Foundations, once in each of Chapters 1 to 5, where the moved sections stood:** "*This factor's dated dispatch and its 2028 and 2036 horizons are in Appendix B (as of 29 August 2026), moved there unchanged under Audit 2.*"
3. **Appendix B's heading:** "Appendix B — Dated: the dispatches, the 2028 and 2036 horizons, and Factor IV's debt-cycle 101 (as of 29 August 2026)". Its one-line preface: "*Moved here from the body on 25 October 2026 under Audit 2's Phase 3, the split of this paper into a timeless body and a dated appendix; the text is unchanged, and each section keeps its number and the date it was written (29 August 2026). The report refreshes these sections; the body does not carry them.*"
4. **The Twenty-Five, once in each family, where its first scenario stood** (seven sentences): "*This family's scenarios (…), each on the seven-element template, are in the companion appendix (a link to `docs/whitepapers/companions/tail-scenarios-companion-appendix.md`), maintained with the Monthly's Part 16 and moved there unchanged under Audit 2.*"
5. **The companion appendix's masthead line:** "**Companion appendix to The Twenty-Five … · maintained with the Monthly's Part 16 · moved from the paper's body on 25 October 2026 under Audit 2's Phase 3 (first edition 29 August 2026)**". Its one-paragraph preface says what is in it, and that its current states are as of the first edition and refreshed with the Monthly's Part 16.
6. **The version lines:**
   - Foundations' masthead and footer: "Version 1.1 · 25 October 2026 · restructured per Audit 2 (first edition 29 August 2026)";
   - The Twenty-Five's masthead: the same.
   - The guide's at-a-glance rows and one-page entries carry v1.1, the new word counts and "restructured per Audit 2".

## Departures

- **The companion appendix's path.** The paste names `docs/whitepapers/tail-scenarios-companion-appendix.md`. The library gate counts every `.md` in that folder as a roster paper, and failed it twice: there is no guide row, and the name is not `<slug>-whitepaper.md`. The paste is docs only, so the gate was not changed. The file sits at `docs/whitepapers/companions/tail-scenarios-companion-appendix.md`, which the gate does not scan (needs-you 1).
- **Section numbers are not renumbered.** Foundations' chapters now run 1.1, 1.2, 1.6, 1.7 (and similarly in each chapter). Renumbering would be a rewrite and would break the in-paper references (the moved 3.4 cites §3.5). The gate checks only `## N.` section numbers, not dotted ones, so it passes (needs-you 3).

## Validation

- **`check_library`:** 27 papers, 0 failures, 0 warnings, after both commits. The dated-appendix rule holds Appendix B to its as-of heading (29 August 2026), with no entry heading dated later, and both HTML editions were rebuilt from their new `.md` (check 10's source stamp).
- **The readability gate** (`tools/validate_readability.py`) does not read the papers, so it does not apply.
- **CI:** read once after the push; recorded below.

## Needs you (five)

1. **The companion appendix's home.** Keep `docs/whitepapers/companions/`, or have a later code paste teach the library gate a companion file in `docs/whitepapers/` (an exclusion by name)?
2. **The merge order with XXVII.** Foundations' 4.1 now points to Debt Cycles' chapters, but XXVII is still on `library-xxvii`. Merge XXVII first, or both together, so the pointer never names a paper the roster lacks.
3. **The section numbering gaps** (1.1, 1.2, 1.6, 1.7 …). Leave them until the paper's next edition, or renumber now with the cross-references?
4. **Two dated passages that the ruling did not name stay in the bodies:** Foundations' 8.2, "The named pathways, with current state", and the Twenty-Five's Part 2 build queue and re-specification log. Move them in a Phase 3b, or keep them as the operations the body owns?
5. **The guide's header word total** ("roughly 426,000") is unchanged. The roster count falls by about 17,000 with the companion outside the roster, so the measured total moves further from the printed one. The proposal in B66's brief (a `--write-total` mode for check 11) would settle it at the next merge.

**CI.** Read once after the push of `bfc88f1`: no run was listed yet, so there is no run id. That push carried a library-gate failure in these notes (a quoted relative link), fixed in the next commit; the next paste that touches this branch reads its CI once.
