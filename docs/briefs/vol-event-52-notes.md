# Batch 9 item 52: the volatility event flag and attribution (session A, 17 Oct 2026)

**Merge order: after `6b-dealer-2`, in the second stitched chain.** Branch `vol-event-52` is cut from the tip of `6b-dealer-2` (`ada7cb2`), so it carries 6b parts 1 and 2 and the st-r5 line, and merges after them. Branch-only: nothing merged, deployed or run on the box, and no unit enabled. Session B's crypto-tranche-a branches, Monday's chain, `post-friday-fixes` and chester-meme were not touched.

**The spec** is `docs/change-order-signal-triage-batch-9-2026-10-17.md`, filed on `docs-batch-9` (`e20df42`): sections 2, 3, 4's placement block, 5 and 8's filing notes.

## What it builds

### ST-R6.52a, the trigger (`altdata/vol_event.py trigger`)

**Two-sided, four arms, as ruled** (`config/vol_event.yaml`):
- **One day:** a VIX change of **15%** or **3 points** either way.
- **Five days:** the change past its own **95th percentile** of |five-session change| over **20 years**.
- **A band crossing:** a crossing of an XIII regime band. The bands are the vol dial's (14/20/30, `config/market_state.yaml`), the ones the close already prints, read in place rather than copied.
- **Compression:** within **5%** of the trailing six-month low, held **three sessions**.

**Level and change are separate fields**, each with its 5-year (1,260 sessions) and 20-year percentile.

**The VIX history** joins FRED's VIXCLS (from 1990) with the same-day ^VIX, the same-day value winning a date.

**The event store is point in time:**
- `vol.event_day`, one JSON row per session, fired or not;
- `calc.vol_compression` (1/0);
- a `vol.event_ledger` row per fired event.

Each is observed on the session and available when the close writes it.

### ST-R6.52b, the nine lenses, one line each, eight computed

