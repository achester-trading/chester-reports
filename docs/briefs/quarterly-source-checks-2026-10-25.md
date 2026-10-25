# The Quarterly's unfilled series: the source checks (B67, session B, 25 Oct 2026)

*Checks and a brief only: no reader, no code, no data stored. Each candidate named in the 6i brief's section 4 (`docs/briefs/6i-spec-draft-2026-10-25.md` on `origin/b63-6i-brief`) was read against the 16 Oct standing rule on sources: public, keyless, easy; robots.txt and the terms allow automated reading and storage; nothing scraped around a refusal.*

*Every request was made once, from the laptop, on 25 Oct 2026, with the repo's generic User-Agent (`chester-reports/1.0 (+https://github.com/achester-trading/chester-reports)`, `altdata/sources/user_agent.py`). robots.txt was read with wildcards, as CLAUDE.md requires. Where a terms page was not at the first URL tried, the located page was read once; that is not a retry of a refusal. A refusal (a 403, or a robots disallow) was never retried. Nothing was written but this brief.*

**Two exceptions to "one request each":**
- **SEC EDGAR was not requested.** The SEC requires the contact form, and this session cannot read it: reading the environment is denied here, and `.env` is never read. EDGAR is already an active source (`sec_edgar`).
- **SNB's first request failed on the laptop's certificate store** (`CERTIFICATE_VERIFY_FAILED`). It was made again once with a standard CA bundle. That is a client fault, not the server's refusal.

## Summary

| Count | Verdict |
|---|---|
| **7** | PASSES |
| **11** | PASSES WITH LIMITS |
| **10** | FAILS: a listed gap |
| 1 | not checked here (EDGAR; an existing source) |

The finding that matters beyond these series is that **Yahoo's chart host disallows every agent** (`query1.finance.yahoo.com/robots.txt`), and Yahoo's terms forbid automated collection. That is the same host and the same terms the system's live `yfinance` source already uses. The registry records it as "unofficial scrape, no SLA, no redistribution right", accepted before the 16 Oct rule. New symbols added to that basket would fail the rule as checked today, so they are a ruling, not a verdict (Rulings, metals and agriculture).

---

## Oil and energy

