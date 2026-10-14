# The Book B scanner — the Weekly's candidate list: session notes

Branch `book-b-scanner` from `origin/w-1-3b-analytics` (66622ba). Spec: the
brief `docs/briefs/book-b-scanner-brief-2026-10-12.md` (ruled 12 Oct 2026, all
eight decisions yes), committed first. Also read: the Operating Doctrine §4.2
(Book B) and §5.1–5.2 (the dials and the regime card), Appendix D (the ratified
mapping), and the Technical Indicators paper.

Session A, night of 12–13 Oct 2026.

## Gates run

**Not run:** the full local suite (CI is the validate), and anything on the box.
I ran the gates this branch touches one at a time; all are green:

| Gate | Result |
|---|---|
| `validate_book_b_scanner` (new) | 44/0 |
| `validate_weekly_calendar` (updated, below) | 40/0 |
| `validate_weekly_opener` | 28/0 |
| `validate_weekly_analytics` | 35/0 |
| `validate_weekly_stack` | 68/0 |
| `validate_weekly_storyline` | 30/0 |
| `validate_weekly_edits` | 90/0 |
| `validate_weekly_complete` | 57/0 |
| `validate_weekly` | 100/0 (1 skipped) |
| `validate_figure_budget` | 110/0 |
| `validate_readability` | 63/0 (the PDF is not validated here: no WeasyPrint) |
| `validate_stack_cadence` | 99/0 |
| `validate_monthly_stack` | 261/0 |
| `validate_config_refs` | 28/0 (with the new YAML tracked) |
| `validate_gates` | 31/0 |
| `check_library` | 0 failures |

**One gate updated.** `validate_weekly_calendar`'s section C tested the block
with no scanner ("no scanner yet") and against a hand-written fixture. The
scanner now exists, so section C checks that:

- the block prints the scanner's result;
- the "activates when" line is gone;
- a dry-run Weekly writes its forecasts to the dry-run namespace.

Its fixture is now the scanner's own candidates over the scanner gate's
synthetic store. Two hand-written rows are added to that fixture: an undeclared
setup and a restricted instrument. The scanner never writes either, so they are
what tests the block's own guards. The productivity counts follow.

**Two findings on the way:**

- `validate_config_refs` refused the config's partial price prefix and the TFF
  key. Both are now built in code from named parts.
- `validate_weekly_edits` refused a bare `tempfile.mkdtemp` in the new gate. It
  now uses `gate_tmp`.

The Makefile carries the new gate. CLAUDE.md on this branch now reads fifty-six
code gates.

## What was built

**`altdata/book_b_scanner.py` and `config/book_b_scanner.yaml`.** The scanner
runs inside the Weekly's build over Friday's close, and nowhere else (decision
7). It reads the store, fetches nothing, and writes only the ledger forecasts.

1. **The universe** (decision 1). Every `yfinance.mkt_*` close series with at
   least 120 sessions.
   - Excluded: the companions (`_high`, `_low`, `_volume`, …) and the index
     levels (VIX, MOVE, the yields, ^GSPC).
   - **The blocklist at write time.** A restricted instrument is dropped at load,
     before anything is computed for it. It is refused again at the ledger write
     and again at print.
   - **The earnings universe.** Its names enter where the store carries their
     closes. Today that is NVDA only; the rest are counted as "not stored".
2. **The primary trend.** Four conditions: the close against the 50-day, the
   close against the 200-day, the 50-day against the 200-day, and higher highs
   plus higher lows over 60 sessions. Three of four is the trend.
   - **Against the tape.** A candidate against the trend is tagged and carries a
     five-session time stop and no add.
3. **The three pivots, as code.** Each fired in the week and still holds at
   Friday's close.
   - **Breakout:** a close through the high of the longest base of 20–60
     sessions with range ≤ 10% of price, on volume ≥ 1.5× its 20-session average.
     The base is the one the close actually cleared: no window reaching back into
     older, higher prices.
   - **Reclaim:** a close back through a level lost within 10 sessions, on
     volume. The level is a base high, the 50-day, or a wall the chain names, and
     it must have held 5 closes before it was lost.
   - **Failed breakdown:** a close below the base low, back above it within 5
     sessions. It dates from the first close below.
   - **Shorts** are the mirrors: a breakdown, the loss of a regained level, a
     failed breakout.
   - **Where they print.** The parameters print beside each candidate, and the
     block's note states them all as set.
