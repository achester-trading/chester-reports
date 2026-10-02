# Brief — The reporting stack: ten sections, tape commentary, charts, and prediction markets

| | |
|---|---|
| Status | **Ruled 2026-10-02 14:21 ET** — Ari: adopt the ten-section stack as the shape of the daily close, the Weekly and the Monthly; pull 6d (prediction markets) forward to follow the daily commentary build; reading targets daily 5 min / weekly 20 min / monthly 40 min; depth changes — Mechanics in the Monthly becomes a retrospective on how the market behaved against dealer positioning; Plumbing & rates goes deep in the daily on a major event; What's priced goes deep in the daily and Weekly on a major movement. Long-horizon tape in the Monthly was asked as a question; the answer is §3.4, with its values *proposed* for the Doctrine monthly. |
| Owner | Ari Chester |
| Binding on | Claude Code sessions building the daily close, the Weekly, the Monthly, and 6d |
| Placement | Four tranches, §7. T1 (daily close) first. |
| Precedence | Below Part 26, the change orders, Amendments #4–#5. Alongside the Monthly v2 brief and the metric-lenses brief: this brief sets the **section order and depth** of every report; Monthly v2 keeps the content rules of its own sections (themes and tags, voices, "our read is bounded"); the lenses brief keeps the forms each metric shows. `altdata/derived.py` stays the one place a delta, percentile or z-score is computed. Levels are computed once (§2.2) and shared by prose and charts. |

## Why

The system collects more than it says. Positioning (CFTC, short interest, retail activity, TIC), plumbing (auction tails, term premium, issuance), what is priced (breakevens, consensus, expectations) and the contradiction table are all in the store and appear in no report, or in a table at the bottom. Each report also grew its own shape, so the reader starts over every time. One stack, in the same order at every cadence, lets the reader know where they are and go straight to what changed. The tape commentary and the charts are the voice and the picture of that stack; prediction markets fill the one sentence the stack cannot write today ("hike odds fell").

## 1. The stack

Every report prints these sections in this order, at the depth the matrix sets. A section with nothing new since the last edition prints its claim line and "(unchanged since *date*)" and nothing else.

| # | Section | What it answers | Reads from | Daily | Weekly | Monthly |
|---|---|---|---|---|---|---|
| 1 | **The read** | The five lines that matter | everything below; the model's only free paragraph | deep | deep | deep |
| 2 | **The tape** | Price across timeframes, levels, volume | bars, level list (§2.2), lenses price family | deep | deep | light + long frame (§3.4) |
| 3 | **Mechanics** | Dealer positioning, vol regime, term structure | GEX/DEX/pin verdicts, gamma and vol dials, IV solver, FlashAlpha cross-check | deep | medium | deep — retrospective (§1.2) |
| 4 | **What doesn't fit** | Contradictions, exceptions, divergences | contradiction table, exceptions, venue-vs-price disagreement (§4) | deep | deep | deep |
| 5 | **Plumbing & rates** | Yields, auctions, term premium, liquidity, credit | FRED rates and spreads, Treasury auctions, ACM, FiscalData, reserves/TGA/RRP, lenses rate/spread/quantity families | light; **deep on a major event** (§1.1) | medium | deep |
| 6 | **Positioning & flows** | Who is positioned how; leadership | CFTC COT, FINRA short interest, RTAT10, ApeWisdom, TIC, sector ETFs and style pairs | light | deep | medium |
| 7 | **What's priced** | Breakevens, consensus, expectations, rate path, prediction markets | FRED breakevens, consensus EPS logger, UMich, NY Fed SCE, fed funds futures (§2.4), 6d (§4) | light; **deep on a major movement** (§1.1) | medium; **deep on a major movement** | deep |
| 8 | **Narratives** | The stories, consensus and dissent, voices | narrative register, claims, voices (Phase B when built) | one line | medium | deep |
| 9 | **Ahead** | Events; scenarios with odds and signposts | events calendar, scenario weights, ledger and Brier | deep | deep | deep |
| 10 | **The book** | Positions, decisions, rule breaks, Book Z | register, heat view, rule_breaks, reconciliation, benchmark ledgers | short | medium | medium |
| — | **Slow layers** | Valuation, base rates, tails, themes | CAPE/ERP, base rates, the 25 tail scenarios, Disruptive Themes, Internal Order | — | — | deep |

Depth words: **deep** = commentary paragraphs, the section's table, a chart where the set (§3.2) has one; **medium** = one paragraph and the table; **light** = two to four lines with figures; **line** = one line. "Not yet tracked" footnotes continue as in Monthly v2: a line the data cannot support says so rather than vanishing.

