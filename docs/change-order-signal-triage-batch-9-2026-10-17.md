# Change order — Signal-triage round 6, Part 4 (item 52): volatility event flag and attribution

**File:** `docs/change-order-signal-triage-batch-9-2026-10-17.md`
**Status:** RULED 2026-10-17 in chat; **FILED 2026-10-17** by the filing chat (08:45 ET). Commits on `docs-batch-9` from main, after Batch 8.
**Encoding:** Batch 9 of Post-Freeze Amendment #4. Round 6 Part 1 (item 45) was folded into Batch 6 at filing on 15 Oct; Part 2 (items 46–48) is Batch 7, filed 16 Oct; Part 3 (items 49–51) is Batch 8, filed 17 Oct. All three were filed before this order arrived, so there was nothing to fold into; this file is round 6 Part 4 and takes the next batch number. Decided by the filing chat, 17 Oct 2026.
**Precedence:** below Part 26 and the 25 Sep integrated signal-triage order; follows its integration rules (R28 sub-states, one system of record, Track D preconditions, validation gates as offline calibration studies with dated ledgers). This item extends the batch-1 10y yield-move attribution pattern (SR-6) to volatility and adds one gate to the 12:30 alert-only slot of the Audit #3 cadence.

---

## 1. Purpose and scope

One item, from an operator design question on 17 Oct 2026 after a +21% VIX day: are significant volatility changes flagged in the daily reporting, and is what drives them analysed? The answer was "partly" — the daily close prints the VIX level and regime band, item 19 adds the MOVE-vs-VIX divergence flag, and the Concentration & Complacency overlay catches prolonged low vol — but there is no defined trigger for a large move in either direction and no attribution of what carried it. This order adds both. No composite weights change; one alert gate is added.

## 2. Entry

### 52 · Volatility event flag and attribution (operator design question; worked example 16 Oct 2026) — BRIEF

**Origin.** Operator question of 17 Oct 2026, prompted by a two-day VIX move from ~16.5 to ~20 (16 Oct: +3.53 to 19.98, +21.5%).

**Thought process.** Level and change are different facts: Thursday was a large change at a modest level, and a flag that conflates them misreads both. The stack already has the right template — the 10y yield-move attribution decomposes a rates move into expected short rates, term premium and breakevens and says which leg carried it; vol needs the same decomposition. Nine lenses do the work, and all but one are computable from data the box already holds or can fetch free. Compression matters as much as expansion: vol pinned at the floor of its range is the complacency condition the Concentration & Complacency overlay exists for, so the flag is two-sided and the compression leg feeds that overlay rather than a new one. The intraday case belongs in the 12:30 alert-only slot, whose rule is that the LLM is called only when a gate opens — a vol shock is the kind of gate it was designed for.

**Worked example — 16 Oct 2026 (FlashAlpha macro block at the close; box data to confirm).** VIX 19.98 (+3.53, +21.5%); VIX9D 20.12, VIX3M 20.50, VIX6M 21.67 (near-flat front, contango collapsed from the front); VVIX 109.9 (+18.7%); SKEW 168.6 (+5.1%); SPX 7,659 (−1.09%); MOVE 101.1 (−1.4%); VIX futures front 20.5 vs spot 19.99; Fear & Greed 18. Reading by the lenses: the SPX move explains roughly a quarter of the VIX move at the usual spot-vol beta, so most of it is a vol bid beyond spot — protection demand; front-led, not yet a whole-curve regime shift; tail demand (SKEW) and vol-of-vol rising faster than ATM; rates not the driver; SPX closed well below the gamma flip (~7,767), so dealer hedging was amplifying. Catalyst: not established from the data pulled — the block must say so rather than guess; the Phase B news scan supplies it.

**Stack today.** VIX level and XIII regime band in the daily close; MOVE in (round-4 item 8); item 19 MOVE-vs-VIX flag (Batch 5); Concentration & Complacency overlay (prolonged low vol); dealer gamma from the 6b engine; no vol-event trigger, no attribution, no vol gate on the 12:30 slot.

