"""The Alternative Asset report's designed report layer -- content, not a pipeline.

Vendored unchanged from the 3 September 2026 package. NOTHING RUNS THIS: no
scheduler, no Makefile target, and no other module in this repo imports it.
Seven of the thirteen modules do not import at all against the current
altdata/ -- they want `altdata.analytics`, which does not exist here, and
`altdata.config.ASSETS` / `ASSETS_BY_ID` / `BENCHMARKS`, which this repo's
config.py does not define. That is expected and is not a bug to fix in place.

It is kept for what it holds -- the narratives, the case and positioning
material, the peer and source tables, the weekly scan's prompt -- against
folding the Alternative Asset report into the Monthly under the system
redesign. See CLAUDE.md's Known cleanup.

This docstring is the only edit to the snapshot; the other twelve modules are
byte-identical to the package.
"""
