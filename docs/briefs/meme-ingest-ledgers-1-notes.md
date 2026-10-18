# meme-ingest-ledgers-1 (17 Oct 2026)

**The base and the merge order.** Branch `meme-ingest-ledgers-1` was cut from the
tip of `audit-leftovers-1` (`717a076`). It is my own line, and it **merges after
`audit-leftovers-1`, in the second stitched chain.** It carries one fold of
Monday's chain (`8f53e6b`, ruling 5). Those commits reach main on Monday, so at
Thursday's merge the fold's conflicts are already resolved and change nothing
else. Not merged, not deployed, nothing run on the box.

Commits:
- `86e4b31` folds the chain;
- `333831a` is the fold's second pass;
- `f3d5bf4` is Part 0, the ingest;
- then Part 1, the ledgers, and the vp-1 families fix described below.

Every commit is authored with the GitHub no-reply address passed through
`git -c user.email=...`. The shared `.git/config` holds the gmail address, which
GitHub now refuses (GH007). I did not edit the config.

## Step 0: CI for audit-leftovers-1

- Run 39075873690 on `a71078c` **failed 4 of 92**. The failures were secrets
  group I (the gate's own fixture output), validate_prices (its pinned freshness
  calls), sr38 (the spdji sweep line) and check_library (CLAUDE.md's tree names).
  All four were mine, and all four are fixed in `717a076`.
- **The re-run, 39078904434 on `717a076`, passed.**

## The 17 Oct rulings, applied

1. **The Alpha Lab outbox gets its own drive.file remote.**
   `scripts/rclone_sync.sh` reads the remote from `CHESTER_RCLONE_OUTBOX_REMOTE`
   (`push_lab_outbox`). The inbox stays read-only on `$INBOX_RNAME`. Neither
   remote is ever the crypt remote. The old token is revoked only after the
   outbox has written through the new remote once: box step 5 below.
   `validate_backups.py` group J holds it.
2. **The box steps run Thursday evening.** The box steps below are written for
   then. Running without crypt for at most one night is accepted.
3. **GeckoTerminal's guard at 6/min is confirmed.** No change.
4. **GLD's archive is a one-time anchor.** No recurring line (rule 30).
5. **The aud-2 fold stands, and the rest of Monday's chain is folded once** (the
   next section).

## The fold's conflicts (8f53e6b into audit-leftovers-1's tip)

The rule: where the same line differed, the chain's version won; where this
line added something, the addition was kept. Files that both sides changed:

- **`metrics_registry.yaml`.** The first pass, a line-level union, split an
  entry. `333831a` re-merged it entry by entry, three ways. Where both sides
  changed a block, this line's version was a superset of the chain's, so it was
  kept. `check_registry` reports OK.
- **The vp-1 lens families: a fold interaction, fixed with Part 1.** The chain
  has no lens gate, so its 18 `calc.vp_*` series (POC, VAH and VAL for spy, qqq
  and iwm, session and 20-session) arrived without a family. validate_lenses
  failed in CI run 39080195144. They are now under `families:` as `price`, and
  validate_lenses passes 49/0 locally.
- **`scripts/rclone_sync.sh`, the README's lab paragraph,
  `tools/validate_backups.py` and `tools/validate_backup.py`.** The chain's Alpha
  Lab copies used one remote. They are re-pointed: the inbox to the read-only
  remote, the outbox to its own (ruling 1). The fake outbox remote is now in
  validate_backup's fixture.
- **`deploy/systemd/chester-backup.service`.** ReadWritePaths is the union of
  both sides.
- **Merged as both:**
  - the Makefile's gate list;
  - `config/catalogue_commands.yaml`;
  - `altdata/loggers/__init__.py`;
  - `.claude/settings.json`, `.gitattributes` and `.gitignore`.
- **CLAUDE.md.** The chain's paragraphs and this line's are both in. The count
  line was recounted, and validate_audit_3a's count plant (its `wrong` value)
  was updated to match.
- **The chain's version, with this line's additions:**
  - `daily_cascade/stack.py` and `daily_cascade/weekly_stack.py`;
  - `monthly_macro/stack.py`;
  - `scripts/fetch_overnight.sh`, `scripts/check_heartbeat_cron.sh` and
    `scripts/backup_retention.py`;
  - `tools/validate_heartbeat_caller.sh`, `tools/validate_monthly_stack.py` and
    `tools/validate_weekly_stack.py`.

**The stitch hazard still stands.** In `tools/validate_batch3_a.py`, keep our
check, then `group_b_daily()` from st-r5-audit and 6b-dealer-3.

## Part 0: the ingest

Full detail is in `docs/briefs/meme-ingest-notes.md`. In short:
- **Inputs are checked before anything is stored.** The manifest and schema are
  checked first. Restricted and blocklisted packets are refused and logged.
  Schema-invalid packets are skipped.
