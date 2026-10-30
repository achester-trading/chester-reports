# A93 notes: the IBKR daily-bars writer, built and switched off

**Branch.** `a93-ibkr-daily-bars`, from origin/main at `422ea697`. It is tranche
1 of the price-source migration:

- the brief is `docs/briefs/price-source-migration-brief-2026-10-25.md`, on
  `b68-price-source-migration`, read whole;
- D38 ruled its ten decisions as recommended on 26 Oct 2026.

**Merge timing.** It merges after chain-8, and stays off until the IBKR
market-data subscription exists. No request went to IBKR from the laptop, and
nothing is turned on.

## What is built

### The writer, `altdata/sources/ibkr_bars.py`

**What it pulls.** Historical daily bars through the shared read-only client
(`ibkr_portfolio.connect`: readonly, paper port, live port refused), on its own
client id: `bars` = 27 in `altdata/ibkr_clients.py`.

**Its commands.** `plan` lists what it would request, without connecting. `pull`
is the routine pull; `backfill` reaches back five years.

**The rules it holds:**

- **Contracts through the Security Master.** An instrument resolves by its Yahoo
  symbol to its entry's `ibkr_conid`. Missing, unknown, ambiguous or restricted
  means it is skipped and named, never guessed. Today the master carries no
  `ibkr_conid` for any instrument (`plan` names all five), so the operator's
  first step is adding them.
- **Pacing in code.** `Pacer` allows at most 60 requests in any ten minutes, and
  the writer makes one request per contract per run.
- **New keys.** `ibkr.<stem>_{open,high,low,close}`, the stem being the yfinance
  key's (`ibkr.spy_close` beside `yfinance.mkt_spy`), never over yfinance's.
- **The point-in-time rule.** A daily bar is knowable at its close plus
  `delay_minutes` (30, declared and to be checked on the parallel run):
  - a live row is stamped no earlier than that, and no earlier than its pull,
    `observed`;
  - a backfill row is close + delay, `reconstructed`, as
    `tools/backfill_prices.py` does;
  - the New York close follows EDT and EST; an FX bar closes at the end of the
    UTC day.
- **STALE, never empty.** No gateway is STALE with the connect error. Every
  request refused for want of an entitlement is STALE "market data subscription
  not present". A partial refusal writes the rest and names the refused
  instrument.
- **Volume is not written yet.** The brief: IBKR may report US equity volume in
  round lots, "checked ... never assumed". It is checked on the box's first dry
  run, then added.

### Switched off

- `config/ibkr_bars.yaml` ships `enabled: false`, `disabled_since: 2026-10-29`.
- Disabled, `pull()` connects to nothing and writes nothing.
- The feed run's external step calls a writer in `feeds.SWITCHED_WRITERS` only
  while its config enables it. Off, its keys are not on the freshness roster, so
  nothing reads as stale for a source not yet bought.
- `source_registry.yaml` carries `ibkr_bars`, `status: disabled`,
  `disabled_since: "2026-10-29"`.
- `metrics_registry.yaml`'s block `ibkr_daily_bars` (40 declared keys) is
  `status_extra: not_yet_sourced`, the registry's own word for a key with no
  writer yet. It has no "pending", and `not_yet_sourced` is quiet in the store
  check.

### The first family

