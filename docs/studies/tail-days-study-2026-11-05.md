# Tail Days 2016–2026: what preceded the ten best and ten worst days, and what the stack would have seen

**Status:** draft 2, 5 Nov 2026 (late evening). Supersedes draft 1 (commit 28db006f). Checked against the replay in `docs/studies/tail-days-2016-2026-data.md` (commit 04fd571f, `tools/studies/tail_days.py`). Figures come from that file unless marked (memory). The per-date condition tables stay in the data file and are not repeated here.
**Prompted by:** Morningstar's "Volatility Cuts Both Ways" table (Morningstar US Market Index, Nov 2016–Nov 2026), which lists 5 Nov 2026 (−4.4%) as the tenth-worst day.
**Register:** item 106 (round 8). Sub-rulings a–h were accepted on 5 Nov 2026 at 22:06. Draft 2 proposes amendments to a, c, e, f and g, and adds i (§5). These are pending a ruling.

---

## 0. What draft 2 changes

The replay withdrew draft 1's headline finding. Draft 1 said the regime behind every tail day could be seen in advance. That held for tail days inside an established high-vol regime. It did not hold for the day that opened the current episode: on index-vol measures, that day was invisible.

Corrections, most important first:

1. **5 Nov 2026 came out of a calm surface.** At the 4 Nov close, VIX was 16.6, 20-day realised vol was 12.9%, the VIX curve was in contango, the S&P was 1.7% below its 52-week high, and there had been no 2% day in 20 sessions. Only two readings were stretched: SPY's Amihud illiquidity sat at the 100th percentile of its year, and equal-weight (RSP) had beaten SPY by 7.4 points in 20 sessions. On 3 Apr 2025, VIX was 1.3x its February level, not the 2–3x draft 1 said.
2. **The 2026 run-up was a Nasdaq move, not an S&P move.** In October the S&P fell 0.9% and the Nasdaq fell 5.3%. The −2.6% on 22 Oct and the 30 Oct drop were Nasdaq figures; on those days the S&P fell 1.2% and 1.8%.
3. **Vol management controls drawdowns; it does not add return.** Since 1990 its Sharpe ratio was 0.58 (0.57 after costs), against 0.55 for buy-and-hold. It returned 6.5% a year against 8.6%. Its max drawdown was −36.5% against −56.8%. It held 0.86 exposure going into 5 Nov 2026, because a rule built on trailing vol cannot see an opener coming. Draft 1's claim that it "improves risk-adjusted returns" is withdrawn.
4. **Forward returns after a bottom-decile day are at or above the all-day baseline.** Only the spread of outcomes gets wider. So draft 1's "halve size after a bottom-decile day" had no basis in expected returns. §5 replaces it with constant-risk sizing.
5. **Ranking.** On the S&P 500, 5 Nov 2026 is the 11th-worst day of the decade. 27 Feb 2020 (−4.42%) makes the S&P's top ten instead. Morningstar's list uses its own broad US index.
6. **Smaller fixes:**
   - The S&P was 7.7% below its peak on 2 Apr 2025, not 8–10%.
   - The 10-year rose 33bp over the three sessions to 9 Apr 2025, and reached 4.48% only on 11 Apr, after the pause.
   - SPHB/SPLV closed −2.7% on 4 Nov 2026. The −3.41% on the posted chart was an 11:04 intraday print. Item 100's −2% flag is still met.
   - VIX was not falling in the week before 10 Nov 2022.
   - Draft 1's hours total counted 106h twice (§5).

**Confirmed by the replay:**
- Morningstar's 8 of 10 reproduces on the S&P 500.
- After a bottom-decile day, the chance of a top-decile day within five sessions is 63%, against 38% on any day. With VIX above 30, it is 90–96%.
- Across all top- and bottom-decile days, the two tails sit together only moderately more often than chance would give: 73% against 65%.

**Gaps:**
- HY and IG OAS before 6 Nov 2023, because FRED now serves only the last three years of the ICE BofA series (§5, 106i).
- VIX for 5 Nov 2026, which FRED has not yet published.

---

## 1. Five episodes

The twenty days fall into five episodes. Fourteen of them sit in one six-week window of 2020. The right-hand column gives the vol state at the close before each episode's first listed day. Percentages are Morningstar's.

