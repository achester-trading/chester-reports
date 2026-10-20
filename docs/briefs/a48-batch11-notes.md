# a48-batch11: signal-triage Batch 11, the opening setup and the dealer scorecard amended (session A, 19 Oct 2026)

**This branch builds on `a47-chain3` and merges in the third chain.** It was branched from `a47-chain3`'s final tip, `ebd10c7`, which carries A47's pre-market line that Part 1 builds on.

- Branch only. I pushed this branch and nothing else, ran nothing on the box, and enabled or started no unit. Nothing is merged to main.
- The order is `docs/change-order-signal-triage-batch-11-2026-10-19.md`, filed verbatim (ruled 19 Oct 2026, 13:05 ET).
- **D2 is held throughout:** no SpotGamma or vendor figure in any file this branch adds, and nothing of SpotGamma's in the store or a report.

## Part 0: the order filed, and D7

- **The order** is committed byte for byte as delivered. No index of later batch orders existed, so it is indexed in the signal-triage register's header, in a new "Batch orders" row listing Batches 3 to 9 and 11.
- **D7, the chat-side FlashAlpha tasks:**
  - the box sheet's E6 now says the two tasks are retired at chain-2's merge (D7, 19 Oct), not on 29 Oct;
  - the a43-render notes' F-4 block says the same;
  - that F-4 block quoted two FlashAlpha figures; D2 removes them, and the line says so.

## Part 1: item 54 (like for like, the scorecard backfill) and item 55's bands

**The gauge (OS-2)** is now a short block, five lines, six with the pre-market centre, under the dealer-surface table:
1. **The head:** the engine's regime word, with net GEX's own-history percentile beside it, its window and n. There is no new regime word.
2. **The implied one-session move:** the close × the 30-day ATM IV × √(1/252). Beside it, the realised |close-to-close| one-session move in the gated regime: median, 80th and 95th percentiles, with n.
3. **The same at five sessions** (√(5/252), the move from the first session's prior close to the fifth session's close).
4. **The five-session high-low range.** It stays only against its implied expected range, a random walk's √(8/π) × IV × √(5/252), and the line says which measure it uses.
5. **The ±1σ bands** (item 55): one-session and five-session around the last close, and again around A47's pre-market price, each labelled by its horizon and its centre.

**Every count is split in two:** "since registration" (the test sample) and "before registration, descriptive".
- **Sources:** the stored `dealer.scorecard_day` rows and the settled profile, as before.
- **Budget:** at most six lines under 60 words each, displacing nothing (`config/opening_setup.yaml`).

**The scorecard backfill** (`python -m daily_cascade.scorecard_backfill run`):
- It rebuilds `dealer.scorecard_day` rows from the 16:10 settled captures on disk, back to the first.
- **Point in time:** each row's morning profile is the prior session's settled capture. Its bars, closes and SPY's IV are the session's own. Its `available_at` is the latest of its inputs': the capture's `fetched_at` and each stored input's.
- **Labelled:** `"backfilled": true`, source `daily_close:backfill`.
- **Idempotent:** a session with any row is skipped, and a live row is never replaced.
- **The fields it cannot rebuild:** the close's pin flags and the put/call ratio are None. No hypothesis reads them.

**The rates** (`altdata/dealer_scorecard.split_tables`):
- **The test sample** is the live rows from the registration date, 17 Oct 2026 (`dealer_scorecard.registered_on`).
- **The rest,** every earlier row and every backfilled row whatever its date, prints beside each rate as "before registration, descriptive": counts and a share, no interval, never a decision.
- The registration file is not edited, and its SHA-256 is unchanged.

**Fixtures:**
- **`validate_opening_setup` A (59/0, now 61/0 with Part 4)**, worked by hand:
  - the one-session distribution median 1.00 / 80th 1.50 / 95th 2.00 over n=24, and the five-session one 1.00 / 1.60 / 2.00 over n=20;
  - the expected high-low range;
  - net GEX at the 60th percentile, n=25;
  - both bands' centres.
