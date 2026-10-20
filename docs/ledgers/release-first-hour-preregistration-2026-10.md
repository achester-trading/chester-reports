# The release-day first hour — pre-registration (October 2026)

*Written and committed on 19 Oct 2026, before any of its scoring code, by session A on branch `a49-secondary-notes`. **Never edited.** A change is a new registration in a new dated file. The spec is the secondary-notes order (`docs/change-order-secondary-notes-2026-10-19.md`), section 4.1 and decision D4, ruled 19 Oct 2026, 14:14 ET.*

## The question

On a day with a tier-1 or tier-2 08:30 release, does the move from just before 08:30 to the first hour's end continue or fade over the rest of the session? This is report-only: it grants nothing and builds no composite.

## The days and the instruments

- **The days:** each session on which `config/release_calendar.yaml` schedules a tier-1 (CPI, PCE, payrolls, GDP, the refunding) or tier-2 (PPI, retail sales, jobless claims) release at 08:30 ET.
  - The first edition reads the release dates from FRED's public release calendar (`fred/releases/dates`) for the same releases, where the store's calendar is not on the laptop.
  - A day with releases of both tiers counts once, under its highest tier.
- **The instruments:** ES (`ES=F`) and the 10-year Treasury yield (`^TNX`, in basis points). Each is scored apart.

## The measure

- **The first move (m1):** the move from the last bar before 08:30 to the end of the first hour.
- **The rest (m2):** the move from the end of the first hour to the 16:00 close.
- **Continues:** m1 and m2 have the same sign and m1 is not zero.
- **Fades:** m1 and m2 have opposite signs.
- **A day with m1 of zero, or a bar missing at either end,** is not scored and is counted as such.

**Two samples, read apart and never pooled:**
1. **The first edition: Yahoo's hourly bars,** labelled with their bar size. Yahoo's hourly history reaches about two years.
   - "The last bar before 08:30" is the 07:00–08:00 bar's close.
   - "The end of the first hour" is the 09:00–10:00 bar's close.
   - "The 16:00 close" is the 15:00–16:00 bar's close.

   So the first edition reads **08:00 to 10:00 against 10:00 to 16:00**, and says so.
2. **The open note's own readings.** The note stores, per release day, the 5-minute move from the last bar before 08:30 to the last before 09:45 (key `calc.release_first_hour`, instruments ES and the 10-year). The close's 16:00 close completes m2: from 09:45 to 16:00.

## The splits

- By release type: CPI, PCE, payrolls, GDP, the refunding, PPI, retail sales and jobless claims.
- By the sign of the naive surprise (`calc.surprise_vs_naive`), where the store holds it. The first edition, run from public sources, carries no naive surprise. It prints that split as "not computed (the naive expectation is the store's)", and the box edition adds it.

## The pass rule

- **A cell** is a release type and an instrument, in one sample.
- **A cell passes** when its continuation share's Wilson 95% interval excludes 50%, with **20 scored days at least**, after a **Benjamini–Hochberg** control at **q = 0.10** across every cell of that sample with 20 days or more.
- **The sample's verdict:**
  - **PASS** when one cell or more passes;
  - **INSUFFICIENT** when no cell reaches 20 days;
  - **FAIL** otherwise.

The share, its interval and n print for every cell, a passing one or not.

## The rights

**None.** A PASS is reported. It reaches the register only as a rule-31 draft, and it grants no reading, flag, dial or decision. The open note's reaction block prints the market's moves, never this ledger's verdict, unless Ari rules otherwise on the evidence.