4. **The confirmations** (decision 3), counted by code:
   - **Relative strength:** the instrument/SPY ratio's percentile in 60
     sessions; ≥ 80 for a long, ≤ 20 for a short.
   - **Positioning:** the CFTC speculative net, or for the yen and the euro the
     TFF leveraged funds, as a two-year level z, |z| ≥ 1.5. A crowd the other way
     confirms; a crowd the same way prints a WARNING.
   - **A Weekly tell that names the instrument:**
     - the style-regime pair (SR-1);
     - XLY/XLP and the consumer RS tell (SR-5);
     - the move screen's 2.5σ print, read from `altdata.move_screen` by name.
   - **A T&B overlay.**
   - **The correlation break** for the Alt Asset instruments, read from
     `altdata.correlation` by name.
   - **Hooks not yet live.** Two hooks read nothing on this branch and say "not
     read" on the candidate: the move screen (`c1-move-screen`) and the
     correlation break (`aq-5-correlation-layer`). Both activate when their
     branch merges.
   - **Thresholds.** A long needs one confirmation, two after a T&B top signal.
     A short needs two plus the regime's permission.
   - **The counter-thesis** is the warnings, then the unmet confirmations, then
     the ones not read.
5. **The regime gates.** They read the dials and recompute none:
   - **The Doctrine regime:** read through `register.heat.regime_band`
     (`dial-to-doctrine-v1.1` with the crossing rule).
   - **Shorts:** only in Overheat, Tightening or Contraction, or with the
     Volatility dial at Rising or worse.
   - **Crisis** closes Book B.
   - **The size multiplier:** Volatility × Transition, capped at 1.0.
   - **Negative gamma** marks "entry timing: wait for positive gamma or a session
     close above the flip"; the flip zone marks "no new entries".
