# chain-6 box sheet: the four post-Monthly branches, in the order they run

*For the operator, after chain-6 merges to main, which is after the 1 Nov Monthly.
Inside the windows (weekdays 09:05-15:40 and 17:20-23:30 ET, never 16:00-17:20;
clear of Sunday 05:00). Dry runs first. Every ledger's box edition is written
OUTSIDE the checkout. No unit changes: every new step rides an existing run.
Gathered from the notes of a57-batch14-b1, b55-batch14-b2, b56-batch15-2 and
a58-batch15-1; each branch's own notes keep its reasons.*

```
cd ~/chester-reports
git log -1 --format='%h %s'      # the merged main, pulled by the next wrapper run
```

## 1. What arrives by itself (nothing to run)

- **FRED, six new series** (a57's four: three PPI lines and Z.1's equity market
  value; b55's `TTLHHM156N`; a58's `NIKKEI225`). The 16:10 FRED pull takes each one's
  full history at its next run. Then
  `.venv/bin/python -m tools.check_store_registry --db data/chester.db`.
  **Expect** the six keys stored, none "no rows". `fred.households` may show stale
  (its newest row runs months behind); see b55's needs-you 4.
- **The CFTC TFF pull** (b56) reads ES and NQ whole, from 13 Jun 2006, at its next
  scheduled run. To take it now: `.venv/bin/python -m altdata.sources.cftc`.
  **Expect** its summary line with rows written, ES and NQ among the instruments.
- **The voices scan** reads Carson Group's feed (a57) at its next 06:15 run.
- **The crypto basket's 17:25 run** gains two steps (b56): the protocol count daily
  and the cyber feeds on Saturdays.
- **The EOD pass** resolves a57's speed-attribution and a58's event ledgers.

## 2. Price history (a57)

```
.venv/bin/python tools/backfill_prices.py --symbols AIQ,SPXT --years 8 --dry-run
.venv/bin/python tools/backfill_prices.py --symbols AIQ,SPXT --years 8
```
**Expect:** the dry run prints the rows it would write; then the same, writing.

## 3. NVD's history and the first cyber and protocol reads (b56)

```
.venv/bin/python -m altdata.cyber_pressure backfill --dry-run
.venv/bin/python -m altdata.cyber_pressure backfill
.venv/bin/python -m altdata.cyber_pressure weekly --force --dry-run
.venv/bin/python -m altdata.protocol_breadth daily --dry-run
```
**Expect:**
- the backfill's dry run: about 35 requests, about 560 weeks from 2016, its last six
  weeks previewed; it takes about four minutes at the public rate (6.5 s between
  requests); then the same, writing;
- `weekly --dry-run`: about 267 rows, `failed` empty (the laptop read 23 Oct: KEV 9
  in the week of 12 Oct, NVD 17, provisional);
- `daily --dry-run`: counts near 8,800 total, 7,900 listed, 5,500 active.

## 4. The 13F data sets (a58; needs `CHESTER_SEC_CONTACT`, already the EDGAR writer's)

```
.venv/bin/python -m altdata.gold_13f fetch --files 9 --dry-run
.venv/bin/python -m altdata.gold_13f fetch --files 9
.venv/bin/python -m altdata.gold_13f load ~/chester-data/inbox/sec13f/*.zip --dry-run
.venv/bin/python -m altdata.gold_13f load ~/chester-data/inbox/sec13f/*.zip
```
**Expect:**
- `fetch --dry-run` lists the nine newest zips, or refuses without the contact;
- `load --dry-run` prints each quarter's filers, marking the partial ones.

## 5. The reads (read-only)

```
.venv/bin/python -m altdata.ai_trade show
.venv/bin/python -m altdata.fragility show
.venv/bin/python -m altdata.speed_attribution show
.venv/bin/python -m altdata.speed_attribution resolve --dry-run
.venv/bin/python -m altdata.cma_table show
.venv/bin/python -m altdata.st_r5_rates show
.venv/bin/python -m altdata.hf_positioning show
.venv/bin/python -m altdata.cyber_pressure show
.venv/bin/python -m altdata.protocol_breadth show
.venv/bin/python -m altdata.ai_lab_ledger
.venv/bin/python -m altdata.gold_13f show
```
**Expect:**
- **a57's reads:**
  - `ai_trade show`: the PPI line, the proxy line (or its reason), the AI-credit gap;
  - `fragility show`: the panel's rows and the flag's line;
  - `speed_attribution show`: "the speed flag did not fire" on a quiet day.
- **b55's reads:**
  - `cma_table show`: six houses "no edition stored" until the publication watch
    writes a CMA scan;
  - `st_r5_rates show`: the housing block with the per-household line (once
    `fred.households` is in).
- **b56's reads:**
  - `hf_positioning show`: ES and NQ with their percentiles, and the squeeze flag's
    line;
  - `cyber_pressure show`: the two counts and the flag;
  - `protocol_breadth show`: the count with "History from <first day>";
  - `ai_lab_ledger`: the unit-economics line, SR-16's line and the IPO watch, "not
    yet public".
- **a58's read:** `gold_13f show`: the holder counts by quarter.

## 6. The ledgers' box editions (outside the checkout)

```
mkdir -p ~/chester-data/ledgers
# a57 (public sources, the registered rules):
.venv/bin/python tools/calibration/st_r6_65a_speed_attribution.py --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/st_r6_71d_air_pockets.py --box --out ~/chester-data/ledgers
# b56 (stored history only; after step 1's CFTC pull):
.venv/bin/python tools/calibration/st_r6_74b_short_extremes.py --db data/chester.db --out ~/chester-data/ledgers
# a58 (the store only):
.venv/bin/python -m altdata.gold_event history --out ~/chester-data/ledgers/st-r6.73a-first-edition.md
.venv/bin/python -m altdata.dm_drawdown history --out ~/chester-data/ledgers/st-r6.73b-first-edition.md
```
**Expect:**
- a57's: INSUFFICIENT n 28 and FAIL n 2965, moved on by the days since;
- b56's: a verdict over about 1,060 ranked ES weeks, with n episodes (no longer the
  laptop's INSUFFICIENT n 0);
- a58's: every fired day listed, with a note where the history is short.

## 7. Store a58's first rows, once read

```
.venv/bin/python -m altdata.gold_event history --write
.venv/bin/python -m altdata.dm_drawdown history --write
.venv/bin/python -m altdata.gold_event show
.venv/bin/python -m altdata.dm_drawdown show
```

## 8. Bring the box editions back

```
scp 'vps:~/chester-data/ledgers/st-r6.*' docs/ledgers/
```
Then ask a session to commit them. The Monthly's dry run stays the operator's, as
always.
