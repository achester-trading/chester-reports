# The Warsh scenario matrix: lines from the signal-triage batches

A **Warsh-matrix line** is one scenario the triage batches ask the Warsh scenario
matrix to carry: the scenario, the measures that say whether it is live, and what
the matrix's cell says the Fed faces in it. The matrix itself is a Tranche H
surface (the 25 Sep order, section 7, "Warsh scenario matrix: section 2.1.5 edit
list"); this file holds the lines until that edit is made.

**Status.** Under the ruling of 16 October 2026, judgment drafts are committed as
drafted and listed for Ari's accept-all. That is the status of every line below
until Ari accepts it. A line has no decision rights and grades nothing.

**This file's origin.** Session A creates this file on `st-r5-audit`. That branch
did not exist when this line was written (16 October 2026), so session B created
the file on `6e-releases` in the same shape. At the stitch the two are joined: one
header, every line kept.

## energy_shock_softening_labour — an energy shock with a softening labour market (Batch 7 item 46)

**Added 16 October 2026 (6e-releases, session B). A draft for Ari's accept-all.**

- **The scenario:** an energy price shock lifts headline inflation while hiring slows: Monchau's "hard October call" on the September 2026 CPI.
- **Live when** both hold in the same month:
  - an energy spike by item 46b's rule (CPI energy up 4.0% or more in a month, within the last three months; `config/releases.yaml`);
  - the labour block reads softening: the cyclical core's three-month average below zero, or the diffusion flag on (lens 1 or lens 2, `altdata/releases.py`).
- **What the cell says the Fed faces:** a headline print it cannot ignore against a labour market that argues for patience. The pass-through flag decides which way the cell leans:
  - with the flag off (the shock contained), the cell reads "look through the energy print";
  - with the flag on (propagating), it reads "the shock is spreading while hiring slows", the 1970s pattern item 32 names.
- **Measured by:** item 46b's spike and pass-through flag, and lenses 1 and 2. Each is report-only.
