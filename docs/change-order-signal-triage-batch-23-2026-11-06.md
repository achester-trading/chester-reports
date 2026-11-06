# Change order — Signal triage Batch 23 (item 124): the tail-days study

| | |
|---|---|
| File | `docs/change-order-signal-triage-batch-23-2026-11-06.md` (drafted as `docs/change-order-tail-days-item-106-2026-11-06.md`; that name is recorded here and not used) |
| Status | **RULED in chat** 5–6 Nov 2026 (sub-items a–i; the order's §10); its decisions D-1 to D-4 ruled and the filing accepted 6 Nov 2026, 07:47 ET, recorded as D60 (`docs/briefs/rulings-2026-11-06.md`). Filed 6 Nov 2026 by paste B129 with filing amendments Q1 to Q6 (§0). The order as drafted in the triage chat is kept at `docs/pastes/B129-attachment-item-124.md`, people's names replaced as the note under §0 says. |
| Encoding | Batch 23 of Post-Freeze Amendment #4, one item, 124 (the order's "106"; sub-items 124a to 124i) (Q1). Register numbers provisional, SR-81 to SR-85, SR-86 reserved, placed by Audit #5 (Q2). |
| Precedence | Below Part 26, the Enterprise Layer order and the dated change-orders edition; equal to the other Amendment #4 batches. Amendments govern their parent items from filing. Tranche 0 binds its build paste (A126). |
| Supersedes | Nothing. |
| Totals | ≈ 54 h of sessions (≈ 61 h if 124c(ii) passes its test) · ≈ 1 h by hand once · ≈ 3 h in the December vendor month. The triage chat's estimates. |
| Built by | Tranche 0: A126 (`a126-item-124-tranche-0`), merged Monday 9 Nov. Tranche 1 in the weekend queue of 7–8 Nov; Tranches 2 and 3 confirmed by Audit #5 (Q5). |

---

## 0. Filing amendments Q1–Q6 (paste B129; ruled 6 Nov 2026, 07:47 ET, D60)

- **Q1, encoding.** Batch 23 of Amendment #4, one item, 124 (the order's "106"; sub-items 124a to 124i), as Batch 18 filed item 98 alone. The order's "same batch number as the round-8 file" is superseded; the round-8 file is Batch 22, items 116–123.

  | Order | Filed |
  |---|---|
  | 106 | 124 |
  | 106a … 106i | 124a … 124i (and so for each part, e.g. 106i.1 is 124i.1) |
  | item 98 | 116 |
  | item 100 | 118 |
  | item 101 | 119 |
  | item 103 | 121 |
  | items 92–105, "the batch file", "batch-17 Tranche A" | Batch 17 (92–97) and Batch 22 (116–123); "batch-17 Tranche A" is Batch 22's Tranche A |

  Items 52 and 97, SR-36 and the 1 Oct metric-lenses ruling are the filed items of those names and stand as written.

- **Q2, register.** Provisional, placed by Audit #5, after Batch 22's SR-80: SR-81 124a (two-sided tail base rates), SR-82 124b (mechanical flow stack), SR-83 124c(i) (vol-state read), SR-84 124d (policy-put trigger panel), SR-85 124e (illiquidity proxy); SR-86 reserved for 124c(ii), assigned only if its pre-registered test passes. 124f, 124g, 124h and 124i are amendments and work, recorded against their parents (items 52 and 119; the Doctrine's Book A rule table and DTH-1; the 1 Oct metric-lenses ruling).

- **Q3, decisions.** D-1 to D-4 accepted as recommended, with one amendment to D-1: ES volume comes from the stored ES bars or Massive's futures tier, never a new yfinance dependency (yfinance retires 22 Dec 2026 – 8 Jan 2027 under the price migration); a gap if neither carries volume.

- **Q4, 106i.1 amended.** Baa less the 10-year is the existing `calc.baa_less_10y` / `calc.baa_less_10y_m` (6i-3; daily from 1986, monthly from 1962); no `fred.baa10y` is added; only `fed.ebp` and `fed.gz_spread` are new series. Every reference to `fred.baa10y` in the order reads `calc.baa_less_10y`.

- **Q5, placement.** Tranche 0 is paste A126 (branch `a126-item-124-tranche-0`, from main after chain-11), merged Monday 9 Nov with the week-after set, not before the 8 Nov Weekly; Tranche 1 in the weekend queue of 7–8 Nov behind Batch 22's Tranche A; 124a is a library-stream paste (a dated-appendix table in Base Rates, by the library's dated-content rule); 124g(i)'s priced Book A table goes to Doctrine #2 beside the pack only if the replay's Parts 8–9 have run and been read by Saturday 07:00 ET, otherwise to Doctrine #3; Audit #5 confirms Tranches 2 and 3.

