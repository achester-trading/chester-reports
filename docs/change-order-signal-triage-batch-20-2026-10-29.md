# Change order — Signal triage Batch 20 (items 111–114): round 10

| | |
|---|---|
| File | `docs/change-order-signal-triage-batch-20-2026-10-29.md` |
| Status | **RULED in chat** 29 Oct 2026, all four items ("Yes adopt" for 111(a)–(d), "Yes" for 112–114; §7, the sign-off); accepted for filing 29 Oct 2026, 23:30 ET (D42.16). Filed 30 Oct 2026 by paste B92 with filing amendments M1 to M5 (§0). The order as drafted in the triage chat is kept at `docs/pastes/B92-attachment-round-10.md`, people's names replaced as M3 rules. |
| Encoding | Batch 20 of Post-Freeze Amendment #4, items 111–114 as written (M1: free on this base; Batch 19 ends at 110). Register numbers are provisional, SR-73 to SR-75, placed by Audit #5. |
| Precedence | Below Part 26, the Enterprise Layer order and the dated change-orders edition; equal to the other Amendment #4 batches. Amendments govern their parent items from filing. |
| Supersedes | Nothing. |
| Totals | ≈ 9.5 h of sessions (≈ 11.5 h if 111(d) applies; see V1) · no by-hand work (M5). The triage chat's estimates. |
| Built by | Nothing yet. Tranche B after 8 Nov, placed by Audit #5. |

---

## 0. Filing amendments (paste B92, 30 Oct 2026; accepted for filing 29 Oct 2026, D42.16)

- **M1, the check.** Batch 20 and items 111–114 are free on this base (`b91-batch-19-filing` at `c8fbe39a`): no batch order, register row or index line holds them, and no remote branch files a Batch 20. Nothing is renumbered; work IDs are ST-R10.111a onward.

- **M2, references.** Each earlier reference resolved **by subject** against `docs/signal-triage-register.md`, the batch orders and the H1, J1 and L1 tables of Batches 16, 17 and 19. The order's text keeps its numbers as written; this table governs.

  | Written | Resolves to | Subject, and where it is filed |
  |---|---|---|
  | 88(b) | 88(b) | The Monthly gold chapter, which carries the base-rate table of gold bull-market drawdowns (Batch 16; SR-62). 112 amends it |
  | item 31 | 31 | Peak concentration of major bubbles, about 40% (BofA Global Investment Strategy, Chart 2; Batch 6). 113 amends it |
  | 81 | 81 | The prime-book net-selling trough ledger (Batch 16; amends 74) |
  | 89 | 89 | Crowding unwind and trend breadth (Batch 16; SR-63, SR-64) |
  | 93 ("central-bank balance-sheet proxy") | **92** | The global-liquidity-momentum proxy: Fed, ECB, BoJ and PBoC assets less the TGA and ON-RRP, amending round-5 item 17 (Batch 17, filed 92; on `a81-batch-17-filing`). The filed 93 is the negative-beta share, logged against SR-19. The subject the order names is 92's |
  | 97 | 97 | The Capitulation Count (Batch 17; SR-67) |
  | 108 | 108 | Money market funds (Batch 19, filed 108) |
  | "102 in Batch 19 numbering" | 102 | The kill-switch board (Batch 19, filed 102; SR-70) |
  | SR-19 | SR-19 | The share of S&P 500 constituents with negative beta |
  | SR-29 ("BTP–Bund, OAT–Bund") | **SR-30** | EU sovereign stress, OAT–Bund and BTP–Bund (Batch 3). The register's SR-29 is Bitcoin long-term-holder supply; the subject the order names is SR-30's. 111(c) sits beside SR-30 |
  | Pillar 5H | Pillar 5's 13F sub-cluster, **not built** | The "5H" smart-money sub-cluster is named only in the pre-build design narrative (`docs/master-narrative.md:72`, `:102`). The built Pillar 5 lists 13F aggregation as not yet sourced (`config/pillars.yaml:140-151`). See V1 |
  | Factor I, Book A, Pillar 5 cross-checks | unchanged | Their own namespaces |

  Every reference resolves. Two resolve to a different number than written (93 → 92, SR-29 → SR-30). One condition is the operator's, 111(d)'s, under V1.

- **M3, names** (D5, D38, the standing rule: no person's name in committed files). Each person's name and each X or LinkedIn handle is replaced by outlet and role, in this file and in the attachment copy:
  - 111's and 114's X accounts: "an X aggregator account";
  - 112's analyst: "a precious-metals derivatives analyst (credible)";
  - 113's relay: "a LinkedIn relay".

  BofA Global Research stays, as an institution, and InProved Terminal stays, as a product. The voices table lists outlets and tags only; X-only accounts go to the X pilot's seed list chat-side. The ruler is "the operator". Everything else is verbatim.

- **M4, sources.** 111(a) EDGAR Form 4, 111(b) BIS SDMX, 111(c) ECB SDMX and 111(d) EDGAR 13F are candidates under the 16 Oct rule. Each gets its robots and terms check when Tranche B builds it, after 8 Nov. Nothing is fetched by the filing. EDGAR calls go through `edgar.user_agent()` (`CHESTER_SEC_CONTACT`), as every sec.gov request does.

- **M5, rule 30.** No by-hand line; the order names none.

---

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
| V1 | 111(d) | Is Pillar 5H still updated by hand? | **Closed by B92 (30 Oct 2026): not built, neither by hand nor by a writer.** No module or config names a "5H"; it exists only in `docs/master-narrative.md:72` and `:102`, which planned a `fetch_13f.py` that was never written. The built Pillar 5 reads the volatility dimension and lists "13F aggregation" as not yet sourced: "none has a fetcher" (`config/pillars.yaml:140-151`). The one 13F reader is the voices scan's `pull_13f` (`altdata/sources/voices_scan.py:769`), for the firms of stored voices only (`config/voices_sources.yaml:404`, `filers_13f`), printed beside a voice in the Monthly's section 4 (`monthly_macro/stack.py:1227`). It has no named-fund cluster and no 50-fund aggregate. Whether 111(d) applies, since its condition was "by hand" and the answer is "not built", is the operator's |
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
