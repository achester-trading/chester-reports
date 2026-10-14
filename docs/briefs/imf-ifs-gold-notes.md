# IMF IFS central-bank gold: writer notes (10 Oct 2026)

Branch `imf-ifs-gold`, from `origin/main` at `14428ed`, not merged. Ruled 10 Oct
2026: IMF IFS is the primary source for central-bank gold. The login-gated
`wgc.*` names are superseded.

## The source as it stands today

- **The legacy service no longer answers.** A request to
  `http://dataservices.imf.org/REST/SDMX_JSON.svc/Dataflow` on 10 Oct 2026 got
  no response.
- **The current API.** The IMF documents SDMX 2.1 and 3.0 APIs for its new data
  portal (data.imf.org, "IMF API" resource page; Swagger at portal.api.imf.org).
  The writer uses the SDMX 3.0 REST endpoint at
  `https://api.imf.org/external/sdmx/3.0`, which answers anonymously, so **no
  key is needed** and no environment variable is read.
- **IFS is split into dataflows.** IFS is no longer one database. The
  gold-volume line is in the International Liquidity dataflow:
  - dataflow `IMF.STA:IL`;
  - indicator `RGV_REVS`, "Gold reserves (volume)";
  - unit `FTO`, fine troy ounces;
  - frequency `M`.
- **The request.** One query:
  `.../data/dataflow/IMF.STA/IL/+/<27 countries joined by +>.RGV_REVS.*.M?attributes=all&measures=all`.
  It returns about 39,000 observations, history back to 1950 where a country
  has it, in roughly 15 seconds.
- **The values are ounces.** China's June 2026 value is `75440000`, and its
  February 2026 value is 74,220,000, which is SAFE's own figure for that month.
  The `SCALE` attribute (6) is a display hint, not a multiplier.
- **Publication timing.** The dataset attributes carry `PUBLICATION_DATE` and
  `UPDATE_DATE`: `2026-10-10T09:00:19Z`, the same across requests hours apart.
  The writer uses the later of the two as `available_at`, with
  `availability_kind` `observed`. Where neither is present it uses the ingest
  instant (`ingest_instant`), and it never uses a stamp later than the ingest
  instant.

## Terms of use — a question for your ruling

The IMF's copyright and terms page (imf.org/en/About/copyright-and-terms) says:

- **Reuse:** users "may download, extract, copy, create derivative works,
  publish, distribute, and use Data". This requires attribution ("Source:
  International Monetary Fund, International Liquidity (IL), <link>"), and the
  citation is in `config/imf_ifs.yaml`.
- **Commercial reuse:** "email copyright@imf.org to request permission."
- **Prohibitions:** "The IMF prohibits bulk download of information by automated
  technology without explicit permission."

