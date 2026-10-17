"""
Validation gate for 6b part 3 (brief v2 sections 2, 3, 5.6 and 8; ST-R6.45c):
what has no home in tools/validate_dealer_block.py.

SYNTHETIC FIXTURES, a temporary store and a temporary state directory: no gate
reads the live store, fetches or calls a model, and the API key is a fixture
string that must appear in no output.

  A  T3. Per horizon: the gated regime with net-to-gross, the magnitude with its
     percentile over the stored history (and its n), the nearest major level, the
     implied one-day range (spot x IV x sqrt(1/252), by hand); the table agrees
     with the windows; the matrix ends "registered hypotheses: 6, none promoted";
     T2 per horizon prints each window's levels.
  B  FIGURE 5. The scorecard chart renders from a fixture ledger: a printable
     hypothesis draws its rate, interval, base rate and baseline; one under the
     floor draws no bar.
  C  THE VENDOR WRITER. A stored fixture of the levels response (and a GEX body)
     parses into the dealer.vendor_* rows, point in time (observed on the session,
     available at capture); an absent field is absent; the daily budget refuses
     the call past it; no key configured, no call; the key is in no output.
  D  THE DIVERGENCE CHECK. GEX against dollar_gamma_per_1pct and raw DEX against
     dex_raw_notional flag past their thresholds and clear inside them; the flip
     and walls in percent of spot; VEX is never compared and carries its flag.
  E  ST-R6.45c, DEALER LEVELS IN ES. A SPY level times the same-minute ratio, by
     hand; the band is two standard deviations of the ratio's daily change; the
     row and the note; no ES price or profile says so; the 16:00 bar is found.

    python tools/validate_dealer_vendor.py
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tests" / "fixtures" / "dealer_block"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp  # noqa: E402

TD = Path(mkdtemp("validate_dealer_vendor_"))
os.environ["CHESTER_STATE_DIR"] = str(TD / "state")
FAKE_KEY = "fixture-key-0123456789abcdef"
os.environ["FLASHALPHA_API_KEY"] = FAKE_KEY
os.environ["FLASHALPHA_BASE_URL"] = "https://fixture.invalid"

import chains as C  # noqa: E402
import exposure_compute as ec  # noqa: E402

from daily_cascade import dealer_block as db  # noqa: E402
from altdata.numeral_audit import ordinal as _ord  # noqa: E402

LINE = "=" * 78
PASS = FAIL = 0
CFG = db.config()
FIX = REPO / "tests" / "fixtures" / "dealer_block"


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


def prof():
    return ec.compute_symbol(C.bs_chain(C.SETTLED), "SPY")


def group_a() -> None:
    head("A. T3, THE HORIZON MATRIX, AND T2 PER HORIZON")
    p = prof()
    hist = {"le7": [5e7 * (i + 1) for i in range(40)], "le45": [], "all": [1e8] * 10}
    m = db.t3(p, CFG, hist, (15.0, "SPY ATM 30-day IV"))
    by = {r[0]: r for r in m["table"]["rows"]}
    w7 = p["horizons"]["le7"]
    want_pct = round(100 * sum(1 for x in hist["le7"] if x <= abs(w7["dollar_gamma_per_1pct"]))
                     / 40)
    check(by["≤ 7 days"][1] == f"{db.regime(w7['net_gex'], w7['net_to_gross'], CFG)} "
                               f"({db.pct(w7['net_to_gross'])})"
          and f"{_ord(want_pct)} percentile of 40 stored" in by["≤ 7 days"][2],
          f"≤ 7 days: the gated regime and net-to-gross from the window; the magnitude at "
          f"its {_ord(want_pct)} percentile of 40 stored, by hand")
    check("no stored history yet" in by["≤ 45 days"][2] and by["0DTE"][1] == "settled, excluded",
          "no history yet says so; the settled 0DTE window is excluded")
    rng = 680.0 * 0.15 * math.sqrt(1 / 252)
    check(by["All"][4] == f"±{rng:.2f} (SPY ATM 30-day IV)",
          f"the implied one-day range: 680 x 15% x sqrt(1/252) = ±{rng:.2f}, by hand")
    name, lvl = db._nearest_level(p["horizons"]["all"], 680.0)
    check(by["All"][3].startswith(f"{name} {db.price(lvl)}"),
          f"the nearest major level ({name} {lvl})")
    check(m["lines"][-1] == "Registered hypotheses: 6, none promoted."
          and m["tail"] == "registered hypotheses: 6, none promoted"
          and len(m["table"]["columns"]) == 5 and "inferred, not observed" in m["table"]["columns"][0],
          "the matrix ends on 'registered hypotheses: 6, none promoted'; no synthesis "
          "sentence; five columns, stamped")
    t2h = {r[0]: r for r in db.t2_by_horizon(p, CFG)["rows"]}
    check(t2h["All"][1].startswith(db.price(p["horizons"]["all"]["call_wall_otm"]))
          and t2h["0DTE"][1] == "settled, excluded",
          "T2 per horizon: each window's OTM walls, zero-gamma and peak strike")
    rows = db.window_rows(p, "2026-10-16T21:00:00+00:00")
    check({r["instrument"] for r in rows} == {"SPY:le7", "SPY:le45", "SPY:all"}
          and all(r["registry_key"] == "dealer.window_gamma" and r["observed_at"] == "2026-10-16"
                  for r in rows),
          "each live window's $/1% is stored for the percentile history")


def group_b() -> None:
    head("B. FIGURE 5, FROM A FIXTURE LEDGER")
    from altdata import dealer_scorecard as dsc  # noqa: PLC0415
    from daily_cascade import charts as ch  # noqa: PLC0415
    rates = [dict(hypothesis="dampened", label="H1 dampened", k=14, n=24, printable=True,
                  interval=dsc.wilson(14, 24), base_rate=0.4, baseline=0.45),
             dict(hypothesis="pinned", label="H4 pinned", k=1, n=2, printable=False,
                  interval=None, base_rate=None, baseline=None)]
    c = ch.dealer_chart("M12", prof(), "x", str(TD), rates=rates)
    f5 = c["drawn"]["figure_5"]["rates"]
    check(not c.get("unavailable") and c["figures"] == [2, 1, 3, 4, 5]
          and abs(f5[0]["rate"] - 14 / 24) < 1e-9 and f5[0]["interval"] == dsc.wilson(14, 24)
          and f5[1]["rate"] is None,
          "M12 draws figure 5: H1's 14/24 with its Wilson interval, base rate and "
          "baseline; H4 under the floor draws no bar")
    w = ch.dealer_chart("W12", prof(), "y", None, rates=rates)
    check(w["figures"] == [2, 1, 3, 5] and w["png_bytes"] <= ch.MAX_PNG_BYTES,
          "W12 carries figure 5 inside its one slot, under the 150 KB cap")


def group_c() -> None:
    head("C. THE VENDOR WRITER")
    from altdata import observations  # noqa: PLC0415
    from altdata.sources import flashalpha as fa  # noqa: PLC0415
    levels = json.loads((FIX / "flashalpha_levels.json").read_text(encoding="utf-8"))
    gex = json.loads((FIX / "flashalpha_gex.json").read_text(encoding="utf-8"))
    f = fa.parse(levels, gex)
    check(f["flip"] == 674.5 and f["call_wall"] == 690.0 and f["put_wall"] == 670.0
          and f["spot"] == 680.2 and f["gex"] == 4.1e8 and f["dex"] == 1.85e10
          and f["vex"] == -1.2e9,
          "the stored fixtures parse: their flip, walls, spot, GEX per 1%, raw DEX, VEX")
    f2 = fa.parse(levels, {})
    check(f2["gex"] is None and f2["dex"] is None and f2["flip"] == 674.5,
          "a GEX body that carries nothing: those fields absent, never guessed")
    rows = fa.rows_from("SPY", f, "2026-10-16", "2026-10-16T20:25:07+00:00")
    check(len(rows) == 7 and all(r["observed_at"] == "2026-10-16"
                                 and r["available_at"] == "2026-10-16T20:25:07+00:00"
                                 and r["instrument"] == "SPY" for r in rows)
          and {r["registry_key"] for r in rows} == set(fa.KEYS.values()),
          "seven dealer.vendor_* rows, observed on the session, available at capture")
    calls = []

    def fake_get(url, key):
        calls.append((url, key == FAKE_KEY))
        return {"status": 200, "body": levels if "levels" in url else gex}
    db_path = str(TD / "vendor.db")
    cfg = fa.config()
    with observations.ObservationStore(db_path) as st:
        out = fa.pull(db=st, get=fake_get, cfg=cfg, day="2026-10-16",
                      quota_path=TD / "q.json")
        from altdata import session as _s  # noqa: PLC0415
        stored = fa.stored(st, _s.utc_iso(), "SPY")
    check(out["status"] == "OK" and out["calls"] == 8 and out["written"] == 28
          and all(k for _, k in calls) and stored["gex"] == 4.1e8,
          "a run: two calls a symbol for SPY, QQQ, IWM and MSTR, 28 rows, read back")
    tight = dict(cfg, daily_call_budget=3)
    with observations.ObservationStore(str(TD / "v2.db")) as st:
        out2 = fa.pull(db=st, get=fake_get, cfg=tight, day="2026-10-16",
                       quota_path=TD / "q2.json")
    check(out2["status"] == "BUDGET" and out2["calls"] == 3
          and "daily budget of 3 calls is spent" in str(out2["symbols"]),
          "the daily budget refuses the call past it, and says so")
    text = json.dumps([out, out2], default=str)
    check(FAKE_KEY not in text and out["key_configured"] is True,
          "the key appears in no output; the summary says only that one is configured")

    def boom(url, key):
        raise RuntimeError(f"connection refused for {url}?apikey={key}")
    with observations.ObservationStore(str(TD / "v3.db")) as st:
        out3 = fa.pull(db=st, get=boom, cfg=cfg, day="2026-10-16", quota_path=TD / "q3.json")
    check(FAKE_KEY not in json.dumps(out3, default=str) and out3["written"] == 0,
          "an error carrying the key is redacted before it reaches the summary")
    saved = os.environ.pop("FLASHALPHA_API_KEY")
    try:
        none = fa.pull(db=None, get=fake_get, cfg=cfg, day="2026-10-16",
                       quota_path=TD / "q4.json")
    finally:
        os.environ["FLASHALPHA_API_KEY"] = saved
    check(none["status"] == "SKIPPED" and none["key_configured"] is False,
          "no key configured: no call, and it says so")


def group_d() -> None:
    head("D. THE DIVERGENCE CHECK")
    from altdata.sources import flashalpha as fa  # noqa: PLC0415
    p = prof()
    o = p["overall"]
    ours_g, ours_d = o["dollar_gamma_per_1pct"], o["dex_raw_notional"]
    near = {"gex": ours_g * 1.3, "dex": ours_d * 1.10, "flip": o["gamma_flip"] * 1.005,
            "call_wall": o["call_wall_otm"], "put_wall": o["put_wall_otm"], "vex": -1e9,
            "day": "2026-10-16"}
    far = dict(near, gex=ours_g * 2.2, dex=ours_d * 1.25, flip=o["gamma_flip"] * 1.02)
    cn, cf = ({r["name"]: r for r in fa.compare(v, p)} for v in (near, far))
    check(cn["GEX ($/1%)"]["flag"] is False and cf["GEX ($/1%)"]["flag"] is True
          and abs(cf["GEX ($/1%)"]["gap"] - (1.2 / 2.2)) < 1e-9,
          "GEX against dollar_gamma_per_1pct: 30% apart clears the 0.50 threshold; "
          "2.2x flags (gap 1.2/2.2)")
    check(cn["DEX, raw-signed ($)"]["flag"] is False and cf["DEX, raw-signed ($)"]["flag"] is True,
          "raw DEX against dex_raw_notional: 10% clears 0.15; 25% flags")
    check(cn["Zero-gamma level"]["flag"] is False and cf["Zero-gamma level"]["flag"] is True,
          "the flip in percent of spot: 0.5% clears the 1.0 threshold; 2% flags")
    check(cn["VEX"]["flag"] is None and "unreconciled" in cn["VEX"]["note"],
          "VEX is never compared and carries its flag")
    line = fa.vendor_line(far, p)
    check(any("past the 0.5 threshold" in x for x in line) and line[0].startswith("FlashAlpha")
          and "never a correction" in line[0],
          "the Weekly's vendor line reads the stored series and says a gap is a question")
    check(fa.vendor_line({}, p)[0].startswith("FlashAlpha: no stored vendor reading"),
          "no stored reading: the line says so")


def group_e() -> None:
    head("E. ST-R6.45c: DEALER LEVELS IN ES")
    from altdata import dealer_es as de  # noqa: PLC0415
    p = prof()
    hist = [10.02 * (1 + 0.0005 * math.sin(i)) for i in range(21)]
    conv = de.convert(p, 6853.4, hist, "ESZ6")
    r = 6853.4 / p["spot"]
    flip = p["overall"]["gamma_flip"]
    ch = [b / a - 1 for a, b in zip(hist, hist[1:])][-20:]
    m = sum(ch) / len(ch)
    band = 2 * math.sqrt(sum((c - m) ** 2 for c in ch) / (len(ch) - 1))
    check(abs(conv["ratio"] - r) < 1e-12 and abs(conv["levels"]["gamma_flip"]["es"] - flip * r) < 1e-9
          and abs(conv["band"] - band) < 1e-12,
          f"the flip {flip:.2f} x the ratio {r:.4f} = {flip * r:,.2f} in ES, by hand; "
          f"the band ±{band * 100:.3f}% (two sigma of the ratio's daily change)")
    check(conv["row"].startswith("Dealer levels in ES (ESZ6): zero-gamma")
          and "Inferred, not observed." in conv["row"]
          and "OTM call wall" in conv["row"] and "(±" in conv["row"]
          and conv["note"].startswith("ES conversion: each SPY level times one same-minute ratio"),
          "the row names the contract and each level with its band; the note gives the "
          "method and the band once")
    check(de.convert(p, None, hist)["row"].startswith("dealer levels in ES: no same-minute"),
          "no ES price: the row says so")
    bars = [{"observed_at": "2026-10-16T19:50:00+00:00", "close": 6850.0},
            {"observed_at": "2026-10-16T19:55:00+00:00", "close": 6853.4}]
    check(de.es_at(bars, "2026-10-16") == 6853.4,
          "the 5-minute bar ending at 16:00 ET is the conversion's ES price")
    short = de.convert(p, 6853.4, hist[:4])
    check(short["band"] is None and "not yet computable" in short["note"],
          "under five ratio changes stored, the band says it is not yet computable")


def main() -> int:
    print(f"{LINE}\n6b PART 3: T3, FIGURE 5, THE VENDOR WRITER, THE ES CONVERSION\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback                                    # noqa: PLC0415
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
