"""
Signal-triage Batch 16 item 88(a) (B75): the Weekly gold block.

  A  PLACEMENT. The `gold` section sits between Plumbing & rates and Positioning
     & flows in config order, at the Weekly only (deep: about 400 words); the
     close and the Monthly lay out without it; assemble places it there.
  B  NOT STORED. On an empty store every line prints "not stored" where its key
     is absent (the tape, each flows row, GVZ, the beta), the official bid "no
     record", the squeeze flag "not stored", the targets "not yet built".
  C  THE BLOCK ON A FIXTURE STORE. The tape (close, the week, from the record and
     the 200-day by hand, the run below it, realised vol), the attribution line
     on a 2-sigma week, the flows at 1 week, 3 months and 12 months by hand, the
     checklist, the Ahead line ranked 1-5 from the calendar's rows, GLD's levels
     line; the render's length printed.
  D  BEFORE THE FIRST EDITION. The 1 Nov Weekly prints the header and "First
     edition 8 Nov." and asks for no prose; no chart.
  E  THE LEDGER. The checklist's pre-registration on file at its SHA-256 (LF
     bytes), "Never edited"; the first edition cites that hash.
  F  THE CHART. W13 joins the plan after W3 inside the cap of 10 (so the plan's
     last chart is set aside, counted); it draws gold's close, its 200-day and
     the record; with too few closes it is unavailable, never faked.
  G  THE PROSE PATH. The section goes through the stack's commentary path with
     its own note (report only, no target, a tell never "a low is in"); the
     Weekly build wires the section and the before-first mark.

Synthetic fixtures only: no live store, no network, no model.

    python tools/validate_weekly_gold_block.py
"""

from __future__ import annotations

import datetime as dt
import hashlib
import math
import random
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gate_tmp  # noqa: E402

from altdata import gold_attribution as ga  # noqa: E402
from altdata import observations  # noqa: E402
from daily_cascade import gold_block as gb  # noqa: E402
from daily_cascade import stack as stack_mod  # noqa: E402

PASS = FAIL = 0
LINE = "=" * 78
CFG = ga.config()
PREREG = "docs/ledgers/gold-exhaustion-preregistration-2026-10.md"
PREREG_SHA = "7883f4554bfa4fc463f96d3ca9d7afeacf2c0d7bcd3ffce4eac15b01ca133ade"
ENDING = "2026-11-08"
NOW = "2026-11-08T10:00:00+00:00"


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


def sessions(n: int, end: str = "2026-11-06") -> list[str]:
    d, out = dt.date.fromisoformat(end), []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= dt.timedelta(days=1)
    return out[::-1]


DAYS = sessions(700)


def walk(start: float, vol: float, seed: int, last: float | None = None):
    r, v, out = random.Random(seed), start, []
    for i, d in enumerate(DAYS):
        if i:
            v *= math.exp(r.gauss(0, vol))
        out.append((d, v))
    if last is not None:
        out[-1] = (DAYS[-1], out[-2][1] * (1 + last))
    return out


def seeded_store() -> tuple[str, dict]:
    db = str(Path(gate_tmp.mkdtemp("goldblock_")) / "chester.db")
    k = CFG["keys"]
    data = {k["gold"]: walk(4000.0, 0.01, 1, last=-0.07),
            k["real_yield"]: [(d, 2.0 + 0.001 * i) for i, d in enumerate(DAYS)],
            k["breakeven"]: [(d, 2.3) for d in DAYS],
            k["dollar"]: walk(100.0, 0.004, 4), k["spx"]: walk(6000.0, 0.01, 5),
            k["ndx"]: walk(500.0, 0.012, 6), k["brent"]: walk(90.0, 0.015, 7),
            k["yield_10y"]: [(d, 4.5) for d in DAYS],
            "etf.gld_shares": [(d, 300e6 + 1e5 * i) for i, d in enumerate(DAYS)],
            "etf.gld_tonnes": [(d, 900.0 + 0.1 * i) for i, d in enumerate(DAYS)]}
    rows = []
    for key, pts in data.items():
        rows += [{"registry_key": key, "observed_at": d, "value": float(v),
                  "available_at": f"{d}T21:30:00+00:00", "source": "fixture"}
                 for d, v in pts]
    rows += [{"registry_key": "cftc.dis_managed_money_net", "instrument": "GOLD",
              "observed_at": d, "value": 150000.0 + 100 * i,
              "available_at": f"{d}T21:30:00+00:00", "source": "fixture"}
             for i, d in enumerate(DAYS[::5])]
    with observations.ObservationStore(db) as st:
        st.write_many(rows)
    return db, data


