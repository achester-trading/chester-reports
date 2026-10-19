# b45-chain3: session notes (Part 3 of session B's paste of 19 Oct 2026)

**This branch merges in the third chain.** It is `chain-2`'s tip `ab27c07` (`STITCH
COMPLETE e0a8cc0`) with alpha-lab-4's final tip `393b9de` merged in: one merge
commit, `96ae85f`, no rebase. Nothing merged to main, deployed or run on the box. No
unit was touched. Session A's branches were read and never pushed to, and
chester-meme was not touched.

## The merge

- **Two conflicts:**
  - `CLAUDE.md`: chain-2's worded count line is kept;
  - `tools/validate_audit_3a.py`: the count plant now reads both forms, words up to
    "one hundred and eighteen" and digits.
- **Everything else merged cleanly:**
  - the Makefile (alpha-lab-4's gate line);
  - `alpha/loops/weekly.py`, the catalogue and `docs/alpha-lab.md`;
  - the signal-triage register (SR-29's line);
  - the two registries (CD-12's keys);
  - `tools/validate_alpha.py`.
- **Ruling 5(b):** the dealer regime does not join search-v1 at this stitch. It
  stays pending on its history. The store holds no `exposure.*` rows: the captures
  are computed files, so the line will read "no history stored" until a writer
  stores them.
- **The count line,** recounted once at the end: **one hundred and twenty code
  gates** (one hundred and seventeen Python, three shell). That is chain-2's 118,
  plus `validate_alpha_lab_4`, plus `validate_b45_chain3`.

Gates run locally on the merged tree:

| Gate | Result |
|---|---|
| `validate_audit_3a` | 88/0 |
| `check_registry` | OK |
| `check_library` | 0 failures |
| `validate_alpha_lab_4` | 65/0 |
| `validate_crypto_sources` | 117/0 |
| `validate_digital_addendum` | 94/0 |
| `validate_st_t5_prl` | 62/0 |

## 1. Ruling 6's code (c75f371)

- **The PROPOSED posting.** `altdata/mechanism_watch.py` `post_entries` posts each
  unposted entry to the narrative register through `NarrativeRegister.propose`, its
  existing path, with its validation and its human gate.
  - **What it cites:** the entry's source, stored first as a `headline` event (a
    proposal must cite stored events).
  - **What it claims:** its factor's template from `config/story_queries.yaml`
    `mechanism_watch.posting`, which sets the implied outcome, the horizon and the
    linked dimension. The entry's own text is the story's direction.
  - **The grade** moves from "awaiting its posting" (G-29's pending grade is gone:
    it needs no new scale) to "proposed", on the entry and on its candidate.
  - **A refusal** keeps the entry pending, with the reason in `post_note`.
  - **Nothing confirms:** confirm and reject stay the operator's.
  - **The scan** posts after its drafts are written (step 6).
  - **The templates are session-set,** a rule-31 draft (see needs-you):
    - Factor I: NVDA's close higher in 182 days, linked to trend +;
    - Factor V: BTC-USD's close higher in 182 days, linked to liquidity +.
- **The feeds' terms.** Each of the seven feeds carries `terms_read: 2026-10-18` (the
  18 Oct review) in its catalogue entry. `monthly_macro/prl_part.feeds_terms_line()`
  adds one line to the Monthly part naming any feed read more than 92 days before
  the as-of, or with no date, and nothing when none is.
- **The PRL part's reads.** `prl_part.allowed_reads()` is the whole read set:
  `calc.prl_*`, and `pearl.chain_*` and `yfinance.crypto_prl` read directly. The
  docstring states ruling 6. No `calc.prl_*` key copies them.
- **G-6** waits for the state dashboard and Draft 3's Appendix E lists it. The deny
  entries are session A's. Nothing here touches either.

## 2. X-3.4, engine 7, intraday dealer regimes

`alpha/engines/intraday_dealer.py`, registered as `intraday_dealer` (family
`intraday_dealer`).

- **Pre-registered** in `config/alpha_intraday_dealer.yaml`'s `spec`, sha256
  `2efa781c6d525bf5b13abb0d95193a4e867e2e04c6b0f56e05722b6a9798f1c7`, quoted by E-7
  in `alpha/research/roster-2026-10-19-x3-4.yaml`. A changed spec is refused.
- **What it reads (our own only):**
  - **the 09:45 captures:** `data/computed/<session>/<SYM>_*_exposure.json`, the
    gamma regime from `overall.net_gex` and `overall.net_to_gross` (at least 0.10,
    the threshold `alpha/event_rates.py` uses);
  - **each capture's spot;**
  - **the stored open and close;**
  - **the 5-minute bars;**
  - **the 0DTE share of the capture chain's volume,** recorded and labelled "no
    side", never a condition.
- **The clocks.**
  - **A capture** is knowable at its computed_at. One computed after the 10:15 ET
    deadline is never read, and that session has no decision.
  - **Prices** are read at their market time: the open at 09:30, a bar at its start.
  - **Two honest limits:**
    - the store records the open and the bars only after the close;
    - the capture's spot is Yahoo's last price, read as real time.

    Both are written into the spec, so a reader can see them.
- **The entry** is the open of the first stored 5-minute bar starting at or after the
  decision, within 10 minutes; otherwise there is no trade ("no stored price near the
  decision"). The bars table exists for the tape set (SPY, QQQ, IWM), so this is the
  nearest honest entry.
- **The bucket** is the symbol, times the 09:45 regime, times the sign of the
  open-to-09:45 move. Indeterminate regimes and zero moves form no bucket.
- **The data gate:** 30 completed sessions per bucket, counted from the captures'
  first day; below that, "awaiting (n=k of 30)".
- **The choice:** from the formation sample, the best of continuation or reversal,
  times 12:30 or the close, by mean net of costs (ties to reversal, then 12:30). It is
  frozen, and only later sessions trade, and only if that mean is above 0.
- **Instruments:** SPY, QQQ, IWM. Each is captured with Greeks, has 5-minute bars
  stored and has the `etf` cost class, which prices a one-session round trip with no
  holding cost.
- **Not tracked:** VWAP and a finer opening range. The writer they need (an intraday
  bar writer at the 09:45 slot) is listed, not built.
- **A research engine:** `signal()` queues nothing. The nightly loop cannot act at
  09:45, so the record is the point-in-time backtest through the harness until an
  intraday fill path exists (listed, not built).
- **No vendor value:** no FlashAlpha key, no `data/vendor` file.
- **Gates (validate_b45_chain3 group B, 23/0 with group A):**
  - the spec hashes to E-7's sha256, and a changed spec is refused;
  - at n=29 the bucket prints "awaiting (n=29 of 30)" with no trades;
  - at n=30 it opens (reversal to the close, on the fixture) and trades only later
    sessions;
  - a capture computed at 10:20 is never read;
  - the entry is the 09:50 bar against a 09:47 decision;
  - costs reproduce 23 bp by hand (2 x (1.5 + 5 + 5) at $2,000);
  - a session's net and its 0DTE share (0.6) are checked by hand;
  - VWAP and the opening range are not tracked, and no signal is queued;
  - a FlashAlpha key set in the environment is never read.

## 3. Registry, catalogue and units

No new store key on this branch: ruling 6 writes `events` and `narratives` rows (no
registry keys), and engine 7 writes nothing. CD-12's four keys arrived with the merge,
registered with their units.

## CI

| Run | Commit | Result |
|---|---|---|
| 39293846470 | 96ae85f (the merge) | 128/129: **`validate_secrets` failed.** CD-12's `btcdata.py` wrote its User-Agent by hand, and chain-2's group J requires `altdata.sources.user_agent` |
| 39294833168 | c75f371 (ruling 6) | the same failure |
| 39296209515 | eab82f8 (engine 7) | queued when read |

**The fix** (the Master Guide paste's Part 0, 19 Oct 2026): `btcdata.py` sends
`user_agent.generic()`. Locally `validate_secrets` reads 58/0 and
`validate_crypto_sources` 117/0. alpha-lab-4 has no `user_agent` module, so its own
gate passed there and the fix lives here, on the merged line.

## Box commands (for Ari; inside a window; after the third chain merges; dry runs first)

```bash
cd ~/chester-reports