6. **Score and rank** (decision 4). The score is the weighted mean of five
   components on [0, 1], with equal weights:
   - trend (the share of the four conditions);
   - base (tightness × duration);
   - confirmations (met / 3);
   - regime alignment (the Macro card's Book B column);
   - liquidity (the position's notional against the 20-session dollar ADV;
     0.5 where no volume is stored).

   The top ten print in §10. Every candidate below the ten goes to the
   reference tier, one row each.
7. **The draft.** The register's fields, code-templated, with no model.
   - **Invalidation:** the base low, the reclaimed level, or the breakdown low,
     less a quarter of the average true range (the paper's zone buffer).
   - **Horizon:** one to six weeks.
   - **Time stop:** 15 sessions, or 5 against the tape.
   - **Size:** 0.75% × the dials' multiplier, printed with its factors.
   - **Expected R:** the base's measured move against the invalidation distance.
   - **Catalyst:** the name's own earnings, else the week ahead's first tier-1
     release.
   - **The ruled shape:** `setup_id` comes from `config/setups.yaml`.
     `candidate_id` is the scanner's own, and `decision_id` is null.
8. **Grading** (decision 6). Every candidate, taken or not, is written to the
   probability ledger at build time:
   - **The forecast:** "reaches +1R before −1R within six weeks", under its setup
     and its id.
   - **The criterion** is declared at emission.
   - **The namespace:** `book_b_candidate`, or `dryrun.book_b_candidate` for a
     dry run.
   - **Resolution:** from the stored closes at each Weekly, by the first barrier
     touched, or 0 at six weeks.
   - **The graded-calls line** in Ahead reports the candidates on their own line,
     "never pooled with the operator's decisions". They are kept out of the pooled
     Brier rows.

**The hook into W-1.3a's §10 block** (`daily_cascade/book_b.py`):

- `scanner_run` reads the scanner's whole result. `scanner_output` keeps the
  candidates-only hook.
- Each line carries the scanner's terms: the WARNING, against the tape, the
  entry timing, R, the parameters, the counter-thesis.
- The "activates when the scanner merges" line is gone. A scanner that fails
  prints "could not be read this week".
- `weekly_stack.build` and `produce` pass `dry_run`, the week ahead's calendar
  and the chain's walls through to it.

## Choices made for the operator to overrule

- **The setup ids are on this branch already.** `config/setups.yaml` with
  `b_breakout`, `b_reclaim` and `b_failed_breakdown` is on `w-1-3b-analytics`,
  the same entries as `origin/el-1-packets`. The scanner reads them through
  `register.store.setup_ids()`, and no "activates when el-1 merges" hook was
  needed. A pivot whose setup id is not declared is dropped and counted.
- **A short is the same family, mirrored.** A breakdown is graded under
  `b_breakout`, the loss of a regained level under `b_reclaim`, a failed breakout
  under `b_failed_breakdown`. The ledger separates long and short by the claim's
  direction.
- **Relative strength is a time-series percentile.** It is the instrument/SPY
  ratio ranked within its own 60 sessions, not a cross-section of the universe.
  It is defined per instrument, so it does not move with the universe's
  composition.
- **The tells, as built:**
  - **The style pair:** the value side is named when the growth/value ratio is
    below its 200-session average, or more than 8% off its 52-week high. The
    SR-1 stretch condition (2σ above a ten-year trend) needs history the store
    does not hold.
  - **The consumer RS tell** reads XLY against SPY. The equal-weight
    discretionary fund and the homebuilders are not stored. SPY, the benchmark,
    is never named by it.
- **The Top & Bottom hook.** It reads two store keys by name, `tb.signal` and
  `tb.overlay`, and counts nothing until a writer stores them. The names are
  mine; the T&B report should write them.
- **Volume from the 5-minute bars.** Where no daily volume is stored, SPY, QQQ
  and IWM sum their complete 5-minute sessions, so they get a volume leg from
  about 60 days of bars.
- **Within a week, one pivot per instrument and direction.** The latest pivot is
  kept. On the same session the more specific pivot wins: a base cleared, then a
  base's edge failed, then a level.
- **Contraction longs** score 0 on regime alignment but are not refused. The
  Doctrine's "bottom-fishing prohibited until the T&B bottom signal" waits for
  that signal to exist.
- **The candidate's archived shape** is unchanged (the ruled fields). The
  scanner's extra terms print on the line and are not archived.

## Needs you

1. **Daily volume is not stored for the basket.** The yfinance pull stores
   closes, plus OHLC for nine tape symbols, but no volume. The volume leg of a
   breakout or a reclaim is therefore testable only for SPY, QQQ and IWM, from
   their 5-minute bars. Everywhere else the pivot fires with "volume not stored —
   the volume leg unconfirmed", and that goes into the counter-thesis. Options:
   - **add volume:** a `_volume` companion beside the OHLC in
     `yfinance_source`, its registry block and a backfill;
   - **keep unconfirmed;**
   - **strict:** refuse the pivot instead.

   Add volume / keep unconfirmed / strict.
2. **The Gamma dial's timing reads opposite to the Doctrine's card.** The brief
   and the paste say negative gamma marks "entry timing: wait", and that is what
   is built (one line of config). The card, §5.2, says the reverse:
   - **Negative gamma:** "breakouts trusted; pyramiding permitted on
     confirmation";
   - **Positive gamma:** "breakouts distrusted — wait for the retest";
   - **The flip zone:** no new entries. That part is built as the card says.

   Keep the brief's reading / follow the card.
3. **The forecast's probability is 0.5.** No setup cites a base rate yet
   (`setups.yaml`: "base_rate: not yet"), so each forecast is the symmetric
   barrier's coin. Its Brier is therefore always 0.25, and the candidates' line
   reports the +1R-first hit rate instead. Keep 0.5 until a setup cites a base
   rate / name a value.
4. **Keep the session-set parameters?**
   - base N 20–60, R 10%, V 1.5×;
   - L 10, held 5, F 5;
   - a quarter-ATR buffer;
   - RS 80th/20th percentile over 60 sessions;
   - crowded at |z| ≥ 1.5;
   - the alignment table.

   One mapping has consequences: the object's Volatility dial at `normal`
   (VIX 14–20) reads as the Doctrine's Rising. That opens shorts and applies the
   0.75 multiplier at an ordinary VIX. Yes / no, or name the changes.
5. **The earnings universe's names are not in the store.** Decision 1 puts the
   29 names in the v1 universe, but the price basket carries only NVDA, so 28
   print as "not stored". Options:
   - add their closes to the basket (`yfinance_source.SYMBOLS`, the registry and a
     backfill; a box pull change after merge);
   - leave them for the single-name item.

   Add / leave.
