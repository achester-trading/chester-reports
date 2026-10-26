# B76 -- trend-signal breadth (Batch 16 item 89(b)) -- notes

*Session B, 26 Oct 2026. Branch `b76-trend-breadth` from `origin/chain-7-main` at
`dfa14a54` (its tip). Code, branch-only; merges with chain-8 on 2 Nov. Filed item
89(b), written as the triage chat's 82(b) in
`docs/change-order-signal-triage-round-7-2026-10-26.md`; ruled 26 Oct 2026. The
paste is `docs/pastes/B76.md`, committed first.*

**The order itself was not on this base or attached to this session.** The build
follows the paste, which carries the spec in full. If entry 82 or cross-item note
2 says anything the paste does not, that governs; see needs-you 5.

## The signal (declared, not fitted)

`config/trend_breadth.yaml` (trend-breadth-v1); `altdata/trend_breadth.py`.

- **The sign** at lookback L (20, 60, 120 and 250 sessions), on a market's session
  t: +1 when the close on t is above the mean of its last L closes (t included),
  -1 below, 0 equal. A rate is read as its yield, a currency pair as quoted. Each
  market keeps its own sessions.
- **The state:**
  - **trending** when all four signs agree and none is 0;
  - **reversing** when the 20-session sign is non-zero, opposite the 250-session
    one, and changed on one of the market's last five sessions (t included);
  - **mixed** otherwise;
  - **insufficient history** while a lookback lacks L closes.
- **The flips:** sign changes across markets and lookbacks observed in the seven
  calendar days to the day.
- **The reversing share:** markets reversing over markets carrying a state, in
  percent. A market carries a state on a day when its latest close is at most
  seven calendar days old.
