# B85 notes: eight derived keys never written; LF for pinned-hash files

Paste B85 (`docs/pastes/B85.md`), 29 Oct 2026. Base `f380e12e`, as the paste
states; origin/main had moved to `422ea697` by the time this ran. Both branches
merge after the 1 Nov Monthly.

## Part 1: the eight keys (branch `b85-crypto-derived-keys`)

No key is class (b). Every one is computed in `crypto_derived.compute`, which the
feed run calls, and each is unwritten for a reason in its inputs.

| Key | Class | The code | Why it has no row |
|---|---|---|---|
| calc.etf_streak | (a) | `s2_rows`, `_series(st, f"farside.{coin}_total")`, then `if not tot: continue` | Its only input is Farside's, refused since 24 Oct 2026 |
| calc.etf_5d_pct | (a) | `s2_rows`, the same | The same |
| calc.flag_etf_extreme | (a) | `s2_rows`, the same | The same |
| calc.dvol_pct_full | (c) | `s4_rows`, `if len(hist) >= 60:` | 60 days of `deribit.dvol_*` needed; the daily pull keeps 14 days back (`daily_window_days`), and the backfill to 2021 is a separate command (`deribit.backfill`) |
| calc.dvol_pct_5y | (c) | `s4_rows`, inside the same `if` | Written with `dvol_pct_full` |
| calc.froth_z | (c) | `s5_rows`, `(day - first).days >= need - 1`, need = `s5.min_store_days` 90 | 90 days of GeckoTerminal's own rows; the sample has no backfill (gt.py: "no backfill exists") |
| calc.flag_froth | (c) | `s5_rows`, `if len(zs) == 2:` over the z days | Written with `froth_z` |
| calc.flag_leverage_crowded | (c) | `compute`, `for d, z in lz.items():` with `lz = zscores(agg, 90, 60)` | `leverage_z` needs 60 observations of `funding_agg`, which began with the first pull; its z prints from 15 Dec 2026 (ruling 5 of 17 Oct, config `z_from`) |

**The change: declarations in `metrics_registry.yaml` `member_overrides`, the
mechanism the refused writers' keys already use.**

- **(a) refused.** The three S-2 keys are `status_extra: refused` with Farside's
  reason and date, as `farside.*` already are. They never lapse.
- **The blocks already say so.** `crypto_blocks.etf_line` and `_etf_daily` print
  `refusals.text("farside")` ahead of any ETF figure: "not tracked: Farside
  refuses automated reads since 2026-10-24 (HTTP 403, a Cloudflare challenge, on
  farside.co.uk/btc/ and /eth/)". `crypto_blocks.py` is therefore unchanged.
- **(c) a stated minimum-history gap.** The five history-bound keys are
  `status_extra: gap`, each with a `gap_reason` naming the history it needs, and
  a new field, `declared_until`: the date its first row is due.
  - `derived.declared_status` now honours `declared_until`. The declaration
    lapses on that date, so a key still unwritten then is counted stale again.
    It is never hidden for good, which `while_held` or an undated gap would do.
  - A declaration without the field behaves exactly as before.
  - The dates: DVOL 2 Dec 2026, the leverage flag 16 Dec 2026, froth 15 Jan 2027.
  - They assume the box's first crypto pulls on 17 Oct 2026, the day both
    tranches landed.
- **Nothing is fetched, typed or scraped.** No new source and no by-hand line.

**Faster for DVOL, the operator's call:** `python -m altdata.sources.deribit
backfill` (a dry run first with `--dry-run`) stores DVOL from March 2021. The
percentiles then write on the next feed run, and their declaration is moot.

**Possibly also affected:** `calc.leverage_z` and `calc.oi_mcap_z` need the same
60 observations. The heartbeat did not name them, so they are left undeclared
here. If they turn up absent, they take the leverage flag's declaration.

**The fixtures:** `tools/validate_crypto_sources.py` group P, five checks.
- S-2's keys are refused with Farside and never lapse.
- The five are gaps with their dates and reasons.
- Each lapses on its date and holds the day before.
- An undated declaration is unchanged.
- With Farside refused nothing is written for S-2, and one stored DVOL day
  writes no percentile.

Group K already proves the 60- and 90-day thresholds on fixtures.

**Gates,** one at a time, in the foreground:
- validate_crypto_sources: 122 passed
- validate_a47_chain3: 42 passed
- check_registry: OK
- validate_feed_repair (the declared-key mechanism): 50 passed

**After the merge,** the heartbeat lists the eight as declared, not stale. The
external roster's stale count falls by eight. With no other external key stale,
the verdict leaves `feed_stale`: the external line should read declared 8 more
than tonight and stale 0. On 2 Dec 2026 the DVOL pair lapse back to counted; by
then they are written, or the backfill has run.