The US equity index funds (the brief's first row):

| Instrument | Keys |
|---|---|
| SPY | `ibkr.spy_open`, `_high`, `_low`, `_close` |
| QQQ | `ibkr.qqq_*` (same four fields) |
| IWM | `ibkr.iwm_*` |
| DIA | `ibkr.dia_*` |
| RSP | `ibkr.rsp_*` |

That is 20 keys. Declared but not included until the next tranche:

- ^GSPC, through the held Cboe indexes subscription;
- ES=F and NQ=F, the overnight block's futures;
- JPY=X and EURUSD=X, through IDEALPRO, MIDPOINT, UTC day.

The single names the Weekly reads are the next family to add. The brief's
inventory lists 34, and the Weekly's set is to be chosen from them.

### The cross-source pairs

`config/data_quality.yaml` `inactive_pairs`: SPY, QQQ, IWM, DIA and RSP, each
IBKR close against the yfinance close it would replace.

- Each is `active: false`, with tolerance "to be measured on the overlap".
- The quality check does not read them. A pair joins `pairs.list` with its
  measured tolerance at the end of the twenty sessions.

### The gate

`tools/validate_ibkr_bars.py`, 28/0, on a fake client and a fake Security
Master:

- **contracts:** resolution through the master, and the real master's five
  named;
- **pacing:** the 61st request waits for the window;
- **point in time:** EDT, EST, FX and reconstructed rows;
- **STALE:** no subscription and no gateway, and a partial refusal;
- **switched off:** nothing written and no feed call;
- **keys:** none a yfinance key, and every close pairs by stem.

**Bookkeeping.** One Makefile line. The gate count goes from 135/132 to
136/133, by hand: main has no stitch tools. **A92 makes the same +1 on its own
branch, so whichever merges second makes it 137/134.**

**Other gates** (one at a time, foreground):

| Gate | Result |
|---|---|
| `validate_audit_3a` | 88/0 (its declared new-key blocks gain `ibkr_daily_bars`) |
| `validate_feeds_scheduled` | 19/0 |
| `validate_ibkr_portfolio` | 63/0 |
| `validate_official_sources` | 340/0 |
| `validate_quality` | 48/0 |
| `validate_outliers` | 37/0 |
| `check_registry` | OK |

## What is left of the brief's 46 hours

**About 39.** The writer's row was 10 hours; about 7 are built here. Its 3 left:

- the conids into the Security Master, the operator's;
- the volume unit, checked on the box;
- turning on and checking the four declared families.

The other 36 are untouched:

- the Cboe index files: 2;
- the FRED moves: 2;
- crypto through OKX: 3;
- the S&P members and actions through Massive: 4;
- intraday bars: 4;
- overnight: 3;
- the chains to Massive: 6;
- EDGAR: 4;
- the checks, the parallel-run line and the supersession: 5;
- the calibration scripts: 3.

## The operator's steps after subscribing

1. **Confirm the entitlement.** Check that the account holds what historical
   daily bars for US ETFs need: the bundle, or confirmation that the free
   non-consolidated feed serves them. That is the brief's open question 1.
2. **Add the conids.** Put each instrument's `ibkr_conid` into
   `config/security_master.yaml`, under `identifiers`, by a session paste
   reviewed as every master change is. Read them from the gateway (TWS's contract
   details), never from memory. Then, on the box:

   ```
   python -m altdata.sources.ibkr_bars plan
   ```

   It must list all five as "conid ...", none as SKIP.
3. **Turn it on in a session paste:**
   - `enabled: true` in `config/ibkr_bars.yaml`;
   - `status: live` and the date in `source_registry.yaml`;
   - remove `status_extra` from the block.
4. **The dry run on the box** (the operator's). Run

   ```
   python -m altdata.sources.ibkr_bars pull
   ```

   once inside the operating windows, after the close. Check that:
   - it says OK with 20 keys written;
   - each key's newest bar is the last session's;
   - each `available_at` is after 16:30 ET.

   Note the volume unit IBKR reports, for the next paste.
5. **The backfill**, once, with `backfill`: five years, reconstructed. Its rows
   are what the parallel run's tolerance is measured against.
6. **The first parallel run.** Twenty sessions, the feed run calling the writer
   every evening beside the yfinance pull. At the end:
   - a session paste runs `python -m altdata.quality measure` on the five pairs;
   - it moves them into `pairs.list` with their measured tolerances;
   - the Weekly prints the family's parallel-run line (the brief's section 4.4,
     part of the 5 hours of checks);
   - then the readers of the first family move to the new keys in one commit,
     the old keys marked superseded.