| Lens | What it reads | Unit and reading |
|---|---|---|
| Spot-vol | SPX (`yfinance.mkt_gspc`) and the VIX | the trailing 60-session OLS beta of the VIX's point change on SPX's % change; the explained share; the residual, the vol bid beyond spot |
| Term structure | VIX9D, VIX, VIX3M, VIX6M | levels and point changes; front-led when VIX9D's change beats VIX6M's by 1+ point, whole-curve when VIX6M moved at least half as far the same way; VIX3M/VIX, contango or backwardation, and its change |
| Tail and vol-of-vol | VVIX, SKEW, the VIX | log changes, the move screen's unit (AUD-3a), each stated; VVIX/VIX |
| Cross-asset | MOVE, HY OAS, crypto DVOL, G10 FX vol | MOVE in log %, HY in bp; systemic when MOVE is up 5%+ or HY 10+ bp; DVOL "awaiting" (`deribit.dvol_btc`, Tranche A); G10 FX vol a listed gap |
| Dealer positioning | the newest settled SPY profile (6b engine) | spot against the zero-gamma level, net GEX per 1% and the gated regime, vanna and charm as sizes, the 0DTE share or "settled, excluded"; inferred, not observed |
| Realised against implied | SPX closes, the VIX | 10- and 20-day realised vol; VRP = VIX less 20-day realised and its change; "a fear premium" or "realised catching up" |
| Breadth | `cboe.cor3m`, `cboe.dspx` (item 18, session B's `st-r4-tranche-1b`) | by key name; "awaiting" until rows are stored |
| Positioning | `cftc.noncomm_net`, instrument VIX | the weekly net and its change. **The CFTC writer already carries VIX futures** (contract `1170E1`, added 3 Oct), so no extension was needed. VIX ETP vega is a listed gap |
| Catalyst | the Phase B scan's stored `press_attributions` for the session | "<outlet> attributed the move to: …", its attribution and never ours; else **"not established"** |

### ST-R6.52c, the block

- **The close.** `stack.vol_event_for` evaluates the session from the store when the close's payload asks (`vol_event: true`, set by `daily_cascade/payload.py`). A gate's synthetic payload reads nothing.
- **A fired event, in Mechanics:**
  - the "Volatility event" sub-section, first: the lens table, the trigger line, the consequence, the base rate, and on compression the complacency line;
  - the trigger line as a priority-1 item;
  - `vol_event` facts for the paragraph. `VOL_EVENT_NOTE` asks the existing narrative step for one passage in the desk voice, behind its audits, with no new model path.
- **A quiet session is silent.**
- **`stack_close`** writes the three rows (not on dry runs).
- **The 07:00 anchor** reads the prior close's stored `vol.event_day` (`morning_payload.stored_vol_event`, never recomputed) and prints it (`morning_render.vol_event_html`). It is silent when nothing fired.
- **The regime consequence** names the XIII band and Book C's vol rule, the operating doctrine's volatile-day protocol: VIX at or above 25 or up 20% on the day halves sizes and limits Book C to the 0700 list, defined-risk. It is **printed, never applied**. On 16 Oct's +21.5% the protocol's VIX condition holds, and the line says so.
- **Compression** prints the complacency read and stores `calc.vol_compression` = 1, the condition the Concentration & Complacency overlay's VIX input (≤ 18) reads when that overlay is built. It is designed, not built (`config/st_r5_t1_rest.yaml`). No new overlay.
- **The 12:30 gate, upward only:** `vol_event.vol_gate`, registered in `daily_cascade/midday_gate.py` beside 6b part 2's dealer gate.
  - The 12:30 capture (`altdata/dealer_capture.py`) reads quotes for ^VIX, ^VIX9D, ^VIX3M, ^VIX6M and ^GSPC from Yahoo, under the basket's exception, plus the stored history to the prior close.
  - A rise of 15% or 3 points opens the alert-only slot with the trigger line and the three intraday lenses (spot-vol, term structure, dealer positioning). The full block follows at 16:45.
  - A fall never opens it. No model is called.

### ST-R6.52d, the base rate and the ledger

- **The base rate** is computed from the box's stored VIX and SPX history, never recalled. It takes prior one-day moves in the same direction, the same size bucket (15–25%, 25–40%, 40%+, or 3–5 and 5+ points for a points-only trigger) and the same level band, and reports their forward 5- and 20-session SPX median, share up, and VIX median, with **n**. Under 10 cases it says "too few to read". The five-day, band and compression arms carry no base rate in v1, and the line says so.
- **The ledger:** `vol.event_ledger`, one row per fired event (instrument = its date) with its nine-line attribution and its realised 5- and 20-session SPX and VIX outcomes.
  - **Resolution:** `python -m altdata.vol_event resolve` writes a resolution as a new vintage. It runs warn-only in the EOD wrapper (`scripts/run_eod_cron.sh`, after the features step).
  - **Rights:** "no modifier right before 30 events" prints with its count.
- **The first row, 16 Oct 2026,** is a one-off seed command for the box (below), not a recurring by-hand line. Its catalyst is whatever the scan stored, likely "not established".

### The basket: ^VIX9D and ^VIX6M

They join `altdata/sources/yfinance_source.py` **under the basket's existing exception** (yfinance, ruled 11 Oct 2026) as `yfinance.mkt_vix9d` and `yfinance.mkt_vix6m` (`vol_index`). The old note that ^VIX9D was "deliberately not here" now says an order asked for it.
- `expected_members` goes 106 to 108 in both basket blocks.
- They need the price backfill on the box (below) before the term-structure lens has history.
- Cboe's free daily files are the verified alternative (verify item 1). **Session B's `st-r4-tranche-1b` already reads those files** for COR1M, COR3M and DSPX, so moving these two onto that reader later is one line each.

### XIII, the Volatility paper (drafts, for the operator's accept-all)

- **A chapter amendment** at the end of Section 36 ("Amendment (17 October 2026): attributing a volatility event"): level against change, the two-sided trigger, the nine lenses with their section cross-references, the consequence printed not applied, the base rate, the ledger and the 30-event rule.
- **Appendix E, "Dated Volatility Events",** with its first line, 16 October 2026, from the order's worked example. It is marked "the box's stored series to confirm in the ledger's first row", the catalyst "not established".
- **The HTML edition** is rebuilt (`docs/html/volatility-whitepaper.html`).

## The verify items

1. **Cboe's free daily files**, read once from the laptop on 17 Oct, read-only:
   - **Location:** `https://cdn.cboe.com/api/global/us_indices/daily_prices/<SYM>_History.csv`. The CDN's robots.txt answers 403, which RFC 9309 reads as no rules; that is the reading session B's reader takes.

   | Index | Columns | History from | 16 Oct 2026 close |
   |---|---|---|---|
   | VIX9D | OHLC | 4 Jan 2011 | 20.12 |
   | VIX3M | OHLC | 18 Sep 2009 | 20.50 |
   | VIX6M | OHLC | 2 Jan 2008 | 21.67 |
   | VVIX | one value | 6 Mar 2006 | 109.91 |
   | SKEW | one value | 2 Jan 1990 | 168.59 |

   Every 16 Oct close matches the order's worked example. **A slip in that read:** the request's User-Agent carried the operator's email address, which it should not have. Nothing else was sent, and no repeat. Every writer in this repo identifies itself with the EDGAR contact as CLAUDE.md says, and none of this branch's code fetches from Cboe.
2. **The 12:30 gate fits the cadence document unchanged:** answered by the filing (note 1). It is a threshold crossing, and the model is called only when it opens; here it is not called at all.
3. **The 16 Oct catalyst.** The scan's stored attributions are on the box, not the laptop, so the seed command reads them. `python -m altdata.vol_event show --date 2026-10-16` prints the catalyst line before anything is written. The filing expects "not established", since the scan's rows for that day predate the block.

## Session-set thresholds, with their reasons

All are in `config/vol_event.yaml`; the ruled ones are marked there.

| Setting | Value | Reason |
|---|---|---|
| five-day change unit | log | the move screen's unit for the VIX: a move from 12 and one from 40 on one scale |
| six-month window | 126 sessions | six months of sessions |
| sessions per year | 252 | the percentiles' windows (1,260 and 5,040) |
| front-led | VIX9D's change beats VIX6M's by 1+ point | a point is past the curve's own noise; the front leading by it says the episode is priced short |
| whole-curve | VIX6M moved at least half VIX9D's change, same sign | half is a regime repricing, not a front squeeze |
| systemic | MOVE up 5%+ (log) or HY OAS up 10+ bp | moves that size are outside a quiet session's range for each |
| base-rate buckets | 15–25%, 25–40%, 40%+; 3–5, 5+ points | three buckets keep each n readable on a 1990-onward history |
| base-rate floor | n ≥ 10 | under 10 the median is a handful of cases |
| the catalyst's markets | US stocks, stocks, S&P 500, volatility, VIX, equities | the scan's `market` labels for an equity or vol move |

Ruled, not session-set: 15% / 3 points; the 95th percentile on 20 years; 5% of the six-month low held three sessions; the 5- and 20-year percentiles; the 60-day beta; 10- and 20-day realised vol; 5- and 20-day outcomes; 30 events before a right; the 12:30 gate at +15% / +3 points, upward only; the protocol's 25 / +20%.

## Registry, catalogue, units

- **Metrics:**
  - `vol.event_day` and `vol.event_ledger` (`count`, JSON rows, mechanism `market_state`);
  - `calc.vol_compression` (`boolean`);
  - families `conditions`.
- **Basket members:** `yfinance.mkt_vix9d` and `yfinance.mkt_vix6m` (`vol_index`), with families and series kinds; `expected_members` 108 in both blocks.
- **Source:** `vol_event` (internal, live).
- **Catalogue:** `altdata.vol_event` (domain computed).
- `check_registry` OK.
- **The keys this branch reads but does not register,** because they belong to other branches: `cboe.cor3m`, `cboe.dspx` (session B, item 18) and `deribit.dvol_btc` (Tranche A). Their namespaces are not yet the registry's, so `validate_config_refs` reads them as plain strings until those branches land. Yahoo's `^COR3M` was not named, for the same reason.
- **CLAUDE.md:** a paragraph on the flag, and the count line recounted to **ninety code gates (eighty-seven Python, three shell), six data gates** (the Makefile counts 90/87).

## Gates

Run locally, one at a time, only those this branch writes or changes:

| Gate | Result | What it holds |
|---|---|---|
| `tools/validate_vol_event.py` (new; Makefile) | **45/0** | A every arm at its threshold and not below, both ways (±15.0% from 10.00 with +14.9% quiet; ±3.0 points with 2.9 quiet; five days past and inside its 95th percentile, up and down; a band crossing up and down; compression three sessions and not two), level and change apart with both percentiles. B the lenses on a 16-Oct-shaped day by hand (beta −0.80, +0.872 of +3.53 explained, 24.7%; front-led, VIX3M/VIX 1.026 from 1.143; VVIX +17.1% and SKEW +5.0% log against the VIX's +19.4%, VVIX/VIX 5.50; MOVE −1.4% log and HY +5 bp equity-specific; realised and VRP; breadth awaiting; CFTC with its change; the dealer lens; the catalyst attributed or "not established"; a missing input says so). C Mechanics' sub-section, item and facts; silence; nothing without the flag; the anchor; the consequence holds at +21.5% and not at +12%; compression and its stored flag. D the base rate's n by hand, "too few to read" under 10. E a resolved event's outcomes by hand, an unresolved one None, the rows' point-in-time stamps, the ledger line. F the 12:30 gate opens at +15.5% with the intraday lenses, stays closed at +0.55 points, a fall and no quote, writes nothing, no model path. G nothing from the brief's "never printed" list |
| `tools/validate_dealer_block.py` | **112/0** | group N's registry check now expects the dealer gate first and the VIX gate beside it |
| `tools/check_registry.py` | **OK** | |

Left to CI: every other gate, and those that render a PDF. `check_library` will see the Volatility paper's new subsection and appendix (consecutive: Appendix E after D) and its rebuilt HTML.

## Box commands, for the operator

Inside a window (weekdays 09:05–15:40 or 17:20–23:30 ET), **after Thursday's merge**:

```
cd ~/chester-reports
# 1. The two new basket members' history (the term-structure lens needs it):
.venv/bin/python tools/backfill_prices.py --period max --symbols ^VIX9D,^VIX6M
# 2. Read 16 Oct 2026 as the stored data has it -- nothing is written:
.venv/bin/python -m altdata.vol_event show --date 2026-10-16
# 3. The ledger's first row (a one-off seed, not a recurring by-hand line):
.venv/bin/python -m altdata.vol_event seed --date 2026-10-16
```

- **The 12:30 gate** runs inside 6b part 2's `chester-dealer-1230` unit; enabling it is in `docs/briefs/6b-dealer-2-notes.md`.
- **The nightly resolve** runs inside the EOD pass from the merge on; nothing to enable.
- **The close and the anchor** print the block from the first session after the merge.

## Files shared with the open branches

Trial merges (`git merge-tree`, nothing committed) against `6e-releases`, `6e-digital`, `6e-rest`, `6e-metric-lenses`, `crypto-tranche-a-1`, `crypto-tranche-a-2`, `st-r4-tranche-1b`, `st-r6-es-block`, `aud-3b-security-master`, `post-friday-fixes` and `docs-batch-9`, compared with the same merges from `6b-dealer-2`'s tip:
- **None conflicts in this branch's own changes.**
- `daily_cascade/morning_render.py` did conflict with `st-r4-tranche-1b` and `st-r6-es-block`, where both add a function before `render()`. This branch's function moved to the end of the file (`47d0685`, the commit after the code) and the trials are clean.
- **The files shared:**
  - `CLAUDE.md` (the count line: recount at stitching);
  - `metrics_registry.yaml` (the basket's `expected_members`: session B's `st-r4-tranche-1b` adds ^DSPX, ^COR1M and ^COR3M, so recount the members at stitching);
  - `altdata/sources/yfinance_source.py` (the same basket);
  - `daily_cascade/stack.py`, `stack_close.py`, `stack_prose.py`, `payload.py`, `morning_payload.py` and `morning_render.py`;
  - `scripts/run_eod_cron.sh`;
  - `docs/whitepapers/volatility-whitepaper.md` with its HTML edition (session B's item 18 notes say XIII held no implied correlation before their branch; their drafts touch other sections).

## Needs you

1. **Accept-all on the XIII drafts:** the amendment to Section 36 and Appendix E's first line.
2. **^VIX9D and ^VIX6M from Yahoo**, under the basket's exception. The alternative is Cboe's files, through session B's reader once it merges. Say if you prefer the files.
3. **The Weekly's part of the placement** ("the Weekly carries the week's events and ledger line") is not built here; the paste's build list did not ask for it. It is a small addition beside 6b part 3's Weekly wiring. Say whether it goes there.
4. **The base rate covers the one-day arm only.** The five-day, band and compression arms say so. Say if any of them should get its own conditioning.
5. **The 12:30 alert's delivery:** the same question as 6b part 2's needs-you 4. It is a file in the outbox today.
6. **Two security-master entries**, `SM00195` (^VIX9D) and `SM00196` (^VIX6M), added for the gate in ^VIX3M's pattern, with their unverified fields listed. The master is reviewed by you.

## CI

| Branch | Commit | Run | Result |
|---|---|---|---|
| `6b-dealer-2` | `ada7cb2` | 39038449525 | failed on three gates (6b part 2's; see its notes); fixed in `345f1d3` and merged here |
| `6b-dealer-2` | `345f1d3` | 39039815290 | **failed**, one check: `validate_audit_2`, "each edition's produce() is metered" -- the chart-dir helper had landed between the Monthly's metering decorator and `produce()`. Fixed on `6b-dealer-2` (`549619d`) and merged here |
| `vol-event-52` | `cd8bd07` | 39039856971 | **failed**, this branch's own (below) and the inherited decorator |
| `vol-event-52` | `1663521` (the fixes) | 39041321537 | **failed**, one check, this branch's own: `validate_security_master`, "SM ids under next_id 195" -- the two new entries took SM00195 and SM00196 without moving `next_id` |
| `vol-event-52` | `5a67995` (`next_id: 197`) and these notes | recorded at the next read | |

**The first run's failures, this branch's own, and the fixes:**
- **`validate_prices`:** it pins the basket at 106 symbols; with ^VIX9D and ^VIX6M it is 108. The gate now pins 108 and names them.
- **`validate_security_master`:** every basket identifier must resolve to one master entry. ^VIX9D and ^VIX6M are added as `SM00195` and `SM00196`, in ^VIX3M's pattern (index; name, currency, exchange and multiplier listed unverified). The master is reviewed by the operator: needs-you 6.
- **`validate_audit_3a`:**
  - CLAUDE.md's "106 market symbols" is now 108;
  - the four new block members (the two closes and their action series) are declared by name in `NEW_BLOCK_MEMBERS`;
  - the count self-test planted nothing at "ninety", the first one-word count in this line. The fix is copied byte for byte from aud-3c's `531d158`, so the two lines meet cleanly at stitching.

  `validate_audit_3a` 85/0, `validate_prices` 101/0.
