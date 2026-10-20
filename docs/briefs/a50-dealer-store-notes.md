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
3. **No restart is needed.** No unit file changed in A50.

## The CI rounds

| Round | Run | Result |
|---|---|---|
| A50 | 39364872331 | failed: `validate_a43_render` 43/3. Its fixed `2026-10-20T00:00:00Z` cutoff hid the vendor pull's wall-clock fixture rows on every run after midnight UTC on 20 Oct, on any branch |
| A50 round 1 | 39366016941 | **green, 132/132 jobs** (`bb33cd5`): the gate reads at a cutoff after the run (46/0 locally) |
| A51 | 39367053057 | failed: `validate_st_r5_t1_rest` pins `FRED_PULL_SERIES` at 266; RSAFS makes it 267 |
| A51 round 1 | (below) | the pin moves to 267 with its reason (103/0 locally) |

**For the merge sheet:** any branch carrying `validate_a43_render` as of A43 fails it from 20 Oct 00:00 UTC, chain-3 included, until this fix (or its equivalent) is on it.

# A51: A49's three answers and the volatile-day flag completed (ruled 19 Oct 2026, late evening)

Same branch, so one pull request carries both. Ruling: "accept all" on the four decisions sent at 23:35 ET.

## Part 1: A49's three answers

### (a) The session-set values stand as starting values

Each value is marked in place "kept 19 Oct 2026 as a starting value; reviewed after the first two live weeks".

| Value | Where | Reason |
|---|---|---|
| evening thresholds 0.75% / 1% / 1.5% | `config/reporting_stack.yaml` `secondary_notes.evening` | ES or NQ at about half the gauge's typical one-session sigma; dollar-yen at the carry-unwind order of magnitude; an Asia index's large open |
| capture wait, 4 minutes | `secondary_notes.open.capture_wait_minutes` | the bounded wait for the 09:45 capture, so the note lands by 09:55 |
| news_max 5 (open) and 8 (evening) | `secondary_notes.open/evening.news_max` | the notes' news blocks stay short; the evening has the after-hours names to carry |
| voices pass, 120 seconds | `secondary_notes.voices_budget_seconds` (new; was hard-coded in `note_fetch.py`) | one pass inside the scan's daily cap, short enough that the open note lands by 09:55 |
| heartbeat allowance, 100 hours | `scripts/check_heartbeat_cron.sh` `ANCHOR_TABLE` | spans a weekend and a holiday for either note; a warning only |
| memory caps, 8% / 10% | `deploy/systemd/chester-open-note.service`, `chester-evening-note.service` | a short fetch and one model call, never beside a heavy unit |
| timeouts, 12 / 15 minutes | the same two units | stop a hung HTTP call holding the lock |

**The two unit files changed in comments only.** Neither unit is enabled or in `DEPLOY_TIMERS`, so the self-deploy copies them with no restart pending.

### (b) Reading forms for PPI and retail sales

`config/release_calendar.yaml` has a new block, `tier2_headlines`, beside `tier1_headlines`:
- **PPI final demand, month on month:** `fred.ppi_final_demand`, which is FRED's **PPIFIS**. The store already holds it (`FRED_6E_SERIES`).
- **Advance retail sales, month on month:** `fred.retail_sales`, which is FRED's **RSAFS** (Advance Retail Sales: Retail Trade and Food Services, millions of dollars, SA, monthly). **It is new:** `altdata/config.py` `FRED_NOTES_SERIES`, joined into `FRED_PULL_SERIES` (now 267), so it is pulled through the existing FRED writer. It is registered as block `fred_notes` (one member) and listed in `validate_audit_3a`'s `NEW_KEY_BLOCKS`. I kept it out of session B's `FRED_RELEASES_SERIES`, whose gate pins 45.

