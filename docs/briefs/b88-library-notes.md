# B88 notes: the library merge rehearsal, and the review packet

Paste B88 (`docs/pastes/B88.md`), 30 Oct 2026. Branch `b88-library-rehearsal` from
`origin/main` at `422ea697`, **never merged**: it scripts next week's library PRs
(D30: each paper merges by its own PR after review). No existing branch was touched.

## The branches found

| Branch | Ahead of main | Tip | In the rehearsal |
|---|---|---|---|
| `library-xxvii` | 6 | `360c13c4` | yes, 1st |
| `library-phase-3a` | 4 | `de217862` | yes, 2nd |
| `library-xxxi` | 2 | `d6fd9181` | yes, 3rd |
| `library-xxxii` | 3 | `1d412b95` | yes, 4th |
| `library-ei-figures` | 5 | `6e6aa1cd` | yes, 5th |
| `library-xxx` | 7 | `50e26cf1` | yes, 6th |
| `library-xxix` | 4 | `88574593` | yes, 7th |
| `library`, `library-draft-3`, `library-st-l` | 0 | — | already on main; nothing to merge |

All seven fork from main at `41803980` and are 33 commits behind `422ea697`.
**There is no `b78-library-rulings` branch.** B78's paste sits on
`library-ei-figures` (`docs/pastes/B78.md`), and its rulings were applied on the
three branches it names (ei-figures, xxxii, xxx), each recorded in that branch's
notes.

## The order, and its sources

The order is xxvii, phase-3a, xxxi, xxxii, ei-figures, xxx, xxix: the paste's
proposed order, unchanged. Its sources:
- **XXVII first:** D38 items 56–60, and B71's paste (Foundations' split points at
  XXVII's chapters). Phase 3a's own needs-you 2 asks the same: "Merge XXVII first,
  or both together, so the pointer never names a paper the roster lacks."
- **The rest:** no branch's notes state an order. XXIX's notes (ruling 5 of
  26 Oct) say "the stitch regenerates" the Master Guide's generated files, "so
  conflicts there are expected and are not fixed per branch". That is the rule
  followed here.

## Each merge

How conflicts were resolved:
- **Generated files** (`docs/figures/master-guide/fig-05-library.svg`,
  `docs/html/master-guide.html`): regenerated from the merged sources with
  `tools/figures/master_guide.py` and `tools/build_paper_html.py
  docs/master-guide.md`. Each new paper's HTML edition was built by
  `bash scripts/make.sh html`.
- **Additive rows** (Table 9, the guide's at-a-glance table, check_library's
  registry, `master_guide.py`'s `GROUPS` and `BOOKS`): both sides kept.

**No conflict touched a paper's body. No branch was stopped.**

| # | Branch | Merge commit | Conflicts | Resolution | check_library | check_master_guide |
|---|---|---|---|---|---|---|
| 1 | xxvii | `f3651ffe` | Guide HTML | regenerated; XXVII's HTML built | 28 papers, 0 F, 1 W | passed |
| 2 | phase-3a | `32ef34e1` | the guide's table (I, II rows against XXVII's row) | both: XXVII's row, phase 3a's restructured I and II | 28, 0 F, 1 W | passed |
| 3 | xxxi | `e2b8d19c` | `GROUPS`, `BOOKS`; Fig 5; Guide HTML | XXVII and XXXI both in the big frame; regenerated | 29, 0 F, 1 W | passed |
| 4 | xxxii | `c69bb5d8` | Table 9; the guide's System rows; check_library's registry; `GROUPS`, `BOOKS`; Fig 5; Guide HTML | both everywhere; XXXII into the evidence group by hand; regenerated | 30, 0 F, 4 W | passed |
| 5 | ei-figures | `1e7ac075` | Guide HTML | regenerated | 30, 0 F, 4 W | passed |
| 6 | xxx | `8dc9cef9` | check_library's registry; Fig 5; Guide HTML | both; regenerated; XXX's HTML built | 31, 0 F, 5 W | passed |
| 7 | xxix | `7bf92899` | `BOOKS`; Fig 5; Guide HTML | both; regenerated; XXIX's HTML built | 32, 0 F, 6 W | passed |

After every merge, `tools/figures/master_guide.py --check` was clean. Rebuilding
every edition changed nothing but the Guide and the new papers' editions. The
branches' own editions (Disruptive Themes, the Twenty-Five, E&I, the Systematic
Book, the T&B manual, the Annual Review) were current.

**The final tip's six warnings** are what the PRs must settle, not faults of the
merges:
1. **Check 11, the guide's word total.** The header reads "Twenty-seven companion
   documents as of 11 October 2026 … roughly 426,000 words"; measured 494,334
   across 32 papers. It is left as found: the header is the guide's refresh that
   every branch's notes leave "for the merge", and changing one number would
   leave the sentence's other counts wrong.
2. **Check 15, four new papers with no structural-review register row:** XXVII,
   XXX, XXXI and XXIX. XXXII's notes say these are "noted for rowing at their
   merge". Each PR after XXXII's adds its paper's row to
   `docs/reading/structural-review-register.yaml`.
