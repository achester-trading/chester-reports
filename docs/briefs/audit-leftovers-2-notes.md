# audit-leftovers-2: the 14 Oct audit's leftovers, part 2, and Batch 5's ledgers (17 Oct 2026)

**What it builds on, and the merge order.** Branch `audit-leftovers-2` was cut
from the tip of `meme-ingest-ledgers-1` (`806cffb`). It is my own line and carries
everything below it. It **merges after `meme-ingest-ledgers-1`, in the second
stitched chain.** Not merged, not deployed, nothing run on the box. Every commit
is authored with the GitHub no-reply address passed through `git -c`; the shared
`.git/config` is untouched.

## Step 0

**CI for meme-ingest-ledgers-1: run 39081299646 on `1231cc4` passed, 103 of 103
jobs** (94 code gates, 7 data gates, setup and summary). The two runs before it
failed one gate each, validate_lenses, on the vp-1 families; `1231cc4` fixed that.
The read is recorded in that branch's notes (`806cffb`). Nothing of mine was
failing.

**Conservative readings taken.** The previous needs-you list is not ruled yet.
Where an item touches this paste:

1. **Pass rules are not pre-registered.** 17b and 19b report "no gate in the
   order" and grant nothing, the same as last night's five.
2. **Item 36's measure, the item-25 quadrant and the missing writers** do not
   touch this paste. Nothing changed for them.
3. **The source tier.** The order asks for the tier to decide between two sources
   "at the same as-of". I applied it only there: two sources sharing one
   period's newest instant. The architecture's broader rule, that a lower tier
   never overwrites a higher one, would also let an older higher-tier vintage
   beat a newer lower-tier one. That changes more reads, so I did not apply it.
   It is listed under needs-you.
4. **The source-id refusal stops at the history.** Nothing stored is rewritten,
   and no alias is invented for strings the box's store has not shown.

**A fix to last night's work.** Four store keys in the 30b, 35b and 36b
mappings were guesses that this line's registry does not hold:
- `fred.z1_household_equity_share` (30b);
- `fred.ppi_fd_core_ex_trade` and `fred.ulc_nfb` (35b);
- `redfin.months_of_supply` (36b).

Their writers are on the unmerged st-r5 branches. Each is now `None`, so a
`--source store` run names the missing key and refuses, instead of looking up a
key that does not exist. The public runs are unchanged.

## Part 0: the audit's leftovers

### 1. The outlier and cross-source marks

AUD-3c had already built the check (`altdata/quality.py`), but it was read-only
and ran only inside the close. This branch adds:

- **`python -m altdata.quality record`**, run after the EOD pass's price and FRED
  pull (`scripts/run_eod_cron.sh`, after the volume profile) and after the 06:45
  FRED pull (`scripts/fetch_overnight.sh`, after the loggers).
  - Each flag becomes one row in **`data_quality_flags`**, keyed by day, kind and
    key, with its reason.
  - Each run writes a row in `data_quality_runs`, so a clean day reads "0
    outliers" rather than "no record yet".
  - Both tables sit in the store's database. They are not `observations`, and
    they are written through `open_writer()`. The flags table refuses UPDATE and
    DELETE.
  - The run log lists each mark.
  - **A flagged value is never altered, dropped or withheld.** The gate checks
    the observations byte for byte.
- **`python -m altdata.quality outliers`** prints "data check: n outliers on D
  (keys)". The freshness check prints that line, and the heartbeat carries it as
  `quality=<n>`: a warning, never a verdict or an exit code.
- **The FRED blocks.** `fred_6e` (25 series) and `fred_releases` (45) joined the
  pull after AUD-3c listed its blocks, so 70 FRED series were unchecked. They are
  in now.

**Session-set values** (`config/data_quality.yaml`):

| Setting | Value |
|---|---|
| Multiple | 6 standard deviations of the key's own last changes |
| Window | 60 changes |
| Per family (`outliers.families`) | price, rate, spread, release, quantity, conditions and ratio, each 6 and 60 |
| Change measure | each key's own delta rule: log for a price, a difference for a rate or spread, the move screen's pinned log basis for the vol indexes |
| ^TNX against DGS10 | tolerance printed in bp; floor 1 bp |
| ^VIX against VIXCLS | floor 0.01 points |
| ^TYX against DGS30 | kept from AUD-3c |

