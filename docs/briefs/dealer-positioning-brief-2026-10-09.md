# Dealer positioning — the tables, the charts, the commentary and the scorecard (brief, 9 Oct 2026)

| | |
|---|---|
| Status | Drafted 9 Oct 2026 from the operator's ask ("deep awareness of dealer positioning, how it might affect the strategy, and whether the market does in fact respond as positioning implies") and an outside four-table recommendation he supplied. Placed by Audit #4 under Part V (the "dealer charts as a tool" row expands into this brief); builds inside **6b** as the dealer block, with the scorecard extension beside EL-12's engine registration. |
| Owner | Ari Chester |
| Source of every figure | The engine's exposure output (`tools/exposure_compute.py`, convention `dealers-hand-v1`): one exposure JSON per capture per symbol, with `overall`, `buckets`, `per_strike`, `expiration_release`, `max_pain`, `gates`. **Every table and chart below is a view of that one dataset; nothing recomputes.** The outside note's own first principle — one canonical exposure dataset, the tables as views — is already how the engine is built. |
| Captures | Today: 16:10 settled (0DTE excluded by rule). With 6b: 09:45 and 12:30 as well, and the engine's 5–15-minute SPY recompute between them; an intraday capture includes the day's 0DTE. |
| Charts | `tools/dealer_charts.py` (this commit): the four figures of 9 Oct, drawn from an exposure JSON and its chain. `daily_cascade/charts.py` imports its `draw_*` functions when the block lands. |
| Hours | ≈ 17 h in 6b: tables and synthesis 6, charts wired 2, scorecard extension 6, Weekly/Monthly wiring 3. |

## 1. What the block answers, in order

1. **Which regime, how far from the flip, and how steep** — the sign is not the story when spot is 0.2% from the zero-gamma level; the profile's slope is.
2. **Where the hedging concentrates** — walls, max pain, the secondary strikes, and which expiry carries them.
3. **What rolls off and when** — the expiration-release schedule and the DEX horizon.
4. **Whether the horizons agree** — 0DTE against the week against everything.
5. **What changed since the equivalent capture** — settled against settled, 09:45 against 09:45; never a settled read against an intraday one.
6. **Whether the market did what positioning implied** — the scorecard, with the base rate beside every hit rate.

## 2. The tables (views; horizons by days to expiry)

The engine buckets by listing type (0DTE, weekly ≤ 7 days, monthly third-Fridays, quarterly, other). The outside note's four horizons are **windows by days to expiry**, which read better on a page and avoid the "other" bucket's 29% of |GEX| sitting under an opaque label. The tables therefore print **0DTE · ≤ 7 days · ≤ 45 days · all**, each a roll-up of the engine's buckets by DTE (a `horizon_windows` list in `config/reporting_stack.yaml`; the engine's buckets stay as stored). At a settled capture the 0DTE column prints "settled — excluded", never a number.

**T1 — Dashboard** (every capture; the close, and each intraday slot after 6b). Rows: net GEX ($ per 1%), regime, zero-gamma level and its distance from spot, call wall, put wall (OTM and gamma), net DEX (dealer-hand, with the raw-signed figure in a footnote for the FlashAlpha cross-check), spot's distance to each level. Columns: the four horizons. Every qualitative word sits beside its number. Below the table, three sentences (§4).

