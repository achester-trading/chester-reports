# GEX / DEX scale against FlashAlpha — 30 Sep 2026 SPY (read-only diagnostic)

*Run 2026-09-30 by `tools/gex_scale_diagnostic.py` on a local copy of the box's
stored chain `data/chains/2026-09-30/SPY_201420Z.csv`, captured 16:14 ET. Nothing
was written to any store. Dated; never edited.*

**The question.** Our 30 Sep SPY close printed $γ/1% **−9.92bn** and DEX
**+199bn**. FlashAlpha Basic printed **≈ −$1.0bn per 1%** (1.3M shares) and DEX
**+33.7bn** at 10:01 ET. The gaps are 9.9× and 5.9×, in the same direction. Sign,
regime, flip (768.92 vs 767.79) and max pain (760) all agree.

## Verdict: not a units fault. GEX is a definition difference; DEX is undetermined, most likely coverage.

- **The pipeline is clean.**
  - The stored chain reproduces the printed figures exactly: −9,924,651,374 and
    +199,073,618,408.
  - No duplicate rows; total OI 18.85M contracts.
  - ×100 (`CONTRACT_MULTIPLIER`) is applied once.
  - S appears twice in $/1%, and does so by definition: once in the delta change
    per 1% (S × 0.01), and once to turn shares into dollars.
  - Low-IV rows carry 0.0% of the gamma mass, and the largest single row is 1.5%
    of it.
- **GEX — a definition difference.** FlashAlpha documents its GEX as
  **Σ sign × Γ × OI × 100 × S** and labels it "per 1% move"
  ([flashalpha.com/concepts/gex](https://flashalpha.com/concepts/gex)). The
  standard per-1% figure, and this repo's, is Σ sign × Γ × OI × 100 × **S² × 0.01**.
  - The two differ by S × 0.01 = **7.62×** at spot 762.48.
  - FlashAlpha's quantity is this repo's `net_gex`: **−1.30bn** with 0DTE excluded,
    as the box computes a settled capture, and **−0.79bn** with 0DTE alive.
    FlashAlpha's −1.0bn sits between the two. That is consistent with their 10:01
    ET capture, when 0DTE still had six hours of life; ours was settled.
  - The residual 1.3× is coverage and timing.
- **DEX — undetermined.** DEX has no per-1% factor, so the definition above does
  not reach it.
  - Under our convention (dealers long calls, short puts), DEX accumulated to
    **≤ 14 DTE is $32.6bn**, against FlashAlpha's $33.7bn. All expiries give $209bn.
  - That points to a front-weighted coverage window on their side, but their DEX
    window and convention are not documented in what was checked, so it is not
    settled.

## The table

| Subset | $/1% (ours: Σ sign·Γ·OI·100·S²·0.01) | shares/1% | Σ sign·Γ·OI·100·S (FlashAlpha's GEX) | DEX $ |
|---|---|---|---|---|
| All expiries (0DTE incl., t floored 1h) | −6,009,319,878 | −7,881,282 | −788,128,217 | 209,117,553,349 |
| **All, 0DTE excluded — what the box prints** | **−9,924,651,374** | **−13,016,278** | **−1,301,627,797** | **199,073,618,408** |
| ≤ 45 DTE | −5,025,826,739 | −6,591,421 | −659,142,124 | 74,967,984,717 |
| ≤ 7 DTE | +1,042,426,639 | +1,367,153 | +136,715,280 | 23,447,220,058 |
| 0DTE only (t floored 1h) | +3,915,331,496 | +5,134,996 | +513,499,580 | 10,043,934,941 |
| FlashAlpha Basic, 10:01 ET | ≈ −1.0bn (labelled per 1%) | ≈ −1.3M | — | 33.7bn |

DEX in $bn, cumulative by DTE cutoff:

| Convention | ≤0 | ≤1 | ≤2 | ≤7 | ≤14 | ≤21 | ≤30 | ≤45 | ≤60 | ≤90 | all |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dealer +calls / −puts (ours) | 10.0 | 13.1 | 20.0 | 23.4 | **32.6** | 57.5 | 74.5 | 75.0 | 89.9 | 124.9 | 209.1 |
| raw net Σ Δ·OI | 1.0 | 0.3 | −1.4 | −2.8 | −4.9 | −11.8 | −15.4 | −15.6 | −19.2 | −5.0 | 17.1 |
| calls only | 5.5 | 6.7 | 9.3 | 10.3 | 13.8 | 22.8 | 29.5 | 29.7 | 35.4 | 59.9 | 113.1 |

## What follows (operator's ruling, not done here)

- No units fix is warranted: changing ours to FlashAlpha's definition would make
  "per 1%" untrue. Every stored percentile stays as it is.
- The FlashAlpha cross-check should compare FlashAlpha's GEX with our `net_gex`,
  not with `dollar_gamma_per_1pct`. Their DEX should be compared on a stated DTE
  window, and keep its "definition unreconciled" flag until a same-time capture
  (≈ 10:00 ET, 0DTE alive) and their DEX definition settle the window.
