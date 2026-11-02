# B117 notes: the twelve library decisions of D48, by status

Paste B117 (`docs/pastes/B117.md`), 2 Nov 2026. D48 (31 Oct) accepted B93's memo,
`docs/briefs/library-review-decisions-2026-10-30.md`, whole.

The memo's summary table gains one column, "Status (B117, 2 Nov 2026)". Nothing
else in it changed: 15 lines (the header, the separator, the 13 rows), each with
only the column appended.

**The classes:**
- **(i)** a docs edit, built now;
- **(ii)** a build or a box step;
- **(iii)** done, superseded, or nothing to build;
- **(iv)** needs the operator or Doctrine #2.

## The twelve

| # | Paper | What it asks | Class | Branch | Commit, or the next step |
|---|---|---|---|---|---|
| 1 | XXVII | Keep the length (24,647) | (iii) | — | Ruled by D30(4); cuts are marked on review |
| 2 | XXVII | No rewording of 17.4's proposed rule | (iii) | — | Ruled by D30(2); it stays a proposal, for Doctrine #3 |
| 3 | XXVII | Cite the missing 13 Sep order by name, as its record; merge after chain-8 | **(i)** | `library-xxvii` | **`26302feb`**: B.7 in XXVII's dated Appendix B, citing "Post-Freeze Amendment #3 (13 Sep 2026; its record, original not committed)" by name. Not as a link: the record file reaches main with chain-8 and is not on this branch. The order (chain-8 first) holds in B116's script |
| 4 | Phase 3a | One reader's-note sentence on Foundations' numbering gaps | **(iv)** | `library-phase-3a` | The reader's note is body text, and B117's rule allows no body edit. Next step: the operator's go to add, at phase 3a's PR, "Moved sections keep their numbers and are in Appendix B." |
| 5 | Phase 3a | Keep `docs/whitepapers/companions/` | (iii) | — | No change; the gate passes today |
| 6 | Phase 3a | Keep the two dated passages in the bodies | (iii) | — | No change now; a Phase 3b at the papers' next edition |
| 7 | XXXI | The ten triggers' roll-up tiers | **(iv)** | `library-xxxi` | Ruled at Doctrine #2 (7–8 Nov). Next step: a writing paste records the ruled rule on the branch before its PR |
| 8 | XXXI | State the gap-patch's input gap | (iii) | — | No change: the notes state the gap, the manual stays as written, and the build declares the inputs |
| 9 | XXXII | The spread calendar; XXIX in March, XXX in July | **(i)** | `library-xxxii` | **`197883df`**: the structural-review register's rows XXIX (`review_month: 3`) and XXX (`review_month: 7`), version "1.0 Draft 1" of 26 Oct 2026, from their mastheads |
| 10 | E&I | Accept the five drawn figures | (iii) | — | Accepted as drawn; no change |
| 11 | XXX | The four store figures from a box export | **(ii)** | `library-xxx` | The operator runs the read-only export on the box, Tue 3 Nov after 17:20 ET (the memo's section 11; quoted in `docs/briefs/b116-library-script.md`). Then a drawing paste on `library-xxx` before its PR |
| 12 | XXIX | Clear the eight marks | (iii) | `library-xxix` | Done by B94, `c148862b` |

B110's Appendix C (Foundations' second "Appendix B") is not one of the memo's
twelve. It was built by B110 on chain-8 (`faac8c48`), and B116 rehearsed it.

## The branches touched

**Detached HEADs, pushed fast-forward.** `library-xxvii` and `library-xxxii` are each
checked out in an idle worktree (`chester-lib27`, `chester-b78-xxxii`): both clean,
at origin's tip and last touched in October. So each decision was built on a
detached HEAD at the origin tip and pushed fast-forward to the branch. The two
worktrees' files were not touched; their local branches now trail origin by one
commit.

| Branch | Base | Commit | check_library | check_registry |
|---|---|---|---|---|
| `library-xxvii` | `360c13c4` | `26302feb` (decision 3) | 28 papers, 0 F, 1 W: "guide claims 426,000 words, measured 468,134", the branch's standing warning (B88 saw it) | OK |
| `library-xxxii` | `1d412b95` | `197883df` (decision 9) | 28 papers, 0 F, 3 W, all check 15: "the structural-review register rows XXIX, which the roster does not have" and the same for XXX, both clearing once XXIX and XXX merge after XXXII (B116's order); and the standing "25 older papers have no Assumptions and Falsifiers appendix" | OK |
| `b88-library-rehearsal` | `4c734105` | the paste `9e9a99b5`; the memo's column and these notes | — (no paper changed) | — |

Neither paper has a gate of its own.

**On the warnings at the real PRs.** Between XXXII's PR and XXIX's, main will show
check 15's two "rows … which the roster does not have" warnings. They are
warnings, not failures, and they clear at XXIX's and XXX's PRs.