**T2 — Key levels** (the close and the Weekly; one table per horizon at the Weekly, the all-expiries table at the close). Rows: call wall, secondary call concentration, zero-gamma, spot, secondary put concentration, put wall, max pain. Columns: strike, GEX at the strike, DEX at the strike, distance from spot, rank (share of the horizon's |GEX|), and a conditional reading ("potential pin / resistance", "acceleration zone below", "regime transition") — conditional words only, the Doctrine's and the Dealer's Hand's, never "support" or "resistance" as facts.

**T3 — Horizon agreement** (the close, as three lines, not a table; the Weekly as a table). Per horizon: gamma sign and magnitude (low / medium / high against the series' own five-year percentile), delta bias, nearest major level, expected behaviour (reversion / expansion / unclear). Then the synthesis line from a fixed rule set, each rule printed with its own hit rate and base rate from the scorecard (§5) — "0DTE negative, aggregate positive: intraday amplification inside a stabilising week (n = 14, 9 amplified; base rate 0.38)". A rule with fewer than 20 scored sessions prints "untested (n = …)".

**T4 — Changes since the equivalent capture** (every capture). Rows: all-expiry GEX, ≤ 7-day GEX, 0DTE GEX (intraday only), zero-gamma, call wall, put wall, all-expiry DEX, largest |GEX| strike. Columns: now, the equivalent prior capture, change, and one clause ("pivot moved up 1.9 points", "overhead concentration migrated 780 → 785"). The comparison key is the capture slot: 16:10 against the prior session's 16:10; 09:45 against the prior 09:45. A missing prior capture prints "no equivalent capture", never a comparison against a different slot.

**The decision summary** (the close and the 09:45 slot; the Doctrine's form, not the outside note's "buy dip / sell rip"): intraday regime; broader regime; upside reference; downside reference; **the setups whose conditions hold** from `config/setups.yaml` (`c_pin_fade` in positive gamma near a pin candidate; `c_negative_gamma_continuation` after confirmation through a level; `d_forced_flow` on an expiry-pin or release day), each with the level, the invalidation and the time stop the setup requires; and "no setup" when none holds. The books decide; the block proposes. The Book B scanner (Audit #4 item II.3) reads these conditions; nothing here writes the register.

## 3. The charts

| Figure | Where it prints | Why |
|---|---|---|
| 2 — gamma profile across spot | the close (its one dealer chart), the Weekly, the Monthly | Carries the regime, the distance to the flip and the asymmetry in one picture; the sign alone misleads near the flip |
| 1 — GEX by strike with the levels | the Weekly, the Monthly; the 09:45 slot after 6b | Where the gamma sits and in which hand |
| 3 — buckets and the expiration-release schedule | the Weekly, the Monthly | What rolls off this week and next, and the week's dealer flow from expiries |
| 4 — DEX by horizon | the Monthly | The hedge book's tenor; slow-moving, monthly is enough |
| 5 — the scorecard chart (new, with §5) | the Weekly, the Monthly | Hit rate against base rate per rule, last 20 and last 60 sessions, with n |

The close's budget is three charts; the profile takes one. The Weekly's cap of ten takes figures 1–3 and 5; the Monthly's all five. Each figure is stamped with the capture time and "settled" or "intraday".

## 4. The commentary

Fixed shape, model-written through the section writer, behind the numeral and flag-word audits, every capture:

1. **Regime and distance.** "Negative gamma, $3.5bn per 1%, with the zero-gamma level 0.2% above spot: a regime on a knife-edge. One percent lower and the book is $16bn short gamma; one percent higher, $19bn long."
2. **Where the hedging is.** Walls, max pain, the strikes that matter and their expiry; what releases at the next expiry and in which direction.
3. **What it implies, conditionally, and what would change it.** The setups whose conditions hold (or none), with the level that invalidates the read — the flip crossing, the wall breaking, the expiry passing. Written in the Doctrine's conditional language; a sentence may say "pinned", "held" or "amplified" about a past session only where the scorecard's flag says so (the existing flag-word audit).

At the Weekly, a fourth paragraph: how the week went against the Monday read (from the scorecard rows), and the base-rate line.

## 5. The scorecard — does the market do what positioning implies?

The close already stores one `dealer.scorecard_day` row per session with three flags (pinned, held, amplified) and an IV check, scored by the Weekly's rule; the Monthly's Mechanics prints their counts as hit rates once 20 sessions are scored. This brief extends that, it does not replace it:

- **A base rate beside every hit rate** (the Base Rates convention): pinned against the unconditional share of closes within `pinned_pct` of max pain; held against the share of all wall touches that closed inside; amplified against the share of all sessions whose range exceeded the implied range by the ratio. A hit rate without its base rate is not printed.
- **Split by regime**: every rate reported for positive-gamma and negative-gamma sessions separately, because the hypothesis is conditional.
- **Two more flags**: *dampened* (positive gamma; the realised range below the implied range by the mirror ratio — the half of the claim the scorecard does not yet test) and *expanded* (negative gamma with the profile steeper than its 60-session median; the next session's range in the top tercile of the trailing 60). Both scored from the stored captures and the pin log, never from the live store.
- **The rule set in T3** is graded the same way: each synthesis rule is a named flag with its hit rate, base rate and n, so a rule that does not beat its base rate after 40 sessions is retired by the Doctrine's own kill criterion, not by argument.
- **Horizons**: last 20 and last 60 sessions at the Weekly; the month and the trailing three months at the Monthly's retrospective.
- **The vendor line**: the Wednesday FlashAlpha reconciliation's verdicts (ledger of 9 Oct) print once a week in the Weekly's Mechanics, so a definition drift is seen the week it happens.

This scorecard is also the base rate the first paper engine needs before its first paper trade (Doctrine item 5: ≥ 20 sessions of stored close verdicts), so the engine's registration (EL-12) reads it rather than building its own.

## 6. What is deliberately not built

Strike-level charts for every expiry (the per-strike figure at one horizon is enough; the rest is in T2); a "market direction" cell (direction comes from the full framework, as the outside note itself says); directional readings from DEX alone (DEX says how much hedge rolls off and when, not which way the market goes); any order, alert or setup written to the register by this block (the scanner and the books do that); comparisons across SPY, QQQ and IWM in raw dollars (normalised per 1% of each underlying's notional, and labelled).

## 7. Build order inside 6b

1. `horizon_windows` roll-up and T1/T4 at the close (2 h) → 2. T2 and the decision summary (2 h) → 3. charts wired through `daily_cascade/charts.py` from `tools/dealer_charts.py` (2 h) → 4. the scorecard extension: base rates, regime split, the two flags, the rule flags (6 h) → 5. T3 and the synthesis with its rates (2 h) → 6. Weekly and Monthly wiring, figure 5, the vendor line (3 h). Validators extend `validate_weekly_complete.py` and `validate_monthly_stack.py`; the flag-word audit covers the new words.
