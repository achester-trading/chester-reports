"""
SEC EDGAR XBRL frames -- the five hyperscalers' annual operating cash flow and
capital expenditure, for GTM-4's cash-flow bridge.

    python -m altdata.sources.edgar_xbrl          # one pull, summary to stdout

The J.P. Morgan Guide batch, part 2 (17 Oct 2026; change order of 3 Oct 2026,
GTM-4): operating cash flow less capex, 2019 to the latest filed year, beside the
Guide's consensus capex path (sourced figures, config/gtm.yaml).

SOURCE. https://data.sec.gov/api/xbrl/frames/us-gaap/<tag>/USD/CY<year>.json --
no key. One call per tag per calendar year returns every filer's one fact that
most closely fits the year (an annual duration of 365 days, +/- 30). The filers,
their CIKs and the tags are config/ai_buckets.yaml's `bridge`. A FISCAL year sits
in the calendar frame its larger part falls in, so Microsoft's year to June 2024
and Oracle's to May 2024 are in CY2023: the stored row keeps the fact's own end
date, and altdata/gtm_equities.py groups by the year of the period's midpoint,
which is the frame's year.

THE CONTACT. EDGAR serves only a User-Agent carrying a contact address, and this
module takes it from edgar.user_agent() (CHESTER_SEC_CONTACT) and nowhere else.
Without it the run is PENDING, "not configured", and fetches nothing.

STORED, dollars, instrument = the filer's ticker (Alphabet as GOOGL), observed_at
= the fact's period end:
  edgar.xbrl_operating_cash_flow   NetCashProvidedByUsedInOperatingActivities
  edgar.xbrl_capex                 PaymentsToAcquirePropertyPlantAndEquipment,
                                   else PaymentsToAcquireProductiveAssets
                                   (Amazon's purchases of property and equipment)
A filer with none of a field's tags in a year's frame writes nothing for it, and
the bridge prints "not stored" in its place.

ST-4 (st-t1-rest, 18 Oct 2026) adds, from config/edgar_xbrl.yaml:
  edgar.xbrl_long_term_debt  the hyperscalers' year-end long-term debt and cash,
  edgar.xbrl_cash            from the annual INSTANT frames (CY<year>Q4I) --
                             calc.hs_netdebt_12m's inputs
  edgar.xbrl_mu_inventory    Micron's quarter-end inventory and its quarter's
  edgar.xbrl_mu_cogs_q       cost of goods, from Micron's two company-concept
                             files (api/xbrl/companyconcept): calc.mu_inv_days'
A filer or quarter without a tag writes nothing, as above.

A102 (1 Nov 2026; tranche 6 of the price-source migration) adds, behind
config/price_sources.yaml's `fundamentals` and `earnings_dates` switches and
config/edgar_xbrl.yaml's two `enabled` flags (off until the operator starts the
parallel run):
  edgar.fund_<ticker>_<field>  Yahoo's 40 yfinance.fund_* keys' twins, from the
                               company facts, each vintage at its filing's
                               acceptance (FUND_KEYS; the tags are the config's)
  events, type 'earnings',     past report dates (the 8-K item 2.02 acceptance)
  source 'sec_edgar'           and the quarter's diluted EPS as first filed; no
                               forward date and no consensus (listed gaps)
    python -m altdata.sources.edgar_xbrl fundamentals|earnings [--dry-run]
Requests are paced (`request_pause_s`, under the SEC's ten a second).

WHICH YEARS. The first pull reads every year from `first_year` to last year; a
later pull reads the years not yet stored and the last two years again (a 10-K
filed in the spring, a restatement), so a run is a handful of calls. The frames
carry no publication instant, so available_at is the write instant
(`ingest_instant`): late but never early. revision_policy: revised.
"""

from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Optional

import yaml

from .. import observations, session
from . import _publication as pub
from . import edgar
from ._base import http_get_json

log = logging.getLogger(__name__)

