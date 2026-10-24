"""
SEC EDGAR: the hyperscalers' capex GUIDANCE, read from their own 10-Q and 10-K
filings (A66; signal-triage items 26 and 63). Config: config/edgar_guidance.yaml.

    python -m altdata.sources.edgar_guidance dry-run  # the same requests; prints, writes nothing
    python -m altdata.sources.edgar_guidance          # one pull, summary to stdout
    python -m altdata.sources.edgar_guidance show     # what is stored, as of now

RULE 30: NO BY-HAND DATA LINE. A figure enters only as a sourced record: the
filing's own sentence, quoted verbatim (at most 400 characters), with the
document's URL, the accession number and the filing date, and the dollar figure
the code extracted from that sentence, labelled with the rule that found it and
the extraction's confidence. Where no figure can be extracted the record holds the
sentence and prints "guidance quoted, figure not extracted". No figure is ever
stored without its sentence. No press report, transcript site or analyst note is
a source, and an earnings call is not a filing.

THE SOURCE, EDGAR ONLY (the sources rule of 16 Oct 2026; the probe of 24 Oct is in
docs/briefs/a66-capex-guidance-notes.md). For each filer:
  1. https://data.sec.gov/submissions/CIK##########.json -- its recent filings;
     the newest 10-Q or 10-K (`form`, `accessionNumber`, `filingDate`,
     `reportDate`, `acceptanceDateTime`, `primaryDocument`);
  2. when its accession is not the one already stored, the primary document,
     https://www.sec.gov/Archives/edgar/data/<cik>/<accession, no dashes>/<doc>.
One request each, a pause of `pause_seconds` (1 s) between requests -- a tenth of
EDGAR's 10-a-second fair-access ceiling -- and the contact User-Agent
(edgar.user_agent(), CHESTER_SEC_CONTACT) on every one. Without the contact the
run is PENDING and asks nothing. A refusal (any 4xx) or a failure makes that filer
STALE with its reason; it is never retried around.

THE READ. The document's text, its MD&A section (Item 2 of a 10-Q, Item 7 of a
10-K; the whole document when the section is not located, and the record says
so), split into sentences; a sentence is kept when it holds a capex term (the
common one, or the filer's own) and a forward marker ("expect", "anticipate",
"plan", "intend", or a fiscal year named that is still ahead of the filing date).

THE EXTRACTION (config `rules`, session-set): "$X to $Y billion" and its forms
give the midpoint, labelled "midpoint of range"; "approximately $X billion" is
labelled "approximately"; any other "$X billion" is "stated". Confidence is high
when the sentence yields exactly one figure and names exactly one fiscal year, low
otherwise.

STORED, both observed_at = the filing date and available_at = the filing's
acceptance instant (the vintage is the filing's), instrument none:
  edgar.capex_guidance.<ticker>         the filing's guidance figure, US dollars in
                                        billions (B) -- its primary sentence's: high
                                        confidence first, then the furthest fiscal
                                        year ahead. Written only beside its record.
  edgar.capex_guidance_record.<ticker>  the record, JSON: company, form, accession,
                                        filing date, period, URL, section, and every
                                        kept sentence with what was extracted from it.
                                        A filing with no guidance sentence still
                                        writes its record (no sentence), so the next
                                        pull knows it was read.
The guided fiscal year is the record's, not the key's: two vintages compare only
when they guide the same year.

Report only. Read by item 63's capex-chain line, item 26's revisions line and the
Quarterly's question; no flag, tell, dial, book or decision reads it.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional

import yaml

from .. import observations, session
from . import _publication as pub
from . import edgar
from ._base import FetchError, http_get_bytes

log = logging.getLogger(__name__)

SOURCE = "edgar_guidance"
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "edgar_guidance.yaml"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
DOC_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
FIGURE_KEY = "edgar.capex_guidance.{t}"
RECORD_KEY = "edgar.capex_guidance_record.{t}"


def config(path: Optional[Path] = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def tickers(cfg: Optional[dict] = None) -> list[str]:
    return [f["ticker"] for f in (cfg or config()).get("filers") or []]


def figure_key(ticker: str) -> str:
    return FIGURE_KEY.format(t=ticker.lower())


def record_key(ticker: str) -> str:
    return RECORD_KEY.format(t=ticker.lower())


def keys(cfg: Optional[dict] = None) -> list[str]:
    out = []
    for t in tickers(cfg):
        out += [figure_key(t), record_key(t)]
    return out


# ---------------------------------------------------------------------------
# The filing index
# ---------------------------------------------------------------------------
def latest_filing(sub: dict, forms: list[str], cik: int) -> Optional[dict]:
    """The newest filing of one of `forms` in a submissions JSON, with its
    primary document's URL; None when there is none."""
    rec = ((sub or {}).get("filings") or {}).get("recent") or {}
    n = len(rec.get("form") or [])
    best = None
    for i in range(n):
        if rec["form"][i] not in forms:
            continue
        f = {k: (rec.get(k) or [None] * n)[i] for k in
             ("form", "accessionNumber", "filingDate", "reportDate",
              "acceptanceDateTime", "primaryDocument")}
        if best is None or str(f["filingDate"]) > str(best["filingDate"]):
            best = f
    if not best or not best.get("primaryDocument"):
        return None
    best["url"] = DOC_URL.format(cik=int(cik), acc=str(best["accessionNumber"]).replace("-", ""),
                                 doc=best["primaryDocument"])
    return best