The API exists for programmatic import ("import data from datasets on
data.imf.org into their own systems"). The writer makes one narrow query a day:
one indicator, 27 countries, in the 16:10 pass only (not the 06:45 early set).
I read that as the sanctioned channel used narrowly, not bulk download.

- **What I could not settle:** whether the first full-history pull counts as
  "bulk", and whether this system's use counts as commercial.
- **If you want certainty:** a short email to datahelp@imf.org or
  copyright@imf.org describing the daily query would settle both.
- **If the ruling goes the other way:** removing `imf_ifs` from
  `feeds.OFFICIAL_WRITERS` stops the pull, and the stored history stays.

## What was built

| Piece | Where |
|---|---|
| Country set, API, tolerance, oz per tonne | `config/imf_ifs.yaml` |
| The writer (official group, 16:10 pass) | `altdata/sources/imf_ifs.py`, `altdata/feeds.py` `OFFICIAL_WRITERS` |
| 56 registry entries; `superseded` status; `wgc.*` re-pointed | `metrics_registry.yaml` |
| Source `imf_ifs`, live | `source_registry.yaml` |
| Code gate, on a fixture cut from the real response | `tools/validate_imf_ifs.py`, `tools/fixtures/imf_il_gold_volume.json` |
| China SAFE against IFS, 1% tolerance | `tools/validate_imf_china.py` (a data gate), `imf_ifs.crosscheck()` |

**Stored, in ounces** (tonnes are a display conversion at 32,150.7466 oz a tonne,
`imf_ifs.tonnes()`):

- **`imf.ifs.gold_reserves_oz.<iso3>`:** the month-end holding.
- **`imf.ifs.gold_net_purchases_oz.<iso3>`:** its change from the month before,
  derived from the same IMF vintage.
- **`imf.ifs.gold_net_purchases_oz.total`:** the sum of the month's net
  purchases across the configured countries that reported both months.
- **`imf.ifs.gold_net_purchases_count.total`:** how many countries that sum
  covers.

**Revisions and writes.** The aggregate grows as late reporters land, and each
growth is a new vintage. A revised value is always a second vintage, never an
overwrite. After the first write, only the last 400 days are re-sent
(`_publication`'s write window).

**The country set: 27.** The 25 largest official holders among countries, ranked
by the IL series itself as served on 10 Oct 2026:

USA, Germany, Italy, France, China, Russia, Switzerland, India, Japan, Türkiye,
Poland, Netherlands, Uzbekistan, Taiwan Province of China, Portugal, Kazakhstan,
Saudi Arabia, UK, Lebanon, Spain, Austria, Thailand, Belgium, Singapore, Iraq.

Of the ten named in the order, eight are already among the 25. Czechia and
Hungary are added.

- **Supranational holders are left out:** the IMF (2,814 t), the ECB (508 t) and
  the BIS (234 t). They are not countries, and the IMF's own gold is not
  central-bank buying.
- **Stopped reporting:** Russia (last month reported 2025-M11) and Lebanon
  (2025-M03). Both are stored, and kept off the freshness roster, so the
  heartbeat does not read a non-reporter as a stale feed.

**Why the country list exists twice.** The feeds roster reads a writer's `KEYS`
from source without importing it, so the list is a literal in the module as well
as the config. The gate fails if the two differ.

**China.** SAFE stays primary. IFS is the cross-check, and a gap over 1% on any
month both hold in the last two years is flagged by `tools/validate_imf_china.py`.
That is a data gate: it runs on the box in `make data-gates` and skips in CI.

## The IMF's publication lag, and what the January Quarterly can print

On 10 Oct 2026, the latest month served for the 25 reporting countries in the set
was:

| Latest month | Countries |
|---|---|
| Sep 2026 (about 10 days after month-end) | 5 (Japan, Türkiye, Poland, UK, Hungary) |
| Aug 2026 | 8 |
| Jul 2026 (the euro members) | 9 |
| Jun 2026 | 2 (China, Iraq) |
| Apr 2026 | 1 (Taiwan) |

The aggregate's coverage for each month on that date:

| Month | Countries covered |
|---|---|
| June | 24 |
| July | 22 |
| August | 13 |
| September | 5 |

So a month is effectively complete about three and a half months after it ends.

**For the January 2027 Quarterly, printed in mid-January:**

- **3Q26 official buying is complete.** September has reached about 24 of 25
  countries by then.
- **4Q26 is not complete.** October will be mostly in (about 22), November
  about half (about 13), and December a handful (about 5). Euro members and
  China are about three months behind, so their December lands in late March.

The Quarterly should print 3Q26 as the quarter and 4Q26 as partial, with the
count beside it. The `.count.total` series is there for exactly that line. A full
4Q26 is an April edition figure.

## The two-bid's official leg (AQ-8a), once both branches are on main

AQ-8a (branch `aq-8a-gold-residual`) reads China's holdings level and takes the
change over three prints. Its code is left untouched here. To read the IFS
aggregate instead, the aggregate is already a monthly change, so the leg sums it
rather than differencing it. That takes one config line and one code line:

```
config/attribution.yaml  two_bid.official.key: imf.ifs.gold_net_purchases_oz.total   # was safe.gold_reserves_oz
altdata/paper_bid.py     two_bid_state: "change_oz": sum(v for _, v in off[-k:]),    # was off[-1][1] - off[-1 - k][1]
```

The leg should also print `imf.ifs.gold_net_purchases_count.total` beside it, so
a three-month sum over 5 countries is not read as one over 25. That is a sentence
in AQ-8a's line, not a rule change.

## Box command (the operator, after the merge; inside the windows)

The first pull is the backfill (the API serves every month; `_publication` writes
a key's whole history on its first write). It then runs nightly in the 16:10
official pass:

```
cd ~/chester-reports && git pull --ff-only
.venv/bin/python -m altdata.sources.imf_ifs
.venv/bin/python -m altdata.sources.imf_ifs crosscheck
.venv/bin/python tools/validate_imf_china.py
```

The first command prints a JSON summary: look for `"status": "OK"` and
`"written"` around 39,000. The last two show China's SAFE-against-IFS gaps and the
gate's verdict.
