"""
Extended per-asset narratives — substantially deeper than the base narratives.

This module exists separately from narratives.py so that asset coverage can be
upgraded incrementally without disturbing the base content. The exporter checks
NARRATIVES_EXTENDED first for each asset; assets not present here fall back to
the shorter narratives in narratives.py.

Style: full institutional research depth. Specific numbers, named mechanisms,
historical episodes, concrete catalysts with cadence. Multi-paragraph supply,
demand, and outlook sections. Honest about uncertainty.

Each entry overrides supply, demand, outlook for that asset. Performance and
correlation_txt are pulled from the base narratives unless explicitly overridden
here.

Architectural note: in the future, weekly news-scan output (per sources.py) can
be appended to or interleaved with these structural narratives, producing
truly live weekly mini-reports. The current content captures the durable
structural picture that doesn't change week to week.
"""


def P(*paragraphs):
    """Join paragraphs with double-newlines for clean rendering."""
    return "\n\n".join(paragraphs)


NARRATIVES_EXTENDED = {

    # ──────────────────────────────────────────────────────────────────────
    # GOLD — flagship example of the full institutional-depth treatment
    # ──────────────────────────────────────────────────────────────────────
    "gold": {
        "supply": P(
            "Global mine supply runs around 3,500-3,700 tonnes annually and has been roughly flat for the better part of a "
            "decade — the structural picture is one of supply rigidity meeting growing demand. Production is geographically "
            "diversified across China (the world's largest producer at ~370 tonnes annually), Russia, Australia, Canada, the "
            "United States, and a long tail of African producers including Ghana, Mali, Burkina Faso, and South Africa, "
            "whose own production has declined dramatically from its 1970s peak of nearly 1,000 tonnes annually to under 100 "
            "tonnes today. No single jurisdiction has the supply concentration that affects oil markets through OPEC or "
            "industrial metals through Chilean copper, which means individual country disruptions have only marginal global "
            "supply effects.",

            "The deeper supply constraint is geological and developmental rather than political. Ore grades at major mines "
            "have been in secular decline for decades — the industry-average grade is now under 1 gram per tonne, roughly "
            "half what it was forty years ago. Truly large, high-grade deposits are increasingly rare; the major discoveries "
            "of the past 30 years (Carlin Trend developments, Olympic Dam by-product gold, Grasberg in Indonesia) are mature "
            "operations. Development timelines from initial discovery to first production routinely exceed 10-15 years, "
            "encompassing exploration, feasibility studies, permitting (now a multi-year process in most Western "
            "jurisdictions), financing, construction, and ramp-up. This long lead time means even sustained high prices "
            "struggle to translate into materially higher mine supply on any policy-relevant horizon. The industry exploration "
            "budget collapsed during the 2013-2018 price downturn and has only partially recovered, ensuring thin discovery "
            "pipelines for the late 2020s.",

            "Recycling provides the swing supply — roughly 1,100-1,300 tonnes annually, primarily from jewelry scrap (the "
            "dominant category), industrial recovery, and bar/coin liquidation. Recycling supply is strongly counter-"
            "cyclical: high gold prices coax more jewelry scrap back to market, particularly from Asia where families hold "
            "significant gold reserves and may liquidate during personal financial distress. This counter-cyclical recycling "
            "buffer moderates short-term price spikes but doesn't change the supply curve's underlying inelasticity. Notably, "
            "much-discussed urban mining (gold recovery from electronics) provides only modest tonnage — perhaps 100-150 "
            "tonnes annually — despite the high theoretical potential.",

            "On the cost side, the industry-wide all-in sustaining cost (AISC) has migrated from around $700-900/oz a decade "
            "ago to roughly $1,300-1,500/oz today, reflecting grade deterioration, labor inflation, energy costs, and "
            "increasingly stringent environmental and community-relations spending. This rising cost floor means lower-"
            "quartile producers — historically a backstop for declining-price regimes — face genuinely negative margins "
            "below ~$1,400, and the supply response to price declines is increasingly violent (mine closures rather than "
            "gradual production cuts). Major producers (Newmont, Barrick, Agnico Eagle, AngloGold Ashanti) report AISC in "
            "quarterly disclosures, providing real-time evidence of the cost curve.",

            "Above-ground gold stocks — the cumulative stock of all gold ever mined, estimated by the World Gold Council at "
            "more than 210,000 tonnes — dwarf annual mine supply by a factor of roughly 60x. The implication is that above-"
            "ground holdings behavior (central banks deciding to add or sell, ETFs receiving or redeeming, jewelry being "
            "melted or hoarded) drives short-term supply-demand balance far more than mine output does. This is a critical "
            "structural feature: in any given week or month, mine flow is a small input compared to potential above-ground "
            "redistribution. Central bank disposal could in principle add hundreds of tonnes to effective supply; the post-"
            "1999 European central bank gold sales (the Washington Agreement era) were a sustained demonstration of this. "
            "Conversely, the post-2009 transition of central banks from net sellers to net buyers represents the same "
            "above-ground stock flowing the other direction at scale."
        ),

        "demand": P(
            "Central bank purchases have been the dominant marginal demand source since 2022, running above 1,000 tonnes "
            "annually — roughly double the prior decade's pace and the highest sustained pace since the Bretton Woods era. "
            "The buying has been led by emerging-market central banks: the People's Bank of China (whose reported purchases "
            "almost certainly understate actual accumulation, given persistent discrepancies between PBoC disclosures and "
            "physical import data through Hong Kong and Shanghai), the Reserve Bank of India (which has been a consistent "
            "buyer through 2022-2024), Turkey (where the central bank both accumulates and periodically sells depending on "
            "currency conditions), Poland (the National Bank of Poland under President Glapinski has been one of the most "
            "aggressive buyers, targeting gold as roughly 20% of total reserves), Singapore (MAS), the Czech Republic, "
            "Hungary, and several Middle Eastern central banks (Qatar, Egypt, UAE).",

            "The strategic logic crystallized after February 2022, when the Western freezing of Russia's foreign exchange "
            "reserves — approximately $300 billion in primarily dollar-denominated assets — demonstrated that dollar-"
            "denominated reserve assets carry political risk for any nation that might find itself on the wrong side of US "
            "foreign policy. Gold sits outside this political risk category because it has no counterparty — physical gold "
            "in a domestic vault cannot be frozen by foreign sanctions, cannot have its claims invalidated by a foreign "
            "court, and cannot be devalued by a foreign monetary policy decision. For central banks of nations with "
            "potentially adversarial geopolitical positioning relative to the US — China, Russia (before sanctions), India "
            "(to a lesser degree), Turkey, various Middle Eastern states — this property is uniquely valuable.",

            "The pace and persistence of central bank buying has genuinely surprised market participants. The World Gold "
            "Council reports central banks added more than 1,000 tonnes in each of 2022, 2023, and 2024 — three consecutive "
            "years at a pace not seen in over half a century, and roughly 20-25% of annual mine supply being absorbed by "
            "this single demand pool. The buying appears largely price-insensitive, suggesting reserve managers operate on "
            "a multi-year allocation framework rather than tactical entry timing. This is fundamentally different demand "
            "from the Western financial demand that dominated previous cycles — central banks are not concerned with the "
            "10Y TIPS yield or the dollar level when making strategic allocation decisions toward gold reserves, and the "
            "demand has accordingly proceeded through what would historically have been adverse conditions.",

            "Jewelry demand is large in tonnage terms (around 2,000-2,200 tonnes annually, the single largest end-use "
            "category) but highly price-elastic — Indian and Chinese consumers, the dominant jewelry markets at "
            "approximately 600-700 tonnes each annually, materially reduce purchases when prices rise sharply, and "
            "accelerate buying on dips. Indian wedding-season demand (October through January, with the Dhanteras and "
            "Diwali festival period in October-November the single largest gold-buying period of the year) and Chinese New "
            "Year demand (January-February) create predictable seasonal patterns. The longer-term trend is modest erosion "
            "as younger consumers shift toward investment-grade gold (coins, bars, digital gold accounts on platforms like "
            "Paytm Gold in India) and away from heavy traditional jewelry. The 22-karat traditional Indian wedding gold and "
            "24-karat investment-grade Chinese physical gold represent different demand profiles within the same category.",

            "Western investment demand — primarily through ETFs (the SPDR Gold Trust GLD with ~700+ tonnes of holdings being "
            "the dominant vehicle, plus the iShares Gold Trust IAU, the Aberdeen Standard Physical Gold Shares SGOL, and "
            "various European products), bar and coin sales through dealers like APMEX, JM Bullion, and the U.S. Mint's "
            "American Gold Eagle program — has been notably absent during much of the 2023-24 rally. ETF holdings actually "
            "declined modestly during this period even as the price made new highs, an extraordinary historical anomaly. "
            "Pre-2022 cycles featured ETF flows as a coincident-to-leading indicator of gold price moves; the broken "
            "relationship in 2022-2024 is itself diagnostic of the regime change. The structural read is that Western "
            "investors remained underweight gold throughout the rally, with allocations in model portfolios and wealth-"
            "manager templates capped at 0-2% versus historical norms of 5%+. This underweight positioning represents "
            "substantial latent upside fuel: a sustained move into gold by US wealth advisors, model portfolio allocators, "
            "and tactical asset managers could materially extend the rally even if central bank purchases moderate.",

            "Technology and dental demand together account for roughly 300-350 tonnes annually, a small but stable category. "
            "Within technology, gold is used in semiconductors, connectors, and high-reliability electronics where its "
            "corrosion resistance and conductivity command a premium over copper or aluminum alternatives. Modest growth "
            "from increasing electronics complexity (more solder joints per device, more interconnects per semiconductor) "
            "is offset by miniaturization that reduces gold per device. This category is essentially flat over time."
        ),

        "outlook": P(
            "The structural bull case rests on continued central bank diversification, fiscal-dominance concerns in "
            "developed markets, and a re-engagement of Western investors who remain underweight. The fiscal angle deserves "
            "emphasis: US debt-to-GDP has crossed 120%, fiscal deficits run 6-7% of GDP in non-recession years, and the "
            "political incentive structure points to continued expansion regardless of administration. The CBO's long-term "
            "projections show debt-to-GDP rising toward 150-180% by mid-century absent policy action that no major political "
            "constituency appears willing to take. In such an environment, gold's appeal as a non-sovereign store of value "
            "strengthens, particularly for institutions concerned about the durability of dollar reserve status. The Fed's "
            "constrained position — needing to maintain accommodative real conditions to service the debt while also "
            "maintaining inflation-fighting credibility — creates structural conditions favorable to gold even if cyclical "
            "tightness occurs.",

            "The principal risks are several and worth taking seriously. First, a genuine restoration of real-yield "
            "discipline — either through a fiscal policy shift toward consolidation (essentially unprecedented in modern "
            "US politics but theoretically possible) or a Fed willing to hold real yields elevated despite economic weakness "
            "(the 1980s Volcker pattern, similarly difficult given current conditions) — would remove gold's macro support. "
            "Second, the de-dollarization narrative may be largely priced; if BRICS and EM diversification flows moderate "
            "from the current torrid pace, the marginal central bank buyer effectively disappears and the structural bid "
            "weakens. Third, a sharp risk-off episode could produce gold weakness alongside everything else as institutions "
            "sell what they can to meet margin calls (the March 2020 dynamic, when gold initially sold off sharply before "
            "rallying as the Fed intervened with massive liquidity provision). Fourth, opportunity cost: if real yields "
            "rise materially, the no-yield nature of gold becomes a more meaningful headwind for institutional allocators "
            "comparing it to TIPS or other inflation-linked instruments offering real yield.",

            "Tail risks both directions deserve flagging. Upside: a major geopolitical event (Taiwan strait crisis, "
            "Middle East war escalation, broader financial system stress event) drives safe-haven demand from Western "
            "investors who have been absent; major sovereign wealth funds (Norway's NBIM, Singapore's GIC, Middle Eastern "
            "SWFs) begin material gold allocations; the US dollar reserve status is meaningfully challenged by an "
            "alternative system. Downside: a major fiscal credibility restoration in the US; emerging market central banks "
            "pause or reverse their gold accumulation; gold becomes a crowded long position vulnerable to a positioning "
            "unwind.",

            "Catalysts to monitor on a calendar basis. World Gold Council Gold Demand Trends report (quarterly, typically "
            "released in late January, April, July, October): authoritative data on central bank flows, ETF, jewelry, "
            "technology — the single most important data release. Monthly central bank purchase data from WGC, with a ~2-"
            "month lag. FOMC decisions and the SEP/dot plot (quarterly): rate-path expectations. US CPI and PCE prints "
            "(monthly): inflation persistence informing Fed policy. PBoC monthly reserve disclosures: directly observed "
            "Chinese official purchases (though widely believed to understate actual buying). Russia/Ukraine and Middle "
            "East developments: geopolitical risk premium. BRICS summit announcements: de-dollarization narrative "
            "validation. Major Western asset allocator commentary (BlackRock, JPM, Goldman Wealth, Morgan Stanley): early "
            "signals of Western re-engagement. CFTC Commitments of Traders gold report (weekly): speculative positioning "
            "in COMEX futures. SPDR Gold Trust (GLD) holdings (daily): proxy for Western financial demand.",

            "Tactically, gold has traded in defined ranges punctuated by sharp upside breaks; positioning into ETF flow "
            "inflection points (after sustained outflows have created underweight setups) has historically been "
            "productive. The relationship with real yields is currently broken, but watching for its restoration is "
            "informative — if gold begins responding to real-yield moves again, the central bank bid may be moderating. "
            "Gold mining equities (GDX, GDXJ for juniors) provide leveraged exposure that has lagged the metal in recent "
            "cycles — an open question is whether the gap closes as cost pressures stabilize and operational performance "
            "improves at major producers."
        ),
    },

    # ──────────────────────────────────────────────────────────────────────
    # COPPER
    # ──────────────────────────────────────────────────────────────────────
    "copper": {
        "supply": P(
            "Global mine supply runs around 22-23 million tonnes annually, concentrated in Chile (the world's largest "
            "producer at ~5.3 million tonnes through state-owned Codelco and major private operators including BHP's "
            "Escondida — the world's largest single mine — Antofagasta, and Anglo American's Los Bronces and Collahuasi), "
            "Peru (~2.4 million tonnes, with Glencore-controlled Antamina and the politically fraught Las Bambas being key "
            "operations), the Democratic Republic of Congo (~2.5 million tonnes and rising rapidly, driven by Chinese "
            "investment through China Molybdenum's Tenke Fungurume and Ivanhoe-Zijin joint venture's Kamoa-Kakula complex), "
            "China itself (~1.7 million tonnes of domestic mine output, supplemented by significant import dependence), the "
            "United States, Australia, Russia, and Zambia. The geographic concentration in Chile and Peru — together over "
            "a third of global supply — creates real political and operational risk; both countries have seen left-leaning "
            "political shifts with mining-tax and royalty agendas in recent years, though most attempted reforms have been "
            "moderated significantly in implementation.",

            "The structural supply constraint operates on multiple horizons. Short-term: ore grades at major mines are in "
            "secular decline. Escondida's average grade has fallen from above 1.5% copper at its peak to below 0.7% over "
            "two decades. Across the industry, grades have declined roughly 30% over the past 25 years. Falling grades "
            "mean more rock must be moved, more water consumed, and more energy expended to produce the same metal — "
            "fundamentally a higher marginal cost curve. This is observable in producer AISC disclosures, which have "
            "trended upward consistently. Medium-term: water access in the Chilean Atacama and similar arid mining regions "
            "has become a binding constraint, requiring desalination plants and water pipelines that add hundreds of "
            "millions of dollars in capex and meaningful operating cost. BHP and other Chilean operators have invested "
            "billions in desalination infrastructure that ten years ago would have been considered unthinkable. Long-term: "
            "the new-project pipeline is unusually thin. Years of underinvestment during the 2012-2016 price downturn left "
            "exploration budgets and project development substantially reduced; the major-bank commodities desks broadly "
            "agree that no realistic combination of currently-permitted projects can fill the demand gap that emerges in "
            "the late 2020s under any reasonable demand-growth scenario.",

            "Disruption risk is recurring and operationally meaningful. Strikes at Chilean mines have repeatedly shut down "
            "major operations for weeks at a time — the 2017 Escondida strike removed approximately 200,000 tonnes from "
            "global supply. Indonesian and Filipino regulatory interventions (export bans, ownership requirements) have "
            "periodically disrupted supply. The DRC's growing share creates new political risk — Chinese operators "
            "dominate DRC production, and the relationship between the DRC government and its mining partners has been "
            "increasingly contested, with renegotiations of contracts under President Tshisekedi. Panama's late-2023 "
            "closure of First Quantum's Cobre Panamá mine — which had produced approximately 350,000 tonnes annually, "
            "roughly 1.5% of global supply — demonstrated how rapidly a single political event can remove material supply "
            "from the market. The mine has not restarted as of the most recent updates, despite First Quantum's continued "
            "efforts at resolution.",

            "TC/RC dynamics deserve particular attention as a real-time supply tightness indicator. Treatment and refining "
            "charges are what miners pay smelters to process concentrate into refined copper — the spread compensates "
            "smelters for their conversion service. When concentrate is abundant relative to smelter capacity, miners can "
            "negotiate high TC/RCs (smelters compete for material to keep their plants running). When concentrate is scarce, "
            "smelters compete and accept low TC/RCs to retain throughput. Current TC/RCs have compressed to multi-year lows "
            "and have at times approached zero — a signal of severe concentrate tightness that has not yet flowed through "
            "to refined copper prices because Chinese smelter capacity additions through 2021-2023 absorbed the gap. The "
            "March 2024 announcement by major Chinese smelters (the CSPT alliance) of coordinated production cuts in "
            "response to negative TC/RCs was a watershed moment, suggesting the concentrate tightness has begun to bind "
            "on refined output. This dynamic — concentrate-tight, refined-balanced — is the central feature of the current "
            "copper market structure.",

            "Recycling provides roughly 4-5 million tonnes of additional refined-copper-equivalent supply annually, "
            "increasingly important as the secondary market for copper scrap grows. Chinese scrap import policy has been a "
            "major variable: the tightening of scrap import standards in 2018-2020 reshaped global scrap flows, with "
            "material increasingly processed in Malaysia, Vietnam, and other intermediate hubs before reaching China. The "
            "long-term scrap pool grows mechanically as the installed base of copper (in buildings, infrastructure, "
            "appliances, vehicles) ages and reaches end-of-life; this represents a meaningful but slow-moving structural "
            "supply addition over 20-50 year horizons."
        ),

        "demand": P(
            "Chinese demand is the dominant cyclical variable and accounts for roughly half of global refined consumption "
            "(approximately 12-14 million tonnes annually out of global demand of 25-26 million tonnes). Within China, "
            "copper demand has historically been driven by three large pillars: construction (residential buildings, "
            "commercial real estate, traditional infrastructure including water and sewerage), electrical grid expansion "
            "(both transmission infrastructure and consumer-side wiring), and manufacturing/appliances (air conditioners, "
            "refrigerators, motors, industrial machinery). The property-sector downturn that began in 2021 — initially with "
            "Evergrande's distress and now spread through multiple major developers including Country Garden, Sunac, and "
            "Vanke — has materially weighed on construction-related copper demand. New housing starts have collapsed to "
            "multi-decade lows, signaling that one major demand component is in structural decline. The completion of "
            "structures still in construction continues to provide a floor as developers prioritize delivering pre-sold "
            "units (under government pressure to maintain social stability), but this is a finite tail that's working "
            "through over the next 24-36 months.",

            "What has held up Chinese copper demand against the property headwind is the aggressive buildout of grid "
            "infrastructure, renewable capacity, and EV-related manufacturing. China is installing renewable capacity at a "
            "pace that dwarfs all other countries combined — adding more solar capacity in some recent years than the rest "
            "of the world combined. The State Grid Corporation of China alone runs an investment program of $80-100 "
            "billion annually, much of it copper-intensive (high-voltage transmission lines, transformers, distribution "
            "infrastructure). EV production in China — Chinese OEMs now produce more EVs than the rest of the world "
            "combined, led by BYD, Tesla Shanghai, Geely, Nio, Xpeng, Li Auto, and others — has been a major copper sink, "
            "with each EV containing roughly 60-80 kg of copper versus 20-25 kg in an ICE vehicle. Charging "
            "infrastructure is similarly copper-intensive. The structural question is whether these growth vectors can "
            "continue to offset the property decline; recent ICSG and CRU analyses suggest yes, with copper-intensive "
            "green-economy demand growing faster than property-related demand contracts.",

            "Outside China, structural demand sits on several drivers. EV adoption in Europe (with sales penetration in "
            "Norway, Netherlands, and the Nordics well above 50% and growing in larger markets) and the US (slowing "
            "growth but continuing) drives meaningful copper demand growth. The US Inflation Reduction Act and Bipartisan "
            "Infrastructure Law together earmark hundreds of billions for grid modernization, EV infrastructure, and "
            "renewable capacity — all copper-intensive. European grid investment programs (the EU's REPowerEU initiative, "
            "national grid modernization programs in Germany, France, UK, Spain, Italy) provide additional structural "
            "demand. Indian copper demand has been growing strongly off a small base; India aims to grow per-capita "
            "copper consumption substantially over the next decade as electrification deepens.",

            "The emerging AI data-center vector deserves explicit attention as a relatively new and growing structural "
            "demand source. Data centers are enormously copper-intensive across multiple components: power transmission "
            "infrastructure from the grid (substations, transformers, transmission cabling), on-site distribution "
            "(switchgear, UPS systems, cooling system pumps and chillers), within the racks themselves (server power "
            "supplies, network cabling, busbars), and indirectly through the increased grid investment needed to power "
            "the data centers. The acceleration of AI training and inference workloads has driven hyperscaler capex "
            "(Microsoft, Google, Amazon, Meta, Oracle, plus emerging players like xAI and CoreWeave) to record levels — "
            "combined annual capex from the major hyperscalers now exceeds $250 billion, with multi-year expansion plans "
            "that imply sustained high spending. Estimates for incremental copper demand from data center buildout vary "
            "widely (from <1 million tonnes additional annual demand to several million tonnes by 2030), but the direction "
            "is unambiguous and additive to the electrification thesis. Combined with grid expansion needed to power these "
            "data centers, AI-related copper demand may emerge as one of the most important demand drivers of the late "
            "2020s.",

            "Industrial demand outside the structural growth vectors — appliances, traditional construction, conventional "
            "vehicles — remains large in tonnage terms (over half of global demand) and broadly tracks the global "
            "manufacturing cycle. Manufacturing PMIs (US ISM, China Caixin, Eurozone Composite, JPMorgan Global PMI) are "
            "the cyclical confirmation pair. The 2023-2024 manufacturing soft patch globally has weighed on this "
            "category, but underlying installed base maintenance and replacement demand provides a floor.",

            "Inventory dynamics affect short-term price formation substantially. Exchange-reported stocks at LME, COMEX, "
            "and SHFE — plus the less-visible bonded stocks in Chinese ports — comprise the readily-available copper "
            "supply that smooths short-term supply-demand imbalances. These inventories have oscillated meaningfully but "
            "trended lower in aggregate over recent quarters. Significant concurrent drawdowns across all three exchange "
            "venues, combined with depressed bonded stocks in China, would signal genuine acute tightness; the current "
            "picture is moderate but not extreme inventory drawdown."
        ),

        "outlook": P(
            "The structural bull consensus among institutional commodities analysts is unusually strong: electrification-"
            "driven demand surge colliding with slow-to-respond supply points to a multi-year deficit later this decade. "
            "Major projections from CRU, Wood Mackenzie, BloombergNEF, the IEA's net-zero pathway analysis, and the major "
            "investment-bank commodities desks (Goldman Sachs has been particularly vocal in advocating the deficit "
            "thesis; JPM, Morgan Stanley, Citi have published supporting analysis) broadly agree on the direction even "
            "where they disagree on magnitude. Lead times on new supply mean that even a sustained price signal cannot "
            "quickly resolve the deficit — the supply response is measured in years for brownfield expansion and decades "
            "for major new discoveries. This is the structural setup most often compared to oil in the mid-2000s, when "
            "underinvestment from the 1990s low-price era produced a multi-year cycle of rising prices despite high-cost "
            "supply gradually responding.",

            "The cyclical and tactical caution is real and has dominated recent price action. Chinese property weakness, "
            "intermittent global manufacturing softness, and dollar strength have all weighed on copper despite the bullish "
            "structural narrative. Inventories, while drawing down, have not signaled the kind of acute tightness that "
            "would force a price re-rating. The risk for bulls is that the cycle continues to dominate the structure for "
            "longer than positioning can sustain, producing painful drawdowns within the longer-term uptrend. Goldman's "
            "early-2024 'time to buy copper' call has proven premature even though the directional view may eventually be "
            "vindicated.",

            "Several outright bear risks deserve weighing. First, a serious China demand contraction — beyond property "
            "weakness into broader industrial slowdown — would overwhelm the electrification thesis on any reasonable "
            "timeframe. China's structural growth rate is slowing for reasons that go beyond property (demographics, "
            "debt levels, geopolitical fragmentation), and a meaningful reset of Chinese growth expectations would hit "
            "copper hard. Second, EV adoption could disappoint relative to current trajectories, particularly if hybrid "
            "vehicles (which use less copper than full BEVs) capture market share from BEVs as some recent data suggests. "
            "Third, recycling and substitution could prove more responsive to high prices than the bull case assumes — "
            "aluminum is a viable substitute in some grid applications, and improved scrap processing has potential. "
            "Fourth, the new mining pipeline, while thin, includes several large projects (Kamoa-Kakula in DRC continues "
            "to ramp toward 600,000+ tonnes annually; Oyu Tolgoi underground in Mongolia is producing; various Chilean "
            "brownfield expansions; Indonesian projects) that could provide more supply than the bull narrative "
            "anticipates.",

            "Tail risks. Upside: Chinese stimulus arrives with greater force than expected and revives property "
            "completion plus broader industrial activity; data center demand exceeds even bullish projections; major "
            "supply disruption (Chilean strikes, Peruvian protests, Cobre Panamá-style political shutdown of another "
            "major mine); aluminum substitution proves more difficult than anticipated. Downside: prolonged Chinese "
            "stagnation; EV adoption disappoints; major demand destruction from sustained recession; new supply comes "
            "online faster than expected.",

            "Catalysts and what to watch. ICSG Monthly Bulletin (typically mid-month): the authoritative global S/D "
            "balance from the International Copper Study Group. Exchange inventories at LME, COMEX, SHFE (daily): "
            "concurrent drawdowns are the genuine-tightness signal. TC/RCs: real-time concentrate tightness indicator. "
            "Chinese property data (monthly NBS releases) and stimulus announcements: the central cyclical variable. "
            "Manufacturing PMIs globally: cyclical confirmation. Mine disruptions: Chilean labor situation, DRC political "
            "developments, Indonesian and Filipino policy, Peruvian protests. Goldman Sachs commodity research notes: "
            "long-standing advocate of the copper deficit thesis with detailed supply tracking. BloombergNEF for "
            "structural demand modeling. Hyperscaler capex announcements (Microsoft, Google, Amazon, Meta quarterly "
            "earnings): proxy for data-center buildout pace. China customs monthly copper and concentrate imports: actual "
            "demand pulse.",

            "Tactically, copper has historically rewarded patience and punished early entries: the cycle can keep "
            "grinding long after the structural case appears compelling. Positioning into Chinese stimulus cycles and "
            "global PMI troughs has been more productive than chasing structural narratives alone. The forward curve "
            "shape, while less informative than for oil, can flag tightness — backwardation in copper has been rare and "
            "tends to coincide with acute physical tightness. Copper-equity exposures (Freeport-McMoRan, Southern Copper, "
            "Antofagasta, First Quantum) offer operational leverage but introduce country-specific and operational risk; "
            "the equities have historically traded at higher beta than the metal itself."
        ),
    },

    # ──────────────────────────────────────────────────────────────────────
    # OIL (WTI)
    # ──────────────────────────────────────────────────────────────────────
    "oil": {
        "supply": P(
            "OPEC+ controls roughly 40% of global supply when including the Russia-led non-OPEC participants brought into "
            "the alliance in 2016. The cartel currently holds 3-4 million barrels per day of spare capacity, concentrated "
            "heavily in Saudi Arabia (with smaller cushions at the UAE and Kuwait). This spare capacity functions as the "
            "market's shock absorber — it can be activated quickly to address supply disruptions but is also held back to "
            "defend prices when fundamentals soften. The composition of OPEC+ cuts matters: Saudi Arabia's additional "
            "voluntary cuts beyond the group quotas (the additional ~1 million b/d voluntary reduction announced in 2023 "
            "and extended multiple times) have functioned as the marginal price-setting decision in recent years. The "
            "Saudi commitment to defending a price band has been the dominant single factor in keeping crude in its "
            "managed range.",

            "Within OPEC+, member compliance with quotas varies considerably. Iraq has chronically over-produced relative "
            "to its quota, with the dispute reflecting Iraqi domestic political pressures and oil-revenue needs. Kazakhstan "
            "has at various times failed to meet pledges. UAE production capacity has grown faster than its quota share, "
            "creating internal alliance tension that has been managed through periodic quota revisions but remains a "
            "structural fault line. Russia's role within OPEC+ has been complicated by sanctions and the redirection of "
            "exports from Europe to India and China at discounts. OPEC+ ministerial meetings (held every 1-2 months, with "
            "major decisions at semi-annual ministerial-level meetings, typically in late November/early December and "
            "early June) are calendar-known events that can move the market substantially when policy shifts.",

            "US production at record levels above 13 million b/d makes the US the world's largest oil producer, surpassing "
            "both Saudi Arabia and Russia. This is fundamentally a shale phenomenon: tight-oil production from the Permian "
            "Basin (the dominant basin at roughly 6+ million b/d, with most of the growth concentrated here), the Bakken "
            "in North Dakota, Eagle Ford in Texas, and smaller contributions from other basins. The key shift in shale "
            "economics has been the transition from growth-at-all-costs (the 2014-2019 era when shale companies pursued "
            "production growth and accumulated debt regardless of free cash flow) to capital discipline (post-2020): "
            "public shale producers now prioritize returning cash to shareholders via dividends and buybacks over volume "
            "growth, having been chastened by the 2014-2016 and 2020 price collapses. This shift has tempered the "
            "historical price-response curve — high prices no longer reliably bring a flood of new supply. However, the "
            "still-substantial private shale operator base (which now produces a meaningful share of US output and is "
            "owned primarily by E&P-focused private equity funds) retains a more growth-oriented orientation, with "
            "private operators continuing to drill and complete wells more aggressively than public peers.",

            "Permian Basin dynamics deserve specific attention given the basin's outsized share of US growth. The basin "
            "has progressed through the highest-quality acreage (the 'Tier 1' inventory in the core Midland and Delaware "
            "subbasins), and remaining inventory is generally of lower quality requiring more capital per barrel of "
            "production. Major operators (ExxonMobil's post-Pioneer combined position is now the largest; Chevron's "
            "Hess deal positioning the company strategically; Diamondback, Coterra, EOG, Devon, Occidental as the other "
            "majors) have begun signaling that the era of rapid Permian growth is moderating. Permian production growth, "
            "which was 700,000-800,000 b/d annually at peak, has decelerated meaningfully and is expected to grow by less "
            "than half that rate over coming years.",

            "Sanctioned and constrained barrels add a separate supply layer with substantial geopolitical sensitivity. "
            "Russian production has remained surprisingly resilient despite Western sanctions and the G7 price cap, with "
            "crude flows redirected from Europe to India (which became a major buyer of Russian crude at discounts), China, "
            "and Turkey. The G7 price cap has been progressively evaded through 'shadow fleet' tanker arrangements "
            "(older tankers with opaque ownership operating outside Western insurance) and alternative insurance "
            "(non-Western P&I clubs). Iranian production has recovered to ~3.5+ million b/d under loose sanctions "
            "enforcement under the Biden administration; any tightening of enforcement under the Trump administration "
            "would remove significant supply (estimated 1-1.5 million b/d). Venezuelan output, after the partial "
            "sanctions relief allowing Chevron's continued operations, sits around 800,000-900,000 b/d versus 2-3 million "
            "in its earlier peak. The enforcement intensity on these sanctioned barrels directly determines what's "
            "available to the legitimate market and represents a major variable for oil prices.",

            "Outside the headline producers, the long tail of supply matters cumulatively. Guyana has emerged as a major "
            "new producer (ExxonMobil-led Stabroek block now producing 600,000+ b/d, with capacity expanding rapidly "
            "toward 1+ million b/d through additional development phases). Brazil's pre-salt production continues to "
            "grow modestly, with Petrobras and partners adding capacity. Canadian oil sands production has remained "
            "steady around 4 million b/d, with limited new investment but extending lives of existing facilities. The "
            "North Sea is in long-term decline. Each adds or subtracts at the margin, and cumulatively these non-OPEC, "
            "non-shale producers are the swing factor for whether OPEC+ can hold its preferred price band.",

            "Refining capacity is a related supply constraint deserving attention. Global refining capacity is barely "
            "growing — major new capacity in China and the Middle East (Saudi Aramco's Jazan, the UAE's Ruwais expansions, "
            "China's continued capacity additions) is offset by closures in Europe and the US (multiple US East Coast "
            "and Western European refineries closed in 2020-2023, with more announced). This means refining margins have "
            "remained structurally elevated, and crude prices and product prices (gasoline, diesel, jet fuel) can diverge "
            "significantly during cycle peaks and troughs. The 3-2-1 crack spread (a measure of refining margin) has "
            "averaged materially higher post-2022 than pre-2022."
        ),

        "demand": P(
            "Global demand sits around 102-103 million b/d with modest growth concentrated in emerging Asia. The IEA, "
            "OPEC, and EIA all publish monthly demand forecasts, and these regularly diverge — the IEA has typically "
            "projected lower demand growth and an earlier peak than OPEC, which has consistently projected demand growth "
            "extending well into the 2030s. The methodological differences reflect different assumptions about EV "
            "adoption, efficiency gains, and demand-destruction at higher prices. The OPEC view tends to align with "
            "producer interests; the IEA view tends to align with climate-policy frameworks. The actual outcome will "
            "likely fall between these forecasts.",

            "India has emerged as the most reliable demand-growth engine, projected to grow from ~5 million b/d "
            "currently to 6-7+ million b/d over the next 5-10 years driven by vehicle fleet expansion (India is still in "
            "the early innings of mass vehicle ownership), petrochemicals buildout (Reliance and others continue major "
            "refining/petchem expansions), and aviation growth (IndiGo, Air India expanding aggressively). India is the "
            "single largest source of long-term demand growth uncertainty in oil markets — the country could materially "
            "exceed or fall short of these projections.",

            "China's demand trajectory is the single most-watched variable in the oil market and has surprised in recent "
            "years to the downside. China imports roughly 11+ million b/d of crude, making it the world's largest crude "
            "importer. Post-pandemic recovery has been weaker than anticipated; property weakness has reduced industrial "
            "diesel demand; broad consumer caution has reduced gasoline demand. But the most underappreciated factor is "
            "China's rapid EV adoption — new EV sales now exceed 50% of total vehicle sales in some months, the world's "
            "most aggressive transition. China's gasoline demand appears to have peaked or be near peak as the EV "
            "penetration progresses; some Chinese analysts forecast outright gasoline demand declines as soon as 2025-"
            "2026. Diesel demand is structurally challenged by property weakness and slowing industrial activity. "
            "Petrochemicals demand has held up better, supporting naphtha and LPG. The mix shift within Chinese demand "
            "(away from transport fuels, toward petrochemical feedstocks) is consistent with the broader thesis that "
            "the China demand growth engine is moderating.",

            "Sectoral demand decomposes broadly across global consumption: light vehicles (gasoline + light diesel) "
            "roughly 25 million b/d, heavy vehicles (diesel) roughly 25 million b/d, aviation (jet fuel) roughly 7 "
            "million b/d, petrochemicals (naphtha, LPG, ethane) roughly 14 million b/d, marine bunker fuel 4-5 million "
            "b/d, residential/commercial heating ~4 million b/d, and various industrial uses making up the balance. "
            "The categories most exposed to EV displacement are light-vehicle gasoline and to a lesser extent light-"
            "vehicle diesel; aviation, marine, heavy-duty trucking, and petrochemicals face less immediate substitution "
            "risk and represent the resilient demand floor. The pace of light-vehicle electrification varies dramatically "
            "by region (China leading, Europe behind, US further behind, emerging markets generally slow), creating "
            "complex regional demand mosaics.",

            "Petrochemicals are the most underrated growth vector. Naphtha and ethane feedstocks for plastics, packaging, "
            "and synthetic materials grow with developing-world consumption regardless of vehicle electrification. The "
            "buildout of major petrochemical complexes in China, the Middle East (Saudi Aramco's SATORP, ADNOC's Ruwais), "
            "and India provides a structural floor under crude demand even as transportation fuel demand peaks. Aviation "
            "is similarly resilient — sustainable aviation fuel (SAF) technology remains expensive (typically 2-4x "
            "conventional jet fuel cost) and limited in supply, while jet fuel demand grows with global middle-class "
            "travel and the recovery and expansion of Asian aviation networks. Marine bunker fuel demand grows with "
            "global trade volumes. Heavy-duty trucking and rail face limited EV penetration on relevant horizons due to "
            "battery weight constraints.",

            "Strategic petroleum reserves (SPR) and inventory dynamics add another demand layer with policy "
            "implications. The US SPR has been significantly drawn down (from over 700 million barrels to around 360 "
            "million in late 2023, partially refilling since under the Biden administration's repurchase program; "
            "Trump administration policy on SPR is uncertain). China has been a steady stockpiler, building strategic "
            "reserves opportunistically during price weakness — the actual size of Chinese reserves is opaque. India is "
            "building strategic reserves. These flows can absorb hundreds of thousands of barrels per day at the margin "
            "and are policy-driven rather than market-driven, complicating analysis of underlying demand signals."
        ),

        "outlook": P(
            "The managed-range view holds as a reasonable base case: OPEC+ defends a floor at roughly $70-80 WTI through "
            "voluntary cuts that can be expanded if needed; shale, demand concerns, and OPEC+ spare capacity cap the "
            "upside around $85-95; breakouts in either direction require either supply shocks (geopolitical disruption, "
            "intensified sanctions enforcement) or demand shocks (recession, sharp China weakness, sudden EV adoption "
            "acceleration). This managed range has held for most of the post-2022 period and reflects the genuine "
            "balance of forces. The Saudi commitment to defending the floor appears credible given the fiscal "
            "break-even of the Saudi budget (roughly $80-85 Brent equivalent given Vision 2030 spending requirements); "
            "the upside cap is enforced by the activation of OPEC+ spare capacity in any sustained price spike scenario.",

            "The bull case beyond the range: underinvestment in long-cycle supply during the 2014-2020 low-price era "
            "and the post-2020 capital-discipline era has left the supply pipeline thin beyond what shale and Guyana "
            "can fill. OPEC+ spare capacity, while currently elevated, would shrink rapidly in a demand-resilience "
            "scenario. Shale production has begun to plateau as the best Permian acreage is drilled out and capital "
            "discipline persists. EM demand growth (India in particular) is resilient and growing. Geopolitical "
            "fragility in the Middle East, Russia-Ukraine, and other producing regions creates persistent tail risk. In "
            "this view, the market is one disruption — or one sustained demand surprise — from a spike toward $100+. "
            "Major bull-leaning analysts (Goldman's Damien Courvalin, several JPM strategists) have periodically called "
            "for prices toward $100, with the calls validated occasionally but not sustained.",

            "The bear case: EV adoption accelerates globally faster than expected, particularly in major Asian markets "
            "where the cost-of-ownership has crossed below ICE in several segments. Demand peak arrives earlier than "
            "the bull case allows for; the IEA scenarios have demand peaking in the late 2020s, and recent EV data has "
            "been broadly consistent with this. China's structural slowdown becomes permanent rather than cyclical. "
            "OPEC+ unity fragments, particularly around Saudi-UAE quota disputes, leading to a price war that crashes "
            "prices (the 2020 episode being the recent precedent). The world has substantial spare capacity that gets "
            "activated, and the underinvestment thesis turns out to be wrong because shale and Guyana are simply more "
            "responsive than the bull case credited.",

            "Tail risks. Upside: major Middle East war (Israel-Iran escalation, Strait of Hormuz disruption, broader "
            "regional conflict drawing in Saudi infrastructure); Russia-related supply disruption beyond current "
            "sanctions; intensified Iran sanctions enforcement under Trump; OPEC+ surprise cut expansion; Venezuela "
            "sanctions reversal. Downside: prolonged Chinese stagnation; OPEC+ fragmentation and Saudi-led market-share "
            "war; EV adoption inflection; major recession; Iran nuclear deal resurrection releasing more Iranian oil.",

            "Catalysts and what to watch. EIA Weekly Petroleum Status Report (Wednesday 10:30 ET, Thursday if a "
            "Wednesday holiday) — the most market-moving weekly print, with crude stocks, gasoline, distillates, and "
            "refinery utilization. IEA Monthly Oil Market Report — authoritative monthly demand forecasts and OECD "
            "inventories. OPEC MOMR (monthly) — the cartel's view. EIA Short-Term Energy Outlook (monthly) — US "
            "production forecasts and global S/D. OPEC+ ministerial meetings — calendar-known events. Baker Hughes "
            "rig count (weekly Friday) — leading shale supply indicator. Geopolitical events: Russia/Ukraine, Israel/"
            "Iran, Houthi attacks on shipping, OFAC enforcement actions. Major bank oil research (Goldman, JPM, MS, "
            "Citi) — often market-moving when these desks shift outlooks. CFTC COT data weekly — speculative positioning. "
            "Saudi monthly production data and stated policy from MbS-aligned spokespeople.",

            "Tactically, oil has rewarded fading extreme positioning more reliably than chasing trends. Net-long "
            "managed-money positioning extremes (visible in CFTC COT data) have historically marked counter-trend "
            "turning points. The forward curve shape (backwardation vs contango) is a useful confirmation: structural "
            "backwardation signals genuine tightness; contango signals oversupply and increases the cost of being long "
            "via roll yield (a meaningful drag for index-rolled exposures like USO that has historically destroyed "
            "substantial value vs spot price moves). Energy-equity exposures (XLE for diversified, oil-services through "
            "OIH, individual operators) provide different risk profiles — equities have generally underperformed crude "
            "during the post-2022 strong-price period due to investor wariness about the energy-transition narrative "
            "depressing valuations even with strong cash flows."
        ),
    },

    # ──────────────────────────────────────────────────────────────────────
    # BITCOIN
    # ──────────────────────────────────────────────────────────────────────
    "btc": {
        "supply": P(
            "Bitcoin's supply schedule is the most predictable of any asset in existence and is enforced by the protocol "
            "rather than any institution. Total supply is hard-capped at 21 million coins. Block rewards halve "
            "approximately every four years (every 210,000 blocks, with average block times of 10 minutes targeted by "
            "difficulty adjustment). Following the April 2024 halving — the fourth in Bitcoin's history — block rewards "
            "dropped from 6.25 BTC to 3.125 BTC per block, reducing daily issuance from approximately 900 new BTC to "
            "approximately 450 new BTC. This represents an annualized issuance rate now below 1% of circulating supply, "
            "lower than the issuance rate of gold (1.5-2% annually). The next halving in 2028 will reduce issuance to "
            "approximately 225 BTC per day, and the schedule continues progressively until effective issuance approaches "
            "zero around the year 2140.",

            "As of recent data, approximately 19.8 million BTC of the 21 million maximum have been mined. The remaining "
            "~1.2 million BTC will be issued progressively over the next 116 years under the geometric reduction schedule. "
            "Beyond the immediate supply rate, the structural feature is that the protocol's supply schedule cannot be "
            "altered by any single party or institution — changing the supply cap would require a hard fork that the "
            "majority of network participants (miners by hashrate, full nodes for validation, exchanges and economic "
            "actors who would need to accept the new chain) would need to accept. The entire economic value proposition "
            "rests on the predictability of this schedule. The Bitcoin community has repeatedly demonstrated resistance "
            "to changing fundamental monetary parameters; the 2017 block-size wars are the canonical illustration of how "
            "contentious even modest protocol changes can be.",

            "On-chain supply dynamics matter as much as new issuance for understanding effective liquid supply. "
            "Long-term holder supply (Glassnode's metric for coins last moved more than 155 days ago) has trended upward "
            "consistently, with substantial Bitcoin held in cold storage for multi-year horizons and effectively removed "
            "from short-term liquid float. Various estimates put 'illiquid' supply (coins in addresses showing strong "
            "HODL behavior) at 70%+ of circulating supply. Exchange balances have declined substantially over the past "
            "several years — total BTC held on centralized exchanges has fallen meaningfully from peaks, with much of "
            "this Bitcoin moving to either ETF custodians (Coinbase Prime, which custodies most US spot ETF assets, is "
            "now one of the largest single holders of Bitcoin in custody) or self-custody. Lower exchange balances "
            "mean less Bitcoin readily available for short-term selling pressure, supporting price stability during "
            "periods of demand growth.",

            "Lost Bitcoin is a major consideration with implications for effective supply. Various estimates suggest "
            "3-4 million BTC are permanently lost — keys destroyed, hardware failed without backups, early miners who "
            "discarded keys before Bitcoin had material value, and accidentally-sent transactions to invalid addresses. "
            "This includes the dormant 'Satoshi coins' (approximately 1 million BTC mined by Satoshi Nakamoto in "
            "Bitcoin's first months and never moved). If a substantial portion of these are permanently inaccessible — "
            "the Satoshi coins specifically are widely presumed permanently dormant — the effective maximum supply is "
            "closer to 17-18 million BTC, meaningfully tighter than the headline 21 million. Chainalysis and other "
            "on-chain analysts publish periodic updated estimates of lost supply.",

            "Miner economics are increasingly important to short-term supply dynamics. After the 2024 halving, miner "
            "revenue per block fell by half in BTC terms; the dollar-revenue effect depends on price action. Less "
            "efficient miners (those with higher electricity costs above ~$0.05-0.06/kWh or older ASIC hardware like "
            "the S17/S19 series) faced negative gross margins at lower BTC prices, forcing some to shut down or reduce "
            "operations and creating moments of forced selling. The miner-sell pressure is observable in on-chain data "
            "(miner outflows to exchanges) and has historically corresponded with local price weakness. Public mining "
            "companies (Marathon, Riot, CleanSpark, Core Scientific, Hut 8, CipherMining, Bitfarms) provide quarterly "
            "disclosures of holdings and sales, allowing tracking of institutional-scale miner behavior. Some public "
            "miners (Marathon notably) have adopted hodl strategies, retaining mined BTC rather than selling for "
            "operational cash flow.",

            "Mining hashrate (the total computational power securing the network, measured in exahashes per second) "
            "is now near record levels around 600-700+ EH/s, indicating miners are bringing more capacity online "
            "despite the reduced per-block rewards. The hashrate growth is being driven by hyperscale operators with "
            "low electricity costs (often in west Texas, Wyoming, the Middle East, or stranded-gas locations using "
            "flare gas) running the most efficient hardware (S21 and newer-generation ASICs). High hashrate increases "
            "network security; it also means difficulty adjusts upward (mining difficulty adjusts every ~2 weeks to "
            "target 10-minute average block times), further pressuring marginal miners. The capacity additions reflect "
            "long-cycle investment decisions made when prices were materially higher and energy contracts that are "
            "difficult to wind down."
        ),

        "demand": P(
            "Spot ETF flows have become the dominant and most-watched demand signal in Bitcoin markets. The US spot "
            "Bitcoin ETFs — IBIT (BlackRock), FBTC (Fidelity), ARKB (Ark/21Shares), BITB (Bitwise), HODL (VanEck), "
            "BRRR (Valkyrie), and others including the converted Grayscale GBTC — collectively hold more than a "
            "million BTC, representing roughly 5%+ of total circulating supply absorbed in less than two years since "
            "ETF launch in January 2024. IBIT specifically has accumulated faster than any commodity ETF in history "
            "and crossed $50+ billion in AUM faster than any ETF launch ever recorded across all asset classes. Daily "
            "ETF flow data (tracked by Farside Investors, Bloomberg ETF data, and Sosovalue) is the single most-"
            "watched data point in Bitcoin markets — sustained net inflows of 5,000-15,000 BTC per week represent "
            "steady, price-insensitive accumulation that fundamentally absorbs new supply (which post-halving is only "
            "~3,150 BTC per week).",

            "The ETF inflow phenomenon has changed the marginal buyer profile in ways that may have permanently "
            "altered Bitcoin's price-formation dynamics. Pre-ETF, marginal Bitcoin demand came from crypto-native "
            "channels: existing crypto holders rebalancing, retail trading apps (Coinbase, Robinhood, Cash App), "
            "high-net-worth allocations through Grayscale's GBTC at premiums/discounts to NAV, and corporate "
            "treasuries (then a small category). Post-ETF, marginal demand includes registered investment advisors "
            "building 1-3% allocations in model portfolios (Morgan Stanley, Wells Fargo, Bank of America wealth "
            "channels have approved BTC ETF availability), family offices, pension funds (a small but growing channel "
            "with the State of Wisconsin Investment Board being the first major US public pension to disclose Bitcoin "
            "ETF holdings), endowments, and the broader financial advisor channel. This is fundamentally different "
            "demand from the previous crypto-native bull cycles and is generally less price-sensitive and longer-"
            "duration.",

            "Corporate treasury demand has been led by Strategy (Michael Saylor's MicroStrategy rebrand following the "
            "company's explicit pivot to a Bitcoin-treasury strategy), which holds over 200,000 BTC accumulated "
            "through equity and debt issuance to fund purchases. Strategy's market capitalization now substantially "
            "exceeds the underlying value of its Bitcoin holdings, with the market pricing in continued accumulation "
            "and a 'Bitcoin treasury company' multiple. The Strategy model — essentially using public equity markets "
            "to acquire Bitcoin at scale — has been imitated by smaller companies (Marathon Digital and Riot "
            "Platforms among miners; Metaplanet in Japan; various smaller companies with explicit Bitcoin treasury "
            "strategies including Semler Scientific, Trump Media's announced reserve). Total corporate Bitcoin "
            "holdings now exceed 350,000+ BTC across known treasury holders. The strategic logic varies — some treat "
            "Bitcoin as a treasury reserve asset (Tesla's earlier holdings, Block/Square), others as the explicit "
            "core business (Strategy).",

            "Sovereign and nation-state interest is still nascent but growing in importance. El Salvador holds "
            "several thousand Bitcoin as part of its legal-tender experiment, though the Bukele government has "
            "moderated some elements under IMF program negotiations. Bhutan has accumulated meaningful Bitcoin "
            "through state-operated mining using hydroelectric power. The US government holds substantial seized "
            "Bitcoin from various legal actions (Silk Road seizures, Bitfinex hacker recovery — combined holdings "
            "of 200,000+ BTC at various points). Discussion of a US Strategic Bitcoin Reserve emerged prominently "
            "during the 2024 election cycle, with the Trump administration signaling intent to establish such a "
            "reserve and Senator Cynthia Lummis introducing related legislation. Various US states have "
            "explored similar concepts (Pennsylvania, Wyoming have considered state-level Bitcoin reserve "
            "legislation). Whether any major economy adopts an active accumulation policy remains an open "
            "question — the existence of such discussions is itself meaningful for the long-term demand narrative.",

            "Retail and speculative demand persists as the cyclical layer above the structural ETF/corporate demand. "
            "Retail flows through Coinbase, Robinhood, Kraken, and international exchanges (Binance, Bybit, OKX, the "
            "Asia-focused exchanges) drive near-term momentum. Stablecoin growth (USDT now exceeds $130 billion in "
            "supply; USDC around $40 billion) is a structural enabler of retail demand globally — stablecoin supply "
            "expansion tends to flow into Bitcoin and other crypto over time. Derivatives positioning (perpetual "
            "futures funding rates, options open interest on Deribit, CME futures positioning) reflects retail and "
            "prop-firm leverage and provides tactical signals.",

            "Increasingly, Bitcoin trades as a macro liquidity-sensitive asset. Federal Reserve liquidity conditions, "
            "global central bank balance sheets, and broader financial-conditions indicators have shown strong "
            "correlation with Bitcoin's directional moves. Bitcoin rallies during periods of liquidity expansion (rate "
            "cuts, QE, fiscal stimulus, dollar weakness) and sells off during liquidity contraction (QT, tightening "
            "cycles, dollar strength episodes). This makes Fed policy and global liquidity proxies (M2 growth, "
            "central bank balance sheet aggregates) directly relevant to Bitcoin's medium-term outlook. The Bitcoin-"
            "to-Nasdaq correlation has typically been elevated during major directional moves, reinforcing the macro-"
            "risk-asset characterization."
        ),

        "outlook": P(
            "The institutional bull consensus has strengthened considerably in 2024-2025. The 'digital gold' framing "
            "has gained meaningful institutional acceptance, supported by Bitcoin's fixed supply, growing adoption "
            "infrastructure (regulated custody through Coinbase, Fidelity, BNY Mellon; ETFs; standardized "
            "derivatives on CME), and its role as a hedge against currency debasement in a high-deficit fiscal world. "
            "Major institutional reports (BlackRock's Bitcoin paper authored by Robbie Mitchnick, Fidelity Digital "
            "Assets research, ARK's Big Ideas reports, Cathie Wood's price targets) frame Bitcoin as a meaningful "
            "allocation target with multi-year time horizons. The framework supports 1-5% portfolio allocations from "
            "a wide range of institutional investors, and even modest realization of this allocation across global "
            "institutional capital would represent demand far in excess of available supply at current prices.",

            "The skeptic case requires equally careful consideration. Persistent volatility — Bitcoin has had "
            "multiple 80%+ drawdowns in its history (2011-2012, 2014-2015, 2018, 2022) and the volatility profile "
            "remains unsuitable for many institutional mandates with strict drawdown tolerances. Tight correlation "
            "to risk assets during stress episodes contradicts the 'uncorrelated digital gold' claim — Bitcoin sold "
            "off violently in March 2020 alongside everything else, sold off in 2022 alongside tech stocks and the "
            "bond crash, and remains sensitive to financial conditions. Regulatory uncertainty persists despite the "
            "ETF approvals; the SEC's posture under different administrations could materially affect institutional "
            "adoption pace. The four-year cycle structure (halving-driven) may still dictate eventual sharp "
            "drawdowns even if institutional buying smooths the path; multiple historical cycles have included "
            "post-rally drawdowns of 60-80%, and the lower-volatility post-ETF cycle may still include substantial "
            "drawdowns. Operational risks — exchange hacks, custody failures, regulatory enforcement actions — "
            "periodically affect the broader market.",

            "Tail risks both directions deserve flagging explicitly. Upside: a major sovereign adopts Bitcoin "
            "reserves (US Strategic Bitcoin Reserve being the most material near-term possibility); a major "
            "financial crisis validates the debasement-hedge thesis dramatically; corporate treasury adoption "
            "accelerates beyond current pace as more companies follow the Strategy playbook; sovereign wealth funds "
            "begin meaningful allocations. Downside: severe regulatory action (less likely given ETF approvals but "
            "not impossible — particularly around stablecoin/Tether issues affecting market liquidity); a major "
            "exchange or custody failure with cascading effects (a Coinbase issue would be systemic); quantum "
            "computing progress threatening cryptographic security (currently a long-dated tail risk but worth "
            "monitoring); persistent risk-off macro environment with broad institutional outflows.",

            "Catalysts and what to watch. Daily ETF flow data (Farside Investors, Bloomberg ETF data, Sosovalue): "
            "the single most important demand signal. FOMC decisions and broader Fed policy: liquidity drives "
            "Bitcoin. Major macro data (CPI, payrolls, GDP) for Fed-path implications. Regulatory developments: "
            "SEC enforcement actions, stablecoin legislation (Treasury and Congressional bills like the FIT21 act "
            "and various stablecoin frameworks), market structure legislation, potential CFTC vs SEC jurisdictional "
            "clarification. Corporate-treasury and sovereign-adoption announcements (Strategy's quarterly "
            "purchases, new entrants to the BTC treasury playbook, any US state or federal Strategic Bitcoin "
            "Reserve action). On-chain metrics from Glassnode and CryptoQuant: long-term holder behavior, exchange "
            "balances, miner activity, MVRV ratio. Derivatives data: perpetual funding rates, options skew, open "
            "interest. Halving cycle position — though the predictability of the cycle is debated, the historical "
            "pattern of price strength in the 12-18 months after each halving remains a reference. BTC dominance "
            "(BTC market cap share of total crypto) as alt-rotation signal — declining dominance signals alt-"
            "season, rising dominance signals flight to BTC quality.",

            "Tactically, Bitcoin has rewarded contrarian patience and punished trend-chasing at cycle extremes. "
            "Major drawdowns (50%+ from highs) have historically been productive accumulation zones; momentum tops "
            "have produced sharp reversals. The post-ETF cycle may dampen but not eliminate these dynamics. "
            "Position sizing must account for the asset's volatility — 50%+ drawdowns remain plausible even in "
            "benign macro scenarios. Direct BTC exposure (via ETF or self-custody), corporate proxies (Strategy "
            "stock as a leveraged play, but with substantial premium and execution risk), and mining stocks (high-"
            "beta, operationally levered) each have distinct risk-reward profiles."
        ),
    },

    # ──────────────────────────────────────────────────────────────────────
    # US REAL ESTATE
    # ──────────────────────────────────────────────────────────────────────
    "us_re": {
        "supply": P(
            "Commercial real estate supply dynamics vary dramatically by property type, and treating CRE as a single "
            "category obscures more than it illuminates. The starting point for any supply analysis must be the "
            "specific property type — office, multifamily, industrial, data center, retail — because the structural "
            "story differs fundamentally across categories.",

            "Office supply faces the most challenged dynamic in modern US real estate history. Pre-pandemic, US "
            "office stock totaled roughly 4 billion square feet across major markets. Post-pandemic, persistent "
            "remote and hybrid work has reduced office demand materially — Kastle Systems' Back-to-Office Index "
            "(measuring building access activity across major metros) shows occupancy generally in the 50-65% range "
            "of pre-pandemic norms across major US cities, with significant variation (Sun Belt cities showing higher "
            "occupancy than NYC, SF, or Chicago). The structural picture is that significant office space is "
            "functionally obsolete: older Class B and C buildings that were marginal pre-pandemic now face permanent "
            "demand reduction. Office construction has collapsed to multi-decade lows — new office starts in 2024 "
            "were the lowest since the 1990s by some measures — but the existing oversupply will take years to clear "
            "through conversion (office-to-residential conversions are happening but face structural challenges: "
            "floor plates often don't suit residential layouts, plumbing access points are insufficient for "
            "multifamily configurations, window configurations frequently don't allow operable windows required for "
            "residential), demolition, or repurposing. Notable conversion projects in NYC, Cleveland, Detroit, and "
            "elsewhere have demonstrated the viability of conversion for select buildings, but the practical scale "
            "remains modest relative to the oversupply. Class A trophy assets in prime locations have held value "
            "relatively well; the bifurcation between top-tier and lower-quality office is more severe than at any "
            "point in modern history.",

            "Multifamily/apartment supply has been the opposite story — heavy speculative development through 2021-"
            "2023, particularly in Sun Belt markets (Austin, Phoenix, Nashville, Charlotte, Atlanta, Tampa, Raleigh-"
            "Durham) that drew population during the pandemic. The development pipeline delivered record volumes of "
            "apartment units in 2024-2025, with total deliveries exceeding 500,000 units in 2024 — the most in "
            "decades. This wave of new supply has pressured rents materially in these markets. Rents in major Sun "
            "Belt metros have declined in year-over-year terms (Austin specifically has seen sustained "
            "year-over-year rent declines), the first material rent declines in over a decade. The development "
            "response has been to slash starts dramatically — apartment starts have collapsed to multi-year lows as "
            "rising rates and construction costs have killed project economics. National apartment starts in 2024 "
            "were less than half their 2021-2022 peaks. This creates the seeds of future supply tightness as the "
            "current oversupply works through delivery and the development pipeline empties over the next 18-36 "
            "months — by late 2026, the supply picture may have inverted from excess to scarcity. Coastal markets "
            "(NYC, LA, Boston, San Francisco) had less speculative development and have generally seen rent "
            "stability or modest growth even during the Sun Belt supply wave.",

            "Industrial/logistics supply boomed during the e-commerce explosion (2020-2022) with major development "
            "of warehouse and distribution capacity. Amazon's aggressive expansion was the dominant single-tenant "
            "driver — Amazon roughly doubled its industrial real estate footprint in two years. The post-pandemic "
            "normalization saw some industrial vacancy increase as Amazon and other e-commerce operators digested "
            "excess capacity, with Amazon notably subletting space and pausing expansion in many markets. But the "
            "structural picture remains supportive — reshoring trends, supply chain resilience priorities, and "
            "continued e-commerce penetration support industrial demand. The development response has moderated "
            "rather than collapsed, with industrial starts well off the 2021-22 peaks but maintaining a healthier "
            "pace than other property types. Industrial vacancy rates have risen modestly from historical lows but "
            "remain healthy by historical standards.",

            "Data center supply has been profoundly affected by the AI boom and represents the most acute supply-"
            "constrained property type in modern memory. Hyperscaler demand for capacity has exceeded supply across "
            "major markets (Northern Virginia, the largest US data center market; Phoenix; Dallas; Atlanta; Chicago; "
            "and emerging markets like Columbus, Ohio and Reno, Nevada), with multi-year wait lists for new capacity "
            "in some markets. The constraints are increasingly power availability rather than construction speed — "
            "major data center markets face transmission capacity limits and waiting periods for utility "
            "interconnection extending years. Dominion Energy in Virginia has flagged interconnection queues "
            "extending 5+ years. This power-constrained supply situation has driven the performance of data center "
            "REITs (Digital Realty, Equinix, the privately-held QTS), and there is no near-term supply response that "
            "can quickly resolve the imbalance. Behind-the-meter solutions (on-site gas-fired generation, nuclear "
            "partnerships, dedicated solar+storage) are emerging as workarounds for grid constraints.",

            "Retail real estate has bifurcated by quality and format. Class A malls and luxury retail centers (Simon "
            "Property Group's top-tier portfolio, Macerich's better assets) have held up well; lower-quality "
            "regional malls have struggled severely, with many converting to other uses (warehousing, residential, "
            "mixed-use development) or closing entirely. Strip centers anchored by grocery and necessity retail "
            "(Kimco, Regency Centers, Brixmor) have been resilient. The structural pressure from e-commerce continues "
            "but has moderated as consumers return to physical retail for experiences, essentials, and the social "
            "elements that e-commerce can't replicate.",

            "Higher rates and elevated construction costs (lumber, labor, and project-financing costs all up "
            "materially from pre-pandemic levels — construction-cost indices show 30-40% cumulative inflation since "
            "2020) have sharply curtailed new development across most property types. This near-term supply "
            "restriction is self-correcting some current oversupply situations and will support fundamentals for "
            "surviving and operating properties as the development pipeline empties. The aggregate story is one of "
            "supply discipline forced by rates and costs, even if individual property type situations vary."
        ),

        "demand": P(
            "Demand for real estate is sharply bifurcated by property type, again rendering 'CRE demand' an "
            "uninformative aggregate. The structurally favored property types continue to see growing demand; the "
            "challenged types face permanent demand reduction.",

            "Data centers face surging demand driven by cloud computing growth and now substantially augmented by "
            "AI workloads. Hyperscaler capex (Microsoft, Amazon, Google, Meta, Oracle, plus emerging players like "
            "xAI, CoreWeave, Anthropic's infrastructure investments) has scaled to record levels, with combined "
            "annual capex from the major hyperscalers now exceeding $250+ billion and growing. All four major "
            "hyperscalers are running multi-year expansion plans that depend on substantial additional data center "
            "capacity. The capacity additions are heavily constrained by power availability and grid "
            "interconnection — the demand is essentially uncapped relative to current supply, and the bidding for "
            "available power and land has driven prices substantially higher. Specialist data center REITs (Digital "
            "Realty, Equinix, Iron Mountain's emerging data center business) have benefited; some traditional "
            "industrial REITs (Prologis specifically) are pivoting toward data center development on existing land "
            "positions. The structural demand visibility from hyperscaler 5-10 year capex plans is unusually clear "
            "for a real estate category.",

            "Industrial/logistics demand is supported by structural drivers: continued e-commerce penetration growth "
            "(though slowed from pandemic peaks, still trending higher each year), supply chain resilience and "
            "near-shoring priorities driving manufacturing reshoring (the CHIPS Act, Inflation Reduction Act, and "
            "broader industrial policy have catalyzed significant new manufacturing investment requiring industrial "
            "space), and the broader logistics buildout supporting same-day and next-day delivery infrastructure. "
            "Major tenants include Amazon (the dominant single tenant in many markets, though pace of expansion has "
            "slowed materially from 2021-2022), Walmart, Target, FedEx, UPS, and an array of third-party logistics "
            "providers and manufacturers. Industrial demand is cyclically sensitive — economic slowdown reduces "
            "freight volumes and tenant expansion — but structurally supported. The reshoring story specifically has "
            "produced large investments in Arizona (TSMC, Intel), Ohio (Intel, others), and across the Southeast "
            "(BMW, Hyundai, various manufacturers).",

            "Residential demand is supported by housing affordability constraints in for-sale housing (high mortgage "
            "rates above 6.5% as of recent data have made homeownership unaffordable for many would-be buyers, "
            "keeping them in the rental market longer than they otherwise would be), demographic factors (millennial "
            "household formation continuing as the largest demographic cohort progresses through household-formation "
            "ages, immigration providing additional household demand), and supply constraints in many markets. The "
            "challenge is concentrated in markets that saw excess speculative supply (Sun Belt) where demand has "
            "been outpaced by supply; coastal markets with constrained supply remain tight. Single-family rental "
            "REITs (Invitation Homes, American Homes 4 Rent, Tricon Residential before its acquisition) play in the "
            "structurally favored single-family rental segment, which benefits from the for-sale affordability "
            "crisis pushing former homeowners into single-family rentals. Senior housing (Welltower, Ventas, "
            "Brookdale among operators) faces a major demographic tailwind as the baby boomer generation reaches "
            "ages of significant senior-housing demand.",

            "Office demand faces permanent reduction from remote/hybrid work. The structural picture is that office "
            "demand per knowledge worker has declined meaningfully — even employees who return to the office "
            "part-time occupy fewer total square feet per worker than pre-pandemic, as companies right-size their "
            "footprints to actual attendance patterns rather than maximum capacity. Major tenants are not renewing "
            "full pre-pandemic footprints when leases expire; tenant footprint reductions of 20-40% are common at "
            "lease renewal. The implications for office rents and values are severe. Class A trophy office in prime "
            "locations (Hudson Yards in NYC, Salesforce Tower in SF, the best assets in major CBDs) retains demand "
            "from tenants paying premium for high-quality space to attract employees back; Class B and below faces "
            "existential pressure. Vacancy rates in major office markets have risen to 15-20%+ at the metro level "
            "and substantially higher in specific submarkets (San Francisco SOMA, parts of midtown Manhattan, "
            "downtown Chicago).",

            "Retail demand has stabilized after the pandemic-era acceleration of e-commerce. Necessity retail "
            "(grocery-anchored strip centers, drug stores, dollar stores) remains resilient. Experiential retail "
            "(restaurants, entertainment venues, fitness facilities, beauty services) has recovered strongly. Class "
            "A malls (Simon Property Group's top assets, for example) continue to perform; lower-quality regional "
            "malls face ongoing challenges. The 'death of retail' narrative has proven overstated — physical retail "
            "remains the majority of US consumer spending and continues to evolve rather than disappear.",

            "Across all property types, demand is heavily mediated by the rate environment and economic growth. "
            "Lower rates would reduce financing costs (mortgage rates feed through to apartment affordability and "
            "SFR REIT economics; commercial mortgage rates affect property values and cap rates), compress cap "
            "rates (raising property values mechanically), and revive transactions. Higher rates have the opposite "
            "effects. The Fed cycle is therefore the single most important macro variable for the broad REIT "
            "sector, though property type-specific dynamics dominate within sub-sectors.",

            "CRE debt is a critical demand-related variable through a different channel. Roughly $2-2.5 trillion of "
            "CRE debt is scheduled to mature over 2024-2027, much of it originated in the low-rate environment of "
            "2020-2021 and facing significantly higher refinancing rates. The refinancing wall is most acute in "
            "office (where values may have fallen below the debt level on some properties, creating effective "
            "default situations) and in markets with substantial regional bank exposure. Regional banks have "
            "approximately $1.5 trillion in CRE exposure concentrated in office and smaller-property segments where "
            "CMBS doesn't typically participate. CRE debt refinancing outcomes will materially affect transaction "
            "volumes, distressed asset sales, and the broader sector's recovery trajectory. The first wave of "
            "office distress is now visible in CMBS delinquency data and in specific large-property distress "
            "events (245 Park Avenue, various other major office buildings)."
        ),

        "outlook": P(
            "Consensus on US real estate is necessarily bifurcated by property type rather than directional on the "
            "asset class as a whole. Constructive on: data centers (the AI capex cycle continues with multi-year "
            "visibility, power constraints support pricing power for incumbents, hyperscaler demand visibility is "
            "multi-year and growing); industrial/logistics (structural supply chain reshoring, e-commerce "
            "penetration growth, particularly in last-mile facilities serving population centers); select "
            "residential (single-family rentals, certain multifamily markets that didn't see speculative supply, "
            "senior housing benefiting from demographics, build-to-rent communities); necessity retail (grocery-"
            "anchored strip centers, dollar stores, drug stores); self-storage (mixed but generally resilient). "
            "Cautious-to-bearish on: traditional office (permanent demand reduction from remote work, refinancing "
            "wall, severe Class B obsolescence); lower-quality regional retail and lower-tier malls; multifamily in "
            "Sun Belt markets with excess speculative supply still working through delivery and absorption.",

            "The broad sector hinges on rate relief from the Fed. The standard REIT framework — REITs as bond "
            "proxies with operating-business overlays — implies that any sustained Fed easing cycle would "
            "meaningfully support REIT prices through both lower discount rates (raising property values mechanically) "
            "and lower financing costs (improving operating economics and refinancing outcomes). Conversely, "
            "sustained 'higher for longer' rates would continue to pressure the sector. The CRE debt refinancing "
            "wall is the principal systemic risk: if a significant portion of maturing CRE debt cannot be "
            "refinanced at reasonable rates, forced sales and value-impairment events could cascade. Regional banks "
            "have substantial CRE exposure (particularly to office and to the smaller-property segments where "
            "CMBS doesn't typically participate), making regional bank stress a meaningful indirect risk for the "
            "sector — and a direct linkage to the broader macro outlook through bank lending and credit creation.",

            "Tail risks. Upside: faster Fed easing than current expectations; data center demand exceeds even "
            "bullish projections (AI capex remains in its growth phase); office bottoms (highly contested but "
            "possible if return-to-office accelerates due to corporate mandates or labor market changes); reshoring "
            "boom drives industrial demand beyond current expectations; major regulatory or tax change favors REITs "
            "(unlikely but possible). Downside: prolonged higher-for-longer rate regime; CRE debt refinancing wall "
            "produces forced selling and value impairment more broadly than currently expected; regional bank "
            "stress (similar to but more severe than Silicon Valley Bank/Signature Bank/First Republic episodes); "
            "office sector deteriorates from current depressed levels to actual financial distress at major office "
            "REITs (SL Green, Vornado have been notable office-concentrated REITs); broader economic recession "
            "depresses all property types simultaneously.",

            "Catalysts and what to watch. FOMC decisions and rate expectations: the master variable. CPI and PCE "
            "prints: Fed-path inputs. CRE debt refinancing outcomes — Trepp delinquency data, major property "
            "sales, public REIT financial disclosures, individual property distress events. Office vacancy trends "
            "(CBRE, Cushman & Wakefield, JLL quarterly market reports). Data center demand signals: hyperscaler "
            "capex announcements (Microsoft, Amazon, Google, Meta quarterly earnings — quarterly capex disclosures "
            "are increasingly informative for data center demand), Equinix and Digital Realty pricing and "
            "occupancy. Industrial vacancy and rent trends (Prologis quarterly earnings provides the clearest "
            "industry pulse). Regional bank stress indicators: KBW Bank Index, individual regional bank "
            "disclosures on CRE exposure. Kastle Back-to-Office Index for office occupancy trends. Green Street "
            "Advisors Commercial Property Price Index (the gold standard for private CRE valuations). FDIC "
            "Quarterly Banking Profile. NAREIT T-Tracker for aggregate REIT operating metrics. Federal Reserve "
            "H.8 Bank Credit (weekly).",

            "Tactically, the sector has rewarded property-type-specific positioning over broad index exposure. Long "
            "data centers / industrial / select residential paired against short office (via specific REIT shorts "
            "or via CMBX office tranches) has been the structurally winning trade. Distressed value opportunities "
            "are emerging in office and in some multifamily situations but require careful underwriting given the "
            "genuine uncertainties about terminal demand. The broad sector ETFs (VNQ, IYR) blend the favored and "
            "challenged categories, which both moderates risk and dilutes returns relative to selective property-"
            "type positioning. Private REITs (BREIT, Starwood SREIT, KKR's KREST) have faced redemption pressure "
            "during the rate cycle, with NAV adjustments lagging public REIT pricing — the relative attractiveness "
            "of public vs private REITs is an ongoing capital-allocation question for institutional allocators."
        ),
    },

    # ──────────────────────────────────────────────────────────────────────
    # DXY (Dollar Index)
    # ──────────────────────────────────────────────────────────────────────
    "dxy": {
        "supply": P(
            "Dollar 'supply' is fundamentally determined by Federal Reserve policy — both the federal funds rate "
            "target (which affects the marginal opportunity cost of holding dollars) and the size and composition of "
            "the Fed's balance sheet (which directly determines the quantity of base-money dollars in circulation). "
            "The Fed's monetary policy framework as articulated since the 2020 framework review targets average "
            "inflation around 2% over time, allowing for transitory overshoots, with significant emphasis on full "
            "employment. The dual mandate creates the framework within which dollar supply policy operates.",

            "The Fed balance sheet expanded dramatically in response to the COVID crisis (from approximately $4 "
            "trillion in early 2020 to nearly $9 trillion at the 2022 peak), then contracted under quantitative "
            "tightening (QT) beginning in 2022, with the balance sheet declining toward $7 trillion by late 2024. "
            "The pace of QT has been slowed and is approaching a likely conclusion. Whether the Fed will resume "
            "QE in any future stress scenario is essentially certain — the Fed has demonstrated repeatedly (2008, "
            "2020, March 2023 banking stress) that it will expand its balance sheet aggressively to address "
            "systemic threats. The asymmetric policy reaction function — substantial easing during stress, slower "
            "tightening during recovery — has implications for long-term dollar supply that bear on the dollar's "
            "value relative to assets like gold over multi-year horizons.",

            "Beyond the Fed's domestic operations, global dollar liquidity is influenced through several "
            "channels. Fed swap lines with major central banks (the Bank of Japan, European Central Bank, Bank "
            "of England, Swiss National Bank, Bank of Canada have permanent swap lines; the Reserve Bank of "
            "Australia, Reserve Bank of New Zealand, Banco de México, Singapore's MAS, Korea's BOK, Brazil's BCB, "
            "and Denmark's Nationalbank have temporary lines that have been activated in past stress periods) "
            "allow foreign central banks to provide dollars to their domestic banking systems. Swap line usage "
            "spikes during dollar-shortage episodes (March 2020 was the dramatic recent example, with hundreds of "
            "billions in usage at peak). Foreign central bank borrowing from the Fed's Standing Repo Facility "
            "(introduced in 2021) provides another channel. These tools manage offshore dollar liquidity, which "
            "matters enormously for global financial conditions.",

            "Eurodollar markets — the offshore dollar lending and deposit market — represent dollar 'supply' "
            "outside Fed direct control. The eurodollar market is enormous (estimated at multiple trillions in "
            "outstanding claims, though precise measurement is difficult given the offshore nature), and "
            "eurodollar conditions can tighten independently of Fed domestic policy. The repo market (where "
            "dollar-denominated short-term funding occurs) is critical to short-term dollar conditions; repo "
            "rate spikes (most famously September 2019) signal dollar funding stress and have prompted Fed "
            "intervention. Bank of International Settlements quarterly data on cross-border banking provides the "
            "best public window into offshore dollar funding conditions.",

            "Treasury issuance affects dollar supply at the longer-duration end of the curve. The US federal "
            "deficit, currently running 6-7% of GDP in non-recession years and projected to remain elevated, "
            "means substantial ongoing Treasury issuance. Treasury issuance composition (the share at short vs "
            "long maturities) affects yield curve shape; the Quarterly Refunding Announcements from Treasury are "
            "important calendar events. The 'bills-led' issuance strategy of 2023-2024 (issuing primarily short-"
            "duration bills) had implications for both yield curve shape and short-term liquidity that affected "
            "broader dollar conditions.",

            "Structural de-dollarization dynamics are a slow-moving but real consideration for very-long-horizon "
            "dollar supply. BRICS-related discussions of alternative settlement systems, China's CIPS (Cross-"
            "Border Interbank Payment System), bilateral currency swap arrangements bypassing dollar settlement, "
            "and the IMF's special drawing rights as a potential reserve alternative all represent efforts to "
            "reduce dollar dependence. The actual progress has been slow — the dollar's share of global reserves "
            "has declined modestly (from ~70% in 2000 to ~58% currently per IMF COFER data) but the dollar "
            "remains overwhelmingly dominant. Practical alternatives lack the depth, liquidity, and rule-of-law "
            "framework that supports dollar use. The dynamic is real but is best understood as a multi-decade "
            "trajectory rather than a near-term policy variable."
        ),

        "demand": P(
            "Dollar demand comes through several distinct channels that don't always move together. Understanding "
            "current dollar conditions requires decomposing which channel is driving observed moves.",

            "Interest-rate differentials are the dominant cyclical driver of dollar demand. When US rates are "
            "elevated relative to other major economies, capital flows toward dollar assets to capture the yield. "
            "The US-Eurozone 2Y rate differential, the US-Japan differential, and the US-UK differential are the "
            "primary observable spreads, with the broader US-G10 differential the cleanest summary measure. "
            "Following the post-pandemic tightening cycle, the US held meaningfully higher rates than the "
            "Eurozone, Japan, and to a degree the UK and Canada — supporting dollar strength. As the global rate-"
            "cutting cycle has begun, with the ECB cutting ahead of the Fed and the BoJ moving cautiously toward "
            "normalization, the differential dynamics have become more contested. Whether the Fed cuts faster or "
            "slower than peers will determine the differential trajectory.",

            "Safe-haven demand is the dollar's crisis function. In risk-off episodes — financial market stress, "
            "geopolitical shocks, broad recession fears — capital floods to dollar safety/liquidity regardless of "
            "US-specific fundamentals. This produces the apparent paradox that the dollar can strengthen during "
            "crises that originate in the US (the 2008 global financial crisis being the canonical example: "
            "originating in US subprime, yet producing dollar strength as global investors fled to the deepest, "
            "most liquid asset class). The mechanism is partly about Treasury demand (the deepest, most liquid "
            "government debt market), partly about the dollar's role as global reserve currency creating natural "
            "demand for dollar funding when stress occurs, and partly about the unwind of dollar-funded carry "
            "trades during stress (which involves buying dollars to repay borrowed positions).",

            "Reserve demand from foreign central banks supports a baseline level of dollar holdings. The IMF "
            "COFER (Composition of Foreign Exchange Reserves) data show roughly $7 trillion in dollar reserves "
            "held by foreign central banks, representing 58-59% of allocated global reserves. China holds the "
            "largest single foreign dollar reserve position (estimated at $1.5-2+ trillion across PBoC reserves "
            "and SAFE's other dollar holdings), Japan substantial reserves (over $1 trillion), and various other "
            "central banks holding sizable positions. Reserve demand has been a slow declining share of global "
            "reserves but remains overwhelmingly the largest single category and provides a structural floor "
            "under dollar demand.",

            "Trade invoicing creates additional dollar demand. The majority of global trade is invoiced in "
            "dollars (estimates range from 50-90% depending on methodology and trade category), even for trades "
            "that don't involve US parties. Commodity trade is overwhelmingly dollar-denominated (oil, copper, "
            "gold, agricultural commodities all primarily price in dollars). This trade-related dollar demand "
            "creates structural dollar usage outside the US economy. Recent partial moves toward non-dollar "
            "settlement (Russia-China trade increasingly settling in rubles/yuan, some Middle East-China oil "
            "trade exploring alternative arrangements) represent the de-dollarization channel but remain a small "
            "share of global trade.",

            "Carry trade demand represents speculative borrowing in lower-yielding currencies to invest in higher-"
            "yielding ones, with the dollar's role varying with the rate cycle. When US rates are high relative "
            "to others (recent years), the dollar is often the borrowed currency for the carry trade is reversed "
            "— investors borrow yen or Swiss francs to invest in dollar assets, supporting dollar strength. When "
            "US rates fall below other major economies, the pattern can reverse. The yen carry trade has been "
            "the most prominent carry-trade dynamic in recent years, with the August 2024 yen carry-trade unwind "
            "producing a major short-term dollar/yen move and broader market dislocation.",

            "Speculative positioning measured via CFTC Commitments of Traders dollar index futures provides a "
            "tactical view of net dollar positioning. Extreme net long or net short positioning has historically "
            "marked turning points in the dollar cycle. Positioning is currently moderate, with shifts informative "
            "for tactical timing but not yet at extremes that would signal imminent reversal.",

            "Treasury and US asset demand from foreign investors connects dollar demand to broader financial "
            "flows. Foreign holdings of US Treasuries (China, Japan as the largest holders; broader Asian official "
            "holdings; Cayman/Belgium as conduits for various beneficial owners) and US equities create dollar "
            "demand at scale. The TIC (Treasury International Capital) data provides monthly visibility into these "
            "flows with substantial lag."
        ),

        "outlook": P(
            "The cyclical bull case for the dollar rests on continued US economic outperformance ('US "
            "exceptionalism' framing), elevated US yields relative to peers maintaining the rate differential bid, "
            "and safe-haven demand during persistent risk-off episodes. US growth has consistently outperformed "
            "the Eurozone and Japan since 2022, and the Federal Reserve's slower-to-ease posture relative to "
            "other major central banks supports continued dollar strength on the differential channel. The "
            "Trump administration's tariff agenda creates additional dollar-supportive dynamics — tariffs are "
            "typically dollar-positive both because they protect US growth at the expense of trading partners "
            "and because they reduce imports (improving the trade balance in dollar terms). Risk-off episodes "
            "during global growth scares produce safe-haven dollar bid.",

            "The cyclical bear case rests on the Fed eventually easing more than peers as US growth eventually "
            "moderates, current dollar overvaluation versus purchasing-power-parity metrics (the dollar appears "
            "overvalued by 10-20% versus major peers on PPP basis), eventual unwind of carry trades benefiting "
            "from elevated US rates, and the possibility of risk-on episodes drawing capital out of dollar safety "
            "into higher-return foreign markets. The synchronized-growth scenario — where global growth surprises "
            "to the upside and capital flows from US safety to higher-beta foreign markets (particularly EM) — "
            "would be dollar-bearish.",

            "The structural debate is more interesting. The de-dollarization thesis argues that the dollar's "
            "dominance is gradually eroding due to: (1) BRICS-related efforts to develop alternative settlement "
            "systems; (2) reserve diversification by emerging-market central banks (visible in their gold "
            "buying); (3) US sanctions policy creating incentives for non-aligned countries to reduce dollar "
            "dependence (the 2022 Russia reserve freezing being the catalytic event); (4) US fiscal trajectory "
            "raising questions about long-term dollar value. The counter-argument is that practical alternatives "
            "to dollar dominance are limited — the euro lacks the depth and political coherence to serve as a "
            "primary reserve, the yuan is constrained by China's capital controls and rule-of-law concerns, gold "
            "and crypto are partial complements but not substitutes for dollar-denominated financial "
            "infrastructure. The consensus view is gradual erosion rather than sudden shift, with the dollar "
            "remaining dominant but progressively less dominant over decades.",

            "Tail risks both directions. Upside: major geopolitical crisis triggers safe-haven dollar surge; Fed "
            "remains substantially more restrictive than peers for longer than current expectations; tariff "
            "policy produces sustained dollar-supportive dynamics; emerging market crisis triggers EM capital "
            "flight to dollar. Downside: Fed easing surprises to the dovish side relative to peers; US fiscal "
            "credibility erosion event (Treasury auction stress, debt-ceiling crisis with unprecedented outcome); "
            "synchronized global growth recovery; major BRICS coordination on settlement alternatives; persistent "
            "trade surplus reversal among major holders (China continues to reduce Treasury holdings).",

            "Catalysts and what to watch. Federal Reserve FOMC statements, minutes, projections (the Summary of "
            "Economic Projections released quarterly): the master dollar variable. BLS Employment Situation "
            "(monthly), CPI (monthly), BEA PCE (monthly), GDP (quarterly): major US data shapes Fed expectations "
            "and the dollar. Other major central bank meetings (ECB, BoJ, BoE, BoC) for the differential "
            "trajectory. Trade policy announcements: tariff threats, implementation, retaliation cycles. CFTC "
            "Commitments of Traders for dollar positioning. FRED Trade Weighted U.S. Dollar Index for broader-"
            "than-DXY measurement. BIS US Dollar Cross-Border Banking Statistics (quarterly): global dollar "
            "funding conditions. Fed swap line activity disclosure: dollar-shortage indicator. BRICS summit "
            "declarations and any concrete steps on alternative settlement. Treasury Quarterly Refunding "
            "Announcements: bond issuance and supply dynamics. TIC data (monthly with lag): foreign holdings of "
            "US assets.",

            "Tactically, the dollar tends to trade in multi-year cycles — sustained bull markets followed by "
            "sustained bear markets, often coinciding with broader macro regimes. The post-2014 dollar bull "
            "market has now lasted over a decade and is among the longest dollar bull markets on record, "
            "raising the question of mean reversion. Position sizing in dollar-related trades should account for "
            "the dollar's role in essentially every other macro asset — dollar positioning effectively underlies "
            "all other macro views and should be sized accordingly. Carry-trade unwinds can produce violent "
            "moves (August 2024 yen episode) that overshadow longer-cycle dynamics."
        ),
    },

}
