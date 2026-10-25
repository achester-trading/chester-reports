# B70: the Quarterly's readers, tranche 2 (crypto, credit, Thailand, and the declared gaps): build notes

*Session B, 25 Oct 2026, on branch `b70-quarterly-readers-2` from `origin/b69-quarterly-readers-1` (`6b895b9`). The second half of ruling D34 of 24 Oct 2026. Tranche 1's conventions carry over: the robots read at every pull, every request through the module's own helpers, `--dry-run`, report-only, barred from the market-state object. **Nothing here merges before the 1 Nov Monthly.** No Security Master id was needed: no reader adds an instrument to the master.*

## Base, commits and CI

- **Base:** `6b895b9`.
- **B69's CI, read once at the start:** runs 40153487365 and 40153499172 were both **queued**, after 16 minutes. Every run in the repository was queued at that read, session A's included (`a61b-feed-repair`, `library-ei-figures`), so the backlog is account-wide.
- **This branch's CI:** recorded at the end.

## The readers

| # | Reader (module) | Keys | Terms condition, and how the code honours it | Probe on the laptop, 25 Oct 2026 |
|---|---|---|---|---|
| 1 | Blockscout supply (`blockscout_supply`, source `blockscout`) | `eth.burn_daily`, `eth.issuance_daily`, `eth.net_issuance`, registered not_yet_sourced | **B67 asked the build to confirm the fields exist. They do not.** The reader is a field check. It returns PENDING with the field list while none is a burn or issuance field. If one appears, it returns STALE naming it, and its meaning is never guessed | `/api/v2/stats` 200: average_block_time, coin_price, gas_prices, gas_used_today, market_cap, network_utilization_percentage, total_addresses, total_blocks, total_transactions, transactions_today, tvl. No burn and no issuance |
| 2 | DefiLlama breadth (`llama_breadth`, source `defillama`) | `llama.tvl.category.{rwa, lending, liquid_staking, dexs, cdp, bridge, yield, derivatives, restaking, basis_trading}`, `llama.tvl.chain.{arbitrum, base, optimism, blast, scroll, linea, zksync_era, mantle, starknet}` | **Stored, never republished,** in every key's description. CEX balances are excluded. **The AERO convention** (D29 (3)) is in code: `MERGED` records each merged child with its parent, date and category at the merge; a child later listed under another category is a named, labelled break (`breaks`) | `/protocols` 200 (8,820 protocols; aerodrome-v1 and aerodrome-slipstream under `parent#aero-protocol`, Dexs, so no break); `/v2/chains` 200 |
| 3 | iShares holdings (`ishares_holdings`, source `ishares_trusts`) | `ishares.{ibit,etha}.{aum,shares}` | **Level, not flow,** in every key's description and every Quarterly label. Farside's flows stay the flow source, and the float stays a gap. The same key-fact parser and browser-shaped project identity as `ishares_trusts` | IBIT (333011) and ETHA (337614) pages 200. ETHA: AUM 7,815,585,782, shares 144,293,284, as of 23 Oct |
| 4 | BDC facts (`edgar_bdc`, source `sec_edgar`) | `edgar.bdc.{arcc,fsk,bxsl,obdc,main}.{investments_fv,nav_per_share}`; `.nonaccrual_fv` registered not_yet_sourced | The SEC contact, `CHESTER_SEC_CONTACT`, from the environment; PENDING without it. **The Brookfield blocklist** at write time refuses OCSL (Oaktree's BDC, tier 4), which is not in NAMES. The CIK comes from `company_tickers.json` | **Not probed:** the SEC contact cannot be read in this session (environment reads are denied, `.env` is never read). The parser is held on a fixture filing |
| 5 | Thailand's current account | `thai.current_account_usd`, registered not_yet_sourced | **Not built** (needs-you 1) | the page B67 checked (reportID 650) is "Thai Direct Investment Abroad", not the current account; the BoT publishes no index of its report ids; its API needs `BOT_API_KEY` and has no verified balance-of-payments endpoint here |
| 6 | The Commerce ministry's construction index | `thai.construction_materials_index`, registered not_yet_sourced | a candidate, "re-check at the next quarterly scan" | HTTP 500 at B67's check; not retried |

**Where each prints** (`config/quarterly_chapters.yaml`):
- **the crypto chapter:** the RWA TVL, IBIT's and ETHA's net assets beside "ETF flows read against float", and RWA plus three layer-2 chains in the deck items. The ETF AUM rows are now shares outstanding, labelled level, not flow. ETH burn prints "not tracked" with Blockscout's reason;
- **credit:** the five BDCs' investments at fair value, ARCC's and FSK's NAV per share, and non-accruals as "not tracked: no standard us-gaap tag". The listed-BDC discount reads "the NAVs are stored; the prices are pending D33";
- **Thailand:** the current account and the construction index, each with its reason.

**One placement not wired:** the Digital Assets addendum's own breadth line, beside item 78's active-protocol count. The DefiLlama rows print in the Quarterly's crypto chapter, and the addendum's page is unchanged.

## The declared gaps (registry entries `status_extra: not_yet_sourced`, each with its reason and the check date; refused sources registered `status: refused`)

| Row | Key | Reason, as printed |
|---|---|---|
| PJM capacity auctions | `pjm.capacity_auction` (source `pjm`) | "not tracked: PJM's terms confer no licence (B67, 25 Oct 2026)" |
| LBNL interconnection queues | `lbnl.interconnection_queue` (`lbnl`) | "LBNL's queue data answered HTTP 403" |
| Taiwan export orders | `moea.export_orders` (`moea_tw`) | "MOEA answered HTTP 403" |
| TSMC foundry revenue | `tsmc.monthly_revenue` (`tsmc`) | "TSMC's terms allow personal viewing only" |
| USDC and USDT attestations | `circle.usdc_reserves`, `tether.usdt_reserves` | "Circle's terms could not be found and Tether's robots.txt disallows its file" |
| GDX, SIL | `yahoo_pending.gdx`, `.sil` | "pending D33: no new yfinance symbols" (the miners' falsification test) |
| Corn, wheat, soybean fronts | `yahoo_pending.{corn,wheat,soybeans}_front` | "pending D33: no new yfinance symbols" |
| ETH burn and issuance | `eth.*` | "not tracked: Blockscout's public stats carry no burn or issuance field" |
| BDC non-accruals | `edgar.bdc.*.nonaccrual_fv` | "not tracked: no standard us-gaap tag carries a BDC's non-accruals" |
| Thailand's current account | `thai.current_account_usd` | "the BoT's public report pages have no index and its API endpoint was not verified" |
| The construction index | `thai.construction_materials_index` | "a candidate ... re-check at the next quarterly scan" |

## The gate

`tools/validate_quarterly_readers_2.py` passes 30 to 0, on fixtures only. Its groups:
- A: the parsers;
- B: the Blockscout field check (absent is PENDING and writes nothing; a field that appears is STALE, never guessed);
- C: DefiLlama's no-republish note on every key, and the AERO convention (no break for AERO's children; a named break for a child that moves category);
- D: iShares' level, not flow, on keys and labels;
- E: EDGAR on a fixture filing (instants, the later filing wins, NAV in USD/shares), OCSL refused, PENDING without the contact, non-accruals not_yet_sourced;
- F: every declared gap registered with its reason and date, printing where it would have printed, and the six refused sources registered refused with their read date;
- G: registered, barred (a new `market_state_barred` entry citing D34), no regime import;
- H: no address;
- I: the external roster, static KEYS and the catalogue.

It is registered in the Makefile after tranche 1's gate. **CLAUDE.md's count line is recounted to one hundred and forty-one code gates (one hundred and thirty-eight Python, three shell)**, from B69's 140 plus this one.

Run locally:
- **the new gate:** 30 passed, 0 failed;
- **`validate_official_sources`:** 368 passed, 0 failed. Its outage test reaches the four new readers through their own helpers and sends nothing;
- **`validate_digital_addendum`:** 98 passed, 0 failed;
- **`check_registry`:** OK;
- **`check_library`:** 0 failures, 0 warnings;
- **`validate_audit_3a`:** 88 passed, 0 failed (41 external writers);
- **`validate_quarterly_readers_1`:** 48 passed, 0 failed;
- **`validate_quarterly_stack`:** passed.

**What else moved:**
- `altdata/feeds.py` EXTERNAL_WRITERS (37 to 41);
- `metrics_registry.yaml`: 54 entries, their families and the barred entry;
- `source_registry.yaml`: six refused sources;
- `config/catalogue_commands.yaml`: four lines;
- CLAUDE.md: the roster count and a paragraph;
- the architecture document's store box (41 external writers).

## Box commands, for chain-8's box sheet (the operator's; dry runs first)

```
python -m altdata.sources.ishares_holdings --dry-run
python -m altdata.sources.llama_breadth --dry-run
python -m altdata.sources.edgar_bdc --dry-run        # needs CHESTER_SEC_CONTACT in .env
python -m altdata.sources.blockscout_supply --dry-run  # expect PENDING: no supply field
```

None of the four serves history:
- iShares and DefiLlama are daily snapshots from the first real pull;
- `edgar_bdc`'s first real pull takes each BDC's newest 20 quarters from the concept files;
- Blockscout writes nothing until a supply field exists and its parser is ruled.

On the box's first EDGAR read, the session that reads the log should record which fair-value tag each BDC resolved, and whether any filing carries a non-accrual tag (needs-you 2).

## Needs you (five)

1. **Thailand's current account.** Name the BoT statistics report id for the balance of payments, or the BoT API endpoint the operator's key can read. The reader is then a short paste. Until then it prints "not tracked" with the reason.
2. **BDC non-accruals.** No standard us-gaap tag carries them. Either a box session reads the five BDCs' filings and names each company's extension tag, ruled into `NONACCRUAL_TAGS`, or non-accruals stay a listed gap.
3. **The BDC names.** ARCC, FSK, BXSL, OBDC and MAIN were chosen because the 6i brief names none: five of the largest listed BDCs, OCSL excluded by the blocklist. Confirm or change the list.
4. **The Digital Assets addendum's breadth line** is not wired. The DefiLlama rows print in the Quarterly only. Add them to the addendum's page beside item 78, or leave the addendum as it is?
5. **The CI queue.** Every run in the repository was queued at this paste's start, B69's for 16 minutes, and session A's too. If it is an account limit, merges will wait on results that are hours behind.

**CI.** At the one read after the push of `6bd2d53`, no run was listed yet, so there is no run id. The next paste that touches this branch reads it once.