SOURCE = "edgar_xbrl"
FRAMES_URL = "https://data.sec.gov/api/xbrl/frames/us-gaap/{tag}/USD/CY{year}.json"
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "ai_buckets.yaml"
ST4_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "edgar_xbrl.yaml"
INSTANT_URL = "https://data.sec.gov/api/xbrl/frames/us-gaap/{tag}/USD/CY{year}Q4I.json"
CONCEPT_URL = ("https://data.sec.gov/api/xbrl/companyconcept/CIK{cik:010d}/us-gaap/"
               "{tag}.json")
DEBT_KEY = "edgar.xbrl_long_term_debt"
CASH_KEY = "edgar.xbrl_cash"
MU_INV_KEY = "edgar.xbrl_mu_inventory"
MU_COGS_KEY = "edgar.xbrl_mu_cogs_q"
BALANCE_KEYS = {"long_term_debt": DEBT_KEY, "cash": CASH_KEY}
MEMORY_KEYS = {"inventory": MU_INV_KEY, "cogs": MU_COGS_KEY}
OCF_KEY = "edgar.xbrl_operating_cash_flow"
CAPEX_KEY = "edgar.xbrl_capex"
FIELD_KEYS = {"operating_cash_flow": OCF_KEY, "capex": CAPEX_KEY}
KEYS = [OCF_KEY, CAPEX_KEY, DEBT_KEY, CASH_KEY, MU_INV_KEY, MU_COGS_KEY]
REFRESH_YEARS = 2


def bridge_config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return (yaml.safe_load(fh) or {}).get("bridge") or {}