def _stub_built(extra: dict) -> dict:
    b = {sid: {"items": [stack_mod.item(f"{sid}:x", f"{sid} line", 2, 1)]}
         for sid in stack_mod.SECTION_ORDER}
    b.update(extra)
    return b


def flat_text(sec: dict) -> str:
    out = [it["text"] for it in sec.get("items") or []]
    for ss in sec.get("subsections") or []:
        out += list(ss.get("lines") or [])
        for r in (ss.get("table") or {}).get("rows") or []:
            out += [str(c) for c in r]
    return "\n".join(out + list(sec.get("not_tracked") or []))


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. PLACEMENT")
    cfg = stack_mod.config()
    ids = [s["id"] for s in cfg["sections"]]
    i = ids.index("gold")
    spec = cfg["sections"][i]
    check(ids.index("plumbing") < i < ids.index("positioning")
          and spec.get("weekly") == "deep" and not spec.get("daily")
          and not spec.get("monthly"),
          "the gold row: after Plumbing & rates, before Positioning & flows, the Weekly "
          "only, deep")
    built = _stub_built({"gold": {"items": [stack_mod.item("gold:x", "Gold line", 1, 1)]}})
    wk = stack_mod.section_ids(cfg, "weekly", built)
    check(wk.index("plumbing") + 1 == wk.index("gold") == wk.index("positioning") - 1,
          f"assemble's Weekly order places it between the two ({wk})")
    check("gold" not in stack_mod.section_ids(cfg, "daily", built)
          and "gold" not in stack_mod.section_ids(cfg, "monthly", built),
          "the close and the Monthly lay out without it")
    secs = stack_mod.assemble(built, cfg, None, "weekly")
    g = next(s for s in secs if s["id"] == "gold")
    check(g["title"] == "Gold" and g["depth"] == "deep", "assembled at its depth")


def group_b() -> None:
    head("B. NOT STORED")
    db = str(Path(gate_tmp.mkdtemp("goldblock_empty_")) / "chester.db")
    with observations.ObservationStore(db) as st:
        sec = gb.weekly_section(st, NOW, ENDING)
    txt = flat_text(sec)
    tape = sec["subsections"][0]["table"]["rows"]
    check(tape == [["Gold (COMEX front future)", "not stored (yfinance.mkt_gold_front)"]],
          "the tape: not stored")
    flows = sec["subsections"][2]["table"]["rows"]
    check(all(r[1] == "not stored" for r in flows),
          f"each flows row: not stored ({len(flows)} rows)")
    check("The 60-day beta: not stored." in txt and "no record" in txt
          and "Sell-side targets: not yet built (Tranche B)." in txt,
          "the beta not stored, the official bid 'no record', the targets not yet built")
    check(any(x.startswith("not stored: no GVZ") for x in sec["not_tracked"])
          and any("squeeze-risk flag" in x for x in sec["not_tracked"]),
          "GVZ and the squeeze flag listed as not stored")
    check("Exhaustion checklist, 0 of 4 ticked" in txt and txt.count("not stored") >= 8,
          "the checklist with every tell not stored")


