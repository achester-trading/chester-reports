"""
Validation gate for the Book B scanner (altdata/book_b_scanner.py;
docs/briefs/book-b-scanner-brief-2026-10-12.md, ruled 12 Oct 2026). On a
synthetic store of its own, no network, no box, no register write; the ledger
rows go to the dry-run namespace only.

  A  THE PIVOTS. One breakout (XLK: a 57-session base cleared on 3x volume),
     one reclaim (GLD: the 50-day lost and taken back on volume), one failed
     breakdown (IWM: a close below the base low, back above in two sessions);
     a breakout on its 1x days does not fire; a pivot with no stored volume
     fires "unconfirmed" and says so; a restricted instrument never enters the
     universe. The parameters print beside each candidate.
  B  AGAINST THE TAPE. QQQ, a long breakout in a primary downtrend: tagged,
     a five-session time stop, no add; a with-trend candidate keeps fifteen.
  C  CONFIRMATIONS. TLT's crowd on the same side prints a WARNING and leads
     the counter-thesis; a crowd the other way confirms (GLD, IWM, QQQ); a
     long with no confirmation is refused; unmet confirmations are the
     counter-thesis; a T&B top signal raises the long bar to two.
  D  THE SHORT SIDE. XLY's breakdown, with relative strength and a consumer
     tell behind it, is refused in Expansion-Calm-Positive and accepted in
     Overheat with two confirmations; the Gamma dial's timing is the regime
     card's words (Doctrine 5.2): negative trusts breakouts, positive waits for
     the retest, the flip zone opens no new entries; the Volatility dial's
     multiplier is printed in the size.
  E  SCORE AND RANK. The score is the weighted mean of its five components;
     the list is ranked by it; the block prints the top N and the rest go to
     the reference tier, one row each.
  F  THE LEDGER. Every candidate a forecast "+1R before -1R within six weeks"
     under its setup and id, in the dry-run namespace and nowhere else;
     resolved from stored closes as they come; the Weekly's graded-calls line
     reports the candidates on their own line, never pooled.
  G  THE BLOCK. W-1.3a's section-10 block prints the scanner's candidates in
     its ruled shape; the "activates when the scanner merges" line is gone.
  H  THE FOLLOW-UPS (ruled 13 Oct 2026). A VIX of 17 is the object's `normal`
     and the Doctrine's Normal: no short opens and no 0.75 applies; every
     candidate carries risk_usd from its size and the paper capital; the volume
     legs read the stored daily volume, by its unit; the earnings names enter
     the universe where their closes are stored.

    python tools/validate_book_b_scanner.py
"""

from __future__ import annotations

import datetime as dt
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gate_tmp                                                 # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
ENDING = "2026-10-09"                     # a Friday
N = 260


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


# ---------------------------------------------------------------------------
# The synthetic store
# ---------------------------------------------------------------------------
def sessions(n: int = N, ending: str = ENDING) -> list[str]:
    d, out = dt.date.fromisoformat(ending), []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= dt.timedelta(days=1)
    return out[::-1]


def zz(i: int, amp: float) -> float:
    return amp if i % 2 else -amp


def lin(a: float, b: float, n: int) -> list[float]:
    return [a + (b - a) * k / (n - 1) for k in range(n)]


def paths() -> dict[str, dict]:
    """symbol -> {close, volume (or None), high/low (or None)}; index 259 is
    Friday 9 Oct, 257 Wednesday 7 Oct."""
    out = {}
    # SPY, the benchmark: a smooth rise.
    out["SPY"] = {"close": [400 * 1.0005 ** i for i in range(N)]}
    # XLK, THE BREAKOUT: a trend, a 57-session base at 150 (+-1.5), cleared on
    # Wednesday on 3x volume; Thursday and Friday hold it on ordinary volume.
    c = [v + zz(i, 0.3) for i, v in enumerate(lin(100, 150, 200))]
    c += [150 + zz(i, 1.5) for i in range(57)] + [156.0, 157.0, 158.0]
    vol = [1e6] * N
    vol[257] = 3e6
    out["XLK"] = {"close": c, "volume": vol,
                  "high": [x * 1.004 for x in c], "low": [x * 0.996 for x in c]}
    # TLT, THE CROWDED SAME WAY: XLK's shape, the speculative crowd long.
    c = [v + zz(i, 0.2) for i, v in enumerate(lin(90, 120, 200))]
    c += [120 + zz(i, 1.0) for i in range(57)] + [124.0, 124.5, 125.0]
    out["TLT"] = {"close": c, "volume": vol}
    # GLD, THE RECLAIM: a rise, a dip under the 50-day for nine sessions, taken
    # back on Wednesday on 2x volume.
    c = lin(150, 199.6, 247) + [196.0, 191.0] + [191 + zz(i, 1.0) for i in range(8)] \
        + [199.0, 200.0, 201.0]
    v = [1e6] * N
    v[257] = 2e6
    out["GLD"] = {"close": c, "volume": v}
    # IWM, THE FAILED BREAKDOWN: a base at 200 (+-2), a close below it on
    # Monday the 5th, back above on Wednesday; ordinary volume throughout.
    c = lin(180, 200, 200) + [200 + zz(i, 2.0) for i in range(54)] \
        + [195.0, 194.0, 199.0, 200.0, 200.5, 201.0]
    out["IWM"] = {"close": c, "volume": [1e6] * N}
    # QQQ, AGAINST THE TAPE: a downtrend, a 25-session base, a long breakout;
    # NO VOLUME STORED (the leg unconfirmed).
    c = lin(400, 300, 230) + [300 + zz(i, 3.0) for i in range(25)] \
        + [305.0, 306.0, 307.0, 308.0, 309.0]
    out["QQQ"] = {"close": c}
    # XLY, THE SHORT: a downtrend, a base, broken on Wednesday on 3x volume.
    c = [v + zz(i, 0.3) for i, v in enumerate(lin(200, 150, 200))]
    c += [150 + zz(i, 1.5) for i in range(57)] + [144.0, 143.0, 142.0]
    out["XLY"] = {"close": c, "volume": vol}
    # XLP, flat: the consumer tell's denominator.
    out["XLP"] = {"close": [70 + zz(i, 0.3) for i in range(N)]}
    # BN, RESTRICTED: XLK's breakout, which must never be scanned.
    out["BN"] = {"close": list(out["XLK"]["close"]), "volume": vol}
    return out


