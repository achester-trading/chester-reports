# GEX / DEX definitions against FlashAlpha — 9 Oct 2026 SPY, per-strike (read-only diagnostic)

*Run 2026-10-09 09:34–09:36 ET from the decision chat through FlashAlpha's MCP
connector (Basic plan, endpoint version 2026.09.30, six of the day's 250 requests),
against a local copy of the box's stored chain `data/chains/2026-10-08/SPY_202138Z.csv`
(settled capture, 16:21 ET 8 Oct, spot 773.97). The box did not call FlashAlpha and
never will: the connector is chat-side, for audits. Nothing was written to any
store. Dated; never edited. Supersedes the definition finding of
`gex-scale-flashalpha-2026-09-30.md`; that ledger's pipeline findings stand.*

**The question.** The 30 Sep ledger could compare only two headline numbers six
hours apart, and concluded from FlashAlpha's concepts page that their GEX is
Σ sign·Γ·OI·100·S (this repo's `net_gex`) while ours is per 1% (`dollar_gamma_per_1pct`),
and that their DEX window was undetermined. The connector returns **strike-by-strike**
GEX and DEX for one expiry, with their open interest beside each strike, so the
definition can be read off the numbers instead of the documentation.

## Verdict

- **GEX: FlashAlpha's per-strike GEX is Σ sign·Γ·OI·100·S²·0.01 — dollars per 1% move,
  this repo's `dollar_gamma_per_1pct`, under the same dealer-hand signing (calls +,
  puts −).** Recomputing each strike of the 16 Oct expiry with FlashAlpha's own OI,
  their spot (776.65) and our 8 Oct close IV gives a ratio FlashAlpha ÷ ours of
  **1.01 median** across the 760–800 strikes (0.99–1.07; wider only where the
  overnight IV move dominates a far strike). Against `net_gex` the ratio is 7.8 ≈
  0.01 × S, which is the per-1% factor and nothing else. The 30 Sep reading is
  withdrawn: **the cross-check compares their GEX with `dollar_gamma_per_1pct`.**
- **DEX: FlashAlpha's DEX is Σ Δ·OI·100·S with raw option deltas — calls positive,
  puts negative, no dealer flip.** A deep-ITM 300 call with 43 OI prints
  3,334,830 = 0.9986 × 43 × 100 × 776.65; every put prints negative. Ours is
  dealer-hand (short puts carry +delta), so **ours = Σ(call_dex − put_dex)** in their
  columns. Re-pricing our full 8 Oct chain at their morning spot under raw signing
  gives **$66.7bn against their $65.96bn** (1%). The window was never the issue;
  the signing was. "Definition unreconciled" comes off DEX.
- **Levels agree where the method is the same.** Flip 774.55 (theirs, 09:36) against
  775.46 (ours, 8 Oct close): 0.1%. Max pain 765 = 765. Their put wall 774 is our
  `put_wall_gamma` 775 within a strike; their call wall 780 against our 790 is wall
  selection among three near-equal candidates (780/785/790 each carried ~$150–200M at
  the close), not a definition difference.
- **Headline GEX does not agree, and cannot at six-hours-and-a-day apart.** Their
  full-chain +$7.34bn/1% at 09:36 against our 8 Oct chain re-priced at 776.50:
  +$0.66bn/1%. The profile is at its steepest here (zero crossing 775.46; −1% of spot takes
  net gamma to −$16bn/1%, +1% to +$19bn/1%), their OI feed is one vintage fresher than our
  16:21 chain (`oi_feed 2026-10-08T20:00Z`; e.g. 795 calls 38,398 against 24,348,
  765 puts 30,167 against 21,934), and today's 0DTE is alive in theirs. The
  single-expiry test shows the definition and the maths agree to 5% on the same
  inputs (+$0.541bn against +$0.570bn for 16 Oct); the headline gap is inputs and
  time. **Level agreement needs a same-minute pair with the same OI vintage** — the
  box's capture and a connector pull at the same clock minute.
- **CHEX looks like shares per day** (theirs −2.78M, ours −3.50M at the close; same
  sign, 25% apart on day-old inputs) — provisional, untested per strike. **VEX is
  unreconciled**: theirs −$160.4bn, ours +$7.45bn per vol point; sign and scale both
  differ, so their unit is not per vol point and may be customer-hand. A per-strike
  `get_vex` test on one expiry settles it next time at one request.

## The per-strike test (16 Oct expiry, their OI, their spot 776.65, our 8 Oct IV, T = 7/365)

| Strike | Right | IV (8 Oct) | OI (FA) | OI (yf, 8 Oct) | Ours Σ sign·Γ·OI·100·S, $M | FA GEX, $M | FA ÷ ours | FA ÷ (ours·0.01·S) |
|---|---|---|---|---|---|---|---|---|
| 760 | C | 0.149 | 10,128 | 10,099 | 10.7 | 75.8 | 7.09 | 0.913 |
| 760 | P | 0.120 | 24,185 | 24,619 | −23.0 | −189.8 | 8.25 | 1.062 |
| 765 | C | 0.134 | 7,787 | 7,738 | 11.5 | 90.6 | 7.89 | 1.015 |
| 765 | P | 0.111 | 30,167 | 21,934 | −45.4 | −349.4 | 7.70 | 0.991 |
| 770 | C | 0.121 | 19,911 | 19,384 | 40.2 | 332.5 | 8.27 | 1.065 |
| 770 | P | 0.102 | 22,525 | 20,426 | −50.7 | −363.8 | 7.18 | 0.924 |
| 775 | C | 0.111 | 23,112 | 21,996 | 58.9 | 486.9 | 8.27 | 1.065 |
| 775 | P | 0.093 | 8,689 | 9,812 | −26.1 | −174.4 | 6.67 | 0.859 |
| 780 | C | 0.102 | 20,909 | 18,924 | 57.2 | 461.8 | 8.08 | 1.040 |
| 780 | P | 0.085 | 6,928 | 7,520 | −22.5 | −143.7 | 6.38 | 0.822 |
| 785 | C | 0.097 | 44,310 | 40,737 | 101.0 | 795.5 | 7.88 | 1.014 |
| 785 | P | 0.073 | 7,031 | 7,358 | −17.3 | −119.9 | 6.93 | 0.892 |
| 790 | C | 0.094 | 28,870 | 29,684 | 41.0 | 320.0 | 7.81 | 1.005 |
| 795 | C | 0.093 | 38,398 | 24,348 | 26.1 | 208.4 | 8.00 | 1.029 |
| 800 | C | 0.096 | 27,578 | 27,597 | 8.1 | 67.5 | 8.33 | 1.072 |

Median of the last column over 755–800, both rights: **1.01** (mean 0.97). The
scatter is the IV we did not have: theirs is live 9 Oct, ours is the 8 Oct close,
and gamma at 7 DTE moves with it. Twenty strikes were tested; the table shows the
near-money half.

## Totals

| Quantity | Ours, 8 Oct chain | FlashAlpha, 9 Oct 09:36 ET | Note |
|---|---|---|---|
| GEX, 16 Oct expiry only, $/1% at 776.65 | +0.541bn | +0.570bn | same inputs but IV and OI vintage; 5% |
| GEX, full chain, $/1% — settled at 773.97 | −3.464bn | — | what the box printed |
| GEX, full chain, $/1% — re-priced at 776.50, 9 Oct expiry excluded | +0.659bn | +7.34bn | inputs and time; see verdict |
| DEX, 16 Oct expiry, raw signing | +8.51bn | +5.87bn | near-money deltas on day-old inputs |
| DEX, full chain, raw signing — re-priced at 776.50 | +66.7bn | +65.96bn | **1%** — definition settled |
| DEX, full chain, dealer-hand (ours) — settled | +209.9bn | — | = Σ(call_dex − put_dex) in their columns |
| Gamma flip | 775.46 (close) | 774.55–774.59 | 0.1% |
| Call wall / put wall | 790 / 767 (OTM); 775 (gamma) | 780 / 774 | selection, not definition |
| Max pain | 765 | 765 | agree |
| CHEX | −3.50M shares/day | −2,779,107 (unit unstated) | provisional: shares/day |
| VEX | +7.45bn per vol point | −160.4bn (unit unstated) | unreconciled |

Also returned, unused here: their macro block (VIX 15.07, VIX9D/3M/6M 12.21/18.08/20.04,
MOVE 99.1, SKEW 149.2, Fear & Greed 38) and ATM IV 10.26 against HV20 10.16.

## What follows (operator's ruling, not done here)

- **No change to any stored figure.** Ours were already per 1%; the 30 Sep ledger
  said not to change them and this one agrees for the opposite reason.
- **Rewire the cross-check line**: compare FlashAlpha's GEX with
  `dollar_gamma_per_1pct`, their DEX with a raw-signed Σ Δ·OI·100·S that
  `exposure_compute` does not print today (one line to add; `gex_scale_diagnostic.py`
  already prints the row as "raw net Σ Δ·OI"), and drop "definition unreconciled"
  from DEX. VEX keeps the flag until its per-strike test.
- **Make the audit same-minute.** On the chosen weekday the operator sends the word
  at the box's capture minute; the chat pulls `get_stock_summary`, `get_levels` and
  one single-expiry `get_gex` (three requests) and reconciles that evening against the
  stored chain. With 6b's 09:45 capture that pairing also shares the OI vintage.
- The 30 Sep comparison is reopened under this definition: FlashAlpha's −$1.0bn at
  10:01 against our −$6.0bn at 16:14 with 0DTE alive was a timing gap on a steep
  profile day, and cannot be settled from that pair.
