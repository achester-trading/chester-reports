# AQ-2 part 2 — the other eight chapters: build notes (11 Oct 2026)

Branch `aq-2-chapters-2`, built on `aq-2-chapters-1` (d3855fd). Not merged. It
follows the change order
`docs/change-order-alternative-assets-quarterly-2026-10-10.md`: §4.1 (the
template), §4.5–§4.11, §5, §6, §8 and §10A. It uses part 1's machinery
(`docs/briefs/aq-2-chapters-notes.md`).

## What was built

- **All eleven chapters are filled.** `config/quarterly_chapters.yaml` adds EM,
  China, crypto, real estate, credit, international equities, Thailand and
  agriculture. Each chapter declares:
  - the five lines;
  - its structure series, each a registry key or `absent: <reason>`;
  - two structure charts;
  - the implied-range fund;
  - the analyses, with their hooks and kill conditions;
  - the falsification tests and the ten questions, in the paper's own words;
  - the permitted and banned words;
  - a figure budget per written item.
- **Where no paper owns a chapter, no test or question is invented.** This
  covers EM, China, real estate, Thailand and agriculture. Items 7 and 11 print
  "no owning paper — not stated".
- **Tests and questions that come from a paper:**

  | Paper | Tests | Ten questions |
  |---|---|---|
  | Digital Assets (IX) | 7 | Appendix D |
  | Credit (VI) | 7 | Appendix D |
  | International Equities (XXI) | 4, from §15.7 (the paper has no "Falsification Tests" section) | none (the paper has no Appendix D) |

  The gate checks every statement verbatim against the paper file. It also
  checks the one related test, real estate's Credit §21 line, which is printed
  as another paper's words and not graded.
- **New machinery in `monthly_macro/quarterly_items.py`:**
  - **Computed rows from two registered keys:**
    - `diff`: BB–CCC, the mortgage spread, UST–CGB;
    - `share`: China's gold share of reserves;
    - `ratio_pct`: the CNY fixing gap against the ±2% band;
    - `rel_return`: the ten-year US-minus-international gap, and REITs, utilities and small caps against SPY;
    - `corr`: the three-year US–international correlation with XXI 14.2's bands, BTC against SPY and QQQ, and BTC against net liquidity.
  - **New falsification rule kinds:** `change_above`, `drawdown_at_least`, `correlation_in_band` and `unmeasured`. With `unmeasured`, a test whose other leg did not occur still reads "holds".
  - **New sub-sections:**
    - item 0, the frame;
    - item 2a, the scenario sets, each printed with the paper's prior; this quarter's weight is AQ-6's;
    - the chapter's own **panels**, each placed after a named template item.
  - **Panel kinds:**

    | Kind | What it is |
    |---|---|
    | `series` | rows of series |
    | `matrix` | a table whose cells are named but not stored |
    | `hook` | another branch's block, by module and branch |
    | `calendar` | a hand-seeded calendar |
    | `lines` | lines of text |
    | `political` | China's quote-only sub-section |
    | `light_tier` | the crypto light tier |
    | `return_decomp` | GTM-19's decomposition |
    | `coins` | the coin page |
- **The template now governs what renders** (`quarterly.build_filled`). Light
  chapters print items 1–4, 7, 8 and 10. Thailand prints everything but 11.
  Before this, part 1's builder printed every item for every filled chapter.
- **Hooks to other branches.** Each is imported only at run time and prints
  "not yet: <branch>" until that branch is merged:

  | What | Branch | Where it prints |
  |---|---|---|
  | `altdata.em_scorecard.quarterly_block` | `aq-9a-em-scorecard` | EM 4d |
  | `altdata.move_screen.quarter_episodes` | `c1-move-screen` | EM 4e, the SR-46 episode list |
  | `imf.ifs.gold_reserves_oz.chn` | `imf-ifs-gold` | China item 4; read once the registry holds the key |
  | `altdata.correlation.breaks_between` | `aq-5-correlation-layer` | the EM and China break logic |
  | AQ-4, AQ-5, AQ-6, AQ-8a | their branches | as in part 1 |
- **EM:**
  - The frame prints "frame: Emerging Markets — A Structural Framework, Draft 1,
    not yet filed", with §4.5's frame paragraph as the interim and its citations.
  - The twelve-month set is "not yet — the EM paper supplies it".
  - The structure rows:
    - stored: SR-14's MSCI legs, EEM, EMXC and MXN;
    - absent, by name: the ICE BofA EM spreads, the EM FX basket and dollar index, IIF flows, the basis.
  - S15's three-IMF-programmes rule, in the paper's words.
