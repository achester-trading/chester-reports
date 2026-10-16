# Dated-appendix entries awaiting their paper

*Judgment drafts that a change order assigns to a paper's dated appendix, notes
the order names by a paper's numeral, and by-hand layouts, committed as drafted
under ruling (c) of 16 October 2026 ("judgment drafts (narrative lines, appendix
notes, rule-table edits) are committed by the session as drafted and listed for
Ari's accept-all"). An entry moves into its paper's dated appendix when that
paper is written or next revised, and is then struck from here. Entries are
added, never rewritten; a correction is a new line under the entry.*

## For XXVII, Debt Cycles, Regimes, and Environments (reserved; not yet written)

### Base-rate note: the long-bond cycle chart (Batch 5 item 18)

> *Dated 9 Oct 2026.* arvy (Thierry, Macro Cycles; a product pitch) charts 200
> years of long-bond yields as 56-, 59- and 67-year secular legs, with 2020 as
> the turn and an oscillator run out to 2060. The leg lengths are fitted to the
> chart, and the 2060 line is a forecast; we keep it here as a dated picture of
> the long cycle, not a measure. The testable claim, that dispersion is back,
> is measured in Mechanics' dispersion panel (Cboe DSPX and COR1M/COR3M).

## The dated appendix line for the stock-bond flag (Batch 5 item 24)

The order says "dated appendix" without naming a paper; XXVII, which carries the
regimes, is the likely home, and Ari's accept-all decides.

> The 10-year Treasury yield (FRED DGS10) closed at or above 5.25% in the week of
> 5 Oct 2026 — 5.31% on 5 Oct, 5.27% on 6 Oct and 5.28% on 7 Oct — after first
> closing above it at 5.26% on 29 Sep 2026; the last close at or above 5.25% before
> that was 5.26% on 12 Jun 2007. Verified from FRED, not from the chart.

*Verify item 5, answered 16 Oct 2026 from FRED's DGS10 (fredgraph.csv, read by
session B). The draft said "the first time since 2002"; FRED says June 2007, and
the cross came the week before 5 Oct, so the line carries the verified dates.*

## For XII, as the order names it (Batch 5 item 23)

The order calls it "XII's power-buildout narrative"; the library's XII is the
Daily Cascade paper, so the numeral is the order's and the home is Ari's to name
(the power-buildout thesis is argued in Foundations' Factor I chapter).

### Disagreement note: power construction against data centers

> Census VIP, August 2026 (preliminary, SAAR): total power construction +8.5%
> nominal year over year, against data centers +73.2% (the poster's real figures:
> +4.1% and +64.5%). Power is growing at a fraction of the data-center pace, which
> cuts against XII's power-buildout thesis. Logged as a disagreement, not
> resolved.

### Base-rate note: manufacturing construction

> Manufacturing's fall is mostly the CHIPS and IRA fab boom rolling off, a base
> effect, which is why the level against 2019 prints beside the year over year.

## The sovereign fragility scorecard (Batch 5 item 21): its layout

Under Factor IV in the Monthly's slow layers, quarterly, from the IMF Fiscal
Monitor and the OECD. **Not live:** it is a recurring by-hand data line, and
ruling (b) of 16 Oct 2026 says none survives without Ari's explicit yes. The
layout, as drafted:

| Country | GFN / GDP | Interest / revenue | Weighted average maturity | Foreign-held share | Primary balance / GDP | Source and vintage |
|---|---|---|---|---|---|---|
| US | | | | | | |
| DE | | | | | | |
| FR | | | | | | |
| IT | | | | | | |
| GR | | | | | | |
| JP | | | | | | |
| UK | | | | | | |

## For the Book A rule table: A-6 (Batch 5 item 24)

The table's home is a dated Appendix C, "The Book A rule table (dated;
candidates)", in Base Rates (the 25 Sep order's section 2.4 has Base Rates hold
it until Portfolio Construction does). Session A builds that appendix on
`st-r5-fixes` with A-1 to A-3 and its A-4 and A-5, and asked that this branch
number from A-6, so this entry moves there at the stitch rather than opening a
second table.

| Rule | Condition | Action | Source items | Gate |
|---|---|---|---|---|
| A-6 Duration hedge status under the stock-bond flag | The stock-bond flag live (SR-9, amended by Batch 5 item 24: the 60-day correlation beside the two-year window, its strength conditioned on the 10-year attribution) | Treasury duration loses hedge status; replacement diversifiers per the item-25 map: T-bills, gold, commodities, trend-following, defined-outcome option structures. Strong (breakeven-led): full substitution. Moderate: partial. Weak (real-yield- or term-premium-led, inflation anchored): duration kept, sized down | SR-9; Batch 5 items 24 and 25 | as A-1's: SR-9 regression (backlog) or driver calibration (ST-3) |

As drafted (the draft called it "A-1, amended"; it is A-1's hedge substitution
made specific to the flag, so it keeps A-1's gate):

> While the stock-bond flag is live, Treasury duration loses hedge status.
> Replacement diversifiers per the item-25 map: T-bills, gold, commodities,
> trend-following, defined-outcome option structures. Strength strong
> (breakeven-led): full substitution. Moderate: partial. Weak (real-yield- or
> term-premium-led, inflation anchored): duration kept, sized down. The flag's
> threshold and strength rules are config/batch5_tranche_1.yaml's.

The flag is computed by `altdata/batch5.py` and printed in Mechanics; nothing in
the code acts on the rule table.

## For the narrative register's pairs: "what's driving 5.3%" (Batch 5 item 26)

The register has no pair kind and so no confirm step for one. Session A opens
`docs/narrative-register-pairs.md` on `st-r5-fixes` under this pair's id,
`what_driving_5_3`, and adds item 35's bear-side addition there. This section
moves into that file at the stitch (not created here, to avoid an add/add
conflict). Side B is also committed as a pending register proposal,
`capital_competition` in config/narratives.yaml, since side A is the seeded
`fiscal_dominance`. As drafted:

> `id: what_driving_5_3; kind: disagreement; side_a: fiscal -- the term premium
> is the long end pricing debt (Kovač, TAAI; Hartnett, BofA); side_b: capital
> competition -- private demand for capital repricing the expected path and r*
> (Boivin, BlackRock Investment Institute; Rai); adjudicator: the fiscal-bark
> flag on the 10-year attribution, monthly -- side A when the term premium
> carried at least half of the six-month rise, side B when the expected short
> rate did; review: monthly.`
