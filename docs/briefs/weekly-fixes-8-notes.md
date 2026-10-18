# weekly-fixes-8: the fixes from the first live Weekly (session notes, 18 Oct 2026)

**This branch, `weekly-fixes-8`, is cut from the tip of `writer-fixes-1`
(`4cad29b`), which is Monday's chain. It merges on Monday 19 Oct, after
`writer-fixes-1`, and before anything on chain #2.** Tuesday's stitch carries it
into chain #2 (the shared files are listed below).

Branch only: pushed, not merged, not deployed, nothing run on the box. No unit
was enabled, started or reconfigured. Session A's `st-t3-calib` and its branches
were not touched, and chester-meme was not touched at all.

| Part | Commit |
|---|---|
| The fixes and their gate | `7af5b0e` |
| These notes | the commit after |

## What I read first

- **The faults, as the paste wrote them.** I cannot see this morning's edition.
- **My weekly-fixes-7 notes**, so nothing is fixed twice:
  - item 12's signed-zero rule is already in `_change` (below one, two places);
  - item 3 is the 10-year's tape-versus-FRED rule.

  W8-8 and W8-13 extend those two rules and do not redo them.
- **The commentary writer and its audit loop** (`daily_cascade/stack_prose.py`
  `write`/`run`/`attempt`, `opener.retry_note` and its `RULES`, `precis.write`).
  - The Weekly already had three attempts, and the précis three.
  - Each retry was told the reason and the rule, then asked to "write it again
    from the same data". It was **never shown its own draft**, so it re-drew a
    new draft with new faults.
  - The closes' and anchors' `narrative.generate` callers drafted once.
- **The numeral audit**: `audit()`, its type check (`COMPATIBLE` lets "points"
  accept a z, which is how "1.6 points of open interest" passed) and the label
  audit (G-1).
- **The Weekly's tape and mechanics builders**: Plumbing's `change_over` rows,
  Positioning's CFTC/TFF and FINRA rows.
- **The Ahead matrix**: `implied_move` and `earnings_row`, the classes'
  channels, and the technical appendix row in `config/reporting_stack.yaml`.
- **The Book B scanner and its "Pivots as set" line**, for the weekly-fixes-9
  queue only.
- **CLAUDE.md.**

## The faults, where each was, what changed, its fixture

### W8-1: the audit retry

**Where.**
- `stack_prose.write`'s `run`: the Weekly's three attempts, the close's two.
- `precis.write`: three attempts.
- `close_report.py` and `morning_anchor.py`: one draft, no retry.

None of these retries carried the draft.

**What changed.** `daily_cascade/audit_retry.py` is the one retry:
- **When:** on any audit failure, ONE revision.
- **The prompt:** the same data block (the user message is the first call's,
  byte for byte), the whole withhold message, the failing rule's text (opener's
  `RULES`), the **failing span** and the **draft itself**, with "Revise THAT
  draft: fix exactly the failing span under the rule above and change nothing
  else".
- **The span:** each quoted fragment the reason names, or the sentence holding
  each figure the numeral audit refused. For a length or shape fault it is
  "the draft as a whole".
- **The outcome:** audited again exactly as the draft was. A second failure
  withholds and prints the second reason, as before (`first_reason` is kept).
- **What is not retried:** a fault that is not the prose's (no client, a failed
  call, the payload guard, an empty reply, a runaway length).
- **The log:** both attempts go to the run log as `audit retry:
  <report>/<section> attempt n of 2 ...`, with the withheld draft. That is the
  log the EL-6 withheld-drafts log takes over once it merges; EL-6 is not built
  here.

**Every report that uses the loop:**
- `stack_prose.run`, which covers the Weekly, the stacked close and the stacked
  Monthly;
- `precis.write`;
- `close_report` and `morning_anchor`, through `audit_retry.generate`.

The Monthly v2 fallback's own loop (`monthly_macro/prose.py`, three attempts)
is not this writer and is unchanged. Needs-you 1.

**The cost:** one extra model call per failed audit, bounded to one.
- The Weekly's and the précis's three attempts are withdrawn: the
  `prose_attempts: 3` key is gone, and `ATTEMPTS = 2` everywhere.
