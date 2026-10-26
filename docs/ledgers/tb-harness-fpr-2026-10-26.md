# T&B harness ledger -- the continuous false-positive rate (6i-3)

**Pre-registered 26 Oct 2026, before the first run** (A79; the 6i brief's section 2.3 item 3, Part 23's deferred item 3: "the real false-positive-rate measurement; calibration is episode-level only"). This head was committed alone, ahead of the code that runs it. A run fills the Result section below the marker and never edits the head; `tools/validate_tb_harness_fpr.py` holds the hash printed here equal to `fpr_rule` in `config/tb_episodes.yaml`. A re-run against a later store is a new dated file with this head unchanged.

> The continuous false-positive rate (6i-3), pre-registered on 26 Oct 2026 before its first run. SESSIONS: every session on which the store holds an S&P 500 close (yfinance.mkt_gspc), from its first to its last. SCORING: each session is read through each of Part 23's three overlays as config/tb_episodes.yaml defines them (Concentration & Complacency, HY Spread Acceleration, Liquidity & Funding Stress), and through the credit leg's Baa proxy, every input read as of that session's close by available_at, exactly as the calibration reads a decision date. The Baa proxy is the HY Spread Acceleration overlay's four triggers read on Baa less the 10-year (calc.baa_less_10y, daily from DBAA; before DBAA exists, calc.baa_less_10y_m, monthly from BAA): at least +50% off its 12-month low, its 30-day change at least +40bp, its 30-day change at least +15bp, and its level at least 225bp, firing at three of four; the first three carry Part 23's HY and IG thresholds unchanged, the level is session-set because Part 23's IG at least 110bp has no Baa analogue. A reading is FIRED when the overlay's state is FIRES; CLEAR, UNREAD and NOT EXISTENT readings are counted and never enter the rate. EPISODES: an episode begins at its top, the three calibration tops and the tops of the extended set's eight post-1970 bears and five pre-1970 episodes; controls and near-misses begin no episode, because the calibration scores a fire before one as a false call. WINDOW: 365 calendar days forward. A fired reading on session d is a TRUE POSITIVE if an episode begins on a day t with d <= t <= d + 365 days, and a FALSE POSITIVE otherwise; a fired reading whose window runs past the store's last session and holds no episode start is CENSORED and enters neither count. STATISTIC: per overlay, false positives over true plus false positives, printed with n (that denominator), the scored sessions (FIRES or CLEAR), the censored count and the number of distinct firing runs (consecutive fired sessions). No threshold, window or episode is tuned on the result; a change is a new registration and a new dated ledger. Report-only: the rate enters no composite, the market-state object, a dial, a band or a packet.

| | |
|---|---|
| Window | 365 calendar days forward of each fired session |
| Rule | as quoted above |
| Rule SHA-256 | `5c82265bf1e760eec88ac89959686c38704aaac4f195bf336b1f7bb2ac2ace42` (over the whitespace-normalised text, as `altdata/tb_harness.py` hashes the pass rule) |
| Sessions | every stored S&P 500 close |
| Episodes | the tops of config/tb_episodes.yaml: calibration, extended bears, pre-1970 |
| Rights consequence | None. Report-only (the brief, 2.5); no composite is stored (decision 3). |

<!-- RESULT BELOW. The head above is pre-registered and never edited. -->

## Result

Not yet run.
