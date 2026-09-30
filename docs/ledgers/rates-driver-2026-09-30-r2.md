# Rates driver — calibration ledger, rerun 2 (SR-6, SR-9, SR-17)

*Run 2026-09-30 by `tools/calibration/sr06_09_17_driver.py` against config `market-state-v1.12`. Judged against the pre-registration [rates-driver-2026-09-30-r2-preregistration.md](rates-driver-2026-09-30-r2-preregistration.md), committed before this rerun's code. Dated; never edited.*

## Verdict: the gate FAILS

- **2 of 5** episodes pass under the pre-registered rule (c); the gate needs all five.
- Models **agree** on the driver in 2 episode(s): **0 pass** (the modal cell must be the expected one).
- Models **disagree** in 3 episode(s): **2 pass** (the expected cell or `mixed` counts).
- Robustness only, not the verdict: 0 of 27 grid points pass all five.

## What changed since rerun 1 — as pre-registered, and one disclosure

- **(a)** DKW's shares are of path + premium; the TIPS liquidity premium is out of the denominator.
- **(b) H1**: `fed_path` tests breakevens over 20 sessions, signed to the 60-session move. `growth` keeps the 60-session breakevens. Thresholds are v1.11's, unchanged.
- **(c)** The pass rule below.
- **Disclosed, beyond H1's letter** (commit 12f4fdd): a rule with a condition *known false* now fails even when another of its inputs is absent. Before H1 all of a rule's conditions read one window, so this could not arise. With every input present, outcomes are unchanged.

## SR-6's episode sets under rule (c)

Agreement is per episode: each available decomposition's **median** 60-session path share over the window names a side (`path` ≥ share_min, `premium` when 1 − path ≥ share_min, else none). Agree means every available decomposition names the same side.

| Episode | Set | Expected | DKW / KW / ACM median path share | Sides | Agree | Determined / sessions | Cells | Modal | Passing cells | Base | Live DKW lag | Grid (of 27) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1994 | bear flattening | fed_path | 0.70 / 0.71 / 0.85 | dkw path, kw path, acm path | yes | 29 / 190 | not_determined 161, mixed 29 | mixed | fed_path | FAIL | FAIL (mixed) | 0 |
| Q4 2018 | bear flattening | fed_path | 0.63 / 0.72 / 0.33 | dkw path, kw path, acm premium | no | 31 / 55 | not_determined 24, growth 20, mixed 7, fed_path 4 | growth | fed_path, mixed | FAIL | PASS (mixed) | 9 |
| 2022 | bear flattening | fed_path | 0.71 / 0.60 / 0.94 | dkw path, kw path, acm path | yes | 156 / 202 | mixed 61, growth 56, not_determined 46, fed_path 37, term_premium 2 | mixed | fed_path | FAIL | FAIL (mixed) | 9 |
| 2013 | bear steepening | term_premium | 0.41 / 0.41 / 0.04 | dkw none, kw none, acm premium | no | 72 / 88 | mixed 67, not_determined 16, term_premium 5 | mixed | mixed, term_premium | PASS | PASS (mixed) | 27 |
| Aug-Oct 2023 | bear steepening | term_premium | 0.49 / 0.51 / 0.30 | dkw none, kw none, acm premium | no | 55 / 57 | mixed 49, growth 5, not_determined 2, term_premium 1 | mixed | mixed, term_premium | PASS | PASS (mixed) | 21 |

- **1994** (1994-02-04 → 1994-11-07) — Fed hikes from 3% to 5.5%; 10y 5.6% -> 8.0%, 2y faster.
- **Q4 2018** (2018-08-22 → 2018-11-08) — the last leg of the 2015-18 cycle into the 3.24% peak.
- **2022** (2022-01-03 → 2022-10-21) — the fastest hiking cycle since 1981; 2y leads, breakevens fall.
- **2013** (2013-05-02 → 2013-09-05) — the taper tantrum: front end anchored at zero, long end reprices.
- **Aug-Oct 2023** (2023-07-31 → 2023-10-19) — the refunding and term-premium selloff to 5%; Fed on hold.

## Inside each episode

Medians over the window. `be 60` / `be 20` are breakevens' change, in bp, signed to the 60-session move (negative = against it; H1 reads `be 20`). `dkw liq` is the liquidity leg's share of the whole real move, now outside the denominator.

