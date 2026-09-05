"""
Validation gate for Expression Intelligence (26.11 Gate 1.5).

Runs with NO Gateway and no network. Every IBKR interaction is faked, which is
the point: the properties checked here are properties of our code, and a gate
that needs a live broker is a gate that gets skipped on the day it matters.

  A  NO ORDER SUBMISSION. ibkr_whatif must construct an Order -- What-If has no
     other form -- so the grep here is necessarily narrower than the one over
     ibkr_portfolio, and the difference is stated rather than blurred.
  B  whatIf=True actually reaches the order object, and losing it is refused.
  C  The Double.MAX_VALUE sentinel becomes None rather than a 1.8e308 cost.
  D  parse_state against a canned OrderState.
  E  Buying power is DERIVED with a measured multiplier, never assumed.
  F  Error classification: read-only refusal is its own type.
  G  flat/hedge are refused rather than guessed.
  H  A partial option specification is refused.

    python tools/validate_ibkr_whatif.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata.sources import ibkr_portfolio as ibkr     # noqa: E402
from altdata.sources import ibkr_whatif as wi          # noqa: E402

LINE = "=" * 78
PASSED = FAILED = 0


def check(cond: bool, label: str) -> None:
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  FAIL  {label}")


def raises(fn, exc, label: str, contains: str = "") -> None:
    try:
        fn()
    except exc as e:
        check(contains.lower() in str(e).lower(),
              f"{label} (message names {contains!r})" if contains else label)
    except Exception as e:  # noqa: BLE001
        check(False, f"{label} -- raised {type(e).__name__} not {exc.__name__}: {e}")
    else:
        check(False, f"{label} -- nothing raised")


# --- fakes ------------------------------------------------------------------
class FakeAV:
    def __init__(self, tag, value, currency="USD"):
        self.tag, self.value, self.currency = tag, value, currency
        self.account = "DU1234567"


class FakeState:
    """Shaped exactly like IBKR's OrderState: numbers arrive as STRINGS."""
    def __init__(self, **kw):
        self.status = "PreSubmitted"
        self.initMarginBefore = "10000.00"
        self.maintMarginBefore = "8000.00"
        self.equityWithLoanBefore = "100000.00"
        self.initMarginChange = "19500.00"
        self.maintMarginChange = "15600.00"
        self.equityWithLoanChange = "0.00"
        self.initMarginAfter = "29500.00"
        self.maintMarginAfter = "23600.00"
        self.equityWithLoanAfter = "100000.00"
        self.commission = 1.0
        self.minCommission = wi.IB_UNSET
        self.maxCommission = wi.IB_UNSET
        self.commissionCurrency = "USD"
        self.warningText = ""
        self.completedTime = ""
        self.completedStatus = ""
        self.__dict__.update(kw)


class FakeDetails:
    def __init__(self, contract):
        self.contract = contract


class FakeIB:
    """Records what it was asked to do; never pretends to be a broker."""
    _DEFAULT = object()      # so state=None means None, not "use the default"

    def __init__(self, state=_DEFAULT, raise_on_whatif=None, details=True):
        self.connect_kwargs = {}
        self.placed = []
        self.what_ifs = []
        self._state = FakeState() if state is FakeIB._DEFAULT else state
        self._raise = raise_on_whatif
        self._details = details
        self.disconnected = False

    def connect(self, host, port, clientId, timeout, readonly=False):
        self.connect_kwargs = dict(host=host, port=port, clientId=clientId,
                                   timeout=timeout, readonly=readonly)

    def accountSummary(self):
        return [FakeAV("NetLiquidation", "100000.00"),
                FakeAV("BuyingPower", "400000.00"),
                FakeAV("AvailableFunds", "90000.00"),
                FakeAV("ExcessLiquidity", "92000.00"),
                FakeAV("FullInitMarginReq", "10000.00"),
                FakeAV("FullMaintMarginReq", "8000.00")]

    def reqContractDetails(self, contract):
        if not self._details:
            return []
        contract.localSymbol = getattr(contract, "symbol", "?")
        return [FakeDetails(contract)]

    def whatIfOrder(self, contract, order):
        if self._raise:
            raise self._raise
        self.what_ifs.append((contract, order))
        return self._state

    # Deliberately present so that a call to it would SUCCEED rather than
    # AttributeError -- group A must prove we do not call it, not that we
    # cannot.
    def placeOrder(self, *a, **kw):
        self.placed.append((a, kw))
        return object()

    def disconnect(self):
        self.disconnected = True