**Ruling.**
1. **Trigger, two-sided.** A vol event fires on any of: one-day VIX change ≥ ±15% or ≥ ±3 points; five-day change beyond its own 95th percentile (20-year window); a crossing of an XIII regime band; or compression to the floor of the trailing six-month range (within 5% of the six-month low, held three sessions). Level and change are printed as separate fields with dual percentiles (five-year and 20-year).
2. **Attribution, nine lenses**, printed as a compact table with one line each:
   - *Spot-vol:* share of the VIX move explained by the SPX move at the trailing 60-day spot-vol beta; the residual is the vol bid beyond spot.
   - *Term structure:* VIX9D, VIX, VIX3M, VIX6M — front-led vs whole-curve; the contango/backwardation state and its change.
   - *Tail and vol-of-vol:* Cboe SKEW and VVIX changes relative to the ATM move; VVIX/VIX ratio.
   - *Cross-asset:* MOVE, HY OAS, a G10 FX vol proxy, crypto DVOL — equity-specific vs systemic.
   - *Dealer positioning:* spot vs gamma flip, net GEX sign and size from the box's engine; vanna and charm read; 0DTE share where available.
   - *Realized vs implied:* 10- and 20-day realized SPX vol against VIX; VRP change — implied running ahead of realized (fear premium) vs realized catching up.
   - *Breadth of the vol move:* implied correlation and the item-18 dispersion panel — correlation-led (macro) vs dispersion-led (idiosyncratic).
   - *Positioning:* CFTC VIX futures non-commercial net position (weekly) and VIX ETP vega — the crowding that turns a spike into a cascade.
   - *Catalyst:* the Phase B news scan names the event; the narrative register logs it with intensity; "not established" is a permitted value.
3. **Output.** A vol-event block in the 16:45 close and the next 07:00 anchor: trigger line, attribution table, one paragraph on what's behind it in the desk voice, the regime consequence (XIII band; the Book C vol-targeting rule), and the base rate for the configuration (forward SPX and VIX paths after prior moves of the same size from the same level band, computed from the box's history, not recalled). Compression events print the complacency read and feed the Concentration & Complacency overlay's existing input; no new overlay.
4. **Intraday gate.** A one-day VIX change ≥ +15% or ≥ +3 points by 12:30 ET opens the 12:30 alert-only slot with the trigger line and the lenses computable intraday (spot-vol, term structure, dealer positioning); the full block follows at 16:45.
5. **Ledger.** Every fired event is logged with its attribution and the realised 5- and 20-day SPX and VIX outcomes, as the calibration ledger for any later modifier right.

**Rights.** Flag and alert gate only. No composite weight. Modifier rights (for example a Book C sizing step) only after the ledger holds ≥ 30 events.

**Placement.** Mechanics (daily close, 07:00 anchor); 12:30 alert slot; Weekly carries the week's events and ledger line; XIII Volatility paper gains a dated-appendix line per event and a short chapter amendment describing the attribution.

**Data.** Cboe daily files for VIX9D, VIX3M, VIX6M, VVIX, SKEW (free CSVs; yfinance as fallback for VIX and VIX3M); FRED for VIXCLS, MOVE and HY OAS; realized vol from the box's SPX series; gamma from the 6b engine; CFTC COT (free, weekly); FlashAlpha `get_vix_state` and `get_spot_vol_correlation` as the Wednesday cross-check under the existing vendor tasks, never as the source.

**Work.** ST-R6.52a trigger logic, dual percentiles, event store — 1.5h. ST-R6.52b attribution lenses (eight computable; catalyst from Phase B) — 3h. ST-R6.52c block rendering in both anchors + 12:30 gate — 1.5h. ST-R6.52d base-rate computation and event ledger — 1.5h. XIII appendix line and chapter amendment — by hand 1h. **Total ≈ 7.5h sessions + 1h by hand.** Dependencies: dealer-positioning lens waits for the 6b engine (FlashAlpha levels by hand until then); breadth lens waits for ST-R4.18a (dispersion panel); positioning lens is weekly-only.

## 3. Cross-item notes

- Same shape as the 10y attribution (SR-6, batch 1): one build pattern, two markets. The two blocks print adjacent in mechanics on days both fire.
- Item 19 (MOVE-vs-VIX divergence) is a configuration this block will often print alongside; its calibration ledger and this one stay separate.
- Item 18's dispersion panel supplies the breadth lens; item 45's three-timeframe ES block prints the same session's dealer map, so the two blocks reference one set of levels.
- Compression events feed the Concentration & Complacency overlay's existing input; no new overlay, no weight change.

## 4. Work order (provisional; the audit places it)

- **Now:** ST-R6.52a (1.5), ST-R6.52b (3, dealer and breadth lenses stubbed until their parents land), ST-R6.52c (1.5), ST-R6.52d (1.5) — ≈7.5h, candidate for the 1 Nov Monthly's mechanics section if the calendar allows.
- **By hand:** XIII appendix line and chapter amendment — 1h; 16 Oct 2026 entered as the first ledger row.

