# B133: item 124a, the two-sided tail table in Base Rates' dated appendix (6 Nov 2026)

Paste B133 (`docs/pastes/B133.md`). Batch 23 item 124a (the order's 106a), on
`origin/b129-five-filings`
(`docs/change-order-signal-triage-batch-23-2026-11-06.md`), and the study's
figures in `docs/studies/tail-days-2016-2026-data.md`, Parts 2, 4 and 5, on
`origin/study/tail-days` at `2380a145`.

**The base.** `origin/main` at `ee04ba21`. `library-xx-tail-table` is a new
branch from it. `origin/study/tail-days` exists, at `2380a145`.

## What was built

1. **`tools/calibration/tail_days_base_rates.py`**, the recompute. A study tool,
   not a gate.
   - It has two sources:
     - `--source store`, the box's: `yfinance.mkt_gspc` and `fred.vix`, read
       through `altdata.ledgers.sources`;
     - `--source public`, the laptop's: ^GSPC through the yfinance writer's
       reader, and VIXCLS from FRED's public graph CSV.
   - Its computation is printed at the head of its output, with its SHA-256
     `eb3c1f924c0192f1ffb3a7667856cbfd99d4e0455450f70be4836ba86dcda3ed`.
   - It writes nothing but stdout, or the `--out` file.
   - The laptop's store holds neither key, so this edition is the public run
     `--source public --through 2026-11-05`.
2. **Base Rates (XX), `docs/whitepapers/base-rates-whitepaper.md`**:
   - a new `## Appendix E — Dated: Two-sided tail base rates (item 124a) (as of 5 November 2026)`;
   - one table, with its as-of, its sample and the ruled sentence;
   - the standardised columns lead (GARCH, then RV20, then raw);
   - nothing in the body. The HTML edition was rebuilt.
3. **The narrative register**: `dont_miss_best_days`, added under
   `config/narratives.yaml` `proposals:`, the committed-proposal seed path.
   - It enters PROPOSED at the next `seed`, carrying the study's rebuttal in its
     direction.
   - Confirm or reject is the operator's.
   - `tools/validate_narratives.py`'s count of committed proposals goes from 7
     to 8. That is the only edit to the gate.

## The headline figures (as of 5 Nov 2026)

| Row | GARCH | RV20 | Raw | Any day |
|---|---|---|---|---|
| P(top-decile day within 5 \| bottom-decile day) | 49.7% | 51.6% | 62.8% | 41.9% / 41.3% / 37.6% |
| Clustering against the shuffled mean | 60.3% vs 65.1% | 60.8% vs 65.2% | 72.6% vs 65.1% | |
| Forward 20 sessions after a bottom-decile day, mean | +0.11σ | +0.13σ | +0.93% | +0.15σ / +0.17σ / +0.69% |
| Forward 20 sessions, 10th percentile | −1.37σ | −1.60σ | −5.90% | −1.23σ / −1.33σ / −4.37% |
| VIX at T-1: below 20 / 20–30 / 30–45 / 45 and above, P(top ≤ 5), raw | | | 56.3 / 79.5 / 89.7 / 95.7% | 45.6% from 1990 |

The openers: 6 of 93 bottom-1% days since 1990. 5 Nov 2026 (−4.36%) is the only
one at −4% or worse, and its next-session and five-session outcomes are pending.

## Against the study's figures

**No differences beyond rounding.** The recompute reproduces:
- Part 2.1's raw follow-through;
- Part 2.3's VIX-bucket rows, on the 1950 sample's deciles as the study defines
  them: n 428, 493, 156 and 46, at 56.3%, 79.5%, 89.7% and 95.7%;
- every row of Part 4.1, 4.2 and 4.3, the latest GARCH fit included
  (ω 0.0119, α 0.0937, β 0.8954);
- Part 5's six openers, with their dates, returns, VIX at T-1 and outcomes.

The appendix adds two kinds of row that are not in the study: the VIX buckets on
GARCH-z deciles (56.8%, 59.0%, 67.2% and 73.3%; n 548, 310, 64 and 15), and the
"any day from 1990" baselines (44.4% GARCH, 45.6% raw). They are the recompute's.

**One naming difference.** The study's Part 2.3 prints n = 429 for VIX below 20 at
h = 1 and 428 in its P(top) table, because the one-session window drops one fewer
day. The appendix carries 428, the five-session n.

## The gates

| Gate | Result |
|---|---|
| `check_library` | 27 papers, 0 failures, 0 warnings |
| `validate_narratives` (the register's gate; it is not in the Makefile's list under that name, so it was run directly) | 103 passed, 0 failed |
| `check_registry` | OK |

The guide's word total for Base Rates is unchanged: it is L-4's.

## CI

Read once after the push.

**B142.** CI run 42324183860 was red on `validate_batch14_b2`: "the proposals
pin is seven". The pin is now eight (this branch's `dont_miss_best_days`); chain-13's
stitch sets it to ten.
