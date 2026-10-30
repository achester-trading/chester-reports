# T&B harness ledger -- the 3 Sep thirteen through Part 23's overlays (6i-2)

**Edition:** 2026-10-26, laptop run over the observation store, read-only, as of each decision date. A re-run against the box's store supersedes it (a new dated file); this one is never edited.

**The pass rule is pre-registered** (the calibration-ledger convention of 17 Oct 2026): written in config/tb_episodes.yaml before this edition ran, printed here verbatim with its SHA-256, held equal by tools/validate_tb_harness.py. A re-run may apply it, never change it.

> The harness's first edition is read twice. First, the ledger's own question: does it reproduce the 3 Sep record (tops 0/3, bottoms 4/6, controls 4/4)? That record was the composite's, and decision 3 stores no composite, so the answer is REPRODUCED only if every class is read and each class's k of n equals the record's; otherwise NOT REPRODUCIBLE ON THIS BUILD, with the class that cannot be read named. Second, the overlays' own record on the thirteen: a top is called when any overlay FIRES at its decision date; a control is refused when no overlay FIRES at either of its decision dates; the bottoms are not scored by the overlays, which are top-side. PASS when all three tops and all four controls are read, at least 2 of 3 tops are called and at least 3 of 4 controls are refused; INSUFFICIENT when any top or control is unread (an overlay neither FIRES nor is CLEAR because too few of its triggers are read); FAIL otherwise. The extended set is reported beside it and never enters either count.

| | |
|---|---|
| As of | each decision date's close (23:59 ET), by available_at; Shiller's months lagged 3 months; run 2026-10-26T18:46 UTC |
| Window | the 3 Sep thirteen, 1990-10-11 to 2024-08-05; the extended set beside it, never pooled |
| n | 13 episodes, 17 decision dates; extended 50 dates |
| Statistic | the overlays' record: tops 0/3 (3 unread), controls 0/4 (4 unread), bottoms —/6 |
| Pass rule | as quoted above |
| Pass rule SHA-256 | `937503cbe9ba98051c0888a6e8214e48b20d31967a2c6d5adc245168913c250a` |
| Verdict | **INSUFFICIENT (3 of 3 tops and 4 of 4 controls unread)** |
| Rights consequence | None. Report-only (the brief, 2.5): nothing enters a composite, the market-state object, a dial, a band or a packet; no composite is stored (decision 3). |

## The ledger's own question

**Does the harness reproduce "tops 0/3, bottoms 4/6, controls 4/4"?** **NOT REPRODUCIBLE ON THIS BUILD -- tops (3 unread), controls (4 unread), bottoms (not scored by the overlays).** The record was the composite's under the original weights (the architecture's Part 23); the composite and its hand-keyed table stayed in the 3 Sep session and decision 3 stores none, so the harness reads Part 23's three overlays instead. They are top-side: a bottom is not scored by them. The overlays' own record: tops 0/3 (3 unread), controls 0/4 (4 unread), bottoms —/6.

## The thirteen

| Episode | Class | Date | S&P 500 in the store | Concentration | HY acceleration | Liquidity | Classification | Session-set |
|---|---|---|---|---|---|---|---|---|
| top_2000 | top | 2000-03-24 | agrees (1,527.46) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 2 not existent) | unread | no |
| top_2007 | top | 2007-10-09 | agrees (1,565.15) | UNREAD 1/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 1 not existent) | unread | no |
| top_2022 | top | 2022-01-03 | agrees (4,796.56) | UNREAD 1/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read) | unread | no |
| bottom_1990 | bottom | 1990-10-11 | agrees (295.46) | UNREAD 0/5 (1 read, 1 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) | not scored | yes |
| bottom_2002 | bottom | 2002-10-09 | agrees (776.76) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 2 not existent) | not scored | yes |
| bottom_2009 | bottom | 2009-03-09 | agrees (676.53) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 1 not existent) | not scored | yes |
| bottom_2011 | bottom | 2011-10-03 | agrees (1,099.23) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 1 not existent) | not scored | yes |
| bottom_2020 | bottom | 2020-03-23 | agrees (2,237.40) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read) | not scored | yes |
| bottom_2022 | bottom | 2022-10-12 | agrees (3,577.03) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read) | not scored | no |
| control_1998 | control | 1998-07-17 | agrees (1,186.75) | UNREAD 1/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 2 not existent) | unread | yes |
|  |  | 1998-10-08 | agrees (959.44) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 2 not existent) |  |  |
| control_2015 | control | 2015-05-21 | agrees (2,130.82) | UNREAD 1/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 1 not existent) | unread | yes |
|  |  | 2016-02-11 | agrees (1,829.08) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 1 not existent) |  |  |
| control_2018 | control | 2018-09-20 | agrees (2,930.75) | UNREAD 1/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read) | unread | no |
|  |  | 2018-12-24 | agrees (2,351.10) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read) |  |  |
| control_2024 | control | 2024-07-16 | agrees (5,667.20) | UNREAD 1/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read) | unread | yes |
|  |  | 2024-08-05 | agrees (5,186.33) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read) |  |  |

Each episode's source passage, and the basis of every session-set date or class, is in config/tb_episodes.yaml and the notes (docs/briefs/a77-6i-notes.md).

## Point in time against the papers' hand-keyed values

The papers' figures were "hand-compiled for this study, not machine-extracted from a point-in-time database" (Tops and Bottoms, "Caveats restated"). Beside each, the harness's reading as of the date; "differs" past 10% of the paper's value.