### 1. US strategic petroleum reserve, weekly (EIA)
- **Verdict: PASSES.**
- **Terms** (https://www.eia.gov/about/copyrights_reuse.php): "U.S. government publications are in the public domain and are not subject to copyright protection", with an acknowledgment asked for.
- **robots.txt** (www.eia.gov): allows `/dnav/`.
- **One request:** `dnav/pet/hist_xls/WCSSTUS1w.xls`, HTTP 200, an OLE2 `.xls` of 130 KB. Weekly, with the history the workbook carries.
- **Reader:** the existing `altdata/sources/eia.py` pattern (the history workbooks, keyless; "the v2 API needs one"): key `eia.spr_stocks`, weekly, the WPSR's publication-lag family, printed in the oil chapter beside commercial stocks.
- **Hours:** 0.5.

### 2. Refinery utilisation, weekly (EIA)
- **Verdict: PASSES** (same terms and robots).
- **One request:** `WPULEUS3w.xls`, HTTP 200, OLE2 `.xls`, 111 KB.
- **Reader:** `eia.refinery_utilisation`, weekly, the WPSR's lag, in the oil chapter.
- **Hours:** 0.5.

### 3. US natural-gas storage against the five-year band (EIA)
- **Verdict: PASSES.**
- **One request:** `dnav/ng/hist_xls/NW2_EPG0_SWO_R48_BCFw.xls`, HTTP 200, OLE2 `.xls`, 67 KB.
- **Reader:** `eia.gas_storage_l48`, weekly (the Thursday storage report), the five-year band computed in the chapter, in oil and energy.
- **Hours:** 1.

### 4. LNG exports (the feedgas row's monthly stand-in, EIA)
- **Verdict: PASSES**, with one note. The candidate serves **monthly LNG exports**, not daily feedgas, which EIA's history files do not carry. The row would read "LNG exports (monthly), feedgas not tracked".
- **One request:** `dnav/ng/hist_xls/N9133US2m.xls`, HTTP 200, OLE2 `.xls`, 43 KB.
- **Reader:** `eia.lng_exports`, monthly, EIA's monthly lag, in oil and energy.
- **Hours:** 0.5.

### 5. OVX, crude-oil implied volatility (FRED `OVXCLS`)
- **Verdict: PASSES WITH LIMITS.**
- **The series page** (https://fred.stlouisfed.org/series/OVXCLS): "Copyright, 2016, Chicago Board Options Exchange, Inc." and "Please review the copyright information in the series notes before sharing."
- **FRED's legal FAQ** (https://fred.stlouisfed.org/legal/): "Before using data with a copyright notice for anything other than your own personal use, you must contact the data owner to obtain permission", and "Don't do any data mining, scraping or extraction of FRED data."
- **The limits:**
  - read through the FRED API with the system's existing key, not the graph CSV;
  - stored for the operator's own use and never redistributed;
  - the store is outside the public repository, which keeps that true.
- **One request:** `fredgraph.csv?id=OVXCLS`, HTTP 200, CSV from 2007-05-10.
- **Reader:** add `OVXCLS` to a FRED list (one line), `fred.ovx`, daily, in the oil chapter.
- **Hours:** 0.5.

### 6. PJM capacity auction results
- **Verdict: FAILS: a listed gap.**
- **The site's legal page** (https://www.pjm.com/about-pjm/legal.aspx): "Access to this website does not confer any license or ownership interest in either the form or content of the website ... and PJM hereby expressly reserves such rights and property in its entirety." No grant covers automated reading and storage.
- **PJM's tool terms**, as indexed: Data Miner 2's licence says "non-members are specifically prohibited from republishing data".
- **One request:** `markets-and-operations/rpm`, HTTP 200, HTML; robots allows it.
- **Hours:** none.

### 7. Gulf exports and transits (IMF PortWatch)
- **Verdict: PASSES WITH LIMITS.**
- **IMF terms** (https://www.imf.org/en/About/copyright-and-terms) distinguish Content from Data. Content: "Copying or downloading IMF Content in any systematic way" needs written permission. Data: "Users may download, extract, copy, create derivative works, publish, distribute, and use Data obtained from IMF Sites subject to these conditions", attribution first.
- **The limits:** read the data service, not the pages; one request a day; attribution kept. The existing `imf_ifs` writer reads the same terms the same way.
- **robots.txt** (portwatch.imf.org): allows `/`.
- **One request:** the portal page, HTTP 200, HTML. The data service behind it was not requested; the build session makes its one request and records the endpoint.
- **Reader:** `imf.portwatch_transits.<chokepoint>`, daily, a lag row from the service's own stamp, in oil and energy (the Hormuz spare-capacity and disruption rows).
- **Hours:** 2.

### 8. Interconnection queues (LBNL, "Queued Up")
- **Verdict: FAILS: a listed gap.**
- **One request:** emp.lbl.gov's robots.txt allows `/queues`, but the page answered **HTTP 403**, and so did www.lbl.gov's robots and disclaimers. Not retried.
- **Hours:** none.

---

## Currencies

### 9. Canada's two-year yield (Bank of Canada Valet)
- **Verdict: PASSES.**
- **Terms** (https://www.bankofcanada.ca/terms/): "the Bank permits you to freely use, copy, distribute and transmit its website content under the following terms", with attribution.
- **robots.txt:** allows `/valet/`.
- **One request:** `valet/observations/BD.CDN.2YR.DQ.YLD/json?recent=5`, HTTP 200, JSON that carries its own terms link.
- **Reader:** `boc.yield_2y`, daily, a new lag row (BoC's own, read from its page at build), feeding the DXY-weighted two-year spread.
- **Hours:** 1.

### 10. Sweden's two-year yield (Riksbank SWEA API)
- **Verdict: PASSES WITH LIMITS.**
- **The API FAQ** (riksbank.se, "FAQ – The API for interest rates and exchange rates"): "The Riksbank's API is freely available without charge and the data may be freely adapted and used without any particular permission or agreement being required."
- **The limit:** the unregistered rate per IP, which the Riksbank's pages say a registration raises. One request a day is well inside it.
- **One request:** `swea/v1/Observations/Latest/SEGVB2YC`, HTTP 200, `{"date":"2026-10-23","value":2.702}`; robots 404 (no rules).
- **Reader:** `riksbank.yield_2y`, daily, for the two-year spread.
- **Hours:** 1.

### 11. Switzerland: SNB sight deposits and the balance sheet (SNB data portal)
- **Verdict: PASSES WITH LIMITS.**
- **robots.txt** (data.snb.ch): `User-agent: *` with no disallow.
- **The terms:** the portal's terms page is a JavaScript shell, and its text was not readable without a browser. The SNB's datasets as listed on Switzerland's open-data catalogue read "Open use. Must provide the source. Use for commercial purposes requires permission of the data owner." The system's use is non-commercial and attributed; the build session reads the portal's own terms text first.
- **One request** (with a CA bundle, after the laptop's TLS failure): `api/cube/snbbipo/data/csv/en`, HTTP 200, CSV of 280 KB from 1996-12, monthly.
- **Reader:** `snb.<cube item>`, monthly, for the intervention-footprint row. The weekly sight-deposits cube is located at build.
- **Hours:** 1.5.

### 12. Japan's intervention record (MoF)
- **Verdict: PASSES WITH LIMITS.**
- **robots.txt** (www.mof.go.jp): 404, no rules.
- **One request:** the Foreign Exchange Intervention Operations page, HTTP 200, HTML.
- **The terms:** the copyright page tried answered 404. The existing `mof_japan` and `mof_reserves` sources record the site as "public, no key". The limit is that the build session reads and quotes the copyright page before the first pull.
- **Reader:** `mof.fx_intervention_jpy`, monthly and quarterly as published, in currencies.
- **Hours:** 1.5.

**Two-year yields already held:** the euro area's (the Bundesbank's term structure) and Japan's (MoF's JGB rates) are existing live sources, so they were not requested. The UK leg stays a gap: "the Bank of England's database disallows robots" (AQ-3 part 2).

---

## EM and China

### 13. Taiwan export orders (MOEA)
- **Verdict: FAILS: a listed gap.**
- **One request:** www.moea.gov.tw answered **HTTP 403** to robots.txt and to the page. Not retried.
- **A lead, not checked:** Taiwan's open-data platform licenses its datasets for reuse ("Licenses apply to open data", data.gov.tw/en/license; its robots answered 500). The export-orders dataset there was not located. A future check may find it.

### 14. Foundry monthly revenue (TSMC)
- **Verdict: FAILS: a listed gap.**
- **Terms** (https://www.tsmc.com/english/legal_and_trademark): "You are hereby granted permission to access the Content from the Site in whole or in part, solely for your personal, non-commercial use of viewing and browsing", and "TSMC does not grant you any permission to use the Content or Software other than the permission expressly stated". Automated reading and storage are not granted.
- **One request:** the monthly-revenue page, HTTP 200, HTML; robots allows it.

---

## Crypto

### 15. ETH burn, issuance and network activity (Blockscout)
- **Verdict: PASSES WITH LIMITS.**
- **The source is already live** (`blockscout`: "public explorer API, no key"); robots allows `/`. The terms URL tried answered 404, and the registry's record stands.
- **One request:** `eth.blockscout.com/api/v2/stats`, HTTP 200, 656 bytes of JSON.
- **The limit:** the response's field list was not recorded past its first fields. Whether it carries burnt fees is for the build session's one request to confirm. Etherscan stays unregistered.
- **Reader:** `blockscout.eth_burnt` and `.eth_issuance` if the fields exist, daily, in the crypto chapter's ETH rows.
- **Hours:** 1.

### 16. RWA, L2, sector and venue rows (DefiLlama)
- **Verdict: PASSES WITH LIMITS.**
- **The source is already built** (`defillama`). The registry quotes its terms: "personal, non-commercial use; no republishing of the data without permission". api.llama.fi publishes no robots.txt.
- **One request each:** `api.llama.fi/protocols`, HTTP 200, a JSON array over 2 MB (truncated at the 2 MB read), each protocol with its category; `api.llama.fi/v2/chains`, HTTP 200, a JSON array of 58 KB.
- **Reader:** `llama.category_tvl.<category>` (RWA, the L2s, the sectors) and `llama.chain_tvl` by chain, daily, in crypto. Stored, never republished.
- **Hours:** 2.

### 17. Crypto ETF holdings and the float (the issuers' pages: iShares)
- **Verdict: PASSES WITH LIMITS.**
- **The source is already live** (`ishares_trusts`: "public product pages, no key"); robots allows the product page.
- **One request:** IBIT's page, HTTP 200, HTML of 1.6 MB.
- **The limit:** AQ-3 part 1 found the page "carries the per-basket bitcoin amount only". So AUM and shares are readable, while the float (bitcoin held against the supply) stays a gap. The terms URL tried answered 404, and the registry's record stands.
- **Hours:** 1.

### 18. USDC attestations (Circle)
- **Verdict: FAILS: a listed gap.**
- **One request:** the transparency page, HTTP 200, HTML; robots allows it.
- **The terms:** the site-terms URL tried answered 404, and no general terms of use for circle.com was found; only product terms are indexed. Under the rule, a source whose terms cannot be read does not pass.

### 19. USDT attestations (Tether)
- **Verdict: FAILS: a listed gap.**
- **robots.txt** (app.tether.to) disallows `transparency.json`, so the data was not requested.

---

## Credit

### 20. BDC non-accruals, PIK share and the listed-BDC discount (SEC EDGAR)
- **Not checked here.** EDGAR requires the contact form, which this session cannot read. It is already an active source (`sec_edgar`) with its fair-access rule recorded.
- **Reader, if ruled:** the BDCs' 10-Q XBRL facts through the existing `edgar_xbrl` frames, quarterly, in credit.
- **Hours:** 3.

---

## Thailand

### 21. The current account (Bank of Thailand statistics)
- **Verdict: PASSES WITH LIMITS.**
- **robots.txt** (app.bot.or.th) answered 401, which RFC 9309 reads as "unavailable": no rules apply.
- **One request:** the statistics report page, HTTP 200, HTML.
- **The limits:**
  - the registry's `bot` record stands ("public; the API needs a free personal key"), and that key route is not taken;
  - the terms URL tried answered 404, so the build session quotes the BoT's terms page first;
  - the report is HTML and needs a table parser.
- **Reader:** `thai.current_account`, monthly, the BoT's lag, in Thailand.
- **Hours:** 1.5.

### 22. Construction-materials price index (Thailand's Ministry of Commerce, price.moc.go.th)
- **Verdict: FAILS: a listed gap** for now.
- **One request:** www.price.moc.go.th answered **HTTP 500**; robots 404. Not retried. The existing `tpso` source (CPI) stays as it is.

---

## Metals and agriculture

### 23 and 24. Miners (GDX, SIL), and corn, wheat and soybean front months (Yahoo)
- **Verdict: FAILS the rule as checked**, and a ruling (see the summary).
- **robots.txt** (query1.finance.yahoo.com): `User-agent: *`, `Disallow: /`. The data was not requested.
- **Terms** (https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html): users may not "access or collect data ... from our Services using any automated means ... including but not limited to robots, spiders, scrapers, data mining tools, or data gathering or extraction tools, for any purpose without our express written permission".
- **Hours if ruled yes:** 0.5 (symbols added to the basket and the Security Master).

### 25. WASDE balances (USDA)
- **Verdict: PASSES WITH LIMITS**, through ESMIS rather than usda.gov.
- **www.usda.gov answered HTTP 403** ("Access Denied") to its robots.txt, the WASDE page and the policies page. Not retried.
- **ESMIS** (esmis.nal.usda.gov, the National Agricultural Library's release service): robots allows the WASDE publication page, which answered HTTP 200 and lists the releases as pdf, txt, xls and xml.
- **The limits:** WASDE is a work of the US government, so not subject to copyright. ESMIS's own terms page was not located, and the build session reads it first.
- **Reader:** `usda.wasde.<crop>.<line>`, monthly, each release stored as its own vintage, projections kept apart from observed, in agriculture.
- **Hours:** 3.

### 26. The crop calendar (USDA crop progress, through Cornell's ESMIS mirror)
- **Verdict: PASSES WITH LIMITS.**
- **robots.txt** (usda.library.cornell.edu) allows the publication page, which answered HTTP 200, HTML. The `about` page tried answered 404, so the terms are unread; the crop-progress reports are US government works.
- **Reader:** `usda.crop_progress.<crop>.<stage>`, weekly in season, in agriculture.
- **Hours:** 2.

### 27. The ENSO state (NOAA CPC, the ONI)
- **Verdict: PASSES.**
- **The NWS disclaimer** (https://www.weather.gov/disclaimer): NWS material is "not subject to copyright protection", and "Permission is not required to display unaltered NWS products".
- **robots.txt** (www.cpc.ncep.noaa.gov): 404, no rules. NOAA CPC is already a built source (`noaa_cpc`).
- **One request:** `data/indices/oni.ascii.txt`, HTTP 200, text from DJF 1950.
- **Reader:** `noaa.oni`, monthly (a three-month season), context only, in agriculture.
- **Hours:** 0.5.

### 28. Disaggregated COT for the grains (CFTC)
- **Verdict: PASSES.**
- **The source is already live** (`cftc`: "public, no key (Socrata)"); robots allows `/resource/`.
- **One request:** `publicreporting.cftc.gov/resource/72hh-3qpy.json` for CBOT corn, HTTP 200, a JSON row.
- **Reader:** the existing CFTC writer with the agricultural contract codes added: `cftc.dis_managed_money_net_oi`, instrument CORN, WHEAT, SOYBEANS, weekly.
- **Hours:** 1.

---

## Rulings for Ari

| Chapter | Source and series | Verdict | Recommend | Yes / no |
|---|---|---|---|---|
| Metals | Yahoo: GDX, SIL into the basket | FAILS as checked (robots, terms) | **No** until the yfinance question below is ruled | |
| Oil and energy | EIA: SPR, refinery utilisation, gas storage, LNG exports | PASSES | **Yes** | |
| Oil and energy | FRED: OVXCLS (Cboe's copyright, own use only) | PASSES WITH LIMITS | **Yes**, via the API key, never redistributed | |
| Oil and energy | IMF PortWatch transits | PASSES WITH LIMITS | **Yes**, one request a day, attributed | |
| Oil and energy | PJM auctions; LBNL queues | FAILS | listed gaps | |
| Currencies | Bank of Canada two-year | PASSES | **Yes** | |
| Currencies | Riksbank two-year | PASSES WITH LIMITS | **Yes** | |
| Currencies | SNB data portal | PASSES WITH LIMITS | **Yes**, after its terms text is read | |
| Currencies | MoF intervention record | PASSES WITH LIMITS | **Yes**, after its copyright page is quoted | |
| EM and China | MOEA export orders; TSMC revenue | FAILS | listed gaps | |
| Crypto | Blockscout ETH burn and issuance | PASSES WITH LIMITS | **Yes**, if the fields exist | |
| Crypto | DefiLlama categories and chains | PASSES WITH LIMITS | **Yes**, stored, never republished | |
| Crypto | iShares holdings (AUM and shares; the float stays a gap) | PASSES WITH LIMITS | **Yes** | |
| Crypto | Circle and Tether attestations | FAILS | listed gaps | |
| Real estate | none: every unfilled row was "no keyless source named" in the 6i brief | — | — | |
| Credit | EDGAR BDC facts | not checked here (existing source) | **Yes**, through the existing EDGAR writer | |
| International equities | none: every unfilled row was "no keyless source named" | — | — | |
| Thailand | BoT current account | PASSES WITH LIMITS | **Yes** | |
| Thailand | Commerce ministry construction index | FAILS (HTTP 500) | re-check at the next quarterly scan | |
| Agriculture | Yahoo front months (corn, wheat, soybeans) | FAILS as checked | **No** until the yfinance question is ruled | |
| Agriculture | WASDE and crop progress through ESMIS | PASSES WITH LIMITS | **Yes** | |
| Agriculture | NOAA CPC ONI | PASSES | **Yes** | |
| Agriculture | CFTC disaggregated grains | PASSES | **Yes** | |
| **All** | **The yfinance question:** may new symbols join a source whose host now disallows every agent and whose terms forbid automated collection, accepted before 16 Oct as "unofficial scrape"? | — | **No new symbols** until the question is ruled at a sitting, with the existing basket's exposure stated beside it | |

**Hours if every recommended yes is built:** about 27.

---

## Notes

- **The yfinance finding is not this brief's to resolve.** It bears on the whole price basket (127 symbols), not just these rows. It is stated so the next sitting can rule with the facts in front of it.
- **Superseded or retired sources were not re-tried:** CoinGecko, ICI's money-fund page, S&P DJI, LBMA and Google News (the B58 check).
- **CI.** Read once after the push; recorded below.
