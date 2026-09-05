"""
Validation gate for Portfolio Truth (architecture 26.11, Gate 1).

Runs entirely against fakes. THE LIVE TEST HAPPENS ON THE VPS once Gateway is
confirmed up -- this proves the code is correct, not that the Gateway is
reachable, and conflating those two is how a green build comes to mean nothing.

What it proves:

  A  NO ORDER CAPABILITY. The module's own source is searched for order-placing
     calls, and connect() is checked to pass readonly=True. The architecture's
     Gate 1 wording is "not disabled, not commented out, absent", which is a
     claim about the source text, so the source text is what gets checked.
  B  DISTINCT ERROR PATHS. Connection refused, handshake timeout, signed-out
     Gateway and everything else raise four different types with four different
     messages and four different exit codes. Collapsing them is what turns a
     6am timer failure into a twenty-minute diagnosis.
  C  THE PORT IS THE MODE. The source tag is derived from the port, so a row
     cannot claim to be paper while holding live balances, and a live port is
     refused unless explicitly allowed.
  D  PARSING AND POINT-IN-TIME SHAPE. Canned broker state produces the right
     observation rows, with source=ibkr_paper and observed_at == available_at.

    python tools/validate_ibkr_portfolio.py
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import observations                       # noqa: E402
from altdata.sources import ibkr_portfolio as ibkr     # noqa: E402

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


def raises(fn, exc, m: str) -> None:
    try:
        fn()
    except exc as e:
        ok(f"{m}  -> {type(e).__name__}")
        return
    except Exception as e:  # noqa: BLE001
        bad(f"{m} -- raised {type(e).__name__} instead: {e}")
        return
    bad(f"{m} -- did not raise")


# ---------------------------------------------------------------------------
# Fakes. Deliberately minimal: just the attribute shapes ib_async returns.
# ---------------------------------------------------------------------------
class _Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class FakeIB:
    """Records how it was connected; serves canned state."""

    def __init__(self, fail=None, accounts=("DU1234567",)):
        self.fail = fail
        self._accounts = list(accounts)
        self.connect_kwargs = None
        self.disconnected = False

    def connect(self, host, port, clientId=None, timeout=None, readonly=None):
        self.connect_kwargs = {"host": host, "port": port, "clientId": clientId,
                               "timeout": timeout, "readonly": readonly}
        if self.fail:
            raise self.fail

    def managedAccounts(self):
        return self._accounts

    def accountSummary(self):
        return [
            _Obj(account="DU1234567", tag="NetLiquidation", value="1043210.55", currency="USD"),
            _Obj(account="DU1234567", tag="TotalCashValue", value="250000.00", currency="USD"),
            _Obj(account="DU1234567", tag="BuyingPower", value="4000000.00", currency="USD"),
            _Obj(account="DU1234567", tag="GrossPositionValue", value="800000.00", currency="USD"),
            _Obj(account="DU1234567", tag="FullInitMarginReq", value="120000.00", currency="USD"),
            _Obj(account="DU1234567", tag="FullMaintMarginReq", value="100000.00", currency="USD"),
            _Obj(account="DU1234567", tag="ExcessLiquidity", value="943210.55", currency="USD"),
            _Obj(account="DU1234567", tag="AvailableFunds", value="923210.55", currency="USD"),
            _Obj(account="DU1234567", tag="Cushion", value="0.904", currency=""),
            _Obj(account="DU1234567", tag="IrrelevantTag", value="99", currency="USD"),
        ]

    def portfolio(self):
        return [
            _Obj(account="DU1234567", position=100.0, averageCost=765.4,
                 marketValue=77024.0, unrealizedPNL=484.0,
                 contract=_Obj(symbol="SPY", localSymbol="SPY", secType="STK",
                               currency="USD")),
            _Obj(account="DU1234567", position=-5.0, averageCost=1230.0,
                 marketValue=-4900.0, unrealizedPNL=1250.0,
                 contract=_Obj(symbol="SPY", localSymbol="SPY   260918C00780000",
                               secType="OPT", currency="USD")),
        ]

    def disconnect(self):
        self.disconnected = True


# ---------------------------------------------------------------------------
def group_a() -> None:
    print(f"\n{LINE}\nA. NO ORDER CAPABILITY -- absent, not disabled\n{LINE}")
    src = (REPO / "altdata" / "sources" / "ibkr_portfolio.py").read_text(encoding="utf-8")
    # Strip the docstring: it discusses these names precisely in order to
    # promise they are absent, and a check that trips on its own explanation is
    # a check nobody will keep.
    body = src.split('"""', 2)[-1]
    banned = ["placeOrder", "MarketOrder", "LimitOrder", "StopOrder",
              "bracketOrder", "cancelOrder", "reqIds", "Order("]
    found = [b for b in banned if b in body]
    check(not found, f"no order-placing call appears in the source ({found or 'none'})")
    # NOT "the session rejects orders at the socket" -- it does not, and the
    # label used to say so. ib_async's readonly only skips fetching orders at
    # startup; the absence check above is the actual guarantee.
    check("readonly=True" in body,
          "connect() passes readonly=True (a second layer, not the guarantee)")

    ib = FakeIB()
    ibkr.connect(port=4002, ib_factory=lambda: ib)
    check(ib.connect_kwargs.get("readonly") is True,
          "readonly=True actually reaches the client, not just the source")
    check(ib.connect_kwargs.get("port") == 4002, "defaults to the paper port 4002")