def group_c() -> None:
    head("C. THE BLOCK ON A FIXTURE STORE")
    db, data = seeded_store()
    gold = data[CFG["keys"]["gold"]]
    events = [{"date": "2026-11-12", "time": "08:30", "event": "CPI", "tier": 1,
               "cls": "inflation_print"},
              {"date": "2026-11-10", "time": "13:00", "event": "10-year auction",
               "tier": 2, "cls": "coupon_benchmark"},
              {"date": "2026-11-11", "time": "16:00", "event": "AAPL earnings",
               "tier": 3, "cls": "earnings"}]
    with observations.ObservationStore(db) as st:
        sec = gb.weekly_section(st, NOW, ENDING, events=events)
    t = sec["data"]["gold"]["tape"]
    close = gold[-1][1]
    ma = statistics.fmean(v for _, v in gold[-200:])
    rec = max(v for _, v in gold)
    check(abs(t["close"] - close) < 1e-9 and abs(t["ma200"] - ma) < 1e-9
          and abs(t["from_record_pct"] - (close / rec - 1) * 100) < 1e-9,
          "close, the 200-day and the distance from the record by hand")
    wk = [v for d, v in gold if d <= "2026-10-30"][-1]
    check(abs(t["week_pct"] - (close / wk - 1) * 100) < 1e-9, "the week's change by hand")
    lr = [math.log(b / a) for (_, a), (_, b) in zip(gold, gold[1:])]
    check(abs(t["vol20"] - statistics.stdev(lr[-20:]) * math.sqrt(252) * 100) < 1e-9
          and t["run_below"] >= 1, "realised vol by hand; the run below the 200-day")
    txt = flat_text(sec)
    fd = sec["data"]["gold"]["fired_days"]
    check(fd and fd[-1] == DAYS[-1] and txt.count("The five lenses") == 2
          and (len(fd) == 1 or "Also past 2σ this week" in txt),
          f"the week's newest 2-sigma day with its five lenses, the others by date ({fd})")
    flows = {r[0]: r for r in sec["subsections"][2]["table"]["rows"]}
    sh = dict(data["etf.gld_shares"])
    want = sh[DAYS[-1]] - sh[[d for d in DAYS if d <= "2026-10-30"][-1]]
    check(flows["GLD shares outstanding"][2] == f"{want:+,.0f}"
          and flows["IAU shares outstanding"][1] == "not stored"
          and flows["CFTC managed money, net (COMEX gold)"][1].endswith(")"),
          "the flows at 1 week by hand; IAU not stored; CFTC managed money read")
    ah = next(it["text"] for it in sec["items"] if it["key"] == "gold:ahead")
    check(ah == "Ahead for gold: 1. CPI (2026-11-12); 2. 10-year auction (2026-11-10).",
          f"the Ahead line ranked from the calendar's rows ({ah})")
    check(any(it["key"] == "gold:gld_levels" and "GLD's dealer levels" in it["text"]
              for it in sec["items"]), "GLD's levels line")
    cfg = stack_mod.config()
    secs = stack_mod.assemble(_stub_built({"gold": sec}), cfg, None, "weekly")
    g = next(s for s in secs if s["id"] == "gold")
    from daily_cascade import stack_render                     # noqa: PLC0415
    html = stack_render.section_html(g, 6, {}, "email", "weekly")
    words = len(flat_text(sec).split())
    print(f"        the block's fixture render: {len(html):,} characters of HTML, "
          f"{words} words of lines and cells before prose")
    check(not g.get("empty") and "Gold" in html and len(html) > 1000,
          f"renders through the stack's renderer ({len(html):,} characters)")


def group_d() -> None:
    head("D. BEFORE THE FIRST EDITION")
    db = str(Path(gate_tmp.mkdtemp("goldblock_first_")) / "chester.db")
    with observations.ObservationStore(db) as st:
        sec = gb.weekly_section(st, "2026-11-01T10:00:00+00:00", "2026-11-01")
    cfg = stack_mod.config()
    built = _stub_built({"gold": sec})
    secs = stack_mod.assemble(built, cfg, None, "weekly")
    gb.mark_before_first(secs, built)
    g = next(s for s in secs if s["id"] == "gold")
    check(g["empty"] and g["empty_note"] == "First edition 8 Nov.",
          "the 1 Nov Weekly: the header and 'First edition 8 Nov.', no prose")
    from daily_cascade import weekly_stack                     # noqa: PLC0415
    plan = weekly_stack.chart_plan({"sections": secs, "budget": {"charts": 10}})
    check("W13" not in plan, "and no chart")


