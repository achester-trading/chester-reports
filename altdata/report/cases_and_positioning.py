"""
Per-asset structured case summaries and trading environment templates.

Each entry provides:
  - cases:              bull / bear / flat (range-bound) cases as bullet lists
  - trading_environment: durable description of this asset's tape character —
                         what typical positioning extremes look like, what
                         features the recent regime, what dynamics to watch
  - positioning_lens:   which positioning data sources are relevant for this
                        asset (cot, etf_flows, on_chain, corporate_treasury,
                        central_bank, etc.) — drives which positioning widgets
                        the dashboard renders

The bullet cases are intentionally crisp — they distill the multi-paragraph
narratives in narratives_extended.py into a structured scannable form for the
end of the Outlook & Catalysts section.

The trading_environment narrative is durable enough to hold for months but
will eventually be updated by the weekly news-scan layer once that's wired.
Today it captures what's structurally true about this asset's recent tape.
"""

CASES_AND_POSITIONING = {

    # ──────────────────────────────────────────────────────────────────────
    # GOLD
    # ──────────────────────────────────────────────────────────────────────
    "gold": {
        "cases": {
            "bull": [
                "Central bank accumulation continues above 1,000 tonnes annually as EM reserve managers diversify out of dollar assets post-2022 sanctions precedent",
                "US fiscal trajectory (debt-to-GDP above 120%, deficits 6-7% of GDP) supports gold as non-sovereign store of value",
                "Western investors remain materially underweight (model portfolios at 0-2% vs historical 5%+) — re-engagement represents latent upside fuel",
                "Real-yield framework broken since 2022; gold trading on a different demand pool that's insensitive to TIPS yields",
                "Geopolitical tail risks (Middle East, Taiwan, broader fragmentation) support persistent safe-haven bid",
            ],
            "bear": [
                "De-dollarization narrative substantially priced; further EM reserve diversification flows may moderate from torrid 2022-24 pace",
                "Restoration of real-yield discipline (either via fiscal consolidation or sustained restrictive Fed) would remove macro support",
                "Sharp risk-off liquidity events can produce gold weakness as institutions sell what they can (March 2020 dynamic)",
                "Position crowding: speculative positioning at extremes vulnerable to unwind",
                "Opportunity cost rises if real yields move materially higher; no-yield character becomes meaningful headwind",
            ],
            "flat": [
                "Range-bound between central bank floor (price-insensitive accumulation) and Western investor cap (sustained underweight)",
                "Mine supply rigidity keeps supply curve fixed; demand variations within a band produce range-trading",
                "Real-yield decoupling persists but absence of new catalyst (Western re-engagement or central bank pause) keeps price contained",
                "Tactical opportunities driven by ETF flow inflections and seasonal Asian demand cycles",
            ],
        },
        "trading_environment": (
            "Gold has traded with persistent upside bias and shallow drawdowns through the post-2022 regime. ETF flows have been weak yet "
            "price has rallied — an unusual pattern historically that points to non-Western demand dominating the marginal bid. CFTC managed-"
            "money positioning has stayed elevated but below 2020/2011 extremes, suggesting the rally has been less speculatively-driven than "
            "prior cycles. The Shanghai Gold Exchange premium to London has periodically run wide, signaling persistent Chinese physical "
            "tightness. Mining equities have lagged the metal — a divergence that often resolves in equity catch-up during sustained price "
            "strength, though that pattern has been slow to play out this cycle. Tactical entries have rewarded patience during pullbacks "
            "toward technical support; chasing breakouts has been less productive given the slow grind nature of the rally."
        ),
        "positioning_lens": ["cot", "central_bank", "etf_holdings"],
    },

    # ──────────────────────────────────────────────────────────────────────
    # SILVER
    # ──────────────────────────────────────────────────────────────────────
    "silver": {
        "cases": {
            "bull": [
                "Structural industrial deficit from solar PV demand growth meets inelastic byproduct supply",
                "Above-ground inventories (COMEX, LBMA) drawing down; the buffer that has absorbed the deficit is finite",
                "Gold-silver ratio above 80 leaves silver mean-reversion case unrealized; any gold rally tends to produce silver outperformance",
                "EV adoption, 5G, electronics drive silver intensity per device higher; substitution alternatives are technically immature",
                "Investment demand has been muted; Western re-engagement would be additive to industrial tightness",
            ],
            "bear": [
                "China-led industrial slowdown would hit silver harder than gold via solar manufacturing exposure",
                "Solar cell silver-loading continues to fall via thrifting; structural demand growth may be blunted",
                "Gold-silver ratio elevation may be structural — old mean-reversion playbooks may simply be broken",
                "Long-promised inventory squeeze hasn't produced violent moves; above-ground stock buffer may be larger than reported deficits imply",
                "Silver is acutely sensitive to global manufacturing cycle; any sustained PMI weakness drags the metal",
            ],
            "flat": [
                "Industrial demand growth offset by ongoing thrifting; net structural pull is positive but slow",
                "Gold-silver ratio settles in a new equilibrium range above historical norms",
                "Range-bound trading with periodic violent moves on positioning extremes",
                "Tactical opportunities tied to gold-silver ratio mean reversion rather than directional view",
            ],
        },
        "trading_environment": (
            "Silver remains among the most volatile precious metals contracts, with violent moves both directions when positioning becomes "
            "extreme. The asset has tended to lag gold during the early phase of precious-metals advances then catch up sharply — the "
            "characteristic 'silver plays catch-up' pattern. Recent quarters have seen this dynamic muted, with silver underperforming gold "
            "more persistently than historical norms. CFTC managed-money positioning swings are wider in silver than gold given the smaller "
            "futures market. The retail-driven 'silver squeeze' attempts of 2021 demonstrated both how rapidly investment demand can "
            "mobilize and how difficult sustained price pressure is against industrial-flow producers and structural hedging. Tactical "
            "entries during gold-led rallies when the gold-silver ratio is moving lower (silver outperforming) have been more productive "
            "than directional silver bets."
        ),
        "positioning_lens": ["cot", "etf_holdings"],
    },

    # ──────────────────────────────────────────────────────────────────────
    # COPPER
    # ──────────────────────────────────────────────────────────────────────
    "copper": {
        "cases": {
            "bull": [
                "Structural deficit from electrification (EVs, grid, renewables) collides with slow-to-respond supply pipeline",
                "TC/RCs at multi-year lows signal severe concentrate tightness; Chinese smelters cutting production validates the upstream squeeze",
                "AI data center buildout adds new structural demand vector; hyperscaler capex at record levels",
                "Mine supply pipeline thin beyond Kamoa-Kakula; major project lead times measured in decades",
                "Years of underinvestment 2014-2020 left supply pipeline unable to fill demand gap emerging late this decade",
            ],
            "bear": [
                "Chinese property sector weakness continues; broader Chinese industrial slowdown overwhelms electrification thesis",
                "EV adoption disappoints relative to bullish projections; hybrid share grows at BEV expense",
                "Recycling and aluminum substitution prove more responsive to high prices than bull case assumes",
                "New supply pipeline (DRC, Indonesia, brownfield expansions) delivers more than bull case credits",
                "Manufacturing PMIs globally remain in contraction; cycle dominates structure on multi-year horizon",
            ],
            "flat": [
                "Cyclical Chinese weakness offsets structural electrification demand — net flat for now",
                "OPEC-style discipline from major producers caps both upside (Codelco, BHP, Glencore can flex) and downside (closures)",
                "Exchange inventories oscillating but not signaling acute tightness",
                "Tactical opportunities tied to Chinese stimulus cycles and PMI inflections",
            ],
        },
        "trading_environment": (
            "Copper has traded sideways-to-higher with significant volatility, oscillating between bullish structural narrative pulls and "
            "bearish cyclical Chinese signal. The forward curve has flipped between modest backwardation and contango without sustained "
            "directional signal. Speculative positioning via CME copper futures has been less crowded than at prior cycle peaks, suggesting "
            "the structural thesis is not yet broadly positioned. TC/RC compression is the cleanest real-time tightness signal and has "
            "moved decisively lower, but refined market tightness hasn't yet flowed through to spot prices because Chinese smelter capacity "
            "absorbed the gap until recently. Mining equities (Freeport, Southern Copper, BHP, Antofagasta, First Quantum) have traded with "
            "high operational leverage to the metal; Cobre Panamá closure remains an open chapter affecting First Quantum specifically. "
            "Tactical positioning into Chinese stimulus announcements has been productive; chasing structural narrative breakouts has been "
            "less so."
        ),
        "positioning_lens": ["cot", "exchange_inventories"],
    },

    # ──────────────────────────────────────────────────────────────────────
    # OIL
    # ──────────────────────────────────────────────────────────────────────
    "oil": {
        "cases": {
            "bull": [
                "Underinvestment 2014-2020 left supply pipeline thin beyond shale and Guyana; OPEC+ spare capacity erodes in demand-resilience scenario",
                "Shale capital discipline persists; quick-cycle responsiveness reduced from 2014-2019 norms",
                "EM demand growth (India in particular) resilient and growing structurally",
                "Geopolitical fragility (Middle East, Russia-Ukraine, sanctions enforcement intensification) creates persistent tail risk",
                "Petrochemical and aviation demand resilient to EV displacement; demand peak may be later than IEA scenarios suggest",
            ],
            "bear": [
                "EV adoption accelerates faster than expected; Chinese gasoline demand peak arrives earlier than bull case",
                "OPEC+ unity fragments (Saudi-UAE quota dispute) producing 2020-style price war",
                "Demand peak arrives mid-2020s under IEA scenarios; structural demand erosion begins",
                "Substantial OPEC+ spare capacity gets activated; shale plus Guyana plus other non-OPEC growth provides supply response",
                "Chinese structural slowdown becomes permanent rather than cyclical",
            ],
            "flat": [
                "OPEC+ defends floor at $70-80 WTI through voluntary cuts; spare capacity caps upside near $85-95",
                "Saudi fiscal break-even (~$85 Brent) anchors the floor commitment",
                "Geopolitical premium fades within weeks of any shock as supply responds or fears moderate",
                "Range-bound trading with breakouts requiring supply or demand shocks",
            ],
        },
        "trading_environment": (
            "Crude has held a managed range broadly defined by OPEC+ floor defense and shale-plus-demand-concern upside cap. Volatility has "
            "compressed materially compared to 2020-2022 but periodic spikes on geopolitical events have been quickly faded. Managed-money "
            "net positioning on NYMEX WTI (visible in CFTC COT) has cycled between net long extremes that have historically marked tops and "
            "net flat that has typically marked bottoms. The forward curve has oscillated between backwardation (signaling near-term "
            "tightness) and modest contango. Brent-WTI spreads have remained well-behaved. Refining margins (3-2-1 cracks) have been "
            "structurally elevated relative to pre-2022. The geopolitical risk premium has been smaller than the 2022 spike implied — "
            "markets have learned to discount geopolitical shocks faster as actual supply disruptions have repeatedly been smaller than "
            "feared. Tactical opportunities have favored fading extreme positioning rather than chasing momentum."
        ),
        "positioning_lens": ["cot", "spr_inventory", "rig_count"],
    },

    # ──────────────────────────────────────────────────────────────────────
    # NATURAL GAS
    # ──────────────────────────────────────────────────────────────────────
    "natgas": {
        "cases": {
            "bull": [
                "LNG export ramp progressively absorbs chronic US oversupply; capacity nearly doubling by 2027-2028",
                "Data center electricity demand reviving US load growth after 20 years of stagnation",
                "Coal-to-gas switching continues; gas as renewable backup grows structurally",
                "Pipeline takeaway constraints limit supply response in Appalachia regardless of price",
                "Henry Hub progressively links to global TTF/JKM, supporting structurally higher and less volatile prices",
            ],
            "bear": [
                "Robust associated-gas production from Permian responds to oil prices not gas prices; chronic oversupply persists",
                "Mild winter or LNG export outage produces sharp storage overhang and price collapse",
                "European demand structurally lower post-2022 shock; demand destruction in industry permanent",
                "Hyperscaler shifts to nuclear or other firm low-carbon options blunts data-center gas demand growth",
                "Renewables and storage progressively displace gas peaker demand on faster trajectory than expected",
            ],
            "flat": [
                "Storage cycle range-bound between five-year average bands; weather and LNG variables average out",
                "Production discipline meets demand variability; price oscillates around marginal cost of dedicated dry-gas production",
                "Volatility remains elevated but mean-reverts; range trading within $2-4 Henry Hub band",
            ],
        },
        "trading_environment": (
            "Natural gas remains among the most volatile of any liquid commodity contract. Price moves of 5-10% in a single session are "
            "routine; weekly EIA storage reports (Thursdays) routinely produce immediate 2-5% moves on surprise prints. Speculative "
            "positioning via NYMEX Henry Hub futures swings violently with weather forecasts. Open interest is dominated by physical-market "
            "hedgers (producers, utilities, industrial users) with speculators providing the marginal price discovery. The futures curve "
            "shape is informative: structural contango through 2024 has gradually flattened as LNG demand growth absorbs supply, but the "
            "front-month often disconnects from later contracts during weather and storage events. Regional basis differentials (Permian "
            "Waha Hub at deep discounts to Henry Hub during pipeline-constrained periods; New England premiums during winter cold snaps) "
            "create significant intra-market dispersion. LNG terminal feedgas data is increasingly the key real-time export-demand "
            "indicator. Position sizing in gas trades should reflect the genuine volatility — outsized moves both ways are common."
        ),
        "positioning_lens": ["cot", "storage", "lng_feedgas"],
    },

    # ──────────────────────────────────────────────────────────────────────
    # AGRICULTURE
    # ──────────────────────────────────────────────────────────────────────
    "agri": {
        "cases": {
            "bull": [
                "Climate volatility increasingly disrupts major growing regions; weather risk a structural tailwind",
                "Constrained arable land per capita as global population grows; dietary upgrading multiplicative for feed demand",
                "Biofuel mandate structure ties agri to energy prices; renewable diesel growth supports vegetable oil demand",
                "Specific crop deficits (cocoa, coffee, orange juice) demonstrate how rapidly supply shocks can produce dramatic price moves",
                "Indian and emerging-Asia consumption growth provides structural demand floor",
            ],
            "bear": [
                "Major grain harvests have been favorable; stocks-to-use ratios elevated and weighing on corn, soy, wheat",
                "Index-rolled exposure (DBA, PDBC) destroys value via contango drag in steeply-contangoed agri curves",
                "Chinese soybean demand growth has slowed materially; African Swine Fever feed-demand boost fully digested",
                "Better seed genetics, improved farming practices steadily raise yields above historical trend",
                "Tariff disruptions can redistribute flows but rarely produce sustained global price impact",
            ],
            "flat": [
                "Crop-specific dispersion masks aggregate flat picture — basket exposure suffers from this",
                "Weather cycles produce range-bound trading punctuated by occasional supply shocks per crop",
                "Stocks-to-use comfortable across major grains; tightness confined to specific softs",
            ],
        },
        "trading_environment": (
            "Agricultural commodities exhibit enormous dispersion at any given time — broad agri indices (DBA, PDBC) often produce returns "
            "that obscure dramatic moves in individual crops. Recent quarters have seen this pattern continue: ample grain harvests "
            "pressuring corn, soy, and wheat while cocoa hit record highs above $11,000/tonne on West African disease and weather, coffee "
            "rallied on Brazilian frost concerns, and orange juice traded at historic levels on Florida citrus disease. The futures curves "
            "are typically steeply contangoed (storage costs plus convenience yield), creating substantial roll costs for passive long "
            "exposure — the canonical reason DBA-style exposure has consistently underperformed spot prices. Managed-money positioning via "
            "CFTC COT is informative per crop: grain net long extremes have marked seasonal tops, net short extremes have marked weather-"
            "risk troughs. The agri trade is fundamentally a targeted crop-by-crop exercise, not a basket play. USDA WASDE prints (monthly) "
            "remain the dominant short-term mover. Producer stocks (Bunge, ADM, Tyson) and farmland exposures provide alternative ways to "
            "access the broader thesis with different cost structures."
        ),
        "positioning_lens": ["cot", "stocks_to_use"],
    },

    # ──────────────────────────────────────────────────────────────────────
    # BITCOIN
    # ──────────────────────────────────────────────────────────────────────
    "btc": {
        "cases": {
            "bull": [
                "Spot ETF demand continues — institutional/wealth-management channel still in early innings; RIA allocations growing in model portfolios",
                "Corporate treasury adoption accelerating beyond Strategy; total corporate holdings exceeding 350,000 BTC and rising",
                "US Strategic Bitcoin Reserve discussion alive in policy circles; even partial adoption represents major demand",
                "Halved issuance (~450 BTC/day post-2024 halving) below 1% of supply annually — issuance rate below gold's",
                "Long-term holder supply trending up; exchange balances declining; effective liquid float tightening",
                "Macro liquidity expansion (Fed eventual cuts, global rate-cutting cycle) historically supports Bitcoin",
            ],
            "bear": [
                "Persistent volatility (multiple historical 80%+ drawdowns) unsuitable for many institutional mandates",
                "Tight correlation to risk assets during stress contradicts 'digital gold' thesis; recent rolling correlation to Nasdaq elevated",
                "Regulatory tail risk remains; stablecoin (Tether) concerns could affect market liquidity dramatically",
                "Four-year halving cycle may still dictate drawdowns even with institutional buying smoothing the path",
                "ETF flows can reverse rapidly; outflow episodes have produced sharp short-term selloffs",
            ],
            "flat": [
                "ETF inflow steady-state absorbs new supply; range-bound consolidation between cycle peaks",
                "Institutional bid balances retail/leverage-driven selloff during macro stress",
                "Halving cycle dynamics produce extended consolidations after initial post-halving rallies",
            ],
        },
        "trading_environment": (
            "Bitcoin has traded in a fundamentally different regime since spot ETF launches in January 2024. Daily ETF flow data (Farside "
            "Investors, Bloomberg) has become the dominant short-term price signal — sustained net inflows above 5,000 BTC/week "
            "historically correspond with price strength; net outflows produce drawdowns. The character of cycles has changed: drawdowns "
            "have been less violent than pre-ETF cycles (2024 max drawdown materially smaller than 2018, 2022 declines), but the upside "
            "has been more sustained and less explosive than the 2017 and 2020-21 retail-driven blow-off tops. Derivatives positioning "
            "(perpetual futures funding rates, options open interest on Deribit, CME futures positioning) provides tactical signals — "
            "elevated funding rates above 0.05% per 8 hours have typically marked overheating; deeply negative funding has marked capitulation. "
            "On-chain metrics from Glassnode (long-term holder supply, MVRV, exchange balances, miner outflows) provide independent demand-"
            "supply signals. Strategy's quarterly purchases provide a steady-bid signal. The macro-correlation pattern is the most "
            "important framework shift: Bitcoin trades as a liquidity-sensitive risk asset, rallying when financial conditions ease and "
            "selling off in liquidity tightening episodes."
        ),
        "positioning_lens": ["etf_flows", "corporate_treasury", "on_chain", "derivatives"],
    },

    # ──────────────────────────────────────────────────────────────────────
    # ETHEREUM
    # ──────────────────────────────────────────────────────────────────────
    "eth": {
        "cases": {
            "bull": [
                "Largest decentralized settlement layer for DeFi, stablecoins, and emerging RWA tokenization",
                "Staking yield (3-4%) provides productive return distinct from BTC's pure store-of-value",
                "RWA tokenization growing (BlackRock BUIDL, Franklin Templeton BENJI); Ethereum primary settlement infrastructure",
                "Pectra and subsequent upgrades refining PoS economics; protocol roadmap active",
                "ETH/BTC ratio near multi-year lows; oversold relative to Bitcoin on technical and fundamental measures",
            ],
            "bear": [
                "L2s and competing L1s capture activity, fees, and developer mindshare while ETH itself struggles to capture value",
                "Post-Dencun L1 fee reduction weakened deflationary narrative; ETH net inflationary in many periods",
                "Spot ETH ETF flows have been disappointing vs BTC; institutional pitch isn't landing",
                "Persistent underperformance vs Bitcoin has eroded confidence in ETH-specific theses",
                "Competition from Solana, Aptos, Sui, and others in smart-contract layer",
            ],
            "flat": [
                "Stuck in BTC's shadow with no specific catalyst to drive independent move",
                "L2 success grows ecosystem but ETH itself sees modest value capture",
                "Range-bound trading on staking-yield support and risk-asset macro moves",
            ],
        },
        "trading_environment": (
            "Ethereum has traded as a high-beta Bitcoin proxy through the post-ETF era, but with persistent underperformance that has made "
            "ETH/BTC the dominant pair to watch. The ratio has fallen consistently through 2024-2025, reflecting both BTC's stronger "
            "institutional bid and ETH-specific value-capture concerns. Spot ETH ETF flows (Farside Investors) have been an order of "
            "magnitude smaller than BTC ETF flows. Staking yield (around 3-4% via direct staking or via liquid staking derivatives like "
            "Lido's stETH or Rocket Pool's rETH) provides an income floor distinct from BTC. Network activity metrics — gas usage, L1 vs "
            "L2 transaction volume, base-layer fee burn vs issuance — are the cleanest measures of value-capture dynamics; recent data has "
            "been mixed. Deribit options markets have priced ETH volatility persistently lower than BTC, perhaps reflecting the asset's "
            "ranger character through this cycle. RWA tokenization milestones (BlackRock BUIDL growth, Franklin Templeton BENJI on "
            "various chains) provide intermittent positive catalysts. The structural debate — whether ETH captures value from ecosystem "
            "growth or whether L2s and other chains do — remains unresolved and dominates the medium-term picture."
        ),
        "positioning_lens": ["etf_flows", "on_chain", "derivatives", "staking"],
    },

    # ──────────────────────────────────────────────────────────────────────
    # SOLANA
    # ──────────────────────────────────────────────────────────────────────
    "sol": {
        "cases": {
            "bull": [
                "Leading contender for mainstream consumer crypto; architectural fit for high-throughput applications",
                "Spot Solana ETF approval potential — major prospective demand catalyst across multiple filings (VanEck, 21Shares, Bitwise, Canary)",
                "Firedancer rollout improves performance and decentralization; addresses historical reliability concerns",
                "DEX volume periodically matches/exceeds Ethereum mainnet; demonstrated product-market fit",
                "DePIN category traction (Helium, Render, Hivemapper) positions Solana for novel use cases",
                "Network uptime has improved meaningfully from 2021-22 outage cadence",
            ],
            "bear": [
                "Historical reliability concerns linger; any major outage would re-traumatize institutional perception",
                "Inflationary supply (~5% annually, declining toward 1.5% floor) requires continued demand growth",
                "Speculative-activity dependence (memecoins) vulnerable to crypto-cycle downturns",
                "Decentralization tradeoffs vs Ethereum are real and would matter in adversarial scenarios",
                "Competition from other high-throughput L1s (Aptos, Sui) limits structural moat",
            ],
            "flat": [
                "ETF approval timing uncertain; absent that catalyst, SOL trades as high-beta BTC proxy",
                "DePIN traction continues at modest pace; not yet transformational",
                "Range-bound trading with violent moves on positioning extremes",
            ],
        },
        "trading_environment": (
            "Solana is the highest-beta major crypto asset, with violent moves both directions. The SOL/BTC and SOL/ETH ratios are the "
            "canonical rotation gauges — both rallied dramatically in late 2023/early 2024, have since traded sideways-to-down. Daily DEX "
            "volume (Jupiter, Raydium, Orca) has been a real on-chain activity signal; periods of Solana DEX volume exceeding Ethereum "
            "mainnet plus L2s combined have generally coincided with SOL outperformance. Memecoin activity on Pump.fun has been a "
            "meaningful share of on-chain volume — controversial but real economic activity. CME Solana futures launched in 2024 "
            "providing institutional positioning visibility. Staking yield (~6-7% nominal) is meaningful but staked ETH earns inflationary "
            "rewards. Position sizing must account for the high beta — 60%+ drawdowns have been common in prior cycles and remain "
            "plausible. ETF approval timeline drives tactical positioning; multiple filings (VanEck, 21Shares, Bitwise, Canary, others) "
            "create cascading approval-decision dates through 2025."
        ),
        "positioning_lens": ["on_chain", "derivatives", "etf_flows", "staking"],
    },

    # ──────────────────────────────────────────────────────────────────────
    # ZCASH
    # ──────────────────────────────────────────────────────────────────────
    "zec": {
        "cases": {
            "bull": [
                "Genuine financial-privacy need in increasingly surveilled digital economy",
                "Cryptographic technology genuinely sophisticated (zk-SNARKs); foundational to broader crypto innovation",
                "Bitcoin-like scarcity model with 21M cap and halving schedule",
                "Optionality on regulatory reassessment toward selective-disclosure privacy mechanisms",
                "Thin liquidity means small flow shifts can drive outsized moves",
            ],
            "bear": [
                "Regulatory hostility intensifies; FATF and major jurisdictions push toward more restriction",
                "Exchange delistings continue to constrain accessibility and liquidity",
                "Adoption has lagged Bitcoin (store-of-value) and Monero (privacy-coin) categories",
                "Concentrated ownership creates supply-pressure tail risk from large holder distributions",
                "Existential risk from criminalization or severe restriction of private cryptocurrency",
            ],
            "flat": [
                "Holds existing market position without significant adoption growth",
                "Range-bound trading punctuated by regulatory news events",
                "Crypto-cycle beta dominates absent ZEC-specific catalysts",
            ],
        },
        "trading_environment": (
            "Zcash trades with extreme volatility shaped by low liquidity — moves of 10-20% in a single session are not uncommon on "
            "modest flows. The asset's high beta to broader crypto-market moves means alt-coin rallies tend to include ZEC, but ZEC "
            "underperformance is the persistent pattern. Major exchange listing/delisting announcements move the price disproportionately "
            "given the thin float. Position sizing should be small relative to other crypto allocations given the genuine binary regulatory "
            "tail risks. Shielded-pool adoption metrics (the share of ZEC actually held in privacy-preserving addresses vs transparent "
            "addresses) is the cleanest measure of genuine privacy use — recent data shows shielded share has grown but remains a "
            "minority of total supply. Grayscale Zcash Trust (ZCSH) provides one limited institutional channel; flows are small but "
            "informative. Slippage on entry and exit can be substantial for any meaningful position size."
        ),
        "positioning_lens": ["on_chain", "exchange_listings"],
    },

    # ──────────────────────────────────────────────────────────────────────
    # US REAL ESTATE
    # ──────────────────────────────────────────────────────────────────────
    "us_re": {
        "cases": {
            "bull": [
                "Fed easing cycle reduces financing costs and compresses cap rates; bond-proxy character benefits",
                "Data center demand from AI capex unprecedented; multi-year visibility from hyperscaler plans",
                "Industrial/logistics structurally supported by reshoring and e-commerce penetration growth",
                "Multifamily supply pipeline empty after 2024 deliveries; tightness building 2026+",
                "Public REITs trade at discounts to estimated NAV; private vehicles still adjusting",
            ],
            "bear": [
                "CRE debt refinancing wall ($2-2.5T maturing 2024-2027) at significantly higher rates",
                "Office sector continues to deteriorate; Class B obsolescence permanent",
                "Regional bank CRE exposure creates systemic risk; SVB/Signature-style stress could cascade",
                "Higher-for-longer rate environment persists; bond-proxy character cuts both ways",
                "Recession scenario depresses all property types simultaneously",
            ],
            "flat": [
                "Bifurcated sector — data centers/industrial/select residential offset office/regional retail weakness in aggregate",
                "Property-type dispersion creates pair-trade opportunities but flat broad-index performance",
                "Cap rates stabilize at new equilibrium; transaction volumes recover slowly",
                "Refinancing wall works through without systemic stress; distress concentrated in specific assets",
            ],
        },
        "trading_environment": (
            "US listed REITs have traded with substantial property-type dispersion that broad index performance fails to capture. Data "
            "center REITs (Digital Realty, Equinix) and industrial (Prologis, Rexford) have outperformed materially; office REITs (SL "
            "Green, Vornado, BXP) have suffered severe drawdowns from pre-pandemic highs. Single-family rental REITs (Invitation Homes, "
            "American Homes 4 Rent) and senior housing (Welltower, Ventas) have been resilient. Sector ETFs (VNQ, IYR) blend these "
            "stories, producing returns that diverge significantly from property-type specific positioning. CMBX office tranches have "
            "provided liquid short-office exposure for sophisticated investors. The REIT-bond correlation has tightened as the sector "
            "trades increasingly as a duration play; rate moves dominate short-term REIT performance. Regional bank stress indicators "
            "(KBW Bank Index, individual disclosures) provide CRE-credit signals before they appear in REIT pricing. Public-private REIT "
            "valuation gaps have created flow patterns: BREIT and similar private vehicles faced redemption pressure during the rate "
            "cycle; public REITs trade at discounts to estimated NAV. The structural winners (data centers especially) trade at premium "
            "multiples but with multi-year visibility."
        ),
        "positioning_lens": ["reit_flows", "cmbs_delinquencies", "regional_bank_stress"],
    },

    # ──────────────────────────────────────────────────────────────────────
    # INTL REAL ESTATE
    # ──────────────────────────────────────────────────────────────────────
    "intl_re": {
        "cases": {
            "bull": [
                "Japan reflation and corporate governance reform supports J-REITs; weak yen attracts foreign capital",
                "ECB easing cycle ahead of Fed supports European real estate financing conditions",
                "Constrained supply in major coastal Asian cities (Tokyo, Singapore, Hong Kong) supports values",
                "Indian real estate demand growth supported by urbanization and rising middle class",
                "Currency-driven foreign capital inflows benefit specific markets disproportionately",
            ],
            "bear": [
                "China property crisis weighs on Chinese-listed real estate and broader sentiment",
                "BoJ normalization eventually pressures Japanese property values via higher discount rates",
                "Regional dispersion masks pockets of severe stress; aggregate indices misleading",
                "Currency moves can dominate dollar-based returns regardless of underlying property performance",
                "European structural challenges (demographics, growth) constrain demand in some markets",
            ],
            "flat": [
                "Regional dispersion produces flat aggregate; each market trades on local fundamentals",
                "Currency moves average out over time across regions",
                "Tactical opportunities tied to specific country cycles rather than international real estate as a whole",
            ],
        },
        "trading_environment": (
            "International real estate trades with extreme regional dispersion that aggregate indices obscure. Japanese REITs (J-REITs) "
            "have outperformed materially through the reflation thesis; Chinese property has been a persistent drag. European real estate "
            "has been mixed with ECB easing providing some support against structural growth concerns. Currency moves frequently dominate "
            "dollar-based returns — Japanese property strength in local terms has been partially offset by weak yen for unhedged dollar "
            "investors. Currency-hedged international real estate exposures (DBEU, HEFA, HEWJ-style hedges) have produced different return "
            "profiles than unhedged. Foreign capital flows into specific markets — major Wall Street firms buying Japanese property at "
            "weak-yen prices, Singapore and Middle Eastern sovereign wealth funds active in Europe — create flow signals that often "
            "precede broader index moves. Country-specific events (BoJ meetings, China property stimulus announcements, ECB decisions) "
            "provide tactical entry points. Aggregate international real estate exposure is rarely the right way to express specific views."
        ),
        "positioning_lens": ["country_flows", "currency_hedge_demand"],
    },

    # ──────────────────────────────────────────────────────────────────────
    # EM EQUITY
    # ──────────────────────────────────────────────────────────────────────
    "em": {
        "cases": {
            "bull": [
                "Attractive valuations vs DM with persistent forward-PE discount of 30-40%",
                "Fed easing and dollar weakness historically the canonical EM rally setup",
                "India structural story (demographics, reforms, reshoring beneficiary) growing index weight",
                "Underowned positioning — many global allocators below EM benchmark — provides rally fuel",
                "EM ex-China decomposition increasingly available; reduces China-weight overhang for those who want it",
            ],
            "bear": [
                "Dollar strength persists; financial conditions tight for EM corporates and sovereigns",
                "China overhang continues; geopolitical tensions add structural premium",
                "Higher volatility and governance risks; EM history of disappointing structural-growth theses",
                "Semiconductor cycle weakness hits Taiwan/Korea index weights (large index components)",
                "Specific country crises (Argentina, Turkey lira episodes) hit broader EM sentiment",
            ],
            "flat": [
                "Range-bound between attractive-valuation support and dollar-strength resistance",
                "Country-specific dispersion produces flat aggregate; India strength offset by China weakness",
                "Tactical opportunities tied to dollar cycles and Fed-path expectations",
            ],
        },
        "trading_environment": (
            "EM equities (EEM, VWO as broad ETFs, EMXC for ex-China) have traded substantially driven by the dollar cycle and Fed path. "
            "Country dispersion has been enormous: India has been a relative bright spot (the MSCI India Index has materially outperformed "
            "broader EM); China has been the dominant drag; Latin America has provided pockets of strength via attractive yields and "
            "commodity beta. The semiconductor weighting through Taiwan (TSMC) and Korea (Samsung, SK Hynix) means tech-cycle dynamics "
            "drive a significant share of broad EM index returns. Capital flow data (IIF weekly tracker, EPFR) provides the cleanest "
            "positioning signal; sustained outflows have historically been productive contrarian setups. Dollar moves dominate short-term "
            "returns. EM credit (EMBI) provides confirming signals — EM equity rallies generally require both attractive equity valuations "
            "and benign EM credit conditions. The EM ex-China decomposition has become important — many global allocators want EM "
            "exposure without the China component, supporting EMXC flows. Country-specific events (RBI meetings, Banxico decisions, BCB "
            "policy, elections in major EM countries) provide tactical entry points but rarely move the broad index."
        ),
        "positioning_lens": ["fund_flows", "em_credit_spreads", "dollar"],
    },

    # ──────────────────────────────────────────────────────────────────────
    # CHINA
    # ──────────────────────────────────────────────────────────────────────
    "china": {
        "cases": {
            "bull": [
                "Valuations at deep discounts to global peers — world-class tech and consumer companies at depressed multiples",
                "Foreign positioning at multi-year lows; underowned status provides rally fuel on any sentiment shift",
                "Stimulus capacity remains; CCP demonstrated willingness to support markets via 'national team' interventions",
                "Property crisis stabilization (price declines moderating) reduces tail risk",
                "Trump tariff pressure could paradoxically force more aggressive Chinese stimulus response",
            ],
            "bear": [
                "Structural headwinds (property, demographics, debt, state direction) suggest cheap-for-reason valuations",
                "Geopolitical tensions persist and intensify; US-China trade war 2.0 under Trump administration",
                "Consumer confidence damaged by property crisis remains depressed; saving rate elevated",
                "Capital flight pressure on yuan limits PBoC monetary stimulus capacity",
                "Cheap valuations have been cheap for years; value trap risk substantial",
            ],
            "flat": [
                "Range-bound trading on policy intervention and disappointment cycles",
                "Stimulus announcements drive sharp rallies that fade on implementation disappointment",
                "Foreign flows oscillate around bearish baseline",
                "Country trades on its own dynamics largely independent of broader EM and US",
            ],
        },
        "trading_environment": (
            "Chinese equities (MCHI, FXI for broad; KWEB for internet/tech; CQQQ for tech specifically) have been among the most policy-"
            "driven asset classes in global markets. Sharp rallies on stimulus announcements (the late-September 2024 stimulus package "
            "produced one of the most violent multi-day rallies in any major market in recent memory) have repeatedly faded on "
            "implementation disappointment. Foreign positioning has been at multi-year lows by various metrics, including Stock Connect "
            "northbound flows. The 'national team' (state-affiliated funds intervening to support markets) is an unusual price-support "
            "dynamic absent in other major markets. Hong Kong-listed H-shares vs ADR-listed US shares vs onshore A-shares often diverge "
            "substantially based on capital-flow accessibility. Hang Seng Index leadership periodically diverges from mainland CSI 300. "
            "Volatility has been extreme — VIX-equivalent measures for Chinese equities have been multiples of US VIX. Tactical "
            "positioning around major political events (Politburo, Central Economic Work Conference in December, Two Sessions in March, "
            "Plenum meetings) has produced productive setups when positioning is extreme in either direction. The relationship between "
            "Chinese equities and the yuan is informative — yuan weakness with equity rallies signals managed currency relative to "
            "stimulus-driven asset prices."
        ),
        "positioning_lens": ["stock_connect_flows", "national_team", "policy_calendar"],
    },

    # ──────────────────────────────────────────────────────────────────────
    # DXY (Dollar)
    # ──────────────────────────────────────────────────────────────────────
    "dxy": {
        "cases": {
            "bull": [
                "Fed maintains higher-for-longer relative to peers; rate differential bid persists",
                "US economic outperformance ('US exceptionalism') continues; growth differential supports dollar",
                "Trump tariff agenda dollar-supportive — tariffs protect US growth at trading-partner expense",
                "Safe-haven demand during risk-off episodes; deepest, most liquid asset markets",
                "Carry-trade positioning continues to flow toward elevated US yields",
            ],
            "bear": [
                "Fed eases more than peers as US growth eventually moderates; rate differential narrows",
                "Dollar overvaluation versus PPP (10-20% rich on most measures)",
                "Carry-trade unwinds (August 2024-style yen episode) can produce violent dollar weakness",
                "Synchronized global growth scenarios draw capital from dollar safety to higher-beta foreign markets",
                "De-dollarization narrative slowly erodes structural demand over multi-decade horizon",
            ],
            "flat": [
                "Range-bound between bull and bear factors; managed within current trading bands",
                "Rate-differential moves offset by safe-haven and growth dynamics",
                "Tactical opportunities tied to specific Fed-vs-peer-central-bank surprises",
            ],
        },
        "trading_environment": (
            "The dollar trades in multi-year cycles with the post-2014 bull market now exceeding a decade — among the longest dollar bull "
            "runs on record, raising mean-reversion questions. Within the bull regime, intermediate-cycle moves of 5-10% are common. The "
            "DXY composition heavily weights EUR (~57%) and JPY (~14%); these two currencies dominate short-term DXY moves. The broader "
            "Trade-Weighted Dollar Index (DTWEXBGS in FRED) is more comprehensive but tracks DXY closely on most horizons. CFTC dollar "
            "index futures positioning (also available for individual currencies — EUR, JPY, GBP, AUD futures positioning) provides "
            "tactical signals; extreme net positions have historically marked turning points. Carry-trade unwinds produce violent moves "
            "that overshadow longer-cycle dynamics — the August 2024 yen carry-trade unwind was the most dramatic recent example. Fed "
            "policy expectations (Fed funds futures, SOFR futures) drive the rate-differential channel of dollar demand. Risk-off "
            "episodes typically produce dollar strength regardless of underlying US-specific conditions. The dollar's role as the "
            "denominator for essentially every other macro asset means dollar moves cascade through commodity prices (priced in dollars "
            "globally), EM equity returns, gold price action, and Treasury demand from foreign holders."
        ),
        "positioning_lens": ["cot", "rate_differentials", "fed_path"],
    },

    # ──────────────────────────────────────────────────────────────────────
    # EUR
    # ──────────────────────────────────────────────────────────────────────
    "eur": {
        "cases": {
            "bull": [
                "Growth gap with US narrows as Eurozone bottoms; tightening differential",
                "ECB pauses cutting cycle ahead of Fed; relative rate move supports EUR",
                "Current account surplus structurally supportive (Eurozone runs persistent goods surplus)",
                "Risk-on environments favor EUR as higher-beta currency vs USD",
                "Peripheral stress remains contained; Italian and Spanish spreads behaved",
            ],
            "bear": [
                "Structural growth underperformance vs US continues; Eurozone trapped in low-growth regime",
                "ECB easing accelerates ahead of Fed; differential widens against EUR",
                "Energy vulnerability persists; geopolitical disruption to Norwegian/Algerian gas would pressure EUR",
                "Risk-off weakness; EUR sells off in stress episodes",
                "Trump tariffs hit EUR-area exports disproportionately",
            ],
            "flat": [
                "Range-bound between US-Eurozone growth gap considerations",
                "ECB-Fed differential settles into stable spread",
                "EUR/USD trades in 1.04-1.12 band absent specific catalysts",
            ],
        },
        "trading_environment": (
            "EUR/USD has been the most-traded currency pair globally and dominates DXY composition. The pair has held a downward bias "
            "through the US growth outperformance era. ECB cuts ahead of Fed cuts in 2024 created near-term pressure; whether this "
            "differential persists or narrows depends on relative path expectations. Peripheral spread stress (Italian BTP-Bund spread, "
            "Spanish 10Y-Bund) provides eurozone-cohesion signals — wide spreads pressure EUR independently of broader USD direction. "
            "CFTC EUR positioning swings between extremes and has marked turning points historically. ECB and Fed meetings drive short-"
            "term moves; the relative hawkishness comparison is the cleanest tactical signal. Energy prices (TTF natural gas, Brent oil) "
            "create EUR-specific channels given European import dependence. Risk-on/off dynamics consistently favor USD over EUR. "
            "Carry-trade dynamics — EUR has been a borrowed currency at times given lower ECB rates than Fed — affect short-term flows."
        ),
        "positioning_lens": ["cot", "ecb_fed_differential", "peripheral_spreads"],
    },

    # ──────────────────────────────────────────────────────────────────────
    # JPY
    # ──────────────────────────────────────────────────────────────────────
    "jpy": {
        "cases": {
            "bull": [
                "BoJ normalization (hike cycle) narrows rate differential with Fed",
                "Yen significantly undervalued vs PPP and historical averages",
                "Safe-haven appeal in an elevated-risk geopolitical environment",
                "Wage-price spiral evidence (shunto wage rounds) supports BoJ normalization narrative",
                "Carry-trade positioning unwinds support yen strength in stress episodes",
            ],
            "bear": [
                "Fed-BoJ rate differential remains wide despite narrowing; carry incentive persists",
                "BoJ moves cautiously; normalization slower than expected",
                "Japan investor outflows continue as Japanese institutions seek foreign yields",
                "Risk-on episodes favor higher-yielding currencies over JPY",
                "Ministry of Finance intervention only caps weakness rather than reversing trend",
            ],
            "flat": [
                "Range-bound trading on BoJ pace expectations",
                "Carry-trade flows balance fundamental yen-undervalue case",
                "Volatility elevated but mean-reverting absent specific catalysts",
            ],
        },
        "trading_environment": (
            "The yen has traded with extreme volatility through the post-YCC era. The August 2024 yen carry-trade unwind produced one "
            "of the most dramatic short-term currency moves in years — USD/JPY moved from 162 to 142 in weeks, triggering broad risk-"
            "asset selloffs as carry positions liquidated globally. The episode highlighted both yen's structural undervalue and the "
            "scale of carry-trade positioning that had built up. Ministry of Finance intervention (multiple episodes in 2022-2024 with "
            "varied effectiveness) has capped extreme yen weakness without reversing the multi-year trend. BoJ meetings drive substantial "
            "moves on every guidance shift. JGB 10Y yields (now freely-moving post-YCC) have become an additional channel for yen "
            "dynamics. CFTC JPY futures positioning shows speculative short yen has been a crowded trade at times; extreme short "
            "positioning has marked turning points. Japanese investor outflows (visible in MoF International Transactions in Securities "
            "data, weekly) provide a structural-flow signal. The yen's safe-haven function remains intact — yen strengthens in genuine "
            "risk-off episodes — but is partially obscured by carry-trade dynamics."
        ),
        "positioning_lens": ["cot", "boj_path", "carry_positioning", "mof_intervention"],
    },

    # ──────────────────────────────────────────────────────────────────────
    # CNY
    # ──────────────────────────────────────────────────────────────────────
    "cny": {
        "cases": {
            "bull": [
                "PBoC defends currency stability through fix management; tail risks limited by active management",
                "Trade surplus remains structurally supportive",
                "Capital controls limit outflow pressure compared to free-floating EM currencies",
                "Stimulus delivers and Chinese growth picks up; CNY supported by improving fundamentals",
                "US-China trade resolution reduces tariff-related depreciation pressure",
            ],
            "bear": [
                "Tariff escalation under Trump triggers managed devaluation response from PBoC",
                "Chinese growth weakness continues; capital outflow pressure builds",
                "Rate differential with US remains unfavorable for CNY; PBoC easing widens gap",
                "Property crisis stabilization elusive; consumer confidence remains depressed",
                "Geopolitical tensions reduce foreign capital appetite for Chinese assets",
            ],
            "flat": [
                "PBoC manages gradual depreciation within tolerable range",
                "Range-bound trading within band as PBoC actively manages",
                "CNH-CNY spread provides real-time gauge of pressure",
            ],
        },
        "trading_environment": (
            "The yuan is a managed currency — the PBoC sets a daily reference fix (9:15 AM Beijing time) and intervenes via the trading "
            "band, reserve operations, and macroprudential measures. The CNH-CNY spread (offshore yuan in Hong Kong vs onshore yuan in "
            "China) is the cleanest real-time gauge of market pressure on the official rate; persistent CNH weakness vs CNY signals "
            "depreciation pressure being absorbed by PBoC management. Daily fix moves are the primary signal — fixes weaker than market "
            "expectation signal PBoC depreciation tolerance; stronger fixes signal stability commitment. PBoC monetary easing widens the "
            "rate differential with the US, creating tension between domestic stimulus needs and currency stability. Tariff developments "
            "are the primary geopolitical channel — historical pattern has been managed CNY weakening following tariff escalations, "
            "reaching tolerance limits before PBoC re-engages stability measures. SAFE capital flow data (monthly with lag) provides "
            "structural-flow context. Trade balance data informs the fundamental support level. The CNY's role in Asian FX (where many "
            "currencies trade with CNY as anchor) means CNY weakness cascades through Asian EM. The relationship between CNY and copper, "
            "iron ore, and broader China-proxy assets is bidirectional — they tend to move together but with CNY often leading."
        ),
        "positioning_lens": ["cnh_cny_spread", "pboc_fix", "trade_balance"],
    },

}
