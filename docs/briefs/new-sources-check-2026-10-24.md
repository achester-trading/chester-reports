# New sources for after the Monthly: the source checks (B58, session B, 24 Oct 2026)

*Checks and a brief only: no reader, no code, no data stored. Each source was
read against the 16 Oct standing rule on sources: public, keyless, easy;
robots.txt and the terms allow automated reading and storage; nothing scraped
around a refusal. Every request below was made once, from the laptop, on 23-24
Oct 2026 ET, with the repo's generic User-Agent
(`chester-reports/1.0 (+https://github.com/achester-trading/chester-reports)`,
`altdata/sources/user_agent.py`). Nothing was written but this brief. Each
source, if built, enters first as a report-only Alpha Lab hypothesis.*

## Summary

| # | Source | Verdict |
|---|---|---|
| 1 | Google News RSS, article counts per narrative | **FAILS** |
| 2 | GDELT: the DOC and GEO APIs and the raw event files | **PASSES WITH LIMITS** (the raw files; the DOC API throttled the laptop; the GEO API's v2 path is gone) |
| 3 | Google Patents public data and Google Trends through BigQuery | **FAILS the keyless test as it stands**; on Ari's yes to a Google account, PASSES WITH LIMITS |
| 4 | NOAA CPC degree days, US population-weighted | **PASSES** |
| 5 | A Chinese AI model-release watch (Hugging Face's API; GitHub release feeds) | **PASSES** (Hugging Face); GitHub releases add little |

## 1. Google News RSS: article counts per narrative

- **Verdict: FAILS.**
- **robots.txt** (https://news.google.com/robots.txt): `User-agent: *` then
  `Disallow: /`, with allows only for the home page, `/topics/`, `/publications/`,
  `/stories/` and a few others. There is no allow for `/rss`. The search feed
  (`/rss/search?q=...`) is therefore disallowed to every agent.
- **One request:** `/rss/search?q=fiscal+dominance` answered HTTP 200 with an
  RSS document of about 120 KB. The server answers; robots.txt forbids the
  reading, and a 200 does not override it.
- **The repo already ruled on this:** CLAUDE.md records "The Google News
  story-query fetch is retired: its robots.txt forbids it". The voices scan
  writes the story queries' headline rows instead.
- **What it would have measured:** a daily article count per narrative in
  `config/narratives.yaml` (12 entries), as each story's attention.
- **The keyless alternative already in place:** the narrative register's
  evidence comes from the voices scan's `headline` rows and GDELT (below). A
  per-narrative count from GDELT's raw files is the substitute; see 2.
- **Hours to build:** none (not built).

## 2. GDELT: tone and event counts for the geopolitical families

- **Verdict: PASSES WITH LIMITS.**
- **Terms** (https://www.gdeltproject.org/about.html): "all datasets released by
  the GDELT Project are available for unlimited and unrestricted use for any
  academic, commercial, or governmental use of any kind without fee", and "You
  may redistribute, rehost, republish, and mirror any of the GDELT datasets in
  any form". Storage is allowed.
- **robots.txt:** api.gdeltproject.org and data.gdeltproject.org both answer
  404, which RFC 9309 reads as no rules.
- **The three paths, one request each:**
  - **The raw event files** (https://data.gdeltproject.org/gdeltv2/lastupdate.txt):
    HTTP 200 (after a redirect to https), naming the newest 15-minute
    `export.CSV.zip` (about 49 KB), `mentions` and `gkg` files. Keyless, every 15
    minutes, from February 2015 (GDELT 2.0); the 1.0 daily files reach back to
    1979. The event rows carry the CAMEO event code, the actors' countries, the
    Goldstein scale and `AvgTone`.
  - **The DOC 2.0 API** (`/api/v2/doc/doc?mode=timelinevol` and `timelinetone`):
    **HTTP 429 to both requests and to a retry 12 seconds later.** The body asks
    callers to "limit requests to one every 5 seconds", and points high-traffic
    users to its ngrams dataset and daily briefings (the message's contact address
    is not copied here). A reader would pace itself at one request per 5 seconds or
    more and treat a 429 as STALE, never retry around it.
  - **The GEO 2.0 API** (`/api/v2/geo/geo`): **HTTP 404.** The path is gone; the
    raw files' geocoded rows are the substitute.
- **What it would measure:** per geopolitical family (Factor III and the
  Twenty-Five's geopolitical scenarios: the Taiwan Strait, the Middle East and
  the Gulf, Russia-Ukraine, the Korean peninsula), the day's count of conflict
  events (CAMEO root codes 18-20) whose actors or location match the family's
  countries, and the mean `AvgTone` of all events in that family.
- **Proposed reader:**
  - `altdata/sources/gdelt.py`, a daily step: the day's 96 export files, filtered
    by `config/gdelt_families.yaml` (countries and CAMEO roots per family);
  - store keys `gdelt.conflict_events.<family>` and `gdelt.avg_tone.<family>`;
  - report-only, in the Monthly's Factor III lines and the Weekly's tail register,
    with dual percentiles.
- **Alpha Lab hypothesis:** "A five-day sum of a family's conflict-event count
  at or above its 95th percentile of five years is followed by a rise in VIX over
  the next five sessions more often than the unconditional share."
- **Hours to build:** about 4 (the reader and its fixture, the families'
  config, the lines).

## 3. Google Patents public data and Google Trends through BigQuery

- **Verdict: FAILS the keyless test as it stands.** Both live only in BigQuery,
  which needs a Google account and an authenticated client. Under the standing
  rule, friction is a gap, not a key. **On Ari's yes to an account, PASSES WITH
  LIMITS**, with the two limits below.
- **What the account needs** (https://docs.cloud.google.com/bigquery/docs/sandbox,
  read 24 Oct 2026):
  - a Google account ("Authenticate with your Google Account, or create a new
    one");
  - **no billing account:** the sandbox lets you use BigQuery "without providing
    a credit card or creating a billing account for your project";
  - a service-account key for a scheduled reader. That is a secret for `.env` and
    the deny list, the operator's to create, not a session's.
- **The free-tier limits:**
  - "a lifetime limit of 10 GiB of storage" (not refunded when data is deleted);
  - "1 TiB of processed query data each month";
  - tables, views and partitions "automatically expire after 60 days";
  - no streaming, DML or the Data Transfer Service.
- **Limit 1: Google Trends in BigQuery is not a keyword series.**
  `bigquery-public-data.google_trends` holds "the Top 25 stories and Top 25
  Rising queries for the United States", by DMA and week, refreshed daily, each
  partition with "a time-to-live of 30 days" over a rolling five-year backfill
  (Google Cloud blog, "Top 25 Google Search terms, now in BigQuery", 28 Jun 2021).
  **It cannot count arbitrary terms** (a narrative's keywords), only say when one
  enters the top 25. That is a much weaker measure than the request assumed.
- **Limit 2: storing query results.** The sandbox page says nothing on exporting
  or storing results. Google's `patents-public-data` repository on GitHub carries
  the Apache 2.0 licence for its code; **the data tables' own licence was not
  confirmed on any page read tonight.** It has to be read on the dataset's
  Marketplace listing, from the account, before anything is stored.
- **What it would measure:**
  - patents: weekly counts of new publications in AI-relevant CPC classes (G06N,
    and H01L for semiconductors) by assignee country, for the AI thread (Factor I)
    and the Chinese AI watch;
  - Trends: the weekly appearance of a narrative's terms in the top-25 tables.
- **Proposed reader:** `altdata/sources/bq_public.py`, weekly, one parameterised
  query per measure against the public datasets, results stored in our
  observation store, never in BigQuery (the 10 GiB lifetime cap). Store keys
  `patents.ai_publications.<country>` and `trends.top25_hits.<narrative>`;
  report-only, in Factor I's lines.
- **Alpha Lab hypothesis:** "A quarter's year-on-year growth in China-assignee
  G06N publications above the US's predicts the Chinese AI model-release count
  (5) rising over the next two quarters." (A slow, structural test; it needs
  years to accrue n.)
- **Hours to build:** about 5 after the account exists (credentials, the
  queries, the licence check, the fixture).

## 4. NOAA degree days, heating and cooling, US population-weighted

- **Verdict: PASSES.**
- **Terms** (https://www.weather.gov/disclaimer): NWS information "is in the
  public domain, unless specifically noted otherwise, and may be used without
  charge for any lawful purpose", and reuse must note that it "is not subject to
  copyright protection". The CPC is part of the NWS.
- **robots.txt:** ftp.cpc.ncep.noaa.gov and www.cpc.ncep.noaa.gov answer 404,
  which means no rules.
- **One request:**
  `https://ftp.cpc.ncep.noaa.gov/htdocs/degree_days/weighted/daily_data/2026/Population.Heating.txt`
  answered HTTP 200 with plain text, pipe-delimited. Its header lines are
  "Product: Daily Heating Degree Days", "Regions:
  CPC::Regions::CensusDivisions" and "Weights: Population". There is one row per
  census division (1-9) and a `CONUS` row, and one column per day of the year to
  date. `Population.Cooling.txt` is the same for cooling, and the year
  directories run from **1981**.
- **Cadence:** daily, the file growing a column a day.
- **What it would measure:** weather-driven energy demand, population-weighted,
  against its own seasonal normal. It serves the Energy paper, natural gas (the
  EIA storage writer already in the store) and the oil buffer in Factor III.
- **Proposed reader:**
  - `altdata/sources/cpc_degree_days.py`, a daily step: this year's two files
    (and, once, every year back to 1981 for the history);
  - store keys `noaa.hdd_pop.<division>` and `noaa.cdd_pop.<division>`, with
    `conus` among the instruments; the deviation from the same calendar week's
    30-year mean computed on read;
  - report-only, beside the EIA natural-gas storage line in the Monthly's
    commodities block, with dual percentiles.
- **Alpha Lab hypothesis:** "A week's CONUS population-weighted heating degree
  days above the 80th percentile of the same calendar week's history is followed
  by a positive natural-gas front-month return over the next week more often than
  the unconditional share."
- **Hours to build:** about 3.

## 5. A Chinese AI model-release watch

- **Verdict: PASSES** for Hugging Face's API. GitHub's release feeds are keyless
  but add little.
- **Hugging Face:**
  - **robots.txt** (https://huggingface.co/robots.txt): `User-agent: *` then
    `Allow: /`.
  - **Terms:** the terms of service (https://huggingface.co/terms-of-service,
    effective 15 Sep 2022) carry no clause on automated access or rate limits;
    the API's limits are in the response headers.
  - **One request:**
    `https://huggingface.co/api/models?author=deepseek-ai&sort=createdAt&direction=-1&limit=3`
    answered HTTP 200 with JSON, one object per model repository: `id`, `createdAt`,
    `likes`, `downloads`, `tags`, `pipeline_tag`.
  - **Rate limit:** the headers read `RateLimit-Policy: "fixed window";"api";q=500;w=300`,
    500 requests per 300 seconds, anonymous.
  - **History:** deepseek-ai's oldest model repository is dated 23 Oct 2023;
    Qwen's newest on 24 Oct was 9 Oct 2026.
- **GitHub:**
  - api.github.com has no robots.txt (404 JSON).
  - Its REST API is keyless at 60 requests an hour.
  - `GET /repos/QwenLM/Qwen3/releases` answered 200 with `[]`: the labs publish
    weights on Hugging Face, not as GitHub releases.
  - github.com's robots.txt disallows a long list of paths and names AI crawlers
    apart; the API, not the site, would be read. GitHub adds little and is left
    out of the proposal.
- **What it would measure:** the count and date of new model repositories per
  watched organisation per week (organisations only: deepseek-ai, Qwen,
  moonshotai, zai-org, MiniMaxAI and peers, `config/ai_release_watch.yaml`). It
  records counts and dates only, never weights or cards. It serves the AI thread
  (Factor I, item 65's AI-trade lines, the next Disruptive Themes refresh brief).
- **Proposed reader:**
  - `altdata/sources/hf_releases.py`, a daily step: one request per organisation,
    sorted by `createdAt`;
  - store key `ai.model_releases.<org>`, weekly counts, with a `ai.model_release`
    event row per new repository (its id and date);
  - report-only, in the Monthly's Factor I lines and the Weekly's AI line.
  - A repository's `createdAt` can predate its public release, so the event's
    available_at is the pull that first saw it, never `createdAt`.
- **Alpha Lab hypothesis:** "In the five sessions after a week in which the
  watched organisations publish at or above the 90th percentile of their weekly
  model count, SMH underperforms SPY more often than in other weeks."
- **Hours to build:** about 3.

## Rulings for Ari

| # | Source | Ruling sought | Recommendation |
|---|---|---|---|
| 1 | Google News RSS | **No**: it stays retired (robots.txt forbids `/rss`) | No. Use GDELT's raw files for per-narrative counts instead |
| 2 | GDELT raw event files | Yes or no to building the reader on the raw 15-minute files, the DOC API paced and STALE on a 429 | **Yes**: free, unrestricted terms, keyless, and it covers the geopolitical families and a per-narrative count |
| 3 | BigQuery (Patents, Trends) | Yes or no to a Google account and a service-account key in `.env` | **No for now.** Trends in BigQuery cannot count arbitrary terms, and the data licence is unconfirmed; revisit for patents only if the AI thread needs it |
| 4 | NOAA CPC degree days | Yes or no to the daily reader | **Yes**: public domain, keyless, daily from 1981 |
| 5 | Hugging Face model-release watch | Yes or no to the daily reader over the declared organisations | **Yes**: keyless, explicit limits, counts and dates only |
