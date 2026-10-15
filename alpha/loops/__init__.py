"""
The lab's loops (the brief's section 8). Tranche 1 builds the nightly loop
(nightly.py) and the weekly loop's first duty, the allocator's rebalance
(weekly.py); the weekly re-fit and research agenda are X-2.4's, the fortnightly
innovation loop X-2.7's, the quarterly meta-loop X-3.7's.

Every loop runs as its own systemd unit on its own timer, never inside a
report's run; a loop that fails writes its failure to loop_events and touches
nothing else.
"""