| Episode | Δ10y | be 60 | be 20 | curve share | dkw path | dkw prem | dkw liq | be 20 against, % of sessions |
|---|---|---|---|---|---|---|---|---|
| 1994 | +48 | — | — | 1.31 | 0.70 | 0.30 | — | — |
| Q4 2018 | +19 | +1 | +3 | 1.05 | 0.63 | 0.37 | 0.30 | 11% |
| 2022 | +50 | -4 | -2 | 1.68 | 0.71 | 0.29 | 0.36 | 44% |
| 2013 | +67 | -18 | -7 | 0.15 | 0.41 | 0.59 | 0.47 | 56% |
| Aug-Oct 2023 | +61 | +12 | +3 | 0.74 | 0.49 | 0.51 | 0.13 | 12% |

What decided each session:

- **1994**: fed_path cannot be tested (145); neither share reaches 0.60 (16); below the 15bp move floor (15); the models disagree on the sign of the term-premium change and the arbiter dkw has no sign to settle it (11); premium-driven, but no shape confirms a cell (2); growth cannot be tested (1)
- **Q4 2018**: below the 15bp move floor (22); growth (20); neither share reaches 0.60 (6); fed_path (4); fed_path cannot be tested (2); path-driven, but no shape confirms a cell (1)
- **2022**: growth (56); fed_path (37); below the 15bp move floor (36); path-driven, but no shape confirms a cell (25); the models disagree on the sign of the term-premium change and the arbiter dkw has no sign to settle it (23); fed_path cannot be tested (10); premium-driven, but no shape confirms a cell (7); neither share reaches 0.60 (6); term_premium (2)
- **2013**: neither share reaches 0.60 (67); below the 15bp move floor (16); term_premium (5)
- **Aug-Oct 2023**: neither share reaches 0.60 (49); growth (5); fed_path cannot be tested (2); term_premium (1)

## Data source and vintage

| Series | From | To | n |
|---|---|---|---|
| DGS10 | 1962-01-02 | 2026-09-28 | 16,170 |
| DGS2 | 1976-06-01 | 2026-09-28 | 12,578 |
| DFII10 | 2003-01-02 | 2026-09-28 | 5,939 |
| THREEFYTP10 (Kim-Wright) | 1990-01-02 | 2026-09-25 | 9,170 |
| DKW | 1983-01-03 | 2026-08-31 | 10,899 |
| ACM | 1961-06-14 | 2026-09-29 | 16,288 |
| SF Fed | 1998-01-02 | 2026-09-28 | 7,174 |
| SPY | 1993-01-29 | 2026-09-30 | 8,475 |
| TLT | 2002-07-30 | 2026-09-30 | 6,082 |
| ^GSPC | 1990-01-02 | 2026-09-30 | 9,254 |

Downloaded 2026-09-30; the publishers' own files, parsed by the feeds' parsers. **Model term premia are today's re-estimates of the past**, not what was knowable then. DFII10 starts January 2003, so 1994 cannot test a path-side cell. Before TLT (July 2002) the correlation uses ^GSPC against a constant-maturity 10-year (carry less 8.5 × Δyield).

## SR-17: forward equity outcomes by cell inside its four episodes

Base rate only. ^GSPC forward returns; overlapping windows.

| Episode | Cell | Sessions | Fwd 3m mean | Fwd 6m mean | Fwd 6m > 0 |
|---|---|---|---|---|---|
| Q4 2018 | fed_path | 4 | -2% | 7% | 100% |
| Q4 2018 | growth | 20 | -10% | 1% | 45% |
| Q4 2018 | mixed | 7 | -6% | 3% | 86% |
| Q4 2018 | not_determined | 24 | -7% | -1% | 21% |
| 2022 | fed_path | 37 | 1% | 2% | 62% |
| 2022 | growth | 56 | -7% | -9% | 12% |
| 2022 | mixed | 61 | -3% | -3% | 34% |
| 2022 | not_determined | 46 | -3% | -4% | 37% |
| 2022 | term_premium | 2 | -6% | -0% | 50% |
| 2013 | mixed | 67 | 5% | 10% | 100% |
| 2013 | not_determined | 16 | 1% | 9% | 100% |
| 2013 | term_premium | 5 | 1% | 10% | 100% |
| Aug-Oct 2023 | growth | 5 | -6% | 9% | 100% |
| Aug-Oct 2023 | mixed | 49 | 6% | 16% | 100% |
| Aug-Oct 2023 | not_determined | 2 | -3% | 11% | 100% |
| Aug-Oct 2023 | term_premium | 1 | 11% | 22% | 100% |

## The full sample, 2003-06-01 to the last session

