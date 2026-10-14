"""
Validation gate for the horizon bars, the family frames, the returns quilt and the
roll-yield row (AQ-4; change order "Alternative Assets Quarterly", 10 Oct 2026,
section 7).

SEEDED, never sampled: every store here is a throwaway written by this gate with
prices whose returns are known by construction, and every chart renders headless
(Agg) into a throwaway directory. Nothing here opens the live store or the
network.

  A  SHAPES. Every universe asset has a family and a return kind; one fixed hue
     per family, none repeated; the quilt's ten classes, each its own hue; the
     universe is read from config/correlation.yaml when that file exists (VIX
     skipped, an asset without a family refused) and from the own copy when it
     does not; DBC is in the price feed for the quilt's commodities.
  B  THE ARITHMETIC. Total return reinvests a dividend at the ex-date's close; the
     cash index compounds DTB3 at its bond-equivalent yield; a series growing at
     a known rate annualises to that rate; an inverted quote reads as its own
     price.
  C  "SINCE INCEPTION". A series younger than the horizon prints since its first
     stored close, annualised over its own life, and is flagged and hatched;
     under a year it is cumulative and says so; a first close inside the grace
     days counts as covering the horizon; a gap at the start is no bar at all.
  D  THE RANKING. Each horizon's bars are drawn in descending order, every bar in
     its family's hue.
  E  THE QUILT. Fifteen year columns, the last the current year's YTD and headed
     so; each column ranked; a class not stored for a whole year is left out of
     that column, never zero.
  F  THE JSON IS WHAT WAS DRAWN. Every bar's JSON value is the width read back
     off the drawn artist and equals the computed figure; each carries asset,
     horizon, start date and return kind; an absent asset is listed as not drawn
     with its reason; the quilt's cells are the drawn labels.
  G  AS-OF. A row dated after the as-of, or knowable only after its cutoff, moves
     no figure; every figure carries the as-of and the cutoff.
  H  NO FETCH. The tool imports nothing that fetches and names none of the
     feeds' fetch functions in its code (strings and comments aside).
  I  THE ROLL-YIELD HOOK. With no curve stored every row prints "not tracked —
     the curve arrives with 6b"; with a seeded front and second the row is
     ln(front/second) x 365 / days, signed by the curve.
  J  THE CLI. `--as-of --out --db` writes the three bar charts, the frames, the
     quilt, the two tables and the JSON.

    python tools/validate_horizon_charts.py
"""

from __future__ import annotations

import ast
import copy
import datetime as dt
import io
import json
import math
import sys
import tokenize
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import yaml  # noqa: E402

from altdata import observations  # noqa: E402
from altdata.sources import yfinance_source as yf_src  # noqa: E402
from gate_tmp import mkdtemp as gate_mkdtemp  # noqa: E402
import horizon_charts as H  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78
TD = Path(gate_mkdtemp("horizon_gate_"))
AS_OF = "2026-09-30"
# The keys AQ-5's universe gives the six assets that join the price feed there.
AQ5_KEYS = {"agri": "yfinance.mkt_dba", "eth": "yfinance.mkt_eth_usd",
            "sol": "yfinance.mkt_sol_usd", "zec": "yfinance.mkt_zec_usd",
            "intl_re": "yfinance.mkt_vnqi", "china": "yfinance.mkt_mchi"}


