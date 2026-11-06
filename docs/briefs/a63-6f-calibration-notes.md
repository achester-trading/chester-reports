# A63: 6f tranche 2, calibration (session A)

**Branch-only, overnight. Nothing here merges before the 1 Nov Monthly.** Built under rulings 7a and 8a of D27 (`docs/briefs/rulings-2026-10-24.md`):

- 7a: "uncalibrated (n = k of 30)" prints until a row is calibrated, never an empty field.
- 8a: the ledger takes dial transition rows only, at three horizons, once a row is calibrated.

The method is the spec's section 3, `docs/briefs/6f-spec-draft-2026-10-24.md`.

## Base and commits

- **Base:** `a63-6f-calibration` from `origin/a62-6f-build` at `1309c81`, in the same worktree as A62 (`../chester-a57`).

| Commit | What |
|---|---|
| (this) | `altdata/state_calibration.py`, its hooks, `tools/validate_6f_calibration.py`, the gate line, these notes. |

## The method

`altdata/state_calibration.py`. It is not in regime's method hash: it reads stored objects and changes nothing the object says, so there is no method or config bump.

1. **The pairs.** For each dial (macro, vol, gamma), the published state at session t and at t + h, both READ from stored objects and never recomputed. The horizons are 5, 20 and 63 sessions (Books C, B and A), counted on the session calendar (`regime.session_days`). P(s′ | s, h) is the share of the pairs starting in s that end in s′: counted, not modelled.
2. **Point in time.** A read as of a cutoff uses only objects whose `available_at` is at or before it (the latest such vintage per session), and only objects under the current method version (method-11).
   - A pair needs its t + h object knowable at the cutoff too.
   - A pair across a session whose object is absent, a fault or not stored is skipped and counted (`_skipped`).
   - The cutoff is normalised to the store's own width (`observations.canonical_instant`). Without that, an object computed at the cutoff instant compared as later than it, which the gate caught.
3. **The sample.** A row is calibrated when its state has at least 30 INDEPENDENT starts: start sessions at least h apart, taken greedily from the earliest. Below that it prints the literal `uncalibrated (n = k of 30)`. With no current state it prints `no current state; uncalibrated (n = 0 of 30)`: never a number, never empty.
4. **The calibrated row.** Each state's count plus one half, over the row's pairs plus half the number of states (add-half smoothing). No state is 0 or 1, which the ledger refuses, and the row still sums to 1.
5. **The backfilled history,** as section 3.3 allows: objects computed as of their own session, under the current method. Bands are not fitted, and a band moved after reading the scores is a new pre-registration.

**Where it prints:**
- **The daily close:** one line in the mechanics section ("Dial transitions -- macro (state): 5s …; 20s …; 63s … | vol … | gamma …").
- **The Weekly:** the table, dial × horizon, nine rows.
- **The Monthly:** the table, plus the dimensions' table, **unledgered** (8a): k per dimension and horizon, or the probabilities once calibrated.

**The ledger** (`write_ledger`, called by the close after it stores the object). Dial rows only, and only once a row is calibrated. Each calibrated row writes one binary row per state:

| Field | Value |
|---|---|
| source | `market_state` |
| scenario_set | `state:<dial>:<h>s:<session>` |
| claim | `the <dial> dial is <state> at <horizon date>` |
| resolution criterion | `the published state of the <dial> dial on the market_state object for <horizon date>, latest vintage` |
| emitted_by | `regime:<method>` |

`resolve_due` resolves each due row against the stored object for its horizon date. The existing tooling scores it (`ProbabilityLedger.resolve`, Brier per row, `score_by_source`). The ledger is the probability ledger, not the decision register. The object reads the ledger only for its `tail:` prefix, so these `state:` rows cannot feed back into it.

## Every session-set value, with its reason

| Value | Set to | Reason |
|---|---|---|
| The minimum | 30 independent starts | the spec (3.2), ruled 7a |
| Independence | starts at least h sessions apart, greedy from the earliest | the spec's definition, and deterministic, so a replay counts the same |
| Smoothing | add one half per state | keeps every probability inside (0, 1) and the set summing to 1 for `coherence()` |
| The states counted | the dial's declared states plus any state its pairs reached | a state the config declares but the history never reached still gets its half count |
| The current object for a read | `regime.latest(as_of)` | the one reader every report uses |

