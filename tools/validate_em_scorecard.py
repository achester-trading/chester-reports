"""
Validation gate for the EM vulnerability scorecard (AQ-9a, 11 Oct 2026).

FIXTURES FROM EACH API'S ACTUAL RESPONSE, trimmed to Brazil and China
(tools/fixtures/em/): the IMF's SDMX-JSON 2.0 for WEO (the current edition and
the October 2025 vintage), IL, ITG and CPI; the BIS WS_CBPOL CSV; the World
Bank v2 JSON for QEDS. Every store is a throwaway; nothing here opens the live
store or the network (the writers' HTTP function is replaced by the fixtures).

  A  SHAPES. Thirteen countries, each with a target or a stated none and its
     source; each writer's country list mirrors the config; every (country,
     lens) is sourced or declared not_yet_sourced with a candidate; every key
     registered with the four fields, trigger_eligible false; five sources live.
  B  PARSERS on the real shapes: publication instants, the projections dropped,
     values in their stored units, dimension and column checks that raise.
  C  WEO VINTAGES AND AS-OF. Two editions stored as two vintages at their own
     instants, never an overwrite; an as-of read before April 2026 sees
     October 2025's numbers; an unchanged value is one vintage.
  D  IDEMPOTENCE. A second pull of every writer writes nothing.
  E  STALE, NOT EMPTY. An outage and an empty response write nothing.
  F  THE LENSES. Each lens's arithmetic; available_at is the latest input's; a
     month missing an input has no row.
  G  THE SCORECARD. Ranked per column; a missing lens renders "not tracked",
     never a blank; nothing sums the lenses; the Quarterly block's shape; the
     Monthly line names three deteriorations with their data-as-of, and says so
     when there is no quarter of history.
  H  THE FEEDS CHECK knows the new keys, read with and without importing.

    python tools/validate_em_scorecard.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import yaml  # noqa: E402

from altdata import em_scorecard as E  # noqa: E402
from altdata import feeds, observations, session  # noqa: E402
from altdata.sources import _imf_sdmx as sdmx  # noqa: E402
from altdata.sources import _publication as pub  # noqa: E402
from altdata.sources import bis_cbpol, em_lenses, imf_em, imf_weo, wb_qeds  # noqa: E402
from altdata.sources._base import FetchError  # noqa: E402
from gate_tmp import mkdtemp as gate_mkdtemp  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78
TD = Path(gate_mkdtemp("em_gate_"))
FX = REPO / "tools" / "fixtures" / "em"
WRITERS = (imf_weo, imf_em, bis_cbpol, wb_qeds, em_lenses)


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


def load(name: str):
    return json.loads((FX / name).read_text(encoding="utf-8"))


def fake_get(url, params=None, timeout=None, headers=None, max_retries=None):
    """The fixtures by URL, as http_get_response returns them."""
    route = [("WEO_2025_OCT_VINTAGE", "weo_2025_oct.json"), ("WEO_2026_APR", "weo_current.json"),
             ("IMF.RES/WEO/", "weo_current.json"), ("/IL/", "il.json"), ("/ITG/", "itg.json"),
             ("/CPI/", "cpi.json"), ("WS_CBPOL", "bis_cbpol.csv"),
             ("DT.DOD.DECT.CD.AR.US", "qeds_ext.json"), ("DT.DOD.DSTC.CD.US", "qeds_st.json")]
    for frag, name in route:
        if frag in url:
            return (FX / name).read_bytes(), {"last-modified": "Fri, 09 Oct 2026 14:00:00 GMT"}
    raise FetchError(f"no fixture for {url}")


def patched(fn):
    saved = {m: getattr(m, "http_get_response", None) for m in WRITERS}
    for m in WRITERS:
        if saved[m] is not None:
            m.http_get_response = fn
    return saved


def restore(saved):
    for m, f in saved.items():
        if f is not None:
            m.http_get_response = f


def store(name: str) -> observations.ObservationStore:
    return observations.ObservationStore(str(TD / f"{name}.db"))


def pull_all(db):
    return {m.SOURCE: m.pull(db=db) for m in WRITERS}


# ---------------------------------------------------------------------------
def group_a() -> None:
    print(f"\n{LINE}\nA. SHAPES\n{LINE}")
    cfg = E.config()
    iso = [c["iso3"] for c in cfg["countries"]]
    check(len(iso) == 13 and iso[-1] == "THA" and len(set(iso)) == 13,
          "thirteen countries: the twelve largest EM plus Thailand")
    check(all(("target" in c) and c.get("target_source") for c in cfg["countries"])
          and all(isinstance(c["target"], (int, float)) or c["target"] is None
                  for c in cfg["countries"]),
          "each carries its inflation target (or a stated none) with its source")
    check(tuple(iso) == imf_weo.COUNTRIES == imf_em.COUNTRIES == em_lenses.COUNTRIES,
          "the IMF writers and the lenses mirror the config's countries")
    check(set(bis_cbpol.COUNTRIES) == {c["iso3"] for c in cfg["countries"] if c.get("policy_rate")}
          and all(bis_cbpol.ISO2[c["iso3"]] == c["iso2"] for c in cfg["countries"]
                  if c["iso3"] in bis_cbpol.ISO2),
          "the BIS writer reads exactly the countries with a configured policy rate")
    nys = cfg["not_yet_sourced"]
    need = {"reserves_imp": set(em_lenses.WITH_IMPORTS), "reserves_std": set(em_lenses.WITH_QEDS),
            "ext_debt_gdp": set(em_lenses.WITH_QEDS), "real_rate": set(em_lenses.WITH_RATE_AND_CPI),
            "infl_gap": set(em_lenses.WITH_TARGET)}
    gaps = []
    for c in iso:
        for lens, have in need.items():
            declared = (nys.get(c) or {}).get(lens)
            no_target = lens == "infl_gap" and next(x for x in cfg["countries"]
                                                    if x["iso3"] == c)["target"] is None
            if c not in have and not declared and not no_target:
                gaps.append((c, lens))
            if c in have and declared:
                gaps.append((c, lens, "declared but sourced"))
    check(not gaps, f"every (country, lens) is sourced, or declared not_yet_sourced with "
                    f"its candidate, or has no target ({gaps})")
    check(all("candidate" in w for v in nys.values() for w in v.values()
              if "target" not in w or "candidate" in w),
          "each not_yet_sourced entry names its candidate source")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))["metrics"]
    src = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))["sources"]
    for m in WRITERS:
        miss = [k for k in m.KEYS if not all((reg.get(k) or {}).get(f) for f in (
            "units", "information_half_life", "revision_policy", "mechanism_group"))]
        trig = [k for k in m.KEYS if (reg.get(k) or {}).get("trigger_eligible") is not False]
        s = src.get(m.SOURCE) or {}
        check(m.KEYS and not miss and not trig and s.get("status") == "live"
              and (REPO / s.get("implemented_by", "x")).is_file(),
              f"{m.SOURCE}: {len(m.KEYS)} keys registered, trigger_eligible false, source live")
    check(sum(len(m.KEYS) for m in WRITERS) == 175, "175 keys across the five writers "
          "(174, and bis.policy_rate: every area, ST-R5.43a)")
    lenses = [L["id"] for L in cfg["lenses"]]
    check(lenses == ["ca_gdp", "reserves_imp", "reserves_std", "ext_debt_gdp", "real_rate",
                     "infl_gap", "fiscal_gdp", "debt_gdp"]
          and all(L["worse"] in ("lower", "higher") for L in cfg["lenses"]),
          "the eight lenses of section 4.5, each with its vulnerable direction")


def group_b() -> None:
    print(f"\n{LINE}\nB. PARSERS ON THE REAL SHAPES\n{LINE}")
    cur = sdmx.parse(load("weo_current.json"))
    oct_ = sdmx.parse(load("weo_2025_oct.json"))
    check(cur["published"] == "2026-04-15T13:00:00Z" and oct_["published"] == "2025-11-19T21:00:00Z",
          f"WEO: each edition's instant is the later of its PUBLICATION_DATE and UPDATE_DATE "
          f"({cur['published']}, {oct_['published']})")
    rows = imf_weo.rows_from(cur, now="2026-10-11T12:00:00Z")
    today = session.session_date()
    check(rows and max(r["observed_at"] for r in rows) <= today
          and not any(r["observed_at"] > today for r in rows),
          f"WEO: projections (to 2031 in the response) are not stored -- latest row "
          f"{max(r['observed_at'] for r in rows)}")
    bra = {r["observed_at"]: r["value"] for r in rows if r["registry_key"] == "em.weo.gdp_usd.bra"}
    check(abs(bra.get("2025-12-31", 0) - 2279917849000) < 1,
          "WEO: GDP is stored in dollars as served (Brazil 2025: 2,279,917,849,000); "
          "SCALE is a display hint")
    debt = {r["observed_at"]: r["value"] for r in rows if r["registry_key"] == "em.weo.debt_gdp.bra"}
    check(abs(debt.get("2025-12-31", 0) - 93.329176) < 1e-6, "WEO: Brazil's 2025 debt 93.3% of GDP")
    check(sdmx.period_end("2026-M06") == "2026-06-30" and sdmx.period_end("2026-Q1") == "2026-03-31"
          and sdmx.period_end("2026Q1") == "2026-03-31" and sdmx.period_end("2025") == "2025-12-31"
          and sdmx.period_end("2026-09") == "2026-09-30", "periods to period-ends, every shape")
    il = sdmx.parse(load("il.json"))
    req = imf_em.requests(E.config())
    r_il = imf_em.rows_from(il, req[0][2], req[0][3], now="2026-10-11T12:00:00Z")
    check(r_il and all(r["registry_key"].startswith("em.ifs.reserves_usd.") for r in r_il)
          and all(r["availability_kind"] == "observed" for r in r_il),
          f"IL: {len(r_il)} reserve rows at the response's own publication instant")
    try:
        imf_em.rows_from(il, req[1][2], req[1][3])
        bad("a series of the wrong dimensions raises")
    except ValueError as exc:
        ok(f"a series of the wrong dimensions raises ({str(exc)[:60]})")
    # Observation periods out of order parse to the same values.
    raw = load("cpi.json")
    vals = raw["data"]["structures"][0]["dimensions"]["observation"][0]["values"]
    n = len(vals)
    raw["data"]["structures"][0]["dimensions"]["observation"][0]["values"] = vals[::-1]
    for s in raw["data"]["dataSets"][0]["series"].values():
        s["observations"] = {str(n - 1 - int(i)): o for i, o in s["observations"].items()}
    a = {(tuple(sorted(x["dims"].items())), p): v for x in sdmx.parse(load("cpi.json"))["series"]
         for p, v in x["obs"].items()}
    b = {(tuple(sorted(x["dims"].items())), p): v for x in sdmx.parse(raw)["series"]
         for p, v in x["obs"].items()}
    check(a == b and a, "TIME_PERIOD out of chronological order parses to the same values")
    bad_shape = load("il.json")
    bad_shape["data"]["structures"][0]["dimensions"]["observation"][0]["id"] = "DATE"
    try:
        sdmx.parse(bad_shape)
        bad("an observation dimension other than TIME_PERIOD raises")
    except ValueError:
        ok("an observation dimension other than TIME_PERIOD raises")
    bis = bis_cbpol.parse((FX / "bis_cbpol.csv").read_text(encoding="utf-8"))
    check(set(bis) == {"BRA", "CHN"} and bis["BRA"].get("2026-09-30") == 13.75,
          f"BIS: Brazil's September 2026 policy rate 13.75% (month-end key)")
    try:
        bis_cbpol.parse("REF_AREA,VALUE\nBR,1\n")
        bad("a BIS CSV without its columns raises")
    except ValueError:
        ok("a BIS CSV without its columns raises")
    q = wb_qeds.parse(load("qeds_st.json"), "DT.DOD.DSTC.CD.US")
    check(q["published"] == "2026-08-08T00:00:00Z" and abs(q["series"]["BRA"]["2026-03-31"]
                                                         - 114736933763.24) < 1,
          "QEDS: lastupdated 2026-08-07 read as the end of that day; Brazil's short-term debt "
          "2026Q1 by country.id (countryiso3code is empty in the response)")
    for payload, why in (([{"message": [{"id": "120", "value": "Invalid value"}]}], "an error answer"),
                         ([{"page": 1, "pages": 2}, []], "a second page")):
        try:
            wb_qeds.parse(payload, "DT.DOD.DSTC.CD.US")
            bad(f"QEDS: {why} raises")
        except ValueError:
            ok(f"QEDS: {why} raises")


def group_c_d() -> observations.ObservationStore:
    print(f"\n{LINE}\nC/D. WEO VINTAGES, AS-OF, IDEMPOTENCE\n{LINE}")
    db = store("main")
    saved = patched(fake_get)
    try:
        first = pull_all(db)
        check(all(r["status"] == "OK" and r["written"] > 0 for r in first.values()),
              "every writer's first pull is the backfill: "
              + ", ".join(f"{k} {r['written']}" for k, r in first.items()))
        second = pull_all(db)
        check(all(r["status"] == "OK" and r["written"] == 0 for r in second.values()),
              "a second pull of every writer writes nothing")
    finally:
        restore(saved)
    k = "em.weo.debt_gdp.chn"
    vint = db.vintages(k, "2025-12-31")
    vals = sorted(float(v["value_num"]) for v in vint)
    check(len(vint) == 2 and abs(vals[0] - 96.262) < 1e-6 and abs(vals[1] - 99.237751) < 1e-6,
          f"two editions of China's 2025 debt are two vintages, never an overwrite ({vals})")
    before = {str(r["observed_at"])[:10]: float(r["value_num"]) for r in db.as_of(k, "2026-03-01T00:00:00Z")}
    after = {str(r["observed_at"])[:10]: float(r["value_num"]) for r in db.as_of(k, "2026-05-01T00:00:00Z")}
    check(abs(before["2025-12-31"] - 96.262) < 1e-6 and abs(after["2025-12-31"] - 99.237751) < 1e-6,
          "an as-of read in March 2026 sees October 2025's edition; in May, April's")
    unchanged = db.vintages("em.weo.gdp_usd.bra", "2015-12-31")
    check(len(unchanged) <= 2, f"history the editions agree on is not duplicated "
                               f"({len(unchanged)} vintage(s) of Brazil's 2015 GDP)")
    return db


def group_e() -> None:
    print(f"\n{LINE}\nE. STALE, NOT EMPTY\n{LINE}")
    db = store("outage")

    def boom(*a, **k):
        raise FetchError("simulated outage")

    def empty(url, **k):
        if "worldbank" in url:
            return json.dumps([{"page": 1, "pages": 1, "lastupdated": "2026-08-07"}, []]).encode(), {}
        if "bis.org" in url:
            return b"FREQ,REF_AREA,TIME_PERIOD,OBS_VALUE\n", {}
        d = load("il.json")
        d["data"]["dataSets"][0]["series"] = {}
        return json.dumps(d).encode(), {}
    for fn, why in ((boom, "an outage"), (empty, "a response with none of the countries")):
        saved = patched(fn)
        try:
            for m in WRITERS:
                n0 = db.count()
                r = m.pull(db=db)
                check(r["status"] == pub.STALE and r["written"] == 0 and db.count() == n0,
                      f"{m.SOURCE}: {why} is STALE and writes nothing")
        finally:
            restore(saved)
    db.close()


def group_f(db) -> None:
    print(f"\n{LINE}\nF. THE LENSES\n{LINE}")

    def last(key):
        r = db.as_of(key)
        return (str(r[-1]["observed_at"])[:10], float(r[-1]["value_num"]),
                observations.canonical_instant(r[-1]["available_at"])) if r else None

    def at(key, day):
        return next((float(r["value_num"]), observations.canonical_instant(r["available_at"]))
                    for r in db.as_of(key) if str(r["observed_at"])[:10] == day)
    d, v, av = last("em.lens.real_policy_rate.bra")
    pol, pav = at("em.bis.policy_rate.bra", d)
    cpi, cav = at("em.cpi.yoy.bra", d)
    check(abs(v - (pol - cpi)) < 1e-9 and av == max(pav, cav),
          f"real policy rate = policy rate less CPI ({pol} - {cpi:.2f} at {d}), available "
          f"at the later input")
    d, v, _ = last("em.lens.inflation_gap.chn")
    cpi, _ = at("em.cpi.yoy.chn", d)
    check(abs(v - (cpi - 2.0)) < 1e-9, f"inflation gap = CPI less the 2% target (China {d})")
    d, v, _ = last("em.lens.reserves_import_months.bra")
    res, _ = at("em.ifs.reserves_usd.bra", d)
    months = em_lenses._month_ends_back(d, 12)                      # noqa: SLF001
    imp = [at("em.itg.imports_usd.bra", m)[0] for m in months]
    check(abs(v - res / (sum(imp) / 12)) < 1e-6, f"months of imports = reserves over the "
                                                f"trailing twelve months' average ({d}: {v:.1f})")
    ilast = last("em.ifs.reserves_usd.bra")[0]
    mlast = last("em.itg.imports_usd.bra")[0]
    check(d == min(ilast, mlast), f"a month without its imports has no row (reserves to "
                                  f"{ilast}, imports to {mlast}, lens to {d})")
    d, v, _ = last("em.lens.ext_debt_gdp.bra")
    ext, _ = at("em.qeds.ext_debt_usd.bra", d)
    gdp = at("em.weo.gdp_usd.bra", f"{d[:4]}-12-31") if d[:4] <= "2025" else \
        at("em.weo.gdp_usd.bra", f"{int(d[:4]) - 1}-12-31")
    check(abs(v - 100 * ext / gdp[0]) < 1e-9 and 20 < v < 60,
          f"external debt % of GDP over the latest full year's GDP ({d}: {v:.1f}%)")
    d, v, _ = last("em.lens.reserves_st_debt.chn")
    check(abs(v - at("em.ifs.reserves_usd.chn", d)[0] / at("em.qeds.st_debt_usd.chn", d)[0]) < 1e-9,
          f"reserves over short-term debt at the quarter-end (China {d}: {v:.2f}x)")


def group_g(db) -> None:
    print(f"\n{LINE}\nG. THE SCORECARD\n{LINE}")
    sc = E.build(db)
    t = E.table(sc)
    check(len(t["rows"]) == 13 and len(t["columns"]) == 9, "13 countries x 8 lenses")
    blanks = [(r[0], i) for r in t["rows"] for i, c in enumerate(r[1:]) if not str(c).strip()]
    check(not blanks, "no blank cell anywhere")
    tw = next(r for r in t["rows"] if r[0] == "Taiwan")
    check(tw[3].startswith("not tracked: no QEDS row") and tw[1].startswith("not tracked: nothing stored"),
          "a fixture country with a missing lens renders 'not tracked' with why (Taiwan: "
          "no QEDS row; no stored WEO in the fixture)")
    br = sc["cells"]["BRA"]["debt_gdp"]
    check(br["state"] == "tracked" and br["rank"] in (1, 2) and br["as_of"] == "2025-12-31",
          f"Brazil's government debt ranks among the most vulnerable of the two fixture "
          f"countries (#{br['rank']}, data as of {br['as_of']})")
    ranks = sc["ranks"]["debt_gdp"]
    check(sorted(ranks.values()) == list(range(1, len(ranks) + 1)),
          "each column is ranked 1..n over its tracked cells")
    src = (REPO / "altdata" / "em_scorecard.py").read_text(encoding="utf-8")
    check(not any(w in src for w in ("composite =", "score =", "sum(cell", "mean(")),
          "nothing sums or averages the lenses into one number")
    qb = E.quarterly_block(db)
    check(set(qb) >= {"title", "table", "notes", "data"} and qb["data"]["cells"]
          and all("percentile" not in k or k.endswith("_ordinal")
                  for c in qb["data"]["cells"] for k in c),
          "the Quarterly's block: the stack's sub-section shape, ordinals only in its data")
    line = E.monthly_line(db)
    check("no lens deteriorated on the quarter" in line,
          f"the fixture's WEO cells were knowable a quarter ago and unchanged since: the "
          f"line says no lens deteriorated ({line[:80]})")
    young = store("young")
    young.write_many([{"registry_key": "em.lens.real_policy_rate.bra", "instrument": None,
                       "observed_at": "2026-09-30", "available_at": "2026-10-09T00:00:00Z",
                       "value": 3.0, "source": "gate", "availability_kind": "observed"}])
    check("no cell was knowable a quarter ago" in E.monthly_line(young, "2026-10-11T12:00:00Z"),
          "with nothing knowable a quarter ago, the line says the quarter's change cannot "
          "be read yet -- not that nothing deteriorated")
    young.close()
    # A quarter of history: an earlier vintage of Brazil's real rate, knowable in June.
    d = store("history")
    key = "em.lens.real_policy_rate.bra"
    d.write_many([{"registry_key": key, "instrument": None, "observed_at": f"{y}-{m:02d}-28",
                   "available_at": "2026-06-01T00:00:00Z", "value": 8.0 + 0.01 * i,
                   "source": "gate", "availability_kind": "observed"}
                  for i, (y, m) in enumerate((y, m) for y in range(2017, 2026) for m in range(1, 13))])
    d.write_many([{"registry_key": key, "instrument": None, "observed_at": "2026-09-30",
                   "available_at": "2026-10-05T00:00:00Z", "value": 2.0, "source": "gate",
                   "availability_kind": "observed"}])
    worst = E.deteriorations(E.build(d, "2026-10-11T12:00:00Z"))
    line = E.monthly_line(d, "2026-10-11T12:00:00Z")
    check(worst and worst[0]["country"] == "Brazil" and worst[0]["as_of"] == "2026-09-30",
          f"a real rate falling to its ten-year low is the quarter's largest deterioration "
          f"({worst[0]['points']:.0f} percentile points)" if worst else "a deterioration is found")
    check("Brazil real policy rate +2.0 pts" in line and "data as of 2026-09-30" in line
          and line.count("data as of") <= 3,
          f"the Monthly line names it with its data-as-of ({line[:140]}...)")
    d.close()


def group_h() -> None:
    print(f"\n{LINE}\nH. THE FEEDS CHECK\n{LINE}")
    names = [m.SOURCE for m in WRITERS]
    ow = list(feeds.OFFICIAL_WRITERS)
    check(all(n in ow for n in names) and ow.index("em_lenses") > max(
        ow.index(n) for n in names[:-1]),
          "the five writers are in the official group, the lenses after their sources")
    check(all(feeds.static_keys(m.SOURCE) == list(m.KEYS) for m in WRITERS),
          "each writer's KEYS read from source without importing equal the module's")
    ok_keys = set(feeds.official_keys())
    check(all(k in ok_keys for m in WRITERS for k in m.KEYS),
          f"the feeds roster knows all {sum(len(m.KEYS) for m in WRITERS)} new keys")
    check("em_sc.monthly_line" in (REPO / "monthly_macro" / "stack.py").read_text(encoding="utf-8"),
          "the Monthly's slow layers print the scorecard's line")


def main() -> int:
    print(f"{LINE}\nTHE EM VULNERABILITY SCORECARD (AQ-9a)\n{LINE}")
    group_a()
    group_b()
    db = group_c_d()
    group_e()
    group_f(db)
    group_g(db)
    db.close()
    group_h()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
