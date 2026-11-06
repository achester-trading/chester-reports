"""
paper_exec -- the paper-only IBKR executor (A98; D43, ruled 31 Oct 2026).

A thin, separately audited executor on ib_async, in its own package OUTSIDE
alpha/ (D43 b): the lab never imports it, and tools/validate_alpha_no_orders.py
keeps alpha/ absolute. No live order before 2027; Claude stays out of the
execution path; a session never places an order (the deny list names this
package's run and clear-kill commands). No timer, no unit, no feed hook in this
tranche: it runs only by hand on the box, after the merge, in dry mode.

THE RULES, EACH IN CODE AND EACH WITH A FIXTURE (tools/validate_paper_exec.py):

  1. PAPER ONLY. The port must be one of the config's paper ports before any
     connection (client.connect); after connecting, every account the gateway
     reports must begin with "DU", or the session is closed and LiveAccount
     raised -- with the reason logged, before any order object is built.
  2. OFF BY DEFAULT. `enabled: false` ships: nothing connects, and the status
     command prints "paper executor off".
  3. DRY BY DEFAULT. `dry_run: true` builds and logs every intended bracket
     (contract, side, size, entry, stop, target) and sends nothing. Sending needs
     both flags set by the operator in config: enabled true, dry_run false.
  4. BRACKETS ONLY. An entry is a parent with its stop and its target attached,
     or it is not sent (orders.check, executor._send).
  5. SIZE. The config's contract ceiling, the Doctrine's heat cap over the open
     paper risk (config/risk_limits.yaml), and the lab's governor: a halted lab
     or a frozen engine refuses, a halved engine halves. MES only: ES is refused
     by contract.
  6. THE KILL SWITCH. A `kill` file in the state directory stops all sending
     within one loop and writes `killed`, sticky until the operator clears it.

And before any send: RECONCILIATION (reconcile.py) -- the gateway's positions
and open orders against the ledger and the executor's order log; a mismatch
stops sending and names it. And the EDGE-DECAY PAUSE (pause.py, D43): an engine
whose last 20 paper trades fall two standard errors below its backtest sends
nothing until the operator resumes it.

Fills come back into the lab's ledger (fills.py), `source = paper_exec`, with the
venue's order id and the fill's time.
"""
