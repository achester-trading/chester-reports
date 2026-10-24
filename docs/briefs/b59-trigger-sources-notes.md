# b59-trigger-sources: D15, the one-day 10-year trigger, and D26, three new sources (session B, 24 Oct 2026)

**What it is.** The rulings of 24 Oct 2026:
- **D15:** a one-day 10-year move runs the attribution, with its own pre-registered ledger;
- **D26:** GDELT's raw event files, NOAA CPC's degree days and a Hugging Face model-release watch are built as report-only readers, each registered first as an Alpha Lab hypothesis. Google News RSS stays retired, and BigQuery is not built.

**THIS BRANCH MERGES AFTER THE 1 NOV MONTHLY.** It is branch-only: pushed, not merged, nothing run on the box, no unit, no secret, no `.env`, no register write. Nothing here enters a composite or the market-state object.

## Base

- **Branch:** `b59-trigger-sources`, cut from `origin/chain-6` at `69cc88d`. That was chain-6's tip when fetched on 24 Oct about 12:15 ET; it had not moved.
- **Worktree:** `../chester-b59`.
- **Read only:** the rulings log (`C:\Users\arich\Downloads\rulings-2026-10-24.md`, D15 and D26) and B58's brief (`docs/briefs/new-sources-check-2026-10-24.md` on `origin/b58-sources-check`).

## The commits, in order

| Commit | What |
|---|---|
| `5bc0ce2` | Part 1 (a): D15's pre-registration, committed **alone**, before any scoring code |
| `fe1fe6c` | Part 2 (a): the three hypotheses, committed **alone**, before any reader |
| `05a2290` | Part 1 (b): D15's module, config and scoring script, and the laptop first edition |
| `05d77fd` | Part 2 (b): the three readers, their configs, keys, sources, publication lag and catalogue lines |
| `b3df812` | Parts 1 and 2 (c): the placements, the basket's steps, the rosters, the EOD resolve |
| (next) | Part 3: the gate, the Makefile, CLAUDE.md, the Master Guide's Table 7a and its HTML, these notes |

## The source checks, re-confirmed before each reader (24 Oct 2026, from the laptop, the repo's generic User-Agent)

| Source | robots.txt | Terms (the deciding clause) | One request |
|---|---|---|---|
| **GDELT raw files** (data.gdeltproject.org) | 404: no rules (RFC 9309) | "available for unlimited and unrestricted use for any academic, commercial, or governmental use of any kind without fee" (gdeltproject.org/about.html) | `gdeltv2/lastupdate.txt` 200, naming the 16:30 UTC export. The 1.0 daily file for 23 Oct: 200, 7.4 MB zipped, 117,193 events |
| **NOAA CPC** (ftp.cpc.ncep.noaa.gov) | 404: no rules | NWS information "is in the public domain ... and may be used without charge for any lawful purpose" (weather.gov/disclaimer) | the daily-data index 200, years from 1981; the 2026 heating file's newest column 22 Oct |
| **Hugging Face** (huggingface.co) | "User-agent: *" then "Allow: /" | no clause on automated access in the terms of service; the API's limit in its headers: `RateLimit-Policy: "fixed window";"api";q=500;w=300` | `/api/models?author=Qwen...` 200; every declared organisation answered 200 |

Each config file (`config/gdelt.yaml`, `config/cpc_degree_days.yaml`, `config/ai_release_watch.yaml`) records its check, and so does each source's `license` in `source_registry.yaml`. **GDELT's DOC API is not read:** it answered 429 to the laptop on 23-24 Oct and asks one request per 5 s, and the raw files carry what the reader needs.

## Part 1: D15, the one-day 10-year trigger

- **The trigger** (`altdata/oneday_10y.py`, `config/oneday_10y.yaml`):
  - DGS10's change from the stored observation before, in bp;
  - against the 97.5th percentile (linear interpolation, `derived.percentile_at`) of the absolute one-day changes on the stored days in the five years before;
  - fires when the absolute change is greater, either sign;
  - under 1,000 prior changes it prints "not read".