- **`validate_a48_batch11` A:**
  - the backfill on synthetic captures (dry run, point in time, idempotent, labelled);
  - a backfilled row after the registration date kept out of the test sample;
  - the registration hash unchanged.

## Part 2: item 55's H6, the level clusters

**The registration came first.** `docs/ledgers/dealer-scorecard-preregistration-2026-10-h6.md` was committed (`15963c2`) before any scoring code, in the form of the scorecard's registration. It is never edited, and `validate_dealer_block` holds it to its SHA-256, `ec5691a6…`.

What it registers:
- **The four families:** positioning, the implied bands, the volume profile, and the prior session.
- **The cluster rule:** three or more families within 0.2%, frozen 30 days.
- **Eligibility:** H3's 0.25% approach.
- **Outcomes:** held, broke or not reached, in the session (H6s) and over five sessions (H6f).
- **The base rate:** any single level. **The baseline:** round numbers, $5 for SPY and QQQ, $2.50 for IWM.
- **Promotion:** H1 to H5's rule, with Benjamini–Hochberg across eight tests.

**The detector** (`altdata/level_clusters.py`) reads only our own levels, for SPY, QQQ and IWM. SPX joins after the solver gate, as a new registration.
- **The 16:45 close writes** the next session's zones, with every member level, under `calc.level_zones` (new key, registered).
- **The 07:00 anchor** prints at most two zones, nearest the prior close first. Each is one line with its families named, SPY's also in SPX and ES terms.
- **The close** prints one outcome line, as a Mechanics item: data, outside the word budget.
- **The Weekly** prints H6s and H6f beside H1 to H5, in their form.

**A design point for your review.** The prior-session family's overnight high and low are the overnight that led INTO that session: the close finds tomorrow's zones before tomorrow's overnight exists.

**The vendor annotation** is in the Weekly's vendor line only (`dealer_weekly.vendor_zone_notes`). For each week's SPY zone it says whether the vendor's flip and walls fall inside it. It uses words only, never a figure, and is never counted.
- The detector is in the opening-setup gate's vendor grep, and no module but `dealer_weekly` reads the vendor for it.

**Fixtures** (`validate_a48_batch11` B, 20/0 at the time):
- three families within 0.136% make a cluster; two families do not; 0.212% apart does not;
- the 30-day freeze, and a later overlapping zone not stored again;
- held, broke and not reached by hand;
- H6f's windows, the anchor's two lines, and the rates' form;
- the vendor note, words only.

## Part 3: item 53