# --- groups -----------------------------------------------------------------
def group_a() -> None:
    print(f"\n{LINE}\nA. NO ORDER SUBMISSION (necessarily narrower than "
          f"Portfolio Truth's)\n{LINE}")
    src = (REPO / "altdata" / "sources" / "ibkr_whatif.py").read_text(encoding="utf-8")
    body = src.split('"""', 2)[-1]

    # ibkr_portfolio bans `Order(` outright. This module cannot: What-If IS a
    # placeOrder message with a flag, so the order object must exist. What
    # stays banned is every route by which one is SENT.
    banned = ["ib.placeOrder", "cancelOrder", "bracketOrder", "reqIds",
              "placeOrderAsync"]
    found = [b for b in banned if b in body]
    check(not found, f"no order-submitting call in the source ({found or 'none'})")
    check("whatIf = True" in body or "whatIf=True" in body,
          "the whatIf flag is set explicitly in the source")

    # And the neighbour's absolute claim is still absolute -- this module
    # existing must not have weakened it.
    pf = (REPO / "altdata" / "sources" / "ibkr_portfolio.py").read_text(encoding="utf-8")
    pf_body = pf.split('"""', 2)[-1]
    check("Order(" not in pf_body,
          "ibkr_portfolio.py still constructs no Order at all")

    ib = FakeIB()
    wi.run("SPY", "long", 100, ib_factory=lambda: ib)
    check(ib.connect_kwargs.get("readonly") is True,
          "connect passes readonly=True")
    check(ib.connect_kwargs.get("clientId") == wi.WHATIF_CLIENT_ID == 18,
          "uses client id 18, distinct from Portfolio Truth's 17")
    check(ib.placed == [], "placeOrder was NEVER called (the fake would record it)")
    check(len(ib.what_ifs) == 1, "exactly one whatIfOrder call")
    check(ib.disconnected, "disconnects even on the happy path")


def group_b() -> None:
    print(f"\n{LINE}\nB. THE FLAG IS THE WHOLE DIFFERENCE\n{LINE}")
    o = wi.build_order("BUY", 100)
    check(o.whatIf is True, "build_order sets whatIf=True")
    check(o.transmit is False, "build_order sets transmit=False as well")
    check(o.action == "BUY" and o.totalQuantity == 100.0,
          "action and quantity land on the order")

    ib = FakeIB()
    _, order = None, None
    wi.preview(ib, "SPY", "long", 100)
    _c, order = ib.what_ifs[0]
    check(order.whatIf is True, "the order that reaches whatIfOrder still has it")

    # The boundary re-check: strip the flag and it must refuse.
    real_build = wi.build_order

    def stripped(*a, **kw):
        bad = real_build(*a, **kw)
        bad.whatIf = False
        return bad

    wi.build_order = stripped
    try:
        raises(lambda: wi.preview(FakeIB(), "SPY", "long", 100), wi.WhatIfError,
               "an order that lost whatIf is refused at the boundary",
               "whatIf is not True")
    finally:
        wi.build_order = real_build

    raises(lambda: wi.build_order("BUY", -5), ValueError,
           "a negative quantity is refused", "must be positive")
    raises(lambda: wi.build_order("BUY", 100, order_type="LMT"), ValueError,
           "a LMT with no limit price is refused", "limit-price")


def group_c() -> None:
    print(f"\n{LINE}\nC. THE DOUBLE.MAX_VALUE SENTINEL\n{LINE}")
    check(wi._num(wi.IB_UNSET) is None,
          "1.7976931348623157e308 parses to None, not to a 1.8e308 commission")
    check(wi._num(str(wi.IB_UNSET)) is None,
          "and also when it arrives as a string, as IBKR sends the margins")
    check(wi._num("12.34") == 12.34, "an ordinary string number still parses")
    check(wi._num(0.0) == 0.0, "zero survives -- a free trade is not a missing one")
    check(wi._num(None) is None and wi._num("") is None, "None/empty are None")
    check(wi._num(float("nan")) is None, "NaN is None")


def group_d() -> None:
    print(f"\n{LINE}\nD. PARSE A CANNED OrderState\n{LINE}")
    ib = FakeIB()
    p = wi.preview(ib, "SPY", "long", 100, port=4002)
    check(p["commission"]["estimate"] == 1.0, "commission read")
    check(p["commission"]["min"] is None and p["commission"]["max"] is None,
          "sentinel min/max commission became None")
    check(p["margin"]["init_change"] == 19500.0, "init margin change read")
    check(p["margin"]["maint_change"] == 15600.0, "maint margin change read")
    check(p["margin"]["init_after"] == 29500.0, "init margin after read")
    check(p["equity_with_loan"]["change"] == 0.0, "equity-with-loan change read")
    check(p["mode"] == "paper" and p["source"] == "ibkr_paper",
          "mode and source derived FROM THE PORT (4002 -> paper)")
    check(p["action"] == "BUY", "long maps to BUY")
    check(p["complete"] is True, "a preview with commission and margin is complete")

    # A preview missing both must NOT read as a free trade.
    bare = FakeIB(state=FakeState(commission=wi.IB_UNSET,
                                  initMarginChange=str(wi.IB_UNSET),
                                  initMarginAfter=str(wi.IB_UNSET),
                                  initMarginBefore=str(wi.IB_UNSET)))
    p2 = wi.preview(bare, "SPY", "long", 100)
    check(p2["complete"] is False,
          "no commission and no margin figure is INCOMPLETE, not free")

    live = wi.preview(FakeIB(), "SPY", "long", 100, port=4001)
    check(live["mode"] == "live" and live["source"] == "ibkr_live",
          "port 4001 is reported live -- a preview cannot claim paper wrongly")


