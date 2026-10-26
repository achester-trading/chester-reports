"""
Signal-triage Batch 16 items 87 and 88(d) (B75): gold's five-lens attribution,
the 60-day real-yield beta, and gold on exception in the daily close.

  A  THE TRIGGER. The move screen's own sigma and window (its five-year history
     of 1- and 5-day log changes, population sigma, today's excluded), the
     order's 2: a quiet day does not fire, a 2-sigma day does, the z by hand;
     fewer closes than the screen's 500 is "not read", never a guess.
  B  THE FIVE LENSES, by hand over the lead horizon: the real yield and the
     breakeven in bp, the dollar in %, the liquidation correlation with the S&P
     500 and the Nasdaq-100 (QQQ) and the day's signs, the squeeze flag "not
     stored", the official bid "no record" until a dated record exists and then
     the latest on or before the day (never a later one); a lens whose key is
     absent prints "not stored".
  C  THE BETA. OLS by hand over the last 60 paired sessions, with its n and
     window; "absent" below 40 pairs.
  D  THE TELLS. Each of the four ticked and clear on a constructed week, by hand;
     a missing input is "not stored".
  E  THE CLOSE ON EXCEPTION (88(d)). A quiet day prints nothing; a 2-sigma day
     prints the move and the five lenses in one line; a tell that flips prints
     the tell; the close's hook and its store path are wired, never on a dry run.
  F  THE ROWS. The beta each session and the five lenses on a fired day, JSON
     bodies (no level a screen would read), source registered, available at the
     compute instant; the backfill writes through the store and a second pass
     duplicates nothing; the keys registered and barred from the market-state
     object; no vendor, model or register import.

Synthetic fixtures only: no live store, no network, no model.

    python tools/validate_gold_attribution.py
"""

from __future__ import annotations

import ast
import datetime as dt
import json
import math
import random
import re
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gate_tmp  # noqa: E402
import yaml  # noqa: E402

from altdata import gold_attribution as ga  # noqa: E402
from altdata import move_screen  # noqa: E402

PASS = FAIL = 0
LINE = "=" * 78
CFG = ga.config()
MS = move_screen.load_config()


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


def sessions(n: int, end: str = "2026-10-23") -> list[str]:
    d, out = dt.date.fromisoformat(end), []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= dt.timedelta(days=1)
    return out[::-1]


def walk(days: list[str], start: float, vol: float, seed: int,
         last: float | None = None) -> list[tuple[str, float]]:
    r = random.Random(seed)
    v, out = start, []
    for i, d in enumerate(days):
        if i:
            v *= math.exp(r.gauss(0, vol))
        out.append((d, v))
    if last is not None:
        out[-1] = (days[-1], out[-2][1] * (1 + last))
    return out


def levels(days: list[str], start: float, step: float, seed: int
           ) -> list[tuple[str, float]]:
    r = random.Random(seed)
    v, out = start, []
    for d in days:
        v += r.gauss(0, step)
        out.append((d, v))
    return out


DAYS = sessions(700)
DAY = DAYS[-1]


def quiet_tail(pts: list[tuple[str, float]], n: int = 6) -> list[tuple[str, float]]:
    """The last `n` closes drift up 0.1% a session: no 2-sigma move on either arm."""
    base = pts[-n - 1][1]
    return pts[:-n] + [(d, base * 1.001 ** (i + 1)) for i, (d, _) in enumerate(pts[-n:])]


