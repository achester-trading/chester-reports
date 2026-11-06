# chain-7 box sheet: chain-6's sheet in full, then every later branch's box commands, in run order

*For the operator, after chain-7 merges to main. That is after the 1 Nov Monthly, and
after a61b-feed-repair has merged by itself (Tue 27 Oct, with its own box sheet) and
chain-7 has taken main. Inside the windows (weekdays 09:05-15:40 and 17:20-23:30 ET,
never 16:00-17:20; clear of Sunday 05:00). Dry runs first. Every ledger's box edition
is written OUTSIDE the checkout. No unit changes: every new step rides an existing
run.*

*Part I is chain-6's sheet, unchanged. Part II gathers the later branches' commands
from the notes of a61-rulings-1024, a62-6f-build, a63-6f-calibration,
b59-trigger-sources and b60-reading-budgets; each branch's own notes keep its
reasons. A command that offers no dry run says so.*

# Part I: chain-6's sheet (a57, b55, b56, a58), in full

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

# Part II: the later branches, in the order they run

## 9. What arrives by itself with the merge (nothing to run)

- **The reading targets (b60).** The close's 10 minutes, the Weekly's 35 and the
  addendum's 7 take effect at each one's next run. Nothing is cut or withheld for
  length; an edition over its target prints one foot line. **Expect:** on a long
  day, "This edition runs about N minutes against a 10-minute target." in the
  close's footer.
- **The 6f object v2 (a62).** The 16:45 close computes the market-state object under
  `market-state-method-11` from the next close after the merge. The CP-bill series
  rides the 16:10 pass (two FRED legs already pulled; a62's needs-you 5).
- **The calibration rows (a63).** The close writes calibrated dial rows and resolves
  the due ones each evening; none until a row has 30 independent starts.
- **The one-day 10-year trigger (b59).** The EOD pass runs `oneday_10y resolve`; the
  close prints its line on a trigger day only.
- **b59's daily pulls.** The crypto basket's 17:25 run takes the GDELT, NOAA degree
  days and Hugging Face daily steps from its next pull of main.
- **FXEmpire (a61)** joins the voices scan's 06:15 run, at tier 3.

## 10. QAI and the ProShares funds (a61)

```
.venv/bin/python tools/backfill_prices.py --symbols QAI --years 8 --dry-run
.venv/bin/python tools/backfill_prices.py --symbols QAI --years 8
# The five ProShares funds read each file from inception at the next EOD pass's
# ProShares pull; to take it at once (no dry run offered):
.venv/bin/python -m altdata.sources.proshares
```
**Expect:** the dry run prints the QAI rows it would write (about eight years); then
the same, writing. The ProShares pull prints its JSON summary: the five funds
(SM00216-SM00220) read, with the rows written.

## 11. The 6f object v2: tranche 0's checks, then the re-backfill under method-11 (a62)

```
# Read-only:
.venv/bin/python -m regime range                 # the supportable window: how far as-of history reaches
.venv/bin/python -m regime method                # method-11, pinned 1664e465a940aadc
.venv/bin/python - <<'EOF'                       # how many as-of-correct objects per dial state
import collections, json, sqlite3, os
db = os.path.expanduser("~/chester-data/chester.db")
c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
n = collections.Counter()
for (v,) in c.execute("SELECT value_text FROM observations WHERE registry_key='market_state'"):
    o = json.loads(v); d = o.get("dials") or {}
    for k in ("macro", "vol", "gamma"):
        n[(k, (d.get(k) or {}).get("state"), o.get("method_version"))] += 1
for k, v in sorted(n.items(), key=str): print(k, v)
EOF
# The v2 object, computed and printed, NOT stored (this step is the dry run):
.venv/bin/python -c "import regime; o=regime.compute(); print({n: d.get('state') for n, d in o['dimensions'].items()}); print(o['horizons']); print([(f['family'], f['state']) for f in o['tail_families']])"
# Then the re-backfill (writes market_state vintages; `regime backfill` offers no dry run):
.venv/bin/python -m regime backfill --no-resume
```
**Expect:**
- `regime method`: `market-state-method-11` and the pinned hash `1664e465a940aadc`;
- the count: every stored object under an older method, none under method-11;
- the printed object: the new dimensions with their states or their reasons for
  being absent, the horizons, and the tail families;
- the re-backfill: one object per session over the supportable window, at
  method-11. Run it in an evening window, because it computes one session at a time.
  Afterwards the replay gate should pass on the box before the next close.

## 12. The first calibration read (a63; read-only, after step 11)

```
.venv/bin/python -m altdata.state_calibration show
.venv/bin/python -m altdata.state_calibration show --as-of 2026-10-30T21:30:00+00:00
```
**Expect:** k for each dial and horizon over the method-11 objects. Most rows, and
certainly the 63-session rows, read "awaiting" (fewer than 30 independent starts).
Before step 11's re-backfill it reads nothing.

## 13. b59: the hypotheses, then the three new sources

```
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
```
**Expect:**
- `alpha.manifest register`: three hypotheses (H-B59-1 to H-B59-3), registered at the
  manifest's instant;
- `gdelt daily --dry-run`: three days of about 117,000 events each, across five
  families;
- `cpc_degree_days daily --dry-run`: about 260 rows;
- `hf_releases daily --dry-run`: 15 organisations, `failed` empty;
- `cpc_degree_days show`: a normal and a departure once the backfill is in;
- `oneday_10y show`: "the one-day trigger did not fire" on a quiet day.

## 14. The ledgers' box editions since chain-6 (outside the checkout)

```
mkdir -p ~/chester-data/ledgers
# b59 (D15, the one-day 10-year trigger; public sources, the registered rule):
.venv/bin/python tools/calibration/d15_oneday_10y.py --box --out ~/chester-data/ledgers
```
**Expect:** INSUFFICIENT, n 67 (as in the laptop's first edition), plus whatever the
days since have added. a62 and a63 have no edition to write by hand: a63's
calibration ledger is written by the close, row by row, once a row is calibrated.

## 15. Bring the box editions back

```
scp 'vps:~/chester-data/ledgers/d15-*' docs/ledgers/
```
Then ask a session to commit them, together with step 8's. The Monthly's dry run
stays the operator's, as always.
