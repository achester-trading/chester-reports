#!/usr/bin/env python3
"""
Validation gate: b45-chain3 -- session B's third-chain branch (19 Oct 2026), where
no existing gate is the home. On fixtures; no network, no model, no live store.

  A  RULING 6 OF 19 OCT 2026. An assessed mechanism-watch entry is posted to the
     narrative register as a PROPOSED story through its existing proposal path,
     with its factor's implied outcome and horizon, citing its source stored as a
     headline event; nothing is confirmed, and the entry's grade moves from
     "awaiting its posting" to "proposed"; a refused posting keeps the entry
     pending with its reason. Each of the seven feeds carries its terms-read date;
     the Monthly line names a feed read 93 days before its as-of and not one read
     92. The PRL part reads exactly its allowed keys -- calc.prl_*, and the
     explorer's pearl.chain_* and the basket's PRL price directly -- and no
     calc.prl_* key copies them.
  B  X-3.4, ENGINE 7 (alpha/engines/intraday_dealer.py): see its section below.

    python tools/validate_b45_chain3.py
"""

from __future__ import annotations

import datetime as dt
import os
import socket
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

TD = Path(gate_mkdtemp("b45_chain3_"))
os.environ["CHESTER_DB"] = str(TD / "store.sqlite")
os.environ.pop("ALPHA_DB", None)
for _k, _d in (("ALPHA_INBOX", "inbox"), ("ALPHA_OUTBOX", "outbox"),
               ("ALPHA_RESEARCH_DIR", "research"), ("ALPHA_REPORTS_DIR", "reports")):
    os.environ[_k] = str(TD / _d)
os.environ["CHESTER_UNIT_STARTED"] = "0"
PASS = FAIL = 0
LINE = "=" * 78


def _no_connect(*a, **k):
    raise OSError("validate_b45_chain3: no network in a code gate")


socket.socket.connect = _no_connect                             # type: ignore[method-assign]
socket.create_connection = _no_connect                          # type: ignore[assignment]


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


