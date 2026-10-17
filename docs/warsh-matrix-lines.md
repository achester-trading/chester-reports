# Warsh matrix: scenario lines

The **Warsh matrix** is Ari's own scenario document for the Federal Reserve under Chair Warsh. It is kept outside this repository, and its cells and weights are his. The signal-triage batches send it **scenario lines** (Batch 6 items 34 and 42; Batch 7 item 46). Until now those lines had no home in the repo, so each was left in a session's notes. This file holds them.

Each entry records:
- the item it comes from, and the date it was added;
- the scenario, in one sentence;
- the measure that adjudicates it, by its ST id where the stack computes one.

**Status.** Under the ruling of 16 October 2026, judgment drafts are committed as drafted and listed for Ari's accept-all. Every entry below has that status until Ari accepts it. A line here does not weight a cell. The matrix's weights stay Ari's, and the measures are descriptive and unvalidated until their ledgers say otherwise. Entries are added with their date and never rewritten. A later ruling that changes a line is a new entry.

The disagreement pairs that some of these items also produce are in `docs/narrative-register-pairs.md`.

## Item 34 — the market does the tightening (Batch 6; added 16 October 2026)

- **Scenario:** while the long end rises and twelve-month policy pricing falls, the market is tightening conditions in the Fed's place, so "fewer hikes delivered" reads as the long end doing the work, not as easing.
- **Weighting it suggests:** with the flag on and the NFCI tightening, weight the hold-and-let-the-curve-work cell up and the hikes-resume cell down. With the flag off, this line says nothing.
- **Adjudicated by:** ST-R5.34a, the market-does-the-tightening flag (the 10-year up while twelve-month policy pricing falls over four weeks, read from fed funds futures for the US and two-year yields elsewhere), with the Chicago Fed NFCI as the confirming conditions measure. The G8 two-year panel is ST-R5.34b.
- **Source:** Ruth Carson (Bloomberg), quoting Ken Orchard (T. Rowe Price). Drafted by this branch, because no draft existed: the order's "Warsh-matrix line — by hand 0.25h" was never written.

## Item 42 — inflation expectations turning up (Batch 6; added 16 October 2026)

- **Scenario:** if composite inflation expectations re-anchor higher, the Fed follows with a lag and hikes resume. If they fall while the 10-year rises, the long end is doing the tightening.
- **Weighting it suggests:**
  - with the composite at or above +1.0 z and rising, weight the hikes-resume cell up;
  - with the composite below 0 and falling while the 10-year rises, weight the hold-and-let-the-curve-work cell up.
- **Adjudicated by:** ST-R5.42a, the composite inflation-expectations z-score (the 5y5y breakeven, Michigan 5–10-year, NY Fed SCE 3-year and Cleveland Fed 10-year expected inflation, monthly), read against item 34's flag.
- **Source:** Callum Thomas (Topdown Charts). Moved here from the `st-r5-t1-rest` session notes, where it was drafted, with its text unchanged in substance.

## Item 46 — (Batch 7)

Session B adds item 46's line here, in the same shape.
