# The Book B scanner, follow-ups ruled 13 Oct 2026: session notes

Branch `book-b-scanner-2` from the integrated `book-b-scanner` (429a527, which
carries W-1.1a, W-1.2, W-1.3a and W-1.3b). The rulings are the "Needs you" list in
`docs/briefs/book-b-scanner-notes.md`:
- volume: add;
- the Gamma timing: follow the card;
- the Volatility mapping: `normal` is Normal;
- the earnings names: add;
- `risk_usd` by code, with EL-2/3;
- the forecast's 0.5, the +1R-first hit rate and the other session-set parameters
  stay as built.

Also read: the Operating Doctrine §5.1–5.2 (the Gamma dial card) and EL-2/3's
notes on `origin/el-2-3-rollup`, for what `risk_usd` means at the order gate.

Session A, 13 Oct 2026. Nothing was run on the box, and no store but the gates'
own was touched.

## Gates run

**Not run:** the full local suite (CI is the validate). I ran the gates this
branch touches; all are green:

| Gate | Result |
|---|---|
| `validate_book_b_scanner` (group H new; one D check rewritten) | 57/0 |
| `validate_prices` (group J new; the basket count 53 → 81) | 90/0 |
| `validate_enforce` (one check's example name changed, one added) | pass |
| `check_registry` (three volume blocks; the basket blocks 53 → 81) | OK |
| `validate_weekly_calendar` | 40/0 |
| `validate_weekly`, `_complete`, `_edits`, `_stack`, `_opener`, `_analytics`, `_storyline` | pass |
| `validate_base_rates`, `validate_benchmark`, `validate_official_sources`, `validate_voices`, `validate_events` | pass |
| `validate_audit_fixes`, `validate_figure_budget`, `validate_stack_cadence`, `validate_monthly_stack` | pass |
| `validate_config_refs`, `validate_gates`, `validate_secrets`, `validate_ibkr_portfolio` | pass |

No gate was added, so the Makefile and CLAUDE.md's count are unchanged.

## What each item changed

### 1. Volume (ruled: add)

`altdata/sources/yfinance_source.py` now:
- reads `Volume` beside the close;
- stores `yfinance.<key>_volume` on the days the close was kept;
- writes the same companions from the live pull and the backfill
  (`companion_series` = the tape set's OHLC + the volume).

**The unit differs by kind, so it is declared per symbol** (`VOLUME_UNITS`).
The net-liquidity trap in CLAUDE.md is a unit copied from a neighbouring line.
There are three registry blocks, one per unit:

| Block | Members | Unit | Why |
|---|---|---|---|
| `market_volume_shares` | 65 (ETFs and stocks) | `shares` | Yahoo's equity volume |
| `market_volume_contracts` | 3 (GC=F, CL=F, HG=F) | `count` | front-month contracts, not a notional |
| `market_volume_usd` | 1 (BTC-USD) | `usd` | Yahoo quotes crypto volume in dollars |

**No volume, by declaration.** 12 symbols carry none:
- the index levels (^VIX, ^VIX3M, ^VVIX, ^SKEW, ^MOVE, ^TNX, ^TYX, ^GSPC);
- the currency pairs (JPY=X, EURUSD=X, CNY=X);
- the dollar index (DX-Y.NYB).

**A zero is never stored**, for any symbol: it is the source having none, not a
session in which nothing traded.

**The scanner** already read `<key>_volume` first, with the 5-minute-bar sum as
the fallback for SPY, QQQ and IWM. What changed:
- each instrument now carries its volume unit;
- **the liquidity score's dollar volume reads it** (`dollar_volume`): shares ×
  the close, crypto's dollars as quoted;
- futures give none, because contracts × the close misses the contract
  multiplier (100 oz, 1,000 bbl). They score the declared
  `liquidity_when_absent`, 0.5. The volume leg's ratio is unit-free, so every
  unit serves it.

**"Volume not stored"** now prints only where the source has none, or before
the backfill below has run.

**The backfill:** `tools/backfill_prices.py --volume-only` writes the
`_volume` companion alone. The closes already stored are left as they are.

### 2. The Gamma dial's timing (ruled: follow the card)

`config/book_b_scanner.yaml` `regime.timing` is now the card's "Book B timing"
column, verbatim, for all three states:
- **Positive:** "Breakouts distrusted — wait for the retest; adds on confirmation
  only".
- **Flip-zone:** "No new entries".
- **Negative:** "Breakouts trusted; pyramiding permitted on confirmation".

The candidate carries the state it was read under (`entry_timing_state`). The
line prints:

> entry timing — the regime card, Gamma Negative: "Breakouts trusted;
> pyramiding permitted on confirmation"

**Fixture:**
- XLY's short under Overheat/Negative prints the Negative words;
- XLK's breakout under Positive prints the Positive words;
- the config carries exactly the card's three states.

### 3. The Volatility dial's mapping (ruled)

The object's `normal` (VIX 14–20) now reads as the Doctrine's **Normal**, with a
multiplier of 1.0. Normal is not in `short_vol`. Shorts open, and the 0.75
applies, only at Rising or worse, as before.

**Fixture:**
- a scratch store holds fifteen sessions of an Expansion object;
- its Volatility state comes from `config/market_state.yaml`'s own level bands
  at VIX 17, which gives `normal`;
- the scanner reads it back through `regime_read`, as Expansion, Normal,
  Positive.

**In that store:**
- XLY's breakdown is refused: "no short in Expansion, Normal, Positive
  (Doctrine 4.2)";
- no short stands;
- the standing long's size is "0.75% of capital at risk (0.75% × 1: Volatility
  Normal 1)".

**A consequence, see Needs you 1:** the object's level bands carry no
"climbing" leg, so no object state reads as Rising any more. `elevated`
(VIX 20–30) is still Stressed.

### 4. The 28 earnings names (ruled: add)

`SYMBOLS` gains the earnings universe less NVDA: AAPL ABBV AMZN AVGO BAC BRK-B
C COST GOOG GOOGL GS HD JNJ JPM LLY MA META MS MSFT NFLX ORCL PG TSLA UNH V WFC
WMT XOM. The keys are `mkt_<name>`, and BRK-B is `mkt_brk_b`.

- **The basket set.** `EARNINGS_SYMBOLS` holds the 29 as a set. A gate checks
  that it equals `earnings.universe()` today and sits inside the basket.
- **Restricted names.** None of the 29 is on the restriction list. The scanner
  still drops any restricted name at load, at the ledger and at print.
- **The registry.** `market_closes` and `market_actions` read 81 members. The
  scanner reads the new names like the rest.

**Fixture:** a scratch store with AAPL and BRK-B closes and volume.
- Both enter the universe, BRK-B by its yfinance ticker.
- MSFT, with no closes, stays in "earnings not stored".

### 5. `risk_usd` by code (ruled with EL-2/3)

Every candidate carries `risk_usd`, computed as the paper capital
(`config/risk_limits.yaml`, `capital_usd` 300,000) × its printed risk
percentage. That is the dollars from entry to invalidation at the printed size,
the meaning EL-2/3's heat gives it.
- **The archive.** It joins the candidate's archived fields
  (`daily_cascade/book_b.FIELDS`).
- **The print.** The size reads "… = $2,250 of the $300,000 paper capital".
- **The order gate.** A candidate the sitting takes has the input that gate needs.
- **The position.** Its notional is computed from the same figure.

**Fixture:** every candidate in two scans carries
`risk_usd = capital × size%`, and the standard-tier long carries 2,250.00.

### 6. As built (ruled)

These are unchanged:
- the forecast's 0.5;
- the +1R-first hit rate;
- every session-set parameter except item 3's mapping.

## The backfill, for Ari (after merge, on the box, inside the windows)

Run these after `book-b-scanner-2` merges and the box has pulled it. Run them
before Sunday 05:00, so the Weekly's scanner reads the history, and keep clear
of 16:00–17:20 ET. Each takes `--dry-run` first if you want the counts.

```
# the 28 new names: five years of closes, actions and volume
ssh vps 'cd ~/chester-reports && .venv/bin/python tools/backfill_prices.py --years 5 --symbols AAPL,ABBV,AMZN,AVGO,BAC,BRK-B,C,COST,GOOG,GOOGL,GS,HD,JNJ,JPM,LLY,MA,META,MS,MSFT,NFLX,ORCL,PG,TSLA,UNH,V,WFC,WMT,XOM'

# the volume beside the closes already stored (the whole basket; indices and
# currency pairs write nothing; re-running is idempotent)
ssh vps 'cd ~/chester-reports && .venv/bin/python tools/backfill_prices.py --years 5 --volume-only'
```

Until they run, the eod pull's two-year live read stores the new names' closes
and every symbol's volume from the next 16:10 on, stamped with the pull instant.
The backfill adds the reconstructed vintages behind them.

## Found on the way

- **EDGAR's universe grows by 27 names.** `altdata/sources/edgar.universe()`
  derives the equities from `SYMBOLS`, excluding any ticker with `^`, `=` or
  `-`, so BRK-B stays out. The filings scan reads 27 more companies from the
  next run.
- **The eod pull goes from 53 symbols to 81.** At 0.5 s pacing plus the fetch,
  that is under a minute more, inside `chester-eod.service`'s 30-minute
  timeout.
- **The freshness watch** lists the new close and volume series from the merge.
  They read PENDING until their first pull, by `feeds.py`'s rule.
- **`validate_enforce`'s "no beta → delay" check** used AAPL as its name outside
  the basket. It now uses AMD, and a second check holds that a basket name with
  no stored closes (AAPL) delays too.
- **The Flip-zone is marked, not refused.** "No new entries" prints as the
  timing line, and the candidate still stands, as `book-b-scanner` built it.
  See Needs you 2.
- **CLAUDE.md's layout line** still says yfinance pulls "27 market symbols". It
  was already stale at 53 and is left alone, to keep tonight's merges free of
  CLAUDE.md conflicts.

## Needs you

1. **No object state reads as Rising now.** With `normal` → Normal, the
   Volatility dial opens shorts only at `elevated` (VIX ≥ 20), which maps to
   Stressed at 0.5. The Doctrine's Rising is "mid-teens to low twenties *and
   climbing*", and the object's bands carry no climbing leg. Keep
   `elevated` → Stressed / map `elevated` → Rising (0.75) / add a climbing leg
   to the object (a config v1.13 bump).
2. **Should the Flip-zone refuse at the gate?** The card says "No new entries".
   As built, the line prints that, and the candidate still stands and is graded.
   Keep marked / refuse at the gate (the candidate goes to the refused list,
   still graded).
3. **The two backfill commands above** are yours, on the box, after merge.
4. **EDGAR's 27 new names:** accept the wider filings scan / hold EDGAR at the
   old list (a second list, which `edgar.universe()`'s docstring argues
   against).

## Second rulings (13 Oct 2026, evening)

Two rulings on this branch's needs-you list, built in one commit on top of
`d69ea1d`.

**1. The Volatility dial: `elevated` is Rising.** The object's `elevated` (VIX
20–30) now maps to the Doctrine's Rising, at 0.75, and shorts open there.
`normal` stays Normal. The Doctrine's "and climbing" leg is deferred to
Doctrine #2, a config v1.13 bump to the object. Until then, Rising is read on
the level alone.

