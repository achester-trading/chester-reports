# writer-fixes-1: the official writers the first full pull broke on (17 Oct 2026)

Branch `writer-fixes-1` from the tip of `weekly-fixes-7`, so it carries Part 0 and
**merges on Monday after it**. It touches only the writers named and their
fixtures and gate. Nothing here ran on the box.

Ari's `feeds pull --skip loggers` on 17 Oct at 20:31 UTC was the first pull for
every writer Friday's merges added. 30 official writers ran: 562,928 rows
written, four STALE. 15 external writers ran: 11,940 rows, none STALE. All four
STALE lines are read below. **Three were broken parsers or queries, and so was
the fourth, the one the paste expected to be transient.**

Every fixture is cut from the real file, read from the laptop on 17 Oct 2026, and
sits under `tests/fixtures/<writer>/`. Each one says where it came from.

## 1. fedboard_h41: "H.4.1 package lacks ['tic.fima_repo', 'tic.fima_repo_weekavg']"

**Cause: the query, not the mapping.** The Board's H.4.1 package still carries
the FIMA repo line under the identifiers the writer maps:

- `H41/H41/RESPPALGTRF_N.WW`, "Assets: Other: Repurchase agreements - Foreign
  official: Wednesday level";
- `H41/H41/RESPPALGTRF_XAW_N.WW`, "… week average".

The fault was the URL's **empty `lastobs=`**. The Data Download Program now
answers that with HTTP 200 and an **empty body**, so the parser found no
identifier row and reported both keys missing. What I measured from the laptop:

- `lastobs=1`, `260`, `520` and `1000` return the package;
- `1200` returns empty;
- a `from`/`to` date range returns empty.

**Fix.**

- `URL_H41` asks for `lastobs=520`. That value is SESSION-SET: ten years of
  Wednesdays, which covers the facility from its 2020 start.
