# A71: the audit's leftovers, reconciled, and the smallest built (24–25 Oct 2026, overnight)

`a71-audit-leftovers` branches from `origin/a70-amendment-3-record` at its tip, `1623a33b`. Branch-only: nothing merged, the box not touched, no units, no secrets. Nothing here merges before the 1 Nov Monthly.

**A70's CI at A71's start.** Run `40151381058` was queued, and was not waited on.

## 1. The reconciliation (workplan v7, section 5, item 7)

Each leftover is checked against the code on this branch. The new gate's group A holds the evidence for each one that is done.

| Leftover | Status | Evidence |
|---|---|---|
| Incremental pulls | **Done, except four SDMX writers** | audit-leftovers-1 (17 Oct). FRED from its newest date less a revision window by frequency (`altdata/sources/fred.py`, `REVISION_WINDOW_DAYS` 30/120/400). fng and ecb_irs made incremental. Bundesbank, CFETS, auctions, fiscal data, the crypto venues and FRED releases were already windowed. **Built here:** H.4.1 (below). **Left:** imf_ifs, bis_cbpol, imf_weo and imf_em, whose `startPeriod` was never tested against their endpoints (about 1 h with one live request each, on the box or by a probe paste). Whole-file sources (EIA, ACM, the Tuck library, the Shiller workbook and others) have no "since" parameter |
| The chester-meme draft ingest | **Done** | `altdata/meme_ingest.py` (the `meme_drafts` table, Book D drafts), on main via chain-3. Its timer is the operator's (21:15, and the 06:45 pass) |
| Encrypted backups and the Drive mirror | **Done** | audit-leftovers-1 part 2: the crypt remote in `scripts/rclone_sync.sh`, the weekly restore test, retention on both sides; `validate_backups`, `validate_backup_crypt` |
| Append-only triggers on observations | **Done; the install is the operator's** | `observations_no_update` / `_no_delete` and the one `maintenance()` path (`altdata/observations.py`); `python -m altdata.observations install-triggers` is a box write |
| The as-of join's source tier | **Done for one instant** | audit-leftovers-2 part 3: at the same newest instant the higher tier wins, with `tier` and `tier_over` shown (`validate_outliers` group D). **Left, a ruling:** the broader rule (a lower tier never overwriting a higher across instants) |
| Writers onto their registered source ids | **Done** | `open_writer()` refuses an unregistered source (`UnregisteredSource`). `validate_outliers` group C scans every writer module's literal sources, the b59, b56 and a58 writers included: 37/0 here. No data is rewritten; old rows keep their tags and read through `source_ids.canonical()` |
| Call sites onto the Security Master, the yfinance basket first | **Done for the basket; built here: the blocklist at its resolver** | audit-leftovers-2 part 4 moved the yfinance and crypto baskets onto `resolve_basket`. **Built here:** below. **Left, listed with why:** the config universes (hand-edited YAML), `fx_charts.CATALOG` (behind its generator rework), the issuer-file name maps, `edgar.universe()` (a ruling: it changes EDGAR's universe), the meme loggers' universe (chester-meme's interface) |
| The FRED history run and the deep price backfill | **The operator's box steps** | `python -m altdata.fred_history backfill` and the deep price backfill after the compaction; in the box sheets |

## 2. Built here

**The as-of source tier** was done before this branch, at one instant, so nothing was built for it and no report figure changes.

**The blocklist at the basket's resolver** (`altdata/sources/yfinance_source.py`, `resolve_basket`).
- Each symbol is asked of the master's `is_restricted` at the place its key is resolved. For a string the master does not know, that falls back to the tracked-entities rule.
- A restricted name is logged and listed in `pull()`'s summary (`restricted`). It is **not dropped**: Standing rule 1 bars a recommendation, not a price, and the register refuses the recommendation at write time.
- No stored key changes. On the real master the basket's 127 symbols resolve, none of them restricted.

**No literal ticker in the basket's call sites.** `pull()` and `pull_crypto_basket()` carry no `mkt_` literal and resolve their basket once. The new gate's group C holds this by AST.

**H.4.1 incremental once held** (`altdata/sources/fedboard.py`). This is audit-leftovers-1's one-line follow-up.
- With both FIMA keys stored, the package is asked for its last **8** Wednesdays: the newest and seven before it, the stated overlap, which covers the release's restatements. The full ten years (520) are asked only when either key is missing.
- `H41_HELD_LASTOBS` is session-set.
- The URL is otherwise the one the writer always used. The program serves any `lastobs` up to 1,000.
- No stored value changes, only how much is fetched.

**No report figure changes.** The leftovers here change what is asked and what is logged, never a stored value. The gates that print figures pass as before: `validate_security_master` 102/0, `validate_official_sources` 340/0, `validate_crypto_sources` 117/0.

## 3. Gates

| Gate | Result |
|---|---|
| `tools/validate_audit_leftovers.py` (**new**, in the Makefile) | 18/0: A reconciliation 7, B the blocklist 5, C no literal 2, D H.4.1 4 |
| `tools/validate_security_master.py` | 102/0 (group M's source check now reads the call's prefix, since the call passes the restricted list) |
| `tools/validate_outliers.py` (groups C and D: registered sources, the tier) | 37/0 |
| `tools/validate_audit_2.py` | 26/0 |
| `tools/validate_official_sources.py`, `validate_crypto_sources.py` | 340/0, 117/0 |
| `tools/validate_audit_3a.py` (CLAUDE.md's counts) | 88/0, after the recount |
| `check_registry`, `check_library` | OK; 0 failures, 0 warnings |

**The count.** One gate is added, so CLAUDE.md's line now reads one hundred and forty-one code gates (one hundred and thirty-eight Python, three shell), as `validate_audit_3a` holds it.

## 4. What is left, with the hours each needs

| Item | Hours | Why it is left |
|---|---|---|
| imf_ifs, bis_cbpol, imf_weo, imf_em incremental | about 1 | each `startPeriod` needs one live request to confirm, under the sources rule; not probed from the laptop |
| The broader tier rule across instants | ruling, then about 1 | the operator's (audit-leftovers-2) |
| The config universes onto the Security Master | about 3 | changes hand-edited YAML formats; a ruling on the format first |
| `edgar.universe()` onto the Security Master | about 0.5 after a ruling | it would change EDGAR's universe (BRK-B) |
| The FRED history run, the deep price backfill, `install-triggers` | box | the operator's, from the box sheets |

## CI

| Run | On | Result |
|---|---|---|
| read once after the push | the A71 tip | see the report |

## Needs you (at most five)

1. **The box steps** that close three leftovers: `install-triggers`, the FRED history run and the deep price backfill (the box sheets).
2. **The broader tier rule** across instants: yes or no.
3. **`edgar.universe()`:** may it move onto the Security Master (it would add BRK-B to EDGAR's universe)?
4. **The four SDMX writers' windows:** a paste that allows one probe each.