def acceptance_instant(f: dict) -> str:
    """The instant the filing became public, UTC ISO; the filing date's end in ET
    when EDGAR gives no acceptance time."""
    raw = str(f.get("acceptanceDateTime") or "")
    try:
        t = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=dt.timezone.utc)
        return t.astimezone(dt.timezone.utc).isoformat(timespec="seconds")
    except ValueError:
        d = dt.date.fromisoformat(str(f["filingDate"])[:10])
        et = session.to_eastern(dt.datetime(d.year, d.month, d.day, 23, 59,
                                            tzinfo=dt.timezone.utc)).tzinfo
        return (dt.datetime(d.year, d.month, d.day, 23, 59, tzinfo=et)
                .astimezone(dt.timezone.utc).isoformat(timespec="seconds"))


# ---------------------------------------------------------------------------
# The document's text, the section, the sentences
# ---------------------------------------------------------------------------
_DROP = re.compile(r"<(script|style|head)\b.*?</\1\s*>", re.I | re.S)
_TAG = re.compile(r"<[^>]+>")
_BLOCK = re.compile(r"</?(p|div|br|tr|td|li|h[1-6]|table)\b[^>]*>", re.I)


def html_text(raw: bytes) -> str:
    """The document's visible text, one space between words, block ends kept as
    sentence boundaries."""
    s = raw.decode("utf-8", errors="replace")
    s = _DROP.sub(" ", s)
    s = _BLOCK.sub(" \n ", s)
    s = _TAG.sub(" ", s)
    s = html.unescape(s).replace("\xa0", " ").replace("​", "")
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    return re.sub(r"\s*\n\s*", "\n", s).strip()


def mdna(text: str, cfg: dict) -> tuple[str, bool]:
    """(the MD&A section, located). Of the headings' matches the longest span to
    the next end heading is the section -- the table of contents repeats both."""
    starts = [m.start() for m in re.finditer(cfg["mdna_start"], text, re.I)]
    best = ""
    for s in starts:
        m = re.compile(cfg["mdna_end"], re.I).search(text, s + 1)
        span = text[s:m.start() if m else len(text)]
        if len(span) > len(best):
            best = span
    return (best, True) if len(best) > 2000 else (text, False)


_SPLIT = re.compile(r"(?<=[.;])\s+(?=[A-Z(“\"])|\n+")


def sentences(text: str) -> list[str]:
    return [" ".join(s.split()) for s in _SPLIT.split(text) if s and s.strip()]


def fy_end(year: int, month: int) -> dt.date:
    nxt = dt.date(year + (month == 12), month % 12 + 1, 1)
    return nxt - dt.timedelta(days=1)


def years_named(sentence: str, cfg: dict) -> list[int]:
    out = []
    for m in re.finditer(cfg["year_pattern"], sentence, re.I):
        y = int(m.group(1))
        if y not in out:
            out.append(y)
    return out


def is_guidance(sentence: str, filer: dict, filing_date: str, cfg: dict) -> bool:
    low = sentence.lower()
    terms = [t.lower() for t in (cfg.get("capex_terms") or []) + (filer.get("terms") or [])]
    if not any(t in low for t in terms):
        return False
    if any(re.search(rf"\b{re.escape(m)}", low) for m in cfg.get("forward_markers") or []):
        return True
    fd = dt.date.fromisoformat(filing_date[:10])
    return any(fy_end(int(m.group(1)), int(filer.get("fy_end_month", 12))) > fd
               for m in re.finditer(cfg["fy_marker_pattern"], sentence, re.I))


