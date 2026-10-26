# Trend-signal breadth against what followed -- calibration ledger (Batch 16 item 89(b))

<!-- prereg:begin -->
## Pre-registration

*Written on 26 Oct 2026 by session B on branch `b76-trend-breadth` (B76), committed alone before the module that scores it. **The block between the two markers is never edited.** A change is a new registration in a new dated file; `tools/validate_trend_breadth.py` holds this block to the SHA-256 recorded in `config/trend_breadth.yaml` (`ledger.prereg_sha256`) and printed beneath it. The spec is signal-triage Batch 16 item 89(b), written as the triage chat's 82(b) in `docs/change-order-signal-triage-round-7-2026-10-26.md`, ruled 26 Oct 2026. Rights: none until Audit #5 or a sitting reads it.*

**One question.** When an unusually large share of the markets we hold are reversing their trend, are the S&P 500's and the Nasdaq-100's returns over the next 5 and 20 sessions different from other weeks?

**The signal** (declared, not fitted; `config/trend_breadth.yaml`, version trend-breadth-v1):
- On a market's session t, the sign at lookback L (20, 60, 120 and 250 sessions) is +1 when the close on t is above the mean of its last L closes (t included), -1 below, 0 equal. A rate is read as its yield, a currency pair as quoted; each market keeps its own sessions.
- The market's state on t is **trending** when all four signs agree and none is 0; **reversing** when the 20-session sign is non-zero, opposite the 250-session sign, and changed on one of the market's last five sessions (t included); **mixed** otherwise; **insufficient history** while any lookback lacks L closes.
- On a day D, a market **carries a state** when its latest close on or before D is at most 7 calendar days old and its state there is not "insufficient history".
- **The reversing share** on D is the markets reversing over the markets carrying a state, in percent.

**The markets:** the sixteen rows of `config/trend_breadth.yaml` (the order's fifteen and AUD/USD "if stored"), each read from the first of its declared stored keys that holds rows. A market with no stored key is not stored and leaves n.

**The sample.** The last S&P 500 session (`yfinance.mkt_gspc`) of each ISO week on which at least 5 markets carry a state. One observation per week, so no two outcomes at +5 overlap.

**The outcomes.** The percent change of the S&P 500 (`yfinance.mkt_gspc`) and of the Nasdaq-100 (read through QQQ, `yfinance.mkt_qqq`: no index key is stored) from D to the 5th and to the 20th of the outcome's own sessions after D. A week without the full horizon is out of that cell.

**The groups.** A week is **high** when the reversing share is at or above 20.0%, and **rest** otherwise. The threshold is declared here, not chosen from the sample.

## The test

- **The statistic:** the S&P 500's mean +20 change in high weeks less that in rest weeks, with Welch's t.
- **INSUFFICIENT** when either group holds fewer than 30 weeks.
- **PASS** when all three hold:
  1. each group holds at least 30 weeks;
  2. |t| is at least 2.0;
  3. the difference has the same sign in each half of the sample, split at the median week (the earlier half taking the odd week); a half where either group is empty fails this condition.
- **FAIL** otherwise.
- The three other cells (the S&P 500 at +5, the Nasdaq-100 at +5 and +20) are printed with the same columns and verdicts. They are descriptive and do not enter the rule.

## How it prints

Each edition prints its as-of, window and n (weeks), the markets held of those named and which are not stored, and for each cell n high, n rest, each group's mean, the difference, Welch's t, each half's difference and the verdict. The verdict prints as it is: INSUFFICIENT and FAIL are results.

## What this registration does not do

- **It grants nothing.** The signal is a report whatever the verdict. Nothing enters a composite, a flag or the market-state object. Entry to the Top & Bottom intake queue is a ruling after Audit #5 or a sitting reads this ledger (cross-item note 2: 89(b) first, then 81, then 89(a)).
- **No vendor value** is read anywhere in it.
<!-- prereg:end -->

**Pre-registration SHA-256** (the block above, markers included, LF bytes): `9347d6686bc2506dfbe37bb4d25e3d2c7a88e0fcd92527f961667498d34ea976`

*The numbers of the rule (20.0%, 30 weeks a side, |t| of 2.0, 5 markets) were set in `config/trend_breadth.yaml` before the module first ran; this block transcribes them unchanged. The laptop edition below is computed from the laptop's partial store (`python -m altdata.trend_breadth ledger --db PATH --label ...`, read-only), current vintages, so its window is short and its n is what that store holds: a first edition, not the box's.*

## Edition: laptop first edition

- **As of:** 26 Oct 2026 (laptop first edition)
- **Window:** 2023-04-21 to 2026-05-29
- **n:** 163 weeks; markets held 6 of 16 named (not stored: bund_10y, jgb_10y, sofr, es, nq, copper, oil, gold, dxy, audusd)

| Field | Value |
|---|---|
| Verdict | FAIL (the S&P 500 at +20, the rule's cell) |
| n | 163 weeks |

| Outcome | Horizon | n high | n rest | Mean high | Mean rest | Difference | Welch t | Halves | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| S&P 500 | +5 | 43 | 120 | +0.43 | +0.34 | +0.09 | +0.27 | +0.26 / -0.04 | FAIL |
| S&P 500 | +20 | 43 | 120 | +1.76 | +1.59 | +0.16 | +0.23 | +0.66 / -0.21 | FAIL (the rule) |
| Nasdaq-100 (QQQ; no index key is stored) | +5 | 43 | 120 | +0.57 | +0.49 | +0.08 | +0.17 | +0.66 / -0.42 | FAIL |
| Nasdaq-100 (QQQ; no index key is stored) | +20 | 43 | 120 | +2.74 | +2.16 | +0.57 | +0.57 | +1.66 / -0.38 | FAIL |

**Verdict (the pre-registered rule):** FAIL.

**Rights:** none.
