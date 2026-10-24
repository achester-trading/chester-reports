#!/usr/bin/env python3
"""
The a47 chain (session A's third chain, 19 Oct 2026): what has no other home.

  A  CD-9'S DAILY PARAGRAPH, BY HAND: six computed lines on a fixture store -- the
     T-1 ETF flows with streak and percentile (S-2), a stale ETF line with its
     date, aggregate funding with the z's date (ruling 5 of 17 Oct), the open
     interest's change on the day, the DVOL band, Fear & Greed in the publisher's label.
  B  THE SWITCH: off by default (the order's D4/D6 precondition is not recorded
     as met), so the anchor prints nothing and the close adds no sub-section; on,
     both carry it. BTC dominance is never in it.
  C  THE BUDGETS: at most six lines; the close's prose count is the same with the
     paragraph as without it (lines are data); the anchor's lines are short.
  D  NO FLAG, NO FETCH, NO MODEL: the paragraph reads no calc.flag_* key; no new
     module imports a network library or a model path; no by-hand key.
  E  THE 12:30 LINE: registered in midday_gate.GATES; closed, reading nothing,
     until config names a PASS S-3 ledger; the slot then writes nothing. With a
     PASS ledger (a fixture) and the day's flag stored, it opens; a FAIL ledger
     keeps it closed.
  F  THE MONTHLY'S ONE REVISION: prose.ATTEMPTS is audit_retry's; a section that
     fails twice is withheld after exactly two calls, the second carrying the
     rule, the failing span and the draft.
  G  THE S-2 AND S-3 LEDGERS: each script exists, reads no store, labels its
     edition, carries its pass rule as the order states it and a dated first
     edition with its CSV; each states the rights it would grant and grants none;
     the box re-run commands write to ~/chester-data/ledgers.

No gate here reads the live store, fetches, or calls a model.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp                                    # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
TD = Path(mkdtemp("a47-chain3-gate-"))
NOW = "2026-10-17T11:00:00+00:00"


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


def obs(key: str, day: str, value: float, inst=None) -> dict:
    return {"registry_key": key, "instrument": inst, "observed_at": day,
            "available_at": f"{day}T21:00:00+00:00", "value": value, "source": "fixture"}


def fixture_store() -> str:
    from altdata import observations
    path = str(TD / "crypto.db")
    rows = [obs("farside.btc_total", "2026-10-15", 50_000_000.0),
            obs("farside.btc_total", "2026-10-16", 123_400_000.0),
            obs("calc.etf_streak", "2026-10-16", 3.0, "btc"),
            obs("calc.etf_5d_pct", "2026-10-16", 96.2, "btc"),
            obs("farside.eth_total", "2026-10-09", -20_000_000.0),
            obs("calc.funding_agg", "2026-10-16", 8.5, "BTC"),
            obs("calc.funding_agg", "2026-10-16", 11.25, "ETH"),
            obs("calc.oi_usd", "2026-10-15", 50e9),
            obs("calc.oi_usd", "2026-10-16", 51e9),
            obs("deribit.dvol_btc", "2026-10-16", 45.0),
            obs("calc.dvol_pct_full", "2026-10-16", 50.0, "BTC"),
            obs("deribit.dvol_eth", "2026-10-16", 70.0),
            obs("calc.dvol_pct_full", "2026-10-16", 85.0, "ETH"),
            obs("fng.value", "2026-10-16", 30.0),
            obs("paprika.btc_dominance", "2026-10-16", 58.0),
            # A flag stored "on": the paragraph must not print it.
            obs("calc.flag_leverage_crowded", "2026-10-16", 1.0, "BTC")]
    with observations.ObservationStore(path) as st:
        st.write_many(rows)
    return path


WANT = [
    "BTC spot ETF flows (T-1): +$123.4m on 16 Oct 2026; streak 3 inflow sessions; "
    "the 5-day sum at the 96th percentile since January 2024.",
    "ETH spot ETF flows (T-1): STALE, last good 9 Oct 2026.",
    "Perp funding, OI-weighted across exchanges (annualised): BTC 8.50%; z-score "
    "from 15 Dec 2026; ETH 11.25%; z-score from 15 Dec 2026 (16 Oct 2026).",
    "Perp open interest, BTC + ETH: $51.0bn, +2.0% on the day (16 Oct 2026).",
    "Implied vol (DVOL): BTC 45.0, normal; ETH 70.0, stressed (16 Oct 2026).",
    "Fear & Greed: fear (16 Oct 2026).",
]


def _cfg(enabled: bool) -> dict:
    from altdata.sources import _crypto as C
    cfg = C.config()
    return {**cfg, "blocks": {**cfg["blocks"],
                              "daily": {**cfg["blocks"]["daily"], "enabled": enabled}}}


def group_a(db: str) -> None:
    head("A. CD-9'S DAILY PARAGRAPH, BY HAND")
    from altdata import crypto_blocks as CB, observations
    with observations.ObservationStore(db) as st:
        b = CB.daily_paragraph(st, NOW, _cfg(True))
    for i, (got, want) in enumerate(zip(b["lines"], WANT), 1):
        check(got == want, f"line {i}: {got}")
    check(len(b["lines"]) == 6 and b["title"] == "Crypto (positioning and flows)"
          and b["paragraph_wanted"] is False,
          "six computed lines under Positioning and flows; no model paragraph")
    cfg = _cfg(True)
    words = [CB.fng_word(v, cfg) for v in (0, 24, 25, 50, 60, 90)]
    check(words == ["extreme fear", "extreme fear", "fear", "neutral", "greed",
                    "extreme greed"],
          f"Fear & Greed in the publisher's labels, by the session-set bands "
          f"(ruled 20 Oct 2026) ({words})")


def group_b(db: str) -> None:
    head("B. THE SWITCH")
    from altdata import crypto_blocks as CB
    from altdata.sources import _crypto as C
    live = C.config()
    check(live["blocks"]["daily"]["enabled"] is False,
          "the switch ships OFF: the order's D4/D6 precondition is not recorded as met")
    check(CB.daily_paragraph_from_store(NOW, db) is None and CB.daily_html(None) == "",
          "off, the anchor's reader returns nothing and prints nothing")
    on = CB.daily_paragraph_from_store(NOW, db, _cfg(True))
    check(on and on["lines"] == WANT and "Fear &amp; Greed: fear" in CB.daily_html(on),
          "on, the anchor prints the six lines")
    pay = (REPO / "daily_cascade" / "morning_payload.py").read_text(encoding="utf-8")
    ren = (REPO / "daily_cascade" / "morning_render.py").read_text(encoding="utf-8")
    stk = (REPO / "daily_cascade" / "stack.py").read_text(encoding="utf-8")
    check("crypto_blocks.daily_paragraph_from_store(cutoff, db_path)" in pay
          and '"crypto_paragraph": crypto' in pay
          and 'crypto_blocks.daily_html(payload.get("crypto_paragraph"))' in ren
          and 'built.get("positioning") is not None and crypto_blocks.daily_enabled()' in stk
          and 'built["positioning"].setdefault("subsections", []).append(' in stk,
          "the anchor and the close each carry it through one hook, the close's only "
          "while the switch is on, as a Positioning & flows sub-section")
    txt = " ".join(WANT).lower()
    check("dominance" not in txt and "58.0" not in txt,
          "BTC dominance is left out (CoinGecko's /global is retired)")
    units = list((REPO / "deploy" / "systemd").glob("*.timer"))
    check(not any("21:45" in u.read_text(encoding="utf-8") and "crypto" in u.name
                  for u in units),
          "no 21:45 ETF-refresh unit is added (no 21:45 report run exists)")


def group_c(db: str) -> None:
    head("C. THE BUDGETS")
    from altdata import crypto_blocks as CB, observations
    from daily_cascade import stack
    with observations.ObservationStore(db) as st:
        b = CB.daily_paragraph(st, NOW, _cfg(True))
    base = {"id": "positioning", "claim": "Positioning held.",
            "paragraphs": ["Speculators added to yen longs on the week."],
            "items": [], "subsections": []}
    withp = {**base, "subsections": [b]}
    check(stack.section_words(withp) == stack.section_words(base),
          f"the close's prose count is unchanged by the paragraph "
          f"({stack.section_words(base)} words either way): it displaces nothing in "
          f"the 2,250-word target (D19/D20)")
    check(len(b["lines"]) <= 6 and max(len(x.split()) for x in b["lines"]) <= 40,
          "at most six lines, none past 40 words, in the anchor")
    from altdata.sources import _crypto as C
    check(int(C.config()["blocks"]["daily"]["max_lines"]) == 6,
          "the six-line cap is config's")


def group_d() -> None:
    head("D. NO FLAG, NO FETCH, NO MODEL, NO BY-HAND KEY")
    src = (REPO / "altdata" / "crypto_blocks.py").read_text(encoding="utf-8")
    check('"calc.flag' not in src and "FLAG_KEYS" not in src,
          "the paragraph reads no flag key (a stored flag set 'on' prints nowhere: A)")
    bad = []
    for rel in ("altdata/crypto_blocks.py", "daily_cascade/crypto_gate.py"):
        tree = ast.parse((REPO / rel).read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            mods = ([a.name for a in n.names] if isinstance(n, ast.Import) else
                    [n.module or ""] if isinstance(n, ast.ImportFrom) else [])
            for m in mods:
                if re.match(r"(requests|urllib|http|socket|anthropic|httpx)\b|"
                            r"altdata\.(model_meter|sources\.(farside|hl|fut|deribit|fng|"
                            r"paprika|crypto_derived))", m):
                    bad.append(f"{rel}: {m}")
    check(not bad, f"no network library, model path or crypto writer imported ({bad or 'none'})")
    new = "\n".join((REPO / p).read_text(encoding="utf-8") for p in
                    ("altdata/crypto_blocks.py", "daily_cascade/crypto_gate.py",
                     "config/crypto_sources.yaml"))
    check("manual." not in new, "no by-hand key")


def group_e(db: str) -> None:
    head("E. THE 12:30 LINE: CLOSED UNTIL THE S-3 LEDGER PASSES")
    from daily_cascade import crypto_gate as CG, midday_gate as mg
    check(mg.GATES[-1].__name__ == "_crypto_leverage", "registered in midday_gate.GATES")
    ghost = TD / "never-opened.db"
    shut = CG.leverage_gate({"day": "2026-10-16", "db_path": str(ghost)})
    check(not shut["open"] and shut["line"] is None and "has not passed" in shut["why"]
          and not ghost.exists(),
          f"with no admitting ledger it is closed and opens no store ({shut['why']})")
    res = mg.run("2026-10-16", gates=[mg._crypto_leverage], out_dir=TD / "alerts",
                 ctx={"day": "2026-10-16", "db_path": db})
    check(not res["opened"] and res["alert"] is None and not (TD / "alerts").exists()
          and res["model_called"] is False,
          "the closed slot prints and writes nothing, and calls no model")
    led = TD / "s-3-ledger-fixture.md"
    led.write_text("| Verdict | **PASS** (fixture) |\n", encoding="utf-8")
    from altdata.sources import _crypto as C
    base = C.config()
    adm = {**base, "blocks": {**base["blocks"], "midday_leverage":
                              {"admitted_by": str(led), "admitted_verdict": "PASS"}}}
    op = CG.leverage_gate({"day": "2026-10-17", "db_path": db}, cfg=adm)
    check(op["open"] and "no setup rights" in op["line"],
          "with a PASS ledger named and the prior session's flag stored, it opens at "
          "12:30: one information line, no setup rights")
    quiet = CG.leverage_gate({"day": "2026-10-16", "db_path": db}, cfg=adm)
    check(not quiet["open"],
          "the day's own flag is not knowable at 12:30 (computed after the close): closed")
    led.write_text("| Verdict | **FAIL** (fixture) |\n", encoding="utf-8")
    fl = CG.leverage_gate({"day": "2026-10-17", "db_path": db}, cfg=adm)
    check(not fl["open"] and "FAIL" in fl["why"], "a FAIL ledger keeps it closed")


class _Resp:
    def __init__(self, text: str) -> None:
        self.content = [SimpleNamespace(type="text", text=text)]
        self.model = "fixture"
        self.stop_reason = "end_turn"
        self.usage = SimpleNamespace(input_tokens=10, output_tokens=10)


def group_f() -> None:
    head("F. THE MONTHLY'S ONE REVISION")
    from daily_cascade import audit_retry
    from monthly_macro import prose
    check(prose.ATTEMPTS == audit_retry.ATTEMPTS == 2,
          "the Monthly writer's attempts are the stack's: the draft and one revision")
    calls: list = []

    class _Msgs:
        def create(self, **kw):
            calls.append(kw.get("system") or "")
            return _Resp("Bank reserves rose 999 basis points on the month.")

    client = SimpleNamespace(messages=_Msgs())
    sec = [{"key": "probe", "title": "Probe pillar", "scope": "One paragraph.",
            "paragraphs": "exactly 1",
            "slice": {"series": [{"series": "Bank reserves", "change": 12.0}]}}]
    w = prose.write_all({}, client=client, secs=sec)["probe"]
    check(not w["published"] and w["attempts"] == 2 and len(calls) == 2
          and len(w.get("reasons") or []) == 2,
          f"a section that fails twice is withheld after exactly two calls "
          f"({w['state']}, {len(calls)} calls)")
    rev = calls[1] if len(calls) > 1 else ""
    check("WITHHELD BY THE AUDIT" in rev and "THE RULE" in rev
          and "YOUR DRAFT:\n<<<\n" in rev and "999" in rev
          and "Revise THAT draft" in rev and "That draft was attempt 1 of 2." in rev,
          "the revision carries the rule it broke, the failing span and the draft")
    src = (REPO / "monthly_macro" / "prose.py").read_text(encoding="utf-8")
    check("ATTEMPTS = audit_retry.ATTEMPTS" in src
          and 'res.get("state") == "too_long" and res["attempts"] < ATTEMPTS:' in src,
          "too-long is the one revision too: never a third call")


def group_g() -> None:
    head("G. THE S-2 AND S-3 LEDGERS")
    import glob
    for item, script in (("S-2", "s2_etf_flows.py"), ("S-3", "s3_leverage.py")):
        p = REPO / "tools" / "calibration" / script
        if not check(p.is_file(), f"{item}: tools/calibration/{script} exists"):
            continue
        src = p.read_text(encoding="utf-8")
        check(not re.search(r"ObservationStore|observations|derived_forms|regime\.", src),
              f"{item}: the script reads no store (public sources only)")
        eds = sorted(glob.glob(str(REPO / "docs" / "ledgers" /
                                   f"{item.lower()}-ledger-*.md")))
        if not check(eds, f"{item}: a dated first edition in docs/ledgers/"):
            continue
        t = Path(eds[0]).read_text(encoding="utf-8")
        check("laptop run, public sources" in t
              and re.search(r"^\| Verdict \| \*\*(PASS|FAIL|INSUFFICIENT)", t, re.M)
              and "| Pass rule (as the order states it) |" in t
              and Path(eds[0][:-3] + "-episodes.csv").is_file(),
              f"{item}: the first edition is labelled, carries its verdict, its pass rule "
              f"and its CSV ({Path(eds[0]).name})")
        check("grants nothing" in t.lower() or "granted nothing" in t.lower()
              or "stated, not granted" in t.lower(),
              f"{item}: it states the rights it would grant, and grants none")
    notes = (REPO / "docs" / "briefs" / "a47-chain3-notes.md")
    nt = notes.read_text(encoding="utf-8") if notes.is_file() else ""
    check("s2_etf_flows.py --box --out ~/chester-data/ledgers" in nt
          and "s3_leverage.py --box --out ~/chester-data/ledgers" in nt,
          "the box re-run commands write to ~/chester-data/ledgers")
    from altdata.sources import _crypto as C
    m = C.config()["blocks"]["midday_leverage"]
    check(m.get("admitted_by") is None,
          "nothing admits the S-3 line: no ruling has named a passing ledger")


def main() -> int:
    db = fixture_store()
    for g, args in ((group_a, (db,)), (group_b, (db,)), (group_c, (db,)),
                    (group_d, ()), (group_e, (db,)), (group_f, ()), (group_g, ())):
        try:
            g(*args)
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
