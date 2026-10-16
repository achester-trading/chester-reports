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
`tools/validate_st_r4_t1b.py` (49 checks).

### ST-R4.18a, the dispersion panel (Mechanics)

- **Source check, 16 Oct 2026, from the laptop:**
  - `^DSPX`: Yahoo serves daily history from 22 May 2024 (603 sessions, no gap
    over five days).
  - `^COR1M` and `^COR3M`: Yahoo serves **today's quote only**; `period="max"` is
    refused ("must be one of: 1d, 5d"), and a dated start still returns one row.
    So their history is whatever the daily pull accumulates from its first run,
    and the panel prints the real n. Nothing is guessed. A Cboe history file
    would fill them sooner, but it would be a new writer, held for D1c (see
    needs-you).
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
  - Session A's Batch 6 item 44 writer is held for D1c, and its branch
    `st-r5-t1-rest` was not on the remote, so the series name is unknown here.
  - The config key `dispersion.realized.key` is null. Until it is set at merge,
    and until the writer runs, the panel prints **"awaiting constituent prices"**.
  - It reads one registry key with one instrument per constituent. If A's writer
    stores it differently, the reader needs adjusting: one function,
    `batch5b.realized_dispersion`.
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
- **No held reader:** since FRED serves both, there is no BEA writer for D1c to
  hold. The gate's "held reader" check therefore asserts that this branch adds no
  writer at all.
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

## Files shared with the open branches

| Branch | Shared files | At merge |
|---|---|---|
| `st-r5-rates` | CLAUDE.md, Makefile, `altdata/config.py`, `config/catalogue_commands.yaml`, `daily_cascade/weekly_stack.py`, `metrics_registry.yaml`, `monthly_macro/stack.py`, `tools/validate_audit_3a.py` | take both sides |
| `st-r5-index` | the same eight | take both sides |
| `6e-metric-lenses` | CLAUDE.md, Makefile, `metrics_registry.yaml` | take both sides |
| `st-r5-t1-rest` | not on the remote at 16 Oct; not compared | Item 44's writer is where `dispersion.realized.key` comes from |
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
- `tools/validate_st_r4_t1b.py`: 49 passed, 0 failed (new);
- `tools/validate_st_r4_t1.py`: 49 passed, 0 failed (the colon fix);
- `tools/validate_basis_proxy.py`: 31 passed, 0 failed (the fifth co-signal);
- `tools/validate_prices.py`: 101 passed, 0 failed (110 symbols, 92 with volume);
- `tools/validate_audit_3a.py`: 83 passed, 0 failed (counts and new block keys);
- `tools/check_registry.py`: OK; `tools/check_library.py`: 0 failures, 0 warnings.

Every other gate is left to CI, the Weekly and Monthly render gates above all,
since this branch adds sub-sections to both. This branch's run is read once,
after the push; see the session report.

## Needs you

1. **The session-set thresholds above**, the dispersion quintiles and the
   overnight co-signal's 2 sigma above all.
2. **The constituent series name** for the realized-dispersion fallback, from
   session A's item 44 notes, set in `config/batch5_tranche_1b.yaml` at merge
   (one line). Until then the panel prints "awaiting constituent prices".
3. **The overnight leg counts in SR-36's unwind watch.** I read the order's "a
   co-signal in ... SR-36's unwind-watch co-signals" literally, so the watch now
   has five co-signals and still needs two. If you meant it to print beside the
   watch without counting, it is one config line.
4. **COR1M and COR3M have no history from Yahoo.** Cboe publishes daily history
   files. Reading them would be a new writer, held for D1c; say if you want it
   once D1c lands. Until then the percentiles fill from the first pull.
5. **The by-hand drafts:** the XXVII appendix note and the two narrative-register
   entries above. Also the Wednesday FlashAlpha entries (18b).
6. **Run box commands 1 and 2** after the merge, inside a window.
7. **D1c** (carried from part 1): one ruling lifts the Census, Redfin and MBA
   holds, and item 44's writer too.
