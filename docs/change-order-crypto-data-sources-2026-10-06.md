# Change Order — Crypto data sources: the 40-site list, rulings

| | |
|---|---|
| Status | **Ruled 2026-10-06, 03:16–03:30 ET, in chat, one decision at a time:** D-1 No · D-2 drop Binance · D-3 Farside · D-4 DVOL now, GEX with EL-12 · D-5 build now · D-6 yes, two queries · D-7 Batch 4 of Amendment #4, Audit #4 places it · D-8 yes with fallback. Each ruling is applied in §2, §3, §5 and §6 below. Register numbers are assigned at Audit #4 (14–15 Oct), continuing after the GTM batch. |
| Filed | Filed 6 Oct 2026. Register numbers after SR-36 are provisional until Audit #4 (14–15 Oct) assigns them in filing order (GTM batch, crypto Thread D, batch 4); Audit #4 also verifies the SR-30 crisis level (~190bp) and the r2 base-rate levels and places every tranche. Nothing from this order enters the October calendar until then. |
| Source | A circulating list of forty free crypto data sites ("who's buying, who's dumping, who's about to unlock", checked 4 Oct 2026), posted by Ari 6 Oct 2026, with the question: which have an API or can be scraped, and which belong in the daily, weekly or monthly reporting. Five sources not on the list are added because they serve the framework better than most of it. |
| Owner | Ari Chester |
| Binding on | Claude Code sessions building the crypto feed tranches (§6) and the blocks they feed (T2 Weekly, T3 Monthly, the daily anchors after Track D's preconditions) |
| Precedence | Below Part 26, the change orders, Amendments #3–#5, the reporting-stack brief and the metric-lenses brief. Everything here is REPORT_OK-class data with discovery, scorecard or narrow-flag rights; no series enters a composite or a T&B overlay without a passed offline gate and a dated ledger (§1.3 of the consolidated signal-triage order). Thread **D** of the register. |
| Relation to SR-10 | The Pearl mechanism-watch build (ST-13…ST-15) already specifies a CoinGecko fetcher and the point-in-time conventions for crypto series; this order reuses that scaffolding and adds sources beside it. Nothing here changes MW-1…MW-10. |

## §1 What the list is, and what it is for

The list is written for memecoin traders. Three of its six sections — whale and wallet tracking, memecoin safety checks, portfolio tools — answer questions the framework never asks (which wallet bought what, whether a token launched last week is a rug). The value sits in the "where the money goes" and "leverage and liquidations" sections plus two explorers: protocol fees and stablecoin supply, ETF flows, funding and open interest, Bitcoin and Ethereum network state. Those map onto the stack's **positioning & flows**, **mechanics**, **what's priced** and the Monthly's **Factor V** scorecard. Twelve of the forty are adopted; five sources from outside the list are added; the rest are logged with the reason.

## §2 Rulings on the forty, and the five additions

Access and cost as checked 6 Oct 2026; endpoint detail in Appendix A. "Free" means no key or a free key. Hours are session estimates and are summed in §6.

| ID | Site | Access | Cost | Ruling | What is pulled | Cadence → section | Hours |
|---|---|---|---|---|---|---|---|
| DS-1 | Arkham | Intelligence API is enterprise-only; site is JS/auth | Paid | **REJECT** — wallet-level alpha, no framework home | — | — | 0 |
| DS-2 | Nansen | API, credit-priced | Paid | **REJECT** — same | — | — | 0 |
| DS-3 | DeBank | Cloud API, pay-per-unit | Paid | **REJECT** — per-wallet portfolios | — | — | 0 |
| DS-4 | Cielo | API, small free tier | Freemium | **REJECT** — wallet alerts | — | — | 0 |
| DS-5 | Whale Alert | API exists; pricing page unreachable 6 Oct, free tier unverified | Unverified | **LOG** — large exchange-inflow bursts could serve as an attention item; revisit only if a crypto exchange-flow line is wanted later | — | — | 0 |
| DS-6 | Lookonchain | X account, no API | — | **REJECT** | — | — | 0 |
| DS-7 | Kolscan | No API; memecoin KOL trades | — | **REJECT** | — | — | 0 |
| DS-8 | fomo.family | No API | — | **REJECT** | — | — | 0 |
| DS-9 | GMGN | Unofficial endpoints; Solana memecoins | — | **REJECT** | — | — | 0 |
| DS-10 | Solscan | Pro API, keyed, small free tier | Freemium | **LOG** — fine explorer; no Solana on-chain thesis to serve | — | — | 0 |
| DS-11 | Etherscan | Free API key (5/s, 100k/day), V2 unified | Free | **ADOPT** | `ethsupply2` (supply, staked, burnt), gas oracle | Monthly → mechanics (ETH supply/burn); makes DS-37 redundant | 1 |
| DS-12 | RugCheck | Free API | Free | **REJECT** — memecoin safety | — | — | 0 |
| DS-13 | Bubblemaps | Partner API | Paid | **REJECT** | — | — | 0 |
| DS-14 | InsightX | No public API | — | **REJECT** | — | — | 0 |
| DS-15 | SolSniffer | API, paid | Paid | **REJECT** | — | — | 0 |
| DS-16 | TokenSniffer | API, paid | Paid | **REJECT** | — | — | 0 |
| DS-17 | DexScreener | Open API, no key (300/min) | Free | **ADOPT as backup** to DS-19 for pair lookups; no series of its own | search / pair endpoints on demand | — | 0.5 |
| DS-18 | Birdeye | Keyed API, free compute units | Freemium | **REJECT** — Solana-only | — | — | 0 |
| DS-19 | GeckoTerminal | Open API, no key (30/min) | Free | **ADOPT** (D-5 ruled build now, 6 Oct) | new-pool count and trending-pool 24h volume on Solana and Base → the froth gauge (§3, S-5); sampling starts the day the fetcher deploys, since no backfill exists | Weekly → what doesn't fit (unscored until the gate); C&C intake queue behind SR-19 after the gate | 3 |
| DS-20 | Tokenomist | API enterprise-only; JS site | Paid | **REJECT** — DS-21 covers the use | — | — | 0 |
| DS-21 | DefiLlama Unlocks | Page free; `/emissions` API is Pro ($300/mo) | Free (page) | **ADOPT by hand** — unlock schedules for the watch names hardcoded into the Security Master from project docs (static); page checked quarterly | `secmaster.unlock_schedule` | Monthly → the book (next-90-day unlock table) | 0 (+1 by hand) |
| DS-22 | CryptoRank | Keyed API, free tier thin | Freemium | **REJECT** — DS-29's `/raises` covers VC funding | — | — | 0 |
| DS-23 | DropsTab | No public API | — | **REJECT** | — | — | 0 |
| DS-24 | CoinGlass (Hyperliquid page) | API only; **no free tier**; site scraping prohibited by its terms | $29/mo Hobbyist (80+ endpoints, 30/min, personal use) | **REJECT** — D-1 ruled No, 6 Oct: funding and OI come from the free venues (DS-42, DS-43); no liquidation series in this order | — | — | 0 |
| DS-25 | Hyperliquid leaderboard | Public JSON (unofficial) | Free | **LOG** — top-trader PnL is noise for the framework | — | — | 0 |
| DS-26 | CoinGlass liquidation heatmap | Visual; in the API as liquidation data | with DS-24 | **REJECT** with DS-24 (D-1) | — | — | 0 |
| DS-27 | Velo | API, paid tiers | Paid | **LOG** — best derivatives data on the list; DS-24 + DS-42 cover ~80% free; revisit at the 6b feed purchase | — | — | 0 |
| DS-28 | CoinAnk | API, paid | Paid | **REJECT** — exchange APIs direct | — | — | 0 |
| DS-29 | DefiLlama | Open REST API, no key | Free | **ADOPT** — highest value on the list | stablecoin supply total and by chain; fees and revenue by protocol for the watch names; chain TVL; DEX volume; perps OI overview; `/raises` | Weekly → positioning & flows; Monthly → Factor V scorecard rows (AMEND SR-20), watch-name fundamentals, VC raises as a slow-layer cycle gauge | 3 |
| DS-30 | Token Terminal | API enterprise-only | Paid | **REJECT** — DS-29 covers fees | — | — | 0 |
| DS-31 | CryptoFees | Open API | Free | **LOG** — redundant with DS-29; cross-check only | — | — | 0 |
| DS-32 | Artemis | Keyed API, free tier thin | Freemium | **REJECT** — stablecoin flows and chain fundamentals from DS-29 | — | — | 0 |
| DS-33 | Farside | Plain HTML tables (`/btc/`, `/eth/`, all-data pages); no API | Free | **ADOPT** (D-3 ruled Farside, 6 Oct) — the one scrape in this order; STALE-not-empty and a column-change validator are mandatory | daily spot ETF flows by issuer and total, BTC and ETH; history from the all-data page | Daily → positioning & flows (T-1 in the 07:00 anchor; same-day in the 21:45 run); Weekly → flows; S-2 flag | 2 |
| DS-34 | Dune | Keyed API; free plan carries a small monthly credit budget (confirm at build) | Free | **ADOPT** (D-6 ruled yes, 6 Oct) — exactly two saved queries, run once a month, behind a credit-budget guard | on-chain ETF custody balances (check on DS-33's reported flows); stablecoin flows by venue | Monthly → mechanics | 1.5 |
| DS-35 | Messari | Keyed API; free tier is price data | Freemium | **REJECT** — CoinGecko already | — | — | 0 |
| DS-36 | L2BEAT | Unofficial JSON behind the site; open data repo | Free | **LOG** — L2 value secured as one Monthly line, built when a session is already in the ETH block; endpoint discovered then | `l2beat.tvs_total` | Monthly → mechanics | 0.5 |
| DS-37 | ultrasound.money | Unofficial API | Free | **REJECT** — DS-11's `ethsupply2` gives supply and burn | — | — | 0 |
| DS-38 | mempool.space | Open REST API, no key | Free | **ADOPT** | hashrate (3m), difficulty adjustment, recommended fees, mempool depth, pool shares | Weekly → mechanics; Monthly → BTC network health, the 500-day halving rule row (batch 3) | 1 |
| DS-39 | Step Finance | Portfolio app | — | **REJECT** | — | — | 0 |
| DS-40 | DeBank Stream | Social feed | — | **REJECT** | — | — | 0 |
| **DS-41** | **Deribit** (not on the list) | Open public API, no key | Free | **ADOPT — DVOL now** (D-4, 6 Oct); strike-level OI for a crypto GEX is **logged against EL-12** and built when the dealer engine is registered after 6b | DVOL index history (BTC, ETH) | Daily → what's priced (S-4) | 2 |
| **DS-42** | **Exchange futures APIs** — Bybit, OKX (not on the list); Binance dropped by D-2 | Open public APIs, no key, reachable from both the box and the laptop | Free | **ADOPT** Bybit and OKX; **Binance rejected** (D-2, 6 Oct: 451 from US addresses would make the leg box-only and untestable from the laptop) | funding, OI, top-trader and account long/short for BTC and ETH perps; aggregated with Hyperliquid | Daily → positioning & flows (S-3) | in DS-43 |
| **DS-43** | **Hyperliquid info endpoint** (the list names only its leaderboard) | Open API, no key | Free | **ADOPT** | funding, OI, mark for BTC/ETH/SOL and the watch names; HYPE fees via DS-29 | Daily → positioning & flows (S-3) | 4 (with DS-42) |
| **DS-44** | **alternative.me Fear & Greed** (not on the list) | Open API | Free | **ADOPT** | daily index, full history | Daily → what's priced (one word); narratives | 0.5 |
| **DS-45** | **bitcoin-data.com** (not on the list) | Open API, open source; endpoint coverage to verify | Free | **ADOPT with fallback** (D-8 ruled yes, 6 Oct) — mechanizes SR-29 (long-term-holder supply) if the series is served; if not, SR-29 stays by hand and this row is marked LOG | `btcdata.lth_supply_share` | Monthly → the SR-29 scorecard row, computed instead of by hand, with dual percentiles | 1 |

Also ruled in this order:

- **CoinGecko `/global`** (total market cap, BTC dominance) is added to the existing ST-13 fetcher. Daily → tape. 0.5 h.
- **One source family per venue.** Store families: `llama.*`, `hl.*`, `fut.*` (Bybit/OKX, venue in the key), `deribit.*`, `farside.*`, `coinglass.*`, `mempool.*`, `etherscan.*`, `gt.*`, `dune.*`, `fng.*`, `btcdata.*`. CoinGecko stays `coingecko.*` from ST-13. Modules in `altdata/sources/<family>.py`.
- **Every series carries `family` and `long_window`** under the metric-lenses brief: funding and OI in the positioning family (90-day and full-history windows); DVOL in the volatility family (5-year and full); stablecoin supply and ETF flows in the flows family (full history, which for both starts 2020/2024).
- **Keys live in `.env`** (`ETHERSCAN_API_KEY`, `DUNE_API_KEY`). Sessions print the key names Ari must add; they never write `.env`.
- **The unlock table, the DS-5/DS-25/DS-27/DS-31/DS-36 LOG rows and every REJECT** are recorded here so the next circulating list of forty does not re-propose them.

## §3 Derived series — candidate register entries

Five derived series come out of the adopted feeds. Each is written in the register's entry form; numbers are assigned at Audit #4 after the GTM batch. Rights follow §1.3: flags only after a passed gate.

### S-1 Stablecoin supply impulse — Thread D

**Ruling.** Adopt as Factor V scorecard rows (AMEND SR-20): total stablecoin supply, 30-day and 90-day change, and the share by chain (Ethereum, Tron, Solana, Base). The monetary-architecture thread has an official-reserve leg (COFER) and no private-dollar leg; this is the private-dollar leg. Reject any "liquidity signal" reading of it until a gate says otherwise. **Home.** Monthly Factor V scorecard; Weekly flows line. **Rights.** None (scorecard). **Data.** `llama.stable_total`, `llama.stable_by_chain`; full history from `stablecoincharts/all` (2020→), so the 5-year lens is available on day one. *Lives in:* `altdata/sources/llama.py`; `calc.stable_impulse_30d`, `calc.stable_impulse_90d`. **Validation gate.** None required for a scorecard; a flag proposal would need a 90-day ledger against BTC and risk returns.

### S-2 ETF flow streak and extreme — Thread D

**Ruling.** Adopt: daily total flow, streak length (consecutive same-sign sessions), and the 5-day sum's percentile against the full history from Jan 2024. Reject a level reading ("$66M is small") without the percentile. **Home.** 07:00 anchor positioning & flows (T-1), 21:45 run (same day), Weekly flows block. **Rights.** Narrow flag "ETF flows — extreme" at the 5th/95th percentile of the 5-day sum, after the gate. **Data.** `farside.btc_total`, `farside.eth_total`, by-issuer columns; backfilled from the all-data pages. *Lives in:* `altdata/sources/farside.py`; `calc.etf_streak`, `calc.etf_5d_pct`. **Validation gate.** Forward 5/20-day BTC return after extremes, 2024→; pass is a non-zero asymmetry at 20 days across ≥8 non-overlapping episodes. Offline; ledger in `docs/ledgers/`.

### S-3 Aggregate funding and open-interest extreme — Thread D

**Ruling.** Adopt: OI-weighted BTC and ETH perp funding across Hyperliquid, Bybit and OKX (Binance dropped, D-2), annualized; total OI in USD and OI/market-cap; z-scores on a 90-day window. Reject single-venue readings and the long/short "ratio" as a direction call (it is a retail-skew measure; stored, not flagged). **Home.** 07:00 anchor and 16:45 close positioning & flows; Weekly; 12:30 alert exception when the leverage flag trips intraday (after its gate; no liquidation series after D-1). **Rights.** Narrow flag "crypto leverage — crowded" (funding z > +2 with OI/mcap at a 90-day high) after the gate; the leverage-unwind tell pairs with SR-2's unwind logic in the Liquidity & Funding Stress overlay only through the one-at-a-time intake queue. **Data.** `hl.funding`, `hl.oi`, `fut.funding.<venue>`, `fut.oi.<venue>`, `fut.ls_top.<venue>`; backfill: Hyperliquid funding history from launch, Bybit and OKX funding history (paginated), OI history only as deep as each venue serves (so OI lenses mature over the first quarter). *Lives in:* `altdata/sources/hl.py`, `fut.py`; `calc.funding_agg`, `calc.oi_usd`, `calc.oi_mcap`, `calc.leverage_z`. **Validation gate.** Anatomy check on the Aug 2024, Feb 2025 and Oct 2025 unwinds and the May 2026 rush: the flag fires before the drawdown's largest day in ≥3 of 4 with ≤2 false positives per year. Offline.

### S-4 DVOL regime — Thread D

**Ruling.** Adopt: Deribit BTC and ETH DVOL, dual percentiles (5-year and full history from 2021), and DVOL minus 30-day realized as the crypto implied–realized spread. This is the cross-asset vol line the Volatility paper asks for and the stack does not yet have. Reject DVOL as a direction signal. **Home.** What's priced (daily, one line); the Volatility family lens in the Monthly. **Rights.** Modifier to the volatility family read (crypto vol regime: compressed / normal / stressed by percentile band), no gate needed for a lens; a flag would need one. **Data.** `deribit.dvol_btc`, `deribit.dvol_eth`; `calc.dvol_pct_5y`, `calc.dvol_pct_full`, `calc.dvol_minus_rv30`. The GEX extension (`deribit.oi_by_strike` → `calc.crypto_gex`) is logged against the dealer engine (EL-12) per D-4 and is built there after 6b, not here. *Lives in:* `altdata/sources/deribit.py`. **Validation gate.** None for the lens.

### S-5 Speculative froth gauge — Thread D

**Ruling.** Adopt (D-5, build now): count of new DEX pools created in the last 24 hours and the 24-hour volume of the top-20 trending pools on Solana and Base, each z-scored on a 20-day window once 90 days of store exist. The idea: memecoin launch velocity is a direct read on speculative appetite that the equity-side C&C overlay sees only through call volume and breadth. Reject any use before the calibration study. **Home.** Weekly what-doesn't-fit (one line); candidate input to the Concentration & Complacency overlay through the intake queue, **behind SR-19**. **Rights.** None until the gate; then conditioner only, like SR-19. **Data.** `gt.new_pools_24h.<network>`, `gt.trending_vol_24h.<network>`; no backfill exists (sampled from launch), so the gate cannot run before January 2027. *Lives in:* `altdata/sources/gt.py`; `calc.froth_z`. **Validation gate.** Offline study after 90 days of store: concordance with the C&C overlay's existing inputs and with forward 20-day SPX and BTC returns; pass is incremental information beyond the overlay's current inputs. Ledger in `docs/ledgers/`.

## §4 Placement in the stack

- **07:00 anchor and 16:45 close — positioning & flows, one crypto paragraph (≤ 6 lines):** T-1 ETF flows with streak and percentile (S-2); aggregate funding and OI change (S-3); DVOL band (S-4); Fear & Greed as one word. Tape carries BTC dominance from `/global`. Wired only after Track D's D4/D6 (the Daily/T&B wiring precondition); until then the block renders in the Weekly only.
- **21:45 run:** refreshes the ETF line with same-day Farside data when it has posted; otherwise the morning line stands with its `available_at`.
- **12:30 alert-only slot:** one information line when the leverage flag (S-3, after its gate) trips intraday; no setup rights, mirroring MW-3's exception.
- **Intraday runs (09:15, 10:30, 15:00):** nothing. The grep gate from MW-3 extends to cover these families.
- **Sunday 05:00 Weekly — a crypto flows block (W-block, ≤ 12 lines):** stablecoin supply 7d/30d (S-1); ETF flows week total and streak (S-2); funding and OI week change (S-3); DVOL band (S-4); hashrate and difficulty change, fee tier (DS-38); froth line (S-5, from launch, unscored); the Mechanism Watch block (MW-3) stays separate beneath it.
- **Monthly — in mechanics and the slow layers:** Factor V scorecard rows (S-1, AMEND SR-20); watch-name fundamentals table (fees, revenue, TVL from DS-29, 30-day change and percentile); BTC network health (hashrate, difficulty, fees; the SR-29 LTH row computed if D-8); ETH supply and burn (DS-11), L2 value secured when built (DS-36); VC raises, trailing 3 months (DS-29); next-90-day unlock table from the Security Master (DS-21); Dune items if D-6. Every row in the triple form (latest / long-run average / percentile, data as of).
- **Rights summary.** Scorecards and lenses print from day one. Flags (S-2, S-3, S-5) print only after their ledgers pass. Nothing enters a composite; the C&C and Liquidity overlays receive candidates only through the one-at-a-time intake queue.

## §5 Decisions to take in chat, one at a time

| # | Decision | Options | Default if not taken |
|---|---|---|---|
| D-1 | CoinGlass Hobbyist subscription ($29/mo, personal use) for liquidations, cross-venue funding and possibly ETF flows | Yes · No · Trial one month | **Ruled No, 6 Oct 03:16 ET.** DS-24/DS-26 rejected, CD-6 struck; funding and OI from the free venues; no liquidation line |
| D-2 | Binance futures API from the Hetzner box (works from Germany; 451 from Pittsburgh, so laptop tests use Bybit/OKX) | Yes, on the box only · No, Bybit + OKX + Hyperliquid only | **Ruled 6 Oct 03:19 ET: drop Binance.** Aggregate is Hyperliquid + Bybit + OKX; one fetcher that behaves the same on the box and the laptop |
| D-3 | Farside as the ETF-flow source (HTML scrape with STALE fallback), or no ETF-flow series (the Farside figure then quoted by hand in the narrative) | Farside · None | **Ruled 6 Oct 03:21 ET: Farside.** CD-4 builds; S-2 backfilled from the all-data pages |
| D-4 | Deribit scope | DVOL only (2 h) · DVOL + strike-level OI for crypto GEX (+4 h; lands with EL-12 after 6b) | **Ruled 6 Oct 03:23 ET: DVOL now, GEX later.** The strike-level build (≈4 h) is logged against EL-12 in the Enterprise Layer order's dealer-engine item |
| D-5 | Froth gauge (S-5): build and store now so the January gate is possible, or shelve | Build · Shelve | **Ruled 6 Oct 03:25 ET: build now.** CD-7 joins Tranche A so sampling starts with the first deploy; the Weekly line prints unscored; gate no earlier than January 2027 |
| D-6 | Dune free plan for at most two saved queries | Yes · Skip | **Ruled 6 Oct 03:27 ET: yes.** Two saved queries (ETF custody balances; stablecoin flows by venue), monthly, guard at 80% of the month's credits; `DUNE_API_KEY` in `.env` |
| D-7 | Encoding and slot: Batch 4 of Amendment #4 (Thread D), Tranche A placed by Audit #4 — candidate slots: with the GTM batch after 6e, or earlier beside Phase B if the 6d ingestion scaffolding makes it cheap | Audit #4 places it · Earlier, beside Phase B | **Ruled 6 Oct 03:28 ET: later.** Encoded as Batch 4 of Amendment #4, Thread D; Audit #4 (14–15 Oct) places Tranche A, proposed beside the GTM batch after 6e; nothing from this order enters the October calendar |
| D-8 | AMEND SR-29 to compute LTH supply share from bitcoin-data.com if the endpoint serves it (verified at build; falls back to by-hand) | Yes · Keep by hand | **Ruled 6 Oct 03:30 ET: yes with fallback.** CD-12 verifies the endpoint first; if the series is absent, SR-29 keeps its by-hand status and the session reports it in "needs you" |

## §6 Build

| ID | Item | Hours | Depends on |
|---|---|---|---|
| CD-1 | `llama.py`: stablecoins (total, by chain, full history), fees/revenue for the watch names (slugs resolved from `/protocols`), chain TVL, DEX volume, perps OI overview, `/raises`; S-1 series | 3 | D1c (new writers); ST-13 conventions |
| CD-2 | `hl.py` + `fut.py`: funding, OI, long/short for BTC and ETH perps across Hyperliquid, Bybit, OKX; aggregation; S-3 series and backfill | 4 | D1c |
| CD-3 | `deribit.py`: DVOL history and dual percentiles; S-4 (strike-level OI deferred to EL-12 per D-4) | 2 | D1c |
| CD-4 | `farside.py`: `/btc/`, `/eth/` tables with a browser user-agent, all-data backfill, STALE-not-empty; S-2 series | 2 | D1c |
| CD-5 | `mempool.py` + `etherscan.py` + `/global` on the CoinGecko fetcher + `fng.py` | 2 | D1c |
| CD-6 | `coinglass.py` — **struck** (D-1 ruled No) | 0 | — |
| CD-7 | `gt.py`: new-pool count and trending volume, Solana and Base; DexScreener search as fallback; S-5 series | 3 | D1c |
| CD-8 | Derived series and flags: `calc.*` for S-1…S-5, Factor V rows (AMEND SR-20), `family`/`long_window` on every series | 3 | CD-1…CD-7 |
| CD-9 | Blocks: Weekly W-block; Monthly rows and the unlock table; daily paragraph and 12:30 line (wired only after D4/D6) | 4 | T2, T3 built; D4/D6 for the daily part |
| CD-10 | Validators: `available_at` present; STALE render test; family/long_window check; intraday grep gate extended; Farside column-change detector | 2 | CD-4, CD-9 |
| CD-11 | `dune.py`: two saved queries, credit budget guard | 1.5 | D1c; `DUNE_API_KEY` in `.env` |
| CD-12 | `btcdata.py`: verify the LTH/STH endpoints, then LTH supply share with the SR-29 row computed; by-hand fallback recorded if absent | 1 | D1c |
| By hand | Security Master unlock schedules for the watch names (DS-21); `.env` keys; CoinGlass sign-up if D-1 | ~1.5 | — |

**Tranches.** **A** — CD-1…CD-5, CD-7, CD-8, the Weekly and Monthly parts of CD-9, CD-10: about **19 h**, free, no daily wiring, placed by Audit #4 (D-7: proposed beside the GTM batch after 6e; CD-7 rides in A so the froth series starts accruing history at the first deploy). **B** — the daily paragraph and the 12:30 line: about **4 h**, after Track D's D4/D6. **C** — CD-11 (1.5 h) and CD-12 (1 h), both Monthly-only and built with the Monthly rows; each severable. The GEX extension (≈4 h) travels with EL-12, not this order. Core total ≈ 23 h; everything ≈ 25 h; by hand ≈ 1.5 h.

**Calibration ledgers.** S-2 and S-3 gates can run as soon as their backfills land (one offline session, ~3 h, counted in the signal-triage calibration budget, not here). S-5's gate waits for 90 days of store.

## §7 Register

Numbers for S-1…S-5 are assigned at Audit #4, continuing after the GTM batch. SR-20 is amended with the stablecoin rows (S-1); SR-29 is amended from "by hand" to "computed (bitcoin-data.com), by-hand fallback" (D-8); SR-10 is unchanged and shares the CoinGecko fetcher. The DS table in §2 is recorded against the register as the disposition of the forty-site list so that the next such list is diffed against it rather than re-triaged.

## §8 Sign-off

| Field | Entry |
|---|---|
| D-1…D-8 | taken in chat 6 Oct 2026, 03:16–03:30 ET; recorded in §5 |
| Encoding | Batch 4 of Amendment #4, Thread D (D-7); slot set at Audit #4 |
| Signed | Ari Chester — 2026-10-06 (the eight rulings above constitute the signature; Audit #4 places the tranches) |

---

## Appendix A — Endpoint reference

Checked 6 Oct 2026 unless marked *verify*. All GET unless stated. Rate limits are the published or commonly observed ones; the fetchers back off on 429.

**DefiLlama** (`https://api.llama.fi`, no key)
- `/protocols` (slug resolution); `/protocol/{slug}`; `/v2/chains`; `/v2/historicalChainTvl/{chain}`
- `https://stablecoins.llama.fi/stablecoins?includePrices=true`; `/stablecoincharts/all`; `/stablecoincharts/{chain}`; `/stablecoin/{id}`
- `/overview/fees?excludeTotalDataChart=true&dataType=dailyFees` and `dataType=dailyRevenue`; `/summary/fees/{slug}?dataType=dailyRevenue`
- `/overview/dexs`; `/overview/open-interest`; `/raises`
- Unlocks (`/emissions`) are Pro-only — not used.

**Hyperliquid** (`POST https://api.hyperliquid.xyz/info`, JSON body, no key; aggregated weight limit ≈ 1,200/min per IP — *verify*)
- `{"type":"metaAndAssetCtxs"}` → per-asset funding, openInterest, markPx, dayNtlVlm
- `{"type":"fundingHistory","coin":"BTC","startTime":<ms>}`; `{"type":"candleSnapshot","req":{"coin":"BTC","interval":"1d","startTime":<ms>,"endTime":<ms>}}`
- Leaderboard (unofficial, LOG only): `https://stats-data.hyperliquid.xyz/Mainnet/leaderboard`

**Binance** — not used (D-2: dropped; HTTP 451 from US addresses).

**Bybit** (`https://api.bybit.com`, no key)
- `/v5/market/tickers?category=linear&symbol=BTCUSDT` (fundingRate, openInterest); `/v5/market/funding/history?category=linear&symbol=BTCUSDT`; `/v5/market/open-interest?category=linear&symbol=BTCUSDT&intervalTime=1d`

**OKX** (`https://www.okx.com`, no key)
- `/api/v5/public/funding-rate?instId=BTC-USDT-SWAP`; `/api/v5/public/funding-rate-history?instId=BTC-USDT-SWAP`; `/api/v5/public/open-interest?instType=SWAP&instId=BTC-USDT-SWAP`; `/api/v5/rubik/stat/contracts/long-short-account-ratio?ccy=BTC`

**Deribit** (`https://www.deribit.com/api/v2`, no key for public methods)
- `/public/get_volatility_index_data?currency=BTC&start_timestamp=<ms>&end_timestamp=<ms>&resolution=1D` (paginate by window)
- For the EL-12 extension later (not built here): `/public/get_book_summary_by_currency?currency=BTC&kind=option` (OI by instrument → strike/expiry for GEX); `/public/get_instruments?currency=BTC&kind=option`; `/public/get_index_price?index_name=btc_usd`

**Farside** (HTML; send a browser user-agent; `pandas.read_html`)
- `https://farside.co.uk/btc/`, `https://farside.co.uk/eth/` (recent window, Total column, summary rows to drop)
- All-data pages for backfill: `https://farside.co.uk/bitcoin-etf-flow-all-data/`, `https://farside.co.uk/ethereum-etf-flow-all-data/` — *verify the slugs at build*; the recent pages link to them.
- Posting time: US evening; the 21:45 run is the earliest same-day read.

**CoinGlass** — not used (D-1 ruled No). For the record: `https://open-api-v4.coinglass.com`, header `CG-API-KEY`, Hobbyist 30/min; aggregated liquidations and ETF flows are in its catalogue if the ruling is ever revisited.

**mempool.space** (`https://mempool.space/api`, no key)
- `/v1/mining/hashrate/3m`; `/v1/difficulty-adjustment`; `/v1/fees/recommended`; `/v1/fees/mempool-blocks`; `/blocks/tip/height`; `/v1/mining/pools/1w`

**Etherscan** (`https://api.etherscan.io/v2/api?chainid=1`, key in `.env` as `ETHERSCAN_API_KEY`; 5/s, 100k/day)
- `&module=stats&action=ethsupply2`; `&module=gastracker&action=gasoracle`

**GeckoTerminal** (`https://api.geckoterminal.com/api/v2`, header `Accept: application/json;version=20230302`, no key, 30/min)
- `/networks/{network}/new_pools?page={1..10}` (networks `solana`, `base`; count pools with `pool_created_at` in the last 24 h; ≥200 means saturated, store as censored)
- `/networks/{network}/trending_pools` (sum `volume_usd.h24` over the top 20)

**DexScreener** (`https://api.dexscreener.com`, no key, 300/min) — backup only
- `/latest/dex/search?q={query}`; `/token-pairs/v1/{chainId}/{tokenAddress}`

**Dune** (`https://api.dune.com/api/v1`, header `X-Dune-API-Key`)
- `POST /query/{id}/execute` → `GET /execution/{id}/results`; or `GET /query/{id}/results` for the last run. Credit budget read from the account page; guard at 80%.

**alternative.me** (`https://api.alternative.me/fng/?limit=0&format=json`, no key) — full history in one call.

**bitcoin-data.com** — open API; the LTH/STH supply endpoints are to be confirmed from its documentation at build (D-8). If absent, SR-29 stays by hand and the session says so.

**CoinGecko** (existing ST-13 fetcher, Demo key) — add `/global` (total market cap, BTC dominance).

**L2BEAT** (DS-36, LOG) — endpoint discovered when built; the l2beat GitHub data repo is the fallback.

## Appendix B — First session paste (Tranche A, part 1: CD-1, CD-2, CD-5)

*Runtime: about 60–90 minutes of session time; `make validate` afterwards runs 3–5 minutes in Git's bash on the laptop. Ari's own line goes on top.*

> Read `docs/change-order-crypto-data-sources-2026-10-06.md` (§2 for what to pull, §3 S-1 and S-3 for the derived series, Appendix A for endpoints) and the ST-13 CoinGecko fetcher for the point-in-time conventions. Build CD-1 (`altdata/sources/llama.py`), CD-2 (`altdata/sources/hl.py`, `altdata/sources/fut.py` with Bybit and OKX only — no Binance, per §5 D-2) and CD-5 (`mempool.py`, `etherscan.py`, `fng.py`, plus `/global` on the CoinGecko fetcher). Every series gets `family`, `long_window` and `available_at`; backfill where Appendix A says history exists; no series without a unit test on its parser. Do not write `.env`; print the key names I must add. Run `make validate`, then stop and report: series created, backfill depth per series, anything in Appendix A that did not match reality, and a "needs you" list. No deploy.