3. **Check 15, 25 older papers owe the Assumptions and Falsifiers appendix** at
   review (decision 52). This is a warning by design.

**A note for whoever scripts the PRs.** In this session, calling
`tools/build_paper_html.py` with several paths at once was refused by the
permission layer. With the Master Guide alone it ran. `bash scripts/make.sh html`
(allowlisted) builds the roster papers but **not** the Master Guide, so the
Guide's HTML needs its own `python tools/build_paper_html.py docs/master-guide.md`
after every merge, or check_library's check 10 fails ("built from a different
master-guide.md").

### The script, per PR

1. Merge the branch.
2. For each conflict:
   - Figure 5 or the Guide's HTML: take either side, it is regenerated below.
   - A table row or registry line: keep both.
   - A paper body: stop, and abort.
3. `python tools/figures/master_guide.py`.
4. `python tools/build_paper_html.py docs/master-guide.md`.
5. `bash scripts/make.sh html`.
6. Add the paper's structural-review register row (after XXXII is on main).
7. Run `check_library` and `check_master_guide`, then commit.

The last PR also refreshes the guide's header: the paper count, the as-of date and
the word total.

## THE REVIEW PACKET

What the operator reads before approving each library PR, in merge order. Word
counts are whitespace-split, as check_library counts them.

### 1. XXVII, Debt Cycles, Regimes, and Environments (`library-xxvii`)
- **Words:** 24,647 (brief ~20,000). **Version:** 1.0 Draft 1, 24 Oct 2026.
- **Chapters (23):**
  - Part I, the cycles (Ch 1–4: the short cycle, the long cycle, repression and
    fiscal dominance, the reserve currency);
  - Part II, locating the present (Ch 5–7);
  - Part III, tops of long cycles from inside (Ch 8–12: 1929, 1989, 2000, 2007,
    now);
  - Part IV, the environments (Ch 13–16);
  - Part V, identification and transition (Ch 17–20);
  - Part VI, tactical applications and wiring (Ch 21–23);
  - Appendix A, assumptions and falsifiers; Appendix B, dated.
- **Figures:** none drawn; 6 placeholders.
- **To verify:** none marked.
- **Decide before the PR:**
  1. the length: keep 24,600, or trim Part I to about 23,000;
  2. the proposed branch rule (17.4): Doctrine #2 or later;
  3. the guide's drafted entry;
  4. Amendment #3 workstream B: the 13 Sep order is not in the repo, and the
     internal-order lens was built without it.
- **At the PR:** its review-register row (check 15).

### 2. Phase 3a, Foundations (I) and The Twenty-Five (II) restructured (`library-phase-3a`)
- **Words:**
  - Foundations: 22,140, a timeless body of about 16,000 plus a new dated
    Appendix B of about 5,900 (5,720 words moved, in 16 sections);
  - The Twenty-Five: body 8,036, plus the companion appendix
    (`docs/whitepapers/companions/`) at 17,223 (17,053 moved, in 25 sections).
  - Text moved, not rewritten. **Version:** 1.1, 25 Oct 2026, for both.
- **Chapters:**
  - Foundations keeps its numbering, with gaps (1.1, 1.2, 1.6, 1.7 …), plus
    Appendices A and B;
  - The Twenty-Five keeps Parts 0–3 in the body, with one pointer sentence per
    family to the companion.
- **Figures:** none. **To verify:** none.
- **Decide before the PR:**
  1. the companion's home: `companions/`, or a gate exclusion;
  2. the numbering gaps: leave them or renumber;
  3. two dated passages left in the bodies (Foundations 8.2; the Twenty-Five's
     Part 2 build queue): a Phase 3b, or keep them.
- **Settled by this order:** XXVII merges first (its needs-you 2).

### 3. XXXI, The Top & Bottom Report Manual (`library-xxxi`)
- **Words:** 8,107. **Version:** 1.0, 24 Oct 2026.
- **Parts:**
  - I, what the report is;
  - II, the composite;
  - III, the ten triggers;
  - IV, the three overlays;
  - V, the gap-patch;
  - VI, calibration;
  - VII, the false-bottom audit;
  - VIII, how a signal joins;
  - IX, what the report may say;
  - Appendix A, where the specification and the code differ.
- **Figures:** none. **To verify:** none marked.
- **Decide before the PR:**
  1. read Draft 1;
  2. the ten triggers' roll-up tiers: unconfirmed in the specification, and the
     manual states none;
  3. the gap-patch's full input list: the repo records only its house-price
     input.
- **At the PR:**
  - its review-register row;
  - it has no Assumptions and Falsifiers appendix. It is dated 24 Oct, before
    `AF_FROM`, so it only warns.

