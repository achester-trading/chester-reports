#!/usr/bin/env python3
"""
Validation gate: the 14 Oct audit's leftovers, reconciled and finished (A71;
workplan v7 section 5 item 7; docs/briefs/a71-audit-leftovers-notes.md). Fixtures
only: no network, no live store.

  A  THE RECONCILIATION, FROM THE CODE. Each leftover that is done is held by
     what does it: incremental FRED windows; the meme ingest; the encrypted sweep;
     the append-only triggers and their one maintenance path; the as-of join's
     source tier; the writer refusing an unregistered source; the yfinance basket
     resolved through the Security Master.
  B  THE BLOCKLIST AT THE BASKET'S RESOLVER. Each symbol is asked of the master's
     is_restricted where its key is resolved: a restricted name is logged and
     listed in the pull's summary, and its key, like every other, is unchanged
     (prices are diagnostics; the register refuses the recommendation). On the
     real master, the resolved basket is identical with and without the check.
  C  NO LITERAL TICKER IN THE BASKET'S CALL SITES. pull() and pull_crypto_basket()
     take every store key from resolve_basket and carry no `mkt_` literal.
  D  H.4.1 INCREMENTAL ONCE HELD. The package is asked for the stated overlap
     (8 Wednesdays) when the FIMA keys are stored, the full ten years when not;
     the URL is otherwise the one the writer has always used.

    python tools/validate_audit_leftovers.py
"""

from __future__ import annotations

import ast
import logging
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

TD = Path(gate_mkdtemp("audit_leftovers_"))
LINE = "=" * 78
PASS = FAIL = 0


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def src(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def group_a() -> None:
    head("A. THE RECONCILIATION, FROM THE CODE")
    from altdata.sources import fred
    check(fred.REVISION_WINDOW_DAYS == {"daily": 30, "weekly": 120, "monthly": 400,
                                        "quarterly": 400},
          "incremental pulls: FRED reads each series from its newest stored date less "
          "its revision window (30 / 120 / 400 days)")
    check((REPO / "altdata" / "meme_ingest.py").exists()
          and "CREATE TABLE IF NOT EXISTS meme_drafts" in src("altdata/meme_ingest.py"),
          "the chester-meme draft ingest writes Book D drafts (altdata/meme_ingest.py)")
    sweep = src("scripts/rclone_sync.sh")
    check("crypt" in sweep, "the backup sweep runs through the encrypted remote")
    obs = src("altdata/observations.py")
    check("CREATE TRIGGER IF NOT EXISTS observations_no_update" in obs
          and "observations_no_delete" in obs and "def maintenance(" in obs,
          "the append-only triggers, and their one audited maintenance path")
    check("tier_over" in obs, "the as-of join keeps the higher source tier at one "
                              "instant, and says what it chose over")
    check("class UnregisteredSource" in obs and "def open_writer(" in obs,
          "a scheduled writer's unregistered source is refused (open_writer)")
    check("resolve_basket(symbols or SYMBOLS" in src("altdata/sources/yfinance_source.py"),
          "the yfinance basket's keys come from the Security Master's resolver")


class FakeMaster:
    def __init__(self, keys: dict, blocked: set):
        self.keys, self.blocked = keys, blocked

    def is_restricted(self, ident, scheme=None, on=None):
        return ident in self.blocked

    def resolve(self, ident, scheme, on=None):
        return {"identifiers": {"store_key": f"yfinance.{self.keys[ident]}"}}


def group_b() -> None:
    from unittest import mock
    from altdata.sources import yfinance_source as ys
    head("B. THE BLOCKLIST AT THE BASKET'S RESOLVER")
    seed = {"SPY": "mkt_spy", "BAM": "mkt_bam", "QQQ": "mkt_qqq"}
    fake = FakeMaster(dict(seed), {"BAM"})
    hits: list = []
    with mock.patch.object(ys, "_master", lambda on=None: fake), \
            mock.patch.object(ys.log, "warning") as warn:
        out = ys.resolve_basket(seed, restricted=hits)
    check(out == seed, f"every key is unchanged, the restricted one included ({out})")
    check(hits == ["BAM"] and warn.called
          and "restricted" in str(warn.call_args),
          "the restricted name is logged and listed, never dropped")
    with mock.patch.object(ys, "_master", lambda on=None: fake):
        plain = ys.resolve_basket(seed)
    check(plain == out, "without a list to fill, the resolution is the same")
    logging.disable(logging.CRITICAL)
    try:
        real_hits: list = []
        with_check = ys.resolve_basket(ys.SYMBOLS, restricted=real_hits)
    finally:
        logging.disable(logging.NOTSET)
    check(with_check and all(with_check[s] for s in ys.SYMBOLS),
          f"on the real master the {len(with_check)} symbols resolve; restricted "
          f"in the basket: {real_hits or 'none'}")
    psrc = src("altdata/sources/yfinance_source.py")
    check('"restricted": restricted' in psrc,
          "pull()'s summary carries the restricted names it saw")


def group_c() -> None:
    head("C. NO LITERAL TICKER IN THE BASKET'S CALL SITES")
    tree = ast.parse(src("altdata/sources/yfinance_source.py"))
    fns = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    bad = []
    for name in ("pull", "pull_crypto_basket"):
        for n in ast.walk(fns[name]):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) \
                    and "mkt_" in n.value:
                bad.append(f"{name}: {n.value!r}")
    check(not bad, f"pull() and pull_crypto_basket() carry no `mkt_` literal ({bad or 'none'})")
    calls = [n for n in ast.walk(fns["pull"]) if isinstance(n, ast.Call)
             and getattr(n.func, "id", None) == "resolve_basket"]
    check(len(calls) == 1, "pull() resolves its basket once, through resolve_basket")


def group_d() -> None:
    from unittest import mock
    from altdata import observations
    from altdata.sources import fedboard as fb
    head("D. H.4.1 INCREMENTAL ONCE HELD")
    check(fb.h41_url(False) == fb.URL_H41 and "lastobs=520&" in fb.h41_url(False),
          "nothing held: the full ten years (lastobs 520), the URL the writer always used")
    check("lastobs=8&" in fb.h41_url(True)
          and fb.h41_url(True).replace("lastobs=8&", "lastobs=520&") == fb.URL_H41,
          "held: the stated overlap of 8 Wednesdays, the URL otherwise unchanged")
    empty = observations.ObservationStore(str(TD / "empty.db"))
    held = observations.ObservationStore(str(TD / "held.db"))
    try:
        for k in fb.KEYS_H41:
            held.write(k, None, "2026-10-14", "2026-10-15T20:30:00+00:00", 1.0,
                       source="frb_h41")
        half = observations.ObservationStore(str(TD / "half.db"))
        half.write(fb.KEYS_H41[0], None, "2026-10-14", "2026-10-15T20:30:00+00:00", 1.0,
                   source="frb_h41")
        check(not fb._h41_held(empty) and fb._h41_held(held) and not fb._h41_held(half),
              "held means every FIMA key stored; one missing key reads the full window")
        half.close()
        asked = []

        def fake_get(url, timeout=None):
            asked.append(url)
            raise RuntimeError("fixture: no fetch")
        with mock.patch.object(fb, "http_get_response", fake_get):
            for st in (empty, held):
                try:
                    fb._produce_h41({}, st)
                except RuntimeError:
                    pass
        check(len(asked) == 2 and "lastobs=520&" in asked[0] and "lastobs=8&" in asked[1],
              "the pull asks for the full window first, then the overlap once held")
    finally:
        empty.close()
        held.close()


def main() -> int:
    for g in (group_a, group_b, group_c, group_d):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