On the per-family lines: no family differs today. The delta rule already differs
by family, so one multiple compares across them. A family that needs its own
number gets it on its line, with a reason.

The pair tolerances stay as ruled on 15 Oct. The VIX's tolerance is the measured
one. ^TNX's and ^TYX's are **measured on the box after the price backfill and
the FRED history run** (week of 19 Oct; the command is in
`docs/briefs/aud-3c-notes.md`). Until then those two pairs print "not measured"
and never mark.

**Fixtures** (`tools/validate_outliers.py` group A). The bad fixture marks four
things:
- a 10σ jump on SPY;
- a split-like halving on QQQ;
- ^TNX 30 bp from DGS10 against a 5 bp fixture tolerance, as a pair mark;
- the same ^TNX print as a 10σ move on its own history.

The normal fixture marks none. A second record writes nothing.

**The ZEC logger's unfinished day was already fixed by aud-1 (5d).**
`shielded.py` drops the unfinished UTC bar through
`yfinance_source.drop_incomplete_bars`, the price feed's bar-finished rule.
Nothing changed here; group E pins it.

### 2. Registered source ids

**The read path already held the mapping, so there is no migration.** AUD-3a's
`source_ids.canonical()` reads old strings through:
- `source_registry.yaml`'s `stored_aliases`;
- the `<id>:<variant>` rule.

The history is never rewritten.

**The writes.** A store opened through `observations.open_writer()` (every
scheduled writer) refuses the whole write when any row's source is not a
registered id or `<id>:<variant>`. It raises `observations.UnregisteredSource`,
naming the string. A declared alias is not writable: aliases read history, and a
writer writes the id. A gate's own fixture store, opened directly, is not
refused.

**The writers today: every literal source resolves.** Group C scans three forms:
- `"source": "..."` in rows;
- `SOURCE = "..."` constants;
- `db.write(..., source="...")` probe rows.

It covers every writer module under `altdata/sources/` and `altdata/loggers/`,
plus every `altdata/*.py` that opens a writer. That is 71 strings, all
registered. The dynamic ones are:
- prediction markets' `<venue>` and `<venue>:backfill`;
- the CSV store's dual write of `fred`;
- the crypto basket's `alt_asset:<family>`.

All of those resolve. The `fed_calendar`, `fred_releases`, `treasury_upcoming`
and `voices_scan` strings are event rows (`events_ingest`), not observations.

**Polymarket.** Its rows carry their own registered id, `polymarket`, under
their own instruments. Every pm.* metric the venues write declares
`sources: [kalshi, polymarket]`. `pm.implied` stays Kalshi-only as aud-3a
pinned it: it is reserved, and nothing writes it.

### 3. The source tier in the as-of join

**When two sources hold one period at the same newest instant, the higher tier
wins.** This applies in `as_of()`, `latest_as_of()` and the row cache.

- **Tier order:** `source_registry.yaml`'s own vocabulary: A0, A1, B, C, D, E,
  then `derived`. A string on no list ranks last.
- **Equal tiers** keep both rows, as the join did before.
- **A newer vintage still wins** over an older one of any tier.
- **The choice is shown.** The kept row carries `tier` and `tier_over` (what it
  was chosen over), and the choice is logged.
- **`python -m altdata.observations as-of KEY [--db PATH]`**, a read-only
  command, prints which source was chosen.

**The fixture** (group D): `fred.vix` holds FRED (A0) and Yahoo (C) at one
instant. The join returns FRED's 20.5 "chosen over yfinance (C)". A newer Yahoo
vintage the next day still wins. Two derived sources keep both. The row cache
answers what the query answers.

**What changes on the fixture store: nothing.** On the fixture, Kalshi and
Polymarket rows sit under their own instruments, so the tier rule does not
change either read. The Polymarket-under-Kalshi finding was a registry
declaration (the pm.* `source: kalshi`), which aud-3a corrected with `sources`;
no as-of read mixed the two. No gate fixture held two sources at one instant
before this branch, so CI's report and stack gates are the check that nothing
else moved.

### 4. Call sites onto the Security Master

