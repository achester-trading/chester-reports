"""
Validation gate for the executions table and the fill read.

Entirely mocked: no Gateway, no network, no fills. It proves the POLICY, which is
the part that would fail silently -- a fill read that drops a commission, or an
execId collision that overwrites a price, produces a plausible-looking table that
is wrong about money.

  A  READ-ONLY IS PRESERVED. Adding a second read must not add an order path.
     The source is searched for order-placing calls the same way
     validate_ibkr_portfolio.py does it, because this change is exactly the kind
     that could smuggle one in.
  B  execId IS THE KEY. Re-syncing is a no-op; a partial fill is several rows,
     not an averaged one; a row with no execId is refused rather than invented.
  C  COMMISSION ARRIVES LATE AND IS NEVER OVERWRITTEN. IBKR delivers the report
     on its own schedule, so a NULL must be completable -- and a recorded value
     must be immutable, because a fill is a fact.
  D  THE INSTRUMENT KEY MATCHES PORTFOLIO TRUTH. A fill has to join the position
     it moved. This is the 17 September case: `SPY` would have matched both
     listings and identified neither.
  E  A FILL READ THAT FAILS COSTS NO POSITIONS. Knowing what is held is the
     service's first duty; the fills are the second and must degrade alone.
  F  TIME IS THE BROKER'S, IN UTC. A fill at the open read at 16:30 is a fact
     about the open.

    python tools/validate_executions.py
"""

from __future__ import annotations

import datetime as dt
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import executions                       # noqa: E402
from altdata.sources import ibkr_portfolio as ibkr    # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78


