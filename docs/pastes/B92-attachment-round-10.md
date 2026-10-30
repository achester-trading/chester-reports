# Change order — signal triage, round 10 (items 111–114; Batch 20, provisional)

| | |
|---|---|
| **File** | `docs/change-order-signal-triage-batch-20-2026-10-29.md` |
| **Status** | RULED 29 Oct 2026 (all four items, in chat); filing pending |
| **Encoding** | Batch 20 of Post-Freeze Amendment #4, provisional (Batch 19 = items 99–110). Chat numbers and filing numbers are aligned from item 111. If Batch 20 or these item numbers are already taken in the register, apply the same collision fix used for Batches 15–19 (shift up, note "chat number + n" here). SR numbers assigned at the audit that places this batch. |
| **Precedence** | Below Part 26, the Enterprise Layer order and the dated change-orders edition; equal to the other Amendment #4 batches. Amendments govern their parent items from filing. |
| **Totals** | ≈ 9.5 h of sessions (≈ 11.5 h if 111(d) applies) · no one-off by-hand work |

Every item is REPORT_OK-class: no path to DECISION_BLOCKED, no composite or T&B weight change, no new regime tag. All new feeds are public and keyless (ruling 16 Oct 2026). Nothing prints without a stored source.

---

## 1. Rulings at a glance

| Item | Short name | Ruled | Kind | Sessions |
|---|---|---|---|---|
| 111 | New free data sources: EDGAR Form 4, BIS GLI, ECB TARGET2, 13F via EDGAR | "Yes adopt" 29 Oct | ADOPT (a–c); ADOPT conditional (d) | 5.5 h (+2 h if d) |
| 112 | Silver drawdown base-rate table, typed by selloff kind | "Yes" 29 Oct | AMEND 88(b) | 1.5 h |
| 113 | Froth breadth — own per-stock bubble count, by sector | "Yes" 29 Oct | AMEND item 31 | 2.5 h |
| 114 | Crypto Fear & Greed at 35 | "Yes" 29 Oct | LOG ONLY | — |

---

## 2. Entries

### 111 · New free data sources
**Source.** An X aggregator account, "50 sites that show what billionaires buy and read" (X, 29 Oct) — *aggregator*. Reviewed at the operator's request for sources with APIs that add incremental insight.
**Thought process.** Most of the list is reading material already on the shelf (Oaktree, Bridgewater, GMO, AQR, Berkshire, JPM GTM, BIS) or data already wired (FRED, EDGAR XBRL, Damodaran). Paid or no-API sites (Trading Economics, Koyfin, Finviz, Morningstar, Portfolio Visualizer, Simply Wall St, ETFdb) fail the keyless rule. Several listed sites are front-ends for free official sources; those sources are what's worth wiring.
**Decisions.**
- **(a) ADOPT — SEC Form 4 insider transactions** (EDGAR JSON endpoints; openinsider.com is a wrapper). S&P-wide insider open-market buy/sell ratio with a 1-year percentile, plus *cluster* buying (≥ 3 insiders in one company within a week). Weekly, positioning & flows. Fills the one positioning gap not covered (corporate insiders vs funds and retail). Report rights; calibration ledger before any candidacy as a Capitulation Count (97) input. 3 h.
- **(b) ADOPT — BIS data portal (SDMX)**: Global Liquidity Indicators — USD credit to non-bank borrowers outside the US. The official complement to item 93's central-bank balance-sheet proxy. Quarterly. 1.5 h.
- **(c) ADOPT — ECB data portal (SDMX)**: TARGET2 balances (Italy, Spain debtors; Germany creditor) — the 2011–12 euro-stress tell, not on FRED. Monthly line beside SR-29 (BTP–Bund, OAT–Bund). 1 h.
- **(d) ADOPT, conditional — 13F via EDGAR** (dataroma, WhaleWisdom, 13f.info repackage it). Automates the Monthly's Pillar 5H smart-money cluster — named funds plus a 50-fund aggregate of top adds and trims. Applies only if the build chat confirms 5H is still by hand. 45-day lag: context, never timing. 2 h.
- **LOG ONLY**: congressional trades (capitoltrades; underlying House/Senate disclosures) — weak post-STOCK Act evidence, 45-day lag; ARK daily holdings CSVs — minor retail-growth sentiment read.

### 112 · Silver drawdown base-rate table — AMEND 88(b)
**Source.** A precious-metals derivatives analyst (credible), metals & mining / precious metals derivatives (LinkedIn, ~25 Oct; InProved Terminal charts) — *metals derivatives, credible*.
**Read.** Silver −53.8% from the $116.85 peak of 28 Jan 2026 (LBMA $53.96, 23 Oct; 268 days since peak), after a 3.9× rise in 12 months. 22 selloffs of ≥ 30% since 1968; of the 20 lows ≥ 3 years old, 10 doubled within 3 years, 13 within 5, 8 tripled within 5, 3 doubled within 1. Type matters more than depth: crashes inside a bull market doubled fast (1982, 2008, 2020: 0.3, 1.1, 0.4 years); blow-off tops kept falling (1980 −72% in four months, ~30 years to triple; 2011 a 4.5-year bear, −72%). At 268 days: 2026 −53.8%, 1980 −48.6%, 2011 −33.6% — tracking 1980. Six past selloffs reached today's depth: 1982 and 2008 were days from the bottom (+86–128% a year later); the other four fell another 18–40% and were flat or lower a year on.
**Thought process.** Careful work. Two caveats: the type label is assigned after the fact, and n per type is small. Silver has no base-rate table in the framework (88 covers gold and the gold/silver ratio), and the post's typing is the conditioning the gold table needs too.
**Decision.** Amend 88(b): a silver drawdown table — every ≥ 30% selloff since 1968, typed *blow-off* vs *in-bull crash* by a criterion fixed in advance (run-up multiple into the peak), with depth, time to low, and forward 1/3/5-year returns; a 2026-vs-1980/2008/2011 path overlay; the same typing applied to the gold table. Base-rate rights. 1.5 h. Voices: the precious-metals derivatives analyst, new.

