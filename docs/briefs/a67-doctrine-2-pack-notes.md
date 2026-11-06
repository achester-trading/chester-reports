# A67: the Doctrine #2 pack, refreshed with October's rulings (24 Oct 2026, overnight)

Docs only and branch-only: no code, no config, no gate change. `docs/briefs/doctrine-2-pack-2026-11.md` is rewritten into the sitting's shape: 72 numbered decisions, D2-1 to D2-72, each with the value as set, the alternative and a one-line recommendation.

## Base

`a67-doctrine-2-pack` branches from `origin/a66-capex-guidance` at its tip, `841d7513`, which carries chain-7, A65 and A66.

## What changed in the pack

- **The new agenda: Parts 1–7, as the brief orders them.**
  1. Values ratified or replaced: D2-1 to D2-4. The five confirmed sets are in full, then B51's lag table and the families added since, the sets ruled earlier in October, and the unruled sets by subsystem.
  2. Structural changes: D2-5 to D2-10. The budgets, B60's caps, and the Weekly's structure and charts since 2 Oct.
  3. Standing rules: D2-11 to D2-17. D5, D6, the 16 Oct sources rule with ten refusals, the lag rule, D21, budgets as targets, and the one-list presentation rule.
  4. Regime and calibration: D2-18 to D2-21. The `calc.infl_vol` bridge, 6f's twelve rulings, the first calibration read, and A65's stamp floor.
  5. The register: D2-22 to D2-25. Items 45–78 drafted at SR-60 to SR-93, the earlier unnumbered items, amendments, and the pending rule-31 lines.
  6. The attention budget: D2-26 to D2-28.
  7. The calendar: D2-29 to D2-31.
- **Part 8 carries the 20 Oct edition's items that still apply,** one row each: D2-32 to D2-72.
  - **Their full text** is Annex A, the 20 Oct Parts A and B, verbatim with headings demoted. The setup drafts are Annex B, the 20 Oct Part C.
  - **Changes noted in Part 8:**
    - V-2's stamp is recorded as done: B49 and chain-4 stamp the Volatility and Gamma dials and the volatile-day flag at entry (`tools/decide.py`, `_gate_detail`).
    - V-3 is corrected from "two" values to three.
    - W-3, W-4 and W-6 and H-2's agenda line moved to D2-27, D2-10, D2-5 and D2-18.
- **Reading time:**
  - the decision list, about 11 minutes;
  - Parts 1–7, about 21;
  - the whole pack with its annexes, about 68 (15,603 words at 230 a minute), inside the two-hour sitting.

## How the inventory was made

Three read-only sweeps went across `docs/`, `config/` and the branches. They covered:
- the session-set tables and their status, the rule-31 drafts and the needs-you counts;
- items 45–78 against the register and the batch orders;
- the budgets, caps, Weekly changes, refusals, 6f and the calendar.

Each fact in the pack names its file and line.

**Notes files read for session-set values** (`docs/briefs/`, `*-notes.md`):
6b-dealer-1, -2, -3; 6e-digital; 6e-releases; 6e-rest; 6e-lenses; a43; a44; a45; a47; a48; a49; a50; a52; a53; a54; a55; a56; a57; a58; a61; a62; a63; a65; a66; alpha-lab-1, -2, -4; aq-2-chapters, aq-2-chapters-2; aq-3-series-1; aq-5; aq-8a; aq-9a; aud-2; aud-3c; audit-leftovers-1, -2; b45; b48; b51; b52; b55; b56; b59; b60; book-b-scanner, -2; c1-move-screen; chain-3, -4, -5-stitch; crypto-basket; crypto-tranche-a-1, -2; friday-stitching; gtm-core-1, -2; lenses-group-b; library-st-l; meme-ingest-ledgers-1; master-guide-notes; sr-36; sr-43-49; st-r4-tranche-1, -1b; st-r5-fixes; st-r5-index; st-r5-t1-rest; st-r6-45; st-t1-rest; st-t2-rates; st-t3-calib; vol-event-52; vp-1; w-1-1; w-1-2; w-1-3a, -3b, -3c; weekly-fixes-7, -8, -9; writer-fixes-1.

Also read from `origin/a61b-feed-repair`: `a61b-feed-repair-notes.md` (no session-set section) and `rulings-2026-10-24-pm.md`.

The needs-you counts were taken by script across all 120 notes files.

## What I could not classify

1. **D4's reach.** Whether D4 ("CONFIRMED as set") covers chain-5's two added lag families (`chain-5-stitch-notes.md`, line 77). D2-2 takes them explicitly.
2. **The 6e-digital budget values** (lines 160–170). Partly superseded by D19/D20 (the addendum to about 1,500 words, 7 min), and nothing records which of the others survive.
3. **A54's 1.5×** is labelled both "RULED, D2" and "session-set, provisional". That D2 is an earlier numbering, not the 24 Oct D2.
4. **A57's ST-R6.71d n.** The notes give n 2,965; the register and D9 give none.
5. **Audit #4's sitting.** The agenda schedules two sittings on 14–15 Oct, but no minutes exist and the attention log has no row. Whether it sat, and for how long, cannot be read from the repo.
6. **Accept-all drafts that never say "rule 31"**, status not found:
   - 6e-releases (line 336);
   - st-r4-tranche-1b (423);
   - st-r5-fixes (125, six drafts);
   - 6e-rest (33, Batch 5 drafts);
   - vol-event-52 (74, the volatility paper's drafts).
7. **Alpha-lab-1's numeric values.** "Not yet ruled" on 14 Oct, and no later ruling found.
8. **The numbers of ST-R6.51c** (the Monthly's first Digital Assets chapter, due before 1 Dec). No build or notes record found (D2-30).
9. **Two calendar items** have no dated line in `docs/`: the wider options universe revisit (1 Dec, in the brief only) and the cloud-session move.
10. **The attention log** holds 2–8 Oct and 24 Oct only. About ten chat ruling rounds from 12 to 23 Oct are recorded only in notes files (D2-28).
11. **Items 47 and 50.** Whether an item that is a by-hand yes with no key (47), or not built pending a ruling (50), should take an SR number now. Table 5.1 gives both one.

## Gates

- `check_library`: 27 papers, 0 failures, 0 warnings.
- Nothing else is touched.

## CI

| Run | On | Result |
|---|---|---|
| 40144509130 | `cf797d36` | **success** (11m7s) |