## Where the spec and the code differ

1. **Clipping.** The spec's section 3.4 says the probability is "clipped to (0.01, 0.99)". Clipping would break a set's sum to 1, and the ledger's `coherence()` would then flag every set, so the probabilities are add-half smoothed instead. The aim is the same (no certainty) and the set stays coherent.
2. **Dimensions' rows.** The spec's 3.4 had dimensions' matrices "printed but not ledgered"; that is what is built (8a).
3. **The close.** The close writes the ledger after it stores the object, in `daily_cascade/close_report.py`. A failure is printed and the report continues, as the object's own compute is.

## k per dial and horizon

**On the laptop's store:** k = 0 for every dial and horizon. The store (`data/chester.db`, 20 KB) holds no stored objects, so every read is `no current state; uncalibrated (n = 0 of 30)`.

**On the gate's fixtures** (`tools/validate_6f_calibration.py`, 15 checks):

| Fixture | Read |
|---|---|
| 60 sessions | macro at 5 sessions: `uncalibrated (n = 11 of 30)` (starts 0, 5, …, 50); 63 sessions: `uncalibrated (n = 0 of 30)` |
| 400 sessions (10-session blocks) | macro at 5 sessions: 40 independent starts, calibrated, P(expansion) = (100 + 0.5) / (200 + 0.5 × 9) = 0.4914, by hand |

## The gate

**`tools/validate_6f_calibration.py`**, groups A–D:
- A: point in time. No object computed after the cutoff, no pair whose t + h object is unknowable, no later vintage early, no other method.
- B: the n-of-30 rendering, and the probabilities by hand.
- C: no ledger row before calibration; dial rows only, coherent, resolved and scored.
- D: where it prints, and that it never recomputes an object.

It is registered in the Makefile after `validate_regime`, and CLAUDE.md's line is recounted on this base: **138 code gates (135 Python, three shell)**, from 137 (134, 3). `config/catalogue_commands.yaml` names the new module (`validate_audit_3a`).

**Local runs:** validate_6f_calibration 15/0, validate_regime 516/0, validate_audit_3a 88/0, check_registry OK, check_library 0 failures. The report gates (`validate_stack`, `validate_weekly_complete`, `validate_monthly`) were killed mid-run when Windows ran low on memory, so per the brief they were not retried locally: CI is their validate (below).

| CI run | On | Result |
|---|---|---|
| 40118726042 | 182b9d35 (the build, before the a62 merge) | failure (superseded by the next) |
| 40119503077 | 02f89b0d | failure: `validate_monthly_stack`, `validate_crypto_basket`, `validate_correlation_layer`, all `KeyError: 'not_tracked'` in `monthly_macro/stack.py` `slow_layers`. The calibration sub-sections were appended last and carried no `not_tracked` list, which the slow layers append their faults to. Mine. |
| A64 round (read once after the push) | aeea2bd2: every `state_v2_block` sub-section carries `not_tracked: []` | crypto_basket 93/0, correlation_layer 75/0, 6f_calibration 15/0, regime 516/0 locally; `validate_monthly_stack` left to CI |

## The box's first calibration read (a dry run; the operator's, after the merge)

```
cd ~/chester-reports
.venv/bin/python -m altdata.state_calibration show          # read-only: k per dial and horizon
.venv/bin/python -m altdata.state_calibration show --as-of 2026-10-30T21:30:00+00:00
```

It reads the stored objects under method-11, so it reads nothing until A62's re-backfill has run (A62's box commands). Until a row has 30 independent starts, the close writes no ledger row. That will take years for the 63-session rows, and depends on how far ALFRED's as-of history reaches (A62's tranche-0 check).

## Needs you (at most five; yes or no each)

1. **Add-half smoothing in place of the spec's clipping,** so every set stays coherent? Yes / no.
2. **The close writes the calibrated dial rows and resolves the due ones each evening** (none until a row is calibrated)? Yes / no.
3. **The dimensions' transition table in the Monthly, unledgered** (8a)? Yes / no.
4. **The first calibration read on the box after A62's re-backfill,** read-only (above)? Yes / no.
