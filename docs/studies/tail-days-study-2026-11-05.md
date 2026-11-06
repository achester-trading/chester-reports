# Tail Days 2016–2026: what preceded the ten best and ten worst days, and what the stack would have seen

**Status:** draft 3, 6 Nov 2026 (morning). Supersedes draft 2 (commit 73227981). Checked against the full replay in `docs/studies/tail-days-2016-2026-data.md` (Parts 1–3 at 04fd571f, Parts 4–7 at 07ebeb6c) and the FRED and environment check in `docs/studies/fred-env-check-2026-11-05.md` (98a12839). Figures come from those files unless marked (memory). The per-date condition tables stay in the data file.
**Prompted by:** Morningstar's "Volatility Cuts Both Ways" table (Morningstar US Market Index, Nov 2016–Nov 2026), which lists 5 Nov 2026 (−4.4%) as the tenth-worst day of the decade.
**Register:** item 106 (round 8). Its change order is `docs/change-order-tail-days-item-106-2026-11-06.md`; this file is the evidence behind it. Rulings so far: 106a–h accepted 5 Nov 22:06; the draft-2 amendments to a, c, g and the new i accepted 5 Nov 23:13; the FRED fixes and the credit long-window switch accepted 6 Nov 07:20.

---

## 0. What draft 3 changes

Draft 2 corrected draft 1's main claim (that every tail day was visible in advance). Parts 4–7 now test draft 2's own claims. Four of them move.

1. **"Best days follow worst days" is volatility clustering, not reversal.** On raw returns, a top-decile day follows a bottom-decile day within five sessions 62.8% of the time, against 37.6% on any day. Divide each return by the volatility forecast at the time and the figures become 49.7% against 41.9% (GARCH) or 51.6% against 41.3% (20-day realised). The two-sided clustering statistic goes from 72.6% against a shuffled 65.1% on raw returns to 60.3% against 65.1% once standardised, which is below what a random series gives. A modest one-way residual survives (a bottom day raises the odds of a top day by about 8 points); the "same phenomenon" reading does not.
2. **Forward returns after a bottom-decile day are no better than baseline, only wider.** Draft 2 said "at or above baseline". Standardised, the next day averages −0.05% (48% positive) and the 20-day return +0.64% against a +0.69% baseline. The spread of outcomes does widen: the 10th-percentile 20-day outcome is −1.37σ against −1.23σ (GARCH) and −1.60σ against −1.33σ (realised vol). That is the only basis for any post-tail sizing rule.
3. **"Calm surface, stressed internals" describes 5 Nov 2026 and nothing else.** Since 1990 there are 93 days in the bottom 1% (−3.11% or worse). Six came out of a calm market (VIX below 20 the day before, no 2% day in the prior 20 sessions): 15 Nov 1991, 27 Feb 2007, 24 Jun 2016, 10 Oct 2018, 24 Feb 2020 and 5 Nov 2026. Only 5 Nov 2026 fell 4% or more, and only 5 Nov 2026 had extreme internals (equal-weight over SPY at the 100th percentile of its history, QQQ over SPY at the 2nd, sector dispersion at the 99th). Before the other five, the same readings sat between the 8th and 96th percentiles, and SPY was unusually liquid (Amihud 1-year percentile 2–5) in three of them. So the internal-stress read (106c(ii)) has one hit, the case that inspired it, and it is built only if an out-of-sample test passes (§5).
4. **Vol management is insurance, priced higher than draft 2 said.** Against a constant mix at the rule's own average exposure (0.90), the rule gives up about 1.4 points a year on top of the 0.7 points that lower exposure alone costs (6.46% against 7.88% against 8.59% buy-and-hold, cash at zero; 6.68% against 8.16% with cash at T-bill rates). On returns in excess of T-bills its Sharpe is lower than the mix's (0.36–0.38 against 0.38–0.40), not higher. What it buys: max drawdown −32.7% to −36.5% against −52.7%, and a worst 20 sessions of −11.0% against −28.2%. The "about Sharpe-neutral" line in draft 2 held only with cash at zero.

