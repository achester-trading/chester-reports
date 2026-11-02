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
