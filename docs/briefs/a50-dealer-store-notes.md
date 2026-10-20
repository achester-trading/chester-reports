# a50-dealer-store: the dealer captures stored, the 09:45 bars, the Ahead matrix's store path (session A, 19 Oct 2026)

**Base and boundaries.** This branch is cut from `a49-secondary-notes`'s final tip, `0d22352` (A49's CI-table commit).
- **Branch only.** Pushed and nothing else: nothing ran on the box, no unit was enabled or started, nothing was merged.
- **It merges on its own, after chain-3.** When chain-3 is on main, main is merged into this branch with a merge commit, the gates are recounted, and the branch is pushed, so its pull request shows only its own commits.
- **The rulings.** Decisions 9 and 10 of 19 Oct 2026, 15:59 ET ("accept all"), and the fix from A48's local-run note.
- **chester-meme was not opened.**

## Part 1: the dealer captures stored (decision 9)

### The writer: `altdata/dealer_store.py`

Each of our engine's exposure files, `data/computed/<session>/<SYM>_<HHMMSSZ>_exposure.json`, becomes one row per field:

| Key | From the profile | New? |
|---|---|---|
| `exposure.net_gex` | `overall.net_gex` | registered before; first rows |
| `exposure.net_to_gross` | `overall.net_to_gross` | registered before; first rows |
| `exposure.regime_word` | the gate's word (below) | **new** |
| `exposure.gamma_flip` | `overall.gamma_flip` | registered before; first rows |
| `exposure.call_wall_otm` | `overall.call_wall_otm` | registered before; first rows |
| `exposure.put_wall_otm` | `overall.put_wall_otm` | registered before; first rows |
| `exposure.spot` | `spot` | registered before; first rows |

**The regime word** is `daily_cascade/dealer_block.regime`'s, with its printed percentage dropped:
- "positive gamma" or "negative gamma" where net-to-gross is at least `dealer_block.net_to_gross_min` (0.10, RULED);
- otherwise "indeterminate";
- no row without both inputs.

It is the capture's own gate reading, as the close prints it. Nothing new is computed.

**Keys and clocks.**
- **instrument:** the symbol.
- **observed_at:** the slot's ET instant on the session, e.g. `2026-10-19T09:45:00-04:00`. The slot comes from `dealer_block.slot_of`: a settled capture is 16:10, and an intraday one takes the nearest declared slot within the 20-minute tolerance. A capture outside every slot is not stored.
- **available_at:** the file's own `computed_at`, never the write instant.
- **source:** `dealer_capture:<the capture's run_id>`, else the file's stem. `dealer_capture` is a new source id in `source_registry.yaml` (tier derived, own computation).

**Why the existing key names.** Every reader that already names the dealer series reads `exposure.net_gex` for instrument `SPY`. That covers search-v1's coverage line on chain-3 (`config/alpha_search.yaml`, `history: {key: exposure.net_gex, instrument: SPY}`), the VRP engine's coverage, and the proposer's packet. Writing under those names switches them to stored rows with no edit to session B's files. Readers that group by day read the first ten characters of observed_at, so a day's three slots are that day's vintages in computed order, and an as-of read takes the newest capture knowable at its cutoff.

**What is refused, each with its reason:**
- a profile whose gamma the vendor supplied (`gamma_source: vendor`);
- any file not named `*_<HHMMSSZ>_exposure.json` (a legacy `*_gex.json` included);
- a restricted (Brookfield) symbol;
- a profile carrying an error, with no `computed_at`, or outside every slot.

No `data/vendor` file or FlashAlpha slot is opened.

### Where it runs

- **The capture:** `altdata/dealer_capture.run`, after `compute_written`. The run's JSON gains a `stored` entry.
- **The EOD pass:** `run_eod.py` Stage 2b, after Stage 2 (compute) and before Stage 3 (the pin log).
- **Never fatal.** `store_after_compute` returns an error line and never raises.
- **No unit and no timer of its own.** The units already allow writes under `%h/chester-reports`, where the store lives.
- **No accidental default store.** A run given its own `out_dir` without a `db_path` stores nothing, so no gate that captures into a temporary directory writes the default store.

### The backfill: Ari's box command, dry run first

```
cd ~/chester-reports
.venv/bin/python -m altdata.dealer_store backfill --dry-run
.venv/bin/python -m altdata.dealer_store backfill
```

- **The dry run** prints the files read, the rows it would write, the first and last session, and the skipped files counted by reason.
- **The second command** writes. Re-running it writes nothing, because the store's vintage key makes a re-store a no-op.
- **Options:** `--from D --to D` bound the sessions, and `--dir` and `--db` override the defaults.
- **Window:** run it inside the box-write windows.

### The two readers