- **Each packet becomes one `meme_drafts` row, keyed by `packet_id`.** The table
  has a SQLite blocklist trigger. The ingest never writes a decision.
- **It runs at 21:45 (held back) and at 06:45.** The close and the anchor print
  one line: "meme drafts awaiting review: n (refused: m)".
- **`tools/validate_meme_ingest.py` holds it, 21/0.**

### The ingest's box steps

These are listed in the box steps below, steps 6 to 9. The message for the meme
session is at the end of `meme-ingest-notes.md`.

## Part 1: the Batch 6 Tranche 2 ledgers

`altdata/ledgers/` runs as `python -m altdata.ledgers run <item|all> --source
public|store`. Each study writes `docs/ledgers/st-r5.<item>-ledger-2026-10-17.md`
and its episodes CSV.

All five are first editions, labelled **"laptop run, public sources"**. That is
the integrated order's §1.10 offline rule: full history pulled from the source.
FRED was read through its public graph CSV, with no key.

**None of the five has a pass rule in the order.** Each ledger states the rule as
"none stated" and its verdict as "NO GATE IN THE ORDER: base rate recorded". No
rule was invented. Each ledger states its rights consequence and grants nothing.

| Item | Sources | As of | n | What it found |
|---|---|---|---|---|
| **30b** allocation → 10y forward return | FRED Z.1 legs (NCBEILQ027S, FBCELLQ027S, six debt legs), BOGZ1FL153064486Q; Shiller price and dividend | 2026-04 | 266 quarters (about 6.7 independent decades) | Forward = 31.25 − 0.633 × allocation, R² 0.74. Allocation is now 54.2%, the highest of 305 quarters. The fitted line implies **−3.1% a year** for the next decade, with a residual band of −5.8% to 0.0%. Household-share robustness row: R² 0.55. |
| **32b** oil-shock classifier | FRED DCOILBRENTEU and DGS10; Yahoo ^GSPC | 2026-10-14 | 3 episodes (2000-06 onward) | **The regime is ON now.** Brent–SPX is −0.33 (2nd percentile) and Brent–10y +0.52 (100th). Mean S&P return after an episode start: −4.17% over 63 sessions and −4.53% over 126, against +2.03% and +4.23% for every day. 60/40: −1.41% and −1.86%, against +1.57% and +3.24%. The item-25 quadrant prints "not built". |
| **35b** price/ULC gap → margins | FRED WPSFD49116, ULCNFB, NFCPATAX, A455RC1Q027SBEA; WPSFD4131 as robustness | 2026-04 | 6 peaks (2014-07 onward) | The gap is now +3.4 pp, so the margin source is **price**. After a peak, the margin moved +0.31 pp over 4 quarters (falling after 3 of 6), against +0.27 for every quarter. Long robustness row: 25 peaks, +0.46 pp against +0.13. |
| **36b** months-of-supply crossings | Redfin country.csv; FRED MSACSR, MORTGAGE30US, CSUSHPINSA, CPIAUCSL | 2026-09 | 0 (row A) | A, Redfin at 6.0: **no crossing since 2012**. B, Redfin at its own 80th percentile (5.0 months): 3 crossings, +4.09% after, none falling. C, Census new homes at 6.0: 8 crossings with 12 months after them, −0.26% after (5 of 8 falling), against +1.58%. Redfin is now 4.1 months. |
| **43b** policy diffusion → OECD CLI | BIS WS_CBPOL (all 49 banks); OECD DF_CLI, G20 and G7 | 2026-09 | 492 months at the 8-month lead | The index is now +0.27. Against the G20 CLI, the best lead is **13 months (r +0.21)**; at the order's 8 months, r +0.12. G7: best 14 months (r +0.34), r +0.21 at 8 months. The order's ~8-month lead appears weaker than stated, and later. The global PMI is by hand and not in the ledger. |

`tools/validate_ledgers_b6.py` (28/0) holds the following:
- each study reproduces a hand-worked figure on a fixture;
- the classifier and crossing rules are evaluated by code;
- a ledger without its as-of, window or n is refused;
- every study's verdict is the order's, with none invented;
- the package never opens the register or writes the store, so the decision
  tables cannot be touched from it.

### Register lines, drafted under rule 31 (for you to file; I wrote none)

```
ledger: docs/ledgers/st-r5.30b-ledger-2026-10-17.md, NO GATE IN THE ORDER (base rate recorded; R2 0.74, n 266; implied -3.1%/yr) -- laptop run, public sources
ledger: docs/ledgers/st-r5.32b-ledger-2026-10-17.md, NO GATE IN THE ORDER (base rate recorded; 3 episodes, regime ON 2026-10-14) -- laptop run, public sources
ledger: docs/ledgers/st-r5.35b-ledger-2026-10-17.md, NO GATE IN THE ORDER (base rate recorded; 6 peaks, source price) -- laptop run, public sources
ledger: docs/ledgers/st-r5.36b-ledger-2026-10-17.md, NO GATE IN THE ORDER (base rate recorded; n 0 on the order's line, measure ruling open) -- laptop run, public sources
ledger: docs/ledgers/st-r5.43b-ledger-2026-10-17.md, NO GATE IN THE ORDER (base rate recorded; best lead 13m r +0.21, r +0.12 at 8m) -- laptop run, public sources
```

