#!/usr/bin/env python3
"""
Validation gate for the readability pass on every stacked report. (T2.5)

    python tools/validate_readability.py

The ruling of 5 Oct 2026, eleven items, on a SYNTHETIC daily close and a
SYNTHETIC Weekly in temporary stores -- a code gate never reads the live store:

  A ONE FACT, ONCE (1)     no bullet list anywhere; at most six figures in any
                           paragraph, and a draft with more is withheld; an item
                           whose figures sit in its table does not print again
  B THE FIXED ORDER (2)    claim -> table(s) -> chart(s) -> one paragraph (at
                           most 120 words) -> footnote, in both reports
  C NO METHOD (3)          the six phrases are banned and none is in a body; one
                           footer line points to the Reader's Guide
  D NO SENTENCE TWICE (4)  a sentence repeating The read is withheld where it
                           repeats, with its reason; The read is asked to reword
  E EMPTY, ONE LINE (5)    an unchanged section prints its footnote alone and
                           makes no model call
  F FORMATTING (6)         plurals by count, "28 Sep" in prose, "±", the ET
                           header stamp, minutes, signed changes
  G HEADER, SUBJECT (7, 8) title, week, reading time and what changed in the
                           header; run metadata in the footer; the claim in the
                           subject
  H PREDICTION MARKETS (9) one table: item, Kalshi, Polymarket, change, note
  I STYLES (10)            the six element styles, the same in both reports;
                           at most six columns; legible at 400 px
  J PDF (11)               print CSS, attached and archived beside the HTML, at
                           most 5 MB; the fixture renders to PDF where WeasyPrint
                           is installed (CI and the box), and says NOT VALIDATED
                           on a laptop without its libraries
"""

from __future__ import annotations

import os
import re
import sys
from email import message_from_bytes
from email.policy import default as email_default
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gate_tmp import mkdtemp as gate_mkdtemp                   # noqa: E402

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


def chunks(html: str) -> list[str]:
    """The rendered sections, each from its <h2> to the next."""
    from daily_cascade import stack_render as sr
    parts = re.split(r'(?=<h2 style="' + re.escape(sr.SECTION) + '">)', html)
    return [p for p in parts if re.match(r'<h2[^>]*>\d+ &middot;', p)]


def body_text(html: str) -> str:
    """The visible text up to the glossary: what a reader reads as the report."""
    cut = html.find(">Glossary</h2>")
    h = html[:cut] if cut > 0 else html
    t = re.sub(r"<[^>]+>", " ", h)
    import html as _h
    return re.sub(r"\s+", " ", _h.unescape(t))


def weekly_fixture(td: str, replies: dict):
    import validate_weekly_stack as vws
    from altdata import config
    from daily_cascade import weekly_stack as ws
    config.COMPUTED_DIR = str(Path(td) / "computed")
    db = str(Path(td) / "weekly.db")
    arch = str(Path(td) / "reports")
    logp = Path(td) / "attention-log.md"
    logp.write_text("| date | kind | minutes | note |\n|---|---|---|---|\n"
                    "| 2026-09-30 | sitting | 22 | fixture sitting |\n"
                    "| 2026-10-01 | ruling | — | fixture ruling |\n", encoding="utf-8")
    seeded = vws.seed(db)
    p = dict(vws.payload(seeded), run_id="weekly-fixture")
    calls: list = []
    out = ws.produce(p, archive_dir=arch, client=client(replies, calls), db_path=db,
                     log_path=logp)
    return out, calls, (p, db, arch, logp)


def close_fixture(td: str, replies: dict):
    import validate_stack as vs
    from altdata import config
    from daily_cascade import stack_close
    config.COMPUTED_DIR = str(Path(td) / "computed_close")
    db = str(Path(td) / "close.db")
    seeded = vs.seed(db)
    p = vs.payload(seeded["market_state"])
    calls: list = []
    out = stack_close.produce(p, archive_dir=str(Path(td) / "close_reports"),
                              dry_run=True, client=client(replies, calls), db_path=db)
    return out, calls


class Resp:
    def __init__(self, t):
        import types
        self.content = [types.SimpleNamespace(type="text", text=t)]
        self.model = "fixture-model"
        self.stop_reason = "end_turn"


DEFAULT = ("The {p} left this section where it was. Nothing in the table moved "
           "far enough to change the picture.")