- **China:**
  - **Structure:**
    - CNY, the fixing, and the fixing gap against the band (CNH absent);
    - the CGB and the UST–CGB spread;
    - SAFE's reserves and BoP;
    - gold in ounces, and its share of reserves;
    - the IFS cross-check hook.
  - **Panels:**
    - 4d: XXI 10.6's observables (TSF, capacity discipline, property, shareholder return, participation, deflation), all absent with reasons;
    - 4e: reserve behaviour (TIC holdings, SAFE gold, state-bank dollar selling; grain and crude are a named gap);
    - 4f: the S8 Taiwan ladder.
  - The ten-year set is XXI 10.7's, 20/40/25/15.
  - **The political sub-section is quote-only (9a/9b):**
    - the four rules;
    - the hand-seeded calendar `config/china_political_calendar.yaml` (a template, no entries);
    - the operator's note, quoted;
    - the stored reporting, quoted and classed as an authoritative release or commentary by outlet;
    - the policy ladder and the Article IV read, absent with reasons.
  - The quote-only rule is enforced three ways:
    - it is a banned-behaviour rule in China's frames;
    - the political sub-sections carry no prose frame;
    - the executive summary never receives them (`quarterly.summary_view`).
- **Crypto:**
  - **The coin page.** Five deep-tier pages (BTC, ETH, SOL, ZEC, PRL), each with
    §4.6's twelve fields in one fixed order. Each field reads one of:
    - a stored series;
    - `cases_and_positioning.py`;
    - the chapter's tests;
    - or, failing those, it prints its not-yet reason.

    The last field is a source and vintage log of the series the page read.
  - **The light tier.** HYPE, TAO, LINK and AAVE carry
    `light_tier_pending_promotion: true` and print "pending MW-6 promotion".
  - **The other tables:**
    - the category gauges;
    - the stablecoin plumbing table (USDT, USDC, DAI/USDS, USDe × five columns);
    - the deck items (developer activity is a named gap);
    - the scanning sub-chapter, with MW-7 verbatim and the scan-only names.
  - **The analyses:**
    - BTC against M2 (computed);
    - the rotation and effective float (AQ-8);
    - the IBIT two-bid (AQ-8a);
    - Factor V's four questions;
    - stablecoins against bills, with its kill condition.
  - **Scenarios:** 45/30/25 and 20/35/30/15.
- **Real estate, credit and international equities, on the light template:**
  - **Real estate:**
    - stored: REITs and the rate-sensitive ratios against SPY, mortgage rates and the mortgage spread;
    - absent, by name: CMBS, extension/foreclosure, CPPI, real house prices;
    - the CRE families, 55/30/15.
  - **Credit:**
    - the Tier 1 set, with BB–CCC computed and the paid series named;
    - the twelve-month four and §38's three;
    - two tests computed.
  - **International equities:**
    - the ten-year US gap;
    - the three-year correlation in the paper's bands;
    - GTM-19's decomposition from ETF proxies: price and dividends, with currency, multiple, earnings and local named as lacking;
    - Japan's reform set and the fragmentation spread, absent;
    - 15.4's four.
- **Thailand (country chapter, isolated):**
  - The market block's own rows carry `namespace: thailand`, and all of them are
    absent (DEXTHUS, BoT, CPI and the rest). The dollar, CNY and JPY are read as
    shared rows.
  - `config/thailand_political_calendar.yaml` is a template.
  - The scan structure, with the Thai source hierarchy.
  - The scenario map, printed with no probabilities.
  - The book prints "No draft, by rule". The frame states the isolation.
  - The personal-finance core is not built and not in the repo. The spec was
    read for its isolation rules only.
- **Agriculture (light):**
  - The WASDE rows wait for AQ-3's writer, by name.
  - Also present: the crop stage, ENSO (as context), trade events, the nitrogen
    complex, and curve and positioning.
  - Sugar, coffee, cocoa and cotton are one table.
  - The four scenarios print with "not stated" priors.
  - The book line: "thin or poorly understood contracts" are a no draft by rule.
- **Gate:** `tools/validate_quarterly_stack.py` group G now covers all eleven
  chapters: 91 checks, up from 65. Group C's shell check now builds a shell
  from an empty configuration, since no chapter is left unfilled. Part 2's
  checks cover:
  - the template per weight;
  - every series is registered or absent with its reason;
  - the tests and questions are verbatim where a paper exists, and "no owning paper" where none does;
  - the budgets;
  - every item renders or says why not;
  - the EM frame and the pending set;
  - China's 10.7 set;
  - the named hooks degrade, and fill when their module is present (a fake module);
  - China's computed rows;
  - **China's quote-only rule:**
    - the note is quoted verbatim, with no prose frame and no model call;
    - the summary slice does not carry the note;
    - the rule is in the frame;
  - crypto's five pages in the fixed shape, the light tier, the plumbing, the computed tests and the scenarios;
  - credit's computed test and BB–CCC;
  - real estate's spread and families;
  - GTM-19;
  - agriculture's no-draft rule;
  - **Thailand's isolation:**
    - no Thai row is a trigger-eligible key;
    - no registry entry under `namespace: thailand` is trigger-eligible;
    - no trigger config names Thailand, THB or DEXTHUS;
    - pillar 11 has no dial, weight or metrics;
    - no code reads the Thai calendar but through this chapter's config;
    - no private-core column prints;
    - no draft is written;
  - the executive summary as one frame per chapter over all eleven, each carrying its chapter's words and rules.
