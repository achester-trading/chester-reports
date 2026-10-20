# a44-opening-setup: the rulings on a43, and the opening setup's first half, OS-2, OS-3, OS-10 and OS-11 (session A, 18 Oct 2026)

**What it builds on.** The branch starts at the tip of `a43-render` (`20dd7ab`, its CI fix), on session A's own line. It therefore carries the dealer engine, item 52, ST-10 and the vendor writer, and everything under them.

**Merge order.** It merges after `a43-render`, in the second stitched chain: … st-t3-calib, a43-render, then a44-opening-setup.

**What was done.** I pushed only. Nothing was merged or deployed, nothing ran on the box, and no unit was enabled or started.

**The ruling in force.** Everything here is **report-only**: no 0–100 score and no weights (D-4), every rank prints its window and n, and the vendor is never read by these builders.

**Commits:**

| Commit | What |
|---|---|
| `20dd7ab` (on a43-render) | a43's CI fixes, and its notes' CI rows |
| `5594468` | Part 0: ruling 2, the expected-move path |
| `e62c828` | Part 1: OS-2, OS-3, OS-10, OS-11 |
| this commit | These notes |

---

## Part 0

### a43-render's CI

**What failed.**
- `39160062209` (`f6bfc9a`), `39160241459` (`869663b`) and `39160398717` (`f165f12`) each failed on five gates of mine, all from ST-10:
  - **`validate_official_sources`:** `funding_hooks` imported a writer (cfets).
  - **`validate_vol_event` and `validate_dealer_block`:** both pinned the two-gate 12:30 registry.
  - **`validate_st_t2_rates` L:** `config/st10_lines.yaml` named an ST-5 key in a comment.
  - **`validate_st_t3_calib` A:** `signal_lines` reads `calc.abs_stress` and was not on the gate's list of display readers.
- `39160062209` also carried the two `869663b` fixes.

**The fix.** `20dd7ab` on a43-render:
- `funding_hooks` reads the gap through `funding_currency.offshore_gap_bp`;
- the two registry checks read four gates;
- the yaml names no key;
- `signal_lines` is a listed display reader;
- both branches' Weekly-builder checks are scoped to their own commit ranges.

Its run, **39175853075, is green.** a43's notes carry the failing rows. This run's number is recorded here, so a43's tip did not move again.

### Ruling 2: the expected-move path

- **The path** is `GET /v1/expected-move/{symbol}`, with optional `?expiry=`.
- **The parser** reads `expected_moves[]` (`expiry`, `daysToExpiry`, `atmIv`) for F-2's 20-DTE IV and the GEX expiries.
- **A 403 or 404** stores nothing, prints "expected move: not served", and the 20-day comparison waits.
- **The fixture** is `tests/fixtures/dealer_block/flashalpha_expected_move_SPY.json`: synthetic values in the ruled shape.
- **The gate** is `validate_a43_render` E: served, it stores the 20-DTE IV (16.8, not the 1-DTE 120.4); a 403 or 404 stores nothing and says so. 46/0.

Nothing else on the vendor writer changed.

**Ruling 3** is in the box sheet below: Ari enables `chester-vendor-chains.timer` on Thursday evening, so **Friday 16:31 is the first capture by the new path.**

**Rulings 1, 4 and 5** need no code. The 57-request plan stands; the stitch keeps both sides of the technical appendix; the drafts are on the accept-all list.

---

## Part 1: the opening setup, first half

Settings live in `config/opening_setup.yaml`, each session-set with its reason. The builders are in `daily_cascade/opening_setup.py`; OS-3 is in `altdata/vol_event.py`.

### OS-2: the expected-movement gauge

