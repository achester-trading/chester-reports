# sm-schema-1-1 — session notes (session A, 16 Oct 2026)

**Merge order:** this branch is cut from `aud-3b-security-master`'s tip, `2fb1048`, the end of next week's chain. It merges **after aud-3b**, as the chain's tenth link. The branch was not merged or deployed, and nothing ran on the box. aud-3b itself is untouched.

**What Ari passed on:** chester-meme's five points after its T5d build. The change order is `docs/change-order-sm-schema-1-1-2026-10-16.md`.

| # | Point | Done |
|---|---|---|
| 1 | Never write into the chester-meme folder; the interface is files only | Added to CLAUDE.md, after the Security Master paragraph. Session B confirmed it had not added the line. |
| 2 | Migration 0008 kept, 0009 adds the rest | Noted. Nothing to do here. |
| 3 | Schema 1.1: `restricted` and `restricted_reason` | Adopted. The schema is at 1.1, and the export writes `restricted` on every security and `restricted_reason` where it is true, from the register's own rule. |
| 4 | Tracking views still show restricted names | Recommendation below. Nothing built. |
| 5 | Ruling: yes to the new-listing start date | Applied in `altdata/ticker_history.py`: a new listing starts the day after the previous snapshot. |

## Changes

- `docs/interface/security_master.schema.json` goes to 1.1:
  - `schema_version` is an enum of "1.0" and "1.1";
  - the two optional properties are added, with chester-meme's descriptions;
  - the example is at 1.1.
- The new SHA-256 is `e90e55fecf83a88d0039e3a8206ced48ec38ba135409cee5a13947c5eb14b712`.
- `altdata/sm_export.py`: `schema_version` "1.1". The new `reason_of()` produces "Brookfield complex: tier N, root X", or "…: name match on 'brookfield'".
- `altdata/ticker_history.py`: the new-listing start date. A reused ticker's new holder still opens on the snapshot date, so no two holders overlap.
- `tools/validate_security_master.py`, five checks added:
  - every security carries `restricted`, and a reason only where it is true;
  - the reason's form, for OCSL and for a name match;
  - a 1.0 document still validates against 1.1;
  - a new listing after two missed mornings starts the day after the previous snapshot;
  - a reuse still has no overlap.

  The pin moved to 1.1. Run locally: **87 passed, 0 failed**.
- CLAUDE.md: the export paragraph names 1.1 and the start-date ruling, and the chester-meme rule follows it.

## Needs you

1. **Point 4, the tracking views. My recommendation is to mark restricted names, not hide them.**
   - **Why mark:** a marked name shows the restriction is working. A hidden name looks the same as a name the scan never saw.
   - **Where enforcement happens:** at the packet stage and in `trade add` on chester-meme's side, and at the register's write here, never in a view.
   - **Why it's chester-meme's to build:** its tracking views are its own. Hand it "mark restricted names in the tracking views (e.g. `restricted: no packet, no trade`), never hide them" if you agree.
   - **On this side:** no report view lists a restricted name as a candidate. The register refuses them, and `config/tracked_entities.yaml`'s monitoring is deliberate.
2. **chester-meme's copy of the schema.** It should copy this branch's `docs/interface/security_master.schema.json` byte for byte once the branch merges. The SHA above is the check.
3. **The box.** Nothing changes there until the merge. The next 06:45 export after the merge writes 1.1. chester-meme's `meme env-check` and its next evening import are its own to run.

## CI

| Run | Commit | Result |
|---|---|---|
| (first push) | — | recorded at the next read |
