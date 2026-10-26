"""
Validation gate for the IMF IFS central-bank gold writer (altdata/sources/imf_ifs.py;
ruled 10 Oct 2026).

SEEDED, never sampled: the parser reads a fixture cut from the API's ACTUAL
response (tools/fixtures/imf_il_gold_volume.json -- the SDMX-JSON 2.0 body of
api.imf.org's IL dataflow, RGV_REVS, for China, Poland, Czechia and Russia,
trimmed to two years with its own shape and ordering intact), every store is a
throwaway, and the network is never reached. Nothing here opens the live store.

  A  THE PARSER, on the real shape: values in ounces (the SCALE attribute is not
     a multiplier); the time periods, which the response does NOT list in
     order, land on the right month-ends; the dataset's PUBLICATION_DATE is the
     publication instant; a response of another shape raises.
  B  SHAPES. The country list is config/imf_ifs.yaml's, mirrored literally in the
     module; KEYS read from source equal the imported module's; every key is a
     registered metric with the four fields, under a live imf_ifs source; the
     non-reporting countries are stored and registered but off the roster; the
     wgc.* names are superseded by imf.ifs.*; tonnes are a display conversion.
  C  THE DERIVED ROWS. Net purchases are the month's change; the aggregate sums
     the countries that reported both months, with its count beside it.
  D  AS-OF, IDEMPOTENCE, VINTAGES. available_at is the IMF's publication instant
     (`observed`), the ingest instant where none (`ingest_instant`), never the
     future; a re-pull writes nothing; a revision is a second vintage and an
     as-of before it still reads the first.
  E  STALE, NOT EMPTY. An outage, or a response with none of the countries,
     writes nothing.
  F  CHINA. SAFE against IFS: a gap under 1% passes, one over 1% is flagged.
  G  THE FEEDS CHECK KNOWS THE KEYS. imf_ifs is an official writer; its keys are
     on the roster and read ABSENT on an empty store.

    python tools/validate_imf_ifs.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import yaml  # noqa: E402

from altdata import feeds, observations  # noqa: E402
from altdata.sources import _publication as pub, imf_ifs as I  # noqa: E402
from altdata.sources._base import FetchError  # noqa: E402
from gate_tmp import mkdtemp as gate_mkdtemp  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78
TD = Path(gate_mkdtemp("imf_ifs_gate_"))
FIXTURE = REPO / "tools" / "fixtures" / "imf_il_gold_volume.json"
PUBLISHED = "2026-10-10T09:00:19.048001+00:00"
_N = 0


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


def store() -> observations.ObservationStore:
    global _N
    _N += 1
    return observations.ObservationStore(str(TD / f"s{_N}.db"))


def fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def set_stamp(payload: dict, stamp) -> dict:
    p = copy.deepcopy(payload)
    s, ds = p["data"]["structures"][0], p["data"]["dataSets"][0]
    for i, a in enumerate(s["attributes"]["dataSet"]):
        if a["id"] in ("PUBLICATION_DATE", "UPDATE_DATE"):
            ds["attributes"][i] = None if stamp is None else [stamp]
    return p


def set_obs(payload: dict, country: str, period: str, value: str) -> dict:
    p = copy.deepcopy(payload)
    s, ds = p["data"]["structures"][0], p["data"]["dataSets"][0]
    ci = [v["id"] for v in s["dimensions"]["series"][0]["values"]].index(country)
    ti = [v["value"] for v in s["dimensions"]["observation"][0]["values"]].index(period)
    for k, ser in ds["series"].items():
        if int(k.split(":")[0]) == ci:
            ser["observations"][str(ti)][0] = value
    return p


def serve(payload: dict):
    calls = []

    def fake(url, params=None, timeout=None, headers=None, **k):
        calls.append((url, params, headers))
        return json.dumps(payload).encode("utf-8"), {}
    fake.calls = calls
    return fake


def with_http(fake, fn):
    saved = I.http_get_response
    I.http_get_response = fake
    try:
        return fn()
    finally:
        I.http_get_response = saved


# ---------------------------------------------------------------------------
def group_a() -> None:
    head("A  THE PARSER, ON THE API'S ACTUAL RESPONSE SHAPE")
    raw = fixture()
    tvals = [v["value"] for v in raw["data"]["structures"][0]["dimensions"]["observation"][0]["values"]]
    p = I.parse(raw)
    s = p["series"]
    # THE API LISTS PERIODS IN NO PARTICULAR ORDER (the full response opens
    # "1977-M12, 1978-M03, ..."), so the parser must index, never assume. The
    # same response with its period list reversed must parse identically.
    rev = copy.deepcopy(raw)
    od = rev["data"]["structures"][0]["dimensions"]["observation"][0]
    n = len(od["values"])
    od["values"] = list(reversed(od["values"]))
    for ser in rev["data"]["dataSets"][0]["series"].values():
        ser["observations"] = {str(n - 1 - int(i)): o for i, o in ser["observations"].items()}
    check(I.parse(rev)["series"] == I.parse(raw)["series"] and len(tvals) == n,
          "the periods are read by index, not position: the response with its "
          "period list reversed parses identically")
    check(s["CHN"]["2026-06-30"] == 75_440_000.0 and s["CHN"]["2026-02-28"] == 74_220_000.0,
          "China in ounces: 75,440,000 at June 2026 (SCALE 6 is not a multiplier), "
          "and 74,220,000 at February -- SAFE's own figure for that month")
    check(max(s["POL"]) == "2026-09-30" and abs(s["POL"]["2026-09-30"] - 21_633_794.527) < 1e-6,
          "Poland's latest month and value land on the right month-end")
    check(max(s["RUS"]) == "2025-11-30" and max(s["CHN"]) == "2026-06-30"
          and max(s["CZE"]) == "2026-08-31",
          "each country's last month is its own (Russia stops at Nov 2025)")
    check(p["published"] == "2026-10-10T09:00:19.048001500Z",
          "the publication instant is the dataset's PUBLICATION_DATE/UPDATE_DATE")
    bad = copy.deepcopy(raw)
    bad["data"]["structures"][0]["dimensions"]["series"][2]["id"] = "UNITS"
    try:
        I.parse(bad)
        check(False, "a response without a UNIT dimension raises")
    except ValueError:
        check(True, "a response without a UNIT dimension raises")
    bad = copy.deepcopy(raw)
    bad["data"]["structures"][0]["dimensions"]["series"][2]["values"][0]["id"] = "USD"
    try:
        I.parse(bad)
        check(False, "a series in another unit raises")
    except ValueError:
        check(True, "a series in another unit raises (only FTO, ounces, is read)")
    u, params = I.url()
    check(u.startswith("https://api.imf.org/external/sdmx/3.0/data/dataflow/IMF.STA/IL/+/")
          and ".RGV_REVS.*.M" in u and "dataservices.imf.org" not in u
          and params == {"attributes": "all", "measures": "all"},
          "one request to the SDMX 3.0 API's IL dataflow, never the legacy service")


def group_b() -> None:
    head("B  SHAPES")
    cfg = I.config()
    cc = cfg["countries"]
    check(tuple(c["iso3"] for c in cc) == I.COUNTRIES,
          f"the module's COUNTRIES mirror config/imf_ifs.yaml ({len(cc)})")
    check(tuple(c["iso3"] for c in cc if c.get("reporting") is False) == I.NOT_REPORTING,
          "and NOT_REPORTING mirrors its reporting: false")
    named = {"CHN", "POL", "IND", "TUR", "SGP", "CZE", "HUN", "UZB", "KAZ", "THA"}
    check(named <= set(I.COUNTRIES) and len(I.COUNTRIES) == 27
          and sum(1 for c in cc if not c.get("added")) == 25,
          "the twenty-five largest holders plus the order's ten named (two not "
          "already among them)")
    check(not {"IMF", "EZB", "BIS"} & set(I.COUNTRIES), "supranational holders are not countries")
    check(feeds.static_keys("imf_ifs") == list(I.KEYS),
          "KEYS read from source equal the imported module's (an import failure "
          "cannot take the writer off the roster)")
    reg = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))["metrics"]
    src = yaml.safe_load((REPO / "source_registry.yaml").read_text(encoding="utf-8"))["sources"]
    allk = list(I.LEVEL_SERIES) + list(I.NET_SERIES) + [I.AGG_KEY, I.AGG_COUNT_KEY]
    miss = [k for k in allk if not all((reg.get(k) or {}).get(f) for f in (
        "units", "information_half_life", "revision_policy", "mechanism_group"))]
    check(not miss and all(reg[k]["source"] == "imf_ifs" and reg[k]["revision_policy"] == "revised"
                           and reg[k]["units"] == "count" for k in allk),
          f"all {len(allk)} keys registered: source imf_ifs, revised, ounces as a count")
    s = src.get("imf_ifs") or {}
    check(s.get("status") == "live" and (REPO / s.get("implemented_by", "x")).is_file(),
          "source imf_ifs is live, implemented by the writer")
    nr = [I.LEVEL + c.lower() for c in I.NOT_REPORTING]
    check(not set(nr) & set(I.KEYS) and set(nr) <= set(reg),
          "Russia and Lebanon are stored and registered, but off the freshness roster")
    for k, new in (("wgc.cb_gold_holdings_t", "imf.ifs.gold_reserves_oz."),
                   ("wgc.cb_net_purchases_t", "imf.ifs.gold_net_purchases_oz.")):
        m = reg.get(k) or {}
        check(m.get("status_extra") == "superseded"
              and str(m.get("superseded_by", "")).startswith(new),
              f"{k} stays as a name, superseded by {new}<iso3>")
    vocab = yaml.safe_load((REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))["vocabularies"]
    check("superseded" in (vocab.get("status_extra") or []), "`superseded` is a declared status")
    check(abs(I.tonnes(32150.7466 * 2290) - 2290) < 1e-9 and I.OZ_PER_TONNE == cfg["ounces_per_tonne"],
          "tonnes are a display conversion at 32,150.7466 oz a tonne")


def group_c() -> None:
    head("C  THE DERIVED ROWS")
    p = I.parse(fixture())
    rows = I.rows_from(p, now="2026-10-11T01:00:00+00:00")
    by = {(r["registry_key"], r["observed_at"]): r["value"] for r in rows}
    check(by[(I.NET + "chn", "2026-06-30")] == 75_440_000 - 74_960_000,
          "China's June net purchases = June less May (480,000 oz)")
    m = "2026-08-31"
    want = sum(p["series"][c][m] - p["series"][c]["2026-07-31"] for c in ("POL", "CZE"))
    check(abs(by[(I.AGG_KEY, m)] - want) < 1e-6 and by[(I.AGG_COUNT_KEY, m)] == 2,
          "the August aggregate sums the two countries that reported July and August, "
          "and says two")
    check((I.NET + "rus", "2025-12-31") not in by and by[(I.AGG_COUNT_KEY, "2025-11-30")] == 4,
          "a month a country did not report adds nothing for it (Russia after November)")
    check(not any(r["observed_at"] == min(p["series"]["CHN"]) and r["registry_key"] == I.NET + "chn"
                  for r in rows), "no net purchase for a country's first month")


def group_d() -> None:
    head("D  AS-OF, IDEMPOTENCE, VINTAGES")
    p = I.parse(fixture())
    rows = I.rows_from(p, now="2026-10-11T01:00:00+00:00")
    check(all(r["available_at"] == PUBLISHED and r["availability_kind"] == "observed" for r in rows),
          "available_at is the IMF's publication instant, `observed`")
    r2 = I.rows_from(I.parse(set_stamp(fixture(), None)), now="2026-10-11T01:00:00+00:00")
    check(all(r["availability_kind"] == "ingest_instant"
              and r["available_at"].startswith("2026-10-11T01:00:00") for r in r2),
          "with no stamp in the response, the ingest instant (`ingest_instant`)")
    r3 = I.rows_from(I.parse(set_stamp(fixture(), "2030-01-01T00:00:00Z")),
                     now="2026-10-11T01:00:00+00:00")
    check(all(r["available_at"].startswith("2026-10-11") for r in r3),
          "a stamp in the future is never used (the ingest instant stands)")
    st = store()
    first = with_http(serve(fixture()), lambda: I.pull(db=st))
    n_rows = len(I.rows_from(I.parse(fixture())))
    check(first["status"] == pub.OK and first["written"] == n_rows,
          f"the first pull writes every month served -- the backfill ({first['written']} rows)")
    again = with_http(serve(fixture()), lambda: I.pull(db=st))
    check(again["status"] == pub.OK and again["written"] == 0, "a re-pull writes nothing")
    rev = set_stamp(set_obs(fixture(), "POL", "2026-M08", "21000000"), "2026-10-10T20:00:00Z")
    third = with_http(serve(rev), lambda: I.pull(db=st))
    n = st.conn.execute("SELECT COUNT(*) FROM observations WHERE registry_key=? AND "
                        "observed_at='2026-08-31'", (I.LEVEL + "pol",)).fetchone()[0]
    check(third["written"] == 5 and n == 2,
          "a revision writes a second vintage of the month (and of the two net "
          "purchases and the aggregate it moves), never an overwrite")
    latest = {r["observed_at"]: r["value_num"] for r in st.as_of(I.LEVEL + "pol")}
    early = {r["observed_at"]: r["value_num"] for r in
             st.as_of(I.LEVEL + "pol", as_of="2026-10-10T12:00:00+00:00")}
    check(latest["2026-08-31"] == 21_000_000 and early["2026-08-31"] != 21_000_000,
          "the reader gets the revision; an as-of before it still reads the first")
    check(all(r["available_at"] <= observations.canonical_instant("2026-10-10T12:00:00Z")
              for r in st.as_of(I.LEVEL + "pol", as_of="2026-10-10T12:00:00+00:00")),
          "nothing read at a cutoff is available after it")


def group_e() -> None:
    head("E  STALE, NOT EMPTY")
    st = store()

    def boom(*a, **k):
        raise FetchError("simulated outage")
    r = with_http(boom, lambda: I.pull(db=st))
    cnt = st.conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    check(r["status"] == pub.STALE and r["written"] == 0 and cnt == 0,
          "an outage is STALE and writes nothing")
    empty = copy.deepcopy(fixture())
    empty["data"]["dataSets"][0]["series"] = {}
    r = with_http(serve(empty), lambda: I.pull(db=st))
    check(r["status"] == pub.STALE and "none of the configured" in r["reason"],
          "a response with none of the countries is STALE, not a quiet month")


def group_f() -> None:
    head("F  CHINA: SAFE AGAINST IFS")
    st = store()

    def put(key, pts):
        st.write_many([{"registry_key": key, "instrument": None, "observed_at": d,
                        "available_at": "2026-10-10T09:00:00+00:00", "value": v,
                        "source": "synthetic", "availability_kind": "observed"}
                       for d, v in pts])
    put("safe.gold_reserves_oz", [("2026-04-30", 74_640_000.0), ("2026-05-31", 74_960_000.0),
                                  ("2026-06-30", 75_440_000.0), ("2026-07-31", 75_600_000.0)])
    put(I.LEVEL + "chn", [("2026-04-30", 74_640_000.0), ("2026-05-31", 74_960_000.0 * 1.005),
                          ("2026-06-30", 75_440_000.0 * 1.015)])
    r = I.crosscheck(st, "2026-10-11T00:00:00+00:00")
    check(len(r["months"]) == 3 and [m["month"] for m in r["flagged"]] == ["2026-06-30"],
          "a 0.5% gap passes; a 1.5% gap is flagged (tolerance 1%, config)")
    check(r["safe_latest"] == "2026-07-31" and r["ifs_latest"] == "2026-06-30",
          "and it reports each source's latest month (SAFE leads IFS)")


def group_g() -> None:
    head("G  THE FEEDS CHECK KNOWS THE NEW KEYS")
    check("imf_ifs" in feeds.OFFICIAL_WRITERS and "imf_ifs" not in feeds.EARLY_WRITERS,
          "imf_ifs is an official writer, run in the 16:10 pass")
    check(set(I.KEYS) <= set(feeds.official_keys()), f"its {len(I.KEYS)} keys are on the roster")
    st = store()
    f = feeds.freshness(store=st)
    off = f["feeds"]["official"]
    check(off["absent"] == len(feeds.official_keys()) and off["expected"] >= len(I.KEYS),
          "an empty store reads them ABSENT, not fine")


def main() -> int:
    print(LINE)
    print("IMF IFS central-bank gold gate")
    print(LINE)
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g):
        try:
            g()
        except Exception as exc:                                  # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n  {PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
