# ST-R4 Tranche 1, part 2: two top-side tells, a base rate and a co-signal (session notes, 16 Oct 2026)

**This branch, `st-r4-tranche-1b`, is cut from the tip of `st-r4-tranche-1`
(`5fa4a21`, after its CI fix; see step 0). So it carries the stitched chain, the
ES block (`st-r6-es-block`) and part 1. Merge order: the chain, then
`st-r6-es-block`, then `st-r4-tranche-1`, then this branch.** Branch only:
pushed, not merged, not deployed, nothing run on the box.

Source: the Batch 5 change order (`docs/change-order-signal-triage-batch-5-2026-10-09.md`,
on main), items 18, 19, 22 and 27; §5 cross-item rulings 3 (the foreign-hours /
Japan cluster: no standalone flag) and 5 (the bull-side asymmetry, a standing
finding, not a design change here); §9 verify item 3, and verify item 10's parts
for items 18 and 22. Item 27 joins SR-32 (Japan slow money) and SR-36 (the
basis-trade proxy) in `docs/signal-triage-register.md`. Tranche 1 only: 19b (the
calibration ledger) and 19c (the T&B queue entry) come later; 18b is Claude's
chat-side Wednesday task.

## Step 0: the CI reads

| Branch | Run | Commit | Verdict | Cause | Done |
|---|---|---|---|---|---|
| `st-r6-es-block` | 38904259575 | `4dd24ac` | **passed**, 93 of 93 jobs | — | recorded in `docs/briefs/st-r6-45-notes.md` (commit `2e83766`, whose own run 38939309455 also passed, 93 of 93) |
| `st-r4-tranche-1` | 38904629572 | `1ee6e76` | **failed**: 92 jobs passed; `validate_weekly_edits.py` (89 of 90) and the summary failed | this branch's own: "no unlabelled id reaches the rendered edition". `calc.corr_spy_tlt_60d` and `calc.net_liquidity` reached the Weekly through the absence reasons of `batch5.stock_bond` and `batch5.net_liquidity` | fixed in `5fa4a21`: every reason names its series in plain words, and `validate_st_r4_t1.py` gained group I (49 checks) |
| `st-r4-tranche-1` | 38939260522 | `5fa4a21` | **passed**, 94 of 94 jobs | — | recorded in `docs/briefs/st-r4-tranche-1-notes.md` |

This branch starts from `5fa4a21`, the fixed tip. One more thing from part 1 is
fixed here, not there: an absence reason that put a date before a colon
("not knowable at 2026-10-09: ...") slipped past `prose_dates`, whose pattern
skips an ISO date followed by a colon. Part 1's fiscal-bark and deflator reasons
had that shape. CI never tripped on them, because the gate fixtures store ACM and
PPIDCS. Both reasons now put the date last; it is in `altdata/batch5.py` on this
branch.

## What it builds on

- The chain's MOVE and VIX closes (`yfinance.mkt_move`, `yfinance.mkt_vix`) and
  the move screen (`altdata/move_screen.py`). The Top & Bottom overlay is not
  built, so item 19's conditioner is a code path with no input yet.
- Batch 3's Japan slow-money family: only the early line (ST-B3-16, the 30-year
  JGB line in Plumbing) is built; the family is Tranche B. SR-36's basis proxy
  and its unwind watch (`altdata/basis_proxy.py`), whose co-signals item 27
  joins.
- The yfinance basket (the operator-sanctioned exception to the robots rule) and
  its daily OHLC set; the FRED writer; `tools/manual_input.py`.
- Part 1's print pattern: tables and code-written lines, no paragraph of their
  own, every absence by plain name, no ISO date outside a table.

## The items, their sources and their fixtures

**New files:** `altdata/batch5b.py` (computes; `python -m altdata.batch5b show`),
`daily_cascade/batch5b_block.py` (prints), `config/batch5_tranche_1b.yaml` (every
threshold, with its reason), `config/nber_expansions.yaml` (the NBER fixture),
`tools/validate_st_r4_t1b.py` (50 checks).

### ST-R4.18a, the dispersion panel (Mechanics)