def group_e() -> None:
    head("E. THE LEDGER")
    raw = (REPO / PREREG).read_bytes().replace(b"\r\n", b"\n")
    check(hashlib.sha256(raw).hexdigest() == PREREG_SHA and b"Never edited" in raw,
          "the pre-registration on file at its SHA-256 (LF bytes), 'Never edited'")
    check(ga.prereg_sha(CFG) == PREREG_SHA and CFG["exhaustion"]["preregistration"] == PREREG,
          "the module reads the same hash from the config's path")
    ed = (REPO / "docs" / "ledgers" / "gold-exhaustion-ledger-2026-10-26.md").read_text(
        encoding="utf-8")
    check(PREREG_SHA in ed and "INSUFFICIENT" in ed and "**Rights:** none." in ed,
          "the first edition cites the hash, prints its n and grants nothing")
    weeks = [{"week": f"w{i}", "oil_below_100": "ticked" if i % 2 else "clear",
              "ten_falling_oil_rising": "clear", "gold_up_equity_down": "not stored",
              "liquidation_flip": "clear", "gold_5d_pct": 1.0,
              "gold_20d_pct": (3.0 if i % 2 else -1.0) + 0.1 * (i % 5),
              "gold_60d_pct": None} for i in range(80)]
    st = ga.ledger_stats(weeks, CFG)
    check(st["oil_below_100"]["verdict"] == "PASS" and st["oil_below_100"]["t"] > 2
          and st["ten_falling_oil_rising"]["verdict"] == "INSUFFICIENT"
          and st["gold_up_equity_down"]["verdict"] == "INSUFFICIENT",
          "the pass rule: Welch t at 2 with 30 a side; INSUFFICIENT below")


def group_f() -> None:
    head("F. THE CHART")
    from daily_cascade import weekly_stack                     # noqa: PLC0415
    cfg = stack_mod.config()
    built = _stub_built({"gold": {"items": [stack_mod.item("gold:x", "Gold", 1, 1)]}})
    secs = stack_mod.assemble(built, cfg, None, "weekly")
    plan = weekly_stack.chart_plan({"sections": secs, "budget": {"charts": 10}})
    check(plan.index("W13") == plan.index("W3") + 1 and len(plan) == 10
          and "W10" not in plan,
          f"W13 after W3, inside the cap of 10, the last set aside ({plan})")
    cap = cfg["budget"]["weekly"]["charts"]
    full = weekly_stack.chart_plan({"sections": secs, "budget": {"charts": cap}})
    check(cap == 11 and len(full) == 11 and "W13" in full and "W10" in full,
          f"at the ruled cap of 11 (26 Oct 2026) W13 pushes nothing out ({full})")
    check(weekly_stack.PLACE["W13"] == ("gold", None), "placed in the gold section")
    _, data = seeded_store()
    cs = gb.chart_series(data[CFG["keys"]["gold"]], ENDING, CFG)
    from daily_cascade import charts as charts_mod             # noqa: PLC0415
    c = charts_mod.gold_chart("W13", cs, "w13_fixture", None)
    check(not c.get("unavailable") and c["png_bytes"] > 0
          and c["drawn"][0]["label"] == "record" and "200-day" in c["caption"],
          "it draws the close, the 200-day and the record")
    check(len(cs["close"]) <= 523 and cs["ma200"] and cs["close"][-1][0] == DAYS[-1],
          "over the chart's window (two years)")
    u = charts_mod.gold_chart("W13", {"close": cs["close"][:5]}, "x", None)
    check(u.get("unavailable"), "too few closes: unavailable, never faked")


def group_g() -> None:
    head("G. THE PROSE PATH")
    from daily_cascade import stack_prose                      # noqa: PLC0415
    note = stack_prose.WEEKLY_NOTES.get("gold") or ""
    check("Report only" in note and "never a target" in note and "a low is in" in note,
          "the section's commentary note")
    src = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    check("gold_block.weekly_section(" in src and "gold_block.mark_before_first(" in src
          and "charts_mod.gold_chart(" in src,
          "the Weekly builds the section, marks the first edition and draws W13")
    sec = {"id": "gold", "title": "Gold", "depth": "deep", "items": [], "data": {}}
    p = stack_prose.section_prompt(sec, "weekly")
    check("GOLD, IN A DESK'S VOICE" in p, "the prompt carries the note at the Weekly")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
