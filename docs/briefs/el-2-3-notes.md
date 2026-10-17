# EL-2 and EL-3 — the cross-book roll-up made explicit; Book Z verified: build notes (12 Oct 2026)

Branch `el-2-3-rollup`, from the tip of `el-1-packets` (`3db3984`) so the packet
fields are present. Not merged. Built and checked against
`docs/change-order-enterprise-layer-2026-09-27.md`:
- §3.2 and §3.3;
- §8 rows EL-2 and EL-3;
- the Operating Doctrine §4.5 and Rule 16 (the heat rule).

The order, the Doctrine and the specifications are not edited.

Paper only: nothing here places or routes an order. No register write was made;
the gates write only their own temporary registers. Nothing on the box was
touched.

**Most of both items already existed.** Phase 5a and P5-B built them. This branch
finds the gaps against the order and the Doctrine, fills those, and writes the
gate the brief asked for.

## What was built

### EL-2 — the roll-up

**Already there:**
- `register/heat.py`'s view summed every open decision across Books A–D and every
  options expression:
  - beta-adjusted notional against SPY, computed from stored returns;
  - sector by look-through weights;
  - duration in dollars per 100 bp;
  - signed vega, by underlying.
- The limits were in `config/risk_limits.yaml` with their provenance, ratified
  2 Oct 2026 (sector 30%, vega 0.5%/pt, duration 5%/100 bp, net beta at the band
  top + 15).
- The gate at entry (`heat.gate`, called by `decide.py record` and `set-status`)
  answered in DTH §XIV's six words (`GATE_OUTCOMES`). It folded the verdict into
  `review_changed` (`GATE_TO_REVIEW`, `review_from_gate`) and held a non-approved
  active request at draft unless the operator's override was recorded.
- `tools/validate_enforce.py` group A already ran a four-packet test (NVDA C,
  QQQ B, NVDA A, short QQQ vol D).

**Added:**
1. **The Doctrine's heat cap and the correlated-once rule (§4.5, Rule 16).**
   Nothing summed open risk before; the view summed exposures only.
   - **`risk_usd`:** a new nullable column on `decisions`, added by the
     register's ALTER migration. It holds dollars from entry to invalidation, or
     an options expression's defined maximum loss. It is passed by
     `decide.py record --risk-usd` and carried forward by `set-status`.
   - **Heat:** the sum of `risk_usd` across Books B, C and D only. It is checked
     against `heat_max_pct: 6` (`source: doctrine`, `books: [B, C, D]`).
   - **The common factor:** each decision gets one. It is the dominant
     look-through sector when that sector carries at least
     `common_factor.min_weight` (0.5) of the instrument, else the instrument
     itself. So NVDA, XLK and QQQ (60% technology) are all `technology`, and
     SPY and IWM are their own.
   - **Clusters:** the heat-book decisions sharing a factor form one cluster.
     Its risk is summed gross, with no credit for an offsetting leg. The cluster
     is held to one position's limit, `cluster_max_pct: 1.5`.
     - The 1.5% is the Doctrine's exceptional tier per position. Applying it to
       a cluster is this session's reading of "one position for heat purposes",
       so it is marked **proposed**. The common-factor rule is proposed as well.
     - A cluster of one is the book's own sizing and is never breached by this
       rule.
   - **What the gate does:**
     - It resizes against heat and clusters by the same arithmetic as every
       other limit, at the largest share of the request that fits.
     - It **delays** a Book B, C or D decision that records no `risk_usd`,
       naming the missing input, as it already delayed a missing size, beta or
       vega.
     - Book A carries no heat and needs no `risk_usd`.
2. **The refusal names the concentrations.** Before this, the view listed its
   concentrations, but the gate's reasons named only the limit the candidate
   tipped. The fourth packet's refusal therefore said "vega" and never
   "technology". Every non-approve, non-delay verdict now appends each
   concentration of the view after the candidate:
   - sector, vega with its underlyings, net beta, heat;
   - each cluster, with its members.

   `decide.py` prints them and the decision stores them in `gate_detail`.
3. **A defect fixed on the way: rate instruments are classified by duration.** A
   Treasury fund (TLT, IEF, SHY) has a duration and no equity sector. The view
   counted the missing sector as a missing input, so **the gate delayed every
   rate decision**. A declared duration now stands in for a sector.