def series(last: float | None = 0.08, **over) -> dict:
    g = walk(DAYS, 4000.0, 0.01, 1, last)
    s = {"gold": quiet_tail(g) if last is None else g,
         "real_yield": levels(DAYS, 2.0, 0.03, 2),
         "breakeven": levels(DAYS, 2.3, 0.02, 3),
         "dollar": walk(DAYS, 100.0, 0.004, 4),
         "spx": walk(DAYS, 6000.0, 0.01, 5),
         "ndx": walk(DAYS, 500.0, 0.012, 6),
         "brent": walk(DAYS, 90.0, 0.015, 7),
         "yield_10y": levels(DAYS, 4.5, 0.04, 8),
         "official_ifs_china": [("2026-07-01", 160760.0), ("2026-08-01", 321507.0)],
         "official_records": []}
    s.update(over)
    return s


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A. THE TRIGGER")
    quiet = ga.trigger(series(last=None)["gold"], DAY, CFG, MS)
    check(quiet["state"] == "read" and not quiet["fired"] and abs(quiet["z1"]) < 2,
          f"a quiet day does not fire (z1 {quiet['z1']:+.2f}, z5 {quiet['z5']:+.2f})")
    s = series()
    tr = ga.trigger(s["gold"], DAY, CFG, MS)
    g = s["gold"]
    lo = (dt.date.fromisoformat(DAY) - dt.timedelta(days=int(MS["history_days"]))).isoformat()
    hist = [math.log(g[i][1] / g[i - 1][1]) for i in range(1, len(g) - 1)
            if g[i - 1][0] >= lo]
    z = (math.log(g[-1][1] / g[-2][1]) - statistics.fmean(hist)) / statistics.pstdev(hist)
    check(tr["fired"] and tr["lead"] == 1 and round(z, 2) == tr["z1"],
          f"an 8% day fires on the 1-day arm, z by hand {z:+.2f} = {tr['z1']:+.2f}")
    check(tr["sigma"] == 2.0 and CFG["trigger"]["sigma"] == 2.0
          and tr["n_changes"] == len(hist),
          "at the order's 2 sigma, on the move screen's window and its count")
    check(abs(tr["move_pct"] - round(math.log(1.08) * 100, 2)) < 1e-9,
          f"the move is the log change, % ({tr['move_pct']})")
    short = ga.trigger(g[-300:], DAY, CFG, MS)
    check(short["state"] == "not read" and not short["fired"]
          and "fewer than the move screen's 500" in short["reason"],
          "fewer closes than the screen's 500: not read, never fired")
    check(ga.trigger(g, "2026-10-24", CFG, MS)["state"] == "absent",
          "no close on the day: absent")
    check("past 2σ" in ga.trigger_text(tr) and "no 2σ move" in ga.trigger_text(quiet),
          "the trigger's text")


def group_b() -> None:
    head("B. THE FIVE LENSES")
    s = series()
    tr = ga.trigger(s["gold"], DAY, CFG, MS)
    att = ga.lenses(s, tr, CFG)
    start = DAYS[-2]
    ry = dict(s["real_yield"])
    check(att["start"] == start and att["horizon"] == 1
          and att["real_yield"]["change"] == round((ry[DAY] - ry[start]) * 100, 2)
          and att["real_yield"]["unit"] == "bp",
          f"the real yield in bp over the lead horizon ({att['real_yield']['change']})")
    be, dx = dict(s["breakeven"]), dict(s["dollar"])
    check(att["breakeven"]["change"] == round((be[DAY] - be[start]) * 100, 2)
          and att["dollar"]["change"] == round((dx[DAY] / dx[start] - 1) * 100, 2),
          "the breakeven in bp, the dollar in %")
    g, e = ga.log_returns(s["gold"]), ga.log_returns(s["spx"])
    days = sorted(e)[-20:]
    c = statistics.correlation([g[d] for d in days], [e[d] for d in days])
    lq = att["liquidation"]
    check(lq["legs"]["S&P 500"]["corr"] == round(c, 2) and lq["legs"]["S&P 500"]["n"] == 20
          and "Nasdaq-100 (QQQ)" in lq["legs"],
          f"the liquidation correlation by hand over 20 sessions ({c:+.2f}), and the "
          f"Nasdaq-100 through QQQ")
    check(lq["squeeze"].startswith("not stored") and "not stored" in ga.lens_text("liquidation", lq),
          "filed item 74's squeeze flag prints 'not stored'")
    ob = att["official_bid"]
    check(ob["record"] is None and ga.official_text(ob).startswith("no record")
          and abs(ob["ifs_china"]["tonnes"] - 10.0) < 0.05,
          "the official bid: 'no record' with no dated record, and the IMF IFS China line")
    recs = [{"date": "2026-09-01", "source": "press", "figure": "~25 t, August",
             "outlet": "a press estimate"},
            {"date": "2026-11-01", "source": "WGC", "figure": "later", "outlet": "WGC"}]
    s2 = series(official_records=recs)
    ob2 = ga.lenses(s2, tr, CFG)["official_bid"]
    check(ob2["record"]["date"] == "2026-09-01" and "~25 t, August" in ga.official_text(ob2),
          "the latest record on or before the day, never a later one")
    s3 = series(breakeven=[])
    att3 = ga.lenses(s3, tr, CFG)
    check(att3["breakeven"]["state"] == "not stored"
          and "not stored" in ga.lens_text("breakeven", att3["breakeven"]),
          "a lens whose key is absent prints 'not stored'")
    ln = ga.lenses_line(att)
    check(all(ga.LENS_LABEL[k].lower() in ln for k in ga.LENSES),
          "the five lenses in one line")
    recs_cfg = yaml.safe_load((REPO / "config" / "gold_official_bid.yaml")
                              .read_text(encoding="utf-8"))
    check(recs_cfg["records"] == [], "the official-bid file holds no session-entered figure")


