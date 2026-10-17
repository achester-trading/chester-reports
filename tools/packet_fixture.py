"""
A complete EL-1 packet for the gates' fixtures (register/store.py ENTRY_FIELDS).

A fixture that records a DECISION_OK (active) decision passes these, beside its
own instrument, thesis, setup and size: since EL-1 (12 Oct 2026) the register
refuses an active decision without the whole decision object, so a fixture that
predates it would be refused for a reason that has nothing to do with what it
tests. Synthetic text, no figure anyone acts on.

    from packet_fixture import PACKET, PACKET_CLI
    reg.record(..., status="active", setup_id="b_breakout", **PACKET)
"""

from __future__ import annotations

# Keyword arguments for Register.record(). Not setup_id, size or the
# falsifiers/counter_thesis a fixture already names: those stay the fixture's.
PACKET = {
    "mechanism": "fixture mechanism: dealers are long gamma and suppress the move",
    "falsifier_date": "2099-12-31",
    "expected_return": "+3% over the horizon (fixture)",
    "expected_downside": "-1.5% at the invalidation (fixture)",
    "entry_condition": "fixture entry: a close above 100",
    "risk_budget": "0.5% of the book (fixture)",
    "benchmark": "SPY (fixture)",
    "red_team": "fixture red team: the move is the index's, not the name's",
    "red_team_review_minutes": 15,
}

# The same, as decide.py record flags.
PACKET_CLI = [
    "--mechanism", PACKET["mechanism"],
    "--falsifier-date", PACKET["falsifier_date"],
    "--expected-return", PACKET["expected_return"],
    "--expected-downside", PACKET["expected_downside"],
    "--entry-condition", PACKET["entry_condition"],
    "--risk-budget", PACKET["risk_budget"],
    "--benchmark", PACKET["benchmark"],
    "--red-team", PACKET["red_team"],
    "--red-team-minutes", str(PACKET["red_team_review_minutes"]),
]

# With the setup and the size too, for a fixture that names neither.
PACKET_FULL = {**PACKET, "setup_id": "unclassified", "size": "fixture size"}
# A falsifier the measurable rule accepts (it names a level).
FALSIFIER = "fixture falsifier: a close below 95"
