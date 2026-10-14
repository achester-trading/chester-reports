# AQ-14: the emerging-markets paper — notes (11 Oct 2026)

Branch `lib-aq14-em-paper`, from `origin/library` at `751dbe9`. Not merged. Commissioned by
`docs/change-order-alternative-assets-quarterly-2026-10-10.md` (on main) §4.5, decision 8, work
order AQ-14.

**What was filed.**

- `docs/whitepapers/emerging-markets-whitepaper.md`: *Emerging Markets: A Structural Framework*,
  Draft 1, numeral **XXXIV (provisional)**. It has eight parts, twenty-five numbered sections,
  Tier 1–4 tables, **eight falsification tests (T1–T8)**, a Cadence Summary and Appendices A–D.
  It has no figures. `wc -w` counts 17,676 words; the library gate's whitespace count runs about
  1.5% higher.
- `docs/html/emerging-markets-whitepaper.html`: the built edition, from `bash scripts/make.sh html`.
  No other edition changed.
- `docs/white-paper-library-guide.md`: four additions, all marked Draft 1 and provisional.
  - The reading-order row and the at-a-glance row, both in Structural asset classes after IX.
  - The dependency row.
  - The one-page entry, `## XXXIV (provisional).`
  - The header's counts: twenty-seven papers, ~419,000 words. The gate measured 419,575.
- `tools/check_library.py`: **one registry line**, `"XXXIV": "emerging-markets"`. This is the only
  non-doc change. Check 1 fails a guide numeral that the registry does not carry. XXXIII was filed
  the same way in `751dbe9`. See Needs you 2.
- `make library-check`: 27 papers, 0 failures, 0 warnings.

Nothing under `altdata/`, `daily_cascade/` or `config/` was touched.

## What the paper claims and where each claim comes from