def ok(m: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    ok(m) if c else bad(m)


class _Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def fill(exec_id, *, side="BOT", shares=100.0, price=762.45, commission=1.05,
         con_id=756733, currency="USD", venue="ARCA", local="SPY",
         when="2026-09-21T13:31:02+00:00", realized=None):
    """One ib_async-shaped Fill."""
    return _Obj(
        contract=_Obj(conId=con_id, symbol="SPY", localSymbol=local,
                      secType="STK", currency=currency, primaryExchange=venue,
                      exchange=venue),
        execution=_Obj(execId=exec_id, acctNumber="DUP735780", orderId=41,
                       permId=990041, exchange=venue, side=side, shares=shares,
                       price=price, avgPrice=price, cumQty=shares,
                       time=dt.datetime.fromisoformat(when), orderRef=None,
                       lastLiquidity=1),
        commissionReport=(None if commission is None else
                          _Obj(execId=exec_id, commission=commission,
                               currency="USD", realizedPNL=realized)),
    )


def row(*a, **kw) -> dict:
    """One fill as the STORE takes it -- through the real reader, deliberately.

    Going via _read_fills() rather than hand-writing a dict means these cases
    exercise the mapping from broker object to row as well as the table. A
    hand-built dict would keep passing after the reader stopped populating a
    field.
    """
    return ibkr._read_fills(FakeIB([fill(*a, **kw)]))[0]


class FakeIB:
    """Serves canned account state and canned fills."""

    def __init__(self, fills=None, fills_raise=None):
        self._fills = fills if fills is not None else []
        self._raise = fills_raise
        self.disconnected = False
        self.connect_kwargs = None
        self.exec_filter_seen = False

    def connect(self, host, port, clientId=None, timeout=None, readonly=None):
        self.connect_kwargs = {"readonly": readonly, "port": port}

    def managedAccounts(self):
        return ["DUP735780"]

    def accountSummary(self):
        return [_Obj(account="DUP735780", tag="NetLiquidation",
                     value="1013838.41", currency="USD")]

    def portfolio(self):
        return [_Obj(account="DUP735780", position=100.0, averageCost=769.07,
                     marketValue=76297.0, unrealizedPNL=-610.0,
                     contract=_Obj(conId=756733, symbol="SPY", localSymbol="SPY",
                                   secType="STK", currency="USD",
                                   primaryExchange="ARCA"))]

    def reqExecutions(self, *a):
        self.exec_filter_seen = bool(a)
        if self._raise:
            raise self._raise
        return list(self._fills)

    def disconnect(self):
        self.disconnected = True


def group_a() -> None:
    print(f"{LINE}\nA. READ-ONLY IS PRESERVED BY THE NEW READ\n{LINE}")
    text = (REPO / "altdata" / "sources" / "ibkr_portfolio.py").read_text(
        encoding="utf-8")
    # Docstrings and comments stripped first, exactly as
    # validate_ibkr_portfolio.py does it: this module's own docstring says it
    # "never calls placeOrder", and a check that trips on the sentence promising
    # the property is a check somebody deletes.
    src = re.sub(r'""".*?"""', "", text, flags=re.S)
    src = re.sub(r"#.*", "", src)
    for call in ("placeOrder", "bracketOrder", "MarketOrder", "LimitOrder",
                 "StopOrder", "qualifyContracts("):
        check(call not in src, f"no {call} anywhere in the source")
    check("reqExecutions" in src, "reqExecutions IS present -- reading fills is "
                                  "the point, and reading is not ordering")
    ib = FakeIB()
    ibkr.connect(port=4002, ib_factory=lambda: ib)
    check(ib.connect_kwargs["readonly"] is True,
          "the client is still constructed readonly=True")


def group_b() -> None:
    print(f"\n{LINE}\nB. execId IS THE KEY\n{LINE}")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        db = str(Path(d) / "x.db")
        with executions.ExecutionStore(db) as st:
            r1 = st.write_many([row("0001.01"), row("0001.02", price=762.50)])
            check(r1["inserted"] == 2, f"two execIds -> two rows ({r1})")
            check(st.count() == 2,
                  "A PARTIAL FILL IS SEVERAL ROWS, not one averaged one -- they "
                  "happened at different prices and the average is derived")

            r2 = st.write_many([row("0001.01"), row("0001.02", price=762.50)])
            check(r2["inserted"] == 0 and r2["already_known"] == 2,
                  f"re-syncing the same fills is a no-op ({r2})")
            check(st.count() == 2, "and adds no rows")

            # A price must not be rewritten by a later read claiming otherwise.
            st.write_many([row("0001.01", price=999.99)])
            got = [r for r in st.latest() if r["exec_id"] == "0001.01"][0]
            check(abs(got["price"] - 762.45) < 1e-9,
                  f"a stored fill's PRICE is immutable ({got['price']}) -- the "
                  f"broker's first complete version is the record")

            r3 = st.write_many([row(None), row("")])
            check(r3["inserted"] == 0,
                  "a fill with no execId is refused, not given a synthetic key")


def group_c() -> None:
    print(f"\n{LINE}\nC. COMMISSION ARRIVES LATE, AND IS NEVER OVERWRITTEN\n{LINE}")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        db = str(Path(d) / "c.db")
        with executions.ExecutionStore(db) as st:
            st.write_many([row("0002.01", commission=None)])
            got = st.latest()[0]
            check(got["commission"] is None,
                  "a fill whose report has not arrived stores commission NULL")
            check(len(st.missing_commission()) == 1,
                  "and is listed by missing_commission(), so the gap is "
                  "surfaceable rather than invisible")

            r = st.write_many([row("0002.01", commission=1.07, realized=-12.5)])
            check(r["commission_completed"] == 1 and r["inserted"] == 0,
                  f"the later report COMPLETES the row rather than duplicating "
                  f"it ({r})")
            got = st.latest()[0]
            check(abs(got["commission"] - 1.07) < 1e-9, "the commission lands")
            check(abs((got["realized_pnl"] or 0) + 12.5) < 1e-9,
                  "and the realized P&L with it")
            check(not st.missing_commission(),
                  "and the row leaves the missing list")

            st.write_many([row("0002.01", commission=99.99)])
            got = st.latest()[0]
            check(abs(got["commission"] - 1.07) < 1e-9,
                  f"a SECOND report does NOT overwrite a recorded commission "
                  f"({got['commission']}) -- a fill is a fact")


def group_d() -> None:
    print(f"\n{LINE}\nD. THE INSTRUMENT KEY MATCHES PORTFOLIO TRUTH\n{LINE}")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        db = str(Path(d) / "k.db")
        # The 17 September book: one fill on each listing.
        arca = fill("0003.01", con_id=756733, currency="USD", venue="ARCA")
        mexi = fill("0003.02", con_id=38709152, currency="MXN", venue="MEXI",
                    price=12317.15, side="SLD")
        rows = ibkr._read_fills(FakeIB([arca, mexi]))
        keys = sorted(r["instrument"] for r in rows)
        check(keys == ["SPY@ARCA.USD", "SPY@MEXI.MXN"],
              f"the two listings key distinctly ({keys})")

        # And identically to the position rows, which is the point: a fill has
        # to join the holding it moved.
        holding = {"local_symbol": "SPY", "symbol": "SPY",
                   "primary_exchange": "MEXI", "currency": "MXN"}
        check(ibkr.instrument_key(holding) == "SPY@MEXI.MXN",
              "and by the SAME function Portfolio Truth keys a position with, "
              "so a fill joins its position without a translation step")

        with executions.ExecutionStore(db) as st:
            st.write_many(rows)
            check(len(st.for_instrument("SPY@MEXI.MXN")) == 1,
                  "for_instrument() finds the peso fill and not the dollar one")
            got = st.for_instrument("SPY@MEXI.MXN")[0]
            check(got["side"] == "SLD" and got["con_id"] == 38709152,
                  f"with its side and conId intact ({got['side']}, "
                  f"{got['con_id']})")


def group_e() -> None:
    print(f"\n{LINE}\nE. A FAILED FILL READ COSTS NO POSITIONS\n{LINE}")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        db = str(Path(d) / "e.db")
        ib = FakeIB(fills_raise=RuntimeError("execution feed unavailable"))
        res = ibkr.sync(port=4002, db_path=db, ib_factory=lambda: ib)
        check(res["positions"] == 1,
              "the position read still succeeds when the fill read raises")
        check(res["observations"] > 0 and res["written"] > 0,
              "and its observations are still written")
        check(res["fills"] == 0 and "execution feed unavailable" in
              (res.get("fills_error") or ""),
              f"the failure is REPORTED by name rather than swallowed "
              f"({res.get('fills_error')})")
        check(ib.disconnected, "and the client is still disconnected")

        # The healthy path, for contrast: both reads land.
        db2 = str(Path(d) / "e2.db")
        ib2 = FakeIB([fill("0004.01")])
        res2 = ibkr.sync(port=4002, db_path=db2, ib_factory=lambda: ib2)
        check(res2["fills"] == 1 and res2["fills_written"]["inserted"] == 1,
              f"a healthy sync writes the fill ({res2['fills_written']})")
        check(res2.get("fills_error") is None, "and reports no error")

        # A dry run reads and writes nothing.
        db3 = str(Path(d) / "e3.db")
        res3 = ibkr.sync(port=4002, db_path=db3, dry_run=True,
                         ib_factory=lambda: FakeIB([fill("0005.01")]))
        check(res3["fills"] == 1 and res3["fills_written"]["inserted"] == 0,
              "--dry-run parses the fills and writes none")


def group_f() -> None:
    print(f"\n{LINE}\nF. TIME IS THE BROKER'S, IN UTC\n{LINE}")
    rows = ibkr._read_fills(FakeIB([fill("0006.01",
                                         when="2026-09-21T13:31:02+00:00")]))
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        with executions.ExecutionStore(str(Path(d) / "t.db")) as st:
            st.write_many(rows)
            got = st.latest()[0]
            check(got["exec_time"].startswith("2026-09-21T13:31:02"),
                  f"the FILL time is stored, not the read time ({got['exec_time']})")
            check(got["exec_time"].endswith("+00:00"),
                  "normalised to UTC, so two boxes in two zones agree")
            check(got["ingested_at"] != got["exec_time"],
                  "and the ingest time is a separate column -- a fill at the "
                  "open read at 16:30 is a fact about the open")

    # A naive timestamp is treated as UTC rather than dropped or guessed.
    rows = ibkr._read_fills(FakeIB([fill("0006.02", when="2026-09-21T13:31:02")]))
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        with executions.ExecutionStore(str(Path(d) / "t2.db")) as st:
            st.write_many(rows)
            check(st.latest()[0]["exec_time"].endswith("+00:00"),
                  "a naive broker timestamp is read as UTC, not discarded")


def main() -> int:
    print(f"{LINE}\nExecutions -- the fill record (mocked; no Gateway)\n{LINE}")
    group_a()
    group_b()
    group_c()
    group_d()
    group_e()
    group_f()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    print("NOTE: no Gateway was contacted. reqExecutions serves the CURRENT DAY "
          "only,\n      so the first real rows arrive with Monday's fills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
