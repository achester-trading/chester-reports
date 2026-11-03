# B106 notes: the clock audit

Paste B106 (`docs/pastes/B106.md`), 2 Nov 2026. Branch `b101-date-drift-gates`,
continued from `eb9688b4`. The rule is now in CLAUDE.md's gates paragraph: "A gate
pins its clock to its fixture's date. A gate that must read today says so in a
comment and names the day it will next need attention."

## How the inventory was taken, and its limit

**Static.** Every `tools/validate_*.py` and `tools/check_*.py` was searched for a
direct read of the clock:
- `date.today()`, `datetime.now()`, `utcnow()`, `time.time()` and
  `Timestamp.now()`;
- `session.utc_now()`, `utc_iso()`, `session_date()` and `session_date_obj()`
  called with no argument;
- `last_completed_session()` and `last_trading_session()`.

20 gates match.

**Empirical.** Each matching gate was run on the real clock (Sunday 1 Nov, about
22:30 ET), then with the clock shifted to 29 Oct and to 2 Dec by B101's scratch
wrapper. The wrapper replaces `datetime.datetime` and `datetime.date` before the gate
loads.

**The limit.** A gate that never touches the clock itself, but whose code under test
stamps rows with `session.utc_now()` while its fixture is dated, is invisible to the
static search. `validate_alpha_proposer` was found that way: from CI, not from the
search. Its 2 Nov runs on b101 and b102 failed while a96's run of 1 Nov passed, with
no code change between them. A full sweep of every gate under a shifted clock would
find the rest of that class. It costs about one whole run of the suite per date, so
it is listed as a follow-up, not done here.

## The inventory: gates

**Verdicts:** (i) pin it; (ii) leave it, reading today on purpose (each now carries a
comment saying so, with its next-attention day); (iii) a defect in the code under
test.

