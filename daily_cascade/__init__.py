"""
The Daily Cascade — the intraday report suite.

Part 32's finding, recorded here because it explains the shape of this package:
**no Daily Cascade code existed.** Every Daily to date was produced inside a
chat session — the operator asked, data was gathered conversationally, prose
came back as an artifact. That is why the reports have been good and why they
have never run without him.

So this is a build, not a migration, and it is sequenced to prove the chain
before trusting the interesting part:

    deliver.py        the delivery layer, built ONCE and used by every run
    payload.py        the store, read as-of, assembled into plain data
    render.py         payload -> HTML. No prose, no interpretation.
    close_report.py   the 16:30 close debrief — the first run (D4c)

The 16:30 run is first because its inputs are already computed twenty minutes
earlier by the EOD pass, so nothing new has to be fetched and the report cannot
fail for a reason the report layer owns. It is DATA ONLY by ruling (32.5):
narrative is added at D4e, after D3's numeral audit exists to fail a block that
invents a number. A Daily that can invent a number is worse than no Daily, and
the way to be sure it cannot is to ship one that contains no sentences.
"""
