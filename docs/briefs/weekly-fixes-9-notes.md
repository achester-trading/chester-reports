# weekly-fixes-9: the rest of the first live Weekly's faults (session notes, 18 Oct 2026)

**This branch, `weekly-fixes-9`, is cut from the tip of `weekly-fixes-8` after
the stitch (`e202312`): Monday's line.** It holds:
1. the chain of nine;
2. `weekly-fixes-7`;
3. `writer-fixes-1`;
4. `weekly-fixes-8`;
5. this branch's commits.

**It merges on Monday after `weekly-fixes-8` if it is green by Monday
afternoon; otherwise it waits for Tuesday's stitch into chain #2.** Monday's
whole order is in `weekly-fixes-8-notes.md` (ruling 4 of 18 Oct).

Branch only: pushed, not merged, not deployed, nothing run on the box. No unit
was enabled, started or reconfigured. Session A's branches and chester-meme were
not touched; `st-t3-calib` was read only, for the trial merge below.

| Part | Commit |
|---|---|
| The fixes and the gate | `459cdb6` |
| These notes | the commit after |

## What I read first

- `weekly-fixes-8-notes.md`'s queue;
- the Tape's level words (`levels.status_of`, `stack.tape_section`'s
  `level_status`) and the named-levels table (`weekly_sections.tape_table`);
- the mechanics table's flip source (`weekly_sections.dealer_week`: each
  session's card, `flip_morning`);
- the Book B scanner (`altdata/book_b_scanner.py`, book-b-scanner-v1: the
  universe, `detect`, `rs_percentile`, `draft`, `parameters_line`) and its block
  (`daily_cascade/book_b.py`);
- the 10-year-top voices table (`altdata/rates_shape.py` `adjudicate`);
- the crypto basket's market-cap field (`altdata/crypto_basket.py`, its writer
  `altdata/sources/llama.py`);
- the detail tables' label source (`altdata/labels.metric`,
  `config/display_labels.yaml`), the Security Master, and the registry;
- CLAUDE.md.

## The faults, where each was, what changed, its fixture

### W8-3: the flip's words, and one flip per session

**Where:**
- **The words.** The Tape's "held" was `levels.status_of` on the last
  session's bar alone: Friday's high touched the flip and Friday closed below
  it. The writer then read that as the week's word, while Wednesday, Thursday
  and Friday all closed below.
- **The values.** The Tape's flip (774.67) is the session's **close capture**,
  the computed profile from the end-of-day chain. Mechanics' Friday flip
  (775.30) is that **morning's** capture. They are two values from two
  captures, and neither was labelled.

**What changed:**
- `weekly_sections.flip_words` reads Mechanics' close-vs-flip column, never the
  model:
  - "crossed on Wed 14 Oct, below since" (the last crossing, and the side every
    close since has kept);
  - "crossed 3 times in the week; last on ..." for a chop across it;
  - "held" only when touched (a session's range within the tolerance of that
    morning's flip) and never closed on the other side;
  - "untested" otherwise.
- `apply_flip_words` writes the word into the Tape's `level_status`, so the
  writer's existing level audit refuses "the gamma flip ... held" against a
  crossed week. "Crossed" passes. The named-levels table's note prints the
  words.
- **Both values print, each labelled with its capture:** "Gamma flip (close
  capture)" in the named levels, "Flip (morning capture)" in Mechanics.
  `validate_weekly_edits`' header pin is updated (left to CI: it renders).

**Fixtures** (`validate_weekly_fixes_9` A):
- Mon and Tue above, Wed to Fri below, prints "crossed on Wed 14 Oct, below
  since";
- the chop, held, untested, and no column at all;
- the Tape's status takes the words;
- the writer's "held" is refused while "crossed" passes;
- both headers are labelled.

### W8-7: the Book B scanner

**Where:**
- `detect` scanned breakouts on every instrument, TRY=X and IDR=X among them,
  and fired an "unconfirmed" breakout with no stored volume.
- `rs_percentile` read RS against SPY for FX.
- `draft` computed R off any invalidation distance: EURUSD's "7.9R".