def ok(m: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    (ok if c else bad)(m)


def near(a, b, tol=1e-9) -> bool:
    return a is not None and b is not None and abs(a - b) <= tol


# ---------------------------------------------------------------------------
# A seeded store
# ---------------------------------------------------------------------------
def days(start: str, end: str, weekdays: bool = True):
    d, e = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    while d <= e:
        if not weekdays or d.weekday() < 5:
            yield d
        d += dt.timedelta(days=1)


def rows_for(key: str, start: str, end: str, f, weekdays: bool = True,
             avail_lag_days: int = 0) -> list[dict]:
    t0 = dt.date.fromisoformat(start)
    return [{"registry_key": key, "instrument": None, "observed_at": d.isoformat(),
             "available_at": f"{(d + dt.timedelta(days=avail_lag_days)).isoformat()}T20:20:00Z",
             "value": f((d - t0).days), "source": "gate",
             "availability_kind": "reconstructed"}
            for d in days(start, end, weekdays)]


def growth(rate: float, p0: float = 100.0):
    return lambda n: p0 * (1.0 + rate) ** (n / 365.25)


def seeded_store(name: str) -> observations.ObservationStore:
    """Twenty-six years of the deep funds, a young one, a very young coin, a
    currency to invert, a 3-month bill, and nothing for the rest."""
    st = observations.ObservationStore(str(TD / f"{name}.db"))
    rows = []
    rows += rows_for("yfinance.mkt_spy", "2000-01-03", AS_OF, growth(0.10))
    rows += rows_for("yfinance.mkt_tlt", "2002-07-30", AS_OF, growth(0.03))
    rows += rows_for("yfinance.mkt_gld", "2004-11-18", AS_OF, growth(0.08))
    rows += rows_for("yfinance.mkt_eem", "2003-04-14", AS_OF, growth(0.05))
    rows += rows_for("yfinance.mkt_efa", "2001-08-27", AS_OF, growth(0.06))
    rows += rows_for("yfinance.mkt_dbc", "2006-02-06", AS_OF, growth(0.01))
    rows += rows_for("yfinance.mkt_dxy", "2000-01-03", AS_OF, growth(-0.01))
    rows += rows_for("yfinance.mkt_xlre", "2015-10-08", AS_OF, growth(0.04))      # young
    rows += rows_for("yfinance.mkt_btc_usd", "2014-09-17", AS_OF, growth(0.60), weekdays=False)
    rows += rows_for("yfinance.mkt_sol_usd", "2026-03-02", AS_OF, growth(1.00), weekdays=False)  # < 1 year
    rows += rows_for("yfinance.mkt_usdjpy", "2000-01-03", AS_OF, growth(0.02))   # inverted
    rows += rows_for("yfinance.mkt_slv", "2006-04-28", AS_OF, growth(0.07))
    rows += rows_for("fred.tbill_3m", "2010-01-04", AS_OF, lambda n: 2.0)
    st.write_many(rows)
    return st


# ---------------------------------------------------------------------------
def group_a(cfg: dict) -> None:
    print(f"\n{LINE}\nA. SHAPES\n{LINE}")
    own_ids = [u["id"] for u in cfg["universe"]]
    check(all(i in cfg["assets"] for i in own_ids),
          f"every one of the own copy's {len(own_ids)} universe assets has a family row")
    check({"spy", "tlt"} <= set(own_ids), "SPY and TLT are in the set")
    hues = [f["hue"] for f in cfg["families"].values()]
    check(len(hues) == len(set(hues)), f"one fixed hue per family, none repeated ({len(hues)} families)")
    frames = [k for k, f in cfg["families"].items() if f.get("frame")]
    want = {"metals", "energy", "currency", "em_china", "crypto", "real_estate", "credit",
            "international", "agriculture"}
    check(set(frames) == want, f"a long frame for each of the nine families ({sorted(frames)})")
    q = cfg["quilt"]["classes"]
    check(len(q) == 10 and len({c["hue"] for c in q}) == 10,
          "the quilt's ten classes, each its own hue")
    check([c["id"] for c in q] == ["us_eq", "dm_eq", "em_eq", "lt_tsy", "gold", "cmdty",
                                   "reits", "btc", "dollar", "cash"],
          "the classes are the order's: SPY, EFA, EEM, TLT, GLD, commodities, XLRE, Bitcoin, DXY, cash")
    check(yf_src.SYMBOLS.get("DBC") == "mkt_dbc" and
          any(c["key"] == "yfinance.mkt_dbc" for c in q),
          "DBC is in the price feed and is the quilt's broad commodities")
    for a in cfg["assets"].values():
        if a.get("key"):
            sym = a["key"].split(".", 1)[1]
            check(sym in yf_src.SYMBOLS.values(), f"added asset key {a['key']} is a price-feed series")

    # The universe source.
    cfg = {**cfg, "universe_file": "config/correlation.yaml"}
    fake = TD / "repo_with"
    (fake / "config").mkdir(parents=True, exist_ok=True)
    uni = [dict(u) for u in cfg["universe"]] + [{"id": "vix", "label": "VIX", "key": "fred.vix"}]
    uni[0]["label"] = "Gold from AQ-5"
    (fake / "config" / "correlation.yaml").write_text(yaml.safe_dump({"universe": uni}), encoding="utf-8")
    assets, origin = H.universe(cfg, fake)
    check(origin == "config/correlation.yaml" and "vix" not in {a["id"] for a in assets},
          f"with config/correlation.yaml present the universe is read from it, VIX skipped ({origin})")
    (fake / "config" / "correlation.yaml").write_text(
        yaml.safe_dump({"universe": uni + [{"id": "platinum", "key": "yfinance.mkt_pplt"}]}),
        encoding="utf-8")
    try:
        H.universe(cfg, fake)
        bad("a universe asset with no family row is refused")
    except ValueError as exc:
        ok(f"a universe asset with no family row is refused ({exc})")
    bare = TD / "repo_without"
    bare.mkdir(exist_ok=True)
    assets, origin = H.universe(cfg, bare)
    check("own copy" in origin and len([a for a in assets if a["id"] in own_ids]) == len(own_ids),
          f"without it, the own copy ({origin})")
    absent = [a["id"] for a in assets if a.get("absent")]
    check({"prl", "uranium", "light_tier"} <= set(absent),
          f"PRL, uranium and the light tier are carried as absent, with reasons ({absent})")


def group_b() -> None:
    print(f"\n{LINE}\nB. THE ARITHMETIC\n{LINE}")
    closes = [("2026-01-02", 100.0), ("2026-01-05", 100.0), ("2026-01-06", 98.0), ("2026-01-07", 99.0)]
    tri = H.total_return_index(closes, [("2026-01-06", 2.0)])
    check(near(tri[-1][1], 100.0 * (100.0 / 100.0) * ((98.0 + 2.0) / 100.0) * (99.0 / 98.0)),
          f"a $2 dividend is reinvested at its ex-date's close (index {tri[-1][1]:.6f})")
    tri2 = H.total_return_index(closes, [("2026-01-03", 1.0)])
    check(near(tri2[1][1], 101.0), "a dividend dated between two closes is paid at the next close")
    cash = H.cash_index([("2026-01-01", 4.0), ("2026-01-31", 4.0)])
    d = 0.04
    bey = 365 * d / (360 - 91 * d)
    check(near(cash[-1][1], 100.0 * (1 + bey * 30 / 365)),
          f"cash compounds DTB3 at its bond-equivalent yield ({bey:.5f} for a 4% discount)")
    pts = [(x.isoformat(), growth(0.10)((x - dt.date(2000, 1, 3)).days))
           for x in days("2000-01-03", AS_OF)]
    f = H.horizon_figure(pts, AS_OF, 20, True, 7, 10)
    check(near(f["value"], 0.10, 1e-6) and not f["since_inception"],
          f"a series growing 10% a year annualises to {100 * f['value']:.4f}% over 20 years")
    f1 = H.horizon_figure(pts, AS_OF, 1, False, 7, 10)
    check(near(f1["value"], 1.10 ** (f1["span_days"] / 365.25) - 1, 1e-9) and not f1["annualised"],
          "the one-year figure is the year's return, not annualised")


def group_c(st, cfg) -> dict:
    print(f"\n{LINE}\nC. \"SINCE INCEPTION\"\n{LINE}")
    res = H.compute(st, cfg, AS_OF)
    by = {a["asset"]: a for a in res["assets"]}
    xl = by["us_re"]
    check(xl["20y"]["since_inception"] and xl["20y"]["start"] == "2015-10-08"
          and xl["20y"]["annualised"] and near(xl["20y"]["value"], 0.04, 1e-6),
          f"XLRE (first stored 2015-10-08) prints since 2015-10-08 at 20 years, annualised over "
          f"its own life ({100 * xl['20y']['value']:.3f}%/yr)")
    check(not xl["5y"]["since_inception"], "and covers the 5-year horizon in full")
    sol = by["sol"]
    check(all(sol[h]["since_inception"] and not sol[h]["annualised"] for h in ("20y", "5y", "1y"))
          and sol["1y"]["start"] == "2026-03-02",
          "Solana stored for under a year is cumulative since 2026-03-02 at every horizon, not annualised")
    check(not by["spy"]["20y"]["since_inception"] and not by["gold"]["20y"]["since_inception"],
          "SPY and GLD, stored past 20 years, are full-horizon bars")
    gld_start = by["gold"]["20y"]["start"]
    check(gld_start <= "2006-09-30", f"GLD's 20-year start is the last close on or before 2006-09-30 ({gld_start})")
    # Grace: a first close three days after the horizon's start covers it.
    pts = [(x.isoformat(), 100.0 + i) for i, x in enumerate(days("2021-10-03", AS_OF))]
    g = H.horizon_figure(pts, AS_OF, 5, True, 7, 10)
    check(not g["since_inception"] and g["start"] == pts[0][0],
          f"a first close {pts[0][0]} inside the grace days covers the 5-year horizon")
    # A gap at the start is no bar.
    gap = [("2001-01-02", 100.0)] + [(x.isoformat(), 100.0) for x in days("2010-01-04", AS_OF)]
    gg = H.horizon_figure(gap, AS_OF, 20, True, 7, 10)
    check(gg["value"] is None and "gap" in gg["reason"],
          f"a gap in the stored history at the start draws nothing ({gg['reason']})")
    jpy = by["jpy"]
    check(near(jpy["20y"]["value"], 1 / 1.02 - 1, 1e-6),
          f"USD/JPY rising 2% a year reads as the yen falling ({100 * jpy['20y']['value']:.3f}%/yr)")
    check(by["oil"]["20y"]["value"] is None and by["oil"]["20y"]["reason"] == "no stored history",
          "an asset with no stored rows is no bar, with its reason")
    return res


def group_d_f(st, cfg) -> dict:
    print(f"\n{LINE}\nD/F. THE RANKING, AND THE JSON IS WHAT WAS DRAWN\n{LINE}")
    out = TD / "out_d"
    doc = H.run(st, AS_OF, out, cfg)
    res = H.compute(st, cfg, AS_OF)
    by = {a["asset"]: a for a in res["assets"]}
    for h in ("20y", "5y", "1y"):
        bars = [b for b in doc["bars"] if b["horizon"] == h]
        vals = [b["value"] for b in bars]
        check(len(bars) > 5 and vals == sorted(vals, reverse=True),
              f"{h}: {len(bars)} bars, ranked descending")
        check(all(near(b["value"], by[b["asset"]][h]["value"]) for b in bars),
              f"{h}: every JSON value equals the computed figure")
        check(all(b.get("start") and b.get("return_kind") in ("total", "price") and b.get("horizon") == h
                  for b in bars), f"{h}: each bar carries its start date and return kind")
        nd = {x["asset"]: x["why"] for x in doc["not_drawn"][h]}
        check("prl" in nd and "no feed" in nd["prl"] and nd.get("oil") == "no stored history",
              f"{h}: absent and unstored assets are listed as not drawn, with reasons")
    # Read the artists directly, independent of run().
    path, drawn = H.draw_bars(res, cfg, "20y", TD)
    jv = {b["asset"]: b["value"] for b in doc["bars"] if b["horizon"] == "20y"}
    check(path.exists() and all(near(d["drawn_value"], jv[d["asset"]]) for d in drawn)
          and len(drawn) == len(jv), "the drawn bar widths match the JSON one for one")
    spy = next(b for b in doc["bars"] if b["asset"] == "spy" and b["horizon"] == "20y")
    check(spy["return_kind"] == "total" and spy["printed"] == H.pct(spy["value"], True),
          f"SPY is total return and the JSON carries the printed label ({spy['printed']})")
    btc = next(b for b in doc["bars"] if b["asset"] == "btc" and b["horizon"] == "5y")
    check(btc["return_kind"] == "price", "Bitcoin is price return")
    xl = next(b for b in doc["bars"] if b["asset"] == "us_re" and b["horizon"] == "20y")
    check(xl["since_inception"] and xl["start"] == "2015-10-08",
          "the JSON says XLRE's 20-year bar is since 2015-10-08 -- the first stored date, honestly")
    names = sorted(p.name for p in out.iterdir())
    check({"bars_20y.png", "bars_5y.png", "bars_1y.png", "quilt.png", "horizon_charts.json",
           "horizon_table.md", "roll_yield.md"} <= set(names),
          f"the charts, the tables and the JSON are written ({len(names)} files)")
    check("frame_metals.png" in names and "frame_agriculture.png" not in names
          and doc["frames"]["agriculture"].get("unavailable"),
          "a family with stored members gets its frame; one with none says why instead")
    m = doc["frames"]["metals"]
    check({x["asset"] for x in m["members"]} == {"gold", "silver"} and
          any(x["asset"] == "copper" for x in m["missing"]),
          "the metals frame draws gold and silver and names copper as not stored")
    return doc


def group_e(doc: dict) -> None:
    print(f"\n{LINE}\nE. THE QUILT\n{LINE}")
    q = doc["quilt"]
    check(q["years"] == list(range(2012, 2027)) and q["ytd_year"] == 2026,
          f"fifteen year columns, {q['years'][0]}-{q['years'][-1]}, the last the YTD year")
    for y in (2013, 2020, 2026):
        col = [c for c in q["cells"] if c["year"] == y]
        vals = [c["value"] for c in col]
        check(vals == sorted(vals, reverse=True) and [c["rank"] for c in col] == list(range(1, len(col) + 1)),
              f"{y}: ranked, {len(col)} classes")
    y14 = {c["class"] for c in q["cells"] if c["year"] == 2014}
    y15 = {c["class"] for c in q["cells"] if c["year"] == 2015}
    check("btc" not in y14 and "btc" in y15,
          "Bitcoin (first stored 2014-09-17) is left out of 2014 and in from 2015")
    check("reits" not in y15 and "reits" in {c["class"] for c in q["cells"] if c["year"] == 2016},
          "XLRE (first stored 2015-10-08) is left out of 2015, never zero")
    spy13 = next(c for c in q["cells"] if c["year"] == 2013 and c["class"] == "us_eq")
    check(near(spy13["value"], 0.10, 0.002), f"SPY's 2013 cell reads its seeded ~10% ({100 * spy13['value']:.2f}%)")
    cash = next(c for c in q["cells"] if c["year"] == 2015 and c["class"] == "cash")
    check(0.019 < cash["value"] < 0.021, f"cash at a 2% bill compounds to ~2% a year ({100 * cash['value']:.3f}%)")
    check(all(abs(c["drawn_value"] - round(c["value"] * 1000) / 1000) < 1e-9 for c in q["cells"]),
          "every quilt cell's drawn label is its value to 0.1%")
    src = Path(H.__file__).read_text(encoding="utf-8")
    check('f"{y}\\nYTD"' in src, "the current year's column head says YTD")


def group_g(cfg) -> None:
    print(f"\n{LINE}\nG. AS-OF\n{LINE}")
    st = seeded_store("asof")
    before = H.compute(st, cfg, AS_OF)
    st.write_many(rows_for("yfinance.mkt_spy", "2026-10-01", "2026-10-09", lambda n: 1e6))
    st.write_many([{"registry_key": "yfinance.mkt_spy", "instrument": None,
                    "observed_at": AS_OF, "available_at": "2026-10-05T12:00:00Z",
                    "value": 1.0, "source": "gate", "availability_kind": "observed"}])
    after = H.compute(st, cfg, AS_OF)
    b = {a["asset"]: a for a in before["assets"]}["spy"]
    a = {a["asset"]: a for a in after["assets"]}["spy"]
    check(all(near(b[h]["value"], a[h]["value"]) for h in ("20y", "5y", "1y")) and
          near(b["ytd"]["value"], a["ytd"]["value"]),
          "closes after the as-of, and a revision knowable only after the cutoff, move nothing")
    check(after["cutoff"] == "2026-10-01T06:00:00Z", f"the cutoff is the morning after the as-of ({after['cutoff']})")
    late = H.compute(st, cfg, "2026-10-09")
    s = {a["asset"]: a for a in late["assets"]}["spy"]
    check(s["1y"]["end"] == "2026-10-09", "a later as-of reads the later closes")
    st.close()


def group_h() -> None:
    print(f"\n{LINE}\nH. NO FETCH\n{LINE}")
    src = Path(H.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods |= {n.name for n in node.names}
        elif isinstance(node, ast.ImportFrom):
            mods.add(("." * node.level) + (node.module or ""))
            mods |= {f"{node.module}.{n.name}" for n in node.names if node.module}
    banned_mods = ("altdata.sources", "yfinance", "requests", "urllib", "http", "socket",
                   "fredapi", "altdata.feeds")
    hit = sorted(m for m in mods if any(m == b or m.startswith(b + ".") for b in banned_mods))
    check(not hit, f"imports nothing that fetches (imports: {sorted(mods)})")
    code = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type not in (tokenize.STRING, tokenize.COMMENT):
            code.append(tok.string)
    names = set(code)
    fetchers = {"_fetch_symbol", "_fetch_series", "pull", "pull_prices", "pull_fred", "backfill",
                "http_get_json", "http_get_response", "import_yfinance", "history", "download",
                "Ticker", "urlopen", "run_feeds", "fetch"}
    found = sorted(names & fetchers)
    check(not found, f"names none of the feeds' fetch functions in code ({found or 'none'})")
    check(any(t == "as_of" for t in code), "reads the store through its as-of join")


def group_i(cfg) -> None:
    print(f"\n{LINE}\nI. THE ROLL-YIELD HOOK\n{LINE}")
    st = seeded_store("roll")
    rows = H.roll_yield(st, cfg, AS_OF, H.cutoff_for(AS_OF))
    check(len(rows) == 6 and all(r["value"] is None and r["state"] == "not tracked — the curve arrives with 6b"
                                 for r in rows),
          "with no curve stored, every row prints the hook's line (6 commodities)")
    check(H.CURVE_HOOK == "6b" and cfg["roll_yield"]["hook"] == "6b", "the hook is named: 6b")
    st.write_many(rows_for("curve.wti.m1", "2026-09-01", AS_OF, lambda n: 70.0)
                  + rows_for("curve.wti.m2", "2026-09-01", AS_OF, lambda n: 69.0)
                  + rows_for("curve.wti.m1_m2_days", "2026-09-01", AS_OF, lambda n: 31.0)
                  + rows_for("curve.natgas.m1", "2026-09-01", AS_OF, lambda n: 3.0)
                  + rows_for("curve.natgas.m2", "2026-09-01", AS_OF, lambda n: 3.3))
    rows = {r["id"]: r for r in H.roll_yield(st, cfg, AS_OF, H.cutoff_for(AS_OF))}
    w, g = rows["wti"], rows["natgas"]
    check(near(w["value"], math.log(70 / 69) * 365 / 31) and w["state"] == "backwardation"
          and w["days_from"] == "stored",
          f"WTI 70 over 69, 31 days apart: {100 * w['value']:+.2f}% a year, backwardation")
    check(near(g["value"], math.log(3.0 / 3.3) * 365 / (365 / 12)) and g["state"] == "contango"
          and g["days_from"] == "declared spacing",
          f"natural gas 3.0 under 3.3 at the declared month: {100 * g['value']:+.1f}% a year, contango")
    check(rows["copper"]["value"] is None, "copper, still unstored, keeps the hook's line")
    md = H.roll_table(H.compute(st, cfg, AS_OF))
    check("not tracked — the curve arrives with 6b" in md and "backwardation" in md,
          "the rendered row carries both")
    st.close()


def group_j() -> None:
    print(f"\n{LINE}\nJ. THE CLI\n{LINE}")
    st = seeded_store("cli")
    db = st.path
    st.close()
    out = TD / "cli_out"
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        rc = H.main(["--as-of", AS_OF, "--out", str(out), "--db", str(db)])
    finally:
        sys.stdout = old
    doc = json.loads((out / "horizon_charts.json").read_text(encoding="utf-8"))
    check(rc == 0 and doc["as_of"] == AS_OF and doc["cutoff"].startswith("2026-10-01"),
          "the CLI writes a JSON stamped with its as-of and cutoff")
    check(all((out / n).exists() for n in ("bars_20y.png", "bars_5y.png", "bars_1y.png", "quilt.png")),
          "and the three bar charts and the quilt")
    check("print 'since' their first stored close" in buf.getvalue(),
          "and says which figures print since their first stored close")


def main() -> int:
    print(f"{LINE}\nHORIZON BARS, FAMILY FRAMES, QUILT, ROLL YIELD (AQ-4)\n{LINE}")
    cfg = H.load_config()
    # The gate runs on the own copy of the universe whether or not AQ-5's file is
    # on this checkout, so its verdict does not depend on which branch merged first.
    cfg = copy.deepcopy(cfg)
    cfg["universe_file"] = "config/__no_correlation_file_in_the_gate__.yaml"
    pending = [u["id"] for u in cfg["universe"] if u.get("absent")]
    print(f"\n{LINE}\n0. THE OWN COPY ON MAIN\n{LINE}")
    check(sorted(pending) == sorted(AQ5_KEYS) and
          not any(u.get("key") for u in cfg["universe"] if u["id"] in AQ5_KEYS),
          f"AQ-5's six are absent in the own copy, naming no unregistered key ({sorted(pending)})")
    # Seed them as AQ-5's universe will key them, so the arithmetic below covers
    # a coin and the young series either way.
    for u in cfg["universe"]:
        if u["id"] in AQ5_KEYS:
            u.pop("absent", None)
            u["key"] = AQ5_KEYS[u["id"]]
    group_a(cfg)
    group_b()
    st = seeded_store("main")
    group_c(st, cfg)
    doc = group_d_f(st, cfg)
    group_e(doc)
    st.close()
    group_g(cfg)
    group_h()
    group_i(cfg)
    group_j()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