def group_c() -> None:
    head("C. THE BETA")
    s = series()
    b = ga.beta(s, DAY, CFG)
    g = ga.log_returns(s["gold"])
    r = ga.diffs(s["real_yield"], 100.0)
    days = sorted(d for d in g if d in r)[-60:]
    xs, ys = [r[d] for d in days], [g[d] for d in days]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    hand = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    check(b["state"] == "computed" and b["n"] == 60 and b["window"] == 60
          and b["beta"] == round(hand, 4),
          f"OLS by hand over 60 sessions ({hand:+.4f})")
    check("60 sessions" in ga.beta_text(b) and "a basis point" in ga.beta_text(b),
          "printed with its window and n")
    thin = ga.beta(series(real_yield=s["real_yield"][-30:]), DAY, CFG)
    check(thin["state"] == "absent" and thin["n"] < 40, "below 40 pairs: absent")


def _flat(days, v):
    return [(d, v) for d in days]


def group_d() -> None:
    head("D. THE TELLS")
    s = series(last=None)
    w = DAYS[-6:]
    brent = s["brent"][:-6] + [(d, 94.0 + i) for i, d in enumerate(w)]
    y10 = s["yield_10y"][:-6] + [(d, 4.5 - 0.02 * i) for i, d in enumerate(w)]
    t = ga.tells(series(last=None, brent=brent, yield_10y=y10), DAY, CFG)
    check(t["oil_below_100"]["state"] == "ticked" and t["ten_falling_oil_rising"]["state"]
          == "ticked", "oil below $100 and the 10-year falling while oil rises: ticked")
    brent2 = s["brent"][:-6] + [(d, 110.0 - i) for i, d in enumerate(w)]
    t2 = ga.tells(series(last=None, brent=brent2, yield_10y=y10), DAY, CFG)
    check(t2["oil_below_100"]["state"] == "clear"
          and t2["ten_falling_oil_rising"]["state"] == "clear", "and clear when not")
    gold = s["gold"][:-6] + [(d, 4000.0 + 10 * i) for i, d in enumerate(w)]
    spx = s["spx"][:-6] + [(d, 6000.0 - 10 * i) for i, d in enumerate(w)]
    t3 = ga.tells(series(last=None, gold=gold, spx=spx), DAY, CFG)
    check(t3["gold_up_equity_down"]["state"] == "ticked", "gold up on an equity-down day")
    spx_up = s["spx"][:-6] + [(d, 6000.0 + 10 * i) for i, d in enumerate(w)]
    t4 = ga.tells(series(last=None, gold=gold, spx=spx_up), DAY, CFG)
    check(t4["gold_up_equity_down"]["state"] == "clear", "and clear with both up")
    # The flip: gold moving with the S&P for months, then against it for the last
    # 14 sessions -- positive a week before (8 of 20 against), negative now.
    def pair(against: int):
        r = random.Random(11)
        eq, gl = [(DAYS[0], 6000.0)], [(DAYS[0], 4000.0)]
        for i, d in enumerate(DAYS[1:], 1):
            x = 0.01 * (1 if i % 2 else -1) * (1 + 0.1 * (i % 3))
            sign = -1 if i >= len(DAYS) - against else 1
            eq.append((d, eq[-1][1] * math.exp(x)))
            gl.append((d, gl[-1][1] * math.exp(sign * x + r.gauss(0, 0.001))))
        return gl, eq
    gl, eq = pair(0)
    t5 = ga.tells(series(last=None, gold=gl, spx=eq), DAY, CFG)
    check(t5["liquidation_flip"]["state"] == "clear"
          and "correlation" in (t5["liquidation_flip"].get("reading") or ""),
          f"moving together all along: clear ({t5['liquidation_flip'].get('reading')})")
    gl, eq = pair(14)
    t7 = ga.tells(series(last=None, gold=gl, spx=eq), DAY, CFG)
    check(t7["liquidation_flip"]["state"] == "ticked",
          f"gold turned against the S&P: the flip ticks "
          f"({t7['liquidation_flip'].get('reading')})")
    t8 = ga.tells(series(last=None, brent=[], spx=[]), DAY, CFG)
    check(t8["oil_below_100"]["state"] == "not stored"
          and t8["gold_up_equity_down"]["state"] == "not stored",
          "a missing input is 'not stored'")
    ln = ga.tells_line(t, CFG)
    check(ln.startswith("Exhaustion checklist, ") and "ticked" in ln, "the checklist's line")