- So the worst case per section falls from three calls to two.

**Fixtures** (`validate_weekly_fixes_8` A):
- a 159-word Narratives draft in the Weekly's medium band (80 to 150) is revised
  once and publishes;
- a draft that fails twice is withheld with the second reason and no third call;
- the revision note carries the reason, the opener rule, "the draft as a whole"
  and the draft;
- Plumbing's filler fault names its sentence as the span, with the filler rule;
- a failed call is not retried;
- both attempts are logged.

The narrative path runs through the real `generate` and the real numeral audit,
with a fake client: 1.5% is withheld and 1.2% published; both calls' messages
are identical, and only the system prompt grows. Twice wrong prints the second
reason. No model is called anywhere.

### W8-2: numeral binding

**Where:** `altdata/numeral_audit.audit()`. The plain match passed any figure
that exists anywhere in the payload.

**What changed:** `series_bindings`, run after the label audit.
- **The series:** read from the section's data block. That is every labelled
  dict (label, name, series, contract, symbol...) and every table row (first
  cell the label, **each cell typed by its column head**, so "Four-week change
  z" is a z).
- **The aliases:** the label, a ticker in its brackets, the name before them,
  the symbol and the declared aliases.
- **The binding:** a measured figure (a percent, a decimal, or one with a unit)
  binds to the alias nearest it in its sentence.
- **Belongs to another row:** it fails with "5.52% is bound to XLK but belongs
  to QQQ".
- **In the row under a field of the wrong kind:** it fails with "1.6 is bound to
  JPY futures but is its four_week_change_z (a z), not a share of open
  interest". "Points of open interest" now asserts a share (a percent), so the
  true sentence "23.4 points of open interest" passes.
- **Left alone:**
  - a figure in no row (a spread between two series, say) goes to the plain
    audit;
  - a sentence naming no series is untouched.
- **The retry:** the failure feeds it through a new `THE BINDING RULE` in
  opener's `RULES`.

**Fixtures** (B):
- both of this morning's cases fail with the text above;
- XLK's own 7.70%, two figures each bound to the name nearest it, the share of
  open interest, and the z called a z all pass;
- "Stocks fell 5.52%" (no series named) is left to the plain audit;
- `validate_numeral_audit` (167/0) is unchanged.

### W8-3: meeting labels

**Where:**
- the prediction-market subject template "a {side} at the {meeting} meeting",
  where `{meeting}` was the month name;
- the W7 odds panel's label, "hold at the {ISO date} meeting";
- the writer, which joined the month with the polished date: "the December
  9 Dec meeting".

**What changed:**
- `readability.meeting_name` makes "9 December", and "17 March 2027" when the
  year is not the edition's. `stack.market_subject` and the W7 label use it.
- `polish` (which every edition string passes through) rewrites any dated
  meeting in prose into the one template: "the December 9 Dec meeting" becomes
  "the 9 December meeting", "the March 17 Mar 2027 meeting" becomes "the 17
  March 2027 meeting", and "the December 9 meeting" becomes "the 9 December
  meeting".
- An undated "the December meeting" is left as written.
- `validate_prediction_markets`' pinned sentence is re-pinned to "the 28 October
  meeting" (52/0).

**Fixtures:** C.

### W8-5: the implied move's expiry

**Where:** `ahead.implied_move`, which took the first expiry *on or after* the
report date.

**What changed:** `ahead.straddle_expiry`.
- When the release time is unknown or after the close, it is the first expiry
  **strictly after** the event date.
- The event date's own expiry serves only before the open: "before the open",
  "pre-market", BMO, or a time before 09:30.
- `earnings_row` passes the row's time.
- The technical appendix row now reads "to the first expiry strictly after the
  event date (the event date's own expiry only when the release is before the
  open)".

**Fixtures** (D):
- META on Wed 21 Oct after the close, on an expiry day: 23 Oct;
- an unknown time and 16:05: 23 Oct;
- before the open and 07:00: 21 Oct;
- end to end on a fixture chain, "implied move ±5.7% (straddle to 2026-10-23)".

`validate_weekly_calendar`'s NVDA case reports before its expiry, so it is
unchanged (left to CI).

### W8-6: the "Why it matters" clause

**Where:** `config/weekly_ahead.yaml`'s `earnings_mega` channel carried the
AI-capex clause for every index-weight leader, TSLA included.

**What changed:**
- The channel is now the plain clause, and the class carries an `ai_clause`.
- `ahead.why_of` appends it only for an AI name. The names are read from
  `config/ai_buckets.yaml` when present (it is not on this branch), else from
  `earnings.ai_names` in the Weekly's own config: the forward-EPS block's nine
  (`config/ai_fcf.yaml`), with GOOG beside GOOGL.

**Fixtures** (E):
- TSLA gets the plain clause, NVDA the AI clause;
- the list matches the forward-EPS block's;
- an `ai_buckets.yaml` in a fixture repo is read first.

### W8-8: the short-interest change column

**Where:** `stack._change`. weekly-fixes-7 kept two places below one, but a
change of 1 or more printed at none ("−1").

**What changed:**
- A series may declare its level's decimals (`dp`). Days to cover declares two,
  in the Weekly's Positioning and in the close.
- So −1.27 prints "−1.27", −0.12 prints "−0.12", and a change rounding to zero
  prints "unch", as weekly-fixes-7's signed-zero rule.

**Fixture:** F.

### W8-9: future-dated as-of

**Where:** `weekly_stack.change_over` read IORB's row dated 19 Oct, its
effective day, into the edition of 16 Oct.

**What changed:**
- A new registry map, `forward_dated` (`metrics_registry.yaml`, read by
  `derived.forward_dated`), declares IORB with its reason.
- `change_over` reads an observation dated after the edition's session only for
  a declared series, and marks it `effective`. The row's cell and its item then
  print "effective 19 Oct" (`asof_cell`, `window`).
- Any other series is read at its newest observation on or before the session.
- The edition's session is the last trading session on or before the cutoff's
  Eastern date (Sunday 18 Oct gives Friday 16 Oct).

**Fixtures** (G):
- IORB dated 19 Oct prints "effective 19 Oct";
- an undeclared SOFR row dated 19 Oct is not read, and the 16 Oct row is;
- every forward-dated key is registered and carries its reason.

### W8-13: the buybacks table

**Where:** `batch3.buyback_operations` read DGS30 only, and FRED's leg lags a
session, so the newest operation printed "not yet stored".

**What changed:**
- The tape's 30-year (`yfinance.mkt_tyx`, config `thirty_year_tape`) comes
  first, and DGS30 only where the tape has no point. This is weekly-fixes-7's
  rule for the 10-year.
- The cell names its source and its date, "+5.0 bp (Yahoo Finance, 15 Oct)", and
  the table note says so in words, with no symbol string.
- `validate_batch3_a`'s pinned row now reads "+5.0 bp (FRED, 11 Sep)": its
  fixture has no tape (60/0).

**Fixtures:** H.

## The gates, locally, one at a time

| Gate | Result |
|---|---|
| `tools/validate_weekly_fixes_8.py` (new, in the Makefile) | **57 passed, 0 failed** (groups A to I above; I: no model client built, no network import in the retry module) |
| `tools/validate_audit_fixes.py` (the writer's gate, re-pinned: withheld after its one revision, "attempt 1 of 2" and "YOUR DRAFT:", two attempts at every cadence) | **73 passed, 0 failed** |
| `tools/validate_weekly_opener.py` (the précis: two attempts, "attempt 1 of 2") | **46 passed, 0 failed** |
| `tools/validate_numeral_audit.py` (the audit changed) | **167 passed, 0 failed** |
| `tools/validate_prediction_markets.py` (the subject re-pinned) | **52 passed, 0 failed** |
| `tools/validate_batch3_a.py` (the buyback row re-pinned) | **60 passed, 0 failed** |
| `tools/check_registry.py`, `tools/check_library.py` | OK; 0 failures, 0 warnings |

**Left to CI:**
- `validate_weekly_stack`, `validate_weekly_complete`, `validate_weekly_calendar`
  and `validate_daily_close`, which render. Their fake prose now also passes
  through the binding.
- Every other gate.

No gate reads the live store, fetches or calls a model, and nothing rendered a
PDF locally. CLAUDE.md's count is now seventy-seven code gates (seventy-four
Python).

## CI

Read once, with `gh run list --branch weekly-fixes-8 --limit 3`. The numbers are
in the session's closing report, and in the commit after these notes if a fix is
needed.

## The weekly-fixes-9 queue (chain #2, Tuesday; not built here)

- **W8-3b, the flip's words.** "The gamma flip at 774.67 held" while Wed, Thu and
  Fri closed below it. 774.67 in the named levels sits against 775.30 in the
  mechanics table. Either one flip per session, or both labelled by capture
  time.
- **W8-7, the Book B scanner.**
  - No breakout scans on instruments without volume, or on managed-currency
    pairs (TRY=X, IDR=X).
  - No RS against SPY for FX.
  - A floor on the invalidation distance (half an ATR or 0.5% of price) before R
    is computed: the EURUSD "7.9R" case.
- **W8-10:** the voices table's "10-year: not stored".
- **W8-11:** the crypto basket's empty market-cap column.
- **W8-12:** registry keys in the detail tables ("mkt eido volume", "jgb 10y").

(The paste numbers the flip's words W8-3; this branch's W8-3 is the meeting
labels, also the paste's. The queue's item keeps its fault text.)

## Files shared with the open branches, for Tuesday's stitch

A trial merge (`git merge-tree`, which writes nothing) of this tip against
chain #2's tips (`lenses-group-b`, `st-t3-calib`, `gtm-core-2`, `vol-event-52`,
`el-4-6`, `st-r4-tranche-1b`) conflicts in four files, with these resolutions:

