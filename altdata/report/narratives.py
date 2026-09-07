"""
Per-asset deep-dive narratives — the content for the dashboard's fourth tab.

Each asset has five fields:
  - performance     : how the asset has behaved and what's driven recent moves
  - supply          : supply-side structural drivers
  - demand          : demand-side structural drivers
  - outlook         : forward view, including upcoming catalysts and events
  - correlation_txt : the textbook correlation expectation to equities
                      (the actual current correlation is computed live and
                       contrasted against this in the dashboard)

These are templates. Each weekly run can refresh them via the report pipeline
once the live news/data feeds are wired (FRED, news API, on-chain). Until then
they capture the durable structural story for each asset, which doesn't move
week to week — the dashboard layers the live correlation read on top of the
textbook view to surface any divergence.

Style guide: institutional research register, full paragraphs (3–6 sentences),
no bullet lists, no marketing voice. Honest about uncertainty.
"""

NARRATIVES = {

    # ─── METALS ────────────────────────────────────────────────────────────
    "gold": {
        "performance": (
            "Gold has spent the last two years in a powerful structural advance, repricing higher despite a "
            "high-real-yield environment that would historically have capped it. The classic real-yield "
            "framework — where gold rallies when 10Y TIPS yields fall and sells off when they rise — has "
            "broken down since 2022. Recent price action has been driven less by Western financial demand "
            "(ETF flows have been mixed) and more by relentless central bank accumulation and Asian "
            "physical demand, two pools that are largely insensitive to US real rates."
        ),
        "supply": (
            "Annual mine output runs around 3,500-3,700 tonnes and grows only 1-2% in good years, "
            "constrained by declining ore grades, the rarity of new deposits, and lead times exceeding a "
            "decade from discovery to production. Recycling provides the swing supply — roughly "
            "1,100-1,300 tonnes annually, counter-cyclical because high prices coax more jewelry scrap "
            "back to market. The all-in sustaining cost of marginal producers establishes a soft floor "
            "near $1,300-1,500/oz, but the supply ceiling is effectively rigid in the short run."
        ),
        "demand": (
            "Central bank purchases have been the dominant marginal buyer post-2022, running above "
            "1,000 tonnes annually — roughly double the prior decade's pace — led by China, Turkey, "
            "India, and Poland. The strategic logic is reserve diversification away from dollar assets "
            "after the freezing of Russia's reserves demonstrated the political risk of dollar holdings. "
            "Jewelry demand (India and China) is large but price-elastic; investment demand via ETFs is "
            "cyclical and Western-driven, and was notably absent from much of the 2023-24 rally — meaning "
            "Western ETF re-engagement represents latent upside fuel."
        ),
        "outlook": (
            "The structural bull case rests on continued central bank diversification, fiscal-dominance "
            "concerns in developed markets, and a re-engagement of Western investors who remain "
            "underweight. The principal risks are a genuine restoration of real-yield discipline or "
            "fiscal credibility, which would remove gold's support, and the possibility that much of the "
            "de-dollarization narrative is now priced. Catalysts to monitor: monthly central bank "
            "purchase data from the World Gold Council, FOMC decisions and dot-plot revisions, US CPI "
            "and PCE prints, PBoC reserve disclosures, and any BRICS-related de-dollarization news."
        ),
        "correlation_txt": (
            "Textbook view: gold is negatively correlated to US equities during risk-off episodes (its "
            "safe-haven role) and largely uncorrelated in calm markets. The relationship to bonds is "
            "more nuanced — historically positive via the shared real-rate channel, but loosened by the "
            "central bank bid."
        ),
    },

    "silver": {
        "performance": (
            "Silver has tracked gold's directional moves with materially higher beta, as expected — its "
            "industrial component (roughly 55-60% of demand) amplifies cyclical swings while its precious-"
            "metal identity ties it to the gold complex. The gold-silver ratio has remained structurally "
            "elevated above 80, suggesting silver's mean-reversion case has not fully played out despite "
            "the metals rally. Above-ground inventories at COMEX and LBMA have drawn down over recent "
            "quarters, consistent with the persistent industrial deficit the Silver Institute has flagged."
        ),
        "supply": (
            "About 70% of silver comes as a byproduct of base-metal mining (lead, zinc, copper, gold), "
            "which makes supply nearly insensitive to the silver price itself — production decisions are "
            "driven by host-metal economics. Annual mine supply runs around 820-830 million ounces with "
            "recycling adding 180-200 million more. This inelasticity is the crux of the bull case: "
            "demand can grow without supply responding, drawing down above-ground inventories."
        ),
        "demand": (
            "Industrial demand has surged, dominated by solar photovoltaics — silver is used in the "
            "conductive paste of solar cells, and despite ongoing thrifting, the scale of global solar "
            "installation has made solar a structural sink. Electronics, EVs (which use more silver than "
            "ICE vehicles), and 5G round out industrial use. Investment demand via SLV and bars/coins is "
            "the cyclical swing factor, and jewelry demand from India is large but price-sensitive."
        ),
        "outlook": (
            "The bull thesis combines silver as a high-beta gold proxy with the structural deficit story "
            "from solar and electrification. Risks: silver is acutely sensitive to global manufacturing "
            "cycles and a China-led industrial slowdown would hit it hard; ongoing thrifting in solar "
            "cells could blunt growth; and the gold-silver ratio has stayed elevated for years, "
            "suggesting old mean-reversion playbooks may be broken. Catalysts: gold-silver ratio "
            "behavior, COMEX inventory drawdowns, Chinese solar manufacturing data, and global "
            "manufacturing PMIs."
        ),
        "correlation_txt": (
            "Textbook view: silver behaves like a higher-beta gold during precious-metals advances "
            "but also carries genuine cyclical sensitivity, so it tends to have a higher and more "
            "positive correlation to equities than gold does, particularly in industrial-cycle moves."
        ),
    },

    "copper": {
        "performance": (
            "Copper has traded sideways-to-higher with significant volatility, caught between the "
            "powerful electrification demand thesis and the headwind of Chinese property weakness. "
            "The cyclical Chinese signal (where China consumes roughly half of global copper) has "
            "kept a lid on prices even as the structural case strengthens. Treatment and refining "
            "charges have compressed materially — a real-time indicator that smelters are competing "
            "for scarce concentrate, signaling tightening mine supply."
        ),
        "supply": (
            "Production is concentrated in Chile, Peru, and the rapidly growing DRC, and faces well-"
            "documented constraints: ore grades at major mines are in secular decline, new world-class "
            "deposits are rare, and development timelines from discovery to first production routinely "
            "exceed 10-20 years. Years of underinvestment during the prior low-price era have left a "
            "thin pipeline of new projects. Mine disruptions — strikes, water access in arid mining "
            "regions, political interventions — are recurring near-term risks."
        ),
        "demand": (
            "Chinese demand is the dominant cyclical variable. The property-sector downturn has weighed "
            "on traditional construction-related copper, but China's aggressive buildout of grid "
            "infrastructure, renewable capacity, and EV production has provided a substantial offset. "
            "Structural demand sits on EVs (which use roughly 2.5-4x the copper of ICE vehicles), grid "
            "expansion globally, solar and wind installations, and the emerging AI data-center vector "
            "(power and cooling infrastructure are enormously copper-intensive)."
        ),
        "outlook": (
            "The structural bull consensus is unusually strong: electrification-driven demand surge "
            "colliding with slow-to-respond supply points to a multi-year deficit later this decade. "
            "Lead times on new supply mean the deficit is hard to resolve quickly even with high "
            "prices. The cyclical caution is the near-term China and global-manufacturing risk. "
            "Catalysts: Chinese property data and stimulus announcements, manufacturing PMIs, exchange "
            "inventories at LME/COMEX/SHFE, mine-supply disruptions, and grid-investment policy."
        ),
        "correlation_txt": (
            "Textbook view: copper is one of the most pro-cyclical commodities — strongly positively "
            "correlated to equities during global growth phases, with the relationship tightening "
            "around China-cycle inflection points. Negative correlation episodes are rare and usually "
            "short-lived."
        ),
    },

    # ─── ENERGY ────────────────────────────────────────────────────────────
    "oil": {
        "performance": (
            "Crude has held a managed range broadly defined by OPEC+ defending a floor through "
            "voluntary cuts (with Saudi Arabia bearing the largest share) and US shale capping the "
            "upside through its quick-cycle responsiveness. The futures curve has oscillated between "
            "modest backwardation (signaling tightness) and contango, with the geopolitical risk "
            "premium contributing periodic spikes that have generally faded."
        ),
        "supply": (
            "OPEC+ controls roughly 40% of global supply and currently holds 3-4 million barrels/day "
            "of spare capacity, concentrated in Saudi Arabia — the market's shock absorber. US shale "
            "production at record levels above 13 million b/d remains the swing producer, but the "
            "shift from growth-at-all-costs to capital discipline has tempered the historical price-"
            "response curve. Sanctioned barrels from Russia, Iran, and Venezuela add a separate "
            "supply layer where enforcement intensity directly affects available crude."
        ),
        "demand": (
            "Global demand sits around 102-103 million b/d with modest growth concentrated in emerging "
            "Asia, particularly India. China's trajectory is the single most-watched variable: post-"
            "pandemic recovery, property weakness, and rapid EV adoption pull in different directions. "
            "Petrochemicals and jet fuel provide offsetting growth against eroding gasoline demand. "
            "The structural question is when (and whether) a demand peak arrives."
        ),
        "outlook": (
            "The managed-range view holds as a base case: OPEC+ defends a floor, shale and demand "
            "concerns cap the upside, breakouts require either supply shocks or recession. Bull case: "
            "underinvestment in long-cycle supply, shrinking spare capacity, resilient EM demand — "
            "the market is one disruption from a spike. Bear case: EV adoption acceleration, demand "
            "peak, and ample OPEC+ spare capacity. Catalysts: OPEC+ meetings, EIA weekly inventories, "
            "IEA/OPEC monthly reports, Chinese activity data, Middle East geopolitics."
        ),
        "correlation_txt": (
            "Textbook view: crude is moderately positively correlated to equities during global growth "
            "phases via the demand channel, but the relationship is noisy and can invert in supply-"
            "shock episodes (where high oil prices are bearish for equities). A supply-driven spike "
            "should show negative correlation; a demand-led rally should show positive correlation."
        ),
    },

    "natgas": {
        "performance": (
            "Natural gas has been the most volatile of the major energy commodities, oscillating "
            "violently on weather and storage. Henry Hub has periodically traded near multi-year lows "
            "on robust associated-gas supply meeting mild weather, only to spike on cold-snap forecasts "
            "or storage surprises. The structural transformation underway — the LNG export ramp tying "
            "US prices to global TTF/JKM — has progressed but has not yet fully overpowered the "
            "domestic weather-and-storage dynamic."
        ),
        "supply": (
            "US production sits at record levels, much of it associated gas — a byproduct of oil "
            "drilling in basins like the Permian — which means a significant share of supply is "
            "insensitive to the gas price itself. Dedicated dry-gas production (Marcellus, Haynesville) "
            "responds to gas economics. Pipeline takeaway constraints can strand supply in producing "
            "regions while creating tightness elsewhere. The pace of LNG export capacity expansion is "
            "effectively a structural demand increase that progressively absorbs domestic oversupply."
        ),
        "demand": (
            "Power generation is the largest and growing category as gas displaces coal and backs up "
            "intermittent renewables; summer cooling load has made gas a two-season demand story. "
            "Residential and commercial heating is highly weather-sensitive, peaking in winter. LNG "
            "exports are the structural growth engine. An emerging vector is electricity demand from "
            "data centers and AI computing, which is reviving load growth after years of stagnation."
        ),
        "outlook": (
            "Structural bull case: LNG export ramp and data-center power demand progressively absorb "
            "the chronic oversupply, supporting higher and less volatile prices over time. Near-term "
            "bear case: recurring oversupply, robust associated-gas output, weather risk, and the "
            "associated-gas dynamic that makes supply slow to respond to low prices. Catalysts: "
            "weekly EIA storage reports (Thursdays), weather forecasts, LNG terminal commissioning "
            "and feedgas demand changes, data-center buildout announcements."
        ),
        "correlation_txt": (
            "Textbook view: natural gas has historically been weakly correlated to equities — its "
            "drivers (weather, storage, regional supply-demand) are largely idiosyncratic to the gas "
            "complex. Correlations tend to be near zero with periodic positive spikes during broad "
            "energy moves."
        ),
    },

    # ─── COMMODITIES ───────────────────────────────────────────────────────
    "agri": {
        "performance": (
            "Agricultural commodities have shown wide dispersion: softs like cocoa and coffee saw "
            "dramatic supply-driven rallies on disease and weather in West Africa and Brazil, while "
            "grains traded heavily on ample harvests and elevated stocks. The broad agri basket masks "
            "this dispersion entirely — at any given moment, some crops may be in glut while others "
            "are in acute deficit. The El Niño/La Niña cycle has been a meaningful macro-weather "
            "overlay affecting global growing conditions across multiple seasons."
        ),
        "supply": (
            "Weather is the dominant swing factor — droughts, floods, frosts, heat — governed by "
            "planting and harvest calendars across both hemispheres. Production concentration matters: "
            "US/Brazil/Argentina dominate corn and soy; the Black Sea is critical for wheat; Brazil "
            "leads sugar and coffee; West Africa dominates cocoa. Stocks-to-use ratios are the key "
            "tightness gauge per crop. Input costs (fertilizer, energy) affect both planting "
            "economics and yields."
        ),
        "demand": (
            "Food demand is relatively inelastic and growing with population and dietary upgrading "
            "in emerging markets — rising meat consumption multiplies grain demand via animal feed. "
            "The biofuel linkage is policy-sensitive: a substantial share of US corn goes to ethanol; "
            "soybean and other vegetable oils feed biodiesel. This ties agri demand to energy prices "
            "and government mandates."
        ),
        "outlook": (
            "Structural bull thesis: population growth, dietary upgrading, climate volatility, "
            "constrained arable land, agri as an inflation hedge. Near-term picture is crop-specific "
            "and often bearish for major grains when harvests are good; supply-constrained softs can "
            "soar independently. The broad agri thesis is best implemented through targeted crop "
            "selection rather than basket exposure (which suffers from contango/roll costs). "
            "Catalysts: monthly USDA WASDE reports, weather forecasts in key growing regions, "
            "biofuel policy, Black Sea trade flows, El Niño/La Niña status."
        ),
        "correlation_txt": (
            "Textbook view: agri commodities have low correlation to equities — their drivers "
            "(weather, seasons, crop-specific supply-demand) are largely orthogonal to financial "
            "markets, which is why agri is often cited as a diversifier."
        ),
    },

    # ─── CRYPTO ────────────────────────────────────────────────────────────
    "btc": {
        "performance": (
            "Bitcoin has undergone a regime change in its demand structure with the launch and growth "
            "of US spot ETFs, which opened institutional and wealth-management distribution at scale. "
            "BlackRock's IBIT in particular has accumulated significant assets, and the steady ETF bid "
            "has materially changed cycle dynamics — the historical four-year halving rhythm now "
            "competes with persistent institutional accumulation. Corporate treasury adoption, with "
            "Strategy (formerly MicroStrategy) the most prominent example, adds a second structural "
            "buyer pool."
        ),
        "supply": (
            "Bitcoin's supply schedule is the most predictable of any asset: hard-capped at 21 million "
            "coins with block rewards halving roughly every four years. Following the 2024 halving, "
            "issuance dropped to ~450 new coins per day — well under 1% annually. Approximately 19.8M "
            "of 21M coins have been mined. On-chain dynamics matter as much as new issuance: long-"
            "term holder supply and declining exchange balances both reduce liquid float available "
            "to absorb demand shocks."
        ),
        "demand": (
            "Spot ETF flows have become the dominant and most-watched demand signal — sustained "
            "inflows represent steady, price-insensitive accumulation. Corporate treasuries and "
            "growing (still nascent) sovereign interest add long-horizon strategic demand. The "
            "traditional retail and risk-on speculation channel remains, but Bitcoin increasingly "
            "trades as a macro asset — high-beta, liquidity-sensitive, rallying when financial "
            "conditions ease and selling off in liquidity crunches."
        ),
        "outlook": (
            "Institutional bull consensus has strengthened: 'digital gold' framing, fixed supply, "
            "growing adoption, debasement hedge in a high-deficit world. Skeptic case: persistent "
            "volatility, tight risk-asset correlation undermining the safe-haven claim, regulatory "
            "uncertainty, possibility that the four-year cycle still dictates eventual sharp "
            "drawdowns. Catalysts: daily ETF flow data, FOMC and macro liquidity, regulatory "
            "developments (stablecoin legislation, market structure, accounting), corporate-treasury "
            "and sovereign-adoption news."
        ),
        "correlation_txt": (
            "Textbook view (early-cycle): Bitcoin is uncorrelated to equities — a separate asset "
            "class. Reality of recent years: Bitcoin trades as a high-beta risk asset, with positive "
            "correlation to equities (especially Nasdaq) tightening during stress episodes. The "
            "'uncorrelated digital gold' claim is contradicted by the actual rolling correlation, "
            "which routinely sits in the 0.4-0.7 range."
        ),
    },

    "eth": {
        "performance": (
            "Ethereum has materially underperformed Bitcoin through the post-ETF era, an "
            "underperformance that crystallized the value-capture debate around Layer-2 scaling. "
            "Spot ETH ETF flows have run well behind Bitcoin's, reflecting the market's greater "
            "difficulty articulating ETH's value proposition to traditional allocators. Network "
            "activity has remained strong but has progressively migrated to L2s, reducing the base-"
            "layer fee burn and weakening the deflationary narrative."
        ),
        "supply": (
            "Post-Merge, ETH issuance flows to stakers and a portion of transaction fees is burned "
            "under EIP-1559. When network activity is high, burning can exceed issuance, making ETH "
            "net deflationary; when activity is low or migrates to L2s, ETH experiences mild "
            "inflation. The staking ratio — share of supply locked in staking — removes liquid "
            "float, though staked ETH earns the inflationary rewards. Staking yield competes with "
            "Treasury yields for capital."
        ),
        "demand": (
            "ETH is required as gas for Ethereum transactions and as collateral across DeFi. The "
            "staking yield attracts holders seeking on-chain returns. Structural demand drivers "
            "include DeFi total value locked, the explosion of stablecoins (largely issued on "
            "Ethereum and its L2s), and the emerging tokenization of real-world assets. The "
            "central question is value capture — whether L2 activity that ultimately settles to "
            "Ethereum drives sufficient demand for ETH itself."
        ),
        "outlook": (
            "Bull case: Ethereum as the dominant decentralized settlement layer capturing value from "
            "DeFi, stablecoins, and RWA tokenization; staking yield; deflationary supply potential; "
            "network effects of the largest developer ecosystem. Bear case: value-capture problem if "
            "L2s and competitors capture activity and fees; persistent underperformance vs Bitcoin; "
            "dilution of the deflationary narrative; competition from faster L1s. Catalysts: ETH "
            "ETF flow trends, protocol upgrades, RWA tokenization milestones, staking-yield "
            "dynamics, ETH/BTC ratio for rotation signals."
        ),
        "correlation_txt": (
            "Textbook view: Ethereum trades with high correlation to Bitcoin and to risk assets, "
            "typically 0.5-0.8 to BTC and similar levels to Nasdaq. Genuinely independent moves are "
            "rare and usually tied to protocol-specific catalysts."
        ),
    },

    "sol": {
        "performance": (
            "Solana has been the highest-beta major crypto asset, leading alt-season rallies with "
            "explosive gains and suffering correspondingly deep drawdowns in risk-off phases. The "
            "performance gap with Bitcoin has been wide in both directions. Network reliability has "
            "improved meaningfully from the historical outage cadence, supporting the institutional "
            "narrative, though concerns persist. DEX trading volume has periodically rivaled or "
            "exceeded Ethereum's, providing real on-chain activity to point to beyond speculation."
        ),
        "supply": (
            "SOL has an inflationary schedule with disinflation toward a long-term floor — new "
            "supply is issued as staking rewards. The staking ratio is high, securing the network "
            "and reducing liquid float though staked tokens earn the inflationary rewards that "
            "maintain proportional share. Transaction fees are minimal by design (the core value "
            "proposition) so there's limited fee-burning to offset issuance — value accrual depends "
            "more on demand growth than supply scarcity."
        ),
        "demand": (
            "Demand derives from use as gas/settlement for high-throughput applications: DEX volume, "
            "memecoin activity (controversial but real on-chain activity), consumer apps, payments "
            "experiments, and DePIN (decentralized physical infrastructure). The case is mainstream "
            "consumer crypto adoption — the chain fast and cheap enough for real-world applications. "
            "Spot Solana ETF filings represent a significant prospective demand catalyst that would "
            "open institutional channels."
        ),
        "outlook": (
            "Bull case: leading contender to capture mainstream consumer crypto; demonstrated product-"
            "market fit in DEX and apps; ETF approval catalyst; Firedancer validator client improving "
            "performance. Bear case: historical reliability concerns; decentralization tradeoffs; "
            "inflationary supply; speculative-activity dependence; competition from Ethereum scaling "
            "and other L1s. Catalysts: Solana ETF approval timeline, Firedancer rollout, network "
            "uptime, DePIN traction, SOL/ETH ratio for rotation."
        ),
        "correlation_txt": (
            "Textbook view: Solana correlates strongly with Bitcoin and Ethereum, with even higher "
            "beta to crypto-market moves. Risk-on rallies show SOL outperforming BTC; risk-off "
            "episodes show it underperforming. Independent moves are tied to network events "
            "(outages, upgrades) or ETF developments."
        ),
    },

    "zec": {
        "performance": (
            "Zcash has substantially underperformed major crypto assets over multi-year horizons, "
            "trading thinly and with extreme volatility shaped by low liquidity. Performance is "
            "dominated by the binary regulatory question for privacy coins and by sentiment swings "
            "in the small privacy-coin segment. Protocol upgrades improving privacy guarantees and "
            "usability have continued, but adoption — measured by shielded-pool usage — has remained "
            "limited relative to the theoretical privacy use case."
        ),
        "supply": (
            "Zcash mirrors Bitcoin's monetary policy: 21M coin cap, periodic block-reward halvings, "
            "scarcity-driven model. A historically distinctive feature was the founders' / dev-fund "
            "reward allocation, which has been the subject of community governance debate. The "
            "shielded-versus-transparent supply split is a key adoption metric for the core privacy "
            "value proposition."
        ),
        "demand": (
            "Demand ties to financial-privacy use cases — users seeking transactional confidentiality "
            "transparent blockchains cannot offer. But the demand base is structurally constrained "
            "by regulatory and compliance pressures: privacy coins have been delisted from various "
            "regulated exchanges over money-laundering concerns. Competition from Monero (greater "
            "share, privacy-by-default vs ZEC's optional shielding) limits ZEC's privacy-coin "
            "market position. Institutional demand is minimal — limited to Grayscale's trust and "
            "speculative interest."
        ),
        "outlook": (
            "Bull case: genuine and growing financial-privacy need; superior cryptographic "
            "technology (zk-SNARKs pioneered foundational techniques); Bitcoin-like scarcity model; "
            "optionality on regulatory reassessment. Bear case (substantial): regulatory hostility, "
            "exchange delistings constraining accessibility; adoption that has lagged both Bitcoin "
            "and Monero; thin liquidity; existential risk from intensifying privacy-coin regulation. "
            "Catalysts: privacy-coin regulatory developments, exchange listings/delistings, protocol "
            "upgrades, shielded-pool adoption trends."
        ),
        "correlation_txt": (
            "Textbook view: Zcash correlates with the broader crypto complex (high beta to BTC) "
            "but with significant idiosyncratic moves driven by privacy-coin regulatory news. "
            "Thin liquidity can produce outsized moves disconnected from market direction."
        ),
    },

    # ─── REAL ESTATE ───────────────────────────────────────────────────────
    "us_re": {
        "performance": (
            "US listed REITs (VNQ) have repriced significantly as interest rates rose, with broad "
            "sector weakness masking extreme dispersion across property types. Office REITs have "
            "been hammered by persistent remote work and the obsolescence of older inventory, while "
            "data-center, industrial, and certain residential REITs have outperformed materially. "
            "Transaction volumes have been depressed by the bid-ask gap between buyers and sellers, "
            "and private real estate valuations have adjusted with a lag that created tension at "
            "large private vehicles."
        ),
        "supply": (
            "Supply varies dramatically by sector. Heavy speculative development in multifamily "
            "(particularly Sun Belt) has pressured rents in the near term. Office faces the opposite: "
            "oversupply of obsolete space colliding with structurally lower demand. Higher rates and "
            "construction costs have sharply curtailed new development across most sectors, sowing "
            "the seeds of future supply constraint — current oversupply in some segments is self-"
            "correcting as the development pipeline empties."
        ),
        "demand": (
            "Sharply bifurcated. Structurally favored: data centers (cloud and AI workloads), "
            "industrial/logistics (e-commerce and reshoring), certain residential (housing "
            "affordability). Structurally challenged: traditional office (permanent demand "
            "reduction from remote/hybrid work), some lower-quality retail. Across all segments, "
            "demand is heavily mediated by the rate environment and economic growth — lower rates "
            "would reduce financing costs, compress cap rates, and revive transactions."
        ),
        "outlook": (
            "Consensus is bifurcated rather than directional on 'real estate' broadly: constructive "
            "on data centers, industrial, select residential; cautious-to-bearish on traditional "
            "office. Broad sector hinges on rate relief; CRE debt refinancing wall is the principal "
            "systemic risk, with regional banks the focal point. Catalysts: FOMC and rate "
            "expectations, CPI/PCE, CRE debt refinancing outcomes, office-vacancy trends, data-"
            "center demand signals, regional-bank stress indicators."
        ),
        "correlation_txt": (
            "Textbook view: REITs are positively correlated to equities (they are equities) but with "
            "additional rate-sensitivity, so correlation is typically 0.5-0.7 to SPY with a separate "
            "negative correlation to Treasury yields. Stress in CRE credit can decouple REITs from "
            "broader equities — credit-sensitive moves are a key tell."
        ),
    },

    "intl_re": {
        "performance": (
            "International real estate has shown enormous regional dispersion. Japan has been a "
            "constructive case — reflation, corporate-governance reform, attractive valuations — "
            "though Bank of Japan normalization introduces risk. China property has been the principal "
            "drag, with the property crisis weighing on broader markets and on consumer wealth. "
            "European markets sit between, affected by the ECB easing cycle and varying local "
            "conditions. Currency moves materially affect dollar-based returns and overlay all of this."
        ),
        "supply": (
            "Entirely market-specific. Japan: disciplined urban supply alongside renewed demand. "
            "China: years of overbuilding created a massive overhang of unsold and unfinished "
            "housing — the heart of the crisis, taking years to clear. Europe: varied, with "
            "planning-constrained markets facing structural undersupply. Across developed markets, "
            "rate-driven development curtailment is setting up future supply tightness."
        ),
        "demand": (
            "Driven by local growth, demographics (aging in developed/Japan; younger/urbanizing in "
            "EM), local rate cycles, and foreign investment flows. Currency dimension matters: a "
            "cheap yen attracted foreign property buyers to Japan; currency strength can deter. "
            "Local rate easing (ECB) is improving demand conditions in Europe. Demographics and "
            "urbanization in EM provide a structural floor; aging in Japan creates senior-housing demand."
        ),
        "outlook": (
            "Consensus is necessarily fragmented: constructive on Japan (despite BoJ risk), cautious "
            "on China property (the principal tail risk), market-by-market for Europe. Catalysts: "
            "BoJ policy meetings, China property-support announcements and data, ECB meetings, and "
            "relevant FX moves (JPY, CNY, EUR)."
        ),
        "correlation_txt": (
            "Textbook view: international real estate correlates positively with US equities through "
            "the global growth channel but with significantly lower correlation than US REITs — "
            "regional drivers dominate. Currency effects can dominate dollar-based correlations, "
            "sometimes producing apparent decoupling that reflects FX rather than property "
            "fundamentals."
        ),
    },

    # ─── REGIONAL EQUITY ───────────────────────────────────────────────────
    "em": {
        "performance": (
            "EM equities (EEM) have been buffeted by the dollar and Fed cycle, the China weighting, "
            "and the global tech cycle through Taiwan and Korea. Index performance has been "
            "substantially driven by these few large constituents, masking strong dispersion across "
            "the developing world. India has been a relative bright spot on a structural-growth "
            "narrative; Latin American markets have offered attractive yields and commodity beta. "
            "EM has been a consensus underweight for many global allocators, leaving the asset class "
            "structurally underowned."
        ),
        "supply": (
            "As an equity asset class, 'supply' is equity issuance, index composition, and capital-"
            "market accessibility. The MSCI EM index is dominated by China, Taiwan, India, Korea — "
            "meaning 'EM' is substantially these. The tech/semiconductor weighting through Taiwan "
            "and Korea makes EM sensitive to the global tech cycle. Capital flows in and out are "
            "the supply-demand dynamic; EM can see sharp flow reversals in global risk-off episodes."
        ),
        "demand": (
            "Demand for EM is fundamentally a global capital-allocation decision, driven by relative "
            "valuations (EM trades at a persistent discount), relative growth, the dollar, and risk "
            "appetite. EM is quintessential risk-on. India has attracted structural interest "
            "(demographics, reforms, supply-chain reshoring). The Fed and dollar are the master "
            "demand variables — anticipated cuts and dollar weakness typically trigger renewed EM "
            "demand, easing the financial-conditions headwind."
        ),
        "outlook": (
            "Bull case: attractive valuations, Fed cuts and dollar weakness, India structural story, "
            "underowned positioning. Bear case: dollar strength risk, China overhang, higher "
            "volatility and governance risks, EM's history of disappointing structural-growth "
            "theses. Consensus increasingly favors selectivity — distinguishing structural winners "
            "(India), commodity/yield plays (LatAm), tech exposure (North Asia) from the contested "
            "China component. Catalysts: FOMC, US inflation data, dollar trajectory, China stimulus, "
            "semiconductor cycle, country-specific events (elections, reforms)."
        ),
        "correlation_txt": (
            "Textbook view: EM equities have high positive correlation to US equities (0.6-0.8) "
            "amplified during risk-on/off episodes, with additional negative correlation to the "
            "dollar. EM is essentially levered exposure to global risk sentiment plus a dollar bet."
        ),
    },

    "china": {
        "performance": (
            "Chinese equities (MCHI/FXI) have been among the most policy-driven asset classes in "
            "global markets — periodic forceful rallies on stimulus announcements followed by fades "
            "on disappointing implementation. Foreign positioning has fallen to multi-year lows amid "
            "structural concerns (property, demographics, debt, state-versus-private orientation) "
            "and US-China geopolitical tensions. Valuations have reached deep discounts to global "
            "peers, with world-class technology and consumer companies trading at depressed multiples."
        ),
        "supply": (
            "Onshore A-shares (Stock Connect access) versus offshore H-shares (Hong Kong) and US-"
            "listed ADRs (delisting risk). State-owned enterprises dominate certain sectors versus "
            "private champions in technology and consumer. State intervention through the 'national "
            "team' of state-affiliated funds buying to support prices is a distinctive supply-demand "
            "dynamic. Capital-flow accessibility affects effective supply to international investors "
            "and contributes to the discount."
        ),
        "demand": (
            "Domestic retail (large and sentiment-driven), domestic institutions, state ('national "
            "team'), and foreign — with foreign deeply underweight, itself a key dynamic. Domestic "
            "demand is heavily influenced by consumer/investor confidence damaged by the property "
            "crisis (real estate being the dominant household-wealth store). Foreign demand hinges "
            "on credibility of policy support, valuations, and geopolitical backdrop. Underowned "
            "positioning means a genuine sentiment shift could produce sharp rallies."
        ),
        "outlook": (
            "Consensus is divided. Bull: too cheap to ignore, forceful stimulus can revive growth "
            "and sentiment, world-class companies mispriced, underowned positioning provides rally "
            "fuel. Bear: structural headwinds (property, demographics, debt, state-direction), "
            "persistent geopolitical tensions, the cheapness is a value trap. High-risk policy-"
            "dependent tactical opportunity. Catalysts: major political/economic meetings (Politburo, "
            "Central Economic Work Conference, Two Sessions), stimulus and property-support "
            "announcements, regulatory signals, US-China developments, economic data."
        ),
        "correlation_txt": (
            "Textbook view: Chinese equities correlate moderately with US equities (0.3-0.5) — "
            "lower than developed markets given the policy-driven nature. The correlation can "
            "decouple sharply on China-specific policy moves or geopolitical events. Independent "
            "China rallies (or declines) are common."
        ),
    },

    # ─── CURRENCIES ────────────────────────────────────────────────────────
    "dxy": {
        "performance": (
            "The dollar has traded in a wide range driven by relative Fed-versus-other-central-bank "
            "expectations and global growth differentials. The 'dollar smile' has held: strength "
            "during US outperformance and during global risk-off, weakness in synchronized-growth "
            "phases. De-dollarization narratives have grown but the dollar's network effects, market "
            "depth, and lack of viable alternatives have kept its dominance largely intact in "
            "practice."
        ),
        "supply": (
            "Fed policy — rates and balance-sheet operations — is the primary supply determinant. "
            "QE expands dollar liquidity, QT contracts it. Global dollar liquidity, including "
            "through Fed swap lines during stress, is the transmission mechanism — dollar shortages "
            "in crises drive sharp dollar spikes. Long-term structural supply ties to US fiscal "
            "trajectory and the slow de-dollarization theme."
        ),
        "demand": (
            "Driven by relative attractiveness of dollar assets (rising with US rates and growth "
            "outperformance), safe-haven flows during stress, trade invoicing role, and reserve "
            "demand. Interest-rate differentials are the dominant cyclical driver. Safe-haven "
            "demand is the crisis function — capital floods to dollar safety/liquidity regardless "
            "of US-specific fundamentals, giving dollar negative correlation to risk during stress."
        ),
        "outlook": (
            "Cyclical bull: US growth/yield outperformance ('US exceptionalism'), safe-haven demand. "
            "Cyclical bear: Fed easing relative to others, synchronized global growth drawing "
            "capital abroad. Structural debate: de-dollarization vs durability of dominance — "
            "consensus view is gradual erosion not sudden shift. Catalysts: FOMC and other major "
            "central banks (relative policy comparison), US data (payrolls, CPI), risk-sentiment "
            "shifts triggering safe-haven flows."
        ),
        "correlation_txt": (
            "Textbook view: the dollar has slightly negative correlation to US equities in normal "
            "times (a strong dollar tightens financial conditions) but positive correlation during "
            "stress episodes (both rise as safe havens, or both fall in pure liquidity provision "
            "episodes). The relationship to bonds is positive (rate-differential channel)."
        ),
    },

    "eur": {
        "performance": (
            "The euro has been the mirror of the dollar (EUR/USD being the dominant DXY component), "
            "with relative ECB-versus-Fed policy and eurozone-versus-US growth as the master "
            "variables. Energy-price shocks weighed materially during the energy crisis given the "
            "eurozone's import dependence. Eurozone structural growth underperformance vs the US has "
            "biased the euro lower across multi-year horizons within wide cyclical swings."
        ),
        "supply": (
            "ECB policy — rates, asset purchases — determines euro supply. ECB easing relative to a "
            "tighter Fed weakens the currency. The eurozone's fragmented fiscal structure means no "
            "single 'eurozone bond' equivalent to Treasuries (though joint issuance has grown); "
            "peripheral-country sovereign dynamics can periodically pressure the euro during stress "
            "episodes via cohesion concerns."
        ),
        "demand": (
            "Relative attractiveness vs dollar assets (rate differentials), eurozone trade and "
            "current-account position (surplus is structurally supportive), risk sentiment (euro is "
            "higher-beta — benefits in risk-on, weakens in risk-off). Energy prices are a euro-"
            "specific factor given import dependence — energy spikes worsen terms of trade, "
            "pressuring the euro."
        ),
        "outlook": (
            "Bull case: narrowing growth gap, ECB holding rates relatively higher than Fed (or Fed "
            "easing faster), current-account surplus, risk-on environments. Bear case: structural "
            "growth underperformance, ECB easing faster than Fed, energy vulnerability, risk-off "
            "weakness. Catalysts: ECB and FOMC meetings, eurozone/US data, energy prices."
        ),
        "correlation_txt": (
            "Textbook view: the euro is positively correlated to US equities (it's a risk-on "
            "currency — risk appetite drives capital out of the dollar to euro assets) with "
            "correlation typically 0.3-0.5 to SPY. Inverse to the dollar by construction."
        ),
    },

    "jpy": {
        "performance": (
            "The yen has been defined by Bank of Japan normalization slowly emerging after decades "
            "of ultra-loose policy. The currency has been the world's premier carry-trade funding "
            "currency — borrowing cheaply in yen to invest in higher-yielding assets — which keeps "
            "structural depreciation pressure on it while building positions that can unwind "
            "violently during global stress. Ministry of Finance intervention has periodically "
            "capped excessive weakness."
        ),
        "supply": (
            "Bank of Japan policy governs supply. The historic shift from negative rates, yield-"
            "curve control, and massive asset purchases toward gradual normalization represents "
            "tightening supply conditions relative to the prior era. The MoF plays a separate role "
            "through FX intervention — the threat alone caps depreciation. Pace of BoJ "
            "normalization is the key variable."
        ),
        "demand": (
            "Interest-rate differentials are the dominant cyclical driver — wide differentials "
            "with higher-yielding currencies drive yen selling (the carry trade); narrowing "
            "supports the yen. Safe-haven flows: in risk-off episodes, carry positions unwind and "
            "Japanese investors repatriate, producing sharp yen strength. Japan's large external "
            "creditor position underpins the safe-haven role. Scale of accumulated carry positions "
            "means unwinds can be violent with global market implications."
        ),
        "outlook": (
            "Structural bull: BoJ normalization narrows the rate differential (especially with Fed "
            "easing), yen significantly undervalued, safe-haven appeal in an elevated-risk world. "
            "Cyclical caution: differential remains wide despite narrowing; BoJ has moved gradually. "
            "Consensus increasingly leans toward structural yen strengthening over time. Catalysts: "
            "BoJ meetings, FOMC (US-Japan differential), Japanese inflation/wage data (informing "
            "BoJ), MoF intervention signals, risk-sentiment shifts."
        ),
        "correlation_txt": (
            "Textbook view: the yen has negative correlation to US equities — it's a safe-haven "
            "currency that strengthens when risk assets fall (carry-trade unwinds, repatriation "
            "flows). Typical correlation is -0.3 to -0.5 to SPY, tightening to more negative levels "
            "during stress."
        ),
    },

    "cny": {
        "performance": (
            "The yuan is a managed currency, with the PBoC actively guiding the value via a daily "
            "reference fix and intervention rather than letting it float freely. The currency has "
            "faced persistent depreciation pressure from China's economic challenges, the unfavorable "
            "rate differential with the US, and capital-outflow tendencies, all offset by active "
            "PBoC management. The CNH-CNY spread (offshore vs onshore) serves as a real-time gauge "
            "of market pressure on the official rate."
        ),
        "supply": (
            "PBoC sets the daily fix, manages the trading band, and intervenes directly via FX "
            "reserves and macroprudential tools affecting capital flows. China's capital account "
            "remains substantially controlled, giving the PBoC significant management capacity. "
            "Monetary easing to support the weak domestic economy widens the unfavorable rate "
            "differential, creating tension between domestic stimulus needs and currency stability."
        ),
        "demand": (
            "Trade position (large surplus is structurally supportive), capital flows (facing "
            "outflow pressure on growth concerns and rate differential), rate differential with "
            "dollar (unfavorable), and economic-policy confidence. The trade-surplus support and "
            "capital-outflow pressure are mediated by PBoC management, which determines the "
            "managed path."
        ),
        "outlook": (
            "Base case: gradual managed depreciation under fundamental pressure, with PBoC "
            "preventing disorderly weakening. Tail risk: larger managed devaluation, particularly "
            "in response to trade tensions and tariffs — would pressure other Asian/EM currencies, "
            "export deflation globally, and could trigger broad risk-off. Catalysts: PBoC fix "
            "signals, US-China trade and tariff developments, China economic data, PBoC monetary "
            "moves, US rates."
        ),
        "correlation_txt": (
            "Textbook view: the managed yuan has muted correlations to equities — its path "
            "reflects PBoC policy choices rather than free-market pricing. Apparent correlations "
            "are policy-mediated. The exception is a managed-devaluation event, which would have "
            "negative implications for global risk assets."
        ),
    },
}
