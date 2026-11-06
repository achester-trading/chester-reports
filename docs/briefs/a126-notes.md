# A126 notes: item 124, Tranche 0 (the tail-days order's 106i; D60, 6 Nov 2026)

**Base.** `origin/main` at `bfd7e149`, PR #50's merge of chain-11, an ancestor
check passed. Branch `a126-item-124-tranche-0`. The paste is committed first as
`docs/pastes/A126.md`. It merges Monday 9 Nov with the week-after set.

**The order's text was not available.** `origin/b129-three-filings` was not on
origin at 09:24, 09:55 or 10:07 ET. So the build follows the paste's seven items
and D60's two amendments:
- locate by content;
- `calc.baa_less_10y` / `_m` in place of `fred.baa10y`.

The B129 attachment's section 6 should be read against this branch before the
merge (needs-you 1).

## 1. The one window label: `derived.window_label`

`window_label(asked, held_days, *, compact=False, start=None)`. It prints:
- the asked window alone when the held span covers it, within a month: "5y";
- "5y asked, 3.4y held" when the span falls short;
- "3.4y/5y" compact, with the caller adding the parentheses;
- "full history from <date>" for a full window, which is never short.

**Call sites:**

| Where | What prints it |
|---|---|
| `altdata/derived.py` `_pct_in_window` | every lens percentile: `pctile_5y_window`, `pctile_long_window`, plus `_window_asked`, `_window_held`, `_window_start` |
| `altdata/derived.py` `derived_forms`, `delta_percentile` | a new `window_label` field each |
| `daily_cascade/lens_cells.py` `_window` / `_pct_cell` | the compact and long cells; the long form keeps n |
| `regime.py` `compute_dimension` | `window_label` on every dimension, `window_days` against the primary's held span: the credit dimension, and all others |
| `regime.py` `percentile_window_note` | the also-window note |
| `regime.py` `session_move` | `window_label_5y` |
| `daily_cascade/state_block.py` | the dimension table, beside the percentile when short; the session move's five-year leg |
| `monthly_macro/stack.py` `triple` | the Monthly's triple table |
| `altdata/st_r5_rates.py` `lens` / `lens_text` | also read by `bank_stress`, `ai_trade`, `fragility`, `st_r5_index`, `st_r5_t1_rest` |
| `altdata/hf_positioning.py` | the table and the squeeze arm |
| `altdata/fragility.py` | the depth arm |
| `altdata/st_r5_t1_rest.py` | the oil-shock line |
| `altdata/vol_event.py` | the VIX line's 5y and 20y |

The gate's source scan found the last three, which an earlier grep had missed.

**What changed in print.**
- A covered window prints "5y" where it said "5 years".
- A short window prints "5y asked, 3.4y held" where it said "shorter than 5 years"
  or "under 5 years".

**Gates moved to the helper's wording:**
- `validate_st_r5_rates`, `st_r5_index`, `st_r5_t1_rest`;
- `batch14_a1`, `batch14_b1`, `batch15_2`;
- `validate_monthly_stack`.

**The flag-word audits.** The label's "held" collides with the dealer flag word
"held".
- `dealer_block.FLAG_WORD`, `monthly_macro/dealer._FLAG_WORD` and
  `validate_vol_event`'s pattern now skip "held" only straight after a year count:
  `(?<![0-9]y )held`.
- A level that "held" is still caught (needs-you 3).

**`METHOD_SOURCE_SHA`** was updated (`python -m regime method --update`). There is
no `METHOD_VERSION` bump: no state, band or percentile changes, only the new label
fields.

## 2. The FRED CSV guard

- **`fred.pull` merges on every path:** `merge=True`, with `full=True` and
  `lookback_days` included.
- **`Store.write_observations(..., allow_shrink=False)`:** it refuses a rewrite that
  would leave fewer rows or a later first date.
  - The CSV is left as it was.
  - The refusal is logged ("store: refused to rewrite <file> ...") and kept in
    `Store.refusals`.
  - `allow_shrink=True` is honoured.
  - The observation store's write is unchanged.

