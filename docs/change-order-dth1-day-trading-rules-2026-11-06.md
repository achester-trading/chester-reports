# Change order — DTH-1 day-trading rules (Addendum A to Post-Freeze Amendment #5)

| | |
|---|---|
| File | `docs/change-order-dth1-day-trading-rules-2026-11-06.md` |
| Status | **RULED in chat** 6 Nov 2026, 09:17 ET: D1 to D7 as recommended, with D8 and D9 (the chat's), recorded as D63 (`docs/briefs/rulings-2026-11-06.md`). Filed 6 Nov 2026 by paste B140 (§0). The order as drafted in chat is kept at `docs/pastes/B140-attachment-dth1-rules.md`, its section 1 redacted as D9 rules. |
| Encoding | Addendum A to Post-Freeze Amendment #5, the Enterprise Layer / DTH-1 (D1). |
| Precedence | Below Part 26 and the Enterprise Layer order. It governs the hand-traded ES/MES intraday layer (DTH-1 expression and timing); no fifth book (the 27 Sep 2026 ruling stands). |
| Supersedes | `docs/es-day-trading-rules-2026-10-30.md` (the rules of 30 Oct and 3 Nov 2026) once the Doctrine's DTH-1 rules section lands (W4) and the standalone file retires (W5). That file is not in the repository at filing. |
| Totals | ≈ 9 h of sessions · under 1 h by hand. The order's estimates. |
| Built by | Nothing yet. W1 to W3 are paste B141 (branch `b141-dth1-rules-build`, from A130's branch); W4 after Doctrine #2; W5 by hand after W4. Audit #5 confirms. |

---

## 0. Filing (paste B140; ruled 6 Nov 2026, 09:17 ET, D63)

- **Encoding (D1).** Addendum A to Post-Freeze Amendment #5. Below Part 26 and the Enterprise Layer order; it governs the hand-traded ES/MES intraday layer (DTH-1 expression and timing); no fifth book (the 27 Sep 2026 ruling stands).

- **D1 to D7 accepted as recommended**, with:
  - **D3.** The start-of-week account base lives only in the Drive chester-cards folder (one line, `dth1-account-base.csv`, which the nightly sweep pulls); the 07:00 plan reads it on the box; no account figure in the repo.
  - **D5.** The Doctrine's DTH-1 rules section ("DT rule n") is ratified at Doctrine #2 (7-8 Nov) beside the pack as a five-minute item, since rules 1-13 are already ruled; the library paste that writes it (W4) follows the sitting; the standalone rules file retires then (W5).

- **D8 (the chat's).** Rule 8 and item 124g(ii) reconciled: structure sets the stop, the ATR multiple is its floor, size = fixed dollar risk / stop distance; one rule.

- **D9 (the chat's).** Section 1 is filed without dollar figures, the account value or the exposure figure (the standing rule: DTH-1 trades, account values and the ledger are never committed); the ES levels and "about 17% of the account" stay. The same redaction is applied to the attachment copy. Three figures are replaced in place, each marked "[… redacted, D9]": the loss in dollars on one ES, the exposure of one ES, and the account value.

- **Placement.** W1-W3 are paste B141 (branch `b141-dth1-rules-build`, from A130's branch); W4 after Doctrine #2; W5 by hand after W4. Audit #5 confirms.

The order as drafted follows, its body unedited but for D9's redaction; §0 governs where they differ.

---

# Change Order — Day-Trading Rules for the Discretionary Intraday Layer

Date: 6 Nov 2026
Status: DRAFT, pending sign-off in the main chat
Proposed encoding: Addendum A to Post-Freeze Amendment #5 (Enterprise Layer / DTH-1). Alternative: standalone amendment. Number at the main chat's discretion.
Source: `docs/es-day-trading-rules-2026-10-30.md` (rules set 30 Oct 2026, extended 3 Nov 2026; this order supersedes it once encoded)

## 1. Why

Week of 26 Oct 2026: a short covered near ES 7700, then a counter-trend long near 7668, held without a resting stop into a tech rout, closed at market near 7570 (about [dollar figure redacted, D9] on one ES, roughly 17% of the account). The read was right; the flip, the missing stop and the size were the mistakes. A resting stop at 7620 would have cut the loss roughly in half. One ES is about [exposure figure redacted, D9] of exposure on a roughly [account value redacted, D9] account.

These rules exist so the daily plan, the ledger and the Weekly check every discretionary trade the same way, without touching direction, which stays discretionary.

## 2. Scope

- Governs the hand-traded ES/MES intraday layer (DTH-1 expression and timing). No new book; the 27 Sep 2026 no-intraday-fifth-book ruling stands.
- Covers how a trade is entered, sized and exited. Direction, the 3-to-5-day view and the fade-the-reaction style stay discretionary and get scored, not constrained.
- A day trade held beyond the session is re-registered in the decision register as a Book C position under Book C's rule table (D7 below).

## 3. The rules (ruled 30 Oct and 3 Nov 2026)

Entry and exit
1. No entry without a stop. The stop order rests in the market the moment the fill comes. No mental stops.
2. A clear thesis for every position. One line before entry: why, where it is wrong, where it is going.
3. Don't catch a falling knife. No counter-trend buys in negative gamma, below the gamma flip, without a confirmed reversal (for example a 30-minute close back above the level).
4. Ride momentum once it is established. Enter on the first pullback in the direction of the trend, stop beyond the last swing. Do not chase.
5. After a big loss, stop trading for the day. Rule 7 defines "big".

Size and risk
6. Risk at most 1% of the account per trade. MES until the ledger shows an edge (D4).
7. Daily loss limit of 2% of the account, set in advance. Hit it and the day is over.
8. Place the stop by market structure, then size to fit it. Never shrink the stop to fit the size.
9. Never add to a loser; only add to a winner.
10. No flipping straight after an exit. After a stop-out or cover, a new setup meeting rules 1 to 4, with a 30-minute minimum before reversing.
11. Flat or reduced before scheduled binaries (FOMC, CPI, PCE, big-tech earnings, elections) unless the trade is about the event. Day trades do not carry over the weekend.
12. No setup means no trade. Log "no setup" and sit out.
13. Log every trade before leaving the screen.

Proposed (D2)
14. A one-line view at the top of each daily plan: direction, conviction 1 to 3, the level that proves it wrong. Scored against outcomes in the ledger.

## 4. Placement in the reporting stack

- 07:00 anchor (the daily plan, beside item 45's three-timeframe ES read): the view line (rule 14), gamma regime and trend, the day's scheduled binaries with the exposure allowed at each, the dollar risk per trade and the daily limit in dollars, named pullback entries with structural stops, or "no setup".
- 16:45 anchor (the daily close, "the book" section): the day's trades checked rule by rule (yes/no per rule), realized P&L against the daily limit.
- Weekly ("the book"): a compliance scorecard: trades taken, rules broken by rule number, P&L of compliant versus non-compliant trades, view-line hit rate by conviction level.
- Monthly / Doctrine sitting: the scorecard rolled up; any rule change goes through the sitting, never mid-week.
- Library: the rules encoded in the Operating Doctrine as a DTH-1 rules section (D5); the week of 26 Oct becomes a worked case in the operator's behavioral paper (XXXV) Draft 2, from register data.

## 5. Ledger fields (expectancy ledger, execution-framework-v2)

Per trade: view line at entry; thesis line; stop resting at fill (yes/no); stop level and the structural level behind it; contracts and dollars at risk vs 1% of account; counter-trend (yes/no) and the reversal signal if so; pullback entry (yes/no); add-ons and whether on a winner; minutes since last exit; scheduled binaries during the hold and exposure at each; logged same day (yes/no). Per day: realized P&L vs the 2% limit; trades after a breach flagged; "no setup" days.

## 6. Decisions for the main chat (each with a recommendation)

- D1. Encoding: addendum to Amendment #5 (DTH-1) or standalone. Recommend addendum: the rules govern the intraday layer that order defines.
- D2. Adopt rule 14 (the view line). Recommend yes: it records the gut call so the 3-to-5-day style can be scored, which is the "make it more scientific" ask of 2 Nov.
- D3. Account base for the 1% and 2% rules. Recommend start-of-week account value, fixed for the week, so intraday gains never size the next trade up.
- D4. The gate for moving from MES back to ES. Recommend: 30 logged trades with positive expectancy and at least 80% rule compliance, confirmed at a Doctrine sitting.
- D5. Where the rules live. Recommend a DTH-1 rules section in the Operating Doctrine, cited as "DT rule n", with `docs/es-day-trading-rules-2026-10-30.md` retired once encoded.
- D6. The weekly compliance scorecard in "the book" section of the Weekly. Recommend yes.
- D7. A day trade held beyond the session is re-registered as Book C under Book C's rule table. Recommend yes; if the Book C table is not yet built, the day-trade rules apply until it is.

## 7. Work order (approximate, for Audit #5 to place)

- W1. 07:00 plan template: view line, risk-in-dollars block, binaries-and-exposure block, "no setup" line. About 2 h.
- W2. Ledger fields (§5) and the rule-by-rule check in the 16:45 close. About 3 h.
- W3. Weekly compliance scorecard. About 2 h.
- W4. Doctrine DTH-1 rules section (library session) and the XXXV Draft 2 worked case. About 2 h.
- W5. By hand: retire the standalone rules file after W4. Under 30 min.

Total about 9 h of sessions plus under 1 h by hand. No new data feeds, no new reports.

## 8. Sign-off

Rules 1 to 13: ruled 30 Oct and 3 Nov 2026 in chat.
D1 to D7 and the work order: pending.