def group_e() -> None:
    print(f"\n{LINE}\nE. BUYING POWER IS DERIVED, AND SAYS SO\n{LINE}")
    p = wi.preview(FakeIB(), "SPY", "long", 100)
    b = p["buying_power"]
    # Baseline: BuyingPower 400000 / AvailableFunds 90000 = 4.444...
    check(abs(b["leverage_multiplier_observed"] - 400000 / 90000) < 1e-9,
          "the multiplier is MEASURED from the account, not assumed to be 4")
    # AvailableFunds after = equityWithLoanAfter - initMarginAfter
    #                      = 100000 - 29500 = 70500
    check(b["available_funds_after"] == 70500.0,
          "available funds after uses IBKR's own identity (EWL - initMargin)")
    check(abs(b["buying_power_after_est"] - 70500 * (400000 / 90000)) < 1e-6,
          "buying power after applies the measured multiplier")
    check(b["buying_power_delta_est"] < 0,
          "buying a position CONSUMES buying power (delta is negative)")
    check("never assumed" in b["derivation"],
          "the derivation is recorded in the output, not just in a docstring")

    # Unmeasurable multiplier must yield None, never a guess.
    class NoFunds(FakeIB):
        def accountSummary(self):
            return [FakeAV("BuyingPower", "400000.00"),
                    FakeAV("AvailableFunds", "0")]
    p2 = wi.preview(NoFunds(), "SPY", "long", 100)
    check(p2["buying_power"]["leverage_multiplier_observed"] is None,
          "a zero AvailableFunds gives no multiplier rather than a ZeroDivision")
    check(p2["buying_power"]["buying_power_after_est"] is None,
          "and no buying-power projection at all, rather than a guess")


def group_f() -> None:
    print(f"\n{LINE}\nF. ERROR CLASSIFICATION -- the fixes are different\n{LINE}")
    ro = FakeIB(raise_on_whatif=RuntimeError(
        "Order rejected - reason: This account is in Read-Only API mode"))
    raises(lambda: wi.preview(ro, "SPY", "long", 100), wi.WhatIfNotPermitted,
           "a read-only refusal is WhatIfNotPermitted", "read-only api")

    none_state = FakeIB(state=None)
    raises(lambda: wi.preview(none_state, "SPY", "long", 100),
           wi.WhatIfNotPermitted,
           "a silent None order state is also WhatIfNotPermitted", "read-only")

    unresolved = FakeIB(details=False)
    raises(lambda: wi.preview(unresolved, "ZZZZ", "long", 100),
           wi.ContractNotResolved,
           "an unresolvable symbol is its own error", "no contract details")

    other = FakeIB(raise_on_whatif=RuntimeError("something else entirely"))
    raises(lambda: wi.preview(other, "SPY", "long", 100), ibkr.IbkrApiError,
           "anything else stays a generic IbkrApiError", "something else")

    # And the live-port guard from Portfolio Truth still applies here.
    raises(lambda: wi.run("SPY", "long", 100, port=4001,
                          ib_factory=lambda: FakeIB()),
           ibkr.IbkrApiError, "a LIVE port needs allow_live", "allow_live")


def group_g() -> None:
    print(f"\n{LINE}\nG. DIRECTIONS THAT DO NOT IMPLY A SIDE\n{LINE}")
    check(wi.action_for_direction("long") == "BUY", "long -> BUY")
    check(wi.action_for_direction("short") == "SELL", "short -> SELL")
    raises(lambda: wi.action_for_direction("flat"), ValueError,
           "flat is refused rather than guessed", "does not determine a side")
    raises(lambda: wi.action_for_direction("hedge"), ValueError,
           "hedge is refused rather than guessed", "does not determine a side")
    check(wi.action_for_direction("hedge", "SELL") == "SELL",
          "an explicit action makes hedge previewable")


def group_h() -> None:
    print(f"\n{LINE}\nH. PARTIAL OPTION SPECIFICATIONS\n{LINE}")
    raises(lambda: wi.build_contract("SPY", sec_type="OPT", strike=770,
                                     right="C"),
           ValueError, "an option with no expiry is refused", "expiry")
    raises(lambda: wi.build_contract("SPY", sec_type="OPT", expiry="20260918",
                                     right="C"),
           ValueError, "an option with no strike is refused", "strike")
    raises(lambda: wi.build_contract("SPY", sec_type="OPT", expiry="20260918",
                                     strike=770, right="X"),
           ValueError, "an invalid right is refused", "right must be")
    c = wi.build_contract("SPY", sec_type="OPT", expiry="2026-09-18",
                          strike=770, right="C")
    check(c.lastTradeDateOrContractMonth == "20260918",
          "a dashed expiry is normalised to YYYYMMDD")
    check(c.multiplier == "100", "the option multiplier is set")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"{LINE}\nEXPRESSION INTELLIGENCE VALIDATION (no Gateway, no "
          f"network)\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g,
              group_h):
        g()
    print(f"\n{LINE}\n{PASSED} passed, {FAILED} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAILED else "VALIDATION FAILED")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
