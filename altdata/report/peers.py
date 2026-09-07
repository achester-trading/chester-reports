"""
Per-asset peer pairings for the cross-asset correlation view.

Each asset has a list of peer asset_ids whose correlation is most informative
for the lens. For each pairing we include a short rationale that the dashboard
shows alongside the computed correlation. The rationale is the textbook
expectation — divergence from it is the signal.

Format:
  peers[asset_id] = [
      {"asset_id": "<peer>", "rationale": "..."},
      ...
  ]

Order matters — most informative pair first.
"""

PEERS = {

    # ─── METALS ─────────────────────────────────────────────────────────────
    "gold": [
        {"asset_id": "silver",
         "rationale": "Gold and silver share the precious-metals identity; silver typically tracks with higher beta. A breakdown in this pairing (gold rallying while silver stalls) signals safe-haven flows dominating industrial demand — a defensive regime."},
        {"asset_id": "dxy",
         "rationale": "The classic inverse relationship: dollar strength is a headwind for gold (priced in dollars globally). When gold rallies despite a strong dollar, the relationship has been broken by another force — typically central bank buying or fiscal-credibility concerns."},
        {"asset_id": "us_re",
         "rationale": "Both are real assets that historically hedge inflation. Divergence — gold up, real estate down — points to monetary debasement / safe-haven demand rather than broad inflation expectations."},
    ],
    "silver": [
        {"asset_id": "gold",
         "rationale": "Silver typically tracks gold with higher beta — the gold/silver ratio is the canonical relative-value gauge. Persistent ratio extremes flag dislocation in one of the two."},
        {"asset_id": "copper",
         "rationale": "Silver's industrial demand (solar, electronics, EVs) makes it part-cyclical. High correlation to copper signals the industrial component is dominant; decoupling signals the precious-metal identity is driving."},
    ],
    "copper": [
        {"asset_id": "china",
         "rationale": "China consumes roughly half of global copper. Copper-China correlation is the cleanest read on the Chinese cycle; a break either flags China-specific stress or the rising influence of non-China demand (electrification, grid, AI data centers)."},
        {"asset_id": "em",
         "rationale": "Copper is the canonical global-growth proxy; EM equities are highly cyclical. The pair moves together in growth phases. Decoupling can signal that copper's structural demand thesis is overcoming the cyclical EM weakness."},
        {"asset_id": "silver",
         "rationale": "Both have major industrial demand vectors. Tight co-movement signals an industrial-cycle move; divergence flags one being driven by its non-industrial use case."},
    ],

    # ─── ENERGY ─────────────────────────────────────────────────────────────
    "oil": [
        {"asset_id": "natgas",
         "rationale": "Both energy commodities, but with largely separate supply-demand dynamics — oil is global, gas is regional. High correlation signals broad energy moves (geopolitics, macro); divergence is the norm."},
        {"asset_id": "em",
         "rationale": "Oil is a global-growth and EM-demand proxy. Strong positive correlation in growth-led moves; supply-shock spikes can invert this (high oil prices pressure EM growth)."},
        {"asset_id": "cny",
         "rationale": "China is the world's largest crude importer. Yuan weakness signals China demand stress, which historically weighs on oil; persistent yuan weakness with oil holding up flags geopolitical premium or OPEC+ floor."},
    ],
    "natgas": [
        {"asset_id": "oil",
         "rationale": "Both energy, but gas is increasingly LNG-globalized rather than purely regional. Rising correlation reflects LNG-tied US prices to global energy; near-zero correlation reflects the historical regional-weather pattern."},
    ],
    "agri": [
        {"asset_id": "oil",
         "rationale": "Energy is a major input cost for agriculture (fertilizer, machinery, transport). High oil prices compress agri margins and pressure planting; biofuel mandates also link prices directly (corn-ethanol, soy-biodiesel)."},
        {"asset_id": "em",
         "rationale": "Many large agri producers and consumers are EM economies. Currency moves and demand from EM populations drive significant share of agri demand."},
    ],

    # ─── CRYPTO ─────────────────────────────────────────────────────────────
    "btc": [
        {"asset_id": "eth",
         "rationale": "BTC and ETH are the two largest crypto assets and trade in tight correlation. The BTC/ETH ratio is the canonical rotation signal — a falling ratio signals risk-on/alt-season; a rising ratio signals flight to crypto quality."},
        {"asset_id": "gold",
         "rationale": "The 'digital gold' thesis claims BTC behaves as a debasement hedge / store of value. The reality: BTC's correlation to gold is unstable and typically lower than its correlation to risk assets. A genuine high BTC-gold correlation would be a major validation of the digital-gold thesis."},
        {"asset_id": "sol",
         "rationale": "BTC vs SOL captures the BTC-vs-alt-coin rotation. SOL outperforming BTC signals risk-on appetite; underperformance signals concentration in BTC quality."},
    ],
    "eth": [
        {"asset_id": "btc",
         "rationale": "ETH typically trades 0.7-0.9 correlation to BTC. The ETH/BTC ratio is the cleanest measure of ETH's relative attractiveness — sustained ratio downtrend signals BTC dominance and ETH's persistent value-capture problem."},
        {"asset_id": "sol",
         "rationale": "ETH and SOL compete in the smart-contract layer. Tight correlation is the norm; SOL outperforming materially flags rotation away from ETH on adoption or technical concerns."},
    ],
    "sol": [
        {"asset_id": "eth",
         "rationale": "Direct L1 competitor. The SOL/ETH ratio is the canonical alt-vs-ETH rotation gauge."},
        {"asset_id": "btc",
         "rationale": "SOL has the highest beta among major crypto. Strong correlation to BTC in directional moves; SOL leads BTC in alt-season rallies and lags in flight-to-quality."},
    ],
    "zec": [
        {"asset_id": "btc",
         "rationale": "Zcash shares Bitcoin's hard-cap monetary policy and was originally a Bitcoin fork. High beta to BTC; ZEC outperformance is rare and typically tied to privacy-coin-specific catalysts."},
        {"asset_id": "eth",
         "rationale": "Both alt-coins with technical narratives (privacy for ZEC, smart contracts for ETH). Correlated as part of the broader alt complex; divergence flags privacy-coin regulatory news."},
    ],

    # ─── REAL ESTATE ────────────────────────────────────────────────────────
    "us_re": [
        {"asset_id": "tlt",
         "rationale": "REITs are highly rate-sensitive; the inverse relationship with long bonds is fundamental. A break here — REITs falling alongside bonds — signals credit stress separate from rates (CRE-specific) and is the primary lateral confirmation channel for credit-spread widening."},
        {"asset_id": "intl_re",
         "rationale": "Different regional real estate markets respond to local rate cycles, demographics, and currency. Tight correlation signals global rate cycle dominating; divergence flags regional-specific drivers."},
    ],
    "intl_re": [
        {"asset_id": "us_re",
         "rationale": "Globally listed real estate moves with shared rate-sensitivity, but local cycles can dominate. Divergence often reflects regional rate differentials or currency moves."},
        {"asset_id": "em",
         "rationale": "International property and EM equities share exposure to global growth and dollar dynamics."},
    ],

    # ─── REGIONAL EQUITY ────────────────────────────────────────────────────
    "em": [
        {"asset_id": "dxy",
         "rationale": "The single most important EM relationship: dollar strength is an EM headwind (financing costs, capital outflows). Inverse correlation is the textbook view; tight inverse correlation confirms the dollar cycle is the master variable."},
        {"asset_id": "china",
         "rationale": "China is the largest EM-index constituent. EM-China correlation measures how much of EM is the China story vs the rest (India, Korea, Taiwan, LatAm)."},
        {"asset_id": "copper",
         "rationale": "EM is highly cyclical and tied to global growth. Copper-EM correlation is the global-cycle confirmation pair."},
    ],
    "china": [
        {"asset_id": "copper",
         "rationale": "China consumes about half of world copper. Copper-China correlation is the cleanest read on the Chinese cycle."},
        {"asset_id": "em",
         "rationale": "China is the largest EM constituent. China leading EM higher or lower flags the China-specific component of the move."},
        {"asset_id": "cny",
         "rationale": "Equity-currency correlation within a single economy. Weak yuan with weak Chinese equities confirms broad pessimism; divergence (equities up, yuan still weak) flags managed-currency dynamics or stimulus-driven asset rally not yet reflected in capital flows."},
    ],

    # ─── CURRENCIES ─────────────────────────────────────────────────────────
    "dxy": [
        {"asset_id": "eur",
         "rationale": "EUR is the largest DXY component (~57%); they move inversely by construction. The pair is mechanical — but divergences vs the broader dollar trade-weighted index can flag EUR-specific moves (ECB, periphery stress)."},
        {"asset_id": "jpy",
         "rationale": "JPY is roughly 14% of DXY. The dollar-yen pair is also a major carry-trade gauge — yen strength against the dollar is often a stress signal beyond what DXY alone shows."},
        {"asset_id": "em",
         "rationale": "Inverse dollar-EM relationship is one of the cleanest in global macro. EM rallying despite dollar strength flags structural EM bid (e.g., India structural flows) overcoming the cyclical headwind."},
    ],
    "eur": [
        {"asset_id": "dxy",
         "rationale": "EUR/USD dominates DXY; inverse relationship is mechanical. Divergences reflect EUR-specific moves vs the broader dollar."},
        {"asset_id": "intl_re",
         "rationale": "European real estate is rate-sensitive to ECB policy; the EUR captures the broader ECB-vs-Fed differential."},
    ],
    "jpy": [
        {"asset_id": "tlt",
         "rationale": "Both are safe-haven assets that strengthen during risk-off. Tight positive correlation confirms a true risk-off regime; divergence (yen up, bonds down) flags carry-trade unwind dynamics distinct from broad risk-off."},
        {"asset_id": "dxy",
         "rationale": "The yen has been the world's premier carry-trade funding currency. Yen strength against the dollar is a stress signal (carry unwind, repatriation flows)."},
    ],
    "cny": [
        {"asset_id": "china",
         "rationale": "Currency-equity link within one economy. Weak yuan with weak Chinese equities reflects broad pessimism; divergence is the managed-currency tell — a stimulus rally not yet validated by capital flows."},
        {"asset_id": "copper",
         "rationale": "Yuan weakness signals Chinese demand stress, which weighs on copper. Persistent yuan weakness with copper holding up flags non-China structural demand absorbing the slowdown."},
    ],
}