- **Q6, evidence.** The study branch `study/tail-days` was not on the remote when the order was drafted; the order's commit references are to the operator's study worktree until it is pushed (noted, not blocking).

**Names** (D5, D38, the standing rule: no person's name in committed files). The literature line's authors are replaced by "a 2017 study of volatility-managed portfolios, and a 2020 study re-testing it across markets", and the operator by "the operator". The "Warsh scenario matrix" keeps its name, the system's established term for that matrix. Institutions stay. Everything else is verbatim.

---

The order as drafted follows, its body unedited; §0 governs where they differ.

---

# Change Order — Signal Triage, Round 8: Item 106 (Tail Days)

**File:** `docs/change-order-tail-days-item-106-2026-11-06.md`
**Status:** RULED (sub-items a–i; see §10 for the dates). Four filing decisions in §7 pending. Filing pending.
**Encoding:** Companion to the round-8 batch (`docs/change-order-signal-triage-batch-17-2026-11-05.md`, items 92–105). Same batch number as that file takes at filing; this order carries item 106 only, because its evidence base is a study rather than a post.
**Precedence:** Below Architecture Part 26 and the governing text of Amendment #4; equal in rank to the other Amendment #4 batches. Binds Claude Code sessions once filed. Tranche 0 (§6) binds the next build paste regardless of filing, because it corrects labels that are printing in live reports.
**Evidence:** `docs/studies/tail-days-study-2026-11-05.md` (draft 3), `docs/studies/tail-days-2016-2026-data.md` (Parts 1–7), `docs/studies/fred-env-check-2026-11-05.md`, all on branch `study/tail-days`, unmerged. Figures below come from those files.

---

## 1. Summary

Morningstar's "Volatility Cuts Both Ways" table prompted a study of the decade's ten best and ten worst days: what preceded them, what the stack would have seen, and what to add. The study ran a data replay on the box's own fetchers (Parts 1–7) and a read-only check of the repo's FRED handling. The findings that drive the rulings:

- Tail days inside an established high-volatility regime were visible beforehand on index-vol measures; the day that opened the current episode (5 Nov 2026) was not. It is one of six "calm-surface openers" since 1990 and the only one at −4% or worse.
- "Best days follow worst days" is volatility clustering. Standardised by the volatility forecast, the two-sided clustering statistic falls below a shuffled baseline (60.3% against 65.1%); only a one-way residual of about 8 points survives.
- Forward returns after a bottom-decile day are baseline, not better; only the spread widens. So post-tail sizing rests on dispersion, never on drift.
- Vol-managed exposure is insurance: it costs 1.4–2.1 points of return a year against a matched constant mix and buys about 20 points of max drawdown; its Sharpe in excess of T-bills is slightly lower, not higher.
- "Calm surface, stressed internals" described 5 Nov 2026 and none of the five earlier openers. It becomes a pre-registered test, not a build.
- Aggregate credit gave no warning before 5 Nov; Baa−10y speed did precede 2020 and 2025 and has history to 1986.
- The box's observation store holds no ICE BofA spread history before 30 May 2023, and FRED now serves those series only from 6 Nov 2023. Two live labels (the credit dimension's percentile and the compact metric-lens cell) imply 5- and 20-year windows over 3.4 years of data.

Rights stay at report lines, flags, ledgers and base-rate rows, plus one sizing modifier (106c(i) → 106g) that changes size, never direction. No composite weight changes; no regime state or tag (R28).