| Gate | Line(s) | What it feeds | Pin already? | Verdict | Real clock | 29 Oct | 2 Dec |
|---|---|---|---|---|---|---|---|
| validate_prediction_markets | (A88) | section J's session | A88 | pinned | — | — | — |
| validate_monthly | `GATE_NOW`, group D, the fixture month | the whole fixture month | B101 (and B101b's wrap fix) | pinned | 361/0 (B101b) | 361/0 | 361/0 |
| validate_st_t5_render | `pin_clock()` | the scan's draft stamps | B101 | pinned | 46/0 | 46/0 | 46/0 |
| validate_voices | `pin_clock()` | the 13F pull's `retrieved_at` | B101b | pinned | 73/0 | 73/0 | 73/0 |
| **validate_alpha_proposer** | the code's `session.utc_iso()` (`alpha_proposer/propose.py` 238, `alpha/manifest.py` 75) against the fixed week of 2026-11-02 | the family budget's week count | **B106** | **(i), pinned** to `AS_OF` | 42/0 (base 41/1) | 42/0 (base 42/0) | 42/0 (base 42/0) |
| validate_a43_render | 62 | a cutoff one day after the run | — | (ii) | pass | pass | pass |
| validate_alpha | 1897, 1906, 1927 | the lab line as of the run | — | (ii) | pass | pass | pass |
| validate_audit_1 | 442 | a 1,500-day fixture window ending today | — | (ii) | pass | wrapper exits 127 inside the FRED compaction: not a gate result | same |
| validate_benchmark | 209, 267 | marks stamped when computed | — | (ii) | pass | pass | pass |
| validate_book_b_scanner | 628 | graded calls as of the run | — | (ii) | 63/0 | 63/0 | 63/0 |
| validate_claims | 122 | the real claims register: none dated in the future | — | (ii) | pass | pass | pass |
| validate_dealer_vendor | 177 | stored vendor rows as of the run | — | (ii) | pass | pass | pass |
| validate_em_scorecard | 180 | no projection past today | — | (ii) | 63/0 | 63/0 | 63/0 |
| validate_events | 402 | release dates relative to today | — | (ii) | pass | pass | pass |
| validate_morning_anchor | 82 | a fetch instant just before the run | — | (ii) | pass | pass | pass |
| validate_narratives | 684 | the register as of the run | — | (ii) | pass | pass | pass |
| validate_official_sources | 383–407, 689–698 | a future-dated row is refused | — | (ii) | pass | pass | pass |
| validate_register | 365–366, 415, 764–771 | `decide.py` runs as a subprocess on the real clock | — | (ii) | pass | the wrapper cannot reach the subprocess: 4 checks fail as an artefact | same |
| validate_security_master | 63 (`TODAY`) | the real master's identifiers resolved today | — | (ii) | pass | pass | pass |
| validate_stack | 168, 176 | the fixed `SESSION` as of the run | — | (ii) | stopped at the 400 s cap on this branch (B97's speed-up is not here) | not run | not run |
| validate_structure_compare | 190 | the last completed session | — | (ii) | pass | pass | pass |
| validate_vendor_divergence | 43 | a data gate on the box's store | — | (ii), a data gate (skips with no store) | skip | — | — |
| check_store_registry | 119 | the store check's default as-of | — | (ii), a store tool (real store) | — | — | — |

**The (ii) gates' next-attention days** are in each gate's comment. Most are "none":
the read is relative to the run, so it cannot drift. The dated ones:
- **validate_benchmark:** a run straddling 00:00 UTC, which can split the stamp from
  the comparison.
- **validate_register:** the eve of a market holiday. It is verified on a Sunday;
  its subprocess and fixture both read the real clock.
- **validate_security_master:** the next active window in
  `config/security_master.yaml` that ends.

**(iii) defects:** none found in the code under test. The one design note is
alpha_proposer's: its fixture checks a fixed week (2026-11-02) while the proposer
stamps the real clock. The pin fixes the gate. The rule in the code, that a family
is counted by the week of its registration, is right.

### The pin made (validate_alpha_proposer)

```python
GATE_NOW = AS_OF          # "2026-10-09T22:10:00+00:00", the fixture's proposer instant

def pin_clock() -> None:
    import datetime as dt
    from altdata import session
    session.utc_now = lambda: dt.datetime.fromisoformat(GATE_NOW)
```

`pin_clock()` runs first in `main()`. Nothing the gate checks changed.

**The failing check on the base, CI run 41379176410 (2 Nov):** "FAIL four valid
proposals of one family: the weekly family budget (2) cuts them (1 kept)". The
fixture's own registration fell in the week of 2026-11-02 once the real clock reached
it. It would fail through Sunday 8 Nov, and pass again after.

## The inventory: the code under test (listed only, nothing changed)

These modules read the clock directly, not through `altdata.session`. A gate's
`pin_clock()` cannot reach them, so a gate on their path needs the wrapper's kind of
patch, or a parameter.

| Module | Line(s) |
|---|---|
| alpha/ledger.py | 483 |
| alpha/report.py | 445 |
| alpha/search.py | 103, 642 |
| altdata/basis_proxy.py | 492 |
| altdata/chain_metrics.py | 495, 533 |
| altdata/claims.py | 154 |
| altdata/events.py | 411, 473 |
| altdata/events_ingest.py | 166 |
| altdata/fomc_audit.py | 173 |
| altdata/fred_history.py | 254, 304 |
| altdata/fx_charts.py | 116, 246, 399 |
| altdata/ledgers/__init__.py | 230 |
| altdata/ledgers/__main__.py | 66 |
| altdata/ledgers/st_r5_31b.py | 274 |
| altdata/ledgers/st_r5_44b.py | 255 |
| altdata/loggers/auction.py | 174, 176, 282–284 |
| altdata/mechanism_watch.py | 108 (`_now`, pinned by B101 for its gate) |
| altdata/meme_ingest.py | 212, 318 |
| altdata/note_fetch.py | 348, 367 |
| altdata/paper_bid.py | 238 |
| altdata/report/ (`__main__`, export, generate, signals, weekly_scan; content, not a pipeline) | 40, 49; 470; 70, 314; 234; 199 |
| altdata/return_attribution.py | 296 |
| altdata/security_master.py | 99 |
| altdata/sm_export.py | 154 |
| altdata/sources/ (_crypto, aaii, bdf_webstat, fed_calendar, llama, news, ons_cpi, overnight, statcan_cpi, upcoming_auctions, voices_scan) | 41; 191, 293; 87; 53; 281; 342; 95; 380; 132; 60; 838 |
| altdata/voices.py | 846, 863 |
| daily_cascade/morning_payload.py | 96 |
| register/heat.py | 151 |

That is 42 files. monthly_macro/ and state/ read the clock only through
`altdata.session`, and the weekly modules have no direct read.

## Gates (one at a time)

| Gate | Tally |
|---|---|
| validate_alpha_proposer (pinned) | real 42/0; 29 Oct 42/0; 2 Dec 42/0. Base: real 41/1, 29 Oct 42/0, 2 Dec 42/0 |
| the (ii) gates | as in the table above; a comment line only, no check changed |
| check_registry | OK |
| check_library | 27 papers, 0 failures, 0 warnings |
| validate_audit_3a (reads CLAUDE.md) | 88 passed, 0 failed |

## A110 (2-3 Nov 2026): the four-clock sweep

**Trees.** The sweep ran on the rehearsed tree, origin/a105-merge-week-rehearsal-2
at `b8023fba`, in a scratch worktree, through B106's wrapper:
- the wrapper is a `sitecustomize` on `PYTHONPATH`, active when `CLOCK_DELTA`
  is set;
- each gate ran once per clock, one at a time, capped at 540 s;
- the gate list was `tools/gate_list.py --kind code` plus `smoke_test.py`, 164 in
  all.

The pins are on origin/b101-date-drift-gates. Its tip `1ce709d6` carries B126's
pre-flight, and this paste's commit was rebased onto it.

**The run, and its restart.**
- **First pass, 2 Nov 21:48 UTC.** 121 gates on the 16 Nov clock, then the
  laptop ran short of memory and the run was killed. It was not restarted then.
- **The wrapper's two fixes, before the restart (ruled in the reorder):**
  - matplotlib, and its date converters, now load before the patch. Loaded
    after it, the converters were keyed to the wrapper's classes, so a real
    date found none ("float() argument must be ... not 'datetime.date'").
  - A `python -c` child whose code reads `sys.modules` now runs unwrapped, on
    the real clock. That is the fresh interpreter validate_alpha_no_orders and
    validate_alpha_proposer inspect, and the wrapper's pandas import had put
    `subprocess` in it.
- **The restart, 3 Nov 03:12 to 05:30 UTC,** detached:
  1. a zero-shift control (`real0`) over the first pass's five failures;
  2. the same five again on the 16 Nov clock, with the fixed wrapper;
  3. the 16 Nov clock from gate 122;
  4. the other three clocks whole.
- **Totals.** 10,468 gate-seconds over 545 runs, plus the first pass's 121. No
  run hit the cap.

**The control.** The first pass's five failures were all the wrapper's:
validate_alpha_no_orders, validate_alpha_proposer, validate_horizon_charts,
validate_price_sources and validate_quarterly_stack. Each passed under `real0`
and again on the 16 Nov clock once the wrapper was fixed.

**The four-clock table.** Each gate's final verdict per clock; the first pass's
five failures are shown by their re-run.

| Gate | 16 Nov | 2 Dec | 4 Jan | 15 Mar | First failing check |
|---|---|---|---|---|---|
| validate_em_scorecard | pass | pass | **FAIL** | **FAIL** | external debt % of GDP over the latest full year's GDP (2026-03-31: 32.5%) |
| validate_sr38_inbox | pass | pass | pass | **FAIL** | the first drop: the three keys are fresh (1) |
| validate_thesis_register | **FAIL** | pass | pass | pass | seed-alt-asset --dry-run prints the refusals and exits 2 |

**Passing on all four shifted clocks (161 of 164):** check_library, check_master_guide, check_registry, validate_6e_rest, validate_6f_calibration, validate_a43_render, validate_a47_chain3, validate_a48_batch11, validate_a50_dealer_store, validate_a55_box_fixes, validate_ai_fcf, validate_alpha, validate_alpha_lab_3, validate_alpha_lab_4, validate_alpha_no_orders, validate_alpha_proposer, validate_alt_asset_scan, validate_aq3_series, validate_attribution, validate_audit_1, validate_audit_2, validate_audit_3a, validate_audit_fixes, validate_audit_leftovers, validate_b45_chain3, validate_b48_scoreboard, validate_b51_registry_html, validate_b59, validate_backup, validate_backups, validate_base_rates, validate_basis_proxy, validate_batch12, validate_batch13, validate_batch14_a1, validate_batch14_a2, validate_batch14_b1, validate_batch14_b2, validate_batch15_1, validate_batch15_2, validate_batch16_midterm, validate_batch3_a, validate_benchmark, validate_book_b_scanner, validate_by_hand_audit, validate_claims, validate_config_refs, validate_correlation_layer, validate_crypto_basket, validate_crypto_sources, validate_daily_close, validate_dealer_block, validate_dealer_vendor, validate_decision_quality, validate_deploy, validate_derived, validate_digital_addendum, validate_dth1, validate_edgar_guidance, validate_edition_consistency, validate_enforce, validate_error_corpus, validate_es_block, validate_events, validate_exec_bits, validate_executions, validate_exposure_edges, validate_feed_repair, validate_feeds_scheduled, validate_figure_budget, validate_fred_history, validate_gates, validate_gld_exposure, validate_gold_attribution, validate_grader, validate_gtm, validate_horizon_charts, validate_ibkr_bars, validate_ibkr_costs, validate_ibkr_portfolio, validate_ibkr_whatif, validate_imf_ifs, validate_ledgers_b6, validate_lenses, validate_library_st_l, validate_ll6, validate_meme_ingest, validate_monthly, validate_monthly_frames, validate_monthly_stack, validate_morning_anchor, validate_move_screen, validate_names, validate_narratives, validate_no_filler, validate_numeral_audit, validate_official_sources, validate_opening_setup, validate_outliers, validate_packets, validate_paper_exec, validate_postmortems, validate_prediction_markets, validate_premium_sleeve, validate_price_sources, validate_prices, validate_quality, validate_quarterly_gates, validate_quarterly_readers_1, validate_quarterly_readers_2, validate_quarterly_rows_6i, validate_quarterly_stack, validate_rates_anchors, validate_readability, validate_regime, validate_register, validate_releases, validate_releases_b, validate_rollup, validate_secondary_notes, validate_secrets, validate_security_master, validate_st_r4_t1, validate_st_r4_t1b, validate_st_r5_index, validate_st_r5_rates, validate_st_r5_t1_rest, validate_st_t1_rest, validate_st_t2_rates, validate_st_t3_calib, validate_st_t5_prl, validate_st_t5_render, validate_stack, validate_stack_cadence, validate_stack_hooks, validate_stitch_tools, validate_structure_compare, validate_system_metrics, validate_systemd_units, validate_tb_harness, validate_tb_harness_fpr, validate_themes_panels, validate_trend_breadth, validate_value_of_information, validate_voices, validate_vol_event, validate_volume_profile, validate_weekly, validate_weekly_analytics, validate_weekly_calendar, validate_weekly_complete, validate_weekly_edits, validate_weekly_fixes_8, validate_weekly_fixes_9, validate_weekly_gold_block, validate_weekly_integrity, validate_weekly_opener, validate_weekly_readability, validate_weekly_stack, validate_weekly_storyline, smoke_test.

**B106's (ii) list (gates that read today on purpose).** All passed on all four
clocks except validate_em_scorecard. Its failing checks are not its deliberate
read of today (group B, "no projection past today is stored", next attention
none). That read is left on the real clock by the pin below.

**The pins (GATE_NOW and pin_clock(), the gate's run only; no check changed).**
None is a defect in the code under test. Each is a fixture dated so that "now"
or "the latest" moves.

| Gate | Why it failed | GATE_NOW |
|---|---|---|
| validate_thesis_register | The CLI case (`seed-alt-asset --dry-run`) cannot pass `now`. It seeds a file written 2026-11-09 at the real instant: refused as "in the future" before 9 Nov and as "more than seven days" after 16 Nov, but **accepted from 9 to 16 Nov**, so CI would fail on those real days too. | `SEED_AT` (2026-11-08T12:00Z), the instant every other seeding in the gate uses |
| validate_em_scorecard | The fixture stores WEO GDP to 2026-12-31 (a projection). From 1 Jan 2027 that row is knowable, so "the latest full year's GDP" and Brazil's debt as-of move. | 2026-10-11T12:00Z, the fixture's own instant; group B's deliberate today read keeps the real clock through `REAL_UTC_NOW` |
| validate_sr38_inbox | The workbook is as of 2026-09-30; by 15 Mar 2027 the first drop's keys are past their allowance, so "the three keys are fresh" fails. | 2026-10-12T00:00Z, the gate's own cut (group E) |

**The five tallies per pinned gate** (b101's tree, the same wrapper):

| Gate | real | 16 Nov | 2 Dec | 4 Jan | 15 Mar |
|---|---|---|---|---|---|
| validate_thesis_register | 66/0 | 66/0 | 66/0 | 66/0 | 66/0 |
| validate_em_scorecard | 63/0 | 63/0 | 63/0 | 63/0 | 63/0 |
| validate_sr38_inbox | 53/0 | 53/0 | 53/0 | 53/0 | 53/0 |

**Defects in the code under test:** none found.

**Not reached by the wrapper (named, not judged):**
- validate_register's subprocess, and validate_audit_1's FRED step (B106's two);
- C-level clock reads: pandas' `Timestamp.now`, numpy's `datetime64("now")`,
  sqlite's `CURRENT_TIMESTAMP`, the shell's `date`;
- since the restart, the `python -c` children that list `sys.modules`. They run
  on the real clock; they check imports, not dates.

**The real clock.** The sweep ran the four shifted clocks over every gate. On the
real clock it ran only the five controls (`real0`) and the three pinned gates.
The rehearsed tree's own real-clock runs are A105's.