**Placement (the filing chat, 17 Oct 2026).** Session A's line, in the night of Sun 18 → Mon 19 beside 6b part 2 (the charts, the three sentences, the scorecard ledger and the 09:45 and 12:30 capture units), which gives the 12:30 gate the slot it opens and the dealer lens the engine additions 6b part 1 makes on 17 Oct. Both ride the second stitched chain (Tue 20 → Wed 21) and merge on Thu 22, so the 1 Nov Monthly candidacy holds. It displaces nothing: session A's Sun → Mon night carried 6b part 2 alone (about 8 hours), and item 52's 7.5 hours fit beside it at the sessions' current pace. The breadth lens reads item 18's dispersion panel, which is on session B's `st-r4-tranche-1b` and merges in the same chain. The XIII appendix line and chapter amendment are committed by the session as drafted, for the operator's accept-all (the 16 Oct ruling on judgment drafts); the 16 Oct 2026 ledger row is a one-off seed, not a recurring by-hand line.

## 5. Verify items

1. Cboe's current free daily file locations for VIX9D, VIX3M, VIX6M, VVIX and SKEW, and their history depth.
2. Whether the 12:30 slot's publish gate accepts a new trigger without a change to the cadence document (Audit #3 §N).
3. The 16 Oct catalyst, from the Phase B scan, for the first ledger row.

## 6. Register and sources

**Register:** item 52 with its round number; SR number at the next Doctrine sitting, after Batches 5 to 8. Recorded as an extension of SR-6's attribution pattern to volatility.
**New sources:** Cboe daily index files (VIX9D, VIX3M, VIX6M, VVIX, SKEW); CFTC COT VIX futures; FlashAlpha `get_vix_state` and `get_spot_vol_correlation` (cross-check only).

## 7. Decisions and sign-off

- 52 — ruled 2026-10-17 ("Yes. draft change order to incorporate this.").

Signed: A. Chester, 2026-10-17 (chat ruling as recorded above).
Filing: filed as Batch 9 (see Encoding); commits on `docs-batch-9` after Batch 8; the work order is placed by the filing chat in §4; register entry at the next Doctrine sitting.

## 8. Filing notes (17 Oct 2026, the integration review)

These notes record what the filing review found in the repo at main `1148c66` and on the open branches. They are not rulings. Each one is for the build session to confirm.

1. **Verify item 2, answered: the gate fits the cadence document without a change.** Audit #3 §I defines the 12:30 slot as "the 12:30 chain capture keeps running for data and feeds an alert only; the LLM is called only when an exception gate opens", and its Alerts row fires on "threshold crossings, percentile extremes, regime-transition probability, contradiction-table entries, heartbeat/drift, portfolio-impact of a move; silent otherwise". Item 52's intraday gate (a one-day VIX change of +15% or +3 points by 12:30) is a threshold crossing, which the row already names, and it calls the model only when it opens. Nothing in the document changes; the gate is one more instance of what it describes.
2. **The slot does not exist in code yet.** No unit on main runs at 12:30 (the timers are the auction sampler at 15:49, the close, the EOD pass, the morning anchor, the overnight pull, the weekly, the monthly and the housekeeping units). The 09:45 and 12:30 captures arrive with 6b part 2, per the dealer-positioning brief, so ST-R6.52c's gate is built against that unit and is placed beside it (above). Until the unit is live on the box, the gate is tested on fixtures only.
3. **Most of the vol series are already pulled.** VIXCLS from FRED (full history, so the 20-year window is available); ^VIX3M, ^VVIX and ^SKEW through the yfinance basket (`mkt_vix3m`, `mkt_vvix`, `mkt_skew`); MOVE and the HY OAS from FRED; the VIX futures curve from the vxcurve logger; SPX for the spot-vol beta and realised vol. Two are not: ^VIX9D (deliberately left out of the basket by an earlier order) and VIX6M. Both are on Cboe's free daily files and on Yahoo; the session adds them under the basket's existing exception or the Cboe files, within robots, and says which.
4. **Two lenses have no free source today.** The G10 FX vol proxy (the published FX vol indices are proprietary) and VIX ETP vega are listed gaps unless the session finds a free series within robots; under the operator's standing rule of 16 Oct neither gets a registration. The CFTC VIX futures positions are an extension of the existing `cftc` writer.
5. **Units follow AUD-3a.** VIX prints in points and percent as the order asks; the move screen's convention that VVIX, MOVE and SKEW change in log terms stands, so the attribution's "relative to the ATM move" lines state their unit.
6. **The base rate is computed from the box's history, as the order says**, from VIXCLS and the stored SPX series; the forward paths are conditional on the level band and the move size, with n printed, never recalled.
7. **The catalyst (verify item 3)** comes from the Phase B news scan's stored events; "not established" is the permitted value and is what the 16 Oct row will likely carry, since the scan's events for that day predate the block.
8. **Rights.** Flag and alert gate only; the Book C vol-targeting consequence is printed, not applied; no modifier before 30 ledger events. Paper only stands.