- **Where:** the 07:00 anchor, one line under the "Prior close — dealer surface" table.
- **What it prints:**
  - the regime word from the morning profile (the prior session's settled 16:10 capture), as the engine prints it, with net-to-gross and the 0.10 rule ("indeterminate (net is x% of gross)" below it);
  - the one-sigma range from our own implied range: last close ± spot × IV × √(1/252), with SPY's ATM 30-day IV, else the VIX labelled as a proxy;
  - "typical realised range at this reading: \<x\>% over 5 sessions (n=\<k\>)", the median over the scorecard's stored sessions of the same gated regime, once n is 20; below that, "awaiting (n=\<k\> of 20)".
- **No CALM / NORMAL / WILD words.**
- **It displaces nothing:** the table keeps its rows, and the ST-10 block's budget is unchanged.
- **Sources:**
  - the dealer engine's settled profile;
  - the scorecard's `dealer.scorecard_day` rows;
  - `yfinance.mkt_spy`;
  - `chain.spy_atm_iv_30d`, else the VIX (yfinance).
- **"Pre-market or last close":** the gauge uses the last close. The pre-market level would need the futures-to-SPY conversion, which is not built.
- **Fixtures (A):**
  - each five-session window is 4.0% of the prior close; 24 sessions make n=20 and it prints, 23 make n=19 and it is "awaiting";
  - the last close × 18.2% × √(1/252) (the close the fixture uses is synthetic since 19 Oct 2026, when a vendor-served spot was removed under the standing rule);
  - the indeterminate gate;
  - the numeral audit passes.

### OS-3: the volatility-regime lenses

These extend item 52's lens table and do not duplicate it.

| Lens | Item 52 had | Now also |
|---|---|---|
| **Realised against implied** | VRP | Its 1-year and 5-year percentiles, each with its n |
| **Term structure** | VIX3M/VIX | Its percentiles, plus VIX6M/VIX with its percentiles |
| **Short-term spike** | — (new lens) | VIX9D/VIX with its percentiles |

- **Each row prints its as-of,** in a third column: the session, or "—" while a lens awaits its input.
- **No composite.**
- **The table still prints only when item 52 fires.** See Needs you 2.
- **Fixtures** (`validate_vol_event` OS-3, 50/0): VIX9D/VIX 1.100 at the top of four; VIX6M/VIX 1.100 at the 75th; the VRP's percentiles at n=252 and 1,260; the as-of column.

### OS-10: the most-active names

- **Where:** the Weekly's Mechanics, after the vendor line, through `dealer_weekly.mechanics`. `weekly_stack.py` is untouched.
- **What it prints:** the week's ten most active names by options volume, with:
  - the volume;
  - the front-month ATM IV;
  - its IV rank and percentile over our stored history, with the window and n (our captures start in September);
  - the one-day IV change;
  - "implied ±x% against realised y%": spot × front IV × √(5/252) against the week's close range.
- **Report-only:** no chart, no paragraph, no score.
- **The data:** two new stored series, `chain.options_volume` and `chain.atm_iv_front` (instrument = the symbol, source `chain_capture`).
  - `altdata/chain_metrics.record_session` records them for every captured name, where the close already records SPY's.
  - **The front month** is the nearest third-Friday expiry at least 7 days out, else the first expiry 7 or more days out (labelled "nearest"), solved as SPY's 30-day IV is.
  - **`backfill-names`** rebuilds them from the captures on disk.
- **The universe** is the captured one: 17 names, including SPY, QQQ and IWM. See Needs you 1.
- **Fixtures (B):**
  - the top ten in order;
  - IV 44.0%, rank 100 and the 100th percentile of n=25;
  - +1.0 points on the day;
  - implied ±6.2% against a realised 6.0%;
  - the third Fridays;
  - a capture's volume summed.

### OS-11: the earnings rows

- **Where:** in the Ahead matrix, each earnings row's consensus cell gains:
  - "last three reactions: \<a\>, \<b\>, \<c\>" ("not stored" where absent);
  - "pricing elevated / muted / in line: implied ±x% against a median absolute reaction of y% (a fifth either way is in line; not a recommendation)".
- **Elevated** is the implied move at least a fifth above the median; **muted** at least a fifth below; anything else is **in line**. With fewer than three reactions stored, no word prints.
- **The implied move is the matrix's own figure.** Its expiry rule (strictly after an after-close or unknown-time event) arrives with weekly-fixes-8's merge on Monday's line; this branch reads it and does not re-implement it.
- **The reaction** is the close before the report date to the close after it, the Weekly's earnings block's own rule. It is read from the earnings writer's events and the stored closes.
- **The store is opened read-only** (`mode=ro`), so a missing file reads "not stored" and nothing is created.
- **The hook** is one line after `earnings_row()` in `ahead.build`, lines B's branches did not change.
- **Fixtures (C):** the words by hand; reactions +5.0%, −4.0% and +3.0% from fixture events and closes, which reads "elevated" against ±6.0%; a missing store.

### Registry, catalogue and units

- `chain.options_volume` (count) and `chain.atm_iv_front` (vol_pct, series kind volatility), source `chain_capture` (declared in `source_registry.yaml`, allowed to the daily cascade and the Weekly);
- the catalogue's `altdata.chain_metrics` line;
- display labels for both keys;
- CLAUDE.md's count is now ninety-eight code gates.

### Gates run locally

| Gate | Result |
|---|---|
| `validate_opening_setup` (new) | 23/0 |
| `validate_vol_event` | 50/0 |
| `validate_a43_render` | 46/0 |
| `check_registry` | OK |

**What `validate_opening_setup` holds:**
- no new code names the vendor's source id or a vendor key (it greps the new module and this branch's added lines);
- no table or config carries a score or a weight;
- no new by-hand key;
- no model or network import;
- neither Weekly builder session B is fixing is touched.