- **The dealer regime's coverage line** (search-v1, chain-3) reads `exposure.net_gex` for SPY by name, so it needed no edit. It now finds the captures' first session. The dealer stays pending in search-v1 under the coverage rule (ruling 5(b)). This starts its history's clock and changes no ruling.
- **`alpha/event_rates.py`'s dealer bucket** now reads the stored regime word. This is session B's code; the change is listed for B below.

## Part 2: the 09:45 bars for engine 7 (decision 10)

`altdata/note_fetch.OPEN_IDS` adds `qqq` and `iwm` beside `spy`.
- **Registration:** they are the tape's own instruments, already registered as `bars.qqq` and `bars.iwm` in the `bars_prices` block, so no new key is needed. The `note_bars` block keeps its 12.
- **What lands:** the open fetch now stores all three of engine 7's instruments' completed 5-minute bars at decision time.
- **The bar in progress:** a fetch at about 09:47 stores bars to the one starting 09:40, because the 09:45 bar is still in progress and is dropped. The unit's 09:50 run stores the 09:45 bar too.
- **Engine 7's frozen spec is not edited.**
- **The intraday paper-fill path stays not built.**

## Part 3: the Ahead matrix's store path (A48's local-run note)

- **`opening_setup.with_pricing` reads only the store it is named.** Given none, it reads nothing and prints "reactions: not stored". It never opens the default store.
- **`ahead.build` takes `db_path` and passes it.** `weekly_stack.ahead_week` takes `db_path`, and the Weekly passes `str(st.path)`, the store it already opened.
- **`tools/validate_opening_setup.py`'s source check** now reads `with_pricing(r, now, db_path)`.
- **The fixture** (the new gate, groups B and G and its last check):
  - `with_pricing` with no path reads nothing, even with the default store seeded;
  - the capture with its own out_dir and no store writes nothing;
  - the whole gate run leaves no `data/chester.db` behind.

## The gate: `tools/validate_a50_dealer_store.py` (43 checks)

I chose a new gate rather than extending `validate_dealer_block` and `validate_secondary_notes`. `validate_secondary_notes` changed in one line only: its live-fetch count now reads `len(OPEN_IDS)` (9), where it had a literal 7.
- **The groups:** A the writer, B where it runs, C the backfill, D the readers, E registration, F the 09:45 bars, G the Ahead store path.
- **Fixtures:** synthetic only.
- **Run locally:** this gate 43/0, `validate_opening_setup` 61/0, `validate_secondary_notes` 87/0. Every other gate was left to CI.
- **The count:** 122 code gates (119 Python, three shell); CLAUDE.md updated.

## Every new key

- `exposure.regime_word` (units label, lens-excluded, trigger-ineligible, source `dealer_capture`).
- **First rows, no new registration:** `exposure.net_gex`, `exposure.net_to_gross`, `exposure.gamma_flip`, `exposure.call_wall_otm`, `exposure.put_wall_otm` and `exposure.spot` were already registered and receive their first rows.
- **A new source id:** `dealer_capture`.
- **A new catalogue command:** `altdata.dealer_store` in `config/catalogue_commands.yaml`.

## Files shared with chain-3

None of this branch's files is changed by `b45-chain3` against this base. The files most likely to meet on the merge are the ones every branch appends to:
- `CLAUDE.md` (the gate count, a new paragraph);
- `Makefile` (one gate line);
- `metrics_registry.yaml`;
- `source_registry.yaml`;
- `config/catalogue_commands.yaml`.

Also changed here, and read by chain-3's engine 7 and search: `alpha/event_rates.py`, `config/alpha_events.yaml`, `altdata/note_fetch.py`, `altdata/dealer_capture.py`, `run_eod.py`, `daily_cascade/ahead.py`, `daily_cascade/opening_setup.py`, `daily_cascade/weekly_stack.py`.

## For session B

**`alpha/event_rates.py`, the dealer bucket's read only:**
- `dealer_bucket(words, cutoff, cfg)` reads the stored regime word (`exposure.regime_word`, new helper `regime_words`). The newest word knowable at the decision within `max_age_days` is the bucket, else "awaiting".
- It no longer reads net GEX and net-to-gross, and it no longer applies its own 0.10 gate (`min_net_to_gross` left `config/alpha_events.yaml`). The gate is the capture's.
- The awaiting reason still names 6b, so `validate_alpha_lab_3`'s check keeps its shape (its fixture seeds no word, so the bucket stays "awaiting").

**Engine 7's "bars only after the close" limit** (`not_tracked.vwap`, `opening_range` and `writer_needed` in `config/alpha_intraday_dealer.yaml`) now applies to the backtest only. From this branch, SPY, QQQ and IWM have 5-minute bars stored at about 09:47 by the open fetch. Please carry that into engine 7's next registration; the frozen spec is untouched here.

## Needs you

1. **The backfill** on the box, dry run first (the commands above), inside the windows.
2. **The merge order.** This branch after chain-3, then main into it with a merge commit, then a recount.
3. **No restart is needed.** No unit file changed.