**OS-6's ledger** is `tools/calibration/os6_positioning.py`, in the ST-7 form.
- **First edition** `docs/ledgers/os-6-ledger-2026-10-19.md` (laptop run, public sources, Yahoo's VIX family and ^GSPC from 2007): **FAIL**. Twelve tests are judged on 498 sampled sessions, and none survives Benjamini–Hochberg at q = 0.10. The nearest is VIX9D/VIX's bottom decile, at p = 0.043.
- **Pre-registered:**
  - point-in-time five-year percentiles;
  - the top and bottom deciles;
  - every 10th session sampled;
  - the 10-session forward return by Welch t, with the 5-session return, the drawdown and the realised vol beside it;
  - 20 sessions a tail at least;
  - Benjamini–Hochberg at 0.10 across the tests judged.
- **No composite and no weights are printed.** Its rights are stated, granting nothing.
- **The put-volume component** joins in the box edition once a five-year percentile is possible, or from D4's backfill (listed in the edition).

**The VIX premium split** is one line in OS-3's realised lens: VIX less RV20 = (SPY's 30-day ATM IV less RV20) + (VIX less SPY's ATM IV). It is labelled "SPY's ATM IV as SPX's proxy", is absent when SPY's IV is not stored, and displaces nothing. Its fixture is +4.0 = +2.0 + +2.0, worked by hand.

## Part 4: items 56, 57 and 58

**Item 56: per-name volatility state.**
- **New keys,** registered:
  - `chain.iv30_atm`: SPY's 30-day method on each name's chain;
  - `chain.rr_25d`: the 25-delta put IV less the 25-delta call IV, on the front month;
  - `chain.rv20` and `chain.rv60`.
- **Writers:** the close's `record_names` and `backfill-names` write them from the stored chains.
- **The Weekly's per-name table** sits after the technical appendix: one row per name (17), each with its window and n. Descriptive only, with no strategy label; a table, outside the word budget, displacing nothing.
- **OS-8's two IV rows** now read the 30-day IV less RV20.

**Item 57: earnings.**
- **The event-only implied move,** where an expiry before the report exists (the one before the post-event expiry), on the straddle convention: straddle / spot = √(2/π) σ √T. The post-event expiry's total variance less the pre-event expiry's variance rate over the same time, labelled. Otherwise the full straddle, labelled "includes non-event days".
- **The worked fixture:** a 40/700 straddle to 23 Oct less the 21 Oct straddle's 19.8/700 rate gives **4.6%**. `validate_weekly_fixes_8`'s META check moves from 5.7% to that, and `validate_weekly_calendar`'s NVDA check gains the label.
- **OS-11** takes up to eight reactions (config), prints n, and computes the word on the median of those available: n of 3 or more, else "n=k, no word". The 20% band is unchanged.
- **One stored record per print,** `calc.earnings_move` (new key): the implied move at the close before the report and the realised move after it.
  - **Written once** by the 16:45 close of the first session after the report (`altdata/earnings_moves.py`).
  - **Read back** by the Ahead rows.
  - **Offered to session B's engine 4,** which does not read it yet.
- **The MSTR row** names MSCI's events from the digital-asset calendar (item 49).

**Item 58: OI builds.**
- **D6's floor:** 2,000 contracts for SPY, QQQ, IWM (and SPX), 500 for a single name. Provisional, session-set, in config.
- **A new column:** the OI change as a share of the session's volume in that contract. The later capture's OI is the earlier session's settlement, so the volume is the earlier capture's.
- **The premium is unchanged:** the mid.
- **The outcome ledger** (`tools/calibration/os9_build_outcomes.py`) rebuilds each session's printed builds from our captures with the anchor's own functions, and resolves them at expiry on Yahoo's closes.
  - **Pre-registered:** with 30 or more resolved, the Brier score beats the base rate's, and every decile of 5 or more holds its mean printed chance inside its Wilson 95%.
  - **First edition: INSUFFICIENT.** The laptop holds no captures.
- **The December comparison** is written as a pre-registered specification, `docs/ledgers/os-9-vendor-month-comparison-spec-2026-10.md`: the overlap of contracts, how often a known side would change the read, and the size check. Agreement statistics only, no vendor figure; it is built with the vendor-month writer.

**Fixtures** (`validate_a48_batch11` D, E and F, by hand; the whole gate is 49/0):
- the risk reversal +5.0, RV20 and RV60;
- the per-name table's row;
- the event-only move;
- "n=2, no word";
- the record written once (a bug caught here: a per-symbol read was needed);
- the floor, and the 64% column;
- the outcome ledger's rule on synthetic builds.

## Part 5: D4's probe, and the backfill

**What Massive's public documentation says (read 19 Oct 2026; quoted in the tool's docstring):**
- the options day-aggregates flat file is "Included in select Options plans";
- **Options Starter:** recency "End-of-day", history "**2 years**";
- "Records date back to June 2, 2014"; "Updated at 11a ET to include the previous day";
- **its columns:** ticker, volume, open, close, high, low, window_start and transactions. **There is no open interest.**
- Massive "returns options open interest only on its snapshots, as the latest daily figure", so no OI history exists in any form we pay for, as expected;
- **access:** S3-compatible, endpoint `https://files.massive.com`, bucket `flatfiles`, prefix `us_options_opra`, with an S3 Access Key and Secret Key from the dashboard; rclone is a supported client.

