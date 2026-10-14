"""
Validation gate for AUD-1 (the data and architecture audit of 14 Oct 2026,
ruled 09:27 ET) -- for what fits in no existing gate. No live store, no
network, no box: every check seeds its own temporary store.

  A  THE FRED COMPACTION (4b). A synthetic store with re-stamped FRED and
     derived rows, one real revision and a value that returns after it: the dry
     run counts and deletes nothing; --apply refuses without a backup, refuses a
     backup path that exists, and otherwise makes and checks its own backup
     first; it keeps the first of each run of identical values, never a
     revision, never a key outside its scope; the backup holds every row.
  B  THE INCREMENTAL RECOMPUTE (4d). market_features and surprise start from
     the newest day they have stored less their window, or from the beginning
     on an empty store, unless --from or --full says otherwise.

    python tools/validate_audit_1.py
"""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from altdata import observations  # noqa: E402

PASS = FAIL = 0
LINE = "=" * 78


def check(c: bool, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def _row(key, day, avail, value, inst=None, source="fred"):
    return {"registry_key": key, "instrument": inst, "observed_at": day,
            "available_at": avail, "value": value, "source": source}


def seed_restamped(path: str) -> None:
    """Five vintages of one FRED period: A A A, then a revision B, then A back."""
    rows = []
    t = ["2026-09-01T14:00:00+00:00", "2026-09-02T14:00:00+00:00",
         "2026-09-03T14:00:00+00:00", "2026-09-04T14:00:00+00:00",
         "2026-09-05T14:00:00+00:00"]
    for i, v in enumerate((4.10, 4.10, 4.10, 4.25, 4.10)):
        rows.append(_row("fred.yield_10y", "2026-08-29", t[i], v))
    # three re-stamps of an unchanged older period, and a single-vintage one
    for i in range(3):
        rows.append(_row("fred.yield_10y", "2026-08-28", t[i], 4.05))
    rows.append(_row("fred.ccc_oas", "2026-08-29", t[0], 9.1))
    # the derived keys that inherited the stamps
    for i in range(3):
        rows.append(_row("calc.yoy_cpi", "2026-08-01", t[i], 2.9, source="calc"))
        rows.append(_row("calc.surprise_vs_naive.cpi", "2026-08-01", t[i], 0.12,
                         source="calc"))
    # OUT OF SCOPE: a price re-read and a price-derived feature, left alone
    for i in range(3):
        rows.append(_row("yfinance.mkt_spy", "2026-08-29", t[i], 700.0,
                         source="yfinance"))
        rows.append(_row("calc.breadth_rsp_over_spy", "2026-08-29", t[i], 0.31,
                         source="calc"))
    with observations.ObservationStore(path) as st:
        st.write_many(rows)


def group_a() -> None:
    head("A. THE FRED COMPACTION (AUD-1 4b)")
    from altdata import compact_fred as cf
    td = tempfile.mkdtemp(prefix="validate_audit_1_")
    db = os.path.join(td, "store.db")
    seed_restamped(db)
    with observations.ObservationStore(db) as st:
        before = st.conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    lines: list[str] = []
    rc = cf.run(db, apply=False, out=lines.append)
    with observations.ObservationStore(db) as st:
        same = st.conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    text = "\n".join(lines)
    check(rc == 0 and same == before and "nothing deleted" in text
          and "fred.yield_10y" in text and "calc.yoy_cpi" in text
          and "calc.surprise_vs_naive.cpi" in text,
          f"the dry run prints the rows per key that would go and deletes none "
          f"({before} rows before and after)")
    check(cf.run(db, apply=True, backup=None, out=lines.append) == 2,
          "--apply without --backup is refused")
    exists = os.path.join(td, "old.db")
    Path(exists).write_bytes(b"x")
    check(cf.run(db, apply=True, backup=exists, out=lines.append) == 2,
          "--apply naming a backup that already exists is refused: this run makes it")
    bk = os.path.join(td, "backup", "pre.db")
    lines.clear()
    rc = cf.run(db, apply=True, backup=bk, out=lines.append)
    text = "\n".join(lines)
    check(rc == 0 and "backup ok" in text and text.index("backup ok") < text.index("deleted"),
          "--apply makes and integrity-checks its backup before deleting anything")
    con = sqlite3.connect(bk)
    n_bk = con.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    con.close()
    check(n_bk == before, f"the backup holds every row ({n_bk} of {before})")
    with observations.ObservationStore(db) as st:
        vs = [v["value_num"] for v in st.vintages("fred.yield_10y", "2026-08-29")]
        old = len(st.vintages("fred.yield_10y", "2026-08-28"))
        der = len(st.vintages("calc.yoy_cpi", "2026-08-01"))
        sur = len(st.vintages("calc.surprise_vs_naive.cpi", "2026-08-01"))
        spy = len(st.vintages("yfinance.mkt_spy", "2026-08-29"))
        brd = len(st.vintages("calc.breadth_rsp_over_spy", "2026-08-29"))
        one = len(st.vintages("fred.ccc_oas", "2026-08-29"))
        late = st.as_of("fred.yield_10y", as_of="2026-09-04T15:00:00+00:00")
    check(vs == [4.10, 4.25, 4.10],
          f"A A A B A keeps the first A, the revision B and the A after it: {vs}")
    check(old == 1 and der == 1 and sur == 1 and one == 1,
          "re-stamped FRED and derived periods keep one vintage each")
    check(spy == 3 and brd == 3,
          "keys outside the scope (prices, price-derived features) are untouched")
    check(late and late[-1]["value_num"] == 4.25,
          "a reader as of the revision's day still reads the revision")
    keys = cf.derived_keys()
    check("calc.yield_curve_2s10s" in keys and "calc.net_liquidity" in keys
          and "calc.breadth_rsp_over_spy" not in keys,
          f"the derived scope is market_features' FRED-derived keys ({len(keys)}), "
          f"not its price-derived ones")


def group_b() -> None:
    head("B. THE INCREMENTAL RECOMPUTE (AUD-1 4d)")
    from altdata import market_features as mf
    from altdata import surprise
    td = tempfile.mkdtemp(prefix="validate_audit_1_b_")
    db = os.path.join(td, "store.db")
    with observations.ObservationStore(db) as st:
        check(mf.default_first_day(st) is None and surprise.default_first_day(st) is None,
              "an empty store computes everything")
        st.write_many([_row("calc.yoy_cpi", "2026-09-01", "2026-09-02T00:00:00+00:00",
                            2.9, source="calc"),
                       _row("calc.surprise_vs_naive.cpi", "2026-08-01",
                            "2026-08-02T00:00:00+00:00", 0.1, source="calc")])
        check(mf.default_first_day(st) == "2026-05-04"
              and surprise.default_first_day(st) == "2026-04-03",
              f"each starts {mf.RECOMPUTE_WINDOW_DAYS} days before the newest day it "
              f"stored ({mf.default_first_day(st)}, {surprise.default_first_day(st)})")
    for mod in (mf, surprise):
        src = Path(mod.__file__).read_text(encoding="utf-8")
        check("if first_day is None and not full:" in src and "--full" in src,
              f"{mod.__name__}: --from and --full override the default start")


def main() -> int:
    print(f"{LINE}\nAUD-1, THE FIXES WITH NO OTHER GATE\n{LINE}")
    for g in (group_a, group_b):
        try:
            g()
        except Exception as exc:                              # noqa: BLE001
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