- `config/book_b_scanner.yaml`: `vol_map` `elevated: Rising`, with the ruling
  in the comment.
- Fixtures, in `validate_book_b_scanner` group H:
  - VIX 17 is `normal`, reads Normal, opens no shorts and takes no 0.75
    (unchanged, still passing);
  - VIX 24 is `elevated`, reads Rising, and XLY's breakdown stands as a short
    at "0.56% of capital at risk (0.75% × 0.75: Volatility Rising 0.75)".

**One reading to confirm.** The ruling says "anything above `elevated` stays
Stressed (0.5)". The object has one state above `elevated`, `crisis` (VIX 30 and
over), and it maps to **Crisis**, not Stressed: the card's 0.0, which closes
Book B. "Stays" reads as no change, so I left `crisis → Crisis` as built, and
the gate holds it. If you meant `crisis → Stressed` (Book B open at 0.5 above
VIX 30), it is a one-word change to `vol_map`. Say so and I will make it.

**2. The flip zone refuses at the gate, and is still graded.**

- `config/book_b_scanner.yaml` gains `regime.refuse_timing: [Flip-zone]`.
- `altdata/book_b_scanner.timing_refusal()` runs after `gate()`. So only a
  candidate that passes every other gate is refused here, with the card's
  words: "the Gamma dial's Flip-zone: “No new entries” (the regime card,
  Doctrine 5.2)".
- The refused entry carries `graded: True` and its score.
- `book_b_scanner.graded(run)` is the standing candidates plus those refusals.
  The Weekly's ledger write (`weekly_stack`) now records `graded(run)`, so each
  such refusal is a forecast, resolved like any other.
- The Book B block's refusal note prints the reason, card's words included.
- Fixture: under Expansion, Calm, Flip-zone, no candidate stands. GLD, the long
  that passes every other gate, is refused with the card's words. It is written
  to the ledger, and resolves 1 when the next week's closes cross +1R.

**Gates run:**

| Gate | Result |
|---|---|
| `validate_book_b_scanner` | 62/0 |
| `validate_weekly_calendar` | 40/0 |
| `validate_weekly_stack`, `validate_weekly`, `validate_weekly_complete`, `validate_config_refs`, `validate_gates` | pass |

Needs you 1 and 2 above are answered by these rulings. Needs you 3 (the
backfills) and 4 (EDGAR) stand.