def positioning_rows(days: list[str]) -> list[dict]:
    """Weekly CFTC rows, two years: UST30Y crowded long (TLT's warning); GOLD,
    RUSSELL2000 and NDX100 crowded short (a crowd the other way confirms)."""
    weeks = [d for d in days if dt.date.fromisoformat(d).weekday() == 1][-100:]
    last = {"UST30Y": 9000.0, "GOLD": -9000.0, "RUSSELL2000": -9000.0,
            "NDX100": -9000.0}
    rows = []
    for c, lv in last.items():
        for k, d in enumerate(weeks):
            v = lv if k == len(weeks) - 1 else 1000.0 * zz(k, 1.0) + 50 * (k % 7)
            rows.append({"registry_key": "cftc.noncomm_net", "instrument": c,
                         "observed_at": d, "available_at": d + "T21:00:00+00:00",
                         "value": v, "source": "cftc"})
    return rows


def seed_store(db: str) -> dict:
    from altdata import observations
    from altdata.sources import yfinance_source as yf
    days = sessions()
    key = {s: "yfinance." + yf.SYMBOLS.get(s, "mkt_" + s.lower()) for s in paths()}
    rows = []
    for sym, p in paths().items():
        k = key[sym]
        for comp, vals in (("", p["close"]), ("_volume", p.get("volume")),
                           ("_high", p.get("high")), ("_low", p.get("low"))):
            for d, v in zip(days, vals or []):
                rows.append({"registry_key": k + comp, "instrument": None,
                             "observed_at": d, "available_at": d + "T20:20:00+00:00",
                             "value": float(v), "source": "yfinance"})
    rows += positioning_rows(days)
    with observations.ObservationStore(db) as st:
        st.write_many(rows)
    return {"days": days, "keys": key}


ECP = {"macro": "Expansion", "vol": "Calm", "gamma": "Positive"}
OVERHEAT = {"macro": "Overheat", "vol": "Calm", "gamma": "Negative"}


def vol_state_at(vix: float) -> str:
    """The object's Volatility state at a VIX level, by its own level bands
    (config/market_state.yaml: the first band whose min_level the level meets)."""
    import yaml                                                 # noqa: PLC0415
    ms = yaml.safe_load((REPO / "config" / "market_state.yaml").read_text(
        encoding="utf-8"))
    for b in ms["dials"]["vol"]["level_bands"]:
        if vix >= float(b.get("min_level", 0)):
            return str(b["state"])
    raise AssertionError("no band")