- **The attribution** is `speed_attribution.attribute()` over one session: KW and ACM, each read only with an observation on the day (F5). A model whose input is not stored prints "awaiting"; one model read makes the read "partial".
- **The ledger** is `rates.oneday_event_ledger`:
  - the close writes it on a trigger day, never on a dry run;
  - `python -m altdata.oneday_10y resolve` runs in the EOD pass after the speed flag's, warn-only. Each resolution is a new vintage: the attribution once the inputs land, and the 5- and 20-session outcomes.
- **Where it prints:**
  - **the close:** one flag line in Mechanics' event area, after item 52's, item 65's and item 73's events;
  - **the Weekly and the Monthly:** a block in Mechanics after the event blocks, either a table of the trigger days with each model's share and the leg, or one line that none fired.
- **The pre-registration** is `docs/ledgers/oneday-10y-preregistration-2026-10.md`. Its SHA-256 over the LF bytes is **`a6423e64a90e81ace210f814e645d32224d701e94b7c730736a98e67615320d3`**. `validate_b59` group B holds it, and checks that its commit precedes the module's and the script's.
  - **Outcome:** the 10-year's change over 5 sessions, with 20 printed beside it.
  - **Groups:** by the leg that carried the move.
  - **Rule (a57's shape):** at least 15 episodes per group, shares 0.15 apart, the same sign by half.
  - **Episode:** a trigger day with no trigger in the 5 sessions before.
- **The laptop first edition** is `docs/ledgers/d15-ledger-2026-10-24.md` with its episodes CSV, from public sources (FRED DGS10 and THREEFYTP10, the New York Fed's ACM workbook). It reads **INSUFFICIENT, n 67**:
  - the term premium carried 2 episodes and expected short rates 65; the models disagree on 80 of the 147 episodes since 1990;
  - continuation is 0.50 against 0.43, with halves -0.33 and +0.47.

  The verdict reaches the register only as a rule-31 draft, and grants nothing.

## Part 2: D26, the three readers

**The hypotheses first.** `alpha/research/hypotheses-2026-10-24-b59-sources.yaml` (`fe1fe6c`, alone, before any reader) follows the alpha-lab-hypotheses/v1 schema: source `model`, channel `sitting`, `model_idea_rule: true`, and no backtest run.

| Hypothesis | Claim (B58's brief) | Grammar |
|---|---|---|
| H-B59-1 GDELT | A family's five-day mean conflict share at or above its five-year 95th: VIX up over the next 5 sessions more often than unconditionally | **needs code**: no n-day mean transform, a family instrument, and the VIX index is not traded |
| H-B59-2 degree days | A week's CONUS HDD above the 80th percentile of the same ISO week's history: Henry Hub up over the next week more often | **needs code**: no same-week seasonal percentile; Henry Hub is a FRED series, not a symbol |
| H-B59-3 model releases | The weekly total at or above its 90th percentile of 104 weeks: short SMH against SPY for 5 sessions | **in the grammar** (`rule_dsl` v1, compiles: daily close, next close, time 5, cooldown 5) |

The operator registers the batch on the box by manifest (box commands below).

**1. GDELT** (`altdata/sources/gdelt.py`, `config/gdelt.yaml`):
- **Daily step:** each complete UTC day of the last 3 not yet stored, 96 exports, 1.5 s apart.
- **A failed or refused export** marks the day STALE with its reason; nothing is written and nothing is ever filled.
- **The families** follow the Twenty-Five's Family D and Factor III:
  - the Taiwan Strait (TWN, or a CHN dyad with USA, JPN or PHL);
  - the Middle East and the Gulf;
  - Russia and Ukraine;
  - the Korean peninsula;
  - US and China, as economic warfare.

  A family matches by actor CAMEO country, action FIPS location or dyad.
- **The measures:** conflict (CAMEO roots 18-20) and reduce relations (root 16).
- **The level is a share per 10,000** of the day's events, so it does not move with GDELT's own volume. On 23 Oct the 2.0 exports and the 1.0 file held the same 117,193 events.
- **The tone** is the mean AvgTone of all the family's events.
- **Per story:** the distinct articles whose address carries one of the story's phrases, matched on whole words of the URL slug. The event files carry no text.
- **The backfill** (the operator's) uses the 1.0 daily files, one request a day, reconstructed at the next day's noon UTC.
- **It prints in:**
  - the Weekly's tail register (one line: the family highest on its percentile);
  - the Weekly's and the Monthly's narratives sections (a table of articles per story);
  - the Monthly's Factor III (each family's share with dual percentiles, its counts and tone).

**2. NOAA CPC degree days** (`altdata/sources/cpc_degree_days.py`, `config/cpc_degree_days.yaml`):
- **Daily step:** this year's two files (and last year's in early January). It writes each new day, and a new vintage only where a re-read day (14 days) changed.
- **The keys:** `noaa.hdd_pop` and `noaa.cdd_pop`, instrument CONUS or the census division.
- **The normal** is computed on read: the 1991-2020 mean of the same calendar day, needing at least 20 of those years. The departure is printed with the dual percentiles of seven-day departures.
- **It prints in** "Energy: degree days beside natural gas", after the oil-shock signature in the Weekly's and the Monthly's Mechanics, with Henry Hub spot (FRED DHHNGSP) beside it.

**3. The Hugging Face model-release watch** (`altdata/sources/hf_releases.py`, `config/ai_release_watch.yaml`):
- **Daily step:** one listing per declared organisation, newest first, paged by the Link header only as far back as the 4 recounted weeks.
- **The keys:**
  - `ai.model_releases_week`, per organisation;
  - `ai.model_releases_week_total`, written only when every organisation was read;
  - `ai.model_release_event`, one row per new repository, available at the pull that first saw it, never at `createdAt`.
- **Counts and dates only.**
- **It prints in** the Weekly's narratives (the AI line) and the Monthly's Factor I-b block (a table by organisation), each release a dated event.
- **The backfill's weeks are reconstructed from `createdAt`**, and the block says from when the history is point in time.

**Wiring.** All three are steps of the crypto basket's 17:25 run (`scripts/run_crypto_basket.sh`), with no new timer and no unit. They are on the freshness roster (`gdelt`, `degree_days`, `ai_releases`).

## The three readers' first laptop reads (24 Oct 2026, dry runs: nothing stored)

- **GDELT:** 23 Oct UTC, 96 exports in 226 s, 117,193 events, 22,958 source articles, no malformed line.
  - The Middle East and the Gulf: 1,613 conflict events, 137.6 per 10,000.
  - Russia and Ukraine: 510 conflict events, 43.5.
  - The Taiwan Strait: 37 conflict and 36 reduce-relations events, 3.2.
  - Stories: the midterm cycle 184 articles, AI capex 102.
- **NOAA CPC:** both 2026 files through 22 Oct. CONUS read 7 HDD and 1 CDD on 22 Oct, and 60 HDD over 16-22 Oct. 260 rows would be written. The normal is "not read" until the backfill lands.
- **Hugging Face:** all 15 organisations read in 16 s, with nothing STALE.
  - The weekly totals: 8 (21 Sep), 2 (28 Sep), 4 (5 Oct), 10 (12 Oct).
  - Among the newest: DeepSeek-V4.1-Flash-1017 (17 Oct) and MiniMax-M3.1-Flash (17 Oct).

## Part 3: the gate

`tools/validate_b59.py`, a new gate: **83 checks, groups A to H**, synthetic fixtures only (no network, no live store, no model).
- **(A)** The trigger's percentile by hand; both signs; strictly "beyond"; "not read" under 1,000; absent; "awaiting", partial and disagree legs by hand.
- **(B)** The outcomes by hand; the ledger row; resolve's new vintage; the pre-registration's SHA-256 and git order; INSUFFICIENT, PASS and FAIL; the first edition as printed; the script opens no store.
- **(C)** The batch validates and is within budget; H-B59-3 compiles; the other two need code with their reasons; no backtest committed; the batch committed alone and before each reader (git order).
- **(D)** GDELT on a fixture export in both layouts:
  - the families by actor, location and dyad;
  - the share by hand;
  - whole-word URL matching;
  - the malformed row and the other day's row left out;
  - the zero rows;
  - the STALE path writing nothing;
  - the pacing (95 pauses);
  - a stored day not re-read.
- **(E)** NOAA: parsing (a bad cell left out); the normal and departure by hand; no normal under 20 years; an unchanged re-read writes nothing; a failed fetch; January reads two years.
- **(F)** Hugging Face: the weekly count by hand; the organisation filter; Link paging and its stop; a refused organisation STALE with no total; an event available at the pull; no repository counted twice.
- **(G)** Placement in the close, the Weekly and the Monthly, the hooks, the steps, the rosters and the EOD resolve.
- **(H)** Every new key registered and trigger-ineligible; each key barred from the market-state object (named in neither `config/market_state.yaml` nor `regime.py`; 6f's registry field arrives on a62); the sources and their dated checks; the lag row; the catalogue; no forbidden import; no unit; no handle or email address.

**The count:** 138 code gates (135 Python, three shell) and 8 data gates, recounted on chain-6's 137 plus this one. CLAUDE.md's line and `validate_audit_3a` (88/0) agree.

**Run locally:**

| Gate | Result |
|---|---|
| `validate_b59` | 83/0 |
| `check_registry` | OK |
| `check_library` | 0/0 |
| `validate_official_sources` | 340/0 |
| `validate_audit_3a` | 88/0 |
| `check_master_guide` | 0/0, after Table 7a gained D15's two files and the HTML was rebuilt |
| `validate_b51_registry_html` | passed (the lag row) |

The stack gates are left to CI.

**CI:** recorded below once read.

## Listed gaps

1. **GDELT's DOC API**: not read (429 to the laptop; one request per 5 s). The raw files serve the counts, so nothing depends on it.
2. **The article text for the per-story counts**: GDELT's event files carry only the address, so a story counts only where its phrase is in the URL slug. That undercounts, and the line says "attention, not agreement".
3. **The Hugging Face history before the first daily pull**: reconstructed from `createdAt`. A repository created private and published later is counted in its creation week, and only from the pull that sees it once it is live.
4. **Google, Microsoft and NVIDIA's Hugging Face organisations**: left out; their hundreds of research checkpoints a year would swamp the frontier count. Listed in the config.
5. **The degree-day normal before the backfill**: "not read" until 20 of 1991-2020's years are stored.
6. **BigQuery (Patents, Trends)** is not built (D26) and **Google News RSS** stays retired (D26).

## Every session-set value, with its reason

| Value | Setting | Reason |
|---|---|---|
| D15 outcome horizon in the rule | 5 sessions (20 printed beside) | a one-day trigger's natural horizon; 20 is the speed flag's |
| D15 episode gap | no trigger in the 5 sessions before | the rule's horizon, so episodes' outcomes do not overlap |
| D15 attribution horizon | one session | the trigger is the one-day move |
| GDELT pause | 1.5 s between exports | no stated limit for the raw files; a day in about 2.5 minutes |
| GDELT catch-up | the last 3 complete UTC days | a missed run catches up; older days are the backfill's |
| GDELT backfill reach | 365 days by default | about 2.6 GB at one 7 MB request a day; the operator may give more |
| GDELT families and dyads | five families (Family D and Factor III) | the Twenty-Five's geopolitical scenarios and Factor III's economic warfare |
| GDELT measures | conflict: CAMEO roots 18-20; reduce relations: root 16 | material conflict; sanctions and embargoes |
| GDELT share | per 10,000 of the day's events | comparable across GDELT's volume and its two layouts |
| GDELT story phrases | `config/gdelt.yaml` `narratives`, eleven stories | each story's own terms, as whole words of the URL |
| NOAA re-read | 14 days, a new vintage only on a change | the newest days are preliminary |
| NOAA normal | 1991-2020, at least 20 years | NOAA's current normals period |
| NOAA window | 7 days; five-year and full percentiles | a week of demand |
| NOAA publication lag | 2 sessions (bound 3) | the file's newest column is two days old |
| Hugging Face organisations | 12 Chinese labs and 3 peers | the brief's five and their open-weight peers; three swamping organisations left out |
| Hugging Face recount | 4 weeks | a late-published repository lands in an older week |
| Hugging Face pause | 0.5 s | a tenth of the stated limit |
| Hugging Face percentile window | 2 years (104 weeks) | the hypothesis' window; the history starts in 2023 |

## Differences from the paste

- **The DOC API** is not used at all (the paste allowed it "only if used at all"); the raw files suffice.
- **GDELT's history** uses the 1.0 daily files, one request a day rather than 96. Both layouts are parsed, and the share keeps them comparable. On 23 Oct both held the same events.
- **"Departure from normal"** is computed on read and not stored, as B58's brief proposed.
- **D15's block** in the Weekly and the Monthly is in Mechanics, after the gold and developed-market events (a58's), which are the existing event blocks there.

## Files shared with other branches

- `CLAUDE.md`, `Makefile`, `metrics_registry.yaml`, `source_registry.yaml`, `config/catalogue_commands.yaml`, `config/publication_lags.yaml`.
- The Master Guide and its HTML.
- `altdata/feeds.py`.
- The stack hooks: `daily_cascade/stack.py`, `stack_close.py`, `weekly_stack.py`, `monthly_macro/stack.py`.
- `scripts/run_crypto_basket.sh`, `scripts/run_eod_cron.sh`.

All are additive, each a one-block insertion after a58's or b56's.

## The box commands (for the chain-7 box sheet; the operator's, after the merge, inside the windows, dry runs first)

```
cd ~/chester-reports
# The hypotheses, by manifest (before any reader's first pull):
.venv/bin/python -m alpha.manifest register alpha/research/hypotheses-2026-10-24-b59-sources.yaml
# The first pulls, dry runs first:
.venv/bin/python -m altdata.sources.gdelt daily --dry-run
.venv/bin/python -m altdata.sources.cpc_degree_days daily --dry-run
.venv/bin/python -m altdata.sources.hf_releases daily --dry-run
# The histories (each once):
.venv/bin/python -m altdata.sources.cpc_degree_days backfill --dry-run
.venv/bin/python -m altdata.sources.cpc_degree_days backfill          # 92 requests, about 2 minutes
.venv/bin/python -m altdata.sources.hf_releases backfill --dry-run
.venv/bin/python -m altdata.sources.hf_releases backfill
.venv/bin/python -m altdata.sources.gdelt backfill --days 365 --dry-run
.venv/bin/python -m altdata.sources.gdelt backfill --days 365         # 365 requests, about 2.6 GB, under an hour
# The reads (read-only):
.venv/bin/python -m altdata.sources.gdelt show
.venv/bin/python -m altdata.sources.cpc_degree_days show
.venv/bin/python -m altdata.sources.hf_releases show
.venv/bin/python -m altdata.oneday_10y show
.venv/bin/python -m altdata.oneday_10y resolve --dry-run
# D15's box edition, outside the checkout:
.venv/bin/python tools/calibration/d15_oneday_10y.py --box --out ~/chester-data/ledgers
```

**Expect:**
- `gdelt daily --dry-run`: three days of about 117,000 events each;
- `cpc_degree_days daily --dry-run`: about 260 rows;
- `hf_releases daily --dry-run`: 15 organisations, `failed` empty;
- `cpc_degree_days show`: a normal and a departure once the backfill is in;
- `oneday_10y show`: "the one-day trigger did not fire" on a quiet day;
- D15's box edition: INSUFFICIENT, n 67, moved on by the days since.

The basket's 17:25 run takes the three daily steps from the next pull of main after the merge. The Monthly's dry run stays the operator's.

## Needs you (at most five)

1. **The hypotheses' registration:** yes or no to running `alpha.manifest register` for the batch on the box after the merge.
2. **GDELT's backfill reach:** 365 days (about 2.6 GB downloaded, nothing kept but the rows), or the five years the percentile wants (about 13 GB)?
3. **The Hugging Face organisations:** accept the 12 Chinese labs and 3 peers, with Google, Microsoft and NVIDIA left out?
4. **GDELT's story phrases:** accept the eleven stories' phrase lists in `config/gdelt.yaml` as session-set?
5. **D15's rule horizon:** accept 5 sessions as the registered outcome (20 printed beside)? The registration is committed, so a change would be a new dated registration.