| Sub-item | What | Rights | Hours |
|---|---|---|---|
| 106i | Credit history source; FRED label and guard fixes; study environment | Report labels; new series | ~5h (Tranche 0) |
| 106a | Two-sided tail base rates (XX), standardised figures leading | Base-rate rows | ~5h |
| 106b | Mechanical flow stack (vol-control, CTA, risk parity) beside item 98 | Report line; flag | ~15h |
| 106c(i) | Vol-state read, calibrated from 1990 | Daily line; sizing input to 106g | ~7h |
| 106c(ii) | Internal-stress read, built only if its test passes | Report-only | ~3h test + ~7h conditional |
| 106d | Policy-put trigger panel, speed-based | Report line; "policy-put unavailable" flag | ~8h |
| 106e | Illiquidity / price-impact proxy as a core input | Tape line; input to c(ii) | ~4h |
| 106f | Catalyst-class tags; seed rows; item 101 window T, T+1, T+2 | Ledger fields | ~1h by hand |
| 106g | Sizing: Book A vol-managed variants priced; DTH-1 constant-dollar-risk | Book A rule candidate; DTH-1 rule | ~7h |
| 106h | FlashAlpha Alpha-month replay of the tail dates | Study | ~3h (December) |

Work order: about 54h of sessions (61h if 106c(ii) passes its test), about 1h by hand once, about 3h in the December Alpha month.

---

## 2. Corrections since the chat

1. The draft-1 and draft-2 hours double-counted 106h once; §6 is the itemised total.
2. "5 Nov is the tenth-worst day" holds on Morningstar's index; on the S&P 500 it ranks 11th of the decade.
3. The SPY illiquidity reading before 5 Nov was the 100th percentile on one year and the 72nd on three; the three-year read is carried.
4. Draft 2's "forward returns at or above baseline after a bottom-decile day" is withdrawn; standardised, they are baseline.
5. Draft 2's "about Sharpe-neutral" for the vol-managed rule held only with cash at zero.

---

## 3. Entries

### 106i — Credit history source; FRED label and guard fixes; study environment

**Finding.** FRED's ICE BofA OAS series now carry a rolling three-year window (first observation 6 Nov 2023 on the public CSV). The box's observation store, queried read-only on 6 Nov, holds `fred.hy_oas`, `fred.ig_oas`, `fred.bb_oas` and `fred.ccc_oas` from 30 May 2023 (csv-migrated, backfilled and daily sources), the aa/bbb series from 26 Sep 2023, EM from 17 Oct 2023, aaa and euro HY from 23 Oct 2023. Nothing older exists anywhere in the system, so there is nothing to protect in the backup; the question is what carries the long-window credit reads. The FRED check found production holiday handling correct on every path into the store, nothing re-pulling history per run except one calibration script, and two labels that overstate their window. It also found that `fred.pull(full=True)` and the `lookback_days` path pass `merge=False`, which would rewrite a series' CSV copy with only what FRED serves now, and that the study's `arch` install changed seven other packages in the shared environment (pip check clean; no repo code imports any of them).

**Ruling (accepted 5 Nov 23:13 for the source question; 6 Nov 07:20 for the six fixes and the lens switch).**

- **106i.1 Long-window credit series.** Add `fred.baa10y` (FRED BAA10Y, Moody's seasoned Baa less the 10-year, daily from 2 Jan 1986) and `fed.ebp` / `fed.gz_spread` (the Federal Reserve's excess bond premium and GZ spread, monthly CSV at federalreserve.gov/econres/notes/feds-notes/ebp_csv.csv, from Jan 1973) to the observation store, with a one-time flagged backfill. Both are keyless. Baa−10y joins the spread family with 5-year and 20-year lenses and a Δ20 (20-observation change) derived form; EBP prints monthly in the Monthly's credit section as the slow read. The metric lenses' long window for the credit family switches to Baa−10y; HY and IG OAS keep their 5-year lens. The T&B harness config already names the Baa proxy for episodes before the stored HY history (`tb_episodes.yaml` 159–162); align its registry key to `fred.baa10y`.
- **106i.2 Honest window labels.** The credit dimension (`regime.py:349`, `config/market_state.yaml:152`, `window_days: 1826`) prints its window and the span actually available, e.g. "5y asked, 3.4y held". The compact metric-lens cell (`lens_cells.py:69`, used at `:149`) prints the held span whenever it is shorter than the asked window, e.g. "(3.4y/20y)"; the long form already prints n. Any other percentile printed with a window label follows the same rule (one helper, used everywhere).
- **106i.3 CSV guard.** `fred.pull` always merges (`fred.py:254-255`); the CSV writer refuses any write that would reduce a series' row count or move its first date later, unless called with an explicit `allow_shrink=True`, and logs the refusal. The observation store is unchanged (append-only already).
- **106i.4 Bank-stress calibration.** `tools/calibration/st_r6_59c_bank_stress.py:65` reads from the observation store instead of re-pulling FRED, uses `fred.baa10y` for dates before the stored HY history, and labels the proxy rows.
- **106i.5 Session labels.** `oneday_10y.one_day_changes` (`:68`) and `speed_attribution.attribute` (`:95`) keep counting FRED observations (the right convention for bond-market data) and say so in their printed names, e.g. "10y Δ3 sessions". The calendar-day windows in the T&B HY trigger (`tb_harness.py:233-247`) are already labelled and stay.
- **106i.6 Environments.** The shared `.venv` is left as it is (arch 8.0.0, statsmodels, scipy, patsy, formulaic, interface_meta, narwhals, wrapt 2.6.0.dev1); nothing is removed. Studies run from a `.venv-study` created in the study worktree from the next run (the Parts 8–9 paste creates it). A line in CLAUDE.md: study sessions install into `.venv-study` only.