**Moved: the yfinance basket and the crypto basket.**
- `yfinance_source.pull()` takes every store key from
  `resolve_basket(SYMBOLS)`, the master's resolver, by Yahoo id.
- `pull_crypto_basket()` does the same through `pull()`.
- `instrument(symbol)` returns the master's id, store key, asset class, currency
  and exchange.

`SYMBOLS`, `CRYPTO_BASKET` and `CONTINUOUS_SYMBOLS` are now the master's seed.
A symbol the master cannot resolve keeps its seed key and logs an error, so a
capture is never lost to a reference gap.

`tools/validate_security_master.py` group M holds the agreement:
- all 106 SYMBOLS and the 12 crypto names resolve to their seed keys;
- `EARNINGS_SYMBOLS` is exactly the basket's equities by the master (29);
- every continuous symbol is crypto or fx.

**One rule stays the module's own: `CONTINUOUS_SYMBOLS`.** "Trades every day" is
not an asset class: IDR=X and TRY=X are fx and are not continuous.

**Left listed, each with why** (from aud-3b's map table):
- **`OHLC_KEYS` and `VOLUME_*_KEYS`** derive from SYMBOLS, so they inherit the
  move.
- **`daily_cascade/consistency.py` `ALIASES`.** `y10` maps to two store keys,
  Yahoo's and FRED's. That is a two-source alias, not an identity.
- **The config universes:**
  - the tape in `config/reporting_stack.yaml`;
  - `config/correlation.yaml`;
  - `config/horizon_charts.yaml`;
  - the Book B scanner's map.

  These are YAML that sessions edit by hand. Moving them changes their file
  format, so not mechanically.
- **`fx_charts.CATALOG`.** A FRED id and/or a Yahoo id per chart. It is behind
  its own generator rework (CLAUDE.md, Known cleanup).
- **`fundamentals.TICKERS`, `proshares.FUNDS` and `ishares_trusts.TRUSTS`.**
  Issuer-file names, not Yahoo ids.
- **`edgar.universe()`.** SYMBOLS less `^`, `=` and `-`, which drops BRK-B
  (aud-3b's disagreement 3). Moving it would change EDGAR's universe, which is a
  ruling, not a mechanical move.
- **The meme loggers' universe** (`consensus.universe()`). That universe is
  chester-meme's interface, so it is out of scope here.

Nothing stored changes.

### 5. The docs and counts

**CLAUDE.md.**
- New counts: **31 official writers, 27 external writers and 7 loggers**.
- The FRED lists are now gated: FRED_6E_SERIES 25 and FRED_RELEASES_SERIES 45.
- Already gated and true: FRED_SIGNAL_SERIES 27 (the audit's 24 was itself
  out of date), 106 market symbols (the audit counted 81) and the FRED pull 199.
- **Gates: ninety-five code gates (ninety-two Python, three shell) and seven data
  gates.**

**The count gate** (`tools/validate_audit_3a.py` group F) now reads all of
these. It also reads the architecture document's store box, whose counts are
checked by the same rule; a stale "27 symbols" there fails.

**The architecture document.** Its "store as built" box gained a dated refresh:
- the FRED pull and the symbols;
- the roster;
- the writer refusal and the tier rule;
- the marks;
- the encrypted, restore-tested backups.

The 4044 and 4133 passages are dated build-chat history and stay as written.

**The README.** Its links all resolve and it prints no counts, so nothing
changed. Nothing else in the papers changed.

## Part 1: Batch 5 Tranche 2, the ledgers

`altdata/ledgers/` has gained `st_r4_17b.py` and `st_r4_19b.py`. Each runs as
`python -m altdata.ledgers run 17b|19b`. Both first editions are **"laptop run,
public sources"**, dated 2026-10-17, each with its episodes CSV. They follow
last night's form: as-of, window, n, the statistic, the pass rule as the order
states it, the verdict that rule gives, and a one-line rights consequence. **The
order states no pass rule for either ledger.** Each says so and grants nothing.

| Item | Sources (point in time) | As of | n | What it found |
|---|---|---|---|---|
| **17b** net liquidity against the S&P | FRED WALCL, WTREGEN, RRPONTSYD (current vintage; the H.4.1 legs are rarely revised, ALFRED not used); Yahoo ^GSPC (not revised). Each week is read from the Friday close after Thursday's 16:30 release, never the Wednesday | 2026-10-14 | 1,218 weeks (2003-03 to 2026-07; 94 non-overlapping) | **No standing signal.** The 13-week change against the S&P's next 13 weeks: r +0.09 (non-overlapping +0.09). The popular same-weeks read: r −0.15. Over 2022–23 both were strongly positive (+0.52 next, +0.58 same): the "mixed record" is a regime, not a rule. The quintiles of the change are flat (+2.66% to +3.28%, against +2.57% for every week). Now: $5,872bn, 13 weeks −$115bn, TGA-led. |
| **19b** MOVE-VIX divergence, replicated | Yahoo ^MOVE (from 2002-11), ^VIX, ^GSPC (none revised); 19a's z (252 sessions, day included, sample sd) and percentiles | 2026-10-16 | 39 complete non-overlapping watch-tier episodes (40 in all); 27 strong (28) | **The study does not replicate.** Watch tier: VIX higher within 1–3 months in 24/39 (62%), against 68% on every day; S&P lower at 3 months in 13/39 (33%), against 29%. Strong tier: 19/27 and 9/27, with a mean 3-month S&P of +2.24%; the study's "every case negative" fails here. The study's 12, 10/12 and 9/12 count from 2000, before this window begins (2003-11). Now: MOVE z +2.19, VIX z +0.58, no tier (the VIX's z is above 0.4). |

`tools/validate_ledgers_b6.py` gains groups I and J (37/0). Each reproduces a
hand figure:
- 17a's +$215bn = Fed +10, TGA +200, RRP +5, led by the TGA;
- the Friday-after-Thursday release lag;
- 19a's tier boundaries at +0.51/+0.50 and +1.01/+1.00, and the VIX at 0.40;
- the z of 1..5 at +1.2649;
- 63-session non-overlap;
- the outcome rules.

The existing groups G and H cover all seven studies: the verdict is the order's,
a ledger without as-of, window or n is refused, and the package never opens the
register, so the decision tables cannot be touched from it.

**ST-R4.20a and 20b are listed, not built: their preconditions are not met.**
- **20a** (the Treasury reaction-function sub-state and its ledger scaffold) is
  "a `rates.driver` sub-state beside the item-7 market-cap mechanism (R28)". The
  `rates.driver` sub-state does not exist. It was withdrawn on 30 Sep after
  failing its calibration gate twice (market-state v1.11 and v1.12 retired;
  `config/market_state.yaml`). Cross-item ruling 1 also orders "attribution
  extensions first", and those are on `st-r4-tranche-1`, which is not on main or
  in this line.
- **20b** (corporate interest burden: net interest over EBIT, S&P
  ex-financials, plus the refinancing wall) falls under the same cross-item build
  order (the 10y attribution is the arbiter for item 20). Its own text carries a
  verify that is still open: "if XI doesn't already wire it", with the series "to
  confirm" and S&P DJI aggregates "if free". I took the conservative reading:
  listed, to build after st-r4-tranche-1 merges and the series is confirmed.
- **Out, as the paste says:**
  - 16c rides Thread D's on-chain build;
  - 25a waits for the register's expression fields;
  - 19c waits for "T&B full" and your queue-order ruling.

### Register lines, drafted under rule 31 (for you to file; I wrote none)

```
ledger: docs/ledgers/st-r4.17b-ledger-2026-10-17.md, NO GATE IN THE ORDER (base rate recorded; r +0.09 with the next 13 weeks, n 1218 weeks; +0.52 over 2022-23) -- laptop run, public sources
ledger: docs/ledgers/st-r4.19b-ledger-2026-10-17.md, NO GATE IN THE ORDER (base rate recorded; watch 39 episodes, VIX higher 62% vs 68% base, S&P lower 33% vs 29%) -- laptop run, public sources
```

### Box commands to re-run them after Thursday's merge

On the box, in the checkout, inside the windows. Each run writes a new dated file
and never edits the laptop's.
```
.venv/bin/python -m altdata.ledgers run 17b --source store
.venv/bin/python -m altdata.ledgers run 19b --source store
```

The store keys are:
- 17b: `fred.fed_balance`, `fred.tga`, `fred.rrp`, `yfinance.mkt_gspc`;
- 19b: `yfinance.mkt_move`, `yfinance.mkt_vix`, `yfinance.mkt_gspc`.

A store run reads only the history the store holds. Until the FRED history run
and the deep price backfill (box steps after Monday's merge) have filled it, the
store's window is shorter than the public one. Use `--source public` (the same
command without `--source store`) for the full window.

## Box steps (Ari's; nothing here was run on the box)

1. **Before Thursday's merge, list the stored source strings that are off the
   list:**
   `.venv/bin/python -m tools.check_store_registry --db data/chester.db`
   (read-only). List 4 names each one, with its row count and example keys.
   Those are history and read through aliases. The refusal applies only to new
   writes, and every writer's literal source is registered (group C). A string
   listed there that a writer still writes would mean a dynamic source the gate
   cannot see: tell me before the merge.
2. **After the merge, nothing needs enabling.** `quality record` runs inside the
   EOD and 06:45 wrappers at their next run, and creates its two tables on the
   first record. The heartbeat reads `quality=none` until then.
3. **The week of 19 Oct**, after the price backfill and the FRED history run:
   measure the ^TNX and ^TYX tolerances (`python -m altdata.quality measure`, as
   in aud-3c's notes) and send me the figures to commit.

## Leftovers still open after this paste

- **Box steps after Monday's merge:** the FRED history run and the deep price
  backfill. Then the two pairs' tolerances.
- **The broader tier rule** (a lower tier never overwrites a higher one across
  instants): your ruling.
- **The call sites left listed above.** The config universes and `edgar.universe`
  need a ruling; the rest move when their own work comes up.
- **The st-r5 series' store keys** for 30b, 35b and 36b, once those writers
  merge.
- **ST-R4.20a and 20b,** after st-r4-tranche-1 merges and the 20b series is
  confirmed.

## Files this branch shares with open branches

- **Session A, gtm-core-1 and gtm-core-2.** Neither is on the remote, so I could
  not diff them. Most likely to meet them:
  - `CLAUDE.md` (the gate count, now 95/92/3 and 7; the roster and leftovers
    paragraphs);
  - the `Makefile`'s gate list;
  - `altdata/observations.py`, especially `write_many`, `as_of` and
    `latest_as_of`;
  - `altdata/derived.py` (RowCache's return);
  - `altdata/feeds.py` (the freshness print);
  - `altdata/sources/yfinance_source.py`;
  - `scripts/check_heartbeat_cron.sh` (the log line and the status line gain
    `quality=`);
  - `scripts/run_eod_cron.sh` and `scripts/fetch_overnight.sh`;
  - `tools/validate_audit_3a.py`.

  Where gtm-core changed one of these, take both sides and recount the gates.
- **Monday's chain:** untouched by this branch.
- **st-r4-tranche-1 and 1b** (mine, unmerged). Read for 17a's and 19a's
  definitions only; no file of theirs is changed here.
- **chester-meme:** not touched.

## Needs you

1. **The tier rule's reach.** It currently applies only within one instant. Do
   you want the architecture's full rule, where a lower tier never overwrites a
   higher one even with a newer vintage?
2. **Pass rules, still open from last night, now for seven ledgers.** 17b and
   19b come back with clear base rates:
   - **17b:** no standing relation, outside 2022–23.
   - **19b:** the study does not replicate on 2003–2026.

   Do you want gates pre-registered? A candidate for 19b, which I have not
   adopted: the watch tier's VIX-higher share beats the every-day base by 10 pp
   on n ≥ 20. This ledger fails it (62% against 68%).
3. **19c** waits for "T&B full" and your queue ruling. On this ledger, the case
   for the queue is weak.
4. **20a's parent is withdrawn.** Re-scope 20a without `rates.driver`, or hold
   it?
5. **Last night's items stand:** item 36's measure, the item-25 quadrant, the
   OECD CLI and full-BIS writers, and the git email.

## CI

- Part 0, run 39087884402 on `c0d5559`: in progress at the time of writing; read
  below once it completes.
