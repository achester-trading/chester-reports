# chester-meme ⇄ chester-reports — interface

For whoever builds the ingest on the `chester-reports` side. The controlling text is spec v1 §3 (and §8.2 for
packets) in `docs/meme-scan-spec-v1.md`; this page is the working contract under it.

## The rule

**One-way, through files, both ways.** `chester-reports` writes one file that this repo reads;
`chester-meme` writes into `drop/`, and `chester-reports` reads it.

- `chester-meme` never reads the main store, never calls the main repo and never reads the register.
- `chester-reports` never calls the scan. It reads `drop/` on its own schedule.
- Nothing else is shared except the trade-ledger field layout, and that is only a layout (§3: Book D trades
  stay in `chester-meme/ledger/trades.csv`).

| Direction | File | Writer | Reader | Contract |
|---|---|---|---|---|
| main → meme | `exports/security_master.json` | chester-reports, nightly | chester-meme, read-only | `security_master.schema.json` |
| meme → main | `drop/packets/YYYY-MM-DD/<packet_id>.json` | scan-evening, scan-morning | main register (Book D drafts) | `decision_packet.schema.json` |
| meme → main | `drop/sm-proposals.jsonl` | universe build (Sunday `fuel-weekly`) | main Security Master (adopt or ignore) | `sm_proposal.schema.json` |
| meme → main | `drop/MANIFEST.json` | every packet stage | the ingest, first | below |
| meme → main | `drop/archive/packets/YYYY-MM-DD/` | every packet stage (retention) | optional | as packets |

Paths are relative to the `chester-meme` checkout. On the VPS that is `~/chester-meme/` (user mode, R-T1c-1), and
`/opt/chester-meme/` once root is back. `exports/` and `drop/` are gitignored: they are data, not source.

## When files are written (ET)

| Time | Job | What lands in `drop/` |
|---|---|---|
| 06:30 Mon–Fri | `scan-morning` | packets for transitions in the morning scan. These are the transitions that make the morning note an exception (§8.1 trigger 1). Then `MANIFEST.json` |
| 19:30 Mon–Fri and Sun | `scan-evening` | packets for the evening scan's transitions, then `MANIFEST.json` |
| Sun 16:30 | `fuel-weekly` | new lines in `sm-proposals.jsonl` (universe rebuild) |

Each scan writes its packets, archives old ones and rewrites the manifest before the note is sent:

- **Evening:** finished by about 19:45, a few minutes after the 19:30 start.
- **Morning:** finished by 06:45.

Read `drop/` after **20:15** and **07:00 ET** to be safe. A late scan only adds files: nothing written earlier ever
changes.

## Packets — `drop/packets/YYYY-MM-DD/<packet_id>.json`

**What a packet is.** One file per *alerted* transition into **Ignition** (`direction: long`) or **Climax**
(`direction: short`). It follows the Decision Packet shape of §8.2 and is validated against
`decision_packet.schema.json` before it is written; a packet that fails validation is not written.

**What is not packeted.**
- Acceleration and Decay transitions.
- A transition held back by the five-day cooldown (§7.4). It is counted in the manifest as `suppressed`.
- Replays of past scans.

**It is a draft.** `book: "D"`, `status: "draft"`. There is no size, stop, target or probability, and the schema
forbids those keys (`no_sizing`). Whether a packet becomes anything is the register's decision (§2, §8.2).

**Fields the ingest needs**