def st4_config(path: Optional[Path] = None) -> dict:
    with open(path or ST4_CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def rows_from_frames(frames: dict[tuple[str, int], dict], cfg: dict,
                     available: str, field_keys: Optional[dict] = None,
                     tags: Optional[dict] = None) -> list[dict]:
    """Observation rows from {(tag, year): frame JSON}. For each filer, field and
    year the FIRST tag in the field's list that carries the filer wins; a filer
    with none writes nothing."""
    by_cik = {int(f["cik"]): f["ticker"] for f in cfg["filers"]}
    years = sorted({y for _, y in frames})
    out = []
    for field, tags in (tags or cfg["tags"]).items():
        key = (field_keys or FIELD_KEYS)[field]
        for year in years:
            seen: set[str] = set()
            for tag in tags:
                fr = frames.get((tag, year)) or {}
                for d in fr.get("data") or []:
                    try:
                        tk = by_cik.get(int(d.get("cik")))
                        val = float(d.get("val"))
                    except (TypeError, ValueError):
                        continue
                    end = str(d.get("end") or "")[:10]
                    if not tk or tk in seen or len(end) != 10:
                        continue
                    seen.add(tk)
                    out.append({"registry_key": key, "instrument": tk,
                                "observed_at": end, "value": val,
                                "available_at": available,
                                "availability_kind": "ingest_instant"})
    return out


def rows_from_concept(concept: dict, key: str, ticker: str, available: str,
                      duration: bool, quarters: int) -> list[dict]:
    """One company-concept file's facts as rows, the newest `quarters` periods: a
    quarter-length duration (80 to 100 days) for a flow, the instant for a
    stock. Where a period was filed twice, the later filing wins."""
    best: dict[str, tuple[str, float]] = {}
    for f in ((concept.get("units") or {}).get("USD") or []):
        end = str(f.get("end") or "")[:10]
        if len(end) != 10:
            continue
        if duration:
            start = str(f.get("start") or "")[:10]
            if len(start) != 10:
                continue
            days = (dt.date.fromisoformat(end) - dt.date.fromisoformat(start)).days
            if not 80 <= days <= 100:
                continue
        elif f.get("start"):
            continue
        try:
            val = float(f.get("val"))
        except (TypeError, ValueError):
            continue
        filed = str(f.get("filed") or "")
        if end not in best or filed >= best[end][0]:
            best[end] = (filed, val)
    ends = sorted(best)[-quarters:]
    return [{"registry_key": key, "instrument": ticker, "observed_at": e,
             "value": best[e][1], "available_at": available,
             "availability_kind": "ingest_instant"} for e in ends]


def years_to_read(db: Optional[observations.ObservationStore], cfg: dict,
                  today: Optional[dt.date] = None) -> list[int]:
    today = today or session.session_date_obj()
    last = today.year - 1
    first = int(cfg.get("first_year", 2019))
    held: set[int] = set()
    if db is not None:
        for (end,) in db.conn.execute(
                "SELECT DISTINCT observed_at FROM observations WHERE registry_key = ?",
                (OCF_KEY,)):
            # The frame's year: the year of the period's midpoint.
            d = dt.date.fromisoformat(str(end)[:10]) - dt.timedelta(days=182)
            held.add(d.year)
    return [y for y in range(first, last + 1)
            if y not in held or y > last - REFRESH_YEARS]


def fetch_frames(years: list[int], cfg: dict, headers: dict) -> dict:
    out = {}
    for tags in cfg["tags"].values():
        for tag in tags:
            for y in years:
                out[(tag, y)] = http_get_json(FRAMES_URL.format(tag=tag, year=y),
                                              headers=headers, timeout=60)
    return out


def st4_rows(years: list[int], cfg: dict, headers: dict, available: str) -> list[dict]:
    """ST-4's EDGAR rows: the hyperscalers' year-end balance sheets and Micron's
    quarters. A fault here costs these rows only, never the bridge's."""
    s4 = st4_config()
    out: list[dict] = []
    bal = s4.get("balance") or {}
    frames = {}
    for tags in (bal.get("tags") or {}).values():
        for tag in tags:
            for y in [y for y in years if y >= int(bal.get("first_year", 2019))]:
                frames[(tag, y)] = http_get_json(INSTANT_URL.format(tag=tag, year=y),
                                                 headers=headers, timeout=60)
    out += rows_from_frames(frames, cfg, available, BALANCE_KEYS, bal.get("tags"))
    mem = s4.get("memory") or {}
    for field, tags in (mem.get("tags") or {}).items():
        for tag in tags:
            try:
                c = http_get_json(CONCEPT_URL.format(cik=int(mem["cik"]), tag=tag),
                                  headers=headers, timeout=60)
            except Exception:                                   # noqa: BLE001
                continue
            rows = rows_from_concept(c, MEMORY_KEYS[field], mem["ticker"], available,
                                     duration=(field == "cogs"),
                                     quarters=int(mem.get("quarters", 12)))
            if rows:
                out += rows
                break
    return out


# =============================================================================
# A102 (1 Nov 2026; tranche 6 of the price-source migration): fundamentals and
# past earnings dates from EDGAR, behind config/price_sources.yaml's
# `fundamentals` and `earnings_dates` families. config/edgar_xbrl.yaml's
# `fundamentals` and `earnings` blocks hold the tags, each cited, and the two
# `enabled` switches (off: the parallel run is the operator's to start).
# =============================================================================
COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
FUND_FIELDS = ("operating_cash_flow", "capex", "net_debt", "inventory", "cogs")
EVENT_SOURCE = "sec_edgar"
NO_CONSENSUS = "not tracked (the consensus was Yahoo's; no keyless source)"
_LAST_CALL = [0.0]


def fund_key(ticker: str, field: str) -> str:
    return f"edgar.fund_{ticker.lower()}_{field}"


def _fund_keys() -> list[str]:
    """Yahoo's 40 keys' EDGAR twins, member for member (fundamentals.keys_for)."""
    from . import fundamentals                                  # noqa: PLC0415
    return [k.replace("yfinance.fund_", "edgar.fund_", 1) for k in fundamentals.KEYS]


FUND_KEYS = _fund_keys()


def _sec_get(url: str, headers: dict, pause: float) -> dict:
    """One SEC request, paced: never closer than `pause` seconds to the last."""
    import time                                                 # noqa: PLC0415
    wait = _LAST_CALL[0] + pause - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    try:
        return http_get_json(url, headers=headers, timeout=60)
    finally:
        _LAST_CALL[0] = time.monotonic()


def acceptance_map(submissions: dict) -> dict[str, str]:
    """{accession: acceptance instant (canonical UTC)} from a submissions file."""
    rec = (submissions.get("filings") or {}).get("recent") or {}
    out = {}
    for accn, acc in zip(rec.get("accessionNumber") or [], rec.get("acceptanceDateTime") or []):
        inst = observations.canonical_instant(acc) if acc else None
        if accn and inst:
            out[str(accn)] = inst
    return out


def _filed_end_of_day(filed: str) -> Optional[str]:
    """A fact's `filed` date read as its END in ET (late, never early)."""
    try:
        d = dt.date.fromisoformat(str(filed)[:10])
    except ValueError:
        return None
    t = dt.datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=session._eastern_tz())  # noqa: SLF001
    return observations.canonical_instant(t.astimezone(dt.timezone.utc).isoformat())