def group_h(cfg: dict, res: dict, db: str, cut: str) -> None:
    import json                                                 # noqa: PLC0415
    import regime                                               # noqa: PLC0415
    from altdata import book_b_scanner as bbs                   # noqa: PLC0415
    from altdata import observations                            # noqa: PLC0415
    from altdata.sources import yfinance_source as yf           # noqa: PLC0415
    from daily_cascade import book_b                            # noqa: PLC0415
    print(f"\n{LINE}\nH. THE FOLLOW-UPS (ruled 13 Oct 2026)\n{LINE}")

    # 3. A VIX OF 17. The object's state from its own bands, stored as fifteen
    # sessions of an Expansion object, read back through the scanner's reader.
    st17 = vol_state_at(17.0)
    rdb = str(Path(gate_tmp.mkdtemp("bbs_vix17_")) / "obs.db")
    with observations.ObservationStore(rdb) as st:
        for d in sessions()[-15:]:
            obj = {"object": "market_state", "session": d,
                   "computed_at": f"{d}T20:50:00+00:00",
                   "dials": {"macro": {"state": "expansion"},
                             "vol": {"state": st17, "level": 17.0},
                             "gamma": {"state": "positive"}},
                   "dimensions": {}, "contradictions": []}
            st.write(regime.STORE_KEY, None, d, obj["computed_at"], json.dumps(obj),
                     source="derived_state")
        reg17 = bbs.regime_read(st, cut, cfg)
    check(st17 == "normal" and reg17["vol"] == "Normal" and reg17["macro"] == "Expansion",
          f"a VIX of 17 is the object's `{st17}` and reads as the Doctrine's Normal, "
          f"not Rising ({reg17})")
    ok, why = bbs.short_permitted(reg17, cfg)
    m, mwhy = bbs.multiplier(reg17, cfg)
    r17 = bbs.scan(ENDING, db, cutoff=cut, regime=reg17, cfg=cfg)
    xly17 = {(c["instrument"], c["direction"]): c for c in r17["refused"]}.get(
        ("XLY", "short"))
    check(not ok and xly17 and xly17["refused"].startswith(
        "no short in Expansion, Normal, Positive")
          and not any(c["direction"] == "short" for c in r17["candidates"]),
          f"a VIX of 17 opens no shorts: XLY's breakdown is refused "
          f"({xly17 and xly17['refused']})")
    # (The store carries C's top signal by now, so the long bar is two: the
    # check reads whichever long stands, its size the standard tier.)
    x17 = next((c for c in r17["candidates"] if c["direction"] == "long"), None)
    check(m == 1.0 and x17 and x17["size"].startswith("0.75% of capital at risk "
                                                      "(0.75% × 1: Volatility Normal 1)"),
          f"and no 0.75 multiplier: the size is the standard tier "
          f"({x17 and x17['size'][:70]})")
    check(bbs.short_permitted({"macro": "Expansion", "vol": "Rising"}, cfg)[0]
          and bbs.multiplier({"vol": "Rising"}, cfg)[0] == 0.75,
          "shorts open and the 0.75 applies at the dial's Rising or worse")

    # SECOND RULING, 1: A VIX OF 24. The object's `elevated` is the Doctrine's
    # Rising: shorts open, at 0.75. Read back the same way as the 17.
    st24 = vol_state_at(24.0)
    rdb24 = str(Path(gate_tmp.mkdtemp("bbs_vix24_")) / "obs.db")
    with observations.ObservationStore(rdb24) as st:
        for d in sessions()[-15:]:
            obj = {"object": "market_state", "session": d,
                   "computed_at": f"{d}T20:50:00+00:00",
                   "dials": {"macro": {"state": "expansion"},
                             "vol": {"state": st24, "level": 24.0},
                             "gamma": {"state": "positive"}},
                   "dimensions": {}, "contradictions": []}
            st.write(regime.STORE_KEY, None, d, obj["computed_at"], json.dumps(obj),
                     source="derived_state")
        reg24 = bbs.regime_read(st, cut, cfg)
    check(st24 == "elevated" and reg24["vol"] == "Rising"
          and cfg["regime"]["vol_map"].get("crisis") == "Crisis",
          f"a VIX of 24 is the object's `{st24}` and reads as the Doctrine's Rising; "
          f"`crisis` stays Crisis ({reg24})")
    r24 = bbs.scan(ENDING, db, cutoff=cut, regime=reg24, cfg=cfg)
    xly24 = {(c["instrument"], c["direction"]): c for c in r24["candidates"]}.get(
        ("XLY", "short"))
    check(bbs.short_permitted(reg24, cfg)[0] and xly24
          and xly24["size"].startswith("0.56% of capital at risk "
                                       "(0.75% × 0.75: Volatility Rising 0.75)"),
          f"a VIX of 24 opens shorts at 0.75: XLY's breakdown stands "
          f"({xly24 and xly24['size'][:70]})")

    # SECOND RULING, 2: THE FLIP ZONE REFUSES AT THE GATE, AND IS GRADED.
    import shutil                                               # noqa: PLC0415
    from altdata import probability_ledger as pl                # noqa: PLC0415
    flip = {"macro": "Expansion", "vol": "Calm", "gamma": "Flip-zone"}
    rf = bbs.scan(ENDING, db, cutoff=cut, regime=flip, cfg=cfg)
    fr = [r for r in rf["refused"] if r.get("graded")]
    # (By now the store carries C's top signal, so a long needs two; GLD is
    # the long that passes every other gate.)
    xf = next((r for r in fr if r["instrument"] == "GLD"), None)
    check(not rf["candidates"] and xf and xf["refused"]
          == "the Gamma dial's Flip-zone: “No new entries” (the regime card, "
             "Doctrine 5.2)" and xf["score"] is not None,
          f"the flip zone: no candidate stands; GLD goes to the refused list with "
          f"the card's words ({xf and xf['refused']})")
    subs, _ = book_b.subsections(rf["candidates"], book_b.sitting_flow(
        ENDING, None, rf["candidates"], [], rows=[]), rf)
    check(any("No new entries" in n for n in subs[0]["notes"]),
          "the block's refusal note carries the card's words")
    fdb = str(Path(gate_tmp.mkdtemp("bbs_flip_")) / "store.db")
    shutil.copyfile(db, fdb)
    # The next week's closes: GLD rises through +1R.
    with observations.ObservationStore(fdb) as st:
        st.write_many([{"registry_key": xf["key"], "instrument": None,
                        "observed_at": d, "available_at": d + "T20:20:00+00:00",
                        "value": xf["entry"] + 1.2 * xf["risk"], "source": "yfinance"}
                       for d in ("2026-10-12", "2026-10-13")])
    fid = bbs.record_forecasts(bbs.graded(rf), ENDING, ENDING + "T23:30:00+00:00",
                               fdb, dry_run=False)
    fg = bbs.grade(fdb, "2026-10-16", None, dry_run=False)
    with pl.ProbabilityLedger(fdb) as led:
        live = [r for r in led.all_rows() if r["source"] == bbs.source_name(False)]
    check(len(fid) == len(fr) >= 1 and len(live) == len(fr)
          and any("GLD long" in r["claim"] for r in live)
          and any("GLD long" in g["claim"] and g["outcome"] == 1 for g in fg),
          f"and it is still written to the ledger and graded: GLD's +1R first "
          f"resolves 1 ({len(fid)} written, {len(fg)} graded)")

    # 5. RISK_USD BY CODE.
    cap = 300000.0
    allc = res["candidates"] + r17["candidates"]
    check(allc and all(isinstance(c.get("risk_usd"), float) and c["risk_usd"] > 0
                       and abs(c["risk_usd"] - round(cap * float(
                           c["size"].split("%")[0]) / 100, 2)) < 0.01 for c in allc),
          f"every candidate carries risk_usd = its size x the paper capital "
          f"({x17 and x17['instrument']}: {x17 and x17['risk_usd']} = 0.75% of "
          f"${cap:,.0f})")
    check(x17 and x17["risk_usd"] == 2250.0
          and "= $2,250 of the $300,000 paper capital" in x17["size"]
          and "risk_usd" in book_b.FIELDS,
          "the size prints the dollars, and risk_usd is archived with the ruled "
          "fields, so the order gate never delays a taken candidate for it")

    # 1. VOLUME, BY ITS UNIT.
    xlk = next(c for c in res["candidates"] if c["instrument"] == "XLK")
    check("3.0× volume" in xlk["thesis"] and "volume not stored" not in xlk["thesis"],
          "the breakout's volume leg reads the stored daily volume")
    inst = {"days": ["d1"], "close": [100.0], "volume": {"d1": 1000.0}}
    check(bbs.dollar_volume({**inst, "vol_unit": "shares"}, 0) == 100000.0
          and bbs.dollar_volume({**inst, "vol_unit": "usd"}, 0) == 1000.0
          and bbs.dollar_volume({**inst, "vol_unit": "count"}, 0) is None,
          "dollar volume: shares x close; crypto's dollars as quoted; futures "
          "contracts give none (the multiplier is not stored)")
    check(bbs._volume_unit("GC=F") == "count"                   # noqa: SLF001
          and bbs._volume_unit("BTC-USD") == "usd"              # noqa: SLF001
          and bbs._volume_unit("AAPL") == "shares",             # noqa: SLF001
          "the unit is the source's declaration (yfinance_source.VOLUME_UNITS)")

    # 4. THE EARNINGS NAMES.
    edb = str(Path(gate_tmp.mkdtemp("bbs_earn_")) / "obs.db")
    days = sessions()
    with observations.ObservationStore(edb) as st:
        rows = []
        for sym in ("AAPL", "BRK-B"):
            k = "yfinance." + yf.SYMBOLS[sym]
            for i, d in enumerate(days):
                for comp, v in (("", 100 + 0.1 * i), ("_volume", 1e6)):
                    rows.append({"registry_key": k + comp, "instrument": None,
                                 "observed_at": d,
                                 "available_at": d + "T20:20:00+00:00",
                                 "value": v, "source": "yfinance"})
        st.write_many(rows)
        insts, skipped = bbs.load_universe(st, ENDING, cut, cfg)
    got = {i["symbol"]: i for i in insts}
    check(set(got) == {"AAPL", "BRK-B"} and got["BRK-B"]["key"] == "yfinance.mkt_brk_b"
          and got["AAPL"]["vol_source"] == "stored"
          and got["AAPL"]["vol_unit"] == "shares",
          "an earnings name with stored closes enters the universe like the rest, "
          "BRK-B by its yfinance ticker")
    check("AAPL" not in skipped["earnings_not_stored"]
          and "MSFT" in skipped["earnings_not_stored"]
          and yf.EARNINGS_SYMBOLS <= set(yf.SYMBOLS),
          "'not stored' lists only the names without closes; all 29 are in the "
          "basket (the backfill is printed in the notes)")


