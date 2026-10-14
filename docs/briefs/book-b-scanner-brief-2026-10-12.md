# Brief — the Book B scanner (the Weekly's candidate list)

| | |
|---|---|
| Status | **Ruled, 12 Oct 2026 — all eight decisions yes, one at a time, 16:08–16:15 ET.** Built tonight by session A; merged with the W-1 branches on Tue 13 evening if green and read, else Fri 16; the first candidates then print in the Weekly of Sun 18 Oct. |
| Owner | Ari Chester |
| Why | Workplan v6 scheduled "the Book B scanner (the paste from the Enterprise Layer spec)" — but the Enterprise Layer spec defines packets, ledgers and engines, not what the scanner scans. Session A found that gap while building W-1.3a's candidates list. The Operating Doctrine §4.2 and §6 do define Book B, in detail; this brief turns those definitions into a scanner the Weekly can run, and leaves the parameters the Doctrine does not state as decisions. |

## 1. What the Doctrine already fixes (not decisions)

Book B is the swing book, one to six weeks. Its edge is trend and momentum "strongest after a pivotal point has been decisively cleared", with variant perception at extremes. A swing trade is a directional position — single name, sector or thematic ETF, an Alt Asset instrument, or a futures contract — entered at or immediately after a pivotal point: *a breakout from a defined base, a reclaim of a lost level with volume, a failed breakdown*. Entry waits for the market to declare itself; adds only on confirmation at a higher price for a long; the exit is a written invalidation level, a time stop, and a profit plan set before the trade.

The weekly reflection report (the Weekly) **owns Book B**: it generates the candidate list "from the week's price action against the Monthly context"; on Sunday the operator selects at most three, writes their packets, and stages conditional orders with brackets. The Monthly gives context only — "no Book B packet is generated from the Monthly alone". The Alternative Asset report supplies the non-equity candidates on the same pivotal-point terms. Disruptive Themes defines the thematic candidate lists. Positioning & Flows supplies the variant-perception confirmations. Top & Bottom's top signal raises the confirmation bar for longs and opens the short side; its bottom signal opens the long side after a Contraction has closed it. The Gamma dial governs Book B's entry timing; the Volatility dial its size.

Sizing: 0.75% of capital per position at standard tier ($2,250), the exceptional tier 1.5% from Phase 2 with the three-dial alignment plus one independent confirmation; at most six open positions; 4% ($12,000) total open risk with correlated positions counted once; a 3% monthly stop. Shorts need one more confirmation than longs and a regime that permits them (Overheat, Tightening, Contraction, or a Volatility dial at Rising or worse); in Expansion-Calm-Positive no outright shorts. A position against the primary trend carries a five-session time stop and may not be added to. Paper only; the blocklist at write time; the Weekly proposes, the sitting disposes.

## 2. What the scanner is

