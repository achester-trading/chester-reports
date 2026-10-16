# ST-R6.45: the standing three-timeframe ES block (session notes, 16 Oct 2026)

**This branch, `st-r6-es-block`, is cut from the tip of `aud-3b-security-master`
(`2fb1048`), the last branch of the chain session A stitched on 16 Oct. It builds
on that chain: it needs VP-1's volume profile (`altdata/volume_profile.py`), which
is on that chain and on no main yet. It merges after `aud-3b-security-master`
and never before it.** Branch only: pushed, not merged, not deployed, nothing run
on the box.

Source: Batch 6 change order, item 45 (ruled 15 Oct 2026), its verify items (§8
items 9 to 11) and §11 filing notes 1 and 2
(`change-order-signal-triage-batch-6-2026-10-15.md`, filed by session A on
`docs-batch-6`). ST-R6.45c, the conversion of dealer levels to ES, waits for the
6b engine and is not built. Report only: nothing here generates a setup.

This file also reports Part 0 of the same paste (chester-meme's Brookfield
restriction): see the last section.

## What it builds on, and what is new

| Reused, unchanged | For |
|---|---|
| The `bars` table and `BarStore` (`altdata/bars.py`): ES=F 5-minute bars for the full futures session (18:00 to 17:00 ET) from the 16:10 feed and the 60-day backfill | every window's bars, through the table's as-of read |
| `bars.session_window("es", day)`: the futures day's 276 bars | each session's expected count |
| VP-1 (`altdata/volume_profile.py`): `profile`, `daily_profile`, `summary`, `trailing_sessions`, `complete_share` | POC, value area and nodes in every window. This block never bins volume itself |
| `narrative.generate()`, its `split` hook, the stack's system prompt, style rules, retry prompt and guide (`daily_cascade/stack_prose.py`) | the read |
| `model_meter.scope` | the read's calls are metered under the anchor's or the close's run |
| The close's Mechanics section and its sub-sections; the anchor's render | where the block prints |

| New | What |
|---|---|
| `config/es_block.yaml` | every setting, with the session-set ones marked |
| `altdata/es_block.py` | the contract, the roll adjustment, the three windows, the indicators, the levels, the ledger (`es_contract`, `es_ledger` tables) |
| `altdata/bars.py` `pull_overnight()` and `python -m altdata.bars overnight` | the 06:45 pull (45a) |
| `daily_cascade/es_read.py` | the read and its lean, and the print in all three reports |
| `tools/validate_es_block.py` | the gate, 68 checks on fixtures, now in the Makefile |
| `scripts/fetch_overnight.sh` | one step after the status line: `altdata.bars overnight` |
| `daily_cascade/stack_close.py`, `morning_payload.py`, `morning_anchor.py`, `morning_render.py`, `weekly_stack.py` | the wiring |
| `daily_cascade/stack_render.py` | a sub-section's `lead` paragraph prints before its tables (HTML and Markdown) |
| `daily_cascade/stack.py` `section_words` | a `lead` counts in the prose budget, because it is model prose |
| `config/catalogue_commands.yaml`, `CLAUDE.md` | the catalogue line, the gate count (85 code gates, 82 Python) and one paragraph |

## The items and their fixtures

**ST-R6.45a: the morning pull and the contract.** `python -m altdata.bars
overnight` runs in the 06:45 job, right after the overnight fetch's status line
and ahead of the long correction pull. It fetches ES=F's 5-minute bars from
18:00 ET the evening before. It keeps every bar that had closed by the fetch and
drops the one still open. Bars are stamped at the fetch and written
INSERT-OR-IGNORE, so the 16:10 feed later adds the rest of the day without
moving an earlier stamp. It records the contract in force in `es_contract`: CME's
rule, its roll date, and the contract Yahoo reports for ES=F
(`Ticker.info["underlyingSymbol"]`) when Yahoo serves one.
*Fixtures (group E):* a fake source spanning 17:00 ET to a bar still open. 153
bars kept, starting at 18:00 ET, one dropped, all stamped at the fetch, and the
contract row is `ESZ6 / 2026-12-10 / ESZ26.CME`.

**The contract rule.** ES lists H, M, U and Z contracts expiring on the third
Friday. CME's roll date is eight days earlier, and a session dated on or after it
belongs to the next contract. So ESZ6 (expiring 18 Dec 2026) rolls on Thursday
10 Dec, and ESH7 rolls on 11 Mar 2027. A contract Yahoo reported at a pull, as
recorded by that pull, outranks the rule for that session: data beats the
calendar. *Fixtures (group A).*