| File | Resolution |
|---|---|
| `daily_cascade/close_report.py`, `daily_cascade/morning_anchor.py` | Keep chain #2's `with model_meter.scope(report=..., run_id=...)` and call `audit_retry.generate(np_, report="close" / "anchor", ...)` inside it, so the revision is metered too |
| `tools/validate_batch3_a.py` | This branch's expected cell, "+5.0 bp (FRED, 11 Sep)" |
| `CLAUDE.md` | The gate counts: recompute at the stitch |

Every other file merges clean. These are the ones chain #2 also edits, so the
stitch knows where to look:
- the writer: `stack_prose.py`, `precis.py`, `narrative.py`, `opener.py`;
- `altdata/numeral_audit.py`;
- `readability.py`, `stack.py`, `weekly_stack.py`, `ahead.py`;
- `batch3.py` and `batch3_block.py`;
- `config/reporting_stack.yaml`, `config/weekly_ahead.yaml`,
  `config/batch3_tranche_a.yaml`;
- `metrics_registry.yaml`, `altdata/derived.py`;
- `Makefile`.

**Chain #2's Weekly panels (dealer, crypto, lab, GTM) are not touched.**
`weekly_stack.py`'s hunks are Plumbing's `change_over` and its row, the FINRA
`dp`, the W7 meeting label and one argument. Chain #2's own Weekly fixtures will
meet the binding audit at the stitch: a fake draft that binds a figure to the
wrong series now withholds there too, by design.

## Needs you

1. **The retry bound.** The paste's one retry withdraws the Weekly's and the
   précis's three attempts (W-1.3c item 6). I applied it everywhere this writer
   runs. The Monthly v2 fallback's own three-attempt loop (`monthly_macro/prose.py`)
   is a different writer and is unchanged. Say if it should take the revision
   too.
2. **The binding is conservative on purpose.** A figure that is in no row (a
   spread or difference between two series) is left to the plain audit, so
   "XLK lagged QQQ by 2.18 points" is not refused when 2.18 is in no row.
   Tighten it only if you want such a figure to need a row of its own.
3. **The meeting template rewrites prose in `polish`**, as it already rewrites
   dates and minus signs. "The December meeting" without a date is left as
   written.
4. **W8-6's list** is the Weekly's own until `config/ai_buckets.yaml` exists
   (session A's, if it lands); the code reads that file first.
5. **Forward-dated series:** only IORB is declared. Another series dated by its
   effective day needs one line in `forward_dated`, with its reason.