**Starter includes two years of per-contract day bars, so the backfill is built:** `tools/massive_flatfiles_backfill.py`, for Ari to run on the box.
- **Resumable,** through `~/chester-data/flatfiles/backfill_state.json`.
- **Capped:** `--max-days`, default 25 sessions a run. **Dry run first:** one listing to prove the credentials, and the plan; nothing is downloaded.
- **One day's file at a time,** streamed through `rclone cat` and the gzip reader, never held whole. It keeps only the 17 names' contracts.
- **It writes,** per name and session:
  - puts' share of volume;
  - the 30-day ATM IV, the 25-delta put skew and the risk reversal, from the day bars' closes, under the same keys with source `chain_capture:flatfiles`, labelled "from last-trade closes, not mids". Each row is `reconstructed`, available at 11:00 ET the next session.
- **No new dependency:** rclone's S3 backend is configured from the environment and never written to rclone.conf.
- **Credentials,** by name in `.env`: `MASSIVE_FLATFILES_ACCESS_KEY_ID`, `MASSIVE_FLATFILES_SECRET_ACCESS_KEY`. They are read through `altdata.secrets`.

**The rank's rule, pre-registered here** (`altdata/flatfile_history.py`):
- **When a rank reads it:** only where the flat-file history's overlap with the captured history is **10 sessions or more** and its **median absolute difference** is within:
  - `chain.iv30_atm` 1.5 vol points;
  - `chain.skew_25d_put` 1.5 vol points;
  - `chain.rr_25d` 2.0 vol points;
  - `chain.put_share_volume` 5.0 percentage points.
- **Otherwise** the rows are stored and unused.
- **A captured reading wins** on a shared session.
- **The two kinds are read apart.** The as-of join keeps only each date's newest row, and a flat-file row, published the next morning, would otherwise hide the capture it is compared with.
- **Fixture:** `validate_a48_batch11` G.

## Registry, catalogue, units and the count

- **New keys, each registered with its units, family or exclusion:** `calc.level_zones`, `calc.earnings_move`, `chain.iv30_atm`, `chain.rr_25d`, `chain.rv20`, `chain.rv60`.
- **New sources:** the backfills' sources are the registered ids with a variant (`daily_close:backfill`, `chain_capture:flatfiles`).
- **The catalogue:** the `chain_metrics` line names the four new readings. No new altdata module runs as `python -m`, so the catalogue gains no command.
- **New config blocks:** `level_clusters` (mirroring H6), `dealer_scorecard.registered_on`, OS-9's `floor`, OS-11's `reactions: 8` and `word_min_n: 3`, and the gauge's `horizons`.
- **The count:** CLAUDE.md now reads one hundred and twenty code gates (one hundred and seventeen Python, three shell) and eight data gates, with `tools/validate_a48_batch11.py` added. **Session B's b45-chain3 also reads 120** with its own gate. Whichever branch merges second must recount: 121 if both stand.

## Gates run locally, one at a time

| Gate | Result |
|---|---|
| validate_a48_batch11 | 49/0 |
| validate_opening_setup | 61/0 |
| validate_dealer_block | 134/0 |
| validate_weekly_fixes_8 | 67/0 |
| validate_weekly_calendar | 44/0 |
| validate_secrets | 58/0 |
| check_registry | OK |

**A local-run note.** One of my local gate runs left an empty `data/chester.db` in this worktree, and `validate_weekly_calendar` then failed 11 checks on its next run. The cause was OS-11's reader, which opens the default store when no path is given and raised on a file without an events table. The reader now treats a missing table as "not stored". The file is gitignored, in my worktree only, and under the deny list's `data/`, so I left it. **No committed gate reads the live store; that is a fault for a later look,** since `with_pricing` is called with no path from the Ahead matrix.

The rest is CI's. That includes `validate_monthly_stack` and `validate_weekly_complete`, which render, and the Weekly gates the per-name table and the scorecard's extra lines may touch.

## Box commands for Ari, after the third chain merges (each dry run first)

1. **The scorecard backfill:**
   ```
   .venv/bin/python -m daily_cascade.scorecard_backfill run --dry-run
   .venv/bin/python -m daily_cascade.scorecard_backfill run
   ```