**Rights.** Report labels and a new series; no composite or overlay change. The 1 Oct metric-lenses ruling (20-year spread percentiles) is amended by 106i.1.
**Hours.** ~3h for 106i.2–106i.5 and the CLAUDE.md line; ~2h for 106i.1. Tranche 0.

---

### 106a — Two-sided tail base rates (XX)

**Finding.** Part 2 and Part 4. Raw: after a bottom-decile day, a top-decile day follows within five sessions 62.8% of the time against 37.6% any day; 79.5% with VIX 20–30 the day before, 89.7% at 30–45, 95.7% above 45. Standardised by a GARCH(1,1) forecast fit without look-ahead: 49.7% against 41.9%; by 20-day realised vol: 51.6% against 41.3%. Clustering (share of top-decile days within ±5 sessions of a bottom-decile day): 72.6% raw against 65.1% shuffled; 60.3% standardised against 65.1%. Forward 20-session return after a bottom-decile day: +0.93% raw against +0.69% baseline; +0.11σ standardised against +0.15σ; next day −0.05%, 48% positive. 10th-percentile 20-session outcome −1.37σ against −1.23σ (GARCH), −1.60σ against −1.33σ (realised). Openers since 1990: 6 of 93 bottom-1% days; 5 Nov 2026 the only one at −4% or worse.

**Ruling (accepted; amended 5 Nov 23:13).** A two-sided tail table in Base Rates (XX): raw and standardised columns side by side, the standardised leading; the VIX-bucket rows; the opener set as rows of its own (count, dates, next-session and five-session outcomes); and one sentence stating that the co-location of best and worst days is a volatility phenomenon, not reversal. The table is the sizing input to 106g through the dispersion columns only. Refreshed yearly by the Annual Structural Review.
**Rights.** Base-rate rows. **Hours.** ~5h.

---

### 106b — Mechanical flow stack

**Ruling (accepted 5 Nov 22:06; unchanged).** Three estimators beside item 98's levered-ETF flow and the 6b dealer-hedging estimate: (i) vol-control exposure — a target-vol model (10–12% target, blended 1-month/3-month realised) giving an implied equity weight and a daily Δ-flow on an assumed AUM; (ii) a CTA trend proxy — multi-horizon moving-average signals on ES, NQ, RTY and the 10-year with flip levels in price terms; (iii) a risk-parity leverage proxy from stock-bond realised vol and correlation. One daily "forced flow" line in $bn with sign, printed at 15:00 and 16:45 with item 98, flip levels in the 07:00 anchor beside the dealer levels. Backtestable from price data; the vol-control estimator is built first because it is the flow that follows an opener (the study's own rule drops from 0.86 to 0.35 after 5 Nov; real funds spread the equivalent over one to three weeks).
**Rights.** Report line and flag; sizing input to 106g. **Hours.** ~15h.

---

### 106c — Two reads: vol state, and internal stress (tested first)

**Finding.** Part 1 medians: at T−1 the ten worst days had VIX 44.6, drawdown −13.6%, eight big-move days in the prior 20; the ten best 53.4, −24.2%, ten. At T−20 the worst days' median VIX was 15.4 with no big-move days, and 5 Nov 2026 kept that reading to T−1 (VIX 16.61, realised vol 12.9%, contango). Part 5.3: the 2026 internals were extreme (RSP−SPY 100th percentile, QQQ−SPY 2nd, sector dispersion 99th, Amihud 100th/72nd); the five earlier openers' internals ranged from the 8th to the 96th percentile, with SPY unusually liquid in three of them. The 20-opener gate in draft 2 would take over a century at one opener per six years.