- **Formatting:**
  - Dollar series print as $3.36tn, $738.00bn and so on, rather than
    3,248,000,000,000.0. This applies to part 1's TIC row too.
  - Sub-0.01 levels print at four significant figures.
  - A row's `dp` governs a raw change (ZEC/BTC +0.000008).

## What waits, and for what

| Waits for | What |
|---|---|
| **AQ-14** (the EM paper) | The EM frame (the interim prints until filed), EM's and China's twelve-month sets, any EM or China tests and ten questions |
| **AQ-9a** (`aq-9a-em-scorecard`) | The vulnerability scorecard (EM 4d) |
| **c1-move-screen** (session A) | The SR-46 episode list (EM 4e) |
| **imf-ifs-gold** | The IFS gold cross-check row and analysis (China) |
| **AQ-5** | EM and China break logic; item 8 everywhere; the S12 copper–gold routing |
| **AQ-6** | Items 1, 2, 10 and the "This quarter" column of every scenario set |
| **AQ-8 / AQ-8a** | The gold–BTC rotation, effective float, the IBIT two-bid, the driver attribution |
| **AQ-3** (series) | ICE BofA EM spreads, the EM FX basket and dollar index, IIF flows, the basis; CNH; TSF, China property, capacity, participation; ETH, SOL and the crypto structure set (stablecoins, LTH, funding, DVOL, ETF share counts); SLOOS, BDC discounts; Case-Shiller; regional valuation and earnings, hedged funds, BTP–Bund; DEXTHUS and the BoT/NESDC rows (with AQ-12); WASDE, grain and softs prices, disaggregated COT (with AQ-13) |
| **ST-13** | Every PRL field (the crypto.watch entry, S1–S8, D1–D6) |
| **AQ-7** (the quarterly scan) | China's stored reporting (`china.*` source ids), the policy ladder's stages, the IMF Article IV read; Thailand's sourced reporting; crypto's mechanisms, regulation and catalysts; agriculture's trade events |
| **The chain capture** | Implied ranges for EEM, FXI, IBIT, XLRE, HYG and EFA, each printed as "not in the chain capture" |
| **By hand** | The China and Thailand calendars; the operator's political note each quarter; the Thailand frame's migration (decision 3); the four MW-6 promotions |

## Choices made for the operator to overrule

1. **The template governs.** Light chapters do not print items 5, 6, 9 or 11.
   Credit's ten questions are carried in config, verbatim and gate-checked, but
   not printed. A one-key change in `config/reporting_stack.yaml`'s template
   prints them.
2. **China has no owning paper, so its tests say "not stated".** XXI 10.6
   supplies the observables and 10.7 the ten-year set, but neither is a test.
3. **The operator's note is stored as a voices row:**
   - `source_id: operator.china_political_note`, `origin: operator`, `tier: 1`, `kind: independent`;
   - the voices schema has no "operator tier", and caps a view at 45 words, so a
     longer note is several rows.

   Stored political reporting is matched by the `china.` source-id prefix (a
   convention for AQ-7's China sources). It is classed as an authoritative
   release or commentary by outlet name, against the list in config.
4. **The executive summary never sees the quote-only sub-sections.** Each
   chapter's word rules join its summary frame.
5. **c1-move-screen's hook name is provisional:**
   `altdata.move_screen.quarter_episodes(st, now)`. Session A's name was not
   known at writing. It is one line in config.
6. **Session-set measurables:**

   | Test | Reading |
   |---|---|
   | BTC store of value | A 63-session correlation of daily log returns against SPY inside 0.4–0.7 reads "strained". It never fails, because "another full cycle" is not declared |
   | Institutional adoption | The drawdown from BTC's stored high: fails at 70%, strained at 50% |
   | Lending standards | The HY OAS change over the quarter above 200 bp. With no such widening the test holds, whatever SLOOS did |
   | Credit leads equities | SPY's drawdown from its one-year high, 15% |
7. **Scenario sets print the paper's prior.** No probability is typed for
   Thailand's map or agriculture's four: neither has a paper.
8. **The coin page's "Bull / base / bear" reads the vendored 3 Sep case file.**
   Its `flat` is labelled "base (range-bound)".
9. **Words.** The permitted and banned lists are session-set starting lists.
   China's and Thailand's rules are written as banned behaviour.
10. **Uncaptured funds are named rather than left off.** Each chapter names a
    fund for its implied range even where the chain is not captured, so the gap
    is visible.
11. **Thailand keeps items 1 and 2** (the theses, via AQ-6). Its isolation is
    held at the triggers and the book: no draft is written.
12. **Part 1's chapters were not given scenario sets (2a).** The change order
    lists theirs (§4.2–§4.4), and adding them is config only.

## Needs you

1. Store the quarterly China political note as voices rows with `source_id: operator.china_political_note` (origin operator, tier 1, ≤ 45 words a row)? yes / no
2. Keep Thailand's theses (items 1–2) on the ledger, with no drafts? yes / no
3. Accept the session-set readings in choice 6 as they stand? yes / no
4. Is `altdata.move_screen.quarter_episodes` the c1-move-screen hook (if not, send session A's name)? yes / no
5. Merge order, inside windows: AQ-1, then part 1, then this branch? yes / no