2. **backfill-names**, which now writes the four new keys too:
   ```
   .venv/bin/python -m altdata.chain_metrics backfill-names --days 60 --dry-run
   .venv/bin/python -m altdata.chain_metrics backfill-names --days 60
   ```
3. **The ledgers' box editions,** each a new dated file outside the checkout:
   ```
   mkdir -p ~/chester-data/ledgers
   .venv/bin/python tools/calibration/os6_positioning.py --box --out ~/chester-data/ledgers
   .venv/bin/python tools/calibration/os9_build_outcomes.py --box --out ~/chester-data/ledgers
   ```
   Then, from the laptop, `scp 'vps:~/chester-data/ledgers/os-[69]-*' docs/ledgers/` and tell a session to commit them.
4. **D4's backfill.** First add the two names to `.env` by hand; the values are yours, from Massive's dashboard: `MASSIVE_FLATFILES_ACCESS_KEY_ID`, `MASSIVE_FLATFILES_SECRET_ACCESS_KEY`.
   ```
   .venv/bin/python -m altdata.secrets MASSIVE_FLATFILES_ACCESS_KEY_ID MASSIVE_FLATFILES_SECRET_ACCESS_KEY
   .venv/bin/python tools/massive_flatfiles_backfill.py --dry-run
   .venv/bin/python tools/massive_flatfiles_backfill.py --max-days 25
   .venv/bin/python tools/massive_flatfiles_backfill.py --status
   ```
   About 500 sessions in all, 25 a run. Run it inside the windows, never 16:00–17:20. It is resumable at any point.
5. **The first two weeks of cluster output:** a review with you (the order's by-hand step), reading the anchor's lines and the close's outcome lines.

## Files shared with session B

| Branch | Files |
|---|---|
| alpha-lab-4 and b45-chain3 | `CLAUDE.md` (the count line), `Makefile` (one gate line each), `config/catalogue_commands.yaml`, `docs/signal-triage-register.md` (my header row only), `metrics_registry.yaml` (new entries and family lines, no edit of theirs) |
| library-st-l | `CLAUDE.md`, `Makefile` |

**For engine 4 (session B):** `calc.earnings_move` is the per-print implied-against-realised record, offered as the order asks. Nothing in the lab reads it on this branch.

## Needs you

1. **The deny list's literal key names.** `.claude/settings.json` denies `cat` and `tail` of any literal key name. The two new names, `MASSIVE_FLATFILES_ACCESS_KEY_ID` and `MASSIVE_FLATFILES_SECRET_ACCESS_KEY`, are not on it, and nor are they in `validate_deploy`'s MUST_DENY. That is a settings edit, which is yours to approve at the laptop, as with ruling 5.
2. **Vendor figures already committed before D2:**
   - `tools/validate_a43_render.py`'s FlashAlpha fixture (now synthetic; vendor figures removed, 19 Oct 2026, under the standing rule);
   - `tools/vendor_reconcile.py`'s docstring;
   - `docs/ledgers/vendor-divergence-notes.md`'s Entry 1.

   D2 says no vendor figure in any committed file. Say whether that reaches back to these. Changing a gate's fixture was beyond this paste.
3. **H6's prior-session family** uses the overnight that led into the prior session (see Part 2). Accept, or rule another reading.
4. **SPX in OS-9's index floor** (2,000): the order names SPY, QQQ and IWM. SPX is an index and takes theirs here, provisionally.
5. **OS-6, S-type verdict:** its first edition is FAIL. Under rule 31 it is a draft for your accept-all; no register entry was written.
6. **D4's backfill** stores readings from last-trade closes. Ranks read them only on the pre-registered agreement. Accept the tolerances, or name others, before the first run.

## CI

| Run | Commit | Result |
|---|---|---|
| 39296690572 | `174da7c` (Parts 0 to 2) | success |
| 39299419882 | `5ebc157` (Parts 3 and 4) | success |
| **39300378572** | **`991520f` (Part 5 and the notes)** | **success: 130 of 130 jobs** |

