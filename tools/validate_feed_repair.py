#!/usr/bin/env python3
"""
Validation gate: a61b-feed-repair -- the feed repair of 24 Oct 2026, before the
1 Nov Monthly (docs/briefs/a61b-feed-repair-notes.md). On synthetic fixtures; no
network, no model, no live store (each store here is the gate's own).

  A  FRED'S NON-JSON PATH. A body that is not JSON is retried (three attempts in
     all, honouring Retry-After up to its cap) and then fails with its HTTP
     status and the body's first characters; a 4xx other than 429 is not
     retried; the pull marks the series failed with that reason and logs ONE
     summary line, no traceback; feeds.pull_fred records the series STALE with
     it; request starts are at least PACING_SECONDS apart; the ALFRED history
     reads through the same fetch.
  B  THE EDGAR CALL. http_get_json takes `headers` (the project User-Agent by
     default, overridden per call), so edgar_xbrl's call with its SEC contact
     header goes through; every caller of http_get_json passes only keywords the
     helper takes.
  C  STATISTICS CANADA. A body that is not JSON is refused by name (its
     Content-Type and first characters); a JSON body parses to both vectors.
  D  A REFUSED SOURCE IS NEVER REQUESTED AGAIN. MBA and Farside are declared
     refused in source_registry.yaml: their pulls return REFUSED with the gap
     text and make no request; feeds counts REFUSED as no failure; the readers
     print "not tracked: <source> refuses automated reads since <date>"; the
     rent writer no longer asks Apartment List.
  E  A DECLARED KEY IS NEVER STALE. A superseded, refused, gap or while_held key
     (the registry's member_overrides) is listed apart by the store check and
     never counted stale; an undeclared key of the same age is stale. The
     declarations the repair made are in force.
  F  INHERITANCE. A derived key takes the LARGEST publication lag among its own
     family and its declared inputs, on a fixture; calc.surprise_vs_naive.core_pce
     now waits as long as calc.naive_expectation.core_pce, and a correlation with
     natural gas's weekly leg inherits EIA's lag.
  G  THE NEW FAMILIES. Each carries its source, reason and a lag within its
     bound, and matches a registered key; each declared new family is present.

    python tools/validate_feed_repair.py
"""

from __future__ import annotations

import ast
import json
import logging
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

TD = Path(gate_mkdtemp("feed_repair_"))
LINE = "=" * 78
PASS = FAIL = 0
EVENING = "2026-10-24T22:00:00+00:00"


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


class Resp:
    def __init__(self, status: int, text: str, headers: dict | None = None):
        self.status_code, self.text, self.headers = status, text, headers or {}

    def json(self):
        return json.loads(self.text)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def scripted(*answers):
    """A fake requests.get answering in order; records each call's headers."""
    calls = []

    def get(url, params=None, timeout=None, headers=None):
        calls.append({"url": url, "headers": dict(headers or {})})
        a = answers[min(len(calls) - 1, len(answers) - 1)]
        if isinstance(a, Exception):
            raise a
        return a
    get.calls = calls
    return get


