# A79 notes: 6i tranches 6i-3 and 6i-4

**Session A, 26 Oct 2026, branch `a79-6i-tranches-3-4`.** The paste is `docs/pastes/A79.md`. The rulings are those of 25 Oct 2026 on `docs/briefs/6i-spec-draft-2026-10-25.md`: decision 6 (both credit proxies side by side) and decision 3 (no stored composite).

**Base:** `origin/a77-6i-tranches-1-2-5` at `4229e77e`.

Code and config only, branch-only. This branch merges after the 1 Nov Monthly. No box, no units, no `.env`, no register write.

**Commits, in order:**
1. `675f469e`: the paste.
2. `ad123908`: the FPR pre-registration, committed alone before any code ran: the ledger head and its CSV header.
3. `118f41d7`: 6i-3.
4. The 6i-4 commit, which also carries the gate, these notes and the counts.

---

## The FPR rule and its hash

The rule is quoted in full at the head of `docs/ledgers/tb-harness-fpr-2026-10-26.md` and as `fpr_rule` in `config/tb_episodes.yaml`.

**SHA-256:** `5c82265bf1e760eec88ac89959686c38704aaac4f195bf336b1f7bb2ac2ace42`. It is taken over the whitespace-normalised text, the same way A77 hashes its pass rule.

In short:
- **Sessions:** every stored S&P 500 close is scored through the three overlays and through the Baa proxy, each input read as of that session's close.
- **Episodes:** an episode begins at a top. That means the 3 calibration tops, the 8 extended bears and the 5 pre-1970 episodes, 13 distinct dates after de-duplication. Controls and near-misses begin no episode.
- **Window:** 365 calendar days forward.
  - A fire with a top inside the window is a true positive.
  - A fire with no top inside it is a false positive.
  - A fire whose window runs past the last session with no top in it is censored.
- **The rate:** false positives over true plus false positives. It is printed with n, the scored sessions, the censored count and the number of firing runs.

**How the ledger is written.** The run fills the Result section below a marker and never edits the head. A later run writes a new dated file, copying this head verbatim. `tools/validate_tb_harness_fpr.py` holds the config's hash equal to the hash at the head.

## The two series' registry lines

**`altdata/config.py`, `FRED_6I3_SERIES`**, which is part of `FRED_PULL_SERIES`:

```
SeriesSpec("dbaa", "DBAA", "Moody's Seasoned Baa Corporate Bond Yield, daily", "6", "%", "daily"),
SeriesSpec("baa",  "BAA",  "Moody's Seasoned Baa Corporate Bond Yield, monthly average", "6", "%", "monthly"),
```

**`metrics_registry.yaml`:**
- **Block `fred_6i3`:** members `fred.dbaa` and `fred.baa`, family `rate`, revised through ALFRED, `trigger_eligible: false`.
- **Metrics `calc.baa_less_10y`:** daily, bps. Inputs: `fred.dbaa` and `fred.yield_10y`.
- **Metrics `calc.baa_less_10y_m`:** monthly, bps. Inputs: `fred.baa` and `fred.yield_10y`.
- **`series_kinds`:** the two calc keys are `spread`; the two FRED keys are `yield`.
- **`market_state_barred`:** all four keys, under the order "the 6i brief's decision 6".

**`config/publication_lags.yaml` (the lag family).** Both families sit before the FRED catch-alls:
- **`fred_moodys_daily`:** DBAA and `calc.baa_less_10y`, 2 sessions, max 3.
- **`fred_moodys_monthly`:** BAA and `calc.baa_less_10y_m`, 12 sessions, max 14.

**How the two spreads are computed** (`altdata/market_features.py`, among the macro features):
- **The daily** is DBAA less DGS10 on the same session.
- **The monthly** is BAA, a monthly average, less that month's mean DGS10, with at least 15 sessions in the month.
- **When each row is knowable:** the latest `available_at` among its inputs.

## What changed in the harness

- **The Baa proxy overlay.** `hy_accel_baa`, with `proxy_of: hy_accel`, uses Part 23's HY Spread Acceleration triggers, read on Baa less the 10-year:
  - at least +50% off its 12-month low;
  - a 30-day change of at least +40bp;
  - a 30-day change of at least +15bp;
  - a level of at least 225bp, which is session-set;
  - it fires on 3 of these 4.
- **Its windows.** It reads the daily from 1986 and the monthly from 1962 (the `fallback`). Before 1962 it is not existent.
- **Where it prints.** It sits beside HY Spread Acceleration in every table. `classify` never counts it, so A77's pass rule and record are unchanged.
- **The "pending 6i-3" text is gone.** Before HY OAS exists, it now reads not existent. After that, until the store holds it, it reads not stored. The proxy prints beside it. A77's gate (`validate_tb_harness.py`) was updated to match: 32/32.
- **New entry points:**
  - `python -m altdata.tb_harness fpr`.
  - `CachedReader`: the store's as-of join over every vintage, loaded once per key. The gate checks it row for row against `Reader`.
  - `latest_record` and `latest_fpr`, for the reports.

## The laptop FPR (partial store)

Every overlay has **n = 0**, so there is no rate on the laptop:

| Overlay | Sessions | Scored | Unread | Not existent |
|---|---|---|---|---|
| Concentration & Complacency | 24,797 | 0 | 24,797 | 0 |
| HY Spread Acceleration | 24,797 | 5 | 7,472 | 17,320 |
| HY Spread Acceleration (Baa proxy) | 24,797 | 0 | 16,288 | 8,509 |
| Liquidity & Funding Stress | 24,797 | 0 | 24,797 | 0 |