## 3. ST-R6.59c reads the store

`tools/calibration/st_r6_59c_bank_stress.py --db PATH`:
- **Reads:** the store read-only (`mode=ro`), the newest vintage per day; nothing is
  fetched.
- **The credit leg:** before the stored HY OAS history it reads
  `calc.baa_less_10y`, already in bp, and each such row prints "(proxy: Baa-10y)".
- **The pass rule:** the first edition's, word for word, which the gate checks;
  `write_ledger` still refuses a changed one.
- **`--public`:** keeps the first edition's run.
- **No new edition was written:** the next one is the operator's, on the box.

## 4. Sessions, not days

- **`oneday_10y`:**
  - `CHANGE_NAME = "10y D1 sessions"`;
  - the trigger's and the block's lines say "one-session change(s)" and "on the
    session";
  - D15's ruled name, "the one-day 10-year trigger", stays in the titles.
- **`speed_attribution.attribute`:** returns `name: "10y D{h} sessions"`, and the
  table's move column prints it.
- **No computation changed.** `validate_b59`'s quiet-line check moved to "one-session".

## 5. The long-window credit series

**The writer, `altdata/sources/fed_ebp.py`:**
- **Source:** the FEDS Notes CSV, keyless, robots.txt 404 (no rules); columns are
  found by name.
- **Keys:** `fed.ebp` and `fed.gz_spread`, percentage points, unit `percent_rate`
  (bp changes), family spread.
- **Backfill:** `--backfill` stores the history under `fed:backfill`, available at
  the pull instant (`ingest_instant`).
- **Regular pulls:** source `fed`, available at the file's Last-Modified, over a
  400-day window.

**Registrations:**
- source `fed`;
- the metrics and families;
- `market_state_barred`;
- `feeds.OFFICIAL_WRITERS` (whose KEYS feed the freshness roster);
- `config/catalogue_commands.yaml`.

**The laptop's first pull was a parse, with no write.**
- The live file gave 646 months of each series, 1973-01-01 to 2026-10-01.
- The latest EBP is −0.27 pp and the GZ spread 1.00 pp.
- Writing the store is the box's; the box step is below.

**The lens config diff.** `config/metric_lenses.yaml` gains two blocks.
- **`credit_long_window`:** series `calc.baa_less_10y`, 20 years, members
  `fred.hy_oas` and `fred.ig_oas`, basis D60. HY and IG OAS keep their own 5-year
  lens, its held span printed ("5y asked, 3.4y held"). Their long column now reads
  Baa less the 10-year's level against its own 20 years, named as that series
  ("62nd (20y of Baa less the 10-year, n=...)"). Their 5y/long disagreement flag
  is withheld, since it would compare two series.
- **`d20_forms: [calc.baa_less_10y]`:** the change over the last 20 stored
  observations, in bp.

**Where Baa less the 10-year prints.** It joins the Weekly's lens table, which the
Monthly reads too. Its compact cell is "D20 ±n bp; pct (5y); pct (20y)".

**The T&B config.** `config/tb_episodes.yaml`'s Baa proxy already names
`calc.baa_less_10y` (`baa_10y`), so it is unchanged.

**The Monthly's line.**
- **Placement:** one slow-read line in the slow layers, after the T&B harness's
  credit lines (`daily_cascade/credit_long_block.py`,
  `config/stack_hooks/monthly-slow-credit-ebp.yaml`).
- **Why there:** the Monthly's only hook anchor is in the slow layers.
- **Before the first pull:** it prints "not yet pulled".
- **Status:** report only; nothing enters the object, a composite or an overlay.

**Not used:** `altdata/config.py` gets no new series list. The paste's list was for
`fred.baa10y`, which D60 struck, and EBP is not a FRED series.

## 6-7. CLAUDE.md and the gate

- **CLAUDE.md:** the study-venv line under the gates paragraph, and the credit
  long-window sentence in the 6e lens paragraph.
