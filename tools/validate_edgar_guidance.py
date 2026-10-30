#!/usr/bin/env python3
"""
Validation gate: the hyperscalers' capex guidance from their own filings (A66;
signal-triage items 26 and 63; altdata/sources/edgar_guidance.py). Synthetic
fixtures only: no network, no live store, no model.

  A  THE SENTENCE FINDER on a fixture 10-Q: the MD&A section found past its
     table-of-contents entry; a forward-looking capex sentence kept, a past one,
     a sentence outside the MD&A and a forward sentence without a capex term
     not; the filer's own term; a fiscal year still ahead counts as a marker; the
     400-character cap.
  B  EACH EXTRACTION RULE BY HAND: a range's midpoint labelled "midpoint of
     range" (four phrasings), "approximately", "stated"; the fiscal year; the
     confidence high only for one figure and one year; "guidance quoted, figure
     not extracted" where no figure is found; millions are not read.
  C  THE PULL against a fake EDGAR: the contact User-Agent required (PENDING and
     no request without it) and sent on every request; one request per document
     and a one-second pause between requests; the figure stored only beside its
     record, at the filing date, vintage the acceptance instant; an unchanged
     accession asks for no document; a refusal is STALE with its reason and is
     never retried.
  D  WHERE IT PRINTS: item 63's capex-chain line beside filed capex, the URL in
     its notes; item 26's revisions between consecutive filings of the same
     fiscal year (and "not comparable" across years); the Quarterly's question
     reads the same keys.
  E  THE CONTRACT: every key registered, under source edgar_guidance, units
     usd_bn and label; the publication-lag family quoting the SEC's own 10-Q and
     10-K deadlines, its lag within its bound; no person's name in the reader,
     its config or this gate.

    python tools/validate_edgar_guidance.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

TD = Path(gate_mkdtemp("edgar_guidance_"))
LINE = "=" * 78
PASS = FAIL = 0


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


META = {"ticker": "META", "cik": 1326801, "fy_end_month": 12,
        "terms": ["capital expenditures, including principal payments on finance leases"]}
MSFT = {"ticker": "MSFT", "cik": 789019, "fy_end_month": 6, "terms": ["property and equipment"]}

FWD = ("We anticipate our full year 2026 capital expenditures, including principal "
       "payments on finance leases, will be in the range of $70 billion to $72 billion.")
PAST = "Capital expenditures were $19.4 billion for the three months ended September 30, 2026."
NOCAPEX = "We expect revenue growth to moderate in the fourth quarter of 2026."
OUTSIDE = "We expect capital expenditures of approximately $99 billion in 2027."

DOC = f"""<html><head><title>10-Q</title><style>p {{color: red}}</style></head><body>
<p>TABLE OF CONTENTS</p>
<p>Item 2. Management&#8217;s Discussion and Analysis of Financial Condition and Results of Operations 25</p>
<p>Item 3. Quantitative and Qualitative Disclosures About Market Risk 40</p>
<p>Item 1A. Risk Factors.</p><p>{OUTSIDE}</p>
<p>Item 2. Management&#8217;s Discussion and Analysis of Financial Condition and Results of Operations</p>
<p>{'Our business is described in the annual report. ' * 50}</p>
<p>{PAST} {FWD}</p>
<p>{NOCAPEX}</p>
<p>Item 3. Quantitative and Qualitative Disclosures About Market Risk</p>
<p>We are exposed to market risks.</p>
</body></html>"""


def group_a(cfg: dict) -> None:
    from altdata.sources import edgar_guidance as eg
    head("A. THE SENTENCE FINDER")
    text = eg.html_text(DOC.encode())
    sec, located = eg.mdna(text, cfg)
    check(located and FWD in sec and OUTSIDE not in sec and "market risks" not in sec,
          "the MD&A is the span past its table-of-contents entry, to Item 3")
    got = [g["sentence"] for g in eg.find_guidance(sec, META, "2026-10-22", cfg)]
    check(got == [FWD], f"kept: the forward capex sentence only -- not the past one, not "
                        f"the forward sentence without a capex term ({got})")
    check(eg.is_guidance(FWD, META, "2026-10-22", cfg)
          and not eg.is_guidance(PAST, META, "2026-10-22", cfg)
          and not eg.is_guidance(NOCAPEX, META, "2026-10-22", cfg),
          "positive and negative fixtures, one by one")
    own = "Purchases of property and equipment in fiscal 2027 are expected to increase."
    check(eg.is_guidance(own, MSFT, "2026-10-22", cfg)
          and not eg.is_guidance(own, META, "2026-10-22", cfg),
          "the filer's own term counts for that filer only")
    ahead = "Capital expenditures for fiscal year 2027 will exceed those of fiscal 2026."
    behind = "Capital expenditures for fiscal year 2026 were $64.6 billion."
    check(eg.is_guidance(ahead, MSFT, "2026-10-22", cfg)
          and not eg.is_guidance(behind, MSFT, "2026-10-22", cfg),
          "a fiscal year still ahead of the filing date is a marker (Microsoft's FY2027 "
          "ends June 2027); one already ended is not")
    long = ("We expect capital expenditures to increase " + "substantially " * 60
            + "next year.")
    clipped, cut = eg.clip(long, META, cfg)
    check(cut and len(clipped) == 400 and "capital expenditures" in clipped,
          "a sentence over 400 characters is stored as the 400-character window around "
          "its capex term, marked truncated")
    whole, loc = eg.mdna("We expect capital expenditures of $5 billion in 2027.", cfg)
    check(not loc, "no MD&A heading: the whole document is read, and the record says so")


def group_b(cfg: dict) -> None:
    from altdata.sources import edgar_guidance as eg
    head("B. THE EXTRACTION RULES, BY HAND")
    cases = [
        (FWD, 71.0, "range", "midpoint of range", 2026, "high"),
        ("We expect 2027 capital expenditures to be between $100 and $120 billion.",
         110.0, "range", "midpoint of range", 2027, "high"),
        ("We expect capital expenditures in 2027 of $90-$95 billion.", 92.5, "range",
         "midpoint of range", 2027, "high"),
        ("We plan capital expenditures of $80 to $84 billion in 2027.", 82.0, "range",
         "midpoint of range", 2027, "high"),
        ("We expect capital expenditures of approximately $25 billion in fiscal 2027.",
         25.0, "approximate", "approximately", 2027, "high"),
        ("We anticipate capital expenditures of $40 billion in 2027.", 40.0, "stated",
         "stated", 2027, "high"),
        ("We expect capital expenditures of $40 billion in 2027 and $50 billion in 2028.",
         40.0, "stated", "stated", 2027, "low"),
        ("We expect capital expenditures of approximately $30 billion.", 30.0,
         "approximate", "approximately", None, "low"),
    ]
    for s, fig, rule, label, fy, conf in cases:
        x = eg.extract(s, META, "2026-10-22", cfg)
        check(x["figure_bn"] == fig and x["rule"] == rule and x["label"] == label
              and x["fiscal_year"] == fy and x["confidence"] == conf,
              f"{s[:60]}... -> {fig} bn, {label}, FY{fy}, {conf} ({x})")
    rng = eg.extract(FWD, META, "2026-10-22", cfg)
    check(rng["low_bn"] == 70.0 and rng["high_bn"] == 72.0
          and rng["figure_bn"] == (70.0 + 72.0) / 2,
          "the range keeps both ends; the figure is their midpoint, by hand 71")
    none = eg.extract("We expect capital expenditures to increase significantly in 2027.",
                      META, "2026-10-22", cfg)
    check(none["figure_bn"] is None and none["text"] == "guidance quoted, figure not extracted"
          and none["fiscal_year"] == 2027,
          "no figure: \"guidance quoted, figure not extracted\", the year still read")
    mil = eg.extract("We expect capital expenditures of $500 million in 2027.", META,
                     "2026-10-22", cfg)
    check(mil["figure_bn"] is None, "a figure in millions is not read as guidance")


class FakeEdgar:
    def __init__(self, filings: dict, docs: dict, refuse: set = frozenset()):
        self.filings, self.docs, self.refuse = filings, docs, set(refuse)
        self.asked: list[str] = []

    def __call__(self, url: str) -> bytes:
        from altdata.sources._base import FetchError
        self.asked.append(url)
        if any(r in url for r in self.refuse):
            raise FetchError(f"HTTP 403 from {url}: refused")
        for cik, sub in self.filings.items():
            if f"CIK{cik:010d}.json" in url:
                return json.dumps(sub).encode()
        if url in self.docs:
            return self.docs[url].encode()
        raise FetchError(f"HTTP 404 from {url}")


def submissions(form: str, acc: str, date: str, doc: str, accepted: str) -> dict:
    return {"filings": {"recent": {
        "form": ["8-K", form, "10-K"], "accessionNumber": ["0-0-1", acc, "0-0-2"],
        "filingDate": ["2026-10-23", date, "2026-01-29"],
        "reportDate": ["2026-10-23", "2026-09-30", "2025-12-31"],
        "acceptanceDateTime": ["2026-10-23T16:05:00.000Z", accepted,
                               "2026-01-29T21:00:00.000Z"],
        "primaryDocument": ["x8k.htm", doc, "x10k.htm"]}}}


def two_filer_cfg(cfg: dict) -> dict:
    return {**cfg, "filers": [META, MSFT]}


def group_c(cfg: dict) -> None:
    from unittest import mock
    from altdata import observations
    from altdata.sources import _publication as pub, edgar, edgar_guidance as eg
    head("C. THE PULL, AGAINST A FAKE EDGAR")
    c2 = two_filer_cfg(cfg)
    murl = eg.DOC_URL.format(cik=1326801, acc="000132680126000099", doc="meta-10q.htm")
    msub = submissions("10-Q", "0001326801-26-000099", "2026-10-22", "meta-10q.htm",
                       "2026-10-22T20:10:00.000Z")
    fake = FakeEdgar({1326801: msub}, {murl: DOC}, refuse={"CIK0000789019"})
    sleeps: list[float] = []
    with mock.patch.object(edgar, "user_agent", lambda: None):
        res = eg.pull(fetch=fake, sleep=sleeps.append)
    check(res["status"] == pub.PENDING and "CHESTER_SEC_CONTACT" in res["reason"]
          and not fake.asked, "no contact: PENDING, the variable named, nothing asked")
    sent = []

    def capture(url, headers=None, max_retries=None, **k):
        sent.append((headers or {}).get("User-Agent"))
        assert max_retries == 1
        return b"{}"
    with mock.patch.object(eg, "http_get_bytes", capture):
        eg.edgar_fetch("chester-reports/1.0 (contact)")(murl)
    check(sent == ["chester-reports/1.0 (contact)"],
          "every request carries the contact User-Agent, with max_retries 1 (no retry)")
    db = str(TD / "pull.db")
    with observations.ObservationStore(db) as st, \
            mock.patch.object(edgar, "user_agent", lambda: "chester-reports/1.0 (c)"), \
            mock.patch.object(eg, "config", lambda path=None: c2):
        res = eg.pull(db=st, fetch=fake, sleep=sleeps.append)
        rec = st.as_of(eg.record_key("META"))
        fig = st.as_of(eg.figure_key("META"))
    check(fake.asked == [eg.SUBMISSIONS_URL.format(cik=1326801), murl,
                         eg.SUBMISSIONS_URL.format(cik=789019)],
          f"one request for the index and one for the document; the refused filer asked "
          f"once ({len(fake.asked)} requests)")
    check(sleeps == [1.0, 1.0], f"a one-second pause between requests ({sleeps})")
    r = json.loads(rec[0]["value_text"]) if rec else {}
    check(res["status"] == pub.OK and len(fig) == 1 and fig[0]["value_num"] == 71.0
          and fig[0]["observed_at"][:10] == "2026-10-22"
          and fig[0]["available_at"].startswith("2026-10-22T20:10:00")
          and r.get("accession") == "0001326801-26-000099" and r.get("url") == murl
          and r["sentences"][r["primary"]]["sentence"] == FWD,
          "the figure (71 bn) is stored beside its record -- sentence verbatim, URL, "
          "accession, filing date -- at the filing date, vintage the acceptance instant")
    check("MSFT" in res["stale_filers"] and "403" in res["stale_filers"]["MSFT"],
          f"a refusal is STALE for that filer with its reason ({res['stale_filers']})")
    fake.asked.clear()
    with observations.ObservationStore(db) as st, \
            mock.patch.object(edgar, "user_agent", lambda: "chester-reports/1.0 (c)"), \
            mock.patch.object(eg, "config", lambda path=None: c2):
        res2 = eg.pull(db=st, fetch=fake, sleep=sleeps.append)
    check(murl not in fake.asked and "META" in res2["filers"]["unchanged"],
          "the same accession again: the index only, no document")
    nofig = DOC.replace(FWD, "We expect capital expenditures to increase meaningfully in 2027.")
    f3 = FakeEdgar({1326801: msub}, {murl: nofig})
    db3 = str(TD / "nofig.db")
    with observations.ObservationStore(db3) as st, \
            mock.patch.object(edgar, "user_agent", lambda: "chester-reports/1.0 (c)"), \
            mock.patch.object(eg, "config", lambda path=None: {**cfg, "filers": [META]}):
        eg.pull(db=st, fetch=f3, sleep=lambda s: None)
        rec3, fig3 = st.as_of(eg.record_key("META")), st.as_of(eg.figure_key("META"))
    r3 = json.loads(rec3[0]["value_text"])
    check(not fig3 and r3["sentences"][0]["text"] == "guidance quoted, figure not extracted",
          "no figure extracted: the record holds the sentence, no figure is stored")
    f4 = FakeEdgar({}, {}, refuse={"CIK"})
    with observations.ObservationStore(str(TD / "stale.db")) as st, \
            mock.patch.object(edgar, "user_agent", lambda: "chester-reports/1.0 (c)"), \
            mock.patch.object(eg, "config", lambda path=None: {**cfg, "filers": [META]}):
        r4 = eg.pull(db=st, fetch=f4, sleep=lambda s: None)
    check(r4["status"] == pub.STALE and "403" in r4["reason"] and len(f4.asked) == 1,
          "every filer refused: STALE with the reason, one request, never retried")


def group_d(cfg: dict) -> None:
    from altdata import capex_chain as cc, observations, batch5
    from altdata.sources import edgar_guidance as eg
    head("D. WHERE IT PRINTS")
    db = str(TD / "prints.db")
    rec_a = {"company": "META", "cik": 1326801, "form": "10-Q", "accession": "A1",
             "filing_date": "2026-07-30", "period": "2026-06-30", "url": "https://x/a",
             "section": "MD&A", "primary": 0,
             "sentences": [{"sentence": "s1", "figure_bn": 68.0, "fiscal_year": 2026,
                            "label": "midpoint of range", "confidence": "high", "rule": "range"}]}
    rec_b = dict(rec_a, accession="A2", filing_date="2026-10-22", url="https://x/b",
                 sentences=[dict(rec_a["sentences"][0], figure_bn=71.0)])
    rec_c = dict(rec_a, company="MSFT", accession="M1", filing_date="2026-07-29",
                 sentences=[dict(rec_a["sentences"][0], fiscal_year=2026, figure_bn=80.0)])
    rec_d = dict(rec_c, accession="M2", filing_date="2026-10-21",
                 sentences=[dict(rec_a["sentences"][0], fiscal_year=2027, figure_bn=95.0)])
    with observations.ObservationStore(db) as st:
        for rec, at in ((rec_a, "2026-07-30T20:00:00+00:00"), (rec_b, "2026-10-22T20:00:00+00:00"),
                        (rec_c, "2026-07-29T20:00:00+00:00"), (rec_d, "2026-10-21T20:00:00+00:00")):
            st.write_many([dict(r, source="edgar_guidance") for r in eg.rows_for(rec, at)])
        r = cc.relative(st, "2026-10-24T12:00:00+00:00")
        lines, notes = cc.relative_lines(r), cc.relative_notes(r)
        rv = batch5.capex_guidance_revisions(st, "2026-10-24T12:00:00+00:00")
        before = batch5.capex_guidance_revisions(st, "2026-10-01T12:00:00+00:00")
    g = next((x for x in lines if "guidance from the filings" in x), "")
    check("META guidance for FY2026: $71 bn (midpoint of range, high confidence), from "
          "the 10-Q of 22 Oct 2026" in g and "AMZN not stored" in g
          and any("filed capex" in x for x in lines),
          f"item 63: the guidance beside the filed capex ({g[:160]})")
    check(any("https://x/b" in n and "accession A2" in n for n in notes)
          and not any("https://" in x for x in lines),
          "the URL and accession are in the notes, not the line")
    meta = next(x for x in rv["rows"] if x["ticker"] == "META")
    msft = next(x for x in rv["rows"] if x["ticker"] == "MSFT")
    check(meta.get("change_bn") == 3.0 and meta.get("fiscal_year") == 2026
          and "META raised FY2026 guidance from $68 bn" in " ".join(rv["lines"]),
          f"item 26: META raised FY2026 by 3 bn between consecutive filings ({meta})")
    check(msft.get("reason") == "not comparable: FY2026 then FY2027",
          "a change across fiscal years is not a revision: \"not comparable\"")
    bm = next(x for x in before["rows"] if x["ticker"] == "META")
    check("1 filing stored" in (bm.get("reason") or ""),
          "as of 1 Oct only the July filing is knowable: no revision yet (point in time)")
    q = __import__("yaml").safe_load((REPO / "config" / "quarterly_chapters.yaml")
                                     .read_text(encoding="utf-8"))
    q7 = [x for f in (q.get("families") or q.get("chapters") or {}).values()
          if isinstance(f, dict) for x in f.get("ten_questions") or []
          if "capex guidance" in x["text"]]
    check(q7 and q7[0]["series"] == [eg.figure_key(t) for t in eg.tickers()],
          "the Quarterly's question 7 reads the five guidance keys")
    blk = (REPO / "daily_cascade" / "batch5_block.py").read_text(encoding="utf-8")
    check("capex_guidance_revisions" in blk,
          "item 26's revisions print beside the fiscal-bark flag")


def group_e(cfg: dict) -> None:
    from altdata import derived
    from altdata.sources import edgar_guidance as eg
    head("E. THE CONTRACT")
    keys = eg.keys(cfg)
    ents = {k: derived.registry_entry(k) for k in keys}
    check(len(keys) == 10 and all(e and e.get("source") == "edgar_guidance" for e in ents.values())
          and all(ents[eg.figure_key(t)]["units"] == "usd_bn"
                  and ents[eg.record_key(t)]["units"] == "label" for t in eg.tickers(cfg)),
          f"ten keys registered: five figures in usd_bn, five records as label ({len(keys)})")
    import yaml
    fam = next(f for f in yaml.safe_load((REPO / "config" / "publication_lags.yaml")
                                         .read_text(encoding="utf-8"))["families"]
               if f["id"] == "sec_periodic_filings")
    check("40 days after the end of the fiscal quarter" in fam["reason"]
          and "60 days" in fam["reason"] and fam["lag_sessions"] <= fam["max_lag"]
          and all(derived.publication_lag(ents[k], k)[1] == "sec_periodic_filings"
                  for k in keys),
          "the lag family quotes the SEC's 10-Q and 10-K deadlines, its lag within its "
          "bound, and every key matches it")
    check(derived.staleness_allowance_of(ents[keys[0]], keys[0])[0] == 95 + 14,
          "the allowance: quarterly 95 plus 14")
    files = [REPO / "altdata" / "sources" / "edgar_guidance.py",
             REPO / "config" / "edgar_guidance.yaml", Path(__file__)]
    hit = [f.name for f in files
           if re.search(r"\b(?:Mr|Ms|Mrs|Dr)\.\s+[A-Z]|\b(?:CEO|CFO|chief \w+ officer)\s+[A-Z][a-z]+",
                        f.read_text(encoding="utf-8"))]
    check(not hit, f"no person's name in the reader, its config or this gate ({hit})")
    src = files[0].read_text(encoding="utf-8")
    check("transcript" not in re.sub(r'""".*?"""', "", src, flags=re.S).lower()
          and "efts" not in src.split('"""', 2)[2],
          "the reader reads EDGAR's filings only: no transcript or search source in code")


def main() -> int:
    from altdata.sources import edgar_guidance as eg
    cfg = eg.config()
    for g in (group_a, group_b, group_c, group_d, group_e):
        try:
            g(cfg)
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"a group raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
