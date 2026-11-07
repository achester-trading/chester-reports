# Item 119's event-vol pricing ledger — pre-registration (Batch 22, the order's 101; with Batch 23 item 124f)

**Filed:** 6 Nov 2026, paste A129, before any code. **Orders:** signal-triage Batch 22 item 119 (`docs/change-order-signal-triage-batch-22-2026-11-05.md`, the body's 101) and Batch 23 item 124f with its D-2 (`docs/change-order-signal-triage-batch-23-2026-11-06.md`, the body's 106f), both on `origin/b129-five-filings`. Batch 23's section 0 (Q3) rules the realised window T, T+1 and T+2 from the start, so the schema below is built once.

This file is never edited. Its SHA-256 (of its LF bytes) is held by `config/event_vol.yaml` and `tools/validate_item_119.py`; a change to it is a new pre-registration, not an amendment.

## 1. The events

Every scheduled event the stack ranks in Ahead whose class is one of six types:

| Type | What counts | The underlying read |
|---|---|---|
| `fomc` | an FOMC statement (the decision day; never the minutes) | SPY |
| `cpi` | the CPI release | SPY |
| `payrolls` | the employment situation release | SPY |
| `refunding` | the Treasury's quarterly refunding announcement | SPY |
| `election` | a US federal election day | SPY |
| `earnings` | a scheduled earnings report of one of the box's 13 tickers (SPY, QQQ and IWM have none; the ten single names: NVDA, AAPL, MSFT, AMZN, META, GOOGL, TSLA, MSTR, COIN, ASTS) | the name itself |

An earnings event's type is `earnings:<SYMBOL>`: a name's own reactions are its scale, so the names are never pooled. SPX's chain (the vendor's 16:31 capture) may be read beside SPY's where it is captured; SPY is the macro events' record because its chain is captured with the solver's IVs on every session.

## 2. Day T

T is the first session whose close falls after the event:
- an event known to land before the close (08:30 releases, the 14:00 FOMC statement): T is the event's date;
- an event known to land after the close (an election's results, an after-close report): T is the next session;
- an event whose time is not stored (most earnings dates are stored as a date only): T is the event's date, and the headline realised move below spans two sessions, so either timing is covered.

T−1 is the session before T.

## 3. The implied move

From the box's own captured chain only (the 16:10 capture of the 13, the vendor's 16:31 capture for SPX): the last capture of the underlying on T−1.

- **The expiry:** the first expiry after the event (Ahead's `straddle_expiry`: strictly after the event's date unless the event lands before the open, when the event date's own expiry counts).
- **The straddle:** the at-the-money call and put mids at the strike nearest spot (Ahead's `atm_straddle`). The full implied move is straddle ÷ spot, in percent.
- **The event day's share of variance.** Where the expiry covers one session only, the share is 1 and the implied event move is the full implied move. Where it covers more than one session, the term structure separates the event day, on the straddle convention (straddle ÷ spot = √(2/π) × σ × √t):
  - with an expiry after T−1 and before the event's expiry, Ahead's `event_move` (item 57) applies: the post-event expiry's total variance less the pre-event expiry's variance rate over the same time;
  - else, with the next expiry after the event's, the two post-event expiries share one base rate: rate = (V₂ − V₁) ÷ (t₂ − t₁), event variance = V₁ − rate × t₁;
  - the share is the event variance over V₁, and the implied event move is the full implied move × √share.
  - A non-positive event variance, or no second expiry, records the share as "not separable" and the full implied move labelled "includes non-event days". That row's implied move is kept but never compared.
- **No chain:** a name with no capture on T−1 records "no chain". FlashAlpha is never read (the 9 Oct rule); a vendor figure is never stored here.

## 4. The realised moves

From the store's closes of the underlying: the close-to-close return of T, of T+1 and of T+2, each signed, in percent; and the **headline realised move**:
- the absolute return from the T−1 close to the T close, for an event of known time;
- the absolute return from the T−1 close to the T+1 close, for an event whose time is not stored.

A session not yet closed is "pending". A row is resolved when its T+2 is stored.

## 5. The tags (Batch 23 item 124f)

Two fields on every row, nullable:
- `scheduled`: `scheduled` or `unscheduled`;
- `catalyst_class`: one of `policy shock`, `policy response`, `exogenous`, `data print`, `positioning unwind`, `earnings`, `political`.

Every row of this ledger is scheduled by construction. Its class defaults by type: `data print` for cpi and payrolls; `policy response` for fomc; `policy shock` for refunding; `political` for election; `earnings` for earnings. The operator may re-tag a row. The same two fields join item 52's volatility-event ledger (`vol.event_ledger`), nullable, its existing rows untouched. Seed rows are judgment drafts for the operator's accept-all (rule 31): the twenty Morningstar days, 27 Feb 2020 and the six calm-surface openers (the study's dates). The five earlier openers' labels are the study's, from memory, and marked "draft" (V-106h).

## 6. The statistic, the print and the flag

- **The median realised move for a type:** the median headline realised move over the type's resolved rows, with n. It is computed from the ledger's own rows only, never from a price history assembled for the purpose.
- **Log-only until 20:** below 20 resolved rows of a type, Ahead prints "accruing (n=k of 20)" beside the implied move, and no flag fires.
- **The flag, "cheap event vol":** at 20 or more, it fires when the event's implied move (the separated event move where separable, else no flag) sits below its type's median realised move. It prints in Ahead only (the close and the Weekly), never in any other section.

## 7. The pass rule

**None stated.** The order grants an Ahead line and a flag and names no pass rule ("log-only until there are at least 20 events of each type"). The first edition says so, and no later edition may supply one.

## 8. Rights

The Ahead line and the flag, nothing else. Nothing here enters a composite, a dial, the market-state object, a tell, a setup, a size or the register. The ledger feeds 124c(ii)'s internal-stress read only if that read's own pre-registered test passes.

## 9. The 2026 midterm (V-101b)

The midterm base-rate ledger gains 2026 by its ruled path: a new dated edition of `tools/calibration/midterm_base_rate.py`'s ledger. Its pre-registered computation is unchanged (the nineteen completed midterm years stay the sample). 2026 prints as its own row beside the sample:
- the year's drawdown to date;
- the election-day close;
- the realised 4 Nov and 5 Nov moves from the store;
- the implied move of about 1.2%, marked "order's figure" (a desk's figure the order quotes, never a chain read).

Its headline is copied into `config/weekly_ahead.yaml` beside its channel, as Batch 16 ruled; a live row never reads a ledger.