class LogCatch(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


# ---------------------------------------------------------------------------
def group_a() -> None:
    from altdata.sources import fred
    from altdata.sources._base import FetchError
    head("A. FRED'S NON-JSON PATH")
    html = "<!DOCTYPE html><html><head><title>Too Many Requests</title></head>" + "x" * 300
    waits = []
    g = scripted(Resp(200, html), Resp(429, html, {"Retry-After": "7"}), Resp(200, html))
    try:
        fred.get_json("https://fred.test/obs", {}, get=g, sleep=waits.append)
        err = None
    except FetchError as e:
        err = str(e)
    check(err is not None and len(g.calls) == fred.RETRY_ATTEMPTS == 3
          and "body not JSON" in err and "HTTP 200" in err
          and "Too Many Requests" in err and "x" * 200 not in err,
          f"three attempts, then a FetchError naming the status and the body's first "
          f"{fred.SNIPPET_CHARS} characters ({(err or '')[:110]}...)")
    check(waits == [fred.RETRY_BACKOFF, 7.0],
          f"a doubling backoff, and Retry-After honoured on the 429 ({waits})")
    waits2 = []
    g2 = scripted(Resp(503, "busy", {"Retry-After": "900"}),
                  Resp(200, json.dumps({"observations": [{"date": "2026-10-01",
                                                          "value": "1.5"}]})))
    d = fred.get_json("https://fred.test/obs", {}, get=g2, sleep=waits2.append)
    check(d["observations"][0]["value"] == "1.5" and waits2 == [fred.RETRY_AFTER_CAP],
          f"a 503 is retried and a long Retry-After is capped at {fred.RETRY_AFTER_CAP:.0f} s; "
          f"the second answer is read ({waits2})")
    g3 = scripted(Resp(400, "Bad Request: series does not exist"))
    try:
        fred.get_json("https://fred.test/obs", {}, get=g3, sleep=lambda s: None)
        e3 = ""
    except FetchError as e:
        e3 = str(e)
    check(len(g3.calls) == 1 and e3.startswith("HTTP 400"),
          f"a 400 is not retried ({e3[:60]})")
    check(g.calls[0]["headers"].get("User-Agent", "").startswith("chester-reports"),
          "the fetch sends the project's User-Agent")

    # The pull: one series fails non-JSON, one succeeds; one summary line.
    from altdata import config

    class FakeStore:
        def __init__(self):
            self.w = {}

        def write_observations(self, key, obs, source=None, merge=False):
            self.w[key] = obs
            return len(obs)
    specs = [s for s in config.FRED_PULL_SERIES if s.key in ("gdp_deflator", "cpi")]
    real = fred.get_json

    def fake_get_json(url, params, get=None, sleep=None):
        if params["series_id"] == "GDPDEF":
            return real(url, params, get=scripted(Resp(200, html)), sleep=lambda s: None)
        return {"observations": [{"date": "2026-09-01", "value": "330.1"}]}
    os.environ.setdefault("FRED_API_KEY", "gate-placeholder-not-a-key")
    fred.get_json = fake_get_json
    pace, fred.PACING_SECONDS = fred.PACING_SECONDS, 0.0
    lc = LogCatch()
    logging.getLogger(fred.__name__).addHandler(lc)
    logging.getLogger(fred.__name__).setLevel(logging.DEBUG)
    try:
        s = fred.pull(FakeStore(), series=specs, full=True)
    finally:
        fred.get_json, fred.PACING_SECONDS = real, pace
        logging.getLogger(fred.__name__).removeHandler(lc)
    failed = dict(s["failed"])
    warn = [r.getMessage() for r in lc.records if r.levelno >= logging.WARNING]
    check(s["success"] == 1 and "gdp_deflator" in failed
          and "body not JSON" in failed["gdp_deflator"],
          f"the pull marks the series failed with the status in the reason "
          f"({failed.get('gdp_deflator', '')[:80]})")
    check(len(warn) == 1 and warn[0].startswith("fred: 1 of 2 series failed: gdp_deflator")
          and not any("Traceback" in r.getMessage() for r in lc.records),
          f"ONE summary line for the run and no traceback ({warn})")
    src = (REPO / "altdata" / "sources" / "fred.py").read_text(encoding="utf-8")
    check("time.monotonic() - last_start" in src and fred.PACING_SECONDS >= 0.5,
          f"request starts at least {fred.PACING_SECONDS} s apart: at most "
          f"{60 / fred.PACING_SECONDS:.0f} a minute, under FRED's 120")
    hsrc = (REPO / "altdata" / "fred_history.py").read_text(encoding="utf-8")
    check("from .sources.fred import get_json" in hsrc,
          "the ALFRED history reads through the same fetch")
    # feeds.pull_fred: STALE with its reason.
    from altdata import feeds
    rec = {}
    orig_rec, orig_present = feeds.record_attempted, feeds.secrets.present
    import altdata.sources.fred as fsrc
    orig_pull = fsrc.pull
    feeds.record_attempted = lambda fam, keys, **kw: rec.update({fam: kw})
    feeds.secrets.present = lambda name: True
    fsrc.pull = lambda store: {"total": 2, "success": 1,
                               "failed": [("gdp_deflator", "HTTP 200, body not JSON: <html>")]}
    try:
        import altdata.store as store_mod
        orig_store = store_mod.Store
        store_mod.Store = lambda *a, **k: None
        feeds.pull_fred()
    finally:
        feeds.record_attempted, feeds.secrets.present = orig_rec, orig_present
        fsrc.pull = orig_pull
        store_mod.Store = orig_store
    fl = (rec.get("fred") or {}).get("failed") or {}
    check(fl.get("fred.gdp_deflator", "").startswith("fred: HTTP 200, body not JSON"),
          f"feeds records the series STALE with the status in its reason ({fl})")


def group_b() -> None:
    import inspect
    from altdata.sources import _base, edgar_xbrl
    head("B. THE EDGAR CALL AND EVERY CALLER OF http_get_json")
    params = inspect.signature(_base.http_get_json).parameters
    check("headers" in params, "http_get_json takes headers")
    seen = []
    orig = _base.requests.get

    def fake(url, params=None, timeout=None, headers=None):
        seen.append(dict(headers or {}))
        return Resp(200, json.dumps({"data": []}))
    sec_ua = {"User-Agent": "chester-reports/1.0 (ops@example.invalid)"}
    _base.requests.get = fake
    try:
        _base.http_get_json("https://example.test/a")
        out = edgar_xbrl.fetch_frames([2025], {"tags": {"capex": ["Assets"]}}, sec_ua)
    except Exception as exc:                                    # noqa: BLE001
        out = exc
    finally:
        _base.requests.get = orig
    check(seen and seen[0].get("User-Agent", "").startswith("chester-reports/")
          and "@" not in seen[0]["User-Agent"],
          "the default header is the project's User-Agent, with no contact in it")
    check(isinstance(out, dict) and ("Assets", 2025) in out and len(seen) == 2
          and seen[1] == sec_ua,
          f"edgar_xbrl's frames call goes through with its SEC header, no TypeError "
          f"({type(out).__name__})")
    bad = []
    for p in (REPO / "altdata").rglob("*.py"):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and getattr(n.func, "id", getattr(n.func, "attr", "")) \
                    == "http_get_json":
                for kw in n.keywords:
                    if kw.arg and kw.arg not in params:
                        bad.append(f"{p.relative_to(REPO)}:{n.lineno} {kw.arg}")
    check(not bad, f"every caller passes only keywords the helper takes ({bad or 'none'})")


def group_c() -> None:
    from altdata.sources import statcan_cpi as sc
    head("C. STATISTICS CANADA")
    try:
        sc.rows_from(b"<!DOCTYPE html><html><body>Service unavailable</body></html>",
                     "text/html; charset=utf-8")
        e = ""
    except sc.NotJSON as exc:
        e = str(exc)
    check("text/html" in e and "Service unavailable" in e,
          f"a body that is not JSON is refused by name ({e[:90]})")

    def block(vid):
        return {"status": "SUCCESS", "object": {"vectorId": vid, "vectorDataPoint": [
            {"refPer": "2025-09-01", "value": 160.0, "releaseTime": "2025-10-21T08:30"},
            {"refPer": "2026-09-01", "value": 163.2, "releaseTime": "2026-10-19T08:30"}]}}
    rows = sc.rows_from(json.dumps([block(v) for v in sc.VECTORS]).encode(), "application/json")
    check(len(rows) == 2 and rows[0]["value"] == 2.0
          and rows[0]["available_at"].startswith("2026-10-19T12:30"),
          f"a JSON body parses: 163.2 over 160.0 is +2.0%, available at the release ({rows[0]})")


def group_d() -> None:
    from altdata.sources import _publication as pub, mba, farside, _base
    from altdata import feeds
    head("D. A REFUSED SOURCE IS NEVER REQUESTED AGAIN")
    asked = []
    o_get = _base.requests.get

    def forbid(*a, **k):
        asked.append(a[0] if a else k.get("url"))
        raise AssertionError("a refused source was requested")
    _base.requests.get = forbid
    try:
        rm, rf = mba.pull(run_id="gate"), farside.pull(run_id="gate")
    finally:
        _base.requests.get = o_get
    check(rm["status"] == pub.REFUSED == rf["status"] and not asked,
          f"MBA and Farside return REFUSED and request nothing ({rm['status']}, "
          f"{rf['status']}, asked {asked})")
    check(rm["reason"].startswith("not tracked: MBA refuses automated reads since 2026-10-24")
          and rf["reason"].startswith("not tracked: Farside refuses automated reads since 2026-10-24"),
          f"the reason is the gap line ({rf['reason'][:90]})")
    fails = feeds.writer_failures([("mba", mba)], {"mba": rm})
    check(fails == {}, "feeds counts a REFUSED writer as no failure of the run")
    fake_reg = {"sources": {"x": {"status": "live"}, "y": {"status": "refused",
                                                           "refused_since": "2026-01-02",
                                                           "short_name": "Y"}}}
    check(pub.refused("x", registry=fake_reg) is None
          and pub.refusal_text("y", registry=fake_reg)
          == "not tracked: Y refuses automated reads since 2026-01-02",
          "a live source is requested as before; a refused one carries its date")
    from altdata import crypto_blocks
    from altdata import observations
    db = TD / "empty.db"
    with observations.ObservationStore(str(db)) as st:
        line = crypto_blocks.etf_line(st, "btc", EVENING, "2026-10-24")
    check("not tracked: Farside refuses automated reads since 2026-10-24" in line[1],
          f"the Digital Assets ETF-flow line prints the gap ({line[1][:70]})")
    from altdata import st_r5_rates
    with observations.ObservationStore(str(db)) as st:
        m = st_r5_rates.mba(st, EVENING)
    check(m.get("absent") and m["reason"].startswith("not tracked: MBA"),
          "the MBA line prints the gap")
    rsrc = (REPO / "altdata" / "sources" / "rent_indices.py").read_text(encoding="utf-8")
    body = rsrc.split("def fetch_rows", 1)[1].split("\ndef ", 1)[0]
    check("APTLIST_PAGE" not in body and "ZILLOW_URL" in body,
          "the rent writer reads Zillow alone; Apartment List is no longer asked")


def group_e() -> None:
    import yaml
    from altdata import derived, observations
    import check_store_registry as csr
    head("E. A DECLARED KEY IS NEVER STALE")
    base = {"source": "fred", "native_horizon": "daily", "freq": "daily",
            "information_half_life": "until_next_release", "units": "ratio"}
    reg = {"metrics": {f"t.{k}": dict(base) for k in
                       ("old", "sup", "ref", "gap", "held")},
           "member_overrides": {"t.sup": {"status_extra": "superseded", "superseded_by": "t.old"},
                                "t.ref": {"status_extra": "refused", "gap_reason": "403"},
                                "t.gap": {"status_extra": "gap", "gap_reason": "retired"},
                                "t.held": {"status_extra": "while_held"}}}
    p = TD / "declared.db"
    with observations.ObservationStore(str(p)) as st:
        for k in ("old", "sup", "ref", "gap", "held"):
            st.write(f"t.{k}", None, "2026-09-01", "2026-09-01T21:00:00+00:00", 1.0, "fred")
    r = csr.check(str(p), EVENING, reg=reg)
    stale = {s["key"] for s in r["stale"]}
    dec = {d["key"]: d["status"] for d in r["declared"]}
    check(stale == {"t.old"} and dec == {"t.sup": "superseded", "t.ref": "refused",
                                         "t.gap": "gap", "t.held": "while_held"},
          f"only the undeclared key is stale; the four declared keys are listed apart "
          f"({sorted(stale)}, {dec})")
    check("declared, not stale" in csr.report(r), "the report prints the declared count")
    res = derived.resolve_registry(yaml.safe_load(
        (REPO / "metrics_registry.yaml").read_text(encoding="utf-8")))
    want = {"fred.ioer": "superseded", "overnight.tnx_chg": "superseded",
            "overnight.tnx_chg_pct": "superseded", "overnight.tnx_prior_settle": "superseded",
            "lbma.gold_pm_usd": "superseded", "crypto.total_market_cap_usd": "gap",
            "zec.crypto_cap_share": "gap", "llama.fees_aero": "gap", "llama.tvl_aero": "gap",
            "mba.purchase_sa_wow": "refused", "aptlist.rent_us": "refused",
            "farside.btc_total": "refused", "portfolio.position_qty": "while_held"}
    got = {k: derived.declared_status(res.get(k)) for k in want}
    check(got == want, f"the repair's declarations are in force ({[k for k in want if got[k] != want[k]] or 'all'})")
    check(res["fred.ioer"].get("superseded_by") == "fred.iorb"
          and res["overnight.tnx_chg"].get("superseded_by") == "yfinance.mkt_tnx",
          "each superseded key names the key that replaced it")
    bk = yaml.safe_load((REPO / "config" / "crypto_basket.yaml").read_text(encoding="utf-8"))
    names = bk.get("names") or bk
    aero = next((v for k, v in (names.items() if isinstance(names, dict) else [])
                 if k == "AERO"), {})
    lsrc = (REPO / "altdata" / "sources" / "llama.py").read_text(encoding="utf-8")
    check(bool(aero.get("llama_hold")) and 'n.get("llama_hold")' in lsrc,
          "AERO's DefiLlama series are held: declared, and the writer requests nothing for it")


def group_f() -> None:
    import yaml
    from altdata import derived
    head("F. INHERITANCE: THE LARGEST INPUT LAG")
    fams = [{"id": "weekly_posting", "keys": ["src.weekly"], "lag_sessions": 6, "max_lag": 7},
            {"id": "monthly_release", "keys": ["src.monthly"], "lag_sessions": 22, "max_lag": 25}]
    look = {"src.weekly": {"freq": "daily"}, "src.monthly": {"freq": "monthly"},
            "src.none": {"freq": "daily"}}.get
    lag, fam = derived.inherited_lag({"inputs": ["src.weekly", "src.monthly", "src.none"]},
                                     "calc.derived_x", fams, look)
    check(lag == 22 and "monthly_release" in fam and "src.monthly" in fam,
          f"a derived key takes the largest of its inputs' lags ({lag}, {fam})")
    lag0, _ = derived.inherited_lag({"inputs": ["src.none"]}, "calc.derived_y", fams, look)
    check(lag0 == 0, "an input with no family adds nothing")
    res = derived.resolve_registry(yaml.safe_load(
        (REPO / "metrics_registry.yaml").read_text(encoding="utf-8")))

    def allow(k):
        return derived.staleness_allowance_of(res[k], k)[0]
    check(allow("calc.surprise_vs_naive.core_pce") == allow("calc.naive_expectation.core_pce") == 54,
          "calc.surprise_vs_naive.core_pce waits 54 sessions, as the naive expectation does")
    check(allow("calc.yoy_core_pce") == 54 and allow("calc.r_real_10y_cpi") == 54
          and allow("calc.surprise_vs_naive.dxy") == 8,
          "calc.yoy_*, calc.r_real_* inherit the monthly release; the daily FX surprise H.10's lag")
    nat = [k for k in res if k.startswith("corr.") and "natgas" in k]
    check(nat and all(allow(k) >= 1 + 6 for k in nat),
          f"every correlation with natural gas's weekly leg inherits EIA's lag ({len(nat)} keys)")


def group_g() -> None:
    import yaml
    from altdata import derived
    head("G. THE NEW FAMILIES")
    fams = derived.publication_lags(REPO / "config" / "publication_lags.yaml")
    new = {"statcan_cpi", "japan_cpi", "uk_cpi", "thailand_cpi", "ecb_irs", "redfin",
           "nyfed_sce", "census_vip", "fred_h6_weekly", "btc_difficulty"}
    have = {f["id"]: f for f in fams}
    check(new <= set(have), f"each new family is present ({sorted(new - set(have)) or 'all'})")
    res = derived.resolve_registry(yaml.safe_load(
        (REPO / "metrics_registry.yaml").read_text(encoding="utf-8")))
    bad = [i for i in new & set(have)
           if not (have[i].get("source") and have[i].get("reason")
                   and have[i]["lag_sessions"] <= have[i]["max_lag"]
                   and any(derived.publication_lag(res[k], k, [have[i]])[0] for k in res))]
    check(not bad, f"each with its source, reason, a lag within its bound, matching a "
                   f"registered key ({bad or 'none'})")
    check(derived.staleness_allowance_of(res["fred.mmf_retail"], "fred.mmf_retail")[0] == 8 + 34
          and derived.staleness_allowance_of(res["mempool.difficulty"], "mempool.difficulty")[0] == 8 + 4,
          "retail money funds: weekly plus H.6's monthly release; the difficulty: weekly plus 4")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g):
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