def main() -> int:
    from altdata import book_b_scanner as bbs
    from daily_cascade import book_b, weekly_stack
    tmp = gate_tmp.mkdtemp("bbs_")
    db = os.path.join(tmp, "store.db")
    seeded = seed_store(db)
    cfg = bbs.load_config()
    cut = ENDING + "T23:00:00+00:00"
    cal = [{"date": "2026-10-15", "event": "Consumer Price Index", "symbol": None,
            "tier1": True}]
    res = bbs.scan(ENDING, db, cutoff=cut, regime=ECP, calendar=cal, cfg=cfg)
    res_oh = bbs.scan(ENDING, db, cutoff=cut, regime=OVERHEAT, calendar=cal, cfg=cfg)
    by = {(c["instrument"], c["direction"]): c for c in res["candidates"]}
    ref = {(c["instrument"], c["direction"]): c for c in res["refused"]}

    print(f"\n{LINE}\nA. THE PIVOTS\n{LINE}")
    xlk, gld, iwm = by.get(("XLK", "long")), by.get(("GLD", "long")), by.get(("IWM", "long"))
    check(xlk and xlk["pivot"] == "breakout" and xlk["setup_id"] == "b_breakout"
          and xlk["pivot_day"] == "2026-10-07" and "3.0× volume" in xlk["thesis"]
          and "base of 60 sessions" in xlk["thesis"],
          f"XLK: a breakout from a 60-session base on 3.0x volume, graded under "
          f"b_breakout ({xlk and xlk['thesis']})")
    check(gld and gld["pivot"] == "reclaim" and gld["setup_id"] == "b_reclaim"
          and "the 50-day" in gld["thesis"] and "2.0× volume" in gld["thesis"],
          f"GLD: a reclaim of the 50-day on 2.0x volume ({gld and gld['thesis']})")
    check(iwm and iwm["pivot"] == "failed_breakdown"
          and iwm["setup_id"] == "b_failed_breakdown"
          and "back above it in 2 session(s)" in iwm["thesis"]
          and iwm["invalidation"].startswith(f"{iwm['invalidation_level']:,.2f} "
                                             "(the breakdown low 194.00"),
          f"IWM: a failed breakdown, back in two sessions; invalidation the "
          f"breakdown low less a buffer ({iwm and iwm['invalidation']})")
    check(xlk and "less a quarter of the ATR" in xlk["invalidation"]
          and "the base low" in xlk["invalidation"]
          and gld and "the 50-day" in gld["invalidation"]
          and "average close-to-close change" in gld["invalidation"],
          "invalidation: the base low (breakout), the reclaimed level (reclaim), "
          "a quarter-range buffer beyond it -- the ATR where a high and low are "
          "stored, the close-to-close change named where not")
    check(xlk and xlk["parameters"].startswith("N 60 (of 20–60), range ")
          and "≤ R 10%" in xlk["parameters"] and "volume 3.0× ≥ V 1.5×" in xlk["parameters"]
          and gld and gld["parameters"].startswith("L 10 (lost 9 before)")
          and iwm and "F 5 (back in 2)" in iwm["parameters"],
          f"the parameters print beside each candidate ({xlk and xlk['parameters']})")
    check("Pivots as set: base N 20–60 sessions, range R ≤ 10.0% of price, volume "
          "V ≥ 1.5× its 20-session average, reclaim window L 10, failed-breakdown "
          "window F 5" in res["parameters"],
          "the block's parameters line states every value as set")
    qqq = by.get(("QQQ", "long"))
    check(qqq and "volume not stored — the volume leg unconfirmed" in qqq["thesis"]
          and "not testable (volume not stored)" in qqq["parameters"],
          "no stored volume: the pivot fires 'unconfirmed' and says so")
    check(not any(c["instrument"] == "BN" for c in res["candidates"] + res["refused"])
          and "BN" in res["skipped"]["restricted"],
          "a restricted instrument never enters the universe (counted)")
    import copy
    strict = copy.deepcopy(cfg)
    strict["pivots"]["volume"]["when_absent"] = "strict"
    rs = bbs.scan(ENDING, db, cutoff=cut, regime=ECP, cfg=strict)
    check(not any(c["instrument"] == "QQQ" for c in rs["candidates"] + rs["refused"]),
          "under `strict` an unconfirmable volume leg refuses the pivot")
    # XLK's Thursday and Friday closes clear the base too, on 1x volume: the
    # pivot is Wednesday's.
    one = bbs.detect(next(i for i in bbs.load_universe(
        __import__("altdata.observations", fromlist=["x"]).ObservationStore(db),
        ENDING, cut, cfg)[0] if i["symbol"] == "XLK"), cfg)
    check([p["t"] for p in one if p["setup"] == "breakout" and p["d"] > 0] == [257],
          "a close through a base on ordinary volume is not a breakout")

    print(f"\n{LINE}\nB. AGAINST THE TAPE\n{LINE}")
    check(qqq and qqq["trend"] == "down" and qqq["against_tape"] and qqq["time_stop"] == 5
          and qqq["no_add"] and "time stop 5 sessions" in qqq["horizon"],
          f"QQQ long in a downtrend: against the tape, five-session stop, no add "
          f"({qqq and qqq['horizon']})")
    check(xlk and not xlk["against_tape"] and xlk["time_stop"] == 15
          and "time stop 15 sessions" in xlk["horizon"],
          "a with-trend candidate keeps the standard fifteen sessions (decision 5)")

    print(f"\n{LINE}\nC. CONFIRMATIONS\n{LINE}")
    tlt = by.get(("TLT", "long"))
    check(tlt and tlt["warnings"] == ["positioning crowded the same way (UST30Y z +9.4)"]
          or (tlt and tlt["warnings"] and tlt["warnings"][0].startswith(
              "positioning crowded the same way (UST30Y")),
          f"TLT: the crowd long the same way prints a WARNING ({tlt and tlt['warnings']})")
    check(tlt and tlt["counter_thesis"].startswith("positioning crowded the same way"),
          "and the warning leads the counter-thesis")
    check(all(x and any(c["family"] == "positioning" and c["met"]
                        and "crowded the other way" in c["text"]
                        for c in x["confirmations"]) for x in (gld, iwm, qqq)),
          "a crowd the other way confirms (GLD, IWM, QQQ)")
    spy = ref.get(("SPY", "long"))
    check(spy and spy["refused"] == "0 confirmation(s) of the 1 a long needs",
          f"SPY's breakout, with no confirmation, is refused ({spy and spy['refused']})")
    # The correlation layer (AQ-5) read by name where it is on the branch: the
    # break is then unmet for GLD, else not read (Friday stitching, 13 Oct).
    import importlib.util                                       # noqa: PLC0415
    corr_txt = ("unmet: no correlation break"
                if importlib.util.find_spec("altdata.correlation")
                else "not read: the correlation layer is not on this branch")
    check(gld and "unmet: no Weekly tell names it" in gld["counter_thesis"]
          and "not read: no Top & Bottom report yet" in gld["counter_thesis"]
          and corr_txt in gld["counter_thesis"],
          f"unmet and unread confirmations are the counter-thesis "
          f"({gld and gld['counter_thesis']})")
    check(xlk and any(c["family"] == "relative strength" and c["met"]
                      for c in xlk["confirmations"]) and "RS 100th percentile" in xlk["thesis"],
          "relative strength against SPY over 60 sessions, counted")
    # A T&B top signal raises the long bar to two.
    from altdata import observations
    with observations.ObservationStore(db) as st:
        st.write_many([{"registry_key": "tb.signal", "instrument": None,
                        "observed_at": ENDING, "available_at": ENDING + "T22:00:00+00:00",
                        "value": '{"signal": "top"}', "source": "derived_state"}])
    top = bbs.scan(ENDING, db, cutoff=cut, regime=ECP, cfg=cfg)
    tref = {(c["instrument"], c["direction"]): c for c in top["refused"]}
    check(top["top_bottom_signal"] == "top" and ("XLK", "long") in tref
          and tref[("XLK", "long")]["refused"].endswith("of the 2 a long needs"),
          "a Top & Bottom top signal raises the long bar to two confirmations")

    print(f"\n{LINE}\nD. THE SHORT SIDE\n{LINE}")
    xly_ref = ref.get(("XLY", "short"))
    xly = {(c["instrument"], c["direction"]): c for c in res_oh["candidates"]}.get(
        ("XLY", "short"))
    check(xly_ref and xly_ref["refused"].startswith(
        "no short in Expansion, Calm, Positive (Doctrine 4.2)")
          and ("XLY", "short") not in by,
          f"Expansion-Calm-Positive: the short is refused ({xly_ref and xly_ref['refused']})")
    check(xly and xly["met"] == 2 and xly["pivot"] == "breakout"
          and "breakdown from a base" in xly["thesis"]
          and {c["family"] for c in xly["confirmations"] if c["met"]}
          == {"relative strength", "a Weekly tell"},
          f"Overheat: accepted with two confirmations, relative strength and a "
          f"consumer tell ({xly and xly['thesis']})")
    card = cfg["regime"]["timing"]
    check(xly and xly["entry_timing"] == "Breakouts trusted; pyramiding permitted on "
          "confirmation" and xly["entry_timing_state"] == "Negative"
          and "entry timing — the regime card, Gamma Negative: “Breakouts trusted; "
          "pyramiding permitted on confirmation”" in book_b.candidate_line(1, xly),
          "negative gamma: the card's words, breakouts trusted, pyramiding on "
          "confirmation (Doctrine 5.2)")
    check(xlk and xlk["entry_timing"] == "Breakouts distrusted — wait for the retest; "
          "adds on confirmation only" and "Gamma Positive" in book_b.candidate_line(1, xlk),
          "positive gamma: breakouts distrusted, wait for the retest")
    check(card.get("Flip-zone") == "No new entries" and set(card) ==
          {"Positive", "Flip-zone", "Negative"},
          "the flip zone: no new entries; the three states, as the card has them")
    one_conf = dict(OVERHEAT)
    check(bbs.short_permitted({"macro": "Expansion", "vol": "Rising"}, cfg)[0]
          and not bbs.short_permitted({"macro": "Transition", "vol": "Calm"}, cfg)[0]
          and bbs.short_permitted({"macro": "Tightening", "vol": "Calm"}, cfg)[0],
          "shorts open in Overheat, Tightening, Contraction, or a Volatility dial at "
          "Rising or worse")
    check(bbs.multiplier({"macro": "Transition", "vol": "Rising"}, cfg)[0] == 0.375
          and xlk and xlk["size"].startswith("0.75% of capital at risk (0.75% × 1")
          and bbs.gate({**xlk, "risk": 1}, {"regime": {"vol": "Crisis"},
                                            "top_bottom": {}}, cfg)
          == "Book B is closed in a Crisis Volatility dial (the card)",
          "the size band prints the dials' multiplier (Rising 0.75 x Transition 0.5); "
          "Crisis closes Book B")
    del one_conf

    print(f"\n{LINE}\nE. SCORE AND RANK\n{LINE}")
    w = cfg["score"]["weights"]
    ok = all(abs(c["score"] - round(sum(w[k] * v for k, v in c["components"].items())
                                    / sum(w[k] for k in c["components"]), 4)) < 1e-9
             for c in res["candidates"])
    check(ok and xlk and set(xlk["components"]) == {"trend", "base", "confirmations",
                                                    "regime", "liquidity"},
          f"the score is the weighted mean of its five components "
          f"(XLK {xlk and xlk['components']} -> {xlk and xlk['score']})")
    check(xlk and xlk["components"]["regime"] == 1.0 and xlk["components"]["trend"] == 0.75
          and qqq and qqq["components"]["liquidity"] == 0.5,
          "regime alignment (Expansion, long: 1.0), the trend share (3 of 4), "
          "liquidity unread at 0.5")
    sc = [c["score"] for c in res["candidates"]]
    check(sc == sorted(sc, reverse=True) and [c["rank"] for c in res["candidates"]]
          == list(range(1, len(sc) + 1)),
          f"ranked by the score, highest first ({[(c['instrument'], c['score']) for c in res['candidates']]})")
    flow = book_b.sitting_flow(ENDING, None, res["candidates"], [], rows=[])
    subs, kept = book_b.subsections(res["candidates"], flow,
                                    {**res, "refused": res["refused"]}, top=2)
    lines = subs[0]["lines"]
    refrows = kept["reference"][0]["table"]["rows"] if kept["reference"] else []
    check(len([x for x in lines if x[:2] in ("1.", "2.")]) == 2
          and [r[0] for r in refrows] == list(range(3, len(sc) + 1))
          and kept["reference"][0]["title"] == book_b.REFERENCE_TITLE
          and len(kept["reference"][0]["table"]["columns"]) <= 6,
          f"the block prints the top N; every candidate below goes to the "
          f"reference tier, one row each ({len(refrows)} rows)")
    check(cfg["score"]["print_top"] == 10,
          "the top ten print (decision 4)")

    print(f"\n{LINE}\nF. THE LEDGER\n{LINE}")
    from altdata import probability_ledger as pl
    emitted = ENDING + "T23:30:00+00:00"
    ids = bbs.record_forecasts(res["candidates"], ENDING, emitted, db, dry_run=True)
    with pl.ProbabilityLedger(db) as led:
        rows = led.all_rows()
    check(len(ids) == len(res["candidates"]) and rows
          and {r["source"] for r in rows} == {"dryrun.book_b_candidate"},
          f"every candidate a forecast, in the dry-run namespace only ({len(ids)})")
    xr = next((r for r in rows if "XLK long" in r["claim"]), None)
    check(xr and "reaches +1R before -1R within six weeks" in xr["claim"]
          and "(b_breakout)" in xr["claim"] and xlk["candidate_id"] in xr["claim"]
          and xr["horizon_date"] == "2026-11-20" and xr["probability"] == 0.5
          and xr["resolution_criterion"].startswith("yfinance.mkt_xlk closes after "
                                                    "2026-10-09"),
          f"the claim names the setup and the candidate; six weeks; the criterion "
          f"declared at emission ({xr and xr['resolution_criterion'][:80]})")
    check(bbs.record_forecasts(res["candidates"], ENDING, emitted, db, dry_run=True)
          == ids, "a re-run of the same Weekly writes no second forecast")
    # The next week's closes: XLK rises through +1R; IWM falls through -1R.
    nxt = ["2026-10-12", "2026-10-13"]
    up = xlk["entry"] + 1.2 * xlk["risk"]
    dn = iwm["entry"] - 1.2 * iwm["risk"]
    with observations.ObservationStore(db) as st:
        st.write_many([{"registry_key": seeded["keys"][s], "instrument": None,
                        "observed_at": d, "available_at": d + "T20:20:00+00:00",
                        "value": v, "source": "yfinance"}
                       for s, v in (("XLK", up), ("IWM", dn)) for d in nxt])
    graded = bbs.grade(db, "2026-10-16", None, dry_run=True)
    out = {g["claim"].split(": ")[1].split(" from")[0]: g["outcome"] for g in graded}
    check(out.get("XLK long") == 1 and out.get("IWM long") == 0 and len(graded) == 2,
          f"resolved from stored closes: +1R first resolves 1, -1R first 0 ({out})")
    check(bbs.grade(db, "2026-10-16", None, dry_run=False) == [],
          "the live namespace is untouched by a dry run's grading")
    with pl.ProbabilityLedger(db) as led:
        led.record(source="weekly_stance", claim="SPY higher", probability=0.6,
                   horizon_date="2026-10-16", resolution_criterion="SPY",
                   emitted_at="2026-10-02T20:00:00+00:00")
        sid = [r for r in led.all_rows() if r["source"] == "weekly_stance"][0]
        led.resolve(sid["probability_id"], 1)
    from altdata import session
    calls = weekly_stack.graded_calls(session.utc_iso(), db)
    check([r["source"] for r in calls["rows"]] == ["weekly_stance"]
          and calls["candidates"] == [{"source": "dryrun.book_b_candidate", "n": 2,
                                       "hits": 1, "open": len(ids) - 2}],
          f"the graded calls keep the candidates out of the pooled rows "
          f"({calls['rows']}; {calls['candidates']})")
    ln = weekly_stack.candidates_line(calls)
    check(ln.startswith("Book B candidates (the scanner's, taken or not; never pooled "
                        "with the operator's decisions), last four weeks: none resolved;"
                        " dry runs n=2, +1R first in 1 (50%)"),
          f"the separate graded-calls line ({ln})")
    ah = weekly_stack.ahead_week({"week_ahead": {}, "week_ending": ENDING}, calls,
                                 now=ENDING + "T23:00:00+00:00")
    gsub = next(s for s in ah["subsections"] if s["title"].startswith("Graded calls"))
    check(ln in gsub["lines"] and all("book_b" not in str(r[0])
                                      for r in gsub["table"]["rows"]),
          "in Ahead, the candidates' line prints on its own beneath the table")

    print(f"\n{LINE}\nG. THE BLOCK\n{LINE}")
    # (The store now carries C's top signal: the hook is read on it, the lines
    # on the scan before it.)
    run = book_b.scanner_run(ENDING, db, cutoff=cut, regime=OVERHEAT)
    check(run is not None and run["candidates"]
          and book_b.scanner_output(ENDING, db, cutoff=cut, regime=OVERHEAT)
          == run["candidates"],
          "the hook reads the scanner by name: its whole result and its candidates")
    flow = book_b.sitting_flow(ENDING, None, res["candidates"], [], rows=[])
    subs, kept = book_b.subsections(res["candidates"], flow, res)
    blk = subs[0]
    allnotes = " ".join(blk["notes"])
    check("activates" not in allnotes and book_b.NO_SCANNER not in blk["lines"]
          and "activates when" not in Path(book_b.__file__).read_text(encoding="utf-8"),
          "the 'activates when the scanner merges' line is gone")
    check(all(set(book_b.FIELDS) == set(c) and c["decision_id"] is None
              and c["setup_id"] in ("b_breakout", "b_reclaim", "b_failed_breakdown")
              for c in kept["printed"]),
          "the printed candidates carry the ruled shape: the register's draft fields, "
          "setup, score, catalyst, id; decision_id null")
    l1 = next(x for x in blk["lines"] if " TLT long" in x)
    check("WARNING: positioning crowded the same way" in l1
          and "catalyst: Consumer Price Index (2026-10-15)" in l1
          and "parameters: N " in l1 and "counter-thesis: positioning crowded" in l1
          and "expected " in l1 and "R (the measured move" in l1,
          f"one line each, the scanner's terms beside it ({l1[:160]}...)")
    cq = next(x for x in blk["lines"] if " QQQ long" in x)
    check("against the tape: a 5-session time stop, no add" in cq,
          "the against-the-tape tag prints on the line")
    check(xlk["catalyst"] == "Consumer Price Index" and xlk["catalyst_date"] == "2026-10-15",
          "the catalyst: the week ahead's first tier-1 release where the name has "
          "no earnings of its own")
    check(any("pivot(s) refused at the gates" in n for n in blk["notes"])
          and any(n.startswith("Pivots as set:") for n in blk["notes"]),
          "the refused are counted and the parameters line is the block's note")

    group_h(cfg, res, db, cut)

    print(f"\n{LINE}\nRESULT: {PASS} passed, {FAIL} failed\n{LINE}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
