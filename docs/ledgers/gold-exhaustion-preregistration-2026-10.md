# The gold exhaustion checklist's ledger — pre-registration (October 2026)

*Written and committed on 26 Oct 2026 by session B on branch `b75-gold-spine`, before any edition of the ledger was computed. **Never edited.** A change is a new registration in a new dated file. The spec is the signal-triage order filed as Batch 16 (written as round 7, `change-order-signal-triage-round-7-2026-10-26.md`), item 88(a) (written as 81(a)): "exhaustion checklist (oil < $100; 10y falling while oil rises; gold up on an equity-down day; liquidation correlation flipping), each ticked weekly with a ledger testing whether they mark lows". Ruled 26 Oct 2026. The order states no pass rule, so this file states the first edition's, and every later edition is held to it.*

## The question

Does a week in which one of the four tells is ticked mark a low in gold, in the sense that gold's forward return after a ticked week exceeds its forward return after a clear week? This is report-only. It grants nothing and builds no composite.

## The weeks

- **The series:** gold's COMEX front future, `yfinance.mkt_gold_front` (GC=F), the series filed items 73 and 87 read, its stored daily closes.
- **A week:** the last stored session of each ISO week. Each week is read with only what was stored to that session.
- **The tells**, each over the five sessions to the week's last (`config/gold_attribution.yaml`, `exhaustion`; `altdata/gold_attribution.tells`):
  1. **Oil below $100:** Brent (`fred.brent`) at the week's last stored print below $100 a barrel.
  2. **The 10-year falling while oil rises:** the 10-year yield (`fred.yield_10y`) down and Brent up over the five sessions.
  3. **Gold up on an equity-down day:** at least one of the five sessions with gold's log return above zero and the S&P 500's (`yfinance.mkt_gspc`) below zero.
  4. **The liquidation correlation flipping sign:** gold's 20-session correlation of daily log returns with the S&P 500 (at least 15 paired sessions) on the opposite side of zero from its value at the session before the week.
- A tell is **ticked**, **clear**, or **not stored** (an input missing); a not-stored week is not scored for that tell.

## The measures

Gold's percentage change from the week's last close to the close **5, 20 and 60 sessions** later (`altdata/asset_event.forward`). A week without the later close is not yet scored at that horizon.

## The comparison and the pass rule

Per tell, separately; the tells are never pooled or combined:

- **The statistic:** the mean +20-session return after ticked weeks less the mean after clear weeks, with Welch's t.
- **INSUFFICIENT** under 30 ticked weeks or under 30 clear weeks with a +20-session reading.
- **PASS** at t of 2.0 or more.
- **FAIL** otherwise.

The +5 and +60 sessions print beside the +20 and decide nothing.

## Editions

`python -m altdata.gold_attribution ledger --out docs/ledgers/gold-exhaustion-ledger-<date>.md` writes a dated edition from the store, its window and n at its head, and this file's SHA-256 beside its pass rule. An edition is never edited.

## Rights

**None until it passes.** A PASS reaches the register only as a rule-31 draft (for the operator's accept-all). The checklist stays report-only either way: ticked in the Weekly's gold block, and a flip printed as a line in the daily close.