def client(replies: dict, calls: list):
    """A model that answers by section title (or READ); figure-free by default,
    so the numeral audit publishes it."""
    import types

    def create(**k):
        sysm = k["system"]
        calls.append(sysm)
        for title, text in replies.items():
            if f"THE SECTION: {title}." in sysm or (title == "READ"
                                                    and "Write THE READ" in sysm):
                return Resp(text() if callable(text) else text)
        period = "week" if "the Weekly" in sysm else "session"
        m = re.search(r"THE SECTION: ([^.]+)\.", sysm)
        tag = (m.group(1) if m else "read").lower()
        return Resp(f"The {tag} view held steady over the {period}. "
                    + DEFAULT.format(p=period))
    return types.SimpleNamespace(messages=types.SimpleNamespace(create=create))


def main() -> int:
    from altdata import bars as bars_mod
    from daily_cascade import deliver, readability as rd, stack_prose, stack_render as sr
    from daily_cascade import weekly_stack as ws

    print(f"{LINE}\nThe readability pass on every stacked report (T2.5)\n{LINE}")
    td = gate_mkdtemp(prefix="validate_readability_")
    read_text = ("Dealer gamma turned negative over the week. Credit and equities "
                 "kept arguing, and the curve kept steepening.")
    wk, wcalls, (wp, wdb, warch, wlog) = weekly_fixture(td, {"READ": read_text})
    wed, whtml = wk["edition"], wk["html_email"]
    cl, ccalls = close_fixture(td, {})
    ced, chtml = cl["edition"], cl["html_email"]
    eds = (("Weekly", wed, whtml), ("close", ced, chtml))

    # --- A. ONE FACT, ONCE ------------------------------------------------------
    print(f"\n{LINE}\nA. ONE FACT, ONCE (item 1)\n{LINE}")
    for name, ed, html in eds:
        check(not re.search(r"<(?:ul|ol|li)\b", html, re.I)
              and not re.search(r"(?m)^\s*(?:[•·*]|-\s)", body_text(html)),
              f"{name}: no bullet list anywhere in the rendered edition")
        paras = [p for s in ed["sections"] for p in s.get("paragraphs") or []]
        worst = max((rd.figure_count(p) for p in paras), default=0)
        check(paras and worst <= rd.PARAGRAPH_FIGURES,
              f"{name}: every paragraph cites at most six figures "
              f"({len(paras)} paragraphs, most {worst})")
    seven = ("SPY rose. It closed at 512.30, up 1.2%, with QQQ up 1.5%, IWM down "
             "0.4%, the 10-year at 4.12% and the 30-year at 4.61%, while HY OAS "
             "sat at 3.10% and gold at 2,401.")
    check(rd.figure_count(seven.split(". ", 1)[1]) == 8
          and stack_prose.figure_faults(seven)
          and not stack_prose.figure_faults("SPY rose. It closed at 512.30, up 1.2%."),
          f"a paragraph citing eight figures is withheld by the audit "
          f"({stack_prose.figure_faults(seven)})")
    check(rd.figure_count("The 10-year and the 20-day average, the S&P 500 and "
                          "2s10s on 28 Sep 2026.") == 0,
          "names and dates that carry digits are not figures")
    sec = {"table": {"columns": ["Market", "Last"], "rows": [["SPY", "512.30"]]},
           "items": [{"key": "t:spy", "text": "SPY 512.30."},
                     {"key": "t:o", "text": "SPY's overnight was +0.40%."},
                     {"key": "t:n", "text": "Dealer gamma read: negative."},
                     {"key": "t:none", "text": "Nothing else."}]}
    keep = [i["key"] for i in rd.printable_items(sec)]
    check(keep == ["t:o", "t:n"],
          f"an item whose figures are all in its table does not print again ({keep})")

    # --- B. THE FIXED ORDER -------------------------------------------------------
    print(f"\n{LINE}\nB. THE FIXED ORDER (item 2)\n{LINE}")
    for name, ed, html in eds:
        bad = []
        for ch, s in zip(chunks(html), ed["sections"]):
            if s.get("empty"):
                continue
            pos = [ch.find(f'style="{sr.CLAIM}"') if s.get("claim") else None,
                   ch.find("<table") if "<table" in ch else None,
                   ch.find("<figure") if "<figure" in ch else None,
                   ch.find(f'style="{sr.PARA}"') if s.get("paragraphs") else None,
                   ch.rfind(f'style="{sr.FOOT}"') if f'style="{sr.FOOT}"' in ch else None]
            seen = [x for x in pos if x is not None]
            if seen != sorted(seen) or ch.count(f'style="{sr.PARA}"') > 1:
                bad.append(s["id"])
        check(not bad, f"{name}: claim -> tables -> charts -> one paragraph -> "
                       f"footnote in every section (out of order: {bad})")
        long_ = [s["id"] for s in ed["sections"]
                 if len(s.get("paragraphs") or []) > 1
                 or any(len(p.split()) > rd.PARAGRAPH_WORDS for p in s["paragraphs"])
                 or any(ss.get("paragraph") for ss in s.get("subsections") or [])]
        check(not long_, f"{name}: one paragraph per section, at most "
                         f"{rd.PARAGRAPH_WORDS} words, none under a sub-section "
                         f"({long_})")
    big = {"sections": [{"id": "tape", "paragraphs": [
        " ".join(f"Sentence {n} has exactly seven words here." for n in range(30)),
        "A second paragraph."], "subsections": [{"paragraph": "x"}]}]}
    rd.finalize(big)
    tp = big["sections"][0]
    check(len(tp["paragraphs"]) == 1 and len(tp["paragraphs"][0].split()) <= 120
          and tp["trimmed"] and "paragraph" not in tp["subsections"][0],
          f"the guard keeps one paragraph, cut at a sentence to 120 words "
          f"({len(tp['paragraphs'][0].split())} words)")
    sec_calls = [c for c in wcalls if "THE SECTION:" in c]
    check(sec_calls and all("ONE paragraph" in c or "ONLY that one sentence" in c
                            for c in sec_calls)
          and not any("[A]" in c for c in sec_calls)
          and all("at most SIX figures" in c for c in sec_calls),
          f"every section's prompt asks for one paragraph, at most six figures, "
          f"no sub-section tags ({len(sec_calls)} calls)")

    # --- C. NO METHOD -------------------------------------------------------------
    print(f"\n{LINE}\nC. NO SENTENCES ABOUT THE METHOD (item 3)\n{LINE}")
    cfg = bars_mod.load_config()
    banned = [b.lower() for b in (cfg.get("style") or {}).get("banned_phrases") or []]
    six = ["for the system", "which is itself the finding",
           "written as such rather than left silent",
           "a count is attention, not evidence", "cited by id", "said positively so"]
    check(all(x in banned for x in six), "the ruling's six phrases are banned")
    check(all(stack_prose.style_faults(f"Rates rose, {x}.", cfg) for x in six),
          "and the prose audit withholds each of them")
    for name, ed, html in eds:
        low = body_text(html).lower()
        hits = [x for x in banned if len(x) > 8 and x in low]
        check(not hits, f"{name}: no banned method phrase in the body ({hits})")
        check(html.count("How to read this report:") == 1
              and rd.READERS_GUIDE in html
              and html.find("How to read this report:") > html.find(">Glossary</h2>"),
              f"{name}: one footer line points to the Reader's Guide")
    check("which is itself the finding" not in whtml
          and "Every figure above was read" not in whtml
          and "figures and odds" in whtml,
          "the standing note moved from the body to the glossary")

    # --- D. NO SENTENCE TWICE -----------------------------------------------------
    print(f"\n{LINE}\nD. NO SENTENCE TWICE (item 4)\n{LINE}")
    ed = {"sections": [
        {"id": "read", "claim": "Dealer gamma turned negative over the week.",
         "paragraphs": ["Credit and equities kept arguing."]},
        {"id": "mechanics", "claim": "Dealer gamma turned negative over the week.",
         "paragraphs": ["The flip sat above spot. Credit and equities kept arguing."]},
        {"id": "plumbing", "claim": "The curve steepened.", "paragraphs": []}]}
    log = rd.withhold_duplicates(ed)
    m = ed["sections"][1]
    check(len(log) == 2 and m["claim"] is None
          and m["paragraphs"] == ["The flip sat above spot."]
          and any("repeated The read" in n for n in m.get("notes") or []),
          f"a repeated claim and a repeated sentence are withheld in the later "
          f"section, with the reason in its footnote ({len(log)})")
    check(ed["sections"][2]["claim"] == "The curve steepened.",
          "a sentence that does not repeat is untouched")
    check(rd.same_sentence("Dealer gamma turned negative over the week.",
                           "Dealer gamma turned negative over the week!")
          and not rd.same_sentence("The curve steepened.", "The curve flattened."),
          "the comparison ignores punctuation and does not merge different sentences")
    dup_td = gate_mkdtemp(prefix="validate_readability_dup_")
    claim = "The tape view held steady over the week."
    _, dcalls, _ = weekly_fixture(dup_td, {"READ": claim + " " + DEFAULT.format(p="week")})
    reads = [c for c in dcalls if "Write THE READ" in c]
    check(len(reads) == 2 and "repeats a section's sentence" in reads[1]
          and "NEVER copy a section's claim" in reads[0],
          "The read is told never to copy a section's sentence, and a draft that "
          "does is sent back once with the reason")
    printed = [s for s in wed["sections"]]
    all_sents = [x for s in printed for t in [s.get("claim")] + list(s.get("paragraphs") or [])
                 for x in rd.sentences(t)]
    rs = rd.read_sentences(wed)
    twice = [x for x in rs if sum(rd.same_sentence(x, y) for y in all_sents) > 1]
    check(not twice, f"in the Weekly, no sentence of The read prints twice ({twice[:1]})")

    # --- E. EMPTY MEANS ONE LINE ---------------------------------------------------
    print(f"\n{LINE}\nE. EMPTY MEANS ONE LINE (item 5)\n{LINE}")
    ws.save_edition(wed, wp["week_ending"], warch)
    prior = ws.load_prior(wp["week_ending"], warch)
    with bars_mod.BarStore(wdb) as bst:
        book = ws.levels_mod.compute(wp["week_ending"], [], store=bst)
    ed2, _ = ws.build(wp, book, prior, wdb, wlog)
    empties = [s for s in ed2["sections"] if s.get("empty")]
    calls2: list = []
    stack_prose.write(ed2, client=client({}, calls2), outlooks=[], cadence="weekly")
    asked = [re.search(r"THE SECTION: ([^.]+)\.", c).group(1) for c in calls2
             if "THE SECTION:" in c]
    check(empties and all(s["title"] not in asked for s in empties),
          f"an unchanged section is empty and makes no model call "
          f"({[s['id'] for s in empties]}; asked {len(asked)})")
    one = sr.section_html(empties[0], 3, {}, "email") if empties else ""
    check(empties and "Unchanged since 2 Oct" in one and "<table" not in one
          and f'style="{sr.CLAIM}"' not in one
          and one.count("<p") <= 1 + len(empties[0].get("not_tracked") or [])
          + int(bool(empties[0].get("legend"))),
          f"and prints its header and its footnote alone "
          f"({re.sub('<[^>]+>', ' ', one)[-80:].strip()})")
    nofacts = [{"id": "misfit", "items": [{"key": "misfit:none",
                                           "text": "No contradiction is open."}]}]
    rd.mark_empty(nofacts, "session")
    check(nofacts[0]["empty"] and nofacts[0]["empty_note"] == "No contradiction is open.",
          "a section with no fact at all is empty, its placeholder the one line")

    # --- F. FORMATTING ------------------------------------------------------------
    print(f"\n{LINE}\nF. FORMATTING (item 6)\n{LINE}")
    cases = {"open 2 session(s) at z +2.6": "open 2 sessions at z +2.6",
             "open 1 session(s)": "open 1 session",
             "20 story evaluation(s) ran": "20 story evaluations ran",
             "two years, +-1 sigma": "two years, ±1 sigma",
             "from 2026-09-28 to 2026-10-02": "from 28 Sep to 2 Oct",
             "since 2025-12-31": "since 31 Dec 2025",
             "net -16,542 contracts": "net −16,542 contracts",
             "outside 10-90%": "outside 10-90%",
             "https://x.org/2026-10-02-note": "https://x.org/2026-10-02-note",
             "at 2026-10-04T09:00:00+00:00": "at 2026-10-04T09:00:00+00:00"}
    bad = {k: rd.polish(k, 2026) for k, v in cases.items() if rd.polish(k, 2026) != v}
    check(not bad, f"plurals, '±', the true minus, prose dates; URLs and "
                   f"timestamps untouched ({bad})")
    check(rd.stamp_et("2026-10-04T09:04:00+00:00") == "Sun 4 Oct, 05:04 ET"
          and rd.stamp_et("2026-10-02T20:45:00+00:00") == "Fri 2 Oct, 16:45 ET",
          "the header stamp reads 'Sun 4 Oct, 05:04 ET'")
    check(rd.plural(1, "chart") == "1 chart" and rd.plural(4, "chart") == "4 charts"
          and rd.plural(0, "story", "stories") == "0 stories",
          "plurals by count")
    for name, ed, html in eds:
        t = body_text(html)
        prose = re.sub(r"<table.*?</table>", " ", html, flags=re.S)
        prose = prose[:prose.find(">Glossary</h2>")] if ">Glossary</h2>" in prose else prose
        prose = re.sub(r"<[^>]+>", " ", prose)
        iso = re.findall(r"(?<![\w/.:=-])\d{4}-\d{2}-\d{2}(?![\w/:])", prose)
        check("(s)" not in t and "+-" not in t and not iso,
              f"{name}: no '(s)', no '+-', no ISO date outside a table "
              f"({iso[:3]})")
        unsigned = []
        for s in ed["sections"]:
            for tb in [s.get("table")] + [ss.get("table") for ss in
                                           s.get("subsections") or []]:
                for i, c in enumerate((tb or {}).get("columns") or []):
                    if i == 0 or c not in ("Session", "Week", "Month", "YTD", "Change",
                                 "Week change", "Session change"):
                        continue
                    for r in tb["rows"]:
                        v = str(r[i] if i < len(r) else "")
                        if re.match(r"^\d{4}-\d{2}", v):     # a period, not a change
                            continue
                        if not re.match(r"^(?:—|n/a|no prior.*|[+−±]|0(?:\.0+)?\b|"
                                        r"\$?0\b|none)", v):
                            unsigned.append(f"{c}: {v}")
        check(not unsigned, f"{name}: every change column carries its sign "
                            f"({unsigned[:3]})")
    book_t = next(s for s in wed["sections"] if s["id"] == "book")["table"]
    sit = next(r for r in book_t["rows"] if r[0].startswith("Sitting"))
    check(sit[1] == "22 minutes" and sit[2] == "120 minutes"
          and "sitting hours" not in whtml,
          f"durations in minutes ({sit})")

    # --- G. HEADER AND SUBJECT --------------------------------------------------
    print(f"\n{LINE}\nG. HEADER AND SUBJECT (items 7, 8)\n{LINE}")
    head = whtml[:whtml.find("&middot; The read")]
    check("Weekly — week ending 2 Oct" in head and "Sun 4 Oct, 05:00 ET" in head
          and re.search(r"about \d+ minutes? to read", head)
          and "Changed since last Weekly" in head,
          "the header: title, week, the ET stamp, reading time, what changed")
    foot = whtml[whtml.find(">Glossary</h2>"):]
    check("Stack " in foot and "as-of cutoff" in foot and "run weekly-fixture" in foot
          and "word" in foot and "Stack " not in head and "run weekly-fixture" not in head,
          "the run metadata (stack, words, cutoff, run id) sits in the footer only")
    ch = "Close" + "—"
    wsub = rd.subject("Weekly", "w/e 2 Oct", wed)
    claim_w = next(s for s in wed["sections"] if s["id"] == "read")["claim"] or ""
    check(wsub == f"Weekly — w/e 2 Oct — {rd.short_claim(claim_w)}" and claim_w,
          f"the Weekly's subject carries The read's claim ({wsub})")
    long_ed = {"sections": [{"id": "read", "claim": "word " * 40}]}
    s90 = rd.subject("Close", "2 Oct", long_ed).split(" — ", 2)[2]
    check(len(s90) <= 90 and s90.endswith("…"),
          f"a claim past 90 characters is cut at a word ({len(s90)})")
    check(rd.subject("Weekly", "w/e 2 Oct", wed, True).startswith("[DRY RUN] Weekly — w/e"),
          "the dry run's subject is the same, marked")
    del ch
    cr = (REPO / "daily_cascade" / "close_report.py").read_text(encoding="utf-8")
    check('readability.subject("Close", readability.prose_date(sess), ed)' in cr,
          "the daily close's subject carries its claim too")

    # --- H. PREDICTION MARKETS ---------------------------------------------------
    print(f"\n{LINE}\nH. PREDICTION MARKETS AS A TABLE (item 9)\n{LINE}")
    pmb = {"legs_sum_band": [0.95, 1.05],
           "fomc_odds": {"2026-10-28": {"kalshi": {"hold": 0.82, "hike": 0.18,
                                                   "cut": 0.08},
                                        "polymarket": {"hold": 0.84, "hike": 0.17,
                                                       "cut": 0.01}}},
           "watch": {"fomc_decision": [
               {"venue": "kalshi", "decision_date": "2026-10-28",
                "question": "Fed decision in October?", "outcome": "Hold",
                "change_5s_points": 4.0},
               {"venue": "polymarket", "decision_date": "2026-10-28",
                "question": "Fed decision in October?", "outcome": "No change",
                "change_5s_points": -1.5}]},
           "venues": {}}
    t = rd.pm_table(pmb, "5s")
    hold = next((r for r in t["rows"] if r[0].endswith("hold")), None)
    check(t["columns"] == ["Item", "Kalshi", "Polymarket", "Week change", "Note"],
          "columns: item · Kalshi · Polymarket · week change · note")
    check(hold and hold[1] == "82%" and hold[2] == "84%"
          and "Kalshi legs sum to 108%" in hold[4],
          f"each side by venue, the legs-sum flag in the note ({hold})")
    cut = next((r for r in t["rows"] if r[0].endswith("cut")), None)
    check(cut and "outside 10–90%" in cut[4], f"odds outside 10–90% noted ({cut})")
    for name, ed, html in eds:
        pri = next(s for s in ed["sections"] if s["id"] == "priced")
        pm = next((ss for ss in pri.get("subsections") or []
                   if ss.get("title") == "Prediction markets"), None)
        check(pm is None or (pm.get("table") or {}).get("columns", [""])[0] == "Item"
              and not pm.get("lines"),
              f"{name}: What's priced prints prediction markets as the table, "
              f"never lines")

    # --- I. STYLES -----------------------------------------------------------------
    print(f"\n{LINE}\nI. STYLES (item 10)\n{LINE}")
    for name, ed, html in eds:
        widths = [len(re.findall(r"<th\b", tb)) for tb in
                  re.findall(r"<table.*?</table>", html, flags=re.S)]
        check(widths and max(widths) <= 6, f"{name}: every table at most six "
                                           f"columns (widest {max(widths or [0])})")
        has = {"section header": f'style="{sr.SECTION}"', "claim": f'style="{sr.CLAIM}"',
               "table header row": f'style="{sr.THL}"', "zebra": f'style="{sr.ZEBRA}"',
               "right-aligned number": f'style="{sr.TD}"',
               "chart caption": f'style="{sr.CAPTION}"',
               "paragraph": f'style="{sr.PARA}"', "footnote": f'style="{sr.FOOT}"'}
        miss = [k for k, v in has.items() if v not in html]
        check(not miss, f"{name}: the element styles are all present ({miss})")
    check("font-weight:700" in sr.CLAIM and float(re.search(r"font-size:([\d.]+)px",
                                                            sr.CLAIM).group(1)) >= 15
          and "font-style:italic" in sr.CAPTION and "font-size:11px" in sr.CAPTION
          and "font-size:11px" in sr.FOOT and "#6b7785" in sr.FOOT
          and "text-align:right" in sr.TD and "background" in sr.ZEBRA,
          "claim bold and larger; caption small italic; footnote small grey; "
          "numbers right; zebra rows")
    wrong = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", whtml, flags=re.S):
        cells = re.findall(r'<td style="([^"]+)">([^<]*)</td>', row)
        wrong += [v for st_, v in cells[1:] if sr.is_number(v)
                  and st_ not in (sr.TD, sr.TDW)]
    check(not wrong and sr.is_number("4.289%") and sr.is_number("+4 bp")
          and sr.is_number("22 minutes") and not sr.is_number("10-year yield")
          and not sr.is_number("2026-10-02"),
          f"every numeric cell after the first column is right-aligned, a name "
          f"that starts with a digit is not ({wrong[:3]})")
    check("max-width:100%" in sr.IMG and "max-width:720px" in sr.WRAP
          and "width:100%" in sr.TBL and "overflow-x:auto" in sr.SCROLL
          and f'<div style="{sr.SCROLL}"><table' in whtml
          and "overflow-wrap:anywhere" in sr.FOOT and "white-space:nowrap" in sr.TD,
          "legible at 400 px: the images shrink, the tables fill and wrap")
    split = sr._table({"columns": list("ABCDEFGH"), "rows": [list("12345678")]})
    check(split.count("<table") == 2 and all(len(re.findall(r"<th\b", x)) <= 6
                                             for x in split.split("</table>")),
          "a table wider than six columns prints as two, the first column repeated")

    # --- J. PDF --------------------------------------------------------------------
    print(f"\n{LINE}\nJ. THE PDF (item 11)\n{LINE}")
    ph = rd.pdf_html(whtml, wk["inline_images"])
    check("cid:" not in ph and "data:image/png;base64," in ph
          and "counter(page)" in ph and "break-inside: avoid" in ph
          and "@page" in ph and rd.PAGE_SIZE in ("A4", "Letter"),
          "the PDF is the emailed HTML: charts as their own PNGs, page numbers, "
          "charts never split, A4/letter")
    req = (REPO / "requirements.txt").read_text(encoding="utf-8")
    check(re.search(r"(?m)^weasyprint\b", req), "WeasyPrint is in requirements.txt")
    fake = b"%PDF-1.7 fixture"
    msg = deliver.build_message({"user": "a@x.invalid", "rcpt": "b@x.invalid"}, "s",
                                whtml, "t", attachments=[("w.pdf", fake, "pdf")],
                                inline_images=wk["inline_images"])
    parts = [pp for pp in message_from_bytes(msg.as_bytes(), policy=email_default).walk()
             if pp.get_content_type() == "application/pdf"]
    check(len(parts) == 1 and parts[0].get_payload(decode=True) == fake
          and parts[0].get_filename() == "w.pdf",
          "the PDF is attached beside the HTML body")
    env = {k: os.environ.pop(k) for k in ("SMTP_USER", "SMTP_PASSWORD")
           if k in os.environ}
    real = deliver.smtp_config
    deliver.smtp_config = lambda: (None, ["SMTP_USER"])
    try:
        res = deliver.deliver("s", whtml, "weekly_tactical_2026-10-02.html",
                              archive_dir=str(Path(td) / "pdfarch"), pdf=fake)
    finally:
        deliver.smtp_config = real
        os.environ.update(env)
    check(res.get("pdf_path") and Path(res["pdf_path"]).read_bytes() == fake
          and Path(res["pdf_path"]).name == "weekly_tactical_2026-10-02.pdf"
          and Path(res["pdf_path"]).parent == Path(res["archive_path"]).parent,
          "and archived next to the HTML, before the send")
    wr = (REPO / "daily_cascade" / "weekly_report.py").read_text(encoding="utf-8")
    dry = wr[wr.find('if getattr(args, "email", False):'):wr.find("return 3")]
    check('pdf=out.get("pdf")' in dry, "the --dry-run --email form attaches it too")
    try:
        import weasyprint  # noqa: F401
        have = True
    except Exception as exc:                                    # noqa: BLE001
        have, why = False, f"{type(exc).__name__}: {str(exc)[:120]}"
    if have:
        pdf, detail = rd.pdf_bytes(whtml, wk["inline_images"])
        # Pages counted by WeasyPrint's own document: the PDF keeps its page
        # objects in compressed object streams, so the bytes cannot be grepped.
        pages = len(weasyprint.HTML(string=rd.pdf_html(whtml, wk["inline_images"]))
                    .render().pages)
        check(pdf and pdf[:5] == b"%PDF-" and len(pdf) <= rd.PDF_MAX_BYTES
              and pages >= 2,
              f"the fixture Weekly renders to PDF: {detail}, {pages} pages")
        pdf_c, detail_c = rd.pdf_bytes(chtml, cl["inline_images"])
        check(pdf_c and len(pdf_c) <= rd.PDF_MAX_BYTES,
              f"and the fixture close: {detail_c}")
        check(wk.get("pdf") and len(wk["pdf"]) <= rd.PDF_MAX_BYTES,
              f"produce() builds it with the edition ({wk.get('pdf_detail')})")
    elif os.environ.get("GITHUB_ACTIONS") == "true":
        check(False, f"WeasyPrint must render the fixture in CI ({why})")
    else:
        print(f"  NOT VALIDATED here: WeasyPrint is not installed with its "
              f"libraries on this machine ({why}); CI and the box render the "
              f"fixture to PDF.")
        check("WeasyPrint unavailable" in str(wk.get("pdf_detail"))
              and wk.get("pdf") is None,
              "without it, the edition builds and says the PDF was not built")

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION FAILED" if FAIL else "VALIDATION PASSED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