4. **The gate, `tools/validate_rollup.py`,** 31 checks, in the Makefile's list
   after `validate_enforce.py`.
   - **A — the specification's four packets:**
     - long NVDA (B);
     - long QQQ (A);
     - long NVDA again, via a call spread (C);
     - short Nasdaq vol, a QQQ iron condor (D).

     The verdicts are approve, approve, resize (46%: the room under technology),
     restructure. The fourth's refusal names three things: the technology
     concentration, the vega concentration with its underlyings, and the
     technology cluster `NVDA (B), NVDA (C), QQQ (D)` counted once.
   - **B — the limits are config:** every value and provenance is read from the
     file, and moving the vega, sector or cluster limit in a copy moves the
     verdict.
   - **C — the vocabulary:**
     - the six words, and their fold into `review_changed`;
     - every word reachable, and nothing else;
     - the register refusing words outside the vocabulary;
     - the fourth packet run through `decide.py record` on the gate's own
       register, printing the refusal and recording `gate_outcome restructure`
       and `review_changed restructured`, held at draft, with `risk_usd` stored.
   - **D — correlated positions counted once:**
     - the Doctrine's own example (two technology names in B plus a Nasdaq call
       spread in C) is one position and fits at 50%;
     - the same risk in three unrelated factors is three positions and is
       approved;
     - an offsetting short adds gross;
     - Book A sits outside heat;
     - five unrelated 4,000 risks breach the 18,000 cap, named as heat;
     - a missing `risk_usd` is a delay, and an open one is listed as missing
       rather than counted as zero;
     - a TLT decision is approved.

**The fixture change.** `validate_enforce.py`'s packets now carry a `risk_usd`
(2% of the notional, or 1,000 for an options expression). Its 48 checks and its
four-packet verdicts are unchanged.

### EL-3 — Book Z, verified against §3.3

**What EL-3 already had (P5-B), each item checked against §3.3:**

| §3.3 says | Already on main | Verdict |
|---|---|---|
| three ledgers: `cash`, `spy`, `sixty_forty` | `altdata/benchmark.py`, `LEDGERS` | as written |
| cash at DTB3, daily accrual | `fred.tbill_3m` = DTB3, pulled; rate × calendar days / 360, the previous session's rate | as written |
| SPY buy-and-hold from the start | units at the start's close, held; dividends to cash | as written |
| 60/40 SPY/AGG, rebalanced on the first session of each month; AGG in the registry | `WEIGHTS` 0.60/0.40; rebalanced at the first marked session of a new month; `AGG → mkt_agg` in the basket and registered | as written |
| marked at every 16:45 close pass | `scripts/run_daily_close.sh` runs `python -m altdata.benchmark mark` after the price pull, before the report | as written |
| `paper.benchmark` rows keyed (session, ledger) | `observed_at` = session, `instrument` = ledger; registered `revision_policy: never` | as written |
| start: the register's first packet date, or 1 Sep 2026 if earlier | `start_date()`: min(first packet, 2026-09-01) | as written |
| point-in-time, never recomputed from a later vintage | a held (session, ledger) is skipped forever; catch-up rows say `reconstructed`, the live session `ingest_instant` | as written |
| one line beside each book's paper equity, Weekly and Monthly | **Weekly:** `book:z`, the paper account's NAV against the three over one window (T2 ruling 1). **Monthly v2 fallback:** the line beside each book. **Stacked Monthly (the live edition): read into the payload, printed nowhere.** | **gap** |
| the gate | `tools/validate_benchmark.py`, 24 checks | kept, extended |

**Added:**
1. **The stacked Monthly prints the line.**
   - `monthly_macro/payload.py` now also reads `benchmark.book_line()` as of
     the Monthly's cutoff, the Weekly's figure over one window.
   - `monthly_macro/stack.py`'s book section prints it as an "Against Book Z"
     sub-section and carries it as the `book:z` item, the Weekly's id. When
     there is no mark, it prints "Book Z absent: <reason>".
   - Nothing is computed there; the marks stay the close pass's.
2. **Eight checks in the existing paper gate.** `validate_benchmark.py` goes
   from 24 to 32:
   - E: the stacked Monthly prints the line, carries the item, says "absent"
     with its reason, and reads the line as of its own cutoff;
   - F, §3.3 as written:
     - exactly the three ledgers and weights;
     - `fred.tbill_3m` is DTB3 and pulled;
     - the start cap;
     - the 60/40 rebalancing on Monday 3 Aug 2026, the first session of a month
       that opens on a Saturday.

