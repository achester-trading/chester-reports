"""
The Daily Cascade — the intraday report suite.

Part 32's finding, recorded here because it explains the shape of this package:
**no Daily Cascade code existed.** Every Daily to date was produced inside a
chat session — the operator asked, data was gathered conversationally, prose
came back as an artifact. That is why the reports have been good and why they
have never run without him.

So this is a build, not a migration, and it is sequenced to prove the chain
before trusting the interesting part:

    deliver.py           the delivery layer, built ONCE and used by every run
    payload.py           the store, read as-of, assembled into plain data
    render.py            payload -> HTML. No prose, no interpretation.
    close_report.py      the 16:45 close debrief — the first run (D4c)

    morning_payload.py   the 07:00 anchor's blocks, read from the store
    morning_render.py    its HTML, over render.py's styles and cells
    morning_anchor.py    the 07:00 morning anchor — Phase 1, second slot

The close run is first because its inputs are already computed half an hour
earlier by the EOD pass, so nothing new has to be fetched and the report cannot
fail for a reason the report layer owns. It is DATA ONLY by ruling (32.5):
narrative is added at D4e, after D3's numeral audit exists to fail a block that
invents a number. A Daily that can invent a number is worse than no Daily, and
the way to be sure it cannot is to ship one that contains no sentences.

The morning anchor is the second slot and is deliberately the same shape: the
chain is proven, so this is payload configuration rather than new pipeline. Its
one structural difference is that something has to be fetched before it can run,
and that fetch is a SEPARATE UNIT at 06:45 (altdata/sources/overnight.py) so this
process still cannot fail for a transport reason. A dead fetch becomes a block
that names why it is empty, which is what the reader needs before the open;
silence would be the one outcome that teaches nothing.

It also carries a heartbeat where the close report does not, and the asymmetry is
the point. The close report's inputs are stored and it can be regenerated for any
past session, so a missed one costs an email. The morning anchor publishes a live
overnight read with no second chance: by 09:30 the levels 06:45 would have
captured are gone, and no --session brings them back.
"""