| Episode | Date | Metric | Paper | Harness | Reading |
|---|---|---|---|---|---|
| top_2000 | 2000-03-24 | cape | 43.8 | — | harness unread: shiller.cape not stored as of 2000-03-24 |
| top_2000 | 2000-03-24 | fwd_pe | 24.5 | — | harness unread: index.forward_pe not stored as of 2000-03-24 |
| top_2000 | 2000-03-24 | erp | 0.4 | — | harness unread: shiller.cape not stored as of 2000-03-24; shiller.gs10 not stored as of 2000-03-24 |
| top_2000 | 2000-03-24 | vix | 22.5 | 23.31 | agrees |
| top_2000 | 2000-03-24 | hy_oas_bp | 575 | — | harness unread: pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2000-03-24) |
| top_2007 | 2007-10-09 | cape | 27.3 | — | harness unread: shiller.cape not stored as of 2007-10-09 |
| top_2007 | 2007-10-09 | fwd_pe | 15.5 | — | harness unread: index.forward_pe not stored as of 2007-10-09 |
| top_2007 | 2007-10-09 | vix | 18 | 16.12 | differs |
| top_2007 | 2007-10-09 | hy_oas_bp | 410 | — | harness unread: pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2007-10-09) |
| top_2022 | 2022-01-03 | cape | 39.4 | — | harness unread: shiller.cape not stored as of 2022-01-03 |
| top_2022 | 2022-01-03 | fwd_pe | 21.7 | — | harness unread: index.forward_pe not stored as of 2022-01-03 |
| top_2022 | 2022-01-03 | erp | 1.4 | — | harness unread: shiller.cape not stored as of 2022-01-03; shiller.gs10 not stored as of 2022-01-03 |
| top_2022 | 2022-01-03 | vix | 16.6 | 16.60 | agrees |
| top_2022 | 2022-01-03 | hy_oas_bp | 315 | — | harness unread: pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2022-01-03) |
| bottom_1990 | 1990-10-11 | cape | 14.8 | — | harness unread: shiller.cape not stored as of 1990-10-11 |
| bottom_2002 | 2002-10-09 | cape | 21.5 | — | harness unread: shiller.cape not stored as of 2002-10-09 |
| bottom_2002 | 2002-10-09 | fwd_pe | 14.5 | — | harness unread: index.forward_pe not stored as of 2002-10-09 |
| bottom_2002 | 2002-10-09 | erp | 2.8 | — | harness unread: shiller.cape not stored as of 2002-10-09; shiller.gs10 not stored as of 2002-10-09 |
| bottom_2002 | 2002-10-09 | vix | 42 | 42.13 | agrees |
| bottom_2002 | 2002-10-09 | hy_oas_bp | 1010 | — | harness unread: pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2002-10-09) |
| bottom_2009 | 2009-03-09 | cape | 13.3 | — | harness unread: shiller.cape not stored as of 2009-03-09 |
| bottom_2009 | 2009-03-09 | fwd_pe | 10.3 | — | harness unread: index.forward_pe not stored as of 2009-03-09 |
| bottom_2009 | 2009-03-09 | vix | 50 | 49.68 | agrees |
| bottom_2009 | 2009-03-09 | hy_oas_bp | 1600 | — | harness unread: pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2009-03-09) |
| bottom_2011 | 2011-10-03 | vix | 48 | 45.45 | agrees |
| bottom_2011 | 2011-10-03 | hy_oas_bp | 800 | — | harness unread: pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2011-10-03) |
| bottom_2020 | 2020-03-23 | cape | 24.8 | — | harness unread: shiller.cape not stored as of 2020-03-23 |
| bottom_2020 | 2020-03-23 | fwd_pe | 13.3 | — | harness unread: index.forward_pe not stored as of 2020-03-23 |
| bottom_2020 | 2020-03-23 | vix | 61.6 | 61.59 | agrees |
| bottom_2020 | 2020-03-23 | hy_oas_bp | 1087 | — | harness unread: pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2020-03-23) |
| bottom_2022 | 2022-10-12 | cape | 27.1 | — | harness unread: shiller.cape not stored as of 2022-10-12 |
| bottom_2022 | 2022-10-12 | fwd_pe | 15.2 | — | harness unread: index.forward_pe not stored as of 2022-10-12 |
| bottom_2022 | 2022-10-12 | erp | 1.6 | — | harness unread: shiller.cape not stored as of 2022-10-12; shiller.gs10 not stored as of 2022-10-12 |
| bottom_2022 | 2022-10-12 | vix | 33.6 | 33.57 | agrees |
| bottom_2022 | 2022-10-12 | hy_oas_bp | 540 | — | harness unread: pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2022-10-12) |
| control_2018 | 2018-12-24 | hy_oas_bp | 545 | — | harness unread: pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2018-12-24) |

## The trigger readings at the thirteen's dates