**Ruling (accepted 5 Nov 22:06; amended 23:13).**
- **106c(i) Vol-state read.** Daily state from index vol, realised vol, term structure (VIX/VIX3M), VVIX and the big-move count, calibrated from 1990 as P(|return| ≥ 3% within 10 sessions | state decile), with transition base rates. Printed in the daily close. This is the sizing input to 106g(i) and (ii). ~7h.
- **106c(ii) Internal-stress read.** Built only if a pre-registered out-of-sample test passes. The test (Part 8 of the replay, issued 6 Nov): on every session from May 2003, fit expanding-window models refit each year-end (predictions 2008–2026 out of sample) of next-10-session realised vol, of a 2% day and of a −3% day, from the vol-state set alone and from the vol-state set plus the internal set (rotation speed and its percentile, QQQ−SPY, sector dispersion, Amihud 1y/3y, HB/LV 20-session change, the one-day HB/LV divergence). Pass criterion: on the subset with VIX below 20, the combined model beats vol-state alone on both the realised-vol R² and the 2%-day AUC, with block-bootstrap 90% intervals above zero. If it passes: build the read (rotation speed, sector gaps, dispersion, illiquidity from 106e, levered-ETF sensitivity from 98, cheap event vol from 101, HB/LV divergence from 100), print it beside the vol-state read with a flag for "surface calm, internals stressed", report-only, with a ledger on the opener set and the looser near-miss class; a sizing right only after the improvement holds at two Annual Structural Reviews. If it fails: the inputs still print where they already have homes (100, 101, 98, 106e) and the read is not built. ~3h for the test (study worktree), ~7h conditional.
**Rights.** c(i): daily line and sizing input. c(ii): report-only. **Hours.** ~7h + ~3h + ~7h conditional.

---

### 106d — Policy-put trigger panel

**Finding.** Every completed best day in the decade was a policy day or a known mechanical bid; in 2020 and 2025 the trigger was the Treasury and funding market, not equities (study §3.5). Part 7: Baa−10y had widened 50bp in 20 observations before 9 Mar 2020, 125bp by 16 Mar and 218bp by the day before the 24 Mar bounce; 16–30bp before 3–4 Apr 2025; 6bp before 5 Nov 2026 (level 152bp against a post-1990 median of 213bp and 90th percentile of 315bp). The October 2026 excess bond premium was −0.27. None of the credit triggers is near firing in this episode.

**Ruling (accepted 5 Nov 22:06; amended by draft 2 and §7 D-3).** One read in plumbing & rates with two parts. *Triggers*, all on rates of change: 10-year and 30-year 3-session changes; swap spreads; SR-36 basis stress; off-the-run spread; MOVE; FRA-OIS / SOFR-IORB; CP spreads; cross-currency basis; HY above 500bp with acceleration; IG primary-market shutdown days; and Baa−10y Δ20 as the long-history credit speed trigger (D-3). *Availability*: Fed stance from the Warsh scenario matrix (easing / hold / hiking), inflation room, whether the shock is the administration's own policy and therefore reversible, emergency-meeting odds from the prediction-market layer. Printed on any day 106c(i) is in its top quintile. A "policy-put unavailable" flag conditions 106a's base rates when it is set.
**Rights.** Report line and flag. **Hours.** ~8h.

---

### 106e — Illiquidity / price-impact proxy

**Finding.** SPY's Amihud ratio (20-session mean of |return| ÷ dollar volume) before 5 Nov sat at the 100th percentile of its trailing year and the 72nd of three years; 76th before 24 Feb 2020; 2nd–5th before the 2007, 2016 and 2018 openers. The one-year extreme partly reflects volume migrating away from SPY.