**What changed:**
- **(a)** `breakout_skip` covers an instrument with no stored volume and any
  `=X` pair (managed currencies among them). Neither is scanned by the breakout
  template; the reclaim and failed-breakdown templates are unchanged.
  - The scan's `skipped["breakout_not_scanned"]` carries each with its reason.
  - The block prints "Not scanned for breakouts: TRY=X: a currency pair -- ...".
  - An FX pair's RS reads "relative strength not read (a currency pair: no RS
    against SPY)".
- **(b)** R is computed only when the invalidation lies at least max(0.5 ATR,
  0.5% of price) from the entry (`config/book_b_scanner.yaml` `r_floor_atr`,
  `r_floor_pct`, session-set). Below the floor the candidate prints "R not
  computed: invalidation too near (within ..., the larger of half an ATR and
  0.5% of price)".
- **The "Pivots as set" line** prints both changes with the date: "Changed 18
  Oct 2026: ...".

**Fixtures:**
- `validate_weekly_fixes_9` B:
  - a TRY=X breakout is not scanned, with the reason;
  - a stock without volume is not scanned, and one with volume is;
  - no RS for FX;
  - the EURUSD fixture: invalidation 0.0006 from the entry, against a floor of
    0.0054 (0.5% of price), prints no R where 13.8R would have printed;
  - beyond the floor, 1.95R prints;
  - the Pivots line and the block's note.
- `validate_book_b_scanner`'s fixture gave its breakout names no volume, the
  old "unconfirmed" rule. SPY and QQQ now carry a volume series, 3x on their
  crossing session. The "no volume" check is now the new rule, tested on a copy
  with the volume removed. The `strict` check now runs on the reclaim template,
  which still fires "unconfirmed". **63 passed, 0 failed.**

### W8-10: the voices table's measure names

**Where:** `rates_shape.adjudicate`'s chop-range voice read the 10-year from the
inflation anchor. The anchor goes absent for want of ten years of CPI, so
"10-year: not stored" printed while the tape carried the 10-year.

**What changed:**
- The chop-range test needs the level alone. Where the anchor is absent it
  reads the newest of FRED's 10-year and the tape's (`ten_year_level`), and the
  measure names the source and date: "10-year 4.12% (Yahoo Finance,
  2026-10-16)".
- With neither stored, the measure names what is missing and for which test:
  "the 10-year's latest close, for the 5-5.5% chop-range test: no 10-year
  (FRED's or the tape's) at the cutoff".
- "Not stored" is never printed for a series the edition prints.

**Fixtures:** C; `validate_rates_anchors` 23/0.

### W8-11: the crypto basket's market cap

**What I found:**
- **The mapping is right.** One read of DefiLlama's coin service (`POST
  coins.llama.fi/mcaps` and `/prices/current`, the twelve configured
  `coingecko:` ids; nothing stored) answers every id in exactly the shape
  `parse_coins` reads.
- **The write is right too:** one row a day, dated that UTC day, from the 17:25
  ET basket run.
- So the twelve dashes mean no `llama.mcap_*` row dated on or before the
  Weekly's Friday was in the box's store. That is a box-side gap (the basket
  timer, or the run's log), which I cannot see from here.

**What changed:**
- Per the paste's fallback, the column is dropped from the Weekly's and the
  Monthly's tables until a cap is stored, with one line: "Market cap: not stored
  for any name yet (DefiLlama's coin service, written by the 17:25 ET basket
  run); the column prints once a cap is stored."
- The day one name has a cap, the column returns.

**Fixtures** (D):
- a price stored and no cap: the column is dropped, with the line;
- nothing stored: weekly-fixes-7's one-line block;
- a stored cap prints, and the column stays.

`validate_crypto_basket` is 93/0.

**For Ari, read-only:**
- `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.catalogue show llama.mcap_aave | head -30'`
- `ssh vps 'systemctl --user list-timers | grep crypto-basket'`
- `ssh vps 'tail -60 ~/logs/crypto-basket-2026-10.log'` (the wrapper's `LOG`,
  unless `CHESTER_LOG_DIR` moves it)

