# The Audit #5 placement pack (week of 23 Nov 2026)

Prepared by B108, 2 Nov 2026, on `b95-batch-21-filing` (tip `8d70126b`). **Nothing
here is placed, renumbered or ruled.** The pack lays out every provisional
signal-register row filed since Audit #4: SR-60 to SR-76, Batches 16 to 21. It gives
what carries each row, the numbering collision with the Doctrine #2 pack's Table 5.1
(D2-80), and each tranche against the merge calendar, so the audit can place them in
one read.

**Sources.** All are read with `git show <branch>:<path>`, never checked out:
- the register on `b95-batch-21-filing`, which carries SR-60 to SR-64 and SR-68 to
  SR-76;
- the register on `a81-batch-17-filing` and on `b86-chain-8-assembly`, which carry
  SR-65 to SR-67;
- the six batch orders;
- the rulings records `docs/briefs/rulings-2026-10-25-27.md` and
  `rulings-2026-10-28-31.md` (on b95);
- the Doctrine #2 pack's Table 5.1 (on `b96-doctrine-2-pack-refresh`);
- A99's merge-week script (`docs/briefs/a99-merge-week-script.md`, on
  `a99-merge-week-rehearsal`).

Every ruling is the operator's.

## Part 1. The rows

**The rows per batch:**

| Batch | Rows | SR numbers |
|---|---|---|
| 16 | 5 | SR-60 to SR-64 |
| 17 | 3 | SR-65 to SR-67 |
| 18 | 1 | SR-68 |
| 19 | 4 | SR-69 to SR-72 |
| 20 | 3 | SR-73 to SR-75 |
| 21 | 1 | SR-76 |

That is **17 rows** in all. Every row's status as filed is "provisional, placed by
Audit #5".

**Written numbers.** Batch 16 was written as items 72–84 and filed as 79–91 (H1,
plus 7). Batch 19 was written as 98–109 and filed as 99–110 (L1, plus 1). Batches
17, 18, 20 and 21 were filed as written (J1, K1, M1, N1).

