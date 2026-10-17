# Fixtures for altdata/sources/gt.py

GeckoTerminal's API is not read: api.geckoterminal.com's robots.txt disallows / (17 Oct 2026).

- `swagger.json` is GeckoTerminal's own spec, read from /docs/, which robots allows.
- `new_pools_p*.json` and `trending_pools.json` are built from the spec's documented example pool (`components.schemas.pool.example`), with synthetic creation times and volumes.
- `dexscreener_search_solana.json` is DexScreener's real response, captured 17 Oct 2026 and trimmed to 6 pairs.
