# Change Order — Security Master export, schema 1.1: `restricted` and `restricted_reason`

| | |
|---|---|
| Status | **Proposed by chester-meme on 16 Oct 2026** in its T5d session report (`docs/sessions/t5d-report.md` in that repository, "Proposed: security_master.schema.json 1.1"). Ari passed it to session A on 16 Oct. It is adopted on branch `sm-schema-1-1` and takes effect when that branch merges. |
| Amends | `docs/interface/security_master.schema.json` (1.0 to 1.1), `altdata/sm_export.py`, `altdata/ticker_history.py` (the new-listing ruling, section 4), CLAUDE.md |
| Owner | Ari Chester |
| Binding on | Both sessions in this repository, and chester-meme's import |
| Precedence | Below Part 26 and the AUD-3b order. This order amends the interface contract only. |

## 1. What changes

Each item of `securities[]` gains two optional properties, and `schema_version` accepts `"1.1"`:

| Field | Type | Meaning |
|---|---|---|
| `restricted` | boolean | true means a standing trading restriction applies (the Brookfield complex). It is written on every security, false included. Where it is present, it decides the security in chester-meme. Where it is absent, there is no statement, and chester-meme's own list decides. |
| `restricted_reason` | string or null | A short free-text reason, e.g. `Brookfield complex: tier 1, root BN`. It is written only when `restricted` is true. |

Nothing else changes. The schema keeps `schema_version` as an enum of `"1.0"` and `"1.1"`, so a 1.0 document still validates against 1.1, and the gate proves it. The manifest does not change.

## 2. Where the values come from

The values come from the same rule the register enforces at write time: `register/instruments.py` over `config/tracked_entities.yaml`. It checks every ticker the security has held and its names.

The full restricted list is:
- tiers 1–3: the twelve core and affiliate roots, the BPY family and its preferreds, DTLAP, and the BNH/BNJ/BEPH–J/BIPH–J notes;
- tier 4: OAK, OCSL and BIRET;
- RA and INF, by name only;
- the name net on "Brookfield" and "Oaktree".

A root match records the tier and root in the reason; a name match records the pattern. The export already wrote `restricted` as a field 1.0 allowed. This order makes it part of the contract and adds the reason.

## 3. The contract file, byte for byte

The 1.1 schema is authored here. Its SHA-256, taken over the file with LF endings, is
`e90e55fecf83a88d0039e3a8206ced48ec38ba135409cee5a13947c5eb14b712`, pinned in `tools/validate_security_master.py` group G. The 1.0 pin was `5288446f…5e78fb2`.

chester-meme bumps its own copy by copying this file's bytes; no session here writes there (CLAUDE.md). Until it does, the two copies differ, which is harmless: chester-meme's import does not pin the version string and already reads the field.

## 4. Ruling recorded: the new-listing start date (aud-3b Needs-you 9)

**Ruled yes, 16 Oct 2026, relayed from the chester-meme side.** A new listing, meaning a FIGI first seen after the first snapshot, starts **the day after the previous snapshot** rather than on the snapshot date. If mornings are missed, the start is early, never late, so chester-meme's guard never nulls the new listing's rows.

On consecutive trading days the only difference is the weekend's calendar days, on which nothing trades. A reused ticker's new holder still opens on the snapshot date, where the old holder's row closes, so no two holders overlap. `from_known` stays true.

## 5. Not in this order

- **Tracking views** (chester-meme's point 4) are recorded in `docs/briefs/sm-schema-1-1-notes.md` as a recommendation for Ari; nothing is built for them.
- **chester-meme's file bump** belongs to its own session.