- **Counts:** by `tools/stitch_counts.py --write`, **167 code gates (164 Python,
  3 shell)**, 8 data gates and 44 official writers. The architecture document's
  count was rewritten with it.
- **The Makefile:** no line. Since S1 the gate list is read from each gate's
  `GATE_KIND` (`tools/gate_list.py`); the A-branches' Makefile lines were dropped
  at every stitch the same way.
- **`tools/validate_item_124_t0.py`:** `GATE_KIND` code, clock pinned to
  2026-11-06. 41 checks over steps 1-5 on fixtures, including must-fails: the label
  scan fires on each hand-built shape, and a renamed CSV column is refused.

## Gates, one at a time

| Gate | Result |
|---|---|
| `validate_item_124_t0` | 41/0 |
| `validate_lenses` | 49/0 (its fixture now seeds Baa-10y, the credit long window) |
| `validate_regime` | 524/0 |
| `validate_batch12` | 57/0 |
| `validate_fred_history` | 25/0 |
| `validate_tb_harness` | 32/0 |
| `validate_tb_harness_fpr` | 47/0 |
| `validate_audit_fixes` | 174/0 |
| `check_registry` | OK |
| `validate_gates` | 32/0 |
| `check_library` | 27 papers, 0 failures, 0 warnings |
| `validate_stack --group A` (`bash scripts/make.sh validate-group validate_stack A`) | 13/0 |

Also run, for the files touched:

| Gate | Passed/failed |
|---|---|
| `audit_3a` | 88/0 |
| `official_sources` | 383/0 |
| `audit_1` | 48/0 |
| `secrets` | 58/0 |
| `stack_hooks` | 15/0 |
| `check_master_guide` | 14/0 |
| `outliers` | 37/0 |
| `morning_anchor` | 71/0 |
| `vol_event` | 50/0 |
| `dealer_block` | 134/0 |
| `st_r5_rates` | 72/0 |
| `st_r5_index` | 58/0 |
| `st_r5_t1_rest` | 103/0 |
| `batch14_a1` | 30/0 |
| `batch14_b1` | 68/0 |
| `batch15_2` | 60/0 |
| `b59` | 83/0 |
| `6e_rest` | 34/0 |
| `releases_b` | 76/0 |
| `gtm` | 77/0 |
| `stack` | 84/0 |
| `weekly_stack` | 83/0 |
| `monthly_stack` | 268/0 |
| `monthly` | 388/0 |
| `monthly_frames` | 48/0 |
| `figure_budget` | 123/0 |
| `numeral_audit` | 181/0 |
| `quarterly_stack` | 94/0 |
| `quarterly_rows_6i` | 34/0 |
| `quarterly_gates` | 95/0 |
| `attribution` | 85/0 |
| `correlation_layer` | 75/0 |

## The box, after the merge (the operator's, inside the windows)

```
python -m altdata.sources.fed_ebp --backfill      # once: the history under fed:backfill
python tools/calibration/st_r6_59c_bank_stress.py --db <the store> --box   # when the next edition is wanted
```

The daily official pass picks `fed_ebp` up from then on, with no new timer.

## Needs you

1. **The order's section 6 was not readable.** B129's branch never reached origin
   during the run. Read the attachment against this branch before Monday's merge;
   anything it asks that the paste did not is not built.
2. **The credit long window, as read here.** HY's and IG's "Pctile long" column
   prints Baa less the 10-year's percentile, named as that series. The alternative
   was a blank long column with a pointer to Baa's own row, which is now in the lens
   table either way.
3. **"held" in the label.** The ruled form "5y asked, 3.4y held" collides with the
   dealer flag word. The audits skip only "<n>y held". Rule a different word if you
   would rather the audits stay untouched.
4. **The OAS family's other members.** BB, CCC, AA, BBB and the EM OAS series also
   hold three years on FRED. They now print their honest spans, but their long
   column still reads their own short history. The paste named HY and IG only.