def group_b() -> None:
    print(f"\n{LINE}\nB. DISTINCT ERROR PATHS\n{LINE}")
    raises(lambda: ibkr.connect(ib_factory=lambda: FakeIB(fail=ConnectionRefusedError())),
           ibkr.GatewayNotRunning, "connection refused -> 'Gateway not running'")

    try:
        ibkr.connect(ib_factory=lambda: FakeIB(fail=ConnectionRefusedError()))
    except ibkr.GatewayNotRunning as e:
        check("Gateway not running" in str(e) and "4002" in str(e),
              "the message names the problem and the port a human must check")

    raises(lambda: ibkr.connect(ib_factory=lambda: FakeIB(fail=TimeoutError())),
           ibkr.GatewayNotResponding,
           "handshake timeout -> a DIFFERENT error from 'not running'")

    err = OSError("refused")
    err.errno = 10061
    raises(lambda: ibkr.connect(ib_factory=lambda: FakeIB(fail=err)),
           ibkr.GatewayNotRunning,
           "a bare OSError with a refused errno is still 'Gateway not running'")

    raises(lambda: ibkr.connect(ib_factory=lambda: FakeIB(fail=RuntimeError("boom"))),
           ibkr.IbkrApiError, "anything else -> IbkrApiError")

    # Running, listening, connected -- and signed out. Looks healthy outside.
    ib = FakeIB(accounts=())
    ibkr.connect(port=4002, ib_factory=lambda: ib)
    raises(lambda: ibkr.read_state(ib, 4002), ibkr.IbkrAuthError,
           "connected but no managed accounts -> IbkrAuthError (signed out)")

    check(len({ibkr.GatewayNotRunning, ibkr.GatewayNotResponding,
               ibkr.IbkrAuthError, ibkr.IbkrApiError}) == 4
          and all(issubclass(c, ibkr.IbkrError) for c in
                  (ibkr.GatewayNotRunning, ibkr.GatewayNotResponding,
                   ibkr.IbkrAuthError, ibkr.IbkrApiError)),
          "four distinct types, all catchable as IbkrError")


def group_c() -> None:
    print(f"\n{LINE}\nC. THE PORT IS THE MODE\n{LINE}")
    check(ibkr.source_for_port(4002) == "ibkr_paper", "4002 -> ibkr_paper")
    check(ibkr.source_for_port(7497) == "ibkr_paper", "7497 (TWS paper) -> ibkr_paper")
    check(ibkr.source_for_port(4001) == "ibkr_live", "4001 -> ibkr_live")
    check(ibkr.source_for_port(7496) == "ibkr_live", "7496 (TWS live) -> ibkr_live")
    raises(lambda: ibkr.connect(port=4001, ib_factory=lambda: FakeIB()),
           ibkr.IbkrApiError,
           "a LIVE port is refused unless allow_live is passed explicitly")
    ib = FakeIB()
    ibkr.connect(port=4001, allow_live=True, ib_factory=lambda: ib)
    check(ib.connect_kwargs["readonly"] is True,
          "even with allow_live, the connection is still read-only")