- **Source check, 16 Oct 2026, from the laptop:**
  - `^DSPX`: Yahoo serves daily history from 22 May 2024 (603 sessions, no gap
    over five days).
  - `^COR1M` and `^COR3M`: Yahoo serves **today's quote only**; `period="max"` is
    refused ("must be one of: 1d, 5d"), and a dated start still returns one row.
    So their history is whatever the daily pull accumulates from its first run,
    and the panel prints the real n. Nothing is guessed. *(Superseded in Part 0:
    Cboe's history files are now read, from 2006, by a new unheld writer.)*
  - All three joined the basket (110 symbols). DSPX is registered as
    `vol_index` (vol points); COR1M and COR3M as `index_points`.
- **The panel:** each index with its 1- and 5-year percentiles, each printing its
  n and first date. The 5-year window says how many years it actually holds.
- **The flag**, "dispersion regime: high or low", is session-set:
  - high: DSPX at or above the 80th percentile of its longest window;
  - low: at or below the 20th;
  - withheld below 250 sessions.
- **The tactical line** (session-set): high DSPX with COR3M at or below its 20th
  percentile prints "the setting in which single names and long-short carry the
  edge over index expression".
- **The free fallback:** realized cross-sectional dispersion, the 21-session mean
  of the daily cross-sectional standard deviation of constituent log returns.
  - It reads `sp500.member_close`, the series session A named on 16 Oct
    (message to this session; `altdata/sources/sp500_members.py` on
    `st-r5-t1-rest`): one registry key, instrument = the member's ticker in
    Yahoo's form, the daily close in USD, split-adjusted and dividend-unadjusted.
  - That writer is held for D1c, so until it stores rows the panel prints
    **"awaiting constituent prices"**. No edit is needed at merge.
- **ST-R4.18b, not built:** two by-hand keys, `manual.flashalpha_implied_corr`
  and `manual.flashalpha_realized_corr` (fractions, 0..1). They enter through
  `tools/manual_input.py`, and the panel prints them as a row when entered.
  FlashAlpha's dispersion endpoint returns both for an index and a basket.
- **Fixtures (group A):**
  - the flag fires high at the 80.0th percentile and not at the 79.67th, and low
    at the 20.0th and not at the 20.33rd;
  - withheld at 200 sessions;
  - the single-name line prints;
  - a missing COR index is a listed gap;
  - "awaiting constituent prices" prints while the fallback is unnamed;
  - named, the fallback gives 3.4637% a day for 120 names with returns
    (i − 59.5) × 0.1%, worked by hand as 0.1 × √((120² − 1)/12);
  - the FlashAlpha row prints when entered.
- **Verify item 10 (18):** XIII held no implied correlation before this branch;
  no COR series was stored.

### ST-R4.19a, the cross-asset vol divergence flag (Mechanics)

- **The order's rules:**
  - z of the MOVE and of the VIX over a one-year rolling window (252 sessions),
    with percentile ranks beside z (the VIX is right-skewed);
  - **watch** when the MOVE's z > +0.5 and the VIX's z < +0.4;
  - **strong** when the MOVE's z > +1.0 and the VIX's z < +0.4;
  - strict inequalities, as written.
- **The conditioner:** the flag is discounted when the T&B bottom signal fired
  within the prior 12 months.
  - T&B is not built, so `tb_bottom.key` is null and the block prints "T&B not
    built; conditioner inactive".
  - The path reads any series named there (a row of 1 on a day it fired), so
    when T&B stores its bottom signal, it is one config line.
- **The read:** when a tier is live, Mechanics' read carries the flag line
  (item `mech:vol_divergence`, priority 1), in the Weekly and the Monthly.
  Otherwise it carries nothing.
- **Session-set:** the window must be at least 227 sessions full (90%).
- **Fixtures (group B):**
  - watch at MOVE z +0.51 and not at +0.50;
  - strong at +1.01; +1.00 is watch, not strong;
  - no tier with the VIX's z at +0.40;
  - with T&B pretended to have fired six months ago, the flag is discounted and
    says so; thirteen months ago, active and not discounted;
  - the read's line appears only when a tier is live.
- **Verify item 3 (Dashiell's window):** **the window is as ruled, one year.**
  Her original post was not re-read in this session; the ruling's one-year
  window is used as given.

### ST-R4.22a, the expansion's age (slow layers)

- **The fixture:** `config/nber_expansions.yaml`.
  - Source: NBER's "US Business Cycle Expansions and Contractions" page, read 16
    Oct 2026. Its latest date is the April 2020 trough; no peak is announced.
  - "Post-war" starts at the October 1945 trough, so the 80-month expansion that
    peaked in February 1945 is the war economy's and is left out.
  - Twelve completed expansions, 770 months in all: mean 64.2, median 51.5,
    longest 128.
- **The line:** the age is in months from the trough month to the edition's
  month: **78 at October 2026**, matching the post's figure. The hazard counts the
  completed expansions that lasted that long, and how many of them peaked within
  the next 12 months (age ≤ months < age + 12).
  - At 78 the answer is **0 of 4**: 92, 106, 120 and 128 all ran past 90.
  - Against the four expansions since 1982 (mean 103 months), this age is
    ordinary; the order makes that point, and the line says so.
  - The line ends "a base rate, not a timing tool".
- **The hazard table** is hand-computed and committed in the fixture at twelve
  ages, and the gate holds the code to it (group C).
- **Verify item 10 (22):** Factor IV has **no measured fiscal impulse**; the
  phrase appears only in a Quarterly chapter's prose (`config/quarterly_chapters.yaml`).

### ST-R4.22b, Factor I's dependency line (slow layers, under Factor I)

- **FRED serves both legs**, so this extends the FRED writer and builds no new
  reader:
  - `Y034RY2Q224SBEA` (information-processing equipment);
  - `B985RY2Q224SBEA` (software).
  - Both are "Percentage Points at Annual Rate, Seasonally Adjusted Annual
    Rate", quarterly, read off each FRED page on 16 Oct 2026. Latest, Q2 2026:
    0.19 and 0.33.
- **No BEA writer:** FRED serves both, so 22b needs no writer of its own. (Part 0
  adds one writer to this branch, the Cboe history reader, for item 18.)
- **Units:** `percent_return` through the block's `member_units`, so a change
  prints in pp.
- **The combined series** (`A679RY2Q224SBEA`) ended in Q1 2013, so the line sums
  the two.
- **The table:** four quarters of equipment, software and their sum, against
  real GDP's annualized growth (from GDPC1, already stored), with the sum's share
  of growth. The share is left blank where growth is under 0.5% either way.
- It is a broad proxy for AI investment (all computers, all software), and the
  table's note says so.
- **Fixtures (group D):** Q2 2026 = 0.19 + 0.33 = +0.52 pp of 4.06% annualized
  growth (+1% quarter on quarter), 13% of it; flat growth leaves the share blank.

### ST-R4.27a, overnight vs session (Positioning & flows)

- **The split:** TLT and ZN=F joined the daily OHLC set, and ZN=F joined the
  basket. Each session splits into three log changes:
  - overnight: ln(open / prior close);
  - session: ln(close / open);
  - the day: ln(close / prior close), which the two legs sum to exactly.
  - Each leg is cumulated over 20 sessions.
- **ZN=F caveat, measured 16 Oct on two years of Yahoo daily bars:**
  - ZN=F's daily bar opens at the 18:00 ET reopen. Its "overnight" leg is only
    the gap to the reopen (standard deviation 0.12% a day against 0.30% for the
    session leg), so Asian hours fall in its session leg.
  - TLT opens at 09:30 ET, so its overnight leg holds Asia and Europe (0.59%
    against 0.50%).
  - So **TLT carries the co-signal**, and ZN=F prints beside it with a note.
- **A co-signal, no standalone flag (cross-item ruling 3).**
  - In SR-36's unwind watch it is the **fifth co-signal**, hooked by name like
    SR-35 (`config/basis_proxy.yaml` `unwind_watch.overnight`).
  - It is on when TLT's 20-session overnight leg is at −2 sigma against five
    years of 20-session overnight legs (falling prices, rising yields) — the
    watch's own 2-sigma rule.
  - It counts toward the watch's two-co-signal minimum (needs-you 3).
  - The watch's rule is otherwise unchanged; the ledger table (ST-B3-14) keeps
    its four co-signal columns.
- **In the Japan slow-money set,** which has no table yet (the family is Tranche
  B), it prints in Positioning under the CFTC table and SR-36's line, naming both
  sets.
- **Deferred:** the Asia-hours split needs intraday data; the block says so.
- **Fixtures (group E):**
  - the legs sum to the day on 59 of 59 sessions;
  - the 20-session sums, with the overnight leg carrying a rising-yield move;
  - the co-signal on at −2 sigma and off when quiet;
  - SR-36 carries it as its fifth;
  - with a level flag, the overnight leg alone does not turn the watch on, and
    with the MOVE it does.

### The display and the registry (group F)

- **Mechanics:** items 18 and 19, in the Weekly and the Monthly.
- **The slow layers:** item 22, with 22b under Factor I. The Monthly only; the
  Weekly has no slow layers.
- **Positioning & flows:** item 27, at both cadences, through the Weekly's
  builder, which the Monthly reuses.
- **Registered:** the four new basket symbols with their units; TLT's and ZN=F's
  OHLC (`market_ohlc`, 11); ZN=F's volume as contracts (`market_volume_contracts`,
  6); the two FRED series (`fred_signal_triage`, 30); the two manual keys.
- **Elsewhere:** a catalogue line for `altdata.batch5b`. `NEW_BLOCK_MEMBERS` in
  `validate_audit_3a.py` names every new block key.
- CLAUDE.md:
  - FRED_SIGNAL_SERIES 30, FRED_PULL_SERIES 132, 110 market symbols;
  - eighty-seven code gates (eighty-four Python);
  - one new paragraph.
- **Group F's checks:** on an empty store all five sub-sections print, with no
  internal id and no ISO date outside a table.

## The session-set thresholds, for Ari

All are in `config/batch5_tranche_1b.yaml`, each with its reason.

| Item | Setting | Value | Why |
|---|---|---|---|
| 18 | dual percentile windows | 1 and 5 years | DSPX's history is 2.4 years; the long window prints its real span |
| 18 | dispersion regime high / low | ≥ 80th / ≤ 20th percentile of the longest window | quintile edges: the order asks for a regime, not a tail |
| 18 | flag minimum | 250 sessions | one trading year |
| 18 | single-name line | DSPX high and COR3M ≤ 20th | the same quintile edge |
| 18 | realized fallback | 21 sessions, at least 100 names a day | one trading month; a thin day is skipped |
| 19 | minimum window fill | 227 of 252 sessions | 90% of the ruled year |
| 27 | co-signal | TLT's 20-session overnight leg at −2 sigma on five years, falling side only | the unwind watch's own rule for its other co-signals |
| 27 | counts in the watch | yes | the order puts it "in SR-36's unwind-watch co-signals" |

The order's own: 19's tiers (+0.5, +1.0, +0.4), its one-year window and its
12-month conditioner; 22's 12-month hazard horizon; 27's 20 sessions.

## The by-hand drafts, for Ari

1. **XXVII dated appendix, base-rate note (item 18):**
   > *Dated 9 Oct 2026.* arvy (Thierry, Macro Cycles; a product pitch) charts 200
   > years of long-bond yields as 56-, 59- and 67-year secular legs, with 2020 as
   > the turn and an oscillator run out to 2060. The leg lengths are fitted to the
   > chart, and the 2060 line is a forecast; we keep it here as a dated picture of
   > the long cycle, not a measure. The testable claim, that dispersion is back,
   > is measured in Mechanics' dispersion panel (Cboe DSPX and COR1M/COR3M).
2. **Narrative register (item 18), "end of the bond bull / active era":**
   > Claim: the 40-year bond bull compressed dispersion and rewarded passive; its
   > end returns the edge to stock-picking. Source arvy / Thierry (product
   > pitch), 9 Oct 2026. Measure: the dispersion regime flag (DSPX percentile)
   > beside implied correlation. Intensity: low; one source.
3. **Narrative register (item 27), "Treasury manipulation / Asian selling":**
   > Claim: the US 30-year rises in Asian hours and falls in US hours, framed as
   > manipulation or Asian selling against US buying. Source Monchau (Syz;
   > credible) relaying Bull Theory (aggregator), two sessions, 30-year ~5.65%.
   > Measure: TLT's overnight leg against its session leg over 20 sessions
   > (Positioning & flows), a co-signal in the Japan slow-money set and SR-36's
   > unwind watch. Two days is noise; "manipulation" is the narrative's word,
   > never the report's. Intensity: low.

Ari also enters the FlashAlpha figures each Wednesday (18b), from Claude's
chat-side vendor pull:
`python tools/manual_input.py manual.flashalpha_implied_corr 0.42 2026-10-21 "FlashAlpha SPX vs <basket>, <weights>, 20d"`
(0.42 is a placeholder), and the same for `manual.flashalpha_realized_corr`.

## Box commands, for Ari (inside a window; nothing here was run on the box)

No unit file changed, so there is nothing to deploy or restart. The new symbols
and the two FRED series arrive at the next scheduled pulls after the merge, but
the history has to be backfilled once. These steps fetch, so they are yours:

1. Price history for the new symbols, and TLT's open, high and low. Dry run
   first:
   `ssh vps 'cd ~/chester-reports && .venv/bin/python tools/backfill_prices.py --years 5 --symbols ^DSPX,^COR1M,^COR3M,ZN=F,TLT --dry-run | tail -30'`
   then the same without `--dry-run`. COR1M and COR3M will return one row each
   (Yahoo serves no history). Read the dry run's TLT lines before writing:
   TLT's closes are already stored, and the backfill should only add the OHLC
   companions beside them.
2. The two BEA series, at their first publication (ALFRED), dry run first:
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.fred_history backfill --series contrib_info_equipment,contrib_software --dry-run | tail -20'`
3. What the blocks would print today (reads only):
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.batch5b show | head -150'`
4. Part 0: the first Cboe history pull (writes COR1M and COR3M from 2006, DSPX
   from 2014; it then runs inside the scheduled external pull):
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.sources.cboe_indices | tail -30'`
5. Part 0: the first Census pull, now unheld (it also runs inside the scheduled
   external pull from the merge on):
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.sources.census_vip | tail -30'`
6. Part 0: seed the three committed narrative proposals into the register (they
   enter as proposed; the close pass's seed does the same at its next run):
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.narratives seed'`
   then confirm or reject each, which is yours alone:
   `python -m altdata.narratives confirm <id>` or `reject <id>`.

## Files shared with the open branches

| Branch | Shared files | At merge |
|---|---|---|
| `st-r5-rates` | CLAUDE.md, Makefile, `altdata/config.py`, `config/catalogue_commands.yaml`, `daily_cascade/weekly_stack.py`, `metrics_registry.yaml`, `monthly_macro/stack.py`, `tools/validate_audit_3a.py` | take both sides |
| `st-r5-index` | the same eight | take both sides |
| `6e-metric-lenses` | CLAUDE.md, Makefile, `metrics_registry.yaml` | take both sides |
| `st-r5-t1-rest` | pushed after this branch's first commit; the fallback reads its `sp500.member_close` by name and shares no file | merges after the chain, `st-r5-rates` and `st-r5-index` (session A) |
| `docs-batch-6` | none | — |

How to take both sides:

- **CLAUDE.md's counts:** `st-r5-index` prints 33 signal series, 135 pulled and
  eighty-six code gates. This branch prints 30, 132 and eighty-seven. The union is
  **36 FRED_SIGNAL_SERIES, 138 FRED_PULL_SERIES, eighty-eight code gates
  (eighty-five Python)** and 110 symbols. Session A changes no basket symbol.
- **`validate_audit_3a.py` `NEW_BLOCK_MEMBERS`:** the union of both sets.
- **The registry:** `fred_signal_triage`'s `expected_members` is the union's 36.
  Keep this branch's `member_units` there; A adds none to that block.

`altdata/basis_proxy.py`, `config/basis_proxy.yaml`, the yfinance basket,
`tools/validate_prices.py` and `tools/manual_input.py`'s registry entries are
touched by no other open branch.

## CI

Locally, only the gates this branch writes or changes were run, one at a time:
- `tools/validate_st_r4_t1b.py`: 50 passed, 0 failed (new);
- `tools/validate_st_r4_t1.py`: 49 passed, 0 failed (the colon fix);
- `tools/validate_basis_proxy.py`: 31 passed, 0 failed (the fifth co-signal);
- `tools/validate_prices.py`: 101 passed, 0 failed (110 symbols, 92 with volume);
- `tools/validate_audit_3a.py`: 83 passed, 0 failed (counts and new block keys);
- `tools/check_registry.py`: OK; `tools/check_library.py`: 0 failures, 0 warnings.

Every other gate is left to CI, the Weekly and Monthly render gates above all,
since this branch adds sub-sections to both.

Runs 38941754491 (`6f61c5c`) and 38944014826 (`053889b`) failed on two gates, both
this branch's doing:
- `validate_numeral_audit`, 171 of 172: the dispersion block wrote the threshold
  ordinals ("80th", "20th") by hand in f-strings, and `_ord` carried its own
  suffix rule. Both now go through `numeral_audit.ordinal()`, the one helper
  (rounded half up, where `_ord` used Python's round-half-even).
- `validate_weekly_edits`, 89 of 90: the gate pins the Positioning sub-section
  titles, and 27a adds one under the CFTC table. The pinned list now carries
  "Treasury moves by session: overnight against the US session" in that place
  (eight sub-sections, not seven). Locally after the fix it is 90 of 90, and
  `validate_st_r4_t1b` is 50 of 50.
The run on the fix commit is read once, after the push; see the session report.

## Part 0 (second paste, 16 Oct 2026): today's rulings applied

### The CI read

Run 38970818174, on `bd5cd2a`: **failed, 111 jobs passed and 13 failed**: three
gates, each this branch's doing, plus the summary job and the exit lines. The two
gates fixed on `bd5cd2a`, `validate_numeral_audit` and `validate_weekly_edits`,
passed.
- `validate_security_master`, 81 of 82: the four new Yahoo symbols (^DSPX,
  ^COR1M, ^COR3M, ZN=F) were in no Security Master entry. Added as SM00200 to
  SM00203 (renumbered at the chain-2 stitch, 19 Oct; first given SM00195 to SM00198,
  which the chain's ^VIX9D, ^VIX6M and TIP/MUB already held) (index, index, index, future, every unknown fact null and listed as
  unverified, the form of their neighbours), and `next_id` moved from 195 to 199.
  Session A's branches end at SM00194, so the ids do not collide today; a
  branch that adds an entry before this merges takes 199.
- `validate_alpha`, 256 of 257: the gate's broken rule used TLT as the
  closes-only instrument for "next_open needs a stored open", and 27a gives TLT
  stored opens. The fixture now uses IEF, which has none.
- `validate_monthly_stack`, 265 of 266: the Monthly's Positioning pins its five
  read blocks (T3.1 item 10), and the 27a sub-section reached it through the
  Weekly's builder. 27a is now the Weekly's only, like the 10A blocks.
Locally after the fix: `validate_security_master` 82 of 82, `validate_alpha` 257
of 257.

Run 38974666074, on `036c393` (Part 0): **failed, 101 jobs passed and 7 failed**:
one gate, `validate_official_sources`, plus the summary job and the exit lines.
Its guard "no report, renderer or regime module imports a writer" caught
`daily_cascade/batch5_block.py`, which still imported `census_vip` to read the
hold; with the writer on the roster the import is a renderer reaching a writer.
The hold check is gone from the block (the hold is lifted, so there is nothing to
read), and no renderer imports either writer. `validate_st_r4_t1` 49 of 49
locally.

Run 38977257824, on `96342c1` (the fix): **passed, 95 jobs, 0 failed** (read once,
16 Oct). The branch is green.

### The Census hold lifted (ruling (a))

`altdata/sources/census_vip.py`: `HELD_FOR_D1C = False`, the docstring quoting
the ruling; its `KEYS` made a literal list, so `feeds.static_keys()` reads it
from source (the roster's own guard against an import failure). On
`altdata/feeds.py` `EXTERNAL_WRITERS`, so `pull_external()` runs it.
`source_registry.yaml` held → live; the four registry descriptions, the
catalogue line and CLAUDE.md say live. The gate's group F now holds the unheld
form: not held, two workbooks fetched into a temporary store, on the external
roster. Group G's held line became the plain-name absence. `validate_st_r4_t1`
49 of 49.

### The COR1M and COR3M history (ruling (e))

`altdata/sources/cboe_indices.py`, a new writer and not held. It reads Cboe's
daily history files (`cdn.cboe.com/api/global/us_indices/daily_prices/<SYM>_History.csv`,
which redirects to `cdn-api.cboe.com`). COR1M's and COR3M's CLOSE run from 3 Jan
2006; DSPX's one column runs from 19 Jun 2014, so it rides the same reader, a
decade more than Yahoo's 2024 start.
- **Robots:** both CDN hosts answer `robots.txt` with 403, which RFC 9309 reads
  as no rules (the reading `altdata/listings.py` takes). Both are checked on
  every pull through the wildcard-aware reader, and a refusal fetches no file.
  `www.cboe.com`'s robots.txt disallows `/book/` and the volume reports only.
- **Timing:** each row carries the file's Last-Modified (21:31 GMT on 16 Oct for
  that day's close).
- **Keys and wiring:** `cboe.cor1m`, `cboe.cor3m` (index_points) and `cboe.dspx`
  (vol_index) are registered, with a source_registry entry (live) and a
  catalogue line. The panel reads the Cboe key first and Yahoo's as the fallback,
  never spliced, and says when it is on the fallback. The Yahoo symbols stay in
  the basket.
- **Gate:** new group G in `validate_st_r4_t1b`, 61 of 61.

### Drafts committed, for Ari's accept-all

Ruling (c). Every one is committed as drafted, with its file and line:

| Draft | Where | Line |
|---|---|---|
| Narrative register, "end of the bond bull / active era" (18) | `config/narratives.yaml`, `proposals:` → `bond_bull_end_active_era`, pending confirm | 340 |
| Narrative register, "Treasury manipulation / Asian selling" (27) | `config/narratives.yaml` → `treasury_asian_hours_selling`, pending confirm | 366 |
| Narrative register, side B of "what's driving 5.3%" (26) | `config/narratives.yaml` → `capital_competition`, pending confirm | 395 |
| The pair "what's driving 5.3%" itself (26) | `docs/dated-appendix-queue.md`, for session A's `docs/narrative-register-pairs.md` at the stitch | 98 |
| XXVII dated-appendix base-rate note (18) | `docs/dated-appendix-queue.md` | 13 |
| Appendix line for item 24, after verify item 5 | `docs/dated-appendix-queue.md` | 22 |
| Book A rule-table edit (24), as A-6 | `docs/dated-appendix-queue.md`, for session A's Base Rates Appendix C at the stitch | 72 |
| XII disagreement note and the manufacturing base-rate note (23) | `docs/dated-appendix-queue.md` | 36 |
| Sovereign scorecard layout (21) | `docs/dated-appendix-queue.md`, marked not live under ruling (b) | 55 |

How each landed:
- **Narrative proposals.** The register confirms model proposals but seeded every
  config story as active, so committing a story there would have skipped your
  confirm. So `altdata/narratives.py`'s `seed()` gains a `proposals:` block,
  written once as `proposed` (origin `config_proposal`, emerging, never
  evaluated), and the Weekly prints each beside its confirm and reject commands.
  - A proposal without `proposed_by` is refused.
  - Once in the register, it is never re-synced.
  - The pair has no register kind, so its side B is the proposal, and side A is
    the seeded `fiscal_dominance`.
  - None of the three declares a story_query, so each starts with its
    series-move evidence alone.
  - Gate: `validate_narratives` group M, 103 of 103.
- **Verify item 5,** answered from FRED's DGS10, which corrected the item 24 line:
  - DGS10 first closed at or above 5.25% on 29 Sep 2026 (5.26).
  - In the week of 5 Oct: 5.31 on the 5th, 5.27 on the 6th and 5.28 on the 7th.
  - The last such close before that was 5.26 on 12 Jun 2007, not 2002 as the
    draft said. The committed line carries the verified dates, and says so.
- **The dated-appendix homes.** XXVII is reserved and not written, the order
  names no paper for item 24's line, and its "XII" for the power note is not the
  library's XII (the Daily Cascade paper). So these wait in one queue file, each
  marked with its intended home.
- **Session A's homes.** Session A told this session (16 Oct) where its ruling
  (c) drafts go on `st-r5-fixes`: Base Rates Appendix C for the Book A table
  (its A-4 and A-5, this branch from A-6), and `docs/narrative-register-pairs.md`
  for the pairs. This branch creates neither file, to avoid an add/add conflict;
  its two entries wait in the queue file for the stitch.

Not committed, and why: the capex-guidance revisions table and the scorecard's
data are recurring by-hand data lines, which need your explicit yes under ruling
(b). The reading-shelf addition goes through the shelf's own change-order
mechanism. The Wednesday FlashAlpha entries (18b) stay Claude's chat-side task.

## Needs you

1. **The session-set thresholds above**, the dispersion quintiles and the
   overnight co-signal's 2 sigma above all. (Ruling (e): they stand.)
2. **The realized-dispersion fallback** reads session A's `sp500.member_close`.
   It prints "awaiting constituent prices" until item 44's writer has rows.
3. **Accept-all on the drafts** listed under Part 0, and confirm or reject each
   of the three narrative proposals (box command 6).
4. **The two homes the orders leave open:** which paper takes item 24's dated
   line, and what the order's "XII" in item 23 names.
5. **Run box commands 1, 2, 4 and 5** after the merge, inside a window.
6. **A yes or no on the by-hand data lines** (capex-guidance revisions, the
   sovereign scorecard's figures), under ruling (b).