# E-6 (engine 6): its read-only dry run, then registration by manifest
.venv/bin/python -m alpha.engines.reversion lines 2>&1 | tee ~/logs/reversion_lines_dryrun.log
.venv/bin/python -m alpha.manifest register alpha/research/roster-2026-10-19-x3-3.yaml

# E-7 (engine 7): its read-only dry run (each bucket's state, the legs not
# tracked), then registration by manifest
.venv/bin/python -m alpha.engines.intraday_dealer lines 2>&1 | tee ~/logs/intraday_dealer_lines_dryrun.log
.venv/bin/python -m alpha.manifest register alpha/research/roster-2026-10-19-x3-4.yaml

# The mechanism scan's posting: the dry run (no model call, no write), then the
# Saturday run posts each entry as a proposed story; confirm or reject is yours:
.venv/bin/python -m altdata.mechanism_scan run --dry-run
#   python -m altdata.narratives confirm <id>   |   python -m altdata.narratives reject <id>
```

The search's first capped step and the bitcoin-data first pull are in alpha-lab-4's
notes.

## Files shared with session A's branches

- **a47-chain3:**
  - `altdata/crypto_blocks.py` and `config/crypto_sources.yaml` (CD-12, through the
    merge);
  - `CLAUDE.md` (the count line, the ST-15, engine 7 and search paragraphs);
  - the `Makefile` (two gate lines);
  - `tools/validate_audit_3a.py` (the plant reads both forms).

  Session A listed these as shareable.
- **library-draft-3:** `docs/alpha-lab.md` (sections 11 and 12) and
  `docs/signal-triage-register.md` (SR-29's line).

## Needs you, with every rule-31 draft for accept-all

1. **The posting templates** (`config/story_queries.yaml`
   `mechanism_watch.posting`), session-set:
   - Factor I: NVDA up over 182 days, linked to trend +;
   - Factor V: BTC-USD up over 182 days, linked to liquidity +.

   They decide what every posted story claims. Accept, or name better series.
2. **Engine 7's session-set choices,** before you register E-7 (registration freezes
   them):
   - the 10:15 decision deadline;
   - the 10-minute entry wait;
   - the 0.10 net-to-gross floor;
   - reading the capture's spot as real time;
   - SPY, QQQ and IWM;
   - the choice rule's tie order;
   - 30 formation sessions per bucket.
3. **`exposure.*` rows are not in the store.** The captures are files, so the dealer
   regime's coverage line, and `alpha/event_rates.py`'s dealer bucket, read nothing.
   Do you want a writer that stores each capture's regime fields with their
   computed_at? It is not built.
4. **An intraday bar writer at 09:45** (for VWAP and the opening range) and **an
   intraday fill path** (for engine 7's paper trades) are listed, not built.
