# B131: XXXV The Operator, Draft 1 (6 Nov 2026)

Paste B131 (`docs/pastes/B131.md`). The library programme's L-6, ruled as R-1
(D59, 6 Nov 2026). The order is `docs/change-order-library-programme-2026-11-06.md`
on `origin/b129-five-filings`.

**The base.** `origin/main` at `ee04ba21` (the merge of b114-names-sweep).
`library-xxxv` is a new branch from that base.

**The commits, in order.**
1. The paste, verbatim, with the name stripped (D38).
2. The brief, verbatim, as `docs/briefs/xxxv-behavioral-brief-2026-11-06.md`,
   before any paper text.
3. One commit per Part:
   - the masthead, the front matter and Part I;
   - Part II;
   - Part III;
   - Part IV;
   - Part V with the two appendices.
4. The roster, registry and Guide wiring, with these notes.

**The paper.** `docs/whitepapers/operator-whitepaper.md`. The slug is the title
less its article, as the Doctrine's and the Dealer's Hand's are. Its HTML edition is
`docs/html/operator-whitepaper.html`.

## Word count by Part

Whitespace-split, the method `check_library` uses.

| Part | Words |
|---|---|
| Masthead, reader's note, prerequisites | 705 |
| I The gap between the read and the trade (Chapters 1–6) | 3,198 |
| II The canon (Chapters 7–12) | 3,499 |
| III The system's answer (Chapters 13–15) | 2,449 |
| IV Routed items (Chapters 16–17) | 1,531 |
| V Tactical Applications, Wiring, Environments (Chapters 18–20) | 2,138 |
| Appendix A, Assumptions and Falsifiers | 716 |
| Appendix B, dated (as of 6 November 2026) | 642 |
| **Total** | **14,892** (`wc -w` 14,811) |

## Wiring

- **The library guide.** XXXV's at-a-glance row (layer "Craft", Draft 1,
  ~14,900 words) and its line in the reading-order list. The guide's "Deliberately
  deferred" paragraph, which still describes the behavioral paper as deferred, was
  left as it is: the paste allows one roster line, and L-4 rewrites that section.
- **`tools/check_library.py`.** `REGISTRY` gains `"XXXV": "operator"`.
- **The Master Guide.** Table 9 gains XXXV's row. `tools/figures/master_guide.py`
  puts XXXV in the "How to decide and judge evidence" group for books ABCD, and
  Fig 5 and the Guide's HTML were regenerated. The paste did not name these files,
  but `check_master_guide` fails on a roster paper with no group ("papers in the
  roster with no group: ['XXXV']"), and CI runs it.

## The gates

| Gate | Result |
|---|---|
| `check_library` | 28 papers, 0 failures, 0 warnings |
| `check_master_guide` | PASSED; 1 warning: the Guide's as-of (29 Oct) is older than the newest change order, a stitch's refresh |
| `check_registry` | OK |
| `validate_gates` | PASSED |
| `validate_names`, with the list set in the environment only | 0 hits, 21/0 |

## Where the brief was under-specified, and what was chosen

1. **The roster line.** The paste says "commissioned" becomes "Draft 1" on the
   Craft shelf. Main's guide has no XXXV line and no Craft shelf: both are L-4's,
   which has not merged. A new row was added with "Craft" in the guide's Layer
   column, placed after the Positioning & the book rows and before System, and the
   same in the reading-order list. When L-4 merges, its "commissioned" line and
   this row will meet in a conflict that keeps this row.
2. **The DTH-1 rules.** The day-trading order filed 6 Nov 2026 as Addendum A to
   Amendment #5 is not in the repository (D41 keeps the manual ledger, the brief
   and the playbook off the public repo). The paper describes the five rules only
   as the brief lists them. It reads the "1% and 2% limits" as a day's and a
   week's loss limits, the shape the Card gives Book C, and says that the order's
   own text governs. It defines the view line in its own words: a dated one-line
   directional call with a horizon, written before the session and graded
   whether or not a trade follows. That is labelled "this paper's reading of the
   order".
3. **Appendix B's figures.** The register lives on the box, and this session
   reads no box and no private folder. Appendix B therefore cites only what the
   repository records: the Doctrine #2 pack's "no cell has 10 graded decisions"
   and the scoreboard's "accruing". The DTH-1 aggregates are named as not read,
   to enter at the operator's read or at Draft 2. The week of 26 Oct is a
   sketch of what was ruled and built that week, with no market or trade content.

**Two smaller choices.**
- **Tactical Applications.** The house standard's chapter carries seven horizons
  with nine fields each. The brief asks for "the day trader, the swing trader and
  the allocator"; the chapter follows the brief, adds Book D's opportunist, and
  gives each a before, an after and a danger sign.
- **The Market Wizards Alpha Framework.** It is not a paper in the library. It
  is cited through the Operating Doctrine's Part III and its Rules 6, 7, 10 and 14.

## The literature citations

Part II's findings are cited from the published studies as the drafting session
knew them. No source was re-read in this session. Each closing clause says
"cited 6 November 2026", not "verified", and Appendix A lists every study for
re-verification at the operator's read.

## Names and figures

- **Names.** No person from the operator's life is named. Author names from the
  literature stay as citations. The X account of item 132 is "account T", as the
  Batch 25 order names it.
- **Figures.** No dollar figure and no account figure appear in the paper, which
  was checked by a scan for currency signs.
- **Personal details.** The Doctrine's personal details (the operator's employment,
  capital and target) are not repeated.

## CI

Read once after the push.