def _days(a: str, b: str) -> int:
    return (dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days


def period_facts(companyfacts: dict, tags: list[str], accept: dict[str, str],
                 unit: str = "USD") -> dict[tuple[str, str], list[tuple[str, float, str]]]:
    """{(start or "", end): [(available_at, value, kind), ...] oldest first}.

    The first tag that carries a period wins it; a later tag fills only the
    periods the earlier ones lack. Each fact is available at its accession's
    acceptance (`observed`), else at its filed date's end (`reconstructed`)."""
    gaap = ((companyfacts.get("facts") or {}).get("us-gaap") or {})
    out: dict[tuple[str, str], list] = {}
    for tag in tags:
        mine: dict[tuple[str, str], list] = {}
        for f in (((gaap.get(tag) or {}).get("units") or {}).get(unit) or []):
            end = str(f.get("end") or "")[:10]
            start = str(f.get("start") or "")[:10]
            if len(end) != 10 or (start and len(start) != 10):
                continue
            try:
                val = float(f.get("val"))
            except (TypeError, ValueError):
                continue
            inst = accept.get(str(f.get("accn") or ""))
            kind = "observed"
            if not inst:
                inst, kind = _filed_end_of_day(f.get("filed")), "reconstructed"
            if not inst:
                continue
            mine.setdefault((start, end), []).append((inst, val, kind))
        for p, v in mine.items():
            if p not in out:
                out[p] = sorted(set(v))
    return out


def _as_of(vintages: list[tuple[str, float, str]], t: str) -> Optional[tuple[float, str]]:
    best = None
    for inst, val, kind in vintages:
        if inst <= t:
            best = (val, kind)
    return best


def quarterly_flow(facts: dict, since: str) -> list[tuple[str, str, float, str]]:
    """[(quarter end, available_at, value, kind)] for a flow, every vintage that
    changed the quarter's value. A quarter filed as three months is read as
    filed; otherwise it is the year-to-date less the previous quarter's
    year-to-date from the same start, at the later acceptance of the two."""
    out = []
    ends = sorted({e for (_s, e) in facts if e >= since})
    for end in ends:
        recipes = [((s, e),) for (s, e) in facts
                   if e == end and s and 80 <= _days(s, e) <= 100]
        for (s, e) in list(facts):
            if e != end or not s or not 100 < _days(s, e) <= 380:
                continue
            for (s2, e2) in facts:
                if s2 == s and e2 < end and 80 <= _days(e2, end) <= 100:
                    recipes.append(((s, e), (s2, e2)))
        if not recipes:
            continue
        instants = sorted({i for r in recipes for p in r for (i, _v, _k) in facts[p]})
        last = None
        for t in instants:
            val = kind = None
            for r in recipes:
                got = [_as_of(facts[p], t) for p in r]
                if all(got):
                    val = got[0][0] - (got[1][0] if len(got) > 1 else 0.0)
                    kind = ("reconstructed" if any(g[1] == "reconstructed" for g in got)
                            else "observed")
                    break
            if val is not None and val != last:
                out.append((end, t, val, kind))
                last = val
    return out


def instant_series(facts: dict, since: str) -> dict[str, list[tuple[str, float, str]]]:
    """{period end: vintages} for a balance-sheet (instant) fact."""
    return {e: v for (s, e), v in facts.items() if not s and e >= since}


def fundamentals_rows(ticker: str, companyfacts: dict, accept: dict[str, str],
                      cfg: dict) -> list[dict]:
    """One filer's edgar.fund_* rows, every vintage at its acceptance."""
    since = str(cfg.get("quarters_from") or "2019-01-01")
    rows: list[dict] = []

    def emit(field: str, end: str, inst: str, val: float, kind: str) -> None:
        rows.append({"registry_key": fund_key(ticker, field), "instrument": None,
                     "observed_at": end, "value": val, "available_at": inst,
                     "availability_kind": kind})

    for field, spec in (cfg.get("fields") or {}).items():
        if spec.get("only") and ticker not in spec["only"]:
            continue
        kind = spec.get("kind")
        if kind == "flow":
            sign = float(spec.get("sign", 1))
            for end, inst, val, k in quarterly_flow(
                    period_facts(companyfacts, spec["tags"], accept), since):
                emit(field, end, inst, sign * val, k)
        elif kind == "stock":
            for end, vints in instant_series(
                    period_facts(companyfacts, spec["tags"], accept), since).items():
                last = None
                for inst, val, k in vints:
                    if val != last:
                        emit(field, end, inst, val, k)
                        last = val
        elif kind == "net":
            debt = instant_series(period_facts(companyfacts, spec["debt"], accept), since)
            cash = instant_series(period_facts(companyfacts, spec["cash"], accept), since)
            for end in sorted(set(debt) & set(cash)):
                last = None
                for t in sorted({i for i, _v, _k in debt[end] + cash[end]}):
                    d, c = _as_of(debt[end], t), _as_of(cash[end], t)
                    if d and c and d[0] - c[0] != last:
                        last = d[0] - c[0]
                        emit(field, end, t, last,
                             "reconstructed" if "reconstructed" in (d[1], c[1]) else "observed")
    return rows


def a102_config(path: Optional[Path] = None) -> dict:
    return st4_config(path)


def fetch_fundamentals(cfg: dict, headers: dict) -> list[dict]:
    pause = float(cfg.get("request_pause_s", 0.15))
    rows: list[dict] = []
    for f in cfg.get("filers") or []:
        cik = int(f["cik"])
        facts = _sec_get(COMPANYFACTS_URL.format(cik=cik), headers, pause)
        subs = _sec_get(SUBMISSIONS_URL.format(cik=cik), headers, pause)
        rows += fundamentals_rows(str(f["ticker"]), facts, acceptance_map(subs), cfg)
    return rows


# -- past earnings dates ------------------------------------------------------
FOURTH_QUARTER_REASON = "not filed as a quarter"
NOT_FOUND_REASON = "EPS not found"


def eps_gap_reason(symbol: str, period_end: str, periodic_form: str,
                   cfg: dict) -> str:
    """Why an event carries no EPS (A114): the name's listed gap in
    config/edgar_xbrl.yaml `earnings.gaps` (for a quarter ending after its
    `after` date, when one is given); the fourth-quarter reason only when the
    quarter's periodic report is a 10-K; "EPS not found" otherwise. Only the
    reason: the figure stays absent, never filled from another source."""
    gap = (cfg.get("gaps") or {}).get(symbol) or {}
    after = str(gap.get("after") or "")
    if gap.get("reason") and (not after or period_end > after):
        return str(gap["reason"])
    if periodic_form == "10-K":
        return FOURTH_QUARTER_REASON
    return NOT_FOUND_REASON


def earnings_events(symbol: str, submissions: dict, companyfacts: dict,
                    cfg: dict) -> list[tuple[str, "object"]]:
    """[(available_at, Event)] for one name's past reports: the 8-K item 2.02's
    acceptance as observed_at, the quarter's diluted EPS as first filed, written
    once the quarter's 10-Q/10-K is accepted (available at the later of the two).
    No consensus, so no surprise; no forward date."""
    from .. import events as ev_mod                             # noqa: PLC0415
    rec = (submissions.get("filings") or {}).get("recent") or {}
    n = len(rec.get("form") or [])
    col = lambda name: list(rec.get(name) or [""] * n)          # noqa: E731
    forms, items, accns = col("form"), col("items"), col("accessionNumber")
    accs, periods = col("acceptanceDateTime"), col("reportDate")
    reports, periodic = [], {}
    for i in range(n):
        acc = observations.canonical_instant(accs[i]) if accs[i] else None
        if not acc:
            continue
        if forms[i] in ("8-K", "8-K/A") and "2.02" in str(items[i] or "").split(","):
            if forms[i] == "8-K":
                reports.append((acc, accns[i]))
        elif forms[i] in ("10-Q", "10-K") and periods[i]:
            p = str(periods[i])[:10]
            if p not in periodic or acc < periodic[p][0]:
                periodic[p] = (acc, accns[i], forms[i])
    eps = period_facts(companyfacts, list(cfg.get("eps_tags") or []),
                       acceptance_map(submissions), unit="USD/shares")
    lag = int(cfg.get("max_report_lag_days", 100))
    out = []
    for acc, accn in sorted(reports)[-int(cfg.get("quarters_back", 12)):]:
        day = acc[:10]
        prior = [p for p in periodic if p < day and _days(p, day) <= lag]
        if not prior:
            continue
        end = max(prior)
        p_acc, p_accn, p_form = periodic[end]
        q =[v for (s, e), v in eps.items() if e == end and s and 80 <= _days(s, e) <= 100]
        first = q[0][0] if q else None
        avail = max(acc, p_acc, first[0] if first else "")
        reported = first[1] if first else None
        out.append((avail, ev_mod.Event(
            type="earnings", observed_at=acc, source=EVENT_SOURCE,
            title=(f"{symbol} reported EPS {reported}" if reported is not None
                   else f"{symbol} earnings (8-K item 2.02)"),
            entities=[symbol], key=f"edgar-earnings-{symbol}-{day}",
            payload={"symbol": symbol, "reported_eps": reported,
                     "eps_note": (None if reported is not None
                                  else eps_gap_reason(symbol, end, p_form, cfg)),
                     "eps_estimate": None, "surprise_pct": None,
                     "consensus": NO_CONSENSUS, "surprise_kind": None,
                     "period_end": end, "report_accession": accn,
                     "report_accepted_at": acc, "periodic_accession": p_accn,
                     "periodic_accepted_at": p_acc,
                     "eps_concept": "us-gaap diluted EPS, three months, as first filed"})))
    return out


def write_earnings(pairs: list[tuple[str, "object"]], store=None) -> dict:
    """Each event at its own reconstructed instant (EventStore.write_many per
    instant), availability `observed`: the acceptances are EDGAR's own."""
    from .. import events as ev_mod                             # noqa: PLC0415
    own = store is None
    ev = store or ev_mod.EventStore()
    tot = {"seen": 0, "inserted": 0, "duplicates": 0}
    try:
        by: dict[str, list] = {}
        for avail, e in pairs:
            by.setdefault(avail, []).append(e)
        for avail, evs in sorted(by.items()):
            r = ev.write_many(evs, available_at=avail, availability_kind="observed")
            for k in tot:
                tot[k] += r[k]
    finally:
        if own:
            ev.close()
    return tot


def fetch_earnings(cfg: dict, pause: float, headers: dict,
                   symbols: Optional[list[str]] = None) -> tuple[list, dict]:
    from . import earnings as yf_earnings                       # noqa: PLC0415
    syms = list(symbols or yf_earnings.universe())
    ciks = edgar.cik_map(headers)
    rep: dict = {"symbols": len(syms), "missing": [], "failed": {}}
    pairs: list = []
    for s in syms:
        cik = ciks.get(s)
        if not cik:
            rep["missing"].append(s)
            continue
        try:
            subs = _sec_get(SUBMISSIONS_URL.format(cik=int(cik)), headers, pause)
            facts = _sec_get(COMPANYFACTS_URL.format(cik=int(cik)), headers, pause)
        except Exception as exc:                                # noqa: BLE001
            rep["failed"][s] = f"{type(exc).__name__}: {exc}"[:120]
            continue
        pairs += earnings_events(s, subs, facts, cfg)
    return pairs, rep


def pull_a102(part: str, run_id: Optional[str] = None, db=None,
              dry_run: bool = False) -> dict:
    """The operator's command for one part ("fundamentals" or "earnings"),
    whatever `enabled` says: the first run is the backfill (every quarter from
    `quarters_from`, every report in `quarters_back`), a later one the update."""
    ua = edgar.user_agent()
    if not ua:
        return pub.pending(SOURCE, f"not configured: {edgar.CONTACT_VAR} is unset, "
                           f"and EDGAR serves no request without a contact", run_id)
    cfg = a102_config()
    headers = {"User-Agent": ua}
    if part == "fundamentals":
        fc = cfg.get("fundamentals") or {}
        if dry_run:
            rows = fetch_fundamentals(fc, headers)
            return {"dry_run": True, "rows": len(rows),
                    "keys_with_rows": len({r["registry_key"] for r in rows}),
                    "keys_without_rows": sorted(set(FUND_KEYS)
                                                - {r["registry_key"] for r in rows})}
        return pub.run(SOURCE, FUND_KEYS, lambda: fetch_fundamentals(fc, headers),
                       run_id=run_id, db=db, window_days=3700)
    ec = cfg.get("earnings") or {}
    pairs, rep = fetch_earnings(ec, float((cfg.get("fundamentals") or {})
                                          .get("request_pause_s", 0.15)), headers)
    if dry_run:
        return {"dry_run": True, "events": len(pairs), "report": rep}
    return {"written": write_earnings(pairs), "report": rep}


def pull(run_id: Optional[str] = None, db=None) -> dict:
    ua = edgar.user_agent()
    if not ua:
        return pub.pending(SOURCE, f"not configured: {edgar.CONTACT_VAR} is unset, "
                           f"and EDGAR serves no request without a contact", run_id)
    cfg = bridge_config()

    def produce() -> list[dict]:
        own = db is None
        store = db or observations.open_writer(__name__)
        try:
            years = years_to_read(store, cfg)
        finally:
            if own:
                store.close()
        now = session.utc_iso(timespec="microseconds")
        frames = fetch_frames(years, cfg, {"User-Agent": ua})
        rows = rows_from_frames(frames, cfg, now)
        try:
            rows += st4_rows(years, cfg, {"User-Agent": ua}, now)
        except Exception as exc:                                # noqa: BLE001
            log.warning("edgar_xbrl: ST-4's balance-sheet and Micron rows failed, "
                        "the bridge's stand: %s", exc)
        # A102's parallel run, once the operator enables it: the fundamentals'
        # vintages at their acceptances, and the past earnings dates as events.
        a102 = a102_config()
        fc, ec = a102.get("fundamentals") or {}, a102.get("earnings") or {}
        if fc.get("enabled"):
            try:
                rows += fetch_fundamentals(fc, {"User-Agent": ua})
            except Exception as exc:                            # noqa: BLE001
                log.warning("edgar_xbrl: A102's fundamentals failed, the rest "
                            "stand: %s", exc)
        if ec.get("enabled"):
            try:
                pairs, _rep = fetch_earnings(ec, float(fc.get("request_pause_s", 0.15)),
                                             {"User-Agent": ua})
                write_earnings(pairs)
            except Exception as exc:                            # noqa: BLE001
                log.warning("edgar_xbrl: A102's earnings dates failed, the rest "
                            "stand: %s", exc)
        return rows
    # The bridge reaches back to 2019: a backfilled year is older than the default
    # write window and must still land on the first run.
    keys = KEYS + (FUND_KEYS if (a102_config().get("fundamentals") or {}).get("enabled")
                   else [])
    return pub.run(SOURCE, keys, produce, run_id=run_id, db=db, window_days=3700)


if __name__ == "__main__":
    import json
    import sys
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    # A102: `fundamentals` or `earnings` [--dry-run] runs that part alone (the
    # backfill on its first run); no argument is the daily pull, as before.
    args = sys.argv[1:]
    part = next((a for a in args if a in ("fundamentals", "earnings")), None)
    out = (pull_a102(part, dry_run="--dry-run" in args) if part else pull())
    print(json.dumps(out, indent=2, sort_keys=True, default=str))