| Claim | Source |
|---|---|
| EM in aggregate is "a dollar-cycle instrument with a commodity overlay … a poor vehicle for a country view and a reasonable vehicle for a dollar view" | International Equities paper, Ch 12. Quoted verbatim in Purpose |
| "Dollar moves tend to lead EM equity and credit performance by weeks"; "long EM equity, long commodities, and short dollars has one position, not three" | Monthly manual, Ch 7 (Predictive Properties; How Institutions Use It). Quoted |
| Contagion runs through funding channels, not trade; the basis "is the one that would fire first in a disorderly version" | The Twenty-Five, Scenario 15 (Precedent; Tripwire). Quoted. **The commissioning text's "the basis fires first" is S15's narrower "would fire first in a disorderly version"; the paper quotes S15** |
| The EM loop | Currencies paper §3. Quoted |
| The dollar channel's four sentences; the basis as "the cleanest real-time indicator"; TIC's custodial attribution problem | Monthly manual, Ch 7 (The 101; Metrics; Failure Modes). Quoted |
| Twenty-four countries, 1,165 constituents; weights Taiwan 28.9 / Korea 21.4 / China 19.8 / India 10.7 / Brazil 4.1 / other 15.1; IT 43.8%; TSMC 15.63%; top ten 39.0%; capitalisation $12.3tn; P/E 14.9 against 21.4 (ACWI); forward P/E 9.7 against 16.3 | MSCI EM Index factsheet (USD, gross), 30 Sep 2026, fetched 11 Oct 2026 |
| Returns: 10.47% a year since Dec 1987 against 9.02% (World) and 8.89% (ACWI); 10-year 9.53 against 12.92; YTD 23.73 against 13.37; 2025 34.36 against 22.87; maximum drawdown 65.14% | Same factsheet |
| Every completed relative turn (1988, 1994, 2001, 2010) came within about a year of a dollar turn; 2016–18 a false start; relative line at a 25-year low with an uptick | SR-14 ruling (signal-triage order, 24 Sep 2026). Quoted |
| 2012–2025: the dollar and EM-minus-ACWI had opposite signs in 11 of 14 years, correlation −0.54; the exceptions were 2016, 2019 and 2023 | **Computed in this session** from FRED `DTWEXBGS` year-ends and the factsheet's calendar returns (n = 14) |
| Broad dollar 121.4 (2 Oct 2026), peak 130.0 (13 Jan 2025), low 117.4 (29 Jan 2026), ~90th percentile since 2006; EM dollar index 129.7; EM corporate OAS 1.58 and EM HY 3.34 (8 Oct 2026); USD/CNY 6.70 against 7.12 a year earlier | FRED `DTWEXBGS`, `DTWEXEMEGS`, `BAMLEMCBPIOAS`, `BAMLEMHBHYCRPIOAS`, `DEXCHUS`, pulled 11 Oct 2026 |
| The leadership-run table's drivers | The standard account, labelled approximate in the paper |
| Three instruments, three exposures; original sin and "original sin redux" | Mechanism; Eichengreen–Hausmann (1999) and later work, named but not quoted |
| The S15 corporate-borrower mutation; the non-dollar-channel mutation | The Twenty-Five, Scenario 15. Quoted |
| Oil–dollar sign rule ("maximum pain for energy-importing EM") | Alternative Assets change order §4.3. Quoted |
| Copper-to-gold "nets the growth signal against the debasement signal" | The Twenty-Five, Scenario 12. Quoted |
| Fed temporary swap lines, March 2020 (incl. Brazil, Korea, Mexico, Singapore); the FIMA facility | Public record. Mechanism, not quantified |
| The three-IMF-programmes rule | The Twenty-Five, Scenario 15. Quoted. **The counting convention in §13 is this paper's proposal** (Needs you 1) |
| The 2022–23 programme wave (Sri Lanka, Zambia, Ghana, Pakistan, Egypt) | Public record; pointer only |
| SR-46 parts (b) and (d): the five-session contagion rule, "the 1995 peso / 1998 Russia sequence" | Signal-triage batch 4 (6 Oct 2026). Quoted |
| No composite; the scorecard's design, its lenses, keys and targets; the not-tracked reasons | Architecture §26.8; change order §4.5; `config/em_scorecard.yaml` on `aq-9a-em-scorecard` |
| Brazil: external debt 37.5% of GDP, real policy rate +9.8, government debt 93.3%. Malaysia: reserves 0.83× short-term debt | AQ-9a notes, from its trial run of 11 Oct 2026 |
| What each lens has and has not predicted | The early-warning literature, named and dated in the text: Kaminsky–Lizondo–Reinhart (1998), Rodrik–Velasco (1999), Greenspan–Guidotti (1999), Frankel–Rose (1996), Eichengreen–Gupta (2014). **These are cited from the literature as known to the author; this session re-read none of the papers** |
| China: three markets; the trap; capacity discipline; the 10.7 ten-year set | International Equities paper, Ch 10. By reference and quoted, not rewritten |
| The devaluation tell; CNH HIBOR at 66% in January 2016; CGB below 2% as the Japanification gauge | SR-4 ruling. Quoted |
| The three-channel China event, its first movers and its aliasing with S15 | The Twenty-Five, Scenario 12. Quoted |
| The policy ladder; authoritative sources against commentary; the LGFV and financial-stability map; the operator's political note | Change order §4.5 and decision 4. Quoted |
| TSF and the credit impulse are not built (PBOC robots.txt; NBS; data.stats.gov.cn 403) | AQ-3 part 2 notes, 11 Oct 2026 |
| Tier tables: every registry key | Read in this session from `metrics_registry.yaml`, `altdata/config.py` and `yfinance_source.py` on main, `aq-3-series-1`, `aq-3-series-2`, `aq-9a-em-scorecard` and `c1-move-screen` |
| The EM central estimate (~7–9.5% a year) and the U.S. and developed-international estimates | International Equities paper, 15.2 (inferred, September 2026) |
| The twelve-month set, the ten-year set and their probabilities | **The author's construction, 11 Oct 2026.** Labelled as such in the paper |

## What is deliberately left to XXVI