| SR | Batch | Filed item (written) | Subject | Rights as filed | Tranche and its condition | What carries it | Depends on | By-hand line | Accepted by |
|---|---|---|---|---|---|---|---|---|---|
| 60 | 16 | 80(b) with 90 (73(b) with 83) | The midterm event row and the midterm base-rate table | Base-rate row (no trigger) | Time-critical: merged Wed 28 Oct, before the dry run (D37) | **Built, on main** (A78, PR #43): `tools/calibration/midterm_base_rate.py`, `docs/ledgers/midterm-base-rate-2026-10-26.md`, the Weekly's Ahead row (`config/weekly_ahead.yaml`) | the stored prediction markets for the odds ("odds not stored" without them) | none | D37, 26 Oct |
| 61 | 16 | 83(b) (76(b)) | The hyperscalers' server and network useful-life watch, from 10-Q and 10-K | Narrow flag | B | Order only | EDGAR filings | The quarterly read is a listed gap (H3) | D37 |
| 62 | 16 | 88 (81) | Gold as standing coverage: the Weekly gold block, the Monthly gold chapter, GLD in the nightly exposure files, the close on exception | Report only | A for 88(a), (c) and (d), merging with chain-8 for the 8 Nov Weekly (D37); B for 88(b) | **Built for Tranche A, on chain-8** (`b86-chain-8-assembly`: `daily_cascade/gold_block.py`, `altdata/gold_13f.py`, `altdata/gold_attribution.py`, `altdata/gold_event.py`, their configs, `config/gold_official_bid.yaml`); 88(b) order only | chain-8's merge (A99 step 1) | **Recurring:** the weekly official-bid line, the one allowed (H3) | D37 |
| 63 | 16 | 89(a) (82(a)) | The crowding-unwind gauge: the momentum factor's z-score and the count of held pair spreads beyond 3σ | Report only; T&B intake after a calibration ledger | B | Order only | a calibration ledger before any T&B intake | none | D37 |
| 64 | 16 | 89(b) (82(b)) | Trend-signal breadth over the held markets, from stored keys only (H4) | Report only; T&B intake after a calibration ledger | A, merging with chain-8 (D37) | **Built, on chain-8** (`altdata/trend_breadth.py`, `config/trend_breadth.yaml`) | chain-8's merge; D33 (no new yfinance symbols) | none | D37 |
| 65 | 17 | 92 | The global-liquidity-momentum proxy: Fed + ECB + BoJ + PBoC total assets in dollars, less TGA and ON-RRP; its 6-month rate of change z-scored on 10 years against SPX YoY | Report only | B | Order only. The filing is on `a81-batch-17-filing`, which chain-8 carries | the PBoC leg from the IMF's keyless IFS, else "PBoC not tracked" (J3) | none | D39, 26 Oct |
| 66 | 17 | 95 | Moody's Analytics "What Could Go Wrong" matrix mapped onto the Twenty-Five, with its month-to-month status diff | Voices and disagreement | B | Order only | — | **Recurring:** the monthly diff, allowed (J2, D39) | D39 |
| 67 | 17 | 97 | The Capitulation Count: one point per family, beside the T&B verdict and never inside it; its three feeds (97(b)) and the SMH divergence line (97(c), J5) | Report only; T&B intake as a bottom-side candidate tell only after its calibration ledger | B (leads); 97(a)–(c) merging after 8 Nov (D39) | **Built, branch-only** (`b79-capitulation-count`: `altdata/capitulation_count.py`, `daily_cascade/capitulation_block.py`, `config/capitulation_count.yaml`) | ICI flows, a listed gap: "k of 4 scorable families" (J4); SMH, not SOXX (J5, D33) | none | D39 |
| 68 | 18 | 98 | The 23-hour equity session: bars tagged night, pre, regular or post from their own UTC timestamp (98(a)); SPY and QQQ overnight in the 07:00 anchor and the 21:30 note (98(b)); night bars from IBKR under the price migration, else a gap (98(c)) | Report only | After Doctrine #2, before the first night (target 6 Dec 2026); 98(c) inside the price migration | Order only. The filing is on `b81-batch-18-overnight-session` | D2-75; the price migration (`a96-price-migration-fred`, D2-73) | none (K4) | D42.5, 28 Oct |
| 69 | 19 | 100 (99) | The premium sleeve: XSP or SPX put spreads, 30–45 DTE, short strike about 16–20 delta, 50% take-profit, the 21-DTE close; gated by VRP, IV rank and the dealer read; benchmark Cboe's PUT index | Paper only (Alpha Lab, family `KS options`); promotion only through RAS (91(b)) and the cost cliff (91(c)) | C, after 99's registry | **Built, branch-only and disabled** (`b99-premium-sleeve`: `alpha/engines/premium_sleeve.py`, `config/alpha_premium_sleeve.yaml`, the P-1 roster; the engine `enabled: false`), on `b98-ks-family-registry` | 99's registry (b98); the count and T&B verdict, not stored (the engine stands down); the PUT index, not stored (D45) | none | D42.15, 29 Oct |
| 70 | 19 | 102 (101) | The kill-switch board: one row per engine and book, lives in, dies in, a pre-registered early-warning threshold, green, amber or red, with its ledger | Report only; red lights are pause candidates for 91(d), the pause the operator's | C (last) | Order only | the engines and books it lists | none | D42.15 |
| 71 | 19 | 104 (103) | The global AI-complex panel: STAR50, CSI 300, KOSPI, TAIEX, SOX and NDX, drawdown and 20-day correlation to SOX, with a lead-lag ledger | Report only | B | Order only | a market with no stored key is a listed gap (L4; D33) | none | D42.15 |
| 72 | 19 | 107 (106) | The intraday dealer read at 09:15, 10:30, the 12:30 alert and 15:00 (107(a)); the 0DTE volume-weighted gamma test with its pre-registered ledger (107(b)) | Report only; 107(b) a test | B | Order only | the captures; no new subscription (107(c)) | none | D42.15 |
| 73 | 20 | 111(a) | The insider buy/sell ratio from SEC Form 4, with a 1-year percentile and cluster buying | Report only; a calibration ledger before any candidacy as a Capitulation Count (97) input | B | Order only | EDGAR (`CHESTER_SEC_CONTACT`) | none (M5) | D42.16, 29 Oct |
| 74 | 20 | 111(b) | The BIS Global Liquidity Indicators, quarterly, beside the global-liquidity proxy and 108 | Report only | B | Order only | BIS SDMX; filed 92 (SR-65) | none (M5) | D42.16 |
| 75 | 20 | 111(c) | TARGET2 balances (Italy and Spain debtors, Germany creditor), monthly, beside SR-30's OAT–Bund and BTP–Bund | Report only | B | Order only | ECB SDMX | none (M5) | D42.16 |
| 76 | 21 | 115 | The evening X read: the evening triage pulled into the box's x-triage inbox the same evening, and an "X after hours" block in the 21:30 evening note (Sun–Thu) | Rumour-track (item 50's rights: attention and rumour tracking, never measurement) | B, after 8 Nov (D47) | Order only on the box. The chat side is planned and paused: the Grok evening automation waits on a third slot (the register, B102; D56) | the Grok evening digest; the sweep's evening pull | none (N3: the automation and the triage run themselves) | D47, 30 Oct |