A code module, `altdata/book_b_scanner.py`, run inside the Weekly's build (Sunday 05:00 ET) over the store's bars, producing the candidate rows that W-1.3a's §10 block prints ("Candidates for the sitting (paper)") in the shape A built: the register's draft fields (instrument, direction, thesis, edge, horizon, size, invalidation, counter-thesis) plus `setup_id` (from EL-1's `config/setups.yaml`), the scanner's score, the catalyst and its date, `candidate_id`; `decision_id` null until the sitting approves. No model writes a candidate; the thesis line is code-templated from the setup ("breakout from a 34-session base on 2.1× volume; RS 88th percentile; positioning not crowded"). Nothing here places an order.

## 3. The pipeline

1. **Universe.** Every instrument in the store with daily bars and enough history (≥ 120 sessions): the price basket (SPY, QQQ, IWM, the sector ETFs, the factor and style ETFs, the Alt Asset set — GLD, SLV, USO, IBIT, the country ETFs, the currency pairs — the continuous futures), plus the earnings universe's 29 names. Single names beyond those wait for a universe and a data feed (decision 1).
2. **Trend structure.** Primary trend per the Technical Indicators paper's structure (higher highs and higher lows over the look-back; the 50- and 200-day as the Doctrine's tape uses them). A candidate against the primary trend is tagged "against the tape" and inherits the five-session time stop.
3. **Pivotal points (three, code-defined).** *Breakout:* close above the high of a base of N sessions whose range is ≤ R% of price, on volume ≥ V× its 20-session average. *Reclaim:* close back above a level lost within the last L sessions (a base high, the 50-day, a round number the chain's walls name), on volume. *Failed breakdown:* a close below a base low followed within F sessions by a close back above it. Parameters session-set from the paper, in config (decision 2).
4. **Confirmations (one for a long; two for a short, plus the regime permission).** From families other than price: relative strength against SPY (percentile over 60 sessions); positioning (the §10A rows — crowded the *other* way is a confirmation, crowded the same way is a warning); a Weekly tell that names the instrument (the style-regime pair, the consumer RS tell, XLY/XLP, the move screen's 2.5σ print); a Top & Bottom overlay reading; for Alt Asset instruments, the correlation layer's break flag. The list is config (decision 3).
5. **Regime gates (code, from the dials).** Shorts only where the Doctrine permits; a top signal raises the long bar to two confirmations; negative gamma marks "entry timing: wait for positive gamma or a session close above the flip"; the Volatility dial's multiplier sets the size band printed.
6. **Score and rank.** A weighted sum, weights in config: trend strength, base quality (tightness × duration), the count of confirmations, regime alignment, liquidity (dollar ADV against the position's size). The top ten print; the sitting selects at most three (decision 4).
7. **The draft.** Invalidation = the base low (breakout), the reclaimed level (reclaim), the breakdown low (failed breakdown); horizon = one to six weeks; size = 0.75% standard, the dials' multiplier applied; time stop = T sessions standard, five against the tape (decision 5); expected return = the base's measured move against the invalidation distance, printed as R; the counter-thesis = the strongest unmet confirmation or the crowding warning.
8. **Grading from day one.** Every candidate, taken or not, is written to the probability ledger as a forecast — "reaches +1R before −1R within six weeks" — with `setup_id`, so the Edge Ledger view groups them and the kill criterion (N ≥ 40) accrues from the first Weekly (decision 6).

## 4. What it does not do

It does not read the Monthly to generate a candidate (context only, as the Doctrine says — the Monthly's regime enters through the dials). It does not scan intraday or produce a daily output (Book C's territory; decision 7). It does not write a thesis in prose. It does not rank by the model. It does not place, stage or size a real order.

## 5. Build

≈ 10 h over one night: the module, the config (`config/book_b_scanner.yaml`), the fixture store with a breakout, a reclaim, a failed breakdown, an against-the-tape case and a crowded-positioning warning; the gate (`tools/validate_book_b_scanner.py`); the hook into W-1.3a's §10 block and its "activates when" line removed; the ledger write in the dry-run namespace. Branch from `w-1-3b-analytics` (so §10's block is present) once EL-1's `config/setups.yaml` exists on `el-1-packets` — the scanner reads setup ids from it, so it stacks on both: build on `w-1-3b-analytics` and read `el-1-packets`'s config by name until Friday's merge.

## 6. Decisions

1. **The v1 universe** — the stored basket plus the earnings universe's 29 names; single-name expansion is a separate item with its own data decision. **Yes — 12 Oct 2026.**
2. **The three pivotal points as code, parameters session-set from the Technical Indicators paper** (base N, tightness R, volume V, reclaim window L, failed-breakdown window F) and printed beside every candidate. **Yes — 12 Oct 2026.**
3. **The confirmation list v1** — relative strength, positioning, a Weekly tell, a T&B overlay, the correlation break — one for a long, two for a short, plus the regime permission. **Yes — 12 Oct 2026.**
4. **Scoring as a weighted sum with config weights; top ten printed; the sitting selects at most three.** **Yes — 12 Oct 2026.**
5. **The standard time stop** — the Doctrine names only the five-session against-the-tape stop. 15 sessions standard (three weeks of a one-to-six-week horizon), session-set. **Yes — 12 Oct 2026.**
6. **Every candidate graded from the day it is written**, taken or not, as a "+1R before −1R in six weeks" forecast under its `setup_id`; the graded-calls line reports candidates separately from the operator's own decisions. **Yes — 12 Oct 2026.**
7. **The scanner runs only inside the Weekly** (Sunday 05:00); no daily candidate output until the DTH-1 scope is ruled at Doctrine #2. **Yes — 12 Oct 2026.**
8. **Which session and night.** Session A, **tonight** (Mon 12 → Tue 13), queued after SR-43/49 reports; the branch stacks on `w-1-3b-analytics` and reads `el-1-packets`'s setups config by name. **Yes, pulled forward a day — 12 Oct 2026** ("I have time tonight and tomorrow").
