# The Market-State Object

**Status:** v1, built in Phase 2 (19 September 2026). Schema from
`chester-reports-audit-3.md` §K; recommendations O.5, O.6, O.12 and O.14.

One object per session day, computed by the close pass, stored as an observation
with `available_at`, read by every report. **Nothing else in the system computes a
regime.**

| Piece | Lives in |
|---|---|
| Standard derived forms | `altdata/derived.py` |
| The object | `regime.py` |
| The contradiction table | `contradictions.py` |
| Every rule, threshold and metric | `config/market_state.yaml` |
| The rendered block both anchors open on | `daily_cascade/state_block.py` |
| Gates | `tools/validate_derived.py`, `tools/validate_regime.py` |

---

## 1. Why one object

Before this, each report derived its own regime from whatever series it happened
to read. Two reports could disagree about the state of the market and there was no
way to tell that from two reports disagreeing about a number. Worse, a decision
recorded in the register carried no statement of the conditions it was taken
under, so a grade at its horizon could not be cut by regime — which is the cut
that matters most.

§K's rule is therefore absolute: **every report reads this object and only this
object for its regime content.** One writer, one reader interface, one version
stamp.

The close pass (`daily_cascade/close_report.py`) is the writer. The 07:00 morning
anchor calls `regime.latest()` and never recomputes: an anchor computing its own
object could disagree with the close report's, and then the system holds two
regimes with no way to say which one a decision was made under.

---

## 2. Standard derived forms

`derived_forms(metric_id, as_of, window=None)` returns, for one metric: `level`,
`delta_1d` / `delta_5d` / `delta_20d`, `rate_of_change`, own-history `percentile`,
`z_score`, an `extreme` flag, `confidence`, `n`, and the window it actually had.

### Delta semantics — the field is `units`, not `observation_type`

A change means three different things depending on the series:

| `units` | Delta is | Example |
|---|---|---|
| `%`, `percent`, `bps` | **basis points** | 10y 4.45 → 4.52 is **+7bp** |
| `$`, `price`, `idx`, `usd` | **percent of level** | SPY 640 → 646 is **+0.94%** |
| `K`, `B`, `M`, `count`, `ratio`, `hrs`, `days` | **raw** | claims 221K → 229K is **+8000** |

One formula for all three is wrong twice and plausible three times.

The Phase 2 change order named `observation_type` as the field carrying this. In
this repo that field's vocabulary is `observed | calculated | inferred` — it
records *how a number came to exist*, not what a change in it means. `units` is
the field that carries the semantics, and for the 59 FRED series it resolves
through the `fred_macro` bulk block to `altdata/config.py`'s own `units`. The
convention is written into `metrics_registry.yaml`'s schema header beside the
fields it reads.

A metric whose units are not in the table is treated as **raw and says so** in
`delta_unit_reason`; so is an unregistered metric id. A silent default here would
be the rule failing with no trace.

### Three more rules

- **As-of correct, always.** Every read goes through
  `ObservationStore.as_of()`, which filters on `available_at` and never on
  `observed_at`. Leakage is about when you *knew* something.
- **A delta whose lookback lands on the level's own observation is `None`, not
  zero.** Ask a monthly series for its 1-session change and zero would claim it
  was measured and did not move — which is how a quarterly series ends up
  reported as the calmest thing in the book.
- **Confidence is derived, never authored.** From staleness against
  `information_half_life` and from `n`. `derived_forms()` has no confidence
  argument, and the gate asserts the signature has none.

### Staleness allowance, and the confidence table

`until_next_release` has no fixed length — it resolves to the series' own cadence
rather than a guess:

| cadence | allowance |
|---|---|
| daily | 2 sessions (one session's grace: FRED posts next morning) |
| weekly | 8 |
| monthly | 32 |
| quarterly | 95 |

| | n ≥ 250 | n ≥ 60 | n ≥ 20 | n < 20 |
|---|---|---|---|---|
| fresh | high | med | med | low |
| stale (≤ 3× allowance) | med | med | med | low |
| very stale | low | low | low | low |

### Optional per-metric registry fields

- `derived_window_days` — own-history window. Absent means five years (1826
  days), which is §K's `percentile_5y`.
- `extreme_percentiles: [lo, hi]` — overrides the 5/95 extreme flag.

### The session-counting caveat

`altdata/session.py`'s holiday table covers **2026–2027** and the store reaches
back to 2022. Outside the covered years, session distances fall back to counting
weekdays, and every row stamps `session_basis` (`calendar`, `weekdays`, `mixed`,
or `same_session`) saying which was used. A silent fallback would be a number
nobody could check.

---

## 3. The object

```
market_state
  object, schema_version, config_version, session, as_of, computed_at,
  git_sha, config_path, derived_convention
  dials:      macro, vol, gamma
  dimensions: growth, inflation, rates, liquidity, credit, trend, breadth,
              volatility
  contradictions: [ ... seven rows ... ]
  absent_dimensions, open_contradictions, absent_contradictions,
  prior_objects_read
```

Each dimension carries `state`, `direction`, `rate_of_change`, `percentile`,
`confidence`, `horizon`, `supporting[]`, `contradicting`, `last_changed`, plus
`raw_state`, `pending_state` and `persistence` when it is mid-transition — and
every member's own level, percentile, z, extreme flag and staleness.

### How a dimension gets its state: bands on one primary

Each dimension declares an ordered list of members. **The first is the primary and
it alone sets the state**, through declared percentile bands. The others are
evidence: a member landing in the state's own band is `supporting`, one landing
elsewhere is `contradicting`.

This is deliberately **not** a 0–100 composite. A composite averages disagreement
away — it turns "credit is calm and equities are not" into a middling number,
which is precisely the information worth keeping. Here the disagreement survives
as a list of metric ids a reader can look up.

`polarity` (+1 / −1) maps a member onto the dimension's own scale, and each one
carries a `because` line in the config, because getting a polarity backwards
inverts a whole dimension. The two most invertible:

- a **wide** HY spread is *stressed* credit, so `fred.hy_oas` is −1;
- cash at the reverse repo facility is liquidity **not** in the system, so
  `fred.rrp` is −1.

### Persistence: states do not flap

A raw reading that disagrees with the published state must hold
`persistence_sessions` (default 2) consecutive session computations before the
published state moves. Until then the object carries the **old** state plus
`pending_state` and `pending_sessions` — the honest rendering of "it looks like it
is turning and has not turned yet".

### `contradicting` is never empty by omission

A dimension with no disagreeing member records the string `none found`, as a
positive claim. A reader can then tell "we looked and everything agreed" from
"nobody looked".

### An absent dimension says why

Three different absences, three different reasons: no series at all, no *fresh*
series (past `max_staleness_sessions`), or no registry entry. Never a faked state,
and never a stale state presented as a current one.

### Two clocks, and why they are not the same clock

- **Market data** is read at the session's own cutoff. The object contains only
  what was knowable that evening. This is the leak rule and it is absolute.
- **The object's memory of itself** — the persistence history — is read at the
  instant the object was computed (`computed_at`).

Conflating them is not a theoretical risk: the first backfill did it, and all 77
sessions reported "first object; published immediately", because each read its
predecessors at that day's evening cutoff and they had been written minutes
earlier in September. Persistence never engaged and the output looked entirely
reasonable.

The same distinction governs reading: `regime.latest(session_day=S)` does not
apply an `as_of` filter, because an object *about* S already contains only what
was knowable on S, and its `available_at` merely records when the system got round
to computing it.

### One object per session day

Stored under `registry_key` `market_state`, `observed_at` = the session,
`available_at` = the compute instant. A recompute of the same day is therefore a
**revision** of that day's object, not a second object: the as-of join returns the
latest revision, so readers always see one object per day and the earlier vintage
stays in the store as the audit trail
(`observations.vintages("market_state", day)`).

If two computes disagree, the second wins for every future reader. A recompute of
an earlier session can also change what a replay of a later one sees — that is a
real change rather than a flaw, and it means the history was edited.

---

## 4. Dimension → metric mapping (v1)

Primary first; polarity in brackets.

| Dimension | States | Members |
|---|---|---|
| growth | expanding / slowing / contracting | `fred.claims_4wk` (−1), `fred.housing_permits`, `fred.job_openings`, `fred.avg_wkly_hours` |
| inflation | rising / stable / falling | `fred.breakeven_10y`, `fred.breakeven_5y5y`, `fred.sticky_core`, `fred.wti` |
| rates | high / mid / low | `fred.yield_10y`, `fred.yield_2y`, `fred.yield_30y`, `fred.mortgage_30y` |
| liquidity | ample / neutral / tight | `fred.rrp` (−1), `fred.bank_reserves`, `fred.fed_balance`, `fred.nfci` (−1) |
| credit | easy / neutral / stressed | `fred.hy_oas` (−1), `fred.bb_oas` (−1), `fred.ccc_oas` (−1), `fred.ig_oas` (−1) |
| trend | up / flat / down | `mkt_spy` — **absent** |
| breadth | broad / mixed / narrow | `mkt_rsp_over_spy` — **absent** |
| volatility | elevated / normal / subdued | `fred.vix` (realized leg absent) |

### The dials

- **macro** — a declared lookup table over the `growth` and `inflation` states
  (`rates` is declared as an input and not yet used, which is visible rather than
  buried in a weighting). Phase 4 maps the eleven pillars onto the dials properly.
  Its catch-all applies only when the inputs *exist* and disagree: an object whose
  inputs are absent gets an absent dial, not `mixed`.
- **vol** — VIX **level** bands (absolute, because the point of a vol dial is that
  30 means something on its own), plus a realized/implied leg and a VX1/VX2/VX3
  term-structure leg that both report absent with their missing inputs named.
- **gamma** — the sign of dealer gamma, **read** from the pin log via
  `altdata/grader.py`'s `PriceSeries`. The pin log is the system's own record of
  what it saw at the close, so "read, never recompute" is literal.

---

## 5. Three dimensions are absent, and this is the gap to close

The Phase 2 order chose the eight dimensions "because the store already has daily
series for them". For five that is true.

- **trend and breadth need equity prices, and the store has none.**
  `altdata/sources/yfinance_source.py` declares 27 symbols including SPY and all
  eleven sector ETFs, and **nothing schedules it** — no timer, no unit, no CI job.
  `data_store/` holds 59 FRED series and not one price.
- **growth has no daily series either.** Its primary is initial claims (weekly),
  which is the fastest growth signal the store actually carries.
- **the volatility dimension is implied-only** for the same reason: realized
  volatility needs SPY closes.

Five of the six computable contradiction pairs have a leg that depends on those
prices, so **one row computes today** — `long_bond_vs_hy`, which happens to be the
pair the order itself calls the standing watch line.

Two further data facts bound what v1 can say:

- **The FRED store stops at 2026-05-28.** Nothing in the repo schedules a FRED
  pull; the series land when the Monthly runs. So for any recent session every
  dimension is past its staleness allowance and reports absent.
- **The FRED history has no real `available_at`.** All 20,372 migrated
  observations share `2026-05-30`, the CSV-to-SQLite migration instant, because
  the CSVs only ever carried `date` and `as_of`. An as-of-correct backfill
  therefore cannot reach behind that date; `regime range` reports the window it
  can support (2026-06-01 → the last session, 77 objects). ALFRED ingestion (O.16)
  is what widens it.

---

## 6. The contradiction table

Seven declared rows: six computed and one reserved.

| Row | Legs | Computes today |
|---|---|---|
| `price_vs_breadth` | trend, breadth | no — prices |
| `equities_vs_credit` | trend, credit | no — prices |
| `long_bond_vs_hy` | `fred.yield_30y`, `fred.hy_oas` | **yes** |
| `implied_vs_realized_vol` | `fred.vix`, realized | no — prices |
| `growth_vs_cyclicals` | growth, XLY/XLP | no — prices |
| `gamma_vs_trend` | gamma dial, trend | no — trend |
| `prediction_markets_vs_assets` | PM implied, trend | reserved: Part 27 v1 |

### The magnitude is the z of the gap, not the gap

    z_a(t) = (a(t) − mean(a)) / sd(a)          over the window
    gap(t) = polarity_a · z_a(t) − polarity_b · z_b(t)
    magnitude = (gap(last) − mean(gap)) / sd(gap)

So 2.0 means "these two are further apart than they have been 95% of the time" —
a claim about the relationship rather than about either level. A raw gap would fire
every day on two legs that normally sit far apart. Legs are aligned on **common
dates** first, or a weekly series against a daily one produces a gap series that
mostly measures which day it is.

A **dial pair** has no series: `gamma_vs_trend` compares a sign the exposure
engine wrote down against a trend state, so it is a state mismatch and its
magnitude is honestly `None`.

Rows open and close on the same persistence rule the dimensions use, `since` is
the session the divergence *began*, and a leg staler than the declared allowance
sends the row absent — a gap measured between two stale prints is not a divergence
today.

### The exception is report-only

At `exception_sessions` (5) an open row is an exception. The order asks for it to
be wired into the Phase 1 exceptions alert path "if one exists; otherwise
report-only and say so". **It does not exist**: `scripts/check_heartbeat_cron.sh`
sends the heartbeat and drift alerts through `scripts/send_smtp_alert.py`, and
nothing sends an exceptions alert. Every exception row therefore carries
`alert_path: report_only` and a note saying the branch belongs beside the drift
branch in that script.

---

## 7. What the anchors print

Both the 16:45 close report and the 07:00 morning anchor open on **WHAT CHANGED**,
rendered by the one shared module, in HTML and in the text fallback:

dimension state changes since the previous object · extreme flags set or cleared ·
dial moves · contradictions opened, closed or persisting with their days ·
coverage changes (a dimension going absent, or coming back) · **every magnitude
stamped with its percentile**.

Levels moved down the page (O.6). A level is the least informative thing on a page
read fast: it says where a series is, not that it moved, not whether the move is
unusual, and not whether anything else disagrees.

A quiet session prints "nothing changed" **positively**, so that a quiet session
and a broken comparison do not look the same.

`market_state`, the open contradiction rows and `what_changed` also travel in the
close narrative's payload — trimmed to the published states and their percentiles,
because the full object holds hundreds of intermediate figures and a narrative
given all of them can cite an intermediate as a headline. The numeral audit covers
them automatically, as payload figures like any other.

---

## 8. Guards

`tools/validate_derived.py` (36 seeded checks) and `tools/validate_regime.py`
(184) are both code gates in the Makefile's one list, so CI runs them.

The heartbeat gained **exit 10, `no_state_object`**: on a session day, the last
completed session must have an object. It reads with `regime show` rather than
computing one — a monitor that computed the object to check whether it exists
would create the thing it is testing for. It is ranked below the pipeline verdicts
and below drift, because a stale pipeline *explains* a missing object and
reporting the symptom over the cause sends the reader to the wrong place.

---

## 9. The v1 / v2 boundary

**v1 (this).** Eight dimensions, bands on one primary, three dials, six
contradiction pairs plus one reserved, persistence, absence with reasons, exact
replay.

**v2 is audit sub-phase 6f, gated on Phase 3.** Not started, and deliberately not
approximated here:

| v2 | Why not now |
|---|---|
| Sixteen dimensions | The other eight (positioning, sentiment, valuation, earnings, funding stress, geopolitical, tail, policy) need sources this repo does not ingest. |
| Transition probabilities per dial | A probability with no calibration series is a number with no error bar. Phase 3 built the Brier ledger; the dial calls have to accumulate before any of them can be scored. |
| Dial calibration | Requires dial state at *t* scored against the realized regime at *t+horizon*. The backfilled history is the record that makes it possible later; the grading is not built. |
| Tail families with Brier | §K's `tail_families[]`. The probability ledger exists (Phase 3) and holds no live tail probability. |
| `debt_cycle_branch` | §K's two mutually exclusive branches, architecture 31.2. Still listed as not-built in the close payload. |
| VIX term structure | Gated on the CFE Enhanced subscription; the dial names the store keys it needs. |

Two nearer-term items, both outside Phase 2's scope and both blocking more than
they cost:

1. **Schedule a price fetch.** `yfinance_source.py` exists and nothing runs it.
   That single gap accounts for two absent dimensions, the missing realized-vol
   leg, and five of six contradiction rows.
2. **Schedule a FRED pull, and ingest ALFRED vintages.** The first makes the five
   working dimensions current; the second gives the history a real `available_at`
   and lets the backfill reach back to 2022.