| Episode | Worst days | Best days | Vol state before |
|---|---|---|---|
| A. Q4 2018 | — | 26 Dec 2018 +5.0% | In-regime (correction under way) |
| B. COVID, Mar–Jun 2020 | 9, 11, 12, 16, 18 Mar; 1 Apr; 11 Jun (the S&P list adds 27 Feb) | 2, 10, 13, 17, 24, 26 Mar; 6 Apr | In-regime from late February |
| C. 2022 bear market | — | 10 Nov 2022 +5.7% | Elevated, not falling |
| D. April 2025 tariffs | 3 Apr −5.0%, 4 Apr −5.9% | 9 Apr +9.6% | Moderate: VIX 1.3x February, S&P 7.7% off its peak |
| E. Nov 2026 AI capex / midterm policy | 5 Nov −4.4% | none yet | Calm: VIX 16.6, realised vol 12.9%, contango |

---

## 2. Episode notes

These notes cover catalysts and mechanisms. The figures are in the data file.

**A. 26 Dec 2018.**
- *Catalysts:* the 19 Dec FOMC hike and Powell's "autopilot" remark on the balance sheet; Christmas Eve capitulation in a thin tape; Mnuchin's calls to bank CEOs; a month-end pension rebalance into equities that was known in advance; Powell's "patient" pivot, which followed on 4 Jan.
- *Type:* capitulation inside an established regime, plus a known mechanical bid and a policy pivot still to come.

**B. March–June 2020.**
- *Rebound days:* every one was a policy day.
  - 2 Mar: G7 and Fed hopes.
  - 10 Mar: stimulus talk.
  - 13 Mar: national emergency declared, fiscal talk.
  - 17 Mar: the CPFF and PDCF facilities.
  - 24 Mar: the day after unlimited QE and the corporate-credit facilities.
  - 26 Mar: the CARES Act passed on the day jobless claims printed 3.3m.
  - 6 Apr: evidence the curve was flattening.