### 4. XXXII, The Annual Structural Review (`library-xxxii`)
- **Words:** 4,324. **Version:** 1.0, 24 Oct 2026.
- **Parts:**
  - I, what a review asks;
  - II, the four instruments;
  - III, the questionnaire;
  - IV, the calendar;
  - V, the standing register;
  - VI, the gate;
  - VII, the log;
  - VIII, a worked review;
  - Appendix A, the register at seeding; Appendix B, assumptions and falsifiers.
- **Also brings:**
  - `docs/reading/structural-review-register.yaml`;
  - check_library's check 15 (decision 52, adopted in B78), with its fixture
    pair.
- **Figures:** none. **To verify:** none.
- **Decide before the PR:** the calendar's departure from the audit's all-in-January.
- **Mind:** from this merge on, check 15 is live. Every later paper needs its
  register row, and a paper first dated on or after 26 Oct needs the appendix or
  it fails.

### 5. Evidence and Inference, figures and the Chapter 14 sentence (`library-ei-figures`)
- **Words:** 4,225. **Version:** 1.0.1, 26 Oct 2026, "Chapter 14 sentence per
  Figure 4".
- **Chapters:** 16, across Parts I–IV, and the card.
- **Figures:** 5 drawn by `tools/figures/evidence_inference.py`, replacing the
  September artwork. Old `fig-06.svg` is removed; Figure 4 is new.
- **To verify:** none.
- **The body edit** is decision 55's one sentence, ruled.
- **Decide before the PR:** look at the five figures once; they were drawn by
  coordinates. Figure 2's preview was seen (B78).

### 6. XXX, Market Structure and Cascades (`library-xxx`)
- **Words:** 16,945 (accepted with no cuts, ruled 26 Oct). **Version:** 1.0
  Draft 1, 26 Oct 2026.
- **Chapters (23):**
  - Part I, how a trade becomes a price (Ch 1–5);
  - Part II, cascades as one subject (Ch 6–8 …);
  - Part III, the cases (to Ch 18, the two short instances, accepted);
  - Part IV, the fragility read (Ch 19–);
  - Part V, tactical (to Ch 23);
  - Appendices A, assumptions and falsifiers, and B, dated.
- **Figures:** 7, renumbered by appearance (B78).
  - **3 drawn:** Fig 1, the cascade loop (conceptual); Fig 3, the stock–bond
    correlation; and Fig 5, the VIX through the cases. Figs 3 and 5 are drawn
    from the laptop store, and the box regenerates them.
  - **4 placeholders, drawn at merge from the box's store:**
    - Fig 2, `exposure.net_gex`;
    - Fig 4, `cftc.tff_lev_money_net_oi`;
    - Fig 6, `levetf.aum`;
    - Fig 7, `finra.margin_debit`.
- **Also moves** the Systematic Book's §3.5 (347 words) to XXX's 5.4. Its light
  edit was accepted 26 Oct; the Systematic Book is now 8,926 words.
- **To verify:** none marked.
- **Decide before the PR:** whether the four store-drawn figures are drawn on the
  box before the PR or left as placeholders for a later edition.
- **At the PR:** its review-register row.

### 7. XXIX, Real Assets and Risk Transfer (`library-xxix`)
- **Words:** 13,759 (13,718 accepted, ruled 26 Oct). **Version:** 1.0 Draft 1,
  26 Oct 2026.
- **Chapters (11):**
  - Part I, real estate (Ch 1–4: housing, the cycle, CRE, REITs);
  - Part II, infrastructure and agriculture (Ch 5–6);
  - Part III, risk transfer (Ch 7 onward, ILS and reinsurance);
  - Part IV, tactical;
  - Appendix A, assumptions and falsifiers;
  - Appendix B, the figures behind the body, dated 26 Oct.
- **Figures:** 6 placeholders, drawn in a later edition, each named with its
  store key.
- **To verify: 8 open marks**, each to be verified before merge (ruled 26 Oct):
  - Freddie Mac PMMS;
  - FTSE Russell / NCREIF;
  - Swiss Re Institute sigma (twice);
  - FDIC;
  - Artemis / Aon;
  - Federal Reserve Z.1 / MBA;
  - FHFA / ICE Mortgage Monitor.

  They cover B.2's five episode rows and B.3's three bullets.
- **Decide before the PR:** clear the eight marks against their sources.
- **At the PR:** its review-register row.

## Needs-you

1. **XXIX's eight "(to verify)" marks.** They must be cleared against their
   public sources before its PR, by a paste that reads the sources, or by the
   operator.
2. **XXX's four store-drawn figures:** drawn on the box before its PR, or left
   as placeholders for a later edition.
3. **The guide's header** (the paper count, the as-of date, roughly 494,000
   words): refreshed in the last PR, or by B66's proposed `--write-total` mode.
4. **The review-register rows** for XXVII, XXX, XXXI and XXIX: each PR adds its
   own, or one pass after XXXII merges.
5. **The open draft decisions** listed per paper above (XXVII's length and
   17.4; phase 3a's companion home and numbering; XXXI's trigger tiers; XXXII's
   calendar).

## CI

Read once at the end (in the report).
