# Incidents

A dated list, newest last, one entry per incident. Started by EL-0 under
`docs/change-order-enterprise-layer-2026-09-27.md` §9; the Monthly's
system-metrics block (§3.7) counts and lists it.

- **INC-1 2026-09-27** — the off-box backup never ran under its unit: `CHESTER_RCLONE_REMOTE` was never set on the box (every 02:30 sweep since deploy ended `no_remote rc=1`), and with it set the snapshot failed because the unit starts in `$HOME` (`ModuleNotFoundError: altdata`). Found by hand 27 Sep; by-hand copy taken 16:04 UTC; drop-in `remote.conf` added by hand; fix B-1 at 61e9b4b; first unit-run proof due 28 Sep 02:30 ET. Monitoring gap: the heartbeat's verdict line had no `backup=` field (H-1 adds it).
- **INC-2 2026-09-27** — narrative prompts were truncated silently from first light until 27 Sep 11:02 ET (style guide cut at 6,000 characters, payload at 12,000); every close since 23 Sep and the first Weekly were written from a partial brief. Editions stand as published (each passed the audits); first whole-brief editions are 28 Sep 07:00 and 16:45. Fix W-1 item 7 at 1846815; a gate now confirms every template and the full Weekly payload reach the model whole.
