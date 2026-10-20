# meme-ingest: chester-meme's packets in as Book D drafts (17 Oct 2026)

Part 0 of `meme-ingest-ledgers-1`. The branch report is
`docs/briefs/meme-ingest-ledgers-1-notes.md`. This file covers only the ingest:
what it does, the fold it stands on, the box steps, and the message for the meme
session.

## What it does

`altdata/meme_ingest.py` reads `$CHESTER_MEME_DROP` (default
`~/chester-meme/drop`). It never writes into that directory. It runs in this
order:

1. **The manifest first.** The manifest names its schema. That schema must be
   `docs/interface/decision_packet.schema.json` at the same version (1.0) and the
   same LF SHA-256 (`e3e97e0e…9522`). If either differs, nothing is read, and the
   refusal is logged as `read`.
2. **Restricted packets are refused.** That means `restricted: true`, or any
   `restricted:*` flag. The packet is logged in `meme_refusals` (kind
   `restricted`) and never stored.
3. **Brookfield-blocklisted names are refused.** The check runs through the
   register's own `Restrictions.check` on ticker, name and security_id, by root
   or by name, aliases included. The refusal is logged (kind `blocklist`).
4. **Schema-invalid packets are skipped and logged** (kind `schema`), never
   repaired. The announced `restricted` field is checked as a boolean, then set
   aside before the 1.0 validation, because 1.0 does not declare it.
5. **Everything else becomes one `meme_drafts` row per `packet_id`.** A second
   sighting writes nothing, so the ingest is idempotent.

**The tables live in the register database. Neither is a decision table.**
- `meme_drafts` has a trigger that refuses any instrument in
  `restricted_instruments`. This is the write-time invariant, the same as the
  register's. Its packet columns are immutable and no row can be deleted. Only
  the review columns change: awaiting, then confirmed or rejected.
- `meme_refusals` is immutable.
- `tools/validate_meme_ingest.py` diffs every other register table before and
  after a run.

**The operator's verbs.** Both are on `.claude/settings.json`'s deny list:
- `decide.py record --meme-packet <id> ...` confirms a draft. It checks the
  draft's instrument, direction and Book D, then writes the decision through the
  register's normal path, so the blocklist runs again.
- `decide.py meme-reject <id> --reason "..."` rejects a draft.

`decide.py meme-drafts [--all]` is read-only.

**The line the reports print.** The 16:45 close's header and the 07:00 anchor's
subtitle print "meme drafts awaiting review: n (refused: m)". Here m counts the
refusals from the last 7 days (`REFUSED_WINDOW_DAYS`).

**When it runs.**
- At 21:45 ET, through `chester-meme-ingest.timer`. It is **held back**: the timer
  is not in `DEPLOY_TIMERS`, and you enable it by hand.
- At the end of the 06:45 overnight pass (`scripts/fetch_overnight.sh`, after the
  pulls), so a packet from the evening scan is counted before the 07:00 anchor
  prints.

## The fold it stands on

Monday's chain tip `8f53e6b` was folded once, as ruling 5 said: aud-3a, aud-3c,
aud-3d, alpha-lab-2, t3-6, vp-1 and aud-3b. Where the same line differed, the
chain's version won and this line's additions were kept. The list of files and
how each was resolved is in the branch report.

## Box steps (Ari's; nothing here was run on the box)

1. Optionally put `CHESTER_MEME_DROP` in `.env`, set to the meme checkout's drop
   directory. Without it, the default is `~/chester-meme/drop`. This step names
   the variable only; it sets no value.
2. Take the first read by hand, in the box's checkout, in this order:
   ```
   .venv/bin/python -m altdata.meme_ingest --dry-run
   .venv/bin/python -m altdata.meme_ingest
   .venv/bin/python -m altdata.meme_ingest status
   ```
3. Enable the timer, once the unit files have reached the box (by the
   self-deploy, or `bash scripts/deploy.sh` from the laptop):
   `systemctl --user enable --now chester-meme-ingest.timer`
4. Check that the next close and anchor carry the line.

## Message for the meme session

The meme session works in its own repository, and I did not touch it. Please pass
this on:

> The chester-reports ingest is built (branch meme-ingest-ledgers-1, not merged).
> It reads your drop directory and manifest, and holds you to these:
> 1. **Keep the manifest's schema at 1.0 with SHA-256 e3e97e0e…9522 (LF).** If
>    you change the schema, bump its version and its SHA. The ingest refuses the
>    whole drop when either differs from the copy in chester-reports'
>    `docs/interface/`, so a schema change needs a matching change on our side.
> 2. **`restricted` is read now as an announced extension (a boolean).** Please
>    add it formally to the schema as 1.1, and we will adopt that copy.
> 3. **A packet's file name is its `packet_id`.** The ingest keys on `packet_id`.
>    A second file with the same id is ignored, so never reuse an id.
> 4. **Write atomically.** Write to `<name>.tmp` and rename. The ingest skips
>    `.tmp` files.
> 5. **Never rewrite a packet file.** A draft's packet columns are immutable. A
>    corrected packet needs a new `packet_id`.
> 6. **Restricted and Brookfield-blocklisted names are refused on our side,
>    whatever the packet says.** Restricted packets are refused before the
>    schema check runs.
