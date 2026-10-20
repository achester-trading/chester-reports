# library-st-l: session notes (Part 2 of session B's paste of 19 Oct 2026)

**Branched from chain-2's tip `ab27c07`** (`docs/briefs/chain-2-stitch-notes.md`'s first
line reads `STITCH COMPLETE e0a8cc0 2026-10-19 12:49 ET`). Merges after chain-2. Nothing
merged, deployed or run on the box. Every document written here is a rule-31 draft for
your accept-all (the list is at the end).

## What was built

### ST-L's dated appendices

Each is `## Appendix X — Dated: Calibration ledgers (ST-L) ... (as of 19 October 2026)`.
Each entry quotes its ledger's as-of, window, n, verdict and rights consequence word
for word, notes the register's acceptance of 19 Oct where the register records it, and
says "laptop first edition; the box edition supersedes it". A study the slot names
with no ledger on chain-2 says so.

| Paper | Appendix | Entries |
|---|---|---|
| The Rate and Liquidity Machine | A | the rates driver (SR-6, SR-9, SR-17), SR-21, SR-22, SR-23, ST-R4.17b, SR-24 (Livingston), SR-7 (the cycle table) |
| Equities | C | SR-1, SR-13, ST-R5.31b, ST-R5.44b; SR-25 has no ledger |
| Currencies | E | SR-2, SR-4, SR-14, SR-20 (COFER) |
| Metals | F | SR-15 |
| Energy | E | ST-R5.32b; SR-18 has no ledger |
| Credit | E | SR-5, ST-R5.35b; SR-16 has no ledger |
| Base Rates | D | SR-1, 2, 5, 6 (the driver), 7 (the cycle table), 12, 13, 15, 21, 22; SR-25 has no ledger |
| Positioning & Flows | A | SR-8 (the audit's fuel metrics), ST-R5.30b, SR-12 |
| The Operating Doctrine | E | SR-8, SR-22, with their proposals for Doctrine #2 |
| Portfolio Construction | A | the Book A rule table's gates: A-3 (SR-12, 15, 21, 22, 23), A-4 (ST-R5.30b), A-5 (ST-R5.32b) |
| Digital Assets | F | the mechanism watch, Pearl and proof-of-useful-work (the order's 2026-09 entry), from chain-2's code |
| Disruptive Themes | A | the Factor I and Factor V evidence log's frame (ruling 6), empty |

- **The one timeless paragraph:** "Proof-of-Useful-Work", a subsection of the Digital
  Assets paper's section 7 (Miners and Validators). No date and no project in it;
  Appendix F is the dated instance.
- **Not on this line, so no appendix:** the Debt Cycles brief, the Market Structure &
  Cascades brief and the operator behavioral paper (ST-L names them; none is a paper
  under `docs/whitepapers/` on chain-2).
- **Positioning & Flows** already had an unlettered `## Appendix — The absorption
  primitive`; the dated one is lettered A because the library check needs a letter on
  a dated heading.
- **For the guide's next update** (I did not edit the library guide or the Reader's
  Guide; Draft 3 owns both): the twelve appendices above, the new ledgers below, and
  the stale word totals the twelve papers now carry.

### Tranche H, the one-time items

- **The hiking-cycle table, computed:** `tools/calibration/fed_cycles.py` writes
  `docs/ledgers/fed-cycles-ledger-2026-10-19.md` and its CSV through
  `altdata.ledgers` (so its name is `<item>-ledger-<date>`, the ledger writer's form;
  the order's `data/reference/fed_cycles.csv` is gitignored).
  - **The rule, pre-registered by the first edition:** the monthly policy rate
    (FEDFUNDS' monthly average to 1982-09, the target at month-end from 1982-10, the
    range's midpoint from 2008-12); a turn is confirmed by a 75 bp reversal; a cycle
    runs from the first month above a confirmed trough to the first month at the next
    confirmed peak, if the rise is at least 100 bp.
  - **Result:** 21 completed cycles, 1954 to 2023. 10 were followed by a recession
    within 24 months of the last hike (median rise 432 bp, median S&P 500 -5.9% over the
    next 12 months); 11 were not (270 bp, +16.8%). No all-cycle average prints.
  - **SR-21's rows** are read from `docs/ledgers/sr-21-ledger-2026-10-18-episodes.csv`:
    7 conceded and 5 refused fall inside cycles.
  - **The effective-rate era** gives one artefact: a one-month "cycle" in February
    1961, which the rule finds and the caveats explain.
- **The Warsh matrix's single edit** (section 2.1.5): appended to
  `docs/warsh-matrix-lines.md`.
  - The driver is withdrawn, so the matrix reads the rates attribution, which decides
    nothing.
  - The refuse branch is stated against SR-21's FAIL and its sign reversal.
  - The concede branch is the 1994 cycle from the table.
  - DEANCHOR's history is the Livingston note.
- **Doctrine #2 (7-8 Nov) proposals:** `docs/briefs/doctrine-2-proposals-st-l.md`
  holds five items:
  - the SR-3 tail-register edits;
  - the 5.25% note (SR-9);
  - the projection-rule rationale (SR-18);
  - SR-8's rule candidate (adopt the principle, hold the re-entry clause: only one
    confirmation element discriminates);
  - SR-22's note.
- **SR-20's first scorecard entry:** `tools/calibration/sr20_cofer.py` writes
  `docs/ledgers/sr-20-ledger-2026-10-19.md`.
  - **The source:** COFER read keyless, within the IMF's terms, through
    `altdata/sources/_imf_sdmx.py` (one request).
  - **The entry:** USD 56.70% of allocated reserves in 2026-Q2, -0.24 pp on four
    quarters; its range since 1999 is 56.52% (2025-Q4) to 72.13% (1999-Q2).
  - **Not tracked, each with its reason:** the constant-FX share, the gold share and
    the holder split (SR-27's tags are not built).
- **SR-24's Livingston note:** `tools/calibration/sr24_livingston.py` writes
  `docs/ledgers/sr-24-ledger-2026-10-19.md`.
  - **The source:** the Philadelphia Fed's MedianGrowthRate.xlsx. Robots allows it, and
    the page carries no reuse terms beyond the Bank's copyright.
  - **The measure:** the CPI forecast (G_BP_To_12M) against CPIAUCNS over the same
    fourteen months.
  - **1965-80:** realised inflation was above the forecast in 88% of 32 surveys, by a
    median 1.76 pp, and the forecast sat below trailing inflation in 88%.
  - **1984-2019 (the control):** 29% above, 44% below.
- **Not created (rule 30):** the manual_input entries. The Mechanism Watch's promote
  and reject stay yours.

## Gates

- `tools/validate_library_st_l.py` (new; in the Makefile, so the count line reads one
  hundred and nineteen code gates, one hundred and sixteen Python): **17/0**.
  - **Group A:** a fixture of the target's real steps reproduces two cycles worked by
    hand: 2004-06 to 2006-06, +425 bp over 25 months; and 2015-12 to 2018-12, +225 bp
    over 37 months.
  - **Group B:** every appendix entry quotes its ledger as recorded.
  - **Group C:** the Tranche H documents.
- `tools/check_library.py`, run once at the end: **0 failures, 0 warnings** (27
  papers), after `make html` rebuilt the twelve editions.
- `tools/validate_audit_3a.py`: **88/0** (the count line).

## Box commands

None for this branch: the three studies read public sources and are re-run on the box
only if you want box editions:

```bash
cd ~/chester-reports
.venv/bin/python tools/calibration/fed_cycles.py --box
.venv/bin/python tools/calibration/sr20_cofer.py --box
.venv/bin/python tools/calibration/sr24_livingston.py --box
```

## Files shared with session A's branches

- **library-draft-3:** the twelve papers' `.md` and their `docs/html/` editions, the
  library guide (untouched here) and `docs/warsh-matrix-lines.md`.
- **a47-chain3:** `CLAUDE.md` (the count line only) and the `Makefile` (one gate line).

## Needs you: the rule-31 drafts, for accept-all

1. The twelve dated appendices above, and the Digital Assets paper's timeless
   paragraph.
2. The Warsh matrix's section 2.1.5 entry.
3. The five Doctrine #2 proposals.
4. The three new ledgers: the cycle table, SR-20's entry and SR-24's note. Each states
   it grants nothing.
