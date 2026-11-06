# B132: XXVI Turning Points, Bubbles, and Crises, Draft 1 (6 Nov 2026)

Paste B132 (`docs/pastes/B132.md`). The library programme's L-7, with R-2 and
R-8 (D59, 6 Nov 2026). The order is
`docs/change-order-library-programme-2026-11-06.md` on `origin/b129-five-filings`.

**The base.** `origin/main` at `ee04ba21`. `library-xxvi` is a new branch from it.

**The commits, in order.**
1. The paste, verbatim, with the name stripped (D38).
2. The brief, verbatim, as `docs/briefs/xxvi-turning-points-brief-2026-11-06.md`,
   before any paper text.
3. One commit per Part:
   - the masthead, the front matter and Part I;
   - Parts II to VII, one commit each;
   - Part VIII with the two appendices.
4. One commit for the move of X, the roster and registry, the Guide wiring and
   these notes.

**The paper.** `docs/whitepapers/turning-points-bubbles-and-crises-whitepaper.md`.
The slug is the title, hyphens only, keeping "and" as Price, Time, and Edge does.
Its HTML edition is `docs/html/turning-points-bubbles-and-crises-whitepaper.html`.

## Word count by Part

Whitespace-split, the method `check_library` uses.

| Part | Words |
|---|---|
| Masthead, reader's note, prerequisites | 830 |
| I What Tops and Bottoms established (Chapters 1–4) | 2,827 |
| II Bubbles as an anatomy (Chapters 5–8) | 3,270 |
| III Banking crises (Chapters 9–11) | 2,184 |
| IV Liquidity crises (Chapters 12–13) | 1,796 |
| V Emerging-market crises (Chapters 14–15) | 1,234 |
| VI International tops (Chapters 16–17) | 1,028 |
| VII Reading a turn from inside (Chapters 18–20) | 1,855 |
| VIII Tactical Applications, Wiring, Environments (Chapters 21–23) | 2,591 |
| Appendix A, Assumptions and Falsifiers | 841 |
| Appendix B, dated (as of 6 November 2026) | 938 |
| **Total** | **19,414** (`wc -w` 19,313) |

The target was about 22,000; the draft is about 12% under. The shortfall is in
Parts V and VI. They were kept to the mechanism and the routed items, because the
live case's detail is dated and belongs in Appendix B.

## X's move (R-8)

- **The study** moved with `git mv` to
  `docs/whitepapers/archive/tops-and-bottoms-2026-05.md`, unchanged.
- **The pointer** is at the old path,
  `docs/whitepapers/tops-and-bottoms-whitepaper.md`. It is a masthead only: the one
  paragraph sits in the Status line, naming XXVI and XXXI. Numerals are allowed in
  a masthead and nowhere else in a paper (check 2).
- **X stays in the registry and the guide.** `check_library` reads every `.md`
  in `docs/whitepapers/` (outside `archive/`) as a roster paper. The pointer is
  therefore registered as X, and the guide's X row is marked archived, its
  numeral retired.
- **Inbound links** to the old path (the Master Guide, the false-bottom ledger,
  `tools/calibration/sr08_false_bottoms.py`'s citation string, the audit-1 work
  order and others) resolve to the pointer, so none was edited.
- **X's HTML edition** was rebuilt from the pointer.

## The roster and the registry

- **The library guide.** XXVI's at-a-glance row heads the Market timing layer
  (Draft 1, ~19,400 words). X's row is marked archived. XXVI's line is in the
  reading-order list, and X's line there is marked archived.
- **`tools/check_library.py`.** `REGISTRY` gains
  `"XXVI": "turning-points-bubbles-and-crises"`.
- **The Master Guide.** Table 9 gains XXVI's row, and X's row reads archived.
  `tools/figures/master_guide.py` puts XXVI in the big-frame group, books A and B,
  as X was. Fig 5 and the Guide's HTML were regenerated. The paste did not name
  these files; `check_master_guide` fails without them, as it did for XXXV in B131.

## The gates

| Gate | Result |
|---|---|
| `check_library` | 28 papers, 0 failures, 0 warnings |
| `check_master_guide` | PASSED; 1 warning (the Guide's as-of, a stitch's refresh) |
| `check_registry` | OK |
| `validate_gates` | PASSED |
| `validate_names`, with the list set in the environment only | 0 hits, 21/0 |

## Where the brief was under-specified, and what was chosen

1. **Debt Cycles, Regimes and Environments is not on main.** It sits on
   `library-xxvii`, unmerged, and the session could not read its text (a
   permission prompt was declined). The paper cites it by name for its Part III,
   as the brief says, and for the eighteen environments. Chapter 23 names the
   environments in which each kind of turn occurs and defers the full mapping
   onto the eighteen until that paper is on main.
2. **"2026 as the live case, dated" in Part VI.** The house standard keeps every
   present-tense figure out of the timeless body. Part VI therefore gives the AI
   chain's structure (concentration, leverage, transmission, U.S. exposure), and
   the state of the four markets is in Appendix B.3. Most of those figures are
   quoted as filed and marked unverified (V-108a, V1).
3. **The Top & Bottom Report Manual (XXXI) is not on main.** It sits on
   `library-xxxi`. The paper reports its calibration findings (tops 0 of 3,
   bottoms 4 of 6, controls 4 of 4; 2007 uncatchable by reweighting) by name. The
   T&B harness ledger of 26 Oct, which is on main, supplies the point-in-time
   verdict ("insufficient").
4. **Tactical Applications.** The house standard asks for seven horizons with
   nine fields. A turn is traded on five horizons in this book (the session, one
   to five days, one to six weeks, one to six months, and Book D's), so the
   chapter covers those five, each paragraph answering the nine fields.
5. **People's names.** Policymakers and strategists are named by role ("the
   European Central Bank's president", "BofA Global Investment Strategy"), as the
   filed orders name them. Authors in the literature (Minsky, Kindleberger,
   Greenwood, Shleifer and You) stay.

## The literature and history

The crisis histories and the literature in Parts II to V are cited from the
published sources as the session knew them, and were not re-read here. Appendix A
lists them for re-verification at the operator's read. The episode figures are
Tops and Bottoms' own, and the 2026 figures are the filed orders', with their
verify items.

## CI

Read once after the push.
