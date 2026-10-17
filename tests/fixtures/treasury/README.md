# Fixtures for altdata/sources/treasury.py

- `bitbo_public_companies.html`: BitcoinTreasuries.com's public-companies table (treasuries.bitbo.io), captured 17 Oct 2026 and trimmed to its first 25 rows.
- `edgar_shares_mstr.json`: NOT CAPTURED. EDGAR refuses any User-Agent without a contact address, and this session has none. The file follows SEC's documented companyconcept response (`units.shares[]` with `end`, `val`, `accn`, `fy`, `fp`, `form`, `filed`). The share counts are synthetic.