Smaller changes:
- The 5 Nov close lifted 20-day realised vol from 12.9% to 20.2%, which sets the study rule's exposure at 0.35 for 6 Nov (from 0.86 held into 5 Nov). Draft 2's estimate of "about 0.35" is confirmed.
- Credit gave no warning before 5 Nov on any aggregate series: Baa minus the 10-year was 152bp the day before (+6bp over 20 observations; post-1990 median 213bp, 90th percentile 315bp), and the Fed's excess bond premium for October was −0.27. Before 9 Mar 2020 the same spread had widened 50bp in 20 observations; before 3–4 Apr 2025, 16–30bp.
- The box's own database holds no ICE BofA spread history before 30 May 2023 (VPS query, 6 Nov; the aa/bbb/aaa/EM/euro series start Sep–Oct 2023). FRED now serves those series only from 6 Nov 2023. Nothing older can be recovered, so Baa−10y (daily from 1986) and the excess bond premium (monthly from 1973) become the long-window credit series (106i).
- The FRED check found no holiday-handling bug in production (every path into the store drops FRED's blank rows; only the study script had the bug, fixed at 07ebeb6c). It found two labels that overstate their window: the credit dimension's percentile (configured as 5 years, printed with no window) and the compact metric-lens cell (prints "(20y)" with no count). Both run on 3.4 years of data. Fixes are the first part of 106i.
- The SPY illiquidity reading before 5 Nov was the 100th percentile on one year but the 72nd on three. The three-year read is the one to carry (106e).
- Draft 2's hours for 106 are restated in the change order: about 54h of sessions, 61h if the internal-stress test passes, plus 1h by hand and 3h in December.

**Gaps:** VIX for 5 Nov 2026 (FRED lag; the 07:00 anchor has it); every ICE BofA figure before Nov 2023; intraday levels; all positioning, dealer-gamma and catalyst claims, which the replay does not test.

---

## 1. Five episodes, and a sixth class

The twenty Morningstar days fall into five episodes; fourteen sit in one six-week window of 2020. Morningstar's percentages; S&P 500 equivalents differ by a few tenths, and on the S&P 5 Nov 2026 ranks 11th of the decade (27 Feb 2020, −4.42%, is 9th).

| Episode | Worst days | Best days | Vol state the day before the first listed day |
|---|---|---|---|
| A. Q4 2018 | — | 26 Dec 2018 +5.0% | In regime: VIX 36.07, drawdown −19.8% |
| B. COVID, Mar–Jun 2020 | 9, 11, 12, 16, 18 Mar; 1 Apr; 11 Jun | 2, 10, 13, 17, 24, 26 Mar; 6 Apr | In regime from 24 Feb (the opener, −3.35%, VIX 17.08 the day before) |
| C. 2022 bear market | — | 10 Nov 2022 +5.7% | Elevated: VIX 26.09, drawdown −21.8% |
| D. April 2025 tariffs | 3 Apr −5.0%, 4 Apr −5.9% | 9 Apr +9.6% | Moderate: VIX 21.51 (1.3x its February median), drawdown −7.7% |
| E. Nov 2026 AI capex / midterm policy | 5 Nov −4.4% | none yet | Calm: VIX 16.61, realised vol 12.9%, contango, drawdown −1.7%, no 2% day in 20 sessions |

The sixth class is the **calm-surface opener**: a bottom-1% day with VIX below 20 the day before and no 2% day in the prior 20 sessions. Six since 1990, one every six years. 5 Nov 2026 is the only one at −4% or worse. Catalysts (memory, not tested by the replay): a Senate vote and biotech selloff (1991), the Shanghai crash (2007), the Brexit vote (2016), a rates-led de-grossing (2018), the Italian COVID weekend (2020), and post-midterm data-center policy news plus OpenAI's capacity reports (2026). Four of the six were exogenous or scheduled shocks.

Two well-known near-misses fail the definition narrowly (memory; to be checked in Part 8): 5 Feb 2018 (−4.1%, but the prior session fell 2.1%) and 5 Aug 2024 (−3.0%, VIX 23 the day before). A looser class that admits them is part of the 106c(ii) test.

---

## 2. Episode notes

Catalysts and mechanisms; figures in the data file §1 and §4.

**A. 26 Dec 2018.** The 19 Dec FOMC hike and "autopilot" remark; Christmas Eve capitulation in a thin tape (−19.8% from the 20 Sep high; VIX 36.07); Mnuchin's calls to bank CEOs; a month-end pension rebalance known in advance; Powell's "patient" pivot on 4 Jan. (Catalysts: memory.) Type: capitulation inside an established regime plus a known mechanical bid and a policy pivot still to come.

**B. March–June 2020.** The 24–28 Feb week took the S&P down 11.5% and VIX from 17.08 to 40.11. Every rebound day was a policy day (G7/Fed hopes 2 Mar; stimulus talk 10 Mar; national emergency 13 Mar; CPFF/PDCF 17 Mar; the day after unlimited QE 24 Mar; CARES Act 26 Mar; curve-flattening evidence 6 Apr). The crash days were an exogenous shock (9 Mar, oil), a policy disappointment (12 Mar), policy that confirmed severity (16 Mar, the Sunday cut to zero, with VIX 57.83 the day before and the S&P already −19.9%), and pure de-leveraging (18 Mar). The aftershock on 11 Jun followed a dour FOMC after a 44.5% rally from the 23 Mar close, with VIX going 27.57 to 40.79. Baa−10y went from 204bp (20 sessions before 16 Mar) to 431bp the day before the 24 Mar bounce; the excess bond premium printed +1.19 for March. Lesson of 16 Mar: a rate cut does nothing when the plumbing is broken; funding and Treasury-market dysfunction were the variables that mattered (memory for the plumbing detail; the ICE BofA figures are unverifiable).

**C. 10 Nov 2022.** October CPI at 7.7% against 7.9% expected; Nasdaq +7.4% (memory). Positioning light after a 25.4% bear market. VIX 26.09 the day before, 25.30 a week earlier: elevated, not falling. Baa−10y 233bp, +6bp over 20. Type: a scheduled-event squeeze on washed-out positioning inside an elevated regime.

**D. 3–9 April 2025.** Tariffs announced after the 2 Apr close at several times what was priced; China retaliated 4 Apr; a false "pause" headline on 7 Apr; the 10-year from 4.01% (4 Apr) to 4.34% (9 Apr), +33bp in three sessions, and on to 4.48% by 11 Apr after the pause; the 90-day pause on 9 Apr with VIX 52.33 the day before. HY OAS went 268bp (19 Feb) to 461bp (7 Apr). Type: the administration's own policy shock, escalating a correction already under way (S&P −7.7%, VIX 1.3x February), reversed by its author once rates moved too fast. The equity bounce did not mean bonds had calmed.

**E. 5 Nov 2026.** Catalysts: reports on 4 Nov that OpenAI had discussed lowering its 2027 data-center capacity expectations; voter-approved local data-center restrictions and three incoming governors backing construction pauses; Goldman's estimate that up to 45% of planned capacity could face moratoria; CoreWeave debt at 17%. Amplifiers: Morgan Stanley QDS's estimate of $52bn of levered-ETF supply into the close (second to $55bn on 5 Jun 2026); hedge funds selling the hyperscaler shares bought in the 4 Nov post-election rally.

Surface on 4 Nov: VIX 16.61, realised vol 12.9%, VIX/VIX3M 0.884, S&P 1.7% off its high, 7 of 11 sectors above their 50-day average, no 2% day in 20 sessions, Baa−10y 152bp, HY OAS 332bp (+23bp over 20). Underneath: equal-weight had beaten SPY by 7.38 points in 20 sessions (100th percentile of RSP's history), QQQ had trailed SPY by 7.34 (2nd percentile), sector dispersion was at the 99th percentile, SPY's Amihud illiquidity at the 100th one-year and 72nd three-year percentile, SPHB/SPLV fell 2.73% on 4 Nov while the index rose 1.58%, and event vol had priced election day at about 1.2% (MS QDS, 3 Nov) with the information arriving over two sessions. October was a Nasdaq move, not an S&P one: Nasdaq −5.3%, S&P −0.9%; the 22 Oct and 30 Oct drops were −2.60% and −2.86% on the Nasdaq against −1.21% and −1.82% on the S&P. The S&P closed 5 Nov at −4.36% (about 7,353, from the 4 Nov close of 7,688.62) with 20-day realised vol at 20.2%.

Type: a calm-surface opener with a structural political catalyst. The policy response behind every completed best day is not available in its usual form: the Fed is tightening, a statement cannot reverse local moratoria, and the CoreWeave signal is a private-credit problem that aggregate spreads did not register.

---

## 3. Findings

**3.1 There are two kinds of tail day.** Index-vol measures rank the in-regime days well: at T−1 the ten worst days had a median VIX of 44.6, a median drawdown of −13.6% and a median of 8 big-move days in the prior 20; the ten best, 53.4, −24.2% and 10. They do not see openers: at T−20 the ten worst days' median VIX was 15.4 with no big-move days, and 5 Nov 2026 kept that reading all the way to T−1. The opener class is small (six in 36 years) and 5 Nov 2026 is its only −4% member, so base rates built on in-regime days should be applied to it with care.

**3.2 What preceded the 2026 opener was internal, and that is one observation.** Rotation speed, sector dispersion, high beta sold on an up day, thin SPY liquidity, cheap event vol and record levered-ETF sensitivity all sat at extremes on 4 Nov. The mechanism is plausible: when stocks inside the index move against each other, the moves offset, index realised vol and VIX stay low, and the first day the rotation turns into de-grossing, correlation jumps and index vol reprices within a session. But Part 5 shows the five earlier openers carried none of these readings, and most breadth gauges read equal-weight outperformance near a high as healthy broadening. The honest status of "calm surface, stressed internals" is a hypothesis with one supporting case. It earns a pre-registered out-of-sample test (§5, 106c(ii)), not a build.

**3.3 Inside a regime, tails cluster because volatility clusters.** Raw: a top-decile day follows a bottom-decile day within five sessions 62.8% of the time (37.6% any day), 79.5% when VIX was 20–30 the day before, 89.7% at 30–45 and 95.7% above 45. Standardised by the volatility forecast: 49.7% against 41.9%. Across all decile days the two tails sit together 72.6% of the time raw against 65.1% by chance, and 60.3% standardised. Morningstar's 8 of 10 reproduces on the S&P and holds at the extreme tail because the most extreme days concentrate in crises; it says nothing about reversal. On direction, standardised forward returns after a bottom-decile day are baseline (+0.11σ over 20 sessions against +0.15σ) with a slightly negative next day (−0.05%, 48% positive). What widens is the spread of outcomes.

**3.4 Vol management buys drawdown protection and nothing else.** Figures in §0 item 4. The rule attaches late: it responds only once realised vol has risen, so an episode's first day stays on the book (0.86 held into 5 Nov; 0.25 on 18 of the 20 Morningstar dates, which were all in-regime). It then cuts both tails: the ten worst days summed −20.1% for the rule against −64.6% for buy-and-hold, the ten best +16.9% against +67.5%. In underwriting terms it is an aggregate stop-loss with a late attachment point; the premium is 1.4–2.1 points of return a year and the recovery is about 20 points of max drawdown and about 17 points of worst-20-session loss. Whether that premium is worth paying is a preference about return against drawdown for Book A (106g(i) prices the variants); it is not a question the evidence decides. The out-of-sample literature reaches the same place (Cederburg, O'Doherty, Wang and Yan, *Journal of Financial Economics*, 2020; memory).

**3.5 Policy responses mark the bounces, and speed is what triggers them.** Every completed best day was a policy day or a known mechanical bid, and in 2025 the trigger was the speed of the bond move. Part 7 adds that Baa−10y speed is a usable trigger with history back to 1986: +50bp in 20 observations before 9 Mar 2020, +125 by 16 Mar, +218 the day before the 24 Mar bounce; +16 to +30 before 3–4 Apr 2025; +6 before 5 Nov 2026. The policy-put read (106d) keys on rates of change in Treasuries, swap spreads, the basis-trade proxy and Baa−10y, with an availability read from the Fed scenario matrix. The replay does not test the policy claim itself; it stays at the hypothesis level.

**3.6 Where 2026 stands.** A bottom-decile day has printed, so the clustering rates apply to the next five sessions; which VIX row applies depends on the 5 Nov close, which the 07:00 anchor shows. Those rates mean wider outcomes in both directions, not a direction. The five earlier openers are the closest precedents: the next session was down in three of five (−1.81%, −2.06%, −3.03%; +0.68% and +0.56% in the other two), five sessions later the index was lower in three of five, the five-session range ran from 2.8% to 12.1% (Feb 2020), and a top-decile day printed within five sessions in four of five. The slower mechanical sellers have mostly not acted yet: the study rule itself drops from 0.86 to 0.35 at the 6 Nov open, and real vol-control funds spread the equivalent over one to three weeks if realised vol stays up. The catalyst most likely to be missing is the usual one, a policy response; candidates for a bounce are corporate (capex reaffirmations, an OpenAI clarification, Nvidia's late-November results) and the 11 Nov MSCI review is already under watch.

---

## 4. Coverage map after the full replay

| Condition or mechanism | Tracked today | Status |
|---|---|---|
| Index vol state (VIX, realised vol, term structure, VVIX, big-move count) | XIII regime read; vol-event attribution (item 52) | Tracked; ranks in-regime days, blind to openers; no daily state with transition base rates (106c(i)) |
| Rotation speed, sector dispersion, implied correlation | Concentration twin (level); dispersion panel (item 18) | Separate, not combined; one-case evidence → test first (106c(ii)) |
| Illiquidity and price impact | — | **Missing**; 3-year percentile is the read (106e) |
| High beta vs low vol on up days | Item 100 | Pending build |
| Event-vol pricing | Item 101 | Pending build; T, T+1, T+2 window (106f) |
| Levered-ETF sensitivity and close flow | Item 98 | Pending build |
| Vol-control, CTA and risk-parity flows | — | **Missing** (106b) |
| Dealer gamma | 6b dealer engine | From Sep 2026; replay needs FlashAlpha Alpha (106h) |
| Credit spreads over long windows | HY acceleration overlay; metric lenses; credit dimension | **3.4 years of data behind 5y and 20y labels**; no older history exists (106i) |
| Credit speed with long history | — | Baa−10y Δ20 from 1986 (106d, 106i) |
| Funding and Treasury speed | Funding overlay; SR-36; 10y speed flag; MOVE–VIX | Tracked separately, not composed (106d) |
| Breadth and capitulation | Capitulation Count; trend-breadth | Tracked; reads "healthy" during a rotation |
| Two-sided tail base rates | — | **Missing**; standardised figures lead (106a) |
| Sizing rule | — | **Missing** (106g) |
| FRED holiday rows | All store paths drop them | Correct in production; n-session measures count observations (label fix in 106i) |

---

## 5. Rulings for item 106 — state after the replay

The controlling text is the change order. Summary of where each sub-item stands:

- **106a** Two-sided tail base rates in XX. Prints raw and standardised side by side, leads with the standardised, describes clustering as a volatility phenomenon, and carries the opener set as rows of its own. ~5h.
- **106b** Mechanical flow stack extending item 98; the vol-control estimator first. ~15h.
- **106c(i)** Vol-state read: index vol, realised vol, term structure, VVIX, big-move count, calibrated from 1990; the input to 106g sizing. ~7h.
- **106c(ii)** Internal-stress read: built only if a pre-registered test passes. The test (Part 8 of the replay): on every session since May 2003, does adding the internal set (rotation speed, QQQ−SPY, sector dispersion, Amihud 1y/3y, HB/LV change and divergence) to the vol-state set improve out-of-sample forecasts of next-10-session realised vol and of a 2% day, fit on expanding windows refit each year-end? Pass if, on the subset with VIX below 20, the combined model beats vol-state alone on both the realised-vol R² and the 2%-day AUC with bootstrap 90% intervals excluding zero. If it passes, build (~7h), report-only, with a sizing right only after the improvement holds at two annual reviews. The 20-opener gate is dropped.
- **106d** Policy-put panel, triggers on speed (10y and 30y 3-session changes, swap spreads, SR-36, Baa−10y Δ20), availability from the Fed scenario matrix. ~8h.
- **106e** Illiquidity as a core input: Amihud on SPY and ES as 1- and 3-year percentiles (the 3-year carried), SPY quoted spread where Massive provides it. ~4h.
- **106f** Catalyst-class tags; seed rows add 27 Feb 2020 and the six openers; item 101's realised window becomes T, T+1, T+2. ~1h by hand.
- **106g(i)** Book A: the vol-managed rule and two cheaper variants (0.5 floor; VIX-based) priced as premium (return given up against the matched mix) and recovery (drawdown avoided), to Doctrine #2 as options. Part 9 of the replay. ~1h.
- **106g(ii)** DTH-1: constant-dollar-risk sizing (stop at an ATR multiple; contracts = fixed dollar risk ÷ stop distance). Replaces "halve after a bad day". ~6h.
- **106h** FlashAlpha Alpha-month replay in December (Alpha, not Growth), adding the opener dates from 2017 on. ~3h then.
- **106i** Credit history and the FRED fixes, first in the build order because two live labels are wrong today: honest window spans on the credit dimension and the compact lens cell; a guard so CSV writes never shorten a series; the bank-stress calibration reading the store with Baa−10y before 2023; "sessions" in the names of observation-count measures; Baa−10y and the excess bond premium into the store as the credit family's long-window series, with HY OAS keeping a 5-year lens under an honest label; studies in their own virtual environment. ~5h.

---

## 6. Replay parts 8–9 (Claude Code paste)

Parts 1–7 are done (04fd571f, 07ebeb6c). Parts 8 and 9 run the 106c(ii) test and the 106g(i) pricing. Issued in chat on 6 Nov; recorded here.

**Where to run:** the study worktree (`C:\Users\arich\projects\chester-reports-study`, branch `study/tail-days`), in a Claude Code session opened there. Branch-only. **Estimated run time:** 20–30 minutes, about ten of them creating the study environment.

```
You are on branch study/tail-days in the chester-reports-study worktree.

0. Study environment. Create a virtual environment at .venv-study inside
   this worktree (make sure .venv-study is gitignored; add the line if it
   is not), install requirements.txt plus arch into it, and run everything
   below from it. Do not touch ../chester-reports/.venv or install anything
   into it.

1. A new draft of docs/studies/tail-days-study-2026-11-05.md has been placed
   over draft 2. Check that line 3 starts "**Status:** draft 3"; if not, stop
   and tell me. Otherwise commit that file alone as "study: tail days draft 3".

2. Extend tools/studies/tail_days.py with Parts 8 and 9 and re-run it from
   the cache in ~/.cache/chester-study/tail_days/, fetching only what is new.
   Append the new parts above the NEW-PARTS-CHANGE marker and leave both
   hand-written sections untouched. Every table carries its source and
   as-of date; print "gap" rather than substituting.

Part 8 - internal-stress test (pre-registered in the study, section 5).
Sample: every session from 2003-05-01 (RSP's first day) to 2026-10-22, so
that every target window is complete. Features at each close t:
  vol-state set S: VIX (FRED VIXCLS), RV20, VIX minus RV20, VIX/VIX3M
  (from 2006-07, else gap), VVIX (from 2007-01, else gap), count of
  |ret| > 2% in the prior 20 sessions, drawdown from the 252-session high;
  internal set I: RSP-SPY 20-session relative return and its expanding
  percentile, QQQ-SPY 20-session relative return, sector-SPDR dispersion
  (20-session, as in Part 5.3), SPY Amihud 1-year and 3-year percentiles,
  SPHB/SPLV 20-session change (from 2011-06, else gap), and the one-day
  divergence (SPY return minus SPHB/SPLV return on day t).
Targets over t+1..t+10: (a) log of realised vol; (b) any |ret| >= 2%;
(c) any ret <= -3%.
Models: linear regression for (a), logistic regression for (b) and (c),
standardised features, missing features filled with the training mean and
a missing flag. Fit on an expanding window refit at each year-end from
2007 onward and applied to the following year, so predictions run 2008 to
2026 out of sample. Compare S-only against S+I. Report out-of-sample R2 for
(a) and AUC and Brier for (b) and (c): over all sessions, and over the
subset with VIX < 20 at t. Give 90% intervals for each difference
(S+I minus S) from a block bootstrap of 500 draws with 21-session blocks.
State in one line whether the pre-registered pass criterion is met: on the
VIX < 20 subset, S+I beats S on both the (a) R2 and the (b) AUC with both
90% intervals above zero. Also print the standardised coefficients of the
I features in the final fit with their signs across refits.
Then the looser opener class: bottom-1% days since 1990 with VIX < 25 at
T-1 and at most one |ret| >= 2% in the prior 20 sessions. List them with
the Part 5.3 internals at T-1 and the Part 5.4 aftermath, and say whether
2018-02-05 and 2024-08-05 are in the class.

Part 9 - vol-managed variants (106g(i)). On ^GSPC since 1990 with cash and
borrowing at DTB3 and 2bp per unit of turnover, run: (A) Part 3's rule;
(B) the same with a 0.5 floor; (C) VIX-based, exposure = min(1.5,
max(0.25, (12 / VIX at the close)^2)); (D) Part 3's rule on the average of
20- and 60-session realised vol; (E) Part 3's rule with a 10% target. For
each variant also run a constant mix at the variant's own average exposure.
Report CAGR, vol, Sharpe in excess of DTB3, max drawdown, worst 20
sessions, average exposure, turnover, then premium = CAGR(mix) minus
CAGR(variant) and recovery = max drawdown(mix) minus max drawdown(variant),
and the exposure each variant held on 2026-11-05 and set at its close.

3. Above the NEW-PARTS-CHANGE marker, add a section headed "what parts 8-9
   change" listing any claim in the draft 3 study that the new numbers
   contradict or support, including whether 106c(ii) passes its test.

4. Commit as "study: tail days replay parts 8-9". Do not merge. Report the
   commit hashes, the pass/fail line, and a five-line summary.
```

---

## 7. Verify items

- The 5 Nov 2026 VIX close and which Part 2.3 row applies to the week of 6 Nov (07:00 anchor).
- Realised levered-ETF rebalancing on 5 Nov against the $52bn 1pm estimate (one unconfirmed tally said about $40bn).
- ES volume without a key for 106e (Massive's free futures tier, or yfinance ES=F).
- The catalyst labels for the five earlier openers (§1), which are from memory.
- The FlashAlpha tier matrix: Alpha unlocks the replay endpoints (the 403s on 5 Nov named Alpha).
- Whether the VPS has weasyprint (the laptop environment does not; PDFs are presumably built on the box).
- T&B's `timeseries.db` and whether it holds any HY series older than May 2023 (the harness config already names the Baa proxy for unstored episodes, so nothing depends on it).

## 8. Sources

- Replay: `docs/studies/tail-days-2016-2026-data.md` (04fd571f, 07ebeb6c). Prices via the repo's yfinance fetcher; VIX, rates, spreads, bills via FRED's public CSV; the excess bond premium via the Federal Reserve's FEDS Notes CSV.
- Check: `docs/studies/fred-env-check-2026-11-05.md` (98a12839).
- VPS observation-store query, 6 Nov 2026 11:43 UTC: `fred.hy_oas`, `fred.ig_oas`, `fred.bb_oas`, `fred.ccc_oas` from 2023-05-30; `fred.aa_oas`, `fred.bbb_oas` from 2023-09-26; `fred.em_corp_oas`, `fred.em_hy_oas` from 2023-10-17; `fred.aaa_oas`, `fred.euro_hy_oas` from 2023-10-23.
- Morgan Stanley Derivatives, 5 Nov 2026 ($52bn estimate): https://x.com/MgnStnlyDerivs/status/2118418288992493963 ; 3 Nov 2026 (midterm implied move; screenshot in chat).
- 5 Nov 2026 drivers: https://huggingnews.com/us-markets/nvidia-erases-2026-gains-as-ai-selloff-pushes-nasdaq-into-correction-c27f83eb
- Morningstar Direct, "Volatility Cuts Both Ways", Nov 2016–Nov 2026 (screenshot in chat).
- From memory, marked in the text: episode catalysts; opener catalysts; the 2018 and 2024 near-misses; Cederburg et al. (2020).
