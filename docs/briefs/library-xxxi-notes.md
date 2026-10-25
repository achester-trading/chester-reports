# library-xxxi: the Top & Bottom Report Manual, Draft 1 (session A, A72, 24 Oct 2026)

**What it is.** Paper XXXI, the Top & Bottom Report Manual, at the numeral Audit 2 reserved for it (`docs/white-paper-library-audit-2.md`, "Decisions taken — 7 September 2026", decision 1, and the roster's XXXI row).
- **File:** `docs/whitepapers/tb-report-manual-whitepaper.md`.
- **Branch:** `library-xxxi` from `origin/main` at `41803980`, in a new library worktree, `../chester-lib31`.
- **Library line:** it merges by its own pull request after the operator reads it, never through a chain.

## Size

**About 8,100 words** (8,107, whitespace-split, the gate's method). The paste asks for about 8–10k. The audit's roster row said about 4k; the paste is later and governs.

## The one fact that shaped it: no T&B package exists

The paste says to write from "the code and its config (find the T&B package by name)". **No T&B package exists in this repository**, on main or any chain. The report's engine (scoring engine v8, a calibration script, report v13) was built on 3 September 2026 as a separate pipeline; its build log is the architecture document's Part 23.

This repository holds five related things, and none of them computes the report:
- the Monthly's `top_bottom_block`, which reads `top_bottom.composite` and `top_bottom.verdict`, finds none, and prints that the harness is not built;
- the bear-rally base rate beside it;
- the inert `config/tb_false_bottom_gate.yaml`;
- `config/tb_intake_queue.yaml`, with one draft entry, GTM-3;
- `docs/ledgers/false-bottom-audit-2026.md`.

The manual is therefore written from the specification and those files:
- the master narrative's section 3;
- the translation table's conflict rule;
- the architecture's Part 23;
- *Tops and Bottoms*' methodology;
- the triage order's section 2.6 and the register.

It says so in its reader's note, in Part I chapter 3, and in Appendix A row 10. Every figure the separate engine produced is in the dated Appendix B with its date and source, none in the body.

## Where the specification and the code differ (Appendix A, ten rows)

The code wins in each:
1. no harness;
2. no timer;
3. no quarterly calibration or continuous backtest;
4. the false-bottom gate is inert;
5. the intake queue holds one draft;
6. the Reinhart–Rogoff input is not in the repo;
7. the ten-trigger roll-up tiers are unconfirmed;
8. inputs are read once from the store;
9. the rates driver is withdrawn;
10. no T&B package.

## House standards applied

- **Prose first, then a cheat-sheet table**, in every Part.
- **Empirical claims carry their sample and date:** the calibration "as of 3 September 2026, thirteen hand-keyed episodes"; the audit "as of 16 October 2026, four bears".
- **No forecast anywhere:** the edition's own "today" synthesis is quoted in Appendix B as a recorded value.
- **Cross-references by short name:** *Tops and Bottoms*, *Base Rates*, *Evidence and Inference*, the Operating Doctrine, the Reader's Guide, the Monthly manual.
- **The masthead in the house format**, at version 1.0.
- **Dated content in a dated appendix:** Appendix B, "Dated: The Report's Recorded Values (as of 24 October 2026)", which the library gate's check 14 reads.
- **A system manual, not a markets paper.** It carries no Tactical Applications, Wiring or Environments chapters, which the house standards require of content papers. It keeps an Assumptions and Falsifiers appendix (C).
- **Not re-narrated:** it cites *Tops and Bottoms* for the history and re-narrates no episode.

**No names of people** except authors of cited published work (Reinhart and Rogoff, *This Time Is Different*, 2009):
- the master narrative's named strategist framework is "a published bull-and-bear indicator from a large bank's research desk";
- the two IPO triggers are described by kind;
- the ledger's data library is not named in the paper.

No Brookfield-group instrument appears.

## What the gate forced

The library gate fails any file in `docs/whitepapers/` with no at-a-glance row and no registry entry, and `check_master_guide` fails a roster paper with no group or Table 9 row. So, as B62 did for XXVII:
- `tools/check_library.py`'s REGISTRY gains `"XXXI": "tb-report-manual"`;
- the guide gains **one placeholder at-a-glance row**, marked as a placeholder;
- `tools/figures/master_guide.py` places XXXI in "The big frame (Book A, the Monthly)", serving Book A;
- the Master Guide's Table 9 gains one row (Draft 1, in review);
- Figure 5 is regenerated, and the Guide's HTML is rebuilt;
- the paper's HTML edition is built.

**Not changed:** the guide header's library total. The gate warns that the claimed 426,000 words is past 5% of the measured 451,487, but that is a warning, not a failure, and the library-draft-4 branch updates the same line. Merging both would conflict.

## The guide's one-page entry, drafted for review (not written into the guide)

> ## XXXI. The Top & Bottom Report Manual
> **Companion to: the Top & Bottom report and Book A's override · v1.0 Draft 1 · ~8,100 words, nine parts + three appendices · 24 Oct 2026**
>
> **What it contains.** The working manual of the turn detector, the counterpart of the Monthly manual.
> - Part I is what the report is: the question it answers, its one right (Book A's override), its place in the tier rule, and the plain fact that its harness is not built in this repository.
> - Part II is the composite: eight categories, about fifty indicators each scored from −2 to +2, five verdicts.
> - Part III is the ten triggers and their states.
> - Part IV is the three overlays (Concentration and Complacency, High-Yield Spread Acceleration, Liquidity and Funding Stress), each built for a top type the composite misses.
> - Part V is the Reinhart–Rogoff gap-patch and what the repository records of it.
> - Part VI is the calibration against thirteen episodes: stronger at bottoms than at tops, the 2007 top structurally uncatchable, and the one reweighting.
> - Part VII is the false-bottom audit and its FAIL.
> - Part VIII is the intake queue, and how a triage item that names the report enters it.
> - Part IX is what the report may say, how to read an edition, and what a build here must satisfy.
> - Appendix A lists where the specification and the code differ; Appendix B holds every recorded value with its date.
>
> **Timeless takeaways:**
> - **Bottoms rhyme; tops do not** — a single average cannot weight every top's cause, so the overlays stand outside the composite.
> - **A condition is not a timing signal** — an active overlay says the shape resembles a top's, never when.
> - **Know which turns the system cannot see** — 2007 was outside the indicator set, and no reweighting found it.

## Gates

| Gate | Result |
|---|---|
| `tools/check_library.py` | 28 papers, 0 failures, 1 warning (the library total, above) |
| `tools/check_master_guide.py` | 0 failures, 0 warnings |
| Sequential numbering | Parts I–IX, chapters 1–27, appendices A–C |

## CI

| Run | On | Result |
|---|---|---|
| 40152328215 | `20d17d83` | **CI queued, run 40152328215** (not waited on) |

## Needs you

1. **Read Draft 1.** It merges by its own pull request after you do.
2. **The ten triggers' roll-up tiers.** These are unconfirmed in the specification. A build here must declare them, and the manual states none.
3. **The gap-patch's full input list.** The repo records only its house-price input, so the manual does not reconstruct the rest.
