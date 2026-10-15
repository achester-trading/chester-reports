"""
alpha -- Layer X, the Alpha Lab (change order docs/change-order-alpha-lab-2026-10-12.md).

A machine's book in ledger-paper beside the four books and the five reports. It
reads the observation store READ-ONLY and writes only alpha.db. It has four
restraints and no others: the Brookfield blocklist; ledger entries against
stored prices, with no order path of any kind before the Gate 3 ruling; a risk
governor; an evidence gate. Its constitution (config/alpha_constitution.yaml) is
read by every loop and written by none.

What this package may never do, and the gate that holds it:

  * import an order, gate, broker or network module, or open a socket
    (tools/validate_alpha_no_orders.py, statically and at import time);
  * write to the observation store (alpha/store.py opens it `mode=ro`; the
    store file's hash is unchanged after a nightly run, tools/validate_alpha.py);
  * write the register, the probability ledger, the narrative ledger or any
    report; the Weekly reads one line FROM alpha.db, read-only, and that is the
    only bridge in Tranche 1;
  * touch config/alpha_constitution.yaml.
"""