**Ruling (accepted 5 Nov 22:06 as "if missing"; promotion to a core input is §7 D-1).** Amihud on SPY and on ES (Massive's free futures tier or yfinance ES=F; a gap if neither is keyless), as one- and three-year percentiles with the three-year carried in the tape section; SPY quoted spread where Massive provides it. Feeds 106c(ii) and the daily close's tape line either way.
**Rights.** Tape line; input to c(ii). **Hours.** ~4h.

---

### 106f — Catalyst-class tags and seed rows

**Ruling (accepted 5 Nov 22:06; the two additions are §7 D-2).** Tag each tail day in the vol-event ledger (item 52) and the event-vol ledger (item 101): scheduled / unscheduled; class (policy shock, policy response, exogenous, data print, positioning unwind, earnings, political). Seed rows by hand: the twenty Morningstar days, 27 Feb 2020 (the S&P's ninth-worst), and the six openers. Item 101's realised window becomes T, T+1 and T+2, because the midterm information took two sessions to price (4 Nov +1.58%, 5 Nov −4.36%, against a one-day implied move of about 1.2%).
**Rights.** Ledger fields. **Hours.** ~1h by hand.

---

### 106g — Sizing

**Finding.** Part 6: buy-and-hold 8.59% a year, vol 17.97%, Sharpe 0.40 in excess of T-bills, max drawdown −56.8%, worst 20 sessions −30.9%. The vol-managed rule (12% target, 20-day realised vol, 0.25–1.5 bounds): 6.46–6.68%, 12.01%, 0.36–0.38, −32.7% to −36.5%, −11.0%, average exposure 0.90, turnover 9.5x. A constant mix at 0.90: 7.88–8.16%, 16.21%, 0.38–0.40, −52.7%, −28.2%. Exposure 0.25 on 18 of the 20 Morningstar dates (all in-regime) and 0.86 into 5 Nov 2026; the ten worst days summed −20.1% against −64.6%, the ten best +16.9% against +67.5%. Part 4: no directional edge after a bottom-decile day; wider outcomes only.

**Ruling (accepted 5 Nov 22:06; rewritten 23:13).**
- **106g(i) Book A.** Part 9 of the replay (issued 6 Nov) prices the rule and four variants (0.5 floor; VIX-based exposure (12/VIX)²; blended 20/60-session realised vol; 10% target), each against a constant mix at its own average exposure with cash and borrowing at T-bill rates and 2bp costs, as *premium* (return given up against the mix) and *recovery* (max drawdown avoided). The priced table goes to Doctrine #2 (7–8 Nov) as options for the Book A rule table; no live orders before 2027, so nothing is urgent.
- **106g(ii) DTH-1.** Constant-dollar-risk sizing: the stop is a multiple of ATR, contracts = fixed dollar risk ÷ stop distance; as volatility widens the contract count shrinks and stops sit outside the noise where algorithmic stop runs work. Replaces "halve size after a bottom-decile day", which the base rates do not support on drift. After a bottom-decile day, 106c(i)'s state sets the ATR multiple; nothing else changes.
**Rights.** Book A rule candidate; DTH-1 rule. **Hours.** ~1h (study) + ~6h.

---

### 106h — FlashAlpha Alpha-month replay

**Ruling (accepted 5 Nov 22:06; unchanged except the date list).** FlashAlpha's archive covers SPY from 3 Jan 2017 to the present (coverage endpoint, 5 Nov) but its replay endpoints (`/v1/exposure/summary`, `/v1/exposure/gex`, `/v1/volatility`) returned "requires Alpha" on Basic. The December one-month upgrade is Alpha, not Growth, and its first job is the replay of the twenty Morningstar dates plus 27 Feb 2020 and the 2017-onward openers (10 Oct 2018, 24 Feb 2020, 5 Nov 2026), ±5 sessions each: exposure summary, GEX by strike, surface, 0DTE share, written to `docs/studies/tail-days-dealer-replay.md`. Reminders exist for 16 and 30 Nov.
**Rights.** Study. **Hours.** ~3h in December.

---

## 4. Cross-item notes

- **106i before everything.** Two labels are wrong in live reports today; Tranche 0 runs as the next build paste after PR #50 (chain-11) merges, on a branch off the merged main, so `fred.py` and `regime.py` edits do not collide.
- **106i and the 1 Oct metric-lenses ruling.** The 20-year spread window now means Baa−10y; HY and IG OAS lenses are 5-year with honest spans. The T&B HY Spread Acceleration overlay already handles unstored episodes with the Baa proxy and is unchanged.
- **106a, 106c(i) and 106g form one chain:** base rates → vol state → size. 106c(ii) and 106e are the optional second chain, gated by the test.
- **106b extends item 98**; the "forced flow" line replaces 98's "mechanical close flow" line once 106b lands (98's line prints alone until then).
- **106d uses SR-36, the 10y speed flag, MOVE–VIX, the funding overlay and the new Baa−10y Δ20**; it composes, it does not recompute.
- **106f touches items 52 and 101**; the T+2 window changes 101's ledger schema before 101 is built, so it is zero-cost if filed first.
- **Rotation speed** (equal-weight over cap-weight in 20 sessions, the clearest 2026 tell) belongs to 106c(ii), not to item 103, whose SPY/RSP chart was showing the same thing.
- **Items 92–97 and 98–105** are in the batch file; this order's §6 tranches slot behind that batch's Tranche A except for Tranche 0.

---

## 5. Verify items

| ID | Check | Due |
|---|---|---|
| V-106a | VIX close on 5 Nov 2026 and the Part 2.3 row applying to the week of 6 Nov | 07:00 anchor, 6 Nov |
| V-106b | Part 8 result: does 106c(ii) pass its pre-registered test | After the Parts 8–9 run |
| V-106c | ES volume without a key (Massive free futures tier or yfinance ES=F) | At 106e build |
| V-106d | FlashAlpha tier matrix: Alpha unlocks the three replay endpoints | Before the December purchase (16 Nov reminder) |
| V-106e | The EBP CSV is reachable from the VPS (it was from the laptop) | At 106i.1 build |
| V-106f | T&B `timeseries.db` holds no HY series older than May 2023 (nothing depends on it; for the record) | At 106i build |
| V-106g | The VPS has weasyprint; the laptop environment does not and never did | At 106i build |
| V-106h | Catalyst labels for the five earlier openers (study §1, from memory) | At 106f seed |
| V-106i | 2018-02-05 and 2024-08-05 fall in the looser near-miss class (Part 8) | After the Parts 8–9 run |

---

## 6. Work order and placement

| Work | Sub-item | Tranche | Sessions | By hand |
|---|---|---|---|---|
| i.2 window-span labels; i.3 CSV guard; i.4 bank-stress reads the store; i.5 session labels; i.6 CLAUDE.md line | 106i | 0 | ~3h | — |
| i.1 `fred.baa10y`, `fed.ebp`, `fed.gz_spread` into the store with backfill, lenses and Δ20; credit long window switched | 106i | 0 | ~2h | — |
| Two-sided tail table in XX | 106a | 1 | ~5h | — |
| Vol-state read | 106c(i) | 1 | ~7h | — |
| DTH-1 constant-dollar-risk sizing | 106g(ii) | 1 | ~6h | — |
| Parts 8–9 of the replay (c(ii) test; g(i) pricing), study worktree | 106c(ii), 106g(i) | 1 | ~4h | — |
| Catalyst tags and seed rows; 101's T+2 window | 106f | 1 | — | ~1h |
| Illiquidity proxy | 106e | 2 | ~4h | — |
| Mechanical flow stack | 106b | 2 | ~15h | — |
| Policy-put panel | 106d | 2 | ~8h | — |
| Internal-stress read (only if Part 8 passes) | 106c(ii) | 3 | ~7h | — |
| FlashAlpha Alpha replay | 106h | Dec | ~3h | — |
| **Total** | | | **~54h (+7h conditional) + 3h Dec** | **~1h** |

**Tranche 0 (~5h):** the next build paste after PR #50 merges. **Tranche 1 (~22h + 1h by hand):** behind the batch-17 Tranche A evidence clocks; 106g(i)'s priced table is needed for Doctrine #2 on 7–8 Nov, so the Parts 8–9 run goes today. **Tranche 2 (~27h):** after Category 1. **Tranche 3:** only on a pass. Audit #5 (week of 23 Nov) confirms placement.

**Build spec for Tranche 0** (for the workplan chat to issue as the next A or B paste; file and line references from the FRED check at 07ebeb6c):
1. One helper that formats a window label as "asked" plus "held" whenever held is shorter: used by `regime.py:349` (credit dimension; read `window_days` from `config/market_state.yaml:152`) and by `lens_cells.py:69`/`:149` (compact cell). Add a gate test that fails if any percentile prints a window label without the helper.
2. `fred.py:254-255`: `merge=True` on every path; the CSV writer refuses to shorten a series (row count or first date) unless `allow_shrink=True`, logging the refusal. Gate test with a synthetic shorter pull.
3. `tools/calibration/st_r6_59c_bank_stress.py:65`: read the observation store; `fred.baa10y` before the stored HY history; proxy rows labelled.
4. `oneday_10y.py:68` and `speed_attribution.py:95`: printed names say "sessions"; no computation change.
5. Registry entries and a flagged one-time backfill for `fred.baa10y` (FRED BAA10Y), `fed.ebp` and `fed.gz_spread` (FEDS Notes CSV); spread-family lenses 5y/20y on Baa−10y, Δ20 derived form; HY/IG lenses stay 5y; `tb_episodes.yaml` proxy key aligned.
6. CLAUDE.md: study sessions install into `.venv-study` only.
7. Run `scripts/make.sh validate`; branch-only; no merge.

---

## 7. Decisions at filing

- **D-1, 106e promoted to a core input** (draft 2's amendment, not yet ruled): Amihud on SPY and ES, the three-year percentile carried, SPY quoted spread where available. Recommend accept.
- **D-2, 106f additions** (draft 2's amendment, not yet ruled): seed rows add 27 Feb 2020 and the six openers; item 101's realised window becomes T, T+1, T+2. Recommend accept; the schema change is free if filed before 101 is built.
- **D-3, Baa−10y Δ20 as 106d's long-history credit trigger.** Calibratable from 1986; preceded 2020 and 2025 and is quiet now. Recommend accept.
- **D-4, the 106c(ii) pass criterion** as pre-registered in §3 (VIX-below-20 subset; realised-vol R² and 2%-day AUC both improved with 90% intervals above zero). Recommend accept; it is deliberately modest, and a looser near-miss opener class is reported beside it.

Register numbers: SR numbers for 106's new entries (a, b, c(i), d, e; c(ii) if built) are assigned at filing after items 92–105, in the order listed.

---

## 8. Register, voices and sources

**Voices.** Morningstar (research publisher; the prompting table). Morgan Stanley QDS (sell-side derivatives desk; the levered-ETF and midterm-vol figures). None new to the register.

**Narrative register.** "Don't miss the best days" (the Morningstar framing) is logged as a popular narrative with the study's rebuttal: the best days are inseparable from the worst, and missing both is the documented drawdown trade-off.

**Sources.**
- `docs/studies/tail-days-study-2026-11-05.md` (draft 3), `docs/studies/tail-days-2016-2026-data.md` (04fd571f, 07ebeb6c), `docs/studies/fred-env-check-2026-11-05.md` (98a12839), branch `study/tail-days`.
- VPS observation-store query, 6 Nov 2026 11:43 UTC (read-only; results in the study §8).
- Morningstar Direct, "Volatility Cuts Both Ways", Morningstar US Market Index, Nov 2016–Nov 2026 (screenshot in chat).
- Morgan Stanley Derivatives, 5 Nov 2026: https://x.com/MgnStnlyDerivs/status/2118418288992493963 ; 3 Nov 2026 midterm implied-vs-realised chart (screenshot in chat).
- FlashAlpha coverage and tier responses pulled 5 Nov 2026 via the MCP connector.
- Literature (memory): a 2017 study of volatility-managed portfolios, and a 2020 study re-testing it across markets.

---

## 9. Merge note for the study branch

`study/tail-days` carries five commits (28db006f draft 1, 04fd571f Parts 1–3, 73227981 draft 2, 07ebeb6c Parts 4–7, 98a12839 the FRED check) plus draft 3 and Parts 8–9 when run. It touches only `docs/studies/` and `tools/studies/`. Merge in any window on the operator's word; nothing on main depends on it, and Tranche 0 does not wait for it.

---

## 10. Sign-off

The rulings given in chat constitute the signature.
- **106a–h as drafted (draft 1):** "accept", 5 Nov 2026, 22:06 ET.
- **Draft-2 amendments to 106a, 106c, 106g, and the new 106i:** "accept rulings", 5 Nov 2026, 23:13 ET.
- **106i's six fixes (labels, CSV guard, bank-stress calibration, session labels, environments, placement as Tranche 0) and the credit long-window switch to Baa−10y:** "accept the decisions", 6 Nov 2026, 07:20 ET.
- **D-1 to D-4 (§7):** pending.

Filed: [commit hash] on [date].