- An empty or non-CSV body now fails with what it is ("no Unique Identifier row …
  the query is wrong, not the package"), never "lacks".
- **One missing key no longer fails the package.** What parsed is written; each
  missing key is logged with its reason, returned in the summary's `absent`, and
  shown absent in the roster (`keys_without_rows`).
- Only a body with no identifier row, or no FIMA column at all, fails the run.

**Fixtures:**

- `package_2026-10-14.csv`: the six header rows and 20 Wednesdays to 14 Oct,
  the four FIMA series and two neighbours;
- `package_weekavg_only_…` (one FIMA column);
- `package_no_fima_…` (none).

## 2. nyfed_sce: "SCE workbook has no sheet 'Five-year ahead Infl Exp'"

**Cause.** The NY Fed reshaped the workbook. It now has 43 sheets, and the
five-year median is column 10 of "Inflation expectations", beside the one- and
three-year.

**Fix.**

- Each key names a pattern for its sheet and one for its column, and takes the
  first sheet that carries a matching column.
- `nyfed.sce_3y` keeps its key, so the report's three-year series is unchanged.
- The old layout still matches.
- Demo, distribution and uncertainty sheets never match.
- A key found nowhere is logged with the full sheet list and left absent; the
  rest is written.
- No inflation-expectations sheet at all raises, naming the sheets.

**Fixture:** `workbook_2026-10.json` holds every sheet name, plus the header rows
and last three months of "Inflation expectations" (Sep 2026: 3-year 3.25%,
5-year 2.995%).

## 3. frb_cie: "STALE -- the source parsed to zero rows"

**Cause: the period's format changed; the series was not withdrawn.** The URL
(`…/FEDS-Note-2873-cie-data.csv`) is unchanged and was updated on schedule, 16 Oct
2026 at 16:00 GMT (the third Friday, noon ET). The update dropped the BOM and
changed the periods:

- before: `M/D/YYYY` ("6/30/2026");
- now: `YYYY-M-D` ("2026-9-30").

Every row failed the old `strptime` and was skipped in silence.

**Fix.**

- Both forms are read.
- A file with rows but no readable period now raises, naming the first, so a
  third format cannot vanish into "zero rows" again.
- The series continues: 111 quarters to 2026Q3 (SPF 2.22, Michigan 3.13).
- **No "not tracked (source withdrawn)" line is needed.**

**Fixture:** the whole 16 Oct file, `cie_2026-10-16.csv` (2 KB).

## 4. treasury_auctions: "500 Server Error … after three retries"

**Not transient, and the query was wrong.** I checked from the laptop:

- **The cause.** TreasuryDirect renamed its record fields. `auctionDate` no
  longer exists, so `dateFieldName=auctionDate` is answered with HTTP 500 for
  **every** window. I tried a year of 2009, a year of 2025 and the 45-day
  refresh window; the error body is `{"status":500,"error":"Internal Server
  Error"}`.
- **The proof.** The same window without that parameter answers 200, and so does
  `dateFieldName=competitiveAuctionCloseDate`.
- **The bidder fields** were renamed too:

| Value | Old field | New field |
|---|---|---|
| the auction day | `auctionDate` | `competitiveAuctionCloseDate` |
| dealer award | `primaryDealerAccepted` | `primaryDealersCompetitiveParAwarded` |
| direct award | `directBidderAccepted` | `directBiddersCompetitiveParAwarded` |
| indirect award | `indirectBidderAccepted` | `indirectBiddersCompetitiveParAwarded` |
| competitive accepted | `competitiveAccepted` | `subtotalCompetitiveParAwardedInsideOfOfferingAmount` |

The identity holds under the new names. On the 3-year of 8 Sep 2026, dealers
6.285bn + direct 15.525bn + indirect 35.809bn = 57.619bn, the competitive
subtotal.

**Fix.**

- `DATE_FIELD = "competitiveAuctionCloseDate"`.
- A `FIELDS` table reads each value under its new name first, then its old one,
  so the existing fixtures (old schema) still pass.
- The backfill windows (one year per request from 2009) and the 45-day refresh
  are unchanged; they were never the problem.

**Fixture:** `search_2026-10.json`, three real records (a held 3-year note, a
held 4-week bill, an unheld TIPS), trimmed to the fields read.

**The stale path, verified.** Gate H's outage case still holds: an outage is
STALE and leaves every stored auction in place. The next scheduled run retries,
because a STALE writer is retried at its next run and nothing marks it done.
This box had no auctions stored (a first pull), so the tables were empty and
nothing was lost. The re-pull after Monday's merge backfills 2009 to date.

## 5. spdr_gld: the 11,103 rows and the browser download

**What the rows came from.** All 11,103 are State Street's daily NAV workbook
(`navhist-us-en-gld.xlsx`, www.ssga.com, robots allows it):

- `etf.gld_shares`, shares outstanding back to 2004;
- `etf.gld_share_flow`, the day-to-day change;

two keys over about 5,550 business days. **No ounces and no tonnes** were
written: `etf.gld_oz` and `etf.gld_tonnes` need the archive as their anchor, and
api.spdrgoldshares.com's robots.txt disallows it.

**One-time anchor, not a recurring line.** GLD's ounces per share move only by
the Sponsor's fee, paid in gold, which the writer already accrues forward from
the anchor (`ounces_per_share`). So **one** archive, downloaded once in a browser,
anchors the series for good. That is reference data, allowed under the 17 Oct
ruling on calendars: one download by Ari. A newer drop only re-anchors (the
writer handles it), and none is ever required. Rule 30 is not engaged, so
nothing goes on the by-hand audit's automation list.

The log message the box printed read like a standing request. It now says "Needed
ONCE, as the anchor (nothing recurring)" (`altdata/sources/spdr_gld.py`); gate U
holds it.

## Gates

`tools/validate_official_sources.py` gains group U:

- H.4.1 with and without the FIMA line, through the runner;
- the SCE workbook's current sheet names, the old layout, a partial workbook and
  an unreadable one;
- the 16 Oct CIE file and an unreadable one;
- the renamed auction schema, its identity, and the query's date field;
- the GLD message.

| Gate | Result (local) |
|---|---|
| `validate_official_sources.py` (with the writers' outage tests, groups H and the STALE cases) | 286 passed, 0 failed |
| `validate_batch3_a.py` (its own H.4.1 parse) | 60 / 0 |

No gate fetches: every fixture is a file.

## Box command, for Ari (after Monday's merge, inside a window; printed, not run)

The re-pull of the official writers, which picks up all four fixes. The auction
backfill is 2009 to date, about 18 requests:

```
ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.feeds pull --only official'
```

It should report `frb_h41`, `nyfed_sce`, `frb_cie` and `treasurydirect` OK.
`frb_h41` writes ten years of Wednesdays (most of them zero; the facility is
rarely used).

**GLD's anchor (once, yours, whenever convenient).** Download the archive in a
browser from spdrgoldshares.com/usa/historical-data/ into Drive
`chester-vendor-checks/etf/`. The nightly sweep copies it to the box, and the
next pull writes ounces and tonnes.

## Files shared with the open branches

`altdata/sources/fedboard.py`, `nyfed_sce.py`, `treasury_auctions.py`,
`spdr_gld.py` and `tools/validate_official_sources.py` (group U before `main`,
plus one line in `main`'s group list). Session A's branches carry
`validate_official_sources.py` changes from the earlier chain.

**Trial merges** (`git merge-tree`, nothing written), this branch's tip against:

- Monday's chain (`docs-batch-9`, `aud-3a`, `aud-3b`, `aud-3c`, `aud-3d`):
  **clean**.
- `st-r5-audit` and `6b-dealer-3` (the second chain, session A's line): the
  pre-existing `CLAUDE.md` conflict (main has it with them already), and **one
  in `tools/validate_batch3_a.py`**. It comes from `weekly-fixes-7`'s CI fix.
  The ECB-legs check had to stop pinning the branch name (item 11), and
  st-r5-audit inserts `group_b_daily()` on the very next line.
  - **The resolution for the Tuesday stitch:** keep weekly-fixes-7's rewritten
    check, then st-r5's `group_b_daily()` call after it.
  - st-r5's own `batch3.py` still names the branch in `EU_WRITER`, but its lines
    there do not overlap mine, so the merge takes this branch's text, and group
    M11 checks the result.

## Needs you

1. The re-pull above, after Monday's merge.
2. GLD's archive, once (above), when convenient; nothing breaks without it.

## CI

| Run | Commit | Result |
|---|---|---|
| 39072731374 (Gates, push) | `0a51898` | **passed: 82 of 82 gate jobs** (76 code, 6 data) |

Read once; green. It ran on the tip that carries `weekly-fixes-7`'s CI fix
(`a5e38e5`, itself green as run 39072463041).
