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

## Item 46 — an energy shock with a softening labour market (Batch 7; `energy_shock_softening_labour`)

**Added 16 October 2026 (6e-releases, session B). A draft for Ari's accept-all.**

- **The scenario:** an energy price shock lifts headline inflation while hiring slows: Monchau's "hard October call" on the September 2026 CPI.
- **Live when** both hold in the same month:
  - an energy spike by item 46b's rule (CPI energy up 4.0% or more in a month, within the last three months; `config/releases.yaml`);
  - the labour block reads softening: the cyclical core's three-month average below zero, or the diffusion flag on (lens 1 or lens 2, `altdata/releases.py`).
- **What the cell says the Fed faces:** a headline print it cannot ignore against a labour market that argues for patience. The pass-through flag decides which way the cell leans:
  - with the flag off (the shock contained), the cell reads "look through the energy print";
  - with the flag on (propagating), it reads "the shock is spreading while hiring slows", the 1970s pattern item 32 names.
- **Measured by:** item 46b's spike and pass-through flag, and lenses 1 and 2. Each is report-only.

## Section 2.1.5 — the order's one edit (Tranche H; added 19 October 2026)

**Rule-31 draft (library-st-l, session B), for Ari's accept-all.** The signal-triage order's section 2.1.5 asks for one edit by hand. Each line below states what the stack holds on chain-2; none weights a cell.

- **`rates.driver` as a matrix variable (SR-6, SR-17).** The four-cell driver failed its gate twice (0 of 5 episodes, then 2 of 5 under the pre-registered rule; `docs/ledgers/rates-driver-2026-09-30-r2.md`) and is withdrawn. What the matrix can read instead is the rates attribution: each model's path and premium split, dated, with a models-agree flag. It decides nothing, so it can inform a cell and never select one.
- **The reaction-function variable, "defends the front end or the long end" (SR-9).** Adjudicated in real time by the attribution above: the 10-year rising through the premium with the front end anchored reads as the long end lost; rising through the expected path reads as tight but credible. Where the models disagree, the variable prints "models disagree" and says nothing.
- **The cell "market prices a hike, the Fed declines", both branches (SR-21, SR-24).**
  - *Refuse → term-premium repricing, gauged by DEANCHOR.* The base rate does not support the branch as written: on 46 completed divergence episodes since 1982 (DGS1 less the target), the refused episodes' median aligned 10-year change over the next 63 sessions was −17.5 bp against the conceded +45.5 bp (`docs/ledgers/sr-21-ledger-2026-10-18.md`, FAIL; the register's dated note of 18 October records the sign reversal). DEANCHOR is a definition-only flag; its history is the Livingston note (`docs/ledgers/sr-24-ledger-2026-10-19.md`): from 1965 to 1980 realised inflation ran above the survey's twelve-month forecast in 88% of 32 surveys, by a median 1.76 pp, against 29% of 72 in 1984–2019.
  - *Concede → bear-flatten, then resolve, 1994 to 1995.* The hiking-cycle table (`docs/ledgers/fed-cycles-ledger-2026-10-19.md`) carries the 1994 cycle as February 1994 to February 1995, +300 bp in 13 months, the 10-year +172 bp over it, no recession within 24 months, and two conceded SR-21 episodes inside it.
- **The cycle table beside the matrix.** Of 21 completed hiking cycles since 1954, 10 were followed by a recession within 24 months of the last hike (median rise 432 bp, median S&P 500 −5.9% over the next 12 months) and 11 were not (median rise 270 bp, +16.8%). No all-cycle average is printed.
