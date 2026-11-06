# B130: the five library branches refreshed to main (6 Nov 2026)

Paste B130 (`docs/pastes/B130.md`). The script was `docs/briefs/b116-library-script.md`
on `origin/b116-library-rehearsal-2`, which was read only.

**The base.** `origin/main` was at `ee04ba21`, the merge of `b114-names-sweep`
(PR #52). Each branch was merged at its own origin tip. Three branch tips had
moved on since the rehearsal took them, through B117 and B119:
- library-xxvii: `360c13c4` became `26302feb`;
- library-phase-3a: `de217862` became `fc336a4e`;
- library-xxxii: `1d412b95` became `197883df`.

**How.** Each of the five branches is checked out in another worktree, and those
local branches stand at the older tips. So each merge was made in this worktree on
a detached HEAD at the branch's origin tip, and pushed to the branch with
`git push origin HEAD:refs/heads/<branch>`. No other worktree was written. Each
branch carries one merge commit. library-xxvii also carries the paste before its
merge and these notes after it.

**Generated files.** Each was taken from the branch's side, then regenerated from
the merged sources:
- `tools/figures/master_guide.py` (Fig 2 and Fig 5);
- `tools/build_paper_html.py` for the Guide and the paper concerned.

`appendix_queue_index.py --check` reported "matches its 7 entry files", and
`master_guide.py --check` was clean after every merge.

## Per branch

| Branch | Base (old tip) | Merge commit | Conflicts and resolution | check_library (papers / failures / warnings) | check_master_guide | validate_gates | validate_names (list set) | CI run |
|---|---|---|---|---|---|---|---|---|
| library-xxvii | `26302feb` | `77d1b6ed` | `docs/html/master-guide.html` only (generated): regenerated, as step 1 | 28 / 0 / 1: "guide claims 451,000 words, measured 477,888" | PASSED | PASSED | 0 hits, 21/0 | 42272641203 (in progress at the read) |
| library-phase-3a | `fc336a4e` | `c3e5bc3a` | Foundations' end of file, as step 2: the library's Appendix B, then A68's Appendix C. The headings read A, B, C at lines 558, 573 and 760, as in the rehearsal. The result is the branch's file byte for byte with main's Appendix C appended. Its HTML was regenerated. The guide merged without conflict. | 27 / 0 / 0 | PASSED | PASSED | 0 hits, 21/0 | 42272860911 (queued) |
| library-xxxii | `197883df` | `9a9f0036` | `docs/master-guide.md` System table and the library guide's System rows, as step 4: main's XXXIII row (Draft 4), then XXXII's row. `check_library.py` and `master_guide.py` merged without conflict. The Guide's HTML was regenerated, and Fig 5 regenerates to the branch's own. | 28 / 0 / 3, all check 15: register rows XXIX and XXX not in this branch's roster; the 25 older papers' appendix | PASSED | PASSED | 0 hits, 21/0 | 42273057873 (queued) |
| library-ei-figures | `6e6aa1cd` | `f5b6f536` | The library guide, by line, as step 5: this branch's XXIII row ("5 computed figures"; main's equalled the base), then main's XXXIII row (Draft 4; this branch's equalled the base). Fig 5 and the Guide's HTML were regenerated. | 27 / 0 / 0 | PASSED | PASSED | 0 hits, 21/0 | 42273360079 (in progress) |
| library-xxix | `c148862b` | `14e1cd74` | `docs/html/master-guide.html` only (generated): regenerated with Fig 5, as step 6 | 28 / 0 / 0 | PASSED | PASSED | 0 hits, 21/0 | not yet listed. The read returned 41215675855, a failure on the old tip `c148862b` |

**Paper gates.** On library-phase-3a, the three gates that read Foundations:
- validate_batch15_1: 71/0;
- validate_alt_asset_scan: 50/0;
- validate_library_st_l: 17/0.

check_registry was OK on all five.

**Other notes.**
- **Unseen conflicts: none.** Every conflict was one the script records, or a
  generated file. No branch was left unmerged.
- **The operator's name.** No library branch's prose carried it: validate_names
  read 0 hits on every merge, with the name and the four `allow:` paths set in the
  environment only.
- **The word total** in the guide's header was left as it was (L-4 refreshes it).
- **Not refreshed here:** XXXI (step 3) and XXX (step 7), as the paste rules.
- **The `docs/html/white-paper-library-guide.html` edition** is not a tracked
  file. One built by mistake during the library-xxxii merge was deleted before
  that merge's commit.