| Cell | Sessions | Share | Corr mean | Corr > 0 | Fwd 3m mean | Fwd 6m mean | Fwd 6m median | Fwd 6m > 0 |
|---|---|---|---|---|---|---|---|---|
| mixed | 2,278 | 39% | -0.22 | 30% | 3% | 6% | 7% | 76% |
| not_determined | 1,931 | 33% | -0.25 | 22% | 2% | 4% | 5% | 76% |
| term_premium | 927 | 16% | -0.31 | 18% | 5% | 8% | 8% | 86% |
| growth | 528 | 9% | -0.18 | 24% | 0% | 2% | 4% | 63% |
| fed_path | 172 | 3% | -0.13 | 34% | 1% | 2% | 2% | 61% |

| Cell | rally | selloff |
|---|---|---|
| fed_path | 60 | 112 |
| growth | 227 | 301 |
| mixed | 1,137 | 1,141 |
| not_determined | 63 | 81 |
| term_premium | 507 | 420 |

The models disagreed on sign and DKW arbitrated on 21% of determined sessions.

## SR-6: the four models side by side, 2026-02-01 to 2026-09-30

60-observation term-premium change in bp (SF Fed: 12 weekly prints) at each month's last session; sign outside the 5 bp dead-band. DKW's last row is 31 Aug, so September carries August forward, as the live object would.

| Month end | Δ10y | Kim-Wright | ACM | SF Fed | DKW (real) | Cell |
|---|---|---|---|---|---|---|
| 2026-02-27 | -12 | -2 (0) | -5 (0) | -16 (−) | -3 (0) | not_determined |
| 2026-03-31 | +11 | +7 (+) | -14 (−) | +2 (0) | +2 (0) | not_determined |
| 2026-04-30 | +11 | +7 (+) | -7 (−) | +7 (+) | +3 (0) | not_determined |
| 2026-05-29 | +32 | +22 (+) | +5 (0) | +2 (0) | +11 (+) | mixed |
| 2026-06-30 | +9 | +2 (0) | -16 (−) | -11 (−) | -1 (0) | not_determined |
| 2026-07-31 | +32 | +14 (+) | +13 (+) | +9 (+) | +9 (+) | mixed |
| 2026-08-31 | +28 | +11 (+) | +10 (+) | +3 (0) | +7 (+) | not_determined |
| 2026-09-28 | +75 | +30 (+) | +20 (+) | -2 (0) | +7 (+) | growth |

## The session's reading (written 2026-09-30, beside the generated tables)

**The gate fails again: 2 of 5.** Agree episodes: 0 of 2 pass. Disagree
episodes: 2 of 3 pass. Judged strictly by the pre-registered rule. Nothing
below re-reads it.

- **1994 (agree: path; FAIL).** All three decompositions say path (DKW 0.70,
  KW 0.71, ACM 0.85). With no DFII10 before 2003, neither path-side cell can be
  tested, so 161 of 190 sessions are not determined. The 29 determined sessions
  are all `mixed` (16 of them "neither share reaches 0.60"). **Under this rule
  and this data, 1994 cannot pass.** The pre-registration said a path cell could
  not be tested there. It did not say what that means for an agree episode. The
  ledger records the consequence and does not reinterpret the rule.
- **2022 (agree: path; FAIL).** H1 moved `fed_path` from 7 sessions (rerun 1)
  to 37, but `mixed` (61) and `growth` (56) still lead. 20-session breakevens ran
  against the move on 44% of the episode's sessions. Of the `mixed` sessions, 23
  are sign disagreements DKW could not settle and 25 are path-driven sessions
  where no shape rule held.
- **Q4 2018 (disagree: ACM says premium; FAIL).** The modal cell is `growth`
  (20 of 31 determined sessions): breakevens rose over both windows. Neither
  `fed_path` nor `mixed`, so it fails.
- **2013 and Aug–Oct 2023 (disagree; PASS).** Both pass **by abstaining**: modal
  `mixed`, with `term_premium` on 5 and 1 sessions. Only ACM calls either
  premium-driven; DKW and Kim-Wright put both near half and half. Rule (c) counts
  that as a pass, and the rule is what was pre-registered. The rule never
  identified a bear steepening as `term_premium`.

**No threshold change.** 0 of 27 grid points pass all five, and choosing one
would be fitting.

**Disclosed: a bug found and fixed before this ledger was written.** The first
draft of rerun 2's script dropped DKW rows without a TIPS liquidity premium
(the column starts in 1999). Definition (a) no longer uses that column, and the
feature itself (`market_features`) never required it. So the draft silently
removed DKW from 1994. The fix restored DKW for 1994; the verdict (2 of 5,
the same episodes) did not change. The object's code was not involved.

**Register:** SR-6 and SR-17 stay `DEFERRED — gate failed`, with this ledger's
statistic.