**Where two documents disagree** (B108 found five; settled by B115, 2 Nov 2026).

The rule (B115):
- **A number** the filing assigned: the order's own section-0 amendment table
  decides.
- **A status:** the branch state decides.
- **A ruling or its wording:** nothing changes; both texts are quoted, and the
  operator rules at Audit #5.

The check found no sixth disagreement: each order's provisional SR range matches
the register's headings.

| # | Disagreement | Class | Deciding source | Fix |
|---|---|---|---|---|
| 1 | **SR-74.** Batch 20's order: "item 93's central-bank balance-sheet proxy"; the register: "the global-liquidity-momentum proxy (filed 92; the order's "93", M2)" | Number | Batch 20's M2 table: "93 ("central-bank balance-sheet proxy") → **92**", and "The order's text keeps its numbers as written; this table governs" | **None needed.** The register already follows M2 and names the order's word. The order's text is kept as written, by M2's own rule |
| 2 | **SR-75.** Batch 20's order: "Monthly line beside SR-29 (BTP–Bund, OAT–Bund)"; the register: "beside SR-30's OAT–Bund and BTP–Bund (the order's "SR-29", M2)" | Number | Batch 20's M2 table: "SR-29 ("BTP–Bund, OAT–Bund") → **SR-30**" | **None needed**, as in row 1 |
| 3 | **SR-60's status.** The register: "table built, branch a78-batch-16-midterm"; `a78-batch-16-midterm` merged to main on 28 Oct 2026 (PR #43, `8166d430`) | Status | The branch state: `a78-batch-16-midterm`'s tip is an ancestor of `origin/main` | **Corrected on this branch.** The register's SR-60 status now reads "table built, on main since 28 Oct 2026 (PR #43)", with "corrected 2 Nov 2026 to match the branch state (B115)". main's register still carries the old text until this branch merges |
| 4 | **SR-65 to SR-67.** b95's register cites "Batch 17's SR-65 to SR-67 (paste A81, on its unmerged branch)" and holds no rows for them | Status | The branch state: 3 rows on `a81-batch-17-filing` and 3 on `b86-chain-8-assembly` (chain-8); 0 on main and 0 here; `a81-batch-17-filing` is not merged | **None needed.** The citation is accurate as written. The rows reach this register through chain-8 at A99's step 5 ("both (65–67, then 68)"); adding them here would duplicate chain-8's |
| 5 | **SR-60 to SR-76 against Table 5.1.** The batches filed SR-60 to SR-76 as provisional; the Doctrine #2 pack's Table 5.1 drafts "SR-60 to SR-93 for items 45–78" (D2-22) | Ruling | D2-80, unruled: the numbering is the audit's to place | **Left for the operator,** at Audit #5. Both texts are quoted here, and Part 2 drafts the three options |

## Part 2. The collision (D2-80), the three options drafted

Table 5.1 (D2-22, on b96) gives items 45–78 the numbers SR-60 to SR-93, 34 rows.
The batches filed since have used SR-60 to SR-76, 17 rows. D2-80's options are below,
each drafted so the audit can accept it whole. The pack's own D2-80 note is the only
recommendation: the sitting rules.

### Option (a): items 45–78 take SR-77 onward (34 rows renumbered; the batches keep theirs)

| Item | Table 5.1 | New |
|---|---|---|
| 45 | SR-60 | SR-77 |
| 46 | SR-61 | SR-78 |
| 47 | SR-62 | SR-79 |
| 48 | SR-63 | SR-80 |
| 49 | SR-64 | SR-81 |
| 50 | SR-65 | SR-82 |
| 51 | SR-66 | SR-83 |
| 52 | SR-67 | SR-84 |
| 53 | SR-68 | SR-85 |
| 54 | SR-69 | SR-86 |
| 55 | SR-70 | SR-87 |
| 56 | SR-71 | SR-88 |
| 57 | SR-72 | SR-89 |
| 58 | SR-73 | SR-90 |
| 59 | SR-74 | SR-91 |
| 60 | SR-75 | SR-92 |
| 61 | SR-76 | SR-93 |
| 62 | SR-77 | SR-94 |
| 63 | SR-78 | SR-95 |
| 64 | SR-79 | SR-96 |
| 65 | SR-80 | SR-97 |
| 66 | SR-81 | SR-98 |
| 67 | SR-82 | SR-99 |
| 68 | SR-83 | SR-100 |
| 69 | SR-84 | SR-101 |
| 70 | SR-85 | SR-102 |
| 71 | SR-86 | SR-103 |
| 72 | SR-87 | SR-104 |
| 73 | SR-88 | SR-105 |
| 74 | SR-89 | SR-106 |
| 75 | SR-90 | SR-107 |
| 76 | SR-91 | SR-108 |
| 77 | SR-92 | SR-109 |
| 78 | SR-93 | SR-110 |

**Files that change:** one, the pack on `b96-doctrine-2-pack-refresh`, its Table 5.1
and its text. Items 45–78 have no register rows yet, so no batch order or register
changes.

### Option (b): the batches' provisional rows renumber after items 45–78 (17 rows renumbered; Table 5.1 stands)

| Batch row | Now | New |
|---|---|---|
| 80(b) with 90 | SR-60 | SR-94 |
| 83(b) | SR-61 | SR-95 |
| 88 | SR-62 | SR-96 |
| 89(a) | SR-63 | SR-97 |
| 89(b) | SR-64 | SR-98 |
| 92 | SR-65 | SR-99 |
| 95 | SR-66 | SR-100 |
| 97 | SR-67 | SR-101 |
| 98 | SR-68 | SR-102 |
| 100 | SR-69 | SR-103 |
| 102 | SR-70 | SR-104 |
| 104 | SR-71 | SR-105 |
| 107 | SR-72 | SR-106 |
| 111(a) | SR-73 | SR-107 |
| 111(b) | SR-74 | SR-108 |
| 111(c) | SR-75 | SR-109 |
| 115 | SR-76 | SR-110 |

**Files that change, by branch** (the register and every order that cites an SR-6x
or SR-7x number):

| Branch | Files |
|---|---|
| main | 1 (the register) |
| `a81-batch-17-filing` | 2 |
| `b81-batch-18-overnight-session` | 2 |
| `b91-batch-19-filing` | 3 |
| `b92-batch-20-filing` | 4 |
| `b95-batch-21-filing` | 5 |
| `b86-chain-8-assembly` | 3 |

Code and notes that cite the numbers would follow; they are not counted here.

### Option (c): both wait for Audit #5, which places every provisional row in the order it chooses

The batches' rows in filing order, with no numbers:
1. 80(b) with 90
2. 83(b)
3. 88
4. 89(a)
5. 89(b)
6. 92
7. 95
8. 97
9. 98
10. 100
11. 102
12. 104
13. 107
14. 111(a)
15. 111(b)
16. 111(c)
17. 115

Then items 45–78 in item order: 34 rows. **Files that change:** every file of option
(b), and the pack, once the audit assigns.

### The cross-references that would move

`SR-6x` and `SR-7x` are counted with `grep -o` on the orders, the registers and the
pack:

| Branch | File | SR-6x | SR-7x | SR-8x and SR-9x |
|---|---|---|---|---|
| main | register | 2 | 0 | 0 |
| a81-batch-17-filing | Batch 17 order | 5 | 0 | 0 |
| a81-batch-17-filing | register | 7 | 0 | 0 |
| b81-batch-18-overnight-session | Batch 18 order | 10 | 0 | 0 |
| b81-batch-18-overnight-session | register | 7 | 0 | 0 |
| b91-batch-19-filing | Batch 18 order | 10 | 0 | 0 |
| b91-batch-19-filing | Batch 19 order | 12 | 4 | 0 |
| b91-batch-19-filing | register | 13 | 1 | 0 |
| b92-batch-20-filing | Batch 18 order | 10 | 0 | 0 |
| b92-batch-20-filing | Batch 19 order | 12 | 4 | 0 |
| b92-batch-20-filing | Batch 20 order | 4 | 3 | 0 |
| b92-batch-20-filing | register | 13 | 4 | 0 |
| b95-batch-21-filing | Batch 18 order | 10 | 0 | 0 |
| b95-batch-21-filing | Batch 19 order | 12 | 4 | 0 |
| b95-batch-21-filing | Batch 20 order | 4 | 3 | 0 |
| b95-batch-21-filing | Batch 21 order | 0 | 2 | 0 |
| b95-batch-21-filing | register | 13 | 6 | 0 |
| b86-chain-8-assembly | Batch 17 order | 5 | 0 | 0 |
| b86-chain-8-assembly | register | 7 | 0 | 0 |
| b86-chain-8-assembly | the pack (A70's edition) | 12 | 10 | 16 |
| b96-doctrine-2-pack-refresh | the pack | 24 | 14 | 17 |
| b96-doctrine-2-pack-refresh | register | 2 | 0 | 0 |

The Batch 16 order carries no SR number: the register assigned them at filing. On a
merged main, after A99's steps 1 to 13, the counts are b95's for the orders and the
register, plus the pack's.

## Part 3. The tranches against the calendar

A99's sheet (`docs/briefs/a99-merge-week-script.md`, Tue 3 and Wed 4 Nov) sets the
order: chain-7 and chain-8 at step 1, b81 at 5, b91 at 11, b92 at 12, b95 at 13, a92
at 14 and a96 at 17.

| SR | Tranche | The merge it waits for | In the 3 Nov sheet? | On 23 Nov it can be placed as |
|---|---|---|---|---|
| 60 | (time-critical) | none: on main since 28 Oct | — | **merged** |
| 61 | B | its build (not started) | — | order only |
| 62 | A for 88(a), (c), (d); B for 88(b) | chain-8 | **yes, step 1** | **merged** (Tranche A); order only (88(b)) |
| 63 | B | its build | — | order only |
| 64 | A | chain-8 | **yes, step 1** | **merged** |
| 65 | B | its build; the filing rides chain-8 | the filing yes (step 1) | order only |
| 66 | B | its build | the filing yes (step 1) | order only |
| 67 | B (leads) | `b79-capitulation-count`, "merging after 8 Nov" (D39) | **no** | built and branch-only, unless b79 merges by 23 Nov |
| 68 | after Doctrine #2 | its build; 98(c) inside the price migration (a96) | the filing yes (step 5); a96 yes (step 17) | order only (target 6 Dec) |
| 69 | C, after 99's registry | `b98-ks-family-registry` and `b99-premium-sleeve`, then the Alpha Lab queue | **no** (both after the rehearsal) | built, disabled, branch-only |
| 70 | C (last) | its build, after the Alpha Lab queue | the filing yes (step 11) | order only |
| 71 | B | its build | the filing yes (step 11) | order only |
| 72 | B | its build | the filing yes (step 11) | order only |
| 73 | B | its build | the filing yes (step 12) | order only |
| 74 | B | its build | the filing yes (step 12) | order only |
| 75 | B | its build | the filing yes (step 12) | order only |
| 76 | B, after 8 Nov | its box build, and the Grok evening slot (D56) | the filing yes (step 13) | order only |

**The "Now" items.**
- **Filed 105(a)**, the EM shock-screen audit: read 1 Nov 2026, and its amendment
  drafted in `docs/briefs/b91-notes.md` Part 3 (B105). It is pending the operator's
  ruling, and is D2-90 in the Doctrine #2 pack.
- **SR-60**, the time-critical item of Batch 16, is already merged.
- **No other row is marked Now.**
