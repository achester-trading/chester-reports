# Rates driver — calibration ledger (SR-6, SR-9, SR-17)

*Run 2026-09-30 by `tools/calibration/sr06_09_17_driver.py` against config `market-state-v1.11`. Dated; never edited — a rerun writes a new ledger.*

The rule calibrated is the market-state object's own: `regime.driver_cell` is imported and called on every session. Its inputs are rebuilt from the publishers' full histories on the definitions of the `calc.attr_*` series in `altdata/market_features.py` (a window of 60 of the denominator's own observations, same-day endpoints, no share below a 5 bp denominator). The observation store is not read.

## Data source and vintage

| Series | Source | From | To | n |
|---|---|---|---|---|
| DGS10 | FRED | 1962-01-02 | 2026-09-28 | 16,170 |
| DGS2 | FRED | 1976-06-01 | 2026-09-28 | 12,578 |
| DFII10 | FRED | 2003-01-02 | 2026-09-28 | 5,939 |
| THREEFYTP10 (Kim-Wright) | FRED (Board, re-estimated) | 1990-01-02 | 2026-09-25 | 9,170 |
| DKW | Federal Reserve Board CSV (re-estimated monthly) | 1983-01-03 | 2026-08-31 | 10,899 |
| ACM | NY Fed workbook, daily sheet (re-estimated) | 1961-06-14 | 2026-09-29 | 16,288 |
| SF Fed | FRBSF workbook, fitted term premium (weekly) | 1998-01-02 | 2026-09-28 | 7,174 |
| SPY | yfinance, adjusted | 1993-01-29 | 2026-09-30 | 8,475 |
| TLT | yfinance, adjusted | 2002-07-30 | 2026-09-30 | 6,082 |
| ^GSPC | yfinance | 1990-01-02 | 2026-09-30 | 9,254 |

Vintage: downloaded 2026-09-30. **The three model term premia (Kim-Wright, ACM, DKW) and SF Fed are today's re-estimates of the past, not what was knowable at the time** — no publisher keeps vintages of them. The ledger therefore measures whether the rule classifies the episodes as the models now describe them, which is a weaker claim than live performance. DKW's publication lag is modelled as a variant (read 21 sessions late); ACM's is not.

Before TLT (July 2002) the stock-bond correlation uses ^GSPC against a constant-maturity 10-year from DGS10 (carry less 8.5 x the yield change). DFII10 starts January 2003, so **1994 has no real/breakeven cut**: a path-side cell cannot be tested there, and the episode can only come out `term_premium`, `mixed` or not determined.

## Thresholds under test

| Threshold | Declared (v1.11) | Grid |
|---|---|---|
| `share_min` | 0.6 | 0.5, 0.6, 0.7 |
| `move_floor_bp` | 15 | 10, 15, 25 |
| `be_flat_bp` | 5 | — |
| `front_leading` | 1.0 | — |
| `front_anchored` | 0.5 | 0.4, 0.5, 0.6 |
| `sign_deadband_bp` | 5 | — |

## SR-6's episode sets and SR-17's four episodes

Gate (signal-triage order §9, ST-3): *the ledger reproduces SR-6's episode sets and SR-17's four episodes*. Scored here as: **the modal cell among the episode's determined sessions is the set's expected cell** — `fed_path` for bear flattening, `term_premium` for bear steepening.

| Episode | Set | Window | Sessions | Determined | Cells (base) | Modal | Expected share | Base | Live DKW lag | Grid (of 27) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1994 | bear flattening | 1994-02-04 → 1994-11-07 | 190 | 68 | not_determined 122, mixed 68 | mixed | 0% | FAIL | FAIL (mixed) | 0 |
| Q4 2018 | bear flattening | 2018-08-22 → 2018-11-08 | 55 | 33 | mixed 33, not_determined 22 | mixed | 0% | FAIL | FAIL (mixed) | 0 |
| 2022 | bear flattening | 2022-01-03 → 2022-10-21 | 202 | 166 | mixed 100, growth 59, not_determined 36, fed_path 7 | mixed | 4% | FAIL | FAIL (mixed) | 0 |
| 2013 | bear steepening | 2013-05-02 → 2013-09-05 | 88 | 72 | mixed 68, not_determined 16, growth 4 | mixed | 0% | FAIL | FAIL (mixed) | 0 |
| Aug-Oct 2023 | bear steepening | 2023-07-31 → 2023-10-19 | 57 | 57 | mixed 57 | mixed | 0% | FAIL | FAIL (mixed) | 0 |

- **1994** — Fed hikes from 3% to 5.5%; 10y 5.6% -> 8.0%, 2y faster.
- **Q4 2018** — the last leg of the 2015-18 cycle into the 3.24% peak.
- **2022** — the fastest hiking cycle since 1981; 2y leads, breakevens fall.
- **2013** — the taper tantrum: front end anchored at zero, long end reprices.
- **Aug-Oct 2023** — the refunding and term-premium selloff to 5%; Fed on hold.

**Base thresholds: 0 of 5 episodes pass.** Best grid point: share_min 0.5, move_floor_bp 10, front_anchored 0.4 — 0 of 5. Grid points passing all five: 0 of 27.

## Why the episodes fail

Each episode's inputs at their in-window medians. `dkw path` / `dkw prem` / `dkw liq` are the v1.11 shares of the model's whole real move; `dkw path xl` is path / (path + premium), the TIPS liquidity premium left out.

| Episode | Δ10y bp | real share | curve share | dkw path | dkw prem | dkw liq | dkw path xl | KW prem | ACM prem |
|---|---|---|---|---|---|---|---|---|---|
| 1994 | +48 | — | 1.31 | — | — | — | — | 0.29 | 0.15 |
| Q4 2018 | +19 | 0.94 | 1.05 | 0.44 | 0.24 | 0.30 | 0.63 | 0.28 | 0.67 |
| 2022 | +50 | 1.05 | 1.68 | 0.55 | 0.17 | 0.36 | 0.71 | 0.40 | 0.06 |
| 2013 | +67 | 1.22 | 0.15 | 0.22 | 0.31 | 0.47 | 0.41 | 0.59 | 0.96 |
| Aug-Oct 2023 | +61 | 0.80 | 0.74 | 0.43 | 0.46 | 0.13 | 0.49 | 0.49 | 0.70 |

What decided each session at the declared thresholds:

- **1994**: fed_path cannot be tested (107); the tie-breakers do not agree on a side at 0.60 (57); below the 15bp move floor (15); the models disagree on the sign of the term-premium change and the arbiter dkw has no sign to settle it (11)
- **Q4 2018**: neither share reaches 0.60 (33); below the 15bp move floor (22)
- **2022**: neither share reaches 0.60 (75); growth (59); below the 15bp move floor (36); the models disagree on the sign of the term-premium change and the arbiter dkw has no sign to settle it (23); fed_path (7); premium-driven, but no shape confirms a cell (2)
- **2013**: neither share reaches 0.60 (68); below the 15bp move floor (16); growth (4)
- **Aug-Oct 2023**: neither share reaches 0.60 (57)

### Sensitivity: DKW shares without the liquidity premium

The same rule with DKW's path and premium measured as shares of their own sum. **Not the object's definition** — reported because it isolates the one definitional choice the diagnosis points at.

| share_min | 1994 | Q4 2018 | 2022 | 2013 | Aug-Oct 2023 | Passing |
|---|---|---|---|---|---|---|
| 0.5 | mixed (0%) | growth (9%) | growth (27%) | term_premium (100%) | growth (33%) | 1 of 5 |
| 0.6 | mixed (0%) | growth (9%) | growth (27%) | mixed (7%) | mixed (2%) | 0 of 5 |
| 0.7 | mixed (0%) | mixed (3%) | mixed (16%) | mixed (0%) | mixed (0%) | 0 of 5 |

## SR-17: forward equity outcomes by cell inside its four episodes

Base rate only (SR-17 carries no rights). ^GSPC forward return from each session in the cell; overlapping windows, so the sessions are not independent draws.

| Episode | Cell | Sessions | Fwd 3m mean | Fwd 6m mean | Fwd 6m > 0 |
|---|---|---|---|---|---|
| Q4 2018 | mixed | 33 | -8% | 2% | 64% |
| Q4 2018 | not_determined | 22 | -7% | -1% | 14% |
| 2022 | fed_path | 7 | 0% | 2% | 86% |
| 2022 | growth | 59 | -9% | -11% | 7% |
| 2022 | mixed | 100 | -1% | -0% | 46% |
| 2022 | not_determined | 36 | -4% | -4% | 36% |
| 2013 | growth | 4 | 6% | 9% | 100% |
| 2013 | mixed | 68 | 5% | 10% | 100% |
| 2013 | not_determined | 16 | 1% | 9% | 100% |
| Aug-Oct 2023 | mixed | 57 | 4% | 16% | 100% |

## The full sample, 2003-06-01 to the last session

SR-9's correlation member by cell, and the forward S&P base rate by cell.

| Cell | Sessions | Share | Corr mean | Corr > 0 | Fwd 3m mean | Fwd 6m mean | Fwd 6m median | Fwd 6m > 0 |
|---|---|---|---|---|---|---|---|---|
| mixed | 2,253 | 39% | -0.19 | 31% | 2% | 5% | 6% | 74% |
| not_determined | 1,787 | 31% | -0.25 | 22% | 2% | 4% | 5% | 76% |
| growth | 1,302 | 22% | -0.25 | 21% | 3% | 6% | 8% | 78% |
| term_premium | 473 | 8% | -0.34 | 18% | 5% | 8% | 8% | 84% |
| fed_path | 21 | 0% | -0.17 | 48% | -1% | -4% | -0% | 48% |

By direction:

| Cell | rally | selloff |
|---|---|---|
| fed_path | 10 | 11 |
| growth | 662 | 640 |
| mixed | 1,010 | 1,243 |
| term_premium | 312 | 161 |

Among determined sessions, the side was decided by: dkw 4,049. The models disagreed on sign and DKW arbitrated on 21% of them.

## SR-6: the four models side by side, 2026-02-01 to 2026-09-30

60-observation term-premium change in bp (SF Fed: 12 weekly prints), at each month's last session in the history; the sign outside the 5 bp dead-band. DKW's last row is 31 Aug, so its September reading is August's carried forward -- which is what the live object would see.

| Month end | Δ10y | Kim-Wright | ACM | SF Fed | DKW (real) | Cell |
|---|---|---|---|---|---|---|
| 2026-02-27 | -12 | -2 (0) | -5 (0) | -16 (−) | -3 (0) | not_determined |
| 2026-03-31 | +11 | +7 (+) | -14 (−) | +2 (0) | +2 (0) | not_determined |
| 2026-04-30 | +11 | +7 (+) | -7 (−) | +7 (+) | +3 (0) | not_determined |
| 2026-05-29 | +32 | +22 (+) | +5 (0) | +2 (0) | +11 (+) | mixed |
| 2026-06-30 | +9 | +2 (0) | -16 (−) | -11 (−) | -1 (0) | not_determined |
| 2026-07-31 | +32 | +14 (+) | +13 (+) | +9 (+) | +9 (+) | mixed |
| 2026-08-31 | +28 | +11 (+) | +10 (+) | +3 (0) | +7 (+) | mixed |
| 2026-09-28 | +75 | +30 (+) | +20 (+) | -2 (0) | +7 (+) | mixed |

Sessions where at least one model has a sign: 162; all signed models agree on 69% of them. Where they disagree, the object lets DKW arbitrate (§2.1.1, SR-17); SR-6's own text named the curve decomposition as the arbiter, and the integration ruling replaced it with DKW.

## Verdict

- Base thresholds (v1.11): **0 of 5** episodes reproduce their set's cell.
- 1994: FAIL — modal mixed (0% of determined sessions fed_path); holds at 0 of 27 grid points.
- Q4 2018: FAIL — modal mixed (0% of determined sessions fed_path); holds at 0 of 27 grid points.
- 2022: FAIL — modal mixed (4% of determined sessions fed_path); holds at 0 of 27 grid points.
- 2013: FAIL — modal mixed (0% of determined sessions term_premium); holds at 0 of 27 grid points.
- Aug-Oct 2023: FAIL — modal mixed (0% of determined sessions term_premium); holds at 0 of 27 grid points.

## The session's reading (written 2026-09-30, beside the generated tables)

**The gate fails, and not for want of tuning.** None of the 27 grid points around
the declared thresholds reproduces a single episode. Two separate things cause it,
and neither is a threshold:

1. **A definitional defect in the DKW shares (ST-3's, not the order's).**
   `calc.attr_dkw_path_share_60d` and `_tp_share_60d` divide by the model's
   whole real-yield move, which includes the TIPS liquidity premium. That leg
   took 30-47% of the move in Q4 2018, 2022 and 2013, so neither path nor
   premium could reach 0.60 even when one clearly dominated the other: 2022's
   path share of the path-plus-premium move is 0.71, against 0.55 as defined.
   The driver's question is path against premium, and the liquidity premium is
   neither. Dividing by path + premium is the definition the question implies.
2. **Even with that fixed, the models do not describe these episodes the way
   SR-6's sets expect** (sensitivity table: 1 of 5 at best, and only at
   share_min 0.5).
   - **2022 and Q4 2018 are path-driven with breakevens roughly flat over 60
     sessions** (real share 1.05 and 0.94), which the rule calls `growth`, not
     `fed_path`. For 2022 all three decompositions agree on path (DKW 0.71 ex
     liquidity, KW 0.60, ACM 0.94), so its miss is the breakeven condition,
     not the models. Breakevens fell in 2022 H2 but rose in H1, and a
     60-session window sees mostly flat.
   - DKW reads **Aug-Oct 2023 as about half path, half premium** (0.49 ex
     liquidity). KW agrees (0.49); ACM calls it premium (0.70).
   - **2013** is premium-led ex liquidity only at 0.59, just under the line.
     ACM (0.96) and KW (0.59) agree on the direction.
   - **1994 cannot be scored on a path-side cell.** The tie-breakers mostly
     agree it was path-driven (at the median KW path 0.71, ACM 0.85; they
     disagree on 57 of 190 sessions), but with no DFII10 before 2003 the
     breakeven condition cannot be tested.

   Across 2003-2026 the rule reaches `fed_path` on 21 sessions in 23 years. The
   conjunction (path >= 0.60, breakevens against by > 5 bp, front end leading)
   almost never holds on 60-session windows.

**No threshold change is made.** A threshold chosen to pass five episodes would
be fitted to them. The declared v1.11 thresholds stay provisional, and the
driver publishes as built: `mixed` or not determined most of the time, with no
consumers until ST-6.

**What needs a ruling, not a session:**
- (a) Adopt path / (path + premium) for the DKW shares. That is a feature
  definition change (registry descriptions, group K, a method bump), and it
  needs a rerun of this study into a new dated ledger.
- (b) Whether `fed_path` should test breakevens and the front end over a
  shorter window than the 60-session decision window (the order's 1w / 1m
  cuts exist as `calc.attr_*_5d` / `_20d`).
- (c) Whether SR-6's episode sets are the right gate at all. For Aug-Oct 2023,
  DKW and KW read half path, half premium where the set says premium, and the
  2022 label rests on a breakeven fall that a 60-session window does not see.
  R5 already says no single model is fact.
- (d) The register: per `docs/ledgers/README.md` a failed gate sets the entry to
  `DEFERRED — gate failed`. SR-6 and SR-17 are left unchanged here pending (a)-(c).