def clip(sentence: str, filer: dict, cfg: dict) -> tuple[str, bool]:
    """The sentence verbatim, or the max_chars window around its capex term."""
    cap = int(cfg.get("max_chars", 400))
    if len(sentence) <= cap:
        return sentence, False
    low = sentence.lower()
    terms = [t.lower() for t in (cfg.get("capex_terms") or []) + (filer.get("terms") or [])]
    at = min((low.find(t) for t in terms if t in low), default=0)
    start = max(0, min(at - cap // 3, len(sentence) - cap))
    return sentence[start:start + cap], True


def find_guidance(text: str, filer: dict, filing_date: str, cfg: dict) -> list[dict]:
    out = []
    for s in sentences(text):
        if is_guidance(s, filer, filing_date, cfg):
            t, cut = clip(s, filer, cfg)
            out.append({"sentence": t, "truncated": cut})
    return out


# ---------------------------------------------------------------------------
# The extraction
# ---------------------------------------------------------------------------
def extract(sentence: str, filer: dict, filing_date: str, cfg: dict) -> dict:
    """The figure (US$ bn) and the fiscal year a sentence guides, by the config's
    rules in order; a span one rule consumed is not read again by the next."""
    found, used = [], []
    for r in cfg.get("rules") or []:
        for m in re.finditer(r["pattern"], sentence, re.I):
            if any(m.start() < b and a < m.end() for a, b in used):
                continue
            used.append((m.start(), m.end()))
            nums = [float(g) for g in m.groups() if g is not None]
            if r["id"] == "range" and len(nums) == 2:
                lo, hi = sorted(nums)
                found.append({"figure_bn": round((lo + hi) / 2, 3), "low_bn": lo,
                              "high_bn": hi, "rule": r["id"], "label": r["label"],
                              "at": m.start()})
            elif nums:
                found.append({"figure_bn": nums[0], "rule": r["id"], "label": r["label"],
                              "at": m.start()})
    found.sort(key=lambda x: x["at"])
    years = years_named(sentence, cfg)
    fd = dt.date.fromisoformat(filing_date[:10])
    ahead = [y for y in years if fy_end(y, int(filer.get("fy_end_month", 12))) > fd]
    if not found:
        return {"figure_bn": None, "text": cfg.get("no_figure_text"),
                "fiscal_year": (ahead or years or [None])[0], "confidence": None}
    out = {k: v for k, v in found[0].items() if k != "at"}
    out["fiscal_year"] = (ahead or years or [None])[0]
    out["confidence"] = "high" if len(found) == 1 and len(years) == 1 else "low"
    out["figures_found"] = len(found)
    return out


def primary(items: list[dict]) -> Optional[int]:
    """The index of the sentence whose figure the key carries: high confidence
    first, then the furthest fiscal year, then the first."""
    cand = [(i, x) for i, x in enumerate(items) if x.get("figure_bn") is not None]
    if not cand:
        return None
    cand.sort(key=lambda p: (p[1].get("confidence") != "high",
                             -(p[1].get("fiscal_year") or 0), p[0]))
    return cand[0][0]


def record_for(filer: dict, f: dict, text: str, cfg: dict) -> dict:
    sec, located = mdna(text, cfg)
    items = []
    for g in find_guidance(sec, filer, f["filingDate"], cfg):
        items.append({**g, **extract(g["sentence"], filer, f["filingDate"], cfg)})
    p = primary(items)
    return {"company": filer["ticker"], "cik": int(filer["cik"]), "form": f["form"],
            "accession": f["accessionNumber"], "filing_date": f["filingDate"],
            "period": f.get("reportDate"), "url": f["url"],
            "section": "MD&A" if located else "whole document (MD&A not located)",
            "sentences": items, "primary": p,
            "note": None if items else "no guidance sentence in the filing"}


def rows_for(rec: dict, available: str) -> list[dict]:
    """The record row, and the figure row beside it when the record has a figure."""
    t = rec["company"]
    out = [{"registry_key": record_key(t), "instrument": None,
            "observed_at": rec["filing_date"], "available_at": available,
            "value": json.dumps(rec, sort_keys=True), "availability_kind": "observed"}]
    if rec.get("primary") is not None:
        fig = rec["sentences"][rec["primary"]]["figure_bn"]
        out.append({"registry_key": figure_key(t), "instrument": None,
                    "observed_at": rec["filing_date"], "available_at": available,
                    "value": float(fig), "availability_kind": "observed"})
    return out


# ---------------------------------------------------------------------------
# The pull
# ---------------------------------------------------------------------------
def stored_accession(st, ticker: str) -> Optional[str]:
    rows = st.as_of(record_key(ticker))
    if not rows:
        return None
    try:
        return json.loads(rows[-1]["value_text"]).get("accession")
    except (TypeError, ValueError):
        return None


def collect(fetch: Callable[[str], bytes], cfg: dict, stored: dict,
            sleep: Callable[[float], None] = time.sleep) -> tuple[list[dict], dict]:
    """(rows, summary). `fetch(url)` makes one request and raises on any failure;
    a filer whose request fails is STALE with its reason and is not retried."""
    pause = float(cfg.get("pause_seconds", 1.0))
    rows: list[dict] = []
    summary: dict[str, Any] = {"read": {}, "unchanged": [], "stale": {}, "requests": 0}
    first = True

    def get(url: str) -> bytes:
        nonlocal first
        if not first:
            sleep(pause)
        first = False
        summary["requests"] += 1
        return fetch(url)
    for filer in cfg.get("filers") or []:
        t = filer["ticker"]
        try:
            sub = json.loads(get(SUBMISSIONS_URL.format(cik=int(filer["cik"]))))
            f = latest_filing(sub, list(cfg.get("forms") or []), filer["cik"])
            if not f:
                summary["stale"][t] = "no 10-Q or 10-K in the recent filings"
                continue
            if f["accessionNumber"] == stored.get(t):
                summary["unchanged"].append(t)
                continue
            rec = record_for(filer, f, html_text(get(f["url"])), cfg)
        except Exception as exc:                              # noqa: BLE001
            summary["stale"][t] = f"{type(exc).__name__}: {exc}"[:300]
            continue
        rows += rows_for(rec, acceptance_instant(f))
        summary["read"][t] = {"form": rec["form"], "filing_date": rec["filing_date"],
                              "sentences": len(rec["sentences"]),
                              "figure": rows[-1]["value"] if rec.get("primary") is not None
                              else None}
    return rows, summary


def edgar_fetch(ua: str) -> Callable[[str], bytes]:
    """One GET with the contact User-Agent; a 4xx raises at once and nothing is
    retried (max_retries 1)."""
    def fetch(url: str) -> bytes:
        return http_get_bytes(url, headers={"User-Agent": ua}, max_retries=1)
    return fetch


def pull(run_id: Optional[str] = None, db=None,
         fetch: Optional[Callable[[str], bytes]] = None,
         sleep: Callable[[float], None] = time.sleep) -> dict:
    ua = edgar.user_agent()
    if not ua:
        return pub.pending(SOURCE, f"not configured: {edgar.CONTACT_VAR} is unset, "
                           f"and EDGAR serves no request without a contact", run_id)
    cfg = config()
    run_id = run_id or session.new_run_id(SOURCE)
    own = db is None
    store = db or observations.open_writer(__name__)
    try:
        stored = {t: stored_accession(store, t) for t in tickers(cfg)}
        rows, summary = collect(fetch or edgar_fetch(ua), cfg, stored, sleep=sleep)
        if rows:
            res = pub.write_rows(SOURCE, rows, keys(cfg), run_id, db=store)
        elif summary["stale"] and not summary["unchanged"]:
            res = pub.stale(SOURCE, keys(cfg), "; ".join(
                f"{t}: {r}" for t, r in summary["stale"].items()), db=store, run_id=run_id)
        else:
            res = {"source": SOURCE, "status": pub.OK, "written": 0, "run_id": run_id,
                   "session": session.session_date(),
                   "reason": "no filing since the stored one"}
    finally:
        if own:
            store.close()
    res.update({"filers": summary, "stale_filers": summary["stale"]})
    return res


# ---------------------------------------------------------------------------
# The readers: item 63's line, item 26's revisions, the Quarterly
# ---------------------------------------------------------------------------
def records(st, ticker: str, cutoff: Optional[str] = None) -> list[dict]:
    """Every stored record knowable at the cutoff, oldest first."""
    out = []
    for r in st.as_of(record_key(ticker), cutoff):
        try:
            out.append(json.loads(r["value_text"]))
        except (TypeError, ValueError):
            continue
    return out


def headline(rec: dict) -> Optional[dict]:
    p = rec.get("primary")
    return None if p is None else rec["sentences"][p]


def _date(iso: str) -> str:
    d = dt.date.fromisoformat(str(iso)[:10])
    return f"{d.day} {d:%b %Y}"


def guidance_line(st, cutoff: Optional[str], names: list[str],
                  cfg: Optional[dict] = None) -> dict:
    """{"lines", "footnotes"}: per name, the newest filing's guidance -- "guidance
    for FY2027: $X bn (midpoint of range, high confidence), from the 10-Q of
    <date>" -- or what the record holds instead; each URL in the footnotes."""
    parts, notes = [], []
    for t in names:
        recs = records(st, t, cutoff)
        if not recs:
            parts.append(f"{t} not stored")
            continue
        rec = recs[-1]
        h = headline(rec)
        notes.append(f"{t}: {rec['form']} filed {_date(rec['filing_date'])}, "
                     f"accession {rec['accession']}, {rec['url']}")
        if h:
            fy = f"FY{h['fiscal_year']}" if h.get("fiscal_year") else "an unnamed year"
            parts.append(f"{t} guidance for {fy}: ${h['figure_bn']:g} bn ({h['label']}, "
                         f"{h['confidence']} confidence), from the {rec['form']} of "
                         f"{_date(rec['filing_date'])}")
        elif rec["sentences"]:
            parts.append(f"{t}: {(cfg or config()).get('no_figure_text')} "
                         f"({rec['form']} of {_date(rec['filing_date'])})")
        else:
            parts.append(f"{t}: no guidance sentence in the {rec['form']} of "
                         f"{_date(rec['filing_date'])}")
    return {"lines": parts, "footnotes": notes}


def revisions(st, cutoff: Optional[str], names: list[str]) -> list[dict]:
    """Item 26: per name, the change in guidance between its two newest filings,
    where both carry a figure for the same fiscal year; otherwise why not."""
    out = []
    for t in names:
        recs = records(st, t, cutoff)
        row: dict[str, Any] = {"ticker": t}
        if len(recs) < 2:
            row["reason"] = f"{len(recs)} filing{'s' if len(recs) != 1 else ''} stored; two needed"
        else:
            a, b = recs[-2], recs[-1]
            ha, hb = headline(a), headline(b)
            row.update({"from": a["filing_date"], "to": b["filing_date"],
                        "from_form": a["form"], "to_form": b["form"]})
            if not (ha and hb):
                row["reason"] = "a figure was not extracted from both filings"
            elif ha.get("fiscal_year") != hb.get("fiscal_year"):
                row["reason"] = (f"not comparable: FY{ha.get('fiscal_year')} then "
                                 f"FY{hb.get('fiscal_year')}")
            else:
                row.update({"fiscal_year": hb["fiscal_year"], "from_bn": ha["figure_bn"],
                            "to_bn": hb["figure_bn"],
                            "change_bn": round(hb["figure_bn"] - ha["figure_bn"], 3),
                            "change_pct": round((hb["figure_bn"] / ha["figure_bn"] - 1) * 100, 1)
                            if ha["figure_bn"] else None})
        out.append(row)
    return out


def revision_text(r: dict) -> str:
    if r.get("reason"):
        return f"{r['ticker']}: {r['reason']}"
    word = "raised" if r["change_bn"] > 0 else "cut" if r["change_bn"] < 0 else "held"
    pct = f", {r['change_pct']:+.1f}%" if r.get("change_pct") is not None else ""
    return (f"{r['ticker']} {word} FY{r['fiscal_year']} guidance from ${r['from_bn']:g} bn "
            f"({r['from_form']} of {_date(r['from'])}) to ${r['to_bn']:g} bn "
            f"({r['to_form']} of {_date(r['to'])}{pct})")


def _main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if argv[:1] == ["dry-run"]:
        # The first pull's rehearsal: the same requests, every record printed,
        # nothing written.
        ua = edgar.user_agent()
        if not ua:
            print(f"PENDING: {edgar.CONTACT_VAR} is unset; nothing asked")
            return 0
        cfg = config()
        with observations.ObservationStore() as st:
            stored = {t: stored_accession(st, t) for t in tickers(cfg)}
        rows, summary = collect(edgar_fetch(ua), cfg, stored)
        for r in rows:
            if r["registry_key"].startswith("edgar.capex_guidance_record."):
                rec = json.loads(r["value"])
                print(f"{rec['company']} {rec['form']} {rec['filing_date']} "
                      f"{rec['accession']} {rec['url']} [{rec['section']}]")
                for s in rec["sentences"] or [{"sentence": rec.get("note")}]:
                    fig = (f"{s['figure_bn']:g} bn FY{s.get('fiscal_year')} "
                           f"({s.get('label')}, {s.get('confidence')})"
                           if s.get("figure_bn") is not None else s.get("text") or "")
                    print(f"  \"{s['sentence']}\"\n    -> {fig}")
        print(json.dumps({"would_write": len(rows), **summary}, indent=2, default=str))
        print("dry run: nothing written")
        return 0
    if argv[:1] == ["show"]:
        with observations.ObservationStore() as st:
            g = guidance_line(st, None, tickers())
            for ln in g["lines"] + g["footnotes"]:
                print(ln)
            for r in revisions(st, None, tickers()):
                print(revision_text(r))
        return 0
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