### 1.1 Conditional depth is computed, never judged

The model does not decide a day was "major". A rule does, from the store, and the rule's firing is printed in the section's header ("deep: CPI released this session").

- **Plumbing & rates, daily → deep** when (a) the events table holds a tier-1 event for this session or the next — FOMC decision or minutes, CPI, PCE, payrolls, GDP, the refunding announcement, a 10-year or 30-year auction — or (b) the session's move crossed a threshold: 10-year or 30-year ≥ ±10 bp, 2s10s ≥ ±8 bp, HY OAS ≥ ±15 bp *(thresholds proposed)*.
- **What's priced, daily and Weekly → deep** when any tracked priced-in series moved beyond its threshold over the report's window: 5-year or 10-year breakeven ≥ 10 bp; the implied rate for any of the next four FOMC meetings ≥ 12.5 bp; any watched prediction-market probability ≥ 10 points (the spec v1.1 attention shock); S&P consensus EPS revision ≥ 1% (Weekly); UMich or SCE one-year expectations ≥ 0.3 pt *(all proposed)*.
- When a trigger fires, the section's chart from the set is included even if the report's chart count is otherwise at its cap; the cap then rises by one.

### 1.2 Mechanics in the Monthly: the dealer retrospective

Code computes a **dealer scorecard** for the month from the stored daily verdicts and the 20-session regime log (if a field the scorecard needs is not stored by the close today, T1 stores it; the Monthly reads, never recomputes): sessions in positive and in negative gamma; sessions on which the pin held (by the close's existing verdict rule) and on which it did not; sessions on which the flip was crossed, with the realized range on those sessions against the others; the month's largest move with the regime and net GEX that morning; realized against implied volatility by regime. The model writes two or three paragraphs from the scorecard alone — how the market behaved relative to positioning, never what to do about it. Every figure comes from the scorecard; the label audit applies; fewer than 15 scored sessions prints "insufficient sessions (n=…)".

### 1.3 The three reading rules

1. **Claim line.** Every section opens with its claim in one bold sentence, written by the model from that section's data table and audited like any paragraph.
2. **Change marks.** An item that changed since the prior edition carries a ◆ in front of it. The mark is computed by diffing the section's stored data against the prior edition's stored data (the same mechanism as Monthly v2's "What changed"); the model never places one.
3. **Odds in the ledger.** Every outlook in "Ahead" is a ledger entry — probability, horizon, resolution rule, source edition — *before* it is printed; a lean without an entry is refused. Grading uses the existing Brier machinery; the Weekly prints the last four weeks' graded calls, the Monthly the month's.

### 1.4 Reading budgets

Daily ≤ 1,000 words and ≤ 3 charts (5 minutes); Weekly ≤ 3,500 words and ≤ 6 charts (20 minutes); Monthly ≤ 7,000 words and ≤ 10 charts (40 minutes) *(proposed)*. Each section declares a priority order for its lines; a report over budget drops the lowest-priority lines and prints "(trimmed)" at the section, so the cut is visible and the model never summarizes to fit.

## 2. The tape commentary

### 2.1 Style, as rules

Ari's 2 Oct sample is the reference for tone. It is **not filed in the repository** unless it is Ari's own writing (then `docs/briefs/tape-style-reference.md`, under the same header as the Monthly reference: tone, structure and density only; never cite, reuse or restate). Its traits, as rules a gate can hold:

1. **Frames in order.** Each report writes the frame it owns and the one above it: the daily writes intraday and daily and places the session in the week; the Weekly writes daily and weekly and places the week in the month; the Monthly writes weekly and monthly and places the month in the long frame (§3.4).
2. **Levels by name and value.** Every level in the prose comes from the level list (§2.2), with its stored label and value; the label audit checks it.
3. **Moves are signed and sized.** `_signed` forms always; the move's own percentile (`delta_percentile`) when it is beyond the 80th or below the 20th.
4. **Co-movement, not motive.** "The long end led: 30-year +9 bp against 2-year +2 bp" is a statement from the store. A cause is named only when a stored event coincides, and then as "on the day of the refunding announcement", never "because of".
5. **Held or broke by rule.** A level "held" or "broke" by the close's existing rule for that level type; the model does not eyeball it.
6. **Outlook as odds.** A lean prints only with its ledger entry: "60% that the week's low holds through Friday; resolved by the Friday close." (§1.3.)
7. **No adjectives doing a number's work.** The banned-phrases audit, Monthly-only today, extends to the close and the Weekly.
8. **Desk register.** Short declarative sentences; one idea per paragraph; the figure in the sentence, not in a parenthesis after it.

### 2.2 The level list

One module (`altdata/levels.py`, new) computes the level list once per edition, stores it with the edition, and both the prose and the charts read it. Per instrument in the tape set (SPY, QQQ, IWM, the 10-year and 30-year, DXY, gold, oil, BTC — SPY stands for ES until 6b): prior close; session high and low; week high and low; 20-, 50- and 200-day moving averages; 52-week high and low with the drawdown; GEX flip, call wall, put wall and max pain from the dealer store; intraday VWAP where bars exist; the 40-week and 10- and 20-month averages for the long frames. Each level carries label, value, source key and as-of. The chart draws only levels in the list; the prose names only levels in the list; the gate checks both against the same object.

### 2.3 Intraday bars until 6b

The close run (16:45) pulls the session's 5-minute bars for the tape set from yfinance, stores them with the three clocks, and uses them for the intraday frame and VWAP. Pulled after the close, the feed's delay does not matter. If fewer than 90% of the session's expected bars arrive, the intraday frame prints "bars incomplete (n=…)" and C1 (§3.2) is omitted with that reason. 6b replaces the source; the schema stays.

### 2.4 The rate path

Fed funds futures join the prices feed: the contracts covering the next four to six FOMC meetings, from yfinance (the session verifies which contracts it serves; the front continuous contract at minimum). The implied rate after each meeting uses the standard meeting-day-weighted arithmetic, documented in the module and gated against a hand-computed fixture. The close and the Weekly print "the market prices *x* bp of cuts by *month* (fed funds futures, as of *date*)" beside the prediction-market odds from 6d; the two disagreeing by ≥ 15 points on the same meeting is a What-doesn't-fit line. If fewer than the next four meetings are retrievable, the path prints "not yet tracked" and the venue odds stand alone.

## 3. The charts

### 3.1 Rendering

Rendered by code from the store at edition time — never from a live fetch — with matplotlib (added to requirements if absent). Each chart is written twice: PNG at 2× for the email, embedded with `Content-ID` in a `multipart/related` body, ≤ 150 KB each; SVG for the HTML edition on disk. The series and the level list behind every chart are saved beside the edition so any chart can be regenerated. Candles: up hollow, down filled, and colored, so color is never the only encoding; a logarithmic price axis beyond two years; a caption written by code from the level list ("SPY, 60 sessions; 20-day 652.10; 50-day 640.30; week high 668.90"), also used as the alt text. A chart that cannot render prints "chart unavailable: *reason*" in its place. Charts never carry a verdict — no arrows, no "buy" annotations.

### 3.2 The chart set

**Daily (≤ 3).** C1 — the session's 5-minute candles with VWAP, prior close, GEX flip, call and put walls, max pain. C2 — 60 daily candles with the 20- and 50-day averages, the week's high and low, and the 200-day when it falls within the window. C3 — chosen by rule: an open contradiction → its z-score over 60 sessions with ±2 bands; else Plumbing deep → the 2-, 10- and 30-year over 60 sessions; else omitted.

**Weekly (≤ 6).** W1 — six months of daily candles with the 50- and 200-day. W2 — two years of weekly candles with the 40-week average. W3 — the 2-, 10- and 30-year and HY OAS over one year. W4 — positioning: CFTC net speculative positions (S&P, 10-year) over two years with ±1σ bands. W5 — leadership: the week's sector and style-pair returns, sorted. W6 — the open contradictions' z-scores.

**Monthly (≤ 10).** M1 — three years of weekly candles with the 40-week. M2 — ten years of monthly candles with the 10- and 20-month averages and the drawdown from the high (§3.4). M3 — the dealer retrospective: the month's closes against flip and max pain with regime shading (§1.2). M4 — the 10-year and the ACM term premium over five years. M5 — HY OAS over twenty years with the long percentile marked. M6 — positioning over five years. M7 — what's priced at month start against month end: breakevens and the implied rate path. M8 — scenario weights and their Brier through time. M9 — Book Z against the books, cumulative since 1 September.

### 3.3 The chart-and-prose rule

The prose may describe only what its chart shows and may name only listed levels; the chart may draw only listed levels. The gate holds both to one object. A chart and its paragraph are rendered from the same stored edition data, so an edition rebuilt later reproduces both.

### 3.4 The long frame in the Monthly (Ari's question)

Yes, add it, as levels and not as signals. The Monthly's tape stays light in words and gains two charts: M1 (three years, weekly, 40-week average) and M2 (ten years, monthly, 10- and 20-month averages, drawdown from the high). The 40-week and the 10-month are the weekly and monthly forms of the 200-day; the 10-month is the most widely watched monthly trend filter and so is a level the tape must know; the 20-month marks the two-year mean. "The index closed the month above its 10-month average for the *n*th consecutive month" is a fact from the store; "therefore long" is not, and the model may not write it. A cross counts only after the monthly close, never intra-month. The lenses' 12-month return percentile and the correction and bear flags print beside the chart. Bars are resampled from the daily bars in the store; where the store holds fewer than ten years, the chart shows what it holds with *n* printed (deep history is 6e). *Proposed for the Doctrine monthly:* the 40-week, 10-month and 20-month as the long-frame averages.

## 4. 6d — prediction markets, pulled forward

Spec v1.1 stands: Polymarket and Kalshi, read-only, with three rights — discovery, attention shock (≥ 10 points in a day), disagreement — and never a trigger. Public market endpoints only; if a key is ever required it goes in the box `.env` by Ari and never in a file or a chat. Pulled in the overnight fetch (06:45) and in the eod run (16:10) so the close can print the day's change, stored with the three clocks.

The watch list (`config/prediction_markets.yaml`): the FOMC decision at each of the next four meetings (cut / hold / hike); a US recession in 2026 and in 2027; each month's CPI print; House and Senate control on 3 November; a government shutdown by date; and a discovery slice of the twenty highest-volume markets whose titles match the narrative register's stories by keyword. Forms: probability, 1-, 5- and 20-session changes, volume. Disagreement: venue against the fed-funds-implied probability ≥ 15 points on the same meeting; venue against our scenario weight ≥ 20 points *(proposed)*.

Placement: What's priced always; an attention shock also earns a line in The read; a disagreement also appears in What doesn't fit. A market with no stored source is refused; a venue outage prints "as of *date*" and goes through the heartbeat's pending-versus-stale logic.

## 5. Gates

- **Stack.** A fixture edition renders all ten sections in order at each cadence; an unchanged section collapses to its claim line; each conditional trigger fires on a fixture with a tier-1 event or a threshold crossing and stays silent without one.
- **Levels.** Every level named in prose is in the level list; every level drawn is in the list; both read the same object. The label audit covers the new level types.
- **Tape.** Signed moves; ordinals; the banned-phrases audit on the close and the Weekly; an outlook line without a ledger entry is refused.
- **Charts.** Each chart type renders to PNG and SVG from a fixture; PNG ≤ 150 KB; the email's `Content-ID` set matches the charts referenced in the body; a render failure prints its reason, never a blank.
- **Intraday.** The bars-incomplete rule.
- **Rate path.** The meeting-day arithmetic against a hand-computed fixture.
- **6d.** Attention shock and disagreement computed from a fixture; a market with no source refused.
- **Budgets.** Word and chart counts enforced; an over-budget fixture prints "(trimmed)" at the right section.
- **Store.** Code gates seed their own temporary store and never read the live one (CLAUDE.md rule); no real position figures in any fixture.

## 6. For the Doctrine monthly (3–4 Oct)

Ratify or change: the Plumbing and What's-priced trigger thresholds (§1.1); the reading budgets (§1.4); the long-frame averages (§3.4); the prediction-market watch list and the two disagreement thresholds (§4); the chart caps per report. All are configuration; the build uses the proposed values until ruled.

## 7. Build order and hours

| Tranche | Scope | Hours | Lands |
|---|---|---|---|
| **T1 — daily close** | levels module; intraday bars; the stack on the close with its claim lines, change marks and collapse rule; tape commentary for the daily; C1–C3; email with embedded PNGs; the outlook ledger entry; the dealer-scorecard fields stored; gates | ~14 | first |
| **6d + rate path** | prediction markets per §4; fed funds futures per §2.4; What's-priced deep trigger live | ~6 | after T1 |
| **T2 — Weekly** | the stack on the Weekly; Positioning & flows and leadership; W1–W6; the graded-calls table | ~10 | after 6d |
| **T3 — Monthly** | the stack order reconciled with Monthly v2 Phase A; the dealer retrospective; M1–M9; Slow layers | ~12 | for the 1 Nov edition |

About 42 hours in all. Proposed order of work after this: cloud migration → 6b intraday slots → 6e with the metric lenses → 6f → Quarterly Structural → Audit #4 (14–15 Oct holds its date). The Doctrine agenda's item 9 is amended to match.

Deploys stay inside the box windows (weekdays 09:05–15:40 and 17:20–23:30 ET; never 16:00–17:20); on a weekend, clear of the Sunday 05:00 Weekly run. Sessions print the unit commands for Ari rather than restarting units.

## Not in scope

Trading signals from moving averages or charts; interactive HTML (SVG only for now); the voices register (Phase B); intraday feeds beyond yfinance (6b); any change to how the regime or the dials are computed; real position figures in any committed file.