### 113 · Froth breadth — AMEND item 31
**Source.** BofA Global Research Bubble Risk Indicator (as of 23 Oct 2026), via a LinkedIn relay — *sell-side, credible*, relayed.
**Read.** Rotation out of AI and tech is pushing US Healthcare and Staples toward BofA's 0.8 bubble-risk threshold; high-dividend stocks posted the largest one-week BRI rise; cloud compute high but not extreme. Froth is localised: 15 S&P stocks above 0.8 (2.2% of index weight), against 50–100 stocks and 20–40% of weight at the dot-com peak.
**Thought process.** The BRI is proprietary; the insight is not — defensives can become the crowded hiding place, a risk to Book A and the low-vol sleeve. It is the same rotation SR-19 (negative-beta share) measures from the other side. Item 31 holds the BofA peak-concentration base-rate table; missing is our own per-stock froth count.
**Decision.** Amend item 31: froth breadth — count and index weight of S&P 500 stocks in a parabolic-acceleration state, pre-registered as 6-month return z-score > 2 and positive convexity of the log-price path; by sector, so defensives froth shows. Monthly, beside SR-19. BofA BRI readings to voices only when press-sourced. Report rights; ledger before any T&B intake. 2.5 h. Voices: BofA Global Research (BRI), new.

### 114 · Crypto Fear & Greed at 35 — LOG ONLY
**Source.** An X aggregator account — *aggregator*; CMC Crypto Fear & Greed chart.
**Read.** Index fell to 35, its lowest since August, from extreme greed.
**Decision.** LOG ONLY. Crypto F&G already sits in the Monthly's Pillar 5 cross-checks; the Digital Assets froth gauge (Batch 4) and the Capitulation Count (97) carry the substance; 35 is fear, not an extreme.

---

## 3. Cross-item notes

1. **Positioning gains a corporate-insider leg** (111a) beside funds (81, 89, 13F), retail (AAII, put/call), and dealers (GEX) — one positioning & flows section.
2. **Liquidity and Europe:** 111(b) joins items 93 and 108 (MMF) in plumbing & rates; 111(c) joins SR-29.
3. **Froth:** 113 and SR-19 read the same rotation — print together. 113 also feeds the kill-switch board's Book A row (102 in Batch 19 numbering).
4. **Metals:** 112 completes the precious-metals base rates in 88(b) (gold and silver, typed).

## 4. Work order

| Tranche | When | Work | Sessions |
|---|---|---|---|
| **B** | After 8 Nov; Audit #5 (week of 23 Nov) places | 111(a) Form 4 · 111(b) BIS · 111(c) TARGET2 · 112 silver table · 113 froth breadth · 111(d) if 5H is manual | 9.5 h (+2 h) |

## 5. Verify items

| # | Item | What | Closes on |
|---|---|---|---|
| V1 | 111(d) | Is Pillar 5H still updated by hand? | Build chat confirms |
| V2 | 112 | Silver figures ($116.85 peak, −53.8%, 22 selloffs, 10/20 doubled in 3y) | Computed from LBMA history in the store |
| V3 | 113 | BofA BRI readings (15 stocks, 2.2% weight; Healthcare/Staples near 0.8) | Press source stored, else post only |

## 6. Registers

**Signal-triage register.** New entries (provisional SR numbers at the audit): 111(a) insider buy/sell ratio · 111(b) BIS GLI · 111(c) TARGET2 balances. Amendments: 88(b) (112) · item 31 (113) · Pillar 5H (111d, conditional). Source registry: EDGAR Form 4 and 13F endpoints, BIS SDMX, ECB SDMX.

**Voices.**

| Voice | Outlet | Tag | Status |
|---|---|---|---|
| A precious-metals derivatives analyst | LinkedIn (metals & mining / precious metals derivatives) | metals derivatives, credible | new |
| BofA Global Research (Bubble Risk Indicator) | BofA | sell-side, credible | new (press-sourced readings only) |
| Two X aggregator accounts · a LinkedIn relay | X / LinkedIn | aggregator | log only |

## 7. Sign-off

| Date / time (ET) | Items | Ruling as stated |
|---|---|---|
| 29 Oct 2026, 23:11 | 111(a)–(d) | "Yes adopt" |
| 29 Oct 2026, 23:23 | 112–114 | "Yes" |
| 29 Oct 2026, 23:23 | Round 10 called | "prepare one more change order cover all of [the] changes since the last summary" |

Open at filing: SR and batch numbers (audit); V1–V3.