| Episode | Date | Overlay | Trigger | Reading |
|---|---|---|---|---|
| top_2000 | 2000-03-24 | Concentration & Complacency | FwdPE ≥ 20 | not stored: index.forward_pe not stored as of 2000-03-24 |
| top_2000 | 2000-03-24 | Concentration & Complacency | CAPE ≥ 30 | not stored: shiller.cape not stored as of 2000-03-24 |
| top_2000 | 2000-03-24 | Concentration & Complacency | ERP ≤ 1.5% | not stored: shiller.cape not stored as of 2000-03-24; shiller.gs10 not stored as of 2000-03-24 |
| top_2000 | 2000-03-24 | Concentration & Complacency | Top10 ≥ 25% | not stored: top-10 share not stored as of 2000-03-24 (no SPY holdings are stored (the constituent writer)) |
| top_2000 | 2000-03-24 | Concentration & Complacency | VIX ≤ 18 | quiet: 23.31 (2000-03-24) |
| top_2000 | 2000-03-24 | HY Spread Acceleration | HY ≥ +50% off its 12-month low | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2000-03-24) |
| top_2000 | 2000-03-24 | HY Spread Acceleration | 30-day HY ≥ +40bp | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2000-03-24) |
| top_2000 | 2000-03-24 | HY Spread Acceleration | 30-day IG ≥ +15bp | not stored: fred.ig_oas not stored as of 2000-03-24 |
| top_2000 | 2000-03-24 | HY Spread Acceleration | IG ≥ 110bp | not stored: fred.ig_oas not stored as of 2000-03-24 |
| top_2000 | 2000-03-24 | Liquidity & Funding Stress | NetLiq YoY ≤ −10% | not existent: net_liq not existent before 2002-12-18 |
| top_2000 | 2000-03-24 | Liquidity & Funding Stress | reserves ≤ $3.15T | not stored: fred.bank_reserves not stored as of 2000-03-24 |
| top_2000 | 2000-03-24 | Liquidity & Funding Stress | SOFR−IORB ≥ +5bp, 5 days | not existent: sofr not existent before 2018-04-02; iorb not existent before 2021-07-29 |
| top_2000 | 2000-03-24 | Liquidity & Funding Stress | RRP ≤ $200B | not stored: fred.rrp not stored as of 2000-03-24 |
| top_2000 | 2000-03-24 | Liquidity & Funding Stress | |TGAΔ| ≥ $200B | not stored: fred.tga not stored as of 2000-03-24 |
| top_2007 | 2007-10-09 | Concentration & Complacency | FwdPE ≥ 20 | not stored: index.forward_pe not stored as of 2007-10-09 |
| top_2007 | 2007-10-09 | Concentration & Complacency | CAPE ≥ 30 | not stored: shiller.cape not stored as of 2007-10-09 |
| top_2007 | 2007-10-09 | Concentration & Complacency | ERP ≤ 1.5% | not stored: shiller.cape not stored as of 2007-10-09; shiller.gs10 not stored as of 2007-10-09 |
| top_2007 | 2007-10-09 | Concentration & Complacency | Top10 ≥ 25% | not stored: top-10 share not stored as of 2007-10-09 (no SPY holdings are stored (the constituent writer)) |
| top_2007 | 2007-10-09 | Concentration & Complacency | VIX ≤ 18 | fires: 16.12 (2007-10-09) |
| top_2007 | 2007-10-09 | HY Spread Acceleration | HY ≥ +50% off its 12-month low | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2007-10-09) |
| top_2007 | 2007-10-09 | HY Spread Acceleration | 30-day HY ≥ +40bp | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2007-10-09) |
| top_2007 | 2007-10-09 | HY Spread Acceleration | 30-day IG ≥ +15bp | not stored: fred.ig_oas not stored as of 2007-10-09 |
| top_2007 | 2007-10-09 | HY Spread Acceleration | IG ≥ 110bp | not stored: fred.ig_oas not stored as of 2007-10-09 |
| top_2007 | 2007-10-09 | Liquidity & Funding Stress | NetLiq YoY ≤ −10% | not stored: calc.net_liquidity not stored as of 2007-10-09 |
| top_2007 | 2007-10-09 | Liquidity & Funding Stress | reserves ≤ $3.15T | not stored: fred.bank_reserves not stored as of 2007-10-09 |
| top_2007 | 2007-10-09 | Liquidity & Funding Stress | SOFR−IORB ≥ +5bp, 5 days | not existent: sofr not existent before 2018-04-02; iorb not existent before 2021-07-29 |
| top_2007 | 2007-10-09 | Liquidity & Funding Stress | RRP ≤ $200B | not stored: fred.rrp not stored as of 2007-10-09 |
| top_2007 | 2007-10-09 | Liquidity & Funding Stress | |TGAΔ| ≥ $200B | not stored: fred.tga not stored as of 2007-10-09 |
| top_2022 | 2022-01-03 | Concentration & Complacency | FwdPE ≥ 20 | not stored: index.forward_pe not stored as of 2022-01-03 |
| top_2022 | 2022-01-03 | Concentration & Complacency | CAPE ≥ 30 | not stored: shiller.cape not stored as of 2022-01-03 |
| top_2022 | 2022-01-03 | Concentration & Complacency | ERP ≤ 1.5% | not stored: shiller.cape not stored as of 2022-01-03; shiller.gs10 not stored as of 2022-01-03 |
| top_2022 | 2022-01-03 | Concentration & Complacency | Top10 ≥ 25% | not stored: top-10 share not stored as of 2022-01-03 (no SPY holdings are stored (the constituent writer)) |
| top_2022 | 2022-01-03 | Concentration & Complacency | VIX ≤ 18 | fires: 16.60 (2022-01-03) |
| top_2022 | 2022-01-03 | HY Spread Acceleration | HY ≥ +50% off its 12-month low | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2022-01-03) |
| top_2022 | 2022-01-03 | HY Spread Acceleration | 30-day HY ≥ +40bp | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2022-01-03) |
| top_2022 | 2022-01-03 | HY Spread Acceleration | 30-day IG ≥ +15bp | not stored: fred.ig_oas not stored as of 2022-01-03 |
| top_2022 | 2022-01-03 | HY Spread Acceleration | IG ≥ 110bp | not stored: fred.ig_oas not stored as of 2022-01-03 |
| top_2022 | 2022-01-03 | Liquidity & Funding Stress | NetLiq YoY ≤ −10% | not stored: calc.net_liquidity not stored as of 2022-01-03 |
| top_2022 | 2022-01-03 | Liquidity & Funding Stress | reserves ≤ $3.15T | not stored: fred.bank_reserves not stored as of 2022-01-03 |
| top_2022 | 2022-01-03 | Liquidity & Funding Stress | SOFR−IORB ≥ +5bp, 5 days | not stored: fred.sofr not stored as of 2022-01-03; fred.iorb not stored as of 2022-01-03 |
| top_2022 | 2022-01-03 | Liquidity & Funding Stress | RRP ≤ $200B | not stored: fred.rrp not stored as of 2022-01-03 |
| top_2022 | 2022-01-03 | Liquidity & Funding Stress | |TGAΔ| ≥ $200B | not stored: fred.tga not stored as of 2022-01-03 |
| bottom_1990 | 1990-10-11 | Concentration & Complacency | FwdPE ≥ 20 | not existent: fwd_pe not existent before 1995-01-01 |
| bottom_1990 | 1990-10-11 | Concentration & Complacency | CAPE ≥ 30 | not stored: shiller.cape not stored as of 1990-10-11 |
| bottom_1990 | 1990-10-11 | Concentration & Complacency | ERP ≤ 1.5% | not stored: shiller.cape not stored as of 1990-10-11; shiller.gs10 not stored as of 1990-10-11 |
| bottom_1990 | 1990-10-11 | Concentration & Complacency | Top10 ≥ 25% | not stored: top-10 share not stored as of 1990-10-11 (no SPY holdings are stored (the constituent writer)) |
| bottom_1990 | 1990-10-11 | Concentration & Complacency | VIX ≤ 18 | quiet: 33.98 (1990-10-11) |
| bottom_1990 | 1990-10-11 | HY Spread Acceleration | HY ≥ +50% off its 12-month low | pending 6i-3: Baa less the 10-year (hy_oas not existent before 1996-12-31) |
| bottom_1990 | 1990-10-11 | HY Spread Acceleration | 30-day HY ≥ +40bp | pending 6i-3: Baa less the 10-year (hy_oas not existent before 1996-12-31) |
| bottom_1990 | 1990-10-11 | HY Spread Acceleration | 30-day IG ≥ +15bp | not existent: ig_oas not existent before 1996-12-31 |
| bottom_1990 | 1990-10-11 | HY Spread Acceleration | IG ≥ 110bp | not existent: ig_oas not existent before 1996-12-31 |
| bottom_1990 | 1990-10-11 | Liquidity & Funding Stress | NetLiq YoY ≤ −10% | not existent: net_liq not existent before 2002-12-18 |
| bottom_1990 | 1990-10-11 | Liquidity & Funding Stress | reserves ≤ $3.15T | not stored: fred.bank_reserves not stored as of 1990-10-11 |
| bottom_1990 | 1990-10-11 | Liquidity & Funding Stress | SOFR−IORB ≥ +5bp, 5 days | not existent: sofr not existent before 2018-04-02; iorb not existent before 2021-07-29 |
| bottom_1990 | 1990-10-11 | Liquidity & Funding Stress | RRP ≤ $200B | not stored: fred.rrp not stored as of 1990-10-11 |
| bottom_1990 | 1990-10-11 | Liquidity & Funding Stress | |TGAΔ| ≥ $200B | not stored: fred.tga not stored as of 1990-10-11 |
| bottom_2002 | 2002-10-09 | Concentration & Complacency | FwdPE ≥ 20 | not stored: index.forward_pe not stored as of 2002-10-09 |
| bottom_2002 | 2002-10-09 | Concentration & Complacency | CAPE ≥ 30 | not stored: shiller.cape not stored as of 2002-10-09 |
| bottom_2002 | 2002-10-09 | Concentration & Complacency | ERP ≤ 1.5% | not stored: shiller.cape not stored as of 2002-10-09; shiller.gs10 not stored as of 2002-10-09 |
| bottom_2002 | 2002-10-09 | Concentration & Complacency | Top10 ≥ 25% | not stored: top-10 share not stored as of 2002-10-09 (no SPY holdings are stored (the constituent writer)) |
| bottom_2002 | 2002-10-09 | Concentration & Complacency | VIX ≤ 18 | quiet: 42.13 (2002-10-09) |
| bottom_2002 | 2002-10-09 | HY Spread Acceleration | HY ≥ +50% off its 12-month low | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2002-10-09) |
| bottom_2002 | 2002-10-09 | HY Spread Acceleration | 30-day HY ≥ +40bp | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2002-10-09) |
| bottom_2002 | 2002-10-09 | HY Spread Acceleration | 30-day IG ≥ +15bp | not stored: fred.ig_oas not stored as of 2002-10-09 |
| bottom_2002 | 2002-10-09 | HY Spread Acceleration | IG ≥ 110bp | not stored: fred.ig_oas not stored as of 2002-10-09 |
| bottom_2002 | 2002-10-09 | Liquidity & Funding Stress | NetLiq YoY ≤ −10% | not existent: net_liq not existent before 2002-12-18 |
| bottom_2002 | 2002-10-09 | Liquidity & Funding Stress | reserves ≤ $3.15T | not stored: fred.bank_reserves not stored as of 2002-10-09 |
| bottom_2002 | 2002-10-09 | Liquidity & Funding Stress | SOFR−IORB ≥ +5bp, 5 days | not existent: sofr not existent before 2018-04-02; iorb not existent before 2021-07-29 |
| bottom_2002 | 2002-10-09 | Liquidity & Funding Stress | RRP ≤ $200B | not stored: fred.rrp not stored as of 2002-10-09 |
| bottom_2002 | 2002-10-09 | Liquidity & Funding Stress | |TGAΔ| ≥ $200B | not stored: fred.tga not stored as of 2002-10-09 |
| bottom_2009 | 2009-03-09 | Concentration & Complacency | FwdPE ≥ 20 | not stored: index.forward_pe not stored as of 2009-03-09 |
| bottom_2009 | 2009-03-09 | Concentration & Complacency | CAPE ≥ 30 | not stored: shiller.cape not stored as of 2009-03-09 |
| bottom_2009 | 2009-03-09 | Concentration & Complacency | ERP ≤ 1.5% | not stored: shiller.cape not stored as of 2009-03-09; shiller.gs10 not stored as of 2009-03-09 |
| bottom_2009 | 2009-03-09 | Concentration & Complacency | Top10 ≥ 25% | not stored: top-10 share not stored as of 2009-03-09 (no SPY holdings are stored (the constituent writer)) |
| bottom_2009 | 2009-03-09 | Concentration & Complacency | VIX ≤ 18 | quiet: 49.68 (2009-03-09) |
| bottom_2009 | 2009-03-09 | HY Spread Acceleration | HY ≥ +50% off its 12-month low | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2009-03-09) |
| bottom_2009 | 2009-03-09 | HY Spread Acceleration | 30-day HY ≥ +40bp | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2009-03-09) |
| bottom_2009 | 2009-03-09 | HY Spread Acceleration | 30-day IG ≥ +15bp | not stored: fred.ig_oas not stored as of 2009-03-09 |
| bottom_2009 | 2009-03-09 | HY Spread Acceleration | IG ≥ 110bp | not stored: fred.ig_oas not stored as of 2009-03-09 |
| bottom_2009 | 2009-03-09 | Liquidity & Funding Stress | NetLiq YoY ≤ −10% | not stored: calc.net_liquidity not stored as of 2009-03-09 |
| bottom_2009 | 2009-03-09 | Liquidity & Funding Stress | reserves ≤ $3.15T | not stored: fred.bank_reserves not stored as of 2009-03-09 |
| bottom_2009 | 2009-03-09 | Liquidity & Funding Stress | SOFR−IORB ≥ +5bp, 5 days | not existent: sofr not existent before 2018-04-02; iorb not existent before 2021-07-29 |
| bottom_2009 | 2009-03-09 | Liquidity & Funding Stress | RRP ≤ $200B | not stored: fred.rrp not stored as of 2009-03-09 |
| bottom_2009 | 2009-03-09 | Liquidity & Funding Stress | |TGAΔ| ≥ $200B | not stored: fred.tga not stored as of 2009-03-09 |
| bottom_2011 | 2011-10-03 | Concentration & Complacency | FwdPE ≥ 20 | not stored: index.forward_pe not stored as of 2011-10-03 |
| bottom_2011 | 2011-10-03 | Concentration & Complacency | CAPE ≥ 30 | not stored: shiller.cape not stored as of 2011-10-03 |
| bottom_2011 | 2011-10-03 | Concentration & Complacency | ERP ≤ 1.5% | not stored: shiller.cape not stored as of 2011-10-03; shiller.gs10 not stored as of 2011-10-03 |
| bottom_2011 | 2011-10-03 | Concentration & Complacency | Top10 ≥ 25% | not stored: top-10 share not stored as of 2011-10-03 (no SPY holdings are stored (the constituent writer)) |
| bottom_2011 | 2011-10-03 | Concentration & Complacency | VIX ≤ 18 | quiet: 45.45 (2011-10-03) |
| bottom_2011 | 2011-10-03 | HY Spread Acceleration | HY ≥ +50% off its 12-month low | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2011-10-03) |
| bottom_2011 | 2011-10-03 | HY Spread Acceleration | 30-day HY ≥ +40bp | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2011-10-03) |
| bottom_2011 | 2011-10-03 | HY Spread Acceleration | 30-day IG ≥ +15bp | not stored: fred.ig_oas not stored as of 2011-10-03 |
| bottom_2011 | 2011-10-03 | HY Spread Acceleration | IG ≥ 110bp | not stored: fred.ig_oas not stored as of 2011-10-03 |
| bottom_2011 | 2011-10-03 | Liquidity & Funding Stress | NetLiq YoY ≤ −10% | not stored: calc.net_liquidity not stored as of 2011-10-03 |
| bottom_2011 | 2011-10-03 | Liquidity & Funding Stress | reserves ≤ $3.15T | not stored: fred.bank_reserves not stored as of 2011-10-03 |
| bottom_2011 | 2011-10-03 | Liquidity & Funding Stress | SOFR−IORB ≥ +5bp, 5 days | not existent: sofr not existent before 2018-04-02; iorb not existent before 2021-07-29 |
| bottom_2011 | 2011-10-03 | Liquidity & Funding Stress | RRP ≤ $200B | not stored: fred.rrp not stored as of 2011-10-03 |
| bottom_2011 | 2011-10-03 | Liquidity & Funding Stress | |TGAΔ| ≥ $200B | not stored: fred.tga not stored as of 2011-10-03 |
| bottom_2020 | 2020-03-23 | Concentration & Complacency | FwdPE ≥ 20 | not stored: index.forward_pe not stored as of 2020-03-23 |
| bottom_2020 | 2020-03-23 | Concentration & Complacency | CAPE ≥ 30 | not stored: shiller.cape not stored as of 2020-03-23 |
| bottom_2020 | 2020-03-23 | Concentration & Complacency | ERP ≤ 1.5% | not stored: shiller.cape not stored as of 2020-03-23; shiller.gs10 not stored as of 2020-03-23 |
| bottom_2020 | 2020-03-23 | Concentration & Complacency | Top10 ≥ 25% | not stored: top-10 share not stored as of 2020-03-23 (no SPY holdings are stored (the constituent writer)) |
| bottom_2020 | 2020-03-23 | Concentration & Complacency | VIX ≤ 18 | quiet: 61.59 (2020-03-23) |
| bottom_2020 | 2020-03-23 | HY Spread Acceleration | HY ≥ +50% off its 12-month low | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2020-03-23) |
| bottom_2020 | 2020-03-23 | HY Spread Acceleration | 30-day HY ≥ +40bp | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2020-03-23) |
| bottom_2020 | 2020-03-23 | HY Spread Acceleration | 30-day IG ≥ +15bp | not stored: fred.ig_oas not stored as of 2020-03-23 |
| bottom_2020 | 2020-03-23 | HY Spread Acceleration | IG ≥ 110bp | not stored: fred.ig_oas not stored as of 2020-03-23 |
| bottom_2020 | 2020-03-23 | Liquidity & Funding Stress | NetLiq YoY ≤ −10% | not stored: calc.net_liquidity not stored as of 2020-03-23 |
| bottom_2020 | 2020-03-23 | Liquidity & Funding Stress | reserves ≤ $3.15T | not stored: fred.bank_reserves not stored as of 2020-03-23 |
| bottom_2020 | 2020-03-23 | Liquidity & Funding Stress | SOFR−IORB ≥ +5bp, 5 days | not stored: fred.sofr not stored as of 2020-03-23; iorb not existent before 2021-07-29 |
| bottom_2020 | 2020-03-23 | Liquidity & Funding Stress | RRP ≤ $200B | not stored: fred.rrp not stored as of 2020-03-23 |
| bottom_2020 | 2020-03-23 | Liquidity & Funding Stress | |TGAΔ| ≥ $200B | not stored: fred.tga not stored as of 2020-03-23 |
| bottom_2022 | 2022-10-12 | Concentration & Complacency | FwdPE ≥ 20 | not stored: index.forward_pe not stored as of 2022-10-12 |
| bottom_2022 | 2022-10-12 | Concentration & Complacency | CAPE ≥ 30 | not stored: shiller.cape not stored as of 2022-10-12 |
| bottom_2022 | 2022-10-12 | Concentration & Complacency | ERP ≤ 1.5% | not stored: shiller.cape not stored as of 2022-10-12; shiller.gs10 not stored as of 2022-10-12 |
| bottom_2022 | 2022-10-12 | Concentration & Complacency | Top10 ≥ 25% | not stored: top-10 share not stored as of 2022-10-12 (no SPY holdings are stored (the constituent writer)) |
| bottom_2022 | 2022-10-12 | Concentration & Complacency | VIX ≤ 18 | quiet: 33.57 (2022-10-12) |
| bottom_2022 | 2022-10-12 | HY Spread Acceleration | HY ≥ +50% off its 12-month low | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2022-10-12) |
| bottom_2022 | 2022-10-12 | HY Spread Acceleration | 30-day HY ≥ +40bp | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2022-10-12) |
| bottom_2022 | 2022-10-12 | HY Spread Acceleration | 30-day IG ≥ +15bp | not stored: fred.ig_oas not stored as of 2022-10-12 |
| bottom_2022 | 2022-10-12 | HY Spread Acceleration | IG ≥ 110bp | not stored: fred.ig_oas not stored as of 2022-10-12 |
| bottom_2022 | 2022-10-12 | Liquidity & Funding Stress | NetLiq YoY ≤ −10% | not stored: calc.net_liquidity not stored as of 2022-10-12 |
| bottom_2022 | 2022-10-12 | Liquidity & Funding Stress | reserves ≤ $3.15T | not stored: fred.bank_reserves not stored as of 2022-10-12 |
| bottom_2022 | 2022-10-12 | Liquidity & Funding Stress | SOFR−IORB ≥ +5bp, 5 days | not stored: fred.sofr not stored as of 2022-10-12; fred.iorb not stored as of 2022-10-12 |
| bottom_2022 | 2022-10-12 | Liquidity & Funding Stress | RRP ≤ $200B | not stored: fred.rrp not stored as of 2022-10-12 |
| bottom_2022 | 2022-10-12 | Liquidity & Funding Stress | |TGAΔ| ≥ $200B | not stored: fred.tga not stored as of 2022-10-12 |
| control_1998 | 1998-07-17 | Concentration & Complacency | FwdPE ≥ 20 | not stored: index.forward_pe not stored as of 1998-07-17 |
| control_1998 | 1998-07-17 | Concentration & Complacency | CAPE ≥ 30 | not stored: shiller.cape not stored as of 1998-07-17 |
| control_1998 | 1998-07-17 | Concentration & Complacency | ERP ≤ 1.5% | not stored: shiller.cape not stored as of 1998-07-17; shiller.gs10 not stored as of 1998-07-17 |
| control_1998 | 1998-07-17 | Concentration & Complacency | Top10 ≥ 25% | not stored: top-10 share not stored as of 1998-07-17 (no SPY holdings are stored (the constituent writer)) |
| control_1998 | 1998-07-17 | Concentration & Complacency | VIX ≤ 18 | fires: 16.23 (1998-07-17) |
| control_1998 | 1998-07-17 | HY Spread Acceleration | HY ≥ +50% off its 12-month low | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 1998-07-17) |
| control_1998 | 1998-07-17 | HY Spread Acceleration | 30-day HY ≥ +40bp | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 1998-07-17) |
| control_1998 | 1998-07-17 | HY Spread Acceleration | 30-day IG ≥ +15bp | not stored: fred.ig_oas not stored as of 1998-07-17 |
| control_1998 | 1998-07-17 | HY Spread Acceleration | IG ≥ 110bp | not stored: fred.ig_oas not stored as of 1998-07-17 |
| control_1998 | 1998-07-17 | Liquidity & Funding Stress | NetLiq YoY ≤ −10% | not existent: net_liq not existent before 2002-12-18 |
| control_1998 | 1998-07-17 | Liquidity & Funding Stress | reserves ≤ $3.15T | not stored: fred.bank_reserves not stored as of 1998-07-17 |
| control_1998 | 1998-07-17 | Liquidity & Funding Stress | SOFR−IORB ≥ +5bp, 5 days | not existent: sofr not existent before 2018-04-02; iorb not existent before 2021-07-29 |
| control_1998 | 1998-07-17 | Liquidity & Funding Stress | RRP ≤ $200B | not stored: fred.rrp not stored as of 1998-07-17 |
| control_1998 | 1998-07-17 | Liquidity & Funding Stress | |TGAΔ| ≥ $200B | not stored: fred.tga not stored as of 1998-07-17 |
| control_1998 | 1998-10-08 | Concentration & Complacency | FwdPE ≥ 20 | not stored: index.forward_pe not stored as of 1998-10-08 |
| control_1998 | 1998-10-08 | Concentration & Complacency | CAPE ≥ 30 | not stored: shiller.cape not stored as of 1998-10-08 |
| control_1998 | 1998-10-08 | Concentration & Complacency | ERP ≤ 1.5% | not stored: shiller.cape not stored as of 1998-10-08; shiller.gs10 not stored as of 1998-10-08 |
| control_1998 | 1998-10-08 | Concentration & Complacency | Top10 ≥ 25% | not stored: top-10 share not stored as of 1998-10-08 (no SPY holdings are stored (the constituent writer)) |
| control_1998 | 1998-10-08 | Concentration & Complacency | VIX ≤ 18 | quiet: 45.74 (1998-10-08) |
| control_1998 | 1998-10-08 | HY Spread Acceleration | HY ≥ +50% off its 12-month low | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 1998-10-08) |
| control_1998 | 1998-10-08 | HY Spread Acceleration | 30-day HY ≥ +40bp | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 1998-10-08) |
| control_1998 | 1998-10-08 | HY Spread Acceleration | 30-day IG ≥ +15bp | not stored: fred.ig_oas not stored as of 1998-10-08 |
| control_1998 | 1998-10-08 | HY Spread Acceleration | IG ≥ 110bp | not stored: fred.ig_oas not stored as of 1998-10-08 |
| control_1998 | 1998-10-08 | Liquidity & Funding Stress | NetLiq YoY ≤ −10% | not existent: net_liq not existent before 2002-12-18 |
| control_1998 | 1998-10-08 | Liquidity & Funding Stress | reserves ≤ $3.15T | not stored: fred.bank_reserves not stored as of 1998-10-08 |
| control_1998 | 1998-10-08 | Liquidity & Funding Stress | SOFR−IORB ≥ +5bp, 5 days | not existent: sofr not existent before 2018-04-02; iorb not existent before 2021-07-29 |
| control_1998 | 1998-10-08 | Liquidity & Funding Stress | RRP ≤ $200B | not stored: fred.rrp not stored as of 1998-10-08 |
| control_1998 | 1998-10-08 | Liquidity & Funding Stress | |TGAΔ| ≥ $200B | not stored: fred.tga not stored as of 1998-10-08 |
| control_2015 | 2015-05-21 | Concentration & Complacency | FwdPE ≥ 20 | not stored: index.forward_pe not stored as of 2015-05-21 |
| control_2015 | 2015-05-21 | Concentration & Complacency | CAPE ≥ 30 | not stored: shiller.cape not stored as of 2015-05-21 |
| control_2015 | 2015-05-21 | Concentration & Complacency | ERP ≤ 1.5% | not stored: shiller.cape not stored as of 2015-05-21; shiller.gs10 not stored as of 2015-05-21 |
| control_2015 | 2015-05-21 | Concentration & Complacency | Top10 ≥ 25% | not stored: top-10 share not stored as of 2015-05-21 (no SPY holdings are stored (the constituent writer)) |
| control_2015 | 2015-05-21 | Concentration & Complacency | VIX ≤ 18 | fires: 12.11 (2015-05-21) |
| control_2015 | 2015-05-21 | HY Spread Acceleration | HY ≥ +50% off its 12-month low | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2015-05-21) |
| control_2015 | 2015-05-21 | HY Spread Acceleration | 30-day HY ≥ +40bp | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2015-05-21) |
| control_2015 | 2015-05-21 | HY Spread Acceleration | 30-day IG ≥ +15bp | not stored: fred.ig_oas not stored as of 2015-05-21 |
| control_2015 | 2015-05-21 | HY Spread Acceleration | IG ≥ 110bp | not stored: fred.ig_oas not stored as of 2015-05-21 |
| control_2015 | 2015-05-21 | Liquidity & Funding Stress | NetLiq YoY ≤ −10% | not stored: calc.net_liquidity not stored as of 2015-05-21 |
| control_2015 | 2015-05-21 | Liquidity & Funding Stress | reserves ≤ $3.15T | not stored: fred.bank_reserves not stored as of 2015-05-21 |
| control_2015 | 2015-05-21 | Liquidity & Funding Stress | SOFR−IORB ≥ +5bp, 5 days | not existent: sofr not existent before 2018-04-02; iorb not existent before 2021-07-29 |
| control_2015 | 2015-05-21 | Liquidity & Funding Stress | RRP ≤ $200B | not stored: fred.rrp not stored as of 2015-05-21 |
| control_2015 | 2015-05-21 | Liquidity & Funding Stress | |TGAΔ| ≥ $200B | not stored: fred.tga not stored as of 2015-05-21 |
| control_2015 | 2016-02-11 | Concentration & Complacency | FwdPE ≥ 20 | not stored: index.forward_pe not stored as of 2016-02-11 |
| control_2015 | 2016-02-11 | Concentration & Complacency | CAPE ≥ 30 | not stored: shiller.cape not stored as of 2016-02-11 |
| control_2015 | 2016-02-11 | Concentration & Complacency | ERP ≤ 1.5% | not stored: shiller.cape not stored as of 2016-02-11; shiller.gs10 not stored as of 2016-02-11 |
| control_2015 | 2016-02-11 | Concentration & Complacency | Top10 ≥ 25% | not stored: top-10 share not stored as of 2016-02-11 (no SPY holdings are stored (the constituent writer)) |
| control_2015 | 2016-02-11 | Concentration & Complacency | VIX ≤ 18 | quiet: 28.14 (2016-02-11) |
| control_2015 | 2016-02-11 | HY Spread Acceleration | HY ≥ +50% off its 12-month low | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2016-02-11) |
| control_2015 | 2016-02-11 | HY Spread Acceleration | 30-day HY ≥ +40bp | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2016-02-11) |
| control_2015 | 2016-02-11 | HY Spread Acceleration | 30-day IG ≥ +15bp | not stored: fred.ig_oas not stored as of 2016-02-11 |
| control_2015 | 2016-02-11 | HY Spread Acceleration | IG ≥ 110bp | not stored: fred.ig_oas not stored as of 2016-02-11 |
| control_2015 | 2016-02-11 | Liquidity & Funding Stress | NetLiq YoY ≤ −10% | not stored: calc.net_liquidity not stored as of 2016-02-11 |
| control_2015 | 2016-02-11 | Liquidity & Funding Stress | reserves ≤ $3.15T | not stored: fred.bank_reserves not stored as of 2016-02-11 |
| control_2015 | 2016-02-11 | Liquidity & Funding Stress | SOFR−IORB ≥ +5bp, 5 days | not existent: sofr not existent before 2018-04-02; iorb not existent before 2021-07-29 |
| control_2015 | 2016-02-11 | Liquidity & Funding Stress | RRP ≤ $200B | not stored: fred.rrp not stored as of 2016-02-11 |
| control_2015 | 2016-02-11 | Liquidity & Funding Stress | |TGAΔ| ≥ $200B | not stored: fred.tga not stored as of 2016-02-11 |
| control_2018 | 2018-09-20 | Concentration & Complacency | FwdPE ≥ 20 | not stored: index.forward_pe not stored as of 2018-09-20 |
| control_2018 | 2018-09-20 | Concentration & Complacency | CAPE ≥ 30 | not stored: shiller.cape not stored as of 2018-09-20 |
| control_2018 | 2018-09-20 | Concentration & Complacency | ERP ≤ 1.5% | not stored: shiller.cape not stored as of 2018-09-20; shiller.gs10 not stored as of 2018-09-20 |
| control_2018 | 2018-09-20 | Concentration & Complacency | Top10 ≥ 25% | not stored: top-10 share not stored as of 2018-09-20 (no SPY holdings are stored (the constituent writer)) |
| control_2018 | 2018-09-20 | Concentration & Complacency | VIX ≤ 18 | fires: 11.80 (2018-09-20) |
| control_2018 | 2018-09-20 | HY Spread Acceleration | HY ≥ +50% off its 12-month low | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2018-09-20) |
| control_2018 | 2018-09-20 | HY Spread Acceleration | 30-day HY ≥ +40bp | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2018-09-20) |
| control_2018 | 2018-09-20 | HY Spread Acceleration | 30-day IG ≥ +15bp | not stored: fred.ig_oas not stored as of 2018-09-20 |
| control_2018 | 2018-09-20 | HY Spread Acceleration | IG ≥ 110bp | not stored: fred.ig_oas not stored as of 2018-09-20 |
| control_2018 | 2018-09-20 | Liquidity & Funding Stress | NetLiq YoY ≤ −10% | not stored: calc.net_liquidity not stored as of 2018-09-20 |
| control_2018 | 2018-09-20 | Liquidity & Funding Stress | reserves ≤ $3.15T | not stored: fred.bank_reserves not stored as of 2018-09-20 |
| control_2018 | 2018-09-20 | Liquidity & Funding Stress | SOFR−IORB ≥ +5bp, 5 days | not stored: fred.sofr not stored as of 2018-09-20; iorb not existent before 2021-07-29 |
| control_2018 | 2018-09-20 | Liquidity & Funding Stress | RRP ≤ $200B | not stored: fred.rrp not stored as of 2018-09-20 |
| control_2018 | 2018-09-20 | Liquidity & Funding Stress | |TGAΔ| ≥ $200B | not stored: fred.tga not stored as of 2018-09-20 |
| control_2018 | 2018-12-24 | Concentration & Complacency | FwdPE ≥ 20 | not stored: index.forward_pe not stored as of 2018-12-24 |
| control_2018 | 2018-12-24 | Concentration & Complacency | CAPE ≥ 30 | not stored: shiller.cape not stored as of 2018-12-24 |
| control_2018 | 2018-12-24 | Concentration & Complacency | ERP ≤ 1.5% | not stored: shiller.cape not stored as of 2018-12-24; shiller.gs10 not stored as of 2018-12-24 |
| control_2018 | 2018-12-24 | Concentration & Complacency | Top10 ≥ 25% | not stored: top-10 share not stored as of 2018-12-24 (no SPY holdings are stored (the constituent writer)) |
| control_2018 | 2018-12-24 | Concentration & Complacency | VIX ≤ 18 | quiet: 36.07 (2018-12-24) |
| control_2018 | 2018-12-24 | HY Spread Acceleration | HY ≥ +50% off its 12-month low | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2018-12-24) |
| control_2018 | 2018-12-24 | HY Spread Acceleration | 30-day HY ≥ +40bp | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2018-12-24) |
| control_2018 | 2018-12-24 | HY Spread Acceleration | 30-day IG ≥ +15bp | not stored: fred.ig_oas not stored as of 2018-12-24 |
| control_2018 | 2018-12-24 | HY Spread Acceleration | IG ≥ 110bp | not stored: fred.ig_oas not stored as of 2018-12-24 |
| control_2018 | 2018-12-24 | Liquidity & Funding Stress | NetLiq YoY ≤ −10% | not stored: calc.net_liquidity not stored as of 2018-12-24 |
| control_2018 | 2018-12-24 | Liquidity & Funding Stress | reserves ≤ $3.15T | not stored: fred.bank_reserves not stored as of 2018-12-24 |
| control_2018 | 2018-12-24 | Liquidity & Funding Stress | SOFR−IORB ≥ +5bp, 5 days | not stored: fred.sofr not stored as of 2018-12-24; iorb not existent before 2021-07-29 |
| control_2018 | 2018-12-24 | Liquidity & Funding Stress | RRP ≤ $200B | not stored: fred.rrp not stored as of 2018-12-24 |
| control_2018 | 2018-12-24 | Liquidity & Funding Stress | |TGAΔ| ≥ $200B | not stored: fred.tga not stored as of 2018-12-24 |
| control_2024 | 2024-07-16 | Concentration & Complacency | FwdPE ≥ 20 | not stored: index.forward_pe not stored as of 2024-07-16 |
| control_2024 | 2024-07-16 | Concentration & Complacency | CAPE ≥ 30 | not stored: shiller.cape not stored as of 2024-07-16 |
| control_2024 | 2024-07-16 | Concentration & Complacency | ERP ≤ 1.5% | not stored: shiller.cape not stored as of 2024-07-16; shiller.gs10 not stored as of 2024-07-16 |
| control_2024 | 2024-07-16 | Concentration & Complacency | Top10 ≥ 25% | not stored: top-10 share not stored as of 2024-07-16 (no SPY holdings are stored (the constituent writer)) |
| control_2024 | 2024-07-16 | Concentration & Complacency | VIX ≤ 18 | fires: 13.19 (2024-07-16) |
| control_2024 | 2024-07-16 | HY Spread Acceleration | HY ≥ +50% off its 12-month low | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2024-07-16) |
| control_2024 | 2024-07-16 | HY Spread Acceleration | 30-day HY ≥ +40bp | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2024-07-16) |
| control_2024 | 2024-07-16 | HY Spread Acceleration | 30-day IG ≥ +15bp | not stored: fred.ig_oas not stored as of 2024-07-16 |
| control_2024 | 2024-07-16 | HY Spread Acceleration | IG ≥ 110bp | not stored: fred.ig_oas not stored as of 2024-07-16 |
| control_2024 | 2024-07-16 | Liquidity & Funding Stress | NetLiq YoY ≤ −10% | not stored: calc.net_liquidity not stored as of 2024-07-16 |
| control_2024 | 2024-07-16 | Liquidity & Funding Stress | reserves ≤ $3.15T | not stored: fred.bank_reserves not stored as of 2024-07-16 |
| control_2024 | 2024-07-16 | Liquidity & Funding Stress | SOFR−IORB ≥ +5bp, 5 days | not stored: fred.sofr not stored as of 2024-07-16; fred.iorb not stored as of 2024-07-16 |
| control_2024 | 2024-07-16 | Liquidity & Funding Stress | RRP ≤ $200B | not stored: fred.rrp not stored as of 2024-07-16 |
| control_2024 | 2024-07-16 | Liquidity & Funding Stress | |TGAΔ| ≥ $200B | not stored: fred.tga not stored as of 2024-07-16 |
| control_2024 | 2024-08-05 | Concentration & Complacency | FwdPE ≥ 20 | not stored: index.forward_pe not stored as of 2024-08-05 |
| control_2024 | 2024-08-05 | Concentration & Complacency | CAPE ≥ 30 | not stored: shiller.cape not stored as of 2024-08-05 |
| control_2024 | 2024-08-05 | Concentration & Complacency | ERP ≤ 1.5% | not stored: shiller.cape not stored as of 2024-08-05; shiller.gs10 not stored as of 2024-08-05 |
| control_2024 | 2024-08-05 | Concentration & Complacency | Top10 ≥ 25% | not stored: top-10 share not stored as of 2024-08-05 (no SPY holdings are stored (the constituent writer)) |
| control_2024 | 2024-08-05 | Concentration & Complacency | VIX ≤ 18 | quiet: 38.57 (2024-08-05) |
| control_2024 | 2024-08-05 | HY Spread Acceleration | HY ≥ +50% off its 12-month low | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2024-08-05) |
| control_2024 | 2024-08-05 | HY Spread Acceleration | 30-day HY ≥ +40bp | pending 6i-3: Baa less the 10-year (fred.hy_oas not stored as of 2024-08-05) |
| control_2024 | 2024-08-05 | HY Spread Acceleration | 30-day IG ≥ +15bp | not stored: fred.ig_oas not stored as of 2024-08-05 |
| control_2024 | 2024-08-05 | HY Spread Acceleration | IG ≥ 110bp | not stored: fred.ig_oas not stored as of 2024-08-05 |
| control_2024 | 2024-08-05 | Liquidity & Funding Stress | NetLiq YoY ≤ −10% | not stored: calc.net_liquidity not stored as of 2024-08-05 |
| control_2024 | 2024-08-05 | Liquidity & Funding Stress | reserves ≤ $3.15T | not stored: fred.bank_reserves not stored as of 2024-08-05 |
| control_2024 | 2024-08-05 | Liquidity & Funding Stress | SOFR−IORB ≥ +5bp, 5 days | not stored: fred.sofr not stored as of 2024-08-05; fred.iorb not stored as of 2024-08-05 |
| control_2024 | 2024-08-05 | Liquidity & Funding Stress | RRP ≤ $200B | not stored: fred.rrp not stored as of 2024-08-05 |
| control_2024 | 2024-08-05 | Liquidity & Funding Stress | |TGAΔ| ≥ $200B | not stored: fred.tga not stored as of 2024-08-05 |