### W8-12: display names in the detail tables

**Where:** `labels.metric` fell back to `plain(key)`, which printed "mkt eido
volume", "mkt vvix", "jgb 10y" and "shares outstanding (SQQQ)".

**What changed** (`labels.derived_label`, between the declared labels and the
plain form):
- a FRED key takes its series description from `altdata/config.py`;
- a Yahoo key takes the Security Master's name, else the tape's own label, else
  an `=X` pair read as "EUR/CHF";
- with its ticker only where the ticker is a plain one, so no `^` or `=X` symbol
  prints (weekly-fixes-7 item 11);
- with the companion's word: volume, high, low, open.

Three keys have no name anywhere in the repo, so `config/display_labels.yaml`
declares them:
- `mof.jgb_10y` "Japan 10-year (JGB)";
- `yfinance.mkt_vvix` "the VVIX (the VIX's own volatility)";
- `levetf.shares_outstanding` "leveraged-ETF shares outstanding".

So "mkt eido volume" becomes "iShares MSCI Indonesia ETF (EIDO) volume".

**The gate.** `validate_weekly_complete` group N greps every detail table's cells
in the fixture Weekly for a registry key or a key made plain ("mkt ...", "jgb
10y"): 90 passed, 0 failed. `validate_weekly_fixes_9` E holds the six names.

### Ruling 1: the Monthly v2 fallback's retry, not built here

**It needs about 1.5 hours, so it is listed for the Monthly's post-dry-run
fixes.**
- `monthly_macro/prose.py` runs three attempts (`ATTEMPTS = 3`).
- `validate_monthly_stack` pins three attempts in six places (lines 1607, 1935,
  1989, 2012, 2453, 2565), and some of its fake models publish only on a third
  draft.
- That gate renders, so it is CI-only here, and each pin's fixture would be
  re-read and re-run through CI.

**The change itself is small:**
- `ATTEMPTS` comes from `audit_retry`;
- `retry_prompt` appends `audit_retry.revision_note`'s failing span and draft
  beside its own vocabulary, figure and cap lines;
- the six pins become two attempts.

### Ruling 2: the technical appendix's audit note

`config/reporting_stack.yaml` `technical_appendix` gains a "Numeral audit" row:
- every figure is one the section's data carries;
- in a sentence naming a series, each figure binds to the series named nearest
  before it in its clause, and must be that series' own, in the unit its column
  states;
- **"Deliberately conservative: a figure in no series' row (a spread between two
  series, say) is left to the plain check"**;
- a draft that fails is revised once, then withheld with its reason.

**Fixture:** F.

## The gates, locally, one at a time

| Gate | Result |
|---|---|
| `tools/validate_weekly_fixes_9.py` (new, in the Makefile) | **37 passed, 0 failed** |
| `tools/validate_book_b_scanner.py` (fixture given volume; two checks to the new rule) | **63 passed, 0 failed** |
| `tools/validate_weekly_complete.py` (group N added) | **90 passed, 0 failed** |
| `tools/validate_rates_anchors.py` | **23 passed, 0 failed** |
| `tools/validate_crypto_basket.py`, `validate_prices.py`, `validate_security_master.py` | **93/0, 101/0, 90/0** |
| `tools/validate_audit_3a.py` (the count line) | **84 passed, 0 failed** |
| `tools/check_registry.py`, `tools/check_library.py` | OK; 0 failures, 0 warnings |

**Left to CI:**
- `validate_weekly_edits` (the header pin), `validate_weekly_stack`,
  `validate_readability` and the other rendering gates;
- everything else.

No gate reads the live store, fetches or calls a model, and nothing rendered a
PDF. CLAUDE.md's count is now eighty-eight code gates (eighty-five Python) and
six data gates.

## CI

Each run read once, with `gh run list --branch weekly-fixes-9 --limit 3`.

| Run | Commit | Result |
|---|---|---|
| 39158278549 | `459cdb6` (the fixes) | **success, 96 of 96 jobs** (88 code gates, 6 data, enumerate and the roll-up) |
| 39158393033 | `e88a94e` (these notes) | **success, 96 of 96 jobs** |
| (the rulings) | the commit after | in the session's closing report |

