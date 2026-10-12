# C1 items 1 and 5 — the store-wide move screen and the EM screen: session notes

Branch `c1-move-screen` from `origin/main` at 785fa19 (not from
`w-1-1-integrity`). Spec: Audit #4 agenda Part III rows 1 and 5. The SR-46
entry in the batch-4 change order (its four-part ruling). The SR-35 entry in
batch 3. Session A, 11 Oct 2026.

**Not run:** the full local suite (CI is the validate), and anything on the box.
The gates this branch touches were run one at a time, all green:

| Gate | Result |
|---|---|
| `validate_move_screen` (new) | 45/0 (39 before the Quarterly's hook) |
| `validate_prices` | 81/0 |
| `check_registry` | OK |
| `validate_register` | 171/0 |
| `validate_derived` | 45/0 |
| `validate_feeds_scheduled` | 19/0 |
| `validate_deploy` | 118/0 |
| `validate_systemd_units` | 75/0 |
| `validate_daily_close` | 102/0 |
| `validate_stack` | 66/0 |
| `validate_weekly_stack` | 68/0 |
| `validate_weekly_complete` | 56/0 |
| `validate_stack_cadence` | 99/0 |
| `validate_monthly_stack` | 261/0 |
| `validate_readability` | 63/0 |
| `validate_weekly_edits` | 89/0 |
| `validate_weekly` | 100/0 |
| `validate_monthly` | 350/0 |
| `validate_config_refs` | 25/0 |
| `validate_morning_anchor` | 71/0 |
| `validate_gates` | 31/0 |
| `check_library` | 0 failures |

## What was built

**Item 1: the store-wide move screen** (`altdata/move_screen.py`, config
`config/move_screen.yaml`).

- **What is screened.** Every series the registry declares daily and the store
  holds, per instrument where a key has instruments. The registry decides:
  `freq: daily`, or `native_horizon: daily` for the yfinance basket. Excluded,
  by key prefix and suffix in config:
  - the reports' own outputs (`screen.`, `events.`, `dealer.`, `paper.`,
    `market_state`), and `pm.` (screened as families, below);
  - OHLC legs and dividend/split events.
  - A series whose last point is older than the previous session is not
    screened that day. That covers a retired series, or FRED's weekly-posted
    dailies between postings.