## The extended set (flagged; never pooled with the thirteen)

Base Rates, chapter 12's first amendment: "the harness must not score a signal that could not have existed". A date before a series begins reads it as not existent.

| Set | Episode | Class | Date | S&P 500 in the store | Concentration | HY acceleration | Liquidity |
|---|---|---|---|---|---|---|---|
| bears | bear_1973 | top | 1973-01-11 | agrees (120.24) | UNREAD 0/5 (0 read, 2 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| bears | bear_1973 | bottom | 1974-10-03 | agrees (62.28) | UNREAD 0/5 (0 read, 2 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| bears | bear_1980 | top | 1980-11-28 | agrees (140.52) | UNREAD 0/5 (0 read, 2 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| bears | bear_1980 | bottom | 1982-08-12 | agrees (102.42) | UNREAD 0/5 (0 read, 2 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| bears | bear_1987 | top | 1987-08-25 | agrees (336.77) | UNREAD 0/5 (0 read, 2 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| bears | bear_1987 | bottom | 1987-12-04 | agrees (223.92) | UNREAD 0/5 (0 read, 2 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| bears | bear_1990 | top | 1990-07-16 | agrees (368.95) | UNREAD 1/5 (1 read, 1 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| bears | bear_1990 | bottom | 1990-10-11 | agrees (295.46) | UNREAD 0/5 (1 read, 1 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| bears | bear_2000 | top | 2000-03-24 | agrees (1,527.46) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 2 not existent) |
| bears | bear_2000 | bottom | 2002-10-09 | agrees (776.76) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 2 not existent) |
| bears | bear_2007 | top | 2007-10-09 | agrees (1,565.15) | UNREAD 1/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 1 not existent) |
| bears | bear_2007 | bottom | 2009-03-09 | agrees (676.53) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 1 not existent) |
| bears | bear_2020 | top | 2020-02-19 | agrees (3,386.15) | UNREAD 1/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read) |
| bears | bear_2020 | bottom | 2020-03-23 | agrees (2,237.40) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read) |
| bears | bear_2022 | top | 2022-01-03 | agrees (4,796.56) | UNREAD 1/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read) |
| bears | bear_2022 | bottom | 2022-10-12 | agrees (3,577.03) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read) |
| near_misses | near_1994 | control | 1994-02-02 | agrees (482.00) | UNREAD 1/5 (1 read, 1 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| near_misses | near_1994 | control | 1994-04-04 | agrees (438.92) | UNREAD 0/5 (1 read, 1 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| near_misses | near_1998 | control | 1998-07-17 | agrees (1,186.75) | UNREAD 1/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 2 not existent) |
| near_misses | near_1998 | control | 1998-10-08 | agrees (959.44) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 2 not existent) |
| near_misses | near_2011 | control | 2011-04-29 | agrees (1,363.61) | UNREAD 1/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 1 not existent) |
| near_misses | near_2011 | control | 2011-10-03 | agrees (1,099.23) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 1 not existent) |
| near_misses | near_2015 | control | 2015-05-21 | agrees (2,130.82) | UNREAD 1/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 1 not existent) |
| near_misses | near_2015 | control | 2016-02-11 | agrees (1,829.08) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 1 not existent) |
| near_misses | near_2018 | control | 2018-09-20 | agrees (2,930.75) | UNREAD 1/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read) |
| near_misses | near_2018 | control | 2018-12-24 | agrees (2,351.10) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read) |
| near_misses | near_2024 | control | 2024-07-16 | agrees (5,667.20) | UNREAD 1/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read) |
| near_misses | near_2024 | control | 2024-08-05 | agrees (5,186.33) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read) |
| pre_1970 | pre_1907 | top | 1906-01-19 | not existent | UNREAD 0/5 (0 read, 2 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| pre_1970 | pre_1907 | bottom | 1907-11-15 | not existent | UNREAD 0/5 (0 read, 2 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| pre_1970 | pre_1929 | top | 1929-09-16 | agrees (31.86) | UNREAD 0/5 (0 read, 2 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| pre_1970 | pre_1929 | bottom | 1932-06-01 | agrees (4.40) | UNREAD 0/5 (0 read, 2 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| pre_1970 | pre_1937 | top | 1937-03-10 | agrees (18.67) | UNREAD 0/5 (0 read, 2 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| pre_1970 | pre_1937 | bottom | 1938-03-31 | agrees (8.50) | UNREAD 0/5 (0 read, 2 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| pre_1970 | pre_1946 | top | 1946-05-29 | agrees (19.25) | UNREAD 0/5 (0 read, 2 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| pre_1970 | pre_1946 | bottom | 1947-05-19 | agrees (13.77) | UNREAD 0/5 (0 read, 2 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| pre_1970 | pre_1961 | top | 1961-12-12 | agrees (72.64) | UNREAD 0/5 (0 read, 2 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| pre_1970 | pre_1961 | bottom | 1962-06-26 | agrees (52.32) | UNREAD 0/5 (0 read, 2 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| false_bottoms | fb_1973_08 | false bottom | 1973-08-22 | agrees (100.53) | UNREAD 0/5 (0 read, 2 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| false_bottoms | fb_1974_02 | false bottom | 1974-02-11 | agrees (90.66) | UNREAD 0/5 (0 read, 2 not existent) | NOT EXISTENT 0/4 (0 read, 2 not existent) | UNREAD 0/5 (0 read, 2 not existent) |
| false_bottoms | fb_2000_04 | false bottom | 2000-04-14 | agrees (1,356.56) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 2 not existent) |
| false_bottoms | fb_2001_04 | false bottom | 2001-04-04 | agrees (1,103.25) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 2 not existent) |
| false_bottoms | fb_2001_09 | false bottom | 2001-09-21 | agrees (965.80) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 2 not existent) |
| false_bottoms | fb_2002_07 | false bottom | 2002-07-23 | agrees (797.70) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 2 not existent) |
| false_bottoms | fb_2008_03 | false bottom | 2008-03-10 | agrees (1,273.37) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 1 not existent) |
| false_bottoms | fb_2008_10a | false bottom | 2008-10-10 | agrees (899.22) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 1 not existent) |
| false_bottoms | fb_2008_10b | false bottom | 2008-10-27 | agrees (848.92) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 1 not existent) |
| false_bottoms | fb_2008_11 | false bottom | 2008-11-20 | agrees (752.44) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read, 1 not existent) |
| false_bottoms | fb_2022_03 | false bottom | 2022-03-08 | agrees (4,170.70) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read) |
| false_bottoms | fb_2022_06 | false bottom | 2022-06-16 | agrees (3,666.77) | UNREAD 0/5 (1 read) | UNREAD 0/4 (0 read) | UNREAD 0/5 (0 read) |

## Caveats

- Shiller's CAPE and 10-year rate are the current file's values, each month treated as knowable 3 months after it begins (session-set (A77): config/publication_lags.yaml states no lag for the shillerdata.com workbook (A64); its earnings lag the price by months (altdata/sources/shiller.py)). They are not first prints.
- The credit leg reads fred.hy_oas where the store holds it; before that it prints "pending 6i-3: Baa less the 10-year" (decision 6). 6i-3 adds DBAA and BAA.
- Part 23's ERP, the SOFR−IORB window, the TGA window and the net-liquidity "accel" are not defined there; their definitions here are session-set and named in config/tb_episodes.yaml.
- The continuous false-positive rate (Part 23's deferred item 3) is 6i-3, not this edition.
- A laptop edition reads a partial store: a reading it cannot make is printed as such, and the box's run supersedes it.