| Field | Meaning |
|---|---|
| `packet_id` | `pk-` + first 20 hex of sha256(`security_id\|transition\|as_of\|rule_version`). **The idempotency key.** |
| `as_of`, `session` | the scan (ET date; `am` 06:30 or `pm` 19:30). The folder is `as_of`. |
| `security_id` | composite FIGI: the same key as the Security Master export. `ticker` is the ACT form at the scan. |
| `direction`, `phase`, `transition` | `long`/`ignition` or `short`/`climax`; `transition` e.g. `dormant->ignition` |
| `rule_version`, `feature_version` | the rules that fired (`chester-meme/ledger/rule-log.md`) |
| `thesis` | plain sentences built from the rule; not a forecast |
| `evidence[]` | each item has `source`, `kind`, `event_date`, `available_at` (UTC, never after the scan's cutoff) and `url`. Kinds: `rule_arm`, `condition`, `filing`, `insider_sale`, `headline`, `borrow`, `rule201`. |
| `fuel` | susceptibility with its F1–F5 attribution, supply risk (F6) and listing flags (F7), as of the latest weekly fuel row. `quality: missing` when there is none. |
| `spark` | the arms and conditions of the rule (fired or not), the board score and its components, and a feature snapshot with quality |
| `flags[]` | `supply_risk:*`, `listing:*`, `tradability:*` (sub-dollar, spread, halts, suspension); for shorts also `borrow:*` (an IBKR snapshot, not the borrow market) and `rule201:*` |
| `quality` | `ok`, or `incomplete` when the scan was incomplete (a critical feed or a stage failed). `quality_detail` lists stale and missing inputs either way. |
| `expires` | `as_of` + 5 NYSE trading days (holidays by rule; unscheduled closures not known) |

**Encoding.** UTF-8, LF line endings, pretty-printed JSON. Unknown top-level keys are refused by the schema
(`additionalProperties: false`); a new field means a new `schema_version`.

## Idempotency and immutability

- **Fixed id.** The same scan, rerun, produces the same `packet_id` and writes nothing new. Each id is listed in the
  scan's own register (`packet` table).
- **Files never change.** A file, once written, is never rewritten, even after a store restore: the file on disk wins.
  Ingest by `packet_id`, and a second sighting is a no-op.
- **Writes are atomic.** Each file is written to `<name>.tmp`, then renamed. **Ignore `*.tmp`.**
- **Withdrawn alerts stay.** A packet is never withdrawn. If a later scan reclassifies the name, that shows up as a
  new transition: a new packet, or none. Use `expires` to stop showing old drafts.

## Retention

Packet folders stay in `drop/packets/` for **90 days** (`[packets] retention_days`) after their date. After that,
each scan moves them to `drop/archive/packets/YYYY-MM-DD/`, unchanged. Nothing is deleted. The nightly backup does
not upload `drop/`, so the main repo's ingest is the durable copy.

## `drop/MANIFEST.json`

Rewritten atomically at the end of every packet stage. Read it first.

```json
{
  "manifest_version": "1.0",
  "producer": "chester-meme 0.1.0",
  "updated_at": "2026-10-15T00:01:12Z",
  "rule_version": "1.0.0",
  "schemas": {"decision_packet": {"version": "1.0", "path": "docs/interface/decision_packet.schema.json", "sha256": "…"},
              "sm_proposal": {"version": "1.0", "path": "docs/interface/sm_proposal.schema.json", "sha256": "…"}},
  "packets": {"dir": "drop/packets", "in_drop": 3, "by_date": {"2026-10-14": 3}, "latest_as_of": "2026-10-14",
              "latest_session": "pm", "archived": 0, "retention_days": 90, "archive_dir": "drop/archive/packets"},
  "sm_proposals": {"path": "drop/sm-proposals.jsonl", "lines": 0},
  "last_run": {"as_of": "2026-10-14", "session": "pm", "written": 3, "existing": 0, "suppressed": 0, "failed": 0,
               "finished_at": "2026-10-15T00:01:12Z"}
}
```

`sha256` is taken over the schema file with LF line endings. When it or `version` changes, re-read the schema.

## Security Master proposals — `drop/sm-proposals.jsonl`

One JSON object per line, appended and never rewritten; each FIGI appears once. These are names the universe build
met (Nasdaq Trader directories + OpenFIGI) that `exports/security_master.json` lacks. Lines are written only once an
export has been imported; until then the file is empty or absent, because every name would otherwise be a proposal.

| Field | Meaning |
|---|---|
| `figi` | the composite FIGI |
| `ticker` | ACT form |
| `type` | the type the export uses |
| `venue` | listing venue |
| `first_seen` | the first date the scan's universe build saw it |
| `reason` | why it is proposed |

`name`, `cik`, `type_source`, `test_issue`, `proposed_at` and `source` are also present. Lines written before T5
(2026-10-14) lack `first_seen` and `reason`. Adopt or ignore each line; the scan never writes the main Security
Master.

## The Security Master export, as this repo reads it

`exports/security_master.json` (override with `$MEME_SM_EXPORT`), in the shape of `security_master.schema.json`.
`scan-evening` reads it each night, read-only; an unchanged file (same SHA-256) is not imported twice.

**The guard (R-T1a-3).** Bars and short volume backfilled before 2026-10-11 were mapped on the assumption that no
ticker changed hands. The guard checks that assumption against the export's `ticker_history`, row by row:

| What the export shows for the row's ticker on the row's date | What happens to the row |
|---|---|
| a different single holder | remapped to that holder |
| no single holder | `security_id` set to NULL, `map_basis` set to `ambiguous` |
| the same holder as the row (the export agrees) | never touched |

Every change is logged with its old value.

**What `chester-reports` needs to know.**
- **`effective_to` must be exact.** Make `effective_to` (exclusive) accurate for reused tickers. That one field is
  what lets the scan repair two years of history.
- **Tickers in ACT form.** Use the ACT form (`BRK.B`, `ABR$D`, `AAC.W`), as the Nasdaq Trader directories do.
- **No export, no guard.** When the file is absent the guard does nothing and records `skipped`.

## What the main repo needs to build (change-order path, §12 decision 3)

1. **The nightly export.** Write `exports/security_master.json` into the `chester-meme` checkout, or anywhere if
   `MEME_SM_EXPORT` points to it, before 19:30 ET. It must validate against `security_master.schema.json`.
2. **A packet ingest.** After 20:15 and 07:00 ET it should:
   - read `drop/MANIFEST.json`;
   - for each `drop/packets/*/pk-*.json` not yet seen (by `packet_id`), validate it against the schema version the
     manifest names;
   - register it as a **Book D draft**, keyed by `packet_id`, keeping `security_id`, `direction`, `expires`,
     `quality` and the evidence URLs.
   - Skip `*.tmp`. It must not write into `drop/`.
3. **Optional: a proposals review.** Read new lines of `sm-proposals.jsonl`. Then either adopt each FIGI into the
   Security Master, which makes it appear in the next export, or ignore it.
4. **The trade link.** When a Book D trade is taken off a packet, record the `packet_id` in `chester-meme`'s
   `ledger/trades.csv` (`trade add --packet-id`), so alert, packet and trade join on one key.