**Not built (a gap in what the books have, not in Book Z):** Books A–D have no
paper-equity ledger of their own. All four trade one paper account, and nothing
attributes the account's equity to a book. Every report therefore prints Book Z
against the account's NAV, and each book's own equity line reads "not yet
sourced". Building per-book equity is a ledger, not a benchmark (see Needs you
4).

**Gates re-run here:**

| Gate | Result |
|---|---|
| `validate_rollup` (new) | 31/0 |
| `validate_enforce` | 48/0 |
| `validate_benchmark` | 32/0 (24 before) |
| `validate_register` | 171/0 (2 skipped, as before) |
| `validate_packets` | 37/0 |
| `validate_prices` | 81/0 |
| `validate_gates` | 31/0 |
| `validate_deploy` | 118/0 |
| `validate_weekly_stack` | 68/0 |
| `validate_weekly_complete` | 56/0 |
| `validate_grader` | 62/0 |
| `validate_monthly` | 350/0 (1 skipped) |
| `validate_monthly_stack` | 261/0 |
| `validate_figure_budget` | 79/0 |
| `validate_readability` | 63/0 |
| `validate_regime` | 404/0 |
| `check_library` | 0 failures |

`validate_monthly_store` is a data gate; it is NOT VALIDATED here and runs on the
box.

## What waits, and for what

- **The operator's next packets carry `--risk-usd`.** From the merge, a Book B,
  C or D decision recorded without it is delayed at the gate and held at draft,
  unless the operator records an override.
  - An existing Book B–D draft has no `risk_usd`, and `set-status` cannot add
    one, so its activation is delayed. Record a new decision instead, as EL-1
    does for an incomplete packet.
  - Open Book B–D decisions already on the register are listed as heat's
    missing input, never counted as zero.
- **Ratifying the two proposed entries** (`cluster_max_pct`, `common_factor`) is
  a Doctrine-monthly item. Until then the view prints the cluster limit as
  "PROPOSED, unratified", and the gate acts on it.
- **Book B's own heat rules**, also §4.5's: six open positions at most, and 4%
  total open risk with correlated positions counted once. They are not built:
  the brief asked for the cross-book roll-up. The cluster machinery here is what
  they would read.
- **Per-book paper equity** (Needs you 4).
- **Ent. §XVII's ablation question** is to be answered against Book Z "from then
  on". That is a Quarterly table, not built here.

## Choices made for the operator to overrule

1. **"Counted once at their common factor" is read as one position.** The
   cluster's risk is summed, gross, and held to one position's maximum risk, the
   Doctrine's 1.5% exceptional tier. The alternative readings:
   - net the cluster (credit for offsets);
   - count it once only for the position count.

   The Doctrine's own example and Rule 16's origin ("diversification across
   instruments is not diversification across risk") point to the gross sum.
2. **The common factor is the dominant look-through sector at ≥ 50%, else the
   instrument.** It is declared, not estimated from return correlations, so the
   verdict replays from config rather than moving with the data. The cost: SPY
   and QQQ, which correlate around 0.9, are different factors. Correlation
   between broad indices is net beta's job, which the Doctrine caps separately.
3. **A heat-book decision without `risk_usd` is delayed**, the existing rule for
   any missing input. Book A is exempt, as the Doctrine's heat is B–D.
4. **The stacked Monthly's line is the Weekly's**: the paper account's NAV
   against the three ledgers over one window, with the excess. It is not the
   bare benchmark returns the v2 fallback prints.
5. **A rate instrument's duration stands in for its sector.** This was a fix to
   existing behaviour, but it changes a verdict: TLT used to be delayed and is
   now approved inside the limits.

## Needs you

1. Read Doctrine §4.5's "correlated positions counted once at their common factor" as: the heat-book decisions sharing a factor are one position, their risk summed gross and held to one position's maximum (1.5%, `cluster_max_pct`, proposed)? yes / no
2. Ratify the common-factor rule (the dominant look-through sector at ≥ 50% of the instrument, else the instrument itself; `common_factor.min_weight: 0.5`, proposed)? yes / no
3. Require `--risk-usd` on every Book B, C and D decision, the gate delaying one without it, so heat can be summed (Book A exempt)? yes / no
4. Book Z prints against the paper account's NAV, because Books A–D share one account and no per-book paper equity exists: accept that for "beside each book's paper equity", or schedule a per-book equity ledger? accept / schedule
5. Merge order, inside windows: after `el-1-packets` (this branch is cut from it), on its own? yes / no