- **The test.** Each series' 1-day and 5-day change, as a z against its own
  five-year history of such changes (today's excluded). Flagged past 2.5σ,
  two-sided.
- **The unit rule.** A price moves by its log change: the registry's delta unit
  is "percent", which covers prices, index levels and currencies per dollar.
  A rate, a spread, a percentage or a probability moves by its simple
  difference, and so does any other raw unit (counts, balances, ratios).
- **Skipped.** Fewer than 500 observations; each skipped series is named in
  the stored summary.
- **The false-flag base rate**, printed "false flag k/N":
  - **N** counts the series' own past prints past 2.5σ over the window, on
    the horizon that flagged today. That is the larger |z| of the two.
  - **k** is how many of them were at least half reversed within five
    sessions.
- **Output.** The 16:45 close wrapper runs `python -m altdata.move_screen write`
  after the features pass (`scripts/run_daily_close.sh`). It is never fatal.
- **Stored.** The rows give each flag its point-in-time record:
  - `screen.move`: one row per flagged series;
  - `screen.move_summary`: counts, the skipped list, and SR-35's companion;
  - `screen.em` and `screen.em_contagion`.
  Each row has `observed_at` = the session and `available_at` = the compute
  instant. All four keys are registered under a new mechanism group,
  `move_screen`.
- **How the reports read it.** The reports read the stored result. With
  nothing stored (CI, a laptop), they compute it in memory and write nothing.
- **What doesn't fit**, on both the close and the Weekly:
  - the top 3 flags (close) or top 5 (Weekly), ranked by |z|;
  - "n more past 2.5σ -- in the tables";
  - every flag in a "Moves past 2.5σ" detail table after section 10. The Weekly
    now prints a detail-tables tier for it.
- **Subsumed, with no separate code path:**
  - **SR-35:** the 10-year's two-week (10-session) and one-month (21-session)
    change as a z on a twenty-year window. It prints as the 10-year row's
    companion at 2σ, beside its row when that row is flagged, otherwise on its
    own.
  - **SR-46(a):** the basket members are store series.
  - **The prediction-market shock flag:** a contract's 5-day move in points,
    against its family's pooled 5-day moves, printed with its family name.

**Item 5: the EM screen (SR-46 b–d).**

- **New series**, codes and units checked against each FRED page on 11 Oct:
  - FRED H.10, local currency per dollar, daily: `fred.usd_brl` (DEXBZUS),
    `fred.usd_zar` (DEXSFUS), `fred.usd_inr` (DEXINUS), `fred.usd_krw`
    (DEXKOUS), `fred.usd_twd` (DEXTAUS), `fred.usd_thb` (DEXTHUS).
  - EM spreads, percent, daily: `fred.em_corp_oas` (BAMLEMCBPIOAS) and
    `fred.em_hy_oas` (BAMLEMHBHYCRPIOAS).
  - These go into `FRED_SIGNAL_SERIES`, the existing FRED pull, and the
    registry block now expects 32 members.
  - MXN and CNY were already stored.
  - yfinance: `TRY=X`, `IDR=X` and EWZ, EWW, EZA, INDA, EWY, EWT, THD, FXI,
    TUR, EIDO. The yfinance basket and its two registry blocks now hold 65
    symbols, and `validate_prices` was updated to match.
  - The six new currency units were added to the delta-unit table.
- **(b) Dispersion against co-movement.**
  - Every member is read in stress terms: a currency per dollar rising, or an
    ETF falling.
  - **Systemic:** at least 80% of the members move the same way and the median
    5-day stress z is at least 1.0. The line ends "systemic -- dollar/risk-off;
    Factor IV's business".
  - **Idiosyncratic:** exactly one country is past 2.5σ. The line ends "a
    candidate for the narrative register". It is printed only; nothing writes
    to any register.
  - **Mixed:** more than one country is flagged without the basket moving.
- **(c) EM spreads.** Each spread's level, 5-day change and percentiles. One is
  over the stored history; the other is over five years where five exist.
  - On the close, an "EM leg" line goes in Plumbing & rates. On the Weekly, an
    "EM leg" table sits under Plumbing.
  - Report-only. The HY Spread Acceleration overlay is not built in this repo,
    so there is no overlay output to sit beside and nothing is wired.
- **(d) The contagion rule.**
  - Each single-country shock is a state with its shock date and a
    five-session window.
  - It is `passed` when a systemic session follows inside the window, or when
    an EM spread's 5-day change reaches 2σ, and the state records which and
    when. Otherwise it stays `watching`, then becomes `lapsed`.
  - The state is recomputed from the store for the last ten sessions and
    stored per shock.
  - The close prints every shock. The Weekly prints only one that passed.
- **The EM calendar.** `config/em_calendar.yaml` is a template with the fields
  (date, country, event, pm_market_id, source) and no entries. The loader
  prints the current quarter's entries, on or after the day, into Ahead: an
  item on the close, an "EM calendar" sub-section on the Weekly. Today it
  prints nothing.

**The gate.** `tools/validate_move_screen.py`, on a synthetic store, covers:

- **The flag:** a −6% session flagged and a normal one not, the 300-observation
  series skipped and named, and the write-and-read round trip.
- **The base rate:** on a constructed history of four past spikes, three
  reversed, it prints "false flag 3/4".
- **The unit rule.**
- **SR-35's companion and the prediction-market family flag.**
- **The classification:** systemic, idiosyncratic and mixed.
- **The contagion window:** passed to the basket, passed to spreads, lapsed and
  watching. The close prints every shock, the Weekly only one that passed.
- **The Weekly's lines:** top five, the companion beside the 10-year, "n
  more", and the reference tier.
- **The calendar:** empty prints nothing; a seeded entry prints in its quarter.

It is in the Makefile, and CLAUDE.md's count is now forty-eight code gates.

**Series skipped (fewer than 500 observations).** The box store could not be
read from here, so the list below comes from the laptop's local copy,
`data/chester.db`. That copy ends 18 Sep 2026, and the screen ran on it
read-only.

- It screened 46 series and skipped 5: `cfe.vx_settle` for the 2026-10-21 (164
  observations), 2026-11-18 (145), 2026-12-16 (125), 2027-01-20 (106) and
  2027-02-17 (81) contracts. A VIX futures contract never lives 500 sessions.
- The 20 new EM members are not in that store at all.
- On the box, `python -m altdata.move_screen skipped` prints the real list. It
  also prints the prediction-market families too short to pool, and the
  stored summary carries the list every session.

**The Quarterly's hook (follow-up).** `altdata.move_screen.quarter_episodes(st,
now)` returns the quarter's EM episodes, oldest first, or `[]` when there are
none. Session B's AQ-2 part 2 calls it by that name. Each row carries `date`,
`series`, `horizon`, `z`, `false_flag`, `classification` and `contagion_passed`,
plus `country` and `kind`. There are two kinds:

- **`member`:** a basket member's store-wide screen flag. It is read from the
  stored session result where one exists, otherwise recomputed from the store
  as of `now`.
- **`spread`:** the session an idiosyncratic shock passed to EM spreads, with
  the spread that widened most and its 5-day z.

Gate group H is its fixture.

## Choices made for the operator to overrule

- **The Quarterly's hook.**
  - "The quarter ending at `now`" is the three calendar months before it, not
    the calendar quarter that contains it. The two agree when `now` falls on a
    quarter end.
  - A member's run of consecutive flagged observations is one episode, because
    a shock's 5-day z stays past 2.5σ for several sessions. It is dated at the
    run's first observation and carries the run's largest |z| and its horizon.
  - The systemic, idiosyncratic or mixed state is under the key
    `classification`.
  - `contagion_passed` is True only for an idiosyncratic shock that passed.
  - There is one spread event per episode, and its `false_flag` is None,
    because the contagion rule has no base rate.
  - A bare date for `now` reads the store without a cutoff. A timestamp is the
    point-in-time cutoff.

- **The false-flag definition, for you to confirm.**
  - A past print is a change on the same horizon past 2.5σ. It is identified
    against the same five-year window's mean and spread: in-sample, not each
    print against its own trailing window.
  - It is "reversed" when, on any of the five sessions after it, the level is
    back at least half the move, in the same unit (log for a price).
  - A print needs five sessions after it, known by today, to count.
  - Today's base rate uses the horizon with the larger |z|.
  - The stored daily rows are what accrue point-in-time from here.
- **The unit rule's raw units.** Counts, balances and ratios move by their
  difference, the brief's rule for "everything not a price". A log change
  would also be defensible for a positive balance.
- **What "daily" means.** `freq: daily`, or no freq with `native_horizon:
  daily`. Excluded: the prefixes and suffixes in config, label-unit keys, and
  `pm.*` (screened as families). Series per instrument, so each VIX future and
  each fed-funds contract month is its own series, and each is skipped until
  it has 500 points.
- **Prediction markets pool by family** (`watch_id`). No contract lives 500
  sessions, so a contract's 5-day move is a z against the pooled 5-day moves
  of its family, needing 500 pooled. Families below that are listed, not
  screened. A pm flag's false-flag base rate is not computed (printed 0/0).
- **FRED's H.10 currencies post weekly.** A week of dailies arrives each
  Monday. The EM screen reads a member on its latest point up to seven days
  old and stores that date. The store-wide screen skips any series not
  updated since the previous session, so a FRED currency is screened only
  around its posting.
- **The EM spreads' five-year percentile.** FRED now serves three years of
  each, its own note since April 2026. The line prints its real window ("since
  <first date>, the history FRED serves") until five years accrue in the
  store.
- **Systemic and idiosyncratic thresholds** (session-set, config):
  - co-movement of at least 80% and a median stress z5 of at least 1.0;
  - idiosyncratic is exactly one country past 2.5σ, either member;
  - contagion via spreads is a 5-day widening z of at least 2.0.
- **How many lines print:** 3 on the close and 5 on the Weekly (config
  `print_lines`), ranked by |z|; every flag is in the detail table. Each line
  is code-written, not prose, so it does not draw on the paragraph's figure
  cap.
- **The Monthly is not wired.** The Monthly calls the Weekly's `misfit_week`
  without a screen, so it prints no move-screen lines. Passing it one is a
  one-line change.
- **Where the screen runs.** The 16:45 close wrapper, not the 16:10 EOD pass,
  so it sees the final prices. The Weekly reads Friday's stored result.

## Needs you

1. **Should the box backfill five years of the twelve new Yahoo symbols?** That
   is TRY=X, IDR=X and the ten country ETFs, via `tools/backfill_prices.py`.
   The routine pull fetches two years, about 500 sessions: just enough to be
   screened, not five years of history. It is your command to run on the box.
   Yes / no.
2. **Confirm the false-flag definition above?** It uses the in-sample spread, a
   half reversal within five sessions, and the horizon that flagged. Yes / no.
3. **Pool prediction-market contracts by family** for the shock flag, since no
   single contract reaches 500 observations? Yes / no.
4. **Keep the EM thresholds as set?** That is co-movement of at least 80%, a
   median stress z5 of at least 1.0, and a 2σ spread widening for contagion.
   Yes / no.
5. **Read BRL, ZAR, INR, KRW, TWD and THB from Yahoo** (`BRL=X` etc.) instead
   of FRED's weekly-posted H.10? That gives same-session reads; the SR-46
   ruling named FRED. Yes / no.
