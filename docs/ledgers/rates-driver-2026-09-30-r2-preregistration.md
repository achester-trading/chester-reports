# Rates driver — pre-registration for rerun 2 (SR-6, SR-17)

*Written and committed on 2026-09-30 **before** any code for rerun 2 exists and
before it has run. Never edited. The rerun's ledger,
`rates-driver-2026-09-30-r2.md`, is judged against this file and nothing else.*

Rerun 1 ([ledger 2026-09](rates-driver-2026-09.md)) failed: 0 of 5 episodes, 0 of
27 grid points. SR-6 and SR-17 are `DEFERRED — gate failed`. The operator ruled
on 30 Sep: (a) fix the DKW share definition, (b) test ONE pre-declared
hypothesis about `fed_path`, (c) keep the episode sets under the pass rule
below, written down first, and (d) defer the register entries, which is done.

## What changes — and nothing else

**(a) The DKW shares' denominator.** `calc.attr_dkw_path_share_60d` =
Δ expected real short rate ÷ (Δ expected real short rate + Δ real term premium),
and `_tp_share_60d` = Δ real term premium ÷ the same sum. Both use 60 DKW
observations. They are written only when |sum| ≥ 5 bp. The TIPS liquidity
premium leaves the denominator: the driver's question is path against premium,
and the liquidity premium is neither. Every other feature definition is
unchanged.

**(b) Hypothesis H1 — the only one tested.** The `fed_path` rule tests its
breakeven condition on the existing **20-session** series, not the 60-session
one:

- Δbreakeven₂₀ = `calc.attr_d10y_20d` × (1 − `calc.attr_real_share_20d`),
  signed against the **60-session** move's direction. The condition is
  "against" when Δbreakeven₂₀ × sign(Δ10y₆₀) < −`be_flat_bp` (5 bp).
- Both 20-session inputs must be written on the move's own session, the same
  rule as the 60-session cuts.
- The rule's front-end condition stays on the 60-session curve share. The
  `growth` rule is unchanged: its breakevens stay on 60 sessions.
- No other window is tried. The 5-session series is not tested.

**Thresholds are v1.11's, untouched:** share_min 0.60, move floor 15 bp,
be_flat 5 bp, front leading > 1.0, front anchored ≤ 0.5, sign dead-band 5 bp.
The 27-point grid is reported as robustness only; it cannot change the verdict
or a threshold.

**Unchanged from rerun 1:**
- the five episode windows (1994 02-04→11-07, Q4 2018 08-22→11-08, 2022
  01-03→10-21, 2013 05-02→09-05, Aug–Oct 2023 07-31→10-19);
- the expected cells: bear flattening → `fed_path`, bear steepening →
  `term_premium`;
- the data sources and the sessions replayed;
- the rule code apart from H1.

The DKW live-lag variant is reported, but the gate is decided on the base
replay.

## (c) The pass rule

**Do the models agree on the driver?** Decided per episode, before looking at
the cells.

- For each decomposition with values in the episode window — DKW (path share
  per (a)), Kim-Wright (path = 1 − premium share), ACM (path = 1 − premium
  share) — take the **median** of its 60-session share over the episode's
  sessions.
- Its side is `path` if the median path share is ≥ 0.60, `premium` if the
  median premium share is ≥ 0.60, and none otherwise.
- The episode is **agree** when every available decomposition names the same
  side. It is **disagree** when any names none or two name different sides. A
  single available decomposition agrees with itself.

**Per-episode pass**, on the modal cell among the episode's determined
sessions (not-determined sessions excluded):

- **agree** episodes pass only if the modal cell **is the set's expected
  cell**;
- **disagree** episodes pass if the modal cell is the expected cell **or
  `mixed`**;
- a tie for the mode passes only if every tied cell would pass. An episode
  with no determined session fails.

**Reported:** the number of agree episodes and how many pass; the number of
disagree episodes and how many pass.

**The gate passes if and only if all five episodes pass.** A pass restores
SR-6 to `ADOPTED — gate pending` → `ADOPTED — rights live` per §1.2, and SR-17
to `MERGED into rates.driver`. A fail leaves both `DEFERRED — gate failed` with
the new statistic.

## What had been seen when this was written

Disclosed, because a pre-registration is only as good as what it was blind to.

**Seen:**
- rerun 1's results at v1.11;
- its per-episode input medians, including `dkw path xl` — the path share
  under definition (a);
- the ex-liquidity sensitivity under rerun 1's modal-only rule: 1 of 5 at
  share_min 0.5, 0 of 5 at 0.6 and 0.7. That modal rule is not rule (c).

**Not seen:**
- any result under H1;
- any result under rule (c);
- any 20-session breakeven reading for any episode.