- *Crash days:* each was one of four things:
  - an exogenous shock (9 Mar, the oil price war);
  - a policy disappointment (12 Mar, when the ECB disappointed and the Fed's repo expansion failed to hold the tape);
  - policy that confirmed how bad things were (16 Mar, the Sunday-night cut to zero);
  - pure de-leveraging (18 Mar, when everything sold).
- *Aftershock:* 11 Jun followed a dour FOMC, after a rally of roughly 45% off the low (memory).
- *Lesson of 16 Mar:* a rate cut does nothing when the plumbing is broken. Funding markets and Treasury-market dysfunction were the variables that mattered.
- *Dropped from this draft:* credit and market-depth figures for this episode, which can no longer be checked from FRED.

**C. 10 Nov 2022.**
- *Catalyst:* October CPI printed 7.7% against 7.9% expected. Two-year yields fell sharply and the Nasdaq rose 7.4%.
- *Conditions:* positioning was light after a 25% bear market. The 13 Oct CPI day had already shown an intraday reversal from about −2% to +2.6% (memory).
- *Withdrawn:* draft 1's "VIX falling".
- *Type:* a squeeze on a scheduled event, with positioning washed out, inside an elevated regime.

**D. 3–9 April 2025.**
- *Sequence:*
  - Tariffs were announced after the 2 Apr close at several times what markets had priced.
  - China retaliated on 4 Apr.
  - On 7 Apr a false "pause" headline caused an intraday swing of about 8% (memory).
  - The 10-year rose 33bp over the three sessions to 9 Apr.
  - The 90-day pause came on 9 Apr.
- *After the pause:* the 10-year kept rising, to 4.48% on 11 Apr. The equity bounce did not mean bonds had calmed.
- *Type:* the administration's own policy shock, escalating a correction already under way (S&P 7.7% off its peak, VIX 1.3x February). It was reversed by the policy's author once rates moved too fast.

**E. 5 Nov 2026.**
- *Catalysts:*
  - reports on Wednesday 4 Nov that OpenAI had discussed lowering its 2027 data-center capacity expectations;
  - local data-center restrictions approved by voters, and three new governors backing construction pauses;
  - Goldman's estimate that up to 45% of planned capacity could face moratoria;
  - CoreWeave debt yielding 17%.
- *Amplifiers:*
  - Morgan Stanley QDS's estimate of $52bn of levered-ETF supply into the close, second only to $55bn on 5 Jun 2026;
  - hedge funds selling the hyperscaler shares they had bought in Wednesday's post-election rally.
- *Surface on 4 Nov:* VIX 16.6, realised vol 12.9%, contango, the S&P 1.7% off its high, no 2% day in 20 sessions. On most index gauges this was a calm, broad market.
- *Underneath:*
  - equal-weight had beaten SPY by 7.4 points in 20 sessions;
  - the Nasdaq fell 5.3% in October against the S&P's 0.9%;
  - SPY illiquidity was at its one-year extreme;
  - SPHB/SPLV fell 2.7% on 4 Nov while the index rose;
  - event-vol priced election day at about 1.2%, and the information arrived over two sessions rather than one (4 Nov rallied, 5 Nov fell).
- *Type:* a calm-surface opener. The policy response behind every completed best day is not available in its usual form: the Fed is tightening, a statement cannot reverse local moratoria, and the CoreWeave signal is a private-credit problem.

---

## 3. Findings

**3.1 There are two kinds of tail day.** Index-vol measures (VIX, realised vol, term structure, the count of recent big moves) rank tail days inside an established regime well, and they miss the day that opens an episode. 5 Nov 2026 is a clean opener. 3 Apr 2025 escalated a moderate regime: a correction was already under way and VIX stood at 1.3x its February level. The data file's T−1 table places the other eighteen days.

How rare is an opener as large as 5 Nov? §6 Part 5 counts S&P falls of 4% or more since 1990 that came with VIX below 20 and no 2% day in the prior 20 sessions. If the count is close to zero, 5 Nov 2026 is an outlier for the VIX era, and base rates built on in-regime days should be applied to it with care.

**3.2 What came before the opener was internal.** Before 5 Nov, the stress sat inside the index:
- a fast rotation (equal-weight +7.4 points in 20 sessions);
- a gap between sectors (in October, Nasdaq −5.3% against S&P −0.9%);
- thin liquidity (SPY's Amihud ratio at its one-year high, which may partly reflect volume moving away from SPY — 106e checks ES);
- high beta lagging on an up day;
- cheap event vol;
- record levered-ETF sensitivity.

The mechanism: when stocks inside the index move against each other, the moves offset. Index realised vol and VIX stay low because realised and implied correlation are low. When the rotation turns into de-grossing, correlation jumps and index vol reprices within a session.

On most breadth gauges, equal-weight beating cap-weight while the index sits near its high reads as healthy broadening. Here it was distribution in the leaders.

Precedents to test (memory): the July 2024 rotation, with implied correlation at record lows ahead of the 5 Aug 2024 spike; and February 2018's short-vol ETP rebalancing, out of a VIX in the low teens a week earlier.

The stack already carries most of these inputs: the dispersion panel, the concentration twin, HB/LV (item 100), item 98 and item 101. But it scores them separately. Nothing reads the combination "calm surface, stressed internals."

**3.3 Inside a regime, tails cluster because volatility clusters.** After a bottom-decile day, a top-decile day follows within five sessions 63% of the time, against 38% on any day. With VIX above 30 the figure is 90–96%. But a fixed decile threshold is easy to clear when daily volatility runs two or three times normal, so most of that conditional figure just restates the vol forecast.

On direction, forward returns after bottom-decile days are at or above the all-day baseline. That gives no evidence for being less long, and strong evidence for wider outcomes.

Morningstar's 8 of 10 holds at the extreme tail because the most extreme days concentrate in crises. Across all decile days, the two tails sit together 73% of the time against 65% by chance. §6 Part 4 re-runs this on vol-standardised returns to see whether anything survives beyond clustering.

**3.4 Vol management buys drawdown protection, not return.**
- Sharpe rises from 0.55 to 0.58 (0.57 after costs).
- Return falls by 2.1 points a year.
- Max drawdown improves from −56.8% to −36.5%.

Part of the return gap is simply lower average exposure. The honest comparison is a constant mix held at the same average exposure (§6 Part 6).

In underwriting terms, it works like an aggregate stop-loss. The premium is the return given up, and the recovery is the drawdown it caps. It also attaches late: a trailing-vol rule only responds once realised vol has risen, so the first day of an episode stays fully on the book (0.86 exposure into 5 Nov 2026). The out-of-sample literature reaches the same conclusion (Cederburg, O'Doherty, Wang and Yan, *Journal of Financial Economics*, 2020; memory).

**3.5 Policy responses still mark the bounces, and speed is what triggers them.** Every completed best day in the decade was either a policy day or a known mechanical bid. In 2025 the trigger was the speed of the bond move (the 10-year up 33bp in three sessions), and bonds kept selling after the pause. The trigger read should therefore key on rates of change. An equity bounce is not evidence that the plumbing has healed. This replay does not test the policy claim, so 106d stays at the hypothesis level.

**3.6 Where 2026 stands.** The episode is now in a high-vol regime by definition, because a bottom-decile day has printed. The clustering base rates therefore apply to the next five sessions. Which row applies depends on the 5 Nov VIX close, which is not yet published; the 07:00 anchor will show it. Those rates point to wider outcomes in both directions, not to a direction.

The mechanical sellers that lag have mostly not acted yet:
- One −4.4% day lifts 20-day realised vol from about 13% to about 20%. That alone would cut the study's own vol-managed rule from 0.86 to roughly 0.35 at the next rebalance. This is arithmetic on the replay inputs; Part 6 will show the exact path.
- Real vol-control funds blend longer windows and smooth their trades. If realised vol stays up, their selling spreads over the next one to three weeks.

The catalyst most likely to be missing is the usual one: a policy response. The candidates for a bounce are corporate instead, such as capex reaffirmations, a clarification from OpenAI, or Nvidia's late-November results.

---

## 4. Coverage map after the replay

The fragility inputs mostly exist. Six things are missing: the two internal tells that actually preceded 5 Nov (rotation speed and illiquidity), the forced-flow estimators, the base rates, a sizing rule, and the history to compute long-window credit percentiles.

| Condition or mechanism | Tracked today | Status |
|---|---|---|
| Index vol state (VIX, realised vol, term structure, VVIX, big-move count) | XIII regime read; vol-event attribution (item 52) | Tracked; ranks in-regime days, blind to openers |
| Rotation speed (RSP–SPY and QQQ–SPY over 20 sessions) | Concentration twin (level only) | **Speed missing**: the clearest tell before 5 Nov |
| Dispersion and implied correlation | Dispersion panel (item 18) | Tracked separately, not combined |
| Illiquidity and price impact | — | **Missing**: the other tell before 5 Nov |
| High beta vs low vol on up days | Item 100 | Pending build |
| Event-vol pricing | Item 101 | Pending build; needs a T+1/T+2 window |
| Levered-ETF sensitivity and close flow | Item 98 | Pending build |
| Vol-control, CTA and risk-parity flows | — | **Missing** (106b) |
| Dealer gamma | 6b dealer engine | Tracked from Sep 2026; replay needs FlashAlpha Alpha (106h) |
| Credit spreads over long windows | HY acceleration overlay; 20-year percentiles in metric lenses | **History at risk** after FRED's truncation (106i) |
| Funding and Treasury speed | Funding overlay; SR-36; 10y speed flag; MOVE–VIX | Tracked separately, not combined (106d) |
| Breadth and capitulation | Capitulation Count; trend-breadth | Tracked, but reads "healthy" during a rotation; needs rotation speed beside it |
| Two-sided tail base rates | — | **Missing** (106a) |
| Sizing rule | — | **Missing** (106g) |

---

## 5. Rulings for item 106

Sub-rulings a–h were accepted on 5 Nov at 22:06 as proposed in draft 1. Draft 2 proposes the amendments marked below and adds 106i. Items not marked as amended stand as accepted.

**106a — Two-sided tail base rates (XX). Amended.** Everything as accepted, plus three additions:
- the same statistics on vol-standardised returns, so the table separates true reversal from volatility clustering;
- the opener set (bottom-1% days since 1990 with VIX below 20 and no 2% day in the prior 20 sessions) as rows of its own;
- the confirmed figures printed: 63% vs 38%, 90–96% with VIX above 30, and 73% vs 65%.

~5h (was 4h).

**106b — Mechanical flow stack.** Unchanged. Build the vol-control estimator first, because that is the flow that follows an opener.

**106c — Fragility read. Amended: two reads instead of one composite.**
- *(i) Vol state:* index vol, realised vol, term structure, VVIX and the big-move count. Calibrated from 1990. This is the input to 106g's sizing.
- *(ii) Internal stress:*
  - rotation speed (RSP–SPY and QQQ–SPY as 20-session percentiles);
  - gaps between sectors and the index;
  - dispersion or implied correlation, where a keyless series exists;
  - illiquidity (106e);
  - levered-ETF sensitivity;
  - cheap event vol (101);
  - HB/LV divergence (100).

  This read is report-only, with a ledger tested on the opener set. It gets no sizing right until its ledger holds 20 openers, which will take years because openers are rare.

The daily close prints both reads on one line and flags the combination "surface calm, internals stressed." ~14h (was 12h).

**106d — Policy-put panel.** Same scope as accepted. Triggers key on speed rather than levels: three-day changes in the 10-year and 30-year, swap spreads, and SR-36.

**106e — Illiquidity. Amended: promoted from "if missing" to a core input.**
- the Amihud ratio on SPY and on ES, as one- and three-year percentiles, adjusted for the long migration of volume away from SPY;
- SPY's quoted spread, where Massive provides it.

This feeds 106c(ii). ~4h (was 3h).

**106f — Catalyst tags. Amended.** Everything as accepted, plus:
- the seed rows add 27 Feb 2020 and the opener set;
- the event-vol ledger (101) records realised moves over T, T+1 and T+2, because the midterm information took two sessions to price.

**106g — Sizing. Rewritten.**
- *(i) Book A:* once the matched-exposure control (§6 Part 6) is in, take vol-managed exposure to Doctrine #2 as a drawdown-control rule. On the replay so far it is about Sharpe-neutral, gives up return, and cuts max drawdown by about a third. Whether to adopt it is a preference about return against drawdown, not a question of evidence.
- *(ii) DTH-1:* constant-dollar-risk sizing. The stop distance is a multiple of ATR, and contracts = a fixed dollar risk ÷ the stop distance. As volatility widens, the contract count shrinks and stops stay outside the noise where algorithmic stop runs work. This replaces "halve size after a bottom-decile day."

~6h.

**106h — FlashAlpha Alpha-month replay.** Unchanged, except that the opener-set dates from 2017 onward are added.

**106i — Source for credit history. New.** FRED now serves only three years of the ICE BofA OAS series.
1. Check whether the box's store holds HY and IG OAS from before Nov 2023.
2. If it does, that history can no longer be downloaded again. Confirm the nightly backup covers it, and read study history from the store.
3. If it does not, adopt Moody's Baa minus 10-year (FRED BAA10Y, daily from 1986) as the long-window credit series, with the Fed's excess bond premium (a monthly CSV) as the slow read on credit stress.

Two earlier decisions depend on this: the 1 Oct metric-lenses ruling (20-year spread percentiles) and the HY-acceleration calibration in T&B. ~2h, plus one check on the box.

**Totals.** About 54h of sessions, about 1h by hand, and about 3h in the December Alpha month. Draft 1 said ~51h of sessions, but that figure counted 106h twice; on the same basis it was ~48h. The build order is unchanged: after Category 1, run a → b → c → d, with e, f, g and i alongside.

---

## 6. Replay parts 4–7 (Claude Code paste)

Parts 1–3 ran on 5 Nov (commit 04fd571f).

**Where to run:** the study worktree (`C:\Users\arich\projects\chester-reports-study`, branch `study/tail-days`), in the same Claude Code session that ran Parts 1–3, or a new one in that folder. Branch-only.

**Estimated run time:** 10–15 minutes.

```
You are on branch study/tail-days in the chester-reports-study worktree.

1. A new draft of docs/studies/tail-days-study-2026-11-05.md has been placed
   over the old one. Commit it alone as "study: tail days draft 2".

2. Extend tools/studies/tail_days.py and re-run it. Reuse cached data where
   it exists and fetch only what is new. Install the arch package if it is
   missing. Append Parts 4-7 to docs/studies/tail-days-2016-2026-data.md
   above the hand-written "what the data contradicts" marker, and leave
   that section untouched. Every table carries its source and as-of date;
   print "gap" for any series that is unavailable rather than substituting.

Part 4 - vol-standardised base rates. Divide each ^GSPC daily return since
1950 by the prior day's GARCH(1,1) volatility forecast (refit on data up to
each year-end and applied to the following year, so there is no look-ahead)
and, as a cross-check, by trailing 20-day realised vol. Recompute Part 2's
statistics on the standardised returns: P(top-decile day within 1, 5, 10
sessions | bottom-decile day), the clustering statistic against a shuffled
baseline, and the next 1/5/20-day standardised and raw return distributions
after bottom-decile days. Show them side by side with Part 2's raw figures.

Part 5 - calm-surface openers. Since 1990, list every day in the bottom 1%
of ^GSPC daily returns (threshold computed on 1990 onward) where VIX at T-1
(FRED VIXCLS) was below 20 and no day in the prior 20 sessions had
|return| >= 2%. Report the count, the dates, and the subset with returns
<= -4%. For each date give the Part 1 condition rows at T-1, plus: RSP/SPY
20-day relative return as a percentile of its own history (RSP from 2003,
else gap); QQQ minus SPY 20-day relative return as a percentile; sector-ETF
dispersion (cross-sectional standard deviation of the 11 sector ETFs'
20-day returns) as a percentile; and the SPY Amihud ratio as 1-year and
3-year percentiles. Then, for the 1 and 5 sessions after each opener:
return, realised range, and whether a top-decile day followed within 5
sessions.

Part 6 - vol-managed control. Repeat Part 3 beside two other rows: a
constant-mix portfolio holding the vol-managed rule's average exposure in
^GSPC with the remainder in 3-month T-bills (FRED DTB3), and buy-and-hold.
For each, report annualised return, vol, Sharpe (same definition as Part 3),
max drawdown, worst 20-day drawdown and average exposure, with and without
2bp costs. Also print the vol-managed exposure path for 2026-10-26 through
the latest available date.

Part 7 - credit substitute. For the twenty Part 1 dates, add FRED BAA10Y
(Moody's Baa minus 10y) at T-1, T-5 and T-20 with its 20-day change, and the
Federal Reserve's excess bond premium (monthly CSV on federalreserve.gov,
if reachable; else gap) for the month before each date. Report the earliest
observation FRED serves for BAMLH0A0HYM2, BAMLC0A0CM and BAA10Y.

3. After Part 7 and above the marker, add a short section headed "what the
   new parts change", listing any claim in the draft 2 study file that the
   new numbers contradict or support.

4. Commit as "study: tail days replay parts 4-7". Do not merge. Report both
   commit hashes and a five-line summary of the results.
```

---

## 7. Verify items

- The per-date T−1 tables in the data file: class each of the twenty dates as calm, moderate or in-regime. Draft 2 names only the dates reported in the replay summary.
- The box store: the earliest HY and IG OAS observation it holds (106i).
- The 5 Nov 2026 S&P close and VIX close (FRED lags), and so which clustering row applies to the week of 6 Nov.
- Realised levered-ETF rebalancing on 5 Nov against Morgan Stanley's $52bn 1pm estimate. One post-close tally said about $40bn; this is unconfirmed.
- Whether ES volume is available without a key for 106e (Massive's free futures tier, or yfinance ES=F).
- The FlashAlpha tier matrix: confirm Alpha unlocks the replay endpoints. The 403 errors on 5 Nov named Alpha as the required tier.

## 8. Sources

- Replay: `docs/studies/tail-days-2016-2026-data.md` (commit 04fd571f). Prices via the repo's yfinance fetcher; rates, spreads and VIX via FRED's public CSV.
- Morgan Stanley Derivatives, 5 Nov 2026, $52bn levered-ETF supply estimate: https://x.com/MgnStnlyDerivs/status/2118418288992493963
- Intraday moves and drivers on 5 Nov 2026: https://huggingnews.com/us-markets/nvidia-erases-2026-gains-as-ai-selloff-pushes-nasdaq-into-correction-c27f83eb
- Morgan Stanley Derivatives, 3 Nov 2026, midterm implied vs realised 1-day move (screenshot in chat).
- Morningstar Direct, "Volatility Cuts Both Ways," Morningstar US Market Index, Nov 2016–Nov 2026 (screenshot in chat).
- StockCharts SPHB:SPLV at 11:04 ET on 4 Nov 2026, as posted by @RachelDashCS (screenshot in chat).
- FlashAlpha historical coverage for SPY and tier responses, pulled 5 Nov 2026.
- From memory, to be checked: episode catalysts for 2018–2025; the July 2024 and February 2018 precedents; Cederburg et al. (2020).
