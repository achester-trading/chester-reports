#!/usr/bin/env python3
"""
Signal-triage Batch 11 (items 53-58, ruled 19 Oct 2026; session A's a48-batch11):
what has no other home.

  A  ITEM 54'S SCORECARD BACKFILL. On synthetic captures: a dry run writes
     nothing; a run writes each session that has a settled 16:10 capture and a
     prior-session capture and no row, point in time (the morning profile is the
     prior session's capture; available_at is the capture's own fetched_at), each
     row labelled backfilled under `daily_close:backfill`; a second run writes
     nothing; a live row is never replaced. A backfilled row never enters the test
     sample, whatever its date; the rates print the test sample with the rest
     beside it, "before registration, descriptive"; the registration file's
     SHA-256 is the one validate_dealer_block records.

No gate here reads the live store, fetches or calls a model; every fixture is
synthetic.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp                                    # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
TD = Path(mkdtemp("a48-batch11-gate-"))


def check(c, m: str) -> bool:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")
    return bool(c)


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def obs(key: str, day: str, value, inst=None, avail=None, source="fixture") -> dict:
    return {"registry_key": key, "instrument": inst, "observed_at": day,
            "available_at": avail or f"{day}T21:00:00+00:00", "value": value,
            "source": source}


# ---------------------------------------------------------------------------
# A. The scorecard backfill
# ---------------------------------------------------------------------------
CAP_DAYS = ("2026-10-14", "2026-10-15", "2026-10-16", "2026-10-19")


def _capture(day: str, k: int) -> dict:
    return {"symbol": "SPY", "session_date": day, "capture": "settled_eod",
            "fetched_at": f"{day}T20:14:00+00:00",
            "overall": {"net_gex": -1.0e9 - k * 1e8, "net_to_gross": 0.25,
                        "gamma_flip": 660.0 + k, "call_wall_otm": 670.0 + k,
                        "put_wall_otm": 650.0 + k, "peak_abs_gex_strike": 662.0 + k,
                        "call_wall": 671.0 + k, "put_wall": 649.0 + k,
                        "max_pain": 661.0 + k}}


def seed(td: Path) -> tuple[str, str]:
    from altdata import bars as bars_mod, observations
    comp = td / "computed"
    for k, day in enumerate(CAP_DAYS):
        (comp / day).mkdir(parents=True, exist_ok=True)
        (comp / day / "SPY_01_exposure.json").write_text(json.dumps(_capture(day, k)),
                                                         encoding="utf-8")
    db = str(td / "store.db")
    closes = {"2026-10-13": 659.0, "2026-10-14": 660.0, "2026-10-15": 663.0,
              "2026-10-16": 661.0, "2026-10-19": 665.0, "2026-10-20": 666.0}
    rows = [obs("yfinance.mkt_spy", d, v, avail=f"{d}T20:05:00+00:00")
            for d, v in closes.items()]
    rows += [obs("chain.spy_atm_iv_30d", d, 18.0, avail=f"{d}T20:15:00+00:00")
             for d in CAP_DAYS]
    # A live row for 16 Oct (before registration) and one for 20 Oct (after it).
    for d in ("2026-10-16", "2026-10-20"):
        rows.append(obs("dealer.scorecard_day", d,
                        json.dumps({"session": d, "symbol": "SPY", "prior_close": 660.0,
                                    "close": 661.0, "session_high": 662.0,
                                    "session_low": 659.0, "net_gex_morning": -1e9,
                                    "net_to_gross_morning": 0.25, "atm_iv_30d": 18.0,
                                    "regime_eligible": True}),
                        "SPY", source="daily_close"))
    with observations.ObservationStore(db) as st:
        st.write_many(rows)
    bst = bars_mod.BarStore(db, create=True)
    bst.write_many([{"instrument": "spy", "symbol": "SPY", "interval": "5m",
                     "observed_at": t, "open": o, "high": h, "low": lo, "close": c,
                     "volume": 1000.0, "available_at": t[:11] + "20:10:00+00:00",
                     "source": "fixture"}
                    for t, o, h, lo, c in (
                        ("2026-10-15T13:30:00+00:00", 660.0, 661.5, 659.5, 661.0),
                        ("2026-10-15T16:00:00+00:00", 661.0, 664.25, 660.5, 664.0),
                        ("2026-10-15T19:55:00+00:00", 664.0, 664.0, 662.5, 663.0))])
    bst.close()
    return db, str(comp)


def group_a() -> None:
    head("A. ITEM 54: THE SCORECARD BACKFILL, AND THE TWO SAMPLES")
    from altdata import dealer_scorecard as dsc, observations
    from daily_cascade import scorecard_backfill as sb
    db, comp = seed(TD / "a")

    def stored():
        with observations.ObservationStore(db) as st:
            return {str(r["observed_at"])[:10]: r for r in
                    st.as_of("dealer.scorecard_day", "9999", "SPY")}

    before = stored()
    dry = sb.run(db, comp, dry_run=True)
    check(stored().keys() == before.keys() and dry["written"] == 0
          and [r["observed_at"] for r in dry["rows"]] == ["2026-10-15", "2026-10-19"],
          f"the dry run writes nothing and plans 15 and 19 Oct "
          f"({[r['observed_at'] for r in dry['rows']]})")
    why = dict(dry["skipped"])
    check(why.get("2026-10-14", "").startswith("no settled capture for the prior session")
          and why.get("2026-10-16") == "a row exists",
          f"14 Oct is skipped (no prior-session capture), 16 Oct keeps its live row ({why})")
    res = sb.run(db, comp, dry_run=False)
    after = stored()
    r15 = json.loads(after["2026-10-15"]["value_text"])
    check(res["written"] == 2 and after["2026-10-15"]["source"] == "daily_close:backfill"
          and r15["backfilled"] is True
          and after["2026-10-15"]["available_at"].startswith("2026-10-15T20:15")
          and after["2026-10-16"]["source"] == "daily_close",
          "a run writes the two, labelled backfilled under daily_close:backfill, available "
          "at the latest of its inputs (the 20:15 IV, after the 20:14 capture); the live 16 "
          "Oct row is untouched")
    check(r15["flip_morning"] == 660.0 and r15["net_gex_morning"] == -1.0e9
          and r15["prior_close"] == 660.0 and r15["close"] == 663.0
          and r15["session_high"] == 664.25 and r15["session_low"] == 659.5
          and r15["session_range_pct"] == round(100 * 4.75 / 660.0, 3)
          and r15["atm_iv_30d"] == 18.0 and r15["flip_in_range"] is True,
          "point in time: 15 Oct's morning profile is 14 Oct's capture (flip 660, net GEX "
          "-1.0bn), its range 664.25 less 659.50 over the 660.00 prior close, 0.72%")
    again = sb.run(db, comp, dry_run=False)
    check(again["written"] == 0 and len(stored()) == len(after),
          "idempotent: a second run writes nothing")
    with observations.ObservationStore(db) as st:
        t = dsc.from_store(st, "9999-12-31T00:00:00+00:00")
    by = {r["session"]: r for r in t["rows"]}
    check(t["registered_on"] == "2026-10-17" and t["test_n"] == 1 and t["before_n"] == 3
          and by["2026-10-19"]["backfilled"] and not dsc.in_test(by["2026-10-19"], "2026-10-17")
          and dsc.in_test(by["2026-10-20"], "2026-10-17"),
          "a backfilled row never enters the test sample, even dated after the "
          "registration (19 Oct); the live 20 Oct row does; 16 Oct's live row is before it")
    check(len(t["lines"]) == 12 and all(l.split(":")[0].endswith(dsc.BEFORE)
                                        for l in t["lines"][1::2])
          and len(t["rates"]) == 6 and t["promoted"] == 0,
          "the rates print the test sample, each beside its line on the rest, labelled "
          "'before registration, descriptive'; six registered, none promoted")
    src = (REPO / "tools" / "validate_dealer_block.py").read_text(encoding="utf-8")
    pinned = re.search(r'^LEDGER_SHA256 = "([0-9a-f]{64})"', src, re.M).group(1)
    raw = (REPO / "docs" / "ledgers" / "dealer-scorecard-preregistration-2026-10.md"
           ).read_bytes().replace(b"\r\n", b"\n")
    check(hashlib.sha256(raw).hexdigest() == pinned,
          "the registration file's SHA-256 is unchanged (the one validate_dealer_block "
          "records): it is not edited")
    os_src = (REPO / "daily_cascade" / "opening_setup.py").read_text(encoding="utf-8")
    check("def in_test(card: dict, reg: str) -> bool:" in os_src
          and 'return not card.get("backfilled")' in os_src,
          "OS-2's typical range reads both samples by the same rule, with their counts")


def main() -> int:
    for g in (group_a,):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