- **Point-in-time:** a sign is available when the latest close in its window is
  (the window's maximum available_at); the share and flips when their latest
  input is.

**Stored** (source `calc`): `trend.<market>.<lookback>` (64 keys, the bulk block
`trend_breadth_signs`, `members_from: altdata.trend_breadth.SIGN_KEYS`),
`trend.flips_week` and `trend.reversing_share`. Registered with
`trigger_eligible: false`, barred from the market-state object
(`market_state_barred`, `trend.*`), and the signs are lens-excluded as signs.

## The markets

The paste names fifteen and lists sixteen rows, AUD/USD "if stored". Every row
reads a key the registry already has; no symbol is added (D33). The first key in
a row that holds rows as of the cutoff leads.

| Market | Stored key(s), in order | Laptop store |
|---|---|---|
| UST 2y / 10y / 30y | `fred.yield_2y` / `_10y` / `_30y` | held (to 28 May 2026) |
| Bund 10y | `bbk.bund_10y` (the Bundesbank fitted curve) | not stored |
| JGB 10y | `mof.jgb_10y` | not stored |
| SOFR | `fred.sofr` | not stored |
| ES, NQ | `overnight.es_prior_settle` / `nq_prior_settle` (instruments ES=F, NQ=F: the 16:00 ET settle the 06:45 overnight writer stores) | not stored |
| Copper, oil, gold | `yfinance.mkt_copper_front`, `_wti_front`, `_gold_front` | not stored |
| Dollar index | `yfinance.mkt_dxy` | not stored |
| EUR/USD | `yfinance.mkt_eurusd`, then `fred.usd_eur` (H.10) | held, via H.10 |
| USD/JPY | `yfinance.mkt_usdjpy`, then `fred.usd_jpy` (H.10) | held, via H.10 |
| AUD/USD | `fred.usd_aud` (DEXUSAL, the FX scan) | not stored |
| BTC | `yfinance.mkt_btc_usd` | held |

**No market lacks a registered key**, so no row is a gap by the registry; on the
box most should be held. A market whose key holds no rows prints "not stored",
and the share prints "of n held", n reduced. ES and NQ's history starts only when
the overnight writer started, since it stores one settle a morning; it is the one
stored daily front for them (the bars table is not keyed).

## What prints

- **The table** goes in the Weekly's Positioning & flows, and the Monthly reads the
  same table (`daily_cascade/trend_breadth_block.py`, hooked in
  `weekly_stack.positioning_subsections` at the weekly and monthly cadences).
  - Columns: each market's four signs and its state, with the as-of day.
  - Lines: the reversing share "k of n held", the trending count, the week's
    flips, the not-stored list, and the window and n.
  - No paragraph, no chart, nothing in the daily close.
  - Before the backfill it prints "not computed yet".
- **`validate_monthly_stack` N5** now lets the table through as a sub-section
  without a written read, and checks that the Monthly carries it.

## The ledger

`docs/ledgers/trend-breadth-2026-10-26.md`. The pre-registration is the block
between `<!-- prereg:begin -->` and `<!-- prereg:end -->`, committed alone at
`e635b32`. Its SHA-256 (LF bytes, markers included) is
`9347d6686bc2506dfbe37bb4d25e3d2c7a88e0fcd92527f961667498d34ea976`; it is printed
beneath the block and recorded in `config/trend_breadth.yaml`
`ledger.prereg_sha256`.

**The rule:**
- **The sample:** each ISO week's last S&P 500 session with at least five markets
  carrying a state.
- **The groups:** a week is high when the reversing share is at or above 20.0%.
- **The statistic:** the S&P 500's mean +20 change in high weeks less rest, with
  Welch's t.
- **INSUFFICIENT** when either group has fewer than 30 weeks. **PASS** at 30 a
  side with |t| of at least 2.0 and one sign in both halves. **FAIL** otherwise.
- The S&P 500 at +5, and the Nasdaq-100 (through QQQ) at +5 and +20, print
  beside it, descriptive only.
- **Rights:** none until Audit #5 or a sitting reads it.

**Honest order of work.** The rule's numbers were set in the config before the
module first ran. The block transcribes them unchanged and was committed before
the module, but the module was drafted, and run once on the laptop, before the
block was written.

**The laptop first edition: FAIL.**
- **n:** 163 weeks, 21 Apr 2023 to 29 May 2026.
- **Markets:** 6 of 16 held.
- **The rule's cell:** 43 high weeks against 120, a difference of +0.16 pp, t
  +0.23, and the halves disagree (+0.66 / -0.21).

## The laptop's reversing share (caveat)

The laptop store is partial: last written 15 Oct, its FRED legs end in May, and 6
of 16 markets are held.
- **On 29 May 2026,** its last day with five or more markets carrying a state, the
  reversing share is **33% (2 of 6)**: the 10- and 30-year reversing, the 2-year,
  EUR/USD and USD/JPY trending, BTC mixed.
- **Today** no market's close is within seven days, so the laptop has no reading.
- This is not the box's figure. The box's first reading comes from the backfill.

## Box commands (the operator's, in order)

    # 1. the backfill's dry run: counts, writes nothing
    python -m altdata.trend_breadth backfill --dry-run
    # 2. the backfill
    python -m altdata.trend_breadth backfill
    # 3. the table, read-only
    python -m altdata.trend_breadth show
    # 4. the box's ledger edition, read-only (a new dated edition, never an edit of the block)
    python -m altdata.trend_breadth ledger --label "box edition"

After that, the features pass (`altdata/market_features.compute`, after ST-5's)
computes the last 30 days each run, never fatally. It never runs the history by
itself, so step 2 stays the operator's. No new unit, timer or fetch.

## Counts and shared files

- **The gate count is updated by hand.** `tools/stitch_counts.py` is not on this
  base. CLAUDE.md's gate sentence now reads one hundred and forty-one code gates,
  one hundred and thirty-eight Python; `validate_audit_3a` holds it to the
  Makefile. The new CLAUDE.md paragraph itself carries no counts.
- **Shared files touched:**
  - `metrics_registry.yaml`: new keys, plus the `trend_breadth` mechanism group
    (needs-you 4), the bar and the lens exclusion;
  - `Makefile`: the gate;
  - `config/catalogue_commands.yaml`: the module's line;
  - `tools/validate_audit_3a.py`: the new block in `NEW_KEY_BLOCKS`;
  - `tools/validate_monthly_stack.py`: N5;
  - the Master Guide's Table 7a: one row, with the HTML edition rebuilt.
- **`config/stack_hooks/` is not on this base**, so the hook is a call in
  `weekly_stack.py`, as B75's gold section is.

## Local runs

- **The new gate:** `validate_trend_breadth` (42 checks).
- **The paste's list:** validate_weekly_complete, validate_monthly_stack,
  check_registry and check_library.
- **Also:** validate_weekly_stack, validate_lenses, validate_gates,
  validate_regime, validate_audit_3a, check_master_guide, validate_volume_profile
  and validate_st_t2_rates.

All pass.

## Needs you

1. **Sixteen or fifteen:** the paste lists AUD/USD "if stored" beside fifteen. It
   is a sixteenth row, read from `fred.usd_aud`. Keep it, or drop it.
2. **ES and NQ** read the overnight writer's 16:00 ET prior settles, the one
   stored daily front for them. Accept that, or name another stored series.
3. **The Nasdaq-100 outcome** reads QQQ, since no index key is stored, as B75's
   gold lens does. Accept that.
4. **The registry vocabulary** gained one mechanism group, `trend_breadth`, beyond
   "new keys only". Accept it, or name an existing group.
5. **The order's text:** it was not available to this session. If entry 82 states
   a pass rule or market list that differs from the paste's, it governs. The fix
   is a new dated registration, never an edit of this block.

- **CI:** in progress at `618e825`, run 40383686285. The next paste on this branch reads it once.
