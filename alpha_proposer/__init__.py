"""
alpha_proposer -- the Alpha Lab's daily proposer (X-2.10b; change order 10.2).

A package of its own, OUTSIDE alpha/, because it makes a network call (the one
model call a session day) and alpha/ may not import anything that can:
tools/validate_alpha_no_orders.py holds alpha/ to no network import at all, and
stays as strict as it was. This package reads the store and alpha.db read-only
(it imports alpha.store, alpha.rules, alpha.hypotheses and alpha.intake for their
read-only checks), writes only the lab's inbox and its own log, imports no order
gate, no broker module and no harness, and never sees a test result
(tools/validate_alpha_proposer.py).

    python -m alpha_proposer [--as-of ISO] [--store PATH] [--ledger PATH]
"""