## The rulings of 18 Oct on this report, as applied

1. **The FX floor.** A pair the scanner still reads (the free floats, EURUSD
   among them) takes half an ATR alone, with no percent leg. Equities and ETFs
   keep the larger of half an ATR and 0.5% of price.
   - The note says which: "half an ATR, a currency pair's floor".
   - The "Pivots as set" line says both floors.
   - **Fixture** (B): one invalidation distance, past half an ATR and inside
     0.5%, prints R for EURUSD and no R for a stock. EURUSD inside half an ATR
     prints no R.
2. **The two labelled flips stand.**
   - The session's level words and flags read the morning capture, as built.
   - The named level is the close capture, the next session's level. Its head
     now prints its time, "Gamma flip (close capture, Fri 16 Oct)".
   - The Tape's flip note says which is which.
   - **Fixture** (A): the dated head. `validate_weekly_edits`' pin accepts it
     (left to CI).
3. **The Monthly v2 fallback's retry** is listed for the Monthly's post-dry-run
   fixes, as above.

Locally: `validate_weekly_fixes_9` **39 passed, 0 failed**,
`validate_book_b_scanner` **63 passed, 0 failed**.

## Files shared with chain #2's open branches, for Tuesday's stitch

I ran a trial merge (`git merge-tree`, which writes nothing) of this tip against
chain #2's tips:
- `lenses-group-b` and `alpha-lab-3` conflict only on `CLAUDE.md`'s count line.
- **Session A's line** (`st-t3-calib`, `gtm-core-2`, `el-4-6`, `vol-event-52`,
  which carry one another) conflicts in five files:

| File | Resolution |
|---|---|
| `daily_cascade/weekly_sections.py` | Both sides add functions at the same place (this branch `flip_words` and `apply_flip_words`; chain #2 its own). Keep both |
| `daily_cascade/weekly_stack.py` | Keep this branch's `mech = ...` line before `built`, with chain #2's arguments: `mech = mechanics_week(st, sessions, now, wis, cfg, computed_dir=p.get("computed_dir"), ending=ending)`, then `"mechanics": mech` |
| `tools/validate_weekly_complete.py` | Keep both: group N's check, then chain #2's `group_m()` call |
| `tools/validate_batch3_a.py` | weekly-fixes-7's check (the source and date, no branch name: item 11) against chain #2's older text; keep this branch's check and chain #2's `group_b_daily` with its helpers |
| `CLAUDE.md` | The count line: recompute at the stitch |

`st-r4-tranche-1b` also conflicts in `altdata/batch3.py`, which is W8-13's
30-year leg from `weekly-fixes-8`. Keep the tape-first `leg()` and add that
branch's own change around it.

The other files this branch touches that chain #2 also edits:
- `daily_cascade/book_b.py` and `altdata/book_b_scanner.py` (the dealer, crypto,
  lab and GTM panels are not touched);
- `altdata/crypto_basket.py`, `altdata/labels.py`, `altdata/rates_shape.py`;
- `config/book_b_scanner.yaml`, `config/display_labels.yaml`,
  `config/reporting_stack.yaml`;
- `Makefile`;
- `tools/validate_book_b_scanner.py` and `tools/validate_weekly_edits.py`.

## Needs you

1. **W8-11's box read** (above). The code and the mapping are right; the cap
   rows were not in the store on or before Friday. If the timer is running and
   the rows are there, the column returns at the next Weekly by itself.
2. **W8-7's floor on FX:** 0.5% of price is about 54 pips on EURUSD, so most FX
   reclaims will print no R. That is the ruling's number. Say if FX should have
   its own floor.
3. **Ruling 1's Monthly v2 retry**, about 1.5 hours, is listed for the
   Monthly's post-dry-run fixes.
4. **W8-3:** the Tape and Mechanics print two flip values, each labelled by
   capture, rather than one. One value per session would mean choosing a
   capture for both; say if you prefer the morning's everywhere.