def group_d() -> None:
    print(f"\n{LINE}\nD. PARSING AND POINT-IN-TIME SHAPE\n{LINE}")
    ib = FakeIB()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        db = str(Path(td) / "t.db")
        res = ibkr.sync(port=4002, db_path=db, ib_factory=lambda: ib)

        check(ib.disconnected, "the client is disconnected after the read")
        check(res["source"] == "ibkr_paper" and res["mode"] == "paper",
              "the run is tagged ibkr_paper from the port")
        check(res["positions"] == 2, "both positions parsed")
        # 9 account tags + 2 positions x 4 fields = 17
        check(res["observations"] == 17,
              f"9 account values + 8 position values = 17 rows "
              f"(got {res['observations']})")
        check(res["written"] == 17, "all rows written to the store")

        store = observations.ObservationStore(db)
        nav = store.latest_as_of("portfolio.nav", instrument="DU1234567")
        check(nav is not None and abs(nav["value_num"] - 1043210.55) < 1e-6,
              "NAV round-trips through the store intact")
        check(nav["source"] == "ibkr_paper", "every row carries source=ibkr_paper")

        rows = store.conn.execute(
            "SELECT observed_at, available_at FROM observations").fetchall()
        check(all(r[0] == r[1] for r in rows),
              "observed_at == available_at -- a broker balance has no release lag")

        opt = store.latest_as_of("portfolio.position_qty",
                                 instrument="SPY   260918C00780000")
        check(opt is not None and opt["value_num"] == -5.0,
              "an option position is keyed on localSymbol, not the bare symbol, "
              "so two contracts on one underlying cannot collide")

        # LINEAGE. Without run_id a row is unattributable the moment history
        # accumulates: two syncs a minute apart become indistinguishable, and a
        # packet cannot claim lineage over rows it cannot identify as its own.
        run_ids = [r[0] for r in store.conn.execute(
            "SELECT DISTINCT run_id FROM observations").fetchall()]
        check(len(run_ids) == 1 and run_ids[0],
              f"every row carries exactly one run_id ({run_ids})")
        check(run_ids[0].startswith("ibkr_portfolio-"),
              f"run_id follows session.new_run_id's convention ({run_ids[0]})")
        check(res["run_id"] == run_ids[0],
              "the sync reports the same run_id it stamped on the rows")
        check(not any(r[0] is None for r in store.conn.execute(
            "SELECT run_id FROM observations").fetchall()),
              "no row is left unattributed")

        cushion = store.latest_as_of("portfolio.cushion", instrument="DU1234567")
        check(cushion is not None and abs(cushion["value_num"] - 0.904) < 1e-9,
              "cushion (the margin-stress reading) is captured")

        before = store.count()
        second = ibkr.sync(port=4002, db_path=db, ib_factory=lambda: FakeIB())
        check(second["run_id"] != res["run_id"],
              "a second sync gets a DIFFERENT run_id -- two runs are two runs")
        check(store.count() > before,
              "a later sync ADDS a snapshot rather than replacing one -- "
              "portfolio state is a series, not a current value")
        store.close()

    res = ibkr.sync(port=4002, dry_run=True, ib_factory=lambda: FakeIB())
    check(res["written"] == 0 and res["observations"] == 17,
          "--dry-run parses everything and writes nothing")


def group_e() -> None:
    print(f"\n{LINE}\nE. REGISTRY COVERAGE\n{LINE}")
    import yaml
    metrics = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    sources = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))
    reg = metrics.get("metrics") or {}

    emitted = {k for k, _ in ibkr.ACCOUNT_TAGS.values()} | set(ibkr.POSITION_METRICS)
    missing = sorted(emitted - set(reg))
    check(not missing, f"every metric this module writes is registered ({missing or 'none'})")
    check(all(reg[k]["mechanism_group"] == "portfolio_truth" for k in emitted),
          "all of them are mechanism_group=portfolio_truth")
    check(not any(reg[k].get("trigger_eligible") for k in emitted),
          "none is trigger_eligible")
    check("ibkr_paper" in (sources.get("sources") or {}),
          "ibkr_paper exists in the source registry")
    check((sources["sources"]["ibkr_paper"].get("allowed_reports") or []) == [],
          "ibkr_paper has an empty allowed_reports -- reconciliation, not a report input")


def main() -> int:
    print(f"{LINE}\nPortfolio Truth validation (fakes only; live test is on the "
          f"VPS)\n{LINE}")
    group_a()
    group_b()
    group_c()
    group_d()
    group_e()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    print("NOTE: no Gateway was contacted. Run "
          "`python -m altdata.sources.ibkr_portfolio --dry-run` on the VPS "
          "once Gateway is up for the live check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