Everything else is CI's.

### CI for this branch

| Commit | Run | Result |
|---|---|---|
| `5594468` (part 0) | 39175949352 | **success** (read on a45) |
| `e62c828` (part 1) | 39176741863 | **success** (read on a45) |
| `9f0ee8e` (these notes) | 39176831103 | queued at a45's one read |

These rows were filled in on a45-opening-setup-2, which merges after this branch, so a44's tip did not move.

---

## What waits

**The second half, a later paste:**
- OS-8, the setup profiles;
- OS-9, the OI-build table ("largest OI builds, side unknown");
- OS-4 and OS-5, the labelled put-volume proxies.

**A tape:** side classification (who bought, who sold). Our chains carry OI and volume, not trade sides.

---

## Box commands, for the operator

Run these inside a window, after Thursday's merge (22 Oct): weekdays 09:05–15:40 or 17:20–23:30 ET, never 16:00–17:20. I ran none of them.

```bash
# Thursday evening, first item of the box sheet (ruling 3):
systemctl --user enable --now chester-vendor-chains.timer     # Friday 16:31 is its first capture

# OS-10's history from the captures already on disk (once; idempotent):
cd ~/chester-reports && git pull --ff-only
.venv/bin/python -m altdata.chain_metrics backfill-names --days 60 --dry-run
.venv/bin/python -m altdata.chain_metrics backfill-names --days 60
```

**The first anchor with the gauge is Friday 23 Oct at 07:00.** It reads Thursday's settle and prints "awaiting (n=\<k\> of 20)" until the scorecard holds 20 sessions of the regime.

**The first Weekly with the most-active table is Sunday 25 Oct.** Its dry run is yours.

---

## Files shared with the open branches

**weekly-fixes-9 (session B's Weekly builders).**
- **Shared files:** `CLAUDE.md`, `Makefile`, `config/catalogue_commands.yaml`, `config/display_labels.yaml`, `daily_cascade/ahead.py`, `metrics_registry.yaml` and `source_registry.yaml`.
- **A read-only trial merge finds no conflicting file that a43-render's tip did not already have.**
- In `ahead.py` my one line sits after `earnings_row()` in `build()`, away from B's `straddle_expiry` and `why_of` hunks.
- I did not touch `weekly_stack.py` or `weekly_sections.py`.

**lenses-group-b:** it also shares `morning_payload.py` and `morning_render.py` (a one-line hook each), and `ahead.py`. No new conflicts.

**weekly-fixes-8:** the same as weekly-fixes-9.

---

## Needs you

1. **OS-10's universe is the 17 captured names, not the paste's 29.** Only the options universe (SPY, QQQ, IWM, the 10 single names) and the paper bid's four have captured chains. Widening the capture is a box and budget question.
2. **OS-3 prints only on an item-52 event day,** because it lives in item 52's lens table, as specified. If the vol-regime lenses should print every day, that is a placement ruling, for example in the anchor's mechanics block beside the gauge.
3. **The gauge uses the last close, not a pre-market level.** A pre-market version needs the futures-to-SPY conversion.
4. **The front month is the nearest third Friday at least 7 days out.** That is session-set; tell me if "front month" should mean the first expiry of any kind.
5. **OS-10's history starts when the backfill runs.** Until then each rank prints n=1 ("one reading") with its window.
6. **The drafts for your accept-all** are unchanged from a43: the six ST-8 gate statuses, the SR-21, SR-22 and two FRED notes, and the Doctrine rule proposal.