### Box commands, for a re-run of the ledgers

On the box, in the checkout, inside the windows. Each run writes a new dated file
and never edits the laptop's.
```
.venv/bin/python -m altdata.ledgers run all --source public
```
`--source store` reads the store's newest vintages instead. It refuses any study
whose series the store has no key for. Today that is all of them:
- 30b: the Livermore legs;
- 35b: the profits and GVA legs;
- 36b: MSACSR;
- 43b: the full BIS table and the OECD CLI.

So `public` is the re-run to use until those writers exist.

## Box steps, in order (Ari's; Thursday evening, inside the windows)

1. Pull the branch once it is merged. Unit files follow at the next self-deploy
   tick, or run `bash scripts/deploy.sh` from the laptop.
2. Run the restore test and the crypt steps from `audit-leftovers-1`'s notes (box
   steps 1 to 4 there). Running without crypt for at most one night is accepted.
3. Set `CHESTER_RCLONE_OUTBOX_REMOTE` in `.env`: the name of the new drive.file
   remote, not its secret.
4. Create that remote with `rclone config` (drive scope `drive.file`, rooted at
   the Alpha Lab outbox folder). Do not reuse the crypt remote.
5. Let the outbox write through it once (the next nightly sweep), confirm the file
   landed, **then** revoke the old token.
6. Optionally set `CHESTER_MEME_DROP` in `.env`. The default is
   `~/chester-meme/drop`.
7. `.venv/bin/python -m altdata.meme_ingest --dry-run`, then without
   `--dry-run`, then `status`.
8. `systemctl --user enable --now chester-meme-ingest.timer`
9. Check that the next 16:45 close and 07:00 anchor print the meme line.

## Shared files

- **Session A, gtm-core-1.** The branch is not on the remote, so I could not diff
  it. These are this branch's widest-reaching files, and the ones most likely to
  meet it:
  - `CLAUDE.md` (the count line, now 94 code gates: 91 Python, 3 shell; and 7
    data gates);
  - the `Makefile`'s gate list;
  - `metrics_registry.yaml` (`families:`, and the merged entries);
  - `.claude/settings.json` (two deny entries);
  - `tools/decide.py`;
  - `daily_cascade/stack_close.py`, `stack_render.py`, `morning_payload.py` and
    `morning_render.py` (one line each);
  - `scripts/fetch_overnight.sh`;
  - `tools/validate_audit_3a.py`.

  Where gtm-core-1 also changed one of these, take both sides and recount the
  gates.
- **Monday's chain.** Folded once, as listed above. I made no other change to
  it.
- **chester-meme's repository.** Not touched. I read its exported manifest and
  schema only.

## What Part 2 takes

- 31b and 44b: the next two ledgers.
- 30c: the T&B intake queue entry for the allocation extreme, after this ledger
  and "T&B full".
- 44c.
- Pass rules pre-registered for any of the five above, if you want gates.
- The writers the store runs need: the Livermore legs, profits and GVA, the full
  BIS table, and the OECD CLI.

## Needs you

1. **Item 36's measure.** Redfin's own series at 6.0 never crosses. Redfin at its
   80th percentile and Census new homes at 6.0 are both in the ledger. Which one
   is the flag?
2. **Pass rules.** Do you want to pre-register gates for 30b, 32b, 35b, 36b and
   43b? The order has none, so every verdict reads "no gate". Candidates, for you
   to choose from, not adopted:
   - 30b: the slope is negative with R² ≥ 0.5, out of sample after 1990.
   - 32b: n ≥ 5 episodes, and the 126-session mean is below the every-day mean.
   - 43b: r ≥ 0.3 at a lead of 6 to 10 months on both CLIs. On this ledger that
     would fail on both: inside the window the highest r is 0.18 on G20 and
     0.28 on G7, both at 10 months. G7 first reaches 0.3 at 11 months.
3. **The item-25 quadrant is not built.** 32b's quadrant column prints "not
   built".
4. **Missing writers.** No writer exists for the OECD CLI, and the BIS writer
   covers only 11 EM banks. Add writers if 43b is to be re-run from the store.
5. **The git identity.** The shared `.git/config` email is refused by GitHub
   (GH007). Do you want the no-reply address set there? I left the config alone.
6. **File the five register lines above**, if you accept them (rule 31).

## CI

See the next section once the run completes.
