# Doctrine monthly — October 2026 — minutes

Sitting held in chat from Fri 2 Oct 2026 14:52 ET, one item at a time, from `docs/briefs/doctrine-monthly-2026-10-agenda.md`. Each ruling is Ari's; the record here is what a session applies. Config changes (`config/risk_limits.yaml` and any other `proposed:` value) are applied by the D-1 session under Ari's own line, transcribing this file; the session changes no value this file does not name.

## Item 0 — Enterprise Layer rulings R-4…R-8 — **signed** (14:52 ET, "sign all")

Applied to `docs/change-order-enterprise-layer-2026-09-27.md` the same minute. The §8 work order stays for Audit #4 (14–15 Oct).

## Item 1 — the regime mapping — **ruled** (14:55 ET, "I accept these")

- **1a. Mapping ratified with one change:** `disinflationary_slowdown` maps to **Tightening**, not Contraction (same 20–40% band; Tightening's book rules — duration sleeve on, short side open — fit a slowdown with falling inflation; Contraction's are written for a recession). The other eight entries stand: expansion, goldilocks → Expansion; late_cycle, overheating → Overheat; stagflation → Tightening; contraction, deflationary_bust → Contraction; mixed → Transition. `regime_mapping.proposed` becomes `false`; version `dial-to-doctrine-v1` becomes `v1.1` with the one change.
- **1b. Crossing rule ratified:** a dial state that changed within the last **10 sessions** maps to Transition (the Doctrine's two-week rule in session units). `transition_sessions: 10` stands, no longer proposed.
- **1c. At once.** The Transition stance applies from the session the dial changes (the Doctrine's rule; Transition is itself the protection against a false change). Dimensions keep their own two-session rule. **Re-engagement** into the new regime's band is a ruling Ari takes at a sitting on or after the 10th session; for the 1 Oct change (expansion → overheating) that is **Audit #4, 14–15 Oct** — added to its agenda. Until then Book A stays in Transition: 60–70%, hedged, cross-book net-beta cap 85%. If the dial reverts first, nothing to rule.

## Item 2 — risk limits (`config/risk_limits.yaml`) — **ruled** (14:57 ET, "I accept your recommendation")

- **2a.** `net_beta_over_band_top_pct: 15` confirmed (the Doctrine's sentence; 95% Expansion, 85% Transition now, 75% Overheat, 55% Contraction).
- **2b.** `sector_max_pct` **25 → 30**, `proposed: false`. Reason recorded: the limit looks through index holdings; Book A at the top of the Expansion band (80% SPY) carries ≈ 27% of capital in tech and would breach 25% with no single name held; at 30% the index at full band passes and Books B/C cannot add tech on top of a full Book A.
- **2c.** `vega_max_pct_per_vol_pt: 0.5` ratified, `proposed: false` (a ten-point vol spike costs 5% of capital, inside the 7% monthly kill switch).
- **2d.** `duration_max_pct_per_100bp: 5` ratified, `proposed: false` (admits the Doctrine's largest duration sleeve, 30% of capital in a duration-16 fund ≈ $14,400 per 100 bp, and nothing beyond).
- **2e.** `config/instrument_reference.yaml` ratified as **approximate, refreshed at each Quarterly Structural from the issuers' published holdings**; the as-of date prints beside any limit that uses it. Its `proposed` flag becomes `false`; a `refresh: quarterly_structural` note and `as_of` field are added.
- The file's own note ("the operator ratifies by setting proposed: false — by hand, not by a session") is amended by this ruling to: *by hand, or by a session transcribing a ruling recorded in the Doctrine-monthly minutes under Ari's own line; the session changes no value the minutes do not name.*

## Item 3 — the change ladder (Enterprise Layer §3.4a) — **ratified** (14:59 ET, "Ratified as you recommend")

- The five tiers stand as written in §3.4(a) of the change order (tactical learning / regime adaptation / relationship change / structural change / durable principle, with their evidence, authority and review cadence).
- **3a.** Tier 2's N = **20** graded outcomes within the regime, the unconditional base rate printed beside the conditional (Base Rates convention).
- **3b.** "One tier per review cadence" means the cadence of the tier being *entered*: tier 3 only after a quarter at tier 2; tier 4 only after a year at tier 3. Every change filed from now carries its tier and the date it entered, in the change order that makes it.
- Nothing already in the Doctrine moves; the ladder governs changes from here. The September signal-triage items are tier-3 proposals and keep their calibration-study route.
- Applied by the EL-4 library session (2–3 h) as a Doctrine section; the Doctrine's dated appendix records this ruling.

## Item 4 — the attention budget (§3.4b) — **ruled** (15:00 ET, "Accept, though I can do 7 packets instead of 5")

- **Seven** packet approvals a week (Ari raised the proposed five); **one review sitting a week of at most two hours** (the Doctrine monthly and Audit sittings count as their weeks' sittings).
- **4a.** A packet the budget defers is recorded on the register as an **abstention with reason `attention_budget`** and graded like any other abstention (R-4), so the budget's cost is measured.
- **4b.** The Weekly prints three counts: packets approved / 7; sitting hours / 2; and **session rulings taken in chat that week** — the third measured, not capped, until Doctrine #2 sets a cap from a month's data.
- Applied by EL-4 (Doctrine section) and by the Weekly build (T2) for the printed counts; the register gains the `attention_budget` abstention reason.

## Item 5 — the intraday rung (§3.4c) — **confirmed** (15:03 ET, "Confirmed")

- The 27 Sep ruling recorded in the Doctrine: Books A–D stand; intraday is a tactics layer for Books B and C (execution timing for decisions those books already approved) plus at most two paper engines; no fifth book. Each engine, before its first trade: a one-paragraph mechanism; the setup's unconditional base rate beside the claimed edge; a target N; the fixed kill criterion (*retired when, after N ≥ 40 graded paper trades, expectancy after modeled costs is ≤ 0 or its Brier is worse than the base rate's; never resized before N*).
- **First engine after 6b: dealer-positioning / 0DTE regimes** (the Dealer's Hand, Part V), on three conditions written into its registration: (1) its base rate is computed from the stored close verdicts over at least 20 sessions before its first paper trade; (2) defined-risk structures only (spreads, never naked), as Book C's tactics layer requires; (3) its trades are **ledger entries graded against stored bars — never orders and never packets**: they carry an `engine_id`, do not count against the attention budget, and Ari reviews the engine, not its trades, at the weekly sitting.
- **Second: the scheduled-event engine** (releases, earnings), after an offline surprise-reaction study queued beside 6e.
- Applied by EL-4 (Doctrine section) and EL-12 (engine registration, after 6b).

## Item 6 — the metric lenses (`docs/briefs/metric-lenses-brief-2026-10-01.md`) — **ratified** (15:05 ET, "ratify all five as stated")

- **6a.** Correction flag at **−10%** and bear flag at **−20%** from the 52-week high.
- **6b.** Credit-widening flag per series: **HY, BB, CCC at +100 bp in three months; IG at +40 bp**. The Top & Bottom's HY-acceleration overlay keeps its own calibrated trigger; the two are documented as different purposes (display label vs turn detector).
- **6c.** Long windows as proposed (spreads and conditions 20y; rates full history; inflation full history; labour and activity 20y; 12-month-return percentile full history; ratios 20y; quantities none), plus a **per-series `long_window` override with a stated reason**: valuation ratios (CAPE, ERP, forward P/E) → full history; TIPS real yields → full history from 2003, n printed.
- **6d.** The **30-point** disagreement flag between `pctile_5y` and `pctile_long`.
- **6e.** Family assignments: unemployment rate → release (labour) with a level percentile added to its forms; breakevens and the ACM term premium → rate; DXY, gold, oil, BTC, sector ETFs → price; VIX → conditions; 2s10s and breadth → ratio (20y); CAPE, ERP, forward P/E → ratio with the full-history override.
- All *proposed* markers in the lenses brief become ratified at these values; applied in the 6e build (registry `family`, `long_window`, per-series flags).

## Item 7 — the Monthly — **ruled** (15:10 ET, "before 6b, and no inbox as new source")

- **7a.** No further content changes to Monthly v2 Phase A before the 23 Oct dry run; T3 adds the stack order, the dealer retrospective, the long-frame charts and Slow layers. Ari rules on trims against the forty-minute target at the 23 Oct dry run, confirmed by a second on 28 Oct.
- **7b. Phase B, the voices register, in full (~10 h), before 6b** — placed in the week of 19 Oct beside T3's second half, so the 1 Nov Monthly prints real voices (all NEW; status computation first works on 1 Dec). Sources: the public commentary pages and RSS of the major desks, Reuters and CNBC strategist quotes, Fed speeches from the speaker-calendar feed; paywalled outlets stay out. **No inbox/newsletter source.** "No stored source, not printed" from day one. 6b and the feed purchase move one week later, to the first week of November. Workplan v3 amended to match.

## Item 8 — lessons from the first fortnight (Doctrine dated appendix, October 2026 entry) — **ruled** (15:11 ET, "stand as written"; no operator's note)

Three entries, to be written into the appendix by the EL-4 library session, no figures:

- **INC-6 — a foreign listing is a currency position.** *A decision's expression must be in its thesis's currency; otherwise the FX leg is a second decision and is recorded as one. The gate refuses a mismatch at entry (built 2 Oct), and `expression_currency` is a required field on every packet.*
- **INC-7 — an exit the system didn't see.** *Every exit is a register event the same session it happens, including one made by hand at the broker; a divergence between broker state and the register is a heartbeat fault, not a Weekly footnote.*
- **The first graded decisions.** *Decisions entered before the enforcement gate existed are graded like any other, with `gate_outcome = pre-gate`; from now, a packet without a time stop and an invalidation level at entry is a rule break. The short side's extra confirmation stands as written.*

## Item 9 — order of work — **confirmed** (15:12 ET, "order confirmed"; Ari intends to run more session hours a day over the next few weeks and finish sooner)

T1 → D-1 → 6d + rate path → T2 → T3 (first half) → freeze → Audit #4 (14–15 Oct) → cloud migration → T3 (second half) + Phase B voices → dry runs 23 and 28 Oct → freeze 29 Oct → 1 Nov Monthly → 6b → dealer engine registered → 6e with the lenses → 6f → Quarterly Structural + 6i → 6m Thailand → Enterprise Layer Tranche A → signal-triage Tranche 1 → library track. Doctrine #2 on 7–8 Nov. **The order is fixed; the calendar is not** — at a faster pace the dates in Workplan v3 pull forward in the same order, with two anchors that do not move: Audit #4 on 14–15 Oct and the Monthly on 1 Nov. If a week runs short, 6b slips, never those two.

## Item 10 — the reporting stack's values (`docs/briefs/reporting-stack-brief-2026-10-02.md`) — **ratified** (15:14 ET, "ratify as stated")

- **Plumbing & rates "deep" trigger (daily):** a tier-1 release this session or next (FOMC decision or minutes, CPI, PCE, payrolls, GDP, the refunding announcement, a 10- or 30-year auction); or in the session 10-year or 30-year ≥ ±10 bp, 2s10s ≥ ±8 bp, HY OAS ≥ ±15 bp.
- **What's priced "deep" trigger (daily and Weekly):** 5- or 10-year breakeven ≥ 10 bp; implied rate for any of the next four FOMC meetings ≥ 12.5 bp; a watched prediction market ≥ 10 points; S&P consensus EPS revision ≥ 1% (Weekly only); UMich or SCE one-year expectations ≥ 0.3 pt.
- **Reading budgets:** daily ≤ 1,000 words / 3 charts; Weekly ≤ 3,500 / 6; Monthly ≤ 7,000 / 10; a firing trigger raises that report's chart cap by one; over budget → lowest-priority lines dropped, "(trimmed)" printed.
- **Long-frame averages (Monthly tape):** 40-week, 10-month, 20-month — levels, never signals; a cross counts only after the monthly close.
- **Prediction-market watch list:** the FOMC decision at each of the next four meetings; US recession in 2026 and in 2027; each month's CPI print; House and Senate control on 3 Nov; a government shutdown by date; plus the twenty highest-volume markets matching the narrative register's stories by keyword.
- **Disagreement thresholds:** venue vs fed-funds-implied ≥ 15 points on the same meeting; venue vs our scenario weight ≥ 20 points.
- The Weekly prints each trigger's firing count; Doctrine #2 recalibrates any that fired more than weekly or not at all in October. All values live in config; the brief's *proposed* markers become ratified.

---

## Sitting closed 15:14 ET — 22 minutes, ten items and item 0, all ruled

**Applied in chat:** item 0 (change order marked signed). **To apply by session:** D-1 (config: regime mapping v1.1, `transition_sessions`, risk limits incl. sector 30%, instrument reference as approximate with quarterly refresh; the stack's values as ratified in `config/`), EL-4 (Doctrine sections: change ladder with N = 20 and the cadence clause, attention budget 7 / 2 h / three counts, intraday rung, the October appendix entries), T2 (Weekly prints the attention counts and trigger counts), EL-12 (dealer engine registration, after 6b), 6e (lenses values). **Added to the Audit #4 agenda:** re-engagement of Book A into the Overheat band (item 1c).

## Post-sitting notes

- 4 Oct — Weekly chart cap raised (W7 intraday, W8 panel, W9 gauges, W10 priced); reading budgets count prose only.