**The roll in the bars.** ES=F is unadjusted, so the first session after a
switch opens at the new contract's price. That jump is the calendar spread, not a
move. Bars before the switch are shifted by the gap between the last bar before
it and the first bar after it (additive). The roll and its gap print beside the
window. A ledger row printed under one contract and scored under the next is
`not_scored`. *Fixtures (group D):* flat at 7800 under ESZ6 and flat at 7850 under
ESH7. The swing window reads a +50 roll, a flat trend and zero MACD, where an
unadjusted read would show a 50-point rally. When Yahoo's recorded contract says
the switch came a session later, the adjustment moves with it.

**ST-R6.45b: the three windows,** computed in the box, point in time:

| Window | Bars | Price line | Profile | MACD (12,26,9), money flow (14) |
|---|---|---|---|---|
| session | the futures day's 5-minute bars, so far at 07:00 | VWAP | VP-1 at 5 bps | over the day plus 1 warmup session |
| swing | 5 sessions on 2-hour bars built from the 5-minute bars, anchored at 18:00 ET (12 a day, the last one hour) | trend line | VP-1 from the 5-minute bars beneath | over the window plus 10 warmup sessions of 2-hour bars |
| position | 63 sessions on daily bars built from the same table | trend line | VP-1 from daily bars at 25 bps, "approximated from daily bars" | over the window |