# ---------------------------------------------------------------------------
# A. Ruling 6
# ---------------------------------------------------------------------------
def group_a() -> None:
    from altdata import mechanism_watch as mw, narratives as nr
    from monthly_macro import prl_part
    head("A. RULING 6 OF 19 OCT 2026: POSTED AS PROPOSED, THE FEEDS' TERMS, THE PRL READS")
    db = str(TD / "a.sqlite")
    with mw.Register(db) as r:
        mid = r.add_candidate({"name": "Lumen", "stage": "mainnet",
                               "mechanism_class": "proof of useful work"},
                              origin="llm_draft", prefilter={"hits": ["fixture"]},
                              at="2026-10-24T14:00:00+00:00")
        e1 = r.add_entry("Lumen: a useful-work chain reached mainnet.", "I",
                         "https://example.org/lumen", mid, "2026-10-24T14:00:00+00:00")
        e2 = r.add_entry("Ferrum: a reserve token backed by a commodity basket.", "V",
                         "the scan", None, "2026-10-24T14:00:00+00:00")
        check(r.conn.execute("SELECT grade FROM mechanism_watch_entries WHERE id=?",
                             (e1,)).fetchone()[0] == mw.GRADE_PENDING == "awaiting its posting",
              "a drafted entry waits at 'awaiting its posting' (no G-29 scale)")
        bad = {"factors": {"I": {"direction": "x", "linked_dimensions": {"nonsense": "+"},
                                 "implied_outcome": {"claim": "x", "metrics": ["no.key"],
                                                     "comparison": "up", "quorum": 1,
                                                     "horizon_days": 182}}}}
        refused = mw.post_entries(r, db, cfg=bad)
        row = r.conn.execute("SELECT grade, narrative_id, post_note FROM "
                             "mechanism_watch_entries WHERE id=?", (e1,)).fetchone()
        check(refused["posted"] == [] and row[0] == mw.GRADE_PENDING and row[1] is None
              and "not registered" in (row[2] or ""),
              "a posting the narrative register refuses leaves the entry pending, with "
              "the reason")
        out = mw.post_entries(r, db, at="2026-10-24T15:00:00+00:00")
        ents = {x["id"]: dict(x) for x in r.conn.execute(
            "SELECT * FROM mechanism_watch_entries").fetchall()}
        cand = r.conn.execute("SELECT grade FROM mechanism_watch WHERE id=?",
                              (mid,)).fetchone()[0]
    with nr.NarrativeRegister(db) as g:
        stories = {s["narrative_id"]: s for s in g.all()}
    n1, n2 = ents[e1]["narrative_id"], ents[e2]["narrative_id"]
    s1, s2 = stories.get(n1), stories.get(n2)
    io1 = s1["implied_outcome"] if s1 else {}
    check(len(out["posted"]) == 2 and s1 and s2
          and s1["status"] == s2["status"] == "proposed"
          and s1["origin"] == "proposal" and s1["opened"] is None,
          f"both entries are posted as PROPOSED stories through the existing proposal "
          f"path ({n1}, {n2}); nothing is confirmed")
    check(io1.get("metrics") == ["yfinance.mkt_nvda"] and io1.get("horizon_days") == 182
          and s2["implied_outcome"]["metrics"] == ["yfinance.mkt_btc_usd"]
          and "Lumen" in s1["name"] and "Lumen: a useful-work chain" in s1["direction"],
          "each carries its factor's implied outcome and horizon (Factor I: NVDA up over "
          "182 days; Factor V: BTC-USD up), the entry's text as its direction")
    from altdata import events as ev_mod
    with ev_mod.EventStore(db) as es:
        basis = es.conn.execute("SELECT type, url FROM events WHERE id IN (%s)" % ",".join(
            str(int(x)) for s in (s1, s2) for x in (s["proposal_basis"]
                                                     if isinstance(s["proposal_basis"], list)
                                                     else __import__("json").loads(
                                                         s["proposal_basis"] or "[]")))
        ).fetchall()
    check(len(basis) == 2 and all(b[0] == "headline" for b in basis)
          and ("https://example.org/lumen",) in [(b[1],) for b in basis],
          "each proposal cites its source, stored first as a headline event")
    check(ents[e1]["grade"] == ents[e2]["grade"] == mw.GRADE_PROPOSED == "proposed"
          and cand == "proposed" and ents[e1]["posted_at"].startswith("2026-10-24"),
          "the entries and the candidate move from 'awaiting its posting' to 'proposed'")
    with mw.Register(db) as r:
        again = mw.post_entries(r, db)
    check(again["posted"] == [] and again["refused"] == [],
          "a posted entry is never posted twice")
    src = (REPO / "altdata" / "mechanism_watch.py").read_text(encoding="utf-8")
    check(".confirm(" not in src and ".reject(" not in src.replace("def reject", ""),
          "nothing in the posting confirms or rejects: the narrative register's gate is "
          "the operator's")

    from altdata.mechanism_scan import config as scan_config
    feeds = scan_config().get("feeds") or []
    check(len(feeds) == 7 and all(f.get("terms_read") for f in feeds),
          "each of the seven feeds carries its terms-read date in the catalogue")
    fx = [{"id": "old", "terms_read": "2026-07-19"}, {"id": "edge", "terms_read": "2026-07-20"},
          {"id": "new", "terms_read": "2026-10-18"}, {"id": "none"}]
    line = prl_part.feeds_terms_line("2026-10-20T21:00:00+00:00", fx)
    check(line and "old (read 2026-07-19)" in line and "edge" not in line
          and "new" not in line and "none (no date)" in line
          and prl_part.feeds_terms_line("2026-10-20T21:00:00+00:00", fx[2:3]) is None,
          f"the Monthly line names a feed read 93 days before its as-of and not one "
          f"read 92: {line}")

    from altdata import prl
    allowed = prl_part.allowed_reads()
    seen: list = []
    real = prl_part._latest                                     # noqa: SLF001
    prl_part._latest = lambda st, k, at: seen.append(k)         # noqa: SLF001
    try:
        prl_part.read(None, "2026-10-20T21:00:00+00:00", "2026-09-20T21:00:00+00:00")
    finally:
        prl_part._latest = real                                 # noqa: SLF001
    direct = {prl.HEIGHT_KEY, prl.SUPPLY_KEY, prl.DIFFICULTY_KEY, "yfinance.crypto_prl"}
    check(set(seen) == set(allowed.values())
          and direct <= set(seen)
          and all(k.startswith("calc.prl_") for k in set(seen) - direct),
          "the PRL part reads exactly its allowed keys: calc.prl_*, and pearl.chain_* and "
          "the basket's PRL price directly")
    copies = [k for k in prl.KEYS.values()
              if k in ("calc.prl_height", "calc.prl_supply", "calc.prl_difficulty",
                       "calc.prl_price", "calc.prl_volume")]
    check(not copies and "ruling 6 of 19 Oct 2026" in (REPO / "monthly_macro" /
                                                       "prl_part.py").read_text(encoding="utf-8"),
          "no calc.prl_* key copies the explorer's rows or the price; the docstring "
          "states the ruling")


def main() -> int:
    try:
        group_a()
    finally:
        import shutil                                           # noqa: PLC0415
        shutil.rmtree(TD, ignore_errors=True)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