The reserved Markets paper *Turning Points, Bubbles, and Crises* (XXVI, Audit 2's roster) carries
EM currency–banking–sovereign crises as narratives. This paper names them only as pointers, where a
mechanism needs an instance, and narrates none:

- **1994–95 Mexico.** Named as the end of the first EM run, the SR-46 contagion precedent, and a
  current-account case.
- **1997–98 Asia and Russia.** Named as S15's full-sequence precedent, the reserves-to-short-term-debt
  evidence, and the crisis the fiscal lenses missed.
- **2001 Argentina.** Named as the external-debt case.
- **2015 China.** Named as the devaluation-tell precedent and the 2015–16 overlay year.
- **2018 Turkey and Argentina.** Named as S15's contained version and the real-rate and
  current-account cases.

Also left to XXVI: crisis anatomy and its sequencing narrative, the sovereign–bank loop, and any
crisis-by-crisis data. §14 states the order of operations as mechanism and gives no episode
timelines.

## Choices made for the operator to overrule

1. **The frame is quoted, not restated.** Purpose opens with the four sentences and their sections,
   and the rest of the paper elaborates or tests them. Where the change order paraphrased a source,
   the paper follows the source:
   - S15's "would fire first in a disorderly version";
   - Portfolio Construction's actual baht sentences, not the change order's "permanent EM-FX
     position counted before any discretionary FX", which is not in that paper.
2. **The "second overlay."** §4 and §8 argue that, on 30 Sep 2026 composition, the aggregate has a
   semiconductor overlay as well as a commodity one. **T7 tests it**, and §24's scenario set gives it
   two rows (North Asia reversal; Narrow or range). This is the paper's one substantive addition to
   the commissioned frame.
3. **Eight lenses, not seven.** The scorecard splits debt into external and government. The paper
   follows the scorecard.
4. **The §13 IMF counting convention.**
   - Counted: new financing arrangements, emergency RFI/RCF included.
   - Not counted: reviews, augmentations, PCI/PSI, stand-alone RSF, and precautionary
     FCL/PLL/SLL.
   - The quarter is the calendar quarter of Board approval.
5. **Scenario resolution is first-match, in the listed order:** China event → Dollar squeeze → North
   Asia reversal → Broad EM cycle → Narrow or range.
   - The broad basket is the equal-weighted EWZ, EWW, EZA, INDA, THD, TUR and EIDO, which are
     `c1-move-screen` keys.
   - EM against the World uses `manual.msci_em_usd` ÷ `manual.msci_world_usd`, the by-hand
     monthly series on main.
6. **Probabilities.**
   - Twelve-month set (1 Oct 2026 – 30 Sep 2027): China 8, squeeze 20, North Asia 12, broad cycle
     25, narrow/range 35.
   - Ten-year set: dollar-down decade 25, convergence 30, dollar strength 30, North Asia rupture 15.
     P(EM beats the World) is 50–55%.
7. **Registry keys on `c1-move-screen`** (the EM OAS rows and the screen) are named with their branch
   even though the brief listed main, AQ-3 and AQ-9a only. The Quarterly's chapter already hooks
   them, so naming them is more useful than printing *not stored*.
8. **The tests use thresholds:** 20%/8% turns (T1), 0.3 (T3), 50 bp / 1% (T4), 15%/40%/half (T5),
   tercile and 8% (T6), four quarters (T7), and 3%/1% (T8). They are reasoned, not calibrated, and
   each is a single number to change.
9. **The audits' closing chapters are not included.** Audit 2's Tactical Applications, Wiring and
   Environments chapters are absent, because the four structural papers this one copies do not carry
   them yet. The Cadence Summary does the wiring.
10. **No figures.** The relative line laid over the broad dollar would be the obvious first one. It
    needs a data pull and a drawing pass, which a docs-only session should not invent.

## Gaps found on the way (no action taken, for the build sessions)

**Data limits.**

- **FRED's ICE BofA EM spreads return three years of history** (from Oct 2023). The percentile window
  of `fred.em_corp_oas` and `fred.em_hy_oas` will be short. T2's spread leg cannot be tested until
  three years are stored.
- **`DTWEXEMEGS` (the EM dollar index) is not in the registry.** It is free, daily, from 2006, and one
  SeriesSpec would add it.
- **No free cross-currency basis, IIF flows, TSF, China PPI or capacity data.** The paper says so in
  place.

**Configuration.**

- **The scorecard's configured country order is stale** against the 30 Sep 2026 factsheet. Korea is
  now second and China third. Whether the twelve-largest tail still holds (the UAE, Malaysia,
  Indonesia, Poland) could not be checked: the factsheet names only the top five.

## Needs you

1. Ratify §13's counting convention for "three IMF programmes in a quarter" (new financing
   arrangements including RFI/RCF; excluding reviews, augmentations, PCI/PSI, stand-alone RSF and
   precautionary lines)? **yes / no**
2. Accept the one-line registry entry in `tools/check_library.py` as within "docs only"? Without it
   the library gate fails the roster row, and XXXIII was filed the same way. **yes / no**
3. Adopt §24's first-match resolution criteria, including the seven-ETF broad basket, as the ledger
   resolution for the first `alt_asset` EM entry at Doctrine #2? **yes / no**
4. Commission a one-line follow-up (code session) to add FRED `DTWEXEMEGS` to the registry and to
   re-order `config/em_scorecard.yaml`'s countries to the 30 Sep 2026 weights? **yes / no**
5. Keep the "second overlay" (semiconductors) and test T7 in the paper's frame, rather than leaving
   the commissioned frame unamended? **yes / no**