Each window is absent with its reason when its bars fall short of the bars
table's `complete_share` (0.90), the same rule VP-1 uses. The position window
counts only the sessions whose own bars reach the share. It prints "n of 63", and
it is absent below 35 sessions, the minimum MACD needs. The levels that matter
are the three nearest above and the three nearest below the last price. They are
drawn from every window's POC, value area, nodes, VWAP, trend value and range
edges, plus, at 07:00, the prior full session's POC and value area. Levels within
two points merge, and every source is named.
*Fixtures (group B, by hand):* EMA(3) of 1..5; MACD of a flat series; money flow
on three bars (41.12); VWAP (17.5); the trend line through 1, 3, 5, 7. *(Group C,
a synthetic ES day):* 276 bars, open 7700, high 7769.50, low 7699.50, last 7769,
+69, VWAP 7734.54 (worked in the gate's comments); 60 two-hour bars in the swing;
the position window at 40 of 63, and absent at 30; the level merge on a hand-built
book.

**ST-R6.45d: the block.**
- **07:00 anchor**, a section of its own before the prior close's dealer surface.
  It shows the overnight session so far, the prior full session's value area and
  POC as reference levels, and the day's levels. A block that is not "ok" adds
  the anchor warning `ES block partial|absent: <reasons>`.
- **16:45 close**, a sub-section of Mechanics. It shows the full session (through
  the 16:10 pull, as every close does). "Since 07:00" gives the price against
  07:00 and the morning's levels and lean, scored so far, in memory, with nothing
  written. Then the levels for tomorrow.
- **Phone layout:** the read first, then the levels table (above from far to
  near, "price now", below from near to far), the windows table, then the lines:
  the contract and its roll date, any roll with its gap, any absent window, and
  `dealer levels in ES: after the 6b engine`.
- **The read** goes through `narrative.generate()` with the stack's system
  prompt, print precision, the numeral audit, markdown refused, the stack's style
  rules, and a forecast rule ("will hold", "should break" and the like are
  withheld). There is one retry on a refusal, as every stacked section has. The
  reply's last line, `LEAN: up|down|none`, is split off before the audit and
  returned beside the prose, so the ledger never parses prose. A reply without
  it is withheld. A withheld read prints its reason and logs no lean. The anchor
  makes the call from `_es_read()`, beside its scan, and the close makes it inside
  its prose step. No new model, client or path.
- **Charts:** none added, so the close's chart budget is unchanged.
- **The Weekly:** a Mechanics sub-section with the position window and the week's
  ledger (levels held, broke and untested; leans resolved, unresolved and not
  scored; rows pending).
- **Both anchors always publish.** The block is a section of the two reports that
  always run, never a conditional report.

*Fixtures (groups F and H):* the stub read publishes with `lean: up`. With no LEAN
line, with a forecast, or with a figure not in the data, it is withheld. The read
prints before the tables in HTML, in Markdown and in the 07:00 section, and the
lead counts in the budget. The Weekly's panel prints `Position (3 months, daily),
n=40 of 63` and the ledger rows.

**ST-R6.45e: the ledger.** `es_ledger` lives in the bars table's database. Each
printed level (label, ES level, side, price at print) and each lean is logged
unscored by the anchor and by the close, idempotent per (session, slot, kind,
label). The close scores every due row first: the 07:00 rows of its own session
and the previous close's rows. It reads only bars that opened after the print,
and a scored row is never rewritten. *Fixtures (group G):* a held, a broken and an
untested level, and a resolved and an unresolved lean, on one target session.
Also: a re-run writes nothing, a scored row stays as scored, a withheld read logs
no lean, a session without bars waits, and the summary counts.

## The session-set choices, for Ari

All of them are in `config/es_block.yaml`, marked `session-set`.

1. **Trend line:** a least-squares line through the window's closes, one point per
   bar: every 2-hour bar of the five swing sessions, and every daily bar of the
   position window. It prints its value at the last bar, its slope per bar and
   its R². I chose it over a moving average because it states one direction and
   its fit for the whole window, and over a channel because it needs no
   judgement.
2. **Ledger, level:** *tested* means a bar's range came within 1.0 point (four
   ticks). *Broke* means a 5-minute bar **closed** beyond the level by more than
   0.5 point (two ticks) on the far side from the price at print. *Held* means
   tested with no close through. Otherwise the level is *untested*. A close, not a
   wick: a wick through that closes back is the level holding.
3. **Ledger, lean:** *resolved* means the next session's last bar closed beyond
   the price at print, in the lean's direction, by at least 0.25%. Otherwise the
   lean is *unresolved*. A lean of none is logged and not scored.
4. **Ledger, timing:** a row is scored at the first close that has its target
   session's bars, so the last 50 minutes of the futures day (16:10 to 17:00) are
   not seen. Only bars after the print count. A row whose print and target sit on
   different contracts is `not_scored`.
5. **Roll:** an additive shift by the gap at the switch; CME's rule unless Yahoo's
   recorded contract says otherwise.
6. **Levels:** three above and three below; merged within 2 points; the range
   edges (swing and position high and low) are included, so a new high still has
   a level above.
7. **Warmups:** 1 session for the session window's indicators, 10 for the swing's,
   none for the position's.
8. **The read:** at most 140 words. Run-away guard 1,500 characters.
9. **The budget:** the read counts in the close's prose budget (about 140 words),
   because it is model prose. If the close runs over, the paragraph guard trims as
   it already does.

## Verify items

- **9. The free ES intraday source and its depth from the VPS.** Answered from
  the repo, not from the box (sessions stay off the box). The source is yfinance
  ES=F 5-minute bars, already in use by the 16:10 feed and the T2.2 backfill, and
  Yahoo serves them for the last 60 calendar days only (`altdata/bars.py`
  backfill). So the box's own record is the history: about 41 sessions from the
  backfill, plus every session since. The position window prints "n of 63" until
  63 sessions are stored. If the backfill ran on 5 Oct, that is in late December;
  the `show` command below prints the actual n. Free alternatives considered:
  Stooq and FRED carry no intraday futures, and CME's delayed quotes are not
  bars. The one longer source is IBKR's historical bars through the Gateway (6b),
  which is a source change for 6b, not this block. Box check: command 2 below.
- **10. Basis convention** (belongs to ST-R6.45c, not built). This block uses the
  front month only, and the contract and roll date are recorded every morning, so
  45c's basis has its contract to hand. Its roll rule is CME's
  (eight days before expiry), overridden by what Yahoo reports.
- **11. 07:00: overnight only, or the prior day's profile too?** Both, as
  proposed. The session window is the overnight session so far, and the prior
  full futures session's POC and value area are printed as reference levels and
  enter the day's levels.

## A sample of both anchors' block, on fixtures

A synthetic tape near 7790, 45 sessions stored, built by the gate's fixtures. The
read is written at run time by the narrative step; here a placeholder stands in.
The table rows print as tables in the reports.

```
07:00 (2026-10-16T11:00Z)
ES — three timeframes
[the read]
  prior session value-area high / position high / swing high | 7,803.29 | +8.18
  position trend line | 7,795.48 | +0.37
  price now | 7,795.11 | –
  swing high-volume node / session value-area high / swing value-area high | 7,791.67 | -3.44
  prior session POC / swing high-volume node | 7,786.00 | -9.11
  position value-area high / session VWAP / swing trend line | 7,780.74 | -14.37
  Session (5-min) | 7,795.11 | VWAP 7,781.01 | 7,754.00–7,792.00 (7,771.00) | -1.51 falling | 17.6
  Swing (5 sessions, 2-hour) | 7,795.11 | trend 7,781.19, +0.18/bar | 7,754.00–7,792.00 (7,767.00) | +2.33 rising | 61.9
  Position (3 months, daily), n=45 of 63 | 7,795.11 | trend 7,795.48, +2.87/bar | 7,670.00–7,780.00 (7,755.00) | -1.72 rising | 70.5
  Prior full session | 7,774.23 | – | 7,764.00–7,802.00 (7,785.00) | – | –
Contract in force ESZ6 (CME's roll rule); rolls to ESH7 on 2026-12-10.
Position window spans the ESU6 to ESZ6 roll on 2026-09-10: earlier bars shifted -33.79.
Position value area approximated from daily bars.
dealer levels in ES: after the 6b engine

16:45 (2026-10-16T20:45Z)
ES — three timeframes
[the read]
  position high / swing high | 7,803.94 | +5.48
  price now | 7,798.46 | –
  position trend line | 7,795.77 | -2.69
  session value-area high / swing high-volume node / swing value-area high | 7,787.00 | -11.46
  session VWAP / position value-area high / swing trend line | 7,779.67 | -18.79
  Session (5-min) | 7,798.46 | VWAP 7,778.53 | 7,756.00–7,786.00 (7,773.00) | +1.04 falling | 100.0
  Swing (5 sessions, 2-hour) | 7,798.46 | trend 7,780.48, +0.14/bar | 7,754.00–7,788.00 (7,767.00) | +1.48 rising | 53.9
  Position (3 months, daily), n=45 of 63 | 7,798.46 | trend 7,795.77, +2.88/bar | 7,670.00–7,780.00 (7,755.00) | -1.51 rising | 71.4
Contract in force ESZ6 (CME's roll rule); rolls to ESH7 on 2026-12-10.
Position window spans the ESU6 to ESZ6 roll on 2026-09-10: earlier bars shifted -33.79.
Position value area approximated from daily bars.
dealer levels in ES: after the 6b engine
```

On the box, the 16:45 block also prints the "Since 07:00" line and the 07:00
levels' outcomes so far, once a 07:00 print has been logged. The fixture tape
above has no 07:00 print. The -33.79 shift is an artefact of the synthetic tape,
which has no real calendar spread at the September roll.

## Box commands, for Ari to run (nothing here was run on the box)

After the merge, inside the windows. No unit file changed, so nothing to deploy
and nothing to restart: `fetch_overnight.sh` reaches the box at the next 06:45 run
through its own `git pull --ff-only`.

1. The first morning after the merge, the pull's log lines:
   `ssh vps 'grep -A12 "bars: ES overnight start" ~/logs/overnight-$(date +%Y-%m).log | tail -30'`
2. Verify item 9, what the box holds and what the block would print (reads only,
   no fetch):
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.es_block show --slot close | head -60'`
   The position window's `n_sessions` is the depth the box has built.
3. The ledger, after the first close:
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.es_block ledger --sessions 5'`
4. Optional: what Yahoo reports as ES=F's contract today. This is one fetch, so it
   is the operator's:
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.bars overnight --dry-run | tail -20'`

## Files shared with the open branches

Checked against every remote branch ahead of `aud-3b-security-master` on 16 Oct.

| File | Also changed on | Note |
|---|---|---|
| `daily_cascade/stack_close.py` (the close) | none | |
| `daily_cascade/morning_anchor.py`, `morning_payload.py`, `morning_render.py` (the anchor) | none | |
| `daily_cascade/stack.py` | `st-r5-rates` (session A) | mine adds two lines to `section_words` |
| `daily_cascade/weekly_stack.py` | `st-r5-rates` | mine adds one block at the end of `mechanics_week` |
| `Makefile`, `CLAUDE.md` | `st-r5-rates`, `6e-metric-lenses`, `el-1-packets`, `el-2-3-rollup` | the gate list and the gate count: the merge recounts |
| `config/catalogue_commands.yaml` | `st-r5-rates` | one entry, alphabetical |
| `daily_cascade/stack_render.py`, `altdata/bars.py`, `scripts/fetch_overnight.sh` | none | |

## CI

Locally, only the gates this branch writes or changes were run, one at a time:
`tools/validate_es_block.py` 68 passed, 0 failed;
`tools/validate_audit_3a.py` (CLAUDE.md's counts and the catalogue) 83 passed,
0 failed; `tools/check_library.py` 0 failures, 0 warnings. Every other gate is
left to CI. The base, `aud-3b-security-master` at `2fb1048`, is green in CI
(run 38795223151).

**Run 38856776755 (`7254de9`): failed. 89 jobs passed; 3 code gates and the
`gates-passed` summary failed:** `validate_stack.py`, `validate_weekly_complete.py`
and `validate_readability.py`, all with the same `UnboundLocalError` on
`model_meter` in `stack_close.produce()`. The cause was this branch's. `produce()`
carried a local `from altdata import model_meter` near its end, which makes the
name local to the whole function, so the ES read's `model_meter.scope(...)`,
earlier in the function, found it unbound. The fix removes the redundant local
import; the module-level import stands. It was fixed on this branch in the
commit after `7254de9`. The two runs before it were cancelled as superseded.
**Run 38900890862 (`44ab334`, the model_meter fix): failed. 91 jobs passed;
`validate_readability.py` and the `gates-passed` summary failed.** The model_meter
fault was gone; the readability gate's rule "no ISO date outside a table" caught
the ES block, whose absent note and lines printed dates as `2026-09-28` (the
close fixtures store no ES bars, so the block printed its absent reason, naming
each short session). The cause was this branch's. The fix prints every date in
the block's code-written notes and lines as "28 Sep" (readability.prose_date),
tells the read to write dates the same way, and adds the check to
`tools/validate_es_block.py` (69 checks). The fixed tip's run is recorded in
`docs/briefs/st-r4-tranche-1-notes.md` (branch `st-r4-tranche-1`, rebased onto
that tip).
**Run 38904259575 (`4dd24ac`, the ISO-date fix): passed. 93 of 93 jobs green**,
the `gates-passed` summary among them (read once, 16 Oct 2026). This tip is the
one `st-r4-tranche-1` and `st-r4-tranche-1b` are cut from; this notes-only commit
after it is not in them, and it touches nothing they change.

## Needs you

1. **The session-set choices above**: the trend line, the three ledger rules and
   their thresholds, the roll adjustment, and the level count and merge distance.
2. **Yahoo's roll timing.** This block assumes ES=F switches on CME's roll date,
   unless a pull records otherwise. The first December roll (10 Dec) will show
   whether Yahoo agrees: the contract line prints "Yahoo's switch differs" if it
   does not.
3. **The read counts in the close's budget** (about 140 words). Say if it should
   sit outside it.
4. **ST-R6.45c** waits for the 6b engine. Its basis (verify item 10) has the
   recorded contract to hand.
5. **The Brookfield items in Part 0**, below.

## Part 0: chester-meme's Brookfield restriction

**Not delivered from this session. Another session owns it.** I built it on
`build/brookfield-restriction` (chester-meme's rule is that session branches are
`build/*`, which is stricter than the paste's `brookfield-restriction`). The
work: a dated local copy of the complex (roots, name patterns, RA and INF by
name only) with chester-reports' `normalise()` plus the ACT `$` form; migration
`0008_restricted` keeping the export's `restricted` field; the packet stage
refusing before build, validation and write, with `restricted` and `refused`
counted in the manifest's `last_run`; the notes dropping restricted triggers;
`trade add` refusing; and `tests/test_restricted.py`, 34 tests. `python -m meme
validate` passed on that tree at about 00:59 ET (pytest, ruff, rule-version,
schema). chester-meme has no CI.

At about 01:00 ET a second session, `chester-meme-59` (the overnight chester-meme
session, on a brief of its own from Ari), began writing in the same checkout, on
the same branch: a different `restricted.py`, a `0009_restricted_detail`
migration, and changes to candidates, scores and config. I stopped writing there
and told it what I had written. It acknowledged, saved my work as a git stash
("prior-session WIP on main: Brookfield restriction…") and a patch in its
scratchpad, kept `0008_restricted.sql` as written, and is carrying the branch to
its own report (t5d). **Nothing from this session was committed or pushed in
chester-meme.** I applied migration 0008 to the laptop's `store/meme.db` (one
nullable column) so validate's store check would pass.

**The two briefs disagree, and only you can settle it:**
- **Names.** This paste: name patterns ("Brookfield", "Oaktree") and a dated copy
  of `tracked_entities.yaml`. Its brief: never infer from names; the 12 seed
  tickers it names.
- **Coverage.** chester-reports blocks recommendations only; diagnostic and
  tracking coverage stays. Its brief excludes the complex at candidate selection
  and from the boards.
- **The list.** Its 12 seeds lack the BPY family, the notes, OAK, OCSL and BIRET.
  It is putting these points in its own "What needs you".

**Found while copying the rule:** chester-reports' own `register/instruments.py
normalise()` does not handle the ACT preferred form `BPY$A` (it returns `BPY$A`,
not `BPY`). The export still marks those securities restricted by name, but a bare
`BPY$A` at the register would miss the root. I did not touch the register: the
paste forbids it. The fix is one rule for whoever owns the register.

**The contract question** (for both sides): should
`docs/interface/security_master.schema.json` define `restricted` as a field, in
a new schema version (1.1), so that both repositories own it? Today
chester-reports writes it and the 1.0 schema does not define it; chester-meme
reads it as an extra field.