def group_e() -> None:
    head("E. THE CLOSE ON EXCEPTION (88(d))")
    quiet = ga.close_line(series(last=None), DAY, CFG, MS)
    check(quiet is None, "a quiet day prints nothing")
    loud = ga.close_line(series(), DAY, CFG, MS)
    check(loud and loud["line"].startswith("Gold +") and "The five lenses" in loud["line"]
          and all(ga.LENS_LABEL[k].lower() in loud["line"] for k in ga.LENSES),
          f"a 2-sigma day prints the move and the five lenses in one line "
          f"({len(loud['line']) if loud else 0} characters)")
    s = series(last=None)
    brent = s["brent"][:-1] + [(DAY, 99.0)]
    brent[-2] = (brent[-2][0], 101.0)
    fl = ga.close_line(series(last=None, brent=brent), DAY, CFG, MS)
    check(fl and "oil_below_100" in fl["flipped"] and "Exhaustion tell flipped" in fl["line"]
          and "Oil below $100 (Brent) now ticked" in fl["line"],
          "a tell that flips prints the tell")
    stack = (REPO / "daily_cascade" / "stack.py").read_text(encoding="utf-8")
    sc = (REPO / "daily_cascade" / "stack_close.py").read_text(encoding="utf-8")
    check("gold_block.close_extras(built, st" in stack and "gold_block.store_rows(" in sc,
          "the close calls the block, and stores its rows through the close's write path")
    from daily_cascade import gold_block                        # noqa: PLC0415
    check(gold_block.close_lines(series(last=None), DAY) == []
          and len(gold_block.close_lines(series(), DAY)) == 1,
          "the block adds no line on a quiet day and one on a fired day")


def group_f() -> None:
    head("F. THE ROWS")
    s = series()
    ev = ga.evaluate(s, DAY, CFG, MS)
    rows = ga.rows_for(ev, "2026-10-23T21:00:00+00:00")
    keys = sorted(r["registry_key"] for r in rows)
    check(keys == sorted([ga.BETA_KEY] + [f"gold.attr.{k}" for k in ga.LENSES]),
          "a fired day: the beta and the five lenses")
    check(all(isinstance(r["value"], str) and json.loads(r["value"]) for r in rows)
          and all(r["source"] == "gold_attribution" for r in rows),
          "JSON bodies under the registered source")
    q = ga.rows_for(ga.evaluate(series(last=None), DAY, CFG, MS), "2026-10-23T21:00:00+00:00")
    check([r["registry_key"] for r in q] == [ga.BETA_KEY], "a quiet day: the beta only")
    from altdata import observations                           # noqa: PLC0415
    db = str(Path(gate_tmp.mkdtemp("goldattr_")) / "chester.db")
    with observations.open_writer("gate:gold_attribution", db) as st:
        short = {k: (v[-560:] if isinstance(v, list) and v and isinstance(v[0], tuple) else v)
                 for k, v in s.items()}
        out = ga.backfill(short, CFG, "2026-10-26T15:00:00+00:00", MS, since=DAYS[-30])
        n1 = st.write_many(out["rows"])
        n2 = st.write_many(out["rows"])
        got = st.as_of(ga.BETA_KEY, "2026-10-26T16:00:00+00:00")
        early = st.as_of(ga.BETA_KEY, "2026-10-26T14:00:00+00:00")
    check(n1 == len(out["rows"]) and n2 == 0 and out["fired"] >= 1,
          f"the backfill writes through an opened writer; a second pass duplicates "
          f"nothing ({n1} rows, {out['fired']} fired)")
    check(len(got) == 30 and not early,
          "available at the compute instant, never backdated")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    want = [f"gold.attr.{k}" for k in ga.LENSES] + [ga.BETA_KEY]
    check(all(k in reg["metrics"] and reg["metrics"][k]["trigger_eligible"] is False
              for k in want), "the six keys registered, trigger_eligible false")
    barred = [p for b in reg.get("market_state_barred") or [] for p in b["keys"]]
    check("gold.attr.*" in barred and ga.BETA_KEY in barred,
          "and barred from the market-state object")
    ms = (REPO / "config" / "market_state.yaml").read_text(encoding="utf-8")
    check("gold.attr" not in ms and "gold.beta" not in ms, "the object's config names none")
    src = (REPO / "altdata" / "gold_attribution.py").read_text(encoding="utf-8")
    mods = set()
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.ImportFrom):
            mods.add(n.module or "")
        elif isinstance(n, ast.Import):
            mods |= {a.name for a in n.names}
    check(not any(m and re.search(r"flashalpha|vendor|anthropic|model_meter|register|"
                                  r"narrative|regime", m) for m in mods),
          f"no vendor, model, register or regime import ({sorted(m for m in mods if m)})")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f):
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