**Why nothing scores.** The laptop store's FRED rows were all first knowable on the migration instant, 30 May 2026. It holds no Shiller rows, no SPY holdings, no DBAA and no BAA. So no overlay can be read as of any historical session. The box's run supersedes this edition.

## 6i-4: the reports

- **The Monthly.** `daily_cascade/tb_harness_block.py` builds one slow sub-section, "Top & Bottom: the harness's overlays and record". It joins through `config/stack_hooks/monthly-slow-tb-harness.yaml`, after `monthly-slow-capex-chain`, and prints three lines:
  1. each overlay's state with its trigger counts, the Baa proxy beside HY;
  2. the episode record from the newest calibration ledger's CSV: tops k of n called, controls k of n refused, bottoms not scored;
  3. the false-positive rate per overlay with n, from the newest FPR CSV.

  It prints no composite and carries none in its data.
- **`top_bottom_block`'s absence line.** It no longer says the harness is unbuilt. It now says decision 3 stores no composite and the harness prints in its own sub-section.
- **The Quarterly.** In the credit chapter, the row "HY spread acceleration" is now `harness_overlay: hy_accel` and no longer carries its absence reason. `structure_rows` prints both overlays' states at the quarter's end through `tb_harness_block.quarterly_row`.

## Box commands (for chain-8's sheet)

These are the operator's. Run them inside the windows, after the merge.

**1. The two series' history, from ALFRED's first vintage. Dry run first:**

```
cd ~/chester-reports && .venv/bin/python -m altdata.fred_history backfill --series DBAA BAA --dry-run
cd ~/chester-reports && .venv/bin/python -m altdata.fred_history backfill --series DBAA BAA
```

Check `python -m altdata.fred_history --help` for the exact series flag before running. The backfill's CLI was not changed here.

**2. The derived spreads over the full history:**

```
cd ~/chester-reports && .venv/bin/python -m altdata.market_features compute --backfill
```

**3. The FPR.** It opens the store read-only and writes outside the checkout:

```
cd ~/chester-reports && .venv/bin/python -m altdata.tb_harness fpr --edition box --dry-run | head -40
cd ~/chester-reports && .venv/bin/python -m altdata.tb_harness fpr --edition box --out-dir ~/chester-data/outbox/tb-harness
```

The box edition is a new dated file with the pre-registered head unchanged. A session copies it back on a branch.

## Gates and the count

**The new gate.** `tools/validate_tb_harness_fpr.py` declares `GATE_KIND = "code"`. Its groups:
- A, the pre-registration and its hash;
- B, the rule's fixtures;
- C, end to end, plus the cached join;
- D, the series, the registry, the bars and the lag families;
- E, the Monthly's three lines with no composite, and the Quarterly row.

**`tools/stitch_counts.py --write`** changed four counts:
- code gates: one hundred and forty-five → one hundred and forty-six;
- Python gates: one hundred and forty-two → one hundred and forty-three;
- FRED pull series: 283 → 285, in both CLAUDE.md and the architecture document's refresh line.

**Run on the laptop, one at a time:**

| Gate | Result |
|---|---|
| validate_tb_harness_fpr | 47/0 |
| validate_tb_harness | 32/0 |
| validate_monthly_stack | 267/0 |
| validate_quarterly_stack | 94/0 |
| validate_prices | 101/0 |
| check_registry | OK |
| check_library | 0 failures, 1 warning |
| check_master_guide | 14/0 |
| validate_audit_3a | 88/0 |
| validate_b51_registry_html | 25/0 |
| validate_stack_hooks | 15/0 |

The check_library warning is the Master Guide's HTML, which is stale by design on a builder's branch: the stitch rebuilds it.

**Base failures fixed here.** A77's CI run 40382171233 failed three gates on the base, and this branch inherited them:
- **check_master_guide:** the T&B ledger was missing from Table 7a. Both T&B ledgers are now rows.
- **validate_audit_3a:** `altdata.tb_harness` was missing from `config/catalogue_commands.yaml`. Added.
- **validate_quarterly_stack:** the Themes slow layer follows the chapters. The check now reads the chapters' slice.

**Gates edited beyond the new one, each for a declared addition:**
- validate_tb_harness: the pending text is resolved.
- validate_quarterly_stack: `harness_overlay` is a valid row.
- validate_audit_3a: `fred_6i3` is a new block.
- validate_stack_hooks: the S1 frozen order is now a prefix, so a later Monthly hook may follow it.

## Needs you

1. **The Baa proxy's level trigger, 225bp, is session-set.** Part 23's IG ≥ 110bp has no Baa analogue, and the value was not measured on the store before registration. It is pre-registered now: a different level would be a new registration and a new dated FPR ledger.
2. **The extended set's tops count as episode starts for the FPR, controls do not.** That follows from the calibration's own rule (a fire before a control is a false call). Say if near-misses should count as starts instead. That too would be a new registration.
3. **The box's DBAA and BAA history.** Run command 1 (ALFRED), then command 2, before the FPR run. Until then the box's Baa proxy is unread.
4. **Files edited beyond the paste's shared list.** All were needed for the Monthly and Quarterly wiring or for the base's CI:
   - `monthly_macro/payload.py`: the absence line;
   - `monthly_macro/quarterly_items.py`: the row reader;
   - `config/quarterly_chapters.yaml`: the one row;
   - `config/publication_lags.yaml`: two families;
   - `config/catalogue_commands.yaml`: one line;
   - `docs/master-guide.md`: two Table 7a rows;
   - the architecture document's FRED count, written by `stitch_counts.py`.

   Accept them, or name another place.
