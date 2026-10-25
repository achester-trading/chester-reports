# A70: the record of Post-Freeze Amendment #3 (24 Oct 2026, overnight)

Docs only and branch-only. `a70-amendment-3-record` branches from `origin/a69-readers-guide-4` at its tip, `cfd95af2`.

**A69's CI at A70's start.** Run `40151163517` was queued, and was not waited on.

## What was searched, and the result

**The order was not found under any name.** The search used `git grep` across `origin/main`, `origin/chain-7`, the four library branches and this branch, for "Amendment #3", "amendment-3", "AI trajectory", "Internal Order", "Factor VI", "consensus drift" and "I-b". The hits fall into three groups:

- **Pointers to the order:**
  - the work plan v3 (line 44);
  - GTM-11's placement with "Amendment #3 workstream B" (the GTM order, lines 25 and 49; the register, line 750; the gtm-core notes);
  - SR-11, consensus drift (the 25 Sep order, lines 262, 422 and 1082; the register, line 265);
  - the chat-side consensus-drift scan (the Master Guide, line 149);
  - the reading shelf's AI and Internal Order groups;
  - Batch 5 item 18 and Batch 6 item 38.
- **A different order with the same number.** The architecture document's Part 29, "Change Order #3: Eight Tactical Additions (post-freeze amendment #3)", 5 Sep 2026. It is not this order.
- **No order file and no architecture Part.** Audit #4's agenda carries no line for the ten-item work order.

**So a record was written:** `docs/change-order-amendment-3-2026-09-13-record.md`. It is indexed in `docs/change-orders.md` as "Record only; original pending", in date order (13 Sep, first).

## What of the two workstreams is built

**Workstream A** (the I-b inputs, consensus drift):
- **Built in part.** The b59 "Factor I-b: open model releases" block is on chain-7, and the reading shelf's AI group exists.
- **Specified only.** GTM-20, the AI adoption markers.
- **Neither built nor scheduled.** Consensus drift: SR-11 is reserved, and only the interim chat-side scan runs.

**Workstream B** (Internal Order as Factor VI):
- **Specified only, as a name.** The reading shelf's internal-order group and the Slow-layers name.
- **Not built.** The Monthly panel, with GTM-11 and SR-55 reserved. Its K-shape line prints as a listed gap.
- **Drafted, not merged.** XXVII's internal-order lens is in Draft 1 on `origin/library-xxvii`, session B's.

## The cross-references

- **The Doctrine #2 pack** (A67), in its register section (Part 5, above Table 5.2): "Amendment #3's filing: record only; original pending."
- **Paper XXVII's notes** (`docs/briefs/library-xxvii-notes.md` on `origin/library-xxvii`; that branch is not touched). The line for it is filed here, for that branch's session to copy: "Amendment #3's filing: record only; original pending (`docs/change-order-amendment-3-2026-09-13-record.md`, A70, 24 Oct 2026); XXVII's §2.3 internal-order lens rests on the references that record lists."

## Gates

`check_library`: run below.

## CI

| Run | On | Result |
|---|---|---|
| read once after the push | the A70 tip | see the report |

## Needs you

1. **The original order** from the 13 Sep chat, to be filed verbatim beside the record.
2. **The number:** two orders are called "amendment #3" (the architecture's Part 29 of 5 Sep, and this one of 13 Sep).