How the notes read them:
- `note_fetch.release_series` reads `tier1_headlines` first, then `tier2_headlines`.
- The open note prints both releases' prints. Lens 24's line prints where it has one (PPI's), and retail sales has none.
- The Weekly's tier-1 tables do not read the new block.
- **Fixtures:** one each, in the new gate's group H. PPI prints +0.40% on +0.20%; retail sales prints -0.30% on +0.50%.

### (c) The Saturday news pull: nothing built

**The check for the merge sheet.** Look at the first Sunday dry run, 25 Oct. Does the Sunday edition's news block reach back to Friday 16:10?
- If Yahoo's items stop short of Friday 16:10, the Saturday news pull is built.
- If they reach it, nothing is built.

## Part 2: the volatile-day flag, all four of Doctrine 5.5's arms

`daily_cascade/volatile_day.py`. Each arm is worded as 5.5 words it, and prints with its reading and its as-of time. The flag is raised when any arm holds. An arm whose input is not stored prints "not read" and does not count either way.

| Arm | Read from | As of |
|---|---|---|
| the VIX at or above 25, or up 20% or more over the prior session | the stored VIX closes (config `book_c`) | the prior close |
| the overnight range in the ES above 1.5 times the 20-day average true range | the ES block's 5-minute bars: the futures day so far against Wilder's true range over the 20 complete sessions before it | 07:00 |
| the gap at the open of 1% or more | **provisional** at 07:00: the pre-market price (ES at the session basis, opening_setup's pre-market line) against SPY's stored prior close. **Settled** by the 09:50 open note from SPY's 09:30 open, which prints whether the flag is now raised | 07:00, then 09:50 |
| the Gamma dial reading Negative | the market-state object the anchor prints (`regime.latest`); read, never computed | the prior session |
| a tier-1 event on the calendar | the events calendar: FOMC statement, Consumer Price Index or Employment Situation on the session's ET day; or an index mover's earnings that day or after the prior 16:00 close | 07:00 |

**Where it prints:**
- **The 07:00 anchor:** `morning_payload` carries `volatile_day`, and `morning_render` prints it under the gauge and in the text edition.
- **The 09:50 open note:** a last block, "Volatile-day flag", with the settled line. Its prose gate gains `volatile_day`, the completed flag.

**Rights unchanged.** The flag is printed, never applied. No size is halved and no packet is refused; the Doctrine's automatic actions wait for Doctrine #2 and Book C's activation. Nothing enters a composite or the market-state object.

### Session-set values (config `vol_event.yaml` `volatile_day`)

| Value | Setting | Reason |
|---|---|---|
| `min_atr_sessions` | 15 | three-quarters of the 20-day window: one missed week does not blank the arm, and a fresh store does not pass a thin average off as a 20-day one |
| `index_movers` | class `earnings_mega` of `config/weekly_ahead.yaml`: the ten largest S&P 500 index weights the ranking holds, plus the hyperscalers. Today that resolves to AAPL, AMZN, AVGO, BRK-B, GOOG, GOOGL, META, MSFT, NVDA, ORCL, TSLA | the largest weights are the names whose own earnings move carries to the index's open, and this ranking is the one list of them the store holds. **Listed for Ari** |
| earnings window | the session's ET day, or after the prior session's 16:00 close | an after-close report moves the next open |

The RULED values are Doctrine 5.5's: VIX 25 and +20%, 1.5 times the 20-day ATR, a 1% gap either way, and FOMC, CPI and the employment report.

### Fixtures (the new gate, group I; `validate_secondary_notes` group D)

- each arm alone raises the flag;
- a day with no arm, and a day with two;
- each arm from its inputs, at and around its threshold;
- the open gap settling a provisional flag, both ways:
  - a provisional +1.20% raises it, and the open at +0.45% settles it "no longer raised";
  - a provisional +0.45% leaves it down, and the open at +1.05% settles it "now raised";
- the seeded CPI-day open note settles its gap at +1.05%, and its gate reads the completed flag.

## A51 needs you

1. **The index-mover rule** (above), session-set: confirm or replace.
2. **`min_atr_sessions` 15**, session-set: confirm or replace.
3. **25 Oct:** the Sunday news-block check (c), on the merge sheet.
4. **RSAFS's history (optional).** Its first rows come from the FRED pull after the merge. A deep history is the existing `python -m altdata.fred_history backfill`, on the box, dry run first, if the open note's prior form is wanted before the next release.
5. Everything in A50's needs-you list still stands.
